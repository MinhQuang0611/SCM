#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BASELINE_DIR="$ROOT_DIR/baselines/text2sql/22_chess"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"
DATASET="sds"
SHARD_SIZE=10
NUM_WORKERS=1
START_SHARD=0
MAX_SHARDS=0
ALLOW_MISSING_PREPROCESS=0

usage() {
  cat <<'EOF'
Usage:
  bash baselines/text2sql/22_chess/scripts/run_ir_ss_cg_realtime.sh [options]

Options:
  --dataset sds|bird-dev       Dataset to shard and run. Default: sds.
  --shard-size N               Examples per shard. Default: 10.
  --num-workers N              CHESS internal workers per shard. Default: 1.
  --start-shard N              First shard index to run. Default: 0.
  --max-shards N               Stop after N shards. Default: 0 means all.
  --allow-missing-preprocess   Run even if some DBs lack LSH/vector artifacts.
  -h, --help                   Show help.

Examples:
  # SDS smoke: first 1 shard of 5 examples, realtime logs
  bash baselines/text2sql/22_chess/scripts/run_ir_ss_cg_realtime.sh --dataset sds --shard-size 5 --max-shards 1

  # SDS pilot: all 147 examples in shards of 10
  bash baselines/text2sql/22_chess/scripts/run_ir_ss_cg_realtime.sh --dataset sds --shard-size 10

  # Full BIRD dev: all 1534 examples in shards of 50
  bash baselines/text2sql/22_chess/scripts/run_ir_ss_cg_realtime.sh --dataset bird-dev --shard-size 50
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dataset) DATASET="$2"; shift 2 ;;
    --shard-size) SHARD_SIZE="$2"; shift 2 ;;
    --num-workers) NUM_WORKERS="$2"; shift 2 ;;
    --start-shard) START_SHARD="$2"; shift 2 ;;
    --max-shards) MAX_SHARDS="$2"; shift 2 ;;
    --allow-missing-preprocess) ALLOW_MISSING_PREPROCESS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$DATASET" in
  sds)
    SOURCE_JSON="$CHESS_DIR/data/dev/sub_sampled_bird_dev_set.json"
    DATASET_LABEL="sds"
    ;;
  bird-dev|full|full-dev)
    SOURCE_JSON="$ROOT_DIR/datasets/text2sql/bird/dev.json"
    DATASET_LABEL="bird_dev"
    ;;
  *)
    echo "Unknown dataset: $DATASET" >&2
    usage >&2
    exit 2
    ;;
esac

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH" >&2
  exit 2
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Missing conda env: $ENV_NAME" >&2
  exit 2
fi

SHARD_DIR="$CHESS_DIR/data/dev/shards/${DATASET_LABEL}_n${SHARD_SIZE}"
mkdir -p "$SHARD_DIR"

python3 - "$SOURCE_JSON" "$SHARD_DIR" "$DATASET_LABEL" "$SHARD_SIZE" <<'PY'
import json, sys
from pathlib import Path
source = Path(sys.argv[1])
shard_dir = Path(sys.argv[2])
label = sys.argv[3]
size = int(sys.argv[4])
data = json.loads(source.read_text(encoding="utf-8"))
for i in range(0, len(data), size):
    shard_id = i // size
    rows = data[i:i + size]
    out = shard_dir / f"{label}_shard_{shard_id:04d}_n{len(rows)}.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

read -r TOTAL_ROWS TOTAL_SHARDS < <(python3 - "$SOURCE_JSON" "$SHARD_SIZE" <<'PY'
import json, sys, math
from pathlib import Path
n = len(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
size = int(sys.argv[2])
print(n, math.ceil(n / size))
PY
)

missing_preprocess="$(
  python3 - "$SOURCE_JSON" "$ROOT_DIR/datasets/text2sql/bird/dev_databases" <<'PY'
import json, sys
from pathlib import Path
source = Path(sys.argv[1])
db_root = Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))
missing = []
for db in sorted({row["db_id"] for row in data}):
    base = db_root / db
    needed = [
        base / "preprocessed" / f"{db}_lsh.pkl",
        base / "preprocessed" / f"{db}_minhashes.pkl",
        base / "preprocessed" / f"{db}_unique_values.pkl",
        base / "context_vector_db" / "chroma.sqlite3",
    ]
    if not all(p.exists() for p in needed):
        missing.append(db)
print(",".join(missing))
PY
)"

if [ -n "$missing_preprocess" ] && [ "$ALLOW_MISSING_PREPROCESS" -ne 1 ]; then
  echo "Missing preprocess artifacts for DBs: $missing_preprocess" >&2
  echo "Run first:" >&2
  echo "  bash baselines/text2sql/22_chess/scripts/preprocess_dbs_realtime.sh $DATASET" >&2
  echo "Or override with --allow-missing-preprocess." >&2
  exit 2
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

mkdir -p "$BASELINE_DIR/logs/realtime"
run_label="$(date +%Y%m%d_%H%M%S)_${DATASET_LABEL}_shard${SHARD_SIZE}"
log_dir="$BASELINE_DIR/logs/realtime/$run_label"
mkdir -p "$log_dir"

echo "CHESS IR_SS_CG realtime run"
echo "dataset=$DATASET_LABEL"
echo "source=$SOURCE_JSON"
echo "rows=$TOTAL_ROWS shards=$TOTAL_SHARDS shard_size=$SHARD_SIZE"
echo "start_shard=$START_SHARD max_shards=$MAX_SHARDS num_workers=$NUM_WORKERS"
echo "log_dir=$log_dir"
echo

cd "$CHESS_DIR"
set -a
source .env
set +a

ran=0
for shard in "$SHARD_DIR"/*.json; do
  name="$(basename "$shard" .json)"
  shard_id="$(printf '%s\n' "$name" | sed -E 's/.*_shard_([0-9]+)_n[0-9]+$/\1/')"
  shard_num=$((10#$shard_id))
  if [ "$shard_num" -lt "$START_SHARD" ]; then
    continue
  fi
  if [ "$MAX_SHARDS" -gt 0 ] && [ "$ran" -ge "$MAX_SHARDS" ]; then
    break
  fi

  echo "============================================================"
  echo "START shard=$shard_num file=$shard"
  echo "TIME $(date '+%F %T %Z')"
  echo "============================================================"

  set +e
  python -u ./src/main.py \
    --data_mode dev \
    --data_path "./data/dev/shards/${DATASET_LABEL}_n${SHARD_SIZE}/$(basename "$shard")" \
    --config ./run/configs/CHESS_IR_SS_CG.yaml \
    --num_workers "$NUM_WORKERS" \
    --pick_final_sql true 2>&1 | tee "$log_dir/${name}.log"
  status=${PIPESTATUS[0]}
  set -e

  latest_result="$(find "$CHESS_DIR/results/dev/CHESS_IR_SS_CG/$name" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -1 || true)"
  if [ -n "$latest_result" ] && [ -f "$latest_result/-statistics.json" ]; then
    echo "STATS shard=$shard_num result=$latest_result"
    python3 - "$latest_result/-statistics.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
print(json.dumps(data.get("counts", {}).get("final_SQL", data), ensure_ascii=False))
PY
  else
    echo "WARN no statistics found for shard=$shard_num"
  fi

  echo "END shard=$shard_num status=$status time=$(date '+%F %T %Z')"
  echo
  if [ "$status" -ne 0 ]; then
    echo "Shard failed: $shard_num" >&2
    exit "$status"
  fi
  ran=$((ran + 1))
done

echo "Realtime run complete: dataset=$DATASET_LABEL shards_ran=$ran"
echo "Logs: $log_dir"
