#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo_root"
site_dir="$repo_root/deploy/oracle/homepage"
archive=${1:-$site_dir/homepage-source.tar.gz}
if [[ $# == 0 ]]; then
  python3 scripts/package-homepage.py --output "$archive"
fi
mkdir -p "$site_dir/source"
tar -xzf "$archive" -C "$site_dir/source"
revision=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["revision"])' "$site_dir/source/homepage-source.json")
test "$revision" = "$(git rev-parse HEAD)"
image="nexstudio-homepage:${revision:0:12}"
sudo -n docker build --progress=plain -t "$image" "$site_dir/source"
export_dir=$(mktemp -d "$site_dir/export.XXXXXX")
container=$(sudo -n docker create "$image")
trap 'sudo -n docker rm "$container" >/dev/null 2>&1 || true' EXIT
sudo -n docker cp "$container:/app/out/." "$export_dir/"
sudo -n docker rm "$container" >/dev/null
trap - EXIT
sudo -n chown -R "$(id -u):$(id -g)" "$export_dir"
test -s "$export_dir/index.html"
test -s "$export_dir/pricing.html"
grep -q 'From brief to' "$export_dir/index.html"
test ! -d "$export_dir/api"
test ! -d "$export_dir/studio"
test ! -d "$export_dir/dashboard"
cp "$site_dir/source/homepage-source.json" "$export_dir/../homepage-source.json"

backup=$(mktemp -d /home/ubuntu/nexstudio-homepage-backup.XXXXXX)
chmod 700 "$backup"
cp deploy/oracle/Caddyfile deploy/oracle/compose.yml "$backup/"
if [[ -d "$site_dir/out" ]]; then
  mv "$site_dir/out" "$site_dir/out.previous.$(date +%s)"
fi
mv "$export_dir" "$site_dir/out"
compose=(sudo -n docker compose --env-file deploy/oracle/.env -f deploy/oracle/compose.yml)
"${compose[@]}" config --quiet
"${compose[@]}" run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
# Recreate Caddy so its directory mount follows the newly exported directory.
"${compose[@]}" up -d --no-deps --no-build --force-recreate caddy
echo "Homepage and pricing deployed from $revision. App pages and APIs are not proxied."
