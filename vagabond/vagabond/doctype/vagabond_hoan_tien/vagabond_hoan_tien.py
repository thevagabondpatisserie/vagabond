"""Yeu cau hoan tien cho khach. Mot don tra hang = mot ban ghi o day."""

import frappe
from frappe.model.document import Document


class VagabondHoanTien(Document):
	def validate(self):
		# Chặn trước khi gửi yêu cầu/chuyển tiền, không tự làm tròn sau khi tiền đã ra.
		if self.get('hoa_don') and frappe.db.exists('Sales Invoice Item',
			{'parent':self.hoa_don,'vgb_combo_luong':['>',0]}):
			from decimal import Decimal
			tien = Decimal(str(self.get('so_tien') or 0))
			if not tien.is_finite() or tien <= 0 or tien != tien.to_integral_value():
				frappe.throw('Hoàn bill combo cần số nguyên đồng lớn hơn0. Nhập lại số tiền trước khi gửi kế toán.')
		if (self.ly_do or "") == "Khac" and not (self.dien_giai or "").strip():
			frappe.throw(
				'Lý do "Khác" thì phải ghi rõ vì sao hoàn, để sau này còn thống kê được. Vui lòng gõ vào ô Diễn giải thêm.'
			)
