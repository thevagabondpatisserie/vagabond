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

# Sua bang hang, cong tru diem tay, chuyen hang hang loat: ba viec nay deu
# dung thang vao quyen loi cua khach nen chi quan ly moi lam duoc.
QUYEN_SUA_HANG = {"System Manager", "Sales Manager", "Accounts Manager", "VGB - Quản lý khuyến mãi"}

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
			fields=["name", "ten_hang", "thu_tu", "loai", "giam_gia", "chi_tieu_tu", "so_thang_xet", "mo_ta"],
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
	"""Khach tich diem duoc, hay la khach le dung chung.

	"Khach le Online" la mot ban ghi Customer duy nhat dung chung cho moi
	don le khong co ten. Cong diem vao do la don toan bo diem cua ca tiem
	vao mot cho, khong cua ai ca.
	"""
	from vagabond.ban_hang import KHACH_LE

	kh = (si.get("customer") or "").strip()
	if not kh or kh == KHACH_LE:
		return ""
	return kh


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
		diem = round(flt(doc.get("grand_total")) * ty_le / 100.0)
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
			"chi_tieu_tu", "so_thang_xet", "bat", "mo_ta",
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

	return {
		"doi": doi[: max(1, min(2000, cint(so_khach) or 500))],
		"tong": len(doi),
		"da_ap": da_ap,
		"so_thang": so_thang,
	}


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
	for k in ds:
		if not frappe.db.exists("Customer", k):
			continue
		frappe.db.set_value("Customer", k, "vgb_hang", h or None)
		xong += 1
	frappe.db.commit()
	_ghi_vet_hang("Chuyển %d khách sang hạng %s" % (xong, h or "(bỏ hạng)"))
	return {"xong": xong, "hang": h}


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
