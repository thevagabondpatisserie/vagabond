"""Trang đặt bánh bản Vue (chạy thử song song, anh Việt chốt 11/10/2026).

Như các trang khách khác: có mã CSRF cho nhân viên đang đăng nhập (thiếu là
Frappe chặn 400 khi gửi đơn), không cache phiên. Tên tệp bằng gạch dưới vì
Frappe tìm mô đun theo luật gạch dưới (bài học v529).
"""
import frappe
from vagabond.web_vue import seo_banh
from vagabond.ten_mien import cong_tac_mien_chinh, la_duong_spa, mien_cong_khai

no_cache = 1


def get_context(context):
	context.no_cache = 1
	# v605: canonical, og:url theo tên miền chính khi công tắc tên miền chính bật.
	req = getattr(frappe.local, "request", None)
	duong = str(getattr(req, "path", "") or "")
	# v692: canonical là đường sạch của đúng màn (/, /dat-truoc, /tuyen-dung...).
	context.seo = seo_banh(mien_cong_khai(cong_tac_mien_chinh()), duong if la_duong_spa(duong) else "/")
	context.csrf_token = frappe.sessions.get_csrf_token()
	# Phát tại /banh (đã tráo) hay một màn đường sạch (v692) thì là trang công
	# khai, cho máy tìm kiếm đọc; ở đường thử /web_moi/banh thì vẫn noindex.
	context.cong_khai = la_duong_spa(duong)
