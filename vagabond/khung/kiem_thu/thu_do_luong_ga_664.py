# -*- coding: utf-8 -*-
"""v664 Google Analytics 4 trên trang web khách (Minh Vũ 16/11/2026).

Ca chốt:
  - Ô "Google Analytics ID" trong Cài đặt đứng ngay dưới ô Meta Pixel ID.
  - Mã dán tay (chữ thường, khoảng trắng, cả đoạn gtag) ra đúng G-XXXX; sai mẫu
    hay trống thì không có thẻ; không chèn được mã lạ.
  - Mọi trang khách có thẻ trong <head>; màn nhân viên không có.
  - Hook update_website_context khai đúng một lần, có thẻ GA.
  - Chạy thật thẻ gtag, đổi sự kiện, biên nhận (hanh_vi/ga_664.mjs).
"""

import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MOC = '{{ vgb_ga_head or "" }}'
TRANG_KHACH = ("www/web_moi/banh.html", "www/web_moi/xong.html", "www/web_moi/banh-si.html",
	"www/web_moi/chinh-sach.html", "www/thanh-vien.html", "www/dat-ban.html", "www/ung-tuyen.html",
	"www/chinh-sach.html", "www/banh/xong.html")


def _ga():
	from vagabond import do_luong_ga

	return do_luong_ga


def _doc(p):
	with open(os.path.join(GOC, "vagabond", p), encoding="utf-8") as f:
		return f.read()


@ca("v664 GA: ô Google Analytics ID ngay dưới Meta Pixel ID, mã dán tay ra đúng G-XXXX")
def _():
	g = _ga()
	f = g.TRUONG_MOI["Vagabond Settings"]
	la("một ô", [(x["fieldname"], x["label"], x["insert_after"]) for x in f],
		[("google_analytics_id", "Google Analytics ID", "meta_pixel_id")])
	for v, mong in (("G-RMWD2XHNZ8", "G-RMWD2XHNZ8"), ("  g-rmwd2xhnz8\n", "G-RMWD2XHNZ8"),
			("<script async src=\"https://www.googletagmanager.com/gtag/js?id=G-RMWD2XHNZ8\"></script>", "G-RMWD2XHNZ8"),
			("", ""), (None, ""), ("UA-1234-1", ""), ("G-", ""), ("abc", "")):
		la(repr(v), g.chuan_ga_id(v), mong)
	la("trống thì không có thẻ", g.the_ga(""), "")
	t = g.the_ga('G-ABCD1234"</script><script>alert(1)//')
	dung("không chèn được mã lạ", "alert" not in t and '"G-ABCD1234"' in t and t.count("<script>") == 1)


@ca("v664 GA: mọi trang khách có thẻ trong <head>, màn nhân viên không có")
def _():
	for p in TRANG_KHACH:
		s = _doc(p)
		dung("%s có thẻ GA trước </head>" % p, (MOC + "</head>") in s and s.count(MOC) == 1)
	for goc, _d, tep in os.walk(os.path.join(GOC, "vagabond", "trang")):
		for t in tep:
			if t.endswith(".html"):
				dung("màn nhân viên %s không có GA" % t, MOC not in open(os.path.join(goc, t), encoding="utf-8").read())


@ca("v664 GA: hook update_website_context khai một lần, có thẻ GA; hook đặt thẻ vào ngữ cảnh")
def _():
	s = _doc("hooks.py")
	la("khai một lần", len(re.findall(r"^update_website_context\s*=", s, re.M)), 1)
	dung("có hook GA", '"vagabond.do_luong_ga.ngu_canh"' in s)
	from unittest import mock
	g = _ga()
	with mock.patch.object(g, "ga_id", lambda: "G-RMWD2XHNZ8"):
		c = g.ngu_canh({})
	dung("ngữ cảnh có thẻ", "G-RMWD2XHNZ8" in str(c["vgb_ga_head"]))
	with mock.patch.object(g, "ga_id", lambda: ""):
		la("chưa khai thì rỗng", str(g.ngu_canh({})["vgb_ga_head"]), "")
	# Máy CI không có markupsafe (không Frappe): hook vẫn đặt được thẻ (CI #575 đỏ vì nuốt ImportError).
	import sys
	with mock.patch.dict(sys.modules, {"markupsafe": None}), mock.patch.object(g, "ga_id", lambda: "G-RMWD2XHNZ8"):
		dung("không có markupsafe vẫn có thẻ", "G-RMWD2XHNZ8" in str(g.ngu_canh({})["vgb_ga_head"]))


@ca("v664 GA chạy thật: thẻ gtag gỡ mã biên nhận, xem thử không nạp, đổi sự kiện, purchase một lần (hanh_vi/ga_664.mjs)")
def _():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/ga_664.mjs"], cwd=GOC, capture_output=True, text=True, timeout=120)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ 8 ca", bool(m) and int(m.group(1)) >= 8)


@ca("v664 GA Codex #575: sự kiện gửi đơn của biên nhận mang số lượng từng món, gộp dòng cùng mã")
def _():
	from vagabond import don_web

	la("ba bánh cùng mã và hai dòng cùng mã", don_web.mon_su_kien({"mon": [{"ma": "B1", "sl": 3}, {"ma": "B2", "sl": 1}, {"ma": "B1", "sl": 2}, {"ma": "", "sl": 9}]}),
		[{"ma": "B1", "sl": 5}, {"ma": "B2", "sl": 1}])
	la("số lượng hỏng là 1", don_web.mon_su_kien({"mon": [{"ma": "B1", "sl": "x"}]}), [{"ma": "B1", "sl": 1}])
	la("không có món", don_web.mon_su_kien({}), [])
	import inspect
	dung("biên nhận gửi mon_sl", '"mon_sl": mon_su_kien(snap)' in inspect.getsource(don_web.bien_nhan_theo_token))
