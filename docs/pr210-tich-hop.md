# PR210 - Đẩy mã Pancake an toàn, v481

Nền 01dc0ae (v480), tích hợp nhánh cũ v435-gia-co-day-ma-pancake và giữ đủ mã/patch trên main. Không force push, không deploy riêng. Issue204, findings ở comment5556113504.

## Hành vi

- Mã cũ tìm theo mã HOẶC tên bằng một truy vấn, thứ tự creation/name ổn định, lấy dư một hàng để báo trang kế. Có ảnh và quyền đẩy theo máy chủ.
- Nút mã mới/mã cũ dùng cùng handler. Chưa rõ hoặc mạng lỗi chỉ cho Kiểm lại; giá0 có xác nhận rõ. Giá âm/NaN/inf bị chặn kể cả khi xác nhận.
- Request chỉ ghi ý định vào Vagabond Day Pancake, tên SHA256(shop + phân cách + mã chuẩn), dưới khoá Item. Worker chỉ được enqueue sau commit. Không POST bên ngoài từ request người dùng.
- Worker khoá hàng ý định, chỉ nhận trạng thái cho, đặt dang_gui và commit TRƯỚC POST. Job trùng không được nhận lại. Không dùng Redis lock/TTL làm hàng rào dữ liệu.
- Tìm dở/lỗi TRƯỚC POST được thử lại. Sau POST, HTTP lỗi/JSON lỗi/timeout đều giữ chua_ro; tìm rỗng không gỡ dấu. Không tự retry POST.
- Kiểm lại chỉ đọc Pancake. Dấu cho bị kẹt enqueue có thể được gửi lại job qua cùng nút Đẩy sau tải lại; DB vẫn chỉ cho một worker nhận.
- Không tự xoá dấu theo tuổi. Trường hợp đã gửi nhưng không xác minh được cần quản trị đối chiếu trên Pancake; bản này không có nút xoá dấu hoặc cưỡng bức tạo lại.

## Nguồn và kiểm

Frappe16.27.1, background_jobs.py enqueue: db.after_commit.add(enqueue_call). Integration Request.clear_old_logs xoá sau30ngày nên không dùng làm dấu chống trùng lâu dài. Nguồn đọc tại tagv16.27.1 SHA f33ac3f00ab818e21b25ddbec93efb653fd9aa1b.

Ca thuần gọi hàm thật với DB/HTTP giả: nhận không POST/không commit caller, enqueue sau commit, timeout rồi rollback/reload không POST lại, worker lặp trong lúc POST, commit lỗi không POST, phản hồi HTTP/JSON lỗi, tìm dở/trùng, giá xấu; Node chạy handler giá0/kiểm lại.

Bench CI dùng một lần: day_pancake_ci.py dựng Item và ý định thật, commit thật; tiến trình con chết sau HTTP stub, tiến trình mới đọc dang_gui và không POST lại; hai tiến trình worker cùng mã chỉ một POST. Có khoá GITHUB_ACTIONS và site bench-ci.localhost/vagabond_bench_thu. Fixture được giữ trong bench dùng một lần và huỷ cùng container; không gọi script này trên production, không gọi Pancake thật.

Chưa có UAT người dùng trên site thật. Không nhận local mock là chứng minh commit/đồng thời DB; chờ artifact pancake-durable.json từ CI. Không thay quy tắc thuế, không phát hành hóa đơn trong PR này.
