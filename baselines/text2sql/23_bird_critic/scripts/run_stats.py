#!/usr/bin/env python3
"""Detailed statistics for a BIRD-CRITIC run.

Joins generation output (tokens, latency, truncation) with evaluation status
and the per-instance report, then breaks results down by dialect, category,
database and answer length.
"""

import argparse
import glob
import json
import os
import re
from collections import Counter, defaultdict

PRICE_IN = 2.5 / 1e6
PRICE_OUT = 10.0 / 1e6


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def pct(a, b):
    return f"{a / b * 100:.1f}%" if b else "-"


def sr(passed, n):
    return f"{passed}/{n} = {passed / n * 100:.1f}%" if n else "-"


def phase_map(report_dir):
    """instance_id -> 'execution' | 'assertion' | 'timeout', parsed from reports.

    Upstream's reports are not consistent across dialects: PostgreSQL labels
    every failure with `Eval Phase: ...`, SQL Server uses `Sol Phase: ...` and
    only labels execution errors, and MySQL labels nothing per instance. Phase
    coverage is therefore partial and is reported alongside the numbers rather
    than silently counted as zero.
    """
    phases = {}
    for path in glob.glob(os.path.join(report_dir, "*_report.txt")):
        for line in open(path, "r", encoding="utf-8"):
            m = re.match(r"Question_(\S+?):", line.strip())
            if not m:
                continue
            iid = m.group(1)
            if "Execution Error" in line:
                phases[iid] = "execution"
            elif "Assertion Error" in line:
                phases[iid] = "assertion"
            elif "Timeout" in line:
                phases[iid] = "timeout"
    return phases


def table(title, rows, headers):
    print(f"\n## {title}")
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen_dir", required=True)
    parser.add_argument("--status_dir", required=True)
    parser.add_argument("--report_dir", required=True)
    args = parser.parse_args()

    gen = {}
    for path in glob.glob(os.path.join(args.gen_dir, "*_inter.jsonl")):
        for r in load_jsonl(path):
            gen[r["instance_id"]] = r

    status = {}
    for path in glob.glob(os.path.join(args.status_dir, "*_output_with_status.jsonl")):
        for r in load_jsonl(path):
            status[r["instance_id"]] = r.get("status")

    phases = phase_map(args.report_dir)

    recs = []
    for iid, g in gen.items():
        if iid not in status:
            continue
        recs.append(
            {
                "id": iid,
                "dialect": g["dialect"],
                "category": g["category"],
                "db": g["db_id"],
                "ok": status[iid] == "success",
                "phase": phases.get(iid),
                "in": g["usage"]["input_tokens"],
                "out": g["usage"]["output_tokens"],
                "lat": g["latency_s"],
                "cut": bool(g.get("truncated")),
                "ntests": len(g.get("test_cases", [])) or None,
            }
        )

    n = len(recs)
    ok = sum(r["ok"] for r in recs)
    print(f"# BIRD-CRITIC run statistics\n\nscored instances: {n}   passed: {ok}   SR: {ok/n*100:.2f}%")

    # by dialect
    rows = []
    for d in ("PostgreSQL", "MySQL", "SQLServer"):
        g = [r for r in recs if r["dialect"] == d]
        if not g:
            continue
        p = sum(r["ok"] for r in g)
        ex = sum(1 for r in g if r["phase"] == "execution")
        asrt = sum(1 for r in g if r["phase"] == "assertion")
        failed = len(g) - p
        labelled = sum(1 for r in g if r["phase"])
        rows.append([d, len(g), p, f"{p/len(g)*100:.1f}%", ex, asrt, f"{labelled}/{failed}",
                     f"{sum(r['in'] for r in g)*PRICE_IN + sum(r['out'] for r in g)*PRICE_OUT:.2f}"])
    table("SR theo dialect", rows,
          ["dialect", "n", "pass", "SR", "exec_err", "assert_err", "phase_labelled", "cost$"])
    print("\nphase_labelled = so case fail duoc upstream gan nhan phase / tong so fail.")
    print("MySQL khong gan nhan nao, SQLServer chi gan execution -> chi PostgreSQL day du.")

    # by category, PostgreSQL only (the only dialect with full phase labels)
    rows = []
    pg = [r for r in recs if r["dialect"] == "PostgreSQL"]
    for c in sorted({r["category"] for r in pg}):
        g = [r for r in pg if r["category"] == c]
        p = sum(r["ok"] for r in g)
        ex = sum(1 for r in g if r["phase"] == "execution")
        asrt = sum(1 for r in g if r["phase"] == "assertion")
        rows.append([c, len(g), p, f"{p/len(g)*100:.1f}%", ex, asrt])
    table("PostgreSQL: SR + loai loi theo category", rows,
          ["category", "n", "pass", "SR", "exec_err", "assert_err"])

    # SR by category across all dialects (no phase columns -- not available)
    rows = []
    for c in sorted({r["category"] for r in recs}):
        g = [r for r in recs if r["category"] == c]
        p = sum(r["ok"] for r in g)
        rows.append([c, len(g), p, f"{p/len(g)*100:.1f}%"])
    table("SR theo category (ca 3 dialect)", rows, ["category", "n", "pass", "SR"])

    # dialect x category
    rows = []
    for d in ("PostgreSQL", "MySQL", "SQLServer"):
        for c in sorted({r["category"] for r in recs}):
            g = [r for r in recs if r["dialect"] == d and r["category"] == c]
            if not g:
                continue
            p = sum(r["ok"] for r in g)
            rows.append([d, c, len(g), p, f"{p/len(g)*100:.1f}%"])
    table("SR theo dialect x category", rows, ["dialect", "category", "n", "pass", "SR"])

    # by database, worst and best
    by_db = defaultdict(list)
    for r in recs:
        by_db[(r["dialect"], r["db"])].append(r)
    db_rows = []
    for (d, db), g in by_db.items():
        if len(g) < 5:
            continue
        p = sum(r["ok"] for r in g)
        db_rows.append([d, db, len(g), p, p / len(g)])
    db_rows.sort(key=lambda x: x[4])
    table("SR theo database (n>=5, thap nhat truoc)",
          [[a, b, c, d_, f"{e*100:.1f}%"] for a, b, c, d_, e in db_rows],
          ["dialect", "db_id", "n", "pass", "SR"])

    # answer length vs success
    buckets = [(0, 300), (300, 500), (500, 800), (800, 1500), (1500, 10 ** 9)]
    rows = []
    for lo, hi in buckets:
        g = [r for r in recs if lo <= r["out"] < hi]
        if not g:
            continue
        p = sum(r["ok"] for r in g)
        label = f"{lo}-{hi}" if hi < 10 ** 9 else f">{lo}"
        rows.append([label, len(g), p, f"{p/len(g)*100:.1f}%", f"{sum(r['lat'] for r in g)/len(g):.1f}s"])
    table("SR theo do dai cau tra loi (output tokens)", rows,
          ["output_tokens", "n", "pass", "SR", "latency_TB"])

    # number of test cases vs success
    rows = []
    for k in sorted({r["ntests"] for r in recs if r["ntests"]}):
        g = [r for r in recs if r["ntests"] == k]
        p = sum(r["ok"] for r in g)
        rows.append([k, len(g), p, f"{p/len(g)*100:.1f}%"])
    table("SR theo so test case cua instance", rows, ["n_tests", "n", "pass", "SR"])

    # truncated
    cut = [r for r in recs if r["cut"]]
    if cut:
        print(f"\n## Runaway (cham tran 8192): {len(cut)} case, pass {sum(r['ok'] for r in cut)}")
        for r in cut:
            print(f"  {r['id']:<16} {r['category']:<16} out={r['out']:<6} {'PASS' if r['ok'] else 'fail'}")

    # would-be truncation under upstream cap
    over = [r for r in recs if r["out"] > 512]
    p_over = sum(r["ok"] for r in over)
    p_under = sum(r["ok"] for r in recs if r["out"] <= 512)
    n_under = n - len(over)
    print(f"\n## Neu giu tran 512 cua upstream")
    print(f"  se bi cat : {len(over)}/{n} = {len(over)/n*100:.1f}%")
    print(f"  SR nhom >512  : {sr(p_over, len(over))}   (se bi anh huong)")
    print(f"  SR nhom <=512 : {sr(p_under, n_under)}   (khong anh huong)")


if __name__ == "__main__":
    main()
