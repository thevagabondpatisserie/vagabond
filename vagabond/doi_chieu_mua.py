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


# Ai duoc GHI SO mot to hoa don mua. Hep hon `_lam_duoc` mot bac.
#
# Chi Dung 28/08/2026: *"khi Uyen noi phieu la may tu ghi so luon a em"*.
# Anh Viet hoi lai: chan lai luc noi phieu, chi ke toan moi duoc ghi so.
#
# Vi sao tach lam hai vai chu khong chan tat: noi phieu la viec DOI CHIEU
# giay to, do la viec cua thu mua, va Uyen lam viec do nhanh nhat. Ghi so
# la viec quyet dinh con so vao so cai, do la viec cua ke toan. Gop hai
# viec vao mot nut nghia la nguoi doi chieu tu duyet phan doi chieu cua
# chinh minh - dung cai ma hai cap duyet sinh ra de tranh.
#
# Uyen van bam "Chi noi phieu" duoc, to hoa don nam o dang nhap cho chi
# Dung ghi so. Khong ai bi ket viec.
VAI_GHI_SO = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
}


def _ghi_so_duoc():
	return bool(VAI_GHI_SO & set(frappe.get_roles()))


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
		# Man hinh phai biet de an nut "Khop va ghi so" di, khong thi Uyen
		# bam roi moi biet minh khong duoc phep - mot vong lam viec vut di.
		"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,
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
		# Man hinh phai biet de an nut "Khop va ghi so" di, khong thi Uyen
		# bam roi moi biet minh khong duoc phep - mot vong lam viec vut di.
		"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,
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
				# He so cua dong phieu nhap. Man hinh dung no de DE XUAT he
				# so khi khai don vi cua nha cung cap vao mon: hai ben cung
				# so luong thi don vi cua ho bang don vi cua minh. Chi de
				# xuat, nguoi van phai go. Xem `khai_don_vi` cuoi tep nay.
				"hs_pnk": flt(hs_pnk) if ds else 0.0,
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


def _khong_qua_kho(item_code):
	"""Dong nay co di qua kho khong. Khong thi dung doi hoi phieu nhap.

	ANH VIET 31/08/2026
	--------------------------------------------------------------------
	*"Chi can co dong phi dich vu van chuyen la da bi lech ngay roi va he
	thong khong cho phep noi hoa don voi PNK do vi ben PNK khong co dong
	phi dich vu van chuyen va cac dong phu phi khac?"*

	Dung y nguyen. Va do la mot be tac CAU TRUC chu khong phai loi vat.

	Phi ship, phi dich vu, van phong pham KHONG BAO GIO nam trong phieu
	nhap kho, vi chung khong phai hang ton kho. Ma phep noi cu doi MOI dong
	phai tim ra phieu, tim khong ra la nem loi cho ca to. Nghia la he to
	hoa don nao co mot dong phi la to do VINH VIEN khong noi duoc. Hoa don
	7100 cua An Phu dung hai dong: mot dong cherry va mot dong phi ship.

	Nen phai tach hai loai dong:
	  - Dong KHONG qua kho: khong doi phieu, khong bao loi, cho di tiep.
	  - Dong CO qua kho ma chua noi: van noi ra, va van chan luc GHI SO
	    (khong co phieu thi gia von sai), nhung KHONG chan buoc noi.
	"""
	ma = str(item_code or "").strip()
	if not ma:
		# Chua gan ma hang thi chua biet no la gi. Khong doan la hang, cung
		# khong doan la phi. Cho di tiep o buoc noi, con ghi so thi da co
		# hang rao rieng.
		return True
	try:
		return not cint(frappe.db.get_value("Item", ma, "is_stock_item"))
	except Exception:
		return False


def _noi(doc, phieu, chi_tiet=False):
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

	# Hai ro rieng biet. `loi` giu nguyen dinh dang cu (danh sach cau chu)
	# vi `dung_lai_hddt._phieu_da_noi` dang doc kieu do. `xep` ghi them dong
	# nao la hang that - chi nhung dong do moi duoc chan luc ghi so.
	loi = []
	xep = []

	def _ghi(idx, ma, cau):
		loi.append(cau)
		xep.append({"idx": idx, "item_code": ma or "",
			"qua_kho": 0 if _khong_qua_kho(ma) else 1, "cau": cau})

	da_noi = 0
	for d in doc.items:
		if (d.get("purchase_receipt") or "").strip():
			continue

		# DONG CHUA GAN MA HANG. Phai chan o day, TRUOC moi phep so sanh.
		#
		# Anh Viet 31/08/2026: *"Anh qua roi voi luong nay roi, cac ben khong
		# the lam viec neu cu bi loi the nay."* Va anh dung.
		#
		# Ca that HDM-26-08-00042, hoa don 6921 cua An Phu: ca ba dong DUA
		# XIEM, CHERRY CALADA va Phi ship deu co `item_code` RONG, vi ten
		# hang cua nha cung cap chua ai anh xa vao Mon nao. Phep tim phieu
		# duoi day tra cuu bang `item_code`, ma khoa rong thi khong bao gio
		# tra ra gi. Man hinh ben duoi ket luan "hang chua duoc nhap kho
		# tren he thong" - trong khi PNK-2026-00171 nam ngay do, da xac
		# nhan, co dung 2 Kg cherry cua chinh nha cung cap do.
		#
		# Cau chan doan sai con hai hon khong co cau nao: Uyen doc xong di
		# lap them phieu nhap cho mot lo hang da nhap kho roi, hoac di tim
		# quyen sua gia. Ngay 31/08 he con 9.985 tren 11.351 dong hoa don o
		# tinh trang nay, tren 2.612 to. Nghia la moi nguoi gap cau bao sai
		# nay gan nhu moi ngay.
		#
		# Nen noi dung mot cau: dong nay chua gan ma hang.
		if not (d.get("item_code") or "").strip():
			_ghi(d.idx, d.get("item_code"),
				"Dòng %d: hàng \"%s\" chưa gắn mã hàng, nên máy không biết "
				"đối chiếu với món nào trong kho. Bấm nút \"Gắn mã hàng\" "
				"ngay trên dòng này để chọn món một lần; lần sau nhà cung cấp "
				"gửi đúng tên hàng đó là máy tự nhận. Hàng không qua kho "
				"(dịch vụ, phí ship, văn phòng phẩm) thì bỏ qua bước nối "
				"phiếu, nhờ kế toán ghi sổ thẳng tờ này."
				% (d.idx, d.item_name or ""))
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
				# CÂU NÀY TỪNG LÀM UYÊN KẸT (anh Việt báo 31/08/2026).
				#
				# Bản cũ chỉ nói "không có trong phiếu nhập nào đang chọn" rồi
				# dừng. Người đọc hiểu là mình chọn nhầm phiếu nên đi chọn lại,
				# chọn mãi không ra, rồi kết luận là hệ thống chặn quyền sửa
				# giá - trong khi sự thật là món đó CHƯA TỪNG được nhập kho,
				# không có phiếu nào để chọn cả.
				#
				# Ca thật: giấy in A4 của Mực In Bảo Tín, hoá đơn 3513. Nhà
				# cung cấp đó không có một phiếu nhập nào trong hệ.
				#
				# Nên câu báo phải nói cả HAI đường đi tiếp, chứ một câu chẩn
				# đoán mà không có đường ra thì người ta tự nghĩ ra đường sai.
				# Toi day thi dong DA co ma hang (khuc tren da chan roi),
				# nen cau nay moi dung: mon co that, ma khong phieu nhap nao
				# cua nha cung cap nay chua no.
				_ghi(d.idx, d.item_code,
					"Dòng %d: món %s có mã hàng rồi nhưng không nằm trong "
					"phiếu nhập kho nào của nhà cung cấp này. Hai đường đi tiếp. "
					"Hàng có qua kho thì lập phiếu nhập kho trước rồi nối lại. "
					"Hàng không qua kho (văn phòng phẩm, dịch vụ, chi phí) thì "
					"bỏ qua bước nối phiếu, nhờ kế toán ghi sổ thẳng tờ này."
					% (d.idx, d.item_name or d.item_code))
			elif dvt_mua.lech_don_vi(d.get("uom"), hs_hd, ds[0].get("uom"), ds[0]["hs"]):
				# Lech don vi thi so luong lech theo, va cai can noi la don vi
				# chu khong phai so luong. Noi dung cai goc.
				_ghi(d.idx, d.item_code, dvt_mua.loi_lech_don_vi(
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
					))
			else:
				_ghi(d.idx, d.item_code,
					"Dòng %d: món %s trên hoá đơn %g %s mà phiếu nhập chỉ còn %g %s."
					% (d.idx, d.item_name or d.item_code, can, dvt_kho, co, dvt_kho))
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
			_ghi(d.idx, d.item_code, dvt_mua.loi_lech_don_vi(
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
				))
			continue
		if xet == dvt_mua.DVT_KHAC_TEN and not _doi_ten_don_vi(d, chon):
			_ghi(d.idx, d.item_code,
				"Dòng %d: món %s ghi đơn vị %s còn phiếu nhập ghi %s. Hai bên "
				"cùng số lượng nhưng danh mục Món chưa khai %s nên chưa đổi tên "
				"được. Khai đơn vị đó vào bảng quy đổi của món rồi nối lại."
				% (
					d.idx,
					d.item_name or d.item_code,
					d.get("uom") or "",
					chon.get("uom") or "",
					chon.get("uom") or "",
				))
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
				_ghi(d.idx, d.item_code,
					"Dòng %d: món %s đơn giá hoá đơn %s, phiếu nhập %s. Hai bên "
					"khác giá nên chỉ kế toán mới ghi sổ được tờ này. Nhờ kế toán "
					"ghi sổ giúp, hoặc đề nghị nhà cung cấp phát hành lại hoá đơn."
					% (d.idx, d.item_name or d.item_code, flt(d.rate), flt(chon["rate"])))
				continue
			_ghi_chu_lech_gia(doc, d, chon)
		chon["con"] -= can
		d.purchase_receipt = chon["phieu"]
		d.pr_detail = chon["name"]
		da_noi += 1

	if not chi_tiet:
		return loi
	return {
		"da_noi": da_noi,
		"loi": loi,
		# Chi nhung dong HANG THAT chua noi moi chan buoc ghi so. Dong phi
		# ship, phi dich vu, van phong pham thi khong bao gio nam trong phieu
		# nhap, doi hoi chung co phieu la doi mot thu khong ton tai.
		"chan_ghi_so": [x for x in xep if x["qua_kho"]],
		"khong_qua_kho": [x for x in xep if not x["qua_kho"]],
	}


@frappe.whitelist()
def noi_phieu(name, phieu=None, ghi_so=0):
	"""Noi hoa don voi phieu nhap, va ghi so luon neu duoc yeu cau.

	Mot nut lam ca hai buoc: dung cai lam Uyen ket hom 12/08 - noi xong bam
	Luu ma trang thai khong doi, vi con thieu nut Gui o cho khac.
	"""
	_kiem_quyen()
	if not _lam_duoc():
		frappe.throw("Chỉ kế toán hoặc thu mua mới nối phiếu và ghi sổ hoá đơn mua được.")
	# Noi phieu thi thu mua lam duoc, GHI SO thi chi ke toan. Chan ngay o
	# dau cua, truoc khi dong vao chung tu, de nguoi bam biet lien chu
	# khong phai doi chay het roi moi bao hong.
	if cint(ghi_so) and not _ghi_so_duoc():
		frappe.throw(
			"Chỉ kế toán mới ghi sổ hoá đơn mua được. Anh chị bấm "
			'"Chỉ nối phiếu" để nối chứng từ, tờ hoá đơn sẽ nằm ở dạng nháp '
			"cho kế toán ghi sổ.",
			title="Chưa đủ quyền ghi sổ",
		)
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

	kq = _noi(doc, phieu, chi_tiet=True)

	# KHONG CHAN BUOC NOI NUA (anh Viet 31/08/2026).
	#
	# Ban cu: `if loi: frappe.throw(...)`. Mot dong khong khop la nem loi cho
	# CA TO, khong dong nao duoc noi. Ma dong phi ship thi khong bao gio khop
	# duoc, vi phieu nhap kho khong chua phi ship. Nghia la moi to hoa don co
	# mot dong phi la mot to VINH VIEN khong noi duoc - va hoa don cua tiem
	# thi hau nhu to nao cung co dong phi.
	#
	# Anh Viet: *"Chi can co dong phi dich vu van chuyen la da bi lech ngay
	# roi va he thong khong cho phep noi hoa don voi PNK do?"* Dung. Do la be
	# tac cau truc, va no la ly do that su khien "cac ben khong the lam viec".
	#
	# Nay: noi duoc dong nao thi noi dong do, dong nao chua noi duoc thi noi
	# ro ra chu khong chan. Hang rao chi con o buoc GHI SO, va chi cho dong
	# HANG THAT - vi hang that ma khong co phieu nhap thi gia von sai.
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	con_lai = [x["cau"] for x in kq["chan_ghi_so"]]
	bo_qua = [x["cau"] for x in kq["khong_qua_kho"]]

	if not cint(ghi_so):
		return {
			"da_noi": 1, "da_ghi_so": 0, "name": doc.name,
			"so_dong_da_noi": kq["da_noi"],
			"con_lai": con_lai, "khong_qua_kho": bo_qua,
			"loi_nhan": _loi_nhan_noi(kq),
		}

	if con_lai:
		frappe.throw(
			"Đã nối %d dòng. Chưa ghi sổ được vì mấy dòng hàng này chưa có "
			"phiếu nhập, ghi sổ luôn thì giá vốn sai:\n\n%s"
			% (kq["da_noi"], "\n".join(con_lai))
		)

	doc.reload()
	doc.flags.ignore_permissions = True
	doc.submit()
	frappe.db.commit()
	return {
		"da_noi": 1, "da_ghi_so": 1, "name": doc.name, "trang_thai": doc.status,
		"so_dong_da_noi": kq["da_noi"], "khong_qua_kho": bo_qua,
		"loi_nhan": _loi_nhan_noi(kq),
	}


def _loi_nhan_noi(kq):
	"""Mot cau cho man hinh, noi ro da lam gi va con gi."""
	p = ["Đã nối %d dòng vào phiếu nhập." % kq["da_noi"]]
	if kq["khong_qua_kho"]:
		p.append(
			"%d dòng không qua kho (phí ship, dịch vụ, chi phí) nên không cần "
			"phiếu nhập, kế toán ghi sổ thẳng." % len(kq["khong_qua_kho"])
		)
	if kq["chan_ghi_so"]:
		p.append(
			"Còn %d dòng hàng chưa có phiếu nhập, xem chi tiết bên dưới."
			% len(kq["chan_ghi_so"])
		)
	return " ".join(p)


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


@frappe.whitelist()
def khai_don_vi(item_code, dvt, he_so):
	"""Khai mot don vi moi vao bang quy doi cua mot mon.

	VI SAO PHAI CO CAI NAY, anh Viet hoi 31/08/2026
	--------------------------------------------------------------------
	*"Cai vu don vi tinh cu suot ngay bi lech anh chang hieu anh phai lam
	gi de no khong lech."*

	Duong cut nam o chinh man nay. Khi nha cung cap ghi mot don vi ma mon
	chua khai, `sua_don_vi` tu choi bang cau "Mon X chua khai don vi Y
	trong bang quy doi. Nho thu mua khai don vi do cho mon truoc, roi quay
	lai doi." Nhung KHONG CO CHO NAO de khai. Muon khai phai mo Desk, tim
	dung mon, mo bang quy doi, them dong. Khong ai lam, nen thang sau lai
	lech y nguyen.

	Nut nay la cai cho do. Khai mot lan cho mot mon, tu do ve sau may
	khong doan nua.

	HAI DIEU KHONG LAM
	--------------------------------------------------------------------
	Khong tu dat he so. He so la con so cua nguoi: 1 THUNG cua nha cung
	cap nay la 5 kg, cua nha khac la 10 kg, may khong biet. Man hinh co
	de xuat mot con so khi hoa don va phieu nhap cung so luong, nhung
	nguoi van phai nhin va bam.

	Khong ghi de he so da co. Doi he so cua mot don vi dang dung la doi
	so luong quy ve kho cua MOI chung tu cu dang dung don vi do, tuc doi
	gia von qua khu. Muon doi thi vao Desk doi tay, co lich su han hoi.
	"""
	_kiem_quyen()
	if not _lam_duoc():
		frappe.throw("Chỉ kế toán hoặc thu mua mới khai đơn vị cho món được.")

	item_code = str(item_code or "").strip()
	dvt = str(dvt or "").strip()
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw("Không tìm thấy món %s." % item_code)
	if not dvt:
		frappe.throw("Chưa chọn đơn vị cần khai.")
	if not frappe.db.exists("UOM", dvt):
		frappe.throw(
			'Hệ chưa có đơn vị "%s" trong danh mục Đơn vị tính. Nhờ kế toán '
			"thêm đơn vị đó vào danh mục trước, rồi quay lại khai cho món." % dvt
		)

	hs = flt(he_so)
	if hs <= 0:
		frappe.throw("Hệ số quy đổi phải là số lớn hơn 0.")

	dvt_kho = frappe.db.get_value("Item", item_code, "stock_uom") or ""
	if dvt_mua.cung_don_vi(dvt, dvt_kho):
		frappe.throw(
			'"%s" chính là đơn vị kho của món này, không cần khai quy đổi.' % dvt
		)

	cu = dvt_mua.he_so_cua_mon(item_code, dvt)
	if cu:
		return {
			"da_co": 1, "item_code": item_code, "dvt": dvt, "he_so": flt(cu),
			"dvt_kho": dvt_kho,
			"loi_nhan": 'Món này đã khai "%s" rồi, 1 %s = %s %s.'
			% (dvt, dvt, flt(cu), dvt_kho),
		}

	doc = frappe.get_doc("Item", item_code)
	doc.append("uoms", {"uom": dvt, "conversion_factor": hs})
	doc.flags.ignore_permissions = True
	doc.save()
	doc.add_comment(
		"Comment",
		"Khai đơn vị %s cho món này: 1 %s = %s %s. %s khai ngày %s."
		% (dvt, dvt, hs, dvt_kho, frappe.session.user, nowdate()),
	)
	frappe.db.commit()
	return {
		"da_co": 0, "item_code": item_code, "dvt": dvt, "he_so": hs,
		"dvt_kho": dvt_kho,
		"loi_nhan": 'Đã khai: 1 %s = %s %s. Từ giờ hoá đơn ghi "%s" là hệ hiểu đúng.'
		% (dvt, hs, dvt_kho, dvt),
	}


def _mst_cua_to(doc):
	"""Ma so thue cua nha cung cap tren mot to hoa don. '' neu chiu.

	Doc tren chinh to truoc, roi moi lui ve ho so Nha cung cap: to hoa don
	dien tu mang MST cua ban goc, con ho so co the da bi sua tay.
	"""
	mst = str(doc.get("tax_id") or "").strip()
	if mst:
		return mst
	return str(frappe.db.get_value("Supplier", doc.get("supplier"), "tax_id") or "").strip()


@frappe.whitelist()
def goi_y_mon(name, dong):
	"""Mon nao co the la dong hoa don nay. CHI DOC.

	VI SAO XEP THEO PHIEU NHAP CHU KHONG THEO TEN
	--------------------------------------------------------------------
	Ten hang cua nha cung cap va ten Mon cua minh gan nhu khong bao gio
	giong nhau. Hoa don 6921 cua An Phu ghi "CHERRY CALADA S10_5K/T", ben
	minh goi la "Trai cherry tuoi, Thung 5 kg". So chuoi kieu gi cung
	khong ra.

	Nhung co mot manh moi chac hon ten: HANG DA VE KHO ROI. Phieu nhap
	chua thanh toan cua chinh nha cung cap do, trong cung khoang ngay, gan
	nhu chac chan la lo hang cua to hoa don nay. Nen dua thang danh sach
	do ra cho nguoi chon, thay vi bat ho go tim trong ba nghin Mon.

	Van co o tim cho truong hop hang khong qua kho. Day chi la xep cai kha
	nang cao nhat len tren.
	"""
	_kiem_quyen()
	doc = frappe.get_doc("Purchase Invoice", name)
	idx = cint(dong)
	d = None
	for x in doc.items:
		if x.idx == idx or x.name == str(dong):
			d = x
			break
	if not d:
		frappe.throw("Không tìm thấy dòng %s trên hoá đơn %s." % (dong, name))

	ten_ncc = (d.item_name or "").strip()
	mst = _mst_cua_to(doc)

	# 1. Mon nam tren phieu nhap chua thanh toan cua chinh nha cung cap nay.
	ra, da_co = [], set()
	for p in _phieu_ung_vien(doc):
		for r in _dong_pnk(p["name"]):
			if r["item_code"] in da_co:
				continue
			da_co.add(r["item_code"])
			ra.append({
				"item_code": r["item_code"],
				"item_name": r["item_name"],
				"vi_sao": "Có trên phiếu nhập %s ngày %s" % (p["name"], p.get("posting_date") or ""),
				"sl_pnk": flt(r.get("qty")),
				"dvt_pnk": r.get("uom") or "",
				"uu_tien": 1,
			})

	# 2. Mon ma chinh nha cung cap nay tung duoc anh xa toi. Hang khong qua
	#    kho (phi ship, dich vu) khong bao gio nam o muc 1, phai co duong nay.
	if mst:
		for m in frappe.get_all(
			"MInvoice NCC Map",
			filters={"supplier_mst": mst, "item_code": ["is", "set"]},
			fields=["item_code", "ten_ncc"],
			limit_page_length=60,
		):
			if m.item_code in da_co:
				continue
			da_co.add(m.item_code)
			ra.append({
				"item_code": m.item_code,
				"item_name": frappe.db.get_value("Item", m.item_code, "item_name") or m.item_code,
				"vi_sao": "Nhà cung cấp này từng gửi \"%s\"" % (m.ten_ncc or ""),
				"sl_pnk": 0.0,
				"dvt_pnk": "",
				"uu_tien": 2,
			})

	ra.sort(key=lambda x: (x["uu_tien"], x["item_name"]))
	return {
		"name": name, "idx": idx, "ten_ncc": ten_ncc, "mst": mst,
		"dvt_ncc": (d.get("uom") or ""),
		"goi_y": ra[:40],
	}


def _phieu_ung_vien(doc):
	"""Phieu nhap chua thanh toan het cua chinh nha cung cap tren to nay."""
	rows = frappe.get_all(
		"Purchase Receipt",
		filters={"supplier": doc.supplier, "docstatus": 1, "company": doc.company},
		fields=["name", "posting_date", "per_billed"],
		order_by="posting_date desc",
		limit_page_length=40,
	)
	return [r for r in rows if flt(r.get("per_billed")) < 99.99]


@frappe.whitelist()
def gan_ma_hang(name, dong, item_code, nho=1):
	"""Gan mot Mon vao dong hoa don chua co ma hang, va NHO cho lan sau.

	ANH VIET 31/08/2026
	--------------------------------------------------------------------
	*"Mong em phai fix triet de."*

	Triet de o day khong phai la sua mot dong. Ngay 31/08 he co 9.985 tren
	11.351 dong hoa don khong co ma hang, tren 2.612 to. Sua tay tung dong
	la lam mai khong het.

	Nen ham nay lam HAI viec trong mot lan bam:

	  1. Gan Mon vao dong nay, va nan lai don vi cho dung bang quy doi cua
	     Mon do. Dong chua co ma hang thi don vi dang la don vi tho cua nha
	     cung cap voi he so 1 - chinh cai duong ha ngam sinh ra lech don vi.
	  2. GHI NHO: ten hang do cua nha cung cap do ung voi Mon nay. Lan sau
	     ho gui hoa don co dung ten do la may tu nhan, khong ai phai bam
	     nua.

	Viec 2 moi la cai chua goc. Moi lan nguoi ta bam nut la mot cai ten
	khong bao giờ phai bam lai.

	KHONG dong toi so luong va don gia. Tien tren to hoa don khong xe dich
	mot dong nao - do la so cua ban goc da gui co quan thue.
	"""
	_kiem_quyen()
	if not _lam_duoc():
		frappe.throw("Chỉ kế toán hoặc thu mua mới gắn mã hàng cho dòng hoá đơn được.")

	item_code = str(item_code or "").strip()
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw("Không tìm thấy món %s." % item_code)

	doc = frappe.get_doc("Purchase Invoice", name)
	if doc.docstatus != 0:
		frappe.throw("Hoá đơn %s đã ghi sổ rồi, không gắn mã hàng được." % name)

	idx = cint(dong)
	d = None
	for x in doc.items:
		if x.idx == idx or x.name == str(dong):
			d = x
			break
	if not d:
		frappe.throw("Không tìm thấy dòng %s trên hoá đơn %s." % (dong, name))
	if (d.get("item_code") or "").strip():
		frappe.throw("Dòng %d đã có mã hàng %s rồi." % (d.idx, d.item_code))

	ten_ncc = (d.item_name or "").strip()
	dvt_ncc = (d.get("uom") or "").strip()

	# NAN LAI DON VI. Don vi tho cua nha cung cap ("BAG", "TRAI") duoc dich
	# sang ten cua minh roi tra bang quy doi cua Mon. Tra khong ra thi lui ve
	# don vi kho he so 1 - y het duong dung chung tu, de hai cho khong bao
	# gio xu khac nhau (QT-19).
	dvt_kho = frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"
	dung_uom, he_so_moi = dvt_kho, 1.0
	for ten_thu in [dvt_ncc, dvt_mua.goi_y_don_vi(dvt_ncc)]:
		if not ten_thu:
			continue
		hs = dvt_mua.he_so_cua_mon(item_code, ten_thu)
		if hs:
			dung_uom, he_so_moi = ten_thu, hs
			break
		if dvt_mua.cung_don_vi(ten_thu, dvt_kho):
			dung_uom, he_so_moi = dvt_kho, 1.0
			break

	d.item_code = item_code
	d.uom = dung_uom
	d.conversion_factor = he_so_moi
	if not (d.get("stock_uom") or "").strip():
		d.stock_uom = dvt_kho
	doc.flags.ignore_permissions = True
	doc.save()

	# GHI NHO cho lan sau. Day moi la phan chua goc.
	da_nho = 0
	mst = _mst_cua_to(doc)
	if cint(nho) and mst and ten_ncc:
		cu = frappe.db.get_value(
			"MInvoice NCC Map", {"supplier_mst": mst, "ten_ncc": ten_ncc[:140]}, "name"
		)
		if not cu:
			m = frappe.get_doc({
				"doctype": "MInvoice NCC Map",
				"supplier_mst": mst,
				"ten_ncc": ten_ncc[:140],
				"item_code": item_code,
			})
			m.flags.ignore_permissions = True
			m.insert(ignore_permissions=True)
			da_nho = 1
		elif not (frappe.db.get_value("MInvoice NCC Map", cu, "item_code") or "").strip():
			frappe.db.set_value("MInvoice NCC Map", cu, "item_code", item_code)
			da_nho = 1

	frappe.db.commit()
	return {
		"name": doc.name, "idx": d.idx, "item_code": item_code,
		"dvt": dung_uom, "he_so": he_so_moi, "da_nho": da_nho,
		"chua_khai_don_vi": 1 if (dvt_ncc and not dvt_mua.cung_don_vi(dvt_ncc, dung_uom)
			and abs(he_so_moi - 1.0) < 1e-9) else 0,
		"loi_nhan": ("Đã gắn món cho dòng %d." % d.idx)
		+ (" Từ giờ nhà cung cấp này gửi \"%s\" là máy tự nhận." % ten_ncc if da_nho else "")
		+ (" Đơn vị \"%s\" món này chưa khai nên tạm để %s, nhớ khai đơn vị."
			% (dvt_ncc, dung_uom)
			if (dvt_ncc and not dvt_mua.cung_don_vi(dvt_ncc, dung_uom)
				and abs(he_so_moi - 1.0) < 1e-9) else ""),
	}


@frappe.whitelist()
def ghi_so_thang(name):
	"""Ghi so mot to hoa don KHONG noi phieu nhap nao.

	CHI DUNG MAT NUT GHI SO (anh Viet bao 31/08/2026)
	--------------------------------------------------------------------
	*"Ben chi Dung noi bong bi mat nut ghi so hoa don du truoc day co."*

	Khong phai bong nhien, va khong phai xung dot ban. Man Doi chieu chi ve
	KHOI NUT khi tim ra it nhat mot phieu nhap goi y:

	    if (kq.lam_duoc && gy.length) { ... }

	Cau do co tu lan tach tep, truoc ban v362. To nao khong co phieu nhap
	nao de goi y thi ca cum nut bien mat, ke ca nut ghi so. Ke toan mo to
	ra, doc cau "nho ke toan ghi so thang to nay", roi khong tim thay nut
	nao de lam viec do.

	Ngay 31/08 nhom "Khong thay phieu nhap nao" co 618 to. Nghia la chi Dung
	gap dung cai ngo cut nay 618 lan. Va phan lon so do la hoa don KHONG BAO
	GIO co phieu nhap: xang dau, Grab, phi dich vu. Chung khong phai hang ton
	kho nen khong co gi de noi ca.

	HANG RAO VAN CON, VA DUNG CHO
	--------------------------------------------------------------------
	Ghi so thang khong co nghia la ghi bua. Dong HANG THAT ma khong co phieu
	nhap thi gia von sai, nen van chan. Chi tha nhung dong khong qua kho -
	dung phep xet `_khong_qua_kho` ma buoc noi phieu dang dung, de hai cho
	khong bao gio xu khac nhau (QT-19).
	"""
	_kiem_quyen()
	if not _ghi_so_duoc():
		frappe.throw(
			"Chỉ kế toán mới ghi sổ hoá đơn mua được. Nhờ kế toán ghi sổ giúp tờ này."
		)

	doc = frappe.get_doc("Purchase Invoice", name)
	if doc.docstatus != 0:
		frappe.throw("Hoá đơn %s không còn ở dạng nháp." % name)

	# Dong hang that ma chua noi phieu: chan. Dong dich vu, phi ship, van
	# phong pham thi cho di.
	ket = []
	for d in doc.items:
		if (d.get("purchase_receipt") or "").strip():
			continue
		if _khong_qua_kho(d.get("item_code")):
			continue
		ket.append(
			"Dòng %d: món %s là hàng qua kho mà chưa nối phiếu nhập. Nối phiếu "
			"trước rồi ghi sổ, ghi sổ luôn thì giá vốn sai."
			% (d.idx, d.item_name or d.item_code)
		)
	if ket:
		frappe.throw("Chưa ghi sổ thẳng được:\n\n" + "\n".join(ket))

	doc.flags.ignore_permissions = True
	doc.submit()
	frappe.db.commit()
	return {
		"name": doc.name, "da_ghi_so": 1, "trang_thai": doc.status,
		"loi_nhan": "Đã ghi sổ tờ %s. Tờ này không có dòng hàng qua kho nên "
		"không cần nối phiếu nhập." % doc.name,
	}
