# Issue #227: HĐĐT đầu ra, hàng tặng và hoá đơn mua

Codex sửa, Claude review bổ sung và phụ trách merge/deploy theo phân công
của anh Việt ngày 07/09/2026. Bản sửa gồm chặn gửi nhầm HĐĐT, kế toán hàng tặng khi chưa có kho sản xuất, và các lỗi hoá đơn mua trong comment mới của anh Việt. Chưa đóng issue #227.

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
  giá tính thuế và VAT. Đơn tặng ghi sổ mới dùng GL riêng như phần kế toán dưới đây.
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

Cổng `kiem_truoc_deploy.sh` mã 0, 2605 ca tầng khung đạt; bundle khớp từng
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

## Kế toán hàng tặng và quyết định về kho ngày 07/09/2026

Anh Việt đã chốt: về sau trừ kho khi ghi sổ hoá đơn. Hiện chưa hoàn thiện
BOM/lệnh sản xuất, chưa có tồn kho ERP; nhập xuất tồn được theo dõi trên
màn Kiểm bánh thay Excel. Không thêm bước kế hoạch chi.

Bản v446 này xử lý giai đoạn hiện tại:

- Đơn Hàng tặng được duyệt hoặc quà VIP ghi sổ mới có dấu nội bộ
  `vgb_tang_so_cai`. SI vẫn giữ giá thị trường để lập HĐĐT, nhưng GL chỉ
  ghi Nợ 64182/Có 33311 phần VAT. Không tạo GL 511/131, Payment Ledger
  hoặc JE gạt toàn bộ giá bán thành chi phí. Khách phải trả 0.
- Phép chia VAT gross theo từng dòng khớp script phát hành hiện tại,
  lấy `MInvoice Phat Hanh Settings.thue_suat` (fallback `or 8` như script).
  Với 1.900.000 và 8%: giá trước thuế 1.759.259, VAT 140.741. Lưu số VAT,
  thuế suất và tài khoản ngay lúc ghi sổ để repost không chạy theo cấu
  hình mới. Cửa phát hành so khớp từng dòng và tổng, lệch thì không gửi.
- Kế toán phải có đúng một tài khoản chi tiết 64182 (Expense) và 33311
  (Liability), đúng công ty, còn dùng, VND; có cost center trên SI hoặc
  mặc định công ty. Không tự tạo/sửa danh mục tài khoản khi migrate.
- Giữ `update_stock=0`, không sửa Kiểm bánh, không sinh SLE hoặc bút toán
  giá vốn giả. Field và thông báo Desk ghi rõ chờ giá vốn. **Chưa triển
  khai tự xuất kho/64181-155**; nếu bật `update_stock=1` trên đơn tặng mới
  thì dừng trước ghi sổ, không âm thầm ghi thiếu phần kho. Giai đoạn kho
  sản xuất sau cần triển khai SLE chuẩn tại submit cùng giá vốn thực tế,
  rồi mới mở cửa này. Không tự xuất bù các đơn đang chờ giá vốn.
- Các loại chưa được hỗ trợ (return/POS/ứng trước/thu tiền/mở sổ/doanh
  thu chờ phân bổ/phiếu giao hàng/tài sản) dừng rõ để kế toán tách đúng
  chứng từ. Hàng tặng mới không tích điểm trên giá tính thuế.
- Phiếu đã ghi sổ trước bản sửa không có dấu mới: giữ đường GL cũ khi
  huỷ/repost. Migration không duyệt lại, không sửa GL và không đổi thuế
  các phiếu cũ. Đơn nháp ghi sổ sau deploy dùng đường mới.

Đã đọc ERPNext de59166: SalesInvoice `get_gl_entries`, `make_gl_entries`,
`on_submit`; AccountsController `get_gl_dict`; general_ledger, GLEntry,
party và Payment Ledger. Override chỉ thay bản đồ GL theo dấu mới; ghi
và đảo bút toán vẫn dùng core. Không gắn Customer lên tài khoản chi phí.

## Cổng bàn giao kế toán cho Claude

Bắt buộc trước merge/deploy: trên bench tương đương chạy
`bench --site <site-thu> execute vagabond.khung.kiem_that.cua.chay`.
Ba ca mới ở `thu_hang_tang_227.py` insert/submit SI thật, đọc GL/PLE/SLE,
kiểm repost và cancel, đơn thường, chặn xuất kho chưa triển khai. Giữ
savepoint, khoá commit và cờ cấm gửi ra ngoài; hai khoá
`chung_tu_con_sot`/`so_luong_lech` phải rỗng. Thiếu danh mục/core ném lỗi
là ca đỏ. Codex chưa chạy tầng này vì máy làm code không có bench/DB.

Ngoài test, Claude cần đối chiếu quyền, flow VIP và đơn Hàng tặng trên
app; xác nhận hiển thị khách trả 0, không tích điểm; kiểm payload preview
và thông báo chờ giá vốn. Không phát hành thật bằng dữ liệu thử. Giữ PR
Draft đến khi bằng chứng tích hợp và review bổ sung đạt.

## Chứng từ cũ

11552 và HDB-26-09-00171 cần kế toán đối chiếu và thực hiện quy trình
điều chỉnh/thay thế cùng bút toán có vết. Không xoá dòng GL hay tự huỷ,
gửi lại HĐĐT đã đến cơ quan thuế. Nội dung issue dẫn Nghị định 123;
quy trình phải đối chiếu cả phần sửa đổi tại Nghị định 70/2025, không dùng
nguyên hướng dẫn cũ: https://vanban.chinhphu.vn/?docid=213179&lang=vi&pageid=27160.

Issue chỉ hoàn tất khi kiểm kế toán trên bench đạt và chứng từ cũ đã được kế toán đối chiếu/xử lý. Kho sản xuất là giai đoạn riêng theo quyết định trên.


## Bổ sung theo comment 5573317438 và 5573341341

Ba ca được tái hiện từ ảnh và mã nguồn, chưa sửa chứng từ trên site:

- Nam An, HDM-26-08-00158: ảnh HĐĐT ghi số **70173** (comment ghi
  10173), tổng 319.800, VAT 15.229. PI cộng thêm một dòng 8% 24.365,76.
- Thanh An, HDM-26-08-00186: 2.400 PCS / 5.520.000, ba phiếu nhập
  PNK-2026-00147, 00131, 00173 tổng 5.460.000. Chênh giá 60.000 là
  dữ liệu người dùng báo; bản sửa giữ giá HĐĐT, không ghi đè giá PR.
- Gia Truyền Sài Gòn, HDM-26-08-00224, HĐ5561: hàng 578.700,
  chiết khấu 28.935, sau giảm 549.765, VAT 43.981, tổng 593.746.
  Trước sửa dòng giảm bị cộng thành hàng rồi đầu phiếu giảm 57.870.

### Nguyên nhân và thay đổi

1. Hook before_validate cũ bỏ qua docstatus=1, trong khi Frappe
   `Document._save` đã đặt docstatus=1 trước validate khi submit. Nay
   chuẩn hoá cả save và submit, bỏ qua cập nhật metadata phiếu đã ghi sổ.
2. Thuế không còn phụ thuộc điều kiện tiền hàng lệch. Mỗi lần chuẩn hoá
   xoá mẫu thuế hàng, giữ đúng một dòng Actual theo VAT HĐĐT, kể cả 0
   (ngăn core nạp default taxes khi new doc có bảng taxes rỗng). Giữ
   ignore_pricing_rule. Thiếu tài khoản đầu vào thì submit dừng rõ.
3. Tính chất dòng dùng chung cho import, dựng lại, học ánh xạ, ghim số
   và dịch vụ. tchat=3 là chiết khấu, 4 là ghi chú; mã nguồn rõ được ưu
   tiên, chỉ dùng nhãn khi không có mã. Không dựng hai loại này thành
   mặt hàng. Với tờ cũ cấu trúc sai, dựng lại hai dòng hàng và giảm một
   lần 28.935. Dịch vụ đã dùng số sau giảm thì xoá giảm giá đầu phiếu cũ.
4. Một dòng PI được chia qua nhiều pr_detail vì core chỉ cho một
   pr_detail trên mỗi dòng. Giữ tổng lượng, đơn giá HĐĐT và mapping;
   ghim lại không nhân lượng gốc lên từng dòng đã chia. Trừ lượng PI đã
   ghi sổ và lượng đã nối trên chính tờ, bỏ PR được chọn trùng.
5. Tên đơn vị giống nhau không che được hệ số khác nhau. Chênh giá vẫn
   qua cửa quyền/cấu hình hiện có và Comment chênh giá, không tắt core.
6. Thêm before_submit kiểm lượng theo pr_detail, kể cả Desk/API và hai
   PI nháp cùng chọn PR. Core `PurchaseInvoice.validate_multiple_billing`
   dùng **amount**, nên giá thấp không đủ bảo vệ số lượng. Khoá PR theo
   thứ tự, current read trực tiếp PIItem.docstatus=1, loại chính PI.
   Patch `mua_hddt_v446` tạo index `(pr_detail, docstatus)`; truy vấn ép
   index này để tránh quét dòng nháp đang bị phiên khác khoá. Không
   JOIN khoá parent PI khác. **Phải migrate trước khi sử dụng hook.**

Đã đối chiếu mã nguồn Frappe f33ac3f và ERPNext de59166: thứ tự save/
submit, child docstatus và row lock, nạp Item/tax defaults, tính thuế,
PurchaseInvoice validate previous document và multiple billing. Đây
không phải xác nhận đã chạy các thay đổi trên runtime thực tế.

### Kiểm và điều kiện Claude cần hoàn tất

- Tầng khung: 2.614 ca, gồm 9 ca mới tái hiện các lỗi trên; môi trường
  không có requests cũng phải đạt. Cổng 10 công đoạn và ghép từng byte
  phải đạt trên SHA cuối cùng. Kết quả CI xem ở PR, không suy từ SHA cũ.
- Đã thêm **5 ca tích hợp** `khung/kiem_that/thu_mua_hddt_227.py` vào
  runner hiện có: Nam An qua save/submit, chiết khấu, dịch vụ, ba PR,
  hai PI nháp giá thấp cùng PR. Các ca insert/submit và đọc GL/SLE/PR
  thật, rollback toàn bộ theo nen. Chưa chạy vì checkout không có bench.
  Cùng với ba ca hàng tặng, cần chạy trên bench tương đương đã migrate;
  `hong=0`, `chung_tu_con_sot=[]`, `so_luong_lech={}`. Ca giá thấp cần
  cấu hình mua cho phép chênh giá như site; không bỏ qua nếu fixture đỏ.
- Trên **site thử riêng**, kiểm EXPLAIN dùng index vgb_pr_docstatus_227;
  chạy hai worker đồng thời submit hai PI có tổng lượng vượt PR nhưng
  tổng amount chưa vượt PR. Chỉ một PI được ghi sổ, PI kia báo hết lượng,
  không nhân GL/SLE. Lặp với submit/cancel: tổng lượng đã ghi sau cùng
  không vượt nhận; deadlock nếu có phải rollback và thử lại an toàn.
  Bộ savepoint một kết nối không chứng minh được ca đồng thời. Chưa
  tuyên bố đã loại mọi deadlock; đặc biệt cancel/repost có thứ tự khoá
  core khác. Claude cần ghi bằng chứng MariaDB trước khi bỏ Draft.
- Đối chiếu ba PI thật đang nháp với HĐĐT gốc rồi dùng Save/luồng nối
  hiện có sau deploy. Không migrate sửa hàng loạt chứng từ cũ, không
  sửa raw MInvoice, không huỷ/gửi lại HĐĐT. Nếu đã ghi sổ, dừng để kế
  toán xử lý theo quy trình; bản vá không sửa metadata thành bút toán.

PR vẫn Draft để Claude review bổ sung và chạy các cổng trên. Codex chỉ
code/test/push; không merge, deploy hoặc chỉnh dữ liệu thật trong lượt này.
