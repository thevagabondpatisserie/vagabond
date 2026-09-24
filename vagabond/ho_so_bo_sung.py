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


# --------------------------------------------------------------- phep thuan
# Tach ra de kiem thu duoc trong cong ma khong can Frappe, khong can site, va
# khong phai gia lap sys.modules. Ham nay CHI doc du lieu dong, tra ve cau loi
# hoac chuoi rong; moi viec nem loi va tra cuu chung tu de phan cham he lo.


def loi_giu_lien_ket(cu_dong, moi_dong, doi_ncc, hoa_don_goc_doi):
	"""Luat giu lien ket bo sung. cu_dong/moi_dong: {ten_dong: dict}.

	Tra ve (idx, cau_loi) cho loi dau tien, hoac (0, "") neu khong co loi.
	Ba luat: khong xoa dong da noi, khong ghi de lien ket, va dong da noi thi
	khong duoc doi NCC, doi hoa don goc hay bo co cho hoa don.
	"""
	for ten, d in cu_dong.items():
		cu_ma = (d.get("hoa_don_bo_sung") or "").strip()
		if not cu_ma:
			continue
		if ten not in moi_dong:
			return d.get("idx") or 0, "đã nối hóa đơn bổ sung, không xóa dòng"
		ma = (moi_dong[ten].get("hoa_don_bo_sung") or "").strip()
		if ma != cu_ma:
			return d.get("idx") or 0, "đã nối hóa đơn bổ sung, không ghi đè liên kết"
		if doi_ncc or hoa_don_goc_doi.get(ten) or not moi_dong[ten].get("cho_hoa_don"):
			return d.get("idx") or 0, "đã nối hóa đơn bổ sung, không đổi NCC, hóa đơn gốc hay bỏ cờ chờ hóa đơn"
	return 0, ""


# v526 (anh Việt chốt 23/09 và 24/09/2026) -------------------------------
# Chi từ TK công ty trước, hoá đơn về sau: tiền đã ghi Nợ chi phí qua bút
# toán của hồ sơ. Hoá đơn về thì NỐI làm chứng từ, hồ sơ chuyển sang chi phí
# hợp lệ tính thuế, và tờ hoá đơn mua đó KHÔNG được ghi sổ nữa (ghi là chi
# phí hai lần, công nợ treo mãi). Thuế GTGT đầu vào kế toán tự xử lý tay.

# Chỉ HUỶ mới làm dấu nối hết hiệu lực. Từ chối KHÔNG: hồ sơ bị trả lại vẫn
# gửi duyệt lại được (ho_so_tt.duyet "gui_fin" nhận cả Tu choi), nên nó phải
# giữ tờ đã nối, không thì tờ đó ghi sổ được hoặc nối sang hồ sơ khác trong
# lúc chờ, rồi hồ sơ cũ sống lại vẫn mang dấu nối: chi phí hai lần (Codex #368
# vòng 4). Muốn trả tờ ra thì huỷ hồ sơ.
TT_HET_HIEU_LUC = ("Huy",)
# Hồ sơ không nhận nối THÊM (kiem_bo_sung chặn): dùng để lọc danh sách khoản
# chờ trên Desk, khác với TT_HET_HIEU_LUC là bộ quyết định ai còn giữ tờ.
TT_KHONG_NOI_THEM = ("Huy", "Tu choi")


def _so(v):
	try:
		return int(v or 0)
	except (TypeError, ValueError):
		return 0


# Tờ hoá đơn nối vào khoản chi phải khớp tiền khoản đó trong ngưỡng này mới
# tính khoản là có hoá đơn thật (cùng ngưỡng lệch với màn Đối chiếu hoá đơn
# mua, doi_chieu_mua.NGUONG_LECH).
NGUONG_KHOP_TIEN = 1000.0


def _tien(v):
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0


def _dd(v):
	return "{:,.0f}".format(_tien(v)).replace(",", ".")


def lech_tien_hoa_don(dong, tong_hd, nguong=NGUONG_KHOP_TIEN):
	"""Các khoản đã nối mà tổng tiền tờ hoá đơn lệch số tiền khoản quá ngưỡng.
	THUẦN. tong_hd: {tờ hoá đơn: tổng tiền}; tờ không đọc được tổng coi là lệch."""
	ra = []
	for d in dong or []:
		ma = (d.get("hoa_don_bo_sung") or "").strip()
		if not ma:
			continue
		if ma not in (tong_hd or {}) or (tong_hd or {}).get(ma) is None:
			ra.append("khoản %s: không đọc được tổng tiền tờ %s" % (d.get("idx") or "?", ma))
			continue
		if abs(_tien(tong_hd[ma]) - _tien(d.get("so_tien"))) > nguong:
			ra.append("khoản %s: tờ %s %s đ, khoản chi %s đ" % (
				d.get("idx") or "?", ma, _dd(tong_hd[ma]), _dd(d.get("so_tien"))))
	return ra


def nen_hop_le(dong, tong_hd=None):
	"""Hồ sơ chuyển sang hợp lệ khi MỌI khoản đều là hoá đơn đến sau, đã nối
	đủ, và (Codex #368 vòng 7) tờ nối vào khớp tiền khoản trong ngưỡng. Khoản
	nào không chờ hoá đơn là khoản không hoá đơn thật: đổi cả hồ sơ sang hợp
	lệ là khai sai khi quyết toán. Nối tờ nhỏ hay không liên quan vào khoản lớn
	cũng vậy. THUẦN. tong_hd None: chỉ xét dấu nối (không dùng ở đường ghi)."""
	ds = list(dong or [])
	du = bool(ds) and all(
		_so(d.get("cho_hoa_don")) and (d.get("hoa_don_bo_sung") or "").strip() for d in ds)
	if not du or tong_hd is None:
		return du
	return not lech_tien_hoa_don(ds, tong_hd)


def loi_noi_hoa_don(docstatus_hd, ho_so_khac, da_huy=0, chi_nhap=True):
	"""Tờ hoá đơn mua nối vào khoản chờ hoá đơn được không. THUẦN.

	docstatus_hd: 0 nháp, 1 đã ghi sổ, 2 đã huỷ.
	ho_so_khac: tên hồ sơ còn hiệu lực khác đang giữ tờ này, rỗng nếu không.
	da_huy: vgb_huy của tờ. Huỷ mềm (chung_tu.danh_dau_huy) để tờ nháp ở
	docstatus 0, nên xét riêng (Codex #368 vòng 2).
	chi_nhap: chỉ hồ sơ Chi từ TK công ty mới buộc tờ còn nháp (chi phí đã
	ghi qua bút toán của hồ sơ). Hồ sơ trả NCC nối tờ ĐÃ ghi sổ là đúng luồng:
	tờ đó tạo công nợ mà hồ sơ trả (bench v526 bắt được, ca #263)."""
	if _so(docstatus_hd) == 2:
		return "đã huỷ"
	if _so(da_huy):
		return ("đã đánh dấu huỷ (bản nháp bỏ đi), không làm chứng từ cho khoản chi được. "
			"Chọn tờ hoá đơn còn hiệu lực")
	if chi_nhap and _so(docstatus_hd) == 1:
		return ("đã ghi sổ, tức chi phí đã vào sổ qua hoá đơn mua. Khoản chi này cũng đã "
			"ghi chi phí qua hồ sơ, nối vào là chi phí hai lần. Chỉ nối tờ còn nháp")
	if ho_so_khac:
		return "đã nối vào hồ sơ %s rồi" % ho_so_khac
	return ""



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
	# PDF phải giữ nguyên byte; Frappe mặc định thử giải mã thành chữ.
	noi = f.get_content(encodings=[])
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
	"""Document chung giu lien ket cung NCC/cong ty va khong cho ghi de.

	Phan luat nam o `loi_giu_lien_ket` (thuan, co ca kiem trong cong). O day chi
	dich cau loi va tra cuu chung tu that.
	"""
	cu = doc.get_doc_before_save()
	cu_dong = {d.name: {"idx": d.idx, "hoa_don_bo_sung": d.get("hoa_don_bo_sung"),
		"cho_hoa_don": cint(d.get("cho_hoa_don")), "hoa_don": d.get("hoa_don")}
		for d in (cu.dong if cu else [])}
	moi_dong = {d.name: {"idx": d.idx, "hoa_don_bo_sung": d.get("hoa_don_bo_sung"),
		"cho_hoa_don": cint(d.get("cho_hoa_don")), "hoa_don": d.get("hoa_don")}
		for d in (doc.dong or [])}
	doi_ncc = bool(cu and doc.nha_cung_cap != cu.nha_cung_cap)
	goc_doi = {t: (moi_dong[t].get("hoa_don") or "") != (cu_dong[t].get("hoa_don") or "")
		for t in cu_dong if t in moi_dong}
	idx, loi = loi_giu_lien_ket(cu_dong, moi_dong, doi_ncc, goc_doi)
	if loi:
		frappe.throw("Khoản %s %s. Nhờ kế toán kiểm tra." % (idx, loi))

	for d in (doc.dong or []):
		ma = (d.get("hoa_don_bo_sung") or "").strip()
		truoc = cu_dong.get(d.name)
		if not ma or (truoc and ma == (truoc.get("hoa_don_bo_sung") or "").strip()):
			continue
		from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD
		_kiem(VAI_FIN | VAI_GD, "nối hóa đơn đến sau")
		if not cint(d.get("cho_hoa_don")):
			frappe.throw("Khoản %s chưa đánh dấu hóa đơn đến sau." % d.idx)
		if doc.trang_thai in TT_KHONG_NOI_THEM:
			frappe.throw("Hồ sơ đã hủy hoặc từ chối, không bổ sung hóa đơn.")
		# v526 (Codex #368 finding 2): KHOÁ tờ hoá đơn trước, rồi mới xét trạng
		# thái và dấu nối, bằng câu đọc hiện hành. Ghi sổ (check_if_latest và
		# chan_ghi_so_hd_da_chi) giữ đúng khoá này, nên nối và ghi sổ cùng một
		# tờ không còn chạy song song. Không đọc docstatus từ get_doc: đó là ảnh
		# chụp REPEATABLE READ, không thấy lần ghi sổ vừa chốt.
		khoa = khoa_hoa_don(ma)
		hd = frappe.get_doc("Purchase Invoice", ma)
		docstatus, da_huy = khoa if khoa else (hd.docstatus, cint(hd.get("vgb_huy")))
		from vagabond.ho_so_tt import _cong_ty_chung_tu
		if docstatus == 2 or hd.supplier != doc.nha_cung_cap or hd.company != _cong_ty_chung_tu():
			frappe.throw("Hóa đơn bổ sung phải còn hiệu lực, đúng nhà cung cấp và công ty của hồ sơ.")
		if ma == d.hoa_don:
			frappe.throw("Hóa đơn này đã là chứng từ gốc của khoản chi, không cần nối bổ sung.")
		# v526: chỉ nối tờ còn nháp, và một tờ chỉ nằm ở một khoản còn hiệu lực.
		from vagabond.ho_so_tt import LOAI_TKCT
		chi_nhap = (getattr(doc, "loai", None) or "") == LOAI_TKCT
		loi = loi_noi_hoa_don(docstatus, ho_so_dang_giu(ma, bo_qua_dong=d.name, khoa=True), da_huy, chi_nhap)
		if loi:
			frappe.throw("Khoản %s: hoá đơn %s %s." % (d.idx, ma, loi))


def _co_dau_huy():
	return frappe.db.has_column("Purchase Invoice", "vgb_huy")


def _loai_tkct():
	from vagabond.ho_so_tt import LOAI_TKCT
	return LOAI_TKCT


def khoa_hoa_don(hoa_don):
	"""Khoá dòng tờ hoá đơn mua, trả (docstatus, vgb_huy) đọc HIỆN HÀNH, hoặc
	None nếu không có tờ.

	Một khoá chung cho mọi đường nối, ghi sổ và đánh dấu huỷ cùng một tờ (Codex
	#368 finding 2 và vòng 2). Giao dịch sau chờ giao dịch trước chốt rồi mới
	xét. Đánh dấu huỷ ghi bằng db.set_value lên đúng dòng này nên cũng xếp
	hàng sau khoá."""
	cot = ", ifnull(vgb_huy, 0)" if _co_dau_huy() else ", 0"
	r = frappe.db.sql("select docstatus" + cot + " from `tabPurchase Invoice` where name=%s for update", hoa_don)
	return (cint(r[0][0]), cint(r[0][1])) if r else None


def chan_huy_hd_da_noi(doc):
	"""chung_tu.danh_dau_huy gọi trước khi huỷ mềm một tờ hoá đơn mua nháp.

	Tờ đang là hoá đơn đến sau của một hồ sơ còn hiệu lực thì không huỷ: hồ sơ
	đó đang là chi phí hợp lệ tính thuế dựa trên chính tờ này (Codex #368
	vòng 2, chiều ngược lại của việc nối tờ đã huỷ)."""
	# Codex #368 vòng 3: danh_dau_huy xét docstatus trên doc nạp từ trước. Giao
	# dịch ghi sổ chen vào thì chỉ câu có khoá này thấy, nên xét ở đây, TRƯỚC
	# khi đọc dấu nối và trước khi gắn dấu huỷ.
	k = khoa_hoa_don(doc.name)
	if k and k[0] != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ (hoặc đã huỷ) ở nơi khác trong lúc đang mở, nên không "
			"đánh dấu huỷ kiểu phiếu nháp được. Tải lại tờ để xem trạng thái mới." % doc.name,
			title="Tờ đã đổi trạng thái")
	giu = ho_so_dang_giu(doc.name, khoa=True)
	if giu:
		frappe.throw(
			"Hoá đơn %s đang là hoá đơn đến sau (chứng từ) của hồ sơ %s. Huỷ tờ này thì "
			"hồ sơ mất chứng từ. Nhờ kế toán xử lý hồ sơ %s trước."
			% (doc.name, giu, giu), title="Tờ này đang làm chứng từ")


def ho_so_dang_giu(hoa_don, bo_qua_dong=None, khoa=False, chi_tkct=False):
	"""Hồ sơ còn hiệu lực đang nối tờ hoá đơn này làm hoá đơn đến sau.

	khoa=True: đọc hiện hành có khoá (for update). Dùng ở chỗ QUYẾT ĐỊNH (nối,
	ghi sổ), sau khi đã khoá tờ bằng khoa_hoa_don. Câu select thường chỉ đọc ảnh
	chụp lúc giao dịch mở, không thấy dấu nối hồ sơ khác vừa chốt: đã tái hiện
	trên MariaDB thật, hai hồ sơ cùng nối một tờ và tờ đã nối vẫn ghi sổ được.
	Chỗ chỉ hiển thị (khoan_cho_hoa_don) để khoa=False.
	chi_tkct=True: chỉ tính hồ sơ Chi từ TK công ty. Dùng cho luật "tờ đã nối
	không ghi sổ": hồ sơ trả NCC nối tờ làm chứng từ công nợ, tờ đó vẫn phải
	ghi sổ bình thường."""
	if not hoa_don:
		return ""
	ds = frappe.db.sql(
		"""select p.name from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where d.hoa_don_bo_sung = %s and d.name != %s
			and ifnull(p.trang_thai, '') not in %s
			and (%s = 0 or p.loai = %s)
		order by p.creation limit 1""" + (" for update" if khoa else ""),
		(hoa_don, bo_qua_dong or "", TT_HET_HIEU_LUC, 1 if chi_tkct else 0, _loai_tkct()))
	return ds[0][0] if ds else ""


TRUONG_KHOA_KHI_NOI = (("supplier", "nhà cung cấp"), ("company", "công ty"))


def giu_hd_da_noi(doc, method=None):
	"""validate Hoá đơn mua (v526, Codex #368 vòng 5): tờ đã nối làm hoá đơn
	đến sau vẫn là tờ NHÁP nên sửa được trên Desk. Đổi nhà cung cấp hay công
	ty sau khi nối là lọt luật "đúng NCC, đúng công ty" mà kiem_bo_sung xét lúc
	nối, trong khi hồ sơ vẫn tính là chi phí hợp lệ. Chỉ hỏi dấu nối khi một
	trong hai ô đó thật sự đổi, để lần lưu thường không tốn thêm truy vấn."""
	if cint(getattr(doc, "docstatus", 0)) != 0:
		return
	if doc.is_new():
		return
	cu = doc.get_doc_before_save()
	if not cu:
		return
	doi = [nhan for truong, nhan in TRUONG_KHOA_KHI_NOI
		if (doc.get(truong) or "") != (cu.get(truong) or "")]
	if not doi:
		return
	khoa_hoa_don(doc.name)
	giu = ho_so_dang_giu(doc.name, khoa=True)
	if giu:
		frappe.throw(
			"Hoá đơn %s đang là hoá đơn đến sau (chứng từ) của hồ sơ %s, nên không đổi %s được. "
			"Hồ sơ đã kiểm đúng nhà cung cấp và công ty lúc nối. Cần đổi thì huỷ hồ sơ %s trước."
			% (doc.name, giu, " và ".join(doi), giu), title="Tờ này đang làm chứng từ")


def chan_ghi_so_hd_da_chi(doc, method=None):
	"""before_submit Hoá đơn mua (v526): tờ đã nối làm hoá đơn đến sau của một
	hồ sơ chi từ TK công ty thì không ghi sổ. Tiền và chi phí đã vào sổ qua
	bút toán của hồ sơ; ghi thêm tờ này là chi phí hai lần và một khoản công
	nợ không bao giờ trả. Mọi đường ghi sổ (Desk, app, API) đều đi qua đây."""
	# Submit đã giữ khoá tờ từ check_if_latest; khoá lại ở đây cho rõ và cho
	# mọi đường gọi, rồi đọc dấu nối hiện hành (Codex #368 finding 2).
	khoa_hoa_don(doc.name)
	giu = ho_so_dang_giu(doc.name, khoa=True, chi_tkct=True)
	if giu:
		frappe.throw(
			"Hoá đơn %s đã nối làm hoá đơn đến sau của hồ sơ %s: khoản chi đã ghi chi phí "
			"qua hồ sơ đó, nên tờ này chỉ là chứng từ, không ghi sổ. Thuế GTGT đầu vào "
			"(nếu có) kế toán xử lý bằng bút toán riêng." % (doc.name, giu),
			title="Tờ này không ghi sổ")


@frappe.whitelist()
def danh_sach_hoa_don(name, tu_khoa=""):
	from vagabond.ho_so_tt import _kiem, VAI_LAP, VAI_FIN, VAI_GD, _cong_ty_chung_tu
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "tìm hóa đơn bổ sung")
	d = frappe.get_doc("Vagabond Ho So TT", name)
	# v526: chỉ tờ còn nháp. Tờ đã ghi sổ thì chi phí đã vào sổ qua hoá đơn.
	from vagabond.ho_so_tt import LOAI_TKCT
	# Chi từ TK công ty: chỉ tờ còn nháp (chi phí đã ghi qua hồ sơ). Hồ sơ trả
	# NCC: tờ đã ghi sổ là chứng từ công nợ đúng luồng, giữ như trước v526.
	loc = {"supplier": d.nha_cung_cap, "company": _cong_ty_chung_tu(),
		"docstatus": 0 if (getattr(d, "loai", None) or "") == LOAI_TKCT else ["<", 2]}
	if _co_dau_huy():
		loc["vgb_huy"] = 0   # tờ nháp đã đánh dấu huỷ không làm chứng từ được
	return frappe.get_list("Purchase Invoice", filters=loc,
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
	# KHONG tu bat co cho_hoa_don o day. Bat ho la vo hieu hoa chinh hang rao
	# "chua danh dau hoa don den sau" trong kiem_bo_sung: bat cu khoan nao cung
	# noi duoc hoa don bo sung. Co phai do nguoi lap ho so danh dau tu dau.
	if not cint(r.get("cho_hoa_don")):
		frappe.throw("Khoản %s chưa đánh dấu Hóa đơn đến sau. Mở hồ sơ đánh dấu khoản đó rồi nối hóa đơn." % dong)
	r.hoa_don_bo_sung = hoa_don
	# v526 (anh Việt 23/09/2026): nối đủ thì hồ sơ thành chi phí hợp lệ tính
	# thuế. Còn khoản không chờ hoá đơn thì giữ nguyên, đó là khoản không
	# hoá đơn thật.
	from vagabond.ho_so_tt import CP_HOP_LE, LOAI_TKCT
	la_tkct = (getattr(d, "loai", None) or "") == LOAI_TKCT
	lech = []
	doi_hop_le = False
	if la_tkct and nen_hop_le(d.dong):
		# Codex #368 vòng 7: so tiền từng tờ với khoản của nó trước khi đổi cả
		# hồ sơ sang hợp lệ. Lệch thì vẫn nối (tờ là chứng từ thật của NCC),
		# nhưng hồ sơ giữ loại cũ và báo rõ khoản nào lệch.
		tong_hd = {}
		for x in d.dong:
			ma = (x.get("hoa_don_bo_sung") or "").strip()
			if ma:
				tong_hd[ma] = frappe.db.get_value("Purchase Invoice", ma, "grand_total")
		lech = lech_tien_hoa_don(d.dong, tong_hd)
		doi_hop_le = not lech and (getattr(d, "loai_cp_thue", None) or "") != CP_HOP_LE
	if doi_hop_le:
		d.loai_cp_thue = CP_HOP_LE
	# Khong goi kiem_bo_sung o day: luc nay get_doc_before_save() con None nen
	# hang rao giu lien ket khong thay ban cu, chay cho co. Controller goi no
	# trong validate voi ban cu that, do moi la cua duy nhat.
	d.save(ignore_permissions=True)
	d.add_comment("Comment", "Nối hóa đơn bổ sung %s vào khoản %s. Không phát sinh bút toán thanh toán.%s" % (
		hoa_don, dong, " Đủ hoá đơn cho mọi khoản, hồ sơ chuyển sang chi phí hợp lệ tính thuế." if doi_hop_le else (
			" Chưa chuyển hợp lệ tính thuế vì tiền lệch: " + "; ".join(lech) + "." if lech else "")))
	return {"ok": 1, "hop_le": 1 if doi_hop_le else 0, "lech": lech}


@frappe.whitelist()
def khoan_cho_hoa_don(hoa_don):
	"""Màn Hoá đơn mua bên Desk (v526): những khoản chi từ TK công ty đang chờ
	hoá đơn của đúng nhà cung cấp này, để nối ngay từ tờ hoá đơn."""
	from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD, _cong_ty_chung_tu
	_kiem(VAI_FIN | VAI_GD, "nối hóa đơn đến sau")
	hd = frappe.db.get_value("Purchase Invoice", hoa_don,
		["name", "supplier", "company", "docstatus"] + (["vgb_huy"] if _co_dau_huy() else []), as_dict=True)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % hoa_don)
	giu = ho_so_dang_giu(hoa_don, chi_tkct=True)
	if giu or hd.docstatus != 0 or cint(hd.get("vgb_huy")) or hd.company != _cong_ty_chung_tu():
		return {"da_noi": giu, "khoan": []}
	ds = frappe.db.sql(
		"""select p.name as ho_so, p.ngay, p.trang_thai, d.idx as dong, d.noi_dung,
			d.so_tien, d.ngay_hd
		from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where p.nha_cung_cap = %s and d.cho_hoa_don = 1 and p.loai = %s
			and ifnull(d.hoa_don_bo_sung, '') = ''
			and ifnull(p.trang_thai, '') not in %s
		order by p.ngay desc, d.idx asc limit 50""",
		(hd.supplier, _loai_tkct(), TT_KHONG_NOI_THEM), as_dict=True)
	return {"da_noi": "", "khoan": [dict(r, so_tien=float(r.so_tien or 0),
		ngay=str(r.ngay or ""), ngay_hd=str(r.ngay_hd or "")) for r in ds]}
