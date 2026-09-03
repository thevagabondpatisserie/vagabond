# -*- coding: utf-8 -*-
"""Cho xuất lô quá hạn, có ghi vết (v406, 03/09/2026).

Chiều 03/09 bếp Khải không ghi được phiếu làm Mille Crepe Avocado vì mấy
dòng nguyên liệu "hết date". Đo trên site: 171 lô quá hạn, 106 lô còn ghi
số dư, mà máy vừa không nhìn thấy chúng vừa không cho xuất. Các ca dưới đây
canh đúng ba lớp chặn đó, để không phiên nào dựng lại một lớp nào.
"""

import io
import os

from vagabond import lo_het_han as lhh
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


# ------------------------------------------------------- phép so ngày hạn


@ca("v406 lô không ghi hạn thì không bao giờ tính là quá hạn")
def _khong_han():
	la("để trống", lhh.qua_han(None, "2026-09-03"), False)
	la("chuỗi rỗng", lhh.qua_han("", "2026-09-03"), False)


@ca("v406 quá hạn tính theo ngày, đúng ngày hết hạn thì vẫn còn dùng được")
def _so_ngay():
	la("hôm qua hết hạn", lhh.qua_han("2026-09-02", "2026-09-03"), True)
	la("đúng hôm nay", lhh.qua_han("2026-09-03", "2026-09-03"), False)
	la("còn hạn", lhh.qua_han("2027-01-30", "2026-09-03"), False)
	# Frappe trả ngày kèm giờ ở vài chỗ, cắt mười ký tự đầu là đủ.
	la("có kèm giờ", lhh.qua_han("2026-09-02 00:00:00", "2026-09-03"), True)


@ca("v406 lọc riêng lô quá hạn, bỏ qua các lô vòng thường đã tính")
def _loc():
	cac_lo = {"A": 100, "B": 50, "C": 30}
	han = {"A": "2023-04-30", "B": "2027-01-30", "C": None}
	la("chỉ còn A", lhh.chi_lo_qua_han(cac_lo, han, "2026-09-03"), {"A": 100})
	la("bỏ qua A", lhh.chi_lo_qua_han(cac_lo, han, "2026-09-03", bo_qua={"A"}), {})
	la("không có lô", lhh.chi_lo_qua_han({}, han, "2026-09-03"), {})


# ------------------------------------------------------------- câu ghi vết


@ca("v406 dùng lô quá hạn thì phiếu phải mang câu ghi vết nêu rõ lô và hạn")
def _cau():
	cau = lhh.cau_ghi_chu([("NVLT00037", "KKK2600007-NVLT00037", "2023-04-30")])
	dung("có mã hàng", "NVLT00037" in cau)
	dung("có tên lô", "KKK2600007-NVLT00037" in cau)
	dung("có ngày hạn", "2023-04-30" in cau)
	la("không dùng lô quá hạn thì không ghi gì", lhh.cau_ghi_chu([]), "")


@ca("v406 lưu phiếu lần hai không xếp chồng câu ghi vết")
def _khong_chong():
	cau = lhh.cau_ghi_chu([("NVLT00037", "LO-1", "2023-04-30")])
	la("ghi chú đang trống", lhh.them_ghi_chu("", cau), cau)
	la("nối đúng một lần", lhh.them_ghi_chu(cau, cau), cau)
	# Lần lưu sau bếp lấy lô khác: câu cũ của mình bị thay, ghi chú người
	# gõ tay thì giữ nguyên.
	cau2 = lhh.cau_ghi_chu([("NVLT00037", "LO-2", "2024-01-01")])
	ra = lhh.them_ghi_chu("Bếp ghi tay: làm bù ca sáng.\n" + cau, cau2)
	dung("giữ chữ của người", "Bếp ghi tay: làm bù ca sáng." in ra)
	dung("mang câu mới", "LO-2" in ra)
	dung("bỏ câu cũ của máy", "LO-1" not in ra)


@ca("v406 giữ nguyên bốn loại phiếu mà ERPNext chặn lô quá hạn")
def _bon_loai():
	la("đủ bốn", sorted(lhh.PHIEU_BI_CHAN), sorted([
		"Manufacture", "Material Transfer for Manufacture", "Repack",
		"Send to Subcontractor",
	]))


# ---------------------------------------------------- canh cách vá và cách gọi


@ca("v406 chỉ thay đúng hàm validate_batch, không thay cả lớp Stock Entry")
def _cach_va():
	src = _py("lo_het_han.py")
	dung("thay đúng một hàm", "StockEntry.validate_batch = _thay_the(goc)" in src)
	dung("lặp lại được", "_DA_THAY" in src)
	dung("lô bị tắt vẫn chặn", "đang bị TẮT" in src)
	hooks = _py("hooks.py")
	dung("không thêm lớp thay Stock Entry",
		'"Stock Entry": "vagabond' not in hooks)
	dung("mở chốt chạy trước gán lô",
		hooks.index("vagabond.lo_het_han.mo_chot") < hooks.index("vagabond.lo_hang.gan_lo"))


@ca("v406 hỏi tồn từng lô phải biết đường xin cả lô quá hạn")
def _xin_lo_qua_han():
	src = _py("lo_hang.py")
	dung("có cờ ke_ca_qua_han", "def _ton_tung_lo(ma, kho, ke_ca_qua_han=False)" in src)
	dung("truyền cờ của ERPNext", "for_stock_levels=bool(ke_ca_qua_han)" in src)


@ca("v406 đường dự phòng phải đọc được số lô nằm trong gói Serial and Batch")
def _du_phong_doc_goi():
	src = _py("lo_hang.py")
	dung("đọc bảng gói", '"Serial and Batch Entry"' in src)
	dung("không còn cộng gộp theo cột trống",
		'fields=["batch_no", "sum(actual_qty) as ton"]' not in src)


@ca("v406 lô quá hạn là vòng vét CUỐI, sau lô còn hạn và sau mã thay thế")
def _vet_cuoi():
	src = _py("lo_hang.py")
	i_thay = src.index("for ma_thay in _cac_ma_thay_the(ma)")
	i_vet = src.index("_ton_lo_qua_han(ma, kho, da_tinh=ton)")
	i_chan = src.index('title="Thiếu hàng trong kho"')
	dung("vét sau mã thay thế", i_thay < i_vet)
	dung("vét trước khi chặn", i_vet < i_chan)
	dung("có ô tắt thì không vét", "not lo_het_han.dang_chan()" in src)


@ca("v406 ô chặn được khai bằng mã nguồn và mặc định là KHÔNG chặn")
def _o_cai_dat():
	src = _py("lo_het_han.py")
	dung("khai trường", '"fieldname": "chan_lo_het_han"' in src)
	dung("mặc định trống", '"default": "0"' in src)
	dung("dựng lại sau deploy", "lo_het_han.TRUONG_MOI" in _py("truong_tu_them.py"))


@ca("v406 có dòng patch mới để Frappe Cloud chạy migrate chứ không chỉ pull")
def _patch():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng v406", "vagabond.patches.dong_bo_cau_truc #v406" in dong)
	dung("dòng của phiên khác còn nguyên", "vagabond.patches.dong_bo_cau_truc #v404" in dong)


# ------------------------------------------- chạy thử chính hàm vá vào chỗ


class _Dong(object):
	def __init__(self, ma, lo):
		self.item_code, self.batch_no = ma, lo


class _Phieu(object):
	"""Phiếu kho giả, đủ những gì hàm validate_batch đụng tới."""

	def __init__(self, purpose, ngay, dong):
		self.purpose, self.posting_date, self._dong = purpose, ngay, dong
		self.remarks = ""

	def get(self, ten):
		return self._dong if ten == "items" else None


_CUA_THAT = (lhh.dang_chan, lhh._ho_so_lo)


def _tra_lai():
	"""Trả hai cửa chạm hệ về như cũ, đừng để ca này ảnh hưởng ca khác."""
	lhh.dang_chan, lhh._ho_so_lo = _CUA_THAT


def _voi_lo(ho_so, chan=0):
	"""Thay tạm hai cửa chạm hệ, trả về hàm validate_batch đã vá."""
	lhh.dang_chan = lambda: chan
	lhh._ho_so_lo = lambda ten: ho_so.get(ten, {})

	def goc(self):
		self.da_goi_goc = True

	return lhh._thay_the(goc)


@ca("v406 chốt tắt: phiếu sản xuất mang lô quá hạn vẫn ghi được, có ghi vết")
def _cho_xuat():
	ho_so = {"LO-CU": {"disabled": 0, "expiry_date": "2023-04-30"}}
	ham = _voi_lo(ho_so)
	p = _Phieu("Manufacture", "2026-09-03", [_Dong("NVLT00037", "LO-CU")])
	ham(p)
	_tra_lai()
	dung("không gọi bản gốc", not getattr(p, "da_goi_goc", False))
	dung("có ghi vết", "NVLT00037" in p.remarks and "2023-04-30" in p.remarks)


@ca("v406 chốt tắt vẫn CHẶN CỨNG lô bị tắt, tắt lô là quyết định của người")
def _lo_bi_tat():
	ham = _voi_lo({"LO-TAT": {"disabled": 1, "expiry_date": None}})
	p = _Phieu("Manufacture", "2026-09-03", [_Dong("NVLT00037", "LO-TAT")])
	try:
		ham(p)
		_tra_lai()
		dung("phải chặn lô bị tắt", False)
	except Exception as e:
		_tra_lai()
		dung("nói rõ lô nào", "LO-TAT" in str(e))


@ca("v406 lô còn hạn thì phiếu sạch, không ai bị ghi vết oan")
def _con_han_sach():
	ham = _voi_lo({"LO-MOI": {"disabled": 0, "expiry_date": "2027-01-30"}})
	p = _Phieu("Manufacture", "2026-09-03", [_Dong("NVLT00039", "LO-MOI")])
	ham(p)
	_tra_lai()
	la("ghi chú vẫn trống", p.remarks, "")


@ca("v406 tích ô chặn thì trả nguyên phép kiểm của ERPNext, không chế thêm")
def _bat_chot_lai():
	ham = _voi_lo({"LO-CU": {"disabled": 0, "expiry_date": "2023-04-30"}}, chan=1)
	p = _Phieu("Manufacture", "2026-09-03", [_Dong("NVLT00037", "LO-CU")])
	ham(p)
	_tra_lai()
	dung("gọi đúng bản gốc của ERPNext", getattr(p, "da_goi_goc", False))
