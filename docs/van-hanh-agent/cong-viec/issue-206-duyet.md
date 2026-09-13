# Bản chốt lô và hạn dùng, PR #302 / v489

Theo quyết định anh Việt ngày 13/09 và đặc tả PR302 comment5653018176. Đây là nội dung triển khai để nghiệm thu; chưa chứng minh đã deploy.

1. Giữ Batch và lịch sử lô. FEFO chọn hàng còn hạn với HSD gần trước, lô không biết hạn sau hàng có hạn còn tốt, lô hết hạn/tắt là vòng vét cuối. Không dùng thứ tự mã lô làm thứ tự lấy hàng.
2. Lô đã chọn thiếu thì giữ phần đủ, bù từ lô khác cùng mã và kho. Bao gồm lô tay và gói nháp trên Desk, cả gói cấp chưa đủ lượng dòng. Nhiều dòng dùng chung số tồn; vẫn chặn kho thật thiếu, sai mã/kho/serial/UOM hoặc gói không thuộc chứng từ.
3. HSD và trạng thái tắt chỉ cảnh báo. Bỏ hẳn công tắc chặn, patch gỡ Custom Field và giá trị Single. Phiếu ghi rõ lô quá hạn/tắt và phần bù lô. Không sửa HSD hoặc chứng từ cũ.
4. Nhận mua thiếu/cận HSD vẫn ghi được. Tạo Batch mới với HSD đã nhập hoặc để trống, không tự cộng shelf life thay ngày trên nhãn ở API nhận mua. Lô mới ở các cửa khác giữ tính shelf life; lô đã lưu không bị suy lại hạn. Cảnh báo được lưu trên phiếu và hiện ở màn nhận.
5. Phạm vi: bảy purpose Stock Entry trong lo_het_han.PHIEU_BI_CHAN; Purchase Receipt, Purchase Invoice cập nhật kho, Delivery Note và Sales Invoice cập nhật kho. Chỉ thay phép kiểm hạn trên controller tương ứng, không thay StockController chung. Stock Reconciliation chưa đổi và chưa nằm trong nghiệm thu này.
6. Giữ mã máy cấp LO-yymmdd-nnnnnn, giữ mã NCC đã nhập. Không đổi phương pháp giá vốn, không bật tồn âm, không đổi tên Item/BOM/dữ liệu kho thật.

Các file Excel tiền tố mã, cặp thay thế và tem tách riêng. Gelatine phantom đã có PR306 kiểm riêng, không tự đổi công thức hay tạo mã mới.

Cổng trước phát hành: local, CI, Claude review và bench trên SHA cuối; hai lượt bench không còn chứng từ/số lượng lệch. Ca thật phải chạm ghi sổ/hủy, không lấy mock thay kết quả Document. Anh Việt duyệt nội dung nghiệm thu cuối trước merge/deploy v489.
