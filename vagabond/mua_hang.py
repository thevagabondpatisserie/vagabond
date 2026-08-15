"""Don mua hang va cong no phai tra (anh Viet 12/08/2026).

Truoc day Uyen phai mo Desk moi theo doi duoc don mua hang: don nao da gui
cho nha cung cap, don nao hang ve roi ma chua co hoa don, don nao tre hen.
Man nay dua het len app, kem chip trang thai de nhin phat la biet.

Ai duoc vao: ke toan, thu mua va giam doc. KHONG mo cho ca tiem - gia mua
va cong no la thong tin nhay cam.

Nguyen tac dat ten trang thai: goi theo viec con phai lam, khong goi theo
ma ky thuat cua ERPNext. "Hang ve roi, chua co hoa don" de hieu hon
"To Bill".
"""

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

# khai = tang khung, cho khai bao man danh sach. Dat ten tat de khong lan
# voi vagabond/hop_dong.py, la mo dun hop dong mua ban chu khong lien quan.
from vagabond.khung import hop_dong as khai
from vagabond.khung import tinh as _tinh

QUYEN_MUA = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Purchase Manager",
	"Purchase User",
	"Bộ phận đặt hàng",
}


def _kiem_quyen():
	if not QUYEN_MUA & set(frappe.get_roles()):
		frappe.throw(
			"Đơn mua hàng và công nợ phải trả chỉ mở cho kế toán, thu mua và giám đốc."
		)


# Cac nhom trang thai cua don mua hang. Mot don chi thuoc DUNG MOT nhom -
# xep tu tren xuong, gap nhom nao dung truoc thi lay nhom do.
def _xep_po(d, bc=None):
	"""Xep mot don vao dung mot nhom. Ham THUAN: khong doc ngay he thong,
	khong goi frappe, hom nay lay tu boi canh dua vao.

	Tach thuan de bo kiem thu A6 chay duoc ma khong phai dung ca mot site.
	Luat xep giu nguyen tung dong nhu cu, chi doi cho lay ngay hom nay.
	"""
	# Huy mem xet truoc: don da bo ma van hien "Cho nhan hang" thi thu mua
	# ngoi doi mot chuyen hang khong bao gio ve.
	if _tinh.co(d.get("vgb_huy")):
		return "huy"
	if d.get("docstatus") == 2:
		return "huy"
	if d.get("docstatus") == 0:
		return "nhap"
	if d.get("status") in ("Closed", "Completed"):
		return "dong"
	nhan = _tinh.so(d.get("per_received"))
	hd = _tinh.so(d.get("per_billed"))
	if nhan < 99.99:
		hom_nay = _tinh.ngay_chu((bc or {}).get("hom_nay"))
		if d.get("schedule_date") and _tinh.ngay_chu(d["schedule_date"]) < hom_nay:
			return "tre_hen"
		return "cho_nhan" if nhan <= 0.01 else "nhan_mot_phan"
	if hd < 99.99:
		return "cho_hoa_don"
	return "xong"



def _tre_ngay(hen, bc=None):
	"""So ngay tre so voi ngay hen. Ham THUAN, hom nay lay tu boi canh."""
	h = _tinh.ngay_chu(hen)
	n = _tinh.ngay_chu((bc or {}).get("hom_nay"))
	if not h or not n or h >= n:
		return 0
	import datetime
	a = datetime.date(*[int(x) for x in h.split("-")])
	b = datetime.date(*[int(x) for x in n.split("-")])
	return (b - a).days


def _nhom_po(d):
	"""Ban co ngay he thong, cho duong cu goi. Ket qua y het _xep_po."""
	return _xep_po(d, {"hom_nay": nowdate()})


NHOM_PO = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "nhap", "ten": "Còn nháp", "ic": "📝"},
	{"k": "cho_nhan", "ten": "Chờ nhận hàng", "ic": "🚚"},
	{"k": "nhan_mot_phan", "ten": "Nhận một phần", "ic": "📦"},
	{"k": "tre_hen", "ten": "Trễ hẹn", "ic": "🔴"},
	{"k": "cho_hoa_don", "ten": "Chưa có hoá đơn", "ic": "🧾"},
	{"k": "xong", "ten": "Xong", "ic": "✅"},
	{"k": "dong", "ten": "Đã đóng", "ic": "🔒"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
]


@frappe.whitelist()
def ds_po(so_ngay=60, tu_khoa="", ncc=None, nhom=None):
	"""Danh sach don mua hang trong khoang ngay gan day.

	so_ngay = 0 nghia la lay het, dung khi ke toan tra don cu.
	"""
	_kiem_quyen()
	loc = {"docstatus": ["<", 3]}
	so_ngay = int(so_ngay or 0)
	if so_ngay:
		loc["transaction_date"] = [">=", add_days(nowdate(), -so_ngay)]
	if ncc:
		loc["supplier"] = ncc
	ds = frappe.get_all(
		"Purchase Order",
		filters=loc,
		fields=[
			"name", "supplier", "supplier_name", "transaction_date", "schedule_date",
			"grand_total", "total_qty", "status", "per_received", "per_billed",
			"docstatus", "owner", "vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi",
		],
		order_by="transaction_date desc, name desc",
		limit_page_length=0,
	)
	q = (tu_khoa or "").strip().lower()
	ra = []
	for d in ds:
		o = dict(d)
		o["nhom"] = _nhom_po(d)
		o["ngay"] = str(d.transaction_date or "")
		o["hen"] = str(d.schedule_date or "")
		o["tre_ngay"] = 0
		if o["nhom"] == "tre_hen" and d.schedule_date:
			o["tre_ngay"] = (getdate(nowdate()) - getdate(d.schedule_date)).days
		if q and q not in (
			(d.name or "") + " " + (d.supplier_name or "") + " " + (d.supplier or "")
		).lower():
			continue
		ra.append(o)

	dem = {}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	dem[""] = len(ra)
	# Dem va tong tinh tren TOAN BO tap khop dieu kien, cat danh sach sau -
	# khong bao gio tinh tren phan da cat.
	chon = (nhom or "").strip()
	loc_ra = [o for o in ra if o["nhom"] == chon] if chon else ra
	return {
		"don": loc_ra[:300],
		"tong_dong": len(loc_ra),
		"bi_cat": max(0, len(loc_ra) - 300),
		"dem": dem,
		"nhom": NHOM_PO,
		# Don da huy khong con la tien phai chi, khong duoc cong vao tong.
		"tong_tien": sum(
			flt(o["grand_total"]) for o in ra if not cint(o.get("vgb_huy"))
		),
	}


@frappe.whitelist()
def xem_po(name):
	"""Chi tiet mot don mua hang, kem cac phieu nhap kho va hoa don da noi
	vao don do - de biet hang ve toi dau, tien tra toi dau."""
	_kiem_quyen()
	d = frappe.get_doc("Purchase Order", name)
	mon = [
		{
			"ma": r.item_code,
			"ten": r.item_name,
			"sl": flt(r.qty),
			"da_nhan": flt(r.received_qty),
			"dvt": r.uom,
			"gia": flt(r.rate),
			"tien": flt(r.amount),
		}
		for r in d.items
	]
	pnk = frappe.get_all(
		"Purchase Receipt Item",
		filters={"purchase_order": name, "docstatus": 1},
		fields=["parent"],
		limit_page_length=0,
	)
	hd = frappe.get_all(
		"Purchase Invoice Item",
		filters={"purchase_order": name, "docstatus": 1},
		fields=["parent"],
		limit_page_length=0,
	)
	return {
		"name": d.name,
		"ncc": d.supplier,
		"ten_ncc": d.supplier_name,
		"ngay": str(d.transaction_date or ""),
		"hen": str(d.schedule_date or ""),
		"tong": flt(d.grand_total),
		"tong_hang": flt(d.total),
		"thue": flt(d.total_taxes_and_charges),
		"trang_thai": d.status,
		"docstatus": d.docstatus,
		"nhom": _nhom_po(
			{
				"docstatus": d.docstatus,
				"status": d.status,
				"per_received": d.per_received,
				"per_billed": d.per_billed,
				"schedule_date": d.schedule_date,
			}
		),
		"da_nhan": flt(d.per_received),
		"da_hoa_don": flt(d.per_billed),
		"mon": mon,
		"phieu_nhap": sorted({r.parent for r in pnk}),
		"hoa_don": sorted({r.parent for r in hd}),
		"ghi_chu": d.get("terms") or "",
	}


# ------------------------------------------------------- cong no phai tra

@frappe.whitelist()
def cong_no_phai_tra():
	"""Con no ai bao nhieu, gom theo nha cung cap.

	Chi tinh hoa don mua DA GHI SO va con outstanding - hoa don nhap chua
	phai la no. Sap xep theo khoan qua han nhieu nhat len dau: do la khoan
	de mat long nha cung cap nhat.
	"""
	_kiem_quyen()
	ds = frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=[
			"name", "supplier", "supplier_name", "posting_date", "due_date",
			"grand_total", "outstanding_amount", "bill_no", "bill_date", "status",
		],
		order_by="due_date asc",
		limit_page_length=0,
	)
	hom_nay = getdate(nowdate())
	gom = {}
	for r in ds:
		o = gom.setdefault(
			r.supplier,
			{
				"ncc": r.supplier,
				"ten": r.supplier_name or r.supplier,
				"so_hd": 0,
				"tien": 0.0,
				"qua_han": 0.0,
				"so_hd_qua_han": 0,
				"han_gan_nhat": None,
				"hd": [],
			},
		)
		tre = 0
		if r.due_date:
			tre = (hom_nay - getdate(r.due_date)).days
		o["so_hd"] += 1
		o["tien"] += flt(r.outstanding_amount)
		if tre > 0:
			o["qua_han"] += flt(r.outstanding_amount)
			o["so_hd_qua_han"] += 1
		if r.due_date and (not o["han_gan_nhat"] or str(r.due_date) < o["han_gan_nhat"]):
			o["han_gan_nhat"] = str(r.due_date)
		o["hd"].append(
			{
				"name": r.name,
				"so_hd_ncc": r.bill_no or "",
				"ngay": str(r.posting_date or ""),
				"han": str(r.due_date or ""),
				"tre_ngay": tre if tre > 0 else 0,
				"tong": flt(r.grand_total),
				"con_no": flt(r.outstanding_amount),
			}
		)
	ra = list(gom.values())
	# Qua han nhieu nhat len dau, roi den tong no lon nhat.
	ra.sort(key=lambda x: (-x["qua_han"], -x["tien"]))
	return {
		"ncc": ra,
		"tong": sum(x["tien"] for x in ra),
		"tong_qua_han": sum(x["qua_han"] for x in ra),
		"so_ncc": len(ra),
	}


# ---------------------------------------------------------------------------
# Man Don mua hang theo khung dung chung (A2, anh Viet duyet 15/08/2026).
#
# Khai bao nay chay SONG SONG voi ds_po o tren, khong thay the. Duong cu van
# nguyen, app van goi duong cu. Khi nao doi chieu tung con so tren du lieu
# that ma khong lech mot dong thi moi go duong cu.
#
# Duong moi goi bang: vagabond.khung.ds.chay voi ma PO.
# ---------------------------------------------------------------------------

BANG_PO = khai.bang(
	ma="PO",
	ten="Đơn mua hàng",
	doctype="Purchase Order",
	quyen=QUYEN_MUA,
	loi_quyen=(
		"Đơn mua hàng và công nợ phải trả chỉ mở cho kế toán, thu mua và giám đốc."
	),
	# Docstatus 3 la ban nhap da bo trong Frappe, khong phai chung tu.
	dieu_kien={"docstatus": ["<", 3]},
	truong=[
		"name", "supplier", "supplier_name", "transaction_date", "schedule_date",
		"grand_total", "total_qty", "status", "per_received", "per_billed",
		"docstatus", "owner", "vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi",
	],
	cot=khai.cot(
		("name", "Số đơn", "chu"),
		("ngay", "Ngày đặt", "ngay"),
		("supplier_name", "Nhà cung cấp", "chu"),
		("_chip", "Trạng thái", "chip"),
		("hen", "Hẹn giao", "ngay"),
		# Cong so ngay tre cua nhieu don lai ra mot con so vo nghia.
		("tre_ngay", "Trễ (ngày)", "so", True),
		("total_qty", "Số lượng", "so"),
		("grand_total", "Thành tiền", "tien"),
	),
	loc=khai.loc(
		{"k": "ngay", "nhan": "Khoảng ngày", "kieu": "ngay",
			"truong": "transaction_date", "mac_dinh": 60},
		{"k": "ncc", "nhan": "Nhà cung cấp", "kieu": "chon_mot", "truong": "supplier"},
		{"k": "tu_khoa", "nhan": "mã đơn hoặc tên nhà cung cấp", "kieu": "tim_chu",
			"tim": ["name", "supplier_name", "supplier"]},
	),
	chip=khai.chip(*NHOM_PO),
	xep=_xep_po,
	them=lambda r, bc: {
		"ngay": str(r.get("transaction_date") or ""),
		"hen": str(r.get("schedule_date") or ""),
		"tre_ngay": _tre_ngay(r.get("schedule_date"), bc)
		if _xep_po(r, bc) == "tre_hen" else 0,
	},
	sap="transaction_date desc, name desc",
	# Giu 300 dung nhu duong cu de doi chieu ra ket qua giong het. Nang len
	# 600 la viec sau, khi da chac hai duong khop nhau.
	tran=300,
	# Don da huy khong con la tien phai chi, khong duoc cong vao tong.
	tinh_dong=lambda r: not _tinh.co(r.get("vgb_huy")),
	tom_tat=[
		("_dong", "Số đơn", "so"),
		("grand_total", "Tổng tiền", "tien"),
	],
	tom_tat_theo_chip=0,
)
