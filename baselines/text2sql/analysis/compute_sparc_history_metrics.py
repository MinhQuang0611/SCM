#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import sqlite3
import time
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[3]
SPARC_DB_ROOT = ROOT / "datasets/text2sql/sparc/sparc/database"
ITERATE_NUM = 30
CASE_TIMING_CAP_S = 1.0
PRICE_INPUT_PER_M = 0.15
PRICE_OUTPUT_PER_M = 0.60

RUNS = [
    (
        "04_din_sql",
        ROOT / "baselines/text2sql/04_din_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    ),
    (
        "06_mac_sql",
        ROOT / "baselines/text2sql/06_mac_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    ),
    (
        "20_c3sql",
        ROOT / "baselines/text2sql/20_c3sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
    ),
    (
        "21_dail_sql",
        ROOT / "baselines/text2sql/21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
    ),
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_ex(row: dict) -> bool:
    return (
        row.get("pred_exec", {}).get("status") == "ok"
        and row.get("gold_exec", {}).get("status") == "ok"
        and row.get("pred_exec", {}).get("result_hash")
        == row.get("gold_exec", {}).get("result_hash")
    )


def usage_and_latency(row: dict) -> tuple[int, int, int, float]:
    usage = row.get("usage")
    if usage:
        return (
            int(usage.get("input_tokens") or 0),
            int(usage.get("output_tokens") or 0),
            int(usage.get("total_tokens") or 0),
            float(row.get("latency_s") or 0.0),
        )
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    latency_s = 0.0
    for trace in row.get("stage_logs") or []:
        trace_usage = trace.get("usage") or {}
        input_tokens += int(trace_usage.get("input_tokens") or 0)
        output_tokens += int(trace_usage.get("output_tokens") or 0)
        total_tokens += int(trace_usage.get("total_tokens") or 0)
        latency_s += float(trace.get("latency_s") or 0.0)
    return input_tokens, output_tokens, total_tokens, latency_s


def db_path(row: dict) -> Path:
    db_id = row["case"]["db_id"]
    return SPARC_DB_ROOT / db_id / f"{db_id}.sqlite"


def run_sql_once(db_file: Path, sql: str) -> float:
    start = time.perf_counter()
    con = sqlite3.connect(str(db_file))
    try:
        con.execute(sql.replace("! =", "!=")).fetchall()
    finally:
        con.close()
    return time.perf_counter() - start


def avg_time(db_file: Path, sql: str) -> tuple[float, bool]:
    times = []
    capped = False
    for _ in range(ITERATE_NUM):
        try:
            elapsed = run_sql_once(db_file, sql)
        except Exception:
            return CASE_TIMING_CAP_S, True
        if elapsed > CASE_TIMING_CAP_S:
            capped = True
            elapsed = CASE_TIMING_CAP_S
        times.append(elapsed)
    return mean(times), capped


def ves_component(row: dict) -> tuple[float, dict]:
    if not is_ex(row):
        return 0.0, {"correct_set_match": False, "time_ratio": 0.0, "capped": False}
    db_file = db_path(row)
    gold_time, gold_capped = avg_time(db_file, row["gold_sql"])
    pred_time, pred_capped = avg_time(db_file, row["pred_sql"])
    pred_time = max(pred_time, 1e-9)
    ratio = gold_time / pred_time
    component = math.sqrt(ratio) * 100.0
    return component, {
        "correct_set_match": True,
        "gold_avg_s": gold_time,
        "pred_avg_s": pred_time,
        "time_ratio": ratio,
        "capped": gold_capped or pred_capped,
    }


def summarize_one(baseline: str, path: Path, details_dir: Path) -> dict:
    rows = load_jsonl(path)
    details_path = details_dir / f"{baseline}_sparc_history_ves_style_capped_details.jsonl"
    components = []
    details_dir.mkdir(parents=True, exist_ok=True)
    with details_path.open("w", encoding="utf-8") as f:
        for row in rows:
            component, detail = ves_component(row)
            components.append(component)
            f.write(
                json.dumps(
                    {
                        "baseline": baseline,
                        "idx": row["case"]["idx"],
                        "db_id": row["case"]["db_id"],
                        "correct_set_match": detail["correct_set_match"],
                        "ves_component": component,
                        **detail,
                        "gold_sql": row["gold_sql"],
                        "pred_sql": row["pred_sql"],
                        "pred_status": row["pred_exec"]["status"],
                        "pred_error": row["pred_exec"].get("error", ""),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    input_tokens = output_tokens = total_tokens = 0
    latencies = []
    for row in rows:
        inp, out, total, latency = usage_and_latency(row)
        input_tokens += inp
        output_tokens += out
        total_tokens += total
        if latency:
            latencies.append(latency)
    n = len(rows)
    ex_count = sum(is_ex(row) for row in rows)
    executable = sum(row["pred_exec"]["status"] == "ok" for row in rows)
    gold_executable = sum(row["gold_exec"]["status"] == "ok" for row in rows)
    call_errors = sum(1 for row in rows if row.get("call_error"))
    empty_sql = sum(1 for row in rows if not (row.get("pred_sql") or "").strip())
    pred_exec_errors = n - executable
    cost = input_tokens / 1_000_000 * PRICE_INPUT_PER_M + output_tokens / 1_000_000 * PRICE_OUTPUT_PER_M
    return {
        "baseline": baseline,
        "n": n,
        "EX_count": ex_count,
        "EX": ex_count / n if n else 0.0,
        "SEV_count": executable,
        "SEV": executable / n if n else 0.0,
        "pred_exec_error_count": pred_exec_errors,
        "pred_exec_error_rate": pred_exec_errors / n if n else 0.0,
        "gold_executable": gold_executable,
        "empty_sql_count": empty_sql,
        "call_error_count": call_errors,
        "VES_style_capped": mean(components) if components else 0.0,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_est_usd": cost,
        "avg_latency_s": mean(latencies) if latencies else 0.0,
        "predictions": str(path.relative_to(ROOT)),
        "ves_details": str(details_path.relative_to(ROOT)),
    }


def main() -> None:
    out_dir = ROOT / "baselines/text2sql/analysis"
    details_dir = ROOT / "baselines/text2sql/evaluation/ves_style_sparc_history_capped"
    summaries = [summarize_one(name, path, details_dir) for name, path in RUNS]
    csv_path = out_dir / "sparc_history_framework_metrics_summary.csv"
    fieldnames = list(summaries[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    md_path = out_dir / "sparc_history_framework_metrics_report.md"
    lines = [
        "# SParC history-aware framework metrics",
        "",
        f"- n: 1203 turns",
        f"- VES-style capped settings: iterate_num={ITERATE_NUM}, case_timing_cap_s={CASE_TIMING_CAP_S}",
        "- SEV: SQL Execution Validity, i.e. predicted SQL executable rate.",
        "- EX: SQLite result-hash match vs gold SQL.",
        "",
        "| baseline | EX | SEV | SQL exec errors | VES-style capped | call errors | tokens | cost est. |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            "| {baseline} | {EX_count}/{n} = {EX:.4f} | {SEV_count}/{n} = {SEV:.4f} | "
            "{pred_exec_error_count} | {VES_style_capped:.2f} | {call_error_count} | "
            "{total_tokens} | ${cost_est_usd:.4f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- These are adapted local SParC runs, not official paper reproduction scores.",
            "- VES-style is an efficiency diagnostic; micro-timing on small SQLite DBs is noisy.",
            "- MAC-SQL and C3SQL have the same EX count on this SParC history-aware run, while DAIL-SQL is highest by EX but lower by SEV due to more execution errors.",
            "",
            f"CSV: `{csv_path.relative_to(ROOT)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(csv_path)
    print(md_path)


if __name__ == "__main__":
    main()
