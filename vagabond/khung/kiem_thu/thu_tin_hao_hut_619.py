# -*- coding: utf-8 -*-
"""v619: tin tuần "Dữ liệu hao hụt" cho nhóm kế toán (anh Việt duyệt mẫu 28/10/2026).

Ca chuỗi chạy ĐÚNG đường máy chạy lúc 08:00 thứ Hai: tin_hao_hut.gui_tuan ->
tin_tuan -> soan -> kenh_zalo.bao_hoac_ghi_loi -> bao -> _ghi_hop_thu -> dòng sổ tin.
Chỉ thay tầng Frappe: phần đọc bảng (_doc_du_lieu) trả đúng số đọc trên site tuần
21/10 - 27/10/2026, sổ tin giả, nhóm giả. Tin ra phải trùng mẫu anh đã duyệt (chỉ
khác ở chỗ máy nêu đủ tên hàng, và kho Lab có thêm "(chỉ 1 dòng)" đúng dữ liệu).
"""
import sys
import types
import unittest.mock as um
from datetime import date
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import lien_ket_app as lk  # noqa: E402
from vagabond import tin_hao_hut as th  # noqa: E402
from vagabond.patches import v619_tin_hao_hut as pv  # noqa: E402

GOI = Path(__file__).resolve().parents[2]
APP = "https://app.thevagabondpatisserie.com"
SITE = ("vagabond.s.frappe.cloud", "erp.thevagabondpatisserie.com", "app.thevagabondpatisserie.com")


# ------------------------------------------------- số đọc trên site tuần 21/10 - 27/10

def _du_lieu_tuan():
	"""Đúng số đọc site 28/10/2026 (System Console, chỉ đọc). Phần món bán: sáu món
	nhiều nhất là tên thật; 22 món chưa có lệnh còn lại và 26 món có lệnh dựng sao cho
	tổng khớp 28/54 món, 493/1.954 cái."""
	ban = [
		{"ma": "BAEN00077", "ten": "Bánh Griotte", "sl": 57},
		{"ma": "BAEN00090", "ten": "Bánh MICHEALMAS", "sl": 50},
		{"ma": "HU00001", "ten": "Hũ Earl Grey Flan Kasutera Verrine", "sl": 38},
		{"ma": "HU00002", "ten": "Hũ Flan Kasutera Verrine", "sl": 31},
		{"ma": "BAEN00078", "ten": "BÁNH MEAD", "sl": 30},
		{"ma": "BAEN00031", "ten": "Bánh Slice Shijuso", "sl": 23},
	]
	for x in ban:
		x["bep"] = "Pastry"
	# 22 món chưa lệnh còn lại: 12 món bếp Baker, 10 món chưa rõ bếp (không vào tin bếp nào).
	ban += [{"ma": "KL%02d" % i, "ten": "Món khác %02d" % i, "sl": 12, "bep": "Baker" if i < 12 else ""} for i in range(22)]
	ban += [{"ma": "CL%02d" % i, "ten": "Món có lệnh %02d" % i, "sl": 56 if i < 21 else 57, "bep": "Baker"} for i in range(26)]
	da_lam = {"CL%02d" % i for i in range(26)}
	phieu = ([{"kho": "Baker - Thành phẩm - TV", "lam": 20, "thuc_te": 20}] * 54
		+ [{"kho": "Kho D1 - TV", "lam": 6, "thuc_te": 6}] * 7
		+ [{"kho": "Pastry - Nguyên liệu - TV", "lam": 1000, "thuc_te": 1000}] * 5
		+ [{"kho": "Pastry - Thành phẩm - TV", "lam": 12, "thuc_te": 12}]
		+ [{"kho": "Kho Lab - TV", "lam": 2, "thuc_te": 2}] * 2)
	kho_bep = ["Baker - Nguyên liệu - TV", "Baker - Thành phẩm - TV", "Kho Lab - TV",
		"Pastry - Nguyên liệu - TV", "Pastry - Thành phẩm - TV"]
	lan_cuoi = {"Baker - Nguyên liệu - TV": {"ngay": date(2026, 10, 20), "dong": 1},
		"Baker - Thành phẩm - TV": {"ngay": date(2026, 9, 30), "dong": 15},
		"Kho Lab - TV": {"ngay": date(2026, 10, 1), "dong": 1},
		"Pastry - Nguyên liệu - TV": {"ngay": date(2026, 10, 13), "dong": 15}}
	bins = [
		{"ma": "NVLT00338", "ten": "Bột quế, Cinnamon powder, Vipep", "dvt": "Gram", "kho": "Kho tổng 307 - TV", "gia": 28.8},
		{"ma": "NVLT00338", "ten": "Bột quế, Cinnamon powder, Vipep", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 310},
		{"ma": "NVLT00338", "ten": "Bột quế, Cinnamon powder, Vipep", "dvt": "Gram", "kho": "Baker - Nguyên liệu - TV", "gia": 310},
		{"ma": "NVLT00330", "ten": "Bột tinh than tre, Takesumi", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 175},
		{"ma": "NVLT00330", "ten": "Bột tinh than tre, Takesumi", "dvt": "Gram", "kho": "Baker - Nguyên liệu - TV", "gia": 175},
		{"ma": "NVLT00330", "ten": "Bột tinh than tre, Takesumi", "dvt": "Gram", "kho": "Kho tổng 307 - TV", "gia": 2500},
		{"ma": "NVLT00056", "ten": "Bột trà Houjicha, Hamasaen", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 560},
		{"ma": "NVLT00056", "ten": "Bột trà Houjicha, Hamasaen", "dvt": "Gram", "kho": "Kho D1 - TV", "gia": 1712.1},
		{"ma": "NVLT00169", "ten": "Gelatin Powder A250 bloom, VMC", "dvt": "Gram", "kho": "Baker - Nguyên liệu - TV", "gia": 13},
		{"ma": "NVLT00169", "ten": "Gelatin Powder A250 bloom, VMC", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 13},
		{"ma": "NVLT00169", "ten": "Gelatin Powder A250 bloom, VMC", "dvt": "Gram", "kho": "Kho Lab - TV", "gia": 333.3},
		{"ma": "NVLT00239", "ten": "Phô mai Dutch Emmental", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 101.9},
		{"ma": "NVLT00239", "ten": "Phô mai Dutch Emmental", "dvt": "Gram", "kho": "Kho tổng 307 - TV", "gia": 328},
		{"ma": "NVLT00113", "ten": "Trái táo tươi", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 77.8},
		{"ma": "NVLT00113", "ten": "Trái táo tươi", "dvt": "Gram", "kho": "Baker - Nguyên liệu - TV", "gia": 1233.2},
		# Bơ lệch dưới 3 lần: không được nêu.
		{"ma": "NVLT00001", "ten": "Bơ lạt", "dvt": "Gram", "kho": "Kho tổng 307 - TV", "gia": 300},
		{"ma": "NVLT00001", "ten": "Bơ lạt", "dvt": "Gram", "kho": "Pastry - Nguyên liệu - TV", "gia": 880},
	]
	btp = ["BTP Brown Butter", "BTP Dark cocoa biscuit", "BTP Dough croissant tart ( Ko sử dụng mã này )",
		"BTP Nước ép dứa", "BTP Sữa chua Hy Lạp VGB", "BTP Thịt bí", "BTP Thịt dứa"]
	return {"ban": ban, "da_lam": da_lam, "phieu": phieu, "kho_bep": kho_bep, "lan_cuoi": lan_cuoi,
		"bins": bins, "btp": btp, "so_ct": 424, "co_hh": 0}


TIN_MONG = "\n".join([
	"📊 BẢN TIN: Dữ liệu hao hụt tuần 21/10 - 27/10",
	"Chưa đủ dữ liệu để tính hao hụt. Còn 5 chỗ cần sửa:",
	"- Bánh bán ra chưa có lệnh sản xuất: 28/54 món, 493/1.954 cái. Nhiều nhất: Bánh Griotte 57, "
	"Bánh MICHEALMAS 50, Hũ Earl Grey Flan Kasutera Verrine 38, Hũ Flan Kasutera Verrine 31, BÁNH MEAD 30 và 23 món khác.",
	"- Hoàn tất lệnh không cân: 69/69 lệnh ghi số cân bằng đúng số làm theo lệnh (Baker 54, D1 7, Pastry 6, Lab 2).",
	"- Kho bếp lâu chưa kiểm kê: Pastry thành phẩm chưa kiểm lần nào; Baker thành phẩm từ 30/09; "
	"Lab từ 01/10 (chỉ 1 dòng); Pastry nguyên liệu từ 13/10; Baker nguyên liệu 20/10 (chỉ 1 dòng).",
	"- Giá vốn một món lệch nhau giữa các kho từ 3 lần trở lên: Gelatin Powder A250 bloom, VMC 13 đ/g "
	"(Baker nguyên liệu, Pastry nguyên liệu) và 333 đ/g (Lab); Trái táo tươi 78 đ/g (Pastry nguyên liệu) và "
	"1.233 đ/g (Baker nguyên liệu); Bột tinh than tre, Takesumi 175 đ/g (Baker nguyên liệu, Pastry nguyên liệu) "
	"và 2.500 đ/g (Kho tổng 307) và 3 món khác.",
	"- Công thức: 7 bán thành phẩm chưa có công thức (Brown Butter, Dark cocoa biscuit, Dough croissant tart "
	"( Ko sử dụng mã này ), Nước ép dứa, Sữa chua Hy Lạp VGB, Thịt bí, Thịt dứa); 0/424 công thức có % hao hụt cho phép.",
	"Phụ trách: Khải (giá vốn, công thức); bếp Pastry, Baker (lệnh, số cân, kiểm kê)",
	"Hạn: trước bản tin thứ Hai tới",
	"Mở: " + APP + "/du-lieu-hao-hut",
])


def _chay_gui(du_lieu, nhom, hom_nay="2026-10-28", ham="gui_tuan"):
	"""Chạy gui_tuan (hay gui_tuan_bep) như nhịp lịch thứ Hai, trả các dòng sổ tin đã ghi."""
	ghi = []

	class Tin(dict):
		def insert(self, **k):
			ghi.append(dict(self))
	fr = types.SimpleNamespace(
		generate_hash=lambda length=8: "h" * length, flags=types.SimpleNamespace(vagabond_kiem_that=False),
		db=types.SimpleNamespace(savepoint=lambda *a: None, rollback=lambda **k: None,
			after_commit=types.SimpleNamespace(add=lambda f: None)),
		get_doc=lambda d: Tin(d), log_error=lambda *a, **k: ghi.append({"loi": k.get("title") or (a[0] if a else "")}),
		get_traceback=lambda: "", DuplicateEntryError=KeyError,
		utils=types.SimpleNamespace(get_url=lambda *a, **k: "https://vagabond.s.frappe.cloud" + (a[0] if a else "")))
	fu = sys.modules["frappe"].utils
	with um.patch.object(kz, "frappe", fr), um.patch.dict(sys.modules["frappe"].__dict__, {"log_error": fr.log_error,
			"get_traceback": fr.get_traceback}), \
			um.patch.object(kz, "_bat", lambda: 1), um.patch.object(kz, "_cac_nhom", lambda: nhom), \
			um.patch.object(lk, "goc_app", lambda: APP), um.patch.object(lk, "may_cua_site", lambda: set(SITE)), \
			um.patch.object(fu, "nowdate", lambda: hom_nay, create=True), \
			um.patch.object(th, "_doc_du_lieu", lambda tu, den: du_lieu):
		getattr(th, ham)()
	return ghi


NHOM_KT = [{"ten_nhom": "VGB • BP • Kế toán", "chat_id": "kt", "bat": 1,
	"tin_nhan": "kt_kiem_ke_lech, kt_du_lieu_hao_hut"}]


@ca("v619 hao hụt: chuỗi thật thứ Hai 08:00 ra đúng mẫu anh Việt duyệt, số tuần 21/10 - 27/10")
def _chuoi_mau():
	ghi = _chay_gui(_du_lieu_tuan(), NHOM_KT)
	la("ghi một tin, không lỗi", [sorted(g) for g in ghi if "loi" in g], [])
	la("một dòng sổ tin", len(ghi), 1)
	la("đúng mẫu đã duyệt", ghi[0]["noi_dung"], TIN_MONG)
	dung("dưới trần 2.000 ký tự", len(ghi[0]["noi_dung"]) < kz.TOI_DA_KY_TU)
	la("mã tin để nhóm Kế toán nhận", ghi[0].get("ma_tin"), "kt_du_lieu_hao_hut")
	la("khoá chống trùng theo ngày và nhóm", ghi[0].get("khoa"), kz.khoa_tin("du-lieu-hao-hut:2026-10-28", "kt"))


@ca("v619 hao hụt: tuần đủ dữ liệu thì tin chỉ một dòng, vẫn có đường mở")
def _du():
	d = _du_lieu_tuan()
	d.update(ban=[{"ma": "CL00", "ten": "Món có lệnh", "sl": 10}], da_lam={"CL00"},
		phieu=[{"kho": "Baker - Thành phẩm - TV", "lam": 20, "thuc_te": 18}] * 6,
		lan_cuoi={k: {"ngay": date(2026, 10, 25), "dong": 30} for k in d["kho_bep"]},
		bins=[], btp=[], co_hh=424)
	ghi = _chay_gui(d, NHOM_KT)
	la("tin gọn", ghi[0]["noi_dung"], "📊 BẢN TIN: Dữ liệu hao hụt tuần 21/10 - 27/10\n"
		"Dữ liệu tuần này đủ để tính hao hụt.\nMở: " + APP + "/du-lieu-hao-hut")


@ca("v619 hao hụt: nhóm chưa tích tin này thì không nhận; lỗi đọc dữ liệu không làm hỏng lịch")
def _nhom_va_loi():
	ghi = _chay_gui(_du_lieu_tuan(), [{"ten_nhom": "VGB • BP • Bán hàng & Sales", "chat_id": "bh", "bat": 1,
		"tin_nhan": "bh_dat_ban"}])
	la("nhóm Sales không nhận", [g for g in ghi if "noi_dung" in g], [])

	def hong(tu, den):
		raise RuntimeError("mất kết nối cơ sở dữ liệu")
	with um.patch.object(th, "_doc_du_lieu", hong):
		loi = []
		with um.patch.object(th, "tin_tuan", lambda hn=None: hong(0, 0)), \
				um.patch("vagabond.tin_kho._ghi_loi", lambda ten: loi.append(ten)):
			th.gui_tuan()
	la("lỗi ghi vào Error Log, không ném ra", loi, ["hao hụt"])


@ca("v619 hao hụt: bánh bán chưa có lệnh, gom trùng mã, bỏ món bán 0, có lệnh trong 14 ngày thì thôi")
def _ban():
	r = th.mon_ban_chua_lenh([{"ma": "A", "ten": "Bánh A", "sl": 3}, {"ma": "A", "ten": "Bánh A", "sl": 2},
		{"ma": "B", "ten": "Bánh B", "sl": 9}, {"ma": "C", "ten": "Bánh C", "sl": 0}, {"ma": "D", "ten": "Bánh D", "sl": 4}], {"D"})
	la("hai món chưa lệnh, nhiều nhất trước", r["ds"], [("Bánh B", 9.0), ("Bánh A", 5.0)])
	la("tổng", [r["mon"], r["cai"], r["tong_mon"], r["tong_cai"]], [2, 14.0, 3, 18.0])
	la("không bán gì", th.mon_ban_chua_lenh([], set())["mon"], 0)


@ca("v619 hao hụt: lệnh không cân chỉ báo khi từ 5 lệnh và từ 90% ghi bằng số làm")
def _khong_can():
	p = lambda kho, lam, tt: {"kho": kho, "lam": lam, "thuc_te": tt}  # noqa: E731
	la("4 lệnh: chưa đủ dấu hiệu", th.lenh_khong_can([p("Kho D1 - TV", 5, 5)] * 4), None)
	la("5/5 bằng: báo", th.lenh_khong_can([p("Kho D1 - TV", 5, 5)] * 5), {"bang": 5, "tong": 5, "theo_bep": [("D1", 5)]})
	la("9/10 bằng: báo (đúng 90%)", th.lenh_khong_can([p("Baker - Thành phẩm - TV", 5, 5)] * 9 + [p("Kho D1 - TV", 5, 4)])["bang"], 9)
	la("8/10 bằng: bếp có cân, không báo", th.lenh_khong_can([p("Baker - Thành phẩm - TV", 5, 5)] * 8
		+ [p("Kho D1 - TV", 5, 4)] * 2), None)
	la("hai kho Pastry gộp một bếp", th.lenh_khong_can([p("Pastry - Nguyên liệu - TV", 1, 1)] * 3
		+ [p("Pastry - Thành phẩm - TV", 1, 1)] * 3)["theo_bep"], [("Pastry", 6)])
	la("lệnh số làm 0 không tính", th.lenh_khong_can([p("Kho D1 - TV", 0, 0)] * 9), None)


@ca("v619 hao hụt: kho bếp chưa đếm (quá 7 ngày, dưới 5 dòng, chưa lần nào), kho khác không xét")
def _dem():
	moc = date(2026, 10, 27)
	la("đúng 7 ngày đủ dòng: không nhắc", th.kho_chua_dem(["Baker - Nguyên liệu - TV"],
		{"Baker - Nguyên liệu - TV": {"ngay": date(2026, 10, 20), "dong": 20}}, moc), [])
	la("8 ngày: nhắc", th.kho_chua_dem(["Baker - Nguyên liệu - TV"],
		{"Baker - Nguyên liệu - TV": {"ngay": "2026-10-19", "dong": 20}}, moc), ["Baker nguyên liệu từ 19/10"])
	la("mới đếm mà 4 dòng: nhắc", th.kho_chua_dem(["Kho Lab - TV"], {"Kho Lab - TV": {"ngay": date(2026, 10, 26), "dong": 4}}, moc),
		["Lab 26/10 (chỉ 4 dòng)"])
	la("chưa lần nào lên đầu", th.kho_chua_dem(["Kho Lab - TV", "Pastry - Thành phẩm - TV"],
		{"Kho Lab - TV": {"ngay": date(2026, 9, 1), "dong": 9}}, moc), ["Pastry thành phẩm chưa kiểm lần nào", "Lab từ 01/09"])
	la("chỉ kho ba bếp", [k for k in ("Baker - Nguyên liệu - TV", "Kho Lab - TV", "Pastry - Thành phẩm - TV",
		"Kho D1 - TV", "Kho tổng 307 - TV", "Kho Sales Online - TV") if th.la_kho_bep(k)],
		["Baker - Nguyên liệu - TV", "Kho Lab - TV", "Pastry - Thành phẩm - TV"])
	la("tên kho gọn", [th.ten_kho_ngan(k) for k in ("Kho D1 - TV", "Kho tổng 307 - TV", "Pastry - Thành phẩm - TV", "")],
		["D1", "Kho tổng 307", "Pastry thành phẩm", ""])


# Codex 4403241208 (86538c56): lần đếm phải lấy từ phiếu kiểm kê, không từ dòng điều chỉnh tồn.
# Site 28/10/2026 (chỉ đọc): Pastry nguyên liệu 13/10 có hai phiếu kiểm kê đếm 1 + 14 món, nhưng
# hai Stock Reconciliation chỉ còn 1 + 8 dòng vì ERPNext bỏ món khớp sổ. Bản cũ báo 8 dòng.
PKK_CA = [  # (tên, kho, ngày, [da_dem từng dòng], Stock Reconciliation gắn phiếu)
	("KK-A", "Pastry - Nguyên liệu - TV", "2026-10-13", [1], "PKK-21"),
	("KK-B", "Pastry - Nguyên liệu - TV", "2026-10-13", [1] * 14, "PKK-22"),
	# Codex: kiểm 20 món, chỉ 1 món lệch -> Stock Reconciliation 1 dòng.
	("KK-C", "Baker - Nguyên liệu - TV", "2026-10-26", [1] * 20, "PKK-30"),
	# Codex: kiểm 12 món khớp hết -> không có Stock Reconciliation.
	("KK-D", "Pastry - Thành phẩm - TV", "2026-10-25", [1] * 12, None),
	# Phiếu cũ trước khi có ô Đã đếm: cả phiếu đã nhập số, tính mọi dòng.
	("KK-E", "Kho Lab - TV", "2026-10-24", [0] * 6, None),
	("KK-F", "Baker - Thành phẩm - TV", "2026-10-01", [1] * 15, "PKK-15"),
]
SR_CA = [  # (tên, kho, ngày, số dòng)
	("PKK-21", "Pastry - Nguyên liệu - TV", "2026-10-13", 1),
	("PKK-22", "Pastry - Nguyên liệu - TV", "2026-10-13", 8),
	("PKK-30", "Baker - Nguyên liệu - TV", "2026-10-26", 1),
	("PKK-15", "Baker - Thành phẩm - TV", "2026-10-01", 15),
	# Điều chỉnh làm thẳng trên Desk, không gắn phiếu: vẫn là một lần đếm.
	("PKK-40", "Baker - Thành phẩm - TV", "2026-10-23", 7),
	# Cùng ngày với phiếu kiểm Lab: nhập tay thêm 2 dòng cho chính các món đã đếm, không cộng dồn.
	("PKK-41", "Kho Lab - TV", "2026-10-24", 2),
]


class _Dong(dict):
	"""Như frappe._dict: dòng as_dict đọc được cả .get lẫn thuộc tính."""
	__getattr__ = dict.get


def _doc_that(phieu=PKK_CA, sr=SR_CA, co_pkk=True):
	"""Chạy ĐÚNG _doc_du_lieu với cơ sở dữ liệu giả trả đúng các bảng. Trả lan_cuoi."""

	def sql(q, v=None, as_dict=False):
		if "`tabPhieu Kiem Ke` p where p.trang_thai" in q:
			assert co_pkk
			return [_Dong(kho=k, ngay=date.fromisoformat(n), dong=(sum(d) if sum(d) > 0 else len(d)))
				for _, k, n, d, _ in phieu if n <= str(v["den"])]
		if "`tabStock Reconciliation`" in q:
			ra = [_Dong(kho=k, name=t, ngay=date.fromisoformat(n), dong=c) for t, k, n, c in sr if n <= str(v["den"])]
			return sorted(ra, key=lambda r: (r.ngay, r.name))
		if "count(*), sum(case" in q:
			return [(0, 0)]
		return []
	db = types.SimpleNamespace(sql=sql, sql_list=lambda *a, **k: [], table_exists=lambda dt: co_pkk)
	fr = sys.modules["frappe"]
	from vagabond import kho_san_xuat
	with um.patch.object(fr, "db", db, create=True), \
			um.patch.object(fr, "get_all", lambda dt, **k: ["Baker - Nguyên liệu - TV", "Baker - Thành phẩm - TV",
				"Kho Lab - TV", "Pastry - Nguyên liệu - TV", "Pastry - Thành phẩm - TV", "Kho D1 - TV"], create=True), \
			um.patch.object(fr.utils, "add_days", lambda d, n: d, create=True), \
			um.patch.object(kho_san_xuat, "_bep_cua_mon", lambda ma: ""):
		return th._doc_du_lieu(date(2026, 10, 21), date(2026, 10, 27))


@ca("v619 hao hụt: lần đếm lấy từ phiếu kiểm kê (cả món khớp sổ), điều chỉnh trên Desk vẫn tính, cùng ngày không cộng hai lần")
def _dem_tu_phieu():
	d = _doc_that()
	la("lần đếm từng kho", {k: (str(v["ngay"]), v["dong"]) for k, v in sorted(d["lan_cuoi"].items())}, {
		"Baker - Nguyên liệu - TV": ("2026-10-26", 20),
		"Baker - Thành phẩm - TV": ("2026-10-23", 7),
		"Kho Lab - TV": ("2026-10-24", 6),
		"Pastry - Nguyên liệu - TV": ("2026-10-13", 15),
		"Pastry - Thành phẩm - TV": ("2026-10-25", 12)})
	la("tin chỉ còn nhắc kho quá 7 ngày", th.kho_chua_dem(d["kho_bep"], d["lan_cuoi"], date(2026, 10, 27)),
		["Pastry nguyên liệu từ 13/10"])
	# Site chưa có bảng phiếu kiểm kê (bench mới dựng): đọc điều chỉnh tồn như cũ, không lỗi.
	d = _doc_that(phieu=[], co_pkk=False)
	la("không có bảng phiếu", {k: v["dong"] for k, v in sorted(d["lan_cuoi"].items())},
		{"Baker - Nguyên liệu - TV": 1, "Baker - Thành phẩm - TV": 7, "Kho Lab - TV": 2, "Pastry - Nguyên liệu - TV": 9})
	la("hàm thuần bỏ dòng thiếu kho hay ngày", th.lan_dem_cuoi([{"kho": "", "ngay": "2026-10-01", "dong": 3},
		{"kho": "K", "ngay": None, "dong": 3}], None), {})


@ca("v619 hao hụt: giá lệch từ 3 lần, đơn vị gọn, chỉ nêu ba món lệch nhất")
def _gia():
	b = lambda ma, kho, gia, dvt="Gram": {"ma": ma, "ten": "Món " + ma, "dvt": dvt, "kho": kho, "gia": gia}  # noqa: E731
	la("đúng 3 lần là lệch", th.gia_lech_kho([b("A", "Kho Lab - TV", 10), b("A", "Kho D1 - TV", 30)]),
		["Món A 10 đ/g (Lab) và 30 đ/g (D1)"])
	la("2,9 lần thì thôi", th.gia_lech_kho([b("A", "Kho Lab - TV", 10), b("A", "Kho D1 - TV", 29)]), [])
	la("giá 0 không tính", th.gia_lech_kho([b("A", "Kho Lab - TV", 0), b("A", "Kho D1 - TV", 29)]), [])
	la("đơn vị ml, cái", th.gia_lech_kho([b("A", "Kho Lab - TV", 1, "ML"), b("A", "Kho D1 - TV", 5, "ML"),
		b("B", "Kho Lab - TV", 1000, "Cái"), b("B", "Kho D1 - TV", 9000, "Cái")]),
		["Món B 1.000 đ/Cái (Lab) và 9.000 đ/Cái (D1)", "Món A 1 đ/ml (Lab) và 5 đ/ml (D1)"])
	d = _du_lieu_tuan()
	chu = th.soan(date(2026, 10, 21), date(2026, 10, 27), None, None, [], th.gia_lech_kho(d["bins"]), [], 0, 0)
	dung("ba món rồi gom phần còn lại", chu.count(" đ/g (") == 6 and "(Kho tổng 307) và 3 món khác.\n" in chu)


@ca("v619 bản vá: tích tin mới cho nhóm đã nhận tin kiểm kê lệch, lũy đẳng, không đụng nhóm khác")
def _ban_va():
	la("nhóm Kế toán", pv.tin_them("kt_hoan_tien, kt_kiem_ke_lech"), "kt_hoan_tien, kt_kiem_ke_lech, kt_du_lieu_hao_hut")
	la("đã có thì thôi", pv.tin_them("kt_kiem_ke_lech, kt_du_lieu_hao_hut"), None)
	la("nhóm khác không đổi", pv.tin_them("bh_dat_ban, kho_da_chuyen"), None)
	la("ô trống (nhận mọi tin) để nguyên", pv.tin_them(""), None)
	la("chấm phẩy vẫn đọc được", pv.tin_them("kt_kiem_ke_lech; kt_hoan_tien"), "kt_kiem_ke_lech, kt_hoan_tien, kt_du_lieu_hao_hut")
	la("nhóm Sản xuất nhận tin bếp", pv.tin_them("bep_ycsx_moi, bep_lenh_chua_xong"),
		"bep_ycsx_moi, bep_lenh_chua_xong, bep_du_lieu_hao_hut")
	ghi = []
	rows = [{"name": "r1", "tin_nhan": "kt_kiem_ke_lech"}, {"name": "r2", "tin_nhan": "bh_dat_ban"}, {"name": "r3", "tin_nhan": None},
		{"name": "r4", "tin_nhan": "bep_lenh_chua_xong"}]
	fr = types.SimpleNamespace(db=types.SimpleNamespace(has_column=lambda dt, c: True,
		set_value=lambda dt, ten, f, v, **k: ghi.append((ten, v)), commit=lambda: None),
		get_all=lambda *a, **k: [dict(r) for r in rows], clear_cache=lambda **k: None)
	with um.patch.dict(sys.modules, {"frappe": fr}):
		pv.execute()
	la("chỉ ghi nhóm Kế toán và nhóm Sản xuất", ghi, [("r1", "kt_kiem_ke_lech, kt_du_lieu_hao_hut"),
		("r4", "bep_lenh_chua_xong, bep_du_lieu_hao_hut")])
	rows[0]["tin_nhan"] = ghi[0][1]
	rows[3]["tin_nhan"] = ghi[1][1]
	ghi.clear()
	with um.patch.dict(sys.modules, {"frappe": fr}):
		pv.execute()
	la("chạy lại không ghi gì", ghi, [])
	src = (GOI / "patches.txt").read_text(encoding="utf-8")
	dung("bản vá có trong patches.txt", "vagabond.patches.v619_tin_hao_hut" in src.split("[post_model_sync]")[1])


@ca("v619 lịch: thứ Hai 08:00 nối đúng hàm gửi")
def _lich():
	ns = {}
	exec(compile((GOI / "hooks.py").read_text(encoding="utf-8"), "hooks.py", "exec"), ns)
	la("đúng một lịch tin kế toán", [g for g, ds in ns["scheduler_events"]["cron"].items() if "vagabond.tin_hao_hut.gui_tuan" in ds], ["0 8 * * 1"])
	la("đúng một lịch tin bếp", [g for g, ds in ns["scheduler_events"]["cron"].items() if "vagabond.tin_hao_hut.gui_tuan_bep" in ds], ["0 8 * * 1"])
	dung("hàm có thật", callable(th.gui_tuan) and callable(th.gui_tuan_bep))


NHOM_SX = [{"ten_nhom": "VGB • VH • Sản xuất & Tồn kho", "chat_id": "sx", "bat": 1,
	"tin_nhan": "bep_lenh_chua_xong, bep_du_lieu_hao_hut"}]

TIN_PASTRY = "\n".join([
	"✅ VIỆC CẦN LÀM: Bếp Pastry ghi đủ lệnh sản xuất và số cân tuần 21/10 - 27/10",
	"- Bánh bán ra tuần qua chưa có lệnh sản xuất: 6 món, 229 cái. Nhiều nhất: Bánh Griotte 57, Bánh MICHEALMAS 50, "
	"Hũ Earl Grey Flan Kasutera Verrine 38 và 3 món khác. Làm xong mẻ nào thì hoàn tất lệnh mẻ đó.",
	"- Khi bấm Hoàn tất, ô \"Thực tế cân được\" ghi số cân thật, không chép lại số làm theo lệnh. Tuần qua 6/6 lệnh chép số.",
	"- Kiểm kê nguyên liệu đắt (bơ, kem, sô cô la, phô mai, hạt, trái cây) mỗi tuần: Pastry thành phẩm chưa kiểm lần nào; "
	"Pastry nguyên liệu từ 13/10.",
	"Hạn: Chủ nhật này",
	"Mở: " + APP + "/san-xuat",
])


@ca("v619 tin bếp: chuỗi thật thứ Hai 08:00, mỗi bếp một tin chỉ việc của bếp đó, không số tiền")
def _chuoi_bep():
	ghi = _chay_gui(_du_lieu_tuan(), NHOM_SX, ham="gui_tuan_bep")
	la("không lỗi", [g for g in ghi if "loi" in g], [])
	la("ba bếp có việc: Baker, Pastry, Lab", [g["noi_dung"].split(":")[1].strip().split(" ghi")[0] for g in ghi],
		["Bếp Baker", "Bếp Pastry", "Sonneto Lab"])
	la("tin Pastry đúng mẫu đã duyệt", ghi[1]["noi_dung"], TIN_PASTRY)
	dung("Baker: 12 món của Baker, 54/54 lệnh, hai kho", "12 món, 144 cái" in ghi[0]["noi_dung"]
		and "54/54 lệnh" in ghi[0]["noi_dung"] and "Baker thành phẩm từ 30/09; Baker nguyên liệu 20/10 (chỉ 1 dòng)" in ghi[0]["noi_dung"])
	dung("Baker không lẫn món Pastry, món chưa rõ bếp", "Griotte" not in ghi[0]["noi_dung"] and "Món khác 12" not in ghi[0]["noi_dung"])
	la("Lab chỉ có dòng kiểm kê (2 lệnh chưa đủ dấu hiệu)", ghi[2]["noi_dung"].count("\n- "), 1)
	dung("không số tiền", not any(kz.MAU_TIEN.search(g["noi_dung"]) or "đ/" in g["noi_dung"] for g in ghi))
	la("mã tin bếp", sorted({g.get("ma_tin") for g in ghi}), ["bep_du_lieu_hao_hut"])
	la("khoá theo bếp và ngày", [g.get("khoa") for g in ghi],
		[kz.khoa_tin("du-lieu-hao-hut-bep:%s:2026-10-28" % b, "sx") for b in ("Baker", "Pastry", "Lab")])
	ghi = _chay_gui(_du_lieu_tuan(), NHOM_KT, ham="gui_tuan_bep")
	la("nhóm Kế toán không nhận tin bếp", [g for g in ghi if "noi_dung" in g], [])


@ca("v619 tin bếp: bếp không có việc thì không gửi")
def _bep_trong():
	la("trống", th.soan_bep("Pastry", date(2026, 10, 21), date(2026, 10, 27), {"mon": 0}, None, []), "")


@ca("v619 báo cáo BC18: đủ từng dòng (tin chỉ nêu vài món), có trong danh sách báo cáo, không lọc điểm bán")
def _bc18():
	from vagabond import bao_cao as bc

	b = bc.THEO_MA.get("BC18")
	dung("có BC18", bool(b) and b["ten"] == "Dữ liệu hao hụt" and b.get("khong_loc") == 1)
	d = _du_lieu_tuan()
	dong = th.dong_bao_cao(d, date(2026, 10, 27))
	muc = [x["muc"] for x in dong]
	la("đủ 28 bánh chưa lệnh", muc.count("Bánh bán ra chưa có lệnh sản xuất"), 28)
	la("bánh nhiều nhất trước, có bếp", dong[0], {"muc": "Bánh bán ra chưa có lệnh sản xuất", "chi_tiet": "Bánh Griotte",
		"so": 57.0, "noi": "Bếp Pastry"})
	dung("món chưa rõ bếp ghi rõ", any(x["noi"] == "Chưa rõ bếp" for x in dong))
	la("lệnh theo từng bếp, kể cả chưa đủ dấu hiệu", [x["chi_tiet"] + " " + x["noi"] for x in dong if x["muc"].startswith("Lệnh")],
		["54/54 lệnh Bếp Baker", "7/7 lệnh D1", "2/2 lệnh Sonneto Lab", "6/6 lệnh Bếp Pastry"])
	la("đủ 6 giá lệch, 7 bán thành phẩm, 5 kho", [muc.count("Giá vốn lệch giữa các kho"), muc.count("Bán thành phẩm chưa có công thức"),
		muc.count("Kho bếp lâu chưa kiểm kê")], [6, 7, 5])
	la("dòng công thức", dong[-1]["chi_tiet"], "0/424 công thức đã khai")
	with um.patch.object(th, "_doc_du_lieu", lambda tu, den: d):
		kq = th.bao_cao(date(2026, 10, 21), date(2026, 10, 27), bc._cot)
	la("cột", [c["k"] for c in kq["cot"]], ["muc", "chi_tiet", "so", "noi"])
	la("dòng", len(kq["dong"]), len(dong))
