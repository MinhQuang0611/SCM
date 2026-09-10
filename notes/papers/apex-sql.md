## APEX-SQL
(KDD '26, DOI 10.1145/3770855.3818075; arXiv 2602.16720v2. Code: github.com/Tencent/APEX-SQL-Project.
Đọc trực tiếp từ `paper/text2sql/2602.16720.pdf` bằng `pdftotext -layout`, 2026-09-07)

# Ý tưởng
- Chuyển từ *passive perception* (nhét schema tĩnh vào prompt, hoặc data profile tiền xử lý) sang **agentic exploration**: agent tự chạy SQL thăm dò lên DB thật để kiểm giả thuyết
- Vòng lặp Hypothesis–Verification, đặt ở CẢ HAI stage: schema linking và SQL generation
- Lý do: DB doanh nghiệp có tên cột mờ nghĩa, ngữ nghĩa nằm trong data chứ không nằm trong metadata -> model "mù dữ liệu" thì sinh SQL đúng cú pháp mà sai ngữ nghĩa

# Pipeline — Schema linking
- Logical Planning : sinh plan schema-agnostic (chưa dính tên bảng/cột) để tách reasoning khỏi nhiễu tên. Sample n=2 path ở T=0.8 rồi gộp thành master plan ở T=0.2
- Dual-Pathway Pruning : chạy song song một pass XOÁ (loại nhiễu) và một pass GIỮ (chọn liên quan), rồi hợp nhất — cột chỉ bị bỏ khi vừa bị từ chối chắc chắn vừa không được chọn. Batch theo bảng, 8–12k token/batch
- Semantic Linking : giả thuyết vai trò từng bảng/cột (vd cột này là primary filter)
- Parallel Data Profiling : mỗi bảng một agent, tự sinh query thăm dò để kiểm vai trò đó trên data thật
- Global Synthesis : gộp lại, đảm bảo subgraph liên thông, phục hồi dependency thiếu

# Pipeline — SQL generation
- Deterministic Guidance Retrieval : từ logical plan suy ra "SQL realization path", rule engine trích keyword rồi match với thư viện best-practice cố định -> ra directive ( vd thấy `RANK` thì bật directive kiểm NULL của cột đó ). Dùng keyword matching chứ không dense retrieval, recall >95% trên pilot BIRD-train
- Action space : Exploration -> Consolidation -> SQL Synthesis -> Confirmation, agent tự chọn
  - Profiling nén kết quả >30 dòng thành top-10 + thống kê (row count, cardinality, type, NULL ratio)
  - Consolidation nén history định kỳ, chỉ giữ query thăm dò + kết quả + plan mới nhất
  - Confirmation: kiểm SQL có khớp yêu cầu + observation đã thu thập, chống logical drift
- Budget: tối đa 40 action / 56k token, ép sinh SQL ở mốc 38 action hoặc 52k token
- Inference: sample 8 candidate. BIRD chọn bằng reward model; Spider 2.0 majority voting theo kết quả

# Metric schema linking ( phần đáng giá nhất cho đề tài )
- **Strict Recall Rate (SRR)** : % câu mà schema lấy về PHỦ HẾT ground truth. Tác giả coi đây là metric quan trọng nhất — thiếu một cột là downstream không thể đúng
- Kèm NSR / NSP / NSF (recall, precision, F1 không strict)
- Ground truth cột : trích từ gold SQL bằng GPT-4.1 + DeepSeek-V3.2 rồi **verify tay** -> mediator có ground truth rẻ, đúng loại đang cần cho mediation decomposition

# Kết quả
- Schema linking SRR : BIRD subset (n=147, DeepSeek-V3.2) **97.28** / BIRD full (n=1534, Qwen3-32B) **87.68** / Spider 2.0-Snow (n=120, GPT-4.1) **88.33** — cao nhất cả 3 setting. ReFoRCE chỉ 35.00 SRR trên Spider 2.0
- NSP của APEX THẤP hơn baseline, tác giả nhận và biện minh: enterprise query có nhiều path hợp lệ, thà giữ thừa còn hơn prune nhầm không cứu được
- BIRD-Dev EX (n=1534, GPT-4o) : Simple 75.9 / Mod 64.4 / Chall 57.2 / **Total 70.7** — trên RSL-SQL 67.2, DSR-SQL 68.3, OpenSearch-SQL 69.3
- Spider 2.0-Snow (n=547, DeepSeek-R1) : **EX 53.03**, Pass@8 68.44. Chú ý: script eval Spider 2.0 đã đổi, DSR-SQL báo 35.28 (bản cũ) vs 52.83 (bản mới) — **không so số giữa hai bản script**

# Ablation schema linking ( Spider 2.0-Snow n=120, SRR )
| | SRR | số cột giữ lại |
|---|---:|---:|
| sau Planning+Pruning, chưa verify | 97.5 | 383 ( từ 3430 ) |
| — w/o Planning | 97.2 (-0.3) | 375 |
| — chỉ Deletion | 80.8 **(-16.7)** | 217 |
| — chỉ Selection | 93.3 (-4.2) | 305 |
| sau cả Verification | 77.5 | 57 |
| — w/o Planning | 72.5 (-5.0) | 33 |
| — w/o Semantic Linking | 63.3 **(-14.2)** | 30 |
| — w/o Data Profiling | 68.3 (-9.2) | 25 |
| — w/o Global Synthesis | 73.3 (-4.2) | 45 |
| — w/o All ( bỏ hẳn verification ) | 55.8 **(-21.7)** | 12 |

- Logical Planning gần như vô hại ở stage pruning (-0.3) nhưng mất 5.0 ở stage verification -> giá trị của nó là **cung cấp ngữ cảnh cho stage sau**, không phải cải thiện stage của chính nó. Đúng dạng hiệu ứng gián tiếp qua mediator
- Đây là ablation phân tầng theo stage ( đo cả intermediate lẫn final ), khác hẳn LOO một tầng của GBV-SQL — mẫu trình bày tốt cho đề tài

# Ablation SQL generation ( EX@8, Spider 2.0-Snow n=120 )
- Có guidance tốt hơn không guidance ở mọi model ( GPT-4o +3.75 EX@8 )
- Số vòng thăm dò R̄ GIẢM khi có guidance, nhưng số query Q̄ giữ nguyên hoặc tăng -> mỗi vòng thăm dò nhiều hơn, ít vòng hơn

# Effect of Exploration ( oracle schema, n=120 )
- Exploration là **performance multiplier**, và mức lợi tỉ lệ với năng lực model ( "rich get richer" ): GPT-4o +5.00 EX, DeepSeek-V3.2 +18.33 EX ( 39.17 -> 57.50 )
- Oracle Exploration ( mớm chi tiết implementation trích từ gold SQL ) giúp model yếu ở mọi metric, nhưng với model mạnh thì tăng EX mà **giảm Pass@8** ( DeepSeek-V3.2 -8.34 ) — thu hẹp search space làm mất độ phủ
- **Selection gap** : DeepSeek-V3.2 Pass@8 79.17 nhưng voting chỉ chốt được 57.50. EX@k phẳng trong khi Pass@k tăng -> sinh đủ tốt rồi, nghẽn ở khâu CHỌN. Trùng đúng kết luận oracle của [reforce](reforce.md) ( Pass@8 +7 mà EX +0.37 )

# Ghi chú cho đề tài
- **SRR là mediator có ground truth rẻ** ( parse gold SQL ra tập cột ), cùng loại với syntax-keyword của [cogsql](cogsql.md). Đã ghi ở [failure-attribution.md](failure-attribution.md)
- Setting **oracle schema** của họ chính là một can thiệp kiểu mediation: khoá stage schema linking để cô lập lỗi của stage generation. Paper này làm sẵn ở mức aggregate, đề tài cần làm ở **mức case**
- Có code Apache/Tencent public -> ứng viên baseline dựng lại được, khác CogSQL và GBV-SQL
- Artifact quan sát được : logical plan, tập cột sau pruning (383) và sau verification (57), observation từng bảng, guidance directive, từng query thăm dò + kết quả, consolidated state, SQL candidate, phán quyết confirmation

# Chưa xác minh
- SRR của APEX trên Spider 2.0-Snow ở Table 1 là **88.33** nhưng dòng "sau Verification" của Table 5 ghi **77.5**, cùng n=120. Caption Table 5 không nêu backbone. Chưa rõ khác nhau ở setting nào — đừng trích lẫn hai con số
- Table 1 ghi "all baseline results locally reproduced", Table 2/3 thì lấy từ literature — trộn hai nguồn, cần tách khi đối chiếu
- Chưa đọc Appendix A/B ( prompt template + thư viện best practice M ) và Appendix C ( case study )
- Chưa kiểm repo Tencent có release đủ để chạy lại không
