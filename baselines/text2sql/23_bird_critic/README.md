# BIRD-CRITIC 1.0 Open

Reference: [23] J. Li et al., "SWE-SQL: Illuminating LLM Pathways to Solve User SQL Issues in
Real-World Applications," NeurIPS 2025 Main. arXiv:2506.18951.

Upstream: https://github.com/bird-bench/BIRD-CRITIC-1 · Project: https://bird-critic.github.io/

Role: **SQL issue diagnosis/repair** evaluation surface. Unlike the other baselines here, the task
is not generating SQL from a question — it is repairing a user's broken SQL given their bug report.
Adopted after the 2026-08-10 meeting; plan in [`notes/plan_week_2026-08-11.md`](../../../notes/plan_week_2026-08-11.md).

## Task shape

Each instance gives the model a user complaint (`query`) plus the failing SQL (`issue_sql`) and asks
for a fix. Scoring is **behavioural**: `test_cases` are Python functions
(`test_case(pred_sqls, sol_sql, db_name, conn)`) that execute the prediction and assert on resulting
database state. An instance counts as success only if **all** its test cases pass. `sol_sql` is a
reference fix, *not* an output to diff against.

This is why `preprocess_sql` / `clean_up_sql` are mandatory: tests write to the database, so state
leaks between instances if teardown is skipped.

## Dataset

Two halves, joined on `instance_id`:

| Half | Source | Fields |
|---|---|---|
| Public | HuggingFace `birdsql/bird-critic-1.0-open` | `dialect`, `version`, `instance_id`, `db_id`, `query`, `issue_sql`, `preprocess_sql`, `clean_up_sql`, `category`, `efficiency` |
| Ground truth | email auto-reply, `bird.bench25@gmail.com` subject `[bird-critic-1 GT&Test Cases]` | `instance_id`, `sol_sql`, `test_cases` |

GT received 2026-08-12, stored at `datasets/text2sql/bird_critic/gt/` and **gitignored** — BIRD
withholds these fields to prevent leakage into training data, so they must not be committed or
redistributed.

### n = 600 vs the 570 in the paper

The released split has **600** instances. The GT bundle's `readme.md` lists **30 efficiency tasks**
to skip; 600 − 30 = **570**, the number the paper and leaderboard report. All 30 carry
`efficiency == true`, so filtering on that flag reproduces the list exactly — no need to hardcode
ids. (The bundle labels that list `BIRD-CRITIC-1.0-PG`, but it contains MySQL/Oracle/SQLServer ids
too; it is the Open list.)

**Reporting rule:** default to the 570 no-efficiency set. Any run over all 600 must state n
explicitly, because the two are not comparable to the leaderboard.

Working set after filtering:

| Dialect | n |
|---|---:|
| PostgreSQL | 276 |
| MySQL | 98 |
| SQL Server | 98 |
| Oracle | 98 |
| **Total** | **570** |

## Layout

```
23_bird_critic/
├── code/                    # upstream clone, byte-identical, gitignored
├── data/                    # merged dataset + prompts + raw outputs, gitignored (contains GT)
│   ├── open_full_600.jsonl
│   ├── open_noeff_570.jsonl
│   ├── by_dialect/          # schema-merged, one file per dialect
│   ├── prompts/             # 570 baseline prompts
│   └── outputs/
├── docker/
│   └── compose.all-dialects.yml
├── scripts/
│   ├── build_dataset.py
│   └── run_cohere.py
└── results/                 # run_manifest.json + predictions, GT stripped
```

## Deviations from upstream

`code/` is left unmodified. Everything below is additive, in `scripts/` or `docker/`.

**1. `baseline/data/pull_data.py` not used.** It does `from datasets import load_dataset` at module
level, which fails here: the package is not installed, and this repo has a `datasets/` directory at
its root that shadows the name. Its actual job — group by dialect, merge `open_schema.jsonl` by
`instance_id`, record fields winning on conflict — is reimplemented in `scripts/build_dataset.py`
with the same contract and output filenames. That script also pulls the public split through the
HuggingFace datasets-server REST API (stdlib only), avoiding `datasets`/`pyarrow` entirely.

**2. `baseline/src/call_api.py` not used.** Three reasons:

- it dispatches on substrings of the model name (`gpt` / `claude` / `gemini`) and raises on anything
  else, so `command-r-plus-*` cannot run through it;
- `api_request` retries inside a bare `while True` with no cap — a permanent 4xx spins forever;
- it stores only the final string, while this project needs the full per-step trajectory.

`scripts/run_cohere.py` replaces it: OpenAI SDK pointed at Cohere's compatibility endpoint
(`https://api.cohere.ai/compatibility/v1`), bounded retry with backoff, no retry on 400/401/403/404/422,
resumable by `instance_id`, and it records `prompt_flow`, `usage`, `latency_s`, `call_error`.

`temperature=0` and `top_p=1` match upstream. **`max_tokens` is deliberately not sent.**

Upstream caps every call at 512 output tokens. That value is undocumented — it appears nowhere in
their README or `run_baseline.sh`; it is the default of the `call_api_model` parameter
(`call_api.py:116`), and `run_baseline.sh` never overrides it, so every number produced by the
shipped script is generated under that cap.

**The cap truncates a lot and changes almost nothing.** Both settings were run over the full 472
instances with `command-a-03-2025` and graded by the same harness:

| | Truncated | No parseable SQL | Success rate |
|---|---:|---:|---:|
| No cap | 7 (1.5%) | 0 | 131/472 = 27.75% |
| `max_tokens=512` | 140 (29.7%) | 18 (3.8%) | 136/472 = 28.81% |

Paired per instance: 19 instances flipped to correct under the cap, 14 flipped to wrong, net +5.
McNemar χ²(cc) = 0.48, **not significant**. Restricting to the 142 instances whose uncapped answer
exceeded 512 tokens — every one of them cut mid-statement under the cap — pass counts were 19 versus
20. Cutting 142 answers off mid-statement moved the needle by one instance.

Note also that the 330 instances the cap could not have touched scored 112 versus 116, so
run-to-run variance is around ±4 instances even at `temperature=0`; the whole +5 net sits inside it.

The explanation is that long answers were already failing: success rate among answers over 512
tokens was 13.4%, against 33.9% below. **Answer length is a symptom of the model being lost, not a
cause of failure**, so truncating a lost answer costs little. An earlier version of this README
claimed the cap was a significant hidden defect; the paired run does not support that.

The cap is still worth knowing about — it is undocumented, it destroys 18 responses outright, and it
would matter for a model whose long answers were actually good. It is simply not what separates
success from failure here.

Note the token count alone cannot detect this — a capped answer reports 511, not 512, so a
`>= max_tokens` test misses every one. `run_cohere.py` records `finish_reason` and a `truncated`
flag instead. Pass `--max_tokens 512` to reproduce upstream's hidden limit.

**3. `docker/compose.all-dialects.yml`.** Upstream ships `docker-compose.yml` with `mysql`,
`postgresql` and `oracle` commented out — only `mssql` is active. Open needs all four. The override
re-enables them instead of editing the clone.

**4. API key.** `.env` holds an OpenAI-format key in `API_KEY`; the Cohere key is `API_KEY_2`.
`run_cohere.py` reads `COHERE_API_KEY` → `CO_API_KEY` → `API_KEY_2`.

**5. `docker/init-databases_mssql.sh`.** Upstream's SQL Server entrypoint waits a fixed `sleep 15`
then runs `sqlcmd` under `set -e`. SQL Server 2022 takes longer than that on first boot here
(it upgrades its `model` database), so the first `sqlcmd` failed with `Login timeout expired` /
TCP `0x2749` and the container exited 1 before restoring a single `.bak`. The patched copy replaces
the fixed sleep with a readiness poll capped at 300s; the rest is byte-for-byte upstream. Mounted
over `/usr/config/entrypoint.sh` through the compose override.

## Environment gotchas

**Line endings.** The machine had `core.autocrlf=true`, so cloning rewrote every `.sh` in
`evaluation/env/` to CRLF. Containers then died with `cannot execute: required file not found` —
the shebang had become `#!/bin/bash\r`. Fixed by `git config core.autocrlf false` in the clone
followed by a re-checkout, which restores the upstream bytes. Any future clone of a repo whose
shell scripts run inside containers needs the same treatment.

**Oracle cannot run on this machine.** `Dockerfile.oracle` builds `FROM 3036197201/oracle19:latest`,
which is published **arm64 only** (`docker image inspect` → `Architecture=arm64`); the Dockerfile
comment confirms it is a MacOS convenience image. On this x86_64 host every `RUN` fails with exit
255. Upstream's alternative is `oracle/database:19.3.0-ee`, which must be built from Oracle's own
docker-images repo with binaries downloaded under an Oracle license.

Consequence: the 98 Oracle instances cannot be scored here without that separate build. Any run
covering only the other three dialects is **partial coverage of Open (472/570)** and must be
reported as such — per-dialect success rates differ, so a partial average is not comparable to the
leaderboard.

## `prompt_flow` doubles as the submission format

BIRD-CRITIC's submission guidelines require `instance_id`, `predicted_sql`, and `prompt_flow` — a
list of `{model, prompt, response}` per step. That is the same shape as this project's `stage_logs`,
so one file serves both attribution input and leaderboard submission. Note the two email channels
share an address but differ: dataset requests use `[bird-critic-1 GT&Test Cases]` (bot), submissions
use `[BIRD-CRITIC-1.0-{split}][Team Name][Method Name]` (human review). Leaderboard entries are
re-run in BIRD's own environment before receiving a "Verified" badge, so locally computed numbers
and leaderboard numbers are not automatically comparable.

## Reproduce

```bash
cd baselines/text2sql/23_bird_critic
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install openai tqdm gdown

# 1. dataset: public split + GT, filtered to 570, split by dialect with schema
python scripts/build_dataset.py

# 2. prompts (upstream generator, unmodified)
./.venv/Scripts/python.exe code/baseline/src/prompt_generator.py \
  --data_path data/by_dialect/postgresql_276.jsonl \
  --prompt_path data/prompts/postgresql_prompts.jsonl \
  --prompt_type baseline --schema_field preprocess_schema --dialect postgresql

# 3. generation
./.venv/Scripts/python.exe scripts/run_cohere.py \
  --prompt_path data/prompts/postgresql_prompts.jsonl \
  --output_path data/outputs/<run_id>/postgresql_inter.jsonl

# 4. extract pred_sqls (upstream post-processor, unmodified)
./.venv/Scripts/python.exe code/baseline/src/post_process.py \
  --input_path data/outputs/<run_id>/postgresql_inter.jsonl \
  --output_path data/outputs/<run_id>/postgresql_final.jsonl

# 5. databases + evaluation container
./.venv/Scripts/python.exe -m gdown --folder \
  "https://drive.google.com/drive/folders/1nJReLrvZVVrnfgBYwwNEgYvLroPGbcPD" -O code/evaluation/_drive
# unzip into code/evaluation/{postgre,mysql,mssql,oracle}_table_dumps
docker compose -f code/evaluation/docker-compose.yml -f docker/compose.all-dialects.yml up --build -d

# 6. evaluate, once per dialect (inside so_eval_env, set dialect in run_eval.sh)
```

## Status

Adapted local run, **not** an official reproduction — see repo-wide convention.

Recorded as of 2026-08-12; anything not listed here has not been run.

| Step | State |
|---|---|
| Dataset merged (600 / 570) | done, all 600 matched a GT record |
| Prompts generated | done, 570 |
| Cohere connectivity | done, 1-call probe, no error |
| Smoke generation n=24 (6/dialect) | done, `call_error` 0/24; 23/24 yielded a parseable SQL block |
| DB dumps downloaded + unzipped | done, 652 MB archives → PG 1.2G / MySQL 995M / MSSQL 1.3G / Oracle 47M |
| Docker services | PostgreSQL, MySQL, SQL Server up and initialised; Oracle not runnable (see above) |
| Smoke evaluation | done, `results/smoke_open_3dialect_n18_commandrplus_20260812/` |
| Full 570 run | not started — awaiting cost approval |

### Full run, `command-a-03-2025`, no `max_tokens` cap, n=472

`results/full_open_3dialect_n472_commanda_nocap_20260812/`

| Dialect | passed / n | SR | Exec err | Assert err | Timeout |
|---|---:|---:|---:|---:|---:|
| PostgreSQL | 69 / 276 | 0.2500 | 88 | 117 | 2 |
| MySQL | 33 / 98 | 0.3367 | 24 | 41 | 0 |
| SQL Server | 29 / 98 | 0.2959 | 24 | 45 | 0 |
| **Total** | **131 / 472** | **0.2775** | 136 | 203 | 2 |

Generation: 0 call errors, 0 unparseable responses, 1.42M input + 297K output tokens, $6.52,
mean latency 11.6s. **Partial coverage — the 98 Oracle instances are missing**, so this is not
comparable to a leaderboard figure computed over all 570.

Failures split roughly 60/40 between answers that return wrong results (203 assertion errors) and
answers that do not run at all (136 execution errors).

#### The hidden 512 cap truncates a third of answers and changes nothing

Both configurations were run over the same 472 instances and graded by the same harness.

| | max_tokens=512 (upstream default) | no cap |
|---|---:|---:|
| PostgreSQL | 74/276 = 26.81% | 69/276 = 25.00% |
| MySQL | 33/98 = 33.67% | 33/98 = 33.67% |
| SQL Server | 29/98 = 29.59% | 29/98 = 29.59% |
| **Total** | **136/472 = 28.81%** | 131/472 = 27.75% |
| Answers truncated | 140 (29.7%) | 7 (1.5%) |
| Answers yielding no parseable SQL | 18 (3.8%) | 0 |

Paired per-instance outcomes: 19 instances pass only under the cap, 14 pass only without it, 322
fail both, 117 pass both. McNemar exact **p = 0.487** — the 1.06-point difference is noise.

So the cap does truncate 29.7% of answers and does destroy 18 answers entirely, yet **it does not
measurably move the success rate**. The explanation is consistent with the length-vs-success
relationship above: answers longer than 512 tokens score 13.4% versus 33.9% for shorter ones, so
the cap mostly truncates answers that were already going to fail. Verbosity is a symptom of the
model struggling, not a resource being cut short.

The defensible criticism is therefore about transparency, not validity: `max_tokens=512` is set by
a function default in `call_api.py` and appears in no documentation, so anyone running
`run_baseline.sh` is silently capped without knowing it. It is not a source of measurement error.

#### Runaway generations

7 answers hit command-a's own 8192-token ceiling. Inspection shows these are degenerate repetition
loops, not long legitimate fixes — `PostgreSQL_1` emits the same SELECT under a repeated heading
"Final and Most Correct SQL" until it runs out of tokens. Raising the cap cannot help this class;
it is a distinct failure mode (the model loses the ability to stop) worth naming separately in a
failure taxonomy.

#### PostgreSQL execution errors, classified

All 88 replayed inside a rolled-back transaction to capture the real error text
(`code/evaluation/data/err_probe.py`); all 88 reproduced.

| Root cause | n | % |
|---|---:|---:|
| Type reasoning (wrong type, cast failure, missing operator) | 30 | 34% |
| Syntax | 21 | 24% |
| Schema linking (column or relation does not exist) | 15 | 17% |
| SQL semantic rules (nested aggregates, GROUP BY) | 12 | 14% |
| Dialect function signatures | 8 | 9% |

Type reasoning dominates, not schema linking. The model generally picks the right tables and
columns but misjudges their types — `column "date" is of type bigint but expression is of type
date`, `operator does not exist: date - bigint`, `function array_length(text[]) does not exist`.
PostgreSQL names the defect precisely in each case, so an execute-and-read-the-error loop should
recover most of this class. The 203 assertion errors are the harder group: the SQL runs, the
database reports nothing, and only the test cases reveal the answer is wrong.

### Smoke result, `command-r-plus-08-2024`, n=18 scored

| Dialect | passed / n | SR |
|---|---:|---:|
| PostgreSQL | 1 / 6 | 0.1667 |
| MySQL | 4 / 6 | 0.6667 |
| SQL Server | 2 / 6 | 0.3333 |
| **Scored total** | **7 / 18** | **0.3889** |
| Oracle | — | generated but not evaluated |

18 of the 24 generated instances were scored; the 6 Oracle ones have predictions but no runnable
server. 73,847 tokens total. **This is a 6-instance-per-dialect smoke, not a measurement** — the
confidence interval at n=6 spans most of the unit interval, so it says the pipeline works end to
end, nothing about where this model lands relative to the leaderboard.
