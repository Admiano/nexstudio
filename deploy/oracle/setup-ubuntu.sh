#!/usr/bin/env bash
set -euo pipefail
if [[ $(id -u) != 0 ]]; then
  echo "Run with sudo: sudo bash deploy/oracle/setup-ubuntu.sh" >&2
  exit 1
fi
source /etc/os-release
if [[ ${ID:-} != ubuntu || ${VERSION_ID:-} != 24.04 ]]; then
  echo "This setup script targets Ubuntu 24.04 LTS." >&2
  exit 1
fi
architecture=$(dpkg --print-architecture)
if [[ $architecture != amd64 && $architecture != arm64 ]]; then
  echo "This deployment supports amd64 and arm64 Linux." >&2
  exit 1
fi
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  echo "Docker Engine and Compose are already installed."
  exit 0
fi
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: $architecture
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker compose version
