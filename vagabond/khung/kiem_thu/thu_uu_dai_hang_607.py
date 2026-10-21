"""v607 (anh Việt 21/10/2026): ưu đãi giảm giá theo hạng thẻ chưa bao giờ được trừ.

Hạng AMBASSADOR 10%, FAMILY 20%, OWNER 100% khai ở Cài đặt hạng khách, màn
tính tiền hiện chip "giảm 10%", nhưng không chỗ nào tính số tiền đó vào hoá
đơn. Ca kiểm chạy THẬT `khuyen_mai.tinh` (một công thức cho xem trước và chốt),
`khuyen_mai.ghi_su_dung`, `diem_otp._km_giam_quay`, và chốt bằng AST hai chỗ
`ban_hang.tao_don_tay` truyền khách vừa chọn qua số điện thoại.

Không import ban_hang (kéo requests, CI tay không không có).
"""

import ast
import sys
import types
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import khuyen_mai as km

GOC = Path(__file__).resolve().parents[2]

HANG = {
	"AMBASSADOR": {"name": "AMBASSADOR", "ten_hang": "AMBASSADOR", "giam_gia": 10, "bat": 1},
	"FAMILY": {"name": "FAMILY", "ten_hang": "FAMILY", "giam_gia": 20, "bat": 1},
	"OWNER": {"name": "OWNER", "ten_hang": "OWNER", "giam_gia": 100, "bat": 1},
	"VOYAGER": {"name": "VOYAGER", "ten_hang": "VOYAGER", "giam_gia": 0, "bat": 1},
	"TAT": {"name": "TAT", "ten_hang": "TAT", "giam_gia": 15, "bat": 0},
}
KHACH = {"KL013432": "AMBASSADOR", "KL011129": "FAMILY", "KL0OWN": "OWNER", "KLVOY": "VOYAGER",
	"KLTAT": "TAT", "KLTHUONG": ""}


class _Doc(dict):
	__getattr__ = dict.get


def _get_value(dt, ten, truong=None, as_dict=False):
	if dt == "Customer" and truong == "vgb_hang":
		return KHACH.get(ten) or None
	if dt == "Vagabond Hang Khach":
		h = HANG.get(ten)
		return _Doc(h) if h else None
	return None


def _frappe(ctkm=None):
	ctkm = ctkm or {}
	return NS(
		db=NS(get_value=_get_value, exists=lambda dt, ten=None: dt == "Vagabond CTKM" and ten in ctkm),
		get_all=lambda *a, **k: [],
		throw=lambda m, *a, **k: (_ for _ in ()).throw(Exception(m)),
	)


def _tinh(khach, nguon="Tại chỗ", ctkm=None, items=None):
	ctkm = ctkm or {}
	items = items or [{"item_code": "BANH", "qty": 1, "rate": 700000}]
	with patch.object(km, "frappe", _frappe(ctkm)), \
			patch.object(km, "_doc_ctkm", lambda m: dict(ctkm[m], name=m)), \
			patch.object(km, "_hop_thoi_gian", lambda *a, **k: (True, "")), \
			patch.object(km, "_hop_kenh", lambda *a, **k: (True, "")), \
			patch.object(km, "_hop_han_muc", lambda *a, **k: (True, "")):
		return km.tinh(items, ctkm=list(ctkm), quay="TCV", nguon=nguon, khach=khach, sdt="0901234567")


def _hang_ap(kq):
	return [(a["ten"], a["giam"]) for a in kq["ap"] if a.get("loai") == "hang"]


@ca("v607 ưu đãi hạng: khách AMBASSADOR không chọn chương trình nào vẫn được giảm 10%")
def _():
	kq = _tinh("KL013432")
	la("dòng ưu đãi hạng", _hang_ap(kq), [("Ưu đãi hạng AMBASSADOR", 70000)])
	la("tổng giảm", kq["tong_giam"], 70000)
	la("còn lại", kq["con_lai"], 630000)
	la("FAMILY 20%", _tinh("KL011129")["tong_giam"], 140000)
	la("OWNER 100% thì bill về 0, không âm", (_tinh("KL0OWN")["tong_giam"], _tinh("KL0OWN")["con_lai"]), (700000, 0))


@ca("v607 ưu đãi hạng: không giảm cho khách lẻ, hạng tích điểm, hạng đang tắt, đơn sàn và đơn sỉ")
def _():
	for khach, nhan in ((None, "chưa chọn khách"), ("KLTHUONG", "khách chưa xếp hạng"),
			("KLVOY", "hạng chỉ tích điểm"), ("KLTAT", "hạng đang tắt")):
		la(nhan, _tinh(khach)["tong_giam"], 0)
	for nguon in km.NGUON_KHONG_GIAM_HANG:
		la("nguồn %s" % nguon, _tinh("KL013432", nguon=nguon)["tong_giam"], 0)
	la("Mang về vẫn giảm", _tinh("KL013432", nguon="Mang về")["tong_giam"], 70000)


@ca("v607 ưu đãi hạng: tính trên phần còn lại sau chương trình cộng dồn; chương trình không cộng dồn thì không giảm hạng")
def _():
	km10 = {"KM10": {"ten": "OneU 10%", "bat": 1, "uu_tien": 1, "cong_don": 1, "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "Phan tram", "gia_tri": 10, "pham_vi": "Ca hoa don", "doi_tuong": "Moi khach"}}
	with patch.object(km, "_tinh_mot", lambda k, gio, tong: {"giam": tong * 0.1, "dien_giai": ""}):
		kq = _tinh("KL013432", ctkm=km10)
		la("CTKM 70.000 rồi hạng 10% của 630.000", [a["giam"] for a in kq["ap"]], [70000, 63000])
		la("tổng", kq["tong_giam"], 133000)
		khong = {"KM10": dict(km10["KM10"], cong_don=0)}
		kq = _tinh("KL013432", ctkm=khong)
		la("không cộng dồn: chỉ chương trình", kq["tong_giam"], 70000)
		dung("báo lý do không giảm hạng", any(b["ten"] == "Ưu đãi hạng AMBASSADOR" and "không cộng dồn" in b["ly_do"]
			for b in kq["bo"]))


@ca("v607 ưu đãi hạng: hàm thuần tien_giam_hang")
def _():
	f = km.tien_giam_hang
	la("10% của 630.000", f(630000, 10), 63000.0)
	la("làm tròn đồng", f(12345, 10), 1234.0)
	la("trên 100% chặn về 100%", f(500, 150), 500.0)
	la("âm thì 0", f(500, -5), 0.0)
	la("còn lại âm thì 0", f(-10, 10), 0.0)


@ca("v607 ưu đãi hạng: ghi lượt khuyến mãi bỏ qua dòng hạng, không lập lượt CTKM giả")
def _():
	ghi = []
	gia = NS(get_doc=lambda d: ghi.append(d) or NS(insert=lambda **k: None),
		db=NS(set_value=lambda *a, **k: ghi.append(("set",) + a), get_value=lambda *a, **k: 0,
			exists=lambda *a, **k: False, commit=lambda: None),
		session=NS(user="quay@vagabond.vn"), log_error=lambda **k: None)
	with patch.object(km, "frappe", gia):
		km.ghi_su_dung({"ap": [{"loai": "hang", "ma": "AMBASSADOR", "ten": "Ưu đãi hạng AMBASSADOR", "giam": 70000}]},
			si_name="SI-1", ngay="2026-10-21")
	la("không ghi gì", ghi, [])


@ca("v607 ưu đãi hạng: danh sách nguồn không giảm trùng các nguồn sàn và sỉ của ban_hang")
def _():
	cay = ast.parse((GOC / "ban_hang.py").read_text(encoding="utf-8"))
	meta = next(n for n in cay.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NGUON_META")
	la("trùng khoá NGUON_META", sorted(ast.literal_eval(k) for k in meta.value.keys), sorted(km.NGUON_KHONG_GIAM_HANG))


@ca("v607 ưu đãi hạng: tao_don_tay truyền khách chọn qua số điện thoại và tính cả khi không chọn chương trình")
def _():
	src = (GOC / "ban_hang.py").read_text(encoding="utf-8")
	cay = ast.parse(src)
	f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "tao_don_tay")
	gan = [n for n in ast.walk(f) if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "khach_km"]
	la("khach_km = khach_no or khach_ma", [ast.unparse(n.value) for n in gan], ["khach_no or khach_ma or None"])
	goi = [n for n in ast.walk(f) if isinstance(n, ast.Call) and ast.unparse(n.func) == "_km.tinh_co_khoa"]
	la("một lời gọi tính khuyến mãi", len(goi), 1)
	la("truyền khách khach_km", [ast.unparse(k.value) for k in goi[0].keywords if k.arg == "khach"], ["khach_km"])
	dk = [n for n in ast.walk(f) if isinstance(n, ast.If) and "ctkm_ap" in ast.unparse(n.test) and "combo_ap" in ast.unparse(n.test)]
	dung("điều kiện tính có khach_km", any("khach_km" in ast.unparse(n.test) for n in dk))


@ca("v607 ưu đãi hạng: trần trừ điểm tại quầy (diem_otp) cũng trừ phần giảm hạng khi không chọn chương trình")
def _():
	# Nạp THẬT riêng hàm từ diem_otp.py (mô đun kéo frappe.rate_limiter, không import được ở đây).
	cay = ast.parse((GOC / "diem_otp.py").read_text(encoding="utf-8"))
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_km_giam_quay")
	goi = []
	gia_km = types.ModuleType("vagabond.khuyen_mai")
	gia_km.tinh = lambda items, **k: goi.append(k) or {"tong_giam": 70000}
	import vagabond
	g = {"flt": float, "frappe": NS(log_error=lambda *a, **k: None, get_traceback=lambda: "")}
	exec(compile(ast.Module(body=[ham], type_ignores=[]), "diem_otp.py", "exec"), g)
	with patch.dict(sys.modules, {"vagabond.khuyen_mai": gia_km}), \
			patch.object(vagabond, "khuyen_mai", gia_km, create=True):
		so = g["_km_giam_quay"]([{"item_code": "BANH", "qty": 1, "rate": 700000}], None, "", None,
			"TCV", "Tại chỗ", "KL013432", "0901234567", "2026-10-21")
		khong_khach = g["_km_giam_quay"]([{"item_code": "BANH", "qty": 1, "rate": 700000}], None, "", None,
			"TCV", "Tại chỗ", "", "", "2026-10-21")
	la("có khách: hỏi khuyen_mai.tinh và trừ 70.000", (so, [g.get("khach") for g in goi]), (70000.0, ["KL013432"]))
	la("không khách, không chương trình: 0, không hỏi", khong_khach, 0.0)
