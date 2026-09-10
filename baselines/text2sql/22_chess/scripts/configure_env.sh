#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BASELINE_DIR="$ROOT_DIR/baselines/text2sql/22_chess"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
WORKSPACE_ENV="$ROOT_DIR/.env"
TARGET_ENV="$CHESS_DIR/.env"

get_env_value() {
  local key="$1"
  local value="${!key:-}"
  if [ -n "$value" ]; then
    printf '%s' "$value"
    return 0
  fi
  if [ -f "$WORKSPACE_ENV" ]; then
    awk -F= -v k="$key" '
      $0 !~ /^[[:space:]]*#/ && $1 == k {
        sub(/^[^=]*=/, "", $0)
        gsub(/^["'\'']|["'\'']$/, "", $0)
        print $0
        exit
      }
    ' "$WORKSPACE_ENV"
  fi
}

mkdir -p "$CHESS_DIR/data/dev" "$BASELINE_DIR/results"

openai_key="$(get_env_value OPENAI_API_KEY)"
if [ -z "$openai_key" ]; then
  openai_key="$(get_env_value API_KEY)"
fi

cat > "$TARGET_ENV" <<EOF
DATA_MODE=dev
DATA_PATH=./data/dev/dev.json
DB_ROOT_PATH=./data/dev
DB_ROOT_DIRECTORY=./data/dev/dev_databases
DATA_TABLES_PATH=./data/dev/dev_tables.json
INDEX_SERVER_HOST=localhost
INDEX_SERVER_PORT=12345

OPENAI_API_KEY=${openai_key}
GCP_PROJECT=$(get_env_value GCP_PROJECT)
GCP_REGION=$(get_env_value GCP_REGION)
GCP_CREDENTIALS=$(get_env_value GCP_CREDENTIALS)
GOOGLE_CLOUD_PROJECT=$(get_env_value GOOGLE_CLOUD_PROJECT)
EOF

chmod 600 "$TARGET_ENV"
echo "Wrote $TARGET_ENV"
echo "API key present: $( [ -n "$openai_key" ] && echo yes || echo no )"
