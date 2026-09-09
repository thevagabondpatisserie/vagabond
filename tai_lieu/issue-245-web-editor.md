# Web order và trình biên tập marketing - Issue #245

## Phạm vi

Tham chiếu [Vagabond (Copy), Home 886:2229](https://www.figma.com/design/Dgdtyqo4ioT6YPg1OXWklr/Vagabond--Copy-?node-id=886-2229).
Nền đen, ảnh croissant gốc, font Vagabond Sans/Qualy, xanh #29bdb3, tiêu đề
lớn và nút viền. Dùng HTML/CSS/JS hiện hành của Frappe. Các ID và API đặt
bánh giữ nguyên. Đây là bản triển khai đầu, chưa phải nghiệm thu toàn bộ
desktop/mobile của file Figma.

`/bien-tap-web` là dashboard nội dung: số khối, số khối hiện, phiên bản,
nháp/xuất bản và lịch sử. Không phải dashboard doanh thu hoặc quảng cáo.

## Team marketing sử dụng

1. Đăng nhập tài khoản có role Marketing hoặc System Manager, mở `/bien-tap-web`.
2. Chọn khối để sửa chữ, ảnh, nút. Tải ảnh PNG/JPG/WebP từ máy hoặc dán URL.
   Ảnh tải lên là file công khai ngay cả khi trang vẫn là nháp.
3. Thêm Ảnh bìa, Câu chuyện, Ảnh và chữ, Thông báo. Kéo hoặc dùng nút lên,
   xuống để đổi thứ tự; dùng Ẩn/Hiện để gỡ khối khỏi trang mà vẫn giữ nội dung.
4. Xem trước Desktop/Mobile. Lưu nháp chưa đổi nội dung khách nhìn thấy.
5. Xuất bản rồi tải lại website để đối chiếu. Có lịch sử 20 bản công khai
   trước; khôi phục vào nháp, xem lại rồi xuất bản.

Nếu có người vừa sửa: giữ nội dung đang viết, tải lại dữ liệu mới rồi sửa
tiếp. API từ chối phiên bản cũ. Khi mất phản hồi, tải lại để đối chiếu trạng
thái đã lưu trước khi thử lại. Không có nút xoá vĩnh viễn.

## Lưu trữ và bảo vệ

- `Vagabond Noi Dung Web/order` giữ nháp, công khai, phiên bản và lịch sử.
- GET công khai chỉ trả `khoi`; không trả nháp, tài khoản hoặc lịch sử.
- POST lưu/tải ảnh kiểm role ở máy chủ, dùng CSRF Frappe; Document.validate
  chặn Desk/REST save trực tiếp không qua editor.
- Kiểm phiên bản bên trong khóa hàng DB. Lần đầu dùng insert với tên duy
  nhất; hai yêu cầu tạo đầu đồng thời có thể bị DB từ chối, không ghi đè.
- Nội dung chỉ là text và URL, renderer dùng textContent; không nhận HTML,
  JavaScript, giá hoặc tồn. Ảnh tải lên kiểm định dạng, dung lượng và số pixel.
- `trang.dong_bo()` không quản DocType nội dung, nên deploy không đè bài viết.
- Không tự cấp role Marketing cho tài khoản nào.

## Kiểm chứng và cổng còn lại

Đã kiểm syntax JS, bộ tầng khung, khớp bundle và cổng trước deploy tại local.
Đã kiểm bằng trình duyệt localhost: tải editor, thêm khối, sửa tiêu đề,
đổi thứ tự bằng nút, khung mobile, nút từ khối dẫn sang luồng đặt trước.
Local preview dùng GET fixture, chưa chứng minh POST hoặc lưu DB thật.

Ca bench có sẵn:

```sh
bench --site <site-thu> execute vagabond.khung.bench_thu.web_editor_245.chay
```

Chỉ chạy site riêng có `vagabond_bench_thu=1`, đã migrate và chưa có nội dung
order. Kiểm tạo/lưu/reload, Guest, Marketing, stale version, Document.save,
nháp/công khai/lịch sử, khôi phục và đồng bộ Web Page; rollback sau ca.

Trước phát hành còn cần:

- Chạy bench trên SHA PR, kiểm upload ảnh thật, hai request đồng thời và
  migrate/reload qua HTTP với tài khoản Marketing thật trên site thử.
- Review độc lập và đối chiếu thêm frame mobile/product/cart trong Figma.
- Kiểm giỏ/checkout desktop/mobile với fixture đủ sản phẩm, ảnh và giao hàng.
- Ảnh bìa gốc Figma khoảng 8 MB: cần bản phân phối tối ưu trước production.
- Đặt phiên bản/patch theo main tại lúc phát hành, kiểm CI, migrate và live.

Chưa merge, deploy hoặc thay dữ liệu site bán hàng. Không suy từ kiểm local
ra trạng thái production.
