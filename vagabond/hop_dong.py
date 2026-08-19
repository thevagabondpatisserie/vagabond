"""Phan he hop dong ban hang: catering, event, teabreak, banh thiet ke, B2B.

Man hinh o app /bep goi cac endpoint nay. Mot hop dong gom nhieu hoa don
(Sales Invoice) gan qua truong custom_hop_dong; tien do thu tien tinh tu
grand_total va outstanding_amount cua cac hoa don da submit.
"""

import frappe
from frappe.utils import flt

# Anh Viet 14/08/2026: *"cấp quyền truy cập cho Loan Anh, thu mua và kế toán"*.
# Loan Anh dang co vai Sales User nen vao duoc ngay. Them thu mua va ke toan
# truong vao day cho du bo.
QUYEN = {
	"System Manager",
	"Sales User",
	"Sales Manager",
	"Accounts User",
	"Accounts Manager",
	"Purchase User",
	"Purchase Manager",
	"Bộ phận đặt hàng",
}


def _quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Không có quyền xem hợp đồng")


def _tong(name):
	"""Tong hop hoa don cua mot hop dong."""
	r = frappe.db.sql(
		"""select count(name), coalesce(sum(grand_total), 0), coalesce(sum(outstanding_amount), 0)
		from `tabSales Invoice` where custom_hop_dong = %s and docstatus = 1""",
		name,
	)[0]
	so_nhap = frappe.db.count(
		"Sales Invoice", {"custom_hop_dong": name, "docstatus": 0, "vgb_huy": 0}
	)
	da_xuat = flt(r[1])
	con_no = flt(r[2])
	return {
		"so_hd_chot": r[0],
		"so_hd_nhap": so_nhap,
		"da_xuat": da_xuat,
		"da_thu": da_xuat - con_no,
		"con_no": con_no,
	}


@frappe.whitelist()
def danh_sach(trang_thai=None):
	_quyen()
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	ds = frappe.get_all(
		"Hop Dong Ban Hang",
		filters=loc,
		fields=["name", "ten", "so_hop_dong", "loai", "trang_thai", "khach_hang", "ngay_su_kien", "gia_tri"],
		order_by="modified desc",
		limit_page_length=200,
	)
	for hd in ds:
		hd.update(_tong(hd["name"]))
	return ds


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	doc = frappe.get_doc("Hop Dong Ban Hang", name)
	hoa_don = frappe.get_all(
		"Sales Invoice",
		filters={"custom_hop_dong": name, "docstatus": ["<", 2], "vgb_huy": 0},
		fields=["name", "posting_date", "grand_total", "outstanding_amount", "docstatus", "customer_name"],
		order_by="posting_date desc",
		limit_page_length=100,
	)
	kq = {
		"hop_dong": {
			"name": doc.name,
			"ten": doc.ten,
			"so_hop_dong": doc.so_hop_dong,
			"loai": doc.loai,
			"trang_thai": doc.trang_thai,
			"khach_hang": doc.khach_hang,
			"ngay_ky": str(doc.ngay_ky or ""),
			"ngay_su_kien": str(doc.ngay_su_kien or ""),
			"gia_tri": flt(doc.gia_tri),
			"mo_ta": doc.mo_ta or "",
			"ghi_chu": doc.ghi_chu or "",
			# Khoi phap ly (anh Viet 18/08/2026). Man Chi tiet hop dong dua
			# vao doc "bao_gia" de biet co bay ba nut Xem truoc, Xuat PDF,
			# Gui Email hay khong: hop dong go tay khong co goc bao gia thi
			# khong dung duoc to phap ly, va khong bay nut ra roi de nguoi
			# ta bam vao chi de nhan mot cau bao loi.
			"bao_gia": doc.get("bao_gia") or "",
			"ten_khach": doc.get("ten_khach") or "",
			"ma_so_thue": doc.get("ma_so_thue") or "",
			"dia_chi": doc.get("dia_chi") or "",
			"dai_dien": doc.get("dai_dien") or "",
			"chuc_vu": doc.get("chuc_vu") or "",
			"dien_thoai": doc.get("dien_thoai") or "",
			"email": doc.get("email") or "",
			"dat_coc_pt": flt(doc.get("dat_coc_pt")),
			"dat_coc_tien": flt(doc.get("dat_coc_tien")),
			"dia_diem_giao": doc.get("dia_diem_giao") or "",
			"thoi_gian_giao": doc.get("thoi_gian_giao") or "",
			# Nguoi ky va ban scan phu luc (anh Viet 18/08/2026). Man chi
			# tiet phai doc duoc de biet con thieu gi truoc khi gui khach.
			"nguoi_ky_a": doc.get("nguoi_ky_a") or "",
			"chuc_vu_ky_a": doc.get("chuc_vu_ky_a") or "",
			"dt_ky_a": doc.get("dt_ky_a") or "",
			"email_ky_a": doc.get("email_ky_a") or "",
			"nguoi_ky_b": doc.get("nguoi_ky_b") or "",
			"chuc_vu_ky_b": doc.get("chuc_vu_ky_b") or "",
			"dt_ky_b": doc.get("dt_ky_b") or "",
			"email_ky_b": doc.get("email_ky_b") or "",
			"phu_luc_scan": doc.get("phu_luc_scan") or "",
		},
		"hoa_don": hoa_don,
	}
	kq.update(_tong(name))
	return kq


@frappe.whitelist()
def tao(ten, so_hop_dong=None, loai=None, khach_hang=None, ngay_ky=None, ngay_su_kien=None, gia_tri=0, mo_ta=None, ghi_chu=None):
	_quyen()
	doc = frappe.get_doc(
		{
			"doctype": "Hop Dong Ban Hang",
			"ten": ten,
			"so_hop_dong": so_hop_dong,
			"loai": loai or "Event - Catering",
			"khach_hang": khach_hang or None,
			"ngay_ky": ngay_ky or None,
			"ngay_su_kien": ngay_su_kien or None,
			"gia_tri": flt(gia_tri),
			"mo_ta": mo_ta,
			"ghi_chu": ghi_chu,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def doi_trang_thai(name, trang_thai):
	_quyen()
	hop_le = {"Nháp", "Đang thực hiện", "Hoàn tất", "Đã thanh lý", "Huỷ"}
	if trang_thai not in hop_le:
		frappe.throw("Trạng thái không hợp lệ")
	frappe.db.set_value("Hop Dong Ban Hang", name, "trang_thai", trang_thai)
	return trang_thai


@frappe.whitelist()
def sua_nguoi_ky(name, nguoi_ky_a=None, chuc_vu_ky_a=None, dt_ky_a=None, email_ky_a=None,
                 nguoi_ky_b=None, chuc_vu_ky_b=None, dt_ky_b=None, email_ky_b=None):
	"""Sua bon o cua khoi chu ky sau khi da tao hop dong.

	Anh Viet 18/08/2026: *"Khoi chu ky cuoi hop dong tuyet doi khong duoc
	ghi Ms./Mr. va khong duoc lay mac dinh ten cua ban Sales"*. Man tao hop
	dong da hoi bon o nay, nhung go nham thi phai sua duoc, khong bat lam
	lai ca to.

	Bo xung ho ngay tai day chu khong tin vao man hinh: cung mot ham voi
	luc tao thi go kieu gi cung ra mot ket qua.
	"""
	_quyen()
	from vagabond.hop_dong_pdf import _bo_xung_ho

	frappe.db.set_value("Hop Dong Ban Hang", name, {
		"nguoi_ky_a": _bo_xung_ho(nguoi_ky_a),
		"chuc_vu_ky_a": (chuc_vu_ky_a or "").strip(),
		"dt_ky_a": (dt_ky_a or "").strip(),
		"email_ky_a": (email_ky_a or "").strip(),
		"nguoi_ky_b": _bo_xung_ho(nguoi_ky_b),
		"chuc_vu_ky_b": (chuc_vu_ky_b or "").strip(),
		"dt_ky_b": (dt_ky_b or "").strip(),
		"email_ky_b": (email_ky_b or "").strip(),
	})
	return True


@frappe.whitelist()
def go_phu_luc_scan(name):
	"""Go ban scan phu luc ra khoi hop dong.

	QT-20: khong xoa han tep, chi bo tro tren hop dong. Tep van nam trong
	kho tep cua he thong, can thi tim lai duoc.
	"""
	_quyen()
	frappe.db.set_value("Hop Dong Ban Hang", name, "phu_luc_scan", "")
	return True


@frappe.whitelist()
def gan_hoa_don(hop_dong, si_name, go=0):
	"""Gan (hoac go) mot hoa don vao hop dong. Dung db_set de gan duoc ca
	hoa don da submit (custom field, khong dung cham vao so lieu)."""
	_quyen()
	if not frappe.db.exists("Sales Invoice", si_name):
		frappe.throw("Không có hoá đơn %s" % si_name)
	frappe.db.set_value("Sales Invoice", si_name, "custom_hop_dong", None if int(go or 0) else hop_dong)
	return si_name


@frappe.whitelist()
def hoa_don_chua_gan(khach_hang=None):
	"""Hoa don 90 ngay gan nhat chua gan hop dong, de tick gan."""
	_quyen()
	loc = {
		"custom_hop_dong": ["in", ["", None]],
		"docstatus": ["<", 2],
		# Hoa don da huy thi khong gan vao hop dong duoc: gan roi la so tien
		# hop dong sai ma khong ai nhin ra.
		"vgb_huy": 0,
		"posting_date": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -90)],
	}
	if khach_hang:
		loc["customer"] = khach_hang
	return frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=["name", "posting_date", "customer_name", "grand_total", "docstatus"],
		order_by="posting_date desc",
		limit_page_length=60,
	)
