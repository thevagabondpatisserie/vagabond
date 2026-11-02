# Đề xuất: bánh Thiết kế riêng và kênh Bánh sỉ trên web (02/11/2026)

Bản đề xuất để Codex góp ý TRƯỚC khi viết code. Chưa có dòng code nào.

## Tóm tắt cho anh Việt

- Vấn đề: tiệm có bánh thiết kế riêng (Croquembouche, bánh cưới) và khách sỉ (quán, khách sạn) nhưng web chưa nhận được hai loại đơn này; Sales đang nhận tay qua Zalo.
- Việc làm: hai tab mới trên trang đặt bánh bản Vue (bản khách đang dùng): "Thiết kế riêng" (đặt cọc 50% qua QR) và "Bánh sỉ" (đăng ký, đăng nhập, đặt theo giá riêng, trả trước hoặc công nợ 15 ngày).
- Kết quả sẽ thấy: khách tự đặt, tự cọc; Sales và bếp nhận tin Zalo khi có đơn và khi tiền về; đơn vào app như đơn web hiện nay.
- Anh đã chốt (02/11): giá web đã gồm thuế; thiết kế riêng cọc 50%, đặt trước ít nhất 7 ngày; dùng CHUNG một mã món "Bánh thiết kế riêng" (BAEV00001), hoá đơn kèm đơn hàng chi tiết, bảng kê; sỉ giao sau 3 ngày kể từ ngày đặt; giá RIÊNG từng khách; công nợ do Sales duyệt từng khách, kỳ 15 ngày.

## Dữ liệu site thật đã đọc (02/11/2026, chỉ đọc)

- `Vagabond Settings.web_ban_vue = 1`: khách dùng trang Vue, chỉ dựng ở `public/web_vue/banh`.
- Mã chung có sẵn: BAEV00001 "Bánh thiết kế riêng" (Event - Catering, đơn vị Món, giá chuẩn 0, đang bật, là hàng bán).
- Price List bán: Standard Selling, Bán tại tiệm. Customer Group "Khách sỉ B2B" chưa gắn bảng giá. Chưa có Payment Terms Template.

## Phần 1: Thiết kế riêng (một PR, làm trước)

### Danh mục tác phẩm
- Khối nội dung mới loại `thiet_ke_rieng` trong `noi_dung_web` (thêm vào `LOAI`, `VI_TRI`, `LOAI_MUC`), Marketing sửa ở trình biên tập theo thẻ như Tiệc: tên, ảnh, câu chuyện, "bánh gồm gì", danh sách size (tên, mô tả kích thước, giá đã gồm VAT), danh sách trang trí (tên, giá cộng thêm, có thể 0), số ngày đặt trước tối thiểu (mặc định 7, không nhận dưới 7).
- Giá là đầu vào người gõ tay: `chuan_hoa` kiểm số nguyên dương, có trần, size không trùng tên.
- Tab Vue "Thiết kế riêng" đọc khối này qua `cong_khai()` như Ưu đãi, Tiệc.

### Đặt và cọc
- Cửa mới `thiet_ke_rieng.dat(du_lieu)` (allow_guest, POST, có giới hạn lượt như `tiec_web.dang_ky`). Máy chủ tự tính lại giá từ khối đã xuất bản theo mã tác phẩm, mã size, mã trang trí; KHÔNG nhận giá từ máy khách.
- Chặn ở cửa nhập: ngày cần bánh phải từ hôm nay + số ngày đặt trước của tác phẩm (giờ Việt Nam); số điện thoại hợp lệ; tác phẩm còn hiện.
- Ghi doctype mới `Vagabond Dat Thiet Ke` (tối thiểu): mã (TKR-YY-MM-###), tác phẩm, size, trang trí, ngày giờ cần bánh, giao hoặc nhận tại cửa hàng (dùng lại phần địa chỉ, phí giao của đơn web), ghi chú bếp, ảnh tham khảo (tệp riêng tư), khách, tổng (gồm VAT), tiền cọc = làm tròn lên 50% tổng, trạng thái: Chờ cọc, Đã cọc, Đã tạo đơn, Đã huỷ.
- QR cọc: sinh VietQR với nội dung chuyển khoản không dấu chứa mã TKR, theo đúng cách `cong_no` và `thu_hop_dong` (gom thành MỘT phép dùng chung, không chép thứ ba). Máy dò SePay khớp theo mã, đổi trạng thái Đã cọc.
- Khi Đã cọc: tạo đơn Pancake qua đúng đường `don_hang` hiện có (một dòng BAEV00001 giá = tổng, ghi chú in và ghi chú nội bộ là bảng kê: tác phẩm, size, trang trí, ngày tiệc), gắn thẻ "Thiết kế riêng"; tin Zalo nhóm Sales và nhóm bếp kèm mã TKR.
- Phần còn lại 50% trả khi nhận bánh tại quầy, như đơn hiện nay.
- Nút "Nhờ Sales tư vấn trước": gửi tên, số, tác phẩm quan tâm vào nhóm Zalo Sales, không tạo đơn.

### Câu hỏi cho Codex (phần 1)
1. Pancake: tạo đơn với số đã cọc thế nào để QR và COD của Pancake chỉ còn phần còn lại? Có trường trả trước nào đã dùng trong repo, hay phải giảm qua dòng giảm giá (sai về thuế)? Nếu Pancake không có cách đúng, đề xuất: chưa đẩy Pancake lúc cọc, Sales bấm "Tạo đơn" ở màn app khi đã chốt.
2. Tiền cọc vào sổ: SePay khớp mã TKR thì ghi Payment Entry tạm ứng của khách (tài khoản người mua trả trước) hay chỉ đánh dấu, để hoá đơn Pancake về sau gom cả hai? Cần đi đúng cách `_soat_sepay` đang chặn ghi sổ khi tiền chưa về, không làm lệch đối soát của chị Dung.
3. Có nên dùng lại `Hop Dong Ban Hang` + phiếu `PTHD` (đã có cọc theo %, QR, SePay khớp) thay vì doctype mới không? Hợp đồng nặng hơn nhưng có sẵn quy trình.

## Phần 2: Bánh sỉ (PR sau)

- Trang công khai "Bánh sỉ": không hiện giá; form đăng ký (tên quán, MST, số Zalo, loại hình, lượng mỗi tuần) vào doctype `Vagabond Dang Ky Si`, tin Zalo nhóm Sales.
- Sales duyệt ở app: gắn vào Customer có sẵn hoặc tạo mới (nhóm Khách sỉ B2B), bật "Đặt sỉ trên web", bật hoặc tắt "Trả cuối kỳ 15 ngày".
- Đăng nhập: OTP Zalo ZNS như `thanh_vien.py` (cookie riêng `vgb_khach_si`, phiên Guest nên mọi hàm gọi chung không được có cổng quyền nhân viên, bài học Codex #517 vòng 8).
- Giá riêng từng khách: bảng giá riêng của khách trong app (Sales khai một lần mỗi món; gợi ý giá từ dòng Pancake gần nhất của khách và `Anh Xa Ma Si`). Món chưa có giá riêng thì không hiện với khách đó.
- Đặt: ngày giao sớm nhất = ngày đặt + 3; "Đặt lại như đơn trước".
- Thanh toán: khách chưa bật công nợ thì QR trả trước; khách đã bật thì ghi công nợ hạn 15 ngày, trả qua QR gộp của `cong_no.py`.

### Câu hỏi cho Codex (phần 2)
4. Bảng giá riêng từng khách: dùng `Item Price` với `customer` (ERPNext hỗ trợ giá theo khách trên một Price List) hay doctype riêng? Ưu tiên cái mà hoá đơn, Pancake đồng bộ về đọc đúng.
5. Đơn sỉ đi Pancake như đơn web, hay tạo Sales Order hoặc Delivery Note thẳng trong app (`xuat_ban.py`)?

## Ngoài phạm vi
- Không sửa dữ liệu, chứng từ quá khứ.
- Trang đặt bàn và chân trang mới: chờ anh Việt duyệt mẫu, làm PR riêng.
