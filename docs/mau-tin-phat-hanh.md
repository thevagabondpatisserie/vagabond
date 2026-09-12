# Mẫu tin nghiệm thu sau deploy (gửi các bộ phận)

Áp dụng cho MỌI biên nhận `[ĐÃ DEPLOY]` và khối `telegram-release` (xem
docs/thong-bao-telegram.md). Người đọc là nhân viên quầy, kế toán, bếp và anh
Việt, không phải lập trình viên. Viết xong tự đọc lại bằng mắt của thu ngân:
chỗ nào phải mở code mới hiểu thì viết lại.

## Khung bắt buộc

```
Vagabond | Bản vNNN | <ngày> | đã lên site thật

MỘT CÂU cho anh Việt: bản này giải quyết chuyện gì (nghiệp vụ, không kỹ thuật).

[Quầy / Sales]
- Trước đây: ... Từ nay: ... Bạn cần làm: ...

[Kế toán]
- Trước đây: ... Từ nay: ... Bạn cần làm: ...

[Bếp / Kho]   (bỏ khối nếu không liên quan)
- ...

VIỆC CẦN LÀM NGAY (tên người - việc - hạn)
- ...

ĐÃ KIỂM TRÊN SITE THẬT
- Màn <tên màn trên app>: <thấy gì, số bao nhiêu>.
- Patch Log ghi vNNN. Doctype <X> đã có trường <Y>.

CÒN TỒN (chưa làm trong bản này)
- ...

Kỹ thuật: PR #..., SHA ..., issue #...   (một dòng, để cuối)
```

## Quy tắc viết

1. Mỗi ý là một câu ngắn theo mẫu "Trước đây / Từ nay / Bạn cần làm". Không
   có "Bạn cần làm" thì ghi "Không cần làm gì thêm".
2. Gọi đúng tên màn hình và nút như trên app: "màn Doanh thu Sales", "nút
   Ghi sổ hoá đơn bán hàng", "màn Đơn còn treo". Không ghi tên hàm, tên
   trường, tên tệp, tên nhánh, tên hook, tên doctype trong phần cho bộ phận.
3. Tối đa 6 gạch đầu dòng mỗi bộ phận. Mỗi dòng dưới 220 ký tự.
4. Công tắc, cấu hình mặc định: ghi rõ đang BẬT hay TẮT, ai được đổi, đổi ở
   đâu, và đổi rồi thì hậu quả nghiệp vụ là gì.
5. Phần "Đã kiểm trên site thật" phải là việc mắt đã thấy: tên màn, con số,
   số phiên bản trong Patch Log. Cấm viết "theo xác nhận phát hành", "CI
   xanh", "merge thành công" thay cho kiểm site.
6. Phần "Còn tồn" liệt kê thật những gì bản này chưa sửa, kể cả lỗi mình biết
   mà chưa có PR. Không có thì ghi "Không".
7. Không kể log, số hoá đơn, tên khách, dữ liệu cá nhân, bí mật.
8. Không dùng dấu em dash hay en dash, chỉ dùng dấu gạch ngang thường.
9. Không đề xuất sửa dữ liệu quá khứ đã ghi sổ hay đã phát hành hoá đơn.
10. Khối `telegram-release`: `features` lấy từ các dòng "Từ nay" ở trên, mỗi
    dòng một tính năng, 1 tới 5 dòng, bỏ phần kỹ thuật.

## Ví dụ hoàn chỉnh: bản v486 (12/09/2026)

```
Vagabond | Bản v486 | 12/09/2026 | đã lên site thật

Bản này sửa nhóm lỗi làm hoá đơn ngày 11/09 bị kẹt và làm đơn tặng không ghi
sổ được. Từ nay một đơn kẹt không kéo cả ngày kẹt theo.

[Quầy / Sales]
- Trước đây: một đơn lỗi làm cả ngày không phát hành hoá đơn được. Từ nay:
  chỉ đơn lỗi bị giữ lại, các đơn còn lại vẫn ghi sổ và xuất hoá đơn bình
  thường. Bạn cần làm: cuối ngày mở màn Đơn còn treo, xử từng đơn kẹt.
- Trước đây: nút Ghi sổ hoá đơn bán hàng ở màn Doanh thu Sales chỉ gom đơn
  Pancake. Từ nay: nút này gom cả bill quầy. Bạn cần làm: bấm một lần là đủ.
- Trước đây: lý do hàng tặng bị mất khi đơn đồng bộ lại từ Pancake. Từ nay:
  lý do được giữ. Bạn cần làm: nhập lý do đủ 5 ký tự trước khi gửi duyệt.
- Trước đây: đơn tặng bị từ chối rồi gửi duyệt lại vẫn hiện "Đã từ chối". Từ
  nay: gửi duyệt lại thì về "Chờ duyệt". Không cần làm gì thêm.
- Trước đây: chọn món combo chưa khai báo thì báo lỗi lúc ghi sổ, không hiểu
  vì sao. Từ nay: màn chọn món báo ngay lý do. Bạn cần làm: báo kế toán khai
  báo combo trước khi bán.
- Màn Đơn còn treo từ nay chỉ hiện đơn của các ngày trước, đơn hôm nay không
  hiện để khỏi loãng.

[Kế toán]
- Trước đây: đơn tặng bị trừ kho điểm bán, kho chưa có hàng nên không ghi sổ
  được. Từ nay: có công tắc "Hàng tặng xuất kho thật" trong Vagabond Settings,
  mặc định TẮT, nghĩa là đơn tặng ghi sổ không trừ kho. Bạn cần làm: giữ TẮT
  cho tới khi bếp làm lệnh sản xuất đủ, muốn bật thì báo anh Việt.
- Trước đây: đơn có cọc phải tự nhớ cấn. Từ nay: hệ thống nhắc kế toán khi
  ghi sổ đơn còn cọc chưa cấn. Bạn cần làm: xem nhắc, cấn cọc rồi mới ghi sổ.

VIỆC CẦN LÀM NGAY
- Loan Anh: sáng 13/09 mở màn Doanh thu Sales, bấm Ghi sổ hoá đơn bán hàng
  cho 7 đơn tặng còn treo của ngày 12/09.
- Kế toán: khai báo các combo đang bán trong Khuyến mãi, kiểm lại danh sách
  combo chưa có mã.

ĐÃ KIỂM TRÊN SITE THẬT
- Patch Log ghi v486. Vagabond Settings có công tắc Hàng tặng xuất kho thật,
  đang TẮT.
- Màn Đơn còn treo: không còn đơn ngày 12/09, chỉ hiện ngày cũ.
- Màn Doanh thu Sales ngày 12/09: 195 đơn đã ghi sổ, 191 đã có hoá đơn, 4 đơn
  tặng chờ ghi sổ sáng mai.

CÒN TỒN
- Chốt ca mới cấn trừ SePay cho bill quầy, đơn Pancake chuyển khoản chưa đối
  chiếu được (issue #290 mục B3).
- POS đổi "Ghi sổ tại quầy" thành "Lưu đơn", duyệt đơn tặng tự chuyển ngày và
  ghi sổ: đang chờ làm ở issue #296.

Kỹ thuật: PR #291 #292 #293, SHA cdca9731, issue #290 #283 #247.
```

Khối Telegram tương ứng:

```
<!-- telegram-release
{"version":"v486","sha":"cdca9731","live_verified":true,"features":["Một đơn kẹt không còn giữ cả ngày, các đơn khác vẫn ghi sổ và xuất hoá đơn.","Nút Ghi sổ hoá đơn bán hàng gom cả bill quầy.","Đơn tặng gửi duyệt lại về Chờ duyệt, lý do không mất khi đồng bộ Pancake.","Công tắc Hàng tặng xuất kho thật, mặc định tắt.","Chọn combo chưa khai báo thì màn chọn món báo ngay lý do."]}
-->
```

## Bảng tự chấm trước khi đăng

- Thu ngân đọc có hiểu không cần hỏi lại? Có / Không
- Có dòng nào chứa tên hàm, tệp, trường, nhánh? Có thì sửa
- Phần "Đã kiểm trên site thật" có tên màn và con số? Có / Không
- Phần "Còn tồn" có ghi thật lỗi còn lại? Có / Không
- Có dấu em dash hay en dash? Có thì sửa
