"""Mã khách và mã nhà cung cấp theo cách kế toán (Fast) theo dõi. v536.

Vì sao có tệp này
-----------------
Chị Dung đối chiếu hoá đơn với Fast theo MÃ: khách lẻ không lấy hoá đơn về
KL0001, công ty và nhà cung cấp mỗi mã số thuế một mã (KH000015, NC000175).
ERP thì mỗi số điện thoại Pancake là một khách KL0xxxxx, hoá đơn công ty
vẫn đứng tên người đặt, nên tìm theo tên công ty không ra và không có cột
mã để đối chiếu (29/09/2026, tờ 14576 của Oliver Marketing).

Luật, anh Việt chốt 29/09/2026:
- Không mã số thuế: KL0001.
- Có mã số thuế: mã Fast trong ô Mã khách hàng (custom_ma_khach) hoặc Mã NCC
  (custom_ma_ncc). Chưa có thì MÁY CẤP MÃ NỐI TIẾP mã lớn nhất đang có,
  không tạm ghi bằng mã số thuế. Từ nay ERP cấp mã, Fast nhập theo ERP.
- Không đổi ô Khách hàng của đơn (người đặt giữ để tích điểm). Chỉ thêm ô
  "Mã khách kế toán" trên hoá đơn bán hàng, điền tự động khi lưu.

Phần trên dòng `import frappe` là phép THUẦN, kiểm được không cần site.
"""

import re

KHACH_LE = "KL0001"
RONG_MA = 6
TIEN_TO = {"Customer": "KH", "Supplier": "NC"}
O_MA = {"Customer": "custom_ma_khach", "Supplier": "custom_ma_ncc"}
NHOM_KHACH_MOI = "Khách doanh nghiệp và quà tặng"
KHOA_CAP_MA = "vgb_ma_ke_toan"


def chuan_mst(s):
	"""10 số giữ nguyên, 12 số (định danh cá nhân) giữ nguyên, 13 số viết
	10 số - 3 số. Khác thì rỗng. Cùng luật với ban_hang._chuan_mst, chép
	lại đây để tầng thuần không kéo ban_hang (ban_hang import requests, CI
	tay không không có)."""
	so = re.sub(r"\D", "", str(s or ""))
	if len(so) in (10, 12):
		return so
	if len(so) == 13:
		return so[:10] + "-" + so[10:]
	return ""


def la_ma(ma, tien_to):
	return bool(re.fullmatch(re.escape(tien_to) + r"\d{4,8}", str(ma or "").strip().upper()))


def so_cua_ma(ma, tien_to):
	m = str(ma or "").strip().upper()
	return int(m[len(tien_to):]) if la_ma(m, tien_to) else 0


def ma_ke_tiep(cac_ma, tien_to, rong=RONG_MA):
	"""Mã kế tiếp sau mã lớn nhất trong danh sách. Danh sách trống thì bắt
	đầu từ 1. Mã không đúng dạng (KL0001, chữ, rỗng) không tính."""
	lon_nhat = max([so_cua_ma(m, tien_to) for m in (cac_ma or [])] + [0])
	return "%s%0*d" % (tien_to, rong, lon_nhat + 1)


def ma_ke_toan_cua_hoa_don(mst, tra_ma):
	"""Mã khách kế toán của một tờ hoá đơn. tra_ma(mst_chuan) trả mã của
	khách có mã số thuế đó, hoặc rỗng. Không MST là khách lẻ KL0001."""
	m = chuan_mst(mst)
	if not m:
		return KHACH_LE
	return str(tra_ma(m) or "").strip().upper()


def doc_tep_fast(dong_ds):
	"""Danh mục Fast (mã, tên, địa chỉ, MST) thành các dòng đã làm sạch.

	Chỉ lấy mã KH và NC. NV, SEP là nhân viên; CTY001, KBNN, CCT là mã
	riêng của Fast không theo luật MST; KL0001 là khách lẻ chung, đã là
	hằng số. Dòng không MST bỏ qua vì không có gì để khớp."""
	ra = []
	for d in dong_ds or []:
		ma = str(d.get("ma") or "").strip().upper()
		loai = "Customer" if ma.startswith("KH") else ("Supplier" if ma.startswith("NC") else "")
		if not loai or not la_ma(ma, TIEN_TO[loai]):
			continue
		mst = chuan_mst(d.get("mst"))
		if not mst:
			continue
		ra.append({"loai": loai, "ma": ma, "mst": mst, "ten": str(d.get("ten") or "").strip(),
			"dia_chi": str(d.get("dia_chi") or "").strip()})
	return ra


def ke_hoach_nap(dong_ds, hien_co, ma_dang_dung=None):
	"""Việc phải làm khi nạp danh mục Fast. THUẦN.

	hien_co: {loai: {mst_chuan: {"name", "ma"}}} là bản ghi ERP đang có.
	ma_dang_dung: {loai: {ma: mst_chuan hoặc ""}} mọi mã ERP đang giữ, kể cả
	bản ghi không MST; bỏ trống thì suy từ hien_co.
	Trả {"cap_nhat": [...], "tao_moi": [...], "xung_dot": [...], "giu": n}.
	- Bản ghi có MST mà chưa có mã: cấp mã theo tệp (cap_nhat).
	- Chưa có bản ghi nào mang MST đó: tạo mới (tao_moi).
	- Đã có mã KHÁC mã trong tệp: xung đột, không ghi đè, để người quyết.
	- Mã trong tệp đang là mã của một bản ghi ERP KHÁC MST: xung đột, vì hai
	  đối tác chung một mã là mất đối chiếu.
	- Cùng mã: giữ.
	Cùng một mã xuất hiện ở hai MST trong tệp thì cũng là xung đột.
	"""
	ra = {"cap_nhat": [], "tao_moi": [], "xung_dot": [], "giu": 0}
	if ma_dang_dung is None:
		ma_dang_dung = {}
		for loai, theo_mst in (hien_co or {}).items():
			for mst, v in theo_mst.items():
				m = str((v or {}).get("ma") or "").strip().upper()
				if m:
					ma_dang_dung.setdefault(loai, {})[m] = mst
	da_thay = {}
	for d in doc_tep_fast(dong_ds):
		k = (d["loai"], d["ma"])
		if k in da_thay and da_thay[k] != d["mst"]:
			ra["xung_dot"].append(dict(d, ly_do="mã %s gắn cho hai MST %s và %s trong tệp" % (d["ma"], da_thay[k], d["mst"])))
			continue
		da_thay[k] = d["mst"]
		co = (hien_co.get(d["loai"]) or {}).get(d["mst"])
		chu_khac = (ma_dang_dung.get(d["loai"]) or {}).get(d["ma"])
		if chu_khac is not None and chu_khac != d["mst"]:
			ra["xung_dot"].append(dict(d, ly_do="ERP đang dùng mã %s cho đối tác khác (MST %s)" % (d["ma"], chu_khac or "trống")))
			continue
		if not co:
			ra["tao_moi"].append(d)
		elif not str(co.get("ma") or "").strip():
			ra["cap_nhat"].append(dict(d, name=co["name"]))
		elif str(co.get("ma")).strip().upper() == d["ma"]:
			ra["giu"] += 1
		else:
			ra["xung_dot"].append(dict(d, name=co["name"], ma_erp=co["ma"],
				ly_do="ERP đang giữ %s, tệp ghi %s" % (co["ma"], d["ma"])))
	return ra


import frappe
from frappe.utils import cint


def _tra_theo_mst(doctype, mst):
	"""Bản ghi (name, mã) đang mang mã số thuế này. So cả dạng có gạch và
	không gạch vì dữ liệu cũ trước 12/08/2026 mất dấu gạch."""
	m = chuan_mst(mst)
	if not m:
		return None
	ung = [m]
	if "-" in m:
		ung.append(m.replace("-", ""))
	r = frappe.get_all(doctype, filters={"tax_id": ["in", ung]}, fields=["name", O_MA[doctype], "tax_id"],
		order_by="creation asc", limit_page_length=2)
	if not r:
		return None
	return {"name": r[0]["name"], "ma": r[0].get(O_MA[doctype]) or ""}


KHOA_DA_NAP = "vgb_ma_ke_toan_da_nap"


def da_nap_danh_muc():
	"""Danh mục Fast đã được nạp lần đầu chưa. Trước đó máy KHÔNG cấp mã
	mới: danh mục Fast của chị Dung đi trước ERP (KH001588 so với KH001382
	ngày 29/09/2026), cấp trước khi nạp là hai công ty chung một mã."""
	return str(frappe.db.get_default(KHOA_DA_NAP) or "") == "1"


def cap_ma(doctype, name):
	"""Cấp mã kế tiếp cho một khách hoặc NCC chưa có mã. Khoá tên toàn
	site trong lúc đọc mã lớn nhất để hai lượt lưu cùng lúc không cùng
	nhận một mã. Đã có mã thì trả mã đang có. Chưa nạp danh mục Fast thì
	trả rỗng, không cấp."""
	o = O_MA[doctype]
	hien = str(frappe.db.get_value(doctype, name, o) or "").strip()
	if hien:
		return hien
	if not da_nap_danh_muc():
		return ""
	frappe.db.sql("select get_lock(%s, 10)", (KHOA_CAP_MA,))
	try:
		hien = str(frappe.db.get_value(doctype, name, o) or "").strip()
		if hien:
			return hien
		tien_to = TIEN_TO[doctype]
		cac_ma = [r[0] for r in frappe.db.sql(
			"select `%s` from `tab%s` where `%s` like %%s" % (o, doctype, o), (tien_to + "%",))]
		ma = ma_ke_tiep(cac_ma, tien_to)
		frappe.db.set_value(doctype, name, o, ma, update_modified=False)
		return ma
	finally:
		frappe.db.sql("select release_lock(%s)", (KHOA_CAP_MA,))


def ma_theo_mst(doctype, mst, ten="", tao_moi=False):
	"""Mã kế toán của đối tác mang MST này; chưa có mã thì cấp; chưa có
	bản ghi thì tạo khi tao_moi. Rỗng khi không tìm ra và không tạo."""
	co = _tra_theo_mst(doctype, mst)
	if not co and tao_moi and ten:
		co = {"name": _tao_doi_tac(doctype, mst, ten), "ma": ""}
	if not co:
		return ""
	return co["ma"] or cap_ma(doctype, co["name"])


def _tao_doi_tac(doctype, mst, ten):
	m = chuan_mst(mst)
	ten = str(ten or "").strip()[:140]
	if doctype == "Customer":
		d = frappe.get_doc({"doctype": "Customer", "customer_name": ten, "customer_type": "Company",
			"customer_group": NHOM_KHACH_MOI if frappe.db.exists("Customer Group", NHOM_KHACH_MOI)
				else frappe.db.get_single_value("Selling Settings", "customer_group"),
			"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
			"tax_id": m})
	else:
		d = frappe.get_doc({"doctype": "Supplier", "supplier_name": ten, "supplier_type": "Company",
			"supplier_group": frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups",
			"tax_id": m})
	d.flags.ignore_permissions = True
	d.insert()
	return d.name


def mst_cua_hoa_don(doc):
	"""MST xuất hoá đơn của một hoá đơn bán hàng: ô Xuất HĐ cho, không có
	thì MST của chính khách hàng (khách sỉ, hợp đồng)."""
	m = chuan_mst(doc.get("vgb_xhd_mst"))
	if m:
		return m
	if doc.get("customer"):
		return chuan_mst(frappe.db.get_value("Customer", doc.customer, "tax_id"))
	return ""


def dien_ma_khach_hoa_don(doc, method=None):
	"""Hook validate Sales Invoice: điền ô Mã khách kế toán. Không bao giờ
	chặn lưu đơn: lỗi thì để trống và ghi Error Log."""
	try:
		mst = mst_cua_hoa_don(doc)
		if not mst:
			ma = KHACH_LE
		else:
			ma = ma_theo_mst("Customer", mst, ten=doc.get("vgb_xhd_ten") or doc.get("customer_name"), tao_moi=True)
		if ma and ma != (doc.get("vgb_ma_khach_ke_toan") or ""):
			doc.vgb_ma_khach_ke_toan = ma
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ma_ke_toan: dien ma khach %s" % doc.get("name"))


def cap_ma_khi_luu(doc, method=None):
	"""Hook after_insert / on_update của Customer và Supplier: có MST mà chưa
	có mã thì cấp mã ngay, để danh mục không có đối tác công ty nào thiếu
	mã. Không chặn lưu."""
	try:
		if chuan_mst(doc.get("tax_id")) and not str(doc.get(O_MA[doc.doctype]) or "").strip():
			ma = cap_ma(doc.doctype, doc.name)
			doc.set(O_MA[doc.doctype], ma)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ma_ke_toan: cap ma %s %s" % (doc.doctype, doc.get("name")))


def bang_ma_theo_mst(ds_mst):
	"""{mst_chuan: mã} cho một loạt MST, dùng cho sổ hoá đơn. Chỉ đọc."""
	mst_ds = sorted({chuan_mst(m) for m in ds_mst or [] if chuan_mst(m)})
	if not mst_ds:
		return {}
	ung = set(mst_ds) | {m.replace("-", "") for m in mst_ds if "-" in m}
	ra = {}
	for r in frappe.get_all("Customer", filters={"tax_id": ["in", sorted(ung)]},
			fields=["tax_id", "custom_ma_khach"], order_by="creation asc", limit_page_length=0):
		k = chuan_mst(r.get("tax_id"))
		if k and k not in ra and str(r.get("custom_ma_khach") or "").strip():
			ra[k] = str(r["custom_ma_khach"]).strip().upper()
	return ra


VAI_NAP = {"System Manager", "Accounts Manager"}


@frappe.whitelist(methods=["POST"])
def nap_danh_muc_fast(dong, tao_moi=0):
	"""Nạp danh mục khách và NCC xuất từ Fast: dòng dạng {ma, ten, mst, dia_chi}.
	Chỉ ghi ô mã cho bản ghi đang trống mã; mã lệch thì trả về xung đột."""
	import json
	if not (set(frappe.get_roles()) & VAI_NAP):
		frappe.throw("Chỉ kế toán trưởng hoặc quản trị được nạp danh mục mã.")
	rows = json.loads(dong) if isinstance(dong, str) else dong
	hien_co = {}
	for dt in ("Customer", "Supplier"):
		hien_co[dt] = {}
		for r in frappe.get_all(dt, filters={"tax_id": ["is", "set"]}, fields=["name", "tax_id", O_MA[dt]],
				order_by="creation asc", limit_page_length=0):
			k = chuan_mst(r.get("tax_id"))
			if k and k not in hien_co[dt]:
				hien_co[dt][k] = {"name": r["name"], "ma": r.get(O_MA[dt]) or ""}
	ma_dang_dung = {}
	for dt in ("Customer", "Supplier"):
		ma_dang_dung[dt] = {}
		for r in frappe.get_all(dt, filters={O_MA[dt]: ["is", "set"]}, fields=["tax_id", O_MA[dt]],
				limit_page_length=0):
			m = str(r.get(O_MA[dt]) or "").strip().upper()
			if m:
				ma_dang_dung[dt].setdefault(m, chuan_mst(r.get("tax_id")))
	kh = ke_hoach_nap(rows, hien_co, ma_dang_dung)
	for d in kh["cap_nhat"]:
		frappe.db.set_value(d["loai"], d["name"], O_MA[d["loai"]], d["ma"], update_modified=False)
	tao = 0
	if cint(tao_moi):
		for d in kh["tao_moi"]:
			try:
				ten = _tao_doi_tac(d["loai"], d["mst"], d["ten"] or d["ma"])
				frappe.db.set_value(d["loai"], ten, O_MA[d["loai"]], d["ma"], update_modified=False)
				tao += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ma_ke_toan: tao %s %s" % (d["loai"], d["ma"]))
	# Từ đây máy được cấp mã nối tiếp; hoá đơn cũ đang trống mã thì điền
	# theo danh mục vừa nạp.
	frappe.defaults.set_global_default(KHOA_DA_NAP, "1")
	dien = dien_ma_hang_loat()
	frappe.db.commit()
	return {"cap_nhat": len(kh["cap_nhat"]), "tao_moi": tao, "chua_tao": len(kh["tao_moi"]) - tao,
		"giu": kh["giu"], "xung_dot": kh["xung_dot"], "hoa_don_dien_ma": dien}


def dien_ma_hang_loat():
	"""Điền ô Mã khách kế toán cho mọi hoá đơn bán đang trống ô đó, chỉ từ
	dữ liệu có sẵn: KL0001 khi không có MST nào, mã Fast của khách mang MST
	xuất hoá đơn, không thì mã của chính khách hàng. Không tạo khách, không
	cấp mã mới, không chạm ô nào khác của tờ. Lặp lại được. Trả số tờ đã điền.
	Dùng chung cho patch v536 và lượt nạp danh mục (một nguồn, điều 18)."""
	truoc = frappe.db.count("Sales Invoice", {"vgb_ma_khach_ke_toan": ["is", "set"]})
	o = O_MA["Customer"]
	# Ô mã Fast là ô khai trên site (06/08/2026); bench mới không có thì chỉ
	# điền được khách lẻ.
	if frappe.db.has_column("Customer", o):
		# 1. Theo MST xuất hoá đơn: khách nào mang MST đó (cả dạng có gạch và
		#    không gạch) và đã có mã.
		frappe.db.sql("""update `tabSales Invoice` hd
			join `tabCustomer` k on replace(k.tax_id, '-', '') = replace(hd.vgb_xhd_mst, '-', '')
				and ifnull(k.`%s`, '') <> ''
			set hd.vgb_ma_khach_ke_toan = upper(trim(k.`%s`))
			where ifnull(hd.vgb_ma_khach_ke_toan, '') = '' and ifnull(hd.vgb_xhd_mst, '') <> ''""" % (o, o))
		# 2. Không có MST xuất hoá đơn: theo MST của chính khách hàng.
		frappe.db.sql("""update `tabSales Invoice` hd
			join `tabCustomer` k on k.name = hd.customer and ifnull(k.tax_id, '') <> '' and ifnull(k.`%s`, '') <> ''
			set hd.vgb_ma_khach_ke_toan = upper(trim(k.`%s`))
			where ifnull(hd.vgb_ma_khach_ke_toan, '') = '' and ifnull(hd.vgb_xhd_mst, '') = ''""" % (o, o))
	# 3. Không MST ở đâu cả: khách lẻ.
	frappe.db.sql("""update `tabSales Invoice` hd
		left join `tabCustomer` k on k.name = hd.customer
		set hd.vgb_ma_khach_ke_toan = %s
		where ifnull(hd.vgb_ma_khach_ke_toan, '') = '' and ifnull(hd.vgb_xhd_mst, '') = ''
			and ifnull(k.tax_id, '') = ''""", (KHACH_LE,))
	return frappe.db.count("Sales Invoice", {"vgb_ma_khach_ke_toan": ["is", "set"]}) - truoc


TRUONG_MOI = {
	"Sales Invoice": [
		{"fieldname": "vgb_ma_khach_ke_toan", "label": "Mã khách kế toán", "fieldtype": "Data",
			"insert_after": "vgb_xhd_mst", "read_only": 1, "in_standard_filter": 1, "in_list_view": 0,
			"description": "KL0001 là khách lẻ không lấy hoá đơn; có mã số thuế thì là mã Fast của công ty. Máy điền khi lưu."},
	],
}
