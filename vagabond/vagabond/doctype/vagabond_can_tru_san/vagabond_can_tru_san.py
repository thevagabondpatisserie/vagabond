"""Phiếu đối soát đã duyệt là căn cứ duy nhất để máy tự bù, issue #262."""
import frappe
from frappe.model.document import Document
from vagabond import can_tru_san as ct

class VagabondCanTruSan(Document):
    def validate(self):
        ct.kiem_phieu(self)

    def before_submit(self):
        ct.kiem_quyen_duyet()
        if not self.xac_nhan:
            frappe.throw('Xác nhận đối soát phí đã bị sàn giữ trước khi duyệt.')

    def on_submit(self):
        ct.thu_bu(self.name)

    def on_cancel(self):
        ct.huy(self)

    def before_update_after_submit(self):
        frappe.throw('Phiếu đã duyệt chỉ được hủy/sửa lại. Các số và trạng thái do máy cập nhật.')

    def on_trash(self):
        frappe.throw('Giữ phiếu đối soát để tra cứu. Dùng Hủy thay vì xóa vĩnh viễn.')
