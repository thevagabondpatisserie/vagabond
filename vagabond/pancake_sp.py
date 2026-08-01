"""Day ma hang tu ERPNext sang Pancake POS - Uyen chi tao ma MOT lan.

Da ban thu that ngay 01/08/2026: API tao san pham cua Pancake NHAN
`display_id` tu dat (du tai lieu khong ghi truong nay, giong vu `tags`
cua don hang). Vay nen ma tren Pancake se dung bang ma Item tren ERPNext.

Dieu kien van hanh di kem (anh Viet lam tren Pancake):
- Tat "Tu dong tao ma mau" trong Thiet lap San pham.
- Don cac ma tu sinh cu (BAWC00140S16CM...).
"""

import frappe
import requests
from frappe.utils import get_url

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key


def _tim_tren_pancake(c, k, ma):
	r = requests.get(
		"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
		params={"api_key": k, "search": ma, "page_size": 5},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	for v in (r.json() or {}).get("data") or []:
		if str(v.get("display_id") or "").strip().lower() == ma.lower():
			return v
	return None


@frappe.whitelist()
def tao_tren_pancake(item_code):
	"""Nut "Tao tren Pancake" tren form Item. Tra ve thong bao tieng Viet."""
	if not frappe.has_permission("Item", "write"):
		frappe.throw("Anh chi khong co quyen sua hang hoa")

	it = frappe.get_doc("Item", item_code)
	ma = (it.item_code or "").strip()

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chua dien khoa Pancake trong Vagabond Settings")

	# Co roi thi thoi, dung tao trung - Pancake cho hai variation cung display_id.
	if _tim_tren_pancake(c, k, ma):
		return {"ok": 0, "thong_bao": "Mã %s ĐÃ CÓ trên Pancake rồi, không tạo lại." % ma}

	gia = 0
	try:
		gia = int(it.standard_rate or 0)
	except (TypeError, ValueError):
		gia = 0

	anh = []
	if it.image and not it.image.startswith("/private"):
		anh = [get_url(it.image)]

	body = {
		"product": {
			"name": it.item_name or ma,
			"is_published": True,
			"variations": [
				{
					"display_id": ma,
					"custom_id": ma,
					"barcode": ma,
					"retail_price": gia,
					"images": anh,
					"is_hidden": False,
					"fields": [],
				}
			],
		}
	}
	r = requests.post(
		"%s/shops/%s/products" % (PANCAKE, c.pancake_shop_id),
		params={"api_key": k},
		json=body,
		timeout=TIMEOUT,
	)
	if r.status_code not in (200, 201) or not (r.json() or {}).get("success"):
		frappe.log_error(title="Vagabond: tao san pham Pancake loi", message=r.text[:1000])
		frappe.throw("Pancake tu choi, thu lai sau. Chi tiet da ghi vao nhat ky loi.")

	phan_duoi = " với giá %s đ." % "{:,}".format(gia).replace(",", ".") if gia else \
		". Item chưa có Giá bán tiêu chuẩn nên bên Pancake đang để 0 đ - điền giá giúp em."
	return {"ok": 1, "thong_bao": "Đã tạo %s trên Pancake%s" % (ma, phan_duoi)}
