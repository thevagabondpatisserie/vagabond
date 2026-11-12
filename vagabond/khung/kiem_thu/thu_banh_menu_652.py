"""v652 (anh Việt 12/11/2026): ảnh và mô tả bánh trên menu tại quầy, tại bàn.

Minh Vũ đã sửa ảnh, mô tả đồ uống ở Biên tập menu nhưng bánh thì không được vì
bánh lấy ảnh, mô tả từ danh mục món mà bạn ấy không được vào. Nhóm Bánh trên tủ
nay có nút Món (màn app: hanh_vi/bien_tap_menu_640.js ca v652): sửa riêng ảnh,
mô tả của bánh từng bày ở tủ điểm đó, lưu vào bản nháp, khách thấy sau Xuất bản.
Ở máy chủ: bánh chỉ giữ ảnh và mô tả (không nhóm nước, không tuỳ chọn, topping),
bánh lạ bị bỏ, menu tại quầy dùng bản riêng trước danh mục.
"""
import json
import sys
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu import thu_bien_tap_menu_640 as t640

_fr = sys.modules["frappe"]
from vagabond import diem_ban, kiem_kho  # noqa: E402
from vagabond import bien_tap_menu as btm  # noqa: E402
from vagabond import goi_mon_ban as g  # noqa: E402

MA = {x["ma"] for x in t640.UONG}
TP = {x["ma"] for x in t640.TOP}
BANH = [{"ma": "BKMN00011", "ten": "Mille-feuille Vanilla", "anh": "/files/mille.jpg", "mo_ta": "Bánh ngàn lớp", "gia": 95000},
	{"ma": "BKMN00020", "ten": "Tarte Chanh Dây", "anh": "", "mo_ta": "", "gia": 85000}]
MA_BANH = {b["ma"] for b in BANH}


@ca("v652 bánh: bản nháp giữ ảnh và mô tả riêng của bánh từng bày ở tủ; bỏ tuỳ chọn, topping gửi kèm; bánh lạ bị bỏ; bánh không chen vào nhóm nước")
def _chuan():
	m = t640._menu()
	m["mon"] = {"BKMN00020": {"anh": "/files/menu-bkmn00020.jpg", "mo_ta": "Tart chanh dây", "tat_tc": ["Đá"], "bat_tp": ["TPNC00001"]},
		"BKMN00099": {"mo_ta": "bánh lạ"}, "BKMN00011": {"anh": "/private/files/x.jpg"}}
	m["nhom"][1]["mon"] = list(m["nhom"][1]["mon"]) + ["BKMN00011"]
	ra = btm.chuan_menu(json.loads(json.dumps(m)), MA, TP, MA_BANH)
	la("chỉ giữ ảnh và mô tả của bánh có thật", ra["mon"], {"BKMN00020": {"mo_ta": "Tart chanh dây", "anh": "/files/menu-bkmn00020.jpg"}})
	dung("bánh không vào nhóm nước", all("BKMN00011" not in (x.get("mon") or []) for x in ra["nhom"]))
	la("không truyền danh sách bánh: bỏ hết bánh như cũ", btm.chuan_menu(json.loads(json.dumps(m)), MA, TP)["mon"], {})


@ca("v652 bánh: rieng_banh và kiem_kho.rieng_banh_menu thuần: có bản riêng thì dùng, trống thì danh mục, không menu thì giữ nguyên")
def _thuan():
	menu = {"mon": {"BKMN00020": {"anh": "/files/a.jpg"}, "BKMN00011": {"mo_ta": "Riêng"}}}
	la("ảnh riêng, mô tả danh mục", btm.rieng_banh(menu, "BKMN00020", "/files/goc.jpg", "Gốc"), ("/files/a.jpg", "Gốc"))
	la("mô tả riêng, ảnh danh mục", btm.rieng_banh(menu, "BKMN00011", "/files/goc.jpg", "Gốc"), ("/files/goc.jpg", "Riêng"))
	la("không sửa riêng", btm.rieng_banh(menu, "X", "", ""), ("", ""))
	la("feed: không có menu", kiem_kho.rieng_banh_menu(None, {"ma": "BKMN00020", "mo_ta": "Gốc"}), ("", "Gốc"))
	la("feed: có menu", kiem_kho.rieng_banh_menu(menu, {"ma": "BKMN00020", "mo_ta": "Gốc"}), ("/files/a.jpg", "Gốc"))


@ca("v652 bánh: mở màn có danh sách bánh; lưu nháp ảnh và mô tả bánh thì khách chưa thấy, thay đổi ghi tên bánh; Xuất bản xong menu tại quầy hiện ảnh, mô tả riêng; bánh khác giữ danh mục")
def _vong_doi():
	kho = t640.Kho()
	with t640._Moi(t640._he(kho) + [patch.object(btm, "banh_cua_diem", side_effect=lambda d, n=None: BANH if d == "TCV" else [])]):
		r = btm.mo(diem="TCV")
		la("màn có bánh", [b["ma"] for b in r["banh"]], ["BKMN00011", "BKMN00020"])
		nhap = r["nhap"]
		nhap.setdefault("mon", {})["BKMN00020"] = {"anh": "/files/menu-bkmn00020.jpg", "mo_ta": "Tart chanh dây chua nhẹ"}
		k = btm.luu_nhap(diem="TCV", noi_dung=json.dumps(nhap))
		la("thay đổi ghi tên bánh", sorted(k["thay_doi"]), ["Tarte Chanh Dây: sửa mô tả trên web", "Tarte Chanh Dây: đổi ảnh trên web"])
		la("khách chưa thấy", btm.menu_dang_chay("TCV"), (None, 0))
		btm.xuat_ban(diem="TCV")
		m, _p = btm.menu_dang_chay("TCV")
		la("đổi điểm không có bánh này: bản nháp điểm đó không nhận", btm.chuan_menu(m, MA, TP, set())["mon"], {})
	la("menu đang chạy giữ bánh", m["mon"]["BKMN00020"], {"mo_ta": "Tart chanh dây chua nhẹ", "anh": "/files/menu-bkmn00020.jpg"})
	diem = [dict(ma="TCV", ten="The Vagabond District 1", ten_ngan="District 1", dia_chi="9 TCV", quay="TCV")]
	tren_tu = [dict(ma="BKMN00011", ten="Mille-feuille Vanilla", con=3, gia_chung=95000, nhom="Bánh", anh_goc="/files/mille.jpg", mo_ta="Bánh ngàn lớp"),
		dict(ma="BKMN00020", ten="Tarte Chanh Dây", con=2, gia_chung=85000, nhom="Bánh", anh_goc="", mo_ta="")]
	lib = sys.modules.get("vagabond.lib")
	with patch.object(kiem_kho, "_diem_co_quay", return_value=diem), patch.object(kiem_kho, "banh_tren_quay", return_value=tren_tu), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: t640.UONG), patch.object(g, "topping_cua_diem", side_effect=lambda ma: t640.TOP), \
			patch.object(btm, "menu_dang_chay", return_value=(m, 1)), patch.object(diem_ban, "gia_rieng", return_value={}), \
			patch.object(lib, "cfg", return_value=_fr._dict(pancake_shop_id="")), patch.object(lib, "key", return_value=""):
		q = kiem_kho.con_tren_quay_web()["quay"][0]
	ban = {x["ma"]: (x["anh"], x["mo_ta"]) for x in q["mon"]}
	la("bánh sửa riêng", ban["BKMN00020"], ("/files/menu-bkmn00020.jpg", "Tart chanh dây chua nhẹ"))
	la("bánh khác giữ danh mục", ban["BKMN00011"], ("/files/mille.jpg", "Bánh ngàn lớp"))


@ca("v652 bánh: banh_cua_diem lấy mã từ Kiểm kho điểm 60 ngày của đúng điểm, bỏ bánh ngừng bán, xếp theo tên, mô tả gọn, giá theo điểm")
def _banh_cua_diem():
	cau = []

	def sql(c, ts=None, **k):
		cau.append((c, ts))
		return [["BKMN00020"], ["BKMN00011"], [None]]

	def get_all(dt, filters=None, fields=None, **k):
		la("hỏi Item đúng mã", (dt, sorted(filters["item_code"][1]), filters["disabled"]), ("Item", ["BKMN00011", "BKMN00020"], 0))
		return [_fr._dict(item_code="BKMN00020", item_name="Tarte Chanh Dây", image="", standard_rate=85000, description="<p>Chua <b>nhẹ</b></p>"),
			_fr._dict(item_code="BKMN00011", item_name="Mille-feuille Vanilla", image="/files/m.jpg", standard_rate=95000, description="")]
	with patch.object(_fr.db, "sql", side_effect=sql), patch.object(_fr, "get_all", side_effect=get_all), \
			patch.object(diem_ban, "gia_rieng", side_effect=lambda d: {"BKMN00011": 99000} if d == "TCV" else {}):
		ra = btm.banh_cua_diem("TCV", "2026-11-12")
	la("giá theo bảng giá điểm bán, không có thì giá chung", [x["gia"] for x in ra], [99000, 85000])
	la("xếp theo tên", [x["ma"] for x in ra], ["BKMN00011", "BKMN00020"])
	la("mô tả gọn", ra[1]["mo_ta"], "Chua nhẹ")
	c, ts = cau[0]
	dung("đọc bảng Kiểm kho điểm", "tabVagabond Kiem Kho Dong" in c and "tabVagabond Kiem Kho Diem" in c and "p.diem" in c)
	la("đúng điểm và 60 ngày", (ts[1], str(ts[2]), str(ts[3])), ("TCV", "2026-09-13", "2026-11-12"))
	with patch.object(_fr.db, "sql", return_value=[]):
		la("chưa từng bày: rỗng, không hỏi Item", btm.banh_cua_diem("NVHTN", "2026-11-12"), [])
