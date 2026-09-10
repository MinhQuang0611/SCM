# AgentSM

Dựng lại 2026-08-24. Gần đề tài nhất về mặt DỮ LIỆU, khác hẳn về mục tiêu.

## Thông tin

- Tên: AgentSM: Semantic Memory for Agentic Text-to-SQL
- Tác giả: Asim Biswal, Chuan Lei, Xiao Qin, Aodong Li, Balakrishnan Narayanaswamy, Tim Kraska
- Trạng thái: preprint arxiv.org/abs/2601.15709, nộp 2026-01-22. Chưa qua peer review.
- Code: có hai link footnote dạng rút gọn, không phát biểu rõ là public. Chưa xác nhận.

## Vì sao đọc

Đề tài này thu stage_logs để CHẨN ĐOÁN. AgentSM thu gần đúng loại dữ liệu đó để TÁI SỬ DỤNG.
Cùng nguyên liệu, khác mục tiêu.

## Kiến trúc

Hai agent:
- Planner — lõi suy luận, dựng execution plan và sinh SQL
- Schema linking agent — khám phá dữ liệu chi tiết khi cần, có tool vector search

Semantic memory dựng thế nào:

1. sinh trace offline — tự sinh câu hỏi tổng hợp để tạo execution trace giàu bước khám phá
2. phân loại theo phase — mỗi bước gán vào exploration / execution / validation
   bằng **regex pattern matching**
3. cấu trúc hóa — lưu ở dạng markdown, header ngữ nghĩa do LLM sinh
4. truy hồi — lọc trace cùng database, chọn trace có câu hỏi tương tự nhất, nạp đoạn trace
   đúng phase mà agent đang ở

Composite tool: gộp chuỗi tool hay đi cùng nhau thành một tool đơn.
Ví dụ get_ext rồi get_ddl gộp thành local_exploration. Đây là cách họ rút ngắn trajectory.

## Kết quả

Base model Claude 4 Sonnet, Spider2-Lite toàn bộ 547 câu:

| Hệ | Overall | BigQuery | Snowflake | SQLite |
|---|---|---|---|---|
| SpiderAgent | 28.7 | | | |
| CodingAgent | 24.7 | | | |
| AgentSM | 44.8 | 52.2 | 35.0 | 51.9 |
| AgentSM + gold table | 57.6 | | | |

Hiệu quả: giảm 25% token trung bình và 35% độ dài trajectory.

Chênh theo engine đáng chú ý: Snowflake 35.0 so với BigQuery 52.2 và SQLite 51.9, trên CÙNG
tập bài toán. Vì Lite 547 bài là cùng nội dung, chênh này là failure do dialect/engine đã
được cô lập sẵn. Ví dụ thực tế tốt cho luận điểm "cặp Lite/Snow là thí nghiệm đối chứng có sẵn".

## Ablation — mẫu số nhỏ

Trên mẫu 75 câu Spider2-Lite:
- bỏ trajectory reading: accuracy -34.7%, số bước +4.37
- bỏ composite tool: accuracy -35.8%, số bước +4.77

Cả hai là thành phần cốt lõi, không phải tinh chỉnh phụ.

## Giới hạn tác giả nêu

- schema linking vẫn khó với schema lồng nhau
- **hiệu năng lệch mạnh theo domain**: 60-78% trên database phổ thông,
  chỉ 14-40% trên database chuyên ngành
- composite tool giúp phần schema linking, ít giúp với toán phức tạp hoặc CTE nhiều tầng
- truy hồi chi tiết quá thì dễ bỏ sót ngữ cảnh cần thiết

## Ý nghĩa với đề tài

Dùng được:
- Phân loại bước theo phase (exploration / execution / validation) là một schema stage tối
  giản, độc lập kiến trúc. Ứng viên để chuẩn hóa stage_logs khi mở sang agent nhiều nhánh.
  NHƯNG họ làm bằng regex, nhãn phase có nhiễu. Mượn thì phải đo agreement, không dùng thẳng.
- Composite tool cho thấy đơn vị "bước" là QUY ƯỚC, không phải sự thật khách quan.
  Gộp hai tool lại thì bước gây lỗi cũng đổi theo. Đây là mối đe dọa trực tiếp tới bài toán
  "when" — mốc step-level 30.3% của TraceElephant có thể một phần đến từ chỗ này.

Khác biệt: AgentSM dùng trace làm input để cải thiện, không gán nhãn nguyên nhân cho case nào.
Không có nhãn lỗi, không có annotator, không đo agreement. Khoảng trống của đề tài giữ nguyên.

Cảnh báo thiết kế thực nghiệm: hệ có memory **vi phạm giả định độc lập giữa các case** — case
sau dùng trace của case trước. Mediation analysis mặc định coi các case độc lập. Đưa hệ loại
này vào testbed thì phải chạy ở chế độ memory rỗng, hoặc xử lý phụ thuộc này tường minh.

## Cần xác minh

- Code có public không
- Chênh 60-78% với 14-40% theo domain là chia theo database nào. Có danh sách thì đó là nguồn
  phân tầng sẵn có.
- Mẫu 75 câu chọn thế nào
