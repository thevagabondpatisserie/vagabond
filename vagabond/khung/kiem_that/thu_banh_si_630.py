"""v630: bánh sỉ trên web, trọn vòng đời trên sổ cái và sổ kho thật.

Đi ĐÚNG các cửa của app, không dựng chứng từ bằng tay:
  1. Sales khai giá riêng (`banh_si.luu_gia`) vào bảng giá riêng; `gia_cua_khach`
     đọc lại đúng giá; bảng giá bán mặc định không có dòng nào của khách.
  2. `banh_si._lap_don`: Sales Order đã ghi sổ, giá = giá riêng gồm VAT, mẫu
     thuế "đã gồm trong giá".
  3. Khách công nợ: `giao_hang` lập phiếu giao (trừ kho MỘT lần) và hoá đơn
     Công nợ hạn +15; hoá đơn không trừ kho lần hai; công nợ hiện ở
     `cong_no.no_cua_khach`.
  4. Khách trả trước: dòng sao kê THẬT mang mã BSI, `khop_don` lập phiếu thu
     nháp chiếm dòng; giao khi còn nháp bị chặn; kế toán ghi sổ; giao hàng
     thì hoá đơn cấn ĐÚNG phiếu đó, không vơ khoản ứng trước khác của khách.
Chạy trong điểm lưu của nen.py, commit bị khoá, không gửi gì ra ngoài.
"""

from frappe.utils import add_days, flt, today

import frappe

from vagabond import banh_si as bs
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, dung, khong_nem, la, mot_kho
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen as _nen_thue
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_thiet_ke_rieng_630 import ANH, _sao_ke, _tien_mat


def _mon_ban_co_ton():
	return _mot("Item", {"is_stock_item": 1, "is_sales_item": 1, "disabled": 0, "has_batch_no": 0, "has_serial_no": 0,
		"has_variants": 0, "is_fixed_asset": 0})


def _nhap_ton(cty, ma, kho, sl):
	se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "purpose": "Material Receipt",
		"company": cty, "posting_date": today(), "items": [{"item_code": ma, "qty": sl, "t_warehouse": kho, "basic_rate": 10000,
		"conversion_factor": 1}]})
	se.insert(ignore_permissions=True)
	_DA_TAO.append((se.doctype, se.name))
	se.submit()


def _khach(ten, cuoi_ky):
	bs.dam_bao()
	c = frappe.get_doc({"doctype": "Customer", "customer_name": ten, "customer_group": bs.NHOM_KHACH,
		"customer_type": "Individual"})
	c.insert(ignore_permissions=True)
	_DA_TAO.append((c.doctype, c.name))
	frappe.db.set_value("Customer", c.name, {"vgb_si_web": 1, "vgb_si_cuoi_ky": cuoi_ky, "vgb_si_sdt": ""})
	return frappe.db.get_value("Customer", c.name, ["name", "customer_name", "vgb_si_cuoi_ky", "tax_id"], as_dict=True)


def _nen(cuoi_ky, ten):
	cty, _tk, _mau = _nen_thue()
	ma, kho = _mon_ban_co_ton(), mot_kho(cty)
	if not (ma and kho):
		frappe.throw("Site chưa có món bán theo tồn kho hoặc kho lá để dựng đơn sỉ thử.")
	_nhap_ton(cty, ma, kho, 10)
	kh = _khach(ten, cuoi_ky)
	khong_nem("khai giá riêng", lambda: bs.luu_gia(kh.name, ma, "27.000"))
	return cty, ma, kho, kh


def _lap(kh, ma, sl):
	gia = bs.gia_cua_khach(kh.name)
	don = bs.chuan_don({"ngay": str(add_days(today(), 3)), "dong": [{"ma": ma, "sl": sl, "gia": 1}]}, gia, today())
	so = khong_nem("lập phiếu đặt", lambda: bs._lap_don(kh, don, "kt630si" + frappe.generate_hash(length=20)))
	if so:
		_DA_TAO.append(("Sales Order", so.name))
		so.reload()
	return so


@ca("v630 bánh sỉ công nợ: giá riêng một nguồn, phiếu đặt giá máy chủ, giao hàng trừ kho một lần, hoá đơn Công nợ hạn +15, hiện ở công nợ của khách")
def _cong_no():
	cty, ma, kho, kh = _nen(1, "Khách sỉ kiểm 630 công nợ")
	la("giá riêng đọc lại", bs.gia_cua_khach(kh.name).get(ma, {}).get("gia"), 27000.0)
	mac_dinh = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	la("bảng giá bán mặc định không có dòng của khách", frappe.db.count("Item Price", {"price_list": mac_dinh, "customer": kh.name}), 0)
	so = _lap(kh, ma, 3)
	if not so:
		return
	la("phiếu đặt đúng giá gồm VAT", (so.docstatus, flt(so.items[0].rate), flt(so.rounded_total) or flt(so.grand_total), so.vgb_si_tt,
		so.selling_price_list), (1, 27000.0, 81000.0, "Công nợ", bs.BANG_GIA))
	dung("thuế đã gồm trong giá", all(t.included_in_print_rate for t in so.taxes))
	la("chưa có bút toán", frappe.db.count("GL Entry", {"voucher_no": so.name}), 0)
	la("trạng thái chờ giao", bs.tom_tat(so.name)["trang_thai"], "cho_giao")
	ton0 = flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty"))
	kq = khong_nem("giao hàng", lambda: bs.giao_hang(so.name, kho, "Kiểm 630"))
	if not kq:
		return
	_DA_TAO.extend([("Delivery Note", kq["phieu_giao"]), ("Sales Invoice", kq["hoa_don"])])
	la("tồn trừ đúng một lần", ton0 - flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty")), 3.0)
	la("hoá đơn không có dòng sổ kho", frappe.db.count("Stock Ledger Entry", {"voucher_no": kq["hoa_don"], "is_cancelled": 0}), 0)
	si = frappe.get_doc("Sales Invoice", kq["hoa_don"])
	la("hoá đơn công nợ", (si.docstatus, si.vgb_pt_thanh_toan, str(si.due_date), si.custom_pancake_id, si.update_stock),
		(1, "Công nợ", str(add_days(today(), 15)), "BSI-" + so.vgb_si_ma, 0))
	la("còn nợ đủ", (flt(si.outstanding_amount), flt(si.rounded_total) or flt(si.grand_total)), (81000.0, 81000.0))
	dung("dòng hoá đơn trỏ phiếu giao và phiếu đặt", all(d.delivery_note == kq["phieu_giao"] and d.sales_order == so.name for d in si.items))
	from vagabond import cong_no
	n = cong_no.no_cua_khach(kh.name)
	la("công nợ của khách", [(h["name"], h["tien"]) for h in n["hd"]], [(si.name, 81000.0)])
	la("hạn", n["han"].get(si.name), str(add_days(today(), 15)))
	la("trạng thái đã giao", bs.tom_tat(so.name)["trang_thai"], "da_giao")
	try:
		bs.giao_hang(so.name, kho)
	except frappe.ValidationError as e:
		dung("chặn giao lần hai", "đã giao" in str(e))
	else:
		dung("phải chặn giao lần hai", False)


@ca("v630 bánh sỉ trả trước: chuyển khoản chiếm sao kê, giao khi còn nháp bị chặn, kế toán ghi sổ, hoá đơn Trả trước cấn đúng phiếu, không vơ ứng trước khác")
def _tra_truoc():
	cty, ma, kho, kh = _nen(0, "Khách sỉ kiểm 630 trả trước")
	_tien_mat(cty)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	so = _lap(kh, ma, 2)
	if not so:
		return
	la("trả trước", (so.vgb_si_tt, bs.tom_tat(so.name)["trang_thai"]), ("Trả trước", "cho_tt"))
	khac = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Receive", "company": cty, "party_type": "Customer",
		"party": kh.name, "paid_amount": 300000, "received_amount": 300000, "posting_date": today(),
		"paid_to": _mot("Account", {"company": cty, "account_type": "Cash", "is_group": 0, "disabled": 0}),
		"reference_no": "KT630SI-KHAC", "reference_date": today()})
	khac.setup_party_account_field()
	khac.set_missing_values()
	khac.insert(ignore_permissions=True)
	_DA_TAO.append((khac.doctype, khac.name))
	khac.submit()
	_sao_ke(ba, 20000, "MBVCB.%s thieu" % so.vgb_si_ma)
	la("chuyển thiếu không lập phiếu", khong_nem("khớp thiếu", lambda: bs.khop_don(so.name)), 0)
	g = _sao_ke(ba, 54000, "MBVCB.%s chuyen tien" % so.vgb_si_ma)
	la("lập một phiếu", khong_nem("khớp", lambda: bs.khop_don(so.name)), 1)
	la("chạy lại không lập đôi", khong_nem("khớp lại", lambda: bs.khop_don(so.name)), 0)
	pe = frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name, "docstatus": 0}, pluck="name")
	la("một phiếu nháp", len(pe), 1)
	if not pe:
		return
	_DA_TAO.append(("Payment Entry", pe[0]))
	from vagabond import doi_soat_sepay as dss
	dung("dòng sao kê có chủ", g.name in dss.chu_cua_giao_dich([g.name]))
	try:
		bs.giao_hang(so.name, kho)
	except frappe.ValidationError as e:
		dung("chặn giao khi phiếu còn nháp", "chờ kế toán" in str(e))
	else:
		dung("phải chặn giao khi phiếu còn nháp", False)
	khong_nem("kế toán ghi sổ", lambda: bs.ghi_so_phieu(so.name, pe[0], ANH))
	kq = khong_nem("giao hàng", lambda: bs.giao_hang(so.name, kho))
	if not kq:
		return
	_DA_TAO.extend([("Delivery Note", kq["phieu_giao"]), ("Sales Invoice", kq["hoa_don"])])
	si = frappe.get_doc("Sales Invoice", kq["hoa_don"])
	la("hoá đơn trả trước", (si.docstatus, si.vgb_pt_thanh_toan, flt(si.total_advance), flt(si.outstanding_amount)),
		(1, "Trả trước", 54000.0, 0.0))
	la("chỉ cấn phiếu của đơn", [a.reference_name for a in si.advances], [pe[0]])
	khac.reload()
	la("ứng trước khác vẫn nguyên", flt(khac.unallocated_amount), 300000.0)
