"""Hóa đơn đến sau khi chi tiền và nén bản thể hiện cho hồ sơ APP #247.

Liên kết bổ sung chỉ chứng minh khoản chi. Không thay hoa_don gốc vì trường
đó quyết định Payment Entry; thay sau ghi sổ có thể làm thanh toán hai lần.
"""

import io


def nen_pdf(noi):
	"""Nén lossless, giữ bản gốc nếu có chữ ký hoặc kết quả không nhỏ hơn."""
	from pypdf import PdfReader, PdfWriter

	if len(noi) > 12 * 1024 * 1024:
		raise ValueError("PDF vượt 12 MB. Chọn bản thể hiện nhỏ hơn rồi tải lại.")
	r = PdfReader(io.BytesIO(noi))
	if r.is_encrypted:
		raise ValueError("PDF có mật khẩu. Xuất bản thể hiện không khóa rồi tải lại.")
	if len(r.pages) > 100:
		raise ValueError("PDF vượt 100 trang. Tách theo hóa đơn rồi tải lại.")
	if any(f.get('/FT') == '/Sig' for f in (r.get_fields() or {}).values()):
		return noi
	w = PdfWriter()
	w.clone_document_from_reader(r)
	for p in w.pages:
		p.compress_content_streams()
	bo = io.BytesIO()
	w.write(bo)
	return bo.getvalue() if bo.tell() < len(noi) else noi


import frappe
from frappe.utils import cint


@frappe.whitelist()
def nen_tep(tep):
	from vagabond.ho_so_tt import _kiem, VAI_LAP, VAI_FIN, VAI_GD
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "tải bản thể hiện hóa đơn")
	f = frappe.get_doc("File", tep)
	# Chỉ xử lý upload riêng của người gọi, chưa gắn vào chứng từ nào.
	if f.owner != frappe.session.user or f.attached_to_name or not f.is_private:
		frappe.throw("Chỉ nén tệp riêng vừa tải lên của anh chị. Vui lòng chọn lại tệp.")
	if not (f.file_name or "").lower().endswith(".pdf"):
		frappe.throw("Bản thể hiện phải là tệp PDF.")
	noi = f.get_content()
	try:
		gon = nen_pdf(noi)
	except Exception as e:
		frappe.throw("Không đọc được PDF. Chọn bản thể hiện hợp lệ rồi tải lại. %s" % str(e))
	if gon != noi:
		from frappe.utils.file_manager import save_file
		# Giữ upload gốc; bản nén là File riêng, không ghi đè chứng từ đã ký.
		f = save_file(f.file_name, gon, None, None, is_private=1)
	return {"ma": f.name, "ten": f.file_name, "url": f.file_url}


def kiem_bo_sung(doc):
	"""Document chung giữ liên kết cùng NCC/công ty và không cho ghi đè."""
	cu = doc.get_doc_before_save()
	cu_dong = {d.name: d for d in (cu.dong if cu else [])}
	moi_dong = {d.name: d for d in (doc.dong or [])}
	for ten, d in cu_dong.items():
		if d.get("hoa_don_bo_sung") and (ten not in moi_dong or
			moi_dong[ten].get("hoa_don_bo_sung") != d.get("hoa_don_bo_sung")):
			frappe.throw("Khoản %s đã nối hóa đơn bổ sung. Không xóa dòng hoặc ghi đè liên kết." % d.idx)
	for d in (doc.dong or []):
		ma = d.get("hoa_don_bo_sung")
		truoc = cu_dong.get(d.name)
		if truoc and truoc.get("hoa_don_bo_sung") and ma != truoc.get("hoa_don_bo_sung"):
			frappe.throw("Khoản %s đã nối hóa đơn bổ sung. Nhờ kế toán kiểm tra, không ghi đè liên kết." % d.idx)
		if not ma:
			continue
		if truoc and ma == truoc.get("hoa_don_bo_sung"):
			if doc.nha_cung_cap != cu.nha_cung_cap or (d.hoa_don or "") != (truoc.hoa_don or "") or not cint(d.get("cho_hoa_don")):
				frappe.throw("Khoản %s đã nối hóa đơn bổ sung. Không đổi NCC, hóa đơn gốc hoặc bỏ cờ chờ hóa đơn." % d.idx)
			continue
		from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD
		_kiem(VAI_FIN | VAI_GD, "nối hóa đơn đến sau")
		if not cint(d.get("cho_hoa_don")):
			frappe.throw("Khoản %s chưa đánh dấu hóa đơn đến sau." % d.idx)
		if doc.trang_thai in ("Huy", "Tu choi"):
			frappe.throw("Hồ sơ đã hủy hoặc từ chối, không bổ sung hóa đơn.")
		hd = frappe.get_doc("Purchase Invoice", ma)
		from vagabond.ho_so_tt import _cong_ty_chung_tu
		if hd.docstatus == 2 or hd.supplier != doc.nha_cung_cap or hd.company != _cong_ty_chung_tu():
			frappe.throw("Hóa đơn bổ sung phải còn hiệu lực, đúng nhà cung cấp và công ty của hồ sơ.")
		if ma == d.hoa_don:
			frappe.throw("Hóa đơn này đã là chứng từ gốc của khoản chi, không cần nối bổ sung.")


@frappe.whitelist()
def danh_sach_hoa_don(name, tu_khoa=""):
	from vagabond.ho_so_tt import _kiem, VAI_LAP, VAI_FIN, VAI_GD, _cong_ty_chung_tu
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "tìm hóa đơn bổ sung")
	d = frappe.get_doc("Vagabond Ho So TT", name)
	return frappe.get_list("Purchase Invoice", filters={"supplier": d.nha_cung_cap,
		"company": _cong_ty_chung_tu(), "docstatus": ["<", 2]},
		or_filters={"name": ["like", "%" + tu_khoa + "%"], "bill_no": ["like", "%" + tu_khoa + "%"]},
		fields=["name", "bill_no", "bill_date", "grand_total", "docstatus"],
		order_by="posting_date desc", limit_page_length=0)


@frappe.whitelist()
def noi_hoa_don(name, dong, hoa_don):
	from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD
	_kiem(VAI_FIN | VAI_GD, "nối hóa đơn đến sau")
	frappe.db.sql("select name from `tabVagabond Ho So TT` where name=%s for update", name)
	d = frappe.get_doc("Vagabond Ho So TT", name)
	if cint(dong) < 1 or cint(dong) > len(d.dong):
		frappe.throw("Không tìm thấy khoản chi. Tải lại hồ sơ rồi chọn lại.")
	r = d.dong[cint(dong) - 1]
	r.cho_hoa_don = 1
	r.hoa_don_bo_sung = hoa_don
	kiem_bo_sung(d)
	d.save(ignore_permissions=True)
	d.add_comment("Comment", "Nối hóa đơn bổ sung %s vào khoản %s. Không phát sinh bút toán thanh toán." % (hoa_don, dong))
	return {"ok": 1}
