"""Giữ bản xuất bản và lịch sử khỏi sửa trực tiếp qua Desk/API (#245)."""
import json
import frappe
from frappe.model.document import Document
from vagabond.noi_dung_web import chuan_hoa, kiem_quyen


class VagabondNoiDungWeb(Document):
    def autoname(self):
        self.name = "order"

    def validate(self):
        kiem_quyen()
        if not self.flags.luu_noi_dung_web:
            frappe.throw("Mở /bien-tap-web để lưu nháp hoặc xuất bản, có kiểm tra phiên bản.")
        if self.name != "order":
            frappe.throw("Chỉ hỗ trợ trang order.")
        for ten in ("ban_nhap", "ban_cong_khai"):
            try:
                self.set(ten, json.dumps(chuan_hoa(self.get(ten)), ensure_ascii=False))
            except (ValueError, TypeError) as e:
                frappe.throw(str(e))
        cu = self.get_doc_before_save()
        self.phien_ban = int(cu.phien_ban or 0) + 1 if cu else 1

    def on_trash(self):
        frappe.throw("Không xoá nội dung website. Dùng lịch sử để khôi phục bản trước.")
