"""Ba lỗi anh Việt báo 23/09/2026, gộp vào v523.

1. HT-2026-02900: tiền đã ra và đã khớp sao kê từ 21/09, tờ trả hàng hỏng
   (lỗi chiết khấu đã sửa ở v518), nhưng hồ sơ KHÔNG có lối nào sinh lại.
   Câu lỗi bảo "bấm lại nút Đối soát lệnh chi", mà nút đó chỉ quét hồ sơ
   CHƯA đối soát và còn thoát sớm khi không có hồ sơ nào chờ. Màn chi tiết
   thì ghi "bước còn lại là đính uỷ nhiệm chi" trong khi chưa có phiếu chi
   nào để đính, nên nút Đính uỷ nhiệm chi cũng biến mất.
2. Uyên, hoá đơn Con Rồng: ánh xạ "Rượu Kahlua 70cl" còn trỏ vào NVLT00325
   (mã trùng đã tắt, đơn vị "Chai 700 ml"). Dòng chọn đúng NVLT00151 thì nút
   Nối phiếu nhập kho chặn "Ánh xạ quy cách NCC ... đang chọn Món NVLT00325",
   sửa ánh xạ sang NVLT00151 thì bị chặn vì "Chai 700 ml" không có trên món
   mới, và phép học mã hàng không bao giờ ghi đè ánh xạ đã có món.

Mọi ca dưới đây chạy HÀM THẬT, chỉ thay lớp dữ liệu. Không dò chuỗi.
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


def _khop_loc(dong, loc):
	for k, v in (loc or {}).items():
		gt = dong.get(k)
		if isinstance(v, list) and len(v) == 2 and v[0] == "!=":
			if (gt or "") == v[1]:
				return False
		elif gt != v:
			return False
	return True


class _Db:
	def __init__(self, bang):
		self.bang = bang
		self.commit_n = 0
		self.rollback_n = 0

	def set_value(self, dt, ten, truong, gt=None):
		thay = truong if isinstance(truong, dict) else {truong: gt}
		self.bang[dt][ten].update(thay)

	def get_value(self, dt, ten, truong, as_dict=False, for_update=False):
		# frappe.db.get_value thật nhận for_update (SELECT ... FOR UPDATE).
		d = self.bang.get(dt, {}).get(ten)
		if d is None:
			return None
		if isinstance(truong, (list, tuple)):
			r = _Doc({k: d.get(k) for k in truong})
			return r if as_dict else [d.get(k) for k in truong]
		return d.get(truong)

	def exists(self, dt, ten):
		return ten in self.bang.get(dt, {})

	def commit(self):
		self.commit_n += 1

	def rollback(self):
		self.rollback_n += 1


def _frappe_gia(bang, loi_log):
	db = _Db(bang)

	def throw(msg, *a, **k):
		raise _Loi(msg)

	def get_all(dt, filters=None, fields=None, limit_page_length=0, **k):
		return [_Doc(dict(d, name=t)) for t, d in bang.get(dt, {}).items() if _khop_loc(dict(d, name=t), filters)]

	return SimpleNamespace(
		db=db, throw=throw, get_all=get_all,
		get_doc=lambda dt, ten: _Doc(dict(bang[dt][ten], name=ten)),
		log_error=lambda *a, **k: loi_log.append(a),
		get_traceback=lambda: "Traceback (most recent call last):\nValidationError: CK vượt tổng",
		get_meta=lambda dt: SimpleNamespace(has_field=lambda f: True),
	)


# ------------------------------------------------------------ HT-2026-02900

DT = "Vagabond Hoan Tien"


def _ho(**k):
	d = dict(da_doi_soat=1, ma_gd="ACC-BTN-2026-05949", trang_thai="Da doi soat",
		hoa_don_tra="", phieu_chi="", loi_sinh_ct="Tiền đã ra ... Số tiền CK bổ sung")
	d.update(k)
	return d


def _chay_ht(bang, sinh_duoc=True, khop=None, goi="doi_soat", ho_so=None):
	"""Chạy doi_soat / sinh_lai THẬT của hoan_tien. Chỉ thay: dữ liệu, vòng
	khớp sao kê (đã có ca riêng), và ruột lập chứng từ (đã có ca v518)."""
	from vagabond import hoan_tien as H

	# Không nạp mô đun ban_hang thật: tệp đó kéo requests ở đầu, máy CI
	# không có (điều 5). sinh_lai/doi_soat chỉ lấy _kiem_quyen từ đó, nên
	# đặt tạm một mô đun giả vào sys.modules rồi trả lại.
	B = SimpleNamespace(_kiem_quyen=lambda *a, **k: None)
	cu_mod = sys.modules.get("vagabond.ban_hang")

	loi_log, da_goi = [], []
	fr = _frappe_gia(bang, loi_log)

	def sinh(ho):
		da_goi.append(ho.name)
		if not sinh_duoc:
			raise _Loi("CK vượt tổng")
		bang[DT][ho.name]["hoa_don_tra"] = "HDB-TRA-1"
		bang[DT][ho.name]["phieu_chi"] = "APP-1"
		return {"bo_qua": 0, "hoa_don_tra": "HDB-TRA-1", "phieu_chi": "APP-1"}

	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu", "_doi_soat_khop", "_duoc_tu_choi")}
	try:
		sys.modules["vagabond.ban_hang"] = B
		H.frappe = fr
		H._sinh_chung_tu = sinh
		H._doi_soat_khop = khop or (lambda ho_so=None, so_ngay=30: {
			"da_khop": 0, "xem_xet": [], "ghi_chu": "Không có phiếu nào chờ đối soát."})
		H._duoc_tu_choi = lambda nguoi=None: True
		if goi == "sinh_lai":
			kq = H.sinh_lai(ho_so)
		else:
			kq = H.doi_soat(ho_so)
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
		if cu_mod is None:
			sys.modules.pop("vagabond.ban_hang", None)
		else:
			sys.modules["vagabond.ban_hang"] = cu_mod
	return kq, da_goi, fr, loi_log


@ca("#523 hồ sơ kẹt: điều kiện được sinh lại chứng từ")
def _ket():
	from vagabond.hoan_tien import ket_chung_tu
	dung("đã khớp, chưa chứng từ: kẹt", ket_chung_tu(_ho()))
	dung("chưa khớp tiền ra: không", not ket_chung_tu(_ho(da_doi_soat=0)))
	dung("không có mã giao dịch: không", not ket_chung_tu(_ho(ma_gd="")))
	dung("đã huỷ: không", not ket_chung_tu(_ho(trang_thai="Da huy")))
	dung("đã có hoá đơn trả: không", not ket_chung_tu(_ho(hoa_don_tra="HDB-1")))
	# Nhánh tiền nộp thừa không có hoá đơn trả để tự chặn: có phiếu chi rồi
	# mà sinh nữa là chi hai lần trên sổ.
	dung("đã có phiếu chi: không", not ket_chung_tu(_ho(phieu_chi="APP-1")))


@ca("#523 HT-2026-02900: bấm Đối soát lệnh chi khi không còn phiếu nào chờ vẫn gỡ hồ sơ kẹt")
def _go_khi_thoat_som():
	# Đúng chuỗi của kế toán: màn danh sách, bấm nút, không truyền hồ sơ.
	# Vòng khớp thoát sớm "Không có phiếu nào chờ đối soát". Trước v523 lượt
	# bấm dừng ở đó và HT-2026-02900 nằm nguyên.
	bang = {DT: {"HT-2026-02900": _ho()}}
	kq, goi, fr, _l = _chay_ht(bang)
	la("đã chạy lại bước sinh chứng từ", goi, ["HT-2026-02900"])
	la("xoá câu lỗi trên phiếu", bang[DT]["HT-2026-02900"]["loi_sinh_ct"], "")
	la("báo lại đã sinh", [x["ho_so"] for x in kq.get("da_sinh") or []], ["HT-2026-02900"])


@ca("#523 gỡ hồ sơ kẹt: không đụng hồ sơ đã có chứng từ, đã huỷ, hay chưa từng lỗi")
def _khong_dung_nham():
	bang = {DT: {
		"HT-CO-PC": _ho(phieu_chi="APP-9"),
		"HT-HUY": _ho(trang_thai="Da huy"),
		"HT-CHUA-LOI": _ho(loi_sinh_ct=""),
		"HT-CHUA-KHOP": _ho(da_doi_soat=0),
	}}
	_kq, goi, _f, _l = _chay_ht(bang)
	la("không sinh cho hồ sơ nào", goi, [])


@ca("#523 hồ sơ vừa thử trong vòng khớp thì không thử lần hai trong cùng một lượt")
def _khong_thu_hai_lan():
	bang = {DT: {"HT-A": _ho()}}

	def khop(ho_so=None, so_ngay=30):
		return {"da_khop": 1, "xem_xet": [], "da_sinh": [], "_da_thu": ["HT-A"]}

	kq, goi, _f, _l = _chay_ht(bang, khop=khop)
	la("không gọi lại", goi, [])
	dung("không lộ khoá nội bộ ra màn", "_da_thu" not in kq)


@ca("#523 sinh lại vẫn hỏng: ghi lỗi lên phiếu, câu lỗi chỉ đúng nút có thật")
def _hong_lai():
	bang = {DT: {"HT-2026-02900": _ho(loi_sinh_ct="cũ")}}
	_kq, goi, fr, log = _chay_ht(bang, sinh_duoc=False)
	la("có thử", goi, ["HT-2026-02900"])
	loi = bang[DT]["HT-2026-02900"]["loi_sinh_ct"]
	dung("chỉ nút Sinh lại chứng từ", "Sinh lại chứng từ" in loi)
	dung("không còn chỉ nút Đối soát lệnh chi", "Đối soát lệnh chi" not in loi)
	dung("lùi giao dịch dở", fr.db.rollback_n >= 1)
	la("ghi một dòng Error Log", len(log), 1)


@ca("#523 nút Sinh lại chứng từ: chạy đúng hồ sơ kẹt, từ chối hồ sơ đã có chứng từ")
def _nut():
	bang = {DT: {"HT-2026-02900": _ho(), "HT-XONG": _ho(phieu_chi="APP-2")}}
	kq, goi, _f, _l = _chay_ht(bang, goi="sinh_lai", ho_so="HT-2026-02900")
	la("sinh được", (kq.get("ok"), kq.get("phieu_chi")), (1, "APP-1"))
	# Vòng 3 Codex #363 đổi hợp đồng: hồ sơ đã có phiếu chi không ném lỗi
	# mà báo "đã xong từ trước", và TUYỆT ĐỐI không lập thêm.
	kq, goi, _f, _l = _chay_ht(bang, goi="sinh_lai", ho_so="HT-XONG")
	la("hồ sơ đã có phiếu chi: không lập thêm", goi, [])
	la("báo đã xong từ trước", (kq.get("ok"), kq.get("da_xong_truoc"), kq.get("phieu_chi")), (1, 1, "APP-2"))


# ------------------------------------------------------ ánh xạ Kahlua đã tắt

def _chay_qc(ham, anh_xa, mon, *a):
	"""Chạy hàm THẬT của quy_cach_ncc với danh mục Món và bảng ánh xạ giả."""
	from vagabond import quy_cach_ncc as Q

	uom = {"NVLT00151": [("ML", 1), ("Chai", 700), ("Gram", 1)],
		"NVLT00325": [("ML", 1), ("Chai", 1000), ("Chai 700 ml", 700)]}

	def get_value(dt, ten, truong, as_dict=False):
		if dt == "Item":
			m = mon.get(ten)
			if m is None:
				return None
			if isinstance(truong, (list, tuple)):
				r = _Doc({k: m.get(k) for k in truong})
				return r if as_dict else [m.get(k) for k in truong]
			return m.get(truong)
		return None

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "UOM Conversion Detail":
			ra = [_Doc(uom=u, conversion_factor=h) for u, h in uom.get(filters.get("parent"), [])]
			if "uom" in filters:
				ra = [r for r in ra if r.uom == filters["uom"]]
			return ra
		return []

	def throw(msg, *a, **k):
		raise _Loi(msg)

	fr = SimpleNamespace(
		db=SimpleNamespace(get_value=get_value, exists=lambda dt, t: True),
		get_all=get_all, throw=throw,
		get_meta=lambda dt: SimpleNamespace(has_field=lambda f: True),
	)
	cu = (Q.frappe, Q._anh_xa)
	try:
		Q.frappe = fr
		Q._anh_xa = lambda mst, truong, gia_tri: [_Doc(r) for r in anh_xa if r.get(truong) == gia_tri]
		return getattr(Q, ham)(*a)
	finally:
		Q.frappe, Q._anh_xa = cu


_MON = {
	"NVLT00151": {"stock_uom": "ML", "disabled": 0},
	"NVLT00325": {"stock_uom": "ML", "disabled": 1},
	"NVLT00150": {"stock_uom": "ML", "disabled": 0},
}
_MAP_TAT = [{"ten_ncc": "Rượu Kahlua 70cl", "ma_ncc": None, "item_code": "NVLT00325",
	"vgb_uom": "Chai 700 ml", "supplier_mst": "0315777858"}]


@ca("#523 Kahlua: ánh xạ trỏ Món đã tắt không chặn nút Nối phiếu nhập kho khi dòng chọn đúng món")
def _lay_mon_tat():
	# Ca thật hoá đơn Con Rồng 23/09: dòng NVLT00151, ánh xạ NVLT00325 đã tắt.
	ra = _chay_qc("lay", _MAP_TAT, _MON, "NVLT00151", "0315777858", "Rượu Kahlua 70cl")
	la("không lấy quy cách của món đã tắt", ra, None)
	# Ánh xạ trỏ vào món KHÁC đang dùng thì vẫn chặn như cũ: đó là bất đồng
	# thật giữa hai lựa chọn còn sống, người phải xem.
	song = [dict(_MAP_TAT[0], item_code="NVLT00150", vgb_uom="Chai")]
	try:
		_chay_qc("lay", song, _MON, "NVLT00151", "0315777858", "Rượu Kahlua 70cl")
		chan = False
	except _Loi:
		chan = True
	dung("món khác còn dùng thì vẫn chặn", chan)


@ca("#523 Kahlua: gợi ý Món cho hoá đơn mới bỏ qua ánh xạ trỏ Món đã tắt")
def _tim_mon_tat():
	la("không gợi ý món đã tắt",
		_chay_qc("tim_mon", _MAP_TAT, _MON, "0315777858", None, "Rượu Kahlua 70cl"), None)
	hai = _MAP_TAT + [dict(_MAP_TAT[0], item_code="NVLT00151", vgb_uom="Chai")]
	la("còn một món sống thì gợi ý món đó, không báo nhiều món",
		_chay_qc("tim_mon", hai, _MON, "0315777858", None, "Rượu Kahlua 70cl"), "NVLT00151")


@ca("#523 Kahlua: sửa ánh xạ sang món mới mà đơn vị cũ không có thì câu lỗi bày đơn vị đúng")
def _kiem_uom_ro():
	try:
		_chay_qc("_kiem_uom", [], _MON, "NVLT00151", "Chai 700 ml")
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("nêu đúng đơn vị sai", '"Chai 700 ml"' in loi)
	dung("bày đơn vị của món mới", "ML" in loi and "Chai" in loi and "Gram" in loi)
	dung("chỉ đúng ô phải sửa", "Đơn vị đã đối chiếu" in loi)
	la("đơn vị đúng thì qua", _chay_qc("_kiem_uom", [], _MON, "NVLT00151", "Chai"), None)


def _chay_hoc(anh_xa, mon):
	"""Chạy hoc_ma_hang THẬT với một tờ hoá đơn một dòng Kahlua."""
	from vagabond import dung_lai_hddt as D

	bang = {"MInvoice NCC Map": {t: dict(r) for t, r in anh_xa.items()}}
	them = []

	def get_value(dt, ten, truong, as_dict=False):
		if dt == "Item":
			return (mon.get(ten) or {}).get(truong)
		if isinstance(ten, dict):
			for t, r in bang[dt].items():
				if all(r.get(k) == v for k, v in ten.items()):
					return t
			return None
		return bang[dt][ten].get(truong)

	def set_value(dt, ten, truong, gt=None):
		bang[dt][ten].update(truong if isinstance(truong, dict) else {truong: gt})

	class _Moi(dict):
		flags = SimpleNamespace()

		def insert(self, **k):
			them.append(dict(self))

	fr = SimpleNamespace(
		db=SimpleNamespace(get_value=get_value, set_value=set_value),
		get_doc=lambda d: _Moi(d),
		get_meta=lambda dt: SimpleNamespace(has_field=lambda f: True),
	)
	cu = D.frappe
	try:
		D.frappe = fr
		doc = {"items": [{"item_code": "NVLT00151", "ten_hang_ncc": "Rượu Kahlua 70cl"}]}
		g = {"mst_doi_tac": "0315777858", "chi_tiet": [{"ten": "Rượu Kahlua 70cl", "tchat": "1"}]}
		n = D.hoc_ma_hang(doc, g)
	finally:
		D.frappe = cu
	return n, bang["MInvoice NCC Map"], them


@ca("#523 học mã hàng: ánh xạ trỏ Món đã tắt thì học món người vừa chốt, bỏ đơn vị của món cũ")
def _hoc():
	goc = {"acm2a8618p": dict(_MAP_TAT[0])}
	n, bang, them = _chay_hoc(goc, _MON)
	la("học một dòng", n, 1)
	la("ánh xạ đổi sang món đang dùng", bang["acm2a8618p"]["item_code"], "NVLT00151")
	la("bỏ đơn vị của món cũ", bang["acm2a8618p"]["vgb_uom"], None)
	# Ánh xạ trỏ món CÒN DÙNG thì giữ nguyên như cũ: không bao giờ đè lên
	# lựa chọn còn sống của người khác (điều 11 trong ghi chú hoc_ma_hang).
	song = {"x": dict(_MAP_TAT[0], item_code="NVLT00150", vgb_uom="Chai")}
	n, bang, them = _chay_hoc(song, _MON)
	la("không đè ánh xạ còn sống", (n, bang["x"]["item_code"], bang["x"]["vgb_uom"]), (0, "NVLT00150", "Chai"))
	n, bang, them = _chay_hoc({}, _MON)
	la("chưa có ánh xạ thì thêm mới", [t["item_code"] for t in them], ["NVLT00151"])


# ----------------------------------------- Codex #363 vòng 1: hai finding

@ca("#523 Codex #363: lượt gỡ chạy trễ đọc danh sách cũ thì KHÔNG lập chứng từ lần hai")
def _dua_nhau():
	# Tái hiện đúng chuỗi Codex tả: nhịp theo giờ và nút Sinh lại cùng thấy
	# hồ sơ còn trắng chứng từ. Lượt A lập xong. Lượt B cầm danh sách đọc
	# TRƯỚC khi A xong, rồi mới tới lượt sinh. Không khoá và soát lại trong
	# giao dịch thì B lập thêm một tờ trả hàng và một phiếu chi nữa.
	from vagabond import hoan_tien as H
	bang = {DT: {"HT-2026-02900": _ho()}}
	loi_log, goi, khoa = [], [], []
	fr = _frappe_gia(bang, loi_log)
	get_value_goc = fr.db.get_value

	def get_value(dt, ten, truong, as_dict=False, for_update=False):
		if for_update:
			khoa.append(ten)
		return get_value_goc(dt, ten, truong, as_dict=as_dict, for_update=for_update)

	fr.db.get_value = get_value

	def sinh(ho):
		goi.append(ho.name)
		bang[DT][ho.name].update(hoa_don_tra="HDB-TRA-%d" % len(goi), phieu_chi="APP-%d" % len(goi))
		return {"bo_qua": 0, "hoa_don_tra": "HDB-TRA-%d" % len(goi), "phieu_chi": "APP-%d" % len(goi)}

	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu")}
	try:
		H.frappe = fr
		H._sinh_chung_tu = sinh
		ds_cu_cua_B = H._ho_so_ket()        # B đọc danh sách khi hồ sơ còn trắng
		H._sinh_va_ghi_loi("HT-2026-02900")  # A lập xong
		for ten in ds_cu_cua_B:              # B tới lượt sinh
			H._sinh_va_ghi_loi(ten)
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
	la("chỉ lập chứng từ MỘT lần", goi, ["HT-2026-02900"])
	la("giữ đúng bộ chứng từ của lượt đầu", bang[DT]["HT-2026-02900"]["phieu_chi"], "APP-1")
	dung("đọc lại hồ sơ có khoá dòng trước khi sinh", "HT-2026-02900" in khoa)


@ca("#523 Codex #363: nút Đối soát lệnh chi gỡ được phiếu kẹt thì báo đúng, không báo 'không có phiếu nào'")
def _bao_dung():
	bang = {DT: {"HT-2026-02900": _ho()}}
	kq, goi, _f, _l = _chay_ht(bang)
	la("đã gỡ", goi, ["HT-2026-02900"])
	dung("không còn câu 'Không có phiếu nào chờ đối soát'",
		"Không có phiếu nào chờ" not in (kq.get("ghi_chu") or ""))
	dung("câu báo nêu đúng phiếu vừa lập lại", "HT-2026-02900" in (kq.get("ghi_chu") or ""))
	la("trả danh sách phiếu đã gỡ cho màn", kq.get("da_go"), ["HT-2026-02900"])
	# Có khớp mới (không thoát sớm) thì câu tổng của màn vẫn do màn ghép,
	# nhưng danh sách đã gỡ phải có để màn nối thêm.
	bang = {DT: {"HT-B": _ho()}}
	kq, goi, _f, _l = _chay_ht(bang, khop=lambda ho_so=None, so_ngay=30: {
		"da_khop": 2, "xem_xet": [], "so_phieu_quet": 3, "da_sinh": [], "_da_thu": []})
	la("không đè câu tổng khi có khớp mới", kq.get("ghi_chu"), None)
	la("vẫn trả danh sách đã gỡ", kq.get("da_go"), ["HT-B"])


# ----------------------------------------- Codex #363 vòng 2

def _chay_xen(bang, khi_khoa=None, khi_lui=None, sinh_duoc=True, goi="sinh", ho_so="HT-2026-02900"):
	"""Chạy hàm THẬT với một lượt khác "ghi xong" đúng lúc ta lấy khoá hoặc
	vừa lùi giao dịch. khi_khoa / khi_lui là thay đổi mà lượt kia đã commit."""
	from vagabond import hoan_tien as H
	loi_log, goi_sinh = [], []
	fr = _frappe_gia(bang, loi_log)
	goc_gv, goc_rb = fr.db.get_value, fr.db.rollback
	cho = {"khoa": dict(khi_khoa or {}), "lui": dict(khi_lui or {})}

	def get_value(dt, ten, truong, as_dict=False, for_update=False):
		if for_update and cho["khoa"]:
			bang[DT][ten].update(cho["khoa"]); cho["khoa"] = {}
		return goc_gv(dt, ten, truong, as_dict=as_dict, for_update=for_update)

	def rollback():
		goc_rb()
		if cho["lui"]:
			bang[DT][ho_so].update(cho["lui"]); cho["lui"] = {}

	fr.db.get_value, fr.db.rollback = get_value, rollback

	def sinh(ho):
		goi_sinh.append(ho.name)
		if not sinh_duoc:
			raise _Loi("CK vượt tổng")
		bang[DT][ho.name].update(hoa_don_tra="HDB-TRA-1", phieu_chi="APP-1")
		return {"bo_qua": 0, "hoa_don_tra": "HDB-TRA-1", "phieu_chi": "APP-1"}

	B = SimpleNamespace(_kiem_quyen=lambda *a, **k: None)
	cu_mod = sys.modules.get("vagabond.ban_hang")
	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu", "_duoc_tu_choi")}
	try:
		sys.modules["vagabond.ban_hang"] = B
		H.frappe, H._sinh_chung_tu = fr, sinh
		H._duoc_tu_choi = lambda nguoi=None: True
		kq = H.sinh_lai(ho_so) if goi == "nut" else H._sinh_va_ghi_loi(ho_so)
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
		if cu_mod is None:
			sys.modules.pop("vagabond.ban_hang", None)
		else:
			sys.modules["vagabond.ban_hang"] = cu_mod
	return kq, goi_sinh


@ca("#523 Codex #363 v2: lượt hỏng vừa lùi thì KHÔNG ghi đè câu lỗi lên hồ sơ lượt khác đã lập xong")
def _khong_de_loi():
	# Lượt ta hỏng và lùi; đúng lúc đó lượt kia (đang chờ khoá) đã lập xong
	# và dọn câu lỗi. Ghi mù câu lỗi là để một hồ sơ đủ chứng từ trông như kẹt.
	bang = {DT: {"HT-2026-02900": _ho(loi_sinh_ct="cũ")}}
	_kq, _g = _chay_xen(bang, sinh_duoc=False,
		khi_lui={"hoa_don_tra": "HDB-TRA-9", "phieu_chi": "APP-9", "loi_sinh_ct": ""})
	la("câu lỗi vẫn trống", bang[DT]["HT-2026-02900"]["loi_sinh_ct"], "")
	la("giữ chứng từ của lượt kia", bang[DT]["HT-2026-02900"]["phieu_chi"], "APP-9")
	# Còn kẹt thật thì vẫn ghi lỗi như cũ.
	bang = {DT: {"HT-2026-02900": _ho(loi_sinh_ct="cũ")}}
	_kq, _g = _chay_xen(bang, sinh_duoc=False)
	dung("kẹt thật thì vẫn ghi lỗi", "Sinh lại chứng từ" in bang[DT]["HT-2026-02900"]["loi_sinh_ct"])


@ca("#523 Codex #363 v2: nút Sinh lại chờ khoá mà nhịp theo giờ đã lập xong thì báo thành công")
def _xong_truoc():
	bang = {DT: {"HT-2026-02900": _ho()}}
	kq, goi = _chay_xen(bang, goi="nut",
		khi_khoa={"hoa_don_tra": "HDB-TRA-7", "phieu_chi": "APP-7", "loi_sinh_ct": ""})
	la("không lập lần hai", goi, [])
	la("báo thành công kèm đúng chứng từ", (kq.get("ok"), kq.get("phieu_chi")), (1, "APP-7"))
	la("nói rõ là đã xong từ trước", kq.get("da_xong_truoc"), 1)


# ----------------------------------------- Codex #363 vòng 3

@ca("#523 Codex #363 v3: lập được tờ trả mà KHÔNG lập được phiếu chi thì chưa phải thành công")
def _thieu_phieu_chi():
	# _lap_phieu_chi nuốt lỗi và trả None. Trước sửa: tờ trả hàng đã ghi sổ,
	# câu lỗi bị dọn, nút báo thành công, và vì đã có tờ trả nên hồ sơ không
	# còn "kẹt", nút Sinh lại biến mất trong khi chưa có phiếu chi để đính UNC.
	from vagabond import hoan_tien as H
	bang = {DT: {"HT-2026-02900": _ho(loi_sinh_ct="cũ")}}
	loi_log = []
	fr = _frappe_gia(bang, loi_log)
	ghi = {}

	def rollback():
		# Lùi giao dịch: bỏ mọi thứ lượt này đã ghi lên hồ sơ.
		bang[DT]["HT-2026-02900"].update(hoa_don_tra="", phieu_chi="")
		ghi["lui"] = 1

	fr.db.rollback = rollback

	def sinh(ho):
		bang[DT][ho.name]["hoa_don_tra"] = "HDB-TRA-1"
		return {"bo_qua": 0, "hoa_don_tra": "HDB-TRA-1", "phieu_chi": None}

	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu")}
	try:
		H.frappe, H._sinh_chung_tu = fr, sinh
		kq = H._sinh_va_ghi_loi("HT-2026-02900")
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
	la("không báo thành công", kq, None)
	dung("lùi cả tờ trả hàng để còn sinh lại được", ghi.get("lui") == 1)
	loi = bang[DT]["HT-2026-02900"]["loi_sinh_ct"]
	dung("ghi lỗi nói rõ thiếu phiếu chi", "phiếu chi" in loi)
	dung("hồ sơ vẫn còn kẹt để bấm lại", H.ket_chung_tu(bang[DT]["HT-2026-02900"]))


@ca("#523 Codex #363 v3: màn còn nút Sinh lại mà nhịp theo giờ đã lập xong TRƯỚC khi bấm thì báo thành công")
def _xong_truoc_khi_bam():
	bang = {DT: {"HT-2026-02900": _ho(hoa_don_tra="HDB-TRA-5", phieu_chi="APP-5", loi_sinh_ct="")}}
	try:
		kq, goi = _chay_xen(bang, goi="nut")
		loi = ""
	except _Loi as e:
		kq, goi, loi = {}, [], str(e)
	la("không ném lỗi", loi, "")
	la("báo thành công đúng chứng từ", (kq.get("ok"), kq.get("phieu_chi"), kq.get("da_xong_truoc")), (1, "APP-5", 1))
	# Chưa khớp tiền ra thì vẫn chặn như cũ.
	bang = {DT: {"HT-X": _ho(da_doi_soat=0)}}
	try:
		_chay_xen(bang, goi="nut", ho_so="HT-X")
		chan = False
	except _Loi:
		chan = True
	dung("hồ sơ chưa khớp tiền ra vẫn bị từ chối", chan)


@ca("#523 Codex #363 v3: ánh xạ chi nhánh cũ trỏ món đã tắt không làm hỏng phép đếm duy nhất")
def _nhieu_chi_nhanh():
	hai = _MAP_TAT + [dict(_MAP_TAT[0], item_code="NVLT00151", vgb_uom="Chai", supplier_mst="0315777858-001")]
	try:
		ra = _chay_qc("lay", hai, _MON, "NVLT00151", "0315777858", "Rượu Kahlua 70cl")
		loi = ""
	except _Loi as e:
		ra, loi = None, str(e)
	la("không báo nhiều ánh xạ", loi, "")
	la("dùng quy cách của ánh xạ còn sống", ra, "Chai")


# ----------------------------------------- Codex #363 vòng 5

@ca("#523 Codex #363 v5: lối Khớp SePay thủ công thiếu phiếu chi thì lùi và giữ hồ sơ kẹt")
def _khop_tay_thieu_pc():
	# Đúng chuỗi: kế toán khớp tay một dòng tiền ra, tầng đối soát chung gọi
	# _khi_khop_hoan_tien, lập tờ trả được mà phiếu chi hỏng (bị nuốt lỗi).
	from vagabond import hoan_tien as H
	bang = {DT: {"HT-K": _ho(da_doi_soat=0, trang_thai="Cho chi", loi_sinh_ct="")}}
	fr = _frappe_gia(bang, [])

	def rollback():
		bang[DT]["HT-K"].update(hoa_don_tra="", phieu_chi="")

	fr.db.rollback = rollback

	def sinh(ho):
		bang[DT][ho.name]["hoa_don_tra"] = "HDB-TRA-1"
		return {"bo_qua": 0, "hoa_don_tra": "HDB-TRA-1", "phieu_chi": None}

	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu")}
	try:
		H.frappe, H._sinh_chung_tu = fr, sinh
		try:
			H._khi_khop_hoan_tien(_Doc(name="HT-K"), "ACC-BTN-1")
			nem = ""
		except _Loi as e:
			nem = str(e)
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
	# Vòng 6: tầng đối soát chung chỉ bày lỗi NÉM ra, nên hỏng phải ném, và
	# câu ném chỉ đúng nút Sinh lại chứng từ.
	dung("ném lỗi để màn Khớp tay không báo thành công", bool(nem))
	dung("câu lỗi chỉ đúng nút Sinh lại chứng từ", "Sinh lại chứng từ" in nem)
	la("vẫn giữ dấu đã khớp tiền ra", bang[DT]["HT-K"]["da_doi_soat"], 1)
	dung("ghi lỗi thiếu phiếu chi lên phiếu", "phiếu chi" in bang[DT]["HT-K"]["loi_sinh_ct"])
	dung("hồ sơ còn kẹt để bấm Sinh lại", H.ket_chung_tu(bang[DT]["HT-K"]))


@ca("#523 Codex #363 v5: chỉ MỘT cửa được gọi thẳng bước lập chứng từ hoàn tiền")
def _mot_cua():
	# Điều 18: gom về một nguồn, rồi chốt không còn lối nào tự gọi. Phép dò
	# này chỉ chốt điều không chạy được (ai gọi ai); hành vi đã có các ca trên.
	import ast
	from pathlib import Path
	src = (Path(__file__).resolve().parents[2] / "hoan_tien.py").read_text()
	goi = []
	for fn in ast.walk(ast.parse(src)):
		if isinstance(fn, ast.FunctionDef):
			for n in ast.walk(fn):
				if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_sinh_chung_tu":
					goi.append(fn.name)
	la("chỉ _sinh_va_ghi_loi gọi _sinh_chung_tu", sorted(set(goi)), ["_sinh_va_ghi_loi"])


@ca("#523 Codex #363 v6: khớp tay trên hồ sơ đã đủ chứng từ thì KHÔNG ném")
def _khop_tay_da_du():
	from vagabond import hoan_tien as H
	bang = {DT: {"HT-D": _ho(hoa_don_tra="HDB-TRA-3", phieu_chi="APP-3", loi_sinh_ct="")}}
	fr = _frappe_gia(bang, [])
	goi = []
	cu = {k: getattr(H, k) for k in ("frappe", "_sinh_chung_tu")}
	try:
		H.frappe = fr
		H._sinh_chung_tu = lambda ho: goi.append(ho.name) or {"bo_qua": 1}
		try:
			kq = H._khi_khop_hoan_tien(_Doc(name="HT-D"), "ACC-BTN-3")
			nem = ""
		except _Loi as e:
			kq, nem = None, str(e)
	finally:
		for k, v in cu.items():
			setattr(H, k, v)
	la("không ném", nem, "")
	la("không lập thêm", goi, [])
	la("giữ phiếu chi cũ", bang[DT]["HT-D"]["phieu_chi"], "APP-3")
