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
