"""Ho so de nghi thanh toan (APP) cho nha cung cap va cho hoan ung.

Anh Viet 13/08/2026: "thao tac tren desktop bi roi qua nen minh lam tren
app". Luong that o tiem: thu mua gom cac hoa don mua den han cua MOT nha
cung cap thanh mot ho so, ke toan (FIN) duyet, giam doc duyet, roi ke toan
chuyen tien va doi chieu voi SePay de clear cong no.

HAI LOAI HO SO, mot phan he:
  - loai "NCC": gom hoa don mua da ghi so cua mot nha cung cap. Dong PHAI
    tro toi mot Purchase Invoice co that.
  - loai "Hoan ung": Uyen go tay tung khoan da chi ho bang tien tam ung
    OCB (hang test khong nhap kho, hang phat sinh, bao tri...). Luc lap
    CHUA co Purchase Invoice nao ca; may sinh hoa don mua sau, o buoc giam
    doc duyet - xem vagabond.ho_so_tt._sinh_hoa_don_hoan_ung.

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
			frappe.throw("Hồ sơ thanh toán phải có ít nhất một dòng.")
		self.tong_tien = sum(flt(d.so_tien) for d in self.dong)
		if self.tong_tien <= 0:
			frappe.throw("Tổng đề nghị trả phải lớn hơn 0.")

		# Tru tam ung: Uyen da ung truoc mot khoan thi lan nay chi chuyen phan
		# con lai. Khong cho tru qua tong - tru qua thanh so am, ma so am o
		# day nghia la cong ty doi lai tien, do la nghiep vu khac han.
		if flt(self.da_tam_ung) < 0:
			frappe.throw("Số tiền đã tạm ứng không được âm.")
		if flt(self.da_tam_ung) > flt(self.tong_tien) + 1:
			frappe.throw(
				"Đã tạm ứng %s đ mà tổng hồ sơ chỉ %s đ. Số trừ không được lớn hơn tổng."
				% (flt(self.da_tam_ung), flt(self.tong_tien))
			)
		self.con_lai = flt(self.tong_tien) - flt(self.da_tam_ung)

		han = [getdate(d.han_tra) for d in self.dong if d.han_tra]
		self.han_tra_som_nhat = min(han) if han else None

		# "TK cong ty" cung khong co hoa don mua nao ca: tien di thang tu tai
		# khoan cong ty, ke toan tu dinh khoan. Xep chung nhom khong-hoa-don.
		la_hoan_ung = (self.loai or "NCC") in ("Hoan ung", "Hoan ung HD", "TK cong ty")

		# Chi tu TK cong ty ma khong co hoa don GTGT thi ho so chi con dua vao
		# chung tu roi: phai noi ro la chung tu gi VA phai dinh kem file that.
		# Khong kiem o lan luu dau tien - luc do ban ghi chua ton tai nen chua
		# the dinh kem duoc gi; tu lan luu thu hai tro di thi bat buoc.
		if (self.loai or "") == "TK cong ty" and (self.loai_cp_thue or "") == "Chi phi khong hop le":
			if not (self.loai_chung_tu or "").strip():
				frappe.throw(
					"Khoản chi không có hoá đơn thì phải chọn Loại chứng từ đính kèm, "
					"rồi đính kèm đúng chứng từ đó."
				)
			if not self.is_new():
				co_tep = frappe.db.count(
					"File",
					{"attached_to_doctype": self.doctype, "attached_to_name": self.name},
				)
				if not co_tep:
					frappe.throw(
						"Hồ sơ %s chưa đính kèm chứng từ nào. Đã chọn loại chứng từ là "
						"\"%s\" thì phải tải đúng file đó lên mới lưu được."
						% (self.name, self.loai_chung_tu)
					)
		for d in self.dong:
			nhan = d.hoa_don or d.so_hd_ncc or d.noi_dung or ("dòng %s" % d.idx)
			if flt(d.so_tien) <= 0:
				frappe.throw("Dòng %s đề nghị trả 0 đồng, bỏ dòng đó ra." % nhan)

			# Mot giao dich ngan hang chi duoc hoan ung MOT lan. Khac voi chan
			# trung hoa don o duoi: cho nay chan theo tien that da ra khoi quy
			# OCB, nen no bat duoc ca truong hop go tay trung voi khoan da tick
			# tu sao ke.
			ma_gd = (d.ma_giao_dich or "").strip()
			if ma_gd:
				trung_gd = frappe.db.sql(
					"""select p.name, p.trang_thai from `tabVagabond Ho So TT Dong` d
					inner join `tabVagabond Ho So TT` p on p.name = d.parent
					where d.ma_giao_dich = %s and p.name != %s""",
					(ma_gd, self.name or ""),
					as_dict=True,
				)
				for t in trung_gd:
					if t["trang_thai"] in CON_HIEU_LUC or t["trang_thai"] == "Da thanh toan":
						frappe.throw(
							"Giao dịch %s đã nằm trong hồ sơ %s (%s), không hoàn ứng hai lần."
							% (ma_gd, t["name"], t["trang_thai"])
						)

			if not d.hoa_don:
				# Ho so NCC bat buoc phai co hoa don mua that; ho so hoan ung
				# thi luc lap chua co, nhung phai co noi dung de con biet chi gi.
				if not la_hoan_ung:
					frappe.throw("Dòng %s chưa chọn hoá đơn mua." % nhan)
				if not (d.noi_dung or "").strip():
					frappe.throw("Dòng %s chưa ghi nội dung chi." % d.idx)
				continue

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
