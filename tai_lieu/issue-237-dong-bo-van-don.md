# Issue237: đồng bộ vận đơn Pancake, v455

## Vấn đề đã sửa

- Truy vấn theo ngày giao không chứa đơn đã dời khỏi ngày đó hoặc đã huỷ. Đọc bổ sung đúng ID các vận đơn còn mở; lượt hôm nay kiểm thêm ngày quá hạn.
- Danh sách món mới rỗng từng bị bỏ qua. Nay xoá đúng bảng con khi nguồn trả items=[] hợp lệ. Thiếu items/sai cấu trúc không phải xoá món. So sánh cả thứ tự, giá và dấu hàng tặng.
- Phản hồi thiếu thông tin liên hệ/ghi chú không ghi đè dữ liệu đang có. Rỗng được chỉ rõ vẫn cập nhật.
- HTTP200 không có data dạng list hoặc success=false không được coi là ngày không có đơn. Thay đổi hẹp ở kiem_banh._keo_don dùng chung; phân trang/retry vẫn giữ.
- Tạo mới dùng ngày thực từ nguồn. Đổi ngày, huỷ pickup chờ khách lấy và bỏ món đi qua đường đồng bộ chung.
- Khoá cùng tên cho cron/nút tay. Mỗi đơn có savepoint: lỗi lưu món sau đổi ngày trả lại cả ngày/món, các đơn khác tiếp tục. Lỗi đọc/ghi trả mã đơn ra giao diện và cron ghi Error Log.
- Đọc bổ sung tối đa20 ID hoặc15 giây mỗi lượt, timeout mỗi GET tối đa5 giây. Cursor luân phiên để ID lỗi không chặn các đơn sau. Danh sách đơn chưa kiểm được báo rõ, lần sau tiếp tục. Đây là giới hạn phần đọc bổ sung; truy vấn theo ngày vẫn phân trang như trước.
- Tab Cần phân công mặc định mới nhất trước, các tab khác giữ thứ tự tuyến; lựa chọn sắp xếp tay vẫn được tôn trọng. Máy chủ trả đủ ngày, không cắt500 dòng trước khi sắp xếp.
- Khách tự lấy và book app không bị mở camera khi hoàn thành. Shipper giao thường vẫn chụp ảnh. Giữ nguyên phân biệt chặng chở tới quầy và khách đã lấy.
- Phí book app lưu vào phi_giao sẵn có, riêng COD. POST, quyền sales/kế toán, số đồng nguyên không âm; chặn sau đối soát hoặc huỷ, có Comment ghi vết. Không tạo GL hoặc đặt xe trong cửa nhập phí.

## Ranh giới

Không suy huỷ từ 404, timeout hay đơn vắng trong kết quả; máy giữ dữ liệu và báo cần kiểm. Đơn đang giao trong ngày vẫn giữ luật yêu cầu điều phối xử lý đổi ngày/huỷ, có nhật ký; không tự giật đơn khỏi người đang cầm hàng. Các đơn đã hoàn thành không mở lại. Khoá đồng bộ bảo vệ cron/nút đồng bộ, không phải ràng buộc unique toàn DB cho mọi đường tạo Van Don.

Chưa chạy bench thật hoặc HTTP/site thật tại Codex, chưa sửa vận đơn thật, chưa merge/deploy. Mọi phản hồi Pancake trong ca kiểm được giả lập. Không đóng issue chỉ dựa CI.

## Bằng chứng local

Gate rc0, 2.655 ca thuần đạt. Ca Node thực thi handler giao: pickup/book không camera/upload, giao thường vẫn camera/upload, mỗi thao tác gọi API hoàn thành một lần. Review chéo đã xử lý các finding: bỏ sót đơn quá hạn, đọc bổ sung không giới hạn, xoá trường vắng, cắt500 đơn trước sort, khoá phường sai chính tả.

## Claude review/bench/deploy

1. Kiểm đúng SHA bàn giao và main mới. PR236 đang độc lập với bản này; giữ đủ patch của mọi bản đã merge và tăng số nếu v455 đã được dùng. Không đưa phần thuế chưa xong vào release này.
2. Chạy gate và bốn ca mới trong khung/kiem_that/thu_dong_bo_237.py qua runner: dời ngày/bỏ món/replay không nhân đôi; items rỗng và huỷ pickup; lỗi sau đổi ngày rollback; phí lưu/reload/COD không đổi/chặn sau đối soát. Ca dùng Van Don mới, savepoint và HTTP stub, không tra đơn thật. Hai khoá chung_tu_con_sot và so_luong_lech phải rỗng.
3. Kiểm API thực: GET không được luu_phi_book; người không có vai trò sales/kế toán bị chặn; NaN/inf/âm/lẻ bị chặn. Hai phiên đồng bộ cùng lúc phải có một phiên giữ khoá; không sinh hai vận đơn cùng ID ở hai lượt đồng bộ.
4. Dùng snapshot ẩn danh của đơn Loan Anh báo để thử: bấm đồng bộ ngày cũ sau khi đổi ngày trên nguồn; reload ngày cũ không còn, ngày mới có đúng một vận đơn; giảm2 món còn1, rồi xoá hết; status6/7; lỗi404/timeout và phản hồi thiếu data giữ nguyên dữ liệu, báo mã lỗi. Ngày/giờ có múi giờ đúng như source thật.
5. Kiểm giao diện: đơn mới đầu Cần phân công, lựa chọn sort tay; pickup/book hoàn thành không camera; chặng bỏ xuống quầy không báo khách đã nhận; phí book nhìn lại đúng và không đổi COD.
6. Đạt thì merge/deploy theo phân công anh Việt. Kiểm APPVER/Patch Log, quan sát một lượt tự đồng bộ và thao tác ngày cũ/ngày mới được phép. Không đánh dấu hoàn thành hay đẩy trạng thái Pancake của đơn thật để thử. Đếm số đơn còn lỗi/đợi đối chiếu, kiểm cursor tiến triển qua các lượt, rồi cập nhật #237 bằng chứng.
