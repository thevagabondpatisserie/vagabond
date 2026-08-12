"""Quyen cua thu ngan tai quay (anh Viet 12/08/2026).

Fabi chia quyen bo mon lam ba muc, va anh Viet chot hoc theo:

  tu_do    - thu ngan tu bo mon, ke ca sau khi da in tam tinh
  gioi_han - bo mon thoai mai TRUOC khi in tam tinh; in tam tinh roi thi
             khong duoc bot mon nua va khong duoc them khuyen mai/giam gia,
             muon lam van duoc nhung phai co ma OTP cua quan ly ca
  duyet    - moi thay doi tren bill da luu deu phai co OTP quan ly

MAC DINH la "duyet" vi do dung la cach he dang chay tu truoc den gio. Noi
long quyen la viec cua nguoi chu, khong phai viec cua ban cap nhat phan
mem: mot ban deploy khong duoc tu nhien lam quay de bo mon hon hom qua.

Vi sao lay moc la "da in tam tinh": luc bam In tam tinh la may da luu hoa
don voi vgb_tam_tinh=1 va to phieu da nam trong tay khach. Tu do tro di
mon bien mat khoi bill la lech voi to khach dang cam.
"""

import frappe
from frappe.utils import cint, flt

from vagabond.lib import cfg

TRUONG = "vgb_quyen_bo_mon"
MAC_DINH = "duyet"

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager"}

MUC = [
	{
		"k": "tu_do",
		"ten": "Thu ngân bỏ món tự do",
		"mo": "Bỏ món lúc nào cũng được, kể cả sau khi đã in tạm tính đưa khách. "
		"Nhanh nhất, nhưng không còn dấu vết ai bớt món của bill nào.",
	},
	{
		"k": "gioi_han",
		"ten": "Giới hạn: in tạm tính rồi thì thôi",
		"mo": "Trước khi in tạm tính thì thu ngân sửa thoải mái. In tạm tính rồi "
		"thì không bớt món và không thêm khuyến mãi được nữa - vẫn làm được nếu "
		"quản lý ca cho mã OTP.",
	},
	{
		"k": "duyet",
		"ten": "Mọi thay đổi cần quản lý duyệt",
		"mo": "Bill đã lưu thì mọi lần sửa món, giảm giá hay phương thức thanh "
		"toán đều phải xin mã OTP của quản lý ca. Chặt nhất.",
	},
]


def muc():
	m = str((cfg().get(TRUONG) or "")).strip()
	return m if m in {x["k"] for x in MUC} else MAC_DINH


def _theo_ma(rows):
	"""Gom so luong theo ma hang.

	Gom theo MA HANG chu khong theo tung dong: thu ngan tach mot dong 2 cai
	thanh hai dong 1 cai (vi mot cai them ghi chu) thi khong phai la bo mon,
	khong duoc bat nham thanh vi pham.
	"""
	ra = {}
	for r in rows or []:
		if isinstance(r, dict):
			ma = (r.get("item_code") or "").strip()
			sl = flt(r.get("qty") or 0)
		else:
			ma = (getattr(r, "item_code", "") or "").strip()
			sl = flt(getattr(r, "qty", 0) or 0)
		if not ma:
			continue
		ra[ma] = ra.get(ma, 0.0) + sl
	return ra


def can_otp(si, items=None, giam_gia=None):
	"""Lan sua nay co phai xin OTP quan ly khong. Tra (can, vi_sao)."""
	m = muc()
	if m == "duyet":
		return True, "hệ đang đặt mức chặt nhất: bill đã lưu thì mọi thay đổi cần quản lý duyệt"
	if m == "tu_do":
		return False, ""

	# gioi_han
	if not cint(si.get("vgb_tam_tinh")):
		return False, ""
	if items is not None:
		cu = _theo_ma(si.get("items"))
		moi = _theo_ma(items)
		bot = [ma for ma, sl in cu.items() if moi.get(ma, 0.0) < sl - 0.0001]
		if bot:
			ten = frappe.db.get_value("Item", bot[0], "item_name") or bot[0]
			return True, (
				"bill này đã in tạm tính đưa khách rồi, bớt \"%s\" thì cần quản lý ca duyệt" % ten
			)
	if them_giam_gia(si, giam_gia):
		return True, "bill này đã in tạm tính đưa khách rồi, thêm giảm giá thì cần quản lý ca duyệt"
	return False, ""


def them_giam_gia(si, giam_gia):
	"""Co phai dang THEM giam gia vao mot bill DA IN TAM TINH khong.

	Tach rieng khoi can_otp vi duong pos_chot phai xet rieng: bill CHUA in
	tam tinh ma chot kem khuyen mai la nghiep vu thuong ngay, ba muc quyen
	deu cho qua. Neu dung chung can_otp o do thi muc "duyet" se doi OTP cho
	moi bill co khuyen mai - dung ngay giua gio dong khach.
	"""
	if giam_gia is None:
		return False
	if not cint(si.get("vgb_tam_tinh")):
		return False
	if muc() == "tu_do":
		return False
	return flt(giam_gia) > flt(si.get("discount_amount") or 0) + 0.5


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def cai_dat():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {
		"muc": muc(),
		"ds": MUC,
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
	}


@frappe.whitelist()
def luu(muc_moi=None):
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới đổi được quyền tại quầy.")
	m = str(muc_moi or "").strip()
	if m not in {x["k"] for x in MUC}:
		frappe.throw("Không có mức quyền %s." % (m or "(trống)"))
	cu = muc()
	frappe.db.set_single_value("Vagabond Settings", TRUONG, m)
	frappe.db.commit()
	if m != cu:
		_ghi_vet("Đổi quyền bỏ món tại quầy: %s -> %s" % (cu, m))
	return cai_dat()


def _ghi_vet(viec):
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
