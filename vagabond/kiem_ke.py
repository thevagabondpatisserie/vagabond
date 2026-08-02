"""Kiem ke xoay vong hang ngay (anh Viet chot 02/08/2026).

Y anh Viet: cho MOI nhan vien di kiem hang moi ngay de khong bi don viec cuoi
thang. Hai rang buoc anh chot:

1. Nhan vien chi DEM va chot phieu; MOI dieu chinh ton kho deu phai qua quan
   ly duyet (trang thai "Cho duyet" -> quan ly ghi so). Server chan them mot
   lop: chi Stock Manager moi tao duoc Stock Reconciliation.
2. May tu chia lich xoay vong, nhan vien mo app la thay hom nay dem gi, khong
   phai tu nghi - trong thang di het mot vong kho, hang dat tien dem day hon.

Cach chia hang (kieu ABC theo gia tri ton):
- Xep moi ma theo gia tri ton (so luong x gia von) giam dan trong tung kho.
- Cong don den 70% gia tri = hang A, den 90% = hang B, con lai hang C.
- Chu ky dem: A moi 7 ngay, B 15 ngay, C 30 ngay.
- Moi ngay chi liet ke toi da MOI_NGAY ma qua han lau nhat, de mot ca lam
  duoc trong 15-20 phut chu khong thanh gong ganh.
"""

import frappe
from frappe.utils import flt, getdate, nowdate

VAI_DEM = {
	"System Manager",
	"Stock Manager",
	"Stock User",
	"Kiểm kê viên",
	"Bộ phận đặt hàng",
	"Manufacturing User",
}
VAI_DUYET = {"System Manager", "Stock Manager"}

CHU_KY = {"A": 7, "B": 15, "C": 30}
NGUONG_A = 0.70
NGUONG_B = 0.90
MOI_NGAY = 40


def _duoc_dem():
	if not VAI_DEM & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền kiểm kê.")


def duoc_duyet():
	return bool(VAI_DUYET & set(frappe.get_roles()))


def _ngay_dem_gan_nhat(kho):
	"""Ma hang -> ngay duoc dem gan nhat trong kho do."""
	rows = frappe.db.sql(
		"""
		select ct.item_code as ma, max(p.ngay_kiem) as ngay
		from `tabChi Tiet Kiem Ke` ct
		join `tabPhieu Kiem Ke` p on p.name = ct.parent
		where p.kho = %s
		  and p.trang_thai in ('Đã chốt', 'Đã ghi sổ')
		  and ct.da_dem = 1
		group by ct.item_code
		""",
		(kho,),
		as_dict=True,
	)
	return {r["ma"]: getdate(r["ngay"]) for r in rows if r.get("ngay")}


def _ton_theo_kho(kho):
	"""Cac ma con ton trong kho kem gia tri ton."""
	return frappe.db.sql(
		"""
		select b.item_code as ma, b.actual_qty as sl, b.stock_value as gia_tri,
		       i.item_name as ten, i.item_group as nhom, i.stock_uom as dvt
		from `tabBin` b
		join `tabItem` i on i.name = b.item_code
		where b.warehouse = %s and b.actual_qty != 0 and i.disabled = 0
		""",
		(kho,),
		as_dict=True,
	)


def _xep_hang(ds):
	"""Gan hang A/B/C cho tung ma theo gia tri ton luy ke."""
	ds = sorted(ds, key=lambda x: flt(x.get("gia_tri")), reverse=True)
	tong = sum(flt(x.get("gia_tri")) for x in ds) or 1.0
	luy = 0.0
	for x in ds:
		luy += flt(x.get("gia_tri"))
		ty = luy / tong
		x["hang"] = "A" if ty <= NGUONG_A else ("B" if ty <= NGUONG_B else "C")
	return ds


@frappe.whitelist()
def lich_hom_nay(kho=None, gioi_han=None):
	"""Danh sach ma can dem hom nay cua mot kho.

	Tra ca ma chua bao gio duoc dem (uu tien cao nhat) lan ma da qua chu ky.
	"""
	_duoc_dem()
	if not kho:
		frappe.throw("Chưa chọn kho.")
	gioi_han = int(gioi_han or MOI_NGAY)
	hom_nay = getdate(nowdate())

	ds = _xep_hang(_ton_theo_kho(kho))
	lan_cuoi = _ngay_dem_gan_nhat(kho)

	den_han = []
	for x in ds:
		ngay = lan_cuoi.get(x["ma"])
		chu_ky = CHU_KY[x["hang"]]
		if ngay is None:
			qua_han = 9999  # chua bao gio dem
		else:
			qua_han = (hom_nay - ngay).days - chu_ky
		if qua_han >= 0:
			x["ngay_dem_cuoi"] = str(ngay) if ngay else ""
			x["qua_han"] = qua_han
			x["chu_ky"] = chu_ky
			den_han.append(x)

	# Qua han lau nhat len truoc; cung muc thi hang dat tien truoc.
	den_han.sort(key=lambda x: (-x["qua_han"], -flt(x.get("gia_tri"))))
	chon = den_han[:gioi_han]
	return {
		"kho": kho,
		"ngay": str(hom_nay),
		"tong_ma_ton": len(ds),
		"tong_den_han": len(den_han),
		"gioi_han": gioi_han,
		"duoc_duyet": 1 if duoc_duyet() else 0,
		"dong": [
			{
				"ma_hang": x["ma"],
				"ten": x.get("ten") or "",
				"nhom": x.get("nhom") or "",
				"dvt": x.get("dvt") or "",
				"hang": x["hang"],
				"ton": flt(x.get("sl")),
				"ngay_dem_cuoi": x.get("ngay_dem_cuoi") or "",
				"qua_han": 0 if x["qua_han"] == 9999 else x["qua_han"],
				"chua_dem_bao_gio": 1 if x["qua_han"] == 9999 else 0,
			}
			for x in chon
		],
	}


@frappe.whitelist()
def tao_phieu_hom_nay(kho=None, gioi_han=None):
	"""Tao san mot Phieu Kiem Ke chua danh sach may chia cho hom nay.

	Nhan vien khong phai tu chon mon: mo app, bam mot nut la co phieu voi
	dung nhung ma den han, di dem roi dien so.
	"""
	_duoc_dem()
	lich = lich_hom_nay(kho, gioi_han)
	if not lich["dong"]:
		return {"ok": 0, "ly_do": "Hôm nay kho này không có mã nào đến hạn đếm."}

	doc = frappe.new_doc("Phieu Kiem Ke")
	doc.ngay_kiem = lich["ngay"]
	doc.kho = kho
	doc.pham_vi = "Tất cả"
	doc.trang_thai = "Đang kiểm"
	doc.nguoi_kiem = frappe.session.user
	doc.ghi_chu = "Máy chia lịch xoay vòng ngày %s" % lich["ngay"]
	for d in lich["dong"]:
		doc.append(
			"items",
			{
				"item_code": d["ma_hang"],
				"item_name": d["ten"],
				"item_group": d["nhom"],
				"dvt": d["dvt"],
				"ton_he_thong": d["ton"],
				"da_dem": 0,
			},
		)
	doc.so_mon = len(doc.items)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "so_mon": doc.so_mon}


@frappe.whitelist()
def phieu_cho_duyet():
	"""Danh sach phieu dang cho quan ly duyet."""
	_duoc_dem()
	return frappe.get_all(
		"Phieu Kiem Ke",
		filters={"trang_thai": "Chờ duyệt"},
		fields=["name", "ngay_kiem", "kho", "nguoi_kiem", "so_mon"],
		order_by="ngay_kiem desc, name desc",
		limit_page_length=100,
	)
