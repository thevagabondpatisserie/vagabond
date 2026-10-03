import frappe
from frappe.model.document import Document


class VagabondSettings(Document):
	def validate(self):
		if self.phu_thu and self.phu_thu < 0:
			frappe.throw("Phu thu khong duoc am")
		if not (self.kitchen_lat and self.kitchen_lng):
			frappe.throw("Phai co toa do bep thi moi hoi duoc phi giao")
		# #307: hai ô tài khoản tồn kho BTP phải là tài khoản kho hợp lệ.
		from vagabond.tai_khoan_btp import kiem_o_cau_hinh
		kiem_o_cau_hinh(self)
		# v562 Codex #417: mỗi nhóm Zalo một dòng, không trùng tên, không trùng mã
		# chat; Loại tin và Chủ đề chỉ nhận mã trong danh mục.
		from vagabond.kenh_zalo import kiem_bang_nhom, kiem_ma_chat
		ds = [r.as_dict() for r in (self.get("zalo_nhom") or [])]
		loi = kiem_bang_nhom(ds)
		if loi:
			frappe.throw(loi)
		# v562 Codex #425: mã chat mới phải là nhóm đã nhắn bot.
		import json
		truoc = getattr(self, "get_doc_before_save", lambda: None)()
		cu = [r.chat_id for r in ((truoc.get("zalo_nhom") if truoc else None) or [])]
		try:
			moi = json.loads(getattr(self, "zalo_chat_moi", None) or "[]")
		except Exception:
			moi = []
		loi = kiem_ma_chat(ds, cu, moi)
		if loi:
			frappe.throw(loi)

	def on_update(self):
		from vagabond.tai_khoan_btp import khi_luu_cau_hinh
		khi_luu_cau_hinh(self)
