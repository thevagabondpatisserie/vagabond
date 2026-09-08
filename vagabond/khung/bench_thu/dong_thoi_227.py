"""#227: hai tiến trình thật cùng lúc trên MariaDB: submit/submit và cancel/submit.

Bộ savepoint một kết nối không chứng minh được ca đồng thời, nên kịch bản
này chạy bằng HAI tiến trình `bench execute` riêng, mỗi tiến trình một kết
nối DB, cùng chờ tới một mốc giờ rồi thao tác. CHỈ chạy trên bench thử
(site_config `vagabond_bench_thu: 1`), có commit thật.

Cách chạy (xem đủ trong tai_lieu/issue-227-ban-giao.md):
    bench --site S execute vagabond.khung.bench_thu.dong_thoi_227.chuan_bi
    # lấy tên PI_A, PI_B, PR từ kết quả; chọn mốc = now + 20s
    bench --site S execute ...dong_thoi_227.submit --kwargs '{"pi":"<A>","moc":<t>}' &
    bench --site S execute ...dong_thoi_227.submit --kwargs '{"pi":"<B>","moc":<t>}' &
    wait
    bench --site S execute ...dong_thoi_227.ket_qua --kwargs '{"pr":"<PR>"}'
Rồi ca cancel/submit:
    bench --site S execute ...dong_thoi_227.them_pi --kwargs '{"pr":"<PR>","qty":7}'  -> PI_C
    bench --site S execute ...dong_thoi_227.cancel --kwargs '{"pi":"<A da ghi so>","moc":<t>}' &
    bench --site S execute ...dong_thoi_227.submit --kwargs '{"pi":"<C>","moc":<t>}' &
"""

import time

import frappe
from frappe.utils import today


def _khoa():
	if not frappe.conf.get("vagabond_bench_thu"):
		frappe.throw("dong_thoi_227 chỉ chạy trên bench thử có vagabond_bench_thu=1.")


def _cty():
	return frappe.db.get_value("Company", {"name": ["!=", ""]}, "name")


def _kho():
	cty = _cty()
	ten = "Kho dong thoi 227 - " + frappe.get_value("Company", cty, "abbr")
	if not frappe.db.exists("Warehouse", ten):
		frappe.get_doc({"doctype": "Warehouse", "warehouse_name": "Kho dong thoi 227", "company": cty,
			"account": frappe.db.get_value("Company", cty, "default_inventory_account")}).insert(ignore_permissions=True)
	return ten


def _mon():
	if not frappe.db.exists("Item", "NVL-DONGTHOI-227"):
		frappe.get_doc({"doctype": "Item", "item_code": "NVL-DONGTHOI-227", "item_name": "NVL đồng thời 227",
			"item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"), "stock_uom": "Nos",
			"is_stock_item": 1, "is_purchase_item": 1, "valuation_rate": 1000}).insert(ignore_permissions=True)
	return "NVL-DONGTHOI-227"


def chuan_bi(qty_pr=10, qty_pi=7, gia_pr=1000, gia_pi=500):
	"""PR nhận 10, hai PI nháp mỗi tờ 7 (tổng lượng 14 > 10 nhưng tổng tiền
	7.000 < 10.000, nên core validate_multiple_billing theo amount không chặn)."""
	_khoa()
	cty, kho, mon = _cty(), _kho(), _mon()
	ncc = frappe.db.get_value("Supplier", {"disabled": 0}, "name")
	pr = frappe.new_doc("Purchase Receipt")
	pr.update({"company": cty, "supplier": ncc, "posting_date": today(), "currency": "VND", "conversion_rate": 1, "set_warehouse": kho})
	pr.append("items", {"item_code": mon, "qty": qty_pr, "rate": gia_pr, "warehouse": kho})
	pr.flags.ignore_permissions = True
	pr.insert(ignore_permissions=True)
	pr.submit()
	frappe.db.commit()
	ds = [them_pi(pr.name, qty_pi, gia_pi) for _ in range(2)]
	return {"pr": pr.name, "pi": ds, "moc_goi_y": int(time.time()) + 25}


def them_pi(pr, qty=7, gia=500):
	_khoa()
	prd = frappe.get_doc("Purchase Receipt", pr)
	dong = prd.items[0]
	pi = frappe.new_doc("Purchase Invoice")
	pi.update({"company": prd.company, "supplier": prd.supplier, "posting_date": today(), "bill_date": today(),
		"bill_no": "dt-227-" + frappe.generate_hash(length=8), "due_date": today(), "currency": "VND", "conversion_rate": 1,
		"update_stock": 0, "ignore_pricing_rule": 1})
	pi.append("items", {"item_code": dong.item_code, "qty": qty, "rate": gia, "purchase_receipt": pr, "pr_detail": dong.name,
		"warehouse": dong.warehouse, "ten_hang_ncc": dong.item_name})
	pi.set("taxes", [])
	pi.flags.ignore_permissions = True
	pi.insert(ignore_permissions=True)
	frappe.db.commit()
	return pi.name


def _cho(moc):
	moc = float(moc or 0)
	while time.time() < moc:
		time.sleep(0.001)


def submit(pi, moc=0):
	_khoa()
	doc = frappe.get_doc("Purchase Invoice", pi)
	doc.flags.ignore_permissions = True
	_cho(moc)
	t0 = time.time()
	try:
		doc.submit()
		frappe.db.commit()
		kq = "SUBMIT OK"
	except Exception as e:
		frappe.db.rollback()
		kq = "SUBMIT CHAN: " + str(e)[:200]
	print("%s %.4f %s %s" % (pi, t0, kq, "deadlock" if "Deadlock" in kq or "1213" in kq else ""))
	return kq


def cancel(pi, moc=0):
	_khoa()
	doc = frappe.get_doc("Purchase Invoice", pi)
	doc.flags.ignore_permissions = True
	_cho(moc)
	t0 = time.time()
	try:
		doc.cancel()
		frappe.db.commit()
		kq = "CANCEL OK"
	except Exception as e:
		frappe.db.rollback()
		kq = "CANCEL CHAN: " + str(e)[:200]
	print("%s %.4f %s" % (pi, t0, kq))
	return kq


def ket_qua(pr):
	"""Tổng lượng PI đã ghi sổ trên từng dòng PR không được vượt lượng nhận;
	GL không nhân đôi."""
	_khoa()
	prd = frappe.get_doc("Purchase Receipt", pr)
	ra = {}
	for d in prd.items:
		da = frappe.db.sql("""select parent, qty, docstatus from `tabPurchase Invoice Item`
			where pr_detail=%s order by parent""", d.name, as_dict=True)
		tong = sum(x.qty for x in da if x.docstatus == 1)
		ra[d.name] = {"nhan": d.qty, "da_ghi_so": tong, "vuot": tong > d.qty + 0.0001,
			"pi": [(x.parent, x.qty, x.docstatus) for x in da]}
	gl = frappe.db.sql("""select voucher_no, count(*) n from `tabGL Entry` where voucher_type='Purchase Invoice'
		and is_cancelled=0 and voucher_no in (select parent from `tabPurchase Invoice Item` where pr_detail in %s)
		group by voucher_no""", ([d.name for d in prd.items],), as_dict=True)
	ra["gl"] = {g.voucher_no: g.n for g in gl}
	return ra
