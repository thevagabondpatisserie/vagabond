"""v575: gom hoá đơn của nhiều pháp nhân vào một phiếu đề nghị thanh toán.

Ca thật 05/10/2026, Loan Anh (Sales Manager): Công ty TNHH Oshima's 3 bill và
anh Vũ Oshima 10 bill, cần một phiếu chung 13 bill.

Phần thuần (gom_phap_nhan.py) kiểm thẳng. Phần chạm hệ chạy THẬT
cong_no.tao_phieu trên bản Frappe giả của nen.py, chỉ thay cửa đọc hoá đơn và
cửa lưu phiếu, rồi soi các dòng phiếu được lưu.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem, gia_lap

fr = gia_lap()

from vagabond import gom_phap_nhan as gpn  # noqa: E402
from vagabond.khung.kiem_thu.thu_cong_no_571 import Doi, _nap_cong_no  # noqa: E402

cn = _nap_cong_no()


@ca("v575 thuần: gom một khách như cũ, hoá đơn khách khác bị chặn khi chưa chọn gom chung")
def _():
	la("một khách", gpn.kiem_khach("A", [("H1", "A"), ("H2", "A")]), ("", ["A"]))
	loi, _c = gpn.kiem_khach("A", [("H1", "A"), ("H2", "B")])
	la("chặn khách khác", loi, "Hoá đơn H2 không phải của khách này.")


@ca("v575 thuần: gom chung hai pháp nhân, khách đứng tên phải có hoá đơn trong phiếu")
def _():
	la("Oshima's và anh Vũ", gpn.kiem_khach("VU", [("H1", "OSH"), ("H2", "VU"), ("H3", "VU")], True),
		("", ["OSH", "VU"]))
	loi, _c = gpn.kiem_khach("KHAC", [("H1", "OSH"), ("H2", "VU")], True)
	la("đứng tên khách ngoài cuộc thì chặn", loi, "Khách đứng tên phiếu phải có ít nhất một hoá đơn trong phiếu.")
	la("chưa chọn khách đứng tên", gpn.kiem_khach("", [("H1", "A")], True)[0], "Chưa chọn khách đứng tên phiếu.")
	la("hoá đơn không có khách", gpn.kiem_khach("A", [("H1", "")], True)[0], "Hoá đơn H1 chưa có khách hàng.")


@ca("v575 thuần: chủ nợ ưu tiên ô khách nợ kế toán gán lại; dòng phiếu cũ lấy khách đứng tên")
def _():
	la("có khách nợ", gpn.chu_no("KH-GOC", "KH-NO"), "KH-NO")
	la("không có thì customer", gpn.chu_no("KH-GOC", None), "KH-GOC")
	la("dòng cũ không ghi khách", gpn.khach_dong(None, "A"), "A")
	la("dòng mới giữ khách của nó", gpn.khach_dong("B", "A"), "B")
	ra = gpn.gom_theo_khach([{"khach": "OSH", "so_tien": 1580000}, {"khach": None, "so_tien": 500000},
		{"khach": "OSH", "so_tien": 1480000}], "VU")
	la("cộng theo khách, giữ thứ tự", [(x["khach"], x["so_hd"], x["tien"]) for x in ra],
		[("OSH", 2, 3060000.0), ("VU", 1, 500000.0)])


HD = {
	"HDB-2026-01066": Doi(customer="CUS-OSHIMA", posting_date="2026-08-10", grand_total=1580000.0),
	"HDB-2026-01972": Doi(customer="CUS-OSHIMA", posting_date="2026-08-14", grand_total=1480000.0),
	"HDB-26-09-00201": Doi(customer="CUS-VU", posting_date="2026-09-01", grand_total=500000.0),
	# Kế toán gán lại chủ nợ sau khi ghi sổ: tính là của anh Vũ.
	"HDB-26-09-00202": Doi(customer="KHACH-LE", vgb_khach_no="CUS-VU", posting_date="2026-09-02", grand_total=500000.0),
}


class PhieuGia(Doi):
	def __init__(self):
		super().__init__(dong=[])

	def append(self, k, v):
		self[k].append(Doi(v))

	def insert(self, **k):
		self.name = "CN-1"
		LUU.append(self)


LUU = []


def _chay(**k):
	import json
	moc = (fr.db.get_value, getattr(fr, "new_doc", None), cn._hd_da_gom, cn._sinh_ma_cn, cn.xem_phieu, cn._kiem_quyen_ban)
	pj = getattr(fr, "parse_json", None)
	fr.parse_json = json.loads

	def get_value(dt, ten, truong=None, **kk):
		if dt == "Sales Invoice":
			h = HD.get(ten)
			if not h:
				return None
			r = Doi(h)
			r.setdefault("vgb_khach_no", None)
			r.update(docstatus=1, vgb_pt_thanh_toan="Công nợ", custom_nguon="Pancake")
			return r
		if dt == "Customer":
			return {"CUS-VU": "Anh Vũ Oshima"}.get(ten)
		return None
	fr.db.get_value = get_value
	fr.new_doc = lambda dt: PhieuGia()
	cn._hd_da_gom = lambda: set()
	cn._sinh_ma_cn = lambda: "DNTT-26-10-00001"
	cn.xem_phieu = lambda name: {"name": name}
	cn._kiem_quyen_ban = lambda: None
	del LUU[:]
	try:
		return cn.tao_phieu(**k)
	finally:
		fr.db.get_value, fr.new_doc, cn._hd_da_gom, cn._sinh_ma_cn, cn.xem_phieu, cn._kiem_quyen_ban = moc
		if pj is None:
			del fr.parse_json
		else:
			fr.parse_json = pj


@ca("v575 thật: tao_phieu gom chung Oshima's và anh Vũ, mỗi dòng ghi đúng khách của hoá đơn")
def _():
	import json
	_chay(khach="CUS-VU", hoa_don=json.dumps(list(HD)), nhieu_khach=1)
	la("lưu một phiếu", len(LUU), 1)
	p = LUU[0]
	la("đứng tên anh Vũ", (p.khach, p.ten_khach), ("CUS-VU", "Anh Vũ Oshima"))
	la("khách từng dòng", [(d.hoa_don, d.khach) for d in p.dong], [
		("HDB-2026-01066", "CUS-OSHIMA"), ("HDB-2026-01972", "CUS-OSHIMA"),
		("HDB-26-09-00201", "CUS-VU"), ("HDB-26-09-00202", "CUS-VU")])


@ca("v575 thật: không bật gom chung thì hoá đơn khách khác vẫn bị chặn như cũ")
def _():
	import json
	try:
		_chay(khach="CUS-VU", hoa_don=json.dumps(list(HD)))
		dung("phải chặn", False)
	except fr.ValidationError as e:
		la("câu chặn", str(e), "Hoá đơn HDB-2026-01066 không phải của khách này.")
	la("không lưu gì", len(LUU), 0)
	# Một khách thì vẫn lập được, dòng vẫn ghi khách.
	_chay(khach="CUS-OSHIMA", hoa_don=json.dumps(["HDB-2026-01066", "HDB-2026-01972"]))
	la("gom một khách", [d.khach for d in LUU[0].dong], ["CUS-OSHIMA", "CUS-OSHIMA"])


@ca("v575 thật: gom chung mà đứng tên khách ngoài cuộc thì chặn, không lưu")
def _():
	import json
	nem("chặn", lambda: _chay(khach="CUS-KHAC", hoa_don=json.dumps(list(HD)), nhieu_khach="1"))
	la("không lưu gì", len(LUU), 0)


@ca("v576 thuần (Codex #442): phiếu có hoá đơn của nhiều khách thì tách phiếu thu theo khách")
def _():
	la("một khách", gpn.khop_tung_hoa_don(["A", "A"]), False)
	la("hai khách", gpn.khop_tung_hoa_don(["A", "B"]), True)
	la("bỏ rỗng", gpn.khop_tung_hoa_don(["A", "", None]), False)


@ca("v576 thuần (Codex #442): nhóm phiếu thu chia một giao dịch được tính chung, phiếu lạ vẫn bị hạ")
def _():
	from vagabond import thu_tien as tt

	ds = [{"pe": "APP-1", "tien": 4540000, "ma_gd": "FT1", "da_xac_minh": 1, "nhom": "FT1:ab"},
		{"pe": "APP-2", "tien": 5000000, "ma_gd": "FT1", "da_xac_minh": 1, "nhom": "FT1:ab"},
		{"pe": "APP-9", "tien": 6000000, "ma_gd": "FT1", "da_xac_minh": 1, "nhom": ""}]
	ra = {p["pe"]: p["da_xac_minh"] for p in tt.mot_phieu_moi_giao_dich(ds)}
	la("nhóm 9,54tr thắng phiếu lẻ 6tr", ra, {"APP-1": 1, "APP-2": 1, "APP-9": 0})
	# Không nhóm thì như cũ: hai phiếu cùng giao dịch chỉ phiếu lớn nhất được tính.
	cu = [{"pe": "A", "tien": 1, "ma_gd": "FT2", "da_xac_minh": 1}, {"pe": "B", "tien": 2, "ma_gd": "FT2", "da_xac_minh": 1}]
	la("không nhóm: một phiếu", {p["pe"]: p["da_xac_minh"] for p in tt.mot_phieu_moi_giao_dich(cu)}, {"A": 0, "B": 1})
	la("ứng viên dạng cũ hai phần tử vẫn đọc được",
		{p["pe"]: p["da_xac_minh"] for p in tt.mot_phieu_moi_giao_dich(cu, {"FT2": [("A", 1), ("B", 2)]})}, {"A": 0, "B": 1})


@ca("v576 thuần (Codex #442): chỉ phiếu cùng nhóm được nối tiếp vào giao dịch đã nối")
def _():
	from vagabond import thu_tien as tt

	la("cùng nhóm", tt.cung_nhom_da_noi("G", "APP-2", [("APP-1", "G")]), True)
	la("khác nhóm", tt.cung_nhom_da_noi("G", "APP-2", [("APP-1", "H")]), False)
	la("phiếu đã nối không có nhóm", tt.cung_nhom_da_noi("G", "APP-2", [("APP-1", "")]), False)
	la("phiếu này không nhóm", tt.cung_nhom_da_noi("", "APP-2", [("APP-1", "")]), False)
	la("chưa nối gì thì không áp dụng", tt.cung_nhom_da_noi("G", "APP-2", []), False)
	la("chính nó đã nối", tt.cung_nhom_da_noi("G", "APP-1", [("APP-1", "G")]), False)
	gd = {"docstatus": 1, "deposit": 9540000, "unallocated_amount": 5000000, "allocated_amount": 4540000,
		"so_noi": 1, "noi": [("APP-1", "FT1:ab")], "currency": "VND"}
	pe = {"payment_type": "Receive", "docstatus": 0, "reference_no": "FT1", "paid_amount": 5000000,
		"received_amount": 5000000, "name": "APP-2", "vgb_nhom_gd": "FT1:ab"}
	la("phiếu thứ hai cùng nhóm xác minh được", tt.xac_minh_tien_ve(pe, gd)[0], True)
	pe2 = dict(pe, vgb_nhom_gd="")
	la("phiếu lạ không xác minh", tt.xac_minh_tien_ve(pe2, gd)[0], False)


def _he_phieu(hd):
	"""Frappe giả của thu_cong_no_571, mỗi phiếu thu một tên riêng."""
	from vagabond.khung.kiem_thu.thu_cong_no_571 import PhieuGia, _dung_he

	nk, tra = _dung_he(hd=hd)
	dem = [0]
	lap = []

	class Phieu(PhieuGia):
		doctype = "Payment Entry"

		class meta:
			@staticmethod
			def has_field(f):
				return f == "vgb_nhom_gd"

		def is_new(self):
			return True

		def set(self, k, v):
			self[k] = v

		def insert(self, **k):
			# Hook validate thật của Payment Entry chạy lúc insert (Codex #443 vòng 3).
			from vagabond import thu_tien as tt
			tt.chan_ghi_tay_nhom(self)
			dem[0] += 1
			self.name = "APP-26-10-%04d" % dem[0]
			lap.append(self)
	fr.new_doc = lambda dt: Phieu(nk)
	return nk, tra, lap


@ca("v576 thật (Codex #442): một giao dịch cho Oshima's + anh Vũ lập HAI phiếu thu nháp, đúng khách, chung nhóm")
def _():
	from vagabond import thu_tien as tt
	from vagabond.khung.kiem_thu.thu_cong_no_571 import HD as HD571, GD

	hai = [Doi(HD571[0], customer="CUS-VU"), Doi(HD571[1], customer="CUS-OSHIMA")]
	nk, tra, lap = _he_phieu(hai)
	try:
		nem("không bật tách thì vẫn chặn như cũ", lambda: tt.lap_phieu_thu_theo_gd([h.name for h in hai], GD, 7600000),
			fr.ValidationError)
		la("không lập gì", len(lap), 0)
		kq = tt.lap_phieu_thu_theo_gd([h.name for h in hai], GD, 7600000, tach_khach=True)
	finally:
		tra()
	la("hai phiếu", len(lap), 2)
	la("mỗi phiếu một khách, đúng hoá đơn của khách đó",
		sorted((p.party, tuple(r.reference_name for r in p.references)) for p in lap),
		[("CUS-OSHIMA", ("HDB-26-09-01679",)), ("CUS-VU", ("HDB-26-09-02477",))])
	la("tiền từng phiếu", sorted(p.paid_amount for p in lap), [2850000.0, 4750000.0])
	la("cùng số giao dịch", {p.reference_no for p in lap}, {"FT26277123"})
	dung("chung một mã nhóm khác rỗng", len({p.vgb_nhom_gd for p in lap}) == 1 and lap[0].vgb_nhom_gd)
	la("tổng", kq["tien"], 7600000.0)
	la("trả cả hai tên", kq["cac_pe"], ["APP-26-10-0001", "APP-26-10-0002"])


@ca("v576 thật (Codex #442): một khách thì vẫn MỘT phiếu thu, không gắn nhóm")
def _():
	from vagabond import thu_tien as tt
	from vagabond.khung.kiem_thu.thu_cong_no_571 import HD as HD571, GD

	nk, tra, lap = _he_phieu(list(HD571))
	try:
		tt.lap_phieu_thu_theo_gd([h.name for h in HD571], GD, 7600000, tach_khach=True)
	finally:
		tra()
	la("một phiếu", len(lap), 1)
	la("không nhóm", lap[0].get("vgb_nhom_gd"), None)


@ca("v576 thật (Codex #442): khớp tay giao dịch cho phiếu nhiều pháp nhân lập phiếu thu NHÁP, không đi đường ghi sổ thẳng")
def _():
	from vagabond import thu_tien as tt
	from vagabond.khung.kiem_thu.thu_cong_no_571 import HD as HD571, GD, PhieuNo

	hai = [Doi(HD571[0], customer="CUS-VU"), Doi(HD571[1], customer="CUS-OSHIMA")]
	nk, tra, lap = _he_phieu(hai)
	doc = PhieuNo(name="DNTT-26-10-00009", ma_phieu="DNTT-26-10-00009", trang_thai="Cho thu", khach="CUS-VU",
		tong_tien=7600000.0, da_thu=0.0, flags=Doi(), _nk=nk, dong=[Doi(hoa_don=h.name) for h in hai])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd, "tim": tt.tim_giao_dich,
		"gui": cn._gui_thu_da_nhan, "ghi": cn.ghi_thu_cho_phieu}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT26277123"
	tt.tim_giao_dich = lambda ma: GD
	cn._gui_thu_da_nhan = lambda d: None
	ghi = []
	cn.ghi_thu_cho_phieu = lambda *a, **k: ghi.append(k)
	try:
		kq = cn.khop_tay(doc.name, 7600000, "FT26277123")
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		cn._gui_thu_da_nhan = moc["gui"]
		cn.ghi_thu_cho_phieu = moc["ghi"]
		tra()
	la("không đi đường ghi sổ thẳng từng hoá đơn", ghi, [])
	la("hai phiếu thu nháp", [p.name for p in lap], ["APP-26-10-0001", "APP-26-10-0002"])
	la("không phiếu nào ghi sổ", [x for x in nk if x[0] == "submit"], [])
	la("phiếu đòi nợ đã thu đủ", doc.trang_thai, "Da thu du")
	dung("câu báo nêu cả hai phiếu thu", "APP-26-10-0001" in kq["loi_nhan"] and "APP-26-10-0002" in kq["loi_nhan"])


class _Dong(Doi):
	pass


class _PhieuThu(Doi):
	"""Phiếu thu nháp giả cho ghi_so_phieu_thu: submit, reload, as_dict."""

	def as_dict(self):
		return dict(self)

	def submit(self):
		self.docstatus = 1
		self["_nk"].append(("submit", self.name))

	def reload(self):
		pass


class _GiaoDich(Doi):
	def add_payment_entries(self, ds):
		for d in ds:
			self.payment_entries.append(_Dong(payment_document=d["payment_doctype"], payment_entry=d["payment_name"],
				allocated_amount=0.0))

	def save(self, **k):
		# Như allocate_payment_entries của ERPNext: dòng mới được cấp tiền phiếu.
		for r in self.payment_entries:
			if not r.allocated_amount:
				r.allocated_amount = self["_tien"][r.payment_entry]
		self.allocated_amount = sum(r.allocated_amount for r in self.payment_entries)
		self.unallocated_amount = self.deposit - self.allocated_amount

	def reload(self):
		pass


def _ghi_so(ten, cac_phieu, gdoc):
	"""Chạy THẬT thu_tien.ghi_so_phieu_thu trên Frappe giả; chỉ thay cửa chạm hệ."""
	import sys
	import types
	from vagabond import thu_tien as tt

	nk = gdoc["_nk"]
	ban = types.ModuleType("vagabond.ban_hang")
	ban._kiem_quyen_doc_luu_don = lambda: None
	cu_ban = sys.modules.get("vagabond.ban_hang")
	sys.modules["vagabond.ban_hang"] = ban
	moc = {k: getattr(fr.db, k, None) for k in ("exists", "savepoint", "rollback")}
	moc.update(get_doc=fr.get_doc, get_all=fr.get_all, clear=getattr(fr, "clear_messages", None))
	mtt = {k: getattr(tt, k) for k in ("_thuoc_tap_unc", "_so_tep_unc", "_gd_theo_so", "la_ke_toan", "_ghi_vet_thu")}

	def gd_theo_so(cac):
		noi = [(r.payment_entry, cac_phieu[r.payment_entry].get("vgb_nhom_gd") or "") for r in gdoc.payment_entries]
		g = {"name": gdoc.name, "reference_number": "FT1", "docstatus": 1, "deposit": gdoc.deposit,
			"withdrawal": 0, "currency": "VND", "unallocated_amount": gdoc.unallocated_amount,
			"allocated_amount": gdoc.allocated_amount, "so_noi": len(noi), "noi": noi, "tk": "", "cty": ""}
		return {"FT1": g}

	fr.db.exists = lambda *a, **k: True
	fr.db.savepoint = lambda *a, **k: None
	fr.db.rollback = lambda *a, **k: nk.append(("lui",))
	fr.clear_messages = lambda: None
	fr.get_doc = lambda dt, ten_, **k: gdoc if dt == "Bank Transaction" else cac_phieu[ten_]
	fr.get_all = lambda dt, filters=None, **k: [Doi(name=n, vgb_nhom_gd=cac_phieu[n].get("vgb_nhom_gd"))
		for n in (filters or {}).get("name", ["in", []])[1] if n in cac_phieu]
	tt._thuoc_tap_unc = lambda d: True
	tt._so_tep_unc = lambda *a: 1
	tt._gd_theo_so = gd_theo_so
	tt.la_ke_toan = lambda: True
	tt._ghi_vet_thu = lambda *a, **k: None
	try:
		return tt.ghi_so_phieu_thu(ten)
	finally:
		for k in ("exists", "savepoint", "rollback"):
			setattr(fr.db, k, moc[k])
		fr.get_doc, fr.get_all = moc["get_doc"], moc["get_all"]
		if moc["clear"] is None:
			del fr.clear_messages
		else:
			fr.clear_messages = moc["clear"]
		for k, v in mtt.items():
			setattr(tt, k, v)
		if cu_ban is None:
			sys.modules.pop("vagabond.ban_hang", None)
		else:
			sys.modules["vagabond.ban_hang"] = cu_ban


def _bo_phieu(nhom2):
	nk = []
	def pt(ten, tien, nhom):
		return _PhieuThu(name=ten, docstatus=0, payment_type="Receive", party_type="Customer", reference_no="FT1",
			paid_amount=tien, received_amount=tien, vgb_nhom_gd=nhom, vgb_thu_unc="", flags=Doi(), _nk=nk)
	cac = {"APP-1": pt("APP-1", 4540000.0, "FT1:ab"), "APP-2": pt("APP-2", 5000000.0, nhom2)}
	g = _GiaoDich(name="BT-1", deposit=9540000.0, allocated_amount=0.0, unallocated_amount=9540000.0,
		payment_entries=[], _nk=nk, _tien={"APP-1": 4540000.0, "APP-2": 5000000.0})
	return nk, cac, g


@ca("v576 thật (Codex #442): ghi sổ lần lượt hai phiếu thu cùng nhóm, giao dịch nối đủ cả hai")
def _():
	nk, cac, g = _bo_phieu("FT1:ab")
	la("phiếu 1", _ghi_so("APP-1", cac, g).get("ok"), 1)
	la("phiếu 2 cùng nhóm nối tiếp", _ghi_so("APP-2", cac, g).get("ok"), 1)
	la("giao dịch nối cả hai", [r.payment_entry for r in g.payment_entries], ["APP-1", "APP-2"])
	la("giao dịch hết tiền chưa phân bổ", g.unallocated_amount, 0.0)


@ca("v576 thật (Codex #442): phiếu KHÁC nhóm không được nối vào giao dịch đã nối, như luật cũ")
def _():
	nk, cac, g = _bo_phieu("")
	la("phiếu 1", _ghi_so("APP-1", cac, g).get("ok"), 1)
	nem("phiếu lạ bị chặn", lambda: _ghi_so("APP-2", cac, g), fr.ValidationError)
	la("phiếu lạ vẫn nháp", cac["APP-2"].docstatus, 0)
	la("giao dịch chỉ nối phiếu 1", [r.payment_entry for r in g.payment_entries], ["APP-1"])


def _nhap_he(bang_pe, ref_hd, g):
	"""Frappe giả cho thu_tien.phieu_thu_nhap: bảng phiếu thu, phân bổ, giao dịch."""
	from vagabond import thu_tien as tt

	def get_all(dt, filters=None, fields=None, **k):
		f = filters or {}
		if dt == "Payment Entry Reference":
			if "reference_name" in f:
				ten = f["reference_name"][1]
				return [Doi(parent=pe, reference_name=hd, allocated_amount=t) for pe, hd, t in ref_hd if hd in ten
					and bang_pe[pe]["docstatus"] == f.get("docstatus", bang_pe[pe]["docstatus"])]
			ten = f["parent"][1]
			return [Doi(parent=pe, reference_name=hd, allocated_amount=t) for pe, hd, t in ref_hd if pe in ten]
		if dt == "Payment Entry":
			ra = []
			for ten, p in bang_pe.items():
				if "name" in f and ten not in f["name"][1]:
					continue
				if "reference_no" in f and isinstance(f["reference_no"], list) and f["reference_no"][0] == "in" \
						and p["reference_no"] not in f["reference_no"][1]:
					continue
				ds = f.get("docstatus")
				if isinstance(ds, list) and not p["docstatus"] < ds[1]:
					continue
				if isinstance(ds, int) and p["docstatus"] != ds:
					continue
				ra.append(Doi(dict(p, name=ten)))
			return ra
		return []
	moc = (fr.get_all, tt._gd_theo_so)
	fr.get_all = get_all
	tt._gd_theo_so = lambda cac: {"FT1": g}
	return moc


@ca("v576 thật (Codex #443 vòng 3): phiếu còn lại của nhóm vẫn hiện ở Tiền đã về sau khi phiếu đầu ghi sổ, phiếu lẻ cũ không chen lên")
def _():
	from vagabond import thu_tien as tt

	chung = dict(payment_type="Receive", party_type="Customer", reference_no="FT1", paid_to="", company="",
		vgb_thu_unc="", party="X", party_name="X", posting_date="2026-10-05")
	bang = {
		"APP-1": dict(chung, docstatus=1, paid_amount=4540000.0, received_amount=4540000.0, vgb_nhom_gd="FT1:ab"),
		"APP-2": dict(chung, docstatus=0, paid_amount=5000000.0, received_amount=5000000.0, vgb_nhom_gd="FT1:ab"),
		# Phiếu lẻ cũ 6tr: lớn hơn phần còn lại của nhóm (5tr), nhỏ hơn cả nhóm (9,54tr).
		"APP-9": dict(chung, docstatus=0, paid_amount=6000000.0, received_amount=6000000.0, vgb_nhom_gd=""),
	}
	ref = [("APP-1", "HD-OSH", 4540000.0), ("APP-2", "HD-VU", 5000000.0), ("APP-9", "HD-CU", 6000000.0)]
	g = {"name": "BT-1", "reference_number": "FT1", "docstatus": 1, "deposit": 9540000.0, "withdrawal": 0,
		"currency": "VND", "unallocated_amount": 5000000.0, "allocated_amount": 4540000.0, "so_noi": 1,
		"noi": [("APP-1", "FT1:ab")], "tk": "", "cty": ""}
	moc = _nhap_he(bang, ref, g)
	try:
		ds = tt.phieu_thu_nhap(cac_si=["HD-VU"])
	finally:
		fr.get_all, tt._gd_theo_so = moc
	la("phiếu APP-2 xác minh được", [(p["pe"], p["da_xac_minh"]) for p in ds], [("APP-2", 1)])


@ca("v576 (Codex #443 vòng 3): ô nhóm chia giao dịch chỉ máy ghi, Desk/API gửi vào thì bị bỏ")
def _():
	from vagabond import thu_tien as tt

	la("máy ghi", tt.nhom_giu(None, "G", True), "G")
	la("ngoài gửi, phiếu mới", tt.nhom_giu(None, "G", False), None)
	la("ngoài gửi, đã có", tt.nhom_giu("G", "H", False), "G")
	la("ngoài xoá", tt.nhom_giu("G", None, False), "G")

	class _Pe(Doi):
		doctype = "Payment Entry"

		class meta:
			@staticmethod
			def has_field(f):
				return f == "vgb_nhom_gd"

		def is_new(self):
			return self["_moi"]

		def set(self, k, v):
			self[k] = v
	cu = fr.db.get_value
	fr.db.get_value = lambda dt, ten, truong: {"APP-5": None, "APP-6": "FT1:ab"}.get(ten)
	try:
		gia = _Pe(name="APP-5", vgb_nhom_gd="FT1:ab", flags=Doi(), _moi=True)
		tt.chan_ghi_tay_nhom(gia)
		la("phiếu mới tự chế mang nhóm người khác: bị bỏ", gia.get("vgb_nhom_gd"), None)
		sua = _Pe(name="APP-6", vgb_nhom_gd="KHAC", flags=Doi(), _moi=False)
		tt.chan_ghi_tay_nhom(sua)
		la("sửa tay phiếu đang lưu: trả về giá trị máy ghi", sua.get("vgb_nhom_gd"), "FT1:ab")
		may = _Pe(name="APP-7", vgb_nhom_gd="FT1:cd", flags=Doi({tt.CO_MAY_GHI_NHOM: True}), _moi=True)
		tt.chan_ghi_tay_nhom(may)
		la("máy ghi thì giữ", may.get("vgb_nhom_gd"), "FT1:cd")
	finally:
		fr.db.get_value = cu
	import os
	h = open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
		"hooks.py"), encoding="utf-8").read()
	dung("hook đã đăng ký", '"vagabond.thu_tien.chan_ghi_tay_nhom"' in h)
