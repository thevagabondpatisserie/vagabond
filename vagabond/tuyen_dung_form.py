# -*- coding: utf-8 -*-
"""v625 Tuyển dụng đợt 2 (anh Việt 31/10/2026): form ứng tuyển dựng từ danh sách
câu hỏi mà Minh Vũ sửa trong trình biên tập web, và các phép bày vị trí lên web
(lương gọn, chia mục mô tả, ảnh theo bộ phận).

Anh chốt: dùng đúng 14 câu của form Lark "Điền thông tin tuyển dụng tại The
Vagabond năm 2026" làm câu mặc định, giữ câu "Tổng thu nhập mà bạn cảm thấy xứng
đáng với năng lực?"; câu giới tính và sinh nhật để như form Lark (bắt buộc), nhưng
AI không bao giờ dùng hai câu này khi chấm.

Toàn bộ tệp là phép THUẦN (không chạm Frappe), để ca kiểm chạy không cần site.
Nơi đọc, ghi cấu hình: noi_dung_web (khoá `tuyen_dung_form` trong bản công khai).
"""

import copy
import json
import re
from datetime import date


class LoiNhap(ValueError):
	"""Dữ liệu người dùng gửi lên không hợp lệ; câu lỗi đọc được, nói việc làm tiếp."""


# Loại câu trả lời. Tên và dòng giải thích hiện trong trình biên tập (mỗi lựa
# chọn có một dòng giải thích, skill vagabond-thiet-ke-tien-loi).
LOAI = {
	"chu": ("Chữ ngắn", "Một dòng"),
	"doan": ("Đoạn văn", "Nhiều dòng"),
	"so_tien": ("Số tiền", "Tự chấm nghìn, đ/tháng"),
	"chon_mot": ("Chọn một", "Chip, chọn 1"),
	"chon_nhieu": ("Chọn nhiều", "Chip, chọn nhiều"),
	"ngay": ("Ngày", "Ngày/tháng/năm"),
	"tep": ("Tệp", "PDF hoặc ảnh"),
	"so_dt": ("Số điện thoại", "Số di động Việt Nam"),
	"email": ("Email", "Địa chỉ email"),
	"vi_tri": ("Vị trí", "Lấy từ phiếu Vị trí trên ERP"),
}
# Loại Minh Vũ chọn được cho câu tự thêm. Ba loại sau gắn với câu gốc của hệ thống.
LOAI_TU_CHON = ("chu", "doan", "so_tien", "chon_mot", "chon_nhieu", "ngay")
BUOC = {1: "Về bạn", 2: "Kinh nghiệm", 3: "Mong muốn"}

# Câu có mã cố định thì máy biết đổ vào ô nào trên hồ sơ. Loại của các câu này
# khoá theo mã (không đổi email thành câu chọn). KHOA_XOA: ERP cần để gọi ứng
# viên, không xoá, luôn bắt buộc.
COT_THEO_MA = {
	"ho_ten": "ho_ten", "sdt": "sdt", "email": "email", "sinh_nhat": "sinh_nhat", "vi_tri": "vi_tri",
	"cv": "tep_cv", "luong": "luong_mong_muon", "nguoi_gioi_thieu": "nguoi_gioi_thieu", "nhan_them": "gioi_thieu",
}
LOAI_THEO_MA = {
	"ho_ten": "chu", "sdt": "so_dt", "email": "email", "sinh_nhat": "ngay", "vi_tri": "vi_tri", "cv": "tep",
	"luong": "so_tien", "nguoi_gioi_thieu": "chu", "nhan_them": "doan", "gioi_tinh": "chon_mot",
	"tham_nien": "chon_mot", "thoi_gian": "chon_mot", "hoc_van": "chon_mot", "biet_tin": "chon_mot",
}
KHOA_XOA = ("ho_ten", "sdt", "vi_tri")
# Không bao giờ đưa cho AI chấm (anh Việt 31/10/2026): giới tính, tuổi.
KHONG_CHO_AI = ("gioi_tinh", "sinh_nhat", "ho_ten", "sdt", "email")

TOI_DA_CAU = 30
TOI_DA_LUA_CHON = 12
DAI_HOI = 300
DAI_GOI_Y = 500
DAI_LUA_CHON = 100
DAI_CHU = 300
DAI_DOAN = 1500
TOI_DA_PHUC_LOI = 12
DAI_PHUC_LOI = 120
LUONG_TOI_DA = 1000000000


def _cau(ma, hoi, loai, bat_buoc, buoc, goi_y="", lua_chon=None, cho_khac=False, ai=True):
	return {"ma": ma, "hoi": hoi, "goi_y": goi_y, "loai": loai, "lua_chon": list(lua_chon or []),
		"cho_khac": bool(cho_khac), "bat_buoc": bool(bat_buoc), "buoc": buoc, "vi_tri": [], "ai": bool(ai)}


# 14 câu của form Lark, đọc ngày 31/10/2026, đúng chữ và đúng câu bắt buộc.
CAU_HOI_MAC_DINH = [
	_cau("ho_ten", "Họ và tên ứng viên", "chu", True, 1, ai=False),
	_cau("gioi_tinh", "Bạn tự định nghĩa giới của mình là?", "chon_mot", True, 1,
		"Giữa muôn vàn đa dạng giới dạng của cuộc sống muôn màu ngoài kia.",
		["Nam (Male)", "Nữ (Female)", "Phi nhị nguyên (Non-binary)", "Không tiết lộ"], cho_khac=True, ai=False),
	_cau("sinh_nhat", "Sinh nhật của bạn", "ngay", True, 1, ai=False),
	_cau("sdt", "Số điện thoại có Zalo", "so_dt", True, 1, "Chúng tôi sẽ tiện liên lạc với bạn hơn.", ai=False),
	_cau("email", "Email của bạn", "email", True, 1, "Hãy điền địa chỉ email còn hoạt động.", ai=False),
	_cau("vi_tri", "Vị trí ứng tuyển", "vi_tri", True, 2,
		"Mỗi người chúng ta đều là một bản thiết kế tuyệt vời để thực thi những nhiệm vụ khác nhau trong từng giai đoạn của cuộc đời!"),
	_cau("tham_nien", "Thâm niên cho vị trí ứng tuyển?", "chon_mot", False, 2,
		"Chỉ tính thời gian làm đúng vị trí bạn chọn ở trên.",
		["Dưới 1 năm", "Từ 1 - 2 năm", "Từ 2 - 3 năm", "Trên 3 năm"]),
	_cau("thoi_gian", "Thời gian làm việc mong muốn", "chon_mot", False, 2,
		"Part-time: đăng ký ca linh động 4-6 tiếng/ngày trong khung 7h00 - 22h30. Full-time: 6 ngày/tuần, xoay ca linh động.",
		["Full-time", "Part-time", "Linh hoạt"]),
	_cau("hoc_van", "Trình độ học vấn cao nhất", "chon_mot", True, 2, "",
		["Tốt nghiệp THPT", "Tốt nghiệp Trung cấp/Dạy nghề", "Tốt nghiệp Cao đẳng/Đại học", "Sau Đại học"]),
	_cau("cv", "Đính kèm CV/Portfolio có ảnh của bạn", "tep", False, 2,
		"CV là phần quan trọng để thể hiện năng lực, hãy cho chúng tôi thấy CV xuất sắc và được cập nhật của bạn."),
	_cau("luong", "Tổng thu nhập mà bạn cảm thấy xứng đáng với năng lực?", "so_tien", True, 3,
		"Cứ ghi đúng mong muốn của bạn."),
	_cau("biet_tin", "Tin tuyển dụng này bay đến với bạn bằng cách nào?", "chon_mot", True, 3, "",
		["Mạng xã hội", "Đã biết tiệm từ trước", "Trang web tuyển dụng", "Bạn bè giới thiệu"], ai=False),
	_cau("nguoi_gioi_thieu", "Tri ân người giới thiệu", "chu", False, 3,
		"Nếu có nhân sự của The Vagabond giới thiệu bạn ứng tuyển, hãy cho chúng tôi biết.", ai=False),
	_cau("nhan_them", "Hãy nói thêm ở đây!", "doan", False, 3,
		"Nếu có thêm điều gì nhắn nhủ hay thắc mắc cho The Vagabond, hãy viết thêm ở đây!"),
]

# Phúc lợi chung lấy từ phần giới thiệu của form Lark; hiện trên trang chi tiết.
PHUC_LOI_MAC_DINH = [
	"Ưu đãi 20% sản phẩm, dịch vụ của The Vagabond",
	"Voucher sinh nhật, voucher nhân viên xuất sắc",
	"Nghỉ phép, BHXH, BHTN đầy đủ theo Luật Lao động",
]
GIOI_THIEU_MAC_DINH = ("Nơi tập hợp của những tâm hồn ngọt ngào yêu cái đẹp và tràn đầy nhiệt huyết với nghề. "
	"Điền vài phút, không bắt buộc có CV.")


def mac_dinh():
	return {"cau_hoi": copy.deepcopy(CAU_HOI_MAC_DINH), "phuc_loi": list(PHUC_LOI_MAC_DINH),
		"gioi_thieu": GIOI_THIEU_MAC_DINH}


def _chu_gon(v, toi_da, ten, nhieu_dong=False):
	if not isinstance(v, str):
		v = "" if v is None else str(v)
	if nhieu_dong:
		v = "\n".join(re.sub(r"[ \t]+", " ", x).strip() for x in v.replace("\r", "").split("\n")).strip()
	else:
		v = re.sub(r"\s+", " ", v).strip()
	if len(v) > toi_da:
		raise LoiNhap("%s tối đa %s ký tự." % (ten, "{:,}".format(toi_da).replace(",", ".")))
	return v


def chuan_form(du_lieu):
	"""THUẦN: cấu hình form từ trình biên tập -> bản sạch để lưu.

	Ô người gõ tay là đầu vào không tin được: chữ thừa khoảng trắng, mã lạ, loại
	sai đều được chuẩn hoá hoặc chặn với câu nói rõ việc cần sửa. Câu gốc (họ
	tên, số điện thoại, vị trí) luôn còn, luôn bắt buộc; câu giới tính, sinh nhật
	không bao giờ cho AI dùng."""
	if isinstance(du_lieu, str):
		try:
			du_lieu = json.loads(du_lieu)
		except ValueError:
			raise LoiNhap("Không đọc được danh sách câu hỏi. Tải lại trang biên tập.")
	if not isinstance(du_lieu, dict):
		raise LoiNhap("Không đọc được danh sách câu hỏi. Tải lại trang biên tập.")
	ds = du_lieu.get("cau_hoi")
	if not isinstance(ds, list) or not ds:
		raise LoiNhap("Form cần ít nhất các câu họ tên, số điện thoại và vị trí.")
	if len(ds) > TOI_DA_CAU:
		raise LoiNhap("Form tối đa %d câu. Bớt câu ít dùng rồi lưu lại." % TOI_DA_CAU)
	ra, da_co = [], set()
	for i, c in enumerate(ds, 1):
		if not isinstance(c, dict):
			raise LoiNhap("Câu %d không đọc được. Tải lại trang biên tập." % i)
		ma = str(c.get("ma") or "").strip()
		if not re.fullmatch(r"(?:[a-z_]{2,20}|c_[a-z0-9]{4,12})", ma) or (not ma.startswith("c_") and ma not in LOAI_THEO_MA):
			raise LoiNhap("Câu %d có mã không hợp lệ. Xoá câu đó rồi thêm lại." % i)
		if ma in da_co:
			raise LoiNhap("Câu %d bị trùng. Xoá một câu rồi lưu lại." % i)
		da_co.add(ma)
		hoi = _chu_gon(c.get("hoi"), DAI_HOI, "Câu hỏi %d" % i)
		if len(hoi) < 3:
			raise LoiNhap("Câu %d chưa có chữ. Điền câu hỏi khách thấy." % i)
		loai = LOAI_THEO_MA.get(ma) or str(c.get("loai") or "")
		if ma.startswith("c_") and loai not in LOAI_TU_CHON:
			raise LoiNhap("Câu %d: chọn loại câu trả lời trong danh sách." % i)
		lua_chon = []
		if loai in ("chon_mot", "chon_nhieu"):
			for x in c.get("lua_chon") or []:
				x = _chu_gon(x, DAI_LUA_CHON, "Mỗi lựa chọn")
				if x and x not in lua_chon:
					lua_chon.append(x)
			if len(lua_chon) < 2:
				raise LoiNhap("Câu %d là câu chọn, cần ít nhất 2 lựa chọn." % i)
			if len(lua_chon) > TOI_DA_LUA_CHON:
				raise LoiNhap("Câu %d tối đa %d lựa chọn." % (i, TOI_DA_LUA_CHON))
		try:
			buoc = int(c.get("buoc") or 1)
		except (TypeError, ValueError):
			buoc = 1
		buoc = buoc if buoc in BUOC else 1
		vt = [str(x).strip() for x in (c.get("vi_tri") or []) if re.fullmatch(r"[A-Za-z0-9-]{1,40}", str(x).strip())]
		bat_buoc = c.get("bat_buoc") in (True, 1, "1", "true") or ma in KHOA_XOA
		if ma in KHOA_XOA:
			vt = []
		ra.append({"ma": ma, "hoi": hoi, "goi_y": _chu_gon(c.get("goi_y"), DAI_GOI_Y, "Dòng gợi ý câu %d" % i),
			"loai": loai, "lua_chon": lua_chon,
			"cho_khac": bool(c.get("cho_khac") in (True, 1, "1", "true")) and loai == "chon_mot",
			"bat_buoc": bool(bat_buoc), "buoc": buoc, "vi_tri": sorted(set(vt)),
			"ai": bool(c.get("ai") in (True, 1, "1", "true")) and ma not in KHONG_CHO_AI})
	thieu = [m for m in KHOA_XOA if m not in da_co]
	if thieu:
		ten = {"ho_ten": "Họ tên", "sdt": "Số điện thoại", "vi_tri": "Vị trí ứng tuyển"}
		raise LoiNhap("Không xoá được câu %s: ERP cần câu này để gọi ứng viên." % ", ".join(ten[m] for m in thieu))
	if sum(1 for c in ra if c["loai"] == "tep") > 1:
		raise LoiNhap("Form chỉ có một ô tải CV.")
	pl = []
	for x in du_lieu.get("phuc_loi") or []:
		x = _chu_gon(x, DAI_PHUC_LOI, "Mỗi dòng phúc lợi")
		if x and x not in pl:
			pl.append(x)
	if len(pl) > TOI_DA_PHUC_LOI:
		raise LoiNhap("Phúc lợi chung tối đa %d dòng." % TOI_DA_PHUC_LOI)
	return {"cau_hoi": ra, "phuc_loi": pl,
		"gioi_thieu": _chu_gon(du_lieu.get("gioi_thieu"), 600, "Lời giới thiệu", nhieu_dong=True)}


def form_hien(nd):
	"""THUẦN: cấu hình đang dùng từ bản công khai của nội dung web. Chưa có hoặc
	hỏng thì dùng 14 câu mặc định (trang ứng tuyển không bao giờ trắng)."""
	g = (nd or {}).get("tuyen_dung_form")
	if not g:
		return mac_dinh()
	try:
		return chuan_form(g)
	except LoiNhap:
		return mac_dinh()


def cau_cho_vi_tri(form, ma_vt):
	"""THUẦN: các câu hỏi áp cho một vị trí (câu không giới hạn vị trí áp mọi vị trí)."""
	return [c for c in form["cau_hoi"] if not c["vi_tri"] or ma_vt in c["vi_tri"]]


# ------------------------------------------------------------------ tiền

def doc_tien(v):
	"""THUẦN: chữ người gõ -> số đồng. Chịu mọi cách gõ hợp lý.

	'9.000.000', '9,000,000', '9000000', '9tr', '9 triệu', '9,5 triệu', '9.5tr',
	'9 củ', '12 - 15 triệu' (lấy số đầu), '35k' (35.000). Trả None nếu không đọc được."""
	s = str(v if v is not None else "").strip().lower()
	if not s:
		return None
	s = s.replace("đồng", "").replace("vnd", "").replace("đ", "").strip()
	# '9 000 000': khoảng trắng ngăn nghìn.
	s = re.sub(r"(?<=\d)[ \u00a0](?=\d{3}(?!\d))", "", s)
	m = re.search(r"\d+(?:[.,]\d+)*", s)
	if not m:
		return None
	so = m.group(0)
	sau = s[m.end():].strip()
	# '12 - 15 triệu': đơn vị đứng sau số thứ hai của khoảng.
	kh = re.match(r"(?:-|\u2013|~|đến|tới)\s*\d+(?:[.,]\d+)*\s*", sau)
	if kh:
		sau = sau[kh.end():]
	nhan = 1
	if re.match(r"(?:tr\b|tr\.|triệu|trieu|củ|cu\b|m\b)", sau) or sau.startswith("tr"):
		nhan = 1000000
	elif re.match(r"(?:k\b|nghìn|ngàn|ngan|nghin)", sau):
		nhan = 1000
	if nhan > 1:
		# 9,5 triệu hay 9.5tr: dấu là thập phân.
		gia = float(so.replace(",", "."))
	else:
		gia = float(re.sub(r"[.,]", "", so))
	n = int(round(gia * nhan))
	if n <= 0 or n > LUONG_TOI_DA:
		return None
	return n


def tien_chu(n):
	"""THUẦN: 9000000 -> '9.000.000'."""
	return "{:,}".format(int(n)).replace(",", ".")


def _gon(n):
	"""THUẦN: 7500000 -> '7,5 triệu'; 32000 -> '32.000đ'."""
	if n >= 1000000:
		t = round(n / 1000000.0, 1)
		return ("%g" % t).replace(".", ",") + " triệu"
	return tien_chu(n) + "đ"


def luong_gon(chu):
	"""THUẦN: dòng lương trên phiếu Vị trí -> chữ ngắn cho thẻ web.

	'Lương cơ bản được thoả thuận từ 7.500.000/tháng trở lên' -> 'Từ 7,5 triệu/tháng'.
	'Lương part-time: từ 32.000/h ... full-time: từ 7.000.0000/tháng' -> 'Từ 7 triệu · 32.000đ/giờ'.
	Không đọc được số thì trả '' (thẻ không hiện ô lương, trang chi tiết vẫn có câu gốc)."""
	s = str(chu or "")
	thang, gio = [], []
	for m in re.finditer(r"(\d{1,3}(?:[.,]\d{3,4})+|\d{4,})\s*(?:đ|đồng|vnđ|vnd)?\s*(/\s*(?:tháng|th|h|giờ|gio)\b)?", s, re.I):
		phan = re.split(r"[.,]", m.group(1))
		# '7.000.0000' gõ thừa một số 0 ở nhóm cuối: bỏ số 0 thừa.
		if len(phan) > 1 and len(phan[-1]) == 4 and phan[-1].endswith("0"):
			phan[-1] = phan[-1][:3]
		n = int("".join(phan))
		don = (m.group(2) or "").replace(" ", "").lower()
		if don in ("/h", "/giờ", "/gio") or (not don and n < 1000000):
			gio.append(n)
		else:
			thang.append(n)
	# '7-9 triệu', 'Từ 8tr'.
	for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*(?:(?:-|\u2013|đến|tới)\s*(\d+(?:[.,]\d+)?)\s*)?(?:triệu|tr)\b", s, re.I):
		for g in (m.group(1), m.group(2)):
			if g:
				thang.append(int(round(float(g.replace(",", ".")) * 1000000)))
	if not thang and not gio:
		return ""
	khoang = bool(re.search(r"\d\s*(?:-|\u2013|đến|tới)\s*\d", s))
	phan = []
	if thang and khoang and len(set(thang)) >= 2:
		lo, hi = min(thang), max(thang)
		phan.append(_gon(lo).replace(" triệu", "") + " - " + _gon(hi) + ("/tháng" if not gio else ""))
	elif thang:
		phan.append(_gon(min(thang)) + ("/tháng" if not gio else ""))
	if gio and khoang and len(set(gio)) >= 2:
		phan.append(tien_chu(min(gio)) + " - " + tien_chu(max(gio)) + "đ/giờ")
	elif gio:
		phan.append(tien_chu(min(gio)) + "đ/giờ")
	ra = " · ".join(phan)
	tu = re.search(r"\btừ\b|trở lên|\bfrom\b", s, re.I) and not (khoang and (len(set(thang)) >= 2 or len(set(gio)) >= 2))
	return ("Từ " + ra) if tu else ra


def tach_luong(muc_luong, yeu_cau):
	"""THUẦN: (dòng lương đầy đủ, các dòng yêu cầu còn lại). Ô Mức lương trên
	phiếu Vị trí đứng trước; không có thì lấy dòng 'Mức lương: ...' trong yêu cầu."""
	dong = [x.strip() for x in str(yeu_cau or "").splitlines() if x.strip()]
	luong = str(muc_luong or "").strip()
	con = []
	for x in dong:
		if not luong and re.match(r"(?:mức\s+)?lương\s*:", x, re.I):
			luong = re.sub(r"^(?:mức\s+)?lương\s*:\s*", "", x, flags=re.I)
			continue
		con.append(x)
	return luong, con


TU_QUYEN_LOI = ("phụ cấp", "bhxh", "bhyt", "bhtn", "bảo hiểm", "thưởng", "nghỉ phép", "ưu đãi", "voucher",
	"du lịch", "đào tạo miễn phí", "tăng lương", "lương tháng 13")


def chia_yeu_cau(dong):
	"""THUẦN: dòng yêu cầu và quyền lợi -> (chúng tôi cần, quyền lợi)."""
	can, ql = [], []
	for x in dong:
		(ql if any(t in x.lower() for t in TU_QUYEN_LOI) else can).append(x)
	return can, ql


TEN_MUC = ("thời gian làm việc", "giờ làm việc", "thời gian", "ca làm", "ca làm việc", "địa điểm", "nơi làm việc",
	"mô tả công việc", "công việc", "nhiệm vụ", "yêu cầu", "yêu cầu công việc", "quyền lợi", "phúc lợi",
	"chế độ", "thu nhập", "mức lương", "lương", "kỹ năng", "kinh nghiệm", "liên hệ", "cách ứng tuyển")


def la_ten_muc(dong):
	"""THUẦN: một dòng mô tả có phải tên mục con không. Chặt tay: dòng kết thúc
	bằng dấu hai chấm, dòng viết hoa toàn bộ, hoặc trùng một tên mục quen thuộc.
	Dòng việc thường ngắn và không dấu chấm cuối, nên không đoán theo độ dài."""
	x = str(dong or "").strip()
	if not x or len(x) > 60 or re.match(r"^[-•*+]", x):
		return False
	than = x.rstrip(":").strip()
	if x.endswith(":") and than and len(than) <= 50:
		return True
	chu = re.sub(r"[^A-Za-zÀ-ỹ]", "", than)
	if len(chu) >= 4 and than.upper() == than and than.lower() != than:
		return True
	return than.lower() in TEN_MUC


def chia_noi_dung(noi_dung):
	"""THUẦN: mô tả công việc -> các mục [{tieu_de, dong}].

	Mục đầu tên 'Bạn sẽ làm'. Dòng là tên mục con (la_ten_muc) thì mở mục mới;
	gạch đầu dòng bị bỏ. Mục rỗng không trả về."""
	muc = [{"tieu_de": "Bạn sẽ làm", "dong": []}]
	for x in str(noi_dung or "").splitlines():
		x = x.strip()
		if not x:
			continue
		if la_ten_muc(x):
			t = x.rstrip(":").strip()
			muc.append({"tieu_de": t[:1].upper() + t[1:].lower() if t.upper() == t else t, "dong": []})
			continue
		muc[-1]["dong"].append(re.sub(r"^[-•*+]\s*", "", x))
	return [m for m in muc if m["dong"]]


# Ảnh mặc định theo bộ phận khi vị trí chưa chọn ảnh (ảnh có sẵn của trang web).
ANH_BEP = "/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg"
ANH_QUAY = "/assets/vagabond/images/quay-sales.jpg"
ANH_CUA_HANG = "/assets/vagabond/images/quay-tcv.jpg"
ANH_CHUNG = "/assets/vagabond/web_order/og-banh.jpg"
ANH_CHON = (
	(ANH_BEP, "Bếp làm bánh", "Tay thợ bánh bắt kem, hợp với vị trí bếp"),
	(ANH_QUAY, "Quầy bánh", "Quầy bánh tại xưởng, hợp với sales và thu ngân"),
	(ANH_CUA_HANG, "Cửa hàng", "Mặt tiền cửa hàng Trần Cao Vân, hợp với phục vụ"),
	(ANH_CHUNG, "Bánh và logo", "Ảnh chung của thương hiệu"),
)


def anh_theo_nhom(nhom, tieu_de=""):
	"""THUẦN: ảnh mặc định theo bộ phận hoặc tên vị trí."""
	s = (str(nhom or "") + " " + str(tieu_de or "")).lower()
	if any(t in s for t in ("bếp", "pastry", "baker", "bánh", "sơ chế", "kitchen")):
		return ANH_BEP
	if any(t in s for t in ("sales", "bán hàng", "thu ngân", "cashier", "kiosk")):
		return ANH_QUAY
	if any(t in s for t in ("phục vụ", "barista", "pha chế", "cửa hàng", "waiter", "giao hàng")):
		return ANH_CUA_HANG
	return ANH_CHUNG


# ------------------------------------------------------------------ trả lời

def _ngay(v):
	s = str(v or "").strip()[:10]
	try:
		return date.fromisoformat(s)
	except ValueError:
		return None


def chuan_tra_loi(form, ma_vt, tra_loi, hom_nay, chuan_sdt, co_cv=False):
	"""THUẦN: câu trả lời gửi lên -> (cột hồ sơ, các dòng trả lời).

	form: cấu hình đang dùng; tra_loi: {mã câu: giá trị}. Chỉ nhận câu áp cho vị
	trí; câu thiếu mà bắt buộc thì báo đúng câu đó. chuan_sdt truyền vào để dùng
	đúng một phép chuẩn số của tuyen_dung. co_cv: đã có tệp CV đi kèm."""
	if not isinstance(tra_loi, dict):
		raise LoiNhap("Không đọc được câu trả lời. Tải lại trang rồi gửi lại.")
	cot, dong = {}, []
	for c in cau_cho_vi_tri(form, ma_vt):
		ma, loai, hoi = c["ma"], c["loai"], c["hoi"]
		if loai == "vi_tri":
			continue
		v = tra_loi.get(ma)
		if loai == "tep":
			if c["bat_buoc"] and not co_cv:
				raise LoiNhap("Tải CV lên ở câu \"%s\"." % hoi)
			continue
		if loai == "chon_nhieu":
			v = [x for x in (v if isinstance(v, list) else []) if isinstance(x, str)]
			v = [x for x in c["lua_chon"] if x in v]
			chu = ", ".join(v)
		else:
			if isinstance(v, (list, dict)):
				v = ""
			chu = re.sub(r"\s+", " ", str(v if v is not None else "")).strip() if loai != "doan" else \
				"\n".join(x.strip() for x in str(v if v is not None else "").replace("\r", "").split("\n")).strip()
		if not chu:
			if c["bat_buoc"]:
				raise LoiNhap("Trả lời câu \"%s\"." % hoi)
			continue
		if loai == "chu":
			if len(chu) > DAI_CHU:
				raise LoiNhap("Câu \"%s\" tối đa %d ký tự." % (hoi, DAI_CHU))
			if ma == "ho_ten" and len(chu) < 2:
				raise LoiNhap("Điền họ tên của bạn.")
		elif loai == "doan":
			if len(chu) > DAI_DOAN:
				raise LoiNhap("Câu \"%s\" tối đa %s ký tự." % (hoi, tien_chu(DAI_DOAN)))
		elif loai == "so_dt":
			chu = chuan_sdt(chu)
			if not chu:
				raise LoiNhap("Điền số điện thoại di động Việt Nam, ví dụ 0909 123 456.")
		elif loai == "email":
			if len(chu) > 140 or not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}", chu):
				raise LoiNhap("Kiểm tra lại email, ví dụ ten@gmail.com.")
		elif loai == "ngay":
			d = _ngay(chu)
			if not d:
				raise LoiNhap("Câu \"%s\": chọn đủ ngày, tháng, năm." % hoi)
			# Giới hạn ngày sinh chỉ áp cho câu sinh nhật; câu ngày tự thêm (ngày có
			# thể bắt đầu làm...) nhận cả ngày tương lai (Codex #523).
			if ma == "sinh_nhat" and (d > hom_nay or d.year < 1940):
				raise LoiNhap("Câu \"%s\": kiểm tra lại năm sinh." % hoi)
			if not 1900 <= d.year <= hom_nay.year + 5:
				raise LoiNhap("Câu \"%s\": kiểm tra lại năm." % hoi)
			chu = d.isoformat()
		elif loai == "so_tien":
			n = doc_tien(chu)
			if not n:
				raise LoiNhap("Câu \"%s\": ghi số tiền, ví dụ 9.000.000." % hoi)
			chu = n
		elif loai == "chon_mot":
			if chu not in c["lua_chon"]:
				if not c["cho_khac"] or len(chu) > DAI_LUA_CHON:
					raise LoiNhap("Câu \"%s\": chọn một lựa chọn trong danh sách." % hoi)
		if ma in COT_THEO_MA:
			cot[COT_THEO_MA[ma]] = chu
		hien = (tien_chu(chu) + " đ/tháng") if loai == "so_tien" else (
			"/".join(reversed(chu.split("-"))) if loai == "ngay" else str(chu))
		dong.append({"ma": ma, "cau_hoi": hoi, "tra_loi": hien})
	if "ho_ten" not in cot or "sdt" not in cot:
		raise LoiNhap("Điền họ tên và số điện thoại để chúng tôi gọi lại.")
	return cot, dong


def cv_cho_ai(form):
	"""THUẦN: tệp CV có được gửi cho AI không. Theo công tắc "Cho AI dùng" của
	câu CV (Codex #523: tắt mà tệp vẫn đi). Form không có câu CV thì không gửi."""
	return any(c["ma"] == "cv" and c["ai"] for c in form["cau_hoi"])


def du_phong_cho_ai(form, dong):
	"""THUẦN: dòng dự phòng của hồ sơ cũ, thêm tay (lấy từ ô hồ sơ, không có bảng
	câu trả lời). Ô trùng mã một câu form thì theo công tắc "Cho AI dùng" của câu
	đó (Codex #523); ô quản lý tự ghi (kinh nghiệm, ca rảnh, khu vực) vẫn gửi; giới
	tính, sinh nhật, liên lạc không bao giờ gửi."""
	tat = {c["ma"] for c in form["cau_hoi"] if not c["ai"]} | set(KHONG_CHO_AI)
	return [d for d in dong if d.get("tra_loi") and d.get("ma") not in tat]


def tra_loi_cho_ai(form, dong):
	"""THUẦN: các dòng trả lời được phép đưa cho AI (bỏ giới tính, sinh nhật,
	thông tin liên lạc, và câu Minh Vũ tắt 'Cho AI dùng')."""
	cho = {c["ma"] for c in form["cau_hoi"] if c["ai"] and c["ma"] not in KHONG_CHO_AI}
	return [d for d in dong if d.get("ma") in cho]
