# Issue 380: công nợ đã trả vẫn hiện, sổ đơn tặng, bộ công cụ danh sách chung

- Nguồn: https://github.com/thevagabondpatisserie/vagabond/issues/380 (góp ý Sales Manager 28/09/2026, anh Việt giao lên phương án cùng Codex, duyệt rồi mới làm PR code).
- Owner: Claude (Cowork). Nền: main 44399628 (v533). Kiểm site thật 28/09/2026, chỉ đọc.
- Trạng thái: PHƯƠNG ÁN, chờ anh Việt duyệt. Chưa có code. PR này chỉ chứa tài liệu để Codex rà.

## Kết quả có bằng chứng (chỉ đọc)

Triệu chứng: khách đã chuyển đủ tiền vẫn nằm trong "Khách đang nợ" của màn Công nợ phải thu.

Chuỗi nguyên nhân đã chứng minh trên một ca thật (tên khách và số chứng từ để trong nhật ký riêng, không đưa vào repo công khai):

1. `cong_no.ds_khach_no` tính nợ bằng `thu_tien.con_no_cua`, trả `min(outstanding_amount, theo_dong)`. Hoá đơn còn `outstanding_amount` đầy đủ nên còn nợ. Code màn hình đúng, sai nằm ở dữ liệu thu tiền.
2. Có Payment Entry chiều Receive đúng số tiền, `reference_no` là số FT ngân hàng, phân bổ đúng hoá đơn, nhưng `docstatus = 0`.
3. Người lập là Administrator, remarks mặc định ERPNext: do Server Script API `vgb_khop_sepay` (chạy 15 phút một lần) lập. Script `insert()` rồi `submit()` trong `try`, `except` nuốt lỗi vào `pt_loi`, cuối cùng `frappe.db.commit()`. Nên bản nháp được lưu, lỗi không vào Error Log.
4. `submit()` hỏng vì hook `before_submit` `chung_tu_tien.chan_thieu_dinh_kem` (NGAY_CHOT 16/08/2026) đòi tệp đính kèm cho mọi chứng từ chạm TK ngân hàng, cả chiều thu.
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
