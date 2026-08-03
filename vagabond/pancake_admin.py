"""Cong cu don danh muc san pham ben Pancake POS - chi System Manager dung.

Vi sao phai nam trong app: Server Script tren Frappe Cloud KHONG goi duoc API
ben ngoai (da do that 31/07/2026, make_get_request bao "name is not defined").
Muon soi hay sua Pancake thi code phai nam trong app roi deploy.

Pancake KHONG CO endpoint DELETE san pham. Muon bo mot bien the thi PUT lai
san pham voi bien the do kem is_removed true. Neu san pham chi con dung mot
bien the thi bo di la mat luon san pham, nen o day chan lai: chi cho bo khi
san pham con bien the khac, con lai thi phai an ca san pham (update_hide)
hoac doi ma bien the ve ma sach.

Anh Viet 03/08/2026: "Don het 10 ma rac ben Pancake, xoa di nha em" - 10 ma
duoi tu sinh BAWC00104S16CM, BAWC00105MINI12CM, BAWC00107M18CM,
BAWC00108L20CM, BAWC00109MINI12CM, BAWC00113L20CM, BAWC00120M18CM,
BAWC00125MINI12CM, BAWC00126M18CM, BAWC00127MINI12CM.

Soi ngay 03/08/2026 moi ra su that: 10 ma do khong phai rac. Moi ma la bien
the DUY NHAT cua mot san pham that dang ban, ten trung khop ben Next, va ma
goc sach (BAWC00104...) chua he co tren Pancake. Cai duoi la do Pancake TU
SINH display_id bang custom_id san pham cong gia tri thuoc tinh bien the
(size 16CM ra S16CM). display_id la truong chi doc: PUT vao thi Pancake tra
422 "[display_id]: is invalid" (da do that). Muon ma sach thi phai go thuoc
tinh bien the (fields rong) chu khong doi thang display_id - xem bo_hau_to.
"""

import frappe
import requests
from frappe.utils import get_url

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key


def _quyen():
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị hệ thống mới dùng được công cụ này")


def _khoa():
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")
	return c, k


def _bien_the(c, k, ma):
	"""Tim mot bien the theo display_id, tra ve nguyen ban ghi Pancake."""
	r = requests.get(
		"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
		params={"api_key": k, "search": ma, "page_size": 20},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	for v in (r.json() or {}).get("data") or []:
		if str(v.get("display_id") or "").strip().lower() == str(ma or "").strip().lower():
			return v
	return None


def _san_pham(c, k, pid):
	"""Doc nguyen san pham theo id de biet no co bao nhieu bien the."""
	r = requests.get(
		"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, pid),
		params={"api_key": k},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	j = r.json() or {}
	return j.get("data") or j.get("product") or j


def _put_san_pham(c, k, pid, than):
	r = requests.put(
		"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, pid),
		params={"api_key": k},
		json={"product": than},
		timeout=TIMEOUT,
	)
	if r.status_code not in (200, 201):
		frappe.log_error(title="Vagabond: PUT san pham Pancake loi", message=r.text[:1000])
		frappe.throw("Pancake từ chối (mã %s). Chi tiết đã ghi vào nhật ký lỗi." % r.status_code)
	return r.json() or {}


@frappe.whitelist()
def soi(ma):
	"""Chi doc. Xem mot ma dang nam o san pham nao, san pham do co may bien the."""
	_quyen()
	c, k = _khoa()
	v = _bien_the(c, k, ma)
	if not v:
		return {"co": 0, "ma": ma}
	sp = (v.get("product") or {})
	pid = sp.get("id") or v.get("product_id")
	day_du = _san_pham(c, k, pid) if pid else {}
	bt = day_du.get("variations") or sp.get("variations") or []
	return {
		"co": 1,
		"ma": ma,
		"product_id": pid,
		"ten_san_pham": day_du.get("name") or sp.get("name") or "",
		"so_bien_the": len(bt),
		"variation_id": v.get("id"),
		"gia": v.get("retail_price"),
		"an": 1 if (v.get("is_hidden") or day_du.get("is_hide")) else 0,
		"cac_ma": [str(x.get("display_id") or "") for x in bt],
		"co_ben_next": 1 if frappe.db.exists("Item", ma) else 0,
	}


@frappe.whitelist()
def doi_ten_san_pham(ma, ten_moi):
	"""Doi ten san pham chua ma nay cho khop voi ten ben Next."""
	_quyen()
	c, k = _khoa()
	ten_moi = str(ten_moi or "").strip()
	if not ten_moi:
		frappe.throw("Chưa nhập tên mới")
	v = _bien_the(c, k, ma)
	if not v:
		frappe.throw("Không thấy mã %s trên Pancake" % ma)
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	cu = (v.get("product") or {}).get("name") or ""
	_put_san_pham(c, k, pid, {"name": ten_moi})
	return {"ok": 1, "ma": ma, "ten_cu": cu, "ten_moi": ten_moi}


@frappe.whitelist()
def xem_tho(ma):
	"""Chi doc. Tra ve nguyen cau truc san pham va bien the de soi."""
	_quyen()
	c, k = _khoa()
	v = _bien_the(c, k, ma)
	if not v:
		return {"co": 0, "ma": ma}
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	sp = _san_pham(c, k, pid) if pid else {}
	ra = {
		"co": 1,
		"san_pham": {x: sp.get(x) for x in ("id", "name", "custom_id", "display_id", "is_hide", "is_published")},
		"bien_the": [],
	}
	for b in sp.get("variations") or []:
		ra["bien_the"].append(
			{x: b.get(x) for x in ("id", "display_id", "custom_id", "barcode", "retail_price", "is_hidden", "fields")}
		)
	return ra


@frappe.whitelist()
def bo_hau_to(ma, ma_sach=None):
	"""Go thuoc tinh bien the de display_id thoi bi noi duoi tu sinh.

	Chi cho chay khi san pham co dung mot bien the: san pham nhieu bien the ma
	go thuoc tinh thi cac bien the trung ma nhau, phai xu ly tay.
	"""
	_quyen()
	c, k = _khoa()
	v = _bien_the(c, k, ma)
	if not v:
		return {"ok": 0, "thong_bao": "Không thấy mã %s trên Pancake." % ma}
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	sp = _san_pham(c, k, pid) if pid else {}
	bt = sp.get("variations") or []
	if len(bt) > 1:
		frappe.throw(
			'Sản phẩm "%s" có %d biến thể. Gỡ thuộc tính sẽ làm trùng mã, phải xử lý tay.'
			% (sp.get("name") or "", len(bt))
		)
	ma_sach = str(ma_sach or "").strip().upper() or str(sp.get("custom_id") or "").strip().upper()
	if not ma_sach:
		frappe.throw("Không đoán được mã sạch cho %s, truyền ma_sach vào giúp em." % ma)
	_put_san_pham(
		c,
		k,
		pid,
		{
			"custom_id": ma_sach,
			"variations": [{"id": v.get("id"), "fields": [], "custom_id": ma_sach, "barcode": ma_sach}],
		},
	)
	sau = _bien_the(c, k, ma_sach)
	return {"ok": 1 if sau else 0, "ma_cu": ma, "ma_sach": ma_sach, "kiem_lai": 1 if sau else 0}


@frappe.whitelist()
def doi_ma_bien_the(ma_cu, ma_moi):
	"""Doi ma bien the. Luu y display_id chi doc, chi ghi duoc custom_id va barcode."""
	_quyen()
	c, k = _khoa()
	ma_moi = str(ma_moi or "").strip().upper()
	if not ma_moi:
		frappe.throw("Chưa nhập mã mới")
	if _bien_the(c, k, ma_moi):
		frappe.throw("Mã %s đã có trên Pancake rồi, không đổi trùng." % ma_moi)
	v = _bien_the(c, k, ma_cu)
	if not v:
		frappe.throw("Không thấy mã %s trên Pancake" % ma_cu)
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	_put_san_pham(
		c,
		k,
		pid,
		{
			"variations": [
				{
					"id": v.get("id"),
					"custom_id": ma_moi,
					"barcode": ma_moi,
				}
			]
		},
	)
	return {"ok": 1, "ma_cu": ma_cu, "ma_moi": ma_moi}


@frappe.whitelist()
def go_bien_the(ma):
	"""Bo mot bien the khoi san pham. Chan neu do la bien the duy nhat."""
	_quyen()
	c, k = _khoa()
	v = _bien_the(c, k, ma)
	if not v:
		return {"ok": 0, "thong_bao": "Không thấy mã %s trên Pancake, coi như đã sạch." % ma}
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	day_du = _san_pham(c, k, pid) if pid else {}
	bt = day_du.get("variations") or []
	if len(bt) <= 1:
		frappe.throw(
			"Mã %s là biến thể DUY NHẤT của sản phẩm \"%s\". Gỡ nó là mất luôn "
			"sản phẩm. Dùng đổi mã hoặc ẩn sản phẩm thay vì gỡ." % (ma, day_du.get("name") or "")
		)
	_put_san_pham(c, k, pid, {"variations": [{"id": v.get("id"), "is_removed": True}]})
	return {"ok": 1, "ma": ma, "con_lai": len(bt) - 1}


@frappe.whitelist()
def an_san_pham(ma, an=1):
	"""An ca san pham khoi gian hang (khong xoa du lieu, don hang cu con nguyen)."""
	_quyen()
	c, k = _khoa()
	v = _bien_the(c, k, ma)
	if not v:
		return {"ok": 0, "thong_bao": "Không thấy mã %s trên Pancake." % ma}
	pid = (v.get("product") or {}).get("id") or v.get("product_id")
	r = requests.put(
		"%s/shops/%s/products/update_hide" % (PANCAKE, c.pancake_shop_id),
		params={"api_key": k},
		json={"is_hide": bool(int(an)), "product_ids": [pid]},
		timeout=TIMEOUT,
	)
	if r.status_code not in (200, 201):
		frappe.log_error(title="Vagabond: an san pham Pancake loi", message=r.text[:1000])
		frappe.throw("Pancake từ chối (mã %s)." % r.status_code)
	return {"ok": 1, "ma": ma, "product_id": pid, "an": int(an)}


@frappe.whitelist()
def day_ma_len(danh_sach):
	"""Day hang loat ma Item len Pancake. Ma da co thi bo qua, khong tao trung."""
	_quyen()
	c, k = _khoa()
	if isinstance(danh_sach, str):
		danh_sach = [x.strip() for x in danh_sach.replace(",", " ").split() if x.strip()]
	ket = []
	for ma in danh_sach or []:
		ma = str(ma).strip().upper()
		if not frappe.db.exists("Item", ma):
			ket.append({"ma": ma, "ket_qua": "khong co ben Next"})
			continue
		if _bien_the(c, k, ma):
			ket.append({"ma": ma, "ket_qua": "da co tren Pancake"})
			continue
		it = frappe.get_doc("Item", ma)
		try:
			gia = int(it.standard_rate or 0)
		except (TypeError, ValueError):
			gia = 0
		anh = []
		if it.image and not it.image.startswith("/private"):
			anh = [get_url(it.image)]
		than = {
			"product": {
				"name": it.item_name or ma,
				"custom_id": ma,
				"is_published": True,
				"variations": [
					{
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
			json=than,
			timeout=TIMEOUT,
		)
		if r.status_code not in (200, 201) or not (r.json() or {}).get("success"):
			frappe.log_error(title="Vagabond: tao san pham Pancake loi", message=r.text[:1000])
			ket.append({"ma": ma, "ket_qua": "Pancake tu choi %s" % r.status_code})
			continue
		ket.append({"ma": ma, "ket_qua": "da tao", "gia": gia, "co_anh": 1 if anh else 0})
	return ket
