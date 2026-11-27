"""v697: trần số bánh mỗi ngày nhận cho hàng mùa vụ trên web và nút "Ngưng nhận
ngày này" (anh Việt chốt 27/11/2026: theo bảng Kiểm bánh theo mùa, đếm mọi kênh).

Chốt:
- số đã nhận của một ngày = bảng Đơn theo ngày (chốt + chờ chốt + kênh khác) cộng
  đơn web tạo sau lần đồng bộ cuối; đơn web chỉ đọc đơn có nhắc mã của mùa;
- đúng bằng trần thì nhận, vượt thì từ chối; trần 0 là không giới hạn; mã ngoài mùa
  không xét; ngày đã ngưng từ chối mọi đơn có hàng của mùa;
- trang khách (thuan.js ngayMuaDay) và máy chủ (mua_vu_web.xet_ngay) chạy CÙNG bộ số;
- cửa nhận đơn xét dưới khoá ngày, sau phép tìm trùng, đọc lại sau khi kết thúc
  giao dịch đọc.
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


@ca("v697 cửa nhận đơn: hàng của mùa xét trần ngày dưới khoá ngày, sau phép tìm trùng, đọc lại sau khi kết thúc giao dịch; nút Ngưng nhận khoá dòng mùa trước khi đọc")
def _():
	src = (GOC / "vagabond/don_hang.py").read_text(encoding="utf-8")
	tao = src[src.index("def tao_don("):]
	vt = tao.index("(mua_vu_web.khoa_ngay(ngay) if co_mua_ngay else contextlib.nullcontext()):")
	dung("khoá ngày nằm trong cùng khối khoá ghi", vt > tao.index("with don_web.khoa_ghi(khoa)"))
	sau = tao[vt:]
	dung("xét sau phép tìm trùng, sau commit đọc", sau.index("tim_trung(khoa)") < sau.index("frappe.db.commit()") < sau.index("xet_ngay_that(hang_goc, ngay, mua_web)"))
	dung("xét trước khi ghi bản ghi", sau.index("xet_ngay_that(") < sau.index("don_web.tao_ban_ghi("))
	mv = (GOC / "vagabond/mua_vu.py").read_text(encoding="utf-8")
	ng = mv[mv.index("def ngung_ngay("):]
	ng = ng[:ng.index("\ndef ")]
	dung("kiểm quyền", "_kiem_quyen()" in ng)
	dung("khoá dòng mùa rồi mới đọc danh sách ngày", ng.index("for update") < ng.index("frappe.get_doc(DT, mua)") < ng.index("doc_ngay_ngung("))
	dung("trang khách nhận trần ngày từ hang_theo_mua", '"han_ngay": han_ngay' in mv)
	cua = (GOC / "vagabond/khung/kiem_thu/thu_cua_ngo.py").read_text(encoding="utf-8")
	dung("ngung_ngay có trong danh sách cửa", '"ngung_ngay"' in cua)


@ca("v697 màn Kiểm bánh theo mùa, Lịch tháng: bấm thật nút Ngưng nhận ngày này bằng node (hanh_vi/mua_vu_ngung_697.js)")
def _():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/mua_vu_ngung_697.js")], capture_output=True, text=True, timeout=180)
	la("mã trả về", (r.returncode, (r.stdout + r.stderr)[-800:] if r.returncode else ""), (0, ""))
