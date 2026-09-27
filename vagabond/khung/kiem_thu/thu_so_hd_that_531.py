"""v531: số hoá đơn thật, và gieo lại nháp chính sách (anh Việt 27/09/2026).

Ca thật: HDM-26-08-00027 (Cấp nước Tân Hoà) mang số hoá đơn "APP.26.08.004",
là mã hồ sơ do luồng Hoàn ứng tự điền khi khoản không có số. Nối tờ đó vào
APP.26.08.005 đã đẩy hồ sơ lên "Chi phí hợp lệ tính thuế" sai. Bộ này chốt:

  - phép thuần nhận ra số hoá đơn giả (trống, toàn 0, mã hồ sơ);
  - nối mức hồ sơ và nối kiểu cũ: vẫn bù trừ, nhưng KHÔNG lên hợp lệ, và
    hồ sơ đang hợp lệ thì hạ;
  - lập hồ sơ TK công ty từ tờ tick không có số thật thì chặn;
  - Hoàn ứng: khoản không VAT sinh tờ để trống số, khoản VAT phải có số thật
    ở mọi cửa gửi duyệt và trước khi sinh tờ;
  - hook Hoá đơn mua chặn ghi mã hồ sơ vào ô số hoá đơn khi đặt mới hay đổi;
  - tờ nháp đã nối không đổi được số hoá đơn;
  - hai đường nối kiểu cũ nạp hồ sơ có khoá;
  - mã số thuế 9 số (rơi số 0 đầu) vẫn nhóm đúng;
  - gieo nháp chính sách đi được nhánh TẠO MỚI (lỗi thật lúc deploy v529).
"""
import json
import types
from types import SimpleNamespace
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_noi_hd_sau_530 import _C, _HoSo, _chay, _mobi, _pi, T331, T6427
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap

T6277 = "6277 - Chi phí dịch vụ mua ngoài - TV"


class _Loi(Exception):
	pass


def _du_thuoc_tinh():
	"""Bộ frappe giả của tầng khung không có sẵn mọi hàm; thêm chỗ trống để
	patch.object thay được (giá trị thật luôn do từng ca patch vào)."""
	import frappe
	for a in ("new_doc", "get_doc", "throw", "log_error", "db"):
		if not hasattr(frappe, a):
			setattr(frappe, a, None)
	if not hasattr(frappe, "session"):
		frappe.session = SimpleNamespace(user="dung@vgb")


_du_thuoc_tinh()


def _throw(msg, *a, **k):
	raise _Loi(msg)


# ---------------------------------------------------------------- phép thuần

@ca("v531 thuần: số hoá đơn giả là trống, toàn 0, hay mã hồ sơ APP; số thật và mã ký hiệu vẫn qua")
def _so_that():
	from vagabond.hoa_don_sau import la_so_hoa_don_that as f
	for so in ("APP.26.08.004", "APP-26-08-004", "app.26.08.004", "APP26080", "APPMEREJM", "", "   ", "0", "0000", "-"):
		la("giả: %r" % so, f(so), False)
	for so in ("5802", "0012515", "C26TAA-12", "APPLE", "Apple 12", "APP.X", "262"):
		la("thật: %r" % so, f(so), True)


@ca("v531 thuần: khoản hoàn ứng có VAT mà thiếu số thật thì liệt kê; khoản không VAT không đòi số")
def _vat_thieu():
	from vagabond.hoa_don_sau import khoan_vat_thieu_so
	ds = [dict(noi_dung="Tiền nước", co_vat=1, so_hd_ncc=""), dict(noi_dung="Gas", co_vat=1, so_hd_ncc="APP.26.08.004"),
		dict(noi_dung="Rau", co_vat=0, so_hd_ncc=""), dict(noi_dung="Điện", co_vat=1, so_hd_ncc="0098812")]
	la("đúng hai khoản", khoan_vat_thieu_so(ds), [(1, "Tiền nước", ""), (2, "Gas", "APP.26.08.004")])


@ca("v531 thuần: mã số thuế 9 số (rơi số 0 đầu) bù lại, nhóm được với chi nhánh")
def _mst_9():
	from vagabond.hoa_don_sau import cung_nhom, mst_goc
	la("Tân Hoà 9 số", mst_goc("310350068"), "0310350068")
	la("10 số giữ nguyên", mst_goc("0100686209-096"), "0100686209")
	la("8 số vẫn không nhóm", mst_goc("12345678"), "")
	dung("9 số cùng nhóm với chi nhánh 10 số", cung_nhom("A", "310350068", "B", "0310350068-001"))


@ca("v531 thuần: nhãn tờ ở ô chọn báo tờ không có số hoá đơn thật; dòng không mang ô số thì không gắn")
def _nhan():
	from vagabond.hoa_don_sau import nhan_to
	dung("mã hồ sơ", "không có số hoá đơn thật" in nhan_to(dict(docstatus=1, outstanding_amount=5, bill_no="APP.26.08.004")))
	dung("số thật", "không có số" not in nhan_to(dict(docstatus=0, bill_no="5802")))
	dung("không mang ô bill_no", "không có số" not in nhan_to(dict(docstatus=0)))


@ca("v531 thuần: tờ giả làm căn cứ (nối mức hồ sơ, nối cũ, hoá đơn gốc) thì không hợp lệ")
def _nen_hop_le():
	from vagabond.hoa_don_sau import nen_hop_le
	k = [dict(so_tien=100, cho_hoa_don=1)]
	dung("tờ thật phủ đủ: hợp lệ", nen_hop_le(k, [dict(hoa_don="PI-1", tien_khop=100)]))
	dung("tờ nối mức hồ sơ giả: không", not nen_hop_le(k, [dict(hoa_don="PI-1", tien_khop=100)], to_gia={"PI-1"}))
	k2 = [dict(so_tien=100, cho_hoa_don=0, hoa_don="PI-G"), dict(so_tien=50, cho_hoa_don=1)]
	dung("hoá đơn gốc giả: không", not nen_hop_le(k2, [dict(hoa_don="PI-2", tien_khop=50)], to_gia={"PI-G"}))


# ------------------------------------------------ nối mức hồ sơ (hàm thật)

def _tan_hoa(cp="Chi phi khong hop le"):
	return _HoSo("APP.26.08.005", "TANHOA", [dict(tk_no=T6277, so_tien=1905303)], cp=cp, ngay_tt="2026-09-04")


@ca("v531 nối tờ đã ghi sổ mang số APP (ca Tân Hoà, hàm nối thật): vẫn bù trừ, KHÔNG lên hợp lệ, báo rõ tờ nào")
def _noi_gia():
	to = {"HDM-26-08-00027": _pi("HDM-26-08-00027", "TANHOA", 1905303, bill="APP.26.08.004", ngay="2026-08-17")}
	r = _chay(_tan_hoa(), to, lambda b: b.noi_nhieu("APP.26.08.005", "HDM-26-08-00027"),
		so_hd={"HDM-26-08-00027": "APP.26.08.004"})
	la("nối được", r.loi, "")
	la("có một bút toán bù trừ (hết chi phí hai lần)", len(r.je), 1)
	la("nhãn giữ Không hợp lệ", (r.hs.loai_cp_thue, r.kq["hop_le"]), ("Chi phi khong hop le", 0))
	la("báo tờ không có số thật", r.kq["khong_hoa_don_that"], ["HDM-26-08-00027"])
	dung("nhật ký ghi lý do", "không có số hoá đơn thật" in r.hs.ghi_chu[-1])
	dung("đọc số hoá đơn bằng câu có khoá", any("select name, bill_no" in q.lower() and "for update" in q.lower() for q in r.cau))
	# Cùng hồ sơ, tờ mang số thật: lên hợp lệ như v530.
	to2 = {"HDM-T": _pi("HDM-T", "TANHOA", 1905303, bill="0012345", ngay="2026-08-17")}
	r2 = _chay(_tan_hoa(), to2, lambda b: b.noi_nhieu("APP.26.08.005", "HDM-T"), so_hd={"HDM-T": "0012345"})
	la("tờ thật: lên hợp lệ", (r2.hs.loai_cp_thue, r2.kq["hop_le"], r2.kq["khong_hoa_don_that"]), ("Chi phi hop le", 1, []))


@ca("v531 hồ sơ đang Hợp lệ mà tờ đã nối trước là tờ giả: lần nối sau hạ về Không hợp lệ")
def _ha_khi_gia():
	ho = _mobi(cp="Chi phi hop le", hd_sau=[dict(hoa_don="HDM-A", tien_khop=700000, da_ghi_so=0, bu_tru=0, but_toan="")])
	to = {"HDM-B": _pi("HDM-B", "MOBI-096", 78784, docstatus=0, bill="5555")}
	r = _chay(ho, to, lambda b: b.noi_nhieu("APP.26.09.102", '["HDM-B"]'), so_hd={"HDM-A": "APP.26.09.001", "HDM-B": "5555"})
	la("nối được", r.loi, "")
	la("hạ nhãn, báo về không hợp lệ", (r.hs.loai_cp_thue, r.kq["ve_khong_hop_le"]), ("Chi phi khong hop le", 1))
	la("tờ vừa nối có số thật nên không bị gọi tên", r.kq["khong_hoa_don_that"], [])


# ------------------------------------------------ nối kiểu cũ (hàm thật)

@ca("v531 nối kiểu cũ một tờ một khoản: tờ số APP thì không đổi hợp lệ, báo lý do; hồ sơ nạp có khoá")
def _noi_cu():
	from vagabond.khung.kiem_thu.thu_v526 import _D, _noi
	r = _D(cho_hoa_don=1, hoa_don_bo_sung="", so_tien=80000)
	goi = []
	d, kq = _noi("TK cong ty", [r], so_hd={"PI-THU": "APP.26.08.004"}, goi=goi)
	la("không đổi hợp lệ", (d.loai_cp_thue, kq["hop_le"]), ("Chi phi khong hop le", 0))
	dung("báo tờ không có số thật", any("không có số hoá đơn thật" in x for x in kq["lech"]))
	dung("nạp hồ sơ có khoá", any(k.get("for_update") for k in goi))
	r = _D(cho_hoa_don=1, hoa_don_bo_sung="", so_tien=80000)
	d, kq = _noi("TK cong ty", [r], so_hd={"PI-THU": "5802"})
	la("tờ thật: hợp lệ như v526", kq["hop_le"], 1)


@ca("v531 đánh dấu bù hoá đơn đến sau: nạp hồ sơ có khoá")
def _danh_dau_khoa():
	_du_thuoc_tinh()
	import frappe
	from unittest.mock import Mock
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	dong = D(idx=1, hoa_don="", hoa_don_bo_sung="", cho_hoa_don=0)
	dong.as_dict = lambda: dict(hoa_don="", hoa_don_bo_sung="", cho_hoa_don=0)
	d = SimpleNamespace(dong=[dong], loai="TK cong ty", trang_thai="Da thanh toan", save=Mock(), add_comment=Mock())
	goi = []

	def get_doc(*a, **k):
		goi.append(k)
		return d
	with patch.object(frappe, "db", SimpleNamespace(sql=lambda *a, **k: ())), \
		patch.object(frappe, "get_doc", side_effect=get_doc), patch.object(hs, "_kiem"):
		kq = bo.danh_dau_cho_hoa_don("APP-THU", 1)
	la("đánh dấu được", kq["ok"], 1)
	dung("nạp hồ sơ có khoá", any(k.get("for_update") for k in goi))


# ------------------------------------------------ tờ nháp đã nối, hook tờ

@ca("v531 tờ nháp đã nối: đổi số hoá đơn khi lưu thì chặn, gọi tên hồ sơ; tờ chưa nối đổi thoải mái")
def _khoa_so_hd():
	from vagabond.khung.kiem_thu.thu_v526 import _hd_sua, CTY
	loi = _hd_sua({"supplier": "XDKV2", "company": CTY, "bill_no": ""}, {"supplier": "XDKV2", "company": CTY, "bill_no": "5802"})
	dung("chặn, gọi tên hồ sơ và số hoá đơn", "APP-A" in loi and "số hoá đơn" in loi)
	la("tờ chưa nối", _hd_sua({"supplier": "XDKV2", "company": CTY, "bill_no": ""},
		{"supplier": "XDKV2", "company": CTY, "bill_no": "5802"}, giu=""), "")


def _hook(so_moi, so_cu=None, moi=False):
	_du_thuoc_tinh()
	import frappe
	from vagabond import ho_so_bo_sung as bo
	cu = None if so_cu is None else D(bill_no=so_cu)
	doc = D(bill_no=so_moi)
	doc.is_new = lambda: moi
	doc.get_doc_before_save = lambda: cu
	with patch.object(frappe, "throw", side_effect=_throw):
		try:
			bo.chan_so_hd_gia(doc)
			return ""
		except _Loi as e:
			return str(e)


@ca("v531 hook Hoá đơn mua: ghi mã hồ sơ vào số hoá đơn thì chặn khi tạo mới hay đổi; tờ cũ giữ nguyên số thì lưu được")
def _hook_so():
	dung("tạo mới mang APP: chặn", "không phải số hoá đơn" in _hook("APP.26.09.200", moi=True))
	dung("đổi từ trống sang APP: chặn", "APP.26.09.200" in _hook("APP.26.09.200", so_cu=""))
	la("tờ cũ đã mang APP, lưu lại không đổi số: qua", _hook("APP.26.08.004", so_cu="APP.26.08.004"), "")
	la("để trống: qua", _hook("", so_cu="5802"), "")
	la("số thật: qua", _hook("0012515", moi=True), "")
	import vagabond.hooks as hk
	dung("đăng ký validate Hoá đơn mua", "vagabond.ho_so_bo_sung.chan_so_hd_gia" in hk.doc_events["Purchase Invoice"]["validate"])


# ------------------------------------------------ lập hồ sơ TK công ty

class _DiTiep(Exception):
	pass


def _tao_tkct(so):
	_du_thuoc_tinh()
	import frappe
	from vagabond import ho_so_tt as hs
	hd = D(name="HDM-X", supplier="TANHOA", supplier_name="Tân Hoà", posting_date="2026-08-17", bill_date="2026-08-17",
		bill_no=so, due_date="2026-08-30", grand_total=1905303, outstanding_amount=1905303, docstatus=1)

	def new_doc(*a, **k):
		raise _DiTiep()
	with patch.object(frappe, "db", SimpleNamespace(get_value=lambda *a, **k: hd)), \
		patch.object(frappe, "throw", side_effect=_throw), patch.object(frappe, "new_doc", side_effect=new_doc), \
		patch.object(hs, "_kiem"), patch.object(hs, "_chan_hoa_don_trung"), patch.object(hs, "_soi_phieu_noi_bo"):
		try:
			hs.tao(hoa_don=["HDM-X"], loai=hs.LOAI_TKCT, tk_chi="MB", loai_cp_thue=hs.CP_HOP_LE)
			return "xong"
		except _Loi as e:
			return str(e)
		except _DiTiep:
			return "đi tiếp"


@ca("v531 lập hồ sơ TK công ty (nhãn hợp lệ) từ tờ tick không có số hoá đơn thật: chặn; tờ số thật đi tiếp")
def _tao_tkct_ca():
	loi = _tao_tkct("APP.26.08.004")
	dung("chặn, gọi tên tờ và số đang ghi", "HDM-X" in loi and "APP.26.08.004" in loi)
	dung("trống số: chặn", "trống số" in _tao_tkct(""))
	la("số thật: qua cửa này", _tao_tkct("0012345"), "đi tiếp")


# ------------------------------------------------ hoàn ứng

def _ho_so_hu(dong, trang_thai="Nhap"):
	rows = []
	for i, x in enumerate(dong, 1):
		r = D(idx=i, hoa_don="", noi_dung=x.get("noi_dung", "Khoản"), ben_ban="", loai_chi="", so_tien=x.get("so_tien", 100000),
			ngay_hd="2026-09-20", co_vat=x.get("co_vat", 0), so_hd_ncc=x.get("so_hd_ncc", ""))
		r.as_dict = (lambda rr: lambda: dict(rr))(r)
		r.db_set = (lambda rr: lambda k, v, **kw: rr.__setitem__(k, v))(r)
		rows.append(r)
	return D(name="APP.26.09.300", loai="Hoan ung", trang_thai=trang_thai, dong=rows, nha_cung_cap="NCC-LE",
		ten_ncc="Mua lẻ", ngay="2026-09-20", stk_nhan="123", reload=lambda: None)


def _sinh(doc):
	_du_thuoc_tinh()
	import frappe
	from vagabond import ho_so_tt as hs
	tao = []

	class PI(D):
		def append(self, k, v):
			self.setdefault(k, []).append(v)

		def insert(self, **k):
			self.name = "PI-%d" % (len(tao) + 1)
			tao.append(self)

		def submit(self):
			pass
	db = SimpleNamespace(exists=lambda *a: True, get_single_value=lambda *a: "CTY", get_value=lambda *a, **k: "Nos",
		commit=lambda: None)
	with patch.object(frappe, "db", db), patch.object(frappe, "new_doc", side_effect=lambda dt: PI(flags=D())), \
		patch.object(frappe, "throw", side_effect=_throw), patch.object(hs, "_ghi_vet"):
		try:
			hs._sinh_hoa_don_hoan_ung(doc)
			return tao, ""
		except _Loi as e:
			return tao, str(e)


@ca("v531 hoàn ứng: tờ gom khoản không VAT để TRỐNG số hoá đơn (không còn mã hồ sơ); tờ VAT mang đúng số")
def _sinh_trong_so():
	tao, loi = _sinh(_ho_so_hu([dict(noi_dung="Rau", co_vat=0), dict(noi_dung="Điện", co_vat=1, so_hd_ncc="0098812")]))
	la("sinh được", loi, "")
	so = sorted((p.get("bill_no") or "") for p in tao)
	la("một tờ trống số, một tờ đúng số", so, ["", "0098812"])
	dung("mã hồ sơ vẫn ở ghi chú tờ", all("APP.26.09.300" in p.remarks for p in tao))


@ca("v531 hoàn ứng: khoản đánh dấu VAT mà thiếu số thật thì dừng TRƯỚC khi sinh tờ nào; cửa gửi duyệt cũng chặn")
def _vat_chan():
	_du_thuoc_tinh()
	import frappe
	from vagabond import ho_so_tt as hs
	tao, loi = _sinh(_ho_so_hu([dict(noi_dung="Tiền nước", co_vat=1, so_hd_ncc="")]))
	dung("sinh: chặn, gọi tên khoản", "Tiền nước" in loi and "chưa ghi số" in loi)
	la("không sinh tờ nào", len(tao), 0)
	doc = _ho_so_hu([dict(noi_dung="Gas", co_vat=1, so_hd_ncc="APP.26.08.004")])
	with patch.object(frappe, "get_doc", return_value=doc), patch.object(frappe, "throw", side_effect=_throw), \
		patch.object(hs, "_kiem"), patch.object(hs, "_dat_buoc_gui", side_effect=_DiTiep):
		try:
			hs.duyet("APP.26.09.300", "gui_fin")
			loi = "đi tiếp"
		except _Loi as e:
			loi = str(e)
		except _DiTiep:
			loi = "đi tiếp"
	dung("gửi duyệt: chặn, gọi số đang ghi", "APP.26.08.004" in loi)
	doc2 = _ho_so_hu([dict(noi_dung="Gas", co_vat=1, so_hd_ncc="0012515")])
	with patch.object(frappe, "get_doc", return_value=doc2), patch.object(frappe, "throw", side_effect=_throw), \
		patch.object(hs, "_kiem"), patch.object(hs, "_dat_buoc_gui", side_effect=_DiTiep):
		try:
			hs.duyet("APP.26.09.300", "gui_fin")
			loi2 = "xong"
		except _DiTiep:
			loi2 = "đi tiếp"
		except _Loi as e:
			loi2 = str(e)
	la("số thật: qua cửa này", loi2, "đi tiếp")
	# Cửa thứ ba (lập hồ sơ kèm gửi luôn) không chạy được trên bộ giả lập vì
	# cần cả chuỗi tài khoản nhận; chốt rằng cửa đó gọi đúng hàm chặn.
	import inspect
	than = inspect.getsource(hs.tao_hoan_ung)
	dung("lập kèm gửi luôn cũng chặn", "_chan_vat_thieu_so(sach)" in than)


# ------------------------------------------------ gieo nháp chính sách

@ca("v531 gieo nháp chính sách nhánh TẠO MỚI: Doc giả giữ luật is_new() của Frappe; bản cũ nổ như site thật, bản sửa tạo được")
def _gieo_moi():
	import copy
	import subprocess
	from vagabond import noi_dung_web
	them = {}

	class Doc(D):
		"""get_doc(dict) của Frappe không đặt cờ __islocal: is_new() False, và
		save() đi tìm bản ghi trong cơ sở dữ liệu. new_doc thì đặt cờ."""
		def is_new(self):
			return bool(self.get("__islocal"))

		def save(self, **k):
			raise _Loi("Vagabond Noi Dung Web order not found")

		def insert(self, **k):
			them["nhap"] = json.loads(self.ban_nhap)
			them["cong_khai"] = self.ban_cong_khai
			them["name"] = self.name

	def new_doc(dt):
		return Doc(doctype=dt, __islocal=1, flags=D())

	def get_doc(x, *a, **k):
		return Doc(dict(x), flags=D())
	fr = types.SimpleNamespace(db=types.SimpleNamespace(exists=lambda *a: False), new_doc=new_doc, get_doc=get_doc)
	g = dict(frappe=fr, DOCTYPE="Vagabond Noi Dung Web", TEN="order", MAC_DINH=noi_dung_web.MAC_DINH,
		CHINH_SACH=noi_dung_web.CHINH_SACH, chuan_hoa=noi_dung_web.chuan_hoa, _doc=None,
		json=json, copy=copy)
	gieo = nap("noi_dung_web.py", "gieo_chinh_sach", g)
	dung("bản sửa: tạo mới được", gieo({"dieu_khoan": "# Điều khoản"}))
	la("đúng tên bản ghi", them.get("name"), "order")
	la("vào nháp, còn ẩn", them["nhap"]["chinh_sach"]["dieu_khoan"], {"hien": False, "vn": "# Điều khoản", "en": ""})
	# Bản 52ca0cc (v529/v530 trên site): cùng Doc giả thì nổ đúng câu site thật báo.
	cu = subprocess.run(["git", "show", "52ca0cc:vagabond/noi_dung_web.py"], capture_output=True, text=True).stdout
	if cu:
		import ast
		cay = ast.parse(cu)
		ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "gieo_chinh_sach")
		ham.decorator_list = []
		g_cu = dict(g)
		exec(compile(ast.Module(body=[ham], type_ignores=[]), "noi_dung_web_52ca0cc.py", "exec"), g_cu)
		gieo_cu = g_cu["gieo_chinh_sach"]
		try:
			gieo_cu({"dieu_khoan": "# Điều khoản"})
			ket = "không nổ"
		except _Loi as e:
			ket = str(e)
		la("bản cũ nổ như site thật", ket, "Vagabond Noi Dung Web order not found")


@ca("v531 patch gieo lại (Codex #375): gieo hỏng thì patch NỔ để migrate dừng, không nuốt lỗi rồi ghi là đã chạy")
def _patch_khong_nuot():
	import importlib
	from vagabond import noi_dung_web
	pt = importlib.import_module("vagabond.patches.gieo_chinh_sach_531")
	goi = []

	def hong():
		goi.append(1)
		raise _Loi("Vagabond Noi Dung Web order not found")
	with patch.object(noi_dung_web, "gieo_tu_tep", side_effect=hong):
		try:
			pt.execute()
			ket = "nuốt lỗi"
		except _Loi as e:
			ket = str(e)
	la("gọi gieo đúng một lần", len(goi), 1)
	la("lỗi nổ ra ngoài patch", ket, "Vagabond Noi Dung Web order not found")
	with patch.object(noi_dung_web, "gieo_tu_tep", return_value=True) as g:
		pt.execute()
	la("gieo được thì chạy êm", g.call_count, 1)


@ca("v531 ca bench gieo (Codex #375): không gọi frappe.delete_doc, vì on_trash của Nội dung web chặn xoá vô điều kiện")
def _bench_khong_delete_doc():
	# Không chạy được ca bench ở tầng khung (cần site thật); chốt bằng cây cú
	# pháp: thân _gieo_that không có lời gọi delete_doc, và on_trash vẫn chặn.
	import ast
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	cay = ast.parse(open(os.path.join(goc, "khung", "kiem_that", "thu_so_hd_that_531.py"), encoding="utf-8").read())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_gieo_that")
	goi = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(ham) if isinstance(n, ast.Call)}
	dung("không gọi delete_doc", "delete_doc" not in goi)
	dung("xoá bằng frappe.db.delete trong điểm lưu", "delete" in goi)
	dt = open(os.path.join(goc, "vagabond", "doctype", "vagabond_noi_dung_web", "vagabond_noi_dung_web.py"), encoding="utf-8").read()
	dung("on_trash vẫn chặn xoá (lý do của ca này)", "def on_trash" in dt and "frappe.throw" in dt.split("def on_trash", 1)[1])
