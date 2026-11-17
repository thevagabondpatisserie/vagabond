# -*- coding: utf-8 -*-
"""v666 Hoá đơn ĐIỀU CHỈNH của nhà cung cấp trên màn Đối chiếu mua.

Ca gốc (anh Việt 17/11/2026): Gourmet Partner xuất hoá đơn 33387 ngày 01/10
sai giá bơ (460.000 đ/kg thay vì 400.000 đ/kg), rồi xuất hoá đơn điều chỉnh
giảm số 39339 ngày 13/11, ghi số âm -1.296.000 đ. Phiếu nhập PNK-2026-00803
nhận đúng 8.000.000 đ. Thu mua không nối được:
- tờ gốc HDM-26-10-00021 (9.200.000 đ) lệch 1,2 triệu với phiếu nhập;
- tờ điều chỉnh HDM-26-11-00218 (-1.200.000 đ) bị màn Đối chiếu coi như một
  lần nhập hàng âm, nên báo lệch đơn vị và lệch -9,2 triệu.
Cộng hai tờ thì đúng 8.000.000 đ, khớp tuyệt đối với phiếu nhập.

Luật từ bản này
---------------
- Tờ điều chỉnh (trạng thái hoá đơn điện tử "Điều chỉnh", có ghi hoá đơn
  gốc) KHÔNG nối phiếu nhập. Hàng đã vào kho bằng phiếu nhập của tờ gốc; tờ
  điều chỉnh chỉ sửa TIỀN. Màn Đối chiếu tìm tờ gốc theo MST người bán, ký
  hiệu và số hoá đơn gốc ghi trên hoá đơn điện tử.
- Tờ gốc so với phiếu nhập bằng TIỀN SAU ĐIỀU CHỈNH: tiền tờ gốc cộng tiền
  mọi tờ điều chỉnh còn hiệu lực của nó.
- Ghi sổ tờ điều chỉnh chỉ khi tờ gốc đã ghi sổ. Tờ âm ghi sổ thành phiếu nợ
  trả lại gắn với tờ gốc (return_against), không đụng tồn kho: công nợ tờ gốc
  giảm đúng số điều chỉnh, tài khoản hàng về chưa có hoá đơn của phiếu nhập
  về 0.
- Không sửa số trên hoá đơn điện tử, không gộp hai tờ thành một: mỗi tờ hoá
  đơn mua vẫn khớp đúng một hoá đơn điện tử để đối chiếu với thuế.

Phần THUẦN đứng trước, phần chạm Frappe sau.
"""

import re

from vagabond import doi_soat_hddt_ra as _ds

DT_HD = "MInvoice Invoice"
PI = "Purchase Invoice"
TT_DIEU_CHINH = "Điều chỉnh"



# ================================================================== THUẦN

def doc_hd_goc(chuoi):
	"""Chuỗi hoá đơn gốc M-Invoice ("KH C26TGP - So 33387 - Ngay 2026-09-30")
	ra {"ky_hieu", "so"} (ký hiệu chuẩn 6 ký tự, số nguyên). Không đọc được: None.
	Đọc qua đúng một hàm với màn đối soát hoá đơn bán ra (tach_goc)."""
	g = _ds.tach_goc(chuoi)
	if not g or not g[1]:
		return None
	return {"ky_hieu": g[0], "so": int(g[1])}


def la_to_dieu_chinh(trang_thai_hddt, hd_goc):
	"""Tờ hoá đơn mua là tờ điều chỉnh: hoá đơn điện tử trạng thái "Điều chỉnh"
	và đọc được hoá đơn gốc. Tờ thay thế không thuộc loại này. THUẦN."""
	return str(trang_thai_hddt or "").strip() == TT_DIEU_CHINH and bool(doc_hd_goc(hd_goc))


def so_nguyen(v):
	s = re.sub(r"\D", "", str(v or ""))
	return int(s) if s else 0


def khop_ky_hieu(a, b):
	"""Ký hiệu khớp, bỏ mẫu số đứng đầu (1C26TGP với C26TGP), cùng một cách
	chuẩn hoá với màn đối soát hoá đơn bán ra. THUẦN."""
	a, b = _ds.kh(a), _ds.kh(b)
	return bool(a) and a == b


def mst_goc(v):
	return str(v or "").split("-")[0].strip()


def chon_goc(goc, ung_vien):
	"""M-Invoice gốc trong các ứng viên cùng MST: đúng số, ký hiệu khớp, không
	phải chính tờ điều chỉnh. Đúng một ứng viên mới nhận. THUẦN."""
	ra = [u for u in ung_vien or []
		if so_nguyen(u.get("so_hd")) == goc["so"] and khop_ky_hieu(u.get("ky_hieu"), goc["ky_hieu"])
		and str(u.get("trang_thai") or "").strip() != TT_DIEU_CHINH]
	return ra[0] if len(ra) == 1 else None


def tien_sau_dieu_chinh(tien_goc, cac_to):
	"""Tiền hàng (trước thuế) của tờ gốc sau mọi tờ điều chỉnh còn hiệu lực.
	Tờ điều chỉnh giảm mang số âm nên chỉ cần cộng. THUẦN."""
	return round(float(tien_goc or 0) + sum(float(t.get("total") or 0) for t in cac_to or []
		if not t.get("huy")), 2)


def ly_do_chua_ghi_so(goc):
	"""Câu báo khi tờ điều chỉnh chưa ghi sổ được, hoặc None. THUẦN."""
	if not goc:
		return ("Chưa tìm thấy tờ hoá đơn mua của hoá đơn gốc. Kiểm hoá đơn gốc đã "
			"được kéo về từ M-Invoice chưa.")
	if goc.get("huy") or goc.get("docstatus") == 2:
		return "Tờ gốc %s đã huỷ, không ghi sổ điều chỉnh vào tờ đã huỷ được." % goc.get("name")
	if goc.get("docstatus") != 1:
		return ("Ghi sổ tờ gốc %s trước (nối phiếu nhập rồi ghi sổ), rồi mới ghi sổ "
			"tờ điều chỉnh này." % goc.get("name"))
	return None


# ================================================================== CHẠM HỆ

def _frappe():
	import frappe
	return frappe


def co_truong(dt, ten):
	"""Doctype có ô này trên site không. Ô trạng thái hoá đơn điện tử trên tờ và
	ô hoá đơn gốc của M-Invoice do site khai, không nằm trong mã nguồn: site
	hay bench thiếu ô thì coi như không dính điều chỉnh, không nổ Unknown column."""
	try:
		return bool(_frappe().get_meta(dt).has_field(ten))
	except Exception:
		return True  # Không đọc được khai báo (máy kiểm không Frappe): giữ đường cũ.


def la_to_dieu_chinh_doc(doc):
	"""Tờ hoá đơn mua này là phần CHÊNH (trả lại, điều chỉnh giảm hay tăng),
	không phải một lần mua với giá đủ. Đơn giá trên tờ là giá phần chênh nên
	không được làm "giá mua gần nhất" ở bất cứ đâu (Codex #578)."""
	return bool(doc.get("is_return")) or str(doc.get("custom_trang_thai_hddt") or "").strip() == TT_DIEU_CHINH


def sql_bo_to_chenh(bi_danh="pi"):
	"""Điều kiện SQL loại tờ phần chênh khỏi câu đọc giá mua (cùng luật với
	la_to_dieu_chinh_doc). Site thiếu ô trạng thái thì chỉ loại tờ trả lại."""
	s = " and ifnull(%s.is_return, 0) = 0" % bi_danh
	if co_truong(PI, "custom_trang_thai_hddt"):
		s += " and ifnull(%s.custom_trang_thai_hddt, '') != '%s'" % (bi_danh, TT_DIEU_CHINH)
	return s


def _mi(ma):
	frappe = _frappe()
	ma = str(ma or "").strip()
	if not ma or not frappe.db.exists("DocType", DT_HD):
		return None
	truong = ["name", "so_hd", "ky_hieu", "mst_doi_tac", "trang_thai", "tong_tien", "tien_truoc_thue"]
	if co_truong(DT_HD, "hd_goc"):
		truong.append("hd_goc")
	return frappe.db.get_value(DT_HD, ma, truong, as_dict=True)


def _pi_cua_mi(ten_mi):
	frappe = _frappe()
	r = frappe.get_all(PI, filters={"custom_minvoice_id": ten_mi, "docstatus": ["<", 2]},
		fields=["name", "docstatus", "vgb_huy", "total", "grand_total", "bill_no", "posting_date",
			"outstanding_amount"],
		order_by="creation asc", limit_page_length=2)
	r = [x for x in r if not x.get("vgb_huy")]
	return r[0] if r else None


def _goi_pi(r):
	if not r:
		return None
	return {"name": r["name"], "docstatus": r.get("docstatus"), "huy": 1 if r.get("vgb_huy") else 0,
		"total": float(r.get("total") or 0), "grand_total": float(r.get("grand_total") or 0),
		"bill_no": r.get("bill_no") or "", "ngay": str(r.get("posting_date") or ""),
		"outstanding_amount": float(r.get("outstanding_amount") or 0)}


def thong_tin(ten_pi):
	"""Tờ hoá đơn mua này có dính hoá đơn điều chỉnh không.

	Trả {} nếu không. Tờ điều chỉnh: {"la_dieu_chinh": 1, "goc": {...} hoặc None,
	"so_goc", "loi"}. Tờ gốc có điều chỉnh: {"cac_to": [...], "tien_dieu_chinh"}."""
	frappe = _frappe()
	truong = ["name", "custom_minvoice_id", "supplier", "total", "docstatus", "vgb_huy"]
	if co_truong(PI, "custom_trang_thai_hddt"):
		truong.append("custom_trang_thai_hddt")
	pi = frappe.db.get_value(PI, ten_pi, truong, as_dict=True)
	if not pi:
		return {}
	mi = _mi(pi.get("custom_minvoice_id"))
	if not mi:
		return {}
	tt = mi.get("trang_thai") or pi.get("custom_trang_thai_hddt")
	if la_to_dieu_chinh(tt, mi.get("hd_goc")):
		goc = doc_hd_goc(mi.get("hd_goc"))
		mst = mst_goc(mi.get("mst_doi_tac"))
		ung = frappe.get_all(DT_HD, filters={"loai": "Đầu vào", "mst_doi_tac": ["like", mst + "%"],
			"so_hd": ["like", "%" + str(goc["so"])]},
			fields=["name", "so_hd", "ky_hieu", "trang_thai"], limit_page_length=0) if mst else []
		ung = [u for u in ung if mst_goc(u.get("mst_doi_tac") or mst) == mst and u["name"] != mi["name"]]
		g = chon_goc(goc, ung)
		goc_pi = _goi_pi(_pi_cua_mi(g["name"])) if g else None
		ra = {"la_dieu_chinh": 1, "so_goc": "%s/%s" % (goc["ky_hieu"], goc["so"]), "goc": goc_pi,
			"tien": float(pi.get("total") or 0)}
		if goc_pi:
			ra["tien_sau"] = tien_sau_dieu_chinh(goc_pi["total"], cac_to_cua(goc_pi["name"]))
		loi = ly_do_chua_ghi_so(goc_pi)
		if loi:
			ra["loi"] = loi
		return ra
	cac = cac_to_cua(pi["name"], mi=mi)
	if not cac:
		return {}
	return {"cac_to": cac, "tien_dieu_chinh": round(sum(t["total"] for t in cac if not t["huy"]), 2),
		"tien_sau": tien_sau_dieu_chinh(pi.get("total"), cac)}


def cac_to_cua(ten_goc, mi=None):
	"""Các tờ hoá đơn mua điều chỉnh còn hiệu lực của một tờ gốc."""
	frappe = _frappe()
	if mi is None:
		mi = _mi(frappe.db.get_value(PI, ten_goc, "custom_minvoice_id"))
	if not mi or not mi.get("so_hd") or not co_truong(DT_HD, "hd_goc"):
		return []
	mst = mst_goc(mi.get("mst_doi_tac"))
	if not mst:
		return []
	so = so_nguyen(mi.get("so_hd"))
	ung = frappe.get_all(DT_HD, filters={"loai": "Đầu vào", "mst_doi_tac": ["like", mst + "%"],
		"trang_thai": TT_DIEU_CHINH, "hd_goc": ["like", "%" + str(so) + "%"]},
		fields=["name", "hd_goc", "mst_doi_tac"], limit_page_length=0)
	ra = []
	for u in ung:
		if mst_goc(u.get("mst_doi_tac")) != mst:
			continue
		g = doc_hd_goc(u.get("hd_goc"))
		if not g or g["so"] != so or not khop_ky_hieu(g["ky_hieu"], mi.get("ky_hieu")):
			continue
		p = _goi_pi(_pi_cua_mi(u["name"]))
		if p:
			ra.append(p)
	return ra


def chuan_bi_ghi_so(ten_pi):
	"""Kiểm và dựng tờ điều chỉnh cho bước ghi sổ (người gọi submit qua cửa ghi
	sổ chung): tờ gốc phải ghi sổ trước; tờ âm gắn return_against = tờ gốc."""
	frappe = _frappe()
	tt = thong_tin(ten_pi)
	if not tt.get("la_dieu_chinh"):
		frappe.throw("Tờ %s không phải hoá đơn điều chỉnh." % ten_pi)
	if tt.get("loi"):
		frappe.throw(tt["loi"])
	doc = frappe.get_doc(PI, ten_pi)
	if doc.docstatus != 0:
		frappe.throw("Hoá đơn %s không còn ở dạng nháp." % ten_pi)
	if doc.supplier != frappe.db.get_value(PI, tt["goc"]["name"], "supplier"):
		frappe.throw("Tờ gốc %s khác nhà cung cấp với tờ điều chỉnh." % tt["goc"]["name"])
	for d in doc.items:
		if (d.get("purchase_receipt") or "").strip():
			frappe.throw("Dòng %d đang nối phiếu nhập. Tờ điều chỉnh chỉ sửa tiền, bỏ nối trước khi ghi sổ." % d.idx)
	if doc.is_return:
		doc.return_against = tt["goc"]["name"]
	doc.flags.ignore_permissions = True
	doc.flags.vgb_dieu_chinh = True
	return doc
