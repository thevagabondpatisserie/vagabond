# Issue #227: HĐĐT sai người nhận và hàng tặng

Codex sửa, Claude review bổ sung và phụ trách merge/deploy theo phân công
của anh Việt ngày 07/09/2026. Đây là phần 1, chưa đóng issue #227.

## Bản sửa hiện tại

- Kịch bản nạp Pancake trước đây dùng tìm kiếm `page_size=1`, lấy `data[0]`
  rồi ghi tên/email mà không đối chiếu mã đơn. Nay phải khớp display_id và
  cả ID Pancake khi SI có ID. Không khớp hoặc nạp lỗi thì phát hành dừng
  đúng phiếu đó, trả lý do để kế toán kiểm liên kết.
- Email ghi chú chung không đủ để thay thông tin người mua. Tên cá nhân
  đã xác nhận được giữ. Khi ghi đè có chủ ý, tên/MST/email được thay cùng
  bộ, không ghép tên mới với MST cũ.
- Cửa cuối chung cho Python và Server Script lấy thông tin từ SI, bỏ
  email/địa chỉ của khách lẻ mặc định, kiểm tên/MST/email và bóc nhãn địa
  chỉ. Python không còn lấy portal bất kỳ khi mã đơn rỗng; portal trùng
  mã phải được xác nhận, không chọn bản đầu.
- Từng dòng của đơn Hàng tặng đã duyệt và quà VIP có ghi chú
  `(Hàng biếu tặng không thu tiền)` trên chính `inv_itemName`. Giữ nguyên
  giá tính thuế và VAT. Chưa sửa luồng GL, tổng khách phải trả hay giá vốn.
- Giữ chỗ trước HTTP bằng current read có khoá và cờ bền vững. Timeout,
  lỗi không rõ kết quả hoặc Save bị từ chối giữ cờ để tránh tự phát hành
  đúp. Lần thành công có ID xoá cờ. ID hoặc số HĐĐT cũng chặn gửi lại.
  Kế toán trưởng/Giám đốc có nút Desk đối chiếu rồi mở lại, bắt xác nhận
  chưa có bản trên M-Invoice, lý do và lưu Comment. Không mở lại khi có ID.
- Các cửa lưu thông tin XHD và nạp/bù email giữ nguyên người mua của phiếu
  đã gửi hoặc đang chờ đối chiếu. Không sửa HĐĐT đã phát hành.

## Nguồn kiểm chứng

Site đã chạy main abccbaa (v445), Frappe f33ac3f v16.27.1, ERPNext de59166
v16.28.0, kiểm trực tiếp trang Apps của Cloud trong tác vụ này.

Đã đọc nguyên script qua Desk bằng tài khoản Nguyễn Hoàng Việt, chỉ sao
chép, không bấm Lưu hoặc phát hành. Snapshot toàn bộ ở
`vagabond/khung/kiem_thu/du_lieu/minvoice_*_20260907.txt`.
Đối chiếu độ dài và FNV-1a theo ký tự với clipboard gốc:

- Nạp: 6470 ký tự, 471469736.
- Phát hành: 9865 ký tự, 511990956.

Các chuỗi mật khẩu/token trong snapshot là tên trường và biến, không phải
giá trị thông tin đăng nhập thật. Test dùng miền `.invalid` và dữ liệu giả.

## Kiểm và giới hạn

Cổng `kiem_truoc_deploy.sh` mã 0, 2600 ca tầng khung đạt; bundle khớp từng
byte, bộ kiểm DOM hiện có xanh. Các ca mới chạy toàn bộ snapshot script,
không chỉ dò chuỗi: bản cũ nạp email từ đơn 1227 vào đơn 227; bản mới
không ghi. Kiểm đúng mã, mail ghi chú chung, giữ tên người mua đã xác nhận,
payload success/reject/timeout/preview, nạp lỗi không Save, quyền mở lại.

Chưa chạy safe_exec trên bench thật hoặc kiểm hai worker cạnh tranh trên
MariaDB. Chưa phát hành/ký/gửi email thật. Trước merge/deploy, Claude cần
kiểm lại snapshot chưa bị ai sửa và chạy kiểm trên bench tương đương site.
Current read dùng `get_doc(..., for_update=True)`; đã đối chiếu cơ chế này
trong `frappe/model/document.py` và transaction trong `database.py`.

## Triển khai phần 1

1. Claude review PR và CI trên SHA cuối; nếu sửa phải chạy lại gate.
2. Bản v446 có patch riêng `minvoice_v446`: tạo field trước rồi tính bản
   vá cho cả hai Server Script trước khi lưu. Đoạn gốc không khớp thì dừng
   migrate, không ghi đè script mới và không chọn bỏ qua failed patches.
3. Patch giữ nguyên API method, quyền và phần còn lại của hai script.
   Không tự phát hành/ký hoặc chỉnh dữ liệu hoá đơn cũ trong migration.
4. Sau migrate, kiểm marker #227 trong cả hai script, field mới, APPVER446.
   Xem thử payload cho khách lẻ, khách có MST và đơn tặng đã duyệt trước
   khi đưa đường phát hành vào sử dụng. Chế độ `thu` vẫn đăng nhập M-Invoice
   theo script gốc nhưng không Save; không dùng chứng từ đã phát hành để thử.
5. Rà các SI chưa gửi đã có thông tin bị nạp nhầm từ trước: bản sửa chặn
   nguồn lỗi mới, không tự đoán và xoá thông tin lịch sử. Đối chiếu đúng
   Pancake/portal và người mua rồi sửa bằng quyền kế toán trước phát hành.
6. Nếu cờ chờ đối chiếu bật, tra M-Invoice theo `key_api=SI.name`. Có bản
   thì đồng bộ ID/trạng thái bằng luồng M-Invoice hiện có; chỉ dùng nút mở
   lại sau xác nhận chưa có bản. Nút không tự gửi hoá đơn.

## Phần 2 còn mở: kế toán hàng tặng

Yêu cầu nghiệp vụ đã nhận: không có doanh thu 511/công nợ 131, giá vốn
Nợ 64181/Có 155; VAT Nợ 64182/Có 33311. Hoá đơn VAT vẫn giữ giá tính thuế
và nói rõ không thu tiền. Không thêm bước kế hoạch chi.

Phát hiện nền: cả đơn Pancake và đơn tại quầy trong `ban_hang.py` hiện
đặt `update_stock=0`. Luồng hàng tặng đang tạo SI thường rồi JE gạt công
nợ, nên 511 vẫn còn và chi phí bị tính theo tổng giá bán, không phải giá
vốn sản xuất. Chỉ đổi JE gạt công nợ sẽ không đáp ứng yêu cầu.

Đã hỏi anh Việt điểm trừ kho hiện tại: ngay tại đơn tặng hay qua phiếu
xuất kho/kiểm bánh cuối ngày. Chưa nhận câu trả lời trong lúc chuẩn bị
bản này. Không tự bật update_stock vì có thể trừ kho hai lần. Sau khi
chốt, sửa đường ghi sổ tại nguồn với tài khoản đúng công ty, không gắn
party vào tài khoản chi phí; thêm test insert/submit đọc GL và SLE thật,
kiểm huỷ/ghi lại và không đụng chứng từ cũ. Phần này chưa code, chưa kiểm.

## Chứng từ cũ

11552 và HDB-26-09-00171 cần kế toán đối chiếu và thực hiện quy trình
điều chỉnh/thay thế cùng bút toán có vết. Không xoá dòng GL hay tự huỷ,
gửi lại HĐĐT đã đến cơ quan thuế. Nội dung issue dẫn Nghị định 123;
quy trình phải đối chiếu cả phần sửa đổi tại Nghị định 70/2025, không dùng
nguyên hướng dẫn cũ: https://vanban.chinhphu.vn/?docid=213179&lang=vi&pageid=27160.

Issue chỉ hoàn tất khi cả phần 2 và đối chiếu chứng từ cũ có kết quả.
