# Hướng dẫn marketing và Sales: trang đặt bánh (#367)

Trang đặt bánh: https://order.thevagabondpatisserie.com/banh
Bảng biên tập: https://order.thevagabondpatisserie.com/bien-tap-web

## Vào bảng biên tập

Mở /bien-tap-web. Chưa đăng nhập thì trang tự chuyển sang đăng nhập rồi quay
lại. Đăng nhập rồi mà thấy "chưa có quyền soạn nội dung" thì nhờ anh Việt cấp
vai Marketing trên Desk (User, thêm dòng Marketing). Góc phải có tên người
đang đăng nhập và nút Đăng xuất.

## Trình biên tập theo thẻ (từ v586)

Minh Vũ đề xuất, anh Việt duyệt ngày 07/10/2026. Mở /bien-tap-web là thấy sáu
thẻ theo việc. **Mỗi lần bấm Lưu là khách thấy ngay**, không còn bước Xuất bản
riêng cho các thẻ này.

- **Ưu đãi**: tên, mô tả, nhóm, mã, đơn tối thiểu, ngày và khung giờ áp dụng,
  ghi chú điều kiện, ảnh 16:9. Khung "Khách sẽ thấy" bên phải hiện đúng thẻ
  khách sẽ thấy. Qua ngày kết thúc web tự ẩn ưu đãi.
- **Tiệc**: tên, mô tả, những gì bao gồm, ngày, giờ, địa điểm, giá vé, số vé,
  hạn đăng ký. Khách bấm "Đăng ký tham gia" trên web, gửi tên, số điện thoại,
  số vé. Gửi đăng ký CHƯA phải đã có vé: nhóm FOH nhận tin trên Lark, Sales gọi
  xác nhận và thu tiền, đổi trạng thái trên Desk (Vagabond Dang Ky Tiec). Web
  hiện số vé còn lại và tự đóng đăng ký khi hết vé hay quá hạn.
- **Tuyển dụng**: tên vị trí, nơi làm (chọn chip hoặc gõ), hình thức, hạn nhận
  hồ sơ, mô tả, yêu cầu và quyền lợi, email nhận hồ sơ.
- **Cửa hàng**: địa chỉ, giờ mở cửa, hotline riêng, link chỉ đường. Bật "Hiện
  trên web" thì có ở mục Ghé cửa hàng cuối trang. Bật "Nhận bánh tại đây" thì
  khách chọn được điểm đó ở bước Tự lấy trong giỏ hàng.
- **Trang và chữ**: mọi câu chữ trên các trang, lọc theo trang và gõ để tìm.
  Để trống một câu là dùng chữ mặc định. Giữ nguyên chỗ trong ngoặc nhọn.
- **Liên hệ**: số điện thoại, email, Zalo, Messenger, Facebook, Instagram,
  TikTok. Đây vẫn là các ô web_* của Vagabond Settings (nguồn từ #367); đổi số
  ở đây là đổi ở đầu trang, chân trang, nút gọi và mọi câu nhắc gọi. Thông tin
  công ty (tên, mã số thuế, địa chỉ đăng ký) chỉ đọc, muốn đổi phải qua kế toán.

Danh sách nào cũng có nhãn trạng thái, công tắc "Hiện trên web" (dòng nhỏ dưới
công tắc nói khách có đang thấy không), nút Sửa và Xoá. Xoá có hỏi lại; bản cũ
vẫn khôi phục được ở Nâng cao, mục Lịch sử xuất bản. Hai người cùng sửa một
mục thì người lưu sau được báo "Có người vừa sửa", không ghi đè.

**Nâng cao** mở bảng theo khối cũ cho ảnh bìa, câu hỏi thường gặp, kênh đặt
hàng, nội dung bánh, chính sách và lịch sử. Bảng này vẫn có Lưu nháp và Xuất
bản riêng; lưu ở các thẻ không cuốn theo phần nháp chưa xuất bản của nó.

## Sửa nội dung chữ (bảng Nâng cao)

Trong **Nhãn và câu chữ**, gõ một phần câu đang thấy trên website để tìm,
hoặc lọc theo Chọn bánh, Giỏ hàng, Đặt bàn, Thành viên, Biên nhận. Sửa cả
headline, nút, hướng dẫn và câu báo lỗi ở đây. Giữ nguyên các chỗ như
{so}, {khung}, {gia_tri_a}; hệ thống tự điền số thực tế. Để trống dùng mặc định.

Trong **Nội dung bánh**, tìm tên hoặc mã, mở từng mã để sửa tên hiển thị,
mô tả, tầng hương, nhãn theo mùa và khẩu phần. Mỗi cỡ là một mã; thẻ danh mục
hiện tên của mã đầu tiên, khi chọn cỡ thì chi tiết hiện chữ của đúng mã đó.
Giá, tồn và mã bán hàng không thay đổi khi sửa chữ.

Câu hỏi thường gặp là loại khối mới. Có thể đổi thứ tự, ẩn/hiện, nhân bản
khối (bản sao ban đầu ẩn) và chỉnh chữ trong từng khối. Headline dùng font
Vagabond Sans gốc; không cần chèn HTML hay định dạng font trong nội dung.

**Hoàn tác/Làm lại** giữ 60 bước trong phiên. **Tải bản đang sửa** tải JSON
để giữ một bản trên máy. Nếu tab còn nội dung chưa lưu khi tải lại, banner
**Mở bản phục hồi** giúp lấy lại. Đây là bản trong tab/trình duyệt hiện tại,
không thay việc Lưu nháp trên máy chủ. Có phiên bản mới từ người khác thì
phải đối chiếu trước; hệ thống chặn ghi đè revision cũ.

Bấm **Lưu nháp** để giữ nội dung riêng. Bấm **Xuất bản** để khách thấy sau
khi tải lại web. Khôi phục lịch sử chỉ đưa vào nháp, cần xuất bản lại.
Preview hiện trang đặt bánh; chữ các trang phụ chỉnh ở nhóm tương ứng,
kiểm trang phụ sau khi xuất bản. Nội dung dạng thẻ HTML được giữ là chữ.

## Ảnh bánh

Ảnh trên web lấy theo thứ tự: ảnh trong hồ sơ món trên ERP, rồi ảnh Pancake,
rồi ảnh nền của tiệm. Muốn đổi ảnh một bánh: Desk, mở món (Item), tải ảnh vào
ô Hình ảnh, lưu. Ảnh phải công khai (không tick "Riêng tư"). Web đổi theo
trong vòng nửa giờ. Bánh nhiều size: tải ảnh ở size nhỏ nhất là đủ.

## Ba trang chính sách

Trong bảng biên tập, mục "Trang chính sách" có ba nút: bảo mật, điều khoản,
giao hàng và đổi trả. Bản nháp anh Việt đã duyệt đã nằm sẵn trong đó.

1. Bấm vào một trang, điền mọi chỗ trong ngoặc vuông, ví dụ [số điện thoại],
   [email], [ngày]. Ô cảnh báo màu vàng đếm số chỗ còn thiếu.
2. Tick "Hiện trang này trên website và chân trang".
3. Bấm Xuất bản. Còn chỗ trong ngoặc vuông thì máy không cho xuất bản và nói
   rõ trang nào còn thiếu.

Chưa xuất bản thì đường dẫn trang đó trả "không tìm thấy" và chân trang không
hiện đường dẫn. Bản tiếng Anh để trống thì trang chỉ có tiếng Việt.

## Cài đặt (anh Việt, Desk, Vagabond Settings)

Mục "Trang đặt bánh và quảng cáo Meta":
- Miễn phí giao từ (đ): mặc định 1.000.000. Để trống hoặc 0 là tắt.
- Số điện thoại, email, Zalo, Messenger, Facebook, Instagram, TikTok cho chân
  trang. Zalo để trống thì dùng zalo.me/<số điện thoại>.
- Webhook nhóm Sales đơn web (Lark): nhận tin khi đơn web quá 30 phút chưa
  vào Pancake.

Mục "Meta Pixel và Conversions API":
- Meta Pixel ID. Để trống thì trang không nạp Pixel, máy không gửi gì.
- Meta CAPI token: ô mật khẩu, chỉ máy chủ đọc, không bao giờ ra trình duyệt.
- Mã sự kiện thử: chỉ điền khi thử trong Events Manager, chạy thật thì xoá.

Sự kiện ghi nhận: PageView, ViewContent (mở chi tiết bánh), AddToCart,
InitiateCheckout (mở giỏ), GuiDon (khách gửi đơn, trình duyệt và máy chủ cùng
event_id), Purchase (chỉ máy chủ, khi hoá đơn của đơn đó được ghi sổ). Giai
đoạn đầu cho quảng cáo tối ưu theo InitiateCheckout rồi GuiDon.

## Sales: đơn web Chờ đối soát

Desk, danh sách "Vagabond Don Web". Chip đỏ Chờ đối soát nghĩa là Pancake mất
phản hồi lúc khách gửi, đơn có thể đã vào Pancake hoặc chưa. Máy tự tìm 5 phút
một lần theo số điện thoại, giờ và món. Quá 30 phút chưa tìm ra thì máy nhắn
nhóm Lark.

Xử lý tay: gọi khách xác nhận. Tìm được đơn bên Pancake thì điền "Mã đơn
Pancake" rồi chọn trạng thái Đã nhận, lưu (yêu cầu hoá đơn công ty tự tạo
theo mã đó). Khách không đặt nữa thì chọn Đã huỷ. Không ai chọn tay được
"Đã ghi sổ": trạng thái đó chỉ đến từ hoá đơn thật.


### Nút nổi đặt hàng và Zalo (PR436)

Trong Các khối nội dung:

- **Mở các kênh đặt hàng**: thay logo nút nổi (mặc định Grab), sửa tên trợ
  năng hoặc tắt cả nút. Website chỉ hiện logo; tên giúp trình đọc màn hình
  nhận biết hành động. Chỉ có một khối cấu hình nút này.
- **GrabFood / ShopeeFood / beFood / XanhSM / Xem tất cả kênh đặt hàng**:
  sửa logo, tên, chữ dự phòng và liên kết HTTPS. Tải logo PNG/JPG/WebP từ máy
  hoặc dán đường dẫn ảnh. Nút lên/xuống đổi thứ tự; Hiển thị khối bật/tắt kênh.
- **Nhắn Zalo**: thay logo, tên, link OA và bật/tắt. Mặc định dùng
  https://zalo.me/thevagabondsaigon theo ảnh anh Việt cung cấp06/10.
- Chữ tiêu đề, lời dẫn, nút đóng và chú thích trong bảng kênh nằm ở
  **Nhãn và câu chữ > Kênh đặt hàng**. Thêm **Kênh đặt hàng** để thêm app.

Logo giữ nguyên tỉ lệ. Thay logo nút nổi không làm đổi logo của từng kênh.
Lưu nháp rồi Xuất bản như nội dung khác. Nút nổi tự ẩn khi mở chi tiết bánh
hoặc thanh toán. Hai khối lời chào/hỗ trợ lặp được ẩn theo duyệt06/10,
chữ vẫn giữ trong Editor và lịch sử để khôi phục khi cần.
