"""Dựng HTML cho các trang khách ngoài trang chọn bánh (#367).

Ba trang mới cần chung một chân trang pháp nhân: trang biên nhận
/banh/xong/<token> và ba trang chính sách. Bộ kiểm của Meta đòi thấy tên
công ty, mã số thuế, địa chỉ và đường dẫn chính sách trên trang đích.

Vì sao dựng HTML ở Python chứ không viết thẳng trong tệp Jinja: Jinja của
Frappe KHÔNG tự thoát ký tự (SandboxedEnvironment, autoescape tắt). Quên một
chữ `| e` là tên khách thành mã chạy trên trang. Dựng ở đây thì mọi chuỗi đều
đi qua `_e`, và bộ kiểm tầng khung chạy được không cần site.

Hàm THUẦN, không chạm Frappe.
"""

import html
import json


def _e(s):
	return html.escape(str(s if s is not None else ""), quote=True)


def _lien_ket_an_toan(u):
	"""Chỉ nhận https:, tel:, mailto: hoặc đường dẫn trong site."""
	u = str(u or "").strip()
	if not u or any(ord(c) < 33 for c in u):
		return ""
	if u.startswith("/") and not u.startswith("//"):
		return u
	thap = u.lower()
	if thap.startswith("https://") or thap.startswith("tel:") or thap.startswith("mailto:"):
		return u
	return ""


def chan_trang_html(phap_nhan, lien_he, chinh_sach):
	"""Chân trang pháp nhân dùng chung. `chinh_sach` là danh sách trang ĐANG HIỆN."""
	pn = phap_nhan or {}
	lh = lien_he or {}
	dong = ['<footer class="ct-web"><div class="ct-in">']
	dong.append('<p class="ct-ten">%s</p>' % _e(pn.get("ten")))
	dong.append('<p>Mã số thuế %s</p>' % _e(pn.get("mst")))
	for d in pn.get("dia_chi") or []:
		dong.append('<p>%s: %s</p>' % (_e(d.get("ten")), _e(d.get("dia_chi"))))
	lk = []
	if lh.get("dien_thoai"):
		lk.append('<a href="tel:%s">%s</a>' % (_e(lh.get("dien_thoai_so") or ""), _e(lh["dien_thoai"])))
	if lh.get("email"):
		lk.append('<a href="mailto:%s">%s</a>' % (_e(lh["email"]), _e(lh["email"])))
	for ten, nhan in (("zalo", "Zalo"), ("messenger", "Messenger"), ("facebook", "Facebook"),
			("instagram", "Instagram"), ("tiktok", "TikTok")):
		u = _lien_ket_an_toan(lh.get(ten))
		if u:
			lk.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (_e(u), nhan))
	if lk:
		dong.append('<p class="ct-lien-he">%s</p>' % " · ".join(lk))
	cs = [c for c in (chinh_sach or []) if _lien_ket_an_toan(c.get("duong"))]
	if cs:
		dong.append('<nav class="ct-chinh-sach" aria-label="Chính sách">%s</nav>' % "".join(
			'<a href="%s">%s</a>' % (_e(c["duong"]), _e(c.get("ten"))) for c in cs))
	dong.append("</div></footer>")
	return "".join(dong)


def bien_nhan_html(tt, lien_he):
	"""Thân trang biên nhận từ `don_web.tom_tat_bien_nhan`. Không có số điện
	thoại, địa chỉ hay email của khách: chỉ những gì trong tóm tắt."""
	tt = tt or {}
	lh = lien_he or {}
	mon = "".join(
		'<li><span>%s</span><b>x%s</b>%s</li>' % (
			_e(m.get("ten")), _e(m.get("sl")),
			('<span class="tien">%s</span>' % _e(m["thanh_tien"])) if m.get("thanh_tien") else "")
		for m in tt.get("mon") or [])
	nut = []
	zalo = _lien_ket_an_toan(lh.get("zalo"))
	if zalo:
		nut.append('<a class="nut" href="%s" target="_blank" rel="noopener">Nhắn Zalo</a>' % _e(zalo))
	mess = _lien_ket_an_toan(lh.get("messenger"))
	if mess:
		nut.append('<a class="nut" href="%s" target="_blank" rel="noopener">Nhắn Messenger</a>' % _e(mess))
	if lh.get("dien_thoai_so"):
		nut.append('<a class="nut phu" href="tel:%s">Gọi %s</a>' % (_e(lh["dien_thoai_so"]), _e(lh.get("dien_thoai"))))
	lop = "bn-trang-thai cho" if tt.get("dang_xac_nhan") else ("bn-trang-thai huy" if tt.get("da_huy") else "bn-trang-thai")
	gio = " · ".join(x for x in (tt.get("ngay_nhan"), tt.get("khung_gio")) if x)
	return "".join([
		'<main class="bn"><div class="bn-in">',
		'<p class="bn-nhan">ĐẶT HÀNG THÀNH CÔNG</p>',
		'<h1>Mã yêu cầu <b>%s</b></h1>' % _e(tt.get("ma")),
		'<p class="%s">%s</p>' % (lop, _e(tt.get("trang_thai"))),
		'<p class="bn-cau">%s</p>' % _e(tt.get("cau")),
		'<dl class="bn-dong">',
		('<div><dt>Người đặt</dt><dd>%s</dd></div>' % _e(tt.get("ten"))) if tt.get("ten") else "",
		('<div><dt>Nhận bánh</dt><dd>%s</dd></div>' % _e(gio)) if gio else "",
		'<div><dt>Cách nhận</dt><dd>%s</dd></div>' % _e(tt.get("cach_nhan")),
		'<div><dt>Thanh toán</dt><dd>%s</dd></div>' % _e(tt.get("thanh_toan")),
		'</dl>',
		'<ul class="bn-mon">%s</ul>' % mon,
		'<dl class="bn-tien">',
		'<div><dt>Tiền bánh</dt><dd>%s</dd></div>' % _e(tt.get("tien_banh")),
		'<div><dt>Phí giao</dt><dd>%s</dd></div>' % _e(tt.get("phi_giao")),
		'<div class="tong"><dt>Tổng</dt><dd>%s</dd></div>' % _e(tt.get("tong")),
		'</dl>',
		'<p class="bn-luu-y">Tiệm chưa thu tiền ở bước này. Sales gọi xác nhận rồi mới gửi mã thanh toán.</p>',
		'<div class="bn-nut">%s<a class="nut chinh" href="/banh">Đặt thêm bánh</a></div>' % "".join(nut),
		'</div></main>',
	])


def json_trong_script(du_lieu):
	"""JSON nhúng vào thẻ <script> mà không phá được thẻ đó."""
	return (json.dumps(du_lieu, ensure_ascii=False)
		.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
		.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
