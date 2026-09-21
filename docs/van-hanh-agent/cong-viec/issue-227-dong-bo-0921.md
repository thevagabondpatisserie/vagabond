# Đồng bộ đầu vào - bổ sung21/09/2026

Owner Codex, branch codex/fix-minvoice-sync-20260921, base3421058f.
Phạm vi: minvoice_chung_tu.py và hồi quy; không đổi hệ số/ánh xạ thật trong patch.

Hai lỗi tái hiện bằng bảng giả: exception từng tờ vẫn ở message_log và tràn response Desk; nan_dau_dong đảo qty âm của dòng giá0 thành dương do -1*0 không <0. Core response.py gửi message_log kể cả exception đã bắt. Lỗi rollback trước đây cũng bị nuốt, có thể cho caller tiếp tục commit; nay đẩy ra ngoài.

Sửa: giữ log trước tờ, gỡ riêng thông báo đã bắt khỏi local.message_log, vẫn trả lý do có số hóa đơn; giữ dấu qty cho dòng0tiền, dòng mô tả trống dùng qty-1 trong phiếu âm. Không ép dòng tiền dương của điều chỉnh hỗn hợp thành âm. Không đoán hệ số UOM hoặc bỏ validation.

3ca mới baseline lỗi, bản sửa đạt; tổng3182 local. Thêm ca PI thật âm có quà0tiền/mô tả, chưa chạy bench. Không sửa nguồn/hạch toán thật. Chờ xác nhận ánh xạ/quy cách thiếu theo luồng nội bộ, chưa đủ tuyên bố xử lý hết tồn đọng. Không lưu chi tiết chứng từ thật trong repo.

Cần tiếp: bench đúngSHA, kiểm modal HTTP thật, review, phát hành sau cổng; đối chiếu nguồn/PI theo ngày và tồn đọng sau deploy. Không lấy max ngày PI làm bằng chứng đồng bộ đủ nhà cung cấp.

Bổ sung: nguồn chỉ có mã được đếm riêng nguon_chua_du trong báo cáoDesk, không bị hiểu là đã có hóa đơn đầy đủ. Cô lập message_log ở cả bước kéo và dựng. APPVER514, chưa phát hành.
