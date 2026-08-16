"""Mot o email go sai KHONG duoc lam rot don hang.

Vi sao co tep nay
-----------------
Ngay 16/08/2026 nhip dong bo bao mot loi va mot don khong vao duoc he:

    InvalidEmailAddressError: nguyenhongthientruc1610@gmail
    khong phai Dia chi email hop le

Khach go thieu phan ".com". Frappe kiem moi truong kieu Email khi luu, nem
loi, va CA DON HANG do khong ghi nhan duoc. Tien da thu that ma doanh thu
khong co.

Cai dang lo khong phai mot don, ma la HINH DANG cua loi: mot o khach tu go
lam hong viec ghi nhan doanh thu, va no chi nam trong Nhat ky loi chu khong
ai duoc bao. Dung loai loi da lam 149 don nam nhap nua thang hoi thang
truoc.

Nguyen tac (anh Viet chot 16/08/2026): DON HANG QUAN TRONG HON O EMAIL.
Email sai thi bo trong o do va van luu don, kem mot dong ghi chu de sales
biet ma hoi lai khach.

Vi sao dat o before_validate cua tung Doctype chu khong sua tung cho ghi
------------------------------------------------------------------------
Co it nhat bon duong dat email vao mot hoa don: nhip dong bo Pancake, man
Tinh tien, man Xuat hoa don, va nguoi go thang tren Desk. Va con Contact
sinh ra tu nhap khach. Va tung cho thi hom nao them cho thu nam la quen.
Dat o hook thi moi duong deu di qua.
"""

import re

import frappe

# Kiem o day chu khong goi validate_email_address cua Frappe: ham do NEM
# LOI, ma o day can mot cau tra loi dung/sai de con quyet dinh bo o di.
#
# Khong co gang bat het moi truong hop cua RFC. Chi can bat dung nhung cai
# Frappe se tu choi, va bat duoc cai da gap: thieu dau cham o phan mien.
RE_EMAIL = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[A-Za-z]{2,}$")


def hop_le(e):
	"""Chuoi nay co phai mot dia chi email dung dinh dang khong. THUAN."""
	e = str(e or "").strip()
	if not e:
		return True  # o trong la hop le, chi la khong co email
	if len(e) > 140:
		return False
	return bool(RE_EMAIL.match(e))


def _o_email(doctype):
	"""Ten cac truong kieu Email cua mot doctype."""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return []
	ra = []
	for f in meta.fields:
		if f.fieldtype == "Data" and (f.options or "") == "Email":
			ra.append(f.fieldname)
	return ra


def don(doc, method=None):
	"""Hook before_validate: bo cac o email go sai, GIU LAI chung tu.

	Khong bao gio nem loi. Ham nay ton tai de chung tu duoc luu, nen no ma
	nem loi thi tu phan boi chinh muc dich cua minh.
	"""
	try:
		xau = []
		for ten in _o_email(doc.doctype):
			gt = doc.get(ten)
			if gt and not hop_le(gt):
				xau.append("%s: %s" % (ten, str(gt)[:60]))
				doc.set(ten, None)
		if not xau:
			return
		nhac = "Email khách ghi sai định dạng nên máy bỏ trống ô đó để vẫn lưu được chứng từ. Cần thì hỏi lại khách: %s" % "; ".join(xau)
		# Ghi vao o ghi chu cua chung tu neu co, de sales nhin thay ngay tren
		# man hinh chu khong phai di mo Nhat ky loi.
		for o in ("vgb_ghi_chu", "remarks"):
			if doc.meta.has_field(o):
				cu = (doc.get(o) or "").strip()
				if nhac not in cu:
					doc.set(o, (cu + ("\n" if cu else "") + nhac)[:2000])
				break
		doc.flags.vgb_email_xau = xau
	except Exception:
		frappe.log_error(frappe.get_traceback(), "email_sach: don o email loi")


def ghi_vet(doc, method=None):
	"""Hook after_insert/on_update: ghi mot binh luan de con truy duoc.

	Tach khoi don() vi luc before_validate ban ghi co the chua co ten, ma
	Comment thi can ten de tro toi.
	"""
	try:
		xau = getattr(doc.flags, "vgb_email_xau", None)
		if not xau:
			return
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": "[Email] Bỏ trống ô email ghi sai để giữ được chứng từ: %s" % "; ".join(xau),
			}
		).insert(ignore_permissions=True)
		doc.flags.vgb_email_xau = None
	except Exception:
		pass


@frappe.whitelist()
def kiem(email=None):
	"""Man hinh hoi truoc khi luu: dia chi nay co dung dinh dang khong.

	Chan tu luc GO vao van tot hon la sua sau khi da hong. Nhung o day chi
	nhac chu khong chan cung: khach doc email qua dien thoai, sales go lai,
	va mot o nhac mau cam la du - chan cung o day thi sales ket khong luu
	duoc don.
	"""
	e = str(email or "").strip()
	if not e:
		return {"ok": 1, "nhac": ""}
	if hop_le(e):
		return {"ok": 1, "nhac": ""}
	nhac = "Email này sai định dạng nên hệ sẽ bỏ trống."
	if "@" in e and "." not in e.split("@")[-1]:
		nhac = "Thiếu phần đuôi sau dấu chấm, ví dụ .com hoặc .vn. Kiểm tra lại giúp em."
	elif "@" not in e:
		nhac = "Thiếu dấu @. Kiểm tra lại giúp em."
	return {"ok": 0, "nhac": nhac}
