# -*- coding: utf-8 -*-
"""v619: chuông thông báo trong app (anh Việt chọn "một chuông gộp cả hai", 28/10/2026).

Máy chủ (vagabond/chuong.py) chọn tin cho từng người theo phòng ban, gộp tin gửi
nhiều nhóm, đếm tin chưa đọc theo mốc riêng từng người, cộng việc đang chờ. Ca chạy
ĐÚNG các hàm mở ra ngoài (dem, thong_bao, da_xem) trên sổ tin giả có tin của nhiều
bộ phận; chỉ thay tầng Frappe (bảng sổ tin, vai, mốc đã đọc) và số Việc cần làm.
"""
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

from vagabond import chuong as ch  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402

APP = "https://app.thevagabondpatisserie.com"


def _tin(name, ma, noi_dung, luc):
	return {"name": name, "ma_tin": ma, "noi_dung": noi_dung, "creation": luc}


SO = [
	_tin("t1", "kt_du_lieu_hao_hut", "📊 BẢN TIN: Dữ liệu hao hụt tuần 21/10 - 27/10\nChưa đủ dữ liệu.\nMở: " + APP + "/du-lieu-hao-hut",
		"2026-10-28 08:00:05.000001"),
	# Cùng tin gửi vào hai nhóm: hai dòng sổ, một tin.
	_tin("t2a", "hd_ket_ghi_so", "🚨 CẢNH BÁO: Kẹt ghi sổ\n- 3 đơn\nMở: " + APP + "/hoa-don-ban", "2026-10-28 07:30:01.000001"),
	_tin("t2b", "hd_ket_ghi_so", "🚨 CẢNH BÁO: Kẹt ghi sổ\n- 3 đơn\nMở: " + APP + "/hoa-don-ban", "2026-10-28 07:30:01.000002"),
	_tin("t3", "kho_da_chuyen", "ℹ️ THÔNG BÁO: Đã chuyển hàng giữa kho\nMở: " + APP + "/hang-chuyen-ve-kho-toi?mo=PDC-1",
		"2026-10-27 19:06:00.000001"),
	_tin("t4", "bep_du_lieu_hao_hut", "✅ VIỆC CẦN LÀM: Bếp Pastry ghi đủ lệnh\n- 6 món", "2026-10-28 08:00:06.000001"),
	_tin("t5", "bh_dat_ban", "✅ VIỆC CẦN LÀM: Đặt bàn mới\n- 4 khách", "2026-10-26 10:00:00.000001"),
	# Quá 14 ngày: không hiện.
	_tin("t6", "kt_du_lieu_hao_hut", "📊 BẢN TIN: tuần cũ", "2026-10-01 08:00:00.000001"),
]


def _chay(ham, phong_ban, vai=(), da_xem="", viec=2, so=None):
	"""Gọi một hàm mở ra ngoài của chuong.py với sổ tin giả. Trả (kết quả, mốc đã ghi)."""
	ghi = {}
	luu = {"vgb_chuong_xem": da_xem}

	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=None):
		assert dt == "Vagabond Tin Kenh"
		ma = set(filters["ma_tin"][1])
		moc = str(filters["creation"][1])
		ra = [dict(r, luc=r["creation"]) for r in (so or SO) if r["ma_tin"] in ma and r["creation"] >= moc]
		ra.sort(key=lambda r: r["creation"], reverse=True)
		return ra[:limit_page_length]

	fr = types.SimpleNamespace(
		session=types.SimpleNamespace(user="nv@vagabond.vn"),
		get_roles=lambda *a: list(vai),
		get_all=get_all,
		defaults=types.SimpleNamespace(
			get_user_default=lambda k, u=None: luu.get(k),
			set_user_default=lambda k, v, user=None: ghi.update({k: v}) or luu.update({k: v})),
	)
	vcl = types.SimpleNamespace(dem=lambda: {"tong": viec})
	with um.patch.object(ch, "frappe", fr), um.patch.object(ch, "_phong_ban", lambda u: phong_ban), \
			um.patch.object(ch, "now_datetime", lambda: "2026-10-28 09:00:00.000000"), \
			um.patch.object(ch, "add_days", lambda d, n: "2026-10-14 09:00:00.000000"), \
			um.patch.dict(sys.modules, {"vagabond.viec_can_lam": vcl}):
		import vagabond
		cu = getattr(vagabond, "viec_can_lam", None)
		vagabond.viec_can_lam = vcl
		try:
			return getattr(ch, ham)(), ghi
		finally:
			if cu is not None:
				vagabond.viec_can_lam = cu
			else:
				del vagabond.viec_can_lam


@ca("v619 chuông: kế toán thấy tin kế toán, đã gộp tin gửi hai nhóm, mới nhất trước, bỏ tin quá 14 ngày")
def _ke_toan():
	kq, _ = _chay("thong_bao", "Kế toán - TV")
	la("hai tin kế toán", [x["ten"] for x in kq["ds"]], ["t1", "t2b"])
	la("tách tiêu đề, thân, đường mở", [kq["ds"][0]["tieu_de"], kq["ds"][0]["than"], kq["ds"][0]["link"]],
		["📊 BẢN TIN: Dữ liệu hao hụt tuần 21/10 - 27/10", "Chưa đủ dữ liệu.", APP + "/du-lieu-hao-hut"])
	la("có phòng ban", kq["co_phong_ban"], 1)


@ca("v619 chuông: bếp thấy tin bếp; kho thấy tin kho; giám đốc và quản trị thấy hết; chưa gắn phòng ban thì không thấy")
def _ai_thay_gi():
	la("bếp Pastry", [x["ten"] for x in _chay("thong_bao", "Bếp Pastry - TV")[0]["ds"]], ["t4"])
	la("kho", [x["ten"] for x in _chay("thong_bao", "Kho - TV")[0]["ds"]], ["t3"])
	la("thu ngân", [x["ten"] for x in _chay("thong_bao", "Thu ngân - TV")[0]["ds"]], ["t5"])
	la("giám đốc theo vai", [x["ten"] for x in _chay("thong_bao", "", vai=("AP Giám đốc",))[0]["ds"]], ["t4", "t1", "t2b", "t3", "t5"])
	kq, _ = _chay("thong_bao", "")
	la("chưa gắn phòng ban", [kq["ds"], kq["co_phong_ban"]], [[], 0])
	la("phòng ban lạ cũng không thấy", _chay("thong_bao", "Phòng mới - TV")[0]["ds"], [])


@ca("v619 chuông: số đỏ = việc đang chờ + tin chưa đọc; mở thẻ Thông báo thì chỉ còn việc")
def _dem():
	kq, _ = _chay("dem", "Kế toán - TV", viec=3)
	la("chưa đọc gì", kq, {"viec": 3, "tin": 2, "tong": 5})
	kq, _ = _chay("dem", "Kế toán - TV", viec=3, da_xem="2026-10-28 08:00:00.000000")
	la("đã đọc tới trước tin 08:00:05", kq, {"viec": 3, "tin": 1, "tong": 4})
	_, ghi = _chay("da_xem", "Kế toán - TV")
	la("mở thẻ là ghi mốc", ghi, {"vgb_chuong_xem": "2026-10-28 09:00:00.000000"})
	kq, _ = _chay("dem", "Kế toán - TV", viec=0, da_xem=ghi["vgb_chuong_xem"])
	la("sau khi đọc", kq, {"viec": 0, "tin": 0, "tong": 0})


@ca("v619 chuông: Việc cần làm lỗi thì vẫn đếm tin, không ném lỗi ra trang chủ")
def _dem_loi():
	def hong():
		raise RuntimeError("lỗi đọc việc")
	ghi = {}
	fr = types.SimpleNamespace(session=types.SimpleNamespace(user="nv"), get_roles=lambda *a: [],
		get_all=lambda *a, **k: [dict(SO[0], luc=SO[0]["creation"])],
		defaults=types.SimpleNamespace(get_user_default=lambda k, u=None: "", set_user_default=lambda *a, **k: ghi))
	import vagabond
	cu = getattr(vagabond, "viec_can_lam", None)
	vagabond.viec_can_lam = types.SimpleNamespace(dem=hong)
	try:
		with um.patch.object(ch, "frappe", fr), um.patch.object(ch, "_phong_ban", lambda u: "Kế toán - TV"), \
				um.patch.dict(sys.modules, {"vagabond.viec_can_lam": vagabond.viec_can_lam}), \
				um.patch.object(ch, "add_days", lambda d, n: "2026-10-14"), um.patch.object(ch, "now_datetime", lambda: "2026-10-28"):
			la("việc 0, tin vẫn đếm", ch.dem(), {"viec": 0, "tin": 1, "tong": 1})
	finally:
		if cu is not None:
			vagabond.viec_can_lam = cu


@ca("v619 chuông: mọi phòng ban trên site đều có bộ phận tin, mọi bộ phận tin là bộ phận có thật")
def _bang():
	site = ["Bếp Baker - TV", "Bếp Pastry - TV", "Kế toán - TV", "Kho - TV", "Marketing - TV", "Pha chế - TV", "Sales - TV",
		"Sonneto Lab - TV", "Thu mua - TV", "Thu ngân - TV", "Vận hành - TV"]
	la("phòng ban site 28/10/2026 đều có tin", [p for p in site if not ch.bo_phan_cua(p)], [])
	la("bộ phận có thật", sorted({b for v in ch.BO_PHAN_TIN.values() if v != ch.TAT_CA for b in v} - set(kz.BO_PHAN)), [])
	dung("không ai ngoài giám đốc thấy tin Hệ thống", all("Hệ thống" not in v for v in ch.BO_PHAN_TIN.values() if v != ch.TAT_CA))
	la("tin không có dòng Mở", ch.tach_tin("A\nB"), ("A", "B", ""))
