# -*- coding: utf-8 -*-
"""v675 (tester 19/11/2026, giám đốc chốt): đơn web chỉ nhận thanh toán trước và
miễn phí giao chỉ trong bán kính 7 km tính đường thẳng từ điểm xuất hàng.

Các ca chạy hàm THẬT (mien_phi_km, don_web.quyet_phi_giao, giao_hang.phi_giao với
hãng giao giả). Phần trang khách nằm ở hanh_vi/web_vue_banh.mjs và
hanh_vi/thanh_toan_web_638.mjs.
"""
import json
from pathlib import Path
from types import SimpleNamespace as D
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import don_web, mien_phi_km as mk  # noqa: E402

GOC = Path(__file__).resolve().parents[3]


@ca("v675 bán kính miễn phí giao: ô chưa điền là 7 km, điền 0 là không giới hạn (không bị coi là chưa điền), số âm hay chữ lạ về 7")
def _o():
	la("chưa điền", [mk.tu_o(None), mk.tu_o(""), mk.tu_o("  ")], [7.0, 7.0, 7.0])
	la("điền 0 là không giới hạn", [mk.tu_o(0), mk.tu_o("0"), mk.tu_o(0.0)], [0.0, 0.0, 0.0])
	la("điền số", [mk.tu_o("5"), mk.tu_o(9.5)], [5.0, 9.5])
	la("âm, chữ lạ", [mk.tu_o(-3), mk.tu_o("abc")], [7.0, 7.0])
	with patch("vagabond.lib.cfg_o", side_effect=RuntimeError("DB")):
		la("đọc hỏng về 7", mk.doc(), 7.0)


@ca("v675 trong hay ngoài bán kính: đúng mép 7 km vẫn miễn, 7,01 km thì không; không giới hạn hay chưa biết khoảng cách thì coi là trong")
def _trong():
	la("mép", [mk.trong({"km_thang": 7.0}, 7), mk.trong({"km_thang": 7.01}, 7), mk.trong({"km_thang": 0.2}, 7)], [True, False, True])
	la("không giới hạn", [mk.trong({"km_thang": 30}, 0), mk.trong({"km_thang": 30}, None)], [True, True])
	la("chưa biết khoảng cách", [mk.trong({}, 7), mk.trong(None, 7), mk.trong({"km_thang": "x"}, 7)], [True, True, True])
	la("gắn cờ", [mk.gan_co({"ok": 1, "km_thang": 9}, 7)["ngoai_km_mien_phi"], mk.gan_co({"ok": 1, "km_thang": 3}, 7)["ngoai_km_mien_phi"]], [True, False])
	la("đơn tự lấy không có báo phí", mk.gan_co(None, 7), None)


@ca("v675 quyết phí giao: đơn 1,2 triệu trong 7 km miễn phí; cùng đơn ở 9 km thì khách trả đúng phí hãng báo; hãng không báo được phí thì chưa rõ, không hiện 0")
def _quyet():
	bp = {"ok": 1, "total_fee": 42000}
	q = lambda km, **k: don_web.quyet_phi_giao(1200000, 1000000, False, mk.gan_co(dict(bp, km_thang=km, **k), 7))
	la("3 km: miễn phí, The Vagabond chịu phí", (q(3)["trang_thai"], q(3)["phi_khach"], q(3)["tiem_chiu"]), ("mien_phi", 0, 42000))
	la("9 km: khách trả phí", (q(9)["trang_thai"], q(9)["phi_khach"], q(9)["mien_phi"]), ("chinh_xac", 42000, False))
	r = don_web.quyet_phi_giao(1200000, 1000000, False, mk.gan_co({"ok": 0, "ly_do": "loi", "km_thang": 9}, 7))
	la("9 km, hãng lỗi: chưa rõ", (r["trang_thai"], r["phi_khach"]), ("chua_ro", None))
	la("không giới hạn bán kính: 9 km vẫn miễn", don_web.quyet_phi_giao(1200000, 1000000, False, mk.gan_co(dict(bp, km_thang=9), 0))["trang_thai"], "mien_phi")
	la("dưới ngưỡng, trong 7 km: trả phí như cũ", don_web.quyet_phi_giao(900000, 1000000, False, mk.gan_co(dict(bp, km_thang=3), 7))["trang_thai"], "chinh_xac")
	la("báo phí không có cờ (nơi gọi cũ): như trước v675", don_web.quyet_phi_giao(1200000, 1000000, False, dict(bp))["trang_thai"], "mien_phi")


@ca("v675 báo phí giao trả khoảng cách đường thẳng từ điểm xuất hàng gần nhất, kể cả khi hãng giao không báo được phí; cửa tạo đơn gắn cờ trước khi quyết phí")
def _bao_phi():
	from vagabond import giao_hang as gh

	c = D(ban_kinh_giao_km=12, phu_thu=0, ahamove_base="x", ahamove_mobile="x")
	diem = {"lat": 10.80, "lng": 106.70, "dia_chi": "X"}
	lay = [{"ten": "bep", "lat": 10.80, "lng": 106.66}]
	chung = [patch.object(gh, "cfg", lambda: c), patch.object(gh, "key", lambda c, f: "k"), patch.object(gh, "nguon_phi", lambda c: "Ahamove"),
		patch.object(gh, "_cac_diem_lay", lambda c: [dict(x) for x in lay]), patch.object(gh, "cache_get", lambda k: None),
		patch.object(gh, "cache_set", lambda *a: None), patch.object(gh, "_luc_giao_unix", lambda x: 0)]
	for p in chung:
		p.start()
	try:
		with patch.object(gh, "_hoi_ahamove", lambda c, a, b, m: ({"total_fee": 30000, "distance": 5.1}, None)):
			r = gh.phi_giao(lat=diem["lat"], lng=diem["lng"])
		dung("có phí và khoảng cách đường thẳng khoảng 4,4 km", r["ok"] == 1 and 4.0 < r["km_thang"] < 4.8)
		with patch.object(gh, "_hoi_ahamove", lambda c, a, b, m: (None, "ahamove_loi")):
			r = gh.phi_giao(lat=diem["lat"], lng=diem["lng"])
		dung("hãng lỗi vẫn có khoảng cách", r["ok"] == 0 and 4.0 < r["km_thang"] < 4.8)
	finally:
		for p in chung:
			p.stop()
	src = (GOC / "vagabond/don_hang.py").read_text()
	dung("cửa tạo đơn gắn cờ bán kính ngay trước quyết phí", src.index("mien_phi_km.gan_co(bao_phi, mien_phi_km.doc())") < src.index("don_web.quyet_phi_giao(tien_banh - giam"))
	j = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text())
	o = [f for f in j["fields"] if f["fieldname"] == "mien_phi_giao_km"]
	dung("ô cài đặt có nhãn có dấu, kiểu số, mặc định 7", len(o) == 1 and o[0]["fieldtype"] == "Float" and o[0]["default"] == "7" and "bán kính" in o[0]["label"])
	dung("ô nằm ngay sau ô Miễn phí giao từ", j["field_order"].index("mien_phi_giao_km") == j["field_order"].index("mien_phi_giao_tu") + 1)


@ca("v675 trang khách: không còn cách Tiền mặt khi nhận bánh; ca hành vi trình duyệt chạy thật trong node đều đạt")
def _trang():
	import subprocess

	dl = (GOC / "vagabond/public/web_vue/banh/du-lieu.js").read_text()
	dung("PAYS không còn cash", "k: 'cash'" not in dl)
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs")], capture_output=True, text=True, timeout=300)
	dung("web_vue_banh.mjs xanh: " + r.stdout[-600:], r.returncode == 0 and " 0 ca hong" in r.stdout)
