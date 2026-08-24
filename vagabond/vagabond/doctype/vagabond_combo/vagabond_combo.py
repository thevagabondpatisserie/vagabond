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
	frappe.throw("Không sinh được mã combo, vui lòng thử lại.")


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
					"Món %s chưa có giá bán trong bảng giá. Vui lòng điền giá gốc vào dòng đó, không thì máy không biết combo tiết kiệm bao nhiêu."
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

		Hoc theo man set combo cua Fabi (anh Viet gui anh 12/08/2026). Moi
		nhom la MOT dong rieng trong bang nhom, co ten, chon toi thieu va
		toi da - chu khong con go lai ten nhom tren tung dong mon.

		Dong mon khong ghi ten nhom la mon BAT BUOC, luon vao bill. Combo
		cu khong khai nhom nao thi chay y nhu truoc.
		"""
		theo_ten = {}
		for d in self.dong:
			d.nhom = (d.nhom or "").strip()
			if d.nhom:
				theo_ten.setdefault(d.nhom, []).append(d)

		ten_nhom = {}
		for g in self.nhom or []:
			g.ten = (g.ten or "").strip()
			if not g.ten:
				frappe.throw("Có nhóm món chưa đặt tên.")
			if g.ten in ten_nhom:
				frappe.throw("Nhóm \"%s\" bị khai hai lần." % g.ten)
			ten_nhom[g.ten] = g

			ds = theo_ten.get(g.ten) or []
			if not ds:
				frappe.throw(
					"Nhóm \"%s\" chưa có món nào. Thêm món vào nhóm, hoặc bỏ "
					"nhóm đó đi." % g.ten
				)
			toi_da = cint(g.chon_toi_da)
			if toi_da <= 0:
				toi_da = 1
			toi_thieu = cint(g.chon_toi_thieu)
			if toi_thieu < 0:
				toi_thieu = 0
			if toi_thieu > toi_da:
				frappe.throw(
					'Nhóm "%s" đang bắt chọn tối thiểu %d món mà tối đa chỉ %d. Vui lòng sửa lại.' % (g.ten, toi_thieu, toi_da)
				)
			if toi_da > len(ds):
				frappe.throw(
					"Nhóm \"%s\" cho chọn tối đa %d món mà trong nhóm mới có %d "
					"món. Thêm món, hoặc hạ số tối đa xuống." % (g.ten, toi_da, len(ds))
				)
			if toi_thieu == toi_da == len(ds):
				frappe.throw(
					"Nhóm \"%s\" bắt khách lấy hết cả %d món thì không còn gì "
					"để chọn. Bỏ tên nhóm khỏi mấy dòng đó là chúng thành món "
					"bắt buộc, gọn hơn." % (g.ten, len(ds))
				)
			g.chon_toi_da = toi_da
			g.chon_toi_thieu = toi_thieu
			# Truong cu tren tung dong mon van giu dong bo, de ban cai dat cu
			# va bao cao doc ra khong lech.
			for d in ds:
				d.chon_trong_nhom = toi_da

		# Dong mon tro toi mot nhom khong co trong bang nhom la mo coi: no
		# se khong bao gio duoc chon, ma man cai dat khong noi cho ai biet.
		for ten in theo_ten:
			if ten not in ten_nhom:
				frappe.throw(
					"Mấy món đang ghi nhóm \"%s\" mà chưa có nhóm nào tên đó. "
					"Bấm Tạo nhóm món để khai, hoặc xoá tên nhóm khỏi mấy dòng "
					"đó." % ten
				)
		for d in self.dong:
			if not d.nhom:
				d.chon_trong_nhom = 0

		if self.tu_ngay and self.den_ngay and str(self.den_ngay) < str(self.tu_ngay):
			frappe.throw("Ngày kết thúc của combo đang sớm hơn ngày bắt đầu.")


def _lay(d, khoa, mac_dinh=None):
	if isinstance(d, dict):
		return d.get(khoa, mac_dinh)
	return getattr(d, khoa, mac_dinh)


def nhom_cua(cb):
	"""Bang ten nhom -> {toi_thieu, toi_da, mo_ta, dong}.

	Doc tu bang NHOM cua combo. Combo khai truoc ngay 12/08/2026 chua co
	bang nhom nhung dong mon da mang ten nhom va so mon duoc chon, nen van
	suy nguoc ra duoc - khong de combo cu bong dung mat nhom.
	"""
	dong = (cb.dong if hasattr(cb, "dong") else cb["dong"]) or []
	theo_ten = {}
	for d in dong:
		ten = str(_lay(d, "nhom", "") or "").strip()
		if ten:
			theo_ten.setdefault(ten, []).append(d)

	ra = {}
	bang = (cb.nhom if hasattr(cb, "nhom") else cb.get("nhom")) or []
	for g in bang:
		ten = str(_lay(g, "ten", "") or "").strip()
		if not ten or ten not in theo_ten:
			continue
		ds = theo_ten[ten]
		toi_da = cint(_lay(g, "chon_toi_da", 0)) or 1
		toi_thieu = cint(_lay(g, "chon_toi_thieu", 0))
		ra[ten] = {
			"toi_thieu": max(0, min(toi_thieu, toi_da)),
			"toi_da": min(toi_da, len(ds)),
			"mo_ta": str(_lay(g, "mo_ta", "") or "").strip(),
			"dong": ds,
		}
	for ten, ds in theo_ten.items():
		if ten in ra:
			continue
		so = max([cint(_lay(d, "chon_trong_nhom", 0)) for d in ds] or [0]) or 1
		so = min(so, len(ds))
		ra[ten] = {"toi_thieu": so, "toi_da": so, "mo_ta": "", "dong": ds}
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
	for _ten, g in nhom_cua(cb).items():
		gia = sorted((_tien_dong(d) for d in g["dong"]), reverse=bool(dat_nhat))
		# Dat nhat la khach lay het suat toi da va toan mon dat; re nhat la
		# khach chi lay dung so toi thieu va toan mon re.
		so = g["toi_da"] if dat_nhat else g["toi_thieu"]
		tong += sum(gia[:so])
	return tong
