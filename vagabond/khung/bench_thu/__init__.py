"""Kịch bản CHỈ chạy trên bench thử (site_config `vagabond_bench_thu: 1`).

Khác tầng `khung/kiem_that` (savepoint, cấm commit), các kịch bản ở đây
CÓ commit và rollback thật, nhiều tiến trình thật, để chứng minh trạng thái
DB sau khi request kết thúc và hành vi khi hai giao dịch đụng nhau. Không
bao giờ trỏ lên site thật; mỗi hàm đều kiểm khoá trước khi làm gì.
"""
