# Kế toán

## Cách hạch toán cấn trừ công nợ: chọn đúng đường theo trường hợp
Từ khoá: cấn trừ, bù trừ, đối trừ, trừ nợ, cấn nợ, cấn cọc, clearing, offset, netting, set-off, bút toán cấn trừ, bù trừ công nợ, Journal Entry, payment reconciliation

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Thu mua | Công nợ phải trả (/cong-no-phai-tra) | [[Cấn trừ công nợ]] |

Không có một nút cấn trừ chung. Tuỳ khoản tiền đã đi đường nào thì chọn đúng chỗ, máy tự lập bút toán.

| Trường hợp | Làm ở đâu |
|---|---|
| Đã có phiếu chi hoặc phiếu cọc trên ERP, nay có hoá đơn | Công nợ phải trả, [[Cấn trừ công nợ]], chọn khoản đã trả |
| Tiền đã trả trước khi lên ERP | Công nợ phải trả, [[Cấn trừ công nợ]], chọn [[Đã trả trước khi lên ERP]] |
| Chi trước trên hồ sơ thanh toán, hoá đơn về sau | Hồ sơ thanh toán, [[Nối hoá đơn đến sau]] |
| Phí sàn Grab, Shopee, Be đã bị sàn giữ | Phiếu Vagabond Can Tru San trên Desk |
| Một đối tác vừa là khách vừa là nhà cung cấp | Bút toán Nợ 331 / Có 131, rồi Đối chiếu thanh toán trên Desk |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Không sinh bút toán mới | | Cấn phiếu chi có sẵn vào hoá đơn: máy chỉ phân bổ |
| 331 (đúng hoá đơn) | 11211 hoặc tài khoản kế toán chọn | Duyệt khoản đã trả trước khi lên ERP |
| 331 (NCC xuất phí) | 131 (khách công nợ sàn) | Xác nhận phiếu cấn trừ phí sàn |

**Lưu ý**
- Không lập thêm phiếu chi hay chuyển tiền thêm chỉ để công nợ về 0.
- Hạch toán theo bản chất từng khoản là việc của kế toán, máy chỉ đặt mặc định.

## Cấn khoản đã trả vào hoá đơn mua
Từ khoá: cấn trừ công nợ, cấn cọc, cấn khoản đã trả, phân bổ thanh toán, trừ nợ nhà cung cấp, đối trừ, offset, allocate, clearing, UNC

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Công nợ phải trả (/cong-no-phai-tra) | [[Xác nhận cấn, không chuyển tiền]] |

Dùng khi ERP đã có phiếu chi hoặc phiếu cọc đã ghi sổ còn tiền chưa phân bổ, và hoá đơn mua cùng nhà cung cấp còn nợ.

**Các bước**
1. Mở Công nợ phải trả, gõ tên nhà cung cấp hoặc số hoá đơn vào ô tìm.
2. Ở dòng hoá đơn, bấm [[Cấn trừ công nợ]].
3. Chọn khoản đã trả trong danh sách (mỗi dòng ghi còn bao nhiêu và số UNC).
4. Sửa ô Số tiền cấn nếu cần (mặc định là số lớn nhất được cấn).
5. Có UNC thì bấm [[Đính UNC]].
6. Bấm [[Xác nhận cấn, không chuyển tiền]], đọc lại số tiền và hoá đơn rồi đồng ý.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Khoản cọc ... chưa đối chiếu đủ tiền trên sao kê | Khớp sao kê ngân hàng cho khoản đó trước |
| Công nợ vừa thay đổi. Tải lại hóa đơn trước khi cấn cọc. | Tải lại màn rồi làm lại |
| Hoá đơn ngoại tệ | Dùng [[Đối chiếu thanh toán lõi (kế toán)]] ở nút [[Xem chứng từ]] |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Không sinh bút toán mới | | Phiếu chi gốc (Nợ 331 / Có 112) phân bổ vào hoá đơn |

**Lưu ý**
- [[Chỉ lưu UNC]] chỉ đính tệp, không làm giảm nợ.
- Mất mạng giữa chừng thì bấm [[Kiểm lần cấn đang chờ]], không cấn lần mới.
- Không có khoản đã trả nào thì app tự mở màn Đã trả trước khi lên ERP.

## Hoá đơn đã trả tiền trước khi lên ERP: ghi giảm công nợ
Từ khoá: đã trả trước khi lên ERP, trả trước ERP, số dư đầu kỳ, công nợ cũ, cấn trừ, bù trừ, giảm nợ, hoá đơn cũ còn nợ, tài khoản tạm, 11211, opening, Printeco

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua, Kế toán | Công nợ phải trả (/cong-no-phai-tra) | [[Gửi kế toán duyệt]] |

Hoá đơn mua còn nợ nhưng tiền đã trả trước khi ERP chạy, nên trên ERP không có phiếu chi nào để cấn.

**Các bước**
1. Mở Công nợ phải trả, tìm hoá đơn, bấm [[Cấn trừ công nợ]].
2. Có danh sách khoản đã trả thì chọn dòng cuối [[Đã trả trước khi lên ERP]].
3. Điền Số tiền đã trả, Ngày đã trả, Ghi chú (tài khoản đã trả, số UNC).
4. Bấm [[Đính UNC / phiếu chi]], chọn tệp.
5. Thu mua bấm [[Gửi kế toán duyệt]]. Kế toán tự lập thì bấm [[Ghi sổ cấn trừ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Đính UNC hoặc phiếu chi để kế toán duyệt. | Thu mua bắt buộc đính chứng từ |
| Chọn ngày đã trả cho nhà cung cấp. | Chọn ngày, không chọn sau hôm nay |
| Hóa đơn này đã có khoản chờ kế toán duyệt bằng toàn bộ dư nợ. | Chờ kế toán duyệt xong |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (đúng hoá đơn) | 11211 Tiền gửi MB Bank (mặc định) | Kế toán duyệt hoặc tự ghi sổ |

**Lưu ý**
- Gửi xong dư nợ CHƯA giảm, dòng hiện "Chờ kế toán duyệt". Thu mua bấm [[Rút lại]] được.
- Vế Có mặc định 11211 theo chị Dung chốt 02/10/2026. Kế toán đổi được lúc duyệt, ví dụ tài khoản tạm khi số dư ngân hàng đầu kỳ đã trừ khoản này.
- Mất mạng thì bấm lại, máy không ghi hai lần.

## Kế toán duyệt khoản đã trả trước khi lên ERP
Từ khoá: duyệt ghi sổ, chờ kế toán duyệt, từ chối, trả trước ERP, chọn tài khoản Có, đổi vế Có, approve, cấn trừ công nợ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Công nợ phải trả (/cong-no-phai-tra) | [[Duyệt ghi sổ]] |

Dòng hoá đơn có thẻ vàng "Chờ kế toán duyệt" là khoản thu mua vừa gửi. Đây là chỗ DUY NHẤT duyệt loại này; màn Bút toán chỉ để tra cứu.

**Các bước**
1. Mở Công nợ phải trả, tìm hoá đơn có thẻ Chờ kế toán duyệt.
2. Bấm [[Xem đủ chi tiết, ghi chú và UNC]], kiểm ngày trả, người gửi, UNC.
3. Bấm [[Duyệt ghi sổ]]. Hộp "Ghi Nợ 331 hóa đơn / Có tài khoản nào?" hiện tài khoản tiền gửi, tiền mặt, tài khoản tạm; dòng đang dùng có dấu tích.
4. Chọn một dòng là ghi sổ luôn. Bấm [[Thôi]] thì không làm gì.
5. Không đúng thì bấm [[Từ chối]]. Hoá đơn giữ nguyên dư nợ, bản nháp vẫn lưu để truy vết.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Không duyệt được ...: Số tiền vượt phần còn nợ có thể cấn | Dư hoá đơn đã giảm vì khoản khác. Từ chối để thu mua gửi lại đúng số |
| Khoản trả trước khi lên ERP: chọn tài khoản Có khi bấm Duyệt ghi sổ ở Công nợ phải trả. | Hiện khi đổi tài khoản ở màn Bút toán. Quay về Công nợ phải trả |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (hoá đơn) | Tài khoản vừa chọn | Chọn dòng trong hộp Duyệt ghi sổ |

**Lưu ý**
- Ghi nhầm sau khi đã ghi sổ: liên hệ kế toán trưởng để huỷ bút toán, dư hoá đơn trở lại như cũ.

## Trả trước cho nhà cung cấp khi chưa có hoá đơn
Từ khoá: trả trước, đặt cọc, cọc nhà cung cấp, tạm ứng nhà cung cấp, advance, prepayment, deposit, chi trước hoá đơn sau, đơn in ấn

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua, Kế toán | Hồ sơ thanh toán (/ho-so-thanh-toan) | [[Lập phiếu và gửi kế toán]] |

Dùng cho đơn in ấn, đơn đặt sản xuất có điều khoản cọc. Khoản này không phải chi phí, nó nằm bên Nợ 331 tới khi hoá đơn về.

**Các bước**
1. Mở Hồ sơ thanh toán, bấm dấu cộng.
2. Chọn [[Trả cho nhà cung cấp qua công nợ]].
3. Ở câu "Hoá đơn mua đã nằm trong hệ chưa?" chọn [[Chưa có, đây là khoản trả trước]].
4. Mục 1: chọn Đơn mua hàng đã duyệt (bắt buộc).
5. Mục 2: nhà cung cấp tự hiện. Có thể bấm [[Đối chiếu tên với cơ quan thuế]].
6. Mục 3: nhập số tiền trả trước. Mục 4: chọn tài khoản tiền đi ra.
7. Mục 5: chọn loại chứng từ, đính báo giá hoặc hợp đồng (bắt buộc).
8. Bấm [[Lập phiếu và gửi kế toán]]. Phiếu đi tiếp ở Duyệt phiếu chi.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Đơn ... chưa duyệt gửi, chưa lập phiếu trả trước được. | Duyệt gửi đơn mua trước |
| Chưa đính kèm chứng từ nào. ... | Đính báo giá hoặc hợp đồng |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (nhà cung cấp, neo đơn mua) | Tài khoản ngân hàng đã chọn | Kế toán bấm Xác nhận đã chuyển tiền |

**Lưu ý**
- Hoá đơn về thì cấn theo mục "Nối hoá đơn về sau vào phiếu chi trả trước".

## Nối hoá đơn về sau vào phiếu chi trả trước
Từ khoá: nối hoá đơn về sau, cấn trừ, cấn cọc, cọc đã chi, trả trước, hoá đơn đến sau, phân bổ, allocate, offset, khớp sao kê cọc, đính UNC sau

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Duyệt phiếu chi (/thanh-toan) | [[Nối hoá đơn về sau (cấn trừ)]] |

Hoá đơn của khoản trả trước đã về và đã ghi sổ thì kế toán cấn khoản trả trước vào tờ đó.

**Các bước**
1. Mở Duyệt phiếu chi, mở phiếu chi trả trước đã ghi sổ. Khối "Chi trước, hoá đơn về sau" có ba dòng: Sao kê ngân hàng, Uỷ nhiệm chi, Hoá đơn đã cấn.
2. Sao kê chưa khớp thì bấm [[Khớp sao kê thủ công]].
3. Chưa có UNC thì chọn tệp, bấm [[Lưu uỷ nhiệm chi]].
4. Bấm [[Nối hoá đơn về sau (cấn trừ)]], chọn tờ hoá đơn (tờ cùng đơn mua đứng đầu).
5. Đọc hộp "Cấn ... từ ... vào ...", bấm [[Cấn cọc]].

Làm trên hồ sơ trả nhà cung cấp: tick hoá đơn, bấm [[Cấn cọc đã chi vào hóa đơn đã chọn]], chọn khoản cọc.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa có hoá đơn đã ghi sổ còn nợ của ... | Ghi sổ tờ hoá đơn trước |
| Khoản cọc ... chưa đối chiếu đủ tiền trên sao kê. | Khớp sao kê trước |
| Khoản cọc không còn đủ tiền. Tải lại trước khi cấn; không bấm lặp để thử. | Tải lại, kiểm số còn lại |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Không sinh bút toán mới | | Phiếu chi trả trước (Nợ 331 / Có 112) được phân bổ vào hoá đơn |

**Lưu ý**
- Chỉ kế toán cấn được; người khác thấy dòng "Cấn cọc do kế toán thực hiện".
- Mất phản hồi thì bấm [[Kiểm kết quả lần cấn trước]], không bấm cấn lại.

## Hồ sơ chi từ tài khoản công ty có hoá đơn đến sau
Từ khoá: hoá đơn đến sau, chi trước hoá đơn sau, nối hoá đơn đến sau, gỡ hoá đơn, bù trừ, cấn trừ, Adecco, chi từ TK công ty, phiếu chi trả trước, chi phí hai lần

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Giám đốc | Hồ sơ thanh toán (/ho-so-thanh-toan) | [[Nối hoá đơn đến sau]] |

Dùng khi chi thẳng từ tài khoản công ty cho nhà cung cấp mà hoá đơn chưa về (ví dụ phí dịch vụ nhân sự tháng).

**Các bước**
1. Lập hồ sơ [[Chi thẳng từ một tài khoản công ty]], ở từng khoản bật chip [[Hóa đơn đến sau thanh toán]]. Khoản này không cần chọn tài khoản Nợ.
2. Duyệt hai cấp, chuyển tiền, bấm [[Ghi nhận đã thanh toán]].
3. Hoá đơn về: mở hồ sơ, phần Hóa đơn đến sau thanh toán bấm [[Nối hoá đơn đến sau]], chọn tờ. Chọn được nhiều tờ.
4. Đầu hồ sơ hiện đã nối đủ, còn thiếu hay thừa.
5. Nối nhầm: bấm [[Gỡ]] ở dòng tờ đó.

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (nhà cung cấp) | 1121 | Ghi nhận đã thanh toán |
| Chi phí + 1331 | 331 | Tờ hoá đơn ghi sổ |
| 331 (tham chiếu tờ) | Đúng tài khoản chi phí hồ sơ đã ghi | Hồ sơ đường cũ, lúc nối tờ đã ghi sổ |

**Lưu ý**
- Tờ đã ghi sổ: lúc nối máy phân bổ phiếu chi vào tờ, 331 của tờ về 0. Tờ còn nháp: nối xong ghi sổ tờ như thường.
- Gỡ: công nợ tờ trở lại, phiếu chi trở lại khoản trả trước, không huỷ phiếu chi.
- Hồ sơ đường cũ là hồ sơ đã ghi chi phí ngay lúc chi; không nối thì chi phí bị ghi hai lần.

## Cấn trừ phí sàn với công nợ sàn (Grab, Shopee, Be)
Từ khoá: cấn trừ phí sàn, bù trừ phí sàn, phí Grab, phí ShopeeFood, phí BeFood, công nợ sàn, đối soát sàn, merchant, 131 sàn, cấn trừ 331 131, offset, Vagabond Can Tru San

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán (Quản lý kế toán xác nhận) | Desk: Vagabond Can Tru San | [[desk:Xác nhận]] |

Bù phần phí (gồm VAT) sàn đã giữ vào công nợ phải thu của sàn, theo bảng đối soát.

**Các bước**
1. Trên Desk mở Vagabond Can Tru San, bấm [[desk:Thêm]].
2. Điền Sàn, Điểm bán, Khách hàng công nợ sàn, Nhà cung cấp xuất phí, kỳ đối soát, Ngày bù, mã và tệp bảng đối soát.
3. Bảng Hoá đơn phí: chọn hoá đơn, điền phí đã gồm VAT.
4. Bảng Hoá đơn bán được bù: chọn hoá đơn, điền công nợ được bù. Hai tổng phải bằng nhau.
5. Tick ô xác nhận đã kiểm, bấm [[desk:Lưu]] rồi [[desk:Xác nhận]].
6. Phiếu ở Chờ đối soát (hoá đơn phí chưa ghi sổ): bổ sung xong bấm [[desk:Kiểm lại đối soát]].
7. Bấm [[desk:Xem công nợ sàn]] để xem công nợ sàn.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Tổng phí đã gồm VAT phải bằng tổng công nợ được bù. ... | Kiểm hai bảng |
| Nhà cung cấp phí chưa có mã số thuế. ... | Bổ sung mã số thuế nhà cung cấp |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (nhà cung cấp xuất phí) | 131 (khách công nợ sàn) | Phiếu được xác nhận và đủ chứng từ |

**Lưu ý**
- Một phiếu một nhà cung cấp (một mã số thuế); Grab và GrabVN lập riêng.
- Muốn bỏ thì huỷ phiếu đối soát để đảo bút toán, không huỷ riêng bút toán.

## Bù trừ công nợ phải thu và phải trả cùng một đối tác
Từ khoá: bù trừ công nợ, cấn trừ 131 331, đối trừ công nợ, cấn trừ giữa khách và nhà cung cấp, netting, offset, set-off, bút toán bù trừ, biên bản bù trừ, Journal Entry, Payment Reconciliation

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Bút toán (/but-toan); Desk: Đối chiếu thanh toán (/desk/payment-reconciliation) | [[Lưu và ghi sổ luôn]], [[desk:Đối chiếu]] |

Đối tác vừa là khách vừa là nhà cung cấp, có biên bản bù trừ. Ghi bút toán, rồi phân bổ vào đúng hoá đơn.

**Các bước**
1. Mở Bút toán, bấm [[Lập bút toán]], chọn [[Tự gõ từng dòng]]. Diễn giải ghi số biên bản.
2. [[Thêm dòng]] 331, Bên Nợ, số tiền, mã nhà cung cấp.
3. [[Thêm dòng]] 131, Bên Có, cùng số tiền, mã khách hàng.
4. Khung hiện Đã cân thì bấm [[Lưu và ghi sổ luôn]].
5. Trên Desk mở Đối chiếu thanh toán: Loại đối tác Nhà cung cấp, đúng đối tác, Tài khoản Phải thu / Phải trả 331.
6. Bấm [[desk:Lấy bút toán chưa đối chiếu]], chọn bút toán và hoá đơn mua, bấm [[desk:Phân bổ]] rồi [[desk:Đối chiếu]].
7. Làm lại bước 5 và 6 với Loại đối tác Khách hàng, tài khoản 131, hoá đơn bán.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Tài khoản ... là tài khoản công nợ, phải chọn khách hàng / nhà cung cấp. | Điền mã đối tác |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (nhà cung cấp) | 131 (khách hàng) | Ghi sổ bút toán, số tiền theo biên bản |

**Lưu ý**
- Dư từng hoá đơn chỉ giảm sau bước 6 và 7.

## Xem công nợ phải trả và xuất Excel
Từ khoá: công nợ phải trả, công nợ nhà cung cấp, nợ NCC, phải trả người bán, 331, quá hạn, accounts payable, AP, dư hoá đơn, xuất Excel

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Thu mua | Công nợ phải trả (/cong-no-phai-tra) | [[Xuất Excel]] |

Xem còn nợ nhà cung cấp nào, hoá đơn nào quá hạn.

**Các bước**
1. Mở Công nợ phải trả. Thẻ đầu là Dư hóa đơn theo bộ lọc, kèm số hoá đơn và số nhà cung cấp.
2. Bấm nút công ty nếu cần đổi công ty.
3. Chọn chặng: [[Còn nợ]], [[Quá hạn]], [[Giảm một phần]], [[Hết dư nợ]], [[Tất cả]].
4. Chọn ngày hoá đơn, ví dụ [[Tháng này]] hoặc [[Mọi ngày HĐ]]. Bấm [[Nhóm NCC]] để lọc nhóm.
5. Gõ tên nhà cung cấp, mã ERP hoặc số hoá đơn vào ô tìm.
6. Bấm [[Xuất Excel]]: đúng bộ lọc đang chọn, đủ dòng mọi trang.
7. Bấm [[Xem chứng từ]] ở một dòng để mở hoá đơn. Bấm [[Mở báo cáo công nợ lõi]] để xem báo cáo Công nợ phải trả trên Desk.

**Lưu ý**
- Số trên màn chỉ gồm hoá đơn mua thường đã ghi sổ, chưa bù trả trước hay bút toán khác, nên có thể khác dư tổng hợp nhà cung cấp.
- Lọc ngày là chọn tập hoá đơn, không tính lại dư tại ngày quá khứ.
- Dư bằng 0 có thể do cấn trừ, không chứng minh có chuyển khoản mới.

## Công nợ phải thu: gom hoá đơn và gửi QR đòi tiền khách
Từ khoá: công nợ phải thu, phải thu khách hàng, 131, đòi nợ, khách sỉ, gom hoá đơn, phiếu đề nghị thanh toán, QR, accounts receivable, AR, khách nợ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Sales | Công nợ phải thu (/cong-no) | [[Tạo phiếu yêu cầu thanh toán công nợ]] |

Khách sỉ, khách VIP gom nhiều hoá đơn trả một lần. Màn có ba thẻ: [[Đang nợ]], [[Tiền đã về]], [[Phiếu đã gửi]].

**Các bước**
1. Mở Công nợ phải thu, thẻ [[Đang nợ]].
2. Bấm tên khách để mở hoá đơn (đỏ là nợ trên 30 ngày, cam trên 15 ngày).
3. Tick từng hoá đơn, hoặc bấm [[Chọn hết]].
4. Bấm nút Gom ... hoá đơn thành phiếu đề nghị thanh toán.
5. Bấm [[Tạo phiếu yêu cầu thanh toán công nợ]]. Máy sinh phiếu kèm QR MB Bank sống 7 ngày, gửi cho khách.
6. Theo dõi ở thẻ [[Phiếu đã gửi]]: Chờ tiền, Thu thiếu, Đã thu đủ, QR hết hạn, Đã huỷ.

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Tài khoản ngân hàng nhận tiền (MB: 11211) | 131 (khách, gắn hoá đơn) | Phiếu thu được ghi sổ |

**Lưu ý**
- Khách chuyển đúng QR thì SePay tự khớp và tự xoá nợ.
- Tiền đã về mà phiếu thu chưa ghi sổ thì sổ cái vẫn tính là nợ.

## Khách đã chuyển tiền nhưng hoá đơn vẫn còn nợ
Từ khoá: khách đã chuyển tiền, tiền đã về, chưa trừ nợ, phiếu thu nháp, UNC khách gửi, ghi sổ phiếu thu, khớp giao dịch, chuyển khoản không ghi mã

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Sales | Công nợ phải thu (/cong-no) | [[Khách đã chuyển tiền]] |

Tiền về mà nội dung chuyển khoản không có mã đơn nên máy không tự khớp, hoặc phiếu thu nháp còn chờ ảnh UNC khách gửi.

**Các bước**
1. Thẻ [[Đang nợ]]: mở khách, ở dòng hoá đơn bấm [[Khách đã chuyển tiền]].
2. Tìm giao dịch theo nội dung, mã giao dịch, số tiền, ngày. Dòng có dấu tích là khớp mã đơn hoặc số điện thoại.
3. Chọn đúng giao dịch, bấm [[Đúng khoản này]]. Máy lập phiếu thu nháp, hoá đơn sang thẻ [[Tiền đã về]].
4. Ở thẻ [[Tiền đã về]], bấm [[Đính UNC khách gửi]], chọn ảnh chuyển khoản.
5. Kế toán bấm [[Lưu và ghi sổ]] hoặc [[Ghi sổ phiếu thu]]. Người khác lưu UNC, kế toán ghi sổ sau.

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Tài khoản ngân hàng nhận tiền | 131 (gắn hoá đơn) | Ghi sổ phiếu thu |

**Lưu ý**
- Máy chỉ gợi ý, không tự gán theo số tiền.
- Không thấy giao dịch nào thì kiểm sao kê hoặc nhập sao kê bù.
- Ghi sổ phiếu thu bắt buộc có ảnh UNC khách gửi (anh Việt chốt 28/09/2026).

## Lập hồ sơ thanh toán (APP): chọn đúng đường
Từ khoá: hồ sơ thanh toán, APP, đề nghị thanh toán, lập APP, trả nhà cung cấp, chi thẳng tài khoản công ty, hoàn ứng, đề nghị chi, payment request

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua, Kế toán | Hồ sơ thanh toán (/ho-so-thanh-toan) | [[Gửi kế toán duyệt]] |

Hồ sơ thanh toán là chứng từ đề nghị trả tiền, duyệt hai cấp (kế toán rồi giám đốc).

**Các bước**
1. Mở Hồ sơ thanh toán, bấm dấu cộng.
2. Câu "Khoản chi này đi theo đường nào?" chọn một: [[Trả cho nhà cung cấp qua công nợ]], [[Chi thẳng từ một tài khoản công ty]], [[Hoàn lại cho người đã ứng tiền ra]].
3. Câu "Hoá đơn mua đã nằm trong hệ chưa?": [[Đã có, đang nợ trên sổ]] thì tick hoá đơn còn nợ; chưa có thì là khoản trả trước (nhà cung cấp) hoặc gõ tay từng khoản (hoàn ứng).
4. Điền đủ, đính chứng từ, bấm [[Gửi kế toán duyệt]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Hoá đơn ... chưa ghi sổ nên chưa đề nghị trả được. | Nhờ kế toán ghi sổ hoá đơn trước |
| Chưa chọn tài khoản ngân hàng của công ty để chi. | Chọn tài khoản chi |
| Khoản ... chưa chọn tài khoản Nợ. | Chọn tài khoản Nợ cho khoản đó |
| Hồ sơ hoàn ứng thiếu tài khoản nhận | Bấm [[Chọn TK nhận]] rồi gửi lại |

**Lưu ý**
- "Đã có" nghĩa là kế toán ĐÃ NHẬP hoá đơn vào hệ. Cầm tờ giấy mà chưa nhập thì chọn chưa có.
- Hồ sơ hoàn ứng: khi giám đốc duyệt, máy tự sinh hoá đơn mua cho từng khoản.

## Duyệt hồ sơ thanh toán và ghi nhận đã thanh toán
Từ khoá: duyệt APP, kế toán duyệt, giám đốc duyệt, ghi nhận đã thanh toán, dò SePay, đối chiếu tay, bỏ đối chiếu, xoá công nợ, thư báo nhà cung cấp

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Giám đốc | Hồ sơ thanh toán (/ho-so-thanh-toan) | [[Ghi nhận đã thanh toán]] |

**Các bước**
1. Kế toán mở hồ sơ chờ kế toán, bấm [[Kế toán duyệt]].
2. Giám đốc bấm [[Giám đốc duyệt]].
3. Chuyển khoản, ghi mã hồ sơ vào nội dung để máy tự khớp.
4. Bấm [[Dò SePay]] xem đã chi đủ chưa. Trả qua mục hoá đơn điện, nước của app ngân hàng thì bấm [[Đối chiếu tay]].
5. Đủ tiền thì bấm [[Ghi nhận đã thanh toán]]. Máy ghi sổ và gửi thư báo kèm UNC cho nhà cung cấp.
6. Không đồng ý thì bấm [[Từ chối]], ghi lý do.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Người lập hồ sơ không tự duyệt được, ... | Nhờ người khác duyệt |
| Bạn đã ký ở cấp kế toán cho hồ sơ này rồi. ... | Hai cấp là hai người |
| Hồ sơ đang ở ... Phải duyệt xong hai cấp mới chuyển tiền được. | Chờ đủ hai chữ ký |
| Hồ sơ đã thanh toán rồi, không huỷ được. | Liên hệ kế toán trưởng |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (gắn hoá đơn) | Tài khoản ngân hàng chi | Hồ sơ trả nhà cung cấp: máy lập phiếu chi |
| Tài khoản Nợ từng khoản | Tài khoản ngân hàng chi | Hồ sơ chi thẳng: máy lập bút toán |

**Lưu ý**
- [[Bỏ đối chiếu]] chỉ làm được khi sao kê hết liên kết và hồ sơ không còn bút toán đã ghi sổ.
- Không chuyển tiền thêm chỉ vì bút toán đã huỷ.

## Duyệt phiếu chi qua ba cấp
Từ khoá: duyệt phiếu chi, phiếu chi, phiếu chi 3 cấp, ba cấp, payment entry, xác nhận hợp lệ, duyệt chi, xác nhận đã chuyển tiền, trả lại, AP Officer, FIN, UNC, workflow

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Người lập (AP Officer), Kế toán (AP Kiểm soát (FIN)), Giám đốc (AP Giám đốc) | Duyệt phiếu chi (/thanh-toan) | [[Xác nhận đã chuyển tiền]] |

Màn chỉ hiện phiếu CHI. Giám đốc duyệt chưa ghi sổ; phiếu ghi sổ khi kế toán xác nhận tiền đã đi.

| Trạng thái | Ai bấm | Nút |
|---|---|---|
| Nháp, Bị trả lại | Người lập | [[Gửi kiểm tra]] |
| Chờ kế toán kiểm tra | Kế toán | [[Xác nhận hợp lệ]] hoặc [[Trả lại]] |
| Chờ giám đốc duyệt chi | Giám đốc | [[Duyệt chi]] hoặc [[Trả lại]] |
| Đã duyệt chi, chờ chuyển tiền | Kế toán | [[Xác nhận đã chuyển tiền]] hoặc [[Trả lại]] |
| Đã chuyển tiền, đã ghi sổ | | Xong |

**Các bước (kế toán ở bước cuối)**
1. Chuyển tiền thật, nội dung ghi mã phiếu.
2. Mở phiếu, đính tờ uỷ nhiệm chi.
3. Bấm [[Xác nhận đã chuyển tiền]], điền mã giao dịch ngân hàng (bỏ trống được).
4. Đọc hộp xác nhận, bấm [[Đã chuyển tiền]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Đính tờ uỷ nhiệm chi vào phiếu trước đã. ... | Đính UNC tải từ e-banking |
| Chưa thấy giao dịch ngân hàng nào mang mã phiếu này. ... | Chờ ngân hàng đẩy về, hoặc Quản lý kế toán ghi lý do để ghi sổ sớm |
| Phiếu chưa qua chữ ký giám đốc. ... | Chờ giám đốc bấm Duyệt chi |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 331 (hoặc tài khoản theo loại chi) | Tài khoản tiền chi | Xác nhận đã chuyển tiền |

## Không ghi sổ được chứng từ ngân hàng vì thiếu uỷ nhiệm chi
Từ khoá: thiếu UNC, uỷ nhiệm chi, giấy báo Nợ, giấy báo Có, đính kèm, không ghi sổ được, kẹp giấy, sao kê SePay, bank payment, attachment

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Desk: Phiếu thu/chi | Nút kẹp giấy đính kèm |

Mọi phiếu thu/chi đi qua tài khoản ngân hàng (lập từ 16/08/2026) phải có tệp đính kèm mới ghi sổ được, kể cả rút tiền gửi về quỹ.

**Các bước**
1. Tải uỷ nhiệm chi hoặc giấy báo từ e-banking.
2. Mở phiếu, bấm nút kẹp giấy ở góc phải, tải tệp lên.
3. Ghi sổ lại.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| ... đi qua tài khoản ngân hàng ... nên bắt buộc phải có Uỷ nhiệm chi đính kèm mới ghi sổ được. | Đính tệp UNC rồi ghi sổ lại |

**Lưu ý**
- Dòng sao kê SePay chỉ để xem tiền đã đi chưa, không thay được UNC khi làm việc với cơ quan thuế (chị Dung chốt 16/08/2026).
- Tên chứng từ tự đổi theo tài khoản: tiền mặt là Phiếu chi, Phiếu thu; ngân hàng là Uỷ nhiệm chi, Giấy báo Có.

## Lập bút toán tay theo định khoản mẫu
Từ khoá: bút toán, bút toán tay, hạch toán tay, định khoản, journal entry, JE, trích lương, bảo hiểm, phân bổ 242, khấu trừ GTGT, nộp thuế, phí ngân hàng, rút tiền, nộp tiền, kết chuyển giá thành

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Bút toán (/but-toan) | [[Lập bút toán]] |

**Các bước**
1. Mở Bút toán, bấm [[Lập bút toán]].
2. Chọn việc theo mẫu (Trích lương, Trích bảo hiểm, Chi trả lương, Phân bổ chi phí trả trước hàng tháng, Khấu trừ thuế GTGT cuối kỳ, Nộp thuế, Phí ngân hàng, Rút tiền gửi về quỹ, Nộp tiền mặt vào ngân hàng, Kết chuyển chi phí sản xuất...) hoặc [[Tự gõ từng dòng]].
3. Sửa Diễn giải, bấm ô ngày để chọn Ngày hạch toán.
4. Điền số tiền. Dòng nền xám là máy tự tính cho cân. Dòng công nợ thì điền mã khách hoặc nhà cung cấp.
5. Bấm [[Thêm dòng]] để thêm tài khoản (gõ số hiệu hoặc tên, chọn Bên Nợ hay Bên Có).
6. Khung hiện Đã cân thì bấm [[Lưu nháp]] hoặc [[Lưu và ghi sổ luôn]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Bút toán phải có ít nhất hai dòng có số tiền. | Thêm dòng |
| Bút toán chưa cân: bên Nợ ..., bên Có ..., lệch ... | Sửa số cho cân |
| Tài khoản ... là tài khoản nhóm, không hạch toán thẳng vào được. | Chọn tài khoản chi tiết |
| Tài khoản của bạn không có quyền ghi sổ bút toán. | Nhân viên kế toán chỉ lưu nháp; nhờ Quản lý kế toán hoặc AP Kiểm soát (FIN) ghi sổ |

**Lưu ý**
- Mẫu ghi "thiếu ... TK" là công ty chưa có tài khoản đó, báo kế toán trưởng.

## Ghi sổ, đổi tài khoản, huỷ bút toán
Từ khoá: ghi sổ bút toán, sửa bút toán, đổi tài khoản, huỷ bút toán, bút toán nháp, cancel journal entry, sai tài khoản

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Bút toán (/but-toan) | [[Ghi sổ]] |

**Các bước**
1. Mở Bút toán. Lọc chip [[Tất cả]], [[Còn nháp]], [[Đã ghi sổ]], [[Đã huỷ]] hoặc gõ ô tìm. Màn hiện 60 ngày gần nhất.
2. Bấm một bút toán để xem định khoản.
3. Bút toán nháp: bấm [[Đổi tài khoản]] ở dòng cần đổi, gõ số hiệu hoặc tên tài khoản mới.
4. Bấm [[Ghi sổ]].
5. Bút toán đã ghi sổ sai: bấm [[Huỷ bút toán]], ghi lý do (bắt buộc), rồi lập lại bút toán đúng.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chỉ sửa được bút toán còn nháp. ... | Huỷ rồi lập lại |
| Dòng công nợ gắn nhà cung cấp, khách hoặc hoá đơn thì không đổi tài khoản được. | Lập bút toán mới |
| Sổ ngày ... đã khoá ... | Xem mục khoá sổ |

**Lưu ý**
- Khoản trả trước khi lên ERP không đổi tài khoản ở đây, chọn vế Có lúc duyệt ở Công nợ phải trả.
- Huỷ không xoá: tờ vẫn nằm trong sổ ở trạng thái đã huỷ.
- Bút toán của kỳ đã chốt hoặc đã đối chiếu: liên hệ kế toán trưởng trước khi huỷ.

## Đối chiếu hoá đơn mua với phiếu nhập kho và ghi sổ
Từ khoá: đối chiếu hoá đơn mua, đối chiếu mua, nối phiếu nhập kho, khớp và ghi sổ, ghi sổ hoá đơn mua, purchase invoice, 3-way match, lệch tiền, hoá đơn nháp, 3311, 632

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Thu mua | Đối chiếu mua (/doi-chieu-mua) | [[Khớp và ghi sổ]] |

Hoá đơn từ m-invoice về ở dạng nháp. Màn này tìm phiếu nhập khớp, chỉ chỗ lệch, rồi nối và ghi sổ.

**Các bước**
1. Mở Đối chiếu mua, chọn khoảng ngày và nhóm ([[Chờ đối chiếu]], [[Không thấy phiếu nhập nào]]...).
2. Bấm một hoá đơn. Máy gợi ý phiếu nhập, so từng món, đơn vị, tiền.
3. Lệch đơn vị thì khai quy đổi ngay trên dòng.
4. Kế toán bấm [[Khớp và ghi sổ]] hoặc [[Chỉ nối phiếu]]. Thu mua chỉ có [[Nối phiếu]].
5. Hoá đơn không có phiếu nhập (xăng, dịch vụ, phí ship): kế toán bấm [[Ghi sổ thẳng, không nối phiếu]].
6. Nối nhầm: bấm [[Bỏ nối]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phiếu nhập ... không phải của nhà cung cấp này. | Chọn phiếu đúng nhà cung cấp |
| Chip "Phiếu nhập đã bị hoá đơn khác lấy" | Nhờ kế toán kiểm, không nhập thêm kho |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 3311 + 1331 | 331 | Hoá đơn nối phiếu nhập kho đã ghi sổ |
| Chi phí theo món + 1331 | 331 | Ghi sổ thẳng, không phiếu nhập |

**Lưu ý**
- Phiếu nhập kho đã ghi Nợ 152 / Có 3311. Phiếu nhập còn nháp thì ghi sổ nó trước rồi mới nối.
- Ghi sổ thẳng: xem tài khoản từng dòng trước. Dòng dịch vụ hiện 632 thường là sai.
- Tờ có chip Hồ sơ là hoá đơn đến sau của hồ sơ chi, không ghi sổ ở đây.

## Xem hoá đơn mua vào và hoá đơn bán ra
Từ khoá: hoá đơn mua, hoá đơn mua vào, purchase invoice, hoá đơn bán, hoá đơn bán ra, sales invoice, tra cứu hoá đơn, còn nợ, quá hạn

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Hoá đơn mua (/hoa-don-mua); Hoá đơn bán (/hoa-don-ban) | Ô tìm |

**Các bước (hoá đơn mua)**
1. Chọn khoảng [[30 ngày]], [[60 ngày]], [[6 tháng]], [[1 năm]] và nhóm.
2. Gõ mã phiếu, tên nhà cung cấp hoặc số hoá đơn.
3. Mỗi dòng ghi còn nháp, đã huỷ, hạn trả, quá hạn bao nhiêu ngày, số còn nợ.

**Các bước (hoá đơn bán)**
1. Chọn [[7 ngày]], [[30 ngày]], [[3 tháng]], [[1 năm]] và điểm bán ([[Cả ba điểm]], Sales Online, District 1, NVHTN).
2. Gõ mã phiếu, tên khách hoặc số hoá đơn điện tử.
3. Mỗi dòng ghi số và trạng thái hoá đơn điện tử, phương thức thanh toán, người bán, trạng thái kho, số còn phải thu.

**Lưu ý**
- Danh sách dài bị cắt thì màn báo; thu hẹp bằng ngày hoặc ô tìm.

## Hoá đơn điện tử: khi nào xuất, xem trạng thái, ngày cũ chưa xuất
Từ khoá: hoá đơn điện tử, HĐĐT, e-invoice, m-invoice, xuất hoá đơn, phát hành hoá đơn, ký số, chờ ký, chưa xuất hoá đơn, hoá đơn ngày cũ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Quản lý | Hoá đơn bán (/hoa-don-ban); Cài đặt cuối ngày (/cai-dat-cuoi-ngay) | [[Xem và xuất hoá đơn cho ngày này]] |

Chỉ hoá đơn bán ĐÃ GHI SỔ mới phát hành sang m-invoice. Điểm bán chưa bật trong Cài đặt cuối ngày thì hoá đơn nằm yên.

**Các bước (tờ đã ghi sổ mà đêm đó không lên được m-invoice)**
1. Mở Cài đặt cuối ngày, phần Hoá đơn ngày cũ chưa xuất được.
2. Chọn Ngày bán, bấm [[Xem và xuất hoá đơn cho ngày này]].
3. Đọc bản xem trước: số tờ, tổng tiền, giữ ngày bán hay lấy ngày lập hôm nay. Rồi mới đồng ý.
4. Quá hạn ký gửi thì cần quản lý xác nhận; máy không tự đổi ngày lập.

**Lưu ý**
- Xem trạng thái: mở Hoá đơn bán, mỗi dòng ghi số và trạng thái, hoặc "chưa xuất hoá đơn điện tử".
- Khung "Khoá gốc bên m-invoice đang chặn": m-invoice đang tắt phát hành hoặc tắt ký, báo kế toán mở lại.
- Sửa, huỷ, thay thế hoá đơn điện tử đã phát hành: liên hệ kế toán trưởng. Không tự làm.

## Nhập tệp sao kê ngân hàng
Từ khoá: nhập sao kê, sao kê ngân hàng, bank statement, import sao kê, thiếu giao dịch, nạp bù sao kê, Excel ngân hàng, CSV, SePay thiếu

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Nhập sao kê (/nhap-sao-ke) | Ghi ... dòng vào sổ |

Dùng khi SePay sót giao dịch, nạp bù từ tệp ngân hàng gửi.

**Các bước**
1. Mục 1. Chọn tài khoản ngân hàng.
2. Mục 2. Bấm [[Chọn tệp .xlsx hoặc .csv]]. Tệp phải có cột Nội dung và PS giảm hoặc PS tăng.
3. Mục 3. Xem trước: máy đếm dòng sẽ thêm, dòng đã có, dòng hỏng.
4. Bấm nút Ghi ... dòng vào sổ, đồng ý ở hộp hỏi.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Tệp nặng quá 20 MB. ... | Cắt sao kê theo tháng |
| Chưa có tài khoản ngân hàng nào trên hệ. ... | Báo kế toán trưởng khai trên Desk |

**Lưu ý**
- Máy chỉ thêm dòng còn thiếu, không ghi đè dòng đã có.
- Ghi rồi muốn bỏ: liên hệ kế toán trưởng.

## Ký nhận biên nhận nộp tiền mặt
Từ khoá: nộp quỹ, nộp tiền mặt, biên nhận nộp tiền, ký nhận tiền, tiền mặt quầy, bảng kê mệnh giá, lệch tiền mặt, cash deposit

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Giám đốc | Biên nhận nộp tiền mặt (/nop-quy) | [[Ký nhận tiền (kế toán / giám đốc)]] |

Thu ngân lập biên nhận, đếm theo mệnh giá, ký bên giao. Kế toán hoặc giám đốc đếm lại và ký nhận.

**Các bước**
1. Mở màn, lọc trạng thái ([[Chờ ký nhận]]...), khoảng ngày, ô tìm.
2. Mở phiếu Chờ ký nhận. Đối chiếu bảng mệnh giá với tiền thực nhận; dòng đỏ "Lệch ..." là chênh với số kỳ vọng.
3. Bấm [[Ký nhận tiền (kế toán / giám đốc)]], ký vào khung, lưu chữ ký.
4. Bấm [[Tải biên bản PDF]]. Ở danh sách bấm [[Tải Excel]] để xuất theo bộ lọc.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chỉ kế toán hoặc giám đốc được ký nhận tiền. | Nhờ đúng người ký |
| Bên giao và bên nhận không được là cùng một người. | Người khác ký nhận |
| Phiếu đang ở trạng thái ..., chưa hoặc không còn chờ ký nhận. | Kiểm trạng thái phiếu |

**Lưu ý**
- Ký nhận xong phiếu khoá cứng, kể cả bảng mệnh giá.
- Ký nhận không sinh bút toán. Kế toán hạch toán tiền nộp quỹ riêng.
- Lệch tiền xử lý thế nào: việc này do anh Việt quyết.

## Chi tiền và đóng phiếu hoàn tiền khách
Từ khoá: hoàn tiền, cash-back, refund, trả lại tiền khách, phiếu hoàn tiền, đối soát lệnh chi, uỷ nhiệm chi hoàn tiền, phiếu chi hoàn tiền

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Hoàn tiền (/hoan-tien) | [[Hoàn thành và ghi sổ]] |

Sales lập phiếu hoàn tiền. Kế toán chuyển khoản trả khách từ tài khoản MB công ty, rồi khép phiếu.

**Các bước**
1. Mở Hoàn tiền, lọc chip [[Chờ chi]].
2. Mở phiếu, chuyển khoản với nội dung bắt đầu bằng THE VAGABOND HOAN TIEN kèm mã phiếu.
3. Ở danh sách bấm [[Đối soát lệnh chi]]. Máy khớp giao dịch, báo riêng phiếu lệch tiền và phiếu trùng giao dịch.
4. Mở phiếu, bấm [[Đính uỷ nhiệm chi]], chọn tệp UNC.
5. Gửi UNC cho khách, bấm [[Hoàn thành và ghi sổ]].

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 131 (khách) | Tài khoản ngân hàng chi (MB 11211) | Hoàn thành và ghi sổ |

**Lưu ý**
- Phiếu chỉ khép được khi có tệp UNC; dòng sao kê SePay không thay được UNC.
- Ghi sổ rồi không sửa được: liên hệ kế toán trưởng.
- Có hoàn hay không, hoàn bao nhiêu: việc này do anh Việt quyết.

## Khai tài sản và chạy khấu hao
Từ khoá: tài sản, tài sản cố định, TSCĐ, công cụ dụng cụ, CCDC, khấu hao, phân bổ 242, 214, asset, depreciation, ghi sổ tài sản

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán | Tài sản (/tai-san) | [[Khai và ghi sổ]] |

**Các bước khai**
1. Lần đầu bấm [[Lập sáu nhóm tài sản]].
2. Bấm [[Khai tài sản]], chọn nhóm (nhóm quyết định số năm và tài khoản chi phí).
3. Điền tên như trên hoá đơn, nguyên giá (chưa gồm thuế GTGT được khấu trừ), ngày bắt đầu dùng, số năm, số đã trích trước (nếu có), nơi để.
4. Bấm [[Khai và ghi sổ]]. Máy dựng lịch khấu hao theo tháng.
5. Tài sản còn nháp: mở, bấm [[Ghi sổ tài sản này]].

**Các bước khấu hao hằng tháng**
1. Ở Tài sản bấm [[Khấu hao]]. Màn hiện số kỳ tới hạn, tổng tiền, chia theo bộ phận.
2. Bấm nút Ghi sổ khấu hao ... kỳ, đồng ý.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Nhóm Công cụ dụng cụ chưa lập được (242 chưa là tài khoản giữ giá trị) | Bấm [[Xem và mở khoá]], đọc kỹ rồi mới đồng ý |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Chi phí khấu hao của bộ phận (6274 bếp, 6424 quản lý...) | 2141 hao mòn | Ghi sổ khấu hao tài sản cố định |
| Chi phí của bộ phận | 242 | Phân bổ công cụ dụng cụ |

**Lưu ý**
- Bút toán khấu hao đã ghi chỉ huỷ được, không xoá.

## Khoá sổ và vì sao báo "Sổ đã khoá"
Từ khoá: khoá sổ, khóa sổ, chốt sổ, sổ đã khoá, không huỷ được, không sửa được hoá đơn cũ, mở khoá, period closing, lock

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán trưởng, Giám đốc | Khoá sổ (/khoa-so) | [[Lưu cấu hình khoá sổ]] |

Chứng từ của ngày đã khoá thì không ghi sổ, không huỷ, không sửa được nữa, trên app hay trên Desk đều vậy.

**Các bước**
1. Mở Khoá sổ. Thẻ xanh "Đang khoá đến hết ..." hoặc thẻ cam "Chưa khoá gì".
2. Tự khoá sau bao nhiêu ngày: chọn [[Không khoá]], [[3 ngày]], [[7 ngày]], [[15 ngày]], [[31 ngày]], hoặc gõ ô Số ngày khác.
3. Mốc khoá cứng: chọn ngày cuối kỳ đã chốt (không chọn được hôm nay). Để trống nếu chưa cần.
4. Bấm [[Lưu cấu hình khoá sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Sổ ngày ... đã khoá (khoá đến hết ...) nên không đụng vào ... được nữa ... | Chứng từ thuộc kỳ đã chốt. Liên hệ kế toán trưởng |
| Chỉ kế toán trưởng hoặc giám đốc mới đụng được vào khoá sổ. | Nhờ đúng người |

**Lưu ý**
- Cần sửa thật một tờ cũ thì kế toán trưởng mở khoá riêng tờ đó: xem mục "Mở khoá riêng một tờ đã khoá sổ".
- Thẻ đỏ "Đang có ... hoá đơn được mở khoá" nhắc sửa xong phải đóng lại.
- Danh sách loại chứng từ áp dụng ghi ở cuối màn.

## Mở khoá riêng một tờ đã khoá sổ
Từ khoá: mở khoá, mở khoá sổ, mở khoá chứng từ, sửa chứng từ cũ, sửa hoá đơn đã khoá, đóng khoá, khoá lại, unlock, sổ đã khoá

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán trưởng, giám đốc | Khoá sổ (/khoa-so), hoặc Desk: mở chính tờ đó | [[Mở khoá tờ này]], [[desk:Mở khoá sổ]] |

Mở riêng một tờ thuộc kỳ đã khoá để sửa. Các tờ khác vẫn khoá. Máy ghi lý do và tên người mở.

**Các bước trên app**
1. Mở Khoá sổ, kéo xuống phần Mở khoá một tờ.
2. Chọn loại chứng từ, gõ số chứng từ, ghi lý do.
3. Bấm [[Mở khoá tờ này]].
4. Sửa xong, quay lại Khoá sổ, bấm [[Đóng khoá]] ở dòng tờ đó.

**Các bước trên Desk**
1. Mở chính tờ cần sửa. Tờ thuộc kỳ khoá thì có nút [[desk:Mở khoá sổ]].
2. Ghi lý do, bấm [[desk:Mở khoá]].
3. Sửa xong bấm [[desk:Đóng khoá sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phải ghi lý do mở khoá thì sau này còn giải trình được. | Ghi lý do rồi bấm lại |
| Không tìm thấy chứng từ ... | Kiểm lại số chứng từ và loại chứng từ đã chọn |
| Chỉ kế toán trưởng hoặc giám đốc mới đụng được vào khoá sổ. | Nhờ đúng người |

**Lưu ý**
- Không thấy nút: tờ đó chưa tới kỳ khoá, sửa được như thường; hoặc bạn không phải kế toán trưởng.
- Hoá đơn điện tử đã phát hành thì mở khoá cũng không sửa nội dung đã gửi cơ quan thuế. Liên hệ kế toán trưởng.
- Sửa xong phải đóng lại. Thẻ đỏ trên màn Khoá sổ liệt kê các tờ còn đang mở.
