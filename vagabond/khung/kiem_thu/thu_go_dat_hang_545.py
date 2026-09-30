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
	dung("dùng QUYEN_BAN_HANG_THAT", "QUYEN_BAN_HANG_THAT" in than)
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
		g = dict(frappe=NS(get_roles=lambda v=vai: [v], throw=nem),
			QUYEN_BAN_HANG={"System Manager", "Sales User", "Sales Manager", VAI},
			QUYEN_BAN_HANG_THAT={"System Manager", "Sales User", "Sales Manager"})
		ham = nap("ban_hang.py", "_kiem_quyen_doc_luu_don", g)
		try:
			ham()
			qua = True
		except PermissionError:
			qua = False
		dung("%s %s" % (vai, "qua" if mong else "bị chặn"), qua == mong)
	g = dict(frappe=NS(get_roles=lambda: [VAI], throw=nem),
		QUYEN_BAN_HANG={"System Manager", "Sales User", "Sales Manager", VAI})
	ham = nap("ban_hang.py", "_kiem_quyen", g)
	try:
		ham()
		qua = True
	except PermissionError:
		qua = False
	dung("cổng chung vẫn cho Bộ phận đặt hàng qua", qua)
