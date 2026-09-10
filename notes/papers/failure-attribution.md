# Failure attribution — nhóm paper ngoài Text-to-SQL

> **Cập nhật 2026-09-06.** Rà lại toàn bộ mảng này qua WebSearch/WebFetch (không phải chỉ đọc
> lại 5 công trình cũ). Tìm thêm được **6 công trình mới** chưa từng ghi trong repo: MAST,
> CausalFlow, Adaptive Influence Graphs, EDGE, AgentLocate, Implicit Execution Tracing —
> cộng một bài survey dễ hiểu nhầm (Causal MAS). Kết luận không đổi so với 2026-08-22:
> **không công trình nào phủ Text-to-SQL, không công trình nào dùng causal mediation dạng
> Baron–Kenny/VanderWeele (phân rã direct/indirect effect) cho attribution.** Nhưng landscape
> đông hơn nhiều so với bản cũ tưởng — bảng dưới đây là bản đủ, không phải bản trích mẫu.

Dựng lại 2026-08-24. Đây là phần novelty check: có ai làm rồi chưa.

## Bảng nhanh — bản đầy đủ 2026-09-06

| Công trình | Venue | Nội dung | Text-to-SQL? | Causal mediation? |
|---|---|---|---|---|
| Who&When (Zhang et al.) [1] | **ICML 2025 Spotlight** (PMLR v267) | định nghĩa bài toán; 3 phương pháp All-at-Once/Step-by-Step/Binary-Search; agent 53.5% / step 14.2% | Không | Không |
| MAST (Cemri et al.) [2] | **NeurIPS 2025** (Datasets & Benchmarks) | taxonomy mô tả 14 failure mode / 3 nhóm; κ=0.88; **không có phương pháp attribution tự động** | Không | Không |
| TraceElephant [3] | **ACL 2026 Long** | benchmark 220 trace fail; agent 65.9% / step 30.3%; full-trace hơn output-only 76.5% tương đối | Không | Không |
| EDGE (Hou et al.) [4] | **EMNLP 2026** | error dependency graph + counterfactual rollout, nhắm **multi-error / lỗi dây chuyền** | Không | Gần — counterfactual, không phải mediation formula |
| AgentLocate (Xia et al.) [5] | **to appear COLM 2026** | multi-perspective LLM-judge + confidence-aware aggregation, quy cả agent lẫn step | Không | Không |
| CausalFlow (Bonagiri et al.) [6] | preprint — **chưa xác nhận venue** | "Causal Responsibility Score" qua counterfactual intervention từng bước | Không (math/code/QA/y tế) | Gần — counterfactual đơn lẻ, không phân rã direct/indirect |
| Adaptive Influence Graphs (Bakish et al.) [7] | preprint — **chưa xác nhận venue** | dựng đồ thị ảnh hưởng từ trace rồi duyệt đồ thị; SOTA trên benchmark Who&When | Không | Không |
| Implicit Execution Tracing (Nian et al.) [8] | preprint — **chưa xác nhận venue** | bài toán khác hẳn: quy trách nhiệm **khi không có log** (nhúng provenance lúc sinh token) | Không | Không |
| StepFinder [9] | preprint 2606.03467 — **chưa xác nhận venue** | attribution theo ngữ nghĩa thời gian | Không | Không |
| AgentRx | preprint 2602.02475 — **chưa xác nhận venue** | chẩn đoán lỗi agent từ execution trajectory | Không | Không |
| Span-level localization | preprint 2606.02060 — **chưa xác nhận venue** | định vị lỗi mức span cho deep-research agent | Không | Không |
| Causal MAS survey (Bazgir et al.) [10] | preprint arXiv:2509.00987 — **chưa xác nhận venue** | **Không cùng nghĩa "causal"** — khảo sát agent LÀM causal discovery/effect estimation hộ người dùng, không phải phân tích causal LÊN chính hệ multi-agent. Trích cẩn thận, dễ hiểu nhầm | Không | Không (đề tài khác) |

**Không công trình nào phủ text-to-SQL.** Kiểm lại 2026-09-06, khoảng trống vẫn còn — và giờ đã
kiểm kỹ hơn nhiều so với lần trước (11 công trình thay vì 5).

## Ba phát hiện mới quan trọng nhất (2026-09-06)

### 1. MAST (NeurIPS 2025) là related work bắt buộc phải trích, và trước đó repo bỏ sót

Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" — taxonomy 14 failure mode, gom 3 nhóm:
system design issues, inter-agent misalignment, task verification. 1600+ trace, 7 framework MAS
phổ biến (GPT-4, Claude 3, Qwen2.5, CodeLlama — coding/math/general agent). Cohen's kappa 0.88,
đo trên 150 trace bởi annotator chuyên gia; sau đó scale bằng LLM-as-Judge.

Đây là taxonomy **mô tả**, không phải phương pháp attribution tự động — họ không thử định vị lỗi
theo case, chỉ phân loại lỗi thủ công/bán tự động rồi đếm tần suất. Đây là chỗ khác biệt quan
trọng với Who&When (Who&When mới là bài **giải bài toán attribution tự động**).

**Dùng để làm gì:** taxonomy 3 nhóm của MAST (system design / inter-agent misalignment / task
verification) là điểm neo tốt để map với 5-stage pipeline của đề tài — ví dụ "system design
issues" gần với lỗi schema linking/plan sai ngay từ đầu, "inter-agent misalignment" gần với lỗi
truyền artifact sai giữa các stage, "task verification" gần với lỗi ở stage verify/select. Có thể
trích MAST khi biện minh vì sao taxonomy 3 tầng của GBV-SQL (SQL-side/NLQ-side/Database) là hợp lý
— vì một taxonomy tổng quát khác (MAST) cũng hội tụ về cấu trúc 3 nhóm tương tự cho lỗi agent nói
chung.

### 2. CausalFlow và EDGE — "causal" nhưng không phải mediation, và đây là chỗ phải viết rõ trong manuscript

Cả hai đều tự nhận là "causal", nhưng cách làm là **counterfactual intervention từng bước** (chạy
lại với một bước bị đổi, xem kết quả đổi thế nào), không phải **phân rã direct/indirect effect**
kiểu Baron–Kenny/VanderWeele mà `.claude/CLAUDE.md` dự kiến làm khung phân tích chính.

Khác biệt kỹ thuật, cần giữ rõ khi viết related work:

- **Counterfactual intervention (CausalFlow, EDGE):** hỏi "nếu bước i khác đi thì kết quả cuối có
  đổi không" — trả lời câu hỏi **causation** ở một bước, từng bước một.
- **Mediation formula (Baron–Kenny/VanderWeele):** phân rã tổng effect thành **direct effect**
  (X → Y không qua M) và **indirect effect** (X → Y qua M), cho toàn chuỗi cùng lúc, và định lượng
  được bao nhiêu phần trăm effect đi qua từng mediator.

Không công trình nào tìm được áp dụng đúng phân rã direct/indirect kiểu mediation cho attribution
agent. Đây là khoảng trống thật, không phải khoảng trống do tìm thiếu — đã tìm cả bằng từ khóa
"direct effect indirect effect mediation multi-agent pipeline" lẫn "causal mediation agent" và chỉ
ra được tài liệu phương pháp thống kê tổng quát (Kenny, VanderWeele, Pearl), không ra được ai áp
dụng cho LLM agent pipeline.

### 3. AIG (Bakish et al.) và AgentLocate — cuộc đua đang nóng ở đúng bài toán Who&When, nhưng vẫn ở domain tổng quát

Adaptive Influence Graphs (25/08/2026, còn rất mới) đã đạt SOTA trên benchmark Who&When bằng cách
biểu diễn trace thành đồ thị rồi cho agent duyệt đồ thị thay vì đọc log tuần tự — không đổi domain,
chỉ đổi cách biểu diễn trace. AgentLocate (to appear COLM 2026) cải tiến bằng multi-perspective
LLM-judge + gộp theo độ tin cậy. Cả hai đều **không chạm Text-to-SQL**, tức là cuộc đua cải tiến độ
chính xác của phương pháp attribution đang diễn ra sôi nổi (ít nhất 5 công trình 2025–2026 cùng
nhắm benchmark Who&When), nhưng **không ai chuyển bài toán sang domain có schema + execution
semantics rõ ràng như Text-to-SQL.**

## Đối chiếu với package `failure_attribution` đã spec sẵn trong repo (chưa implement)

`tests/test_failure_attribution.py` đã spec 4 phương pháp: `all_at_once`, `step_by_step`,
`binary_search`, `hybrid` — **ba cái đầu chính là ba phương pháp của Who&When**, cái thứ tư là mở
rộng riêng của repo. Nghĩa là hướng kỹ thuật repo đã chọn từ trước (dù chưa implement) là đúng
hướng: port phương pháp attribution tự động của Who&When sang Text-to-SQL, có `gold_failure_agent`
/ `gold_failure_step` làm nhãn thật để so khớp — đúng mô hình đánh giá của Who&When/TraceElephant.

Nhưng nếu dừng ở đó (port 3+1 phương pháp LLM-judge sang domain mới) thì đóng góp chỉ là
**domain-transfer**, không phải phương pháp mới — và AIG vừa cho thấy chỉ đổi cách biểu diễn trace
(không đổi domain) đã đủ để đạt SOTA, nghĩa là "domain-transfer thuần" là đóng góp mỏng, dễ bị
review bắt bẻ "vậy khác AIG/AgentLocate chỗ nào". Chỗ để dày thêm: cộng thêm **lớp mediation
decomposition** dùng đúng các mediator có ground-truth rẻ đã tìm được từ 4 paper baseline
(syntax-keyword của CogSQL, Strict Recall Rate của APEX-SQL, schema-link correctness parse từ gold
SQL) — đó là phần không ai trong 11 công trình trên làm, kể cả AIG/AgentLocate/EDGE.

## Việc cần làm

1. Đọc kỹ TraceElephant để lấy annotation scheme và cách tính agreement làm mẫu, thay vì tự
   nghĩ định nghĩa nhãn. (giữ từ bản cũ — vẫn đúng)
2. Đọc thêm MAST §3–4 (taxonomy 14 mode) để map 3 nhóm của họ với 5-stage pipeline của đề tài,
   dùng làm cross-check cho taxonomy GBV-SQL đang định mượn.
3. Nếu implement `failure_attribution` package: giữ nguyên 3+1 phương pháp đã spec (port đúng
   Who&When), nhưng thiết kế `evaluate.py` sao cho xuất được cả bảng mediation decomposition
   (direct/indirect effect qua từng mediator rẻ), không chỉ accuracy của LLM-judge so với gold
   label — đó là phần khác biệt với AIG/EDGE/AgentLocate.
4. Trích Who&When bằng **PMLR proceedings** (proceedings.mlr.press/v267/zhang25cq.html), không
   trích arXiv — đã lên venue chính thức.

## Nguồn (bổ sung 2026-09-06, đánh số nối tiếp phần cũ)

[1] S. Zhang, M. Yin, J. Zhang, J. Liu, Z. Han, J. Zhang, F. Wan, A. Wang, Y. Ma, and Q. Wen,
"Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent
Systems," in *Proc. 42nd Int. Conf. Mach. Learn. (ICML)*, 2025, PMLR vol. 267. [Online]. Available:
https://proceedings.mlr.press/v267/zhang25cq.html

[2] M. Cemri, M. Z. Pan, S. Yang, L. A. Agrawal, B. Chopra, R. Tiwari, K. Keutzer, A. Parameswaran,
D. Klein, K. Ramchandran, M. Zaharia, J. E. Gonzalez, and I. Stoica, "Why Do Multi-Agent LLM
Systems Fail?," in *Proc. Neural Inf. Process. Syst. (NeurIPS), Datasets and Benchmarks Track*,
2025. arXiv:2503.13657.

[3] (tác giả TraceElephant), "Seeing the Whole Elephant: A Benchmark for Failure Attribution in
LLM-based Multi-Agent Systems," in *Proc. 64th Annu. Meeting Assoc. Comput. Linguistics (ACL)*,
2026, pp. (long paper). arXiv:2604.22708. [chưa lấy đủ tên tác giả — cần đối chiếu ACL Anthology
khi trích chính thức]

[4] J. Hou, P. Pitre, Y. Fang, and X. Wang, "EDGE: Error Dependency Graph-Guided Multi-Error
Attribution in Multi-Agent LLM Systems," in *Proc. Conf. Empirical Methods Nat. Lang. Process.
(EMNLP)*, 2026. arXiv:2609.01360.

[5] Y. Xia, A. Gao, Y. Quan, Z. Liu, and M. Fang, "Who Broke the System? Failure Localization in
LLM-Based Multi-Agent Systems," to appear in *Proc. Conf. Lang. Model. (COLM)*, 2026.
arXiv:2607.07989.

[6] A. Bonagiri, D. Borkar, G. J. Anderias, S. Rafatirad, and H. Homayoun, "CausalFlow: Causal
Attribution and Counterfactual Repair for LLM Agent Failures," arXiv:2605.25338, 2026. **Chưa xác
nhận venue.**

[7] Y. Bakish, A. Dudai, R. Ganz, O. Nuriel, E. Ben Avraham, M. Shpigel Nacson, and R. Litman,
"Adaptive Influence Graphs for Failure Attribution in Multi-Agent Systems," arXiv:2608.24361, 2026.
**Chưa xác nhận venue.**

[8] Y. Nian, H. Cao, S. Zhu, H. P. Zou, Q. Luan, Y. Zhang, and Y. Zhao, "When Only the Final Text
Survives: Implicit Execution Tracing for Multi-Agent Attribution," arXiv:2603.17445, 2026. **Chưa
xác nhận venue.**

[9] "StepFinder: A Temporal Semantic Framework for Failure Attribution in Multi-Agent Systems,"
arXiv:2606.03467, 2026. **Chưa xác nhận venue** — tên tác giả chưa trích đủ, cần đối chiếu khi
dùng chính thức.

[10] A. Bazgir, A. Habibdoust, Y. Zhang, and X. Song, "Causal MAS: A Survey of Large Language Model
Architectures for Discovery and Effect Estimation," arXiv:2509.00987, 2025. **Chưa xác nhận venue —
và lưu ý khác đề tài, xem mục "Ba phát hiện mới" ở trên.**

---

## Cap nhat 2026-09-10 — nhanh "dong vong" ma ban ra 2026-09-06 bo sot

Ra lai voi mot cau hoi khac: *khong phai "ai da lam attribution", ma "ai da chung minh
attribution dan toi cai thien accuracy DO DUOC"*. Ket qua doi cuc dien cua phan novelty.

### Phai tach hai muc dong vong

- **Muc case** — sua/chay lai chinh case da fail (re-rollout, inject feedback). He khong doi.
- **Muc he** — sua chinh he (prompt, module, topology), chay lai toan benchmark.

### Bay cong trinh DA dong vong — tat ca deu arXiv-only

| Cong trinh | Muc | Con so |
|---|---|---|
| **Ma et al. causal** (arxiv 2509.08682) | case | Who&When, 50 trajectory fail: `15.4% -> 37.8%`, **control ngau nhien `18.3%`** |
| AgentDebugX (2607.18754) | case | attribution `28.8%` vs `21.7%`; GAIA `55.8% -> 63.6%` |
| AgentDebug (2509.25370) | case | ALFWorld `21->55`, `48->74`, `60->84`. **ICLR 2026 withdrawn** |
| CausalFlow (2605.25338) | case | repair rate TB `42.7%`; accuracy `+13.1` den `+30.8` pp |
| TrajDebug (2608.06346) | case + transfer | memory transfer: `+4.5` den `+6.6` pp |
| DoVer (2512.06749) | case | recover `18-28%` trial fail (GAIA), `49%` (GSMPlus) |
| Agents that Matter (2605.27621) | **he** | `+17%` performance, `-35%` cost — nhung la *contribution* attribution |

### Ba dinh chinh cho phan cu cua note nay

1. **Muc 2 cua note nay mo ta CausalFlow chua du.** Note viet CausalFlow/EDGE "dung counterfactual
   don le, khong phan ra". Dung ve EDGE. **Sai ve CausalFlow** — no co dong vong va bao accuracy
   tang `+13.1` den `+30.8` pp. Phat bieu khac biet phai chinh lai.
2. **Competitor gan nhat KHONG phai EDGE hay CausalFlow — ma la Ma et al.** Ho dung causal
   inference cho dung bai toan nay, tren dung benchmark Who&When, va **co control ngau nhien**.
   Day la cong trinh phai doc ky nhat.
3. **Claim "chua ai lam" khong con dung duoc.** Bay cong trinh tren se pha claim do ngay o vong
   review.

### Phat bieu con dung vung

> Failure attribution o venue peer-reviewed van duoc danh gia thuan bang **attribution accuracy**
> (Who&When ICML 2025, TraceElephant ACL 2026, EDGE EMNLP 2026, AgentLocate COLM 2026 — ca bon
> khong chay lai he). Cac cong trinh dong vong **deu la preprint**, **deu repair muc case**, va
> **tru mot cong trinh, deu khong co control** de chung minh gain den tu do chinh xac cua
> attribution chu khong tu viec cu thu lai.

Survey (arxiv 2605.14892) muc 4.5.1 xac nhan, tieu de nguyen van
**"The Evaluation-Repair Loop Remains Incomplete"**.

### Cong trinh can bo sung vao bang nhanh

Chua co trong bang o dau note: AgentDebug, Ma et al. causal, DoVer, AgentDebugX, TrajDebug,
Agents that Matter, SAGE (2606.31478), MASPrism (2605.07509), GEPA (ICLR 2026 Oral), survey
(2605.14892). TraceElephant nay da co du tac gia: Chen, Wang, Mu, Wang, Liu, Feng, Wang;
ACL Anthology 2026.acl-long.912, pp. 19888-19905.

Chi tiet day du + nhanh Text-to-SQL + nhanh software engineering:
`notes/_search/attribution-to-improvement-evidence-2026-09-10.md`
