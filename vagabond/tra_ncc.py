"""Xuat tra lai nha cung cap - anh Viet giao 02/09/2026.

Vi sao KHONG dung phieu xuat kho thuong
---------------------------------------
Tra hang cho nha cung cap nhin qua thi giong xuat kho: hang roi khoi kho.
Nhung nghiep vu that co HAI ve, va ve thu hai moi la ve quan trong:

  1. Hang ra khoi kho          -> ton giam
  2. Minh khong con no tien no -> cong no phai tra giam

Lap phieu xuat kho thuong thi chi lam duoc ve mot. Hang di roi ma no van
nguyen, va ke toan phai go mot but toan tay de nan lai. Chinh cho phai go
tay do la cho sinh sai.

Nen mo dun nay de xuong PHIEU NHAP MUA DANH DAU TRA LAI (Purchase Receipt
is_return = 1, return_against tro ve phieu nhap goc). ERPNext lo not phan
con lai: gia von hoan dung gia da nhap cua lo do, cong no giam dung so, va
phieu tra noi lai duoc voi phieu nhap goc de sau nay tra cuu.

Vi sao phai chon phieu nhap goc
-------------------------------
Khong phai de cho kho. Tra hang ma khong noi voi phieu nhap nao thi ERPNext
khong biet hoan gia nao: mot ma bot mua thang truoc 80 nghin mot ky, thang
nay 95 nghin, tra ve mot ky thi hoan bao nhieu. Neo vao phieu goc la cach
duy nhat de con so do dung.

Luat phan quyen
---------------
Tra hang lam giam cong no that, nen chi Thu mua, Kho va Ke toan lap duoc.
Ghi so NGAY, khong qua buoc duyet: khac xuat huy o cho hang khong mat di
ma quay ve nha cung cap, va ben do se doi chieu lai - do chinh la lop kiem
tra thu hai.

Quy tac nha
-----------
QT-19  So con tra duoc LUON tinh lai o may chu truoc khi ghi. Con so may
       khach gui len chi de hien.
QT-20  Khong xoa, khong sua chung tu goc. Phieu nhap goc khong bi dong vao
       mot chu.
QT-24  Cau bao loi phai noi nguoi dung lam gi tiep.
"""

import json

import frappe
from frappe.utils import add_days, cint, flt, nowdate

QUYEN_TRA = {
	"System Manager",
	"Stock Manager",
	"Stock User",
	"Purchase Manager",
	"Purchase User",
	"Accounts Manager",
}

# Ly do tra hang. De o day de sua mot cho la app doi theo, giong cach
# `xuat_kho.LY_DO_HUY` dang lam.
LY_DO = [
	"Hàng lỗi, hư hỏng",
	"Giao sai hàng, sai quy cách",
	"Cận hạn sử dụng",
	"Giao thừa so với đơn đặt",
	"Không đạt kiểm tra chất lượng",
	"Khác",
]

# Sai so cho phep khi so sanh so luong. Kg va lit deu co phan le nen so
# sanh bang dau bang tran la sai.
EPS = 0.0001

TRUONG_MOI = {
	"Purchase Receipt": [
		{
			"fieldname": "vgb_ly_do_tra",
			"label": "Lý do trả hàng",
			"fieldtype": "Data",
			"insert_after": "is_return",
			"description": (
				"Máy điền khi lập phiếu trả trên app. Cuối tháng lọc theo ô "
				"này là biết nhà cung cấp nào hay giao lỗi."
			),
		},
		{
			"fieldname": "vgb_anh_tra",
			"label": "Ảnh hàng trả lại",
			"fieldtype": "Attach Image",
			"insert_after": "vgb_ly_do_tra",
			"description": "Ảnh chụp hàng lỗi, để đối chiếu với nhà cung cấp.",
		},
	]
}


# ------------------------------------------------------------- phần thuần


def la_ly_do_hop_le(ly_do):
	"""Ham THUAN."""
	return (ly_do or "").strip() in set(LY_DO)


def con_tra_duoc(da_nhan, da_tra):
	"""Con tra duoc bao nhieu tren mot dong. Ham THUAN.

	`da_tra` la so DUONG (so da tra cong don). Ket qua khong bao gio am:
	tra qua so da nhan la vo nghia, va so am lot xuong duoi se thanh mot
	dong tra nguoc chieu ma khong ai ngo toi.
	"""
	con = flt(da_nhan) - flt(da_tra)
	return con if con > EPS else 0.0


def gop_da_tra(cac_dong_tra):
	"""Gom so da tra theo ma hang. Ham THUAN.

	Vao: danh sach {"ma": ..., "sl": ...} trong do `sl` la so AM vi ERPNext
	ghi dong tra bang so am. Ra: {ma: tong so duong da tra}.

	Doi dau ngay o day chu khong doi o cho goi: quen doi dau mot lan la
	con lai tinh thanh da_nhan cong da_tra, tuc la cang tra cang duoc tra
	nhieu hon.
	"""
	ra = {}
	for d in cac_dong_tra or []:
		ma = (d.get("ma") or d.get("item_code") or "").strip()
		if not ma:
			continue
		ra[ma] = ra.get(ma, 0.0) + abs(flt(d.get("sl") or d.get("qty")))
	return ra


def loc_dong_tra(dong, con_theo_ma):
	"""Loc va kiem cac dong nguoi dung go. Ham THUAN.

	Tra ve (danh sach sach, danh sach cau loi). Dong so 0 bi bo im lang -
	nguoi ta go roi xoa la chuyen thuong. Dong vuot so con tra duoc thi bao
	loi kem ten ma va con so, khong bo im lang: bo im lang la ghi mot phieu
	khac voi cai nguoi ta nhin thay tren man.
	"""
	if isinstance(dong, str):
		dong = json.loads(dong or "[]")
	sach = []
	loi = []
	for d in dong or []:
		ma = (d.get("ma") or d.get("item_code") or "").strip()
		sl = flt(d.get("sl") or d.get("qty"))
		if not ma or sl <= EPS:
			continue
		con = flt(con_theo_ma.get(ma, 0))
		if sl > con + EPS:
			loi.append("%s trả %s nhưng chỉ còn %s trả được" % (ma, _so(sl), _so(con)))
			continue
		sach.append({"ma": ma, "sl": sl})
	return sach, loi


def _so(v):
	"""So luong in ra cho nguoi doc: bo duoi .0 thua. Ham THUAN."""
	v = flt(v)
	return str(int(v)) if abs(v - int(v)) < EPS else ("%.3f" % v).rstrip("0").rstrip(".")


def dien_giai(ly_do, ghi_chu, phieu_goc):
	"""Dong dien giai in tren phieu tra. Ham THUAN."""
	phan = ["Trả lại nhà cung cấp"]
	if (ly_do or "").strip():
		phan.append(ly_do.strip())
	if (phieu_goc or "").strip():
		phan.append("theo phiếu nhập %s" % phieu_goc.strip())
	dong = " - ".join(phan)
	if (ghi_chu or "").strip():
		dong += ". " + ghi_chu.strip()
	return dong


# ------------------------------------------------ phần chạm Frappe


def _kiem_quyen():
	if not QUYEN_TRA & set(frappe.get_roles()):
		frappe.throw(
			"Màn trả hàng nhà cung cấp chỉ mở cho kho, thu mua và kế toán. "
			"Cần vào đây thì báo quản lý cấp thêm quyền Kho hoặc Thu mua."
		)


@frappe.whitelist()
def khoi_dong():
	"""Danh muc ly do va danh sach nha cung cap co phieu nhap gan day.

	Chi liet ke nha cung cap CO phieu nhap trong 90 ngay: danh sach day du
	hon 200 dong ma phan lon khong bao gio tra hang, do xuong o chon chi
	lam nguoi ta phai cuon.
	"""
	_kiem_quyen()
	tu = add_days(nowdate(), -90)
	ds = frappe.get_all(
		"Purchase Receipt",
		filters={"docstatus": 1, "is_return": 0, "posting_date": [">=", tu]},
		fields=["supplier", "supplier_name"],
		limit_page_length=0,
	)
	gap = {}
	for d in ds:
		if d.supplier:
			gap[d.supplier] = d.supplier_name or d.supplier
	return {
		"ly_do": LY_DO,
		"ncc": [{"ma": k, "ten": v} for k, v in sorted(gap.items(), key=lambda x: x[1])],
		"toi": frappe.session.user,
	}


@frappe.whitelist()
def phieu_cua_ncc(ncc=None, so_ngay=90):
	"""Cac phieu nhap da ghi so cua mot nha cung cap, moi nhat truoc."""
	_kiem_quyen()
	if not ncc:
		frappe.throw("Chưa chọn nhà cung cấp.")
	so_ngay = max(1, min(cint(so_ngay) or 90, 365))
	tu = add_days(nowdate(), -so_ngay)
	ds = frappe.get_all(
		"Purchase Receipt",
		filters={
			"docstatus": 1,
			"is_return": 0,
			"supplier": ncc,
			"posting_date": [">=", tu],
		},
		fields=["name", "posting_date", "set_warehouse", "grand_total", "supplier_name"],
		order_by="posting_date desc, creation desc",
		limit_page_length=60,
	)
	for d in ds:
		d["so_dong"] = frappe.db.count("Purchase Receipt Item", {"parent": d.name})
	return ds


def _da_tra_theo_ma(phieu_goc):
	"""So da tra ve cua tung ma tren mot phieu nhap goc.

	Doc TAT CA phieu tra da ghi so co `return_against` tro ve phieu nay.
	Khong doc thi tra hai lan cung mot mon deu duoc chap nhan, va tong tra
	vuot qua tong nhan ma khong ai chan.
	"""
	cac_phieu_tra = frappe.get_all(
		"Purchase Receipt",
		filters={"return_against": phieu_goc, "docstatus": 1, "is_return": 1},
		pluck="name",
		limit_page_length=0,
	)
	if not cac_phieu_tra:
		return {}
	dong = frappe.get_all(
		"Purchase Receipt Item",
		filters={"parent": ["in", cac_phieu_tra], "parenttype": "Purchase Receipt"},
		fields=["item_code", "qty"],
		limit_page_length=0,
	)
	return gop_da_tra([{"ma": d.item_code, "sl": d.qty} for d in dong])


@frappe.whitelist()
def dong_cua_phieu(phieu=None):
	"""Cac dong cua mot phieu nhap kem so CON TRA DUOC.

	QT-19: so con lai tinh lai tai day, khong tin con so may khach gui len.
	"""
	_kiem_quyen()
	if not phieu or not frappe.db.exists("Purchase Receipt", phieu):
		frappe.throw("Không tìm thấy phiếu nhập %s." % (phieu or "(trống)"))
	doc = frappe.get_doc("Purchase Receipt", phieu)
	if cint(doc.docstatus) != 1:
		frappe.throw("Phiếu nhập %s chưa ghi sổ nên chưa trả hàng theo nó được." % phieu)
	if cint(doc.get("is_return")):
		frappe.throw("Phiếu %s đã là phiếu trả hàng, không trả tiếp theo nó được." % phieu)
	da_tra = _da_tra_theo_ma(phieu)
	ra = []
	for d in doc.items:
		con = con_tra_duoc(d.qty, da_tra.get(d.item_code, 0))
		ra.append(
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"kho": d.warehouse,
				"da_nhan": flt(d.qty),
				"da_tra": flt(da_tra.get(d.item_code, 0)),
				"con": con,
				"don_gia": flt(d.rate),
			}
		)
	return {
		"phieu": doc.name,
		"ngay": str(doc.posting_date),
		"ncc": doc.supplier,
		"ten_ncc": doc.supplier_name or doc.supplier,
		"kho": doc.get("set_warehouse") or "",
		"dong": ra,
	}


@frappe.whitelist()
def luu(phieu=None, ly_do=None, ghi_chu=None, dong=None, anh=None):
	"""Lap phieu tra hang va GHI SO ngay.

	Ghi so ngay chu khong qua buoc duyet: hang khong mat di ma quay ve nha
	cung cap, va ben do doi chieu lai - do la lop kiem tra thu hai.
	"""
	_kiem_quyen()
	if not phieu:
		frappe.throw("Chưa chọn phiếu nhập gốc.")
	if not la_ly_do_hop_le(ly_do):
		frappe.throw("Chưa chọn lý do trả hàng.")
	goc = frappe.get_doc("Purchase Receipt", phieu)
	if cint(goc.docstatus) != 1 or cint(goc.get("is_return")):
		frappe.throw("Phiếu nhập gốc phải là phiếu đã ghi sổ và không phải phiếu trả.")

	da_tra = _da_tra_theo_ma(phieu)
	con_theo_ma = {}
	dong_goc = {}
	for d in goc.items:
		con_theo_ma[d.item_code] = con_tra_duoc(d.qty, da_tra.get(d.item_code, 0))
		dong_goc.setdefault(d.item_code, d)
	sach, loi = loc_dong_tra(dong, con_theo_ma)
	if loi:
		frappe.throw(
			"Số trả vượt quá số còn trả được: %s. Mở lại phiếu để lấy số mới nhất "
			"rồi nhập lại." % "; ".join(loi)
		)
	if not sach:
		frappe.throw("Phiếu chưa có dòng hàng nào có số lượng lớn hơn 0.")

	tra = frappe.new_doc("Purchase Receipt")
	tra.supplier = goc.supplier
	tra.company = goc.company
	tra.is_return = 1
	tra.return_against = goc.name
	tra.posting_date = nowdate()
	tra.set_posting_time = 0
	tra.vgb_ly_do_tra = (ly_do or "").strip()
	if anh:
		tra.vgb_anh_tra = anh
	tra.remarks = dien_giai(ly_do, ghi_chu, goc.name)
	for d in sach:
		g = dong_goc.get(d["ma"])
		tra.append(
			"items",
			{
				"item_code": d["ma"],
				# ERPNext ghi dong tra bang SO AM. Quen dau tru o day thi
				# phieu tra lai lam TANG ton va TANG cong no.
				"qty": -abs(d["sl"]),
				"rate": flt(g.rate) if g else 0,
				"uom": g.uom if g else None,
				"stock_uom": g.stock_uom if g else None,
				"conversion_factor": flt(g.conversion_factor) if g else 1,
				"warehouse": g.warehouse if g else None,
				"purchase_receipt_item": g.name if g else None,
			},
		)
	tra.flags.ignore_permissions = True
	tra.insert(ignore_permissions=True)
	tra.submit()
	frappe.db.commit()
	return {"ok": 1, "name": tra.name, "trang_thai": "Đã ghi sổ", "phieu_goc": goc.name}


@frappe.whitelist()
def ds_phieu(gioi_han=40):
	"""Danh sach phieu tra hang gan day."""
	_kiem_quyen()
	ds = frappe.get_all(
		"Purchase Receipt",
		filters={"is_return": 1, "docstatus": ["<", 2]},
		fields=[
			"name",
			"posting_date",
			"docstatus",
			"supplier",
			"supplier_name",
			"return_against",
			"grand_total",
			"owner",
			"remarks",
			"vgb_ly_do_tra",
		],
		order_by="creation desc",
		limit_page_length=int(gioi_han or 40),
	)
	ten = {}
	for u in {d.owner for d in ds}:
		ten[u] = frappe.db.get_value("User", u, "full_name") or u
	for d in ds:
		d["nguoi_tao"] = ten.get(d.owner, d.owner)
		d["trang_thai"] = "Chờ ghi sổ" if d.docstatus == 0 else "Đã ghi sổ"
		d["so_dong"] = frappe.db.count("Purchase Receipt Item", {"parent": d.name})
	return ds


@frappe.whitelist()
def chi_tiet(name=None):
	"""Mot phieu tra hang kem cac dong."""
	_kiem_quyen()
	doc = frappe.get_doc("Purchase Receipt", name)
	if not cint(doc.get("is_return")):
		frappe.throw("Phiếu %s không phải phiếu trả hàng." % name)
	return {
		"name": doc.name,
		"ngay": str(doc.posting_date),
		"docstatus": doc.docstatus,
		"trang_thai": "Chờ ghi sổ" if doc.docstatus == 0 else "Đã ghi sổ",
		"ncc": doc.supplier,
		"ten_ncc": doc.supplier_name or doc.supplier,
		"phieu_goc": doc.get("return_against") or "",
		"ly_do": doc.get("vgb_ly_do_tra") or "",
		"anh": doc.get("vgb_anh_tra") or "",
		"ghi_chu": doc.remarks or "",
		"nguoi_tao": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"tong_tien": abs(flt(doc.grand_total)),
		"dong": [
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				# Hien SO DUONG cho nguoi doc. Trong so ERPNext no la so am,
				# nhung mot dong "tra ve -3 cai" doc len nghe nhu tra nguoc.
				"sl": abs(flt(d.qty)),
				"tien": abs(flt(d.amount)),
				"kho": d.warehouse,
			}
			for d in doc.items
		],
	}
