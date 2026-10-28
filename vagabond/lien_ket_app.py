# -*- coding: utf-8 -*-
"""Mọi đường mở trong tin Zalo đi vào APP, không vào bản desktop (Desk).

Anh Việt 28/10/2026: tin "Đã chuyển hàng giữa kho" ghi
"Mở: https://vagabond.s.frappe.cloud/app/stock-entry/PDC-2026-00602", nhân
viên bấm trên điện thoại thì ra màn Desk của ERPNext. Anh chốt: link trong
thông báo Zalo phải là link app hết, không để link desktop.

MỘT NGUỒN
---------
Có hơn bốn mươi chỗ phát tin, mỗi chỗ tự ghép "/app/<loại>/<mã>". Sửa từng
chỗ thì chỗ mới viết sau lại quên. Nên cửa ghi tin (kenh_zalo._ghi_hop_thu)
cho MỌI tin đi qua `doi_trong_chu`. Mọi đường Desk trong tin, ở dòng "Mở:"
hay nằm giữa nội dung, đều đổi sang màn app tương ứng trên tên miền app.
Đường đã là màn app mà nằm trên tên miền mặc định của site thì đổi sang tên
miền app. Đường của khách (order.*) và đường ngoài site thì để nguyên.

Bảng BANG ánh xạ loại chứng từ (đường Desk) sang màn app. Một số loại chia
theo tiền tố mã phiếu, đọc từ site ngày 28/10/2026:
  phiếu kho     PDC điều chuyển, PSX sản xuất, PNT nhập thẳng,
                PXD xuất (huỷ và dùng nội bộ dùng chung tiền tố, nên nơi phát
                tin xuất huỷ, xuất nội bộ tự ghi đường màn đúng)
  yêu cầu       YCSX sản xuất, YCMH mua hàng, YCDC điều chuyển
Loại chưa có màn app thì về trang chủ app, không bao giờ để lại đường Desk.

Phiếu điều chuyển mở thẳng đúng phiếu trên màn "Hàng chuyển về kho tôi" qua
tham số ?mo=<mã phiếu> (02-trang-chu.js đọc tham số này lúc mở app).
"""

import re
from urllib.parse import parse_qs, unquote, urlsplit

TRANG_CHU = "/bep"

# Đường Desk (sau /app/) -> đường màn app. Giá trị là hàm (mã, tham số) -> đường.
MAN_DIEU_CHUYEN = "/hang-chuyen-ve-kho-toi"


def _phieu_kho(ma, ts):
	ma = ma or ""
	if ma.startswith("PDC-"):
		return MAN_DIEU_CHUYEN + "?mo=" + ma
	if ma.startswith("PSX-"):
		return "/san-xuat"
	if ma.startswith("PNT-"):
		return "/nhap-kho"
	return "/phan-he-xuat-kho"


def _yeu_cau(ma, ts):
	ma = ma or ""
	loai = (ts.get("material_request_type") or [""])[0]
	if ma.startswith("YCSX-") or loai == "Manufacture":
		return "/lap-ke-hoach-san-xuat"
	if ma.startswith("YCDC-") or loai == "Material Transfer":
		return "/xuat-dieu-chuyen"
	return "/duyet-yeu-cau"


def _bao_cao(ma, ts):
	if (ma or "").strip().lower() == "stock balance":
		return "/ton-kho"
	return "/bao-cao"


def _co_dinh(duong):
	return lambda ma, ts: duong


BANG = {
	"stock-entry": _phieu_kho,
	"material-request": _yeu_cau,
	"query-report": _bao_cao,
	"purchase-order": _co_dinh("/don-mua-hang"),
	"purchase-receipt": _co_dinh("/nhap-kho"),
	"purchase-invoice": _co_dinh("/hoa-don-mua"),
	"delivery-note": _co_dinh("/xuat-ban-si"),
	"phieu-kiem-ke": _co_dinh("/kiem-ke"),
	"stock-reconciliation": _co_dinh("/kiem-ke"),
	"batch": _co_dinh("/ton-kho"),
	"work-order": _co_dinh("/san-xuat"),
	"sales-invoice": _co_dinh("/hoa-don-ban"),
	"payment-entry": _co_dinh("/thanh-toan"),
	"journal-entry": _co_dinh("/but-toan"),
	"vagabond-don-web": _co_dinh("/doanh-so"),
	"vagabond-dang-ky-tiec": _co_dinh("/don-tiec"),
	"vagabond-dat-ban": _co_dinh("/thong-tin-dat-ban"),
	"vagabond-kiem-kho-diem": _co_dinh("/kiem-banh"),
}


def la_duong_desk(duong):
	"""Đường (phần path) là của Desk ERPNext: /app, /app/..., /desk..."""
	d = "/" + str(duong or "").lstrip("/")
	return d == "/app" or d.startswith("/app/") or d == "/desk" or d.startswith("/desk/")


def duong_app(duong, hoi=""):
	"""THUẦN: đường Desk (path, chuỗi hỏi) -> đường màn app.

	    /app/stock-entry/PDC-2026-00602  -> /hang-chuyen-ve-kho-toi?mo=PDC-2026-00602
	    /app/purchase-order?status=...   -> /don-mua-hang
	    /app/loai-chua-co-man/X          -> /bep
	"""
	d = "/" + str(duong or "").lstrip("/")
	if d.startswith("/desk"):
		d = "/app" + d[len("/desk"):]
	phan = [unquote(x) for x in d.split("/") if x]
	if len(phan) < 2 or phan[0] != "app":
		return TRANG_CHU
	loai = phan[1].lower()
	ma = phan[2] if len(phan) > 2 else ""
	if ma == "new":
		ma = ""
	ham = BANG.get(loai)
	if not ham:
		return TRANG_CHU
	try:
		ts = parse_qs(hoi or "")
	except Exception:
		ts = {}
	return ham(ma, ts) or TRANG_CHU


def doi_link(link, goc_app, may_cua_site=()):
	"""THUẦN: một đường mở -> đường app tuyệt đối trên tên miền app.

	goc_app: "https://app.thevagabondpatisserie.com" (không có / cuối).
	may_cua_site: các tên máy của chính site (tên miền mặc định, erp.*, app.*);
	đường trên các máy này được đổi về tên miền app. Máy khác để nguyên.
	"""
	s = str(link or "").strip()
	if not s:
		return link
	goc = str(goc_app or "").rstrip("/")
	cua_site = {str(x or "").lower() for x in may_cua_site if x}
	if s.startswith("/"):
		p = urlsplit(s)
		if la_duong_desk(p.path):
			return goc + duong_app(p.path, p.query)
		return goc + s
	try:
		p = urlsplit(s)
	except Exception:
		return link
	if p.scheme not in ("http", "https"):
		return link
	may = (p.hostname or "").lower()
	if may not in cua_site:
		return link
	if la_duong_desk(p.path):
		return goc + duong_app(p.path, p.query)
	duoi = (p.path or "") + (("?" + p.query) if p.query else "") + (("#" + p.fragment) if p.fragment else "")
	return goc + (duoi or TRANG_CHU)


RE_URL = re.compile(r"https?://[^\s<>\"']+")
# Đường Desk tương đối đứng riêng (sau khoảng trắng hoặc đầu dòng).
RE_DESK = re.compile(r"(?<![\w/.:-])/(?:app|desk)(?:/[^\s<>\"']*)?")


# Dấu câu dính ở cuối đường (cuối câu) không thuộc đường.
DUOI_CAU = ".,;:!?)]}"


def _doi_khop(m, goc_app, may_cua_site):
	s = m.group(0)
	duoi = ""
	while s and s[-1] in DUOI_CAU:
		duoi = s[-1] + duoi
		s = s[:-1]
	return doi_link(s, goc_app, may_cua_site) + duoi


def doi_trong_chu(chu, goc_app, may_cua_site=()):
	"""THUẦN: đổi mọi đường mở trong nội dung một tin sang đường app."""
	if not chu:
		return chu
	t = RE_URL.sub(lambda m: _doi_khop(m, goc_app, may_cua_site), str(chu))
	return RE_DESK.sub(lambda m: _doi_khop(m, goc_app, may_cua_site), t)


# ------------------------------------------------------- phần chạm Frappe

def goc_app():
	"""Địa chỉ app cho nhân viên (ô link_app trong Cài đặt, rồi tới địa chỉ site)."""
	from vagabond.nhan_su import link_app

	return link_app()


def may_cua_site():
	"""Tên máy của chính site: tên miền mặc định, Desk, app."""
	import frappe

	from vagabond import ten_mien

	may = {ten_mien.MIEN_APP, ten_mien.MIEN_DESK}
	for ham in (frappe.utils.get_url, goc_app):
		try:
			h = urlsplit(ham()).hostname
			if h:
				may.add(h.lower())
		except Exception:
			pass
	return may


def _ghi_loi():
	try:
		import frappe

		frappe.log_error("Chưa đổi được đường mở trong tin Zalo sang app; tin vẫn gửi với đường cũ.",
			"lien_ket_app: doi link loi")
	except Exception:
		pass


def doi_tin(chu):
	"""Đổi đường trong một tin đã soạn. Lỗi thì trả nguyên tin, không chặn gửi."""
	try:
		return doi_trong_chu(chu, goc_app(), may_cua_site())
	except Exception:
		_ghi_loi()
		return chu


def doi_mot_link(link):
	"""Đổi MỘT đường mở (tham số link của tin). Cả chuỗi là một đường, kể cả khi có
	dấu cách (vd "/app/query-report/Stock Balance"); không tách theo khoảng trắng."""
	try:
		return doi_link(link, goc_app(), may_cua_site())
	except Exception:
		_ghi_loi()
		return link


def link(duong):
	"""Đường màn app tuyệt đối, cho nơi phát tin tự chọn màn (vd "/xuat-huy")."""
	try:
		return goc_app().rstrip("/") + "/" + str(duong or "").lstrip("/")
	except Exception:
		return duong
