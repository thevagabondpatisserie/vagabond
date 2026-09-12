# -*- coding: utf-8 -*-
"""Đẩy mã hàng từ ERPNext sang Pancake POS - Uyên chỉ tạo mã MỘT lần.

Đã bấm thử thật ngày 01/08/2026: API tạo sản phẩm của Pancake NHẬN
`display_id` tự đặt (dù tài liệu không ghi trường này, giống vụ `tags`
của đơn hàng). Vậy nên mã trên Pancake sẽ đúng bằng mã Item trên ERPNext.

Điều kiện vận hành đi kèm (anh Việt làm trên Pancake):
- Tắt "Tự động tạo mã mẫu" trong Thiết lập Sản phẩm. Anh Việt xác nhận
  05/09/2026 là đang TẮT.
- Dọn các mã tự sinh cũ (BAWC00140S16CM...).

BẢN GIA CỐ 05/09/2026, issue 204
---------------------------------
Uyên phản ánh bấm nút đồng bộ sang Pancake mà không thấy chạy. Đi tra thì
chưa xác định được nguyên nhân của lần bấm 31/08 (đường Uyên bấm nằm ở một
Server Script khác, không nằm trong tệp này). Nhưng khi rà lại tệp này thì
Codex chỉ ra năm chỗ hỏng thật, và bản này sửa cả năm:

1. `_tim_tren_pancake` cũ lấy `page_size=5`, KHÔNG phân trang, và trả về
   ngay bản khớp đầu tiên. Mã thật nằm ở trang sau thì báo là không có, rồi
   đi tạo bản thứ hai. Nay quét đủ trang và trả về TẤT CẢ bản khớp khít.
2. Trả về chỉ có `ok` 1 hoặc 0, gộp bốn tình huống khác hẳn nhau vào hai
   con số. Nay trả về trạng thái có tên, xem pancake_ket_qua.py.
3. Gửi lệnh tạo xong mà mạng đứt thì hàm cũ ném lỗi, người bấm lại, và
   Pancake có hai mã. Nay tình huống đó thành `chua_ro` và KHÔNG được thử
   lại mù; phải đi kiểm trạng thái trước.
4. Hai người bấm cùng lúc thì cả hai đều thấy "chưa có" rồi cùng tạo. Nay
   khoá DB và dấu gửi bền theo shop/mã bảo vệ cả worker chết, không dựa TTL.
5. Giá 0 vẫn đẩy, chỉ nhắn một câu trong lời báo thành công nên không ai
   đọc. Nay chặn hẳn, trừ khi người bấm nói rõ là cố ý.

MỘT ĐIỀU CHƯA LÀM, ghi ra để không ai tưởng đã xong
---------------------------------------------------
Mỗi lần POST tạo MỘT sản phẩm với ĐÚNG MỘT mẫu mã. Nên đẩy hai suất vé sẽ
ra hai sản phẩm rời, không phải một sản phẩm hai suất như Uyên đang dựng
bên Pancake. Đường tạo sản phẩm nhiều mẫu mã CHƯA được định nghĩa và chưa
được kiểm chứng, nên bản này không hứa gì về việc nhóm. Codex nêu
05/09/2026.
"""

import frappe
import requests
from frappe.utils import cint, flt, get_url

from vagabond import pancake_ket_qua as kq
from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

# Quét tối đa bấy nhiêu trang khi đi tìm một mã. Một trang 100 mẫu mã, mà
# cả tiệm mới có hơn ba trăm mã, nên chạm trần nghĩa là có chuyện.
TRAN_TRANG = 40
MOI_TRANG = 100

# Dấu gửi trong DB giữ qua reload, mất Redis và worker chết. Integration
# Request của Frappe có clear_old_logs(30), nên không dùng làm hàng rào lâu dài.
DT_DAY = "Vagabond Day Pancake"


def _ten_luot(shop, ma):
	import hashlib
	return hashlib.sha256((str(shop) + "\0" + kq.chuan_ma(ma)).encode()).hexdigest()


def _ket_qua(tt, ma, bao=None):
	return {"ok": int(tt in (kq.KQ_DA_CO, kq.KQ_DA_TAO)), "trang_thai": tt,
		"thong_bao": bao or kq.thong_bao(tt, ma)}


def _doc_luot(ten, khoa=False):
	return frappe.db.get_value(DT_DAY, ten, ["name", "trang_thai", "thong_bao"], as_dict=True, for_update=khoa)


def _tra_luot(luot, ma):
	tt = luot.trang_thai
	if tt == "cho":
		return _ket_qua("chua_ro", ma, "Đã nhận yêu cầu. Chờ một chút rồi bấm Kiểm lại; không gửi thêm.")
	if tt == "dang_gui":
		return _ket_qua("chua_ro", ma, "Lượt gửi đã bắt đầu, chưa xác minh kết quả. Bấm Kiểm lại; không gửi thêm.")
	return _ket_qua(tt, ma, luot.thong_bao)


def tim_het_tren_pancake(c, k, ma):
	"""Tìm ĐỦ mọi mẫu mã mang đúng mã này. Trả về (danh sách, quét đủ chưa).

	Hàm cũ lấy năm kết quả đầu và dừng ở bản khớp đầu tiên. Hai chỗ sai:
	mã thật có thể nằm ngoài năm kết quả đó, và nếu có hai bản trùng mã thì
	nó chỉ thấy một.

	`quét đủ chưa` trả về False khi chạm trần trang mà chưa chứng minh được
	là đã hết. Bên gọi KHÔNG được coi danh sách rỗng của một lần quét dở là
	bằng chứng mã chưa tồn tại, vì kết luận đó dẫn thẳng tới việc tạo trùng.
	"""
	ds, trang = [], 1
	while trang <= TRAN_TRANG:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": MOI_TRANG, "page_number": trang},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
		goi = r.json() or {}
		data = goi.get("data")
		if not isinstance(data, list):
			# Trả 200 mà không có mảng data thì đó không phải một lần quét
			# thành công. Đừng đọc thành "không có mã nào".
			return [], False
		ds.extend(data)
		if len(data) < MOI_TRANG:
			return kq.khop_chinh_xac(ds, ma), True
		trang += 1
	return kq.khop_chinh_xac(ds, ma), False


def _gia_niem_yet(it):
	"""Giá đem đẩy sang Pancake.

	Ưu tiên bảng giá bán chuẩn của ERPNext, vì đó mới là con số kế toán và
	màn bán hàng đang dùng. `standard_rate` chỉ là số gõ trên form Item và
	có thể lạc hậu so với bảng giá.
	"""
	bang = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	if bang:
		g = frappe.db.get_value(
			"Item Price",
			{"item_code": it.name, "price_list": bang, "selling": 1},
			"price_list_rate",
		)
		if flt(g) > 0:
			return flt(g)
	return flt(it.standard_rate or 0)


def trang_thai_tren_pancake(item_code):
	"""Đối chiếu chỉ GET Pancake; không có đường POST lại sau kết quả chưa rõ."""
	ma = kq.chuan_ma(item_code)
	c = cfg(); k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")
	luot = _doc_luot(_ten_luot(c.pancake_shop_id, ma))
	if luot and luot.trang_thai == "cho":
		return _tra_luot(luot, ma)
	try:
		ds, du = tim_het_tren_pancake(c, k, ma)
	except Exception:
		return _ket_qua("chua_ro", ma, "Chưa đọc được Pancake. Bấm Kiểm lại sau; không gửi thêm.")
	if not du:
		return _ket_qua("chua_ro", ma, "Chưa quét hết Pancake. Không gửi thêm; bấm Kiểm lại sau.")
	if not ds and luot and luot.trang_thai != "loi":
		# Kết quả tìm rỗng không chứng minh POST trước chưa thành công.
		return _tra_luot(luot, ma)
	return _ket_qua(kq.xep_ket_qua_tim(len(ds)), ma,
		kq.thong_bao(kq.xep_ket_qua_tim(len(ds)), ma, len(ds)))


@frappe.whitelist(methods=["POST"])
def tao_tren_pancake(item_code, cho_phep_gia_0=0):
	"""Lưu ý định, enqueue sau commit; request người dùng KHÔNG POST Pancake."""
	from vagabond.danh_muc import _duoc_tao, _kiem_quyen
	_kiem_quyen()
	if not _duoc_tao() or not frappe.has_permission("Item", "write"):
		frappe.throw("Chỉ kế toán, thu mua hoặc giám đốc mới đẩy mã sang Pancake được.")
	it = frappe.get_doc("Item", item_code)
	ma = kq.chuan_ma(it.item_code)
	if not kq.duoc_xuat_ban(it.disabled, it.is_sales_item):
		return _ket_qua("loi", ma, "Mã đang ngừng dùng hoặc không phải hàng bán, không đẩy sang Pancake.")
	c = cfg(); k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")
	gia = _gia_niem_yet(it)
	duoc, vi_sao = kq.gia_dung_de_day(gia, cint(cho_phep_gia_0))
	if not duoc:
		return _ket_qua(vi_sao, ma)
	# Khoá Item cho tới cuối request, không có TTL/Redis và không gọi mạng.
	frappe.db.sql("select name from `tabItem` where name=%s for update", (it.name,))
	ten = _ten_luot(c.pancake_shop_id, ma)
	cu = _doc_luot(ten, khoa=True)
	if cu and cu.trang_thai != "loi":
		if cu.trang_thai == "cho":
			frappe.enqueue("vagabond.pancake_sp.chay_luot_day", ten=ten,
				queue="long", timeout=1800, enqueue_after_commit=True)
		return _tra_luot(cu, ma)
	anh = [get_url(it.image)] if it.image and not it.image.startswith("/private") else []
	body = {"product": {"name": it.item_name or ma, "is_published": True,
		"variations": [{"display_id": ma, "custom_id": ma, "barcode": ma,
			"retail_price": int(gia), "images": anh, "is_hidden": False, "fields": []}]}}
	du_lieu = frappe.as_json(body)
	if cu:
		frappe.db.set_value(DT_DAY, ten, {"du_lieu": du_lieu, "trang_thai": "cho",
			"nguoi_yeu_cau": frappe.session.user, "thong_bao": ""})
	else:
		frappe.get_doc({"doctype": DT_DAY, "shop": str(c.pancake_shop_id), "ma": ma,
			"mat_hang": it.name, "nguoi_yeu_cau": frappe.session.user,
			"du_lieu": du_lieu, "trang_thai": "cho"}).insert(ignore_permissions=True, set_name=ten)
	# Frappe16.27.1 background_jobs.enqueue gắn callback vào db.after_commit.
	# Worker không thể gọi Pancake trước khi dấu ý định được lưu bền.
	frappe.enqueue("vagabond.pancake_sp.chay_luot_day", ten=ten,
		queue="long", timeout=1800, enqueue_after_commit=True)
	return _ket_qua("chua_ro", ma, "Đã nhận yêu cầu. Chờ một chút rồi bấm Kiểm lại; không gửi thêm.")


def chay_luot_day(ten):
	"""Chỉ chạy job nền riêng: commit dấu gửi TRƯỚC POST, không gọi từ request."""
	import json
	# Hai job trùng cùng chờ một hàng; job sau chỉ thấy trạng thái đã nhận.
	rows = frappe.db.sql("select name, trang_thai, shop, ma, du_lieu from `tabVagabond Day Pancake` where name=%s for update", (ten,), as_dict=True)
	if not rows or rows[0].trang_thai != "cho":
		return
	luot = rows[0]
	frappe.db.set_value(DT_DAY, ten, "trang_thai", "dang_gui")
	frappe.db.commit()
	# Nếu worker chết từ đây trở đi, dấu dang_gui vẫn chặn mọi POST lại.
	ma = luot.ma
	c = cfg(); k = key(c, "pancake_api_key")
	if not k or str(c.pancake_shop_id) != luot.shop:
		frappe.db.set_value(DT_DAY, ten, {"trang_thai": "loi", "thong_bao": "Cấu hình Pancake đã đổi. Kiểm tra shop và bấm Đẩy lại."})
		return
	try:
		ds, du = tim_het_tren_pancake(c, k, ma)
	except Exception:
		ds, du = [], False
	if not du:
		frappe.db.set_value(DT_DAY, ten, {"trang_thai": "loi", "thong_bao": "Chưa quét hết Pancake, chưa gửi lệnh tạo. Có thể bấm Đẩy để thử lại."})
		return
	if ds:
		tt = kq.xep_ket_qua_tim(len(ds))
		frappe.db.set_value(DT_DAY, ten, {"trang_thai": tt, "thong_bao": kq.thong_bao(tt, ma, len(ds))})
		return
	tt = "chua_ro"
	try:
		r = requests.post("%s/shops/%s/products" % (PANCAKE, luot.shop),
			params={"api_key": k}, json=json.loads(luot.du_lieu), timeout=TIMEOUT)
		goi = r.json()
		if r.status_code in (200, 201) and isinstance(goi, dict) and goi.get("success") is True:
			tt = "da_tao"
	except Exception:
		pass  # Đã gửi: mọi lỗi/mất JSON giữ chưa rõ, không cho POST lần hai.
	frappe.db.set_value(DT_DAY, ten, {"trang_thai": tt, "thong_bao": kq.thong_bao(tt, ma)})
