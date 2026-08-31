# -*- coding: utf-8 -*-
"""Ca kiểm cho hàng rào đơn vị của đơn mua hàng và phiếu nhập kho.

Số liệu lấy nguyên từ 5 đơn mua đang mở ngày 27/08/2026, tìm ra khi rà
43 mẩu lệnh chỉ sống trên Desk.
"""

from vagabond import gac_don_vi as G
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("gac don vi: don vi kho thi luon hop le, khong doi khai gi")
def _dvt_kho():
	la("dung don vi kho", G.soi_dong("Gram", 1, "Gram", None), G.DVT_OK)
	la("viet hoa viet thuong van la mot", G.soi_dong("gram", 1, "Gram", None), G.DVT_OK)


@ca("gac don vi: mon chua khai don vi do thi CHAN")
def _chua_khai():
	# DMH-2026-00127 that: 1 "Box" he so 1, mon NVLT00324 chi khai Gram/Kg/Lon.
	la("Box chua khai", G.soi_dong("Box", 1, "Gram", None), G.DVT_CHUA_KHAI)
	# DMH-2026-00126 that: 2 "Kg" he so 1000, mon NVLT00377 CHI khai Gram.
	la("Kg chua khai du he so dung", G.soi_dong("Kg", 1000, "Gram", None), G.DVT_CHUA_KHAI)


@ca("gac don vi: he so tren dong khac he so mon khai thi CHAN")
def _sai_he_so():
	# DMH-2026-00145 that: 18 "Hop" he so 500, mon NVLT00089 khai Hop he so khac.
	la("he so lech", G.soi_dong("Hộp", 500, "Gram", 1000), G.DVT_SAI_HE_SO)
	la("he so trung thi qua", G.soi_dong("Hộp", 1000, "Gram", 1000), G.DVT_OK)


@ca("gac don vi: chua khai KHAC voi khai he so 0")
def _khong_gop_none_voi_khong():
	# Gop hai ca nay lam mot la mat thong tin: mot ben la "mon chua khai",
	# ben kia la "mon khai sai thanh 0". Cau bao loi phai khac nhau.
	la("None la chua khai", G.soi_dong("Kg", 1000, "Gram", None), G.DVT_CHUA_KHAI)
	la("0 la khai sai", G.soi_dong("Kg", 1000, "Gram", 0), G.DVT_SAI_HE_SO)


@ca("gac don vi: cau bao loi noi ro phai lam gi")
def _cau_bao_loi():
	c = G.loi_chua_khai(1, "NVLT00324", "Bột ca cao", "Box", "Gram", ["Gram", "Kg", "Lon"])
	dung("noi ten mon", "NVLT00324" in c)
	dung("noi don vi thieu", '"Box"' in c)
	dung("liet ke don vi dang co", "Gram, Kg, Lon" in c)
	dung("bao dung sua tay so luong", "Đừng sửa tay số lượng" in c)
	# Nguoi doc cau nay la Uyen chu khong phai lap trinh vien.
	for cam in ("uom", "conversion_factor", "UOM Conversion Detail", "throw"):
		dung("khong lo tu ky thuat %s" % cam, cam not in c)

	c2 = G.loi_sai_he_so(3, "NVLT00089", "Sữa đặc", "Hộp", 500, 1000, "Gram")
	dung("noi ca hai con so", "500" in c2 and "1000" in c2)
	dung("noi dong so may", "Dòng 3" in c2)


@ca("gac don vi: gom het loi bao mot lan chu khong bao tung dong")
def _gom_loi():
	import inspect

	ma = inspect.getsource(G.chan_don_vi_la)
	dung("gom vao mot danh sach", "loi = []" in ma)
	dung("chi throw mot lan o cuoi", ma.count("frappe.throw") == 1)
	dung("noi cac loi lai voi nhau", '"<br><br>".join(loi)' in ma)
	# Bo qua dong khong co ma hang: dong dich vu khong co don vi kho.
	dung("bo qua dong khong ma hang", "if not ma:" in ma)


@ca("gac don vi: da gan vao ca don mua lan phieu nhap")
def _da_gan_hook():
	import inspect

	from vagabond import hooks

	# CAT TU doc_events TRO XUONG chu khong cat o lan gap dau tien trong ca
	# tep. Ban v362 them "Purchase Receipt" vao doctype_js - nam PHIA TREN
	# doc_events - nen phep cat cu roi trung khoi khai tep JS va bao hong
	# trong khi hang rao van con nguyen.
	ma = inspect.getsource(hooks).split("doc_events", 1)[1]
	doan_dm = ma.split('"Purchase Order"', 1)[1][:900]
	dung("don mua co hang rao", "gac_don_vi.chan_don_vi_la" in doan_dm)
	doan_pn = ma.split('"Purchase Receipt"', 1)[1][:900]
	dung("phieu nhap co hang rao", "gac_don_vi.chan_don_vi_la" in doan_pn)


@ca("gac don vi: phan thuan khong cham Frappe")
def _thuan_that():
	import inspect

	for f in (G.soi_dong, G.loi_chua_khai, G.loi_sai_he_so):
		ma = inspect.getsource(f)
		dung("%s khong goi frappe" % f.__name__, "frappe." not in ma)
