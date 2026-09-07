# -*- coding: utf-8 -*-
"""Ghi nhận thanh toán trong MỘT giao dịch, đủ bộ chứng từ (v445, 07/09/2026).

Codex rà soát #225 và chỉ ra bốn lỗ ở `danh_dau_da_tra`:
  R1  hai hàm con tự commit trước khi hồ sơ lưu, khoá nhả sớm, retry sinh
      thêm bút toán; lỗi lấy khoá bị nuốt rồi chạy tiếp.
  R2  tham số `tao_but_toan=0` cho hồ sơ "Đã thanh toán" mà không bút toán.
  R4  `flt(con_lai) or flt(tong_tien)` coi số 0 là "chưa có số".
  R6  `allocated = min(đề nghị, nợ)` còn `paid_amount` là cả tổng: phần dư
      thành khoản ứng trước nhà cung cấp không ai duyệt.

MỌI ca dưới đây CHẠY hàm thật với Frappe giả lập, không dò chuỗi mã nguồn
(bài học #205, điều 16). Mỗi ca dựng đúng chuỗi thao tác của kế toán, không
gọi thêm hàm nào "cho chắc" (điều 15).
"""

import types

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la


# ------------------------------------------------------------- dụng cụ giả


class _Co(dict):
	"""doc.flags giả: dict truy cập được bằng dấu chấm và get()."""

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


class _Doc(object):
	"""Vagabond Ho So TT giả: chỉ đủ cho `danh_dau_da_tra`."""

	def __init__(self, **o):
		o["dong"] = [d if isinstance(d, Doi) else Doi(d) for d in (o.get("dong") or [])]
		self.__dict__.update(o)
		self.flags = _Co()
		self.nhat_ky = o.get("nhat_ky") or []

	def get(self, k, mac=None):
		return self.__dict__.get(k, mac)

	def save(self, **k):
		self.nhat_ky.append("save")


def _dong(hoa_don, so_tien, con_no=None):
	# Dong con cua Frappe doc duoc bang dau cham lan get(), nhu Doi.
	return Doi({"hoa_don": hoa_don, "so_tien": so_tien, "con_no": con_no if con_no is not None else so_tien})


def _ho_so(**o):
	d = dict(name="APP.26.09.001", trang_thai="Da duyet", loai="NCC",
		dong=[_dong("HDM-1", 100.0)], tong_tien=100.0, da_tam_ung=0.0, con_lai=100.0,
		ten_ncc="NCC A", nha_cung_cap="NCC-A", email_ncc="", ghi_chu="", tk_chi="",
		ma_giao_dich="", loai_cp_thue="")
	d.update(o)
	return _Doc(**d)


class _Vet(object):
	"""Vá tạm các hàm của mô đun, và trả lại nguyên trạng khi xong."""

	def __init__(self, **o):
		self.o = o
		self.cu = {}

	def __enter__(self):
		from vagabond import ho_so_tt as hs

		for k, v in self.o.items():
			self.cu[k] = getattr(hs, k)
			setattr(hs, k, v)
		return self

	def __exit__(self, *a):
		from vagabond import ho_so_tt as hs

		for k, v in self.cu.items():
			setattr(hs, k, v)


class _San(object):
	"""Sân giả cho một lượt ghi nhận: khoá, hồ sơ, bút toán có sẵn, SePay, UNC.

	`nhat_ky` ghi THỨ TỰ các việc chạm hệ, để chốt commit đứng sau save và
	thư đứng sau commit.
	"""

	def __init__(self, doc, bo_san=None, chi=100.0, du_unc=True, khoa_hong=False):
		self.doc = doc
		self.bo_san = bo_san if bo_san is not None else []
		self.chi = chi
		self.du_unc = du_unc
		self.khoa_hong = khoa_hong
		self.nhat_ky = doc.nhat_ky
		self.goi_tao = 0
		self.goi_thu = 0

	def __enter__(self):
		import frappe
		from vagabond import ho_so_tt as hs
		from vagabond import tra_tien_app

		self.fr_cu = {"get_value": frappe.db.get_value, "commit": frappe.db.commit,
			"get_doc": frappe.get_doc}
		san = self

		def _get_value(dt, name=None, fieldname=None, *a, **k):
			if k.get("for_update"):
				san.nhat_ky.append("khoa")
				if san.khoa_hong:
					raise Exception("Lock wait timeout exceeded")
				return san.doc.trang_thai
			return None

		def _get_doc(dt, name=None, *a, **k):
			san.nhat_ky.append("get_doc")
			return san.doc

		def _commit(*a, **k):
			san.nhat_ky.append("commit")

		frappe.db.get_value = _get_value
		frappe.db.commit = _commit
		frappe.get_doc = _get_doc

		self.ttx_cu = (tra_tien_app.dem_unc, tra_tien_app.du_unc)
		tra_tien_app.dem_unc = lambda name: 1 if san.du_unc else 0
		tra_tien_app.du_unc = lambda n: bool(n)

		def _tao(doc, ngay, pt):
			san.goi_tao += 1
			san.nhat_ky.append("tao_but_toan")
			# But toan vua sinh xuat hien trong lan doc ke tiep.
			san.bo_san = [_pe("PE-MOI", [("HDM-1", 100.0)])]
			return "PE-MOI"

		def _bo(name):
			san.nhat_ky.append("doc_bo")
			return list(san.bo_san)

		def _thu(doc, gui_thu=1):
			san.goi_thu += 1
			san.nhat_ky.append("thu")
			return {"gui": 0, "vi_sao": "giả lập"}

		self.va = _Vet(
			_tao_but_toan=_tao, _but_toan_cua_ho_so=_bo, _tu_gui_thu_bao=_thu,
			_ghi_vet=lambda *a, **k: san.nhat_ky.append("vet"),
			_sepay_theo_ma_app=lambda ds: {san.doc.name: {"chi": san.chi, "so_gd": 1}},
			_kiem=lambda *a, **k: None,
		)
		self.va.__enter__()
		return self

	def __exit__(self, *a):
		import frappe
		from vagabond import tra_tien_app

		self.va.__exit__(*a)
		frappe.db.get_value = self.fr_cu["get_value"]
		frappe.db.commit = self.fr_cu["commit"]
		frappe.get_doc = self.fr_cu["get_doc"]
		tra_tien_app.dem_unc, tra_tien_app.du_unc = self.ttx_cu


def _pe(ten, phan_bo, party="NCC-A"):
	return {"doctype": "Payment Entry", "name": ten, "company": "TV", "party": party,
		"tham_chieu": [{"reference_name": h, "allocated_amount": t} for h, t in phan_bo]}


def _je(ten, tong):
	return {"doctype": "Journal Entry", "name": ten, "company": "TV", "tong_no": tong}


def _loi(ham):
	"""Gọi hàm phải ném lỗi; trả về câu lỗi để soi chữ."""
	try:
		ham()
	except Exception as e:
		return str(e)
	return ""


# ============================================ R2: đường bỏ qua bút toán đã đóng


@ca("v445 R2: tao_but_toan=0 bị từ chối ngay, chưa đụng tới hồ sơ")
def _r2_tu_choi():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc) as san:
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001", tao_but_toan=0))
	dung("có ném lỗi", bool(cau))
	dung("câu nói rõ đường đã đóng", "bỏ qua bút toán" in cau)
	la("chưa khoá, chưa đọc hồ sơ, chưa làm gì", san.nhat_ky, [])
	la("trạng thái không đổi", doc.trang_thai, "Da duyet")


@ca("v445 R2: tham số dạng chuỗi '0' từ caller cũ cũng bị chặn")
def _r2_chuoi():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc):
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001", tao_but_toan="0"))
	dung("chặn cả '0' dạng chuỗi", "bỏ qua bút toán" in cau)


# ========================================== R1: khoá, một giao dịch, retry


@ca("v445 R1: không giữ được khoá thì DỪNG, không đọc hồ sơ, không sinh gì")
def _r1_khoa_hong():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc, khoa_hong=True) as san:
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
	dung("ném lỗi khoá", "khoá" in cau)
	la("chỉ mới thử khoá", san.nhat_ky, ["khoa"])
	la("không sinh bút toán", san.goi_tao, 0)
	la("trạng thái không đổi", doc.trang_thai, "Da duyet")


@ca("v445 R1: lượt ghi nhận bình thường: sinh bút toán, lưu hồ sơ, rồi MỘT commit, rồi mới thư")
def _r1_mot_giao_dich():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc) as san:
		kq = hs.danh_dau_da_tra("APP.26.09.001", ma_giao_dich="FT1")
	la("ok", kq["ok"], 1)
	la("trạng thái Đã thanh toán", doc.trang_thai, "Da thanh toan")
	la("bút toán trả về", kq["but_toan"], "PE-MOI")
	la("đúng một commit trong cả lượt", san.nhat_ky.count("commit"), 1)
	nk = san.nhat_ky
	dung("khoá trước khi đọc hồ sơ", nk.index("khoa") < nk.index("get_doc"))
	dung("bút toán sinh trước khi lưu hồ sơ", nk.index("tao_but_toan") < nk.index("save"))
	dung("commit đứng SAU lưu hồ sơ", nk.index("save") < nk.index("commit"))
	dung("thư đi SAU commit", nk.index("commit") < nk.index("thu"))
	la("thư gửi đúng một lần", san.goi_thu, 1)
	dung("hồ sơ mang cờ đã đối chiếu bộ chứng từ", bool(doc.flags.get("vgb_bo_chung_tu_da_kiem")))
	la("bộ chứng từ đủ", kq["bo_chung_tu"]["du"], 1)


@ca("v445 R1: retry sau khi lượt trước đã ghi sổ ĐỦ bộ: dùng lại, KHÔNG sinh thêm")
def _r1_retry_du():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc, bo_san=[_pe("PE-CU", [("HDM-1", 100.0)])]) as san:
		kq = hs.danh_dau_da_tra("APP.26.09.001")
	la("không sinh bút toán mới", san.goi_tao, 0)
	la("trả lại đúng bút toán cũ", kq["but_toan"], "PE-CU")
	la("hồ sơ hoàn tất", doc.trang_thai, "Da thanh toan")
	la("vẫn một commit", san.nhat_ky.count("commit"), 1)


@ca("v445 R1: retry mà bộ cũ THIẾU/LỆCH thì dừng, liệt kê, không tự sinh bù")
def _r1_retry_thieu():
	from vagabond import ho_so_tt as hs

	# Ho so hai hoa don, luot truoc chi ghi so duoc mot to (PE thu hai hong).
	doc = _ho_so(dong=[_dong("HDM-1", 60.0), _dong("HDM-2", 40.0)])
	with _San(doc, bo_san=[_pe("PE-CU", [("HDM-1", 60.0)])]) as san:
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
	dung("ném lỗi bộ chưa khớp", "chưa khớp" in cau)
	dung("nói rõ thiếu hoá đơn nào", "HDM-2" in cau)
	la("không sinh bù", san.goi_tao, 0)
	la("không commit", san.nhat_ky.count("commit"), 0)
	la("trạng thái giữ nguyên", doc.trang_thai, "Da duyet")

	# Lech so: phan bo 40 cho hoa don 100.
	doc = _ho_so()
	with _San(doc, bo_san=[_pe("PE-CU", [("HDM-1", 40.0)])]) as san:
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
	dung("lệch số cũng dừng", "lệch" in cau and "HDM-1" in cau)
	la("không sinh bù khi lệch", san.goi_tao, 0)


@ca("v445 R1: bấm lại hồ sơ ĐÃ thanh toán: trả về cùng bộ chứng từ, không thư, không sinh")
def _r1_da_lam_roi():
	from vagabond import ho_so_tt as hs

	doc = _ho_so(trang_thai="Da thanh toan")
	with _San(doc, bo_san=[_pe("PE-CU", [("HDM-1", 100.0)])]) as san:
		kq = hs.danh_dau_da_tra("APP.26.09.001")
	la("báo đã làm rồi", kq["da_lam_roi"], 1)
	la("trả đúng bút toán cũ", kq["but_toan"], "PE-CU")
	la("không sinh", san.goi_tao, 0)
	la("không thư lần hai", san.goi_thu, 0)
	la("không commit", san.nhat_ky.count("commit"), 0)


@ca("v445 R1: bút toán vừa sinh mà đọc lại không khớp kế hoạch thì ném lỗi, không lưu hồ sơ")
def _r1_vua_sinh_lech():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc) as san:
		# Sinh xong nhung hook tang duoi lam lech phan bo con 90.
		def _tao(d, ngay, pt):
			san.goi_tao += 1
			san.bo_san = [_pe("PE-MOI", [("HDM-1", 90.0)])]
			return "PE-MOI"
		with _Vet(_tao_but_toan=_tao):
			cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
	dung("dừng vì lệch", "không khớp" in cau)
	la("hồ sơ chưa lưu", san.nhat_ky.count("save"), 0)
	la("không commit", san.nhat_ky.count("commit"), 0)
	la("trạng thái giữ nguyên", doc.trang_thai, "Da duyet")


@ca("v445 R1: không đọc được danh sách bút toán (ô chưa dựng) thì dừng, không coi là chưa có")
def _r1_khong_doc_duoc():
	import frappe
	from vagabond import ho_so_tt as hs

	cu = frappe.get_all

	def _no(dt, **k):
		if dt == "Journal Entry":
			raise Exception("Unknown column 'vgb_ho_so_tt'")
		return []

	frappe.get_all = _no
	try:
		cau = _loi(lambda: hs._but_toan_cua_ho_so("APP.26.09.001"))
	finally:
		frappe.get_all = cu
	dung("ném lỗi chứ không trả rỗng", "Chưa đọc được" in cau)


# ========================================== R1: hai hàm con không commit


class _PEGia(object):
	def __init__(self, dt):
		self.doctype = dt
		self.references = []
		self.accounts = []
		self.flags = _Co()
		self.source_exchange_rate = 1
		self.paid_from_account_currency = "VND"
		self.name = dt.replace(" ", "-") + "-GIA"
		self.viec = []

	def append(self, bang, dong):
		getattr(self, bang).append(dict(dong))
		return types.SimpleNamespace(**dong)

	def precision(self, f):
		return 2

	def setup_party_account_field(self):
		self.viec.append("setup")

	def set_missing_values(self):
		self.viec.append("missing")

	def insert(self, **k):
		self.viec.append("insert")

	def submit(self):
		self.viec.append("submit")


class _SanButToan(object):
	"""Sân cho `_tao_but_toan`: hoá đơn mua, tài khoản chi, không có Mode of Payment."""

	def __init__(self, hoa_don):
		self.hoa_don = hoa_don   # {ten: dict cua Purchase Invoice}
		self.pe = []
		self.commit = 0

	def __enter__(self):
		import frappe
		from vagabond import chung_tu_tien, tra_tien_app

		san = self
		self.cu = (frappe.db.get_value, frappe.db.exists, frappe.db.commit, frappe.new_doc
			if hasattr(frappe, "new_doc") else None, frappe.db.get_single_value
			if hasattr(frappe.db, "get_single_value") else None)

		def _gv(dt, name=None, fieldname=None, *a, **k):
			if dt == "Purchase Invoice":
				return dict(san.hoa_don.get(name) or {})
			if dt == "Supplier":
				return "Nhà %s" % name
			if dt == "Company":
				return "VND" if fieldname == "default_currency" else "TV - Chính"
			if dt == "Account":
				return "VND" if fieldname == "account_currency" else "Payable"
			if dt == "Bank Account":
				return "11211 - MB"
			return None

		def _new(dt):
			p = _PEGia(dt)
			san.pe.append(p)
			return p

		frappe.db.get_value = _gv
		frappe.db.exists = lambda *a, **k: False
		frappe.db.commit = lambda *a, **k: setattr(san, "commit", san.commit + 1)
		frappe.db.get_single_value = lambda *a, **k: "TV"
		frappe.new_doc = _new
		self.ttx = (tra_tien_app.tk_tien_chi, tra_tien_app.chep_unc, chung_tu_tien.dat_dien_giai)
		tra_tien_app.tk_tien_chi = lambda cty, pt, tk: ("11211 - MB", "MB-1")
		tra_tien_app.chep_unc = lambda *a, **k: 1
		chung_tu_tien.dat_dien_giai = lambda pe, s: None
		return self

	def __exit__(self, *a):
		import frappe
		from vagabond import chung_tu_tien, tra_tien_app

		frappe.db.get_value, frappe.db.exists, frappe.db.commit, nd, gsv = self.cu
		if nd is None:
			del frappe.new_doc
		else:
			frappe.new_doc = nd
		if gsv is None:
			del frappe.db.get_single_value
		else:
			frappe.db.get_single_value = gsv
		tra_tien_app.tk_tien_chi, tra_tien_app.chep_unc, chung_tu_tien.dat_dien_giai = self.ttx


def _pi(supplier="NCC-A", no=100.0, docstatus=1, company="TV"):
	return {"supplier": supplier, "company": company, "grand_total": 100.0,
		"outstanding_amount": no, "due_date": "2026-09-10", "docstatus": docstatus, "currency": "VND"}


@ca("v445 R1: _tao_but_toan sinh và ghi sổ Payment Entry nhưng KHÔNG commit")
def _r1_pe_khong_commit():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _SanButToan({"HDM-1": _pi()}) as san:
		ten = hs._tao_but_toan(doc, "2026-09-07", "Chuyển khoản")
	la("một Payment Entry", len(san.pe), 1)
	la("đã insert rồi submit", san.pe[0].viec[-2:], ["insert", "submit"])
	la("trả tên phiếu", ten, san.pe[0].name)
	la("không commit trong hàm con", san.commit, 0)


@ca("v445 R1: _tao_but_toan_tkct gán vgb_ho_so_tt lên Journal Entry và KHÔNG commit")
def _r1_je_link():
	from vagabond import ho_so_tt as hs

	doc = _ho_so(loai="TK cong ty", tk_chi="MB-1",
		dong=[{"hoa_don": "", "so_tien": 70.0, "tk_no": "6427 - Chi khác", "tk_co": "", "noi_dung": "Điện"}])
	with _SanButToan({}) as san:
		ten = hs._tao_but_toan_tkct(doc, "2026-09-07", "Chuyển khoản")
	la("một Journal Entry", len(san.pe), 1)
	je = san.pe[0]
	la("bút toán trỏ ngược về hồ sơ", getattr(je, "vgb_ho_so_tt", None), "APP.26.09.001")
	la("đã submit", je.viec[-1], "submit")
	la("không commit trong hàm con", san.commit, 0)
	la("trả tên phiếu", ten, je.name)


@ca("v445 R1: ô vgb_ho_so_tt được khai cho Journal Entry, cùng tên với Payment Entry")
def _r1_khai_o_je():
	from vagabond import nghiep_vu_tien as nvt

	je = nvt.TRUONG_MOI.get("Journal Entry") or []
	o = [f for f in je if f["fieldname"] == "vgb_ho_so_tt"]
	la("có đúng một ô", len(o), 1)
	la("là Link tới hồ sơ", (o[0]["fieldtype"], o[0]["options"]), ("Link", "Vagabond Ho So TT"))
	pe = [f for f in nvt.TRUONG_MOI["Payment Entry"] if f["fieldname"] == "vgb_ho_so_tt"]
	la("Payment Entry vẫn giữ ô cũ", len(pe), 1)
	la("một phép tra đọc cả hai", hs_dt(), ("Payment Entry", "Journal Entry"))


def hs_dt():
	from vagabond import ho_so_tt as hs

	return tuple(hs.DT_BUT_TOAN)


# ================================================= R6: công nợ lúc ghi sổ


@ca("v445 R6: nợ còn 40 mà đề nghị 100 thì ném lỗi, nêu rõ nợ lúc duyệt và nợ hiện tại")
def _r6_thieu_no():
	from vagabond import ho_so_tt as hs

	cau = _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 100.0, _pi(no=40.0), 100.0, "TV", 2))
	dung("ném lỗi", bool(cau))
	dung("nêu nợ hiện tại", "40" in cau)
	dung("nêu là đổi sau khi duyệt", "sau khi duyệt" in cau)
	dung("nói máy không tự cắt", "KHÔNG tự cắt" in cau)


@ca("v445 R6: trả một phần (nợ 100, đề nghị 40) vẫn hợp lệ, không bị chặn")
def _r6_tra_mot_phan():
	from vagabond import ho_so_tt as hs

	la("không ném", _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 40.0, _pi(no=100.0), 100.0, "TV", 2)), "")
	# Bang dung so cung qua.
	la("đủ đúng số cũng qua", _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 100.0, _pi(no=100.0), 100.0, "TV", 2)), "")


@ca("v445 R6: hoá đơn đã huỷ hoặc khác công ty thì dừng")
def _r6_huy_khac_cty():
	from vagabond import ho_so_tt as hs

	dung("huỷ thì dừng", "ghi sổ" in _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 10.0, _pi(docstatus=2), 100.0, "TV", 2)))
	dung("khác công ty thì dừng", "công ty" in _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 10.0, _pi(company="KHAC"), 100.0, "TV", 2)))


@ca("v445 R6: so theo số lẻ của khung: 99.999 với nợ 100.00 không bị coi là vượt, 100.004 cũng vậy")
def _r6_so_le():
	from vagabond import ho_so_tt as hs

	la("dưới nợ qua", _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 99.999, _pi(no=100.0), None, "TV", 2)), "")
	la("làm tròn 2 số lẻ bằng nợ thì qua", _loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 100.004, _pi(no=100.0), None, "TV", 2)), "")
	dung("vượt một xu thì chặn", bool(_loi(lambda: hs._kiem_hoa_don_luc_ghi_so("HDM-1", 100.01, _pi(no=100.0), None, "TV", 2))))


@ca("v445 R6: _tao_but_toan phân bổ ĐỦ số đề nghị, paid_amount bằng tổng phân bổ, không còn min()")
def _r6_khong_min():
	from vagabond import ho_so_tt as hs

	doc = _ho_so(dong=[_dong("HDM-1", 60.0), _dong("HDM-2", 40.0)])
	with _SanButToan({"HDM-1": _pi(no=60.0), "HDM-2": _pi(no=100.0)}) as san:
		hs._tao_but_toan(doc, "2026-09-07", "Chuyển khoản")
	pe = san.pe[0]
	la("hai dòng tham chiếu", len(pe.references), 2)
	la("phân bổ đúng kế hoạch", sorted((r["reference_name"], r["allocated_amount"]) for r in pe.references),
		[("HDM-1", 60.0), ("HDM-2", 40.0)])
	la("paid_amount bằng tổng phân bổ, không dư", pe.paid_amount, 100.0)


@ca("v445 R6: _tao_but_toan dừng khi MỘT hoá đơn thiếu nợ dù tổng nhóm vẫn đủ")
def _r6_tung_hoa_don():
	from vagabond import ho_so_tt as hs

	# Tong no 130 >= tong de nghi 100, nhung HDM-2 chi con 30 ma de nghi 40.
	doc = _ho_so(dong=[_dong("HDM-1", 60.0), _dong("HDM-2", 40.0)])
	with _SanButToan({"HDM-1": _pi(no=100.0), "HDM-2": _pi(no=30.0)}) as san:
		cau = _loi(lambda: hs._tao_but_toan(doc, "2026-09-07", "Chuyển khoản"))
	dung("dừng đúng hoá đơn thiếu", "HDM-2" in cau)
	dung("không có phiếu nào được submit", not any("submit" in p.viec for p in san.pe))


# ==================================================== R4: số 0 là số hợp lệ


@ca("v445 R4: _so_phai_chuyen: tạm ứng đủ 100% cho ra 0, không thành tổng")
def _r4_khong():
	from vagabond import ho_so_tt as hs

	so = hs._so_phai_chuyen(_ho_so(da_tam_ung=100.0, con_lai=0.0), 2)
	la("còn phải chuyển 0", so["con"], 0.0)
	la("tổng tính lại từ dòng", so["tong"], 100.0)
	so = hs._so_phai_chuyen(_ho_so(da_tam_ung=40.0, con_lai=60.0), 2)
	la("tạm ứng một phần", so["con"], 60.0)


@ca("v445 R4: ô tạm ứng TRỐNG (None) không được coi là 0")
def _r4_none():
	from vagabond import ho_so_tt as hs

	cau = _loi(lambda: hs._so_phai_chuyen(_ho_so(da_tam_ung=None, con_lai=None), 2))
	dung("ném lỗi nói ô trống", "ô trống" in cau)


@ca("v445 R4: còn lại âm là lỗi cần kiểm, không max(0), không miễn trừ 1 đồng")
def _r4_am():
	from vagabond import ho_so_tt as hs

	# Controller cho tam ung vuot tong toi 1 dong; o cua ghi nhan thi khong.
	cau = _loi(lambda: hs._so_phai_chuyen(_ho_so(da_tam_ung=100.5, con_lai=-0.5), 2))
	dung("âm nửa đồng vẫn chặn", "âm" in cau)
	cau = _loi(lambda: hs._so_phai_chuyen(_ho_so(da_tam_ung=-1.0, con_lai=101.0), 2))
	dung("tạm ứng âm chặn", "âm" in cau)


@ca("v445 R4: số còn lại đã lưu lệch với tính lại từ dòng thì dừng, không tin bên nào")
def _r4_lech_luu():
	from vagabond import ho_so_tt as hs

	cau = _loi(lambda: hs._so_phai_chuyen(_ho_so(da_tam_ung=0.0, con_lai=90.0), 2))
	dung("nói rõ hai con số", "90" in cau and "100" in cau)


@ca("v445 R4: hồ sơ có tạm ứng (một phần hay đủ) chưa hoàn tất được: thiếu chứng từ bù trừ")
def _r4_hang_rao_tam_ung():
	from vagabond import ho_so_tt as hs

	for tam, con in ((40.0, 60.0), (100.0, 0.0)):
		doc = _ho_so(da_tam_ung=tam, con_lai=con)
		with _San(doc) as san:
			cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
		dung("tạm ứng %s: dừng vì thiếu bù trừ" % tam, "bù trừ" in cau)
		la("tạm ứng %s: không sinh" % tam, san.goi_tao, 0)
		la("tạm ứng %s: không commit" % tam, san.nhat_ky.count("commit"), 0)
		la("tạm ứng %s: giữ Đã duyệt" % tam, doc.trang_thai, "Da duyet")


@ca("v445 R4: SePay so với số THẬT phải chuyển; thiếu tiền thì chặn, đủ thì qua")
def _r4_sepay_theo_con_lai():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	with _San(doc, chi=50.0) as san:
		cau = _loi(lambda: hs.danh_dau_da_tra("APP.26.09.001"))
	dung("chi 50 cho hồ sơ 100 thì chặn", "tiền" in cau)
	la("không sinh khi thiếu tiền", san.goi_tao, 0)


@ca("v445 R4: kiem_sepay: còn phải chuyển 0 là 0, ô trống thì báo chưa tính")
def _r4_kiem_sepay():
	import frappe
	from vagabond import ho_so_tt as hs

	cu = frappe.db.get_value

	def _chay(con_lai, chi):
		frappe.db.get_value = lambda *a, **k: {"name": "APP.26.09.001", "tong_tien": 100.0,
			"con_lai": con_lai, "trang_thai": "Da duyet"}
		try:
			with _Vet(_kiem=lambda *a, **k: None,
					_sepay_theo_ma_app=lambda ds: {"APP.26.09.001": {"chi": chi, "so_gd": 1}}):
				return hs.kiem_sepay("APP.26.09.001")["rows"][0]
		finally:
			frappe.db.get_value = cu

	r = _chay(0.0, 0.0)
	la("phải chuyển 0", r["phai_chuyen"], 0.0)
	la("đủ dù ngân hàng chưa chi gì", r["du"], 1)
	la("có tính", r["chua_tinh"], 0)
	r = _chay(None, 0.0)
	la("ô trống thì chưa tính", r["chua_tinh"], 1)
	la("chưa tính thì không đủ", r["du"], 0)
	r = _chay(60.0, 60.0)
	la("tạm ứng một phần, chi đúng phần còn lại thì đủ", r["du"], 1)


# ================================================ đối chiếu bộ chứng từ, thuần


@ca("v445 bộ chứng từ: hai Payment Entry cho hai nhà cung cấp cộng lại mới đủ")
def _bo_nhieu_pe():
	from vagabond import ho_so_tt as hs

	doc = _ho_so(dong=[_dong("HDM-1", 60.0), _dong("HDM-2", 40.0)])
	kq = hs._kiem_bo_chung_tu(doc, [_pe("PE-1", [("HDM-1", 60.0)])], 2)
	la("một tờ chưa đủ", kq["du"], 0)
	kq = hs._kiem_bo_chung_tu(doc, [_pe("PE-1", [("HDM-1", 60.0)]), _pe("PE-2", [("HDM-2", 40.0)], "NCC-B")], 2)
	la("hai tờ đủ", kq["du"], 1)
	la("tên đủ hai", kq["ten"], ["PE-1", "PE-2"])


@ca("v445 bộ chứng từ: phân bổ tới hoá đơn ngoài hồ sơ là THỪA, không phải đủ")
def _bo_thua():
	from vagabond import ho_so_tt as hs

	doc = _ho_so()
	kq = hs._kiem_bo_chung_tu(doc, [_pe("PE-1", [("HDM-1", 100.0), ("HDM-9", 5.0)])], 2)
	la("không đủ", kq["du"], 0)
	dung("nêu HDM-9 thừa", any("HDM-9" in x for x in kq["thua"]))


@ca("v445 bộ chứng từ: hồ sơ không hoá đơn cần đúng MỘT Journal Entry đúng tổng")
def _bo_je():
	from vagabond import ho_so_tt as hs

	doc = _ho_so(loai="TK cong ty", dong=[{"hoa_don": "", "so_tien": 70.0}], tong_tien=70.0)
	la("chưa có gì thì thiếu", hs._kiem_bo_chung_tu(doc, [], 2)["du"], 0)
	la("một JE đúng tổng thì đủ", hs._kiem_bo_chung_tu(doc, [_je("JE-1", 70.0)], 2)["du"], 1)
	la("JE sai tổng thì lệch", hs._kiem_bo_chung_tu(doc, [_je("JE-1", 60.0)], 2)["du"], 0)
	kq = hs._kiem_bo_chung_tu(doc, [_je("JE-1", 70.0), _je("JE-2", 70.0)], 2)
	la("hai JE là thừa một", kq["du"], 0)
	dung("nêu JE-2 thừa", any("JE-2" in x for x in kq["thua"]))


@ca("v445 bộ chứng từ: rỗng không bao giờ là đủ")
def _bo_rong():
	from vagabond import ho_so_tt as hs

	la("rỗng thì không đủ", hs._kiem_bo_chung_tu(_ho_so(), [], 2)["du"], 0)


# ========================================= controller: mọi đường vào một cửa


@ca("v445 R2 controller: đổi thẳng sang Đã thanh toán mà không mang cờ thì chặn")
def _ctrl_chan():
	from vagabond.vagabond.doctype.vagabond_ho_so_tt import vagabond_ho_so_tt as c

	la("Đã duyệt sang Đã thanh toán, không cờ: chặn", c.doi_sang_da_tra_khong_co("Da duyet", "Da thanh toan", None), True)
	la("có cờ thì cho", c.doi_sang_da_tra_khong_co("Da duyet", "Da thanh toan", True), False)
	la("đã là Đã thanh toán rồi thì lưu lại bình thường", c.doi_sang_da_tra_khong_co("Da thanh toan", "Da thanh toan", None), False)
	la("đổi sang trạng thái khác không dính", c.doi_sang_da_tra_khong_co("Da duyet", "Huy", None), False)
	la("tờ mới tạo thẳng ở Đã thanh toán cũng chặn", c.doi_sang_da_tra_khong_co(None, "Da thanh toan", None), True)


@ca("v445 R2 controller: validate chạy hàng rào này TRƯỚC mọi kiểm khác")
def _ctrl_chay_that():
	import frappe
	from vagabond.vagabond.doctype.vagabond_ho_so_tt import vagabond_ho_so_tt as c

	cu = frappe.db.get_value
	frappe.db.get_value = lambda *a, **k: "Da duyet"
	try:
		ho = c.VagabondHoSoTT.__new__(c.VagabondHoSoTT)
		ho.doctype, ho.name, ho.trang_thai, ho.flags = "Vagabond Ho So TT", "APP.26.09.001", "Da thanh toan", _Co()
		ho.is_new = lambda: False
		ho.dong = []
		cau = _loi(ho.validate)
		dung("chặn đúng câu hoàn tất phải qua ghi nhận", "Ghi nhận đã thanh toán" in cau)
		ho.flags.vgb_bo_chung_tu_da_kiem = True
		cau = _loi(ho.validate)
		dung("mang cờ thì qua hàng rào, rơi xuống kiểm dòng", "ít nhất một dòng" in cau)
	finally:
		frappe.db.get_value = cu
