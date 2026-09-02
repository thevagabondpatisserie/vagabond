"""Hai man danh sach hoa don cho ke toan (anh Viet 12/08/2026).

Hoa don ban ra va hoa don mua vao, moi man mot bang kem chip loc. Truoc
day ke toan phai mo Desk, loc bang bo loc chuan cua ERPNext roi tu doc ma
trang thai tieng Anh; nay len app, trang thai goi bang tieng Viet theo
viec con phai lam.

Khac voi phan he Bao cao: bao cao la SO TONG de nhin xu huong, con hai man
nay la DANH SACH TUNG TO de doi chieu va xu ly.
"""

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from vagabond import chung_tu

# khai = tang khung, cho khai bao man danh sach.
from vagabond.khung import hop_dong as khai
from vagabond.khung import tinh as _tinh

QUYEN_KT = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Sales Manager",
	"Vagabond Bao cao",
}

# So dong toi da tra ve mot lan. Ban dau khong dat tran, mo man 30 ngay ra
# 6.127 dong - dien thoai treo (bat duoc 12/08/2026). Con so DEM va TONG
# van tinh tren TOAN BO tap khop dieu kien roi moi cat danh sach, khong bao
# gio tinh tren phan da cat.
TRAN_DONG = 300


def _kiem_quyen():
	if not QUYEN_KT & set(frappe.get_roles()):
		frappe.throw("Danh sách hoá đơn chỉ mở cho kế toán và quản lý.")


def _khoang(so_ngay, tu=None, den=None):
	if tu and den:
		t, d = getdate(tu), getdate(den)
		return (t, d) if t <= d else (d, t)
	so_ngay = int(so_ngay or 30)
	return getdate(add_days(nowdate(), -so_ngay)), getdate(nowdate())


# --------------------------------------------------------- hoa don ban ra

NHOM_BAN = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "nhap", "ten": "Chưa ghi sổ", "ic": "📝"},
	{"k": "chua_hddt", "ten": "Chưa xuất hoá đơn điện tử", "ic": "⚠️"},
	{"k": "cho_ky", "ten": "Chờ ký", "ic": "✍️"},
	{"k": "da_ky", "ten": "Đã ký", "ic": "✅"},
	{"k": "cqt", "ten": "CQT chấp nhận", "ic": "🏛️"},
	{"k": "con_thu", "ten": "Còn phải thu", "ic": "📒"},
	{"k": "da_sua", "ten": "Đã sửa", "ic": "✏️"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
]


def _da_sua(r, co_ban_thay_the=None):
	"""To nay da bi sua chua - la CO PHU, khong phai mot nhom loai tru.

	Neu de "da sua" thanh mot nhom rieng thi moi bill quay tung sua se roi
	khoi chip "Chua ghi so", ma do dung la nhom ke toan can soat ky nhat -
	cuoi ngay bam chip Chua ghi so lai bo sot dung may to dang nghi.
	"""
	if cint(r.get("vgb_lan_sua")):
		return 1
	if (r.get("amended_from") or "").strip():
		return 1
	if co_ban_thay_the and r.get("name") in co_ban_thay_the:
		return 1
	return 0


def _nhom_ban(r):
	"""Xep mot hoa don vao dung mot chip.

	HUY xet TRUOC moi thu khac: mot to da huy ma van hien la "Cho ky" thi
	ke toan doi chieu voi co quan thue se dem nham - va do dung la kieu nham
	lam ra 37 hoa don thay the hom 10/08.
	"""
	if cint(r.get("vgb_huy")):
		return "huy"
	if r.get("docstatus") == 2:
		return "huy"
	if r.get("docstatus") == 0:
		return "nhap"
	tt = (r.get("custom_hddt_trang_thai") or "").strip()
	if not (r.get("custom_hddt_so") or "").strip():
		return "chua_hddt"
	if "chấp nhận" in tt.lower():
		return "cqt"
	if tt.lower().startswith("đã ký"):
		return "da_ky"
	if tt:
		return "cho_ky"
	return "cho_ky"


@frappe.whitelist()
def ds_hoa_don_ban(so_ngay=30, tu=None, den=None, quay=None, tu_khoa="", nhom=None):
	_kiem_quyen()
	t, d = _khoang(so_ngay, tu, den)
	ds = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": ["<", 3], "posting_date": ["between", [str(t), str(d)]]},
		fields=[
			"name", "posting_date", "customer", "customer_name", "grand_total",
			"outstanding_amount", "docstatus", "custom_hddt_so",
			"custom_hddt_trang_thai", "custom_nguon", "vgb_quay",
			"vgb_pt_thanh_toan", "custom_pancake_display_id", "vgb_tam_tinh",
			"vgb_khach_no", "vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi",
			"vgb_lan_sua", "amended_from",
			# Nguoi ban. Anh Viet chot 02/09/2026: moi man hoa don phai thay
			# duoc ai ban to nay, khong phai mo tung to ra doan. O
			# `vgb_nguoi_ban` dung TRUOC nguoi lap, xem vagabond/nguoi_ban.py.
			"owner", "vgb_nguoi_ban",
			# Ten that cua khach le nam trong ghi chu chu khong o customer_name
			# (anh Viet 01/09/2026: moi man phai thay duoc khach tren don).
			"remarks",
		],
		order_by="posting_date desc, name desc",
		limit_page_length=0,
	)
	q = (tu_khoa or "").strip().lower()
	# Doc mot lan cho CA TAP: to nao da co ban thay the. Hoi tung to mot thi
	# man 30 ngay ban ra hang nghin luot goi co so du lieu.
	thay_the = chung_tu.ds_da_bi_sua(
		"Sales Invoice", [r.name for r in ds if r.get("docstatus") == 2]
	)
	# Nhap tai cho chu khong o dau tep: ban_hang keo theo ca chuoi dong bo
	# Pancake, dat o dau tep la ke_toan khong con nhap duoc khi khong co mang
	# (bai hoc CI do ba ca ngay 20/08/2026).
	from vagabond import ban_hang as _bh

	_bh.gan_khach_vao_dong(ds)
	ra = []
	for r in ds:
		if r.get("vgb_tam_tinh"):
			continue
		diem = (r.vgb_quay or "").strip().upper() or "SALES"
		if quay and diem != str(quay).strip().upper():
			continue
		o = dict(r)
		o["diem"] = diem
		o["nhom"] = _nhom_ban(r)
		o["da_sua"] = _da_sua(r, thay_the)
		# Thu tu tin cay: khach cong no da gan tay, roi ten that doc tu ghi
		# chu, roi moi den customer_name. Dat customer_name truoc thi moi don
		# ban le deu ra chu "Khach le Online", dung mot chu ma vo nghia.
		o["khach"] = r.vgb_khach_no or o.get("ten_tren_don") or r.customer_name or r.customer
		if q and q not in (
			(r.name or "") + " " + (o["khach"] or "") + " "
			+ (r.custom_hddt_so or "") + " " + (r.custom_pancake_display_id or "")
		).lower():
			continue
		ra.append(o)

	dem = {}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	dem[""] = len(ra)
	dem["da_sua"] = len([o for o in ra if o["da_sua"]])
	dem["con_thu"] = len(
		[
			o
			for o in ra
			if o["docstatus"] == 1
			and flt(o["outstanding_amount"]) > 0
			and not cint(o.get("vgb_huy"))
		]
	)

	# Doi ma tai khoan thanh TEN nguoi, mot luot cho ca trang chu khong hoi
	# tung dong. Anh Viet chot 02/09/2026, xem `vagabond/ten_nguoi.py`.
	from vagabond import ten_nguoi as _tn

	from vagabond.nguoi_ban import MAY as _MAY_BAN

	for o in ra:
		o["nguoi_ban"] = (o.get("vgb_nguoi_ban") or "").strip() or o.get("owner") or ""
		# To nao quy ve tai khoan may la to CHUA AI GAN nguoi ban - dung
		# dinh nghia voi ro "chua gan" ben man KPI. Ghi ro ra day de man
		# hinh khong phai doan tu cai ten "He thong".
		o["nguoi_ban_may"] = 1 if o["nguoi_ban"] in _MAY_BAN else 0
	_tn.gan(ra, "nguoi_ban", "vgb_huy_boi")

	# Loc theo chip PHAI lam o day, TRUOC khi cat 300 dong - loc tren tap da
	# bi cat thi bam chip "Chua xuat hoa don dien tu" se ra rong trong khi
	# thuc te con hang tram to. Bai hoc cu, khong duoc lap lai.
	chon = (nhom or "").strip()
	if chon == "da_sua":
		loc_ra = [o for o in ra if o["da_sua"]]
	elif chon == "con_thu":
		loc_ra = [
			o
			for o in ra
			if o["docstatus"] == 1
			and flt(o["outstanding_amount"]) > 0
			and not cint(o.get("vgb_huy"))
		]
	elif chon:
		loc_ra = [o for o in ra if o["nhom"] == chon]
	else:
		loc_ra = ra
	return {
		"hd": loc_ra[:TRAN_DONG],
		"tong_dong": len(loc_ra),
		"bi_cat": max(0, len(loc_ra) - TRAN_DONG),
		"dem": dem,
		"nhom": NHOM_BAN,
		"tu": str(t),
		"den": str(d),
		"tong": sum(
			flt(o["grand_total"])
			for o in ra
			if o["docstatus"] == 1 and not cint(o.get("vgb_huy"))
		),
		"con_thu": sum(
			flt(o["outstanding_amount"])
			for o in ra
			if o["docstatus"] == 1 and not cint(o.get("vgb_huy"))
		),
	}


# -------------------------------------------------------- hoa don mua vao

NHOM_MUA = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "nhap", "ten": "Chưa ghi sổ", "ic": "📝"},
	{"k": "qua_han", "ten": "Quá hạn trả", "ic": "🔴"},
	{"k": "con_no", "ten": "Còn nợ", "ic": "📒"},
	{"k": "da_tra", "ten": "Đã trả xong", "ic": "✅"},
	{"k": "da_sua", "ten": "Đã sửa", "ic": "✏️"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
]


def _xep_mua(r, bc=None):
	"""Xep mot to hoa don mua vao dung mot chip. Ham THUAN: khong doc ngay
	he thong, khong goi frappe, hom nay lay tu boi canh dua vao.

	Tach thuan de bo kiem thu A6 chay duoc ma khong phai dung ca mot site.
	Luat xep giu nguyen tung dong nhu cu.
	"""
	if _tinh.co(r.get("vgb_huy")):
		return "huy"
	if r.get("docstatus") == 2:
		return "huy"
	if r.get("docstatus") == 0:
		return "nhap"
	if _tinh.so(r.get("outstanding_amount")) <= 0:
		return "da_tra"
	hom_nay = _tinh.ngay_chu((bc or {}).get("hom_nay"))
	if r.get("due_date") and hom_nay and _tinh.ngay_chu(r["due_date"]) < hom_nay:
		return "qua_han"
	return "con_no"


def _nhom_mua(r, hom_nay):
	"""Ban co ngay san, cho duong cu goi. Ket qua y het _xep_mua."""
	return _xep_mua(r, {"hom_nay": hom_nay})


@frappe.whitelist()
def ds_hoa_don_mua(so_ngay=60, tu=None, den=None, ncc=None, tu_khoa="", nhom=None):
	_kiem_quyen()
	t, d = _khoang(so_ngay, tu, den)
	loc = {"docstatus": ["<", 3], "posting_date": ["between", [str(t), str(d)]]}
	if ncc:
		loc["supplier"] = ncc
	ds = frappe.get_all(
		"Purchase Invoice",
		filters=loc,
		fields=[
			"name", "posting_date", "supplier", "supplier_name", "grand_total",
			"outstanding_amount", "docstatus", "due_date", "bill_no", "bill_date",
			"status", "total_qty", "vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi",
			"amended_from",
		],
		order_by="posting_date desc, name desc",
		limit_page_length=0,
	)
	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	thay_the = chung_tu.ds_da_bi_sua(
		"Purchase Invoice", [r.name for r in ds if r.get("docstatus") == 2]
	)
	ra = []
	for r in ds:
		o = dict(r)
		o["nhom"] = _nhom_mua(r, hom_nay)
		o["da_sua"] = _da_sua(r, thay_the)
		o["tre_ngay"] = (
			(hom_nay - getdate(r.due_date)).days
			if r.due_date and getdate(r.due_date) < hom_nay and flt(r.outstanding_amount) > 0
			else 0
		)
		if q and q not in (
			(r.name or "") + " " + (r.supplier_name or "") + " " + (r.bill_no or "")
		).lower():
			continue
		ra.append(o)

	dem = {}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	dem[""] = len(ra)
	dem["da_sua"] = len([o for o in ra if o["da_sua"]])
	chon = (nhom or "").strip()
	if chon == "da_sua":
		loc_ra = [o for o in ra if o["da_sua"]]
	elif chon:
		loc_ra = [o for o in ra if o["nhom"] == chon]
	else:
		loc_ra = ra
	return {
		"hd": loc_ra[:TRAN_DONG],
		"tong_dong": len(loc_ra),
		"bi_cat": max(0, len(loc_ra) - TRAN_DONG),
		"dem": dem,
		"nhom": NHOM_MUA,
		"tu": str(t),
		"den": str(d),
		"tong": sum(
			flt(o["grand_total"])
			for o in ra
			if o["docstatus"] == 1 and not cint(o.get("vgb_huy"))
		),
		"con_no": sum(
			flt(o["outstanding_amount"])
			for o in ra
			if o["docstatus"] == 1 and not cint(o.get("vgb_huy"))
		),
	}


# ---------------------------------------------------------------------------
# Man Hoa don mua vao theo khung dung chung (A2, anh Viet duyet 15/08/2026).
#
# Chay SONG SONG voi ds_hoa_don_mua o tren, khong thay the. Duong moi goi
# bang: vagabond.khung.ds.chay voi ma HDM.
# ---------------------------------------------------------------------------

def _truoc_hdm(dong, bc):
	"""Hoi MOT lan cho ca tap: to nao da co ban thay the.

	Cau hoi nay bat buoc phai xuong co so du lieu nen khong the nam trong
	ham them() von phai thuan. Cho no chay o day, mot cau hoi cho ca 600
	dong thay vi 600 cau hoi.
	"""
	return {
		"thay_the": chung_tu.ds_da_bi_sua(
			"Purchase Invoice",
			[r.get("name") for r in dong if r.get("docstatus") == 2],
		)
	}


def _them_hdm(r, bc):
	"""Cac o dan xuat cua mot to. Ham THUAN, chi doc tu boi canh."""
	hom_nay = _tinh.ngay_chu(bc.get("hom_nay"))
	han = _tinh.ngay_chu(r.get("due_date"))
	tre = 0
	if han and hom_nay and han < hom_nay and _tinh.so(r.get("outstanding_amount")) > 0:
		import datetime
		a = datetime.date(*[int(x) for x in han.split("-")])
		b = datetime.date(*[int(x) for x in hom_nay.split("-")])
		tre = (b - a).days
	return {"da_sua": _da_sua(r, bc.get("thay_the")), "tre_ngay": tre}


BANG_HOA_DON_MUA = khai.bang(
	ma="HDM",
	ten="Hoá đơn mua vào",
	doctype="Purchase Invoice",
	quyen=QUYEN_KT,
	loi_quyen="Danh sách hoá đơn chỉ mở cho kế toán và quản lý.",
	dieu_kien={"docstatus": ["<", 3]},
	truong=[
		"name", "posting_date", "supplier", "supplier_name", "grand_total",
		"outstanding_amount", "docstatus", "due_date", "bill_no", "bill_date",
		"status", "total_qty", "vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi",
		"amended_from",
	],
	cot=khai.cot(
		("name", "Số tờ", "chu"),
		("posting_date", "Ngày", "ngay"),
		("supplier_name", "Nhà cung cấp", "chu"),
		("bill_no", "Số hoá đơn NCC", "chu"),
		("_chip", "Trạng thái", "chip"),
		("due_date", "Hạn trả", "ngay"),
		("tre_ngay", "Trễ (ngày)", "so", True),
		("grand_total", "Thành tiền", "tien"),
		("outstanding_amount", "Còn nợ", "tien"),
	),
	loc=khai.loc(
		{"k": "ngay", "nhan": "Khoảng ngày", "kieu": "ngay",
			"truong": "posting_date", "mac_dinh": 60},
		{"k": "ncc", "nhan": "Nhà cung cấp", "kieu": "chon_mot", "truong": "supplier"},
		{"k": "tu_khoa", "nhan": "số tờ, tên nhà cung cấp hoặc số hoá đơn NCC", "kieu": "tim_chu",
			"tim": ["name", "supplier_name", "bill_no"]},
	),
	# Da sua la CO PHU, khong loai tru voi cac chip khac: mot to vua Chua
	# ghi so vua Da sua thi phai dem o ca hai cho.
	chip=khai.chip(
		*[dict(c, phu=1) if c["k"] == "da_sua" else dict(c) for c in NHOM_MUA]
	),
	xep=_xep_mua,
	truoc=_truoc_hdm,
	them=_them_hdm,
	sap="posting_date desc, name desc",
	tran=TRAN_DONG,
	# Chi to DA GHI SO va chua huy moi la tien that phai tra.
	tinh_dong=lambda r: r.get("docstatus") == 1 and not _tinh.co(r.get("vgb_huy")),
	tom_tat=[
		("_dong", "Số tờ", "so"),
		("grand_total", "Tổng tiền", "tien"),
		("outstanding_amount", "Còn nợ", "tien"),
	],
	tom_tat_theo_chip=0,
)
