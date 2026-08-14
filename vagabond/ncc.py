# -*- coding: utf-8 -*-
"""Danh mục nhà cung cấp và việc gán nhà cung cấp cho mặt hàng.

Uyên hỏi 14/08/2026: *"có mấy mặt hàng chưa gán NCC, em gán NCC ở mục nào?"*.

Đo thật trước khi làm: 515 nhà cung cấp, 1.451 mặt hàng mua, mà chỉ **3 món**
có gán nhà cung cấp. Nghĩa là câu hỏi thật không phải "bấm ở đâu" mà là
"1.448 món kia làm sao gán cho xuể". Chỉ đường bấm rồi để Uyên ngồi gõ tay
1.448 lần thì đó không phải câu trả lời.

Nên phân hệ này xoay quanh MỘT ý: **máy đã biết sẵn ai bán gì**. Mỗi đơn mua
hàng và mỗi hoá đơn mua đều ghi rõ mua món nào của ai. Quét lịch sử đó ra là
có ngay danh sách gợi ý, Uyên chỉ việc soát và bấm gán hàng loạt. Món nào
chưa từng mua thì mới phải gõ tay, và số đó ít hơn nhiều.

Bảng ERPNext dùng để gán là `Item Supplier` (bảng con của Item). Một món gán
được nhiều nhà cung cấp; nhà đứng đầu bảng là nhà mặc định khi lập đơn mua.
"""

import base64
import io

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

# Ai duoc dung phan he nay. Khop voi QUYEN_MUA ben mua_hang.py: gia mua va
# nha cung cap la thong tin nhay cam, khong mo cho ca tiem.
QUYEN_NCC = {
	"System Manager", "Accounts Manager", "Accounts User",
	"Purchase User", "Purchase Manager", "Vagabond Giam doc",
}


def _kiem(viec):
	if not (QUYEN_NCC & set(frappe.get_roles())):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _tien(v):
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return str(v)


# --------------------------------------------------------- danh sách nhà cung cấp


@frappe.whitelist()
def danh_sach(tu_khoa="", nhom=None, chip=None, so_ngay=180):
	"""Danh mục nhà cung cấp kèm số liệu đủ để lọc bằng chip.

	Ba con số bám theo mỗi nhà: bao nhiêu mặt hàng đã gán cho họ, còn nợ bao
	nhiêu, và lần mua gần nhất là khi nào. Có ba con số đó thì chip lọc mới
	nói được điều gì có ích, chứ danh sách 515 cái tên xếp theo bảng chữ cái
	thì cuộn mỏi tay cũng không tìm ra ai.
	"""
	_kiem("xem danh mục nhà cung cấp")
	loc = {}
	if nhom:
		loc["supplier_group"] = nhom
	ds = frappe.get_all(
		"Supplier",
		filters=loc,
		fields=[
			"name", "supplier_name", "supplier_group", "disabled",
			"email_id", "mobile_no", "tax_id",
			"custom_ma_ncc", "custom_ma_ipos", "custom_dien_thoai_ipos",
			"kenh_dat_hang_mac_dinh", "khong_chiu_thue_gtgt",
		],
		order_by="supplier_name asc",
		limit_page_length=0,
	)

	# Ba phep dem gom MOT lan cho ca danh sach, khong hoi trong vong lap:
	# 515 nha ma hoi tung cai la 1.545 luot hoi co so du lieu.
	so_mon = {}
	for r in frappe.get_all(
		"Item Supplier", fields=["supplier"], limit_page_length=0
	):
		so_mon[r.supplier] = so_mon.get(r.supplier, 0) + 1

	con_no, mua_cuoi = {}, {}
	for r in frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 1},
		fields=["supplier", "outstanding_amount", "posting_date"],
		limit_page_length=0,
	):
		if flt(r.outstanding_amount) > 0:
			con_no[r.supplier] = con_no.get(r.supplier, 0) + flt(r.outstanding_amount)
		d = str(r.posting_date or "")
		if d and d > mua_cuoi.get(r.supplier, ""):
			mua_cuoi[r.supplier] = d

	moc = str(add_days(nowdate(), -int(so_ngay or 180)))
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		o = dict(r)
		o["so_mon"] = so_mon.get(r.name, 0)
		o["con_no"] = con_no.get(r.name, 0.0)
		o["mua_cuoi"] = mua_cuoi.get(r.name, "")
		o["dang_mua"] = 1 if o["mua_cuoi"] and o["mua_cuoi"] >= moc else 0
		o["sdt"] = (r.mobile_no or r.custom_dien_thoai_ipos or "").strip()
		if q:
			kho = " ".join([
				r.name or "", r.supplier_name or "", r.tax_id or "",
				r.custom_ma_ncc or "", r.custom_ma_ipos or "", o["sdt"],
			]).lower()
			if q not in kho:
				continue
		ra.append(o)

	CHIP = {
		"dang_mua": lambda x: x["dang_mua"],
		"con_no": lambda x: x["con_no"] > 0,
		"chua_gan_mon": lambda x: x["so_mon"] == 0,
		"thieu_ho_so": lambda x: not (x.get("tax_id") or "").strip() or not (x.get("email_id") or "").strip(),
		"da_tat": lambda x: cint(x.get("disabled")),
	}
	dem = {k: len([x for x in ra if f(x)]) for k, f in CHIP.items()}
	loc_ra = [x for x in ra if CHIP[chip](x)] if chip in CHIP else ra

	return {
		"rows": loc_ra,
		"tat_ca": len(ra),
		"dem": dem,
		"tong_con_no": sum(x["con_no"] for x in loc_ra),
		"nhom": sorted({x["supplier_group"] for x in ra if x.get("supplier_group")}),
		"quyen": 1,
	}


@frappe.whitelist()
def chi_tiet(ncc):
	"""Một nhà cung cấp: hồ sơ, mặt hàng đã gán, và mặt hàng từng mua."""
	_kiem("xem nhà cung cấp")
	doc = frappe.get_doc("Supplier", ncc)

	da_gan = frappe.get_all(
		"Item Supplier",
		filters={"supplier": ncc},
		fields=["parent", "supplier_part_no"],
		limit_page_length=0,
	)
	ten_mon = {}
	if da_gan:
		for r in frappe.get_all(
			"Item",
			filters={"name": ["in", [x.parent for x in da_gan]]},
			fields=["name", "item_name", "stock_uom", "disabled"],
			limit_page_length=0,
		):
			ten_mon[r.name] = r
	mon_gan = [{
		"ma": x.parent,
		"ten": (ten_mon.get(x.parent) or {}).get("item_name") or x.parent,
		"dvt": (ten_mon.get(x.parent) or {}).get("stock_uom") or "",
		"ma_ncc": x.supplier_part_no or "",
		"tat": cint((ten_mon.get(x.parent) or {}).get("disabled")),
	} for x in da_gan]

	# Mua that: quet hoa don mua da ghi so. Bay ca gia gan nhat de nguoi xem
	# biet lan cuoi mua bao nhieu, khoi phai mo hoa don ra tra.
	lich_su = {}
	for r in frappe.db.sql(
		"""select it.item_code, it.item_name, it.rate, pi.posting_date, pi.name as hoa_don
		from `tabPurchase Invoice Item` it
		inner join `tabPurchase Invoice` pi on pi.name = it.parent
		where pi.supplier = %s and pi.docstatus = 1
		order by pi.posting_date asc""",
		(ncc,), as_dict=True,
	):
		lich_su[r.item_code] = {
			"ma": r.item_code, "ten": r.item_name or r.item_code,
			"gia": flt(r.rate), "ngay": str(r.posting_date or ""),
			"hoa_don": r.hoa_don,
			"so_lan": (lich_su.get(r.item_code) or {}).get("so_lan", 0) + 1,
		}
	da = {x["ma"] for x in mon_gan}
	tung_mua = sorted(
		[v for k, v in lich_su.items() if k not in da],
		key=lambda x: (-x["so_lan"], x["ten"]),
	)

	return {
		"ncc": {
			"ma": doc.name, "ten": doc.supplier_name or doc.name,
			"nhom": doc.supplier_group or "", "tat": cint(doc.disabled),
			"mst": doc.tax_id or "", "email": doc.email_id or "",
			"sdt": (doc.mobile_no or doc.get("custom_dien_thoai_ipos") or "").strip(),
			"dia_chi": (doc.get("custom_dia_chi_ipos") or "").strip(),
			"ma_ncc": doc.get("custom_ma_ncc") or "",
			"ma_ipos": doc.get("custom_ma_ipos") or "",
			"kenh": doc.get("kenh_dat_hang_mac_dinh") or "",
			"khong_vat": cint(doc.get("khong_chiu_thue_gtgt")),
		},
		"mon_gan": mon_gan,
		"tung_mua": tung_mua,
		"so_mon_gan": len(mon_gan),
		"so_tung_mua": len(tung_mua),
	}


# ------------------------------------------------- gán nhà cung cấp cho mặt hàng


def _ncc_tu_lich_su(ma_mon=None):
	"""Món nào đã từng mua của ai, mấy lần, giá gần nhất.

	Quét cả đơn mua hàng lẫn hoá đơn mua: có món đặt đơn rồi mà chưa về hoá
	đơn, bỏ qua đơn mua hàng là mất đúng những món đang mua dở.
	"""
	loc, tham = "", []
	if ma_mon:
		loc = " and it.item_code in %s"
		tham = [tuple(ma_mon)] if len(ma_mon) > 1 else [(ma_mon[0], ma_mon[0])]

	gom = {}

	def _nap(rows, nguon):
		for r in rows:
			k = (r["item_code"], r["supplier"])
			o = gom.setdefault(k, {
				"mon": r["item_code"], "ncc": r["supplier"],
				"so_lan": 0, "gia": 0.0, "ngay": "", "nguon": nguon,
			})
			o["so_lan"] += 1
			d = str(r.get("posting_date") or "")
			if d >= o["ngay"]:
				o["ngay"] = d
				o["gia"] = flt(r.get("rate"))

	_nap(frappe.db.sql(
		"""select it.item_code, pi.supplier, it.rate, pi.posting_date
		from `tabPurchase Invoice Item` it
		inner join `tabPurchase Invoice` pi on pi.name = it.parent
		where pi.docstatus = 1""" + loc, tham, as_dict=True), "hoá đơn mua")
	_nap(frappe.db.sql(
		"""select it.item_code, po.supplier, it.rate, po.transaction_date as posting_date
		from `tabPurchase Order Item` it
		inner join `tabPurchase Order` po on po.name = it.parent
		where po.docstatus = 1""" + loc, tham, as_dict=True), "đơn mua hàng")

	# Mot mon co the mua cua nhieu nha. Xep nha mua nhieu lan nhat len truoc,
	# cung so lan thi lay nha mua gan day hon - do la nha dang dung.
	theo_mon = {}
	for o in gom.values():
		theo_mon.setdefault(o["mon"], []).append(o)
	for m in theo_mon:
		theo_mon[m].sort(key=lambda x: (x["so_lan"], x["ngay"]), reverse=True)
	return theo_mon


@frappe.whitelist()
def mon_chua_gan(tu_khoa="", chi_co_goi_y=0, gioi_han=300):
	"""Mặt hàng mua chưa gán nhà cung cấp nào, kèm gợi ý từ lịch sử mua.

	Đây là màn trả lời thẳng câu hỏi của Uyên. Món nào máy đã thấy trong đơn
	mua hay hoá đơn thì bày sẵn tên nhà cung cấp kèm số lần mua và giá gần
	nhất, tick một cái là gán xong.
	"""
	_kiem("gán nhà cung cấp cho mặt hàng")
	da_gan = {r.parent for r in frappe.get_all("Item Supplier", fields=["parent"], limit_page_length=0)}

	loc = {"is_purchase_item": 1, "disabled": 0}
	q = (tu_khoa or "").strip()
	if q:
		loc["item_name"] = ["like", "%" + q + "%"]
	ds = frappe.get_all(
		"Item",
		filters=loc,
		fields=["name", "item_name", "stock_uom", "item_group"],
		order_by="item_name asc",
		limit_page_length=0,
	)
	chua = [r for r in ds if r.name not in da_gan]

	goi_y = _ncc_tu_lich_su([r.name for r in chua]) if chua else {}
	ten_ncc = {}
	can = {o["ncc"] for v in goi_y.values() for o in v}
	if can:
		for r in frappe.get_all(
			"Supplier", filters={"name": ["in", list(can)]},
			fields=["name", "supplier_name"], limit_page_length=0,
		):
			ten_ncc[r.name] = r.supplier_name or r.name

	ra = []
	for r in chua:
		gy = goi_y.get(r.name) or []
		ra.append({
			"ma": r.name, "ten": r.item_name or r.name,
			"dvt": r.stock_uom or "", "nhom": r.item_group or "",
			"goi_y": [{
				"ncc": g["ncc"], "ten_ncc": ten_ncc.get(g["ncc"], g["ncc"]),
				"so_lan": g["so_lan"], "gia": g["gia"], "ngay": g["ngay"],
				"nguon": g["nguon"],
			} for g in gy[:3]],
		})
	if cint(chi_co_goi_y):
		ra = [x for x in ra if x["goi_y"]]

	co_gy = len([x for x in ra if x["goi_y"]])
	return {
		"rows": ra[: int(gioi_han or 300)],
		"tong_chua_gan": len(chua),
		"co_goi_y": co_gy,
		"khong_goi_y": len(ra) - co_gy,
		"da_cat_bot": max(0, len(ra) - int(gioi_han or 300)),
	}


@frappe.whitelist()
def gan(mon, ncc, ma_ncc=None):
	"""Gán một nhà cung cấp cho một mặt hàng."""
	_kiem("gán nhà cung cấp cho mặt hàng")
	if not frappe.db.exists("Item", mon):
		frappe.throw("Không có mặt hàng %s." % mon)
	if not frappe.db.exists("Supplier", ncc):
		frappe.throw("Không có nhà cung cấp %s." % ncc)
	doc = frappe.get_doc("Item", mon)
	for d in doc.get("supplier_items") or []:
		if d.supplier == ncc:
			return {"ok": 1, "da_co_roi": 1, "mon": mon, "ncc": ncc}
	doc.append("supplier_items", {"supplier": ncc, "supplier_part_no": (ma_ncc or "").strip()})
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "mon": mon, "ncc": ncc, "so_ncc": len(doc.get("supplier_items") or [])}


@frappe.whitelist()
def gan_hang_loat(cap=None):
	"""Gán nhiều cặp mặt hàng và nhà cung cấp trong một lượt.

	cap: danh sách {"mon": ..., "ncc": ...}.

	Một cặp hỏng thì ghi lại rồi đi tiếp, không dừng cả lượt: Uyên tick 200
	món mà một món trục trặc làm hỏng cả mẻ thì lần sau không ai dám bấm.
	"""
	_kiem("gán nhà cung cấp cho mặt hàng")
	if isinstance(cap, str):
		cap = frappe.parse_json(cap)
	if not cap:
		frappe.throw("Chưa chọn cặp mặt hàng và nhà cung cấp nào.")
	xong, bo_qua, loi = 0, 0, []
	for x in cap:
		mon = (x.get("mon") or "").strip()
		ncc = (x.get("ncc") or "").strip()
		if not (mon and ncc):
			continue
		try:
			kq = gan(mon, ncc, x.get("ma_ncc"))
			if kq.get("da_co_roi"):
				bo_qua += 1
			else:
				xong += 1
		except Exception as e:
			loi.append("%s: %s" % (mon, str(e)[:120]))
			frappe.db.rollback()
	frappe.db.commit()
	return {"ok": 1, "da_gan": xong, "bo_qua": bo_qua, "so_loi": len(loi), "loi": loi[:10]}


@frappe.whitelist()
def bo_gan(mon, ncc):
	"""Gỡ một nhà cung cấp khỏi mặt hàng, khi gán nhầm."""
	_kiem("gán nhà cung cấp cho mặt hàng")
	doc = frappe.get_doc("Item", mon)
	con = [d for d in (doc.get("supplier_items") or []) if d.supplier != ncc]
	if len(con) == len(doc.get("supplier_items") or []):
		return {"ok": 1, "khong_co": 1}
	doc.set("supplier_items", [])
	for d in con:
		doc.append("supplier_items", {"supplier": d.supplier, "supplier_part_no": d.supplier_part_no})
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "con_lai": len(con)}


# --------------------------------------------------------------------- Excel


@frappe.whitelist()
def xuat_excel(tu_khoa="", nhom=None, chip=None):
	"""Danh mục nhà cung cấp ra Excel cho chị Dung theo dõi."""
	_kiem("xuất danh mục nhà cung cấp")
	kq = danh_sach(tu_khoa=tu_khoa, nhom=nhom, chip=chip)
	rows = kq["rows"]
	bang = [
		["DANH MỤC NHÀ CUNG CẤP"],
		["Số nhà cung cấp", len(rows), "Tổng còn nợ", kq["tong_con_no"]],
		[],
		["Mã", "Tên nhà cung cấp", "Nhóm", "Mã số thuế", "Điện thoại", "Email",
		 "Mã NCC nội bộ", "Mã iPOS", "Kênh đặt hàng", "Không chịu VAT",
		 "Số mặt hàng đã gán", "Còn nợ", "Mua gần nhất", "Trạng thái"],
	]
	for r in rows:
		bang.append([
			r["name"], r["supplier_name"] or "", r.get("supplier_group") or "",
			r.get("tax_id") or "", r.get("sdt") or "", r.get("email_id") or "",
			r.get("custom_ma_ncc") or "", r.get("custom_ma_ipos") or "",
			r.get("kenh_dat_hang_mac_dinh") or "",
			"Có" if cint(r.get("khong_chiu_thue_gtgt")) else "",
			r["so_mon"], flt(r["con_no"]), r["mua_cuoi"] or "",
			"Đã tắt" if cint(r.get("disabled")) else "Đang dùng",
		])
	bang.append([])
	bang.append(["TỔNG", "", "", "", "", "", "", "", "", "", "", kq["tong_con_no"]])

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Nha cung cap")
	noi = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {
		"ten_file": "danh-muc-ncc-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi).decode(),
	}
