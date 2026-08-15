"""Bo chay kiem thu, va ban gia lap Frappe toi thieu.

Khong import thu vien ngoai nao (tieu chuan so 9). Ca tep nay chay duoc
bang python3 tran.
"""

import datetime
import sys
import types
import traceback

# Ngay co dinh cho moi ca kiem thu. KHONG dung ngay hom nay: mot bo kiem
# thu ma hom nay xanh mai do la bo kiem thu vo dung.
HOM_NAY = datetime.date(2026, 8, 15)

CA = []          # danh sach (ten, ham)
_LOI = []        # cac cau bao hong cua ca dang chay


def ca(ten):
	"""Ghi danh mot ca kiem thu."""
	def boc(ham):
		CA.append((ten, ham))
		return ham
	return boc


# ---------------------------------------------------------------- so sanh

def la(nhan, duoc, mong):
	"""Hai gia tri phai bang nhau. So thuc so voi sai so rat nho."""
	if isinstance(duoc, float) or isinstance(mong, float):
		ok = abs(float(duoc) - float(mong)) < 0.000001
	else:
		ok = duoc == mong
	if not ok:
		_LOI.append("%s: được %r ¦ mong %r" % (nhan, duoc, mong))


def dung(nhan, dieu):
	la(nhan, bool(dieu), True)


def nem(nhan, ham, loai=Exception):
	"""Goi ham nay PHAI nem loi. Khong nem cung la hong."""
	try:
		ham()
	except loai:
		return
	except Exception as e:
		_LOI.append("%s: nem sai loại lỗi %r" % (nhan, e))
		return
	_LOI.append("%s: không ném lỗi" % nhan)


# ------------------------------------------------------------------ chay

def chay_het(im=0):
	"""Chay moi ca da ghi danh. Tra ve so ca hong."""
	global _LOI
	dat = hong = 0
	for ten, ham in CA:
		_LOI = []
		try:
			ham()
		except Exception:
			_LOI.append("nổ giữa chừng:\n" + traceback.format_exc())
		if _LOI:
			hong += 1
			print("  HỎNG  " + ten)
			for x in _LOI:
				print("         " + x)
		else:
			dat += 1
			if not im:
				print("  đạt   " + ten)
	print("")
	print("%d ca đạt, %d ca hỏng, tổng %d ca." % (dat, hong, dat + hong))
	return hong


# ------------------------------------------------- ban gia lap Frappe
#
# CHI dung cho kiem thu, va chi du de NAP duoc mo dun nghiep vu roi goi
# ham thuan ben trong. Khong phai ban mo phong Frappe.
#
# Neu mai nay them mot ham frappe moi vao mo dun nghiep vu thi bo kiem thu
# se no ngay o day. Do la co y: no nhac rang vua them mot chho phu thuoc
# vao Frappe, va phai can nhac xem cho do co dang thuan hay khong.

BANG_GIA = {}    # doctype -> danh sach dong ma frappe.get_all se tra ve


class Doi(dict):
	"""Dictionary truy cap duoc bang dau cham, giong frappe._dict."""

	def __getattr__(self, k):
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)


def _getdate(v=None):
	if v is None or v == "":
		return HOM_NAY
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	return datetime.date(*[int(x) for x in str(v)[:10].split("-")])


def _flt(v, p=None):
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0


def _cint(v):
	try:
		return int(float(v or 0))
	except (TypeError, ValueError):
		return 0


def gia_lap():
	"""Cai ban Frappe gia vao sys.modules. Goi TRUOC khi nap mo dun nghiep vu."""
	if "frappe" in sys.modules:
		return sys.modules["frappe"]

	fr = types.ModuleType("frappe")
	fr.get_roles = lambda *a, **k: ["System Manager"]

	def _throw(msg, *a, **k):
		raise Exception(msg)

	fr.throw = _throw
	fr.whitelist = lambda *a, **k: (lambda f: f)
	fr._dict = Doi
	fr.log_error = lambda *a, **k: None
	fr.get_traceback = lambda *a, **k: ""
	fr.local = types.SimpleNamespace(form_dict={}, lang="vi")
	fr.session = types.SimpleNamespace(user="kiemthu@vagabond")
	fr.get_all = lambda dt, **k: [Doi(r) for r in BANG_GIA.get(dt, [])]
	fr.get_list = fr.get_all
	fr.get_doc = lambda *a, **k: Doi()
	fr.get_cached_doc = lambda *a, **k: Doi()
	fr.get_module = lambda ten: __import__(ten, fromlist=["x"])
	fr.qb = types.SimpleNamespace()
	fr.db = types.SimpleNamespace(
		get_value=lambda *a, **k: None,
		exists=lambda *a, **k: None,
		sql=lambda *a, **k: [],
		get_all=fr.get_all,
		set_value=lambda *a, **k: None,
		commit=lambda *a, **k: None,
	)
	fr.cache = lambda *a, **k: types.SimpleNamespace(
		get_value=lambda *a, **k: None, set_value=lambda *a, **k: None
	)

	ut = types.ModuleType("frappe.utils")
	ut.add_days = lambda d, n: _getdate(d) + datetime.timedelta(days=n)
	ut.add_months = lambda d, n: _getdate(d)
	ut.cint, ut.flt, ut.getdate = _cint, _flt, _getdate
	ut.nowdate = lambda: str(HOM_NAY)
	ut.today = ut.nowdate
	ut.nowtime = lambda: "09:00:00"
	ut.now_datetime = lambda: datetime.datetime(2026, 8, 15, 9, 0, 0)
	ut.get_datetime = lambda v=None: datetime.datetime(2026, 8, 15, 9, 0, 0)
	ut.cstr = lambda v: "" if v is None else str(v)
	ut.fmt_money = lambda v, **k: str(v)
	ut.date_diff = lambda a, b: (_getdate(a) - _getdate(b)).days
	fr.utils = ut

	xl = types.ModuleType("frappe.utils.xlsxutils")
	xl.make_xlsx = lambda *a, **k: None

	md = types.ModuleType("frappe.model")
	dc = types.ModuleType("frappe.model.document")
	dc.Document = object

	sys.modules["frappe"] = fr
	sys.modules["frappe.utils"] = ut
	sys.modules["frappe.utils.xlsxutils"] = xl
	sys.modules["frappe.model"] = md
	sys.modules["frappe.model.document"] = dc
	return fr


# ------------------------------------------------------------ du lieu gia

def don_mua(n, **doi):
	"""Mot don mua hang gia. Truyen them tham so de doi tung o."""
	d = {
		"name": "DMH-2026-%05d" % n,
		"supplier": "NCC%03d" % (n % 7),
		"supplier_name": ["Hùng Phát", "Anh Đào", "Kho Lạnh Sài Gòn"][n % 3],
		"transaction_date": datetime.date(2026, 8, 1),
		"schedule_date": datetime.date(2026, 8, 20),
		"grand_total": 100000.0,
		"total_qty": 10,
		"status": "To Receive and Bill",
		"per_received": 0,
		"per_billed": 0,
		"docstatus": 1,
		"owner": "uyen@vagabond",
		"vgb_huy": 0,
	}
	d.update(doi)
	return d


def hoa_don_mua(n, **doi):
	"""Mot to hoa don mua vao gia."""
	d = {
		"name": "HDM-2026-%05d" % n,
		"posting_date": datetime.date(2026, 8, 1),
		"due_date": datetime.date(2026, 8, 20),
		"supplier": "NCC%03d" % (n % 7),
		"supplier_name": ["Hùng Phát", "Anh Đào", "Kho Lạnh Sài Gòn"][n % 3],
		"bill_no": "SO%04d" % n,
		"grand_total": 100000.0,
		"outstanding_amount": 100000.0,
		"total_qty": 5,
		"docstatus": 1,
		"vgb_huy": 0,
		"amended_from": "",
	}
	d.update(doi)
	return d
