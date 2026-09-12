# #290 - Tách đơn kẹt khỏi chuỗi cuối ngày

Nền: main 948952b, v483. Bản này dự kiến v484, chưa deploy.

- A1: chỉ SI đã ghi sổ chưa có HĐĐT giữ cửa ngày cũ. Giữ cờ đối chiếu, không tự bỏ cờ; lỗi đọc vẫn chặn.
- A2: nút ghi sổ ngày chọn lấy cả bill quầy, loại hủy/tạm tính. Một đơn lỗi không làm mất kết quả đơn khác.
- A3: chuẩn bị ghi sổ lưu nháp có KMCB để hook rã trước submit. Frappe 16.27.1 Document._submit đặt docstatus=1 trước validate, nên không đổi chốt của combo_mon.
- B2: gửi lại thông tin đơn đã từ chối chuyển về Chờ duyệt, gỡ người/thời điểm/ý kiến/dấu cũ. Không tự duyệt.
- B4: thêm Hàng tặng xuất kho thật trong Vagabond Settings, mặc định tắt. Khi tắt, đơn nháp ghi VAT và chờ giá vốn, không SLE; vẫn giữ duyệt và không sinh 511/131. Tờ đã ghi sổ/hủy giữ chính sách lịch sử.
- D1: Đơn còn treo chỉ lấy trước hôm nay trong khoảng ngày đã chọn.

## B1 chưa được kết luận nguyên nhân

_upsert_hoa_don hiện tải SI cũ, cập nhật trường nguồn và không gán lý do/loại tặng. Ca gọi nguyên hàm với nguồn không có lý do vẫn giữ các trường người nhập trên nền hiện tại. Thêm ca DB save/reload để kiểm cả hook. Không nhận modified cùng nhịp đồng bộ là bằng chứng hàm đó đã xóa trường. Cần Version diff hoặc script live của đơn xảy ra sự cố nếu ca bench vẫn giữ được chữ.

## Kiểm và giới hạn

Ca mới A1/A2/A3/B2 đỏ trên mã cũ; sau sửa kiểm tầng khung đạt. Có ca bench kho tắt thiếu tồn vẫn ghi VAT/không SLE/hủy, combo nháp cũ qua cửa ghi sổ, và đồng bộ SI tặng reload. Chờ CI bench trên SHA PR; không dùng unit thay bằng chứng core.

Không thao tác lại hóa đơn 11/09 đã xử lý tay. Không deploy trước 23:30 ngày 12/09 theo điều phối. B3/C1/C2/D2/D3 còn thuộc bản sau, không tuyên bố toàn issue đã hết lỗi.

## Sửa theo review 5646691333

B1 đã tái hiện: với cờ máy còn 1, đồng bộ đổi Hàng tặng thành Tiền mặt. Ca cũ đặt cờ 0 và bỏ qua bảng thanh toán nên chỉ chứng minh nhánh đã đúng, không phủ sự cố. Nay pos_chot/pos_sua_don/luu_thanh_toan hạ cờ khi người chọn; đồng bộ giữ Hàng tặng và không nạp bảng máy. Hook gỡ bảng máy cũ cho quà tặng; bảng nhập tay phải được kiểm sửa rõ ràng, không âm thầm xóa tiền người đã nhập. Ca bench đi qua pos_chot, luu_thong_tin, duyệt, đồng bộ và reload với nguồn trả phương thức thật; không mock hook hay hàm điền bảng.

A2 chỉ lấy Sales có nguồn Pancake và quầy trong tu_ghi_so_quay; không lấy trả hàng hoặc tạm tính; bỏ qua quà chờ duyệt/từ chối. B4 thêm ca bật kho lại rồi hủy tờ đã ghi sổ khi tắt. Nháp đã mang dấu kho 0 vẫn giữ đường cũ sau khi bật lại.

Bench lượt đầu 173/176 mỗi lượt: fixture B1 thiếu nguồn đơn; fixture A3 phát hiện bench thiếu Custom Field vgb_ma_tham_chieu so với snapshot site; ca kho cũ chưa bật công tắc mới. Bổ sung đúng nguồn/cột/công tắc, giữ mọi kiểm GL/SLE. Không coi lượt đỏ là đạt. Trong ca tích hợp, transaction control bị vô hiệu hóa có chủ ý; rollback không savepoint không chứng minh rollback thật.
