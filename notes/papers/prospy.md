# ProSPy

Dựng lại 2026-08-24. SOTA học thuật cao nhất trên Spider 2.0 tính tới nay.

## Thông tin

- Tên: ProSPy: A Profiling-Driven SQL-Python Agentic Framework for Enterprise Text-to-SQL
- Tác giả: Zhaorui Yang, Huawei Zheng, Sen Yang và cộng sự (17 tác giả)
- Trạng thái: preprint arxiv.org/abs/2606.05836, nộp 2026-06-04. Chưa qua peer review.
- Code: không nêu trong paper

## Bốn giai đoạn

1. Data profiling — sinh metadata bằng SQL template
   - suy luận semantic type: metric / dimension / identifier / time / other
   - thống kê theo type, null ratio, sample value, cấu trúc nested
   - ra file JSON profile của DB, tái dùng cho mọi câu hỏi cùng DB
2. Progressive schema pruning — LLM loại dần bảng rồi cột, xử lý theo batch
3. Agentic data fetching — dựng **view trung gian** qua một DSL độc lập dialect
   (tổ chức theo dimension / metric / condition), transpile sang dialect đích,
   materialize ra CSV. View lồng nhau, lặp lại.
4. Python analysis — nạp CSV vào Python, transform nhiều bước, ranking, analytics.
   Chạy lặp có sửa lỗi tới khi ra CSV cuối.

## Kết quả

| Backbone | Lite | Snow |
|---|---|---|
| Claude-Opus-4.5 | 60.15 | 60.51 |
| DeepSeek V3.2 | 41.32 | 40.77 |

Không report BIRD. Số trên là KHÔNG dùng majority voting.

Đáng ghi: Lite và Snow gần bằng nhau. Khớp với việc hai bản là cùng 547 bài toán, và tương
phản với chênh 20 điểm ở top leaderboard — củng cố nghi ngờ hai leaderboard đó không cùng
điều kiện đánh giá.

## Ablation — chú ý mẫu số

Đo trên **mẫu 110 example của Spider2-Snow**, không phải toàn tập:

- bỏ data profiling: -6.4 pp
- bỏ DSL fetching, dùng SQL thẳng: -9.1 pp
- thay Python analysis bằng SQL + majority voting: -16.3 pp
- thay bằng SQL không voting: -19.0 pp

Tác giả tự xếp hạng Python (16.3-19.0) > DSL (9.1) > profiling (6.4), NHƯNG kết luận của họ
nguyên văn là cả ba đều quan trọng:

  "Overall, the ablation results verify that data profiling, DSL-guided data fetching, and
   Python-based analysis all contribute substantially to the effectiveness of ProSPy."

Họ KHÔNG nói profiling kém quan trọng hơn kỳ vọng. Cách đọc "schema/profiling đứng cuối" là
của repo, không phải phát biểu của tác giả. Giữ đúng phân biệt này khi trích.

## Ý nghĩa với đề tài — chủ yếu là cảnh báo

ProSPy là ví dụ rõ nhất cho thấy Spider 2.0 đang kéo các hệ mạnh RA KHỎI phạm vi mà
attribution theo stage áp dụng được:

- Đơn vị lỗi không còn là câu SQL. Kết quả cuối là CSV do Python sinh. Một case sai có thể
  sai ở view trung gian, ở transpile DSL sang dialect, hoặc ở đoạn pandas cuối. Ba chỗ này
  không cùng loại artifact nên không so được bằng một định nghĩa lỗi duy nhất.
- Số vòng lặp không cố định. Fetching lồng nhau và Python sửa lỗi lặp làm số stage biến thiên
  theo case. Hợp đồng stage_logs 4 key không biểu diễn được, cần list-of-steps.
- Giới hạn tác giả tự nêu chính là bài toán của đề tài: **error propagation** — view trung
  gian sai làm hỏng phân tích phía sau. Họ nêu rồi dừng, không đo. Đây là chỗ mediation
  analysis nói được điều họ không nói.

Mặt tiêu cực: ranh giới stage mờ đi thì quy lỗi KHÓ hơn, không dễ hơn. Một lý do độc lập nữa
để không lấy Spider 2.0 làm mặt bằng chính.

## Giới hạn tác giả nêu

- error propagation từ view trung gian sai
- chỉ đánh giá trên Spider2-Lite/Snow, chưa rõ khái quát sang DB enterprise khác

## Cần xác minh

- Code có release không
- Mẫu 110 example chọn thế nào, ngẫu nhiên hay có chủ đích
- 60.15/60.51 chạy trên Claude-Opus-4.5, không đặt cạnh hệ dùng backbone yếu hơn
