from frappe.model.document import Document
from frappe.utils import cint


class VagabondMuaVu(Document):
	def validate(self):
		"""Con ban duoc TINH o day, khong tin so tu ngoai gui vao (QT-19).

		Phep tinh KHONG nam trong tep nay
		---------------------------------
		Ba phep duoi day goi thang sang vagabond/mua_vu.py, noi chung la ham
		THUAN va bo kiem thu chay duoc khong can site.

		Co y de vay: neu viet phep o day thi bo kiem thu buoc phai co mot ban
		sao rieng, va hai ban se lech nhau vao mot ngay khong ai doan truoc -
		dung cai bay da lam hong ba viec trong ngay 16/08/2026 (hai cho dinh
		tuyen, hai duong doi soat, regex chep hai ban). Mot cho tinh, mot cho
		kiem.

		Khac han bang kiem banh theo ngay
		---------------------------------
		Ben theo ngay, nguon hang la ton dau cong bep lam trong ngay, moi sang
		dem lai tu dau. Ben mua vu, nguon hang la mot HAN MUC cho ca mua: 100
		hop MOONLAPIS la 100, khong hon.

		"Cho chot" cung tru (y Loan Anh 01/08/2026, o mua vu con dung hon):
		hang gioi han thi mot don giu cho chua chot van la mot hop khong con
		de ban cho nguoi khac. Khach huy thi don huy, so tu tra lai.
		"""
		from vagabond.mua_vu import (
			banh_le_trong_hop,
			con_ban_duoc,
			con_hop_thuc_te,
			ghep_duoc_tu_ruot,
			han_muc_tu_dot,
			ma_co_nguon_cung,
			ma_la_hop,
			nguon_cung,
			nhan_tu_ten,
			san_luong_theo_ma,
		)

		han = han_muc_tu_dot([d.as_dict() for d in self.get("dot") or []])
		bep = san_luong_theo_ma([d.as_dict() for d in self.get("san_luong") or []])
		la_hop = ma_la_hop([m.as_dict() for m in self.get("dinh_muc") or []])
		ban_hop = {
			d.ma_hang: (d.da_dat or 0) + (d.cho_chot or 0) + (d.don_khac or 0)
			for d in self.dong
		}
		trong_hop = banh_le_trong_hop(
			[m.as_dict() for m in self.get("dinh_muc") or []], ban_hop
		)
		# Nhan ngan cho o lich thang. Nguoi go de trong thi may tu dat, va
		# nhan da co thi giu nguyen - doi nhan cua mot dong dang dung se lam
		# sales doc nham o lich.
		da_dung = {
			str(d.nhan_ngan).strip() for d in self.dong if str(d.nhan_ngan or "").strip()
		}
		for d in self.dong:
			if not str(d.nhan_ngan or "").strip():
				d.nhan_ngan = nhan_tu_ten(d.ten_banh or d.ma_hang, da_dung)
				da_dung.add(d.nhan_ngan)
			# HAI NGUON CUNG, KHONG TRUNG NHAU (anh Viet chot 21/08/2026)
			#
			#   o "Tong nha in giao"  <- tong cac dot DA VE cua nha in
			#   o "San xuat"          <- tong san luong bep nhap theo ngay
			#
			# Ma nao chua khai dot thi o nha in go tay giu nguyen hieu luc, ma
			# nao chua ai nhap san luong ngay nao thi o san xuat go tay giu
			# nguyen hieu luc. Cung mot luat cho ca hai o.
			#
			# Truoc ban nay chi co mot o San xuat gom ca hai thu, nen nhin vao
			# khong biet hop thieu vi nha in giao thieu hay vi bep chua lam kip.
			if d.ma_hang in han:
				d.nha_in_giao = han[d.ma_hang]
			# O "San xuat" CONG hai phan, khong bao gio thay the (anh Viet
			# 22/08/2026: "tab San luong nhap so vao he thong nuot luon").
			#
			# Ban truoc viet `d.san_xuat = bep[d.ma_hang]`, tuc bep nhap 120
			# cai cua mot ngay la con so ca mua go tay 1700 bien mat khong
			# mot loi bao. Nguoi go mat viec cua minh, va con so con lai
			# khong sai kieu de nhin ra, no chi be di.
			#
			# Nay tach lam hai o ro rang:
			#   sx_dau_mua - so bep da lam TRUOC khi mo so ngay, nguoi go tay
			#   san_luong  - cac dong bep nhap theo tung ngay
			# va o "San xuat" la tong hai thu, chi doc, khong ai go thang.
			d.san_xuat = cint(d.sx_dau_mua) + cint(bep.get(d.ma_hang, 0))
			d.trong_hop = trong_hop.get(d.ma_hang, 0)
			d.co_the_ban = con_ban_duoc(
				nguon_cung(d.san_xuat, d.nha_in_giao),
				d.da_dat,
				d.cho_chot,
				d.don_khac,
				d.trong_hop,
			)

		# GHEP NGUOC: ruot con lai ghep duoc bao nhieu hop nua.
		#
		# Phai chay SAU vong lap tren, vi no can co_the_ban cua tung banh le da
		# tinh xong. Chay hai vong la co y, khong phai thua.
		#
		# Luu y ve chan ban lo: rang buoc ruot da duoc con_sau_khi_them chan san
		# tu truoc, vi ban mot hop lam banh le trong hop tang len va dong banh le
		# do se am. Hai cot moi o day la de NHIN THAY va de trang web quyet dinh
		# hien nut Het hang, chu khong phai them mot lop chan thu hai.
		con_banh = {d.ma_hang: cint(d.co_the_ban) for d in self.dong}
		khong_tran = {d.ma_hang for d in self.dong if cint(d.khong_tran)}
		# Ruot DA khai nguon cung thi van chan duoc so hop, du no mang co
		# khong_tran (anh Viet 24/08/2026). Chi ruot CHUA khai gi ca moi bi bo
		# qua, vi luc do la khong biet chu khong phai bang 0. Xem
		# ghep_duoc_tu_ruot de biet vi sao gop hai chuyen do lam mot la sai.
		co_nguon = ma_co_nguon_cung([d.as_dict() for d in self.dong])
		ghep = ghep_duoc_tu_ruot(
			[m.as_dict() for m in self.get("dinh_muc") or []],
			con_banh,
			khong_tran,
			co_nguon,
		)
		for d in self.dong:
			if d.ma_hang in la_hop:
				g = ghep.get(d.ma_hang)
				d.ghep_duoc = cint(g) if g is not None else 0
				d.con_thuc_te = con_hop_thuc_te(d.co_the_ban, g)
				# Hop ma khong ruot nao co han muc rieng: chi vo hop chan duoc.
				# Im lang o day la ban lo ma khong ai biet, nen bat co de man
				# hinh hien chip canh bao.
				d.ruot_khong_rang_buoc = 1 if g is None else 0
			else:
				d.ghep_duoc = 0
				d.con_thuc_te = cint(d.co_the_ban)
				d.ruot_khong_rang_buoc = 0
