#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="$ROOT_DIR/SQLFixAgent_code"

conda create -y -n sqlfixagent python=3.8.5
conda run -n sqlfixagent conda install -y pytorch==1.13.1 pytorch-cuda=11.7 -c pytorch -c nvidia
conda install -y -n sqlfixagent mkl=2023.1.0

cd "$CODE_DIR"
conda run -n sqlfixagent pip install "spacy==3.5.4"
conda run -n sqlfixagent pip install -r requirements.txt

if [ ! -d SimCSE ]; then
  git clone https://github.com/lihaoyang-ruc/SimCSE.git
fi
cd SimCSE
"$HOME/miniconda3/envs/sqlfixagent/bin/python" setup.py install || "$CONDA_PREFIX/envs/sqlfixagent/bin/python" setup.py install

"$HOME/miniconda3/envs/sqlfixagent/bin/python" -m nltk.downloader averaged_perceptron_tagger punkt || true

