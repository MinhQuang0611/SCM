# DSR-SQL

Dựng lại 2026-08-24. Hệ duy nhất trong đợt đọc có cả số Spider2-Snow lẫn BIRD dev.

## Thông tin

- Tên: Text-to-SQL as Dual-State Reasoning: Integrating Adaptive Context and Progressive Generation
- Tác giả: Zhifeng Hao, Qibin Song, Ruichu Cai, Boyan Xu (DMIRLAB)
- Trạng thái: preprint arxiv.org/abs/2511.21402, nộp 2025-11-26. Chưa qua peer review.
- Code: paper ghi github.com/DMIRLAB-Group/DSR-SQL — kiểm 2026-08-22 trả **HTTP 404**,
  repo không có trong danh sách public repo của org. Coi như chưa có code.

## Ý chính

Không dùng post-training, không dùng in-context example. Toàn bộ hiệu năng đến từ cấu trúc
pipeline — đúng loại hệ mà attribution theo stage nói được điều gì đó.

Hai state:

Adaptive Context State
- Schema & Knowledge Refinement — gộp bảng tương đương về cấu trúc, bỏ cột vô nghĩa,
  đưa phần lớn schema xuống dưới 128K token
- Adaptive Schema Selection — chọn bảng liên quan, chiến lược global hoặc partitioned
- Schema-aware Alignment — chạy probing query nhẹ rồi tổng hợp thành mô tả ngữ nghĩa

Progressive Generation State — giữ SQL bộ phận + execution feedback, tiến hóa qua 4 hành động:
- Extend — nối tiếp khi execution ra kết quả hợp lệ
- Revise — sửa mâu thuẫn logic theo tín hiệu lỗi
- Explore — phát truy vấn chẩn đoán khi kết quả bất thường
- Finalize — tổng hợp SQL chạy được

Quỹ đạo suy luận là directed acyclic, không quay lại state cũ.

## Kết quả

- Spider2-Snow 35.28 (DeepSeek-R1-0528, single path)
- BIRD dev 68.32 với DeepSeek-V3.1 (simple 72.65 / moderate 61.21 / challenging 63.45)
- BIRD dev 65.58 với Qwen3-30B-A3B (70.70 / 59.27 / 53.10)

## Ablation trên Spider2-Snow, nền DS-R1

Đầy đủ 35.28
- bỏ Schema & Knowledge Refinement: -12.80 pp
- bỏ Adaptive Schema Selection: -10.79 pp
- bỏ Generation-State Evolution: -7.49 pp
- bỏ Schema-aware Alignment: -3.48 pp

Đây là dữ kiện đối nghịch trực tiếp với ProSPy: cùng trên Spider 2.0, DSR-SQL cho thấy
schema handling chiếm gần hết đóng góp (12.80 + 10.79), còn ProSPy cho thấy phân tích cuối
chuỗi chiếm nhiều nhất (19.0) trong khi profiling chỉ 6.4.

Cộng với CogSQL (module chi phối đổi giữa Spider và BIRD) và GBV-SQL (agent mới nhất về ý
tưởng lại đóng góp ít nhất) thì có ba bằng chứng độc lập rằng mediator chi phối không cố định.

Lưu ý cách diễn đạt: đây KHÔNG phải mâu thuẫn logic. Bốn hệ ablate bốn tập module khác nhau,
kiến trúc và backbone khác nhau. Xem phần cảnh báo trong tong_quan_literature.md.

## Giới hạn tác giả nêu

Vẫn kém các kỹ thuật dùng post-training, in-context example, hoặc multi-path generation.
Họ định vị đóng góp ở mức zero-shot.

## Ý nghĩa với đề tài

- Bốn hành động (Extend / Revise / Explore / Finalize) là một **nhãn bước có sẵn ngữ nghĩa**
  và do chính hệ sinh ra, không phải do annotator gán. Nếu chạy được thì đây là nguồn nhãn
  bước rẻ nhất gặp cho tới giờ. Nhưng nó nói HỆ ĐANG LÀM GÌ, không nói bước đó có sai không.
- Trajectory acyclic làm việc quy lỗi dễ hơn hẳn so với vòng lặp không giới hạn của ProSPy.
- Có số BIRD dev nên đối chiếu được với mặt bằng của repo, nhưng backbone khác gpt-4o-mini
  đang dùng nên không so trực tiếp.

## Cần xác minh

- Repo 404. Hỏi tác giả hoặc theo dõi. Không xếp vào nhóm chạy được cho tới khi có code.
- 35.28 đo trước hay sau bản vá evaluation suite 2025-10-29.
