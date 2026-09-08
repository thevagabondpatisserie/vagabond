"""#243: thêm dấu luồng kho cho SI mới, không đánh dấu hoặc xuất kho SI cũ."""


def execute():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from vagabond.hang_tang_kho import TRUONG
    create_custom_fields(TRUONG, update=True)
