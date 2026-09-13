# Issue 301: thông tin đặt bàn và Lark FOH

Owner Codex; nhánh codex/301-dat-ban-foh, xếp trên PR 309.
Chốt vòng3 comment5651587556 thay bản đầu issue: chỉ thêm dip, khu_vuc,
tre_em, email, banh_kem_theo. Không thêm số điện thoại phụ, dị ứng, kênh liên hệ.
Anh Việt giao code/review, gom chờ deploy sau v489; chưa merge/deploy.

## Code và nguồn

- Form dùng nen.css từ #300. Khu vực và dịp đọc từ máy chủ, giữ payload/khóa
  qua mất phản hồi, khoá mọi chip khi đang chờ. Một cấu hình nhận một cơ sở;
  chip cơ sở là nhãn chỉ đọc, không hứa hỗ trợ nhiều cơ sở cùng lúc.
- chuan_hoa kiểm lựa chọn, số trẻ, email/độ dài; validate giữ thông tin khách
  bất biến sau tạo. Nhân viên ghi thay đổi vào ghi chú xử lý.
- after_insert riêng Vagabond Dat Ban đăng ký callback sau commit, callback
  xếp worker qua frappe.enqueue. Core Frappe utils/background_jobs.py hoãn
  enqueue_call; utils.CallbackManager.run không bắt lỗi. Bao tại callback
  để Redis lỗi không đổi kết quả khách sau khi phiếu đã lưu. Chỉ khi lỗi
  callback mới commit giao dịch Error Log, sau commit phiếu đã kết thúc.
- gui_thu.ban_webhook dùng URL riêng khi được truyền, URL trống không rơi
  sang nhóm quản trị. Kiểm HTTP và mã Lark, không log URL/bí mật.
- Patch dat_ban_foh_301 seed ba khu khi trống, không đè cấu hình. v490 có
  dòng đồng bộ cấu trúc; bộ ghép app tạo bundle. Số490 cần đối chiếu lại nếu
  phiên khác phát hành trước. Giữ thứ tự PR309 trước PR này khi gộp main.

## Kiểm

Code tích hợp 3355546e98a550e5bd740732fe349a749d91c16a gồm delta review #309.
Cổng kiem_truoc_deploy.sh chạy trong môi trường chặn requests, 2974 ca đạt;
27 ca bên cổng con đạt. Bốn mutation đều bị bắt: bỏ giới hạn trẻ, wildcard
hook, ép webhook quản trị và in dòng rỗng. Node chạy form thật qua DOM giả,
kiểm năm ô, chip từ cấu hình, lỗi mạng và cùng payload/khóa khi gửi lại.
Chrome headless qua HTTP local390px đã xem toàn form, không tràn ngang.
Không gửi Lark/OTP thật, chưa kiểm Frappe bench/migrate/site production.

## Còn lại

Claude review logic callback/giao dịch Error Log, schema, retry và hồi quy
sender cũ. Kiểm migration trên bench/CI; sau deploy kiểm form thật390px và
nhóm Lark thử được quản lý cấu hình. Chưa có biên nhận Lark thật.
Phiên cloud trước chỉ báo local commit, không có nhánh remote; không lấy
những biên nhận đó làm bằng chứng phiên bản đã lên repo hoặc site.
