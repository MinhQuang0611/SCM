# Bao cao chi tiet: DIN-SQL, MAC-SQL, C3SQL, DAIL-SQL tren SParC history-aware

Ngay lap: 2026-07-22

## 1. Pham vi bao cao

Bao cao nay tong hop cac metric cua 4 framework Text-to-SQL tren cung mot setting:

- Dataset: SParC local, duoc adapter theo dang Spider-style turns.
- So mau: 1203 turns.
- Che do hoi dap: history-aware, tuc prompt dau vao co conversation history.
- Model API: `gpt-4o-mini`.
- Evaluation: chay SQL tren SQLite local va so sanh result hash voi gold SQL.

Cac run nay la **adapted local runs**, khong phai official paper reproduction. Chung dung official repositories hoac source framework da clone, nhung co adapter de:

- tuong thich OpenAI SDK hien tai;
- dung dataset local co san trong workspace;
- thong nhat logging/evaluation contract giua cac baseline.

## 2. Duong dan artifacts

| Baseline | Predictions | Manifest / summary |
|---|---|---|
| DIN-SQL | `baselines/text2sql/04_din_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl` | `baselines/text2sql/04_din_sql/results/smoke_sparc_adapted_api_n1203_history/run_manifest.json` |
| MAC-SQL | `baselines/text2sql/06_mac_sql/results/smoke_sparc_adapted_api_n1203_history/predictions.jsonl` | `baselines/text2sql/06_mac_sql/results/smoke_sparc_adapted_api_n1203_history/run_manifest.json` |
| C3SQL | `baselines/text2sql/20_c3sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl` | `baselines/text2sql/20_c3sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/run_manifest.json` |
| DAIL-SQL | `baselines/text2sql/21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/predictions.jsonl` | `baselines/text2sql/21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full/run_manifest.json` |

Derived metrics:

- Summary CSV: `baselines/text2sql/analysis/sparc_history_framework_sev_ex_summary.csv`
- Compact report: `baselines/text2sql/analysis/sparc_history_framework_sev_ex_report.md`

## 3. Metric definitions

### EX: Execution Match

EX la execution accuracy theo result set. Mot case duoc tinh dung khi:

1. predicted SQL execute thanh cong;
2. gold SQL execute thanh cong;
3. result hash cua predicted SQL bang result hash cua gold SQL.

Cong thuc:

```text
EX = #cases(result(pred_sql) == result(gold_sql)) / N
```

EX la metric chinh de do chat luong ket qua SQL trong setting nay.

### SEV: SQL Execution Validity

SEV trong bao cao nay duoc dung theo nghia **SQL Execution Validity**: ty le predicted SQL chay duoc trong SQLite, bat ke co ra dung ket qua hay khong.

Cong thuc:

```text
SEV = #cases(pred_sql executes successfully) / N
```

SEV khong do semantic correctness. No do tinh hop le/thuc thi duoc cua SQL. Mot model co SEV cao co the van EX thap neu SQL chay duoc nhung sai logic.

### SQL exec errors

So case predicted SQL khong execute duoc. Trong bao cao nay:

```text
SQL exec errors = N - #executable predicted SQL
```

### Call errors

So case loi API/framework call. Tat ca 4 baseline trong setting nay deu co `call_error_count = 0`.

### Cost estimate

Chi phi duoc uoc tinh theo price schedule:

- input: `$0.15 / 1M tokens`
- output: `$0.60 / 1M tokens`

Chi phi chi bao gom API token, khong bao gom local compute.

## 4. Ket qua tong hop

| Baseline | EX | SEV | SQL exec errors | Call errors | Total tokens | Cost est. | Avg latency s |
|---|---:|---:|---:|---:|---:|---:|---:|
| DIN-SQL | 688/1203 = 0.5719 | 1187/1203 = 0.9867 | 16 | 0 | 11939643 | $2.0900 | 10.888 |
| MAC-SQL | 712/1203 = 0.5919 | 1203/1203 = 1.0000 | 0 | 0 | 2638123 | $0.4791 | 3.096 |
| C3SQL | 712/1203 = 0.5919 | 1167/1203 = 0.9701 | 36 | 0 | 384279 | $0.0735 | 1.292 |
| DAIL-SQL | 728/1203 = 0.6052 | 1146/1203 = 0.9526 | 57 | 0 | 701236 | $0.1205 | 1.287 |

## 5. Ranking theo metric

### Theo EX

| Rank | Baseline | EX |
|---:|---|---:|
| 1 | DAIL-SQL | 0.6052 |
| 2 | MAC-SQL | 0.5919 |
| 2 | C3SQL | 0.5919 |
| 4 | DIN-SQL | 0.5719 |

DAIL-SQL dat EX cao nhat, hon MAC-SQL/C3SQL 16 cases dung tren tong 1203 turns. C3SQL bang MAC-SQL ve EX trong setting nay, du chi phi thap hon nhieu.

### Theo SEV

| Rank | Baseline | SEV |
|---:|---|---:|
| 1 | MAC-SQL | 1.0000 |
| 2 | DIN-SQL | 0.9867 |
| 3 | C3SQL | 0.9701 |
| 4 | DAIL-SQL | 0.9526 |

MAC-SQL co SEV tot nhat: 1203/1203 predicted SQL execute duoc. DAIL-SQL co EX cao nhat nhung SEV thap nhat vi co 57 SQL execution errors.

## 6. Dien giai tung baseline

### DIN-SQL

DIN-SQL dat:

- EX: 0.5719
- SEV: 0.9867
- SQL exec errors: 16
- cost: khoang $2.09

DIN-SQL co SEV cao, tuc hau het SQL sinh ra execute duoc. Tuy nhien EX thap nhat trong 4 baseline. Dieu nay cho thay nhieu SQL cua DIN chay duoc nhung khong tra dung ket qua. Chi phi DIN cao nhat do pipeline decomposed goi nhieu stage LLM: schema linking, classification, generation, correction.

Nhan xet: DIN-SQL la baseline manh ve decomposition va self-correction, nhung trong setting SParC history-aware nay khong vuot MAC/C3/DAIL ve EX, dong thoi ton token/latency cao.

### MAC-SQL

MAC-SQL dat:

- EX: 0.5919
- SEV: 1.0000
- SQL exec errors: 0
- cost: khoang $0.48

MAC-SQL la baseline on dinh nhat ve syntactic/execution validity. Tat ca predicted SQL deu execute duoc. EX bang C3SQL va kem DAIL-SQL mot chut, nhung SEV tot nhat.

Nhan xet: MAC-SQL co tradeoff tot giua quality va robustness. No khong co EX cao nhat, nhung khong tao SQL execution errors, phu hop lam baseline framework on dinh.

### C3SQL

C3SQL dat:

- EX: 0.5919
- SEV: 0.9701
- SQL exec errors: 36
- cost: khoang $0.0735

C3SQL bang MAC-SQL ve EX nhung co chi phi thap hon rat nhieu. Diem yeu la SEV thap hon MAC/DIN do co 36 SQL execution errors.

Nhan xet: C3SQL la baseline prompt pipeline rat hieu qua ve chi phi. Trong adapted run nay, no dat EX ngang MAC-SQL voi token cost thap nhat trong 4 baseline. Tuy nhien, can chu y rang C3SQL khong co agent repair/validation sau generation nen co nhieu SQL execution errors hon MAC.

### DAIL-SQL

DAIL-SQL dat:

- EX: 0.6052
- SEV: 0.9526
- SQL exec errors: 57
- cost: khoang $0.1205

DAIL-SQL co EX cao nhat trong 4 baseline. Dieu nay cho thay few-shot/example-selection style prompt co the giup tang result correctness. Tuy nhien, DAIL-SQL co SEV thap nhat, tuc sinh nhieu SQL khong execute duoc hon cac baseline khac.

Nhan xet: DAIL-SQL co quality cao nhat theo result-match, nhung robustness/executability yeu hon. Neu paper can nhan manh semantic result correctness, DAIL la doi thu manh. Neu nhan manh reliability va valid SQL, MAC-SQL van manh hon.

## 7. EX vs SEV: tradeoff quan trong

Ket qua cho thay EX va SEV khong xep hang giong nhau:

- DAIL-SQL cao nhat ve EX nhung thap nhat ve SEV.
- MAC-SQL cao nhat ve SEV nhung EX chi dong hang voi C3SQL.
- C3SQL dat EX bang MAC-SQL voi cost thap nhat, nhung SEV kem hon.
- DIN-SQL co SEV cao nhung EX thap nhat va cost cao nhat.

Dieu nay quan trong cho interpretation:

```text
SEV cao = SQL chay duoc.
EX cao = SQL tra dung ket qua.
```

Mot framework co the sinh SQL hop le nhung sai logic. Nguoc lai, framework co the dat nhieu case dung hon nhung cung sinh nhieu SQL loi hon tren cac case kho.

## 8. Cost va latency

| Baseline | Total tokens | Cost est. | Avg latency s |
|---|---:|---:|---:|
| DIN-SQL | 11939643 | $2.0900 | 10.888 |
| MAC-SQL | 2638123 | $0.4791 | 3.096 |
| C3SQL | 384279 | $0.0735 | 1.292 |
| DAIL-SQL | 701236 | $0.1205 | 1.287 |

Cost/latency ranking:

1. C3SQL re nhat va nhanh.
2. DAIL-SQL van re, nhung ton token hon C3 do few-shot/example prompt.
3. MAC-SQL ton hon C3/DAIL nhung van thap hon DIN.
4. DIN-SQL ton nhat do multi-stage calls.

Neu xet EX tren cost, C3SQL va DAIL-SQL rat canh tranh. Neu xet stability, MAC-SQL co loi the do SEV = 1.0.

## 9. Ket luan thuc nghiem

Tren SParC history-aware adapted run:

- **Best EX:** DAIL-SQL, 0.6052.
- **Best SEV:** MAC-SQL, 1.0000.
- **Best cost-quality tradeoff:** C3SQL, EX ngang MAC-SQL voi cost thap hon.
- **Most expensive:** DIN-SQL, cost cao nhat nhung EX thap nhat trong nhom nay.

Ket qua nay goi y:

1. DAIL-SQL nen duoc dua vao bang baseline chinh neu claim cua paper lien quan result correctness.
2. MAC-SQL nen tiep tuc la baseline robustness chinh vi khong co SQL execution error.
3. C3SQL la baseline prompt-only rat manh va re; can dua vao so sanh de tranh overclaim ve agent/pipeline complexity.
4. DIN-SQL van huu ich lam decomposed prompting baseline, nhung tren setting nay khong phai baseline manh nhat.

## 10. Caveats

- Day la SParC local adapted evaluation, khong phai official Spider/SParC leaderboard setting.
- C3SQL va DAIL-SQL duoc chay qua adapter smoke, khong phai entrypoint official nguyen ban.
- EX la local SQLite result-hash match; co the khac official evaluator trong mot so edge cases.
- SEV chi do executability, khong do semantic correctness.
- Cost estimate dua tren token usage ghi trong OpenAI response va public price schedule cua `gpt-4o-mini`.
- VES-style timing chua duoc tinh full cho 4 baseline trong bao cao nay vi timing 30 iterations tren 1203 turns x 4 baseline mat nhieu thoi gian. Neu can VES, nen chay rieng voi sampling hoac de qua dem.

## 11. De xuat buoc tiep theo

1. Tinh failure taxonomy cho C3SQL/DAIL-SQL errors: schema hallucination, wrong join, wrong aggregation, history resolution failure.
2. Chay VES-style capped rieng cho 4 baseline neu can efficiency diagnostic.
3. Patch official entrypoints cua C3SQL va DAIL-SQL de co mot run gan reproduction hon.
4. Tao bang tong hop trong manuscript: EX, SEV, SQL exec errors, cost, logs/intermediate trace availability.
