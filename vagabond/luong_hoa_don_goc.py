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
	nhom = {}
	for d in doc.get("items") or []:
		ma = d.get("item_code")
		if not ma or not frappe.db.get_value("Item", ma, "is_stock_item"):
			continue
		nhom.setdefault(dl.khoa_ten(dl.ten_ncc_cua_dong(d)), []).append(d)
	if not nhom:
		return []
	nguon = {}
	for d in mc.dong_hang_hoa(dl.doc_chi_tiet(g.get("chi_tiet"))):
		r = mc.dong_tu_hoa_don(d, mc.dau_cua_to(g.get("tong_tien")))
		nguon.setdefault(dl.khoa_ten(r["ten"]), []).append(r)
	loi = []
	for ten, ds in nhom.items():
		goc = nguon.get(ten, [])
		if not ten or not goc or len({d.get("item_code") for d in ds}) != 1:
			loi.append("Dòng %s: chưa xác định duy nhất món theo tên trên hoá đơn nguồn." % ds[0].get("idx"))
			continue
		can = 0.0
		for r in goc:
			if not r.get("dvt"):
				loi.append("Dòng %s: hoá đơn nguồn thiếu đơn vị, cần xác nhận quy cách." % ds[0].get("idx"))
				break
			_, hs = mc.don_vi_theo_ma(ds[0].get("item_code"), r["dvt"],
				(g.get("mst_doi_tac") or "").split("-")[0], r["ten"])
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
