---
name: vagabond-email-phat-hanh
description: Soạn email thông báo nội bộ sau mỗi lần deploy Vagabond thành công và đã kiểm site thật. Dùng khi kết thúc phát hành, viết release email, hoặc sửa mẫu email branding trên desktop và mobile. Tự thực hiện bước soạn, không chờ anh Việt nhắc lại.
---

# Email sau phát hành Vagabond

Anh Việt yêu cầu ngày 09/09/2026: sau mỗi deploy thành công, soạn email tính
năng mới thật đơn giản, xưng "hệ thống", cho đúng nhân sự liên quan. Giữ bộ
nhận diện do anh Việt và Claude đã thiết kế. Đây là bước của người phụ trách
phát hành, không phải cron hay lời hứa rằng một skill tự chạy khi không có phiên.

## Khi nào soạn

- Chốt bản thực sự đã lên site: SHA, phiên bản, Cloud Success, migrate/Patch
  Log và kiểm live liên quan. CI xanh hoặc merge chưa đủ. Báo cáo của người
  khác phải ghi nguồn trong bàn giao kỹ thuật, không nhận là tự kiểm.
- Đọc diff và bằng chứng của chính bản phát hành. Chỉ kể tính năng đã chạy;
  không đưa việc đang mở, ý tưởng, ca kiểm mô phỏng thành tính năng có thật.
- Nếu deploy hỏng hoặc phải rollback, cập nhật bản nháp theo trạng thái cuối;
  không gửi thông báo tính năng đã sẵn sàng.

## Người nhận và quyền gửi

- Tự soạn HTML, bản chữ và danh sách nhóm cần nhận sau mỗi lần đủ bằng chứng.
  Mặc định lưu nháp. Nếu anh Việt đã cho phép tự gửi cho nhóm liên quan trong
  phiên/quy ước hiện hành thì thực hiện theo quyền đó, không hỏi lại từng lần.
- Đọc danh sách nhân sự/tài khoản đang hoạt động và địa chỉ nội bộ đã khai;
  đối chiếu bộ phận với tính năng. Bán hàng/vận đơn: Sales và điều phối;
  hoá đơn/thuế: kế toán; sản xuất/kho: bếp và kho; thêm quản lý trực tiếp khi
  liên quan. Không mặc định gửi toàn công ty, khách hoặc nhà cung cấp.
- Không đoán email từ tên người. Thiếu danh sách thật thì ghi nhóm dự kiến và
  phần còn thiếu, vẫn hoàn tất bản nháp. Không tự tạo mailing list công khai.
- Trước gửi, đối chiếu lịch sử Communication/Email Queue và nhật ký phát hành
  theo site, SHA/bản phát hành, chủ đề và từng người nhận. Đã gửi/đang đợi thì
  không gửi lặp. Mất phản hồi không có nghĩa là chưa gửi; đọc lại trước retry.
- Dùng đường gửi ERP hiện có, đọc `vagabond/gui_thu.py` và cấu hình sender đang
  chạy trước khi gọi. Không tự tạo SMTP, sửa Email Account hoặc gửi trong patch.
  Chỉ báo "đã gửi" theo bằng chứng hàng đợi; không nhận là người nhận đã đọc.

## Viết sao cho người nhận hiểu ngay

Tiêu đề: "[ERP Vagabond] Cập nhật ngày dd/mm: <việc có ích>".
Mở đầu: "Hệ thống đã cập nhật ... Anh chị có thể ...".
Mỗi ý nói: việc gì đã thay đổi, ai dùng, thao tác tiếp theo nếu có. Dùng tên
màn/nút thật đã kiểm. Tối đa 3-5 ý ngắn, một nút mở app. Không xưng em/Claude/
Codex, không PR/SHA/patch/SQL/fixture trong email cho nhân viên. Không khẳng
định "mọi lỗi đã hết". Nếu giới hạn ảnh hưởng thao tác, nói rõ bằng lời dễ hiểu.
Chỉ dùng dấu gạch ngang thường. Không đưa dữ liệu khách, tiền hoặc chứng từ
thật vào thông báo chung nếu người nhận không cần biết.

## Dựng đúng mẫu và kiểm hiển thị

- Dùng `vagabond.thu_khung.khung_thuan` hoặc `khung`, chân `nhan_vien`, cùng
  logo `images/thu/dau.png`, bảng màu và các helper có sẵn. Không vẽ branding
  mới. Ảnh email thật phải có URL tuyệt đối của site đã xác minh.
- Script `scripts/soan_thu.py` nhận JSON nội dung và xuất HTML + TXT, chỉ lưu
  tệp, không gửi. Chạy từ checkout repo; xem `--help` để biết dữ liệu đầu vào.
- Khung rộng 100%, tối đa 600px; ảnh co theo khung; bảng/URL/mã dài xuống dòng.
  Không dùng overflow:hidden để che nội dung, không thu nhỏ cả lá thư thành ảnh.
- Kiểm ít nhất 320/375/390px và desktop 600/1024px, cả mã dài, URL và bảng tiền.
  Dùng `scripts/kiem_email_mobile.cjs` ở gốc repo sau khi dựng bộ preview bằng
  `scripts/dung_mau_email.py`. Browser chỉ kiểm bố cục, không thay hộp thư thật.
- Trước phát hành mẫu sửa, kiểm thư mẫu trên Outlook mobile và desktop/Gmail
  khi có quyền gửi mẫu. Thiếu kiểm này phải ghi rõ, không tự nhận đã đạt.
  Thư đã gửi trước đây không sửa ngược được; mẫu mới áp dụng thư gửi sau deploy.

## Bàn giao

Lưu HTML/TXT, nhóm và địa chỉ đã xác minh (nội bộ, không commit lên repo),
trạng thái nháp/đợi/gửi/lỗi, bằng chứng deploy và chống gửi lặp trong nhật ký
phát hành. Đưa link preview cho anh Việt. Luôn kèm prompt Claude chứa PR,
SHA thật, kiểm đã chạy, kiểm hộp thư còn thiếu và bước được phép làm tiếp.
