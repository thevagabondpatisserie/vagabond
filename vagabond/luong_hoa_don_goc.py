"""Tổng tiền khớp vẫn có thể sai lượng: qty giảm, rate tăng bù nhau.

Kiểm trước ghi sổ, không tự sửa chứng từ hoặc bỏ đầu nối. Cộng các dòng
cùng tên nguồn để chấp nhận việc tách qua nhiều phiếu nhập. Dùng quy đổi
đã khai theo nhà cung cấp, không suy lượng từ tiền hoặc đơn giá.
"""
import frappe
from frappe.utils import flt
from vagabond import dung_lai_hddt as dl, minvoice_chung_tu as mc


def sai_luong(doc, g):
	"""Đọc-only; trả lý do chưa chứng minh được lượng hàng tồn kho."""
	# Dòng cũ có thể chỉ giữ tên Item nội bộ. Chỉ phục hồi tên nguồn bằng
	# ánh xạ NCC duy nhất, không đoán theo vị trí hoặc tổng tiền.
	alias = {}
	if doc.get("supplier"):
		for r in frappe.get_all("Anh Xa Mat Hang NCC", filters={"nha_cung_cap": doc.get("supplier")},
			fields=["ten_hang_ncc", "ma_hang"], limit_page_length=0):
			alias.setdefault(dl.khoa_ten(r.get("ten_hang_ncc")), set()).add(r.get("ma_hang"))
	nguon_tho = mc.dong_hang_hoa(dl.doc_chi_tiet(g.get("chi_tiet")))
	ten_theo_ma = {}
	for r in nguon_tho:
		ten = dl.khoa_ten(r.get("ten"))
		mas = alias.get(ten, set())
		if len(mas) == 1 and None not in mas and "" not in mas:
			ten_theo_ma.setdefault(next(iter(mas)), set()).add(ten)
	def ten_dong(d):
		ten = dl.khoa_ten(dl.ten_ncc_cua_dong(d))
		if not d.get("ten_hang_ncc") and len(ten_theo_ma.get(d.get("item_code"), set())) == 1:
			return next(iter(ten_theo_ma[d.get("item_code")]))
		return ten
	nhom = {}
	ngoai_kho = set()
	for d in doc.get("items") or []:
		ma = d.get("item_code")
		if ma and not frappe.db.get_value("Item", ma, "is_stock_item"):
			ngoai_kho.add(ten_dong(d))
			continue
		nhom.setdefault(ten_dong(d), []).append(d)
	nguon = {}
	for d in nguon_tho:
		r = {"ten": d.get("ten") or "", "dvt": d.get("dvtinh"), "sl": d.get("sluong")}
		if mc.dau_cua_to(g.get("tong_tien")) < 0 and r["sl"] is not None:
			r["sl"] = -abs(flt(r["sl"]))
		nguon.setdefault(dl.khoa_ten(r["ten"]), []).append(r)
	loi = []
	for ten in sorted(set(nhom) | (set(nguon) - ngoai_kho)):
		ds = nhom.get(ten, [])
		if not ds:
			loi.append("Thiếu món trên hoá đơn nguồn; cần đối chiếu đủ các dòng trước ghi sổ.")
			continue
		goc = nguon.get(ten, [])
		if not ten or not goc or any(not d.get("item_code") for d in ds) or len({d.get("item_code") for d in ds}) != 1:
			loi.append("Dòng %s: chưa xác định duy nhất món theo tên trên hoá đơn nguồn." % ds[0].get("idx"))
			continue
		can = 0.0
		for r in goc:
			if not r.get("dvt") or not flt(r.get("sl")):
				loi.append("Dòng %s: hoá đơn nguồn thiếu đơn vị hoặc số lượng bằng không/trống, cần xác nhận lượng và quy cách." % ds[0].get("idx"))
				break
			try:
				_, hs = mc.don_vi_theo_ma(ds[0].get("item_code"), r["dvt"],
					(g.get("mst_doi_tac") or "").split("-")[0], r["ten"])
			except frappe.ValidationError:
				loi.append("Dòng %s: chưa xác nhận được quy cách của hoá đơn nguồn. Kiểm đơn vị và quy cách nhà cung cấp trước ghi sổ; không tự tạo lại chứng từ đã nối." % ds[0].get("idx"))
				break
			can += flt(r["sl"]) * flt(hs)
		else:
			hien = sum(flt(d.get("qty")) * flt(d.get("conversion_factor")) for d in ds)
			if any(flt(d.get("conversion_factor")) <= 0 for d in ds) or abs(hien - can) > 0.0001:
				loi.append("Dòng %s: lượng quy về đơn vị kho là %s, hoá đơn nguồn là %s. Tổng tiền khớp không thay thế kiểm số lượng." % (ds[0].get("idx"), hien, can))
	return loi


def kiem_truoc_ghi_so(doc, method=None):
	# Phiếu trả có lượng trả riêng theo chứng từ gốc; không ép bằng toàn bộ
	# hóa đơn mua. Không tác động phiếu tay không có nguồn điện tử.
	if doc.get("is_return") or not doc.get("custom_minvoice_id"):
		return
	g = dl._goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw("Không đọc được hoá đơn nguồn để kiểm lượng. Chưa thể ghi sổ.")
	loi = sai_luong(doc, g)
	if loi:
		frappe.throw("Chưa thể ghi sổ: " + " ".join(loi), title="Lượng khác hoá đơn nguồn")
