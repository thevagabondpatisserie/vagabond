# PR A: sửa nền giao diện mới theo lượt kiểm của Codex 21/11/2026

## Tóm tắt cho anh Việt

Lượt kiểm của Codex trên tài khoản anh Việt (giao diện mới đang thử) chỉ ra 10 nhóm lỗi UI01 tới UI10. PR A sửa năm nhóm nằm ở phần dùng chung (UI01 tới UI05), áp cho mọi màn dùng các thành phần đó. Giao diện cũ của cả tiệm không đổi một điểm ảnh (so 51 ảnh với main). Điều hướng nhanh (UI09) để PR B riêng; UI06, UI07, UI08, UI10 nằm trong các màn nghiệp vụ, làm theo PR nhóm màn.

Nền: main `79ed879c0` (v680). Bản phát hành: v681.

## Bảng lỗi UI01 tới UI10

| Mã | Hiện tượng | Trạng thái | Cách sửa và chứng minh |
|---|---|---|---|
| UI01 | Vùng đồng hồ iPhone xanh đặc khi đang ở giao diện mới | Đã sửa, chưa kiểm máy thật | Máy chủ chèn `meta theme-color` màu đầu trang giao diện mới `#EAF4F3` khi bật; giao diện cũ giữ `#50DBF2`; lệch phiên bản thì app gỡ giao diện mới và đổi vỏ về màu cũ cùng lúc. Một màu cho máy chủ (`giao_dien.MAU_VO_APP`), phần 00 (`PWA_MAU_UIB`) và biến `--ui-header-tint`. Ca node chạy nguyên tệp app ở ba trường hợp. Chưa kiểm Safari và app thêm vào màn hình chính trên iPhone thật: Safari mới có thể lấy màu theo nền trang thay vì thẻ meta, cần anh mở thử. Không cần xoá cài lại app: thẻ meta đọc lại mỗi lần mở trang. |
| UI02 | Số 1339 chồng biểu tượng ô Sản xuất ở 360 (2,4px) | Đã sửa | Lớp vẽ đo thật rồi theo bước của bản 4 mục 4: Doto 30, Be Vietnam Pro 24 đậm, rồi đưa số xuống hàng riêng rộng cả ô. Ô Việc cần làm: Doto 48, 40, 30, Be Vietnam Pro 24, rồi hàng riêng. Không cắt số, không thu dưới 24. Kiểm 0, 9, 99, 999, 1339, 12345, 99999, 1234567 và 99+ ở 360, 390, 1366. Số đếm nghiệp vụ không đổi. |
| UI03 | "Thu tiền 0 đ" xuống dòng ở 390, "Tạm tính" xuống dòng ở 360 | Đã sửa cho mọi thanh đáy | Nút chính: đệm trái 16, đệm phải chừa đúng mặt trăng (40 + 6 + 8), thay cho 56 hai bên. Nút phụ rộng 38% như đặc tả, nhãn dài thì nới tới 50%. Hai nút không vừa nhãn một dòng thì xếp chồng (nút phụ trên, nút chính dưới, mỗi nút rộng cả hàng). Nhãn có số tiền từ 6 chữ số được hai dòng, chia đều. Kiểm bằng đúng markup thanh đáy của Tính tiền và Đối soát nhà cung cấp. |
| UI04 | Hộp chọn ghim còn emoji, menu Nhân sự còn emoji Tuyển dụng | Đã sửa | Bộ thay biểu tượng theo dõi cả các hộp gắn ngoài màn chính; hộp chọn chung và bảng trượt có ô biểu tượng riêng; emoji đầu nhãn nút và chip đổi thành biểu tượng chung; chữ gợi ý ô tìm bỏ emoji kính lúp, vẽ kính lúp bằng biểu tượng; thêm `🧑‍💼 → briefcase`. Hộp chọn chung dùng biến của bộ chuẩn (chữ 13, màu chữ phụ đạt tương phản, dòng đã chọn nền mực). |
| UI05 | Nút đóng Trợ lý 34x34 đọc "Dong"; nút đóng hộp chọn là div không tên | Đã sửa | Mọi lớp phủ `.sh` thành dialog có tên; nút đóng có vai trò nút, tên "Đóng", bấm được bằng Enter, Space; focus vào khung hộp khi mở (không bật bàn phím ảo), trả về nút đã mở khi đóng; Escape chỉ đóng hộp trên cùng và không đóng hộp có ô nhập đã sửa; Tab đi vòng trong hộp. Nút đóng Trợ lý 44, đọc "Đóng". Không gửi câu hỏi hay tin thật. |
| UI06 | Nút bàn POS, chip báo cáo, chip Việc cần làm, nút camera dưới 44 | Chưa làm, PR nhóm màn | Máy đo vùng bấm đã bắt được loại này; sửa theo thành phần khi chuyển nhóm màn. |
| UI07 | Chip "Đang chạy" bị cắt trong thẻ Đối soát | Máy kiểm đã bắt được, màn chưa sửa | Thêm phép đo chữ bị cắt trong thẻ dù cả trang không cuộn ngang. Thử phá: chip đẩy tới x446 trong thẻ, máy báo đúng. Màn Đối soát sửa trong PR nhóm Thu mua. |
| UI08 | Báo cáo còn chữ 12 và 12,5, Bảng bếp chưa có ảnh món, màn trộn kiểu cũ | Chưa làm, PR nhóm màn | Màn chưa chuyển không được tính đạt. |
| UI09 | Back, Trang chủ chờ số liệu rồi mới vẽ | Chưa làm, PR B | Tách khỏi PR này để đo trước và sau và để rút lại dễ. |
| UI10 | Bút toán lọc "Đã huỷ 0" nói "chưa có bút toán nào trong 60 ngày" | Chưa làm, PR nhóm Kế toán | |

## Máy kiểm: kịch bản và phép đo mới

Kịch bản thêm trong `cong_cu/ui_b/kich_ban.cjs`:

| Kịch bản | Kiểm | Ghi chú |
|---|---|---|
| `chon-ghim` | Hộp chọn ghim mở từ trang chủ chưa ghim: biểu tượng, chữ, vùng bấm; bàn phím: dialog có tên, focus vào hộp, Escape đóng, focus về nút đã mở | Phép bàn phím chạy ở chế độ bật |
| `tro-ly` | Hộp Trợ lý: nút đóng 44, tên "Đóng" | Mở bằng nút đầu trang (mới) hoặc nút nổi (cũ) |
| `thanh-day` | Bốn thanh đáy dựng lại đúng markup Tính tiền 0 đ, Tính tiền 12.345.000 đ, Đối soát, một nút | Phép thử thành phần, không thay kịch bản màn Tính tiền (PR 2) |
| `so-tren-o` | Số 0, 9, 99, 999, 1339, 12345, 99999, 1234567 trên ô nhóm, 99+ trên Việc cần làm | |

Phép đo thêm trong `cong_cu/ui_b/chup.cjs`: màu vỏ app theo chế độ; số chồng biểu tượng, ra khỏi ô, gãy dòng; chữ bị cắt trong lớp cha có cắt tràn; nhãn ngắn của nút, chip xuống dòng; nút đóng thiếu vai trò hoặc tên; emoji ở mọi chữ của app và hộp; vùng bấm của thành phần dựng thử. Máy chụp mặc định nạp app sau sự kiện load như trang thật.

Thử phá máy kiểm (21/11, khung 390): nút cao 38, chữ 12, chip tràn tới x446 trong thẻ: máy báo đủ ba lỗi. Trên mã main v680 các kịch bản mới trượt đúng lỗi Codex báo (1339 chồng 2,4px ở 360; "Thu tiền 0 đ" hai dòng; nút đóng Trợ lý "Dong"; màu vỏ `#50DBF2`).

## Còn lại, ghi thật

- Chưa kiểm máy thật: Safari và app ngoài màn hình chính trên iPhone (UI01), Android, bàn phím ảo, vùng an toàn, cỡ chữ hệ thống.
- Chưa kiểm vai quầy, bếp, kho, kế toán: kịch bản PR A dùng vai quản trị.
- Thanh đáy chỉ kiểm bằng phép thử thành phần; kịch bản màn Tính tiền và Đối soát thật nằm ở PR nhóm màn.
- 280 hàm màn và 83 hàm hộp: máy chụp mới có 17 kịch bản; danh mục đầy đủ bổ sung theo từng PR nhóm màn.
