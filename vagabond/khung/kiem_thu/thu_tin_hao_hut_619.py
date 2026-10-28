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
	ban += [{"ma": "KL%02d" % i, "ten": "Món khác %02d" % i, "sl": 12} for i in range(22)]
	ban += [{"ma": "CL%02d" % i, "ten": "Món có lệnh %02d" % i, "sl": 56 if i < 21 else 57} for i in range(26)]
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
		"Pastry - Nguyên liệu - TV": {"ngay": date(2026, 10, 13), "dong": 9}}
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
	"Mở: " + APP + "/bao-cao",
])


def _chay_gui(du_lieu, nhom, hom_nay="2026-10-28"):
	"""Chạy gui_tuan như nhịp lịch thứ Hai, trả các dòng sổ tin đã ghi."""
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
		th.gui_tuan()
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
		"Dữ liệu tuần này đủ để tính hao hụt.\nMở: " + APP + "/bao-cao")


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
	ghi = []
	rows = [{"name": "r1", "tin_nhan": "kt_kiem_ke_lech"}, {"name": "r2", "tin_nhan": "bh_dat_ban"}, {"name": "r3", "tin_nhan": None}]
	fr = types.SimpleNamespace(db=types.SimpleNamespace(has_column=lambda dt, c: True,
		set_value=lambda dt, ten, f, v, **k: ghi.append((ten, v)), commit=lambda: None),
		get_all=lambda *a, **k: [dict(r) for r in rows], clear_cache=lambda **k: None)
	with um.patch.dict(sys.modules, {"frappe": fr}):
		pv.execute()
	la("chỉ ghi nhóm Kế toán", ghi, [("r1", "kt_kiem_ke_lech, kt_du_lieu_hao_hut")])
	rows[0]["tin_nhan"] = ghi[0][1]
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
	la("đúng một lịch", [g for g, ds in ns["scheduler_events"]["cron"].items() if "vagabond.tin_hao_hut.gui_tuan" in ds], ["0 8 * * 1"])
	dung("hàm có thật", callable(th.gui_tuan))
