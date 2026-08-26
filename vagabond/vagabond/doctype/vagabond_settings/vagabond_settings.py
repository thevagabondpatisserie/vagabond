import frappe
from frappe.model.document import Document


class VagabondSettings(Document):
	def validate(self):
		if self.phu_thu and self.phu_thu < 0:
			frappe.throw("Phu thu khong duoc am")
		if not (self.kitchen_lat and self.kitchen_lng):
			frappe.throw("Phai co toa do bep thi moi hoi duoc phi giao")
		self._chan_khoa_qz_bi_dien_de()

	def _chan_khoa_qz_bi_dien_de(self):
		"""Khong cho luu mot chuoi khong phai khoa PEM vao o khoa rieng QZ.

		Anh Viet 26/08/2026: o "Khoa rieng QZ Tray" khai kieu Password, ma
		Chrome nhin thay o Password la tu dien mat khau dang nhap da luu vao
		NGAY LUC TRANG NAP XONG. Frappe ghi nhan do la mot thay doi, tieu de
		nhay sang "Chua luu", va lan bam Luu bat ky sau do la khoa in bi thay
		bang mat khau. Da xay ra hai lan trong mot buoi.

		Nhin man hinh khong thay duoc: o Password che noi dung. Nguoi sua chi
		biet khi thu ngan keu may in hien hop la va tu choi chu ky.

		Nen chan thang o day. Khoa that luon co hai dong BEGIN va END; mot mat
		khau thi khong. Chan o buoc validate nghia la du ai bam Luu, du trinh
		duyet dien gi vao, khoa dang chay cung khong mat.

		O rong van cho qua: do la cach tat in ngam mot cach co y.
		"""
		khoa = (self.get("qz_khoa_rieng") or "").strip()
		if not khoa:
			return
		if "-----BEGIN" in khoa and "-----END" in khoa:
			return
		frappe.throw(
			"Ô <b>Khoá riêng QZ Tray</b> đang chứa một chuỗi KHÔNG phải khoá PEM, "
			"nên máy chủ không lưu.<br><br>"
			"Gần như chắc chắn là trình duyệt vừa tự điền mật khẩu đăng nhập vào ô "
			"đó: ô này khai kiểu Password nên Chrome tưởng là ô đăng nhập. Bấm Lưu "
			"lúc này là mất khoá in của cả tiệm.<br><br>"
			"Cách làm: tải lại trang mà KHÔNG lưu, xoá mật khẩu đã lưu cho site này "
			"trong chrome://password-manager/passwords, rồi dán lại trọn tệp khoá "
			"riêng, kể cả hai dòng BEGIN và END.")
