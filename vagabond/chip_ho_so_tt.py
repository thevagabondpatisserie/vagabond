"""APP cần nhìn riêng bước duyệt và việc còn thiếu (#247, PR263).

Đã thanh toán không chứng minh đủ hóa đơn hoặc đã cấn nợ. Các chip chỉ
khẳng định dữ liệu đã đọc, không suy ra nghiệp vụ chưa được triển khai.
Phép thuần dùng chung cho mọi loại hồ sơ trong danh sách.
"""

NHAN = {
	"cho_doi_chieu_sau": "Chờ đối chiếu sau",
	"kiem_lai": "Cần kiểm tra đối chiếu",
	"qua_han": "Quá hạn trả",
	"thieu_unc": "Chưa có UNC",
	"chua_noi_sao_ke": "Chưa nối sao kê",
	"cho_hoa_don": "Chờ hóa đơn đến sau",
	"da_noi_hoa_don": "Đã nối hóa đơn bổ sung",
	"da_chi": "Đã chi theo hồ sơ",
	"cho_lau": "Trả trước chờ quá 7 ngày",
}

# Một dòng giải thích cho mỗi chip lọc: chip là gì và người xem cần làm gì.
# Mã nào trong NHAN cũng phải có mô tả ở đây (ca kiểm chốt).
MO_TA = {
	"cho_doi_chieu_sau": "Đã ghi nhận trả kèm lý do khi sao kê chưa đủ. Kế toán chọn các dòng sao kê ở Đối chiếu tay hoặc đối chiếu trong ERPNext.",
	"kiem_lai": "Bút toán hoặc sao kê đã đổi sau khi ghi nhận. Mở hồ sơ để xem cảnh báo và đối chiếu lại.",
	"qua_han": "Đã quá hạn trả mà hồ sơ chưa thanh toán xong.",
	"thieu_unc": "Hồ sơ đã duyệt nhưng chưa đính uỷ nhiệm chi.",
	"chua_noi_sao_ke": "Hồ sơ đã duyệt nhưng chưa nối với dòng sao kê nào.",
	"cho_hoa_don": "Đã trả trước, còn chờ nhà cung cấp gửi hoá đơn.",
	"da_noi_hoa_don": "Đã nối hoá đơn đến sau. Chưa có nghĩa là đã cấn nợ.",
	"da_chi": "Đã ghi nhận chuyển tiền theo hồ sơ. Chưa có nghĩa là đã đủ chứng từ.",
	"cho_lau": "Phiếu trả trước đã chờ hơn 7 ngày mà chưa xong.",
}


def chip_cua_dong(d):
	"""Không nhắc đi chuyển tiền trên hồ sơ đã hủy hoặc bị từ chối."""
	if d.get("trang_thai") in ("Huy", "Tu choi"):
		return []
	ra = []
	if d.get("cho_doi_chieu_sau"):
		ra.append("cho_doi_chieu_sau")
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
