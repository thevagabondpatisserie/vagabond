"""v697: trần số bánh mỗi ngày nhận cho hàng mùa vụ trên web và nút "Ngưng nhận
ngày này" (anh Việt chốt 27/11/2026: theo bảng Kiểm bánh theo mùa, đếm mọi kênh).

Chốt:
- số đã nhận của một ngày = bảng Đơn theo ngày (chốt + chờ chốt + kênh khác) cộng
  đơn web tạo sau lần đồng bộ cuối; đơn web chỉ đọc đơn có nhắc mã của mùa;
- đúng bằng trần thì nhận, vượt thì từ chối; trần 0 là không giới hạn; mã ngoài mùa
  không xét; ngày đã ngưng từ chối mọi đơn có hàng của mùa;
- trang khách (thuan.js ngayMuaDay) và máy chủ (mua_vu_web.xet_ngay) chạy CÙNG bộ số;
- cửa nhận đơn (tao_don chạy thật trên môi trường giả của bộ #367) xét dưới khoá
  ngày, sau phép tìm trùng, đọc lại sau khi kết thúc giao dịch đọc; nút Ngưng nhận
  (ngung_ngay chạy thật) khoá dòng mùa rồi mới đọc.
Dữ liệu trong ca là GIẢ.
"""
import json
import subprocess
import types
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]

TRAN = {"GIA-P1": 3, "GIA-B1": 2, "GIA-K0": 0}
DA = {("GIA-P1", "2026-12-23"): 2, ("GIA-B1", "2026-12-23"): 2, ("GIA-P1", "2026-12-24"): 3}
NGUNG = ["2026-12-25"]
MA_MUA = ["GIA-P1", "GIA-P2", "GIA-B1", "GIA-K0"]
# (giỏ, ngày, nhận được?) chạy cả hai phía.
BO = [
	({"GIA-P1": 1}, "2026-12-23", True),       # 2 + 1 = 3, đúng bằng trần
	({"GIA-P1": 2}, "2026-12-23", False),      # 2 + 2 > 3
	({"GIA-B1": 1}, "2026-12-23", False),      # Bûche đã đủ 2
	({"GIA-P1": 1}, "2026-12-24", False),      # ngày 24 đã đủ
	({"GIA-P2": 9}, "2026-12-24", True),       # Mini không đặt trần
	({"GIA-K0": 50}, "2026-12-23", True),      # trần 0 là không giới hạn
	({"GIA-P2": 1}, "2026-12-25", False),      # ngày đã ngưng
	({"GIA-THUONG": 1}, "2026-12-25", True),   # giỏ không có hàng của mùa
	({"GIA-P1": 3}, "2026-12-26", True),       # ngày chưa có đơn: tới trần
]


def _w():
	from vagabond import mua_vu_web

	return mua_vu_web


@ca("v697 trần ngày: đọc ngày ngưng, cộng bảng Đơn theo ngày với đơn web chưa vào bảng")
def _():
	w = _w()
	la("ngày ngưng: gọn, bỏ dòng lạ, không trùng", w.doc_ngay_ngung("2026-12-25\n\nla\n2026-12-24, 2026-12-25"), ["2026-12-24", "2026-12-25"])
	la("trống", w.doc_ngay_ngung(None), [])
	da = w.da_nhan_theo_ngay(
		[{"ma": "GIA-P1", "ngay": "2026-12-23", "so": 2}, {"ma": "GIA-P1", "ngay": "2026-12-23 00:00:00", "so": 1}, {"ma": "GIA-B1", "ngay": "2026-12-24", "so": -3}],
		[{"ngay": "2026-12-23 14:00:00", "mon": [{"ma": "GIA-P1", "sl": 2}, {"ma": "GIA-B1", "sl": "x"}]}])
	la("cộng hai nguồn, số âm không trừ", da, {("GIA-P1", "2026-12-23"): 5, ("GIA-B1", "2026-12-24"): 0})


@ca("v697 trần ngày: máy chủ và trang khách cùng một bộ số (đúng bằng trần nhận, vượt từ chối, trần 0 không giới hạn, ngày ngưng, giỏ thường)")
def _():
	w = _w()
	may = [w.xet_ngay([{"variation_id": m, "quantity": sl} for m, sl in g.items()], ng, TRAN, DA, NGUNG, MA_MUA) is None for g, ng, _ in BO]
	la("máy chủ", may, [x[2] for x in BO])
	ma = """import {ngayMuaDay} from './vagabond/public/web_vue/kho/thuan.js';
const BO = %s, hn = %s, MUA = %s;
console.log(JSON.stringify(BO.map(([g, ng]) => ngayMuaDay(Object.entries(g).map(([id, qty]) => (MUA.includes(id) ? {id, qty, mua: 1} : {id, qty, nguon: 'order'})), ng, hn) === null)));""" % (
		json.dumps([[g, ng] for g, ng, _ in BO]),
		json.dumps(w.han_ngay_cho_web(TRAN, DA, NGUNG, "2026-12-01")), json.dumps(MA_MUA))
	r = subprocess.run(["node", "--input-type=module", "-e", ma], cwd=GOC, capture_output=True, text=True, timeout=60)
	la("node chạy được: " + r.stderr[-400:], r.returncode, 0)
	la("trang khách", json.loads(r.stdout or "[]"), [x[2] for x in BO])
	kq = w.xet_ngay([{"variation_id": "GIA-P1", "quantity": 2}], "2026-12-23", TRAN, DA, NGUNG, MA_MUA, {"GIA-P1": "Panettone Thử"})
	la("cùng lý do với lịch để trang khách mở lại lịch", kq["ly_do"], "ngay_mua_vu")
	dung("câu nói còn mấy bánh và tên bánh: " + kq["nhac"][0], "Panettone Thử ngày 23/12/2026 chỉ còn nhận 1 bánh" in kq["nhac"][0])
	dung("câu ngày ngưng", "25/12/2026" in w.xet_ngay([{"variation_id": "GIA-P2", "quantity": 1}], "2026-12-25", TRAN, DA, NGUNG, MA_MUA)["nhac"][0])
	hn = w.han_ngay_cho_web(TRAN, DA, NGUNG + ["2026-11-01"], "2026-12-24")
	la("phần gửi trang khách: chỉ mã có trần, từ hôm nay", hn, {"tran": {"GIA-P1": 3, "GIA-B1": 2}, "da": {"GIA-P1": {"2026-12-24": 3}}, "ngung": ["2026-12-25"]})


@ca("v697 trần ngày: đơn web sau lần đồng bộ chỉ đọc đơn có nhắc mã của mùa, chưa huỷ, trong khoảng mùa; bảng Đơn theo ngày đếm cả kênh khác")
def _():
	import datetime
	import sys

	w = _w()
	goi = []

	def get_all(dt, filters=None, or_filters=None, fields=None, **k):
		goi.append((dt, filters, or_filters))
		return [types.SimpleNamespace(ngay_nhan=datetime.datetime(2026, 12, 23, 14), snapshot=json.dumps({"mon": [{"ma": "GIA-P1", "sl": 2}, {"ma": "KHAC", "sl": 9}]})),
			types.SimpleNamespace(ngay_nhan=None, snapshot="{}"), types.SimpleNamespace(ngay_nhan=datetime.datetime(2026, 12, 24), snapshot="hỏng")]

	fr = types.SimpleNamespace(get_all=get_all, utils=types.SimpleNamespace(
		add_to_date=lambda d, minutes=0: d + datetime.timedelta(minutes=minutes), cint=lambda v: int(v or 0)))
	cu = {k: sys.modules.get(k) for k in ("frappe", "frappe.utils")}
	sys.modules["frappe"] = fr
	try:
		dong = [types.SimpleNamespace(ma_hang="GIA-P1", tran_ngay=3, ten_banh="P1"), types.SimpleNamespace(ma_hang="GIA-P2", tran_ngay=0, ten_banh="P2")]
		lich = [types.SimpleNamespace(ma_hang="GIA-P1", ngay=datetime.date(2026, 12, 23), so_luong=1, cho_chot=1, don_khac=1),
			types.SimpleNamespace(ma_hang="GIA-P2", ngay=datetime.date(2026, 12, 23), so_luong=9, cho_chot=0, don_khac=0)]
		v = {"dong_bo_luc": datetime.datetime(2026, 12, 1, 10, 0), "tu_ngay": "2026-11-24", "den_ngay": "2026-12-31",
			"lich": lich, "ngay_ngung_web": "2026-12-25"}
		doc = types.SimpleNamespace(dong=dong, get=v.get, **v)
		sys.modules["frappe.utils"] = fr.utils
		tran, da, ngung, ten = w.doc_han_ngay(doc)
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v
	la("trần chỉ mã có số", tran, {"GIA-P1": 3})
	la("bảng (chốt + chờ + kênh khác) cộng đơn web; mã khác, đơn hỏng bỏ", da, {("GIA-P1", "2026-12-23"): 5})
	la("ngày ngưng", ngung, ["2026-12-25"])
	dt, loc, hoac = goi[0]
	la("đọc bảng đơn web", dt, "Vagabond Don Web")
	la("đơn chưa huỷ, lùi 10 phút trước lần đồng bộ, trong khoảng mùa",
		(loc["trang_thai"], loc["creation"], loc["ngay_nhan"]),
		(["!=", "Da huy"], [">", datetime.datetime(2026, 12, 1, 9, 50)], ["between", ["2026-11-24 00:00:00", "2026-12-31 23:59:59"]]))
	la("chỉ đơn có nhắc mã có trần (LIKE)", hoac, [["snapshot", "like", '%"GIA-P1"%']])


def _mua_gia(lich, ngung=""):
	"""Bản ghi Mùa vụ GIẢ: GIA-P1 trần 3, GIA-P2 không trần; bảng Đơn theo ngày `lich`."""
	dong = [types.SimpleNamespace(ma_hang="GIA-P1", tran_ngay=3, ten_banh="Panettone Thử", nhom_web="", loai_web="", get=lambda k: None),
		types.SimpleNamespace(ma_hang="GIA-P2", tran_ngay=0, ten_banh="Panettone Mini Thử", nhom_web="", loai_web="", get=lambda k: None)]
	v = {"name": "MUA-GIA-1", "dong_bo_luc": None, "tu_ngay": "2026-11-24", "den_ngay": "2026-12-31", "lich": [
		types.SimpleNamespace(ma_hang=m, ngay=n, so_luong=s, cho_chot=0, don_khac=0) for m, n, s in lich],
		"ngay_ngung_web": ngung, "sot_web": [], "panettone_thu": "", "panettone_truoc": "", "buche_thu": "", "buche_truoc": "", "tinh_trang": "Dang ban"}
	return types.SimpleNamespace(dong=dong, get=v.get, **v)


def _tao_mua(hang, dau, sau=None, ngay="2026-12-23T10:00:00", ton=None):
	"""Chạy don_hang.tao_don THẬT (môi trường giả của bộ ca #367). `dau`: Mùa vụ lúc
	đầu yêu cầu; `sau`: Mùa vụ đọc lại dưới khoá ngày (khách khác vừa đặt, Sales vừa
	bấm Ngưng nhận). `ton`: {tên: hàm} thay phần đọc site của ton_don_web để chạy
	luật ba ngày THẬT (mặc định bỏ qua luật đó). Trả (kết quả, vết)."""
	import contextlib
	import sys
	import unittest.mock as um

	from vagabond import giu_ton_web, mua_vu, mua_vu_web, ton_don_web
	from vagabond.khung.kiem_thu import thu_don_web_367 as t367

	vet, tao_don = t367._moi_truong_tao_don(lambda v: t367._Tra(200, {"data": {"id": "91500"}}))
	khoa = []

	@contextlib.contextmanager
	def khoa_ngay(ng):
		khoa.append(ng)
		vet.su.append("khoa_ngay")
		yield

	def get_doc(dt, ten=None):
		vet.su.append("doc_lai")
		return sau or dau
	fr = sys.modules["frappe"]
	don = t367._don(ngay_nhan=ngay)
	don["items"] = hang
	vo_ton = [um.patch.object(ton_don_web, k, f, create=True) for k, f in (ton or {"kiem": lambda h, n: []}).items()]
	with contextlib.ExitStack() as st:
		for x in vo_ton:
			st.enter_context(x)
		r, khoa = _chay_tao(tao_don, don, dau, mua_vu, mua_vu_web, giu_ton_web, khoa_ngay, get_doc, fr, um), khoa
	vet.khoa_ngay = khoa
	return r, vet


def _chay_tao(tao_don, don, dau, mua_vu, mua_vu_web, giu_ton_web, khoa_ngay, get_doc, fr, um):
	with um.patch.object(mua_vu, "mua_cho_web", lambda: dau), um.patch.object(mua_vu, "kiem_han_muc", lambda *a, **k: []), \
			um.patch.object(mua_vu_web, "khoa_ngay", khoa_ngay), \
			um.patch.object(fr, "get_doc", get_doc, create=True), um.patch.object(fr, "get_all", lambda *a, **k: [], create=True), \
			um.patch.object(giu_ton_web, "kiem_va_giu", lambda h, n: ([], None), create=True), \
			um.patch.object(giu_ton_web, "kiem_va_giu_refill", lambda h, n: ([], None), create=True):
		return tao_don(json.dumps(don))


@ca("v697 cửa nhận đơn THẬT (tao_don): vượt trần, ngày đã ngưng bị từ chối và không ghi đơn; đúng bằng trần thì ghi; đọc lại Mùa vụ dưới khoá ngày sau khi kết thúc giao dịch đọc")
def _():
	p1 = lambda sl: [{"variation_id": "GIA-P1", "quantity": sl}]  # noqa: E731
	r, vet = _tao_mua(p1(2), _mua_gia([("GIA-P1", "2026-12-23", 2)]))
	la("2 đã nhận + 2 vượt trần 3: từ chối", r.get("ly_do"), "ngay_mua_vu")
	dung("câu báo còn 1 bánh: " + str(r.get("nhac")), "chỉ còn nhận 1 bánh" in (r.get("nhac") or [""])[0])
	dung("không ghi đơn, không gọi Pancake", "ghi" not in vet.su and "post" not in vet.su)
	r, vet = _tao_mua([{"variation_id": "GIA-P2", "quantity": 1}], _mua_gia([], ngung="2026-12-23"))
	la("ngày đã ngưng: size không đặt trần cũng bị từ chối", (r.get("ly_do"), "ghi" in vet.su), ("ngay_mua_vu", False))
	r, vet = _tao_mua(p1(1), _mua_gia([("GIA-P1", "2026-12-23", 2)]))
	la("2 đã nhận + 1 đúng bằng trần: ghi đơn", (r.get("ok"), "ghi" in vet.su), (1, True))
	la("khoá đúng ngày nhận", [str(x)[:10] for x in vet.khoa_ngay], ["2026-12-23"])
	su = vet.su
	dung("thứ tự: khoá ghi, khoá ngày, commit, đọc lại, ghi: " + str(su),
		su.index("khoa") < su.index("khoa_ngay") < su.index("commit") < su.index("doc_lai") < su.index("ghi"))
	# Hai khách cùng lúc: lúc đầu yêu cầu bảng còn 1 chỗ, dưới khoá đọc lại thì khách
	# trước vừa lấy chỗ cuối (hoặc Sales vừa bấm Ngưng nhận).
	r, vet = _tao_mua(p1(1), _mua_gia([("GIA-P1", "2026-12-23", 2)]), sau=_mua_gia([("GIA-P1", "2026-12-23", 3)]))
	la("chỗ cuối vừa bị lấy: từ chối theo bản đọc dưới khoá", (r.get("ly_do"), "ghi" in vet.su), ("ngay_mua_vu", False))
	r, vet = _tao_mua(p1(1), _mua_gia([]), sau=_mua_gia([], ngung="2026-12-23"))
	la("vừa bấm Ngưng nhận: từ chối", (r.get("ly_do"), "ghi" in vet.su), ("ngay_mua_vu", False))
	r, vet = _tao_mua([{"variation_id": "GIA-THUONG", "quantity": 1}], _mua_gia([], ngung="2026-12-23"))
	la("giỏ không có hàng của mùa: không khoá ngày, ghi đơn", (r.get("ok"), vet.khoa_ngay), (1, []))


@ca("v697 nút Ngưng nhận ngày này THẬT (mua_vu.ngung_ngay): kiểm quyền, khoá dòng mùa rồi mới đọc, ngưng hai lần giữ một ngày, mở lại bỏ đúng ngày, ngoài mùa và mùa đã đóng bị chặn")
def _():
	import sys
	import unittest.mock as um

	from vagabond import mua_vu

	fr = sys.modules["frappe"]
	su, luu = [], {}
	doc = _mua_gia([], ngung="2026-12-24")

	def get_doc(dt, ten):
		su.append("doc")
		return doc

	def save():
		su.append("luu")
		luu["ngung"] = doc.ngay_ngung_web
	doc.save = save

	class Loi(Exception):
		pass

	def throw(m, *a, **k):
		raise Loi(m)
	db = types.SimpleNamespace(exists=lambda *a: True, sql=lambda q, *a, **k: su.append("khoa" if "for update" in q else "sql"),
		commit=lambda: su.append("commit"))
	# ban_hang kéo requests ở đầu tệp (CI không có): thay bằng mô đun giả chỉ có cửa kiểm quyền.
	ban_hang = types.SimpleNamespace(_kiem_quyen=lambda: su.append("quyen"))
	with um.patch.dict(sys.modules, {"vagabond.ban_hang": ban_hang}), um.patch.object(fr, "db", db, create=True), \
			um.patch.object(fr, "get_doc", get_doc, create=True), um.patch.object(fr, "throw", throw, create=True), \
			um.patch.object(mua_vu, "bang", lambda m: {"lich": {"ngung": luu.get("ngung")}}):
		mua_vu.ngung_ngay(mua="MUA-GIA-1", ngay="2026-12-23", ngung=1)
		la("thứ tự: quyền, khoá dòng, đọc, lưu, commit", su, ["quyen", "khoa", "doc", "luu", "commit"])
		la("thêm ngày, giữ ngày cũ", luu["ngung"], "2026-12-23\n2026-12-24")
		mua_vu.ngung_ngay(mua="MUA-GIA-1", ngay="2026-12-23", ngung=1)
		la("ngưng hai lần: vẫn một ngày", luu["ngung"], "2026-12-23\n2026-12-24")
		mua_vu.ngung_ngay(mua="MUA-GIA-1", ngay="2026-12-23", ngung=0)
		la("mở lại bỏ đúng ngày", luu["ngung"], "2026-12-24")
		loi = []
		for ngay in ("2027-01-05", "khong-phai-ngay"):
			try:
				mua_vu.ngung_ngay(mua="MUA-GIA-1", ngay=ngay, ngung=1)
			except Loi as e:
				loi.append(str(e))
		la("ngoài mùa và ngày hỏng bị chặn", len(loi), 2)
		doc.tinh_trang = "Da dong"
		try:
			mua_vu.ngung_ngay(mua="MUA-GIA-1", ngay="2026-12-23", ngung=1)
			dong = ""
		except Loi as e:
			dong = str(e)
		dung("mùa đã đóng bị chặn", "đã đóng" in dong)
	la("ngày ở cổng không đổi sau các lần bị chặn", luu["ngung"], "2026-12-24")
	cua = (GOC / "vagabond/khung/kiem_thu/thu_cua_ngo.py").read_text(encoding="utf-8")
	dung("ngung_ngay có trong danh sách cửa", '"ngung_ngay"' in cua)


@ca("v697 màn Kiểm bánh theo mùa, Lịch tháng: bấm thật nút Ngưng nhận ngày này bằng node (hanh_vi/mua_vu_ngung_697.js)")
def _():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/mua_vu_ngung_697.js")], capture_output=True, text=True, timeout=180)
	la("mã trả về", (r.returncode, (r.stdout + r.stderr)[-800:] if r.returncode else ""), (0, ""))
