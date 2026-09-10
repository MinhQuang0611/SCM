## GBV-SQL
(ACL 2026 Main, tr.18391-18406; preprint arXiv 2509.12612. Bản dài: `archive/gbv-sql-full.md`)

# Bài toán
- ReFoRCE hỏi "sinh SQL tốt hơn thế nào". GBV-SQL hỏi "làm sao biết SQL này có đúng ý người hỏi không"
- SQL đúng cú pháp + chạy ra kết quả nhưng SAI Ý NGƯỜI HỎI — execution check không bắt được ( silent failure, đúng loại EX không nhìn thấy )

# Pipeline
- Planner : prune schema, làm rõ PK/FK, tách câu hỏi thành sub-question kiểu Targets–Conditions
- SQL Generator : Human-like CoT ( xác định ý định -> chọn bảng/cột -> dựng từng mệnh đề ), sinh sub-SQL rồi ghép
- SQL2Text Validator ( đóng góp chính ) : dịch ngược SQL về tiếng người -> so với câu hỏi gốc -> lệch thì sửa; binary selector chọn giữa bản gốc và bản đã sửa
  - Ý tưởng trung tâm : back-translation làm proxy cho ý định người dùng
- SQL Checker : format, syntax, execution, tối đa 3 vòng repair, truy giá trị thật trong DB để sửa
- Setting : Deepseek-v3 chính + GPT-4o phụ để validate, T = 0

# Kết quả
- BIRD dev ( Deepseek-v3 ) : Simple 69.51 / Moderate 54.62 / Challenging 50.69 / **Total 63.23** — hơn MAC-SQL cùng backbone 5.8 điểm
- Spider : dev 79.6 / test 82.8 (Deepseek-v3), 79.7 / 83.9 (GPT-4o), hơn MAC-SQL 5.2 trên test

# Ablation ( BIRD dev, Total )
| Cấu hình | Total | Loại can thiệp |
|---|---:|---|
| GBV-SQL + Deepseek-v3 | 63.23 | — |
| w/o Planner | 62.13 (-1.10) | **thay bằng MAC-SQL** |
| w/o SQLGenerator | 61.73 (-1.50) | **thay bằng MAC-SQL** |
| w/o SQL2TextValidator | 61.80 (-1.43) | bỏ hẳn |
| w/o Human-like CoT | 61.08 (-2.15) | thay bằng zero-shot prompt |
| w/o SQLChecker | 59.65 (-3.58) | bỏ hẳn |

- Tác giả tự phát biểu (§4.4) : bỏ SQLChecker gây drop lớn nhất -> "profound impact of query executability and proper formatting on the current execution based (EX) evaluation paradigm"
- Trớ trêu : agent đóng góp nhiều nhất là cái SỬA SYNTAX, không phải validator ngữ nghĩa ( chỉ -1.43 ) vốn là đóng góp mới của họ
- **CÁI BẪY** : §4.4 ghi rõ w/o Planner/SQLGenerator là THAY bằng module MAC-SQL, các dòng khác là BỎ HẲN -> ablation loại hỗn hợp, không xếp hạng 5 module trên cùng một thang được
  - Suy ra : ngay trong MỘT paper, 5 dòng của cùng một bảng ablation đã không cùng đơn vị. Luận cứ "LOO ablation không đủ" tốt hơn cách ghép chéo giữa các paper

# Gold Errors ( đóng góp thứ hai )
- Đọc tay toàn bộ 220 case fail execution trên Spider dev : 183 là LỖI CỦA BENCHMARK, chỉ 37 là lỗi model ( 83% )
- Thêm 62 Gold Error nằm trong nhóm case PASS -> có case "đúng" nhờ nhãn sai. Nhiễu annotation làm lệch attribution theo hai hướng ngược nhau
- Ước lượng BIRD : mẫu phân tầng 10% dev -> hơn 30% item có Gold Error. Nguồn thứ hai độc lập với Jin et al. (52.8% trên Mini-Dev), cùng chiều
- Quy trình audit ( §4.3 ) mượn nguyên cho todo #1 : 3 sinh viên thạo SQL, 2 người annotate độc lập theo typology, **Cohen's Kappa = 0.86**, người thứ 3 adjudicate
  - Mốc tham chiếu thứ hai bên cạnh Krippendorff 0.72 / 0.64 của TraceElephant. Gán nhãn *chất lượng gold* dễ đồng thuận hơn hẳn gán nhãn *nguyên nhân lỗi agent* -> nếu repo đo thấp hơn nhiều thì lỗi ở định nghĩa nhãn
- Typology 3 tầng : A SQL-Side (A1 suboptimal / A2 sai ngữ nghĩa-logic, 8 nhánh con / A3 syntax-execution), B NLQ-Side (B1 ambiguity, B2 underspecification, B3 unanswerable), C Database (C1 dirty data, C2 deficient schema)
  - Nhánh A2 map gần 1-1 sang stage của pipeline ( A2.1 -> schema linking; A2.2/A2.3/A2.4/A2.7/A2.8 -> generation ) -> MỘT taxonomy dùng cho cả audit gold lẫn quy lỗi stage, không cần dựng hai bộ nhãn
- **CẢNH BÁO** : hàng "GBV-SQL + No Gold Errors" Spider dev 96.5 / test 97.6 là đo trên subset đã LOẠI BỎ case lỗi nhãn ( không phải sửa ). Số chẩn đoán, không đặt cạnh leaderboard. Hàng này chỉ có cho Spider, KHÔNG có con số BIRD tương ứng

# Ghi chú cho đề tài
- Artifact quan sát được : Planner ( schema đã lọc, sub-question ), Generator ( CoT trace, sub-SQL, SQL ghép ), Validator ( bản dịch ngược, phán quyết, lựa chọn cuối ), Checker ( log lỗi, SQL sau mỗi vòng )
- Novelty : "multi-agent + validator ngữ nghĩa" đã có người làm và đã lên ACL 2026 -> đóng góp của đề tài phải nằm ở **quy lỗi mức case cho từng stage**, không phải thêm agent kiểm chứng
- Không có code public ( grep toàn văn PDF không có `github` ). Danh sách id 183 / 62 nằm ở supplementary, chưa lấy được
- Giới hạn tác giả nêu : chỉ xử lý query "moderately complex" trên một hoặc vài bảng
