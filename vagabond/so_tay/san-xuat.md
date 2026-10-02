# Sản xuất và công thức

## Lập kế hoạch sản xuất cho một ngày

Từ khoá: kế hoạch sản xuất, KHSX, production plan, lên kế hoạch, tính nguyên liệu trong ngày, nổ BOM, bao nhiêu bánh phải làm, phiếu kế hoạch, huỷ kế hoạch, lập lại kế hoạch
Ai dùng: Quản lý sản xuất, bếp trưởng, bếp phó (xem)
Màn hình: Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat)

Máy gom mọi phiếu yêu cầu sản xuất hẹn cho một ngày (kể cả phiếu quá hạn) rồi tính ra thành phẩm, bán thành phẩm, nguyên liệu. Nửa đêm máy tự lập phiếu cho ngày mới.

Các bước:
1. Mở màn Lập kế hoạch sản xuất. Dùng nút "◀ Hôm trước" / "Hôm sau ▶" để chọn ngày bếp làm.
2. Nếu ngày đó chưa có phiếu, bấm "📋 Lập kế hoạch cho ngày này", rồi bấm "Lập kế hoạch" để xác nhận.
3. Đọc ba tab "🎂 Thành phẩm", "🥣 Bán thành phẩm", "🌾 Nguyên liệu". Mỗi thẻ có các cột Cần, Tồn đầu, Tồn giờ, Phải làm.
4. Lọc theo bếp (Cả hai bếp, Pastry, Baker) và theo tình trạng: "🔴 Phải làm", "🟡 Thiếu một phần", "⚙️ Đã có lệnh", "🟢 Đủ tồn".
5. Bấm vào thẻ một món để xổ ra danh sách nguyên liệu của món đó.

Vì sao bị chặn:
- "Ngày ... đã có phiếu kế hoạch ... rồi, không lập thêm": mỗi ngày chỉ một phiếu, mở phiếu đó ra dùng.
- "Không có phiếu yêu cầu sản xuất nào hẹn ngày ...": chưa có điểm bán nào gửi yêu cầu cho ngày đó.

Lưu ý:
- Muốn huỷ phiếu: bấm chip "📑 Các phiếu kế hoạch", chọn phiếu, bấm "🗑️ Huỷ phiếu". Phiếu đã tạo lệnh sản xuất thì máy không cho huỷ, phải huỷ các lệnh đó trước.
- Chỉ quản lý sản xuất và giám đốc lập, huỷ phiếu; bếp phó chỉ xem.

## Ra lệnh sản xuất từ kế hoạch

Từ khoá: tạo lệnh từ kế hoạch, ra lệnh, work order, LSX, lệnh sản xuất hàng loạt, tick chọn món, đổi kho nhập, sửa số cần, đặt lại tồn, tồn giờ
Ai dùng: Quản lý sản xuất, bếp trưởng
Màn hình: Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat)

Từ phiếu kế hoạch, bếp ra lệnh sản xuất cho từng món hoặc nhiều món một lượt.

Các bước:
1. Một món: bấm vào thẻ món, xem "Nhập vào" (kho nhập), bấm "đổi kho" nếu cần, rồi bấm "✅ Hoàn thành, tạo lệnh sản xuất".
2. Muốn làm số khác số máy tính: gõ vào ô "Cần" trên thẻ trước khi bấm tạo lệnh.
3. Nhiều món: tick ô vuông đầu các thẻ, bấm "⚙️ Tạo lệnh cho N món đã chọn", rồi bấm "Tạo N lệnh". Máy ra lệnh theo số đang hiện và kho máy đoán.
4. Bấm "🏭 Xem lệnh đã tạo" để sang màn Sản xuất.

Vì sao bị chặn:
- "Dòng này đã ra lệnh đủ rồi" hoặc "Món ... đã ra lệnh đủ số rồi".
- "Chọn kho nhập trước đã": món chưa có kho nhập, bấm "chọn kho".
- "Kho ... không phải kho bếp": bánh làm xong phải nhập kho bếp trước, chuyển sang điểm bán là phiếu điều chuyển riêng.
- "Món ... không quản tồn kho, nó tự nổ trong lệnh của món cha": đây là mã phantom, không cần lệnh riêng.

Lưu ý:
- Ô "Tồn giờ" gõ được: gõ số mới rồi rời khỏi ô, máy hỏi "Đặt tồn ...", bấm "Ghi phiếu kiểm kê" là máy ghi một phiếu kiểm kê THẬT ngay lúc đó. Ô "Tồn đầu" không sửa được.

## Xin chuyển nguyên liệu từ kho tổng về bếp

Từ khoá: chuyển nguyên liệu, xin nguyên liệu, chuyển kho nguyên liệu cho sản xuất, material transfer, kho tổng 307, lấy hàng về bếp, thiếu nguyên liệu ở bếp
Ai dùng: Quản lý sản xuất, bếp trưởng; kho tổng ghi sổ
Màn hình: Lập kế hoạch sản xuất (/lap-ke-hoach-san-xuat)

Lệnh sản xuất trên app KHÔNG có bước "chuyển nguyên liệu vào sản xuất" riêng. Nguyên liệu bị trừ thẳng tại kho Nguyên liệu của bếp lúc bấm Hoàn tất. Vì vậy hàng phải nằm sẵn ở kho Nguyên liệu của bếp (Baker hoặc Pastry) trước khi làm.

Các bước:
1. Mở phiếu kế hoạch của ngày, chọn bếp ở chip (Pastry hoặc Baker) nếu chỉ xin cho một bếp.
2. Bấm "📦 Xin chuyển nguyên liệu", rồi bấm "Tạo phiếu xin".
3. Máy tạo phiếu chuyển kho NHÁP từ Kho tổng 307 sang kho Nguyên liệu của bếp, đúng theo bảng nguyên liệu còn thiếu, và báo số phiếu.
4. Kho tổng soát hàng rồi ghi sổ phiếu. Bếp nhận hàng ở màn Hàng chuyển về kho tôi (/hang-chuyen-ve-kho-toi).

Vì sao bị chặn:
- "Phiếu này không có dòng nguyên liệu nào thiếu": bếp đã đủ hàng.
- "Không có gì để xin thêm": các mã đã được xin ở phiếu trước.

Lưu ý: bếp này thiếu mà bếp kia còn thì lập phiếu xuất điều chuyển giữa hai kho bếp, câu báo thiếu lúc hoàn tất sẽ nói kho nào đang còn. <!-- kiểm: tên màn chuyển kho giữa hai bếp có phải Xuất điều chuyển (/xuat-dieu-chuyen) không -->

## Xem bảng bếp hôm nay

Từ khoá: bảng bếp, việc bếp hôm nay, danh sách bánh cần làm, phiếu yêu cầu sản xuất, YCSX, đánh dấu đã làm, xác nhận đã giao, kitchen board
Ai dùng: Bếp, bếp phó
Màn hình: Bảng bếp hôm nay (/bang-bep-hom-nay)

Màn gộp mọi phiếu yêu cầu sản xuất của một ngày theo món, để bếp biết tổng số bánh cần làm và giờ cần lấy.

Các bước:
1. Chọn ngày bằng chip "Hôm qua", "Hôm nay", "Ngày mai" hoặc chip lịch (gõ ngày dạng nn/tt/nnnn).
2. Người thuộc một bếp mặc định chỉ thấy phiếu gửi cho bếp mình; bấm chip "👥 Tất cả bếp" để xem hết.
3. Phần "Cần làm - gộp theo món": bấm vào một món để đánh dấu ✓ đã làm (bấm lại để bỏ).
4. Khi mọi món của phiếu đã ✓, phiếu hiện "Sẵn sàng giao". Bấm "Xác nhận đã giao N phiếu", rồi "Xác nhận". Phiếu chuyển sang "Đã giao".
5. Bấm vào một phiếu trong "Phiếu trong ngày" để mở chi tiết.

Lưu ý:
- Dòng cảnh báo "Còn N phiếu của những ngày trước chưa xác nhận xong" nghĩa là có phiếu cũ chưa giao, bấm chip Hôm qua để xem.
- Đánh dấu đã làm ở đây KHÔNG trừ kho. Trừ nguyên liệu và nhập thành phẩm là việc của lệnh sản xuất (bấm Hoàn tất).

## Tạo lệnh sản xuất

Từ khoá: tạo lệnh sản xuất, lệnh sản xuất mới, work order, LSX, ra lệnh, sản xuất bánh, làm bánh, chọn món cần làm, quét mã món
Ai dùng: Bếp, bếp phó, quản lý sản xuất
Màn hình: Sản xuất (/san-xuat)

Các bước:
1. Mở màn Sản xuất, bấm nút tròn dấu cộng góc dưới để vào "Tạo lệnh sản xuất".
2. Kiểm thẻ kho: "Lấy nguyên liệu từ kho" (mặc định theo kho đã khai trên từng món) và "Nhập thành phẩm vào kho" (máy tự chọn theo chặng của món).
3. Chọn khoảng nhu cầu: "Đến hôm nay", "Đến ngày mai", "Đến hết tuần".
4. Thêm món: gõ tên hoặc mã vào ô "Tìm tên hoặc mã món", hoặc bấm nút 📷 để quét mã vạch, rồi bấm dấu "+" trên thẻ món. Muốn lấy hết thì bấm chip "✓ Chọn tất cả N món đang cần". Món không nằm trong phiếu yêu cầu thì bấm "+ Thêm món ngoài phiếu yêu cầu".
5. Trên mỗi thẻ đã chọn, chỉnh "Số lượng sẽ làm".
6. Bấm "Tạo N lệnh sản xuất".
7. Máy chuyển sang màn "Bán thành phẩm cần làm" (xem mục riêng).

Vì sao bị chặn:
- "Chưa chọn món nào".
- "Chưa chọn kho nguyên liệu hoặc kho thành phẩm".
- Thẻ ghi "Chưa có công thức": món chưa có công thức nên không tạo lệnh được, dùng nút "🧾 Khai nguyên liệu đã dùng".

Lưu ý: mỗi thẻ hiện "Phòng ban cần", "Đã có lệnh", "Tồn thành phẩm" để tránh làm trùng. Máy không tự tick sẵn món nào.

## Bán thành phẩm cần làm sau khi tạo lệnh

Từ khoá: bán thành phẩm, BTP, ruột bánh, lệnh bán thành phẩm, lệnh con, sub assembly, nhiều cấp, làm tươi, BTP còn thiếu
Ai dùng: Bếp, quản lý sản xuất
Màn hình: Sản xuất (/san-xuat), màn "Bán thành phẩm cần làm"

Ngay sau khi tạo lệnh, máy tính các bán thành phẩm (đang theo dõi tồn) còn thiếu để làm được số bánh vừa ra lệnh: Công thức cần, Tồn kho NVL, Còn thiếu.

Các bước:
1. Xem từng thẻ, bấm ✓ để chọn hoặc bỏ chọn, chỉnh "Số lượng sẽ làm".
2. Bấm "Duyệt và tạo N lệnh". Máy có thể hỏi tiếp cấp dưới nữa (tối đa bốn cấp).
3. Không cần làm thì bấm "Bỏ qua bước này".

Lưu ý:
- Bán thành phẩm nhập về kho Nguyên liệu của bếp, không phải kho Thành phẩm.
- Bán thành phẩm phantom (không quản tồn) và loại "làm tươi" KHÔNG hiện ở đây: phantom tự trừ thẳng nguyên liệu trong lệnh của món cha; loại làm tươi thì máy tự làm khi bếp bấm Hoàn tất lệnh món cha.
- Nếu hiện "Không cần làm thêm bán thành phẩm nào" là tồn đã đủ.

## Hoàn tất lệnh sản xuất

Từ khoá: hoàn tất lệnh, hoàn thành lệnh sản xuất, xong lệnh, nhập kho thành phẩm, trừ nguyên liệu, báo sản lượng, cân thực tế, hao hụt, manufacture, finish work order, ghi sổ nhiều lệnh
Ai dùng: Bếp, bếp phó, quản lý sản xuất
Màn hình: Sản xuất (/san-xuat)

Bấm Hoàn tất là lúc máy trừ nguyên liệu và nhập thành phẩm vào kho. Bút toán kho ghi xong không sửa lại được.

Các bước:
1. Trên danh sách lệnh, bấm nút ✓ ở cuối dòng lệnh; hoặc mở lệnh rồi bấm "✅ Hoàn tất".
2. Hộp "Hoàn thành phiếu" hiện hai ô: "Số lượng làm theo lệnh" (để trừ nguyên liệu) và "Thực tế cân được" (để nhập kho). Đổi đơn vị tính ở ô chọn cạnh số nếu muốn nhập theo kg hay gram, máy tự quy đổi.
3. Chip "Lần trước ..." gợi ý số bếp hay gõ, bấm vào là điền.
4. Bấm "✅ Hoàn thành".
5. Nếu có bán thành phẩm làm tươi, hộp "Máy làm luôn giúp bếp" hiện danh sách sẽ làm tươi và nguyên liệu sẽ trừ (chip đỏ là thiếu). Bấm "✅ Xác nhận tạo lệnh".
6. Nhiều lệnh cùng món: bấm ✓ trên thẻ gộp, gõ một tổng số; máy chia lần lượt cho từng lệnh, hiện danh sách, bấm "Ghi sổ N lệnh".

Lưu ý: cân ít hơn số làm thì phần chênh được ghi là hao hụt và lệnh vẫn đóng.

Hạch toán: từ 01/10/2026, dòng nguyên liệu Nợ 621 / Có 152; dòng thành phẩm Nợ 1551 / Có 154, mang trung tâm chi phí của bếp. <!-- kiểm: bán thành phẩm nhập kho Nguyên liệu thì Nợ tài khoản kho nào -->

## Vì sao không hoàn tất được lệnh sản xuất

Từ khoá: không hoàn tất được, lỗi hoàn tất, bị chặn, thiếu hàng, thiếu nguyên liệu, không đủ tồn, kho không đủ, thiếu lô, batch mandatory, lệnh treo, lỗi sản xuất
Ai dùng: Bếp, quản lý sản xuất
Màn hình: Sản xuất (/san-xuat)

Vì sao bị chặn:
- "Kho ... không đủ ... để trừ: còn thiếu ...": kho Nguyên liệu của bếp thiếu hàng. Nếu câu báo kèm "Mã này đang còn ở ... tại kho ...", hãy chuyển kho phần thiếu rồi bấm lại. Nếu báo "Chưa tìm thấy tồn mã này ở kho khác" thì kiểm tồn, nhập hàng hoặc kiểm kê lại.
- Câu báo có "Mã thay thế đã khai đang còn ...": mã gốc và mã thay thế cùng kho đều không đủ; mã thay thế nằm ở kho khác thì chuyển về đúng kho rồi bấm lại.
- Chip "⚠️ Thiếu N nguyên liệu" trên dòng lệnh hoặc chữ đỏ ở "Nguyên liệu sẽ trừ": xem trước khi bấm.
- "Số làm theo lệnh không được quá số còn lại là ...": số dư thì ghi vào ô "Thực tế cân được", không ghi vào ô làm theo lệnh.
- "Lệnh này đã làm đủ số rồi" hoặc "Lệnh Đã dừng / Đã đóng nên không hoàn tất được".
- "Chỉ bếp, quản lý sản xuất hoặc giám đốc mới hoàn tất lệnh được": tài khoản chưa có vai bếp, nhờ quản lý mở quyền.
- "Không xác định được kho đích theo chặng ..." hoặc "Kho đích theo chặng ... chưa được tạo": báo quản lý sản xuất.

Lưu ý:
- Lỗi thiếu lô ("Serial No / Batch No are mandatory") gần như không còn: từ 30/09/2026 mọi mã đã tắt quản lý theo lô. Còn gặp thì báo kỹ thuật.
- Máy không ghi âm kho; thiếu là dừng, không để lại phiếu nháp.

## Nguyên liệu hết hàng thì máy có tự dùng mã thay thế không

Từ khoá: mã thay thế, nguyên liệu thay thế, hàng thay thế, item alternative, alternative item, hết whipping, hết bơ, dùng mã khác, thay nguyên liệu, mã gốc hết hàng
Ai dùng: Bếp, quản lý sản xuất, kế toán giá thành
Màn hình: Sản xuất (/san-xuat), lúc bấm Hoàn tất

Có, từ v553 (02/10/2026). Khi bấm Hoàn tất mà mã gốc thiếu ở kho nguyên liệu, máy tự lấy mã thay thế đã khai cho phần còn thiếu, cùng kho.

Điều kiện để máy tự thay:
1. Cặp thay thế đã được khai (xem mục "Khai mã thay thế cho nguyên liệu").
2. Mã gốc đã bật ô cho phép dùng hàng thay thế trên hồ sơ món.
3. Hai mã cùng đơn vị tính kho (gram thay gram).
4. Mã thay thế còn tồn ở CÙNG kho nguyên liệu của lệnh.
5. Chỉ áp cho sản xuất (hoàn tất lệnh, làm tươi, khai nguyên liệu). Nhận hàng điều chuyển thì không bao giờ tự đổi mã.

Máy dùng hết mã gốc trước, thiếu bao nhiêu mới lấy mã thay bấy nhiêu. Dòng thay trên phiếu ghi "Dùng thay ... đang thiếu tại kho (mã thay thế đã khai)", và lệnh vẫn tính là đã dùng đủ nguyên liệu gốc.

Vì sao bị chặn: mã gốc và mã thay cộng lại vẫn không đủ thì máy báo thiếu, kèm tồn của mã thay thế ở các kho khác.

Lưu ý: giá vốn thành phẩm thay đổi theo giá của mã thay thế. Việc chọn mã nào được thay cho mã nào do bếp trưởng và kế toán giá thành quyết.

## Khai mã thay thế cho nguyên liệu

Từ khoá: khai mã thay thế, khai nguyên liệu thay thế, mặt hàng thay thế, item alternative, cặp thay thế, hai chiều, two way, cho phép hàng thay thế, allow alternative item
Ai dùng: Kế toán giá thành, quản lý sản xuất, quản lý danh mục
Màn hình: Desk: Mặt hàng thay thế (Item Alternative)

Các bước:
1. Trên Desk mở hồ sơ món GỐC, bật ô "Cho phép dùng hàng thay thế" rồi lưu. <!-- kiểm: nhãn tiếng Việt của ô Allow Alternative Item trên form Item -->
2. Mở danh sách Mặt hàng thay thế, bấm Thêm mới.
3. Chọn mã gốc và mã thay thế. Tick "Hai chiều" nếu hai mã thay được cho nhau. <!-- kiểm: nhãn ô Two-way và các ô mã trên form Item Alternative -->
4. Lưu.

Đọc cột cảnh báo trên danh sách:
- "Không thay được": hai mã khác đơn vị tính, món thay đã ngừng dùng, hoặc món gốc chưa bật cho phép thay. Máy sẽ KHÔNG dùng cặp này.
- "Cần xem": món thay đang hết hàng ở mọi kho, chưa có giá vốn, giá vốn chênh trên 10 phần trăm, hoặc món gốc chưa nằm trong công thức nào.
- "Dùng được": ổn.

Lưu ý: số liệu cảnh báo được tính lại lúc lưu cặp và mỗi đêm. Thay một nguyên liệu đang có giá bằng một mã chưa có giá vốn sẽ kéo giá vốn thành phẩm xuống mà không ai thấy.

## Sửa số lượng hoặc huỷ lệnh sản xuất

Từ khoá: sửa lệnh, sửa số lượng lệnh, huỷ lệnh sản xuất, xoá lệnh, tạo nhầm lệnh, lệnh trùng, đóng lệnh, dừng lệnh
Ai dùng: Quản lý sản xuất, giám đốc
Màn hình: Sản xuất (/san-xuat), mở chi tiết lệnh

Các bước:
1. Mở lệnh trên danh sách.
2. Lệnh còn nháp: bấm "✏️ Sửa số lượng", gõ số mới.
3. Muốn bỏ lệnh: bấm "🗑️ Huỷ lệnh này", rồi "Huỷ lệnh". Số của món được trả lại cho kế hoạch, ra lệnh mới được ngay.

Vì sao bị chặn:
- "Lệnh ... đã ghi sổ nên không sửa số được. Huỷ lệnh rồi ra lệnh mới với số đúng."
- "Lệnh ... đã làm ra ... rồi nên không huỷ được. Báo quản lý sản xuất để dừng lệnh."
- "Lệnh ... đã chuyển nguyên liệu vào sản xuất nên không huỷ được. Trả nguyên liệu về kho trước."
- "Số lượng phải lớn hơn 0."

Lưu ý: lệnh đã hoàn tất một phần thì không huỷ trên app. Phần đã nhập kho là bút toán đã ghi sổ, không sửa lại; cần xử lý thì liên hệ kế toán trưởng.

## Làm món chưa có công thức

Từ khoá: món chưa có công thức, chưa có BOM, khai nguyên liệu đã dùng, sản xuất không định mức, làm thử, ghi nhận nguyên liệu, lưu thành công thức
Ai dùng: Bếp, bếp phó
Màn hình: Sản xuất (/san-xuat), nút "🧾 Món chưa có công thức"

Món chưa có công thức thì không tạo lệnh được. Bếp khai trực tiếp đã dùng những gì và làm được bao nhiêu.

Các bước:
1. Trên màn Sản xuất bấm "🧾 Món chưa có công thức", chọn món (hoặc bấm "🧾 Khai nguyên liệu đã dùng" trên thẻ món ở màn Tạo lệnh).
2. Kiểm kho "Lấy nguyên liệu từ kho".
3. Gõ "Số lượng làm được".
4. Bấm "+ Thêm nguyên liệu", chọn từng nguyên liệu, gõ "Số lượng đã dùng", chọn đơn vị.
5. Giữ dấu ✓ ở "Lần sau khỏi khai lại" nếu muốn lưu thành công thức của món.
6. Bấm "Xong - trừ kho nguyên liệu", rồi "Xác nhận trừ kho".

Vì sao bị chặn:
- "Chưa nhập số lượng làm được", "Chưa khai nguyên liệu nào", "Có nguyên liệu chưa nhập số lượng".
- "Không thể dùng chính món đang làm làm nguyên liệu".

Lưu ý: công thức lưu từ đây là bản NHÁP; bếp trưởng vào Danh mục công thức rà lại rồi bấm Ghi sổ thì lần sau mới tạo lệnh theo nó được.

## In tem cho mẻ bánh

Từ khoá: in tem, tem HACCP, tem nhãn, nhãn bánh, NSX, HSD, hạn dùng, mẻ, batch, in lại tem, máy in tem, QZ Tray, Brother
Ai dùng: Bếp
Màn hình: Sản xuất (/san-xuat)

Các bước:
1. Mở lệnh, bấm "🖨️ In tem" (trước khi hoàn tất) hoặc "🖨️ In lại tem" (sau khi hoàn tất). Sau khi hoàn tất, máy cũng tự mở màn In tem HACCP.
2. Xem mẫu tem: tên món, NSX, HSD, điều kiện bảo quản, mã mẻ.
3. Chỉnh "Số tem cần in", bấm "In thử 1 tem" hoặc "🖨️ In N tem".
4. In cả nhóm lệnh cùng món: mở thẻ gộp, bấm "🖨️ In tem cả N lệnh" (cần máy in tem đã nối QZ Tray).

Vì sao bị chặn:
- "Món này chưa bật theo dõi lô nên chưa in được tem".
- "Máy in tem chưa nối qua QZ Tray nên chỉ in được từng lệnh một": bật QZ Tray rồi bấm lại, hoặc in từng lệnh.

Lưu ý: hạn dùng trên tem lấy từ số giờ hạn dùng hoặc số ngày hạn dùng khai trên hồ sơ món. <!-- kiểm: từ v545 mọi mã đã tắt quản lý theo lô, nút In tem trên lệnh sản xuất có còn in được không hay luôn báo "chưa bật theo dõi lô" -->

## Xem và tìm công thức

Từ khoá: công thức, BOM, định mức, định lượng, recipe, danh mục công thức, tra công thức, xem nguyên liệu của bánh, phiên bản công thức, bản cũ
Ai dùng: Bếp, bếp phó, quầy bar, quản lý sản xuất, kế toán giá thành
Màn hình: Công thức (/cong-thuc)

Các bước:
1. Mở màn Công thức (Danh mục công thức). Chọn khu: "🎂 Pastry", "🥐 Baker", "🍵 Quầy Bar", "❓ Chưa phân".
2. Gõ vào ô "Tìm theo tên hoặc mã món". Khi tìm, máy tạm bỏ lọc khu và tìm cả tiệm.
3. Lọc thêm theo trạng thái (Đang dùng, Nháp, Bản cũ, Đã huỷ), theo tình trạng hướng dẫn chế biến, theo chặng (Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm).
4. Bấm vào một công thức để xem: mẻ ra bao nhiêu, danh sách nguyên liệu và số lượng cho một mẻ, ghi chú từng dòng.
5. Phần "Chuỗi phiên bản" cho bấm sang bản trước hoặc bản sau.

Lưu ý:
- "Đang dùng" là bản lệnh sản xuất đang nổ theo. "Bản cũ" vẫn tra được nhưng không dùng nữa.
- Nút "📖" trên thẻ cho biết tình trạng hướng dẫn chế biến: cam là chưa soạn, đỏ "⚠️ Soát lại HD" là công thức đã đổi sau khi soạn.

## Tạo công thức mới

Từ khoá: tạo công thức, lập công thức, thêm BOM, định mức mới, recipe mới, công thức cho món mới, lưu nháp công thức, ghi sổ công thức
Ai dùng: Bếp phó, quầy bar (soạn nháp); bếp trưởng, quản lý công thức, giám đốc (ghi sổ)
Màn hình: Công thức (/cong-thuc)

Các bước:
1. Trên màn Công thức bấm nút tròn dấu cộng, chọn món cần lập công thức.
2. Gõ "Một mẻ ra được" (số lượng thành phẩm một mẻ).
3. Bấm "+ Thêm nguyên liệu", chọn từng nguyên liệu, gõ "Số lượng cho một mẻ".
4. Bấm "💾 Lưu nháp", hoặc "✅ Lưu và ghi sổ" nếu có quyền ghi sổ.
5. Người không ghi sổ được: lưu nháp rồi nhờ bếp trưởng mở bản nháp và bấm "✅ Ghi sổ".

Vì sao bị chặn:
- "Công thức phải có ít nhất một dòng nguyên liệu."
- "Có nguyên liệu chưa nhập số lượng." / "Chưa nhập mẻ ra được bao nhiêu."
- "Nguyên liệu này đã có trong công thức".
- "Món này đang có bản nháp ... chờ duyệt, sửa tiếp bản đó."
- "Màn này chỉ bếp và quầy bar soạn công thức được."
- "Chỉ bếp trưởng (Manufacturing Manager) hoặc giám đốc mới ghi sổ công thức."

Lưu ý: ghi sổ xong, lệnh sản xuất từ giờ nổ theo bản này và giá vốn tính theo bản này.

## Điều chỉnh công thức đang dùng

Từ khoá: sửa công thức, điều chỉnh công thức, đổi định mức, đổi định lượng, phiên bản mới, cập nhật BOM, sửa BOM, bỏ bản nháp
Ai dùng: Bếp phó, quầy bar (soạn); bếp trưởng, giám đốc (ghi sổ)
Màn hình: Công thức (/cong-thuc)

Công thức đã ghi sổ không sửa thẳng được. Muốn đổi thì tạo phiên bản mới; ghi sổ bản mới xong, bản cũ tự lui về làm "Bản cũ", vẫn tra lại được.

Các bước:
1. Mở công thức đang dùng, bấm "🔁 Điều chỉnh (ra phiên bản mới)".
2. Máy tạo bản nháp chép từ bản đang dùng và mở màn sửa.
3. Sửa số lượng, bấm dấu "×" để bỏ dòng, "+ Thêm nguyên liệu" để thêm.
4. Bấm "💾 Lưu nháp" hoặc "✅ Lưu và ghi sổ".
5. Muốn sửa tiếp bản nháp: mở nó, bấm "✏️ Sửa nháp". Tạo nhầm: bấm "Bỏ bản nháp này".

Vì sao bị chặn:
- "Món này đang có sẵn bản nháp ..., sửa tiếp bản đó": mỗi món chỉ một bản nháp một lúc.
- "Bản ... đã ghi sổ, muốn đổi thì bấm Điều chỉnh để ra bản mới."
- "Bản ... đã ghi sổ, không bỏ được."

Lưu ý: đổi công thức thì soát lại hướng dẫn chế biến của món (nút chuyển sang "⚠️ Soát lại HD").

## Đầu mã món NVLT, BTPB, BTPN, BAWC nghĩa là gì

Từ khoá: đầu mã, tiền tố mã, mã hàng, mã món, NVLT, BTPB, BTPN, NBTP, BAWC, BAWS, BANU, BAEN, BACF, BASS, BPKG, CCDC, VVPP, nguyên liệu, bán thành phẩm, thành phẩm
Ai dùng: Mọi bộ phận
Màn hình: mọi màn có mã món

Bốn chữ đầu của mã cho biết món thuộc loại nào:
- NVLT: nguyên vật liệu thô (bột, bơ, kem, trứng...).
- BPKG: bao bì. CCDC: công cụ dụng cụ. VVPP: văn phòng phẩm.
- BTPB: bán thành phẩm bánh. BTPN: bán thành phẩm nước (quầy bar). NBTP cũng là bán thành phẩm.
- BAWC: bánh ổ (bánh sinh nhật). BAWS: bánh sỉ.
- BAEN: bánh lạnh (bánh lẻ). BACF: bánh khô (bánh lẻ).
- BANU: bánh nướng. BASS: hộp bánh theo mùa.

Lưu ý:
- Máy dựa vào đầu mã để biết chặng: NVLT, BPKG, CCDC, VVPP là chặng Nguyên liệu; BAWC, BANU, BAEN, BACF, BAWS, BASS là chặng Thành phẩm; BTPB, BTPN, NBTP là bán thành phẩm, chặng cụ thể xem mục "Chặng bán thành phẩm".
- Mã chuẩn gồm đầu mã kèm 5 chữ số, ví dụ BAWC00098, BANU00065.
- Bảng đầu mã đã được anh Việt chốt; muốn thêm đầu mã mới thì hỏi anh Việt.

## Chặng bán thành phẩm là gì

Từ khoá: chặng, chặng bán thành phẩm, BTP thành phần, BTP sơ cấp, BTP sẵn sàng, cấp 1, cấp 2, ruột bánh, bánh khuôn, C1, C2, kho đích, kho nhập thành phẩm, máy sửa kho đích theo chặng
Ai dùng: Quản lý sản xuất, kế toán giá thành, bếp
Màn hình: Desk: Item (ô "Chặng bán thành phẩm")

Mỗi món đứng ở một chặng: Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm. Ô "Chặng bán thành phẩm" trên hồ sơ món có ba lựa chọn:
- BTP thành phần: lớp lẻ như lớp bông lan, nhân bơ, kem dâu; thường không theo tồn, làm xong ghép ngay. Máy xếp về sơ cấp khi chọn kho.
- BTP sơ cấp (cấp 1): ruột bánh, ghép các lớp thành phần lại.
- BTP sẵn sàng (cấp 2): khuôn bánh đã bọc lớp mousse, chờ trang trí.

Máy xác định chặng theo thứ tự: ô khai tay trên hồ sơ món, rồi đầu mã, rồi chữ "Cấp 1" / "Cấp 2" trong tên món, cuối cùng suy từ công thức.

Kho theo chặng:
- Mọi lệnh lấy nguyên liệu từ kho Nguyên liệu của bếp.
- Bán thành phẩm làm xong nhập về kho Nguyên liệu của bếp; chỉ thành phẩm nhập kho Thành phẩm.
- Bếp không chọn kho nhập thành phẩm; chọn nhầm thì máy tự đổi và báo "Máy sửa kho đích theo chặng".

Lưu ý: hai kho BTP sơ cấp và BTP sẵn sàng của hai bếp đã tắt từ 28/08/2026, không chuyển hàng qua đó.

## Xem tồn kho theo chặng và chuyển hàng sai kho

Từ khoá: tồn kho theo chặng, tồn bán thành phẩm, hàng đang ở chặng nào, sai kho, hàng nằm sai kho, chuyển về đúng kho, tồn bếp
Ai dùng: Bếp, quản lý sản xuất, kế toán giá thành
Màn hình: Tồn kho theo chặng (/ton-kho-theo-chang)

Màn trả lời câu "hàng của bếp đang đứng ở chặng nào" (khác màn Tồn kho trả lời "kho này có gì").

Các bước:
1. Chọn bếp: "🏠 Cả hai bếp", "🎂 Pastry", "🥐 Baker".
2. Bấm chip chặng: Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm, hoặc "❓ Chưa phân chặng". Số trên chip là số mã có tồn.
3. Gõ ô tìm theo tên hoặc mã. Mỗi dòng ghi tổng tồn và tồn từng kho.
4. Chip "⚠ Sai kho" lọc ra hàng nằm ở kho khác chặng của nó (chữ đỏ "sai kho").
5. Quản lý sản xuất bấm nút "📦 Chuyển về ..." trên dòng, xác nhận từng kho. Máy lập phiếu chuyển kho NHÁP; ghi sổ phiếu trên máy tính.

Lưu ý:
- Chuyển kho hay nhập tay đưa hàng vào kho bếp sai chặng thì máy chỉ NHẮC, vẫn ghi được; hàng sẽ hiện ở chip Sai kho để chuyển về khi tiện.
- Kiểm kê thấy hàng nằm sai kho thì cứ ghi đúng thực tế, rồi chuyển về bằng phiếu chuyển.
- Chữ "làm tươi" đỏ trên dòng là bán thành phẩm làm tươi.

## Mã phantom là gì

Từ khoá: phantom, mã phantom, BTP phantom, không quản tồn, không theo dõi tồn kho, is phantom, bán thành phẩm không có tồn, vì sao không thấy tồn, nổ thẳng nguyên liệu
Ai dùng: Bếp, quản lý sản xuất, kế toán giá thành
Màn hình: Công thức (/cong-thuc), Sản xuất (/san-xuat)

Phantom là bán thành phẩm CÓ công thức nhưng KHÔNG có kho: nó sinh ra và dùng hết trong cùng một ca bếp (ví dụ lớp bột, lớp kem trộn xong đổ ngay). Phần lớn "BTP thành phần" là phantom.

Hệ quả:
- Mã phantom không có tồn kho, nên tồn luôn trống hoặc 0; đó là đúng, không phải lỗi.
- Không tạo lệnh sản xuất riêng cho mã phantom. Khi hoàn tất lệnh của món cha, máy trừ thẳng nguyên liệu của phantom.
- Không chuyển kho, không nhập kho, không kiểm kê được mã phantom.
- Ra lệnh cho mã phantom thì máy báo "Món ... không quản tồn kho, nó tự nổ trong lệnh của món cha nên không cần lệnh riêng".

Lưu ý: BTP sơ cấp (cấp 1) và BTP sẵn sàng (cấp 2) thì ngược lại, PHẢI giữ tồn vì bánh khuôn nướng hôm nay để mai ráp. Chuyển mã nào sang hay khỏi phantom là việc của quản lý sản xuất, xem hai mục tiếp theo.

## Muốn chuyển kho một mã phantom thì làm sao

Từ khoá: tắt phantom, bỏ phantom, chuyển kho mã phantom, theo dõi tồn lại, bật duy trì tồn kho, maintain stock, phantom BOM, phantom item, giữ tồn bán thành phẩm
Ai dùng: Quản lý sản xuất, kế toán giá thành
Màn hình: Desk: Item, Desk: BOM

Mã phantom không có tồn nên không chuyển kho được. Nếu thực tế bán thành phẩm đó được làm sẵn, cất trữ hoặc chuyển giữa hai bếp, phải tắt phantom để nó có tồn trở lại.

Các bước:
1. Desk, mở hồ sơ món, bật ô "Duy trì tồn kho" rồi lưu. <!-- kiểm: nhãn tiếng Việt của ô Maintain Stock; ERPNext có cho bật lại khi món đã có công thức đã ghi sổ không -->
2. Tạo phiên bản công thức MỚI cho chính món đó (màn Công thức, "🔁 Điều chỉnh"), trên Desk bỏ tick "Phantom BOM" của bản mới, rồi ghi sổ. <!-- kiểm: tên ô Is Phantom BOM trên Desk và có sửa được ở bản nháp tạo từ app không -->
3. Ở các công thức CHA đang dùng món này, tạo phiên bản mới và bỏ tick "Phantom Item" trên dòng của món, rồi ghi sổ.
4. Từ đó tạo lệnh sản xuất riêng cho món, nhập kho, chuyển kho như bán thành phẩm thường.

Lưu ý:
- Chỉ áp dụng từ nay về sau. Không sửa lại lệnh, phiếu kho đã ghi sổ.
- Làm thiếu bước 3 thì lệnh món cha vẫn trừ thẳng nguyên liệu thô, không lấy từ tồn bán thành phẩm.
- Nên báo kỹ thuật kiểm lại sau khi đổi.

## Chuyển bán thành phẩm sang phantom

Từ khoá: chuyển phantom, chuyển sang phantom, bỏ ghi sổ kho BTP, dọn chứng từ thử, đóng lệnh treo, chạy thử, chạy thật
Ai dùng: Giám đốc, quản lý hệ thống
Màn hình: Chuyển phantom (/chuyen-phantom)

Màn hàng loạt chuyển các mã "BTP thành phần" sang phantom (bỏ theo dõi tồn kho, sửa dòng công thức cha). Không có nút hoàn tác.

Các bước:
1. Mở "Dọn chứng từ thử" trước. Đóng hết lệnh sản xuất còn treo bằng nút "Đóng lệnh này" (đóng chứ không xoá, vẫn tra lại được). Mã còn tồn phải xuất hết hoặc kiểm kê về 0.
2. Khi mọi thứ xanh, bấm "Xong, sang bước chuyển Phantom".
3. Màn "Chuyển Phantom" hiện BẢN CHẠY THỬ: số mã bỏ theo dõi tồn, số dòng công thức mở nổ, số dòng chặn nổ ở C1 C2, số công thức cha phải dựng lại. Đọc kỹ cả phần "DÒNG CHƯA XỬ ĐƯỢC".
4. Bấm "Chạy thật, ghi xuống hệ", rồi "Ghi thật".

Vì sao bị chặn: khung đỏ "CHƯA CHẠY THẬT ĐƯỢC" nêu lý do (còn lệnh treo, còn tồn); bấm "Sang màn Dọn chứng từ thử" để xử lý.

Lưu ý: nên chạy ngoài giờ bếp đang làm. Việc này do anh Việt quyết.

## Soạn hướng dẫn chế biến

Từ khoá: hướng dẫn chế biến, cách làm, quy trình làm bánh, SOP món, các bước làm, tiêu chí QC, CCP, OPRP, dị ứng, ảnh món đạt, in A4
Ai dùng: Bếp trưởng, bếp phó, quản lý sản xuất
Màn hình: Hướng dẫn chế biến (/huong-dan-che-bien), hoặc nút 📖 trên thẻ công thức

Các bước:
1. Vào Công thức, bấm nút "📖" trên thẻ món (hoặc nút "📖 Hướng dẫn chế biến" trong chi tiết công thức).
2. Bấm "⬇️ Nạp từ công thức đang dùng" để kéo nguyên liệu, số lượng và ghi chú sang phần Định lượng.
3. Điền "Mẻ chuẩn và thời gian" (Mẻ chuẩn, Ra bao nhiêu thành phẩm, Chuẩn bị, Làm, Nghỉ ủ đông, Hạn sử dụng).
4. "➕ Thêm bước": ghi Công đoạn, Cách làm, Thông số, Nhiệt độ, Thời gian, Điểm tới hạn (Bước thường, OPRP, CCP).
5. "➕ Thêm tiêu chí" cho Tiêu chí QC: Không đạt khi, Không đạt thì làm gì.
6. Điền phần "Dị ứng và bảo quản". Bấm "💾 Lưu".
7. Sau khi lưu: "📷 Chụp ảnh món đạt", "🖨️ In A4".

Lưu ý:
- Trạng thái hướng dẫn: Nháp, Đang dùng, Ngừng dùng.
- Nạp lại từ công thức thay toàn bộ phần Định lượng, không đụng các bước và tiêu chí QC.
- "Lưu lại một lần rồi mới in được" / "...mới đính ảnh được".
- Nút đỏ "⚠️ Soát lại HD" nghĩa là công thức đã đổi sau khi soạn; soát rồi lưu để gỡ cảnh báo.

## Xuất nguyên liệu cho đơn tiệc

Từ khoá: đơn tiệc, tiệc, B2B, catering, teabreak, bánh thiết kế, bán sỉ, xuất nguyên liệu cho tiệc, xuất kho theo hợp đồng, giá vốn tiệc
Ai dùng: Bếp, kho, kinh doanh
Màn hình: Đơn tiệc (/don-tiec)

Gói tiệc làm theo đơn, không có công thức cố định, nên không đi qua lệnh sản xuất. Bếp xuất thẳng nguyên liệu đã dùng cho từng tiệc.

Các bước:
1. Mở màn Đơn tiệc, lọc "Sắp tới", "Tuần này" hoặc "Tất cả", chọn đơn.
2. Xem Ngày sự kiện, Giao lúc, Giá trị, Thực đơn.
3. Bấm "➕ Xuất kho nguyên liệu". Chọn Kho xuất trước.
4. Gõ ô "Tìm tên hoặc mã nguyên liệu" (chỉ hiện mã còn tồn thật), bấm "➕ Thêm", gõ số lượng theo ĐƠN VỊ KHO hiện cạnh ô, ghi chú nếu cần (vd: đợt 1).
5. Bấm "✅ Ghi sổ phiếu xuất", đọc lại số dòng và kho, bấm "Ghi sổ".

Vì sao bị chặn: "Chưa chọn kho xuất.", "Chưa có dòng nào có số lượng lớn hơn 0.", "Có dòng gõ nhiều hơn tồn kho" (kiểm lại đơn vị: mặt hàng tính bằng Kg mà gõ số gram là lệch nghìn lần).

Lưu ý: phiếu ghi thẳng vào sổ kho và sổ cái. Ghi nhầm thì huỷ phiếu (phải ghi lý do), không sửa được.

Hạch toán: Nợ 632 / Có tài khoản kho xuất, gắn theo đơn tiệc.

## Mua hàng phát sinh cho nghiên cứu phát triển

Từ khoá: nghiên cứu phát triển, R&D, RnD, làm thử món mới, test bánh, mua hàng phát sinh, hàng ngoài danh mục, mua lẻ, quỹ tạm ứng
Ai dùng: Bếp, R&D, thu mua
Màn hình: Nghiên cứu phát triển (/nghien-cuu-phat-trien), tên trên màn là "Mua hàng phát sinh"

Phiếu dành cho hàng ngoài danh mục hoặc trên 500.000 một hoá đơn, thường để test món mới: không tạo mã, không theo dõi tồn kho.

Các bước:
1. Bấm dấu cộng để tạo phiếu. Ghi "Mục đích / dự án" (bắt buộc, vd: Test bánh dứa MD2), "Ngày cần hàng", "Ghi chú chung".
2. Bấm "+ Thêm hàng cần mua": tên hàng, số lượng, link tham khảo, ảnh.
3. Bấm "Gửi yêu cầu".
4. Thu mua bấm từng dòng để ghi kết quả mua (nhà cung cấp, giá), đánh dấu "Không mua được" nếu không mua được.
5. Mua xong bấm "Hoàn thành phiếu". Kế toán bấm "Lập phiếu ghi chi phí (nháp)" để dựng hoá đơn mua nháp trả từ quỹ tạm ứng.

Vì sao bị chặn: "Chưa ghi mục đích của phiếu", "Chưa ghi tên hàng cần mua".

Lưu ý: nguyên liệu làm thử theo công thức có mã thì dùng màn Sản xuất, không dùng phiếu này. Có mua được ngoài danh mục hay không là việc anh Việt quyết. <!-- kiểm: màn R&D riêng cho làm thử công thức có tồn tại không, hay chỉ là phiếu mua hàng phát sinh -->
