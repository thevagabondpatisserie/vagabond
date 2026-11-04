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
import re

from vagabond import thanh_toan_web_thuan as ttt


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


# Một nguồn cho nút liên hệ trên biên nhận (trang cũ và Vue, Codex #484):
# (khoá liên hệ, khoá nhãn Editor, chữ mặc định).
NUT_LIEN_HE_BIEN_NHAN = (("zalo", "bien_nhan_ed312c8e3", "Nhắn Zalo"),
	("messenger", "bien_nhan_edbd31524", "Nhắn Messenger"))


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


# Một nguồn (Codex #484): câu nghiệp vụ máy chủ trả trong biên nhận -> (khoá nhãn
# Editor, chữ mặc định). Biên nhận trang cũ dùng ở _chu_bien_nhan, biên nhận Vue
# nhận nguyên bảng này qua du_lieu rồi đọc nhãn bằng chu().
GIA_TRI_BIEN_NHAN = {
    'Sales báo phí khi xác nhận':('bien_nhan_phi_cho','Chúng tôi báo phí khi xác nhận'),
    'Chờ Sales báo phí giao':('bien_nhan_tong_cho','Chờ xác nhận phí giao'),
    'Tự đến lấy':('bien_nhan_nhan_tai_quay','Tự đến lấy'),
    'Giao tận nơi':('bien_nhan_giao_tan_noi','Giao tận nơi'),
    'Chuyển khoản (mã VietQR)':('bien_nhan_chuyen_khoan','Chuyển khoản (mã VietQR)'),
    'Thẻ qua cổng OnePay':('bien_nhan_the','Thẻ qua cổng OnePay'),
    'Tự lấy, không tính phí':('bien_nhan_phi_tu_lay','Tự lấy, không tính phí'),
    'Miễn phí giao':('bien_nhan_phi_mien','Miễn phí giao'),
}
# v638: bốn cách thanh toán, chữ và khoá nhãn lấy từ MỘT nguồn với máy chủ.
GIA_TRI_BIEN_NHAN.update({chu: (khoa, chu) for chu, khoa in ttt.NHAN_PT.values()})
TIEN_TO_TU_LAY = ('Tự lấy tại ', 'bien_nhan_tu_lay_tai', 'Tự lấy tại')


def _chu_bien_nhan(chu):
    """Câu nghiệp vụ thành nhãn; số tiền thật vẫn là dữ liệu đọc-only."""
    tien_to, khoa, mac_dinh = TIEN_TO_TU_LAY
    if str(chu or '').startswith(tien_to):
        return _chu(khoa, mac_dinh) + ' ' + _e(chu[len(tien_to):])
    return _chu(*GIA_TRI_BIEN_NHAN[chu]) if chu in GIA_TRI_BIEN_NHAN else _e(chu)


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
	for kenh, khoa, mac_dinh in NUT_LIEN_HE_BIEN_NHAN:
		u = _lien_ket_an_toan(lh.get(kenh))
		if u:
			nut.append('<a class="nut" href="%s" target="_blank" rel="noopener"><span data-vgb-chu="%s">%s</span></a>' % (_e(u), khoa, mac_dinh))
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
		('<div><dt><span data-vgb-chu="bien_nhan_uu_dai">Ưu đãi</span>%s</dt><dd>%s</dd></div>' % (
			(" (%s)" % _e(tt.get("uu_dai"))) if tt.get("uu_dai") else "", _e(tt.get("giam")))) if tt.get("giam") else "",
		'<div><dt><span data-vgb-chu="bien_nhan_06a446f5c">Phí giao</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("phi_giao")),
		'<div class="tong"><dt><span data-vgb-chu="bien_nhan_de995d836">Tổng</span></dt><dd>%s</dd></div>' % _chu_bien_nhan(tt.get("tong")),
		'</dl>',
		khoi_thanh_toan_html(tt.get("tt")),
		('<p class="bn-luu-y">%s</p>' % _chu("bien_nhan_tt_ho_tro", "Cần hỗ trợ thanh toán? Quý khách nhắn hoặc gọi chúng tôi:")) if nut else "",
		'<div class="bn-nut">%s<a class="nut chinh" href="/banh"><span data-vgb-chu="bien_nhan_3f197d985">Đặt thêm bánh</span></a></div>' % "".join(nut),
		'</div></main>',
	])


RE_ANH_QR = re.compile(r"^data:image/svg\+xml;base64,[A-Za-z0-9+/=]+$")


def khoi_thanh_toan_html(k):
	"""v638: khối thanh toán của biên nhận trang cũ, dựng từ CÙNG dữ liệu máy chủ
	gửi biên nhận Vue (thanh_toan_web.khoi_thanh_toan). Chuyển khoản: mã VietQR,
	tài khoản, nội dung; thẻ: nút sang trang thẻ của tiệm (/tra-the); tiền mặt:
	một câu. Trang cũ không tự hỏi lại trạng thái: khách tải lại trang để xem."""
	k = k or {}
	tt = k.get("trang_thai")
	if not tt or tt == "huy":
		return ""
	ra = ['<section class="bn-tt">', '<h2>%s</h2>' % _chu("bien_nhan_tt_tieu_de", "Thanh toán")]
	if tt == "tien_mat":
		ra.append('<p>%s</p>' % _chu("bien_nhan_tt_tien_mat", "Quý khách thanh toán tiền mặt khi nhận bánh."))
	elif tt == "da_thu":
		ra.append('<p class="bn-tt-ok"><b>%s</b> %s · %s</p>' % (_chu("bien_nhan_tt_da_nhan", "Đã nhận tiền"),
			_e(k.get("da_thu_chu")), _e(k.get("cach_thu"))))
	else:
		if tt == "thieu":
			ra.append('<p class="bn-tt-thieu">%s %s</p>' % (_chu("bien_nhan_tt_thieu", "Đã nhận một phần, còn thiếu"), _e(k.get("con_chu"))))
		the = k.get("the") or {}
		ck = k.get("ck") or {}
		if the.get("duong") and _lien_ket_an_toan(the.get("duong")):
			ra.append('<p class="bn-tt-so">%s <b>%s</b></p>' % (_chu("bien_nhan_tt_so_the", "Số tiền thanh toán"), _e(k.get("con_chu"))))
			ra.append('<a class="nut chinh" href="%s">%s</a>' % (_e(the["duong"]), _chu("bien_nhan_tt_the_nut", "Thanh toán bằng thẻ")))
			ra.append('<p class="bn-tt-phu">%s</p>' % _chu("bien_nhan_tt_the_mo", "Quý khách được chuyển sang trang bảo mật của OnePay để nhập thẻ và mã OTP."))
		elif ck:
			if k.get("the_tat"):
				ra.append('<p class="bn-tt-phu">%s</p>' % _chu("bien_nhan_tt_the_tat", "Thanh toán thẻ đang tạm ngưng. Quý khách chuyển khoản theo mã dưới đây."))
			ra.append('<p class="bn-tt-so">%s <b>%s</b></p>' % (_chu("bien_nhan_tt_so_ck", "Số tiền chuyển khoản"), _e(k.get("con_chu"))))
			if RE_ANH_QR.match(str(ck.get("anh") or "")):
				ra.append('<img class="bn-tt-qr" src="%s" alt="VietQR" width="220" height="220">' % ck["anh"])
			ra.append('<dl class="bn-dong">')
			for khoa, mac, gia in (("bien_nhan_tt_ngan_hang", "Ngân hàng", ck.get("ngan_hang")),
					("bien_nhan_tt_stk", "Số tài khoản", ck.get("stk")), ("bien_nhan_tt_chu_tk", "Chủ tài khoản", ck.get("ten")),
					("bien_nhan_tt_noi_dung", "Nội dung chuyển khoản", ck.get("noi_dung"))):
				ra.append('<div><dt>%s</dt><dd>%s</dd></div>' % (_chu(khoa, mac), _e(gia)))
			ra.append('</dl>')
			ra.append('<p class="bn-tt-phu">%s</p>' % _chu("bien_nhan_tt_quet_cu", "Quét mã bằng ứng dụng ngân hàng, giữ nguyên nội dung. Hệ thống tự xác nhận khi tiền về; quý khách tải lại trang để xem."))
		if k.get("phi_sau"):
			ra.append('<p class="bn-tt-phu">%s</p>' % _chu("bien_nhan_tt_phi_sau", "Số này là tiền bánh. Phí giao quý khách trả khi nhận bánh."))
	ra.append('</section>')
	return "".join(ra)


def json_trong_script(du_lieu):
	"""JSON nhúng vào thẻ <script> mà không phá được thẻ đó."""
	return (json.dumps(du_lieu, ensure_ascii=False)
		.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
		.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
