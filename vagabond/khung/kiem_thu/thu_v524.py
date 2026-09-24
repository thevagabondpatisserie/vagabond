"""v524, anh Việt chốt 24/09/2026.

1. Tick "Đi 242" trên mã món (v525 thay nhóm "CCDC dùng ngay" của v524, anh
   Việt không cho tạo mã mới). Quạt Uyên mua cho nhân viên (Điện Máy Xanh).
   Chị Dung hạch toán CCDC vào 242. Mã được tick luôn là món mua, không quản
   kho, và Item Default mỗi công ty có tài khoản chi phí là tài khoản số 242,
   nên dòng hoá đơn đi 242 và không đòi phiếu nhập kho. Mã đã có sổ kho thì
   không tick được.
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

@ca("#525 tick Đi 242: món chưa có mặc định công ty thì thêm dòng 242")
def _them():
	from vagabond.ccdc_dung_ngay import dong_can_dat
	la("thêm", dong_can_dat([], TK), [(CTY, TK[CTY], "them")])


@ca("#525 tick Đi 242: mặc định đang trỏ 632 thì sửa về 242, đúng rồi thì thôi")
def _sua():
	from vagabond.ccdc_dung_ngay import dong_can_dat
	la("sửa", dong_can_dat([{"company": CTY, "expense_account": "632 - Giá vốn hàng bán - TV"}], TK),
		[(CTY, TK[CTY], "sua")])
	la("đúng rồi", dong_can_dat([{"company": CTY, "expense_account": TK[CTY]}], TK), [])
	# Công ty không có tài khoản 242 (công ty demo) thì không đặt gì cho nó.
	la("công ty không có 242", dong_can_dat([], {"The Vagabond (Demo)": None}), [])


# ------------------------------------------------------------ hook lưu món (v525)

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

	def set(self, k, v):
		self[k] = v


def _luu_mon(doc, so_kho=None, cong_ty=None):
	"""Chạy khi_luu_mon THẬT. so_kho: các dòng SLE của món; exists lọc thật."""
	from vagabond import ccdc_dung_ngay as C

	so_kho = so_kho or []

	def exists(dt, loc):
		if dt != "Stock Ledger Entry":
			return False
		loc = dict(loc or {})
		loc.pop("item_code", None)
		return any(all(r.get(k) == v for k, v in loc.items()) for r in so_kho)

	cu = C.frappe
	C.frappe = SimpleNamespace(
		throw=_throw,
		get_all=lambda dt, **k: list(cong_ty or (list(TK) + ["The Vagabond (Demo)"])),
		db=SimpleNamespace(
			get_value=lambda dt, loc, truong: TK.get(loc.get("company")) if dt == "Account" else None,
			get_single_value=lambda dt, f: "The Vagabond (Demo)",
			exists=exists,
		),
	)
	try:
		C.khi_luu_mon(doc)
	finally:
		C.frappe = cu
	return doc


@ca("#525 tick Đi 242 trên mã CCDC cũ chưa có sổ kho: không quản kho, cho mua, không bán, chi phí 242")
def _tick_ma_cu():
	truoc = _Doc(custom_di_242=0, is_stock_item=1, item_group="Công cụ Dụng cụ")
	d = _luu_mon(_Mon(truoc=truoc, name="CCDC00152", item_group="Công cụ Dụng cụ", custom_di_242=1,
		is_stock_item=1, is_purchase_item=1, is_sales_item=1, has_batch_no=1, has_serial_no=0))
	la("không quản kho", d.is_stock_item, 0)
	la("cho mua", d.is_purchase_item, 1)
	la("không bán cho khách", d.is_sales_item, 0)
	la("mặc định chi phí 242", [(r.company, r.expense_account) for r in d.item_defaults], [(CTY, TK[CTY])])
	la("bỏ theo lô và sê-ri", (d.has_batch_no, d.has_serial_no), (0, 0))


@ca("#525 mã tick mà có gõ tồn đầu kỳ thì báo, không để số tồn mất im lặng")
def _ton_dau_ky():
	try:
		_luu_mon(_Mon(name="CCDC00301", item_group="Công cụ Dụng cụ", custom_di_242=0,
			is_stock_item=1, opening_stock=5))
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("báo bỏ tồn đầu kỳ", "Tồn đầu kỳ" in loi)
	d = _luu_mon(_Mon(name="CCDC00302", item_group="Công cụ Dụng cụ", custom_di_242=0,
		is_stock_item=1, opening_stock=0))
	la("không gõ tồn thì tạo bình thường", d.is_stock_item, 0)


@ca("#525 mã mới mở trong nhóm CCDC tự được tick sẵn, không cần mã CCDN")
def _ma_moi_tick_san():
	d = _luu_mon(_Mon(name="CCDC00300", item_group="Công cụ Dụng cụ", custom_di_242=0,
		is_stock_item=1, is_purchase_item=1))
	la("đã tick", d.custom_di_242, 1)
	la("không quản kho", d.is_stock_item, 0)
	d2 = _luu_mon(_Mon(name="CCDS00001", item_group="Công cụ dụng cụ Sonneto", custom_di_242=0, is_stock_item=1))
	la("nhóm CCDC Sonneto cũng tick sẵn", d2.custom_di_242, 1)


@ca("#525 món nhóm khác không tick thì hook không đụng tới")
def _nhom_khac():
	d = _luu_mon(_Mon(name="NVLT00151", item_group="Nguyên vật liệu Thô", custom_di_242=0, is_stock_item=1))
	la("vẫn quản kho", d.is_stock_item, 1)
	la("không thêm mặc định", d.item_defaults, [])
	d2 = _luu_mon(_Mon(truoc=_Doc(custom_di_242=0, is_stock_item=1), name="CCDC00010",
		item_group="Công cụ Dụng cụ", custom_di_242=0, is_stock_item=1), so_kho=[{"is_cancelled": 0}])
	la("mã CCDC cũ có sổ kho không tick thì lưu bình thường", d2.is_stock_item, 1)


@ca("#525 tick mã đã có sổ kho (kể cả chỉ còn dòng ĐÃ HUỶ) thì chặn, không lách luật của ERPNext")
def _tick_co_so_kho():
	for so in ([{"is_cancelled": 0}], [{"is_cancelled": 1}]):
		try:
			_luu_mon(_Mon(truoc=_Doc(custom_di_242=0, is_stock_item=1), name="CCDC00197",
				item_group="Công cụ Dụng cụ", custom_di_242=1, is_stock_item=1), so_kho=so)
			loi = ""
		except _Loi as e:
			loi = str(e)
		dung("bị chặn khi sổ kho %s" % so, "đã có sổ kho" in loi)
	# Món đang không quản kho mà từng có sổ kho cũng không tick được.
	try:
		_luu_mon(_Mon(truoc=_Doc(custom_di_242=0, is_stock_item=0), name="DV00001",
			item_group="Dịch vụ", custom_di_242=1, is_stock_item=0), so_kho=[{"is_cancelled": 0}])
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("món không quản kho có sổ cũ cũng bị chặn", "đã có sổ kho" in loi)


@ca("#525 bỏ tick thì gỡ 242 khỏi mặc định, không tự bật lại quản kho")
def _bo_tick():
	d = _luu_mon(_Mon(truoc=_Doc(custom_di_242=1, is_stock_item=0), name="CCDC00152",
		item_group="Công cụ Dụng cụ", custom_di_242=0, is_stock_item=0,
		item_defaults=[{"company": CTY, "expense_account": TK[CTY], "default_warehouse": "Kho tổng 307 - TV"}]))
	la("gỡ 242", [r.expense_account for r in d.item_defaults], [None])
	la("giữ kho mặc định", [r.default_warehouse for r in d.item_defaults], ["Kho tổng 307 - TV"])
	la("không tự bật quản kho", d.is_stock_item, 0)


@ca("#525 phép quyết định thuần: tick, gỡ, chặn, không làm gì")
def _viec_thuan():
	from vagabond.ccdc_dung_ngay import viec_khi_luu as v
	la("tick", v(False, 1, 0, "Công cụ Dụng cụ", False), "tick")
	la("chặn", v(False, 1, 0, "Công cụ Dụng cụ", True), "chan")
	la("gỡ", v(False, 0, 1, "Công cụ Dụng cụ", False), "go")
	la("không làm gì", v(False, 0, 0, "Công cụ Dụng cụ", False), "")
	la("mới trong nhóm CCDC", v(True, 0, 0, "Công cụ Dụng cụ", False), "tick")
	la("mới nhóm khác", v(True, 0, 0, "Bao bì", False), "")

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



# ------------------------------------------------------------ patch v525

@ca("#525 patch v525 để lỗi làm hỏng lượt migrate, không nuốt (Codex #364 v2)")
def _patch_nem():
	from vagabond import ccdc_dung_ngay as C
	from vagabond.patches import ccdc_tick_242_v525 as P

	cu = C.dung

	def hong():
		raise _Loi("không lưu được")

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


def _chay_tick(mon, so_kho, giu=True, cong_ty=None):
	"""Chạy tick_ma_cu THẬT với danh mục giả. mon: {mã: {item_group, disabled, custom_di_242}}."""
	from vagabond import ccdc_dung_ngay as C

	item_def = {}
	ghi = []

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Company":
			return list(cong_ty or [CTY, "The Vagabond (Demo)"])
		if dt == "Item":
			nhom = filters["item_group"][1]
			return [_Doc(name=m, custom_di_242=r.get("custom_di_242", 0)) for m, r in mon.items()
				if r["item_group"] in nhom and not r.get("disabled")]
		if dt == "Item Default":
			return [_Doc(d) for d in item_def.get(filters["parent"], [])]
		return []

	def set_value(dt, ten, truong, gt=None, update_modified=True):
		if dt == "Item" and giu:
			mon[ten].update(truong)
		ghi.append((dt, ten))

	class _Dong(_Doc):
		def db_insert(self):
			if giu:
				item_def.setdefault(self["parent"], []).append(dict(self))

	def get_value(dt, ten, truong):
		if dt == "Account":
			return TK.get(ten.get("company"))
		return mon[ten].get(truong)

	cu = C.frappe
	C.frappe = SimpleNamespace(
		throw=_throw, get_all=get_all, new_doc=lambda dt: _Dong(), clear_cache=lambda **k: None,
		db=SimpleNamespace(set_value=set_value, get_value=get_value,
			get_single_value=lambda dt, f: "The Vagabond (Demo)",
			exists=lambda dt, loc: dt == "Stock Ledger Entry" and loc.get("item_code") in so_kho),
	)
	try:
		try:
			return C.tick_ma_cu(), "", mon, item_def
		except _Loi as e:
			return None, str(e), mon, item_def
	finally:
		C.frappe = cu


@ca("#525 patch tick sẵn mã CCDC chưa có sổ kho, bỏ qua mã có sổ kho, mã đã tắt và nhóm khác")
def _tick_hang_loat():
	mon = {
		"CCDC00152": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1},
		"CCDC00197": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1},
		"CCDS00001": {"item_group": "Công cụ dụng cụ Sonneto", "is_stock_item": 1},
		"CCDC00062": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1, "disabled": 1},
		"NVLT00151": {"item_group": "Nguyên vật liệu Thô", "is_stock_item": 1},
	}
	kq, loi, mon, item_def = _chay_tick(mon, so_kho={"CCDC00197"})
	la("không lỗi", loi, "")
	la("tick đúng mã chưa có sổ kho", sorted(kq["ma"]), ["CCDC00152", "CCDS00001"])
	la("mã có sổ kho giữ quản kho", mon["CCDC00197"]["is_stock_item"], 1)
	la("mã tick thành không quản kho", (mon["CCDC00152"]["is_stock_item"], mon["CCDC00152"]["custom_di_242"]), (0, 1))
	la("mặc định 242 đã ghi", [(d["company"], d["expense_account"]) for d in item_def["CCDC00152"]], [(CTY, TK[CTY])])
	la("mã tắt không đụng", mon["CCDC00062"].get("custom_di_242", 0), 0)
	la("patch bỏ theo lô", mon["CCDC00152"].get("has_batch_no"), 0)


@ca("#525 patch tick mà ghi không giữ được thì báo lỗi, không báo xong")
def _tick_khong_giu():
	mon = {"CCDC00152": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1}}
	kq, loi, _, _ = _chay_tick(mon, so_kho=set(), giu=False)
	dung("báo lỗi", "chưa đủ" in loi)


def _xem(nhom):
	if "vagabond.danh_muc" not in sys.modules and "frappe.model.naming" not in sys.modules:
		sys.modules["frappe.model.naming"] = SimpleNamespace(getseries=lambda *a: "00001")
	from vagabond import danh_muc as D
	cu = {k: getattr(D, k) for k in ("_kiem_quyen", "tim_trung", "_dvt_quen", "tien_to_nhom", "_so_ke_tiep")}
	try:
		D._kiem_quyen = lambda: None
		D.tim_trung = lambda **k: []
		D._dvt_quen = lambda n: "Cái"
		D.tien_to_nhom = lambda n: "CCDC"
		D._so_ke_tiep = lambda tt: 300
		return D.xem_truoc(nhom=nhom, loai="nvl", ten="Quạt đứng Midea FS40-24EVN")
	finally:
		for k, v in cu.items():
			setattr(D, k, v)


@ca("#525 màn Mở mã hàng nói trước: mã mới nhóm CCDC tự tick Đi 242, vẫn dùng tiền tố CCDC")
def _xem_ccdc():
	ra = _xem("Công cụ Dụng cụ")
	dung("có câu tick Đi 242", any("Đi 242" in c for c in ra["canh_bao"]))
	la("mã dự kiến theo tiền tố cũ", ra["ma_du_kien"], "CCDC00300")
	ra2 = _xem("Bao bì")
	dung("nhóm khác không có câu này", not any("Đi 242" in c for c in ra2["canh_bao"]))


# ----------------------------------------- Codex #365 vòng 1

@ca("#525 Codex #365 v1: một công ty thật thiếu TK 242 thì patch dừng TRƯỚC khi đổi mã nào")
def _thieu_242_patch():
	mon = {"CCDC00152": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1}}
	kq, loi, mon, item_def = _chay_tick(mon, so_kho=set(), cong_ty=[CTY, "Công ty B", "The Vagabond (Demo)"])
	dung("báo thiếu 242 của Công ty B", "Công ty B" in loi)
	la("chưa đổi mã nào", (mon["CCDC00152"]["is_stock_item"], mon["CCDC00152"].get("custom_di_242", 0)), (1, 0))
	la("chưa ghi mặc định nào", item_def, {})
	# Công ty demo (Global Defaults.demo_company) không cần 242: ca thường vẫn chạy.
	kq, loi, _, _ = _chay_tick({"CCDC00152": {"item_group": "Công cụ Dụng cụ", "is_stock_item": 1}}, so_kho=set())
	la("chỉ thiếu ở công ty demo thì không chặn", loi, "")


@ca("#525 Codex #365 v1: tick trên hồ sơ món mà một công ty thật thiếu TK 242 thì chặn, không đổi cờ")
def _thieu_242_hook():
	d = _Mon(truoc=_Doc(custom_di_242=0, is_stock_item=1), name="CCDC00152",
		item_group="Công cụ Dụng cụ", custom_di_242=1, is_stock_item=1)
	try:
		_luu_mon(d, cong_ty=[CTY, "Công ty B"])
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("báo thiếu 242", "Công ty B" in loi)
	la("cờ quản kho giữ nguyên", d.is_stock_item, 1)


@ca("#525 Codex #365 v1: bỏ tick vẫn làm được dù một công ty thật thiếu TK 242")
def _bo_tick_thieu_242():
	d = _luu_mon(_Mon(truoc=_Doc(custom_di_242=1, is_stock_item=0), name="CCDC00152",
		item_group="Công cụ Dụng cụ", custom_di_242=0, is_stock_item=0,
		item_defaults=[{"company": CTY, "expense_account": TK[CTY]}]), cong_ty=[CTY, "Công ty B"])
	la("gỡ 242", [r.expense_account for r in d.item_defaults], [None])


# ----------------------------------------- Codex #365 vòng 3

def _chay_dung(nhom_co=True, mon_trong_nhom=()):
	"""Chạy dung() THẬT (patch v525) trên site đã nhận v524: nhóm "CCDC dùng
	ngay" còn đó, 0 món. Ghi lại mọi lời gọi xoá."""
	from vagabond import ccdc_dung_ngay as C

	xoa, nhom = [], {C.NHOM_V524} if nhom_co else set()

	def exists(dt, loc=None):
		if dt == "Item Group":
			return loc in nhom
		if dt == "Item" and isinstance(loc, dict) and "item_group" in loc:
			return bool(mon_trong_nhom)
		return False

	def delete_doc(dt, ten, **k):
		xoa.append((dt, ten))
		if dt == "Item Group":
			nhom.discard(ten)

	cu, cu_ccf = C.frappe, sys.modules.get("frappe.custom.doctype.custom_field.custom_field")
	sys.modules["frappe.custom.doctype.custom_field.custom_field"] = SimpleNamespace(
		create_custom_fields=lambda *a, **k: None)
	C.frappe = SimpleNamespace(
		throw=_throw, clear_cache=lambda **k: None, delete_doc=delete_doc,
		get_all=lambda dt, **k: [CTY] if dt == "Company" else [],
		db=SimpleNamespace(updatedb=lambda dt: None, exists=exists,
			get_value=lambda dt, loc, truong: TK.get(loc.get("company")) if dt == "Account" else None,
			get_single_value=lambda dt, f: "The Vagabond (Demo)"),
	)
	try:
		return C.dung(), xoa, nhom
	finally:
		C.frappe = cu
		if cu_ccf is None:
			sys.modules.pop("frappe.custom.doctype.custom_field.custom_field", None)
		else:
			sys.modules["frappe.custom.doctype.custom_field.custom_field"] = cu_ccf


@ca("#525 Codex #365 v3: patch KHÔNG xoá nhóm CCDC dùng ngay của v524, kể cả khi nhóm rỗng (QT-20)")
def _giu_nhom_v524():
	from vagabond import ccdc_dung_ngay as C
	kq, xoa, nhom = _chay_dung()
	la("không gọi xoá gì", xoa, [])
	dung("nhóm v524 còn nguyên", C.NHOM_V524 in nhom)
	la("patch vẫn tick như thường", kq["tick"], 0)


@ca("#525 Codex #365 v3: nhóm v524 ngừng dùng: mở món mới hay đổi món sang nhóm đó thì chặn")
def _chan_vao_nhom_v524():
	from vagabond import ccdc_dung_ngay as C

	def luu(d):
		try:
			_luu_mon(d)
			return ""
		except _Loi as e:
			return str(e)

	loi = luu(_Mon(name="CCDN00001", item_group=C.NHOM_V524, is_stock_item=0))
	dung("mở mới trong nhóm ngừng bị chặn", "ngừng dùng" in loi)
	dung("câu chặn chỉ nhóm thay thế", C.NHOM_CCDC[0] in loi)
	loi = luu(_Mon(truoc=_Doc(item_group="Bao bì"), name="BB00010", item_group=C.NHOM_V524, is_stock_item=1))
	dung("đổi nhóm sang nhóm ngừng bị chặn", "ngừng dùng" in loi)
	# Món đã nằm sẵn trong nhóm (site 24/09 không có món nào, nhưng giữ đường
	# lưu lại cho chắc) thì lưu vì ô khác không bị chặn.
	la("món có sẵn trong nhóm lưu lại được",
		luu(_Mon(truoc=_Doc(item_group=C.NHOM_V524), name="X1", item_group=C.NHOM_V524, is_stock_item=0)), "")
	la("nhóm CCDC thường vẫn mở mới được", luu(_Mon(name="CCDC00300", item_group="Công cụ Dụng cụ")), "")


@ca("#525 Codex #365 v3: phép thuần vào nhóm ngừng")
def _vao_nhom_thuan():
	from vagabond.ccdc_dung_ngay import vao_nhom_ngung, NHOM_V524
	la("mở mới", vao_nhom_ngung(True, NHOM_V524, None), True)
	la("đổi sang", vao_nhom_ngung(False, NHOM_V524, "Bao bì"), True)
	la("đã ở sẵn", vao_nhom_ngung(False, NHOM_V524, NHOM_V524), False)
	la("nhóm khác", vao_nhom_ngung(True, "Công cụ Dụng cụ", None), False)
	la("rời nhóm ngừng", vao_nhom_ngung(False, "Công cụ Dụng cụ", NHOM_V524), False)


@ca("#525 Codex #365 v3: màn Mở mã hàng không bày nhóm v524 đã ngừng, các nhóm khác vẫn đủ")
def _an_nhom_v524():
	if "vagabond.danh_muc" not in sys.modules and "frappe.model.naming" not in sys.modules:
		sys.modules["frappe.model.naming"] = SimpleNamespace(getseries=lambda *a: "00001")
	from vagabond import danh_muc as D
	from vagabond.ccdc_dung_ngay import NHOM_V524
	cu = {k: getattr(D, k) for k in ("_kiem_quyen", "_duoc_tao", "_co_truong", "frappe")}
	try:
		D._kiem_quyen = lambda: None
		D._duoc_tao = lambda: True
		D._co_truong = lambda *a: True
		D.frappe = SimpleNamespace(get_all=lambda dt, **k: [
			{"name": "Bao bì"}, {"name": NHOM_V524}, {"name": "Công cụ Dụng cụ"}])
		ra = D.cai_dat()
	finally:
		for k, v in cu.items():
			setattr(D, k, v)
	la("nhóm bày ra", [n["ten"] for n in ra["nhom"]], ["Bao bì", "Công cụ Dụng cụ"])
