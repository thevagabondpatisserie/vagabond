"""#225: chỉ tạo dấu chính sách tính thuế, không cập nhật hoá đơn quá khứ."""


def execute():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from vagabond.thue_vnd import TRUONG
    create_custom_fields(TRUONG, update=True)
