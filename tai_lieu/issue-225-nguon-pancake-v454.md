# Issue 225: nạp thông tin đúng nguồn, v454

Nền main 7e7033c, v453. PKT cũ đã được Claude xử lý trên site; PR này không sửa chứng từ hay giá vốn.

## Nguyên nhân và thay đổi

Script nạp chạy cho mọi nguồn có custom_nguon. Mã tại quầy cũng nằm trong custom_pancake_display_id, nên lượt xuất rải gọi tìm Pancake rồi dừng vì không khớp đơn.

Kiểm custom_nguon sau khi đọc khoá SI, trước HTTP và mọi db_set: nguồn được khai khác Pancake thì bỏ qua bước nạp. Nguồn rỗng của phiếu cũ vẫn qua kiểm ID/phân trang như trước; không suy nguồn từ tiền tố mã. Áp dụng cả gọi một phiếu và quét theo ngày, kể cả ghi_de=1. Không bỏ qua lỗi tra cứu của nguồn Pancake.

Migration sinh script từ snapshot, nhận thêm đúng hash v449 hiện đã deploy; script sửa ngoài vẫn chặn. Không gọi API ngoài trong migrate. Dòng patch v454 để Cloud chạy migrate.

## Đã kiểm tại Codex

- Ca thực thi script nạp cho Tại chỗ, GrabFood, ShopeeFood, Khách sỉ, cả phiếu lẻ và lô: không HTTP, không đổi dữ liệu, không lỗi tìm đơn.
- Pancake và phiếu cũ thiếu nguồn vẫn tra ID, sai ID vẫn báo lỗi.
- Chạy nối tiếp nạp và phát hành bằng Python exec: Tại chỗ/GrabFood tới Save giả lập đúng một lần, giữ email người mua.
- Review chéo xác nhận hai hash v449 khớp bản cũ thực sinh từ main, script lạ bị từ chối.
- Các HTTP và phản hồi M-Invoice trong ca kiểm đều giả lập; không chứng minh API thật đã phát hành được.

## Claude nhận kiểm và phát hành

1. Kiểm đúng SHA được bàn giao, gate và CI. Kiểm main/số phiên bản mới trước merge.
2. Trên bench chạy migrate, đối chiếu cả hai Server Script bằng minvoice_kich_ban.doi_chieu. Thử script qua safe_exec của Frappe với HTTP được thay bằng stub, không gửi chứng từ thuế thử ra ngoài.
3. Chốt Tại chỗ/GrabFood bỏ qua nạp; Pancake sai ID/phân trang chưa hết vẫn dừng; thông tin khách giữ nguyên; snapshot lạ chặn migrate.
4. Khi đạt, merge/deploy theo phân công anh Việt, kiểm Patch Log và hash script trên site. Không phát hành lại HDB đã có ID/số thuế để thử; quan sát lượt xuất rải được phép tiếp theo và Error Log.

## Còn mở riêng

Làm tròn SI VND, thuế suất từng dòng và thống nhất ba builder chưa được sửa trong PR này. Giá vốn cả năm tờ tặng chờ kế toán chốt, không tự ghi Nợ64181/Có155 khi chưa có căn cứ kho.

Đối với thuế: core ERPNext de59166 giữ item_wise_tax_details theo item_row/tax_row (không theo item_code). Chỉ đặt precision0 vẫn có thể sinh grand_total_diff ở thuế bao gồm giá; không được coi đổi precision là đủ. Cần kiểm tổng gross, net, VAT, chiết khấu và GL đồng thời, giữ chứng từ cũ và precision của Journal Entry.

## Sửa finding deploy vòng1

Claude đã tái hiện migrate có dong_bo_cau_truc #v454 nhưng script vẫn v449.
Đã bổ sung patch minvoice_v454.py và đăng ký vào patches.txt. Patch gọi trực tiếp
minvoice_kich_ban.dong_bo, không nuốt lỗi script lạ. Ca thuần mô phỏng Patch Log
đã chạy hết các bản cũ, kiểm patch mới thực sự gọi đồng bộ đúng một lần.
Gate sau sửa: 2.650 ca đạt. Đây chưa thay thế bằng chứng migrate thật.

Claude chạy lại từ script v449 và Patch Log cũ, migrate bình thường, không gọi
dong_bo bằng tay để làm xanh ca kiểm. Đối chiếu hash cả hai script với ban_moi,
doi_chieu phải trả moi; migrate lần hai không đổi hash. Thử script lạ phải dừng
patch và không ghi Patch Log thành công cho minvoice_v454. Sau đó chạy lại ca
safe_exec nguồn như vòng1. Chỉ có mốc dong_bo_cau_truc #v454 là chưa đủ.
