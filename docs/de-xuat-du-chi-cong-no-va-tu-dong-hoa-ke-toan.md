# Đề xuất: Dự chi công nợ (đợt 10 và 20), tự soạn APP cho thu mua, tự động hoá kế toán

Ngày 12/11/2026. Bản đề xuất, CHƯA có code. Mở để Codex góp ý trước khi viết code trong một PR.

## Tóm tắt cho anh Việt

**Vấn đề.** Tiền trả nhà cung cấp đang làm bằng bảng Excel tay ("Dự chi công nợ tháng 10/2026") rồi lập từng hồ sơ thanh toán (APP) trên app, duyệt từng tờ. Hạn trả trên ERP không dùng được: gần như mọi hoá đơn mua có hạn trả bằng đúng ngày hoá đơn, nên màn Công nợ phải trả báo cả 350 tờ đều "Quá hạn". Kế toán và thu mua mỗi bộ phận mới có 1 việc trong Cài đặt tự động hoá.

**Việc làm.**
1. Màn mới **Dự chi công nợ**: máy soạn sẵn mỗi đợt (ngày 10 và 20), Vin thương lượng trả hết hoặc trả một phần từng hoá đơn, máy tính phần gia hạn và mang sang đợt sau, chốt đợt thì máy lập sẵn APP.
2. Thu mua: máy tự soạn APP (theo đợt, hoá đơn trả ngay, khoản định kỳ) và 4 việc nhắc (giao trễ, hoá đơn chưa về, giá lệch, thẻ điểm NCC).
3. Kế toán: 6 việc mới, trong đó AI chỉ đọc và soạn nháp (UNC khách, tệp đối soát mẫu lạ, ảnh hoá đơn hoàn ứng, gợi ý tài khoản), luật cứng rà soát mỗi đêm, danh sách chốt tháng.

**Kết quả sẽ thấy.** Không còn bảng Excel dự chi; mỗi đợt anh duyệt một lần thay vì khoảng 30 lần; công nợ còn lại sau mỗi đợt luôn đúng số ERP; kế toán và thu mua mở Việc cần làm là có sẵn việc.

**Anh Việt đã chốt (12/11/2026, đồng ý mọi điểm em khuyên):**
1. Hạn trả NCC: ô "Số ngày được nợ" trên hồ sơ NCC, máy gợi số theo lịch sử, Vin xác nhận dần, áp cho hoá đơn từ nay.
2. Duyệt cả đợt một lần; APP sinh ra mang sẵn dấu duyệt, chờ chuyển tiền.
3. Ngưỡng nhắc giá lệch: trên 5%, sửa được trong Cài đặt.
4. Thứ tự: Dự chi và APP trước, kịp đợt 10/12.

**Còn chờ anh:** Vin dùng tài khoản nào trên app, mang vai gì; hộp thư hoadon@ cho phần E (mục E dưới).

## Số liệu thật trên site (đọc 12/11/2026, chỉ đọc)

Nguồn: `Vagabond Ho So TT` và bảng con, `Purchase Invoice` đã ghi sổ còn nợ, màn Công nợ phải trả, màn Cài đặt tự động hoá.

| Điều đo | Số |
|---|---|
| Hồ sơ thanh toán từ 13/08 tới 12/11 | 357 (Uyên lập 219, chị Dung 135, anh Việt 3) |
| Đã chi qua hồ sơ | 332 hồ sơ, 6.015.105.945 đ (T8 85 tr, T9 2,20 tỷ, T10 2,20 tỷ, T11 tới nay 1,53 tỷ) |
| Theo loại đã chi | Chi từ TK công ty 3,05 tỷ; Công nợ NCC 2,54 tỷ; Hoàn ứng 320 tr; Hoàn ứng có HĐ 104 tr |
| Ngày chi NCC dồn vào | ngày 11 (33), 14 (49), 22 (32): 114 trên 195 hồ sơ NCC |
| Số ngày có chi NCC trong tháng | T9: 13, T10: 7, T11 (tới 12/11): 4. Mọi người đang tự dồn về đợt |
| Trung vị thời gian duyệt | lập tới kế toán duyệt 1,9 giờ; kế toán tới giám đốc 6,8 giờ; giám đốc duyệt tới ngày chuyển 1 ngày (90%: 3 ngày) |
| Dòng hoá đơn NCC đã trả qua hồ sơ | 576 dòng, 9 dòng trả một phần |
| Tuổi hoá đơn lúc trả | trung vị 22 ngày, 25%: 12 ngày, 90%: 44 ngày |
| Hạn trả so với ngày hoá đơn | 574 trên 576 dòng: hạn trả bằng hoặc trước ngày hoá đơn |
| Hoá đơn mua còn nợ hôm nay | 350 tờ, 54 NCC, 1.442.665.295 đ |
| Trong đó phí sàn cấn trừ | khoảng 427 tr (Grab, Grab Việt Nam, Foody, Be, Xanh SM, Shinhan) |
| Tuổi nợ | 0 tới 30 ngày 373 tr; 31 tới 60 ngày 482 tr; 61 tới 90 ngày 233 tr; trên 90 ngày 355 tr |
| Khoản định kỳ chi từ TK công ty | Adecco 6 lần 2,04 tỷ; thuê mặt bằng Nguyễn Hữu Phước 3 lần 253 tr; Điện lực 7 lần 146 tr |

Bảng tay anh gửi (tháng 10/2026) so với ERP hôm nay. Bảng tay chốt ở một thời điểm nên lệch là bình thường, nhưng cho thấy vì sao số còn nợ phải luôn đọc từ ERP lúc soạn:

| NCC | Bảng tay | ERP 12/11 |
|---|---|---|
| In ấn Printeco | 362.690.082 | 231.105.722 |
| Bao bì PHP | 386.467.200 | 437.454.000 |
| Kanz Studio Design | 79.083.320 | 79.083.320 |

Bảng tay: Tổng 1.429.002.175 = TT 20/10 380.342.103 + TT 20/11 391.605.950 + Gia hạn 657.054.122 (cộng lại khớp). Ghi chú có "TT 1 phần HD 74" (trả một phần) và "cọc 20% Hộp giáng sinh" (trả trước theo đơn mua, chưa có hoá đơn).

Không sửa dữ liệu quá khứ: các hoá đơn cũ có hạn trả sai giữ nguyên; màn mới chỉ tự tính hạn dự tính để xếp thứ tự.

## Phần A. Dự chi công nợ (đợt 10 và 20)

### Luồng
1. Ngày 7 và 17 (giờ sửa được trong Cài đặt tự động hoá), máy soạn **đợt nháp** cho ngày 10 hoặc 20 và đưa việc vào Việc cần làm của Vin. Đợt nháp gồm:
   - Mọi hoá đơn mua đã ghi sổ còn nợ, nhóm theo NCC. **Số còn có thể đề nghị = `outstanding_amount` trừ phần APP khác còn hiệu lực đang giữ**, tính bằng đúng `phan_bo_app.dang_giu(hoa_don=...)` (một nguồn, không tự tính lại), đọc lúc soạn, không chép số từ đợt trước. Hoá đơn có APP lập riêng hoặc từ `app_tra_ngay` đang giữ một phần thì màn hiện rõ phần đang giữ và chỉ cho chọn phần còn lại (Codex PR #556 vòng 1).
   - Khoản cọc theo đơn mua có lịch thanh toán tới hạn (đi đường trả trước NCC đã có, v551, `tra_truoc_ncc.py`, `coc_app.py`).
   - Khoản định kỳ (thuê mặt bằng, Adecco, điện): máy gợi từ lịch sử 3 tháng (cùng người nhận ít nhất 3 tháng liền), người quản trị xác nhận một lần trong Cài đặt.
   - Ghi chú thương lượng và ngày hẹn trả của đợt trước, gắn theo hoá đơn.
2. Phí sàn cấn trừ (Grab, ShopeeFood, Be, Xanh SM, Shinhan...) tách thành một nhóm riêng "Cấn trừ, không chuyển khoản", không cộng vào tổng đợt.
3. Vin mở từng NCC: bấm **Trả hết**, hoặc gõ số trả từng hoá đơn. Máy tính ngay **Gia hạn = còn nợ - trả đợt này**, Vin ghi chú và chọn đợt hẹn trả.
4. Dòng đầu màn: tổng đợt, số dư MB mới nhất theo SePay, còn thiếu hay dư.
5. Xếp thứ tự gợi ý (luật cứng, Vin quyết): quá hạn dự tính lâu nhất; NCC nguyên vật liệu chính; khoản nhỏ trả hết cho gọn.
6. Gửi kế toán soát, rồi giám đốc duyệt (theo lựa chọn của anh, xem câu hỏi Q-D2).
7. **Chốt đợt**: máy gọi đường lập APP đang có cho từng NCC (`ho_so_tt.tao(ncc, hoa_don=[{hoa_don, so_tien}])` đã hỗ trợ trả một phần), khoản định kỳ đi `tao_chi_cong_ty`, khoản cọc đi đường trả trước NCC. Xuất danh sách chuyển khoản MB. Sau đó dò SePay, đính UNC, thư báo NCC giữ nguyên như hiện nay.
8. Báo cáo: dự chi 4 đợt tới theo nhóm NCC; công nợ còn lại sau đợt.

### Mô hình dữ liệu dự kiến
- Doctype mới `Vagabond Dot Chi` (Đợt chi): mã DC-YY-MM-10 / DC-YY-MM-20, ngày đợt, trạng thái (Nháp máy soạn, Đang thương lượng, Chờ kế toán soát, Chờ giám đốc duyệt, Đã chốt, Đã chi xong, Huỷ), tổng đề xuất, tổng trả, tổng gia hạn, số dư MB lúc soạn, người soát, người duyệt.
- Bảng con `Vagabond Dot Chi Dong`: NCC, nhóm NCC, loại dòng (Hoá đơn, Cọc theo đơn mua, Định kỳ), hoá đơn mua hoặc đơn mua, còn nợ lúc soạn, trả đợt này, gia hạn (máy tính), hạn dự tính, ghi chú thương lượng, đợt hẹn trả, APP đã sinh.
- Trường mới trên Supplier: số ngày được nợ (theo lựa chọn 1 của anh), hoặc dùng `Payment Terms Template` lõi ERPNext để hoá đơn MỚI tự có hạn trả đúng (xem Q-D3).
- Một hoá đơn không nằm trong hai đợt còn hiệu lực; số trả không vượt "còn nợ trừ phần APP khác đang giữ", đọc lại DƯỚI KHOÁ lúc chốt bằng `phan_bo_app.dang_giu(khoa=True, ...)` rồi `phan_bo_app.kiem()`; dòng nào vượt thì dừng dòng đó, báo Vin số mới, không chốt nửa vời.

## Phần B. Thu mua: tự soạn APP và việc nhắc

Thêm vào sổ đăng ký `VIEC` của `viec_tu_dong.py` (bộ phận Thu mua), mỗi việc là việc soạn sẵn trong Việc cần làm:

| Mã đề xuất | Việc | Máy soạn | Người làm |
|---|---|---|---|
| `du_chi_dot` | Dự chi đợt 10 và 20 | Ngày 7 và 17 soạn đợt nháp | Vin thương lượng, gửi soát |
| `app_tra_ngay` | APP cho hoá đơn trả ngay | Hoá đơn của NCC trả ngay vừa ghi sổ thì soạn APP nháp | Uyên bấm Gửi kế toán |
| `chi_dinh_ky` | Khoản chi định kỳ | Trước hạn 3 ngày soạn APP chi từ TK công ty | Người lập soát số, gửi |
| `giao_tre` | Nhắc NCC giao trễ | Đơn mua Đang xử lý quá ngày giao hẹn | Thu mua gọi NCC, ghi ngày hẹn mới |
| `hoa_don_chua_ve` | Hoá đơn chưa về | Đã nhập kho quá 7 ngày chưa có hoá đơn mua | Thu mua nhắc NCC xuất hoá đơn |
| `gia_lech` | Giá lệch | Giá hoá đơn cao hơn lần mua trước quá ngưỡng | Thu mua xác nhận hoặc khiếu nại trước khi lập APP |

Thêm thẻ điểm NCC hàng tháng (đúng hẹn giao, đủ số, giá ổn, hoá đơn đúng hẹn) và nút **Soạn tin xin gia hạn**: AI soạn nháp từ số liệu thật của NCC đó, Vin sửa rồi tự gửi. Máy không tự gửi tin cho NCC.

## Phần C. Kế toán

Nguyên tắc: AI soạn nháp, luật cứng kiểm, người bấm duyệt. Theo quyết định 30/09/2026 của anh, hạch toán khoản đặc thù do kế toán làm; máy chỉ gợi ý.

| Mã đề xuất | Việc | Ghi chú |
|---|---|---|
| `unc_ai` | AI đọc ảnh UNC khách gửi | Lấy số tiền, ngày, người chuyển, nội dung; khớp giao dịch SePay; soạn phiếu thu kèm UNC. Kế toán bấm Ghi sổ. Không gửi số điện thoại, email khách cho AI. |
| `mau_doi_soat_ai` | AI đọc tệp đối soát mẫu lạ | Chỉ khi `doi_soat_mau.py` không nhận ra mẫu. AI đề xuất ánh xạ cột, kế toán xác nhận một lần, máy lưu mẫu. Không gọi AI cho tệp mẫu đã biết. |
| `hoan_ung_ai` | AI đọc ảnh hoá đơn, biên nhận hoàn ứng | Điền sẵn dòng; tổng tiền máy tính lại từ các dòng, không tin tổng của mô hình. |
| `goi_y_tk` | Gợi ý tài khoản kèm lý do | Mở rộng cơ chế nhớ lựa chọn lần trước đã có; kế toán xác nhận, có xác nhận hàng loạt. |
| `ra_soat_dem` | Rà soát mỗi đêm (luật cứng) | Hoá đơn mua trùng số và NCC; hoá đơn đầu vào bị NCC huỷ hoặc thay thế sau khi đã ghi sổ (trạng thái m-invoice); APP đã chuyển chưa khớp SePay; tiền về không mã đơn quá 2 ngày; tạm ứng quá hạn chưa hoàn. Gửi nhóm Zalo Kế toán, mỗi dòng mở thẳng việc. CHỈ LIỆT KÊ, không sửa chứng từ. |
| `chot_thang` | Danh sách chốt tháng | Máy tự đánh dấu bước đã xong (hoá đơn đã nối phiếu nhập, sao kê khớp số dư cuối tháng, chênh lệch kiểm kê đã chọn tài khoản...). Kết chuyển do kế toán bấm. |

AI dùng khoá API Trợ lý đang có, chạy việc nền như `tuyen_dung_ai.py` ("đã xếp" không phải "đã xong"), nhiệt độ thấp, kết quả ghi vào ô nháp.

**AI không bao giờ tự làm:** phát hành, huỷ, thay thế hoá đơn điện tử; ghi sổ, huỷ chứng từ; sửa dữ liệu đã ghi sổ; duyệt chi, chuyển tiền; kết chuyển cuối kỳ; kê khai thuế.

## Phần E. Bản thể hiện hoá đơn NCC tự đính vào hồ sơ APP

**Hiện trạng.** Bước tay duy nhất còn lại của APP là tải bản thể hiện PDF hoá đơn NCC rồi đính vào. Ngày 20/08 đã thử kéo PDF qua API M-Invoice (`minvoice_tep.py`), mọi biến thể đường tải trả lỗi 400; 21/08 anh chốt dùng nút tải lên (`ho_so_tt.dinh_tep`), nhịp kéo đã gỡ khỏi `hooks.py`. Đọc site 12/11: từ 13/08 có 233 tệp tải tay lên hoá đơn mua (Uyên 223, chị Dung 9), 197 PDF và 36 ảnh JPG. Site chưa có hộp thư nhận nào bật (`Email Account` chỉ có erp@, purchasing@, sales@, đều chỉ gửi).

Về giá trị: tệp XML là dữ liệu gốc của hoá đơn điện tử, PDF chỉ là bản thể hiện để đọc. Kế toán lưu được cả hai thì chắc hơn chỉ lưu PDF.

**E1 (em khuyên): đọc hộp thư hoadon@thevagabondpatisserie.com.** Nhà cung cấp và đơn vị hoá đơn điện tử của họ thường gửi thư kèm XML và PDF. ERP đọc hộp thư này, khớp MST bên bán, ký hiệu, số hoá đơn với hoá đơn mua (và bản ghi `MInvoice Invoice`), đính **PDF gốc của NCC và tệp XML** thẳng vào hoá đơn mua (như `dinh_tep` đang làm), ghi Comment nguồn "tự đính từ thư ngày...". Lúc lập APP thì tệp đã nằm sẵn.
- Kiểm trước khi đính: số tiền, MST, ngày trong XML khớp hoá đơn mua; lệch thì không đính, đưa việc cho kế toán xem.
- Thư chỉ có đường link tra cứu, hoặc NCC không gửi thư: đưa việc "Thiếu bản thể hiện" cho thu mua, nút tải tay giữ nguyên.
- Thư lạ, tệp lạ: không mở tệp chạy được, chỉ nhận .xml, .pdf, .zip (bóc lấy hai loại trên).

**E2: dựng bản thể hiện từ XML** khi có XML mà không có PDF: máy in một trang đủ nội dung hoá đơn từ XML, ghi rõ "Bản dựng từ tệp XML gốc". Chỉ làm nếu chị Dung chấp nhận.

**E3: thử lại đường XML của M-Invoice** (`.../download/invoice.xml`, thấy trong bundle trang quản lý ngày 20/08) bằng token đang có, chỉ đọc. Chạy được thì hoá đơn có trên M-Invoice không cần chờ thư.

**Anh cần làm cho E1:** xác nhận NCC đang gửi hoá đơn về hoadon@, và tự dán mật khẩu hộp thư vào ô Email Account máy dựng sẵn (máy không nhập mật khẩu).

## Phần D. Kế hoạch làm trong một PR

1. Dự chi đợt + chốt đợt sinh APP + hạn trả NCC (không cần AI). Mục tiêu kịp đợt 10/12/2026.
2. Việc nhắc thu mua (`app_tra_ngay`, `chi_dinh_ky`, `giao_tre`, `hoa_don_chua_ve`, `gia_lech`).
3. Rà soát đêm và chốt tháng (luật cứng).
4. Bản thể hiện tự đính (phần E1, E3; E2 khi chị Dung đồng ý).
5. Phần AI (`unc_ai`, `mau_doi_soat_ai`, `hoan_ung_ai`, `goi_y_tk`, soạn tin gia hạn).

Mỗi phần: phép thuần tách khỏi phần chạm Frappe, ca kiểm trong `vagabond/khung/kiem_thu/`, hàm whitelist thêm vào `thu_cua_ngo.py`, mục sổ tay `mua-hang.md` và `ke-toan.md`, mỗi màn mới có chỗ trên sidebar desktop.

## Câu hỏi cho Codex

- **Q-D1.** Dựng doctype mới `Vagabond Dot Chi` hay thêm ô "đợt" vào `Vagabond Ho So TT` và gom theo đợt? Em nghiêng doctype mới vì đợt có nhiều NCC, còn hồ sơ đang chặn một NCC một hồ sơ.
- **Q-D2.** Nếu anh chọn duyệt cả đợt một lần: APP sinh ra mang `fin_boi`, `gd_boi` của người duyệt đợt kèm ghi chú "duyệt theo đợt DC-..." có làm yếu kiểm soát hai cấp ở `ho_so_tt.py` không (người lập không tự duyệt, đúng thứ tự)? Cách ghi dấu vết nào đủ cho kiểm toán?
- **Q-D3.** Hạn trả cho hoá đơn mới: dùng `Payment Terms Template` gắn trên Supplier (lõi ERPNext tự tính `due_date` và `payment_schedule`) hay ô riêng của app? Đường sinh hoá đơn mua tự động từ m-invoice có tôn trọng điều khoản trên Supplier không?
- **Q-D4.** Chốt đợt gọi `ho_so_tt.tao` lặp theo NCC: nếu một NCC lỗi giữa chừng thì xử lý thế nào để không có đợt nửa chốt (gói mỗi NCC một lượt riêng, ghi trạng thái từng dòng, cho chốt lại phần lỗi)?
- **Q-D5.** Tách phí sàn cấn trừ: nhận diện theo nhóm NCC hay theo danh sách NCC trong `can_tru_san.py`? Tránh gõ cứng tên.
- **Q-D6.** AI đọc UNC và ảnh hoá đơn: có rủi ro dữ liệu cá nhân hay chi phí nào cần chặn thêm ngoài cách `tuyen_dung_ai.py` đang làm?
- **Q-D7.** Phần E1: khớp thư hoadon@ với hoá đơn mua theo MST, ký hiệu, số hoá đơn đọc từ XML có đủ chắc không, hay cần thêm kiểm chữ ký số trong XML? Kiểm chữ ký số thì thư viện nào chạy được trên CI (Python 3.11, không cài thêm gói nặng)?

## Ngoài phạm vi
- Không sửa hạn trả, số tiền hay trạng thái của hoá đơn, hồ sơ đã ghi sổ hoặc đã chi.
- Không tự chuyển tiền, không gọi API ngân hàng để chi.
- Không đổi cách dò SePay và thư báo NCC hiện có.
