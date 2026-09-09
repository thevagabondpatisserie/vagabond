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

Chốt ba màn theo tần suất thực; ứng viên là vận đơn, nhận hàng/kiểm bánh,
hồ sơ thanh toán. Cùng dữ liệu, role, máy/mạng và số lượt; tách tải lần đầu
và cache. Báo số thao tác, p50/p95 thời gian tới dữ liệu dùng được, số API,
SQL và dung lượng. Chưa có số đo mới nên chưa tuyên bố tăng tốc.
Chỉ tối ưu sau baseline; phép kiểm hồi quy phải bắt lại lỗi cũ.

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
