"""v645 (Minh Vũ báo, anh Việt 08/11/2026): ảnh riêng cho web của từng món trong
Biên tập menu. Màn app cắt vuông 1:1, nén dưới 500 KB rồi tải lên tệp công khai
(trình duyệt thật: cong_cu/kiem_anh_menu_dom.cjs; đường bấm: hanh_vi/
bien_tap_menu_640.js). Ở máy chủ: chỉ nhận đúng đường dẫn tệp công khai, ảnh đi
theo bản nháp và Xuất bản, trang gọi món tại bàn dùng ảnh riêng trước ảnh danh
mục, ảnh ở màn Tính tiền không đổi.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu import thu_bien_tap_menu_640 as t640

_fr = sys.modules["frappe"]
from vagabond import anh_web, diem_ban, kiem_kho  # noqa: E402
from vagabond import bien_tap_menu as btm  # noqa: E402
from vagabond import goi_mon_ban as g  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
MA = {x["ma"] for x in t640.UONG}
TP = {x["ma"] for x in t640.TOP}


def _voi_anh(anh):
	m = t640._menu()
	m["mon"] = {"NUTR00090": {"anh": anh}}
	return btm.chuan_menu(json.loads(json.dumps(m)), MA, TP)


@ca("v645 ảnh riêng cho web: chỉ nhận đường dẫn tệp công khai /files/ dạng ảnh; /private, link ngoài, ../, đuôi lạ, kiểu lạ đều bỏ lặng")
def _chuan():
	for anh in ("/files/menu-nutr00090.jpg", "/files/menu-nutr00090a1b2c3.JPEG", "/files/menu-x.png", "/files/menu-x.webp", "  /files/menu-x.jpg  "):
		la(repr(anh), _voi_anh(anh)["mon"].get("NUTR00090"), {"anh": anh.strip()})
	for anh in ("/private/files/menu.jpg", "https://evil.example/x.jpg", "//evil.example/x.jpg", "/files/../x.jpg", "/files/x.gif",
			"javascript:alert(1)", "/files/a b.jpg", "/files/x.jpg?v=1", "/files/", 12, None, ["/files/x.jpg"], {"u": 1}):
		la(repr(anh), _voi_anh(anh)["mon"].get("NUTR00090"), None)
	m = t640._menu()
	m["mon"] = {"NUTR00090": {"anh": "/files/a.jpg", "mo_ta": "Cherry"}, "MA-LA": {"anh": "/files/b.jpg"}}
	la("giữ cùng mô tả, bỏ món lạ", btm.chuan_menu(m, MA, TP)["mon"], {"NUTR00090": {"mo_ta": "Cherry", "anh": "/files/a.jpg"}})


@ca("v645 áp menu: món có ảnh riêng thì đồ uống mang ảnh riêng, món khác giữ ảnh danh mục; thay đổi đọc được cho màn Xem và xuất bản")
def _ap():
	m = _voi_anh("/files/menu-nutr00090.jpg")
	_nhom, uong = btm.ap_menu(m, t640.UONG)
	anh = {x["ma"]: x["anh"] for x in uong}
	la("ảnh", [anh["NUTR00090"], anh["NUCF00003"]], ["/files/menu-nutr00090.jpg", ""])
	la("không đổi danh mục gốc", t640.UONG[0]["anh"], "/files/kom.jpg")
	ten = {x["ma"]: x["ten"] for x in t640.UONG}
	goc = t640._menu()
	la("đổi ảnh", btm.khac_nhau(goc, m, ten), ["Kombucha Cherry: đổi ảnh trên web"])
	la("về ảnh danh mục", btm.khac_nhau(m, goc, ten), ["Kombucha Cherry: về ảnh trong danh mục món"])
	la("đổi sang ảnh khác", btm.khac_nhau(m, _voi_anh("/files/menu-khac.jpg"), ten), ["Kombucha Cherry: đổi ảnh trên web"])


@ca("v645 nháp rồi xuất bản: ảnh riêng lưu nháp thì khách chưa thấy; Xuất bản xong trang gọi món tại bàn hiện ảnh riêng; món không ảnh vẫn ra ảnh nền")
def _vong_doi():
	kho = t640.Kho()
	with t640._Moi(t640._he(kho)):
		r = btm.mo(diem="TCV")
		la("món mang ảnh danh mục cho màn", {x["ma"]: x["anh"] for x in r["mon"]}["NUTR00090"], "/files/kom.jpg")
		nhap = r["nhap"]
		nhap.setdefault("mon", {})["NUTR00090"] = {"anh": "/files/menu-nutr00090.jpg"}
		k = btm.luu_nhap(diem="TCV", noi_dung=json.dumps(nhap))
		la("thay đổi", k["thay_doi"], ["Kombucha Cherry: đổi ảnh trên web"])
		la("khách chưa thấy", btm.menu_dang_chay("TCV"), (None, 0))
		btm.xuat_ban(diem="TCV")
		m, _p = btm.menu_dang_chay("TCV")
	la("menu đang chạy có ảnh", m["mon"]["NUTR00090"], {"anh": "/files/menu-nutr00090.jpg"})
	diem = [dict(ma="TCV", ten="The Vagabond District 1", ten_ngan="District 1", dia_chi="9 TCV", quay="TCV")]
	lib = sys.modules.get("vagabond.lib")
	with patch.object(kiem_kho, "_diem_co_quay", return_value=diem), patch.object(kiem_kho, "banh_tren_quay", return_value=[]), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: t640.UONG), patch.object(g, "topping_cua_diem", side_effect=lambda ma: t640.TOP), \
			patch.object(btm, "menu_dang_chay", return_value=(m, 1)), patch.object(diem_ban, "gia_rieng", return_value={}), \
			patch.object(lib, "cfg", return_value=_fr._dict(pancake_shop_id="")), patch.object(lib, "key", return_value=""):
		q = kiem_kho.con_tren_quay_web()["quay"][0]
	anh = {x["ma"]: x["anh"] for x in q["do_uong"]}
	la("trang bàn: ảnh riêng, món không ảnh ra ảnh nền", [anh["NUTR00090"], anh["NUCF00003"]], ["/files/menu-nutr00090.jpg", anh_web.ANH_NEN])


@ca("v645 trang gọi món tại bàn: ảnh món khung vuông 1:1, không còn khung 16:9 cắt đầu cắt đuôi; ca trình duyệt thật của ảnh menu nằm trong CI ảnh web")
def _khung():
	css = (GOC / "vagabond/public/web_vue/banh/banh.css").read_text()
	gb = [d for d in css.split("\n") if d.startswith(".gb-anh{")]
	la("lớp cuối thắng", "aspect-ratio:1/1" in gb[-1], True)
	dung("không còn 16:9", not any("16/9" in d for d in gb[1:]))
	wf = (GOC / ".github/workflows/anh-web.yml").read_text()
	dung("CI chạy ca ảnh menu", "node cong_cu/kiem_anh_menu_dom.cjs" in wf and "vagabond/public/js/bep/68-bien-tap-menu.js" in wf)
