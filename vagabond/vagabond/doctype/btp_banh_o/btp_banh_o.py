import frappe
from frappe.model.document import Document

# Các ô có nhật ký (giống btp._ghi_o). decor_da_lam là số máy tự trừ, không hiện.
O_GHI = ("so_btp", "so_decor", "so_refill", "refill_tu", "refill_den")


def doi_khi_luu_ca_bang(truoc, sau):
	"""THUẦN. So hai danh sách dòng (dict có ma_hang) của bảng BTP, trả các
	thay đổi cần ghi nhật ký: (ma_hang, ten_banh, truong, truoc, sau, ly_do).
	Mã mới thêm ghi "ma" với ly_do them_ma, mã bị bỏ ghi xoa_ma."""
	cu = {str(d.get("ma_hang") or ""): d for d in (truoc or []) if d.get("ma_hang")}
	moi = {str(d.get("ma_hang") or ""): d for d in (sau or []) if d.get("ma_hang")}
	ra = []
	for ma, d in moi.items():
		c = cu.get(ma)
		if c is None:
			ra.append((ma, d.get("ten_banh"), "ma", "", ma, "them_ma"))
			c = {}
		for o in O_GHI:
			a, b = c.get(o), d.get(o)
			if str(a if a is not None else "") != str(b if b is not None else ""):
				ra.append((ma, d.get("ten_banh"), o, a, b, "desk"))
	for ma, c in cu.items():
		if ma not in moi:
			ra.append((ma, c.get("ten_banh"), "ma", ma, "", "xoa_ma"))
	return ra


class BTPBanhO(Document):
	def on_update(self):
		"""v653 Codex #560: màn /btp, Kiểm bánh và các hàm của btp.py ghi từng
		dòng bằng UPDATE và tự ghi nhật ký, không lưu cả bảng. Lưu cả bảng chỉ
		xảy ra khi sửa thẳng trên Desk hay qua API; khi đó so với bản trong CSDL
		và ghi nhật ký từng ô đổi, cùng giao dịch, để không còn đường sửa số
		nào mà không biết ai sửa."""
		from vagabond import btp

		ham = getattr(self, "get_doc_before_save", None)
		truoc = ham() if ham else None
		dong_cu = [d.as_dict() for d in (getattr(truoc, "dong", None) or [])]
		dong_moi = [d.as_dict() for d in (self.get("dong") or [])]
		for ma, ten, truong, a, b, ly_do in doi_khi_luu_ca_bang(dong_cu, dong_moi):
			btp.ghi_nhat_ky(ma, ten, truong, a, b, ly_do, nguon="Desk")
