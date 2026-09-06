from frappe.model.document import Document


class KiemBanhNgay(Document):
	def validate(self):
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
