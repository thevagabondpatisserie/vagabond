# -*- coding: utf-8 -*-
"""v519: dòng nguồn chỉ có mã thì đếm, không lập bản ghi rỗng.

Ca thật 23/09/2026. Banner "234 hoá đơn đầu vào đã nhận nhưng chưa thành
phiếu mua" đếm toàn bản ghi rỗng do M-Invoice trả vật tạm lẫn vào danh
sách. Xem chi_co_ma() trong minvoice_dong_bo.py để biết bằng chứng.

CẨN THẬN KHI SỬA CÁC CA DƯỚI ĐÂY: ca kiểm chạy hàm _keo THẬT lấy từ mã
nguồn, không gọi lại hàm nào khác để "cho chắc". Đừng thay _keo bằng bản
giả, vì đúng chỗ đó là chỗ phải chứng minh.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.minvoice_dong_bo import (
	LOAI_RA, LOAI_VAO, chi_co_ma, doc_trang, vo_ruot, _du_lieu, _extra,
)

TEP = Path(__file__).resolve().parents[2] / "minvoice_dong_bo.py"
MA = TEP.read_text(encoding="utf-8")

# Ba hình dạng dòng nguồn gặp thật.
DAY_DU = {"id": "4680f8ea-e127-4b04-9399-75e92599078b", "shdon": 857, "tdlap": "2026-09-21T00:00:00",
	"nbten": "CÔNG TY A", "nbmst": "0311", "tgtttbso": 972000, "khhdon": "C26TAA"}
VO_RUOT = {"id": "2ff8bb30-51d8-4032-bf9f-abe04714fc17", "shdon": 0, "tdlap": "2026-09-22T00:00:00",
	"nbten": None, "tgtttbso": 0}
CHI_MA = {"id": "6ab31e97f475d1ec4eeca851"}


def _chay_keo(lo_theo_trang, da_co=None, tra_lai=None):
	"""Chạy _keo THẬT trên một nguồn giả. Trả (kết quả, những gì đã ghi)."""
	ham = [n for n in ast.parse(MA).body
		if isinstance(n, ast.FunctionDef) and n.name == "_keo"]
	da_co = dict(da_co or {})
	ghi = {"insert": [], "set_value": [], "commit": 0, "rollback": []}

	class Doc(dict):
		def insert(self, **k):
			ghi["insert"].append(dict(self))

	db = SimpleNamespace(
		savepoint=lambda t: None,
		rollback=lambda save_point=None: ghi["rollback"].append(save_point),
		commit=lambda: ghi.__setitem__("commit", ghi["commit"] + 1),
		exists=lambda dt, n: n in da_co,
		get_value=lambda dt, n, f: da_co.get(n, {}).get(f),
		set_value=lambda dt, n, d: ghi["set_value"].append((n, d)),
	)
	f = SimpleNamespace(
		db=db, get_doc=lambda d: Doc(d),
		local=SimpleNamespace(message_log=[]),
		log_error=lambda *a, **k: None,
		get_traceback=lambda: "",
		utils=SimpleNamespace(
			formatdate=lambda d, f: "01/09/2026",
			add_days=lambda d, n: "2026-09-01",
			nowdate=lambda: "2026-09-23",
			get_datetime=lambda s: s,
			add_to_date=lambda d, hours=0: "2026-09-21 07:00:00",
		),
	)
	goi = []

	def _goi(cd, ts):
		goi.append(ts)
		lo = lo_theo_trang[ts["page"] - 1] if ts["page"] <= len(lo_theo_trang) else []
		return {"listInvoice": lo, "totalPage": len(lo_theo_trang)}

	env = dict(
		frappe=f, cint=lambda n: int(n or 0), json=__import__("json"),
		DT_HD="MInvoice Invoice", TRANG_TOI_DA=300,
		LOAI_VAO=LOAI_VAO, LOAI_RA=LOAI_RA,
		doc_trang=doc_trang, vo_ruot=vo_ruot, chi_co_ma=chi_co_ma,
		_du_lieu=_du_lieu, _extra=_extra, _goi_minvoice=_goi,
		_cai_dat=lambda: {"token": "x", "base": "b", "so_ngay": 7, "keo_vao": 1, "keo_ra": 0},
	)
	exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_dong_bo.py", "exec"), env)
	return env["_keo"](chi_loai="in"), ghi


@ca("#519 chi_co_ma: chỉ đúng khi nguồn không đưa cả số lẫn ngày")
def _thuan():
	dung("dòng chỉ có mã", chi_co_ma(CHI_MA))
	la("hoá đơn đủ ruột thì không", chi_co_ma(DAY_DU), False)
	la("vỏ ruột có ngày lập thì không", chi_co_ma(VO_RUOT), False)
	la("có số mà thiếu ngày cũng không", chi_co_ma({"shdon": 3}), False)
	la("dict rỗng là chỉ có mã", chi_co_ma({}), True)
	la("None không nổ", chi_co_ma(None), True)
	# shdon = 0 là "chưa có số" thật, không phải có số bằng không.
	la("số 0 coi như chưa có", chi_co_ma({"shdon": 0}), True)


@ca("#519 _keo: dòng chỉ có mã được ĐẾM mà KHÔNG lập bản ghi")
def _khong_luu():
	kq, ghi = _chay_keo([[DAY_DU, CHI_MA, VO_RUOT]])
	la("chỉ lập 2 bản ghi", len(ghi["insert"]), 2)
	la("không bản ghi nào mang mã ObjectId",
		[d for d in ghi["insert"] if d.get("ma_hd_id") == CHI_MA["id"]], [])
	la("vỏ ruột VẪN được lập", [d["ma_hd_id"] for d in ghi["insert"]].count(VO_RUOT["id"]), 1)
	la("hoá đơn đủ ruột được lập", [d["ma_hd_id"] for d in ghi["insert"]].count(DAY_DU["id"]), 1)
	la("đếm đúng 1 dòng chỉ có mã", kq["dong_chi_ma"], 1)
	la("KHÔNG đếm vào ô chờ nguồn", kq["nguon_chua_du"], 0)
	la("số tờ mới không tính dòng chỉ có mã", kq["moi"], 2)
	la("quét đủ 3 dòng", kq["da_quet"], 3)
	la("không coi là lỗi", kq["so_loi_hoa_don"], 0)
	dung("báo hoàn tất", kq["hoan_tat"])


@ca("#519 _keo: tờ có số mà nguồn thiếu ngày vẫn là hoá đơn, vẫn phải lưu")
def _co_so_thieu_ngay():
	# Chốt riêng vế shdon. Bỏ vế này khỏi chi_co_ma thì tờ có số thật bị
	# ném đi, mà các ca khác không nhìn thấy vì tờ mẫu nào cũng có ngày.
	co_so = {"id": "9c1f0f2e-1111-4222-8333-444455556666", "shdon": 4321, "tdlap": None,
		"nbten": "CÔNG TY B"}
	kq, ghi = _chay_keo([[co_so]])
	la("vẫn lưu tờ có số", [d["ma_hd_id"] for d in ghi["insert"]], [co_so["id"]])
	la("không đếm là chờ nguồn", kq["nguon_chua_du"], 0)
	la("không đếm là dòng chỉ có mã", kq["dong_chi_ma"], 0)
	la("tính là tờ mới", kq["moi"], 1)


@ca("#519 _keo: đường cho vỏ ruột lành lại KHÔNG bị chặn theo")
def _van_lanh():
	day = dict(VO_RUOT, shdon=1234)
	kq, ghi = _chay_keo([[day]], da_co={VO_RUOT["id"]: {"so_hd": None}})
	la("không lập thêm bản ghi", len(ghi["insert"]), 0)
	la("đổ ruột vào bản ghi cũ", len(ghi["set_value"]), 1)
	la("đúng bản ghi đó", ghi["set_value"][0][0], VO_RUOT["id"])
	la("số hoá đơn đã vào", ghi["set_value"][0][1]["so_hd"], 1234)
	la("đếm đã lành", kq["chua_lanh"], 1)
	la("không đếm vào chờ nguồn", kq["nguon_chua_du"], 0)
	la("không đếm là dòng chỉ có mã", kq["dong_chi_ma"], 0)


@ca("#519 _keo: bản ghi rỗng đã lỡ lưu trước đây không bị đụng tới")
def _khong_dung_du_lieu_cu():
	# Mã ObjectId cũ nằm sẵn trong máy, nguồn lượt này trả lại đúng mã đó.
	kq, ghi = _chay_keo([[CHI_MA]], da_co={CHI_MA["id"]: {"so_hd": None}})
	la("không ghi gì vào bản ghi cũ", ghi["set_value"], [])
	la("không lập bản ghi mới", ghi["insert"], [])
	la("tờ đã nằm trong máy mà còn trống số thì vẫn đếm chờ nguồn",
		kq["nguon_chua_du"], 1)


@ca("#519 _keo: dòng không có mã vẫn là lỗi, không lẫn với dòng chỉ có mã")
def _thieu_ma():
	kq, ghi = _chay_keo([[{"shdon": None, "tdlap": None}]])
	la("không lập bản ghi", ghi["insert"], [])
	la("đếm là lỗi", kq["so_loi_hoa_don"], 1)
	la("không đếm là chờ nguồn", kq["nguon_chua_du"], 0)
	la("không đếm là dòng chỉ có mã", kq["dong_chi_ma"], 0)
	la("đã lùi lại tờ hỏng", ghi["rollback"], ["minvoice_mot_to"])


@ca("#519 chỉ một chỗ quyết định, không ai tự dò lại shdon và tdlap")
def _mot_nguon():
	than = MA.split("def _keo(")[1].split("\ndef ")[0]
	la("thân _keo gọi chi_co_ma đúng một lần", than.count("chi_co_ma("), 1)
	la("không còn chỗ nào tự ghép lại điều kiện đó",
		than.count('not inv.get("shdon")'), 0)


# ---- Codex P1 tren SHA dbf808c4: dong chi co ma khong duoc lam nut bao hong

MA_CT = (Path(__file__).resolve().parents[2] / "minvoice_chung_tu.py").read_text(encoding="utf-8")


def _chay_dong_bo(keo_kq, dung_kq=None):
	"""Chạy `dong_bo_ngay` THẬT, chỉ thay bước kéo và bước dựng bằng số cho sẵn.

	Phải chạy hàm thật vì điều cần chốt nằm đúng ở câu tính `hoan_tat`.
	"""
	ham = [n for n in ast.parse(MA_CT).body
		if isinstance(n, ast.FunctionDef) and n.name == "dong_bo_ngay"]
	env = dict(
		frappe=SimpleNamespace(whitelist=lambda: (lambda h: h)),
		_kiem_quyen=lambda s: None, cint=lambda n: int(n or 0),
		_chay=lambda: dict({"da_dung": 1, "con_hong": 0, "dang_chay_do": 0}, **(dung_kq or {})),
	)
	import sys as _sys
	import types as _types
	goi = _types.ModuleType("vagabond")
	goi.minvoice_dong_bo = SimpleNamespace(_keo=lambda so_ngay=None: keo_kq)
	cu = _sys.modules.get("vagabond")
	_sys.modules["vagabond"] = goi
	try:
		exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_chung_tu.py", "exec"), env)
		return env["dong_bo_ngay"]()
	finally:
		if cu is not None:
			_sys.modules["vagabond"] = cu


@ca("#519 nút Đồng bộ: dòng chỉ có mã KHÔNG làm lượt kéo lành bị báo là hỏng")
def _nut_dong_bo():
	# Codex P1 ngày 23/09/2026 trên SHA dbf808c4. Trước khi sửa, gộp dòng chỉ
	# có mã vào `nguon_chua_du` làm `ok` về 0, nên gần như lượt nào cũng hiện
	# bảng cam "Đồng bộ chưa hoàn tất" dù không có gì hỏng. Riêng 23/09 có 16
	# dòng như vậy, tức là mọi lượt trong ngày đều báo hỏng oan.
	lanh = {"loi_o_loai": [], "nguon_chua_du": 0, "dong_chi_ma": 0, "moi": 2, "chua_lanh": 0}
	la("lượt sạch thì ok", _chay_dong_bo(lanh)["ok"], 1)
	la("có dòng chỉ có mã vẫn ok", _chay_dong_bo(dict(lanh, dong_chi_ma=16))["ok"], 1)
	# Ba vế còn lại vẫn phải kéo ok về 0, đừng nới tay quá.
	la("tờ trong máy còn trống số thì chưa xong",
		_chay_dong_bo(dict(lanh, nguon_chua_du=1))["ok"], 0)
	la("lỗi theo loại thì chưa xong",
		_chay_dong_bo(dict(lanh, loi_o_loai=["Đầu vào"]))["ok"], 0)
	la("còn tờ hỏng thì chưa xong",
		_chay_dong_bo(lanh, {"con_hong": 1})["ok"], 0)
	# Chốt không ai lặng lẽ nhét lại `dong_chi_ma` vào câu tính hoàn tất.
	than = MA_CT.split("def dong_bo_ngay(")[1].split("\ndef ")[0]
	la("câu tính hoàn tất không nhắc dòng chỉ có mã", than.count("dong_chi_ma"), 0)
