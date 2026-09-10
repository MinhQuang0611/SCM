# DAIL-SQL

Dựng lại 2026-08-24 từ bản tóm tắt còn giữ. **Mỏng hơn bản gốc đã xóa.**

## Thông tin

- Tên: Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation
- Venue: PVLDB 17(5) 2024, DOI 10.14778/3641204.3641221
- Code: github.com/BeachWang/DAIL-SQL

## Ý chính

Đây là bài **benchmark evaluation về prompt engineering**, không phải bài đề xuất kiến trúc.
Pipeline: question representation, chọn example, generation, tùy chọn self-consistency.

## Đã chạy trong repo — adapted run, không phải reproduction

| Run | n | Model | EX |
|---|---|---|---|
| 21_dail_sql/results/smoke_spider_dev_adapted_api_n1034_c3_dail_full | 1034 | gpt-4o-mini | 0.7147 |
| 21_dail_sql/results/smoke_sparc_adapted_api_n1203_c3_dail_history_full | 1203 | gpt-4o-mini | 0.6052 |

So trên cùng SParC dev n=1203, cùng gpt-4o-mini:

  DAIL-SQL 0.6052 > MAC-SQL 0.5919 = C3SQL 0.5919 > DIN-SQL 0.5719

## Kết luận âm tính, cần ghi rõ

DAIL-SQL **không có stage nội bộ để quy lỗi** — về cơ bản là một lần gọi LLM sinh SQL.
Với đề tài này nó là:
- điểm so sánh accuracy
- đối chứng "không có kiến trúc nhiều agent"

Không phải đối tượng attribution.

## Dữ kiện đáng đưa vào manuscript

Nó đang CAO ĐIỂM HƠN CẢ HAI hệ multi-agent trên SParC dev, cùng backbone.

Dữ kiện này chống lại giả định ngầm "multi-agent thì mạnh hơn", và củng cố lý do phải nghiên
cứu chỗ nào trong pipeline làm hỏng việc — chứ không phải thêm agent.
