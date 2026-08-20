"""Mot phien ban da chot cua mot hop dong ban hang.

Anh Viet 21/08/2026, dat bai tu Loan Anh ben Sales: *"Khi co su dieu chinh,
he thong can tu dong sinh ra cac version (Vi du: Hop dong v1, Hop dong v2)
hoac ghi log ro rang ben duoi de Giam doc biet Sales da thay doi gi so voi
ban goc ban dau."*

Vi sao la mot doctype rieng chu khong phai bang con cua hop dong
----------------------------------------------------------------
Bang con song chet theo cha: sua hop dong la Frappe ghi de ca luoi con. Ma
day dung la thu KHONG duoc phep bien mat khi hop dong doi. Nen tach ra
doctype rieng, moi ban ghi la mot to giay khong ai sua duoc nua.

`anh_chup` giu NGUYEN VAN toan bo truong cua hop dong luc chot, dang JSON.
Giu ca to chu khong chi giu phan khac biet: phan khac biet doc duoc thi
tien, nhung mot nam sau muon dung lai to hop dong v2 that su trong nhu the
nao thi chi anh chup moi tra loi duoc.
"""

from frappe.model.document import Document


class HopDongPhienBan(Document):
	pass
