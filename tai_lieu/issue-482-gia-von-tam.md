# Issue #482: Giá vốn tạm tính cho kế toán giá thành

Đặc tả đầy đủ nằm ở Issue #482. Tệp này chỉ để mở PR làm đầu mối giao việc cho Codex.

- Owner code: Claude (anh Việt đổi vai 16/10/2026). Rà: Codex.
- Phạm vi tệp dự kiến:
  - `vagabond/gia_von_tam.py` (mới)
  - một tệp bep mới cho màn GVT
  - `vagabond/duong_app.py`, `02-trang-chu.js`
  - ca kiểm `thu_gia_von_tam.py` và `hanh_vi/gia_von_tam_*.js`
  - `chay.py`, `thu_cua_ngo.py`, `kiem_truoc_deploy.sh`
  - `truong_tu_them.py` (mục sidebar Desk)
  - APPVER và `patches.txt`
- Không ghi vào BOM, Item, Bin, sổ kho, sổ cái hay giá bán Standard Selling.

## Nhật ký giai đoạn

- 16/10/2026: Claude lập đặc tả, mở PR nháp, giao Codex làm.
- 16/10/2026: bản cloud của Codex (6d88fb113) không đẩy được lên GitHub. Anh Việt đổi vai: Claude tự làm trên nhánh này, mời Codex rà.
- 16/10/2026: Claude đẩy bản v599 gồm máy chủ, màn app GVT, lối vào Desk, ca kiểm và đột biến.
- 16/10/2026 (đã deploy v599): anh Việt xem trên điện thoại, chốt hai việc cho v600:
  - Đọc theo hệ số "lãi số lần" (giá bán gấp mấy lần giá vốn), phần trăm giá vốn chỉ hiện kèm: `x6,1 (16,5%)`. Mục tiêu đặt theo hệ số từng nhóm, giá đề xuất = giá vốn x hệ số, làm tròn lên nghìn. Khoá lưu mới `vgb_gia_von_tam_he_so`; khoá cũ theo % chưa ai đặt nên không chuyển.
  - Món R&D chưa bán: tab "Món thử (R&D)" với Phiếu tính giá thử (doctype `Vagabond Gia Thu`). Mã có sẵn lấy giá như món đang bán (bán thành phẩm theo công thức cộng dồn), NVL chưa có mã nhập giá tay. Không tạo Item, không tạo BOM, không đụng kho hay sổ.
- 17/10/2026 (PR #486, Codex rà vòng 1, 5 finding, tái hiện đủ 5 rồi sửa):
  - Phiếu thử có bản nháp tự lưu trên máy (loại `gia_thu`), mở lại từ thẻ trên trang chủ.
  - Bỏ phiếu là bỏ mềm: trường Đã bỏ, người bỏ, lúc bỏ; danh sách ẩn phiếu đã bỏ; chỉ System Manager còn quyền xoá cứng trên Desk.
  - Lưu trên Desk cũng tính lại giá vốn và giá đề xuất qua `validate()`, chung một nguồn với app.
  - Kết quả tính thử và tìm phiếu về trễ không đè kết quả mới.
  - Danh sách chia trang 30 phiếu, có Xem thêm và ô tìm ở máy chủ.
- 17/10/2026 (PR #486, Codex rà vòng 2 trên 74de7508d, 3 finding, tái hiện đủ 3 rồi sửa):
  - Mã bán thành phẩm có từ hai công thức chưa chọn mặc định: phiếu thử không lấy giá kho thay, báo thiếu để nhập giá tay.
  - Bỏ phiếu giữ nguyên giá vốn và giá đề xuất đã chụp, không tính lại.
  - Phiếu đã bỏ không sửa được nữa, kể cả trên Desk; bỏ phiếu không được kèm sửa nội dung. Một chỗ quyết: `quyet_luu_phieu`, gọi từ `validate()`.
- 17/10/2026 (PR #486, Codex rà vòng 3 trên a848c9fbd, 2 finding, tái hiện đủ 2 rồi sửa):
  - Mã nhiều công thức nằm ở tầng dưới (dòng công thức không ghi bom_no) cũng báo thiếu, không lấy giá kho; áp chung cho món đang bán, sheet chi tiết và phiếu thử. Một nguồn: `gia_la_cua` trong `_doc`.
  - Ô "Một mẻ ra" để 0 hoặc trống: không tự thay 1 khi tính thử, ô kết quả nói cần sửa; Lưu cũng chặn. Máy chủ từ chối tính thử thì ô kết quả hiện đúng câu lỗi, bỏ số cũ.
- 17/10/2026 (PR #486, Codex rà vòng 4 trên bcf8c846e, 2 finding, tái hiện đủ 2 rồi sửa):
  - Không vai nào còn quyền xoá phiếu thử trên Desk, và bộ điều khiển chặn xoá (`on_trash`), kể cả System Manager.
  - Mã vừa chọn mà máy chủ báo thiếu giá thì hiện ngay ô giá tay ở đúng dòng sau khi tính.
- 17/10/2026 (PR #486, giao diện chip theo yêu cầu anh Việt; Codex rà vòng 6 trên d23359d49, 2 finding, tái hiện đủ 2 rồi sửa):
  - Thẻ món bán, thẻ phiếu thử và khối kết quả trong phiếu dùng chung kiểu chip và lưới ba ô.
  - Giá vốn còn thiếu, vòng hoặc chưa có nguyên liệu thì không hiện chip hệ số ở bất kỳ đâu (máy chủ vẫn có thể trả hệ số tính trên giá vốn thiếu). Một chỗ quyết: `gvtTinhDuoc`.
  - Thẻ phiếu thử có ô ảnh món giữ hàng như thẻ món bán.
- 17/10/2026 (PR #486, Codex rà vòng 7 trên 14ec6c0c7, 2 finding P2 theo AGENTS.md 2b, tái hiện đủ 2 rồi sửa):
  - Danh sách phiếu thử có ba hàng chip: trạng thái có đếm, nhóm bán có đếm (kể cả "Chưa chọn nhóm"), khoảng ngày lập. Lọc, đếm và chia trang ở máy chủ (`loc_trang_thu`), Xem thêm đi đúng bộ lọc đang dùng. Trạng thái tính theo giá hôm nay nên máy chủ tính cả tập tối đa 500 phiếu mới sửa nhất rồi lọc; vượt thì màn ghi rõ.
  - Nhóm bán của phiếu (chín nhóm) chọn bằng thẻ giá trị đang chọn mở sheet có ô tìm, không còn hàng chip.
- 17/10/2026 (PR #486, Codex rà vòng 8 trên ba6517a1f, 1 finding P2, tái hiện rồi sửa): quá 500 phiếu khớp tên thì câu "chỉ lọc trong 500 phiếu sửa gần nhất, gõ tên để thu hẹp" hiện cả khi lọc ra rỗng.
- 17/10/2026 (PR #486, Codex rà vòng 9 trên f61c6d30f, 2 finding P1, tái hiện đủ 2 rồi sửa):
  - Dòng có mã: hỏi giá mã trước, chỉ nhận giá nhập tay khi mã thiếu giá (chưa có giá hoặc nhiều công thức chưa chọn). Mã đã có giá thì giá tay cũ bị bỏ qua, màn không hiện ô giá tay. Công thức vòng không bị giá tay che.
  - Dấu vết trên thẻ và màn phiếu: ai lập lúc nào, ai sửa gần nhất lúc nào, chip "Đã sửa N lần". Trường mới `so_lan_sua` (chỉ đọc) do máy chủ đếm mỗi lần lưu có đổi nội dung, kể cả sửa trên Desk; bỏ phiếu không tính.
- 17/10/2026 (PR #486, Codex rà vòng 10 trên 356502e1c, 2 finding, tái hiện đủ 2 rồi sửa): công thức vòng kèm thiếu giá lá thì giá tay không xoá cờ vòng; dấu vết phiếu giữ riêng nên tính thử rồi vẽ lại màn vẫn còn.
- 17/10/2026 (PR #486, Codex rà vòng 11 trên b3a3bd611, 3 finding P2, tái hiện đủ 3 rồi sửa):
  - Sheet hệ số mục tiêu có đủ chín nhóm (máy chủ trả `nhom_ban`), cuộn được; máy chủ chỉ đổi nhóm có gửi (`gop_he_so`), nhóm không gửi giữ nguyên mục tiêu.
  - Công thức vòng: không bảo nhập giá tay, không có ô giá tay, chỉ đường sửa công thức (một câu chung cho thẻ và màn phiếu).
  - Dấu vết nằm trong phiếu đang sửa nên bản nháp của phiếu đã lưu mở lại vẫn còn.
