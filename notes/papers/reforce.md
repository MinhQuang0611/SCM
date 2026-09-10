## ReFoRCE
# Pipeline
- Database Information Compression ( nói chung là schema linking) : gom các bảng, thêm mô tả và data mẫu thay cho toàn bộ schema
- Candidate Generation with Self-refinement : Sinh nhiều candidate SQL -> chạy SQL ( nếu lỗi) -> LLM sửa ( max 5 lần) 
  - Nếu SQL trả kết quả là bảng rỗng vẫn coi là lỗi ( chưa chắc )
- Majority Voting : Bỏ phiếu các SQL dựa trên output của SQL ( nếu không thằng nào chiếm đa số thì qua bước tiếp theo)
- Column Exploration: LLM đọc thêm thông tin về cột sau đó sinh lại SQL -> vòng lặp sinh và vote 

# Oracle Experiment
- Cho luôn gold table . EX tăng từ 35.83 lên 36.2 (0.37) nhưng Pass@8 tăng từ 39.85 lên 46.8 (7)
- Dù biết trước được bảng đúng, pass8 tăng lên đáng kể nhưng lựa chọn cuối vẫn chưa chọn được, nên EX gần như ko cải thiện
