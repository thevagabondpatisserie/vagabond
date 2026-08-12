# -*- coding: utf-8 -*-
"""Doi chieu hoa don mua voi phieu nhap kho (Uyen 12/08/2026).

Uyen hoi: "em noi Hoa don NCC Hoang Le 5605, khop PNK va tien, em bam luu,
nhung cho trang thai hoa don khong thay doi ạ?"

Cau tra loi la con thieu buoc GUI (submit). Nhung cau hoi that nam duoi:
tren man Desk cua ERPNext, "noi phieu" va "ghi so" la hai nut o hai cho
khac nhau, va giua chung khong co gi noi cho nguoi lam biet minh dang o
buoc nao. Uyen lam dung het, chi khong biet la con mot nut nua.

Man nay gop lai thanh MOT duong thang:

  Cho doi chieu  ->  may tu tim phieu nhap khop  ->  hien chenh lech
                 ->  mot nut "Khop va ghi so" lam ca hai viec

Nhung cai KHONG lam, co y:
- Khong tu dong ghi so hang loat. Ghi so hoa don mua la ghi cong no va ghi
  gia von; sai mot to la sai ca ky.
- Khong noi phieu khi so luong hoac ma hang khong khop. Bao ra man hinh de
  nguoi ta xu ly, con hon noi bua roi thang ton kho lech ma khong ai biet.
"""

import frappe
from frappe.utils import cint, flt, getdate, nowdate, add_days

QUYEN = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Purchase Manager",
	"Purchase User",
	"Stock Manager",
}

# Lech duoi muc nay coi nhu khop: chenh vai dong tien la do lam tron thue
# hoac phi van chuyen, khong dang chan nguoi ta lai.
NGUONG_LECH = 1000.0

TRAN_DONG = 200

NHOM = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "cho_doi_chieu", "ten": "Chờ đối chiếu", "ic": "🔍"},
	{"k": "lech", "ten": "Lệch tiền", "ic": "⚠️"},
	{"k": "cho_ghi_so", "ten": "Chờ ghi sổ", "ic": "📒"},
	{"k": "khong_thay", "ten": "Không thấy phiếu nhập", "ic": "❓"},
	{"k": "xong", "ten": "Xong", "ic": "✅"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "🚫"},
]


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Màn đối chiếu hoá đơn mua chỉ dành cho kế toán, thu mua và quản lý kho.")


def _lam_duoc():
	return bool(
		{"System Manager", "Accounts Manager", "Accounts User", "Purchase Manager"}
		& set(frappe.get_roles())
	)


# ------------------------------------------------------------- tim phieu nhap


def _pnk_con_lai(ncc, ngay, so_ngay=60):
	"""Phieu nhap mua da ghi so cua NCC do ma CHUA duoc hoa don nao lay het."""
	ngay = getdate(ngay or nowdate())
	rows = frappe.get_all(
		"Purchase Receipt",
		filters={
			"supplier": ncc,
			"docstatus": 1,
			"posting_date": ["between", [str(add_days(ngay, -so_ngay)), str(add_days(ngay, so_ngay))]],
		},
		fields=["name", "posting_date", "grand_total", "total", "per_billed", "supplier_name"],
		order_by="posting_date desc",
		limit_page_length=0,
	)
	return [r for r in rows if flt(r.get("per_billed")) < 99.99]


def _dong_pnk(ten_pnk):
	return frappe.get_all(
		"Purchase Receipt Item",
		filters={"parent": ten_pnk, "docstatus": 1},
		fields=["name", "item_code", "item_name", "qty", "rate", "amount", "billed_amt", "uom"],
		order_by="idx asc",
		limit_page_length=0,
	)


def _dong_hd(name):
	return frappe.get_all(
		"Purchase Invoice Item",
		filters={"parent": name},
		fields=[
			"name", "idx", "item_code", "item_name", "qty", "rate", "amount",
			"uom", "purchase_receipt", "pr_detail",
		],
		order_by="idx asc",
		limit_page_length=0,
	)


def _goi_y(hd, dong):
	"""Chon cac phieu nhap co kha nang la cua hoa don nay.

	Cham diem bang so ma hang trung nhau chu khong bang tien: nha cung cap
	hay gop hai lan giao vao mot hoa don, luc do khong phieu nao khop tien
	ca ma van dung phieu.
	"""
	ma_hd = {}
	for r in dong:
		ma_hd[r["item_code"]] = ma_hd.get(r["item_code"], 0) + flt(r["qty"])
	ra = []
	for p in _pnk_con_lai(hd.get("supplier"), hd.get("posting_date")):
		dp = _dong_pnk(p["name"])
		trung = 0
		for r in dp:
			if r["item_code"] in ma_hd:
				trung += 1
		if not trung:
			continue
		ra.append(
			{
				"name": p["name"],
				"ngay": str(p.get("posting_date") or ""),
				"tien": flt(p.get("total")),
				"tong": flt(p.get("grand_total")),
				"da_hoa_don": flt(p.get("per_billed")),
				"so_mon": len(dp),
				"so_mon_trung": trung,
				"dong": dp,
			}
		)
	ra.sort(key=lambda x: (-x["so_mon_trung"], x["ngay"]))
	return ra


def _da_noi(dong):
	"""Bao nhieu dong hoa don da tro toi mot phieu nhap."""
	return len([r for r in dong if (r.get("purchase_receipt") or "").strip()])


def _nhom_cua(hd, dong, co_goi_y):
	if cint(hd.get("vgb_huy")) or hd.get("docstatus") == 2:
		return "huy"
	if hd.get("docstatus") == 1:
		return "xong"
	noi = _da_noi(dong)
	if noi and noi == len(dong):
		return "cho_ghi_so"
	if not co_goi_y:
		return "khong_thay"
	return "cho_doi_chieu"


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach(so_ngay=60, nhom=None, tu_khoa=""):
	"""Danh sach hoa don mua kem trang thai doi chieu."""
	_kiem_quyen()
	den = getdate(nowdate())
	tu = add_days(den, -max(1, cint(so_ngay) or 60))
	ds = frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": ["<", 2], "posting_date": ["between", [str(tu), str(den)]]},
		fields=[
			"name", "posting_date", "supplier", "supplier_name", "grand_total",
			"total", "docstatus", "bill_no", "bill_date", "update_stock",
			"outstanding_amount", "vgb_huy",
		],
		order_by="posting_date desc, name desc",
		limit_page_length=0,
	)
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		if q and q not in ((r.name or "") + " " + (r.supplier_name or "") + " " + (r.bill_no or "")).lower():
			continue
		o = dict(r)
		if r.get("docstatus") == 1:
			o["nhom"] = "huy" if cint(r.get("vgb_huy")) else "xong"
			o["so_dong"] = 0
			o["da_noi"] = 0
			o["so_phieu_goi_y"] = 0
			ra.append(o)
			continue
		dong = _dong_hd(r["name"])
		gy = _goi_y(r, dong)
		o["so_dong"] = len(dong)
		o["da_noi"] = _da_noi(dong)
		o["so_phieu_goi_y"] = len(gy)
		o["nhom"] = _nhom_cua(r, dong, bool(gy))
		if o["nhom"] in ("cho_doi_chieu", "cho_ghi_so") and gy:
			# Lech tien tinh tren PHUONG AN MAY DE XUAT, tuc phieu diem cao
			# nhat. Chi de bay chip canh bao tu xa, con so that thi man chi
			# tiet tinh lai theo dung phieu nguoi dung chon.
			tien_pnk = sum(flt(p["tien"]) for p in gy[:1])
			if abs(tien_pnk - flt(r.get("total"))) > NGUONG_LECH:
				o["nhom"] = "lech"
				o["lech"] = flt(r.get("total")) - tien_pnk
		ra.append(o)

	dem = {"": len(ra)}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	chon = (nhom or "").strip()
	loc = [o for o in ra if o["nhom"] == chon] if chon else ra
	return {
		"hd": loc[:TRAN_DONG],
		"tong_dong": len(loc),
		"bi_cat": max(0, len(loc) - TRAN_DONG),
		"dem": dem,
		"nhom": NHOM,
		"lam_duoc": 1 if _lam_duoc() else 0,
		"tu": str(tu),
		"den": str(den),
	}


@frappe.whitelist()
def xem(name):
	"""Mot hoa don: dong hang, phieu nhap goi y, va chenh lech tung mon."""
	_kiem_quyen()
	hd = frappe.db.get_value(
		"Purchase Invoice",
		name,
		[
			"name", "posting_date", "supplier", "supplier_name", "grand_total",
			"total", "docstatus", "bill_no", "bill_date", "update_stock",
			"outstanding_amount", "vgb_huy", "due_date",
		],
		as_dict=True,
	)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % name)
	dong = _dong_hd(name)
	gy = _goi_y(hd, dong) if hd.get("docstatus") == 0 else []
	return {
		"hd": hd,
		"dong": dong,
		"da_noi": _da_noi(dong),
		"goi_y": gy,
		"nhom": _nhom_cua(hd, dong, bool(gy)),
		"lam_duoc": 1 if _lam_duoc() else 0,
		"nguong_lech": NGUONG_LECH,
	}


@frappe.whitelist()
def so_sanh(name, phieu=None):
	"""Doi chieu tung mon giua hoa don va cac phieu nhap duoc chon."""
	_kiem_quyen()
	if isinstance(phieu, str):
		phieu = frappe.parse_json(phieu or "[]")
	phieu = [str(p).strip() for p in (phieu or []) if str(p).strip()]
	hd = frappe.db.get_value(
		"Purchase Invoice", name, ["name", "supplier", "total", "docstatus"], as_dict=True
	)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % name)
	dong = _dong_hd(name)

	kho_pnk = {}
	tien_pnk = 0.0
	for p in phieu:
		if frappe.db.get_value("Purchase Receipt", p, "supplier") != hd["supplier"]:
			frappe.throw("Phiếu nhập %s không phải của nhà cung cấp này." % p)
		for r in _dong_pnk(p):
			r["phieu"] = p
			kho_pnk.setdefault(r["item_code"], []).append(r)
		tien_pnk += flt(frappe.db.get_value("Purchase Receipt", p, "total"))

	ra = []
	con = {k: list(v) for k, v in kho_pnk.items()}
	for r in dong:
		ds = con.get(r["item_code"]) or []
		sl_pnk = sum(flt(x["qty"]) for x in ds)
		gia_pnk = flt(ds[0]["rate"]) if ds else 0.0
		ra.append(
			{
				"idx": r["idx"],
				"item_code": r["item_code"],
				"item_name": r["item_name"],
				"sl_hd": flt(r["qty"]),
				"gia_hd": flt(r["rate"]),
				"tien_hd": flt(r["amount"]),
				"sl_pnk": sl_pnk,
				"gia_pnk": gia_pnk,
				"co_phieu": 1 if ds else 0,
				"lech_sl": flt(r["qty"]) - sl_pnk,
				"lech_gia": flt(r["rate"]) - gia_pnk if ds else 0.0,
				"da_noi": (r.get("purchase_receipt") or ""),
			}
		)

	# Mon nam trong phieu nhap ma hoa don khong he nhac toi: hang da ve kho
	# ma nha cung cap quen tinh tien, hoac hoa don nay chi la mot phan.
	ma_hd = {r["item_code"] for r in dong}
	thua = []
	for ma, ds in kho_pnk.items():
		if ma in ma_hd:
			continue
		thua.append(
			{
				"item_code": ma,
				"item_name": ds[0]["item_name"],
				"sl_pnk": sum(flt(x["qty"]) for x in ds),
				"tien_pnk": sum(flt(x["amount"]) for x in ds),
			}
		)

	return {
		"dong": ra,
		"thua": thua,
		"tien_hd": flt(hd["total"]),
		"tien_pnk": tien_pnk,
		"lech_tien": flt(hd["total"]) - tien_pnk,
		"khop": 1 if abs(flt(hd["total"]) - tien_pnk) <= NGUONG_LECH and not thua else 0,
		"nguong_lech": NGUONG_LECH,
	}


def _noi(doc, phieu):
	"""Gan tung dong hoa don vao dung dong phieu nhap. Tra danh sach loi.

	Noi bua la hong ca gia von lan ton kho, nen o day thua nhan la khong
	noi duoc con hon noi sai: ma hang phai trung, va so luong tren hoa don
	khong duoc VUOT so luong con lai cua phieu.
	"""
	kho = {}
	for p in phieu:
		for r in _dong_pnk(p):
			r["phieu"] = p
			r["con"] = flt(r["qty"])
			kho.setdefault(r["item_code"], []).append(r)

	try:
		giu_gia = cint(frappe.db.get_single_value("Buying Settings", "maintain_same_rate"))
	except Exception:
		giu_gia = 0
	loi = []
	for d in doc.items:
		if (d.get("purchase_receipt") or "").strip():
			continue
		ds = kho.get(d.item_code) or []
		can = flt(d.qty)
		chon = None
		for r in ds:
			if r["con"] >= can - 0.0001:
				chon = r
				break
		if not chon:
			co = sum(r["con"] for r in ds)
			if not ds:
				loi.append(
					"Dòng %d: món %s không có trong phiếu nhập nào đang chọn."
					% (d.idx, d.item_name or d.item_code)
				)
			else:
				loi.append(
					"Dòng %d: món %s trên hoá đơn %g mà phiếu nhập chỉ còn %g."
					% (d.idx, d.item_name or d.item_code, can, co)
				)
			continue
		# ERPNext co the dang bat "Giu nguyen don gia suot chu ky mua hang".
		# Luc do noi mot dong lech gia vao phieu nhap la no chan ngay luc luu,
		# bang mot cau tieng Anh khong ai doc ra. Bao truoc, bang tieng Viet.
		if giu_gia and abs(flt(d.rate) - flt(chon["rate"])) > 0.5:
			loi.append(
				"Dòng %d: món %s đơn giá hoá đơn %s, phiếu nhập %s. Thiết lập "
				"mua hàng đang bắt hai bên phải bằng nhau."
				% (d.idx, d.item_name or d.item_code, flt(d.rate), flt(chon["rate"]))
			)
			continue
		chon["con"] -= can
		d.purchase_receipt = chon["phieu"]
		d.pr_detail = chon["name"]
	return loi


@frappe.whitelist()
def noi_phieu(name, phieu=None, ghi_so=0):
	"""Noi hoa don voi phieu nhap, va ghi so luon neu duoc yeu cau.

	Mot nut lam ca hai buoc: dung cai lam Uyen ket hom 12/08 - noi xong bam
	Luu ma trang thai khong doi, vi con thieu nut Gui o cho khac.
	"""
	_kiem_quyen()
	if not _lam_duoc():
		frappe.throw("Chỉ kế toán hoặc thu mua mới nối phiếu và ghi sổ hoá đơn mua được.")
	if isinstance(phieu, str):
		phieu = frappe.parse_json(phieu or "[]")
	phieu = [str(p).strip() for p in (phieu or []) if str(p).strip()]
	if not phieu:
		frappe.throw("Chưa chọn phiếu nhập kho nào để nối.")

	doc = frappe.get_doc("Purchase Invoice", name)
	if doc.docstatus != 0:
		frappe.throw("Hoá đơn %s đã ghi sổ rồi, không nối lại được." % name)
	if cint(doc.get("update_stock")):
		frappe.throw(
			"Hoá đơn %s đang bật \"Cập nhật tồn kho\". Nối vào phiếu nhập nữa là "
			"hàng vào kho hai lần. Tắt ô đó rồi nối lại giúp em." % name
		)
	for p in phieu:
		if frappe.db.get_value("Purchase Receipt", p, "supplier") != doc.supplier:
			frappe.throw("Phiếu nhập %s không phải của nhà cung cấp này." % p)

	loi = _noi(doc, phieu)
	if loi:
		frappe.throw(
			"Chưa nối được, mấy dòng này chưa khớp:\n\n" + "\n".join(loi) +
			"\n\nSửa lại số lượng trên hoá đơn cho khớp phiếu nhập, hoặc chọn "
			"thêm phiếu nhập khác."
		)
	doc.flags.ignore_permissions = True
	doc.save()

	if not cint(ghi_so):
		frappe.db.commit()
		return {"da_noi": 1, "da_ghi_so": 0, "name": doc.name}

	doc.reload()
	doc.flags.ignore_permissions = True
	doc.submit()
	frappe.db.commit()
	return {"da_noi": 1, "da_ghi_so": 1, "name": doc.name, "trang_thai": doc.status}
