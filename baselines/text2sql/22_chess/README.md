# CHESS Baseline Reproduction

Paper: `arXiv:2405.16755`, "CHESS: Contextual Harnessing for Efficient SQL Synthesis".

Official code: https://github.com/ShayanTalaei/CHESS

Local clone:

- `code/CHESS`
- commit: `3d6e835f858d26885d21d4bc0215aeecf855efbe`

## What This Baseline Reproduces

The paper evaluates CHESS on BIRD, Spider, and an SDS subset of BIRD dev. The
smallest paper-aligned pilot is SDS:

- Dataset: `code/CHESS/data/dev/sub_sampled_bird_dev_set.json`
- Size: `147`
- Primary metric: execution accuracy (`EX`)
- Main pilot configuration: `IR_SS_CG`
- Paper reference point: about `64.62` EX on SDS/BIRD dev ablation
- Higher-compute configuration: `IR_CG_UT`
- Higher-compute reference point: about `68.31` EX on BIRD dev/SDS and `71.10` on BIRD test

These are reference targets, not exact acceptance criteria. The upstream repo
warns that LLM nondeterminism and model updates can change outputs.

## Required Data Layout

CHESS expects BIRD-style data under `code/CHESS/data/dev`:

```text
data/dev/dev.json
data/dev/dev_tables.json
data/dev/dev_databases/<db_id>/<db_id>.sqlite
data/dev/dev_databases/<db_id>/database_description/*.csv
```

The cloned repo includes only `sub_sampled_bird_dev_set.json`; it does not ship
the BIRD database files or `dev_tables.json`. Download the BIRD dev package from
the BIRD benchmark site or provide an existing local BIRD dev directory, then
copy or symlink its files into this layout.

For SDS pilot, use:

```bash
cp code/CHESS/data/dev/sub_sampled_bird_dev_set.json code/CHESS/data/dev/dev.json
```

Do this only after `dev_databases/` and `dev_tables.json` are available.

## Setup

From the repo root:

```bash
bash baselines/text2sql/22_chess/scripts/configure_env.sh
bash baselines/text2sql/22_chess/scripts/setup_conda_env.sh
conda run -n chess python baselines/text2sql/22_chess/scripts/preflight.py
```

`configure_env.sh` creates `code/CHESS/.env` from `.env` or environment
variables. It does not print API keys.

Use `CHESS_CONDA_ENV=<name>` or `CHESS_PYTHON_VERSION=<version>` when you want a
different conda environment name or Python version.

## Smoke

After preflight reports the BIRD files are present:

```bash
cd baselines/text2sql/22_chess/code/CHESS
../../scripts/preprocess_one_db.sh california_schools
../../scripts/run_sds_ir_ss_cg.sh
```

For a minimal smoke, edit `run/run_preprocess.sh` temporarily to set one
`db_id`, and use a tiny `dev.json` containing only matching SDS rows. Do not
record this as paper reproduction; record it as infrastructure smoke.

## Pilot Gate

Pilot acceptance before any full run:

- `preflight.py` status is `PASS` or `PASS_WITH_WARNINGS`.
- preprocessing completes for every SDS database.
- `IR_SS_CG` completes on all 147 SDS examples.
- result artifacts include per-question JSON, logs, args JSON, and statistics JSON.
- EX is computed with the BIRD/CHESS execution environment and reported with
  model/config/commit/date.

Full BIRD dev/test runs remain gated until the SDS pilot is accepted.

## Current Status

- BIRD dev data is centralized at `datasets/text2sql/bird`.
- MAC-SQL keeps its old path through a symlink.
- CHESS uses symlinks from `code/CHESS/data/dev` to the centralized BIRD
  `dev_databases/` and `dev_tables.json`.
- Conda env `chess` with Python `3.11.15` has the upstream requirements installed.
- `preflight.py` passes with no warnings.
- One-DB preprocess smoke passed for `california_schools`.
- SDS pilot and full BIRD runs have not been executed.
