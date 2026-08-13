"""Ho so de nghi thanh toan (APP) cho nha cung cap.

Anh Viet 13/08/2026: "thao tac tren desktop bi roi qua nen minh lam tren
app". Luong that o tiem: thu mua gom cac hoa don mua den han cua MOT nha
cung cap thanh mot ho so, ke toan (FIN) duyet, giam doc duyet, roi ke toan
chuyen tien va doi chieu voi SePay de clear cong no.

Vi sao KHONG dung Payment Entry tran cua ERPNext lam ho so: Payment Entry
la but toan chi tien, no sinh ra SAU khi da duyet. Cai thieu la khuc TRUOC
do - de nghi, duyet hai cap, va dau vet ai duyet luc nao. Ho so nay giu
khuc do, den luc thanh toan moi sinh Payment Entry that.

Mot hoa don khong duoc nam trong hai ho so con hieu luc: khong thi cung
mot khoan no de nghi tra hai lan.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

CON_HIEU_LUC = ("Nhap", "Cho ke toan", "Cho giam doc", "Da duyet")


class VagabondHoSoTT(Document):
	def validate(self):
		if not self.dong:
			frappe.throw("Hồ sơ thanh toán phải có ít nhất một hoá đơn.")
		self.tong_tien = sum(flt(d.so_tien) for d in self.dong)
		if self.tong_tien <= 0:
			frappe.throw("Tổng đề nghị trả phải lớn hơn 0.")

		han = [getdate(d.han_tra) for d in self.dong if d.han_tra]
		self.han_tra_som_nhat = min(han) if han else None

		for d in self.dong:
			if flt(d.so_tien) <= 0:
				frappe.throw("Hoá đơn %s đề nghị trả 0 đồng, bỏ dòng đó ra." % d.hoa_don)
			# Tra hon so con no la sai: tien thua se treo lai thanh so du cho
			# nha cung cap ma khong ai biet vi sao.
			if flt(d.con_no) and flt(d.so_tien) > flt(d.con_no) + 1:
				frappe.throw(
					"Hoá đơn %s chỉ còn nợ %s đ mà đề nghị trả %s đ."
					% (d.hoa_don, flt(d.con_no), flt(d.so_tien))
				)
			trung = frappe.db.sql(
				"""select p.name, p.trang_thai from `tabVagabond Ho So TT Dong` d
				inner join `tabVagabond Ho So TT` p on p.name = d.parent
				where d.hoa_don = %s and p.name != %s""",
				(d.hoa_don, self.name or ""),
				as_dict=True,
			)
			for t in trung:
				if t["trang_thai"] in CON_HIEU_LUC:
					frappe.throw(
						"Hoá đơn %s đã nằm trong hồ sơ %s (%s)."
						% (d.hoa_don, t["name"], t["trang_thai"])
					)
