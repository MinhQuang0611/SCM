#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BASELINE_DIR="$ROOT_DIR/baselines/text2sql/22_chess"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
BIRD_DIR="$ROOT_DIR/datasets/text2sql/bird"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"

ok() { printf 'PASS  %s\n' "$1"; }
warn() { printf 'WARN  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; }
section() { printf '\n== %s ==\n' "$1"; }

exists() {
  local path="$1"
  local label="$2"
  if [ -e "$path" ]; then ok "$label: $path"; else fail "$label missing: $path"; fi
}

section "CHESS Baseline"
printf 'Root: %s\n' "$ROOT_DIR"
printf 'CHESS: %s\n' "$CHESS_DIR"
if [ -d "$CHESS_DIR/.git" ]; then
  printf 'Commit: %s\n' "$(git -C "$CHESS_DIR" rev-parse --short=12 HEAD)"
fi

section "Conda"
if command -v conda >/dev/null 2>&1; then
  ok "conda found: $(conda --version)"
  if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    ok "env exists: $ENV_NAME"
    conda run -n "$ENV_NAME" python --version
    missing="$(
      conda run -n "$ENV_NAME" python - <<'PY'
import importlib.util
mods = ["langchain_openai", "langchain_chroma", "datasketch", "sqlglot", "sentence_transformers", "faiss", "pandas"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
print(",".join(missing))
PY
    )"
    if [ -z "$missing" ]; then ok "required imports available"; else fail "missing imports: $missing"; fi
  else
    fail "env missing: $ENV_NAME"
  fi
else
  fail "conda not found"
fi

section "Data"
exists "$BIRD_DIR" "central BIRD dir"
exists "$BIRD_DIR/dev.json" "BIRD dev.json"
exists "$BIRD_DIR/dev_tables.json" "BIRD dev_tables.json"
exists "$BIRD_DIR/dev_databases" "BIRD dev_databases"
exists "$CHESS_DIR/data/dev/dev.json" "CHESS active dev.json"
exists "$CHESS_DIR/data/dev/sub_sampled_bird_dev_set.json" "CHESS SDS json"
if [ -L "$CHESS_DIR/data/dev/dev_databases" ]; then ok "CHESS dev_databases symlink -> $(readlink "$CHESS_DIR/data/dev/dev_databases")"; else warn "CHESS dev_databases is not a symlink"; fi
if [ -L "$CHESS_DIR/data/dev/dev_tables.json" ]; then ok "CHESS dev_tables symlink -> $(readlink "$CHESS_DIR/data/dev/dev_tables.json")"; else warn "CHESS dev_tables is not a symlink"; fi

section "Dataset Counts"
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
items = [
    ("SDS", Path("baselines/text2sql/22_chess/code/CHESS/data/dev/sub_sampled_bird_dev_set.json")),
    ("active_dev", Path("baselines/text2sql/22_chess/code/CHESS/data/dev/dev.json")),
    ("BIRD_dev", Path("datasets/text2sql/bird/dev.json")),
]
for name, path in items:
    if not path.exists():
        print(f"FAIL  {name}: missing {path}")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    dbs = Counter(row["db_id"] for row in data)
    diff = Counter(row.get("difficulty") for row in data)
    print(f"PASS  {name}: n={len(data)} dbs={len(dbs)} difficulty={dict(diff)}")
    print("      top_dbs=" + ", ".join(f"{k}:{v}" for k, v in dbs.most_common(5)))
PY

section "Preprocess Artifacts"
python3 - <<'PY'
import json
from pathlib import Path
sds = Path("baselines/text2sql/22_chess/code/CHESS/data/dev/sub_sampled_bird_dev_set.json")
db_root = Path("datasets/text2sql/bird/dev_databases")
if not sds.exists() or not db_root.exists():
    print("FAIL  cannot inspect preprocess artifacts")
    raise SystemExit(0)
dbs = sorted({row["db_id"] for row in json.loads(sds.read_text(encoding="utf-8"))})
ready = []
missing = []
for db in dbs:
    base = db_root / db
    needed = [
        base / "preprocessed" / f"{db}_lsh.pkl",
        base / "preprocessed" / f"{db}_minhashes.pkl",
        base / "preprocessed" / f"{db}_unique_values.pkl",
        base / "context_vector_db" / "chroma.sqlite3",
    ]
    if all(p.exists() for p in needed):
        ready.append(db)
    else:
        missing.append(db)
print(f"{'PASS' if not missing else 'WARN'}  SDS DB preprocess ready: {len(ready)}/{len(dbs)}")
if ready:
    print("      ready=" + ", ".join(ready))
if missing:
    print("      missing=" + ", ".join(missing))
PY

section "Preflight"
if command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda run -n "$ENV_NAME" python "$BASELINE_DIR/scripts/preflight.py" || true
else
  warn "skipped preflight because conda env is unavailable"
fi

section "Latest CHESS Runs"
python3 - <<'PY'
from pathlib import Path
import json
root = Path("baselines/text2sql/22_chess/code/CHESS/results")
runs = sorted([p for p in root.rglob("-statistics.json")], key=lambda p: p.stat().st_mtime, reverse=True)
if not runs:
    print("WARN  no CHESS run statistics found")
else:
    for stat in runs[:5]:
        out_dir = stat.parent
        try:
            data = json.loads(stat.read_text(encoding="utf-8"))
            counts = data.get("counts", {}).get("final_SQL", {})
        except Exception as exc:
            counts = {"error": str(exc)}
        print(f"RUN   {out_dir}")
        print(f"      counts={counts}")
PY

section "Useful Commands"
cat <<'EOF'
Preprocess one DB:
  bash baselines/text2sql/22_chess/scripts/preprocess_one_db.sh california_schools

Run current SDS smoke/pilot file:
  bash baselines/text2sql/22_chess/scripts/run_sds_ir_ss_cg.sh

Preprocess SDS DBs with realtime terminal logs:
  bash baselines/text2sql/22_chess/scripts/preprocess_dbs_realtime.sh sds

Run SDS IR_SS_CG with realtime terminal logs:
  bash baselines/text2sql/22_chess/scripts/run_ir_ss_cg_realtime.sh --dataset sds --shard-size 10

Run this status check:
  bash baselines/text2sql/22_chess/scripts/check_status.sh
EOF
