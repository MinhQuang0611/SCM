#!/usr/bin/env bash
set -euo pipefail

BASELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHESS_DIR="$BASELINE_DIR/code/CHESS"
VENV_DIR="$BASELINE_DIR/.venv"

candidate_pythons() {
  if [ -n "${CHESS_PYTHON:-}" ]; then
    command -v "$CHESS_PYTHON"
    return
  fi
  for candidate in python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
    fi
  done
}

python_bins="$(candidate_pythons | awk '!seen[$0]++')"
if [ -z "$python_bins" ]; then
  echo "No supported Python interpreter found. Install Python 3.10-3.12 with venv support or set CHESS_PYTHON." >&2
  exit 2
fi

created=false
while IFS= read -r python_bin; do
  echo "Trying venv with $python_bin ($("$python_bin" --version))"
  rm -rf "$VENV_DIR"
  if "$python_bin" -m venv "$VENV_DIR"; then
    created=true
    break
  fi
done <<< "$python_bins"

if [ "$created" != true ]; then
  echo "Could not create venv. Install python3.12-venv, python3.11-venv, or python3.10-venv, or set CHESS_PYTHON." >&2
  exit 2
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/python" -m pip install -r "$CHESS_DIR/requirements.txt"

echo "Created CHESS venv at $VENV_DIR"
echo "Python: $("$VENV_DIR/bin/python" --version)"
