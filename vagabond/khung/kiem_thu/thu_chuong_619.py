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


def _tin(name, ma, noi_dung, luc, trang_thai="Đã gửi"):
	return {"name": name, "ma_tin": ma, "noi_dung": noi_dung, "creation": luc, "trang_thai": trang_thai}


PHEP = {"in": lambda a, b: a in b, ">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
	"<": lambda a, b: a < b, "<=": lambda a, b: a <= b}


def _loc(r, filters):
	"""Lọc như frappe.get_all: dict {trường: [phép, giá trị]} hay danh sách [trường, phép, giá trị]."""
	ds = filters.items() if isinstance(filters, dict) else [(f[0], f[1:]) for f in filters]
	return all(PHEP[ph](r[tr], (list(gt) if ph == "in" else str(gt))) for tr, (ph, gt) in ds)


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


def _chay(ham, phong_ban, vai=(), da_xem="", viec=2, so=None, ts=None):
	"""Gọi một hàm mở ra ngoài của chuong.py với sổ tin giả. Trả (kết quả, mốc đã ghi)."""
	ghi = {}
	luu = {"vgb_chuong_xem": da_xem}

	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=None):
		assert dt == "Vagabond Tin Kenh" and order_by == "creation desc"
		ra = [dict(r, luc=r["creation"]) for r in (so or SO) if _loc(r, filters)]
		ra.sort(key=lambda r: r["creation"], reverse=True)
		return ra[:limit_page_length] if limit_page_length else ra

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
			return getattr(ch, ham)(**(ts or {})), ghi
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


@ca("v619 chuông: chỉ tin đã gửi thật (cả gửi gộp); tin bỏ qua vì đã xử lý, chờ, hoãn, lỗi không hiện, không đếm")
def _chi_tin_da_gui():
	# Codex 4404477900 (81dfbe70): bản cũ hiện và đếm cả các tin bo, loi, cho, hoan.
	so = [_tin("gui", "kt_du_lieu_hao_hut", "A\nđã gửi", "2026-10-28 08:00:00.000001"),
		_tin("gop", "kt_du_lieu_hao_hut", "B\ngửi gộp giờ im", "2026-10-28 07:30:00.000001", "Đã gửi gộp"),
		_tin("bo", "kt_du_lieu_hao_hut", "C\nviệc đã xong", "2026-10-28 07:00:00.000001", "Bỏ qua (đã xử lý)"),
		_tin("loi", "kt_du_lieu_hao_hut", "D\ngửi lỗi", "2026-10-28 06:00:00.000001", "Lỗi"),
		_tin("cho", "kt_du_lieu_hao_hut", "E\nđang chờ", "2026-10-28 05:00:00.000001", "Chờ gửi"),
		_tin("hoan", "kt_du_lieu_hao_hut", "F\nhoãn giờ im", "2026-10-28 04:00:00.000001", "Hoãn giờ im")]
	la("màn chỉ có tin đã gửi", [x["ten"] for x in _chay("thong_bao", "Kế toán - TV", so=so)[0]["ds"]], ["gui", "gop"])
	la("số đỏ chỉ đếm tin đã gửi", _chay("dem", "Kế toán - TV", so=so, viec=0)[0], {"viec": 0, "tin": 2, "tong": 2})


def _nhieu(n, dau="2026-10-20 00:00:00", ma="kt_du_lieu_hao_hut"):
	from datetime import datetime, timedelta
	g = datetime.fromisoformat(dau)
	return [_tin("n%03d" % i, ma, "Tin %03d\nthân" % i, str(g + timedelta(minutes=7 * i)) + ".000001") for i in range(n)]


@ca("v619 chuông: hơn 60 tin chưa đọc thì hiện hết, chỉ đánh dấu tới tin đã hiện; tin đã đọc có trang cũ hơn")
def _trang():
	# Codex 4404477923 (81dfbe70): 61 tin chưa đọc, bản cũ chỉ hiện 60 và mở màn là tin thứ 61 thành đã đọc.
	so = _nhieu(61)
	kq, _ = _chay("thong_bao", "Kế toán - TV", so=so)
	la("61 tin chưa đọc hiện đủ 61", [len(kq["ds"]), sum(x["moi"] for x in kq["ds"])], [61, 61])
	la("mốc mới là tin mới nhất đã hiện", kq["moc_moi"], so[-1]["creation"])
	_, ghi = _chay("da_xem", "Kế toán - TV", so=so, ts={"den": kq["moc_moi"]})
	la("đánh dấu tới tin đã hiện, không tới bây giờ", ghi, {"vgb_chuong_xem": so[-1]["creation"]})
	la("đọc xong không còn tin mới", _chay("dem", "Kế toán - TV", so=so, viec=0, da_xem=ghi["vgb_chuong_xem"])[0],
		{"viec": 0, "tin": 0, "tong": 0})
	so2 = so + [_tin("sau", "kt_du_lieu_hao_hut", "Tin tới sau\nx", "2026-10-28 08:59:00.000001")]
	la("tin tới sau lúc mở màn vẫn là tin mới", _chay("dem", "Kế toán - TV", so=so2, viec=0, da_xem=ghi["vgb_chuong_xem"])[0],
		{"viec": 0, "tin": 1, "tong": 1})
	# Đã đọc 70 tin: trang đầu 60, còn nút xem cũ hơn; trang sau 10 tin còn lại, hết.
	so = _nhieu(70)
	moc = so[-1]["creation"]
	kq, _ = _chay("thong_bao", "Kế toán - TV", so=so, da_xem=moc)
	la("trang đầu 60 tin đã đọc, còn tin cũ hơn", [len(kq["ds"]), kq["con_nua"], sum(x["moi"] for x in kq["ds"])], [60, 1, 0])
	kq2, _ = _chay("thong_bao", "Kế toán - TV", so=so, da_xem=moc, ts={"truoc": kq["ds"][-1]["luc"]})
	la("trang sau đủ 10 tin còn lại, hết", [len(kq2["ds"]), kq2["con_nua"], kq2["ds"][0]["ten"], kq2["ds"][-1]["ten"]],
		[10, 0, "n009", "n000"])
	la("không trùng tin giữa hai trang", len({x["ten"] for x in kq["ds"] + kq2["ds"]}), 70)
	# Đã đọc 5, có 3 mới: 3 mới đứng đầu rồi tới 5 cũ.
	so = _nhieu(8)
	kq, _ = _chay("thong_bao", "Kế toán - TV", so=so, da_xem=so[4]["creation"])
	la("tin mới đứng đầu, rồi tin cũ", [x["moi"] for x in kq["ds"]], [1, 1, 1, 0, 0, 0, 0, 0])
	_, ghi = _chay("da_xem", "Kế toán - TV", so=so, da_xem="2026-10-28 08:00:00.000000", ts={"den": so[0]["creation"]})
	la("mốc không lùi", ghi, {})


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
