# Alpha-SQL

Đọc lại từ paper 2026-08-24. Bản gốc đã xóa, bản này viết mới.

## Thông tin

- Tên: Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search
- Tác giả: Boyan Li, Jiayi Zhang, Ju Fan, Yanwei Xu, Chong Chen, Nan Tang, Yuyu Luo
- Venue: ICML 2025 — openreview.net/forum?id=kGg1ndttmI
- Preprint: arxiv.org/abs/2502.17248
- Code: github.com/HKUSTDial/Alpha-SQL — CÓ code public

## Ý chính

- Họ nói: fine-tune tốn kém và lỗi thời nhanh vì cứ vài tháng lại có model mới,
  nên nên đi hướng zero-shot.
- Cách làm: dùng **MCTS** để dựng SQL dần theo từng action, dựa trên trạng thái suy luận
  còn dở.
- Hai thành phần riêng:
  - LLM-as-Action-Model — LLM sinh ra các action dựng SQL ngay trong quá trình search
  - reward function tự giám sát — chấm chất lượng candidate mà không cần nhãn

## Kết quả

- BIRD dev 69.7, dùng LLM open-source 32B, không fine-tune
- Hơn cách zero-shot trước đó dựa trên GPT-4o 2.5 điểm

## Vì sao quan trọng với đề tài

- Đây là hệ duy nhất trong nhóm có **search trace dạng cây**, không phải chuỗi tuyến tính.
- Nghĩa là "stage nào gây lỗi" ở đây có dạng khác hẳn: lỗi có thể là
  - nhánh đúng không bao giờ được sinh ra, hoặc
  - nhánh đúng được sinh ra nhưng reward chấm thấp nên bị bỏ
  Hai loại này phân biệt được từ trace, và đó là tín hiệu attribution hiếm.
- Ngược lại: cây search làm khái niệm "stage" mất nghĩa. Không có bốn stage cố định để
  quy lỗi. Nếu đưa vào testbed thì phải định nghĩa lại đơn vị quy lỗi.

## Cần xác minh

- Số node / độ sâu trung bình mỗi case — quyết định trace có annotate nổi bằng tay không.
- Reward tự giám sát tính thế nào, có log lại được điểm từng candidate không.
