"""#227 v447: vá lại hai Server Script từ bản gốc snapshot, sau review Codex PR #228.

Chạy được trên cả site chưa vá (bản gốc) lẫn bench đã chạy minvoice_v446:
`dong_bo` đối chiếu sha256 với ba bản đã biết rồi luôn tính bản mới từ
snapshot, không dựa vào mốc "# VGB-227" để bỏ qua.
"""


def execute():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from vagabond.minvoice_an_toan import TRUONG_MOI
	from vagabond.minvoice_kich_ban import dong_bo

	create_custom_fields(TRUONG_MOI, update=True)
	dong_bo()
