# Kho

## Thu mua in sẵn phiếu nhập kho nháp từ đơn mua
Từ khoá: phiếu nhập kho nháp, lập phiếu nháp, in phiếu nhập, phiếu chờ ký, phiếu in sẵn, PNK nháp, draft purchase receipt, create purchase receipt, thu mua tạo phiếu, Đã tạo - chờ ký

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua | Desk: Đơn mua hàng | [[desk:Tạo]] |

Phiếu nhập kho nháp là tờ in sẵn để thủ kho cầm đi đếm. Phiếu này hiện ở thẻ [[Chờ nhận]] của màn Nhập kho.

**Các bước**
1. Trên Desk, mở Đơn mua hàng đã xác nhận.
2. Bấm [[desk:Tạo]], chọn [[desk:Phiếu nhập kho]]. Nhà cung cấp, món, số lượng, kho nhận tự điền.
3. Bấm [[desk:Lưu]], để ở dạng nháp, không bấm [[desk:Xác nhận]].
4. Bấm [[desk:In]], đưa tờ phiếu cho thủ kho.

**Lưu ý**
- Phiếu in khi chưa nhập có chữ PRINT chìm, có mã vạch từng món, cột số thực nhận và HSD để ghi tay, khung ký hai bên.
- Không tạo được phiếu nhập kho khi không có Đơn mua hàng.
- Không in phiếu cũng được: thủ kho nhận thẳng theo đơn ở thẻ [[Còn phải nhận]].
- Đơn đã có phiếu in sẵn thì nhận trên chính phiếu đó ở thẻ [[Chờ nhận]], để phiếu nháp không nằm lại.

## Tạo phiếu nhập kho khi nhà cung cấp giao hàng
Từ khoá: nhập kho, phiếu nhập, phiếu nhập kho, nhận hàng, nhận hàng nhà cung cấp, hàng về, PNK, purchase receipt, goods receipt, nhập mua, đếm hàng nhập

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thủ kho, Thu mua, Kế toán | Nhập kho (/nhap-kho) | [[Xác nhận nhập kho]] |

Hàng nhà cung cấp giao tới thì thủ kho đếm và nhập kho trên app theo phiếu thu mua đã in sẵn.

**Các bước**
1. Mở màn Nhập kho, chọn thẻ [[Chờ nhận]] (các thẻ khác: [[Còn phải nhận]], [[Đã nhập kho]], [[Đã huỷ]]).
2. Chọn phiếu, hoặc bấm biểu tượng máy ảnh để quét mã vạch số phiếu trên tờ in.
3. Sửa ô Số lượng thực nhận từng món theo số đếm (máy điền sẵn số còn phải nhận).
4. Đánh dấu từng món đã đếm, hoặc quét mã từng món.
5. Đính ảnh hàng đã nhận và bản scan biên bản giao nhận nếu có.
6. Bấm [[Xác nhận nhập kho]], rồi [[Nhập kho]] ở hộp xác nhận.

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Tài khoản kho nhận (152) | 3311 Phải trả người bán, hàng về chưa có hoá đơn | Khi bấm Nhập kho |

**Lưu ý**
- Xác nhận xong là phiếu khoá. Nhập sai số thì liên hệ kế toán trưởng.
- Món nhận thiếu thì phần còn lại vẫn treo trên đơn, nhận tiếp ở thẻ [[Còn phải nhận]].
- Món chưa có giá: máy lấy giá mua gần nhất, không có thì nhập giá 0 và ghi chú để kế toán bổ sung.
- Hộp "Đã nhận hàng - kiểm tra hạn dùng" chỉ là lời nhắc, không chặn. Kiểm chất lượng thật trước khi dùng.

## Nhận hàng đợt sau khi nhà cung cấp giao thiếu
Từ khoá: giao thiếu, nhận đợt 2, nhận tiếp, còn nợ hàng, còn phải nhận, giao làm nhiều đợt, giao từng phần, partial receipt, đơn mua còn thiếu, hàng về sau, nhận theo đơn

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thủ kho, Thu mua | Nhập kho (/nhap-kho), thẻ Còn phải nhận | [[Xác nhận nhận hàng đợt N]] |

Thẻ [[Còn phải nhận]] liệt kê mọi đơn mua đã xác nhận còn món chưa nhận đủ, kể cả đơn chưa có phiếu in. Đơn trễ hẹn có chip đỏ "Trễ N ngày" và đứng đầu.

**Các bước**
1. Mở Nhập kho, chọn thẻ [[Còn phải nhận]], bấm vào đơn.
2. Xem ba con số từng món: Đặt, Đã nhận, Còn lại.
3. Sửa ô Số lượng thực nhận theo số đếm (máy điền sẵn số Còn lại).
4. Đính ảnh hàng và biên bản nếu có.
5. Bấm [[Xác nhận nhận hàng đợt N]], rồi [[Nhận hàng]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Đơn ... chưa ghi sổ nên chưa nhận hàng được | Báo thu mua gửi duyệt đơn |
| Đơn ... đã huỷ, không nhận hàng vào đơn này được | Báo thu mua |
| Đơn ... đã đóng nên không nhận thêm được | Thu mua mở lại đơn |
| Trong lúc anh chị đang đếm thì ... đã được người khác nhận mất rồi | Thoát ra, mở lại đơn |

**Lưu ý**
- Mỗi đợt máy tự lập một phiếu nhập kho mới, không cần thu mua tạo phiếu nháp.
- Món đã nhận đủ bị làm mờ, không gõ được.

## Nhà cung cấp giao dư hoặc báo không giao nữa
Từ khoá: giao dư, giao thừa, nhận dư, vượt số đặt, dung sai, ngưỡng kho, over delivery, tolerance, đóng đơn, không giao nữa, hết hàng, đóng phần còn lại, huỷ phần còn lại

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thủ kho, Thu mua | Nhập kho (/nhap-kho) | [[Nhà cung cấp không giao nữa · đóng phần còn lại]] |

Giao dư trong mức dung sai thì máy cho nhận và ghi vết. Nhà cung cấp báo không giao nữa thì đóng phần còn lại của đơn.

**Các bước đóng phần còn lại**
1. Mở đơn ở thẻ [[Còn phải nhận]].
2. Bấm [[Nhà cung cấp không giao nữa · đóng phần còn lại]].
3. Ghi lý do (bắt buộc), ví dụ nhà cung cấp hết hàng.
4. Bấm [[Đóng phần còn lại]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Nhận dư quá mức cho phép | Nhận đúng số trong mức, báo thu mua lên đơn bổ sung cho phần dư |
| Nhà cung cấp giao dư ... món so với số còn phải nhận | Phiếu in sẵn chỉ nhận tới số còn lại, phần dư báo thu mua |

**Lưu ý**
- Mức dung sai (mặc định 5%) do quản lý kho hoặc kế toán đặt ở màn Ngưỡng kho, trong phân hệ Cài đặt (/phan-he-cai-dat).
- Đóng xong đơn rời thẻ Còn phải nhận. Số đã đặt giữ nguyên, mở lại được.

## Vì sao không xác nhận nhập kho được
Từ khoá: lỗi nhập kho, không nhập kho được, bị chặn nhập kho, phiếu nhập báo lỗi, không ghi được phiếu nhập, lỗi nhận hàng, quét phiếu không thấy

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thủ kho, Thu mua | Nhập kho (/nhap-kho) | [[Xác nhận nhập kho]] |

Các câu máy báo hay gặp khi nhập kho và cách gỡ.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa có món nào có số lượng, chưa nhập kho được | Gõ số thực nhận cho ít nhất một món |
| Phiếu vừa được sửa. Mở lại phiếu để lấy số liệu mới rồi nhận hàng | Thoát ra, mở lại phiếu |
| Số thực nhận phải lớn hơn 0 và không vượt phiếu nháp | Sửa lại số |
| Chỉ nhận hàng trên phiếu nháp nhập mua, không phải phiếu trả | Phiếu đang mở là phiếu trả nhà cung cấp |
| Màn nhận hàng chỉ mở cho kho, thu mua và kế toán | Báo quản lý cấp quyền Kho |
| Không thấy phiếu ... trong hệ thống (khi quét) | Mã vạch in sai hoặc phiếu chưa tạo |
| Phiếu ... đã nhập máy xong rồi | Phiếu đã ở thẻ Đã nhập kho |
| Đang có phiếu kiểm kê mở trên những mặt hàng này | Xem mục "Đang có phiếu kiểm kê mở" |

**Lưu ý**
- Phiếu đã nhập kho sai số thì không tự sửa, liên hệ kế toán trưởng.

## Nối phiếu nhập kho với hoá đơn mua
Từ khoá: nối phiếu, nối phiếu nhập kho, gắn phiếu nhập vào hoá đơn, đối chiếu hoá đơn mua, khớp hoá đơn với phiếu nhập, HDM, PNK, purchase invoice, ghi sổ hoá đơn mua, 3 way match

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua, Kế toán | Đối chiếu mua (/doi-chieu-mua) | [[Nối phiếu, chuyển kế toán ghi sổ]] |

Hàng nhập kho trước, hoá đơn về sau. Hoá đơn mua phải nối với phiếu nhập kho của đúng lô hàng thì mới ghi sổ đúng.

**Các bước**
1. Mở Đối chiếu mua, lọc nhóm Chờ đối chiếu hoặc Lệch tiền, bấm vào tờ hoá đơn.
2. Ở phần "Phiếu nhập kho của nhà cung cấp này", chạm chọn một hoặc nhiều phiếu.
3. Xem bảng so sánh từng dòng: lệch số lượng, đơn giá, đơn vị.
4. Thu mua bấm [[Nối phiếu, chuyển kế toán ghi sổ]].
5. Kế toán bấm [[Chỉ nối phiếu]] hoặc [[Khớp và ghi sổ]].

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 3311 và 1331 | 331 Phải trả người bán | Khi kế toán ghi sổ hoá đơn |

**Lưu ý**
- Không bấm [[desk:Lấy mặt hàng từ]] trên Desk: nó chép đè dòng hàng, mất dòng phí dịch vụ, phí giao hàng.
- Nên nối trên màn Đối chiếu mua. <!-- kiểm: nút "Nối phiếu nhập kho" trên Desk: dòng nhắc trên Desk nói nút chỉ gắn, không sửa số lượng và đơn giá; màn Đối chiếu mua nói nút đó chép đè giá phiếu nhập lên hoá đơn. Chưa rõ bên nào đúng -->
- Hàng không qua kho (dịch vụ, phí ship) không có phiếu nhập: kế toán bấm [[Ghi sổ thẳng, không nối phiếu]].

## Vì sao không nối được phiếu nhập kho vào hoá đơn
Từ khoá: lỗi nối phiếu, không nối được, lệch đơn vị, lệch giá hoá đơn, hoá đơn lệch phiếu nhập, chưa nối phiếu nhập, không ghi sổ được hoá đơn mua, cập nhật kho

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Thu mua, Kế toán | Đối chiếu mua (/doi-chieu-mua) | [[Nối phiếu, chuyển kế toán ghi sổ]] |

Các câu máy báo khi nối phiếu và cách gỡ.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa nối được vì lệch đơn vị | Bấm [[Đổi đơn vị dòng này thành ...]], hoặc khai đơn vị cho món để lần sau máy tự hiểu |
| Phiếu nhập đã bị hoá đơn khác lấy mất lượng | Nối lại, hoặc [[Bỏ nối, chọn lại phiếu từ đầu]] |
| Dòng N: món ... là hàng qua kho mà chưa nối phiếu nhập | Nối phiếu trước, không ghi sổ thẳng |
| Lệch so với hoá đơn điện tử của nhà cung cấp | Bấm [[Dựng lại theo hoá đơn điện tử]] nếu có nút |
| Hoá đơn ... đang bật "Cập nhật tồn kho" | Nhờ kế toán tắt ô [[desk:Cập nhật kho]] trên Desk rồi nối lại |
| Không thấy phiếu nhập kho nào | Hàng chưa nhập kho hoặc phiếu còn nháp: nhập kho trước |
| Chỉ kế toán mới ghi sổ hoá đơn mua được | Thu mua bấm [[Chỉ nối phiếu]], kế toán ghi sổ sau |

**Lưu ý**
- Giá trên hoá đơn khác giá phiếu nhập thì vẫn ghi sổ được, nhưng phải là kế toán ghi.

## Xác nhận hàng chuyển về kho tôi
Từ khoá: nhận điều chuyển, nhận hàng điều chuyển, hàng chuyển về, hàng về kho bếp, hàng về cửa hàng, xác nhận nhận hàng, nhận thiếu, kho khác chuyển sang, transfer receipt, PDC

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, Cửa hàng, người giữ kho | Hàng chuyển về kho tôi (/hang-chuyen-ve-kho-toi) | [[✓ Xác nhận nhận hàng]] |

Phiếu điều chuyển ghi sổ là hàng đã vào kho bạn trong sổ. Màn này để bạn khai số đếm thật.

**Các bước**
1. Mở Hàng chuyển về kho tôi, chọn [[7 ngày]], [[14 ngày]] hoặc [[30 ngày]].
2. Bấm vào một phiếu để xem hàng.
3. Bấm [[✓ Xác nhận nhận hàng]].
4. Dòng nào lệch thì gõ số đếm thật và ghi chú. Đủ thì giữ nguyên.
5. Bấm [[Xác nhận đã nhận]], rồi [[Xác nhận]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Tài khoản của bạn chưa khai Kho phụ trách | Báo anh Việt khai ở màn Người dùng |
| Phiếu này chuyển về kho ..., không phải kho bạn phụ trách | Người giữ kho nhận xác nhận |

**Lưu ý**
- Màn này KHÔNG sửa tồn. Phần nhận thiếu thành việc cần làm cho thủ kho đối chiếu.
- Đã xác nhận thì không xác nhận đè. Khai sai thì báo thủ kho.
- Hàng xin bằng Yêu cầu điều chuyển nội bộ (phân hệ Đặt hàng, /phan-he-dat-hang): mở phiếu, bấm [[Đã nhận hàng]]. Bước này trừ kho xuất và cộng kho nhận thật.

## Xuất điều chuyển hàng sang kho khác
Từ khoá: điều chuyển, chuyển kho, xuất chuyển, chuyển hàng sang bếp, chuyển bánh ra cửa hàng, chuyển nguyên liệu, material transfer, stock transfer, PDC, chuyển nội bộ

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kho, Bếp, Cửa hàng | Xuất điều chuyển (/xuat-dieu-chuyen) | [[Ghi sổ phiếu chuyển]] |

Chuyển hàng từ kho này sang kho khác. Phiếu ghi sổ ngay.

**Các bước**
1. Mở Xuất điều chuyển, bấm nút +.
2. Chuyển theo phiếu yêu cầu thì chọn ở ô "Theo phiếu yêu cầu điều chuyển", máy tự điền.
3. Chọn Kho xuất và Kho nhận.
4. Bấm [[+ Thêm hàng]], chọn món (chỉ hiện mã còn tồn ở kho xuất), sửa số lượng.
5. Ghi chú nếu cần, bấm [[Ghi sổ phiếu chuyển]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phải chọn cả kho xuất và kho nhận | Chọn đủ hai kho |
| Kho xuất và kho nhận không được trùng nhau | Chọn lại kho nhận |
| Số lượng xuất vượt quá tồn kho: ... | Sửa số, hoặc xem tồn ở màn Tồn kho |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Tài khoản kho nhận | Tài khoản kho xuất | Khi ghi sổ, chỉ khi hai kho khác tài khoản |

**Lưu ý**
- Kho nhận vẫn phải đếm và xác nhận ở màn Hàng chuyển về kho tôi.
- Đổi kho xuất thì phải chọn lại hàng.
- Phiếu đã ghi sổ có nút [[Lập vận đơn giao hàng này]] để phân công shipper.

## Xuất huỷ hàng hỏng, hết hạn
Từ khoá: xuất huỷ, huỷ hàng, bỏ hàng, hàng hỏng, hàng hết hạn, hàng vỡ, bánh trưng bày hết ngày, thất thoát, write off, scrap, material issue, PXD

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Người giữ kho lập, Quản lý kho ghi sổ | Xuất huỷ (/xuat-huy) | [[Lưu phiếu, chờ quản lý ghi sổ]] |

Hàng hỏng thật, hết hạn, thất thoát thì lập phiếu xuất huỷ. Tồn chỉ trừ khi quản lý kho ghi sổ.

**Các bước**
1. Mở Xuất huỷ, bấm nút +.
2. Chọn Kho xuất.
3. Chọn Lý do huỷ: Hỏng, vỡ trong quá trình làm; Hết hạn sử dụng; Không đạt chất lượng; Mẫu thử, nếm, chụp hình; Bánh trưng bày hết ngày; Thất thoát chưa rõ nguyên nhân; Khác.
4. Chụp ảnh chứng minh (bắt buộc).
5. Bấm [[+ Thêm hàng]], chọn món, sửa số lượng.
6. Bấm [[Lưu phiếu, chờ quản lý ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa chọn kho xuất / Chưa chọn lý do huỷ | Chọn đủ |
| Phiếu xuất huỷ bắt buộc có ảnh chứng minh | Chụp ảnh |
| Số lượng xuất vượt quá tồn kho | Sửa số |
| Chỉ quản lý kho mới được ghi sổ phiếu xuất huỷ | Nhờ quản lý kho |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 632 Giá vốn hàng bán | Tài khoản kho xuất | Khi quản lý ghi sổ |

**Lưu ý**
- Hao hụt ngoài định mức kế toán chuyển tay sang 811.
- Bánh chụp ảnh, mời khách, ăn ca thì dùng Xuất dùng nội bộ.
- Phiếu điều chuyển đã ghi sổ có nút [[Xuất huỷ hàng này tại ...]] cho hàng nhận về không bán được.

## Xuất dùng nội bộ: chụp ảnh, mẫu thử, mời khách, ăn ca
Từ khoá: xuất dùng nội bộ, xuất dùng, xuất cho marketing, bánh chụp ảnh, mẫu thử, nếm thử, R&D, mời khách, tặng đối tác, nhân viên ăn ca, đào tạo, internal use, PXD

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Marketing, Bếp, Lab, Cửa hàng; Quản lý kho ghi sổ | Xuất dùng nội bộ (/xuat-dung-noi-bo) | [[Lưu phiếu, chờ quản lý ghi sổ]] |

Hàng ra khỏi kho mà tiệm vẫn dùng. Tồn chỉ trừ khi quản lý kho ghi sổ.

**Các bước**
1. Mở Xuất dùng nội bộ, bấm nút +.
2. Chọn kho xuất.
3. Chọn Mục đích: Marketing chụp ảnh, quay phim; Mẫu thử, nghiên cứu công thức; Mời khách, tặng đối tác; Nhân viên ăn ca; Đào tạo, huấn luyện; Việc nội bộ khác.
4. Chọn Bộ phận chịu chi phí (máy gợi ý theo mục đích).
5. Bấm [[+ Thêm hàng]], chọn món, gõ số lượng.
6. Ghi chú, bấm [[Lưu phiếu, chờ quản lý ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa chọn mục đích xuất dùng / Chưa chọn bộ phận chịu chi phí | Chọn đủ |
| Có ... món vượt tồn | Sửa số |
| Bộ phận ... chưa có trong hệ thống | Báo anh Việt |
| Chỉ quản lý kho mới được ghi sổ phiếu xuất dùng nội bộ | Nhờ quản lý kho |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Marketing 641x; mẫu thử, đào tạo 627x; mời khách, ăn ca, việc khác 642x | Tài khoản kho xuất | Khi quản lý ghi sổ |

**Lưu ý**
- Chọn "Việc nội bộ khác" thì ghi rõ ở Ghi chú. Ảnh không bắt buộc.

## Xuất kho phục vụ bán hàng: chốt bao bì, nguyên liệu tại điểm bán
Từ khoá: xuất kho phục vụ bán hàng, chốt kho điểm bán, chốt bao bì, xuất bao bì, túi hộp ly, nguyên liệu pha chế, đếm còn lại, xuất dùng cửa hàng, công cụ dụng cụ quầy, văn phòng phẩm, PXD

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Cửa hàng, Sales Online | Xuất kho phục vụ bán hàng (/xuat-kho-phuc-vu-ban-hang) | [[Ghi sổ phiếu xuất]] |

Màn này là bảng đếm: bạn gõ số CÒN LẠI của từng mã, máy tự tính số đã dùng và trừ kho.

**Các bước**
1. Mở màn, bấm nút + ([[Chốt kho điểm bán]]).
2. Chọn kho và Bộ phận chịu chi phí.
3. Ở mục Đếm còn lại, gõ số còn lại từng mã đã đếm. Mã chưa đếm thì bỏ trống.
4. Ghi chú (ví dụ chốt tuần 38), bấm [[Ghi sổ phiếu xuất]], rồi [[Ghi sổ]].

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 641x (bao bì, công cụ dụng cụ, văn phòng phẩm) | Tài khoản kho | Khi bấm Ghi sổ |
| 632 (nguyên liệu, bán thành phẩm) | Tài khoản kho | Khi bấm Ghi sổ |

**Lưu ý**
- Bấm là tồn trừ ngay, không chờ kế toán.
- Bánh và đồ uống thành phẩm không có trong bảng vì đã trừ kho theo hoá đơn bán. Khai ở đây là trừ hai lần.
- Dòng số còn lại lớn hơn tồn bị tô đỏ, sửa trước khi lưu.

## Xuất trả hàng cho nhà cung cấp
Từ khoá: trả hàng nhà cung cấp, trả NCC, hàng lỗi trả lại, trả hàng hư, giao sai hàng, purchase return, return to supplier, giảm công nợ, phiếu trả hàng, PNK-TRA

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kho, Thu mua, Kế toán | Xuất trả nhà cung cấp (/xuat-tra-nha-cung-cap) | [[Lưu và ghi sổ phiếu trả]] |

Trả hàng lỗi, giao sai về nhà cung cấp, neo vào phiếu nhập gốc để hoàn đúng giá đã nhập.

**Các bước**
1. Mở màn, bấm nút +.
2. Chọn Nhà cung cấp (chỉ hiện nhà cung cấp có phiếu nhập trong 90 ngày).
3. Chọn Phiếu nhập gốc.
4. Chọn Lý do trả.
5. Gõ số lượng trả từng món (máy hiện số còn trả được).
6. Bấm [[Lưu và ghi sổ phiếu trả]], rồi [[Ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phiếu nhập ... chưa ghi sổ nên chưa trả hàng theo nó được | Nhập kho phiếu gốc trước |
| Số trả vượt quá số còn trả được | Mở lại phiếu lấy số mới nhất |
| Màn trả hàng nhà cung cấp chỉ mở cho kho, thu mua và kế toán | Báo quản lý cấp quyền |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 3311 | Tài khoản kho | Khi ghi sổ, ngược phiếu nhập gốc |

<!-- kiểm: phiếu gốc đã có hoá đơn mua ghi sổ thì kế toán xử lý phần công nợ thế nào (hoá đơn trả hàng HDM-TRA hay cách khác), nguồn chưa nói -->

**Lưu ý**
- Phiếu ghi sổ ngay, tồn giảm cùng lúc. Không dùng Xuất huỷ cho hàng trả nhà cung cấp.

## Xuất bán sỉ, lập phiếu giao hàng cho khách doanh nghiệp
Từ khoá: xuất bán sỉ, bán sỉ, wholesale, giao hàng khách doanh nghiệp, phiếu giao hàng, delivery note, giao đơn sỉ, PGH, biên bản giao nhận, trừ kho hai lần

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Sales, Kho, Kế toán | Xuất bán sỉ (/xuat-ban-si) | [[Lưu và ghi sổ phiếu giao]] |

Phiếu giao hàng cho khách sỉ trừ kho thật và ghi giá vốn ngay khi ghi sổ.

**Các bước**
1. Mở Xuất bán sỉ, bấm nút +.
2. Đọc khung cảnh báo vàng ở đầu màn.
3. Chọn Khách hàng và kho xuất.
4. Bấm [[+ Thêm hàng]], chọn món, gõ số lượng.
5. Ghi Người nhận hàng (người ký nhận bên khách) và Ghi chú.
6. Bấm [[Lưu và ghi sổ phiếu giao]], rồi [[Ghi sổ]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chưa chọn khách hàng / Chưa chọn kho xuất | Chọn đủ |
| Có ... món vượt tồn | Sửa số |
| Màn xuất bán sỉ chỉ mở cho Sales, kho và kế toán | Báo quản lý cấp quyền |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 632 Giá vốn hàng bán | Tài khoản kho xuất | Khi ghi sổ phiếu giao |

**Lưu ý**
- Hoá đơn của đơn sỉ phải lập từ chính phiếu giao này (trên Desk mở phiếu, bấm [[desk:Tạo]], chọn [[desk:Hóa đơn bán hàng]]). Hoá đơn nối với phiếu giao thì máy không trừ kho lần hai.
- Hoá đơn lập rời, không nối phiếu giao, thì từ 01/10/2026 máy coi như bán thường và có thể trừ kho lần nữa. Gặp tờ như vậy báo kế toán.
- Hoá đơn trộn dòng lấy từ phiếu giao với dòng gõ thêm thì dòng gõ thêm không trừ kho, tờ hiện "Chưa trừ kho" để kế toán xử lý.

## Ghi sổ hoặc bỏ phiếu xuất đang chờ
Từ khoá: ghi sổ phiếu xuất, duyệt phiếu xuất huỷ, duyệt xuất dùng, phiếu chờ ghi sổ, bỏ phiếu, huỷ phiếu nháp, xoá phiếu xuất, lập nhầm phiếu

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý kho ghi sổ; người lập bỏ phiếu | Xuất huỷ (/xuat-huy), Xuất dùng nội bộ (/xuat-dung-noi-bo) | [[Ghi sổ phiếu này]] |

Phiếu xuất huỷ và xuất dùng nội bộ nằm ở thẻ Chờ ghi sổ cho tới khi quản lý kho ghi sổ hoặc người lập bỏ phiếu.

**Các bước ghi sổ**
1. Mở màn, chọn thẻ Chờ ghi sổ, bấm vào phiếu.
2. Xem kho, lý do hoặc mục đích, ảnh, danh sách hàng.
3. Bấm [[Ghi sổ phiếu này]]. Tồn trừ thật.

**Các bước bỏ phiếu lập sai**
1. Mở phiếu đang chờ, bấm [[Bỏ phiếu này]].
2. Ghi lý do (lập nhầm, sai kho, sai số lượng), xác nhận.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Phiếu này đã bỏ nên không ghi sổ được | Lập phiếu mới |
| Phiếu này không còn ở trạng thái bản nháp | Phiếu đã ghi sổ hoặc đã bỏ |
| Chỉ người tạo phiếu hoặc quản lý kho mới bỏ được phiếu này | Nhờ người lập hoặc quản lý kho |
| Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính | Liên hệ kế toán trưởng |

**Lưu ý**
- Phiếu bỏ không bị xoá, vẫn nằm trong danh sách để tra.
- Ảnh gỡ được (nút ✕ góc ảnh) khi phiếu chưa ghi sổ.

## Kiểm kê kho: tạo phiếu và đếm hàng
Từ khoá: kiểm kê, kiểm kho, đếm kho, đếm hàng tồn, phiếu kiểm kê, stock take, stocktake, inventory count, KK, kiểm tồn cuối tháng, đếm mù

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kho, Bếp, Cửa hàng, Kiểm kê viên | Kiểm kê (/kiem-ke) | [[Chốt phiếu]] |

Mỗi phiếu kiểm kê là một kho, một nhóm hàng. Phiếu tự lưu nên đếm được nhiều buổi.

**Các bước**
1. Mở Kiểm kê, bấm dấu +.
2. Chọn Ngày kiểm, Kho kiểm, Nhóm hàng kiểm, Vị trí kiểm nếu kho chia tủ.
3. Bấm [[Bắt đầu kiểm]].
4. Bấm [[Quét mã vạch liên tục]], hoặc gõ tên món rồi bấm + để thêm. Nhập số đếm.
5. Bấm [[Lưu lại]] giữa chừng. Đếm xong bấm [[Chốt phiếu]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Tài khoản của bạn chưa được cấp quyền kiểm kê | Báo quản lý cấp quyền |
| Kho này đang có phiếu kiểm dở | Mở phiếu đó đếm tiếp, tránh đếm trùng |

**Lưu ý**
- Người đếm không thấy tồn trên máy (đếm mù), cứ ghi đúng số đếm.
- Món trong nhóm mà chưa đếm thì không ghi vào sổ, tồn giữ nguyên.
- Kho tổng 307 chỉ bộ phận Kho tổng 307 chốt số.
- Chốt rồi vẫn bấm [[Mở lại để sửa]] được. Lập nhầm thì bấm [[Huỷ phiếu kiểm kê này]].

## Ghi sổ phiếu kiểm kê và chọn lý do chênh lệch
Từ khoá: ghi sổ kiểm kê, chốt kiểm kê, điều chỉnh tồn, lý do chênh lệch, lệch tồn, hao hụt, stock reconciliation, PKK, giá vốn kiểm kê, tồn đầu kỳ, opening stock

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Quản lý kho, Giám đốc | Kiểm kê (/kiem-ke) | [[Ghi sổ vào phần mềm]] |

Ghi sổ là lúc tồn trên máy đổi theo số đếm. Máy lập phiếu điều chỉnh tồn (mã PKK) và nộp luôn.

**Các bước**
1. Mở phiếu đã chốt, bấm [[Ghi sổ vào phần mềm]].
2. Chọn Kiểu ghi sổ: Điều chỉnh tồn (kiểm kê định kỳ) hoặc Tồn đầu kỳ (lần đầu đưa số lên máy).
3. Kiểm tra Tài khoản đối ứng chênh lệch và Trung tâm chi phí.
4. Mục Cần điền giá vốn: gõ giá mua 1 đơn vị (chưa VAT) cho món máy chưa biết giá.
5. Mục Lệch so với máy: chọn lý do cho từng món lệch.
6. Bấm [[Tạo phiếu điều chỉnh và nộp]], rồi [[Ghi sổ ngay]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Còn ... món chưa có giá vốn | Điền giá ở mục Cần điền giá vốn |
| Còn ... món lệch chưa chọn lý do | Chọn đủ lý do |
| Chọn tài khoản đối ứng chênh lệch trước đã | Chọn tài khoản |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| Tài khoản kho (thừa) hoặc tài khoản đối ứng (thiếu) | Bên còn lại | Khi Ghi sổ ngay |

Tài khoản đối ứng máy điền sẵn tài khoản chênh lệch mặc định của công ty; Tồn đầu kỳ dùng tài khoản tạm đầu kỳ. <!-- kiểm: số tài khoản chênh lệch mặc định: dòng nhắc trên màn ghi 811, ghi chép 25/08 dùng 6328, ghi chép 01/10 ghi 632. Kế toán chốt -->

**Lưu ý**
- Ghi sổ xong không sửa bằng app được. Sai thì liên hệ kế toán trưởng.
- Lý do lệch: thiếu hàng chọn lý do bên thiếu, thừa chọn bên thừa.

## Vì sao bị chặn "Đang có phiếu kiểm kê mở trên những mặt hàng này"
Từ khoá: phiếu kiểm kê đang mở, khoá kiểm kê, không ghi sổ được vì đang kiểm, bị khoá mã hàng, đang đếm kho, freeze

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Kiểm kê (/kiem-ke) | [[Ghi sổ vào phần mềm]] |

Phiếu kiểm kê ở trạng thái Đang kiểm, Chờ duyệt hoặc Đã chốt sẽ khoá các mã trong phiếu ở đúng kho đó. Nhập, xuất, điều chuyển chạm mã đó bị chặn, câu báo kèm tên món và kho.

**Các bước gỡ**
1. Mở Kiểm kê, tìm phiếu của kho đó đang kiểm dở hoặc đã chốt.
2. Đếm xong, nhờ quản lý ghi sổ phiếu kiểm. Lập nhầm thì huỷ phiếu.
3. Quay lại lưu chứng từ, lúc này lưu được ngay.

**Lưu ý**
- Khoá chỉ hiệu lực trong 2 ngày kể từ ngày kiểm.
- Lý do khoá: ghi sổ lúc đang đếm thì số chênh lệch không còn đúng với thời điểm nào.

## Tra tồn kho
Từ khoá: tồn kho, xem tồn, tra tồn, còn bao nhiêu, kho còn hàng không, stock, stock balance, inventory, tồn âm, cận hạn, giá trị tồn

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Tồn kho (/ton-kho) | Ô Kho |

Xem mỗi món còn bao nhiêu ở từng kho.

**Các bước**
1. Mở Tồn kho, bấm ô Kho để chọn kho.
2. Gõ tên hoặc mã hàng, hoặc quét mã vạch.
3. Lọc bằng chip nhóm hàng; chip Cận hạn và Tồn âm hiện khi có.
4. Bấm vào một món để xem tồn theo từng kho và các lô còn hàng.

**Lưu ý**
- Dòng tóm tắt cho biết số mã và tổng của bộ lọc đang chọn.
- Giá trị tồn chỉ hiện với người được xem giá.
- Danh sách dài thì gõ ô tìm để thu hẹp.
- Muốn biết hàng bếp đang ở chặng nào thì dùng Tồn kho theo chặng.

## Tồn kho theo chặng và hàng nằm sai kho
Từ khoá: tồn theo chặng, chặng, nguyên liệu, bán thành phẩm, BTP sơ cấp, BTP sẵn sàng, thành phẩm, sai kho, chuyển về đúng kho, chưa phân chặng, tồn bếp

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Bếp, Kế toán giá thành, Kho | Tồn kho theo chặng (/ton-kho-theo-chang) | [[Lập phiếu nháp]] |

Màn này cho biết hàng của bếp đang ở chặng nào: Nguyên liệu, BTP sơ cấp, BTP sẵn sàng, Thành phẩm.

**Các bước**
1. Mở Tồn kho theo chặng, chọn bếp: Cả hai bếp, Pastry hoặc Baker.
2. Bấm chip chặng để lọc; chip Chưa phân chặng là món chưa gắn chặng.
3. Chip Sai kho liệt kê món nằm ở kho không đúng chặng.
4. Ở món sai kho, bấm [[Chuyển về ...]], rồi [[Lập phiếu nháp]].

**Lưu ý**
- Phiếu chuyển lập ra là NHÁP, chuyển hết số nằm sai. Quản lý xem lại trên máy tính rồi mới ghi sổ.
- Máy chỉ nhắc, không chặn hàng nằm sai kho.

## Hoá đơn chưa trừ kho và trừ bù
Từ khoá: hoá đơn chưa trừ kho, chưa trừ kho, trừ bù, trừ kho bù, trừ kho sau, bán khi kho chưa có hàng, đã trừ một phần, phiếu bù, giá vốn hoá đơn bán

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kế toán, Quản lý cửa hàng, Giám đốc (Sales chỉ xem) | Hoá đơn chưa trừ kho (/hoa-don-chua-tru-kho) | [[Trừ bù]] |

Hoá đơn bán lúc kho điểm bán chưa có hàng vẫn ghi sổ doanh thu. Máy trừ ngay món đang có; món còn thiếu tự trừ bù khi hàng về kho điểm bán, và quét lại mỗi giờ.

**Các bước trừ bù tay**
1. Mở Hoá đơn chưa trừ kho, lọc theo điểm bán, khoảng ngày, chip trạng thái.
2. Chip [[Kho đủ để trừ bù]] là hoá đơn trừ được ngay.
3. Bấm [[Trừ bù]] trên từng hoá đơn, hoặc [[Trừ bù cả điểm này]].

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Chỉ kế toán, quản lý cửa hàng hoặc giám đốc được bấm trừ bù | Nhờ người có quyền |
| Điểm bán ... chưa khai kho xuất | Báo anh Việt khai kho cho điểm bán |
| Chưa trừ bù được | Kho chưa đủ hàng, chờ hàng về |

**Hạch toán**
| Nợ | Có | Khi nào |
|---|---|---|
| 632 Giá vốn hàng bán | Tài khoản kho điểm bán | Mỗi lần trừ bù (máy lập phiếu PXD gắn hoá đơn) |

**Lưu ý**
- Chip trạng thái: Chưa trừ kho, Đã trừ một phần, Đã trừ bù, Phiếu bù bị gỡ tay. Chip tồn: Kho đủ để trừ bù, Kho đủ một phần, Kho chưa có hàng.
- Trang đặt bánh web không trừ thêm lần nữa vì đã giữ hàng lúc lưu hoá đơn.

## Lô hàng và hạn sử dụng khi nhập, xuất kho
Từ khoá: lô, lô hàng, batch, mẻ, quản lý theo mẻ, hạn sử dụng, HSD, hết hạn, cận hạn, FEFO, gói số seri và lô, lô quá hạn, hạn dùng tối thiểu

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Kho, Bếp, Kế toán | Nhập kho (/nhap-kho), Tồn kho (/ton-kho) | Không có |

Từ 30/09/2026 tiệm tắt quản lý theo lô cho toàn bộ mã hàng. Nhập, xuất, sản xuất, kiểm kê không cần chọn lô.

**Lưu ý**
- Màn Nhập kho chỉ hiện ô Hạn sử dụng cho món còn quản lý theo lô.
- Tồn cũ ở các lô cũ coi là tồn chung của mã. Chứng từ cũ có lô giữ nguyên.
- Huỷ chứng từ cũ có lô có thể báo lỗi: liên hệ kế toán trưởng.
- Còn gặp câu "Vui lòng thêm Gói Số seri và Lô" thì mã đó vẫn bật lô: báo anh Việt hoặc kế toán, không tự sửa.
- Hạn dùng ngắn hoặc quá hạn lúc nhận chỉ bị nhắc, không chặn.
- Bật lại lô cho mã nào do anh Việt quyết.

## Cây kho: kho nào dùng cho việc gì
Từ khoá: cây kho, danh sách kho, kho nào, kho tổng 307, kho D1, kho NVHTN, kho Sales Online, kho bếp, kho nguyên liệu bếp, kho thành phẩm, kho Lab, kho phụ trách, warehouse

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Kho hàng (/tra-cuu-kho-hang) | Không có |

Mỗi kho trên máy ứng với một nơi giữ hàng thật.

| Kho | Dùng cho |
|---|---|
| Kho tổng 307 (307/1 Nguyễn Văn Trỗi) | Nguyên liệu mua về, bộ phận kho giữ |
| Pastry, Baker: Nguyên liệu | Nguyên liệu và bán thành phẩm của bếp; lệnh sản xuất rút từ đây |
| Pastry, Baker: Thành phẩm | Bánh làm xong |
| Kho Lab | Bếp nghiên cứu Sonneto Lab |
| Kho D1 (9 Trần Cao Vân), Kho NVHTN (21 Phạm Ngọc Thạch), Kho Sales Online | Kho điểm bán, bánh từ kho Thành phẩm chuyển ra |

**Lưu ý**
- Hai kho BTP sơ cấp và BTP sẵn sàng đã tắt từ 28/08/2026.
- Mỗi tài khoản có ô Kho phụ trách. Cần thêm kho thì báo anh Việt khai ở màn Người dùng.
- Máy không chặn chuyển hàng giữa các kho, chỉ nhắc khi hàng nằm sai chặng.

## Mã chứng từ kho: PNK, PDC, PXD, PKK là gì
Từ khoá: mã phiếu, mã chứng từ, số phiếu, PNK, PNK-TRA, PDC, PXD, PKK, PSX, KK, YCDC, YCXD, DMH, HDM, PGH, HDB, tiền tố phiếu, naming series, MAT-STE

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Mọi màn kho | Không có |

Mã có dạng MÃ-NĂM-SỐ, ví dụ PNK-2026-00054. Nhìn tiền tố là biết loại phiếu.

| Mã | Phiếu |
|---|---|
| DMH | Đơn mua hàng |
| PNK | Phiếu nhập kho mua hàng |
| PNK-TRA | Phiếu trả hàng nhà cung cấp |
| HDM | Hoá đơn mua |
| YCDC / YCXD | Yêu cầu điều chuyển / Yêu cầu xuất dùng |
| PDC | Phiếu điều chuyển kho |
| PXD | Phiếu xuất dùng: xuất huỷ, xuất dùng nội bộ, xuất phục vụ bán hàng, phiếu trừ bù |
| PSX | Phiếu sản xuất |
| KK | Phiếu kiểm kê trên app (phiếu đếm) |
| PKK | Phiếu điều chỉnh tồn khi ghi sổ kiểm kê |
| PGH | Phiếu giao hàng (xuất bán sỉ); trên Desk gọi là Phiếu xuất kho |
| HDB | Hoá đơn bán |

**Lưu ý**
- Phiếu tạo trước 03/08/2026 còn mang mã cũ của ERPNext (MAT-STE, MAT-PRE...), vẫn dùng bình thường.
- Xuất huỷ và xuất dùng cùng mã PXD; phân biệt bằng màn đã lập phiếu.

## Các câu chặn hay gặp khi ghi sổ phiếu kho
Từ khoá: lỗi ghi sổ phiếu kho, thiếu hàng, không đủ hàng, tồn âm, vượt tồn, thiếu lô, tài khoản chi phí, không có quyền xuất kho, lỗi phiếu xuất

| Ai dùng | Màn hình | Nút chính |
|---|---|---|
| Mọi bộ phận | Các màn Xuất kho, Nhập kho, Kiểm kê | Không có |

Tiệm không cho tồn âm, nên mọi phiếu kho đều kiểm tồn trước khi ghi sổ.

**Vì sao bị chặn**
| Máy báo | Cách gỡ |
|---|---|
| Số lượng xuất vượt quá tồn kho: mã (tồn ..., xuất ...) | Sửa số, chuyển hàng về kho này trước, hoặc kiểm kê lại |
| Kho ... không đủ ... để trừ: còn thiếu ... | Câu báo nói kho nào còn mã đó, chuyển phần thiếu rồi bấm lại |
| Đang có phiếu kiểm kê mở trên những mặt hàng này | Xem mục "Đang có phiếu kiểm kê mở" |
| Vui lòng thêm Gói Số seri và Lô | Mã vẫn bật lô, báo anh Việt hoặc kế toán |
| Chưa có tài khoản chi phí nào để ghi giá trị hàng huỷ, nhờ kế toán khai thêm | Báo kế toán |
| Tài khoản của bạn chưa được cấp quyền xuất kho | Báo quản lý cấp quyền |
| Kho này không nằm trong các kho bạn phụ trách | Báo anh Việt khai Kho phụ trách |
| Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính | Liên hệ kế toán trưởng |
| Phiếu chưa có dòng hàng nào có số lượng lớn hơn 0 | Gõ số lượng cho ít nhất một dòng |
