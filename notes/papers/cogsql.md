## CogSQL
(AAAI-25, PDF gốc: `paper/08630-YuanH.pdf`. Bản dài: `archive/cogsql-full.md`)

# Pipeline
- Key Concept Recalling ( nhớ lại trước khi viết ) : gồm 2 dự đoán tách rời
  - Coarse-to-fine schema linking : cross-encoder lọc thô top-5 bảng (k1=5) -> LLM lọc tinh 7 cột (k2=7)
  - Syntax keyword prediction : classifier riêng đoán trước SQL sẽ cần từ khóa gì (COUNT, GROUP BY, WHERE...) rồi mớm cho LLM
- Concept-enhanced CoT : diễn giải lại câu hỏi trước -> mới dựng SQL. Fixed two-shot, không retrieval ( lý do nêu: rẻ hơn )
- Consistency-based Correction : 2 hướng kiểm
  - NLQ consistency : SQL có khớp ý câu hỏi không
  - Result consistency : kết quả chạy ra có hợp lý không ( hỏi 1 trường mà ra 300 dòng )

# Kết quả
- CogSQL + GPT-4 : Spider dev 85.40 / test 86.40, BIRD 59.58, VES 64.30
- CogSQL + GPT-4o-mini : 84.20 / 83.80 / 56.26 / 61.31
- Bảng có DIN-SQL, MAC-SQL, DAIL-SQL cùng nền GPT-4 -> dùng làm mốc đối chiếu ( repo chạy gpt-4o-mini, không so trực tiếp )

# Ablation ( nền GPT-4o-mini, đầy đủ 84.20 / 56.26 )
| Bỏ đi | Spider | BIRD |
|---|---:|---:|
| schema linking | 82.40 **(-1.80)** | 55.74 (-0.52) |
| syntax keyword | 83.50 | 55.02 |
| concept-enhanced CoT | 83.50 | 52.41 **(-3.85)** |
| NLQ consistency | 83.70 | 55.93 |
| result consistency | 83.60 | 53.85 **(-2.41)** |

- Spider : module chi phối là schema linking. BIRD : là CoT + result consistency
- Cùng một hệ, đổi benchmark thì đổi luôn module quan trọng nhất — apples-to-apples nằm gọn trong MỘT paper
- Tác giả CÓ phát biểu cả hai vế (mục "Module Design" tr.7) nhưng giải thích bằng "BIRD phức tạp hơn", KHÔNG rút kết luận về tính chuyển được giữa cấu hình. Kết luận đó là của repo

# Error taxonomy trước/sau ( 500 NLQ ngẫu nhiên từ BIRD, GPT-4o-mini )
- Schema Misuse 123->75, Nested Query 47->39, Keyword Misuse 46->35, NLQ Misunderstanding 35->22, Syntax 11->2. Tổng 262->173
- Taxonomy này độc lập kiến trúc agent -> map được sang DIN-SQL / MAC-SQL. Phân loại lỗi CỦA MODEL, khác typology A/B/C của GBV-SQL ( lỗi CỦA BENCHMARK )

# Ghi chú cho đề tài
- Artifact quan sát được : schema 2 mức, tập keyword dự đoán, diễn giải câu hỏi, SQL nháp, phán quyết NLQ consistency, kết quả execution + SQL sau sửa
- **Syntax keyword là mediator có ground truth rẻ tiền** — keyword thật trích từ gold SQL bằng parser, không cần annotate tay
- Không có code public. Checkpoint schema linking mượn từ CodeS
- Cảnh báo: các bản tóm tắt trên mạng ghi pipeline "Understanding -> Decomposition -> Planning -> Generation -> Reflection" là SAI, không phải kiến trúc trong paper
