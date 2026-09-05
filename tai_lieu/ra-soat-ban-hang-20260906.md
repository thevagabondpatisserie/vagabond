# Rà soát phân hệ bán hàng, 06/09/2026

Owner: Codex. Điều phối và review: [Issue #209](https://github.com/thevagabondpatisserie/vagabond/issues/209).
Nhánh: `codex/ra-soat-ban-hang-20260906`. Nền: `ccf8e33` (main, v433).

## Trạng thái nghiệm thu

**CHƯA nghiệm thu toàn phân hệ.** Đây là bản sửa đầu tiên và sổ theo dõi những điểm còn phải xử lý. Chưa review chéo, chưa merge/deploy, chưa chạy giao dịch bán hàng thử trên site. Không sửa dữ liệu lịch sử, không gửi/hủy HĐĐT, không gọi thanh toán thật.

Đã chạy 15 ca hành vi mới. Trước sửa, 9/14 ca đầu đỏ; sau sửa, cả 14 xanh. Ca thứ 15 về lọc mã có dấu gạch đỏ trên mã cũ rồi xanh sau sửa. Chạy lại toàn cổng kiểm: 2.385 ca khung, 27 ca phiên bản báo giá và 2.309 ca bộ điểm đều đạt; Python, JS, 105 đường màn hình và bản ghép app đều đạt. Không có wkhtmltopdf nên phần dựng PDF của bộ kiểm có sẵn bị bỏ qua.

Đây không phải 4.721 giao dịch thực tế. Bộ có nhiều ca dò cấu trúc/chuỗi; 15 ca mới chạy thân hàm thật với cổng dữ liệu giả lập. Chúng không chứng minh tính đúng của GL/Payment Ledger/Stock Ledger, SQL đồng thời hay kết nối đối tác.

Frappe Cloud của bench-44405 hiển thị Frappe v16.27.1 và ERPNext v16.28.0, nhánh `version-16`. Đã đọc mã gốc nhánh đó: Frappe `33bf510`, ERPNext `0b50853`. Đây là mã nhánh tham chiếu, không khẳng định trùng commit đang chạy trên site. Nguồn chính: `frappe/database/database.py:set_value/get_value`, `frappe/model/document.py:check_docstatus_transition/validate_update_after_submit`, `erpnext/controllers/selling_controller.py:validate`. `set_value` không chạy sự kiện Document, vì vậy cửa lưu trực tiếp phải tự kiểm trạng thái; đã ghi lý do trong bản sửa.

## Các lỗi đã sửa trên nhánh, chưa đưa lên hệ thật

| Mã | Mức | Tái hiện và hậu quả | Bản sửa |
|---|---|---|---|
| BH-01 | P1 | BT ghi `VGBAAAAA VGBBBBBB`, 400.000 đ. Mở riêng A thì matcher lọc mất B, nhận cả 400.000 đ cho A. Công nợ CN/DNTT có cùng lỗi. | Phát hiện mọi mã trong dòng trước khi lọc danh sách cần hỏi. Dòng nhiều mã liên quan được trả về diện nhập nhằng, không tự chia tiền. `chiem_sao_ke.cong_tien`, `cong_no._sepay_theo_ma_cn`. |
| BH-02 | P2 | Tra phiếu công nợ rỗng/không có mã hợp lệ trả `{}` nhưng caller giải nén thành hai biến, làm vỡ màn. | Mọi nhánh trả cùng dạng `({}, [])`, không hỏi SQL khi không có mã. |
| BH-03 | P1 | `luu_thanh_toan` vẫn ghi phương thức/mã tham chiếu trên SI đã submit hoặc đã hủy, không điều chỉnh chứng từ thu tương ứng. | Khóa dòng khi đọc; chặn sửa hóa đơn không còn nháp và hóa đơn hủy mềm. Submit cùng giá trị chỉ no-op, giữ đường lưu thông tin xuất HĐ của màn sales. |
| BH-04 | P1 | Chế độ `gioi_han`, đã in tạm tính, giữ số lượng nhưng đổi giá 100.000 xuống 60.000: không xin OTP. Tăng qty lên 2 cũng che được việc hạ giá nếu chỉ nhìn tổng tiền. | So đơn giá bình quân theo mã hàng. Tách dòng cùng giá không bị hỏi nhầm. Giữ nguyên `tu_do`, bill chưa in và lựa chọn quyền của chủ. |
| BH-05 | P1 | `kiem_sepay` trên phiếu `Huy` có thể đổi về `Thu thieu`/`Da thu du`, nhận lại sao kê và sinh phiếu thu. | Chặn ngay trước đọc tiền, save, gửi thư hoặc sinh chứng từ. |
| BH-06 | P1 | SQL lọc sơ bộ bằng `DNTT26`, nên nội dung `DNTT-26-09-00001` hoặc `DNTT 26 09 00001` bị loại trước khi Python bỏ dấu phân cách. Khách đã trả nhưng màn báo chưa thấy tiền. | SQL chỉ lọc tiền tố chữ CN/DNTT, Python kiểm mã đầy đủ. Cần đo thời gian truy vấn trên site trước phát hành vì tập ứng viên rộng hơn. |

Ca mới nằm trong `vagabond/khung/kiem_thu/thu_ra_soat_ban_hang.py`, đăng ký vào `chay.py` nên không bị đứng ngoài cổng kiểm hiện có.

## Lỗi còn mở và rủi ro cần xác minh

### BH-07, P1: phân bổ lại tiền cũ hoặc bỏ sót đợt thu mới

Vị trí: `cong_no.ghi_thu_cho_phieu`, `thu_tien.ghi_thu_tien`, `cong_no.kiem_sepay`.

`con = doc.da_thu` dùng tổng lũy kế mỗi lần, nhưng danh sách hóa đơn chỉ còn các tờ chưa hết dư nợ. Khóa chống trùng lại cố định theo SI + nguồn phiếu + phương thức.

Đã chạy thân hàm phân bổ thật, giả lập dư nợ và hành vi khóa của cổng thu, với hai kết quả:

| Kịch bản | Tiền thật đầu vào | Kết quả hiện tại | Kết quả phải có |
|---|---:|---|---|
| A nợ 100.000, B nợ 100.000. Thu 100.000, kiểm lại cùng số | 100.000 | Phân bổ A 100.000 rồi B 100.000 | Tổng chỉ 100.000, B còn nợ 100.000 |
| A nợ 1.000.000. Thu 400.000, sau đó tổng thu lên 1.000.000 | 1.000.000 | Chỉ ghi 400.000, còn treo nợ 600.000 | Lần sau chỉ ghi thêm 600.000 |

Đây là bằng chứng thuật toán, chưa phải chứng từ Payment Entry thật. Cần kiểm thêm: lỗi submit sau insert để lại draft; lỗi cấu hình tài khoản; nhận tiền từ hai nguồn; hai yêu cầu đồng thời; giao dịch đã bị phiếu khác giữ. `kiem_sepay` còn commit trạng thái đủ tiền trước sinh phiếu thu và không thử lại khi trạng thái trước đó đã đủ. Không được hiển thị đã tất toán chỉ vì cờ phiếu đã đổi.

Đã đề nghị Claude nhận phần ghi thu, chưa có xác nhận nhận việc. Hướng sửa: lấy tiền đã thực sự phân bổ cho nguồn phiếu, chỉ ghi phần chênh chưa nhận; khóa nguồn và hóa đơn; phân biệt chứng từ draft/submitted; có đường thử lại không nhân đôi. Không tự sửa Payment Entry lịch sử. Bắt buộc đọc core kế toán đúng phiên bản và có ca tích hợp rollback.

### BH-08, P1: hủy phiếu đã thu một phần và ghi đè số thu tay

`cong_no.huy_phieu` chỉ chặn `Da thu du`, chưa chặn `Thu thieu` có tiền đã ghi sổ. Khi phiếu hủy mất quyền giữ giao dịch, cần tránh cùng khoản tiền được nhận ở phiếu mới trong khi phiếu thu cũ vẫn tồn tại.

`kiem_sepay` còn gán `doc.da_thu = nhan` kể cả khi `_sepay_cn` trả rỗng do không tìm được hoặc lỗi đọc. Phiếu đã khớp tay có thể bị ghi số thu về 0 nhưng cờ trạng thái không được đưa về tương ứng. Cần phân biệt chưa đọc được, không tìm thấy, đã khớp tay và thay đổi dữ liệu ngân hàng. Không tự đảo sổ đã ghi. BH-05 chỉ chặn hồi sinh phiếu đã hủy, chưa giải quyết hai vấn đề này.

### BH-09, P1: đặt giao bánh khi không tính được phí

`don_hang.tao_don`: nếu `phi_giao` trả `ok=0` do Ahamove lỗi/chưa cấu hình/không tìm được địa chỉ, chỉ lý do `ngoai_vung_giao` bị chặn. Các lỗi khác vẫn gửi Pancake với `shipping_fee=0`, `partner_fee=0`. Đây không phải quyết định miễn phí của tiệm.

Cần chặn đặt giao khi chưa có báo phí hợp lệ, giữ nguyên đường tự lấy, có thông báo thử lại hoặc liên hệ tiệm. Phối hợp giao diện với Claude ở #205/PR #208. Chưa sửa để không giao một thay đổi API mà màn hình chưa giải thích được. Kiểm cả trường hợp khách gọi trực tiếp, tọa độ không khớp địa chỉ và timeout sau khi Pancake đã nhận đơn.

### BH-10, P2: đối soát thu hợp đồng luôn lùi về không có giao dịch

`thu_hop_dong.kiem_sepay` gọi `sepay.tim_theo_noi_dung` nếu hàm tồn tại, nếu không trả `[]`. Trong `sepay.py` hiện tại không có hàm này. Màn nhận `da_ve=0` thay vì thông báo tính năng chưa đọc được sao kê. Không thể dùng kết quả này làm bằng chứng khách chưa trả.

Cần nối đúng cổng tra cứu, chỉ rõ tổng theo hợp đồng hay theo từng đợt, tránh tiền đợt trước bị hiểu là đợt mới. `ghi_da_thu` dùng quyền xem hợp đồng gồm Sales/Purchase dù mô tả nói kế toán; cần chủ xác nhận ai được đánh dấu đã nhận tiền trước khi thay chính sách quyền.

### BH-11, P1: lộ địa chỉ khách ở cổng tra số điện thoại

`api.tra_khach` cho Guest tra số điện thoại, trả cả `dia_chi_che` lẫn địa chỉ đầy đủ, tên và số điện thoại trong JSON. Che số nhà trên UI không bảo vệ dữ liệu ở response. Đã xác nhận bằng mã nguồn, không thực hiện tra hàng loạt hay xuất dữ liệu khách thật.

Cần xác thực người giữ số điện thoại trước khi trả địa chỉ đầy đủ, hoặc chỉ trả địa chỉ sau luồng được xác thực. Phối hợp frontend/backend và rà cache. Không coi rate limit 20/phút là xác thực.

### BH-12, P1 cần kiểm đồng thời: mở hai ca cùng điểm bán

`ca_quay.mo_ca` kiểm chưa có ca, insert, count rồi commit. Hai transaction cùng chạy có thể chỉ thấy bản ghi của chính mình ở bước count. Controller `VagabondCaQuay` không có logic bổ sung; schema không có khóa duy nhất cho ca đang mở.

Chưa chạy hai kết nối database nên ghi là rủi ro có đường xảy ra, không khẳng định đã phát sinh trên dữ liệu thật. Cần khóa một khóa ổn định theo điểm bán, rồi kiểm lại trong transaction. Đồng thời kiểm ca Sales Online: bộ tính tiền lấy theo ngày, có thể lặp doanh số nếu một ngày được chốt nhiều ca. Phải thống nhất đơn vị đối soát là ngày hay ca trước khi đổi.

### BH-13, P1: vận đơn đã kết thúc có thể quay về luồng giao

`van_don.giao_loi` đặt `Không giao được` mà không kiểm trạng thái cũ. Từ `Huỷ` hoặc `Đã giao` có thể gọi cửa này, rồi `giao_xong` không còn thấy trạng thái kết thúc để chặn và có thể đẩy Pancake trạng thái 3. `huy_van_don` cũng ghi trực tiếp trạng thái, thiếu kiểm chuyển bước.

Cần phân biệt báo lỗi khi đang giao với mở lại đơn đã kết thúc; đường mở lại phải có quyền/lý do và dấu vết. Kiểm vai shipper so với sales, người được giao đơn, pickup nội bộ và lần giao cuối cho khách. Không chạy các cửa thay trạng thái trên vận đơn thật để tái hiện.

## Ma trận bao phủ và cổng còn thiếu

| Luồng | Đã làm trong đợt này | Còn phải nghiệm thu |
|---|---|---|
| Quầy: tạo, in tạm tính, sửa, chốt | Rà các cửa chính; BH-03/04; bộ kiểm cũ + ca mới | Thao tác hai máy, máy in, OTP, nhiều mức quyền, bấm lại khi mất mạng |
| Pancake: đồng bộ, thanh toán, ghi doanh số | Đọc luồng và đối chiếu issue #201/#204; matcher BH-01 | So đơn thật với SI: giá, giảm, món tặng, phí ship, tổng, trạng thái; đồng bộ lại không nhân đôi |
| Thu nhiều phương thức và công nợ | Đọc bảng dòng, ghi thu và hai mô phỏng BH-07 | Payment Entry/Payment Ledger thật, thu nhiều đợt, rollback, lỗi cấu hình, đua hai yêu cầu |
| Đối soát ngân hàng | BH-01/02/05/06 và 15 ca mới | Giữ giao dịch nguyên tử giữa nhiều phiếu, nhiều họ mã, đa tài khoản, manual match, hiệu năng SQL |
| Đặt web | Rà payload và đường tính lại phí; BH-09/11 | Checkout từ Guest, timeout/đặt trùng, lịch nhận, mã SKU/UUID, giữ hàng mùa vụ đồng thời |
| Đặt bánh trước | Đối chiếu nền #195, bộ kiểm hiện có | Thu đủ trước, tiền mặt vào ca đúng nơi, đổi ngày/điểm nhận, hoàn qua ngân hàng, VAT lúc giao |
| Báo giá, B2B, hợp đồng | Bộ phiên bản 27 ca, bộ thuế/điểm hiện có; BH-10 | Tạo SI từ báo giá từng đợt, lặp yêu cầu, thuế 0%, thuế bao gồm/chưa bao gồm, giảm từng dòng |
| Giao hàng, pickup, COD | Đọc chuyển trạng thái, kiểm liên kết issue #201; BH-13 | Không lẫn giao nội bộ với giao khách, COD đối chiếu tiền, retry Pancake, quyền người giao |
| Hủy và hoàn tiền | Đọc cửa lập hồ sơ, đối soát, UNC, kết thúc; bộ kiểm hiện có | Chứng từ thu/chi thật, hoàn nhiều lần, hủy một phần, ngân hàng giữ hộ, không hoàn vượt, không dùng lại giao dịch |
| Chốt ca, nộp quỹ | Đọc tính tiền, thời gian và mở/chốt ca; BH-12 | Hai ca cùng điểm, ca qua đêm, khách cọc trước và nhận sau, ca Online theo ngày, phiếu nộp thực |
| HĐĐT | Kiểm cửa bảo vệ dữ liệu đã phát hành; không thay luồng thuế | Sandbox nhà cung cấp, timeout sau phát hành, gửi lại không trùng, trạng thái CQT, điều chỉnh/thay thế có duyệt |
| Quyền, dữ liệu khách và vận hành | Rà các cửa ghi trong phạm vi trên; BH-03/04/11/13 | Ma trận vai trò thực và điểm bán, log lỗi, cảnh báo job, kiểm phục hồi, mobile/desktop |

Các tính năng đã biết chưa xong như #201 A/C và #204 phần 2 không được tính là lỗi mới. Không sửa chồng nhánh Claude #204, PR #207 hoặc PR #208.

## Handoff và điều kiện phát hành

1. Claude review nhánh sửa sáu lỗi đầu, đặc biệt SQL rộng hơn, bill ghi sổ no-op và bình quân giá theo mã. Chưa có review thì chưa tạo PR theo AGENTS.md mục 9.
2. Claude xác nhận claim phần ghi thu BH-07/08 hoặc phân chia lại tại #209. Không sửa chồng `cong_no.py`; phân chia theo hàm phải được ghi rõ và hai bên đồng ý.
3. Các lỗi web BH-09/11 phối hợp #205; không chỉ sửa chữ giao diện. BH-10/12/13 cần nhận việc riêng và ca tái hiện đi kèm.
4. Có site kiểm thử đúng phiên bản, dữ liệu dựng mới và chặn mọi gửi ra ngoài. GL/SLE/Payment Entry phải chạy insert/submit thật trong savepoint, khóa commit, rollback; `chung_tu_con_sot` và `so_luong_lech` phải rỗng.
5. Cổng chỉ đọc cấu hình tài khoản thu qua trình duyệt bị client chặn trong lần thử này; không có số liệu mới để xác nhận cấu hình đang đủ. Không suy từ nhận xét lịch sử rằng cấu hình hiện vẫn thiếu. Cần người có quyền kiểm bảng Hình thức thanh toán trên site.
6. Chỉ phát hành khi test, CI, review chéo và kiểm site đạt. Không dùng bản audit này để tự động merge/deploy hoặc sửa chứng từ cũ. Issue #209 tiếp tục mở cho đến khi các hàng trong ma trận có bằng chứng nghiệm thu.
