# Sản xuất và công thức

## Lập kế hoạch sản xuất cho một ngày
Từ khoá: kế hoạch sản xuất, KHSX, production plan, lên kế hoạch, tính nguyên liệu trong ngày, nổ BOM, bao nhiêu bánh phải làm, phiếu kế hoạch, huỷ kế hoạch, lập lại kế hoạch

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, bếp trưởng; bếp phó chỉ xem | Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat) | [[Lập kế hoạch cho ngày này]] |

Máy gom mọi phiếu yêu cầu sản xuất hẹn cho một ngày (kể cả phiếu quá hạn) rồi tính ra thành phẩm, bán thành phẩm, nguyên liệu. Nửa đêm máy tự lập phiếu cho ngày mới.

**Các bước**
1. Bấm [[◀ Hôm trước]] hoặc [[Hôm sau ▶]] để chọn ngày bếp làm.
2. Ngày chưa có phiếu: bấm [[Lập kế hoạch cho ngày này]], rồi [[Lập kế hoạch]].
3. Đọc ba thẻ Thành phẩm, Bán thành phẩm, Nguyên liệu: mỗi món có Cần, Tồn đầu, Tồn giờ, Phải làm.
4. Lọc bếp: [[Cả hai bếp]], [[Pastry]], [[Baker]].
5. Lọc tình trạng: [[Phải làm]], [[Thiếu một phần]], [[Đã có lệnh]], [[Đủ tồn]].
6. Bấm vào thẻ một món để xem nguyên liệu của món đó.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Ngày ... đã có phiếu kế hoạch ... rồi, không lập thêm | Mỗi ngày một phiếu, mở phiếu đó ra dùng |
| Không có phiếu yêu cầu sản xuất nào hẹn ngày ... | Chưa điểm bán nào gửi yêu cầu cho ngày đó |

**Lưu ý**
- Huỷ phiếu: bấm [[Các phiếu kế hoạch]], chọn phiếu, bấm [[Huỷ phiếu]]. Phiếu đã có lệnh sản xuất thì phải huỷ các lệnh đó trước.
- Chỉ quản lý sản xuất và giám đốc lập, huỷ phiếu.

## Ra lệnh sản xuất từ kế hoạch
Từ khoá: tạo lệnh từ kế hoạch, ra lệnh, work order, LSX, lệnh sản xuất hàng loạt, tick chọn món, đổi kho nhập, sửa số cần, đặt lại tồn, tồn giờ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, bếp trưởng | Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat) | [[Hoàn thành, tạo lệnh sản xuất]] |

Từ phiếu kế hoạch, bếp ra lệnh cho từng món hoặc nhiều món một lượt.

**Các bước**
1. Một món: bấm vào thẻ món, xem dòng Nhập vào, bấm [[đổi kho]] nếu cần.
2. Muốn làm khác số máy tính: gõ vào ô Cần trên thẻ.
3. Bấm [[Hoàn thành, tạo lệnh sản xuất]].
4. Nhiều món: tick ô vuông đầu các thẻ, bấm [[Tạo lệnh cho N món đã chọn]], rồi [[Tạo N lệnh]].
5. Bấm [[Xem lệnh đã tạo]] để sang màn Sản xuất.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Món ... đã ra lệnh đủ số rồi | Không cần ra thêm |
| Chọn kho nhập trước đã | Bấm [[chọn kho]] trên thẻ |
| Kho ... không phải kho bếp | Bánh nhập kho bếp trước, chuyển sang điểm bán bằng phiếu điều chuyển riêng |
| Món ... không quản tồn kho, nó tự nổ trong lệnh của món cha | Đây là mặt hàng ảo, không cần lệnh riêng |

**Lưu ý**
- Ô Tồn giờ gõ được: gõ số mới rồi rời ô, máy hỏi Đặt tồn, bấm [[Ghi phiếu kiểm kê]] là máy ghi một phiếu kiểm kê THẬT ngay lúc đó. Ô Tồn đầu không sửa được.

## Xin chuyển nguyên liệu từ kho tổng về bếp
Từ khoá: chuyển nguyên liệu, xin nguyên liệu, chuyển kho nguyên liệu cho sản xuất, material transfer, kho tổng 307, lấy hàng về bếp, thiếu nguyên liệu ở bếp

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, bếp trưởng; kho tổng ghi sổ | Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat) | [[Xin chuyển nguyên liệu]] |

Lệnh sản xuất trừ nguyên liệu thẳng ở kho Nguyên liệu của bếp lúc bấm Hoàn tất, không có bước chuyển riêng. Hàng phải nằm sẵn ở kho Nguyên liệu của bếp trước khi làm.

**Các bước**
1. Mở phiếu kế hoạch của ngày. Chỉ xin cho một bếp thì chọn [[Pastry]] hoặc [[Baker]].
2. Bấm [[Xin chuyển nguyên liệu]], rồi [[Tạo phiếu xin]].
3. Máy tạo phiếu chuyển kho NHÁP từ Kho tổng 307 sang kho Nguyên liệu của bếp theo phần còn thiếu, và báo số phiếu.
4. Kho tổng soát hàng rồi ghi sổ phiếu.
5. Bếp xem hàng về ở màn Hàng chuyển về kho tôi (/hang-chuyen-ve-kho-toi).

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phiếu này không có dòng nguyên liệu nào thiếu | Bếp đã đủ hàng |
| Không có gì để xin thêm | Các mã đã xin ở phiếu trước |

**Lưu ý**
- Bếp này thiếu mà bếp kia còn: xem mục "Chuyển nguyên liệu giữa hai bếp".

## Chuyển nguyên liệu giữa hai bếp
Từ khoá: chuyển kho giữa hai bếp, mượn nguyên liệu bếp kia, Baker sang Pastry, Pastry sang Baker, điều chuyển nội bộ, stock transfer, thiếu hàng bếp này còn bếp kia

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp trưởng, quản lý sản xuất, kho | Xuất điều chuyển (/xuat-dieu-chuyen) | [[Ghi sổ phiếu chuyển]] |

Khi bấm Hoàn tất bị báo thiếu kèm câu "Mã này đang còn ở ... tại kho ...", chuyển phần thiếu từ kho đang còn sang kho Nguyên liệu của bếp làm lệnh.

**Các bước**
1. Mở màn Xuất điều chuyển, bấm nút tròn dấu cộng.
2. Chọn Kho xuất là kho đang còn hàng, Kho nhận là kho Nguyên liệu của bếp đang làm.
3. Bấm [[+ Thêm hàng]], chọn mã, gõ số lượng.
4. Bấm [[Ghi sổ phiếu chuyển]].
5. Quay lại lệnh sản xuất, bấm Hoàn tất lại.

**Lưu ý**
- Ghi sổ xong hàng đã nằm ở kho nhận; bên nhận vẫn đếm lại khi nhận.
- Kho không hiện trong ô chọn là do tài khoản chưa được cấp kho đó, nhờ quản lý mở quyền.

## Xem bảng bếp hôm nay
Từ khoá: bảng bếp, việc bếp hôm nay, danh sách bánh cần làm, phiếu yêu cầu sản xuất, YCSX, đánh dấu đã làm, xác nhận đã giao, kitchen board

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, bếp phó | Bảng bếp hôm nay (/bang-bep-hom-nay) | [[Xác nhận đã giao N phiếu]] |

Gộp mọi phiếu yêu cầu sản xuất của một ngày theo món, để bếp biết tổng số bánh cần làm và giờ cần lấy.

**Các bước**
1. Chọn ngày: [[Hôm qua]], [[Hôm nay]], [[Ngày mai]] hoặc chip lịch (gõ nn/tt/nnnn).
2. Mặc định chỉ thấy phiếu gửi cho bếp mình; bấm [[Tất cả bếp]] để xem hết.
3. Ở phần Cần làm - gộp theo món, bấm một món để đánh dấu đã làm (bấm lại để bỏ).
4. Mọi món của phiếu đã đánh dấu thì phiếu hiện Sẵn sàng giao.
5. Bấm [[Xác nhận đã giao N phiếu]], rồi [[Xác nhận]]. Phiếu sang Đã giao.

**Lưu ý**
- Dòng "Còn N phiếu của những ngày trước chưa xác nhận xong": bấm [[Hôm qua]] để xem phiếu cũ.
- Đánh dấu đã làm ở đây KHÔNG trừ kho. Trừ nguyên liệu và nhập thành phẩm là lúc bấm Hoàn tất lệnh sản xuất.

## Tạo lệnh sản xuất
Từ khoá: tạo lệnh sản xuất, lệnh sản xuất mới, work order, LSX, ra lệnh, sản xuất bánh, làm bánh, chọn món cần làm, quét mã món

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, bếp phó, quản lý sản xuất | Sản xuất (/san-xuat) | [[Tạo N lệnh sản xuất]] |

**Các bước**
1. Bấm nút tròn dấu cộng góc dưới để vào Tạo lệnh sản xuất.
2. Kiểm Lấy nguyên liệu từ kho và Nhập thành phẩm vào kho (máy tự chọn theo chặng của món).
3. Chọn khoảng nhu cầu: [[Đến hôm nay]], [[Đến ngày mai]], [[Đến hết tuần]].
4. Gõ tên, mã vào ô Tìm tên hoặc mã món, hoặc bấm nút máy ảnh để quét mã vạch.
5. Bấm dấu cộng trên thẻ món. Lấy hết thì bấm [[✓ Chọn tất cả N món đang cần]].
6. Món ngoài phiếu yêu cầu: bấm [[+ Thêm món ngoài phiếu yêu cầu]].
7. Chỉnh Số lượng sẽ làm trên từng thẻ, bấm [[Tạo N lệnh sản xuất]].
8. Máy chuyển sang màn Bán thành phẩm cần làm (xem mục riêng).

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa chọn món nào | Bấm dấu cộng trên ít nhất một thẻ |
| Chưa chọn kho nguyên liệu hoặc kho thành phẩm | Chọn hai ô kho ở đầu màn |
| Thẻ ghi Chưa có công thức | Bấm [[Khai nguyên liệu đã dùng]] |

**Lưu ý**
- Mỗi thẻ hiện Phòng ban cần, Đã có lệnh, Tồn thành phẩm để tránh làm trùng. Máy không tự tick sẵn món nào.

## Bán thành phẩm cần làm sau khi tạo lệnh
Từ khoá: bán thành phẩm, BTP, ruột bánh, bánh khuôn, C1, C2, lệnh bán thành phẩm, lệnh con, sub assembly, nhiều cấp, làm tươi, BTP còn thiếu

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, quản lý sản xuất | Sản xuất (/san-xuat), màn Bán thành phẩm cần làm | [[Duyệt và tạo N lệnh]] |

Ngay sau khi tạo lệnh, máy tính bán thành phẩm có giữ tồn (ruột bánh, bánh khuôn) còn thiếu: Công thức cần, Tồn kho NVL, Còn thiếu.

**Các bước**
1. Bấm dấu ✓ trên từng thẻ để chọn hoặc bỏ, chỉnh Số lượng sẽ làm.
2. Bấm [[Duyệt và tạo N lệnh]]. Máy có thể hỏi tiếp cấp dưới, tối đa bốn cấp.
3. Không cần làm thì bấm [[Bỏ qua bước này]].

**Lưu ý**
- Bán thành phẩm nhập về kho Nguyên liệu của bếp, không vào kho Thành phẩm.
- Mặt hàng ảo và loại làm tươi KHÔNG hiện ở đây: máy tự trừ hoặc tự làm khi bấm Hoàn tất lệnh món cha.
- Hiện "Không cần làm thêm bán thành phẩm nào" là tồn đã đủ.

## Hoàn tất lệnh sản xuất
Từ khoá: hoàn tất lệnh, hoàn thành lệnh sản xuất, xong lệnh, nhập kho thành phẩm, trừ nguyên liệu, báo sản lượng, cân thực tế, hao hụt, manufacture, finish work order, ghi sổ nhiều lệnh

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, bếp phó, quản lý sản xuất | Sản xuất (/san-xuat) | [[Hoàn tất]] |

Bấm Hoàn tất là lúc máy trừ nguyên liệu và nhập thành phẩm vào kho. Bút toán kho ghi xong không sửa lại được.

**Các bước**
1. Bấm dấu ✓ cuối dòng lệnh, hoặc mở lệnh rồi bấm [[Hoàn tất]].
2. Hộp Hoàn thành phiếu: gõ Số lượng làm theo lệnh (để trừ nguyên liệu).
3. Gõ Thực tế cân được (để nhập kho). Đổi đơn vị ở ô cạnh số nếu cân theo kg hay gram.
4. Chip Lần trước gợi ý số hay gõ, bấm vào là điền.
5. Bấm [[Hoàn thành]].
6. Có bán thành phẩm làm tươi: hộp Máy làm luôn giúp bếp hiện danh sách, bấm [[Xác nhận tạo lệnh]].
7. Nhiều lệnh cùng món: bấm ✓ trên thẻ gộp, gõ tổng số, bấm [[Ghi sổ N lệnh]].

**Hạch toán** (từ 01/10/2026, mang trung tâm chi phí của bếp)
| Nợ | Có | Khi nào |
|---|---|---|
| 621 | 152 | Dòng nguyên liệu bị trừ |
| 1551 | 154 | Thành phẩm nhập kho Thành phẩm |
| 152 | 154 | Bán thành phẩm nhập kho Nguyên liệu của bếp |

**Lưu ý**
- Cân ít hơn số làm thì phần chênh ghi là hao hụt và lệnh vẫn đóng.
- Câu chặn hay gặp: xem mục "Vì sao không hoàn tất được lệnh sản xuất".

## Vì sao không hoàn tất được lệnh sản xuất
Từ khoá: không hoàn tất được, lỗi hoàn tất, bị chặn, thiếu hàng, thiếu nguyên liệu, không đủ tồn, kho không đủ, thiếu lô, batch mandatory, lệnh treo, lỗi sản xuất

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, quản lý sản xuất | Sản xuất (/san-xuat) | [[Hoàn tất]] |

Máy không ghi âm kho: thiếu là dừng, không để lại phiếu nháp. Xem chip "Thiếu N nguyên liệu" trên dòng lệnh hoặc chữ đỏ ở Nguyên liệu sẽ trừ trước khi bấm.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Kho ... không đủ ... để trừ: còn thiếu ... Mã này đang còn ở ... | Chuyển phần thiếu về kho Nguyên liệu của bếp rồi bấm lại |
| ... Chưa tìm thấy tồn mã này ở kho khác | Kiểm tồn, nhập hàng hoặc kiểm kê lại |
| ... Mã thay thế đã khai đang còn ... | Mã thay nằm ở kho khác, chuyển về đúng kho rồi bấm lại |
| Số làm theo lệnh không được quá số còn lại là ... | Phần dư ghi vào ô Thực tế cân được |
| Lệnh này đã làm đủ số rồi | Không cần hoàn tất nữa |
| Lệnh Đã dừng / Đã đóng nên không hoàn tất được | Ra lệnh mới |
| Chỉ bếp, quản lý sản xuất hoặc giám đốc mới hoàn tất lệnh được | Nhờ quản lý mở quyền |
| Không xác định được kho đích theo chặng ... | Báo quản lý sản xuất |

**Lưu ý**
- Lỗi máy báo thiếu số lô gần như không còn: từ 30/09/2026 mọi mã đã tắt quản lý theo lô. Còn gặp thì báo kỹ thuật.

## Nguyên liệu hết hàng thì máy có tự dùng mã thay thế không
Từ khoá: mã thay thế, nguyên liệu thay thế, hàng thay thế, item alternative, alternative item, hết whipping, hết bơ, dùng mã khác, thay nguyên liệu, mã gốc hết hàng

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, quản lý sản xuất, kế toán giá thành | Sản xuất (/san-xuat) | [[Hoàn tất]] |

Có, từ 02/10/2026. Bấm Hoàn tất mà mã gốc thiếu ở kho nguyên liệu, máy tự lấy mã thay thế đã khai cho phần còn thiếu, cùng kho.

**Điều kiện để máy tự thay**
| Điều kiện | Kiểm ở đâu |
|---|---|
| Cặp thay thế đã khai | Desk: Mặt hàng thay thế |
| Mã gốc bật ô Cho phép mặt hàng thay thế | Desk: hồ sơ Món |
| Hai mã cùng đơn vị tính kho | Ví dụ ml thay ml |
| Mã thay còn tồn ở CÙNG kho nguyên liệu của lệnh | Màn Tồn kho |

Máy dùng hết mã gốc trước, thiếu bao nhiêu lấy mã thay bấy nhiêu. Dòng thay ghi "Dùng thay ... đang thiếu tại kho (mã thay thế đã khai)".

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Thiếu, kèm "Mã thay thế đã khai đang còn ..." | Gốc cộng thay vẫn không đủ ở kho này; chuyển hàng về rồi bấm lại |

**Lưu ý**
- Chỉ áp cho sản xuất. Nhận hàng điều chuyển không bao giờ tự đổi mã.
- Giá vốn thành phẩm đổi theo giá mã thay. Cặp nào được thay cho nhau do bếp trưởng và kế toán giá thành quyết.

## Khai mã thay thế cho nguyên liệu
Từ khoá: khai mã thay thế, khai nguyên liệu thay thế, mặt hàng thay thế, item alternative, cặp thay thế, hai chiều, two way, cho phép mặt hàng thay thế, allow alternative item

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán giá thành, quản lý sản xuất, quản lý danh mục | Desk: Mặt hàng thay thế | [[desk:Thêm Mặt hàng thay thế]] |

**Các bước**
1. Trên Desk mở hồ sơ Món của mã GỐC, tick ô Cho phép mặt hàng thay thế, bấm [[desk:Lưu]].
2. Mở danh sách Mặt hàng thay thế, bấm [[desk:Thêm Mặt hàng thay thế]].
3. Ô Mã món chọn mã gốc, ô Mã MH thay thế chọn mã thay.
4. Tick Hai chiều nếu hai mã thay được cho nhau.
5. Bấm [[desk:Lưu]].

**Cột cảnh báo trên danh sách**
| Máy ghi | Nghĩa |
|---|---|
| Không thay được | Khác đơn vị tính, mã thay đã ngừng, hoặc mã gốc chưa bật cho phép. Máy KHÔNG dùng cặp này |
| Cần xem | Mã thay hết ở mọi kho, chưa có giá vốn, giá vốn chênh trên 10 phần trăm, hoặc mã gốc chưa nằm trong công thức nào |
| Dùng được | Ổn |

**Lưu ý**
- Cảnh báo tính lại lúc lưu cặp và mỗi đêm.
- Thay bằng một mã chưa có giá vốn sẽ kéo giá vốn thành phẩm xuống mà không ai thấy.

## Sửa số lượng hoặc huỷ lệnh sản xuất
Từ khoá: sửa lệnh, sửa số lượng lệnh, huỷ lệnh sản xuất, xoá lệnh, tạo nhầm lệnh, lệnh trùng, đóng lệnh, dừng lệnh

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, giám đốc | Sản xuất (/san-xuat), chi tiết lệnh | [[Huỷ lệnh này]] |

**Các bước**
1. Mở lệnh trên danh sách.
2. Lệnh còn nháp: bấm [[Sửa số lượng]], gõ số mới.
3. Bỏ lệnh: bấm [[Huỷ lệnh này]], rồi [[Huỷ lệnh]]. Số của món trả lại cho kế hoạch, ra lệnh mới được ngay.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Lệnh ... đã ghi sổ nên không sửa số được | Huỷ lệnh rồi ra lệnh mới với số đúng |
| Lệnh ... đã làm ra ... rồi nên không huỷ được | Báo quản lý sản xuất để dừng lệnh |
| Lệnh ... đã chuyển nguyên liệu vào sản xuất nên không huỷ được | Trả nguyên liệu về kho trước |
| Số lượng phải lớn hơn 0 | Gõ lại số |

**Lưu ý**
- Phần đã hoàn tất là bút toán đã ghi sổ, không sửa trên app; cần xử lý thì liên hệ kế toán trưởng.

## Làm món chưa có công thức
Từ khoá: món chưa có công thức, chưa có BOM, khai nguyên liệu đã dùng, sản xuất không định mức, làm thử, ghi nhận nguyên liệu, lưu thành công thức

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, bếp phó | Sản xuất (/san-xuat) | [[Món chưa có công thức]] |

Món chưa có công thức thì không tạo lệnh được. Bếp khai đã dùng những gì và làm được bao nhiêu.

**Các bước**
1. Bấm [[Món chưa có công thức]], chọn món (hoặc [[Khai nguyên liệu đã dùng]] trên thẻ ở màn Tạo lệnh).
2. Kiểm ô Lấy nguyên liệu từ kho.
3. Gõ Số lượng làm được.
4. Bấm [[+ Thêm nguyên liệu]], chọn nguyên liệu, gõ Số lượng đã dùng, chọn đơn vị.
5. Giữ dấu ✓ ở Lần sau khỏi khai lại nếu muốn lưu thành công thức.
6. Bấm [[Xong - trừ kho nguyên liệu]], rồi [[Xác nhận trừ kho]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa nhập số lượng làm được | Gõ số |
| Chưa khai nguyên liệu nào / Có nguyên liệu chưa nhập số lượng | Thêm hoặc điền số |
| Không thể dùng chính món đang làm làm nguyên liệu | Bỏ dòng đó |

**Lưu ý**
- Công thức lưu từ đây là bản NHÁP; bếp trưởng rà lại ở màn Công thức rồi bấm Ghi sổ thì lần sau mới tạo lệnh theo nó được.

## In tem cho mẻ bánh
Từ khoá: in tem, tem HACCP, tem nhãn, nhãn bánh, NSX, HSD, hạn dùng, mẻ, batch, in lại tem, máy in tem, QZ Tray, Brother, chưa bật theo dõi lô

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp | Sản xuất (/san-xuat), chi tiết lệnh | [[In tem]] |

Tem ghi tên món, khối lượng tịnh, điều kiện bảo quản, chất gây dị ứng, NSX, HSD, mã vạch món. Từ 03/10/2026 tem không cần lô: dòng lô cũ đổi thành "Ngày: ......" để bếp điền tay.

**Các bước**
1. Mở lệnh, bấm [[In tem]] hoặc [[In lại tem]]. Bấm [[Hoàn thành]] xong máy cũng tự mở màn In tem HACCP.
2. Chỉnh Số tem cần in.
3. Bấm [[In thử 1 tem]] hoặc [[In N tem]].
4. Dán tem, điền tay ngày vào dòng Ngày.

**In cả nhóm**: trên thẻ gộp bấm [[In tem cả N lệnh]], mỗi lệnh một xấp tem theo số đã làm.

**Lưu ý**
- NSX là giờ bấm in, HSD tính từ NSX. In trước để dán sau thì sửa tay cho đúng.
- Đừng tự bật lại Có quản lý lô trên Desk: tắt lô là quyết định của anh Việt 30/09/2026.
- Hạn dùng trên tem lấy từ số giờ hạn dùng hoặc Thời gian Sử dụng theo Ngày trên hồ sơ món.
- In cả nhóm cần máy in tem đã nối QZ Tray; chưa nối thì máy báo "chỉ in được từng lệnh một".

## Xem và tìm công thức
Từ khoá: công thức, BOM, định mức, định lượng, recipe, danh mục công thức, tra công thức, xem nguyên liệu của bánh, phiên bản công thức, bản cũ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, bếp phó, quầy bar, quản lý sản xuất, kế toán giá thành | Công thức (/cong-thuc) | [[Pastry]] |

**Các bước**
1. Mở màn Công thức (tiêu đề Danh mục công thức).
2. Chọn khu: [[Pastry]], [[Baker]], [[Quầy Bar]], [[Chưa phân]].
3. Gõ ô Tìm theo tên hoặc mã món. Khi tìm, máy bỏ lọc khu và tìm cả tiệm.
4. Lọc thêm theo trạng thái (Đang dùng, Nháp, Bản cũ, Đã huỷ), tình trạng hướng dẫn, chặng.
5. Bấm vào công thức để xem mẻ ra bao nhiêu, nguyên liệu và số lượng cho một mẻ.
6. Phần Chuỗi phiên bản cho bấm sang bản trước hoặc bản sau.

**Lưu ý**
- Đang dùng là bản lệnh sản xuất nổ theo. Bản cũ vẫn tra được nhưng không dùng nữa.
- Nút hình quyển sách trên thẻ: cam là chưa soạn hướng dẫn, đỏ [[Soát lại HD]] là công thức đã đổi sau khi soạn.

## Tạo công thức mới
Từ khoá: tạo công thức, lập công thức, thêm BOM, định mức mới, recipe mới, công thức cho món mới, lưu nháp công thức, ghi sổ công thức

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp phó, quầy bar soạn; bếp trưởng, giám đốc ghi sổ | Công thức (/cong-thuc) | [[Lưu và ghi sổ]] |

**Các bước**
1. Bấm nút tròn dấu cộng, chọn món cần lập công thức.
2. Gõ Một mẻ ra được.
3. Bấm [[+ Thêm nguyên liệu]], chọn từng nguyên liệu, gõ Số lượng cho một mẻ.
4. Bấm [[Lưu nháp]], hoặc [[Lưu và ghi sổ]] nếu có quyền.
5. Không ghi sổ được: lưu nháp rồi nhờ bếp trưởng mở bản nháp, bấm [[Ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Công thức phải có ít nhất một dòng nguyên liệu | Thêm nguyên liệu |
| Có nguyên liệu chưa nhập số lượng / Chưa nhập mẻ ra được bao nhiêu | Điền số |
| Nguyên liệu này đã có trong công thức | Sửa số ở dòng cũ |
| Món này đang có bản nháp ... chờ duyệt, sửa tiếp bản đó | Mở bản nháp đó |
| Màn này chỉ bếp và quầy bar soạn công thức được | Nhờ người có quyền |
| Chỉ bếp trưởng (Manufacturing Manager) hoặc giám đốc mới ghi sổ công thức | Lưu nháp, nhờ bếp trưởng |

**Lưu ý**
- Ghi sổ xong, lệnh sản xuất và giá vốn tính theo bản này.

## Điều chỉnh công thức đang dùng
Từ khoá: sửa công thức, điều chỉnh công thức, đổi định mức, đổi định lượng, phiên bản mới, cập nhật BOM, sửa BOM, bỏ bản nháp

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp phó, quầy bar soạn; bếp trưởng, giám đốc ghi sổ | Công thức (/cong-thuc) | [[Điều chỉnh (ra phiên bản mới)]] |

Công thức đã ghi sổ không sửa thẳng được. Ghi sổ bản mới xong, bản cũ tự thành Bản cũ, vẫn tra được.

**Các bước**
1. Mở công thức đang dùng, bấm [[Điều chỉnh (ra phiên bản mới)]].
2. Máy chép ra bản nháp và mở màn sửa.
3. Sửa số lượng, bấm dấu × để bỏ dòng, [[+ Thêm nguyên liệu]] để thêm.
4. Bấm [[Lưu nháp]] hoặc [[Lưu và ghi sổ]].
5. Sửa tiếp bản nháp: mở nó, bấm [[Sửa nháp]]. Tạo nhầm: bấm [[Bỏ bản nháp này]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Món này đang có sẵn bản nháp ..., sửa tiếp bản đó | Mỗi món một bản nháp một lúc |
| Bản ... đã ghi sổ, muốn đổi thì bấm Điều chỉnh để ra bản mới | Dùng [[Điều chỉnh (ra phiên bản mới)]] |
| Bản ... đã ghi sổ, không bỏ được | Không bỏ bản đã ghi sổ |

**Lưu ý**
- Đổi công thức thì soát lại hướng dẫn chế biến (nút chuyển sang [[Soát lại HD]]).

## Đầu mã món NVLT, BTPB, BTPN, BAWC nghĩa là gì
Từ khoá: đầu mã, tiền tố mã, mã hàng, mã món, NVLT, BTPB, BTPN, NBTP, BAWC, BAWS, BANU, BAEN, BACF, BASS, BPKG, CCDC, VVPP, nguyên liệu, bán thành phẩm, thành phẩm, prefix

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Mọi màn có mã món | |

Bốn chữ đầu của mã cho biết loại món. Mã chuẩn là đầu mã kèm 5 chữ số, ví dụ BAWC00098.

| Đầu mã | Loại | Chặng máy hiểu |
|---|---|---|
| NVLT | Nguyên vật liệu thô | Nguyên liệu |
| BPKG, CCDC, VVPP | Bao bì, công cụ dụng cụ, văn phòng phẩm | Nguyên liệu |
| BTPB | Bán thành phẩm bánh | Bán thành phẩm |
| BTPN | Bán thành phẩm nước (quầy bar) | Bán thành phẩm |
| NBTP | Bán thành phẩm bánh ổ | Bán thành phẩm |
| BAWC | Bánh ổ (sinh nhật) | Thành phẩm |
| BAWS | Bánh sỉ | Thành phẩm |
| BAEN, BACF | Bánh lạnh, bánh khô (bánh lẻ) | Thành phẩm |
| BANU | Bánh nướng | Thành phẩm |
| BASS | Hộp bánh theo mùa | Thành phẩm |

**Lưu ý**
- Chặng cụ thể của bán thành phẩm xem mục "Chặng bán thành phẩm là gì".
- Thêm đầu mã mới: Việc này do anh Việt quyết.

## Chặng bán thành phẩm là gì
Từ khoá: chặng, chặng bán thành phẩm, BTP thành phần, BTP sơ cấp, BTP sẵn sàng, cấp 1, cấp 2, ruột bánh, bánh khuôn, C1, C2, kho đích, kho nhập thành phẩm, máy sửa kho đích theo chặng

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, kế toán giá thành, bếp | Desk: hồ sơ Món, ô Chặng bán thành phẩm | |

Mỗi món đứng ở một chặng: Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm.

| Lựa chọn ô Chặng bán thành phẩm | Ví dụ | Giữ tồn |
|---|---|---|
| BTP thành phần | Lớp bông lan, nhân bơ, kem dâu, làm xong ghép ngay | Không, đa số là mặt hàng ảo |
| BTP sơ cấp (cấp 1) | Ruột bánh, ghép các lớp | Có |
| BTP sẵn sàng (cấp 2) | Khuôn bánh đã bọc mousse, chờ trang trí | Có |

Máy xác định chặng theo thứ tự: ô khai tay trên hồ sơ món, đầu mã, chữ Cấp 1 / Cấp 2 trong tên, cuối cùng suy từ công thức.

**Kho theo chặng**
| Hàng | Kho |
|---|---|
| Nguyên liệu mọi lệnh | Kho Nguyên liệu của bếp |
| Bán thành phẩm làm xong | Kho Nguyên liệu của bếp |
| Thành phẩm làm xong | Kho Thành phẩm của bếp |

**Lưu ý**
- Chọn nhầm kho nhập thì máy tự đổi và báo "Máy sửa kho đích theo chặng".
- Hai kho BTP sơ cấp và BTP sẵn sàng của hai bếp đã tắt từ 28/08/2026, không chuyển hàng qua đó.

## Xem tồn kho theo chặng và chuyển hàng sai kho
Từ khoá: tồn kho theo chặng, tồn bán thành phẩm, hàng đang ở chặng nào, sai kho, hàng nằm sai kho, chuyển về đúng kho, tồn bếp

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, quản lý sản xuất, kế toán giá thành | Tồn kho theo chặng (/ton-kho-theo-chang) | [[Chuyển về ...]] |

Cho biết hàng của bếp đang đứng ở chặng nào (màn Tồn kho thì cho biết một kho có gì).

**Các bước**
1. Chọn bếp: [[Cả hai bếp]], [[Pastry]], [[Baker]].
2. Bấm chip chặng: Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm, hoặc [[Chưa phân chặng]]. Số trên chip là số mã có tồn.
3. Gõ ô tìm theo tên hoặc mã. Mỗi dòng ghi tổng tồn và tồn từng kho.
4. Bấm [[Sai kho]] để lọc hàng nằm ở kho khác chặng của nó.
5. Quản lý sản xuất bấm [[Chuyển về ...]] trên dòng, rồi [[Lập phiếu nháp]].
6. Ghi sổ phiếu kho nháp đó trên Desk (bấm [[desk:Xác nhận]]).

**Lưu ý**
- Chuyển kho hay nhập tay vào kho bếp sai chặng thì máy chỉ NHẮC, vẫn ghi được; hàng sẽ hiện ở chip Sai kho.
- Kiểm kê thấy hàng nằm sai kho thì cứ ghi đúng thực tế, rồi chuyển về bằng phiếu chuyển.
- Chữ làm tươi đỏ trên dòng là bán thành phẩm làm tươi.

## Mặt hàng ảo (phantom) là gì
Từ khoá: phantom, mã phantom, BTP phantom, mặt hàng ảo, công thức ảo, không quản tồn, không theo dõi tồn kho, is phantom, bán thành phẩm không có tồn, vì sao không thấy tồn, nổ thẳng nguyên liệu

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, quản lý sản xuất, kế toán giá thành | Công thức (/cong-thuc), Sản xuất (/san-xuat) | |

Mặt hàng ảo là bán thành phẩm CÓ công thức nhưng KHÔNG có kho: sinh ra và dùng hết trong cùng một ca bếp (lớp bột, lớp kem trộn xong đổ ngay). Phần lớn BTP thành phần là mặt hàng ảo.

**Trên Desk nhận ra bằng**
| Chỗ | Ô |
|---|---|
| Hồ sơ Món | Quản lý tồn kho bỏ tick |
| Công thức của chính nó | Là ĐMNVL ảo có tick |
| Dòng của nó trong công thức cha | Là MH ảo có tick |

**Hệ quả**
- Không có tồn kho, tồn trống hoặc 0 là đúng, không phải lỗi.
- Không tạo lệnh riêng. Hoàn tất lệnh món cha thì máy trừ thẳng nguyên liệu bên trong.
- Không chuyển kho, nhập kho, kiểm kê được.

**Lưu ý**
- BTP sơ cấp (cấp 1), BTP sẵn sàng (cấp 2) và bán thành phẩm nước (BTPN) thì ngược lại, PHẢI giữ tồn vì được làm sẵn, đóng gói hoặc chuyển kho.
- Ranh giới: thứ nào rời tay người làm thành một gói riêng, sang kho khác hay sang ca khác thì giữ tồn.

## Muốn chuyển kho một mặt hàng ảo thì làm sao
Từ khoá: tắt phantom, bỏ phantom, bỏ ảo, chuyển kho mã phantom, theo dõi tồn lại, bật quản lý tồn kho, maintain stock, phantom BOM, phantom item, giữ tồn bán thành phẩm

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý sản xuất, kế toán giá thành, kỹ thuật | Desk: Món, Desk: Công thức | |

Mặt hàng ảo không có tồn nên không chuyển kho được. Nếu thực tế bán thành phẩm đó được làm sẵn, cất trữ hoặc chuyển giữa hai bếp thì phải bỏ ảo để nó có tồn trở lại.

**Ba chỗ phải đổi cùng lúc, thiếu một là hỏng**
| Chỗ | Ô | Đổi thành |
|---|---|---|
| Hồ sơ Món của mã | Quản lý tồn kho | Tick |
| Công thức của chính mã đó (ra phiên bản mới) | Là ĐMNVL ảo | Bỏ tick |
| Mọi công thức cha đang dùng mã (ra phiên bản mới) | Là MH ảo trên dòng của mã | Bỏ tick |

**Các bước**
1. Báo quản lý sản xuất và kỹ thuật, nói rõ mã nào và vì sao cần giữ tồn.
2. Kỹ thuật đổi ba chỗ trên rồi dựng lại công thức cha.
3. Từ đó tạo lệnh riêng cho mã, nhập kho, chuyển kho như bán thành phẩm thường.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Vì có giao dịch đã nộp theo MH ..., không thể đổi giá trị của Quản lý tồn kho | Desk không cho tick lại ô này khi mã đã từng có phiếu; nhờ kỹ thuật |

**Lưu ý**
- Thiếu bước công thức cha thì lệnh món cha vẫn trừ thẳng nguyên liệu thô, không lấy từ tồn bán thành phẩm.
- Chỉ áp từ nay về sau, không sửa lệnh hay phiếu kho đã ghi sổ.
- Có giữ tồn mã nào hay không: Việc này do anh Việt quyết.
- Sắp có công cụ bỏ ảo trên app và Desk. Trong lúc chờ, nhờ kỹ thuật.

## Chuyển bán thành phẩm sang mặt hàng ảo hàng loạt
Từ khoá: chuyển phantom, chuyển sang phantom, chuyển sang ảo, bỏ ghi sổ kho BTP, dọn chứng từ thử, đóng lệnh treo, chạy thử, chạy thật

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Giám đốc, quản lý hệ thống | Chuyển phantom (/chuyen-phantom) | [[Chạy thật, ghi xuống hệ]] |

Chuyển hàng loạt các mã BTP thành phần sang mặt hàng ảo (bỏ quản lý tồn, sửa dòng công thức cha). Không có nút hoàn tác.

**Các bước**
1. Mở Dọn chứng từ thử. Đóng hết lệnh còn treo bằng [[Đóng lệnh này]] (đóng chứ không xoá).
2. Mã còn tồn thì xuất hết hoặc kiểm kê về 0.
3. Khi mọi thứ xanh, bấm [[Xong, sang bước chuyển Phantom]].
4. Đọc BẢN CHẠY THỬ: số mã bỏ theo dõi tồn, số dòng công thức đổi, số công thức cha dựng lại, và phần DÒNG CHƯA XỬ ĐƯỢC.
5. Bấm [[Chạy thật, ghi xuống hệ]], rồi [[Ghi thật]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Khung đỏ CHƯA CHẠY THẬT ĐƯỢC (còn lệnh treo, còn tồn) | Bấm [[Sang màn Dọn chứng từ thử]] để xử lý |

**Lưu ý**
- Chạy ngoài giờ bếp đang làm. Việc này do anh Việt quyết.

## Soạn hướng dẫn chế biến
Từ khoá: hướng dẫn chế biến, cách làm, quy trình làm bánh, SOP món, các bước làm, tiêu chí QC, CCP, OPRP, dị ứng, ảnh món đạt, in A4

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp trưởng, bếp phó, quản lý sản xuất | Hướng dẫn chế biến (/huong-dan-che-bien) | [[Lưu]] |

**Các bước**
1. Ở màn Công thức bấm nút hình quyển sách trên thẻ món, hoặc [[Hướng dẫn chế biến]] trong chi tiết công thức.
2. Bấm [[Nạp từ công thức đang dùng]] để kéo nguyên liệu, số lượng sang phần Định lượng.
3. Điền Mẻ chuẩn và thời gian: Mẻ chuẩn, Ra bao nhiêu thành phẩm, Chuẩn bị, Làm, Nghỉ ủ đông, Hạn sử dụng.
4. Bấm [[Thêm bước]]: Công đoạn, Cách làm, Thông số, Nhiệt độ, Thời gian, Điểm tới hạn (Bước thường, OPRP, CCP).
5. Bấm [[Thêm tiêu chí]] cho Tiêu chí QC: Không đạt khi, Không đạt thì làm gì.
6. Điền Dị ứng và bảo quản, bấm [[Lưu]].
7. Sau khi lưu: [[Chụp ảnh món đạt]], [[In A4]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Lưu lại một lần rồi mới in được / mới đính ảnh được | Bấm Lưu trước |

**Lưu ý**
- Trạng thái hướng dẫn: Nháp, Đang dùng, Ngừng dùng.
- Nạp lại từ công thức thay toàn bộ phần Định lượng, không đụng các bước và tiêu chí QC.
- Nút đỏ [[Soát lại HD]]: công thức đã đổi sau khi soạn; soát rồi lưu để gỡ.

## Xuất nguyên liệu cho đơn tiệc
Từ khoá: đơn tiệc, tiệc, B2B, catering, teabreak, bánh thiết kế, bán sỉ, xuất nguyên liệu cho tiệc, xuất kho theo hợp đồng, giá vốn tiệc

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, kho, kinh doanh | Đơn tiệc (/don-tiec) | [[Ghi sổ phiếu xuất]] |

Gói tiệc làm theo đơn, không có công thức cố định, nên không qua lệnh sản xuất. Bếp xuất thẳng nguyên liệu đã dùng cho từng tiệc.

**Các bước**
1. Lọc [[Sắp tới]], [[Tuần này]] hoặc [[Tất cả]], chọn đơn.
2. Xem Ngày sự kiện, Giao lúc, Giá trị, Thực đơn.
3. Bấm [[Xuất kho nguyên liệu]], chọn Kho xuất trước.
4. Gõ ô Tìm tên hoặc mã nguyên liệu (chỉ hiện mã còn tồn), bấm [[Thêm]].
5. Gõ số lượng theo ĐƠN VỊ KHO hiện cạnh ô, ghi chú nếu cần (ví dụ: đợt 1).
6. Bấm [[Ghi sổ phiếu xuất]], đọc lại số dòng và kho, bấm [[Ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa chọn kho xuất | Chọn kho |
| Chưa có dòng nào có số lượng lớn hơn 0 | Gõ số |
| Có dòng gõ nhiều hơn tồn kho | Kiểm đơn vị: mã tính bằng Kg mà gõ số gram là lệch nghìn lần |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 632 | Tài khoản của kho xuất | Khi bấm Ghi sổ, gắn theo đơn tiệc |

**Lưu ý**
- Phiếu vào thẳng sổ kho và sổ cái. Ghi nhầm thì huỷ phiếu (phải ghi lý do), không sửa được.

## Mua hàng phát sinh cho nghiên cứu phát triển
Từ khoá: nghiên cứu phát triển, R&D, RnD, làm thử món mới, test bánh, mua hàng phát sinh, mua hàng test, hàng ngoài danh mục, mua lẻ, quỹ tạm ứng

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, R&D, thu mua, kế toán | Nghiên cứu phát triển (/nghien-cuu-phat-trien), tiêu đề Mua hàng phát sinh | [[Gửi yêu cầu]] |

Phiếu cho hàng ngoài danh mục hoặc trên 500.000 một hoá đơn, thường để test món mới: không tạo mã, không theo dõi tồn kho. Đây là màn duy nhất của địa chỉ này; làm thử theo công thức có mã thì dùng màn Sản xuất.

**Các bước**
1. Bấm nút tròn dấu cộng để tạo phiếu.
2. Ghi Mục đích / dự án (bắt buộc), Ngày cần hàng, Ghi chú chung.
3. Bấm [[+ Thêm hàng cần mua]]: tên hàng, số lượng, link tham khảo, ảnh.
4. Bấm [[Gửi yêu cầu]].
5. Thu mua bấm từng dòng ghi kết quả mua (nhà cung cấp, giá), hoặc [[Không mua được]].
6. Mua xong bấm [[Hoàn thành phiếu]].
7. Kế toán bấm [[Lập phiếu ghi chi phí (nháp)]] để dựng hoá đơn mua nháp trả từ quỹ tạm ứng.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa ghi mục đích của phiếu | Điền Mục đích / dự án |
| Chưa ghi tên hàng cần mua | Điền tên hàng |

**Lưu ý**
- Có được mua ngoài danh mục hay không: Việc này do anh Việt quyết.
