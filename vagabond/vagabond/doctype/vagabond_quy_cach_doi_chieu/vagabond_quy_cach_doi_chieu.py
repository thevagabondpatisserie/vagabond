"""Xác nhận quy cách đối chiếu có căn cứ kiểm kê, không sửa sổ kho cũ."""
import frappe
from frappe.model.document import Document
from vagabond.quy_cach_doi_chieu import kiem_ban_xac_nhan


class VagabondQuyCachDoiChieu(Document):
	def validate(self):
		kiem_ban_xac_nhan(self)

	def before_cancel(self):
		frappe.throw("Căn cứ quy cách đã xác nhận không được huỷ trực tiếp. Nhờ kế toán đối chiếu các hoá đơn liên quan trước.")

	def on_trash(self):
		frappe.throw("Giữ lại căn cứ quy cách để tra lịch sử, không xoá vĩnh viễn.")
