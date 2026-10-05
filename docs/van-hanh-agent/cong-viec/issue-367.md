# Cập nhật 05/10/2026 - Minh Vũ, Marketing và lỗi luồng khách

Owner Codex, branch `codex/web-editor-toan-bo-chu`, PR436 mở rộng trên main
`fbcb324cc` v576. Phiên bản dự kiến v578 (v577 đang dùng ở PR422).

- In store: chọn điểm theo mã thật trong API, lọc Item Group, giữ quầy hết
  hàng nhìn thấy; không gán TCV/NVHTN vào kho bằng tên đoán.
- Ưu đãi/tuyển dụng: thêm hai loại nội dung trong CMS hiện có; không tạo
  DocType. Có ảnh, chữ/nút/link, nhóm, thời hạn; việc làm thêm địa điểm,
  hình thức, email. Nháp mới mặc định ẩn; nhân bản cũng ẩn. Công khai loại
  nội dung ẩn/hết hạn, chương trình tương lai ghi Sắp diễn ra, ngày VN.
- Editor tìm theo tên/mã/nhóm/nơi làm, lọc trạng thái có đếm; đổi ảnh bằng
  upload có sẵn hoặc URL. Preview tự mở đúng chuyên mục, xem được bản ẩn;
  Lưu nháp/Xuất bản, revision, lịch sử, Undo/Redo giữ luồng có sẵn.
- Headline gọn, dùng Vagabond Sans gốc. Có JPEG tay làm bánh do AI tạo,
  ảnh minh hoạ mặc định thay được; không phải ảnh nhân sự thật.
- Giỏ: giữ bản đang soạn trong sessionStorage 24 giờ, loại dữ liệu giá
  cũ khi phục hồi, không nhớ checkbox đồng ý/quote phí. Sửa một dòng bánh
  không cộng thêm số lượng, giữ nguồn today/order và dụng cụ. Bánh mùa vụ
  phục hồi sau API để lấy giá hiện tại, không có lời chúc/phụ kiện riêng.
- Kích thước chi tiết theo đúng tab; giờ hết hạn bị vô hiệu; tóm tắt chưa
  chọn giờ không hiện như đã xác nhận. Nến object-fit contain, 5 cột mobile,
  tăng nút +/-/Bỏ/Xoá; yêu cầu số nĩa/dĩa được đưa vào ghi chú đơn.

Bằng chứng: `/Users/jin/Documents/ChatGPT/ERP/output/web-order-20261005`.
Browser fixture local: thêm nhanh Candle 650.000, sửa lời chúc + nến23 +
6 nĩa -> vẫn 1 bánh, 684.000; reload giữ đủ. Mobile390: nút nến65x82,
ảnh57x64 nằm trọn nút; ảnh, tiêu đề Editor đổi ở iframe, Undo khôi phục;
chọn NVHTN fixture rỗng hiện giải thích. Không gửi đơn thật.

Cổng local trước chốt: 4.061 ca tầng khung đạt, không hỏng; 2 ca PDF #247
chưa chạy vì Python hệ thống thiếu pypdf; các cổng còn lại exit0. Bundle
khớp. SHA cuối, CI/bench/Claude theo biên nhận PR, không dùng kết quả SHA cũ.

**Chưa hoàn tất để phát hành:**
- API live GET phi_giao ngày05/10, địa chỉ cửa hàng công khai: ok0,
  ly_do=ahamove_loi. Nút thử lại không phải sửa gốc dịch vụ; cần log Ahamove
  phía server để phân biệt auth/service/response. Không thay phí/credential.
- Trang chính sách cần nội dung thật được duyệt và xuất bản. Link hỏi thông
  tin bảo mật là đường hỗ trợ tạm thời, không thay thế chính sách công khai.
- JPEG mới chờ duyệt; mẫu ưu đãi/job chỉ có ở fixture, không xuất bản giả,
  không kích hoạt voucher/giảm tiền. Discount thực cần quy tắc/hạn mức.
- CI/bench exact SHA, Claude review và UAT production còn chờ. Không merge,
  deploy, migrate, gửi email trong phiên này khi các cổng chưa đủ.

# Cập nhật 04/10/2026 - mở toàn bộ chữ theo duyệt trực tiếp

Anh Việt yêu cầu “cho sửa hết trong editor”, gồm bốn dòng pháp lý bị khóa
ở PR431/432. Codex mở lại tên pháp nhân, MST và hai địa chỉ qua danh mục
Nhãn và câu chữ, marker textContent hiện có; giữ fallback tĩnh trong HTML.
Chỉ đổi chữ hiển thị, không ghi Company/Tax ID hoặc chứng từ ERP. Quyền
Marketing, nháp/xuất bản/lịch sử không đổi. Không đổi font trong lượt này.

Nền main b8a2bd142 (v570), branch codex/web-editor-toan-bo-chu.
PR431 đã đóng; PR432 đã merge7544931a2 và code mới đã hiện trong HTML live
(câu chào mới, escape tên phụ kiện), nhưng bốn nhãn vẫn đang khóa trên live.
Ca cũ cấm sửa được thay bằng kiểm validator nhận đủ bốn nhãn, public snapshot
nhận chữ, fallback trống và marker escape; 10/10 ca tập trung đạt.
Cổng/SHA cuối theo PR tiếp nối; không dùng CI432 làm kiểm cho thay đổi mới.

# Issue 367: website đặt bánh và Marketing Studio

## Hiện tại 03/10/2026: chữ, font và Editor

Owner: Codex, nhánh `codex/web-order-noi-dung-day-du`; Claude review độc lập.
Anh Việt đã duyệt giao diện JPEG, yêu cầu lời chào chính xác "Chúng tôi mong
được phục vụ cho quý khách", xưng "chúng tôi/quý khách", headline dùng
Vagabond Sans gốc và Marketing sửa được nội dung web. Bản trước ở dưới là
lịch sử PR372, không dùng vai trò hoặc trạng thái chưa deploy cũ cho phiên này.

- Mở hơn 400 chỗ chữ qua danh mục có khóa, tìm kiếm theo màn; placeholder,
  nút, thông báo có số, giỏ, đặt bàn, thành viên, biên nhận, chính sách.
- Tên/mô tả/tầng hương/khẩu phần theo mã bánh; tên hiển thị không đổi mã
  đặt hàng, giá hoặc tồn. Nội dung fallback 24 mã cũng tìm được trong Editor.
- FAQ, nhân bản khối ẩn, hoàn tác/làm lại 60 bước, phục hồi bản chưa lưu
  theo người dùng/tab, tải JSON; lưu/xuất bản giữ kiểm revision hiện hành.
- Font có sẵn tại public/mau_in/VagabondSans-Regular.otf, đã đọc cmap, đủ
  dấu câu chào; không cần dựng hoặc thay font bằng bản mô phỏng.
- Patch chuyển đúng các câu mặc định cũ và thêm 4 khối hỗ trợ. Chuyển
  nháp/công khai riêng, giữ lịch sử, không tự bật chính sách còn chỗ trống.
- Khắc phục finding audit: tra_khach chỉ trả địa chỉ khi cookie OTP xác
  thực đúng số. Guest vẫn tự nhập địa chỉ mới. Không gọi Pancake nếu thiếu
  quyền; request cũ về chậm không thay địa chỉ của số mới.

Kiểm trước tích hợp main mới: cổng kiem_truoc_deploy.sh exit 0, 3.865 ca
tầng khung; kiểm trình duyệt 390 px không tràn ngang, tên bánh sửa trong
Editor đổi ngay ở preview, Undo khôi phục, giữ nguyên giá/lời chúc/lịch nhận.
Đã thêm ca bench Frappe thật cho nháp/xuất bản/revision, chỉ chạy site
bench-ci.localhost. SHA cuối, CI, bench và Claude còn chờ ở PR phát hành.
Ảnh local chỉ là chứng cứ preview, chưa phải site production.

Giới hạn: giá, tồn, ngày giờ, liên hệ và cấu hình nghiệp vụ lấy từ hệ thống;
Editor chỉ soạn chữ. Voucher WEB50 trong bộ duyệt là đề xuất, chưa kích hoạt
chi tiêu hoặc hạn mức. Bản này chưa thay luồng checkout thành ba màn riêng,
chưa có lập lịch xuất bản hoặc trạng thái vận đơn mới. Các mục đó theo
nghiệm thu tiếp của Issue367, không nhận hoàn thành từ giao diện phác thảo.

### Review PR424

PR: https://github.com/thevagabondpatisserie/vagabond/pull/424.
Trên e4171bc999199585636f6c4e8fe00302ed47987e, CI và bench hai lượt đạt
(run37123417221, run37123417230). Claude run37123464175 hoàn tất bước model
nhưng chưa có kết luận đăng lên PR; log có 5 permission denials, không coi
check xanh là review đạt.

- R1: escape nhãn tại nhánh lỗi mã số thuế, địa chỉ rỗng, phí giao và quầy;
  escape cả tên công ty/địa chỉ trả từ API. Canary tái hiện trên SHA trên,
  không còn tạo thẻ HTML sau sửa.
- R2: sự kiện vgb-nhan đã làm mới cards/cart ở SHA trên; bổ sung phụ kiện,
  tình trạng và hộp hàng mùa đang mở. Ca hành vi giữ size/giá/nến/lời chúc/
  scroll; bản cũ giữ nội dung mùa cũ, bản sửa nhận đúng chữ mới.
- Nhóm lọc Editor nằm gọn theo hàng; tăng cỡ headline Vagabond Sans cho
  dễ đọc. Ảnh local08-editor-tim-chu-preview.png, chưa là production.

Merge/deploy/migrate/live vẫn chờ kết luận độc lập và kiểm SHA cuối.

## Lịch sử PR1 quảng cáo Meta


- Nguồn: issue #367, sáu điểm Claude chốt 24/09, quyết định phí giao của anh
  Việt 24/09, ba bản nháp chính sách anh Việt duyệt 25/09, mục 8 lối đăng nhập.
- Owner: Claude implement (anh Việt giao 25/09: "làm PR 367 thật triệt để, cho
  Codex review"). Codex review. Nhánh `v529-don-web-367`, nền main 6b9922b.
- Công của Codex ở c59e139f, 0d69cac3, 88b8699d, d122f410 KHÔNG có trên GitHub
  (Codex Cloud không đẩy được), nên dựng lại từ main theo đặc tả trên issue.

## Đã làm, kèm bằng chứng

- Bản ghi bền `Vagabond Don Web` ghi và commit TRƯỚC khi gọi Pancake; chống
  trùng 15 phút theo khoá (SĐT, món, giờ nhận, nonce) có khoá tệp; Pancake mất
  phản hồi hay 5xx là Chờ đối soát, 4xx là từ chối, không bao giờ tự gửi lại.
- Token biên nhận 32 byte HMAC(khoá site, muối bản ghi, nonce), CSDL chỉ giữ
  băm; gửi trùng ra đúng đường dẫn cũ. event_id GuiDon và Purchase là uuid riêng.
- Tiền bánh máy chủ tính theo giá hồ sơ món; ngưỡng miễn phí trong Settings;
  tách phí khách trả và phí Ahamove; bốn trạng thái phí; Ahamove lỗi không thành 0.
- Trang /banh/xong/<token>: no-store, no-referrer, noindex, 404 thật khi token
  sai, tên viết tắt, không SĐT/địa chỉ/email; JS gỡ token trước khi nạp Pixel.
- CAPI: GuiDon sau khi lưu, Purchase ở hook on_submit Sales Invoice (khớp mã
  Pancake), hàng đợi, thử lại 3 lần, lỗi chỉ Error Log không token.
- Nhịp 5 phút ghép đơn Chờ đối soát với Pancake (đúng một đơn khớp SĐT, giờ,
  món); quá 30 phút báo nhóm Sales qua Lark (anh Việt chọn Lark 25/09).
- Ba trang chính sách trong Vagabond Noi Dung Web, patch gieo nháp nguyên văn,
  Marketing Studio sửa và bật hiện, chặn xuất bản còn ngoặc vuông, trang công
  khai qua sanitize_html bắt buộc, chưa xuất bản thì 404.
- Chân trang pháp nhân (HTML tĩnh), ô đồng ý, Pixel bốn mốc, phí giao dự kiến
  theo khu vực, số thứ tự lần hỏi phí, nút "+", ảnh ERP trước Pancake ở cả bốn
  nhánh qua `anh_web.chon_anh`, phông thường cho chữ Việt và số.
- Mục 8: gốc thật là tên mô đun `bien-tap-web.py` (Frappe chỉ tìm
  `bien_tap_web.py`), đo trên site: csrf-token mang nguyên văn `{{ csrf_token }}`.
  Đổi tên, thêm chuyển hướng đăng nhập, trang báo quyền, nút Đăng xuất.

Kiểm: bộ khung (chay.py -im), dung_app_bep --kiem, kiem_truoc_deploy.sh, giả lập
CI không requests; đột biến 20 trên 20; ảnh 320/375/390 từ tệp repo với API
giả (không phải site thật). Số liệu cụ thể ở comment bàn giao trên PR.

## Còn lại và bàn giao

- Chưa chạy bench `vagabond.khung.kiem_that.cua.chay` (ca mới
  `kiem_that/thu_don_web_367.py`), chưa kiểm site thật, chưa merge, chưa deploy.
- /dat-ban và /thanh-vien cùng lỗi tên mô đun có gạch nối, ngoài phạm vi, chưa đổi.
- Toạ độ tâm khu vực là số gần đúng, chỉ dùng cho phí dự kiến.
- Marketing phải điền chỗ trống và xuất bản ba trang chính sách, anh Việt điền
  Pixel ID, token CAPI, email, webhook Lark trước khi chạy quảng cáo.
- PR2 (trang từng bánh, Open Graph, Meta Catalog) chưa làm.

## Vòng 2 (25/09/2026, Claude sửa theo rà soát Codex trên b03e43a)

- Ba trang chính sách 404: Frappe không truyền `defaults` của
  `website_route_rules` vào `form_dict`. Bỏ `defaults`, thêm
  `noi_dung_web.khoa_tu_duong(duong)` thuần, `www/chinh_sach.py` suy khoá từ
  `frappe.local.request.path` (dự phòng `frappe.local.path`); đường lạ hay
  chưa xuất bản vẫn 404. Ca mới nhóm J.
- `_bao_sales` chỉ đóng dấu `da_bao_sales_luc` SAU khi Lark trả nhận; thiếu
  URL hay gửi hỏng thì để trống để nhịp sau thử lại, có Error Log. Ca mới nhóm H.
- Nhịp `doi_soat_tu_dong` tách `_doi_soat_mot(r, dons, gan)`, mỗi bản ghi
  một `try` riêng, lỗi thì rollback và ghi log, bản ghi sau vẫn chạy. Ca mới nhóm H.
- `ghep_don_pancake` bỏ đơn Pancake trạng thái 6, 7 (huỷ, xoá), cùng luật
  với `kiem_banh` và `mua_vu`. Ca nhóm H mở rộng.
- Bench `kiem_that/thu_don_web_367.py`: tự gieo Item bánh có giá khi site CI
  trống (bench đỏ run 36148002675), tắt cờ `vagabond_kiem_that` trong
  `try/finally` quanh `khi_ghi_so_hoa_don` để hook thật chạy.
- Không đổi APPVER (vẫn 529, chưa phát hành), không thêm patch.
