# Annotation errors — Jin et al. (UIUC)

Dựng lại 2026-08-24. Đã trích trực tiếp từ bản PDF CIDR nên phần này CHẮC, không phải nhớ lại.

## Hai bài, không phải một

Cùng nhóm: Tengjun Jin, Yoojin Choi, Yuxuan Zhu, Daniel Kang (University of Illinois).

| Bản | Tên | Snow | Cách đo | Re-evaluation |
|---|---|---|---|---|
| CIDR'26 | Text-to-SQL Benchmarks are Broken: An In-Depth Analysis of Annotation Errors | 66.1% | 80 lỗi trên 121 bài có gold SQL public | 5 hệ open-source, đổi -3% tới 31%, thứ hạng dịch tối đa 3 bậc |
| arXiv 2601.08778 v3 (2026-01-19) | Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards | 62.8% | bản mở rộng | 16 agent từ BIRD leaderboard, đổi -7% tới 31%, thứ hạng dịch -9 tới +9 |

BIRD Mini-Dev: 52.8% ở cả hai bản, trên 498 example.

Hai con số Snow KHÔNG mâu thuẫn. Khác bài, khác phạm vi.

## Cách trích đúng

- Dùng bản arXiv (62.8%, 16 agent) làm số chính — mới hơn, mẫu re-evaluation lớn hơn.
- Nhắc bản CIDR khi cần venue peer-reviewed.
- **LUÔN kèm mẫu số.** Tỉ lệ Snow đo trên 121 bài có gold public, KHÔNG phải 547, và không
  phải mẫu ngẫu nhiên. Đừng viết gọn thành "62.8% của Spider 2.0".

## Bốn pattern lỗi họ định nghĩa

- E1 — ngữ nghĩa câu hỏi lệch với logic mà gold SQL định làm
- E2 — câu hỏi lệch với dữ liệu/schema thật, do người annotate không hiểu dữ liệu
- E3 — lệch với domain knowledge, hoặc chính domain knowledge bị annotate sai
- E4 — câu hỏi mơ hồ

E2 là pattern hay gặp nhất ở cả hai benchmark: 57.8% trên BIRD Mini-Dev, 55% trên Snow.

## Ví dụ cụ thể họ đưa (Spider 2.0-Snow)

- E1 — annotator dùng TO_TIMESTAMP(end_date), cast ngày về ĐẦU ngày chứ không phải cuối ngày,
  nên gold query sót các dòng xảy ra sau 00:00:00 của ngày cuối
- E2 — không kiểm kết quả trung gian sau JOIN hoặc FLATTEN, làm phồng số dòng (4 ví dụ)
- E3 — tính forward citation sai: join nhầm cited.patent_id = apps.patent_id
  thay vì cited.citation_id = apps.patent_id
- E4 — 7 câu hỏi mơ hồ về format output, yêu cầu thay dấu nháy. Agent nào sinh SQL có dấu
  nháy là bị chấm sai.

BIRD Mini-Dev:
- E1 — dùng BETWEEN...AND cho bất đẳng thức chặt (> hoặc <)
- E2 — với DB california_schools, câu hỏi hỏi về trường học nhưng gold bỏ điều kiện
  rtype = 'S' (thứ phân biệt school với district). Annotator còn đánh dấu cột rtype là
  "unuseful" trong khi chính nó là cột phân biệt.
- E3 — hiểu sai "K-12" trong 3 ví dụ, "+n Lap" trong 4 ví dụ

## Hệ quả nặng nhất

Chấm lại 16 agent open-source trên BIRD bằng nhãn đã sửa:
- tương quan xếp hạng với full Dev tụt từ Spearman 0.85 (p=3.26e-5) xuống 0.32 (p=0.23)

Tức là: **subset đã sửa nhãn KHÔNG còn dự đoán được thứ hạng trên full Dev.**
Thứ hạng leaderboard gần như mất nghĩa.

## Vì sao đây là mối đe dọa trực tiếp cho đề tài

Không phải cảnh báo phụ. Mỗi case bị quy "pipeline sai" có xác suất đáng kể thật ra là
"gold sai". Không có bước kiểm nhãn trên sample thì mọi bảng attribution đều có thể đang đo
nhiễu annotation.

Kết hợp với GBV-SQL (62 case "đúng nhờ nhãn sai" trên Spider dev) thì nhiễu đi cả hai chiều:
vừa tạo lỗi giả, vừa tạo đúng giả.

Việc phải làm: kiểm tay khoảng 50 case sai từ run SParC/BIRD đã có, TRƯỚC mọi bảng attribution.

## Nguồn

- vldb.org/cidrdb/papers/2026/p5-jin.pdf (CIDR'26, 18-21/01/2026, Chaminade USA)
- arxiv.org/abs/2601.08778
