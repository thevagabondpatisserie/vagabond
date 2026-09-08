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


@ca("206 thay hai phép kiểm lô riêng Stock Entry, không thay controller dùng chung")
def _cach_va():
	src = _py("lo_het_han.py")
	dung("thay validate_batch", "StockEntry.validate_batch = _thay_the(goc)" in src)
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
	# 06/09/2026: ca nay truoc day do vi tri ba doan CHUOI trong ma nguon.
	# Doi chuoi mot cai la ca do, ma do khong chung minh duoc thu tu that
	# (dieu 16). Nay chay that gan_lo va xem no lay lo nao truoc.
	from vagabond.khung.kiem_thu import thu_nhan_nvl_chon_lo as t

	ra = t.chay_gan_lo(
		purpose="Manufacture",
		dong=[t.dong("NVL1", "Kho A", 100)],
		ton={("NVL1", "Kho A"): {"CON-HAN": 40}, ("NVL2", "Kho A"): {"THAY": 30}},
		qua_han={("NVL1", "Kho A"): {"QUA-HAN": 100}},
		thay_the={"NVL1": ["NVL2"]},
	)
	# Thu tu LAY moi la thu tu can canh, khong phai thu tu DONG in ra:
	# ma chinh (ke ca phan vet) in truoc, ma thay the in sau. Neu vong vet
	# chay TRUOC ma thay the thi QUA-HAN se lay 60 va THAY lay 0.
	lay = {}
	for d in ra:
		lay[(d["item_code"], d["batch_no"])] = d["qty"]
	la("lô còn hạn lấy trước", lay.get(("NVL1", "CON-HAN")), 40.0)
	la("hết lô còn hạn thì tới mã thay thế", lay.get(("NVL2", "THAY")), 30.0)
	la("lô quá hạn chỉ nhận phần còn lại", lay.get(("NVL1", "QUA-HAN")), 30.0)
	la("đúng ba dòng", len(ra), 3)
	src = _py("lo_hang.py")
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
	ham = _voi_lo({"LO-CU": {"disabled": 0, "expiry_date": "2027-04-30"}}, chan=1)
	p = _Phieu("Manufacture", "2026-09-03", [_Dong("NVLT00037", "LO-CU")])
	ham(p)
	_tra_lai()
	dung("gọi đúng bản gốc của ERPNext", getattr(p, "da_goi_goc", False))


@ca("206 lớp kiểm thứ hai: tắt chốt, nhiều lô/gói, giữ ghi chú, không lặp vết")
def _lop_hai():
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	import sys
	p = _Phieu('Manufacture', '2026-09-08', [
		_Dong('BOT', 'HET-1'), _Dong('BO', 'HET-2')])
	p._dong[1].serial_and_batch_bundle = 'GOI-2'
	p.remarks = 'Bếp ghi tay'
	goc = Mock()
	with patch.object(lhh, 'dang_chan', return_value=0), \
		patch.object(lhh, '_ho_so_lo', return_value={'disabled': 0, 'expiry_date': '2026-09-01'}), \
		patch.object(lhh.frappe, 'get_all', return_value=['HET-2'], create=True), \
		patch.dict(sys.modules, {'erpnext.stock.doctype.serial_no.serial_no': SimpleNamespace(get_serial_nos=lambda x: x.splitlines())}):
		ham = lhh._thay_kiem_serial(goc)
		ham(p); ham(p)
	goc.assert_not_called()
	la('giữ ghi tay', p.remarks.splitlines()[0], 'Bếp ghi tay')
	la('một câu dấu vết', p.remarks.count(lhh.DAU_CAU), 1)
	la('lô tay/gói không ghi trùng', p.remarks.count('HET-2'), 1)
	dung('ghi đủ hai mã lô hạn', all(x in p.remarks for x in ['BOT', 'BO', 'HET-1', 'HET-2', '2026-09-01']))


@ca("206 bật chốt chặn cả gói quá hạn; tắt chốt vẫn chặn gói bị tắt")
def _chan_goi():
	from unittest.mock import patch, Mock
	p = _Phieu('Manufacture', '2026-09-08', [_Dong('BOT', None)])
	p._dong[0].serial_and_batch_bundle = 'GOI'
	for chan, ho in [(1, {'disabled':0, 'expiry_date':'2026-09-01'}), (0, {'disabled':1})]:
		with patch.object(lhh.frappe, 'get_all', return_value=['LO-GOI'], create=True), \
			patch.object(lhh, '_ho_so_lo', return_value=ho):
			try:
				lhh._kiem_lo_va_ghi_vet(p, chan=chan)
				dung('phải chặn', False)
			except Exception as e:
				dung('đúng lô', 'LO-GOI' in str(e))


@ca("206 không bỏ kiểm serial sai lô và không nới phiếu nhận/huỷ")
def _serial_sai():
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	import sys
	p = _Phieu('Manufacture', '2026-09-08', [_Dong('BOT', 'LO-A')])
	p._dong[0].serial_no = 'SERIAL-1'; p._dong[0].idx = 2
	goc = Mock()
	with patch.object(lhh, 'dang_chan', return_value=0), \
		patch.object(lhh.frappe, '_', side_effect=lambda x: x, create=True), \
		patch.object(lhh.frappe, 'get_all', return_value=[SimpleNamespace(name='SERIAL-1', batch_no='LO-B', warehouse='Pastry')], create=True), \
		patch.dict(sys.modules, {'erpnext.stock.doctype.serial_no.serial_no': SimpleNamespace(get_serial_nos=lambda x: x.splitlines())}):
		ham = lhh._thay_kiem_serial(goc)
		try:
			ham(p)
			dung('serial sai lô phải chặn', False)
		except Exception as e:
			dung('đúng serial và lô', 'SERIAL-1' in str(e) and 'LO-A' in str(e))
		p.purpose = 'Material Receipt'; ham(p)
		p.purpose = 'Manufacture'; p.docstatus = 2; ham(p)
	la('nhận và huỷ đi nguyên lõi', goc.call_count, 2)
