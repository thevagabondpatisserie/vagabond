# -*- coding: utf-8 -*-
"""v631, Codex rà PR #531 trên 88a247a: bốn finding, anh Việt giao Claude sửa (02/11/2026).

1. Hai lượt hỏi trạng thái (hoặc lượt hỏi và nhịp 5 phút) cùng khớp một đơn:
   lượt sau chờ khoá phiếu đặt xong vẫn đọc phiếu thu và chủ dòng sao kê bằng
   ẢNH CHỤP REPEATABLE READ có từ trước lúc chờ, nên lập phiếu thu thứ hai cho
   CÙNG một dòng sao kê. Cọc 50% thành "đã thu đủ".
2. Hai lần gửi cùng mã lần gửi: lần sau chờ khoá xong vẫn tra mã lần gửi bằng
   phép đọc thường, nên lập phiếu đặt thứ hai.
3. Đính PDF giấy báo Có ở màn Đơn đặt trước và Đơn sỉ web: tệp PDF bị bỏ lặng
   lẽ, phiếu thu bị hook đính kèm chặn ghi sổ, bánh không giao được.
4. Khách sỉ trả trước tải lại trang hoặc sang Tài khoản trước khi chuyển tiền
   thì không mở lại được QR của đơn (QR chỉ nằm trong bộ nhớ trang).

Ca 1 và 2 chạy phép THẬT (trang_thai_don, khop, dat) trên một MariaDB giả có
HAI KẾT NỐI chạy hai luồng thật: đọc thường thấy ảnh chụp lấy ở lần đọc thường
đầu tiên của giao dịch, đọc `for update` thấy bản đã commit và giữ khoá dòng
tới hết yêu cầu, kết nối khác xin cùng khoá thì CHỜ thật. Thứ tự đan xen do ca
kiểm đặt bằng điểm dừng, không gọi thêm hàm nào "cho chắc".
"""

import base64
import contextlib
import copy
import json
import re
import sys
import threading
import types
from pathlib import Path
from unittest import mock

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)
if not hasattr(_fr, "UniqueValidationError"):
	class UniqueValidationError(_fr.ValidationError):
		pass

	_fr.UniqueValidationError = UniqueValidationError

from vagabond import banh_si as bs  # noqa: E402
from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import thiet_ke_rieng as tkr  # noqa: E402
from vagabond import ung_truoc_don as utd  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
KHOA_XEM = "abcdefghijklmnopqrstuvwx"
CHO = 10.0


# ================================================== MariaDB giả hai kết nối

class _KetNoi(object):
	def __init__(self, ten, dung_tai=()):
		self.ten = ten
		self.anh = None          # ảnh chụp REPEATABLE READ, lấy ở lần đọc thường đầu
		self.cho = []            # dòng chính kết nối này đã ghi, chưa commit
		self.moc = {}            # savepoint -> số dòng đã ghi lúc đặt
		self.dung = {d: threading.Event() for d in dung_tai}
		self.dang_dung = ""
		self.dang_cho = None     # khoá đang chờ
		self.xong = False
		self.kq = None
		self.loi = None


class _MayChu(object):
	"""Cơ sở dữ liệu giả. Phiếu đặt (so), sao kê (bt), phiếu thu (pe) đã commit
	nằm ở đây; mỗi yêu cầu web là một luồng có kết nối riêng."""

	def __init__(self, so=None, bt=None, ndw=None):
		self.so = {r["name"]: dict(r) for r in (so or [])}
		self.bt = [dict(g) for g in (bt or [])]
		self.pe = []
		self.ndw = ndw
		self.so_moi = []
		self.thu_ghi_so = 0
		self.si = []   # hoá đơn đã commit (vòng 6)
		self.dn = []   # phiếu giao đã commit (vòng 6)
		self.dem_pe = 0
		self.dem_so = 0
		self.cv = threading.Condition()
		self.khoa = {}
		self.tl = threading.local()
		self.nhat_ky = []
		self.tin = []

	# ---------- kết nối, ảnh chụp, khoá
	def kn(self):
		return self.tl.kn

	def _anh(self):
		kn = self.kn()
		if kn.anh is None:
			with self.cv:
				kn.anh = {"pe": copy.deepcopy(self.pe), "bt": copy.deepcopy(self.bt), "so": copy.deepcopy(self.so_moi),
					"sodon": copy.deepcopy(self.so), "si": copy.deepcopy(self.si), "dn": copy.deepcopy(self.dn)}
		return kn.anh

	def _bang_xem(self, bang, hien_tai):
		if hien_tai:
			with self.cv:
				goc = copy.deepcopy(getattr(self, bang))
		else:
			goc = copy.deepcopy(self._anh().get(bang, []))
		return goc + [r for r in self.kn().cho if r["_bang"] == bang]

	def _so_xem(self, hien_tai):
		"""Phiếu đặt có sẵn (vòng 6: huỷ được): đọc thường thấy ảnh chụp, đọc có
		khoá thấy bản đã commit, cộng phần chính kết nối này vừa đổi."""
		if hien_tai:
			with self.cv:
				d = copy.deepcopy(self.so)
		else:
			d = copy.deepcopy(self._anh().get("sodon", self.so))
		for r in self.kn().cho:
			if r["_bang"] == "so_doi" and r["name"] in d:
				d[r["name"]].update(r["doi"])
		return d

	def _dung(self, diem):
		kn = self.kn()
		ev = kn.dung.get(diem)
		if ev is None or ev.is_set():
			return
		with self.cv:
			kn.dang_dung = diem
			self.cv.notify_all()
		if not ev.wait(CHO):
			raise AssertionError("kết nối %s dừng ở %s quá lâu" % (kn.ten, diem))
		with self.cv:
			kn.dang_dung = ""

	def _khoa(self, k):
		kn = self.kn()
		self._dung("truoc_khoa:" + k[0])
		with self.cv:
			het = threading.Event()
			while self.khoa.get(k) not in (None, kn):
				kn.dang_cho = k
				self.cv.notify_all()
				if not self.cv.wait(CHO):
					het.set()
					break
			kn.dang_cho = None
			if het.is_set():
				raise AssertionError("kết nối %s chờ khoá %s quá lâu" % (kn.ten, k))
			self.khoa[k] = kn

	def commit(self, *a, **k):
		kn = self.kn()
		with self.cv:
			for r in kn.cho:
				if r["_bang"] == "so_doi":
					self.so[r["name"]].update(r["doi"])
					continue
				if r["_bang"] in ("si", "dn"):
					getattr(self, r["_bang"]).append(r)
					continue
				(self.pe if r["_bang"] == "pe" else self.so_moi).append(r)
			kn.cho, kn.moc, kn.anh = [], {}, None
			for k2 in [x for x, v in self.khoa.items() if v is kn]:
				del self.khoa[k2]
			self.cv.notify_all()

	def rollback(self, save_point=None, **k):
		kn = self.kn()
		if save_point:
			del kn.cho[kn.moc.get(save_point, len(kn.cho)):]
			return
		with self.cv:
			kn.cho, kn.moc, kn.anh = [], {}, None
			for k2 in [x for x, v in self.khoa.items() if v is kn]:
				del self.khoa[k2]
			self.cv.notify_all()

	def savepoint(self, ten):
		self.kn().moc[ten] = len(self.kn().cho)

	# ---------- các bảng nhìn theo hai kiểu đọc
	def _pe(self, hien_tai):
		kn = self.kn()
		if hien_tai:
			with self.cv:
				goc = copy.deepcopy(self.pe)
		else:
			goc = self._anh()["pe"]
		return goc + [r for r in kn.cho if r["_bang"] == "pe"]

	def _so_moi(self, hien_tai):
		kn = self.kn()
		if hien_tai:
			with self.cv:
				goc = copy.deepcopy(self.so_moi)
		else:
			goc = self._anh()["so"]
		return goc + [r for r in kn.cho if r["_bang"] == "so"]

	# ---------- frappe.db.sql
	def sql(self, q, a=None, as_dict=False, **k):
		khoa = "for update" in q.lower()
		if "`tabVagabond Noi Dung Web`" in q:
			if self.ndw is None:
				return []
			if khoa:
				self._khoa(("NDW", "1"))
			return [(json.dumps(self.ndw, ensure_ascii=False),)]
		if "`tabCustomer`" in q:
			if khoa:
				self._khoa(("KH", a[0]))
			return [(a[0],)]
		if "`tabSales Order Item`" in q:
			ds = [r for r in self._so_moi(khoa) if r["name"] == (a[0] if not isinstance(a, dict) else a.get("so"))]
			return [_fr._dict(d) for r in ds for d in r.get("items", [])]
		if "from `tabSales Order`" in q:
			if khoa:
				self._khoa(("SO", a[0]))
			r = self._so_xem(khoa).get(a[0])
			return [_fr._dict(r)] if r else []
		if "`tabBank Transaction`" in q:
			if khoa:
				ds = a.get("ds") if isinstance(a, dict) else (a[0],)
				for ten in sorted(ds):
					self._khoa(("BT", ten))
				if as_dict:
					# Đọc HIỆN TẠI trong khoá: bản mới nhất, không phải ảnh chụp.
					with self.cv:
						hien = copy.deepcopy(self.bt)
					return [_fr._dict(g) for g in sorted(hien, key=lambda x: x["name"]) if g["name"] in ds]
				return [(t,) for t in sorted(ds)]
			m = a["m"].strip("%")
			ql = " ".join(q.lower().split())
			return [_fr._dict(g) for g in self._anh()["bt"]
				if m in ("%s %s" % (g.get("description") or "", g.get("reference_number") or "")).upper()
				# Điều kiện SQL có trong câu thì làm như cơ sở dữ liệu thật làm.
				and ("docstatus = 1" not in ql or int(g.get("docstatus", 1)) == 1)
				and ("deposit > 0" not in ql or float(g.get("deposit") or 0) > 0)]
		if "`tabDelivery Note`" in q:
			return [(r["name"],) for r in self._bang_xem("dn", khoa) if r["against_sales_order"] == a[0] and r["docstatus"] == 1]
		if "`tabPayment Entry`" in q:
			ds = self._pe(khoa)
			ds = [p for p in ds if int(p["docstatus"]) < 2]
			if isinstance(a, dict) and "ds" in a:
				ds = [p for p in ds if p.get("vgb_gd_tkr") in a["ds"]]
			if isinstance(a, dict) and "so" in a:
				ds = [p for p in ds if p.get("vgb_phieu_dat") == a["so"]]
			if isinstance(a, dict) and a.get("tru"):
				ds = [p for p in ds if p["name"] != a["tru"]]
			return [_fr._dict(p) for p in ds] if as_dict else [(p["name"], p.get("vgb_gd_tkr")) for p in ds]
		return []

	# ---------- frappe.get_all / frappe.db.get_value
	def get_all(self, dt, filters=None, fields=None, **k):
		if dt == "Payment Entry":
			f = filters or {}
			return [_fr._dict(p) for p in self._pe(False)
				if p.get("vgb_phieu_dat") == f.get("vgb_phieu_dat") and int(p["docstatus"]) < 2]
		if dt == "Sales Order Item":
			ten = (filters or {}).get("parent")
			return [_fr._dict(d) for r in self._so_moi(False) if r["name"] == ten for d in r.get("items", [])]
		self._anh()
		return []

	def get_value(self, dt, f=None, fields=None, as_dict=False, for_update=False, **k):
		if dt == "Bank Account":
			return "1121 - MB"
		if dt == "Sales Invoice" and isinstance(f, dict):
			ds = [r for r in self._bang_xem("si", for_update) if r["custom_pancake_id"] == f.get("custom_pancake_id")
				and r["docstatus"] < 2]
			if not ds:
				return None
			return _fr._dict({x: ds[0].get(x) for x in fields}) if isinstance(fields, (list, tuple)) else ds[0].get(fields)
		if dt != "Sales Order":
			return None
		if isinstance(f, dict) and ("vgb_tkr_lan" in f or "vgb_si_lan" in f):
			o = "vgb_tkr_lan" if "vgb_tkr_lan" in f else "vgb_si_lan"
			ds = [r for r in self._so_moi(for_update) if r.get(o) == f[o]]
			return _fr._dict(ds[0]) if ds else None
		self._anh()
		if isinstance(f, dict):
			for r in self.so.values():
				if all(r.get(x) == y for x, y in f.items()):
					return r["name"]
			return None
		if f not in self.so:
			# Phiếu đặt mới lập trong lúc chạy: đọc thường thấy ảnh chụp, đọc có
			# khoá thấy bản đã commit. Không thấy thì trả None như Frappe thật.
			ds = [r for r in self._so_moi(for_update) if r["name"] == f]
			if not ds:
				return None
			r = ds[0]
			if isinstance(fields, (list, tuple)):
				return _fr._dict({x: r.get(x) for x in fields})
			return r.get(fields)
		r = self._so_xem(for_update).get(f) or {}
		if isinstance(fields, (list, tuple)):
			return _fr._dict({x: r.get(x) for x in fields})
		if fields in ("vgb_tkr_du_lieu", "vgb_si_du_lieu"):
			return "{}"
		return r.get(fields)

	# ---------- frappe.get_doc(dict) cho phiếu thu
	def get_doc(self, d, *a, **k):
		may = self
		if d == "Sales Order":
			ten = a[0] if a else k.get("name")

			class DonDat(_fr._dict):
				def add_comment(self, *a2, **k2):
					pass

				def cancel(self):
					may.kn().cho.append({"_bang": "so_doi", "name": ten, "doi": {"docstatus": 2, "status": "Cancelled"}})
			o = DonDat(may._so_xem(bool(k.get("for_update"))).get(ten) or {})
			o.flags = _fr._dict()
			return o

		class Doc(_fr._dict):
			def setup_party_account_field(self):
				pass

			def set_missing_values(self):
				pass

			def insert(self, **k2):
				may._dung("truoc_insert")
				with may.cv:
					may.dem_pe += 1
					self.name = "PE-%d" % may.dem_pe
				may.kn().cho.append({"_bang": "pe", "name": self.name, "docstatus": 0, "payment_type": "Receive",
					"paid_amount": self.paid_amount, "received_amount": self.received_amount,
					"vgb_gd_tkr": self.vgb_gd_tkr, "vgb_phieu_dat": self.vgb_phieu_dat,
					"mode_of_payment": self.mode_of_payment, "vgb_quay": self.vgb_quay,
					"posting_date": self.posting_date, "creation": "2026-11-03 10:00:%02d" % may.dem_pe})

			def submit(self):
				for r in may.kn().cho:
					if r.get("name") == self.name:
						r["docstatus"] = 1
				self.docstatus = 1
		doc = Doc(d)
		doc.flags = _fr._dict()
		return doc

	# ---------- phiếu đặt mới (ô mã lần gửi), giữ ràng buộc DUY NHẤT nếu ô khai unique
	def lap_so(self, o, lan, ma, truong_moi, them=None):
		self._dung("truoc_insert")
		with self.cv:
			self.thu_ghi_so += 1
		unique = any(x.get("unique") for x in truong_moi if x["fieldname"] == o)
		if unique and any(r.get(o) == lan for r in self._so_moi(True)):
			raise _fr.UniqueValidationError("Sales Order", "", "Duplicate entry for key %s" % o)
		with self.cv:
			self.dem_so += 1
			ten = "SO-%d" % (100 + self.dem_so)
		self.kn().cho.append(dict(them or {}, _bang="so", name=ten, ma=ma, **{o: lan}))
		return _fr._dict(name=ten, vgb_tkr_ma=ma, vgb_si_ma=ma, vgb_si_tt=(them or {}).get("vgb_si_tt", "Công nợ"))

	# ---------- chạy một yêu cầu web trên luồng riêng
	def chay(self, ten, ham, dung_tai=()):
		kn = _KetNoi(ten, dung_tai)

		def than():
			self.tl.kn = kn
			try:
				kn.kq = ham()
				self.commit()
			except BaseException as e:  # noqa: B902 - ghi lại để ca kiểm đọc
				kn.loi = e
				self.rollback()
			finally:
				with self.cv:
					kn.xong = True
					self.cv.notify_all()
		threading.Thread(target=than, daemon=True).start()
		return kn

	def cho_toi(self, dk, ten):
		with self.cv:
			if not self.cv.wait_for(dk, CHO):
				raise AssertionError("treo: " + ten)

	def tha(self, kn, diem):
		kn.dung[diem].set()

	def doc_lai(self, ham):
		"""Một yêu cầu thứ ba, chạy sau cùng: đọc trạng thái như khách thấy."""
		kn = self.chay("doc", ham)
		self.cho_toi(lambda: kn.xong, "đọc lại")
		if kn.loi:
			raise kn.loi
		return kn.kq


def _vao(may, them=()):
	"""Gắn Frappe giả vào MariaDB giả. Chỉ thay phần chạm hệ và tin Zalo, giữ
	nguyên trang_thai_don, khop_mot, khop_don, ung_truoc_don.khop, tom_tat."""
	from vagabond import doi_soat_sepay as dss
	from vagabond import thu_tien

	def chu_anh_chup(ds, **k):
		# chu_cua_giao_dich thật đọc bằng frappe.get_all: đọc thường, ảnh chụp.
		return {p["vgb_gd_tkr"]: "phiếu thu " + p["name"] for p in may._pe(False)
			if p.get("vgb_gd_tkr") in ds and int(p["docstatus"]) < 2}
	diem = [{"ma": "SALES", "quay": "", "bat": 1, "ten": "Sales Online"}, {"ma": "TCV", "quay": "TCV", "bat": 1, "ten": "TCV"}]
	ps = [mock.patch.object(_fr.db, "sql", may.sql), mock.patch.object(_fr, "get_all", may.get_all),
		mock.patch.object(_fr.db, "get_value", may.get_value), mock.patch.object(_fr, "get_doc", may.get_doc),
		mock.patch.object(_fr.db, "exists", lambda *a, **k: True),
		mock.patch.object(_fr.db, "commit", may.commit), mock.patch.object(_fr.db, "rollback", may.rollback),
		mock.patch.object(_fr.db, "savepoint", may.savepoint),
		mock.patch.object(_fr, "log_error", lambda *a, **k: may.nhat_ky.append(a[-1] if a else k.get("title"))),
		mock.patch.object(dss, "chu_cua_giao_dich", chu_anh_chup),
		mock.patch.object(dss, "tai_khoan_duoc_khop", lambda: {"BA-MB"}),
		mock.patch.object(thu_tien, "nang_quyen_lap_phieu", contextlib.nullcontext),
		mock.patch.object(tkr, "_ds_diem", lambda: diem), mock.patch.object(tkr, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(tkr, "_bao_sales_coc", lambda *a, **k: may.tin.append("tkr_sales")),
		mock.patch.object(tkr, "_bao_bep_coc", lambda *a, **k: may.tin.append("tkr_bep")),
		mock.patch.object(bs, "_ds_diem", lambda: diem), mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(bs, "_bao_da_tt", lambda *a, **k: may.tin.append("bsi_da_tt")),
		mock.patch.object(bs, "_khach_phien", lambda: (may.get_all("Customer") or 1) and (_fr._dict(name="SI00012",
			customer_name="Café Lá Me", vgb_si_cuoi_ky=0), ""))]
	ps += list(them)
	return ps


@contextlib.contextmanager
def _gan(ps):
	for p in ps:
		p.start()
	try:
		yield
	finally:
		for p in reversed(ps):
			p.stop()


SO_TKR = {"name": "SO-1", "docstatus": 1, "status": "To Deliver and Bill", "vgb_tkr_ma": "TKR26110001",
	"vgb_tkr_khoa": KHOA_XEM, "vgb_tkr_coc": 3780000, "customer": "KH-1", "customer_name": "Nguyễn An",
	"grand_total": 7560000, "rounded_total": 7560000, "per_billed": 0, "delivery_date": "2026-11-14",
	"vgb_tkr_du_lieu": "{}", "vgb_tkr_bang_ke": ""}
SO_BSI = {"name": "SO-2", "docstatus": 1, "status": "To Deliver and Bill", "vgb_si_ma": "BSI26110002",
	"vgb_tkr_coc": 0, "customer": "SI00012", "customer_name": "Café Lá Me", "grand_total": 3780000,
	"rounded_total": 3780000, "per_billed": 0, "vgb_si_tt": "Trả trước", "net_total": 3500000,
	"total_taxes_and_charges": 280000, "delivery_date": "2026-11-05", "vgb_si_du_lieu": "{}"}


def _bt(ten, tien, mo):
	return {"name": ten, "date": "2026-11-03", "deposit": tien, "withdrawal": 0, "description": mo,
		"reference_number": "FT" + ten, "bank_account": "BA-MB", "transaction_id": ten, "docstatus": 1}


def _hoi_tkr():
	return tkr.trang_thai_don("TKR26110001", KHOA_XEM)


def _hoi_bsi():
	return bs.trang_thai_don("BSI26110002")


def _phieu_cua(may, so):
	return sorted((p["vgb_gd_tkr"], p["paid_amount"]) for p in may.pe if p["vgb_phieu_dat"] == so and p["docstatus"] < 2)


def _khong_loi(may, *kns):
	for kn in kns:
		if kn.loi:
			raise kn.loi
	la("không lượt khớp nào nuốt lỗi", [x for x in may.nhat_ky if "khớp" in str(x)], [])


def _hai_luot_cung_don(may, hoi, khoi_dong_a_truoc=None):
	"""Lượt B đọc thường trước (ảnh chụp), rồi chờ khoá phiếu đặt đang ở lượt A;
	A khớp xong, commit; B được khoá và khớp tiếp. Đúng chuỗi của hai lần hỏi
	trạng thái cách nhau vài trăm mili giây."""
	b = may.chay("B", hoi, ("truoc_khoa:SO",))
	may.cho_toi(lambda: b.dang_dung == "truoc_khoa:SO", "B tới khoá phiếu đặt")
	a = may.chay("A", hoi)
	may.cho_toi(lambda: a.xong, "A xong")
	may.tha(b, "truoc_khoa:SO")
	may.cho_toi(lambda: b.xong, "B xong")
	_khong_loi(may, a, b)
	return a, b


# ================================================== finding 1: phiếu thu đôi

@ca("Codex #531 f1: hai lượt khách hỏi trạng thái cùng một đơn thiết kế riêng, MỘT dòng sao kê cọc chỉ ra MỘT phiếu thu; đơn vẫn 'đã cọc', không thành 'đủ tiền'")
def _f1_hai_luot_hoi():
	may = _MayChu(so=[SO_TKR], bt=[_bt("BT-7", 3780000, "MBVCB TKR26110001 coc")])
	with _gan(_vao(may)):
		_hai_luot_cung_don(may, _hoi_tkr)
		la("phiếu thu của đơn", _phieu_cua(may, "SO-1"), [("BT-7", 3780000.0)])
		la("báo Sales và bếp đúng một lần", may.tin, ["tkr_sales", "tkr_bep"])
		la("khách thấy", may.doc_lai(_hoi_tkr)["trang_thai"], "da_coc")


@ca("Codex #531 f1: đã cọc rồi khách chuyển thêm CẢ đơn; lượt chờ khoá phải đọc phiếu thu hiện tại, không lập phiếu vượt tổng đơn")
def _f1_doc_phieu_hien_tai():
	may = _MayChu(so=[SO_TKR], bt=[_bt("BT-7", 3780000, "TKR26110001 coc"), _bt("BT-8", 7560000, "TKR26110001 tra du")])
	with _gan(_vao(may)):
		_hai_luot_cung_don(may, _hoi_tkr)
		la("phiếu thu của đơn", _phieu_cua(may, "SO-1"), [("BT-7", 3780000.0)])
		la("tổng phiếu không vượt tổng đơn", sum(x[1] for x in _phieu_cua(may, "SO-1")) <= 7560000, True)


@ca("Codex #531 f1: dòng sao kê mới chỉ lượt sau thấy; lượt sau bỏ dòng lượt trước đã chiếm (đọc chủ hiện tại) và vẫn nhận dòng mới")
def _f1_doc_chu_hien_tai():
	may = _MayChu(so=[SO_TKR], bt=[_bt("BT-7", 3780000, "TKR26110001 coc")])
	with _gan(_vao(may)):
		a = may.chay("A", _hoi_tkr, ("truoc_khoa:SO",))
		may.cho_toi(lambda: a.dang_dung == "truoc_khoa:SO", "A chụp ảnh")
		with may.cv:
			may.bt.append(_bt("BT-8", 3780000, "TKR26110001 phan con lai"))
		b = may.chay("B", _hoi_tkr, ("truoc_khoa:SO",))
		may.cho_toi(lambda: b.dang_dung == "truoc_khoa:SO", "B chụp ảnh")
		may.tha(a, "truoc_khoa:SO")
		may.cho_toi(lambda: a.xong, "A xong")
		may.tha(b, "truoc_khoa:SO")
		may.cho_toi(lambda: b.xong, "B xong")
		_khong_loi(may, a, b)
		la("mỗi dòng sao kê một phiếu", _phieu_cua(may, "SO-1"), [("BT-7", 3780000.0), ("BT-8", 3780000.0)])
		la("khách thấy đủ tiền", may.doc_lai(_hoi_tkr)["trang_thai"], "du_tien")


@ca("Codex #531 f1: một dòng sao kê mang mã của HAI đơn (thiết kế riêng và sỉ) khớp cùng lúc: khoá dòng sao kê, chỉ một phiếu thu chiếm dòng")
def _f1_khoa_dong_sao_ke():
	may = _MayChu(so=[SO_TKR, SO_BSI], bt=[_bt("BT-5", 3780000, "TKR26110001 BSI26110002")])
	with _gan(_vao(may)):
		b = may.chay("B", _hoi_bsi, ("truoc_insert",))
		may.cho_toi(lambda: b.dang_dung == "truoc_insert", "B sắp ghi phiếu")
		a = may.chay("A", _hoi_tkr)
		may.cho_toi(lambda: a.xong or a.dang_cho is not None, "A xong hoặc đang chờ khoá")
		may.tha(b, "truoc_insert")
		may.cho_toi(lambda: a.xong and b.xong, "hai lượt xong")
		_khong_loi(may, a, b)
		la("số phiếu chiếm BT-5", len([p for p in may.pe if p["vgb_gd_tkr"] == "BT-5"]), 1)


# ================================================== finding 2: phiếu đặt đôi

TP = nw.chuan_tkr(nw.TKR_MAU)
DIEM = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]
MA_LAN = "123e4567-e89b-42d3-a456-426614174000"


def _don_tkr():
	return json.dumps({"tac_pham": TP["id"], "kich_co": "M", "trang_tri": ["Hoa lan trắng"], "ngay": "2026-11-14",
		"gio": "17:00", "ten": "Nguyễn An", "sdt": "0909 123 456", "ghi_chu": "", "diem_nhan": "tcv"}, ensure_ascii=False)


def _vao_dat(may):
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(dict(TP))
	if may.ndw is not None:
		may.ndw = nd
	so_ma = {}

	def lap_tkr(don, lan):
		ma = "TKR2611%04d" % (len(so_ma) + 1)
		so = may.lap_so("vgb_tkr_lan", lan, ma, tkr.TRUONG_MOI["Sales Order"],
			{"vgb_tkr_du_lieu": json.dumps({"bam": don["bam"]}), "vgb_tkr_ma": ma, "vgb_tkr_khoa": KHOA_XEM,
				"vgb_tkr_coc": don["coc"], "grand_total": don["tong"], "rounded_total": don["tong"],
				"delivery_date": don["ngay"], "docstatus": 1})
		so_ma[so.name] = so.vgb_tkr_ma
		return so

	def lap_bsi(kh, don, lan):
		ma = "BSI2611%04d" % (len(so_ma) + 1)
		so = may.lap_so("vgb_si_lan", lan, ma, bs.TRUONG_MOI["Sales Order"],
			{"customer": kh.name, "customer_name": kh.customer_name, "vgb_si_du_lieu": json.dumps({"bam": don["bam"]}),
				"vgb_si_ma": ma, "vgb_si_tt": "Trả trước", "docstatus": 1, "delivery_date": don["ngay"],
				"grand_total": don["tong"], "rounded_total": don["tong"], "net_total": 777778, "total_taxes_and_charges": 62222,
				"items": [{"item_code": d["ma"], "item_name": "Croissant bơ", "qty": d["sl"], "rate": d["gia"],
					"amount": d["sl"] * d["gia"], "idx": i + 1} for i, d in enumerate(don["dong"])]})
		so_ma[so.name] = so.vgb_si_ma
		return so

	# Codex #531 vòng 3: bản trước thay `_ket_qua` bằng hàm giả trả mã từ bộ nhớ
	# ca kiểm, nên che mất lỗi lượt sau dựng phản hồi bằng phép đọc thường
	# (không thấy phiếu đặt vừa commit, nổ AttributeError). Nay giữ `_ket_qua`,
	# `tom_tat` THẬT; chỉ thay phần dựng ảnh QR (cấu hình tài khoản ngân hàng).
	def qr(ma, so):
		return {"noi_dung": ma, "so_tien": so, "anh": "data:x"}
	them = [mock.patch("vagabond.noi_dung_web._ban_cong_khai", nw._ban_cong_khai if may.ndw is not None else
		(lambda khoa=False: copy.deepcopy(nd))),
		mock.patch.object(tkr, "_diem_nhan", lambda ban: DIEM), mock.patch.object(tkr, "_hom_nay", lambda: "2026-11-02"),
		mock.patch.object(tkr, "_lap_phieu_dat", lap_tkr), mock.patch.object(tkr, "_bao_moi", lambda *a, **k: None),
		mock.patch.object(tkr, "_qr", qr),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02"),
		mock.patch.object(bs, "gia_cua_khach", lambda k, n=None: {"BANU00001": {"ten": "Croissant bơ", "gia": 28000,
			"anh": "", "dvt": "Cái", "nhom": "Bánh mì"}}),
		mock.patch.object(bs, "_lap_don", lap_bsi), mock.patch.object(bs, "_bao_don_moi", lambda *a, **k: None),
		mock.patch.object(bs, "_qr", qr),
		mock.patch.object(_fr, "generate_hash", lambda *a, **k: "moc", create=True)]
	return _vao(may, them)


def _gui_dong_thoi(may, gui, diem):
	b = may.chay("B", gui, (diem,))
	may.cho_toi(lambda: b.dang_dung == diem, "B tới " + diem)
	a = may.chay("A", gui)
	may.cho_toi(lambda: a.xong, "A xong")
	may.tha(b, diem)
	may.cho_toi(lambda: b.xong, "B xong")
	return a, b


@ca("Codex #531 f2: bấm gửi đơn thiết kế riêng hai lần cùng mã lần gửi, lần sau chờ khoá nội dung web xong phải tra lại mã bằng phép đọc hiện tại: MỘT phiếu đặt")
def _f2_tkr_khoa():
	may = _MayChu(ndw={})
	with _gan(_vao_dat(may)):
		a, b = _gui_dong_thoi(may, lambda: tkr.dat(_don_tkr(), MA_LAN), "truoc_khoa:NDW")
		_khong_loi(may, a, b)
		la("số phiếu đặt mang mã lần gửi", len(may.so_moi), 1)
		# Lần sau trả đơn cũ ngay ở phép tra có khoá, không đi tới bước ghi rồi
		# mới nhờ ràng buộc duy nhất (lớp phòng hờ, kiểm ở ca dưới).
		la("số lần thử ghi phiếu đặt", may.thu_ghi_so, 1)
		la("lần sau trả đúng đơn lần trước", b.kq["ma"], a.kq["ma"])
		la("lần sau vẫn có QR cọc", (b.kq["qr"]["noi_dung"], b.kq["qr"]["so_tien"], b.kq["coc"]), (a.kq["ma"], 3780000.0, 3780000.0))


@ca("Codex #531 f2: chưa có hàng nội dung web để khoá, hai lần gửi cùng mã lọt tới bước ghi: ràng buộc duy nhất của ô mã lần gửi chặn, lần sau trả đơn lần trước")
def _f2_tkr_duy_nhat():
	may = _MayChu(ndw=None)
	with _gan(_vao_dat(may)):
		a, b = _gui_dong_thoi(may, lambda: tkr.dat(_don_tkr(), MA_LAN), "truoc_insert")
		_khong_loi(may, a, b)
		la("số phiếu đặt mang mã lần gửi", len(may.so_moi), 1)
		la("lần sau trả đúng đơn lần trước", b.kq["ma"], a.kq["ma"])
		la("lần sau vẫn có QR cọc", b.kq["qr"]["so_tien"], 3780000.0)


@ca("Codex #531 f2: đơn sỉ bấm gửi hai lần cùng mã lần gửi, lần sau chờ khoá khách xong phải tra lại mã bằng phép đọc hiện tại: MỘT phiếu đặt")
def _f2_bsi_khoa():
	may = _MayChu()
	don = json.dumps({"ngay": "2026-11-05", "ghi_chu": "", "dong": [{"ma": "BANU00001", "sl": 30}]})
	with _gan(_vao_dat(may)):
		a, b = _gui_dong_thoi(may, lambda: bs.dat(don, MA_LAN), "truoc_khoa:KH")
		_khong_loi(may, a, b)
		la("số phiếu đặt mang mã lần gửi", len(may.so_moi), 1)
		la("số lần thử ghi phiếu đặt", may.thu_ghi_so, 1)
		la("lần sau trả đúng đơn lần trước", b.kq["ma"], a.kq["ma"])
		la("lần sau có QR đủ tiền đơn và đủ dòng hàng", (b.kq["qr"]["so_tien"], b.kq["con_lai"], [(d["ma"], d["sl"]) for d in b.kq["dong"]]),
			(840000.0, 840000.0, [("BANU00001", 30.0)]))


@ca("Codex #531 f2: ô mã lần gửi trên phiếu đặt (thiết kế riêng, sỉ) khai ràng buộc duy nhất; ô dòng sao kê đã chiếm có chỉ mục để đọc có khoá không khoá cả bảng")
def _f2_khai_o():
	o = {f["fieldname"]: f for d in (tkr.TRUONG_MOI, bs.TRUONG_MOI) for v in d.values() for f in v}
	la("unique", (o["vgb_tkr_lan"].get("unique"), o["vgb_si_lan"].get("unique")), (1, 1))
	la("chỉ mục vgb_gd_tkr", o["vgb_gd_tkr"].get("search_index"), 1)


# ================================================== finding 3: đính PDF giấy báo Có

PDF = "data:application/pdf;base64," + base64.b64encode(b"%PDF-1.4 giay bao co").decode()


class _Ghi(object):
	"""Frappe giả cho ghi_so_phieu: một phiếu thu nháp chuyển khoản do máy lập,
	hook trước ghi sổ chạy THẬT chung_tu_tien.chan_thieu_dinh_kem."""

	def __init__(self, so, gd="BT-7", khac=()):
		self.so, self.gd, self.tep, self.da_ghi, self.khac = so, gd, [], [], list(khac)

	def get_doc(self, dt, ten=None, *a, **k):
		g = self
		if isinstance(dt, dict) and dt.get("doctype") == "File":
			class Tep(_fr._dict):
				def insert(self, **k2):
					g.tep.append(dict(self))
			t = Tep(dt)
			t.flags = _fr._dict()
			return t

		class Pe(_fr._dict):
			def submit(self):
				from vagabond import chung_tu_tien
				chung_tu_tien.chan_thieu_dinh_kem(self)
				self.docstatus = 1
				g.da_ghi.append(self.name)
		p = Pe(doctype="Payment Entry", name=ten, docstatus=0, vgb_phieu_dat=self.so, vgb_gd_tkr=self.gd,
			paid_amount=3780000, payment_type="Receive", paid_from="1311 - Phải thu", paid_to="1121 - MB",
			creation="2026-11-03 10:00:00")
		p.flags = _fr._dict()
		return p

	def count(self, dt, f=None):
		return len([x for x in self.tep if x.get("attached_to_name") == (f or {}).get("attached_to_name")])

	def get_value(self, dt, ten=None, f=None, as_dict=False, **k):
		if dt == "Bank Transaction":
			return _fr._dict(docstatus=1, deposit=3780000)
		return None

	def sql(self, q, a=None, as_dict=False, **k):
		if "`tabPayment Entry`" in q:
			# Đọc hiện tại các phiếu chiếm dòng sao kê: chính phiếu đang ghi sổ và phiếu khác (nếu có).
			return [_fr._dict(name=x, vgb_gd_tkr=self.gd) for x in ["PE-9"] + self.khac]
		if "`tabSales Order`" in q:
			return [(a[0],)]
		return [(self.gd,)]


def _ghi_so(mo_dun, so, anh, khac=()):
	g = _Ghi(so, khac=khac)
	ps = [mock.patch.object(_fr, "get_doc", g.get_doc), mock.patch.object(_fr.db, "count", g.count, create=True),
		mock.patch.object(_fr.db, "get_value", g.get_value), mock.patch.object(_fr.db, "sql", g.sql),
		mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Accounts User"]),
		mock.patch.object(_fr, "parse_json", json.loads, create=True),
		mock.patch.object(mo_dun, "tom_tat", lambda ten, khoa=False: {"name": ten})]
	loi = None
	with _gan(ps):
		try:
			mo_dun.ghi_so_phieu(so, "PE-9", json.dumps(anh))
		except Exception as e:  # noqa: B902
			loi = e
	return g, loi


@ca("Codex #531 f3: kế toán đính PDF giấy báo Có ở màn Đơn đặt trước rồi ghi sổ: tệp PDF được đính, phiếu thu ghi sổ được")
def _f3_pdf_tkr():
	g, loi = _ghi_so(tkr, "SO-1", [{"ten": "giay-bao-co.pdf", "noi_dung": PDF}])
	la("lỗi", str(loi) if loi else "", "")
	la("tệp đính vào phiếu", [(t["file_name"], t["attached_to_name"]) for t in g.tep], [("giay-bao-co.pdf", "PE-9")])
	la("phiếu đã ghi sổ", g.da_ghi, ["PE-9"])


@ca("Codex #531 f3: kế toán đính PDF giấy báo Có ở màn Đơn sỉ web rồi ghi sổ: tệp PDF được đính, phiếu thu ghi sổ được")
def _f3_pdf_bsi():
	g, loi = _ghi_so(bs, "SO-2", [{"ten": "GBC 0311.PDF", "noi_dung": PDF}])
	la("lỗi", str(loi) if loi else "", "")
	la("tệp đính vào phiếu", [(t["file_name"], t["attached_to_name"]) for t in g.tep], [("GBC 0311.PDF", "PE-9")])
	la("phiếu đã ghi sổ", g.da_ghi, ["PE-9"])


@ca("Codex #531 f3: tệp không nhận (docx) hoặc rỗng thì báo câu tiếng Việt nói rõ cần ảnh hay PDF, KHÔNG gọi ghi sổ")
def _f3_tep_sai():
	g, loi = _ghi_so(tkr, "SO-1", [{"ten": "giay-bao-co.docx", "noi_dung": PDF}])
	dung("câu nói rõ đuôi nhận", loi is not None and "PDF" in str(loi))
	la("không ghi sổ", g.da_ghi, [])
	g, loi = _ghi_so(bs, "SO-2", [])
	dung("không tệp nào thì nói rõ giấy báo Có", loi is not None and "giấy báo Có" in str(loi))
	dung("câu không phải câu hook Uỷ nhiệm chi", "Uỷ nhiệm chi" not in str(loi))
	la("không ghi sổ", g.da_ghi, [])


@ca("Codex #531 f3: dòng sao kê của phiếu đã có phiếu thu khác chiếm (nháp đôi cũ) thì không ghi sổ phiếu thứ hai")
def _f3_chan_phieu_doi():
	g, loi = _ghi_so(tkr, "SO-1", [{"ten": "gbc.jpg", "noi_dung": PDF}], khac=["PE-3"])
	dung("chặn và nêu phiếu kia", loi is not None and "PE-3" in str(loi))
	la("không ghi sổ", g.da_ghi, [])


# ================================================== finding 4: mở lại QR đơn sỉ trả trước

def _qr_don(t, khach="SI00012", ma="BSI26110002"):
	ps = [mock.patch.object(bs, "_khach_phien", lambda: (_fr._dict(name=khach), "") if khach else (None, "chua_dang_nhap")),
		mock.patch.object(_fr.db, "get_value", lambda dt, f=None, *a, **k: "SO-2" if (
			isinstance(f, dict) and f.get("customer") == "SI00012" and f.get("vgb_si_ma") == "BSI26110002") else None),
		mock.patch.object(bs, "tom_tat", lambda ten, khoa=False: dict(t, name=ten)),
		mock.patch.object(bs, "_qr", lambda m, so: {"noi_dung": m, "so_tien": so, "anh": "data:x"}),
		mock.patch.object(bs, "_khong_cache", lambda: None)]
	with _gan(ps):
		return bs.qr_don(ma)


@ca("Codex #531 f4: khách sỉ mở lại QR đơn trả trước chưa chuyển: máy chủ trả QR đúng mã đơn, số tiền là phần còn phải thu máy chủ tính")
def _f4_qr_don():
	t = {"ma": "BSI26110002", "tra_truoc": 1, "trang_thai": "cho_tt", "con_lai": 3780000.0, "tong": 3780000}
	r = _qr_don(t)
	la("qr", (r.get("ok"), r["qr"]["noi_dung"], r["qr"]["so_tien"], r["trang_thai"]), (1, "BSI26110002", 3780000.0, "cho_tt"))
	r = _qr_don(dict(t, trang_thai="cho_giao", con_lai=0.0))
	la("đơn đã nhận tiền không có QR", (r.get("ok"), r.get("qr")), (1, None))
	r = _qr_don(dict(t, tra_truoc=0, trang_thai="cho_giao", con_lai=0.0))
	la("đơn công nợ không có QR", r.get("qr"), None)
	nem("đơn của khách khác", lambda: _qr_don(t, khach="SI00099"))
	nem("chưa đăng nhập", lambda: _qr_don(t, khach=""))
	nem("mã sai dạng", lambda: _qr_don(t, ma="TKR26110001"))


@ca("Codex #531 f4: qr_don là cửa khách (Guest, POST, trần lượt), không đi qua cổng quyền nhân viên, có trong danh sách cửa ngõ")
def _f4_cua_ngo():
	import ast
	cay = ast.parse((GOC / "vagabond/banh_si.py").read_text(encoding="utf-8"))
	f = [x for x in cay.body if isinstance(x, ast.FunctionDef) and x.name == "qr_don"]
	la("có một hàm", len(f), 1)
	trang = [ast.unparse(d) for d in f[0].decorator_list]
	dung("Guest POST", any("allow_guest=True" in d and "POST" in d for d in trang))
	dung("trần lượt", any(d.startswith("rate_limit") for d in trang))
	than = ast.unparse(f[0])
	dung("không cổng nhân viên", "_kiem_quyen" not in than)
	dung("lấy khách từ phiên", "_khach_phien()" in than)
	from vagabond.khung.kiem_thu import thu_cua_ngo
	dung("đăng ký cửa ngõ", "qr_don" in thu_cua_ngo.CUA_NGO["banh_si.py"])


# ================================================== vòng 4: QR công nợ chỉ đòi phần còn lại

class _CongNo(object):
	"""Frappe giả cho cong_no: hoá đơn công nợ, phiếu đòi nợ lập ra và đọc lại.
	Chạy THẬT bang_khach_no, lap_phieu_doi_no, no_cua_khach, qr_no_cua_khach
	và phép tính nợ của thu_tien; phiếu đòi nợ tính tong_tien như controller
	VagabondCongNo.validate (tổng ô so_tien các dòng)."""

	TRUONG = ("name", "customer", "customer_name", "posting_date", "grand_total", "outstanding_amount",
		"vgb_pt_thanh_toan", "custom_nguon", "vgb_quay", "vgb_ma_tham_chieu", "vgb_khach_no", "docstatus")

	def __init__(self, hd):
		self.hd = {h["name"]: dict(h) for h in hd}
		self.phieu = {}

	def get_all(self, dt, filters=None, fields=None, **k):
		f = filters or {}
		if dt != "Sales Invoice":
			return []
		ds = [h for h in self.hd.values() if h["docstatus"] == 1]
		if isinstance(f.get("name"), list):
			ds = [h for h in ds if h["name"] in f["name"][1]]
		if f.get("vgb_pt_thanh_toan"):
			ds = [h for h in ds if h["vgb_pt_thanh_toan"] == f["vgb_pt_thanh_toan"]]
		if k.get("pluck"):
			return [h[k["pluck"]] for h in ds]
		return [_fr._dict(h, due_date="2026-11-20") for h in ds]

	def get_value(self, dt, ten=None, f=None, as_dict=False, **k):
		if dt == "Sales Invoice":
			h = self.hd.get(ten)
			if not h:
				return None
			return _fr._dict({x: h.get(x) for x in f}) if isinstance(f, (list, tuple)) else h.get(f)
		if dt == "Customer":
			return "Café Lá Me"
		return None

	def sql(self, q, a=None, as_dict=False, **k):
		if "`tabVagabond Cong No Dong`" in q:
			return [(d.hoa_don,) for p in self.phieu.values() for d in p.dong]
		if "from `tabVagabond Cong No` where khach" in q:
			ds = [{"name": n} for n, p in self.phieu.items() if p.khach == a[0]]
			# Câu SQL có LIMIT thì cơ sở dữ liệu cắt đúng như vậy (vòng 5).
			m = re.search(r"limit (\d+)", q)
			return ds[:int(m.group(1))] if m else ds
		return []

	def new_doc(self, dt):
		g = self

		class Phieu(_fr._dict):
			def append(self, o, d):
				self.setdefault(o, []).append(_fr._dict(d))

			def insert(self, **k2):
				self.tong_tien = sum(float(d.so_tien or 0) for d in self.get("dong") or [])
				self.name = "CN-%d" % (len(g.phieu) + 1)
				self.da_thu = 0
				g.phieu[self.name] = self
		p = Phieu(doctype=dt)
		p.flags = _fr._dict()
		return p

	def get_doc(self, dt, ten=None, *a, **k):
		return self.phieu[ten]

	def da_gom(self):
		return {d.hoa_don for p in self.phieu.values() for d in p.dong}


def _hd_no(ten, tong, con):
	return {"name": ten, "customer": "SI00012", "customer_name": "Café Lá Me", "posting_date": "2026-10-20",
		"grand_total": tong, "outstanding_amount": con, "vgb_pt_thanh_toan": "Công nợ", "custom_nguon": "Khách sỉ",
		"vgb_quay": "SALES", "vgb_ma_tham_chieu": "", "vgb_khach_no": None, "docstatus": 1}


def _gan_cong_no(g, vai, ve=None):
	from vagabond import cong_no, tai_khoan
	from vagabond import thu_tien as tt
	return [mock.patch.object(_fr, "get_all", g.get_all), mock.patch.object(_fr.db, "get_value", g.get_value),
		mock.patch.object(_fr.db, "sql", g.sql), mock.patch.object(_fr, "new_doc", g.new_doc, create=True),
		mock.patch.object(_fr, "get_doc", g.get_doc), mock.patch.object(_fr.db, "exists", lambda *a, **k: None),
		mock.patch.object(_fr, "get_roles", lambda *a, **k: vai),
		mock.patch.object(_fr, "parse_json", json.loads, create=True),
		mock.patch.object(tt, "si_co_dong_cong_no", lambda: set()), mock.patch.object(tt, "bang_dong_cua", lambda ds: {}),
		mock.patch.object(cong_no, "_hd_da_gom", g.da_gom), mock.patch.object(cong_no, "_tien_da_ve_theo_hd", lambda ds: {k: v for k, v in (ve or {}).items() if k in ds}),
		mock.patch.object(cong_no, "_sepay_cn", lambda ma: {}),
		mock.patch.object(tai_khoan, "tk_phieu_no", lambda: {"bank": "MB", "stk": "0931224334", "ten": "VAGABOND"}),
		mock.patch("vagabond.qr_chuyen_khoan.anh_qr", lambda tk, so, nd: "data:qr")]


@ca("Codex #531 v4: khách sỉ đã trả một phần hoá đơn rồi bấm Thanh toán qua QR: phiếu đòi nợ và QR chỉ đòi phần còn lại (1.000.000 đã trả 600.000 thì đòi 400.000)")
def _v4_qr_khach_si():
	g = _CongNo([_hd_no("SI-1", 1000000, 400000), _hd_no("SI-2", 500000, 500000)])
	kh = _fr._dict(name="SI00012", customer_name="Café Lá Me", vgb_si_cuoi_ky=1)
	ps = _gan_cong_no(g, ["Guest"]) + [mock.patch.object(bs, "_khach_phien", lambda: (kh, "")),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02")]
	with _gan(ps):
		r = bs.qr_no()
	la("một phiếu", len(r["phieu"]), 1)
	p = r["phieu"][0]
	la("QR đòi", (p["qr"]["so_tien"], p["con_thieu"], p["tong_tien"]), (900000, 900000.0, 900000.0))
	la("dòng phiếu", sorted((d.hoa_don, d.so_tien) for d in g.phieu["CN-1"].dong), [("SI-1", 400000.0), ("SI-2", 500000.0)])


@ca("Codex #531 v4: Sales lập phiếu đòi nợ ở màn Công nợ cho hoá đơn đã trả một phần: phiếu ghi đúng số còn đòi như màn hiện, không ghi cả tờ")
def _v4_sales_tao_phieu():
	from vagabond import cong_no
	g = _CongNo([_hd_no("SI-1", 1000000, 400000)])
	with _gan(_gan_cong_no(g, ["Sales Manager"]) + [mock.patch.object(cong_no, "xem_phieu", lambda ten: {"name": ten})]):
		man = cong_no.ds_khach_no()
		cong_no.tao_phieu("SI00012", json.dumps(["SI-1"]))
	la("màn Công nợ hiện còn đòi", man["khach"][0]["hd"][0]["tien"], 400000.0)
	la("phiếu ghi", (g.phieu["CN-1"].tong_tien, g.phieu["CN-1"].dong[0].so_tien), (400000.0, 400000.0))


@ca("Codex #531 v4: tiền đã về chờ ghi sổ (đã xác minh) cũng trừ khỏi phiếu, đúng số màn Công nợ hiện: còn nợ sổ cái 400.000, đã về 100.000 thì đòi 300.000")
def _v4_tien_da_ve():
	from vagabond import cong_no
	g = _CongNo([_hd_no("SI-1", 1000000, 400000)])
	ve = {"SI-1": {"phan_bo": 100000, "da_xac_minh": 1, "cac_pe": ["PE-NHAP"]}}
	with _gan(_gan_cong_no(g, ["Sales Manager"], ve) + [mock.patch.object(cong_no, "xem_phieu", lambda ten: {"name": ten})]):
		man = cong_no.ds_khach_no()
		cong_no.tao_phieu("SI00012", json.dumps(["SI-1"]))
	la("màn hiện", man["khach"][0]["hd"][0]["tien"], 300000.0)
	la("phiếu ghi", g.phieu["CN-1"].tong_tien, 300000.0)


@ca("Codex #531 v4: hoá đơn đã thu đủ thì không lập phiếu đòi nợ, câu tiếng Việt nêu số hoá đơn")
def _v4_da_thu_du():
	from vagabond import cong_no
	g = _CongNo([_hd_no("SI-1", 1000000, 0)])
	with _gan(_gan_cong_no(g, ["Sales Manager"])):
		try:
			cong_no.lap_phieu_doi_no("SI00012", ["SI-1"])
			loi = ""
		except _fr.ValidationError as e:
			loi = str(e)
	dung("câu nêu hoá đơn đã thu đủ: " + loi, "SI-1" in loi and "đã thu đủ" in loi)
	la("không phiếu nào", g.phieu, {})


@ca("Codex #531 v4: một phép tính số còn đòi trong cong_no (tinh_con_doi); màn Công nợ và lập phiếu đòi nợ cùng gọi nó, không chỗ nào tự tính hay lấy grand_total làm số đòi")
def _v4_mot_nguon():
	import ast
	cay = ast.parse((GOC / "vagabond/cong_no.py").read_text(encoding="utf-8"))
	ham = {f.name: f for f in cay.body if isinstance(f, ast.FunctionDef)}

	def goi(f):
		return {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
			for n in ast.walk(f) if isinstance(n, ast.Call)}
	tu_tinh = sorted(t for t, f in ham.items() if t != "tinh_con_doi" and goi(f) & {"con_no_cua", "chia_no_hoa_don"})
	la("hàm tự tính nợ ngoài tinh_con_doi", tu_tinh, [])
	for t in ("bang_khach_no", "lap_phieu_doi_no"):
		dung(t + " gọi tinh_con_doi", "tinh_con_doi" in goi(ham[t]))
	dung("lap_phieu_doi_no không đọc grand_total", "grand_total" not in ast.unparse(ham["lap_phieu_doi_no"]))


# ================================================== vòng 5: đủ phiếu, và đọc hiện tại khi dựng QR công nợ

def _phieu_mo(ten, ma, hoa_don, tien, khach="SI00012"):
	return _fr._dict(name=ten, ma_phieu=ma, khach=khach, tong_tien=tien, da_thu=0, han_qr="2026-11-09", trang_thai="Cho thu",
		ma_gd="", dong=[_fr._dict(hoa_don=hoa_don, so_tien=tien, khach=khach)])


@ca("Codex #531 v5: khách có 21 phiếu đòi nợ còn mở, mỗi phiếu còn 100.000: tổng công nợ và danh sách QR tính ĐỦ 21 phiếu (2.100.000), không cắt ở 20")
def _v5_du_phieu():
	from vagabond import cong_no
	g = _CongNo([])
	for i in range(1, 22):
		g.phieu["CN-%02d" % i] = _phieu_mo("CN-%02d" % i, "DNTT-26-10-%05d" % i, "SI-%02d" % i, 100000)
	kh = _fr._dict(name="SI00012", customer_name="Café Lá Me", vgb_si_cuoi_ky=1)
	ps = _gan_cong_no(g, ["Guest"]) + [mock.patch.object(bs, "_khach_phien", lambda: (kh, "")),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02")]
	with _gan(ps):
		n = cong_no.no_cua_khach("SI00012")
		tk = bs.tom_tat_no(n["hd"], n["phieu"], n["han"], "2026-11-02")
		r = bs.qr_no()
	la("tổng công nợ trang Tài khoản", tk["tong"], 2100000.0)
	la("số phiếu có QR", len(r["phieu"]), 21)
	la("tổng trong phản hồi QR", r["no"]["tong"], 2100000.0)


class _CongNoHaiKetNoi(_MayChu):
	"""MariaDB giả hai kết nối (như _MayChu) cho cong_no: hoá đơn công nợ tĩnh,
	phiếu đòi nợ và dòng phiếu có ảnh chụp REPEATABLE READ; đọc `for update`
	(kể cả frappe.get_doc(..., for_update=True)) thấy bản đã commit."""

	def __init__(self, hd):
		_MayChu.__init__(self)
		self.hd = {h["name"]: dict(h) for h in hd}
		self.cn = {}
		self.dem_cn = 0

	def _anh(self):
		kn = self.kn()
		if kn.anh is None:
			with self.cv:
				kn.anh = {"pe": copy.deepcopy(self.pe), "bt": copy.deepcopy(self.bt), "so": copy.deepcopy(self.so_moi),
					"cn": copy.deepcopy(self.cn)}
		return kn.anh

	def commit(self, *a, **k):
		kn = self.kn()
		with self.cv:
			for r in [x for x in kn.cho if x["_bang"] == "cn"]:
				self.cn[r["name"]] = r
			kn.cho = [x for x in kn.cho if x["_bang"] != "cn"]
		_MayChu.commit(self)

	def _cn(self, hien_tai):
		if hien_tai:
			with self.cv:
				goc = copy.deepcopy(self.cn)
		else:
			goc = copy.deepcopy(self._anh()["cn"])
		for r in self.kn().cho:
			if r["_bang"] == "cn":
				goc[r["name"]] = r
		return goc

	def sql(self, q, a=None, as_dict=False, **k):
		khoa = "for update" in q.lower()
		if "inner join" in q and "`tabVagabond Cong No`" in q:
			return [{"hoa_don": d["hoa_don"]} for p in self._cn(khoa).values()
				if p["trang_thai"] in ("Cho thu", "Thu thieu") for d in p["dong"]]
		if "from `tabVagabond Cong No` where khach" in q:
			ds = [{"name": n} for n, p in sorted(self._cn(khoa).items()) if p["khach"] == a[0]
				and p["trang_thai"] in ("Cho thu", "Thu thieu")]
			m = re.search(r"limit (\d+)", q)
			return ds[:int(m.group(1))] if m else ds
		if "`tabVagabond Cong No Dong`" in q:
			cha = set(a[0])
			return [(d["hoa_don"],) for n, p in self._cn(khoa).items() if n in cha for d in p["dong"]]
		if "ma_phieu like" in q:
			return []
		return _MayChu.sql(self, q, a, as_dict, **k)

	def get_all(self, dt, filters=None, fields=None, **k):
		if dt == "Sales Invoice":
			self._anh()
			return _CongNo.get_all(self, dt, filters, fields, **k)
		return _MayChu.get_all(self, dt, filters, fields, **k)

	def get_value(self, dt, f=None, fields=None, as_dict=False, for_update=False, **k):
		if dt in ("Sales Invoice", "Customer"):
			self._anh()
			return _CongNo.get_value(self, dt, f, fields, as_dict)
		return _MayChu.get_value(self, dt, f, fields, as_dict, for_update, **k)

	def get_doc(self, dt, ten=None, *a, **k):
		if dt != "Vagabond Cong No":
			return _MayChu.get_doc(self, dt, ten, *a, **k)
		p = self._cn(bool(k.get("for_update"))).get(ten)
		if not p:
			raise _fr.ValidationError("Vagabond Cong No %s not found" % ten)
		return _fr._dict(p, dong=[_fr._dict(d) for d in p["dong"]])

	def new_doc(self, dt):
		may = self

		class Phieu(_fr._dict):
			def append(self, o, d):
				self.setdefault(o, []).append(_fr._dict(d))

			def insert(self, **k2):
				with may.cv:
					may.dem_cn += 1
					self.name = "CN-%d" % may.dem_cn
				may.kn().cho.append({"_bang": "cn", "name": self.name, "khach": self.khach, "ma_phieu": self.ma_phieu,
					"tong_tien": sum(float(d.so_tien or 0) for d in self.get("dong") or []), "da_thu": 0, "ma_gd": "",
					"han_qr": str(self.han_qr), "trang_thai": self.trang_thai,
					"dong": [dict(d) for d in self.get("dong") or []]})
		p = Phieu(doctype=dt)
		p.flags = _fr._dict()
		return p


@ca("Codex #531 v5: hai lần bấm QR công nợ cùng lúc của một khách: lượt chờ khoá khách dựng phản hồi bằng đọc hiện tại, vẫn nhận QR của phiếu lượt trước vừa lập (không trả danh sách QR rỗng)")
def _v5_qr_dong_thoi():
	from vagabond import cong_no, tai_khoan
	from vagabond import thu_tien as tt
	may = _CongNoHaiKetNoi([_hd_no("SI-1", 1000000, 400000), _hd_no("SI-2", 500000, 500000)])
	kh = _fr._dict(name="SI00012", customer_name="Café Lá Me", vgb_si_cuoi_ky=1)

	def khach_phien():
		may.get_all("Sales Invoice", {"name": ["in", ["__"]]})  # phiên khách: đọc thường, chụp ảnh như get_all thật
		return kh, ""
	ps = [mock.patch.object(_fr, "get_all", may.get_all), mock.patch.object(_fr.db, "get_value", may.get_value),
		mock.patch.object(_fr.db, "sql", may.sql), mock.patch.object(_fr, "new_doc", may.new_doc, create=True),
		mock.patch.object(_fr, "get_doc", may.get_doc), mock.patch.object(_fr.db, "exists", lambda *a, **k: None),
		mock.patch.object(_fr.db, "commit", may.commit), mock.patch.object(_fr.db, "rollback", may.rollback),
		mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Guest"]),
		mock.patch.object(_fr, "parse_json", json.loads, create=True),
		mock.patch.object(tt, "si_co_dong_cong_no", lambda: set()), mock.patch.object(tt, "bang_dong_cua", lambda ds: {}),
		mock.patch.object(cong_no, "_tien_da_ve_theo_hd", lambda ds: {}), mock.patch.object(cong_no, "_sepay_cn", lambda ma: {}),
		mock.patch.object(tai_khoan, "tk_phieu_no", lambda: {"bank": "MB", "stk": "0931224334", "ten": "VAGABOND"}),
		mock.patch("vagabond.qr_chuyen_khoan.anh_qr", lambda tk, so, nd: "data:qr"),
		mock.patch.object(bs, "_khach_phien", khach_phien), mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02")]
	with _gan(ps):
		b = may.chay("B", bs.qr_no, ("truoc_khoa:KH",))
		may.cho_toi(lambda: b.dang_dung == "truoc_khoa:KH", "B tới khoá khách")
		a = may.chay("A", bs.qr_no)
		may.cho_toi(lambda: a.xong, "A xong")
		may.tha(b, "truoc_khoa:KH")
		may.cho_toi(lambda: b.xong, "B xong")
	for kn in (a, b):
		if kn.loi:
			raise kn.loi
	la("chỉ một phiếu đòi nợ được lập", len(may.cn), 1)
	la("lượt trước có QR", [(p["ma_phieu"] and p["qr"]["so_tien"]) for p in a.kq["phieu"]], [900000])
	la("lượt chờ khoá cũng có QR của đúng phiếu đó", [(p["ma_phieu"], p["qr"]["so_tien"]) for p in b.kq["phieu"]],
		[(p["ma_phieu"], p["qr"]["so_tien"]) for p in a.kq["phieu"]])
	la("lượt chờ khoá: tổng công nợ không đếm hai lần", b.kq["no"]["tong"], 900000.0)


# ------------------------------------------------- bench #531: cột bộ sao kê

@ca("Bench #531 v631: hỏi chủ dòng sao kê cho bộ sao kê không lọc cột bộ sao kê trên loại chứng từ không có cột đó (phiếu thu cọc thiết kế riêng)")
def _bench_cot_bo_sao_ke():
	# Bench thật (do_khoa_476) trên 4934852 đổ: dc.gan → _chu_khac(bo=True)
	# duyệt sổ đối soát, gặp luồng thiết kế riêng khai Payment Entry và thêm
	# điều kiện vgb_bo_sao_ke; MariaDB báo (1054, "Unknown column
	# 'vgb_bo_sao_ke' in 'WHERE'"). Ca này chạy THẬT nap_so với đủ mô đun đã
	# khai và một get_value giả bắt chước MariaDB: cột không có là ném lỗi.
	import frappe
	from vagabond import bo_sao_ke_db as bsdb, doi_chieu_app as dc, doi_soat_sepay as dss
	from vagabond import thiet_ke_rieng as tkr

	hoi = []

	class LoiCot(Exception):
		pass

	def get_value(dt, loc, field, **kw):
		hoi.append((dt, dict(loc)))
		if "vgb_bo_sao_ke" in loc and dt not in bsdb.PHIEU:
			raise LoiCot("(1054, \"Unknown column 'vgb_bo_sao_ke' in 'WHERE'\") trên " + dt)
		if dt == tkr.PE and "vgb_gd_tkr" in loc:
			return "PE-TKR-1"
		return None

	g = frappe._dict(name="BT-1", reference_number="FT1", flags=frappe._dict())
	d = frappe._dict(name="TTNB-1", doctype="Vagabond De Nghi Chi")
	with mock.patch.object(frappe.db, "sql", return_value=[]), \
			mock.patch.object(frappe.db, "get_value", side_effect=get_value):
		for bo in (True, False):
			hoi.clear()
			try:
				chu = dc._chu_khac(g, d, bo=bo)
			except LoiCot as e:
				chu = "LOI: %s" % e
			la("bo=%s: phiếu thu cọc vẫn là chủ dòng, không lỗi cột" % bo, chu, "PE-TKR-1")
			dung("bo=%s: sổ có luồng thiết kế riêng" % bo, any(dt == tkr.PE for dt, _ in hoi))
	# Loại có cột bộ sao kê vẫn giữ điều kiện loại phiếu đã vào bộ.
	hoi.clear()
	with mock.patch.object(frappe.db, "sql", return_value=[]), \
			mock.patch.object(frappe.db, "get_value", side_effect=lambda dt, loc, f, **k: hoi.append((dt, dict(loc)))):
		la("không chủ", dc._chu_khac(g, d, bo=True), "")
	co_cot = [dt for dt, loc in hoi if dt in bsdb.PHIEU]
	dung("có loại chứng từ mang cột bộ sao kê trong sổ: %r" % co_cot, bool(co_cot))
	dung("các loại đó vẫn lọc phiếu đã vào bộ", all("vgb_bo_sao_ke" in loc for dt, loc in hoi if dt in bsdb.PHIEU))
	dung("loại không có cột thì không lọc", all("vgb_bo_sao_ke" not in loc for dt, loc in hoi if dt not in bsdb.PHIEU))


@ca("Bench #531 v631: số điện thoại ở form thiết kế riêng và bánh sỉ đọc theo MỘT phép với phép tạo khách; số đầu không có nhà mạng bị chặn ở cửa nhập")
def _bench_mot_phep_sdt():
	# Bench thật trên 977d3c8: số ngẫu nhiên đầu 095 qua chuan_sdt cũ
	# (0[35789]xxxxxxxx) nhưng khach_cho_don (lib.sdt, theo đầu số nhà mạng)
	# trả rỗng, phiếu đặt báo "Chưa ghi nhận được thông tin khách" SAU khi
	# khách đã gửi. Chặn ở cửa nhập: form phải đọc đúng như phép tạo khách.
	from vagabond import banh_si as bs_, lib, nhap_khach as nk
	from vagabond import thiet_ke_rieng as tkr_
	mau = ["0909 123 456", "84909123456", "+84 909 123 456", "0951234567", "0801234567", "0312345678",
		"0531234567", "0283 822 9999", "", "abc", "0389123456", "0701234567", "909123456"]
	for ham, ten in ((tkr_.chuan_sdt, "thiết kế riêng"), (bs_.chuan_sdt, "bánh sỉ")):
		la(ten + ": khớp phép tạo khách trên mọi mẫu", [ham(x) for x in mau], [nk.sdt_chuan(x) for x in mau])
		la(ten + ": đầu 095, 080, 031, 053 bị chặn", [ham(x) for x in ("0951234567", "0801234567", "0312345678", "0531234567")],
			["", "", "", ""])
		la(ten + ": số thật vẫn nhận", ham("0909 123 456"), "0909123456")
	la("nk.sdt_chuan là lib.sdt", nk.sdt_chuan is lib.sdt, True)
	nem("form thiết kế riêng chặn số 095 ngay khi nhận", lambda: tkr_.chuan_don({"tac_pham": "x", "kich_co": "M",
		"ngay": "2026-12-01", "ten": "An", "sdt": "0951234567", "diem_nhan": "tcv"}, None, "2026-11-02", []), ValueError)


# ================================================== vòng 6: khoá phiếu đặt rồi quyết định tiền bằng đọc hiện tại

def _pe_co(ten, so, tien, ds, pt="Chuyển khoản", gd=""):
	return {"_bang": "pe", "name": ten, "docstatus": ds, "payment_type": "Receive", "paid_amount": tien, "received_amount": tien,
		"vgb_gd_tkr": gd, "vgb_phieu_dat": so, "mode_of_payment": pt, "vgb_quay": "SALES" if pt != "Tiền mặt" else "TCV",
		"posting_date": "2026-11-03", "creation": "2026-11-03 09:00:00"}


def _sinh_giao(vet):
	"""Mô đun erpnext giả cho giao_banh / giao_hang: ghi lại lúc tới bước lập
	chứng từ rồi ném lỗi có dấu, để ca kiểm biết các phép chặn trước đó đã qua."""
	class Ct(_fr._dict):
		def set(self, k, v):
			self[k] = v

		def append(self, k, v):
			self.setdefault(k, []).append(v)

		def run_method(self, *a):
			pass

	def lap(ten, **k):
		vet["lap"] = ten
		c = Ct(items=[])
		c.flags = _fr._dict()
		may = vet.get("may")

		def insert(**k2):
			c.name = c.get("name") or "SI-%d" % (len(may.si) + 1)

		def submit():
			# Ô gán bằng thuộc tính (si.custom_pancake_id = ...) như mã thật.
			may.kn().cho.append({"_bang": "si", "name": c.name, "custom_pancake_id": getattr(c, "custom_pancake_id", None),
				"docstatus": 1})
		c.insert, c.submit = insert, submit
		return c
	sel = types.ModuleType("erpnext.selling.doctype.sales_order.sales_order")
	sel.make_sales_invoice = lap
	sel.make_delivery_note = lap
	dnm = types.ModuleType("erpnext.stock.doctype.delivery_note.delivery_note")
	dnm.make_sales_invoice = lap
	mods = {}
	if "vagabond.ban_hang" not in sys.modules:
		# ban_hang kéo requests ở đầu tệp, máy CI không có; giao_banh chỉ lấy
		# một hằng chữ từ đó nên ca kiểm không nạp mô đun thật.
		bh = types.ModuleType("vagabond.ban_hang")
		bh.XHD_MAC_DINH = "Bán cho người tiêu dùng"
		mods["vagabond.ban_hang"] = bh
	return dict(mods, **{"erpnext": types.ModuleType("erpnext"), "erpnext.selling": types.ModuleType("x"),
		"erpnext.selling.doctype": types.ModuleType("x"), "erpnext.selling.doctype.sales_order": types.ModuleType("x"),
		"erpnext.selling.doctype.sales_order.sales_order": sel, "erpnext.stock": types.ModuleType("x"),
		"erpnext.stock.doctype": types.ModuleType("x"), "erpnext.stock.doctype.delivery_note": types.ModuleType("x"),
		"erpnext.stock.doctype.delivery_note.delivery_note": dnm})


def _vao6(may, vet):
	"""Như _vao, thêm phần thu tiền mặt, giao, huỷ. Điểm bán đọc bằng phép
	thường (cấu hình), nên lượt thu tiền mặt đã có ảnh chụp TRƯỚC khi khoá đơn,
	đúng như diem_ban.ds thật."""
	from vagabond import thu_tien, xuat_kho
	diem = [{"ma": "SALES", "quay": "", "bat": 1, "ten": "Sales Online"}, {"ma": "TCV", "quay": "TCV", "bat": 1, "ten": "TCV"}]

	def ds_diem():
		may.get_all("Vagabond Diem Ban")
		return diem

	vet["may"] = may

	def cap(si, ds):
		vet.setdefault("lan_cap", []).append(sorted(ds))
		vet["cap"] = sorted(ds)
		if vet.get("cho_qua"):
			return si
		raise RuntimeError("toi_buoc_can")
	def vai(*a, **k):
		# frappe.get_roles hụt cache thì đọc bảng Has Role (đọc thường): yêu cầu
		# đã có ảnh chụp trước lúc khoá đơn, như mọi màn kiểm vai rồi mới khoá.
		may.get_all("Has Role")
		return ["Sales Manager", "System Manager"]
	them = [mock.patch.object(_fr, "get_roles", vai),
		mock.patch.object(_fr, "generate_hash", lambda *a, **k: "moc", create=True),
		mock.patch.object(thu_tien, "tk_tien_thu", lambda cty, pt: ("1111 - TM", None)),
		mock.patch.object(thu_tien, "_giu_chu", lambda *a, **k: None),
		mock.patch.object(utd, "cap_ung_truoc", cap),
		mock.patch.object(xuat_kho, "_kho_that", lambda ct: [_fr._dict(name="Kho Sỉ - VGB", warehouse_name="Kho Sỉ")]),
		mock.patch.object(xuat_kho, "_chan_qua_ton", lambda *a: None),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-05"),
		mock.patch.dict(sys.modules, _sinh_giao(vet))]
	ps = _vao(may, them)
	ps = [p for p in ps if getattr(p, "attribute", None) != "_ds_diem"]
	ps += [mock.patch.object(tkr, "_ds_diem", ds_diem), mock.patch.object(bs, "_ds_diem", ds_diem)]
	return ps


def _chay_dua(may, truoc, sau, diem="truoc_khoa:SO"):
	"""`sau` đọc thường trước (ảnh chụp), chờ khoá phiếu đặt đang ở `truoc`;
	`truoc` xong và commit thì `sau` được khoá và chạy tiếp."""
	b = may.chay("B", sau, (diem,))
	may.cho_toi(lambda: b.dang_dung == diem, "B tới " + diem)
	a = may.chay("A", truoc)
	may.cho_toi(lambda: a.xong, "A xong")
	may.tha(b, diem)
	may.cho_toi(lambda: b.xong, "B xong")
	if a.loi:
		raise a.loi
	return a, b


@ca("Codex #531 v6: thu tiền mặt chờ khoá trong lúc lượt khớp chuyển khoản lập phiếu cọc 3.780.000: chỉ thu phần còn lại 3.780.000, không lập phiếu 7.560.000")
def _v6_thu_tien_mat():
	may = _MayChu(so=[SO_TKR], bt=[_bt("BT-7", 3780000, "TKR26110001 coc")])
	vet = {}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, _hoi_tkr, lambda: tkr.thu_tien_mat("SO-1", "TCV"))
	la("lỗi lượt thu tiền mặt", str(b.loi or ""), "")
	la("phiếu thu của đơn", _phieu_cua(may, "SO-1"), [("", 3780000.0), ("BT-7", 3780000.0)])
	la("tổng phiếu thu bằng tổng đơn", sum(x[1] for x in _phieu_cua(may, "SO-1")), 7560000.0)


@ca("Codex #531 v6: huỷ đơn thiết kế riêng chờ khoá trong lúc tiền cọc vừa về và được lập phiếu: huỷ bị chặn, phiếu đặt không bị huỷ còn tiền treo")
def _v6_huy_tkr():
	may = _MayChu(so=[SO_TKR], bt=[_bt("BT-7", 3780000, "TKR26110001 coc")])
	vet = {}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, _hoi_tkr, lambda: tkr.huy("SO-1", "khách đổi ý không đặt nữa"))
	la("phiếu đặt còn hiệu lực", may.so["SO-1"]["docstatus"], 1)
	dung("câu chặn nói đã nhận tiền: %s" % b.loi, b.loi is not None and "đã nhận tiền" in str(b.loi))
	la("phiếu cọc", _phieu_cua(may, "SO-1"), [("BT-7", 3780000.0)])


@ca("Codex #531 v6: giao bánh chờ khoá trong lúc quầy thu nốt tiền mặt: giao đi tiếp và cấn ĐỦ hai phiếu đã ghi sổ (không chặn nhầm 'còn phải thu')")
def _v6_giao_tkr():
	may = _MayChu(so=[SO_TKR])
	may.pe.append(_pe_co("PE-CK", "SO-1", 3780000, 1, gd="BT-1"))
	vet = {}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, lambda: tkr.thu_tien_mat("SO-1", "TCV"), lambda: tkr.giao_banh("SO-1", "TCV"))
	dung("tới bước cấn ứng trước: %s" % b.loi, "toi_buoc_can" in str(b.loi or ""))
	la("cấn đúng hai phiếu đã ghi sổ", vet.get("cap"), ["PE-1", "PE-CK"])


@ca("Codex #531 v6: huỷ đơn sỉ trả trước chờ khoá trong lúc tiền về và được lập phiếu thu: huỷ bị chặn, phiếu đặt không bị huỷ")
def _v6_huy_bsi():
	may = _MayChu(so=[SO_BSI], bt=[_bt("BT-9", 3780000, "BSI26110002 chuyen tien")])
	vet = {}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, _hoi_bsi, lambda: bs.huy_don("SO-2", "khách đổi ý không lấy nữa"))
	la("phiếu đặt còn hiệu lực", may.so["SO-2"]["docstatus"], 1)
	dung("câu chặn nói đã có tiền: %s" % b.loi, b.loi is not None and "đã có tiền" in str(b.loi))


@ca("Codex #531 v6: giao hàng sỉ chờ khoá trong lúc đơn vừa bị huỷ: không lập phiếu giao từ phiếu đặt đã huỷ")
def _v6_giao_bsi_da_huy():
	so3 = dict(SO_BSI, name="SO-3", vgb_si_ma="BSI26110003", vgb_si_tt="Công nợ")
	may = _MayChu(so=[so3])
	vet = {}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, lambda: bs.huy_don("SO-3", "khách đổi ý không lấy nữa"), lambda: bs.giao_hang("SO-3", "Kho Sỉ - VGB"))
	la("lượt huỷ xong", (a.kq or {}).get("ok"), 1)
	la("không tới bước lập phiếu giao", vet.get("lap"), None)
	dung("câu chặn nói đã huỷ: %s" % b.loi, b.loi is not None and "huỷ" in str(b.loi))


@ca("Codex #531 v6: hai người cùng bấm huỷ một đơn thiết kế riêng chưa cọc: lượt chờ khoá thấy đơn đã huỷ (đọc hiện tại phiếu đặt), báo 'đã huỷ', không huỷ lần hai")
def _v6_huy_hai_lan():
	may = _MayChu(so=[SO_TKR])
	vet = {}
	huy = lambda: tkr.huy("SO-1", "khách đổi ý không đặt nữa")  # noqa: E731
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, huy, huy)
	la("lượt đầu huỷ được", (a.kq or {}).get("ok"), 1)
	la("câu lượt sau", str(b.loi or ""), "Đơn TKR26110001 đã huỷ.")


@ca("Codex #531 v6: hai người cùng bấm Giao bánh và xuất hoá đơn: lượt chờ khoá thấy hoá đơn lượt trước vừa xuất (đọc hiện tại hoá đơn), báo 'đã giao', không xuất hoá đơn thứ hai")
def _v6_giao_hai_lan():
	may = _MayChu(so=[SO_TKR])
	may.pe += [_pe_co("PE-CK", "SO-1", 3780000, 1, gd="BT-1"), _pe_co("PE-TM", "SO-1", 3780000, 1, pt="Tiền mặt")]
	vet = {"cho_qua": True}
	giao = lambda: tkr.giao_banh("SO-1", "TCV")  # noqa: E731
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, giao, giao)
	la("lượt đầu xuất hoá đơn", (a.kq or {}).get("hoa_don"), "SI-1")
	la("số hoá đơn của đơn", len(may.si), 1)
	dung("lượt sau báo đã giao: %s" % b.loi, b.loi is not None and "đã giao" in str(b.loi))


@ca("Codex #531 v6: giao hàng sỉ chờ khoá trong lúc phiếu giao được lập ở Desk (ghi sổ phiếu giao cập nhật phiếu đặt nên giữ khoá hàng phiếu đặt): đọc hiện tại phiếu giao, không lập phiếu giao thứ hai")
def _v6_giao_bsi_co_phieu_giao():
	so3 = dict(SO_BSI, name="SO-3", vgb_si_ma="BSI26110003", vgb_si_tt="Công nợ")
	may = _MayChu(so=[so3])
	vet = {}

	def desk_lap_phieu_giao():
		# Mô hình lõi ERPNext: ghi sổ Delivery Note cập nhật per_delivered trên
		# Sales Order, tức là giữ khoá hàng phiếu đặt tới khi commit.
		may.sql("select name from `tabSales Order` where name=%s for update", ("SO-3",))
		may.kn().cho.append({"_bang": "dn", "name": "DN-DESK", "against_sales_order": "SO-3", "docstatus": 1})
		return {"ok": 1}
	with _gan(_vao6(may, vet)):
		a, b = _chay_dua(may, desk_lap_phieu_giao, lambda: bs.giao_hang("SO-3", "Kho Sỉ - VGB"))
	la("không tới bước lập phiếu giao", vet.get("lap"), None)
	dung("câu chặn nói đã có phiếu giao: %s" % b.loi, b.loi is not None and "đã có phiếu giao hàng" in str(b.loi))


# ================================================== vòng 7: ảnh tác phẩm trên màn Đơn đặt trước

@ca("Codex #531 v7: tom_tat trả ảnh tác phẩm từ danh mục thiết kế riêng (kể cả tác phẩm đang ẩn); đơn không tìm ra tác phẩm thì ảnh rỗng; ds_don đọc danh mục một lần")
def _v7_anh_tac_pham():
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(dict(TP, anh="/files/croquembouche.jpg"))
	nd["khoi"].append(dict(TP, id="tkr-an", tieu_de="Tác phẩm đã ẩn", hien=False, anh="/files/an.jpg"))
	may = _MayChu(so=[dict(SO_TKR, vgb_tkr_du_lieu=json.dumps({"tac_pham_id": TP["id"]})),
		dict(SO_TKR, name="SO-2", vgb_tkr_ma="TKR26110002", vgb_tkr_du_lieu=json.dumps({"tac_pham_id": "tkr-an"})),
		dict(SO_TKR, name="SO-3", vgb_tkr_ma="TKR26110003", vgb_tkr_du_lieu="{}")])
	doc = []

	def ban():
		doc.append(1)
		return copy.deepcopy(nd)

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Sales Order":
			return ["SO-1", "SO-2", "SO-3"]
		return may.get_all(dt, filters, fields, **k)
	ps = [mock.patch.object(_fr.db, "sql", may.sql), mock.patch.object(_fr, "get_all", get_all),
		mock.patch.object(_fr.db, "get_value", may.get_value), mock.patch.object(tkr, "_ban", ban),
		mock.patch.object(tkr, "_hom_nay", lambda: "2026-11-02"), mock.patch.object(tkr, "_ds_diem", lambda: []),
		mock.patch.object(tkr, "_la_ke_toan", lambda: 0),
		mock.patch.object(utd, "ten_don_man", lambda *a, **k: ["SO-1", "SO-2", "SO-3"]),
		mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Sales Manager"])]
	with _gan(ps):
		kq = may.doc_lai(lambda: tkr.ds_don())
		mot = may.doc_lai(lambda: tkr.tom_tat("SO-1"))
	la("ảnh theo đơn", [r["anh"] for r in kq["rows"]], ["/files/croquembouche.jpg", "/files/an.jpg", ""])
	la("ds_don đọc danh mục một lần (cộng một lần của tom_tat lẻ)", len(doc), 2)
	la("tom_tat một đơn tự đọc danh mục", mot["anh"], "/files/croquembouche.jpg")


@ca("Codex #531 v7: logo khách (Customer.image) chỉ nhận ảnh /files/ công khai; ds_don đọc logo MỘT lượt cho cả danh sách; ds_khach, bang_gia, tim_khach, xem_don trả ô logo")
def _v7_logo_khach():
	la("lọc logo", [bs.logo_khach(u) for u in ("/files/la-me.png", "/private/files/a.png", "https://x/a.png",
		"/files/../a", "/files/a b.png", "/files/a\"x.png", "", None)], ["/files/la-me.png", "", "", "", "", "", "", ""])
	hoi = []
	anh = {"SI00012": "/files/la-me.png", "SI00013": "/private/files/x.png", "SI00014": None}

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Sales Order":
			return ["SO-1", "SO-2", "SO-3", "SO-4"]
		if dt == "Customer":
			hoi.append(filters)
			f = filters if isinstance(filters, dict) else {}
			ten = f["name"][1] if isinstance(f.get("name"), list) else list(anh)
			return [_fr._dict(name=t, customer_name=t, image=anh.get(t), tax_id="", vgb_si_sdt="", vgb_si_cuoi_ky=0,
				disabled=0, customer_group="", mobile_no="", vgb_si_web=1) for t in ten]
		return []
	khach_don = {"SO-1": "SI00012", "SO-2": "SI00013", "SO-3": "SI00012", "SO-4": "SI00014"}
	ps = [mock.patch.object(_fr, "get_all", get_all), mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Sales Manager"]),
		mock.patch.object(utd, "ten_don_man", lambda *a, **k: ["SO-1", "SO-2", "SO-3", "SO-4"]),
		mock.patch.object(bs, "tom_tat", lambda t, khoa=False: {"name": t, "ma_khach": khach_don[t], "trang_thai": "cho_giao",
			"tra_truoc": 0, "con_lai": 0, "phieu": [], "ma": t}),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-05"), mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(bs, "_la_ke_toan", lambda: 0), mock.patch.object(bs, "_dong_gia", lambda k: []),
		mock.patch("vagabond.xuat_kho._kho_that", lambda ct: []),
		mock.patch.object(_fr.db, "get_value", lambda dt, ten, f=None, **k: _fr._dict(name=ten, customer_name="Lá Me",
			image="/files/la-me.png") if dt == "Customer" else None),
		mock.patch.object(bs, "gia_cua_khach", lambda k, n=None: {}), mock.patch.object(bs, "_lich_su_gia", lambda k: []),
		mock.patch.object(bs, "_anh_xa_si", lambda: {})]
	with _gan(ps):
		kq = bs.ds_don()
		la("logo theo đơn", [r["logo"] for r in kq["rows"]], ["/files/la-me.png", "", "/files/la-me.png", ""])
		la("một lượt đọc khách cho cả danh sách", len(hoi), 1)
		la("xem_don có logo", bs.xem_don("SO-1")["logo"], "/files/la-me.png")
		la("ds_khach có logo, ảnh riêng tư bị bỏ", [(r["name"], r["logo"]) for r in bs.ds_khach()["rows"]],
			[("SI00012", "/files/la-me.png"), ("SI00013", ""), ("SI00014", "")])
		dung("ds_khach không lộ ô image thô", all("image" not in r for r in bs.ds_khach()["rows"]))
		la("bang_gia có logo", bs.bang_gia("SI00012")["khach"]["logo"], "/files/la-me.png")
		la("tim_khach có logo", [r["logo"] for r in bs.tim_khach("Lá")], ["/files/la-me.png", "", ""])


# ================================================== vòng 8: không cắt nguồn danh sách việc đang chờ

def _khop_loc(r, f):
	for k, v in (f or {}).items():
		x = r.get(k)
		if isinstance(v, (list, tuple)):
			op, gt = v[0], v[1]
			if op == "in" and x not in gt:
				return False
			if op == "not in" and x in gt:
				return False
			if op == "is" and gt == "set" and not x:
				return False
			if op == ">=" and not (str(x or "") >= str(gt)):
				return False
			if op == "<" and not (float(x or 0) < float(gt)):
				return False
			if op == "!=" and x == gt:
				return False
		elif x != v:
			return False
	return True


class _Nguon8(object):
	"""Bảng giả có LIMIT, ORDER BY và lọc thật cho get_all và cho các câu SQL
	đọc phiếu đặt (điều kiện "đang mở" đọc từ chính câu SQL: docstatus và hoá
	đơn đã ghi sổ mang custom_pancake_id), để ca kiểm thấy đúng cái bị cắt."""

	def __init__(self, so, si=(), dk=()):
		self.so = {r["name"]: dict(r) for r in so}
		self.si = list(si)
		self.dk = list(dk)

	def _sap(self, ds, order_by):
		for phan in reversed([x.strip() for x in str(order_by or "").split(",") if x.strip()]):
			o, _, chieu = phan.partition(" ")
			ds = sorted(ds, key=lambda r: str(r.get(o.split(".")[-1]) or ""), reverse=chieu.strip().lower() == "desc")
		return ds

	def get_all(self, dt, filters=None, fields=None, pluck=None, order_by=None, limit_page_length=20, **k):
		bang = {"Sales Order": list(self.so.values()), "Vagabond Dang Ky Si": self.dk}.get(dt)
		if bang is None:
			return []
		ds = self._sap([r for r in bang if _khop_loc(r, filters)], order_by)
		if limit_page_length:
			ds = ds[:int(limit_page_length)]
		return [r[pluck] for r in ds] if pluck else [_fr._dict(r) for r in ds]

	def _da_giao(self, r, o, tt):
		return any(x["custom_pancake_id"] == "%s-%s" % (tt, r.get(o)) and x["docstatus"] == 1 for x in self.si)

	def sql(self, q, a=None, as_dict=False, **k):
		if "from `tabSales Order` so" not in q:
			return []
		o = re.search(r"so\.`?(vgb_\w+_ma)`?", q).group(1)
		tt = "TKR" if o == "vgb_tkr_ma" else "BSI"
		a = list(a or [])
		ds = [r for r in self.so.values() if r.get(o)]
		if "so.customer = %s" in q:
			kh = a.pop(0)
			ds = [r for r in ds if r.get("customer") == kh]
		if "so.docstatus = 1" in q:
			ds = [r for r in ds if r["docstatus"] == 1]
		if "not exists" in q:
			ds = [r for r in ds if not self._da_giao(r, o, tt)]
		if "docstatus in (1, 2)" in q:
			ds = [r for r in ds if r["docstatus"] in (1, 2)]
		if "delivery_date >= %s" in q:
			tu = a.pop(0)
			ds = [r for r in ds if str(r.get("delivery_date") or "") >= str(tu)]
		m = re.search(r"order by ([^\n]+?)(?: limit|$)", q.strip())
		if m:
			ds = self._sap(ds, m.group(1).replace("so.", ""))
		m = re.search(r"limit (\d+|%s)", q)
		if m:
			ds = ds[:int(a.pop(0) if m.group(1) == "%s" else m.group(1))]
		return [_fr._dict(r) for r in ds]

	def get_value(self, dt, f=None, fields=None, as_dict=False, **k):
		if dt == "Sales Order":
			r = self.so.get(f) or {}
			return _fr._dict({x: r.get(x) for x in fields}) if isinstance(fields, (list, tuple)) else r.get(fields)
		if dt == "Sales Invoice" and isinstance(f, dict):
			ds = [x for x in self.si if x["custom_pancake_id"] == f.get("custom_pancake_id") and x["docstatus"] < 2]
			return _fr._dict(ds[0], name="SI-" + ds[0]["custom_pancake_id"], due_date="", outstanding_amount=0) if ds else None
		return None

	def gan(self, them=()):
		return [mock.patch.object(_fr, "get_all", self.get_all), mock.patch.object(_fr.db, "sql", self.sql),
			mock.patch.object(_fr.db, "get_value", self.get_value)] + list(them)


def _don_si(ten, ma, ds, tao, giao="2026-11-10", tt="Trả trước", kh="SI00012"):
	return {"name": ten, "vgb_si_ma": ma, "customer": kh, "customer_name": "Café Lá Me", "docstatus": ds,
		"delivery_date": giao, "transaction_date": tao[:10], "creation": tao, "grand_total": 840000, "rounded_total": 840000,
		"net_total": 777778, "total_taxes_and_charges": 62222, "vgb_si_tt": tt, "vgb_si_du_lieu": "{}",
		"status": "To Deliver and Bill", "per_billed": 0}


@ca("Codex #531 v8: khách có một đơn chờ chuyển khoản rồi đặt thêm 30 đơn mới hơn (đã huỷ): Tài khoản vẫn có đơn đó ở 'Đơn sắp giao', đủ dữ liệu cho nút mở lại QR")
def _v8_toi_du_don_mo():
	so = [_don_si("SO-CU", "BSI26100001", 1, "2026-10-01 09:00:00")]
	so += [_don_si("SO-%02d" % i, "BSI261100%02d" % i, 2, "2026-11-01 09:%02d:00" % i) for i in range(1, 31)]
	g = _Nguon8(so)
	kh = _fr._dict(name="SI00012", customer_name="Café Lá Me", vgb_si_cuoi_ky=0)
	ps = g.gan([mock.patch.object(bs, "_khach_phien", lambda: (kh, "")), mock.patch.object(bs, "_khong_cache", lambda: None),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02"), mock.patch.object(bs, "gia_cua_khach", lambda k, n=None: {})])
	with _gan(ps):
		r = bs.toi()
	la("đơn sắp giao", [(d["ma"], d["trang_thai"], d["tra_truoc"], d["con_lai"]) for d in r["sap_giao"]],
		[("BSI26100001", "cho_tt", 1, 840000.0)])
	la("lịch sử vẫn cắt 20", len(r["lich_su"]), 20)


@ca("Codex #531 v8: màn Đơn sỉ web và Đơn đặt trước: đơn đang mở quá hạn giao trước cửa sổ ngày vẫn hiện; đơn đã giao cũ thì không")
def _v8_ds_don_qua_han():
	so = [_don_si("SO-QH", "BSI26090001", 1, "2026-09-01 09:00:00", giao="2026-09-03", tt="Công nợ"),
		_don_si("SO-GIAO-CU", "BSI26090002", 1, "2026-09-01 10:00:00", giao="2026-09-04", tt="Công nợ"),
		_don_si("SO-HUY-CU", "BSI26080003", 2, "2026-08-01 09:00:00", giao="2026-08-05", tt="Công nợ"),
		_don_si("SO-MOI", "BSI26110001", 1, "2026-11-01 09:00:00", giao="2026-11-06", tt="Công nợ")]
	g = _Nguon8(so, si=[{"custom_pancake_id": "BSI-BSI26090002", "docstatus": 1}])
	ps = g.gan([mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Sales Manager"]),
		mock.patch.object(bs, "_hom_nay", lambda: "2026-11-02"), mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(bs, "_la_ke_toan", lambda: 0), mock.patch("vagabond.xuat_kho._kho_that", lambda ct: []),
		mock.patch.object(bs, "_logo_cac_khach", lambda ds: {})])
	with _gan(ps):
		kq = bs.ds_don()
	la("đơn sỉ trên màn", [(r["ma"], r["trang_thai"]) for r in kq["rows"]], [("BSI26090001", "cho_giao"), ("BSI26110001", "cho_giao")])
	tk = [{"name": "SO-T1", "vgb_tkr_ma": "TKR26080001", "docstatus": 1, "delivery_date": "2026-08-20", "creation": "2026-08-01 09:00:00"},
		{"name": "SO-T2", "vgb_tkr_ma": "TKR26110002", "docstatus": 2, "delivery_date": "2026-11-20", "creation": "2026-11-01 09:00:00"}]
	g2 = _Nguon8(tk)
	thay = []
	with _gan(g2.gan([mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Sales Manager"]),
			mock.patch.object(tkr, "_hom_nay", lambda: "2026-11-02"), mock.patch.object(tkr, "_ban", lambda: {}),
			mock.patch.object(tkr, "tom_tat", lambda t, khoa=False, anh_tp=None: thay.append(t) or {"trang_thai": "cho_coc"}),
			mock.patch.object(tkr, "_ds_diem", lambda: []), mock.patch.object(tkr, "_la_ke_toan", lambda: 0)])):
		tkr.ds_don()
	la("đơn thiết kế riêng trên màn: đơn chờ cọc quá hạn từ tháng 8 vẫn có", thay, ["SO-T1", "SO-T2"])


@ca("Codex #531 v8: nhịp 5 phút khớp tiền đi qua MỌI đơn còn chờ tiền (501 đơn sỉ, 501 đơn thiết kế riêng), không cắt 500")
def _v8_quet_du():
	so = [_don_si("SO-%03d" % i, "BSI2611%04d" % i, 1, "2026-11-01 09:00:00") for i in range(501)]
	g = _Nguon8(so)
	da = []
	with _gan(g.gan([mock.patch.object(bs, "khop_don", lambda t: da.append(t)), mock.patch.object(_fr.db, "commit", lambda: None)])):
		bs.quet()
	la("đơn sỉ đã xét", len(da), 501)
	tk = [{"name": "SO-T%03d" % i, "vgb_tkr_ma": "TKR2611%04d" % i, "docstatus": 1, "status": "To Deliver and Bill",
		"per_billed": 0} for i in range(501)]
	g2 = _Nguon8(tk)
	da2 = []
	with _gan(g2.gan([mock.patch.object(tkr, "khop_mot", lambda t: da2.append(t)), mock.patch.object(_fr.db, "commit", lambda: None)])):
		tkr.quet()
	la("đơn thiết kế riêng đã xét", len(da2), 501)


@ca("Codex #531 v8: đăng ký chờ duyệt là việc đang chờ: 1 đăng ký chờ duyệt cũ và 300 đăng ký đã xử lý mới hơn, danh sách 'tất cả' vẫn có đăng ký chờ duyệt")
def _v8_dang_ky_cho():
	dk = [{"name": "dk-cho", "ten_quan": "Café Cũ", "trang_thai": "Chờ duyệt", "creation": "2026-09-01 09:00:00", "khach": ""}]
	dk += [{"name": "dk-%03d" % i, "ten_quan": "Q%d" % i, "trang_thai": "Từ chối", "creation": "2026-10-%02d 09:%02d:00" % (1 + i % 28, i % 60),
		"khach": ""} for i in range(300)]
	g = _Nguon8([], dk=dk)
	with _gan(g.gan([mock.patch.object(_fr, "get_roles", lambda *a, **k: ["Sales Manager"])])):
		kq = bs.ds_dang_ky("")
		cho = bs.ds_dang_ky("Chờ duyệt")
	dung("tất cả: có đăng ký chờ duyệt", "dk-cho" in [r["name"] for r in kq["rows"]])
	la("lọc chờ duyệt", [r["name"] for r in cho["rows"]], ["dk-cho"])


# ================================================== vòng 9: lọc dòng sao kê TRƯỚC khi chọn và cộng dồn

def _bt9(ten, tien, mo, tk="BA-MB", ngay="2026-11-03", **them):
	d = dict(_bt(ten, tien, mo), bank_account=tk, date=ngay, docstatus=1, currency="VND", unallocated_amount=tien)
	d.update(them)
	return d


def _khop9(so, bts, hoi, tk_so_cai=None):
	from vagabond import doi_soat_sepay as dss
	may = _MayChu(so=[so], bt=bts)
	tk_so_cai = tk_so_cai or {}
	goc = may.get_value

	def gv(dt, f=None, *a, **k):
		if dt == "Bank Account":
			return tk_so_cai.get(f, "1121 - MB")
		return goc(dt, f, *a, **k)
	# Tài khoản trong `tk_so_cai` là tài khoản ĐƯỢC khớp: ca đó thử riêng điều kiện sổ cái.
	cho_phep = {"BA-MB"} | set(tk_so_cai)
	with _gan(_vao(may, [mock.patch.object(_fr.db, "get_value", gv),
			mock.patch.object(dss, "tai_khoan_duoc_khop", lambda: cho_phep)])):
		kn = may.chay("A", hoi)
		may.cho_toi(lambda: kn.xong, "khớp xong")
	if kn.loi:
		raise kn.loi
	return _phieu_cua(may, so["name"])


@ca("Codex #531 v9: đơn sỉ 3.780.000, dòng sao kê cũ ở tài khoản không được khớp và dòng đúng ở tài khoản được khớp: lập phiếu cho dòng đúng")
def _v9_sai_tai_khoan_bsi():
	r = _khop9(SO_BSI, [_bt9("BT-1", 3780000, "BSI26110002", tk="BA-LA", ngay="2026-11-02"),
		_bt9("BT-2", 3780000, "BSI26110002 chuyen lai", ngay="2026-11-03")], _hoi_bsi)
	la("phiếu thu", r, [("BT-2", 3780000.0)])


@ca("Codex #531 v9: đơn thiết kế riêng, dòng trả đủ 7.560.000 ở tài khoản không được khớp và dòng cọc 3.780.000 đúng tài khoản: lập phiếu cọc")
def _v9_sai_tai_khoan_tkr():
	r = _khop9(SO_TKR, [_bt9("BT-1", 7560000, "TKR26110001", tk="BA-LA", ngay="2026-11-02"),
		_bt9("BT-2", 3780000, "TKR26110001 coc", ngay="2026-11-03")], _hoi_tkr)
	la("phiếu thu", r, [("BT-2", 3780000.0)])


@ca("Codex #531 v9: mọi điều kiện loại dòng đứng trước phép chọn: tài khoản ngân hàng chưa gắn sổ cái, đã đối chiếu hết ở nơi khác, khác tiền tệ, chưa ghi sổ, không phải tiền vào đều không chiếm phần còn thu của dòng đúng")
def _v9_loai_truoc():
	dung_bt = _bt9("BT-OK", 3780000, "BSI26110002", ngay="2026-11-05")
	for ten, bt, tk in (
			("chưa gắn sổ cái", _bt9("BT-X", 3780000, "BSI26110002", tk="BA-TRONG", ngay="2026-11-01"), {"BA-TRONG": None}),
			("đã đối chiếu hết", _bt9("BT-X", 3780000, "BSI26110002", ngay="2026-11-01", unallocated_amount=0), None),
			("khác tiền tệ", _bt9("BT-X", 3780000, "BSI26110002", ngay="2026-11-01", currency="USD"), None),
			("chưa ghi sổ", _bt9("BT-X", 3780000, "BSI26110002", ngay="2026-11-01", docstatus=0), None),
			("không phải tiền vào", _bt9("BT-X", 0, "BSI26110002", ngay="2026-11-01", withdrawal=3780000), None)):
		la(ten, _khop9(SO_BSI, [bt, dict(dung_bt)], _hoi_bsi, tk), [("BT-OK", 3780000.0)])


def _khop9_doi(so, bts, hoi, doi):
	"""Như `_khop9`, nhưng giữa lúc TÌM (ảnh chụp) và lúc KHOÁ dòng sao kê, một
	phiên khác đổi dòng (huỷ, đối chiếu ở nơi khác) và commit."""
	may = _MayChu(so=[so], bt=bts)
	with _gan(_vao(may)):
		kn = may.chay("A", hoi, ("truoc_khoa:BT",))
		may.cho_toi(lambda: kn.dang_dung == "truoc_khoa:BT" or kn.xong, "A sắp khoá dòng sao kê")
		dung("A dừng trước khoá dòng sao kê", kn.dang_dung == "truoc_khoa:BT")
		with may.cv:
			for g in may.bt:
				g.update(doi.get(g["name"], {}))
		may.tha(kn, "truoc_khoa:BT")
		may.cho_toi(lambda: kn.xong, "khớp xong")
	if kn.loi:
		raise kn.loi
	return _phieu_cua(may, so["name"])


@ca("Codex #531 v9: dòng sao kê bị đối chiếu ở nơi khác hoặc bị huỷ giữa lúc tìm và lúc khoá: phép lọc quyết trên bản đọc trong khoá, lập phiếu cho dòng còn lại")
def _v9_doi_giua_luc_tim_va_khoa():
	bts = lambda tien: [_bt9("BT-1", tien, "BSI26110002", ngay="2026-11-02"),  # noqa: E731
		_bt9("BT-2", 3780000, "BSI26110002 lan 2", ngay="2026-11-03")]
	la("sỉ, BT-1 đã đối chiếu hết ở nơi khác", _khop9_doi(SO_BSI, bts(3780000), _hoi_bsi,
		{"BT-1": {"unallocated_amount": 0}}), [("BT-2", 3780000.0)])
	la("sỉ, BT-1 bị huỷ", _khop9_doi(SO_BSI, bts(3780000), _hoi_bsi, {"BT-1": {"docstatus": 2}}),
		[("BT-2", 3780000.0)])
	tk = [_bt9("BT-1", 7560000, "TKR26110001", ngay="2026-11-02"), _bt9("BT-2", 3780000, "TKR26110001 coc", ngay="2026-11-03")]
	la("thiết kế riêng, BT-1 đã đối chiếu hết ở nơi khác", _khop9_doi(SO_TKR, tk, _hoi_tkr,
		{"BT-1": {"unallocated_amount": 0}}), [("BT-2", 3780000.0)])


@ca("Codex #531 v9: dòng đã có chủ (bộ sao kê, chứng từ khác) bị bỏ trước phép cộng dồn, không chiếm phần còn thu của dòng đúng")
def _v9_co_chu_truoc():
	from vagabond import doi_soat_sepay as dss
	bts = [_bt9("BT-1", 3780000, "BSI26110002", ngay="2026-11-02"), _bt9("BT-2", 3780000, "BSI26110002 lan 2", ngay="2026-11-03")]
	for ten, chu in (("bộ sao kê", "bộ sao kê BSK-0001"), ("chứng từ khác", "phiếu chi PC-0001")):
		may = _MayChu(so=[SO_BSI], bt=[dict(g) for g in bts])
		with _gan(_vao(may, [mock.patch.object(dss, "chu_cua_giao_dich",
				lambda ds, chu=chu, **k: {g: chu for g in ds if g == "BT-1"})])):
			kn = may.chay("A", _hoi_bsi)
			may.cho_toi(lambda: kn.xong, "khớp xong")
		if kn.loi:
			raise kn.loi
		la(ten, _phieu_cua(may, SO_BSI["name"]), [("BT-2", 3780000.0)])


@ca("Codex #531 v9: phép lọc thuần trả đúng lý do cho từng điều kiện, và để nguyên dòng hợp lệ")
def _v9_loc_thuan():
	ly_do_tk = lambda tk: "" if tk in ("BA-MB", "BA-TRONG") else "chưa được khớp"  # noqa: E731
	so_cai = {"BA-MB": "1121 - MB", "BA-TRONG": None}
	g = _bt9("BT-1", 3780000, "BSI26110002")
	for ten, doi, mong in (
			("hợp lệ", {}, ""),
			("chưa biết phần còn lại thì coi như còn đủ", {"unallocated_amount": None}, ""),
			("lệch dưới 1 đồng vẫn dùng", {"unallocated_amount": 3779999.5}, ""),
			("tiền đồng viết thường", {"currency": "vnd"}, ""),
			("tiền ra", {"deposit": 0, "withdrawal": 3780000}, "Dòng sao kê không phải tiền vào."),
			("vừa vào vừa ra", {"withdrawal": 1}, "Dòng sao kê không phải tiền vào."),
			("nháp", {"docstatus": 0}, "Dòng sao kê chưa ghi sổ hoặc đã huỷ."),
			("đã huỷ", {"docstatus": 2}, "Dòng sao kê chưa ghi sổ hoặc đã huỷ."),
			("đô la", {"currency": "USD"}, "Dòng sao kê không phải tiền đồng."),
			("tài khoản không được khớp", {"bank_account": "BA-LA"}, "chưa được khớp"),
			("chưa gắn sổ cái", {"bank_account": "BA-TRONG"}, "Tài khoản ngân hàng BA-TRONG chưa gắn tài khoản sổ cái."),
			("đã đối chiếu hết", {"unallocated_amount": 0}, "Dòng sao kê đã đối chiếu một phần hoặc toàn bộ ở nơi khác."),
			("đã đối chiếu một phần", {"unallocated_amount": 1000000}, "Dòng sao kê đã đối chiếu một phần hoặc toàn bộ ở nơi khác.")):
		la(ten, utd.ly_do_loai_dong(dict(g, **doi), ly_do_tk, so_cai), mong)
	dung_dc, loai = utd.loc_dong_sao_ke([dict(g, bank_account="BA-LA"), dict(g, name="BT-2")], ly_do_tk, so_cai)
	la("lọc giữ dòng hợp lệ", [x["name"] for x in dung_dc], ["BT-2"])
	la("lọc ghi lý do dòng bị loại", loai, [{"gd": "BT-1", "ly_do": "chưa được khớp"}])
