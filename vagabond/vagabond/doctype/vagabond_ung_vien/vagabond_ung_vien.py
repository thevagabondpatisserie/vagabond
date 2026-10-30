"""Một lượt ứng tuyển (v622). Không xoá cứng; hết hạn lưu thì máy xoá thông tin cá nhân."""
import frappe
from frappe.model.document import Document


class VagabondUngVien(Document):
	def validate(self):
		# Mọi đường tạo hồ sơ (app, web, Desk, API) đều qua đây: bắt đồng ý lưu và
		# đặt hạn lưu, để nhịp xoá theo hạn luôn chọn được hồ sơ (Codex #518).
		from vagabond.tuyen_dung import an_danh, kiem_an_danh, kiem_luu_tru
		# Hồ sơ đã xoá theo hạn: Desk, API không được ghi lại thông tin cá nhân hay
		# mở lại cờ đã xoá (Codex #518 vòng 3).
		truoc = self.get_doc_before_save() if hasattr(self, "get_doc_before_save") else None
		row = {k: self.get(k) for k in an_danh({})}
		row["danh_gia"] = [{"nhan_xet": d.get("nhan_xet")} for d in (self.get("danh_gia") or [])]
		loi = kiem_an_danh(row, truoc.get("da_an_danh") if truoc else 0)
		if loi:
			frappe.throw(loi)
		loi, them = kiem_luu_tru({k: self.get(k) for k in ("dong_y", "dong_y_luc", "han_luu", "da_an_danh")},
			frappe.utils.now_datetime())
		if loi:
			frappe.throw(loi)
		for k, v in them.items():
			self.set(k, v)
