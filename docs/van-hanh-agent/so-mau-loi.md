# Sổ mẫu lỗi Codex và cách làm mỗi vòng rà

Chép từ instruction project bản 22/11/2026 (mục H1 tới H8) để Codex và bot trên GitHub cùng đọc. Instruction project vẫn là bản anh Việt dán; hai bản lệch nhau thì báo anh chốt.

Mục tiêu: mỗi PR tối đa 2 vòng Codex. Phần lớn vòng thừa là CÙNG MỘT LOẠI lỗi Codex chỉ ra ở chỗ khác.

H1. TỰ RÀ TRƯỚC KHI GỌI CODEX. Đọc lại toàn bộ diff theo sổ mẫu lỗi (H8) và E2. Với từng loại có dính, trả lời câu hỏi kiểm và phải có ca kiểm chặn. Ghi trong bàn giao một dòng: "Tự rà: loại 1, 3, 4 có dính, ca kiểm X, Y, Z; loại khác không dính; E2: N màn, ảnh chụp ...".

H2. SỬA THEO LOẠI, KHÔNG SỬA THEO CHỖ. Codex chỉ ra một lỗi thì gọi tên loại của nó, rồi quét TOÀN BỘ diff và các hàm cùng gọi nguồn đó, sửa hết trong MỘT vòng. Ghi rõ: "Thuộc loại N. Đã quét X chỗ cùng loại, sửa Y chỗ (Codex chỉ 1)."

H3. Ca đỏ trước khi sửa. Viết ca kiểm dựng đúng thao tác Codex mô tả, chạy trên mã CŨ thấy đỏ, sửa, chạy lại thấy xanh. Chỉ dựng trên bench khi lỗi nói về hành vi của chính ERPNext. Dò chuỗi trong mã nguồn KHÔNG phải kiểm thử. Mã trình duyệt thì nạp cả trang vào node bằng vagabond/khung/kiem_thu/gia_lap_trang.js. Không ra được ca đỏ thì ghi "không tái hiện được trong các điều kiện đã kiểm" kèm điều kiện. Góp ý về sự thật trong repo (đường dẫn, tệp có hay không) thì kiểm bằng lệnh đầy đủ, không cắt kết quả bằng head (#607).

H4. MỘT VÒNG LÀ MỘT LƯỢT ĐẨY. Sửa xong mọi góp ý và mọi chỗ cùng loại rồi mới đẩy. Bài học sự cố viết MỘT lần lúc PR sắp merge.

H5. ĐỘT BIẾN. Viết ca xong cố tình làm hỏng lại chỗ vừa sửa. Đột biến không làm đổ ca có bốn nguyên nhân:
- (a) bộ kiểm yếu;
- (b) mẫu tìm-thay không khớp, luôn khẳng định khớp đúng một lần;
- (c) dư một lớp bảo vệ;
- (d) Python chạy .pyc cũ: dùng python3 -B.

Bộ đột biến chạy lâu có thể bị dừng giữa chừng: kiểm lại tệp nguồn đã trả về nguyên trạng trước khi làm tiếp. Báo cáo đúng con số.

H6. Vòng 3 mà Codex còn chỉ ra lỗi thuộc loại đã có trong sổ: dừng, quét lại cả PR theo loại đó. Loại CHƯA có trong sổ thì sau khi PR merge đề xuất anh thêm một dòng vào H8.

H7. MERGE RỒI CHƯA PHẢI XONG. Đọc tiếp comment trên PR đã đóng. Lỗi phát hiện sau merge thì mở PR mới từ main mới nhất, liên kết PR cũ. Không revert main. Gộp hai PR đã rà đạt thì nhánh gộp chỉ chứa phần gỡ xung đột; ghi rõ "N tệp lấy nguyên từ head đã rà, M tệp gỡ xung đột".

H8. SỔ MẪU LỖI CODEX. Mỗi dòng: loại, câu hỏi kiểm, PR đã dính.
1. Đọc trước khi khoá: hai người bấm cùng lúc thì sao? Mọi chỗ đọc số dư, trạng thái, tổng rồi ghi hoặc trả lời đều phải đọc SAU khoá (for update, get_lock). (#531, #527, #541, #542, #544, #557)
2. Đọc thiếu: có LIMIT, phân trang, chỉ trang đầu, hay lọc SAU khi cộng dồn không? Có ca hơn 10, hơn 20 bản ghi. Việc nền có trần số bản ghi thì bản ghi cũ không xử được có chặn bản ghi mới không? (#531, #534, #545, #592)
3. Nhiều nguồn sự thật: con số này còn được tính ở chỗ nào khác? Grep hết, gom một hàm, ca chốt "không còn chỗ tự tính". (#531, #532, #552)
4. Chạy lại và đổi trạng thái: bấm hai lần, đọc lại, huỷ giữa chừng, hai lượt ngược thứ tự thì sao? (#538, #541, #544, #546, #527, #557)
5. Dữ liệu và Cài đặt cũ trên site: bản ghi tạo trước bản vá thì mã mới có áp không? Đổi mặc định phải kèm bước nâng chạy một lần. (#552, #554)
6. Mốc ngày giờ: cuối ngày, mốc chốt, cuối tháng, múi giờ, tháng chưa hết? Có ca 28/02, 31, nửa đêm. (#536, #527, #557, #592)
7. Phạm vi và quyền: đúng pháp nhân, điểm bán, người đứng tên, vai thật trên site chưa? (#541, #544, #545, #557, #581)
8. Bản nháp và màn mở lại: lưu dở, mở lại, lưu nối nhau, màn cũ trả lời muộn ghi đè màn mới thì sao? (#526, #536, #543, #545)
9. Chuẩn chạm của CẢ PR: mọi nút, ô, chip MỚI cao từ 44 điểm, chữ từ 13 điểm, 390 px không tràn? (#528, #545, #553)
10. Bản giả khác ERPNext thật: cột đọc bằng SQL có thật trên doctype không, ghi sổ và kho thật có khác bản giả không? (#527, #541, #551, #553)
11. Chọn "bản ghi vừa tạo" bằng chênh lệch danh sách toàn hệ thống: phải lọc theo khoá riêng của đúng lần đó. (#562)
12. Ô gõ tay cho mã danh mục: thay bằng ô chọn có tìm VÀ kiểm lại mã ở mọi đường ghi. (#581, #584)
13. Màn thiếu khung chuẩn: chip trạng thái có đếm, chip từng dòng, ảnh món, ô tìm, ba trạng thái phụ. (#545, #553, #584)
14. Giá trị rỗng hợp lệ bị thay mặc định: 0, chuỗi rỗng, False có bị "or mặc định" nuốt mất không? (#581)
15. Dữ liệu thật và phạm vi ca kiểm (mới 22/11): ca kiểm, tài liệu có chép dữ liệu thật từ site không? Ca bench hay hàm lịch trong ca có đọc, sửa, ghi sổ bản ghi thật không, khi ca chạy trên site? Phải dùng dữ liệu giả, cách ly khoá bản ghi, truyền danh sách bản ghi của ca, và có phép kiểm chứng minh bản ghi thật giữ nguyên. (#592)
