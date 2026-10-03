# Issue420: đối soát vendor

- Issue: https://github.com/thevagabondpatisserie/vagabond/issues/420
- Owner: Codex, nhánh `codex/doi-soat-vendor`. Claude review độc lập.
- Anh Việt duyệt maquette 03/10/2026, yêu cầu đưa PR và cùng hoàn thiện để merge.
- Base lúc dựng: `403cb217` (main v557); code đã kiểm:
  `dca3ce509648062ea0cf16545ea26a3e3a78992c`.
- Tài liệu đầy đủ: [thiết kế và maquette](../../doi-soat-vendor/README.md).

## Có bằng chứng

Module thuần `doi_soat_nguon.py`: đọc tiền Decimal theo locale rõ, giữ mã gốc,
kiểm phạm vi/kỳ/dấu/tổng/số dòng, nhận biết sự kiện trùng hoặc thay nội dung;
giữ lỗi cả nhóm trùng để không nhận bản đầu qua nút nhận phần hợp lệ.
Không có API/ghi DB/hook/lịch/UI runtime hoặc adapter đọc file ở vòng này.

- 46/46 ca tập trung đạt; đã gắn vào `khung/kiem_thu/chay.py`.
- `dung_app_bep.py --kiem`: khớp từng byte.
- `kiem_truoc_deploy.sh`: exit0; tầng khung 3908/3908, các cổng tiếp theo đạt.
  Lượt đầu thiếu Node trong PATH nên dừng đúng; chạy lại bằng runtime bundled
  Node/Python. Không sửa cổng hoặc bỏ ca.
- Toàn bộ fixture là giả. Không đưa file vendor/email cá nhân vào Git.
- Maquette đã render ở phiên duyệt, không phải kiểm UI ERP sau triển khai.

## Còn lại và bàn giao

Trạng thái: triển khai vòng đầu, chưa đủ merge toàn luồng. Push/CI/review xem
trực tiếp trên PR theo HEAD; bench/merge/deploy/migrate/live chưa thực hiện.
Không coi 46 ca thuần là bằng chứng khóa DB, phân bổ hoặc lưu nguồn thành công.

Claude cần review: (1) persistence dùng core nào để giữ nguồn, phiên bản và
ngoại lệ; (2) hợp đồng tiền, ID sự kiện, kỳ; (3) luồng thao tác và quyền;
(4) bổ sung ca biên/ranh giới tiếp theo. Workflow Claude đang là read-only
review; gửi đề xuất/diff trong findings, Codex tích hợp, không nhận rằng bot
đã có quyền tự push vào file Codex đang claim.

Codex làm tiếp các checkbox trong spec: persistence + adapter, hai đường
email/tải tay, UI, gợi ý nối và bench trên SHA cuối. Không mở thêm PR con khi
phạm vi vẫn thuộc đầu mối này. Không kích hoạt email/lịch hoặc giao dịch thật
để chứng minh thiết kế. Chỉ phát hành sau review độc lập và đủ cổng.

Model/effort thực tế và token provider: chưa có metadata xác minh. Không
giả nhận đã dùng model theo tên trong instruction. Số lượt review bắt đầu:
xem GitHub Actions; không suy từ số comment được đăng.
