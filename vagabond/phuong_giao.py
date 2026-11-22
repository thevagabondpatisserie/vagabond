"""Phường giao theo phường mới (BẢN 2 mục 2.3, v684). THUẦN, không chạm Frappe.

Từ 01/7/2025 TP.HCM dùng phường mới theo Nghị quyết 1685/NQ-UBTVQH15. Ô
"Phường giao" trên trang đặt bánh cho khách gõ tìm theo tên phường mới, tên
quận cũ hoặc tên phường cũ, có dấu hay không dấu.

Nguồn dữ liệu (đọc 22/11/2026):
  - Tên và mã phường mới: bảng địa chỉ mới của Pancake
    (pos.pages.fm/api/v1/geo/communes?province_id=84_VN129), để tên trên
    đơn khớp đúng chữ Pancake lưu.
  - Phường cũ nào ghép vào phường mới nào: Nghị quyết 1685. Bảng nối cũ mới
    của Pancake thiếu nhiều dòng và có chỗ sai (Phường 5 Gò Vấp bị ghi vào
    Đức Nhuận), nên không dùng.

Chỉ có các phường thuộc 20 khu vực đang giao (don_web.QUAN), không mở rộng.

Không có phí dự kiến theo phường (anh Việt bỏ 22/11/2026): ô Phường giao chỉ
để chọn phường; phí giao chỉ tính theo địa chỉ khách gõ (giao_hang.phi_giao).

Mỗi dòng: (mã Pancake, tên phường mới, khu vực giao, quận cũ, phường cũ, loại)
  loai ""        : thuộc vùng đang giao.
  loai "mot_phan": có phần ngoài vùng giao (anh Việt duyệt 22/11/2026). KHÔNG
                   nhận nguyên phường: trang báo "chưa tính được, gõ địa chỉ để
                   có phí"; có địa chỉ thì hệ thống quyết theo khoảng cách (luật
                   bán kính), ngoài bán kính thì mời khách nhận tại cửa hàng.
  Bình Phú, Bình Hưng Hòa nằm trên hai quận cũ nhưng trọn trong vùng giao.
"""

import re
import unicodedata

TIEN_TO = "84_VN129"

# Phường cũ ghi tắt "P5" là "Phường 5".
BANG = [
	# Quận 1
	("01", "Sài Gòn", "q1", "Quận 1", ["Bến Nghé", "Đa Kao", "Nguyễn Thái Bình"], ""),
	("02", "Tân Định", "q1", "Quận 1", ["Tân Định", "Đa Kao"], ""),
	("03", "Bến Thành", "q1", "Quận 1", ["Bến Thành", "Phạm Ngũ Lão", "Cầu Ông Lãnh", "Nguyễn Thái Bình"], ""),
	("04", "Cầu Ông Lãnh", "q1", "Quận 1", ["Nguyễn Cư Trinh", "Cầu Kho", "Cô Giang", "Cầu Ông Lãnh"], ""),
	# Quận 3
	("015", "Bàn Cờ", "q3", "Quận 3", ["P1", "P2", "P3", "P5", "P4"], ""),
	("05", "Xuân Hòa", "q3", "Quận 3", ["Võ Thị Sáu", "P4"], ""),
	("06", "Nhiêu Lộc", "q3", "Quận 3", ["P9", "P11", "P12", "P14"], ""),
	# Quận 4
	("07", "Xóm Chiếu", "q4", "Quận 4", ["P13", "P16", "P18", "P15"], ""),
	("08", "Khánh Hội", "q4", "Quận 4", ["P8", "P9", "P2", "P4", "P15"], ""),
	("09", "Vĩnh Hội", "q4", "Quận 4", ["P1", "P3", "P2", "P4"], ""),
	# Quận 5
	("10", "Chợ Quán", "q5", "Quận 5", ["P1", "P2", "P4"], ""),
	("11", "An Đông", "q5", "Quận 5", ["P5", "P7", "P9"], ""),
	("12", "Chợ Lớn", "q5", "Quận 5", ["P11", "P12", "P13", "P14"], ""),
	# Quận 6
	("13", "Bình Tây", "q6", "Quận 6", ["P2", "P9"], ""),
	("14", "Bình Tiên", "q6", "Quận 6", ["P1", "P7", "P8"], ""),
	("16", "Bình Phú", "q6", "Quận 6", ["P10", "P11", "P16 (Quận 8)"], ""),
	("17", "Phú Lâm", "q6", "Quận 6", ["P12", "P13", "P14"], ""),
	# Quận 7
	("18", "Tân Thuận", "q7", "Quận 7", ["Bình Thuận", "Tân Thuận Đông", "Tân Thuận Tây"], ""),
	("19", "Phú Thuận", "q7", "Quận 7", ["Phú Thuận", "Phú Mỹ"], ""),
	("20", "Tân Mỹ", "q7", "Quận 7", ["Tân Phú", "Phú Mỹ"], ""),
	("21", "Tân Hưng", "q7", "Quận 7", ["Tân Phong", "Tân Quy", "Tân Kiểng", "Tân Hưng"], ""),
	# Quận 8
	("22", "Chánh Hưng", "q8", "Quận 8", ["P4", "Rạch Ông", "Hưng Phú", "P5"], ""),
	("23", "Phú Định", "q8", "Quận 8", ["P14", "P15", "Xóm Củi", "P16"], ""),
	("24", "Bình Đông", "q8", "Quận 8", ["P6", "P7", "P5", "An Phú Tây (Bình Chánh)"], "mot_phan"),
	# Quận 10
	("25", "Diên Hồng", "q10", "Quận 10", ["P6", "P8", "P14"], ""),
	("26", "Vườn Lài", "q10", "Quận 10", ["P1", "P2", "P4", "P9", "P10"], ""),
	("27", "Hòa Hưng", "q10", "Quận 10", ["P12", "P13", "P15", "P14"], ""),
	# Quận 11
	("28", "Minh Phụng", "q11", "Quận 11", ["P1", "P7", "P16"], ""),
	("29", "Bình Thới", "q11", "Quận 11", ["P3", "P10", "P8"], ""),
	("30", "Hòa Bình", "q11", "Quận 11", ["P5", "P14"], ""),
	("31", "Phú Thọ", "q11", "Quận 11", ["P11", "P15", "P8"], ""),
	# Quận 12
	("32", "Đông Hưng Thuận", "q12", "Quận 12", ["Tân Thới Nhất", "Tân Hưng Thuận", "Đông Hưng Thuận"], ""),
	("33", "Trung Mỹ Tây", "q12", "Quận 12", ["Tân Chánh Hiệp", "Trung Mỹ Tây"], ""),
	("34", "Tân Thới Hiệp", "q12", "Quận 12", ["Hiệp Thành", "Tân Thới Hiệp"], ""),
	("35", "Thới An", "q12", "Quận 12", ["Thạnh Xuân", "Thới An"], ""),
	("36", "An Phú Đông", "q12", "Quận 12", ["Thạnh Lộc", "An Phú Đông"], ""),
	# Bình Tân
	("37", "An Lạc", "binh-tan", "Bình Tân", ["Bình Trị Đông B", "An Lạc A", "An Lạc"], ""),
	("38", "Bình Tân", "binh-tan", "Bình Tân", ["Bình Hưng Hòa B", "Bình Trị Đông A", "Tân Tạo"], ""),
	("39", "Tân Tạo", "binh-tan", "Bình Tân", ["Tân Tạo A", "Tân Tạo", "Tân Kiên (Bình Chánh)"], "mot_phan"),
	("40", "Bình Trị Đông", "binh-tan", "Bình Tân", ["Bình Trị Đông", "Bình Hưng Hòa A", "Bình Trị Đông A"], ""),
	("41", "Bình Hưng Hòa", "binh-tan", "Bình Tân", ["Bình Hưng Hòa", "Bình Hưng Hòa A", "Sơn Kỳ (Tân Phú)"], ""),
	# Bình Thạnh
	("42", "Gia Định", "binh-thanh", "Bình Thạnh", ["P1", "P2", "P7", "P17"], ""),
	("43", "Bình Thạnh", "binh-thanh", "Bình Thạnh", ["P12", "P14", "P26"], ""),
	("44", "Bình Lợi Trung", "binh-thanh", "Bình Thạnh", ["P5", "P11", "P13"], ""),
	("45", "Thạnh Mỹ Tây", "binh-thanh", "Bình Thạnh", ["P19", "P22", "P25"], ""),
	("46", "Bình Quới", "binh-thanh", "Bình Thạnh", ["P27", "P28"], ""),
	# Gò Vấp
	("47", "Hạnh Thông", "go-vap", "Gò Vấp", ["P1", "P3"], ""),
	("48", "An Nhơn", "go-vap", "Gò Vấp", ["P5", "P6"], ""),
	("49", "Gò Vấp", "go-vap", "Gò Vấp", ["P10", "P17"], ""),
	("50", "An Hội Đông", "go-vap", "Gò Vấp", ["P15", "P16"], ""),
	("51", "Thông Tây Hội", "go-vap", "Gò Vấp", ["P8", "P11"], ""),
	("52", "An Hội Tây", "go-vap", "Gò Vấp", ["P12", "P14"], ""),
	# Phú Nhuận
	("53", "Đức Nhuận", "phu-nhuan", "Phú Nhuận", ["P4", "P5", "P9"], ""),
	("54", "Cầu Kiệu", "phu-nhuan", "Phú Nhuận", ["P1", "P2", "P7", "P15"], ""),
	("55", "Phú Nhuận", "phu-nhuan", "Phú Nhuận", ["P8", "P10", "P11", "P13", "P15"], ""),
	# Tân Bình
	("56", "Tân Sơn Hòa", "tan-binh", "Tân Bình", ["P1", "P2", "P3"], ""),
	("57", "Tân Sơn Nhất", "tan-binh", "Tân Bình", ["P4", "P5", "P7"], ""),
	("58", "Tân Hòa", "tan-binh", "Tân Bình", ["P6", "P8", "P9"], ""),
	("59", "Bảy Hiền", "tan-binh", "Tân Bình", ["P10", "P11", "P12"], ""),
	("60", "Tân Bình", "tan-binh", "Tân Bình", ["P13", "P14", "P15"], ""),
	("61", "Tân Sơn", "tan-binh", "Tân Bình", ["P15"], ""),
	# Tân Phú
	("62", "Tây Thạnh", "tan-phu", "Tân Phú", ["Tây Thạnh", "Sơn Kỳ"], ""),
	("63", "Tân Sơn Nhì", "tan-phu", "Tân Phú", ["Tân Sơn Nhì", "Sơn Kỳ", "Tân Quý", "Tân Thành"], ""),
	("64", "Phú Thọ Hòa", "tan-phu", "Tân Phú", ["Phú Thọ Hòa", "Tân Thành", "Tân Quý"], ""),
	("65", "Tân Phú", "tan-phu", "Tân Phú", ["Phú Trung", "Hòa Thạnh", "Tân Thới Hòa", "Tân Thành"], ""),
	("66", "Phú Thạnh", "tan-phu", "Tân Phú", ["Hiệp Tân", "Phú Thạnh", "Tân Thới Hòa"], ""),
	# Thủ Đức (khu Thủ Đức cũ)
	("67", "Hiệp Bình", "thu-duc", "Thủ Đức", ["Hiệp Bình Chánh", "Hiệp Bình Phước", "Linh Đông"], ""),
	("68", "Thủ Đức", "thu-duc", "Thủ Đức", ["Bình Thọ", "Linh Chiểu", "Trường Thọ", "Linh Tây", "Linh Đông"], ""),
	("69", "Tam Bình", "thu-duc", "Thủ Đức", ["Bình Chiểu", "Tam Phú", "Tam Bình"], ""),
	("70", "Linh Xuân", "thu-duc", "Thủ Đức", ["Linh Trung", "Linh Xuân", "Linh Tây"], ""),
	# Thủ Đức (Quận 9 cũ)
	("71", "Tăng Nhơn Phú", "thu-duc-q9", "Quận 9", ["Tân Phú", "Hiệp Phú", "Tăng Nhơn Phú A", "Tăng Nhơn Phú B", "Long Thạnh Mỹ"], ""),
	("72", "Long Bình", "thu-duc-q9", "Quận 9", ["Long Bình", "Long Thạnh Mỹ"], ""),
	("73", "Long Phước", "thu-duc-q9", "Quận 9", ["Trường Thạnh", "Long Phước"], ""),
	("74", "Long Trường", "thu-duc-q9", "Quận 9", ["Phú Hữu", "Long Trường"], ""),
	("77", "Phước Long", "thu-duc-q9", "Quận 9", ["Phước Bình", "Phước Long A", "Phước Long B"], ""),
	# Thủ Đức (Quận 2 cũ)
	("75", "Cát Lái", "thu-duc-q2", "Quận 2", ["Thạnh Mỹ Lợi", "Cát Lái"], ""),
	("76", "Bình Trưng", "thu-duc-q2", "Quận 2", ["Bình Trưng Đông", "Bình Trưng Tây", "An Phú"], ""),
	("78", "An Khánh", "thu-duc-q2", "Quận 2", ["Thủ Thiêm", "An Lợi Đông", "Thảo Điền", "An Khánh", "An Phú"], ""),
	# Nhà Bè
	("134", "Nhà Bè", "nha-be", "Nhà Bè", ["Thị trấn Nhà Bè", "Phú Xuân", "Phước Kiển", "Phước Lộc"], ""),
	("135", "Hiệp Phước", "nha-be", "Nhà Bè", ["Nhơn Đức", "Long Thới", "Hiệp Phước"], ""),
	# Bình Chánh có phần thuộc Quận 8, Bình Tân: không nhận nguyên xã.
	("114", "Tân Vĩnh Lộc", "binh-tan", "Bình Chánh", ["Vĩnh Lộc B", "Phạm Văn Hai", "Tân Tạo (Bình Tân)"], "mot_phan"),
	("116", "Tân Nhựt", "binh-tan", "Bình Chánh", ["Tân Túc", "Tân Nhựt", "Tân Tạo A (Bình Tân)", "Tân Kiên", "P16 (Quận 8)"], "mot_phan"),
	("119", "Bình Hưng", "q8", "Bình Chánh", ["Phong Phú", "Bình Hưng", "P7 (Quận 8)"], "mot_phan"),
]

# Xã (không phải phường): tên hiển thị "Xã ...".
XA = {"Nhà Bè", "Hiệp Phước", "Tân Vĩnh Lộc", "Tân Nhựt", "Bình Hưng"}


def bo_dau(s):
	"""Chữ thường, bỏ dấu, đ thành d, gom khoảng trắng."""
	s = unicodedata.normalize("NFD", str(s or "").lower().replace("đ", "d").replace("Đ", "d"))
	s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
	return " ".join(s.split())


def ten_cu(x):
	"""'P5' -> 'Phường 5'; tên khác giữ nguyên."""
	x = str(x)
	if x.startswith("P") and x[1:2].isdigit():
		return "Phường " + x[1:]
	return x


def ten_day_du(ten):
	return ("Xã " if ten in XA else "Phường ") + ten


def nhan_quan_cu(quan):
	"""Tên quận cũ (dữ liệu, ví dụ 'Quận 3'). Chữ ' cũ' khách thấy do trang ghép từ
	bảng chữ Marketing sửa được (Codex #606), máy chủ không trả câu chữ."""
	return quan


def danh_sach():
	"""Bảng phường cho trang đặt bánh: chỉ dữ liệu công khai, không có phí."""
	out = []
	for ma, ten, khu, quan, cu, loai in BANG:
		out.append({
			"ma": TIEN_TO + ma,
			"ten": ten_day_du(ten),
			"khu": khu,
			"quan_cu": nhan_quan_cu(quan),
			"cu": [ten_cu(x) for x in cu],
			"loai": loai,
		})
	return out


def tim(ma):
	ma = str(ma or "").strip()
	for p in danh_sach():
		if p["ma"] == ma:
			return p
	return None


def la_dia_chi_cu(dia_chi):
	"""Địa chỉ còn ghi Quận, Huyện, TP Thủ Đức (kiểu trước 7/2025). THUẦN.
	Cùng luật với laDiaChiCu ở web_vue/kho/thuan.js."""
	a = " " + " ".join(re.sub(r"[^a-z0-9 ]+", " ", bo_dau(dia_chi)).split()) + " "
	return bool(re.search(r" (quan|huyen) ", a) or re.search(r" (thanh pho|tp) thu duc ", a))


def dia_chi_co_phuong(dia_chi, p):
	"""Địa chỉ gửi Pancake mang tên phường mới (mục 2.3). THUẦN.

	Khách đã chọn phường mà chuỗi địa chỉ chưa có tên phường đó thì nối thêm
	", Phường ..." vào cuối. Đã có (gõ không dấu cũng tính) thì giữ nguyên,
	không nhân đôi. Không chọn phường thì không đổi gì.
	"""
	dia_chi = str(dia_chi or "").strip()
	if not p:
		return dia_chi
	ten = p["ten"]
	# Địa chỉ kiểu cũ (còn Quận, Huyện): tên phường trong đó là phường CŨ, có thể
	# trùng tên phường mới ở nơi khác, nên vẫn ghi rõ phường mới (Codex #606).
	if not la_dia_chi_cu(dia_chi) and bo_dau(ten.split(" ", 1)[1]) in bo_dau(dia_chi):
		return dia_chi
	return (dia_chi.rstrip(" ,") + ", " + ten) if dia_chi else ten

