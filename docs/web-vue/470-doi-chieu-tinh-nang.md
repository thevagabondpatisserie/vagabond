# #470 - Giai đoạn 1: đối chiếu trang đặt bánh cũ và Vue

Nguồn: [issue #470](https://github.com/thevagabondpatisserie/vagabond/issues/470).
Owner: Codex. Nền kiểm kê: `42cb9fb9a` (main v592, ngày 13/10/2026).
Một PR Draft xuyên suốt bốn giai đoạn; giai đoạn này chỉ kiểm kê, chưa tráo
miền, chưa chuyển Editor hoặc viết lại luồng khách. v593 là mốc dự kiến của
PR theo mục bắt buộc, phải đọc lại main trước khi chốt phát hành.

## Cách đọc bằng chứng

- **Có**: tìm thấy đường chạy trong code Vue, không đồng nghĩa đã nghiệm thu.
- **Một phần**: có code nhưng chưa đủ luồng hoặc chưa đủ kiểm hành vi.
- **Chưa**: chưa có bản Vue tương ứng. Không ghi ca kiểm backend thành ca UI.
- **K** là kiểm kho Vue thật trong Node, mạng/đồng hồ giả, không mount DOM.
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
| F01 | Có sẵn hôm nay, tồn Sales online | Có: Kho `napTon`, `banhHomNay`, `gioiHanNhan`; Mẫu tab today | K `#463: napTon giữ đúng mã và số Sales online`, `Giới hạn số còn nhận` | DOM chọn tab, hết tồn khi đang mở và so phản hồi máy chủ |
| F02 | In store D1 | Một phần: Kho `napQuay`, App `quayHien`, Mẫu danh sách quầy | K `PR #462: quầy trả lỗi vẫn hiện tab In store` chỉ kiểm lỗi/thử lại | Fixture riêng D1, đổi quầy/nhóm và nhãn/tồn thật trên DOM |
| F03 | In store NVHTN | Một phần: cùng nguồn mảng `STORE.quay`, chọn `quayChon` | Ca F02 không chứng minh NVHTN riêng | Fixture riêng NVHTN và đổi qua lại D1 không trộn kho |
| F04 | Đặt trước, size còn nhận | Có: Kho `banhDatTruoc`, `kichThuocDangBan`, `pick`, `pickSlot` | K `Giới hạn số còn nhận`, `Chưa tự chọn đủ ngày và giờ` | DOM chọn size/ngày; so giới hạn máy chủ, không chỉ computed |
| F05 | Hàng mùa vụ | Có: Kho `napMua`, `themHangMua`; App route in-season | K `Hàng mùa vụ: không thêm quá số còn của mùa` | DOM chi tiết, hết mùa, link trực tiếp và lỗi tải |
| F06 | Chi tiết bánh, ảnh, chọn size | Có: App `chiTiet`, `kichThuocDong`; Kho `moBanh`, `setSize` | K `Thêm nhanh: nhiều cỡ thì mở chi tiết`, `Danh mục máy chủ trộn vào bánh` | Bấm gallery/size trên DOM, so Rocca và nội dung Editor |
| F07 | Phụ kiện, nến số, đĩa/nĩa | Có: Kho `toggleAdd`, `toggleNum`, `addToCart`; Thuần `hangGui` | K `hangGui gộp dòng trùng mã và phụ kiện theo số bánh` | Chuỗi chọn nến/phụ kiện -> sửa giỏ -> payload; ca hiện tại chỉ phủ phép gộp |
| F08 | Lời chúc, bánh tặng, người nhận khác | Có: Kho `wish`, `CO.gift`, `CO.other`, `submitOrder` | K `Gửi đơn: thứ tự chặn` kiểm tag bánh tặng, chưa đủ lời chúc/người nhận | DOM sửa lời chúc, người nhận khác; giữ sau reload |
| F09 | Giỏ tăng/giảm/xóa/sửa dòng | Có: Kho `cartQty`, `cartRemove`, `suaDongGio`; App `suaDongGio` | K `Bấm + trong giỏ: tiền bánh và tổng đổi NGAY` | DOM sửa dòng rồi quay lại, xóa cuối cùng, tổng phụ kiện |
| F10 | Khôi phục giỏ hiện tại | Có: Kho `luuGio`, `phucHoiGio`, `lamTuoiGiaGio`, khóa `vgb-gio-v1` | K `Lưu giỏ trong phiên rồi tải lại`, `Trước khi khôi phục xong` | Reload trình duyệt và storage lỗi, giữ nguyên giới hạn sessionStorage |
| F11 | Nháp cũ qua Vue và quay lại | Có: Kho `phucHoiGio` đọc dạng cũ, `luuGio` giữ tương thích | K `PR #462: nháp trang cũ khôi phục đủ ô` | Trọn vòng trang cũ -> Vue -> tắt công tắc -> trang cũ, cùng phiên |
| F12 | Nhận tại quầy, điểm nhận do Editor cấu hình | Có: Kho `setMode`, `setPickup`, `capNhatDiemNhan`; App watch ND | B `v586 ... đơn tự lấy chỉ nhận điểm đang bật`, `v586b ... Marketing tắt hoặc đổi điểm nhận` | DOM chọn điểm/tắt điểm giữa lượt; đối chiếu địa chỉ máy chủ |
| F13 | Giao hàng, địa chỉ/gợi ý/ngoài vùng | Có: Kho `lookupPhone`, `goiYDiaChi`, `chonGoiY`, `quoteShip` | K gửi đơn kiểm thiếu địa chỉ; chưa đủ gợi ý/ngoài vùng | DOM gõ/chọn/sửa địa chỉ, phản hồi muộn; không giữ tọa độ cũ |
| F14 | Phí Ahamove, miễn phí, lỗi dịch vụ | Có: Kho `quoteShip`, `apPhiGiao`, `tong`; Đơn chốt lại | K `Phí giao: lần hỏi cũ về muộn bị bỏ`; B `#367 C tự lấy phí 0`, `#367 E miễn phí giao` | DOM cả tự lấy/giao/ngoài vùng/lỗi, so tổng máy chủ từng nhánh |
| F15 | Ngày giờ nhận, qua nửa đêm | Có: Kho `neoNgay`, `fixSlot`, `mocGioNhan` | K `Qua nửa đêm`, `Khung giờ đã qua`, `Chưa tự chọn đủ ngày`; B `v590: giờ nhận Việt Nam` | Kiểm DOM đồng hồ tiến, đổi tab, ngày gửi máy chủ cùng nhãn |
| F16 | Ưu đãi tự động, mã, xem trước tổng | Có: Kho `xemUuDai`, `apMaUuDai`, computed `giam`, `tong` | K `Ưu đãi: đổi giỏ`, `kết quả lần hỏi CŨ`, `v590: gợi ý mã hiện tổng` | DOM bấm Áp dụng và chuỗi đổi giỏ/ngày/số; tổng đối chiếu backend |
| F17 | Mã hết lượt/đã dùng, giá đổi khi gửi | Có: Kho `submitOrder` giữ giỏ/nonce, yêu cầu xem lại | K `Máy chủ đổi giảm sang` (0 và 80000), `Mã đã dùng`; B `Codex #461 vòng 3` | Kiểm xuyên DOM -> API; không tự gửi lại khi khách chưa chốt tổng |
| F18 | Hóa đơn công ty, MST10/12/13, điền tay | Có: Kho `lookupMst`, `submitOrder` tạo hoa_don, Mẫu vatBlock | K `Codex #462: MST 12 số ... 11 số`; B luồng đơn dùng chung | Chưa đủ ca Vue riêng10/13, tra lỗi/thiếu tên, payload đầy đủ sau reload |
| F19 | Gửi chống trùng nonce | Một phần: Kho `moGio`, `submitOrder`; Mẫu khóa nút bằng trạng thái; Đơn chống trùng | B `#367 E gửi trùng trong 15 phút`, `thiếu nonce`; K giữ nonce khi đổi giảm | DOM nhấp kép, reload/mất phản hồi, gọi lại cùng nonce chỉ một đơn. Không suy từ nút disabled là đủ |
| F20 | Lỗi mạng khi gửi, giữ giỏ, thử lại | Có: Kho `submitOrder` catch và giữ dữ liệu; Đơn ghi trước HTTP | B `#367 E Pancake mất phản hồi`, `Pancake từ chối`; K chưa phủ đầy đủ mạng gửi Vue | Bổ sung hành vi mất phản hồi -> thử lại -> biên nhận cũ, không tạo trùng |
| F21 | Hết hàng/đổi tồn khi khách đang mua | Một phần: Kho giới hạn từ tồn đã tải; gửi qua Đơn | K giới hạn local, tải tồn Sales online | Đo chính sách cửa máy chủ hiện tại trước sửa; thử tồn đổi giữa tải và gửi. Không nhận mock tồn là kiểm cạnh tranh |
| F22 | Biên nhận /banh/xong/token | Chưa có Vue: App `guiDon` chuyển tới trang cũ [xong.html](../../vagabond/www/banh/xong.html), [bien-nhan.js](../../vagabond/public/web_order/bien-nhan.js) | B `#367 F` token/riêng tư/lỗi/chờ đối soát là kiểm bản cũ | GĐ2 dựng Vue giữ cùng API, token, noindex, referrer, trạng thái; không lộ PII |
| F23 | Pixel phía trình duyệt | Một phần: App `napPixel`, Kho `suKien` khi chọn/giỏ; Thuần `docFb` | K môi trường `suKien` đang no-op, chưa chứng minh gửi sự kiện thật | Spy PageView/ViewContent/AddToCart/InitiateCheckout, tránh lặp và tắt preview |
| F24 | CAPI máy chủ | Có đường dùng chung: Kho gửi fbp/fbc; Đơn -> don_web | B `#367 G CAPI`, `gửi CAPI ... đã gửi thì không gửi lại` | Vue payload fbp/fbc, event_id và dedup với Pixel; lỗi/retry, không gửi Meta thật để thử |
| F25 | Link chia sẻ bánh, back/forward | Có: App `apDuongDan`, `nav`, chờ `tonDaThu` | S `Codex #462: link #/banh...` chỉ dò chuỗi; K `tonDaThu chỉ bật...` | DOM link mới/refresh/back, slug không tồn tại, bánh tải chậm; chưa là ca trình duyệt trong lượt này |
| F26 | SEO, OG, canonical | Chưa đủ: [web_moi/banh.html](../../vagabond/www/web_moi/banh.html) có title cố định và noindex,nofollow; chưa OG/canonical riêng | S CSRF/no-cache không kiểm SEO | GĐ2 xác định metadata theo nội dung Editor; GĐ4 chỉ index route chính, route thử vẫn noindex; kiểm crawler không chạy JS |
| F27 | Ba chính sách, link chân trang/đồng ý | Một phần: App `chinhSach` chỉ render link; bản đích [chinh-sach.html](../../vagabond/www/chinh-sach.html) chưa Vue | B chính sách/cấu hình công khai hiện có, không chứng minh trang Vue | GĐ2 Vue đọc nội dung đã xuất bản, nháp không lộ, link cũ giữ nguyên |
| F28 | Ưu đãi, tiệc, tuyển dụng, cửa hàng, kênh liên hệ | Có: [noi-dung.js](../../vagabond/public/web_vue/banh/noi-dung.js), App `ChuyenMuc` và dsMuc | S chữ không thành HTML, khóa chữ có trong sổ | DOM các chuyên mục, link HTTPS, logo/ảnh/tắt khối sau xuất bản; so Rocca |
| F29 | Chữ, ảnh, logo, link sửa từ Editor | Một phần: Chữ `apNoiDung`, t/tMon; Vue nhận dữ liệu chung; còn fallback trong du-lieu/anh.js | S kiểm nhãn, không chứng minh mọi ảnh/logo/link sửa được | GĐ3 kiểm từng vùng: sửa -> xuất bản -> reload -> còn sau cập nhật; lập danh sách fallback không biên tập được |
| F30 | Editor và xem trước | Chưa có Editor Vue: [bien-tap.js](../../vagabond/public/web_order/bien-tap.js) đặt preview.src='/banh?bien_tap=1' | Vue có nhận vgb-xem-thu-chon nhưng không chứng minh preview Vue | GĐ3 chuyển Editor, iframe trỏ Vue thật; mobile/desktop, lưu/phiên bản/hoàn tác/lịch sử |
| F31 | Quyền và dữ liệu nội dung cũ | Backend dùng chung [noi_dung_web.py](../../vagabond/noi_dung_web.py): Marketing/System Manager, nháp/công khai | Có kiểm backend trong repo; chưa kiểm Editor Vue vì chưa tồn tại | GĐ3 bản sao nội dung cũ, kiểm quyền thật; không tạo cấu trúc lưu trữ mới tùy tiện |
| F32 | Tráo miền và quay lại | Chưa có công tắc: [ten_mien.py](../../vagabond/ten_mien.py) vẫn /banh, DAU_KHACH chưa có route thử | [thu_cua_ngo.py](../../vagabond/khung/kiem_thu/thu_cua_ngo.py) kiểm định tuyến cũ | GĐ4 mặc định tắt, đảo cả /banh và biên nhận, không mất nháp; thêm whitelist phải thêm ca; giữ bản cũ |
| F33 | Chọn cách thanh toán, đồng ý điều khoản | Có: Mẫu `PAYS`, Kho `CO.pay`, `CO.dongy`, `submitOrder` | K `Gửi đơn: thứ tự chặn`; B `#367 L chưa tick đồng ý` | DOM đổi phương thức, gửi đúng mã, giữ sau reload; không coi gửi đơn là đã thanh toán |
| F34 | Hỗ trợ liên hệ, tìm khách theo số điện thoại | Có: Kho `lookupPhone`, App `lienHe`, Chữ `mxh`/`telSo` | Chưa tìm thấy ca Vue xuyên DOM dành riêng cả luồng này | Không hiện thông tin cũ khi đổi số; link sửa từ Editor, lỗi API vẫn cho điền tay |
| F35 | Mobile/desktop, bàn phím, cuộn và quay lại | Có: App focus trap, Escape, popstate, watch tab; CSS Rocca dùng chung và Vue | K không mount DOM nên chưa chứng minh focus/cuộn; có công cụ chụp ảnh trong cong_cu | GĐ4 ảnh390x844/desktop đúng SHA và kiểm focus/back; không suy ảnh giống từ tên CSS |

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
