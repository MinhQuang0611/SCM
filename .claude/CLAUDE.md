# SCM — Failure Attribution for Text-to-SQL Multi-Agent Systems

## Bối cảnh dự án

Workspace nghiên cứu, không phải ứng dụng. Mục tiêu: **failure attribution** trên các hệ Text-to-SQL
multi-agent — xác định agent/stage nào gây lỗi, chứ không chỉ đo đúng/sai cuối cùng.
Khung phân tích dự kiến là causal mediation (xem `paper/`: Baron–Kenny, VanderWeele, Albert et al.).

Scope literature hiện tại và tiêu chí chọn baseline/dataset: `notes/README.md`. Đọc file đó trước
khi đề xuất thêm paper hoặc baseline.

## Ngôn ngữ

- Trả lời và viết note bằng **tiếng Việt**, trừ khi được yêu cầu khác.
- Thuật ngữ kỹ thuật (execution accuracy, schema linking, failure attribution…) giữ nguyên tiếng Anh.
- Manuscript và nội dung nộp hội nghị viết bằng **tiếng Anh**.

## ARS standing preferences

Áp dụng cho các skill `deep-research`, `academic-paper`, `academic-paper-reviewer`, `academic-pipeline`.

- Citation style: **IEEE** (numbered) — khớp quy ước sẵn có trong `baselines/text2sql/*/README.md`.
- Literature search: loại preprint trừ khi được yêu cầu rõ; ưu tiên venue peer-reviewed.
- Với paper chỉ có trên arXiv, phải ghi rõ "chưa xác nhận venue" như `analysis/text2sql_public_frameworks_report.md` đang làm.
- Ưu tiên bản open access khi có.
- Ưu tiên venue tier cao (SIGMOD/VLDB/ICML/ACL/EMNLP) cho phần related work.

## Quy tắc liêm chính nghiên cứu

Bắt buộc, không có ngoại lệ:

- **Không bịa** citation, số liệu, run, metric, hay việc thực thi thành công. Không có kết quả thì nói là chưa có.
- **Raw data và raw run output là immutable.** Không sửa, không ghi đè `predictions.jsonl`, `logs.jsonl`,
  `run_manifest.json` của run đã hoàn tất. Cần sửa thì tạo run id mới.
- Không để bước implementation âm thầm thay đổi quyết định thiết kế khoa học — nếu buộc phải lệch khỏi
  protocol, nêu rõ và hỏi.
- Phân biệt rạch ròi **adapted local run** với **official paper reproduction**. Toàn bộ kết quả hiện có
  trong repo là adapted run, không phải reproduction — mọi report phải giữ nguyên phân biệt này.

### Gate thực nghiệm

- Không chạy full run trước khi smoke/pilot pass.
- Không phân tích kết quả trước khi audit đạt PASS hoặc PASS_WITH_WARNINGS.
- Không chốt claim trong manuscript trước khi validate lại methodology sau phân tích.

### Human checkpoint

1. Duyệt research question, quyết định methodology, và protocol đã freeze.
2. Duyệt output pilot trước khi chạy full (tốn API cost).
3. Duyệt claim matrix cuối trước khi hoàn thiện manuscript.

## Quy ước repo

**Dataset**: nguồn duy nhất là `datasets/text2sql/<name>`. Baseline symlink vào đây, không nhân bản.

**Layout baseline**: `baselines/text2sql/NN_<name>/` với `README.md`, `code/`, `data/`, `logs/`, `results/`.
`code/` chứa repo gốc đã clone; không sửa trực tiếp mà ghi rõ patch trong README.

**Hợp đồng output** — mỗi case một dòng trong `results/<run_id>/predictions.jsonl`:

```
baseline, smoke_status, case{idx, db_id, question, utterance,
                             conversation_history, query, sql}
model, pred_sql, gold_sql
pred_exec{status, row_count, result_hash, error}
gold_exec{...}
call_error, usage{input/output/total_tokens}, latency_s
stage_logs{...}          # raw output từng stage — dữ liệu cốt lõi cho attribution
```

`stage_logs` là **Logging Matrix**, thứ phân biệt dự án này với attribution who/when tổng quát.
Mọi adapter mới phải ghi được nó. Với DIN-SQL, key là
`schema_links_raw`, `classification_raw`, `sql_raw`, `correction_raw`.

Mỗi run kèm `run_manifest.json` ghi `status`, `n`, `model`, `metrics`, `outputs`, và với run đã merge
thì thêm `merge{source_files, unique_case_ids, missing_case_ids, duplicate_case_ids}`.

**Metric**: tính tập trung bằng `baselines/text2sql/analysis/`, không dùng evaluator riêng của từng repo —
để 4 baseline so sánh được với nhau. EX so `result_hash` trên SQLite local; VES-style theo BIRD
(`sqrt(gold_time/pred_time)*100`, 30 vòng, cap 1s/case).

## Trạng thái cần biết

- Git chỉ track 98 file, toàn bộ nằm trong `07_sqlfixagent/server_bundle/`. Code adapter, kết quả run,
  script phân tích đều **chưa được track** — kết quả hiện tại không tái tạo được từ repo.
- Runner sinh `predictions.jsonl` không có trong repo. `01_gpt4o_mini_direct/README.md` trỏ tới
  `scripts/run_gpt4o_mini_direct_text2sql.py` — thư mục `scripts/` ở root không tồn tại.
- `tests/test_failure_attribution.py` import package `failure_attribution` (các module `evaluate`,
  `methods`, `normalization`, `run`, `schema`, `llm`) — package chưa tồn tại. Test mô tả 4 phương pháp
  attribution: `all_at_once`, `step_by_step`, `binary_search`, `hybrid`.
- `baselines/text2sql/baselines/text2sql/analysis/` là thư mục lồng sai do script chạy sai cwd.
- Run thật thực hiện từ WSL (`source_repo: /mnt/c/research/...`). SQLFixAgent cần server GPU riêng.

Khi ba mục đầu được xử lý, xóa chúng khỏi phần này.
