"""Ghi trực tiếp BOM và dấu vết trong cùng giao dịch, không tự commit."""
import frappe
from html import escape


# Chỉ ghi thay đổi nghiệp vụ; giá vốn là kết quả core tính lại, không phải thao tác sửa.
NHAN = {"is_active": "Đang dùng", "is_default": "Mặc định", "custom_chang": "Chặng sản xuất",
	"is_phantom_bom": "Công thức ảo"}


def _gia_tri(k, v):
	"""Dùng chữ cho ô Check, không coi chuỗi '0' là True."""
	if k in ("is_active", "is_default", "is_phantom_bom"):
		bat = v in (1, True, "1")
		if k == "is_active":
			return "Bật" if bat else "Tắt"
		return "Có" if bat else "Không"
	return "Chưa chọn" if v is None or v == "" else str(v)


def dat_bom(doctype, name, fieldname, value=None, *, nguon, **kwargs):
	assert doctype == "BOM"
	doi = fieldname if isinstance(fieldname, dict) else {fieldname: value}
	cu = frappe.db.get_value("BOM", name, list(doi), as_dict=True) or {}
	kq = frappe.db.set_value("BOM", name, fieldname, value, **kwargs)
	cau = ["%s: %s thành %s" % (NHAN[k], _gia_tri(k, cu.get(k)), _gia_tri(k, v)) for k, v in doi.items()
		if k in NHAN and _gia_tri(k, cu.get(k)) != _gia_tri(k, v)]
	if cau:
		# Không nuốt lỗi: nếu không ghi được dấu vết, request phải rollback.
		frappe.get_doc("BOM", name).add_comment("Comment", escape(
			"%s. Người sửa: %s. %s" % (nguon, frappe.session.user, "; ".join(cau))))
	return kq
