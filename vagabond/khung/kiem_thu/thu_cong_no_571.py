"""v571: khớp tay một giao dịch trả GỘP nhiều hoá đơn, và quyền lập phiếu thu.

Ca thật 04/10/2026, Loan Anh (Sales Manager) báo:
  * gộp hai hoá đơn của chị Hồng (HDB-26-09-01679 4.750.000, HDB-26-09-02477
    2.850.000) vào phiếu DNTT-26-10-00002, khớp tay một giao dịch 7.600.000,
    máy báo "Công nợ đã sạch" mà tab Đang nợ vẫn hiện đủ hai hoá đơn; tab
    Phiếu đã gửi ghi "Đã thu đủ" mà dòng dưới "còn 7.600.000 đ".
  * bấm "Khách đã chuyển tiền" cho Ms.Quyên thì bị chặn "không có quyền truy
    cập doctype ... Phiếu thu/chi".

Nhật ký lỗi site thật (Error Log "cong_no: sinh chung tu thu tien", 19:38
04/10/2026): ERPNext payment_entry.get_account_details tự gọi
frappe.has_permission("Payment Entry", throw=True), nên ignore_permissions
trên insert không qua được.

Các ca dưới đây CHẠY THẬT khop_tay và lap_phieu_thu_theo_gd trên bản Frappe
giả của nen.py, thay đúng những cửa chạm hệ, rồi soi thứ tự việc xảy ra.
Không dò chuỗi trong mã nguồn (CLAUDE.md điều 16).
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem, gia_lap

fr = gia_lap()

import sys  # noqa: E402
import types  # noqa: E402

from vagabond import thu_tien as tt  # noqa: E402


def _nap_cong_no():
	"""Nạp cong_no mà KHÔNG kéo ban_hang (ban_hang import requests).

	Máy CI tay không, không có requests (bài học 20/08/2026). cong_no chỉ cần
	đúng một tên từ ban_hang là cửa quyền _kiem_quyen_ban, mà ca kiểm nào cũng
	thay cửa đó. Nên đặt một ban_hang giả TRONG LÚC nạp rồi gỡ ngay, để các ca
	khác vẫn nạp ban_hang thật nếu máy có.
	"""
	if "vagabond.cong_no" in sys.modules:
		return sys.modules["vagabond.cong_no"]
	cu = sys.modules.get("vagabond.ban_hang")
	if cu is None:
		gia = types.ModuleType("vagabond.ban_hang")
		gia._kiem_quyen_ban = lambda: None
		sys.modules["vagabond.ban_hang"] = gia
	try:
		from vagabond import cong_no
	finally:
		if cu is None:
			sys.modules.pop("vagabond.ban_hang", None)
			import vagabond
			if getattr(vagabond, "ban_hang", None) is not None and not hasattr(vagabond.ban_hang, "__file__"):
				delattr(vagabond, "ban_hang")
	return cong_no


cn = _nap_cong_no()


class Doi(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


class PhieuGia(Doi):
	"""Payment Entry giả: ghi lại ai đang đăng nhập lúc từng bước chạy."""

	def __init__(self, nhat_ky):
		super().__init__(references=[], flags=Doi())
		self["_nk"] = nhat_ky

	def append(self, k, v):
		self[k].append(Doi(v))

	def setup_party_account_field(self):
		pass

	def set_missing_values(self):
		# Đúng như ERPNext: bước này tự hỏi quyền đọc Payment Entry.
		self["_nk"].append(("set_missing_values", fr.session.user))
		if fr.session.user != "Administrator":
			raise fr.ValidationError("khong co quyen Payment Entry")

	def insert(self, **k):
		self["_nk"].append(("insert", fr.session.user))
		self.name = "APP-26-10-0001"

	def submit(self):
		self["_nk"].append(("submit", fr.session.user))


HD = [
	Doi(name="HDB-26-09-02477", customer="KH-HONG", company="TV", outstanding_amount=2850000.0,
		posting_date="2026-09-13", grand_total=2850000.0, due_date="2026-09-13"),
	Doi(name="HDB-26-09-01679", customer="KH-HONG", company="TV", outstanding_amount=4750000.0,
		posting_date="2026-09-10", grand_total=4750000.0, due_date="2026-09-10"),
]

GD = Doi(name="BT-1", reference_number="FT26277123", docstatus=1, deposit=7600000.0,
	currency="VND", payment_entries=[], unallocated_amount=7600000.0, bank_account="MB-TV",
	date="2026-10-04")


def _dung_he(hd=None, pe_cu=None, nhap=None, bank=None, bt=None):
	"""Thay các cửa chạm hệ của bản Frappe giả. Trả nhật ký và hàm trả lại."""
	nk = []
	cu = {}
	moc = {
		"get_all": fr.get_all, "new_doc": getattr(fr, "new_doc", None),
		"set_user": getattr(fr, "set_user", None), "user": fr.session.user,
		"get_value": fr.db.get_value, "exists": fr.db.exists,
	}
	hd = HD if hd is None else hd

	def get_all(dt, filters=None, **k):
		if dt == "Vagabond Cong No Dong":
			return [Doi(hoa_don=h.name) for h in hd]
		if dt == "Sales Invoice":
			ten = (filters or {}).get("name")
			ds = [h for h in hd if not ten or h.name in ten[1]]
			if "posting_date" in str(k.get("order_by") or ""):
				ds = sorted(ds, key=lambda h: str(h.posting_date))
			if k.get("pluck") == "name":
				return [h.name for h in ds if h.outstanding_amount > 0.5]
			return [Doi(h) for h in ds]
		if dt == "Payment Entry":
			return list(pe_cu or [])
		if dt == "Bank Transaction":
			# bt: {tên giao dịch: tiền về}. Mặc định giao dịch GD 7,6tr.
			bang = {"BT-1": 7600000.0} if bt is None else bt
			ten = ((filters or {}).get("name") or ["in", []])[1]
			return [Doi(name=n, deposit=v, withdrawal=0.0) for n, v in bang.items() if n in ten]
		if dt == "Payment Entry Reference":
			# nhap: list Doi(reference_name, allocated_amount) cua phieu thu NHAP.
			# Phieu thu DA GHI SO (docstatus 1) ca kiem nay khong dung toi.
			if ((filters or {}).get("docstatus") == 1):
				return []
			nk.append(("doc_nhap",))
			ds = list(nhap or [])
			if k.get("pluck"):
				return [r.get(k["pluck"]) for r in ds]
			return [Doi(r) for r in ds]
		return []

	def set_user(u):
		nk.append(("set_user", u))
		fr.session.user = u

	fr.get_all = get_all
	fr.new_doc = lambda dt: PhieuGia(nk)
	fr.set_user = set_user
	def get_value(dt, ten, *a, **k):
		if k.get("for_update"):
			nk.append(("khoa", dt, ten))
		if dt == "Bank Account":
			return Doi(bank or {"account": "1121 - MB - TV", "company": "TV", "is_company_account": 1})
		return None
	fr.db.get_value = get_value
	fr.db.exists = lambda *a, **k: True
	fr.session.user = "ntla.3008@gmail.com"
	fr.generate_hash = lambda length=8, **k: "x" * length
	tt._ghi_vet_thu = lambda *a, **k: nk.append(("vet", fr.session.user))
	# Bảng phiếu thu nháp kèm kết quả xác minh: mỗi dòng nhap là một phân bổ,
	# gom theo `pe` (mặc định mỗi dòng một phiếu), `xm` mặc định 1 (đã xác minh).
	moc["ptn"] = tt.phieu_thu_nhap

	def phieu_thu_nhap(cac_si=None, **k):
		theo = {}
		for i, r in enumerate(nhap or []):
			pe = r.get("pe") or "PE-%d" % i
			p = theo.setdefault(pe, {"pe": pe, "da_xac_minh": 1 if r.get("xm", 1) else 0,
				"ma_gd": r.get("ma_gd") or "FT-" + pe, "gd": "", "hd": []})
			p["hd"].append((r.reference_name, r.allocated_amount))
		return list(theo.values())
	tt.phieu_thu_nhap = phieu_thu_nhap

	def tra():
		fr.get_all = moc["get_all"]
		fr.new_doc = moc["new_doc"]
		fr.set_user = moc["set_user"]
		fr.session.user = moc["user"]
		fr.db.get_value = moc["get_value"]
		fr.db.exists = moc["exists"]
		tt.phieu_thu_nhap = moc["ptn"]
	cu["tra"] = tra
	return nk, tra


@ca("v571: chia tiền gộp cho hoá đơn CŨ trước, không chia quá số còn nợ")
def _():
	ds = [{"name": "B", "con_no": 2850000, "ngay": "2026-09-13"},
		{"name": "A", "con_no": 4750000, "ngay": "2026-09-10"}]
	la("đủ tiền", tt.chia_tien_cho_hd(7600000, ds), [("A", 4750000), ("B", 2850000)])
	la("thiếu tiền: tờ cũ đủ, tờ mới phần còn lại", tt.chia_tien_cho_hd(5000000, ds),
		[("A", 4750000), ("B", 250000)])
	la("thừa tiền: không gán phần dư", tt.chia_tien_cho_hd(9000000, ds),
		[("A", 4750000), ("B", 2850000)])
	la("không tiền", tt.chia_tien_cho_hd(0, ds), [])


@ca("v571: lập MỘT phiếu thu nháp cho cả hai hoá đơn chị Hồng, mang mã giao dịch")
def _():
	nk, tra = _dung_he()
	try:
		kq = tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000, "Theo phiếu DNTT-26-10-00002.")
	finally:
		tra()
	la("một phiếu", kq["pe"], "APP-26-10-0001")
	la("phân bổ cũ trước", kq["hd"], [("HDB-26-09-01679", 4750000.0), ("HDB-26-09-02477", 2850000.0)])
	la("mã giao dịch", kq["ma_gd"], "FT26277123")
	la("không ghi sổ, chỉ insert", [x[0] for x in nk if x[0] in ("insert", "submit")], ["insert"])


@ca("v571: Sales Manager lập được phiếu: bước hỏi quyền chạy bằng Administrator rồi TRẢ LẠI người gọi")
def _():
	nk, tra = _dung_he()
	try:
		tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000)
		sau = fr.session.user
	finally:
		tra()
	la("set_missing_values chạy quyền hệ thống", [x[1] for x in nk if x[0] == "set_missing_values"], ["Administrator"])
	la("trả lại đúng người gọi", sau, "ntla.3008@gmail.com")
	la("vết ghi bằng tên người gọi", [x[1] for x in nk if x[0] == "vet"], ["ntla.3008@gmail.com"])


@ca("v571: lỗi giữa chừng vẫn TRẢ LẠI người gọi, không để request chạy quyền Administrator")
def _():
	nk, tra = _dung_he()
	try:
		def hong():
			with tt.nang_quyen_lap_phieu():
				raise RuntimeError("hong giua chung")
		nem("lỗi được ném ra", hong, RuntimeError)
		sau = fr.session.user
	finally:
		tra()
	la("đã trả lại", sau, "ntla.3008@gmail.com")


@ca("v571: giao dịch đã có phiếu thu, hoá đơn của hai mã khách, tài khoản lạ thì CHẶN, không lập gì")
def _():
	nk, tra = _dung_he(pe_cu=["APP-CU"])
	try:
		nem("đã có phiếu", lambda: tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000), fr.ValidationError)
	finally:
		tra()
	la("không insert", [x for x in nk if x[0] == "insert"], [])
	hai = [Doi(HD[0]), Doi(HD[1], customer="KH-KHAC")]
	nk, tra = _dung_he(hd=hai)
	try:
		nem("hai mã khách", lambda: tt.lap_phieu_thu_theo_gd([h.name for h in hai], GD, 7600000), fr.ValidationError)
	finally:
		tra()
	la("không insert", [x for x in nk if x[0] == "insert"], [])
	nk, tra = _dung_he(bank={"account": "1121", "company": "CTY-KHAC", "is_company_account": 1})
	try:
		nem("tài khoản công ty khác", lambda: tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000), fr.ValidationError)
	finally:
		tra()


@ca("v571 vòng 9: tiền đã nhận CỘNG DỒN số đã ghi và giao dịch SePay chưa ghi, không quá tổng")
def _():
	la("ghi tay 2tr + SePay 5,6tr", cn.tong_da_nhan(7600000, 2000000, {"BT-S": 5600000}), 7600000.0)
	la("chưa nhận gì", cn.tong_da_nhan(7600000, 0, {}), 0.0)
	la("không quá tổng phiếu", cn.tong_da_nhan(7600000, 5000000, {"BT-S": 5600000}), 7600000.0)


@ca("v571: câu báo khớp tay nói ĐÚNG việc đã xảy ra, không báo sạch khi phiếu thu hỏng")
def _():
	c = cn.cau_bao_khop_tay("DNTT-26-10-00002", 7600000, "Da thu du",
		{"pe": "APP-1", "hd": [("A", 1), ("B", 2)], "ma_gd": "FT1"}, [])
	dung("có tên phiếu thu", "APP-1" in c)
	dung("nói chuyển sang Tiền đã về", "Tiền đã về" in c)
	dung("không nói đã sạch", "đã sạch" not in c)
	c = cn.cau_bao_khop_tay("DNTT-26-10-00002", 7600000, "Da thu du", None, ["A: khong co quyen"])
	dung("nói CHƯA lập được", "CHƯA lập được" in c)
	dung("không nói đã sạch", "đã sạch" not in c)


class PhieuNo(Doi):
	def save(self, **k):
		self["_nk"].append(("luu_phieu", self.trang_thai))

	def add_comment(self, *a, **k):
		self["_nk"].append(("binh_luan", a[1] if len(a) > 1 else ""))


@ca("v571: khop_tay lập phiếu thu TRƯỚC, hỏng thì phiếu đòi nợ KHÔNG bị đánh dấu đã thu")
def _():
	nhap = []
	nk, tra = _dung_he(nhap=nhap)
	doc = PhieuNo(name="DNTT-26-10-00002", ma_phieu="DNTT-26-10-00002", trang_thai="Cho thu",
		tong_tien=7600000.0, da_thu=0.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan,
		"ghi": cn.ghi_thu_cho_phieu}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT26277123"
	tt.tim_giao_dich = lambda ma: GD
	cn._gui_thu_da_nhan = lambda d: None
	cn.ghi_thu_cho_phieu = lambda *a, **k: nk.append(("ghi_thu_cu",))

	def lap_hong(*a, **k):
		nk.append(("lap",))
		raise fr.ValidationError("Giao dịch FT26277123 đã nối với chứng từ khác.")
	tt.lap_phieu_thu_theo_gd = lap_hong
	try:
		nem("lỗi lập phiếu được báo ra", lambda: cn.khop_tay(doc.name, 7600000, "FT26277123"), fr.ValidationError)
		la("phiếu đòi nợ KHÔNG lưu", [x for x in nk if x[0] == "luu_phieu"], [])
		la("vẫn Chờ thu", doc.trang_thai, "Cho thu")

		def lap_ok(cac_si, g, so, gc=""):
			nk.append(("lap", tuple(cac_si)))
			# Phiếu nháp thật phủ đủ hai tờ: da_thu được tính lại từ đây.
			nhap.extend(Doi(reference_name=h.name, allocated_amount=h.outstanding_amount) for h in HD)
			return {"pe": "APP-1", "hd": [(s, 1) for s in cac_si], "ma_gd": "FT26277123", "tien": 7600000.0}
		tt.lap_phieu_thu_theo_gd = lap_ok
		kq = cn.khop_tay(doc.name, 7600000, "FT26277123")
		buoc = [x[0] for x in nk]
		dung("lập trước khi lưu phiếu", buoc.index("lap", 1) < buoc.index("luu_phieu"))
		la("lập cho CẢ HAI hoá đơn", [x for x in nk if x[0] == "lap" and len(x) > 1][0][1],
			("HDB-26-09-02477", "HDB-26-09-01679"))
		la("không đi lối cũ từng hoá đơn", [x for x in nk if x[0] == "ghi_thu_cu"], [])
		la("đã thu đủ", doc.trang_thai, "Da thu du")
		la("trả tên phiếu thu", kq["pe"], "APP-1")
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		cn.ghi_thu_cho_phieu = moc["ghi"]
		tra()


@ca("v571: phiếu ĐÃ thu đủ mà hoá đơn chưa có phiếu thu thì khớp lại được (ca DNTT-26-10-00002)")
def _():
	nk, tra = _dung_he()
	doc = PhieuNo(name="DNTT-26-10-00002", ma_phieu="DNTT-26-10-00002", trang_thai="Da thu du",
		tong_tien=7600000.0, da_thu=7600000.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT26277123"
	tt.tim_giao_dich = lambda ma: GD
	cn._gui_thu_da_nhan = lambda d: nk.append(("gui_thu",))
	tt.lap_phieu_thu_theo_gd = lambda cac_si, g, so, gc="": (
		nk.append(("lap", tuple(cac_si))) or {"pe": "APP-1", "hd": [], "ma_gd": "FT"})
	try:
		kq = cn.khop_tay(doc.name, 7600000, "FT26277123")
		la("đã lập phiếu thu", kq["pe"], "APP-1")
		la("không gửi lại thư báo nhận tiền lần hai", [x for x in nk if x[0] == "gui_thu"], [])
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		tra()


@ca("Codex #437 F1: chọn giao dịch mà không nạp được thì DỪNG, không đánh dấu đã thu, không đi lối cũ")
def _():
	# Trên 30e2b9d: tim_giao_dich trả None (mã gõ nhầm hay giao dịch vừa huỷ)
	# thì khop_tay coi như không chọn giao dịch: phiếu thành Da thu du và đi
	# ghi_thu_cho_phieu từng hoá đơn. Đo được: buoc = [luu_phieu, ghi_thu_cu].
	nk, tra = _dung_he()
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Cho thu",
		tong_tien=7600000.0, da_thu=0.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "ghi": cn.ghi_thu_cho_phieu}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT-SAI"
	tt.tim_giao_dich = lambda ma: None
	cn.ghi_thu_cho_phieu = lambda *a, **k: nk.append(("ghi_thu_cu",))
	try:
		nem("báo lỗi", lambda: cn.khop_tay(doc.name, 7600000, "FT-SAI"), fr.ValidationError)
		la("không lưu phiếu", [x for x in nk if x[0] == "luu_phieu"], [])
		la("không đi lối cũ", [x for x in nk if x[0] == "ghi_thu_cu"], [])
		la("vẫn Chờ thu", doc.trang_thai, "Cho thu")
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		cn.ghi_thu_cho_phieu = moc["ghi"]
		tra()


@ca("Codex #437 vòng 3: phần nợ chưa phủ = dư nợ trừ phân bổ phiếu thu NHÁP, không phải có phiếu là phủ đủ")
def _():
	la("trả góp 2tr trên tờ 4,75tr", tt.con_chua_phu(4750000, 2000000), 2750000.0)
	la("chưa có phiếu nháp", tt.con_chua_phu(2850000, None), 2850000.0)
	la("nháp phủ dư thì 0", tt.con_chua_phu(1000000, 1500000), 0.0)


@ca("Codex #437 vòng 3: khách trả góp, lần chuyển sau chia vào CẢ phần còn lại của tờ đã có phiếu nháp")
def _():
	# Trên 3c40e63: tờ 4,75tr đã có phiếu nháp 2tr bị loại hẳn, giao dịch
	# 5,6tr chỉ chia 2,85tr vào tờ kia, 2,75tr bơ vơ.
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0)]
	gd = Doi(GD, deposit=5600000.0, unallocated_amount=5600000.0)
	nk, tra = _dung_he(nhap=nhap)
	try:
		kq = tt.lap_phieu_thu_theo_gd([h.name for h in HD], gd, 5600000)
	finally:
		tra()
	la("chia đủ hai tờ", kq["hd"], [("HDB-26-09-01679", 2750000.0), ("HDB-26-09-02477", 2850000.0)])
	la("không bơ vơ đồng nào", kq["tien"], 5600000.0)


@ca("Codex #437 vòng 3: khop_tay đưa CẢ tờ đã có phiếu nháp một phần sang bước lập phiếu")
def _():
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0)]
	nk, tra = _dung_he(nhap=nhap)
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Thu thieu",
		tong_tien=7600000.0, da_thu=2000000.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT2"
	tt.tim_giao_dich = lambda ma: GD
	cn._gui_thu_da_nhan = lambda d: None
	tt.lap_phieu_thu_theo_gd = lambda cac_si, g, so, gc="": (
		nk.append(("lap", tuple(sorted(cac_si)))) or {"pe": "APP-2", "hd": [], "ma_gd": "FT2"})
	try:
		cn.khop_tay(doc.name, 5600000, "FT2")
		la("đưa cả hai tờ", [x[1] for x in nk if x[0] == "lap"], [("HDB-26-09-01679", "HDB-26-09-02477")])
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		tra()


@ca("Codex #437 vòng 4: KHOÁ từng hoá đơn theo thứ tự tên TRƯỚC khi đọc phân bổ nháp")
def _():
	nk, tra = _dung_he()
	try:
		tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000)
	finally:
		tra()
	khoa = [x for x in nk if x[0] == "khoa"]
	la("khoá hai tờ theo thứ tự tên", [(x[1], x[2]) for x in khoa],
		[("Sales Invoice", "HDB-26-09-01679"), ("Sales Invoice", "HDB-26-09-02477")])
	buoc = [x[0] for x in nk]
	dung("khoá xong mới đọc nháp", buoc.index("doc_nhap") > max(i for i, b in enumerate(buoc) if b == "khoa"))


@ca("Codex #437 vòng 4: trả góp 2tr rồi 5,6tr thì đã thu CỘNG DỒN 7,6tr, phiếu Đã thu đủ")
def _():
	# Trên c6a3b7d: da_thu bị ghi đè còn 5.600.000, phiếu Thu thiếu, màn hiện
	# lại QR đòi 2.000.000 khách đã trả.
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0)]
	nk, tra = _dung_he(nhap=nhap, bt={"BT-0": 2000000.0, "BT-2": 5600000.0})
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Thu thieu",
		tong_tien=7600000.0, da_thu=2000000.0, ma_gd="BT-0", flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT2"
	tt.tim_giao_dich = lambda ma: Doi(GD, name="BT-2", deposit=5600000.0, unallocated_amount=5600000.0)
	cn._gui_thu_da_nhan = lambda d: None

	def lap(cac_si, g, so, gc=""):
		# Phiếu nháp mới đi vào sổ như thật: thêm phân bổ cho phần còn lại.
		nhap.append(Doi(reference_name="HDB-26-09-01679", allocated_amount=2750000.0))
		nhap.append(Doi(reference_name="HDB-26-09-02477", allocated_amount=2850000.0))
		return {"pe": "APP-2", "hd": [], "ma_gd": "FT2", "tien": 5600000.0}
	tt.lap_phieu_thu_theo_gd = lap
	try:
		cn.khop_tay(doc.name, 5600000, "FT2")
		la("đã thu cộng dồn", doc.da_thu, 7600000.0)
		la("đã thu đủ", doc.trang_thai, "Da thu du")
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		tra()


@ca("Codex #437 vòng 4: trả lại người gọi HỎNG thì báo lỗi, không chạy tiếp bằng Administrator")
def _():
	nk, tra = _dung_he()
	goc_set = fr.set_user

	def set_user_hong(u):
		nk.append(("set_user", u))
		if u != "Administrator":
			raise RuntimeError("khong doi duoc nguoi dung")
		fr.session.user = u
	fr.set_user = set_user_hong
	try:
		def chay():
			with tt.nang_quyen_lap_phieu():
				pass
		nem("lỗi bay ra ngoài", chay, Exception)
	finally:
		fr.set_user = goc_set
		tra()


@ca("Codex #437 vòng 5: phiếu nháp CHƯA xác minh không tính là đã nhận, phiếu không được báo đã thu đủ")
def _():
	# Trên 45ba543: da_thu tính từ mọi phân bổ nháp, nên nháp 2tr chưa có
	# tiền về cộng với lần 5,6tr thật vẫn ra 7,6tr, Da thu du, gửi thư.
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0, xm=0)]
	nk, tra = _dung_he(nhap=nhap, bt={"BT-2": 5600000.0})
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Cho thu",
		tong_tien=7600000.0, da_thu=0.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT2"
	tt.tim_giao_dich = lambda ma: Doi(GD, name="BT-2", deposit=5600000.0, unallocated_amount=5600000.0)
	cn._gui_thu_da_nhan = lambda d: nk.append(("gui_thu",))

	def lap(cac_si, g, so, gc=""):
		nhap.append(Doi(reference_name="HDB-26-09-01679", allocated_amount=2750000.0, pe="APP-2"))
		nhap.append(Doi(reference_name="HDB-26-09-02477", allocated_amount=2850000.0, pe="APP-2"))
		return {"pe": "APP-2", "hd": [], "ma_gd": "FT2", "tien": 5600000.0}
	tt.lap_phieu_thu_theo_gd = lap
	try:
		cn.khop_tay(doc.name, 5600000, "FT2")
		la("chỉ tính phần đã xác minh", doc.da_thu, 5600000.0)
		la("vẫn Thu thiếu", doc.trang_thai, "Thu thieu")
		la("không gửi thư đã nhận đủ", [x for x in nk if x[0] == "gui_thu"], [])
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		tra()


@ca("Codex #437 vòng 5: số tiền phiếu thu lấy từ giao dịch, không tin số máy khách gửi")
def _():
	nk, tra = _dung_he()
	try:
		kq = tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 1000000)
	finally:
		tra()
	la("lấy đủ 7,6tr của giao dịch", kq["tien"], 7600000.0)
	la("chia đủ hai tờ", kq["hd"], [("HDB-26-09-01679", 4750000.0), ("HDB-26-09-02477", 2850000.0)])


@ca("Codex #437 vòng 6: giao dịch LỚN hơn phần nợ chưa phủ thì dừng, không lập phiếu thiếu chiếm mã giao dịch")
def _():
	# Trên 529a684: nháp 2tr chưa xác minh đang giữ một phần, giao dịch thật
	# 7,6tr lập phiếu 5,6tr, 2tr còn lại của giao dịch không bao giờ phân bổ được.
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0, xm=0)]
	nk, tra = _dung_he(nhap=nhap)
	try:
		nem("báo lỗi", lambda: tt.lap_phieu_thu_theo_gd([h.name for h in HD], GD, 7600000), fr.ValidationError)
	finally:
		tra()
	la("không insert phiếu nào", [x for x in nk if x[0] == "insert"], [])


@ca("Codex #437 vòng 6: bình luận và câu báo ghi ĐÚNG số máy chủ đã phân bổ, không ghi số máy khách gửi")
def _():
	nhap = []
	nk, tra = _dung_he(nhap=nhap)
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Cho thu",
		tong_tien=7600000.0, da_thu=0.0, flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"tim": tt.tim_giao_dich, "lap": tt.lap_phieu_thu_theo_gd, "gui": cn._gui_thu_da_nhan}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "FT1"
	tt.tim_giao_dich = lambda ma: GD
	cn._gui_thu_da_nhan = lambda d: None

	def lap(cac_si, g, so, gc=""):
		nhap.extend(Doi(reference_name=h.name, allocated_amount=h.outstanding_amount, pe="APP-1") for h in HD)
		return {"pe": "APP-1", "hd": [(h.name, h.outstanding_amount) for h in HD], "ma_gd": "FT1", "tien": 7600000.0}
	tt.lap_phieu_thu_theo_gd = lap
	try:
		kq = cn.khop_tay(doc.name, 1000000, "FT1")
		bl = [x[1] for x in nk if x[0] == "binh_luan"]
		dung("bình luận ghi 7.600.000, được " + str(bl), bl and "7.600.000" in bl[0])
		dung("câu báo ghi 7.600.000", "7.600.000" in kq["loi_nhan"])
		dung("không ghi 1.000.000", "1.000.000" not in kq["loi_nhan"])
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		tt.tim_giao_dich = moc["tim"]
		tt.lap_phieu_thu_theo_gd = moc["lap"]
		cn._gui_thu_da_nhan = moc["gui"]
		tra()


@ca("Codex #437 vòng 9: ghi tay 2tr rồi SePay tự khớp 5,6tr thì đã thu 7,6tr, không bị SePay ghi đè")
def _():
	# Trên 9db2bcd: kiem_sepay ghi da_thu = 5.600.000 đè lên 2.000.000 ghi tay,
	# màn còn đòi 2.000.000 lần nữa.
	nk, tra = _dung_he(bt={"BT-S": 5600000.0})
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Thu thieu",
		tong_tien=7600000.0, da_thu=2000000.0,
		ma_gd="", flags=Doi(), _nk=nk, dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd, "sp": cn._sepay_cn,
		"gui": cn._gui_thu_da_nhan, "ghi": cn.ghi_thu_cho_phieu, "xem": cn.xem_phieu}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: "\n".join(ds)
	cn._sepay_cn = lambda ma: {"nhan": 5600000.0, "so_gd": 1, "gd": ["BT-S"]}
	cn._gui_thu_da_nhan = lambda d: None
	cn.ghi_thu_cho_phieu = lambda *a, **k: nk.append(("ghi_thu", k.get("so_tien"), k.get("khoa"))) or []
	cn.xem_phieu = lambda name: {}
	try:
		cn.kiem_sepay("P")
		la("cộng dồn 7,6tr", doc.da_thu, 7600000.0)
		la("phiếu thu chỉ cho PHẦN MỚI, khoá theo giao dịch",
			[x[1:] for x in nk if x[0] == "ghi_thu"], [(5600000.0, "sepay:BT-S")])
		la("đã thu đủ", doc.trang_thai, "Da thu du")
		dung("giữ mã giao dịch SePay", "BT-S" in (doc.ma_gd or ""))
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		cn._sepay_cn = moc["sp"]
		cn._gui_thu_da_nhan = moc["gui"]
		cn.ghi_thu_cho_phieu = moc["ghi"]
		cn.xem_phieu = moc["xem"]
		tra()


@ca("Codex #437 vòng 9: một giao dịch vừa SePay thấy vừa khớp tay chỉ tính MỘT lần")
def _():
	nk, tra = _dung_he(bt={"BT-1": 7600000.0})
	try:
		doc = Doi(tong_tien=15200000.0, da_thu=7600000.0, ma_gd="FT26277123\nBT-1")
		la("giao dịch đã ghi không tính lại", cn._da_nhan_phieu(doc, {"gd": ["BT-1"]}), 7600000.0)
		doc2 = Doi(tong_tien=15200000.0, da_thu=0.0, ma_gd="")
		la("giao dịch SePay chưa ghi thì tính vào", cn._da_nhan_phieu(doc2, {"gd": ["BT-1"]}), 7600000.0)
	finally:
		tra()


@ca("Codex #437 vòng 10: phiếu khớp TRƯỚC v571 vẫn đọc đúng số đã nhận, không về 0")
def _():
	nk, tra = _dung_he(bt={})
	try:
		cu = Doi(tong_tien=7600000.0, da_thu=7600000.0, ma_gd="FT26277123")
		la("phiếu cũ giữ 7,6tr", cn._da_nhan_phieu(cu, {}), 7600000.0)
	finally:
		tra()


@ca("Codex #437 vòng 10: lập phiếu thu cho PHẦN MỚI, chia phần chưa phủ, khoá riêng từng lần")
def _():
	nhap = [Doi(reference_name="HDB-26-09-01679", allocated_amount=2000000.0)]
	nk, tra = _dung_he(nhap=nhap)
	goc = tt.ghi_thu_tien
	tt.ghi_thu_tien = lambda si, dong, nguon="", **k: nk.append(("thu", si, dong[0]["so_tien"], nguon)) or ["PE"]
	try:
		doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", da_thu=7600000.0, flags=Doi(), _nk=nk)
		cn.ghi_thu_cho_phieu(doc, so_tien=5600000.0, khoa="sepay:BT-S")
	finally:
		tt.ghi_thu_tien = goc
		tra()
	la("chia phần còn lại, khoá theo lần nhận", [x[1:] for x in nk if x[0] == "thu"],
		[("HDB-26-09-01679", 2750000.0, "phieu:P:sepay:BT-S"), ("HDB-26-09-02477", 2850000.0, "phieu:P:sepay:BT-S")])


@ca("Codex #437 vòng 9: phiếu nháp CHƯA xác minh không làm hoá đơn trông như đã có phiếu thu")
def _():
	nhap = [Doi(reference_name=h.name, allocated_amount=h.outstanding_amount, xm=0) for h in HD]
	nk, tra = _dung_he(nhap=nhap)
	try:
		la("vẫn thiếu phiếu thu cả hai tờ", cn._hd_chua_co_phieu_thu([h.name for h in HD]),
			{h.name for h in HD})
	finally:
		tra()
	nhap2 = [Doi(reference_name=h.name, allocated_amount=h.outstanding_amount, xm=1) for h in HD]
	nk, tra = _dung_he(nhap=nhap2)
	try:
		la("nháp đã xác minh thì đủ", cn._hd_chua_co_phieu_thu([h.name for h in HD]), set())
	finally:
		tra()


@ca("Codex #437 vòng 10: lần nhận 2tr thì chỉ lập phiếu thu 2tr, dù phiếu đã ghi nhận nhiều hơn")
def _():
	nk, tra = _dung_he()
	goc = tt.ghi_thu_tien
	tt.ghi_thu_tien = lambda si, dong, nguon="", **k: nk.append(("thu", si, dong[0]["so_tien"])) or ["PE"]
	try:
		doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", da_thu=7600000.0, flags=Doi(), _nk=nk)
		cn.ghi_thu_cho_phieu(doc, so_tien=2000000.0, khoa="tay:1")
	finally:
		tt.ghi_thu_tien = goc
		tra()
	la("chỉ 2tr vào tờ cũ nhất", [x[1:] for x in nk if x[0] == "thu"], [("HDB-26-09-01679", 2000000.0)])


@ca("Codex #437 vòng 10: gửi lại cùng mã lần khớp tay thì KHÔNG cộng tiền, không lập phiếu thu lần hai")
def _():
	nk, tra = _dung_he()
	binh = []
	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00002", trang_thai="Cho thu",
		tong_tien=7600000.0, da_thu=0.0, ma_gd="", flags=Doi(), _nk=nk,
		dong=[Doi(hoa_don=h.name) for h in HD])
	moc = {"get_doc": fr.get_doc, "kq": cn._kiem_quyen_ban, "giu": cn._giu_gd,
		"gui": cn._gui_thu_da_nhan, "ghi": cn.ghi_thu_cho_phieu, "ex": fr.db.exists}
	fr.get_doc = lambda *a, **k: doc
	cn._kiem_quyen_ban = lambda: None
	cn._giu_gd = lambda d, ds: ""
	cn._gui_thu_da_nhan = lambda d: None
	cn.ghi_thu_cho_phieu = lambda *a, **k: nk.append(("ghi_thu", k.get("so_tien"), k.get("khoa"))) or []
	# Dấu lần khớp nằm trong bình luận: exists đọc đúng các bình luận đã ghi.
	fr.db.exists = lambda dt, f=None, **k: dt == "Comment" and any(
		f["content"][1].strip("%") in x[1] for x in nk if x[0] == "binh_luan")
	try:
		cn.khop_tay("P", 2000000, "", "khach dua tien mat", ma_lan="lan1")
		kq2 = cn.khop_tay("P", 2000000, "", "khach dua tien mat", ma_lan="lan1")
		la("đã thu chỉ cộng một lần", doc.da_thu, 2000000.0)
		la("chỉ một lần lập phiếu thu, khoá ổn định", [x[1:] for x in nk if x[0] == "ghi_thu"],
			[(2000000.0, "tay:lan1")])
		la("lần sau báo đã làm rồi", kq2.get("da_lam_roi"), 1)
	finally:
		fr.get_doc = moc["get_doc"]
		cn._kiem_quyen_ban = moc["kq"]
		cn._giu_gd = moc["giu"]
		cn._gui_thu_da_nhan = moc["gui"]
		cn.ghi_thu_cho_phieu = moc["ghi"]
		fr.db.exists = moc["ex"]
		tra()
