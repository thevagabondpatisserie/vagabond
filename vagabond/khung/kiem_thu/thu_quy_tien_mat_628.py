# -*- coding: utf-8 -*-
"""v628: Quỹ tiền mặt công ty (anh Việt duyệt ảnh mẫu 4 màn ngày 02/11/2026).

Kiểm quỹ theo mệnh giá, lệch thì bút toán chênh lệch, lệch quá 2 triệu chờ Giám đốc
duyệt; nộp tiền mặt vào ngân hàng ghép giao dịch SePay. Ca chạm hệ chạy HÀM THẬT, chỉ
thay tầng Frappe, bút toán và kênh Zalo bằng bản giả ghi lại lời gọi.
"""

import ast
import datetime as dt
import re
import sys
import unittest.mock as um
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import quy_tien_mat as q  # noqa: E402
from vagabond import tai_chinh as tc  # noqa: E402
from vagabond import tin_tai_chinh as ttc  # noqa: E402
from vagabond.patches import v628_tin_tai_chinh as pv  # noqa: E402

GOI = Path(__file__).resolve().parents[2]
D = dt.date


def _khong_gach(nhan, chu):
	dung(nhan + ": không có em dash, en dash", "—" not in chu and "–" not in chu)


@ca("v628 quỹ: bảng đếm mệnh giá cộng đúng, bỏ ô trống, chặn số tờ âm, chữ, mệnh giá lạ")
def _bang_dem():
	dong, tong, loi = q.doc_bang_dem({"500000": "85", "200000": "1", "100000": "", "50000": "0"})
	la("hai dòng, lớn trước", [(x["menh_gia"], x["so_to"]) for x in dong], [(500000, 85), (200000, 1)])
	la("tổng", (tong, loi), (42700000.0, ""))
	la("nhận cả JSON", q.doc_bang_dem('{"1000": "3"}')[1], 3000.0)
	dung("số âm bị chặn", "số nguyên không âm" in q.doc_bang_dem({"500000": "-2"})[2])
	dung("chữ bị chặn", "số nguyên không âm" in q.doc_bang_dem({"500000": "a"})[2])
	dung("mệnh giá lạ bị chặn", "không có trong danh mục" in q.doc_bang_dem({"300000": "1"})[2])
	dung("JSON hỏng", "không đọc được" in q.doc_bang_dem("{hỏng")[2])


@ca("v628 quỹ: lệch dưới 1 đồng là khớp; quá 2.000.000 mới chờ duyệt, đúng 2.000.000 thì ghi ngay")
def _lech():
	la("khớp", q.phan_loai_lech(45200000, 45200000.4), {"lech": 0, "loai": "khop", "can_duyet": 0})
	la("thiếu nhỏ", q.phan_loai_lech(45200000, 45050000), {"lech": -150000, "loai": "thieu", "can_duyet": 0})
	la("thiếu đúng 2 triệu", q.phan_loai_lech(45200000, 43200000)["can_duyet"], 0)
	la("thiếu 2,5 triệu", q.phan_loai_lech(45200000, 42700000), {"lech": -2500000, "loai": "thieu", "can_duyet": 1})
	la("thừa 2.000.001", q.phan_loai_lech(0, 2000001)["can_duyet"], 1)
	la("ngưỡng là số anh Việt chốt", q.NGUONG_DUYET, 2000000)


@ca("v628 quỹ: bút toán thiếu Nợ TK thiếu Có quỹ; thừa Nợ quỹ Có TK thừa; nộp Nợ ngân hàng Có quỹ")
def _but_toan():
	la("thiếu", q.dong_but_toan_lech(-150000, "1111", "1381", "3381"),
		[{"tk": "1381", "no": 150000, "co": 0}, {"tk": "1111", "no": 0, "co": 150000}])
	la("thừa", q.dong_but_toan_lech(50000, "1111", "1381", "3381"),
		[{"tk": "1111", "no": 50000, "co": 0}, {"tk": "3381", "no": 0, "co": 50000}])
	la("khớp không có dòng", q.dong_but_toan_lech(0, "1111", "1381", "3381"), [])
	la("nộp", q.dong_but_toan_nop(20000000, "1121 MB", "1111"),
		[{"tk": "1121 MB", "no": 20000000, "co": 0}, {"tk": "1111", "no": 0, "co": 20000000}])


@ca("v628 quỹ: chặn phiếu nộp vượt quỹ, quỹ chưa chốt, ngày sau hôm nay, ngày không sau mốc")
def _kiem_nop():
	hom = D(2026, 11, 2)
	la("hợp lệ", q.kiem_nop(20000000, 45200000, hom, D(2026, 10, 31), hom), "")
	dung("vượt quỹ", "Quỹ chỉ còn" in q.kiem_nop(50000000, 45200000, hom, D(2026, 10, 31), hom))
	dung("chưa chốt", "chưa chốt" in q.kiem_nop(1, None, hom, None, hom))
	dung("số 0", "Gõ số tiền" in q.kiem_nop(0, 1, hom, None, hom))
	dung("ngày mai", "sau hôm nay" in q.kiem_nop(1, 5, D(2026, 11, 3), None, hom))
	dung("ngày mốc", "không sau mốc chốt" in q.kiem_nop(1, 5, D(2026, 10, 31), D(2026, 10, 31), hom))


@ca("v628 quỹ: ghép SePay đúng tài khoản, đúng số (lệch tối đa 1 đồng), trong 3 ngày, bỏ khoản đã có chủ, lấy khoản sớm nhất")
def _ghep():
	p = {"ngay": "2026-11-01", "so_tien": 20000000, "bank_account": "MB"}
	gd = [
		{"ten": "BT-1", "bank_account": "SHB", "deposit": 20000000, "date": "2026-11-01", "creation": "1"},
		{"ten": "BT-2", "bank_account": "MB", "deposit": 19999000, "date": "2026-11-01", "creation": "1"},
		{"ten": "BT-3", "bank_account": "MB", "deposit": 20000000, "date": "2026-10-31", "creation": "1"},
		{"ten": "BT-4", "bank_account": "MB", "deposit": 20000000, "date": "2026-11-05", "creation": "1"},
		{"ten": "BT-5", "bank_account": "MB", "deposit": 20000000.5, "date": "2026-11-03", "creation": "2"},
		{"ten": "BT-6", "bank_account": "MB", "deposit": 20000000, "date": "2026-11-02", "creation": "9"},
	]
	la("sớm nhất hợp lệ", q.chon_gd_khop(p, gd), "BT-6")
	la("BT-6 có chủ thì sang BT-5", q.chon_gd_khop(p, gd, {"BT-6"}), "BT-5")
	la("không còn khoản nào", q.chon_gd_khop(p, gd, {"BT-6", "BT-5"}), "")
	la("nhận ngày kiểu date", q.chon_gd_khop({"ngay": D(2026, 11, 1), "so_tien": 1, "bank_account": "MB"},
		[{"ten": "X", "bank_account": "MB", "deposit": 1, "date": D(2026, 11, 4)}]), "X")


@ca("v628 quỹ: chữ tin Zalo lệch chờ duyệt, nộp chưa khớp, dòng tin cuối ngày; không em dash")
def _chu():
	td, dong = q.soan_lech_cho_duyet({"lech": -2500000, "so_may": 45200000, "so_dem": 42700000, "ly_do": "chi_chua_nhap",
		"ghi_chu": "Trả tiền ga", "luc": "2026-11-02 16:30:00"}, "Ngô Hoàng Ngọc Dung")
	la("tiêu đề", td, "Kiểm quỹ thiếu 2.500.000 đ, chờ giám đốc duyệt")
	la("dòng", dong[:3], ["Ngô Hoàng Ngọc Dung kiểm quỹ tiền mặt công ty lúc 16:30",
		"Máy tính: 45.200.000 đ · Đếm được: 42.700.000 đ", "Lý do: Chi chưa nhập app · \"Trả tiền ga\""])
	td2, dong2 = q.soan_nop_chua_khop([{"name": "PQ-26-11-00001", "so_tien": 20000000, "ten_tai_khoan": "MB Bank ···1568", "ngay": "2026-11-01"}])
	la("dòng đầu", dong2[0], "1 phiếu, tổng 20.000.000 đ, quá 2 ngày chưa khớp SePay")
	la("dòng phiếu", dong2[1], "PQ-26-11-00001 · 20.000.000 đ · MB Bank ···1568 · nộp 01/11")
	cn = q.dong_cuoi_ngay([{"luc": "2026-11-02 10:00:00", "lech": 0}, {"luc": "2026-11-02 16:30:00", "lech": -150000, "ly_do": "chi_chua_nhap",
		"trang_thai": "Đã ghi"}, {"luc": "2026-11-02 17:00:00", "lech": -2500000, "ly_do": "chua_ro", "trang_thai": "Chờ duyệt"}])
	la("cuối ngày", cn, ["Kiểm quỹ 10:00: khớp", "Kiểm quỹ 16:30: thiếu 150.000 đ (Chi chưa nhập app)",
		"Kiểm quỹ 17:00: thiếu 2.500.000 đ (Chưa rõ), chờ duyệt"])
	for x in [td] + dong + [td2] + dong2 + cn:
		_khong_gach("tin quỹ", x)


@ca("v628 quỹ: tin Tiền cuối ngày mang dòng kiểm quỹ trong ngày (lệch nhỏ ghi ngay vẫn tới Ban giám đốc)")
def _cuoi_ngay():
	td, dong = ttc.soan_cuoi_ngay("2026-11-02", {"tong": {"tong": 1}, "dong": []}, None,
		[{"luc": "2026-11-02 16:30:00", "lech": -150000, "ly_do": "dem_sai", "trang_thai": "Đã ghi"}])
	la("dòng cuối", dong[-1], "Kiểm quỹ 16:30: thiếu 150.000 đ (Lần trước đếm sai)")
	td0, dong0 = ttc.soan_cuoi_ngay("2026-11-02", {"tong": {"tong": 1}, "dong": []}, None)
	dung("không kiểm thì không có dòng", not any("Kiểm quỹ" in x for x in dong0))


@ca("v628 quỹ: một nguồn tính quỹ: Tiền hiện có và màn Quỹ cùng gọi tai_chinh.tinh_quy, không chỗ nào tự cộng sổ cái quỹ")
def _mot_nguon():
	goi = {}
	for tep in ("tai_chinh.py", "quy_tien_mat.py", "tin_tai_chinh.py"):
		cay = ast.parse((GOI / tep).read_text(encoding="utf-8"))
		for n in ast.walk(cay):
			if isinstance(n, ast.Call):
				f = n.func
				ten = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
				if ten in ("_so_cai_quy", "tinh_quy", "_nop_quy"):
					cha = [x.name for x in ast.walk(cay) if isinstance(x, ast.FunctionDef) and n in list(ast.walk(x))]
					goi.setdefault(ten, set()).add("%s:%s" % (tep, cha[-1] if cha else "?"))
	la("sổ cái quỹ chỉ đọc trong tinh_quy", goi.get("_so_cai_quy"), {"tai_chinh.py:tinh_quy"})
	dung("Tiền hiện có gọi tinh_quy", "tai_chinh.py:_tinh_tien" in goi.get("tinh_quy", set()))
	dung("màn Quỹ gọi tinh_quy", "quy_tien_mat.py:_so_quy" in goi.get("tinh_quy", set()))


class _Doc(dict):
	def __init__(self, d):
		super().__init__(d)
		self.name = "PQ-26-11-00001"
		self.flags = NS()

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		# Như Document thật: gán thuộc tính là gán trường, doc.get đọc lại được.
		if k in ("name", "flags"):
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def insert(self, **k):
		_VET.append(("insert", self.get("trang_thai")))
		return self

	def db_set(self, k, v, **kw):
		self[k] = v

	def as_dict(self):
		return dict(self)

	def save(self, **k):
		_VET.append(("save", self.get("trang_thai")))


_VET = []


def _vat_kiem(so_may=45200000, ngay_chot="2026-10-31", tk=("1111", "1381", "3381")):
	zalo, je = [], []
	vat = [
		um.patch.object(q, "_kiem_lam", lambda: None), um.patch.object(q, "_khoa_quy", lambda: None),
		um.patch.object(q, "_so_quy", lambda: (so_may, {"ngay_chot": ngay_chot, "so_du": 1})),
		um.patch.object(q, "_tk_dung", lambda k: dict(zip(("tk_quy", "tk_thieu", "tk_thua"), tk))[k]),
		um.patch.object(q, "_ten", lambda u: "Dung"), um.patch.object(q, "nowdate", lambda: "2026-11-02"),
		um.patch.object(q, "_lap_but_toan", lambda dong, ngay, dg: je.append((dong, str(ngay), dg)) or "ACC-JV-1"),
		um.patch.object(_fr, "get_doc", lambda d, *a: _Doc(d)),
		um.patch.object(_fr, "session", NS(user="dung@x")),
		um.patch.object(kz, "bao_hoac_ghi_loi", lambda *a, **k: zalo.append((a, k))),
	]
	from vagabond import tep_dinh_kem
	vat.append(um.patch.object(tep_dinh_kem, "gan_vao", lambda *a, **k: []))
	return vat, zalo, je


def _chay(vat, ham):
	for v in vat:
		v.start()
	try:
		return ham()
	finally:
		for v in vat:
			v.stop()


@ca("v628 kiểm quỹ chạy thật: thiếu 150.000 ghi bút toán ngay, không tin chờ duyệt; lệch 2,5 triệu chờ duyệt, có tin Ban giám đốc, chưa bút toán")
def _kiem_that():
	_VET.clear()
	vat, zalo, je = _vat_kiem()
	kq = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "90", "50000": "1"}', ly_do="chi_chua_nhap", ghi_chu="gửi xe"))
	la("lệch nhỏ (đếm 45.050.000, máy 45.200.000)", (kq["trang_thai"], kq["lech"]), ("Đã ghi", -150000))
	la("bút toán thiếu", je[0][0], [{"tk": "1381", "no": 150000, "co": 0}, {"tk": "1111", "no": 0, "co": 150000}])
	dung("diễn giải có lý do", "Chi chưa nhập app" in je[0][2])
	la("không tin", zalo, [])
	vat, zalo, je = _vat_kiem()
	kq = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "85", "200000": "1"}', ly_do="chi_chua_nhap", ghi_chu="ga"))
	la("lệch lớn", (kq["trang_thai"], kq["lech"]), ("Chờ duyệt", -2500000))
	la("chưa bút toán", je, [])
	la("một tin, mã đúng", [k["ma_tin"] for a, k in zalo], ["bgd_kiem_quy_lech"])
	la("tiêu đề", zalo[0][0][2], "Kiểm quỹ thiếu 2.500.000 đ, chờ giám đốc duyệt")
	vat, zalo, je = _vat_kiem()
	kq = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "90", "200000": "1"}'))
	la("khớp: không lý do, không bút toán", (kq["trang_thai"], je, zalo), ("Khớp", [], []))


@ca("v628 kiểm quỹ chạy thật: lệch mà thiếu lý do, Chưa rõ không ghi chú, mốc chốt hôm nay, thiếu tài khoản thì chặn")
def _kiem_chan():
	vat, zalo, je = _vat_kiem()
	nem("thiếu lý do", lambda: _chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}')))
	vat, zalo, je = _vat_kiem()
	nem("chưa rõ không ghi chú", lambda: _chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}', ly_do="chua_ro")))
	vat, zalo, je = _vat_kiem(ngay_chot="2026-11-02")
	nem("mốc hôm nay", lambda: _chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}', ly_do="dem_sai")))
	vat, zalo, je = _vat_kiem(tk=("1111", "", "3381"))
	nem("thiếu TK thiếu", lambda: _chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}', ly_do="dem_sai")))
	vat, zalo, je = _vat_kiem(so_may=None)
	nem("chưa chốt quỹ", lambda: _chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}', ly_do="dem_sai")))
	la("không bút toán nào", je, [])


@ca("v628 duyệt kiểm quỹ: người kiểm không tự duyệt; Giám đốc duyệt thì bút toán thiếu; trả lại phải có lý do")
def _duyet():
	je = []
	phieu = {}

	def doc_moi():
		d = _Doc({"loai": q.KIEM, "trang_thai": "Chờ duyệt", "nguoi": "dung@x", "lech": -2500000, "ly_do": "chi_chua_nhap"})
		phieu["d"] = d
		return d
	vat = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "get_doc", lambda *a: doc_moi()),
		um.patch.object(_fr.db, "sql", lambda *a, **k: []), um.patch.object(q, "nowdate", lambda: "2026-11-02"),
		um.patch.object(q, "_tk_dung", lambda k: {"tk_quy": "1111", "tk_thieu": "1381", "tk_thua": "3381"}[k]),
		um.patch.object(q, "_lap_but_toan", lambda dong, ngay, dg: je.append(dong) or "ACC-JV-2")]
	_chay(vat + [um.patch.object(_fr, "session", NS(user="dung@x"))],
		lambda: nem("tự duyệt", lambda: q.duyet_kiem_quy("PQ-1", 1)))
	la("tự duyệt không bút toán", je, [])
	kq = _chay(vat + [um.patch.object(_fr, "session", NS(user="viet@x"))], lambda: q.duyet_kiem_quy("PQ-1", 1))
	la("đã ghi", (kq["trang_thai"], kq["but_toan"]), ("Đã ghi", "ACC-JV-2"))
	la("bút toán thiếu", je[0], [{"tk": "1381", "no": 2500000, "co": 0}, {"tk": "1111", "no": 0, "co": 2500000}])
	_chay(vat + [um.patch.object(_fr, "session", NS(user="viet@x"))],
		lambda: nem("trả lại không lý do", lambda: q.duyet_kiem_quy("PQ-1", 0, "")))
	kq = _chay(vat + [um.patch.object(_fr, "session", NS(user="viet@x"))], lambda: q.duyet_kiem_quy("PQ-1", 0, "Đếm lại"))
	la("trả lại", (kq["trang_thai"], phieu["d"]["ly_do_tra"]), ("Trả lại", "Đếm lại"))


@ca("v628 nộp ngân hàng chạy thật: ghép giao dịch không có chủ, bỏ khoản bill đang giữ")
def _khop_that():
	ghi = []
	phieu = [NS(name="PQ-1", ngay="2026-11-01", so_tien=20000000, bank_account="MB")]
	gd = [NS(ten="BT-9", bank_account="MB", deposit=20000000, date="2026-11-01", creation="1", mo_ta="SOL3D4A9", tham_chieu="FT1"),
		NS(ten="BT-10", bank_account="MB", deposit=20000000, date="2026-11-02", creation="2", mo_ta="NOP TIEN MAT", tham_chieu="FT2")]
	for g in gd:
		g.get = lambda k, d=None, g=g: getattr(g, k, d)
	for p in phieu:
		p.get = lambda k, d=None, p=p: getattr(p, k, d)
	# Không import ban_hang thật: đầu tệp đó kéo thư viện mạng (thu_ma_vach). Thay bằng
	# mô đun giả chỉ có phép hỏi chủ toàn hệ.
	import vagabond
	bh = NS(_gd_co_chu_toan_he=lambda ds, *a, **k: {"BT-9": "hoá đơn bán HDB-1"})
	# Câu đọc sao kê trả gd; các câu khoá dòng (Codex #527 vòng 2) không thấy phiếu nào khác giữ.
	vat = [um.patch.object(_fr, "get_all", lambda *a, **k: phieu),
		um.patch.object(_fr.db, "sql", lambda cau, *a, **k: gd if "where docstatus=1" in cau else []),
		um.patch.object(vagabond, "ban_hang", bh, create=True), um.patch.dict(sys.modules, {"vagabond.ban_hang": bh}),
		um.patch.object(_fr.db, "set_value", lambda dt_, n, v, *a, **k: ghi.append((n, v["gd_sepay"], v["trang_thai"])))]
	so = _chay(vat, lambda: q.khop_nop_ngan_hang())
	la("ghép BT-10, bỏ BT-9 đang có chủ", (so, ghi), (1, [("PQ-1", "BT-10", "Đã khớp")]))


@ca("v628 quỹ: phiếu nộp ngân hàng giữ giao dịch, bill và luồng khác hỏi chủ toàn hệ thấy")
def _chu_toan_he():
	from vagabond import doi_soat_sepay as dss
	goi = []

	def get_all(dt_, filters=None, fields=None, **k):
		goi.append(dt_)
		if dt_ == "Vagabond Phieu Quy":
			return [{"name": "PQ-1", "gd_sepay": "BT-10"}]
		return []
	vat = [um.patch.object(_fr, "get_all", get_all), um.patch.object(dss, "nap_so", lambda: None),
		um.patch.dict(dss._SO, {}, clear=True)]
	from vagabond import bo_sao_ke_db as bs
	vat.append(um.patch.object(bs, "_cac_bo", lambda ma: []))
	ra = _chay(vat, lambda: dss.chu_cua_giao_dich(["BT-10", "BT-11"]))
	la("BT-10 thuộc phiếu quỹ", ra, {"BT-10": "phiếu nộp tiền mặt vào ngân hàng PQ-1"})


@ca("v628 quỹ: hai tin mới có trong danh mục Zalo, bản Desk và app giống nhau, bản vá tích cho nhóm mốc")
def _tin():
	for ma, bp in (("bgd_kiem_quy_lech", "Ban giám đốc"), ("kt_nop_nh_chua_khop", "Hoá đơn, kế toán")):
		la("bộ phận " + ma, kz.TIN[ma][0], bp)
	js = (GOI / "public" / "js" / "cai_dat_loi_chung.js").read_text(encoding="utf-8")
	for ma in ("bgd_kiem_quy_lech", "kt_nop_nh_chua_khop"):
		m = re.search(r"\n\t" + ma + r": \['([^']*)', '([^']*)', '([^']*)'\]", js)
		dung("JS có " + ma, bool(m))
		la("JS trùng " + ma, m.groups(), kz.TIN[ma][:3])
	dung("nhóm Ban giám đốc nhận tin lệch", "bgd_kiem_quy_lech" in pv.tin_them("bgd_bao_cao_ngay"))
	dung("nhóm kế toán nhận tin nộp chưa khớp", "kt_nop_nh_chua_khop" in pv.tin_them("hd_dau_vao"))


# ------------------------------------------------ Codex #527 vòng 2 (SHA 204b484d2)


def _vat_hai_lan(so_may=10000000):
	"""Kiểm quỹ hai lần liên tiếp trên CÙNG một số máy (phiếu trước chưa duyệt nên
	số máy chưa đổi). Bộ nhớ phiếu giả dùng chung cho get_all, set_value, get_doc."""
	kho = {}
	dem = {"n": 0}

	class _DocKho(_Doc):
		def insert(self, **k):
			dem["n"] += 1
			object.__setattr__(self, "name", "PQ-26-11-%05d" % dem["n"])
			self.setdefault("luc", "2026-11-02 10:%02d:00" % dem["n"])
			kho[self.name] = self
			return self

	def get_all(dt_, filters=None, fields=None, **k):
		if dt_ != q.DT:
			return []
		ra = []
		for n, d in kho.items():
			ok = True
			for kk, v in (filters or {}).items():
				x = d.get(kk) if kk != "name" else n
				if isinstance(v, (list, tuple)) and v[0] == "!=":
					ok = ok and x != v[1]
				elif isinstance(v, (list, tuple)) and v[0] == ">":
					ok = ok and str(x) > str(v[1])
				elif isinstance(v, (list, tuple)) and v[0] == "in":
					ok = ok and x in v[1]
				else:
					ok = ok and x == v
			if ok:
				ra.append(NS(name=n, **{kk: d.get(kk) for kk in ("trang_thai", "luc", "lech")}))
		return ra

	def set_value(dt_, n, a, b=None, **k):
		kho[n].update(a if isinstance(a, dict) else {a: b})

	def get_doc(d, *a):
		if isinstance(d, dict):
			return _DocKho(d)
		return kho[a[0]] if a else kho[d]
	vat, zalo, je = _vat_kiem(so_may=so_may)
	vat = [v for v in vat if getattr(v, "attribute", "") != "get_doc"]
	vat += [um.patch.object(_fr, "get_doc", get_doc), um.patch.object(_fr, "get_all", get_all),
		um.patch.object(_fr.db, "set_value", set_value), um.patch.object(_fr.db, "sql", lambda *a, **k: [])]
	return vat, kho, je


@ca("v628 Codex #527 vòng 2: kiểm lại khi phiếu lệch trước còn chờ duyệt thì phiếu trước bị thay, không ghi sổ hai lần")
def _codex_cho_duyet_trung():
	vat, kho, je = _vat_hai_lan()
	bang = '{"500000": "14"}'  # 7.000.000, máy 10.000.000: thiếu 3.000.000
	a = _chay(vat, lambda: q.kiem_quy(bang=bang, ly_do="chua_ro", ghi_chu="đếm lần một"))
	b = _chay(vat, lambda: q.kiem_quy(bang=bang, ly_do="chua_ro", ghi_chu="đếm lần hai"))
	la("lần hai vẫn chờ duyệt", b["trang_thai"], "Chờ duyệt")
	la("phiếu lần một không còn chờ duyệt", kho[a["name"]]["trang_thai"], "Đã thay")
	dung("phiếu lần một ghi rõ bị phiếu nào thay", b["name"] in (kho[a["name"]].get("ly_do_tra") or ""))
	duyet = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "session", NS(user="viet@x"))]
	_chay(vat + duyet, lambda: nem("duyệt phiếu đã bị thay", lambda: q.duyet_kiem_quy(a["name"], 1)))
	kq = _chay(vat + duyet, lambda: q.duyet_kiem_quy(b["name"], 1))
	la("duyệt phiếu còn hiệu lực", kq["trang_thai"], "Đã ghi")
	la("chỉ MỘT bút toán thiếu 3.000.000", [d for d, _n, _g in je],
		[[{"tk": "1381", "no": 3000000, "co": 0}, {"tk": "1111", "no": 0, "co": 3000000}]])


@ca("v628 Codex #527 vòng 2: phiếu chờ duyệt mà đã có lần kiểm sau (ghi chen) thì Giám đốc không duyệt được")
def _codex_cho_duyet_cu():
	vat, kho, je = _vat_hai_lan()
	a = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm lần một"))
	# Lần kiểm sau ghi thẳng (không qua cửa kiem_quy), như hai lượt chạy chen nhau.
	kho["PQ-26-11-00099"] = _Doc({"loai": q.KIEM, "trang_thai": "Khớp", "luc": "2026-11-02 11:00:00", "lech": 0})
	duyet = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "session", NS(user="viet@x"))]
	_chay(vat + duyet, lambda: nem("có lần kiểm sau", lambda: q.duyet_kiem_quy(a["name"], 1)))
	la("không bút toán", je, [])


def _khop_gia(phieu, gd, chu_he, khoa_phieu=None):
	"""Chạy THẬT khop_nop_ngan_hang. Phép hỏi chủ toàn hệ giả dùng ĐÚNG luật
	doi_soat_ck.chu_theo_noi_dung (dòng đã khớp Đối chiếu ngân hàng là có chủ),
	cộng chủ ở luồng khác cho sẵn trong `chu_he`. `khoa_phieu` là bảng phiếu quỹ
	đang giữ giao dịch mà câu đọc có khoá thấy (lượt khác vừa ghi xong)."""
	import vagabond
	from vagabond import doi_soat_ck as dsck
	ghi, nhan = [], []

	def hoi_chu(ds, *a, **k):
		nhan.extend(ds)
		ra = dict(dsck.chu_theo_noi_dung(ds, (), None))
		ra.update({g["ten"]: c for g in ds for t, c in chu_he.items() if g["ten"] == t})
		return ra
	bh = NS(_gd_co_chu_toan_he=hoi_chu)

	def sql(cau, *a, **k):
		if "from `tabBank Transaction` where docstatus=1" in cau:
			return gd
		if "gd_sepay" in cau and "for update" in cau:
			ten = a[0][0] if a and a[0] else ""
			return [NS(name=n) for n, g in (khoa_phieu or {}).items() if g == ten]
		return []
	for x in phieu + gd:
		x.get = lambda k, d=None, x=x: getattr(x, k, d)
	vat = [um.patch.object(_fr, "get_all", lambda *a, **k: phieu), um.patch.object(_fr.db, "sql", sql),
		um.patch.object(vagabond, "ban_hang", bh, create=True), um.patch.dict(sys.modules, {"vagabond.ban_hang": bh}),
		um.patch.object(_fr.db, "get_value", lambda dt_, n, f=None, **k: "Chờ tiền về"),
		um.patch.object(_fr.db, "set_value", lambda dt_, n, v, *a, **k: ghi.append((n, v["gd_sepay"])))]
	so = _chay(vat, lambda: q.khop_nop_ngan_hang())
	return so, ghi, nhan


@ca("v628 Codex #527 vòng 2: giao dịch đã khớp chứng từ trong Đối chiếu ngân hàng thì phiếu nộp quỹ không nhận")
def _codex_da_phan_bo():
	phieu = [NS(name="PQ-1", ngay="2026-11-01", so_tien=20000000, bank_account="MB")]
	gd = [NS(ten="BT-1", bank_account="MB", deposit=20000000, unallocated_amount=0, date="2026-11-01", creation="1",
		mo_ta="NOP TIEN", tham_chieu="FT1")]
	so, ghi, nhan = _khop_gia(phieu, gd, {})
	la("truyền số đã phân bổ thật", [g["da_phan_bo"] for g in nhan], [20000000.0])
	la("không ghép", (so, ghi), (0, []))
	gd[0].unallocated_amount = 20000000
	so, ghi, nhan = _khop_gia(phieu, gd, {})
	la("chưa phân bổ thì ghép", (so, ghi), (1, [("PQ-1", "BT-1")]))


@ca("v628 Codex #527 vòng 2: hai lượt ghép chạy chen nhau thì một giao dịch chỉ xác nhận MỘT phiếu nộp")
def _codex_chen_nhau():
	gd = [NS(ten="BT-1", bank_account="MB", deposit=20000000, unallocated_amount=20000000, date="2026-11-01",
		creation="1", mo_ta="NOP TIEN", tham_chieu="FT1")]
	p1 = [NS(name="PQ-1", ngay="2026-11-01", so_tien=20000000, bank_account="MB")]
	p2 = [NS(name="PQ-2", ngay="2026-11-01", so_tien=20000000, bank_account="MB")]
	so1, ghi1, _n = _khop_gia(p1, gd, {})
	la("lượt một ghép PQ-1", ghi1, [("PQ-1", "BT-1")])
	# Lượt hai đọc danh sách chủ TRƯỚC khi lượt một ghi (ảnh chụp cũ, chu_he rỗng),
	# nhưng câu đọc có khoá thấy PQ-1 đã giữ BT-1.
	so2, ghi2, _n = _khop_gia(p2, gd, {}, khoa_phieu={"PQ-1": "BT-1"})
	la("lượt hai không ghép lại BT-1", (so2, ghi2), (0, []))


# ------------------------------------------------ Codex #527 vòng 3 (SHA 2ee032d24)


class _MvccGia:
	"""Mô hình MariaDB REPEATABLE READ tối thiểu: lần ĐỌC THƯỜNG đầu tiên của một giao
	dịch chụp ảnh số liệu đã commit; câu có khoá (for update) không chụp; commit ghi phần
	đang chờ và bỏ ảnh chụp. `chen` chạy ĐÚNG MỘT LẦN ngay khi giao dịch xin khoá quỹ,
	mô phỏng người thứ nhất đang giữ khoá, ghi xong và commit trước khi người thứ hai có khoá."""

	def __init__(self, so_du):
		self.da_commit = {"so_du": so_du}
		self.anh = None
		self.cho = 0.0
		self.chen = None

	def doc(self, k):
		if self.anh is None:
			self.anh = dict(self.da_commit)
		return self.anh[k]

	def ghi_tru(self, so):
		self.cho += so

	def commit(self):
		self.da_commit["so_du"] -= self.cho
		self.cho = 0.0
		self.anh = None

	def sql(self, cau, *a, **k):
		if "for update" in cau and self.chen:
			f, self.chen = self.chen, None
			f()
		return []


def _vat_nop_mvcc(db):
	je = []

	class _DocNop(_Doc):
		def insert(self, **k):
			return self
	vat = [
		um.patch.object(q, "_kiem_lam", lambda: None),
		um.patch.object(q, "_tai_khoan_nh", lambda: db.doc("tk")),
		um.patch.object(q, "_so_quy", lambda: (db.doc("so_du"), {"ngay_chot": "2026-10-31", "so_du": 1})),
		um.patch.object(q, "_tk_dung", lambda k: {"tk_quy": "1111", "tk_thieu": "1381", "tk_thua": "3381"}[k]),
		um.patch.object(q, "_ten", lambda u: "Dung"), um.patch.object(q, "nowdate", lambda: "2026-11-02"),
		um.patch.object(q, "_lap_but_toan", lambda dong, ngay, dg: (db.ghi_tru(dong[1]["co"]), je.append(dong))[1] or "ACC-JV-9"),
		um.patch.object(q, "khop_nop_ngan_hang", lambda chi=None: 0),
		um.patch.object(_fr, "get_doc", lambda d, *a: _DocNop(d)),
		um.patch.object(_fr, "session", NS(user="dung@x")),
		um.patch.object(_fr.db, "sql", db.sql), um.patch.object(_fr.db, "commit", db.commit),
		um.patch.object(_fr.db, "get_value", lambda *a, **k: "Chờ tiền về"),
	]
	from vagabond import tep_dinh_kem
	vat += [um.patch.object(tep_dinh_kem, "doc_ds", lambda x: [1]), um.patch.object(tep_dinh_kem, "gan_vao", lambda *a, **k: []),
		um.patch.object(tep_dinh_kem, "ghi_ds", lambda ds: "")]
	return vat, je


@ca("v628 Codex #527 vòng 3: hai kế toán cùng nộp 7 triệu từ quỹ 10 triệu thì người sau đọc số quỹ SAU khi có khoá, bị chặn")
def _codex_nop_chen():
	db = _MvccGia(10000000.0)
	db.da_commit["tk"] = [{"ma": "MB", "ten": "MB", "tk": "1121"}]
	vat, je = _vat_nop_mvcc(db)

	def nop():
		return q.nop_ngan_hang(so_tien="7.000.000", bank_account="MB", ngay="2026-11-02", anh="[1]")

	def nguoi_mot():
		# Giao dịch riêng của người thứ nhất: ảnh chụp riêng, ghi xong commit.
		anh_hai, db.anh = db.anh, None
		nop()
		db.commit()
		db.anh = anh_hai
	db.chen = nguoi_mot
	loi = None
	try:
		_chay(vat, nop)
		db.commit()
	except Exception as e:
		loi = str(e)
	dung("người sau bị chặn vì quỹ chỉ còn 3 triệu: %s" % loi, bool(loi) and "Quỹ chỉ còn 3.000.000" in loi)
	la("chỉ một bút toán nộp", len(je), 1)
	la("quỹ còn 3 triệu", db.da_commit["so_du"], 3000000.0)


@ca("v628 Codex #527 vòng 3: phiếu chờ duyệt mà quỹ đã chốt số dư lại từ ngày kiểm trở đi thì không duyệt được")
def _codex_duyet_sau_moc():
	vat, kho, je = _vat_hai_lan()
	a = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm thiếu"))
	from vagabond import tai_chinh as tc_
	duyet = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "session", NS(user="viet@x")),
		um.patch.object(tc_, "moc_quy", lambda: {"ngay_chot": "2026-11-02", "so_du": 7000000})]
	_chay(vat + duyet, lambda: nem("mốc chốt cùng ngày kiểm", lambda: q.duyet_kiem_quy(a["name"], 1)))
	la("không bút toán", je, [])
	duyet[-1] = um.patch.object(tc_, "moc_quy", lambda: {"ngay_chot": "2026-11-01", "so_du": 10000000})
	kq = _chay(vat + duyet, lambda: q.duyet_kiem_quy(a["name"], 1))
	la("mốc trước ngày kiểm thì duyệt được", kq["trang_thai"], "Đã ghi")


# ------------------------------------------------ Codex #527 vòng 4 (SHA a9124bceb)


class _KhoaQuyGia:
	"""Khoá quỹ chung tối thiểu: `for update` trên tài khoản quỹ là giữ khoá tới commit.
	Người khác bấm trong lúc khoá đang bị giữ thì CHỜ (chạy sau commit). `chen_khi_ghi`
	là thao tác của người khác chen vào đúng lúc người đang chạy chuẩn bị ghi bút toán;
	`dang_giu` là thao tác của người đã giữ khoá TRƯỚC, chạy xong rồi mới tới lượt người xin."""

	def __init__(self, so_du):
		self.so_du = so_du
		self.cho = 0.0
		self.giu = False
		self.hoan = []
		self.chen_khi_ghi = None
		self.dang_giu = None
		self.je = []

	def sql(self, cau, *a, **k):
		if "tabAccount" in cau and "for update" in cau:
			if self.dang_giu:
				f, self.dang_giu = self.dang_giu, None
				f()
			self.giu = True
		return []

	def commit(self):
		self.so_du += self.cho
		self.cho = 0.0
		self.giu = False
		while self.hoan:
			self.hoan.pop(0)()

	def thu(self, f):
		if self.giu:
			self.hoan.append(f)
		else:
			f()

	def lap_bt(self, dong, ngay, dg):
		if self.chen_khi_ghi:
			f, self.chen_khi_ghi = self.chen_khi_ghi, None
			f()
		self.cho += sum(float(d.get("no") or 0) - float(d.get("co") or 0) for d in dong if d.get("tk") == "1111")
		self.je.append(dong)
		return "ACC-JV-%d" % len(self.je)


def _vat_khoa_quy(db):
	vat, kho, _je = _vat_hai_lan(so_may=db.so_du)
	bo = ("_khoa_quy", "_so_quy", "_lap_but_toan", "sql")
	vat = [v for v in vat if getattr(v, "attribute", "") not in bo]
	vat += [um.patch.object(q, "_so_quy", lambda: (db.so_du, {"ngay_chot": "2026-10-31", "so_du": 1})),
		um.patch.object(q, "_lap_but_toan", db.lap_bt),
		um.patch.object(_fr.db, "sql", db.sql), um.patch.object(_fr.db, "commit", db.commit)]
	from vagabond import tai_chinh as tc_
	vat.append(um.patch.object(tc_, "moc_quy", lambda: {"ngay_chot": "2026-10-31", "so_du": 1}))
	return vat, kho


def _ke_toan_kiem(ket, ghi_chu):
	"""Kế toán đếm lại được 7.000.000 (14 tờ 500.000) rồi bấm Lưu, chạy trong giao dịch riêng."""
	def chay():
		with um.patch.object(_fr, "session", NS(user="dung@x")):
			ket.append(q.kiem_quy(bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu=ghi_chu))
	return chay


@ca("v628 Codex #527 vòng 4: Giám đốc đang duyệt thiếu 3 triệu thì kế toán kiểm lại phải CHỜ, đọc quỹ 7 triệu sau duyệt, không ra khoản thiếu thứ hai")
def _codex_duyet_chen_kiem():
	db = _KhoaQuyGia(10000000.0)
	vat, kho = _vat_khoa_quy(db)
	a = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm lần một"))
	db.commit()
	ket = []
	db.chen_khi_ghi = lambda: db.thu(lambda: (_ke_toan_kiem(ket, "đếm lần hai")(), db.commit()))
	duyet = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "session", NS(user="viet@x"))]
	_chay(vat + duyet, lambda: q.duyet_kiem_quy(a["name"], 1))
	_chay(vat, db.commit)
	for b in [k for k in ket if k.get("trang_thai") == "Chờ duyệt"]:
		_chay(vat + duyet, lambda: q.duyet_kiem_quy(b["name"], 1))
		db.commit()
	la("kế toán kiểm lại đọc quỹ sau duyệt nên khớp", [k.get("trang_thai") for k in ket], ["Khớp"])
	la("chỉ MỘT bút toán thiếu 3.000.000", len(db.je), 1)
	la("quỹ còn 7.000.000", db.so_du, 7000000.0)


@ca("v628 Codex #527 vòng 4: kế toán kiểm lại giữ khoá trước thì Giám đốc duyệt phiếu cũ sau đó bị chặn, chỉ phiếu mới được duyệt")
def _codex_kiem_truoc_duyet():
	db = _KhoaQuyGia(10000000.0)
	vat, kho = _vat_khoa_quy(db)
	a = _chay(vat, lambda: q.kiem_quy(bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm lần một"))
	db.commit()
	ket = []
	db.dang_giu = lambda: (_ke_toan_kiem(ket, "đếm lần hai")(), db.commit())
	duyet = [um.patch.object(q, "_la_giam_doc", lambda: True), um.patch.object(_fr, "session", NS(user="viet@x"))]
	_chay(vat + duyet, lambda: nem("phiếu cũ đã bị lần kiểm sau thay", lambda: q.duyet_kiem_quy(a["name"], 1)))
	_chay(vat, db.commit)
	la("phiếu cũ bị thay, không bút toán", (kho[a["name"]]["trang_thai"], len(db.je)), ("Đã thay", 0))
	_chay(vat + duyet, lambda: q.duyet_kiem_quy(ket[0]["name"], 1))
	db.commit()
	la("chỉ MỘT bút toán thiếu 3.000.000", len(db.je), 1)
	la("quỹ còn 7.000.000", db.so_du, 7000000.0)


@ca("v628 Codex #527 vòng 4 (cùng loại): huỷ phiếu nộp 2 triệu lấy khoá quỹ, kế toán kiểm quỹ chen vào phải chờ, đọc quỹ đã cộng lại 2 triệu")
def _codex_huy_chen_kiem():
	db = _KhoaQuyGia(8000000.0)
	vat, kho = _vat_khoa_quy(db)

	class _ButToan(_Doc):
		def cancel(self):
			if db.chen_khi_ghi:
				f, db.chen_khi_ghi = db.chen_khi_ghi, None
				f()
			db.cho += 2000000.0
			self["docstatus"] = 2
	kho["ACC-JV-NOP"] = _ButToan({"loai": "bút toán", "docstatus": 1})
	kho["PQ-NOP"] = _Doc({"loai": q.NOP, "trang_thai": "Chờ tiền về", "but_toan": "ACC-JV-NOP", "luc": "2026-11-02 09:00:00"})
	ket = []

	def ke_toan():
		with um.patch.object(_fr, "session", NS(user="dung@x")):
			ket.append(q.kiem_quy(bang='{"500000": "20"}', ly_do="dem_sai", ghi_chu="đếm két"))
		db.commit()
	db.chen_khi_ghi = lambda: db.thu(ke_toan)
	_chay(vat, lambda: q.huy_phieu("PQ-NOP", "ghi nhầm số"))
	_chay(vat, db.commit)
	la("kế toán đọc quỹ sau khi huỷ nên khớp", [k.get("trang_thai") for k in ket], ["Khớp"])
	la("không bút toán thừa 2 triệu", db.je, [])
	la("quỹ 10.000.000 đúng số két", db.so_du, 10000000.0)
