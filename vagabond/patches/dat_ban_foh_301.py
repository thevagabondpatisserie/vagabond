"""#301: khai khu ngồi ban đầu, không ghi đè lựa chọn quản lý đã lưu."""
import frappe


def execute():
    frappe.reload_doc('vagabond', 'doctype', 'vagabond_cau_hinh_dat_ban')
    if not frappe.db.get_single_value('Vagabond Cau Hinh Dat Ban', 'khu_vuc'):
        frappe.db.set_single_value('Vagabond Cau Hinh Dat Ban', 'khu_vuc',
                                   'Bàn ghế cao\nBàn sofa thấp\nPhòng áp mái')
