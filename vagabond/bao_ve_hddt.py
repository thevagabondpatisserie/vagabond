"""#225: Desk không được huỷ SI còn chứng từ bên cơ quan thuế.

Document.run_before_save_methods gọi before_cancel trước db_update/on_cancel.
Đọc cả DB để payload xoá số HĐĐT rồi cancel không vượt cửa chặn. Đường huỷ
mềm dùng db.set_value cũng phải gọi cùng kiểm tra trước khi ghi.
"""


def co_dau_hddt(doc):
	"""Trạng thái lạ cũng cần đối chiếu, không suy nó là chưa phát hành."""
	return any(str(doc.get(o) or "").strip() for o in (
		"custom_hddt_so", "custom_hddt_id", "custom_minvoice_id",
		"custom_hddt_trang_thai", "vgb_hddt_cho_doi_chieu",
	))


def chan_huy(doc, method=None):
	import frappe
	if doc.doctype != "Sales Invoice":
		return
	cu = _doc_dau(doc)
	if co_dau_hddt(doc) or (cu and co_dau_hddt(cu)):
		frappe.throw(
			"Hoá đơn %s còn dấu vết hoá đơn điện tử hoặc đang chờ đối chiếu. "
			"Không huỷ chứng từ gốc tại đây. Kế toán đối chiếu M-Invoice; "
			"sửa bút toán nội bộ bằng chứng từ riêng, giữ nguyên hoá đơn đã phát hành."
			% doc.name
		)


def chan_huy_mem(doc, method=None):
	from frappe.utils import cint
	import frappe
	if doc.doctype != "Sales Invoice":
		return
	if cint(doc.get("vgb_huy")):
		chan_huy(doc)
	# Không cho xoá dấu qua save trước, rồi gọi cancel ở request kế tiếp.
	cu = _doc_dau(doc)
	if cu and co_dau_hddt(cu) and not co_dau_hddt(doc):
		frappe.throw("Không xoá toàn bộ dấu hoá đơn điện tử để huỷ phiếu. Kế toán đối chiếu M-Invoice trước.")


def _doc_dau(doc):
	import frappe
	return frappe.db.get_value("Sales Invoice", doc.name, [
		"custom_hddt_so", "custom_hddt_id", "custom_minvoice_id",
		"custom_hddt_trang_thai", "vgb_hddt_cho_doi_chieu",
	], as_dict=True, for_update=True) if doc.name else None
