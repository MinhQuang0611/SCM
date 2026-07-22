#!/usr/bin/env bash
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../SQLFixAgent_code" && pwd)"
cd "$CODE_DIR"
mkdir -p output .tmp .hf_cache
export TMPDIR="$CODE_DIR/.tmp"
export TRANSFORMERS_CACHE="$CODE_DIR/.hf_cache"

PYTHON="${PYTHON:-$HOME/miniconda3/envs/sqlfixagent/bin/python}"

"$PYTHON" -u run_sqltool.py \
  --llm_path ./model/codes-3b-spider \
  --sic_path ./sic_ckpts/sic_spider \
  --table_num 6 \
  --column_num 10 \
  --train_data_path ./data/sft_spider_train_text2sql.json \
  --dev_data_path ./data/sft_spider_dev_text2sql.json \
  --max_tokens 4096 \
  --max_new_tokens 256 \
  --log_path ./output/sqlfixagent_spider_dev_sqltool_log.txt

