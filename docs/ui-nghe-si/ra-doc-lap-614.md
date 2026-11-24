# Rà độc lập 82 mục giao diện mới (#614, v691)

Báo cáo của Codex trên #614 (comment 7124225204) liệt kê UI17 tới UI98 cùng 45 chip dưới 44 điểm và 22 nhãn ngắn xuống dòng. Tệp này ghi kết quả đối chiếu với bản v691 đã rà (d270a2b) và phần sửa thêm.

## Cách đo

- `cong_cu/ui_b/ra_muc.cjs` mở đúng màn của từng mục bằng hàm vẽ thật, dữ liệu thử lấy từ hàm máy chủ thật (`cong_cu/ui_b/du_lieu_that.py`, không chạm site), rồi đo trong Chromium: emoji, chữ dưới 13, vùng bấm dưới 44, nút gãy chữ, nút dính nhau, ô chọn hệ điều hành, màu cũ, hàng chip xếp dọc, chữ thô.
- Mỗi mục có kết luận còn, khép hoặc không rõ. Không rõ khi chữ gợi ý không có trên màn, để không khép nhầm.
- Chạy cùng công cụ với `--app` là app_bep.js của d270a2b để có kết quả trước khi sửa.
- `cong_cu/ui_b/quet_man.cjs` quét 134 màn cho chip nhỏ và nhãn xuống dòng.

```
node cong_cu/ui_b/ra_muc.cjs --ra /tmp/ra --khung 390x844 [--app tệp] [--ma UI62,UI85]
node cong_cu/ui_b/quet_man.cjs --ra /tmp/quet [--khung 360x780] [--app tệp]
```

## Kết quả

- Trên d270a2b: 48 mục đã khép từ v691 vòng trước, 35 mục còn. Không sửa lại 48 mục này.
- Trên SHA cuối: 83 mục khép ở cả bốn khung 360x780, 390x844, 1366x768, 683x384 (Chromium).
- Quét 134 màn, 390x844: chip và nút dưới 44 từ 44 còn 0; nhãn xuống dòng từ 22 còn 8. Tám chỗ còn lại là ô số liệu nhiều tầng có chủ ý (Đặt bàn 4, Tuyển dụng 3, Đối soát chuyển khoản 1): mỗi tầng một khối riêng (nhãn, số, dòng phụ), không phải chữ bị ép.
- Chế độ tắt: `so_che_do_tat.py --goc d270a2b` so 60 màn của máy chụp, 0 điểm ảnh khác. Phạm vi là 60 màn đó, không phải mọi màn của app.
- Ba nhãn đổi ở cả hai chế độ, có chủ ý: Chức danh riêng (thay Title riêng), Số tiền mỗi tháng (đ), Chọn nhà cung cấp (bỏ "trong danh mục").

## Sửa theo loại

| Loại | Cách sửa chung |
|---|---|
| A emoji | Ba emoji mới của danh mục Zalo chung (🚨 🚀 🛠) vào bảng biểu tượng; ca chốt mọi emoji trong nguồn phải có trong bảng |
| B nhãn gãy | Hàng nút ngang hoặc lưới nhiều cột: một nút gãy hai dòng thì cả hàng xếp dọc, nút rộng hết (`uiBVfDoc`, `uib-hang-doc`) |
| C vùng bấm | Chip POS thành lớp `posc`; công tắc Cài đặt lõi viền trong suốt 7 điểm; nút min-height viết thẳng 36 tới 42 lên 44; ô tích trong nhãn tính vùng bấm theo nhãn; hai nút xếp dọc dính nhau có khe 12 (`uiBCachNut`) |
| D chữ nhỏ | Sau mỗi lần vẽ, đo cỡ chữ tính ra; từ 9.5 tới dưới 13 thì thêm lớp lên 13 (`uiBCoChu`). Dưới 9.5 là ký hiệu trang trí, không đổi |
| E ô chọn, chữ thô | Ô chọn thành nút mở hộp chọn có tìm (`uiBChon`), giữ select gốc để mã cũ đọc giá trị, phát input và change; mã nhóm Zalo gập; ô bot hiện tên |
| F màu cũ | Nền teal, tím trên nút, chip sang mực; nền nhạt sang `--ui-header-tint`; hổ phách sang `--ui-cho` |

## Ca kiểm và làm hỏng có chủ ý

- `_ui_b_ra_doc_lap_v691` (chạy hàm thật trong node, `hanh_vi/ui_b_ra_doc_lap_v691.js`): mã mới xanh, ba tệp phần của d270a2b đỏ ở cả bốn nhóm ý.
- `_ui_b_bang_phu_moi_emoji`: đỏ trên bảng cũ (🚨 🚀 🛠), xanh bây giờ.
- Làm hỏng có chủ ý, bắt được 10 trên 10: ba chỗ trong 51-cai-dat-loi.js (ca node), sáu chỗ trong 81-ui-b.js (công cụ rà trên Chromium: `uiBCoChu`, `uiBCachNut`, `uiBChon`, viền công tắc, xếp dọc hàng nút, min-height 44), một bộ chọn ngoài `html.ui-b` có dấu phẩy ngoài cùng (`kiem_khai_bao.py` vẫn bắt sau khi sửa cách tách bộ chọn).
- Bàn phím (Codex #614 P2 trên e4b8594): dòng của hộp chọn có tabindex, vai option, Enter và Space chọn qua bộ phím chung, mũi tên lên xuống đi giữa các dòng; mở hộp thì tiêu điểm vào dòng đang chọn, chọn xong về lại nút. Ca `_ui_b_hop_chon_phim_v691` đỏ trên e4b8594, xanh bây giờ; làm hỏng 3 chỗ, bắt 3. Chromium: mở bằng nút, mũi tên xuống, Enter đổi giá trị, change phát một lần.
- Ô chọn mới thử thật: mở hộp, chạm Techcombank, select đổi giá trị, input và change phát một lần, hộp đóng, nút cao 45.

## Chưa kiểm

- WebKit: máy làm việc không tải được trình duyệt WebKit (máy chủ tải bị chặn). Chưa kiểm.
- 18 hàm chưa có dữ liệu thử; màn Mẫu in ấn lỗi dữ liệu thử ở cả d270a2b, không phải lỗi app.
- Cỡ chữ điện thoại 150%, 200%, bàn phím ảo, máy thật.

## Bảng 83 mục

| Mã | Nhóm | Màn | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| UI17 | A | cdl | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI18 | A | cdl_loai | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; bảng biểu tượng, ca _ui_b_bang_phu_moi_emoji |
| UI19 | A | cdl_chude | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; bảng biểu tượng, ca _ui_b_bang_phu_moi_emoji |
| UI20 | A | cdl_bot | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI21 | A | rcv | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI22 | A | stock | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI23 | A | stock | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI24 | A | stock | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI25 | A | sotay | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI26 | A | bep | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI27 | A | km | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI28 | A | km | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI29 | A | km | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI30 | A | nbanh | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI31 | A | xksi | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI32 | A | xktra | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI33 | A | hdtao | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI34 | A | hd | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI35 | A | rnd | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI36 | A | vdtao | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI37 | A | kk | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI38 | A | mfg | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI39 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI40 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI41 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI42 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI43 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI44 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI45 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI46 | A | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI47 | A | pos_mon | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI48 | B | cdl_nhom | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI49 | B | cdl_nhom | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI50 | B | cdl_bh | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI51 | B | tq | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBVfDoc, uib-hang-doc |
| UI52 | B | lich | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI53 | C | rcv | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI54 | C | stock | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI55 | C | km | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI56 | C | gvt | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI57 | C | hhgt | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI58 | C | xksi | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI59 | C | xktra | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI60 | C | dm | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI61 | C | ph | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI62 | C | cdl_bh | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; posc, cdl-tg, uiBCachNut, vùng bấm 44 |
| UI63 | C | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI64 | C | pos | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI65 | C | pos_mon | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; posc, cdl-tg, uiBCachNut, vùng bấm 44 |
| UI66 | C | bt | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; posc, cdl-tg, uiBCachNut, vùng bấm 44 |
| UI67 | D | cdl | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI68 | D | dm | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI69 | D | tk | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI70 | D | tdh | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI71 | D | hhgt | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI72 | D | muavu | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI73 | D | km | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI74 | D | nbanh | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI75 | D | sk | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI76 | D | stock | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI77 | D | xksi | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI78 | D | xktra | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI79 | D | rnd | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI80 | D | vdtao | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI81 | D | pos | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBCoChu, lớp uib-c13 |
| UI82 | D | cdl_bot | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI83 | E | cdl_nhom | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI84 | E | cdl_nhom | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI85 | E | tk | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI86 | E | dm | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI87 | E | sk | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI88 | E | tq | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI89 | E | lich | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; uiBChon; ca _ui_b_ra_doc_lap_v691 |
| UI90 | F | km | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI91 | F | stock | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI92 | F | hhgt | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI93 | F | xksi | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI94 | F | xktra | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI95 | F | dm | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI96 | F | dgq | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
| UI97 | F | pos | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| UI98 | F | pos_mon | Đã sửa ở SHA cuối | đỏ trên d270a2b, xanh SHA cuối; màu cũ trên nút, chip sang bảng mới |
| VD-CHIP | B | vd | Đã sửa ở d270a2b | khép trên d270a2b và SHA cuối |
