"""v657: phiếu đề xuất công thức đổi trạng thái "Chờ Khải" thành "Chờ Kế toán".

Quy tắc chữ ERP (anh Việt duyệt 14/11/2026, docs/quy-tac-chu-erp.md): chữ trên
app gọi bộ phận, không gọi tên người. Chỉ đổi phiếu đang chờ xử lý, không đụng
chứng từ đã ghi sổ. Chạy lại không đổi gì thêm.
"""
import frappe


def execute():
	from vagabond.de_xuat_cong_thuc import TT_CHO, TT_CHO_CU
	if not frappe.db.table_exists("Vagabond De Xuat Cong Thuc"):
		return
	frappe.db.sql(
		"update `tabVagabond De Xuat Cong Thuc` set trang_thai=%s where trang_thai=%s",
		(TT_CHO, TT_CHO_CU))
