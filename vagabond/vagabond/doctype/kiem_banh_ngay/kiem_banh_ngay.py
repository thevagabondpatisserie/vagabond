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
				# "Huỷ trong ngày" (06/09/2026, anh Việt chốt hướng A của
				# issue #216): bánh hỏng, hết hạn, rơi vỡ, nếm thử. Cửa hàng
				# gõ tay ngay trên bảng này. Bánh đã huỷ thì KHÔNG bán được
				# nữa nên phải trừ, và lúc chốt ngày nó cũng ăn vào lô hàng
				# giống như bánh bán ra - xem kiem_banh.so_roi_tu.
				#
				# Vỏ BTP thì KHÔNG trừ theo huỷ: quy tắc đó chưa ai duyệt sửa,
				# xem chú thích trong kiem_banh.chot_ngay.
				#
				# Vì sao không đi qua phiếu xuất huỷ kho: tồn ERPNext của Kho
				# D1 không được nạp hàng ngày, 218 mã bánh chỉ 30 mã có tồn,
				# nên màn xuất huỷ không liệt kê được món nào để huỷ. Lý do
				# đầy đủ nằm trong vagabond/nhan_banh.py.
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
		"""Số huỷ phải là số nguyên KHÔNG ÂM. Kiểm TRƯỚC khi ép kiểu.

		Codex bắt hai vòng liền trên PR #218.

		Vòng một: `kiem_banh.luu_o` có kẹp `max(0, ...)`, nhưng đó chỉ là MỘT
		đường vào. Doctype này mở quyền write cho Sales User và Stock User,
		nên lưu thẳng từ Desk hoặc từ API `frappe.client.set_value` không đi
		qua `luu_o` một tí nào. Số huỷ âm thì `co_the_ban` TĂNG lên - quầy
		được mời bán số bánh không tồn tại.

		Vòng hai: bản vá đầu viết `int(d.huy or 0)` rồi mới xét `n < 0`, tức
		là CẮT SỐ TRƯỚC KHI KIỂM. Đo trên chính lớp này: `huy = -0.5` được
		nhận và lưu thành 0, `huy = 1.9` được nhận và lưu thành 1. Giá trị
		không hợp lệ bị biến thành một con số khác mà không ai báo, đúng kiểu
		hỏng âm thầm mà cột này sinh ra để tránh. Nên nay kiểm giá trị trước,
		ép kiểu sau.

		Chính sách nhận, viết ra để khỏi đoán:

		  - Rỗng (None, "") coi là 0. Ô chưa điền là chưa huỷ gì.
		  - Số nguyên: nhận nếu không âm.
		  - Số thực: chỉ nhận khi hữu hạn VÀ tròn (3.0 được, 1.9 và -0.5 bị
		    chặn). Nửa cái bánh huỷ không phải là một con số đếm được.
		  - Chuỗi: chỉ nhận khi là số nguyên viết thẳng ("3", " 3 "). Chuỗi
		    "3.5" và "ba" bị chặn.
		  - Còn lại bị chặn.

		Chặn ở đây chứ không chỉ đặt `min="0"` cho ô nhập: ô nhập là gợi ý cho
		người gõ, không phải hàng rào cho máy.

		LƯU Ý về `luu_o`: cửa đó vẫn KẸP số âm về 0 theo hành vi cũ, không ném
		lỗi. Nên câu đúng là "lớp doctype từ chối số huỷ không hợp lệ", KHÔNG
		phải "mọi cửa vào đều từ chối số âm".

		KHÔNG kẹp `co_the_ban` về 0. Số âm ở cột đó là số có thật và phải hiện
		đỏ để người đối chiếu, khác hẳn số huỷ âm vốn là số vô nghĩa.
		"""
		for d in self.dong:
			d.huy = self._doc_so_huy(d.huy, d.ma_hang)

	@staticmethod
	def _doc_so_huy(gia_tri, ma_hang=None):
		"""Đọc một ô huỷ. Trả về số nguyên không âm, hoặc ném lỗi có dấu."""
		import math

		def _chan():
			frappe.throw(
				"Số huỷ của mã %s đang là %s. Số huỷ phải là số nguyên không "
				"âm - sửa về 0 hoặc số dương rồi lưu lại."
				% (ma_hang or "(chưa có mã)", gia_tri)
			)

		v = gia_tri
		if v is None:
			return 0
		if isinstance(v, str):
			v = v.strip()
			if not v:
				return 0
			try:
				v = int(v)
			except ValueError:
				_chan()
		elif isinstance(v, float):
			if not math.isfinite(v) or v != int(v):
				_chan()
			v = int(v)
		elif not isinstance(v, int):
			_chan()
		if v < 0:
			_chan()
		return int(v)
