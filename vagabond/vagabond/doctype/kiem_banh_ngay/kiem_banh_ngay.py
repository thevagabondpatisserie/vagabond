import frappe
from frappe.model.document import Document


class KiemBanhNgay(Document):
	def validate(self):
		self._chan_huy_am()
		# "Co the ban" TINH o day, khong tin so tu ngoai gui vao.
		# Ton dau mang dau CONG (chot voi anh Viet 01/08): banh hom qua van
		# ban duoc, theo doi NSX de uu tien day hang cu di truoc.
		# "Cho chot" la don trang thai Moi - giu cho mem, TRU AO luon vao
		# co the ban (y Loan Anh 01/08): khach nhan tin hoi la sales tao don
		# Moi ngay, so tu giu; khach khong lay thi huy don, so tu tra lai.
		# "Kenh khac" (08/08/2026) la banh ban qua Grab, Shopee, khach si,
		# quay - nhung don khong di qua Pancake nen may khong dem duoc tu
		# don Pancake. Truoc day Loan Anh phai tao mot don Pancake gia de
		# tru so, thanh ra mot khach hai bill. Nay dem thang tu hoa don ban
		# ra co nguon khac Pancake trong ngay.
		# "Giu cho" (05/09/2026): phieu dat banh o tai cua hang, tinh theo
		# ngay khach ra nhan. Xem vagabond/dat_banh.py.
		for d in self.dong:
			d.co_the_ban = (
				(d.ton_cu or 0)
				+ (d.ton_d2 or 0)
				+ (d.ton_d1 or 0)
				+ (d.sx or 0)
				# "Huy trong ngay" (06/09/2026, anh Viet chot huong A cua
				# issue #216): banh hong, het han, roi vo, nem thu. Cua hang
				# go tay ngay tren bang nay. Banh da huy thi KHONG ban duoc
				# nua nen phai tru, va luc chot ngay no cung an vao lo hang
				# giong nhu banh ban ra - xem kiem_banh.so_da_tieu.
				#
				# Vi sao khong di qua phieu xuat huy kho: ton ERPNext cua Kho
				# D1 khong duoc nap hang ngay, 218 ma banh chi 30 ma co ton,
				# nen man xuat huy khong liet ke duoc mon nao de huy. Ly do
				# day du nam trong vagabond/nhan_banh.py.
				- (d.huy or 0)
				- (d.da_dat or 0)
				- (d.phat_sinh or 0)
				- (d.cho_chot or 0)
				- (d.don_khac or 0)
				# "Giu cho" (05/09/2026) la banh khach da dat tai cua hang va
				# TRA TRUOC TOAN BO, nhung chua toi ngay ra lay. Tru vao ngay
				# NHAN chu khong phai ngay dat: hang phai co mat dung hom
				# khach toi. Phan da giao roi thi roi khoi cot nay va di vao
				# cot Kenh khac cua chinh ngay giao, nen tong luon can.
				- (d.giu_cho or 0)
			)


	def _chan_huy_am(self):
		"""Số huỷ phải là số nguyên KHÔNG ÂM. Chặn ngay ở lớp doctype.

		Codex bắt trên PR #218 ngày 06/09/2026. `kiem_banh.luu_o` có kẹp
		`max(0, ...)`, nhưng đó chỉ là MỘT đường vào. Doctype này mở quyền
		write cho Sales User và Stock User, nên lưu thẳng từ Desk hoặc từ API
		`frappe.client.set_value` không đi qua `luu_o` một tí nào.

		Số huỷ âm thì `co_the_ban` TĂNG lên - quầy được mời bán số bánh không
		tồn tại. Mà lúc chốt ngày `so_roi_tu` lại kẹp về 0, nên hai đường cho
		ra hai ý nghĩa khác nhau trên cùng một con số. Tái hiện được trước khi
		sửa: một dòng tồn 10 huỷ -3 cho ra `co_the_ban` = 13.

		Chặn ở đây chứ không chỉ đặt `min="0"` cho ô nhập: ô nhập là gợi ý cho
		người gõ, không phải hàng rào cho máy.

		KHÔNG kẹp `co_the_ban` về 0. Số âm ở cột đó là số có thật và phải hiện
		đỏ để người đối chiếu, khác hẳn số huỷ âm vốn là số vô nghĩa.
		"""
		for d in self.dong:
			try:
				n = int(d.huy or 0)
			except (TypeError, ValueError):
				n = None
			if n is None or n < 0:
				frappe.throw(
					"Số huỷ của mã %s đang là %s. Số huỷ phải là số nguyên không "
					"âm - sửa về 0 hoặc số dương rồi lưu lại."
					% (d.ma_hang or "(chưa có mã)", d.huy)
				)
			d.huy = n
