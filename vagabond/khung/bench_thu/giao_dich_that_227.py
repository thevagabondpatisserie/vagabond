"""#227 v447: chứng minh trạng thái cờ chờ đối chiếu SAU KHI request kết thúc.

Khác với `cua.chay` (savepoint, cấm commit), kịch bản này CÓ commit và
CÓ rollback thật, vì đây chính là điều cần chứng minh: gỡ cờ rồi
frappe.throw thì Frappe rollback cả request, việc gỡ cờ có bị cuốn theo
hay không chỉ đọc lại DB bằng một KẾT NỐI KHÁC mới biết.

Bởi vậy nó CHỈ chạy trên bench thử (site_config `vagabond_bench_thu: 1`),
không bao giờ trên site thật. HTTP tới M-Invoice và Pancake được thay
bằng bản giả ngay trong tiến trình; không gói tin nào ra ngoài.

Mỗi bước mô phỏng đúng vòng đời một request Frappe: gọi hàm, nếu ném lỗi
thì `frappe.db.rollback()` như frappe/app.py làm, rồi đọc DB bằng pymysql
kết nối riêng.

Chạy:
    bench --site <site-thu> execute vagabond.khung.bench_thu.giao_dich_that_227.chay
"""

import json

import frappe
from frappe.utils import today

from vagabond import minvoice_an_toan as at
from vagabond import minvoice_kich_ban as kb

KQ = []


def _khoa():
	if not frappe.conf.get("vagabond_bench_thu"):
		frappe.throw("giao_dich_that_227 chỉ chạy trên bench thử có vagabond_bench_thu=1.")


def _ghi(nhan, duoc, mong):
	ok = duoc == mong
	KQ.append(("DAT" if ok else "HONG", nhan, duoc, mong))
	return ok


# ---------------------------------------------------------------- đọc DB bằng kết nối riêng

def _doc_rieng(sql, args=()):
	import pymysql
	c = frappe.conf
	ket_noi = pymysql.connect(host=c.get("db_host") or "127.0.0.1", port=int(c.get("db_port") or 3306),
		user=c.db_user or c.db_name, password=c.db_password, database=c.db_name, charset="utf8mb4")
	try:
		with ket_noi.cursor() as cur:
			cur.execute(sql, args)
			return cur.fetchall()
	finally:
		ket_noi.close()


def _trang_thai(si):
	r = _doc_rieng("select vgb_hddt_cho_doi_chieu, custom_hddt_id, custom_minvoice_id, custom_hddt_so, custom_hddt_trang_thai from `tabSales Invoice` where name=%s", (si,))
	cm = _doc_rieng("select count(*) from `tabComment` where reference_doctype='Sales Invoice' and reference_name=%s and comment_type='Comment' and content like %s", (si, "%M-Invoice từ chối%"))
	return {"co": int(r[0][0] or 0), "hddt_id": r[0][1] or "", "minvoice_id": r[0][2] or "", "so": r[0][3] or "", "tt": r[0][4] or "", "vet": int(cm[0][0])}


# ---------------------------------------------------------------- HTTP giả

class _PhanHoi:
	def __init__(self, than, ma=200):
		self.than, self.status_code = than, ma

	def raise_for_status(self):
		if self.status_code >= 400:
			raise RuntimeError("HTTP %s" % self.status_code)

	def json(self):
		return self.than


class RequestsGia:
	"""Thay `vagabond.ban_hang.requests`. `kich_ban` quyết định Save trả gì."""

	def __init__(self):
		self.kich_ban = "ok"
		self.so_save = 0

	def post(self, url, **kw):
		if url.endswith("/api/Account/Login"):
			return _PhanHoi({"code": "00", "ok": True, "token": "token-gia"})
		if url.endswith("/api/InvoiceApi78/Save"):
			self.so_save += 1
			return _tra(self.kich_ban)
		raise RuntimeError("URL lạ " + url)

	def get(self, url, **kw):
		raise RuntimeError("không có GET trong kịch bản này")


def _tra(kich_ban):
	if kich_ban == "timeout":
		raise TimeoutError("Read timed out. (read timeout=30)")
	if kich_ban == "ok":
		return _PhanHoi({"code": "00", "ok": True, "message": "Thành công", "data": {"inv_invoiceAuth_id": "gia-" + frappe.generate_hash(length=8),
			"inv_invoiceNumber": 227, "sobaomat": "ABCD1234", "tthai": "Chờ ký"}})
	if kich_ban == "tu_choi":
		return _PhanHoi({"code": "296", "ok": False, "message": "Create invoice fail"})
	if kich_ban == "ma_la":
		return _PhanHoi({"code": "99", "ok": False, "message": "Loi khac"})
	if kich_ban == "trung":
		return _PhanHoi({"code": "296", "ok": False, "message": "Hoa don da ton tai"})
	if kich_ban == "296_co_so":
		# Mẫu giả Codex nêu 08/09 để kiểm độ bền, không phải phản hồi thật.
		return _PhanHoi({"code": "296", "ok": False, "message": "Create invoice fail", "data": {"inv_invoiceNumber": "123"}})
	if kich_ban == "296_data_list":
		return _PhanHoi({"code": "296", "data": [{"inv_invoiceAuth_id": "DA-TAO"}]})
	raise ValueError(kich_ban)


# ---------------------------------------------------------------- dựng phiếu

def _si(ma_don, pid, ten="Công ty TNHH Kiểm Thử 227", mst="0311234567"):
	cty = frappe.db.get_value("Company", {"name": ["!=", ""]}, "name")
	kh = frappe.db.get_value("Customer", {"disabled": 0}, "name")
	mon = frappe.db.get_value("Item", {"is_sales_item": 1, "disabled": 0}, "name")
	hd = frappe.new_doc("Sales Invoice")
	hd.update({"company": cty, "customer": kh, "posting_date": today(), "due_date": today(), "currency": "VND",
		"conversion_rate": 1, "update_stock": 0, "ignore_pricing_rule": 1, "custom_nguon": "Pancake",
		"custom_pancake_display_id": ma_don, "custom_pancake_id": pid, "vgb_xhd_ten": ten, "vgb_xhd_mst": mst,
		"vgb_pt_thanh_toan": "Chuyển khoản"})
	hd.set("taxes", [])
	hd.append("items", {"item_code": mon, "qty": 1, "rate": 1900000})
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	hd.submit()
	frappe.db.commit()
	return hd.name


def _don_dep(ds):
	for ten in ds:
		try:
			hd = frappe.get_doc("Sales Invoice", ten)
			if hd.docstatus == 1:
				hd.flags.ignore_permissions = True
				hd.cancel()
			# App cấm xoá chứng từ (quy tắc chung), phiếu thử để lại ở trạng thái huỷ trên bench.
		except Exception as e:
			KQ.append(("GHI", "dọn " + ten, str(e)[:100], ""))
	frappe.db.commit()


def _request(ham, *a, **kw):
	"""Mô phỏng vòng đời request: lỗi thì rollback như frappe/app.py."""
	try:
		ra = ham(*a, **kw)
		frappe.db.commit()
		return ra, None
	except Exception as e:
		frappe.db.rollback()
		frappe.local.message_log = []
		return None, str(e)


# ---------------------------------------------------------------- đường Python

def _duong_python():
	from vagabond import ban_hang
	st = frappe.get_doc("Vagabond Settings")
	st.db_set("minvoice_host", "https://minvoice.invalid", update_modified=False)
	st.db_set("minvoice_username", "thu", update_modified=False)
	st.db_set("tu_xuat_hddt", 0, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache()
	gia = RequestsGia()
	goc = ban_hang.requests
	ban_hang.requests = gia
	si = _si("227", "ID-227")
	try:
		# 1. Từ chối rõ (296): sau request, cờ phải = 0 và có vết Comment.
		gia.kich_ban = "tu_choi"
		_ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
		tt = _trang_thai(si)
		_ghi("PY1 từ chối: request ném lỗi", bool(loi), True)
		_ghi("PY1 từ chối: cờ đọc lại bằng kết nối khác", tt["co"], 0)
		_ghi("PY1 từ chối: có vết Comment", tt["vet"], 1)
		_ghi("PY1 từ chối: chưa có ID", tt["hddt_id"], "")
		_ghi("PY1 từ chối: đã gọi Save đúng 1 lần", gia.so_save, 1)
		# 2. Kế toán sửa MST rồi gửi lại, lần này timeout: cờ phải giữ = 1.
		frappe.db.set_value("Sales Invoice", si, "vgb_xhd_mst", "0311234568", update_modified=False)
		frappe.db.commit()
		gia.kich_ban = "timeout"
		_ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
		tt = _trang_thai(si)
		_ghi("PY2 timeout: request ném lỗi", bool(loi), True)
		_ghi("PY2 timeout: cờ giữ 1 sau rollback", tt["co"], 1)
		_ghi("PY2 timeout: Save gọi thêm 1 lần", gia.so_save, 2)
		# 3. Thử lại ngay: bị chặn TRƯỚC HTTP, không gọi Save, không tạo đúp.
		gia.kich_ban = "ok"
		_ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
		_ghi("PY3 thử lại khi chờ đối chiếu: bị chặn", "đối chiếu" in (loi or "") or "đã gửi" in (loi or "").lower(), True)
		_ghi("PY3 thử lại: KHÔNG gọi Save", gia.so_save, 2)
		_ghi("PY3 thử lại: cờ vẫn 1", _trang_thai(si)["co"], 1)
		# 4. Mã lạ và trùng cũng giữ cờ (qua mo_lai trước để gửi được).
		for kb_ in ("ma_la", "trung", "296_co_so", "296_data_list"):
			_request(at.mo_lai, si, "Kế toán đã kiểm theo mã phiếu, chưa có hoá đơn bên M-Invoice", 1)
			_ghi("PY4 mở lại trước " + kb_, _trang_thai(si)["co"], 0)
			gia.kich_ban = kb_
			_ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
			_ghi("PY4 %s: ném lỗi" % kb_, bool(loi), True)
			_ghi("PY4 %s: giữ cờ 1" % kb_, _trang_thai(si)["co"], 1)
		# 5. Giám đốc đối chiếu, mở lại, gửi thành công: có ID, cờ 0.
		_request(at.mo_lai, si, "Kế toán đã kiểm theo mã phiếu, chưa có hoá đơn bên M-Invoice", 1)
		_ghi("PY5 mở lại sau đối chiếu", _trang_thai(si)["co"], 0)
		gia.kich_ban = "ok"
		ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
		tt = _trang_thai(si)
		_ghi("PY5 thành công: không lỗi", loi, None)
		_ghi("PY5 thành công: có ID", bool(tt["hddt_id"]), True)
		_ghi("PY5 thành công: cờ 0", tt["co"], 0)
		_ghi("PY5 thành công: trạng thái Chờ ký", tt["tt"], "Chờ ký")
		# 6. Gửi lại sau khi có ID: chặn, không gọi Save.
		so = gia.so_save
		_ra, loi = _request(ban_hang.xuat_hoa_don_dien_tu, si)
		_ghi("PY6 đã có ID: chặn", bool(loi), True)
		_ghi("PY6 đã có ID: không gọi Save", gia.so_save, so)
	finally:
		ban_hang.requests = goc
		_don_dep([si])


# ---------------------------------------------------------------- đường Server Script

def _dung_server_script(tinh_huong="moi"):
	"""Đặt hai Server Script về bản gốc / v446 / mới, có commit."""
	for ten, loai, cu, sua in kb.BO:
		goc = kb.ban_goc(loai)
		ma = {"goc": goc, "v446": cu(goc), "moi": sua(goc)}[tinh_huong]
		if frappe.db.exists("Server Script", ten):
			doc = frappe.get_doc("Server Script", ten)
		else:
			doc = frappe.new_doc("Server Script")
			doc.name = ten
			doc.script_type = "API"
			doc.api_method = "vgb_" + loai + "_kiem"
		doc.disabled = 0
		doc.script = ma
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
	frappe.db.commit()


def _duong_script():
	from frappe.integrations import utils as iu
	_dung_server_script("moi")
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "api2_base", "https://minvoice.invalid")
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "api2_username", "thu")
	st = frappe.get_doc("MInvoice Phat Hanh Settings")
	st.api2_password = "mat-khau-gia"
	st.save(ignore_permissions=True)
	from frappe.utils.password import set_encrypted_password
	frappe.db.set_single_value("Vagabond Settings", "pancake_shop_id", "shop-gia")
	set_encrypted_password("Vagabond Settings", "Vagabond Settings", "khoa-gia", "pancake_api_key")
	frappe.db.commit()
	frappe.clear_cache()
	kich_ban = {"save": "ok"}
	dem = {"save": 0, "pancake": []}
	# Đúng như Pancake của tiệm trả về (đo 08/09/2026): display_id null, id là số.
	don_khac = {"id": 91227, "display_id": None, "note_print": "Tên công ty: Công ty người khác\nMST: 0399999999\nEmail: khac@example.com"}
	don_dung = {"id": 227, "display_id": None, "note_print": "Tên công ty: Công ty TNHH Kiểm Thử 227\nMST: 0311234567\nEmail: dung@example.com"}

	def post_gia(url, data=None, headers=None, **kw):
		if url.endswith("/api/Account/Login"):
			return {"code": "00", "ok": True, "token": "token-gia"}
		if url.endswith("/api/InvoiceApi78/Save"):
			dem["save"] += 1
			return _tra(kich_ban["save"]).than
		raise RuntimeError("URL lạ " + url)

	trang_day = [{"id": 1000 + i, "display_id": None, "note_print": ""} for i in range(50)]
	che_do_pancake = {"day": False}

	def get_gia(url, headers=None, params=None, **kw):
		dem["pancake"].append((url.rsplit("/", 1)[1], dict(params or {})))
		if url.endswith("/orders/227"):
			return {"data": don_dung, "success": True}
		if url.endswith("/orders"):
			if che_do_pancake["day"]:
				# Mọi trang đều đầy 50, total_pages 6; trang 1 có 227. Chưa đọc hết.
				so = int((params or {}).get("page_number") or 1)
				return {"data": (([don_dung] + trang_day[:49]) if so == 1 else trang_day), "total_pages": 6, "total_entries": 300, "page_number": so, "page_size": 50, "success": True}
			return {"data": [don_khac, don_dung], "total_pages": 1, "total_entries": 2, "page_number": 1, "page_size": 50, "success": True}
		return {}

	goc_post, goc_get = iu.make_post_request, iu.make_get_request
	iu.make_post_request, iu.make_get_request = post_gia, get_gia
	si = _si("227", "227", ten="", mst="")
	si2 = _si("227", "", ten="", mst="")
	si3 = _si("227", "", ten="", mst="")

	def chay_script(phieu):
		frappe.local.form_dict = frappe._dict({"phieu": phieu, "che_do": "day"})
		# Như frappe.init trong một request thật: response có sẵn khoá docs,
		# safe_exec chỉ đưa frappe.response vào script khi nó không rỗng.
		frappe.local.response = frappe._dict({"docs": []})
		frappe.get_doc("Server Script", kb.TEN_PHAT_HANH).execute_method()
		return dict(frappe.local.response.get("message") or {})

	try:
		# 1. Từ chối rõ: script tự gỡ cờ và commit, DB đọc lại = 0, có vết.
		kich_ban["save"] = "tu_choi"
		ra, loi = _request(chay_script, si)
		tt = _trang_thai(si)
		_ghi("SS1 từ chối: script không ném lỗi", loi, None)
		if loi:
			print("SS1 loi:", loi[:2000])
			return
		_ghi("SS1 từ chối: báo đã mở lại", any("mo lai" in x for x in ra.get("loi", [])), True)
		_ghi("SS1 từ chối: cờ 0 đọc lại", tt["co"], 0)
		_ghi("SS1 từ chối: có vết", tt["vet"], 1)
		_ghi("SS1 nạp Pancake theo đúng ID, không tìm gần đúng", [g[0] for g in dem["pancake"]], ["227"])
		mst = _doc_rieng("select vgb_xhd_mst, vgb_xhd_email from `tabSales Invoice` where name=%s", (si,))[0]
		_ghi("SS1 nạp đúng MST của đơn 227", mst[0], "0311234567")
		_ghi("SS1 nạp đúng email của đơn 227", mst[1], "dung@example.com")
		# 2. Timeout: giữ cờ; chạy lại bị bỏ qua, không Save.
		kich_ban["save"] = "timeout"
		ra, loi = _request(chay_script, si)
		_ghi("SS2 timeout: cờ 1", _trang_thai(si)["co"], 1)
		_ghi("SS2 timeout: nói rõ giữ đối chiếu", any("giu doi chieu" in x for x in ra.get("loi", [])), True)
		so = dem["save"]
		kich_ban["save"] = "ok"
		ra, loi = _request(chay_script, si)
		_ghi("SS3 chạy lại khi chờ đối chiếu: không Save", dem["save"], so)
		_ghi("SS3 chạy lại: cờ vẫn 1", _trang_thai(si)["co"], 1)
		# 3. Mở lại rồi thành công.
		_request(at.mo_lai, si, "Kế toán đã kiểm theo mã phiếu, chưa có hoá đơn bên M-Invoice", 1)
		ra, loi = _request(chay_script, si)
		tt = _trang_thai(si)
		_ghi("SS4 thành công: tao_ok 1", ra.get("tao_ok"), 1)
		_ghi("SS4 thành công: có ID", bool(tt["minvoice_id"]), True)
		_ghi("SS4 thành công: cờ 0", tt["co"], 0)
		_ghi("SS4 thành công: số HĐ", tt["so"], "227")
		# 4. SI không có ID Pancake: 1227 đứng trước 227 vẫn chọn đúng 227.
		dem["pancake"] = []
		kich_ban["save"] = "ok"
		ra, loi = _request(chay_script, si2)
		r2 = _doc_rieng("select vgb_xhd_mst, vgb_xhd_email from `tabSales Invoice` where name=%s", (si2,))[0]
		_ghi("SS5 không ID: tìm trang 50", all(g[1].get("page_size") == 50 for g in dem["pancake"]), True)
		_ghi("SS5 không ID: 1227 đứng trước vẫn chọn 227", r2[0], "0311234567")
		_ghi("SS5 không ID: email đúng đơn", r2[1], "dung@example.com")
		_ghi("SS5 không ID: phát hành được", ra.get("tao_ok"), 1)
		# 5. Codex 08/09: trang 1 có 227 nhưng 5 trang đều đầy: không kết luận, không ghi, không Save.
		dem["pancake"] = []
		che_do_pancake["day"] = True
		so = dem["save"]
		ra, loi = _request(chay_script, si3)
		r3 = _doc_rieng("select vgb_xhd_ten, vgb_xhd_mst, vgb_xhd_email, vgb_hddt_cho_doi_chieu from `tabSales Invoice` where name=%s", (si3,))[0]
		_ghi("SS6 trang 5 vẫn đầy: đã duyệt đúng 5 trang", len(dem["pancake"]), 5)
		_ghi("SS6 trang 5 vẫn đầy: không ghi người mua", (r3[0] or "", r3[1] or "", r3[2] or ""), ("", "", ""))
		_ghi("SS6 trang 5 vẫn đầy: báo chưa hết kết quả", any("chưa hết kết quả" in x for x in ra.get("loi", [])), True)
		_ghi("SS6 trang 5 vẫn đầy: không gọi Save", dem["save"], so)
		_ghi("SS6 trang 5 vẫn đầy: không giữ cờ (chưa tới bước gửi)", int(r3[3] or 0), 0)
	finally:
		iu.make_post_request, iu.make_get_request = goc_post, goc_get
		_don_dep([si, si2, si3])


# ---------------------------------------------------------------- migrate

def chuan_bi_migrate(tinh_huong="goc"):
	"""Đặt Server Script về bản `goc` hoặc `v446` và xoá Patch Log tương ứng,
	để `bench migrate` chạy lại patch. Gọi trước bench migrate."""
	_khoa()
	_dung_server_script(tinh_huong)
	xoa = ["vagabond.patches.minvoice_v447"] + (["vagabond.patches.minvoice_v446"] if tinh_huong == "goc" else [])
	for p in xoa:
		frappe.db.delete("Patch Log", {"patch": p})
	frappe.db.commit()
	return {ten: kb.bam(frappe.db.get_value("Server Script", ten, "script"))[:16] for ten, _l, _c, _s in kb.BO}


def kiem_sau_migrate():
	"""Sau bench migrate: cả hai script phải bằng bản mới từng byte."""
	_khoa()
	ra = {}
	for ten, loai, _cu, _sua in kb.BO:
		hien = frappe.db.get_value("Server Script", ten, "script")
		ra[ten] = {"nhan": kb.doi_chieu(loai, hien), "sha256": kb.bam(hien)[:16], "khop_ban_moi": hien == kb.ban_moi(loai)}
	ra["patch_log"] = frappe.get_all("Patch Log", filters={"patch": ["like", "%minvoice_v44%"]}, pluck="patch")
	ra["truong"] = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "vgb_hddt_cho_doi_chieu"}) and 1 or 0
	return ra


def lam_lech_script():
	"""Sửa tay một script rồi để migrate phải dừng."""
	_khoa()
	doc = frappe.get_doc("Server Script", kb.TEN_NAP)
	doc.script = doc.script + "\n# ai do sua tay"
	doc.save(ignore_permissions=True)
	frappe.db.delete("Patch Log", {"patch": "vagabond.patches.minvoice_v447"})
	frappe.db.commit()


def chay():
	_khoa()
	KQ[:] = []
	_duong_python()
	_duong_script()
	hong = [k for k in KQ if k[0] == "HONG"]
	for k in KQ:
		print("%-4s %s%s" % (k[0], k[1], "" if k[0] == "DAT" else "  | được %r mong %r" % (k[2], k[3])))
	print("Tổng %d, hỏng %d" % (len(KQ), len(hong)))
	return {"tong": len(KQ), "hong": len(hong), "chi_tiet": [k for k in KQ if k[0] != "DAT"]}
