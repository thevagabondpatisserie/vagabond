# Issue322: trình bày SePay cho TTNB

Owner Codex, branch codex/sepay-nhan-tai-khoan, base2b3484e8.

A7: chỉ chuỗi mới bỏ gạch. Phát hiện duyet ghi đè noi_dung_ck nên chuyển
sang chỉ điền ô trống, giữ nguyên phiếu cũ. Không migrate sửa dữ liệu.
A6: nhãn ngân hàng/bốn số cuối từ Bank Account, đưa vào ứng viên, kết quả
khớp chung và kết quả TTNB hàng loạt. Chip TTNB từ mapping, tài khoản chưa
map có chẩn đoán, không hardcode Shinhan. Điều kiện khớp tiền/mã giữ nguyên.

Local3032/3032, patch27/27, cổng0. Chưa bench/UI live, cần Claude review,
đặc biệt vòng đời nội dung cũ, giới hạn500 dòng sao kê và phân quyền danh
sách tài khoản. Bản495 tách khỏi PR321/v494, chưa merge/deploy.

## PR323 - review F1/F2

Đẩy lọc bank_account xuống truy vấn trước limit500; ca dựng501 dòng của
tài khoản đông và một dòng tài khoản ít, kiểm dòng ít vẫn được lấy.
Chip dùng CSS chips/chip/on có sẵn. Chưa xử lý F3-F7 (quyền chẩn đoán,
escape kép, trạng thái/fallback, giới hạn danh sách, truy vấn nhãn trùng).
Không chốt sẵn sàng phát hành chỉ vì CI trước xanh.

## PR323 F3-F7

Chẩn đoán tài khoản chưa nối chỉ trả vai kế toán/quản trị. Truyền nhãn
đã đọc vào truy vấn sao kê, không đọc lại. Ca gọi ung_vien kiểm hai vai,
tham số lọc và nhãn dùng chung. Bỏ escape kép ở nội dung đưa vào baoTin,
giữ câu Đã chi kể cả response cũ thiếu nhãn. Trả tối đa5 dòng đã khớp,
UI chỉ liệt kê khi tổng không quá5; các số đếm toàn lô giữ nguyên.
Cần Claude review và bench SHA mới, chưa phát hành.
