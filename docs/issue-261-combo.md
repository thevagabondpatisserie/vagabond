# #261 - Mã hàng combo và món thành phần

Ảnh issue ghi KMCB00002 vào HDB-26-09-01599 như Item thường. Luồng cũ chỉ
rã Vagabond Combo (CB...), còn Kiểm bánh đọc Sales Invoice Item nên không
thấy món ruột. Đây là hai loại mã khác nhau, không suy ruột từ tên món.

## Thay đổi

- Cấu hình Vagabond Combo có Link Mã hàng combo (KMCB), unique và ô tìm trên app.
- Chọn KMCB tại POS dùng cấu hình đúng quầy/nguồn. Mã thiếu cấu hình báo rõ,
  không tiếp tục đưa một dòng combo không đếm được vào bill.
- Món từ combo có mã và tên combo; hai cấu hình cùng tên không nhập chung.
- before_validate của Sales Invoice rã mã KMCB cố định cho đường Desk/API.
  Phân giá trọn bộ theo giá lẻ, phần dư VND theo phần lẻ lớn nhất, không âm.
- Không tạo phiếu xuất riêng: core và luồng xuất hiện hành dùng món đã rã.
- Không sửa hàng loạt bill cũ. Hoá đơn đã ghi sổ/có số HĐĐT không được rã lại.

## Cấu hình trước phát hành

Quản lý chọn mã KMCB và khai đúng các món trong Khuyến mãi - combo. Không tự
điền thành phần KMCB00002 từ tên “3 bánh”. Đang chờ xác nhận mã/số lượng thật.
Combo có nhóm chọn/OTP/hạn mức phải đi qua màn Combo; API nhập thẳng mã cha
báo chuyển sang màn chọn để giữ các luật khuyến mãi hiện có.

## Kiểm

- Phép thuần: tổng tiền, nhiều bộ, món trùng, số không hợp lệ, chia lẻ không âm.
- Node: món lẻ và hai combo cùng tên giữ đúng số lượng/nguồn.
- Bench: API tao_don_tay, insert/reload, ba điểm, lưu lại và hủy mềm, không SLE riêng.
- Trước merge: cần bench đúng SHA, review độc lập, xác nhận cấu hình thật và
  kiểm UI/in tại ba điểm. Ca mất phản hồi tạo bill, nhóm chọn sửa lại và kho
  stock-item thực tế cần bổ sung bằng chứng; không coi test helper là UAT.

## Sửa theo review PR264

Thành tiền phân bổ được lưu riêng trên dòng rã và chốt sau
`calculate_item_values` của core, trước VAT/chiết khấu. Đơn giá đã làm tròn
không được dùng để tính ngược làm mất đồng. Chỉ áp dụng mẫu VAT VND được
hỗ trợ; sửa lượng riêng trên dòng rã yêu cầu chọn lại combo. Giữ nguyên
object/tên các dòng không phải combo khi rã thêm mã cha. Bench bổ sung
combo 155.000 với lượng 3 và 1, precision đơn giá 0/2, lưu lại, GL/payload.

Thứ tự tích hợp: PR264 trước, PR265 kế tiếp; PR265 nhận đầy đủ PR264 và
giữ phiên bản472. Chưa merge main, chưa deploy.

Hoàn theo tiền trên bill combo giữ số nguyên đồng đã duyệt, không tự làm tròn sau khi chuyển tiền. Nếu bill đã có phiếu trả ghi sổ, kế toán phải đối chiếu và xử lý phiếu cũ trước khi lập yêu cầu hoàn khác; không hoàn toàn bộ chồng lên phần đã trả. Sửa đổi phiếu hoàn đã hủy giữ lại số tiền đã duyệt.
