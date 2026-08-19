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
		# Phien ban thuong luong khong an mot so moi: no la HAU TO dan vao ten
		# to goc, vd VGB-PQ-2026-0007-v2. Khach nhin ma la biet ngay day van
		# la to cu, chi khac vong. Nhanh nay phai dat TRUOC nhanh dem so.
		if self.get("goc") and int(self.get("phien_ban") or 1) > 1:
			self.name = "%s-v%d" % (self.goc, int(self.phien_ban))
			return

		# Mau bao gia dem rieng: mau khong phai to gui khach, khong duoc an
		# mat mot so trong day VGB-PQ (luu mot mau xong to that ke tiep se
		# nhay so, Loan Anh nhin vao tuong mat to).
		if self.get("la_mau"):
			tien_to = "MAU-BG-"
		else:
			nam = getdate(self.ngay_bao_gia or nowdate()).year
			tien_to = "VGB-PQ-%d-" % nam
		# Phai loai cac to "-vN" ra khoi cau dem, neu khong bo dem chet.
		# VGB-PQ-2026-0011-v2 dai hon va lon hon VGB-PQ-2026-0011 khi so
		# chuoi, nen no se duoc chon lam moc; rsplit("-", 1)[1] ra "v2",
		# int() nem loi, khoi except keo so ve 1 va to moi lay ten
		# VGB-PQ-2026-0001 - trung ten mot to da co. Loi nay chi no khi
		# vong thuong luong roi dung vao to co so lon nhat, tuc no im lang
		# ca thang roi mot ngay dep troi lam sales khong luu duoc to nao.
		cuoi = frappe.db.sql(
			"""select name from `tabBao Gia Ban Hang`
			where name like %(t)s and name not like %(v)s
			order by length(name) desc, name desc limit 1""",
			{"t": tien_to + "%", "v": tien_to + "%-v%"},
		)
		so = 1
		if cuoi:
			try:
				so = int(str(cuoi[0][0]).rsplit("-", 1)[1]) + 1
			except Exception:
				so = 1
		self.name = "%s%04d" % (tien_to, so)

	def validate(self):
		# Khoa cung ban da bi thay the. Dat o day chu khong chi o ham luu()
		# vi day la cho DUY NHAT moi duong ghi deu phai di qua: app, man
		# Desk, script cua nguoi khac. Duong ghi hop le duy nhat len mot ban
		# dong bang la frappe.db.set_value, va no co y khong chay validate.
		if self.get("thay_the_boi") and not self.is_new():
			frappe.throw(
				"Báo giá %s là bản lịch sử, đã được thay bằng %s nên không "
				"sửa được nữa. Mở %s để sửa, bản này giữ nguyên làm bằng "
				"chứng về những gì đã gửi khách."
				% (self.name, self.thay_the_boi, self.thay_the_boi)
			)
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
			# Tran 100 chi dung cho chiet khau tinh theo PHAN TRAM. Tu dot
			# v228 mot dong con chiet khau duoc theo SO TIEN, va mot dong
			# giam 500.000 d se vap ngay cai chan nay neu khong tach ra.
			if flt(d.chiet_khau) < 0:
				frappe.throw("Dòng %s: chiết khấu không được âm." % (d.ten_mon or d.idx))
			if (d.get("kieu_ck") or "") != "So tien" and flt(d.chiet_khau) > 100:
				frappe.throw(
					"Dòng %s: chiết khấu theo phần trăm phải trong khoảng 0 đến 100%%. "
					"Muốn giảm một số tiền cụ thể thì bấm chip \"Giảm giá theo số tiền\" "
					"của dòng đó." % (d.ten_mon or d.idx)
				)
