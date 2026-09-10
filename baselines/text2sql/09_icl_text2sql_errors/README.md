# A Study of In-Context-Learning-Based Text-to-SQL Errors

Reference: [9] J. Shen et al., "A Study of In-Context-Learning-Based Text-to-SQL Errors,"
in *Proc. ACM Int. Conf. Foundations of Software Engineering (FSE)*, 2026.
(Da accepted FSE 2026 — truoc day note nay ghi nham la 2025.)

Role: error-analysis and taxonomy reference.

Runnable baseline suitability: not a generator baseline by itself.

Why it is relevant: `Text2SQL_Hallucination.pdf` repeatedly uses this work for failure categories and stage-level error framing. It should inform the label set used when comparing the current MAS pipeline with baseline systems.

Use in protocol:

- Align error labels before running baselines.
- Define criteria for skeleton, schema, intent, and execution failures.
- Avoid making unsupported stage-level claims when a baseline does not expose intermediate artifacts.

## Cap nhat 2026-09-10 — MapleRepair va con so mis-repair

Cong trinh nay dong thoi gioi thieu **MapleRepair**, va do la phan quan trong nhat cho
failure attribution:

- **Quy mo error analysis**: `4.602` SQL sai tren `12.340` query sinh ra, tu 4 ky thuat ICL
  (MAC-SQL, DIN-SQL, CHESS, DEA-SQL) x 2 benchmark (Spider dev, BIRD dev) x 2 LLM.
  Taxonomy 7 nhom / 27-29 loai. Gan nhan boi 3 dong tac gia doc lap roi hop nhat bang
  consensus — **khong bao kappa** (khac GBV-SQL 0.86).
- **Chan doan thu hai, dang chu y hon**: 5 phuong phap repair san co deu **mis-repair nhieu**
  (pha case von dung) va ton latency.
- **Ket qua MapleRepair**: repair them `13.8%` query so voi giai phap tot nhat hien co,
  mis-repair "negligible", giam `67.4%` latency.

Day la mot trong bon cong trinh Text-to-SQL peer-reviewed **dong duoc vong**
`chan doan -> sua -> do EX`. Chan doan van la **dem loi thu cong o muc aggregate**
(~840 person-hours), khong phai attribution muc case.

Xem `notes/_search/attribution-to-improvement-evidence-2026-09-10.md` de doi chieu voi
DIN-SQL, TA-SQL, MAGIC va nam bang chung cho thay chan doan aggregate da dan toi can thiep sai.

Con so `4.602` / `13.8%` / `67.4%` moi trich mot lan, **chua doi chieu lai PDF** — khong dung
trong manuscript truoc khi doc lai.
