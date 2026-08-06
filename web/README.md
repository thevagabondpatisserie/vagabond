# Thư mục web

Mã nguồn các màn hình chạy bằng Web Page của Frappe. Các tệp ở đây là **bản sao để đối chiếu và khôi phục**, không tự động deploy - Frappe vẫn đọc từ bản ghi Web Page trong database.

| Tệp | Web Page | Đường dẫn |
|---|---|---|
| `banh.html` | `banh-vagabond-ban-mau` (trường `main_section_html`) | `order.thevagabondpatisserie.com` |
| `app_nhom_xuat_kho.js` | `màn-hình-nghiệp-vụ` (trường `javascript`) | `app.thevagabondpatisserie.com/bep` |

## Quy tắc

Sửa Web Page xong thì cập nhật tệp ở đây trong cùng ngày. Trước khi vá phải đọc bản ghi ngay trước đó, vá xong đọc lại so bằng SHA-256 - đã có lần hai phiên cùng sửa một Web Page và nuốt mất phần vừa vá của nhau.

## Bẫy: tiện ích trình duyệt chèn rác vào nội dung

Ngày 06/08/2026 phát hiện `main_section_html` đang chứa hai thẻ `<script src="//local.adguard.org?...">` do tiện ích chặn quảng cáo trên máy người sửa chèn vào, rồi bị lưu thẳng vào database. Khách vào trang sẽ tải hai đường dẫn chết đó. Đã gỡ.

Khi lấy nội dung Web Page ra để lưu, luôn lọc lại:

```
<script[^>]*local\.adguard\.org[^>]*></script>
```

và kiểm SHA-256 của tệp so với nội dung trong database trước khi commit.
