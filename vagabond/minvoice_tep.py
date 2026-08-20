# -*- coding: utf-8 -*-
"""Ban the hien PDF cua hoa don M-Invoice: keo ve, dinh vao ho so, don sau 60 ngay.

Vi sao tep nay ton tai
----------------------
Anh Viet 20/08/2026: *"Khong chi lay data text ma phai fetch luon ban the
hien PDF cua hoa don do ve, luu thanh File tren ERPNext... Khi Ke toan/Thu
mua tao Ho so de nghi thanh toan (Ho so APP) va chon ma hoa don, he thong
tu dong keo cai file PDF ban the hien nay dinh kem vao phieu luon de Ke
toan truong duyet cho hop le, khong bat ke toan phai tai tay tu M-Invoice
nua. Du lieu file nay neu nang database thi em cai cho xoa sau 60 ngay."*

Ba viec, ba ham chinh:
  keo_pdf_thieu()    nhip hang gio, keo PDF cho hoa don DAU VAO con thieu
  dinh_vao_ho_so(d)  goi tu ho_so_tt ngay sau khi insert ho so
  don_dep_pdf()      nhip hang dem, xoa PDF qua so ngay giu (mac dinh 60)

Nguyen tac
----------
1. PDF la BAN CACHE cua ban the hien, khong phai chung tu goc. Ban goc
   nam ben M-Invoice va luc nao cung tai lai duoc. Vi vay viec xoa sau 60
   ngay la xoa cache, khong pham QT-20 (anh Viet duyet ro dieu nay).
2. Duong dinh vao ho so KHONG BAO GIO lam hong viec tao ho so: M-Invoice
   sap thi ho so van phai tao duoc, thieu PDF thi ke toan truong van con
   duong tai tay nhu cu. Moi loi o day chi vao Error Log.
3. Tep luu is_private=1: hoa don mua co gia von, khong phoi ra duong
   cong khai.
4. Hoa don loi lien tuc (5 lan) thi thoi, khong thu lai nua de khong dot
   het luot goi cua cac to khac. Danh sach bo qua nam trong Cai dat, xoa
   trang o do la may thu lai tu dau.
"""

# ------------------------------------------------------------ phan thuan
# Ham thuan tren `import frappe`, bo kiem thu nap bang python3 tran.

TEN_TIEN_TO = "HDDT-"


def ten_tep_pdf(ky_hieu, so_hd):
	"""Ten tep thong nhat de moi cho khac nhan ra PDF nao cua may sinh.

	Chi giu chu, so, gach ngang: ky hieu hoa don co the mang ky tu la,
	nhet thang vao ten tep la hong duong dan tren dia.
	"""
	loi = "%s%s-%s" % (TEN_TIEN_TO, str(ky_hieu or "KH"), str(so_hd or "0"))
	sach = "".join(c if (c.isalnum() or c == "-") else "-" for c in loi)
	while "--" in sach:
		sach = sach.replace("--", "-")
	return sach.strip("-") + ".pdf"


def la_pdf(ruot):
	"""Dung la PDF that khi bat dau bang %PDF. JSON bao loi thi khong phai."""
	return isinstance(ruot, (bytes, bytearray)) and ruot[:4] == b"%PDF"


def boc_b64_trong_json(du):
	"""Tim chuoi base64 cua PDF trong mot goi JSON M-Invoice tra ve.

	Duong /invoices/{id}/pdf tra JSON chu khong tra byte. Khong biet chac
	ho dat ten truong gi nen do cac ten hay gap; gia tri phai la chuoi du
	dai moi tinh.
	"""
	if not isinstance(du, dict):
		return ""
	for k in ("data", "pdf", "content", "file", "fileData", "base64", "result"):
		v = du.get(k)
		if isinstance(v, dict):
			v = boc_b64_trong_json(v)
		if isinstance(v, str) and len(v) > 400:
			return v
	return ""


# ------------------------------------------------------- phan can Frappe

import json

import frappe
from frappe.utils import cint

DT_HD = "MInvoice Invoice"
DT_HS = "Vagabond Ho So TT"

# Toi da bao nhieu PDF mot nhip hang gio. 30 to mot gio la 720 to mot
# ngay, gap nhieu lan so hoa don dau vao that cua tiem.
MOI_NHIP = 30
LOI_TOI_DA = 5

TRUONG_MOI = {
	"Vagabond Settings": [
		{
			"fieldname": "sec_minvoice_pdf", "label": "M-Invoice - bản thể hiện PDF",
			"fieldtype": "Section Break", "insert_after": "sepay_chua_map",
		},
		{
			"fieldname": "minvoice_pdf_bat", "label": "Tự kéo PDF bản thể hiện",
			"fieldtype": "Check", "insert_after": "sec_minvoice_pdf", "default": "1",
			"description": (
				"Bật thì mỗi giờ máy kéo PDF bản thể hiện của hoá đơn đầu vào "
				"về làm tệp đính kèm, để hồ sơ APP tự có hoá đơn cho kế toán "
				"trưởng duyệt."
			),
		},
		{
			"fieldname": "minvoice_pdf_ngay_giu", "label": "Số ngày giữ PDF",
			"fieldtype": "Int", "insert_after": "minvoice_pdf_bat", "default": "60",
			"description": (
				"Quá số ngày này thì máy xoá tệp PDF cho nhẹ hệ thống. Đây là "
				"bản cache, bản gốc vẫn nằm bên M-Invoice và kéo lại được."
			),
		},
		{
			"fieldname": "minvoice_pdf_bo_qua", "label": "Hoá đơn kéo PDF lỗi (máy tự ghi)",
			"fieldtype": "Small Text", "insert_after": "minvoice_pdf_ngay_giu",
			"read_only": 1,
			"description": (
				"Hoá đơn kéo lỗi 5 lần thì máy thôi thử và ghi vào đây. Xoá "
				"trắng ô này là máy thử lại từ đầu."
			),
		},
	]
}


def _cai_dat_chung():
	from vagabond.lib import cfg

	return cfg()


def _tai_pdf_tho(hid, loai):
	"""Goi sang M-Invoice lay byte PDF cua mot hoa don. Tra (bytes, loi).

	Do duong ngay 20/08/2026, hai bang chung:
	1. Tham do khong token: /erp/qlhd-api/invoices/<id>/download/... tra 401
	   (co that, cho moi ten tep), con /pdf va batch-download tra 404.
	2. Doc bundle SPA cua trang quan ly: ho tai XML bang GET
	   .../<id>/download/invoice.xml, nen PDF thu invoice.pdf truoc; goi
	   "download/pdf" tran da nghiem thu tra 400 (thieu ten tep).
	Moi lan truot deu ghi kem ruot phan hoi de lan sau khong phai doan.
	Neu tra ve goi zip (PK) thi boc lay tep .pdf dau tien ben trong.
	"""
	import requests

	from vagabond.minvoice_dong_bo import LOAI_RA, _cai_dat

	cd = _cai_dat()
	dau = {"apiToken": cd["token"]}
	kieu = "out" if loai == LOAI_RA else "in"
	goc = cd["base"] + "/erp/qlhd-api/invoices/"
	cac_duong = [
		goc + "%s/download/invoice.pdf" % hid,
		goc + "%s/download/pdf?type=%s" % (hid, kieu),
		goc + "%s/download/pdf" % hid,
	]
	vet = []
	for duong in cac_duong:
		try:
			r = requests.get(duong, headers=dau, timeout=40)
			if r.status_code != 200:
				vet.append("%s -> HTTP %s [%s]" % (duong, r.status_code, r.content[:120]))
				continue
			ruot = _boc_pdf(r.content)
			if ruot:
				return ruot, ""
			vet.append("%s -> 200 nhung khong phai PDF (%s...)" % (duong, r.content[:80]))
		except Exception as e:
			vet.append("%s -> %s" % (duong, str(e)[:120]))
	return None, "\n".join(vet)


def _boc_pdf(ruot):
	"""Boc byte PDF tu phan hoi: PDF tran, goi zip, hay JSON boc base64."""
	import base64

	if la_pdf(ruot):
		return ruot
	# Goi zip: duong tai ve hay duoc nen lai, tep .pdf nam ben trong.
	if isinstance(ruot, (bytes, bytearray)) and ruot[:2] == b"PK":
		try:
			import io as _io
			import zipfile

			with zipfile.ZipFile(_io.BytesIO(bytes(ruot))) as z:
				for ten in z.namelist():
					if ten.lower().endswith(".pdf"):
						trong = z.read(ten)
						if la_pdf(trong):
							return trong
		except Exception:
			return None
	# JSON boc base64.
	try:
		giai = base64.b64decode(boc_b64_trong_json(json.loads(ruot)))
		if la_pdf(giai):
			return giai
	except Exception:
		pass
	return None


def _pdf_dang_co(hid):
	"""Tep PDF ban the hien dang dinh tren mot hoa don M-Invoice, neu co."""
	ds = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": DT_HD, "attached_to_name": hid,
			"file_name": ["like", TEN_TIEN_TO + "%"],
		},
		fields=["name", "file_name", "file_url"],
		order_by="creation desc",
		limit_page_length=1,
	)
	return ds[0] if ds else None


def _bo_qua():
	try:
		return json.loads(_cai_dat_chung().get("minvoice_pdf_bo_qua") or "{}") or {}
	except Exception:
		return {}


def _ghi_bo_qua(bang):
	try:
		frappe.db.set_single_value(
			"Vagabond Settings", "minvoice_pdf_bo_qua",
			json.dumps(bang, ensure_ascii=False),
		)
		frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_tep: ghi danh sach bo qua")


def _keo_va_dinh(hid):
	"""Keo PDF cua mot hoa don va dinh vao chinh ban ghi do. Tra ve tep.

	Da co roi thi tra ve tep cu, khong keo lai - moi hoa don mot ban.
	"""
	co = _pdf_dang_co(hid)
	if co:
		return co
	hd = frappe.db.get_value(
		DT_HD, hid, ["name", "ky_hieu", "so_hd", "loai"], as_dict=True
	)
	if not hd:
		frappe.throw("Không có hoá đơn M-Invoice %s trong hệ." % hid)
	ruot, loi = _tai_pdf_tho(hid, hd.loai)
	if not ruot:
		raise Exception("Khong keo duoc PDF cua %s:\n%s" % (hid, loi))
	f = frappe.get_doc({
		"doctype": "File",
		"file_name": ten_tep_pdf(hd.ky_hieu, hd.so_hd),
		"attached_to_doctype": DT_HD,
		"attached_to_name": hid,
		"content": ruot,
		"is_private": 1,
	})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	return {"name": f.name, "file_name": f.file_name, "file_url": f.file_url}


@frappe.whitelist()
def lay_pdf(ma):
	"""Lay (keo neu chua co) PDF ban the hien cua mot hoa don M-Invoice."""
	from vagabond.ho_so_tt import VAI_FIN, VAI_GD, VAI_LAP

	if not ((VAI_LAP | VAI_FIN | VAI_GD) & set(frappe.get_roles())):
		frappe.throw("Tài khoản của bạn chưa được xem hoá đơn mua. Nhờ kế toán mở giúp.")
	tep = _keo_va_dinh(ma)
	frappe.db.commit()
	return {"ok": 1, "tep": tep["name"], "ten": tep["file_name"], "url": tep["file_url"]}


def dinh_vao_ho_so(doc):
	"""Dinh PDF ban the hien cua tung hoa don trong ho so vao chinh ho so.

	Goi ngay sau doc.insert() o ho_so_tt. KHONG BAO GIO throw: M-Invoice
	sap thi ho so van phai tao duoc (nguyen tac 2 o dau tep).
	"""
	try:
		if not cint(_cai_dat_chung().get("minvoice_pdf_bat") or 1):
			return 0
		da_dinh = 0
		da_gap = set()
		for dong in (doc.get("dong") or []):
			pi = (dong.get("hoa_don") or "").strip()
			if not pi or pi in da_gap:
				continue
			da_gap.add(pi)
			hid = (frappe.db.get_value("Purchase Invoice", pi, "custom_minvoice_id") or "").strip()
			if not hid or not frappe.db.exists(DT_HD, hid):
				continue
			try:
				tep = _keo_va_dinh(hid)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					"minvoice_tep: keo PDF cho ho so %s" % doc.name,
				)
				continue
			# Dinh vao ho so bang cach tro cung file_url, khong nhan doi
			# noi dung tren dia.
			if frappe.db.exists("File", {
				"attached_to_doctype": DT_HS, "attached_to_name": doc.name,
				"file_url": tep["file_url"],
			}):
				continue
			f = frappe.get_doc({
				"doctype": "File",
				"file_name": tep["file_name"],
				"file_url": tep["file_url"],
				"attached_to_doctype": DT_HS,
				"attached_to_name": doc.name,
				"is_private": 1,
			})
			f.flags.ignore_permissions = True
			f.insert(ignore_permissions=True)
			da_dinh += 1
		return da_dinh
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_tep: dinh vao ho so")
		return 0


def keo_pdf_thieu():
	"""Nhip hang gio: keo PDF cho hoa don DAU VAO gan day con thieu tep.

	Chi dau vao: ho so APP toan hoa don mua. Dau ra da co ban luu ben
	M-Invoice va khong ai duyet chi bang dau ra ca.
	"""
	try:
		if not frappe.db.exists("DocType", DT_HD):
			return
		c = _cai_dat_chung()
		if not cint(c.get("minvoice_pdf_bat") or 1):
			return
		ngay_giu = cint(c.get("minvoice_pdf_ngay_giu")) or 60
		bo_qua = _bo_qua()
		ds = frappe.db.sql(
			"""select hd.name from `tabMInvoice Invoice` hd
			where hd.loai = %(loai)s
			  and hd.ngay_lap >= %(tu)s
			  and ifnull(hd.so_hd, '') != '' and hd.so_hd != '0'
			  and not exists (
				select 1 from `tabFile` f
				where f.attached_to_doctype = %(dt)s
				  and f.attached_to_name = hd.name
				  and f.file_name like %(tien_to)s)
			order by hd.ngay_lap desc limit %(gioi_han)s""",
			{
				"loai": "Đầu vào",
				"tu": frappe.utils.add_days(frappe.utils.nowdate(), -ngay_giu),
				"dt": DT_HD,
				"tien_to": TEN_TIEN_TO + "%",
				"gioi_han": MOI_NHIP,
			},
			as_dict=True,
		)
		doi = 0
		for r in ds:
			if cint(bo_qua.get(r.name)) >= LOI_TOI_DA:
				continue
			try:
				_keo_va_dinh(r.name)
				bo_qua.pop(r.name, None)
			except Exception:
				bo_qua[r.name] = cint(bo_qua.get(r.name)) + 1
				doi += 1
				frappe.log_error(
					frappe.get_traceback(), "minvoice_tep: keo PDF %s" % r.name
				)
			frappe.db.commit()
		if doi:
			_ghi_bo_qua(bo_qua)
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_tep: nhip keo PDF vo loi")


def don_dep_pdf():
	"""Nhip hang dem: xoa PDF ban the hien qua so ngay giu.

	Day la don CACHE, khong phai xoa chung tu: ban goc nam ben M-Invoice,
	can lai thi keo lai duoc (anh Viet chot 20/08/2026: "Du lieu file nay
	neu nang database thi em cai cho xoa sau 60 ngay").

	Xoa ca cac dong File tro cung file_url (ban dinh vao ho so) TRUOC roi
	moi xoa dong goc, de noi dung tren dia di theo dong cuoi cung.
	"""
	try:
		ngay_giu = cint(_cai_dat_chung().get("minvoice_pdf_ngay_giu")) or 60
		moc = frappe.utils.add_days(frappe.utils.nowdate(), -ngay_giu)
		goc = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": DT_HD,
				"file_name": ["like", TEN_TIEN_TO + "%"],
				"creation": ["<", moc],
			},
			fields=["name", "file_url"],
			limit_page_length=200,
		)
		da_xoa = 0
		for g in goc:
			try:
				if g.file_url:
					for ban in frappe.get_all(
						"File",
						filters={"file_url": g.file_url, "name": ["!=", g.name]},
						pluck="name",
					):
						frappe.delete_doc("File", ban, ignore_permissions=True)
						da_xoa += 1
				frappe.delete_doc("File", g.name, ignore_permissions=True)
				da_xoa += 1
				frappe.db.commit()
			except Exception:
				frappe.log_error(
					frappe.get_traceback(), "minvoice_tep: don tep %s" % g.name
				)
		return da_xoa
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_tep: nhip don PDF vo loi")
		return 0
