"""Thu vien bao gia: mot cho duy nhat giu moi thu Loan Anh dua vao to bao gia.

Anh Viet 14/08/2026: *"Đa phần các sản phẩm trong báo giá là các sản phẩm
thiết kế riêng không có trong danh mục... Cần có hình ảnh, mô tả, làm song
ngữ toàn bộ hợp đồng"* va *"tính các phần nhân công, vận chuyển, set up,...
phải lưu vào đâu để sau này thao tác nhanh (có thể sửa giá các món này)"*.

Nen mot ban ghi o day co the la:
  - MON co san trong danh muc: khai ma_item, hinh va don gia tu keo ve tu
    Item, khoi nhap lai;
  - MON THIET KE RIENG cho mot khach: khong co ma_item, tu nhap hinh va gia;
  - PHI (gia cong khuon, thu banh, nhan cong, set up): loai = "Phí";
  - DICH VU THEM co gia bang chu ("Miễn phí", "Báo theo khoảng cách"):
    loai = "Dịch vụ thêm", dien gia_chu_vi va gia_chu_en thay cho don_gia.
"""

import frappe
from frappe.model.document import Document


class BaoGiaThuVien(Document):
	def autoname(self):
		"""Danh so TVBG-00001. Chuoi "format:TVBG-{#####}" mot minh khong du:
		Frappe doc rieng tung cap ngoac nen o dem chay voi tien to rong, dung
		chung bo dem toan he - muc dau tien ra TVBG-00710 chu khong phai
		00001. Dem chinh cac ban ghi TVBG hien co."""
		cuoi = frappe.db.sql(
			"""select name from `tabBao Gia Thu Vien`
			where name like 'TVBG-%' order by name desc limit 1"""
		)
		so = 1
		if cuoi:
			try:
				so = int(str(cuoi[0][0]).rsplit("-", 1)[1]) + 1
			except Exception:
				so = 1
		self.name = "TVBG-%05d" % so

	def validate(self):
		for f in ("ten_vi", "ten_en", "nhom", "kich_thuoc"):
			if self.get(f):
				self.set(f, str(self.get(f)).strip())
		if not self.ten_vi:
			frappe.throw("Phải có tên tiếng Việt.")

		# Mon co trong danh muc thi keo hinh, ten va gia ve, khong bat nguoi
		# dung go lai. Chi dien vao cho con TRONG - da sua tay thi giu nguyen.
		if self.ma_item:
			it = frappe.db.get_value(
				"Item",
				self.ma_item,
				["item_name", "image", "stock_uom", "description"],
				as_dict=True,
			) or {}
			if not self.hinh and it.get("image"):
				self.hinh = it["image"]
			if not self.dvt_vi and it.get("stock_uom"):
				self.dvt_vi = it["stock_uom"]
			if not self.mo_ta_vi and it.get("description"):
				self.mo_ta_vi = frappe.utils.strip_html(it["description"]).strip()[:900]
