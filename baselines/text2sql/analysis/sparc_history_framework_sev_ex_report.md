# SParC history-aware EX/SEV comparison

- SEV = SQL Execution Validity = predicted SQL executable rate.
- EX = SQLite result-hash match vs gold SQL.
- All runs are adapted local runs with conversation history, n=1203.

| baseline | EX | SEV | SQL exec errors | call errors | tokens | cost est. | avg latency s |
|---|---:|---:|---:|---:|---:|---:|---:|
| `04_din_sql` | 688/1203 = 0.5719 | 1187/1203 = 0.9867 | 16 | 0 | 11939643 | $2.0900 | 10.888 |
| `06_mac_sql` | 712/1203 = 0.5919 | 1203/1203 = 1.0000 | 0 | 0 | 2638123 | $0.4791 | 3.096 |
| `20_c3sql` | 712/1203 = 0.5919 | 1167/1203 = 0.9701 | 36 | 0 | 384279 | $0.0735 | 1.292 |
| `21_dail_sql` | 728/1203 = 0.6052 | 1146/1203 = 0.9526 | 57 | 0 | 701236 | $0.1205 | 1.287 |

## Ranking

- EX: DAIL-SQL (0.6052) > C3SQL/MAC-SQL (0.5919) > DIN-SQL (0.5719).
- SEV: MAC-SQL (1.0000) > DIN-SQL (0.9867) > C3SQL (0.9701) > DAIL-SQL (0.9526).
- DAIL-SQL has the best result-match EX, but also the lowest SQL executable rate among these four.

CSV: `baselines/text2sql/analysis/sparc_history_framework_sev_ex_summary.csv`
