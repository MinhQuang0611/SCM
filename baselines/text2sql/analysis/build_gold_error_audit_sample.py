"""Dung sample de audit chat luong nhan (Gold Error) tren SParC dev.

Doc-only tren cac run da hoan tat; khong sua predictions/logs/manifest.

Chien luoc: dung su dong thuan giua 4 framework lam tin hieu uu tien.
Neu ca 4 deu sai va phan lon lai cho CUNG mot ket qua khac gold, kha nang cao
la gold sai chu khong phai ca 4 he cung sai theo mot kieu.

Strata:
  A_all_wrong_agree   ca 4 sai, >=3 framework cho cung result_hash  -> nghi gold sai
  B_all_wrong_diverge ca 4 sai, khong dong thuan                    -> nghi loi that
  C_mixed             co it nhat 1 dung va 1 sai                    -> ranh gioi
  D_all_correct       ca 4 dung                                     -> tim case "dung nho nhan sai"

Typology gan nhan theo GBV-SQL (ACL 2026): A=gold SQL sai, B=cau hoi loi,
C=schema/du lieu ban, none=nhan dung.
"""

import argparse
import csv
import json
import os
import random
from collections import Counter

RUNS = {
    "04_din_sql": "baselines/text2sql/04_din_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    "06_mac_sql": "baselines/text2sql/06_mac_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl",
    "20_c3sql": "baselines/text2sql/20_c3sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
    "21_dail_sql": "baselines/text2sql/21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl",
}

QUOTA = {"A_all_wrong_agree": 30, "B_all_wrong_diverge": 25, "C_mixed": 20, "D_all_correct": 25}
SEED = 20260822


def load(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def is_correct(rec):
    pe, ge = rec.get("pred_exec") or {}, rec.get("gold_exec") or {}
    if pe.get("status") != "ok" or ge.get("status") != "ok":
        return False
    return bool(pe.get("result_hash")) and pe.get("result_hash") == ge.get("result_hash")


def stratum_of(per_fw):
    correct = [k for k, v in per_fw.items() if v["correct"]]
    if len(correct) == len(per_fw):
        return "D_all_correct"
    if correct:
        return "C_mixed"
    hashes = [v["pred_hash"] for v in per_fw.values() if v["pred_hash"]]
    if hashes and Counter(hashes).most_common(1)[0][1] >= 3:
        return "A_all_wrong_agree"
    return "B_all_wrong_diverge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="baselines/text2sql/analysis/gold_error_audit_20260822")
    args = ap.parse_args()

    by_idx = {}
    for fw, path in RUNS.items():
        if not os.path.exists(path):
            raise SystemExit(f"missing run file: {path}")
        for rec in load(path):
            idx = rec["case"]["idx"]
            slot = by_idx.setdefault(idx, {"case": rec["case"], "gold_sql": rec.get("gold_sql"), "fw": {}})
            slot["fw"][fw] = {
                "pred_sql": rec.get("pred_sql"),
                "correct": is_correct(rec),
                "pred_hash": (rec.get("pred_exec") or {}).get("result_hash"),
                "pred_status": (rec.get("pred_exec") or {}).get("status"),
                "pred_error": (rec.get("pred_exec") or {}).get("error"),
                "gold_status": (rec.get("gold_exec") or {}).get("status"),
            }

    complete = {i: v for i, v in by_idx.items() if len(v["fw"]) == len(RUNS)}
    strata = {}
    for idx, v in complete.items():
        strata.setdefault(stratum_of(v["fw"]), []).append(idx)

    rng = random.Random(SEED)
    picked = {}
    for name, idxs in strata.items():
        idxs = sorted(idxs)
        quota = QUOTA.get(name, 0)
        picked[name] = sorted(rng.sample(idxs, min(quota, len(idxs))))

    os.makedirs(args.out_dir, exist_ok=True)
    sheet = os.path.join(args.out_dir, "audit_sheet.csv")
    detail = os.path.join(args.out_dir, "audit_cases.jsonl")

    cols = [
        "stratum", "case_idx", "db_id", "question", "gold_sql",
        "n_correct", "pred_agreement",
        "gold_error_type", "gold_error_note", "annotator",
    ]
    with open(sheet, "w", encoding="utf-8", newline="") as fh, open(detail, "w", encoding="utf-8") as dfh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for name in sorted(picked):
            for idx in picked[name]:
                v = complete[idx]
                hashes = [f["pred_hash"] for f in v["fw"].values() if f["pred_hash"]]
                agree = Counter(hashes).most_common(1)[0][1] if hashes else 0
                w.writerow({
                    "stratum": name,
                    "case_idx": idx,
                    "db_id": v["case"]["db_id"],
                    "question": v["case"]["question"],
                    "gold_sql": v["gold_sql"],
                    "n_correct": sum(1 for f in v["fw"].values() if f["correct"]),
                    "pred_agreement": f"{agree}/{len(RUNS)}",
                    "gold_error_type": "",
                    "gold_error_note": "",
                    "annotator": "",
                })
                dfh.write(json.dumps({"stratum": name, "case_idx": idx, **v}, ensure_ascii=False) + "\n")

    summary = {
        "seed": SEED,
        "n_cases_all_frameworks": len(complete),
        "frameworks": sorted(RUNS),
        "stratum_population": {k: len(v) for k, v in sorted(strata.items())},
        "stratum_sampled": {k: len(v) for k, v in sorted(picked.items())},
        "outputs": {"sheet": sheet, "detail": detail},
        "sources": RUNS,
    }
    with open(os.path.join(args.out_dir, "sample_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
