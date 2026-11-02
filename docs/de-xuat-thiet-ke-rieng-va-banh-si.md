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

### Đặt và cọc (bản 2, anh Việt chốt 02/11 sau góp ý Codex)

Codex vòng 1 chỉ ra: đẩy đơn cọc qua Pancake thì Pancake vẫn đòi đủ tiền, `_soat_sepay` so tiền theo mã Pancake với toàn bộ hoá đơn nên đơn trả hai lần bị chặn ghi sổ, và đường `don_hang` không giữ được giá máy chủ cho BAEV00001 (giá chuẩn 0). Anh Việt chọn: đơn Thiết kế riêng đi LUỒNG ĐẶT BÁNH CỦA APP (`dat_banh.py`, issue #195), mở thêm cọc 50%, KHÔNG qua Pancake.

- Cửa mới `thiet_ke_rieng.dat(du_lieu)` (allow_guest, POST, giới hạn lượt như `tiec_web.dang_ky`). Máy chủ tự tính giá từ khối đã xuất bản theo mã tác phẩm, size, trang trí; không nhận giá từ trình duyệt.
- Chặn ở cửa nhập: ngày nhận từ hôm nay + số ngày đặt trước của tác phẩm (giờ Việt Nam), số điện thoại hợp lệ, tác phẩm còn hiện.
- Tạo phiếu đặt đúng kiểu `dat_banh` (Sales Order), một dòng BAEV00001 giá = giá đã xác nhận ở máy chủ (gồm VAT), mô tả dòng và ghi chú là bảng kê: tác phẩm, size, trang trí, ngày tiệc. Ngày nhận = ngày giao, điểm nhận chọn trên web. Trạng thái chờ cọc.
- QR cọc: VietQR nội dung không dấu chứa mã phiếu đặt, số = làm tròn lên 50% tổng. Gom phép dựng QR của `cong_no` và `thu_hop_dong` thành MỘT phép dùng chung.
- Tiền về: máy dò SePay khớp theo mã, tạo chứng từ thu ứng trước trỏ ĐÚNG phiếu đặt (qua đủ bốn hàng rào `loi_phieu_dat_banh`), đánh dấu chiếm giao dịch với `doi_soat_sepay` để giao dịch không bị dùng lại. Tin Zalo nhóm Sales và nhóm bếp.
- Ngày giao: thu phần còn lại tại quầy trên màn nhận bánh (tiền mặt, chuyển khoản, QR) thành chứng từ thu thứ hai cùng phiếu đặt; hoá đơn VAT xuất ngày giao, cấn cả hai khoản ứng trước như luồng đặt bánh hiện nay. Bất biến: mỗi đồng vào két hoặc tài khoản đúng một lần.
- Nút "Nhờ Sales tư vấn trước": gửi tên, số, tác phẩm quan tâm vào nhóm Zalo Sales, không tạo đơn.

### Câu hỏi cho Codex (phần 1, vòng 2)
1. `dat_banh` hiện chốt "trả trước toàn bộ". Mở cọc một phần thì những chỗ nào đang giả định đã trả đủ (màn nhận bánh, `con_giu_cho`, phương thức "Trả trước" trên hoá đơn ngày giao, `tong_ung_truoc`)?
2. Cọc vào bằng chuyển khoản trên web nên không có quầy thu; hàng rào 1 của `loi_phieu_dat_banh` bắt có quầy. Gán quầy = điểm nhận bánh có đúng với `thu_ung_truoc` và đối soát két không, hay cần một nhánh "ứng trước qua ngân hàng" ngoài két?
3. Khi Sales đã có phiếu đặt tay cho khách, tránh trùng với phiếu web thế nào?

## Phần 2: Bánh sỉ (PR sau)

- Trang công khai "Bánh sỉ": không hiện giá; form đăng ký (tên quán, MST, số Zalo, loại hình, lượng mỗi tuần) vào doctype `Vagabond Dang Ky Si`, tin Zalo nhóm Sales.
- Sales duyệt ở app: gắn vào Customer có sẵn hoặc tạo mới (nhóm Khách sỉ B2B), bật "Đặt sỉ trên web", bật hoặc tắt "Trả cuối kỳ 15 ngày".
- Đăng nhập: OTP Zalo ZNS như `thanh_vien.py` (cookie riêng `vgb_khach_si`, phiên Guest nên mọi hàm gọi chung không được có cổng quyền nhân viên, bài học Codex #517 vòng 8).
- Giá riêng từng khách: bảng giá riêng của khách trong app (Sales khai một lần mỗi món; gợi ý giá từ dòng Pancake gần nhất của khách và `Anh Xa Ma Si`). Món chưa có giá riêng thì không hiện với khách đó.
- Đặt: ngày giao sớm nhất = ngày đặt + 3; "Đặt lại như đơn trước".
- Thanh toán: khách chưa bật công nợ thì QR trả trước; khách đã bật thì ghi công nợ hạn 15 ngày, trả qua QR gộp của `cong_no.py`.

### Hướng sau góp ý Codex vòng 1 (câu 4, 5)
- Codex: đường đơn web không đọc Item Price, và `xuat_ban.luu` submit Delivery Note trừ kho ngay, nên không dùng lúc đặt trước ba ngày.
- Hướng: đơn sỉ trên web là Sales Order trong app (bước nhận đơn), giao hàng là bước riêng ở ngày giao (Delivery Note, hoá đơn như khách sỉ hiện nay). Giá theo khách đọc qua MỘT hàm máy chủ (Item Price có `customer` trên bảng giá bán) cho cả web lẫn màn nhận đơn; không nhận giá từ trình duyệt.

### Câu hỏi cho Codex (phần 2, vòng 2)
4. Sales Order sỉ có cần giữ chỗ bảng kiểm bánh như phiếu đặt `dat_banh` không, hay bếp lên kế hoạch từ danh sách đơn sỉ theo ngày giao?
5. Công nợ 15 ngày: đặt `payment_terms` trên hoá đơn hay chỉ tính hạn ở `cong_no.py` cho khớp màn Công nợ hiện có?

## Ngoài phạm vi
- Không sửa dữ liệu, chứng từ quá khứ.
- Trang đặt bàn và chân trang mới: chờ anh Việt duyệt mẫu, làm PR riêng.
