# Issue311 - cập nhật riêng Frappe trong nhánh16

## Quyền và owner
Anh Việt duyệt tiếp ngày14/09: có thể update Frappe; v491 do Claude deploy.
Codex giữ owner khảo sát/bench/tích hợp core. Không deploy trùng v491.

## Bộ phiên bản
- Cloud đọc trực tiếp: Active, Vagabond67fbb50(v491), Frappe16.27.1,
  ERPNext16.28.0. Chưa nhận là đã kiểm nghiệp vụ của đợt Claude deploy.
- Frappe cũ f33ac3f00ab818e21b25ddbec93efb653fd9aa1b; đích16.33.1
  988e54f3c4c291e2077a83809663f123731abe76.
- Giữ ERPNext de591661b9ba0bd3f62ac25b99b5c85c723515f6, không nâng major.
- PR này ghim bench vào bộ đích. Không đổi code ứng dụng/APPVER/patch.

## Kiểm và đối chiếu
- Nguồn: https://github.com/frappe/frappe/releases/tag/v16.33.1
- Diff Document: permission/masked child, chặn run_method tên bắt đầu _,
  đổi hàm follow nội bộ; không thấy đổi thứ tự hooks trong diff đó.
- Diff Database: chỉ xác thực traceID trong đoạn SQL; User đổi email và
  cache mention, chữ ký send_welcome_mail_to_user giữ nguyên.
- safe_exec/làm tròn/jobs đang đối chiếu riêng; APIcompare trả tối đa300tệp,
  không coi danh sách ấy là diff đầy đủ của740commit.
- Cổng dự kiến: migrate2lượt, bộ tích hợp2lượt, hai cửa MInvoice HTTPstub,
  stagingUI và quyền. Không gửi thông báo/OTP/HĐĐT thật.
- Chưa có kết quả bench bộ đích; chưa review tương thích; chưa nâng live.

## Trước phát hành core

Owner thực hiện và khôi phục: Codex. Anh Việt đã cho phép nâng Frappe.
Giữ PR mở đến sát đợt nâng; không đổi bộ core trên main trước khi các cổng
đích đạt. Đây là lựa chọn triển khai trong quyền đã giao, không cần xin lại.

### Phạm vi và phiên bản đã xác minh
- Cloud > Vagabond Private Bench > Sites ngày 14/09 chỉ liệt kê một site:
  `vagabond.s.frappe.cloud`, ID `erpnext-qwy-acq.s.frappe.cloud`, Active.
  Bench đang phục vụ là `bench-44405-000500-f23s`. Kiểm lại danh sách ngay
  trước update; nếu thêm site phải kiểm tương thích và backup site đó trước.
- GitHub ref tag `v16.33.1` trỏ thẳng commit `988e54f` nêu trên.
  `pyproject.toml` tại SHA này yêu cầu Python >=3.14,<3.15;
  `package.json` yêu cầu Node >=24. Khớp runtime CI.
- Đã đọc trực tiếp 69 Server Script đang bật trên site: không có literal
  `frappe.request`, `frappe.local.request`, hoặc `run_method` với tên bắt
  đầu `_`. Đây là tìm literal, không chứng minh mọi tham chiếu động.
- Diff đầy đủ từng tệp `safe_exec.py`, `utils/data.py`,
  `utils/background_jobs.py` đã đối chiếu ở hai SHA: sandbox bỏ `request`,
  rounding đổi epsilon/Decimal, background_jobs không đổi. Python app dùng
  `frappe.request` ngoài sandbox không chịu việc bỏ namespace này.

### Backup và đường quay lại
1. Trước bấm update, lấy backup thủ công tại site > Backups > Take Backup,
   gồm database, public files, private files, config. Chờ Success, ghi ID,
   giờ và dung lượng. Backup lịch 14/09 09:15 đã Success (DB 139.32 MB,
   public 438.71 MB, private 142.66 MB) chỉ là bằng chứng sẵn có, không thay
   backup sát giờ nâng và không được gọi là đã thử restore.
2. Ghi bench cũ, bốn SHA app và site trước nâng. Giữ bản backup Cloud;
   không xoá bench cũ hoặc thư mục backup migration `.migrate`.
3. Chuẩn bị cửa sổ dừng dự kiến 15-30 phút, là dự toán không phải cam kết.
   Chỉ bắt đầu khi backup đầy đủ, bench/review đạt và không có deploy khác.
   Nếu Cloud không cung cấp đường phục hồi đã xác minh thì giữ site hiện
   tại, chưa nâng; không thử restore đè production để chứng minh.
4. Nếu job update thất bại: xem Updates và job phục hồi. Nếu site đã quay
   lại bench cũ, kiểm lại version, migrate và route trước cho thao tác lại.
   Không mặc định mọi lỗi đều tự rollback.
5. Nếu migrate xong nhưng nghiệm thu lỗi: dừng tiếp nhận ghi mới, ghi giờ
   chốt và phát sinh sau backup. Cloud > Backups > menu bản thủ công >
   Restore Backup on another Site trên bench mang bộ SHA cũ để xác minh
   khôi phục trước chuyển lại. Chỉ dùng Restore Backup vào site gốc sau
   khi đã giữ dữ liệu phát sinh và đánh giá mất dữ liệu; không tự ghi đè.
   Nếu không chọn lại được bộ SHA cũ trong Cloud, yêu cầu Frappe Cloud
   support phục hồi bench cũ kèm backup ID, site ID và deploy ID. Không
   checkout core cũ đơn lẻ trên database đã migrate.

Nguồn phục hồi: [backup migration](https://docs.frappe.io/cloud/storage-addons)
và chức năng Restore Backup / Restore Backup on another Site đã thấy trên
Cloud. Chưa chạy thử restore; đây vẫn là cổng phát hành cần hoàn thành.

### Thao tác cập nhật và nghiệm thu
- Fetch Latest Updates, đối chiếu chính xác `988e54f`, chỉ chọn Frappe và
  site trên. Giữ ERPNext `de59166`, Vagabond v491, Email Delivery Service.
  Không chọn Skip failed patches. Nếu SHA đích đổi phải kiểm bộ mới.
- Cloud: build Success và site Updates Migrate Success là hai kết quả.
- System Console: version Frappe 16.33.1, ERPNext 16.28.0; đối chiếu Patch
  Log với trước nâng, không có patch chạy lỗi; scheduler không paused,
  worker hoạt động, ghi số job lỗi trước/sau để phát hiện lỗi mới.
- Mở APP, Lệnh sản xuất, Hóa đơn mua hàng, Phiếu thu/chi và trang đặt bàn:
  mỗi màn tải được, không traceback; so số đếm cùng bộ lọc trước/sau,
  không lấy số cũ từ nhật ký làm chuẩn hiện tại.
- Bench đích: migrate 2 lượt, tích hợp 2 lượt, hai đường M-Invoice có HTTP
  stub, staging UI/quyền và ca kéo Pancake giả lập đều phải đạt. Ghi số ca
  thực tế từ artifact. Không phát hành HĐĐT hoặc kéo đơn thật để thử.
- Sau live: tra trạng thái tác vụ Pancake/M-Invoice và lỗi mới theo mốc nâng,
  không gửi hoá đơn/OTP/thông báo thử. Nếu chưa có giao dịch tự nhiên thì
  ghi giới hạn này, không nhận UAT đã xong.
