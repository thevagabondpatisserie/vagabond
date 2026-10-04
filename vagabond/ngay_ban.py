# -*- coding: utf-8 -*-
"""v573: một nguồn cho "bánh rời quầy ngày nào" (Dễ báo 04/10/2026).

VÌ SAO CÓ TỆP NÀY
-----------------
Dễ báo: tặng 1 Croissant, out bill bằng phương thức Hàng tặng, số bán hôm đó
đã trừ 1 cái. Sáng hôm sau anh Việt duyệt đơn tặng thì số bán lại trừ thêm 1
cái nữa. Một bill, trừ hai lần.

Gốc: duyệt hàng tặng (và OTP kế toán ghi sổ bill nháp ngày cũ) đều đi qua
`ban_hang._doi_ngay_ban_nhap`, đổi `posting_date` của bill sang ngày ghi sổ để
hoá đơn điện tử mang đúng ngày. Bảng Kiểm kho và bảng Kiểm bánh lại đếm số bán
theo `posting_date`. Ngày cũ thường đã chốt nên không đo lại, còn ngày mới thì
đếm thêm cái bánh đã rời quầy từ hôm trước.

CÁCH LÀM
--------
Bill đổi ngày lần đầu thì giữ lại ngày bán gốc ở ô `vgb_ngay_ban`. Mọi chỗ đếm
"đã bán trong ngày" đọc ngày bán gốc nếu có, không thì đọc `posting_date`.
Ngày ghi sổ và hoá đơn điện tử giữ nguyên như cũ, chỉ phép đếm bánh đổi.

Điều kiện SQL viết dạng "posting_date = ngày và chưa đổi ngày, hoặc ngày bán
gốc = ngày" thay vì coalesce, để còn dùng được chỉ mục posting_date.

Không sửa dữ liệu cũ: bill đã đổi ngày trước bản này không có ngày bán gốc,
giữ nguyên cách đếm cũ.
"""

TRUONG = "vgb_ngay_ban"

TRUONG_MOI = {
	"Sales Invoice": [
		dict(fieldname=TRUONG, label="Ngày bán tại quầy", fieldtype="Date",
			read_only=1, no_copy=1, insert_after="posting_date",
			depends_on="eval:doc.vgb_ngay_ban",
			description="Ngày bill được bán ra, giữ lại khi hoá đơn đổi sang ngày ghi sổ "
				"(duyệt hàng tặng, kế toán ghi sổ bill ngày cũ). Bảng Kiểm kho và Kiểm bánh "
				"đếm bánh theo ngày này."),
	],
}


# ------------------------------------------------------------ phần thuần

def _chuoi_ngay(v):
	return str(v or "").strip()[:10]


def ngay_ban_khi_doi(ngay_ban_cu, posting_cu):
	"""Giá trị ô ngày bán gốc khi bill nháp đổi ngày. THUẦN.

	Đã có thì giữ (đổi ngày hai lần vẫn nhớ ngày bán đầu tiên), chưa có thì
	lấy posting_date trước khi đổi."""
	return _chuoi_ngay(ngay_ban_cu) or _chuoi_ngay(posting_cu) or None


def ngay_dem(r):
	"""Bill tính vào số bán của ngày nào. THUẦN. r có posting_date, vgb_ngay_ban."""
	return _chuoi_ngay(r.get(TRUONG)) or _chuoi_ngay(r.get("posting_date"))


def thuoc_ngay(r, ngay):
	"""Bill có tính vào số bán ngày `ngay` không. THUẦN, cùng nghĩa với dk_sql."""
	return ngay_dem(r) == _chuoi_ngay(ngay)


def dk_sql(bi_danh="si", ten_tham_so="ngay"):
	"""Điều kiện SQL cùng nghĩa với thuoc_ngay, cho mọi chỗ đếm số bán.

	Dùng %(ten)s nên câu gọi phải truyền tham số dạng dict."""
	a = bi_danh
	p = "%%(%s)s" % ten_tham_so
	return ("((%s.posting_date = %s and ifnull(%s.%s, '') = '') or %s.%s = %s)"
		% (a, p, a, TRUONG, a, TRUONG, p))


def gia_tri_giu(gia_tri_cu, gia_tri_moi, may_ghi):
	"""Giá trị ô ngày bán được phép lưu. THUẦN.

	Codex #438: read_only chỉ khoá giao diện, Desk hay API vẫn gửi được giá trị
	vào ô. Ô này quyết định bánh trừ vào ngày nào, nên chỉ máy được ghi (qua
	ghi_khi_doi). Mọi giá trị khác bị bỏ, giữ đúng giá trị đang lưu (bill mới
	thì rỗng)."""
	if may_ghi:
		return _chuoi_ngay(gia_tri_moi) or None
	return _chuoi_ngay(gia_tri_cu) or None


def cac_ngay_phai_do(ngay_cu, ngay_moi, ngay_ban):
	"""Bill đổi ngày thì đo lại những ngày nào. THUẦN. Bỏ rỗng, bỏ trùng."""
	ra = []
	for n in (ngay_cu, ngay_moi, ngay_ban):
		n = _chuoi_ngay(n)
		if n and n not in ra:
			ra.append(n)
	return ra


# ------------------------------------------------------------ phần chạm hệ

CO_MAY_GHI = "vgb_may_ghi_ngay_ban"


def chan_ghi_tay(doc, method=None):
	"""Hook validate của Sales Invoice: chỉ máy được đặt ô ngày bán (Codex #438).

	Không chặn lưu, không báo lỗi: giá trị gửi từ ngoài bị trả về giá trị đang
	lưu trong cơ sở dữ liệu (bill mới thì rỗng)."""
	try:
		if not doc.meta.has_field(TRUONG):
			return
	except Exception:
		return
	may_ghi = bool(doc.flags.get(CO_MAY_GHI))
	cu = None
	if not may_ghi and not doc.is_new():
		import frappe
		cu = frappe.db.get_value(doc.doctype, doc.name, TRUONG)
	doc.set(TRUONG, gia_tri_giu(cu, doc.get(TRUONG), may_ghi))


def ghi_khi_doi(si):
	"""Gọi NGAY TRƯỚC khi đổi posting_date của bill nháp. Không lưu, người gọi lưu."""
	try:
		if not si.meta.has_field(TRUONG):
			return
	except Exception:
		return
	import frappe
	# Đọc ngày gốc đang LƯU, không tin giá trị trên đối tượng (có thể bị gửi
	# kèm từ ngoài trước khi tới đây).
	cu = None if si.is_new() else frappe.db.get_value(si.doctype, si.name, TRUONG)
	si.set(TRUONG, ngay_ban_khi_doi(cu, si.get("posting_date")))
	si.flags[CO_MAY_GHI] = True
