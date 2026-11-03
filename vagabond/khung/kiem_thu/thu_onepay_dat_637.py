# -*- coding: utf-8 -*-
"""v637: khách trả thẻ OnePay cho đơn đặt trước tại quầy (anh Việt 03/11/2026).

Khách quét QR trên màn quầy, trả thẻ trên trang OnePay; OnePay báo thành công
thì máy ghi sổ ngay một phiếu thu ứng trước của đúng phiếu đặt, phương thức
OnePay, quầy = điểm bán không két (tiền của Sales, Chốt ca không đếm).

Ca chạm hệ chạy HÀM THẬT (onepay.ghi_nhan, onepay_dat.ghi_nhan_the, tao_gd,
_lap_phieu, onepay.quet), chỉ thay tầng Frappe bằng bản giả ghi lại lời gọi.
Phần bấm trên màn ở hanh_vi/don_dat_truoc_630.js.
"""

import contextlib
import json
import sys
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import dat_banh as db  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import onepay as op  # noqa: E402
from vagabond import onepay_dat as od  # noqa: E402
from vagabond import thiet_ke_rieng as tkr  # noqa: E402

KHOA = "0123456789ABCDEF0123456789ABCDEF"
C = {"bat": 1, "cong": "https://onepay.vn/paygate/vpcpay.op", "merchant": "VAGABONDWEB", "access_code": "ABCD1234",
	"hash_code": KHOA, "query_user": "op01", "query_password": "mk"}
DIEM = [{"ma": "TCV", "quay": "TCV", "bat": 1}, {"ma": "NVHTN", "quay": "NVHTN", "bat": 1}, {"ma": "SALES", "bat": 1}]


def _kq(ma="TKR26110002-1", tien=3780000, ma_kq="0"):
	ts = {"vpc_MerchTxnRef": ma, "vpc_Amount": op.so_tien_vpc(tien), "vpc_TxnResponseCode": ma_kq,
		"vpc_TransactionNo": "998877", "vpc_Card": "VC", "vpc_Merchant": "VAGABONDWEB"}
	ts["vpc_SecureHash"] = op.ky(ts, KHOA)
	return ts


@ca("v637 OnePay đơn đặt trước: nhận đúng mã đơn TKR, mã giao dịch TKR...-lần đi qua phép mã chung; mã công nợ vẫn như cũ")
def _ma():
	la("mã đơn", [od.la_ma_don(x) for x in ("TKR26110002", "tkr26110002", "TKR2611000", "DNTT261100002", "BSI26110001", "")],
		[True, True, False, False, False, False])
	la("ô mang mã", (od.truong_ma("TKR26110002"), od.truong_ma("DNTT261100002")), ("vgb_tkr_ma", None))
	la("mã giao dịch", op.ma_gd("TKR26110002", 3), "TKR26110002-3")
	la("tách mã đơn", (op.ma_phieu_cua_gd("TKR26110002-3"), op.ma_phieu_cua_gd("DNTT261100002-1")), ("TKR26110002", "DNTT261100002"))
	la("lần tiếp theo", op.lan_tiep([{"ma": "TKR26110002-1"}, {"ma": "TKR26110002-4"}]), 5)
	la("khoá chống trùng", od.khoa_phieu_thu("TKR26110002-2"), "onepay:TKR26110002-2")


@ca("v637 tiền thẻ là của Sales: phiếu thu mang quầy KHÔNG két, không bao giờ là quầy cửa hàng; qua đủ hàng rào phiếu đặt bánh")
def _quay():
	q = od.chon_quay(DIEM)
	la("quầy không két", q, "SALES")
	dung("không phải quầy cửa hàng nào", q not in [d.get("quay") for d in DIEM if d.get("quay")])
	p = tkr.phieu_thu("SO-2", "KH-1", 7560000, 3780000, q, op.PT, "2026-11-14", None, od.ghi_chu_phieu("TKR26110002", {"ma": "TKR26110002-1", "ma_onepay": "99"}))
	la("phương thức, quầy, phiếu đặt", (p["mode_of_payment"], p["vgb_quay"], p["vgb_phieu_dat"]), ("OnePay", "SALES", "SO-2"))
	dung("qua hàng rào phiếu đặt bánh", not tkr.loi_phieu(p))
	dung("diễn giải nói rõ không vào két", "không vào két quầy" in p["remarks"])
	la("chốt ca của quầy TCV không thấy phiếu này", db.tong_ung_truoc([]), db.tong_ung_truoc([]))


class _Db:
	"""frappe.db giả: một phiếu đặt SO-2 với ô nhật ký thẻ."""

	def __init__(self, nk=None, docstatus=1):
		self.o = {"vgb_onepay_gd": json.dumps(nk or [], ensure_ascii=False), "customer": "KH-1", "name": "SO-2"}
		self.commit_n = 0
		self.docstatus = docstatus

	def get_value(self, dt, ten, o=None, for_update=False, **kw):
		if isinstance(ten, dict):
			# Như cơ sở dữ liệu thật: tôn trọng bộ lọc docstatus của câu hỏi.
			ds = ten.get("docstatus")
			if ds and ds[0] == "<" and not self.docstatus < ds[1]:
				return None
			if ds and ds[0] == "in" and self.docstatus not in ds[1]:
				return None
			return "SO-2" if ten.get("vgb_tkr_ma") == "TKR26110002" else None
		return self.o.get(o)

	def set_value(self, dt, ten, o, v=None, **kw):
		self.o[o] = v

	def commit(self):
		self.commit_n += 1


def _tt(con=3780000, trang_thai="da_coc"):
	return {"ma": "TKR26110002", "khach": "Nguyễn An", "tong": 7560000, "con_lai": con, "trang_thai": trang_thai}


def _vat(dbg, lap, tt=None, phieu=None):
	"""Thay tầng Frappe. `phieu`: danh sách phiếu thu đã ghi sổ trên sổ giả (đọc lại sổ)."""
	phieu = phieu if phieu is not None else []
	so = types.SimpleNamespace(add_comment=lambda *a, **k: None)

	def lap_gia(ten, t, kq, so_tien):
		lap.append((ten, kq["ma"], so_tien))
		phieu.append({"name": "PE-%d" % len(phieu), "paid_amount": so_tien, "ref": od.khoa_phieu_thu(kq["ma"])})
		return "PE-%d" % (len(phieu) - 1)

	def doc_so(ten, ma):
		ds = [p for p in phieu if p["ref"] == od.khoa_phieu_thu(ma)]
		return [p["name"] for p in ds], sum(p["paid_amount"] for p in ds)
	return [patch.object(_fr, "db", dbg), patch.object(_fr, "get_doc", lambda *a, **k: so),
		patch.object(op, "cau_hinh", return_value=dict(C)), patch.object(od, "_khoa", lambda ten: None),
		patch.object(od, "_tom_tat", lambda ten, khoa=False: tt or _tt()), patch.object(od, "_lap_phieu", lap_gia),
		patch.object(od, "_phieu_cua_gd", doc_so), patch.object(kz, "bao", lambda *a, **k: None)]


def _chay(vat, ham):
	with contextlib.ExitStack() as st:
		for v in vat:
			st.enter_context(v)
		return ham()


@ca("v637 IPN của đơn đặt trước đi đúng đường đơn (không lọt sang phiếu công nợ); thành công thì lập ĐÚNG MỘT phiếu thu, IPN lặp và trang về không lập thêm")
def _ghi_mot_lan():
	dbg = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}])
	lap = []
	vat = _vat(dbg, lap)
	r1 = _chay(vat, lambda: op.ghi_nhan(_kq(), "ipn"))
	r2 = _chay(vat, lambda: op.ghi_nhan(_kq(), "ipn"))
	r3 = _chay(vat, lambda: op.ghi_nhan(_kq(), "trang_ve"))
	la("một phiếu đúng đơn, đúng số", lap, [("SO-2", "TKR26110002-1", 3780000.0)])
	la("lần đầu ghi, lần sau đã ghi rồi", [r1.get("ly_do"), r2.get("ly_do"), r3.get("ly_do")], ["", "da_ghi_roi", "da_ghi_roi"])
	gd = json.loads(dbg.o["vgb_onepay_gd"])[0]
	la("nhật ký", (gd["trang_thai"], gd["so_ghi"], gd["phieu_thu"], gd["nguon"]), ("da_ghi", 3780000.0, ["PE-0"], "ipn"))


@ca("v637 đơn đặt trước: chữ ký sai, thất bại, lệch số tiền, giao dịch lạ thì không lập phiếu; thất bại thì nhật ký ghi that_bai")
def _khong_ghi():
	lap = []
	dbg = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}])
	vat = _vat(dbg, lap)
	gia = _kq()
	gia["vpc_Amount"] = op.so_tien_vpc(1)
	la("chữ ký sai", _chay(vat, lambda: op.ghi_nhan(gia, "ipn"))["ly_do"], "chu_ky_sai")
	la("thất bại", _chay(vat, lambda: op.ghi_nhan(_kq(ma_kq="99"), "ipn"))["ly_do"], "khong_thanh_cong")
	la("nhật ký that_bai", json.loads(dbg.o["vgb_onepay_gd"])[0]["trang_thai"], "that_bai")
	dbg2 = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}])
	vat2 = _vat(dbg2, lap)
	la("lệch số tiền", _chay(vat2, lambda: op.ghi_nhan(_kq(tien=1000000), "ipn"))["ly_do"], "lech_so_tien")
	la("giao dịch lạ", _chay(vat2, lambda: op.ghi_nhan(_kq(ma="TKR26110002-7"), "ipn"))["ly_do"], "gd_la")
	la("đơn không có", _chay(vat2, lambda: op.ghi_nhan(_kq(ma="TKR26119999-1"), "ipn"))["ly_do"], "gd_la")
	la("không lập phiếu nào", lap, [])


@ca("v637 đơn đặt trước: lượt trước đã lập phiếu thu rồi lỗi trước khi ghi nhật ký thì lượt sau đọc lại sổ, không lập lần hai; đơn đã thu ở chỗ khác thì chỉ ghi phần còn lại")
def _doc_lai_so():
	lap = []
	so_cu = [{"name": "PE-9", "paid_amount": 3780000.0, "ref": od.khoa_phieu_thu("TKR26110002-1")}]
	dbg = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}])
	r = _chay(_vat(dbg, lap, phieu=so_cu), lambda: op.ghi_nhan(_kq(), "ipn"))
	la("không lập thêm", lap, [])
	la("nhận phiếu cũ", (r["phieu_thu"], json.loads(dbg.o["vgb_onepay_gd"])[0]["trang_thai"]), (["PE-9"], "da_ghi"))
	dbg2 = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}])
	_chay(_vat(dbg2, lap, tt=_tt(con=1000000)), lambda: op.ghi_nhan(_kq(), "ipn"))
	la("chỉ ghi phần còn lại", lap, [("SO-2", "TKR26110002-1", 1000000.0)])
	la("ghi phần dư", json.loads(dbg2.o["vgb_onepay_gd"])[0]["du"], 2780000.0)


@ca("v637 khách bấm trả thẻ: giao dịch mới đúng SỐ CÒN PHẢI THU đọc ở máy chủ, ghi nhật ký trên phiếu đặt; đơn huỷ, đã đủ, khoá sai thì chặn")
def _tao_gd():
	dbg = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "that_bai"}])
	vat = _vat(dbg, []) + [patch.object(od, "tim_don", lambda ma, k: "SO-2" if k == "a" * 16 else None),
		patch.object(od, "link_don", lambda ma: "https://vagabond.test/tra-the/%s?k=%s" % (ma, "a" * 16)),
		patch.object(op, "dung_duoc", return_value=True)]
	kq = _chay(vat, lambda: op.tao_gd("TKR26110002", "a" * 16))
	nk = json.loads(dbg.o["vgb_onepay_gd"])
	la("giao dịch lần 2 đúng số", (nk[-1]["ma"], nk[-1]["so_tien"], nk[-1]["trang_thai"]), ("TKR26110002-2", 3780000, "cho"))
	dung("chuyển sang cổng OnePay với đúng mã", "vpc_MerchTxnRef=TKR26110002-2" in kq["url"] and "vpc_Amount=378000000" in kq["url"])
	nem("khoá sai", lambda: _chay(vat, lambda: op.tao_gd("TKR26110002", "b" * 16)))
	for tt in (_tt(trang_thai="da_huy"), _tt(con=0, trang_thai="du_tien"), _tt(con=5000)):
		vat2 = _vat(_Db(), [], tt=tt) + vat[-3:]
		nem("chặn %s" % tt["trang_thai"], lambda: _chay(vat2, lambda: op.tao_gd("TKR26110002", "a" * 16)))


@ca("v637 trang khách của đơn đặt trước: đúng số còn phải thu, đơn huỷ thì báo huỷ, không có khối chuyển khoản công nợ")
def _trang():
	vat = [patch.object(od, "tim_don", lambda ma, k: "SO-2"), patch.object(op, "dung_duoc", return_value=True),
		patch.object(od, "_tom_tat", lambda ten, khoa=False: _tt())]
	p = _chay(vat, lambda: op.thong_tin_trang("TKR26110002", "a" * 16))
	la("trang", (p["ma_phieu"], p["con"], p["huy"], p["dung_duoc"]), ("TKR26110002", 3780000.0, False, True))
	la("cách trả", op.cach_tra(p), {"da_du": False, "tra_the": True, "con_nho": False})
	vat[-1] = patch.object(od, "_tom_tat", lambda ten, khoa=False: _tt(con=0, trang_thai="da_huy"))
	la("đơn huỷ", _chay(vat, lambda: op.thong_tin_trang("TKR26110002", "a" * 16))["huy"], True)


@ca("v637 lập phiếu thu thẻ chạy thật: phương thức và tài khoản OnePay, quầy không két, khoá chống trùng; biên nhận đính TRƯỚC khi ghi sổ")
def _lap_that():
	vet = []

	class _Pe(dict):
		name = "PE-NEW"
		flags = types.SimpleNamespace()

		def __getattr__(self, k):
			return self.get(k)

		def setup_party_account_field(self):
			pass

		def set_missing_values(self):
			pass

		def insert(self, **k):
			vet.append(("insert", dict(self)))

		def submit(self):
			vet.append(("submit",))

	class _Tep(dict):
		def insert(self, **k):
			vet.append(("dinh", self["attached_to_name"], self["file_name"]))

	def get_doc(d, *a, **k):
		d = dict(d)
		return _Tep(d) if d.get("doctype") == "File" else _Pe(d)

	@contextlib.contextmanager
	def nang():
		yield "goc"

	from vagabond import thu_tien as tt
	vat = [patch.object(_fr, "get_doc", get_doc), patch.object(_fr, "db", _Db()),
		patch.object(tkr, "_cong_ty", lambda: "Vagabond"), patch.object(tkr, "_ds_diem", lambda: DIEM),
		patch.object(tkr, "_hom_nay", lambda: "2026-11-14"),
		patch.object(tt, "tk_tien_thu", lambda cty, pt: ("11211 - MB" if pt == "OnePay" else "", None)),
		patch.object(tt, "nang_quyen_lap_phieu", nang), patch.object(tt, "_giu_chu", lambda pe, goc: vet.append(("giu",)))]
	kq = op.doc_ket_qua(_kq(), KHOA)
	ten = _chay(vat, lambda: od._lap_phieu("SO-2", _tt(), kq, 3780000))
	la("tên", ten, "PE-NEW")
	la("thứ tự: lập nháp, đính biên nhận, ghi sổ", [v[0] for v in vet], ["insert", "dinh", "submit", "giu"])
	p = vet[0][1]
	la("các ô", (p["mode_of_payment"], p["paid_to"], p["vgb_quay"], p["vgb_phieu_dat"], p["reference_no"], p["paid_amount"]),
		("OnePay", "11211 - MB", "SALES", "SO-2", "onepay:TKR26110002-1", 3780000))
	la("biên nhận", vet[1][1:], ("PE-NEW", "onepay-TKR26110002-1.html"))
	vat[5] = patch.object(tt, "tk_tien_thu", lambda cty, pt: ("", None))
	nem("chưa khai tài khoản OnePay thì ném, không lập", lambda: _chay(vat, lambda: od._lap_phieu("SO-2", _tt(), kq, 3780000)))


@ca("v637 lượt quét 15 phút đi cả phiếu đặt có giao dịch chờ, cho hết hạn trên đúng phiếu đặt")
def _quet():
	from datetime import datetime

	bay_gio = datetime(2026, 11, 14, 12, 0, 0)
	kho = {("Sales Order", "SO-2"): json.dumps([{"ma": "TKR26110002-1", "so_tien": 1, "tao_luc": "2026-11-14 11:00:00", "trang_thai": "cho"},
		{"ma": "TKR26110002-2", "so_tien": 1, "tao_luc": "2026-11-01 11:00:00", "trang_thai": "cho"}])}
	loc = []

	def get_all(dt, filters=None, limit_page_length=0, **kw):
		loc.append((dt, sorted((filters or {}).keys())))
		return [t for (d, t), v in kho.items() if d == dt and '"cho"' in v and not (filters or {}).get("name", [0, ""])[1]]

	class _D:
		def get_value(self, dt, ten, o, for_update=False):
			return kho.get((dt, ten))

		def set_value(self, dt, ten, o, v, **k):
			kho[(dt, ten)] = v

		def commit(self):
			pass

		def rollback(self):
			pass

	gia = types.SimpleNamespace(get_all=get_all, db=_D(), log_error=lambda *a, **k: None, get_traceback=lambda: "",
		utils=types.SimpleNamespace(now_datetime=lambda: bay_gio))
	hoi = []
	with patch.object(op, "frappe", gia), patch.object(op, "cau_hinh", return_value=dict(C)), \
			patch.object(op, "tra_cuu", side_effect=lambda ma: hoi.append(ma) or {"vpc_DRExists": "N"}):
		op.quet()
	la("đi cả hai loại", [x[0] for x in loc], ["Vagabond Cong No", "Sales Order"])
	la("lọc phiếu đặt theo ô nhật ký thẻ, đã ghi sổ", loc[1][1], ["docstatus", "name", "vgb_onepay_gd"])
	la("hỏi giao dịch mới", hoi, ["TKR26110002-1"])
	la("giao dịch quá hạn hết hạn trên phiếu đặt", [g["trang_thai"] for g in json.loads(kho[("Sales Order", "SO-2")])], ["cho", "het_han"])
	# Phiếu đặt đọc hỏng (ô nhật ký chưa có vì chưa migrate) thì phiếu công nợ vẫn được quét, có Error Log.
	loi = []
	kho2 = {("Vagabond Cong No", "CN-1"): json.dumps([{"ma": "DNTT261100001-1", "so_tien": 1, "tao_luc": "2026-11-14 11:00:00", "trang_thai": "cho"}])}

	def get_all2(dt, filters=None, limit_page_length=0, **kw):
		if dt == "Sales Order":
			raise Exception("Unknown column vgb_onepay_gd")
		return [t for (d, t), v in kho2.items() if d == dt and not (filters or {}).get("name", [0, ""])[1]]

	class _D2(_D):
		def get_value(self, dt, ten, o, for_update=False):
			return kho2.get((dt, ten))

	gia2 = types.SimpleNamespace(get_all=get_all2, db=_D2(), log_error=lambda *a, **k: loi.append(a), get_traceback=lambda: "tb",
		utils=types.SimpleNamespace(now_datetime=lambda: bay_gio))
	hoi2 = []
	with patch.object(op, "frappe", gia2), patch.object(op, "cau_hinh", return_value=dict(C)), \
			patch.object(op, "tra_cuu", side_effect=lambda ma: hoi2.append(ma) or {"vpc_DRExists": "N"}):
		op.quet()
	la("phiếu công nợ vẫn được quét", hoi2, ["DNTT261100001-1"])
	dung("có Error Log cho phần phiếu đặt", any("Sales Order" in str(a) for a in loi))


@ca("v637 nối: ô nhật ký thẻ trên phiếu đặt có neo, ẩn, không chép; cửa màn quầy đăng ký cửa ngõ; màn chi tiết đơn báo OnePay bật")
def _noi():
	o = {f["fieldname"]: f for f in tkr.TRUONG_MOI["Sales Order"]}
	f = o.get("vgb_onepay_gd") or {}
	la("ô nhật ký", (f.get("fieldtype"), f.get("insert_after"), f.get("hidden"), f.get("no_copy"), f.get("read_only")),
		("Long Text", "vgb_tkr_lan", 1, 1, 1))
	from vagabond.khung.kiem_thu import thu_cua_ngo as cn
	la("cửa ngõ", sorted(cn.CUA_NGO.get("onepay_dat.py", [])), ["con_lai", "ma_the"])


# ------------------------------------------------ Codex #538 vòng 1 (SHA cd0dc1c17)


@ca("v637 Codex #538: khách đang trả thẻ thì đơn bị huỷ, OnePay báo thành công sau: KHÔNG được coi là giao dịch lạ; nhật ký ghi đã nhận, toàn bộ tiền là tiền phải hoàn, báo kế toán (trước: gd_la, tiền mất dấu)")
def _codex_huy_giua_chung():
	dbg = _Db([{"ma": "TKR26110002-1", "so_tien": 3780000, "trang_thai": "cho"}], docstatus=2)
	lap, tin = [], []
	vat = _vat(dbg, lap, tt=_tt(con=7560000, trang_thai="da_huy")) + [patch.object(kz, "bao", lambda *a, **k: tin.append((a, k)))]
	r = _chay(vat, lambda: op.ghi_nhan(_kq(), "ipn"))
	la("không phải giao dịch lạ", r["ly_do"], "du")
	la("không lập phiếu thu cho đơn đã huỷ", lap, [])
	gd = json.loads(dbg.o["vgb_onepay_gd"])[0]
	la("nhật ký: đã nhận, ghi 0, hoàn toàn bộ", (gd["trang_thai"], gd["so_ghi"], gd["du"]), ("da_ghi", 0.0, 3780000.0))
	la("báo kế toán một tin", len(tin), 1)
	dung("tin nói rõ phải hoàn", "hoàn" in json.dumps(tin[0][0], ensure_ascii=False) and "TKR26110002" in json.dumps(tin[0][0], ensure_ascii=False))
	r2 = _chay(vat, lambda: op.ghi_nhan(_kq(), "ipn"))
	la("IPN lặp không báo lại", (r2["ly_do"], len(tin)), ("da_ghi_roi", 1))


@ca("v637 Codex #538: lượt quét 15 phút hỏi cả đơn đã huỷ còn giao dịch chờ (khách trả rồi mới huỷ)")
def _codex_quet_don_huy():
	loc = []
	gia = types.SimpleNamespace(get_all=lambda dt, filters=None, **k: loc.append((dt, filters)) or [], db=types.SimpleNamespace(rollback=lambda: None),
		log_error=lambda *a, **k: None, get_traceback=lambda: "", utils=types.SimpleNamespace(now_datetime=lambda: __import__("datetime").datetime(2026, 11, 14, 12)))
	with patch.object(op, "frappe", gia), patch.object(op, "cau_hinh", return_value=dict(C)):
		op.quet()
	f = [f for d, f in loc if d == "Sales Order"][0]
	la("lọc phiếu đặt gồm cả đã huỷ", f.get("docstatus"), ["in", [1, 2]])
