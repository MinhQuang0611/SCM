#!/usr/bin/env bash
set -euo pipefail

BASELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
ENV_NAME="${CHESS_CONDA_ENV:-chess}"
PYTHON_VERSION="${CHESS_PYTHON_VERSION:-3.11}"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is not available on PATH" >&2
  exit 2
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -n "$ENV_NAME" "python=$PYTHON_VERSION" -y
fi

conda run -n "$ENV_NAME" python -m pip install --upgrade pip setuptools wheel
conda run -n "$ENV_NAME" python -m pip install -r "$CHESS_DIR/requirements.txt"

echo "Created/updated conda env: $ENV_NAME"
conda run -n "$ENV_NAME" python --version

