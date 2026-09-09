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

Fresh install đánh dấu patch đã chạy mà không chạy thân patch. `nang_cap_ci` gieo hai Server Script từ snapshot cũ, bỏ đúng bảy dấu patch trên bench dùng một lần rồi chạy migrate thật. Sau hai lượt phải có đủ cột, metadata, Patch Log và Server Script khớp mã nguồn. Asset được build thật để kiểm đường in của Frappe.

Sau hai lượt đầy đủ và hoàn nguyên sạch, runner chạy hai cửa M-Invoice với hai SI độc lập qua Python và Server Script; chỉ HTTP cuối được giả lập. Ca nghiệp vụ đỏ vẫn cho chạy các phần độc lập để thu đủ chẩn đoán, nhưng kết quả cuối bắt buộc đỏ nếu bất kỳ phần nào hỏng. Mất an toàn hoàn nguyên thì dừng ngay. Sau khi đóng kết nối của bộ savepoint, tiến trình riêng kiểm hai người xuất đồng thời, nhiều dòng qua nhiều lô và thử lại sau commit mất phản hồi. Các ca này có commit thật, chỉ chạy trên bench dùng một lần. Artifact bổ sung `minvoice-243.json`, `kho-tang-243.json` và kết quả từng tiến trình.

Server Script được bật trong `common_site_config.json` của bench dùng một lần. Đối chiếu bằng chính `is_safe_exec_enabled()` của Frappe trước khi chạy, vì cờ cùng tên trong cấu hình site không bật được đường này trên Frappe 16.

Đây là môi trường tái hiện dùng fixture. Kết quả đạt không thay thế kiểm cấu hình thực tế trước deploy và kiểm live sau migrate.
