# Audit chất lượng nhãn + độ chặt của metric — SParC dev, 2026-08-22

> Bước 1 của hướng "khai thác dữ liệu sẵn có". Toàn bộ read-only trên 4 run đã hoàn tất;
> không file run nào bị sửa.
>
> **[verified]** = tính trực tiếp trên dữ liệu local · **[suy luận]** = nhận định chưa kiểm chứng

## Vì sao có thư mục này

Hai paper đọc ngày `2026-08-22` buộc phải kiểm nhãn trước khi phân tích attribution:

- [GBV-SQL](../../../../notes/baselines/gbv-sql.md) (ACL 2026) tìm thấy `183` Gold Error trong case fail
  **và `62` trong case pass** trên Spider dev — nhãn sai tạo cả điểm sai lẫn **điểm đúng giả**.
- [Annotation errors](../../../../notes/review_week_2026-08-22_spider2_landscape.md) (arXiv 2601.08778):
  chấm lại `16` agent bằng nhãn đã sửa làm tương quan xếp hạng tụt từ `r=0.85` xuống `r=0.32`.

Nếu ~1/5 số "failure" không phải failure, mọi bảng attribution xây trên đó đang đo nhiễu.

## Phần 1 — Sample để audit tay

Script: [`../build_gold_error_audit_sample.py`](../build_gold_error_audit_sample.py) · seed `20260822`

Ý tưởng: dùng **sự đồng thuận giữa 4 framework** làm tín hiệu ưu tiên. Nếu cả 4 hệ đều sai mà phần lớn
lại cho *cùng một kết quả* khác gold, khả năng cao là gold sai, chứ không phải 4 hệ độc lập cùng sai theo
một kiểu.

| Stratum | Định nghĩa | Population **[verified]** | Lấy mẫu |
|---|---|---:|---:|
| `A_all_wrong_agree` | cả 4 sai, ≥3 cho cùng `result_hash` | `176` | `30` |
| `B_all_wrong_diverge` | cả 4 sai, không đồng thuận | `116` | `25` |
| `C_mixed` | có cả đúng lẫn sai | `416` | `20` |
| `D_all_correct` | cả 4 đúng (tìm case "đúng nhờ nhãn sai") | `495` | `25` |

Output:

- `audit_sheet.csv` — bảng để gán nhãn tay; cột trống `gold_error_type` (`A`/`B`/`C`/`none` theo typology
  GBV-SQL), `gold_error_note`, `annotator`.
- `audit_cases.jsonl` — chi tiết đầy đủ từng case, gồm SQL của cả 4 framework.
- `sample_manifest.json` — seed, population, nguồn.

**Chưa ai gán nhãn.** Bảng hiện đang trống cột annotation.

## Phần 2 — Chẩn đoán độ chặt của metric **[verified]**

Script: [`../diagnose_metric_strictness.py`](../diagnose_metric_strictness.py)

Kiểm mẫu vài case ở stratum A cho thấy một pattern lặp lại, không phải lỗi suy luận:

| idx | Câu hỏi | Gold | Cả 4 hệ sinh ra |
|---:|---|---|---|
| `153` | "countries in the Caribbean region?" | `SELECT * FROM country WHERE Region='Caribbean'` | `SELECT Name FROM country WHERE ...` |
| `304` | "minimum and maximum share" | `SELECT max(SHARE), min(SHARE)` | `SELECT MIN(Share), MAX(Share)` |
| `365` | "count the number of people for each nationality" | `SELECT COUNT(*) ... GROUP BY Nationality` | `SELECT Nationality, COUNT(*) ... GROUP BY Nationality` |

Ba dạng: **thừa/thiếu cột chiếu**, **sai thứ tự cột**, **`SELECT *` vs cột cụ thể**. Không cái nào là lỗi
hiểu câu hỏi — idx `304` thậm chí đúng thứ tự mà câu hỏi nêu.

Chạy lại toàn bộ `1203` case × 4 framework trên SQLite local, so kết quả theo ba mức:

- `exact` — như `result_hash` hiện tại: đúng thứ tự cột.
- `colperm` — bỏ qua thứ tự cột (sort các ô trong mỗi hàng trước khi so). **Chặt, an toàn.**
- `projection` — chỉ đòi mọi cột của gold có mặt trong pred, pred được phép thừa cột; số hàng bằng nhau.
  **Lỏng — bỏ qua tương ứng hàng-với-hàng, chỉ dùng làm chẩn đoán, không phải metric báo cáo.**

| Framework | `EX` hiện tại | `EX` nếu `colperm` | `EX` nếu `projection` | % failure được "cứu" |
|---|---:|---:|---:|---:|
| 04_din_sql | `0.5719` | `0.5885` | `0.6475` | `17.7%` |
| 06_mac_sql | `0.5919` | `0.6126` | `0.6825` | `22.2%` |
| 20_c3sql | `0.5919` | `0.6135` | `0.6417` | `12.2%` |
| 21_dail_sql | **`0.6052`** | **`0.6226`** | `0.6617` | `14.3%` |

### Ba hệ quả

1. **`12.2%`–`22.2%` số "failure" là artifact của cách so kết quả, không phải lỗi hệ thống.** Với DIN-SQL
   đó là `91` trên `515` case sai.
2. **Thứ hạng đổi.** Theo `EX` hiện tại: `DAIL > MAC = C3 > DIN`. Theo `projection`:
   `MAC (0.6825) > DAIL (0.6617) > DIN (0.6475) > C3 (0.6417)` — MAC-SQL từ hạng nhì lên hạng nhất.
   Đây đúng hiện tượng mà bài annotation-error mô tả, nhưng nguyên nhân ở đây là **implementation của
   metric**, không phải nhãn.
3. **Mức độ bị phạt khác nhau giữa framework** (`12.2%` vs `22.2%`), nên artifact này **không** triệt tiêu
   khi so sánh tương đối. MAC-SQL bị phạt nặng nhất vì hay chiếu thêm cột ngữ cảnh.

### Ảnh hưởng trực tiếp tới attribution **[suy luận]**

Một case bị chấm sai vì thừa cột sẽ được quy lỗi cho stage sinh SQL, trong khi thực chất không stage nào
sai. Nếu tỉ lệ này khoảng `1/5` và **lệch giữa các framework**, mediation analysis sẽ gán effect giả cho
generation stage, và gán mạnh hơn ở framework nào hay chiếu thừa cột. Đây là confounder có hệ thống, không
phải nhiễu ngẫu nhiên.

## Việc tiếp theo

1. Gán nhãn `audit_sheet.csv` (`100` case) theo typology A/B/C — cần người làm, chưa tự động hoá được.
2. Chốt định nghĩa `EX` dùng cho phần attribution. Đề xuất **[suy luận]**: giữ `exact` làm metric báo cáo
   để so với lịch sử, nhưng **loại các case `colperm`/`projection` khỏi tập phân tích attribution**, hoặc
   gán chúng nhãn riêng `metric_artifact` thay vì quy lỗi cho stage.
3. ~~Kiểm chéo A với case được "cứu"~~ — đã làm, kết quả ngay dưới.

## Phần 3 — Kiểm chéo hai tín hiệu **[verified]**

| | n | Cả 4 framework được "cứu" bởi metric lỏng | ≥1 được cứu |
|---|---:|---:|---:|
| `A_all_wrong_agree` | `176` | `25` (`14.2%`) | `39` |
| `B_all_wrong_diverge` | `116` | `3` (`2.6%`) | — |

Hai tín hiệu **phần lớn không trùng nhau**: chỉ `14.2%` nhóm A giải thích được bằng metric. Còn lại
**`137` case** vừa bị cả 4 hệ trả lời giống nhau khác gold, vừa không phải artifact metric — đây là nhóm
nghi vấn gold error mạnh nhất, và là nơi audit tay đáng bỏ công nhất.

Nhóm B ngược lại: chỉ `2.6%` là artifact, tức phần lớn `116` case đó là **failure thật** — nhóm này mới là
dữ liệu sạch cho attribution.

**[suy luận]** Vậy có ba tập tách biệt, không phải một: `metric artifact` (~`12`–`22%` số failure),
`nghi gold error` (`137` case), và `failure thật`. Attribution chỉ nên chạy trên tập thứ ba. Đây là lý do
kỹ thuật để tách nhãn `metric_artifact` ra khỏi pipeline gán nhãn, chứ không gộp vào "sai".

Điểm 2 là **quyết định methodology, cần human checkpoint** — không tự đổi.

## Giới hạn

- `projection` bỏ qua tương ứng hàng-với-hàng nên là **cận trên**; con số thật nằm giữa `colperm` và
  `projection`.
- Chỉ chạy trên SParC dev, adapted run, backbone `gpt-4o-mini`. Chưa kiểm trên BIRD/Spider dev.
- Việc chạy lại SQL dùng SQLite local trong `datasets/text2sql/sparc/sparc/database`; không đối chiếu với
  evaluator gốc của SParC (vốn dùng `EM`).
