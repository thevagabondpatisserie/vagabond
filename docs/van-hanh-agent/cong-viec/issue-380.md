# Issue 380: công nợ đã trả vẫn hiện, sổ đơn tặng, bộ công cụ danh sách chung

- Nguồn: https://github.com/thevagabondpatisserie/vagabond/issues/380 (góp ý Sales Manager 28/09/2026, anh Việt giao lên phương án cùng Codex, duyệt rồi mới làm PR code).
- Owner: Claude (Cowork). Nền: main 44399628 (v533). Kiểm site thật 28/09/2026, chỉ đọc.
- Trạng thái: anh Việt đã chốt 4 câu ngày 28/09 (mục "Quyết định" dưới). Đợt 1 làm ở nhánh v534, xếp chồng trên tài liệu này.

## Kết quả có bằng chứng (chỉ đọc)

Triệu chứng: khách đã chuyển đủ tiền vẫn nằm trong "Khách đang nợ" của màn Công nợ phải thu.

Chuỗi nguyên nhân đã chứng minh trên một ca thật (tên khách và số chứng từ để trong nhật ký riêng, không đưa vào repo công khai):

1. `cong_no.ds_khach_no` tính nợ bằng `thu_tien.con_no_cua`, trả `min(outstanding_amount, theo_dong)`. Hoá đơn còn `outstanding_amount` đầy đủ nên còn nợ. Code màn hình đúng, sai nằm ở dữ liệu thu tiền.
2. Có Payment Entry chiều Receive đúng số tiền, `reference_no` là số FT ngân hàng, phân bổ đúng hoá đơn, nhưng `docstatus = 0`.
3. Người lập là Administrator, remarks mặc định ERPNext: do Server Script API `vgb_khop_sepay` (chạy 15 phút một lần) lập. Script `insert()` rồi `submit()` trong `try`, `except` nuốt lỗi vào `pt_loi`, cuối cùng `frappe.db.commit()`. Nên bản nháp được lưu, lỗi không vào Error Log.
4. (Giả thuyết mạnh, chưa có nguyên văn lỗi, Codex #381) `submit()` hỏng vì hook `before_submit` `chung_tu_tien.chan_thieu_dinh_kem` (NGAY_CHOT 16/08/2026) đòi tệp đính kèm cho mọi chứng từ chạm TK ngân hàng, cả chiều thu.
5. Lần chạy sau, script bỏ qua hoá đơn đã có Payment Entry Reference `docstatus < 2`, nên không bao giờ thử lại.

Số đo 28/09/2026:

- 1.428 Payment Entry Receive nháp mang `reference_no` FT, 16/08 tới 27/09, tổng 1.330.492.197 đ; 0 phiếu FT nào ghi sổ được kể từ 16/08; khoảng 25 tới 36 phiếu mỗi ngày.
- 1.428 hoá đơn tương ứng, tất cả còn `outstanding_amount > 0` (tổng 1.374.915.695 đ); 1.422 mang phương thức Chuyển khoản, 6 mang Công nợ.
- Màn Công nợ: 67 hoá đơn, 182.258.100 đ; 7 hoá đơn (7 khách, 27.622.100 đ) có phiếu thu nháp.
- Cùng nguyên nhân đã ghi ở nhật ký 22/08/2026 (lúc đó 139 phiếu), ba phương án chưa được chốt.

Màn Duyệt đơn hàng tặng (`41-duyet-don-tang.js`, `hang_tang.ds_don`): 3 trạng thái `Chờ duyệt / Đã duyệt / Từ chối`; `da_ghi_so` chỉ là nhãn, không phải chip; không lọc ngày; không mở lại bill; không Excel.

Khảo sát nhanh bằng dò chuỗi (ước lượng, không phải kiểm thử): khoảng 60 hàm `scr*` gọi API danh sách; khoảng 33 có chip; 9 hàm `xuat_excel` máy chủ viết riêng (bao_cao, de_nghi_chi, don_huy x2, ho_so_tt, hoan_tien, ncc, nop_quy, van_don); khuôn `khung.ds` (phần 15) có chip, lọc, tóm tắt nhưng chưa có Excel.

## Phương án

### 1. Công nợ

- 1A (quyết định kế toán, anh Việt và chị Dung): `chan_thieu_dinh_kem` cho qua phiếu Receive khi `reference_no` khớp một Bank Transaction đã ghi sổ và số tiền không vượt `unallocated_amount`. Chiều Pay giữ nguyên. Thuần hoá phép so khớp để kiểm không cần site.
- 1B (màn hình, không đụng dữ liệu): `ds_khach_no` trả thêm nhóm `cho_ghi_so` gồm hoá đơn có Payment Entry Receive nháp phân bổ đủ phần còn nợ. Nhóm này không cộng vào `tong`, hiện ở chip riêng "Tiền đã về, chờ ghi sổ" với số tiền, ngày tiền về, mã phiếu thu. Hàm phân loại là phép thuần.
- 1C (cần duyệt riêng vì chạm Server Script): chuyển phần lập phiếu thu sang `vagabond/thu_tien.py` (git quản, có ca kiểm, đăng ký `thu_cua_ngo.py` nếu whitelist), lỗi submit ghi thành việc cho kế toán thay vì nuốt. Tắt Server Script chỉ khi anh Việt tự bấm hoặc cho phép rõ.
- 1D: không tự ghi sổ 1.428 phiếu tồn (điều 11). Thêm bảng chỉ đọc cho chị Dung, ghi sổ theo đợt có rà soát sau khi chốt 1A.

### 2. Sổ đơn hàng tặng

- `ds_don` nhận thêm `chang` (cho_duyet, cho_ghi_so, hoan_tat, tu_choi) và `tu`, `den`; đếm chip ở máy chủ. `hoan_tat` = đã duyệt và `docstatus = 1`.
- Mỗi dòng hoàn tất: nút xem lại hoặc in lại bill (dùng hàm in bill có sẵn), số HĐĐT, người duyệt.
- Excel qua hàm dùng chung ở mục 3. Sales đọc được, duyệt giữ `duoc_duyet()`.

### 3. Bộ công cụ danh sách dùng chung

- Máy chủ `vagabond/khung/xuat_bang.py`: `dung_bang(cot, dong)` thuần, `xuat(ma_man, **loc)` chạy lại hàm danh sách của màn với `day_du=1`, kiểm quyền bằng chính hàm gốc, trả xlsx base64. Một sổ khai `MAN_XUAT = {ma: (ham, cot)}`.
- App: `dsCongCu({chip, chang, tim, xuat})` vẽ một hàng chip lọc, một hàng chip chặng từ bảng `CHANG[loai]`, ô tìm, nút Xuất Excel. Gắn vào khuôn `kg` trước.
- Ca kiểm chốt kiểu v533: mọi màn danh sách phải dùng `dsCongCu` hoặc nằm trong `MIEN` kèm lý do; Excel xuất đúng số dòng màn đếm (ca hành vi trên `gia_lap_trang.js`).
- Đợt 1 (Sales), đợt 2 (Kế toán), đợt 3 (Kho, bếp), mỗi đợt một PR.

## Còn lại và bàn giao

- Chờ anh Việt trả lời 4 câu ở issue #380.
- Codex: rà phương án (đúng nguyên nhân chưa, rủi ro 1A với luật chứng từ, thiết kế 3 có vỡ màn cũ không). Không có code để rà.
- Chưa kiểm: lý do submit cụ thể của từng phiếu trong 1.428 (script không lưu); đã suy ra từ hook và từ việc 0 phiếu FT ghi sổ sau 16/08. Quyền của tài khoản Sales với màn Duyệt tặng chưa kiểm bằng tài khoản thật.
- Không merge, không deploy.

## Quyết định anh Việt 28/09/2026

1. Không công nhận riêng giao dịch ngân hàng làm chứng từ gốc chiều thu. Thêm ô đính **uỷ nhiệm chi khách gửi**; có tệp đó mới ghi sổ phiếu thu. Hook đính kèm giữ nguyên. Phương án 1A cũ bỏ.
2. Đồng ý chuyển phần tự lập phiếu thu từ Server Script về repo (1C). Làm PR riêng sau v534, vì phải tắt phần tạo phiếu của Server Script cùng lúc.
3. Đợt 1 gộp một PR: màn Công nợ, sổ Hàng tặng, bộ công cụ danh sách chung.
4. Sales được xem sổ Hàng tặng (chỉ xem). Quản lý cửa hàng cũng xem được. Kiểm site 28/09: hai tài khoản Sales Manager và quản lý cửa hàng đều mang vai Sales User nên đã qua cổng quyền đọc; chỉ thiếu lối vào ở nhóm Bán hàng.

## Trả lời 6 finding Codex trên #381 (SHA f7d1d9a)

- F1 nguyên nhân submit chưa có nguyên văn: đồng ý, đã đổi thành giả thuyết. Bằng chứng thêm 28/09: cả 1.428 phiếu có `paid_to` bắt đầu 112, `creation` từ 2026-08-16 23:01, 0 tệp đính kèm, nên `chan_thieu_dinh_kem` chắc chắn ném lỗi nếu tới lượt before_submit. Chưa loại được một lỗi ở `validate` chạy trước. v534 thêm hàm chẩn đoán chỉ đọc (chạy validate và before_submit trong savepoint rồi lùi, không chạy on_submit, không sinh GL) để lấy nguyên văn trên site sau deploy.
- F2 giữ chỗ giao dịch ngân hàng: 1A bỏ, nhưng bước ghi sổ phiếu thu mới vẫn đối soát Bank Transaction: khoá dòng (for_update), kiểm chiều tiền vào, cùng tài khoản sổ cái với `paid_to`, cùng công ty, VND, chưa nối chứng từ khác, số chưa phân bổ đủ; ghi sổ xong `add_payment_entries` rồi tải lại xác minh; lỗi giữa chừng lùi cả lượt bằng savepoint. Theo mẫu `tam_ung_app.ghi_nhan_cap`.
- F3 ca tích hợp sổ cái: thêm ca `kiem_that` chạy trên bench: SI thật, BT thật, PE nháp, tệp UNC, ghi sổ, đọc GL, thử lại không ghi hai lần, thiếu tệp bị chặn, BT đã nối chứng từ khác bị chặn, lỗi sau submit lùi sạch.
- F4 giữ khoản chưa ghi sổ trong tổng nợ: sửa lại. "Tiền đã về, chờ ghi sổ" chỉ tách khi Bank Transaction đã xác minh độc lập (điều kiện ở F2). Thẻ tổng hiện cả hai con số, kèm một dòng "Sổ cái vẫn tính nợ khoản tiền đã về cho tới khi phiếu thu được ghi sổ", không để con số nợ trên sổ lặng lẽ biến mất.
- F5 Excel đủ dòng: sổ khai mỗi màn một adapter riêng nhận đúng bộ lọc của màn, bỏ trần dòng khi xuất; có ca thuần chốt xuất 501 dòng ra đủ 501.
- F6 đặc tả giao diện: khối dưới đây.

## Giao diện (v534)

Khung dùng lại: frame, card, posChipNut, kmHangChip, sheet có sẵn, tdkKhoi (ô tải tệp dùng chung), bcTaiVe.

Thanh công cụ dùng chung `dsCongCu` (thêm vào 15-khuon-danh-sach.js), thứ tự từ trên xuống:
1. Hàng chip chặng (màu xanh két), có số đếm máy chủ.
2. Các hàng chip lọc riêng của màn (mỗi họ một màu như cũ).
3. Hàng chip ngày: Mọi ngày, Hôm nay, 7 ngày, Tháng này, Tháng trước, Tuỳ chọn (bấm Tuỳ chọn mới hiện hai ô ngày).
4. Một hàng: ô tìm (chiếm phần còn lại) và nút viền "Xuất Excel N" bên phải.
Nhãn chip tối đa khoảng 16 ký tự, số đếm in đậm sau nhãn; hàng chip cuộn ngang, chừa lề. Chạm tối thiểu 44 điểm.

Công nợ phải thu:
1. Thẻ số: CÒN PHẢI ĐÒI (cam), TIỀN ĐÃ VỀ CHỜ GHI SỔ (xanh), ĐÃ GỬI CHỜ TIỀN (xanh dương); một dòng nhỏ dưới nói sổ cái vẫn tính nợ khoản tiền đã về cho tới khi phiếu thu vào sổ.
2. Chip tab: "Đang nợ N", "Tiền đã về N", "Phiếu đã gửi N".
3. Thanh công cụ. Tab Đang nợ: tìm tên khách, Excel. Tab Tiền đã về: chip nguồn "Khách công nợ" (mặc định) và "Đơn chuyển khoản", chip ngày, tìm, Excel.
4. Danh sách. Dòng Tiền đã về: tên khách đậm, dòng phụ "HĐ ... · về dd/mm · GD ...1234" (mã giao dịch rút bốn số cuối), số tiền bên phải; chip "Chưa có UNC" đỏ nhạt hoặc "Có UNC" xanh; nút "📎 Đính UNC khách gửi" (viền); tài khoản kế toán thêm nút chính "Ghi sổ phiếu thu".
Ba trạng thái: 0 dòng "Không có khoản nào đang chờ ghi sổ."; 1 dòng hiện đủ; 60 dòng trở lên chỉ hiện 200 dòng đầu kèm câu "còn N dòng, thu hẹp bằng chip ngày hoặc tìm" (Excel vẫn đủ). Lỗi: câu tiếng người lấy từ máy chủ, không trắng màn.

Sổ hàng tặng (màn Duyệt đơn hàng tặng, đổi tên hiển thị "Hàng tặng: duyệt và sổ đơn"):
1. Thẻ tóm tắt như cũ (thu gọn lời giải thích thành hai dòng).
2. Thanh công cụ: chip chặng Chờ duyệt, Chờ ghi sổ, Hoàn tất, Từ chối; chip điểm bán; chip loại tặng; chip ngày; tìm; Excel.
3. Danh sách như cũ; dòng mở rộng thêm nút viền "🧾 Xem lại bill".
Lối vào: thêm thẻ ở nhóm Bán hàng cho Sales và quản lý cửa hàng; nút Duyệt vẫn chỉ hiện với giám đốc.
Số thật 28/09: 41 đơn tặng (1 chờ duyệt, 40 hoàn tất), công nợ 29 khách, tiền đã về chờ ghi sổ 1.428 dòng.

Bằng chứng giao diện: ca hành vi node (không tính CSS) trên PR; ảnh site thật 390px chỉ có sau deploy, ghi rõ nguồn.
