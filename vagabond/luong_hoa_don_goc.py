"""Tổng tiền khớp vẫn có thể sai lượng: qty giảm, rate tăng bù nhau.

Chỉ cảnh báo trước ghi sổ, không chặn và không tự sửa chứng từ hoặc bỏ đầu nối. Cộng các dòng
cùng tên nguồn để chấp nhận việc tách qua nhiều phiếu nhập. Dùng quy đổi
đã khai theo nhà cung cấp, không suy lượng từ tiền hoặc đơn giá.
"""
from html import escape
import frappe
from frappe.utils import flt
from vagabond import dung_lai_hddt as dl, minvoice_chung_tu as mc


def sai_luong(doc, g, kem_nhom=False):
	"""Đọc-only; trả lý do chưa chứng minh được lượng hàng tồn kho."""
	# Dòng cũ có thể chỉ giữ tên Item nội bộ. Chỉ phục hồi tên nguồn bằng
	# ánh xạ NCC duy nhất, không đoán theo vị trí hoặc tổng tiền.
	def khoa(ten):
		return dl.khoa_ten(str(ten or "")[:140])
	alias = {}
	if doc.get("supplier"):
		for r in frappe.get_all("Anh Xa Mat Hang NCC", filters={"nha_cung_cap": doc.get("supplier")},
			fields=["ten_hang_ncc", "ma_hang"], limit_page_length=0):
			if khoa(r.get("ten_hang_ncc")):
				alias.setdefault(khoa(r.get("ten_hang_ncc")), set()).add(r.get("ma_hang"))
	nguon_tho = mc.dong_hang_hoa(dl.doc_chi_tiet(g.get("chi_tiet")))
	ten_theo_ma = {}
	for r in nguon_tho:
		ten = khoa(r.get("ten"))
		mas = alias.get(ten, set())
		if len(mas) == 1 and None not in mas and "" not in mas:
			ten_theo_ma.setdefault(next(iter(mas)), set()).add(ten)
	def ten_dong(d):
		ten = khoa(dl.ten_ncc_cua_dong(d))
		if not str(d.get("ten_hang_ncc") or "").strip() and len(ten_theo_ma.get(d.get("item_code"), set())) == 1:
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
		nguon.setdefault(khoa(r["ten"]), []).append(r)
	loi = []
	def bao(nhom, chu):
		loi.append({"nhom": nhom, "chu": chu})
	for ten in sorted(set(nhom) | (set(nguon) - ngoai_kho)):
		ds = nhom.get(ten, [])
		if not ds:
			bao("nhan_dien", "Chưa đối chiếu được món nguồn: %s. Kiểm tên/mã và ánh xạ nhà cung cấp." % (str(nguon.get(ten, [{}])[0].get("ten") or "").strip() or "(nguồn chưa ghi tên món)"))
			continue
		goc = nguon.get(ten, [])
		if not ten or not goc or any(not d.get("item_code") for d in ds) or len({d.get("item_code") for d in ds}) != 1:
			bao("nhan_dien", "Dòng %s: chưa xác định duy nhất món theo tên trên hoá đơn nguồn." % ds[0].get("idx"))
			continue
		can = 0.0
		for r in goc:
			if not r.get("dvt") or not flt(r.get("sl")):
				bao("luong", "Dòng %s: hoá đơn nguồn thiếu đơn vị hoặc số lượng bằng không/trống, cần xác nhận lượng và quy cách." % ds[0].get("idx"))
				break
			try:
				_, hs = mc.don_vi_theo_ma(ds[0].get("item_code"), r["dvt"],
					(g.get("mst_doi_tac") or "").split("-")[0], r["ten"])
			except frappe.ValidationError:
				bao("luong", "Dòng %s: chưa xác nhận được quy cách của hoá đơn nguồn. Kiểm đơn vị và quy cách nhà cung cấp trước ghi sổ; không tự tạo lại chứng từ đã nối." % ds[0].get("idx"))
				break
			can += flt(r["sl"]) * flt(hs)
		else:
			hien = sum(flt(d.get("qty")) * flt(d.get("conversion_factor")) for d in ds)
			if any(flt(d.get("conversion_factor")) <= 0 for d in ds) or abs(hien - can) > 0.0001:
				bao("luong", "Dòng %s: lượng quy về đơn vị kho là %s, hoá đơn nguồn là %s. Tổng tiền khớp không thay thế kiểm số lượng." % (ds[0].get("idx"), hien, can))
	return loi if kem_nhom else [x["chu"] for x in loi]


def doc_canh_bao(doc):
	"""Chỉ đọc, dùng chung cho báo cáo và popup, không ghi dữ liệu."""
	if doc.get("is_return") or not doc.get("custom_minvoice_id"):
		return []
	try:
		g = dl._goc(doc.get("custom_minvoice_id"))
		return sai_luong(doc, g, kem_nhom=True) if g else [{"nhom": "nguon", "chu": "Chưa đọc được hoá đơn nguồn để kiểm lượng."}]
	except Exception:
		return [{"nhom": "nguon", "chu": "Chưa kiểm được lượng theo hoá đơn nguồn."}]


def kiem_truoc_ghi_so(doc, method=None):
	"""Anh Việt duyệt F10: chỉ popup lượng/quy cách, phần khác xem báo cáo."""
	loi = [x for x in doc_canh_bao(doc) if x["nhom"] == "luong"]
	if loi:
		duong = frappe.utils.get_url_to_form("Purchase Invoice", doc.get("name")) if doc.get("name") else ""
		loi = list(dict.fromkeys(x["chu"] for x in loi))
		huong_dan = "Đây là cảnh báo, không chặn ghi sổ. Đối chiếu lượng và quy cách với bản gốc trước khi sửa tay theo quyền hiện có. Chứng từ đã ghi sổ dùng quy trình sửa/hủy chuẩn của ERP."
		noi_dung = "<br>".join(escape(x) for x in loi[:5])
		if len(loi) > 5:
			noi_dung += "<br>Còn %s mục cần kiểm tra trên chứng từ." % (len(loi) - 5)
		frappe.msgprint(noi_dung + "<br>" + huong_dan +
			('<br><a href="' + escape(duong, quote=True) + '">Mở chứng từ để kiểm tra và sửa tay</a>' if doc.get("name") else ""),
			title="Cần kiểm tra lượng theo hoá đơn nguồn", indicator="orange")
