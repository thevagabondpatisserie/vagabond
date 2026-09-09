"""Issue #247: chọn sao kê cho APP trước khi ghi sổ, dùng liên kết lõi.

Không tạo DocType. Ô ma_giao_dich giữ Bank Transaction.name đã chọn;
Bank Transaction Payments mới là bằng chứng đối chiếu sau khi ghi sổ.
"""

from functools import wraps
from vagabond.khop_sao_ke import co_ma


# phần cần Frappe
import frappe
from frappe.utils import add_days, cint, flt, nowdate

DT = "Vagabond Ho So TT"
BT = "Bank Transaction"


def _ho_so(name, khoa=False):
	from vagabond import ho_so_tt as hs

	hs._kiem(hs.VAI_FIN, "đối chiếu giao dịch ngân hàng")
	if khoa:
		frappe.db.get_value(DT, name, "name", for_update=True)
	doc = frappe.get_doc(DT, name, for_update=khoa)
	doc.check_permission("read")
	if doc.trang_thai not in (hs.TT_DA_DUYET, hs.TT_DA_TRA):
		frappe.throw("Hồ sơ %s chưa duyệt xong. Duyệt đủ hai cấp rồi đối chiếu ngân hàng." % name)
	return doc


def _nguon(doc):
	from vagabond import ho_so_tt as hs

	ke = hs._dung_ke_hoach_chi(doc)
	loi = hs._loi_ke_hoach_chi(ke)
	if loi:
		frappe.throw("Hồ sơ %s chưa xác định được nguồn chi: %s." % (doc.name, loi))
	if ke["loai"] == "PE":
		nguon = {(r["company"], r["nguon_chi"]) for r in ke["hoa_don"].values()}
	else:
		nguon = {(ke["company"], tk) for tk, tien in ke["co"].items() if tien > 0}
	if len(nguon) != 1:
		frappe.throw("Hồ sơ %s có nhiều nguồn chi. Kế toán đối chiếu từng bút toán trong Đối chiếu ngân hàng." % doc.name)
	cty, tk = next(iter(nguon))
	return cty, tk, hs._so_phai_chuyen(doc, hs._do_chinh_xac())["con"]


def _chu_khac(g, doc):
	"""Kiểm cả mã bản ghi và tham chiếu cũ, không nuốt lỗi đọc chủ."""
	ma = sorted({g.name, g.reference_number} - {None, ""})
	# Current reads sau khóa BT: snapshot cũ không được che mất APP vừa
	# chọn ở request cạnh tranh. Deadlock thì DB hủy một lượt, không ghi đôi.
	for r in frappe.db.sql("""select name from `tabVagabond Ho So TT`
		where name != %s and ma_giao_dich in %s and trang_thai != 'Tu choi'
		limit 1""" + (" for update" if g.flags.get("for_update") else ""), (doc.name, tuple(ma))):
		return r[0]
	for r in frappe.db.sql("""select d.parent from `tabVagabond Ho So TT Dong` d
		join `tabVagabond Ho So TT` p on p.name=d.parent
		where d.ma_giao_dich in %s and d.parent != %s and p.trang_thai != 'Tu choi'
		limit 1""" + (" for update" if g.flags.get("for_update") else ""), (tuple(ma), doc.name)):
		return r[0]
	from vagabond import doi_soat_sepay as dss
	# Nhập trực tiếp để lỗi nạp luồng không bị nap_so nuốt mất.
	import importlib
	for ten in dss.MO_DUN_KHAI:
		importlib.import_module("vagabond." + ten)
	dss.nap_so()
	for b in dss._SO.values():
		loc = dict(b.get("loc_chiem") or {})
		loc[b["truong_gd"]] = ["in", ma]
		chu = frappe.db.get_value(b["doctype"], loc, "name")
		if chu:
			return chu
	return ""


def _kiem(g, doc, nguon):
	cty, tk, tien = nguon
	if cint(g.docstatus) != 1 or flt(g.deposit) != 0 or flt(g.withdrawal) <= 0:
		return "Chọn giao dịch tiền ra đã xác nhận trên sao kê."
	ba = frappe.db.get_value("Bank Account", g.bank_account,
		["company", "account", "is_company_account", "disabled"], as_dict=True) or {}
	if ba.get("company") != cty or ba.get("account") != tk or not ba.get("is_company_account") or ba.get("disabled"):
		return "Tài khoản ngân hàng không khớp nguồn chi của hồ sơ."
	if g.currency != "VND" or tien <= 0 or abs(flt(g.withdrawal) - tien) > 0.001:
		return "Số tiền hoặc tiền tệ không khớp khoản phải chuyển. Kế toán kiểm khoản chi tách lần/phí trong Đối chiếu ngân hàng."
	chu = _chu_khac(g, doc)
	if chu:
		return "Giao dịch đã được %s sử dụng. Chọn giao dịch khác." % chu
	# Lõi có thể nối nhiều PE/JE cho một APP, nhưng không được lấy phần đã
	# phân bổ cho chứng từ ngoài hồ sơ. Không coi unallocated > 0 là đủ.
	for r in g.payment_entries or []:
		if r.payment_document not in ("Payment Entry", "Journal Entry"):
			return "Giao dịch đã đối chiếu với chứng từ khác."
		if frappe.db.get_value(r.payment_document, r.payment_entry, "vgb_ho_so_tt") != doc.name:
			return "Giao dịch đã đối chiếu với chứng từ %s." % r.payment_entry
	return ""


def chon(doc, ma=None, khoa=False):
	"""Dò tự động chỉ khi có đúng một giao dịch; chọn tay cũng kiểm y hệt."""
	nguon = _nguon(doc)
	ma = str(ma or doc.get("ma_giao_dich") or "").strip()
	if ma:
		# Không chuyển chuỗi tham chiếu không duy nhất thành một bản ghi ngẫu nhiên.
		ten = ma if frappe.db.exists(BT, ma) else None
		if not ten:
			ds = frappe.get_all(BT, filters={"reference_number": ma, "docstatus": 1}, pluck="name", limit_page_length=2)
			if len(ds) != 1:
				frappe.throw("Mã giao dịch cũ không xác định được một dòng sao kê. Bấm Đối chiếu tay để chọn lại.")
			ten = ds[0]
		ds = [ten]
	else:
		# Lọc theo tài khoản trước, so cả nội dung và tham chiếu bằng phép
		# chung có ranh giới số. Không cộng một dòng hai lần khi mã lặp.
		cty, tk, tien = nguon
		bas = frappe.get_all("Bank Account", filters={"company": cty, "account": tk}, pluck="name")
		ds = []
		if bas:
			for r in frappe.get_all(BT, filters={"bank_account": ["in", bas], "docstatus": 1,
				"withdrawal": tien, "deposit": 0}, fields=["name", "description", "reference_number"], limit_page_length=0):
				if co_ma(r.description, doc.name) or co_ma(r.reference_number, doc.name):
					ds.append(r.name)
		if len(ds) > 1:
			frappe.throw("Có nhiều giao dịch mang mã %s. Bấm Đối chiếu tay và chọn đúng dòng sao kê." % doc.name)
	if not ds:
		return None
	if khoa:
		frappe.db.get_value(BT, ds[0], "name", for_update=True)
	g = frappe.get_doc(BT, ds[0], for_update=khoa)
	loi = _kiem(g, doc, nguon)
	if loi:
		frappe.throw("Giao dịch %s: %s" % (g.name, loi))
	return g


def noi_but_toan(doc, g):
	"""Core bank_transaction.py allocate_payment_entries chỉ nhận GL đã có.

	ERPNext de591661, accounts/doctype/bank_transaction/bank_transaction.py:
	get_clearance_details ném lỗi nếu gl_bank_account không có trong GL.
	Vì vậy gọi sau submit PE/JE, trước commit cuối của hồ sơ; không tự ghi
	allocated_amount hoặc clearance_date, để core tính từ GL.
	"""
	from vagabond import ho_so_tt as hs

	bo = hs._but_toan_cua_ho_so(doc.name)
	kq = hs._kiem_bo_chung_tu(hs._ke_hoach_duyet(doc), bo, hs._do_chinh_xac())
	if not kq["du"]:
		frappe.throw("Bộ bút toán hồ sơ %s chưa khớp. Kế toán kiểm lại trước khi đối chiếu." % doc.name)
	da = {(r.payment_document, r.payment_entry) for r in g.payment_entries or []}
	moi = [{"payment_doctype": b["doctype"], "payment_name": b["name"]} for b in bo
		if (b["doctype"], b["name"]) not in da]
	if moi:
		# Quyền nghiệp vụ được kiểm tại cửa APP. Core vẫn chạy nguyên validate,
		# allocate và update-after-submit; chỉ quyền ghi BT được ủy quyền ở đây.
		g = frappe.get_doc(BT, g.name, for_update=True)
		g.flags.ignore_permissions = True
		g.add_payment_entries(moi)
		g.save(ignore_permissions=True)
	g.reload()
	if abs(flt(g.unallocated_amount)) > 0.001 or abs(flt(g.allocated_amount) - flt(g.withdrawal)) > 0.001:
		frappe.throw("Đối chiếu chưa phân bổ hết giao dịch %s. Đã dừng ghi nhận, kế toán kiểm lại bút toán." % g.name)
	if {(r.payment_document, r.payment_entry) for r in g.payment_entries} != {(b["doctype"], b["name"]) for b in bo}:
		frappe.throw("Liên kết đối chiếu không đủ bộ bút toán hồ sơ %s." % doc.name)


@frappe.whitelist()
def danh_sach(name, tu_khoa="", so_ngay=120, so_tien=None, chi_chua_gom=0):
	doc = _ho_so(name)
	nguon = _nguon(doc)
	cty, tk, tien = nguon
	bas = frappe.get_all("Bank Account", filters={"company": cty, "account": tk}, pluck="name")
	loc = {"bank_account": ["in", bas], "docstatus": 1, "withdrawal": tien, "deposit": 0,
		"date": [">=", add_days(nowdate(), -min(max(cint(so_ngay), 1), 3650))]}
	k = str(tu_khoa or "").strip().lower()
	rows = []
	for r in frappe.get_all(BT, filters=loc, fields=["name", "description", "reference_number"], order_by="date desc, name desc", limit_page_length=0) if bas else []:
		if k and k not in (r.name + " " + (r.description or "") + " " + (r.reference_number or "")).lower():
			continue
		g = frappe.get_doc(BT, r.name)
		loi = _kiem(g, doc, nguon)
		if cint(chi_chua_gom) and loi:
			continue
		rows.append({"ma": g.name, "ten_ban_ghi": g.name, "ngay": str(g.date), "noi_dung": g.description,
			"chi": g.withdrawal, "thu": 0, "tien": g.withdrawal, "tai_khoan": g.bank_account,
			"da_gom": 1 if loi else 0, "ly_do": loi, "tham_chieu": g.reference_number})
	return {"rows": rows[:300], "tong": len(rows), "con_nua": max(0, len(rows)-300), "sua_duoc": 1, "so_tien_chuyen": tien}


def _bao_tranh_chap(ham):
	"""POST vẫn ném lỗi để Frappe rollback toàn lượt, không trả thành công dở."""
	@wraps(ham)
	def goi(*args, **kwargs):
		try:
			return ham(*args, **kwargs)
		except frappe.QueryDeadlockError:
			frappe.throw("Có người đang xử lý cùng giao dịch ngân hàng. Tải lại hồ sơ và chọn lại dòng sao kê; nếu đã có hồ sơ khác giữ giao dịch, chọn dòng khác.")
	return goi


def _kiem_bo(doc, ma):
	"""Core bank_transaction.py remove_payment_entries gỡ liên kết khi huỷ.

	Chỉ giải phóng chỗ giữ APP sau khi lõi đã gỡ và không còn PE/JE ghi sổ.
	Không tự huỷ hoặc sửa GL, không coi sao kê hết liên kết là đã huỷ tiền chi.
	"""
	if ma:
		ten = ma if frappe.db.exists(BT, ma) else None
		if not ten:
			ds = frappe.get_all(BT, filters={"reference_number": ma}, pluck="name", limit_page_length=2)
			if len(ds) != 1:
				frappe.throw("Mã cũ không xác định được một dòng sao kê. Nhờ quản trị kiểm tham chiếu trước khi bỏ đối chiếu.")
			ten = ds[0]
		g = frappe.get_doc(BT, ten, for_update=True)
		if g.payment_entries or flt(g.allocated_amount):
			frappe.throw("Sao kê còn liên kết bút toán. Kế toán kiểm và huỷ bút toán sai trong ERPNext trước khi bỏ đối chiếu.")
	for dt in ("Payment Entry", "Journal Entry"):
		# Current read: không dùng snapshot trước khi chờ khoá sao kê.
		if frappe.db.sql("select name from `tab%s` where vgb_ho_so_tt=%%s and docstatus=1 limit 1 for update" % dt, (doc.name,)):
			frappe.throw("Hồ sơ còn bút toán đã ghi sổ. Đối chiếu lại với bút toán đó, hoặc huỷ bút toán sai trong ERPNext rồi bỏ đối chiếu.")


@frappe.whitelist(methods=["POST"])
@_bao_tranh_chap
def bo(name):
	doc = _ho_so(name, khoa=True)
	ma = str(doc.get("ma_giao_dich") or "").strip()
	if ma or doc.trang_thai == "Da thanh toan":
		# Controller kiểm cùng một cửa cho app, Desk xoá mã hoặc mở lại.
		doc.ma_giao_dich = ""
		if doc.trang_thai == "Da thanh toan":
			doc.trang_thai = "Da duyet"
		doc.save(ignore_permissions=True)
	return {"ok": 1, "trang_thai": doc.trang_thai,
		"loi_nhan": "Đã bỏ đối chiếu. Hồ sơ ở Đã duyệt, cần kiểm tra và ghi nhận lại. Không chuyển tiền thêm chỉ vì bút toán đã huỷ."}


@frappe.whitelist(methods=["POST"])
@_bao_tranh_chap
def gan(name, ma_giao_dich):
	doc = _ho_so(name, khoa=True)
	g = chon(doc, ma_giao_dich, khoa=True)
	if not g:
		frappe.throw("Chưa chọn giao dịch. Bấm vào một dòng sao kê để đối chiếu.")
	if doc.trang_thai == "Da thanh toan":
		noi_but_toan(doc, g)
	doc.ma_giao_dich = g.name
	doc.save(ignore_permissions=True)
	doc.add_comment("Comment", "Đối chiếu tay với giao dịch %s, tham chiếu %s." % (g.name, g.reference_number or ""))
	return {"ok": 1, "loi_nhan": "Đã chọn giao dịch. " + ("Đã đối chiếu bút toán." if doc.trang_thai == "Da thanh toan" else "Đính UNC và bấm Ghi nhận đã thanh toán để hoàn tất.")}


def kiem_luu(doc):
	"""Bỏ mã và mở lại sau huỷ là một lần lưu, cả app lẫn Desk đều qua đây."""
	cu = doc.get_doc_before_save()
	ma = str(doc.get("ma_giao_dich") or "").strip()
	ma_cu = str(cu.get("ma_giao_dich") or "").strip() if cu else ""
	da_tra = bool(cu and cu.trang_thai == "Da thanh toan")
	mo_lai = da_tra and (doc.trang_thai != "Da thanh toan" or (ma_cu and not ma))
	if ma == ma_cu and not mo_lai:
		return
	from vagabond import ho_so_tt as hs
	hs._kiem(hs.VAI_FIN, "gán hoặc bỏ đối chiếu giao dịch ngân hàng")
	if doc.trang_thai not in (hs.TT_DA_DUYET, hs.TT_DA_TRA):
		frappe.throw("Dùng Bỏ đối chiếu để mở lại hồ sơ về Đã duyệt sau khi huỷ bút toán.")
	if ma_cu or mo_lai:
		_kiem_bo(doc, ma_cu)
	if mo_lai:
		# Bản cũ có thể đã bỏ mã nhưng còn Đã thanh toán. Chỉ mở lại khi
		# đọc được bút toán huỷ thật, không suy đoán lịch sử từ ô mã trống.
		huy = []
		for dt in ("Payment Entry", "Journal Entry"):
			huy.extend(r[0] for r in frappe.db.sql(
				"select name from `tab%s` where vgb_ho_so_tt=%%s and docstatus=2 for update" % dt, (doc.name,)))
		if not huy:
			frappe.throw("Chưa tìm thấy bút toán đã huỷ của hồ sơ. Nhờ kế toán kiểm lịch sử trước khi mở lại; máy không tự kết luận đã huỷ thanh toán.")
		doc.trang_thai = hs.TT_DA_DUYET
		doc.da_tra = 0
		doc.ngay_thanh_toan = None
		doc.ma_giao_dich = ""
		doc.add_comment("Comment", "Bỏ đối chiếu %s và mở lại về Đã duyệt sau khi huỷ %s. "
			"Trước đó đã trả %s, ngày %s. Giữ UNC, lịch sử duyệt và thư đã gửi. "
			"Cần kiểm tra sao kê trước khi ghi nhận lại; không yêu cầu chuyển tiền thêm."
			% (ma_cu or "(mã đã được bỏ trước đó)", ", ".join(huy), cu.da_tra, cu.ngay_thanh_toan or ""))
	elif ma:
		chon(doc, ma, khoa=True)
	elif ma_cu:
		doc.add_comment("Comment", "Bỏ đối chiếu giao dịch %s sau khi kiểm không còn liên kết và bút toán đã ghi sổ." % ma_cu)
