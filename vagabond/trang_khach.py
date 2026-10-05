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


def _chu(khoa, mac_dinh):
    return '<span data-vgb-chu="%s">%s</span>' % (_e(khoa), _e(mac_dinh))


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
	dong.append('<p>%s %s</p>' % (_chu('ma_so_thue','Mã số thuế'), _e(pn.get("mst"))))
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


def _chu_bien_nhan(chu):
    """Câu nghiệp vụ thành nhãn; số tiền thật vẫn là dữ liệu đọc-only."""
    bang = {
        'Sales báo phí khi xác nhận':('bien_nhan_phi_cho','Chúng tôi báo phí khi xác nhận'),
        'Chờ Sales báo phí giao':('bien_nhan_tong_cho','Chờ xác nhận phí giao'),
        'Tự đến lấy':('bien_nhan_nhan_tai_quay','Tự đến lấy'),
        'Giao tận nơi':('bien_nhan_giao_tan_noi','Giao tận nơi'),
        'Chuyển khoản (mã VietQR)':('bien_nhan_chuyen_khoan','Chuyển khoản (mã VietQR)'),
        'Thẻ qua cổng OnePay':('bien_nhan_the','Thẻ qua cổng OnePay'),
        'Tự lấy, không tính phí':('bien_nhan_phi_tu_lay','Tự lấy, không tính phí'),
        'Miễn phí giao':('bien_nhan_phi_mien','Miễn phí giao'),
    }
    if str(chu or '').startswith('Tự lấy tại '):
        return _chu('bien_nhan_tu_lay_tai','Tự lấy tại') + ' ' + _e(chu[len('Tự lấy tại '):])
    return _chu(*bang[chu]) if chu in bang else _e(chu)


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
		nut.append('<a class="nut" href="%s" target="_blank" rel="noopener"><span data-vgb-chu="bien_nhan_ed312c8e3">Nhắn Zalo</span></a>' % _e(zalo))
	mess = _lien_ket_an_toan(lh.get("messenger"))
	if mess:
		nut.append('<a class="nut" href="%s" target="_blank" rel="noopener"><span data-vgb-chu="bien_nhan_edbd31524">Nhắn Messenger</span></a>' % _e(mess))
	if lh.get("dien_thoai_so"):
		nut.append('<a class="nut phu" href="tel:%s">Gọi %s</a>' % (_e(lh["dien_thoai_so"]), _e(lh.get("dien_thoai"))))
	lop = "bn-trang-thai cho" if tt.get("dang_xac_nhan") else ("bn-trang-thai huy" if tt.get("da_huy") else "bn-trang-thai")
	gio = " · ".join(x for x in (tt.get("ngay_nhan"), tt.get("khung_gio")) if x)
	return "".join([
		'<main class="bn"><div class="bn-in">',
		'<p class="bn-nhan"><span data-vgb-chu="bien_nhan_ee537c03e">ĐÃ TIẾP NHẬN YÊU CẦU</span></p>',
		'<h1><span data-vgb-chu="bien_nhan_65781f4fe">Mã yêu cầu </span><b>%s</b></h1>' % _e(tt.get("ma")),
		'<p class="%s">%s</p>' % (lop, (_chu("bien_nhan_tt_cho", "Đang xác nhận") if tt.get("dang_xac_nhan") else (_chu("bien_nhan_tt_huy", "Đã huỷ") if tt.get("da_huy") else _chu("bien_nhan_tt_nhan", "Đã nhận")))),
		'<p class="bn-cau">%s</p>' % (_chu("bien_nhan_cho", 'Chúng tôi đã tiếp nhận yêu cầu và đang kiểm tra. Quý khách không cần đặt lại.') if tt.get("dang_xac_nhan") else (_chu("bien_nhan_huy", 'Đơn này đã được huỷ. Quý khách có thể đặt đơn mới hoặc liên hệ để được hỗ trợ.') if tt.get("da_huy") else _chu("bien_nhan_nhan", 'Chúng tôi đã nhận đơn. Nhân viên sẽ liên hệ xác nhận và hướng dẫn thanh toán.'))),
		'<dl class="bn-dong">',
		('<div><dt><span data-vgb-chu="bien_nhan_bd76ef893">Người đặt</span></dt><dd>%s</dd></div>' % _e(tt.get("ten"))) if tt.get("ten") else "",
		('<div><dt><span data-vgb-chu="bien_nhan_c3baf86a6">Nhận bánh</span></dt><dd>%s</dd></div>' % _e(gio)) if gio else "",
		'<div><dt><span data-vgb-chu="bien_nhan_d5ba29353">Cách nhận</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("cach_nhan")),
		'<div><dt><span data-vgb-chu="bien_nhan_9d5a6614c">Thanh toán</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("thanh_toan")),
		'</dl>',
		'<ul class="bn-mon">%s</ul>' % mon,
		'<dl class="bn-tien">',
		'<div><dt><span data-vgb-chu="bien_nhan_ea3b9f8b1">Tiền bánh</span></dt><dd>%s</dd></div>' % _e(tt.get("tien_banh")),
		'<div><dt><span data-vgb-chu="bien_nhan_06a446f5c">Phí giao</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("phi_giao")),
		'<div class="tong"><dt><span data-vgb-chu="bien_nhan_de995d836">Tổng</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("tong")),
		'</dl>',
		'<p class="bn-luu-y"><span data-vgb-chu="bien_nhan_0ea4a5a10">Chúng tôi chưa thu tiền ở bước này. Chúng tôi sẽ gọi xác nhận rồi gửi hướng dẫn thanh toán.</span></p>',
		'<div class="bn-nut">%s<a class="nut chinh" href="/banh"><span data-vgb-chu="bien_nhan_3f197d985">Đặt thêm bánh</span></a></div>' % "".join(nut),
		'</div></main>',
	])


def json_trong_script(du_lieu):
	"""JSON nhúng vào thẻ <script> mà không phá được thẻ đó."""
	return (json.dumps(du_lieu, ensure_ascii=False)
		.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
		.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
