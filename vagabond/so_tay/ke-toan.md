# Kế toán

## Cách hạch toán cấn trừ công nợ: chọn đúng đường theo trường hợp
Từ khoá: cấn trừ, bù trừ, đối trừ, trừ nợ, cấn nợ, cấn cọc, clearing, offset, netting, set-off, bút toán cấn trừ, bù trừ công nợ, Journal Entry, payment reconciliation
Ai dùng: Kế toán, Thu mua
Màn hình: Công nợ phải trả (/cong-no-phai-tra)

Không có một nút cấn trừ chung. Tuỳ khoản tiền đã đi đường nào mà chọn đúng chỗ, máy tự lập bút toán.

Các trường hợp:
1. Đã có phiếu chi hoặc phiếu cọc trên ERP, nay có hoá đơn mua: Công nợ phải trả, dòng hoá đơn, bấm Cấn trừ công nợ, chọn khoản đã trả. Xem mục "Cấn khoản đã trả vào hoá đơn mua".
2. Hoá đơn đã trả tiền trước khi lên ERP: Công nợ phải trả, Cấn trừ công nợ, chọn Đã trả trước khi lên ERP.
3. Chi trước, hoá đơn về sau trên hồ sơ thanh toán: trên hồ sơ bấm Nối hoá đơn đến sau.
4. Phí sàn (Grab, Shopee...) đã bị sàn giữ lại từ tiền hàng: phiếu cấn trừ phí sàn trên Desk.
5. Hoàn ứng của nhân viên trừ vào tạm ứng: chọn phiếu tạm ứng ở phần Cấn trừ tạm ứng khi lập phiếu hoàn ứng.

Hạch toán:
- Trường hợp 1 và 3 (từ bản hiện hành): không sinh bút toán mới, máy phân bổ phiếu chi (đã ghi Nợ 331 / Có 112) vào đúng hoá đơn.
- Trường hợp 2: Nợ 331 (đúng NCC, đúng hoá đơn) / Có tài khoản kế toán chọn khi duyệt (mặc định 11211).
- Trường hợp 4: Nợ 331 (NCC xuất phí) / Có 131 (khách hàng công nợ sàn).

Lưu ý: không tạo thêm phiếu chi hay chuyển tiền thêm chỉ để công nợ về 0. Hạch toán theo bản chất từng khoản là việc của kế toán, máy chỉ đặt mặc định.

## Cấn khoản đã trả vào hoá đơn mua
Từ khoá: cấn trừ công nợ, cấn cọc, cấn khoản đã trả, phân bổ thanh toán, trừ nợ nhà cung cấp, đối trừ, offset, allocate, clearing, UNC
Ai dùng: Kế toán
Màn hình: Công nợ phải trả (/cong-no-phai-tra)

Dùng khi trên ERP đã có phiếu chi hoặc phiếu cọc đã ghi sổ cho nhà cung cấp, còn tiền chưa phân bổ, và hoá đơn mua của NCC đó đang còn nợ.

Các bước:
1. Mở Công nợ phải trả, gõ tên NCC hoặc số hoá đơn vào ô tìm.
2. Ở dòng hoá đơn, bấm Cấn trừ công nợ.
3. Chọn khoản đã trả trong danh sách (mỗi dòng ghi còn bao nhiêu và số UNC).
4. Ô Số tiền cấn mặc định là số lớn nhất được cấn. Sửa nếu cần.
5. Có UNC thì bấm Đính UNC. Muốn chỉ lưu UNC mà chưa cấn thì bấm Chỉ lưu UNC (nút này không làm giảm nợ).
6. Bấm Xác nhận cấn, không chuyển tiền, đọc lại số tiền và hoá đơn trong hộp xác nhận rồi đồng ý.

Vì sao bị chặn:
- "Khoản cọc ... chưa đối chiếu đủ tiền trên sao kê": khoản đó chưa khớp sao kê ngân hàng. Kế toán khớp sao kê trước rồi mới cấn.
- "Nhập số tiền lớn hơn 0, không vượt dư hóa đơn và khoản đã trả."
- "Công nợ vừa thay đổi. Tải lại hóa đơn trước khi cấn cọc."
- Hoá đơn ngoại tệ: dùng Đối chiếu thanh toán lõi (kế toán) trong nút Xem chứng từ.

Lưu ý: mất mạng giữa chừng thì bấm Kiểm lần cấn đang chờ, không tạo lần cấn mới. Không có khoản đã trả nào thì app tự chuyển sang màn Đã trả trước khi lên ERP.

Hạch toán: không sinh bút toán mới. Phiếu chi gốc (Nợ 331 / Có 112) được phân bổ vào hoá đơn, dư hoá đơn giảm ngay.

## Hoá đơn đã trả tiền trước khi lên ERP: ghi giảm công nợ
Từ khoá: đã trả trước khi lên ERP, trả trước ERP, số dư đầu kỳ, công nợ cũ, cấn trừ, bù trừ, giảm nợ, hoá đơn cũ còn nợ, tài khoản tạm, Printeco
Ai dùng: Thu mua (Uyên), Kế toán
Màn hình: Công nợ phải trả (/cong-no-phai-tra)

Dùng khi hoá đơn mua đang hiện còn nợ nhưng tiền đã chuyển cho NCC từ trước khi ERP chạy, nên trên ERP không có phiếu chi nào để cấn.

Các bước:
1. Mở Công nợ phải trả, tìm hoá đơn, bấm Cấn trừ công nợ.
2. Nếu hiện danh sách khoản đã trả, chọn dòng cuối Đã trả trước khi lên ERP. Nếu không có phiếu chi nào, app vào thẳng màn này.
3. Điền Số tiền đã trả, Ngày đã trả, Ghi chú (tài khoản đã trả, số UNC...).
4. Bấm Đính UNC / phiếu chi và chọn tệp. Thu mua bắt buộc phải đính.
5. Thu mua bấm Gửi kế toán duyệt. Kế toán tự lập thì nút là Ghi sổ cấn trừ, ghi sổ luôn.

Vì sao bị chặn:
- "Đính UNC hoặc phiếu chi để kế toán duyệt."
- "Chọn ngày đã trả cho nhà cung cấp." hoặc "Ngày đã trả không được sau hôm nay."
- "Hóa đơn này đã có khoản chờ kế toán duyệt bằng toàn bộ dư nợ."
- "Hóa đơn ngoại tệ: kế toán xử lý ở Đối chiếu thanh toán lõi."

Lưu ý: gửi xong dòng hoá đơn hiện "Chờ kế toán duyệt", dư nợ CHƯA giảm. Thu mua bấm Rút lại được nháp của mình. Mất mạng thì bấm lại, máy không ghi hai lần.

Hạch toán: Nợ 331 (đúng NCC, đúng hoá đơn) / Có tài khoản mặc định 11211 Tiền gửi MB Bank; công ty không có 11211 thì máy dùng tài khoản tạm. Kế toán đổi được vế Có lúc duyệt. Không chuyển tiền.
<!-- kiểm: tài liệu hướng dẫn cũ (01/10) ghi Có tài khoản tạm, không Có 1121; mã nguồn v552 (02/10) đổi mặc định sang 11211 theo chị Dung. Cần chị Dung xác nhận cách ghi cuối cùng. -->

## Kế toán duyệt khoản đã trả trước khi lên ERP
Từ khoá: duyệt ghi sổ, chờ kế toán duyệt, từ chối, trả trước ERP, chọn tài khoản Có, đổi vế Có, approve, cấn trừ công nợ
Ai dùng: Kế toán
Màn hình: Công nợ phải trả (/cong-no-phai-tra)

Thu mua gửi khoản đã trả trước khi lên ERP thì dòng hoá đơn có thẻ vàng "Chờ kế toán duyệt". Đây là chỗ DUY NHẤT duyệt loại này; màn Bút toán chỉ để tra cứu.

Các bước:
1. Mở Công nợ phải trả, tìm hoá đơn có thẻ Chờ kế toán duyệt.
2. Bấm Xem đủ chi tiết, ghi chú và UNC để kiểm ngày trả, người gửi, UNC.
3. Bấm Duyệt ghi sổ. Hộp hỏi "Ghi Nợ 331 hóa đơn / Có tài khoản nào?" hiện danh sách tài khoản tiền gửi, tiền mặt và tài khoản tạm; dòng đang dùng có dấu tích.
4. Chọn một dòng là ghi sổ luôn. Bấm Thôi thì không làm gì.
5. Không đúng thì bấm Từ chối. Hoá đơn giữ nguyên dư nợ, bản nháp vẫn lưu để truy vết.

Vì sao bị chặn:
- "Không duyệt được ...: Số tiền vượt phần còn nợ có thể cấn": sau khi thu mua gửi, dư hoá đơn đã giảm vì khoản khác. Từ chối nháp này để thu mua gửi lại đúng số.
- "Khoản trả trước khi lên ERP: chọn tài khoản Có khi bấm Duyệt ghi sổ ở Công nợ phải trả." (hiện khi thử ghi sổ ở màn Bút toán).

Lưu ý: ghi nhầm sau khi đã ghi sổ thì liên hệ kế toán trưởng để huỷ bút toán trên Desk, dư hoá đơn trở lại như cũ.

Hạch toán: Nợ 331 hoá đơn / Có tài khoản vừa chọn.

## Trả trước cho nhà cung cấp khi chưa có hoá đơn
Từ khoá: trả trước, đặt cọc, cọc nhà cung cấp, tạm ứng nhà cung cấp, advance, prepayment, deposit, chi trước hoá đơn sau, đơn in ấn
Ai dùng: Thu mua, Kế toán
Màn hình: Hồ sơ thanh toán (/ho-so-thanh-toan)

Dùng cho đơn in ấn, đơn đặt sản xuất có điều khoản cọc: phải trả tiền trước, hoá đơn về sau. Khoản này không phải chi phí, nó nằm bên Nợ 331 cho tới khi hoá đơn về.

Các bước:
1. Mở Hồ sơ thanh toán, bấm dấu cộng.
2. Chọn Trả cho nhà cung cấp qua công nợ.
3. Câu "Hoá đơn mua đã nằm trong hệ chưa?" chọn Chưa có, đây là khoản trả trước.
4. Mục 1: chọn Đơn mua hàng (bắt buộc, đơn phải đã duyệt).
5. Mục 2: nhà cung cấp tự hiện theo đơn. Có thể bấm Đối chiếu tên với cơ quan thuế.
6. Mục 3: nhập số tiền trả trước. Mục 4: chọn tiền đi ra từ tài khoản nào.
7. Mục 5: chọn loại chứng từ, bấm Đính kèm (báo giá hoặc hợp đồng, bắt buộc).
8. Bấm Lập phiếu và gửi kế toán. Phiếu chi đi tiếp chuỗi duyệt ở Duyệt phiếu chi.

Vì sao bị chặn:
- "Đơn ... chưa duyệt gửi, chưa lập phiếu trả trước được."
- "Chưa đính kèm chứng từ nào. Khoản trả trước chưa có hoá đơn nên bắt buộc phải có báo giá hoặc hợp đồng."

Hạch toán: phiếu chi Nợ 331 (NCC) / Có tài khoản ngân hàng đã chọn, neo vào đơn mua. Hoá đơn về thì cấn theo mục "Nối hoá đơn về sau vào phiếu chi trả trước".

## Nối hoá đơn về sau vào phiếu chi trả trước
Từ khoá: nối hoá đơn về sau, cấn trừ, cấn cọc, cọc đã chi, trả trước, hoá đơn đến sau, phân bổ, allocate, offset, khớp sao kê cọc
Ai dùng: Kế toán
Màn hình: Duyệt phiếu chi (/thanh-toan); Hồ sơ thanh toán (/ho-so-thanh-toan)

Khi hoá đơn của khoản trả trước đã về và đã ghi sổ, kế toán cấn khoản trả trước vào tờ đó để công nợ về đúng.

Các bước (trên phiếu chi trả trước):
1. Mở Duyệt phiếu chi, mở phiếu chi trả trước. Khối "Chi trước, hoá đơn về sau" có ba dòng kiểm: Sao kê ngân hàng, Uỷ nhiệm chi, Hoá đơn đã cấn.
2. Sao kê chưa khớp thì bấm Khớp sao kê thủ công.
3. Chưa có UNC thì chọn tệp rồi bấm Lưu uỷ nhiệm chi.
4. Bấm Nối hoá đơn về sau (cấn trừ), chọn tờ hoá đơn (tờ cùng đơn mua có biểu tượng nối, đứng đầu).
5. Đọc hộp xác nhận "Cấn ... từ ... vào ...", bấm Cấn cọc.

Trên hồ sơ trả NCC: tick hoá đơn rồi bấm Cấn cọc đã chi vào hóa đơn đã chọn, chọn khoản cọc.

Vì sao bị chặn:
- "Chưa có hoá đơn đã ghi sổ còn nợ của ...": ghi sổ tờ hoá đơn trước rồi quay lại.
- "Khoản cọc ... chưa đối chiếu đủ tiền trên sao kê."
- "Khoản cọc không còn đủ tiền. Tải lại trước khi cấn; không bấm lặp để thử."

Lưu ý: chỉ kế toán cấn được; người khác thấy dòng "Cấn cọc do kế toán thực hiện". Mất phản hồi thì bấm Kiểm kết quả lần cấn trước.

Hạch toán: không sinh bút toán mới, phiếu chi trả trước (Nợ 331 / Có 112) được phân bổ vào hoá đơn, không chuyển thêm tiền.

## Hồ sơ chi từ tài khoản công ty có hoá đơn đến sau
Từ khoá: hoá đơn đến sau, chi trước hoá đơn sau, nối hoá đơn đến sau, gỡ hoá đơn, bù trừ, cấn trừ, Adecco, chi từ TK công ty, phiếu chi trả trước
Ai dùng: Kế toán, Giám đốc
Màn hình: Hồ sơ thanh toán (/ho-so-thanh-toan)

Dùng khi chi thẳng từ tài khoản công ty cho NCC mà hoá đơn chưa về (ví dụ phí dịch vụ nhân sự tháng).

Các bước:
1. Lập hồ sơ: chọn Chi thẳng từ một tài khoản công ty, ở từng khoản bật chip Hóa đơn đến sau thanh toán. Khoản này không cần chọn tài khoản Nợ.
2. Duyệt hai cấp, chuyển tiền, bấm Ghi nhận đã thanh toán như hồ sơ thường.
3. Hoá đơn về: mở hồ sơ, ở phần Hóa đơn đến sau thanh toán bấm Nối hoá đơn đến sau, chọn tờ. Chọn được nhiều tờ cho một hồ sơ.
4. Phần đầu hiện "Cần ... đã nối ... đủ hoá đơn / còn thiếu / thừa".
5. Nối nhầm: bấm Gỡ ở dòng tờ đó.

Lưu ý:
- Tờ hoá đơn đã ghi sổ: lúc nối máy phân bổ phiếu chi vào tờ, 331 của tờ về 0.
- Tờ còn nháp: nối xong ghi sổ tờ như thường, máy tự phân bổ lúc ghi sổ.
- Gỡ: máy gỡ phần phân bổ, công nợ tờ trở lại, phiếu chi trở lại thành khoản trả trước, không huỷ phiếu chi.
- Hồ sơ đã chi theo cách cũ (ghi chi phí ngay) giữ đường cũ: khi nối, máy lập bút toán bù trừ.

Hạch toán:
- Lúc chi: Nợ 331 (NCC) / Có 1121.
- Hoá đơn về: Nợ chi phí + 1331 / Có 331 (tờ hoá đơn tự ghi).
- Đường cũ: lúc chi Nợ chi phí / Có 1121, lúc nối bút toán bù trừ Nợ 331 / Có chi phí.
<!-- kiểm: số tài khoản bút toán bù trừ đường cũ lấy từ ghi chú đầu tệp nghiệp vụ, chưa đối chiếu hàm sinh bút toán. -->

## Cấn trừ phí sàn với công nợ sàn (Grab, Shopee, Be)
Từ khoá: cấn trừ phí sàn, bù trừ phí sàn, phí Grab, phí ShopeeFood, phí BeFood, công nợ sàn, đối soát sàn, merchant, 131 sàn, cấn trừ 331 131, offset
Ai dùng: Kế toán (Accounts Manager duyệt)
Màn hình: Desk: Vagabond Can Tru San

Sàn trả tiền hàng sau khi đã giữ lại phí (gồm VAT). Phiếu này bù phần phí đã bị giữ vào công nợ phải thu của sàn, theo bảng đối soát.

Các bước:
1. Trên Desk mở Vagabond Can Tru San, tạo mới.
2. Chọn Công ty, Sàn, Điểm bán, Khách hàng công nợ sàn, Nhà cung cấp xuất phí. Điền Từ ngày, Đến ngày, Ngày bù, Mã bảng đối soát sàn, đính Bảng đối soát xác nhận phí đã giữ.
3. Bảng Hoá đơn phí: chọn hoá đơn phí, điền Phí đã gồm VAT bị sàn giữ.
4. Bảng Hoá đơn bán được bù: chọn hoá đơn bán, điền Công nợ được bù. Tổng hai bảng phải bằng nhau.
5. Tick Đã kiểm đúng pháp nhân, điểm bán và phí đã bị khấu trừ, rồi duyệt phiếu.
6. Đủ chứng từ thì máy ghi bút toán ngay. Hoá đơn phí chưa ghi sổ thì phiếu ở Chờ đối soát, máy tự thử lại; bấm Kiểm lại đối soát khi đã bổ sung.
7. Nút Xem công nợ sàn cho bảng đầu kỳ, doanh thu, tiền đã nhận, phí đã cấn, cuối kỳ.

Vì sao bị chặn:
- "Xác nhận đối soát phí đã bị sàn giữ trước khi duyệt."
- "Giữ phiếu đối soát để tra cứu. Dùng Hủy thay vì xóa vĩnh viễn."

Lưu ý: một phiếu một NCC (một MST); Grab và GrabVN lập riêng. Huỷ phiếu là đảo bút toán; không huỷ riêng bút toán.

Hạch toán: Nợ 331 (NCC xuất phí) / Có 131 (khách hàng công nợ sàn), gắn từng hoá đơn.

## Bù trừ công nợ phải thu và phải trả cùng một đối tác
Từ khoá: bù trừ công nợ, cấn trừ 131 331, đối trừ công nợ, cấn trừ giữa khách và nhà cung cấp, netting, offset, set-off, bút toán bù trừ, Journal Entry
Ai dùng: Kế toán
Màn hình: Bút toán (/but-toan); Desk: Payment Reconciliation

Dùng khi một đối tác vừa là khách vừa là nhà cung cấp, hai bên thống nhất trừ nợ cho nhau bằng biên bản bù trừ. Trường hợp phí sàn có màn riêng (xem mục cấn trừ phí sàn).

Các bước:
1. Mở Bút toán, bấm Lập bút toán, chọn Tự gõ từng dòng.
2. Điền Diễn giải (ghi số biên bản bù trừ), chọn Ngày hạch toán.
3. Bấm Thêm dòng, gõ 331, chọn tài khoản, chọn Bên Nợ, điền số tiền và mã nhà cung cấp.
4. Thêm dòng 131, chọn Bên Có, điền cùng số tiền và mã khách hàng.
5. Khi khung hiện Đã cân, bấm Lưu nháp hoặc Lưu và ghi sổ luôn.
6. Sau khi ghi sổ, mở Payment Reconciliation trên Desk để phân bổ bút toán vào đúng hoá đơn mua và hoá đơn bán.

Vì sao bị chặn:
- "Tài khoản ... là tài khoản công nợ, phải chọn khách hàng / nhà cung cấp."
- "Bút toán chưa cân: bên Nợ ..., bên Có ..."

Hạch toán: Nợ 331 (NCC) / Có 131 (khách hàng), số tiền theo biên bản.
<!-- kiểm: bút toán tay trên app không gắn hoá đơn, nên dư từng hoá đơn chỉ giảm sau bước phân bổ ở Payment Reconciliation. Chưa có luồng riêng trong app cho ca này; cần kế toán trưởng xác nhận cách làm. -->

## Xem công nợ phải trả và xuất Excel
Từ khoá: công nợ phải trả, công nợ nhà cung cấp, nợ NCC, phải trả người bán, 331, quá hạn, accounts payable, AP, dư hoá đơn, xuất Excel
Ai dùng: Kế toán, Thu mua
Màn hình: Công nợ phải trả (/cong-no-phai-tra)

Xem còn nợ NCC nào, hoá đơn nào quá hạn.

Các bước:
1. Mở Công nợ phải trả. Thẻ đầu là Dư hóa đơn theo bộ lọc, kèm số hoá đơn và số NCC.
2. Bấm nút công ty để chọn công ty khác.
3. Chọn chặng: Còn nợ, Quá hạn, Giảm một phần, Hết dư nợ, Tất cả.
4. Chọn ngày hoá đơn: Tháng này, Tháng trước, 7 ngày, Mọi ngày HĐ. Bấm Nhóm NCC để lọc theo nhóm.
5. Gõ tên NCC, mã ERP hoặc số hoá đơn vào ô tìm.
6. Xuất Excel dùng đúng bộ lọc đang chọn, đủ dòng của mọi trang.
7. Bấm Xem chứng từ ở một dòng để mở hoá đơn ERP hoặc hướng dẫn. Bấm Mở báo cáo công nợ lõi để xem báo cáo Accounts Payable.

Lưu ý:
- Số trên màn chỉ gồm hoá đơn mua thường đã ghi sổ, chưa bù trả trước hay bút toán khác, nên có thể khác dư tổng hợp NCC.
- Lọc ngày là chọn tập hoá đơn, không tính lại dư tại ngày quá khứ.
- Dư bằng 0 có thể do cấn trừ, không chứng minh đã có chuyển khoản mới.
- Nút Khoản đã trả trước ERP mở hướng dẫn xử lý hoá đơn cũ đã trả.

## Công nợ phải thu: gom hoá đơn và gửi QR đòi tiền khách
Từ khoá: công nợ phải thu, phải thu khách hàng, 131, đòi nợ, khách sỉ, gom hoá đơn, phiếu đề nghị thanh toán, QR, accounts receivable, AR, khách nợ
Ai dùng: Kế toán, Sales
Màn hình: Công nợ phải thu (/cong-no)

Khách sỉ, khách VIP gom nhiều hoá đơn trả một lần. Màn có ba tab: Đang nợ, Tiền đã về, Phiếu đã gửi.

Các bước:
1. Mở Công nợ phải thu, tab Đang nợ. Thẻ đầu có CÒN PHẢI ĐÒI, TIỀN ĐÃ VỀ CHỜ GHI SỔ, ĐÃ GỬI CHỜ TIỀN.
2. Bấm tên khách để mở danh sách hoá đơn (màu đỏ là nợ trên 30 ngày, cam là trên 15 ngày).
3. Tick từng hoá đơn, hoặc bấm Chọn hết.
4. Bấm Gom ... hoá đơn thành phiếu đề nghị thanh toán, rồi Tạo phiếu yêu cầu thanh toán công nợ.
5. Máy sinh phiếu kèm QR MB Bank sống 7 ngày. Gửi phiếu cho khách.
6. Theo dõi ở tab Phiếu đã gửi: Chờ tiền, Thu thiếu, Đã thu đủ, QR hết hạn, Đã huỷ.

Lưu ý: khách chuyển đúng QR thì SePay tự khớp và tự xoá nợ. Khoản tiền đã về mà phiếu thu chưa ghi sổ thì sổ cái vẫn tính là nợ.

Hạch toán: phiếu thu Nợ tiền gửi ngân hàng / Có 131 (khách hàng), gắn hoá đơn.
<!-- kiểm: số tài khoản Nợ của phiếu thu theo tài khoản nhận tiền đã khai, chưa đối chiếu mã nguồn. -->

## Khách đã chuyển tiền nhưng hoá đơn vẫn còn nợ
Từ khoá: khách đã chuyển tiền, tiền đã về, chưa trừ nợ, phiếu thu nháp, UNC khách gửi, ghi sổ phiếu thu, khớp giao dịch, chuyển khoản không ghi mã
Ai dùng: Kế toán, Sales
Màn hình: Công nợ phải thu (/cong-no)

Hai tình huống: tiền về nhưng nội dung chuyển khoản không có mã đơn nên máy không tự khớp; hoặc máy đã lập phiếu thu nháp nhưng còn chờ ảnh UNC khách gửi.

Các bước khi hoá đơn còn ở tab Đang nợ:
1. Mở khách, ở dòng hoá đơn bấm Khách đã chuyển tiền.
2. Danh sách giao dịch tiền vào chưa nối hiện ra, có ô tìm theo nội dung, mã giao dịch, số tiền, ngày. Dòng có dấu tích là khớp mã đơn hoặc số điện thoại.
3. Chọn đúng giao dịch, bấm Đúng khoản này. Máy lập phiếu thu nháp, hoá đơn sang tab Tiền đã về.

Các bước ở tab Tiền đã về:
1. Lọc theo nguồn, kỳ hoặc ô tìm.
2. Bấm Đính UNC khách gửi, chọn ảnh chuyển khoản.
3. Kế toán bấm Lưu và ghi sổ (hoặc Ghi sổ phiếu thu khi đã có UNC). Người khác bấm Lưu uỷ nhiệm chi, kế toán ghi sổ sau.

Lưu ý: máy chỉ gợi ý, không tự gán theo số tiền. Không thấy giao dịch nào thì kiểm lại sao kê hoặc nhập sao kê bù. Ghi sổ phiếu thu bắt buộc có ảnh UNC khách gửi (anh Việt chốt 28/09/2026).

Hạch toán: Nợ tiền gửi ngân hàng / Có 131, gắn hoá đơn.

## Lập hồ sơ thanh toán (APP): chọn đúng đường
Từ khoá: hồ sơ thanh toán, APP, đề nghị thanh toán, lập APP, trả nhà cung cấp, chi thẳng tài khoản công ty, hoàn ứng, đề nghị chi, payment request
Ai dùng: Thu mua, Kế toán
Màn hình: Hồ sơ thanh toán (/ho-so-thanh-toan)

Hồ sơ thanh toán là chứng từ đề nghị trả tiền, duyệt hai cấp (kế toán rồi giám đốc).

Các bước:
1. Mở Hồ sơ thanh toán, bấm dấu cộng.
2. Câu "Khoản chi này đi theo đường nào?":
   - Trả cho nhà cung cấp qua công nợ: tiền đi từ tài khoản MB tới bên bán theo đợt trả công nợ.
   - Chi thẳng từ một tài khoản công ty: không qua công nợ Purchasing, vào thẳng màn lập.
   - Hoàn lại cho người đã ứng tiền ra.
3. Câu "Hoá đơn mua đã nằm trong hệ chưa?":
   - Đã có, đang nợ trên sổ: tick các hoá đơn còn nợ.
   - Chưa có: với NCC là khoản trả trước; với hoàn ứng là gõ tay từng khoản, máy tự sinh hoá đơn mua khi giám đốc duyệt.
4. Điền đủ, đính chứng từ, bấm Gửi kế toán duyệt.

Vì sao bị chặn:
- "Hoá đơn ... chưa ghi sổ nên chưa đề nghị trả được."
- "Chưa chọn tài khoản ngân hàng của công ty để chi."
- "Khoản ... chưa chọn tài khoản Nợ."
- Hồ sơ hoàn ứng thiếu tài khoản nhận: bấm Chọn TK nhận rồi gửi lại.

Lưu ý: "đã có" nghĩa là kế toán ĐÃ NHẬP hoá đơn vào hệ. Cầm tờ hoá đơn giấy mà kế toán chưa nhập thì vẫn chọn Chưa có.

## Duyệt hồ sơ thanh toán và ghi nhận đã thanh toán
Từ khoá: duyệt APP, kế toán duyệt, giám đốc duyệt, ghi nhận đã thanh toán, dò SePay, đối chiếu tay, bỏ đối chiếu, xoá công nợ, thư báo nhà cung cấp
Ai dùng: Kế toán, Giám đốc
Màn hình: Hồ sơ thanh toán (/ho-so-thanh-toan)

Các bước:
1. Kế toán mở hồ sơ ở trạng thái chờ kế toán, bấm Kế toán duyệt.
2. Giám đốc bấm Giám đốc duyệt. Hồ sơ hoàn ứng: lúc này máy lập hoá đơn mua cho từng khoản.
3. Chuyển khoản, ghi mã hồ sơ vào nội dung để máy tự khớp.
4. Bấm Dò SePay để xem ngân hàng đã chi đủ chưa. Trả qua tính năng thanh toán hoá đơn điện, nước của app ngân hàng thì bấm Đối chiếu tay, tìm theo số tiền.
5. Đủ tiền thì bấm Ghi nhận đã thanh toán. Máy lập bút toán xoá công nợ và tự gửi thư báo kèm UNC cho NCC.
6. Từ chối thì bấm Từ chối và ghi lý do.

Vì sao bị chặn:
- "Người lập hồ sơ không tự duyệt được, nhờ người khác duyệt giúp."
- "Bạn đã ký ở cấp kế toán cho hồ sơ này rồi. Hai cấp duyệt phải là hai người khác nhau."
- "Hồ sơ đang ở ... Phải duyệt xong hai cấp mới chuyển tiền được."
- "Hồ sơ đã thanh toán rồi, không huỷ được."

Lưu ý: Bỏ đối chiếu chỉ làm được khi sao kê hết liên kết và hồ sơ không còn bút toán đã ghi sổ. Không chuyển tiền thêm chỉ vì bút toán đã huỷ. Có thể Xem trước và Gửi thử thư báo trước khi trả.

Hạch toán (hồ sơ trả NCC): phiếu chi Nợ 331 (NCC, gắn hoá đơn) / Có tài khoản ngân hàng chi.

## Duyệt phiếu chi
Từ khoá: duyệt phiếu chi, phiếu chi, payment entry, xác nhận hợp lệ, duyệt chi, xác nhận đã chuyển tiền, trả lại, AP Officer, FIN, UNC
Ai dùng: AP Officer, Kiểm soát tài chính (FIN), Giám đốc
Màn hình: Duyệt phiếu chi (/thanh-toan)

Màn chỉ hiện phiếu CHI (tiền đi ra), không hiện phiếu thu tiền khách.

Các bước theo trạng thái:
1. Nháp: người lập bấm Gửi kiểm tra, phiếu sang Chờ kế toán kiểm tra.
2. Kế toán (FIN) bấm Xác nhận hợp lệ, hoặc Trả lại.
3. Giám đốc bấm Duyệt chi, phiếu sang Đã duyệt chi, chờ chuyển tiền. Giám đốc duyệt chưa ghi sổ.
4. Kế toán chuyển tiền thật, đính UNC, khớp giao dịch ngân hàng, rồi bấm Xác nhận đã chuyển tiền. Phiếu sang Đã chuyển tiền, đã ghi sổ.
5. Phiếu Bị trả lại: người lập sửa rồi Gửi kiểm tra lại.

Lưu ý: bước Xác nhận đã chuyển tiền có kiểm UNC và giao dịch ngân hàng trước khi ghi sổ.

Hạch toán: Nợ 331 (hoặc tài khoản theo loại chi) / Có tài khoản tiền chi.
<!-- kiểm: điều kiện cụ thể của bước Xác nhận đã chuyển tiền (bắt buộc UNC hay sao kê) chưa đọc hết. -->

## Lập bút toán tay theo định khoản mẫu
Từ khoá: bút toán, bút toán tay, hạch toán tay, định khoản, journal entry, JE, trích lương, bảo hiểm, phân bổ 242, khấu trừ GTGT, nộp thuế, phí ngân hàng, rút tiền, nộp tiền, kết chuyển giá thành
Ai dùng: Kế toán
Màn hình: Bút toán (/but-toan)

Các bước:
1. Mở Bút toán, bấm Lập bút toán.
2. Chọn việc theo mẫu: Trích lương phải trả nhân viên, Trích bảo hiểm phần công ty chịu, Khấu trừ bảo hiểm vào lương nhân viên, Chi trả lương, Ghi nhận chi phí trả trước, Phân bổ chi phí trả trước hàng tháng, Khấu trừ thuế GTGT cuối kỳ, Nộp thuế vào ngân sách, Phí ngân hàng và phí dịch vụ nhỏ, Rút tiền gửi về quỹ tiền mặt, Nộp tiền mặt vào ngân hàng, Kết chuyển chi phí sản xuất vào giá thành. Hoặc Tự gõ từng dòng.
3. Sửa Diễn giải, bấm ô ngày để chọn Ngày hạch toán.
4. Điền số tiền cho dòng cần dùng. Dòng nền xám là máy tự tính cho cân. Dòng công nợ thì điền Mã khách hàng hoặc nhà cung cấp.
5. Bấm Thêm dòng để thêm tài khoản (gõ số hiệu hoặc tên, chọn Bên Nợ hay Bên Có). Bấm dấu x để bỏ dòng.
6. Khung dưới hiện Đã cân thì bấm Lưu nháp hoặc Lưu và ghi sổ luôn.

Vì sao bị chặn:
- "Bút toán phải có ít nhất hai dòng có số tiền."
- "Bút toán chưa cân: bên Nợ ..., bên Có ..., lệch ..."
- "Tài khoản ... là tài khoản nhóm, không hạch toán thẳng vào được."
- "Tài khoản của bạn không có quyền ghi sổ bút toán." (Accounts User lưu nháp được, ghi sổ cần Accounts Manager hoặc FIN)

Lưu ý: mẫu ghi "thiếu ... TK" là công ty chưa có tài khoản đó, báo kế toán trưởng.

## Ghi sổ, đổi tài khoản, huỷ bút toán
Từ khoá: ghi sổ bút toán, sửa bút toán, đổi tài khoản, huỷ bút toán, bút toán nháp, cancel journal entry, sai tài khoản
Ai dùng: Kế toán
Màn hình: Bút toán (/but-toan)

Các bước:
1. Mở Bút toán. Lọc bằng chip Tất cả, Còn nháp, Đã ghi sổ, Đã huỷ, hoặc gõ diễn giải, mã bút toán vào ô tìm. Màn hiện 60 ngày gần nhất.
2. Bấm một bút toán để xem định khoản.
3. Bút toán nháp: dòng đổi được có nút Đổi tài khoản. Gõ số hiệu hoặc tên tài khoản, chọn tài khoản mới.
4. Bấm Ghi sổ để ghi.
5. Bút toán đã ghi sổ sai: bấm Huỷ bút toán, ghi lý do (bắt buộc), rồi lập lại bút toán đúng.

Vì sao bị chặn:
- "Chỉ sửa được bút toán còn nháp. Bút toán đã ghi sổ thì huỷ rồi lập lại."
- "Dòng công nợ gắn nhà cung cấp, khách hoặc hoá đơn thì không đổi tài khoản được."
- "Bút toán này không còn ở dạng nháp."
- "Sổ ngày ... đã khoá ...": xem mục khoá sổ.

Lưu ý: khoản trả trước khi lên ERP không ghi sổ ở đây, duyệt ở Công nợ phải trả. Huỷ không xoá: tờ vẫn nằm trong sổ ở trạng thái đã huỷ. Bút toán của kỳ đã chốt hoặc đã đối chiếu thì liên hệ kế toán trưởng trước khi huỷ.

## Đối chiếu hoá đơn mua với phiếu nhập kho và ghi sổ
Từ khoá: đối chiếu hoá đơn mua, đối chiếu mua, nối phiếu nhập kho, khớp và ghi sổ, ghi sổ hoá đơn mua, purchase invoice, 3-way match, lệch tiền, hoá đơn nháp
Ai dùng: Kế toán, Thu mua, Quản lý kho
Màn hình: Đối chiếu mua (/doi-chieu-mua)

Hoá đơn NCC về (từ m-invoice) nằm ở dạng nháp. Màn này tìm phiếu nhập kho khớp, chỉ ra chỗ lệch, rồi nối và ghi sổ.

Các bước:
1. Mở Đối chiếu mua, chọn khoảng ngày và nhóm (Chờ đối chiếu, Lệch, Không thấy phiếu nhập nào, Đã nối phiếu chờ ghi sổ...).
2. Bấm một hoá đơn. Máy gợi ý phiếu nhập, so từng món, đơn vị, tiền.
3. Lệch đơn vị thì dùng nút đổi đơn vị hoặc khai quy đổi ngay trên dòng.
4. Kế toán bấm Khớp và ghi sổ (hoặc Chỉ nối phiếu). Thu mua chỉ có nút Nối phiếu, chuyển kế toán ghi sổ.
5. Hoá đơn không có phiếu nhập (xăng dầu, dịch vụ, phí ship): kế toán bấm Ghi sổ thẳng, không nối phiếu.
6. Nối nhầm: bấm Bỏ nối, chọn lại phiếu từ đầu.

Vì sao bị chặn:
- "Hoá đơn ... đã ghi sổ rồi, không nối lại được."
- "Phiếu nhập ... không phải của nhà cung cấp này."
- Chip "Phiếu nhập đã bị hoá đơn khác lấy, nối lại": nhờ kế toán kiểm hoá đơn kia. Không nhập thêm kho để vượt cảnh báo.

Lưu ý: tờ có chip Hồ sơ là chứng từ hoá đơn đến sau của hồ sơ chi, không ghi sổ ở đây.

Hạch toán: Nợ 152/156 hoặc chi phí + 1331 / Có 331 (NCC).
<!-- kiểm: tài khoản Nợ phụ thuộc kho và loại món, xem tài liệu tài khoản tồn kho theo kho. -->

## Xem hoá đơn mua vào và hoá đơn bán ra
Từ khoá: hoá đơn mua, hoá đơn mua vào, purchase invoice, hoá đơn bán, hoá đơn bán ra, sales invoice, tra cứu hoá đơn, còn nợ, quá hạn
Ai dùng: Kế toán
Màn hình: Hoá đơn mua (/hoa-don-mua); Hoá đơn bán (/hoa-don-ban)

Hoá đơn mua vào:
1. Chọn khoảng 30 ngày, 60 ngày, 6 tháng, 1 năm. Chọn nhóm.
2. Gõ mã phiếu, tên NCC hoặc số hoá đơn vào ô tìm.
3. Mỗi dòng ghi còn nháp, đã huỷ, hạn trả, quá hạn bao nhiêu ngày, đã trả xong, và số còn nợ.

Hoá đơn bán ra:
1. Chọn 7 ngày, 30 ngày, 3 tháng, 1 năm. Chọn điểm bán: Cả ba điểm, Sales Online, District 1, NVHTN.
2. Chọn nhóm, gõ mã phiếu, tên khách hoặc số hoá đơn điện tử vào ô tìm.
3. Mỗi dòng ghi số và trạng thái hoá đơn điện tử (hoặc "chưa xuất hoá đơn điện tử"), phương thức thanh toán, người bán, trạng thái kho, số còn phải thu.

Lưu ý: thẻ đầu ghi tổng tiền, số hoá đơn, còn nợ hoặc còn phải thu. Danh sách dài bị cắt thì màn báo, thu hẹp bằng ngày hoặc ô tìm.

## Hoá đơn điện tử: khi nào xuất, xem trạng thái, ngày cũ chưa xuất
Từ khoá: hoá đơn điện tử, HĐĐT, e-invoice, m-invoice, xuất hoá đơn, phát hành hoá đơn, ký số, chờ ký, chưa xuất hoá đơn, hoá đơn ngày cũ
Ai dùng: Kế toán, Quản lý
Màn hình: Hoá đơn bán (/hoa-don-ban); Cài đặt cuối ngày (/cai-dat-cuoi-ngay)

Chỉ hoá đơn bán ĐÃ GHI SỔ mới được phát hành sang m-invoice. Điểm bán nào chưa bật trong Cài đặt cuối ngày thì hoá đơn nằm yên trong hệ.

Xem trạng thái: mở Hoá đơn bán, mỗi dòng ghi số HĐ và trạng thái, hoặc "chưa xuất hoá đơn điện tử".

Tờ đã ghi sổ mà đêm đó không lên được m-invoice:
1. Mở Cài đặt cuối ngày, phần Hoá đơn ngày cũ chưa xuất được.
2. Chọn Ngày bán, bấm Xem và xuất hoá đơn cho ngày này.
3. Máy xem trước: số tờ, tổng tiền, giữ ngày bán hay lấy ngày lập là hôm nay. Đọc kỹ rồi mới đồng ý.
4. Quá hạn ký gửi thì cần quản lý xác nhận; máy không tự đổi ngày lập.

Lưu ý:
- Khung "Khoá gốc bên m-invoice đang chặn" nghĩa là cấu hình m-invoice đang tắt phát hành hoặc tắt ký, báo kế toán mở lại.
- Sửa, huỷ, thay thế hoá đơn điện tử đã phát hành: liên hệ kế toán trưởng. Không tự làm.
- Tờ đang giữ cờ đối chiếu chỉ được gỡ cờ khi máy đã hỏi m-invoice và không có tờ nào.

## Nhập tệp sao kê ngân hàng
Từ khoá: nhập sao kê, sao kê ngân hàng, bank statement, import sao kê, thiếu giao dịch, nạp bù sao kê, Excel ngân hàng, CSV, SePay thiếu
Ai dùng: Kế toán
Màn hình: Nhập sao kê (/nhap-sao-ke)

Dùng khi SePay sót giao dịch, cần nạp bù từ tệp ngân hàng gửi.

Các bước:
1. Mục 1. Chọn tài khoản: chọn tài khoản ngân hàng.
2. Mục 2. Chọn tệp sao kê: bấm Chọn tệp .xlsx hoặc .csv. Tệp phải có cột Nội dung và PS giảm hoặc PS tăng; mấy dòng đầu ghi tên ngân hàng, kỳ sao kê cứ để nguyên.
3. Mục 3. Xem trước, chưa ghi gì: máy đếm dòng sẽ thêm, dòng đã có, dòng hỏng.
4. Bấm Ghi ... dòng vào sổ, đồng ý ở hộp hỏi.

Vì sao bị chặn:
- "Tệp nặng quá 20 MB. Vui lòng cắt sao kê theo tháng rồi tải từng tệp."
- "Chưa có tài khoản ngân hàng nào trên hệ. Khai ở Desk rồi quay lại."

Lưu ý: máy chỉ thêm dòng còn thiếu, không ghi đè dòng đã có. Ghi rồi muốn bỏ thì phải huỷ từng dòng trên Desk, liên hệ kế toán trưởng.

## Ký nhận biên nhận nộp tiền mặt
Từ khoá: nộp quỹ, nộp tiền mặt, biên nhận nộp tiền, ký nhận tiền, tiền mặt quầy, bảng kê mệnh giá, lệch tiền mặt, cash deposit
Ai dùng: Kế toán, Giám đốc, Thu ngân
Màn hình: Biên nhận nộp tiền mặt (kế toán) (/nop-quy)

Thu ngân lập biên nhận, đếm tiền theo mệnh giá và ký bên giao. Kế toán hoặc giám đốc đếm lại và ký nhận.

Các bước (kế toán):
1. Mở Biên nhận nộp tiền mặt (kế toán). Lọc theo trạng thái (Nháp, Chờ ký nhận, Đã nộp quỹ, Đã huỷ), khoảng ngày, ô tìm.
2. Mở phiếu Chờ ký nhận. Đối chiếu bảng kê mệnh giá với tiền thực nhận; dòng đỏ "Lệch ..." là chênh với số kỳ vọng.
3. Bấm Ký nhận tiền (kế toán / giám đốc), ký bằng ngón tay vào khung, bấm Xong, lưu chữ ký.
4. Bấm Tải biên bản PDF để lưu. Bấm Tải Excel ở danh sách để xuất theo bộ lọc.

Vì sao bị chặn:
- "Chỉ kế toán hoặc giám đốc được ký nhận tiền."
- "Bên giao và bên nhận không được là cùng một người."
- "Phiếu đang ở trạng thái ..., chưa hoặc không còn chờ ký nhận."

Lưu ý: ký nhận xong phiếu khoá cứng, kể cả bảng mệnh giá. Lệch tiền thì do anh Việt quyết cách xử lý.
<!-- kiểm: chưa thấy biên nhận này tự sinh bút toán quỹ; kế toán có thể phải hạch toán chuyển quỹ riêng. -->

## Chi tiền và đóng phiếu hoàn tiền khách
Từ khoá: hoàn tiền, cash-back, refund, trả lại tiền khách, phiếu hoàn tiền, đối soát lệnh chi, uỷ nhiệm chi hoàn tiền, phiếu chi hoàn tiền
Ai dùng: Kế toán
Màn hình: Hoàn tiền (/hoan-tien)

Sales lập phiếu hoàn tiền. Kế toán chuyển khoản trả khách từ tài khoản MB công ty, rồi khép phiếu.

Các bước:
1. Mở Hoàn tiền. Lọc chip Chờ chi, Đã chi, Đã đối soát, Hoàn thành, Đã huỷ / Từ chối; gõ ô tìm rồi Enter.
2. Mở phiếu Chờ chi, chuyển khoản với nội dung bắt đầu bằng THE VAGABOND HOAN TIEN kèm mã phiếu.
3. Ở danh sách bấm Đối soát lệnh chi để máy khớp giao dịch ngân hàng. Máy báo riêng phiếu lệch số tiền và phiếu trùng giao dịch.
4. Mở phiếu, bấm Đính uỷ nhiệm chi, chọn tệp UNC.
5. Gửi tệp UNC cho khách, rồi bấm Hoàn thành và ghi sổ.

Lưu ý: dòng sao kê SePay không thay được UNC khi giải trình với cơ quan thuế, nên phiếu chỉ khép được khi có tệp UNC. Ghi sổ rồi không sửa được, chỉ huỷ bút toán. Hoàn hay không, hoàn bao nhiêu là việc do anh Việt quyết.

Hạch toán: phiếu chi Nợ 131 (khách) / Có tài khoản ngân hàng MB.
<!-- kiểm: tài khoản Nợ của phiếu chi hoàn tiền và chân thu đi kèm chưa đọc trong hàm sinh phiếu. -->

## Khai tài sản và chạy khấu hao
Từ khoá: tài sản, tài sản cố định, TSCĐ, công cụ dụng cụ, CCDC, khấu hao, phân bổ 242, 214, asset, depreciation, ghi sổ tài sản
Ai dùng: Kế toán
Màn hình: Tài sản (/tai-san)

Các bước khai:
1. Lần đầu: bấm Lập sáu nhóm tài sản.
2. Bấm Khai tài sản, chọn nhóm (nhóm quyết định số năm và tài khoản chi phí).
3. Lần lượt điền tên (ghi như trên hoá đơn), nguyên giá (chưa gồm thuế GTGT được khấu trừ), ngày bắt đầu dùng, số năm sử dụng, số đã trích khấu hao trước (nếu có), nơi để.
4. Bấm Khai và ghi sổ. Máy dựng lịch khấu hao theo tháng.
5. Tài sản còn nháp: mở, bấm Ghi sổ tài sản này.

Các bước khấu hao hằng tháng:
1. Ở Tài sản bấm Khấu hao. Màn hiện số kỳ tới hạn, tổng tiền, chia theo bộ phận.
2. Bấm Ghi sổ khấu hao ... kỳ, đồng ý.

Vì sao bị chặn: nhóm Công cụ dụng cụ chưa lập được vì tài khoản 242 chưa đánh dấu là tài khoản giữ giá trị; bấm Xem và mở khoá, đọc kỹ rồi mới đồng ý (sửa bảng tài khoản).

Hạch toán: Nợ chi phí khấu hao của bộ phận (6274 bếp, 6424 quản lý...) / Có 2141 hao mòn; công cụ dụng cụ Có 242. Bút toán đã ghi chỉ huỷ được, không xoá.

## Khoá sổ và vì sao báo "Sổ đã khoá"
Từ khoá: khoá sổ, khóa sổ, chốt sổ, sổ đã khoá, không huỷ được, không sửa được hoá đơn cũ, mở khoá, period closing, lock
Ai dùng: Kế toán trưởng, Giám đốc
Màn hình: Khoá sổ (/khoa-so)

Chứng từ của ngày đã khoá thì không ghi sổ, không huỷ, không sửa được nữa, trên app hay trên máy tính đều vậy.

Các bước cài:
1. Mở Khoá sổ. Thẻ xanh "Đang khoá đến hết ..." hoặc thẻ cam "Chưa khoá gì".
2. Tự khoá sau bao nhiêu ngày: chọn Không khoá, 3, 7, 15, 31 ngày, hoặc gõ ở ô Số ngày khác.
3. Mốc khoá cứng: chọn ngày cuối kỳ đã chốt (không chọn được hôm nay). Để trống nếu chưa cần.
4. Bấm Lưu cấu hình khoá sổ.

Vì sao bị chặn:
- "Sổ ngày ... đã khoá (khoá đến hết ...) nên không đụng vào ... được nữa ...": chứng từ thuộc kỳ đã chốt. Liên hệ kế toán trưởng; cần sửa thật thì kế toán mở khoá riêng tờ đó, máy ghi lý do và tên người mở.
- "Chỉ kế toán trưởng hoặc giám đốc mới đụng được vào khoá sổ."

Lưu ý: thẻ đỏ "Đang có ... hoá đơn được mở khoá" nhắc sửa xong phải đóng lại. Danh sách loại chứng từ áp dụng ghi ở cuối màn.
<!-- kiểm: chưa thấy nút mở khoá riêng một tờ trên app; có thể chỉ làm trên Desk. -->
