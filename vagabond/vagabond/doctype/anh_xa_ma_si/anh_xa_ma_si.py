"""Anh xa ma si ve ma banh goc.

Anh Viet chot 03/08/2026 (huong B): don si van len tren Pancake la chinh,
moi khach si giu ma rieng cua minh (BAWS00001 Croissant Plain Ravie 30.000,
BAWS00011 Croissant Plain Society 32.000, BAWS00015 Ristreet 37.000,
BAWS00019 Rolu 40.000... deu la MOT cai banh Croissant Plain). Ban tren
Pancake bang ma rieng thi sales chon nhanh va dung gia tung khach; nhung ve
den Next thi 20 ma si do phai gop lai thanh khoang 11 ma banh that, neu
khong thi ton kho tach vun, gia von phai khai lai cho tung ma, bao cao ban
chay bi chia nho.

Bang nay lam dung viec do: mot dong = mot ma si tro ve mot ma banh goc.
Khi don Pancake ve toi vagabond.ban_hang._dong_hang thi ma si bi thay bang
ma goc, con GIA thi GIU NGUYEN theo dong don (tuc gia si cua khach do),
khong lay theo bang gia cua ma goc.

An toan: moi dong co o "Dang ap dung" mac dinh TAT. Em dien san ma goc de
xuat, anh Viet tich xac nhan tung dong thi luc do he thong moi doi. Chua
tich thi don ve van giu nguyen ma si nhu hien nay, khong co gi thay doi.

Pham vi: CHI ap dung o lop hoa don va kho. Bang kiem banh (kiem_banh.py)
loc theo tien to BAWC/BAWS nen KHONG dung anh xa - anh Viet yeu cau ngay
02/08 la mo them nhom BAWS de theo doi banh si tren bang kiem banh, gop ve
ma goc BANU/BAEN o do se lam bien mat cac dong ay.
"""

import frappe
from frappe.model.document import Document


class AnhXaMaSi(Document):
	def validate(self):
		if self.ma_goc and self.ma_goc == self.ma_si:
			frappe.throw("Mã gốc trùng luôn mã sỉ thì ánh xạ không có ý nghĩa.")
		if self.hoat_dong and not self.ma_goc:
			frappe.throw(
				"Chưa chọn mã bánh gốc thì không bật được 'Đang áp dụng'. "
				"Chọn mã gốc trước rồi hãy tích."
			)

	def on_update(self):
		xoa_bo_nho()

	def after_delete(self):
		xoa_bo_nho()


def xoa_bo_nho():
	frappe.cache().delete_value("vagabond_anh_xa_ma_si")


def bang_anh_xa():
	"""Tra {ma_si: ma_goc} cho cac dong DANG AP DUNG. Co nho dem."""
	bang = frappe.cache().get_value("vagabond_anh_xa_ma_si")
	if bang is None:
		bang = {}
		if frappe.db.table_exists("Anh Xa Ma Si"):
			for d in frappe.get_all(
				"Anh Xa Ma Si",
				filters={"hoat_dong": 1},
				fields=["ma_si", "ma_goc"],
			):
				if d.ma_si and d.ma_goc:
					bang[d.ma_si] = d.ma_goc
		frappe.cache().set_value("vagabond_anh_xa_ma_si", bang)
	return bang


def doi_ma(ma):
	"""Doi mot ma si sang ma banh goc neu dong anh xa dang bat."""
	if not ma:
		return ma
	goc = bang_anh_xa().get(ma)
	if goc and frappe.db.exists("Item", goc):
		return goc
	return ma
