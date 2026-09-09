# Issue #249: email mobile và thông báo sau phát hành

## Nguyên nhân và cách sửa

`thu_khung.khung_thuan` trước đây đặt `width="600"` và `width:600px` cho
mọi hộp thư. Trên điện thoại 320/375/390px, cả lá thư vượt màn hình. Khung
chung nay rộng 100%, tối đa 600px; chỉ Outlook Word dùng bảng cố định qua
conditional comment. Ảnh logo co theo bảng, giữ tài sản và màu branding cũ.

`cap` có nhãn nowrap, `bang` có tổng tiền nowrap, các bảng để auto layout:
mã dài vẫn có thể đẩy khung rộng ra dù đã sửa bảng ngoài. Nay bảng fixed
layout, chữ được xuống dòng, không cắt hoặc giấu nội dung. Padding ngang
20px và nút toàn chiều rộng giúp màn hẹp vẫn đọc và chạm được.

Không đổi đường gửi, sender, người nhận, nội dung nghiệp vụ hoặc chứng từ.
Mẫu sửa chỉ áp dụng email tạo sau khi phát hành, không sửa thư đã gửi.

## Kiểm có thể chạy lại

```sh
python3 scripts/dung_mau_email.py /tmp/mau-email
node scripts/kiem_email_mobile.cjs /tmp/mau-email
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```

Phép browser cần Playwright có sẵn (`PLAYWRIGHT_MODULE` nếu không ở node_modules)
và Chromium hoặc `CHROME_BIN` trỏ executable. Không cần site hay gửi thư.
Bộ kiểm có 14 mẫu sẵn và 1 ca chuỗi dài, tại 320/375/390/600/1024px.
Bản sửa đạt 75/75; mẫu cũ trên nền v460 hỏng 61/75 bằng cùng bộ kiểm.
Có thêm kiểm bản nháp v460 tại 5 độ rộng. Browser không thay kiểm Outlook.

Cổng local đạt 2706 ca, rc 0, bundle khớp từng byte. Đã đồng bộ nền main
46c1eeb (v461), bản đề xuất v462 giữ đủ patches v459/v460/v461.
Review chéo nội bộ không thấy blocker; đã sửa hai điểm tài liệu về trạng
thái Email Queue Sent và đường dẫn lệnh. Chưa phải review của Claude.

## Skill và phạm vi tự động

`.agents/skills/vagabond-email-phat-hanh/SKILL.md` dùng chung cho Codex/Claude,
được gọi từ AGENTS sau xác minh deploy. Script đi kèm chỉ soạn HTML/TXT.
Mặc định nháp tới khi có quyền gửi. Không thêm cron, hook migrate gửi thư,
mailing list hay đường SMTP. Skill yêu cầu danh sách nhân sự thật đang hoạt
động theo phạm vi tính năng, tránh gửi lặp và không tự đoán địa chỉ email.

## Claude kiểm tiếp trước phát hành

- Rà đúng SHA cuối, CI/gate và xác nhận không đổi cấu hình email.
- Kiểm HTML thực tế qua đường gửi Frappe trên bench và mẫu trên Outlook
  điện thoại/desktop, Gmail nếu có. Chỉ gửi mẫu khi có quyền gửi tới địa chỉ
  thử; không dùng khách/nhà cung cấp hoặc nhân sự thật làm ca kiểm.
- Sau phát hành, xác minh SHA/Patch Log/APPVER và mẫu email dựng từ site.
  Skill soạn thông báo theo bản thực đã lên, đúng quyền gửi được giao.
- Chưa có bằng chứng Outlook thật thì ghi rõ giới hạn; không coi 75 browser
  cases là chứng nhận tương thích mọi email client.
