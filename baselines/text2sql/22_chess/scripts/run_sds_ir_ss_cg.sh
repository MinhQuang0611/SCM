#!/usr/bin/env bash
set -euo pipefail

BASELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH" >&2
  exit 2
fi

cd "$CHESS_DIR"
set -a
source .env
set +a

conda run -n "$ENV_NAME" python -u ./src/main.py \
  --data_mode "${DATA_MODE:-dev}" \
  --data_path "${DATA_PATH:-./data/dev/dev.json}" \
  --config ./run/configs/CHESS_IR_SS_CG.yaml \
  --num_workers "${CHESS_NUM_WORKERS:-1}" \
  --pick_final_sql true
