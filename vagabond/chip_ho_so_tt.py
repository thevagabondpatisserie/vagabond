"""APP cần nhìn riêng bước duyệt và việc còn thiếu (#247, PR263).

Đã thanh toán không chứng minh đủ hóa đơn hoặc đã cấn nợ. Các chip chỉ
khẳng định dữ liệu đã đọc, không suy ra nghiệp vụ chưa được triển khai.
Phép thuần dùng chung cho mọi loại hồ sơ trong danh sách.
"""

NHAN = {
	"kiem_lai": "Cần kiểm tra đối chiếu",
	"qua_han": "Quá hạn trả",
	"thieu_unc": "Chưa có UNC",
	"chua_noi_sao_ke": "Chưa nối sao kê",
	"cho_hoa_don": "Chờ hóa đơn đến sau",
	"da_noi_hoa_don": "Đã nối hóa đơn bổ sung",
	"da_chi": "Đã chi theo hồ sơ",
	"cho_lau": "Trả trước chờ quá 7 ngày",
}


def chip_cua_dong(d):
	"""Không nhắc đi chuyển tiền trên hồ sơ đã hủy hoặc bị từ chối."""
	if d.get("trang_thai") in ("Huy", "Tu choi"):
		return []
	ra = []
	if d.get("canh_bao_doi_chieu"):
		ra.append("kiem_lai")
	if (d.get("tre_ngay") or 0) > 0:
		ra.append("qua_han")
	# Phiếu trả trước có cửa UNC/đối chiếu riêng. Không diễn giải giá trị
	# co_unc=0 mà nguồn gom_phieu đang gán mặc định thành thiếu thật.
	if d.get("trang_thai") == "Da duyet" and not d.get("la_phieu_chi"):
		if not d.get("co_unc"):
			ra.append("thieu_unc")
		if not d.get("ma_giao_dich"):
			ra.append("chua_noi_sao_ke")
	if (d.get("so_cho_hoa_don") or 0) > 0:
		ra.append("cho_hoa_don")
	if (d.get("so_da_noi_hoa_don") or 0) > 0:
		ra.append("da_noi_hoa_don")
	if d.get("trang_thai") == "Da thanh toan" and not d.get("canh_bao_doi_chieu"):
		ra.append("da_chi")
	if (d.get("cho_ngay") or 0) > 7:
		ra.append("cho_lau")
	return ra
