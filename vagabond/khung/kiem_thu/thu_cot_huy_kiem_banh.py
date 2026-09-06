# -*- coding: utf-8 -*-
"""Cột Huỷ trên bảng Kiểm bánh hôm nay.

Anh Việt chốt ngày 06/09/2026, hướng A của issue #216: *"Em thêm cột huỷ trên
màn kiểm bánh cho các bạn nhập tay theo dõi là được."*

Vì sao cửa hàng không đi qua phiếu xuất huỷ kho: `xuat_kho.tim_hang` chỉ liệt
kê mã còn tồn ERPNext trong kho đã chọn, mà Kho D1 không được nạp bánh hàng
ngày - 218 mã bánh thành phẩm chỉ 30 mã có tồn ở đó. Gốc rễ là Sổ nhận bánh cố
ý không sinh Stock Entry (quyết định 23/08/2026, lý do đầy đủ trong
`vagabond/nhan_banh.py`).

BỐN CHỖ CÓ THỂ HỎNG ÂM THẦM, mỗi chỗ có ca chặn:

  1. Huỷ không trừ vào "bán được" -> quầy vẫn bán con bánh đã vứt.
  2. Huỷ không ăn vào lô hàng lúc chốt ngày -> tồn đầu ngày mai phình ảo, cộng
     dồn mãi.
  3. Huỷ ÂM -> "bán được" TĂNG lên. Codex bắt trên PR #218: `luu_o` có kẹp về 0
     nhưng đó chỉ là một đường vào, Desk và API document đi thẳng vào doctype.
  4. Huỷ ăn nhầm vào vỏ BTP. Quy tắc trừ BTP chưa ai duyệt sửa.

ĐÂY LÀ TỆP ĐÃ TỪNG BỊ BẮT LÀ KIỂM YẾU. Vòng một chỉ có ca thuần và ca dò chuỗi,
nên bốn lỗi trên lọt hết. Vòng hai thêm các ca CHẠY THẬT `luu_o`, `xoa_dong`,
`bang` và `chot_ngay` qua một cửa cơ sở dữ liệu giả có kiểm soát. Đừng rút các
ca đó về dò chuỗi cho gọn.
"""

import io
import json
import os
import re

import frappe

from vagabond import kiem_banh
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la, nem
from vagabond.vagabond.doctype.kiem_banh_ngay.kiem_banh_ngay import KiemBanhNgay

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*ten):
	with io.open(os.path.join(GOI, *ten), encoding="utf-8") as f:
		return f.read()


# ------------------------------------------------------- bàn dựng bảng giả


COT = ("ton_cu", "ton_d2", "ton_d1", "sx", "huy", "da_dat", "phat_sinh",
	"don_khac", "cho_chot", "giu_cho", "co_the_ban")


class DongGia(Doi):
	"""Một dòng bảng, đủ hành vi `get`/`set` mà mã nghiệp vụ đang gọi."""

	def get(self, k, mac_dinh=None):
		return dict.get(self, k, mac_dinh)

	def set(self, k, v):
		self[k] = v


class BangGia(KiemBanhNgay):
	"""Một bản ghi Kiem Banh Ngay chạy được ngoài site.

	Kế thừa THẲNG lớp doctype thật, nên `validate` chạy đúng bản đang có trong
	repo chứ không phải bản chép lại. Chỉ giả đúng ba việc Frappe làm hộ:
	`save`, `append`, `remove`.
	"""

	def __init__(self, ngay="2026-08-15", tinh_trang="Dang ban", dong=None):
		self.ngay = ngay
		self.tinh_trang = tinh_trang
		self.dong = list(dong or [])
		self.so_lan_luu = 0
		self.dong_bo_luc = None
		self.chot_luc = None
		self.ghi_chu = ""

	def save(self, *a, **k):
		self.validate()
		self.so_lan_luu += 1

	def reload(self):
		return self

	def append(self, _bang, gt):
		d = _tao_dong(**gt)
		self.dong.append(d)
		return d

	def remove(self, d):
		self.dong.remove(d)


def _tao_dong(**kw):
	d = DongGia({c: 0 for c in COT})
	d.update({"ma_hang": "BAWC00001", "ten_banh": "Bánh thử", "hinh": "",
		"nsx_cu": None, "nsx_d2": None, "nsx_d1": None,
		"ten_khach_ps": "", "ten_khach_cho": "", "ten_khach_khac": ""})
	d.update(kw)
	return d


class CuaGia(object):
	"""Thay `frappe.get_doc` và bạn bè trong đúng một ca kiểm, rồi trả lại.

	Có lớp này thì mới gọi được `luu_o`, `xoa_dong`, `bang`, `chot_ngay` THẬT.
	Không có nó thì chỉ còn cách dò chuỗi, mà dò chuỗi đã để lọt cả bốn lỗi ở
	vòng một.
	"""

	def __init__(self, **bang):
		self.bang = dict(bang)
		self.btp = None
		self.cu = {}

	def __enter__(self):
		self.cu = {
			"get_doc": frappe.get_doc,
			"exists": frappe.db.exists,
			"get_single": getattr(frappe, "get_single", None),
			"dong_bo": kiem_banh.dong_bo,
			"tat_bang": kiem_banh.tat_ban_web.bang,
		}
		frappe.get_doc = lambda dt, ten=None, *a, **k: self._lay(ten)
		frappe.db.exists = lambda dt, ten=None, *a, **k: ten in self.bang
		frappe.get_single = lambda dt: self.btp
		kiem_banh.dong_bo = lambda ngay=None: None
		kiem_banh.tat_ban_web.bang = lambda ds, ngay=None: {}
		return self

	def __exit__(self, *a):
		frappe.get_doc = self.cu["get_doc"]
		frappe.db.exists = self.cu["exists"]
		if self.cu["get_single"] is not None:
			frappe.get_single = self.cu["get_single"]
		kiem_banh.dong_bo = self.cu["dong_bo"]
		kiem_banh.tat_ban_web.bang = self.cu["tat_bang"]
		return False

	def _lay(self, ten):
		if ten not in self.bang:
			self.bang[ten] = BangGia(ngay=str(ten).replace("KB-", ""))
		return self.bang[ten]


def _tinh(**kw):
	"""Chạy THẬT `validate` của doctype rồi trả về "có thể bán"."""
	d = _tao_dong(**kw)
	BangGia(dong=[d]).validate()
	return d.co_the_ban


# --------------------------------------------------- 1. trừ vào "bán được"


@ca("huỷ trừ thẳng vào bán được, không đụng các cột khác")
def _():
	la("chưa huỷ gì", _tinh(ton_d1=10, sx=5), 15)
	la("huỷ 3", _tinh(ton_d1=10, sx=5, huy=3), 12)
	la("huỷ hết", _tinh(ton_d1=10, sx=5, huy=15), 0)
	# Huỷ nhiều hơn tồn là con số ÂM có thật, không được kẹp về 0: bảng phải
	# tô đỏ để người đối chiếu, giống hệt cột bán được âm sẵn có.
	la("huỷ quá tồn thì âm, không kẹp về 0", _tinh(ton_d1=2, huy=5), -3)


@ca("huỷ cộng dồn đúng với các cột đang có, không thay chỗ cột nào")
def _():
	chung = dict(ton_cu=4, ton_d2=3, ton_d1=2, sx=10, da_dat=5, phat_sinh=1,
		cho_chot=2, don_khac=1, giu_cho=1)
	la("chưa có cột huỷ", _tinh(**chung), 9)
	la("thêm huỷ 4", _tinh(huy=4, **chung), 5)


# ------------------------------------------------------- 2. chặn huỷ âm


@ca("huỷ ÂM bị doctype chặn thẳng, không lặng lẽ làm tăng bán được")
def _():
	"""Codex bắt trên PR #218. Trước khi sửa: tồn 10 huỷ -3 cho ra 13."""
	nem("huỷ -1 phải ném lỗi", lambda: _tinh(ton_d1=10, huy=-1))
	nem("huỷ -3 phải ném lỗi", lambda: _tinh(ton_d1=10, huy=-3))
	nem("huỷ không phải số phải ném lỗi", lambda: _tinh(ton_d1=10, huy="ba"))
	# 0 và số dương vẫn phải chạy bình thường.
	la("huỷ 0 vẫn chạy", _tinh(ton_d1=10, huy=0), 10)
	la("huỷ 4 vẫn chạy", _tinh(ton_d1=10, huy=4), 6)


@ca("số huỷ được KIỂM trước khi ép kiểu, không cắt số rồi mới xét")
def _():
	"""Codex bắt vòng hai trên PR #218.

	Bản vá đầu viết `int(d.huy or 0)` rồi mới xét `n < 0`, nên `-0.5` được
	nhận và lưu thành 0, `1.9` được nhận và lưu thành 1. Giá trị không hợp lệ
	bị biến thành một con số khác mà không ai báo - đúng kiểu hỏng âm thầm mà
	cột này sinh ra để tránh.
	"""
	nem("-0.5 phải ném lỗi, không được thành 0", lambda: _tinh(ton_d1=10, huy=-0.5))
	nem("1.9 phải ném lỗi, không được thành 1", lambda: _tinh(ton_d1=10, huy=1.9))
	nem("chuỗi '3.5' phải ném lỗi", lambda: _tinh(ton_d1=10, huy="3.5"))
	nem("vô cực phải ném lỗi", lambda: _tinh(ton_d1=10, huy=float("inf")))
	nem("NaN phải ném lỗi", lambda: _tinh(ton_d1=10, huy=float("nan")))
	nem("kiểu lạ phải ném lỗi", lambda: _tinh(ton_d1=10, huy=[3]))
	# Va khong duoc lang le doi thanh so khac: kiem CA GIA TRI da luu.
	d = _tao_dong(ton_d1=10, huy=-0.5)
	try:
		BangGia(dong=[d]).validate()
	except Exception:
		pass
	dung("giá trị sai KHÔNG bị biến thành 0 rồi lưu", d.huy in (-0.5,))


@ca("chính sách nhận số huỷ: rỗng là 0, số tròn và chuỗi số nguyên thì nhận")
def _():
	"""Viết chính sách ra thành ca kiểm để người sau khỏi phải đoán."""
	doc_so = KiemBanhNgay._doc_so_huy
	la("None là 0", doc_so(None), 0)
	la("chuỗi rỗng là 0", doc_so(""), 0)
	la("khoảng trắng là 0", doc_so("   "), 0)
	la("số nguyên giữ nguyên", doc_so(3), 3)
	la("chuỗi số nguyên đọc được", doc_so("3"), 3)
	la("chuỗi có khoảng trắng vẫn đọc được", doc_so(" 3 "), 3)
	la("số thực TRÒN thì nhận", doc_so(3.0), 3)
	la("0 vẫn là 0", doc_so(0), 0)
	# Và các giá trị bị chặn thì không bao giờ trả về số.
	for xau in (-1, -0.5, 1.9, "3.5", "ba", [3], {}, float("inf"), float("nan")):
		nem("chặn %r" % (xau,), lambda x=xau: doc_so(x))


@ca("lời báo huỷ âm có dấu và nói rõ cách sửa")
def _():
	try:
		_tinh(ma_hang="BAWC00099", ton_d1=10, huy=-2)
	except Exception as e:
		loi = str(e)
	else:
		loi = ""
	dung("có ném lỗi", bool(loi))
	dung("nhắc đúng mã hàng", "BAWC00099" in loi)
	dung("nói rõ phải không âm", "không âm" in loi)
	dung("bảo người ta làm gì", "sửa về 0" in loi)


@ca("chặn ở lớp doctype chứ không chỉ ở ô nhập trên màn")
def _():
	"""Ô nhập có min=0 là gợi ý cho người gõ, không phải hàng rào cho máy.

	Desk và `frappe.client.set_value` đi thẳng vào doctype, không qua `luu_o`.
	"""
	src = _doc("vagabond", "doctype", "kiem_banh_ngay", "kiem_banh_ngay.py")
	dung("validate có gọi hàng rào", "self._chan_huy_am()" in src)
	i = src.find("def validate(")
	j = src.find("_chan_huy_am()", i)
	k = src.find("co_the_ban", i)
	dung("chặn TRƯỚC khi tính có thể bán", -1 < j < k)


# --------------------------------------------------- 3. hai đại lượng riêng


@ca("bán ra và rời tủ là HAI đại lượng, chỉ dùng chung một nền")
def _():
	la("bán ra không tính huỷ", kiem_banh.so_ban_ra(3, 2, 1), 6)
	la("rời tủ có tính huỷ", kiem_banh.so_roi_tu(3, 2, 1, 4), 10)
	la("không huỷ thì hai số bằng nhau",
		kiem_banh.so_roi_tu(3, 2, 1, 0), kiem_banh.so_ban_ra(3, 2, 1))
	la("chỉ huỷ", kiem_banh.so_roi_tu(0, 0, 0, 7), 7)
	la("None cũng chịu được", kiem_banh.so_roi_tu(None, None, None, None), 0)
	la("bán ra không bao giờ âm", kiem_banh.so_ban_ra(-5, 0, 0), 0)
	la("phần huỷ âm không kéo tổng xuống", kiem_banh.so_roi_tu(3, 0, 0, -9), 3)


@ca("bánh huỷ ăn vào lô cũ trước, KHÔNG chạy sang tồn ngày mai")
def _():
	lo = [[2, "cu"], [3, "d2"], [4, "d1"], [10, "sx"]]
	du = kiem_banh.tru_theo_lo(lo, kiem_banh.so_roi_tu(0, 0, 0, 6))
	la("không dư", du, 0)
	la("lô cũ nhất hết trước", lo[0][0], 0)
	la("lô d2 hết theo", lo[1][0], 0)
	la("lô d1 còn 3", lo[2][0], 3)
	la("lô bếp làm còn nguyên", lo[3][0], 10)


@ca("huỷ và bán cùng ngày thì cộng lại rồi mới ăn vào lô")
def _():
	lo = [[5, "cu"], [0, None], [0, None], [8, "sx"]]
	kiem_banh.tru_theo_lo(lo, kiem_banh.so_roi_tu(4, 0, 0, 3))
	la("lô cũ hết", lo[0][0], 0)
	la("ăn tiếp 2 vào lô bếp làm", lo[3][0], 6)


@ca("tiêu nhiều hơn tồn thì báo phần dư, không để lô âm")
def _():
	lo = [[2, "cu"], [1, "d1"]]
	du = kiem_banh.tru_theo_lo(lo, 9)
	la("dư 6", du, 6)
	la("lô không âm", [c[0] for c in lo], [0, 0])


# ------------------------------------- 4. chạy thật luu_o, xoa_dong, bang


@ca("luu_o ghi được số huỷ và trả về bán được đã tính lại")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10)
	bang = BangGia(dong=[d])
	with CuaGia(**{"KB-2026-08-15": bang}):
		kq = kiem_banh.luu_o("2026-08-15", "BAWC00055", "huy", 3)
	la("ô huỷ đã ghi", d.huy, 3)
	la("bán được trả về đúng", kq["co_the_ban"], 7)
	la("có lưu đúng một lần", bang.so_lan_luu, 1)


@ca("luu_o kẹp số huỷ âm về 0 thay vì để doctype ném lỗi")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10)
	with CuaGia(**{"KB-2026-08-15": BangGia(dong=[d])}):
		kq = kiem_banh.luu_o("2026-08-15", "BAWC00055", "huy", -4)
	la("kẹp về 0", d.huy, 0)
	la("bán được nguyên tồn", kq["co_the_ban"], 10)


@ca("luu_o không cho sửa cột máy đếm, và không cho sửa ngày đã chốt")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10)
	with CuaGia(**{"KB-2026-08-15": BangGia(dong=[d])}):
		nem("không sửa được đã đặt",
			lambda: kiem_banh.luu_o("2026-08-15", "BAWC00055", "da_dat", 5))
		nem("không sửa được có thể bán",
			lambda: kiem_banh.luu_o("2026-08-15", "BAWC00055", "co_the_ban", 5))
	d2 = _tao_dong(ma_hang="BAWC00055", ton_d1=10)
	chot = BangGia(tinh_trang="Da chot", dong=[d2])
	with CuaGia(**{"KB-2026-08-15": chot}):
		nem("ngày đã chốt thì không ghi huỷ",
			lambda: kiem_banh.luu_o("2026-08-15", "BAWC00055", "huy", 2))
	la("số cũ không đổi", d2.huy, 0)


@ca("dòng đang có số huỷ thì dấu x không xoá được")
def _():
	d = _tao_dong(ma_hang="BAWC00055", huy=2)
	bang = BangGia(dong=[d])
	with CuaGia(**{"KB-2026-08-15": bang}):
		nem("có số huỷ thì chặn",
			lambda: kiem_banh.xoa_dong("2026-08-15", "BAWC00055"))
		la("dòng còn nguyên", len(bang.dong), 1)
		d["huy"] = 0
		kq = kiem_banh.xoa_dong("2026-08-15", "BAWC00055")
	la("xoá số về 0 rồi thì xoá được", kq["ok"], 1)
	la("bảng còn 0 dòng", len(bang.dong), 0)


@ca("bang trả cột huỷ xuống màn hình")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, huy=3)
	bang = BangGia(dong=[d])
	bang.validate()
	with CuaGia(**{"KB-2026-08-15": bang}):
		kq = kiem_banh.bang("2026-08-15")
	la("có đúng một dòng", len(kq["dong"]), 1)
	la("có khoá huy", kq["dong"][0]["huy"], 3)
	la("bán được đi kèm", kq["dong"][0]["co_the_ban"], 7)


# ------------------------------------------- 5. chạy thật chot_ngay


def _chot(hom_nay, mai=None, btp=None):
	"""Chạy THẬT `chot_ngay` rồi trả về bảng ngày mai và kho BTP."""
	nay = BangGia(ngay="2026-08-15", dong=hom_nay)
	ngay_mai = BangGia(ngay="2026-08-16", dong=(mai or []))
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": ngay_mai})
	cua.btp = Doi({"dong": btp or [], "cap_nhat_luc": None,
		"save": lambda *a, **k: None})
	with cua:
		kiem_banh.chot_ngay("2026-08-15")
	return nay, ngay_mai, cua.btp


@ca("chốt ngày: bánh huỷ biến khỏi tồn, phần còn lại chạy sang ngày mai")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, huy=3)
	nay, mai, _b = _chot([d])
	la("ngày mai có một dòng", len(mai.dong), 1)
	la("tồn chuyển sang đúng 7", mai.dong[0].ton_cu + mai.dong[0].ton_d2
		+ mai.dong[0].ton_d1, 7)
	la("hôm nay đã khoá", nay.tinh_trang, "Da chot")


@ca("chốt ngày KHÔNG trừ vỏ BTP theo số huỷ - giữ nguyên quy tắc cũ")
def _():
	"""Quy tắc trừ BTP chưa ai duyệt sửa (Codex chặn trên PR #218).

	Bản đầu của PR gộp huỷ vào cùng một hàm với bán ra rồi dùng cho cả hai
	chỗ, thành ra lặng lẽ đổi luôn số vỏ BTP. Ca này khoá lại: chỉ số BÁN RA
	mới ăn vào vỏ.
	"""
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=20, da_dat=5, huy=3)
	b = Doi({"ma_hang": "BAWC00055", "so_btp": 20, "so_decor": 15})
	_nay, mai, kho = _chot([d], btp=[b])
	la("vỏ BTP chỉ trừ 5 bánh bán ra", kho["dong"][0].so_btp, 15)
	la("decor cũng chỉ trừ 5", kho["dong"][0].so_decor, 10)
	# Nhưng tồn thì vẫn phải trừ cả 8 (5 bán + 3 huỷ).
	la("tồn ngày mai là 12, tức trừ đủ 8", mai.dong[0].ton_cu
		+ mai.dong[0].ton_d2 + mai.dong[0].ton_d1, 12)


@ca("GÓC ĐÃ BIẾT: hôm nay huỷ hết thì chốt ngày KHÔNG đụng dòng ngày mai")
def _():
	"""Nhánh CŨ, không phải PR này sinh ra. Codex yêu cầu ghi lại và khoá.

	Khi hôm nay không còn lô nào thì `chot_ngay` `continue`, nên một dòng
	cùng mã đã có sẵn bên ngày mai giữ nguyên số của nó. Chưa xác định được
	số đó là tồn chuyển sang hay số kiểm kê độc lập của ngày mai, nên KHÔNG
	tự xoá. Ca này chốt hành vi hiện tại để người sau đổi thì phải đổi có ý
	thức, chứ không phải để tuyên bố hành vi này đúng.
	"""
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=3, huy=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d1=7)
	_nay, mai, _b = _chot([d], mai=[m])
	la("dòng ngày mai vẫn còn", len(mai.dong), 1)
	la("số ngày mai KHÔNG bị đụng tới", mai.dong[0].ton_d1, 7)


# --------------------------------------------------- 6. các cửa chặn khác


@ca("huỷ là cột người gõ tay, và luu_o nhận nó")
def _():
	dung("huỷ sửa tay được", "huy" in kiem_banh.SUA_DUOC)
	for cot in ("ton_cu", "ton_d2", "ton_d1", "sx"):
		dung("vẫn giữ %s" % cot, cot in kiem_banh.SUA_DUOC)
	for cot in ("da_dat", "phat_sinh", "don_khac", "cho_chot", "giu_cho", "co_the_ban"):
		dung("%s vẫn không sửa tay được" % cot, cot not in kiem_banh.SUA_DUOC)


@ca("huỷ nằm trong danh sách phải rỗng mới xoá được dòng")
def _():
	dung("huỷ nằm trong danh sách", "huy" in kiem_banh.SO_PHAI_RONG)
	for cot in ("ton_cu", "ton_d2", "ton_d1", "sx", "da_dat", "phat_sinh",
			"cho_chot", "don_khac"):
		dung("vẫn giữ %s" % cot, cot in kiem_banh.SO_PHAI_RONG)


@ca("ô huỷ đã khai trong doctype, nhãn có dấu, đặt ngay sau Bếp làm")
def _():
	d = json.loads(_doc("vagabond", "doctype", "kiem_banh_dong",
		"kiem_banh_dong.json"))
	ten = [f["fieldname"] for f in d["fields"]]
	dung("có ô huy", "huy" in ten)
	la("nằm ngay sau sx", ten[ten.index("sx") + 1], "huy")
	la("cũng đứng đúng chỗ trong field_order",
		d["field_order"][d["field_order"].index("sx") + 1], "huy")
	o = [f for f in d["fields"] if f["fieldname"] == "huy"][0]
	la("là số nguyên", o["fieldtype"], "Int")
	# AGENTS.md mục 3: chuỗi hiện ra màn hình phải có dấu tiếng Việt.
	la("nhãn có dấu", o["label"], "Huỷ trong ngày")


# --------------------------------------------------------- 7. màn hình


@ca("màn kiểm bánh vẽ ô Huỷ, gõ tay được, nằm sau Bếp làm")
def _():
	js = _doc("trang", "kiem-banh.js")
	i = js.find('+ o(d, "sx", "Bếp làm "')
	dung("tìm thấy ô Bếp làm", i > 0)
	sau = js[i:i + 900]
	j = sau.find('o(d, "huy"')
	dung("ô Huỷ nằm sau ô Bếp làm", j > 0)
	dung("ô Huỷ đứng trước ô Đã đặt", j < sau.find('o(d, "da_dat"'))
	dung("gõ tay được", 'o(d, "huy", "Huỷ", d.huy, true, "huy")' in js)
	dung("dòng có số huỷ thì không xoá được", "d.huy ||" in js)


def _nen_theo_o(css, so_o=17):
	"""Giải cascade các luật nth-child của lưới, trả về nền từng ô.

	Vì sao phải giải chứ không dò chuỗi: vòng một chỉ tìm chuỗi nhóm vàng nên
	ca vẫn xanh, trong khi một luật NẰM SAU nó nhắm đúng ô 15 đã ghi đè mất
	màu vàng của ô Đủ decor và bỏ trắng ô 17. Codex bắt được, bộ kiểm thì
	không. Đo bằng trình duyệt cho ra cùng kết quả, nhưng bộ kiểm tầng khung
	không có trình duyệt nên giải bằng tay ở đây.

	Mọi luật trong khối này cùng dạng `#kb .kb-so .kb-o:nth-child(...)`, nên
	độ ưu tiên chỉ khác nhau ở SỐ pseudo-class; bằng nhau thì luật sau thắng.
	"""
	mau = {}
	uu_tien = {}
	re_luat = re.compile(r"^(#kb \.kb-so \.kb-o:nth-child\([^{]*?)\{([^}]*)\}$")
	for thu_tu, dong in enumerate(css.splitlines()):
		dong = dong.strip()
		m = re_luat.match(dong)
		if not m:
			continue
		chon, than = m.group(1), m.group(2)
		if "background" not in than:
			continue
		nen = re.search(r"background:(#[0-9a-fA-F]+)", than)
		if not nen:
			continue
		nen = nen.group(1)
		for bo in chon.split(","):
			bo = bo.strip()
			if bo.endswith(" label"):
				continue
			so_pseudo = bo.count(":nth-child(")
			rng = re.search(r":nth-child\(n\+(\d+)\):nth-child\(-n\+(\d+)\)", bo)
			don = re.search(r":nth-child\((\d+)\)$", bo)
			if rng:
				cac_o = range(int(rng.group(1)), int(rng.group(2)) + 1)
			elif don:
				cac_o = [int(don.group(1))]
			else:
				continue
			for n in cac_o:
				if n > so_o:
					continue
				khoa = (so_pseudo, thu_tu)
				if khoa >= uu_tien.get(n, (-1, -1)):
					uu_tien[n] = khoa
					mau[n] = nen
	return mau


@ca("lưới đủ 17 cột và MỖI ô nhận đúng màu nhóm của nó")
def _():
	css = _doc("trang", "kiem-banh.html")
	dung("lưới 17 cột", "grid-template-columns:repeat(17,1fr)" in css)
	dung("không còn lưới 16 cột", "repeat(16,1fr)" not in css)
	mau = _nen_theo_o(css)
	MONG = {
		4: "#fefce8",                                    # Bếp làm
		6: "#eff6ff", 7: "#eff6ff", 8: "#eff6ff",        # khối đơn máy đếm
		9: "#eff6ff", 10: "#eff6ff", 11: "#eff6ff", 12: "#eff6ff",
		13: "#fff",                                      # BÁN ĐƯỢC
		14: "#fefce8", 15: "#fefce8",                    # BTP sẵn, Đủ decor
		16: "#effbf8", 17: "#effbf8",                    # hai ô CÒN NHẬN
	}
	for n, nen in sorted(MONG.items()):
		la("ô %d đúng màu nhóm" % n, mau.get(n), nen)
	for n in (1, 2, 3):
		dung("ô %d không bị nhóm nào tô" % n, n not in mau)
	# Ô Huỷ tô bằng lớp riêng chứ không bằng nth-child, để còn đổi chỗ được.
	dung("ô Huỷ có màu riêng theo lớp", ".kb-o.huy{background:#fff5f5}" in css)
	dung("ô Huỷ không bị nth-child tô đè", 5 not in mau)


@ca("chú giải trên màn nói đúng: huỷ không trừ vào kho BTP")
def _():
	css = _doc("trang", "kiem-banh.html")
	dung("nói rõ ô này không nhận số âm", "Ô này không nhận số âm" in css)
	dung("nói rõ huỷ không trừ BTP", "KHÔNG trừ vào kho BTP sẵn" in css)
	dung("công thức BÁN ĐƯỢC có huỷ",
		"tồn + bếp làm - huỷ - đã đặt" in css)
	dung("chú giải chốt ngày nói BÁN RA chứ không nói rời tủ",
		"KHÔNG tính huỷ" in css)


@ca("KHÔNG còn chỗ nào tự cộng lại số bán ra thay vì gọi hàm chung")
def _():
	"""Điều 18: sửa bằng cách gom về một nguồn, không rải phép cộng."""
	src = _doc("kiem_banh.py")
	i = src.find("def chot_ngay(")
	than = src[i:src.find("\ndef ", i + 10)]
	dung("không còn phép cộng tay trong chot_ngay",
		"(d.da_dat or 0) + (d.phat_sinh or 0)" not in than)
	la("lô hàng gọi so_roi_tu đúng một lần", than.count("so_roi_tu("), 1)
	la("vỏ BTP gọi so_ban_ra đúng một lần", than.count("so_ban_ra("), 1)
	dung("không còn tên hàm gộp cũ", "so_da_tieu(" not in src)
