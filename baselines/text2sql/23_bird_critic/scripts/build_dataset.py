#!/usr/bin/env python3
"""Build the BIRD-CRITIC-1.0-Open working set.

Pulls the public split from the HuggingFace datasets-server (stdlib only, no
pyarrow/datasets needed), merges the ground truth received by email
(``sol_sql`` + ``test_cases``), and writes two JSONL files:

* ``open_full_600.jsonl``   -- every released instance
* ``open_noeff_570.jsonl``  -- ``efficiency == false`` only, i.e. the 570 the
  paper and the leaderboard report on

The GT file is never copied into the repo tree; it is read from the dataset
store under ``datasets/text2sql/bird_critic/gt/``.
"""

import json
import os
import sys
import urllib.request

DATASET = "birdsql/bird-critic-1.0-open"
CONFIG = "default"
SPLIT = "open"
PAGE = 100

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GT_PATH = os.path.join(
    REPO_ROOT, "datasets", "text2sql", "bird_critic", "gt",
    "BIRD-Critic-sol", "open", "open_sol.jsonl",
)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_rows():
    """Page through datasets-server and return the public records in order."""
    rows = []
    offset = 0
    while True:
        url = (
            "https://datasets-server.huggingface.co/rows"
            f"?dataset={urllib.parse.quote(DATASET, safe='')}"
            f"&config={CONFIG}&split={SPLIT}&offset={offset}&length={PAGE}"
        )
        with urllib.request.urlopen(url, timeout=120) as resp:
            payload = json.load(resp)
        batch = payload.get("rows", [])
        if not batch:
            break
        rows.extend(item["row"] for item in batch)
        total = payload.get("num_rows_total")
        offset += len(batch)
        print(f"  fetched {len(rows)}/{total}")
        if total is not None and len(rows) >= total:
            break
    return rows


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def split_by_dialect(records):
    """Group by dialect and merge the per-instance schema.

    Same contract as the repo's ``baseline/data/pull_data.py`` (schema fields
    first, record fields win on conflict), reimplemented here because that
    script imports ``datasets`` at module level and the repo root has a
    ``datasets/`` directory that shadows the package. Filenames match what
    ``generate_prompt.sh`` and the evaluation scripts expect.
    """
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "code", "baseline", "data", "open_schema.jsonl"
    )
    schema_map = {r["instance_id"]: r for r in load_jsonl(schema_path)}

    names = {
        "PostgreSQL": "postgresql",
        "MySQL": "mysql",
        "SQLServer": "mssql",
        "Oracle": "oracle",
    }

    print("\nno-efficiency set by dialect:")
    for dialect, stem in names.items():
        subset = [r for r in records if r.get("dialect") == dialect]
        merged = [{**schema_map.get(r["instance_id"], {}), **r} for r in subset]
        no_schema = [r["instance_id"] for r in merged if "preprocess_schema" not in r]
        out = os.path.join(OUT_DIR, "by_dialect", f"{stem}_{len(merged)}.jsonl")
        dump_jsonl(merged, out)
        flag = f"  MISSING SCHEMA: {len(no_schema)}" if no_schema else ""
        print(f"  {dialect:<12} {len(merged):>3} -> {os.path.basename(out)}{flag}")


def main():
    if not os.path.isfile(GT_PATH):
        sys.exit(f"GT not found at {GT_PATH} -- unzip open_sol.zip first")

    print("Fetching public split from datasets-server...")
    public = fetch_rows()
    print(f"public rows: {len(public)}")

    gt = load_jsonl(GT_PATH)
    gt_map = {rec["instance_id"]: rec for rec in gt}
    print(f"gt rows: {len(gt)}")

    merged = []
    missing = []
    for rec in public:
        iid = rec.get("instance_id")
        gt_rec = gt_map.get(iid)
        if gt_rec is None:
            missing.append(iid)
            continue
        merged.append({**rec, "sol_sql": gt_rec["sol_sql"], "test_cases": gt_rec["test_cases"]})

    if missing:
        print(f"WARNING: {len(missing)} instances without GT: {missing[:10]}")

    noeff = [r for r in merged if not r.get("efficiency")]

    full_path = os.path.join(OUT_DIR, "open_full_600.jsonl")
    noeff_path = os.path.join(OUT_DIR, "open_noeff_570.jsonl")
    dump_jsonl(merged, full_path)
    dump_jsonl(noeff, noeff_path)

    print(f"\nwrote {len(merged):>4} -> {os.path.normpath(full_path)}")
    print(f"wrote {len(noeff):>4} -> {os.path.normpath(noeff_path)}")

    split_by_dialect(noeff)


if __name__ == "__main__":
    main()
