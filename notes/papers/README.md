# Note chi tiết từng paper

Đọc [../tong_quan_literature.md](../tong_quan_literature.md) trước — đó là bản tổng hợp.
Thư mục này là chi tiết từng bài.

Toàn bộ file ở đây viết lại ngày 2026-08-24, sau khi thư mục baselines/ và benchmarks/
bị xóa. Xem cột "Độ tin" để biết cái nào đọc lại từ paper, cái nào dựng từ tóm tắt.

## Baseline

| Note | Venue | Code | Độ tin |
|---|---|---|---|
| [deepeye-sql](deepeye-sql.md) | SIGMOD 2026 | CÓ | đọc lại từ paper 2026-08-24 |
| [alpha-sql](alpha-sql.md) | ICML 2025 | CÓ | đọc lại từ paper 2026-08-24 |
| [vet](vet.md) | Findings ACL 2026 | không thấy | đọc lại từ paper 2026-08-24 |
| [cogsql](cogsql.md) | AAAI-25 | không | đối chiếu từ PDF `paper/08630-YuanH.pdf` 2026-09-06 |
| [gbv-sql](gbv-sql.md) | ACL 2026 Main | không | đọc lại từ PDF 2026-08-24 (đợt 2) |
| [prospy](prospy.md) | preprint | không | đầy đủ |
| [agentsm](agentsm.md) | preprint | chưa rõ | đầy đủ |
| [dsr-sql](dsr-sql.md) | preprint | repo 404 | đầy đủ |
| [reforce](reforce.md) | workshop | CÓ, Apache-2.0 | đọc lại từ PDF 2026-08-24 (đợt 2) |
| [apex-sql](apex-sql.md) | KDD 2026 | CÓ (Tencent) | đọc từ PDF 2026-09-07 |
| [dail-sql](dail-sql.md) | PVLDB 2024 | CÓ | **mỏng**, nhưng đã chạy trong repo |

## Benchmark

| Note | Nội dung | Độ tin |
|---|---|---|
| [spider-2](spider-2.md) | Spider 2.0 + trạng thái 2026 + AIFunc | đầy đủ |
| [bird-sparc-drspider](bird-sparc-drspider.md) | ba benchmark đang dùng + BIRD-CRITIC/INTERACT | **mỏng**, gộp từ bảng so sánh |
| [annotation-errors](annotation-errors.md) | Jin et al., chất lượng nhãn | đầy đủ, trích trực tiếp từ PDF |

## Novelty check

| Note | Nội dung |
|---|---|
| [failure-attribution](failure-attribution.md) | **Cập nhật 2026-09-06**, 11 công trình: Who&When (ICML 2025), MAST (NeurIPS 2025), TraceElephant (ACL 2026), EDGE (EMNLP 2026), AgentLocate (COLM 2026), CausalFlow, Adaptive Influence Graphs, Implicit Execution Tracing, StepFinder, AgentRx, Causal MAS survey |
| [../review_2026-09-06_failure_attribution_landscape_and_rq.md](../review_2026-09-06_failure_attribution_landscape_and_rq.md) | Annotated bibliography + đề xuất research question, dựng từ bản cập nhật trên |

## Cái nào cần đọc lại

1. ~~cogsql.md — cần mở PDF AAAI~~ **ĐÃ ĐÓNG 2026-09-06.** PDF chính thức AAAI-25 hoá ra vẫn nằm
   sẵn trong repo (`paper/08630-YuanH.pdf`), chỉ là chưa ai thử đường đó trước. Đối chiếu xong:
   Table 2 và Table 5 khớp 100%, và tác giả CÓ tự phát biểu cả hai vế (mục Module Design, tr.7) —
   nhưng không tự rút ra kết luận về tính chuyển được giữa cấu hình (ghi trong cogsql.md, mục Ablation).
2. bird-sparc-drspider.md — ba benchmark này từng có note riêng, giờ chỉ còn mức bảng
3. deepeye-sql.md — chưa trích được bảng ablation
4. reforce.md — ablation / defer / chi phí ĐÃ ĐÓNG 2026-08-24. Còn lại: format log thật
   mà repo Snowflake-Labs xuất ra (phải clone mới biết)

## Bốn note theo kiểu gọn (reforce, gbv-sql, cogsql, apex-sql)

reforce.md, gbv-sql.md, cogsql.md, apex-sql.md dùng chung một dạng: `## <Tên>` + các section `#` bullet ngắn,
chỉ giữ pipeline, số liệu chính, thí nghiệm đáng chú ý và ghi chú cho đề tài.

Bản dài trước đó (sơ đồ luồng ASCII, ví dụ SQL cụ thể, giải thích từng module) của gbv-sql và cogsql
giữ ở [archive/](archive/) — không xoá, dùng khi cần trích chi tiết.
