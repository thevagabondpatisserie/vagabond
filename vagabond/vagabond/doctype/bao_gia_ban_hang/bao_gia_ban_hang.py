"""Bao gia ban hang gui khach doanh nghiep.

So bao gia sinh theo thang: BG-26-08-00001. Cung cach danh so voi phieu de
nghi thanh toan DNTT-26-08-00001 de ai nhin cung doan duoc thang nao.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BaoGiaBanHang(Document):
	def validate(self):
		if self.ten:
			self.ten = self.ten.strip()
		if self.khach_hang and not self.ten_khach:
			self.ten_khach = (
				frappe.db.get_value("Customer", self.khach_hang, "customer_name")
				or self.khach_hang
			)
		if self.hieu_luc_den and self.ngay_bao_gia:
			if frappe.utils.getdate(self.hieu_luc_den) < frappe.utils.getdate(
				self.ngay_bao_gia
			):
				frappe.throw("Ngày hết hiệu lực không được trước ngày báo giá.")
		for d in self.dong:
			if flt(d.so_luong) <= 0:
				frappe.throw(
					"Dòng %s: số lượng phải lớn hơn 0." % (d.ten_mon or d.idx)
				)
			if flt(d.chiet_khau) < 0 or flt(d.chiet_khau) > 100:
				frappe.throw(
					"Dòng %s: chiết khấu phải trong khoảng 0 đến 100%%."
					% (d.ten_mon or d.idx)
				)
