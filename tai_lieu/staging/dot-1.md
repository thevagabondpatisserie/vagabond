# Đợt 1 - Issue257

## Phạm vi nghiệm thu

| Luồng | Thao tác qua app | Bằng chứng bắt buộc |
|---|---|---|
| Nhận hàng | chọn phiếu, nhập số, gửi; lỗi rồi sửa/gửi lại | một chứng từ, đúng hệ số/SLE; không khoá form vĩnh viễn |
| Sản xuất | chọn BOM, nguyên liệu, ghi nhận thành phẩm | đúng nguyên liệu/thành phẩm/SLE; lô tham chiếu không gây chặn vô lý |
| Bán/hàng tặng | chọn kho, ghi sổ, hủy chứng từ thử | giá vốn đúng kho/64181, thuế hỗn hợp, đảo đủ; M-Invoice chỉ stub |
| Thanh toán | đối chiếu, ghi nhận, huỷ, bỏ đối chiếu, ghi nhận lại | trạng thái rõ, không chuyển/ghi đôi, không gửi thư trùng; phụ thuộc PR250 |
| Vận đơn | cập nhật ngày đang xem, đổi ngày ở nguồn thử | đơn đổi ngày biến mất khỏi ngày cũ, có ở ngày mới; hàng đợi không bỏ đói |

Chưa có ca trình duyệt chạy đủ năm luồng. Bộ bench hiện có là nền kiểm
Document/GL/SLE, không được đổi tên thành E2E. Nghiệm thu cần bấm nút thật,
HTTP thật tới site thử, chỉ stub dịch vụ bên ngoài ở ranh giới.

## Môi trường

Tái dùng core pin và fixture trong khung/bench_thu. CI hiện dùng một lần,
không phải staging cố định. Staging cố định cần URL/tài nguyên riêng được
xác minh, không lấy production làm site thử, không tạo dịch vụ tính phí
chưa có hạn mức. Không dùng mật khẩu mẫu CI trên site truy cập công khai.
Không mang dữ liệu/bí mật production sang thử; email và API ngoài bị chặn.

## Trạng thái và đơn vị

PR250 giữ nguyên quyền sở hữu nhánh. Chuẩn hoá theo cùng nguồn máy chủ,
không sửa chồng. Công cụ `python3 -m vagabond.khung.staging.ra_uom input.json
output.json` chỉ rà snapshot đã xuất, chưa đọc live hoặc sửa dữ liệu.
JSON gồm items (item_code, stock_uom, purchase_uom, sales_uom, uoms với
uom/conversion_factor) và quy_uoc_da_duyet (item_code -> stock_uom).
Quy đổi đóng gói cần bằng chứng từng món; không suy số quả/thùng từ tên.

## Đo trước và sau

Anh Việt xác nhận nhóm màn dùng thường xuyên ngày09/09: vận đơn,
nhận hàng/kiểm bánh và hồ sơ thanh toán. Chọn ba màn đo là Vận đơn,
Kiểm bánh, Hồ sơ thanh toán; Nhận hàng vẫn thuộc kiểm nghiệp vụ bắt buộc.
Cùng dữ liệu, role, máy/mạng và số lượt; tách tải lần đầu
và cache. Báo số thao tác, p50/p95 thời gian tới dữ liệu dùng được, số API,
SQL và dung lượng. Chưa có số đo mới nên chưa tuyên bố tăng tốc.
Chỉ tối ưu sau baseline; phép kiểm hồi quy phải bắt lại lỗi cũ.

Màn Kiểm bánh có JS riêng `trang/kiem-banh.js`, không nằm trong bundle
app_bep. `chonNgay` gọi `kiem_banh.dong_bo` ngay khi mở, lỗi mới đọc `bang`;
không coi mở màn này là phép chỉ đọc. Đo trên staging với fixture và cửa
Pancake giả lập đủ hợp đồng, không lặp mở site thật để lấy baseline.

Gateway `khung/staging/phuc_vu_ci.py` mới chỉ là nền phục vụ HTTP local;
chưa có kết quả chạy trên CI, chưa phải staging đã nghiệm thu. Kiểm cờ site,
chặn socket connect/connect_ex ra ngoài, không có worker và chỉ bind127.0.0.1.
Đây không phải firewall chống mọi subprocess. Driver `kiem_man.cjs` đăng nhập
qua HTTP thật, mở năm màn ở 390px/1280px và kiểm ô sẵn sàng, lỗi API/JS;
lưu ảnh, trace và thời gian vào artifacts. Đây chỉ là kiểm mở màn với
Administrator, chưa chứng minh quyền nhân viên hoặc năm luồng nghiệp vụ.
Đã nối bước browser sau bench qua kết nối GitHub của app có quyền workflow.
Còn cần kết quả runtime và đủ fixture/thao tác cho năm kịch bản.

## Ca vận đơn đã viết, chưa chạy browser

`van_don_ci.py` dựng một vận đơn trong tương lai trên bench CI dùng một lần.
`kiem_van_don.cjs` bấm nút đồng bộ, đợi API và khung màn thay mới, kiểm ngày
cũ hết đơn, ngày mới có đơn; bấm lại không nhân đôi. CLI cuối đọc DB và log
HTTP để kiểm đúng đường danh sách rỗng -> GET ID -> danh sách ngày mới.
Chỉ thay `requests.Session.request`; không thay hàm đồng bộ hoặc ghi DB.
Đây chưa phải ca hàng đợi 1.325 đơn và chưa kiểm quyền nhân viên.

Bốn ca thuần mới đã đăng ký trong `kiem_thu/chay.py`: tổng 2713 đạt local.
Con số 2709 trước đó là bộ cũ, chưa gồm tệp UOM mới vì thiếu đăng ký.

## Xuất danh mục để đối chiếu

`vagabond.khung.staging.xuat_uom.xuat(tep)` chạy qua CLI trên site được phép
đọc, bằng Administrator/System Manager. Chỉ đọc Item/UOM Conversion Detail,
phân trang theo tên trong DB, xuất mã/đơn vị/hệ số; không có endpoint mới,
không đổi danh mục và không ghi đè tệp bằng chứng. Dùng tệp này làm đầu vào
`ra_uom`, tự bổ sung quy ước từng mã đã được duyệt vào bản làm việc riêng.
Kiểm modified chỉ phát hiện thay đổi nhìn thấy trong transaction, không
chứng minh chặn mọi giao dịch đồng thời/raw SQL; phải đối chiếu lại trước
một đợt sửa danh mục. Công cụ chưa chạy trên site thật.

Theo comment mới của #252, nhánh `codex/227-252-dong-bo-va-gram` đang giữ
phần 14 mã nguyên liệu/BOM; không sửa chồng từ #257. Chỉ nhận quy đổi đã
merge và xác minh, không suy rộng quy ước của 14 mã ra toàn bộ danh mục.

## Phụ thuộc vừa phát hiện cho ca Nhận hàng

`bep/00-nen.js` giữ COMPANY cố định, còn bench_thu dùng công ty Vagabond Kiem.
`doReceive` trong `03-kho-chung-tu.js` gửi COMPANY vào cửa lan_nhan. Cần dựng
công ty thử tương thích hoặc cấu hình công ty app đúng thiết kế trước ca
xuyên luồng. Không sửa payload ở driver để che lỗi, không dùng company thật
với chứng từ thật làm nền. Chưa sửa app hoặc thay cấu hình production.

Đã viết `nhan_hang_ci.py` tạo công ty tổng hợp có tên tương thích hằng app,
hai kho và một món thử, nhập30 rồi yêu cầu50. `kiem_nhan_hang.cjs` thao tác
qua phân hệ Đặt hàng, nhận50 phải bị NegativeStockError, ô số mở lại để sửa20.
Sau thành công mở trang mới, số còn phải nhận30 và không còn khoá chờ.
CLI cuối kiểm MR, số phiếu kể cả nháp rỗng, dòng không mất liên kết, SLE và Bin.
Review đã sửa race bấm lại chi tiết cũ ngay sau POST. Chưa runtime, chưa kiểm
role nhân viên; chưa thay thế toàn bộ kịch bản mất phản hồi/gửi trùng.

## Hoàn tất sản xuất

`san_xuat_ci.py` dựng BOM/lệnh thử2 bánh và10 nguyên liệu. Driver bấm Hoàn
tất trên app, nhập2, chờ màn tem, mở lại lệnh đã xong và kiểm không còn nút
hoàn tất. CLI kiểm một phiếu ghi sổ, SLE trừ2/nhập2, GL cân, giá trị kho
không tự tăng/giảm, gói lô đủ2 và Bin. Chưa kiểm tạo lệnh/chọn BOM trên UI,
chưa kiểm role bếp hoặc hoàn tất từng phần; không nhận toàn luồng đã đủ.

## Runtime đầu tiên

CI run34359614912 trên5304ec4: dựng/migrate và tích hợp hai lượt đạt, browser
chưa mở vì Settings.validate chặn fixture thiếu kitchen_lat/kitchen_lng.
Đã bổ sung toạ độ giả1/1 trước save thật; không tắt validation. Cần chạy lại
trên SHA mới, chưa coi sửa code là bằng chứng runtime đã đạt.

Mốc đồng bộ: đã gộp main5bd5d4e (PR259) vào nhánh, giữ phần14mã/BOM của
nhánh kia. CI5304ec4 trước đó chạy107/107 hai lượt, sạch rollback; đây là
bằng chứng SHA cũ, không thay kiểm trên nền main mới. Runner browser nay
thu kết quả từng cửa riêng ngay cả khi một cửa lỗi, và vẫn trả exit1 nếu
bất kỳ cửa nào lỗi. Không dùng việc chạy tiếp làm miễn trừ cổng.

Run34361298751 trên35f2c85:116/116 tích hợp hai lượt sạch, browser10/10
không mở được. Web.log và ảnh xác nhận HTTP404, không có API nghiệp vụ.
Gốc là `trang.dong_bo()` cố ý không tạo Web Page mới, nên CI trắng chưa có
trang `bep` cho hook route trỏ tới. Fixture gateway nay dựng `bep` và
`kiem-banh` bằng `trang.doc_mot`/Document.insert rồi reload kiểm byte nội
dung, sau khoá CI. Không thay chính sách migrate production. Smoke kiểm
HTTP trước selector, ghi lỗi từng ca và lưu HTML để không chờ10phút chỉ
vì404. Review mã và gate local đạt, cần runtime SHA kế tiếp.

## Đường UI cho hai ca tiếp theo

Đã đọc trên main5bd5d4e và nhánh35f2c85:

- Hàng tặng: `/duyet-don-hang-tang`, mở `[data-dtgm]`, bấm
  `[data-dtgok]`, nhập `#hqIn`, xác nhận `[data-hqok]` gọi
  `hang_tang.duyet`. Cửa này chỉ duyệt, chưa ghi sổ.
- `/hoa-don-ban` mở `[data-hdb]` tới `scrDsView` trong
  `08-doanh-so-sales.js`. `#dsvChot` lưu thông tin người mua rồi gọi
  `ban_hang.chot_mot_don`. Cửa này cần custom_pancake_id kể cả khi nguồn
  Sales không phải Pancake; fixture phải dựng đúng dữ liệu, không sửa request.
- `chot_mot_don` submit/commit rồi gọi `_tu_xuat_hddt`. Không thay helper
  này bằng mock thành công. Ca kiểm phát hành phải có HTTP stub M-Invoice
  và kiểm payload; ca chỉ ghi sổ phải ghi rõ chưa kiểm phát hành, dùng cấu
  hình site thử tắt tự xuất. Mọi đường vẫn giữ khoá kết nối ngoài.
- Ca tặng dùng bánh từ ca hoàn tất sản xuất, kiểm SLE và 64181 theo giá
  1.000 mỗi bánh, tách VAT vào64182/33311; không lấy giá bán làm giá vốn.
  Kiểm sản xuất phải chạy trước khi tặng thay đổi tồn của cùng món.
- PR250 tại047c024 vẫn Draft/chưa merge, còn xung đột với main tại lúc
  kiểm. Ca hủy/bỏ đối chiếu cần tích hợp nhánh đó trước khi nghiệm thu trạng
  thái mới. Không nhận main đã có nhãn Đã duyệt, cần kiểm tra lại và không
  viết một bản sửa trạng thái song song trong PR258.

Các mục trên mới là đường mã đã xác minh, chưa phải ca browser đã viết/chạy.

Đã viết `hang_tang_ci.py` và `kiem_hang_tang.cjs`: dựng đơn tặng nháp dùng
hai bánh từ ca sản xuất, duyệt và ghi sổ qua app, tải lại chứng từ để kiểm
Đã chốt. CLI đối chiếu toàn bộ tài khoản/giá trị GL, SLE đúng kho/-2/-2.000,
VAT160 và tồn cuối0. Chạy sau kiểm sản xuất. Cấu hình thử tắt tự xuất HĐĐT;
không mock helper nghiệp vụ. Review mã và cổng local2724 đạt, chưa runtime.
Chưa kiểm tạo đơn/hủy/thuế hỗn hợp qua UI hoặc M-Invoice, chưa dùng role Sales.


### CI ea86fc7 và chuẩn bị số đo mạng

- Run34365834517 kết thúc failure: fixture khách đã qua, nhưng kho thử chưa có Warehouse.account nên hang_tang_kho.kiem_kho chặn trước insert SI. Bộ tích hợp116/116 hai lượt đã qua, chưa tới browser.
- Dựng tài khoản Stock/VND/Asset riêng và gắn ngay khi tạo hai kho fixture, trước mọi SE. Giữ validation của app và core.
- Smoke bổ sung thời gian nhận đầy đủ phản hồi API, TTFB và số byte body/header từ Playwright requestfinished. Chỉ lưu path/metadata, không body/cookie/query. Lỗi đo ghi riêng; các số này là chẩn đoán một lượt, chưa phải baseline hay chứng minh tối ưu.
- Ba màn cần benchmark vẫn là Vận đơn/Kiểm bánh/Hồ sơ thanh toán. Kiểm bánh tự gọi đồng bộ khi mở; phải dựng hợp đồng provider estimate_delivery_date và inserted_at trước khi đo, không dùng dữ liệu production.


### Chuẩn bị kiểm màn Kiểm bánh

Nguồn thử nhận hai trường ngày độc lập estimate_delivery_date và inserted_at; ca thuần chứng minh đơn giao10/09 tạo08/09 không được trả vào nhóm tạo10/09. Trường lạ hoặc thiếu ngày trong fixture vẫn lỗi. Driver kiem_kiem_banh.cjs mở trang thật ở390/1280px, đợi API đồng bộ thành công và màn ngày trống, bắt lỗi JS/API/cảnh báo nguồn, giữ screenshot và trace. Chạy sau verifier vận đơn để không nhiễu ba bước HTTP của ca dời ngày. Đây chỉ là smoke trên dữ liệu tối thiểu, chưa baseline/nhập tồn/chốt ngày hoặc quyền nhân viên.


### Nền Desk cũ và lỗi boot CI47

Log trực tiếp job102518466756 cho thấy nhan_su.khoi_dong500, fallback Item Group get_list417, rồi đợi header mỗi màn60giây. Nhóm hàm cùng đọc custom_bep_phu_trach; repo chỉ tham chiếu mà không khai tạo trường cũ. Đọc Desk thật (chỉ đọc) ngày09/09 xác minh Custom Field Item/Item Group-custom_bep_phu_trach: Select, không bắt buộc, options dòng đầu rỗng rồi Bếp Pastry/Bếp Baker/Bếp Lab. Nền CI dựng hai trường nếu thiếu, kiểm cấu trúc nếu đã có và gọi khoi_dong trước khi chạy browser. Không đổi schema hoặc dữ liệu site thật. Đây là hai trường cần thiết đã xác minh, chưa phải snapshot đầy đủ cấu trúc production.

### CI48 và snapshot cấu trúc cũ

CI48 terminal failure: thiếu nhiều trường Desk cũ và hai DocType làm API danh sách417/500/404. Đã đọc metadata thật qua SELECT ngày09/09; cau_truc_cu.json giữ21trường và4DocType gồm2bảngcon, cùng DocPerm đã đọc. Gateway tạo bảngcon trước, kiểm cấu trúc/quyền sau reload, không ghi đè DocType sẵn có. Không phải full export: chưa có workflow, Server Script hay Custom DocPerm; cột workflow_state không thay workflow. Kiểm bánh ngày trống390/1280 đạt740/706ms, chưa baseline. Thay đổi nền CI chưa có runtime mới.

### CI50 và ca thanh toán qua app

CI50 đã qua migrate/tích hợp rồi dừng ở schema: nen_bench tạo Sales Invoice.vgb_huy read_only0, trái Desk read_only1. Sửa nguồn fixture thành1, giữ guard. Thêm fixture/driver/verifier thanh toán: chọn BT và ghi PE qua app, bỏ đối chiếu lúc còn PE phải lỗi, huỷ riêng PE qua Desk (không Cancel All), bỏ đối chiếu, đọc lại Đã duyệt/đã trả0/ngày rỗng/BT chưa phân bổ rồi cùng BT ghi nhận lại. Verifier kiểm đúng PI/Supplier/tài khoản ngân hàng/công nợ, GL12345 và phiếu cũ không còn tác động. Đã nối runner; chưa có runtime. Chưa kiểm role nhân viên, nhãn cảnh báo hiển thị hoặc thư trùng, chưa coi đủ nghiệm thu5luồng.

## CI51: xác nhận ngân hàng và cấu trúc cũ

- SHA 19f7173f95dc29b7561e539330a37be31d5a1d27, run 34373843267: tích hợp 141/141 x2, sạch. UI Nhận hàng và Vận đơn đạt cả browser/DB; Kiểm bánh mở ngày trống đạt hai khổ. Không phải baseline hiệu năng.
- Browser vẫn đỏ: thiếu User.custom_bo_phan, Item.custom_han_dung_gio, SI.vgb_ma_tham_chieu và nhóm vgb_huy_ly_do/boi/luc. Đọc SELECT metadata site, commit tắt; bổ sung đúng 36 trường vào snapshot thử, không sửa production.
- Payment driver đã ghi nhận và kiểm chặn bỏ đối chiếu, nhưng dừng ở xác nhận thứ hai của ERPNext before_cancel. Đối chiếu payment_entry.js tại pin de591661b9ba0bd3f62ac25b99b5c85c723515f6: xác nhận hủy trước, rồi hỏi tự gỡ BT. Driver mới kiểm đúng BT fixture trước xác nhận lần hai; không bỏ qua cửa core. Review độc lập không thấy blocker, còn phải chạy runtime.
- Artifact 10113668021 SHA256 02bfb10b48649f69e01dccf4cb1510b94c1df37e6173ea569c803c9ff878f931. Chưa đủ năm luồng UI, chưa merge/deploy.
## Kiểm quyền bằng tài khoản tổng hợp

`vai_ci.py` dựng bốn User thử trên CI: Sales User, Stock User,
Manufacturing User, Accounts User. Mỗi tài khoản chỉ có một vai nghiệp vụ;
không sao chép tài khoản/email công ty và không gửi welcome email.
`kiem_vai.cjs` đăng nhập HTTP riêng từng người, kiểm đúng vai từ API boot,
kiểm Kế toán thấy hồ sơ fixture và ba vai còn lại bị chặn đúng lý do.
Đây mới là kiểm quyền đọc danh sách tài chính, chưa thay UAT ghi chứng từ
theo từng vai hoặc kiểm các tổ hợp quyền nhân viên thật. Cần runtime CI.
## CI52: thanh toán UI và dữ liệu đạt

Run34376822980 trên9d66981:141/141 x2 sạch. Nhận hàng, Vận đơn và Thanh toán
đạt browser+DB. Thanh toán đi qua hủy PE trên Desk, bỏ đối chiếu, về Đã duyệt,
ghi nhận lại bằng PE mới; đúng BT/reference/GL12345 và công nợ0.
Artifact10114681564 có SHA256
`bb28597c755c40b5c2d5d32c55866ad3afdb9f59999648f445e699246f1d1c14`.

Còn lỗi schema User.custom_kho_phu_trach, Batch.custom_lenh_san_xuat,
SI.vgb_lan_sua. Đã đọc SELECT metadata site và thêm đúng cấu trúc vào snapshot.
Sản xuất còn trả417 tại hoan_tat_phieu, chưa biết nguyên nhân vì driver cũ
short-circuit trước r.json(), đóng trang khi body chưa vào trace. Driver mới
đọc/lưu body trước kiểm status. Không nhận thêm schema là đã sửa lỗi sản xuất.
## CI53: lỗi giờ máy khách khi hoàn tất sản xuất

Artifact10115311432 SHA256
`2869c9230936861dad98dc6277b83bf2a4f684bbdaaa0b512ab9f66788247492`.
Bốn ca quyền HTTP đạt. Sản xuất gửi posting_time16:54:22 trong khi lệnh
fixture tạo23:53:58 theo site Việt Nam; API trả NegativeStockError. Browser
UTC đã đặt phiếu xuất trước nhập. Hàng tặng sau đó bị chặn đúng vì chưa có bánh.

Hoàn tất app chỉ ghi nhận ngay, không có ô chọn ngày lùi. Cửa máy chủ nay
tắt set_posting_time để ERPNext TransactionBase.validate_posting_time lấy giờ
site (pin de591661, erpnext/utilities/transaction_base.py). Không chỉnh múi
giờ browser để che lỗi: driver giữUTC, fixture kiểm siteAsia/Ho_Chi_Minh,
verifier kiểm thời điểm xuất không trước phiếu nhập và giữ toàn bộ SLE/GL.
Chưa có runtime bản sửa. Chưa thay các cửa nhập trực tiếp/Desk hoặc chuẩn
hoá mọi chỗ dùng nowStamp trong app.


## CI54: năm luồng qua browser và kiểm DB

Run34380254862, SHA328471e634a705ebad0b0b7e6cc1201b3836aa72.
Artifact10115914394 SHA256
`738ae53794586d7abb21f98342c64bddcbdff53331ff37fe04bbc25c350ef97f`.
Tích hợp141/141 hai lượt. Sản xuất2 bánh qua API200; verifier kiểm thời
điểm nhập/xuất, SLE/GL/bundle đạt. Đơn tặng tiếp theo giá vốn2000/VAT160/nợ0.
Nhận hàng20, vận đơn đổi ngày và thanh toán ghi/hủy/bỏ đối chiếu/ghi lại đều
qua browser và DB. Đây là dữ liệu CI ít dòng, chưa là baseline hiệu năng.

Bổ sung tiếp: API Desk `vgb_gd_sepay` trước đây thiếu ở CI khiến ô tra giao
dịch báo lỗi nhưng luồng ghi sổ vẫn qua. Snapshot `sepay_cu.txt` đọc bằng
SELECT, hash đối chiếu trước insert và sau reload, chỉ dựng qua khoá CI.
Driver nay kiểm cả response API và câu hiển thị chưa có giao dịch của đúng
đơn thử. Không giả response. Chưa runtime phần bổ sung này.

Giới hạn: ca SePay này chỉ kiểm đơn không có giao dịch. Script legacy có
allow_guest=0 nhưng từ code chưa thấy kiểm vai hoặc quyền đọc hoá đơn trước
get_all Bank Transaction. Đây là nghi vấn quyền cần tái hiện riêng, không
nhận script an toàn và không dùng snapshot làm patch triển khai production.


## Đo API và truy vấn trên CI

`do_truy_van.py` chỉ cài sau khoá site CI, không phải hook production.
Mỗi request `/api/method/` ghi path, status, số lần Database.sql, sql_ms
và ms; không lưu SQL/parameters/body/cookie. sql_ms là thời gian toàn hàm
Database.sql (gồm xử lý Python), ms kéo dài tới đọc/đóng iterable WSGI,
không phải riêng thời gian nghiệp vụ. ContextVar tránh trộn request threaded.
Kiểm đồng thời2/7truy vấn, lỗi SQL và ngắt/đọc hết iterable trên API/ngoài API.
Review bắt double-close khi dùng yield from, đã thay vòng for và thêm ca ngắt.
Chưa có baseline tải đại diện hoặc so sánh trước/sau tối ưu.


## Tải thử Vận đơn và nguồn apt CI56

Hai mức100/500VD,3dòng món mỗi đơn, ngày riêng, khôngpancake_id, chỉ dựng
sau tất cả ca chức năng/quyền đạt. Browser390/1280, mỗi khổ5lượt, xác nhận
đủ ID cả API vàDOM rồi tìm mã cuối. Thời gian gồm lệnh driver/đọc JSON/
đối chiếu/polling, không phải render thuần. lenh_driver không phải số chạm
của người dùng. Chưa có runtime20lượt hoặc phân bố tải site đã xác minh.

CI56 hai attempt dừng tại apt GoogleChrome Packages.gz Hash Sum mismatch,
trước bench. Runner dùng Chromium của Playwright, không cần nguồn Chrome.
Chỉ comment dòng deb/deb-src URL GoogleChrome trong *.list trên runner tạm;
không tắt hash/chữ ký và không bỏ qua apt failure. Nếu runner dùng .sources
thì vẫn fail để xử lý theo nguồn mới. Bản này chưa được kiểm runtime CI.


## CI57 và bộ đo đủ ba màn

CI57 run34386953007 vượt apt, migrate và tích hợp. Benchmark dừng tìm mã:
artifact10118614892 SHA256
`62bf3e7514f4fb6cac38e4963485ee39af1450315a4df66f959f40a48abd5903`.
Query DO257-100-0099 khớp cả VD-2026-00099 (display0097) và display0099,
vì tìm từng token trên nhiều trường. Đổi fixture sang token Z0099 để không
trùng mã nội bộ; không đổi thuật toán tìm app. Driver giữ trace/HTML khi lỗi.

Nối Kiểm bánh50/200 dòng và Hồ sơ300 hoàn ứng nháp sau hồi quy chức năng.
Mỗi màn5lượt x2khổ, so API/DOM IDset và số tiền/số bán. Hồ sơ dùng fillEnter
đúng UI. Kiểm bánh ghi số lần HTTPstub theo request để phân loại đọc nguồn/
không đọc nguồn; header chốt khi trả JSON, không áp dụng suy luận streaming.
Mức tải là tổng hợp, Hồ sơ chỉ nháp, chưa đại diện trạng thái hỗn hợp/site.
Các benchmark độc lập tiếp tục khi một màn đo hỏng, nhưng CI cuối vẫn đỏ.
Chưa runtime bản gộp; chưa kết luận tăng tốc hoặc giảm số chạm thực tế.


## CI58: đủ60lượt, hoàn thiện hợp đồng nguồn trước tối ưu

Artifact10119611564 SHA256
`1b99e47c746ad60b5243650999886eccc944b281b3da43378d148912f34c366a`,
SHA c1de8099726674aefa3a10e7fd8f3fba33a343ec. Cả60lượt đo đạt.
Mobile medianVD100/500=308.1/599.4ms, HS300/1=430.2/295.7ms.
Bao driver/đối chiếu, chưa là số production hay chứng minh đã tăng tốc.

KB50/200 lượt đầu có52/152lần gọi nguồn, lần sau0: loopbùảnh tra từng mã,
cache6giờ giữ50mã dùng chung giữa hai tải. Stubcũ chưa hỗ trợ variations,
helpercatchrồi fallbackDB nên chưa phải mô phỏng source hoàn chỉnh.
Bổ sung danh mục tổng hợp có tên/khôngảnh cho đúng200mã thử. Mọi lời gọi
ngoài hợp đồng (kể cả khôngGET) ghi vết trước raise để helpercatchkhôngche.
Tổng hợp cuối CI yêu cầu60lượt đủ, SHAđịnhdạng hợp lệ và lognguồn khôngngoài
hợp đồng. Provenance vẫn cần đối chiếu hashartifactnguyênbộ, công cụ không
phát hiện trộn file thủ công. Báo cáo nhóm theo tải/khổ/số lần nguồn,
min/trungvị/max, không p95 với5mẫu. Chưa runtimebảnbổsung.


## Thử tối ưu tải Vận đơn

BaselineCI59 artifact10121299214 SHA256
`46b14536ebe6f4164c0d05e1a9da1fe99d23181293c87a3b2c78375e4c65dfe9`,
SHA273d8f23776cc9fc2c2d2311f0d314852b12c801. Bộnguồnhoànchỉnh/gateđạt.
MedianmởVDmobile100/500=286.6/520.2ms; desktop273.9/550.2ms,
5lượt mỗi nhóm. Đây là mốc so cùngdriver/core, vẫn có nhiễu máyCI.

vdNapDanhSach tải đồng thời danh sách/bộlọc/shipper/điểmpickup vì cácAPIđọc
độclập. Giữ quyền/errorởmáychủ, fallbackdanhmục nhưcũ; primaryfailvẫnchặnmàn.
Helpertestkiểm4requestbắtđầutrướcreply, cache/optionalerror/primaryerror.
Reviewer khôngblocker; chưa chứngminh nhanhhơn cho tới CIcùngfixture.
Raceđiềuhướngnhanhgiữahai ngày là giớihạn cósẵn cần kiểmtiếp, không nhận
helpertest là UAT điều hướng. Cần phiênbản mới trước phát hành sau đủgates.


## Giảm giải mã dấu kiểm đếm

`bang()` gọi `_nguon_ton_cho_man`: cùng JSON nguồn được đọc1lần/dòng,
trướcđây6lần. Khôngđổi dữliệu/audit/nhãn/mặcđịnh. Ca thu_doc_nguon lấy
cáchàmthuần thật từAST, kiểmnguồncũ/rỗng/hỏng, nhãnbaô, người/lúc,
khôngđổipayload, lỗi kiểuconkhôngbịnuốt thêm và đúng1lầnparse.
Đã so biểu thức cũ trên6đầuvào, chưa kết luận cải thiệnms cho tới bench.


### Đọc tên trong danh sách hồ sơ

Danh sách dùng bộ nhớ riêng cho từng request để mỗi mã người chỉ qua `_ten_nguoi` một lần. Giữ nguyên resolver hiện hành, gồm fallback Employee và Redis cache sẵn có; không cam kết lần tải sau đọc lại DB. Ca kiểm 900 lượt gọi với 3 mã còn 3 lần vào resolver, request mới không dùng bộ nhớ của request trước. Đây là giảm công việc lặp, chưa là bằng chứng giảm thời gian site thật.

CI60 tại SHA 5aefb3e22e748556eaca3f756bb496282cb4d108 đạt. So CI59, trung vị mở Vận đơn mobile 100/500 dòng từ 286.6/520.2 xuống 223.6/455.9 ms; desktop từ 273.9/550.2 xuống 242.7/420.8 ms. Mỗi nhóm 5 lượt. Hai màn chưa sửa cũng nhanh hơn trong CI60 nên chưa quy chênh lệch này hoàn toàn cho code, cần đối chứng cùng runner. Artifact 10122046864 có SHA256 a7a0aaad75cb40d92b34c4ad8e7fde93740b712a7fb44dadbb445a35d2cd9e40 đã đối chiếu.
