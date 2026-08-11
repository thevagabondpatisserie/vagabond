"""Combo: phoi may mon thanh mot goi co gia re hon tong le.

Luc tinh tien, cashier bam ma combo thi may RA combo thanh tung mon thanh
phan roi dat mot dong giam gia ben duoi (anh Viet 11/08/2026). Lam vay vi:
- bep va tem dan mon phai thay ten mon that, khong ai lam duoc "combo"
- doanh thu tung mon van dung, bao cao mon ban chay khong bi lech
- kiem banh tru so dung tung ma banh
Bill in ra KHONG in ma combo.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt


def sinh_ma_combo():
	chu = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	for _ in range(40):
		ma = "CB" + "".join(chu[int(c, 16) % len(chu)] for c in frappe.generate_hash(length=4))
		if not frappe.db.exists("Vagabond Combo", ma):
			return ma
	frappe.throw("Không sinh được mã combo, thử lại giúp em.")


def gia_ban_mon(item_code):
	"""Gia ban le dang hieu luc cua mot mon."""
	gia = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "selling": 1},
		"price_list_rate",
		order_by="valid_from desc, modified desc",
	)
	return flt(gia)


class VagabondCombo(Document):
	def autoname(self):
		if not self.ma_combo:
			self.ma_combo = sinh_ma_combo()
		self.name = self.ma_combo

	def validate(self):
		if not self.nguoi_tao:
			self.nguoi_tao = frappe.session.user
		if not self.dong:
			frappe.throw("Combo phải có ít nhất một món.")

		tong = 0.0
		for d in self.dong:
			if flt(d.so_luong) <= 0:
				frappe.throw("Số lượng của %s phải lớn hơn 0." % d.item_code)
			if not flt(d.gia_goc):
				d.gia_goc = gia_ban_mon(d.item_code)
			if not flt(d.gia_goc):
				frappe.throw(
					"Món %s chưa có giá bán trong bảng giá. Điền giá gốc vào dòng "
					"đó giúp em, không thì máy không biết combo tiết kiệm bao nhiêu."
					% d.item_code
				)
			d.thanh_tien = flt(d.gia_goc) * flt(d.so_luong)
			tong += d.thanh_tien
		self.gia_goc = tong

		if self.kieu == "Gia tron goi":
			if flt(self.gia_combo) <= 0:
				frappe.throw("Combo giá trọn gói thì phải điền giá bán của combo.")
			if flt(self.gia_combo) > tong:
				frappe.throw(
					"Giá combo %s đang CAO HƠN tổng giá lẻ %s. Khách mua lẻ còn rẻ hơn."
					% (flt(self.gia_combo), tong)
				)
			self.tiet_kiem = tong - flt(self.gia_combo)
		elif self.kieu == "Giam phan tram":
			if not 0 < flt(self.gia_tri) <= 100:
				frappe.throw("Phần trăm giảm của combo phải trong khoảng 0 đến 100.")
			self.tiet_kiem = tong * flt(self.gia_tri) / 100.0
			self.gia_combo = tong - self.tiet_kiem
		else:
			if flt(self.gia_tri) <= 0:
				frappe.throw("Combo giảm số tiền thì phải điền số tiền giảm.")
			if flt(self.gia_tri) >= tong:
				frappe.throw("Số tiền giảm đang bằng hoặc lớn hơn tổng giá lẻ của combo.")
			self.tiet_kiem = flt(self.gia_tri)
			self.gia_combo = tong - self.tiet_kiem

		if self.tu_ngay and self.den_ngay and str(self.den_ngay) < str(self.tu_ngay):
			frappe.throw("Ngày kết thúc của combo đang sớm hơn ngày bắt đầu.")
