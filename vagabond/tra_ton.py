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


def xep_lo(lo):
	"""Lô có hạn xếp trước theo hạn gần nhất, lô không hạn xếp sau. THUẦN.

	MariaDB xếp NULL lên đầu khi order by asc, nên lô không HSD đè lên lô
	sắp hết hạn (Codex #350). Xếp ở Python cho rõ luật.
	"""
	return sorted(lo or [], key=lambda x: (0 if x.get("han") else 1, x.get("han") or "", x.get("lo") or ""))


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


def gop_so_lo(dong_so, dong_goi):
	"""Cộng số theo (lô, kho) từ hai đường của sổ kho. THUẦN.

	ERPNext v16 để trống cột batch_no của Stock Ledger Entry và cất số lô
	trong gói Serial and Batch Bundle (số đã mang dấu); bản cũ ghi thẳng
	batch_no. lo_hang.py đã cộng cả hai đường từ 03/09; màn tra tồn cũng
	phải vậy, không thì lô nào đi qua gói bị đếm 0 và mất cảnh báo HSD
	(Codex #350).

	dong_so: [(batch_no, warehouse, actual_qty, bundle)] từ SLE.
	dong_goi: {bundle: [(batch_no, qty)]} từ Serial and Batch Entry.
	Trả {(lô, kho): số}.
	"""
	ra = {}
	for lo, kho, sl, goi in dong_so or []:
		if lo:
			ra[(lo, kho)] = flt(ra.get((lo, kho), 0)) + flt(sl)
		elif goi:
			for lo2, sl2 in (dong_goi or {}).get(goi) or []:
				if lo2:
					ra[(lo2, kho)] = flt(ra.get((lo2, kho), 0)) + flt(sl2)
	return ra


def _so_lo(loc_sle):
	"""{(lô, kho): số} đọc thật từ sổ kho theo bộ lọc SLE, cộng cả hai đường."""
	dong = frappe.get_all(
		"Stock Ledger Entry",
		filters=dict(loc_sle, is_cancelled=0),
		fields=["batch_no", "warehouse", "actual_qty", "serial_and_batch_bundle"],
		limit_page_length=0,
	)
	goi = sorted({d["serial_and_batch_bundle"] for d in dong if not d.get("batch_no") and d.get("serial_and_batch_bundle")})
	dong_goi = {}
	if goi:
		for e in frappe.get_all(
			"Serial and Batch Entry",
			filters={"parenttype": "Serial and Batch Bundle", "parent": ["in", goi]},
			fields=["parent", "batch_no", "qty"],
			limit_page_length=0,
		):
			dong_goi.setdefault(e["parent"], []).append((e.get("batch_no"), e.get("qty")))
	return gop_so_lo(
		[(d.get("batch_no"), d.get("warehouse"), d.get("actual_qty"), d.get("serial_and_batch_bundle")) for d in dong],
		dong_goi,
	)


def _lo_trong_kho(kho, ds_ma):
	"""{ma: [(han, sl)]} từ lô còn hàng trong kho này, đọc cả gói lẫn cột lô."""
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
	so = _so_lo({"warehouse": kho, "item_code": ["in", ds_ma]})
	for b in lo:
		ra.setdefault(b["item"], []).append((b.get("expiry_date"), so.get((b["name"], kho), 0)))
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
	dang_loc = bool((chip or "").strip() or (tim or "").strip())
	# Codex #350: dang loc thi cau tom tat phai noi ve DUNG pham vi dang hien,
	# khong lay so ca kho gan len tren mot danh sach da loc.
	gt_loc = sum(flt(r.get("gia_tri")) for r in ds) if xem_gt else None
	return {
		"kho": kho,
		"ds": ds[:300],
		"tong_dong": len(ds),
		"dem": dem_chip(tat_ca),
		"loai": [{"ma": m, "ten": t, "icon": i} for m, t, i in LOAI],
		"tom_tat": ("Theo bộ lọc: " if dang_loc else "") + cau_tom_tat(ds, gt_loc),
		"tom_tat_kho": cau_tom_tat(tat_ca, tong_gt if xem_gt else None),
		"dang_loc": 1 if dang_loc else 0,
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
		so = _so_lo({"item_code": ma})
		han = {b["name"]: b.get("expiry_date") for b in frappe.get_all(
			"Batch", filters={"item": ma}, fields=["name", "expiry_date"], limit_page_length=0)}
		hom_nay = nowdate()
		for (ten_lo, kho_lo), sl in so.items():
			if flt(sl) <= 0:
				continue
			lo.append({
				"lo": ten_lo, "kho": kho_lo, "sl": flt(sl),
				"han": str(han.get(ten_lo) or ""), "tt": trang_thai_lo(han.get(ten_lo), hom_nay),
			})
		lo = xep_lo(lo)
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
