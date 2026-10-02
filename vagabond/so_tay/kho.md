# Kho

## Tạo phiếu nhập kho khi nhà cung cấp giao hàng
Từ khoá: nhập kho, phiếu nhập, phiếu nhập kho, nhận hàng, nhận hàng nhà cung cấp, hàng về, PNK, purchase receipt, goods receipt, nhập mua, đếm hàng nhập
Ai dùng: Kho (thủ kho), Thu mua, Kế toán
Màn hình: Nhập kho (/nhap-kho)

Hàng nhà cung cấp giao tới thì thủ kho đếm và nhập kho trên app. Phiếu nhập kho nháp do thu mua tạo từ Đơn mua hàng nằm ở tab Chờ nhận.
<!-- kiểm: thu mua tạo phiếu nháp trên Desk từ Đơn mua hàng (nút Tạo > Phiếu nhập kho) hay đường nào khác -->

Các bước:
1. Mở màn Nhập kho. Có bốn tab: Chờ nhận, Còn phải nhận, Đã nhập kho, Đã huỷ.
2. Bấm biểu tượng máy ảnh ở góc trên để quét mã vạch số phiếu in trên tờ phiếu, hoặc chọn phiếu trong tab Chờ nhận.
3. Mỗi món có ô Số lượng thực nhận, máy điền sẵn số còn lại phải nhận (không phải số đặt ban đầu). Đếm tới đâu sửa số tới đó bằng nút trừ, cộng hoặc gõ số.
4. Bấm dấu ✓ ở từng món để đánh dấu đã đếm, hoặc bấm máy ảnh để quét mã từng món.
5. Mục Chứng từ giao nhận (không bắt buộc): đính Ảnh hàng đã nhận (1), (2) và bản scan biên bản giao nhận của NCC.
6. Bấm Xác nhận nhập kho, rồi bấm Nhập kho ở hộp xác nhận.

Lưu ý:
- Xác nhận xong là phiếu khoá lại, muốn sửa phải báo kế toán.
- Món nào nhận thiếu thì phần còn lại vẫn treo trên đơn mua, nhận tiếp ở tab Còn phải nhận.
- Đơn có món chưa có đơn giá vẫn nhập kho được nhưng giá vốn ghi 0, báo kế toán bổ sung giá.

Hạch toán: Nợ 152 (tài khoản của kho nhận) / Có 3311 Phải trả người bán, hàng về chưa có hoá đơn.

## Nhận hàng đợt sau khi nhà cung cấp giao thiếu
Từ khoá: giao thiếu, nhận đợt 2, nhận tiếp, còn nợ hàng, còn phải nhận, giao làm nhiều đợt, giao từng phần, partial receipt, đơn mua còn thiếu, hàng về sau
Ai dùng: Kho, Thu mua
Màn hình: Nhập kho (/nhap-kho), tab Còn phải nhận

Đơn mua nào nhà cung cấp mới giao một phần thì nằm ở tab Còn phải nhận cho tới khi nhận đủ. Đơn trễ hẹn hiện chip đỏ "Trễ N ngày" và đứng đầu danh sách.

Các bước:
1. Mở Nhập kho, chọn tab Còn phải nhận, bấm vào đơn cần nhận.
2. Màn Nhận hàng đợt N hiện ba con số cho từng món: Đặt, Đã nhận, Còn lại. Phần Đã nhận các đợt trước liệt kê ở trên.
3. Ô Số lượng thực nhận điền sẵn số Còn lại. Sửa theo số đếm thật. Món đã nhận đủ bị làm mờ, không gõ được.
4. Đính ảnh hàng và biên bản nếu có.
5. Bấm Xác nhận nhận hàng đợt N, rồi bấm Nhận hàng.

Lưu ý:
- Mỗi đợt máy lập một phiếu nhập kho mới từ đơn mua, không cần thu mua tạo phiếu nháp.
- Xong máy báo số phiếu và đơn còn nợ bao nhiêu. Còn nợ thì đơn vẫn ở tab Còn phải nhận.

Vì sao bị chặn:
- "Đơn ... chưa ghi sổ nên chưa nhận hàng được": báo thu mua gửi duyệt đơn.
- "Đơn ... đã đóng nên không nhận thêm được": mở lại đơn bên phần Đơn mua hàng.
- "Trong lúc anh chị đang đếm thì ... đã được người khác nhận mất rồi": thoát ra mở lại đơn để lấy số còn lại mới nhất.

## Nhà cung cấp giao dư hoặc báo không giao nữa
Từ khoá: giao dư, giao thừa, nhận dư, vượt số đặt, dung sai, over delivery, đóng đơn, không giao nữa, hết hàng, đóng phần còn lại, huỷ phần còn lại
Ai dùng: Kho, Thu mua
Màn hình: Nhập kho (/nhap-kho)

Giao dư:
- Ở tab Còn phải nhận, nhà cung cấp giao dư trong mức dung sai (phần trăm hiện trên màn) thì máy cho nhận và ghi lại vết trên phiếu. Dư quá mức thì bị chặn với câu "Nhận dư quá mức cho phép".
- Ở tab Chờ nhận (phiếu nháp), máy không cho nhập quá số còn lại phải nhận.
- Dư nhiều thì báo thu mua lên đơn bổ sung rồi nhập sau, không nhập dồn vào đơn cũ.

Không giao nữa:
1. Mở đơn ở tab Còn phải nhận.
2. Bấm nút "Nhà cung cấp không giao nữa · đóng phần còn lại".
3. Ghi lý do (bắt buộc), ví dụ nhà cung cấp báo hết hàng.
4. Bấm Đóng phần còn lại.

Lưu ý:
- Đóng xong đơn không hiện ở tab Còn phải nhận nữa. Số đã đặt giữ nguyên, không xoá dòng nào, mở lại được bất cứ lúc nào.
- Mức dung sai giao dư do quản lý đặt trong phần Cài đặt kho. <!-- kiểm: tên màn cài đặt dung sai (Cài đặt kho, khoá CDKHO) chưa có trong bảng địa chỉ -->

## Vì sao không xác nhận nhập kho được
Từ khoá: lỗi nhập kho, không nhập kho được, bị chặn nhập kho, phiếu nhập báo lỗi, không ghi được phiếu nhập, lỗi nhận hàng
Ai dùng: Kho, Thu mua
Màn hình: Nhập kho (/nhap-kho)

Vì sao bị chặn:
- "Chưa có món nào có số lượng, chưa nhập kho được": mọi ô Số lượng thực nhận đang là 0.
- "Nhà cung cấp giao dư ... món so với số còn phải nhận": trên phiếu nháp chỉ nhập đúng số còn lại, phần dư báo thu mua lên đơn bổ sung.
- "Phiếu vừa được sửa. Mở lại phiếu để lấy số liệu mới rồi nhận hàng": có người vừa sửa phiếu nháp, thoát ra mở lại.
- "Số thực nhận phải lớn hơn 0 và không vượt phiếu nháp": sửa lại số.
- "Chỉ nhận hàng trên phiếu nháp nhập mua, không phải phiếu trả": phiếu đang mở là phiếu trả nhà cung cấp.
- "Màn nhận hàng chỉ mở cho kho, thu mua và kế toán": báo quản lý cấp thêm quyền Kho.
- "Không thấy phiếu ... trong hệ thống" khi quét: mã vạch in sai hoặc phiếu chưa tạo. "Phiếu ... đã nhập máy xong rồi": phiếu đã ở tab Đã nhập kho.

Lưu ý: phiếu đã nhập kho sai số thì không tự sửa, liên hệ kế toán trưởng.

## Nối phiếu nhập kho với hoá đơn mua
Từ khoá: nối phiếu, nối phiếu nhập kho, gắn phiếu nhập vào hoá đơn, đối chiếu hoá đơn mua, khớp hoá đơn với phiếu nhập, HDM, PNK, purchase invoice, ghi sổ hoá đơn mua, 3 way match
Ai dùng: Thu mua, Kế toán
Màn hình: Đối chiếu mua (/doi-chieu-mua)

Hàng nhập kho trước, hoá đơn nhà cung cấp về sau. Hoá đơn mua phải nối với phiếu nhập kho của đúng lô hàng đó thì mới ghi sổ đúng giá vốn.

Các bước:
1. Mở màn Đối chiếu hoá đơn mua, lọc nhóm Chờ đối chiếu hoặc Lệch tiền, bấm vào tờ hoá đơn.
2. Phần "Phiếu nhập kho của nhà cung cấp này" liệt kê các phiếu còn chưa hoá đơn nào lấy. Chạm để chọn (hiện ✅) một hoặc nhiều phiếu.
3. Xem bảng so sánh từng dòng: lệch số lượng, lệch đơn giá, lệch đơn vị.
4. Thu mua bấm "🔗 Nối phiếu, chuyển kế toán ghi sổ". Kế toán thấy hai nút "🔗 Chỉ nối phiếu" và "✅ Khớp và ghi sổ".

Lưu ý:
- Nối xong tờ hoá đơn nằm ở nhóm Chờ ghi sổ cho kế toán.
- Không bấm nút "Lấy mặt hàng từ" trên Desk: nó chép đè dòng hàng, làm mất dòng phí dịch vụ, phí giao hàng.
- Hoá đơn đang bật Cập nhật tồn kho thì không nối được, nhờ tắt ô đó bên Desk.
- Hàng không qua kho (xăng, dịch vụ, phí ship) không có phiếu nhập: kế toán bấm "✅ Ghi sổ thẳng, không nối phiếu".
<!-- kiểm: nút "Nối phiếu nhập kho" trên Desk: mã nói chỉ gắn, màn Đối chiếu mua nói chép đè giá; có nên hướng dẫn không -->

Hạch toán: Nợ 3311 và Nợ 133 / Có 331 Phải trả người bán. <!-- kiểm: tài khoản kế toán chị Dung xác nhận -->

## Vì sao không nối được phiếu nhập kho vào hoá đơn
Từ khoá: lỗi nối phiếu, không nối được, lệch đơn vị, lệch giá hoá đơn, hoá đơn lệch phiếu nhập, dấu nối cũ, chưa nối phiếu nhập, không ghi sổ được hoá đơn mua
Ai dùng: Thu mua, Kế toán
Màn hình: Đối chiếu mua (/doi-chieu-mua)

Vì sao bị chặn:
- "Chưa nối được vì lệch đơn vị": hoá đơn điện tử ghi đơn vị máy chưa biết. Bấm "Đổi đơn vị dòng này thành ..." cho dòng đó, hoặc "Khai đơn vị ... cho món này" để lần sau máy tự hiểu.
- "Phiếu nhập đã bị hoá đơn khác lấy mất lượng": bấm Nối phiếu lại để máy chia theo lượng còn thật, hoặc "Bỏ nối, chọn lại phiếu từ đầu".
- "Dòng N: món ... là hàng qua kho mà chưa nối phiếu nhập": hàng qua kho không ghi sổ thẳng được, phải nối phiếu trước.
- "Giá trên hoá đơn khác giá phiếu nhập": tờ vẫn ghi sổ được nhưng phải là kế toán ghi.
- "Lệch so với hoá đơn điện tử của nhà cung cấp": bấm "Dựng lại theo hoá đơn điện tử" nếu có nút.
- "Không thấy phiếu nhập kho nào...": hàng chưa nhập kho hoặc phiếu nhập còn nháp. Nhập kho trước rồi quay lại.
- "Chỉ kế toán hoặc thu mua mới nối phiếu và ghi sổ hoá đơn mua được": cần quyền phù hợp.

## Xác nhận hàng chuyển về kho tôi
Từ khoá: nhận điều chuyển, nhận hàng điều chuyển, hàng chuyển về, hàng về kho bếp, hàng về cửa hàng, xác nhận nhận hàng, nhận thiếu, kho khác chuyển sang, transfer receipt, PDC
Ai dùng: Bếp, Cửa hàng, mọi bộ phận giữ kho
Màn hình: Hàng chuyển về kho tôi (/hang-chuyen-ve-kho-toi)

Kho khác lập phiếu điều chuyển là hàng đã vào kho của bạn trong sổ ngay lúc đó. Màn này để bạn khai số thật đếm được.

Các bước:
1. Mở Hàng chuyển về kho tôi. Chọn khoảng 7 ngày, 14 ngày hoặc 30 ngày.
2. Bấm vào một phiếu để xem danh sách hàng.
3. Bấm ✓ Xác nhận nhận hàng.
4. Máy điền sẵn số theo số kho giao. Đúng đủ thì giữ nguyên. Dòng nào lệch thì gõ số đếm thật, ghi chú nếu cần.
5. Bấm Xác nhận đã nhận, rồi Xác nhận.

Lưu ý:
- Màn này KHÔNG sửa tồn kho. Phần nhận thiếu treo thành việc cần làm cho thủ kho đối chiếu.
- Đã xác nhận rồi thì không xác nhận đè được. Khai sai thì báo thủ kho.
- Bếp xin hàng bằng phiếu yêu cầu điều chuyển thì mở phiếu đó trong Yêu cầu điều chuyển nội bộ và bấm 📦 Đã nhận hàng: bước này trừ kho xuất và nhập kho nhận thật. <!-- kiểm: địa chỉ màn Yêu cầu điều chuyển nội bộ chưa có trong bảng -->

Vì sao bị chặn:
- "Tài khoản của bạn chưa khai Kho phụ trách": báo anh Việt khai ở màn Người dùng.
- "Phiếu này chuyển về kho ..., không phải kho bạn phụ trách": chỉ người giữ kho nhận mới xác nhận được.

## Xuất điều chuyển hàng sang kho khác
Từ khoá: điều chuyển, chuyển kho, xuất chuyển, chuyển hàng sang bếp, chuyển bánh ra cửa hàng, chuyển nguyên liệu, material transfer, stock transfer, PDC, chuyển nội bộ
Ai dùng: Kho, Bếp, Cửa hàng
Màn hình: Xuất điều chuyển (/xuat-dieu-chuyen)

Các bước:
1. Mở Xuất điều chuyển, bấm nút +.
2. Nếu chuyển theo phiếu yêu cầu, chọn ở ô "Theo phiếu yêu cầu điều chuyển": máy tự điền kho và danh sách hàng.
3. Chọn Kho xuất và Kho nhận.
4. Bấm + Thêm hàng, gõ tên hoặc mã (chỉ hiện mã còn tồn ở kho xuất), chọn món. Sửa số lượng từng dòng, bấm × để bỏ dòng.
5. Ghi chú nếu cần, bấm Ghi sổ phiếu chuyển.

Lưu ý:
- Phiếu ghi sổ ngay, hàng nằm ở kho nhận luôn. Kho nhận vẫn phải đếm lại và xác nhận ở màn Hàng chuyển về kho tôi.
- Đổi kho xuất thì phải chọn lại hàng.
- Trên phiếu đã ghi sổ có nút 🛵 Lập vận đơn giao hàng này để phân công shipper.

Vì sao bị chặn:
- "Phải chọn cả kho xuất và kho nhận", "Kho xuất và kho nhận không được trùng nhau".
- "Số lượng xuất vượt quá tồn kho: ...": sửa số, hoặc kiểm tra tồn ở màn Tồn kho.

Hạch toán: hai kho cùng tài khoản thì không sinh bút toán; khác tài khoản (ví dụ kho nguyên liệu sang kho thành phẩm) thì Nợ tài khoản kho nhận / Có tài khoản kho xuất. <!-- kiểm: tài khoản gắn từng kho hiện hành -->

## Xuất huỷ hàng hỏng, hết hạn
Từ khoá: xuất huỷ, huỷ hàng, bỏ hàng, hàng hỏng, hàng hết hạn, hàng vỡ, bánh trưng bày hết ngày, thất thoát, write off, scrap, material issue, PXD
Ai dùng: Mọi bộ phận giữ kho lập; Quản lý kho ghi sổ
Màn hình: Xuất huỷ (/xuat-huy)

Các bước:
1. Mở Xuất huỷ, bấm nút +.
2. Chọn Kho xuất (bắt buộc).
3. Chọn Lý do huỷ (bắt buộc): Hỏng, vỡ trong quá trình làm; Hết hạn sử dụng; Không đạt chất lượng; Mẫu thử, nếm, chụp hình; Bánh trưng bày hết ngày; Thất thoát chưa rõ nguyên nhân; Khác.
4. Chụp Ảnh chứng minh (bắt buộc).
5. Bấm + Thêm hàng, chọn món và sửa số lượng.
6. Ghi chú, bấm "Lưu phiếu, chờ quản lý ghi sổ".

Lưu ý:
- Tồn kho chỉ trừ sau khi quản lý kho bấm Ghi sổ phiếu này. Phiếu nằm ở tab Chờ ghi sổ.
- Bánh chụp ảnh, mời khách, ăn ca thì dùng Xuất dùng nội bộ, không dùng Xuất huỷ.
- Phiếu điều chuyển đã ghi sổ có nút "🗑️ Xuất huỷ hàng này tại ..." để huỷ hàng nhận về không bán được.

Vì sao bị chặn: "Chưa chọn kho xuất", "Chưa chọn lý do huỷ", "Phiếu xuất huỷ bắt buộc có ảnh chứng minh", "Số lượng xuất vượt quá tồn kho", "Chỉ quản lý kho mới được ghi sổ phiếu xuất huỷ".

Hạch toán: Nợ 632 Giá vốn hàng bán / Có tài khoản kho (152 hoặc 1551). Hao hụt ngoài định mức kế toán chuyển tay sang 811.

## Xuất dùng nội bộ: chụp ảnh, mẫu thử, mời khách, ăn ca
Từ khoá: xuất dùng nội bộ, xuất dùng, xuất cho marketing, bánh chụp ảnh, mẫu thử, nếm thử, R&D, mời khách, tặng đối tác, nhân viên ăn ca, đào tạo, internal use, PXD
Ai dùng: Marketing, Bếp, Lab, Cửa hàng; Quản lý kho ghi sổ
Màn hình: Xuất dùng nội bộ (/xuat-dung-noi-bo)

Hàng ra khỏi kho mà tiệm vẫn dùng. Hàng hỏng thật thì dùng Xuất huỷ.

Các bước:
1. Mở Xuất dùng nội bộ, bấm nút +.
2. Chọn kho xuất.
3. Chọn Mục đích xuất dùng: Marketing chụp ảnh, quay phim; Mẫu thử, nghiên cứu công thức; Mời khách, tặng đối tác; Nhân viên ăn ca; Đào tạo, huấn luyện; Việc nội bộ khác.
4. Chọn Bộ phận chịu chi phí (máy gợi ý theo mục đích, đổi được).
5. Bấm + Thêm hàng, chọn món, gõ số lượng.
6. Ảnh không bắt buộc. Ghi chú, bấm "Lưu phiếu, chờ quản lý ghi sổ".

Lưu ý: tồn chỉ trừ khi quản lý kho bấm Ghi sổ phiếu này. Mục "Việc nội bộ khác" nhớ ghi rõ ở Ghi chú.

Vì sao bị chặn: "Chưa chọn mục đích xuất dùng", "Chưa chọn bộ phận chịu chi phí", "Có ... món vượt tồn", "Bộ phận ... chưa có trong hệ thống" (báo anh Việt), "Chỉ quản lý kho mới được ghi sổ phiếu xuất dùng nội bộ".

Hạch toán: Nợ tài khoản chi phí theo mục đích (Marketing 641x; mẫu thử, đào tạo 627x; mời khách, ăn ca, việc khác 642x) / Có tài khoản kho.

## Xuất kho phục vụ bán hàng: chốt bao bì, nguyên liệu tại điểm bán
Từ khoá: xuất kho phục vụ bán hàng, chốt kho điểm bán, chốt bao bì, xuất bao bì, túi hộp ly, nguyên liệu pha chế, đếm còn lại, xuất dùng cửa hàng, công cụ dụng cụ quầy, văn phòng phẩm, PXD
Ai dùng: Cửa hàng, Sales Online
Màn hình: Xuất kho phục vụ bán hàng (/xuat-kho-phuc-vu-ban-hang)

Màn này là bảng đếm: máy liệt kê mọi mã đang có tồn ở kho, bạn chỉ gõ số CÒN LẠI, máy tự tính số đã dùng.

Các bước:
1. Mở màn, bấm nút + (Chốt kho điểm bán).
2. Chọn kho và Bộ phận chịu chi phí.
3. Ở mục Đếm còn lại, gõ số còn lại cho từng mã đã đếm. Mã chưa đếm thì bỏ trống, máy không tính. Dùng ô tìm hoặc chip nhóm để lọc.
4. Ghi chú (ví dụ chốt tuần 38), bấm Ghi sổ phiếu xuất, rồi Ghi sổ.

Lưu ý:
- Bấm là tồn kho trừ ngay theo số đã dùng, không chờ kế toán (từ 20/09/2026).
- Bánh và đồ uống thành phẩm không có trong bảng vì đã trừ kho theo hoá đơn bán. Khai ở đây nữa là trừ hai lần.
- Dòng gõ sai (số còn lại lớn hơn tồn) bị tô đỏ, sửa trước khi lưu.

Hạch toán: bao bì, công cụ dụng cụ, văn phòng phẩm: Nợ 641x Chi phí bán hàng; nguyên liệu, bán thành phẩm: Nợ 632 Giá vốn / Có tài khoản kho.

## Xuất trả hàng cho nhà cung cấp
Từ khoá: trả hàng nhà cung cấp, trả NCC, hàng lỗi trả lại, trả hàng hư, giao sai hàng, purchase return, return to supplier, giảm công nợ, phiếu trả hàng
Ai dùng: Kho, Thu mua, Kế toán
Màn hình: Xuất trả nhà cung cấp (/xuat-tra-nha-cung-cap)

Các bước:
1. Mở màn, bấm nút +.
2. Chọn Nhà cung cấp (chỉ hiện nhà cung cấp có phiếu nhập trong 90 ngày).
3. Chọn Phiếu nhập gốc: máy hoàn đúng giá đã nhập của lô đó.
4. Chọn Lý do trả.
5. Gõ số lượng trả cho từng món (máy hiện số còn trả được).
6. Ảnh hàng lỗi và Ghi chú không bắt buộc. Bấm "Lưu và ghi sổ phiếu trả", rồi Ghi sổ.

Lưu ý: phiếu ghi sổ ngay, tồn giảm và công nợ phải trả nhà cung cấp giảm cùng lúc. Không dùng Xuất huỷ cho hàng trả nhà cung cấp.

Vì sao bị chặn:
- "Phiếu nhập ... chưa ghi sổ nên chưa trả hàng theo nó được".
- "Số trả vượt quá số còn trả được": mở lại phiếu để lấy số mới nhất.
- "Màn trả hàng nhà cung cấp chỉ mở cho kho, thu mua và kế toán".

Hạch toán: ngược phiếu nhập gốc, Nợ 3311 / Có tài khoản kho. <!-- kiểm: tài khoản khi phiếu gốc đã có hoá đơn mua -->

## Xuất bán sỉ, lập phiếu giao hàng cho khách doanh nghiệp
Từ khoá: xuất bán sỉ, bán sỉ, wholesale, giao hàng khách doanh nghiệp, phiếu giao hàng, delivery note, giao đơn sỉ, PGH, biên bản giao nhận
Ai dùng: Sales, Kho, Kế toán
Màn hình: Xuất bán sỉ (/xuat-ban-si)

Các bước:
1. Mở Xuất bán sỉ, bấm nút +.
2. Đọc khung cảnh báo vàng ở đầu màn.
3. Chọn Khách hàng và kho xuất.
4. Bấm + Thêm hàng, chọn món, gõ số lượng.
5. Ghi Người nhận hàng (tên người ký nhận bên khách) và Ghi chú.
6. Bấm "Lưu và ghi sổ phiếu giao", rồi Ghi sổ.

Lưu ý:
- Phiếu ghi sổ ngay, trừ kho thật và ghi giá vốn.
- Hoá đơn cho đơn này kế toán không bật thêm Cập nhật kho, không thì hàng bị trừ hai lần.
<!-- kiểm: từ 01/10/2026 hoá đơn bán tự trừ kho theo từng bill; cần xác nhận đơn sỉ đã lập phiếu giao có bị trừ lần hai qua hoá đơn không -->

Vì sao bị chặn: "Chưa chọn khách hàng", "Chưa chọn kho xuất", "Có ... món vượt tồn", "Màn xuất bán sỉ chỉ mở cho Sales, kho và kế toán".

Hạch toán: Nợ 632 Giá vốn hàng bán / Có tài khoản kho.

## Ghi sổ hoặc bỏ phiếu xuất đang chờ
Từ khoá: ghi sổ phiếu xuất, duyệt phiếu xuất huỷ, duyệt xuất dùng, phiếu chờ ghi sổ, bỏ phiếu, huỷ phiếu nháp, xoá phiếu xuất, lập nhầm phiếu
Ai dùng: Quản lý kho (ghi sổ); người lập phiếu (bỏ phiếu)
Màn hình: Xuất huỷ (/xuat-huy), Xuất dùng nội bộ (/xuat-dung-noi-bo)

Các bước ghi sổ:
1. Mở màn, chọn tab Chờ ghi sổ, bấm vào phiếu.
2. Xem kho, lý do hoặc mục đích, ảnh và danh sách hàng.
3. Bấm Ghi sổ phiếu này. Tồn kho trừ thật.

Các bước bỏ phiếu nháp sai:
1. Mở phiếu đang chờ, bấm 🚫 Bỏ phiếu này.
2. Ghi lý do (lập nhầm, sai kho, sai số lượng), xác nhận.

Lưu ý:
- Phiếu không bị xoá, chỉ đánh dấu đã bỏ và vẫn nằm trong danh sách để tra.
- Chỉ người tạo phiếu hoặc quản lý kho bỏ được phiếu.
- Ảnh chứng minh gỡ được (nút ✕ ở góc ảnh) khi phiếu chưa ghi sổ.
- Phiếu đã ghi sổ không bỏ được trên app. Cần huỷ thì liên hệ kế toán trưởng.

Vì sao bị chặn: "Phiếu này đã bỏ nên không ghi sổ được" (lập phiếu mới), "Phiếu này không còn ở trạng thái bản nháp", "Phiếu này không phải phiếu xuất dùng nội bộ. Phiếu xuất huỷ thì ghi sổ ở màn Xuất huỷ".

## Kiểm kê kho: tạo phiếu và đếm hàng
Từ khoá: kiểm kê, kiểm kho, đếm kho, đếm hàng tồn, phiếu kiểm kê, stock take, stocktake, inventory count, KK, kiểm tồn cuối tháng, đếm mù
Ai dùng: Kho, Bếp, Cửa hàng, Kiểm kê viên
Màn hình: Kiểm kê (/kiem-ke)

Mỗi phiếu kiểm kê là một kho, một nhóm hàng. Phiếu tự lưu nên đếm được nhiều buổi.

Các bước:
1. Mở Kiểm kê, bấm dấu +.
2. Chọn Ngày kiểm, Kho kiểm, Nhóm hàng kiểm (Nguyên vật liệu, Bán thành phẩm, Thành phẩm, Công cụ - Bao bì, Tất cả), và Vị trí kiểm nếu kho có chia tủ.
3. Bấm Bắt đầu kiểm.
4. Bấm 📷 Quét mã vạch liên tục, hoặc gõ tên món vào ô tìm rồi bấm + để thêm. Nhập số đếm được.
5. Bấm Lưu lại giữa chừng. Đếm xong bấm Chốt phiếu.

Lưu ý:
- Người đếm không thấy tồn trên máy (đếm mù), cứ ghi đúng số đếm.
- Món trong nhóm mà chưa đếm thì KHÔNG ghi vào sổ, tồn giữ nguyên.
- Kho đang có phiếu dở cùng nhóm hàng thì máy mời mở phiếu đó, tránh đếm trùng.
- Kho tổng 307 chỉ bộ phận Kho tổng 307 chốt số, người khác chỉ mở xem.
- Chốt rồi vẫn bấm Mở lại để sửa được. Bấm Huỷ phiếu kiểm kê này nếu lập nhầm.

Vì sao bị chặn: "Tài khoản của bạn chưa được cấp quyền kiểm kê".

## Ghi sổ phiếu kiểm kê và chọn lý do chênh lệch
Từ khoá: ghi sổ kiểm kê, chốt kiểm kê, điều chỉnh tồn, lý do chênh lệch, lệch tồn, hao hụt, stock reconciliation, PKK, giá vốn kiểm kê, tồn đầu kỳ
Ai dùng: Quản lý kho, Giám đốc
Màn hình: Kiểm kê (/kiem-ke)

Các bước:
1. Mở phiếu trạng thái Chờ duyệt hoặc Đã chốt, bấm Ghi sổ vào phần mềm.
2. Chọn Kiểu ghi sổ: Điều chỉnh tồn (kiểm kê định kỳ) hoặc Tồn đầu kỳ (lần đầu đưa số lên máy).
3. Kiểm tra Tài khoản đối ứng chênh lệch và Trung tâm chi phí.
4. Mục Cần điền giá vốn: điền giá mua 1 đơn vị (chưa VAT) cho món máy chưa biết giá.
5. Mục Lệch so với máy: chọn lý do cho từng món lệch (Hao hụt tự nhiên; Hư hỏng, hết hạn; Xuất dùng quên lập phiếu; Mất hàng; Nhập quên lập phiếu; Lệch đơn vị hoặc quy cách; Định lượng công thức sai).
6. Bấm Tạo phiếu điều chỉnh và nộp, rồi Ghi sổ ngay.

Lưu ý: ghi sổ xong tồn đổi theo số đếm và không sửa lại bằng app. Sai thì liên hệ kế toán trưởng.
<!-- kiểm: bản v547 cho máy tự lấy giá vốn khi trống; repo hiện hành vẫn bắt điền tay -->

Vì sao bị chặn:
- "Còn ... món lệch chưa chọn lý do": lý do là bắt buộc.
- "Lý do chọn ngược chiều với chênh lệch": thiếu hàng chọn lý do bên thiếu, thừa chọn bên thừa.
- "Còn ... món chưa có giá vốn".

Hạch toán: chênh lệch đối ứng vào tài khoản đã chọn (mặc định của công ty, màn ghi 811). Tồn đầu kỳ dùng Temporary Opening.

## Vì sao bị chặn "Đang có phiếu kiểm kê mở trên những mặt hàng này"
Từ khoá: phiếu kiểm kê đang mở, khoá kiểm kê, không ghi sổ được vì đang kiểm, bị khoá mã hàng, đang đếm kho
Ai dùng: Mọi bộ phận
Màn hình: Kiểm kê (/kiem-ke)

Khi một phiếu kiểm kê đang ở trạng thái Đang kiểm, Chờ duyệt hoặc Đã chốt, các mã hàng trong phiếu bị khoá ở đúng kho đó. Chứng từ kho khác chạm vào các mã này (nhập, xuất, điều chuyển) bị chặn với câu "Đang có phiếu kiểm kê mở trên những mặt hàng này nên chưa ghi sổ được", kèm tên món và kho.

Cách gỡ:
1. Mở màn Kiểm kê, tìm phiếu của kho đó ở mục Đang kiểm dở hoặc Đã chốt.
2. Đếm xong và nhờ quản lý ghi sổ phiếu kiểm, hoặc huỷ phiếu nếu lập nhầm.
3. Quay lại lưu chứng từ, lúc này lưu được ngay.

Lưu ý: khoá chỉ còn hiệu lực trong 2 ngày kể từ ngày kiểm. Lý do khoá: ghi sổ lúc đang đếm thì con số chênh lệch không còn đúng với thời điểm nào.

## Tra tồn kho
Từ khoá: tồn kho, xem tồn, tra tồn, còn bao nhiêu, kho còn hàng không, stock, stock balance, inventory, tồn âm, cận hạn, giá trị tồn
Ai dùng: Mọi bộ phận
Màn hình: Tồn kho (/ton-kho)

Các bước:
1. Mở Tra tồn kho, bấm ô Kho để chọn kho.
2. Gõ tên hoặc mã hàng vào ô tìm, hoặc quét mã vạch.
3. Lọc bằng chip nhóm hàng; chip ⏰ Cận hạn và ⚠ Tồn âm hiện khi có.
4. Đổi thứ tự sắp xếp bằng các nút cạnh dòng tóm tắt.
5. Bấm vào một món để xem Chi tiết tồn: tồn theo từng kho và các lô còn hàng.

Lưu ý:
- Dòng tóm tắt 📊 cho biết số mã và tổng của bộ lọc đang chọn.
- Giá trị tồn chỉ hiện với người được xem giá.
- Danh sách dài thì máy chỉ hiện một phần, gõ ô tìm để thu hẹp.
- Muốn biết hàng của bếp đang ở chặng nào thì dùng Tồn kho theo chặng.

## Tồn kho theo chặng và hàng nằm sai kho
Từ khoá: tồn theo chặng, chặng, nguyên liệu, bán thành phẩm, BTP sơ cấp, BTP sẵn sàng, thành phẩm, sai kho, chuyển về đúng kho, chưa phân chặng, tồn bếp
Ai dùng: Bếp, Kế toán giá thành, Kho
Màn hình: Tồn kho theo chặng (/ton-kho-theo-chang)

Màn này trả lời câu "hàng của bếp đang đứng ở chặng nào": Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm.

Các bước:
1. Mở Tồn kho theo chặng. Chọn bếp: Cả hai bếp, Pastry hoặc Baker.
2. Bấm chip chặng để lọc; chip ❓ Chưa phân chặng là món chưa gắn chặng.
3. Chip ⚠ Sai kho liệt kê món đang nằm ở kho không đúng chặng của nó.
4. Ở món sai kho, bấm 📦 Chuyển về ... rồi Lập phiếu nháp.

Lưu ý:
- Chuyển về đúng kho chỉ lập phiếu chuyển kho NHÁP, chuyển hết số đang nằm sai. Quản lý xem lại trên máy tính rồi mới ghi sổ.
- Máy chỉ nhắc, không chặn hàng nằm sai kho.

## Hoá đơn chưa trừ kho và trừ bù
Từ khoá: hoá đơn chưa trừ kho, chưa trừ kho, trừ bù, trừ kho bù, trừ kho sau, bán khi kho chưa có hàng, đã trừ một phần, phiếu bù, giá vốn hoá đơn bán
Ai dùng: Kế toán, Quản lý cửa hàng, Giám đốc (Sales chỉ xem)
Màn hình: Hoá đơn chưa trừ kho (/hoa-don-chua-tru-kho)

Hoá đơn bán lúc kho điểm bán chưa có hàng vẫn ghi sổ doanh thu. Máy trừ ngay món đang có; món còn thiếu tự trừ bù khi hàng nhập về kho điểm bán, và quét lại mỗi giờ.

Các bước trừ bù tay:
1. Mở Hoá đơn chưa trừ kho. Lọc theo điểm bán, khoảng ngày, chip trạng thái.
2. Chip "✅ Kho đủ để trừ bù" là hoá đơn bấm trừ được ngay.
3. Bấm 🔁 Trừ bù trên từng hoá đơn, hoặc 🔁 Trừ bù cả điểm này.

Lưu ý:
- Chip trạng thái: Chưa trừ kho, Đã trừ một phần, Đã trừ bù, Phiếu bù bị gỡ tay. Chip tồn hiện tại: Kho đủ để trừ bù, Kho đủ một phần, Kho chưa có hàng.
- Mỗi lần trừ bù máy lập một phiếu xuất dùng (mã PXD) gắn với hoá đơn.
- Website đặt bánh không bị ảnh hưởng, số trên web đã trừ ngay lúc lưu hoá đơn.

Vì sao bị chặn: "Chỉ kế toán, quản lý cửa hàng hoặc giám đốc được bấm trừ bù"; "Điểm bán ... chưa khai kho xuất".

Hạch toán: Nợ 632 Giá vốn hàng bán / Có tài khoản kho điểm bán.

## Lô hàng và hạn sử dụng khi nhập, xuất kho
Từ khoá: lô, lô hàng, batch, mẻ, quản lý theo mẻ, hạn sử dụng, HSD, hết hạn, cận hạn, FEFO, gói số seri và lô, lô quá hạn
Ai dùng: Kho, Bếp, Kế toán
Màn hình: Nhập kho (/nhap-kho), Tồn kho (/ton-kho)

Từ 30/09/2026 tiệm đã tắt quản lý theo lô cho toàn bộ mã hàng (bánh, bán thành phẩm, nhân, nguyên liệu thô). Từ nay nhập, xuất, sản xuất, kiểm kê không cần chọn lô.

Lưu ý:
- Màn Nhập kho chỉ hiện ô Hạn sử dụng cho món còn quản lý theo lô. Món đã tắt lô thì không có ô này.
- Tồn cũ nằm ở các lô cũ được coi là tồn chung của mã.
- Chứng từ cũ có lô giữ nguyên. Huỷ một chứng từ cũ có lô có thể bị báo lỗi, liên hệ kế toán trưởng.
- Còn gặp câu "Vui lòng thêm Gói Số seri và Lô" thì mã đó vẫn đang bật lô: báo anh Việt hoặc kế toán kiểm tra mã hàng, không tự sửa.
- Lô quá hạn trên chứng từ cũ chỉ bị cảnh báo, không chặn.

Việc bật lại lô cho mã nào do anh Việt quyết.

## Cây kho: kho nào dùng cho việc gì
Từ khoá: cây kho, danh sách kho, kho nào, kho tổng 307, kho D1, kho NVHTN, kho Sales Online, kho bếp, kho nguyên liệu bếp, kho thành phẩm, kho Lab, warehouse
Ai dùng: Mọi bộ phận
Màn hình: Tồn kho (/ton-kho)

- Kho tổng 307 (307/1 Nguyễn Văn Trỗi): nguyên liệu mua về nhập vào đây, bộ phận kho giữ.
- Bếp Pastry và Bếp Baker, mỗi bếp có kho Nguyên liệu và kho Thành phẩm. Nguyên liệu chuyển từ Kho tổng 307 sang kho Nguyên liệu của bếp; lệnh sản xuất rút nguyên liệu từ đó, thành phẩm nhập kho Thành phẩm.
- Hai kho BTP sơ cấp và BTP sẵn sàng đã tắt từ 28/08/2026, không dùng nữa.
- Kho Lab: bếp nghiên cứu Sonneto Lab.
- Kho D1 (9 Trần Cao Vân), Kho NVHTN (21 Phạm Ngọc Thạch), Kho Sales Online: kho điểm bán. Bánh từ kho Thành phẩm bếp chuyển ra đây để bán.

Lưu ý:
- Mỗi tài khoản có ô Kho phụ trách; màn xuất kho chỉ cho chọn kho mình phụ trách. Cần thêm kho thì báo anh Việt khai ở màn Người dùng.
- Máy không chặn chuyển hàng giữa các kho, chỉ nhắc khi hàng nằm sai chặng.
<!-- kiểm: danh sách kho hiện hành và địa chỉ lấy từ ghi chép 07-08/2026; cần đối chiếu cây kho trên site -->

## Mã chứng từ kho: PNK, PDC, PXD, PKK là gì
Từ khoá: mã phiếu, mã chứng từ, số phiếu, PNK, PDC, PXD, PKK, PSX, KK, YCDC, DMH, HDM, PGH, tiền tố phiếu, naming series
Ai dùng: Mọi bộ phận
Màn hình: Desk: các chứng từ kho

Mã có dạng MÃ-NĂM-SỐ, ví dụ PNK-2026-00054.
- DMH: đơn mua hàng.
- PNK: phiếu nhập kho mua hàng.
- HDM: hoá đơn mua.
- YCDC: yêu cầu điều chuyển; YCXD: yêu cầu xuất dùng.
- PDC: phiếu điều chuyển kho.
- PXD: phiếu xuất dùng (xuất huỷ, xuất dùng nội bộ, xuất phục vụ bán hàng, phiếu trừ kho bù).
- PSX: phiếu sản xuất.
- KK: phiếu kiểm kê trên app (phiếu đếm).
- PKK: phiếu điều chỉnh tồn sinh ra khi ghi sổ kiểm kê.
- PGH: phiếu giao hàng (xuất bán sỉ).
- HDB: hoá đơn bán.

Lưu ý: phiếu tạo trước 03/08/2026 còn mang mã cũ của ERPNext (MAT-STE, MAT-PRE...), vẫn dùng bình thường.
<!-- kiểm: mã xuất huỷ có thật là PXD không, mã phiếu trả nhà cung cấp, mã phiếu giao hàng PGH, và mã KK đầy đủ của phiếu kiểm kê app -->

## Các câu chặn hay gặp khi ghi sổ phiếu kho
Từ khoá: lỗi ghi sổ phiếu kho, thiếu hàng, không đủ hàng, tồn âm, vượt tồn, thiếu lô, tài khoản chi phí, tài khoản chênh lệch, không có quyền xuất kho, lỗi phiếu xuất
Ai dùng: Mọi bộ phận
Màn hình: các màn Xuất kho, Nhập kho, Kiểm kê

Vì sao bị chặn:
- "Số lượng xuất vượt quá tồn kho: mã (tồn ..., xuất ...)": tiệm không cho tồn âm. Sửa số, hoặc chuyển hàng về kho này trước, hoặc kiểm kê lại.
- "Kho ... không đủ ... để trừ: còn thiếu ..." (tiêu đề Thiếu hàng trong kho): câu này nói luôn kho nào còn mã đó. Chuyển kho phần thiếu rồi bấm lại.
- "Đang có phiếu kiểm kê mở trên những mặt hàng này": xem mục Vì sao bị chặn "Đang có phiếu kiểm kê mở".
- "Vui lòng thêm Gói Số seri và Lô": mã vẫn bật lô dù tiệm đã tắt lô; báo anh Việt hoặc kế toán.
- "Chưa có tài khoản chi phí nào để ghi giá trị hàng huỷ, nhờ kế toán khai thêm": báo kế toán.
- "Tài khoản của bạn chưa được cấp quyền xuất kho": báo quản lý cấp quyền.
- "Kho này không nằm trong các kho bạn phụ trách": báo anh Việt khai thêm Kho phụ trách.
- "Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính": liên hệ kế toán trưởng.
- "Phiếu chưa có dòng hàng nào có số lượng lớn hơn 0": gõ số lượng cho ít nhất một dòng.
