"""Phát trang đặt bánh bản Vue ngay tại /banh khi công tắc Cài đặt đang bật.

Anh Việt chốt 17/10/2026: chuyển web sang bản Vue. Không đổi đường dẫn khách
đang dùng, không xoá Web Page "banh" cũ: tắt công tắc "Dùng trang đặt bánh bản
mới" trong Cài đặt là /banh về trang cũ ngay, không cần deploy.

Cơ chế: hook `page_renderer` của Frappe. Bộ dựng tự khai được hỏi TRƯỚC mọi bộ
dựng sẵn (xem frappe/website/path_resolver.py), nên khi công tắc bật thì nó
nhận đường /banh và dựng tệp www/web_moi/banh.html; tắt thì nó từ chối và
Frappe dựng Web Page "banh" như cũ. v603: biên nhận /banh/xong[/<token>] cũng
đi theo công tắc (dựng www/web_moi/xong.html), để khách đặt ở bản Vue thấy
biên nhận cùng bản; ba trang chính sách giữ trang cũ (xem web_vue.TEP_VUE). Quyết định nằm ở hàm thuần
`web_vue.dung_ban_vue` để kiểm thử không cần site.
"""
import frappe
from frappe.website.page_renderers.template_page import TemplatePage

from vagabond.web_vue import TEP_VUE, tep_ban_vue


def cong_tac_bat():
	try:
		return frappe.db.get_single_value("Vagabond Settings", "web_ban_vue", cache=True)
	except Exception:
		# Đọc lỗi (chưa migrate trường mới, CSDL chập chờn): giữ trang cũ.
		return 0


class TrangBanhVue(TemplatePage):
	# Frappe tạo bộ dựng này cho MỌI request web (trước cả trang tĩnh, tài liệu).
	# Đường khác /banh, /banh/xong thì không quét tệp, không đọc Cài đặt: chỉ giữ vài thuộc
	# tính tối thiểu rồi can_render trả False ngay.
	def __init__(self, path=None, http_status_code=None):
		self.duong_goc = str(path or "").strip("/ ")
		if self.duong_goc not in TEP_VUE:
			self.path = self.duong_goc
			self.http_status_code = http_status_code or 200
			self.headers = None
			return
		super().__init__(TEP_VUE[self.duong_goc], http_status_code)

	def can_render(self):
		if self.duong_goc not in TEP_VUE:
			return False
		if not tep_ban_vue(self.duong_goc, cong_tac_bat(), dict(frappe.form_dict or {})):
			return False
		return super().can_render()
