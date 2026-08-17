from frappe.model.document import Document


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
			han_muc_tu_dot,
			nhan_tu_ten,
		)

		han = han_muc_tu_dot([d.as_dict() for d in self.get("dot") or []])
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
			# Han muc: uu tien tong cac dot da ve, roi moi den o go tay. Mua
			# chua khai dot nao thi o go tay giu nguyen hieu luc.
			if d.ma_hang in han:
				d.san_xuat = han[d.ma_hang]
			d.trong_hop = trong_hop.get(d.ma_hang, 0)
			d.co_the_ban = con_ban_duoc(
				d.san_xuat, d.da_dat, d.cho_chot, d.don_khac, d.trong_hop
			)
