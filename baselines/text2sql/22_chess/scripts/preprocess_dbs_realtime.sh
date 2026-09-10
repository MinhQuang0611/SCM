#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BASELINE_DIR="$ROOT_DIR/baselines/text2sql/22_chess"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"
DATASET="${1:-sds}"

usage() {
  cat <<'EOF'
Usage:
  bash baselines/text2sql/22_chess/scripts/preprocess_dbs_realtime.sh [sds|bird-dev]

Environment:
  CHESS_CONDA_ENV=chess    conda env name
EOF
}

case "$DATASET" in
  sds) SOURCE_JSON="$CHESS_DIR/data/dev/sub_sampled_bird_dev_set.json" ;;
  bird-dev|full|full-dev) SOURCE_JSON="$ROOT_DIR/datasets/text2sql/bird/dev.json" ;;
  -h|--help) usage; exit 0 ;;
  *) echo "Unknown dataset: $DATASET" >&2; usage >&2; exit 2 ;;
esac

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH" >&2
  exit 2
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Missing conda env: $ENV_NAME" >&2
  exit 2
fi

mapfile -t DBS < <(python3 - "$SOURCE_JSON" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
for db in sorted({row["db_id"] for row in data}):
    print(db)
PY
)

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

mkdir -p "$BASELINE_DIR/logs/preprocess"
run_label="$(date +%Y%m%d_%H%M%S)_${DATASET}"
log_dir="$BASELINE_DIR/logs/preprocess/$run_label"
mkdir -p "$log_dir"

echo "CHESS preprocess realtime"
echo "dataset=$DATASET"
echo "source=$SOURCE_JSON"
echo "db_count=${#DBS[@]}"
echo "log_dir=$log_dir"
echo

cd "$CHESS_DIR"
set -a
source .env
set +a

for i in "${!DBS[@]}"; do
  db="${DBS[$i]}"
  idx=$((i + 1))
  base="$ROOT_DIR/datasets/text2sql/bird/dev_databases/$db"
  lsh="$base/preprocessed/${db}_lsh.pkl"
  minhash="$base/preprocessed/${db}_minhashes.pkl"
  unique="$base/preprocessed/${db}_unique_values.pkl"
  chroma="$base/context_vector_db/chroma.sqlite3"
  echo "[$idx/${#DBS[@]}] DB=$db"
  if [ -f "$lsh" ] && [ -f "$minhash" ] && [ -f "$unique" ] && [ -f "$chroma" ]; then
    echo "[$idx/${#DBS[@]}] SKIP already preprocessed: $db"
    echo
    continue
  fi
  python -u ./src/preprocess.py \
    --db_root_directory "${DB_ROOT_DIRECTORY:-./data/dev/dev_databases}" \
    --signature_size 100 \
    --n_gram 3 \
    --threshold 0.01 \
    --db_id "$db" \
    --verbose true 2>&1 | tee "$log_dir/${idx}_${db}.log"
  echo "[$idx/${#DBS[@]}] DONE DB=$db"
  echo
done

echo "Preprocess batch complete: $DATASET"
echo "Logs: $log_dir"

