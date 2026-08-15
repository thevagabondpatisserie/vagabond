"""Bao gia ban hang gui khach doanh nghiep, song ngu Viet - Anh.

Danh so VGB-PQ-YYYY-NNNN cho khop dung ma Loan Anh dang gui khach tren file
Word (vd VGB-PQ-2026-0011), dem lai tu 1 moi nam.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class BaoGiaBanHang(Document):
	def autoname(self):
		"""Danh so VGB-PQ-YYYY-NNNN, dem lai tu 1 moi nam.

		Khong dung duoc chuoi "format:VGB-PQ-{YYYY}-{####}" cua Frappe mot
		minh: trong _format_autoname moi cap ngoac duoc doc RIENG mot lan,
		nen o {####} bo dem chay voi tien to rong, tuc dung chung mot bo dem
		toan he - to dau tien tung ra BG-26-08-00668 chu khong phai 00001.
		Frappe goi doc.run_method("autoname") TRUOC khi xet chuoi format nen
		ham nay thang; chuoi format giu lai lam duong lui.
		"""
		# Mau bao gia dem rieng: mau khong phai to gui khach, khong duoc an
		# mat mot so trong day VGB-PQ (luu mot mau xong to that ke tiep se
		# nhay so, Loan Anh nhin vao tuong mat to).
		if self.get("la_mau"):
			tien_to = "MAU-BG-"
		else:
			nam = getdate(self.ngay_bao_gia or nowdate()).year
			tien_to = "VGB-PQ-%d-" % nam
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
		self.name = "%s%04d" % (tien_to, so)

	def validate(self):
		if self.ten:
			self.ten = self.ten.strip()
		if self.khach_hang and not self.ten_khach:
			self.ten_khach = (
				frappe.db.get_value("Customer", self.khach_hang, "customer_name")
				or self.khach_hang
			)
		# Hieu luc: uu tien so ngay cho de sua, tu tinh ra ngay het han.
		if self.hieu_luc_ngay and self.ngay_bao_gia:
			from frappe.utils import add_days

			self.hieu_luc_den = add_days(getdate(self.ngay_bao_gia), int(self.hieu_luc_ngay))
		if self.hieu_luc_den and self.ngay_bao_gia:
			if getdate(self.hieu_luc_den) < getdate(self.ngay_bao_gia):
				frappe.throw("Ngày hết hiệu lực không được trước ngày báo giá.")
		for d in self.dong:
			if flt(d.so_luong) <= 0:
				frappe.throw("Dòng %s: số lượng phải lớn hơn 0." % (d.ten_mon or d.idx))
			if flt(d.chiet_khau) < 0 or flt(d.chiet_khau) > 100:
				frappe.throw(
					"Dòng %s: chiết khấu phải trong khoảng 0 đến 100%%." % (d.ten_mon or d.idx)
				)
