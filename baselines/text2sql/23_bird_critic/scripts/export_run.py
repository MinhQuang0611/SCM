#!/usr/bin/env python3
"""Export a BIRD-CRITIC run into the repo's results contract.

Reads the per-dialect generation output (and the evaluation status file when
one exists), then writes ``results/<run_id>/predictions.jsonl`` plus
``run_manifest.json``.

Ground truth is stripped: ``sol_sql`` and ``test_cases`` never reach
``results/``, so that directory stays committable. Everything the attribution
work needs -- ``stage_logs`` / ``prompt_flow``, usage, latency -- is kept.
"""

import argparse
import glob
import json
import os
from datetime import datetime, timezone

GT_FIELDS = ("sol_sql", "test_cases")
DIALECTS = ("postgresql", "mysql", "sqlserver", "oracle")


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def dump_jsonl(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_status(status_dir, dialect):
    """Evaluation writes status.jsonl when run with --logging save."""
    if not status_dir:
        return {}
    matches = glob.glob(os.path.join(status_dir, f"*{dialect}*status*.jsonl"))
    if not matches:
        return {}
    status = {}
    for rec in load_jsonl(matches[0]):
        iid = rec.get("instance_id")
        if iid:
            status[iid] = rec
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs_dir", required=True, help="dir with <dialect>_final.jsonl")
    parser.add_argument("--run_id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--status_dir", default=None, help="dir holding eval status.jsonl files")
    parser.add_argument("--split", default="bird-critic-1.0-open (efficiency excluded)")
    parser.add_argument("--results_root", default=None)
    args = parser.parse_args()

    base = args.results_root or os.path.join(os.path.dirname(__file__), "..", "results")
    run_dir = os.path.join(base, args.run_id)

    predictions = []
    per_dialect = {}

    for dialect in DIALECTS:
        path = os.path.join(args.outputs_dir, f"{dialect}_final.jsonl")
        if not os.path.isfile(path):
            continue
        rows = load_jsonl(path)
        status = load_status(args.status_dir, dialect)

        passed = 0
        scored = 0
        for row in rows:
            iid = row.get("instance_id")
            st = status.get(iid, {})
            success = st.get("success") if "success" in st else st.get("status")
            if success is not None:
                scored += 1
                if success in (True, 1, "success", "passed"):
                    passed += 1

            predictions.append(
                {
                    "baseline": "bird_critic_open",
                    "case": {
                        "instance_id": iid,
                        "db_id": row.get("db_id"),
                        "dialect": row.get("dialect"),
                        "category": row.get("category"),
                        "efficiency": row.get("efficiency"),
                        "query": row.get("query"),
                        "issue_sql": row.get("issue_sql"),
                    },
                    "model": args.model,
                    "pred_sqls": row.get("pred_sqls", []),
                    "eval": {
                        "success": success,
                        "error": st.get("error_message") or st.get("error"),
                        "scored": success is not None,
                    },
                    "call_error": row.get("call_error"),
                    "usage": row.get("usage", {}),
                    "latency_s": row.get("latency_s"),
                    # Logging Matrix: raw per-step trajectory. Same shape as the
                    # prompt_flow BIRD-CRITIC asks for in leaderboard submissions.
                    "stage_logs": {"prompt_flow": row.get("prompt_flow", [])},
                }
            )

        per_dialect[dialect] = {
            "n": len(rows),
            "scored": scored,
            "passed": passed,
            "success_rate": round(passed / scored, 4) if scored else None,
            "empty_pred": sum(1 for r in rows if not r.get("pred_sqls")),
            "call_errors": sum(1 for r in rows if r.get("call_error")),
        }

    pred_path = os.path.join(run_dir, "predictions.jsonl")
    dump_jsonl(predictions, pred_path)

    total_scored = sum(d["scored"] for d in per_dialect.values())
    total_passed = sum(d["passed"] for d in per_dialect.values())
    tokens = sum(p["usage"].get("total_tokens", 0) for p in predictions)

    manifest = {
        "baseline": "bird_critic_open",
        "run_id": args.run_id,
        "status": "PASS" if total_scored else "GENERATION_ONLY",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": args.split,
        "n": len(predictions),
        "model": args.model,
        "run_type": "adapted local run, not an official paper reproduction",
        "metrics": {
            "success_rate": round(total_passed / total_scored, 4) if total_scored else None,
            "scored": total_scored,
            "passed": total_passed,
            "total_tokens": tokens,
            "by_dialect": per_dialect,
        },
        "outputs": {
            "predictions": os.path.relpath(pred_path, run_dir).replace("\\", "/"),
            "generation_dir": os.path.normpath(args.outputs_dir).replace("\\", "/"),
        },
        "notes": [
            "sol_sql and test_cases stripped from predictions.jsonl -- BIRD withholds them.",
            "Generation params are upstream defaults: temperature=0, max_tokens=512, top_p=1.",
        ],
    }

    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    print(f"run_id : {args.run_id}")
    print(f"n      : {len(predictions)}")
    for dialect, stats in per_dialect.items():
        sr = stats["success_rate"]
        sr_txt = "not evaluated" if sr is None else f"SR={sr:.4f} ({stats['passed']}/{stats['scored']})"
        print(f"  {dialect:<12} n={stats['n']:<4} {sr_txt}")
    print(f"\nwrote {os.path.normpath(run_dir)}")


if __name__ == "__main__":
    main()
