# Bench tích hợp theo SHA

Workflow `Bench tich hop SHA` chạy khi PR vào main cập nhật, hoặc bấm Run workflow sau khi workflow đã có trên main. Checkout SHA đầu PR, không dùng SHA merge giả của GitHub. Không nhận URL, tài khoản hay dữ liệu của site sản xuất.

Nền dùng một lần trên Ubuntu 24.04:

- Frappe `f33ac3f00ab818e21b25ddbec93efb653fd9aa1b`.
- ERPNext `de591661b9ba0bd3f62ac25b99b5c85c723515f6`.
- Bench `c9d12503d9d7fbfd94086c3de3cd4ac23dd44823`.
- Python 3.14 và Node 24 theo pyproject/package của Frappe trên.
- MariaDB 10.6, Redis 7; mật khẩu chỉ dành cho container dùng một lần, không phải bí mật sản xuất.

`dung_ci.sh` cài ứng dụng, dựng fixture `nen_bench.dung`, migrate hai lần. Không bật worker, lịch chạy hay email. `chay_ci.py` mở một kết nối Frappe và gọi toàn bộ `cua.chay(im=0)` hai lần trong cùng tiến trình Python. Hai lượt không dựng lại fixture nên bắt được lỗi cache và hàng đợi còn sót. Chặn kết nối socket ra ngoài trong lúc chạy ca kiểm; MariaDB và Redis cục bộ vẫn là thật.

Job đỏ nếu thiếu 11 ca #243, có ca chưa chạy, bất kỳ ca hỏng, mất điểm lưu, còn chứng từ hoặc số lượng lệch. Lỗi cũ cũng không được tự bỏ qua. Khi hoàn nguyên mất an toàn, dừng ngay. Khi chỉ có ca nghiệp vụ đỏ nhưng khung sạch, vẫn chạy lượt hai để có bằng chứng trạng thái lặp lại.

Artifact `bench-<SHA>` gồm SHA của ba repo, log dựng bench, hai log migrate, JSON từng lượt, log tích hợp và traceback nếu lỗi. Không tải site_config, database, email hay thông tin đăng nhập. Workflow không deploy. Chỉ triển khai đúng SHA đã có bằng chứng tích hợp, review và cổng phát hành đạt.

Đây là môi trường tái hiện dùng fixture. Kết quả đạt không thay thế kiểm cấu hình thực tế trước deploy và kiểm live sau migrate. Cửa phát hành M-Invoice và kịch bản đồng thời cần bằng chứng riêng khi thay đổi chạm tới chúng.
