"""Phieu doi cong no: gom nhieu hoa don chua tra cua MOT khach thanh mot
phieu, sinh mot ma QR MB Bank duy nhat de khach chuyen mot lan.

Vi sao khong dung Payment Request co san cua ERPNext: minh can ma QR song
dung 7 ngay, noi dung chuyen khoan mang ma rieng de SePay tu khop, va mot
so trang thai rieng cho viec di doi (anh Viet chot 11/08/2026).
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class VagabondCongNo(Document):
	def validate(self):
		self.tong_tien = sum(flt(d.so_tien) for d in (self.dong or []))
		if not self.dong:
			frappe.throw("Phiếu công nợ phải có ít nhất một hoá đơn.")
		# Mot hoa don khong duoc nam trong hai phieu cong no con hieu luc -
		# neu khong ke toan se di doi hai lan cung mot so tien.
		for d in self.dong:
			trung = frappe.get_all(
				"Vagabond Cong No Dong",
				filters={"hoa_don": d.hoa_don, "parent": ["!=", self.name or ""]},
				fields=["parent"],
				limit_page_length=0,
			)
			for t in trung:
				tt = frappe.db.get_value("Vagabond Cong No", t.parent, "trang_thai")
				if tt in ("Cho thu", "Thu thieu"):
					frappe.throw(
						"Hoá đơn %s đã nằm trong phiếu công nợ %s đang chờ thu."
						% (d.hoa_don, t.parent)
					)
