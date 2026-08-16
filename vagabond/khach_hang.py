# -*- coding: utf-8 -*-
"""Danh sach khach hang de tra cuu: phan theo DANG khach (si hay le) va
HANG khach (anh Viet 11/08/2026).

Hang xet theo chi tieu: EXPLORER thap nhat, roi VOYAGER, roi VAGABONDER.
Hai hang gan tay: FAMILY giam 20% cho so dien thoai nhan vien, AMBASSADOR
giam vinh vien 10%.

Muc chi tieu tung hang nam trong doctype "Vagabond Hang Khach" chu khong
nhet trong ma - anh Viet chot con so luc nao thi sua o do, khong phai doi
deploy.
"""

import frappe
from frappe.utils import add_months, cint, flt, getdate, nowdate

from vagabond.ban_hang import _kiem_quyen
from vagabond.lib import sdt

# Sua bang hang, cong tru diem tay, chuyen hang hang loat: ba viec nay deu
# dung thang vao quyen loi cua khach nen chi quan ly moi lam duoc.
QUYEN_SUA_HANG = {"System Manager", "Sales Manager", "Accounts Manager", "VGB - Quản lý khuyến mãi"}

# Nhung ban ghi Customer KHONG phai mot nguoi that, ma la mot cai gio dung
# chung cho khach vang lai khong xung ten. Chung phai nam ngoai moi thu
# lien quan den hang va diem.
#
# Bat duoc 12/08/2026 khi chay thu xet lai: "Khach le Online" gom 140 trieu
# va "Khach ban le" gom 103 trieu, ca hai deu se len VAGABONDER. Nghia la
# moi don le vang lai bong nhien huong quyen loi hang cao nhat, va toan bo
# diem cua ca tiem don vao mot cho khong cua ai.
KHACH_GOP = {"Khách lẻ Online", "Khách bán lẻ"}


def la_khach_gop(ma):
	"""Ban ghi nay la gio dung chung hay la mot khach that."""
	from vagabond.ban_hang import KHACH_LE

	m = (ma or "").strip()
	return (not m) or m == KHACH_LE or m in KHACH_GOP

# Nhom khach ben ERPNext nao duoc coi la khach SI. Nhan dien theo TEN nhom
# chu khong liet ke cung, vi ke toan hay them nhom moi (hien co "Khach si
# B2B", truoc do la "Khach si"). Con lai la khach le.
def _la_si(nhom):
	n = (nhom or "").strip().lower()
	return ("sỉ" in n) or ("si b2b" in n) or ("wholesale" in n) or ("b2b" in n)


def _nhom_si():
	"""Danh sach ten nhom khach duoc coi la si, doc that tu danh muc."""
	try:
		ds = frappe.get_all("Customer Group", fields=["name"], limit_page_length=0)
	except Exception:
		return []
	return [r["name"] for r in ds if _la_si(r["name"])]


@frappe.whitelist()
def ds_hang():
	"""Bang hang khach dang cau hinh, xep tu thap len cao."""
	_kiem_quyen()
	try:
		ds = frappe.get_all(
			"Vagabond Hang Khach",
			filters={"bat": 1},
			# "anh" la anh the thanh vien, app deo len chip hang o man Danh
			# muc khach hang. "tich_diem" de man do con noi duoc hang nay
			# tich bao nhieu ma khong phai goi them mot luot nua.
			fields=[
				"name", "ten_hang", "thu_tu", "loai", "giam_gia", "tich_diem",
				"chi_tieu_tu", "so_thang_xet", "mo_ta", "anh",
			],
			order_by="thu_tu asc",
			limit_page_length=0,
		)
	except Exception:
		return {"hang": []}
	return {"hang": ds}


def _chi_tieu(ds_khach, so_thang=12):
	"""Tong tien da mua cua tung khach trong ky xet."""
	if not ds_khach:
		return {}
	tu = add_months(getdate(nowdate()), -abs(int(so_thang or 12)))
	# Gom o MAY CHU chu khong keo tung dong hoa don ve Python. Xet lai hang
	# la chay tren CA 1.545 khach: 12 thang hoa don cua ho la vai chuc ngan
	# dong, keo het ve la ton bo nho vo ich va man hinh cho rat lau.
	# Bo hoa don da danh dau huy: tien do khong vao tui tiem nen khong duoc
	# tinh la chi tieu cua khach.
	rows = frappe.db.sql(
		"""
		select customer, sum(grand_total) tien, count(*) so_don,
		       max(posting_date) gan_nhat
		from `tabSales Invoice`
		where docstatus = 1 and posting_date >= %s and ifnull(vgb_huy, 0) = 0
		group by customer
		""",
		(str(tu),),
		as_dict=True,
	)
	can = set(ds_khach)
	ra = {}
	for r in rows:
		if r.get("customer") not in can:
			continue
		ra[r["customer"]] = {
			"tien": flt(r.get("tien")),
			"so_don": int(r.get("so_don") or 0),
			"gan_nhat": str(r.get("gan_nhat") or ""),
		}

	# Cong them phan da tieu ben Fabi (anh Viet chot 12/08/2026: khach giu
	# duoc cong suc da tieu ben he cu, khong bi tut hang khi minh doi he).
	# So nay la mot MOC TICH LUY dung yen mot cho, khong het han theo ky xet
	# nhu doanh so 12 thang - nen phai cong rieng chu khong gop vao cau
	# truy van tren.
	try:
		cu = frappe.db.sql(
			"""
			select name, ifnull(vgb_chi_tieu_cu, 0) tien
			from `tabCustomer`
			where ifnull(vgb_chi_tieu_cu, 0) > 0
			""",
			as_dict=True,
		)
	except Exception:
		# Chua tao truong thi coi nhu chua ai co chi tieu cu, khong duoc
		# lam hong man danh sach khach.
		cu = []
	for r in cu:
		if r["name"] not in can:
			continue
		o = ra.setdefault(r["name"], {"tien": 0.0, "so_don": 0, "gan_nhat": ""})
		o["tien"] = flt(o["tien"]) + flt(r["tien"])
		o["tieu_cu"] = flt(r["tien"])
	return ra


@frappe.whitelist()
def ds_khach(tu_khoa="", dang="", hang=""):
	"""Danh sach khach hang de tra cuu, kem chi tieu va hang.

	Chi tieu tinh trong 12 thang gan nhat theo hoa don DA GHI SO - don con
	o ban nhap chua phai la tien that.
	"""
	_kiem_quyen()
	q = (tu_khoa or "").strip()
	# Loc phai chay o MAY CHU truoc khi cat bot, khong thi khach si nam
	# cuoi bang chu cai se bien mat: co 1545 khach ma chi tai 500 cai dau
	# thi 5 khach si B2B khong bao gio hien ra (bat duoc 11/08/2026).
	loc = {"disabled": 0}
	nhom_si = _nhom_si()
	if dang == "si":
		if not nhom_si:
			return {"khach": [], "tong_tien": 0, "so_si": 0, "so_le": 0, "tong_so": 0}
		loc["customer_group"] = ["in", nhom_si]
	elif dang == "le" and nhom_si:
		loc["customer_group"] = ["not in", nhom_si]
	if hang == "_chua":
		loc["vgb_hang"] = ["in", ["", None]]
	elif hang:
		loc["vgb_hang"] = hang
	doi = {
		"doctype": "Customer",
		"filters": loc,
		"fields": [
			"name", "customer_name", "customer_group", "tax_id",
			"mobile_no", "territory", "creation",
		],
		"order_by": "customer_name asc",
		"limit_page_length": 400,
	}
	if q:
		doi["or_filters"] = {
			"name": ["like", "%" + q + "%"],
			"customer_name": ["like", "%" + q + "%"],
			"tax_id": ["like", "%" + q + "%"],
			"mobile_no": ["like", "%" + q + "%"],
		}
	try:
		tong_so = frappe.db.count("Customer", loc)
	except Exception:
		tong_so = 0
	ds = frappe.get_all(**doi)

	# Truong hang nam o Custom Field tren Customer. Doc rieng de neu chua
	# tao field thi man hinh van chay, chi la chua ai co hang.
	hang_map = {}
	try:
		for r in frappe.get_all(
			"Customer",
			filters={"name": ["in", [x["name"] for x in ds]]},
			fields=["name", "vgb_hang"],
			limit_page_length=0,
		):
			if r.get("vgb_hang"):
				hang_map[r["name"]] = r["vgb_hang"]
	except Exception:
		hang_map = {}

	ct = _chi_tieu([r["name"] for r in ds])
	bang_hang = {h["name"]: h for h in (ds_hang().get("hang") or [])}

	ra = []
	for r in ds:
		o = ct.get(r["name"]) or {}
		h = hang_map.get(r["name"]) or ""
		hd = bang_hang.get(h) or {}
		ra.append(
			{
				"ma": r["name"],
				"ten": r.get("customer_name") or r["name"],
				"nhom": r.get("customer_group") or "",
				"si": 1 if _la_si(r.get("customer_group")) else 0,
				"mst": r.get("tax_id") or "",
				"dt": r.get("mobile_no") or "",
				"hang": h,
				"giam": flt(hd.get("giam_gia")),
				"tien": flt(o.get("tien")),
				"so_don": int(o.get("so_don") or 0),
				"gan_nhat": o.get("gan_nhat") or "",
			}
		)

	# Khach chi nhieu nhat len dau - do la khach can cham nhat.
	ra.sort(key=lambda x: -x["tien"])
	try:
		so_si = frappe.db.count("Customer", {"disabled": 0, "customer_group": ["in", nhom_si]}) if nhom_si else 0
		so_tat = frappe.db.count("Customer", {"disabled": 0})
	except Exception:
		so_si, so_tat = 0, len(ra)
	return {
		"khach": ra,
		"tong_tien": sum(x["tien"] for x in ra),
		"so_si": so_si,
		"so_le": max(0, so_tat - so_si),
		"tong_so": tong_so,
		"da_tai": len(ra),
	}


@frappe.whitelist()
def dat_hang(khach=None, hang=None):
	"""Gan hang cho mot khach. Hang gan tay (FAMILY, AMBASSADOR) chi quan
	ly moi dat duoc, nen di qua ham nay chu khong sua thang tren Desk."""
	_kiem_quyen()
	khach = (khach or "").strip()
	hang = (hang or "").strip().upper()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	if la_khach_gop(khach):
		frappe.throw(
			"\"%s\" là giỏ dùng chung cho khách vãng lai, không phải một người "
			"thật nên không gán hạng được. Muốn khách này có hạng thì lập một "
			"khách hàng riêng cho họ." % khach
		)
	if hang and not frappe.db.exists("Vagabond Hang Khach", hang):
		frappe.throw("Không có hạng %s trong danh mục." % hang)
	frappe.db.set_value("Customer", khach, "vgb_hang", hang or None)
	frappe.db.commit()
	return {"khach": khach, "hang": hang}


@frappe.whitelist()
def goi_y_hang(khach=None):
	"""Hang ma khach DANG DUOC HUONG theo chi tieu, de quan ly doi chieu
	voi hang dang gan. Khong tu doi hang - doi hang la viec cua nguoi."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		return {}
	bang = [
		h for h in (ds_hang().get("hang") or [])
		if (h.get("loai") or "Theo chi tieu") == "Theo chi tieu"
	]
	if not bang:
		return {"hang": "", "tien": 0}
	so_thang = max([int(h.get("so_thang_xet") or 12) for h in bang] or [12])
	ct = _chi_tieu([khach], so_thang).get(khach) or {}
	tien = flt(ct.get("tien"))
	dat = ""
	for h in sorted(bang, key=lambda x: flt(x.get("chi_tieu_tu"))):
		if tien >= flt(h.get("chi_tieu_tu")):
			dat = h["name"]
	return {"hang": dat, "tien": tien, "so_thang": so_thang}


# ---------------------------------------------------------------- diem tich luy
#
# 1 diem = 1 dong, hoc theo Fabi cho khach khoi phai doi thoi quen. Hang nao
# tich bao nhieu phan tram thi khai o "Vagabond Hang Khach.tich_diem".
#
# Ghi thanh SO chu khong giu moi mot con so du tren Customer: diem la tien
# cua khach, mat mot cuc ma khong biet no di dau thi khong ai giai trinh
# duoc voi khach. So du chi la ban tong hop, lech luc nao thi tinh lai tu so.

SO_DIEM = "Vagabond So Diem"


def _hang_cua(khach):
	"""Cau hinh hang cua mot khach, lay ca hang dang tat de doc hoa don cu."""
	h = frappe.db.get_value("Customer", khach, "vgb_hang")
	if not h:
		return None
	try:
		return frappe.db.get_value(
			"Vagabond Hang Khach", h, ["name", "tich_diem", "giam_gia"], as_dict=True
		)
	except Exception:
		return None


def _tinh_lai_so_du(khach):
	"""Cong lai toan bo so va ghi de so du tren Customer."""
	tong = frappe.db.sql(
		"select sum(diem) from `tab%s` where khach = %%s" % SO_DIEM, (khach,)
	)
	so = flt((tong or [[0]])[0][0])
	try:
		frappe.db.set_value("Customer", khach, "vgb_diem", so)
	except Exception:
		pass
	return so


def _ghi_so_diem(khach, diem, loai, hoa_don=None, ghi_chu=""):
	"""Ghi mot but vao so diem roi tinh lai so du."""
	diem = flt(diem)
	if not khach or not diem:
		return None
	doc = frappe.get_doc(
		{
			"doctype": SO_DIEM,
			"khach": khach,
			"ngay": frappe.utils.now_datetime(),
			"loai": loai,
			"diem": diem,
			"hoa_don": hoa_don,
			"ghi_chu": (ghi_chu or "")[:500],
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	_tinh_lai_so_du(khach)
	return doc.name


def _khach_that(si):
	"""Khach tich diem duoc, hay la mot gio dung chung. Xem KHACH_GOP."""
	kh = (si.get("customer") or "").strip()
	return "" if la_khach_gop(kh) else kh


def diem_cho_don(tien, ty_le):
	"""So diem mot don duoc tich. THUAN: hai so vao, mot so ra.

	Tach rieng vi man Chi tiet don phai BAO TRUOC cho khach so diem se
	duoc, ma hoa don thi mai moi ghi so. Neu man hinh tu tinh mot phep con
	hook cong diem tinh mot phep khac thi som muon hai con so lech nhau, va
	nguoi chiu la khach dung o quay nghe bao mot dang roi nhan mot dang.
	"""
	ty_le = flt(ty_le)
	if ty_le <= 0:
		return 0
	return int(round(flt(tien) * ty_le / 100.0))


def _da_tich(hoa_don, loai="Tich tu hoa don"):
	try:
		return frappe.db.exists(SO_DIEM, {"hoa_don": hoa_don, "loai": loai})
	except Exception:
		return None


def cong_diem_hoa_don(doc, method=None):
	"""Hook on_submit cua Hoa don ban hang: cong diem theo hang cua khach."""
	try:
		if cint(doc.get("vgb_huy")):
			return
		kh = _khach_that(doc)
		if not kh:
			return
		if _da_tich(doc.name):
			return
		hang = _hang_cua(kh)
		ty_le = flt((hang or {}).get("tich_diem"))
		if ty_le <= 0:
			return
		diem = diem_cho_don(doc.get("grand_total"), ty_le)
		if diem <= 0:
			return
		_ghi_so_diem(
			kh, diem, "Tich tu hoa don", doc.name,
			"Hạng %s, tích %s%% của %s đ" % ((hang or {}).get("name"), ty_le, doc.get("grand_total")),
		)
	except Exception:
		# Tich diem KHONG duoc lam hong viec ghi so hoa don. Hong thi ghi
		# nhat ky roi thoi, chay lai bang nut "Tinh lai diem" duoc.
		frappe.log_error(frappe.get_traceback(), "khach_hang: cong diem loi")


def hoan_diem_hoa_don(doc, method=None):
	"""Hook on_cancel: huy hoa don thi rut lai dung so diem da cong."""
	try:
		kh = _khach_that(doc)
		if not kh:
			return
		if _da_tich(doc.name, "Hoan lai khi huy hoa don"):
			return
		da = frappe.db.sql(
			"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s" % SO_DIEM,
			(doc.name, "Tich tu hoa don"),
		)
		diem = flt((da or [[0]])[0][0])
		if diem <= 0:
			return
		_ghi_so_diem(kh, -diem, "Hoan lai khi huy hoa don", doc.name, "Hoá đơn bị huỷ")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "khach_hang: hoan diem loi")


@frappe.whitelist()
def so_diem(khach=None, so_dong=50):
	"""So du va cac but gan nhat cua mot khach."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		return {"so_du": 0, "but": []}
	but = frappe.get_all(
		SO_DIEM,
		filters={"khach": khach},
		fields=["name", "ngay", "loai", "diem", "hoa_don", "ghi_chu", "nguoi"],
		order_by="ngay desc",
		limit_page_length=max(1, min(200, cint(so_dong) or 50)),
	)
	return {"so_du": _tinh_lai_so_du(khach), "but": but}


@frappe.whitelist()
def sua_diem(khach=None, diem=None, ghi_chu=None):
	"""Cong hoac tru diem tay. Bat buoc ghi ly do."""
	_kiem_quyen()
	if not QUYEN_SUA_HANG & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý mới cộng trừ điểm tay được.")
	khach = (khach or "").strip()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	d = flt(diem)
	if not d:
		frappe.throw("Số điểm phải khác 0.")
	if not (ghi_chu or "").strip():
		frappe.throw("Phải ghi lý do thì sau này còn giải trình với khách được.")
	_ghi_so_diem(khach, d, "Dieu chinh tay", None, ghi_chu)
	return so_diem(khach)


# ------------------------------------------------------- man Cai dat hang khach

LOAI_HANG = ["Theo chi tieu", "Gan tay"]


@frappe.whitelist()
def cai_dat_hang():
	"""Bang hang day du cho man Cai dat, ke ca hang dang tat."""
	_kiem_quyen()
	ds = frappe.get_all(
		"Vagabond Hang Khach",
		fields=[
			"name", "ten_hang", "thu_tu", "loai", "giam_gia", "tich_diem",
			"chi_tieu_tu", "so_thang_xet", "bat", "mo_ta", "anh",
		],
		order_by="thu_tu asc, ten_hang asc",
		limit_page_length=0,
	)
	dem = {}
	try:
		for r in frappe.db.sql(
			"select ifnull(vgb_hang,'') h, count(*) n from `tabCustomer` "
			"where ifnull(disabled,0) = 0 group by ifnull(vgb_hang,'')",
			as_dict=True,
		):
			dem[r["h"]] = r["n"]
	except Exception:
		pass
	for d in ds:
		d["so_khach"] = dem.get(d["name"], 0)
	return {
		"hang": ds,
		"chua_xep": dem.get("", 0),
		"loai": LOAI_HANG,
		"sua_duoc": 1 if QUYEN_SUA_HANG & set(frappe.get_roles()) else 0,
	}


def _kiem_hang(ra):
	if not ra:
		frappe.throw("Phải còn ít nhất một hạng.")
	ten = {}
	theo_ct = []
	for d in ra:
		t = str(d.get("ten_hang") or "").strip()
		if not t:
			frappe.throw("Có hạng chưa đặt tên.")
		if t in ten:
			frappe.throw("Hạng \"%s\" bị trùng tên." % t)
		ten[t] = 1
		if flt(d.get("giam_gia")) < 0 or flt(d.get("giam_gia")) > 100:
			frappe.throw("Giảm giá của \"%s\" phải trong khoảng 0 đến 100%%." % t)
		# Tich diem 100% nghia la ban mot dong tang lai mot dong. Gan nhu
		# chac chan la go nham dau phay, chan lai con hon de mot dem chay
		# job cong het diem cho ca ngan khach.
		if flt(d.get("tich_diem")) < 0 or flt(d.get("tich_diem")) > 50:
			frappe.throw(
				"Tích điểm của \"%s\" phải trong khoảng 0 đến 50%%. Ghi %s%% là "
				"mỗi hoá đơn tặng lại gần hết tiền hàng." % (t, flt(d.get("tich_diem")))
			)
		if str(d.get("loai") or "Theo chi tieu") == "Theo chi tieu":
			theo_ct.append((flt(d.get("chi_tieu_tu")), t))
	if not theo_ct:
		frappe.throw(
			"Phải còn ít nhất một hạng xét theo chi tiêu, không thì không ai "
			"lên hạng được nữa."
		)
	# Hai hang cung mot nguong thi khach dat nguong do roi may khong biet
	# xep vao hang nao - va no se xep khac nhau moi lan chay.
	moc = {}
	for tien, t in theo_ct:
		if tien in moc:
			frappe.throw(
				"Hạng \"%s\" và \"%s\" cùng mức chi tiêu %s đ. Đặt hai mốc khác "
				"nhau thì máy mới biết xếp khách vào đâu." % (moc[tien], t, tien)
			)
		moc[tien] = t


@frappe.whitelist()
def luu_hang(hang=None):
	"""Luu ca bang hang tu man Cai dat."""
	_kiem_quyen()
	if not QUYEN_SUA_HANG & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý mới sửa được bảng hạng thành viên.")
	if isinstance(hang, str):
		hang = frappe.parse_json(hang or "[]")
	ra = [d for d in (hang or []) if str(d.get("ten_hang") or "").strip()]
	_kiem_hang(ra)

	cu = {d["name"]: d for d in frappe.get_all("Vagabond Hang Khach", fields=["name"], limit_page_length=0)}
	giu = set()
	for i, d in enumerate(ra):
		t = str(d["ten_hang"]).strip()
		giu.add(t)
		gt = {
			"ten_hang": t,
			"thu_tu": cint(d.get("thu_tu") or (i + 1)),
			"loai": str(d.get("loai") or "Theo chi tieu"),
			"giam_gia": flt(d.get("giam_gia")),
			"tich_diem": flt(d.get("tich_diem")),
			"chi_tieu_tu": flt(d.get("chi_tieu_tu")),
			"so_thang_xet": cint(d.get("so_thang_xet") or 12),
			"bat": 1 if cint(d.get("bat") if d.get("bat") is not None else 1) else 0,
			"mo_ta": str(d.get("mo_ta") or "").strip(),
			# Anh the thanh vien (anh Viet 12/08/2026): thay day bieu tuong
			# bang dung file the cua tung hang cho de phan biet.
			"anh": str(d.get("anh") or "").strip(),
		}
		if t in cu:
			doc = frappe.get_doc("Vagabond Hang Khach", t)
			doc.update(gt)
			doc.flags.ignore_permissions = True
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc(dict(doctype="Vagabond Hang Khach", **gt))
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)

	# Hang bi bo khoi bang: chi cho bo khi khong con khach nao dang deo.
	for t in cu:
		if t in giu:
			continue
		n = frappe.db.count("Customer", {"vgb_hang": t})
		if n:
			frappe.throw(
				"Hạng \"%s\" đang có %d khách nên không bỏ được. Muốn ngừng dùng "
				"thì tắt nó đi, khách cũ vẫn giữ nguyên hạng." % (t, n)
			)
		frappe.delete_doc("Vagabond Hang Khach", t, ignore_permissions=True, force=1)

	frappe.db.commit()
	return cai_dat_hang()


# ----------------------------------------------------- xet lai hang hang loat


def _bang_theo_chi_tieu():
	"""Hang xet theo chi tieu, dang bat, sap tu nguong thap len cao."""
	ds = frappe.get_all(
		"Vagabond Hang Khach",
		filters={"bat": 1, "loai": "Theo chi tieu"},
		fields=["name", "chi_tieu_tu", "so_thang_xet", "thu_tu"],
		limit_page_length=0,
	)
	return sorted(ds, key=lambda x: flt(x.get("chi_tieu_tu")))


def _gan_tay():
	"""Hang gan tay: may KHONG duoc tu doi cua nhung khach nay."""
	return {
		d["name"]
		for d in frappe.get_all(
			"Vagabond Hang Khach", filters={"loai": "Gan tay"}, fields=["name"], limit_page_length=0
		)
	}


def _bang_co_chay_duoc(bang):
	"""Bang hang co du dieu kien de xet lai khong. Tra cau bao loi, hoac "".

	Bat duoc 12/08/2026: ca ba hang deu de nguong chi tieu 0, nghia la moi
	khach deu vuot nguong cua hang cao nhat. Bam xet lai luc do la 1.545
	khach cung len VAGABONDER huong giam 10% vinh vien, va khong co duong
	quay lai vi khong ai con biet hang cu cua tung nguoi la gi.
	"""
	moc = {}
	for h in bang:
		t = flt(h.get("chi_tieu_tu"))
		if t in moc:
			return (
				"Hạng \"%s\" và \"%s\" cùng mức chi tiêu %s đ nên máy không biết "
				"xếp khách vào đâu. Vào Cài đặt > Hạng thành viên đặt mốc cho từng "
				"hạng trước đã." % (moc[t], h["name"], int(t))
			)
		moc[t] = h["name"]
	if len([h for h in bang if flt(h.get("chi_tieu_tu")) > 0]) < 1:
		return (
			"Chưa hạng nào có mức chi tiêu lớn hơn 0. Chạy bây giờ là cả tiệm "
			"cùng lên hạng cao nhất. Vào Cài đặt > Hạng thành viên đặt mốc trước đã."
		)
	return ""


@frappe.whitelist()
def xet_lai(ap=0, so_khach=500):
	"""So hang dang deo voi hang dang duoc huong theo chi tieu.

	ap=0 chi tra ve danh sach de nguoi xem truoc. ap=1 moi thuc su doi.
	Khong bao gio dong toi khach dang deo hang GAN TAY: nhan vien, dai su,
	nguoi nha - may tu ha hang cua ho la mat mat that voi nguoi that.
	"""
	_kiem_quyen()
	ap = cint(ap)
	if ap and not QUYEN_SUA_HANG & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý mới chuyển hạng hàng loạt được.")

	bang = _bang_theo_chi_tieu()
	if not bang:
		return {"doi": [], "tong": 0, "da_ap": 0, "loi_nhac": "Chưa khai hạng nào xét theo chi tiêu."}
	loi = _bang_co_chay_duoc(bang)
	if loi:
		if ap:
			frappe.throw(loi)
		return {"doi": [], "tong": 0, "da_ap": 0, "loi_nhac": loi}
	so_thang = max([cint(h.get("so_thang_xet") or 12) for h in bang] or [12])
	tay = _gan_tay()

	khach = frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		fields=["name", "customer_name", "vgb_hang"],
		limit_page_length=0,
	)
	ct = _chi_tieu([k["name"] for k in khach], so_thang)

	doi = []
	for k in khach:
		if la_khach_gop(k["name"]):
			continue
		dang = (k.get("vgb_hang") or "").strip()
		if dang and dang in tay:
			continue
		tien = flt((ct.get(k["name"]) or {}).get("tien"))
		nen = ""
		for h in bang:
			if tien >= flt(h.get("chi_tieu_tu")):
				nen = h["name"]
		if not nen:
			nen = bang[0]["name"]
		# HA HANG MOI KY CHI MOT BAC (anh Viet chot 16/08/2026).
		#
		# Khong co chot nay thi mot khach VAGABONDER nghi mua nua nam se rot
		# thang ve EXPLORER trong mot dem, tut hai bac. Voi khach do thi do
		# la mot cu nga chu khong phai mot nhac nho, va ho se goi len hoi.
		# Len hang thi van len thang toi noi - khong ai phan nan vi len
		# nhanh qua.
		if dang and nen != dang and _xuong_tung_bac():
			b_dang, b_nen = _bac(bang, dang), _bac(bang, nen)
			if b_dang >= 0 and 0 <= b_nen < b_dang - 1:
				nen = bang[b_dang - 1]["name"]
		if nen == dang:
			continue
		doi.append(
			{
				"ma": k["name"],
				"ten": k.get("customer_name") or k["name"],
				"tu": dang,
				"sang": nen,
				"tien": tien,
				"len": 1 if not dang or _bac(bang, nen) > _bac(bang, dang) else 0,
			}
		)

	doi.sort(key=lambda x: -x["tien"])
	da_ap = 0
	if ap:
		for x in doi:
			frappe.db.set_value("Customer", x["ma"], "vgb_hang", x["sang"])
			da_ap += 1
		frappe.db.commit()
		_ghi_vet_hang("Xét lại hạng hàng loạt: đổi %d khách (chu kỳ %d tháng)" % (da_ap, so_thang))

	# Dem tren TOAN BO tap roi moi cat danh sach. Dem tren phan da cat thi
	# man hinh se noi "1.143 khach xuong hang" trong khi that ra ho dang tu
	# chua xep len EXPLORER - va nguoi doc se khong dam bam nut.
	so_len = len([x for x in doi if x["len"]])
	return {
		"doi": doi[: max(1, min(2000, cint(so_khach) or 500))],
		"tong": len(doi),
		"so_len": so_len,
		"so_xuong": len(doi) - so_len,
		"da_ap": da_ap,
		"so_thang": so_thang,
	}


def _xuong_tung_bac():
	"""Cai dat: ha hang moi ky chi mot bac. Mac dinh BAT."""
	try:
		from vagabond.lib import cfg

		v = cfg().get("ha_hang_tung_bac")
		return True if v is None else bool(cint(v))
	except Exception:
		return True


def _bac(bang, ten):
	for i, h in enumerate(bang):
		if h["name"] == ten:
			return i
	return -1


@frappe.whitelist()
def dat_hang_nhieu(khach=None, hang=None):
	"""Gan mot hang cho nhieu khach cung luc, tu man Danh sach khach hang."""
	_kiem_quyen()
	if not QUYEN_SUA_HANG & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý mới chuyển hạng hàng loạt được.")
	if isinstance(khach, str):
		khach = frappe.parse_json(khach or "[]")
	ds = [str(x).strip() for x in (khach or []) if str(x).strip()]
	if not ds:
		frappe.throw("Chưa chọn khách nào.")
	h = (hang or "").strip()
	if h and not frappe.db.exists("Vagabond Hang Khach", h):
		frappe.throw("Không có hạng %s trong danh mục." % h)
	xong = 0
	bo_qua = []
	for k in ds:
		if not frappe.db.exists("Customer", k):
			continue
		if la_khach_gop(k):
			bo_qua.append(k)
			continue
		frappe.db.set_value("Customer", k, "vgb_hang", h or None)
		xong += 1
	frappe.db.commit()
	_ghi_vet_hang("Chuyển %d khách sang hạng %s" % (xong, h or "(bỏ hạng)"))
	return {"xong": xong, "hang": h, "bo_qua": bo_qua}


def xet_lai_tu_dong():
	"""Chay hang dem: xet lai hang theo chi tieu cua ky.

	Anh Viet chot 11/08/2026 la BAT xet lai theo chu ky, khac Fabi (Fabi tat
	nen khach len hang la giu mai). Job nay chi dong vao hang xet theo chi
	tieu, khong dong vao hang gan tay.
	"""
	try:
		thu = xet_lai(ap=0, so_khach=1)
		if thu.get("loi_nhac"):
			# Khong nem loi: job dem nem loi moi dem la mot dong Error Log
			# giong het nhau, doc mai khong ai thay cai that su hong.
			frappe.log_error(thu["loi_nhac"], "khach_hang: chua xet lai hang duoc")
			return
		if not thu.get("tong"):
			return
		xet_lai(ap=1, so_khach=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "khach_hang: xet lai hang tu dong loi")


def _ghi_vet_hang(viec):
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


# ------------------------------------------------------ ho so mot khach hang
#
# Anh Viet 12/08/2026: bam vao mot khach thi khong thay thong tin gi ca. Man
# cu chi co ten, chi tieu va bang gan hang.
#
# Nay tra ve mot ho so day du de cham soc khach: lien he, lich su mua ben he
# nay va ben Fabi, tinh trang the thanh vien, va con bao nhieu tien nua thi
# len hang. Gom trong MOT luot goi chu khong de app hoi ba bon lan.


def _lien_he(khach):
	"""So dien thoai va email lay tu lien he chinh cua khach."""
	ma = frappe.db.get_value("Customer", khach, "customer_primary_contact")
	if not ma:
		# Chua tro lien he chinh thi tim qua Dynamic Link, van con doc duoc.
		rows = frappe.db.sql(
			"""
			select dl.parent ten
			from `tabDynamic Link` dl
			where dl.link_doctype = 'Customer' and dl.link_name = %s
			  and dl.parenttype = 'Contact'
			limit 1
			""",
			(khach,),
		)
		ma = rows[0][0] if rows else None
	if not ma:
		return {"ma": "", "sdt": "", "email": ""}
	d = frappe.db.get_value("Contact", ma, ["name", "mobile_no", "phone", "email_id"], as_dict=True) or {}
	return {
		"ma": d.get("name") or "",
		"sdt": sdt(d.get("mobile_no")) or sdt(d.get("phone")) or "",
		"email": (d.get("email_id") or "").strip(),
	}


@frappe.whitelist()
def ho_so(khach=None):
	"""Ho so day du cua mot khach, cho man Chi tiet khach hang tren app."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))

	truong = [
		"name", "customer_name", "customer_group", "territory", "tax_id",
		"gender", "mobile_no", "customer_primary_contact",
		"vgb_hang", "vgb_hang_tu", "vgb_diem", "vgb_sinh_nhat",
		"vgb_chi_tieu_cu", "vgb_so_don_cu", "vgb_lan_dau_cu", "vgb_lan_cuoi_cu",
		"vgb_ngay_dang_ky", "vgb_kenh_dang_ky", "vgb_zalo_id", "vgb_tags",
		"vgb_cua_hang_cu", "vgb_dia_chi_cu", "vgb_ma_cu", "disabled", "creation",
	]
	co = frappe.get_meta("Customer").get_valid_columns()
	d = frappe.db.get_value("Customer", khach, [t for t in truong if t in co], as_dict=True) or {}
	lh = _lien_he(khach)

	# Mua hang ben he nay. Tinh rieng chu khong dung _chi_tieu: o day can ca
	# hoa don gan nhat va tong so don, ma _chi_tieu chi tra trong ky xet.
	don = frappe.db.sql(
		"""
		select count(*) so_don, sum(grand_total) tien,
		       min(posting_date) lan_dau, max(posting_date) lan_cuoi
		from `tabSales Invoice`
		where customer = %s and docstatus = 1 and ifnull(vgb_huy, 0) = 0
		""",
		(khach,),
		as_dict=True,
	)
	don = (don or [{}])[0] or {}
	gan_day = frappe.get_all(
		"Sales Invoice",
		filters={"customer": khach, "docstatus": 1, "vgb_huy": 0},
		fields=["name", "posting_date", "grand_total", "custom_nguon", "vgb_quay", "vgb_pt_thanh_toan"],
		order_by="posting_date desc, creation desc",
		limit_page_length=20,
	)

	# The thanh vien: dang o hang nao, con bao nhieu tien nua thi len hang.
	bang = [
		h for h in (ds_hang().get("hang") or [])
		if (h.get("loai") or "Theo chi tieu") == "Theo chi tieu"
	]
	bang.sort(key=lambda x: flt(x.get("chi_tieu_tu")))
	so_thang = max([int(h.get("so_thang_xet") or 12) for h in bang] or [12])
	ct = _chi_tieu([khach], so_thang).get(khach) or {}
	tien_ky = flt(ct.get("tien"))
	dat = ""
	for h in bang:
		if tien_ky >= flt(h.get("chi_tieu_tu")):
			dat = h["name"]
	tiep, con_thieu = "", 0
	for h in bang:
		if flt(h.get("chi_tieu_tu")) > tien_ky:
			tiep = h["name"]
			con_thieu = flt(h.get("chi_tieu_tu")) - tien_ky
			break

	hang_dang = d.get("vgb_hang") or ""
	hd = {}
	if hang_dang:
		hd = frappe.db.get_value(
			"Vagabond Hang Khach", hang_dang,
			["name", "ten_hang", "giam_gia", "tich_diem", "loai", "anh", "mo_ta"],
			as_dict=True,
		) or {}

	return {
		"khach": d,
		"lien_he": lh,
		"la_gop": 1 if la_khach_gop(khach) else 0,
		"hang": hd,
		"the": {
			"tien_ky": tien_ky,
			"so_thang": so_thang,
			"hang_du_dieu_kien": dat,
			"hang_tiep": tiep,
			"con_thieu": con_thieu,
			"diem": flt(d.get("vgb_diem")),
		},
		"mua_next": {
			"so_don": int(don.get("so_don") or 0),
			"tien": flt(don.get("tien")),
			"lan_dau": str(don.get("lan_dau") or ""),
			"lan_cuoi": str(don.get("lan_cuoi") or ""),
			"trung_binh": flt(don.get("tien")) / (int(don.get("so_don") or 0) or 1),
		},
		"mua_fabi": {
			"so_don": cint(d.get("vgb_so_don_cu")),
			"tien": flt(d.get("vgb_chi_tieu_cu")),
			"lan_dau": str(d.get("vgb_lan_dau_cu") or ""),
			"lan_cuoi": str(d.get("vgb_lan_cuoi_cu") or ""),
			"trung_binh": flt(d.get("vgb_chi_tieu_cu")) / (cint(d.get("vgb_so_don_cu")) or 1),
			"cua_hang": d.get("vgb_cua_hang_cu") or "",
		},
		"don_gan_day": gan_day,
	}


@frappe.whitelist()
def luu_ho_so(khach=None, dat=None):
	"""Sua thong tin lien he cua mot khach tu man app.

	Chi cho sua nhung o NGUOI DUNG dien: ten, so dien thoai, email, sinh
	nhat, gioi tinh, dia chi, nhan. Cac o mang tu Fabi sang deu de chi doc -
	sua chung khong lam khach duoc cham soc tot hon, ma lai mat dau vet.
	"""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	if isinstance(dat, str):
		dat = frappe.parse_json(dat or "{}")
	dat = dat or {}

	kh, lh = {}, {}
	if "ten" in dat:
		t = str(dat.get("ten") or "").strip()
		if not t:
			frappe.throw("Tên khách không được để trống.")
		kh["customer_name"] = t[:140]
	if "gioi_tinh" in dat:
		g = str(dat.get("gioi_tinh") or "").strip()
		kh["gender"] = g if g in ("Male", "Female") else None
	for o, truong in (("sinh_nhat", "vgb_sinh_nhat"), ("ngay_dang_ky", "vgb_ngay_dang_ky")):
		if o in dat:
			kh[truong] = _ngay_hop_le(dat.get(o))
	if "dia_chi" in dat:
		kh["vgb_dia_chi_cu"] = str(dat.get("dia_chi") or "").strip()[:500]
	if "tags" in dat:
		kh["vgb_tags"] = str(dat.get("tags") or "").strip()[:500]
	if "zalo" in dat:
		kh["vgb_zalo_id"] = str(dat.get("zalo") or "").strip()[:140]

	if "sdt" in dat:
		s = sdt(dat.get("sdt"))
		if str(dat.get("sdt") or "").strip() and not s:
			frappe.throw(
				"Số điện thoại %s không đọc được thành số di động Việt Nam. "
				"Nhập lại giúp em, không thì khách này không nhận được tin nhắn nào."
				% dat.get("sdt")
			)
		# Mot so chi thuoc mot khach: hai ban ghi cho mot nguoi la chi tieu
		# bi chia doi, hang xet sai, diem tich ra hai so du.
		if s:
			from vagabond.nhap_khach import tim_theo_sdt

			chu = tim_theo_sdt(s)
			if chu and chu != khach:
				frappe.throw(
					"Số %s đang là của khách %s. Một số chỉ thuộc một người." % (s, chu)
				)
		lh["mobile_no"] = s
	if "email" in dat:
		e = str(dat.get("email") or "").strip()
		if e and "@" not in e:
			frappe.throw("Email %s không đúng dạng." % e)
		lh["email_id"] = e[:140]

	if kh:
		frappe.db.set_value("Customer", khach, kh)
	if lh:
		_luu_lien_he(khach, lh)
	frappe.db.commit()
	return ho_so(khach)


def _ngay_hop_le(v):
	v = str(v or "").strip()
	if not v:
		return None
	try:
		return getdate(v)
	except Exception:
		frappe.throw("Ngày %s không đúng dạng." % v)


def _luu_lien_he(khach, dat):
	"""Ghi so dien thoai va email vao LIEN HE, khong ghi thang vao Customer.

	Customer.mobile_no la truong chi doc, ERPNext keo tu lien he chinh sang.
	Ghi thang vao do thi lan sau ai mo khach ra bam Luu la so bi xoa trang -
	dung cai da lam 1.545 khach doanh nghiep khong ai co so dien thoai.
	"""
	from vagabond.nhap_khach import _tach_ten

	cu = _lien_he(khach)
	ten = frappe.db.get_value("Customer", khach, "customer_name") or khach
	if cu.get("ma"):
		doc = frappe.get_doc("Contact", cu["ma"])
	else:
		ho, dem = _tach_ten(ten)
		doc = frappe.new_doc("Contact")
		doc.first_name = ho[:140]
		doc.last_name = dem[:140]
		doc.is_primary_contact = 1
		doc.append("links", {"link_doctype": "Customer", "link_name": khach})

	if "mobile_no" in dat:
		so = dat["mobile_no"]
		doc.mobile_no = so
		doc.phone_nos = []
		if so:
			doc.append("phone_nos", {"phone": so, "is_primary_mobile_no": 1})
	if "email_id" in dat:
		em = dat["email_id"]
		doc.email_ids = []
		if em:
			doc.append("email_ids", {"email_id": em, "is_primary": 1})

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.set_value(
		"Customer",
		khach,
		{"customer_primary_contact": doc.name, "mobile_no": doc.mobile_no or ""},
		update_modified=False,
	)


# ------------------------------------------------------- the thanh vien tren don
#
# Anh Viet 16/08/2026, tren man Chi tiet don: *"thay vi emoji kia thi phai
# hien thi kem cai hinh the hang thanh vien"*, cong hai o "So diem hien
# tai" va "So diem tich cho don nay".
#
# HAI DIEU HAM NAY PHAI LAM CHO DUNG
# ----------------------------------
# Mot. So diem hien tai phai la so du TRUOC khi chot don nay. Voi don da
# ghi so va da tich roi thi so du dang co DA GOM diem cua chinh don do,
# nen phai tru ra - khong thi sales doc cho khach mot con so cao hon thuc
# te, va khach se hoi lai luc doi qua.
#
# Hai. O "diem tich cho don nay" phai phan biet DA TICH voi SE TICH. Don
# cu ma hien so du kien thi sai; don moi ma hien so da tich thi cung sai.


@frappe.whitelist()
def the_tren_don(khach=None, tien=0, hoa_don=None):
	"""Hang the, so diem hien co va so diem cua rieng don nay.

	CHI DOC. Khong ghi mot but diem nao - viec cong diem van do hook
	on_submit cua hoa don lam, dung mot cho duy nhat.
	"""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		return {"co": 0}

	kh = frappe.db.get_value(
		"Customer", khach, ["customer_name", "vgb_hang", "vgb_diem"], as_dict=True
	) or {}
	if not kh:
		return {"co": 0}

	hang = _hang_cua(khach) or {}
	ta = {}
	if hang.get("name"):
		ta = frappe.db.get_value(
			"Vagabond Hang Khach", hang["name"],
			["ten_hang", "anh", "giam_gia", "tich_diem", "mo_ta"], as_dict=True
		) or {}

	# So du lay tu SO, khong tin o tong hop tren Customer: so la nguon that.
	so_du = flt(
		(frappe.db.sql(
			"select sum(diem) from `tab%s` where khach = %%s" % SO_DIEM, (khach,)
		) or [[0]])[0][0]
	)

	ty_le = flt(hang.get("tich_diem"))
	da_tich = None
	if hoa_don:
		da_tich = frappe.db.get_value(
			SO_DIEM, {"hoa_don": hoa_don, "loai": "Tich tu hoa don"}, "diem"
		)

	if da_tich is not None:
		# Don da tich roi: bao dung so THAT da ghi so, va tru no ra khoi so
		# du de o "hien tai" dung nghia la truoc khi chot don nay.
		diem_don = int(round(flt(da_tich)))
		truoc_don = so_du - flt(da_tich)
	else:
		diem_don = diem_cho_don(tien, ty_le)
		truoc_don = so_du

	return {
		"co": 1,
		"khach": khach,
		"ten": kh.get("customer_name") or khach,
		"hang": hang.get("name") or "",
		"ten_hang": ta.get("ten_hang") or hang.get("name") or "",
		"anh_hang": ta.get("anh") or "",
		"giam_gia": flt(ta.get("giam_gia")),
		"tich_diem_pt": ty_le,
		"diem_hien_tai": int(round(truoc_don)),
		"diem_don_nay": diem_don,
		"da_tich": 1 if da_tich is not None else 0,
		"so_du_sau": int(round(truoc_don + diem_don)),
	}
