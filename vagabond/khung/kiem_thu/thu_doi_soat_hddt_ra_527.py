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
	# v527: ô thay thế nay có thể do máy đồng bộ ghi, lời nói theo ô trên đơn.
	dung("nói rõ nối theo ô ghi trên đơn", "đơn đã ghi" in ket["TO-14402"]["ly_do"])


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


# ------------------------------------ Codex vòng 1 (#369): ba finding của BC17


def _doc_voi(ky_hieu):
	"""Chạy doc() thật với ô ký hiệu tuỳ ý. ky_hieu là hàm để giả được cả lỗi đọc."""
	hoi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=0):
		hoi.append(dt)
		if dt == "MInvoice Invoice" and "ngay_lap" in filters:
			return [_D(_to(300, "2026-09-20")), _D(dict(_to(1, "2026-09-20"), ky_hieu="C26MVO"))]
		return []

	import frappe as _fr
	f = NS(get_all=get_all, db=NS(get_single_value=ky_hieu), throw=_fr.throw)
	with unittest.mock.patch.object(ds, "frappe", f):
		try:
			to = ds.doc("2026-09-20", "2026-09-20")[0]
			return "chạy", sorted(t.ky_hieu for t in to), hoi
		except Exception as e:
			return "dừng", str(e), hoi


@ca("v527 Codex F1: ô ký hiệu trống hoặc đọc lỗi thì dừng có lời, không đếm lẫn dải Fabi C26MVO")
def _ky_hieu_dong_cua():
	kq, chi, hoi = _doc_voi(lambda *a: "")
	la("ký hiệu trống thì dừng", kq, "dừng")
	dung("lời dừng chỉ chỗ sửa", "ký hiệu" in str(chi))
	la("không đọc bảng tờ khi chưa biết ký hiệu", hoi.count("MInvoice Invoice"), 0)

	def loi(*a):
		raise RuntimeError("mất kết nối")
	kq, chi, hoi = _doc_voi(loi)
	la("đọc cài đặt lỗi thì dừng", kq, "dừng")
	la("không đọc bảng tờ khi đọc cài đặt lỗi", hoi.count("MInvoice Invoice"), 0)
	# Đối chứng: có ký hiệu thì chạy và chỉ lấy đúng dải đang phát hành.
	kq, chi, hoi = _doc_voi(lambda *a: "1C26MPV")
	la("có ký hiệu thì chỉ đúng dải", (kq, chi), ("chạy", ["C26MPV"]))


def _chay_bc(ma, n_to=0, **ts):
	"""Chạy bao_cao.chay THẬT. Chỉ giả lớp đọc đơn và lớp đọc bảng tờ."""
	from vagabond import bao_cao as bc
	hoi_hd = []

	def hoa_don(tu, den, diem=None, nguon=None, pt=None):
		hoi_hd.append((diem, nguon, pt))
		return [_D({"name": "HD1", "grand_total": 10, "_nhap": 0, "custom_nguon": "Grab",
			"vgb_pt_thanh_toan": "Tiền mặt", "custom_hddt_so": "1"}),
			_D({"name": "HD2", "grand_total": 20, "_nhap": 0, "custom_nguon": "Tại chỗ",
			"vgb_pt_thanh_toan": "Chuyển khoản", "custom_hddt_so": ""})]
	to = [_to(20000 + i, "2026-09-20", mst="03%08d" % i) for i in range(n_to)]
	with unittest.mock.patch.object(bc, "_hoa_don", hoa_don), \
			unittest.mock.patch.object(bc, "_diem_ban", lambda: [{"ma": "TCV", "ten": "TCV", "dia_chi": ""}]), \
			unittest.mock.patch.object(ds, "doc", lambda tu, den: (to, [], [], [])):
		kq = bc.chay(ma, ky="tuy_chon", tu="2026-09-20", den="2026-09-20", **ts)
	return kq, hoi_hd


@ca("v527 Codex F2: bảng phụ BC17 không mất tờ nào khi xuất Excel, màn hình cắt thì nói rõ")
def _phu_du_dong():
	from vagabond import bao_cao as bc
	n = bc.GIOI_HAN_DONG + 100
	kq, _h = _chay_bc("BC17", n_to=n, day_du=1)
	la("xuất đủ: bảng phụ đủ mọi tờ", len(kq["phu"]["dong"]), n)
	kq, _h = _chay_bc("BC17", n_to=n)
	la("màn hình: cắt đúng giới hạn", len(kq["phu"]["dong"]), bc.GIOI_HAN_DONG)
	la("màn hình: báo tổng và cờ cắt", (kq["phu"].get("tong_dong"), kq["phu"].get("bi_cat")), (n, 1))
	# Đi đúng nút Xuất Excel: file phải có đủ n dòng tờ, không chỉ n của hàm chay.
	bang = []
	xl = __import__("sys").modules["frappe.utils.xlsxutils"]
	with unittest.mock.patch.object(xl, "make_xlsx", lambda b, ten: bang.extend(b) or b"x"), \
			unittest.mock.patch.object(bc, "_hoa_don", lambda *a, **k: []), \
			unittest.mock.patch.object(ds, "doc", lambda tu, den: (
				[_to(20000 + i, "2026-09-20") for i in range(n)], [], [], [])):
		bc.xuat_excel("BC17", ky="tuy_chon", tu="2026-09-20", den="2026-09-20")
	la("file Excel có đủ mọi tờ", sum(1 for r in bang if len(r) > 1 and str(r[1]).startswith("2") and str(r[1]).isdigit()), n)
	# Ít dòng thì không cắt, không báo.
	kq, _h = _chay_bc("BC17", n_to=3)
	la("ít dòng: không cờ cắt", (len(kq["phu"]["dong"]), kq["phu"].get("bi_cat")), (3, 0))


@ca("v527 Codex F3: BC17 không nhận lọc điểm bán, nguồn, phương thức; báo cáo khác vẫn nhận")
def _bc17_khong_loc():
	kq, hoi = _chay_bc("BC17", diem="TCV", nguon="Grab", pt="Tiền mặt")
	la("BC17 đọc toàn công ty", hoi, [(None, None, None)])
	la("BC17 báo màn hình ẩn lọc", kq.get("khong_loc"), 1)
	la("BC17 không gửi chip nguồn, phương thức", (kq["nguon_loc"], kq["pt_loc"]), ([], []))
	# Đối chứng: BC05 vẫn lọc như cũ, nên phép giả đọc đơn thật sự ghi được tham số.
	kq, hoi = _chay_bc("BC05", diem="TCV", nguon="Grab", pt="Tiền mặt")
	la("BC05 vẫn lọc", hoi, [("TCV", "Grab", "Tiền mặt")])
	la("BC05 không cờ ẩn lọc", kq.get("khong_loc"), 0)


def _ve_bc(kq, bc_diem="TCV"):
	"""Chạy thật scrBaoCaoXem của 14-bao-cao.js trong node với API giả."""
	import json
	import subprocess
	goc = GOC / "public" / "js" / "bep"

	def cat(tep, ten):
		import re
		m = re.search(r"\nfunction %s\([^)]*\) ?\{.*?\n\}" % ten, (goc / tep).read_text(encoding="utf-8"), re.S)
		if not m:
			m = re.search(r"\nfunction %s\([^\n]*\n" % ten, (goc / tep).read_text(encoding="utf-8"))
		return m.group(0)
	nen = cat("00-nen.js", "h") + cat("00-nen.js", "money") + cat("09-tinh-tien-quay.js", "posChipNut") + \
		cat("13-khuyen-mai.js", "kmHangChip") + \
		cat("09-tinh-tien-quay.js", "posNgayVn")
	man = (goc / "14-bao-cao.js").read_text(encoding="utf-8")
	kich = r"""
const vm = require('vm');
const ghi = { html: [], api: [] };
const ctx = { console: console, setTimeout: setTimeout,
  document: { getElementById: function () { return { onclick: null }; } },
  frame: function (t, b) { ghi.html.push(b); return { onclick: null, querySelector: function () { return null; } }; },
  api: async function (m, a) { ghi.api.push(a); return __KQ__; },
  today: function () { return '2026-09-20'; }, go: function () {}, busy: function () {}, toast: function () {} };
vm.createContext(ctx);
vm.runInContext(__NEN__, ctx);
vm.runInContext(__MAN__, ctx);
vm.runInContext("bcMa = 'BC17'; bcDiem = " + JSON.stringify(__DIEM__) + ";", ctx);
ctx.scrBaoCaoXem().then(function () {
  process.stdout.write(JSON.stringify({ html: ghi.html[ghi.html.length - 1], api: ghi.api }));
}).catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	# Thay khoá nhỏ trước, hai khối mã nguồn sau cùng, để không thay nhầm chữ bên trong mã.
	kich = kich.replace("__KQ__", json.dumps(kq)).replace("__DIEM__", json.dumps(bc_diem))
	kich = kich.replace("__NEN__", json.dumps(nen)).replace("__MAN__", json.dumps(man))
	r = subprocess.run(["node", "-e", kich], capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("node lỗi: " + (r.stderr or "").strip()[:500])
	return json.loads(r.stdout)


def _kq_man(**doi):
	kq = {"ma": "BC17", "ten": "Đối chiếu", "ic": "🔎", "mo": "", "nhan_ky": "Ngày 20/09/2026",
		"tong_doanh_thu": 0, "so_hoa_don": 0, "nhap": 1, "chot": 0, "so_nhap": 0, "tien_nhap": 0,
		"cot": [{"k": "ngay", "nhan": "Ngày lập", "kieu": "ngay"}], "dong": [{"ngay": "2026-09-20"}],
		"cong": {}, "tong_dong": 1, "bi_cat": 0, "gioi_han": 600, "ss": None, "co_ss_dong": 0,
		"bieu_do": None, "nhan_dinh": None, "nguon_loc": ["Grab", "Tại chỗ"], "pt_loc": ["Tiền mặt", "Thẻ"],
		"diem_ban": [{"ma": "TCV", "ten": "TCV"}, {"ma": "NVHTN", "ten": "NVHTN"}],
		"phu": {"tieu_de": "Tờ lập thẳng", "cot": [{"k": "so_hd", "nhan": "Số", "kieu": "chu"}],
			"dong": [{"so_hd": "1"}], "tong_dong": 1, "bi_cat": 0, "gioi_han": 600}}
	kq.update(doi)
	return kq


@ca("v527 Codex F2+F3 trên màn thật: BC17 ẩn chip điểm bán và có lời vì sao; bảng phụ bị cắt thì nói rõ")
def _man_bc17():
	ra = _ve_bc(_kq_man(khong_loc=1, nguon_loc=[], pt_loc=[]))
	dung("BC17: không vẽ chip điểm bán", "data-bcdiem" not in ra["html"])
	dung("BC17: không vẽ chip nguồn, phương thức", "data-bcnguon" not in ra["html"] and "data-bcpt" not in ra["html"])
	dung("BC17: nói rõ vì sao không lọc", "không lọc theo điểm bán" in ra["html"])
	# Đối chứng: báo cáo thường vẫn có đủ ba hàng chip, nên phép dò không xanh vì màn trống.
	ra = _ve_bc(_kq_man(ma="BC05", khong_loc=0))
	dung("báo cáo thường: còn chip điểm bán", "data-bcdiem" in ra["html"])
	dung("báo cáo thường: còn chip nguồn", "data-bcnguon" in ra["html"])
	dung("báo cáo thường: không có lời ẩn lọc", "không lọc theo điểm bán" not in ra["html"])
	ra = _ve_bc(_kq_man(khong_loc=1, phu={"tieu_de": "Tờ lập thẳng", "cot": [{"k": "so_hd", "nhan": "Số", "kieu": "chu"}],
		"dong": [{"so_hd": "1"}], "tong_dong": 700, "bi_cat": 1, "gioi_han": 600}))
	dung("bảng phụ bị cắt: báo tổng 700", "700" in ra["html"] and "Xuất Excel" in ra["html"])


# --------------------- Codex vòng 2 (#369) G2: đơn cũ kéo ngày lập vào kỳ xem


def _loc(rows, filters):
	"""Lọc giả đủ cho các phép get_all của doc(): =, in, between, is set."""
	def khop(r, k, v):
		x = r.get(k)
		if isinstance(v, list):
			op, gt = v[0], v[1] if len(v) > 1 else None
			if op == "in":
				# Ô Data trên site trả chuỗi: so theo chuỗi (lần đầu so int với
				# chuỗi nên tờ gốc bị thay lọt khỏi phép cộng, đột biến Q3 không đổ).
				return str(x) in [str(v) for v in gt]
			if op == "between":
				return x is not None and str(gt[0]) <= str(x) <= str(gt[1])
			if op == "is":
				return bool(x) if gt == "set" else not x
			raise AssertionError("phép lọc chưa hỗ trợ: %s" % op)
		return str(x) == str(v) if isinstance(x, (int, str)) and isinstance(v, (int, str)) else x == v
	return [r for r in rows if all(khop(r, k, v) for k, v in filters.items())]


@ca("v527 Codex G2: đơn bán 10/09 kéo ngày lập sang 20/09 vẫn được đếm cho ngày 20/09")
def _g2_don_keo_ngay():
	don = [_D(dict(_don("HDB-26-09-01000", "15000", ngay="2026-09-10"), vgb_hddt_ngay_xuat="2026-09-20",
		docstatus=1))]
	import frappe as _fr

	def get_all(dt, filters=None, fields=None, limit_page_length=0):
		if dt == "Sales Invoice":
			return _loc(don, filters)
		return []
	f = NS(get_all=get_all, db=NS(get_single_value=lambda *a: "1C26MPV"), throw=_fr.throw)
	with unittest.mock.patch.object(ds, "frappe", f):
		si_ngay = ds.doc("2026-09-20", "2026-09-20")[3]
	la("đơn kéo ngày có mặt trong tập đếm ERP của 20/09", [s.name for s in si_ngay], ["HDB-26-09-01000"])
	with unittest.mock.patch.object(ds, "frappe", f):
		si_ngay = ds.doc("2026-09-10", "2026-09-10")[3]
	la("và không bị đếm cho ngày sổ 10/09", si_ngay, [])


# ============ v527 anh Việt chốt 25/09: tờ thay thế tự về đơn, nối tay tờ tách


def _dthay(ten, so_, thay="", ky="1C26MPV"):
	return _D(dict(_don(ten, so_, thay, kh=ky), docstatus=1))


@ca("v527 tờ thay thế về đơn: 22/09 ba tờ ghi vào ô trống, tờ đã ghi thì thôi, không đụng Điều chỉnh")
def _thay_the_ke_hoach():
	don = [_dthay("HDB-26-09-01138", "12736"), _dthay("HDB-26-08-02245", "10749"),
		_dthay("HDB-26-08-03934", "11191"), _dthay("HDB-26-09-02861", "14159", "1C26MPV 14401")]
	to = [_to(15439, "2026-09-22", "Thay thế", 12736), _to(15440, "2026-09-22", "Thay thế", 10749),
		_to(15441, "2026-09-22", "Thay thế", 11191), _to(14401, "2026-09-17", "Thay thế", 14159),
		_to(15600, "2026-09-23", "Điều chỉnh", 12736)]
	viec, xd = ds.ke_hoach_thay_the(to, don)
	la("ba đơn 22/09 được ghi đúng tờ", sorted((v["don"], v["cu"], v["moi"]) for v in viec), [
		("HDB-26-08-02245", "", "1C26MPV 15440"), ("HDB-26-08-03934", "", "1C26MPV 15441"),
		("HDB-26-09-01138", "", "1C26MPV 15439")])
	la("không xung đột", xd, [])


@ca("v527 tờ thay thế về đơn: thay nhiều đời nâng ô lên tờ mới nhất, kể cả hai đời trong cùng một lượt")
def _thay_the_nhieu_doi():
	don = [_dthay("HDB-26-09-02861", "14159", "1C26MPV 14401")]
	viec, xd = ds.ke_hoach_thay_the([_to(16000, "2026-09-24", "Thay thế", 14401)], don)
	la("đời 2: ô đang ghi đúng tờ bị thay thì nâng", [(v["cu"], v["moi"]) for v in viec], [("1C26MPV 14401", "1C26MPV 16000")])
	don = [_dthay("HDB-26-09-01138", "12736")]
	viec, xd = ds.ke_hoach_thay_the([_to(16001, "2026-09-24", "Thay thế", 15439),
		_to(15439, "2026-09-22", "Thay thế", 12736)], don)
	la("hai đời trong một lượt: đi theo thứ tự ngày, điều kiện nối nhau",
		[(v["cu"], v["moi"]) for v in viec], [("", "1C26MPV 15439"), ("1C26MPV 15439", "1C26MPV 16001")])


@ca("v527 tờ thay thế về đơn: ô đã ghi tờ KHÁC hoặc tờ gốc khớp hai đơn thì không ghi, báo xung đột")
def _thay_the_xung_dot():
	viec, xd = ds.ke_hoach_thay_the([_to(15439, "2026-09-22", "Thay thế", 12736)],
		[_dthay("HDB-26-09-01138", "12736", "1C26MPV 99999")])
	la("không ghi đè", viec, [])
	dung("báo đang ghi tờ khác", len(xd) == 1 and "99999" in xd[0]["ly_do"])
	viec, xd = ds.ke_hoach_thay_the([_to(15439, "2026-09-22", "Thay thế", 12736)],
		[_dthay("A", "12736"), _dthay("B", "12736")])
	la("hai đơn cùng số: không chọn", (viec, len(xd)), ([], 1))
	viec, xd = ds.ke_hoach_thay_the([_to(15439, "2026-09-22", "Thay thế", 12736)],
		[_dthay("A", "12736", ky="1C26MVO")])
	la("đơn khác dải ký hiệu: không phải đơn gốc", (viec, xd), ([], []))
	viec, xd = ds.ke_hoach_thay_the([_to(15439, "2026-09-22", "Thay thế", 777)], [_dthay("A", "12736")])
	la("tờ gốc không có trong ERP: bỏ qua", (viec, xd), ([], []))


def _chay_noi_thay_the(to, don, chen=None):
	"""noi_thay_the_tu_dong THẬT; bảng đơn giả ghi có điều kiện như SQL thật."""
	hoi, ghi, nhat_ky = [], [], []
	kho = {d.name: dict(d) for d in don}

	def get_all(dt, filters=None, fields=None, limit_page_length=0):
		hoi.append((dt, dict(filters)))
		if dt == ds.DT_TO:
			return [_D(t) for t in to]
		return [_D(v) for v in _loc(list(kho.values()), filters)]

	def sql(cau, ts):
		# Bảng giả làm ĐÚNG câu ghi nhận được: câu có điều kiện ô cũ thì mới xét
		# (lần đầu bảng giả tự xét điều kiện nên đột biến bỏ điều kiện R6 không đổ).
		if chen:
			chen(kho)
		d = kho.get(ts["don"])
		co_dk = "ifnull(custom_hddt_thay_the, '') = %(cu)s" in cau
		if d and (not co_dk or (d.get("custom_hddt_thay_the") or "") == ts["cu"]):
			d["custom_hddt_thay_the"] = ts["moi"]
			ghi.append((ts["don"], ts["moi"]))

	class _Doc(dict):
		def insert(self, **k):
			nhat_ky.append((self["reference_name"], self["content"]))
	import frappe as _fr
	f = NS(get_all=get_all, throw=_fr.throw, log_error=lambda *a, **k: None, get_traceback=lambda: "",
		get_doc=lambda d: _Doc(d), db=NS(get_single_value=lambda *a: "1C26MPV", sql=sql, commit=lambda: None,
			rollback=lambda: None, get_value=lambda dt, n, fld: kho[n].get(fld)))
	with unittest.mock.patch.object(ds, "frappe", f), \
			unittest.mock.patch.object(ds, "getdate", lambda *a: datetime.date(2026, 9, 25)), \
			unittest.mock.patch.object(ds, "now_datetime", lambda: datetime.datetime(2026, 9, 25, 15, 0)):
		so_ghi = ds.noi_thay_the_tu_dong()
	return so_ghi, ghi, nhat_ky, hoi


@ca("v527 tờ thay thế về đơn (hàm thật): quét 30 ngày, ghi có điều kiện, để lại nhật ký trên đơn")
def _thay_the_that():
	to = [_to(15439, "2026-09-22", "Thay thế", 12736)]
	so_ghi, ghi, nk, hoi = _chay_noi_thay_the(to, [_dthay("HDB-26-09-01138", "12736")])
	la("ghi một đơn", (so_ghi, ghi), (1, [("HDB-26-09-01138", "1C26MPV 15439")]))
	dung("nhật ký nói rõ máy ghi theo m-invoice", len(nk) == 1 and "m-invoice" in nk[0][1] and "15439" in nk[0][1])
	loc_to = [h[1] for h in hoi if h[0] == ds.DT_TO][0]
	la("quét đúng 30 ngày ngày lập", str(loc_to["ngay_lap"][1]), "2026-08-26")
	la("chỉ tờ Thay thế", loc_to["trang_thai"], "Thay thế")

	def ke_toan_go_tay(kho):
		kho["HDB-26-09-01138"]["custom_hddt_thay_the"] = "1C26MPV 15439 (ke toan)"
	so_ghi, ghi, nk, _ = _chay_noi_thay_the(to, [_dthay("HDB-26-09-01138", "12736")], chen=ke_toan_go_tay)
	la("kế toán gõ tay chen vào giữa: máy không ghi đè, không nhật ký", (so_ghi, ghi, nk), (0, [], []))
	# Chạy lại lần hai trên dữ liệu đã ghi: không ghi gì thêm (idempotent).
	so_ghi, ghi, nk, _ = _chay_noi_thay_the(to, [_dthay("HDB-26-09-01138", "12736", "1C26MPV 15439")])
	la("lần hai không ghi lại", (so_ghi, nk), (0, []))


@ca("v527 nhịp 15 phút và nhịp đêm đều gọi ghi tờ thay thế, kể cả khi lượt kéo lỗi")
def _thay_the_nhip():
	from vagabond import minvoice_dong_bo as md
	goi = []
	f = NS(db=NS(exists=lambda *a: True), log_error=lambda *a, **k: None, get_traceback=lambda: "")
	for ten, keo_loi in (("dong_bo_tu_dong", False), ("dong_bo_tu_dong", True), ("tu_lanh_hang_dem", True)):
		goi.clear()

		def keo(**k):
			if keo_loi:
				raise RuntimeError("m-invoice 502")
		with unittest.mock.patch.object(md, "frappe", f), unittest.mock.patch.object(md, "_keo", keo), \
				unittest.mock.patch.object(ds, "noi_thay_the_tu_dong", lambda: goi.append(1) or 0):
			getattr(md, ten)()
		la("%s (kéo lỗi %s) gọi ghi tờ thay thế" % (ten, keo_loi), goi, [1])


@ca("v527 nối tay: tờ đã nối vào đơn đếm là ERP ghi nhận, ngày 21/09 hết lệch khi nối đủ 4 tờ tách")
def _noi_tay_dem():
	to = [dict(t, vgb_don_erp="HDB-26-09-03340") if t["so_hd"] in (15228, 15229, 15230, 15231) else t for t in TO]
	don = DON + [_don("HDB-26-09-09001", "15500", ngay="2026-09-21")]
	ket = ds.phan_loai(to, don)
	la("tờ tách xếp loại nối tay về đúng đơn", {ket["TO-%d" % n]["loai"] for n in (15228, 15229, 15230, 15231)},
		{ds.LOAI_NOI_TAY})
	d21 = [r for r in ds.tong_hop_ngay(to, ket) if r["ngay"] == "2026-09-21"][0]
	la("21/09: nối tay 4, lệch 0", (d21["noi_tay"], d21["lech"]), (4, 0))
	la("nút gỡ cho tờ đã nối, nút nối cho tờ tạo tay",
		(ds.nut_cua_dong(ket["TO-15228"], to[4])["lam"], ds.nut_cua_dong({"loai": ds.LOAI_TAO_TAY}, TO[4])["lam"]),
		("go", "noi"))
	la("tờ ERP phát hành không có nút", ds.nut_cua_dong({"loai": ds.LOAI_ERP}, TO[0]), None)


def _noi_that(xac_nhan=0, don_nhap="HDB-26-09-03340", tien_don=3800000, quyen=("Accounts User",), to_ten="TO-15231",
		dang_noi="", chen=None, erp_giu=""):
	"""noi_to_vao_don THẬT, dữ liệu 21/09 dựng lại (tiền giả)."""
	bang = {t["name"]: _D(dict(t, loai="Đầu ra", tong_tien=950000)) for t in TO if t["so_hd"] in (15228, 15229, 15230, 15231)}
	for n in (15228, 15229, 15230):
		bang["TO-%d" % n]["vgb_don_erp"] = "HDB-26-09-03340"
	bang[to_ten]["vgb_don_erp"] = dang_noi
	bang["TO-14634"] = _D(dict(_to(14634, "2026-09-18", "Bị thay thế", mst=MST_TACH), loai="Đầu ra", tong_tien=3800000))
	bang["TO-15217"] = _D(dict(_to(15217, "2026-09-21", "Thay thế", 14634, MST_TACH), loai="Đầu ra", tong_tien=0))
	si = _D(dict(_don("HDB-26-09-03340", "14634", "1C26MPV 15217", MST_TACH), docstatus=1, grand_total=tien_don,
		customer_name="Khách giả"))
	ghi, nk = [], []

	def get_value(dt, ten, fields=None, as_dict=False):
		if dt == "Sales Invoice":
			return si if ten == si.name else None
		t = bang.get(ten)
		if isinstance(fields, str):
			return t.get(fields) if t else None
		return t

	def get_all(dt, filters=None, fields=None, limit_page_length=0):
		if dt == "Sales Invoice":
			if filters.get("custom_pancake_display_id") == si.custom_pancake_display_id:
				return [si]
			# Đơn ERP đã phát hành tờ này, ghi mã m-invoice ở một trong hai ô.
			if erp_giu and filters.get(erp_giu) == to_ten:
				return [_D(name="HDB-ERP-GIU")]
			return []
		return _loc(list(bang.values()), {k: v for k, v in filters.items()})

	def sql(cau, ts):
		if chen:
			chen(bang)
		t = bang[ts["to"]]
		co_dk = "ifnull(vgb_don_erp, '') = ''" in cau
		if "set vgb_don_erp = %(don)s" in cau and (not co_dk or not t.get("vgb_don_erp")):
			t["vgb_don_erp"] = ts["don"]
			ghi.append(ts["to"])

	class _Doc(dict):
		def insert(self, **k):
			nk.append(self["content"])
	import frappe as _fr
	f = NS(get_roles=lambda: list(quyen), throw=_fr.throw, session=NS(user="dung@vagabond"),
		get_all=get_all, get_doc=lambda d: _Doc(d), log_error=lambda *a, **k: None,
		db=NS(get_value=get_value, get_single_value=lambda *a: "1C26MPV", sql=sql, commit=lambda: None))
	bh = NS(QUYEN_HDDT_THAY_THE={"System Manager", "Accounts Manager", "Accounts User"})
	with unittest.mock.patch.object(ds, "frappe", f), \
			unittest.mock.patch.object(ds, "now_datetime", lambda: datetime.datetime(2026, 9, 25, 15, 0)), \
			unittest.mock.patch.dict(__import__("sys").modules, {"vagabond.ban_hang": bh}):
		try:
			return ds.noi_to_vao_don(to=to_ten, don=don_nhap, xac_nhan=xac_nhan), ghi, nk
		except Exception as e:
			return {"loi": str(e)}, ghi, nk


@ca("v527 nối tay (hàm thật): xem trước không ghi, tính tiền các tờ còn hiệu lực, xác nhận mới ghi")
def _noi_tay_that():
	kq, ghi, nk = _noi_that()
	la("xem trước: không ghi gì", (ghi, nk), ([], []))
	la("tổng tờ còn hiệu lực: 15217 (0 đ) + 4 tờ tách, bỏ tờ gốc bị thay", kq["tong_to"], 3800000.0)
	la("khớp tiền đơn", (kq["lech"], kq["lech_qua_nguong"]), (0.0, 0))
	kq, ghi, nk = _noi_that(xac_nhan=1)
	la("xác nhận: ghi đúng tờ", ghi, ["TO-15231"])
	dung("nhật ký trên đơn nói số hoá đơn giữ nguyên", len(nk) == 1 and "15231" in nk[0] and "giữ nguyên" in nk[0])
	kq, ghi, nk = _noi_that(tien_don=2850000)
	la("nối nhầm làm vượt tiền đơn: báo lệch", (kq["lech"], kq["lech_qua_nguong"]), (950000.0, 1))


@ca("v527 nối tay (hàm thật): chặn người không phải kế toán, tờ đang nối đơn khác, tờ ERP tự phát hành")
def _noi_tay_chan():
	kq, ghi, _ = _noi_that(xac_nhan=1, quyen=("Sales User",))
	dung("sales không nối được", "kế toán" in kq.get("loi", "") and ghi == [])
	kq, ghi, _ = _noi_that(xac_nhan=1, dang_noi="HDB-KHAC")
	dung("đang nối đơn khác thì phải gỡ trước", "Gỡ nối trước" in kq.get("loi", "") and ghi == [])
	kq, ghi, _ = _noi_that(xac_nhan=1, to_ten="TO-15231", don_nhap="P-3340")
	la("nhập mã đơn bán (Pancake) cũng tìm được đơn", ghi, ["TO-15231"])
	kq, ghi, _ = _noi_that(xac_nhan=1, dang_noi="HDB-26-09-03340")
	dung("đã nối đúng đơn: trả lời đã nối, không ghi lần hai", kq.get("da_noi") == 1 and ghi == [])

	def nguoi_khac_noi_truoc(bang):
		bang["TO-15231"]["vgb_don_erp"] = "HDB-KHAC"
	kq, ghi, nk = _noi_that(xac_nhan=1, chen=nguoi_khac_noi_truoc)
	dung("người khác nối chen giữa lúc xem và lúc ghi: không đè, báo rõ",
		ghi == [] and "người khác" in kq.get("loi", "") and nk == [])


def _bam_bc(kq, nut, hoi_chu, hoi_co=True, tra_xem=None):
	"""Vẽ BC17 thật trong node, bấm nút trên bảng phụ, trả các lời gọi API."""
	import json
	import subprocess
	goc = GOC / "public" / "js" / "bep"

	def cat(tep, ten):
		import re
		m = re.search(r"\nfunction %s\([^)]*\) ?\{.*?\n\}" % ten, (goc / tep).read_text(encoding="utf-8"), re.S)
		if not m:
			m = re.search(r"\nfunction %s\([^\n]*\n" % ten, (goc / tep).read_text(encoding="utf-8"))
		return m.group(0)
	nen = cat("00-nen.js", "h") + cat("00-nen.js", "money") + cat("09-tinh-tien-quay.js", "posChipNut") + \
		cat("13-khuyen-mai.js", "kmHangChip") + cat("09-tinh-tien-quay.js", "posNgayVn")
	man = (goc / "14-bao-cao.js").read_text(encoding="utf-8")
	kich = r"""
const vm = require('vm');
const ghi = { html: [], api: [], toast: [], bao: [], go: [] };
let khung = null;
const ctx = { console: console, setTimeout: setTimeout,
  document: { getElementById: function () { return { onclick: null }; } },
  frame: function (t, b) { ghi.html.push(b); khung = { onclick: null, querySelector: function () { return null; } }; return khung; },
  api: async function (m, a) { ghi.api.push([m, a || {}]);
    if (m === 'vagabond.bao_cao.chay') return __KQ__;
    if (a && a.xac_nhan === 0) return __XEM__;
    return { loi_nhan: 'xong' }; },
  hoiChu: async function () { return __CHU__; }, hoiCo: async function () { return __CO__; },
  baoTin: function (x) { ghi.bao.push(x); }, today: function () { return '2026-09-21'; },
  go: function (f) { ghi.go.push(f && f.name); }, busy: function () {}, toast: function (x) { ghi.toast.push(x); } };
vm.createContext(ctx);
vm.runInContext(__NEN__, ctx);
vm.runInContext(__MAN__, ctx);
vm.runInContext("bcMa = 'BC17';", ctx);
(async function () {
  await ctx.scrBaoCaoXem();
  const html = ghi.html[ghi.html.length - 1];
  const THUOC = __NUT__;
  const m = html.match(new RegExp('<button[^>]*' + THUOC + '="[^"]*"[^>]*>'));
  let bam = 'khong_thay_nut';
  if (m) {
    const the = m[0];
    const el = { getAttribute: function (k) { const r = the.match(new RegExp(k + '="([^"]*)"')); return r ? r[1] : null; } };
    await khung.onclick({ target: { closest: function (sel) { return sel === '[' + THUOC + ']' ? el : null; } } });
    bam = 'da_bam';
  }
  process.stdout.write(JSON.stringify({ html: html, api: ghi.api, toast: ghi.toast, bao: ghi.bao, bam: bam, go: ghi.go }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	for k, v in (("__KQ__", kq), ("__XEM__", tra_xem or {}), ("__CHU__", hoi_chu), ("__CO__", hoi_co), ("__NUT__", nut)):
		kich = kich.replace(k, json.dumps(v))
	kich = kich.replace("__NEN__", json.dumps(nen)).replace("__MAN__", json.dumps(man))
	r = subprocess.run(["node", "-e", kich], capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("node lỗi: " + (r.stderr or "").strip()[:500])
	return json.loads(r.stdout)


def _kq_bc17_nut():
	return _kq_man(khong_loc=1, nguon_loc=[], pt_loc=[], phu={"tieu_de": "Tờ lập thẳng",
		"cot": [{"k": "so_hd", "nhan": "Số", "kieu": "chu"}], "tong_dong": 2, "bi_cat": 0, "gioi_han": 600,
		"dong": [{"so_hd": "15231", "_nut": {"lam": "noi", "to": "TO-15231", "so": "15231", "goi_y": "HDB-26-09-03340"}},
			{"so_hd": "15228", "_nut": {"lam": "go", "to": "TO-15228", "so": "15228", "don": "HDB-26-09-03340"}}]})


@ca("v527 nối tay trên màn thật: bảng phụ có nút, bấm Nối thì xem trước rồi mới ghi, bấm Thôi thì không ghi")
def _noi_tay_man():
	xem = {"to": "TO-15231", "so": "15231", "don": "HDB-26-09-03340", "ma_don": "94132", "khach": "Khách",
		"tien_don": 3800000, "tong_to": 3800000, "lech": 0, "lech_qua_nguong": 0, "cac_to": [{}, {}, {}, {}, {}]}
	ra = _bam_bc(_kq_bc17_nut(), "data-bcnoi", "HDB-26-09-03340", True, xem)
	la("có bấm", ra["bam"], "da_bam")
	goi = [(m, a.get("xac_nhan"), a.get("don")) for m, a in ra["api"] if m != "vagabond.bao_cao.chay"]
	la("xem trước rồi xác nhận, đúng đơn",
		goi, [("vagabond.doi_soat_hddt_ra.noi_to_vao_don", 0, "HDB-26-09-03340"),
			("vagabond.doi_soat_hddt_ra.noi_to_vao_don", 1, "HDB-26-09-03340")])
	la("vẽ lại báo cáo sau khi nối", ra["go"], ["scrBaoCaoXem"])
	ra = _bam_bc(_kq_bc17_nut(), "data-bcnoi", "HDB-26-09-03340", False, xem)
	la("bấm Thôi ở bước xác nhận: chỉ xem trước", [a.get("xac_nhan") for m, a in ra["api"] if "doi_soat" in m], [0])
	ra = _bam_bc(_kq_bc17_nut(), "data-bcgo", "nối nhầm đơn", True)
	la("gỡ gửi lý do", [(m, a.get("ly_do")) for m, a in ra["api"] if "doi_soat" in m],
		[("vagabond.doi_soat_hddt_ra.go_to_khoi_don", "nối nhầm đơn")])
	# Bảng chính không có nút; nút không phải cột nên Excel không in.
	dung("bảng chính không có nút", ra["html"].count("data-bcnoi") == 1 and ra["html"].count("data-bcgo") == 1)


# ---------------------------------------------- Codex vòng 3 (#369) trên cbff7e2


@ca("v527 Codex H3: tờ ERP tự phát hành ghi mã ở ô custom_hddt_id (đường cũ) cũng không nối tay được")
def _h3_hai_o_ma():
	for o in ("custom_minvoice_id", "custom_hddt_id"):
		kq, ghi, nk = _noi_that(xac_nhan=1, erp_giu=o)
		dung("mã ở %s: chặn, không ghi" % o, "ERP tự phát hành" in kq.get("loi", "") and ghi == [] and nk == [])


def _go_that(chen=None):
	bang = {"TO-15231": _D(name="TO-15231", so_hd=15231, vgb_don_erp="HDB-26-09-03340")}
	nk = []

	def sql(cau, ts):
		if chen:
			chen(bang)
		t = bang[ts["to"]]
		if "vgb_don_erp = %(cu)s" not in cau or t.get("vgb_don_erp") == ts["cu"]:
			t["vgb_don_erp"] = None

	def get_value(dt, ten, fields=None, as_dict=False):
		t = bang.get(ten)
		if isinstance(fields, str):
			return t.get(fields) if t else None
		return t

	class _Doc(dict):
		def insert(self, **k):
			nk.append(self["content"])
	import frappe as _fr
	f = NS(get_roles=lambda: ["Accounts User"], throw=_fr.throw, session=NS(user="dung@vagabond"),
		get_doc=lambda d: _Doc(d), log_error=lambda *a, **k: None,
		db=NS(get_value=get_value, sql=sql, commit=lambda: None))
	bh = NS(QUYEN_HDDT_THAY_THE={"Accounts User"})
	with unittest.mock.patch.object(ds, "frappe", f), \
			unittest.mock.patch.dict(__import__("sys").modules, {"vagabond.ban_hang": bh}):
		try:
			return ds.go_to_khoi_don(to="TO-15231", ly_do="nối nhầm"), bang, nk
		except Exception as e:
			return {"loi": str(e)}, bang, nk


@ca("v527 Codex H4: gỡ nối mà người khác vừa nối sang đơn khác thì báo rõ, không ghi nhật ký gỡ sai")
def _h4_go_chen_ngang():
	kq, bang, nk = _go_that()
	la("gỡ thường: gỡ được, một dòng nhật ký", (kq.get("ok"), bang["TO-15231"]["vgb_don_erp"], len(nk)), (1, None, 1))

	def nguoi_khac(bang):
		bang["TO-15231"]["vgb_don_erp"] = "HDB-KHAC"
	kq, bang, nk = _go_that(chen=nguoi_khac)
	dung("chen ngang: báo lỗi", "người khác" in kq.get("loi", ""))
	la("liên kết mới còn nguyên, không nhật ký", (bang["TO-15231"]["vgb_don_erp"], nk), ("HDB-KHAC", []))


@ca("v527 Codex H2: BC17 luôn chỉ tính đơn đã ghi sổ, màn không bày công tắc đơn chưa ghi sổ")
def _h2_nhap():
	kq, hoi = _chay_bc("BC17", nhap=1)
	la("bật công tắc vẫn chỉ đơn đã ghi sổ", kq["nhap"], 0)
	kq, hoi = _chay_bc("BC05", nhap=1)
	la("đối chứng BC05: công tắc vẫn có tác dụng", kq["nhap"], 1)
	ra = _ve_bc(_kq_man(khong_loc=1, nhap=0, nguon_loc=[], pt_loc=[]))
	dung("BC17: không có chip đơn chưa ghi sổ", "data-bcnhap" not in ra["html"])
	ra = _ve_bc(_kq_man(ma="BC05", khong_loc=0))
	dung("đối chứng BC05: còn chip", "data-bcnhap" in ra["html"])

