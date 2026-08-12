"""Combo: phoi may mon thanh mot goi co gia re hon tong le.

Luc tinh tien, cashier bam ma combo thi may RA combo thanh tung mon thanh
phan roi dat mot dong giam gia ben duoi (anh Viet 11/08/2026). Lam vay vi:
- bep va tem dan mon phai thay ten mon that, khong ai lam duoc "combo"
- doanh thu tung mon van dung, bao cao mon ban chay khong bi lech
- kiem banh tru so dung tung ma banh
Bill in ra KHONG in ma combo.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


def sinh_ma_combo():
	chu = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	for _ in range(40):
		ma = "CB" + "".join(chu[int(c, 16) % len(chu)] for c in frappe.generate_hash(length=4))
		if not frappe.db.exists("Vagabond Combo", ma):
			return ma
	frappe.throw("Không sinh được mã combo, thử lại giúp em.")


def gia_ban_mon(item_code):
	"""Gia ban le dang hieu luc cua mot mon."""
	gia = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "selling": 1},
		"price_list_rate",
		order_by="valid_from desc, modified desc",
	)
	return flt(gia)


class VagabondCombo(Document):
	def autoname(self):
		if not self.ma_combo:
			self.ma_combo = sinh_ma_combo()
		self.name = self.ma_combo

	def validate(self):
		if not self.nguoi_tao:
			self.nguoi_tao = frappe.session.user
		if not self.dong:
			frappe.throw("Combo phải có ít nhất một món.")

		for d in self.dong:
			if flt(d.so_luong) <= 0:
				frappe.throw("Số lượng của %s phải lớn hơn 0." % d.item_code)
			if not flt(d.gia_goc):
				d.gia_goc = gia_ban_mon(d.item_code)
			if not flt(d.gia_goc):
				frappe.throw(
					"Món %s chưa có giá bán trong bảng giá. Điền giá gốc vào dòng "
					"đó giúp em, không thì máy không biết combo tiết kiệm bao nhiêu."
					% d.item_code
				)
			d.thanh_tien = flt(d.gia_goc) * flt(d.so_luong)
			d.nhom = (d.nhom or "").strip()

		self._kiem_nhom()
		# Gia goc HIEN THI lay truong hop khach chon toan mon dat nhat; tien
		# tiet kiem lai lay truong hop khach chon toan mon re nhat. Noi thieu
		# con hon noi thua: bang gia dan cho khach ghi "tiet kiem X" thi phai
		# la con so khach LUON duoc, chon kieu gi cung khong tut xuong duoi.
		goc_max = goc_bo(self, dat_nhat=True)
		goc_min = goc_bo(self, dat_nhat=False)
		self.gia_goc = goc_max

		if self.kieu == "Gia tron goi":
			if flt(self.gia_combo) <= 0:
				frappe.throw("Combo giá trọn gói thì phải điền giá bán của combo.")
			if flt(self.gia_combo) > goc_min:
				frappe.throw(
					"Giá combo %s đang CAO HƠN tổng giá lẻ %s của phương án khách "
					"chọn rẻ nhất. Khách mua lẻ còn rẻ hơn."
					% (flt(self.gia_combo), goc_min)
				)
			self.tiet_kiem = goc_min - flt(self.gia_combo)
		elif self.kieu == "Giam phan tram":
			if not 0 < flt(self.gia_tri) <= 100:
				frappe.throw("Phần trăm giảm của combo phải trong khoảng 0 đến 100.")
			self.tiet_kiem = goc_min * flt(self.gia_tri) / 100.0
			self.gia_combo = goc_min - self.tiet_kiem
		else:
			if flt(self.gia_tri) <= 0:
				frappe.throw("Combo giảm số tiền thì phải điền số tiền giảm.")
			if flt(self.gia_tri) >= goc_min:
				frappe.throw(
					"Số tiền giảm đang bằng hoặc lớn hơn tổng giá lẻ %s của phương "
					"án khách chọn rẻ nhất." % goc_min
				)
			self.tiet_kiem = flt(self.gia_tri)
			self.gia_combo = goc_min - self.tiet_kiem

	def _kiem_nhom(self):
		"""Nhom mon cho khach chon: "1 mon nuoc trong 2, 1 banh trong 4".

		Cai nay hoc theo man set combo cua Fabi (De feedback 12/08/2026).
		Dong khong ghi nhom la mon BAT BUOC, luon vao bill - giu nguyen cach
		combo cu chay, nen combo da khai truoc day khong doi hanh vi.
		"""
		nhom = {}
		for d in self.dong:
			if not d.nhom:
				d.chon_trong_nhom = 0
				continue
			nhom.setdefault(d.nhom, []).append(d)
		for ten, ds in nhom.items():
			# So mon duoc chon ghi tren tung dong cho de sua tren app; o day
			# quy ve mot con so cho ca nhom, khong thi hai dong noi hai kieu.
			so = max(cint(d.chon_trong_nhom) for d in ds)
			if so <= 0:
				so = 1
			if so >= len(ds):
				frappe.throw(
					"Nhóm \"%s\" có %d món mà cho chọn %d món thì khách không "
					"còn gì để chọn. Thêm món vào nhóm, hoặc bỏ tên nhóm đi để "
					"mấy món đó thành món bắt buộc." % (ten, len(ds), so)
				)
			for d in ds:
				d.chon_trong_nhom = so

		if self.tu_ngay and self.den_ngay and str(self.den_ngay) < str(self.tu_ngay):
			frappe.throw("Ngày kết thúc của combo đang sớm hơn ngày bắt đầu.")


def nhom_cua(cb):
	"""Bang nhom -> (so mon duoc chon, cac dong trong nhom)."""
	ra = {}
	for d in (cb.dong if hasattr(cb, "dong") else cb["dong"]) or []:
		ten = (d.get("nhom") if isinstance(d, dict) else (d.nhom or "")) or ""
		ten = str(ten).strip()
		if not ten:
			continue
		so = cint(d.get("chon_trong_nhom") if isinstance(d, dict) else d.chon_trong_nhom) or 1
		cu = ra.setdefault(ten, [so, []])
		cu[0] = max(cu[0], so)
		cu[1].append(d)
	return ra


def _tien_dong(d):
	if isinstance(d, dict):
		return flt(d.get("thanh_tien")) or flt(d.get("gia_goc")) * flt(d.get("so_luong"))
	return flt(d.thanh_tien) or flt(d.gia_goc) * flt(d.so_luong)


def goc_bo(cb, dat_nhat=True):
	"""Tong gia le cua MOT bo combo.

	dat_nhat=True lay phuong an khach chon toan mon dat nhat trong moi nhom,
	False lay phuong an re nhat. Combo khong co nhom nao thi hai so bang
	nhau va bang tong ca dong - dung y het cach tinh cu.
	"""
	dong = (cb.dong if hasattr(cb, "dong") else cb["dong"]) or []
	tong = 0.0
	for d in dong:
		ten = (d.get("nhom") if isinstance(d, dict) else (d.nhom or "")) or ""
		if not str(ten).strip():
			tong += _tien_dong(d)
	for _ten, (so, ds) in nhom_cua(cb).items():
		gia = sorted((_tien_dong(d) for d in ds), reverse=bool(dat_nhat))
		tong += sum(gia[:so])
	return tong
