"""Chuong trinh khuyen mai.

Vi sao khong dung Pricing Rule co san cua ERPNext (anh Viet 11/08/2026):
Pricing Rule lam duoc giam tong hoa don, giam gia mon, mua X tang Y va dong
gia, nhung khong lam duoc "mua A giam B", khong co han muc chong gian lan
theo thu ngan / theo ca, khong co ma voucher dung mot lan, va man cau hinh
cua no o Desk qua nang cho thu ngan. Nen minh giu mot doctype rieng, gon,
va man cau hinh nam ngay trong app /bep.

Moi rang buoc o day deu la de CHAN SAI LUC CAU HINH. Chan o luc tinh tien
thi da muon: bill in ra roi, tien da thu roi.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

CACH_CAN_MON_UU_DAI = ("Giam gia mon", "Mua A giam B", "Mua X tang Y", "Tang mon", "Dong gia")
CACH_CAN_MON_DIEU_KIEN = ("Mua A giam B", "Mua X tang Y")


def sinh_ma_ctkm():
	"""Ma dang KM + 6 ky tu. Bo chu O va so 0, chu I va so 1 - nhan vien doc
	ma qua dien thoai cho doi tac rat de nham hai cap nay."""
	chu = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	for _ in range(40):
		ma = "KM" + "".join(chu[int(c, 16) % len(chu)] for c in frappe.generate_hash(length=6))
		if not frappe.db.exists("Vagabond CTKM", ma):
			return ma
	frappe.throw("Không sinh được mã chương trình, vui lòng thử lại.")


class VagabondCTKM(Document):
	def autoname(self):
		if not self.ma_ctkm:
			self.ma_ctkm = sinh_ma_ctkm()
		self.name = self.ma_ctkm

	def validate(self):
		if not self.nguoi_tao:
			self.nguoi_tao = frappe.session.user

		# --- muc uu dai phai co that ---
		if self.cach_thuc == "Dong gia":
			if flt(self.gia_dong) <= 0:
				frappe.throw("Đồng giá thì phải điền mức giá đồng, ví dụ 39.000đ.")
		elif self.cach_thuc == "Giam luy ke":
			if not self.dong_bac:
				frappe.throw("Giảm luỹ kế thì phải khai ít nhất một bậc.")
		elif self.cach_thuc == "Tang mon":
			pass  # muc uu dai nam o dong mon
		elif flt(self.gia_tri) <= 0 and self.cach_thuc != "Mua X tang Y":
			frappe.throw("Chương trình chưa có mức giảm. Vui lòng điền giá trị giảm.")

		if self.kieu_giam == "Phan tram" and flt(self.gia_tri) > 100:
			frappe.throw("Giảm theo phần trăm mà điền %s là quá 100%%." % flt(self.gia_tri))

		# --- bac luy ke phai xep tang dan va khong trung nguong ---
		if self.cach_thuc == "Giam luy ke":
			moc = []
			for b in self.dong_bac:
				if flt(b.tu_tien) in moc:
					frappe.throw("Bậc %s bị khai hai lần." % flt(b.tu_tien))
				moc.append(flt(b.tu_tien))
				if b.kieu_giam == "Phan tram" and flt(b.gia_tri) > 100:
					frappe.throw("Bậc từ %s giảm quá 100%%." % flt(b.tu_tien))

		# --- mon phai du vai tro cho tung cach thuc ---
		uu_dai = [d for d in (self.dong_mon or []) if d.vai_tro == "Uu dai"]
		dieu_kien = [d for d in (self.dong_mon or []) if d.vai_tro == "Dieu kien"]
		if self.cach_thuc in CACH_CAN_MON_UU_DAI and not uu_dai and self.pham_vi == "Mon chi dinh":
			frappe.throw(
				"Cách thức %s cần ít nhất một món vai trò Ưu đãi." % self.cach_thuc
			)
		if self.cach_thuc in CACH_CAN_MON_DIEU_KIEN and not dieu_kien:
			frappe.throw(
				"Cách thức %s cần ít nhất một món vai trò Điều kiện (món khách phải mua)."
				% self.cach_thuc
			)
		if self.cach_thuc in ("Tang mon", "Mua X tang Y") and not uu_dai:
			frappe.throw("Chương trình tặng món thì phải khai món được tặng ở vai trò Ưu đãi.")

		# --- pham vi mon ---
		if self.pham_vi == "Nhom mon chi dinh" and not (self.nhom_mon or "").strip():
			frappe.throw("Chọn phạm vi Nhóm món chỉ định thì phải liệt kê nhóm món.")
		if self.pham_vi == "Mon chi dinh" and not uu_dai:
			frappe.throw("Chọn phạm vi Món chỉ định thì phải liệt kê món ở bảng dưới.")

		# --- ma voucher ---
		if self.cach_ma == "Ma co dinh":
			ma = (self.ma_co_dinh or "").strip().upper()
			if not ma:
				frappe.throw("Chọn mã cố định thì phải điền mã cho cashier gõ.")
			self.ma_co_dinh = ma
			trung = frappe.db.get_value(
				"Vagabond CTKM",
				{"ma_co_dinh": ma, "bat": 1, "name": ["!=", self.name or ""]},
				"ten",
			)
			if trung and cint(self.bat):
				frappe.throw("Mã %s đang được chương trình \"%s\" dùng rồi." % (ma, trung))

		# --- thoi gian ---
		if self.tu_ngay and self.den_ngay and str(self.den_ngay) < str(self.tu_ngay):
			frappe.throw("Ngày kết thúc đang sớm hơn ngày bắt đầu.")

		# --- doi tuong ---
		if self.doi_tuong == "Theo hang khach" and not (self.hang_khach or "").strip():
			frappe.throw("Chọn theo hạng khách thì phải liệt kê hạng.")
		if self.doi_tuong == "Theo nhom khach" and not (self.nhom_khach or "").strip():
			frappe.throw("Chọn theo nhóm khách thì phải liệt kê nhóm.")
		if self.doi_tuong == "Khach chi dinh" and not self.dong_khach:
			frappe.throw("Chọn khách chỉ định thì phải liệt kê khách.")

		# --- canh bao chong gian lan ---
		# Khong chan, chi nhac: chuong trinh giam sau ma khong co tran va
		# khong can OTP la mieng moi de nhan vien tu bam cho nguoi quen.
		sau = (self.kieu_giam == "Phan tram" and flt(self.gia_tri) >= 30) or (
			self.kieu_giam == "So tien" and flt(self.gia_tri) >= 100000
		)
		if cint(self.bat) and sau and not cint(self.can_otp) and not flt(self.giam_toi_da):
			frappe.msgprint(
				"Chương trình này giảm khá sâu mà chưa đặt trần giảm cũng chưa bắt "
				"buộc OTP quản lý. Nên đặt ít nhất một trong hai để nhân viên không "
				"tự bấm cho người quen.",
				indicator="orange",
				alert=True,
			)
