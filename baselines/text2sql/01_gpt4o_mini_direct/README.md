# GPT-4o-mini Direct

Baseline id: `gpt4o_mini_direct`

Role: anchor direct-prompt baseline for `t2sql_baseline_pilot_v1`.

This is not an official paper reproduction. It is the local anchor baseline used
to verify dataset loading, SQLite execution, logging, and cost/latency accounting
before official paper baselines are adapted.

## Run

```bash
python3 scripts/run_gpt4o_mini_direct_text2sql.py
```

Default output:

```text
baselines/text2sql/01_gpt4o_mini_direct/results/t2sql_baseline_pilot_v1_n50/
```

## Existing Pilot Result

The current pilot was finalized from completed partial outputs without repeating
API calls. Required artifacts:

- `run_manifest.json`
- `predictions.jsonl`
- `logs.jsonl`
- `summary.csv`
- `leaderboard.csv`
- `logging_quality.csv`
- `failure_cases.jsonl`
- `protocol_audit.md`
