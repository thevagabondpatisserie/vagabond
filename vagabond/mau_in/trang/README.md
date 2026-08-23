# Ảnh chụp các Web Page đang chạy

Đây là **bản chụp để đối chiếu và khôi phục**, KHÔNG phải nguồn tự động đẩy
xuống cơ sở dữ liệu.

## Vì sao chỉ chụp chứ không đẩy

Anh Việt 23/08/2026 đề nghị dùng `fixtures` trong `hooks.py` để quản lịch sử.
Đã cân nhắc và KHÔNG bật, vì `fixtures` không chỉ xuất ra, nó còn **nhập vào
mỗi lần Migrate**. Hệ quả:

1. Tệp trong git cũ hơn bản trên site thì lần deploy tới **âm thầm ghi đè**
   bản trên site. Đó đúng là cảnh mất code mà bộ quy tắc này sinh ra để chặn,
   chỉ khác chiều.
2. Trang `bep` đang được một **Server Script** tên `Chan ghi de APPVER - Web
   Page` canh giữ. Đẩy tự động vào đúng trang đó là hai cơ chế giành nhau một
   bản ghi, và Server Script thì nằm trong cơ sở dữ liệu, git không thấy.
3. Trang `banh` nặng 482KB và có người ngoài kỹ thuật sửa. Ghi đè âm thầm ở
   đó là mất việc của họ.

Nên cách làm ở đây: **chụp lại để có lịch sử và có đường khôi phục, rồi SOI
LỆCH để chuyện sửa tay không còn âm thầm**. Gọi `vagabond.mau_in.soi_lech`
từ app hoặc từ Desk là biết bản trên site có lệch bản trong repo không.

Muốn bật `fixtures` thật thì phải làm đủ ba việc trước, không được làm tắt:
xuất đủ mọi trang từ bản đang chạy để tệp không cũ hơn site, gỡ hoặc dời
Server Script kia, và chốt với người đang sửa trang `banh` rằng từ nay sửa
trên git chứ không sửa trên Desk.

## Cập nhật ảnh chụp

Chưa có lệnh tự động vì Cowork không chạy được `bench`. Cách làm tay: mở
trang trên Desk, chép `main_section_html` và `javascript` ra đúng hai tệp
`<route>.html` và `<route>.js`, rồi chạy `soi_lech` để xác nhận hết lệch.
