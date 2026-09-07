"""#227: thêm dấu chống gửi lặp rồi vá hai script đã review, không sửa SI cũ."""


def execute():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from vagabond.minvoice_an_toan import TRUONG_MOI
	from vagabond.minvoice_kich_ban import dong_bo

	create_custom_fields(TRUONG_MOI, update=True)
	from vagabond.hang_tang_so_cai import TRUONG_MOI as TRUONG_TANG
	create_custom_fields(TRUONG_TANG, update=True)
	dong_bo()
