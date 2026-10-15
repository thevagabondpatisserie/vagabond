"""Khóa bộ trước khóa ngầm của Document, chỉ bốn loại phiếu được khai.

Frappe f33ac3f Document._save/check_if_latest khóa phiếu trước validate.
Mixin chạy trước bước đó, không thay quyền, validate, version hay ghi sổ lõi.
"""
from vagabond.bo_sao_ke_db import khoa_phieu


class KhoaBoSaoKe:
    def load_from_db(self):
        if self.flags.get('for_update'):
            khoa_phieu(self.doctype, self.name)
        return super().load_from_db()

    def _save(self, *args, **kwargs):
        if not self.is_new():
            khoa_phieu(self.doctype, self.name)
        return super()._save(*args, **kwargs)


class KhoaBoHoanTien:
    """PE ghi sổ/cancel khóa bộ trước khóa PE và hook cập nhật hồ sơ hoàn."""
    def _khoa_bo_hoan(self):
        import frappe
        ma = self.get('vgb_hoan_tien')
        if self.name and not self.is_new():
            ma = frappe.db.get_value('Payment Entry', self.name, 'vgb_hoan_tien') or ma
        if ma:
            khoa_phieu('Vagabond Hoan Tien', ma)

    def load_from_db(self):
        if self.flags.get('for_update'):
            self._khoa_bo_hoan()
        return super().load_from_db()

    def _save(self, *args, **kwargs):
        self._khoa_bo_hoan()
        return super()._save(*args, **kwargs)


class KhoaBoThu:
    """Khóa chủ bộ từ DB trước khóa PE, cả load for_update và Desk save."""
    def _khoa_bo_thu(self):
        import frappe
        if self.name and not self.is_new():
            from vagabond.bo_sao_ke_thu import chu
            chu(self.name, khoa=True)
        # BT/chủ bộ -> SI theo tên -> PE. Factory lập nháp cũng khóa SI
        # trước đọc phần nợ đã phủ, nên Desk submit không đảo PE -> SI.
        ds = {r.reference_name for r in self.get('references') or []
              if r.reference_doctype == 'Sales Invoice' and r.reference_name}
        if self.name and not self.is_new():
            ds.update(frappe.get_all('Payment Entry Reference', filters={
                'parent': self.name, 'parenttype': 'Payment Entry',
                'reference_doctype': 'Sales Invoice'}, pluck='reference_name', limit_page_length=0))
        for ten in sorted(x for x in ds if x):
            frappe.db.get_value('Sales Invoice', ten, 'name', for_update=True)

    def load_from_db(self):
        if self.flags.get('for_update'):
            self._khoa_bo_thu()
        return super().load_from_db()

    def _save(self, *args, **kwargs):
        self._khoa_bo_thu()
        return super()._save(*args, **kwargs)
