# Issue #247: đối chiếu thanh toán APP

Ảnh lỗi là Hồ sơ thanh toán APP.26.09.015. Chưa truy vấn sao kê production
nên chưa kết luận dòng cụ thể bị thiếu đồng bộ hay không khớp nội dung.
Nguồn đã xác nhận: bộ dò bỏ `reference_number`, không chặn đuôi mã dài,
cộng lặp một dòng khi nội dung lặp mã; nút khớp tay chỉ có sau thanh toán.

## Hướng xử lý

- Tất cả loại Hồ sơ thanh toán dùng một cửa Đối chiếu tay sau khi duyệt.
- Danh sách lấy Bank Transaction đã submit, chiều chi, cùng nguồn chi.
  Có tìm nội dung/tham chiếu, lọc ngày và tiền; nêu lý do không chọn được.
- Mã gán là Bank Transaction.name, không phải chuỗi tham chiếu tùy ý.
  Mã cũ chỉ được dùng khi quy về duy nhất một bản ghi, nếu không phải chọn lại.
- Chọn tay giữ hồ sơ Đã duyệt. Ghi nhận đã thanh toán vẫn cần UNC và bộ
  bút toán đúng. Dò mã tự động dùng cùng các kiểm tra với chọn tay.
- Sau submit PE/JE, trước commit hồ sơ: gọi add_payment_entries + save của
  Bank Transaction. Core tính allocated_amount và clearance_date từ GL.
  Kiểm lại đủ bộ liên kết và không còn unallocated. Không thêm DocType.
- Khóa hồ sơ rồi sao kê, đọc lại, kiểm chủ cả mã bản ghi/tham chiếu cũ;
  controller kiểm cả Desk/API đổi mã. Retry không sinh bút toán mới.
- Hồ sơ đã ghi sổ: đối chiếu tay chỉ nối bộ bút toán đã có và đã kiểm đủ.

## Core đã đọc

ERPNext `de591661b9ba0bd3f62ac25b99b5c85c723515f6`:
`accounts/doctype/bank_transaction/bank_transaction.py`, các hàm
`add_payment_entries`, `before_update_after_submit`, `allocate_payment_entries`,
`get_clearance_details`. Lõi đòi GL có tài khoản ngân hàng tương ứng, vì vậy
không nối PE/JE nháp. Frappe `f33ac3f00ab818e21b25ddbec93efb653fd9aa1b`:
`model/document.py` hỗ trợ `get_doc(..., for_update=True)` cho parent/child.
Đây là core pin trong workflow bench; không nhận là xác minh core live.

## Phạm vi và cổng còn lại

- Một giao dịch thanh toán toàn bộ khoản còn phải chuyển, một nguồn chi,
  VND. Một APP có thể sinh nhiều PE theo nhà cung cấp, hoặc JE cho tiện ích.
- Trả nhiều lần, phí, nhiều nguồn chi: chỉ dẫn kế toán tới Đối chiếu ngân hàng
  lõi, không tự cộng tiền để đánh dấu đủ. Cổng tạm ứng chưa có bù trừ giữ nguyên.
- Không tự chạy scheduler ghi sổ hồ sơ cũ, không backfill, không gửi thư thật.
  Dò tự động nghĩa là tự tìm giao dịch khi người dùng dò/ghi nhận; chưa có
  tự động hoàn tất không cần người bấm.
- Chưa thay đổi luồng phiếu chi lẻ Payment Entry hoặc TTNB.
- Draft chờ bench theo SHA, review độc lập, kiểm UI trên app và đọc-only
  sao kê của hồ sơ được báo. Cần kiểm cạnh tranh hai kết nối, quyền FIN
  thật và hủy/đảo liên kết trước khi phát hành. Đặt phiên bản tăng từ main
  mới nhất khi chuẩn bị phát hành; không merge/deploy trong phiên này.
