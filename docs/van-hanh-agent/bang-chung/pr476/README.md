# Bằng chứng màn chọn bộ sao kê

Ảnh 390x844 chụp bằng Chromium headless từ `file:///tmp/476-man-bo.html`, dùng CSS thật trong `00-nen.js`, mã màn thật `23-khop-sepay.js` và API giả lập. Không phải site thật; không chứng minh quyền, ghi sổ hay số dư thực tế. Dữ liệu thử: 450.000.000 + 264.138.056 = 714.138.056 đồng.

- [APP](app-390x844.png)
- [Công nợ](cong_no-390x844.png)
- [TTNB](ttnb-390x844.png)
- [Hoàn tiền](hoan_tien-390x844.png)
- [Tạm ứng](tam_ung-390x844.png)

Ca thao tác chạy bằng `node vagabond/khung/kiem_thu/gia_lap_trang.js --bo-sao-ke`: 19 ca. Bao gồm từng luồng chọn nhiều dòng, giữ lựa chọn qua tìm và trang, nút Gán tắt khi thiếu và sáng khi đủ. Ca riêng kiểm khác ngân hàng, bị người khác giữ, retry và bấm hai lần. DOM giả không đo CSS; ảnh trên do trình duyệt thật vẽ.

## Bảng mười nhóm nghiệm thu

| Nhóm | Ca hoặc tệp chạy thật | Đường lỗi được kiểm |
|---|---|---|
| 1. Lương tách lệnh | `thu_bo_sao_ke_595`: APP tự dò hai dòng cùng mã, một PE và hai phân bổ lõi qua cửa thanh toán | Tổng714.138.056 qua450.000.000+264.138.056, retry không nhân PE |
| 2. Chọn tay | `gia_lap_trang.js --bo-sao-ke`, `hanh_vi/bo_sao_ke_476.js` | Tổng thiếu/đủ, cùng nguồn, giữ lựa chọn qua tìm/trang |
| 3. Thiếu/thừa/sai nguồn | `thu_bo_sao_ke_469`, `thu_phan_con_595`, `thu_doi_soat_sepay` | Phép chung xet_bo, mapping, chiều, số dư, chủ cũ |
| 4. Một dòng nhiều phiếu | `thu_bo_sao_ke_595`: APP một BT trả hai phiếu; `thu_sepay_mb_247`: Cấp quỹ bộ | Phần giữ và lõi không trừ hai lần; không vượt dư |
| 5. Tranh chấp | `bench_thu/bo_sao_ke_476`, `thu_dong_thoi_476`, `do_khoa_476` | Hai người tranh BT; SI có PE nháp/đã ghi sổ; current read; không khóa phiếu không liên quan |
| 6. Đủ luồng | `thu_bo_sao_ke_595`: TTNB, hoàn tiền, hoàn ứng, công nợ trả hai kỳ, tạm ứng; `thu_sepay_mb_247`: cấp quỹ bộ | Nhiều BT/phiếu, nhiều Customer/PE, ghi từng PE, hủy, retry |
| 7. Bỏ bộ | `thu_bo_sao_ke_595`: APP chọn/bỏ, từ chối/hủy, công nợ bỏ bộ; `thu_sepay_mb_247`: hủy cấp quỹ | Không nhả phần phiếu khác, không bỏ khi bút toán còn sống |
| 8. Ngoại lệ | `thu_bo_sao_ke_595`: FIN không được bỏ SePay; Manager ghi kèm lý do; DOM `hanh_vi/chay.js` | Đúng vai, lý do bắt buộc, Chờ đối chiếu sau dựa trên lõi |
| 9. Sổ tay | `thu_so_tay_554._cau_that` | Câu thật của chị Dung tìm đúng mục đứng đầu bằng chon_muc thật |
| 10. Đột biến | Nhật ký kiểm và bảng đột biến trong bàn giao cuối | Bỏ kiểm tổng/nguồn/giữ, stale SI/PE, giữ tồn và DOM phải bị bắt |

Bảng là ánh xạ ca kiểm, không tự khẳng định bench SHA cuối đã xanh. Kết quả cuối phải đọc run CI/bench của đúng SHA trong bàn giao PR.
