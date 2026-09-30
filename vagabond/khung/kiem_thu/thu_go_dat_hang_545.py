"""v545: gỡ vai "Bộ phận đặt hàng" khỏi mọi tập quyền bán hàng.

Anh Việt 01/10/2026: "Bộ phận đặt hàng" là nhân viên đặt hàng lên cho thu
mua (bếp, kho, thu mua đều giữ vai này), không phải vai bán hàng. Trước đây
vai này nằm trong tập quyền bán hàng nên bếp và kho bấm được các nút thu tiền
ở màn Công nợ, đồng bộ đơn web, khuyến mãi. Kiểm trên site 01/10: mọi Sales
thật đều giữ Sales User; 6 tài khoản chỉ có Bộ phận đặt hàng không lập hoá
đơn bán hay phiếu thu nào từ 01/09.

Đọc văn bản tệp, không import (ban_hang kéo theo requests, CI không có).
"""

import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAI = "Bộ phận đặt hàng"

TAP_BAN_HANG = [
	("ban_hang.py", "QUYEN_BAN_HANG_THAT"),
	("van_don.py", "QUYEN_SALES"),
	("web_dong_bo.py", "QUYEN"),
	("doi_soat.py", "QUYEN"),
	("khuyen_mai.py", "QUYEN_KM"),
	("viec_can_lam.py", "VAI_SALES"),
]


def _doc(t):
	return open(os.path.join(GOC, t), encoding="utf-8").read()


def _tap_that():
	"""Đọc ĐÚNG ba tập quyền đang có trong ban_hang.py, không tự gõ lại trong ca kiểm.

	#398 vòng 4: ca cũ tự khai tập quyền trong globals, nên đổi tập thật ở
	ban_hang.py thì ca vẫn xanh. Giờ chạy đúng các dòng khai báo trong tệp.
	"""
	s = _doc("ban_hang.py")
	g = {}
	for ten in ("QUYEN_BAN_HANG", "QUYEN_BAN_HANG_THAT", "QUYEN_BAN_VA_KE_TOAN"):
		m = re.search(r"^%s\s*=.*$" % ten, s, re.M)
		exec(m.group(0), g)
	return {k: g[k] for k in ("QUYEN_BAN_HANG", "QUYEN_BAN_HANG_THAT", "QUYEN_BAN_VA_KE_TOAN")}


def _tap(t, ten):
	m = re.search(r"^%s\s*=\s*\{([^}]*)\}" % re.escape(ten), _doc(t), re.M)
	return m.group(1) if m else None


@ca("v545 Bộ phận đặt hàng không nằm trong tập quyền bán hàng nào")
def _khong_trong_ban_hang():
	for t, ten in TAP_BAN_HANG:
		than = _tap(t, ten)
		dung("%s có tập %s" % (t, ten), than is not None)
		dung("%s.%s không có Bộ phận đặt hàng" % (t, ten), than is not None and VAI not in than)
		dung("%s.%s vẫn có Sales User" % (t, ten), than is not None and "Sales User" in than)


@ca("v545 gợi ý người nhận việc bộ phận Sales không gợi ý Bộ phận đặt hàng")
def _goi_y_sales():
	m = re.search(r'"sales":\s*\{([^}]*)\}', _doc("phan_tich.py"))
	dung("có dòng sales", bool(m))
	dung("không gợi ý Bộ phận đặt hàng", bool(m) and VAI not in m.group(1))


@ca("v545 app bếp: isSales không tính Bộ phận đặt hàng")
def _is_sales_js():
	s = _doc(os.path.join("public", "js", "bep", "06-nhap-kho-kiem-ke.js"))
	m = re.search(r"function isSales\(\)\s*\{([^}]*)\}", s)
	dung("có isSales", bool(m))
	dung("isSales không có Bộ phận đặt hàng", bool(m) and VAI not in m.group(1))


@ca("v545 vai thu mua vẫn giữ Bộ phận đặt hàng (đặt hàng, kiểm kê, xuất kho)")
def _thu_mua_giu():
	dung("viec_can_lam.VAI_THU_MUA giữ", VAI in (_tap("viec_can_lam.py", "VAI_THU_MUA") or ""))
	dung("kiem_ke.VAI_DEM giữ", VAI in (_tap("kiem_ke.py", "VAI_DEM") or ""))
	dung("xuat_kho.VAI_XUAT giữ", VAI in (_tap("xuat_kho.py", "VAI_XUAT") or ""))


@ca("v545 Codex #398: cổng chung QUYEN_BAN_HANG giữ Bộ phận đặt hàng, Việc cần làm của bếp, kho, thu mua không bị khoá")
def _cong_chung_giu():
	than = _tap("ban_hang.py", "QUYEN_BAN_HANG")
	dung("QUYEN_BAN_HANG còn Bộ phận đặt hàng", than is not None and VAI in than)
	s = _doc("viec_can_lam.py")
	i = s.index("def danh_sach(")
	dung("Việc cần làm vẫn qua cổng chung QUYEN_BAN_HANG", "QUYEN_BAN_HANG & set(vai)" in s[i:i + 1500])


@ca("v545 đọc, lưu đơn và thu tiền khách chỉ cho Sales thật và kế toán")
def _doc_luu_don_chi_sales():
	s = _doc("ban_hang.py")
	i = s.index("def _kiem_quyen_doc_luu_don(")
	than = s[i:s.index("\ndef ", i + 10)]
	dung("dùng QUYEN_BAN_VA_KE_TOAN", "QUYEN_BAN_VA_KE_TOAN" in than)
	dung("không dùng cổng chung", "(QUYEN_BAN_HANG |" not in than)
	t = _doc("thu_tien.py")
	for ham in ("def nhan_tien_ve(", "def ung_vien_tien_ve(", "def ghi_so_phieu_thu("):
		j = t.index(ham)
		dung("%s qua cổng đọc, lưu đơn" % ham, "_kiem_quyen_doc_luu_don()" in t[j:j + 2500])


@ca("v545 chạy thật cổng đọc, lưu đơn: Bộ phận đặt hàng bị chặn, Sales và kế toán qua")
def _chay_cong_doc_luu_don():
	from types import SimpleNamespace as NS
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap

	def nem(cau, **kw):
		raise PermissionError(cau)

	for vai, mong in (("Bộ phận đặt hàng", False), ("Sales User", True), ("Sales Manager", True),
			("Accounts User", True), ("Accounts Manager", True), ("Guest", False)):
		g = dict(frappe=NS(get_roles=lambda v=vai: [v], throw=nem), **_tap_that())
		ham = nap("ban_hang.py", "_kiem_quyen_doc_luu_don", g)
		try:
			ham()
			qua = True
		except PermissionError:
			qua = False
		dung("%s %s" % (vai, "qua" if mong else "bị chặn"), qua == mong)
	g = dict(frappe=NS(get_roles=lambda: [VAI], throw=nem), **_tap_that())
	ham = nap("ban_hang.py", "_kiem_quyen", g)
	try:
		ham()
		qua = True
	except PermissionError:
		qua = False
	dung("cổng chung vẫn cho Bộ phận đặt hàng qua", qua)


# Codex #398 vòng 3 (review 1b08afa61f): giữ vai trong cổng chung thì mọi hàm
# ghi đơn bán còn gọi _kiem_quyen() vẫn mở cho Bộ phận đặt hàng qua API trực
# tiếp, dù màn hình đã ẩn. Sửa bằng MỘT cổng riêng _kiem_quyen_ban cho toàn bộ
# mô đun bán hàng và hoàn tiền, và chốt "không còn chỗ nào dùng cổng chung".
MO_DUN_BAN = ("ban_hang.py", "hoan_tien.py")


@ca("v545 Codex #398 v3: mô đun bán hàng và hoàn tiền không còn gọi cổng chung _kiem_quyen()")
def _khong_con_cong_chung_trong_ban():
	for t in MO_DUN_BAN:
		s = _doc(t)
		con = [m.start() for m in re.finditer(r"(?<![\w.])_kiem_quyen\(\)", s)
			if not s[max(0, m.start() - 4):m.start()].endswith("def ")]
		dung("%s còn %d chỗ gọi cổng chung" % (t, len(con)), not con)
		dung("%s có gọi cổng bán hàng" % t, "_kiem_quyen_ban()" in s)
	s = _doc("ban_hang.py")
	i = s.index("def _kiem_quyen_ban(")
	than = s[i:s.index("\ndef ", i + 10)]
	dung("cổng bán hàng dùng QUYEN_BAN_VA_KE_TOAN", "QUYEN_BAN_VA_KE_TOAN &" in than and "QUYEN_BAN_HANG &" not in than)


@ca("v545 Codex #398 v3: chạy thật pos_chot, pos_luu_don, dong_bo_doanh_so với vai Bộ phận đặt hàng thì bị chặn trước khi đọc đơn")
def _chay_that_ham_ghi_ban():
	from types import SimpleNamespace as NS
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap

	def nem(cau, **kw):
		raise PermissionError(cau)

	for vai, mong in ((VAI, False), ("Guest", False), ("Sales User", True), ("Sales Manager", True),
			("Accounts User", True), ("Accounts Manager", True), ("Manufacturing User", False)):
		for ten, doi in (("pos_chot", ("SI1",)), ("pos_luu_don", ("SI1",)), ("dong_bo_doanh_so", ())):
			vet = []

			def doc(*a, **k):
				vet.append("doc")
				raise LookupError("dừng sau quyền")

			g = dict(frappe=NS(get_roles=lambda v=vai: [v], throw=nem),
				_pos_lay=doc, _dong_bo_doanh_so=doc, **_tap_that())
			nap("ban_hang.py", "_kiem_quyen", g)
			nap("ban_hang.py", "_kiem_quyen_ban", g)
			try:
				nap("ban_hang.py", ten, g)(*doi)
			except PermissionError:
				pass
			except LookupError:
				pass
			dung("%s / %s %s" % (ten, vai, "qua quyền" if mong else "bị chặn"), (vet == ["doc"]) == mong)


# Codex #398 vòng 4 (review a498c9732a): cong_no.khop_tay và các mô đun thu
# tiền, công nợ khác vẫn nhập cổng chung. Gom về một luật: mọi mô đun bán hàng,
# công nợ phải thu, dòng tiền quầy KHÔNG được nhập cổng chung _kiem_quyen hay
# tập QUYEN_BAN_HANG từ ban_hang. Mô đun dùng chung (Việc cần làm, mua vụ,
# kho, thu mua) vẫn dùng cổng chung, có chủ đích.
MO_DUN_THU_TIEN = ("cong_no.py", "thanh_toan_nhieu.py", "nop_quy.py", "don_huy.py",
	"ca_quay.py", "diem_otp.py", "khach_hang.py", "nguoi_ban.py", "hang_tang.py", "hoan_tien.py")


@ca("v546 Codex #398 v4: mô đun công nợ, dòng tiền quầy, hoàn tiền không nhập cổng chung")
def _thu_tien_khong_nhap_cong_chung():
	for t in MO_DUN_THU_TIEN:
		s = _doc(t)
		nhap = re.findall(r"from vagabond\.ban_hang import[^\n]*", s)
		sai = [x for x in nhap if re.search(r"\b(_kiem_quyen|QUYEN_BAN_HANG)\b(?!_)", x)]
		dung("%s nhập cổng chung: %s" % (t, sai), not sai)
		dung("%s có đi qua cổng bán hàng" % t, "_kiem_quyen_ban" in s)


@ca("v546 Codex #398 v4: chạy thật cong_no.khop_tay, Bộ phận đặt hàng bị chặn trước khi đọc phiếu")
def _chay_that_khop_tay():
	from types import SimpleNamespace as NS
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap

	def nem(cau, **kw):
		raise PermissionError(cau)

	for vai, mong in ((VAI, False), ("Manufacturing User", False), ("Sales User", True), ("Accounts User", True)):
		vet = []

		def doc(*a, **k):
			vet.append("doc")
			raise LookupError("dừng sau quyền")

		g = dict(frappe=NS(get_roles=lambda v=vai: [v], throw=nem, get_doc=doc),
			flt=lambda x: float(x or 0), **_tap_that())
		g["_kiem_quyen_ban"] = nap("ban_hang.py", "_kiem_quyen_ban", g)
		try:
			nap("cong_no.py", "khop_tay", g)("CN1", 100000)
		except (PermissionError, LookupError):
			pass
		dung("khop_tay / %s %s" % (vai, "qua quyền" if mong else "bị chặn"), (vet == ["doc"]) == mong)


@ca("v546 Codex #398 v4: cờ ban_hang trên app theo cổng bán hàng, Việc cần làm theo cờ cổng chung")
def _co_quyen_nen():
	s = _doc("nhan_su.py")
	dung("cờ ban_hang dùng QUYEN_BAN_VA_KE_TOAN", '"ban_hang": bool(vai & QUYEN_BAN_VA_KE_TOAN)' in s)
	dung("có cờ cong_chung theo QUYEN_BAN_HANG", '"cong_chung": bool(vai & QUYEN_BAN_HANG)' in s)
	j = _doc("public/js/bep/02-trang-chu.js")
	i = j.index("async function vgbDemVCL(")
	dung("đếm Việc cần làm hỏi cờ cong_chung", "nenCoQuyen('cong_chung')" in j[i:i + 400])
	t = _tap_that()
	dung("kế toán nằm trong cổng bán hàng", {"Accounts User", "Accounts Manager"} <= t["QUYEN_BAN_VA_KE_TOAN"])
	dung("Bộ phận đặt hàng không nằm trong cổng bán hàng", VAI not in t["QUYEN_BAN_VA_KE_TOAN"])
	dung("Bộ phận đặt hàng vẫn trong cổng chung", VAI in t["QUYEN_BAN_HANG"])
