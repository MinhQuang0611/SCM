# GBV-SQL

Viết lại 2026-08-24 (đợt 2). **Đọc trực tiếp từ PDF arXiv 2509.12612**, trích bằng `pdftotext -layout`.
Paper gần đề tài nhất trong nhóm đã đọc.

## Thông tin

- Tên: GBV-SQL: Guided Generation and SQL2Text Back-Translation Validation for Multi-Agent Text2SQL
- Tác giả: Daojun Chen, Xi Wang, Shenyuan Ren, Qingzhi Ma, Pengpeng Zhao, An Liu
- Venue: ACL 2026 Main (Long), tr. 18391-18406 — aclanthology.org/2026.acl-long.837/
- Preprint: arxiv.org/abs/2509.12612 (2025-09-16)
- Code: KHÔNG. `grep` toàn văn PDF không có chuỗi `github`, không có statement release.

## Vì sao phải đọc kỹ

Nó đụng đồng thời hai thứ đề tài đang làm:

1. multi-agent Text2SQL có agent chuyên kiểm chứng ngữ nghĩa — một mediator được thiết kế tường minh,
   có ablation đo riêng
2. audit chất lượng benchmark, kèm typology "Gold Errors" và quy trình annotate có đo agreement

Đọc để định vị lại đóng góp, không phải để bỏ hướng.

## Bài toán

ReFoRCE hỏi "làm sao sinh SQL tốt hơn". GBV-SQL hỏi "làm sao biết SQL này có đúng ý người hỏi không".

Vì SQL có thể:

```
[ok] đúng cú pháp
[ok] chạy ra kết quả
[X]  SAI Ý NGƯỜI HỎI
```

Ví dụ chính paper dùng (Figure 1, BIRD dev):

```
Question: Which school has an average writing score of 499?
```

```sql
-- Pred SQL: chạy được, nhưng gom nhóm theo charter
SELECT AVG(T2.AvgScrWrite)
FROM schools AS T1
JOIN satscores AS T2 ON T1.CDSCode = T2.cds
GROUP BY T1.Charter
```

```sql
-- Gold: người hỏi muốn MỘT trường có điểm bằng 499
SELECT T1.CharterNum
FROM schools AS T1
INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds
WHERE T2.AvgScrWrite = 499
```

Execution check KHÔNG bắt được loại lỗi này — query chạy trơn tru. Đây là silent failure, đúng loại lỗi
mà EX không nhìn thấy.

## Ý tưởng: dịch ngược SQL về tiếng người

```
Question gốc  --------------------------+
                                        |
SQL sinh ra --> dịch ngược --> "Câu này hỏi gì?"
                                        |
                                        v
                                 SO SÁNH HAI CÂU
                                        |
                            +-----------+-----------+
                           khớp                   lệch
                            |                       |
                            v                       v
                         Output                  Sửa SQL
```

Cụ thể:

```sql
SELECT name FROM student WHERE age > 20
```
-> dịch ngược -> "Trả về tên của các sinh viên trên 20 tuổi."
-> so với câu hỏi gốc -> khớp -> chấp nhận.

Nếu SQL là `GROUP BY department ORDER BY SUM(salary)` thì bản dịch ngược sẽ là "phòng ban có tổng lương
cao nhất", so với câu hỏi "phòng ban có lương trung bình cao nhất" -> lệch -> sửa.

Ý tưởng trung tâm: **back-translation làm proxy cho ý định người dùng.**

## Bốn agent

```
Question
   |
   v
+------------------------------------------+
| 1. PLANNER                               |
|    prune schema, làm rõ PK/FK            |
|    tách câu hỏi thành sub-question        |
+------------------+-----------------------+
                   v
+------------------------------------------+
| 2. SQL GENERATOR                         |
|    Human-like CoT: xác định ý định ->    |
|    chọn bảng/cột -> dựng từng mệnh đề    |
|    sinh sub-SQL rồi ghép                 |
+------------------+-----------------------+
                   v
+------------------------------------------+
| 3. SQL2TEXT VALIDATOR   <- đóng góp chính|
|    SQL -> tiếng người -> so câu hỏi gốc  |
|    lệch thì sửa; binary selector chọn    |
|    giữa bản gốc và bản đã sửa            |
+------------------+-----------------------+
                   v
+------------------------------------------+
| 4. SQL CHECKER                           |
|    format, syntax, execution             |
|    TỐI ĐA 3 VÒNG repair                  |
|    truy giá trị thật trong DB để sửa     |
+------------------+-----------------------+
                   v
              Final SQL
```

Planner tách câu hỏi theo kiểu Targets-Conditions:

```
"Find customers who bought products after 2023 and spent more than $1000"

Targets:     customer name
Conditions:  purchase_date > 2023-01-01
             SUM(amount) > 1000
```

Artifact quan sát được từng agent:

| Agent | Artifact |
|---|---|
| Planner | schema đã lọc, danh sách sub-question |
| SQLGenerator | CoT trace, sub-SQL, SQL ghép |
| SQL2TextValidator | bản dịch ngược, phán quyết, lựa chọn cuối |
| SQLChecker | log lỗi, SQL sau mỗi vòng (tối đa 3) |

Setting: Deepseek-v3 chính + GPT-4o phụ để validate, T = 0.

## Kết quả

BIRD dev, nền Deepseek-v3:

| | Simple | Moderate | Challenging | **Total** |
|---|---:|---:|---:|---:|
| GBV-SQL | 69.51 | 54.62 | 50.69 | **63.23** |

Hơn MAC-SQL cùng backbone 5.8 điểm. Spider: dev 79.6 / test 82.8 (Deepseek-v3), 79.7 / 83.9 (GPT-4o).
Cả hai hơn MAC-SQL 5.2 trên test.

## Ablation trên BIRD dev

| Cấu hình | Simple | Mod. | Chall. | Total | Loại can thiệp |
|---|---:|---:|---:|---:|---|
| GBV-SQL + Deepseek-v3 | 69.51 | 54.62 | 50.69 | 63.23 | — |
| w/o Planner | 68.76 | 53.98 | 45.83 | 62.13 (-1.10) | **thay bằng MAC-SQL** |
| w/o SQLGenerator | 67.78 | 53.76 | 48.61 | 61.73 (-1.50) | **thay bằng MAC-SQL** |
| w/o SQL2TextValidator | 68.54 | 52.69 | 47.92 | 61.80 (-1.43) | bỏ hẳn |
| w/o Human-like CoT | 66.70 | 52.90 | 51.39 | 61.08 (-2.15) | thay bằng zero-shot prompt |
| w/o SQLChecker | 66.49 | 49.89 | 47.22 | 59.65 (-3.58) | bỏ hẳn |

```
Bỏ SQLChecker           ########  -3.58
Bỏ Human-like CoT       #####     -2.15
Thay SQLGenerator       ###       -1.50
Bỏ SQL2TextValidator    ###       -1.43
Thay Planner            ##        -1.10
```

**Chính tác giả phát biểu, không phải mình suy ra.** §4.4 nguyên văn:

  "Notably, ablating the SQLChecker, which handles final formatting and executability analysis, causes
   the most significant performance drop."

  "This underscores the profound impact of query executability and proper formatting on the current
   execution based (EX) evaluation paradigm."

Có một điều trớ trêu: agent đóng góp nhiều nhất là cái SỬA SYNTAX, không phải validator ngữ nghĩa — vốn
là đóng góp mới của chính họ (chỉ -1.43).

### CÁI BẪY khi đọc bảng này — mới phát hiện 2026-08-24

Nguyên văn §4.4: *"'w/o Planner/SQLGenerator' indicates **replacement with MAC-SQL's modules**, while
other variants remove the specified component."*

Nghĩa là ablation này LOẠI HỖN HỢP:
- `-1.10` của Planner = "Planner của GBV so với Planner của MAC-SQL" (thay thế)
- `-3.58` của SQLChecker = "có hay không có" (bỏ hẳn)

KHÔNG xếp hạng 5 module trên cùng một thang được. Phát biểu của tác giả vẫn đúng trong nhóm *bỏ hẳn*
(SQLChecker -3.58 > SQL2TextValidator -1.43), nhưng so nó với Planner/SQLGenerator là so hai loại can
thiệp khác nhau.

Suy ra: điều này LÀM MẠNH THÊM lập luận "LOO ablation không đủ" theo một hướng mới — ngay trong MỘT
paper, năm dòng của cùng một bảng ablation đã không cùng đơn vị. Người đọc bảng, kể cả reviewer, mặc
định đó là leave-one-out. Đây là luận cứ tốt hơn cách nói "các paper kết luận khác nhau", vì không cần
ghép chéo giữa các paper.

## Đóng góp thứ hai: "Gold Errors"

Đọc tay toàn bộ case fail execution trên Spider dev:

```
Case fail execution trên Spider dev: 220
      |
      +-- 183  <- LỖI CỦA BENCHMARK (gold sai)
      +--  37  <- lỗi thật của model
```

83% "thất bại" không phải model sai mà là nhãn sai.

Ví dụ họ đưa (Figure 7): database `flight_2` có space thừa trong TEXT attribute, khiến nhiều gold SQL
chính thức chạy sai — trong khi GBV-SQL lại xử lý đúng dữ liệu bẩn đó nên bị chấm là fail.

Ngoài ra: 62 Gold Error nằm trong nhóm case PASS. Tức **có case "đúng" nhờ nhãn sai.** Nhiễu annotation
không chỉ làm hệ bị chấm oan, nó còn tạo điểm đúng giả. Với attribution, cả hai chiều đều làm lệch kết
quả, theo hai hướng ngược nhau.

Ước lượng cho BIRD: mẫu phân tầng 10% của BIRD dev -> **hơn 30%** item có Gold Error. Đây là nguồn thứ
hai, độc lập với Jin et al. (52.8% trên Mini-Dev), cùng chiều. Trích được cả hai thì lập luận chắc hơn
dùng một.

### Quy trình audit nhãn — mượn nguyên cho todo #1

§4.3 nguyên văn:

  "The process is conducted by three SQL-proficient graduate students. Initially, two students
   independently inspect and classify potential quality issues in every data item according to our
   proposed typology (Figure 5), achieving a substantial inter-annotator agreement (Cohen's Kappa = 0.86).
   A third student then adjudicates all disagreements to make the final classification."

Đây là template làm sẵn cho việc "kiểm nhãn tay ~50 case sai": 2 annotator độc lập + 1 adjudicator,
có số agreement công bố.

`kappa = 0.86` là MỐC THAM CHIẾU THỨ HAI bên cạnh Krippendorff 0.72 / 0.64 của TraceElephant. Khác biệt
đáng chú ý: gán nhãn *chất lượng gold* dễ đồng thuận hơn hẳn gán nhãn *nguyên nhân lỗi agent*. Nghĩa là
bước audit nhãn của repo nên đạt agreement cao; nếu thấp hơn nhiều thì lỗi ở định nghĩa nhãn, không phải
ở độ khó bài toán.

### Typology Gold Error — ba tầng, không phải ba loại

```
A. SQL-Side          A1 Suboptimal SQL Representation
                     A2 Incorrect Semantic & Logical Implementation
                        +- A2.1 sai bảng/cột
                        +- A2.2 sai JOIN logic
                        +- A2.3 sai WHERE/HAVING (improper query conditions)
                        +- A2.4 sai aggregation / GROUP BY
                        +- A2.5 hardcode sai giá trị (incorrect value usage)
                        +- A2.6 nuanced: A2.6.1 NULL handling, A2.6.2 implicit type conversion
                        +- A2.7 sai sorting (cột hoặc ASC/DESC)
                        +- A2.8 deduplication (thiếu/thừa DISTINCT)
                     A3 Syntactic & Execution
                        +- A3.1 Syntax Errors
                        +- A3.2 Schema Mismatch (tham chiếu bảng/cột không tồn tại)

B. NLQ-Side          B1 Ambiguity
                        +- B1.1 Lexical/Semantic  B1.2 Syntactic  B1.3 Schema-Induced
                     B2 Underspecification & Implicit Assumptions
                        +- B2.1 Implicit Assumptions  B2.2 Ambiguous JOIN Decisions
                     B3 Unanswerable or Self-Contradictory Questions

C. Database          C1 Dirty Data
                     C2 Deficient Schema Design
```

Nhánh A2 map gần như 1-1 sang các stage của pipeline text-to-SQL (A2.1 -> schema linking; A2.2/A2.3 ->
generation; A2.4/A2.7/A2.8 -> generation). Nghĩa là MỘT taxonomy dùng được cho cả hai chiều: audit gold
trước, rồi tái dùng chính nhãn đó để quy lỗi cho stage. Không cần dựng hai bộ nhãn riêng như note cũ
giả định.

Đối chiếu: typology A/B/C này phân loại lỗi CỦA BENCHMARK. Taxonomy của CogSQL (schema misuse, keyword
misuse...) phân loại lỗi CỦA MODEL. Quy trình gán nhãn của repo cần cả hai, và thứ tự là: kiểm Gold Error
trước, rồi mới quy lỗi cho stage.

## CẢNH BÁO khi trích 96.5 / 97.6

Table 2 có hàng "GBV-SQL + No Gold Errors": Spider dev 96.5 / test 97.6.

Caption nguyên văn: *"The 'No Gold Errors' designation indicates evaluation on a cleaned subset of the
benchmark, from which entries with quality issues have been **removed**."*

Tức là LOẠI BỎ, không phải sửa. Đây là con số CHẨN ĐOÁN — cho biết bao nhiêu phần "sai" thật ra là nhãn
sai — không phải điểm hiệu năng. Không đặt cạnh số leaderboard.

SỬA LỖI TRONG NOTE CŨ: bản trước ghi "BIRD dev 90.42" sau khi sửa nhãn. Con số này KHÔNG có trong paper.
Hàng "No Gold Errors" chỉ tồn tại cho Spider. Đã bỏ.

## Giới hạn tác giả nêu

- Chỉ xử lý query "moderately complex" trên một hoặc vài bảng
- Kịch bản enterprise kiểu Spider 2.0 để lại cho future work

## Tóm tắt một câu

GBV-SQL thêm một semantic verifier vào pipeline: dịch SQL ngược về tiếng người rồi so với câu hỏi gốc để
bắt loại lỗi "chạy được nhưng sai ý"; đồng thời chỉ ra rằng phần lớn thất bại đo được trên Spider thực ra
là lỗi của benchmark chứ không phải của model.

## Ý nghĩa với đề tài

- Novelty: "multi-agent + validator ngữ nghĩa" đã có người làm và đã lên ACL 2026. Đóng góp còn lại của
  đề tài phải nằm ở chỗ khác: **quy lỗi ở mức case cho từng stage**, không phải thêm một agent kiểm chứng.
- Phương pháp: mượn nguyên typology 3 tầng + quy trình 2+1 annotator làm bước tiền xử lý (todo #1).
- Đối chứng: nếu dựng lại được, GBV-SQL có 4 agent tách bạch và có sẵn ablation để so với kết quả
  attribution. Nếu attribution nói SQLChecker là mediator chính thì khớp với ablation của họ — một dạng
  kiểm chứng chéo không cần annotate tay. Nhưng nhớ cái bẫy loại-can-thiệp ở trên.

## Chưa xác minh

- Danh sách id 183 / 62 có release không. Paper ghi chi tiết Spider test set nằm ở supplementary
  "due to space limitations" — không có trong PDF chính. Chưa lấy được id.
- 63.23 đo trên Deepseek-v3; muốn so với run trong repo (gpt-4o-mini) phải đối chiếu backbone.
