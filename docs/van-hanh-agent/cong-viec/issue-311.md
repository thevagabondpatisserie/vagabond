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
Xác minh backup DB/files hoàn tất và đường khôi phục, không chỉ thấy tên.
Mời Claude review trên SHA thử, chỉ update Frappe sau đủ cổng. Trên Cloud
FetchLatestUpdates, đối chiếu đúng988e54f, chọn riêng Frappe và site, không
skip patch lỗi. Nếu đích thay đổi thì dừng và kiểm lại, không lấylatestmù.
Sau update: phiên bản, migrate, scheduler/worker, các route nghiệp vụ.
Khôi phục phải gồm DB/files cùng bảncode cũ, không chỉ checkout core cũ.
