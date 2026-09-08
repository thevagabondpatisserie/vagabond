# PR #243: thuế máy chủ và giá vốn hàng tặng

## Phân công và trạng thái

Codex code/test/push. Claude review cuối, chạy bench còn thiếu và phát hành.
PR giữ Draft cho tới khi có bằng chứng tích hợp trên SHA cuối. Không đóng
#225 hoặc #237, không xử lý lại năm hoá đơn tặng cũ.

Nền main `4e95e2a`, v457. Nhánh `codex/225-thue-tung-dong`, đề xuất v458.
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
- Tầng khung: 2.692 ca đạt ở vòng hiện tại. Phải ghi SHA cuối và kết quả
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
