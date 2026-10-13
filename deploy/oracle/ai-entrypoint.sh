#!/bin/sh
set -eu
: "${LOCAL_AI_API_KEY:?LOCAL_AI_API_KEY is required}"
model=/models/qwen3b.gguf
mkdir -p /models
if [ ! -s "$model" ]; then
  echo "Downloading the Qwen 2.5 3B narration model into persistent storage..."
  curl --fail --location --retry 5 --retry-delay 3 --continue-at - \
    --output "$model.part" \
    'https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf'
  mv "$model.part" "$model"
fi
parallel=${AI_PARALLEL:-auto}
if [ "$parallel" = auto ]; then parallel=$(nproc); fi
case "$parallel" in ''|*[!0-9]*) echo 'AI_PARALLEL must be auto or a positive integer' >&2; exit 1;; esac
[ "$parallel" -gt 0 ] || { echo 'AI_PARALLEL must be positive' >&2; exit 1; }
# Keep 4096 tokens per request as the number of simultaneous slots increases.
set -- -m "$model" \
  --host 0.0.0.0 --port 8787 --jinja --alias qwen2.5-3b-instruct \
  --api-key "$LOCAL_AI_API_KEY" --no-repack \
  -c "$((4096 * parallel))" -np "$parallel"
threads=${AI_THREADS:-auto}
if [ "$threads" != auto ]; then
  case "$threads" in ''|*[!0-9]*) echo 'AI_THREADS must be auto or a positive integer' >&2; exit 1;; esac
  [ "$threads" -gt 0 ] || { echo 'AI_THREADS must be positive' >&2; exit 1; }
  set -- "$@" -t "$threads" -tb "$threads"
fi
exec /opt/llama/bin/llama-server "$@"
