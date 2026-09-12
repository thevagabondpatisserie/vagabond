# PR210 - Đẩy mã Pancake an toàn, v481

Nền 01dc0ae (v480), tích hợp nhánh cũ v435-gia-co-day-ma-pancake và giữ đủ mã/patch trên main. Không force push, không deploy riêng. Issue204, findings ở comment5556113504.

## Hành vi

- Mã cũ tìm theo mã HOẶC tên bằng một truy vấn, thứ tự creation/name ổn định, lấy dư một hàng để báo trang kế. Có ảnh và quyền đẩy theo máy chủ.
- Nút mã mới/mã cũ dùng cùng handler. Chưa rõ hoặc mạng lỗi chỉ cho Kiểm lại; giá0 có xác nhận rõ. Giá âm/NaN/inf bị chặn kể cả khi xác nhận.
- Request chỉ ghi ý định vào Vagabond Day Pancake, tên SHA256(shop + phân cách + mã chuẩn), dưới khoá Item. Worker chỉ được enqueue sau commit. Không POST bên ngoài từ request người dùng.
- Worker khoá hàng ý định, chỉ nhận trạng thái cho, đặt dang_gui và commit TRƯỚC POST. Job trùng không được nhận lại. Không dùng Redis lock/TTL làm hàng rào dữ liệu.
- Tìm dở/lỗi TRƯỚC POST được thử lại. Sau POST, HTTP lỗi/JSON lỗi/timeout đều giữ chua_ro; tìm rỗng không gỡ dấu. Không tự retry POST.
- Kiểm lại chỉ GET Pancake và lưu kết quả khớp vào dấu nội bộ. Dấu cho bị kẹt enqueue có thể được gửi lại job qua cùng nút Đẩy sau tải lại; DB vẫn chỉ cho một worker nhận.
- Không tự xoá dấu theo tuổi. Trường hợp đã gửi nhưng không xác minh được cần quản trị đối chiếu trên Pancake; Desk có cửa đối soát cho giám đốc với lý do/bằng chứng bắt buộc; không xóa dấu hoặc tự gửi lại.

## Nguồn và kiểm

Frappe16.27.1, background_jobs.py enqueue: db.after_commit.add(enqueue_call). Integration Request.clear_old_logs xoá sau30ngày nên không dùng làm dấu chống trùng lâu dài. Nguồn đọc tại tagv16.27.1 SHA f33ac3f00ab818e21b25ddbec93efb653fd9aa1b.

Ca thuần gọi hàm thật với DB/HTTP giả: nhận không POST/không commit caller, enqueue sau commit, timeout rồi rollback/reload không POST lại, worker lặp trong lúc POST, commit lỗi không POST, phản hồi HTTP/JSON lỗi, tìm dở/trùng, giá xấu; Node chạy handler giá0/kiểm lại.

Bench CI dùng một lần: day_pancake_ci.py dựng Item và ý định thật, commit thật; tiến trình con chết sau HTTP stub, tiến trình mới đọc dang_gui và không POST lại; hai tiến trình worker cùng mã chỉ một POST. Có khoá GITHUB_ACTIONS và site bench-ci.localhost/vagabond_bench_thu. Fixture được giữ trong bench dùng một lần và huỷ cùng container; không gọi script này trên production, không gọi Pancake thật.

Chưa có UAT người dùng trên site thật. Không nhận local mock là chứng minh commit/đồng thời DB; chờ artifact pancake-durable.json từ CI. Không thay quy tắc thuế, không phát hành hóa đơn trong PR này.


## Vòng Claude 12/09

- Đã thêm Desk Đối soát và mở lại, chỉ System Manager/Giám đốc/AP Giám đốc. Bắt buộc lý do và bằng chứng Pancake đã xác minh không còn mã hoặc xử lý yêu cầu cũ; tìm rỗng không đủ. Lưu lịch sử, không tự gửi.
- Worker commit dấu rồi khóa lại xuyên suốt HTTP; mã lần gửi chặn worker cũ khi người đối soát đã mở lại giữa hai lần khóa. Không suy ra ConnectionError nghĩa là chưa gửi.
- Payload hỏng trước POST thành lỗi có thể lập lại. Kiểm lại tìm đúng một mã lưu trạng thái; dấu thành công mà tìm rỗng báo lệch, không xanh.
- Trạng thái mới nhận là dang_cho màu vàng. Thông báo cùng mã cập nhật cả ô vừa tạo và danh sách.
- Bỏ bảy ca dò chuỗi cũ; bổ sung hành vi đọc trang/giá, payload hỏng, đối soát và worker cũ.
- Giá là snapshot lúc người dùng bấm; worker không tự thay bằng giá khác. Không nhận đây là đồng bộ cập nhật giá liên tục.


## Vòng tiếp: vết gửi, quyền và khóa không chờ

Giữ khóa Item để tuần tự hóa hai request lúc chưa có dấu, nhưng cả Item/dấu trong request đều NOWAIT. Không có đường giữ Item chờ HTTP. Worker vẫn giữ dấu xuyên POST; đối soát đang chen vào phải trả câu chờ. Kết quả worker ghi bằng SQL có điều kiện ma_lan/dang_gui. Bench thêm stub POST chờ tín hiệu, gọi request/đối soát trong lúc đó để đo khóa thật.

Vết gửi lưu thời điểm bắt đầu trước commit, HTTP/loại lỗi/hash và độ dài phản hồi. Không lưu nguyên URL/ngoại lệ/body có thể chứa API key. Kiểm lại cần quyền đẩy và Item write; đọc mới sau GET. Bổ sung xử lý lỗi đọc giá, chặn giá lẻ đồng bị cắt thành0, deduplicate job theo mã lần, nhãn nút trên cùng.

Bench3790bcb: migrate và tích hợp hai lượt đạt; durability/crash PASS. Bước Desk timeout chờ nút trên390. Đã đối chiếu Frappe16.27.1 page.add_inner_button: mobile dùng menu link, bổ sung đúng đường bấm và lưu ảnh/text khi hỏng. Chưa coi là kiểm Desk đạt.

## Chốt góp ý trên 29cff23

Kiểm lại sau GET đầy đủ và rỗng bỏ thông báo lỗi trước POST đã cũ, trả chua_co; các dấu chưa rõ vẫn giữ nguyên hàng rào. SQL kết lượt xóa document cache cả khi CAS không ghi vì mã lần đã đổi. CAS không trúng là trường hợp worker cũ hợp lệ; lỗi SQL/schema vẫn ném ngoại lệ, không bị nuốt.

Bench giai đoạn worker giữ khóa nay bắt đúng dang_cho và câu "Đang có lượt xử lý mã này", không chấp nhận chua_ro do đọc dấu không khóa. Ca này chứng minh khóa dấu; không tự nhận riêng nó chứng minh khóa Item lúc dấu chưa tồn tại.

Bench 29cff23: migrate/integration hai lượt và durability/phase2 PASS. Dialog Desk đã mở trên390 nhưng locator input khớp cả ô ẩn và checkbox nên strict mode lỗi. Sửa locator thành input[type="checkbox"]; chờ chạy lại, chưa nhận UAT đạt.
