"""v577: khớp tay không gắn giao dịch, huỷ phiếu kẹt, SePay lập phiếu nháp, thư mọi pháp nhân.

Ca thật 05/10/2026, Loan Anh báo phiếu DNTT-26-10-00004 (Ms.Dung, 17 hoá đơn,
8.450.000 đ): "khớp tay, chọn đúng giao dịch ngân hàng, không có giao dịch khớp
với bill, nhập số tiền đã nhận, Hoàn thành nhưng vẫn chưa clear được bill bên
đang nợ". Site thật:
  * khách Kiệt Tác chuyển 9.550.000 đ, hộp Khớp tay lọc ĐÚNG số tiền phiếu nên
    giao dịch đó không hiện;
  * lối "Không thấy giao dịch" lập 17 phiếu thu ngân hàng rồi ghi sổ thẳng,
    hook chan_thieu_dinh_kem chặn cả 17 (thiếu UNC), lỗi bị nuốt, phiếu đòi nợ
    vẫn "Đã thu đủ", 17 phiếu nháp hỏng ở lại giữ phần nợ.

Các ca dưới CHẠY THẬT khop_tay, ghi_thu_cho_phieu, ghi_thu_tien, ham_dinh_unc,
soat_tep_unc_moi, tim_giao_dich_thu, huy_phieu, kiem_sepay, _gui_thu_da_nhan
trên bản Frappe giả của nen.py. Payment Entry giả ghi sổ HỎNG như hook thật khi
chưa có tệp đính vào chính nó. Không dò chuỗi trong mã nguồn (CLAUDE.md điều 16).
"""

import json

from vagabond.khung.kiem_thu.nen import ca, dung, la, gia_lap

fr = gia_lap()

from vagabond import thu_tien as tt  # noqa: E402
from vagabond import gom_phap_nhan as gpn  # noqa: E402
from vagabond.khung.kiem_thu.thu_cong_no_571 import cn, Doi  # noqa: E402


class Thay(object):
	"""Thay thuộc tính trong lúc chạy một ca, trả lại nguyên trạng dù ca ném lỗi."""

	def __init__(self):
		self.cu = []

	def dat(self, obj, ten, gt):
		self.cu.append((obj, ten, getattr(obj, ten, None), hasattr(obj, ten)))
		setattr(obj, ten, gt)

	def tra(self):
		for obj, ten, gt, co in reversed(self.cu):
			if co:
				setattr(obj, ten, gt)
			else:
				delattr(obj, ten)


def _bat(ham):
	try:
		ham()
	except Exception as e:
		return e
	return None


HD = [
	Doi(name="HDB-26-08-00354", customer="KL028403", company="TV", outstanding_amount=500000.0,
		posting_date="2026-08-17", grand_total=500000.0, due_date="2026-08-17", docstatus=1),
	Doi(name="HDB-26-09-00999", customer="KL028403", company="TV", outstanding_amount=450000.0,
		posting_date="2026-09-06", grand_total=450000.0, due_date="2026-09-06", docstatus=1),
]
TK_NH = "11211 - Tiền gửi MB Bank - TV"
UNC = "/private/files/unc-kiet-tac.jpg"


class He(object):
	"""Bản hệ giả cho một ca: hoá đơn, phiếu thu, tệp, giao dịch CSDL.

	Payment Entry giả ghi sổ như hook thật: phiếu thu về ngân hàng mà chưa có
	dòng File nào gắn vào CHÍNH nó thì ném "bắt buộc phải có Uỷ nhiệm chi".
	commit() mới ghi bền; lỗi giữa chừng thì những gì chưa commit mất hết.
	"""

	def __init__(self, vai=("Accounts User",), hd=None, tep=None, nhap=None, hong_o=None):
		self.th = Thay()
		self.nk = []
		self.hd = [Doi(h) for h in (hd or HD)]
		self.tep = dict(tep or {UNC: Doi(name="F-UNC", owner="ketoan@vagabond", file_name="unc.jpg",
			is_private=1, attached_to_doctype=None, attached_to_name=None)})
		self.gan = {}       # tên phiếu thu -> [đường dẫn tệp đã gắn]
		self.pe = {}        # tên phiếu thu -> phiếu
		self.nhap = list(nhap or [])
		self.hong_o = hong_o  # lần ghi sổ thứ mấy thì hỏng vì lý do khác
		self.ben = {"phieu": None, "binh_luan": []}
		self.dang = {"binh_luan": []}
		self.vai = list(vai)
		self.dat_he()

	def dat_he(self):
		he = self
		th = self.th

		def get_all(dt, filters=None, **k):
			f = filters or {}
			if dt == "Vagabond Cong No Dong":
				return [Doi(hoa_don=h.name) for h in he.hd]
			if dt == "Sales Invoice":
				ten = (f.get("name") or ["in", [h.name for h in he.hd]])[1]
				ds = [h for h in he.hd if h.name in ten]
				if f.get("outstanding_amount"):
					ds = [h for h in ds if h.outstanding_amount > f["outstanding_amount"][1]]
				ds = sorted(ds, key=lambda h: str(h.posting_date))
				if k.get("pluck") == "name":
					return [h.name for h in ds]
				return [Doi(h) for h in ds]
			if dt == "Payment Entry Reference":
				return [Doi(r) for r in he.nhap]
			if dt == "Customer":
				return [Doi(name=h.customer, customer_name="Ms.Dung") for h in he.hd]
			return []

		def get_value(dt, ten, fields=None, as_dict=False, **k):
			if dt == "Sales Invoice":
				h = [x for x in he.hd if x.name == ten]
				return Doi(h[0]) if h else None
			if dt == "Mode of Payment Account":
				return TK_NH
			if dt == "Bank Account":
				return "MB-TV"
			if dt == "File":
				return he.tep.get((ten or {}).get("file_url"))
			return None

		def exists(dt, f=None, **k):
			if dt == "Mode of Payment":
				return True
			if dt == "Comment":
				return any(f["content"][1].strip("%") in x for x in he.ben["binh_luan"])
			return False

		def set_value(dt, ten, gt, *a, **k):
			if dt == "File":
				t = [x for x in he.tep.values() if x.name == ten][0]
				t.update(gt)
				he.gan.setdefault(gt["attached_to_name"], []).append(("chuyen", [u for u, x in he.tep.items() if x is t][0]))
				he.nk.append(("gan_tep", gt["attached_to_name"]))
			else:
				he.nk.append(("set_value", dt, ten))

		class PE(Doi):
			def append(self, k, v):
				self.setdefault(k, []).append(Doi(v))

			def setup_party_account_field(self):
				pass

			def set_missing_values(self):
				pass

			def insert(self, **k):
				self.name = "APP-26-10-%03d" % (134 + len(he.pe))
				self.owner = fr.session.user
				he.pe[self.name] = self
				he.nk.append(("insert", self.name))

			def submit(self):
				if he.hong_o and len([x for x in he.nk if x[0] == "submit"]) + 1 == he.hong_o:
					raise fr.ValidationError("Kỳ kế toán đã khoá")
				if self.paid_to == TK_NH and not he.gan.get(self.name):
					raise fr.ValidationError("Giấy báo Có %s đi qua tài khoản ngân hàng %s nên bắt buộc phải có "
						"Uỷ nhiệm chi đính kèm mới ghi sổ được." % (self.name, TK_NH))
				self.docstatus = 1
				# Như ERPNext: phiếu vào sổ thì trừ dư nợ hoá đơn trên sổ cái.
				for r in self.get("references") or []:
					for h in he.hd:
						if h.name == r.reference_name:
							h.outstanding_amount -= r.allocated_amount
				he.nk.append(("submit", self.name, self.get("vgb_thu_unc")))

		class TepGia(Doi):
			def insert(self, **k):
				he.gan.setdefault(self.attached_to_name, []).append(("chep", self.file_url))
				he.nk.append(("chep_tep", self.attached_to_name))

		def get_doc(*a, **k):
			if a and isinstance(a[0], dict):
				return TepGia(a[0])
			return he.lay_phieu()

		def set_user(u):
			fr.session.user = u

		def commit(*a, **k):
			he.nk.append(("commit",))
			he.ben["phieu"] = {x: v for x, v in he.dang["doc"].items() if x not in ("flags", "_he")}
			he.ben["binh_luan"] += he.dang["binh_luan"]
			he.dang["binh_luan"] = []

		th.dat(fr, "get_all", get_all)
		th.dat(fr.db, "get_value", get_value)
		th.dat(fr.db, "exists", exists)
		th.dat(fr.db, "set_value", set_value)
		th.dat(fr.db, "commit", commit)
		th.dat(fr, "new_doc", lambda dt: PE(docstatus=0, flags=Doi()))
		th.dat(fr, "get_doc", get_doc)
		th.dat(fr, "set_user", set_user)
		th.dat(fr, "get_roles", lambda *a, **k: list(he.vai))
		th.dat(fr, "generate_hash", lambda length=8, **k: "x" * length)
		th.dat(fr.session, "user", "ketoan@vagabond")
		th.dat(cn, "_kiem_quyen_ban", lambda: None)
		th.dat(cn, "_giu_gd", lambda d, ds: "")
		th.dat(cn, "_gui_thu_da_nhan", lambda d, **k: he.nk.append(("gui_thu",)) or (True, "x@y"))
		th.dat(tt, "phieu_thu_nhap", lambda cac_si=None, **k: [])

	def phieu(self, **doi):
		goc = dict(name="DNTT-26-10-00004", ma_phieu="DNTT-26-10-00004", khach="KL028403",
			ten_khach="Ms.Dung", trang_thai="Cho thu", tong_tien=950000.0, da_thu=0.0, ma_gd="")
		goc.update(doi)
		self.ben["phieu"] = goc
		return goc

	def lay_phieu(self):
		he = self

		class PhieuNo(Doi):
			def save(self, **k):
				he.nk.append(("luu_phieu", self.trang_thai))

			def add_comment(self, *a, **k):
				he.dang["binh_luan"].append(a[1])

		d = PhieuNo(dict(self.ben["phieu"]), flags=Doi(), dong=[Doi(hoa_don=h.name, so_tien=h.grand_total) for h in self.hd])
		self.dang = {"doc": d, "binh_luan": []}
		return d

	def tra(self):
		self.th.tra()


# ------------------------------------------------------------ phép thuần


@ca("v577 câu báo giao dịch lớn hơn phiếu nói đủ ba con số và chỉ đường huỷ rồi gom lại (ca Kiệt Tác)")
def _():
	c = tt.cau_gd_lon_hon("FT26278", 9550000, 8450000)
	for x in ("9.550.000 đ", "8.450.000 đ", "dư 1.100.000 đ", "Huỷ phiếu này", "pháp nhân khác"):
		dung("có '%s'" % x, x in c)


@ca("v577 hộp Khớp tay: giao dịch ĐÚNG số tiền xếp đầu, khoản khác vẫn có, giữ thứ tự ngày")
def _():
	ds = [{"ma": "A", "con": 9550000.0}, {"ma": "B", "con": 8450000.0}, {"ma": "C", "con": 200000.0},
		{"ma": "D", "con": 8450000.4}]
	ra = tt.xep_gd_khop_tay(ds, 8450000)
	la("đúng số lên đầu, rồi tới các khoản khác", [x["ma"] for x in ra], ["B", "D", "A", "C"])
	la("đánh dấu đúng số", [x["dung_so"] for x in ra], [1, 1, 0, 0])
	la("không có số cần thu thì không đánh dấu", [x["dung_so"] for x in tt.xep_gd_khop_tay(ds, 0)], [0, 0, 0, 0])


@ca("v577 phiếu Đã thu đủ chỉ huỷ được khi chưa gạch giao dịch và chưa có phiếu thu vào sổ")
def _():
	la("kẹt kiểu Ms.Dung: huỷ được", cn.huy_duoc_phieu_da_thu("", [])[0], True)
	ok, vi_sao = cn.huy_duoc_phieu_da_thu("FT123\nBT-9", [])
	la("đã gạch giao dịch: không", ok, False)
	dung("chỉ sang Tiền đã về", "Tiền đã về" in vi_sao)
	ok, vi_sao = cn.huy_duoc_phieu_da_thu("", ["APP-1"])
	la("có phiếu thu vào sổ: không", ok, False)
	dung("nêu tên phiếu thu", "APP-1" in vi_sao)


@ca("v577 thư báo nhận tiền: mọi pháp nhân có email, khách đứng tên trước, bỏ trống và trùng")
def _():
	email = {"OSHIMA": "ketoan@oshima.vn", "VU": "vu@gmail.com", "TRONG": "", "CHUNG": "KETOAN@oshima.vn"}
	hoi = []

	def cua(k):
		hoi.append(k)
		return email.get(k, "")
	la("đủ, đúng thứ tự", gpn.ds_email_thu(["VU", "OSHIMA", "VU", "TRONG", "CHUNG", ""], cua),
		["vu@gmail.com", "ketoan@oshima.vn"])
	la("mỗi khách hỏi một lần", hoi, ["VU", "OSHIMA", "TRONG", "CHUNG"])


# ------------------------------------------------- khớp tay không gắn giao dịch


@ca("v577 Sales chọn không giao dịch: CHẶN trước mọi thay đổi, không lập phiếu thu, chỉ đường tìm giao dịch")
def _():
	he = He(vai=("Sales Manager", "Sales User"))
	try:
		he.phieu()
		e = _bat(lambda: cn.khop_tay("DNTT-26-10-00004", 950000, "", "Kiet Tac", ma_lan="l1", unc=json.dumps([UNC])))
		dung("phải chặn", e is not None)
		dung("nói chỉ kế toán: " + str(e)[:80], "chỉ kế toán" in str(e))
		dung("chỉ cách tìm giao dịch", "ô tìm" in str(e))
		la("không lưu, không lập, không ghi sổ", [x[0] for x in he.nk if x[0] in ("luu_phieu", "insert", "submit", "commit")], [])
		la("phiếu vẫn chờ thu", he.ben["phieu"]["trang_thai"], "Cho thu")
	finally:
		he.tra()


@ca("v577 kế toán chọn không giao dịch mà không đính UNC: CHẶN trước mọi thay đổi")
def _():
	he = He()
	try:
		he.phieu()
		e = _bat(lambda: cn.khop_tay("DNTT-26-10-00004", 950000, "", "Kiet Tac", ma_lan="l2"))
		dung("phải chặn", e is not None)
		dung("nói phải đính UNC: " + str(e)[:80], "uỷ nhiệm chi" in str(e))
		la("không lưu, không lập", [x[0] for x in he.nk if x[0] in ("luu_phieu", "insert", "commit")], [])
	finally:
		he.tra()


@ca("v577 TRƯỚC bản sửa (đo lại ca Ms.Dung): lối cũ không UNC nuốt lỗi từng hoá đơn, để lại phiếu thu nháp hỏng")
def _():
	# Gọi đúng lời gọi lối cũ (không chat, không dinh) trên cùng hệ giả: đây là
	# số đo TRƯỚC khi sửa, để thấy ca sau đo đúng chỗ.
	he = He()
	try:
		he.phieu()
		doc = he.lay_phieu()
		ra = cn.ghi_thu_cho_phieu(doc, "Chuyển khoản", "Kế toán khớp tay.", so_tien=950000.0, khoa="tay:cu")
		la("không phiếu nào vào sổ", ra, [])
		la("hai lỗi bị nuốt", len(doc.flags.loi_thu or []), 2)
		dung("lỗi là thiếu UNC", all("Uỷ nhiệm chi" in x for x in doc.flags.loi_thu))
		la("hai phiếu nháp hỏng ở lại", sorted(n for n, p in he.pe.items() if not p.get("docstatus")),
			["APP-26-10-134", "APP-26-10-135"])
	finally:
		he.tra()


@ca("v577 kế toán khớp tay không giao dịch, đính UNC: MỌI phiếu thu có tệp TRƯỚC khi ghi sổ, vào sổ hết, phiếu thu đủ")
def _():
	he = He()
	try:
		he.phieu()
		kq = cn.khop_tay("DNTT-26-10-00004", 950000, "", "Kiet Tac doi soat", ma_lan="l3", unc=json.dumps([UNC]))
		la("hai phiếu thu đã vào sổ", sorted(n for n, p in he.pe.items() if p.docstatus == 1),
			["APP-26-10-134", "APP-26-10-135"])
		buoc = [x[:2] for x in he.nk if x[0] in ("insert", "gan_tep", "chep_tep", "submit")]
		la("từng phiếu: lưu nháp, gắn tệp, rồi mới ghi sổ", buoc, [
			("insert", "APP-26-10-134"), ("gan_tep", "APP-26-10-134"), ("submit", "APP-26-10-134"),
			("insert", "APP-26-10-135"), ("chep_tep", "APP-26-10-135"), ("submit", "APP-26-10-135")])
		la("phiếu đầu nhận chính tệp đã tải, phiếu sau nhận bản chép cùng đường dẫn",
			[he.gan[n] for n in ("APP-26-10-134", "APP-26-10-135")], [[("chuyen", UNC)], [("chep", UNC)]])
		la("ô UNC trên cả hai phiếu", [x[2] for x in he.nk if x[0] == "submit"], [json.dumps([UNC])] * 2)
		la("đã commit", he.ben["phieu"]["trang_thai"], "Da thu du")
		la("không lỗi", kq["loi"], [])
		la("gửi thư báo nhận tiền một lần", [x for x in he.nk if x[0] == "gui_thu"], [("gui_thu",)])
	finally:
		he.tra()


@ca("v577 kế toán khớp tay không giao dịch: phiếu thu thứ hai HỎNG thì cả lượt lùi, phiếu đòi nợ KHÔNG thành đã thu")
def _():
	he = He(hong_o=2)
	try:
		he.phieu()
		e = _bat(lambda: cn.khop_tay("DNTT-26-10-00004", 950000, "", "Kiet Tac", ma_lan="l4", unc=json.dumps([UNC])))
		dung("phải báo lỗi", e is not None)
		dung("nêu đúng hoá đơn hỏng: " + str(e)[:120], "HDB-26-09-00999" in str(e))
		dung("nêu lý do thật", "Kỳ kế toán đã khoá" in str(e))
		dung("nói phiếu chưa đổi", "chưa bị đổi gì" in str(e))
		la("không commit gì", [x for x in he.nk if x[0] == "commit"], [])
		la("phiếu đòi nợ bền vẫn chờ thu", he.ben["phieu"]["trang_thai"], "Cho thu")
		la("dấu lần khớp chưa ghi bền", he.ben["binh_luan"], [])
	finally:
		he.tra()


@ca("v577 kế toán khớp tay không giao dịch mà không còn phần nợ nào để lập: báo rõ, không thành đã thu")
def _():
	nhap = [Doi(reference_name=h.name, allocated_amount=h.outstanding_amount) for h in HD]
	he = He(nhap=nhap)
	try:
		he.phieu()
		e = _bat(lambda: cn.khop_tay("DNTT-26-10-00004", 950000, "", "Kiet Tac", ma_lan="l5", unc=json.dumps([UNC])))
		dung("phải báo lỗi", e is not None)
		dung("nói không còn phần nợ: " + str(e)[:100], "không còn phần nợ" in str(e))
		la("không commit", [x for x in he.nk if x[0] == "commit"], [])
	finally:
		he.tra()


@ca("v577 soát tệp UNC bằng người bấm: thiếu tệp, tệp đã thuộc chứng từ khác, tệp người khác đều chặn")
def _():
	he = He(vai=("Accounts User",), tep={
		"/a.jpg": Doi(name="FA", owner="ketoan@vagabond", file_name="a.jpg", is_private=1),
		"/b.jpg": Doi(name="FB", owner="ketoan@vagabond", file_name="b.jpg", is_private=1,
			attached_to_doctype="Payment Entry", attached_to_name="APP-9"),
		"/c.jpg": Doi(name="FC", owner="sales@vagabond", file_name="c.jpg", is_private=0),
	})
	try:
		dung("rỗng", "uỷ nhiệm chi" in str(_bat(lambda: tt.soat_tep_unc_moi("[]"))))
		dung("không có thật", "Không thấy tệp" in str(_bat(lambda: tt.soat_tep_unc_moi('["/z.jpg"]'))))
		dung("đã thuộc chứng từ khác", "APP-9" in str(_bat(lambda: tt.soat_tep_unc_moi('["/b.jpg"]'))))
		dung("tệp người khác", "người tải tệp" in str(_bat(lambda: tt.soat_tep_unc_moi('["/c.jpg"]'))))
		la("tệp đúng", tt.soat_tep_unc_moi('["/a.jpg"]'),
			[{"url": "/a.jpg", "ten": "FA", "ten_tep": "a.jpg", "rieng": 1}])
	finally:
		he.tra()


# --------------------------------------------------- danh sách giao dịch


@ca("v577 hộp Khớp tay nhận MỌI giao dịch chưa nối (ca Kiệt Tác 9,55tr cho phiếu 8,45tr), bỏ giao dịch đã có phiếu thu")
def _():
	loc = {}
	BT = [Doi(name="BT-1", date="2026-10-05", description="Kiet Tac doi soat Vagabond 8.9 nam 2026", deposit=9550000.0,
			bank_account="MB", reference_number="FT-KIETTAC", unallocated_amount=9550000.0),
		Doi(name="BT-2", date="2026-10-04", description="DNTT khac", deposit=8450000.0, bank_account="MB",
			reference_number="FT-DUNG", unallocated_amount=8450000.0),
		Doi(name="BT-3", date="2026-10-03", description="da co phieu thu nhap", deposit=8450000.0, bank_account="MB",
			reference_number="FT-DACO", unallocated_amount=8450000.0)]
	th = Thay()

	def get_all(dt, filters=None, **k):
		if dt == "Bank Transaction":
			loc.update(filters)
			return [Doi(b) for b in BT]
		if dt == "Payment Entry":
			la("hỏi đúng mã giao dịch", sorted(filters["reference_no"][1]), ["FT-DACO", "FT-DUNG", "FT-KIETTAC"])
			return ["FT-DACO"]
		return []
	th.dat(fr, "get_all", get_all)
	th.dat(cn, "_kiem_quyen_ban", lambda: None)
	try:
		kq = cn.tim_giao_dich_thu(so_ngay=120, so_tien=8450000, chua_noi=1)
		la("đúng số lên đầu, giao dịch lớn hơn vẫn có, bỏ khoản đã có phiếu", [r["ma"] for r in kq["rows"]],
			["FT-DUNG", "FT-KIETTAC"])
		la("lọc giao dịch đã xác nhận, còn tiền, chưa nối",
			(loc.get("docstatus"), loc.get("unallocated_amount"), loc.get("allocated_amount")),
			(1, [">", 0.5], ["<", 0.5]))
		la("trả số tiền chưa nối", kq["rows"][1]["con"], 9550000.0)
		cu = cn.tim_giao_dich_thu(so_ngay=120, so_tien=8450000)
		la("cách gọi cũ vẫn lọc đúng số như trước", [r["ma"] for r in cu["rows"]], ["FT-DUNG", "FT-DACO"])
	finally:
		th.tra()


# ------------------------------------------------------- huỷ phiếu kẹt


def _he_huy(trang_thai, ma_gd="", da_ghi=(), nhap=("APP-26-10-134", "APP-26-10-150")):
	nk = []
	th = Thay()

	class PhieuNo(Doi):
		def save(self, **k):
			nk.append(("luu", self.trang_thai))

		def add_comment(self, *a, **k):
			nk.append(("binh_luan", a[1]))

	doc = PhieuNo(name="DNTT-26-10-00004", ma_phieu="DNTT-26-10-00004", trang_thai=trang_thai, ma_gd=ma_gd, ghi_chu="")

	def get_all(dt, filters=None, **k):
		if dt == "Payment Entry":
			mau = filters["reference_no"][1]
			nk.append(("tim", filters["docstatus"], mau))
			ds = list(da_ghi) if filters["docstatus"] == 1 else list(nhap)
			return ds if mau.endswith(":%") else []
		return []
	class PT(Doi):
		def set(self, k, v):
			self[k] = v

		def save(self, **k):
			nk.append(("luu_pt", self.name, fr.session.user, len(self.references), self.reference_no))

	pts = {t: PT(name=t, docstatus=0, reference_no="THU:HDB-%s:phieu:DNTT-26-10-00004:tay:x|Chuyển khoản" % t,
		remarks="Thu tiền", flags=Doi(), references=[Doi(reference_name="HDB-" + t, allocated_amount=500000.0)])
		for t in nhap}

	def get_doc(dt, *a, **k):
		return pts[a[0]] if dt == "Payment Entry" else doc
	th.dat(fr, "get_all", get_all)
	th.dat(fr, "get_doc", get_doc)
	th.dat(fr, "set_user", lambda u: setattr(fr.session, "user", u))
	th.dat(fr.session, "user", "ntla.3008@gmail.com")
	th.dat(fr, "delete_doc", lambda dt, ten, **k: nk.append(("xoa", dt, ten)))
	doc["_pts"] = pts
	th.dat(cn, "_kiem_quyen_ban", lambda: None)
	return doc, nk, th


@ca("v577 huỷ phiếu kẹt kiểu Ms.Dung: GỠ phiếu thu NHÁP hỏng khỏi hoá đơn, KHÔNG xoá, ghi vết, rồi mới huỷ")
def _():
	# Codex #444 vòng 2 (QT-20): trên fe52e62 hai nháp bị delete_doc. Nay gỡ liên kết, giữ phiếu.
	doc, nk, th = _he_huy("Da thu du")
	try:
		kq = cn.huy_phieu("DNTT-26-10-00004", "Loan Anh")
		la("gỡ hai nháp hỏng", kq["da_go_nhap"], ["APP-26-10-134", "APP-26-10-150"])
		la("không xoá phiếu nào", [x for x in nk if x[0] == "xoa"], [])
		la("lưu bằng quyền hệ thống: hết dòng hoá đơn, khoá đổi sang GO:",
			[x[:4] + (x[4][:4],) for x in nk if x[0] == "luu_pt"],
			[("luu_pt", "APP-26-10-134", "Administrator", 0, "GO:T"),
			("luu_pt", "APP-26-10-150", "Administrator", 0, "GO:T")])
		dung("lưu bằng cờ máy gỡ (hook cho qua)", all(p.flags.get(tt.CO_MAY_GO_NHAP) for p in doc["_pts"].values()))
		vet = doc["_pts"]["APP-26-10-134"].remarks
		dung("ghi vết hoá đơn, số tiền, phiếu đòi nợ: " + vet[:160],
			"HDB-APP-26-10-134 500.000 đ" in vet and "DNTT-26-10-00004" in vet and "Không ghi sổ" in vet)
		la("trả lại người gọi", fr.session.user, "ntla.3008@gmail.com")
		la("tìm theo đúng mẫu khoá của phiếu", sorted({x[2] for x in nk if x[0] == "tim"}),
			["THU:%:phieu:DNTT-26-10-00004:%", "THU:%:phieu:DNTT-26-10-00004|%"])
		la("phiếu đã huỷ", doc.trang_thai, "Huy")
		dung("ghi lại đã dọn gì", any("APP-26-10-150" in x[1] for x in nk if x[0] == "binh_luan"))
	finally:
		th.tra()


@ca("v577 phiếu Đã thu đủ có giao dịch hay có phiếu thu vào sổ thì KHÔNG huỷ, không xoá gì")
def _():
	for ma_gd, da_ghi in (("FT-KIETTAC", ()), ("", ("APP-26-10-200",))):
		doc, nk, th = _he_huy("Da thu du", ma_gd=ma_gd, da_ghi=da_ghi)
		try:
			e = _bat(lambda: cn.huy_phieu("DNTT-26-10-00004", "x"))
			dung("phải chặn", e is not None and "không huỷ được" in str(e))
			la("không xoá, không lưu", [x for x in nk if x[0] in ("xoa", "luu", "luu_pt")], [])
			la("giữ trạng thái", doc.trang_thai, "Da thu du")
		finally:
			th.tra()


@ca("v577 huỷ phiếu chờ thu cũng dọn nháp hỏng của chính nó (lỗi SePay cũ), huỷ lần hai không làm gì")
def _():
	doc, nk, th = _he_huy("Cho thu", nhap=("APP-9",))
	try:
		la("gỡ", cn.huy_phieu("DNTT-26-10-00004", "x")["da_go_nhap"], ["APP-9"])
		la("đã huỷ", doc.trang_thai, "Huy")
		nk[:] = []
		la("lần hai trả về ngay", cn.huy_phieu("DNTT-26-10-00004", "x")["da_go_nhap"], [])
		la("không đụng gì thêm", [x for x in nk if x[0] in ("xoa", "luu_pt")], [])
	finally:
		th.tra()


# ------------------------------------------------------------ SePay


def _he_sepay(lap):
	nk = []
	th = Thay()

	class PhieuNo(Doi):
		def save(self, **k):
			nk.append(("luu", self.trang_thai))

		def add_comment(self, *a, **k):
			nk.append(("binh_luan", a[1]))

	doc = PhieuNo(name="P", ma_phieu="DNTT-26-10-00007", khach="OSHIMA", trang_thai="Cho thu", tong_tien=13000000.0,
		da_thu=0.0, ma_gd="", flags=Doi(), dong=[Doi(hoa_don="HD-OSH", khach="OSHIMA"), Doi(hoa_don="HD-VU", khach="VU")])

	def get_doc(dt, *a, **k):
		if dt == "Bank Transaction":
			nk.append(("nap_gd", a[0], k.get("for_update")))
			return Doi(name=a[0], reference_number="FT-" + a[0])
		return doc

	def get_all(dt, filters=None, **k):
		if dt == "Bank Transaction":
			return [Doi(name="BT-S", reference_number="FT-BT-S", deposit=13000000.0, withdrawal=0.0)]
		if dt == "Sales Invoice":
			if (filters or {}).get("outstanding_amount"):
				return ["HD-OSH", "HD-VU"]
			return [Doi(name="HD-OSH", customer="OSHIMA"), Doi(name="HD-VU", customer="VU")]
		return []
	th.dat(fr, "get_doc", get_doc)
	th.dat(fr, "get_all", get_all)
	th.dat(fr.db, "savepoint", lambda ten: nk.append(("diem_luu", ten)))
	th.dat(fr.db, "rollback", lambda save_point=None: nk.append(("lui", save_point)))
	th.dat(fr.db, "commit", lambda: nk.append(("commit",)))
	th.dat(cn, "_kiem_quyen_ban", lambda: None)
	th.dat(cn, "_giu_gd", lambda d, ds: "\n".join(ds))
	th.dat(cn, "_sepay_cn", lambda ma: {"nhan": 13000000.0, "so_gd": 1, "gd": ["BT-S"]})
	th.dat(cn, "_gui_thu_da_nhan", lambda d, **k: nk.append(("gui_thu",)) or (True, "x@y"))
	th.dat(cn, "xem_phieu", lambda name: {})
	th.dat(tt, "lap_phieu_thu_theo_gd", lambda cac_si, g, so, gc="", **k: lap(nk, cac_si, g, so, k))
	return doc, nk, th


@ca("v577 SePay tự khớp: lập phiếu thu NHÁP theo đúng giao dịch mới về, gom pháp nhân thì tách khách")
def _():
	def lap(nk, cac_si, g, so, k):
		nk.append(("lap", tuple(cac_si), g.name, so, k.get("tach_khach")))
		return {"pe": "APP-1, APP-2"}
	doc, nk, th = _he_sepay(lap)
	try:
		cn.kiem_sepay("P")
		la("lập theo giao dịch đã khoá, tách hai pháp nhân", [x for x in nk if x[0] in ("nap_gd", "lap")],
			[("nap_gd", "BT-S", True), ("lap", ("HD-OSH", "HD-VU"), "BT-S", 13000000.0, True)])
		la("đã thu đủ", doc.trang_thai, "Da thu du")
		la("không ghi bình luận lỗi", [x for x in nk if x[0] == "binh_luan"], [])
		dung("lập trước khi lưu phiếu", [x[0] for x in nk].index("lap") < [x[0] for x in nk].index("luu"))
		# Codex #444 F1: phiếu thu còn NHÁP, sổ cái vẫn nợ: chưa gửi thư "đã tất toán".
		la("chưa gửi thư khi sổ cái còn nợ", [x for x in nk if x[0] == "gui_thu"], [])
	finally:
		th.tra()


@ca("v577 SePay tự khớp mà lập phiếu thu hỏng: lùi ĐÚNG lần lập đó, vẫn ghi nhận tiền, ghi rõ lý do lên phiếu")
def _():
	def lap(nk, cac_si, g, so, k):
		raise fr.ValidationError(tt.cau_gd_lon_hon("FT-BT-S", 13000000, 9550000))
	doc, nk, th = _he_sepay(lap)
	try:
		cn.kiem_sepay("P")
		la("mở và lùi đúng điểm lưu", [x for x in nk if x[0] in ("diem_luu", "lui")],
			[("diem_luu", "vgb_sepay_lap"), ("lui", "vgb_sepay_lap")])
		la("tiền vẫn ghi nhận", doc.da_thu, 13000000.0)
		bl = [x[1] for x in nk if x[0] == "binh_luan"]
		la("một bình luận", len(bl), 1)
		dung("có lý do và chỉ đường: " + (bl[0] if bl else "")[:120], "dư 3.450.000 đ" in bl[0] and "Khớp tay" in bl[0])
		dung("bình luận trước commit", [x[0] for x in nk].index("binh_luan") < [x[0] for x in nk].index("commit"))
	finally:
		th.tra()


# ------------------------------------------------------------ thư báo


@ca("v577 thư báo nhận tiền phiếu gom: gửi MỌI pháp nhân, kính gửi đủ tên, khách đứng tên trước")
def _():
	gui = []
	th = Thay()
	doc = Doi(name="P", ma_phieu="DNTT-26-10-00007", khach="VU", ten_khach="Anh Vũ Oshima", tong_tien=13000000.0,
		da_thu=13000000.0, email_da_gui=0,
		dong=[Doi(hoa_don="HD-1", khach="OSHIMA", so_tien=3000000.0), Doi(hoa_don="HD-2", khach="VU", so_tien=10000000.0)])
	doc.db_set = lambda *a, **k: gui.append(("db_set",) + a)
	doc.add_comment = lambda *a, **k: gui.append(("bl", a[1]))
	th.dat(cn, "_email_khach", lambda k: {"OSHIMA": "ketoan@oshima.vn", "VU": "vu@gmail.com"}.get(k, ""))
	th.dat(cn, "_cac_khach_phieu", lambda d: [{"khach": "OSHIMA", "ten": "Công ty TNHH Oshima's"},
		{"khach": "VU", "ten": "Anh Vũ Oshima"}])
	th.dat(cn, "_thu_da_nhan_html", lambda d, ds: "Kính gửi " + cn._ten_kinh_gui(d))
	th.dat(fr, "sendmail", lambda **k: gui.append(("mail", k["recipients"], k["message"])))
	try:
		da, toi = cn._gui_thu_da_nhan(doc)
		la("gửi được", da, True)
		mail = [x for x in gui if x[0] == "mail"]
		la("một thư, đủ hai pháp nhân, khách đứng tên trước", [x[1] for x in mail], ["vu@gmail.com, ketoan@oshima.vn"])
		la("kính gửi đủ tên", mail[0][2], "Kính gửi Công ty TNHH Oshima's và Anh Vũ Oshima")
		dung("ghi lại gửi tới ai", ("db_set", "email_gui_toi", "vu@gmail.com, ketoan@oshima.vn") in gui)
	finally:
		th.tra()


# ------------------------------------------- Codex #444: thư khi sổ sạch, tìm trên máy chủ


@ca("Codex #444 F2: tìm giao dịch theo nội dung, mã, hoặc số tiền gõ có dấu chấm")
def _():
	k = tt.gd_khop_tu_khoa
	dung("nội dung", k("kiet tac", "Kiet Tac doi soat Vagabond 8.9", "FT1", 9550000))
	dung("mã", k("ft26278", "abc", "FT26278XYZ", 1))
	dung("số tiền có dấu chấm", k("9.550.000", "abc", "FT1", 9550000.0))
	dung("số tiền có chữ đ", k("9.550.000 đ", "abc", "FT1", 9550000.0))
	dung("không khớp số khác", not k("9.550.000", "abc", "FT1", 8450000.0))
	dung("số quá ngắn không dò theo tiền", not k("55", "abc", "FT1", 9550000.0))
	dung("trống là khớp hết", k("", "abc", "FT1", 1))


@ca("Codex #444 F2: máy chủ tìm trên TOÀN BỘ giao dịch chưa nối, kể cả khoản ngoài 300 dòng mới nhất")
def _():
	BT = [Doi(name="BT-%d" % i, date="2026-10-01", description="khach le %d" % i, deposit=100000.0 + i,
		bank_account="MB", reference_number="FT-%d" % i, unallocated_amount=100000.0 + i) for i in range(400)]
	BT.append(Doi(name="BT-KT", date="2026-06-10", description="Kiet Tac doi soat", deposit=9550000.0,
		bank_account="MB", reference_number="FT-KIETTAC", unallocated_amount=9550000.0))
	th = Thay()
	th.dat(fr, "get_all", lambda dt, filters=None, **k: [Doi(b) for b in BT] if dt == "Bank Transaction" else [])
	th.dat(cn, "_kiem_quyen_ban", lambda: None)
	try:
		het = cn.tim_giao_dich_thu(so_tien=8450000, chua_noi=1)
		la("không gõ: 300 dòng, báo còn", (len(het["rows"]), het["con_nua"]), (300, 101))
		dung("khoản Kiệt Tác nằm ngoài 300 dòng", "FT-KIETTAC" not in [r["ma"] for r in het["rows"]])
		la("gõ tên khách thì ra", [r["ma"] for r in cn.tim_giao_dich_thu(tu_khoa="kiet tac", so_tien=8450000, chua_noi=1)["rows"]],
			["FT-KIETTAC"])
		la("gõ số tiền thì ra", [r["ma"] for r in cn.tim_giao_dich_thu(tu_khoa="9.550.000", so_tien=8450000, chua_noi=1)["rows"]],
			["FT-KIETTAC"])
	finally:
		th.tra()


@ca("Codex #444 F1: thư báo nhận tiền chỉ gửi khi sổ cái hết nợ mọi hoá đơn của phiếu")
def _():
	gui = []
	con_no = {"v": ["HD-1"]}
	th = Thay()
	th.dat(fr, "get_all", lambda dt, filters=None, **k: list(con_no["v"]) if dt == "Sales Invoice" else [])
	th.dat(cn, "_gui_thu_da_nhan", lambda d, **k: gui.append(d.name) or (True, "x@y"))
	try:
		d = Doi(name="P", trang_thai="Da thu du", email_da_gui=0, dong=[Doi(hoa_don="HD-1"), Doi(hoa_don="HD-2")])
		la("sổ còn nợ: không gửi", cn._gui_thu_khi_sach(d), False)
		con_no["v"] = []
		la("sổ sạch: gửi", cn._gui_thu_khi_sach(d), True)
		d.email_da_gui = 1
		la("đã gửi rồi: không gửi lại", cn._gui_thu_khi_sach(Doi(d)), False)
		la("phiếu chưa thu đủ: không gửi", cn._gui_thu_khi_sach(Doi(d, trang_thai="Thu thieu", email_da_gui=0)), False)
		la("đúng một thư", gui, ["P"])
	finally:
		th.tra()


@ca("Codex #444 F1: kế toán ghi sổ phiếu thu cuối thì phiếu đòi nợ chứa hoá đơn đó gửi thư, phiếu khác không")
def _():
	gui = []
	phieu = {"P1": Doi(name="P1", trang_thai="Da thu du", email_da_gui=0, dong=[Doi(hoa_don="HD-1")]),
		"P2": Doi(name="P2", trang_thai="Da thu du", email_da_gui=0, dong=[Doi(hoa_don="HD-2")])}
	hoi = []
	th = Thay()

	def get_all(dt, filters=None, **k):
		if dt == "Vagabond Cong No Dong":
			hoi.append(sorted(filters["hoa_don"][1]))
			return ["P1"]
		if dt == "Sales Invoice":
			return []
		return []
	th.dat(fr, "get_all", get_all)
	th.dat(fr, "get_doc", lambda dt, ten, **k: phieu[ten])
	th.dat(cn, "_gui_thu_da_nhan", lambda d, **k: gui.append(d.name) or (True, "x@y"))
	try:
		la("gửi đúng phiếu", cn.gui_thu_sau_ghi_so(["HD-1"]), ["P1"])
		la("hỏi theo hoá đơn của phiếu thu", hoi, [["HD-1"]])
		la("một thư", gui, ["P1"])
	finally:
		th.tra()


@ca("Codex #444 F1: ghi sổ phiếu thu THÀNH CÔNG thì gọi gửi thư theo hoá đơn của phiếu; ghi sổ hỏng thì không")
def _():
	from vagabond.khung.kiem_thu.thu_gom_phap_nhan_575 import _bo_phieu, _ghi_so
	goi = []
	th = Thay()
	th.dat(fr, "get_attr", lambda duong: (lambda ds: goi.append((duong, list(ds)))))
	try:
		nk, cac, g = _bo_phieu("KHAC")
		cac["APP-1"].references = [Doi(reference_doctype="Sales Invoice", reference_name="HD-OSH")]
		cac["APP-2"].references = [Doi(reference_doctype="Sales Invoice", reference_name="HD-VU")]
		la("phiếu 1 vào sổ", _ghi_so("APP-1", cac, g).get("ok"), 1)
		la("gọi gửi thư đúng hoá đơn", goi, [("vagabond.cong_no.gui_thu_sau_ghi_so", ["HD-OSH"])])
		e = _bat(lambda: _ghi_so("APP-2", cac, g))
		dung("phiếu khác nhóm bị chặn", e is not None)
		la("ghi sổ hỏng không gọi gửi thư", len(goi), 1)
	finally:
		th.tra()


@ca("Codex #444 F1: màn phiếu nhận số hoá đơn còn nợ trên sổ cái khi phiếu đã thu đủ, để không báo công nợ đã sạch")
def _():
	con_no = {"v": ["HD-1", "HD-2"]}
	th = Thay()
	doc = Doi(name="P", ma_phieu="DNTT-26-10-00007", khach="K", ten_khach="K", ngay_tao="", han_qr="",
		tong_tien=2.0, da_thu=2.0, trang_thai="Da thu du", ghi_chu="", ma_gd="BT-1",
		dong=[Doi(hoa_don="HD-1", ngay="", nguon="", so_tien=1.0), Doi(hoa_don="HD-2", ngay="", nguon="", so_tien=1.0)])
	th.dat(fr, "get_doc", lambda *a, **k: doc)
	th.dat(fr, "get_all", lambda dt, filters=None, **k: list(con_no["v"]) if dt == "Sales Invoice" else [])
	for ten, gt in (("_kiem_quyen_ban", lambda: None), ("_sepay_cn", lambda ma: {}), ("_da_nhan_phieu", lambda d, s: 2.0),
			("_hd_chua_co_phieu_thu", lambda ds: set()), ("_cac_khach_phieu", lambda d: []), ("_so_hd_gtgt", lambda hd: ""),
			("_phieu_thu_cua_phieu", lambda t, ds: []), ("_la_ke_toan", lambda: False)):
		th.dat(cn, ten, gt)
	th.dat(cn.tai_khoan, "tk_phieu_no", lambda: {})
	try:
		la("phiếu thu còn nháp: 2 hoá đơn chờ ghi sổ", cn.xem_phieu("P")["cho_ghi_so"], 2)
		# Codex #444 vòng 3: hoá đơn chưa có phiếu thu nào (lập nháp hỏng) không tính là chờ ghi sổ.
		th.dat(cn, "_hd_chua_co_phieu_thu", lambda ds: {"HD-1"})
		la("hoá đơn thiếu phiếu thu không tính chờ ghi sổ", cn.xem_phieu("P")["cho_ghi_so"], 1)
		con_no["v"] = []
		la("sổ sạch: 0", cn.xem_phieu("P")["cho_ghi_so"], 0)
	finally:
		th.tra()



@ca("Codex #444 vòng 2: thư gửi từ giữa request ghi sổ (chưa commit) thì XẾP HÀNG trong giao dịch, không gửi ngay")
def _():
	gui = []
	th = Thay()
	doc = Doi(name="P", ma_phieu="DNTT-1", khach="K", ten_khach="K", tong_tien=1.0, da_thu=1.0, email_da_gui=0,
		trang_thai="Da thu du", dong=[Doi(hoa_don="HD-1", khach="K", so_tien=1.0)])
	doc.db_set = lambda *a, **k: None
	doc.add_comment = lambda *a, **k: None
	th.dat(cn, "_email_khach", lambda k: "k@x.vn")
	th.dat(cn, "_thu_da_nhan_html", lambda d, ds: "thu")
	th.dat(fr, "sendmail", lambda **k: gui.append(k["delayed"]))
	th.dat(fr, "get_all", lambda dt, filters=None, **k: ["P"] if dt == "Vagabond Cong No Dong" else [])
	th.dat(fr, "get_doc", lambda *a, **k: doc)
	try:
		cn._gui_thu_da_nhan(Doi(doc))
		la("gửi tay (đã commit): gửi ngay như cũ", gui, [False])
		la("sau ghi sổ: một phiếu", cn.gui_thu_sau_ghi_so(["HD-1"]), ["P"])
		la("sau ghi sổ: xếp hàng", gui, [False, True])
	finally:
		th.tra()



@ca("bench #444: mã phiếu không đúng mẫu thì đọc SePay trả rỗng đủ HAI giá trị, xem phiếu không nổ")
def _():
	# Trên fe52e62 bench đỏ: _sepay_theo_ma_cn trả {} một giá trị, _sepay_cn gỡ hai giá trị.
	la("không mã hợp lệ", cn._sepay_theo_ma_cn(["DNTT-KT576-abcdef", ""]), ({}, []))
	la("đọc một mã lạ", cn._sepay_cn("PHIEU-TU-CHE"), {})



@ca("Codex #444 vòng 3: phiếu thu đã GỠ không ghi sổ được, không đổi khoá về được, người không tự đánh dấu được")
def _():
	f = tt.ly_do_chan_nhap_da_go
	G = "GO:THU:HDB-1:phieu:DNTT-1:tay:x|Chuyển khoản"
	dung("ghi sổ phiếu đã gỡ: chặn", "không ghi sổ được" in f(G, G, 1, False, "APP-1"))
	dung("đổi khoá về THU: chặn", "không đổi số tham chiếu" in f("THU:HDB-1", G, 0, False, "APP-1"))
	dung("người tự gắn GO: chặn", "Chỉ máy" in f(G, "THU:HDB-1", 0, False))
	la("máy gỡ: cho qua", f(G, "THU:HDB-1", 0, True), "")
	la("lưu lại phiếu đã gỡ không đổi khoá: cho qua", f(G, G, 0, False), "")
	la("phiếu thường: cho qua", f("FT123", "FT123", 1, False), "")
	la("phiếu mới thường: cho qua", f("FT9", None, 0, False), "")


@ca("Codex #444 vòng 3: hook validate thật chặn ghi sổ phiếu đã gỡ trên Desk")
def _():
	th = Thay()
	th.dat(fr.db, "get_value", lambda dt, ten, f=None, **k: "GO:THU:HDB-1:phieu:DNTT-1:tay:x|Chuyển khoản")

	class PE(Doi):
		def is_new(self):
			return False
	try:
		pe = PE(doctype="Payment Entry", name="APP-26-10-134", reference_no="GO:THU:HDB-1:phieu:DNTT-1:tay:x|Chuyển khoản",
			docstatus=1, flags=Doi())
		e = _bat(lambda: tt.chan_nhap_da_go(pe))
		dung("chặn ghi sổ: " + str(e)[:80], e is not None and "APP-26-10-134" in str(e))
		pe.docstatus = 0
		la("lưu nháp giữ khoá: qua", _bat(lambda: tt.chan_nhap_da_go(pe)), None)
		la("doctype khác: bỏ qua", _bat(lambda: tt.chan_nhap_da_go(PE(doctype="Journal Entry", flags=Doi()))), None)
	finally:
		th.tra()
