# PR #243: thuế máy chủ và giá vốn hàng tặng

## Phân công và trạng thái

Codex code/test/push. Claude review cuối, chạy bench còn thiếu và phát hành.
PR giữ Draft cho tới khi có bằng chứng tích hợp trên SHA cuối. Không đóng
#225 hoặc #237, không xử lý lại năm hoá đơn tặng cũ.

Nền main `de53971`, v459. Nhánh `codex/225-thue-tung-dong`, đề xuất v460.
Fetch lại trước đẩy; số phiên bản phải kiểm lại ngay trước phát hành.

## Vấn đề và hành vi sau sửa

1. `AccountsController.set_taxes_and_charges` của ERPNext de59166 phụ thuộc
   Accounts Settings. Khi máy chủ tạo SI, có tên mẫu chưa đủ để nạp bảng
   con. Controller SI nay nạp mẫu chỉ định hoặc mẫu mặc định duy nhất còn
   dùng của công ty trước cửa này. Không lấy 8% từ M-Invoice để đoán thuế.
2. Dòng thuế tự sinh từ Item Tax Template mặc định chưa gồm giá, gây bill
   220.000 thành 239.000. Dòng tự sinh được thay bằng bảng của mẫu gồm giá.
   Mẫu món quyết thuế suất, tài khoản phải khớp bảng thuế. Bảng thuế có sẵn
   do người dùng khai được giữ nguyên, không âm thầm sửa chính sách ngoài giá.
3. SI VND đủ điều kiện tính số tiền nguyên đồng từng dòng. Cache precision
   chỉ sống trong lần tính, không đổi giá/qty hoặc precision toàn hệ thống.
   Payload hai cửa M-Invoice và VAT hàng tặng đọc số đã lưu theo item_row,
   không nối theo item_code hoặc lấy một thuế suất chung từ Settings.
4. SI mới sau patch có dấu chính sách kho. Khi là hàng tặng có món quản
   kho, máy dùng Kho xuất hàng tặng của điểm bán, đặt expense_account 64181
   từng dòng và bật update_stock. Kho phải là kho lá, cùng công ty, gắn
   tài khoản tồn kho VND thuộc 155 (bao gồm 1551). Không tự đổi tài khoản
   kho thật hoặc lấy Item Default đang trỏ về kho nguyên liệu 152.
5. Trước ghi sổ, khoá Bin và kiểm tổng lượng theo mã/kho, không cho xuất âm.
   Lô người dùng chọn được core kiểm; lô tự chọn lấy lô còn dùng theo hạn
   dùng và chia chung cho cả hoá đơn, tránh hai dòng trùng mã lấy trùng tồn.
   Bundle dùng SerialBatchCreation của core, không tự ghi SLE.
6. GL giá vốn lấy trực tiếp StockController.get_gl_entries từ SLE thực tế:
   Nợ 64181 / Có tài khoản kho thực tế. Ghép VAT 64182/33311, không ghi
   doanh thu/công nợ của giá thị trường. Huỷ/repost dùng cơ chế core.
7. Điểm lưu bao lần chuyển SI nháp sang ghi sổ để caller bắt lỗi rồi commit
   không giữ lại parent/SLE/GL dở. Dọn callback commit của lần thất bại.
   Tạo thẳng SI docstatus 1 bị chặn trước write; phải lưu nháp rồi submit.
   Đổi tặng sang bán thường gỡ cờ tự xuất và 64181. Đổi phương thức muộn
   trong bảng nhiều phương thức bị chặn ghi sổ, yêu cầu lưu lại nháp.

## Cấu hình cần làm trước khi dùng hàng tặng mới

- App: Cài đặt > Điểm bán > chọn điểm > Kho xuất hàng tặng > Lưu.
  Ô chọn có tìm kiếm từ danh mục Warehouse. Không tự gán kho khi migrate.
- Chọn kho theo nơi thực giao; tài khoản Có do kho đó quyết định. Site đã
  ghi nhận có kho thành phẩm gắn 1551, không yêu cầu đổi về tài khoản 155.
- Tài khoản 64181/64182/33311 phải là tài khoản chi tiết còn dùng, đúng
  công ty, tiền tệ VND. Perpetual inventory phải bật khi xuất kho tặng.
- Thiếu cấu hình sẽ chặn có chỉ dẫn. Công ty Demo không tự được cấu hình.

## Chống xuất hai lần và giới hạn phải nói rõ

SI mới tự xuất kho khi ghi sổ. Không đưa cùng bánh tặng vào phiếu xuất tay
cuối ngày. Stock Entry có liên kết `Hoá đơn hàng tặng liên quan` trỏ SI mới
sẽ bị chặn cả ở validate và before_submit. Dòng xuất dùng 64181 bắt khai
liên kết này. SI legacy liên kết phiếu riêng chỉ được có một phiếu còn hiệu
lực/nháp; khoá invoice để tránh hai người tạo trùng.

Giới hạn: hệ thống không thể suy ra một phiếu xuất tay không khai nguồn,
ghi sang tài khoản khác, là cùng bánh đã tặng. Không tuyên bố tự chặn mọi
phiếu tay dựa trên tên món/ngày. Khi chốt ca, kế toán đối chiếu các phiếu
SI tự xuất trước khi lập phiếu tổng. Hàng bán thường giữ luồng update_stock=0;
không chuyển toàn bộ bán hàng sang xuất kho trong PR này.

Kiểm bánh/In-store vẫn là bảng kiểm đếm, không nhập hoặc xuất kho kế toán.
SI cũ không nhận dấu kho mới khi migrate. Không tự xuất kho bù, sửa hoặc
huỷ chứng từ cũ. Bộ sản phẩm Product Bundle bị chặn trong luồng tặng mới:
tách thành các món tồn kho thực giao rồi duyệt để không bỏ sót giá vốn.

## Kiểm đã làm ở máy Codex

- Đọc core ERPNext de59166 và Frappe f33ac3f, đặc biệt trình tự validate,
  set_missing_values, set_taxes_and_charges, insert/_save/on_submit,
  StockController.get_gl_entries và SerialBatchCreation.
- Review chéo bắt hai lỗi và đã sửa: chuyển tặng sang thường giữ 64181;
  insert docstatus1 bỏ qua điểm lưu. Có ca giữ lại hai tình huống.
- Tầng khung: 2.703 ca đạt ở vòng hiện tại. Phải ghi SHA cuối và kết quả
  cổng đầy đủ vào comment PR sau commit; không coi số này là bằng chứng core.
- Thêm 11 ca bench ở thu_cua_thue_243.py và thu_hang_tang_kho_243.py.
  Codex chưa thực thi vì máy hiện tại không có bench/Docker/MariaDB;
  đã hỏi đường truy cập bench thử. Không chạy code chưa phát hành trên site thật.

## Chặn phát hành và bằng chứng cần trả

1. Bench đúng core: migrate và đọc Patch Log của `thue_vnd_v458` cùng
   `hang_tang_kho_v458`, kiểm ba field mới. Patch kho tách riêng vì bench
   Claude đã chạy patch thuế tại SHA trước. Chạy migrate lần hai không đổi dữ liệu.
2. Chạy 7 ca #225 cũ + 11 ca #243 mới trên bench, bao gồm đúng tao_don_tay,
   bill hỗn hợp 220.000, insert có tên mẫu thiếu bảng, phần trăm giảm/qty lẻ;
   BOM -> WO -> Manufacture có batch -> SI -> SLE/GL; rollback sau GL rồi
   thử lại, thiếu tồn, sai batch, huỷ, chuyển loại, insert trực tiếp, xuất tay trùng.
   Hai khoá chung_tu_con_sot và so_luong_lech phải rỗng.
3. Chạy trọn hai Server Script bằng safe_exec và HTTP stub, không chỉ cửa
   chuan_goi. Đối chiếu payload sau SI reload từng dòng, VAT, tổng với GL.
   Các ca legacy #225/#227 cũng phải chạy; lỗi fixture phải chỉ rõ và dựng
   đủ fixture, không chấp nhận ném lỗi core nhưng vẫn báo ca đạt.
4. Chạy thêm hai người cùng xuất một kho và hai dòng trùng mã qua nhiều lô;
   mất phản hồi sau commit -> mở lại SI -> thử lại không thêm SLE/GL.
5. Thống kê chỉ đọc SI cũ chưa phát hành và các dạng ngoài chính sách tiền:
   nhiều dòng thuế/phí, Actual, trả hàng, tiền tệ khác, shipping rule,
   cash/non-trade discount, nội bộ. Chúng giữ core/cách xuất cũ. SI VND mới/nháp trống bảng và không có mẫu mặc định duy nhất bị chặn
   với chỉ dẫn chọn mẫu, kể cả khi không có nguồn app. Không coi bảng thuế
   trống là chính sách 0%; thuế 0% phải khai tường minh.
6. Cấu hình kho từng điểm bán có người phụ trách đối chiếu kho thực giao;
   hướng dẫn kế toán loại phần SI tự xuất khỏi phiếu xuất tổng cuối ngày.
   Sau merge/deploy, xác minh phiên bản, Patch Log và màn thật riêng.

Không phát hành M-Invoice thử. Không sửa hoá đơn đã gửi cơ quan thuế.


## Vòng 3: bộ ca chạy nối tiếp và nền v460

Anh Việt cho phép gộp main v459 và đặt v460. Giữ đủ thay đổi #237 của
main và các dòng patch v458/v459, thêm dòng đồng bộ v460. Hai patch
thue_vnd_v458/hang_tang_kho_v458 giữ tên vì bench đã ghi Patch Log.

Review Claude vòng 2 ở SHA 6fc500c xác nhận hai lỗi VAT cũ đã hết;
chuỗi sản xuất có lô -> SI -> SLE/GL và huỷ chạy được. Phát hành tay qua
safe_exec/HTTP stub khớp tiền SI; xuất rải gửi 0 gói do dùng lại SI đã
phát hành, nên CHƯA coi là kiểm xong cửa xuất rải.

Sáu ca sau ca xuyên luồng lỗi tại dựng kho. Đọc đúng core chỉ ra:
`erpnext/stock/__init__.py:get_warehouse_account_map` giữ bảng kho trong
`frappe.flags` suốt request. Mỗi ca tạo kho mới nhưng bảng vẫn là ca cũ.
`Database.rollback(save_point)` chỉ xoá value_cache, không xoá bảng này
hay bốn CallbackManager. Đây là đường nhiễm trạng thái đã có bằng chứng
mã nguồn và ca hồi quy khung. Không kết luận huỷ SI tự commit: core
on_cancel không có commit trực tiếp, commit thường bị bộ đếm chặn.
`_DA_TAO` cũng không xoá tài khoản, chỉ ghi tên và kiểm còn sót.

Sửa tại khung chung:
- Cách ly bảng kho/tài khoản trước mỗi ca; dọn request cache và cache
  document đã chạm/tạo sau rollback, phục hồi bốn hàng đợi và realtime log.
- Giữ nguyên cờ và bộ đếm giao dịch của caller. Không bật frappe.in_test
  để đi sang đường khác với site thật, không dùng tài khoản thật cố định
  để che lỗi bộ nhớ, không xoá chứng từ thử bằng delete_doc.
- Chặn DDL trước cửa sql_ddl tự bỏ khoá/commit của Frappe; chặn SQL thoát
  giao dịch trực tiếp, giữ rollback tới savepoint hoạt động. Câu lỗi có
  traceback để tìm đúng caller nếu còn đường làm mất điểm lưu.
- Nếu không rollback được, dừng lượt ngay; trả mat_diem_luu, da_chay,
  chua_chay, sach=0. Không báo sạch chỉ vì hai bảng đếm chưa lệch. Cửa HTTP ném lỗi kèm chẩn đoán nếu không sạch để Frappe
  không tự commit khi POST kết thúc.
- Theo dõi thêm SI, phiếu kho, WO, BOM, Account, Warehouse, Batch và bundle.
- Fixture lô được khai trong nen_bench (chỉ bench có cờ cho phép) và tạm
  trong từng ca kho. Ca thiếu tồn bật allow_negative_stock=1 thực sự.

Kiểm khung: 2.703 ca đạt, gồm 6 ca mới chạy chính nen.py với DB giao dịch
mô phỏng: hai ca nối tiếp, lỗi giữa ca, mất savepoint, DDL/SQL phá giao
dịch, và cố tình bỏ dọn bảng kho/callback/realtime. Cả ba bản phá đều
bị bắt. Các ca này chứng minh khung, không thay bằng chứng ERPNext.

Claude cần chạy lại full cua.chay HAI LƯỢT trong cùng process, không chỉ
chạy riêng từng hàm. Phải có đủ 11 ca #243 đạt, da_chay=so_ca,
chua_chay=0, mat_diem_luu=false, chung_tu_con_sot=[] và so_luong_lech={};
đối chiếu lỗi cũ với main đúng nền de53971. Nếu còn mất điểm lưu, gửi
nguyên traceback từ khung mới. Không sửa khung để bỏ qua rollback lỗi.
Dùng hai SI thử độc lập cho xuất tay và xuất rải để mỗi cửa thật sự gửi
đúng một gói tới HTTP stub. Các cửa đồng thời/nhiều lô/mất phản hồi và
thống kê SI ngoài chính sách vẫn theo mục chặn phát hành trên.
