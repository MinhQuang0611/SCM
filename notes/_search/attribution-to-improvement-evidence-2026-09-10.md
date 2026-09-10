# Attribution → improvement: bằng chứng thực nghiệm ba nhánh

> Rà ngày **2026-09-10**. Câu hỏi gốc: *"Failure attribution có dẫn tới cải thiện accuracy ĐO ĐƯỢC
> không, và bằng chứng ở đâu?"* — phát sinh khi contribution của đề tài bị chất vấn: không thể lấy
> "chưa ai làm" làm lý do thêm một khung phân tích vào pipeline.

> [!abstract] Kết luận một câu
> Bằng chứng **tách đôi theo consumer**: khi kết quả attribution được tiêu thụ bởi **một tool tự
> động**, có bằng chứng benchmark mạnh và lặp lại được (tới **2×** repair rate). Khi consumer là
> **con người**, 15 năm literature SE gần như **không** có bằng chứng ủng hộ nào vượt kiểm định, và
> có bằng chứng phủ định trực tiếp rằng **thay đổi thứ hạng dòng lỗi không tạo hiệu ứng đo được**.

---

## Nhánh A — LLM multi-agent systems

**Câu hỏi**: đã có ai đóng vòng `attribution → fix → re-measure` chưa?

Phải tách hai mức, nếu không sẽ đọc nhầm hàng loạt paper:
- **Vòng mức case**: sửa/chạy lại chính case đã fail (re-rollout, inject feedback). Hệ không đổi.
- **Vòng mức hệ**: sửa chính hệ (prompt, module, topology), chạy lại toàn benchmark.

### Nhóm KHÔNG đóng vòng — và toàn bộ là venue peer-reviewed tier cao

| Công trình | Venue | Kết quả báo cáo |
|---|---|---|
| Who&When [1] | **ICML 2025** | agent-level `53.5%`, step-level `14.2%`. Không có thí nghiệm feed attribution ngược lại MAS |
| TraceElephant [3] | **ACL 2026 Long** | agent `65.9%` / step `30.3%`. Có reproducible execution environment nhưng **không** chạy repair |
| EDGE [4] | **EMNLP 2026 Main** | counterfactual rollout dùng để *validate cạnh nhân quả*, không để sửa hệ |
| AgentLocate [5] | **COLM 2026** | attribution accuracy + token/runtime. Không repair |
| AIG [14] | arXiv, chưa xác nhận venue | SOTA trên Who&When. Chỉ đo attribution |
| MASPrism [15] | arXiv, chưa xác nhận venue | Oracle-free, **thiết kế loại bỏ** khả năng replay |

Không công trình nào nêu trong Limitations rằng "chưa chứng minh attribution dẫn tới cải thiện" —
chỉ ngầm định qua motivation. Đây là điểm yếu chung có thể tấn công.

### Nhóm CÓ đóng vòng — bảy công trình, **tất cả đều arXiv-only**

| Công trình | Mức | Con số |
|---|---|---|
| **Ma et al. causal** [7] | case | Who&When, 50 trajectory fail: `15.4% → 37.8%`, **control ngẫu nhiên `18.3%`** |
| AgentDebugX [9] | case | Who&When attribution `28.8%` vs `21.7%`; GAIA `55.8% → 63.6%`, sửa `13/73` vs `4–6` baseline |
| AgentDebug [6] | case | ALFWorld `21→55`, `48→74`, `60→84` (qua tối đa 5 re-rollout). **ICLR 2026 đã withdrawn** |
| CausalFlow [11] | case | repair rate TB `42.7%`; accuracy `+13.1` đến `+30.8` pp trên 4 benchmark |
| TrajDebug [10] | case + transfer | oracle: Airline `78→90`; **memory transfer (thực tế hơn)**: `+4.5` đến `+6.6` pp |
| DoVer [8] | case | recover `18–28%` trial fail (GAIA), `49%` (GSMPlus). Không có accuracy toàn benchmark |
| Agents that Matter [12] | **hệ** | `+17%` task performance, `−35%` cost. Nhưng là *contribution* attribution, không phải *failure* |

**MAST** [2] (NeurIPS 2025) là ngoại lệ peer-reviewed duy nhất chạm mức hệ: ChatDev `+9.4%` và
`+15.6%`. Nhưng MAST **không có phương pháp attribution tự động** — người đọc taxonomy rồi sửa tay.
Chính tác giả nói gain không đủ: *"not all failure modes are resolved... more substantial
improvements are needed."*

### Ba khoảng trống còn lại

1. **Chưa ai lấy output của một thuật toán attribution tự động, dịch thành thay đổi cấu hình hệ,
   rồi đo lại toàn benchmark.** Vòng mức hệ chỉ có [2] và [12], cả hai không dùng attribution per-case.
2. **Chưa ai đóng vòng trong Text-to-SQL** (xem nhánh B).
3. **Chỉ `1/7` có control ngẫu nhiên.** Sáu công trình còn lại không tách được gain do *attribution
   chỉ đúng chỗ* khỏi gain do *cứ thử lại thì kiểu gì cũng khá hơn*.

Survey [17] xác nhận, mục 4.5.1 tiêu đề **"The Evaluation–Repair Loop Remains Incomplete"**:
*"without the ability to act on diagnostic results, attribution yields limited practical value."*

---

## Nhánh B — Text-to-SQL

**Câu hỏi**: có ai dùng stage-level diagnosis để motivate thay đổi kiến trúc rồi đo EX trước/sau?

### CÓ — bốn công trình peer-reviewed

| Công trình | Venue | Chẩn đoán | EX trước → sau |
|---|---|---|---|
| DIN-SQL [B1] | NeurIPS 2023 | đọc tay 500 query Spider train → "schema linking là nhóm lỗi lớn nhất" | `67.4 → 85.3` (dev vs test, **không cùng split**) |
| TA-SQL [B2] | Findings ACL 2024 | taxonomy hallucination có tỉ lệ, một module cho một nhóm lỗi | BIRD dev `46.35 → 56.19` |
| MapleRepair [B3] | **FSE 2026** | `4.602` SQL sai, 3 người gán nhãn độc lập, ~840 person-hours | repair `+13.8%`, latency `−67.4%` |
| MAGIC [B5] | AAAI-25 | agent tự sinh guideline từ failure của train set | BIRD `56.52 → 59.13` |

Điểm chung: **chẩn đoán bằng đọc tay ở mức aggregate**. Không công trình nào dùng attribution
**mức case** để quyết định sửa stage nào.

Gần nhất về phương pháp là **Rethinking Schema Linking** [B6] (Findings EACL 2026): dùng **oracle
upper-bound** đo khoảng cách full-schema → perfect-schema, thu hẹp `50%` khoảng cách đó. Đây **là**
một can thiệp kiểu mediation, chỉ khác là báo cáo ở mức tập dữ liệu chứ không mức case. APEX-SQL
cũng có setting oracle schema tương tự.

### Chẩn đoán aggregate đã bị chứng minh SAI — năm lần độc lập

Đây là phát hiện đáng giá nhất của cả ba nhánh.

1. **"The Death of Schema Linking?"** [B4] (NeurIPS 2024 TRL Workshop) — oracle schema linker bằng
   SQLGlot, bơm false positive `99% → 0%` trên 12 model. Model mạnh **gần như miễn nhiễm** với
   schema nhiễu; thêm schema linking truyền thống **làm giảm** EX. Hạng 1 BIRD `71.83%` **không có**
   schema linking. Nguyên văn: *"the benefit of schema linking diminishes... can result in a net
   reduction in accuracy."*
2. **DIN-SQL Table 5** (chính bài đó, ít ai trích) — cùng một generic self-correction: CodeX
   `67.3 → 69.9` (+2.6) nhưng GPT-4 `73.3 → 70.0` (**−3.3**). Tác giả: *"can hurt the performance."*
3. **CogSQL** — gỡ schema linking mất `1.80` EX trên Spider nhưng chỉ `0.52` trên BIRD.
4. **ReFoRCE** — `Pass@8 +7` mà EX chỉ `+0.37`.
5. **APEX-SQL** — selection gap: Pass@8 `79.17` nhưng voting chốt `57.50`.

### KHÔNG tính

MAC-SQL, CHESS, GBV-SQL, SQLFixAgent, RSL-SQL đều là **ablation**. Dr.Spider (ICLR 2023) là
**diagnostic benchmark** — chẩn đoán tốt nhưng chính paper đó không sửa kiến trúc rồi đo lại; vòng
chỉ được đóng bởi paper khác (Solid-SQL). BIRD-CRITIC là benchmark debugging.

---

## Nhánh C — Software engineering (đối chứng lâu đời nhất)

**Câu hỏi**: fault localization tốt hơn có dẫn tới repair tốt hơn không?

### Phía PHỦ ĐỊNH — consumer là người

**Parnin & Orso, ISSTA 2011** [C1] (ISSTA 2021 Impact Paper Award). Controlled experiment, 24 + 10
sinh viên, Tarantula ranked list.
- **Hypothesis 3 — kết quả quan trọng nhất**: can thiệp nhân tạo vào rank. Hạ dòng lỗi Tetris
  `7 → 35`; nâng NanoXML `83 → 16`. Kết quả: **không có khác biệt significant**; tỉ lệ thời gian
  Tetris/NanoXML **`.79` giống hệt ở cả hai nhóm**. Nguyên văn: *"the rank of the faulty statement(s)
  may not be as important as other factors or strategies."*
- **Cơ chế**: developer **không đọc list theo thứ tự**. 37% số click nhảy quá 1 vị trí, trung bình
  bỏ qua **10 vị trí**; TB **10.3 lần zigzag**. Ngoại lệ duy nhất: low performer duyệt tuần tự `95%`
  — *chỉ người kém mới tuân theo ranking*.
- **Bác "perfect bug understanding"**: 10/24 người từng click đúng dòng lỗi, **chỉ 1 người dừng lại**.
  9 người còn lại tiêu thêm TB 10 phút = **61% tổng thời gian sau khi đã chạm đúng chỗ**.

**Xie et al., ICSE 2016** [C5] — replication của Parnin & Orso với eye/focus-tracking. SBFL **không**
cải thiện hiệu quả debugging; pattern điều hướng không khớp ranked list. *(n = 207 participants /
17 tasks lấy từ nguồn thứ cấp, **chưa đối chiếu bản gốc**.)*

**Kochhar et al., ISSTA 2016** [C2] — survey `386` practitioner, >30 quốc gia.
- `~9%` chỉ chấp nhận **Top-1**; `73.58%` đặt ngưỡng **5 elements**; cộng lại **`>80%` yêu cầu Top-5**;
  **`~98%` từ chối quá Top-10**.
- Review FL paper 2011–2015 ở ICSE/FSE/ISSTA/TSE/TOSEM theo chính tiêu chí Top-5: **không paper nào**
  thoả mãn ≥75% respondent. Chỉ 5 paper thoả ≥50%, và cả 5 dùng granularity class/file mà đa số từ chối.
- Kinh nghiệm càng cao càng ít coi FL là "Essential": Spearman `ρ = −0.14, p = 0.007`.

**Pearson et al., ICSE 2017** [C3] — phủ định **tính hợp lệ của cả cơ sở bằng chứng**. Trên `2.995`
lỗi nhân tạo: `7/10` claim significant nhưng **chỉ `3/10`** có effect size non-negligible. Trên `310`
lỗi thật: ***"Every previous result was refuted or was statistically and practically insignificant."***

**Soremekun et al., ICSE 2023** [C4] — `352` bug, `46` chương trình C, `19` kỹ thuật AFL, `76`
professional developer. Ba giả định (fix location = root cause; single fault; perfect bug
understanding) có mặt trong **`55%`** thí nghiệm được khảo sát, và làm AFL **có vẻ hiệu quả hơn tới
`38%`**. Giả định "fix location" phổ biến nhất (**`76%`** thí nghiệm) đồng thời bị `83%` developer
đánh giá là cản trở năng suất.

**TOSEM, "Is FL Effective on Industrial Software?"** [C7] — `76` lỗi thật, 3 project CAE. Kỹ thuật
chính xác nhất vẫn đòi xem TB **`467.18` statements**. So với ngưỡng Top-5 của [C2]: **lệch hai bậc
độ lớn**. *(Tác giả/năm chưa xác minh — ACM DL trả 403.)*

### Phía KHẲNG ĐỊNH — consumer là máy

**Liu et al., ICST 2019** [C8] — Defects4J `395` bug, tool kPAR:

| Cấu hình FL | Bug sửa đúng |
|---|---|
| Normal FL (Ochiai/GZoltar) | **18** |
| File Assumption | 22 |
| Method Assumption | 23 |
| **Line Assumption (perfect FL)** | **36** |

**Perfect FL nhân đôi số bug sửa đúng.** Thêm nữa: `132/395` bug **không localize được** với cấu
hình phổ biến nhất → trần trên của cả pipeline bị FL đặt ra trước khi patch generation bắt đầu.

**Liu et al., ICSE 2020** [C9] — `16` APR tool, cùng cấu hình FL. Khi cấp ground-truth fix location:
TBar `+30`, kPAR `+23`, FixMiner `+22`, AVATAR `+11`. Median NPC của SimFix từ `~200` xuống `~20`.
**Nhưng cùng paper có bằng chứng phản chiều**: ACS `−1`, Cardumen `−1`, jKali `−4`; và
*"the repair tool is rather misled, in the cases of specific bugs, when it is given the right bug
positions."* Hiệu ứng tập trung ở **template-based** repair (bottleneck = duyệt search space); tool
constraint/semantics-based không hưởng lợi vì bottleneck nằm ở năng lực sinh patch.

**Lou et al., ISSTA 2020** [C10] — **chiều nhân quả ĐẢO, và là insight quan trọng nhất cho SCM.**
ProFL dùng **kết quả thực thi patch** làm feedback cho FL: `161/395` Top-1 so với **`≤117`** của
SBFL/MBFL tốt nhất (`+37.6%` tương đối). Tức bằng chứng mạnh nhất không phải *"FL tốt → repair tốt"*
mà là ***"thử can thiệp → biết chỗ lỗi"***. Counterfactual intervention thắng coverage correlation.

**Eladawy, Le Goues, Brun, ICSE 2024** [C12] — human study tốt nhất trong danh sách: `40` developer
(median 6 năm), `9` defect thật, `160` session.
- Suggestion **đúng**: odds thành công **`+14.000%`**.
- Suggestion **deceptive** (pass test nhưng sai spec): odds **`−65%`**.
- **Không** khác biệt significant giữa novice và expert — ngược với [C1].
- *Lưu ý*: đây là về **patch suggestion**, không phải FL ranking thuần. Nhưng nó là bằng chứng tốt
  nhất rằng chẩn đoán **sai thì phản tác dụng**, không trung tính.

**Agentless, FSE 2025** [C11] — SWE-bench Lite. *"the percentage of patches with correct locations
correlates heavily with the solve rate."* Nhưng **counterexample ngay trong cùng bảng**: OpenCSG
StarShip đạt `88.3%` file-level localization — cao nhất — mà solve rate chỉ `23.67%`, thua Agentless
(`32.00%`). Localization đúng là **điều kiện cần, còn xa mới đủ**.

**Monperrus, ACM CSUR 2018** — một finding tự nó: trong survey chuẩn mực của APR, cụm "fault
localization" **chỉ xuất hiện 3 lần**, không có mục riêng. Lĩnh vực APR **coi FL là input cho sẵn,
không phải biến cần nghiên cứu** cho tới [C8], [C9].

---

## Threat cho thiết kế SCM hiện tại

**T1 — "fix location ≠ fault location" đâm thẳng vào lõi mediation.** Trong DIN-SQL, chỗ lỗi *biểu
hiện* thường là `sql_raw`; chỗ *gây* lỗi thường là `schema_links_raw`; chỗ *tốt nhất để can thiệp*
có thể là chỗ thứ ba. [C4] chứng minh nhầm ba thứ này thổi phồng hiệu quả AFL tới `38%`. Với khung
mediation, **mediator vs cause là toàn bộ nội dung của khung** — nếu lấy "stage mà can thiệp vào thì
sửa được" làm ground truth, đó là fix location và mang đúng bias đó.

**T2 — ngưỡng, không phải gradient.** [C2]: `>80%` yêu cầu Top-5. Trong pipeline 4 stage, "Top-5
trong 4 stage" là vô nghĩa — attribution ở granularity stage đã nằm sẵn trong ngưỡng, nên **cải
thiện attribution accuracy mức stage có thể không mang thêm giá trị nào**. Ở granularity hữu ích
thật (cột nào trong `schema_links_raw`, mệnh đề nào trong `sql_raw`) thì search space lớn và ngưỡng
lại khắc nghiệt. Phải chọn granularity và biện minh.

**T3 — metric trên lỗi cấy không transfer sang lỗi tự nhiên.** [C3]: `10/10` claim sụp khi chuyển từ
lỗi nhân tạo sang lỗi thật. Bốn phương pháp trong `tests/test_failure_attribution.py`
(`all_at_once`, `step_by_step`, `binary_search`, `hybrid`) chịu đúng threat này nếu đánh giá bằng
lỗi inject.

**T4 — bão hoà.** [C11]: attribution có thể gần hoàn hảo mà EX không nhúc nhích, vì bottleneck nằm ở
năng lực sinh SQL. **Cần ceiling test trước khi làm gì khác** — và arm `11` trong thiết kế hiện tại
đã chính là nó.

**T5 — attribution sai gây hại chủ động.** [C12]: `−65%` odds. Mọi claim dạng "attribution accuracy
X%" mà không kèm phân tích chi phí của `(100−X)%` là báo cáo một nửa. Claim matrix cuối phải có ô
"hiệu ứng của attribution SAI lên downstream".

**T6 — cảnh báo framing related work.** Không viết "FL đã được chứng minh là quan trọng cho repair".
Điều đó chỉ được chứng minh **từ 2019**, **chỉ cho template-based APR**, **chỉ trên Defects4J**.

## Điểm thuận lợi lớn nhất

[C10] ProFL: chiều nhân quả literature ủng hộ mạnh nhất là **"thử can thiệp → biết chỗ lỗi"**, chính
xác là oracle intervention của SCM. Hướng này không phụ thuộc giả định về consumer là người, và nó
khớp thẳng với khung mediation trong `paper/`.

---

## Hệ quả cho contribution

- *"Chưa ai làm"* — **chết hai lần**. Bảy công trình MAS đã đóng vòng; bốn công trình Text-to-SQL
  peer-reviewed đã làm chuỗi chẩn đoán → sửa → đo EX.
- *"Cải thiện độ chính xác"* — **chưa chứng minh được bằng thiết kế hiện tại**, vì mục thiết kế dừng
  ở arm oracle, không có bước fix triển khai được (oracle dùng gold, không có ở inference time).
- Thứ còn đứng vững: chẩn đoán aggregate thủ công **đã sai năm lần độc lập** trong chính Text-to-SQL;
  và trong bảy công trình MAS đóng vòng thì **chỉ một** có control tách "attribution đúng chỗ" khỏi
  "thử lại thì kiểu gì cũng khá hơn".
- **Competitor gần nhất là Ma et al.** [7], không phải EDGE hay CausalFlow như note chính đang giả
  định. Họ đã dùng causal inference + control cho đúng bài toán này.

---

## Chưa xác minh được

- [C5] Xie et al. ICSE 2016: `207` participants / `17` tasks từ nguồn thứ cấp. Tác giả/năm/venue/DOI đã khớp.
- [C7] TOSEM: **tác giả và năm** chưa xác minh (ACM DL 403). Tiêu đề/DOI/`76` bugs/`467.18` khớp hai nguồn.
- Gazzola et al. TSE 2019: bib đã xác minh, **không trích được nội dung** về vai trò FL (paywall).
- Hossain et al. FSE 2024 (Toggle): venue xác minh, **con số ablation token vs line chưa lấy được**.
- MAGIC [B5], MapleRepair [B3] bảng repair/mis-repair, TA-SQL Spider `74.0→85.0`: **một lần trích,
  chưa đối chiếu** — không dùng trong manuscript trước khi đọc lại PDF.
- Đối chiếu hai lần, tin được: DIN-SQL Table 5; TA-SQL `46.35 → 56.19`.

## Nguồn

**Nhánh A**
[1] Who&When, ICML 2025 — proceedings.mlr.press/v267/zhang25cq.html ·
[2] MAST, NeurIPS 2025 D&B — arxiv.org/abs/2503.13657 ·
[3] TraceElephant, ACL 2026 — DOI 10.18653/v1/2026.acl-long.912 ·
[4] EDGE, EMNLP 2026 — arxiv.org/abs/2609.01360 ·
[5] AgentLocate, COLM 2026 — arxiv.org/abs/2607.07989 ·
[6] AgentDebug — arxiv.org/abs/2509.25370 (ICLR 2026 withdrawn) ·
[7] Ma et al. causal — arxiv.org/abs/2509.08682 ·
[8] DoVer — arxiv.org/abs/2512.06749 ·
[9] AgentDebugX — arxiv.org/abs/2607.18754 ·
[10] TrajDebug — arxiv.org/abs/2608.06346 ·
[11] CausalFlow — arxiv.org/abs/2605.25338 ·
[12] Agents that Matter — arxiv.org/abs/2605.27621 ·
[14] AIG — arxiv.org/abs/2608.24361 ·
[15] MASPrism — arxiv.org/html/2605.07509 ·
[17] Survey — arxiv.org/abs/2605.14892

**Nhánh B**
[B1] DIN-SQL, NeurIPS 2023 — arxiv.org/abs/2304.11015 ·
[B2] TA-SQL, Findings ACL 2024 — DOI 10.18653/v1/2024.findings-acl.324 ·
[B3] MapleRepair, FSE 2026 — arxiv.org/abs/2501.09310 ·
[B4] Death of Schema Linking, NeurIPS 2024 TRL Workshop — arxiv.org/abs/2408.07702 ·
[B5] MAGIC, AAAI-25 — ojs.aaai.org/index.php/AAAI/article/view/34511 ·
[B6] Rethinking Schema Linking, Findings EACL 2026 — aclanthology.org/2026.findings-eacl.236

**Nhánh C**
[C1] Parnin & Orso, ISSTA 2011 — DOI 10.1145/2001420.2001445 ·
[C2] Kochhar et al., ISSTA 2016 — DOI 10.1145/2931037.2931051 ·
[C3] Pearson et al., ICSE 2017 ·
[C4] Soremekun et al., ICSE 2023, pp. 159–171 ·
[C5] Xie et al., ICSE 2016 — DOI 10.1145/2884781.2884834 ·
[C7] TOSEM — DOI 10.1145/3731448 ·
[C8] Liu et al., ICST 2019 — arxiv.org/abs/1812.07283 ·
[C9] Liu et al., ICSE 2020 — DOI 10.1145/3377811.3380338 ·
[C10] Lou et al., ISSTA 2020 — DOI 10.1145/3395363.3397351 ·
[C11] Xia et al., FSE 2025 (Agentless) ·
[C12] Eladawy, Le Goues, Brun, ICSE 2024 — DOI 10.1145/3597503.3639095
