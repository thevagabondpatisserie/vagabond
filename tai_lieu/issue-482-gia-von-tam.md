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
