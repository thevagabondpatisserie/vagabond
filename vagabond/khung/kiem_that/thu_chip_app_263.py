"""Đọc chip từ danh_sach thật sau save/reload, không chỉ kiểm phép thuần."""
from vagabond.khung.kiem_that.nen import ca, la, dung


@ca("#263 chip APP: dem dong cho va da noi tu DB, UNC doi thi doc lai")
def _():
	from vagabond import ho_so_tt as hs
	from vagabond.ho_so_bo_sung import noi_hoa_don
	from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _ho_so_ncc, _unc_gia
	hd = _hoa_don_mua(26300)
	hd2 = _hoa_don_mua(26301, hd.supplier)
	bo_sung = _hoa_don_mua(26302, hd.supplier)
	d = _ho_so_ncc([hd, hd2])
	for r in d.dong:
		r.cho_hoa_don = 1
	d.save(ignore_permissions=True)

	def doc():
		rows = hs.danh_sach(tu_khoa=d.ma, loai="NCC")["rows"]
		la("chi ho so dang kiem", len(rows), 1)
		return rows[0]

	ra = doc()
	la("hai dong cho", ra["so_cho_hoa_don"], 2)
	dung("chip thieu UNC", "thieu_unc" in ra["chip_nghiep_vu"])
	noi_hoa_don(d.name, 1, bo_sung.name)
	ra = doc()
	la("mot dong cho", ra["so_cho_hoa_don"], 1)
	la("mot dong noi", ra["so_da_noi_hoa_don"], 1)
	dung("giu hai nhom", {"cho_hoa_don", "da_noi_hoa_don"}.issubset(ra["chip_nghiep_vu"]))
	_unc_gia(d)
	dung("doc lai bo chip thieu UNC", "thieu_unc" not in doc()["chip_nghiep_vu"])
	# Nối chứng từ không được tự coi là đã trả hoặc làm thay đổi dư nợ.
	hd.reload()
	la("du no giu nguyen", float(hd.outstanding_amount), 26300.0)
	dung("khong bao da chi", "da_chi" not in doc()["chip_nghiep_vu"])
