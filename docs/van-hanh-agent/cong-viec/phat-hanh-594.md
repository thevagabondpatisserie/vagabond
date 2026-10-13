# Phát hành v594

Owner: Codex. Base: main 42cb9fb9a9310c2c7a03d9e2f19e26dd17dd0375.
Nhánh: codex/phat-hanh-594. Claude rà độc lập sau cổng; chưa merge/deploy.

## Phạm vi theo comment giao việc trên #474

- Merge theo thứ tự #474 8be4cc7a22f36271a94b8691b2e62cf69bd6a71c,
  #473 6074ebe35d26c3811b38e138f25e7f3eb3d1c016,
  #469 a205cdbb2bad1b266a72e5fd4b73a613a72a32f8.
- Lấy riêng diff máy chủ, trang cũ, ca kiểm F21 của 3f2ad0b70 và
  4e3f85e56. Gồm mua_vu.py vì callback cảnh báo nguồn mùa vụ được don_hang
  gọi. Không lấy giai đoạn Vue hoặc tệp web_vue/web_moi.
- APPVER 594, thêm đúng một patch v594 sau v592 của main; bỏ v593 nhánh con.
- Bốn điểm BOM: Tất cả đúng bộ lọc Excel; kiểm quyền ở API; ngày Sài Gòn;
  lịch sử tiếng Việt, không giá vốn máy tính, không escape hai lần.
- xet_bo của #469 còn là phép thuần, chưa nối đường ghi: việc tách lệnh
  ngân hàng làm PR sau từ main. #471 tiếp tục Vue trên nền sau phát hành.

## Kiểm và bàn giao

Tám đột biến BOM đều bị bắt, mỗi đột biến làm đỏ một nhóm ca. Bộ khung trên
bản gom: 4489/4489; hai ca PDF #247 không chạy do máy thiếu pypdf, không tính
đạt. Giả lập CI không requests cũng 4489/4489; dựng app và cổng trước deploy
mã 0. F21 trang cũ đạt ca DOM giữ giỏ/nonce và tải lại tồn ở 390/1440px;
hai đột biến backend bắt 2/2, mỗi lần hỏng 3/11 ca. Bench theo SHA cuối
nằm trong biên nhận PR.
Các tệp có sửa riêng là cong_thuc.py, lich_su_bom.py, 26-cong-thuc.js cùng ca
BOM. Tệp đăng ký ca, bài học giữ cả phần thêm; app_bep.js dựng lại từ nguồn.

## Đối chiếu tệp chính

| Nguồn | Tệp | SHA-256 nguồn = bản gom |
|---|---|---|
| #474 8be4cc7a2 | `vagabond/qr_chuyen_khoan.py` | `5088453c621261290bf34dcd0e6c059e2dddda5cb1f0c71b888f6c79b648d9ad` |
| #474 8be4cc7a2 | `vagabond/public/js/qr_chuyen_khoan.js` | `d8fa08b7d482b7da30efc4951964f94fa995c36b8197b97f7b33b1b55a5d3531` |
| #474 8be4cc7a2 | `vagabond/public/js/bep/25-man-hinh-khach.js` | `3e8d9628cf43d7d3e025e35f1212041e61ce2110c646310dfcb4ecf47bcb4cae` |
| #474 8be4cc7a2 | `vagabond/tai_khoan.py` | `186424b913c71d8cc894f9b19ca30b9d1d8bd312d3cea8d56e8e0bcf4a7b1286` |
| #473 6074ebe35 | `vagabond/kiem_ke.py` | `11d52e10d5c1d11280402f548079c8a35c9bb877b1087dbb15684db01a80eac3` |
| #473 6074ebe35 | `vagabond/public/js/bep/06-nhap-kho-kiem-ke.js` | `6f56c138b01f766fd5ed6d745a181ea913eba311e2fe8a2c75cbde56a5af8c6c` |
| #469 a205cdbb2 | `vagabond/don_bep.py` | `a041e7acaf023cf184fd97afb0a303c25c45b165c0bad2f0a5c7018f737ec252` |
| #469 a205cdbb2 | `vagabond/doi_dvt_bom.py` | `8dd0fe471dde57e15315eb8a0cdaf327ec7af9d89a2761f0d8033803ba1cb647` |
| #469 a205cdbb2 | `vagabond/bo_ao.py` | `09edec94105fc0a71bbb67e78c9f88d29db8eaa07e022efcb9692df57246d406` |
| #469 a205cdbb2 | `vagabond/ton_chang.py` | `368fff2d21865fbe06991797432d21c9b84262fa6ace2a4e41e4ed0170243469` |
| #469 a205cdbb2 | `vagabond/khop_sao_ke.py` | `11f52e8b9d163c057b1bf6ccf17b363b9a753cb41d96484c88cdae861addf741` |
| #471 4e3f85e56 | `vagabond/ton_don_web.py` | `9503a56009a535d8b36dc74924d7f632db2f67349edd9d4b23cd4db7b217ac0f` |
| #471 4e3f85e56 | `vagabond/don_hang.py` | `890d83e6222d911b58ff99aef9e947705652b99f2e8c6473e1011f2645818f2d` |
| #471 4e3f85e56 | `vagabond/mua_vu.py` | `59a0726cd315475b36461aafe40401bd4fafd5dea5bdac691081b093cde5080c` |
| #471 4e3f85e56 | `vagabond/trang/banh.html` | `e91058d2f33aab9d93c6122bafde6aa8a2b5af5d10f15d854683565cb371ea59` |
| #471 4e3f85e56 | `vagabond/khung/kiem_thu/thu_ton_don_web_593.py` | `8bd1944425f0f7ce34520b76117b1bfc99a91a5a1f5f3d240d4fc7eb52428521` |
| #471 4e3f85e56 | `vagabond/khung/kiem_that/thu_ton_don_web_593.py` | `8cdd8d1f6300f97fdad58f175e414a83e64dfc1bbac0c77b0004d573ef69e768` |
