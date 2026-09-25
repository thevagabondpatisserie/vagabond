"""v530: nối hoá đơn đến sau NHIỀU-NHIỀU ở mức hồ sơ (chị Dung, anh Việt 25/09/2026).

Ba hồ sơ thật không nối được trên v526-v528:
  - APP.26.09.009 Adecco: MỘT tờ (số 5802, 686.810.159 đ) phủ BA khoản theo bộ phận.
  - APP.26.09.102 Mobifone: SÁU tờ theo từng số thuê bao phủ MỘT khoản 778.784 đ,
    và sáu tờ mang MST chi nhánh -096 trong khi hồ sơ chọn chi nhánh -002.
  - APP.26.08.016 Văn An: tờ số 262 đã ghi sổ trước khi nối.
Cả ba tờ đúng ĐÃ GHI SỔ, còn nợ đủ, trong khi hồ sơ đã ghi Nợ chi phí: chi phí
hai lần. Từ v530 máy lập MỘT bút toán bù trừ Nợ 331 / Có đúng tài khoản chi phí
hồ sơ đã ghi.

Phép thuần chạy thẳng. noi_nhieu, go_noi, kiem_bo_sung chạy HÀM THẬT, chỉ thay
lớp dữ liệu (lớp giả trả đúng số của ba hồ sơ thật). Không dò chuỗi.
Phần trình duyệt: hanh_vi/hoa_don_sau_530.js.
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la


class _Loi(Exception):
	pass


def _throw(msg, *a, **k):
	raise _Loi(msg)


class _C(dict):
	"""Dòng con / bản ghi giả: đọc được cả kiểu thuộc tính lẫn kiểu dict."""

	def __getattr__(self, k):
		if k.startswith("__"):
			raise AttributeError(k)
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)


CTY = "CÔNG TY TNHH PATISSERIE VAGABOND"
T331 = "331 - Phải trả cho người bán - TV"
T6427, T621, T6411, T6421, T152 = ("6427 - Chi phí dịch vụ mua ngoài - TV", "621 - Chi phí NVL trực tiếp - TV",
	"6411 - Chi phí nhân viên - TV", "6421 - Chi phí nhân viên quản lý - TV", "152 - Nguyên liệu, vật liệu - TV")
NCC = {"MOBI-002": "0100686209-002", "MOBI-096": "0100686209-096", "ADECCO": "0311285460", "VAN-AN": "0316000262",
	"KHAC": "0999999999"}
MOBI = [("HDM-26-09-00093", "5310710", 159000), ("HDM-26-09-00287", "5332207", 105570),
	("HDM-26-09-00288", "5422323", 107000), ("HDM-26-09-00289", "5619189", 105290),
	("HDM-26-09-00317", "5284552", 106390), ("HDM-26-09-00318", "5519595", 195534)]


def _pi(name, ncc, tien, docstatus=1, con=None, bill="", ngay="2026-09-05", huy=0):
	return _C(name=name, supplier=ncc, company=CTY, grand_total=tien, docstatus=docstatus,
		outstanding_amount=tien if con is None else con, credit_to=T331, posting_date=ngay, bill_no=bill, vgb_huy=huy)


NHAT_KY = []


class _HoSo:
	def __init__(self, ten, ncc, dong, loai="TK cong ty", tt="Da thanh toan", ngay_tt="2026-09-24", hd_sau=None,
			cp="Chi phi khong hop le"):
		self.name = ten
		self.nha_cung_cap = ncc
		self.loai = loai
		self.trang_thai = tt
		self.loai_cp_thue = cp
		self.ngay_thanh_toan = ngay_tt
		self.dong = [_C(dict(name="D%d" % (i + 1), idx=i + 1, hoa_don="", hoa_don_bo_sung="", cho_hoa_don=1), **x)
			for i, x in enumerate(dong)]
		self.hd_sau = [_C(x) for x in (hd_sau or [])]
		self.flags = _C()
		self.luu = 0
		self.ghi_chu = []

	def get(self, k, md=None):
		return getattr(self, k, md)

	def append(self, bang, x):
		c = _C(x)
		getattr(self, bang).append(c)
		return c

	def remove(self, c):
		self.hd_sau = [r for r in self.hd_sau if r is not c]

	def save(self, **k):
		NHAT_KY.append("luu " + ",".join(r.hoa_don for r in self.hd_sau))
		from vagabond import ho_so_bo_sung as bo
		# Lưu thật đi qua validate: chạy CHÍNH luật bảng tờ nối (loi_sua_hd_sau)
		# như controller, với bản trước lúc lưu là ảnh đã chụp khi mở hồ sơ.
		from vagabond.hoa_don_sau import loi_sua_hd_sau
		loi = loi_sua_hd_sau(self._truoc, [dict(r) for r in self.hd_sau], bool(self.flags.vgb_noi_hd_sau))
		if loi:
			raise _Loi(loi)
		self.luu += 1

	def add_comment(self, loai, noi):
		self.ghi_chu.append(noi)


class _JE:
	def __init__(self, ds_je, ten=None, docstatus=0):
		self.accounts = []
		self.flags = _C()
		self.docstatus = docstatus
		self.name = ten
		self._ds = ds_je

	def append(self, bang, x):
		getattr(self, bang).append(dict(x))

	def insert(self, **k):
		self.name = "PKT-2026-%05d" % (900 + len(self._ds))
		self._ds.append(self)

	def submit(self):
		no = round(sum(r.get("debit_in_account_currency", 0) for r in self.accounts), 2)
		co = round(sum(r.get("credit_in_account_currency", 0) for r in self.accounts), 2)
		if abs(no - co) > 0.001:
			raise _Loi("bút toán lệch Nợ %s Có %s" % (no, co))
		self.docstatus = 1

	def get(self, k, md=None):
		return getattr(self, k, md)

	def cancel(self):
		# Chạy CHÍNH hook before_cancel của repo như ERPNext thật (Codex #373 v2).
		from vagabond import ho_so_bo_sung as bo
		bo.chan_huy_bu_tru(self)
		NHAT_KY.append("huy " + self.name)
		self.docstatus = 2


def _chay(ho_so, to, ham, giu_cu=None, giu_moi=None, no_ho_so=None, bu_truoc=None, ds_je=None):
	"""Chạy HÀM THẬT của ho_so_bo_sung trên lớp dữ liệu giả.

	to: {tên: tờ HIỆN HÀNH}. giu_cu/giu_moi: {tờ: hồ sơ khác đang giữ} theo
	nguồn cũ (dòng khoản) và mới (bảng tờ nối). no_ho_so: {tài khoản: số Nợ}
	bút toán chi của hồ sơ đã ghi; mặc định đúng từng khoản như _tao_but_toan_tkct.
	bu_truoc: {tài khoản: số Có} các bút toán bù trừ trước."""
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	giu_cu, giu_moi = giu_cu or {}, giu_moi or {}
	if no_ho_so is None:
		no_ho_so = {}
		for r in ho_so.dong:
			no_ho_so[r.tk_no] = no_ho_so.get(r.tk_no, 0) + r.so_tien
	ds_je = [] if ds_je is None else ds_je
	cau = []

	def sql(q, v=None, as_dict=False, **k):
		cau.append(q)
		ql = q.lower()
		tham = v if isinstance(v, (list, tuple)) else (v,)
		if "tabvagabond ho so tt`" in ql and "for update" in ql and "join" not in ql:
			return ()
		if "tabsupplier" in ql:
			goc = tham[0].rstrip("%")
			return [(n, t) for n, t in NCC.items() if t.startswith(goc)]
		if "select docstatus" in ql and "tabpurchase invoice" in ql:
			x = to.get(tham[0])
			return ((x.docstatus, x.vgb_huy),) if x else ()
		if "select grand_total from `tabpurchase invoice`" in ql:
			x = to.get(tham[0])
			return ((x.grand_total,),) if x else ()
		if "tabpurchase invoice" in ql and "credit_to" in ql:
			x = to.get(tham[0])
			return [_C(x)] if x else []
		if "hoa_don_bo_sung in %s" in ql:
			return [(t, g) for t, g in giu_cu.items() if t in tham[0]]
		if "h.hoa_don in %s" in ql:
			return [(t, g) for t, g in giu_moi.items() if t in tham[0]]
		if "tabvagabond ho so tt dong" in ql and "hoa_don_bo_sung = %s" in ql:
			g = giu_cu.get(tham[0])
			return ((g,),) if g else ()
		if "tabvagabond ho so tt hd sau" in ql and "h.hoa_don = %s" in ql:
			g = giu_moi.get(tham[0])
			return [_C(ho_so=g, loai="TK cong ty", tong_hd=0, da_ghi_so=0)] if g else []
		if "from `tabjournal entry` where docstatus = 1 and vgb_ho_so_tt" in ql:
			return (("PKT-CHI",),)
		if "tabjournal entry account" in ql and "parent in" in ql:
			return [(tk, n) for tk, n in no_ho_so.items()]
		if "vgb_bu_tru_ho_so = %s group by" in ql:
			return [(tk, c) for tk, c in (bu_truoc or {}).items()]
		return ()

	def get_value(dt, ten, truong=None, *a, **k):
		if dt == "Supplier":
			return NCC.get(ten)
		if dt == "Account":
			return "Payable" if ten == T331 else ""
		if dt == "Company":
			return "Main - TV"
		return None

	def get_doc(dt, ten=None):
		if dt == "Vagabond Ho So TT":
			return ho_so
		if dt == "Journal Entry":
			return next(j for j in ds_je if j.name == ten)
		raise _Loi("không có %s" % dt)

	db = SimpleNamespace(sql=sql, get_value=get_value, has_column=lambda *a: True, table_exists=lambda *a: True)
	def get_all(dt, filters=None, or_filters=None, fields=None, order_by=None, limit_page_length=0, **k):
		hoi.append((dt, filters, or_filters))
		ra = []
		for x in to.values():
			ncc = (filters or {}).get("supplier")
			if ncc and x.supplier not in ncc[1]:
				continue
			if x.docstatus >= 2:
				continue
			if or_filters:
				q = or_filters["bill_no"][1].strip("%")
				if q not in x.name and q not in (x.bill_no or ""):
					continue
			ra.append(_C(x, supplier_name=x.supplier, bill_date=x.posting_date))
		# get_list kèm luật quyền trả trùng một tờ (ảnh chị Dung 25/09).
		return ra + ra[:1]
	hoi = []
	fr = SimpleNamespace(throw=_throw, db=db, get_doc=get_doc, new_doc=lambda dt: _JE(ds_je), get_all=get_all,
		session=SimpleNamespace(user="dung@vgb"))
	ho_so._truoc = [dict(r) for r in ho_so.hd_sau]
	cu = bo.frappe
	bo.frappe = fr
	try:
		with patch.object(hs, "_kiem"), patch.object(hs, "_cong_ty_chung_tu", return_value=CTY):
			try:
				kq = ham(bo)
				loi = ""
			except _Loi as e:
				kq, loi = None, str(e)
	finally:
		bo.frappe = cu
	return SimpleNamespace(kq=kq, loi=loi, je=ds_je, cau=cau, hs=ho_so, hoi=hoi)


def _mobi(**k):
	return _HoSo("APP.26.09.102", "MOBI-002", [dict(tk_no=T6427, so_tien=778784)], **k)


def _to_mobi():
	return {m: _pi(m, "MOBI-096", t, bill=b) for m, b, t in MOBI}


def _adecco(**k):
	return _HoSo("APP.26.09.009", "ADECCO", [dict(tk_no=T621, so_tien=290659834), dict(tk_no=T6411, so_tien=202911506),
		dict(tk_no=T6421, so_tien=193238819, cho_hoa_don=0)], ngay_tt="2026-09-08", **k)


# ---------------------------------------------------------------- phép thuần

@ca("v530 MST gốc: Mobifone chi nhánh -002 và -096 cùng nhóm; không MST thì chỉ đúng tên")
def _mst():
	from vagabond.hoa_don_sau import mst_goc, cung_nhom
	la("gốc 10 số", mst_goc("0100686209-096"), "0100686209")
	dung("hai chi nhánh cùng nhóm", cung_nhom("MOBI-002", "0100686209-002", "MOBI-096", "0100686209-096"))
	dung("khác MST khác nhóm", not cung_nhom("MOBI-002", "0100686209-002", "KHAC", "0999999999"))
	dung("không MST: khác tên là khác nhóm", not cung_nhom("A", "", "B", ""))
	dung("không MST: cùng tên vẫn cùng nhóm", cung_nhom("A", "", "A", ""))
	la("MST ngắn không nhóm", mst_goc("12345"), "")


@ca("v530 máy gợi ý Mobifone: 6 tờ cộng ĐÚNG 778.784 đ thắng tổ hợp 5 tờ lệch trong ngưỡng")
def _goi_mobi():
	from vagabond.hoa_don_sau import goi_y
	nhieu = [("X1", "3952", 347133), ("X2", "769", 349533), ("X3", "157", 35000), ("X4", "128", 60000)]
	uv = [dict(name=m, bill_no=b, tien=t) for m, b, t in MOBI + nhieu]
	g = goi_y(uv, 778784)
	la("đúng sáu tờ", sorted(g["hoa_don"]), sorted(m for m, _b, _t in MOBI))
	la("tổng khớp đúng", g["tong"], 778784.0)
	dung("không ghi lệch", "lệch" not in g["ly_do"])


@ca("v530 máy gợi ý: một tờ khớp (Adecco), theo số hoá đơn ghi trên khoản (Văn An), hai tờ cùng tiền thì báo còn cách khác")
def _goi_khac():
	from vagabond.hoa_don_sau import goi_y
	g = goi_y([dict(name="HDM-26-09-00134", bill_no="5801", tien=2160000),
		dict(name="HDM-26-09-00135", bill_no="5802", tien=686810159)], 686810159)
	la("Adecco một tờ", g["hoa_don"], ["HDM-26-09-00135"])
	g = goi_y([dict(name="HDM-2026-00424", bill_no="230", tien=1425600),
		dict(name="HDM-26-08-00188", bill_no="262", tien=4730400)], 4730400, ["262"])
	la("Văn An theo số 262", (g["hoa_don"], g["ly_do"]), (["HDM-26-08-00188"], "Khớp số hoá đơn ghi trên khoản chi"))
	g = goi_y([dict(name="SP-AUG", bill_no="9758", tien=920000), dict(name="SP-SEP", bill_no="12515", tien=920000)], 920000)
	dung("hai tháng cùng tiền: gợi ý nhưng báo còn cách khác", g["con_cach_khac"] is True and len(g["hoa_don"]) == 1)
	la("không có gì khớp", goi_y([dict(name="A", bill_no="1", tien=5000)], 778784), None)
	la("đã đủ (còn thiếu 0): không gợi ý", goi_y([dict(name="A", bill_no="1", tien=5000)], 0), None)


@ca("v530 máy gợi ý có ngân sách: 40 tờ lẻ không khớp vẫn trả trong giới hạn, không treo")
def _goi_ngan_sach():
	import time
	from vagabond.hoa_don_sau import goi_y
	uv = [dict(name=str(i), bill_no=str(i), tien=100003 + i * 7919) for i in range(40)]
	t = time.time()
	goi_y(uv, 1)  # dưới ngưỡng: None ngay
	goi_y(uv, 3333333, gioi_han=20000)
	dung("dưới 3 giây", time.time() - t < 3)


@ca("v530 luật nối tờ: nháp và đã ghi sổ còn nợ nối được; đã trả hết, đã huỷ, hồ sơ khác, khác MST chưa xác nhận thì không")
def _loi_noi():
	from vagabond.hoa_don_sau import loi_noi_to
	la("nháp", loi_noi_to(_pi("A", "X", 100, docstatus=0)), "")
	la("đã ghi sổ còn nợ", loi_noi_to(_pi("A", "X", 100)), "")
	dung("đã ghi sổ trả hết", "trả hai lần" in loi_noi_to(_pi("A", "X", 100, con=0)))
	la("hồ sơ trả NCC nối tờ đã trả hết: được (chứng từ công nợ)", loi_noi_to(_pi("A", "X", 100, con=0), tkct=False), "")
	dung("đã huỷ", "huỷ" in loi_noi_to(_pi("A", "X", 100, docstatus=2)))
	dung("nháp đánh dấu huỷ", "đánh dấu huỷ" in loi_noi_to(_pi("A", "X", 100, docstatus=0, huy=1)))
	dung("hồ sơ khác", "APP-9" in loi_noi_to(_pi("A", "X", 100), "APP-9"))
	dung("khác MST chưa xác nhận", "xác nhận" in loi_noi_to(_pi("A", "X", 100), trong_nhom=False))
	la("khác MST đã xác nhận", loi_noi_to(_pi("A", "X", 100), trong_nhom=False, cho_ngoai_nhom=True), "")
	dung("khác công ty", "công ty khác" in loi_noi_to(_pi("A", "X", 100), dung_cong_ty=False))


@ca("v530 kế hoạch bù trừ: Adecco Có đúng 621, 6411, 6421 theo khoản; phần đã dùng đi trước; khoản công nợ bỏ qua")
def _ke_hoach():
	from vagabond.hoa_don_sau import ke_hoach_bu_tru
	k = [dict(idx=1, tk_no=T621, so_tien=290659834), dict(idx=2, tk_no=T6411, so_tien=202911506),
		dict(idx=3, tk_no=T6421, so_tien=193238819)]
	la("Adecco trọn", ke_hoach_bu_tru(k, 0, 686810159),
		(686810159.0, [(T621, 290659834.0), (T6411, 202911506.0), (T6421, 193238819.0)]))
	la("đã dùng 300 triệu: bắt đầu giữa khoản 2", ke_hoach_bu_tru(k, 300000000, 100000000),
		(100000000.0, [(T6411, 100000000.0)]))
	la("tờ lớn hơn chi phí còn lại: chỉ bù phần còn", ke_hoach_bu_tru(k, 686000000, 5000000)[0], 810159.0)
	la("khoản công nợ không bù", ke_hoach_bu_tru([dict(idx=1, tk_no=T331, so_tien=100, cong_no=True)], 0, 100), (0.0, []))


@ca("v530 dòng bút toán: Nợ 331 tham chiếu đúng tờ và đúng NCC trên tờ, Có từng tài khoản; ngày không trước ngày tờ")
def _dong_je():
	from vagabond.hoa_don_sau import dong_but_toan_bu_tru, ngay_bu_tru
	d = dong_but_toan_bu_tru(_pi("HDM-1", "MOBI-096", 159000), 159000, [(T6427, 159000)], "Main - TV")
	la("Nợ 331", (d[0]["account"], d[0]["party"], d[0]["reference_type"], d[0]["reference_name"], d[0]["debit_in_account_currency"]),
		(T331, "MOBI-096", "Purchase Invoice", "HDM-1", 159000))
	la("Có 6427", (d[1]["account"], d[1]["credit_in_account_currency"]), (T6427, 159000))
	la("ngày: chi 04/09 mà tờ 26/08 thì 04/09", ngay_bu_tru("2026-09-04", "2026-08-26"), "2026-09-04")
	la("ngày: chi 08/09 mà tờ vào sổ 10/09 thì 10/09", ngay_bu_tru("2026-09-08", "2026-09-10"), "2026-09-10")


@ca("v530 mức phủ và hợp lệ: đủ khi tổng tờ khớp; còn khoản không chờ hoá đơn hay tờ cũ lệch thì không hợp lệ")
def _phu():
	from vagabond.hoa_don_sau import do_phu, nen_hop_le
	k = [dict(so_tien=290659834, cho_hoa_don=1), dict(so_tien=202911506, cho_hoa_don=1), dict(so_tien=193238819, cho_hoa_don=1)]
	lk = [dict(tien_khop=686810159)]
	la("đủ", do_phu(k, lk)["du"], True)
	dung("hợp lệ", nen_hop_le(k, lk))
	k2 = [dict(k[0]), dict(k[1]), dict(k[2], cho_hoa_don=0)]
	dung("còn khoản không hoá đơn thật: không hợp lệ", not nen_hop_le(k2, lk))
	dung("tờ cũ lệch: không hợp lệ", not nen_hop_le(k, lk, ["khoản 1 lệch"]))
	la("thiếu", do_phu(k, [dict(tien_khop=600000000)])["con_thieu"], 86810159.0)
	p = do_phu([dict(so_tien=100, hoa_don_bo_sung="PI-CU"), dict(so_tien=778784)], [dict(tien_khop=778784)])
	la("khoản đã nối kiểu cũ không tính vào số cần", (p["can"], p["du"]), (778784.0, True))
	dung("chưa nối gì mà còn số cần: không hợp lệ", not nen_hop_le([dict(so_tien=5000, cho_hoa_don=1)], []))


@ca("v530 bảng tờ nối chỉ đổi qua nút: thêm, xoá, sửa tay đều dừng; có cờ thì được; thứ tự không tính")
def _sua_tay():
	from vagabond.hoa_don_sau import loi_sua_hd_sau
	a = dict(hoa_don="A", but_toan="PKT-1", tien_khop=100, bu_tru=100)
	b = dict(hoa_don="B", but_toan="", tien_khop=50, bu_tru=0)
	la("không đổi", loi_sua_hd_sau([a, b], [dict(b), dict(a)]), "")
	dung("xoá dòng", loi_sua_hd_sau([a, b], [b]) != "")
	dung("thêm dòng", loi_sua_hd_sau([a], [a, b]) != "")
	dung("sửa bút toán", loi_sua_hd_sau([a], [dict(a, but_toan="")]) != "")
	la("có cờ nút", loi_sua_hd_sau([a], [], True), "")


@ca("v530 có bút toán bù trừ thì hồ sơ không rời Đã thanh toán (bỏ đối chiếu, mở lại)")
def _bo_tt():
	from vagabond.hoa_don_sau import loi_bo_thanh_toan
	dung("chặn", "HDM-1" in loi_bo_thanh_toan("Da thanh toan", "Da duyet", [dict(hoa_don="HDM-1", but_toan="PKT-1")]))
	la("tờ nháp không bút toán: được", loi_bo_thanh_toan("Da thanh toan", "Da duyet", [dict(hoa_don="A", but_toan="")]), "")
	la("không rời Đã thanh toán", loi_bo_thanh_toan("Da thanh toan", "Da thanh toan", [dict(hoa_don="A", but_toan="P")]), "")


# ---------------------------------------------------------- hàm thật, dữ liệu thật

@ca("v530 Mobifone (hàm thật): 6 tờ đã ghi sổ ở chi nhánh -096 nối vào hồ sơ -002: MỘT bút toán, Nợ 331 sáu dòng, Có 6427 778.784")
def _noi_mobi():
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", json.dumps([m for m, _b, _t in MOBI])))
	la("không lỗi", r.loi, "")
	la("một bút toán", len(r.je), 1)
	je = r.je[0]
	no = [(x["reference_name"], x["party"], x["debit_in_account_currency"]) for x in je.accounts if x.get("debit_in_account_currency")]
	la("Nợ 331 đúng từng tờ, đúng NCC trên tờ", no, [(m, "MOBI-096", t) for m, _b, t in MOBI])
	la("Có 6427 đúng tổng", [(x["account"], x["credit_in_account_currency"]) for x in je.accounts if x.get("credit_in_account_currency")],
		[(T6427, 778784.0)])
	la("ghi sổ", je.docstatus, 1)
	la("đánh dấu bù trừ đúng hồ sơ, không mang ô bút toán chi", (je.vgb_bu_tru_ho_so, getattr(je, "vgb_ho_so_tt", None)),
		("APP.26.09.102", None))
	la("ngày bút toán là ngày chi", je.posting_date, "2026-09-24")
	la("sáu dòng nối cùng bút toán", {x.but_toan for x in r.hs.hd_sau}, {je.name})
	la("hợp lệ tính thuế", (r.hs.loai_cp_thue, r.kq["hop_le"]), ("Chi phi hop le", 1))
	la("lưu một lần", r.hs.luu, 1)
	dung("nhật ký ghi bút toán", je.name in r.hs.ghi_chu[0])


@ca("v530 Adecco (hàm thật): một tờ 686.810.159 phủ ba khoản; khoản 3 chưa đánh dấu thì đánh dấu luôn; Có 621/6411/6421 đúng số")
def _noi_adecco():
	to = {"HDM-26-09-00135": _pi("HDM-26-09-00135", "ADECCO", 686810159, bill="5802", ngay="2026-09-08")}
	r = _chay(_adecco(), to, lambda bo: bo.noi_nhieu("APP.26.09.009", "HDM-26-09-00135"))
	la("không lỗi", r.loi, "")
	la("đánh dấu khoản 3", (r.kq["danh_dau"], r.hs.dong[2].cho_hoa_don), ([3], 1))
	la("Có đúng ba tài khoản hồ sơ đã ghi", [(x["account"], x["credit_in_account_currency"]) for x in r.je[0].accounts if x.get("credit_in_account_currency")],
		[(T621, 290659834.0), (T6411, 202911506.0), (T6421, 193238819.0)])
	la("hợp lệ", r.hs.loai_cp_thue, "Chi phi hop le")


@ca("v530 Văn An (hàm thật): tờ 262 đã ghi sổ 26/08, hồ sơ chi 04/09 ghi Nợ 152: Có 152, ngày 04/09")
def _noi_van_an():
	ho = _HoSo("APP.26.08.016", "VAN-AN", [dict(tk_no=T152, so_tien=4730400, so_hd_ncc="262")], ngay_tt="2026-09-04")
	to = {"HDM-26-08-00188": _pi("HDM-26-08-00188", "VAN-AN", 4730400, bill="262", ngay="2026-08-26")}
	r = _chay(ho, to, lambda bo: bo.noi_nhieu("APP.26.08.016", '["HDM-26-08-00188"]'))
	la("không lỗi", r.loi, "")
	la("Có 152", [(x["account"], x["credit_in_account_currency"]) for x in r.je[0].accounts if x.get("credit_in_account_currency")], [(T152, 4730400.0)])
	la("ngày chi", r.je[0].posting_date, "2026-09-04")


@ca("v530 tờ đã ghi sổ mà hồ sơ CHƯA ghi nhận chi tiền: dừng, không lập bút toán")
def _chua_chi():
	r = _chay(_mobi(tt="Da duyet"), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'))
	dung("dừng, nói rõ", "chưa ghi nhận đã chi" in r.loi)
	la("không bút toán", len(r.je), 0)


@ca("v530 tờ đã ghi sổ ĐÃ trả hết ở chỗ khác: dừng, không bù trừ lần hai")
def _da_tra():
	to = _to_mobi()
	to["HDM-26-09-00093"] = _pi("HDM-26-09-00093", "MOBI-096", 159000, con=0)
	r = _chay(_mobi(), to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'))
	dung("dừng", "trả hai lần" in r.loi)
	la("không bút toán, không lưu", (len(r.je), r.hs.luu), (0, 0))


@ca("v530 tờ khác MST: chưa xác nhận thì dừng; xác nhận thì nối và ghi dấu ngoài nhà cung cấp")
def _ngoai():
	to = {"HDM-K": _pi("HDM-K", "KHAC", 778784, docstatus=0)}
	r = _chay(_mobi(), to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-K"]'))
	dung("dừng khi chưa xác nhận", "xác nhận" in r.loi)
	r = _chay(_mobi(), to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-K"]', ngoai_ncc=1))
	la("nối được, dấu ngoài NCC", (r.loi, r.hs.hd_sau[0].ngoai_ncc), ("", 1))
	dung("nhật ký ghi đã xác nhận", "xác nhận" in r.hs.ghi_chu[0])


@ca("v530 tờ đang ở hồ sơ khác (đọc có khoá, cả nguồn cũ lẫn nguồn mới): dừng, gọi tên hồ sơ kia")
def _ho_so_khac():
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'),
		giu_moi={"HDM-26-09-00093": "APP.26.09.200"})
	dung("nguồn mới", "APP.26.09.200" in r.loi)
	dung("đọc bảng tờ nối bằng câu có khoá", any("hd sau" in q.lower() and "for update" in q.lower() for q in r.cau))
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'),
		giu_cu={"HDM-26-09-00093": "APP.26.08.001"})
	dung("nguồn cũ", "APP.26.08.001" in r.loi)
	la("không bút toán", len(r.je), 0)


@ca("v530 sổ chi của hồ sơ không ghi Nợ đủ tài khoản định Có: dừng, không lập bút toán Có lố")
def _so_khong_du():
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", json.dumps([m for m, _b, _t in MOBI])),
		no_ho_so={T6427: 500000})
	dung("dừng, gọi tên tài khoản", "6427" in r.loi and "không đủ" in r.loi)
	la("không bút toán", len(r.je), 0)
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'),
		bu_truoc={T6427: 700000})
	dung("tính cả bút toán bù trừ trước", "không đủ" in r.loi)


@ca("v530 tờ nháp trước, tờ đã ghi sổ sau: nháp không bút toán, tờ ghi sổ chỉ bù phần chi phí còn lại")
def _nhap_roi_ghi():
	to = {"NHAP": _pi("NHAP", "MOBI-096", 600000, docstatus=0), "GHI": _pi("GHI", "MOBI-096", 178784)}
	r = _chay(_mobi(), to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["NHAP", "GHI"]'))
	la("không lỗi", r.loi, "")
	la("nháp không có bút toán, ghi sổ có", [(x.hoa_don, bool(x.but_toan), x.bu_tru) for x in r.hs.hd_sau],
		[("NHAP", False, 0), ("GHI", True, 178784.0)])
	la("Có 6427 đúng phần còn lại", [x["credit_in_account_currency"] for x in r.je[0].accounts if x.get("credit_in_account_currency")], [178784.0])


@ca("v530 lệch tiền không chặn: nối tờ nhỏ hơn số cần, hồ sơ giữ không hợp lệ, báo còn thiếu")
def _lech():
	to = {"NHO": _pi("NHO", "MOBI-096", 159000, docstatus=0)}
	r = _chay(_mobi(), to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["NHO"]'))
	la("nối được", (r.loi, len(r.hs.hd_sau)), ("", 1))
	la("giữ không hợp lệ", (r.hs.loai_cp_thue, r.kq["hop_le"]), ("Chi phi khong hop le", 0))
	la("còn thiếu", r.kq["phu"]["con_thieu"], 619784.0)


@ca("v530 nối lại tờ đã có trong chính hồ sơ: dừng")
def _trung():
	ho = _mobi(hd_sau=[dict(hoa_don="HDM-26-09-00093", tien_khop=159000, da_ghi_so=1, bu_tru=159000, but_toan="PKT-1")])
	r = _chay(ho, _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", '["HDM-26-09-00093"]'))
	dung("dừng", "chính hồ sơ này" in r.loi)


@ca("v530 hồ sơ trả NCC nối tờ đã ghi sổ: chỉ làm chứng từ, KHÔNG bút toán bù trừ, không đổi loại chi phí")
def _ncc():
	ho = _HoSo("APP.26.09.300", "MOBI-002", [dict(tk_no=T331, so_tien=159000)], loai="NCC", cp="")
	r = _chay(ho, _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.300", '["HDM-26-09-00093"]'))
	la("không lỗi, không bút toán", (r.loi, len(r.je)), ("", 0))
	la("không đổi loại", r.hs.loai_cp_thue, "")


@ca("v530 gỡ (hàm thật): gỡ một tờ Mobifone thì huỷ bút toán chung và gỡ cả nhóm, hồ sơ trở lại không hợp lệ")
def _go_nhom():
	ds_je = []
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", json.dumps([m for m, _b, _t in MOBI])), ds_je=ds_je)
	ho = r.hs
	r2 = _chay(ho, _to_mobi(), lambda bo: bo.go_noi("APP.26.09.102", "HDM-26-09-00287"), ds_je=ds_je)
	la("không lỗi", r2.loi, "")
	la("bút toán huỷ", ds_je[0].docstatus, 2)
	la("gỡ cả sáu", (len(ho.hd_sau), sorted(r2.kq["go"])), (0, sorted(m for m, _b, _t in MOBI)))
	la("về không hợp lệ", (ho.loai_cp_thue, r2.kq["ve_khong_hop_le"]), ("Chi phi khong hop le", 1))


# Codex #373 vòng 1 (inline, commit đầu nhánh): huỷ bút toán trong lúc dòng
# nối còn trỏ vào nó thì Frappe có thể chặn vì còn liên kết ngược. Đọc mã
# Frappe v16 (get_linked_docs): lúc Cancel chỉ chặn liên kết từ chứng từ ĐÃ
# SUBMIT, mà hồ sơ không submit được, nên chưa tái hiện được bằng suy luận;
# không có bench trong phiên. Vẫn đổi thứ tự cho hết phụ thuộc: lưu hồ sơ đã
# gỡ dòng TRƯỚC, huỷ bút toán SAU. Ca bench thu_noi_hd_sau_530 kiểm trên site.
@ca("v530 Codex #373 v1: gỡ lưu hồ sơ (bỏ dòng trỏ vào bút toán) TRƯỚC rồi mới huỷ bút toán")
def _go_thu_tu():
	ds_je = []
	r = _chay(_mobi(), _to_mobi(), lambda bo: bo.noi_nhieu("APP.26.09.102", json.dumps([m for m, _b, _t in MOBI])), ds_je=ds_je)
	del NHAT_KY[:]
	_chay(r.hs, _to_mobi(), lambda bo: bo.go_noi("APP.26.09.102", "HDM-26-09-00093"), ds_je=ds_je)
	la("thứ tự", NHAT_KY, ["luu ", "huy " + ds_je[0].name])


@ca("v530 gỡ tờ nháp: chỉ tờ đó, không huỷ bút toán nào")
def _go_nhap():
	ho = _mobi(hd_sau=[dict(hoa_don="A", tien_khop=100, da_ghi_so=0, bu_tru=0, but_toan=""),
		dict(hoa_don="B", tien_khop=100, da_ghi_so=0, bu_tru=0, but_toan="")])
	r = _chay(ho, {}, lambda bo: bo.go_noi("APP.26.09.102", "A"))
	la("còn B", ([x.hoa_don for x in ho.hd_sau], r.kq["huy_but_toan"]), (["B"], ""))


@ca("v530 kiem_bo_sung (hàm thật): sửa bảng tờ nối trên Desk thì dừng; bỏ đối chiếu khi có bù trừ thì dừng")
def _kiem_bo_sung():
	from vagabond import ho_so_bo_sung as bo
	cu = _mobi(hd_sau=[dict(hoa_don="A", tien_khop=100, da_ghi_so=1, bu_tru=100, but_toan="PKT-1")])
	moi = _mobi()
	moi.get_doc_before_save = lambda: cu
	r = _chay(moi, {}, lambda bo: bo.kiem_bo_sung(moi))
	dung("xoá dòng trên Desk: dừng", "chỉ nối hoặc gỡ bằng nút" in r.loi)
	moi2 = _mobi(tt="Da duyet", hd_sau=[dict(hoa_don="A", tien_khop=100, da_ghi_so=1, bu_tru=100, but_toan="PKT-1")])
	moi2.get_doc_before_save = lambda: cu
	r = _chay(moi2, {}, lambda bo: bo.kiem_bo_sung(moi2))
	dung("bỏ đối chiếu: dừng, gọi tên tờ", "bù trừ" in r.loi and "A" in r.loi)
	moi3 = _mobi(hd_sau=[dict(hoa_don="A", tien_khop=100, da_ghi_so=1, bu_tru=100, but_toan="PKT-1")])
	moi3.get_doc_before_save = lambda: cu
	r = _chay(moi3, {}, lambda bo: bo.kiem_bo_sung(moi3))
	la("lưu thường không đổi bảng: qua", r.loi, "")


@ca("v530 tờ NHÁP nối ở mức hồ sơ TK công ty thì chặn ghi sổ (nguồn thứ hai của ho_so_dang_giu)")
def _chan_ghi_so():
	r = _chay(_mobi(), {}, lambda bo: bo.chan_ghi_so_hd_da_chi(_C(name="HDM-NHAP")), giu_moi={"HDM-NHAP": "APP.26.09.102"})
	dung("chặn, gọi tên hồ sơ", "APP.26.09.102" in r.loi)
	r = _chay(_mobi(), {}, lambda bo: bo.chan_ghi_so_hd_da_chi(_C(name="HDM-NHAP")))
	la("không ai giữ: ghi sổ được", r.loi, "")


@ca("v530 danh sách chọn (hàm thật): lọc cả nhóm MST gốc, hiện tờ đã ghi sổ còn nợ, bỏ tờ đã trả và tờ hồ sơ khác giữ, không trùng, máy gợi ý đúng sáu tờ")
def _ung_vien():
	to = _to_mobi()
	to["DA-TRA"] = _pi("DA-TRA", "MOBI-096", 105570, con=0, bill="999")
	to["GIU"] = _pi("GIU", "MOBI-002", 5000, docstatus=0, bill="888")
	to["KHAC"] = _pi("KHAC", "KHAC", 778784, docstatus=0, bill="777")
	r = _chay(_mobi(tt="Da thanh toan"), to, lambda bo: bo.ung_vien_hoa_don("APP.26.09.102"), giu_moi={"GIU": "APP.26.09.200"})
	la("không lỗi", r.loi, "")
	loc = r.hoi[0][1]
	la("lọc cả hai chi nhánh", sorted(loc["supplier"][1]), ["MOBI-002", "MOBI-096"])
	ten = [x["name"] for x in r.kq["ds"]]
	la("đúng sáu tờ còn nợ, mỗi tờ một lần", sorted(ten), sorted(m for m, _b, _t in MOBI))
	la("nhãn tờ đã ghi sổ", r.kq["ds"][0]["nhan"].startswith("Đã ghi sổ, còn nợ"), True)
	la("máy gợi ý sáu tờ", sorted(r.kq["goi_y"]["hoa_don"]), sorted(m for m, _b, _t in MOBI))
	la("số cần", r.kq["phu"]["can"], 778784.0)
	r = _chay(_mobi(), to, lambda bo: bo.ung_vien_hoa_don("APP.26.09.102", "777", 1))
	la("tìm mọi NCC theo số: ra tờ khác MST, ghi khác nhóm, không gợi ý",
		([(x["name"], x["cung_nhom"]) for x in r.kq["ds"]], r.kq["goi_y"]), ([("KHAC", 0)], None))
	dung("tìm mọi NCC: bỏ lọc nhà cung cấp", "supplier" not in r.hoi[0][1])


@ca("v530 ca hành vi trình duyệt nằm trong cổng")
def _cong():
	import pathlib
	goc = pathlib.Path(__file__).resolve().parents[3]
	dung("cổng chạy hanh_vi/hoa_don_sau_530.js", "hanh_vi/hoa_don_sau_530.js" in (goc / "kiem_truoc_deploy.sh").read_text(encoding="utf-8"))


# Codex #373 vòng 1 trên 33fb7d5 ----------------------------------------------

@ca("v530 Codex #373 v1 F3: sửa tay BẤT KỲ ô đã lưu của dòng tờ nối (tổng tờ, đã ghi sổ, NCC, ngoài NCC...) đều dừng")
def _sua_moi_o():
	from vagabond.hoa_don_sau import loi_sua_hd_sau, TRUONG_HD_SAU
	goc = dict(hoa_don="HDM-1", so_hd_ncc="5802", ncc="ADECCO", tong_hd=686810159, tien_khop=686810159,
		da_ghi_so=1, bu_tru=686810159, but_toan="PKT-1", ngoai_ncc=0, noi_boi="dung@vgb", noi_luc="2026-09-25 22:00:00")
	doi = {"so_hd_ncc": "9999", "ncc": "KHAC", "tong_hd": 1, "tien_khop": 1, "da_ghi_so": 0, "bu_tru": 1,
		"but_toan": "PKT-2", "ngoai_ncc": 1, "noi_boi": "ai@vgb", "noi_luc": "2026-01-01 00:00:00", "hoa_don": "HDM-2"}
	la("đủ mọi ô", sorted(doi), sorted(TRUONG_HD_SAU))
	lot = [k for k, v in doi.items() if not loi_sua_hd_sau([goc], [dict(goc, **{k: v})])]
	la("không ô nào sửa tay lọt", lot, [])
	la("cùng giá trị khác kiểu (số thực, chuỗi ngày dài) không báo nhầm",
		loi_sua_hd_sau([goc], [dict(goc, tong_hd=686810159.0, noi_luc="2026-09-25 22:00:00.123456")]), "")


@ca("v530 Codex #373 v1 F4: bản thể hiện gốc của tờ nối mức hồ sơ vào bộ hồ sơ xuất, ghi nhãn số hoá đơn")
def _xuat_anh():
	from unittest.mock import patch
	from vagabond import ho_so_tt as hs
	d = {"dong": [], "ho_so_dinh_kem": [], "hd_sau": [{"hoa_don": "HDM-26-09-00135", "so_hd_ncc": "5802",
		"scan": [{"file": "F1", "ten": "hd-5802.jpg"}]}]}
	with patch.object(hs, "_anh_b64", return_value="QUJD"):
		anh, bo = hs._gom_anh_ho_so(d)
	la("một ảnh, nhãn số hoá đơn", [a["nhan"] for a in anh], ["Hoá đơn đến sau số 5802 · hd-5802.jpg"])


@ca("v530 Codex #373 v1 F5: sáu tờ chung một bút toán bù trừ thì bộ hồ sơ in bút toán MỘT lần")
def _xuat_je():
	from vagabond.ho_so_tt import trang_hd_sau
	d = {"hd_sau": [{"hoa_don": m, "but_toan": "PKT-9"} for m, _b, _t in MOBI] + [{"hoa_don": "NHAP", "but_toan": ""}]}
	t = trang_hd_sau(d)
	la("bảy trang tờ, một trang bút toán", ([x[0] for x in t].count("Purchase Invoice"), [x[1] for x in t if x[0] == "Journal Entry"]),
		(7, ["PKT-9"]))


# Codex #373 vòng 2 trên 92a437d ----------------------------------------------

@ca("v530 Codex #373 v2 F6: huỷ thẳng bút toán bù trừ (Desk) bị chặn, gọi tên hồ sơ; qua nút Gỡ thì được; bút toán khác không ảnh hưởng")
def _chan_huy_thang():
	import importlib
	from vagabond import ho_so_bo_sung as bo
	je = _C(name="PKT-2026-00100", vgb_bu_tru_ho_so="APP.26.09.009", flags=_C())
	r = _chay(_adecco(), {}, lambda b: b.chan_huy_bu_tru(je))
	dung("chặn, chỉ đường nút Gỡ", "APP.26.09.009" in r.loi and "Gỡ" in r.loi)
	je.flags.vgb_go_noi = True
	la("có cờ Gỡ: qua", _chay(_adecco(), {}, lambda b: b.chan_huy_bu_tru(je)).loi, "")
	la("bút toán thường: qua", _chay(_adecco(), {}, lambda b: b.chan_huy_bu_tru(_C(name="PKT-1", flags=_C()))).loi, "")
	import vagabond.hooks as hk
	dung("hook before_cancel Journal Entry đã đăng ký",
		"vagabond.ho_so_bo_sung.chan_huy_bu_tru" in hk.doc_events["Journal Entry"]["before_cancel"])


@ca("v530 Codex #373 v2 F7: hồ sơ đang hợp lệ mà lần nối sau làm thừa quá ngưỡng thì về KHÔNG hợp lệ; nối đủ lại thì lên hợp lệ")
def _ha_hop_le():
	ho = _mobi(cp="Chi phi hop le", hd_sau=[dict(hoa_don="HDM-A", tien_khop=778784, da_ghi_so=0, bu_tru=0, but_toan="")])
	to = {"THUA": _pi("THUA", "MOBI-096", 5000, docstatus=0)}
	r = _chay(ho, to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["THUA"]'))
	la("nối được", r.loi, "")
	la("về không hợp lệ, báo rõ", (r.hs.loai_cp_thue, r.kq["ve_khong_hop_le"], r.kq["hop_le"]), ("Chi phi khong hop le", 1, 0))
	dung("nhật ký ghi lý do", "không còn khớp" in r.hs.ghi_chu[-1])
	r2 = _chay(r.hs, to, lambda bo: bo.go_noi("APP.26.09.102", "THUA"))
	la("gỡ tờ thừa: phủ đủ lại thì lên hợp lệ lại", r2.hs.loai_cp_thue, "Chi phi hop le")
	ho2 = _mobi(cp="Chi phi hop le", hd_sau=[dict(hoa_don="HDM-A", tien_khop=778784, da_ghi_so=0, bu_tru=0, but_toan="")])
	ho2.dong.append(_C(name="D2", idx=2, hoa_don="PI-GOC", hoa_don_bo_sung="", cho_hoa_don=0, tk_no=T6427, so_tien=100))
	r3 = _chay(ho2, to, lambda bo: bo.noi_nhieu("APP.26.09.102", '["THUA"]'))
	la("hồ sơ có khoản mang hoá đơn gốc riêng: không hạ nhãn", r3.hs.loai_cp_thue, "Chi phi hop le")

