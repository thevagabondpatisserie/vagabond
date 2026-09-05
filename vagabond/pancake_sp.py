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
   có khoá theo shop và mã.
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

# Khoá sống bấy nhiêu giây. Đủ dài để một lượt gọi Pancake xong, đủ ngắn để
# một tiến trình chết không khoá mã đó mãi mãi.
KHOA_GIAY = 90


def _khoa_ten(shop, ma):
	return "vgb_day_pancake:%s:%s" % (shop, kq.chuan_ma(ma))


def _giu_khoa(shop, ma):
	"""Giành khoá cho cặp shop và mã. Trả về True nếu giành được.

	Hai người cùng bấm một mã, hoặc một người bấm hai lần vì sốt ruột, thì
	cả hai lượt đều thấy "chưa có" rồi cùng gửi lệnh tạo. Tìm trước khi tạo
	KHÔNG chặn được chuyện đó, vì hai lượt chạy xen kẽ nhau.
	"""
	try:
		c = frappe.cache()
		# setnx là phép nguyên tử: chỉ đặt được khi chưa ai đặt.
		if not c.setnx(_khoa_ten(shop, ma), b"1"):
			return False
		c.expire(_khoa_ten(shop, ma), KHOA_GIAY)
		return True
	except Exception:
		# Không có Redis thì thà chạy tiếp còn hơn chặn hết việc, nhưng phải
		# ghi lại để biết mình đang chạy không khoá.
		frappe.log_error(
			title="Vagabond: khong giu duoc khoa day Pancake",
			message=frappe.get_traceback(),
		)
		return True


def _nha_khoa(shop, ma):
	try:
		frappe.cache().delete_value(_khoa_ten(shop, ma))
	except Exception:
		pass


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
	try:
		bang = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	except Exception:
		bang = None
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
	"""Mã này đang ở tình trạng nào bên Pancake. CHỈ ĐỌC, không tạo gì.

	Đây là đường để bấm "Kiểm lại" sau khi một lần đẩy trả về chưa rõ. Codex
	yêu cầu: chưa rõ thì đi kiểm, không POST lại.
	"""
	ma = kq.chuan_ma(item_code)
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")
	try:
		ds, du = tim_het_tren_pancake(c, k, ma)
	except Exception:
		frappe.log_error(title="Vagabond: tim ma tren Pancake loi", message=frappe.get_traceback())
		return {"trang_thai": kq.KQ_LOI, "so_ban": 0, "quet_du": 0,
			"thong_bao": kq.thong_bao(kq.KQ_LOI, ma)}
	if not du:
		return {"trang_thai": kq.KQ_CHUA_RO, "so_ban": len(ds), "quet_du": 0,
			"thong_bao": "Chưa quét hết danh mục Pancake nên chưa dám kết luận về %s." % ma}
	tt = kq.xep_ket_qua_tim(len(ds))
	return {"trang_thai": tt, "so_ban": len(ds), "quet_du": 1,
		"thong_bao": kq.thong_bao(tt, ma, len(ds))}


@frappe.whitelist()
def tao_tren_pancake(item_code, cho_phep_gia_0=0):
	"""Đẩy một mã sang Pancake. Trả về trạng thái có tên, xem pancake_ket_qua.

	Đọc đầu tệp để biết năm chỗ đã gia cố. Điều quan trọng nhất khi sửa hàm
	này về sau: KHÔNG được biến `chua_ro` thành một lần POST nữa.
	"""
	if not frappe.has_permission("Item", "write"):
		frappe.throw("Anh chị không có quyền sửa hàng hoá")

	it = frappe.get_doc("Item", item_code)
	ma = kq.chuan_ma(it.item_code)

	if not kq.duoc_xuat_ban(it.disabled, it.is_sales_item):
		return {"ok": 0, "trang_thai": kq.KQ_LOI, "so_ban": 0,
			"thong_bao": "Mã %s đang ngừng dùng hoặc không phải hàng bán, "
				"không đưa lên Pancake." % ma}

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")

	gia = _gia_niem_yet(it)
	duoc_gia, vi_sao = kq.gia_dung_de_day(gia, cint(cho_phep_gia_0))
	if not duoc_gia:
		return {"ok": 0, "trang_thai": vi_sao, "so_ban": 0,
			"thong_bao": kq.thong_bao(vi_sao, ma)}

	if not _giu_khoa(c.pancake_shop_id, ma):
		return {"ok": 0, "trang_thai": kq.KQ_CHUA_RO, "so_ban": 0,
			"thong_bao": "Mã %s đang được đẩy ở một lượt khác. "
				"Chờ một chút rồi bấm Kiểm lại." % ma}

	try:
		try:
			ds, du = tim_het_tren_pancake(c, k, ma)
		except Exception:
			frappe.log_error(title="Vagabond: tim ma tren Pancake loi",
				message=frappe.get_traceback())
			return {"ok": 0, "trang_thai": kq.KQ_LOI, "so_ban": 0,
				"thong_bao": kq.thong_bao(kq.KQ_LOI, ma)}

		# Quét dở thì DỪNG. Danh sách rỗng của một lần quét chưa xong không
		# phải bằng chứng mã chưa tồn tại.
		if not du:
			return {"ok": 0, "trang_thai": kq.KQ_CHUA_RO, "so_ban": len(ds),
				"thong_bao": "Chưa quét hết danh mục Pancake nên chưa dám tạo %s. "
					"Bấm Kiểm lại sau ít phút." % ma}

		tt = kq.xep_ket_qua_tim(len(ds))
		if not kq.duoc_tao(tt):
			return {"ok": 0, "trang_thai": tt, "so_ban": len(ds),
				"thong_bao": kq.thong_bao(tt, ma, len(ds))}

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
						"retail_price": int(gia),
						"images": anh,
						"is_hidden": False,
						"fields": [],
					}
				],
			}
		}
		try:
			r = requests.post(
				"%s/shops/%s/products" % (PANCAKE, c.pancake_shop_id),
				params={"api_key": k},
				json=body,
				timeout=TIMEOUT,
			)
		except Exception:
			# Đứt giữa chừng: rất có thể Pancake ĐÃ nhận. Không được nói là
			# lỗi, vì nói lỗi thì người ta bấm lại và đẻ ra mã thứ hai.
			frappe.log_error(title="Vagabond: day Pancake khong ro ket qua",
				message=frappe.get_traceback())
			return {"ok": 0, "trang_thai": kq.KQ_CHUA_RO, "so_ban": 0,
				"thong_bao": kq.thong_bao(kq.KQ_CHUA_RO, ma)}

		if r.status_code not in (200, 201) or not (r.json() or {}).get("success"):
			frappe.log_error(title="Vagabond: tao san pham Pancake loi",
				message=r.text[:1000])
			return {"ok": 0, "trang_thai": kq.KQ_LOI, "so_ban": 0,
				"thong_bao": kq.thong_bao(kq.KQ_LOI, ma)}

		return {"ok": 1, "trang_thai": kq.KQ_DA_TAO, "so_ban": 1,
			"gia": int(gia), "thong_bao": kq.thong_bao(kq.KQ_DA_TAO, ma)}
	finally:
		_nha_khoa(c.pancake_shop_id, ma)

