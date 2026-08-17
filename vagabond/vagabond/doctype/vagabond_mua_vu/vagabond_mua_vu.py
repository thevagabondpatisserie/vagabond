from frappe.model.document import Document


class VagabondMuaVu(Document):
	def validate(self):
		"""Con ban duoc TINH o day, khong tin so tu ngoai gui vao (QT-19).

		Khac han bang kiem banh theo ngay
		---------------------------------
		Ben theo ngay, nguon hang la ton dau cong bep lam trong ngay, va moi
		sang lai dem lai tu dau.

		Ben mua vu, nguon hang la MOT HAN MUC CO DINH cho ca mua: 100 hop
		MOONLAPIS la 100, khong hon. Nha in giao them thi sales sua o "So
		luong san xuat" len; hong mat mot chuc hop thi sua xuong. Nen o do
		la o duy nhat nguoi duoc go, con lai may dem het.

		Vi sao "cho chot" cung tru: y Loan Anh 01/08/2026 ben bang ngay, va
		o mua vu con dung hon - hang gioi han thi mot don giu cho chua chot
		van la mot hop khong con de ban cho nguoi khac. Khach huy thi don
		huy, so tu tra lai.
		"""
		for d in self.dong:
			d.co_the_ban = (
				(d.san_xuat or 0)
				- (d.da_dat or 0)
				- (d.cho_chot or 0)
				- (d.don_khac or 0)
			)
