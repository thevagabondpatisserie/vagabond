"""Xuat ban cho khach si va khach doanh nghiep - anh Viet giao 02/09/2026.

De xuong Phieu giao hang (Delivery Note) cua ERPNext. Day la chung tu duy
nhat vua tru ton, vua ghi GIA VON HANG BAN, vua noi lai duoc voi hoa don.

MOT DIEU PHAI DOC TRUOC KHI DUNG MAN NAY
----------------------------------------
Hom nay MOI hoa don ban hang cua tiem deu tao voi `update_stock = 0`: ban
le tai quay, don Pancake, don san giao do an, khong don nao tru kho ca.
Ton kho dang dung duoc la nho cac ban kiem ke roi nan so ve cho khop.

Nghia la man nay lam ton kho di THEO MOT DUONG KHAC voi ban le. Cu the:

  Ban le tai quay  -> hoa don ghi doanh thu, ton kho KHONG doi
  Xuat ban si      -> phieu giao hang tru ton va ghi gia von THAT

Hai duong khac nhau khong sai, va cung khong phai loi cua man nay: no la
hien trang cua he tu truoc. Nhung phai biet de khong hoang khi thay ton
cua mot ma banh tut nhanh hon binh thuong.

BAY PHAI TRANH: mot don giao roi thi ke toan lam hoa don cho don do PHAI
de `update_stock = 0` nhu binh thuong. Neu mot ngay nao do anh Viet chot
bat tru kho cho hoa don ban, thi phai ra soat lai cho nay ngay, khong thi
mot don si bi tru kho hai lan - mot lan o phieu giao, mot lan o hoa don.
Da ghi canh bao nay ngay tren man hinh cho nguoi lap doc.

Luat phan quyen
---------------
Sales, kho, ke toan lap duoc. Ghi so NGAY: hang da len xe di giao thi cho
duyet khong con y nghia gi, ma cho la sai ton trong luc cho.

Quy tac nha
-----------
QT-19  Ton kho LUON kiem lai o may chu truoc khi ghi.
QT-20  Khong xoa chung tu. Phieu sai thi huy dung nghiep vu ben may tinh.
QT-24  Cau bao loi phai noi nguoi dung lam gi tiep.
"""

import frappe
from frappe.utils import add_days, cint, flt, nowdate

from vagabond import xuat_kho

QUYEN_BAN = {
	"System Manager",
	"Sales Manager",
	"Sales User",
	"Stock Manager",
	"Stock User",
	"Accounts Manager",
	"Bộ phận đặt hàng",
}

TRUONG_MOI = {
	"Delivery Note": [
		{
			"fieldname": "vgb_nguoi_nhan",
			"label": "Người nhận hàng",
			"fieldtype": "Data",
			"insert_after": "customer_name",
			"description": "Tên người ký nhận bên khách, để đối chiếu khi có tranh chấp.",
		},
		{
			"fieldname": "vgb_hop_dong",
			"label": "Hợp đồng",
			"fieldtype": "Link",
			"options": "Hop Dong Ban Hang",
			"insert_after": "vgb_nguoi_nhan",
			"description": "Đơn giao theo hợp đồng nào, để trống nếu là đơn lẻ.",
		},
		# O DIEN GIAI RIENG (sua 03/09/2026). Phieu giao hang cua ERPNext KHONG
		# co o `remarks` nhu Hoa don hay Phieu kho. Ban v387 ghi vao
		# `doc.remarks` - Frappe im lang bo qua nen ghi chu roi mat - va doc
		# `remarks` trong get_all - MariaDB nem "Unknown column", danh sach
		# phieu do ba lan hom 03/09 ma man chi hien "chua co phieu nao" vi
		# loi bi nuot. Loi cua phien v387, khong phai cua ai khac.
		{
			"fieldname": "vgb_dien_giai",
			"label": "Diễn giải",
			"fieldtype": "Small Text",
			"insert_after": "vgb_hop_dong",
			"description": "Máy ghép từ khách, người nhận và ghi chú lúc lập phiếu trên app.",
		},
	]
}

# Ten o dien giai, dung o BON cho ben duoi. Mot hang so de khong ai go
# "remarks" lai lan nua.
O_DIEN_GIAI = "vgb_dien_giai"


# ------------------------------------------------------------- phần thuần


def thieu_gi(khach, kho, so_dong):
	"""Phieu nay con thieu gi truoc khi ghi so. Ham THUAN.

	Tra ve danh sach cau nhac, rong la du. Man hinh va may chu dung chung
	mot bo luat thay vi moi ben tu che mot bo.
	"""
	nhac = []
	if not (khach or "").strip():
		nhac.append("Chưa chọn khách hàng.")
	if not (kho or "").strip():
		nhac.append("Chưa chọn kho xuất.")
	if cint(so_dong) <= 0:
		nhac.append("Chưa có món nào trong phiếu.")
	return nhac


def dien_giai(ten_khach, nguoi_nhan, ghi_chu):
	"""Dong dien giai in tren phieu giao. Ham THUAN."""
	phan = ["Xuất bán sỉ"]
	if (ten_khach or "").strip():
		phan.append(ten_khach.strip())
	if (nguoi_nhan or "").strip():
		phan.append("Người nhận: %s" % nguoi_nhan.strip())
	dong = " - ".join(phan)
	if (ghi_chu or "").strip():
		dong += ". " + ghi_chu.strip()
	return dong


def canh_bao_trung_kho():
	"""Cau canh bao hien ngay tren man lap phieu. Ham THUAN.

	Viet thanh ham de ca kiem chot duoc rang cau nay CON o do. Bo cau nay
	di la nguoi lap khong con biet vi sao ton kho cua don si di khac ban le.
	"""
	return (
		"Phiếu giao hàng này TRỪ KHO thật và ghi giá vốn. Hoá đơn cho đơn "
		"này vẫn để như bình thường, kế toán không bật thêm Cập nhật kho, "
		"không thì hàng bị trừ hai lần."
	)


# ------------------------------------------------ phần chạm Frappe


def _kiem_quyen():
	if not QUYEN_BAN & set(frappe.get_roles()):
		frappe.throw(
			"Màn xuất bán sỉ chỉ mở cho Sales, kho và kế toán. Cần vào đây "
			"thì báo quản lý cấp thêm quyền."
		)


@frappe.whitelist()
def khoi_dong():
	"""Kho va cau canh bao cho man lap phieu."""
	_kiem_quyen()
	ct = xuat_kho._cong_ty()
	return {
		"cong_ty": ct,
		"kho": xuat_kho._kho_that(ct),
		"canh_bao": canh_bao_trung_kho(),
		"toi": frappe.session.user,
	}


@frappe.whitelist()
def tim_khach(tu_khoa=None, gioi_han=30):
	"""Tim khach hang theo ten hoac ma.

	Di qua cua nay chu khong de app goi thang Customer: vai Kiem ke vien va
	Stock User khong doc duoc Customer bang API chuan, ma ho la nguoi hay
	phai soan hang di giao.
	"""
	_kiem_quyen()
	tu = (tu_khoa or "").strip()
	dieu_kien = {"disabled": 0}
	if tu:
		return frappe.get_all(
			"Customer",
			filters=dieu_kien,
			or_filters={"name": ["like", "%" + tu + "%"], "customer_name": ["like", "%" + tu + "%"]},
			fields=["name", "customer_name"],
			order_by="customer_name",
			limit_page_length=int(gioi_han or 30),
		)
	return frappe.get_all(
		"Customer",
		filters=dieu_kien,
		fields=["name", "customer_name"],
		order_by="modified desc",
		limit_page_length=int(gioi_han or 30),
	)


@frappe.whitelist()
def luu(khach=None, kho=None, nguoi_nhan=None, hop_dong=None, ghi_chu=None, dong=None):
	"""Lap phieu giao hang va GHI SO ngay."""
	_kiem_quyen()
	sach = xuat_kho._doc_dong(dong)
	nhac = thieu_gi(khach, kho, len(sach))
	if nhac:
		frappe.throw(" ".join(nhac))
	if not frappe.db.exists("Customer", khach):
		frappe.throw("Không tìm thấy khách hàng %s." % khach)
	xuat_kho._chan_qua_ton(kho, sach)

	ct = xuat_kho._cong_ty()
	ten_khach = frappe.db.get_value("Customer", khach, "customer_name") or khach
	doc = frappe.new_doc("Delivery Note")
	doc.customer = khach
	doc.company = ct
	doc.posting_date = nowdate()
	doc.set_posting_time = 0
	doc.set_warehouse = kho
	doc.vgb_nguoi_nhan = (nguoi_nhan or "").strip()
	if hop_dong and frappe.db.exists("Hop Dong Ban Hang", hop_dong):
		doc.vgb_hop_dong = hop_dong
	doc.set(O_DIEN_GIAI, dien_giai(ten_khach, nguoi_nhan, ghi_chu))
	for d in sach:
		doc.append("items", {"item_code": d["ma"], "qty": d["sl"], "warehouse": kho})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Đã ghi sổ"}


@frappe.whitelist()
def ds_phieu(gioi_han=40, so_ngay=60):
	"""Danh sach phieu giao hang gan day."""
	_kiem_quyen()
	so_ngay = max(1, min(cint(so_ngay) or 60, 365))
	ds = frappe.get_all(
		"Delivery Note",
		filters={
			"docstatus": ["<", 2],
			"is_return": 0,
			"posting_date": [">=", add_days(nowdate(), -so_ngay)],
		},
		fields=[
			"name",
			"posting_date",
			"docstatus",
			"customer",
			"customer_name",
			"set_warehouse",
			"grand_total",
			"owner",
			O_DIEN_GIAI,
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
		d["so_dong"] = frappe.db.count("Delivery Note Item", {"parent": d.name})
		# App cu doc `remarks`; giu ten do trong goi tra ve de man khong doi.
		d["remarks"] = d.get(O_DIEN_GIAI) or ""
	return ds


@frappe.whitelist()
def chi_tiet(name=None):
	"""Mot phieu giao hang kem cac dong."""
	_kiem_quyen()
	doc = frappe.get_doc("Delivery Note", name)
	return {
		"name": doc.name,
		"ngay": str(doc.posting_date),
		"docstatus": doc.docstatus,
		"trang_thai": "Chờ ghi sổ" if doc.docstatus == 0 else "Đã ghi sổ",
		"khach": doc.customer,
		"ten_khach": doc.customer_name or doc.customer,
		"kho": doc.get("set_warehouse") or "",
		"nguoi_nhan": doc.get("vgb_nguoi_nhan") or "",
		"hop_dong": doc.get("vgb_hop_dong") or "",
		"ghi_chu": doc.get(O_DIEN_GIAI) or "",
		"nguoi_tao": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"tong_tien": flt(doc.grand_total),
		"dong": [
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"sl": flt(d.qty),
				"tien": flt(d.amount),
				"kho": d.warehouse,
			}
			for d in doc.items
		],
	}
