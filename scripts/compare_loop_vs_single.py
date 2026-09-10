#!/usr/bin/env python3
"""Compare the iterative repair loop against the single-shot baseline.

Both runs are graded by the same official harness; this only joins their
outputs and reports the three quantities the de-risk experiment was set up to
answer:

1. Success-rate lift, which bounds the headroom a localization signal could
   still add on top of plain execution feedback.
2. The distribution of the round at which the submitted answer stopped
   changing. Mass concentrated on round 1 means later rounds are inert and
   there is no step structure for attribution to work over.
3. The lift split by how the single-shot attempt failed. Execution errors carry
   a database message naming the defect; assertion failures carry none. If the
   loop only recovers the former, that is direct evidence that execution
   feedback helps unevenly -- and locates where a different signal is needed.

Comparison is paired: only instances present in both runs are counted, and the
per-instance outcomes drive a McNemar-style breakdown rather than two
independent rates.
"""

import argparse
import json
import os
import re
from collections import Counter


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def status_map(path):
    return {r["instance_id"]: r.get("status") for r in load_jsonl(path)}


def phase_map(report_path):
    """instance_id -> execution | assertion | timeout, from the harness report."""
    phases = {}
    if not os.path.isfile(report_path):
        return phases
    for line in open(report_path, encoding="utf-8"):
        m = re.match(r"Question_(\S+?):", line.strip())
        if not m:
            continue
        if "Execution Error" in line:
            phases[m.group(1)] = "execution"
        elif "Assertion Error" in line:
            phases[m.group(1)] = "assertion"
        elif "Timeout" in line:
            phases[m.group(1)] = "timeout"
    return phases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--single_status", required=True, help="single-shot *_output_with_status.jsonl")
    ap.add_argument("--single_report", required=True, help="single-shot *_report.txt")
    ap.add_argument("--loop_status", required=True, help="loop *_output_with_status.jsonl")
    ap.add_argument("--loop_traj", required=True, help="loop trajectory jsonl from repair_loop.py")
    args = ap.parse_args()

    single = status_map(args.single_status)
    loop = status_map(args.loop_status)
    phases = phase_map(args.single_report)
    traj = {r["instance_id"]: r for r in load_jsonl(args.loop_traj)}

    ids = sorted(set(single) & set(loop))
    if not ids:
        raise SystemExit("No overlapping instances between the two runs.")

    ok = lambda d, i: d.get(i) == "success"
    s_pass = sum(ok(single, i) for i in ids)
    l_pass = sum(ok(loop, i) for i in ids)

    print(f"paired instances: {len(ids)}\n")
    print("## 1. Success rate")
    print(f"  single-shot : {s_pass}/{len(ids)} = {s_pass/len(ids)*100:.1f}%")
    print(f"  loop (k)    : {l_pass}/{len(ids)} = {l_pass/len(ids)*100:.1f}%")
    print(f"  lift        : {(l_pass-s_pass)/len(ids)*100:+.1f} diem")

    gained = [i for i in ids if not ok(single, i) and ok(loop, i)]
    lost = [i for i in ids if ok(single, i) and not ok(loop, i)]
    print(f"\n  loop cuu duoc : {len(gained)}")
    print(f"  loop lam hong : {len(lost)}   <- vong lap pha ket qua von dung")
    if lost:
        print("    " + ", ".join(lost[:10]))

    print("\n## 2. Vong ma dap an duoc chot (gate)")
    settled = Counter(traj[i]["settled_round"] for i in ids if i in traj)
    tot = sum(settled.values())
    for r, n in sorted(settled.items()):
        print(f"  vong {r}: {n:>3}  ({n/tot*100:>5.1f}%)")
    changed = sum(n for r, n in settled.items() if r > 1)
    print(f"  doi dap an sau vong 1: {changed}/{tot} = {changed/tot*100:.1f}%")

    print("\n## 3. Lift tach theo cach single-shot that bai")
    for cls in ("execution", "assertion", "timeout"):
        sub = [i for i in ids if not ok(single, i) and phases.get(i) == cls]
        if not sub:
            continue
        rec = sum(ok(loop, i) for i in sub)
        print(f"  {cls:<10} n={len(sub):<4} loop cuu duoc {rec:>3} = {rec/len(sub)*100:>5.1f}%")
    unknown = [i for i in ids if not ok(single, i) and i not in phases]
    if unknown:
        rec = sum(ok(loop, i) for i in unknown)
        print(f"  {'(no label)':<10} n={len(unknown):<4} loop cuu duoc {rec:>3} = {rec/len(unknown)*100:>5.1f}%")

    print("\n## 4. Chi phi")
    tok = sum(traj[i]["usage"].get("total_tokens", 0) for i in ids if i in traj)
    rounds = sum(traj[i]["n_rounds"] for i in ids if i in traj)
    print(f"  tong token loop : {tok:,}")
    print(f"  so luot goi LLM : {rounds} (trung binh {rounds/len(ids):.2f}/case)")


if __name__ == "__main__":
    main()
