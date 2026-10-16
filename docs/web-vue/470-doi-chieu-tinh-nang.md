# #470 - Đối chiếu trang đặt bánh cũ và Vue

Nguồn: [issue #470](https://github.com/thevagabondpatisserie/vagabond/issues/470).
Owner: Codex. Nền kiểm kê: `42cb9fb9a` (main v592, ngày 13/10/2026).
Một PR Draft xuyên suốt bốn giai đoạn; GĐ1 đã được Claude duyệt; GĐ2 đang bổ sung luồng khách. Chưa tráo
miền hoặc chuyển Editor. v593 là mốc dự kiến của
PR theo mục bắt buộc, phải đọc lại main trước khi chốt phát hành.

## Cách đọc bằng chứng

- **Có**: tìm thấy đường chạy trong code Vue, không đồng nghĩa đã nghiệm thu.
- **Một phần**: có code nhưng chưa đủ luồng hoặc chưa đủ kiểm hành vi.
- **Chưa**: chưa có bản Vue tương ứng. Không ghi ca kiểm backend thành ca UI.
- **K** là kiểm kho Vue thật trong Node, mạng/đồng hồ giả, không mount DOM.
- **D** là Chromium/Playwright fixture localhost: `cong_cu/kiem_web_vue_dom.cjs`, thao tác DOM thật, không gọi hàm kho để trợ giúp. Không phải site thật.
- **S** là kiểm cấu trúc/chuỗi; **B** là kiểm Python/API với giả lập.
- SEO/OG được ghi là yêu cầu nghiệm thu #470; chưa thấy OG/canonical trong vỏ Cũ cũng không biến nó thành hồi quy riêng của Vue.
- Giai đoạn 1 không tạo đơn thật, không đo production, không có ảnh mới.
  Các ảnh hay lời xác nhận ở PR cũ không được coi là ảnh nghiệm thu SHA này.

Các đường dẫn viết tắt dưới đây trỏ tới mã đang kiểm kê:

| Ký hiệu | Nguồn |
|---|---|
| Cũ | [trang/banh.html](../../vagabond/trang/banh.html) |
| Kho | [web_vue/banh/kho-banh.js](../../vagabond/public/web_vue/banh/kho-banh.js) |
| App | [web_vue/banh/app.js](../../vagabond/public/web_vue/banh/app.js) |
| Mẫu | [web_vue/banh/mau.js](../../vagabond/public/web_vue/banh/mau.js) |
| Thuần | [web_vue/kho/thuan.js](../../vagabond/public/web_vue/kho/thuan.js) |
| Chữ | [web_vue/kho/chu.js](../../vagabond/public/web_vue/kho/chu.js) |
| K | [hanh_vi/web_vue_banh.mjs](../../vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs) |
| S | [thu_web_vue.py](../../vagabond/khung/kiem_thu/thu_web_vue.py) |
| B | [thu_don_web_367.py](../../vagabond/khung/kiem_thu/thu_don_web_367.py) |
| Đơn | [don_hang.py](../../vagabond/don_hang.py), [don_web.py](../../vagabond/don_web.py) |

## Bảng đối chiếu khách

Tên ca dưới đây là tên hoặc phần đầu duy nhất để tìm trong tệp, không phải
cam kết bộ kiểm đã phủ toàn bộ thao tác ở hàng đó.

| ID | Tính năng ở Cũ | Vue hiện có, tệp/hàm | Ca kiểm chứng minh hiện có | Việc còn lại trước nghiệm thu |
|---|---|---|---|---|
| F01 | Có sẵn hôm nay, tồn Sales online | Có: Kho `napTon`, `banhHomNay`, `gioiHanNhan`; Mẫu tab today | K tồn; D lỗi tải -> hiện thông báo -> bấm tải lại -> có bánh | F21 đã chốt cách B; xem dòng F21 và nhật ký issue470 |
| F02 | In store D1 | Một phần: Kho `napQuay`, App `quayHien`, Mẫu danh sách quầy | D F02/F03: click quầy D1, đúng món riêng, còn12 | Chưa nghiệm thu dữ liệu site và ảnh Rocca ở GĐ4 |
| F03 | In store NVHTN | Một phần: cùng nguồn mảng `STORE.quay`, chọn `quayChon` | D F02/F03: NVHTN còn3, qua lại D1 không lẫn món | Chưa nghiệm thu dữ liệu site và ảnh Rocca ở GĐ4 |
| F04 | Đặt trước, size còn nhận | Có: Kho `banhDatTruoc`, `kichThuocDangBan`, `pick`, `pickSlot` | K `Giới hạn số còn nhận`, `Chưa tự chọn đủ ngày và giờ` | DOM chọn size/ngày; so giới hạn máy chủ, không chỉ computed |
| F05 | Hàng mùa vụ | Có: Kho `napMua`, `themHangMua`; App route in-season | K chặn quá số; D mở link mùa vụ, hàng hết khóa nút, hàng còn bấm thêm vào giỏ | Còn hết mùa giữa phiên; kiểm site/ảnh ở GĐ4 |
| F06 | Chi tiết bánh, ảnh, chọn size | Có: App `chiTiet`, `kichThuocDong`; Kho `moBanh`, `setSize` | D mở link CANDLE, đổi size, nhập lời chúc, bấm thêm giỏ; K nhiều size | Còn gallery và so Rocca |
| F07 | Phụ kiện, nến số, đĩa/nĩa | Có: Kho `toggleAdd`, `toggleNum`, `addToCart`; Thuần `hangGui` | K `hangGui gộp dòng trùng mã và phụ kiện theo số bánh` | D chọn nến2, nến xoắn, dĩa/nĩa -> giỏ -> payload; còn sửa dòng đã có |
| F08 | Lời chúc, bánh tặng, người nhận khác | Có: Kho `wish`, `CO.gift`, `CO.other`, `submitOrder` | D nhập lời chúc, người nhận khác và bánh tặng, reload giữ tên | D kiểm tên người nhận trong payload; còn assert tag bánh tặng |
| F09 | Giỏ tăng/giảm/xóa/sửa dòng | Có: Kho `cartQty`, `cartRemove`, `suaDongGio`; App `suaDongGio` | D tăng/giảm giỏ, tổng đổi rồi trở về đúng tổng cũ | Còn sửa phụ kiện và xóa dòng cuối trên DOM |
| F10 | Khôi phục giỏ hiện tại | Có: Kho `luuGio`, `phucHoiGio`, `lamTuoiGiaGio`, khóa `vgb-gio-v1` | D reload giữ giỏ/người nhận/MST/cách thanh toán; K storage | Còn storage bị chặn trên trình duyệt |
| F11 | Nháp cũ qua Vue và quay lại | Có: Kho `phucHoiGio` đọc dạng cũ, `luuGio` giữ tương thích | K `PR #462: nháp trang cũ khôi phục đủ ô` | D trọn vòng bản cũ -> Vue -> cũ giữ tên/lời chúc/giỏ cùng phiên; công tắc thuộc GĐ4 |
| F12 | Nhận tại quầy, điểm nhận do Editor cấu hình | Có: Kho `setMode`, `setPickup`, `capNhatDiemNhan`; App watch ND | B `v586 ... đơn tự lấy chỉ nhận điểm đang bật`, `v586b ... Marketing tắt hoặc đổi điểm nhận` | DOM chọn điểm/tắt điểm giữa lượt; đối chiếu địa chỉ máy chủ |
| F13 | Giao hàng, địa chỉ/gợi ý/ngoài vùng | Có: Kho `lookupPhone`, `goiYDiaChi`, `chonGoiY`, `quoteShip` | D gõ/chọn địa chỉ; K phản hồi gợi ý/toạ độ muộn bị bỏ | D ngoài vùng, gợi ý/chọn/sửa; phản hồi muộn kiểm K, chưa DOM |
| F14 | Phí Ahamove, miễn phí, lỗi dịch vụ | Có: Kho `quoteShip`, `apPhiGiao`, `tong`; Đơn chốt lại | D phí42000 và chuyển tự lấy hết phí; B core phí hiện có | D so tổng với hàm Python thật tính tiền/phí từ bảng giá fixture độc lập: giao, tự lấy, miễn phí, lỗi; ngoài vùng hiện nhắc. Chưa tạo đơn production |
| F15 | Ngày giờ nhận, qua nửa đêm | Có: Kho `neoNgay`, `fixSlot`, `mocGioNhan` | K `Qua nửa đêm`, `Khung giờ đã qua`, `Chưa tự chọn đủ ngày`; B `v590: giờ nhận Việt Nam` | Kiểm DOM đồng hồ tiến, đổi tab, ngày gửi máy chủ cùng nhãn |
| F16 | Ưu đãi tự động, mã, xem trước tổng | Có: Kho `xemUuDai`, `apMaUuDai`, computed `giam`, `tong` | K `Ưu đãi: đổi giỏ`, `kết quả lần hỏi CŨ`, `v590: gợi ý mã hiện tổng` | D bấm Áp dụng mã GIAM10, thấy100000; còn DOM đổi ngày/số khi mã đã áp |
| F17 | Mã hết lượt/đã dùng, giá đổi khi gửi | Có: Kho `submitOrder` giữ giỏ/nonce, yêu cầu xem lại | K `Máy chủ đổi giảm sang` (0 và 80000), `Mã đã dùng`; B `Codex #461 vòng 3` | D API đổi giảm100000 về0, cập nhật tổng, không tự POST; khách bấm lại cùng nonce và giam_da_xem0 |
| F18 | Hóa đơn công ty, MST10/12/13, điền tay | Có: Kho `lookupMst`, `submitOrder` tạo hoa_don, Mẫu vatBlock | D MST10/12/13, sửa tay, reload, kiểm MST13/tên trong payload; K loại11 | Còn DOM tra lỗi/thiếu tên công ty |
| F19 | Gửi chống trùng nonce | Một phần: Kho `moGio`, `submitOrder`; Mẫu khóa nút bằng trạng thái; Đơn chống trùng | K nhấp kép1POST; D mạng lỗi rồi gửi lại cùng nonce/biên nhận; B chống trùng | D hai click khi HTTP đang chờ chỉ1POST; còn reload giữa lúc gửi và cạnh tranh DB thật |
| F20 | Lỗi mạng khi gửi, giữ giỏ, thử lại | Có: Kho `submitOrder` catch và giữ dữ liệu; Đơn ghi trước HTTP | K giả máy chủ đã tạo rồi mất phản hồi, retry trả cũ; D giữ giỏ/nonce khi mạng lỗi | Chưa có thử crash HTTP/DB thật, không suy Map giả là kiểm cạnh tranh |
| F21 | Hết hàng/đổi tồn khi khách đang mua | Cách B: nonce trước tồn KB hôm nay/Dư decor ba ngày; nguồn lỗi nhận và báo Sales | Backend8/0, Vue29/0, DOM cả hai trang giữ giỏ/tải tồn; bốn đột biến bắt được; site đọc trước sửa comment6144541606 | Đã code; hai ca Document nối cổng bench, chờ CI SHA cuối và Claude. Không merge/deploy |
| F22 | Biên nhận /banh/xong/token | Có bản Vue song song GĐ2; xem bằng chứng cạnh bên | Có Vue: web_moi/xong + web_vue/trang/app.js. B404/no-token/privacy; D receipt/reload; K Pixel | Chạy song song /web_moi/banh/xong; chưa tráo route cũ. Còn ảnh/trạng thái hủy/chờ trên DOM |
| F23 | Pixel phía trình duyệt | Một phần: App `napPixel`, Kho `suKien` khi chọn/giỏ; Thuần `docFb` | D Pixel spy receipt gỡ token và1GuiDon; K không gỡ token thì không Pixel | D kiểm queue PageView/ViewContent/AddToCart/InitiateCheckout; không gọi Meta thật |
| F24 | CAPI máy chủ | Có đường dùng chung: Kho gửi fbp/fbc; Đơn -> don_web | B gọi bien_nhan_theo_token và goi_su_kien thật, chạy Pixel Vue trong Node, cùng id/value/currency/ids; không Purchase | Chưa kiểm worker/network Meta thật; không gửi conversion thử |
| F25 | Link chia sẻ bánh, back/forward | Có: App `apDuongDan`, `nav`, chờ `tonDaThu` | S `Codex #462: link #/banh...` chỉ dò chuỗi; K `tonDaThu chỉ bật...` | DOM link mới/refresh/back, slug không tồn tại, bánh tải chậm; chưa là ca trình duyệt trong lượt này |
| F26 | SEO, OG, canonical | Có bản Vue song song GĐ2; xem bằng chứng cạnh bên | Có SSR SEO/OG từ nhãn/khối Editor công khai; B hidden block không lấy; giữ noindex | Cần nghiệm thu crawler/meta trên site thử; canonical giữ /banh |
| F27 | Ba chính sách, link chân trang/đồng ý | Có bản Vue song song GĐ2; xem bằng chứng cạnh bên | Có Vue cây thẻ từ HTML core đã sanitize; B3route/public/404/ngôn ngữ; D3page chữ không thực thi | Còn so trình bày và nút đổi ngôn ngữ trên DOM; site thật chưa kiểm |
| F28 | Ưu đãi, tiệc, tuyển dụng, cửa hàng, kênh liên hệ | Có: [noi-dung.js](../../vagabond/public/web_vue/banh/noi-dung.js), App `ChuyenMuc` và dsMuc | S chữ không thành HTML, khóa chữ có trong sổ | DOM các chuyên mục, link HTTPS, logo/ảnh/tắt khối sau xuất bản; so Rocca |
| F29 | Chữ, ảnh, logo, link sửa từ Editor | Một phần: Chữ `apNoiDung`, t/tMon; Vue nhận dữ liệu chung; còn fallback trong du-lieu/anh.js | S kiểm nhãn, không chứng minh mọi ảnh/logo/link sửa được | GĐ3 kiểm từng vùng: sửa -> xuất bản -> reload -> còn sau cập nhật; lập danh sách fallback không biên tập được |
| F30 | Editor và xem trước | Chưa có Editor Vue: [bien-tap.js](../../vagabond/public/web_order/bien-tap.js) đặt preview.src='/banh?bien_tap=1' | Vue có nhận vgb-xem-thu-chon nhưng không chứng minh preview Vue | GĐ3 chuyển Editor, iframe trỏ Vue thật; mobile/desktop, lưu/phiên bản/hoàn tác/lịch sử |
| F31 | Quyền và dữ liệu nội dung cũ | Backend dùng chung [noi_dung_web.py](../../vagabond/noi_dung_web.py): Marketing/System Manager, nháp/công khai | Có kiểm backend trong repo; chưa kiểm Editor Vue vì chưa tồn tại | GĐ3 bản sao nội dung cũ, kiểm quyền thật; không tạo cấu trúc lưu trữ mới tùy tiện |
| F32 | Tráo miền và quay lại | Chưa có công tắc: [ten_mien.py](../../vagabond/ten_mien.py) vẫn /banh, DAU_KHACH chưa có route thử | [thu_cua_ngo.py](../../vagabond/khung/kiem_thu/thu_cua_ngo.py) kiểm định tuyến cũ | GĐ4 mặc định tắt, đảo cả /banh và biên nhận, không mất nháp; thêm whitelist phải thêm ca; giữ bản cũ |
| F33 | Chọn cách thanh toán, đồng ý điều khoản | Có: Mẫu `PAYS`, Kho `CO.pay`, `CO.dongy`, `submitOrder` | D đổi phương thức, reload giữ; bấm đồng ý rồi gửi; B không coi đơn là tiền thu | Còn đối chiếu mã thanh toán trong payload DOM |
| F34 | Hỗ trợ liên hệ, tìm khách theo số điện thoại | Có: Kho `lookupPhone`, App `lienHe`, Chữ `mxh`/`telSo` | Chưa tìm thấy ca Vue xuyên DOM dành riêng cả luồng này | Không hiện thông tin cũ khi đổi số; link sửa từ Editor, lỗi API vẫn cho điền tay |
| F35 | Mobile/desktop, bàn phím, cuộn và quay lại | Có: App focus trap, Escape, popstate, watch tab; CSS Rocca dùng chung và Vue | K không mount DOM nên chưa chứng minh focus/cuộn; có công cụ chụp ảnh trong cong_cu | GĐ4 ảnh390x844/desktop đúng SHA và kiểm focus/back; không suy ảnh giống từ tên CSS |
| F36 | v597: đồ có sẵn trong hộp bánh, Cách chọn size, đồ dự phòng gấp, thiệp nhỏ | Có (v598): Dữ liệu `ACC`, `HUONG_SIZE`, `ADDONS.du_phong`; Thuần `chuanDungCu`, `chuDungCu`, `cartKey`, `duongCat`; App `moHuongSize`/`dongHuongSize`, Escape bắt pha capture, trả con trỏ về nút mở hộp; CSS chép nguyên từ banh.html | D F36 chạy CẢ trang cũ và Vue cùng một chuỗi: khung có sẵn hiện không cần mở gấp, hộp size 4 ô và 16 lát ở size 4, Escape chỉ đóng hộp, dự phòng đóng sẵn, giỏ và ghi chú bếp có "2 thiệp nhỏ"; K cộng dồn, sửa dòng, tải lại giữ thiệp; đột biến 6/6 | Khác bản cũ có chủ ý: Vue để khung đồ có sẵn NGOÀI mục gấp Phụ kiện cho bánh để khách thấy ngay; ảnh site thật ở GĐ4 |

## Chốt phạm vi giai đoạn tiếp theo

1. GĐ2: F22/F26/F27 có phần thiếu rõ; các hàng còn lại phải bổ sung ca thao
   tác DOM và đối chiếu tổng máy chủ ở chỗ ghi chưa đủ. Ưu tiên F19-F21 trước
   khi gọi luồng mua hàng là hoàn tất. Không sửa chính sách tồn theo phỏng đoán.
2. GĐ3: F29-F31, toàn bộ Editor Vue, nội dung cũ nguyên vẹn, bản nháp không
   lộ. Giữ backend nội dung hiện có; chỉ làm migration nếu có bằng chứng cần.
3. GĐ4: F32, công tắc mặc định tắt, quay lại không deploy; ảnh desktop và
   390x844 đúng SHA, nguồn ảnh rõ, so Rocca. Các trang /dat-ban, /thanh-vien,
   /tt, /xhd giữ bản cũ, cần ca chứng minh không bị chuyển theo.

## Cổng và giới hạn giai đoạn 1

Không thay hành vi nghiệp vụ hoặc whitelist. Không có mutation mới cho bảng
Markdown; không gọi việc sửa chữ trong bảng là chứng minh hồi quy. Có chạy
một mutation đối chứng trên kho Vue hiện có trong bản sao tạm (bỏ giảm khỏi
computed tổng); số bắt được ghi trong bàn giao, không sửa source PR để thử.
Chạy K trực tiếp và cả bốn cổng issue yêu cầu; kết quả chính xác/log/SHA ở
comment bàn giao PR. CI, bench, review, ảnh, merge và deploy là các mốc riêng.

## GĐ2 đang thực hiện, chưa nghiệm thu toàn bộ

Đã bổ sung chống nhấp kép, bỏ phản hồi địa chỉ cũ, trạng thái lỗi tải tồn;
biên nhận và ba chính sách Vue, SEO/OG. Không đổi chính sách tạo đơn/hạn mức,
không tạo đơn thật, không ghi production. Bản cũ và Editor vẫn nguyên.
Các ô còn lại ở bảng trên là việc thật còn thiếu, không đánh dấu GĐ2 hoàn tất.
F21 anh Việt đã chốt cách B ngày13/10; xem nhật ký issue470 và bằng chứng trên PR.

Lệnh DOM: cài Playwright theo môi trường kiểm, chạy
`node cong_cu/kiem_web_vue_dom.cjs`; có thể đặt
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` tới Chromium kiểm thử đã cài.
Máy chủ fixture chỉ nghe localhost, mạng ngoài bị chặn, không dùng hồ sơ Chrome cá nhân.
Node kho và DOM là hai bộ kiểm riêng; cổng Python không tự chạy Chromium.

Đột biến trong bản sao tạm: bỏ khóa lượt gửi ->1ca hỏng;
bỏ chặn phản hồi địa chỉ cũ ->1ca hỏng;
bỏ điều kiện gỡ token trước Pixel ->1ca hỏng. Mỗi lượt27đạt/1hỏng trên28ca.
Kết quả cổng và SHA chính xác ghi ở bàn giao PR, không nhận là CI/bench/live.

Bản code GĐ2 lượt này: `1a914c0fc` (SHA đầy đủ trong bàn giao PR).
Kiểm local: framework4451/0; CI giả chặn requests4451/0; kho Vue28/0;
Chromium9nhóm/0; bundle khớp; kiem_truoc_deploy.sh exit0. Hai ca PDF #247
thiếu pypdf được báo bỏ, không tính đạt. Full gate dùng PYTHONPYCACHEPREFIX
ở /tmp vì cache Python trong checkout không ghi được. CI GitHub/bench/live
chưa được xác minh cho bản mới, giữ Draft.
