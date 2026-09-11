# Đối chứng GetInfoInvoice ngày11/09/2026

Codex đọc trực tiếp từ production qua System Console, ô commit tắt. Chỉ Login và GetInfoInvoice; không phát hành, ký, gỡ cờ hoặc đổi cấu hình. Dùng cùng tài khoản trong MInvoice Phat Hanh Settings, không ghi thông tin đăng nhập vào tài liệu.

- Dương tính: keyApi HDB-26-09-01429 trả code00/oktrue, data.key_api đúng, số12925, ký hiệu1C26MPV, ngày08/09/2026. Khớp số lưu trong ERP.
- Âm tính: keyApi CODEX-READONLY-NOT-ISSUED-20260911-F6062A4 trả chính xác ba khóa sau.
- Tờ thật giữ cờ: HDB-26-09-01650 trả chính xác cùng cấu trúc.

```json
{"code":"29404","message":"Get Invoice fail because not found  invoice is not exist.","ok":false}
```

Nguồn đối chiếu ý nghĩa mã: tài liệu M-Invoice2.0 v1.0.9, mục11 tra bằng keyApi trang25, bảng mã trang31. Bản tài liệu được đăng lại tại https://www.scribd.com/document/974235861/M-Invoice-2-0-Document-API-v1-0-9-1; không phải xác nhận riêng từ nhân viên nhà cung cấp. Mã29404 được mô tả là không tìm thấy hóa đơn cần xem. Không dùng mã9999 hoặc riêng chữnotfound để suy nghĩa.

Chốt triển khai: chỉ nhận đúng toàn bộ ba khóa, giá trị và kiểu. Thêm dữ liệu khác cũng giữ cờ. Mỗi lượt vẫn phải đối chứng tờ có thật và mã không tồn tại; từng chứng từ phải được hỏi riêng; trước gỡ giữ khóa và đọc lại dấu ID/cờ. Phản hồi này không chứng minh mọi tờ09/09 chưa xuất, không chứng minh tờ tạo tay bằng mã khác không tồn tại.

Live09/09:197SI gồm120ghi sổ,77nháp;117ghi sổ giữ cờ. Cổng web đúng ký hiệu1C26MPV có tờ12944 ngày09/09 dạngThay thế, đơn92680. Không lấy thiếuID trong ERP làm bằng chứng chưa phát hành. Cần đối chiếu phạm vi trước chạy thật.
