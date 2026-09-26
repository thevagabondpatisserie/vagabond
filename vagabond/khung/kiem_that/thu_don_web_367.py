"""#367: đơn web đi trọn đường trên site thật, trong điểm lưu, không gọi ra ngoài.

Tầng khung đã chạy phép thuần và chạy tao_don với Frappe giả. Tầng này hỏi
câu tầng khung không trả lời được: Frappe THẬT có nhận bản ghi `Vagabond Don
Web` không (ô unique, chỉ mục, đặt tên DW-.., quyền), trang /banh/xong THẬT
có mở được bằng token vừa sinh không, và hook ghi sổ hoá đơn có đổi trạng
thái đúng không.

Mọi đường ra ngoài đều bị chặn bằng `patch`: Pancake, Ahamove, Meta. Cờ
`vagabond_kiem_that` giữ nguyên suốt ca, nên kể cả khi quên một patch thì
xep_capi/gui_capi cũng tự im lặng. Riêng ca gửi CAPI cố ý tắt cờ đó trong
một khối `try/finally`, và `requests.post` đã bị thay trước khi tắt.
"""

import json
from unittest.mock import patch

import frappe

from vagabond import don_hang, don_web
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la

NONCE = "KiemThat367" + "x" * 13


class _Tra:
	def __init__(self, ma, du_lieu):
		self.status_code, self._d, self.text = ma, du_lieu, json.dumps(du_lieu)

	def json(self):
		return self._d


def _mot_mon():
	"""Một mã bánh ô có giá để tao_don tính được tiền bánh thật.

	Site CI trống, không có bánh nào, nên ca tự gieo một Item trong điểm lưu
	(ghi vào _DA_TAO để nền rollback), không lệ thuộc dữ liệu có sẵn (Codex,
	bench đỏ run 36148002675). Site thật có bánh thì dùng luôn bánh đang bán.
	"""
	co = frappe.db.get_value("Item", {"item_code": ["like", "BAWC%"], "disabled": 0,
		"standard_rate": [">", 0]}, ["item_code", "standard_rate"], as_dict=True)
	if co:
		return co
	from vagabond.khung.kiem_that import nen
	d = frappe.get_doc({"doctype": "Item", "item_code": "BAWC-KIEM-367", "item_name": "Bánh ô kiểm 367",
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_sales_item": 1, "standard_rate": 668000})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return frappe._dict(item_code=d.name, standard_rate=d.standard_rate)


def _goi(don, pancake):
	vet = []

	def post(url, **k):
		vet.append(k.get("json"))
		return pancake()

	with patch.object(don_hang, "phi_giao", lambda **k: {"ok": 1, "total_fee": 36000}), \
			patch.object(don_hang, "_uuid_tu_ma", lambda c, k, ma: "00000000-0000-0000-0000-000000000367"), \
			patch.object(don_hang, "key", lambda c, f: "khoa-thu"), \
			patch.object(don_hang.requests, "post", post), \
			patch.object(don_web, "nguong_mien_phi", lambda: 1000000):
		c = frappe.get_cached_doc("Vagabond Settings")
		cu = c.pancake_shop_id
		c.pancake_shop_id = c.pancake_shop_id or "67355"
		try:
			r = don_hang.tao_don(json.dumps(don))
		finally:
			c.pancake_shop_id = cu
	return r, vet


def _don(ma, sl=1):
	return {"ho_ten": "Kiểm Thử Ba Sáu Bảy", "dien_thoai": "0900000367", "tu_lay": False,
		"dia_chi": "9 Trần Cao Vân, Phường Sài Gòn", "ngay_nhan": "2026-12-01T13:00:00",
		"items": [{"variation_id": ma, "quantity": sl}], "nonce": NONCE, "dong_y": True, "thanh_toan": "bank"}


@ca("367 đơn web: ghi bản ghi thật, token mở được biên nhận, gửi trùng không tạo thêm, token sai là 404")
def _():
	mon = _mot_mon()
	if not mon:
		dung("site có ít nhất một bánh ô có giá", False)
		return
	r, vet = _goi(_don(mon.item_code), lambda: _Tra(200, {"success": True, "data": {"id": "9036701"}}))
	la("tao_don trả ok", r.get("ok"), 1)
	ten = r.get("ma_yeu_cau")
	_DA_TAO.append((don_web.DOCTYPE, ten))
	d = frappe.get_doc(don_web.DOCTYPE, ten)
	la("trạng thái", d.trang_thai, "Da nhan")
	la("mã Pancake", d.pancake_display_id, "9036701")
	la("tiền bánh máy chủ tính", int(d.tien_banh), int(mon.standard_rate))
	dung("tên đúng mẫu DW-", ten.startswith("DW-"))
	token = r["duong_dan"].rsplit("/", 1)[1]
	dung("CSDL giữ băm, không giữ token", d.token_hash == don_web.bam(token) and token not in (d.snapshot or ""))
	bn = don_web.bien_nhan_theo_token(token)
	la("token mở đúng bản ghi", bn and bn["bien_nhan"]["ma"], ten)
	la("token sai không mở được", don_web.bien_nhan_theo_token("b" * 43), None)
	r2, vet2 = _goi(_don(mon.item_code), lambda: _Tra(200, {"data": {"id": "khong-duoc-goi"}}))
	la("gửi trùng trả bản cũ", (r2.get("trung"), r2.get("ma_yeu_cau"), r2.get("duong_dan")), (1, ten, r["duong_dan"]))
	la("gửi trùng không gọi Pancake", len(vet2), 0)
	la("một lần gọi Pancake", len(vet), 1)
	la("phí khách trả khi dưới ngưỡng", vet[0]["shipping_fee"], 0 if int(mon.standard_rate) >= 1000000 else 36000)
	# Trang www THẬT: 404 khi token sai.
	from vagabond.www.banh import xong
	frappe.form_dict.token = "b" * 43
	try:
		xong.get_context(frappe._dict())
		dung("token sai phải 404", False)
	except frappe.PageDoesNotExistError:
		pass
	frappe.form_dict.token = token
	ctx = frappe._dict()
	xong.get_context(ctx)
	dung("trang thật dựng được biên nhận", ten in ctx.than and "0900000367" not in ctx.than)


@ca("367 đơn web: Pancake mất phản hồi thì Chờ đối soát, không gọi lại; hoá đơn ghi sổ thì Đã ghi sổ và xếp Purchase")
def _():
	mon = _mot_mon()
	if not mon:
		return
	don = dict(_don(mon.item_code, 2), nonce=NONCE.replace("x", "y"))

	def mat():
		raise OSError("timeout gia lap")
	r, vet = _goi(don, mat)
	la("khách vẫn có biên nhận", r.get("ok"), 1)
	ten = r.get("ma_yeu_cau")
	_DA_TAO.append((don_web.DOCTYPE, ten))
	la("không gọi lại", len(vet), 1)
	la("Chờ đối soát", frappe.db.get_value(don_web.DOCTYPE, ten, "trang_thai"), "Cho doi soat")
	# Sales ghép tay: điền mã rồi chọn Đã nhận, như hướng dẫn trên form.
	d = frappe.get_doc(don_web.DOCTYPE, ten)
	d.pancake_display_id = "9036702"
	d.trang_thai = "Da nhan"
	d.save(ignore_permissions=True)
	# Hook ghi sổ với một hoá đơn giả mang mã đó (không dựng Sales Invoice thật:
	# hook chỉ đọc hai ô mã và tổng tiền).
	# Hook về sớm khi cờ vagabond_kiem_that bật (nen._cach_ly bật suốt ca), nên
	# tắt cờ đúng quanh lời gọi; xep_capi đã bị thay trước nên không ra ngoài (Codex).
	xep = []
	co = frappe.flags.vagabond_kiem_that
	with patch.object(don_web, "xep_capi", lambda *a, **k: xep.append((a, k))):
		frappe.flags.vagabond_kiem_that = False
		try:
			don_web.khi_ghi_so_hoa_don(frappe._dict(name="SINV-KIEM-367", custom_pancake_id="",
				custom_pancake_display_id="9036702", grand_total=1336000))
		finally:
			frappe.flags.vagabond_kiem_that = co
	d.reload()
	la("Đã ghi sổ", d.trang_thai, "Da ghi so")
	la("giá trị ghi sổ", int(d.gia_tri_ghi_so), 1336000)
	la("xếp Purchase sau commit", xep and (xep[0][0][1], xep[0][1].get("sau_commit")), ("Purchase", True))
	la("hook chỉ xếp đúng một lần", len(xep), 1)


@ca("367 CAPI: gửi đúng event_id và giá trị, băm số điện thoại, không gửi lại lần hai")
def _():
	mon = _mot_mon()
	if not mon:
		return
	r, _v = _goi(dict(_don(mon.item_code), nonce=NONCE.replace("x", "z")),
		lambda: _Tra(200, {"data": {"id": "9036703"}}))
	ten = r.get("ma_yeu_cau")
	_DA_TAO.append((don_web.DOCTYPE, ten))
	d = frappe.get_doc(don_web.DOCTYPE, ten)
	gui = []

	def post(url, params=None, json=None, timeout=None):
		gui.append({"url": url, "than": json, "co_token": bool((params or {}).get("access_token"))})
		return _Tra(200, {"events_received": 1})
	co = frappe.flags.vagabond_kiem_that
	with patch("requests.post", post), patch.object(don_web, "pixel_id", lambda: "123456"), \
			patch.object(don_web, "key", lambda c, f: "token-thu"):
		frappe.flags.vagabond_kiem_that = False
		try:
			don_web.gui_capi(ten, "GuiDon")
			don_web.gui_capi(ten, "GuiDon")
		finally:
			frappe.flags.vagabond_kiem_that = co
	la("gửi đúng một lần", len(gui), 1)
	ev = gui[0]["than"]["data"][0] if gui else {}
	la("đúng event_id", ev.get("event_id"), d.event_id_gui_don)
	la("giá trị là tiền bánh", ev.get("custom_data", {}).get("value"), int(d.tien_banh))
	la("số điện thoại đã băm", ev.get("user_data", {}).get("ph"), [don_web.bam("84900000367")])
	dung("token Meta đi trong tham số, không nằm trong thân", gui and gui[0]["co_token"] and "token-thu" not in json.dumps(ev))
	dung("URL nguồn không mang token biên nhận", "/banh/xong" not in ev.get("event_source_url", ""))
