# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo này là gì

App Frappe/ERPNext tên `vagabond` của The Vagabond Pâtisserie (tiệm bánh tại TP.HCM): cổng đặt bánh online cho khách và app nghiệp vụ nội bộ (bếp, kho, vận đơn, bán hàng). App nối Frappe với các dịch vụ ngoài mà Server Script trên Frappe Cloud không gọi được: Pancake POS, Goong (bản đồ), Ahamove (giao hàng), Zalo ZNS (OTP và tin thanh toán), m-invoice (hóa đơn điện tử), VietQR, WhatsApp Cloud API.

Mọi khóa API nằm trong single doctype **Vagabond Settings** (trường kiểu Password, Frappe mã hóa khi lưu). Khóa không bao giờ ra trình duyệt.

## Lệnh phát triển

Repo không có test suite, không có linter, không có build frontend. Đây là app Frappe chuẩn, chạy trong một bench:

    bench get-app https://github.com/thevagabondpatisserie/vagabond
    bench --site <ten-site> install-app vagabond
    bench --site <ten-site> migrate        # chạy patches.txt sau khi đổi doctype/patch
    bench build --app vagabond             # khi sửa file trong vagabond/public/
    bench --site <ten-site> clear-cache

Trên production (Frappe Cloud): push lên `main` rồi deploy qua dashboard Frappe Cloud. Patch khai trong `vagabond/patches.txt` (mục `[post_model_sync]`); muốn chạy lại một patch thì thêm dòng trùng kèm comment `#chay lai <ngay>`.

## Kiến trúc

### Backend: module phẳng theo nghiệp vụ

Toàn bộ logic nằm ở các module phẳng `vagabond/*.py`, mỗi file một nghiệp vụ, tên tiếng Việt không dấu. Endpoint là hàm `@frappe.whitelist()` ngay trong module, không khai báo thêm ở `hooks.py`. Các module chính:

- `lib.py` - tiện ích dùng chung: `cfg()` đọc Vagabond Settings, `key()` đọc trường Password, `cache_get/cache_set`, hằng URL các API ngoài, hook đổi og:image theo tên miền (order.* và app.* trỏ chung một site)
- `api.py`, `dia_chi.py`, `giao_hang.py` - endpoint mở cho khách vãng lai (tra khách cũ Pancake, gợi ý địa chỉ Goong, phí giao Ahamove), đều có `rate_limit` vì mỗi lượt gọi tốn tiền thật
- `don_hang.py` - tạo đơn thật bên Pancake từ trang đặt bánh; không tin bất kỳ con số nào trình duyệt gửi lên, phí giao tính lại ở máy chủ
- `ban_hang.py` (lớn nhất) - doanh số ngày từ Pancake thành Sales Invoice, xuất hóa đơn điện tử m-invoice, tính tiền tại quầy, SePay
- `kiem_banh.py` - kiểm bánh ngày: đếm đơn Pancake tự động thay bảng ghi tay
- `van_don.py`, `xep_tuyen.py` - vận đơn giao bánh và xếp tuyến (cheapest insertion cho VRPTW)
- `dang_nhap.py`, `zalo.py` - đăng nhập khách bằng số điện thoại + OTP qua Zalo ZNS
- `thanh_toan.py` - link thanh toán QR gửi khách sau khi sales chốt đơn
- `pancake_sp.py`, `pancake_admin.py`, `doi_soat.py` - đẩy mã hàng sang Pancake, dọn danh mục, đối soát mã

Doctype riêng nằm ở `vagabond/vagabond/doctype/` (van_don, kiem_banh_ngay, vagabond_settings, vagabond_otp, hop_dong_ban_hang...).

`hooks.py` khai: cron đồng bộ (kéo đơn Pancake 5 phút một lần, doanh số 30 phút, xuất hóa đơn điện tử bù hằng giờ, dọn dẹp ban đêm), doc_events trên Sales Invoice (chặn trùng mã Pancake, trả số kiểm bánh khi hủy/xóa), và override class User (`nhan_su.NguoiDung` đổi thư mời nhân viên).

### Frontend: không có build system, ba nơi chứa mã

1. **`vagabond/public/js/app_bep.js`** - app nghiệp vụ mobile (một file vanilla JS duy nhất, CSS nhúng trong chuỗi), phục vụ tại `/assets/vagabond/js/app_bep.js`. Đây là BẢN SỐNG, được version qua commit message dạng "App vNN: ...". File `app_bep.js` ở gốc repo là bản upload cũ ngày 08/08/2026, KHÔNG sửa file đó.
2. **`web/`** - bản sao để đối chiếu và khôi phục của các Web Page trong database (`banh.html` trang đặt bánh, `thanh-toan.html` trang QR route `tt`, `app_nhom_xuat_kho.js` màn nghiệp vụ). Frappe đọc từ bản ghi Web Page, KHÔNG tự deploy từ thư mục này. Đọc `web/README.md` trước khi đụng vào: sửa Web Page xong phải cập nhật tệp cùng ngày, so SHA-256 trước và sau khi vá (đã có lần hai phiên nuốt mất phần vá của nhau), và lọc rác `<script src="//local.adguard.org...">` do tiện ích trình duyệt chèn vào.
3. **Ảnh** ở `vagabond/public/images/`, tham chiếu qua `/assets/vagabond/images/...`.

## Quy ước bắt buộc

- **Tiếng Việt mọi nơi**: tên file, tên hàm, tên doctype viết tiếng Việt không dấu; docstring, comment và commit message viết tiếng Việt (commit message không dấu theo lịch sử hiện có).
- **Không dùng dấu em dash (—) và en dash (–)** trong mọi văn bản, chỉ dùng gạch ngang thường "-" (quy ước anh Viet 25/07/2026).
- **Comment ghi quyết định nghiệp vụ kèm ngày chốt** (ví dụ "anh Viet chốt 01/08/2026") và số liệu đo thật. Đây là nguồn sự thật về nghiệp vụ của tiệm - giữ nguyên phong cách này khi thêm code, đừng xóa các ghi chú đó khi refactor.
- Python indent bằng tab (chuẩn Frappe).

## Luật nghiệp vụ đã chốt, không được phá

- **Một đơn Pancake = một Sales Invoice.** Chốt bằng khóa duy nhất `ux_vgb_pancake_id` dưới database (xem `khoa_ma_pancake.py` - kiểm tra trong code không chặn được hai request song song).
- **Một đơn hàng = một hóa đơn VAT.** Tuyệt đối không gộp nhiều đơn thành một hóa đơn, kể cả gộp cuối ngày (luật kế toán, chốt 02/08/2026).
- **Bộ mã hàng trên ERPNext là bộ chuẩn**; Pancake, Grab... phải chỉnh theo Next, không sửa ngược.
- **Mã QR thanh toán lấy từ Pancake, không tự sinh** - MB cấp mỗi đơn một số tài khoản ảo riêng để tự đối soát; tự sinh QR là mất đối soát tự động.
- **Endpoint mở phải tự lọc lại dữ liệu**: `tra_khach` chỉ trả địa chỉ khớp đúng số điện thoại vừa tra, vì Pancake tìm lỏng tay trả cả khách khác. Endpoint mở luôn có rate limit, và khi chưa điền khóa thì trả `ly_do: chua_dien_khoa_...` chứ không lỗi 500.
- **Người đếm và người ghi sổ không được là một**: kiểm kê và xuất hủy chỉ tạo bản nháp, quản lý duyệt mới trừ tồn (xuất điều chuyển nội bộ thì ghi sổ ngay).
- **Phí Ahamove đổi theo giờ** - luôn truyền `order_time` là lúc khách muốn nhận bánh, không để 0.
- Gửi tin nhắn: **luôn Zalo ZNS trước**, chỉ dùng WhatsApp khi được yêu cầu rõ hoặc Zalo từ chối.
