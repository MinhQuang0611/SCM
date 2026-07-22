# SQLFixAgent Server Bundle

Folder nay dung de chuyen SQLFixAgent sang server GPU manh hon.

## Da chuan bi trong bundle

- `SQLFixAgent_code/`: official SQLFixAgent code, da patch nhe de chay duoc trong env Python 3.8.
- `scripts/setup_env.sh`: tao/cai env `sqlfixagent`.
- `scripts/download_assets.sh`: tai official data, SIC checkpoints, CodeS-3B Spider, SimCSE model.
- `scripts/run_spider_dev_sqltool.sh`: chay SQLTool official tren Spider-dev.
- `.env.example`: mau bien moi truong, khong chua API key that.

## Patch da apply so voi official repo

- `core/api_config.py`: doc `.env`/environment, uu tien `OPENAI_API_KEY_2` hoac `API_KEY_2`, model mac dinh `gpt-4o-mini`.
- `core/llm.py`: sua cu phap `with (...)` ve Python 3.8-compatible.
- `run_sqltool.py`: append checkpoint JSONL sau moi case vao `output/*_sqltool_checkpoint.jsonl`.

## Assets khong copy vao bundle

Local folder goc hien co khoang 64GB, nen bundle khong copy:

- `data.zip`, `data/`
- `sic_ckpts.zip`, `sic_ckpts/`
- `model/`
- `.hf_cache/`, `.tmp/`, `output/`

Tai lai tren server bang:

```bash
cd SQLFixAgent_code
bash ../scripts/download_assets.sh
```

## Setup tren server

```bash
cd server_bundle
cp .env.example SQLFixAgent_code/.env
# sua SQLFixAgent_code/.env va dien OPENAI_API_KEY_2
bash scripts/setup_env.sh
cd SQLFixAgent_code
bash ../scripts/download_assets.sh
bash ../scripts/run_spider_dev_sqltool.sh
```

## Dieu kien server

- GPU NVIDIA, khuyen nghi VRAM >= 24GB cho CodeS-3B Spider.
- Conda.
- Network ra Google Drive va HuggingFace.
- Neu server co `git-lfs` thi tot, nhung script dung `hf download` nen khong bat buoc.

## Output ky vong

- Checkpoint tung case: `SQLFixAgent_code/output/sft_spider_dev_text2sql_sqltool_checkpoint.jsonl`
- SQLTool final prediction: `SQLFixAgent_code/codes-3b-spider_pred_spider_dev.txt`
- Official Spider evaluation stdout trong terminal.

Neu chay tiep phase fix:

```bash
cd SQLFixAgent_code
bash ../scripts/run_spider_dev_fix.sh
```

