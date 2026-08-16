"""Hang OWNER: don tieu dung noi bo, giam 100%, khong xuat hoa don dien tu.

Chot voi anh Viet 16/08/2026:
  1. Thu ngan van thao tac len don binh thuong tren POS de tru kho.
  2. He tu ap giam 100%, KHONG cong don voi bat ky khuyen mai nao khac.
  3. Don 0 dong nay TUYET DOI khong xuat hoa don dien tu.
  4. Ve ke toan, ghi vao Chi phi tiep khach thay vi Doanh thu.

Ba viec dau lam duoc bang ma nguon va nam trong tep nay. VIEC THU TU KHONG
NAM O DAY va co chu y - xem ghi chu "Vi sao chua tu dinh khoan" o cuoi tep.
"""

import frappe
from frappe.utils import cint, flt

HANG_NOI_BO = "OWNER"
SI = "Sales Invoice"


TRUONG_MOI = {
	"Sales Invoice": [
		{
			"fieldname": "vgb_noi_bo",
			"label": "Đơn tiêu dùng nội bộ (hạng OWNER)",
			"fieldtype": "Check",
			"insert_after": "vgb_giam_diem",
			"read_only": 1,
			"description": (
				"Đơn của khách hạng OWNER: giảm 100%, không xuất hoá đơn điện tử, "
				"và kế toán bóc riêng khỏi doanh thu để đưa vào chi phí tiếp khách."
			),
		}
	]
}


def la_noi_bo(khach):
	"""Khach nay co phai hang noi bo khong. Nhan ma khach hoac None."""
	if not khach:
		return False
	try:
		return (frappe.db.get_value("Customer", khach, "vgb_hang") or "").strip().upper() == HANG_NOI_BO
	except Exception:
		return False


def khach_cua_to(si):
	"""Khach an uu dai cua to nay. Uu tien o khach than thiet tren don."""
	return (si.get("vgb_khach_no") or "").strip() or (si.get("customer") or "").strip()


def giam_100(si):
	"""To nay co phai don noi bo khong. THUAN theo nghia khong ghi gi."""
	return la_noi_bo(khach_cua_to(si))


def dat_co_noi_bo(si):
	"""Bat co tren to, de ke toan loc ra duoc bang mot bo loc.

	Dung .get() truoc khi gan: cot nay do ma nguon khai, co the chua ton tai
	neu deploy ma chua Migrate. Tu khi co luong tu Migrate thi truong hop do
	gan nhu khong con, nhung ham van phai chay duoc.
	"""
	try:
		si.vgb_noi_bo = 1 if giam_100(si) else 0
	except Exception:
		pass


def chan_hoa_don_dien_tu(si):
	"""Nem loi neu ai do co xuat hoa don dien tu cho don noi bo.

	Dat o day chu khong chi an nut tren giao dien: nut an chi chan duoc
	nguoi bam nut, con duong tu dong (tu_xuat_hddt) va duong goi ham thang
	tu Desk thi khong. Hoa don dien tu da gui sang co quan thue thi rat kho
	go lai - anh Viet dan rat ky ngay 13/08/2026 sau vu phai vao m-invoice
	huy tay 135 to.
	"""
	if not giam_100(si):
		return
	frappe.throw(
		"Đơn %s là đơn tiêu dùng nội bộ hạng %s nên không xuất hoá đơn điện tử. "
		"Cần hoá đơn cho đơn này thì phải đổi khách sang khách thường trước."
		% (si.get("name"), HANG_NOI_BO)
	)


def ap_giam_noi_bo(si):
	"""Dat giam 100% cho to noi bo. Tra True neu da ap.

	Dung additional_discount_percentage chu KHONG tu tinh so tien: de
	ERPNext tu quy ra tien thi con so luon dung theo thue va theo tung dong,
	con tu tinh la sai moi khi co thue suat khac nhau tren mot to.
	"""
	if not giam_100(si):
		return False
	si.apply_discount_on = "Grand Total"
	si.additional_discount_percentage = 100
	# KHONG cong don: xoa moi khoan giam khac de khong ai cong nham hai lan.
	si.discount_amount = 0
	try:
		si.vgb_giam_diem = 0
	except Exception:
		pass
	dat_co_noi_bo(si)
	return True


def truoc_khi_luu(doc, method=None):
	"""Hook before_validate cua Sales Invoice.

	Vi sao dat o before_validate chu khong o tung ham cua POS
	---------------------------------------------------------
	Co it nhat nam duong tao ra hoac sua mot hoa don: pos_luu, pos_chot,
	pos_sua_don, nhip dong bo Pancake, va nguoi go thang tren Desk. Gan
	vao tung duong thi hom nao them duong thu sau la quen, ma quen o day
	nghia la mot don noi bo di thang vao doanh thu.

	before_validate chay TRUOC khi ERPNext tinh lai thue va tong tien, nen
	dat additional_discount_percentage o day thi may tu quy ra so tien.
	Neu dat o validate thi tong tien da tinh xong roi, con so se khong an.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		if giam_100(doc):
			ap_giam_noi_bo(doc)
		else:
			dat_co_noi_bo(doc)
	except Exception:
		# Khong duoc lam hong viec luu hoa don. Hong thi ghi nhat ky roi thoi.
		frappe.log_error(frappe.get_traceback(), "noi_bo: truoc khi luu")


# ---------------------------------------------------------------------------
# Vi sao chua tu dinh khoan vao Chi phi tiep khach
# ---------------------------------------------------------------------------
#
# Anh Viet yeu cau ghi gia tri don nay vao Chi phi tiep khach thay vi Doanh
# thu. Em lam ba viec dau va DUNG LAI o viec thu tu, co chu y, vi hai le.
#
# Le thu nhat, ky thuat. Mot to giam 100% thi Grand Total bang 0, nen KHONG
# CON SO TIEN NAO de dua vao chi phi: but toan se la Doanh thu 0, Gia von
# van chay binh thuong. Muon co so tien thi phai KHONG giam 100%, ma ghi so
# binh thuong roi dua mot but chuyen tu Phai thu sang Chi phi tiep khach.
# Tuc la hai cach lam nay LOAI TRU NHAU, khong the vua giam 100% vua ghi
# chi phi theo gia tri don.
#
# Le thu hai, thue. Hang dung de bieu tang hoac tieu dung noi bo o Viet Nam
# co quy dinh rieng ve viec co phai xuat hoa don va ke khai thue GTGT dau ra
# hay khong. Em khong phai nguoi tu van thue va khong duoc phep doan ho.
#
# Nen viec thu tu phai la mot quyet dinh cua chi Dung, khong phai cua em.
# Ba cach lam va danh doi cua tung cach nam trong tai lieu trinh anh ngay
# 16/08/2026. Khi nao chi Dung chot thi em gan tiep vao day.
