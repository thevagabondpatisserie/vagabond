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


def loi_trung_trong_ho_so(moi_dong, cu_dong):
	"""Một tờ hoá đơn chỉ làm chứng từ cho MỘT khoản, kể cả trong cùng hồ sơ. THUẦN.

	Codex #368 vòng 12: ho_so_dang_giu chỉ đọc dòng ĐÃ lưu, nên một lần lưu gán
	cùng một tờ chưa dùng cho hai khoản mới thì mỗi khoản đều không thấy khoản
	kia, rồi nen_hop_le coi một tờ là chứng từ cho cả hai. Xét ngay trên bản
	đang lưu. Tờ cũng không được vừa là hoá đơn gốc của khoản này vừa là hoá
	đơn bổ sung của khoản khác.
	moi_dong/cu_dong: {ten_dong: {"idx", "hoa_don_bo_sung", "hoa_don"}}.
	Chỉ báo khi xung đột có ít nhất một VẾ mới hoặc đổi ở lần lưu này (vế bổ
	sung hoặc vế hoá đơn gốc, vòng 13: chỉ xét vế bổ sung thì thêm hoá đơn gốc
	trùng một tờ đã nối sẵn là lọt), để hồ sơ cũ nếu lỡ có trùng không bị khoá
	cứng ở mọi lần lưu."""
	cu_dong = cu_dong or {}

	def _v(r, k):
		return ((r or {}).get(k) or "").strip()

	def doi(t, k):
		# Dòng mới (không có ở bản cũ) thì mọi vế khác rỗng đều là mới.
		return _v(moi_dong[t], k) != _v(cu_dong.get(t), k)

	goc = {}
	for t, r in (moi_dong or {}).items():
		if _v(r, "hoa_don"):
			goc.setdefault(_v(r, "hoa_don"), []).append(t)
	nhom = {}
	for t, r in (moi_dong or {}).items():
		if _v(r, "hoa_don_bo_sung"):
			nhom.setdefault(_v(r, "hoa_don_bo_sung"), []).append(t)
	so = lambda ts: ", ".join(str(i) for i in sorted(moi_dong[t].get("idx") or 0 for t in ts))
	for ma in sorted(nhom):
		cac = nhom[ma]
		if len(cac) > 1 and any(doi(t, "hoa_don_bo_sung") for t in cac):
			return "Hoá đơn %s đang gán cho nhiều khoản (%s) trong cùng hồ sơ. Một tờ chỉ làm chứng từ cho một khoản." % (
				ma, so(cac))
		khac = [t for t in goc.get(ma, []) if t not in cac]
		if khac and (any(doi(t, "hoa_don_bo_sung") for t in cac) or any(doi(t, "hoa_don") for t in khac)):
			return "Hoá đơn %s vừa là hoá đơn gốc của khoản %s vừa nối bổ sung cho khoản %s. Một tờ chỉ làm chứng từ cho một khoản." % (
				ma, so(khac), so(cac))
	return ""


def loi_mo_lai_huy(tt_cu, tt_moi, cu_dong):
	"""Hồ sơ đã Huỷ đang mang dấu nối hoá đơn đến sau thì không mở lại. THUẦN.

	Chỉ Huỷ làm dấu nối hết hiệu lực (TT_HET_HIEU_LUC), nên sau khi huỷ, tờ đó
	ghi sổ hoặc nối sang hồ sơ khác là đúng luật. trang_thai lại sửa được trên
	Desk/API: đưa hồ sơ huỷ về Nháp là dấu nối sống lại trên một tờ có thể đã
	ghi sổ hoặc đang ở hồ sơ khác, chi phí hai lần. Tự bắt khi làm vòng 10."""
	if tt_cu not in TT_HET_HIEU_LUC or tt_moi in TT_HET_HIEU_LUC:
		return ""
	for r in (cu_dong or {}).values():
		ma = (r.get("hoa_don_bo_sung") or "").strip()
		if ma:
			return ("Hồ sơ đã huỷ, khoản %s từng nối hoá đơn %s nên không mở lại được: huỷ là đã trả tờ đó ra, "
				"tờ có thể đã ghi sổ hoặc nối sang hồ sơ khác. Lập hồ sơ mới nếu cần." % (r.get("idx"), ma))
	return ""


def loi_doi_loai(loai_cu, loai_moi, cu_dong, mac_dinh="NCC"):
	"""Đổi loại hồ sơ khi hồ sơ đang nối hoá đơn đến sau thì không được. THUẦN.

	Codex #368 vòng 10: mọi luật hoá đơn đến sau (chỉ nối tờ nháp, chặn ghi
	sổ tờ đã nối, soát số tiền) xét theo loại hồ sơ. Loại lại là ô sửa được
	trên Desk/API, nên đổi loại cùng lần lưu là thoát luật, rồi tờ nháp ghi sổ
	được, chi phí vào sổ hai lần. Giữ MỘT bất biến: đang nối thì loại đứng yên,
	mọi luật theo loại đọc ra cùng một giá trị với lúc nối.
	Loại chỉ đặt lúc lập hồ sơ (ho_so_tt), không đường nghiệp vụ nào đổi sau."""
	cu = (loai_cu or "").strip() or mac_dinh
	moi = (loai_moi or "").strip() or mac_dinh
	if cu == moi:
		return ""
	for r in (cu_dong or {}).values():
		ma = (r.get("hoa_don_bo_sung") or "").strip()
		if ma:
			return ("Hồ sơ đang nối hoá đơn %s ở khoản %s nên không đổi loại hồ sơ (%s sang %s) được. "
				"Loại hồ sơ quyết định tờ đó còn ghi sổ được hay không. Lập sai loại thì huỷ hồ sơ rồi lập lại."
				% (ma, r.get("idx"), cu, moi))
	return ""



def loi_danh_dau_bu(loai, trang_thai, dong, loai_tkct="TK cong ty"):
	"""Khoản này có được đánh dấu BÙ "hoá đơn đến sau" không. THUẦN.

	v528 (anh Việt 25/09/2026, hồ sơ APP.26.09.010 Adecco): hồ sơ lập trước
	v526 chưa có chip "Hoá đơn đến sau", nên khoản chi trước không bao giờ nối
	được hoá đơn về sau. Cho FIN hoặc giám đốc đánh dấu bù, đúng một cửa, chỉ
	khi khoản đó thật sự đang chờ hoá đơn: chi từ TK công ty (tiền đã ghi Nợ
	chi phí qua bút toán hồ sơ), chưa có hoá đơn gốc, chưa nối gì.
	Trả câu lỗi, rỗng là được.
	"""
	dong = dong or {}
	if (loai or "") != loai_tkct:
		return "chỉ khoản chi từ TK công ty mới có hoá đơn đến sau"
	if (trang_thai or "") in TT_KHONG_NOI_THEM:
		return "hồ sơ đã huỷ hoặc bị từ chối"
	if (dong.get("hoa_don") or "").strip():
		return "khoản đã có hoá đơn gốc"
	if (dong.get("hoa_don_bo_sung") or "").strip():
		return "khoản đã nối hoá đơn bổ sung"
	if _so(dong.get("cho_hoa_don")):
		return "khoản đã đánh dấu hoá đơn đến sau rồi"
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
		"cho_hoa_don": cint(d.get("cho_hoa_don")), "hoa_don": d.get("hoa_don"),
		"so_tien": d.get("so_tien")}
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
	# v530: bảng tờ nối mức hồ sơ chỉ đổi qua noi_nhieu / go_noi (cờ), và hồ
	# sơ đang có bút toán bù trừ thì không rời Đã thanh toán.
	from vagabond.hoa_don_sau import loi_sua_hd_sau, loi_bo_thanh_toan
	cu_hd = [_dict_dong(r) for r in (getattr(cu, "hd_sau", None) or [])]
	moi_hd = [_dict_dong(r) for r in (getattr(doc, "hd_sau", None) or [])]
	cho_phep = bool(getattr(getattr(doc, "flags", None), "vgb_noi_hd_sau", False))
	loi = loi_sua_hd_sau(cu_hd, moi_hd, cho_phep)
	if loi:
		frappe.throw(loi, title="Hoá đơn đến sau")
	if cu:
		loi = loi_bo_thanh_toan(getattr(cu, "trang_thai", None), getattr(doc, "trang_thai", None), cu_hd)
		if loi:
			frappe.throw(loi, title="Hồ sơ đang có bút toán bù trừ")
	if cu:
		from vagabond.ho_so_tt import LOAI_NCC
		ca_hai = dict(cu_dong)
		for i, r in enumerate(cu_hd):
			ca_hai["__hd_sau_%d" % i] = {"idx": "nối ở mức hồ sơ", "hoa_don_bo_sung": r.get("hoa_don")}
		loi = (loi_mo_lai_huy(getattr(cu, "trang_thai", None), getattr(doc, "trang_thai", None), ca_hai)
			or loi_doi_loai(getattr(cu, "loai", None), getattr(doc, "loai", None), ca_hai, LOAI_NCC))
		if loi:
			frappe.throw(loi, title="Hồ sơ đang có chứng từ")
	# Khoá theo từng dòng thật, không theo d.name: dòng mới chưa có tên thì
	# nhiều dòng trùng khoá None sẽ gộp làm một và lọt trùng.
	loi = loi_trung_trong_ho_so({(d.name or "__moi_%d" % i): {"idx": d.idx,
		"hoa_don_bo_sung": d.get("hoa_don_bo_sung"), "hoa_don": d.get("hoa_don")}
		for i, d in enumerate(doc.dong or [])}, cu_dong)
	if loi:
		frappe.throw(loi, title="Hoá đơn trùng khoản")
	_giu_tien_khoan_da_noi(doc, cu_dong)

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


def _dict_dong(r):
	if hasattr(r, "as_dict"):
		return r.as_dict()
	return dict(r) if isinstance(r, dict) else dict(vars(r))


def _bo_trung(ds, khoa="name"):
	thay, ra = set(), []
	for r in ds or []:
		k = r.get(khoa) if hasattr(r, "get") else r[khoa]
		if k in thay:
			continue
		thay.add(k)
		ra.append(r)
	return ra


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
	if ds:
		return ds[0][0]
	# v530: nguồn thứ hai, tờ nối ở mức hồ sơ. MỌI luật "ai đang giữ tờ này"
	# (chặn ghi sổ, chặn huỷ mềm, chặn đổi NCC, chặn nối trùng) đều đi qua
	# hàm này, nên thêm nguồn ở đây là đủ cho cả họ (điều 18).
	ds = _giu_hd_sau(hoa_don, khoa=khoa, chi_tkct=chi_tkct)
	return ds[0]["ho_so"] if ds else ""


def _co_hd_sau():
	"""Bảng tờ nối mức hồ sơ đã dựng chưa (trước migrate v530 thì chưa)."""
	try:
		return bool(frappe.db.table_exists("Vagabond Ho So TT HD Sau"))
	except Exception:
		return False


def _giu_hd_sau(hoa_don, khoa=False, chi_tkct=False, bo_qua_ho_so=""):
	"""Các dòng nối mức hồ sơ (v530) còn hiệu lực đang giữ tờ này."""
	if not hoa_don or not _co_hd_sau():
		return []
	return frappe.db.sql(
		"""select p.name as ho_so, p.loai as loai, h.tong_hd as tong_hd, h.da_ghi_so as da_ghi_so
		from `tabVagabond Ho So TT HD Sau` h
		inner join `tabVagabond Ho So TT` p on p.name = h.parent
		where h.hoa_don = %s and p.name != %s
			and ifnull(p.trang_thai, '') not in %s
			and (%s = 0 or p.loai = %s)
		order by p.creation limit 1""" + (" for update" if khoa else ""),
		(hoa_don, bo_qua_ho_so or "", TT_HET_HIEU_LUC, 1 if chi_tkct else 0, _loai_tkct()), as_dict=True) or []


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
	# Codex #368 vòng 8: sửa dòng làm đổi TỔNG TIỀN cũng phải soát lại, vì hồ
	# sơ TK công ty chỉ hợp lệ khi tờ khớp tiền khoản (vòng 7).
	doi_tien = abs(_tien(doc.get("grand_total")) - _tien(cu.get("grand_total"))) > 0.005
	if not doi and not doi_tien:
		return
	khoa_hoa_don(doc.name)
	if doi:
		giu = ho_so_dang_giu(doc.name, khoa=True)
		if giu:
			frappe.throw(
				"Hoá đơn %s đang là hoá đơn đến sau (chứng từ) của hồ sơ %s, nên không đổi %s được. "
				"Hồ sơ đã kiểm đúng nhà cung cấp và công ty lúc nối. Cần đổi thì huỷ hồ sơ %s trước."
				% (doc.name, giu, " và ".join(doi), giu), title="Tờ này đang làm chứng từ")
	if doi_tien:
		# v530: tờ nháp nối ở mức hồ sơ thì so với tổng tờ lúc nối.
		for g in _giu_hd_sau(doc.name, khoa=True):
			if abs(_tien(doc.get("grand_total")) - _tien(g["tong_hd"])) > NGUONG_KHOP_TIEN:
				frappe.throw(
					"Hoá đơn %s đang là hoá đơn đến sau của hồ sơ %s với tổng %s đ. Tổng mới %s đ lệch quá "
					"%s đ, hồ sơ sẽ không còn khớp chứng từ. Gỡ nối trên hồ sơ trước rồi mới sửa tờ."
					% (doc.name, g["ho_so"], _dd(g["tong_hd"]), _dd(doc.get("grand_total")), _dd(NGUONG_KHOP_TIEN)),
					title="Tờ này đang làm chứng từ")
		k = khoan_dang_giu(doc.name)
		if k and k[1] == _loai_tkct() and abs(_tien(doc.get("grand_total")) - _tien(k[2])) > NGUONG_KHOP_TIEN:
			frappe.throw(
				"Hoá đơn %s đang là chứng từ của khoản %s đ ở hồ sơ %s. Tổng mới %s đ lệch quá %s đ, "
				"hồ sơ sẽ không còn khớp chứng từ. Kiểm lại dòng hoá đơn, hoặc huỷ hồ sơ %s trước nếu "
				"thật sự nối nhầm tờ." % (doc.name, _dd(k[2]), k[0], _dd(doc.get("grand_total")),
					_dd(NGUONG_KHOP_TIEN), k[0]), title="Tờ này đang làm chứng từ")


def _giu_tien_khoan_da_noi(doc, cu_dong):
	"""Codex #368 vòng 9, chiều ngược của giu_hd_da_noi: khoản đã nối tờ ở hồ sơ
	TK công ty mà sửa số tiền thì soát lại với tổng tờ (khoá tờ, đọc hiện
	hành). Lệch quá NGUONG_KHOP_TIEN thì chặn. Chỉ hỏi khi số tiền thật sự đổi."""
	if (getattr(doc, "loai", None) or "") != _loai_tkct():
		return
	for d in (doc.dong or []):
		ma = (d.get("hoa_don_bo_sung") or "").strip()
		truoc = cu_dong.get(d.name)
		if not ma or not truoc or (truoc.get("hoa_don_bo_sung") or "").strip() != ma:
			continue
		if abs(_tien(d.get("so_tien")) - _tien(truoc.get("so_tien"))) <= 0.005:
			continue
		tong = tong_hoa_don_khoa(ma)
		if tong is None or abs(_tien(tong) - _tien(d.get("so_tien"))) > NGUONG_KHOP_TIEN:
			frappe.throw(
				"Khoản %s đang nối hoá đơn %s (%s đ). Số tiền mới %s đ lệch quá %s đ nên hồ sơ không "
				"còn khớp chứng từ. Kiểm lại số tiền khoản, hoặc huỷ hồ sơ rồi lập lại nếu nối nhầm tờ."
				% (d.idx, ma, _dd(tong), _dd(d.get("so_tien")), _dd(NGUONG_KHOP_TIEN)),
				title="Khoản này đang có chứng từ")


def tong_hoa_don_khoa(hoa_don):
	"""Tổng tiền tờ hoá đơn mua đọc HIỆN HÀNH có khoá (for update), None nếu
	không có tờ. Nguồn duy nhất cho mọi lần so tiền tờ với khoản (Codex #368
	vòng 11): get_value thường đọc ảnh chụp REPEATABLE READ, không thấy lần sửa
	tổng tiền vừa chốt ở giao dịch khác, rồi quyết hợp lệ theo số cũ."""
	r = frappe.db.sql("select grand_total from `tabPurchase Invoice` where name=%s for update", hoa_don)
	return r[0][0] if r else None


def khoan_dang_giu(hoa_don):
	"""(hồ sơ, loại hồ sơ, số tiền khoản) còn hiệu lực đang nối tờ này, đọc có
	khoá. Gọi sau khoa_hoa_don."""
	ds = frappe.db.sql(
		"""select p.name, p.loai, d.so_tien from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where d.hoa_don_bo_sung = %s and ifnull(p.trang_thai, '') not in %s
		order by p.creation limit 1 for update""",
		(hoa_don, TT_HET_HIEU_LUC))
	return tuple(ds[0]) if ds else None


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
	ds = frappe.get_list("Purchase Invoice", filters=loc,
		or_filters={"name": ["like", "%" + tu_khoa + "%"], "bill_no": ["like", "%" + tu_khoa + "%"]},
		fields=["name", "bill_no", "bill_date", "grand_total", "docstatus"],
		order_by="posting_date desc", limit_page_length=0)
	# v530: get_list kèm luật quyền có thể trả một tờ hai lần (ảnh chị Dung
	# 25/09: 2830, 2171, 1407 mỗi tờ hiện hai dòng). Giữ lần đầu.
	return _bo_trung(ds)


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
		# Vòng 11: đọc tổng từng tờ qua tong_hoa_don_khoa (khoá tờ, đọc hiện
		# hành), không get_value. Khoá theo thứ tự tên để hai lần nối không
		# khoá chéo nhau.
		tong_hd = {}
		for ma in sorted({(x.get("hoa_don_bo_sung") or "").strip() for x in d.dong} - {""}):
			tong_hd[ma] = tong_hoa_don_khoa(ma)
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


@frappe.whitelist(methods=["POST"])
def danh_dau_cho_hoa_don(name, dong):
	"""Đánh dấu bù một khoản là "hoá đơn đến sau" (v528). FIN hoặc giám đốc.

	Chỉ bật cờ trên khoản; không tạo bút toán, không đổi tiền, không nối tờ
	nào. Nối vẫn đi đúng cửa noi_hoa_don như hồ sơ mới. Ghi nhật ký người bấm.
	"""
	from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD, LOAI_TKCT
	_kiem(VAI_FIN | VAI_GD, "đánh dấu hoá đơn đến sau")
	frappe.db.sql("select name from `tabVagabond Ho So TT` where name=%s for update", name)
	d = frappe.get_doc("Vagabond Ho So TT", name)
	i = cint(dong)
	if i < 1 or i > len(d.dong):
		frappe.throw("Không tìm thấy khoản chi. Tải lại hồ sơ rồi chọn lại.")
	r = d.dong[i - 1]
	loi = loi_danh_dau_bu(getattr(d, "loai", None), getattr(d, "trang_thai", None), r.as_dict(), LOAI_TKCT)
	if loi:
		frappe.throw("Khoản %s: %s." % (i, loi))
	r.cho_hoa_don = 1
	d.save(ignore_permissions=True)
	d.add_comment("Comment", "Đánh dấu bù khoản %s là hoá đơn đến sau. Tiền đã ghi qua bút toán của hồ sơ; "
		"hoá đơn về thì nối vào khoản này. Người đánh dấu: %s." % (i, frappe.session.user))
	return {"ok": 1, "dong": i}



# ================================================================ v530
# Nối hoá đơn đến sau NHIỀU-NHIỀU ở mức hồ sơ (chị Dung, anh Việt 25/09/2026).
# Phép thuần và lý do nằm ở vagabond/hoa_don_sau.py. Ở đây chỉ tra cứu, khoá
# và ghi. Đường cũ một tờ một khoản (noi_hoa_don) giữ nguyên cho màn Desk.

def _nhom_ncc(ncc):
	"""(danh sách nhà cung cấp cùng MST gốc với `ncc`, MST gốc). Không có MST
	thì chỉ chính nó."""
	from vagabond.hoa_don_sau import mst_goc
	goc = mst_goc(frappe.db.get_value("Supplier", ncc, "tax_id"))
	if not goc:
		return [ncc], ""
	ds = [r[0] for r in frappe.db.sql(
		"select name, tax_id from `tabSupplier` where tax_id like %s", (goc + "%",))
		if mst_goc(r[1]) == goc]
	if ncc not in ds:
		ds.insert(0, ncc)
	return ds, goc


def _giu_boi_ho_so(ten_hd, tru=""):
	"""{tờ: hồ sơ khác còn hiệu lực đang giữ} cho cả hai nguồn, đọc thường
	(chỉ để HIỂN THỊ; chỗ quyết định đọc lại có khoá qua ho_so_dang_giu)."""
	if not ten_hd:
		return {}
	ra = {}
	for ten, ho_so in frappe.db.sql(
		"""select d.hoa_don_bo_sung, p.name from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where d.hoa_don_bo_sung in %s and p.name != %s and ifnull(p.trang_thai, '') not in %s""",
		(tuple(ten_hd), tru, TT_HET_HIEU_LUC)):
		ra.setdefault(ten, ho_so)
	if _co_hd_sau():
		for ten, ho_so in frappe.db.sql(
			"""select h.hoa_don, p.name from `tabVagabond Ho So TT HD Sau` h
			inner join `tabVagabond Ho So TT` p on p.name = h.parent
			where h.hoa_don in %s and p.name != %s and ifnull(p.trang_thai, '') not in %s""",
			(tuple(ten_hd), tru, TT_HET_HIEU_LUC)):
			ra.setdefault(ten, ho_so)
	return ra


def _lien_ket_cua(d):
	return [_dict_dong(r) for r in (getattr(d, "hd_sau", None) or [])]


def _khoan_cua(d):
	return [_dict_dong(r) for r in (d.dong or [])]


def phu_cua(d):
	"""Mức phủ hoá đơn của hồ sơ (cần, đã nối, còn thiếu). Dùng cho màn."""
	from vagabond.hoa_don_sau import do_phu
	return do_phu(_khoan_cua(d), _lien_ket_cua(d))


def _so_ngay(a, b):
	from frappe.utils import date_diff
	try:
		return abs(date_diff(a, b)) if a and b else 9999
	except Exception:
		return 9999


@frappe.whitelist()
def ung_vien_hoa_don(name, tu_khoa="", moi_ncc=0):
	"""Ô chọn hoá đơn đến sau (v530): tờ còn mở của NHÓM nhà cung cấp (cùng
	MST gốc), cả tờ nháp lẫn tờ đã ghi sổ còn nợ, kèm gợi ý của máy.
	moi_ncc=1 và có từ khoá: tìm theo số hoá đơn trên mọi nhà cung cấp (đường
	thoát khi hồ sơ chọn sai nhà cung cấp)."""
	from vagabond.ho_so_tt import _kiem, VAI_LAP, VAI_FIN, VAI_GD, _cong_ty_chung_tu, LOAI_TKCT
	from vagabond import hoa_don_sau as hs
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "tìm hóa đơn đến sau")
	d = frappe.get_doc("Vagabond Ho So TT", name)
	tkct = (getattr(d, "loai", None) or "") == LOAI_TKCT
	nhom, goc = _nhom_ncc(d.nha_cung_cap)
	tu_khoa = (tu_khoa or "").strip()
	moi = cint(moi_ncc) and len(tu_khoa) >= 2
	loc = {"company": _cong_ty_chung_tu(), "docstatus": ["<", 2]}
	if _co_dau_huy():
		loc["vgb_huy"] = 0
	if not moi:
		loc["supplier"] = ["in", nhom]
	or_loc = None
	if tu_khoa:
		or_loc = {"name": ["like", "%" + tu_khoa + "%"], "bill_no": ["like", "%" + tu_khoa + "%"]}
	ds = _bo_trung(frappe.get_all("Purchase Invoice", filters=loc, or_filters=or_loc,
		fields=["name", "bill_no", "bill_date", "posting_date", "supplier", "supplier_name",
			"grand_total", "outstanding_amount", "docstatus"],
		order_by="posting_date desc", limit_page_length=60 if moi else 300))
	cua_minh = {r.get("hoa_don") for r in _lien_ket_cua(d)} | {
		(r.get("hoa_don_bo_sung") or "").strip() for r in _khoan_cua(d)} | {
		(r.get("hoa_don") or "").strip() for r in _khoan_cua(d)}
	giu = _giu_boi_ho_so([r["name"] for r in ds], tru=d.name)
	moc = str(d.get("ngay_thanh_toan") or d.get("ngay") or "")
	ra = []
	for r in ds:
		if r["name"] in cua_minh or r["name"] in giu:
			continue
		if hs.da_ghi_so(r) and hs.tien_khop(r) <= 0.5 and tkct:
			continue
		ra.append({
			"name": r["name"], "so_hd": r.get("bill_no") or "", "ngay": str(r.get("bill_date") or r.get("posting_date") or ""),
			"ncc": r.get("supplier") or "", "ncc_ten": r.get("supplier_name") or r.get("supplier") or "",
			"cung_nhom": 1 if r.get("supplier") in nhom else 0,
			"tong": _tien(r.get("grand_total")), "tien": hs.tien_khop(r),
			"da_ghi_so": 1 if hs.da_ghi_so(r) else 0, "nhan": hs.nhan_to(r),
			"_cach": _so_ngay(r.get("bill_date") or r.get("posting_date"), moc),
		})
	ra.sort(key=lambda x: (0 if x["cung_nhom"] else 1, x["_cach"]))
	for x in ra:
		x.pop("_cach", None)
	phu = hs.do_phu(_khoan_cua(d), _lien_ket_cua(d))
	goi = None
	if not moi:
		goi = hs.goi_y([x for x in ra if x["cung_nhom"]], phu["con_thieu"],
			[r.get("so_hd_ncc") for r in _khoan_cua(d)])
	return {"ds": ra, "goi_y": goi, "phu": phu, "tkct": 1 if tkct else 0, "ncc": d.nha_cung_cap,
		"mst_goc": goc, "so_ncc_nhom": len(nhom), "tim_moi_ncc": 1 if moi else 0}


def _no_chi_phi_con_lai(d):
	"""{tài khoản: số Nợ bút toán chi của hồ sơ còn lại sau các lần bù trừ}.

	Bút toán chi: Journal Entry mang vgb_ho_so_tt, hồ sơ cũ trước v445 thì
	nhận theo số tham chiếu (cheque_no) là mã hồ sơ. Đây là phép soát cuối:
	kế hoạch bù trừ lập từ khoản chi, nhưng Có vào tài khoản nào thì tài
	khoản đó phải THẬT SỰ đã được hồ sơ ghi Nợ đủ số."""
	je = [r[0] for r in frappe.db.sql(
		"select name from `tabJournal Entry` where docstatus = 1 and vgb_ho_so_tt = %s", (d.name,))]
	if not je:
		je = [r[0] for r in frappe.db.sql(
			"select name from `tabJournal Entry` where docstatus = 1 and cheque_no = %s", (d.name,))]
	no = {}
	if je:
		for tk, n in frappe.db.sql(
			"""select account, sum(debit_in_account_currency) from `tabJournal Entry Account`
			where parent in %s group by account""", (tuple(je),)):
			no[tk] = _tien(n)
	for tk, c in frappe.db.sql(
		"""select a.account, sum(a.credit_in_account_currency) from `tabJournal Entry Account` a
		inner join `tabJournal Entry` j on j.name = a.parent
		where j.docstatus = 1 and j.vgb_bu_tru_ho_so = %s group by a.account""", (d.name,)):
		no[tk] = no.get(tk, 0.0) - _tien(c)
	return no


def _lap_bu_tru(d, cac):
	"""Lập và ghi sổ MỘT bút toán bù trừ cho mọi tờ đã ghi sổ của một lần nối.

	cac: [(tờ, số bù, kế hoạch)]. Một lần nối một chứng từ (Mobifone sáu tờ
	là một bút toán sáu dòng Nợ 331, không phải sáu bút toán). Không commit:
	cùng giao dịch với lần lưu hồ sơ, lỗi ở đâu thì cả lần nối lùi lại."""
	from vagabond import hoa_don_sau as hs
	from vagabond.ho_so_tt import _cong_ty_chung_tu
	con = _no_chi_phi_con_lai(d)
	can = {}
	for _hd, _so, ke in cac:
		for tk, tien in ke:
			can[tk] = can.get(tk, 0.0) + tien
	for tk in sorted(can):
		if can[tk] > con.get(tk, 0.0) + 0.5:
			frappe.throw(
				"Bút toán chi của hồ sơ %s chỉ còn ghi Nợ %s %s đ, không đủ %s đ để bù trừ. "
				"Nhờ kế toán kiểm bút toán chi của hồ sơ." % (d.name, tk, _dd(con.get(tk, 0.0)), _dd(can[tk])),
				title="Chưa bù trừ được")
	cty = _cong_ty_chung_tu()
	ttcp = frappe.db.get_value("Company", cty, "cost_center")
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = cty
	ngay = ""
	for hd, _so, _ke in cac:
		ngay = max(ngay, hs.ngay_bu_tru(d.get("ngay_thanh_toan"), hd.get("posting_date")))
	je.posting_date = ngay
	je.user_remark = (
		"Bù trừ hoá đơn đến sau: hồ sơ %s đã chi từ tài khoản công ty, tờ %s đã ghi sổ. Chuyển %s đ chi phí "
		"đã ghi qua hồ sơ sang trả công nợ các tờ này, chi phí chỉ còn một lần theo tờ hoá đơn."
		% (d.name, ", ".join("%s (số %s)" % (hd["name"], hd.get("bill_no") or "") for hd, _s, _k in cac),
			hs.dd(sum(so for _h, so, _k in cac)))
	)
	gop, thu_tu = {}, []
	for hd, so, ke in cac:
		dong = hs.dong_but_toan_bu_tru(hd, so, ke, ttcp)
		je.append("accounts", dong[0])
		for r in dong[1:]:
			if r["account"] not in gop:
				thu_tu.append(r["account"])
				gop[r["account"]] = 0.0
			gop[r["account"]] += r["credit_in_account_currency"]
	for tk in thu_tu:
		je.append("accounts", {"account": tk, "credit_in_account_currency": round(gop[tk], 2), "cost_center": ttcp})
	je.vgb_bu_tru_ho_so = d.name
	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	je.submit()
	return je.name


def _loai_tk(tk):
	return frappe.db.get_value("Account", tk, "account_type") if tk else ""


def _cap_nhat_hop_le(d, tkct):
	"""Đổi hồ sơ sang Hợp lệ tính thuế khi phủ đủ, trả 1 nếu vừa đổi."""
	from vagabond import hoa_don_sau as hs
	from vagabond.ho_so_tt import CP_HOP_LE
	if not tkct:
		return 0
	tong = {}
	for ma in sorted({(x.get("hoa_don_bo_sung") or "").strip() for x in _khoan_cua(d)} - {""}):
		tong[ma] = tong_hoa_don_khoa(ma)
	lech = lech_tien_hoa_don(_khoan_cua(d), tong)
	if hs.nen_hop_le(_khoan_cua(d), _lien_ket_cua(d), lech) and (getattr(d, "loai_cp_thue", None) or "") != CP_HOP_LE:
		d.loai_cp_thue = CP_HOP_LE
		return 1
	return 0


@frappe.whitelist(methods=["POST"])
def noi_nhieu(name, hoa_don, ngoai_ncc=0):
	"""Nối một hay nhiều tờ vào hồ sơ (v530). FIN hoặc giám đốc.

	Tờ nháp: làm chứng từ, không được ghi sổ nữa (như v526). Tờ đã ghi sổ còn
	nợ ở hồ sơ chi từ TK công ty: lập bút toán bù trừ. Khoản chưa đánh dấu
	hoá đơn đến sau mà đủ điều kiện thì đánh dấu luôn: một nút, không hai bước
	(chị Dung 25/09/2026). Lệch tiền vẫn nối, hồ sơ chỉ chưa thành hợp lệ."""
	import json
	from frappe.utils import now_datetime
	from vagabond import hoa_don_sau as hs
	from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD, _cong_ty_chung_tu, LOAI_TKCT
	_kiem(VAI_FIN | VAI_GD, "nối hóa đơn đến sau")
	ds = hoa_don
	if isinstance(ds, str):
		ds = json.loads(ds) if ds.strip().startswith("[") else [ds]
	ds = list(dict.fromkeys((str(x) or "").strip() for x in (ds or []) if str(x or "").strip()))
	if not ds:
		frappe.throw("Chưa chọn hoá đơn nào.")
	frappe.db.sql("select name from `tabVagabond Ho So TT` where name=%s for update", name)
	d = frappe.get_doc("Vagabond Ho So TT", name)
	if d.trang_thai in TT_KHONG_NOI_THEM:
		frappe.throw("Hồ sơ đã huỷ hoặc bị từ chối, không nối thêm hoá đơn.")
	tkct = (getattr(d, "loai", None) or "") == LOAI_TKCT
	nhom, _goc = _nhom_ncc(d.nha_cung_cap)
	cty = _cong_ty_chung_tu()
	# Khoá mọi tờ theo thứ tự tên trước khi đọc gì: hai lần nối chéo nhau
	# không khoá vòng.
	for ma in sorted(ds):
		khoa_hoa_don(ma)
	da_co = {r.get("hoa_don") for r in _lien_ket_cua(d)} | {
		(r.get("hoa_don_bo_sung") or "").strip() for r in _khoan_cua(d)} | {
		(r.get("hoa_don") or "").strip() for r in _khoan_cua(d)}
	danh_dau = []
	if tkct:
		for i, r in enumerate(d.dong):
			if not cint(r.get("cho_hoa_don")) and not loi_danh_dau_bu(d.loai, d.trang_thai, _dict_dong(r), LOAI_TKCT):
				r.cho_hoa_don = 1
				danh_dau.append(i + 1)
	khoan = [{"idx": r.idx, "tk_no": r.get("tk_no"), "so_tien": _tien(r.get("so_tien")),
		"cong_no": hs.la_khoan_cong_no(r.get("tk_no"), _loai_tk(r.get("tk_no")))}
		for r in d.dong if not (r.get("hoa_don") or "").strip() and not (r.get("hoa_don_bo_sung") or "").strip()]
	da_dung = sum(_tien(r.get("bu_tru")) if cint(r.get("da_ghi_so")) else _tien(r.get("tien_khop"))
		for r in _lien_ket_cua(d))
	bu = []
	for ma in ds:
		if ma in da_co:
			frappe.throw("Hoá đơn %s đã nối vào chính hồ sơ này rồi." % ma)
		r = frappe.db.sql(
			"""select name, docstatus, supplier, company, grand_total, outstanding_amount, credit_to,
				posting_date, bill_no""" + (", ifnull(vgb_huy, 0) as vgb_huy" if _co_dau_huy() else ", 0 as vgb_huy") + """
			from `tabPurchase Invoice` where name = %s for update""", (ma,), as_dict=True)
		if not r:
			frappe.throw("Không có hoá đơn %s. Tải lại danh sách rồi chọn lại." % ma)
		hd = r[0]
		trong_nhom = hd["supplier"] in nhom
		loi = hs.loi_noi_to(hd, ho_so_dang_giu(ma, khoa=True), tkct, trong_nhom, bool(cint(ngoai_ncc)),
			hd["company"] == cty)
		if loi:
			frappe.throw("Hoá đơn %s (số %s) %s." % (ma, hd.get("bill_no") or "", loi), title="Chưa nối được")
		tk = hs.tien_khop(hd)
		dong = {"hoa_don": ma, "so_hd_ncc": hd.get("bill_no") or "", "ncc": hd["supplier"],
			"tong_hd": _tien(hd.get("grand_total")), "tien_khop": tk, "da_ghi_so": 1 if hs.da_ghi_so(hd) else 0,
			"ngoai_ncc": 0 if trong_nhom else 1, "noi_boi": frappe.session.user, "noi_luc": now_datetime(),
			"bu_tru": 0, "but_toan": ""}
		if tkct and hs.da_ghi_so(hd):
			if d.trang_thai != "Da thanh toan":
				frappe.throw("Hồ sơ %s chưa ghi nhận đã chi tiền, nên chưa có chi phí nào để bù trừ tờ đã ghi sổ %s. "
					"Ghi nhận thanh toán trước, hoặc trả tờ này bằng hồ sơ trả nhà cung cấp." % (d.name, ma))
			so_bu, ke = hs.ke_hoach_bu_tru(khoan, da_dung, tk)
			if so_bu <= 0.5:
				frappe.throw("Chi phí hồ sơ %s đã được các tờ nối trước phủ hết, không còn gì để bù trừ tờ %s. "
					"Kiểm lại các tờ đã nối." % (d.name, ma), title="Chưa nối được")
			dong["bu_tru"] = so_bu
			da_dung += so_bu
			bu.append((hd, so_bu, ke, dong))
		else:
			da_dung += tk
		d.append("hd_sau", dong)
		da_co.add(ma)
	but_toan = []
	if bu:
		ten = _lap_bu_tru(d, [(hd, so, ke) for hd, so, ke, _d in bu])
		but_toan.append(ten)
		ma_bu = {x[0]["name"] for x in bu}
		for r in d.hd_sau:
			if r.hoa_don in ma_bu and not r.but_toan:
				r.but_toan = ten
	doi_hop_le = _cap_nhat_hop_le(d, tkct)
	d.flags.vgb_noi_hd_sau = True
	d.save(ignore_permissions=True)
	phu = hs.do_phu(_khoan_cua(d), _lien_ket_cua(d))
	d.add_comment("Comment", "Nối %d hoá đơn đến sau: %s.%s%s%s Đã nối %s đ trên %s đ cần.%s" % (
		len(ds), ", ".join(ds),
		(" Đánh dấu hoá đơn đến sau cho khoản %s." % ", ".join(str(i) for i in danh_dau)) if danh_dau else "",
		(" Bút toán bù trừ: %s." % ", ".join(but_toan)) if but_toan else "",
		" Có tờ ngoài nhà cung cấp, người nối đã xác nhận." if cint(ngoai_ncc) else "",
		hs.dd(phu["da_noi"]), hs.dd(phu["can"]),
		" Đủ hoá đơn, hồ sơ chuyển sang chi phí hợp lệ tính thuế." if doi_hop_le else ""))
	return {"ok": 1, "hop_le": doi_hop_le, "phu": phu, "but_toan": but_toan, "danh_dau": danh_dau}


@frappe.whitelist(methods=["POST"])
def go_noi(name, hoa_don):
	"""Gỡ một tờ nối mức hồ sơ (v530), đường sửa khi nối nhầm. FIN hoặc giám
	đốc. Tờ có bút toán bù trừ thì huỷ bút toán đó, công nợ tờ trở lại như cũ."""
	from vagabond import hoa_don_sau as hs
	from vagabond.ho_so_tt import _kiem, VAI_FIN, VAI_GD, LOAI_TKCT, CP_HOP_LE, CP_KHONG_HOP_LE
	_kiem(VAI_FIN | VAI_GD, "gỡ hóa đơn đến sau")
	frappe.db.sql("select name from `tabVagabond Ho So TT` where name=%s for update", name)
	d = frappe.get_doc("Vagabond Ho So TT", name)
	ma = (hoa_don or "").strip()
	dong = next((r for r in (d.get("hd_sau") or []) if r.hoa_don == ma), None)
	if not dong:
		frappe.throw("Hồ sơ %s không có tờ %s nối ở mức hồ sơ. Tờ nối kiểu cũ theo khoản thì nhờ kế toán xử lý." % (name, ma))
	# Tờ nối cùng lần chung một bút toán bù trừ: huỷ bút toán là cả nhóm mất
	# bù trừ, nên gỡ cả nhóm (màn đã báo trước khi hỏi).
	nhom = [r for r in d.hd_sau if dong.but_toan and r.but_toan == dong.but_toan] or [dong]
	but_toan = dong.but_toan or ""
	for r in nhom:
		d.remove(r)
	tkct = (getattr(d, "loai", None) or "") == LOAI_TKCT
	ve = 0
	if tkct and (getattr(d, "loai_cp_thue", None) or "") == CP_HOP_LE and all(
			cint(r.get("cho_hoa_don")) for r in d.dong) and not hs.nen_hop_le(_khoan_cua(d), _lien_ket_cua(d)):
		d.loai_cp_thue = CP_KHONG_HOP_LE
		ve = 1
	d.flags.vgb_noi_hd_sau = True
	d.save(ignore_permissions=True)
	# Codex #373 vòng 1: gỡ dòng nối (lưu hồ sơ) TRƯỚC rồi mới huỷ bút toán,
	# để lúc huỷ không còn dòng nào trỏ vào bút toán. Cùng một giao dịch: huỷ
	# lỗi thì cả lần gỡ lùi lại, dòng nối trở về.
	if but_toan:
		je = frappe.get_doc("Journal Entry", but_toan)
		if je.docstatus == 1:
			je.flags.ignore_permissions = True
			je.cancel()
	go = [r.hoa_don for r in nhom]
	d.add_comment("Comment", "Gỡ hoá đơn đến sau %s.%s%s" % (
		", ".join(go), (" Huỷ bút toán bù trừ %s, công nợ các tờ trở lại." % but_toan) if but_toan else "",
		" Hồ sơ trở lại chi phí không hợp lệ tính thuế vì không còn đủ hoá đơn." if ve else ""))
	return {"ok": 1, "huy_but_toan": but_toan, "go": go, "ve_khong_hop_le": ve}
