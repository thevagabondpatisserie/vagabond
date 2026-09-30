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


def ma_ke_tiep(cac_ma, tien_to, rong=RONG_MA, san=0):
	"""Mã kế tiếp sau mã lớn nhất trong danh sách. Danh sách trống thì bắt
	đầu từ 1. Mã không đúng dạng (KL0001, chữ, rỗng) không tính. `san` là
	số lớn nhất Fast đang giữ (kể cả mã chưa có bản ghi ERP), mã cấp ra
	phải vượt cả sàn đó."""
	lon_nhat = max([so_cua_ma(m, tien_to) for m in (cac_ma or [])] + [0, int(san or 0)])
	return "%s%0*d" % (tien_to, rong, lon_nhat + 1)


def san_cua_tep(dong_ds):
	"""{loai: số lớn nhất} của MỌI mã KH và NC trong tệp Fast, kể cả dòng
	sẽ không được tạo bản ghi (tao_moi=0) hay không có MST. Codex #383 F1:
	dòng bị bỏ qua vẫn là mã Fast đang dùng, máy cấp đè lên là trùng."""
	ra = {}
	for d in dong_ds or []:
		ma = str(d.get("ma") or "").strip().upper()
		for loai, tt in TIEN_TO.items():
			if la_ma(ma, tt):
				ra[loai] = max(ra.get(loai, 0), so_cua_ma(ma, tt))
	return ra


def ma_ke_toan_cua_hoa_don(mst, tra_ma):
	"""Mã khách kế toán của một tờ hoá đơn. tra_ma(mst_chuan) trả mã của
	khách có mã số thuế đó, hoặc rỗng. Không MST là khách lẻ KL0001."""
	m = chuan_mst(mst)
	if not m:
		return KHACH_LE
	return str(tra_ma(m) or "").strip().upper()


def loi_tep_danh_muc(dong_ds):
	"""Tệp danh mục Fast có đủ để bật cấp mã nối tiếp không. THUẦN.

	Trả lời nhắn cho người nạp, hoặc rỗng nếu đủ. Codex #389 (P1): tệp rỗng,
	hay tệp mà mọi dòng đều bị loại, không lập được sàn mã Fast nào, vậy mà
	bản trước vẫn bật cờ "đã nạp"; máy liền cấp mã từ số lớn nhất của ERP,
	thấp hơn Fast, và cấp trùng mã Fast đang dùng. Tệp chỉ có một loại mã
	(ví dụ chỉ khách) thì vẫn nhận, nhưng cap_ma chỉ cấp cho loại ĐÃ có sàn."""
	if san_cua_tep(dong_ds):
		return ""
	return ("Tệp danh mục không có mã KH hay NC hợp lệ nào nên chưa bật cấp mã nối tiếp. "
		"Xuất lại danh mục khách hoặc nhà cung cấp từ Fast (cột mã, tên, MST, địa chỉ) rồi nạp lại.")


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

	hien_co: {loai: {mst_chuan: {"name", "ma", "cac_ma"}}}; cac_ma gồm mọi
	mã ERP cùng MST, name/ma là bản ghi đầu để điền khi không xung đột.
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
	# Codex #389 (P1): một MST trong tệp chỉ được một mã. Dòng lặp y hệt thì
	# xử một lần (không sinh hai lần tạo mới); một MST mang hai mã khác nhau
	# thì cả MST đó là xung đột, không ghi gì cho nó, để người quyết.
	sach = doc_tep_fast(dong_ds)
	ma_cua_mst, mst_cua_ma = {}, {}
	for d in sach:
		ma_cua_mst.setdefault((d["loai"], d["mst"]), set()).add(d["ma"])
		mst_cua_ma.setdefault((d["loai"], d["ma"]), set()).add(d["mst"])
	da_xu, ma_da_bao = set(), set()
	for d in sach:
		km = (d["loai"], d["mst"])
		k = (d["loai"], d["ma"])
		# Codex #389 (P2 vòng 3): một mã gắn cho nhiều MST thì loại MỌI dòng của
		# mã đó khỏi kế hoạch ghi, kể cả dòng đứng trước. Để thứ tự dòng trong
		# tệp quyết định mã về tay ai là sai.
		if len(mst_cua_ma[k]) > 1:
			if k not in ma_da_bao:
				ma_da_bao.add(k)
				ra["xung_dot"].append(dict(d, ly_do="mã %s gắn cho %d MST trong tệp: %s" % (
					d["ma"], len(mst_cua_ma[k]), ", ".join(sorted(mst_cua_ma[k])))))
			continue
		if len(ma_cua_mst[km]) > 1:
			if km not in da_xu:
				da_xu.add(km)
				ra["xung_dot"].append(dict(d, ly_do="MST %s mang %d mã trong tệp: %s" % (
					d["mst"], len(ma_cua_mst[km]), ", ".join(sorted(ma_cua_mst[km])))))
			continue
		if km in da_xu:
			continue
		da_xu.add(km)
		co = (hien_co.get(d["loai"]) or {}).get(d["mst"])
		chu_khac = (ma_dang_dung.get(d["loai"]) or {}).get(d["ma"])
		chu_ds = set(chu_khac) if isinstance(chu_khac, (set, list, tuple)) else ({chu_khac} if chu_khac is not None else set())
		if chu_ds - {d["mst"]}:
			ra["xung_dot"].append(dict(d, ly_do="ERP đang dùng mã %s cho đối tác khác (MST %s)" % (d["ma"], ", ".join(sorted(m or "trống" for m in chu_ds)))))
			continue
		ma_ds = {str(m or "").strip().upper() for m in (co.get("cac_ma", [co.get("ma")]) if co else []) if str(m or "").strip()}
		if ma_ds - {d["ma"]}:
			ra["xung_dot"].append(dict(d, name=co["name"], ma_erp=", ".join(sorted(ma_ds)),
				ly_do="ERP đang giữ %s, tệp ghi %s" % (", ".join(sorted(ma_ds)), d["ma"])))
		elif not co:
			ra["tao_moi"].append(d)
		elif not str(co.get("ma") or "").strip():
			ra["cap_nhat"].append(dict(d, name=co["name"]))
		else:
			ra["giu"] += 1
	return ra


import frappe
from frappe.utils import cint


def _ban_ghi_mst(doctype, ds_mst):
	"""Tra tất cả cách viết MST mà chuan_mst chấp nhận, không lấy dòng đầu."""
	o = O_MA[doctype]  # Chỉ Customer/Supplier, không nhận tên bảng/cột tùy ý.
	mst = sorted({chuan_mst(m).replace("-", "") for m in ds_mst if chuan_mst(m)})
	if not mst:
		return []
	return frappe.db.sql("""select name, tax_id, `%s` from `tab%s`
		where regexp_replace(ifnull(tax_id, ''), '[^0-9]', '') in %%s
		order by creation asc, name asc""" % (o, doctype), (tuple(mst),), as_dict=True)


def _tra_theo_mst(doctype, mst):
	r = _ban_ghi_mst(doctype, [mst])
	if not r:
		return None
	ma = ma_dung_lai([d.get(O_MA[doctype]) for d in r])
	return {"name": r[0]["name"], "ma": ma or "", "xung_dot": ma is None}


KHOA_DA_NAP = "vgb_ma_ke_toan_da_nap"
# Sàn mã Fast theo tiền tố, ghi lúc nạp tệp: khoá mặc định "vgb_ma_ke_toan_san_KH".
KHOA_SAN = "vgb_ma_ke_toan_san_"


def da_nap_danh_muc():
	"""Danh mục Fast đã được nạp lần đầu chưa. Trước đó máy KHÔNG cấp mã
	mới: danh mục Fast của chị Dung đi trước ERP (KH001588 so với KH001382
	ngày 29/09/2026), cấp trước khi nạp là hai công ty chung một mã."""
	return str(frappe.db.get_default(KHOA_DA_NAP) or "") == "1"


def _nha_khoa():
	frappe.db.sql("select release_lock(%s)", (KHOA_CAP_MA,))


def ma_dung_lai(cac_ma):
	"""Mã đã cấp của các bản ghi khác cùng MST. THUẦN. Rỗng: chưa ai có mã,
	được cấp mới. Một mã: dùng lại. Nhiều mã khác nhau: None, xung đột."""
	ds = {str(m or "").strip().upper() for m in cac_ma or [] if str(m or "").strip()}
	if not ds:
		return ""
	return ds.pop() if len(ds) == 1 else None


def cap_ma(doctype, name):
	"""Cấp mã kế tiếp cho một khách hoặc NCC chưa có mã. Đã có mã thì trả
	mã đang có. Chưa nạp danh mục Fast thì trả rỗng, không cấp.

	Khoá tên toàn site (GET_LOCK) trong lúc đọc mã lớn nhất, và GIỮ KHOÁ TỚI
	LÚC COMMIT hoặc ROLLBACK chứ không nhả ngay trong hàm (Codex #383 F2):
	mã vừa ghi chỉ thấy được với lượt khác sau khi commit, nhả sớm là lượt
	sau đọc mã lớn nhất cũ và tính ra cùng một mã. Không lấy được khoá
	(lượt khác giữ quá 10 giây) thì ném, không cấp bừa."""
	o = O_MA[doctype]
	hien = str(frappe.db.get_value(doctype, name, o) or "").strip()
	if hien:
		return hien
	if not da_nap_danh_muc():
		return ""
	duoc = frappe.db.sql("select get_lock(%s, 10)", (KHOA_CAP_MA,))
	if not duoc or cint(duoc[0][0]) != 1:
		frappe.throw("Không lấy được khoá cấp mã kế toán, thử lưu lại sau vài giây.")
	frappe.db.after_commit.add(_nha_khoa)
	frappe.db.after_rollback.add(_nha_khoa)
	hien = str(frappe.db.get_value(doctype, name, o) or "").strip()
	if hien:
		return hien
	# Codex #389 (P1 vòng 4): cùng một MST chỉ một mã. Bản ghi khác cùng MST
	# đã có mã thì dùng lại mã đó; có nhiều mã khác nhau thì không cấp gì, để
	# người gộp. Đọc SAU khi giữ khoá, nên hai lượt lưu nối tiếp cùng MST
	# không thể mỗi lượt cấp một mã.
	mst = chuan_mst(frappe.db.get_value(doctype, name, "tax_id"))
	if mst:
		cung = [r.get(o) for r in _ban_ghi_mst(doctype, [mst]) if r.get("name") != name]
		dung_lai = ma_dung_lai(cung)
		if dung_lai is None:
			return ""
		if dung_lai:
			frappe.db.set_value(doctype, name, o, dung_lai, update_modified=False)
			return dung_lai
	tien_to = TIEN_TO[doctype]
	san = frappe.db.get_default(KHOA_SAN + tien_to)
	if not cint(san):
		# Chưa nạp danh mục Fast cho loại mã này (Codex #389 P1): không có sàn
		# thì mã lớn nhất của ERP thấp hơn Fast, cấp là trùng mã Fast.
		return ""
	cac_ma = [r[0] for r in frappe.db.sql(
		"select `%s` from `tab%s` where `%s` like %%s" % (o, doctype, o), (tien_to + "%",))]
	ma = ma_ke_tiep(cac_ma, tien_to, san=san)
	frappe.db.set_value(doctype, name, o, ma, update_modified=False)
	return ma


def ma_theo_mst(doctype, mst, ten="", tao_moi=False):
	"""Mã kế toán của đối tác mang MST này; chưa có mã thì cấp; chưa có
	bản ghi thì tạo khi tao_moi. Rỗng khi không tìm ra và không tạo."""
	co = _tra_theo_mst(doctype, mst)
	if not co and tao_moi and ten:
		co = {"name": _tao_doi_tac(doctype, mst, ten), "ma": ""}
	if not co or co.get("xung_dot"):
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
	# Xóa giá trị dẫn xuất cũ cả khi tra mã lỗi; không để KL0001 bám vào MST mới.
	doc.vgb_ma_khach_ke_toan = ""
	try:
		mst = mst_cua_hoa_don(doc)
		if not mst:
			ma = KHACH_LE
		else:
			ma = ma_theo_mst("Customer", mst, ten=doc.get("vgb_xhd_ten") or doc.get("customer_name"), tao_moi=True)
		if ma != (doc.get("vgb_ma_khach_ke_toan") or ""):
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
	ra = {}
	for r in _ban_ghi_mst("Customer", mst_ds):
		k = chuan_mst(r.get("tax_id"))
		if k:
			ra.setdefault(k, []).append(r.get("custom_ma_khach"))
	return {k: ma for k, ds in ra.items() if (ma := ma_dung_lai(ds))}


VAI_NAP = {"System Manager", "Accounts Manager"}


@frappe.whitelist(methods=["POST"])
def nap_danh_muc_fast(dong, tao_moi=0):
	"""Nạp danh mục khách và NCC xuất từ Fast: dòng dạng {ma, ten, mst, dia_chi}.
	Chỉ ghi ô mã cho bản ghi đang trống mã; mã lệch thì trả về xung đột."""
	import json
	if not (set(frappe.get_roles()) & VAI_NAP):
		frappe.throw("Chỉ kế toán trưởng hoặc quản trị được nạp danh mục mã.")
	rows = json.loads(dong) if isinstance(dong, str) else dong
	loi = loi_tep_danh_muc(rows)
	if loi:
		# Chặn TRƯỚC mọi lần ghi: cờ "đã nạp" chưa bật thì máy chưa cấp mã.
		frappe.throw(loi)
	hien_co = {}
	for dt in ("Customer", "Supplier"):
		hien_co[dt] = {}
		for r in frappe.get_all(dt, filters={"tax_id": ["is", "set"]}, fields=["name", "tax_id", O_MA[dt]],
				order_by="creation asc", limit_page_length=0):
			k = chuan_mst(r.get("tax_id"))
			if k:
				co = hien_co[dt].setdefault(k, {"name": r["name"], "ma": r.get(O_MA[dt]) or "", "cac_ma": []})
				co["cac_ma"].append(r.get(O_MA[dt]) or "")
	ma_dang_dung = {}
	for dt in ("Customer", "Supplier"):
		ma_dang_dung[dt] = {}
		for r in frappe.get_all(dt, filters={O_MA[dt]: ["is", "set"]}, fields=["tax_id", O_MA[dt]],
				limit_page_length=0):
			m = str(r.get(O_MA[dt]) or "").strip().upper()
			if m:
				ma_dang_dung[dt].setdefault(m, set()).add(chuan_mst(r.get("tax_id")))
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
	# Sàn mã Fast: giữ số lớn nhất của MỌI dòng trong tệp, kể cả dòng bị bỏ
	# qua, để máy không bao giờ cấp lại một mã Fast đang dùng (Codex #383 F1).
	# Chỉ nâng, không hạ: tệp nạp lần sau cũ hơn cũng không kéo sàn xuống.
	for loai, so in san_cua_tep(rows).items():
		tt = TIEN_TO[loai]
		cu = cint(frappe.db.get_default(KHOA_SAN + tt) or 0)
		if so > cu:
			frappe.defaults.set_global_default(KHOA_SAN + tt, str(so))
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
		# Gom mã trên TOÀN BỘ MST trước khi nối vào hóa đơn. Một MST nhiều
		# mã thì bỏ cả nhóm, không để kế hoạch JOIN chọn một mã tùy ý (#389).
		# REGEXP_REPLACE cùng chuẩn bỏ ký tự không phải số của chuan_mst.
		bang = """(select regexp_replace(ifnull(tax_id, ''), '[^0-9]', '') as mst,
			min(upper(trim(`%s`))) as ma from `tabCustomer`
			where ifnull(trim(`%s`), '') <> ''
			group by mst having length(mst) in (10, 12, 13)
			and count(distinct upper(trim(`%s`))) = 1)""" % (o, o, o)
		# 1. MST trên hóa đơn ưu tiên; 2. không khai mới xét khách của đơn.
		frappe.db.sql("""update `tabSales Invoice` hd
			join %s k on k.mst = regexp_replace(ifnull(hd.vgb_xhd_mst, ''), '[^0-9]', '')
			set hd.vgb_ma_khach_ke_toan = k.ma
			where ifnull(hd.vgb_ma_khach_ke_toan, '') = '' and ifnull(hd.vgb_xhd_mst, '') <> ''""" % bang)
		frappe.db.sql("""update `tabSales Invoice` hd
			join `tabCustomer` chu on chu.name = hd.customer
			join %s k on k.mst = regexp_replace(ifnull(chu.tax_id, ''), '[^0-9]', '')
			set hd.vgb_ma_khach_ke_toan = k.ma
			where ifnull(hd.vgb_ma_khach_ke_toan, '') = '' and ifnull(hd.vgb_xhd_mst, '') = ''""" % bang)
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
