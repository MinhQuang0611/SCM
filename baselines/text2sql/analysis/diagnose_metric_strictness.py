"""Chan doan: bao nhieu 'failure' tren SParC dev thuc ra la artifact cua cach so ket qua?

Doc-only tren run da hoan tat. Chay lai pred_sql/gold_sql tren SQLite local va so
ket qua theo ba muc do chat khac nhau:

  exact       giong result_hash hien tai: dung thu tu cot, dung thu tu hang (da sort hang)
  colperm     bo qua thu tu cot: sort cac o trong moi hang truoc khi so
  projection  chi doi hoi MOI cot cua gold xuat hien trong pred (pred duoc phep thua cot),
              va so hang bang nhau

'projection' la can tren long leo — no bo qua tuong ung hang-voi-hang, nen chi dung
lam CHAN DOAN, khong dung lam metric bao cao.

Khong ghi de bat ky file run nao.
"""

import argparse
import json
import os
import sqlite3
from collections import Counter

RUNS = {
    "04_din_sql": "baselines/text2sql/04_din_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    "06_mac_sql": "baselines/text2sql/06_mac_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    "20_c3sql": "baselines/text2sql/20_c3sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
    "21_dail_sql": "baselines/text2sql/21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
}
DB_ROOT = "datasets/text2sql/sparc/sparc/database"
TIMEOUT_S = 10


def run_sql(db_id, sql):
    path = os.path.join(DB_ROOT, db_id, f"{db_id}.sqlite")
    if not sql or not os.path.exists(path):
        return None
    try:
        con = sqlite3.connect(path, timeout=TIMEOUT_S)
        con.text_factory = lambda b: b.decode("utf-8", "replace")
        cur = con.execute(sql)
        rows = cur.fetchall()
        con.close()
        return [tuple("" if c is None else str(c) for c in r) for r in rows]
    except Exception:
        return None


def m_exact(g, p):
    return sorted(g) == sorted(p)


def m_colperm(g, p):
    return sorted(tuple(sorted(r)) for r in g) == sorted(tuple(sorted(r)) for r in p)


def m_projection(g, p):
    if len(g) != len(p):
        return False
    if not g:
        return True
    gcols = [Counter(r[i] for r in g) for i in range(len(g[0]))]
    pcols = [Counter(r[i] for r in p) for i in range(len(p[0]))]
    used = set()
    for gc in gcols:
        hit = next((j for j, pc in enumerate(pcols) if j not in used and pc == gc), None)
        if hit is None:
            return False
        used.add(hit)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="baselines/text2sql/analysis/gold_error_audit_20260822")
    args = ap.parse_args()

    data = {}
    for fw, path in RUNS.items():
        for line in open(path, encoding="utf-8"):
            rec = json.loads(line)
            idx = rec["case"]["idx"]
            slot = data.setdefault(idx, {"db_id": rec["case"]["db_id"], "gold_sql": rec.get("gold_sql"), "fw": {}})
            pe, ge = rec.get("pred_exec") or {}, rec.get("gold_exec") or {}
            slot["fw"][fw] = {
                "pred_sql": rec.get("pred_sql"),
                "reported_ok": pe.get("status") == "ok" and ge.get("status") == "ok"
                and bool(pe.get("result_hash")) and pe.get("result_hash") == ge.get("result_hash"),
            }

    gold_cache, stats, per_case = {}, {}, {}
    for fw in RUNS:
        stats[fw] = Counter()

    for idx, v in sorted(data.items()):
        if idx not in gold_cache:
            gold_cache[idx] = run_sql(v["db_id"], v["gold_sql"])
        g = gold_cache[idx]
        marks = {}
        for fw, f in v["fw"].items():
            if f["reported_ok"]:
                stats[fw]["reported_ok"] += 1
                marks[fw] = "ok"
                continue
            stats[fw]["reported_wrong"] += 1
            p = run_sql(v["db_id"], f["pred_sql"])
            if g is None or p is None:
                stats[fw]["not_executable"] += 1
                marks[fw] = "exec_fail"
                continue
            if m_exact(g, p):
                stats[fw]["rescued_exact"] += 1
                marks[fw] = "exact"
            elif m_colperm(g, p):
                stats[fw]["rescued_colperm"] += 1
                marks[fw] = "colperm"
            elif m_projection(g, p):
                stats[fw]["rescued_projection"] += 1
                marks[fw] = "projection"
            else:
                stats[fw]["genuinely_wrong"] += 1
                marks[fw] = "wrong"
        per_case[idx] = marks

    n = len(data)
    out = {
        "n_cases": n,
        "db_root": DB_ROOT,
        "metric_note": "projection la chan doan, khong phai metric bao cao",
        "per_framework": {},
    }
    for fw, c in stats.items():
        wrong = c["reported_wrong"] or 1
        out["per_framework"][fw] = {
            **dict(c),
            "EX_reported": round(c["reported_ok"] / n, 4),
            "EX_if_colperm": round((c["reported_ok"] + c["rescued_exact"] + c["rescued_colperm"]) / n, 4),
            "EX_if_projection": round(
                (c["reported_ok"] + c["rescued_exact"] + c["rescued_colperm"] + c["rescued_projection"]) / n, 4),
            "share_of_failures_rescued": round(
                (c["rescued_exact"] + c["rescued_colperm"] + c["rescued_projection"]) / wrong, 4),
        }

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "metric_strictness.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(args.out_dir, "metric_strictness_per_case.json"), "w", encoding="utf-8") as fh:
        json.dump(per_case, fh, indent=2)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
