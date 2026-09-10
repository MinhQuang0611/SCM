# Spider 2.0

Dựng lại 2026-08-24. Gồm cả phần cập nhật trạng thái năm 2026.

## Thông tin

- Tên: Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows
- Tác giả: Fangyu Lei và cộng sự
- Venue: ICLR 2025 Oral
- Project: spider2-sql.github.io · Code/data: github.com/xlang-ai/Spider2 (MIT)

## Quy mô

Paper giới thiệu 632 bài. Release hiện tại khác:

| Variant | Task | Số bài | Engine |
|---|---|---|---|
| Spider2-Lite | Text-to-SQL | 547 | BigQuery 214, Snowflake 198, SQLite 135 |
| Spider2-Snow | Text-to-SQL | 547 | Snowflake toàn bộ |
| Spider2-DBT | code-agent mức repo | 68 | DuckDB/DBT |

Không dùng 632 và số của release hiện tại như cùng một split.

## Lite và Snow KHÔNG phải hai dataset — đã kiểm trên file local

547/547 map một-một, toàn bộ câu hỏi khớp từng chữ. Chỉ khác engine và cách đặt id
(Snow thêm tiền tố sf_ cho id chưa có):

| Lite | thành Snow | Số bài | Engine trong Lite |
|---|---|---|---|
| bq* | sf_bq* | 180 | BigQuery |
| sf_bq* | giữ nguyên | 189 | Snowflake |
| local* | sf_local* | 135 | SQLite |
| ga* | sf_ga* | 25 | Google Analytics |
| sf* | giữ nguyên | 18 | Snowflake |

Hệ quả khi báo cáo: chạy cả Lite lẫn Snow KHÔNG cho hai kết quả độc lập. Trình bày như hai
benchmark riêng là đếm trùng.

Nhìn ngược lại: cặp Lite/Snow là thí nghiệm đối chứng có sẵn. Cùng câu hỏi, cùng gold, chỉ
khác dialect và engine. Case đúng bên này sai bên kia là failure do dialect/engine, đã được
cô lập sẵn khỏi nguyên nhân khác.

## Vì sao khó

- DB lấy từ ứng dụng enterprise, có thể hơn 1000 cột
- phải đọc metadata, tài liệu dialect, hoặc code mức project
- nhiều bài cần nhiều query + transformation + workflow phân tích
- SQL có thể dài hơn 100 dòng
- Trong paper: code-agent nền o1-preview chỉ giải được 21.3%, so với 91.2% trên Spider 1.0
  và 73.0% trên BIRD

## Trạng thái 2026 — ba vấn đề

1. Leaderboard bão hòa bởi hệ không reproduce được. Đọc 2026-08-22:
   Snow top-1 96.70 (Genloop, proprietary), Lite top-1 76.23 (Tianqiong / GLM 5.2),
   DBT top-1 65.6. Top-5 cả ba setting gần như toàn hệ thương mại, không paper, không code,
   điểm self-reported.
   - Snow 96.70 CAO HƠN Lite 76.23 dù là cùng 547 bài. Hai leaderboard không cùng điều kiện.
   - Trang project vẫn ghi "Last update 2025-05-22" trong khi bảng có entry dùng model 2026.

2. Hạ tầng đánh giá gián đoạn. Changelog xlang-ai/Spider2:
   - 2026-08-12: nguyên văn "the Snowflake evaluation account is currently experiencing an
     unexpected suspension issue" — kiểm lại 2026-08-22 vẫn chưa gỡ
   - 2025-11-06: đổi chính sách password/MFA
   - 2025-10-29: sửa evaluation suite, thay đổi điểm
   - 2025-07-13: sửa ambiguity trong spider2-snow.jsonl
   Nghĩa là điểm chấm ở hai thời điểm khác nhau không so được với nhau.

3. Chất lượng nhãn thấp nhất trong nhóm đang xét. Xem annotation-errors.md.

## Nhánh mới: Spider 2.0-AIFunc

arxiv.org/abs/2607.06229, 2026-07-07, preprint, có tác giả Spider 2.0 gốc.
465 instance đã verify trên 125 database, thêm 6 loại AI function của Snowflake.
Proprietary tốt nhất 67-70% EX, open-source tốt nhất 58.1%.
Nguồn lỗi chính họ báo: predicate specification, schema grounding, AI function parameterization.

Kết luận của họ đáng chú ý: **framework agent phức tạp (schema retrieval, table selection)
không chuyển được sang setting này — cấu hình agent tối giản ngang bằng hoặc tốt hơn.**

Suy ra cho đề tài: "nhiều stage hơn" không đồng nghĩa "quy lỗi được nhiều hơn". Khi stage
không đóng góp gì thì mediation analysis trên stage đó ra hiệu ứng gần 0, không nói lên gì.

## Vai trò trong đề tài

Chỉ là **bài kiểm tra tính chuyển được**, chạy sau, trên subset nhỏ. Không phải mặt bằng chính.

Nếu chạm vào: chạy phần local* của Lite trước — 135 bài, SQLite, không cần cloud credential.
Không chạy Snow cho tới khi trạng thái evaluation account rõ ràng.

## Chưa xác minh

- Quan hệ giữa 547 của release hiện tại và 632 trong paper gốc
- Thư mục Snow local có hai file spider2-snow.jsonl và spider2-snow-0713.jsonl, cùng 547 bài.
  Mọi experiment phải ghi commit hash, data version, evaluator version.
