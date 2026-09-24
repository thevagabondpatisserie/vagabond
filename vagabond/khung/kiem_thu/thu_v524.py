"""v524, anh Việt chốt 24/09/2026.

1. Nhóm "CCDC dùng ngay": quạt Uyên mua cho nhân viên (Điện Máy Xanh, Midea
   FS40-24EVN). Chị Dung hạch toán CCDC vào 242, không qua 153. Món nhóm này
   luôn là món mua, không quản kho, và Item Default mỗi công ty có tài khoản
   chi phí là tài khoản số 242 của công ty đó, nên dòng hoá đơn đi 242 và
   không đòi phiếu nhập kho.
2. Ca Kahlua: ánh xạ lập 07/09 khi NVLT00325 còn dùng, 15/09 món bị tắt mà
   hệ không nói gì. Từ nay: tắt món còn ánh xạ trỏ vào thì chặn, và lưu ánh
   xạ mới trỏ món đã tắt thì chặn cả khi ô đơn vị để trống.

Mọi ca chạy HÀM THẬT, chỉ thay lớp dữ liệu. Không dò chuỗi.
"""
import sys
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la


class _Loi(Exception):
	pass


class _Doc(dict):
	def __getattr__(self, k):
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)

	def __setattr__(self, k, v):
		self[k] = v


def _throw(msg, *a, **k):
	raise _Loi(msg)


TK = {"CÔNG TY TNHH PATISSERIE VAGABOND": "242 - Chi phí chờ phân bổ - TV"}
CTY = "CÔNG TY TNHH PATISSERIE VAGABOND"


# ------------------------------------------------------------ phần thuần

@ca("#524 CCDC dùng ngay: món chưa có mặc định công ty thì thêm dòng 242")
def _them():
	from vagabond.ccdc_dung_ngay import dong_can_dat
	la("thêm", dong_can_dat([], TK), [(CTY, TK[CTY], "them")])


@ca("#524 CCDC dùng ngay: mặc định đang trỏ 632 thì sửa về 242, đúng rồi thì thôi")
def _sua():
	from vagabond.ccdc_dung_ngay import dong_can_dat
	la("sửa", dong_can_dat([{"company": CTY, "expense_account": "632 - Giá vốn hàng bán - TV"}], TK),
		[(CTY, TK[CTY], "sua")])
	la("đúng rồi", dong_can_dat([{"company": CTY, "expense_account": TK[CTY]}], TK), [])
	# Công ty không có tài khoản 242 (công ty demo) thì không đặt gì cho nó.
	la("công ty không có 242", dong_can_dat([], {"The Vagabond (Demo)": None}), [])


# ------------------------------------------------------------ hook lưu món

class _Mon(_Doc):
	def __init__(self, truoc=None, **k):
		super().__init__(**k)
		dict.__setitem__(self, "_truoc", truoc)
		dict.__setitem__(self, "item_defaults", [_Doc(d) for d in k.get("item_defaults", [])])

	def is_new(self):
		return self["_truoc"] is None

	def get_doc_before_save(self):
		return self["_truoc"]

	def append(self, bang, dong):
		self[bang].append(_Doc(dong))


def _luu_mon(doc, co_so_kho=False, so_kho=None):
	from vagabond import ccdc_dung_ngay as C

	# Sổ kho giả: danh sách dòng SLE của món. exists lọc THẬT theo điều kiện
	# hàm gửi xuống, để ca Codex #364 v1 (chỉ còn SLE đã huỷ) không bị che.
	if so_kho is None:
		so_kho = [{"is_cancelled": 0}] if co_so_kho else []

	def exists(dt, loc):
		if dt != "Stock Ledger Entry":
			return False
		loc = dict(loc or {})
		loc.pop("item_code", None)
		return any(all(r.get(k) == v for k, v in loc.items()) for r in so_kho)

	cu = C.frappe
	C.frappe = SimpleNamespace(
		throw=_throw,
		get_all=lambda dt, **k: list(TK) + ["The Vagabond (Demo)"],
		db=SimpleNamespace(
			get_value=lambda dt, loc, truong: TK.get(loc.get("company")) if dt == "Account" else None,
			exists=exists,
		),
	)
	try:
		C.khi_luu_mon(doc)
	finally:
		C.frappe = cu
	return doc


@ca("#524 quạt Midea mở mã nhóm CCDC dùng ngay: không quản kho, cho mua, chi phí 242")
def _mon_moi():
	d = _luu_mon(_Mon(name="CCDN00001", item_group="CCDC dùng ngay", is_stock_item=1, is_purchase_item=0,
		is_sales_item=1))
	la("không quản kho", d.is_stock_item, 0)
	la("không bán cho khách (Codex #364 v2)", d.is_sales_item, 0)
	la("cho mua", d.is_purchase_item, 1)
	la("mặc định chi phí 242", [(r.company, r.expense_account) for r in d.item_defaults], [(CTY, TK[CTY])])


@ca("#524 món nhóm khác không bị hook CCDC đụng tới")
def _nhom_khac():
	d = _luu_mon(_Mon(name="CCDC00152", item_group="Công cụ Dụng cụ", is_stock_item=1, is_purchase_item=1))
	la("vẫn quản kho", d.is_stock_item, 1)
	la("không thêm mặc định", d.item_defaults, [])


@ca("#524 món đã có sổ kho chuyển sang nhóm CCDC dùng ngay thì chặn, không lách luật của ERPNext")
def _co_so_kho():
	truoc = _Doc(is_stock_item=1, item_group="Công cụ Dụng cụ")
	try:
		_luu_mon(_Mon(truoc=truoc, name="CCDC00197", item_group="CCDC dùng ngay", is_stock_item=1), co_so_kho=True)
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("bị chặn", "đã có sổ kho" in loi)
	# Chưa từng có sổ kho thì chuyển được.
	d = _luu_mon(_Mon(truoc=truoc, name="CCDC00999", item_group="CCDC dùng ngay", is_stock_item=1), co_so_kho=False)
	la("chưa có sổ kho thì đổi được", d.is_stock_item, 0)


# ------------------------------------------------------------ ánh xạ NCC

class _AnhXa(_Doc):
	def __init__(self, moi=True, doi_mon=False, **k):
		super().__init__(**k)
		dict.__setitem__(self, "_moi", moi)
		dict.__setitem__(self, "_doi", doi_mon)

	def is_new(self):
		return self["_moi"]

	def has_value_changed(self, f):
		return f == "item_code" and self["_doi"]


_MON = {"NVLT00151": {"stock_uom": "ML", "disabled": 0}, "NVLT00325": {"stock_uom": "ML", "disabled": 1}}


def _chay_q(ham, doc, anh_xa=()):
	from vagabond import quy_cach_ncc as Q

	def get_value(dt, ten, truong, as_dict=False):
		m = _MON.get(ten) if dt == "Item" else None
		if m is None:
			return None
		if isinstance(truong, (list, tuple)):
			r = _Doc({k: m.get(k) for k in truong})
			return r if as_dict else [m.get(k) for k in truong]
		return m.get(truong)

	cu = Q.frappe
	Q.frappe = SimpleNamespace(
		throw=_throw,
		db=SimpleNamespace(get_value=get_value, exists=lambda dt, ten=None: True),
		get_all=lambda dt, filters=None, **k: [_Doc(r) for r in anh_xa
			if all(r.get(a) == b for a, b in (filters or {}).items())],
	)
	try:
		getattr(Q, ham)(doc)
		return ""
	except _Loi as e:
		return str(e)
	finally:
		Q.frappe = cu


_KAHLUA = dict(supplier_mst="0315777858", ten_ncc="Rượu Kahlua 70cl", ma_ncc=None)


@ca("#524 lưu ánh xạ MỚI trỏ món đã tắt bị chặn cả khi ô đơn vị để trống")
def _anh_xa_moi_tat():
	loi = _chay_q("kiem", _AnhXa(item_code="NVLT00325", vgb_uom="", **_KAHLUA))
	dung("chặn", "đã tắt" in loi)
	la("món đang dùng thì lưu được", _chay_q("kiem", _AnhXa(item_code="NVLT00151", vgb_uom="", **_KAHLUA)), "")


@ca("#524 đổi ô Món của ánh xạ cũ sang món đã tắt bị chặn")
def _doi_sang_tat():
	loi = _chay_q("kiem", _AnhXa(moi=False, doi_mon=True, item_code="NVLT00325", vgb_uom="", **_KAHLUA))
	dung("chặn", "đã tắt" in loi)


@ca("#524 ánh xạ cũ trỏ món đã tắt TỪ TRƯỚC, lưu lại vì ô khác, không bị chặn thêm ở cửa mới")
def _anh_xa_cu():
	# Bốn ánh xạ cũ trên site (Kahlua và ba dòng CCDC00062). Mọi lối đọc đã bỏ
	# qua chúng từ v523; chặn lưu thì máy học không đổi được món cho chúng.
	la("không chặn", _chay_q("kiem", _AnhXa(moi=False, doi_mon=False, item_code="NVLT00325", vgb_uom="", **_KAHLUA)), "")


class _Item(_Doc):
	def __init__(self, moi=False, doi=True, **k):
		super().__init__(**k)
		dict.__setitem__(self, "_moi", moi)
		dict.__setitem__(self, "_doi", doi)

	def is_new(self):
		return self["_moi"]

	def has_value_changed(self, f):
		return f == "disabled" and self["_doi"]


_BANG = [dict(name="acm2a8618p", item_code="NVLT00325", **_KAHLUA),
	dict(name="x1", item_code="CCDC00062", supplier_mst="0301", ten_ncc="Lifebuoy 4kg", ma_ncc=None)]


@ca("#524 ca Kahlua: tắt món còn ánh xạ trỏ vào thì chặn và kể tên ánh xạ")
def _tat_con_anh_xa():
	loi = _chay_q("chan_tat_mon", _Item(name="NVLT00325", disabled=1), _BANG)
	dung("chặn", "Chưa tắt được món NVLT00325" in loi)
	dung("kể tên dòng ánh xạ", "Rượu Kahlua 70cl (MST 0315777858)" in loi)
	dung("không kể ánh xạ của món khác", "Lifebuoy" not in loi)


@ca("#524 tắt món không còn ánh xạ, món mới, hay lưu món đã tắt sẵn thì không chặn")
def _tat_duoc():
	la("không còn ánh xạ", _chay_q("chan_tat_mon", _Item(name="NVLT00999", disabled=1), _BANG), "")
	la("món mới tạo ở trạng thái tắt", _chay_q("chan_tat_mon", _Item(moi=True, name="NVLT00325", disabled=1), _BANG), "")
	la("đã tắt từ trước, lưu vì ô khác", _chay_q("chan_tat_mon", _Item(doi=False, name="NVLT00325", disabled=1), _BANG), "")
	la("bật lại món", _chay_q("chan_tat_mon", _Item(name="NVLT00325", disabled=0), _BANG), "")


@ca("#524 câu chặn gọn khi món có nhiều ánh xạ")
def _cau_nhieu():
	from vagabond.quy_cach_ncc import cau_chan_tat
	ds = [{"ten_ncc": "Hàng %d" % i, "supplier_mst": "01"} for i in range(8)]
	c = cau_chan_tat("CCDC00062", ds)
	dung("đếm đủ tám", "còn 8 ánh xạ" in c)
	dung("kể năm dòng rồi gộp phần còn lại", "Hàng 4" in c and "Hàng 5" not in c and "và 3 ánh xạ khác" in c)


# ------------------------------------------------------------ mở mã hàng

def _nap_danh_muc():
	# Khung frappe giả của bộ kiểm không có frappe.model.naming; danh_muc chỉ
	# lấy getseries từ đó, mà ca dưới thay luôn _ma_moi, nên đặt mô đun giả.
	if "vagabond.danh_muc" not in sys.modules and "frappe.model.naming" not in sys.modules:
		sys.modules["frappe.model.naming"] = SimpleNamespace(getseries=lambda *a: "00001")
	from vagabond import danh_muc
	return danh_muc


def _tao(nhom, loai, quy_cach=None, goi_trung=None):
	D = _nap_danh_muc()

	tao = []
	goi_trung = goi_trung if goi_trung is not None else []

	def new_doc(dt):
		d = _Doc(doctype=dt, flags=SimpleNamespace(), standard_rate=0)
		d.insert = lambda: (tao.append(dict(d)), dict.__setitem__(d, "name", d["item_code"]))
		return d

	fr = SimpleNamespace(
		throw=_throw, msgprint=lambda *a, **k: None,
		db=SimpleNamespace(
			exists=lambda dt, ten=None: True,
			get_value=lambda dt, ten, truong: 0,
			get_default=lambda k: "",
			commit=lambda: None,
		),
		new_doc=new_doc,
	)
	cu = {k: getattr(D, k) for k in ("frappe", "_kiem_quyen", "_duoc_tao", "tim_trung", "_ma_moi", "_dvt_quen", "tien_to_nhom")}
	try:
		D.frappe = fr
		D._kiem_quyen = lambda: None
		D._duoc_tao = lambda: True
		D.tim_trung = lambda **k: goi_trung.append(k) or []
		D._ma_moi = lambda tt: tt + "00001"
		D._dvt_quen = lambda n: "Cái"
		D.tien_to_nhom = lambda n: ""
		try:
			return D.tao(nhom=nhom, loai=loai, ten="Quạt đứng Midea FS40-24EVN", quy_cach=quy_cach), tao, ""
		except _Loi as e:
			return None, tao, str(e)
	finally:
		for k, v in cu.items():
			setattr(D, k, v)


@ca("#524 mở mã trong nhóm CCDC dùng ngay: máy tự lấy đúng loại và tiền tố CCDN dù người chọn nhầm loại")
def _tao_ccdc():
	ra, tao, loi = _tao("CCDC dùng ngay", "nvl")
	la("không lỗi", loi, "")
	la("mã", ra["ma"], "CCDN00001")
	la("ba cờ mua - bán - tồn", (ra["mua"], ra["ban"], ra["ton"]), (1, 0, 0))


@ca("#524 chọn loại CCDC dùng ngay mà nhóm khác thì báo chọn đúng nhóm, không tạo mã")
def _tao_sai_nhom():
	ra, tao, loi = _tao("Công cụ Dụng cụ", "ccdc_dung_ngay")
	dung("báo", 'chỉ đi với nhóm "CCDC dùng ngay"' in loi)
	la("không tạo", tao, [])


# ----------------------------------------- Codex #364 vòng 1

@ca("#524 Codex #364 v1: món chỉ còn sổ kho ĐÃ HUỶ vẫn không được chuyển sang nhóm CCDC dùng ngay")
def _so_kho_da_huy():
	truoc = _Doc(is_stock_item=1, item_group="Công cụ Dụng cụ")
	try:
		_luu_mon(_Mon(truoc=truoc, name="CCDC00197", item_group="CCDC dùng ngay", is_stock_item=1),
			so_kho=[{"is_cancelled": 1}])
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("bị chặn", "đã có sổ kho" in loi)


@ca("#524 Codex #364 v1: món đang KHÔNG quản kho mà có sổ kho cũ cũng không được chuyển sang nhóm")
def _khong_quan_kho_co_so():
	truoc = _Doc(is_stock_item=0, item_group="Dịch vụ")
	try:
		_luu_mon(_Mon(truoc=truoc, name="DV00001", item_group="CCDC dùng ngay", is_stock_item=0),
			so_kho=[{"is_cancelled": 0}])
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("bị chặn", "đã có sổ kho" in loi)
	# Món đã ở trong nhóm từ trước (không phải lúc chuyển vào), lưu lại vì ô khác: không chặn.
	d = _luu_mon(_Mon(truoc=_Doc(is_stock_item=0, item_group="CCDC dùng ngay"), name="CCDN00001",
		item_group="CCDC dùng ngay", is_stock_item=0), so_kho=[])
	la("lưu lại món trong nhóm", d.is_stock_item, 0)


@ca("#524 Codex #364 v3: soát trùng tên dùng ĐÚNG loại CCDC dùng ngay khi màn còn mang loại khác")
def _trung_theo_loai_chuan():
	goi = []
	ra, tao, loi = _tao("CCDC dùng ngay", "thanh_pham", quy_cach="Trắng", goi_trung=goi)
	la("không lỗi", loi, "")
	la("soát trùng gọi đúng loại của nhóm", [g.get("loai") for g in goi], ["ccdc_dung_ngay"])
	la("tên món không gắn quy cách như hàng bán", tao[0]["item_name"], "Quạt đứng Midea FS40-24EVN")


class _Nhom(_Doc):
	def __init__(self, giu=True, **k):
		super().__init__(**k)
		dict.__setitem__(self, "item_group_defaults", [])
		dict.__setitem__(self, "_giu", giu)
		dict.__setitem__(self, "flags", SimpleNamespace())

	def append(self, bang, dong):
		self[bang].append(_Doc(dong))

	def save(self):
		if not self["_giu"]:
			# Mô phỏng lượt lưu không giữ được dòng mặc định.
			self["item_group_defaults"].clear()

	def insert(self):
		pass


def _chay_dung(giu=True, co_cha=True):
	from vagabond import ccdc_dung_ngay as C

	nhom = _Nhom(giu=giu, name=C.NHOM)
	da_tao = []

	def exists(dt, ten=None):
		if ten in (C.CHA, C.NHOM):
			# Bench dựng mới: chưa có cả nhóm cha lẫn nhóm lá.
			return co_cha or any(d.get("item_group_name") == ten for d in da_tao)
		return True

	def get_doc(dt, ten=None):
		if isinstance(dt, dict):
			d = _Nhom(**dt)
			da_tao.append(dt)
			return d
		return nhom

	cu = C.frappe
	C.frappe = SimpleNamespace(
		throw=_throw, get_doc=get_doc,
		get_all=lambda dt, **k: [CTY],
		db=SimpleNamespace(exists=exists, get_value=lambda dt, loc, truong: TK.get(loc.get("company"))),
	)
	nested = sys.modules.get("frappe.utils.nestedset")
	sys.modules["frappe.utils.nestedset"] = SimpleNamespace(get_root_of=lambda dt: "All Item Groups")
	try:
		try:
			return C.dung(), "", da_tao, nhom
		except _Loi as e:
			return None, str(e), da_tao, nhom
	finally:
		C.frappe = cu
		if nested is None:
			sys.modules.pop("frappe.utils.nestedset", None)
		else:
			sys.modules["frappe.utils.nestedset"] = nested


@ca("#524 Codex #364 v2: dựng nhóm mà mặc định 242 không giữ được thì báo lỗi, không báo xong")
def _dung_khong_giu():
	ra, loi, _, _ = _chay_dung(giu=False)
	dung("báo lỗi", "chưa nhận đủ mặc định 242" in loi)
	ra, loi, _, nhom = _chay_dung(giu=True)
	la("giữ được thì xong", loi, "")
	la("nhóm có mặc định 242", [(d.company, d.expense_account) for d in nhom.item_group_defaults], [(CTY, TK[CTY])])


@ca("#524 Codex #364 v2: chưa có nhóm Mua vào thì dựng nhóm cha, không bỏ qua")
def _dung_thieu_cha():
	from vagabond import ccdc_dung_ngay as C
	ra, loi, da_tao, _ = _chay_dung(co_cha=False)
	la("không lỗi", loi, "")
	la("dựng nhóm cha rồi nhóm lá", [(d["item_group_name"], d["parent_item_group"]) for d in da_tao],
		[(C.CHA, "All Item Groups"), (C.NHOM, C.CHA)])


@ca("#524 Codex #364 v2: patch v524 để lỗi dựng nhóm làm hỏng lượt migrate")
def _patch_nem():
	from vagabond import ccdc_dung_ngay as C
	from vagabond.patches import ccdc_dung_ngay_v524 as P

	cu = C.dung

	def hong():
		raise _Loi("không lưu được nhóm")

	C.dung = hong
	try:
		try:
			P.execute()
			nem = False
		except _Loi:
			nem = True
	finally:
		C.dung = cu
	dung("lỗi đi ra ngoài patch", nem)


# ----------------------------------------- Codex #364 vòng 2

def _xem(nhom, loai, quy_cach=None):
	D = _nap_danh_muc()
	goi = []
	cu = {k: getattr(D, k) for k in ("frappe", "_kiem_quyen", "tim_trung", "_dvt_quen", "tien_to_nhom", "_so_ke_tiep")}
	try:
		D.frappe = SimpleNamespace(throw=_throw)
		D._kiem_quyen = lambda: None
		D.tim_trung = lambda **k: goi.append(k) or []
		D._dvt_quen = lambda n: "Cái"
		D.tien_to_nhom = lambda n: ""
		D._so_ke_tiep = lambda tt: 1
		return D.xem_truoc(nhom=nhom, loai=loai, ten="Quạt đứng Midea FS40-24EVN", quy_cach=quy_cach), goi
	finally:
		for k, v in cu.items():
			setattr(D, k, v)


@ca("#524 Codex #364 v2: xem trước khớp với mã sẽ tạo khi chọn nhóm CCDC dùng ngay mà chip còn Thành phẩm")
def _xem_truoc_khop():
	ra, goi = _xem("CCDC dùng ngay", "thanh_pham", quy_cach="Trắng")
	la("loại thật của nhóm", ra["loai"], "ccdc_dung_ngay")
	la("tên không gắn quy cách như hàng bán", ra["ten_day_du"], "Quạt đứng Midea FS40-24EVN")
	la("mã dự kiến theo tiền tố CCDN", ra["ma_du_kien"], "CCDN00001")
	dung("không báo chưa đoán được tiền tố", not any("tiền tố" in c for c in ra["canh_bao"]))
	la("soát trùng theo loại thật", [g.get("loai") for g in goi], ["ccdc_dung_ngay"])


@ca("#524 Codex #364 v2: xem trước loại CCDC dùng ngay với nhóm khác thì cảnh báo, không nổ")
def _xem_truoc_sai_nhom():
	ra, goi = _xem("Công cụ Dụng cụ", "ccdc_dung_ngay")
	dung("có cảnh báo chọn đúng nhóm", any('chỉ đi với nhóm "CCDC dùng ngay"' in c for c in ra["canh_bao"]))
