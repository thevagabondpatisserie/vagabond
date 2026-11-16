# -*- coding: utf-8 -*-
"""v664 Google Analytics 4 trên các trang web khách (Minh Vũ, 16/11/2026).

Marketing tự dán mã đo lường GA4 (dạng G-XXXXXXXXXX) vào ô "Google Analytics ID"
trong Cài đặt Vagabond, ngay dưới ô Meta Pixel ID. Để trống thì trang không nạp
GA, không gửi gì.

Đường đi:
  - Hook update_website_context (`ngu_canh`) đặt `vgb_ga_head` vào ngữ cảnh mọi
    trang web. Chỉ các trang KHÁCH (đặt bánh, biên nhận, bánh sỉ, thành viên, đặt
    bàn, ứng tuyển, chính sách) chèn `{{ vgb_ga_head }}` trong <head>; màn nhân
    viên (/bep, /kiem-banh...) không chèn nên không bị đo.
  - Thẻ gtag đặt page_location đã GỠ mã biên nhận (/banh/xong/<token> thành
    /banh/xong) và chỉ giữ tham số quảng cáo (utm_*, gclid, fbclid...), để mã
    biên nhận và số điện thoại trên đường dẫn không sang Google. Trang đang mở
    trong khung xem thử của Biên tập web (bien_tap=1) không nạp GA.
  - Sự kiện bắn ở đúng chỗ đang bắn Meta Pixel: xem bánh (view_item), thêm vào
    giỏ (add_to_cart), bắt đầu thanh toán (begin_checkout), gửi đơn (purchase,
    mã giao dịch là mã sự kiện của đơn để không đếm hai lần).

Ô người điền tay là đầu vào không tin được (v608): nhận cả khi dán kèm khoảng
trắng, chữ thường, hay dán nguyên đoạn mã gtag; chỉ lấy đúng mẫu G-XXXX.
"""

import json
import re

O_GA = "google_analytics_id"

TRUONG_MOI = {
	"Vagabond Settings": [
		{"fieldname": O_GA, "label": "Google Analytics ID", "fieldtype": "Data",
			"insert_after": "meta_pixel_id",
			"description": "Mã đo lường GA4 dạng G-XXXXXXXXXX (Google Analytics > Quản trị > Luồng dữ liệu). "
				"Để trống thì trang khách không nạp Google Analytics và không gửi sự kiện nào."},
	],
}

RE_GA = re.compile(r"\bG-[A-Z0-9]{4,20}\b")


def chuan_ga_id(v):
	"""Ô Google Analytics ID người dán tay -> "G-XXXX" hoặc "". THUẦN."""
	m = RE_GA.search(str(v or "").upper())
	return m.group(0) if m else ""


# Đoạn nạp gtag. Mã GA chỉ đi qua json.dumps của chuỗi đã lọc đúng mẫu G-[A-Z0-9],
# nên không chèn được mã lạ vào trang.
MAU_THE = """<script>(function(w,d,id){try{
if(w.parent!==w&&new URLSearchParams(w.location.search).get('bien_tap')==='1')return;
var sach=function(u){try{var x=new URL(u,w.location.href),g=new URLSearchParams();
x.searchParams.forEach(function(v,k){if(/^(utm_[a-z_]+|gclid|gbraid|wbraid|fbclid|ttclid)$/.test(k))g.append(k,v);});
var q=g.toString();return x.origin+x.pathname.replace(/\\/xong\\/[^\\/]+\\/?$/,'/xong')+(q?'?'+q:'');}catch(e){return '';}};
var r=d.referrer||'',cfg={page_location:sach(w.location.href)};
if(r){try{cfg.page_referrer=new URL(r).origin===w.location.origin?sach(r):new URL(r).origin+'/';}catch(e){}}
w.dataLayer=w.dataLayer||[];w.gtag=function(){w.dataLayer.push(arguments);};
w.gtag('js',new Date());w.gtag('config',id,cfg);
var s=d.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(id);
(d.head||d.documentElement).appendChild(s);}catch(e){}})(window,document,%s);</script>"""


def the_ga(ga_id):
	"""Thẻ <script> nạp GA cho <head>, hoặc "" khi chưa khai mã hợp lệ. THUẦN."""
	ma = chuan_ga_id(ga_id)
	if not ma:
		return ""
	return MAU_THE % json.dumps(ma)


def ga_id():
	import frappe

	try:
		return chuan_ga_id(frappe.db.get_single_value("Vagabond Settings", O_GA, cache=True))
	except Exception:
		return ""


def ngu_canh(context=None):
	"""Hook update_website_context: đặt thẻ GA vào ngữ cảnh trang web."""
	if context is None:
		return context
	try:
		from markupsafe import Markup

		context["vgb_ga_head"] = Markup(the_ga(ga_id()))
	except Exception:
		context["vgb_ga_head"] = ""
	return context
