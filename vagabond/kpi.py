# -*- coding: utf-8 -*-
"""Phân hệ KPI và hoa hồng (anh Việt chốt 01/09/2026).

Anh Việt chốt bảy điều sau bản thiết kế trình ngày 01/09:

 1. Làm thẳng trong app Vagabond, chưa cài phân hệ HR của Frappe.
 2. Chu kỳ THÁNG cho toàn bộ nhân sự.
 3. Hoa hồng Sales luỹ tiến, sàn 150 triệu, ba mốc 350/450/600 triệu.
 4. Trần 15 triệu một người một kỳ cho khối cửa hàng. Hợp đồng B2B và
    voucher đối tác bóc riêng, không tính vào doanh thu lẻ tại quầy.
 5. Trọng số điều chỉnh cho định vị bánh lạnh cao cấp: bếp nặng về hao hụt
    và hàng lỗi, sales nặng về khách quay lại chứ không phải số đơn.
 6. Cửa hàng trưởng và bếp trưởng chấm nhân viên, giám đốc chấm cấp quản lý.
    Quản lý nghỉ thì quyền duyệt bước 2 tự mở lên cho giám đốc.
 7. Phiếu chốt xong tự đẩy sang Đề nghị chi, tiền hoa hồng chuyển khoản
    tách khỏi lương cứng.

BA NGUYÊN TẮC GỐC

Máy đo được thì máy đo, người chỉ chấm cái máy không đo được. Bắt quản lý gõ
tay lại doanh thu là mở đường cho sai số và cho tranh cãi.

Chốt số một lần rồi đóng băng. Lúc duyệt, mọi con số được chụp vào phiếu.
Sau đó dữ liệu gốc có đổi thì phiếu đã duyệt không đổi theo.

Sai sót kỳ cũ điều chỉnh ở kỳ mới, không sửa kỳ cũ. Đúng điều anh Việt chốt
ngày 13/08/2026.

HAI CHỖ TRONG MỤC 3 CÒN VƯỚNG, ĐÃ BÁO ANH VIỆT

Thứ nhất, giữa sàn 150 triệu và mốc đầu 350 triệu có một khoảng trống: bán
200 triệu thì trên sàn nhưng chưa tới mốc, ra 0 đồng. Nếu đúng ý vậy thì sàn
thật là 350 triệu và con số 150 triệu không có tác dụng gì.

Thứ hai, mốc 3 viết là "2% trên TOÀN BỘ phần doanh thu vượt 400 triệu",
khác kiểu với hai mốc dưới. Nó tạo một bậc nhảy ngay tại 600 triệu: bán 599
triệu được 3.235.000, bán 601 triệu được 4.020.000. Hai triệu doanh thu
thêm mà hoa hồng nhảy 785.000. Đây đúng cái bẫy đã cảnh báo ở bản thiết kế:
người ta sẽ dồn đơn qua tháng cho đủ mốc.

Máy vẫn tính ĐÚNG NHƯ ANH VIẾT, vì đó là quyết định của anh. Nhưng bảng cấu
hình tự dò và hiện cảnh báo ở mọi điểm nhảy bậc, để lần sau anh sửa thì thấy
ngay mình đang tạo ra một bậc nhảy hay không. Xem `diem_nhay_bac`.
"""

import json

# ------------------------------------------------------------ phần thuần
# Trên mốc này KHÔNG chạm Frappe, để kiểm thử được mà không cần site.

TRUONG_CAU_HINH = "vgb_kpi_cau_hinh"

# Trạng thái phiếu, đúng năm bước anh Việt chốt.
# Giá trị LƯU trong kho viết KHÔNG dấu, đúng lệ của mọi doctype khác trong
# repo này (đề nghị chi, hồ sơ thanh toán, hoàn tiền...). Chữ có dấu để ở
# NHAN_TT bên dưới, chỉ dùng để hiện lên màn.
#
# Ngày 01/09/2026 bản v381 lỡ lưu chữ CÓ dấu trong khi danh sách của kho ghi
# không dấu. Frappe không báo lỗi, nó lặng lẽ thay bằng lựa chọn đầu danh
# sách. Phiếu dựng ra đứng ở "bước 0/5", nút duyệt biến mất, cả luồng kẹt.
TT_QUAN_LY = "Cho quan ly"
TT_KE_TOAN = "Cho ke toan"
TT_GIAM_DOC = "Cho giam doc"
TT_DUYET = "Da duyet"
TT_DA_CHI = "Da day chi"
TT_HUY = "Da huy"

CHUOI = [TT_QUAN_LY, TT_KE_TOAN, TT_GIAM_DOC, TT_DUYET, TT_DA_CHI]

NHAN_TT = {
	TT_QUAN_LY: "Chờ quản lý xác nhận",
	TT_KE_TOAN: "Chờ kế toán soát",
	TT_GIAM_DOC: "Chờ giám đốc duyệt",
	TT_DUYET: "Đã duyệt, chờ đẩy chi",
	TT_DA_CHI: "Đã đẩy sang đề nghị chi",
	TT_HUY: "Đã huỷ",
}

# Trần điểm một tiêu chí. Không chặn thì một tháng may mắn kéo cả năm, và
# người ta có động cơ dồn đơn vào một kỳ.
TRAN_DIEM = 120.0

# Số ngày quản lý được giữ phiếu ở bước 2. Quá hạn thì quyền duyệt tự MỞ
# THÊM cho giám đốc - mở thêm chứ không cướp, quản lý về vẫn bấm được.
NGAY_CHO_QUAN_LY = 3

XEP_LOAI = (
	(100.0, "Xuất sắc", 1.25),
	(85.0, "Tốt", 1.10),
	(70.0, "Đạt", 1.00),
	(0.0, "Chưa đạt", 0.0),
)


def _f(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


# ------------------------------------------------------------- điểm số

def diem_mot_tieu_chi(dat, muc_tieu, nguoc=False):
	"""Điểm một tiêu chí, tính theo phần trăm so với mục tiêu, chặn ở 120.

	`nguoc` là tiêu chí càng thấp càng tốt: tỷ lệ huỷ, hao hụt nguyên liệu.
	Với loại đó, đạt đúng mục tiêu là 100 điểm, thấp hơn mục tiêu thì điểm
	cao hơn, cao hơn mục tiêu thì điểm thấp đi.
	"""
	dat = _f(dat)
	mt = _f(muc_tieu)
	if mt <= 0:
		# Không khai mục tiêu thì không có gì để so. Trả 0 chứ không đoán
		# bừa 100: đoán 100 là cho không một tiêu chí chưa ai đặt chuẩn.
		return 0.0
	if nguoc:
		if dat <= 0:
			return TRAN_DIEM
		d = mt / dat * 100.0
	else:
		d = dat / mt * 100.0
	return round(min(d, TRAN_DIEM), 1)


def diem_tong(dong):
	"""Điểm tổng, cộng theo trọng số.

	Trọng số của các dòng cộng lại phải bằng 100. Nếu người khai lỡ để
	tổng khác 100 thì máy vẫn chia đúng theo tỷ lệ thật, không trả ra một
	con số vô nghĩa. Bảng cấu hình có phép kiểm riêng cho chuyện này.
	"""
	tong_ts = sum(_f(d.get("trong_so")) for d in (dong or []))
	if tong_ts <= 0:
		return 0.0
	tong = sum(_f(d.get("diem")) * _f(d.get("trong_so")) for d in dong)
	return round(tong / tong_ts, 1)


def xep_loai(diem):
	"""Xếp loại và hệ số nhân hoa hồng. Trả về (nhãn, hệ số)."""
	d = _f(diem)
	for nguong, nhan, he_so in XEP_LOAI:
		if d >= nguong:
			return nhan, he_so
	return "Chưa đạt", 0.0


# ------------------------------------------------------------- hoa hồng

def hoa_hong_tho(doanh_thu, bac, san=0):
	"""Hoa hồng THÔ theo bậc thang, chưa nhân hệ số xếp loại, chưa áp trần.

	Hai kiểu bậc:

	  phan_vuot  tiền = tỷ lệ x (phần doanh thu nằm trong bậc này).
	             Các bậc kiểu này CỘNG DỒN với nhau.
	  tu_moc     tiền = tỷ lệ x (doanh thu trừ đi mốc). Bậc kiểu này THAY
	             THẾ toàn bộ các bậc dưới chứ không cộng thêm.

	Kiểu `tu_moc` là để diễn đạt đúng câu anh Việt viết cho mốc 3: "2% trên
	toàn bộ phần doanh thu vượt 400tr". Nó tạo bậc nhảy, và `diem_nhay_bac`
	sẽ chỉ ra chỗ nhảy đó cho người khai thấy.
	"""
	dt = _f(doanh_thu)
	if dt <= _f(san):
		return 0.0

	# Bậc thay thế: lấy bậc CAO NHẤT mà doanh thu đã với tới.
	thay_the = None
	for b in bac or []:
		if (b.get("kieu") or "phan_vuot") != "tu_moc":
			continue
		if dt > _f(b.get("tu")) and (thay_the is None or _f(b.get("tu")) > _f(thay_the.get("tu"))):
			thay_the = b
	if thay_the is not None:
		moc = _f(thay_the.get("moc"))
		return round(max(0.0, dt - moc) * _f(thay_the.get("ty_le")) / 100.0, 0)

	tien = 0.0
	for b in bac or []:
		if (b.get("kieu") or "phan_vuot") == "tu_moc":
			continue
		tu = _f(b.get("tu"))
		den = b.get("den")
		den = _f(den) if den not in (None, "") else None
		if dt <= tu:
			continue
		tren = dt if den is None else min(dt, den)
		tien += max(0.0, tren - tu) * _f(b.get("ty_le")) / 100.0
	return round(tien, 0)


def hoa_hong(doanh_thu, bac, san=0, he_so=1.0, tran=0):
	"""Hoa hồng cuối cùng: thô, nhân hệ số xếp loại, rồi áp trần.

	Thứ tự này quan trọng. Áp trần TRƯỚC rồi mới nhân hệ số thì người xuất
	sắc vẫn vượt trần, tức là trần không còn là trần.
	"""
	tho = hoa_hong_tho(doanh_thu, bac, san)
	tien = round(tho * _f(he_so), 0)
	t = _f(tran)
	if t > 0 and tien > t:
		return t, tien
	return tien, tien


def diem_nhay_bac(bac, san=0, buoc=1000000, den=1500000000):
	"""Dò những chỗ doanh thu nhích một bước mà hoa hồng nhảy vọt.

	Trả về danh sách các mốc nhảy kèm số tiền nhảy. Rỗng nghĩa là bảng bậc
	trơn, không có chỗ nào xui người ta dồn đơn qua tháng.

	Ngưỡng coi là "nhảy": tiền tăng nhiều hơn hai lần mức đáng lẽ tăng của
	bậc cao nhất trong bảng. Chọn cách so tương đối chứ không so một con số
	cứng, để bảng nào cũng dùng được.
	"""
	bac = bac or []
	ty_le_max = max([_f(b.get("ty_le")) for b in bac] or [0])
	nguong = _f(buoc) * ty_le_max / 100.0 * 2 + 1
	ra = []
	x = 0.0
	truoc = hoa_hong_tho(0, bac, san)
	while x < _f(den):
		x += _f(buoc)
		nay = hoa_hong_tho(x, bac, san)
		if nay - truoc > nguong:
			ra.append({
				"tai": x,
				"truoc": truoc,
				"sau": nay,
				"nhay": round(nay - truoc, 0),
			})
		truoc = nay
	return ra


def kiem_bac(bac, san=0):
	"""Soát bảng bậc, trả về danh sách câu cảnh báo. Rỗng là bảng sạch."""
	loi = []
	bac = sorted(bac or [], key=lambda b: _f(b.get("tu")))
	if not bac:
		return ["Chưa khai bậc hoa hồng nào."]
	dau = _f(bac[0].get("tu"))
	if _f(san) > 0 and dau > _f(san):
		loi.append(
			"Sàn đang là %s nhưng bậc đầu tiên mới bắt đầu từ %s. Doanh thu "
			"nằm giữa hai con số này không được đồng hoa hồng nào, nên sàn "
			"thật sự là %s."
			% (_tien(san), _tien(dau), _tien(dau))
		)
	truoc = None
	for b in bac:
		tu, den = _f(b.get("tu")), b.get("den")
		if den not in (None, "") and _f(den) <= tu:
			loi.append("Bậc %s tới %s có mốc trên nhỏ hơn mốc dưới." % (_tien(tu), _tien(den)))
		if truoc is not None and truoc not in (None, "") and _f(truoc) < tu:
			loi.append(
				"Có khoảng trống giữa %s và %s, doanh thu rơi vào đó không "
				"được tính bậc nào." % (_tien(truoc), _tien(tu))
			)
		truoc = b.get("den")
	for d in diem_nhay_bac(bac, san):
		loi.append(
			"Tại mốc %s hoa hồng nhảy vọt %s (từ %s lên %s). Chỗ nhảy như "
			"vậy xui người ta dồn đơn qua tháng cho đủ mốc."
			% (_tien(d["tai"]), _tien(d["nhay"]), _tien(d["truoc"]), _tien(d["sau"]))
		)
	return loi


def _tien(x):
	"""Số tiền viết cho người đọc, dấu chấm ngăn nghìn."""
	return "{:,.0f}".format(_f(x)).replace(",", ".") + " đ"


# --------------------------------------------------- ai duyệt bước quản lý

def duyet_buoc_quan_ly(vai, la_quan_ly_cua_nguoi_do, quan_ly_con_lam, so_ngay_cho):
	"""Ai bấm được bước 2, theo đúng điều 6 anh Việt chốt.

	Trả về (được hay không, câu giải thích khi không được).

	Ba đường được bấm:
	  - đúng người quản lý trực tiếp của người được chấm
	  - giám đốc, luôn luôn, vì giám đốc chấm cấp quản lý
	  - giám đốc, khi quản lý đã nghỉ hoặc giữ phiếu quá hạn

	Đường thứ ba là "mở thêm" chứ không "cướp quyền": quản lý đi làm lại
	vẫn bấm được. Cướp quyền thì kỳ nào quản lý bận vài ngày là mất luôn
	tiếng nói về nhân viên của mình.
	"""
	vai = set(vai or [])
	la_gd = bool(vai & VAI_GIAM_DOC)
	if la_gd:
		return True, ""
	if la_quan_ly_cua_nguoi_do:
		return True, ""
	if not quan_ly_con_lam or _f(so_ngay_cho) > NGAY_CHO_QUAN_LY:
		return False, (
			"Quản lý trực tiếp đang nghỉ hoặc đã giữ phiếu quá %s ngày, "
			"phiếu này chờ giám đốc xử lý." % NGAY_CHO_QUAN_LY
		)
	return False, "Chỉ quản lý trực tiếp của người được chấm mới xác nhận bước này."


def qua_han_quan_ly(so_ngay_cho, quan_ly_con_lam=True):
	"""Phiếu đã tới lúc tự mở quyền lên cho giám đốc chưa."""
	return (not quan_ly_con_lam) or _f(so_ngay_cho) > NGAY_CHO_QUAN_LY


# ------------------------------------------------------------ cấu hình gốc

VAI_GIAM_DOC = {"System Manager", "Giám đốc", "AP Giám đốc"}
VAI_KE_TOAN = {"Accounts Manager", "Accounts User", "Kế toán"}
VAI_QUAN_LY = {"Sales Manager", "Quản lý cửa hàng", "Bếp trưởng"}
VAI_XEM = VAI_GIAM_DOC | VAI_KE_TOAN | VAI_QUAN_LY

# Nguồn số của một tiêu chí:
#   may  máy tự đo, người không sửa được
#   tay  người chấm, máy để trống chờ chấm
MAY, TAY = "may", "tay"

# Bộ tiêu chí theo VAI, không theo từng người. Trọng số mỗi bộ cộng lại 100.
# Các con số dưới đây là bản anh Việt chốt 01/09/2026 ở điều 5.
BO_MAC_DINH = {
	"sales": {
		"ten": "Sales và bán hàng",
		"tieu_chi": [
			{"k": "dt", "ten": "Doanh thu đã ghi sổ trong kỳ", "trong_so": 45, "nguon": MAY, "muc_tieu": 350000000, "don_vi": "đ"},
			# Anh Việt chốt: giảm số đơn xuống 5, đẩy khách quay lại lên 20.
			# Lý do anh nêu: tập trung chất lượng chăm sóc khách chứ không
			# bào số lượng đơn.
			{"k": "so_don", "ten": "Số đơn hoàn thành", "trong_so": 5, "nguon": MAY, "muc_tieu": 120, "don_vi": "đơn"},
			{"k": "bq_don", "ten": "Giá trị đơn bình quân", "trong_so": 10, "nguon": MAY, "muc_tieu": 900000, "don_vi": "đ"},
			{"k": "ty_le_huy", "ten": "Tỷ lệ đơn bị huỷ", "trong_so": 10, "nguon": MAY, "muc_tieu": 3, "nguoc": 1, "don_vi": "%"},
			{"k": "khach_lai", "ten": "Khách thành viên quay lại", "trong_so": 20, "nguon": MAY, "muc_tieu": 25, "don_vi": "khách"},
			{"k": "thai_do", "ten": "Thái độ và phối hợp", "trong_so": 10, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
		],
		"co_hoa_hong": 1,
	},
	"cua_hang": {
		"ten": "Quản lý cửa hàng",
		"tieu_chi": [
			{"k": "dt_diem", "ten": "Doanh thu điểm bán", "trong_so": 35, "nguon": MAY, "muc_tieu": 400000000, "don_vi": "đ"},
			{"k": "kiem_ke", "ten": "Kiểm kê khớp, không lệch tồn", "trong_so": 20, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
			{"k": "nop_quy", "ten": "Nộp quỹ tiền mặt đủ và đúng hạn", "trong_so": 15, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
			{"k": "ty_le_huy", "ten": "Tỷ lệ phiếu huỷ và hoàn tiền", "trong_so": 15, "nguon": MAY, "muc_tieu": 3, "nguoc": 1, "don_vi": "%"},
			{"k": "quan_ly_ca", "ten": "Quản lý ca và nhân sự", "trong_so": 15, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
		],
		"co_hoa_hong": 1,
	},
	"bep": {
		"ten": "Bếp và sản xuất",
		"tieu_chi": [
			# Anh Việt chốt: hao hụt lên 30, hàng lỗi 20. Bánh entremet yêu
			# cầu độ hoàn thiện khắt khe, nguyên liệu cao cấp không được phí.
			# Năm điểm phải bù vào đâu đó, em rút ở sản lượng: sản lượng đạt
			# kế hoạch vốn đã được đo bởi chính hai tiêu chí kia.
			{"k": "san_luong", "ten": "Sản lượng đạt kế hoạch", "trong_so": 25, "nguon": TAY, "muc_tieu": 100, "don_vi": "%"},
			{"k": "hao_hut", "ten": "Hao hụt nguyên liệu trong định mức", "trong_so": 30, "nguon": TAY, "muc_tieu": 3, "nguoc": 1, "don_vi": "%"},
			{"k": "hang_loi", "ten": "Hàng hỏng, lỗi ngoại quan, phải làm lại", "trong_so": 20, "nguon": TAY, "muc_tieu": 2, "nguoc": 1, "don_vi": "%"},
			{"k": "ve_sinh", "ten": "Vệ sinh và an toàn thực phẩm", "trong_so": 15, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
			{"k": "sang_kien", "ten": "Sáng kiến, đào tạo người mới", "trong_so": 10, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
		],
		"co_hoa_hong": 0,
	},
	"ke_toan": {
		"ten": "Kế toán",
		"tieu_chi": [
			{"k": "don_treo", "ten": "Đóng sổ đúng hạn, không đơn treo cuối kỳ", "trong_so": 30, "nguon": MAY, "muc_tieu": 5, "nguoc": 1, "don_vi": "đơn"},
			{"k": "hddt_thieu", "ten": "Hoá đơn điện tử xuất đủ và đúng hạn", "trong_so": 25, "nguon": MAY, "muc_tieu": 5, "nguoc": 1, "don_vi": "đơn"},
			{"k": "doi_soat", "ten": "Đối soát ngân hàng khớp hết trong kỳ", "trong_so": 20, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
			{"k": "tiet_kiem", "ten": "Tiết kiệm chi phí kiểm soát được", "trong_so": 15, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
			{"k": "ho_so", "ten": "Hồ sơ chứng từ đủ, không phiếu thiếu tệp", "trong_so": 10, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
		],
		"co_hoa_hong": 0,
	},
	"marketing": {
		"ten": "Marketing",
		"tieu_chi": [
			{"k": "dt_kenh", "ten": "Doanh thu từ kênh phụ trách", "trong_so": 35, "nguon": MAY, "muc_tieu": 200000000, "don_vi": "đ"},
			{"k": "don_moi", "ten": "Số đơn mới từ kênh đó", "trong_so": 20, "nguon": MAY, "muc_tieu": 150, "don_vi": "đơn"},
			{"k": "chi_phi_don", "ten": "Chi phí quảng cáo trên mỗi đơn", "trong_so": 20, "nguon": TAY, "muc_tieu": 30000, "nguoc": 1, "don_vi": "đ"},
			{"k": "khach_moi", "ten": "Số khách mới lần đầu mua", "trong_so": 15, "nguon": MAY, "muc_tieu": 60, "don_vi": "khách"},
			{"k": "noi_dung", "ten": "Nội dung và hình ảnh đúng hạn", "trong_so": 10, "nguon": TAY, "muc_tieu": 100, "don_vi": "điểm"},
		],
		"co_hoa_hong": 0,
	},
}

# Bậc hoa hồng anh Việt chốt điều 3, và trần điều 4.
CAU_HINH_MAC_DINH = {
	"chu_ky": "thang",
	"san": 150000000,
	"bac": [
		{"tu": 350000000, "den": 450000000, "ty_le": 1.0, "kieu": "phan_vuot"},
		{"tu": 450000000, "den": 600000000, "ty_le": 1.5, "kieu": "phan_vuot"},
		{"tu": 600000000, "den": None, "ty_le": 2.0, "kieu": "tu_moc", "moc": 400000000},
	],
	"tran": 15000000,
	# Điều 4: hợp đồng B2B và voucher đối tác bóc riêng, không tính vào
	# doanh thu lẻ tại quầy để tránh biến động quỹ lương.
	"loai_tru_hop_dong": 1,
	"loai_tru_nguon": ["Voucher đối tác", "B2B", "Hợp đồng"],
	"bo": BO_MAC_DINH,
}


# --------------------------------------------------------- phiếu tự khai
# Anh Việt chốt 02/09/2026: tháng trước máy chưa có số liệu nên các bạn tự
# tính bằng Excel. Cho các bạn tự lập phiếu, đính kèm bảng kê, gửi kế toán
# và giám đốc duyệt. Đây là đường TẠM cho các kỳ máy chưa đo được, không
# thay cho phiếu máy dựng.

TRAN_TU_KHAI = 200000000.0


def kiem_ky_tu_khai(thang, nam, hom_nay_nam, hom_nay_thang):
	"""Tháng năm khai có hợp lệ không. Trả về (mã kỳ, câu từ chối).

	Chặn kỳ TƯƠNG LAI: khai hoa hồng cho tháng chưa hết là khai một con số
	chưa ai đối chiếu được. Chặn kỳ quá cũ hơn hai năm: gõ nhầm năm thì
	phiếu trôi vào một chỗ không ai nhìn.
	"""
	try:
		t = int(thang)
		n = int(nam)
	except Exception:
		return "", "Tháng và năm phải là số."
	if t < 1 or t > 12:
		return "", "Tháng phải từ 1 đến 12."
	if n < hom_nay_nam - 2 or n > hom_nay_nam:
		return "", "Năm phải trong khoảng %s tới %s." % (hom_nay_nam - 2, hom_nay_nam)
	if n > hom_nay_nam or (n == hom_nay_nam and t > hom_nay_thang):
		return "", "Chưa khai được kỳ chưa tới."
	if n == hom_nay_nam and t == hom_nay_thang:
		return "", "Kỳ này chưa hết tháng, chờ sang tháng sau rồi khai."
	return "%04d-%02d" % (n, t), ""


def kiem_tien_tu_khai(tien, tran=TRAN_TU_KHAI):
	"""Số tiền khai có nhận được không. Trả về (số tiền, câu từ chối)."""
	try:
		v = float(str(tien).replace(",", "").strip() or 0)
	except Exception:
		return 0.0, "Số tiền không đọc được."
	if v <= 0:
		return 0.0, "Số tiền phải lớn hơn 0."
	if v > tran:
		return 0.0, (
			"Số tiền vượt %s đ nên phải gửi giám đốc bằng đường khác, "
			"không khai ở đây." % ("{:,.0f}".format(tran).replace(",", "."))
		)
	return v, ""


def gop_cau_hinh(luu):
	"""Cấu hình đang dùng: bản đã lưu đè lên bản gốc, thiếu thì lấy gốc.

	Đè theo TỪNG KHOÁ chứ không thay cả cụm: thêm một tiêu chí mới vào bản
	gốc thì site đã lưu cấu hình cũ vẫn nhận được tiêu chí đó, không phải
	khai lại từ đầu.
	"""
	ra = json.loads(json.dumps(CAU_HINH_MAC_DINH))
	if isinstance(luu, str):
		try:
			luu = json.loads(luu or "{}")
		except Exception:
			luu = {}
	if not isinstance(luu, dict):
		return ra
	for k, v in luu.items():
		if k == "bo" and isinstance(v, dict):
			for vai, bo in v.items():
				if isinstance(bo, dict):
					ra["bo"].setdefault(vai, {})
					ra["bo"][vai].update(bo)
		else:
			ra[k] = v
	return ra


def tong_trong_so(bo):
	return sum(_f(t.get("trong_so")) for t in (bo or {}).get("tieu_chi") or [])


# ------------------------------------------------------- phần cần Frappe

import frappe  # noqa: E402
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate  # noqa: E402

from vagabond.lib import cfg, cfg_o  # noqa: E402
# `cfg_o` PHAI nam trong cau import that, khong duoc de trong phan chu thich.
# Truoc 04/09/2026 ten cfg_o bi day sang sau dau thang cua noqa, nhin luot
# tuong da nhap ca hai. Python khong bao gi luc nap mo dun, chi khi co nguoi
# mo man KPI thi `cau_hinh()` goi `cfg_o` va ca man tra ve loi 500.
from vagabond import tep_dinh_kem  # noqa: E402

DT = "Vagabond KPI Phieu"


def _vai():
	return set(frappe.get_roles())


def _la_gd():
	return bool(_vai() & VAI_GIAM_DOC)


def _kiem_quyen():
	if not (_vai() & VAI_XEM):
		frappe.throw(
			"Phân hệ KPI chỉ mở cho quản lý, kế toán và ban giám đốc."
		)


def cau_hinh():
	"""Cấu hình đang dùng trên site này."""
	return gop_cau_hinh((cfg_o(TRUONG_CAU_HINH) or "").strip())


def khoang_ky(ky=None):
	"""Đổi mã kỳ dạng 2026-08 thành cặp ngày. Không truyền thì lấy kỳ TRƯỚC.

	Mặc định là kỳ trước chứ không phải kỳ này: KPI chốt sau khi kỳ đã
	đóng. Mở màn giữa tháng mà máy dựng phiếu cho tháng đang chạy thì con
	số nào cũng dở dang và ai nhìn cũng tưởng mình đang tụt.
	"""
	if not ky:
		d = getdate(nowdate())
		dau_thang_nay = d.replace(day=1)
		truoc = add_days(dau_thang_nay, -1)
		ky = "%04d-%02d" % (truoc.year, truoc.month)
	nam, thang = str(ky).split("-")[:2]
	tu = getdate("%s-%s-01" % (nam, thang))
	den = add_days(add_thang(tu, 1), -1)
	return ky, tu, den


def add_thang(d, n):
	from frappe.utils import add_months

	return add_months(d, n)


def ky_truoc(ky):
	_, tu, _d = khoang_ky(ky)
	t = add_thang(tu, -1)
	return "%04d-%02d" % (t.year, t.month)


# ----------------------------------------------------------- đọc số liệu

def _hoa_don_ky(tu, den, cf):
	"""Hoá đơn tính vào KPI trong kỳ, đã loại những gì phải loại.

	Loại ra: đơn tạm tính (giấy giữ món, chưa phải tiền), đơn huỷ mềm, và
	theo điều 4 anh Việt chốt là hợp đồng B2B cùng các nguồn voucher đối
	tác - những khoản đó do ban giám đốc trực tiếp xử lý, không tính vào
	doanh thu lẻ tại quầy để tránh biến động quỹ lương.
	"""
	ds = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"posting_date": ["between", [str(tu), str(den)]],
		},
		fields=[
			"name", "owner", "grand_total", "vgb_quay", "custom_nguon",
			"custom_hop_dong", "custom_ma_khach", "customer",
			"vgb_tam_tinh", "vgb_huy", "vgb_pt_thanh_toan",
			# Ô người bán, thêm 02/09/2026. Đọc ô này TRƯỚC người lập:
			# người lập chỉ là người bấm nút, còn ô kia là người bán thật.
			"vgb_nguoi_ban",
		],
		limit_page_length=0,
	)
	tru_nguon = {str(x).strip().lower() for x in (cf.get("loai_tru_nguon") or [])}
	ra = []
	for r in ds:
		if r.get("vgb_tam_tinh") or r.get("vgb_huy"):
			continue
		if cint(cf.get("loai_tru_hop_dong")) and (r.get("custom_hop_dong") or "").strip():
			continue
		if (r.get("custom_nguon") or "").strip().lower() in tru_nguon:
			continue
		ra.append(r)
	return ra


def _don_huy_ky(tu, den):
	"""Số đơn bị huỷ trong kỳ, cả huỷ nghiệp vụ lẫn huỷ mềm bản nháp."""
	a = frappe.db.count("Sales Invoice", {
		"docstatus": 2, "posting_date": ["between", [str(tu), str(den)]],
	})
	b = frappe.db.count("Sales Invoice", {
		"docstatus": 0, "vgb_huy": 1,
		"posting_date": ["between", [str(tu), str(den)]],
	})
	return a + b


def so_lieu_tu_dong(ky=None):
	"""Số máy tự đo được cho một kỳ, gom theo NGƯỜI TẠO hoá đơn.

	MỘT ĐIỀU PHẢI NÓI THẲNG: hệ chưa có trường "người bán" trên hoá đơn.
	Tháng 8/2026 có 1.071 trên 1.907 hoá đơn mang người tạo là Administrator,
	tức là do máy dựng từ Pancake hoặc từ nhịp ghi sổ tự động. Gán doanh thu
	theo người tạo thì hơn một nửa doanh thu rơi vào một cái tên không phải
	người.

	Nên phần đó KHÔNG bị chia bừa. Nó nằm trong một rổ riêng gọi là "chưa
	gán người bán", hiện rõ số tiền trên màn, và quản lý gán tay từng đơn
	cho từng người. Gán tay ghi vào PHIẾU KPI, không sửa hoá đơn - đúng
	nguyên tắc không sửa dữ liệu quá khứ anh Việt chốt 13/08/2026.
	"""
	cf = cau_hinh()
	ky, tu, den = khoang_ky(ky)
	hd = _hoa_don_ky(tu, den, cf)

	may = set()
	for r in frappe.get_all(
		"User", filters={"enabled": 1}, fields=["name"], limit_page_length=0
	):
		may.add(r["name"])

	theo_nguoi, theo_diem, chua_gan = {}, {}, []
	khach_theo_nguoi = {}
	for r in hd:
		# Ô người bán đứng TRƯỚC người lập. Đơn nào chưa có ô đó thì rơi
		# về người lập như cũ, nên đơn cũ không đổi cách tính.
		ng = (r.get("vgb_nguoi_ban") or "").strip() or (r.get("owner") or "")
		tien = flt(r.get("grand_total"))
		d = (r.get("vgb_quay") or "").strip().upper() or "SALES"
		theo_diem[d] = theo_diem.get(d, 0.0) + tien
		# Administrator là tài khoản MÁY, không phải người bán.
		if ng == "Administrator" or ng not in may:
			chua_gan.append({
				"ma": r["name"], "tien": tien, "diem": d,
				"nguon": (r.get("custom_nguon") or "").strip(),
				"khach": r.get("customer") or "",
			})
			continue
		o = theo_nguoi.setdefault(ng, {"dt": 0.0, "so_don": 0})
		o["dt"] += tien
		o["so_don"] += 1
		k = (r.get("custom_ma_khach") or r.get("customer") or "").strip()
		if k:
			khach_theo_nguoi.setdefault(ng, {}).setdefault(k, 0)
			khach_theo_nguoi[ng][k] += 1

	for ng, o in theo_nguoi.items():
		o["bq_don"] = o["dt"] / o["so_don"] if o["so_don"] else 0.0
		o["khach_lai"] = sum(1 for _k, n in (khach_theo_nguoi.get(ng) or {}).items() if n >= 2)

	tong_don = len(hd)
	huy = _don_huy_ky(tu, den)
	chung = {
		"ty_le_huy": round(huy / (tong_don + huy) * 100.0, 2) if (tong_don + huy) else 0.0,
		"don_treo": frappe.db.count("Sales Invoice", {
			"docstatus": 0, "vgb_huy": 0, "vgb_tam_tinh": 0,
			"posting_date": ["between", [str(tu), str(den)]],
		}),
		"hddt_thieu": frappe.db.count("Sales Invoice", {
			"docstatus": 1, "custom_hddt_so": ["in", ["", None]],
			"posting_date": ["between", [str(tu), str(den)]],
		}),
	}
	return {
		"ky": ky, "tu": str(tu), "den": str(den),
		"theo_nguoi": theo_nguoi,
		"theo_diem": theo_diem,
		"chung": chung,
		"chua_gan": sorted(chua_gan, key=lambda x: -x["tien"]),
		"tien_chua_gan": round(sum(x["tien"] for x in chua_gan), 0),
		"so_don_chua_gan": len(chua_gan),
	}


# ------------------------------------------------------------ dựng phiếu

def _ten_nguoi(u):
	"""Mot phep doi duy nhat cho ca he, xem `vagabond/ten_nguoi.py`."""
	from vagabond import ten_nguoi as _tn

	return _tn.ten(u)


def _don_da_gan(ky, tru_phieu=None):
	"""Đơn nào đã được gán tay cho ai trong kỳ này. Chặn gán trùng.

	Một đơn gán cho hai người là cộng đôi doanh thu, và không ai nhìn ra
	cho tới lúc đối chiếu tổng.
	"""
	ra = {}
	for r in frappe.get_all(
		DT, filters={"ky": ky}, fields=["name", "nguoi", "don_gan_tay"],
		limit_page_length=0, ignore_permissions=True,
	):
		if tru_phieu and r["name"] == tru_phieu:
			continue
		for ma in _doc_ds(r.get("don_gan_tay")):
			ra[ma] = r["nguoi"]
	return ra


def _doc_ds(gt):
	if not gt:
		return []
	if isinstance(gt, (list, tuple)):
		return list(gt)
	try:
		v = json.loads(gt)
	except Exception:
		return []
	return v if isinstance(v, list) else []


def _do_tieu_chi(k, nguoi, sl):
	"""Con số máy đo được cho một tiêu chí. None nghĩa là máy không đo."""
	ng = (sl.get("theo_nguoi") or {}).get(nguoi) or {}
	chung = sl.get("chung") or {}
	if k in ("dt", "dt_kenh"):
		return ng.get("dt", 0.0)
	if k in ("so_don", "don_moi"):
		return ng.get("so_don", 0)
	if k == "bq_don":
		return ng.get("bq_don", 0.0)
	if k in ("khach_lai", "khach_moi"):
		return ng.get("khach_lai", 0)
	if k in ("ty_le_huy", "don_treo", "hddt_thieu"):
		return chung.get(k, 0)
	return None


@frappe.whitelist()
def dung_phieu(ky=None, nguoi=None, bo="sales"):
	"""Dựng một phiếu KPI cho một người trong một kỳ.

	Dựng lại phiếu đã có thì chỉ CẬP NHẬT lại phần máy đo, giữ nguyên phần
	người đã chấm. Phiếu đã đóng băng thì không đụng tới.
	"""
	_kiem_quyen()
	cf = cau_hinh()
	ky, tu, den = khoang_ky(ky)
	nguoi = (nguoi or "").strip()
	if not nguoi:
		frappe.throw("Chưa chọn người để dựng phiếu.")
	bo = (bo or "sales").strip()
	if bo not in (cf.get("bo") or {}):
		frappe.throw("Không có bộ tiêu chí %s." % bo)

	ten = frappe.db.get_value(DT, {"ky": ky, "nguoi": nguoi}, "name")
	doc = frappe.get_doc(DT, ten) if ten else frappe.new_doc(DT)
	if ten and cint(doc.dong_bang):
		frappe.throw("Phiếu kỳ %s của %s đã chốt, không dựng lại được." % (ky, _ten_nguoi(nguoi)))

	doc.ky = ky
	doc.tu_ngay = tu
	doc.den_ngay = den
	doc.nguoi = nguoi
	doc.ten_nguoi = _ten_nguoi(nguoi)
	doc.bo = bo
	# Trạng thái lạ thì kéo về bước đầu. Bản v381 lỡ ghi danh sách trạng thái
	# trong kho KHÔNG dấu, nên phiếu dựng ngày 01/09 bị đóng dấu sai và kẹt
	# ở "bước 0/5", không ai bấm được. Dòng này gỡ luôn cho phiếu cũ khi dựng
	# lại, khỏi phải đụng tay vào cơ sở dữ liệu.
	if doc.trang_thai not in CHUOI and doc.trang_thai != TT_HUY:
		doc.trang_thai = TT_QUAN_LY

	cu = {d.k: d for d in (doc.get("cac_dong") or [])}
	sl = so_lieu_tu_dong(ky)
	doc.set("cac_dong", [])
	for t in (cf["bo"][bo].get("tieu_chi") or []):
		dat = _do_tieu_chi(t["k"], nguoi, sl) if t.get("nguon") == MAY else None
		if dat is None:
			# Người chấm: giữ nguyên con số đã chấm nếu có.
			dat = flt((cu.get(t["k"]) or {}).get("dat")) if t["k"] in cu else None
		doc.append("cac_dong", {
			"k": t["k"], "ten": t["ten"], "trong_so": t.get("trong_so"),
			"nguon": t.get("nguon"), "muc_tieu": t.get("muc_tieu"),
			"don_vi": t.get("don_vi"), "nguoc": cint(t.get("nguoc")),
			"dat": dat,
			"ghi_chu": (cu.get(t["k"]) or {}).get("ghi_chu") if t["k"] in cu else None,
		})
	doc.so_lieu = json.dumps({
		"chua_gan_tien": sl.get("tien_chua_gan"),
		"chua_gan_so_don": sl.get("so_don_chua_gan"),
	}, ensure_ascii=False)
	tinh_lai(doc, cf, sl)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma": doc.name}


def tinh_lai(doc, cf=None, sl=None):
	"""Tính lại điểm, xếp loại và hoa hồng của một phiếu. KHÔNG lưu."""
	cf = cf or cau_hinh()
	bo = (cf.get("bo") or {}).get(doc.bo) or {}

	# Doanh thu = phần máy gán theo người tạo, cộng phần quản lý gán tay.
	gan = _doc_ds(doc.get("don_gan_tay"))
	tien_gan = 0.0
	if gan:
		for r in frappe.get_all(
			"Sales Invoice", filters={"name": ["in", gan]},
			fields=["name", "grand_total"], limit_page_length=0,
		):
			tien_gan += flt(r["grand_total"])
	doc.doanh_thu_gan_tay = tien_gan

	dong = []
	for d in doc.get("cac_dong") or []:
		dat = flt(d.dat)
		if d.k in ("dt", "dt_diem", "dt_kenh"):
			dat += tien_gan
			d.dat = dat
		d.diem = diem_mot_tieu_chi(dat, d.muc_tieu, cint(d.nguoc))
		dong.append({"diem": d.diem, "trong_so": d.trong_so})
		if d.k in ("dt", "dt_diem", "dt_kenh"):
			doc.doanh_thu = dat

	doc.diem_tong = diem_tong(dong)
	nhan, he_so = xep_loai(doc.diem_tong)
	doc.xep_loai = nhan
	doc.he_so = he_so

	if cint(bo.get("co_hoa_hong")):
		tien, tho = hoa_hong(
			doc.doanh_thu, cf.get("bac"), cf.get("san"), he_so, cf.get("tran")
		)
		doc.hoa_hong_tho = tho
		doc.hoa_hong = tien
		doc.bi_tran = 1 if tho > tien else 0
	else:
		doc.hoa_hong_tho = 0
		doc.hoa_hong = 0
		doc.bi_tran = 0
	# Chưa chấm đủ phần định tính thì nói ra, đừng để điểm tổng trông như
	# đã xong trong khi còn ba tiêu chí bỏ trống.
	doc.con_thieu = len([
		d for d in (doc.get("cac_dong") or [])
		if d.nguon == TAY and (d.dat is None or d.dat == "")
	])
	return doc


# ---------------------------------------------------------- chuỗi duyệt

def _quan_ly_cua(nguoi):
	"""Ai là quản lý trực tiếp của người này.

	Chưa cài phân hệ HR nên chưa có cây tổ chức. Tạm đọc từ trường
	`custom_quan_ly` trên User nếu site có khai; không có thì trả rỗng và
	luật rơi về đường giám đốc, đúng điều 6 anh Việt chốt.
	"""
	try:
		return (frappe.db.get_value("User", nguoi, "custom_quan_ly") or "").strip()
	except Exception:
		return ""


def _con_lam_viec(u):
	if not u:
		return False
	return bool(frappe.db.get_value("User", u, "enabled"))


def _so_ngay_cho(doc):
	moc = doc.get("vao_buoc_luc") or doc.get("modified")
	if not moc:
		return 0
	from frappe.utils import date_diff

	return date_diff(nowdate(), str(moc)[:10])


def duoc_bam(doc):
	"""Người đang đăng nhập bấm được bước hiện tại của phiếu này không.

	Trả về (được, câu giải thích). Tính ở MÁY CHỦ chứ không để màn hình tự
	suy theo vai: luật thật còn có "không ai tự duyệt phiếu của chính
	mình", mà màn hình thì không biết phiếu của ai.
	"""
	vai = _vai()
	toi = frappe.session.user
	tt = doc.trang_thai

	if doc.nguoi == toi and not _la_gd():
		return False, "Không ai tự duyệt phiếu KPI của chính mình."

	if tt == TT_QUAN_LY:
		ql = _quan_ly_cua(doc.nguoi)
		return duyet_buoc_quan_ly(
			vai, bool(ql) and ql == toi, _con_lam_viec(ql), _so_ngay_cho(doc)
		)
	if tt == TT_KE_TOAN:
		if vai & (VAI_KE_TOAN | VAI_GIAM_DOC):
			return True, ""
		return False, "Bước này chờ kế toán soát số tiền và nguồn chi."
	if tt == TT_GIAM_DOC:
		if _la_gd():
			return True, ""
		return False, "Bước cuối chỉ giám đốc bấm được."
	if tt == TT_DUYET:
		if vai & (VAI_KE_TOAN | VAI_GIAM_DOC):
			return True, ""
		return False, "Đẩy sang đề nghị chi là việc của kế toán hoặc giám đốc."
	return False, "Phiếu đã đi hết chuỗi."


@frappe.whitelist()
def cham(ma=None, du_lieu=None):
	"""Quản lý chấm phần định tính và ghi nhận xét. Chỉ ở bước quản lý."""
	_kiem_quyen()
	doc = frappe.get_doc(DT, ma)
	if cint(doc.dong_bang):
		frappe.throw("Phiếu đã chốt, không chấm lại được.")
	if doc.trang_thai != TT_QUAN_LY:
		frappe.throw(
			"Phiếu đang ở bước %s nên không chấm lại được. Trả phiếu về bước "
			"quản lý trước đã." % (NHAN_TT.get(doc.trang_thai) or doc.trang_thai)
		)
	duoc, vi_sao = duoc_bam(doc)
	if not duoc:
		frappe.throw(vi_sao)

	d = frappe.parse_json(du_lieu) if isinstance(du_lieu, str) else (du_lieu or {})
	diem_tay = d.get("diem") or {}
	for dong in doc.get("cac_dong") or []:
		# Máy đo được thì người KHÔNG sửa. Cho sửa là mở đường cho một con
		# số đẹp hơn số thật, mà không ai đối chiếu lại.
		if dong.nguon != TAY:
			continue
		if dong.k in diem_tay:
			dong.dat = flt(diem_tay[dong.k])
		gc = (d.get("ghi_chu") or {}).get(dong.k)
		if gc is not None:
			dong.ghi_chu = str(gc)[:300]
	if d.get("nhan_xet") is not None:
		doc.ghi_chu_quan_ly = str(d.get("nhan_xet"))[:1000]
	if d.get("don_gan_tay") is not None:
		_gan_don(doc, d.get("don_gan_tay"))
	tinh_lai(doc)
	doc.nguoi_cham = frappe.session.user
	doc.luc_cham = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return chi_tiet(doc.name)


def _gan_don(doc, ds):
	"""Gán tay một số hoá đơn của rổ chưa gán cho người này."""
	ds = [str(x).strip() for x in _doc_ds(ds) if str(x or "").strip()]
	da = _don_da_gan(doc.ky, tru_phieu=doc.name)
	trung = [m for m in ds if m in da and da[m] != doc.nguoi]
	if trung:
		frappe.throw(
			"Đơn %s đã gán cho %s trong kỳ này rồi. Một đơn chỉ được tính "
			"cho một người." % (", ".join(trung[:5]), _ten_nguoi(da[trung[0]]))
		)
	doc.don_gan_tay = json.dumps(ds, ensure_ascii=False) if ds else None


@frappe.whitelist()
def duyet(ma=None, ghi_chu=None):
	"""Bấm duyệt một bước. Máy tự biết đang ở bước nào."""
	_kiem_quyen()
	doc = frappe.get_doc(DT, ma)
	duoc, vi_sao = duoc_bam(doc)
	if not duoc:
		frappe.throw(vi_sao)
	if doc.trang_thai == TT_QUAN_LY:
		tinh_lai(doc)
		if cint(doc.con_thieu):
			frappe.throw(
				"Còn %s tiêu chí định tính chưa chấm. Chấm đủ rồi mới chuyển "
				"sang kế toán được." % doc.con_thieu
			)
		doc.trang_thai = TT_KE_TOAN
		doc.nguoi_cham = doc.nguoi_cham or frappe.session.user
		doc.luc_cham = doc.luc_cham or now_datetime()
	elif doc.trang_thai == TT_KE_TOAN:
		doc.trang_thai = TT_GIAM_DOC
		doc.nguoi_ke_toan = frappe.session.user
		doc.luc_ke_toan = now_datetime()
	elif doc.trang_thai == TT_GIAM_DOC:
		# Giám đốc bấm là CHỐT. Từ đây số liệu đóng băng: dữ liệu gốc có
		# đổi thì phiếu này không đổi theo nữa.
		tinh_lai(doc)
		doc.trang_thai = TT_DUYET
		doc.nguoi_giam_doc = frappe.session.user
		doc.luc_giam_doc = now_datetime()
		doc.dong_bang = 1
	else:
		frappe.throw("Phiếu đã đi hết chuỗi duyệt.")
	if ghi_chu:
		doc.ghi_chu_duyet = str(ghi_chu)[:1000]
	doc.vao_buoc_luc = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return chi_tiet(doc.name)


@frappe.whitelist()
def tra_lai(ma=None, ly_do=None):
	"""Trả phiếu về BƯỚC TRƯỚC kèm lý do, không trả về đầu chuỗi.

	Trả về đầu thì người ta phải làm lại từ số một, mà lỗi thường chỉ nằm ở
	một tiêu chí. Phiếu đã đóng băng thì không trả lại được: mở lại một
	phiếu đã chốt là mở đường sửa số đã trả tiền.
	"""
	_kiem_quyen()
	ly_do = (ly_do or "").strip()
	if not ly_do:
		frappe.throw("Phải ghi lý do trả lại để người nhận biết sửa chỗ nào.")
	doc = frappe.get_doc(DT, ma)
	if cint(doc.dong_bang):
		frappe.throw("Phiếu đã chốt và đóng băng, không trả lại được.")
	duoc, vi_sao = duoc_bam(doc)
	if not duoc:
		frappe.throw(vi_sao)
	if doc.trang_thai not in CHUOI or doc.trang_thai == TT_QUAN_LY:
		frappe.throw("Phiếu đang ở bước đầu, không có bước trước để trả về.")
	doc.trang_thai = CHUOI[CHUOI.index(doc.trang_thai) - 1]
	doc.tra_lai_boi = frappe.session.user
	doc.tra_lai_ly_do = ly_do[:1000]
	doc.vao_buoc_luc = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return chi_tiet(doc.name)


@frappe.whitelist()
def y_kien(ma=None, noi_dung=None):
	"""Người được chấm nói lại. Bảy ngày kể từ khi phiếu vào bước quản lý.

	Không có cửa này thì mỗi kỳ là một lần đến bàn giám đốc cãi, và cái
	đến bàn thì không lưu lại được ở đâu.
	"""
	doc = frappe.get_doc(DT, ma)
	if doc.nguoi != frappe.session.user:
		frappe.throw("Chỉ người được chấm mới ghi ý kiến vào phiếu của mình.")
	if cint(doc.dong_bang):
		frappe.throw("Phiếu đã chốt. Anh chị trao đổi trực tiếp với quản lý nhé.")
	doc.y_kien_nhan_vien = (str(noi_dung or "").strip())[:1000]
	doc.y_kien_luc = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


# --------------------------------------------------- đẩy sang đề nghị chi

@frappe.whitelist()
def day_chi(ma=None):
	"""Đẩy hoa hồng đã duyệt sang một Đề nghị chi riêng.

	Điều 7 anh Việt chốt: tiền hoa hồng chuyển khoản TÁCH khỏi lương cứng,
	để nhân sự cảm nhận rõ giá trị khoản thưởng hiệu suất và kế toán dễ
	hạch toán chi phí.

	Đi qua đúng cổng `de_nghi_chi.tao` chứ không tự dựng phiếu chi ở đây:
	cổng đó giữ luật hạch toán, luật duyệt theo mức tiền và luật chứng từ.
	Viết lại luật ở đây là mở đường cho hai bộ luật lệch nhau.
	"""
	_kiem_quyen()
	doc = frappe.get_doc(DT, ma)
	if doc.trang_thai != TT_DUYET:
		frappe.throw("Chỉ phiếu đã giám đốc duyệt mới đẩy sang đề nghị chi được.")
	if (doc.get("phieu_chi") or "").strip():
		frappe.throw("Phiếu này đã đẩy sang %s rồi." % doc.phieu_chi)
	if flt(doc.hoa_hong) <= 0:
		frappe.throw("Phiếu này không có hoa hồng nên không có gì để chi.")
	duoc, vi_sao = duoc_bam(doc)
	if not duoc:
		frappe.throw(vi_sao)

	from vagabond import de_nghi_chi

	r = de_nghi_chi.tao(du_lieu={
		"loai_nghiep_vu": "Chi phí",
		"dien_giai": "Hoa hồng hiệu suất kỳ %s cho %s" % (doc.ky, doc.ten_nguoi),
		"hinh_thuc": "Hoàn tiền cho nhân viên",
		"phuong_thuc": "Chuyển khoản",
		"ngay_can_tt": str(add_days(nowdate(), 7)),
		"cac_khoan": [{
			"noi_dung": "Hoa hồng kỳ %s - %s (điểm %s, %s)"
			% (doc.ky, doc.ten_nguoi, doc.diem_tong, doc.xep_loai),
			"so_tien": flt(doc.hoa_hong),
			"phan_loai": "Chi phí nhân công",
			"loai_chung_tu": "Bảng kê không hoá đơn",
		}],
	}, gui_luon=0)

	doc.phieu_chi = r.get("ma")
	doc.trang_thai = TT_DA_CHI
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "phieu_chi": doc.phieu_chi, "nhac":
		"Đã lập đề nghị chi %s ở trạng thái nháp. Kế toán mở phiếu đó, đính "
		"bảng kê rồi gửi duyệt như phiếu chi bình thường." % doc.phieu_chi}


# --------------------------------------------------------------- màn hình

@frappe.whitelist()
def danh_sach(ky=None, bo=None, trang_thai=None):
	"""Danh sách phiếu của một kỳ, kèm số tổng để nhìn phát là biết."""
	_kiem_quyen()
	ky, tu, den = khoang_ky(ky)
	loc = {"ky": ky}
	if bo:
		loc["bo"] = bo
	if trang_thai:
		loc["trang_thai"] = trang_thai
	ds = frappe.get_all(
		DT, filters=loc,
		fields=[
			"name", "nguoi", "ten_nguoi", "bo", "trang_thai", "diem_tong",
			"xep_loai", "doanh_thu", "hoa_hong", "bi_tran", "con_thieu",
			"phieu_chi", "dong_bang",
		],
		order_by="hoa_hong desc, diem_tong desc",
		limit_page_length=0, ignore_permissions=True,
	)
	cf = cau_hinh()
	sl = so_lieu_tu_dong(ky)
	return {
		"ky": ky, "tu": str(tu), "den": str(den),
		"ky_truoc": ky_truoc(ky),
		"ds": ds,
		"tong_hoa_hong": round(sum(flt(r["hoa_hong"]) for r in ds), 0),
		"so_phieu": len(ds),
		"bo": [{"k": k, "ten": v.get("ten"), "co_hoa_hong": cint(v.get("co_hoa_hong"))}
		       for k, v in (cf.get("bo") or {}).items()],
		"trang_thai": CHUOI + [TT_HUY],
		"nhan_trang_thai": NHAN_TT,
		"chua_gan": {
			"so_don": sl.get("so_don_chua_gan"),
			"tien": sl.get("tien_chua_gan"),
		},
		"la_giam_doc": 1 if _la_gd() else 0,
		"canh_bao_bac": kiem_bac(cf.get("bac"), cf.get("san")),
	}


@frappe.whitelist()
def chi_tiet(ma=None):
	"""Một phiếu đầy đủ, kèm quyền bấm bước hiện tại tính ở máy chủ."""
	doc = frappe.get_doc(DT, ma)
	if doc.nguoi != frappe.session.user:
		_kiem_quyen()
	ra = doc.as_dict()
	for k in list(ra.keys()):
		if k.startswith("_"):
			ra.pop(k, None)
	duoc, vi_sao = duoc_bam(doc)
	ra["duoc_bam"] = 1 if duoc else 0
	ra["vi_sao_khong_bam"] = "" if duoc else vi_sao
	ra["nhan_trang_thai"] = NHAN_TT.get(doc.trang_thai) or doc.trang_thai
	ra["la_cua_toi"] = 1 if doc.nguoi == frappe.session.user else 0
	ra["buoc"] = (CHUOI.index(doc.trang_thai) + 1) if doc.trang_thai in CHUOI else 0
	ra["tong_buoc"] = len(CHUOI)
	# Kỳ trước để so, đúng thứ người xem cần nhất khi nhìn một con số điểm.
	kt = frappe.db.get_value(
		DT, {"ky": ky_truoc(doc.ky), "nguoi": doc.nguoi},
		["diem_tong", "xep_loai", "hoa_hong"], as_dict=True,
	)
	ra["ky_truoc"] = kt or None
	# Bang ke dinh kem cua phieu tu khai, doi thanh duong dan xem duoc.
	ra["tep_hien"] = tep_dinh_kem.hien(doc.get("tep_dinh_kem"))
	if doc.trang_thai == TT_QUAN_LY and not cint(doc.dong_bang):
		sl = so_lieu_tu_dong(doc.ky)
		da = _don_da_gan(doc.ky, tru_phieu=doc.name)
		ra["chua_gan"] = [x for x in (sl.get("chua_gan") or []) if x["ma"] not in da][:200]
		ra["da_gan"] = _doc_ds(doc.get("don_gan_tay"))
	return ra


@frappe.whitelist()
def cua_toi(ky=None):
	"""Nhân viên xem điểm của chính mình. Không cần vai gì cả.

	Đây là thứ làm KPI có tác dụng. Cuối kỳ mới cho biết thì nó chỉ là
	bảng chấm điểm, không phải công cụ điều hành.
	"""
	ky, tu, den = khoang_ky(ky)
	ten = frappe.db.get_value(DT, {"ky": ky, "nguoi": frappe.session.user}, "name")
	if not ten:
		return {"ky": ky, "co": 0}
	d = chi_tiet(ten)
	d["co"] = 1
	return d


@frappe.whitelist()
def tu_khai(thang=None, nam=None, tien=None, ly_do=None, tep=None):
	"""Nhân viên tự lập phiếu duyệt KPI và hoa hồng cho một kỳ đã qua.

	Anh Việt chốt 02/09/2026: *"tháng trước máy không có số liệu để tính,
	các bạn đã tự tính excel"*. Đây là đường TẠM cho những kỳ đó: người
	nhận tiền tự khai, đính kèm bảng kê, rồi kế toán soát và giám đốc
	duyệt. Không thay cho phiếu máy dựng, và cố ý bỏ qua bước quản lý:
	quản lý không có số liệu để xác nhận thì bắt họ bấm cũng chỉ là bấm.

	Ba hàng rào, vì đây là người tự khai tiền của chính mình:
	  1. Chỉ khai được cho CHÍNH MÌNH, không khai hộ ai.
	  2. Kỳ phải là kỳ đã hết tháng, và không quá hai năm trước.
	  3. Kỳ nào máy đã dựng phiếu thì KHÔNG khai đè: đã có số máy đo thì
	     con số tự khai không có chỗ đứng.
	Bảng kê đính kèm là BẮT BUỘC. Một con số tự khai không kèm bảng kê thì
	kế toán không có gì để soát.
	"""
	toi = frappe.session.user
	hn = getdate(nowdate())
	ky, loi = kiem_ky_tu_khai(thang, nam, hn.year, hn.month)
	if loi:
		frappe.throw(loi)
	so_tien, loi = kiem_tien_tu_khai(tien)
	if loi:
		frappe.throw(loi)

	ds_tep = tep_dinh_kem.doc_ds(tep)
	if not ds_tep:
		frappe.throw(
			"Phải đính kèm bảng kê chi tiết. Con số tự khai không có bảng kê "
			"thì kế toán không soát được."
		)

	cu = frappe.db.get_value(
		DT, {"ky": ky, "nguoi": toi}, ["name", "tu_khai", "trang_thai", "dong_bang"],
		as_dict=True,
	)
	if cu and not cint(cu.get("tu_khai")):
		frappe.throw(
			"Kỳ %s đã có phiếu do máy dựng nên không khai tay đè lên được. "
			"Mở phiếu đó ra xem, thấy sai thì ghi ý kiến vào phiếu." % ky
		)
	if cu and cint(cu.get("dong_bang")):
		frappe.throw("Phiếu tự khai kỳ %s đã chốt, không sửa lại được." % ky)
	if cu and cu.get("trang_thai") == TT_DA_CHI:
		frappe.throw("Phiếu tự khai kỳ %s đã đẩy chi rồi." % ky)

	tu, den = _hai_dau_ky(ky)
	doc = frappe.get_doc(DT, cu["name"]) if cu else frappe.new_doc(DT)
	doc.ky = ky
	doc.tu_ngay = tu
	doc.den_ngay = den
	doc.nguoi = toi
	doc.ten_nguoi = _ten_nguoi(toi)
	doc.bo = "tu_khai"
	doc.tu_khai = 1
	doc.hoa_hong = so_tien
	doc.hoa_hong_tho = so_tien
	doc.doanh_thu = 0
	doc.diem_tong = 0
	doc.xep_loai = "Tự khai"
	doc.he_so = 1
	doc.con_thieu = 0
	doc.ly_do_tu_khai = (ly_do or "").strip()[:2000]
	doc.tep_dinh_kem = tep_dinh_kem.ghi_ds(ds_tep)
	doc.set("cac_dong", [])
	# Vao thang buoc ke toan. Nguoi khai la nguoi nhan tien, nen `duoc_bam`
	# van chan ho tu duyet phieu cua chinh minh.
	doc.trang_thai = TT_KE_TOAN
	doc.vao_buoc_luc = now_datetime()
	doc.dong_bang = 0
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	# Buoc tep khoi trang thai treo sang phieu, de nhip don rac dem khong
	# xoa mat bang ke. Xem `vagabond/tep_dinh_kem.py`.
	tep_dinh_kem.gan_vao(DT, doc.name, "tep_dinh_kem", ds_tep)
	frappe.db.commit()
	return {"ma": doc.name, "ky": ky, "tien": so_tien}


def _hai_dau_ky(ky):
	"""Ngày đầu và ngày cuối của một mã kỳ dạng 2026-08."""
	n, t = int(ky[:4]), int(ky[5:7])
	dau = getdate("%04d-%02d-01" % (n, t))
	if t == 12:
		sau = getdate("%04d-01-01" % (n + 1))
	else:
		sau = getdate("%04d-%02d-01" % (n, t + 1))
	return dau, add_days(sau, -1)


@frappe.whitelist()
def cai_dat():
	"""Bảng cấu hình: bộ tiêu chí, bậc hoa hồng, trần, và phép soát bậc."""
	_kiem_quyen()
	cf = cau_hinh()
	return {
		"cf": cf,
		"sua_duoc": 1 if _la_gd() else 0,
		"canh_bao": kiem_bac(cf.get("bac"), cf.get("san")),
		"tong_trong_so": {k: tong_trong_so(v) for k, v in (cf.get("bo") or {}).items()},
		"thu_tinh": [
			{"dt": x, "tien": hoa_hong_tho(x, cf.get("bac"), cf.get("san"))}
			for x in (
				100000000, 200000000, 300000000, 350000000, 400000000,
				450000000, 500000000, 550000000, 599000000, 600000000,
				601000000, 700000000, 800000000, 1000000000,
			)
		],
	}


@frappe.whitelist()
def luu_cai_dat(du_lieu=None):
	"""Ghi cấu hình. Chỉ giám đốc, và soát bậc trước khi ghi."""
	_kiem_quyen()
	if not _la_gd():
		frappe.throw("Chỉ ban giám đốc sửa được bảng chỉ tiêu và bậc hoa hồng.")
	d = frappe.parse_json(du_lieu) if isinstance(du_lieu, str) else (du_lieu or {})
	if not isinstance(d, dict):
		frappe.throw("Dữ liệu gửi lên không đúng định dạng.")
	moi = gop_cau_hinh(d)
	for vai, bo in (moi.get("bo") or {}).items():
		ts = tong_trong_so(bo)
		if abs(ts - 100) > 0.01:
			frappe.throw(
				"Bộ tiêu chí %s có tổng trọng số %s, phải bằng 100."
				% (bo.get("ten") or vai, ts)
			)
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG_CAU_HINH,
		json.dumps(moi, ensure_ascii=False, indent=1),
	)
	frappe.db.commit()
	return cai_dat()


@frappe.whitelist()
def nguoi_dung():
	"""Danh sách tài khoản còn hoạt động, để quản lý chọn dựng phiếu."""
	_kiem_quyen()
	ra = []
	for r in frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=0,
	):
		if r["name"] in ("Administrator", "Guest"):
			continue
		ra.append({"ma": r["name"], "ten": r.get("full_name") or r["name"]})
	return {"ds": ra}
