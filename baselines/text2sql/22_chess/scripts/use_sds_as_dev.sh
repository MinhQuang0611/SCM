#!/usr/bin/env bash
set -euo pipefail

BASELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
SDS="$CHESS_DIR/data/dev/sub_sampled_bird_dev_set.json"
DEV="$CHESS_DIR/data/dev/dev.json"

if [ ! -f "$SDS" ]; then
  echo "Missing $SDS" >&2
  exit 2
fi

cp "$SDS" "$DEV"
echo "Wrote $DEV from SDS ($SDS)"

