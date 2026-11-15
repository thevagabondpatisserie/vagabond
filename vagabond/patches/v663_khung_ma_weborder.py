"""v663: gieo khung bốn mã ưu đãi đơn giao của quầy (WEBORDER), trạng thái TẮT,
mức giảm 0 (anh Việt 15/11/2026: làm sẵn, Marketing điền sau). Mã đã có thì để
nguyên; chạy lại không đổi gì. Không đụng chứng từ đã ghi sổ.
"""
import frappe


def execute():
	if not frappe.db.table_exists("Vagabond CTKM"):
		return
	from vagabond import don_quay

	don_quay.gieo_khung_ma()
