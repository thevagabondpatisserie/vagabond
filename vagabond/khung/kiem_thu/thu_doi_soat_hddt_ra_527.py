# -*- coding: utf-8 -*-
"""v527 phần B: tờ lập thẳng trên m-invoice không có trong ERP.

Dữ liệu dựng lại đúng SỐ HOÁ ĐƠN và quan hệ thay thế thật của 17/09 tới
22/09 (chị Dung tổng hợp 25/09/2026). Tên người mua và mã số thuế là giả,
không đưa dữ liệu khách vào repo. Ca kiểm chạy hàm thật của
doi_soat_hddt_ra và _keo thật của minvoice_dong_bo.
"""

import ast
import datetime
from pathlib import Path
from types import SimpleNamespace as NS
import unittest.mock

from vagabond import doi_soat_hddt_ra as ds
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
MST_TACH = "0300000001"


class _D(dict):
	"""Như frappe._dict: đọc được cả .get lẫn thuộc tính."""
	__getattr__ = dict.get


def _to(so, ngay, tt="Gốc", goc="", mst="", ten=None):
	return {"name": ten or "TO-%s" % so, "so_hd": so, "ky_hieu": "C26MPV", "ngay_lap": ngay,
		"trang_thai": tt, "hd_goc": ("KH C26MPV - So %s - Ngay 2026-09-01" % goc) if goc else "",
		"mst_doi_tac": mst, "tong_tien": 100000, "nguoi_mua_ban": "Người mua"}


def _don(ten, so="", thay="", mst="", ngay="2026-09-15", kh="1C26MPV", day=None, id_=""):
	return {"name": ten, "custom_hddt_so": so, "custom_hddt_ky_hieu": kh, "custom_hddt_thay_the": thay,
		"vgb_xhd_mst": mst, "posting_date": ngay, "vgb_hddt_ngay_xuat": None,
		"custom_minvoice_id": id_, "custom_hddt_id": "", "custom_minvoice_ngay_day": day,
		"custom_pancake_display_id": "P-" + ten[-4:]}


# Bảy đơn gốc thật và cách kế toán đã ghi (bốn đơn có ô thay thế, ba không).
DON = [
	_don("HDB-26-09-02861", "14159", "1C26MPV 14401"),
	_don("HDB-26-09-02805", "14180", "1C26MPV 14402"),
	_don("HDB-26-09-03253", "14514", "1C26MPV 14576"),
	_don("HDB-26-09-03340", "14634", "", MST_TACH, "2026-09-18"),
	_don("HDB-26-08-02245", "10749", "", "", "2026-08-20"),
	_don("HDB-26-08-03934", "11191", "", "", "2026-08-27"),
	_don("HDB-26-09-01138", "12736", "", "", "2026-09-07"),
	_don("HDB-26-09-09999", "15500"),
]
TO = [
	_to(14401, "2026-09-17", "Thay thế", 14159), _to(14402, "2026-09-17", "Thay thế", 14180),
	_to(14576, "2026-09-18", "Thay thế", 14514),
	_to(15217, "2026-09-21", "Thay thế", 14634, MST_TACH),
	_to(15228, "2026-09-21", mst=MST_TACH), _to(15229, "2026-09-21", mst=MST_TACH),
	_to(15230, "2026-09-21", mst=MST_TACH), _to(15231, "2026-09-21", mst=MST_TACH),
	_to(15439, "2026-09-22", "Thay thế", 12736), _to(15440, "2026-09-22", "Thay thế", 10749),
	_to(15441, "2026-09-22", "Thay thế", 11191),
	_to(15500, "2026-09-22"),
]


@ca("v527 chuẩn hoá: ký hiệu 1C26MPV khớp C26MPV, số không 0 đứng đầu, đọc ô tờ gốc và ô thay thế")
def _chuan():
	la("ký hiệu", (ds.kh("1c26mpv"), ds.kh("C26MPV"), ds.kh("")), ("C26MPV", "C26MPV", ""))
	la("số", (ds.so(14401), ds.so("014401"), ds.so(14401.0), ds.so(0), ds.so(None)), ("14401", "14401", "14401", "", ""))
	la("tờ gốc", ds.tach_goc("KH C26MPV - So 14180 - Ngay 2026-09-14"), ("C26MPV", "14180"))
	la("ô tờ gốc trống", ds.tach_goc(""), None)
	la("ô thay thế kế toán ghi", ds.tach_ghi_thay_the("1C26MPV 14402"), ("C26MPV", "14402"))


@ca("v527 xếp loại 11 tờ chị Dung đếm thiếu: 7 thay thế nối về đúng đơn, 4 tờ tách gợi ý đơn 94132")
def _mot_muoi_mot_to():
	ket = ds.phan_loai(TO, DON)
	thay = {so: ket["TO-%s" % so]["don"] for so in (14401, 14402, 14576, 15217, 15439, 15440, 15441)}
	la("bảy tờ thay thế nối về đúng đơn gốc", thay, {
		14401: "HDB-26-09-02861", 14402: "HDB-26-09-02805", 14576: "HDB-26-09-03253",
		15217: "HDB-26-09-03340", 15439: "HDB-26-09-01138", 15440: "HDB-26-08-02245",
		15441: "HDB-26-08-03934"})
	dung("cả bảy là loại thay thế",
		all(ket["TO-%s" % so]["loai"] == ds.LOAI_THAY for so in thay))
	la("ba tờ 22/09 nối theo số tờ gốc, không cần ô ghi tay",
		[ket["TO-%s" % so]["ly_do"] for so in (15439, 15440, 15441)],
		["thay tờ 12736 của đơn", "thay tờ 10749 của đơn", "thay tờ 11191 của đơn"])
	for so in (15228, 15229, 15230, 15231):
		la("tờ tách %s là tạo tay" % so, ket["TO-%s" % so]["loai"], ds.LOAI_TAO_TAY)
		la("gợi ý đơn 94132", ket["TO-%s" % so]["goi_y"], "HDB-26-09-03340")
	la("tờ thường của ERP", (ket["TO-15500"]["loai"], ket["TO-15500"]["don"]), (ds.LOAI_ERP, "HDB-26-09-09999"))


@ca("v527 xếp loại: lần chuỗi thay thế nhiều đời, tờ gốc nằm ngoài khoảng xem")
def _nhieu_doi():
	don = [_don("SI-A", "100")]
	b = _to(200, "2026-09-10", "Thay thế", 100)
	c = _to(300, "2026-09-20", "Thay thế", 200)
	ket = ds.phan_loai([c], don, [b])
	la("tờ đời thứ hai nối về đơn A", (ket["TO-300"]["loai"], ket["TO-300"]["don"]), (ds.LOAI_THAY, "SI-A"))
	dung("ghi rõ lần qua hai đời", "2 đời" in ket["TO-300"]["ly_do"])
	ket = ds.phan_loai([c], don)
	la("thiếu đời giữa thì không đoán", ket["TO-300"]["loai"], ds.LOAI_THAY_CHUA_NOI)


@ca("v527 xếp loại: không đoán bừa (khác ký hiệu, gợi ý không duy nhất, tờ gốc ngoài ERP)")
def _khong_doan():
	ket = ds.phan_loai([_to(15500, "2026-09-22")], [_don("SI-FABI", "15500", kh="1C26MVO")])
	la("cùng số khác ký hiệu không phải tờ ERP", ket["TO-15500"]["loai"], ds.LOAI_TAO_TAY)
	ket = ds.phan_loai([_to(15500, "2026-09-22")], [_don("SI-CU", "15500", kh="")])
	la("đơn cũ thiếu ký hiệu mà duy nhất mang số đó thì nhận", ket["TO-15500"]["loai"], ds.LOAI_ERP)
	ket = ds.phan_loai([_to(15600, "2026-09-22", mst=MST_TACH)],
		[_don("SI-1", "1", mst=MST_TACH), _don("SI-2", "2", mst=MST_TACH)])
	la("hai đơn cùng mã số thuế thì không gợi ý", ket["TO-15600"]["goi_y"], "")
	ket = ds.phan_loai([_to(15700, "2026-09-22", "Thay thế", 99999)], DON)
	la("tờ gốc không có trong ERP", ket["TO-15700"]["loai"], ds.LOAI_THAY_CHUA_NOI)
	dung("nói rõ số tờ gốc", "99999" in ket["TO-15700"]["ly_do"])


@ca("v527 xếp loại: tờ thay thế nguồn không ghi tờ gốc thì nối theo ô thay thế kế toán ghi trên đơn")
def _chi_co_ghi_tay():
	# Đột biến "bỏ ô ghi tay" lần đầu không đổ ca nào (điều 17c): bốn tờ ghi
	# tay ở ca 11 tờ đều có cả số tờ gốc, đường lần theo tờ gốc đỡ. Ca này
	# tách riêng: nguồn không trả số tờ gốc.
	to = dict(_to(14402, "2026-09-17", "Thay thế"), hd_goc="")
	ket = ds.phan_loai([to], DON)
	la("nối về đơn ghi tay", (ket["TO-14402"]["loai"], ket["TO-14402"]["don"]), (ds.LOAI_THAY, "HDB-26-09-02805"))
	dung("nói rõ do kế toán ghi", "kế toán" in ket["TO-14402"]["ly_do"])


@ca("v527 xếp loại: khớp mã m-invoice trước, số sau")
def _theo_ma():
	ket = ds.phan_loai([_to(1, "2026-09-22", ten="uuid-1")], [_don("SI-ID", "", id_="uuid-1")])
	la("khớp theo mã", (ket["uuid-1"]["loai"], ket["uuid-1"]["don"]), (ds.LOAI_ERP, "SI-ID"))


@ca("v527 tổng hợp ngày: đúng bốn con số chị Dung đếm, và ERP nay ghi nhận đủ tờ thay thế")
def _tong_hop():
	# Mỗi ngày thêm tờ thường của ERP để ra đúng tổng thật.
	to, don = list(TO), list(DON)
	for ngay, them in (("2026-09-17", 173), ("2026-09-18", 217), ("2026-09-21", 171), ("2026-09-22", 158)):
		for i in range(them):
			so = "%s%03d" % (ngay[-2:], i)
			to.append(_to(int("9" + so), ngay))
			don.append(_don("SI-%s" % so, "9" + so, ngay=ngay))
	dong = {r["ngay"]: r for r in ds.tong_hop_ngay(to, ds.phan_loai(to, don))}
	la("tổng tờ trên m-invoice", [dong[d]["tren_minvoice"] for d in sorted(dong)], [175, 218, 176, 162])
	la("ERP phát hành (con số chị Dung thấy)", [dong[d]["erp_phat_hanh"] for d in sorted(dong)], [173, 217, 171, 159])
	la("ERP ghi nhận sau khi nối thay thế", [dong[d]["erp_ghi_nhan"] for d in sorted(dong)], [175, 218, 172, 162])
	la("còn lệch đúng 4 tờ tách của 21/09", [dong[d]["lech"] for d in sorted(dong)], [0, 0, 4, 0])


@ca("v527 tổng hợp ngày: đếm tờ ERP chưa kéo về và tờ đẩy lên m-invoice sau nửa đêm")
def _sau_0h():
	don = [_don("SI-1", "1", ngay="2026-09-23", day="2026-09-24 00:16:08"),
		_don("SI-2", "2", ngay="2026-09-23", day="2026-09-23 22:40:00"),
		_don("SI-3", "3", ngay="2026-09-23", day="2026-09-23 23:05:00")]
	to = [_to(1, "2026-09-23"), _to(2, "2026-09-23")]
	r = ds.tong_hop_ngay(to, ds.phan_loai(to, don), don)[0]
	la("một tờ đẩy sau 0h", r["xuat_sau_0h"], 1)
	la("một tờ ERP có mà m-invoice chưa kéo về", r["erp_chua_keo"], 1)


@ca("v527 đọc dữ liệu: lọc đúng ký hiệu đang phát hành, đọc tờ gốc ngoài khoảng theo số, nhiều đời")
def _doc():
	hoi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0):
		hoi.append((dt, dict(filters)))
		if dt == "MInvoice Invoice":
			if "ngay_lap" in filters:
				return [_D(_to(300, "2026-09-20", "Thay thế", 200)), _D(dict(_to(1, "2026-09-20"), ky_hieu="C26MVO"))]
			so = filters["so_hd"][1]
			if so == ["200"]:
				return [_D(_to(200, "2026-09-10", "Thay thế", 100))]
			if so == ["100"]:
				return [_D(_to(100, "2026-09-01"))]
			return []
		return []
	f = NS(get_all=get_all, db=NS(get_single_value=lambda *a: "1C26MPV"))
	with unittest.mock.patch.object(ds, "frappe", f):
		to, goc, si, si_ngay = ds.doc("2026-09-20", "2026-09-20")
	la("bỏ tờ khác ký hiệu", [t.so_hd for t in to], [300])
	la("đọc tờ gốc hai đời", sorted(t.so_hd for t in goc), [100, 200])
	so_don = [h[1]["custom_hddt_so"][1] for h in hoi if h[0] == "Sales Invoice" and "custom_hddt_so" in h[1] and h[1]["custom_hddt_so"][0] == "in"]
	la("đơn được hỏi theo đủ số của cả chuỗi", so_don, [["100", "200", "300"]])


@ca("v527 BC17 có trong danh sách báo cáo Kế toán và trả đúng hình dạng màn báo cáo")
def _bc17():
	from vagabond import bao_cao
	b = bao_cao.THEO_MA.get("BC17")
	dung("có BC17", bool(b))
	la("nhóm Kế toán, không so kỳ trước", (b["nhom"], b["ss"]), ("Kế toán", None))
	with unittest.mock.patch.object(ds, "doc", lambda tu, den: (TO, [], DON, [])):
		kq = b["ham"]([], tu="2026-09-17", den="2026-09-22")
	la("một dòng mỗi ngày", [r["ngay"] for r in kq["dong"]], ["2026-09-17", "2026-09-18", "2026-09-21", "2026-09-22"])
	la("bảng phụ liệt kê đủ 11 tờ lập thẳng", len(kq["phu"]["dong"]), 11)
	la("tờ 15441 chỉ ra đơn gốc", [(r["so_hd"], r["don"]) for r in kq["phu"]["dong"] if r["so_hd"] == "15441"],
		[("15441", "HDB-26-08-03934")])
	dung("cột có khoá và nhãn", all("k" in c for c in kq["cot"]))


# ------------------------------------------- _keo thật: trạng thái đổi về sau


def _keo(inv, da_co):
	ma = (GOC / "minvoice_dong_bo.py").read_text(encoding="utf-8")
	ham = [n for n in ast.parse(ma).body if isinstance(n, ast.FunctionDef) and n.name == "_keo"]
	from vagabond import minvoice_dong_bo as md
	ghi = []
	db = NS(savepoint=lambda t: None, rollback=lambda save_point=None: None, commit=lambda: None,
		exists=lambda dt, n: n in da_co, get_value=lambda dt, n, f: da_co.get(n, {}).get(f),
		set_value=lambda dt, n, d: ghi.append((n, d)))
	f = NS(db=db, get_doc=lambda d: None, local=NS(message_log=[]), log_error=lambda *a, **k: None,
		get_traceback=lambda: "", utils=NS(formatdate=lambda d, f: "01/09/2026", add_days=lambda d, n: d,
			nowdate=lambda: "2026-09-25"))
	env = dict(frappe=f, cint=lambda n: int(n or 0), json=__import__("json"), DT_HD="MInvoice Invoice",
		TRANG_TOI_DA=300, LOAI_VAO=md.LOAI_VAO, LOAI_RA=md.LOAI_RA, doc_trang=md.doc_trang, vo_ruot=md.vo_ruot,
		chi_co_ma=md.chi_co_ma, _du_lieu=md._du_lieu, _extra=md._extra,
		trang_thai_doi_ve_sau=md.trang_thai_doi_ve_sau,
		_goi_minvoice=lambda cd, ts: {"listInvoice": [inv], "totalPage": 1},
		_cai_dat=lambda: {"token": "x", "base": "b", "so_ngay": 7, "keo_vao": 0, "keo_ra": 1})
	exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_dong_bo.py", "exec"), env)
	return env["_keo"](chi_loai="out"), ghi


@ca("v527 kéo m-invoice: tờ gốc đã có trong máy mà nay bị thay thế thì cập nhật đúng một ô")
def _keo_trang_thai():
	inv = {"id": "ID-14159", "shdon": 14159, "tdlap": "2026-09-15T00:00:00", "tthai": 4}
	kq, ghi = _keo(inv, {"ID-14159": {"so_hd": 14159, "trang_thai": "Gốc"}})
	la("ghi đúng ô trạng thái", ghi, [("ID-14159", {"trang_thai": "Bị thay thế"})])
	la("đếm cập nhật", kq["cap_nhat"], 1)
	kq, ghi = _keo(inv, {"ID-14159": {"so_hd": 14159, "trang_thai": "Bị thay thế"}})
	la("đã đúng thì không ghi", ghi, [])
	kq, ghi = _keo(dict(inv, tthai=1), {"ID-14159": {"so_hd": 14159, "trang_thai": "Bị thay thế"}})
	la("không bao giờ quay về Gốc", ghi, [])
	kq, ghi = _keo(dict(inv, tthai=6), {"ID-14159": {"so_hd": None, "trang_thai": ""}})
	dung("vỏ ruột vẫn đi đường lành cũ, không đi đường mới",
		len(ghi) == 1 and "so_hd" in ghi[0][1])
