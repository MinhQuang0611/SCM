# VET

Đọc lại từ paper 2026-08-24. Bản gốc đã xóa, bản này viết mới.

## Thông tin

- Tên: VET: Verifiable Execution Tracing for Reliable Text-to-SQL Generation
- Tác giả: Dongyu Wang, Jingyu Li, Lan Zhang, Ganggang Yu, Liang Huang
- Venue: Findings of ACL 2026, tr. 30867-30883, DOI 10.18653/v1/2026.findings-acl.1544
- Code: không thấy link trên trang anthology

## Ý chính

- Họ nói: LLM sinh SQL hay bịa và **không có cơ chế kiểm chứng** nào cả.
- Cách làm: biến suy luận thành **step-wise executable semantics** — mỗi bước suy luận
  được chạy thật trên database, cho ra kết quả trung gian quan sát được.
- Nguyên văn ý chính: mỗi bước "is executed against the real database to produce observable
  intermediate results", biến quá trình sinh từ hộp đen thành tương tác debug được.

## Kết quả

- BIRD 70.93
- Spider 2.0-lite 37.04
- Cải thiện rõ nhất ở nhóm query phức tạp

## Vì sao quan trọng với đề tài

- Đây là paper **gần nhất về mặt kỹ thuật** với ý tưởng Logging Matrix: họ cũng cho rằng
  kết quả trung gian quan sát được là thứ quyết định.
- Khác biệt: họ dùng trace để **làm hệ chạy tốt hơn**, không dùng để **quy lỗi**.
  Không có nhãn nguyên nhân, không có annotator, không đo agreement.
- Nếu chạy được thì đây là nguồn stage_logs sạch nhất, vì mỗi bước đã có kết quả execution
  đi kèm sẵn — không phải tự chế thêm.

## Cần xác minh

- Code có public ở đâu không. Chưa thấy thì không xếp vào nhóm chạy lại được.
- "Bước" của họ định nghĩa thế nào, có cố định số bước không hay biến thiên theo case.
- 37.04 trên Spider2-lite đo trước hay sau bản vá evaluation suite 2025-10-29.
