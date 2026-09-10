# CogSQL

> **Cập nhật 2026-09-06 — mục "không đọc được PDF" bên dưới đã hết hiệu lực.**
> Bản PDF chính thức của AAAI-25 nằm sẵn trong repo tại `paper/08630-YuanH.pdf`.
> Đã đối chiếu lại trực tiếp từ file đó:
> - Table 2 khớp: CogSQL + GPT-4 → Spider dev `85.40`, Spider test `86.40`, BIRD EX `59.58`,
>   VES `64.30`. CogSQL + GPT-4o-mini → `84.20` / `83.80` / `56.26` / `61.31`.
> - Table 5 (ablation) khớp toàn bộ, và có thêm 2 dòng note cũ thiếu:
>   w/o syntax keyword prediction `83.50` / `55.02`, w/o NLQ consistency `83.70` / `55.93`.
> - `k1 = 5`, `k2 = 7` khớp.
> - **Câu hỏi treo đã đóng:** tác giả CÓ tự phát biểu cả hai vế, ở mục "Module Design" trang 7 —
>   trên Spider "its absence causes the most significant drop" (schema linking), trên BIRD
>   "concept-enhanced CoT prompting and result consistency modules are vital". Nhưng họ giải
>   thích chênh lệch bằng "BIRD phức tạp hơn", **không** rút ra kết luận về tính chuyển được
>   giữa các cấu hình. Kết luận đó vẫn là của repo.
>
> Ghi chú lịch sử bên dưới giữ nguyên để biết vì sao note cũ ghi như vậy.

Viết lại 2026-08-24 (đợt 2). **KHÔNG đọc được PDF gốc** — OJS của AAAI từ chối kết nối cả 3 lần thử
(`socket hang up` qua WebFetch, `curl (56) schannel: server closed abruptly` qua curl), giống lần thử
trước cùng ngày. Số liệu và kiến trúc giữ nguyên từ note cũ; phần diễn giải và sơ đồ là của repo.

## Thông tin

- Tên: CogSQL: A Cognitive Framework for Enhancing Large Language Models in Text-to-SQL Translation
- Tác giả: Hongwei Yuan, Xiu Tang, Ke Chen, Lidan Shou, Gang Chen, Huan Li (Zhejiang University)
- Venue: AAAI-25, vol 39 no 24, tr. 25778-25786, DOI 10.1609/aaai.v39i24.34770
- Code: KHÔNG nêu URL trong paper, tìm thêm cũng không thấy repo

## Ý tưởng

Người viết SQL không viết ngay. Họ **nhớ lại** trước — câu này chắc phải dùng bảng nào, chắc phải có
`GROUP BY`, chắc phải `JOIN`. Rồi mới viết. Rồi đọc lại.

Hầu hết Text-to-SQL trước đó làm:

```
Question -> LLM -> SQL
```

CogSQL mô phỏng đúng ba nhịp nhận thức đó:

```
Question
   |
   v
+--------------------------------------------+
| 1. KEY CONCEPT RECALLING  (nhớ lại)        |
|                                            |
|   a) coarse-to-fine schema linking         |
|      thô: cross-encoder (checkpoint CodeS) |
|      tinh: LLM lọc lại   (k1=5, k2=7)      |
|                                            |
|   b) syntax keyword prediction             |
|      classifier riêng đoán trước SQL sẽ    |
|      cần từ khóa gì (LoRA rank 128,        |
|      lr 1e-6)                              |
+--------------------+-----------------------+
                     v
+--------------------------------------------+
| 2. CONCEPT-ENHANCED CoT   (viết)           |
|    bước 1: diễn giải lại câu hỏi           |
|    bước 2: mới dựng SQL                    |
|    fixed two-shot, KHÔNG retrieval         |
|    (lý do họ nêu: rẻ hơn)                  |
+--------------------+-----------------------+
                     v
+--------------------------------------------+
| 3. CONSISTENCY-BASED CORRECTION (đọc lại)  |
|    NLQ consistency:  SQL có khớp câu hỏi?  |
|    result consistency: kết quả có hợp lý?  |
+--------------------+-----------------------+
                     v
                 Final SQL
```

Khác DIN-SQL / MAC-SQL ở chỗ: tách **schema** và **syntax keyword** thành hai dự đoán riêng, mỗi cái có
output quan sát được.

## Module 1 — hai dự đoán tách rời

**(a) Schema linking hai mức** — lọc thô bằng model rẻ trước, rồi mới để LLM lọc tinh:

```
50 bảng, 800 cột
      |
      v  cross-encoder (rẻ, chạy local, checkpoint mượn từ CodeS)
top-5 bảng ứng viên          <- k1 = 5
      |
      v  LLM
7 cột thật sự cần            <- k2 = 7
```

**(b) Syntax keyword prediction** — một classifier riêng đoán trước bộ xương của SQL:

```
Question:
  "How many students older than 20 are there in each department?"
      |
      v  classifier
  { COUNT, GROUP BY, WHERE, comparison(>) }
```

LLM nhận gợi ý này TRƯỚC khi viết — biết trước "sẽ cần GROUP BY" thay vì tự nhớ ra.

Các nhóm keyword họ dự đoán: clause, aggregation, string, date, null, comparison, DISTINCT/CAST...

## Module 3 — hai loại consistency

Không phải một, mà hai hướng kiểm khác nhau:

```
NLQ consistency      "SQL này có khớp ý câu hỏi không?"
                      -> kiểm ở mức ngữ nghĩa, giống GBV-SQL

Result consistency   "Kết quả chạy ra có hợp lý không?"
                      -> ví dụ: hỏi 1 trường mà trả về 300 dòng
                                hỏi điểm trung bình mà ra số âm
```

## Kết quả chính (EX)

| Method | Spider dev | Spider test | BIRD | BIRD VES |
|---|---:|---:|---:|---:|
| DIN-SQL + GPT-4 | 83.50 | 85.30 | 50.72 | 58.79 |
| MAC-SQL + GPT-4 | 78.60 | 82.80 | 57.56 | 58.76 |
| DAIL-SQL + GPT-4 | 83.10 | 86.20 | 54.76 | 56.08 |
| **CogSQL + GPT-4** | **85.40** | **86.40** | **59.58** | **64.30** |
| CogSQL + GPT-4o-mini | 84.20 | 83.80 | 56.26 | 61.31 |

Đây là một trong ít bảng có DIN-SQL, MAC-SQL và DAIL-SQL trên CÙNG điều kiện GPT-4 — dùng làm mốc đối
chiếu cho adapted run của repo (repo chạy gpt-4o-mini nên thấp hơn, không so trực tiếp được).

## Ablation — phần đáng giá nhất

Nền GPT-4o-mini. Đầy đủ: Spider 84.20 / BIRD 56.26.

| Bỏ đi | Spider | BIRD |
|---|---:|---:|
| coarse-to-fine schema linking | 82.40 **(-1.80)** | 55.74 (-0.52) |
| syntax keyword prediction | 83.50 | 55.02 |
| concept-enhanced CoT | 83.50 | 52.41 **(-3.85)** |
| NLQ consistency | 83.70 | 55.93 |
| result consistency | 83.60 | 53.85 **(-2.41)** |

Đọc theo cột:

```
Trên SPIDER   -> module quan trọng nhất là schema linking
Trên BIRD     -> module quan trọng nhất là CoT + result consistency
```

**Cùng một hệ, cùng bộ module, đổi benchmark thì đổi luôn module quan trọng nhất.**

Đây là bằng chứng mạnh nhất cho motivation của đề tài, vì so sánh apples-to-apples nằm gọn trong MỘT
paper chứ không phải ghép chéo giữa các paper.

CHƯA XÁC MINH: tác giả có tự phát biểu điều này hay chỉ mình đọc ra từ bảng. Cần đóng trước khi dùng làm
luận cứ chính. Thử lần 3 ngày 2026-08-24, OJS vẫn không mở được. Đường khác cần thử: bản PDF từ trang
đồng tác giả (ZJU), Semantic Scholar, hoặc thư viện trường.

## Error taxonomy trước/sau

Lấy 500 NLQ ngẫu nhiên từ BIRD, nền GPT-4o-mini:

| Nhóm lỗi | trước | sau CogSQL | giảm |
|---|---:|---:|---:|
| Schema Misuse | 123 | 75 | -48 |
| Nested Query Misuse | 47 | 39 | -8 |
| Keyword Misuse | 46 | 35 | -11 |
| NLQ Misunderstanding | 35 | 22 | -13 |
| Syntax Error | 11 | 2 | -9 |
| **Tổng** | **262** | **173** | **-89** |

Taxonomy này (schema / keyword / nested / intent / syntax) ĐỘC LẬP với kiến trúc agent, nên map được
sang cả DIN-SQL lẫn MAC-SQL. Ứng viên tốt để đối chiếu với nhãn của repo.

Đối chiếu với GBV-SQL: taxonomy của CogSQL phân loại lỗi CỦA MODEL; typology A/B/C của GBV-SQL phân loại
lỗi CỦA BENCHMARK. Repo cần cả hai.

## Artifact quan sát được

- schema đã lọc, hai mức thô và tinh
- tập keyword dự đoán (+ AUC của classifier)
- diễn giải câu hỏi dạng text
- SQL nháp
- phán quyết NLQ consistency + SQL sau sửa
- kết quả execution + SQL sau sửa

Đáng chú ý: **syntax keyword prediction là mediator CÓ GROUND TRUTH RẺ TIỀN** — keyword thật trích được
từ gold SQL bằng parser, không cần annotate tay. Ứng viên tốt nhất gặp được cho tới giờ nếu cần một
mediator đo chính xác mà không tốn công gán nhãn.

## Tóm tắt một câu

CogSQL mô phỏng ba nhịp nhận thức của người viết SQL — nhớ lại (schema linking hai mức + đoán trước
keyword) → viết (CoT hai bước) → đọc lại (kiểm khớp câu hỏi + kiểm kết quả hợp lý) — và cho thấy module
nào quan trọng nhất phụ thuộc vào benchmark chứ không phải vào bản thân module.

## Chưa xác minh

- **Tác giả có tự phát biểu chuyện "module chi phối đổi theo benchmark" hay không.** Mục treo chính.
- Code có public không. Không có thì chỉ dùng làm nguồn số liệu và mẫu trình bày.
- Checkpoint schema linking mượn từ CodeS — chạy lại phải tính cả phụ thuộc đó.
- Bảng số DIN-SQL / MAC-SQL là trích lại từ paper gốc hay tự chạy lại.

## Cảnh báo về mô tả sai đang lưu hành

Một số bản tóm tắt CogSQL trên mạng mô tả pipeline là "Understanding -> Decomposition -> Planning ->
Generation -> Reflection". **Đó KHÔNG phải kiến trúc trong paper.** Kiến trúc thật là ba module:
Key Concept Recalling (schema linking + syntax keyword prediction) / Concept-enhanced CoT /
Consistency-based Correction. Đừng trích bản 5 bước đó.
