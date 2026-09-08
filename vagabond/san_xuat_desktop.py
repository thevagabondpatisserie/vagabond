"""Kho khai một lần trên món, và thông tin kiểm tra LSX cho Khải (#206).

Kho trên món là gợi ý cho lệnh mới. Kho đã chọn trên lệnh và trên dòng
không được suy lại theo nhóm món khi lưu. Lệnh cũ chỉ được đọc để cảnh báo,
không tự sửa vì có thể đã chuyển hoặc tiêu hao nguyên liệu.
"""

# phần thuần
TRUONG_KHO = "custom_kho_nguyen_lieu_sx"
TRUONG_MOI = {"Item": [{
	"fieldname": TRUONG_KHO,
	"label": "Kho nguyên liệu mặc định khi sản xuất",
	"fieldtype": "Link", "options": "Warehouse",
	"insert_after": "default_bom", "in_standard_filter": 1,
	"description": "Kho lấy nguyên liệu khi sản xuất MÓN NÀY. Khai một lần cho lệnh mới; "
		"vẫn đổi kho riêng trên lệnh. Không thay đổi lệnh cũ hoặc kho nhập thành phẩm.",
}]}


def thong_tin_lenh(doc):
	"""Tóm tắt từ chứng từ đang đọc, không suy 'đủ hàng' từ trạng thái LSX."""
	nguon = doc.get("source_warehouse") or ""
	dong = []
	for i, d in enumerate(doc.get("required_items") or [], 1):
		kho = d.get("source_warehouse") or nguon
		dong.append({"idx": d.get("idx") or i, "ma": d.get("item_code"),
			"ten": d.get("item_name") or d.get("item_code"), "kho": kho,
			"khac_kho": bool(nguon and kho and kho != nguon)})
	so = float(doc.get("qty") or 0)
	da = float(doc.get("produced_qty") or 0)
	hao = float(doc.get("process_loss_qty") or 0)
	return {"ten": doc.get("name"), "kho_nguon": nguon,
		"kho_dich": doc.get("fg_warehouse") or "", "so_lenh": so,
		"da_lam": da, "hao_hut": hao, "con_lai": max(0, so - da - hao),
		"don_vi": doc.get("stock_uom") or "", "dong": dong,
		"so_khac_kho": sum(1 for d in dong if d["khac_kho"]),
		"qua_wip": not bool(doc.get("skip_transfer")) or bool(doc.get("from_wip_warehouse")),
		"kho_wip": doc.get("wip_warehouse") or ""}


# phần cần Frappe
import frappe
from frappe.utils import cint


def kiem_kho(kho, cong_ty=None):
	"""Frappe kiểm Link trước before_validate, nên kho tự điền phải kiểm lại.

	ERPNext 16.28.0 WorkOrder.validate_warehouse_belongs_to_company và
	StockController.validate_warehouse kiểm công ty; không đổi quy tắc lõi.
	"""
	if not kho:
		return
	ho = frappe.get_doc("Warehouse", kho)
	ho.check_permission("read")
	if cint(ho.get("is_group")) or cint(ho.get("disabled")):
		frappe.throw("Kho nguyên liệu phải là kho đang hoạt động, không phải nhóm kho.")
	if cong_ty and ho.company != cong_ty:
		frappe.throw("Kho nguyên liệu không thuộc công ty của lệnh. Chọn lại kho trên lệnh.")


def kho_tren_mon(ma):
	# Trước migrate không được hỏi cột chưa tồn tại.
	if not ma or not frappe.get_meta("Item").has_field(TRUONG_KHO):
		return ""
	return frappe.db.get_value("Item", ma, TRUONG_KHO) or ""


def kiem_mon(doc, method=None):
	kho = doc.get(TRUONG_KHO)
	if kho:
		kiem_kho(kho)


def dien_kho_mon(doc):
	# Không tự áp cấu hình mới lên bất kỳ lệnh đã lưu nào.
	if not doc.is_new() or doc.get("source_warehouse"):
		return
	kho = kho_tren_mon(doc.get("production_item"))
	if kho:
		kiem_kho(kho, doc.get("company"))
		doc.source_warehouse = kho


@frappe.whitelist()
def chi_tiet(ten):
	"""Chỉ đọc lệnh người dùng có quyền; không lộ tồn/kho của lệnh khác."""
	doc = frappe.get_doc("Work Order", ten)
	doc.check_permission("read")
	return thong_tin_lenh(doc)
