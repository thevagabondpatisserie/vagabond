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
