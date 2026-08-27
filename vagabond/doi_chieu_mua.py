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

from vagabond import dvt_mua

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

# Ai duoc chot mot to hoa don co don gia khac gia dat hang.
#
# Anh Viet chot 27/08/2026: mo cho Uyen. Uyen giu vai Purchase Manager va
# AP Officer nen hai vai do nam trong day.
#
# Vi sao viet vao ma nguon chu khong dua vao o thiet lap cua ERPNext: o
# "role_to_override_stop_action" chi chua DUNG MOT vai, va no chi co tac
# dung khi o kia dang de muc "Stop". Hom nay o kia dang de "Warn" nen ai
# vao duoc man nay cung chot duoc - nhung ai do lo tay doi lai thanh "Stop"
# la Uyen mat quyen ma khong ai hay. Viet ra day thi quyet dinh cua anh Viet
# song sot qua moi lan doi thiet lap.
VAI_CHOT_GIA_KHAC = {
	"System Manager",
	"Accounts Manager",
	"Purchase Manager",
	"AP Officer",
}

TRAN_DONG = 300

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


# Vai duoc phep ghi so mot to hoa don co don gia khac phieu nhap. Khong ghi
# cung o day ma DOC tu chinh o thiet lap cua ERPNext, de app va ERPNext
# khong bao gio noi hai dieu khac nhau: ERPNext chan hay khong chan cung
# nhin dung o do.
#
# Patch dong_bo_cau_truc dat o do bang "Accounts Manager" khi no con trong.
# Doi vai khac thi vao Buying Settings sua mot cho, khong phai sua ma nguon.
VAI_VUOT_GIA_MAC_DINH = "Accounts Manager"


def _vai_vuot_lech_gia():
	try:
		return (
			frappe.db.get_single_value("Buying Settings", "role_to_override_stop_action") or ""
		).strip()
	except Exception:
		return ""


def _vuot_lech_gia_duoc():
	"""Nguoi dang dung co duoc noi mot dong lech gia vao phieu nhap khong.

	Doc dung hai o thiet lap ma ERPNext doc, de nut ben app va nut ben man
	quan tri KHONG BAO GIO xu khac nhau (anh Viet 26/08/2026, lenh dong bo
	hai man). Tu v318 thiet lap chuyen tu "Stop" sang "Warn": ERPNext chi
	nhac chu khong chan nua, thi ben app cung vay - van ghi vet ai duyet
	vao to hoa don, nhung khong chan.
	"""
	try:
		if (
			frappe.db.get_single_value("Buying Settings", "maintain_same_rate_action")
			or "Stop"
		).strip() != "Stop":
			return True
	except Exception:
		pass
	cua_toi = set(frappe.get_roles())
	if VAI_CHOT_GIA_KHAC & cua_toi:
		return True
	vai = _vai_vuot_lech_gia()
	if not vai:
		return False
	return vai in cua_toi


def _ghi_chu_lech_gia(doc, dong, phieu):
	"""Ghi lai vao chinh to hoa don rang ai cho qua khoan lech gia nao.

	Cho qua ma khong de lai dau vet thi thang sau khong ai truy duoc vi sao
	gia von thang nay nhay.
	"""
	cau = (
		"Lệch giá dòng %d món %s: hoá đơn %s, phiếu nhập %s (%s duyệt %s)."
		% (
			dong.idx,
			dong.item_name or dong.item_code,
			flt(dong.rate),
			flt(phieu.get("rate")),
			frappe.session.user,
			nowdate(),
		)
	)
	cu = (doc.get("remarks") or "").strip()
	if cau in cu:
		return
	doc.remarks = (cu + "\n" + cau).strip() if cu else cau


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
		fields=[
			"name", "item_code", "item_name", "qty", "rate", "amount", "billed_amt",
			"uom", "conversion_factor", "stock_uom", "stock_qty",
		],
		order_by="idx asc",
		limit_page_length=0,
	)


def _dong_hd(name):
	return frappe.get_all(
		"Purchase Invoice Item",
		filters={"parent": name},
		fields=[
			"name", "idx", "item_code", "item_name", "qty", "rate", "amount",
			"uom", "conversion_factor", "stock_uom", "stock_qty", "description",
			"purchase_receipt", "pr_detail",
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
	"""Danh sach hoa don mua kem trang thai doi chieu.

	Doc TAT CA trong vai cau truy van roi ghep trong bo nho, khong doc
	tung to mot: hien co hon tam tram hoa don mua con nhap, doc tung to la
	moi lan mo man phai chay may nghin cau truy van.
	"""
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
	ds = [
		r
		for r in ds
		if not q
		or q in ((r.name or "") + " " + (r.supplier_name or "") + " " + (r.bill_no or "")).lower()
	]
	nhap = [r["name"] for r in ds if r.get("docstatus") == 0]
	ncc = sorted({r["supplier"] for r in ds if r.get("docstatus") == 0 and r.get("supplier")})

	# Dong hang cua moi hoa don con nhap, mot cau.
	dong_theo_hd = {}
	if nhap:
		for r in frappe.get_all(
			"Purchase Invoice Item",
			filters={"parent": ["in", nhap]},
			fields=["parent", "item_code", "purchase_receipt"],
			limit_page_length=0,
		):
			dong_theo_hd.setdefault(r["parent"], []).append(r)

	# Phieu nhap con chua duoc hoa don nao lay het, cua dung may nha cung
	# cap dang co hoa don nhap. Noi rong khoang ngay hai dau, vi hang ve
	# truoc va hoa don ve sau la chuyen thuong.
	pnk_theo_ncc = {}
	dong_pnk = {}
	if ncc:
		pnks = frappe.get_all(
			"Purchase Receipt",
			filters={
				"supplier": ["in", ncc],
				"docstatus": 1,
				"posting_date": ["between", [str(add_days(tu, -60)), str(add_days(den, 60))]],
			},
			fields=["name", "supplier", "posting_date", "total", "per_billed"],
			limit_page_length=0,
		)
		pnks = [p for p in pnks if flt(p.get("per_billed")) < 99.99]
		for p in pnks:
			pnk_theo_ncc.setdefault(p["supplier"], []).append(p)
		if pnks:
			for r in frappe.get_all(
				"Purchase Receipt Item",
				filters={"parent": ["in", [p["name"] for p in pnks]]},
				fields=["parent", "item_code"],
				limit_page_length=0,
			):
				dong_pnk.setdefault(r["parent"], set()).add(r["item_code"])

	ra = []
	for r in ds:
		o = dict(r)
		if r.get("docstatus") == 1:
			o["nhom"] = "huy" if cint(r.get("vgb_huy")) else "xong"
			o["so_dong"] = 0
			o["da_noi"] = 0
			o["so_phieu_goi_y"] = 0
			ra.append(o)
			continue
		dong = dong_theo_hd.get(r["name"]) or []
		ma_hd = {d["item_code"] for d in dong}
		gy = []
		for p in pnk_theo_ncc.get(r["supplier"]) or []:
			if dong_pnk.get(p["name"], set()) & ma_hd:
				gy.append(p)
		gy.sort(key=lambda p: -len(dong_pnk.get(p["name"], set()) & ma_hd))
		o["so_dong"] = len(dong)
		o["da_noi"] = _da_noi(dong)
		o["so_phieu_goi_y"] = len(gy)
		o["nhom"] = _nhom_cua(r, dong, bool(gy))
		if o["nhom"] in ("cho_doi_chieu", "cho_ghi_so") and gy:
			# Lech tien tinh tren PHUONG AN MAY DE XUAT, tuc phieu diem cao
			# nhat. Chi de bay chip canh bao tu xa, con so that thi man chi
			# tiet tinh lai theo dung phieu nguoi dung chon.
			tien_pnk = flt(gy[0]["total"])
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
			"outstanding_amount", "vgb_huy", "due_date", "custom_minvoice_id",
		],
		as_dict=True,
	)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % name)
	dong = _dong_hd(name)
	gy = _goi_y(hd, dong) if hd.get("docstatus") == 0 else []
	# Phieu ma hoa don nay DA tro toi. Uyen noi phieu tu hom truoc roi bo
	# do vi khong biet con nut Gui; mo lai man nay ma may tick san mot
	# phieu khac thi bang doi chieu ben duoi noi sai chuyen.
	da_noi_ds = sorted({(r.get("purchase_receipt") or "").strip() for r in dong} - {""})
	ten_gy = {p["name"] for p in gy}
	for ma in da_noi_ds:
		if ma in ten_gy:
			continue
		p = frappe.db.get_value(
			"Purchase Receipt", ma, ["name", "posting_date", "total", "per_billed"], as_dict=True
		)
		if not p:
			continue
		dp = _dong_pnk(ma)
		gy.insert(0, {
			"name": p["name"],
			"ngay": str(p.get("posting_date") or ""),
			"tien": flt(p.get("total")),
			"tong": flt(p.get("total")),
			"da_hoa_don": flt(p.get("per_billed")),
			"so_mon": len(dp),
			"so_mon_trung": len(dp),
			"dong": dp,
		})
	# To nay sinh tu hoa don dien tu thi so tong voi ban goc. Lech la co
	# nguoi da chep de len dong hang, thuong la nut "Noi phieu nhap kho" ben
	# man quan tri. Doc `vagabond/dung_lai_hddt.py`.
	hddt = None
	try:
		from vagabond import dung_lai_hddt

		g = dung_lai_hddt._goc(hd.get("custom_minvoice_id"))
		if g and flt(g.get("tong_tien")):
			viec, so = dung_lai_hddt.huong_lech(hd.get("grand_total"), g.get("tong_tien"))
			hddt = {
				"so": "%s/%s" % (g.get("ky_hieu") or "", g.get("so_hd") or ""),
				"tong": flt(g.get("tong_tien")),
				"viec": viec,
				"lech": so,
				"dung_lai_duoc": 1 if (viec != "khop" and hd.get("docstatus") == 0) else 0,
			}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "doi_chieu_mua: soi hoa don dien tu")

	return {
		"hd": hd,
		"hddt": hddt,
		"dong": dong,
		"da_noi": _da_noi(dong),
		"phieu_da_noi": da_noi_ds,
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
		hs_hd = dvt_mua.he_so(r.get("conversion_factor"))
		hs_pnk = dvt_mua.he_so(ds[0].get("conversion_factor")) if ds else hs_hd
		dvt_kho = r.get("stock_uom") or (ds[0].get("stock_uom") if ds else "") or ""
		# So luong va don gia deu quy ve DON VI KHO truoc khi tru nhau. Truoc
		# v315 cho nay tru thang "4" voi "4" ma khong nhin don vi, nen mot
		# dong 4 Gram doi dien 4 Tui van hien ra la khop so luong.
		ton_hd = dvt_mua.ton(r.get("qty"), hs_hd)
		ton_pnk = sum(dvt_mua.ton(x.get("qty"), x.get("conversion_factor")) for x in ds)
		gia_kho_hd = dvt_mua.gia_moi_don_vi_kho(r.get("rate"), hs_hd)
		gia_kho_pnk = dvt_mua.gia_moi_don_vi_kho(ds[0].get("rate"), hs_pnk) if ds else 0.0
		# MOT phep xet dung chung voi phep noi. Truoc 27/08/2026 hai cho xet
		# khac nhau nen man hinh bao khop ma nut noi lai tu choi.
		xet = (
			dvt_mua.xet_don_vi(r.get("uom"), hs_hd, ds[0].get("uom"), hs_pnk)
			if ds
			else dvt_mua.DVT_KHOP
		)
		lech_dvt = 1 if xet == dvt_mua.DVT_LECH else 0
		khac_ten_dvt = 1 if xet == dvt_mua.DVT_KHAC_TEN else 0
		ra.append(
			{
				"idx": r["idx"],
				"item_code": r["item_code"],
				"item_name": r["item_name"],
				"sl_hd": flt(r["qty"]),
				"gia_hd": flt(r["rate"]),
				"tien_hd": flt(r["amount"]),
				"sl_pnk": sum(flt(x["qty"]) for x in ds),
				"gia_pnk": flt(ds[0]["rate"]) if ds else 0.0,
				"dvt_hd": r.get("uom") or "",
				"dvt_pnk": (ds[0].get("uom") or "") if ds else "",
				"dvt_kho": dvt_kho,
				"dvt_ncc": dvt_mua.dvt_tren_hoa_don(r.get("description")),
				"ton_hd": ton_hd,
				"ton_pnk": ton_pnk,
				"gia_kho_hd": gia_kho_hd,
				"gia_kho_pnk": gia_kho_pnk,
				"lech_dvt": lech_dvt,
				# Cung so luong, chi khac cai ten. Khong phai loi, phep noi tu
				# doi ten cho khop. Van tra ra de man hinh noi cho nguoi ta biet.
				"khac_ten_dvt": khac_ten_dvt,
				"co_phieu": 1 if ds else 0,
				"lech_sl": ton_hd - ton_pnk,
				"lech_gia": (gia_kho_hd - gia_kho_pnk) if ds else 0.0,
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

	so_lech_dvt = len([r for r in ra if r.get("lech_dvt")])
	so_khac_ten_dvt = len([r for r in ra if r.get("khac_ten_dvt")])
	return {
		"dong": ra,
		"thua": thua,
		"tien_hd": flt(hd["total"]),
		"tien_pnk": tien_pnk,
		"lech_tien": flt(hd["total"]) - tien_pnk,
		# Lech don vi thi khong bao gio duoc coi la khop, du tien co bang nhau
		# tuyet doi: tien bang nhau ma so luong lech mot nghin lan la ca that
		# ngay 26/08/2026, doc `vagabond/dvt_mua.py`.
		"khop": 1
		if abs(flt(hd["total"]) - tien_pnk) <= NGUONG_LECH and not thua and not so_lech_dvt
		else 0,
		"so_lech_dvt": so_lech_dvt,
		"so_khac_ten_dvt": so_khac_ten_dvt,
		"vuot_lech_gia_duoc": 1 if _vuot_lech_gia_duoc() else 0,
		"nguong_lech": NGUONG_LECH,
	}


def _doi_ten_don_vi(dong, phieu):
	"""Doi ten don vi cua dong hoa don theo dong phieu nhap. True neu doi duoc.

	CHI goi khi da xac dinh hai ben cung so luong quy ve kho, tuc la he so
	bang nhau. Khi do doi ten khong lam so luong that xe dich mot ly nao:
	`stock_qty` van bang `qty` nhan he so, ma he so giu nguyen.

	Van kiem danh muc Mon co khai don vi do khong. Dat mot don vi ma Mon
	chua khai la ERPNext tu tinh lai he so theo cach cua no, va cai gia phai
	tra la sai so luong ton kho - dung cai minh dang tranh.
	"""
	dvt = (phieu.get("uom") or "").strip()
	if not dvt:
		return False
	ma = (dong.get("item_code") or "").strip()
	if not ma:
		return False
	hs = frappe.db.get_value(
		"UOM Conversion Detail", {"parent": ma, "uom": dvt}, "conversion_factor"
	)
	if not hs:
		return False
	if abs(dvt_mua.he_so(hs) - dvt_mua.he_so(phieu.get("hs"))) > 1e-9:
		return False
	dong.uom = dvt
	dong.conversion_factor = flt(hs)
	return True


def _noi(doc, phieu):
	"""Gan tung dong hoa don vao dung dong phieu nhap. Tra danh sach loi.

	Noi bua la hong ca gia von lan ton kho, nen o day thua nhan la khong
	noi duoc con hon noi sai: ma hang phai trung, va so luong tren hoa don
	khong duoc VUOT so luong con lai cua phieu.

	Tu v315 moi phep so deu quy ve DON VI KHO. Truoc do cho nay tru thang
	so luong voi so luong, nen mot dong hoa don ghi 4 GRAM doi dien mot
	dong phieu nhap 4 TUI van duoc coi la khop - lech mot nghin lan ma
	man hinh bao la chi lech gia. Doc `vagabond/dvt_mua.py`.
	"""
	kho = {}
	for p in phieu:
		for r in _dong_pnk(p):
			r["phieu"] = p
			r["hs"] = dvt_mua.he_so(r.get("conversion_factor"))
			r["con"] = dvt_mua.ton(r.get("qty"), r["hs"])
			kho.setdefault(r["item_code"], []).append(r)

	try:
		giu_gia = cint(frappe.db.get_single_value("Buying Settings", "maintain_same_rate"))
	except Exception:
		giu_gia = 0
	vuot_duoc = _vuot_lech_gia_duoc()
	loi = []
	for d in doc.items:
		if (d.get("purchase_receipt") or "").strip():
			continue
		ds = kho.get(d.item_code) or []
		hs_hd = dvt_mua.he_so(d.get("conversion_factor"))
		can = dvt_mua.ton(d.get("qty"), hs_hd)
		dvt_kho = d.get("stock_uom") or (ds[0].get("stock_uom") if ds else "") or ""
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
			elif dvt_mua.lech_don_vi(d.get("uom"), hs_hd, ds[0].get("uom"), ds[0]["hs"]):
				# Lech don vi thi so luong lech theo, va cai can noi la don vi
				# chu khong phai so luong. Noi dung cai goc.
				loi.append(
					dvt_mua.loi_lech_don_vi(
						d.idx,
						d.item_name or d.item_code,
						d.get("qty"),
						d.get("uom"),
						hs_hd,
						ds[0].get("qty"),
						ds[0].get("uom"),
						ds[0]["hs"],
						dvt_kho,
						dvt_mua.dvt_tren_hoa_don(d.get("description")),
					)
				)
			else:
				loi.append(
					"Dòng %d: món %s trên hoá đơn %g %s mà phiếu nhập chỉ còn %g %s."
					% (d.idx, d.item_name or d.item_code, can, dvt_kho, co, dvt_kho)
				)
			continue
		# ERPNext doi o "uom" cua hai ben bang nhau TUNG CHU, da do ma nguon
		# v16: compare_fields cua Purchase Receipt Item la
		# [["project","="], ["item_code","="], ["uom","="]]. Don gia KHONG
		# nam trong danh sach do.
		#
		# Nen o day tach lam hai:
		#   * He so khac nhau  -> so luong that lech, KHONG noi, bao ro.
		#   * Cung so luong ma khac ten -> TU DOI ten dong hoa don theo phieu
		#     nhap roi di tiep. An toan vi so luong quy ve kho khong doi mot
		#     ly nao. Truoc 27/08/2026 cho nay bat nguoi ta bam them mot nut,
		#     ma nut do lai khong hien vi man hinh coi la khop - ket cung.
		xet = dvt_mua.xet_don_vi(d.get("uom"), hs_hd, chon.get("uom"), chon["hs"])
		if xet == dvt_mua.DVT_LECH:
			loi.append(
				dvt_mua.loi_lech_don_vi(
					d.idx,
					d.item_name or d.item_code,
					d.get("qty"),
					d.get("uom"),
					hs_hd,
					chon.get("qty"),
					chon.get("uom"),
					chon["hs"],
					dvt_kho,
					dvt_mua.dvt_tren_hoa_don(d.get("description")),
				)
			)
			continue
		if xet == dvt_mua.DVT_KHAC_TEN and not _doi_ten_don_vi(d, chon):
			loi.append(
				"Dòng %d: món %s ghi đơn vị %s còn phiếu nhập ghi %s. Hai bên "
				"cùng số lượng nhưng danh mục Món chưa khai %s nên chưa đổi tên "
				"được. Khai đơn vị đó vào bảng quy đổi của món rồi nối lại."
				% (
					d.idx,
					d.item_name or d.item_code,
					d.get("uom") or "",
					chon.get("uom") or "",
					chon.get("uom") or "",
				)
			)
			continue
		# ERPNext dang bat "Giu nguyen don gia suot chu ky mua hang". Noi mot
		# dong lech gia vao phieu nhap la no chan ngay luc luu.
		#
		# Nhung lech gia KHONG phai lúc nào cũng là nhầm. Ngay 26/08/2026 anh
		# Viet bao: Uyen dat hang luc nha cung cap con khuyen mai 161.000, den
		# luc ho xuat hoa don thi het chuong trinh nen ghi 280.000. Hang da ve
		# kho roi, hoa don la that, phai ghi so duoc.
		#
		# Nen o day khong chan cung nua: ai co quyen vuot thi cho di kem mot
		# dong ghi chu vao chinh to hoa don, ai khong co thi bao ro la nho ke
		# toan ghi so, thay vi mot cau tieng Anh khong ai doc ra.
		gia_hd = dvt_mua.gia_moi_don_vi_kho(d.get("rate"), hs_hd)
		gia_pnk = dvt_mua.gia_moi_don_vi_kho(chon.get("rate"), chon["hs"])
		if giu_gia and abs(gia_hd - gia_pnk) > 0.5 / max(1.0, hs_hd):
			if not vuot_duoc:
				loi.append(
					"Dòng %d: món %s đơn giá hoá đơn %s, phiếu nhập %s. Hai bên "
					"khác giá nên chỉ kế toán mới ghi sổ được tờ này. Nhờ kế toán "
					"ghi sổ giúp, hoặc đề nghị nhà cung cấp phát hành lại hoá đơn."
					% (d.idx, d.item_name or d.item_code, flt(d.rate), flt(chon["rate"]))
				)
				continue
			_ghi_chu_lech_gia(doc, d, chon)
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
			'Hoá đơn %s đang bật "Cập nhật tồn kho". Nối vào phiếu nhập nữa là hàng vào kho hai lần. Vui lòng tắt ô đó rồi nối lại.' % name
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


@frappe.whitelist()
def sua_don_vi(name, dong=None, dvt=None):
	"""Sua DON VI cua mot dong hoa don mua con nhap, giu nguyen tien.

	Vi sao co ham nay: man hinh bao "hai bên khác đơn vị" ma khong co duong
	nao sua thi cau bao do vo dung. Uyen phai mo Desk, tim dung dong, doi o
	don vi - viec ma man nay sinh ra de khoi phai lam.

	Doi CAI GI: chi `uom` va `conversion_factor`. So luong va don gia giu
	nguyen nen THANH TIEN khong doi mot dong nao, chi so luong quy ve kho
	la duoc nan lai cho dung. Vi du dong 4 Gram gia 280.000 doi sang Tui thi
	van la 1.120.000, nhung ton kho tinh la 4.000 gram chu khong phai 4.

	Don vi moi PHAI co san trong bang quy doi cua chinh mon do. Khong co thi
	tu choi, khong tu them dong vao bang quy doi - bang do la khai bao cua
	nguoi, may khong duoc tu dat.
	"""
	_kiem_quyen()
	if not _lam_duoc():
		frappe.throw("Chỉ kế toán hoặc thu mua mới sửa đơn vị dòng hoá đơn được.")
	dvt = str(dvt or "").strip()
	if not dvt:
		frappe.throw("Chưa chọn đơn vị mới.")
	doc = frappe.get_doc("Purchase Invoice", name)
	if doc.docstatus != 0:
		frappe.throw("Hoá đơn %s đã ghi sổ rồi, không sửa đơn vị được." % name)
	ds_dong = [str(x).strip() for x in frappe.parse_json(dong or "[]")] if isinstance(dong, str) else [
		str(x).strip() for x in (dong or [])
	]
	sua = 0
	for d in doc.items:
		if ds_dong and d.name not in ds_dong and str(d.idx) not in ds_dong:
			continue
		if (d.get("purchase_receipt") or "").strip():
			frappe.throw(
				"Dòng %d đã nối vào phiếu nhập rồi. Bỏ nối trước khi đổi đơn vị." % d.idx
			)
		hs = dvt_mua.he_so_cua_mon(d.item_code, dvt)
		if not hs:
			frappe.throw(
				'Món %s chưa khai đơn vị "%s" trong bảng quy đổi. Nhờ thu mua khai '
				"đơn vị đó cho món trước, rồi quay lại đổi." % (d.item_name or d.item_code, dvt)
			)
		if dvt_mua.cung_don_vi(d.get("uom"), dvt):
			continue
		d.uom = dvt
		d.conversion_factor = hs
		sua += 1
	if not sua:
		frappe.throw("Không có dòng nào cần đổi đơn vị.")
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"da_sua": sua, "name": doc.name}


@frappe.whitelist()
def don_vi_cua_mon(item_code):
	"""Cac don vi mot mon dang khai, de man hinh cho chon. CHI DOC."""
	_kiem_quyen()
	kho = frappe.db.get_value("Item", item_code, "stock_uom") or ""
	ds = frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": item_code},
		fields=["uom", "conversion_factor"],
		order_by="conversion_factor asc",
		limit_page_length=0,
	)
	return {"kho": kho, "dvt": [{"ten": r["uom"], "he_so": flt(r["conversion_factor"])} for r in ds]}
