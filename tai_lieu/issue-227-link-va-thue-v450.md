# #227: link khách tự điền và thuế đơn mua v450

Theo comment 5579026767 ngày 08/09/2026. Codex implement; Claude review
bổ sung và chạy bench. Nền main 2a39f6d, PR #228 đã merge. Không sửa
minvoice_kich_ban.py của PR #229/v449 đang do Claude xử lý.

## Bằng chứng và nguyên nhân

- Ảnh anh Việt: DMH-2026-00324, CCDC00052, tiền trước thuế 742.857;
  đầu phiếu chọn5%, thuế59.428,56 tức8%.
- Đọc site bằng System Console, không save: dòng hiện có
  item_tax_template=GTGT 8% - TV; item_tax_rate có1331=8 và33311=8.
  Phiếu đang lưu hiện là mẫu8%, đơn giá714.290; khác ảnh chưa lưu.
- Core ERPNext16.28.0, de591661: taxes_and_totals._get_tax_rate ưu tiên
  item_tax_map. validate_item_tax_template còn có thể đổi mẫu5 về8 nếu
  danh mục món chỉ khai8. transaction.js nạp lại mẫu khi sửa giá.
- QR cũ neo SI nhưng hết hạn sau2 giờ từ creation. Dùng nguyên QR đó làm
  link gửi sau vài giờ sẽ đưa khách vào link hết hạn ngay.

## Bản sửa

- Nút Tạo link điền thông tin xuất hoá đơn trên chi tiết bill dùng chung
  các điểm bán, ngay vùng Thông tin xuất hoá đơn; có ô link và nút sao chép,
  có cách chọn/copy tay nếu trình duyệt không cho clipboard.
- Link HMAC-SHA256 ký SI+hạn,2 giờ từ lúc tạo, tối đa23h30 cùng ngày bill.
  Kiểm quyền đọc SI và vai trò trước tạo. QR in cũ không đổi định dạng/hạn.
- Trang khách gửi kèm hạn đã ký vào cả xem và lưu. Chặn sai bill/chữ ký/hạn,
  bill huỷ/trả hàng và trạng thái đã gửi/chờ đối chiếu. Lưu dưới row lock,
  kiểm lại hạn sau khi đợi lock, ghi dấu khách tự điền. Dùng bốn ô XHD
  hiện có nên đường payload/cuối ngày đọc cùng dữ liệu, không tạo bản đồ
  người mua mới và không mở rộng mã lỗi M-Invoice.
- PO thêm Check Dùng mẫu thuế đầu phiếu cho mọi món, mặc định0 để không
  thay các đơn nhiều mức hiện có. Nút áp mẫu bật lựa chọn trên đơn.
  Bật thì mẫu đầu phiếu là nguồn: before_validate dựng taxes từ master
  được chọn và xoá Item Tax Template/map từng dòng. Chuỗi rỗng được core
  giữ qua save, không thay Item toàn cục. Khi bật không sửa tay bảng thuế;
  muốn thuế/phí riêng thì tắt. Có shipping_rule riêng thì không bật chế độ này để tránh làm mất phí. Wrapper từng form giữ lựa chọn trước mọi
  phép tính, kể cả callback sau sửa giá/thêm món. Tắt giữ nhiều mức.
- Patch thue_don_mua_v450 chỉ thêm cấu hình trường, không sửa chứng từ cũ.
  Bản Web Page xhd được đồng bộ qua quy trình trang/after_migrate có sẵn.

## Kiểm đã chạy tại máy Codex

- Cổng kiem_truoc_deploy.sh RC0,2628 ca tầng khung đạt; bundle khớp byte.
- Ca JS hành vi: tái hiện5/8 trong ảnh, áp5, callback muộn trả8, thêm món,
  giữ nhiều mức và hộp hỏi cũ không áp vào mẫu vừa đổi. Đã đưa vào gate.
- Ca link: chữ ký sai/Unicode, sửa SI, sửa hạn, hết hạn, sai quyền, bill cũ,
  chờ đối chiếu, huỷ và QR cũ. Không dùng phản hồi M-Invoice thật.
- Review chéo bỏ hai phương án lỗi: chọn Item Tax Template5 bất kỳ có thể
  bị core đổi về8; chỉ xoá một lần sẽ bị callback sửa giá nạp lại8.

## Điều kiện Claude cần hoàn thành trước merge/deploy

1. Chạy2 ca mới trong khung/kiem_that/thu_link_thue_227.py qua runner
   savepoint/khóa commit/cấm gửi. Tự dựng Item/mẫu/PO mới. Xác nhận insert,
   save/reload, sửa giá/thêm món và submit thật đều5%; mode0 vẫn nhiều mức.
   Không chạy trực tiếp từng hàm bỏ qua runner. Báo nguyên lỗi nếu fixture
   hoặc core không chấp nhận; Codex chưa có bench để chạy độc lập.
2. Ca SI: khách lưu đúng bill, email vào payload, chờ đối chiếu cấm ghi lại.
   Mail được chặn trong ca, không gọi Save thật sang M-Invoice.
3. Kiểm trình duyệt Frappe thật: role thu ngân/sales từng điểm có quyền
   tạo link; link khách trên miền order; QR cũ; sao chép bị từ chối;
   bill chờ đối chiếu không cho sửa. Kiểm sửa giá với mạng chậm trên PO.
4. PR #229/v449 là việc khác còn cần review riêng. Nếu merge229 trước,
   đồng bộ nhánh này trên main mới, giữ đủ449/450 và chạy lại gate/CI.
   Không lấy bản450 này làm bằng chứng rằng hotfix229 đã review/deploy.
5. Giữ Draft đến khi review+bench+CI đủ. Không tự merge/deploy từ handoff
   này. Sau khi được chốt mới migrate, kiểm Patch Log thue_don_mua_v450,
   trường PO, Web Page xhd,APPVER450, và màn trên site.

Không đổi danh mục thuế, không sửa đơn DMH thật, không phát hành HĐĐT,
không sửa chứng từ cũ, không đóng issue227.
