"""Bao gia ban hang gui khach doanh nghiep.

So bao gia sinh theo thang: BG-26-08-00001. Cung cach danh so voi phieu de
nghi thanh toan DNTT-26-08-00001 de ai nhin cung doan duoc thang nao.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class BaoGiaBanHang(Document):
	def autoname(self):
		"""Danh so BG-YY-MM-NNNNN, dem lai tu 1 moi thang.

		Khong dung duoc autoname "format:BG-{YY}-{MM}-{#####}" cua Frappe:
		trong _format_autoname moi cap ngoac duoc doc RIENG mot lan, nen o
		{#####} bo dem chay voi tien to rong - tuc la dung chung mot bo dem
		toan he. To thu dau tien ra thang BG-26-08-00668 chu khong phai
		00001. Nen sinh ma o day, do chinh cac to BG cung thang ma dem len.
		"""
		hn = getdate(self.ngay_bao_gia or nowdate())
		tien_to = "BG-%02d-%02d-" % (hn.year % 100, hn.month)
		cuoi = frappe.db.sql(
			"""select name from `tabBao Gia Ban Hang`
			where name like %s order by name desc limit 1""",
			tien_to + "%",
		)
		so = 1
		if cuoi:
			try:
				so = int(str(cuoi[0][0]).rsplit("-", 1)[1]) + 1
			except Exception:
				so = 1
		self.name = "%s%05d" % (tien_to, so)

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
