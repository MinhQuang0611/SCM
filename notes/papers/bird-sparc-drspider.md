# BIRD, SParC, Dr.Spider — ba benchmark đang dùng

Dựng lại 2026-08-24. **Mỏng hơn ba note gốc đã xóa** — chỉ còn phần đã đưa vào bảng so sánh.
Muốn chi tiết từng paper thì phải đọc lại.

Số "đã kiểm" = đếm trực tiếp trên file trong datasets/text2sql/.
Số "paper" = do paper report, chưa chạy lại.

## BIRD

- Venue: NeurIPS 2023 Datasets & Benchmarks
- Task: sinh SQL, một query, single-turn
- Quy mô (paper): 12,751 cặp / 95 DB. Dev (đã kiểm): 1,534 câu / 11 DB
- DB: SQLite. Metric: EX, VES
- Headroom (paper): GPT-4 54.89%, người 92.96%
- Đã chạy trong repo: DIN-SQL, MAC-SQL trên dev
- Vai trò: **mặt bằng chính**. Là benchmark duy nhất cả ba baseline core đều dùng.
- Lưu ý: Mini-Dev (498 bài) có 52.8% lỗi annotation — xem annotation-errors.md

## SParC

- Venue: ACL 2019
- Task: sinh SQL multi-turn, có sẵn history hội thoại
- Quy mô (paper): 4,298 sequence / hơn 12k câu hỏi / 200 DB
- Dev (đã kiểm): 1,203 turn / 422 interaction
- DB: SQLite. Metric gốc: EM (theo question và theo interaction)
- Headroom (paper): tốt nhất EM 20.2% (số năm 2019, đã cũ)
- Đã chạy trong repo: **4 framework, đầy đủ**, có stage_logs đủ bốn stage.
  Run DIN-SQL có 515 case sai (đã kiểm).
- Vai trò: **nguồn dữ liệu attribution sẵn nhất**. Thêm được chiều "lỗi ở turn nào".
- Lưu ý: repo đang chấm bằng EX theo result_hash, không phải EM. Không đặt cạnh số EM gốc.
- Chưa audit chất lượng nhãn.

## Dr.Spider

- Venue: ICLR 2023, top 5%
- Task: chẩn đoán robustness — cùng bài toán, can thiệp có kiểm soát
- Quy mô (paper): 15K perturbed / 17 test set. Đã kiểm: 15,269 / 17 set
- DB: SQLite. Metric: mức sụt giảm trước/sau can thiệp, không phải giá trị tuyệt đối
- Headroom (paper): sụt trung bình 14.0%, set khó nhất sụt 50.7%
- Chưa chạy trong repo
- Vai trò: **nơi kiểm chứng phương pháp attribution mà KHÔNG cần annotate tay.**

Vì sao Dr.Spider quan trọng: mỗi case có cặp trước/sau khớp nhau, chỉ khác đúng một yếu tố
đã biết. Nếu can thiệp vào schema mà phương pháp quy lỗi cho generation thì đó là bằng chứng
phương pháp sai. Hiện chưa có case nào trong repo mang nhãn gold_failure_agent, nên đây là
con đường rẻ nhất để có tín hiệu kiểm chứng.

Giới hạn: can thiệp mang tính nhân tạo. Điều kiện cần, không phải điều kiện đủ.

## Cảnh báo dùng chung

- **Spider family.** SParC và Dr.Spider đều dẫn xuất từ Spider. Kết quả tốt trên cả hai
  KHÔNG chứng minh khái quát ra ngoài Spider family. BIRD và Spider 2.0 mới cho tín hiệu đó.
- **Metric không so chéo được.** SParC gốc dùng EM, repo dùng EX. Dr.Spider quan tâm mức sụt.
  Không đặt các số này cạnh nhau trong một bảng.
- **Split và setting.** So sánh baseline chỉ có nghĩa khi cùng split, cùng metric
  implementation, cùng external-knowledge setting. BIRD test và SParC test đều hidden
  evaluation nên dev là điểm bắt đầu thực tế.
- **Adapted run khác reproduction.** Toàn bộ kết quả hiện có trong repo là adapted local run.
  Không so trực tiếp với leaderboard.

## Ngoài scope hiện tại

- **BIRD-CRITIC / SWE-SQL** — NeurIPS 2025 Main. Task là SỬA SQL: input đã là SQL lỗi.
  Không áp dụng attribution được vì lỗi là input chứ không phải thứ sinh ra.
  PG 530 bài, Multi 570 bài. PostgreSQL/MySQL/SQL Server/Oracle. O3-Mini 38.87% SR.
  Đọc phần taxonomy lỗi thôi, không chạy.
- **BIRD-INTERACT** — ICLR 2026 Oral. Agent chủ động hỏi lại user. Full 600 / Lite 300.
  GPT-5 chỉ 8.67% / 17.00%. Khả năng định vị lỗi thấp nhất vì thêm cả lỗi interaction policy.
  Ngoài scope.

## Kết luận chọn benchmark

- BIRD-dev — mặt bằng chính
- SParC dev — nguồn dữ liệu attribution
- Dr.Spider — kiểm chứng phương pháp
- Spider2-Lite — kiểm tra tính chuyển được, subset local* nhỏ. Snow không phải dataset thứ hai.

Ba cái đầu bổ sung nhau theo ba vai trò khác nhau, không thay thế nhau.
