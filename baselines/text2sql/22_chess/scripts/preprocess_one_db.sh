#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <db_id>" >&2
  exit 2
fi

BASELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"
DB_ID="$1"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH" >&2
  exit 2
fi

cd "$CHESS_DIR"
set -a
source .env
set +a

conda run -n "$ENV_NAME" python -u ./src/preprocess.py \
  --db_root_directory "${DB_ROOT_DIRECTORY:-./data/dev/dev_databases}" \
  --signature_size 100 \
  --n_gram 3 \
  --threshold 0.01 \
  --db_id "$DB_ID" \
  --verbose true
