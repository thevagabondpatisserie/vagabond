"""v678: voucher Grab Dine-Out chỉ giảm đúng PHẦN TIỆM CHỊU (anh Việt chốt
20/11/2026, phương án A).

Đo trên site 20/11/2026: báo cáo GrabFood của 418 bill mã GD- từ 17/09/2026,
cột "khuyến mãi" (phần quán chịu) chỉ có hai mức: 40.000 đ với voucher
200.000 đ (237 đơn) và 60.000 đ với voucher 300.000 đ (178 đơn). Phần còn
lại Grab trả. Trước bản này hai chương trình giảm đủ giá voucher, nên bill
thấp hơn tiền Grab trả.

Chỉ nâng chương trình còn ĐÚNG giá trị cũ (200.000, 300.000); chương trình đã
có người sửa thì để nguyên. Không đụng hoá đơn đã lập. Chạy lại không đổi gì.
"""
import re

import frappe

DT = "Vagabond CTKM"
# Giá voucher -> phần tiệm chịu (đ).
PHAN_TIEM_CHIU = {200000: 40000, 300000: 60000}
CHU_TEN = " (tiệm chịu %s)"


def la_voucher_grab(km):
	"""THUẦN: chương trình là voucher Grab Dine-Out (theo tên)."""
	return bool(re.search(r"grab[\s_-]*dine[\s_-]*out", str((km or {}).get("ten") or ""), re.I))


def nang(km):
	"""THUẦN: {gia_tri, ten} mới cho một chương trình voucher Grab còn giá trị
	cũ, hoặc None khi không phải voucher Grab, đã nâng, hay đã có người sửa."""
	if not la_voucher_grab(km) or (km.get("kieu_giam") or "") != "So tien":
		return None
	cu = int(round(float(km.get("gia_tri") or 0)))
	if cu not in PHAN_TIEM_CHIU:
		return None
	moi = PHAN_TIEM_CHIU[cu]
	ten = str(km.get("ten") or "")
	duoi = CHU_TEN % "{:,}".format(moi).replace(",", ".")
	return {"gia_tri": moi, "ten": ten if ten.endswith(duoi) else (ten + duoi)[:140]}


def execute():
	try:
		for km in frappe.get_all(DT, fields=["name", "ten", "kieu_giam", "gia_tri"]):
			moi = nang(km)
			if not moi:
				continue
			frappe.db.set_value(DT, km.name, moi, update_modified=True)
			frappe.get_doc(DT, km.name).add_comment(
				"Comment", "v678: voucher Grab Dine-Out chỉ giảm phần tiệm chịu %s đ (trước giảm đủ %s đ); phần còn lại Grab trả."
				% ("{:,}".format(moi["gia_tri"]).replace(",", "."), "{:,}".format(int(float(km.gia_tri))).replace(",", ".")))
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: v678 voucher Grab Dine-Out phần tiệm chịu")
