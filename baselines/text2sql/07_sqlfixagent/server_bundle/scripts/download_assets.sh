#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../SQLFixAgent_code"
mkdir -p model

python -m pip install -q gdown huggingface_hub

if [ ! -d data ]; then
  gdown 1-24BgxgyRRroZkTJ9tpF3jmTggvj7fZp -O data.zip
  unzip -q data.zip
fi

if [ ! -d sic_ckpts ]; then
  gdown 1V3F4ihTSPbV18g3lrg94VMH-kbWR_-lY -O sic_ckpts.zip
  unzip -q sic_ckpts.zip
fi

if [ ! -d model/codes-3b-spider ]; then
  hf download seeklhy/codes-3b-spider --local-dir model/codes-3b-spider
fi

if [ ! -d model/sup-simcse-roberta-base ]; then
  hf download princeton-nlp/sup-simcse-roberta-base --local-dir model/sup-simcse-roberta-base
fi

