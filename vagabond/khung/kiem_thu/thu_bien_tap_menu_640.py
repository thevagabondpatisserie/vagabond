"""Ca kiểm v640 Biên tập menu (anh Việt duyệt mẫu 05/11/2026): menu theo điểm bán,
bản nháp rồi xuất bản, một nguồn cho trang bàn (kiem_kho feed, cửa gọi món) và
màn Tính tiền (pos_ds_tuy_chon). Phần trình duyệt nạp thật trong node:
hanh_vi/bien_tap_menu_640.js (màn app), hanh_vi/goi_mon_ban_638.mjs (trang khách).
"""
import json
import subprocess
import sys
import threading
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import diem_ban, kiem_kho  # noqa: E402
from vagabond import bien_tap_menu as btm  # noqa: E402
from vagabond import goi_mon_ban as g  # noqa: E402

GOC = Path(__file__).resolve().parents[3]

# Dữ liệu thật trên site 05/11/2026: một dòng "Vagabond Tuy Chon Mon" gồm cả đá,
# đường và "Thay sữa yến mạch" (ảnh anh Việt chụp Kombucha hiện cả sữa yến mạch).
TC_CU = [{"nhom": "Đá / Đường", "lua_chon": ["Đá riêng", "50% đá", "0% đá", "50% đường", "0% đường", "Thay sữa yến mạch"],
	"nhom_mon": ["Trà", "Cà phê", "Matcha", "Cacao", "Ice Cream - Kem"]}]
UONG = [
	{"ma": "NUTR00090", "ten": "Kombucha Cherry", "gia": 120000, "anh": "/files/kom.jpg", "nhom_goc": "Trà", "ban_web": 1, "khong_pha": 0, "mo_ta": "Lên men"},
	{"ma": "NUTR00031", "ten": "Trà Sữa Lài Kem Phô Mai, Size M, Đá/Iced", "gia": 75000, "anh": "", "nhom_goc": "Trà", "ban_web": 1, "khong_pha": 0, "mo_ta": ""},
	{"ma": "NUTR00040", "ten": "Kombucha Chill , Chai 300ml", "gia": 100000, "anh": "", "nhom_goc": "Trà", "ban_web": 1, "khong_pha": 1, "mo_ta": ""},
	{"ma": "NUCF00003", "ten": "Cà phê sữa", "gia": 40000, "anh": "", "nhom_goc": "Cà phê", "ban_web": 1, "khong_pha": 0, "mo_ta": ""},
	{"ma": "NUIC00002", "ten": "Kem Vani", "gia": 30000, "anh": "", "nhom_goc": "Ice Cream - Kem", "ban_web": 1, "khong_pha": 0, "mo_ta": ""},
]
TOP = [{"ma": "TPNC00001", "ten": "Trân châu ô long", "gia": 10000}, {"ma": "TPNC00005", "ten": "Thêm Cà Phê Phin", "gia": 15000}]


def _menu():
	return btm.menu_mac_dinh(UONG, TOP, TC_CU)


@ca("v640 menu mặc định từ dữ liệu cũ: khung \"Đá / Đường\" tách thành Đá, Đường (mặc định Bình thường) và Tuỳ chọn khác; nhóm theo nhóm gốc, đúng thứ tự; topping áp mọi nhóm như v639")
def _mac_dinh():
	m = _menu()
	la("nhóm", [(x["ma"], x["ten"], x.get("mon")) for x in m["nhom"]],
		[("banh", "Bánh trên tủ", None), ("n-tra", "Trà", ["NUTR00090", "NUTR00031", "NUTR00040"]), ("n-ca-phe", "Cà phê", ["NUCF00003"]),
			("n-ice-cream-kem", "Kem", ["NUIC00002"])])
	la("tuỳ chọn", [(t["ten"], t["muc"], t["mac_dinh"], t["ap"]) for t in m["tuy_chon"]],
		[("Đá", ["Bình thường", "Đá riêng", "50% đá", "0% đá"], "Bình thường", ["n-tra", "n-ca-phe", "n-ice-cream-kem"]),
			("Đường", ["Bình thường", "50% đường", "0% đường"], "Bình thường", ["n-tra", "n-ca-phe", "n-ice-cream-kem"]),
			("Tuỳ chọn khác", ["Thay sữa yến mạch"], "", ["n-tra", "n-ca-phe", "n-ice-cream-kem"])])
	la("topping áp mọi nhóm nước", m["topping"], {"TPNC00001": ["n-tra", "n-ca-phe", "n-ice-cream-kem"], "TPNC00005": ["n-tra", "n-ca-phe", "n-ice-cream-kem"]})
	# Nhóm cũ chỉ khai một số nhóm món thì Đá chỉ áp đúng các nhóm đó; nhóm chỉ có "Ít ngọt" giữ tên cũ.
	t = btm.tach_tuy_chon_cu([{"nhom": "Đá", "lua_chon": ["Ít đá"], "nhom_mon": ["Trà"]}, {"nhom": "Đá", "lua_chon": ["Không đá"], "nhom_mon": []},
		{"nhom": "Độ ngọt", "lua_chon": ["Ít ngọt"], "nhom_mon": ["Cacao"]}])
	la("gộp nhóm trùng tên, rỗng là mọi nhóm", [(x["ten"], x["muc"], x["ap_goc"]) for x in t],
		[("Đá", ["Bình thường", "Ít đá", "Không đá"], []), ("Độ ngọt", ["Ít ngọt"], ["Cacao"])])


@ca("v640 chuẩn hoá menu quản lý gửi: bỏ mã lạ và món trùng nhóm, luôn có nhóm Bánh, mặc định sai thì bỏ, tên nhóm trùng thì nói rõ")
def _chuan():
	ma = {x["ma"] for x in UONG}
	tp = {x["ma"] for x in TOP}
	m = btm.chuan_menu({"nhom": [{"ma": "n-tra", "ten": " Trà ", "loai": "nuoc", "mon": ["NUTR00090", "LA", "NUTR00090"]},
		{"ma": "n-tra-sua", "ten": "Trà sữa", "mon": ["NUTR00090", "NUTR00031"], "hien": 0}],
		"tuy_chon": [{"ten": "Đá", "muc": ["Bình thường", "Ít đá", "ít đá"], "mac_dinh": "Nhiều đá", "ap": ["n-tra", "n-la"]}],
		"topping": {"TPNC00001": ["n-tra-sua", "x"], "LA": ["n-tra"]}, "an": ["NUTR00031", "LA"],
		"mon": {"NUTR00090": {"mo_ta": "  Cherry  ", "tat_tc": ["Đá", "Không có"], "tat_tp": ["TPNC00001", "LA"]}, "LA": {"mo_ta": "x"}}}, ma, tp)
	la("nhóm: có Bánh, bỏ mã lạ, món chỉ ở một nhóm", [(x["ma"], x["ten"], x.get("mon"), x["hien"]) for x in m["nhom"]],
		[("banh", "Bánh trên tủ", None, 1), ("n-tra", "Trà", ["NUTR00090"], 1), ("n-tra-sua", "Trà sữa", ["NUTR00031"], 0)])
	la("tuỳ chọn: mức trùng bỏ, mặc định sai bỏ, áp nhóm lạ bỏ", m["tuy_chon"], [{"ten": "Đá", "muc": ["Bình thường", "Ít đá"], "mac_dinh": "", "ap": ["n-tra"]}])
	la("topping, ẩn, sửa riêng", [m["topping"], m["an"], m["mon"]],
		[{"TPNC00001": ["n-tra-sua"]}, ["NUTR00031"], {"NUTR00090": {"mo_ta": "Cherry", "tat_tc": ["Đá"], "tat_tp": ["TPNC00001"]}}])
	nem("hai nhóm cùng tên", lambda: btm.chuan_menu({"nhom": [{"ma": "n-a", "ten": "Trà"}, {"ma": "n-b", "ten": "TRÀ"}]}, ma, tp), ValueError)
	nem("nhóm tuỳ chọn không mức", lambda: btm.chuan_menu({"nhom": [], "tuy_chon": [{"ten": "Đá", "muc": []}]}, ma, tp), ValueError)
	nem("mã nhóm lạ", lambda: btm.chuan_menu({"nhom": [{"ma": "Tra <b>", "ten": "Trà"}]}, ma, tp), ValueError)
	nem("chuỗi hỏng", lambda: btm.chuan_menu("{x", ma, tp), ValueError)


@ca("v640 áp menu lên đồ uống: thứ tự nhóm rồi thứ tự món; nhóm tắt, món ẩn, món chưa xếp, nhóm rỗng không lên web; tuỳ chọn, topping theo nhóm trừ phần tắt riêng; chai không hỏi; mô tả sửa riêng")
def _ap():
	m = _menu()
	m["nhom"] = [m["nhom"][2], m["nhom"][0], m["nhom"][1], m["nhom"][3]]  # Cà phê, Bánh, Trà, Kem
	m["nhom"][3]["hien"] = 0  # Kem ẩn
	m["nhom"][2]["mon"] = ["NUTR00040", "NUTR00090"]  # Trà sữa (NUTR00031) chưa xếp
	m["an"] = ["NUCF00003"]  # nhóm Cà phê còn rỗng
	m["topping"]["TPNC00005"] = ["n-ca-phe"]
	m["mon"] = {"NUTR00090": {"mo_ta": "Cherry chín mọng", "tat_tc": ["Tuỳ chọn khác"]}}
	nhom, uong = btm.ap_menu(m, UONG)
	la("nhóm lên web", [(x["ma"], x["loai"]) for x in nhom], [("banh", "banh"), ("n-tra", "nuoc")])
	la("món theo thứ tự trong nhóm", [x["ma"] for x in uong], ["NUTR00040", "NUTR00090"])
	kom = uong[1]
	la("Kombucha: Đá, Đường; tắt riêng Tuỳ chọn khác; chỉ Trân châu; mô tả riêng", [[t["nhom"] for t in kom["tc"]], kom["tc"][0]["mac_dinh"], kom["tp"], kom["mo_ta"], kom["nhom_hien"]],
		[["Đá", "Đường"], "Bình thường", ["TPNC00001"], "Cherry chín mọng", "n-tra"])
	la("chai: không tuỳ chọn, không topping", [uong[0]["tc"], uong[0]["tp"]], [[], []])
	la("món chưa xếp", btm.mon_chua_xep(m, UONG), ["NUTR00031"])
	la("món chưa xếp: màn Tính tiền vẫn hỏi theo nhóm gốc", [t["nhom"] for t in btm.tc_cua_mon(m, "NUTR00031", "Trà")], ["Đá", "Đường", "Tuỳ chọn khác"])


@ca("v640 màn Tính tiền đọc menu của quầy: mỗi đồ uống một danh sách nhóm (có mặc định), danh sách theo nhóm gốc cho món lạ; nhóm tuỳ chọn không áp nhóm nào thì bỏ hẳn (rỗng ở bản cũ là mọi nhóm)")
def _quay():
	m = _menu()
	m["tuy_chon"][2]["ap"] = []
	r = btm.tc_cho_quay(m, UONG)
	la("theo món", {k: [(t["nhom"], t["mac_dinh"]) for t in v] for k, v in r["mon"].items()},
		{"NUTR00090": [("Đá", "Bình thường"), ("Đường", "Bình thường")], "NUTR00031": [("Đá", "Bình thường"), ("Đường", "Bình thường")],
			"NUCF00003": [("Đá", "Bình thường"), ("Đường", "Bình thường")], "NUIC00002": [("Đá", "Bình thường"), ("Đường", "Bình thường")],
			"NUTR00040": []})
	# Codex PR #543: món quản lý tắt HẾT tuỳ chọn vẫn phải có mục rỗng trong "mon",
	# không thì màn Tính tiền rơi về tuỳ chọn theo nhóm gốc và hiện lại thứ vừa tắt.
	m2 = _menu()
	m2["mon"] = {"NUTR00090": {"tat_tc": ["Đá", "Đường", "Tuỳ chọn khác"]}}
	r3 = btm.tc_cho_quay(m2, UONG)
	la("tắt hết tuỳ chọn: mục rỗng, không vắng", [r3["mon"].get("NUTR00090", "VẮNG"), r3["mon"].get("NUTR00040", "VẮNG")], [[], []])
	la("theo nhóm gốc", [(t["nhom"], t["nhom_mon"]) for t in r["tc"]], [("Đá", ["Cà phê", "Ice Cream - Kem", "Trà"]), ("Đường", ["Cà phê", "Ice Cream - Kem", "Trà"])])
	with patch.object(diem_ban, "ma_theo_quay", side_effect=lambda q: q), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: UONG), patch.object(g, "topping_cua_diem", side_effect=lambda ma: TOP), \
			patch.object(btm, "menu_dang_chay", side_effect=lambda d: ((m, 3) if d == "NVHTN" else (None, 0))), \
			patch.object(g, "doc_tuy_chon", return_value=TC_CU):
		r1 = btm.tc_theo_quay("NVHTN")
		r2 = btm.tc_theo_quay("TCV")
	la("NVHTN đọc đúng menu của nó (Tuỳ chọn khác đã bỏ)", sorted({t["nhom"] for v in r1["mon"].values() for t in v}), ["Đá", "Đường"])
	la("TCV chưa xuất bản: menu mặc định có Tuỳ chọn khác", sorted({t["nhom"] for v in r2["mon"].values() for t in v}), ["Tuỳ chọn khác", "Đá", "Đường"])
	# ban_hang kéo thư viện mạng ở đầu tệp nên bộ kiểm không nạp nó (thu_ma_vach
	# chặn). Đọc thân pos_ds_tuy_chon: không truyền quầy giữ như trước v640,
	# có quầy thì chuyển hẳn cho tc_theo_quay (không tự tính lần hai).
	src = (GOC / "vagabond" / "ban_hang.py").read_text(encoding="utf-8")
	than = src.split("def pos_ds_tuy_chon(quay=None):", 1)[1].split("\ndef ", 1)[0]
	dung("app cũ không truyền quầy: như trước v640", 'if not quay:\n\t\treturn {"tc": doc_tuy_chon()}' in than)
	dung("có quầy: một nguồn tc_theo_quay", "return bien_tap_menu.tc_theo_quay(quay)" in than and "tc_cho_quay" not in than)


@ca("v640 cửa gọi món chặn theo menu: món ẩn không gọi được, topping không khai cho món thì báo, mức mặc định không ghi lên bill")
def _chan():
	m = _menu()
	m["an"] = ["NUCF00003"]
	m["topping"]["TPNC00005"] = ["n-ca-phe"]
	d = {"ma": "TCV", "ten": "District 1"}
	import datetime
	with patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: UONG), patch.object(g, "topping_cua_diem", side_effect=lambda ma: TOP), \
			patch.object(btm, "menu_dang_chay", return_value=(m, 1)), patch.object(g, "_da_nhan_cua", return_value=[]), patch.object(g, "_cho_cua", return_value=[]), \
			patch.object(g, "_phieu_tam_mo", return_value=set()), patch.object(kiem_kho, "banh_tren_quay", return_value=[]), \
			patch.object(diem_ban, "gia_rieng", return_value={}), patch.object(g, "now_datetime", return_value=datetime.datetime(2026, 11, 5, 10, 0)):
		bang = g.bang_mon(d)
	dung("món ẩn không có trong bảng", "NUCF00003" not in bang)
	la("Kombucha kèm được", bang["NUTR00090"]["tp_cho"], ["TPNC00001"])
	try:
		g.chuan_gio([{"ma": "NUTR00090", "sl": 1, "tp": ["TPNC00005"]}], bang)
		dung("phải chặn topping cà phê cho Kombucha", False)
	except ValueError as e:
		dung("câu nêu món và topping", "Kombucha Cherry" in str(e) and "Thêm Cà Phê Phin" in str(e))
	dong, tam = g.chuan_gio([{"ma": "NUTR00090", "sl": 2, "tc": {"Đá": "Bình thường", "Đường": "50% đường"}, "tp": ["TPNC00001"]}], bang)
	la("mặc định không ghi, mức khác ghi", [dong[0]["tc"], tam], [["50% đường"], 260000])
	try:
		g.chuan_gio([{"ma": "NUCF00003", "sl": 1}], bang)
		dung("phải chặn món ẩn", False)
	except ValueError as e:
		dung("món ẩn: báo tải lại", "tải lại" in str(e))


class Kho:
	"""Bảng Vagabond Menu giả, đủ cho mo / luu_nhap / xuat_ban / bo_nhap / khoi_phuc."""
	def __init__(self):
		self.dong, self.so = {}, 0
		self.khoa, self.mu = {}, threading.Lock()

	def get_all(self, dt, filters=None, fields=None, order_by=None, limit_page_length=None, **k):
		assert dt == btm.DT
		ra = [dict(r) for r in self.dong.values() if all(r.get(a) == b for a, b in (filters or {}).items())]
		ra.sort(key=lambda r: (-int(r.get("phien") or 0), -r["_tt"]))
		ra = ra[:limit_page_length] if limit_page_length else ra
		return [_fr._dict(r) for r in ra]

	def get_doc(self, d, *a, **k):
		kho = self

		class Doc(dict):
			def insert(self, **kk):
				kho.so += 1
				self["name"] = "MENU-%s-%05d" % (self["diem"], kho.so)
				self["_tt"] = kho.so
				kho.dong[self["name"]] = dict(self)
				return self

			@property
			def name(self):
				return self["name"]
		return Doc(d)

	def set_value(self, dt, ten, gt, *a, **k):
		self.dong[ten].update(gt)

	def sql(self, cau, ts=None, **k):
		if "get_lock(" in cau:
			with self.mu:
				kt = self.khoa.setdefault(ts[0], threading.Lock())
			return [[1 if kt.acquire(timeout=float(ts[1])) else 0]]
		if "release_lock(" in cau:
			kt = self.khoa.get(ts[0])
			if kt and kt.locked():
				kt.release()
			return [[1]]
		return []


def _he(kho, vai=("VGB - Quản lý cửa hàng",)):
	return [patch.object(_fr, "get_all", side_effect=kho.get_all), patch.object(_fr, "get_doc", side_effect=kho.get_doc),
		patch.object(_fr.db, "set_value", side_effect=kho.set_value), patch.object(_fr.db, "sql", side_effect=kho.sql),
		patch.object(_fr.db, "commit", lambda *a, **k: None), patch.object(_fr, "get_roles", return_value=list(vai)),
		patch.object(btm, "_diem_co_quay", return_value=[{"ma": "TCV", "ten": "The Vagabond District 1", "ten_ngan": "District 1", "quay": "TCV"},
			{"ma": "NVHTN", "ten": "Nhà Văn Hóa Thanh Niên", "ten_ngan": "NVHTN", "quay": "NVHTN"}]),
		patch.object(btm, "_du_lieu", side_effect=lambda d, n=None: (UONG if d == "TCV" else UONG[:2], TOP)),
		patch.object(g, "doc_tuy_chon", return_value=TC_CU)]


class _Moi:
	def __init__(self, ds):
		self.ds = ds

	def __enter__(self):
		for p in self.ds:
			p.start()

	def __exit__(self, *a):
		for p in reversed(self.ds):
			p.stop()


@ca("v640 nháp rồi xuất bản: mở là nháp bằng menu đang chạy; lưu nháp khách chưa thấy; xuất bản thành phiên 1, menu đang chạy đổi; mỗi điểm một menu; bỏ nháp; quay về phiên cũ thành phiên mới; chỉ quản lý")
def _vong_doi():
	kho = Kho()
	with _Moi(_he(kho)):
		r = btm.mo()
		la("mặc định điểm đầu, chưa thay đổi", [r["diem"], r["phien"], r["thay_doi"], [x["ma"] for x in r["cac_diem"]]], ["TCV", 0, [], ["TCV", "NVHTN"]])
		nhap = r["nhap"]
		nhap["nhom"] = [nhap["nhom"][0], nhap["nhom"][2], nhap["nhom"][1], nhap["nhom"][3]]
		nhap["an"] = ["NUIC00002"]
		nhap["topping"]["TPNC00005"] = ["n-ca-phe"]
		k = btm.luu_nhap(diem="TCV", noi_dung=json.dumps(nhap))
		la("thay đổi đọc được", k["thay_doi"], ["Đổi thứ tự nhóm: Bánh trên tủ, Cà phê, Trà, Kem", "Ẩn Kem Vani trên web", "Topping Thêm Cà Phê Phin: áp cho Cà phê"])
		la("khách chưa thấy: chưa có bản xuất bản", btm.menu_dang_chay("TCV"), (None, 0))
		x = btm.xuat_ban(diem="TCV")
		la("phiên 1", x["phien"], 1)
		m, p = btm.menu_dang_chay("TCV")
		la("menu đang chạy đổi theo nháp", [p, [g2["ma"] for g2 in m["nhom"]], m["an"]], [1, ["banh", "n-ca-phe", "n-tra", "n-ice-cream-kem"], ["NUIC00002"]])
		la("NVHTN vẫn chưa có menu riêng", btm.menu_dang_chay("NVHTN"), (None, 0))
		la("mở lại: nháp bằng đang chạy, không thay đổi", btm.mo(diem="TCV")["thay_doi"], [])
		la("xuất bản lại khi không đổi gì: không thêm phiên", btm.xuat_ban(diem="TCV").get("khong_doi"), 1)
		# NVHTN: menu nhỏ hơn, độc lập
		n = btm.mo(diem="NVHTN")
		la("NVHTN chỉ có món của NVHTN", sorted(x["ma"] for x in n["mon"]), ["NUTR00031", "NUTR00090"])
		nn = n["nhap"]
		nn["an"] = ["NUTR00031"]
		btm.luu_nhap(diem="NVHTN", noi_dung=json.dumps(nn))
		btm.xuat_ban(diem="NVHTN")
		la("NVHTN phiên 1 riêng", [btm.menu_dang_chay("NVHTN")[1], btm.menu_dang_chay("NVHTN")[0]["an"], btm.menu_dang_chay("TCV")[0]["an"]], [1, ["NUTR00031"], ["NUIC00002"]])
		# sửa tiếp TCV, bỏ nháp
		r = btm.mo(diem="TCV")
		r["nhap"]["an"] = []
		btm.luu_nhap(diem="TCV", noi_dung=json.dumps(r["nhap"]))
		la("có nháp", btm.mo(diem="TCV")["thay_doi"], ["Hiện lại Kem Vani trên web"])
		btm.bo_nhap(diem="TCV")
		la("bỏ nháp: hết thay đổi", btm.mo(diem="TCV")["thay_doi"], [])
		# xuất phiên 2 rồi quay về phiên 1
		r = btm.mo(diem="TCV")
		r["nhap"]["an"] = []
		btm.luu_nhap(diem="TCV", noi_dung=json.dumps(r["nhap"]))
		la("phiên 2", btm.xuat_ban(diem="TCV")["phien"], 2)
		la("lịch sử mới nhất trước", [x["phien"] for x in btm.mo(diem="TCV")["lich_su"]], [2, 1])
		la("quay về phiên 1 thành phiên 3", btm.khoi_phuc(diem="TCV", phien=1)["phien"], 3)
		m3, p3 = btm.menu_dang_chay("TCV")
		la("phiên 3 mang nội dung phiên 1", [p3, m3["an"]], [3, ["NUIC00002"]])
		dung("ghi chú phiên 3", btm.mo(diem="TCV")["lich_su"][0]["thay_doi"].startswith("Quay về bản phiên 1"))
		nem("điểm lạ", lambda: btm.mo(diem="XYZ"), _fr.ValidationError)
		nem("menu hỏng", lambda: btm.luu_nhap(diem="TCV", noi_dung="{x"), _fr.ValidationError)
	with _Moi(_he(kho, vai=("Sales User",))):
		nem("nhân viên quầy không mở được", lambda: btm.mo(), Exception)
		nem("nhân viên quầy không xuất bản được", lambda: btm.xuat_ban(diem="TCV"), Exception)


@ca("v640 hai quản lý bấm Xuất bản cùng lúc: khoá theo điểm, không ra hai bản cùng phiên")
def _dua():
	kho = Kho()
	cho = threading.Barrier(2)
	goc = btm.menu_dang_chay

	def doi(d):
		r = goc(d)
		try:
			cho.wait(timeout=0.5)
		except threading.BrokenBarrierError:
			pass
		return r
	with _Moi(_he(kho)):
		r = btm.mo(diem="TCV")
		r["nhap"]["an"] = ["NUIC00002"]
		btm.luu_nhap(diem="TCV", noi_dung=json.dumps(r["nhap"]))
		kq = []
		with patch.object(btm, "menu_dang_chay", side_effect=doi):
			ts = [threading.Thread(target=lambda: kq.append(btm._xuat("TCV", r["nhap"], ["x"]))) for _ in range(2)]
			for t in ts:
				t.start()
			for t in ts:
				t.join(10)
	phien = sorted(int(x["phien"]) for x in kho.dong.values() if x["loai"] == btm.XUAT)
	la("hai bản, hai phiên khác nhau", [sorted(kq), phien], [[1, 2], [1, 2]])


@ca("v640 tab Tại quầy theo menu: nhom_menu đúng thứ tự, đồ uống mang nhom_hien, tp; món ẩn không lên; nút cửa mới khai trong cửa ngõ")
def _feed():
	m = _menu()
	m["nhom"] = [m["nhom"][1], m["nhom"][0], m["nhom"][2], m["nhom"][3]]
	m["an"] = ["NUTR00031"]
	diem = [dict(ma="TCV", ten="The Vagabond District 1", ten_ngan="District 1", dia_chi="9 TCV", quay="TCV")]
	lib = sys.modules.get("vagabond.lib")
	with patch.object(kiem_kho, "_diem_co_quay", return_value=diem), patch.object(kiem_kho, "banh_tren_quay", return_value=[]), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: UONG), patch.object(g, "topping_cua_diem", side_effect=lambda ma: TOP), \
			patch.object(btm, "menu_dang_chay", return_value=(m, 2)), patch.object(diem_ban, "gia_rieng", return_value={}), \
			patch.object(lib, "cfg", return_value=_fr._dict(pancake_shop_id="")), patch.object(lib, "key", return_value=""):
		q = kiem_kho.con_tren_quay_web()["quay"][0]
	la("nhóm theo menu", [x["ma"] for x in q["nhom_menu"]], ["n-tra", "banh", "n-ca-phe", "n-ice-cream-kem"])
	la("đồ uống theo menu, món ẩn không lên", [(x["ma"], x["nhom_hien"]) for x in q["do_uong"]],
		[("NUTR00090", "n-tra"), ("NUTR00040", "n-tra"), ("NUCF00003", "n-ca-phe"), ("NUIC00002", "n-ice-cream-kem")])
	la("tp theo món", [x["tp"] for x in q["do_uong"]], [["TPNC00001", "TPNC00005"], [], ["TPNC00001", "TPNC00005"], ["TPNC00001", "TPNC00005"]])
	s = (GOC / "vagabond/khung/kiem_thu/thu_cua_ngo.py").read_text()
	for ten in ("mo", "luu_nhap", "xuat_ban", "bo_nhap", "khoi_phuc"):
		dung("cửa ngõ khai %s" % ten, '"%s"' % ten in s.split('"bien_tap_menu.py"')[1].split("]")[0])


@ca("v640 màn Biên tập menu chạy thật trong node (hanh_vi/bien_tap_menu_640.js)")
def _node():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/bien_tap_menu_640.js")], capture_output=True, text=True, timeout=120)
	dung("node chạy được: " + (r.stdout[-1500:] + r.stderr[-800:]), r.returncode == 0)
	dung("đủ số ca", "17 ca dat, 0 ca hong" in r.stdout)


@ca("v642 (anh Việt 06/11/2026): tuỳ chọn, topping riêng từng món ba nấc: Có bật thêm dù nhóm không áp, Không tắt, Theo nhóm; trang bàn, cửa gọi món và màn Tính tiền cùng thấy")
def _rieng_ba_nac():
	m = _menu()
	# Nhóm tuỳ chọn mới chưa áp nhóm món nào; một topping chưa áp nhóm nào.
	m["tuy_chon"].append({"ten": "Nhiệt độ", "muc": ["Đá", "Nóng"], "mac_dinh": "Đá", "ap": []})
	m["topping"]["TPNC00005"] = []
	m["mon"] = {"NUTR00090": {"bat_tc": ["Nhiệt độ"], "tat_tc": ["Đường"], "bat_tp": ["TPNC00005"], "tat_tp": ["TPNC00001"]}}
	ma_hop_le = {x["ma"] for x in UONG}
	tp_hop_le = {x["ma"] for x in TOP}
	c = btm.chuan_menu(json.loads(json.dumps(m)), ma_hop_le, tp_hop_le)
	la("chuẩn hoá giữ bat_tc, bat_tp", c["mon"]["NUTR00090"],
		{"bat_tc": ["Nhiệt độ"], "tat_tc": ["Đường"], "bat_tp": ["TPNC00005"], "tat_tp": ["TPNC00001"]})
	la("tuỳ chọn của món: theo thứ tự bảng, có Nhiệt độ, không Đường",
		[t["nhom"] for t in btm.tc_cua_mon(c, "NUTR00090", "Trà")], ["Đá", "Tuỳ chọn khác", "Nhiệt độ"])
	la("topping của món: bật riêng Thêm Cà Phê Phin, tắt Trân châu", btm.tp_cua_mon(c, "NUTR00090", "Trà"), ["TPNC00005"])
	la("món khác cùng nhóm không bị ảnh hưởng", ([t["nhom"] for t in btm.tc_cua_mon(c, "NUTR00031", "Trà")], btm.tp_cua_mon(c, "NUTR00031", "Trà")),
		(["Đá", "Đường", "Tuỳ chọn khác"], ["TPNC00001"]))
	la("món đóng sẵn vẫn không hỏi gì dù có bật riêng", btm.tc_cua_mon(c, "NUTR00040", "Trà", khong_pha=True), [])
	_nhom, uong = btm.ap_menu(c, UONG)
	kom = next(x for x in uong if x["ma"] == "NUTR00090")
	la("trang bàn (ap_menu) dùng cùng phép", ([t["nhom"] for t in kom["tc"]], kom["tp"]), (["Đá", "Tuỳ chọn khác", "Nhiệt độ"], ["TPNC00005"]))
	la("màn Tính tiền (tc_cho_quay) dùng cùng phép", [t["nhom"] for t in btm.tc_cho_quay(c, UONG)["mon"]["NUTR00090"]],
		["Đá", "Tuỳ chọn khác", "Nhiệt độ"])
	# Dữ liệu sửa tay ghi cùng mục ở cả hai nấc: Không thắng.
	m2 = json.loads(json.dumps(m))
	m2["mon"]["NUTR00090"] = {"bat_tc": ["Đá"], "tat_tc": ["Đá"], "bat_tp": ["TPNC00001"], "tat_tp": ["TPNC00001"]}
	c2 = btm.chuan_menu(m2, ma_hop_le, tp_hop_le)
	la("một mục hai nấc: Không thắng", c2["mon"]["NUTR00090"], {"tat_tc": ["Đá"], "tat_tp": ["TPNC00001"]})
	# Tên tuỳ chọn, mã topping không còn thì bỏ lặng lẽ.
	m3 = json.loads(json.dumps(m))
	m3["mon"]["NUTR00090"] = {"bat_tc": ["Không có"], "bat_tp": ["TPNC09999"]}
	la("mục không còn thì bỏ", btm.chuan_menu(m3, ma_hop_le, tp_hop_le)["mon"], {})
	thay = btm.khac_nhau(btm.chuan_menu(_menu(), ma_hop_le, tp_hop_le), c, {"NUTR00090": "Kombucha Cherry", "TPNC00005": "Thêm Cà Phê Phin"})
	dung("Xem và xuất bản ghi thêm riêng: " + "; ".join(thay), "Kombucha Cherry: thêm riêng tuỳ chọn Nhiệt độ" in thay
		and "Kombucha Cherry: thêm riêng topping Thêm Cà Phê Phin" in thay)
