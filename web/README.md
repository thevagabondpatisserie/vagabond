# Thư mục web (ĐÃ CHUYỂN, giữ lại để không đứt đường dẫn cũ)

Từ **v288 (23/08/2026)** mã nguồn Web Page nằm ở `vagabond/trang/`, và mỗi
lần Migrate máy tự đẩy xuống cơ sở dữ liệu. Đọc `vagabond/trang/__init__.py`.

Thư mục này trước đây là **bản sao chép tay để đối chiếu**, không tự deploy.
Cách đó có một lỗ hổng đã lộ ra: bản sao dễ cũ hơn bản trên site mà không ai
biết, vì không có gì bắt buộc phải cập nhật nó.

| Tệp cũ | Nay nằm ở |
|---|---|
| `banh.html` | `vagabond/trang/banh.html` |
| `app_nhom_xuat_kho.js` | không còn dùng, xem bên dưới |

`app_nhom_xuat_kho.js` là bản chép tay của trường `javascript` trang `bep`
từ thời trang đó còn dán nguyên mã app. Nay trang `bep` chỉ còn đoạn nạp
`app_bep.js` dài 737 byte, nằm ở `vagabond/trang/bep.js`. Tệp cũ giữ lại làm
tư liệu, KHÔNG được đẩy lên site.

## Bẫy vẫn còn nguyên giá trị: tiện ích trình duyệt chèn rác

Ngày 06/08/2026 phát hiện `main_section_html` đang chứa hai thẻ
`<script src="//local.adguard.org?...">` do tiện ích chặn quảng cáo trên máy
người sửa chèn vào, rồi bị lưu thẳng vào database. Khách vào trang sẽ tải hai
đường dẫn chết đó.

`vagabond/trang/loc_rac()` nay lọc đúng mẫu này mỗi lần đẩy xuống, và có ca
kiểm thử canh. Không phải nhớ bằng tay nữa.
