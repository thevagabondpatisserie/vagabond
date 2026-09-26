# Issue 367: trang đặt bánh đủ điều kiện chạy quảng cáo Meta (PR1)

- Nguồn: issue #367, sáu điểm Claude chốt 24/09, quyết định phí giao của anh
  Việt 24/09, ba bản nháp chính sách anh Việt duyệt 25/09, mục 8 lối đăng nhập.
- Owner: Claude implement (anh Việt giao 25/09: "làm PR 367 thật triệt để, cho
  Codex review"). Codex review. Nhánh `v529-don-web-367`, nền main 6b9922b.
- Công của Codex ở c59e139f, 0d69cac3, 88b8699d, d122f410 KHÔNG có trên GitHub
  (Codex Cloud không đẩy được), nên dựng lại từ main theo đặc tả trên issue.

## Đã làm, kèm bằng chứng

- Bản ghi bền `Vagabond Don Web` ghi và commit TRƯỚC khi gọi Pancake; chống
  trùng 15 phút theo khoá (SĐT, món, giờ nhận, nonce) có khoá tệp; Pancake mất
  phản hồi hay 5xx là Chờ đối soát, 4xx là từ chối, không bao giờ tự gửi lại.
- Token biên nhận 32 byte HMAC(khoá site, muối bản ghi, nonce), CSDL chỉ giữ
  băm; gửi trùng ra đúng đường dẫn cũ. event_id GuiDon và Purchase là uuid riêng.
- Tiền bánh máy chủ tính theo giá hồ sơ món; ngưỡng miễn phí trong Settings;
  tách phí khách trả và phí Ahamove; bốn trạng thái phí; Ahamove lỗi không thành 0.
- Trang /banh/xong/<token>: no-store, no-referrer, noindex, 404 thật khi token
  sai, tên viết tắt, không SĐT/địa chỉ/email; JS gỡ token trước khi nạp Pixel.
- CAPI: GuiDon sau khi lưu, Purchase ở hook on_submit Sales Invoice (khớp mã
  Pancake), hàng đợi, thử lại 3 lần, lỗi chỉ Error Log không token.
- Nhịp 5 phút ghép đơn Chờ đối soát với Pancake (đúng một đơn khớp SĐT, giờ,
  món); quá 30 phút báo nhóm Sales qua Lark (anh Việt chọn Lark 25/09).
- Ba trang chính sách trong Vagabond Noi Dung Web, patch gieo nháp nguyên văn,
  Marketing Studio sửa và bật hiện, chặn xuất bản còn ngoặc vuông, trang công
  khai qua sanitize_html bắt buộc, chưa xuất bản thì 404.
- Chân trang pháp nhân (HTML tĩnh), ô đồng ý, Pixel bốn mốc, phí giao dự kiến
  theo khu vực, số thứ tự lần hỏi phí, nút "+", ảnh ERP trước Pancake ở cả bốn
  nhánh qua `anh_web.chon_anh`, phông thường cho chữ Việt và số.
- Mục 8: gốc thật là tên mô đun `bien-tap-web.py` (Frappe chỉ tìm
  `bien_tap_web.py`), đo trên site: csrf-token mang nguyên văn `{{ csrf_token }}`.
  Đổi tên, thêm chuyển hướng đăng nhập, trang báo quyền, nút Đăng xuất.

Kiểm: bộ khung (chay.py -im), dung_app_bep --kiem, kiem_truoc_deploy.sh, giả lập
CI không requests; đột biến 20 trên 20; ảnh 320/375/390 từ tệp repo với API
giả (không phải site thật). Số liệu cụ thể ở comment bàn giao trên PR.

## Còn lại và bàn giao

- Chưa chạy bench `vagabond.khung.kiem_that.cua.chay` (ca mới
  `kiem_that/thu_don_web_367.py`), chưa kiểm site thật, chưa merge, chưa deploy.
- /dat-ban và /thanh-vien cùng lỗi tên mô đun có gạch nối, ngoài phạm vi, chưa đổi.
- Toạ độ tâm khu vực là số gần đúng, chỉ dùng cho phí dự kiến.
- Marketing phải điền chỗ trống và xuất bản ba trang chính sách, anh Việt điền
  Pixel ID, token CAPI, email, webhook Lark trước khi chạy quảng cáo.
- PR2 (trang từng bánh, Open Graph, Meta Catalog) chưa làm.

## Vòng 2 (25/09/2026, Claude sửa theo rà soát Codex trên b03e43a)

- Ba trang chính sách 404: Frappe không truyền `defaults` của
  `website_route_rules` vào `form_dict`. Bỏ `defaults`, thêm
  `noi_dung_web.khoa_tu_duong(duong)` thuần, `www/chinh_sach.py` suy khoá từ
  `frappe.local.request.path` (dự phòng `frappe.local.path`); đường lạ hay
  chưa xuất bản vẫn 404. Ca mới nhóm J.
- `_bao_sales` chỉ đóng dấu `da_bao_sales_luc` SAU khi Lark trả nhận; thiếu
  URL hay gửi hỏng thì để trống để nhịp sau thử lại, có Error Log. Ca mới nhóm H.
- Nhịp `doi_soat_tu_dong` tách `_doi_soat_mot(r, dons, gan)`, mỗi bản ghi
  một `try` riêng, lỗi thì rollback và ghi log, bản ghi sau vẫn chạy. Ca mới nhóm H.
- `ghep_don_pancake` bỏ đơn Pancake trạng thái 6, 7 (huỷ, xoá), cùng luật
  với `kiem_banh` và `mua_vu`. Ca nhóm H mở rộng.
- Bench `kiem_that/thu_don_web_367.py`: tự gieo Item bánh có giá khi site CI
  trống (bench đỏ run 36148002675), tắt cờ `vagabond_kiem_that` trong
  `try/finally` quanh `khi_ghi_so_hoa_don` để hook thật chạy.
- Không đổi APPVER (vẫn 529, chưa phát hành), không thêm patch.
