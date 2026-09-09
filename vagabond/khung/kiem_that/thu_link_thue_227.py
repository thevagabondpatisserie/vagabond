"""#227: chứng từ thử mới trong savepoint, không sửa đơn hay danh mục thật.

Ca thuế bắt buộc save/reload/submit với món chỉ có mẫu8%, rồi chọn đầu
phiếu5%. Thiếu tài khoản/danh mục là đỏ, không coi mock là bench đã đạt.
"""

import frappe
from unittest.mock import patch
from frappe.utils import getdate, today
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung


def _luu(d):
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return d


@ca("#227 link/thuế: PO mẫu5 thắng món8 qua save, sửa giá, thêm dòng và submit thật")
def _don_mua():
	cty = nen.cong_ty()
	tk = frappe.db.get_value("Account", {"company": cty, "is_group": 0,
		"disabled": 0, "name": ["like", "1331 -%"]}, "name")
	dung("cần tài khoản thuế đầu vào", bool(tk))
	duoi = frappe.generate_hash(length=10)
	mau8 = _luu(frappe.get_doc({"doctype": "Item Tax Template", "title": "Thử 227 tám " + duoi,
		"company": cty, "taxes": [{"tax_type": tk, "tax_rate": 8}]}))
	mau5 = _luu(frappe.get_doc({"doctype": "Purchase Taxes and Charges Template",
		"title": "Thử 227 năm " + duoi, "company": cty,
		"taxes": [{"charge_type": "On Net Total", "account_head": tk, "rate": 5,
			"description": "VAT thử", "category": "Total", "add_deduct_tax": "Add"}]}))
	mon = _luu(frappe.get_doc({"doctype": "Item", "item_code": "THU227" + duoi,
		"item_name": "Món thử thuế 227", "item_group": nen._mot("Item Group", {"is_group": 0}),
		"stock_uom": nen._mot("UOM", {}), "is_stock_item": 0, "is_purchase_item": 1,
		"taxes": [{"item_tax_template": mau8.name}]}))
	po = frappe.new_doc("Purchase Order")
	po.company, po.supplier = cty, nen.mot_nha_cung_cap()
	# Core buying_controller.validate_schedule_date lấy min() trên mọi dòng.
	# Sau reload ngày là date, nên dòng thêm mới cũng phải cùng kiểu.
	ngay = getdate(today())
	po.transaction_date = po.schedule_date = ngay
	po.currency, po.conversion_rate = "VND", 1
	po.ignore_pricing_rule = 1
	po.taxes_and_charges = mau5.name
	po.set("taxes", [{"charge_type": "On Net Total", "account_head": tk, "rate": 5,
		"description": "VAT thử", "category": "Total", "add_deduct_tax": "Add"}])
	po.append("items", {"item_code": mon.name, "qty": 1, "rate": 742857,
		"schedule_date": ngay, "item_tax_template": mau8.name})
	_luu(po)
	po.reload()
	la("tái hiện lỗi gốc8%", po.total_taxes_and_charges, 59428.56)
	po.vgb_thue_theo_mau = 1
	po.save(ignore_permissions=True)
	po.reload()
	la("sau chọn5% và reload", po.total_taxes_and_charges, 37142.85)
	la("giữ chế độ trong DB", po.vgb_thue_theo_mau, 1)
	po.items[0].rate = 100000
	po.items[0].item_tax_template = mau8.name
	# Giả đường API chỉ đổi tên mẫu nhưng còn mang bảng thuế8 cũ.
	po.taxes[0].rate = 8
	po.append("items", {"item_code": mon.name, "qty": 1, "rate": 100000,
		"schedule_date": ngay, "item_tax_template": mau8.name})
	po.save(ignore_permissions=True)
	po.reload()
	la("giữ5% sau sửa giá/thêm món/bảng thuế cũ", po.total_taxes_and_charges, 10000)
	po.flags.ignore_permissions = True
	po.submit()
	po.reload()
	la("submit thật", po.docstatus, 1)
	la("submit giữ5%", po.total_taxes_and_charges, 10000)


@ca("#227 link/thuế: khách lưu đúng SI và payload, trạng thái chờ đối chiếu cấm ghi lại")
@patch("vagabond.ban_hang.now_datetime", lambda: frappe.utils.get_datetime(frappe.utils.today() + " 12:00:00"))
def _khach_dien():
	# Ca này kiểm lưu thông tin, không kiểm giờ đóng cửa. Giữ đồng hồ của
	# cả ký và xác minh link ở buổi trưa cùng ngày SI, kể cả CI chạy đêm.
	from unittest.mock import patch
	from urllib.parse import parse_qs, urlparse
	from vagabond import ban_hang, minvoice_an_toan
	from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don
	si = _hoa_don(False)
	lk = ban_hang.pos_link_xhd(si.name, tao_moi=1)
	qs = parse_qs(urlparse(lk["url"]).query)
	cu = frappe.session.user
	try:
		frappe.set_user("Guest")
		with patch.object(ban_hang, "_xhd_mail_tiep_nhan", lambda *a: None):
			ban_hang.xhd_khach_luu(d=si.name, t=qs["t"][0], e=qs["e"][0],
				ten="Công ty TNHH Kiểm thử 227", mst="0101234567",
				dia_chi="Địa chỉ: 227 Đường Kiểm Thử", email="kiem227@example.com")
		si.reload()
		la("đúng email trên SI", si.vgb_xhd_email, "kiem227@example.com")
		# Chính sách tiền mới kiểm đúng mã/qty từng dòng trước khi gửi.
		# Ca khách điền phải dựng payload thật của SI, không dùng bảng rỗng.
		dong_gui = [{"inv_itemCode": d.item_code, "inv_quantity": d.qty} for d in si.items]
		goi = minvoice_an_toan.chuan_goi(si, {"data": [{"details": [{"data": dong_gui}]}]})
		la("đúng email trong payload cuối", goi["data"][0]["inv_buyerEmail"], "kiem227@example.com")
		la("địa chỉ đã làm sạch", si.vgb_xhd_dia_chi, "227 Đường Kiểm Thử")
		frappe.db.set_value("Sales Invoice", si.name, "vgb_hddt_cho_doi_chieu", 1)
		try:
			ban_hang.xhd_khach_luu(d=si.name, t=qs["t"][0], e=qs["e"][0],
				ten="Công ty TNHH Khác", mst="0101234567", email="khac@example.com")
			dung("phải chặn sửa khi đang đối chiếu", False)
		except frappe.ValidationError:
			pass
		si.reload()
		la("email không bị thay", si.vgb_xhd_email, "kiem227@example.com")
	finally:
		frappe.set_user(cu)
