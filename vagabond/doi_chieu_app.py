"""Issue #247: chọn sao kê cho APP trước khi ghi sổ, dùng liên kết lõi.

Không tạo DocType. Ô ma_giao_dich giữ Bank Transaction.name đã chọn;
Bank Transaction Payments mới là bằng chứng đối chiếu sau khi ghi sổ.
"""

from functools import wraps
from vagabond.khop_sao_ke import co_ma, doc_ds_mau, khop_mau, mau_sao_ke, xep_goi_y


# phần cần Frappe
import frappe
from frappe.utils import add_days, cint, flt, nowdate

DT = "Vagabond Ho So TT"
BT = "Bank Transaction"

# v528: thanh toán tiện ích (điện, nước, internet) qua app ngân hàng không gõ
# được mã APP. Máy nhớ mẫu đầu dòng sao kê theo nhà cung cấp; xem lớp 3 của
# khop_sao_ke. Ô nằm trên Supplier vì một NCC có nhiều hồ sơ theo tháng.
O_MAU = "vgb_mau_sao_ke"
# Giao dịch trước ngày lập hồ sơ bao lâu vẫn được xét: có khoản trả trước
# rồi mới lập hồ sơ (tiền điện trích tự động).
SO_NGAY_TRUOC = 45
TRUONG_MOI = {
	"Supplier": [{
		"fieldname": O_MAU, "label": "Mẫu nội dung sao kê (thanh toán tiện ích)",
		"fieldtype": "Small Text", "insert_after": "email_cc",
		"description": (
			"Mỗi dòng một mẫu đầu dòng sao kê, ví dụ WATER BT WATER. Khoản trả "
			"qua tính năng thanh toán hoá đơn của app ngân hàng không ghi được mã "
			"APP; sao kê bắt đầu bằng mẫu này, đúng số tiền, đúng tài khoản và chỉ "
			"một dòng chưa ai dùng thì máy tự khớp. Xoá dòng để máy thôi nhớ."
		),
	}],
}


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
	theo_mau = False
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
		ds, hang = [], []
		if bas:
			hang = frappe.get_all(BT, filters={"bank_account": ["in", bas], "docstatus": 1,
				"withdrawal": tien, "deposit": 0}, fields=["name", "date", "description", "reference_number"], limit_page_length=0)
			for r in hang:
				if co_ma(r.description, doc.name) or co_ma(r.reference_number, doc.name):
					ds.append(r.name)
		if len(ds) > 1:
			frappe.throw("Có nhiều giao dịch mang mã %s. Bấm Đối chiếu tay và chọn đúng dòng sao kê." % doc.name)
		if not ds:
			ds = _theo_mau(doc, nguon, hang)
			theo_mau = bool(ds)
	if not ds:
		return None
	if khoa:
		frappe.db.get_value(BT, ds[0], "name", for_update=True)
	g = frappe.get_doc(BT, ds[0], for_update=khoa)
	loi = _kiem(g, doc, nguon)
	if loi:
		frappe.throw("Giao dịch %s: %s" % (g.name, loi))
	g.flags.theo_mau = theo_mau
	return g


def _mau_cua_ncc(ncc):
	"""Mẫu đã nhớ của NCC. Trước khi migrate dựng ô thì coi như chưa nhớ."""
	if not ncc or not frappe.get_meta("Supplier").has_field(O_MAU):
		return []
	return doc_ds_mau(frappe.db.get_value("Supplier", ncc, O_MAU))


def _tu_ngay(doc):
	return str(add_days(doc.get("ngay") or nowdate(), -SO_NGAY_TRUOC))


def _theo_mau(doc, nguon, hang):
	"""Khớp tự động khoản trả tiện ích: mẫu NCC đã nhớ, đúng tiền, đúng tài
	khoản (hang đã lọc hai điều đó), trong khoảng ngày, và CHỈ MỘT dòng còn
	dùng được. Nhiều dòng thì không đoán, để người chọn trong gợi ý."""
	mau = _mau_cua_ncc(doc.get("nha_cung_cap"))
	if not mau:
		return []
	tu = _tu_ngay(doc)
	khop = [r for r in hang if str(r.date or "") >= tu and khop_mau(r.description, mau)]
	dung = [r.name for r in khop if not _kiem(frappe.get_doc(BT, r.name), doc, nguon)]
	return dung if len(dung) == 1 else []


def goi_y_khong_ma(doc, gioi_han=5):
	"""Dòng sao kê đúng tiền, đúng tài khoản, chưa ai dùng, trong khoảng ngày
	của hồ sơ, mà KHÔNG mang mã. Chỉ để NGƯỜI bấm chọn; không gán gì."""
	nguon = _nguon(doc)
	cty, tk, tien = nguon
	bas = frappe.get_all("Bank Account", filters={"company": cty, "account": tk,
		"is_company_account": 1, "disabled": 0}, pluck="name")
	if not bas or tien <= 0:
		return []
	mau = _mau_cua_ncc(doc.get("nha_cung_cap"))
	ra = []
	for r in frappe.get_all(BT, filters={"bank_account": ["in", bas], "docstatus": 1,
			"withdrawal": tien, "deposit": 0, "date": [">=", _tu_ngay(doc)]},
			fields=["name", "date", "description", "reference_number"],
			order_by="date desc, name desc", limit_page_length=30):
		if _kiem(frappe.get_doc(BT, r.name), doc, nguon):
			continue
		ra.append({"name": r.name, "date": str(r.date or ""), "mo_ta": (r.description or "").strip(),
			"tham_chieu": r.reference_number or "", "tien": tien,
			"mau": mau_sao_ke(r.description), "da_nho": int(bool(khop_mau(r.description, mau)))})
	return xep_goi_y(ra, doc.get("ngay"))[:gioi_han]


def de_nghi_nho_mau(doc, g):
	"""Sau khi người gán tay một dòng KHÔNG mang mã, đề nghị nhớ mẫu cho NCC.

	Không đề nghị khi: dòng có mã APP (đã tự khớp được), hồ sơ không có NCC,
	không bóc được mẫu, NCC đã nhớ, hoặc mẫu đã thuộc NCC khác."""
	ncc = doc.get("nha_cung_cap")
	if not ncc or co_ma(g.description, doc.name) or co_ma(g.reference_number, doc.name):
		return None
	if not frappe.get_meta("Supplier").has_field(O_MAU):
		return None
	mau = mau_sao_ke(g.description)
	if not mau or mau in _mau_cua_ncc(ncc) or _chu_mau_khac(mau, ncc):
		return None
	return {"mau": mau, "ncc": ncc, "ten_ncc": doc.get("ten_ncc") or ncc}


def _chu_mau_khac(mau, ncc):
	for r in frappe.get_all("Supplier", filters={O_MAU: ["like", "%" + mau + "%"], "name": ["!=", ncc]},
			fields=["name", O_MAU], limit_page_length=0):
		if mau in doc_ds_mau(r.get(O_MAU)):
			return r.name
	return ""


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
	# Sao kê hoàn tiền chỉ nối PE phần trả thêm, JE cấn không có tiền ra112.
	bo = [b for b in bo if b["name"] != doc.get("vgb_can_ung")]
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


def ung_vien_chung(name, so_ngay=120, tu_khoa="", tai_khoan="", thu_tu="goi_y", bat_dau=0, chi_dung=0):
	"""APP dùng cùng danh sách, giữ kiểm nguồn chi và cửa gán riêng."""
	from vagabond import doi_soat_sepay as dss
	doc = _ho_so(name)
	nguon = _nguon(doc)
	cty, tk, tien = nguon
	bas = set(frappe.get_all("Bank Account", filters={"company": cty, "account": tk,
		"is_company_account": 1, "disabled": 0}, pluck="name"))
	def ly_do(g):
		# Kiểm rẻ trước, tránh nạp Document/đọc chủ từng dòng không liên quan.
		if g.get("bank_account") not in bas:
			return "Tài khoản ngân hàng không khớp nguồn chi của hồ sơ."
		if abs(flt(g.get("withdrawal")) - tien) > 0.001:
			return "Số tiền không khớp khoản phải chuyển. Kế toán dùng Đối chiếu ngân hàng cho khoản tách lần hoặc phí."
		return _kiem(frappe.get_doc(BT, g["name"]), doc, nguon)
	kq = dss.danh_sach_chon(dss.RA, doc.name, tien, so_ngay, tu_khoa, tai_khoan,
		thu_tu, bat_dau, ly_do=ly_do, chi_dung=chi_dung)
	kq.update(ten_man="Hồ sơ thanh toán", ma_gd_dang_gan=doc.get("ma_giao_dich") or "")
	return kq


@frappe.whitelist()
def danh_sach(name, tu_khoa="", so_ngay=120, so_tien=None, chi_chua_gom=0):
	# Giữ hình dạng API cũ cho khách chưa tải app mới, dữ liệu cùng một cửa.
	kq = ung_vien_chung(name, so_ngay, tu_khoa, chi_dung=chi_chua_gom)
	for r in kq["rows"]:
		r.update(ma=r["name"], ten_ban_ghi=r["name"], ngay=r["date"],
			noi_dung=r["mo_ta"], chi=r["tien"], thu=0, tai_khoan=r.get("bank_account"),
			da_gom=int(not r["dung_duoc"]), ly_do=r["vi_sao_khong"], tham_chieu=r.get("reference_number"))
	kq.update(sua_duoc=1, so_tien_chuyen=kq["so_tien"])
	return kq


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
	return {"ok": 1, "loi_nhan": "Đã chọn giao dịch. " + ("Đã đối chiếu bút toán." if doc.trang_thai == "Da thanh toan" else "Đính UNC và bấm Ghi nhận đã thanh toán để hoàn tất."),
		"nho_mau": de_nghi_nho_mau(doc, g)}


@frappe.whitelist(methods=["POST"])
def nho_mau(name, mau):
	"""Nhớ mẫu đầu dòng sao kê cho NCC của hồ sơ, sau khi người đã gán tay.

	Chỉ nhận đúng mẫu bóc từ giao dịch hồ sơ đang giữ, không nhận chữ tự gõ,
	để không ai nhớ nhầm một mẫu chung làm máy khớp bừa về sau."""
	doc = _ho_so(name)
	ma = str(doc.get("ma_giao_dich") or "").strip()
	if not ma or not frappe.db.exists(BT, ma):
		frappe.throw("Hồ sơ %s chưa gán giao dịch ngân hàng. Khớp giao dịch trước rồi mới nhớ mẫu." % name)
	g = frappe.get_doc(BT, ma)
	de = de_nghi_nho_mau(doc, g)
	mau = " ".join(str(mau or "").split()).upper()
	if not de or de["mau"] != mau:
		chu = _chu_mau_khac(mau, doc.get("nha_cung_cap") or "") if mau else ""
		frappe.throw(("Mẫu %s đã nhớ cho nhà cung cấp %s. Hai nhà cung cấp chung một mẫu thì máy không phân biệt được, kế toán khớp tay từng lần." % (mau, chu))
			if chu else "Mẫu không khớp giao dịch %s của hồ sơ, hoặc nhà cung cấp đã nhớ rồi." % ma)
	ncc = de["ncc"]
	frappe.db.get_value("Supplier", ncc, "name", for_update=True)
	cu = doc_ds_mau(frappe.db.get_value("Supplier", ncc, O_MAU))
	if mau not in cu:
		frappe.db.set_value("Supplier", ncc, O_MAU, "\n".join(cu + [mau]))
		frappe.get_doc("Supplier", ncc).add_comment("Comment",
			"Nhớ mẫu sao kê %s từ hồ sơ %s, giao dịch %s." % (mau, name, ma))
		doc.add_comment("Comment", "Nhớ mẫu sao kê %s cho nhà cung cấp %s." % (mau, ncc))
	return {"ok": 1, "loi_nhan": "Đã nhớ mẫu %s cho %s. Lần sau đúng số tiền, đúng tài khoản thì máy tự khớp." % (mau, de["ten_ncc"])}


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



def canh_bao_mo_lai(ds):
	"""Một nguồn cảnh báo cho danh sách/chi tiết, đọc theo lô từ voucher thật."""
	ten = [r.get("name") or r.get("ma") for r in ds if r.get("trang_thai") == "Da duyet"]
	if not ten:
		return {}
	huy = set()
	for dt in ("Payment Entry", "Journal Entry"):
		huy.update(frappe.get_all(dt, filters={"vgb_ho_so_tt": ["in", ten], "docstatus": 2},
			pluck="vgb_ho_so_tt", limit_page_length=0))
	return {ma: "Đã huỷ bút toán. Kiểm tra sao kê trước khi ghi nhận lại; không tự chuyển tiền thêm." for ma in huy}
