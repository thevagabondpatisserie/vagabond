"""#227: PI thật qua save/submit, thuế gốc, chiết khấu và nhiều lần nhận.

Chỉ tạo chứng từ mới trong savepoint của nen; không gọi nhà cung cấp
HĐĐT, không đụng ba hoá đơn thật người dùng báo. Thiếu danh mục là ca đỏ.
"""

import frappe
from frappe.utils import flt, today

from vagabond import doi_chieu_mua, mua_dich_vu
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la


def _luu(doc):
	doc.insert(ignore_permissions=True)
	nen._DA_TAO.append((doc.doctype, doc.name))
	return doc


def _nguon(dong, thue, tong):
	return _luu(frappe.get_doc({
		"doctype": "MInvoice Invoice", "ma_hd_id": "kiem-227-" + frappe.generate_hash(length=20),
		"loai": "Đầu vào", "ky_hieu": "KIEM227", "so_hd": "227",
		"ngay_lap": today(), "nguoi_mua_ban": "Kiểm thử trong điểm lưu #227",
		"tien_truoc_thue": tong - thue, "tien_thue": thue, "tong_tien": tong,
		"chi_tiet": frappe.as_json(dong),
	}))


def _phieu(dong, mon=None, ncc=None):
	cty = nen.cong_ty()
	mon = mon or nen._mot("Item", {"disabled": 0, "is_stock_item": 0,
		"is_purchase_item": 1, "is_fixed_asset": 0})
	ncc = ncc or nen.mot_nha_cung_cap()
	tk = frappe.db.get_value("Account", {"company": cty, "is_group": 0,
		"disabled": 0, "name": ["like", "1331 -%"]}, "name")
	if not mon or not ncc or not tk:
		frappe.throw("Ca #227 cần món mua không qua kho, NCC và tài khoản 1331 hợp lệ.")
	hd = frappe.new_doc("Purchase Invoice")
	hd.company = cty
	hd.supplier = ncc
	hd.currency = "VND"
	hd.conversion_rate = 1
	hd.posting_date = today()
	hd.bill_date = today()
	hd.bill_no = "kiem-227-" + frappe.generate_hash(length=12)
	hd.due_date = today()
	hd.update_stock = 0
	hd.ignore_pricing_rule = 1
	hd.cost_center = frappe.db.get_value("Company", cty, "cost_center")
	hd.flags.ignore_permissions = True
	for ten, sl, gia in dong:
		hd.append("items", {"item_code": mon, "item_name": ten,
			"ten_hang_ncc": ten, "qty": sl, "rate": gia})
	hd.set("taxes", [])
	hd.append("taxes", {"charge_type": "Actual", "account_head": tk,
		"description": "VAT thử #227", "tax_amount": 0, "category": "Total",
		"add_deduct_tax": "Add", "cost_center": hd.cost_center})
	return hd


def _ghi_so(hd, tong, thue):
	hd.submit()
	hd.reload()
	la("đã ghi sổ thật", hd.docstatus, 1)
	dung("tổng khớp trong ngưỡng làm tròn 1 đồng", abs(flt(hd.grand_total) - tong) <= 1)
	la("thuế đúng nguồn", sum(flt(t.tax_amount) for t in hd.taxes), thue)
	gl = nen.so_cai_cua(hd)
	dung("có GL thật", bool(gl))
	dung("GL cân", abs(sum(flt(d.debit) - flt(d.credit) for d in gl)) < 0.01)
	la("VAT đầu vào lên sổ đúng", sum(flt(d.debit) - flt(d.credit)
		for d in gl if d.account == hd.taxes[0].account_head), thue)
	la("không nhập kho lần hai", frappe.db.count("Stock Ledger Entry",
		{"voucher_type": hd.doctype, "voucher_no": hd.name}), 0)


@ca("#227: Nam An save và submit không cộng mẫu thuế lần hai vào GL")
def _nam_an():
	g = _nguon([{"ten": "Món thử Nam An", "sluong": 2, "dgia": 152286,
		"thtien": 304571}], 15229, 319800)
	hd = _phieu([("Món thử Nam An", 2, 152286)])
	_luu(hd)
	hd.custom_minvoice_id = g.name
	for buoc in ("save", "submit"):
		hd.append("taxes", {"charge_type": "On Net Total", "account_head": hd.taxes[0].account_head,
			"description": "Mẫu thừa 8%", "rate": 8, "category": "Total", "add_deduct_tax": "Add"})
		if buoc == "save":
			hd.save()
			la("save chỉ còn thuế gốc", len(hd.taxes), 1)
		else:
			_ghi_so(hd, 319800, 15229)


@ca("#227: 5561 chiết khấu cũ thành hàng được sửa một lần và ghi GL đúng")
def _chiet_khau():
	g = _nguon([
		{"ten": "Món thử rong biển", "sluong": 5, "dgia": 69444, "thtien": 347220},
		{"ten": "Món thử nước mắm", "sluong": 5, "dgia": 46296, "thtien": 231480},
		{"ten": "Chiết khấu", "tchat": 3, "sluong": 1, "dgia": 28935, "thtien": 28935},
	], 43981, 593746)
	hd = _phieu([("Món thử rong biển", 5, 69444), ("Món thử nước mắm", 5, 46296), ("Chiết khấu", 1, 28935)])
	hd.apply_discount_on = "Net Total"
	hd.discount_amount = 57870
	_luu(hd)
	hd.custom_minvoice_id = g.name
	for _ in range(2):
		hd.save()
		la("giữ hai dòng hàng", len(hd.items), 2)
		la("giảm đúng một lần", hd.discount_amount, 28935)
	_ghi_so(hd, 593746, 43981)


@ca("#227: dịch vụ 5561 không trừ chiết khấu cũ lần hai khi submit")
def _dich_vu():
	g = _nguon([{"ten": "Dịch vụ thử", "thtien": 578700},
		{"ten": "Chiết khấu", "tchat": 3, "thtien": 28935}], 43981, 593746)
	hd = _phieu([("Dịch vụ thử", 1, 549765)])
	_luu(hd)
	hd.custom_minvoice_id = g.name
	hd.vgb_loai_chung_tu = mua_dich_vu.LOAI_DICH_VU
	hd.apply_discount_on = "Net Total"
	hd.discount_amount = 57870
	_ghi_so(hd, 593746, 43981)
	la("không còn giảm lần hai", hd.discount_amount, 0)


@ca("#227: PI 2400 nối ba PR, lưu lặp giữ lượng và submit không nhập kho đúp")
def _ba_lan_nhan():
	phieu = [nen.phieu_nhap_ao(800, 2300) for _ in range(3)]
	d = phieu[0].items[0]
	g = _nguon([{"ten": "Trứng thử", "sluong": 2400, "dgia": 2300,
		"thtien": 5520000, "dvtinh": d.uom}], 0, 5520000)
	hd = _phieu([("Trứng thử", 2400, 2300)], d.item_code, phieu[0].supplier)
	hd.items[0].uom = d.uom
	hd.items[0].conversion_factor = d.conversion_factor
	hd.items[0].warehouse = d.warehouse
	hd.custom_minvoice_id = g.name
	_luu(hd)
	kq = doi_chieu_mua._noi(hd, [p.name for p in phieu], True)
	la("nối đủ ba lần nhận", kq["da_noi"], 3)
	la("không lỗi", kq["loi"], [])
	for _ in range(2):
		hd.save()
		la("số lượng không nhân", sum(flt(x.qty) for x in hd.items), 2400)
		la("đủ liên kết", {x.pr_detail for x in hd.items}, {p.items[0].name for p in phieu})
	_ghi_so(hd, 5520000, 0)
	for p in phieu:
		p.reload()
		dung("PR đã nhận tiền hoá đơn", flt(p.items[0].billed_amt) > 0)


@ca("#227: hai PI nháp cùng PR, PI thứ hai giá thấp vẫn bị chặn vượt lượng")
def _hai_nhap():
	p = nen.phieu_nhap_ao(800, 2300)
	d = p.items[0]
	ds = []
	# Hai PI đều được nối khi PR chưa có hoá đơn. Đơn giá thấp làm tổng
	# amount của cả hai vẫn <= tiền PR, nên cửa core theo tiền không đủ.
	for _ in range(2):
		hd = _phieu([("Lượng thử song song", 800, 1000)], d.item_code, p.supplier)
		hd.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor,
			"warehouse": d.warehouse, "purchase_receipt": p.name, "pr_detail": d.name})
		_luu(hd)
		ds.append(hd)
	ds[0].submit()
	try:
		ds[1].submit()
	except frappe.ValidationError as loi:
		# v472 (#252): câu chặn nêu tên hoá đơn đã lấy và chỉ đường ra.
		dung("đúng cửa số lượng, không phải chỉ cửa tiền", "đã ghi sổ lấy" in str(loi))
		dung("nêu đúng tên hoá đơn đã lấy", ds[0].name in str(loi))
	else:
		dung("phải chặn PI thứ hai", False)
	la("PI thứ hai vẫn nháp trong DB", frappe.db.get_value("Purchase Invoice", ds[1].name, "docstatus"), 0)
	la("PI thứ hai không có GL", len(nen.so_cai_cua(ds[1])), 0)


@ca("#227: tờ trả dựng lại dấu âm, save lặp và GL đảo đúng")
def _tra_lai_dung_dau():
	from vagabond import dung_lai_hddt
	g = _nguon([{"ten": "Món trả thử", "sluong": -2, "dgia": -100000,
		"thtien": -200000}, {"ten": "Chiết khấu", "tchat": 3, "thtien": -20000}],
		-18000, -198000)
	hd = _phieu([("Món trả thử", 2, 100000)])
	_luu(hd)
	hd.custom_minvoice_id = g.name
	# Đi qua đúng đường dựng lại trước save, không tự gán dấu đúng cho fixture.
	dung_lai_hddt._dung_dong_tai_cho(hd, g.as_dict())
	for _ in range(2):
		hd.save()
		hd.reload()
		la("là phiếu trả", hd.is_return, 1)
		la("lượng âm", hd.items[0].qty, -2)
		la("giá dương", hd.items[0].rate, 100000)
		la("giảm theo chiều trả", hd.discount_amount, -20000)
	_ghi_so(hd, -198000, -18000)


@ca("#321: PI tiền khớp nhưng nửa lượng chỉ cảnh báo khi Document.submit")
def _nguon_luong_321():
	p = nen.phieu_nhap_ao(6, 100000)
	d = p.items[0]
	g = _nguon([{"ten": "Lượng nguồn thử", "sluong": 6, "dgia": 100000,
		"thtien": 600000, "dvtinh": d.uom}], 0, 600000)
	hd = _phieu([("Lượng nguồn thử", 3, 200000)], d.item_code, p.supplier)
	hd.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor,
		"warehouse": d.warehouse, "purchase_receipt": p.name, "pr_detail": d.name})
	hd.custom_minvoice_id = g.name
	_luu(hd)
	hd.reload()
	la("tái hiện nửa lượng trước ghi sổ", hd.items[0].qty, 3)
	hd.submit()
	hd.reload()
	la("cảnh báo không chặn ghi sổ", hd.docstatus, 1)
	from vagabond.vagabond.report.doi_chieu_nguon_hoa_don_mua.doi_chieu_nguon_hoa_don_mua import execute
	_, bao_cao, _ = execute(dict(from_date=hd.posting_date, to_date=hd.posting_date, hoa_don=hd.name))
	dung("báo cáo đọc chứng từ thật đã ghi sổ", any(r["hoa_don"] == hd.name for r in bao_cao))
	dung("sổ cái đã sinh", len(nen.so_cai_cua(hd)) > 0)

	# Chỉ đổi fixture nguồn trong bench để chạm throw thật của resolver.
	raw = frappe.parse_json(g.chi_tiet)
	raw[0]["dvtinh"] = "TEST-UNKNOWN-UOM-321"
	g.db_set("chi_tiet", frappe.as_json(raw))
	truoc = len(getattr(frappe.local, "message_log", None) or [])
	co_cu = frappe.flags.get("mute_messages")
	_, bao_cao, _ = execute(dict(hoa_don=hd.name))
	dung("thiếu quy cách vẫn nằm trên báo cáo", any(r["nhom"] == "Lượng/quy cách" for r in bao_cao))
	la("không để lại hộp thoại throw", len(getattr(frappe.local, "message_log", None) or []), truoc)
	la("khôi phục cờ mute", frappe.flags.get("mute_messages"), co_cu)



@ca("#321: bỏ một món nguồn và bù giá món khác chỉ cảnh báo, vẫn ghi sổ")
def _mat_mon_321():
	p = nen.phieu_nhap_ao(2, 400000)
	d = p.items[0]
	g = _nguon([{"ten": "A nguồn thử", "sluong": 6, "dgia": 100000, "dvtinh": d.uom},
		{"ten": "B nguồn thử", "sluong": 2, "dgia": 100000, "dvtinh": d.uom}], 0, 800000)
	hd = _phieu([("B nguồn thử", 2, 400000)], d.item_code, p.supplier)
	hd.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor,
		"warehouse": d.warehouse, "purchase_receipt": p.name, "pr_detail": d.name})
	hd.custom_minvoice_id = g.name
	_luu(hd)
	hd.reload()
	la("fixture đã bỏ một món", len(hd.items), 1)
	hd.submit()
	hd.reload()
	la("cảnh báo không chặn ghi sổ", hd.docstatus, 1)
	from vagabond.vagabond.report.doi_chieu_nguon_hoa_don_mua.doi_chieu_nguon_hoa_don_mua import execute
	_, bao_cao, _ = execute(dict(from_date=hd.posting_date, to_date=hd.posting_date, hoa_don=hd.name))
	dung("báo cáo đọc chứng từ thật đã ghi sổ", any(r["hoa_don"] == hd.name for r in bao_cao))
	dung("sổ cái đã sinh", len(nen.so_cai_cua(hd)) > 0)


@ca('#332: API đổi mã từ ánh xạ disabled giữ giá nguồn qua save/reload và retry')
def _doi_ma_nguon_332():
	from vagabond import sua_ma_hoa_don as sm, quy_cach_ncc as qc
	mon_nen = nen._mot('Item', {'disabled':0, 'is_stock_item':0, 'is_purchase_item':1, 'is_fixed_asset':0})
	cac = []
	for _ in range(2):
		m = frappe.copy_doc(frappe.get_doc('Item', mon_nen))
		m.item_code = 'KIEM332-' + frappe.generate_hash(length=12)
		m.item_name = m.item_code
		m.disabled = 0
		_luu(m)
		cac.append(m)
	cu, moi = cac
	g = _nguon([{'ten':'Món thử đổi mã 332','mhhdvu':'MA332','sluong':3,'dgia':331818,
		'thtien':995454,'dvtinh':moi.stock_uom}], 99545, 1094999)
	# MST thử không mang hậu tố chi nhánh, chỉ chạm nguồn mới trong savepoint.
	mst = '332' + frappe.generate_hash(length=10)
	g.mst_doi_tac = mst
	g.save()
	mapping = _luu(frappe.get_doc(dict(doctype=qc.LOAI, supplier_mst=mst,
		ten_ncc='Tên cũ của mã 332', ma_ncc='MA332', item_code=cu.name, vgb_uom=cu.stock_uom)))
	hd = _phieu([('Món thử đổi mã 332',3,395000)], moi.name)
	_luu(hd)
	# Dựng trạng thái lịch sử đã mất tên; chỉ trên chứng từ thử của ca này.
	hd.db_set('custom_minvoice_id', g.name, update_modified=False)
	hd.items[0].db_set('ten_hang_ncc', '', update_modified=False)
	cu.disabled = 1
	cu.save()
	hd.reload()
	modified = str(hd.modified)
	r = sm.sua(hd.name, hd.items[0].name, '0', moi.name, moi.stock_uom, modified)
	hd.reload()
	la('giá nguồn sau DB reload', hd.items[0].rate, 331818)
	la('tiền dòng đúng', hd.items[0].amount, 995454)
	la('tổng gồm thuế đúng', hd.grand_total, 1094999)
	la('mã thay thế còn', hd.items[0].item_code, moi.name)
	la('tên nguồn còn', hd.items[0].ten_hang_ncc, 'Món thử đổi mã 332')
	mapping.reload()
	la('mapping mới lưu cùng PI', mapping.item_code, moi.name)
	for _ in range(2):
		hd.save()
		hd.reload()
		la('save lặp giữ tổng', hd.grand_total, 1094999)
	try:
		sm.sua(hd.name, hd.items[0].name, '0', moi.name, moi.stock_uom, modified)
	except frappe.ValidationError as e:
		dung('retry stale nói tải lại', 'Tải lại' in str(e))
	else:
		dung('không ghi từ phiên cũ', False)
	la('không tự ghi sổ', hd.docstatus, 0)
	la('không tạo GL', len(nen.so_cai_cua(hd)), 0)

	# Ép lỗi ở cuối Document.save, sau khi mapping đã ghi và PI đã db_update.
	from unittest.mock import patch
	cu.disabled = 0
	cu.save()
	with patch.object(type(hd), 'on_update', side_effect=frappe.ValidationError('Lỗi thử sau ghi PI')):
		try:
			sm.sua(hd.name, hd.items[0].name, '0', cu.name, cu.stock_uom, str(hd.modified))
		except frappe.ValidationError as e:
			dung('đã chạm cuối save', 'Lỗi thử sau ghi PI' in str(e))
		else:
			dung('phải báo lỗi thử', False)
	hd.reload()
	mapping.reload()
	la('rollback PI vẫn mã mới', hd.items[0].item_code, moi.name)
	la('rollback mapping vẫn mã mới', mapping.item_code, moi.name)
	la('rollback giữ tiền', hd.grand_total, 1094999)

	# Quyền sửa không tự ghi sổ; kế toán chủ động submit phải đi hết GL thật.
	_ghi_so(hd, 1094999, 99545)
	gl = nen.so_cai_cua(hd)
	la('công nợ NCC đúng tiền nguồn', sum(flt(d.credit) - flt(d.debit)
		for d in gl if d.account == hd.credit_to), 1094999)
	from vagabond import minvoice_chung_tu as mc
	dong = sm._dong_goc(g.as_dict())[0]
	ma_sau, _, _ = mc._tra_ma_hang(dong, mst, hd.supplier)
	la('đồng bộ tiếp tra mã NCC vẫn chọn mã mới', ma_sau, moi.name)
