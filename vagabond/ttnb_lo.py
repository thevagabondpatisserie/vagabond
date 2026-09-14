"""#317: gộp phiếu cùng người thụ hưởng, giữ một lần tiền ra cho một lô.

Mã lô không phải Bank Transaction. Không ghi ma_gd giả, không chuyển tiền.
Tất toán các phiếu cùng lô trong một giao dịch DB sau khi khóa sao kê/phiếu.
"""
import hashlib
import unicodedata


def chia_lo(ds):
	"""Nhóm theo ngân hàng và số tài khoản; mã ổn định khi retry cùng tập phiếu."""
	ra = {}
	for d in ds:
		k = (str(d.get("ngan_hang") or "").strip(), str(d.get("so_tk") or "").strip())
		if not all(k):
			raise ValueError("Phiếu %s thiếu ngân hàng hoặc số tài khoản." % d.get("name"))
		g = ra.setdefault(k, dict(ngan_hang=k[0], so_tk=k[1], ten_tk=d.get("ten_tk") or "", phieu=[], tong_tien=0))
		g["phieu"].append(d["name"])
		g["tong_tien"] += float(d.get("tong_tien") or d.get("so_tien") or 0)
	for g in ra.values():
		g["phieu"].sort()
		g["ma_lo"] = "TTLO-" + hashlib.sha256("|".join(g["phieu"]).encode()).hexdigest()[:16].upper()
		ten = unicodedata.normalize("NFD", g["ten_tk"]).encode("ascii", "ignore").decode().upper()
		g["noi_dung"] = "VAGABOND HOAN UNG %s %s %s" % (ten, g["ma_lo"], ",".join(g["phieu"]))
	return sorted(ra.values(), key=lambda g: g["ma_lo"])


import frappe


def _quyen():
	from vagabond import de_nghi_chi as dc
	if not (dc._vai() & (dc.VAI_KE_TOAN | dc.VAI_GIAM_DOC)):
		frappe.throw("Chỉ kế toán hoặc giám đốc được gộp chuyển.")


@frappe.whitelist()
def gop(phieu, xac_nhan=0):
	from vagabond import de_nghi_chi as dc
	_quyen()
	ten = frappe.parse_json(phieu) if isinstance(phieu, str) else phieu
	if not isinstance(ten, list) or not ten or len(ten) > 100 or len(set(ten)) != len(ten):
		frappe.throw("Chọn từ 1 đến 100 phiếu khác nhau.")
	# Khóa trước kiểm trạng thái, ngăn hai người gộp cùng một phiếu.
	ds = frappe.db.sql("select * from `tabVagabond De Nghi Chi` where name in %s order by name for update", (tuple(ten),), as_dict=True)
	if len(ds) != len(ten):
		frappe.throw("Có phiếu không còn tồn tại. Tải lại danh sách.")
	for d in ds:
		frappe.get_doc(dc.DT, d.name).check_permission("read")
		if d.trang_thai not in (dc.TT_CHO_KE_TOAN, dc.TT_HOAN_TAT) or d.phuong_thuc != "Chuyển khoản" or d.ma_gd or dc.tien_phieu(d) <= 0:
			frappe.throw("Phiếu %s không còn chờ chi chuyển khoản. Tải lại danh sách." % d.name)
	lo = chia_lo(ds)
	for g in lo:
		for d in ds:
			if d.name in g["phieu"] and d.get("lo_chuyen") and d.lo_chuyen != g["ma_lo"]:
				frappe.throw("Phiếu %s đã thuộc lô khác. Không gộp lại." % d.name)
		cu = frappe.get_all(dc.DT, filters={"lo_chuyen": g["ma_lo"]}, pluck="name", limit_page_length=0)
		if cu and set(cu) != set(g["phieu"]):
			frappe.throw("Lô đã đổi thành viên. Tải lại danh sách.")
	if frappe.utils.cint(xac_nhan):
		for g in lo:
			for ten_phieu in g["phieu"]:
				frappe.db.set_value(dc.DT, ten_phieu, {"lo_chuyen": g["ma_lo"], "noi_dung_ck": g["noi_dung"]})
	return {"lo": lo, "da_ghi": bool(frappe.utils.cint(xac_nhan))}


def khop(g):
	"""True nghĩa sao kê có mã lô, caller không được thử khớp từng phiếu nữa."""
	from vagabond import de_nghi_chi as dc, doi_soat_sepay as dss
	mo = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
	los = frappe.get_all(dc.DT, filters={"lo_chuyen": ["!=", ""]}, pluck="lo_chuyen", distinct=True, limit_page_length=0)
	trung = [ma for ma in los if dc.khop_noi_dung(mo, ma)]
	if not trung:
		return False
	if len(trung) != 1:
		return True
	# Cùng khóa Bank Transaction trước khi kiểm quyền chiếm của mọi luồng.
	frappe.db.sql("select name from `tabBank Transaction` where name=%s for update", (g["name"],))
	g = frappe.db.get_value(dc.BT, g["name"], ["name", "withdrawal", "docstatus", "bank_account", "description", "reference_number"], as_dict=True)
	if not g or g.docstatus == 2 or dc._loi_nguon_chi_ttnb(g):
		return True
	ds = frappe.db.sql("select * from `tabVagabond De Nghi Chi` where lo_chuyen=%s order by name for update", (trung[0],), as_dict=True)
	if ds and all(d.ma_gd == g.name and d.trang_thai == dc.TT_DA_CHI for d in ds):
		return True
	if not ds or any(d.ma_gd or d.trang_thai not in (dc.TT_CHO_KE_TOAN, dc.TT_HOAN_TAT) or d.phuong_thuc != "Chuyển khoản" for d in ds):
		return True
	lo = chia_lo(ds)
	if len(lo) != 1 or lo[0]["ma_lo"] != trung[0] or abs(float(g.withdrawal) - lo[0]["tong_tien"]) > 0.01:
		return True
	if dss.chu_cua_giao_dich([g.name]):
		return True
	frappe.db.savepoint("ttnb_lo_317")
	try:
		for d in ds:
			frappe.db.set_value(dc.DT, d.name, {"trang_thai": dc.TT_DA_CHI, "ma_gd": g.name, "ngay_da_chi": frappe.utils.now_datetime()})
	except Exception:
		frappe.db.rollback(save_point="ttnb_lo_317")
		raise
	# Đã ghi đủ cả lô mới commit; không commit từng phiếu.
	frappe.db.commit()
	for d in ds:
		dc._het_viec(d.name)
	return True
