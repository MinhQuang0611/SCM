# DeepEye-SQL

Đọc lại từ paper 2026-08-24. Bản gốc đã xóa, bản này viết mới.

## Thông tin

- Tên: DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework
- Tác giả: Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, Yuyu Luo
- Venue: SIGMOD 2026 (Proc. ACM Manag. Data), DOI 10.1145/3802035
- Preprint: arxiv.org/abs/2510.17586 (v1 2025-10-20, v3 2026-04-03)
- Code: github.com/HKUSTDial/DeepEye-SQL — CÓ code public

## Ý chính

- Họ nói: Text-to-SQL không nên coi là sinh văn bản tự do, mà là **viết một chương trình nhỏ**,
  nên phải làm theo quy trình phần mềm có kiểm chứng (SDLC).
- Nguyên văn: "treating Text-to-SQL not as free-form language generation but as a
  software-engineering problem that demands structured, verifiable orchestration."

## Pipeline — 4 giai đoạn

1. Schema linking, có ràng buộc relational closure
   - trước đó có Semantic Value Retrieval: neo câu hỏi vào dữ liệu thật trong DB
2. N-version programming: sinh **nhiều candidate song song từ 3 generator khác nhau**,
   mỗi generator một lối suy luận
3. Verification bằng tool-chain "Syntax - Logic - Quality", chặn lỗi TRƯỚC khi execute
4. Confidence-aware selection: chọn candidate bằng execution-guided adjudication

## Kết quả

- BIRD dev 73.5, BIRD test 75.07, Spider test 89.8
- Backbone: MoE open-source ~30B tổng / ~3B activated, KHÔNG fine-tune

## Vì sao quan trọng với đề tài

- Đây là baseline sinh ra **nhiều loại artifact nhất** trong nhóm đang xét:
  candidate từ 3 generator, log của checker, SQL sau revision, điểm confidence khi chọn.
- Có sẵn hai câu hỏi attribution kinh điển:
  - hệ không sinh được candidate đúng, hay sinh được rồi chọn sai?
  - checker phát hiện lỗi nhưng sửa không được, hay sửa xong lại xấu đi?
- Có code public, nên là ứng viên testbed thực tế nhất cùng với ReFoRCE.

## Cần xác minh

- Bản v3 (2026-04) khác v1 chỗ nào — số trong repo phải ghi rõ đọc bản nào.
- Ablation từng module: chưa trích được trong lần đọc này, cần mở PDF đầy đủ.
- Chi phí chạy: 3 generator song song nghĩa là chi phí API gấp nhiều lần baseline một lượt.
