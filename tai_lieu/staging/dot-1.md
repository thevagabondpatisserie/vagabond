# Đợt 1 - Issue257

## Phạm vi nghiệm thu

| Luồng | Thao tác qua app | Bằng chứng bắt buộc |
|---|---|---|
| Nhận hàng | chọn phiếu, nhập số, gửi; lỗi rồi sửa/gửi lại | một chứng từ, đúng hệ số/SLE; không khoá form vĩnh viễn |
| Sản xuất | chọn BOM, nguyên liệu, ghi nhận thành phẩm | đúng nguyên liệu/thành phẩm/SLE; lô tham chiếu không gây chặn vô lý |
| Bán/hàng tặng | chọn kho, ghi sổ, hủy chứng từ thử | giá vốn đúng kho/64181, thuế hỗn hợp, đảo đủ; M-Invoice chỉ stub |
| Thanh toán | đối chiếu, ghi nhận, huỷ, bỏ đối chiếu, ghi nhận lại | trạng thái rõ, không chuyển/ghi đôi, không gửi thư trùng; phụ thuộc PR250 |
| Vận đơn | cập nhật ngày đang xem, đổi ngày ở nguồn thử | đơn đổi ngày biến mất khỏi ngày cũ, có ở ngày mới; hàng đợi không bỏ đói |

Chưa có ca trình duyệt chạy đủ năm luồng. Bộ bench hiện có là nền kiểm
Document/GL/SLE, không được đổi tên thành E2E. Nghiệm thu cần bấm nút thật,
HTTP thật tới site thử, chỉ stub dịch vụ bên ngoài ở ranh giới.

## Môi trường

Tái dùng core pin và fixture trong khung/bench_thu. CI hiện dùng một lần,
không phải staging cố định. Staging cố định cần URL/tài nguyên riêng được
xác minh, không lấy production làm site thử, không tạo dịch vụ tính phí
chưa có hạn mức. Không dùng mật khẩu mẫu CI trên site truy cập công khai.
Không mang dữ liệu/bí mật production sang thử; email và API ngoài bị chặn.

## Trạng thái và đơn vị

PR250 giữ nguyên quyền sở hữu nhánh. Chuẩn hoá theo cùng nguồn máy chủ,
không sửa chồng. Công cụ `python3 -m vagabond.khung.staging.ra_uom input.json
output.json` chỉ rà snapshot đã xuất, chưa đọc live hoặc sửa dữ liệu.
JSON gồm items (item_code, stock_uom, purchase_uom, sales_uom, uoms với
uom/conversion_factor) và quy_uoc_da_duyet (item_code -> stock_uom).
Quy đổi đóng gói cần bằng chứng từng món; không suy số quả/thùng từ tên.

## Đo trước và sau

Chốt ba màn theo tần suất thực; ứng viên là vận đơn, nhận hàng/kiểm bánh,
hồ sơ thanh toán. Cùng dữ liệu, role, máy/mạng và số lượt; tách tải lần đầu
và cache. Báo số thao tác, p50/p95 thời gian tới dữ liệu dùng được, số API,
SQL và dung lượng. Chưa có số đo mới nên chưa tuyên bố tăng tốc.
Chỉ tối ưu sau baseline; phép kiểm hồi quy phải bắt lại lỗi cũ.

Gateway `khung/staging/phuc_vu_ci.py` mới chỉ là nền phục vụ HTTP local;
chưa có kết quả chạy trên CI, chưa phải staging đã nghiệm thu. Kiểm cờ site,
chặn socket connect/connect_ex ra ngoài, không có worker và chỉ bind127.0.0.1.
Đây không phải firewall chống mọi subprocess. Driver `kiem_man.cjs` đăng nhập
qua HTTP thật, mở năm màn ở 390px/1280px và kiểm ô sẵn sàng, lỗi API/JS;
lưu ảnh, trace và thời gian vào artifacts. Đây chỉ là kiểm mở màn với
Administrator, chưa chứng minh quyền nhân viên hoặc năm luồng nghiệp vụ.
CI chạy bước này sau bench. Còn cần fixture thao tác và năm kịch bản đầy đủ.
