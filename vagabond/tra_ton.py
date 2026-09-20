# -*- coding: utf-8 -*-
"""Tra tồn kho trên app: một cửa, có phân loại, cảnh báo và chi tiết theo kho.

Anh Việt 20/09/2026 (ảnh màn Tra tồn kho): *"nút tra cứu tồn kho đang không
có chip lọc, trạng thái, ảnh món,... gì cả. Em code các phần thật hữu ích
cho nút này."*

Trước đây màn này đọc thẳng bảng Bin từ trình duyệt, chỉ có ô tìm. Nay máy
chủ trả về một lần đủ: loại hàng (bao bì, công cụ, nguyên liệu, bán thành
phẩm, thành phẩm) suy từ tiền tố mã, ảnh món, số lô cận hạn hay đã quá hạn
trong đúng kho đó, tồn âm, và bấm vào một mã thì thấy mã đó nằm ở kho nào
bao nhiêu, lô nào hết hạn ngày nào.

Phép THUẦN ở trên, phần chạm Frappe ở dưới, để kiểm thử được không cần site.
Giá trị tồn chỉ trả cho người có vai kho hoặc kế toán; nhân viên quầy chỉ
thấy số lượng.
"""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from vagabond.kho_san_xuat import TIEN_TO_BTP, TIEN_TO_THANH_PHAM

# Loại hàng trên màn tra tồn. Bao bì và công cụ tách khỏi nguyên liệu vì
# quầy hỏi "còn bao nhiêu túi" nhiều hơn hỏi "còn bao nhiêu bột".
LOAI = (
	("bao_bi", "Bao bì", "🛍️"),
	("ccdc", "Công cụ", "🧰"),
	("nguyen_lieu", "Nguyên liệu", "🥚"),
	("btp", "Bán thành phẩm", "🥣"),
	("thanh_pham", "Thành phẩm", "🎂"),
	("khac", "Khác", "📦"),
)
TEN_LOAI = {m: t for m, t, _ in LOAI}
ICON_LOAI = {m: i for m, _, i in LOAI}

TIEN_TO_LOAI = (
	(("BPKG",), "bao_bi"),
	(("CCDC", "VVPP"), "ccdc"),
	(("NVLT",), "nguyen_lieu"),
	(tuple(TIEN_TO_BTP), "btp"),
	(tuple(TIEN_TO_THANH_PHAM), "thanh_pham"),
)

# Lô còn hạn dưới ngần này ngày thì tính là cận hạn.
NGAY_CAN_HAN = 7

VAI_XEM_GIA_TRI = {"System Manager", "Stock Manager", "Accounts Manager", "Accounts User", "Giám đốc", "AP Giám đốc"}

SAP_XEP = {
	"ten": lambda r: (r.get("ten") or r.get("ma") or "").lower(),
	"nhieu": lambda r: -flt(r.get("ton")),
	"it": lambda r: flt(r.get("ton")),
}


def loai_cua_ma(ma):
	"""Loại hàng từ tiền tố mã. THUẦN. Không nhận ra thì "khac"."""
	m = (ma or "").strip().upper()
	for tien_to, loai in TIEN_TO_LOAI:
		if m.startswith(tien_to):
			return loai
	return "khac"


def trang_thai_lo(han, hom_nay, ngay_can=NGAY_CAN_HAN):
	"""Một lô là "qua_han", "can_han" hay "" (còn hạn xa). THUẦN.

	`han` None nghĩa là lô không có hạn: không cảnh báo gì.
	"""
	if not han:
		return ""
	h = getdate(han)
	t = getdate(hom_nay)
	if h < t:
		return "qua_han"
	if (h - t).days <= ngay_can:
		return "can_han"
	return ""


def dem_lo(lo_theo_ma, hom_nay, ngay_can=NGAY_CAN_HAN):
	"""{ma: [(han, so_luong), ...]} -> {ma: {"can_han": n, "qua_han": n}}. THUẦN.

	Chỉ đếm lô còn hàng (số lượng > 0). Lô hết hàng mà quá hạn không phải
	việc của màn tồn.
	"""
	ra = {}
	for ma, ds in (lo_theo_ma or {}).items():
		d = {"can_han": 0, "qua_han": 0}
		for han, sl in ds or []:
			if flt(sl) <= 0:
				continue
			tt = trang_thai_lo(han, hom_nay, ngay_can)
			if tt:
				d[tt] += 1
		ra[ma] = d
	return ra


def loc(rows, chip="", tim=""):
	"""Lọc theo chip và ô tìm. THUẦN.

	chip: "" tất cả, một mã LOAI, "can_han" (có lô cận hạn hoặc quá hạn),
	"am" (tồn âm), "het" (tồn 0 nhưng có trong danh sách vì có lô hay từng có).
	"""
	q = (tim or "").strip().lower()
	ra = []
	for r in rows or []:
		if chip in TEN_LOAI and r.get("loai") != chip:
			continue
		if chip == "can_han" and not (r.get("can_han") or r.get("qua_han")):
			continue
		if chip == "am" and flt(r.get("ton")) >= 0:
			continue
		if q and q not in ((r.get("ten") or "") + " " + (r.get("ma") or "")).lower():
			continue
		ra.append(r)
	return ra


def sap_xep(rows, sap="ten"):
	"""Sắp theo tên (mặc định), tồn nhiều trước, hoặc tồn ít trước. THUẦN."""
	return sorted(rows or [], key=SAP_XEP.get(sap) or SAP_XEP["ten"])


def dem_chip(rows):
	"""Số mã của từng chip, để chip nào cũng có số kể cả 0. THUẦN."""
	d = {"": len(rows or []), "can_han": 0, "am": 0}
	for m in TEN_LOAI:
		d[m] = 0
	for r in rows or []:
		d[r.get("loai") or "khac"] += 1
		if r.get("can_han") or r.get("qua_han"):
			d["can_han"] += 1
		if flt(r.get("ton")) < 0:
			d["am"] += 1
	return d


def cau_tom_tat(rows, gia_tri=None):
	"""Một câu trên đầu màn. THUẦN."""
	n = len(rows or [])
	dem = dem_chip(rows)
	phan = ["%d mã có tồn" % n]
	if dem["can_han"]:
		phan.append("⏰ %d mã có lô cận hạn hoặc quá hạn" % dem["can_han"])
	if dem["am"]:
		phan.append("⚠ %d mã tồn âm" % dem["am"])
	if gia_tri is not None:
		phan.append("giá trị %s đ" % "{:,.0f}".format(flt(gia_tri)).replace(",", "."))
	return " · ".join(phan)


# ---------------------------------------------------------------- chạm Frappe


def _xem_gia_tri():
	return bool(VAI_XEM_GIA_TRI & set(frappe.get_roles()))


def _lo_trong_kho(kho, ds_ma):
	"""{ma: [(han, sl)]} từ Batch còn hàng trong kho này."""
	if not ds_ma:
		return {}
	ra = {}
	lo = frappe.get_all(
		"Batch",
		filters={"item": ["in", ds_ma], "disabled": 0},
		fields=["name", "item", "expiry_date"],
		limit_page_length=0,
	)
	if not lo:
		return ra
	# Số lượng theo lô trong kho: đọc Stock Ledger Entry gộp, một câu cho
	# cả kho thay vì gọi get_batch_qty từng lô.
	sl = frappe.db.sql(
		"""select batch_no, sum(actual_qty) sl from `tabStock Ledger Entry`
		where warehouse=%s and is_cancelled=0 and batch_no in %s group by batch_no""",
		(kho, tuple(b["name"] for b in lo)),
		as_dict=True,
	)
	sl_lo = {x["batch_no"]: flt(x["sl"]) for x in sl}
	for b in lo:
		ra.setdefault(b["item"], []).append((b.get("expiry_date"), sl_lo.get(b["name"], 0)))
	return ra


@frappe.whitelist()
def ton_kho(kho=None, tim=None, chip=None, sap=None):
	"""Danh sách tồn của một kho, đã phân loại, kèm cảnh báo lô và ảnh món."""
	kho = (kho or "").strip()
	if not kho:
		frappe.throw("Chưa chọn kho.")
	if not frappe.db.exists("Warehouse", kho):
		frappe.throw("Không có kho %s." % kho)
	bins = frappe.get_all(
		"Bin",
		filters={"warehouse": kho, "actual_qty": ["!=", 0]},
		fields=["item_code", "actual_qty", "stock_uom", "stock_value"],
		limit_page_length=0,
	)
	ds_ma = [b["item_code"] for b in bins]
	mon = {}
	for i in range(0, len(ds_ma), 400):
		for it in frappe.get_all(
			"Item",
			filters={"name": ["in", ds_ma[i:i + 400]]},
			fields=["name", "item_name", "item_group", "image", "has_batch_no"],
			limit_page_length=0,
		):
			mon[it["name"]] = it
	hom_nay = nowdate()
	lo = dem_lo(_lo_trong_kho(kho, [m for m in ds_ma if (mon.get(m) or {}).get("has_batch_no")]), hom_nay)
	xem_gt = _xem_gia_tri()
	rows = []
	tong_gt = 0.0
	for b in bins:
		it = mon.get(b["item_code"]) or {}
		l = lo.get(b["item_code"]) or {}
		r = {
			"ma": b["item_code"],
			"ten": it.get("item_name") or b["item_code"],
			"nhom": it.get("item_group") or "",
			"anh": it.get("image") or "",
			"ton": flt(b["actual_qty"]),
			"dvt": b.get("stock_uom") or "",
			"loai": loai_cua_ma(b["item_code"]),
			"can_han": l.get("can_han", 0),
			"qua_han": l.get("qua_han", 0),
		}
		if xem_gt:
			r["gia_tri"] = flt(b.get("stock_value"))
			tong_gt += r["gia_tri"]
		rows.append(r)
	tat_ca = sap_xep(rows, sap or "ten")
	ds = loc(tat_ca, chip or "", tim or "")
	return {
		"kho": kho,
		"ds": ds[:300],
		"tong_dong": len(ds),
		"dem": dem_chip(tat_ca),
		"loai": [{"ma": m, "ten": t, "icon": i} for m, t, i in LOAI],
		"tom_tat": cau_tom_tat(tat_ca, tong_gt if xem_gt else None),
		"xem_gia_tri": 1 if xem_gt else 0,
		"ngay_can_han": NGAY_CAN_HAN,
	}


@frappe.whitelist()
def chi_tiet_ma(ma=None):
	"""Một mã nằm ở kho nào bao nhiêu, lô nào hết hạn ngày nào."""
	ma = (ma or "").strip()
	if not ma or not frappe.db.exists("Item", ma):
		frappe.throw("Không có mã %s." % ma)
	it = frappe.db.get_value("Item", ma, ["item_name", "item_group", "image", "stock_uom", "has_batch_no"], as_dict=True)
	kho = frappe.get_all(
		"Bin",
		filters={"item_code": ma, "actual_qty": ["!=", 0]},
		fields=["warehouse", "actual_qty"],
		order_by="actual_qty desc",
		limit_page_length=0,
	)
	lo = []
	if it.get("has_batch_no"):
		rows = frappe.db.sql(
			"""select sle.batch_no, sle.warehouse, sum(sle.actual_qty) sl, b.expiry_date
			from `tabStock Ledger Entry` sle left join `tabBatch` b on b.name = sle.batch_no
			where sle.item_code=%s and sle.is_cancelled=0 and ifnull(sle.batch_no,'')!=''
			group by sle.batch_no, sle.warehouse having sl > 0
			order by b.expiry_date asc""",
			(ma,),
			as_dict=True,
		)
		hom_nay = nowdate()
		for r in rows:
			lo.append({
				"lo": r["batch_no"], "kho": r["warehouse"], "sl": flt(r["sl"]),
				"han": str(r["expiry_date"] or ""), "tt": trang_thai_lo(r.get("expiry_date"), hom_nay),
			})
	return {
		"ma": ma,
		"ten": it.get("item_name") or ma,
		"nhom": it.get("item_group") or "",
		"anh": it.get("image") or "",
		"dvt": it.get("stock_uom") or "",
		"loai": loai_cua_ma(ma),
		"tong": sum(flt(k["actual_qty"]) for k in kho),
		"kho": [{"kho": k["warehouse"], "sl": flt(k["actual_qty"])} for k in kho],
		"lo": lo,
		"hom_nay": nowdate(),
		"cach_day": add_days(nowdate(), NGAY_CAN_HAN),
	}
