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
