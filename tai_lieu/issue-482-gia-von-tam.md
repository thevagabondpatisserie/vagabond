# Issue #482: Giá vốn tạm tính cho kế toán giá thành

Đặc tả đầy đủ nằm ở Issue #482. Tệp này chỉ để mở PR làm đầu mối giao việc cho Codex.

- Owner code: Codex. Lead và rà: Claude.
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
