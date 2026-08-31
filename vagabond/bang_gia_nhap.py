# -*- coding: utf-8 -*-
"""Bảng giá nhập tự đuổi theo giá trên hoá đơn mua.

ANH VIỆT HỎI 31/08/2026
------------------------
*"Giá trên phiếu nhập kho đó lấy ở đâu ra? Lúc Kiên làm phiếu nhập đâu có
chỗ để nhập giá vào đâu?"*

Đường đi của con số đó có ba chặng, không ai gõ chặng nào:

    Bảng giá nhập  ->  Đơn mua hàng  ->  Phiếu nhập kho

Ca thật: món NVLT00116 trái cherry. Bảng giá nhập ghi 420 đ mỗi Gram, đặt
ngày 30/07/2026. Đơn mua ngày 20/08 kéo con số đó xuống. Phiếu nhập dựng
từ đơn mua nên thừa hưởng luôn. Hoá đơn thật của nhà cung cấp ngày 19/08
là 480.000 đ một Kg. Bảng giá trễ 60.000 đ một Kg và không ai biết.

VÌ SAO BẢNG GIÁ ĐỨNG YÊN
------------------------
Thiết lập kho đang là: món chưa có giá thì lần mua đầu tiên hệ tự ghi một
dòng vào bảng giá; đã có giá rồi thì không bao giờ cập nhật nữa. Bảng giá
đóng băng ở giá lần mua đầu, còn nhà cung cấp thì tăng giá mỗi quý.

VÌ SAO KHÔNG BẬT THẲNG Ô CỦA ERPNext
------------------------------------
ERPNext có sẵn một ô "cập nhật lại bảng giá theo giá giao dịch". Bật ô đó
là mọi chứng từ mua đều ghi ngược vào bảng giá, kể cả đơn mua và phiếu
nhập - mà hai thứ đó lấy giá TỪ chính bảng giá. Vòng tròn, không chữa
được gì.

Nặng hơn: nó ghi cả những dòng đang mang đơn vị sai. Ngày 31/08 hệ còn
hàng trăm dòng hoá đơn có đơn vị nhà cung cấp chưa khai, những dòng đó
đang bị hạ ngầm về đơn vị kho hệ số 1. Một dòng "4 BAG giá 280.000" bị
đọc thành "4 Gram giá 280.000" mà ghi vào bảng giá là bảng giá thành 280
nghìn một gram, tức sai gấp một nghìn lần. Bật ô của ERPNext lúc này là
đầu độc bảng giá nặng hơn hiện trạng.

Nên chỗ này làm cửa riêng, hẹp hơn ba tầng:

  1. Chỉ nghe HOÁ ĐƠN MUA lúc ghi sổ. Đơn mua và phiếu nhập không được
     nói, vì giá của chúng vốn chảy ra từ bảng giá.
  2. Chỉ nhận dòng có ĐƠN VỊ SẠCH. Dòng nào mang dấu vân tay của đường hạ
     ngầm thì bỏ qua và đếm lại, không ghi.
  3. Ghi xong để lại vết trên chính dòng bảng giá: giá cũ, giá mới, số hoá
     đơn nào đổi. Tháng sau có ai hỏi vì sao giá vốn nhảy thì truy được.

Hỏng ở đây KHÔNG được phép chặn kế toán ghi sổ. Cả hàm bọc trong try, hỏng
thì ghi nhật ký rồi thôi. Bảng giá chỉ là gợi ý cho lần đặt hàng sau; giá
vốn thật đã do chính tờ hoá đơn này quyết rồi.
"""

import frappe
from frappe.utils import flt, nowdate

from vagabond import dvt_mua

TEN_BANG_GIA = "Bảng giá nhập"


# ------------------------------------------------------------- phần thuần


# Vì sao dòng này không được ghi vào bảng giá. Chuỗi rỗng nghĩa là ghi được.
BO_KHONG_MA = "khong_ma_hang"
BO_GIA_KHONG = "gia_khong"
BO_KHONG_DON_VI = "khong_don_vi"
BO_DON_VI_CHUA_KHAI = "don_vi_chua_khai"


def ly_do_bo_qua(ma_hang, dvt_dong, he_so_dong, gia, dvt_ncc=""):
	"""Dòng hoá đơn này có được phép ghi vào bảng giá không. THUẦN.

	Trả chuỗi rỗng nếu ghi được, còn không thì trả mã lý do.

	Thứ tự xét có chủ ý: đơn vị chưa khai xét CUỐI, để những dòng vốn đã
	hỏng vì lý do khác không bị đếm nhầm vào con số "đơn vị cần khai" mà
	màn hình đưa cho thu mua.
	"""
	if not str(ma_hang or "").strip():
		return BO_KHONG_MA
	try:
		g = float(gia or 0)
	except (TypeError, ValueError):
		g = 0.0
	if g <= 0:
		return BO_GIA_KHONG
	if not str(dvt_dong or "").strip():
		return BO_KHONG_DON_VI
	if dvt_mua.don_vi_chua_khai(dvt_ncc, dvt_dong, he_so_dong):
		return BO_DON_VI_CHUA_KHAI
	return ""


def dang_ke(gia_cu, gia_moi, nguong=0.005):
	"""Giá có thật sự đổi không, hay chỉ là sai số làm tròn. THUẦN.

	Không có phép này thì mỗi lần ghi sổ một tờ hoá đơn là một dòng ghi chú
	mới trên bảng giá dù giá y hệt, và sau ba tháng không ai đọc nổi lịch
	sử của một món nào nữa.
	"""
	try:
		a = float(gia_cu or 0)
		b = float(gia_moi or 0)
	except (TypeError, ValueError):
		return False
	return abs(a - b) > float(nguong)


# ------------------------------------------------------- phần cần Frappe


def _ghi_mot_dong(ma_hang, dvt, gia, ngay, so_hd, ten_hd):
	"""Đặt lại giá của một món trong Bảng giá nhập. Trả 'sua', 'them' hoặc ''."""
	ten = frappe.db.get_value(
		"Item Price", {"item_code": ma_hang, "price_list": TEN_BANG_GIA, "uom": dvt}, "name"
	)
	if ten:
		cu = flt(frappe.db.get_value("Item Price", ten, "price_list_rate"))
		if not dang_ke(cu, gia):
			return ""
		doc = frappe.get_doc("Item Price", ten)
		doc.price_list_rate = gia
		doc.valid_from = ngay
		doc.flags.ignore_permissions = True
		doc.save()
		doc.add_comment(
			"Comment",
			"Giá nhập đổi từ %s thành %s mỗi %s, theo hoá đơn %s (%s)."
			% (cu, gia, dvt, so_hd or ten_hd, ten_hd),
		)
		return "sua"

	doc = frappe.get_doc({
		"doctype": "Item Price",
		"item_code": ma_hang,
		"price_list": TEN_BANG_GIA,
		"uom": dvt,
		"price_list_rate": gia,
		"valid_from": ngay,
		"buying": 1,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.add_comment(
		"Comment",
		"Dựng giá nhập %s mỗi %s theo hoá đơn %s (%s)." % (gia, dvt, so_hd or ten_hd, ten_hd),
	)
	return "them"


def cap_nhat_tu_hoa_don(doc, method=None):
	"""Ghi sổ một hoá đơn mua thì bảng giá nhập đuổi theo. Móc on_submit."""
	try:
		return _chay(doc)
	except Exception:
		# Bảng giá lệch một hôm thì đặt hàng hơi sai, còn chặn kế toán ghi sổ
		# là cả tiệm đứng. Không bao giờ ném ngược lên.
		frappe.log_error(
			frappe.get_traceback(), "bang_gia_nhap: cap nhat tu %s" % doc.name
		)
		return None


def _chay(doc):
	ngay = str(doc.get("posting_date") or nowdate())
	so_hd = (doc.get("bill_no") or "").strip()
	kq = {"sua": 0, "them": 0, "giu_nguyen": 0, "bo_qua": {}}
	for d in doc.get("items") or []:
		dvt_ncc = dvt_mua.dvt_tren_hoa_don(d.get("description"))
		vi_sao = ly_do_bo_qua(
			d.get("item_code"), d.get("uom"), d.get("conversion_factor"),
			d.get("rate"), dvt_ncc,
		)
		if vi_sao:
			kq["bo_qua"][vi_sao] = kq["bo_qua"].get(vi_sao, 0) + 1
			continue
		viec = _ghi_mot_dong(
			d.get("item_code"), d.get("uom"), flt(d.get("rate")), ngay, so_hd, doc.name
		)
		if viec:
			kq[viec] += 1
		else:
			kq["giu_nguyen"] += 1
	return kq


@frappe.whitelist()
def can_khai_don_vi(gioi_han=400):
	"""CHỈ ĐỌC: những đơn vị nhà cung cấp đang ghi mà món chưa khai.

	Đây là câu trả lời cho "anh phải làm gì để nó không lệch". Gộp theo
	cặp (món, đơn vị nhà cung cấp) chứ không liệt kê từng dòng: cùng một
	món của cùng một nhà cung cấp thì khai MỘT lần là xong cả trăm tờ sau.

	Kèm sẵn tên đơn vị tiếng Việt gợi ý, còn hệ số thì để trống - hệ số là
	con số của người, máy không được bịa. Đọc `khai_don_vi` trong
	`doi_chieu_mua.py` để biết vì sao.
	"""
	if not frappe.has_permission("Purchase Invoice", "read"):
		frappe.throw("Bạn không có quyền xem danh mục hoá đơn mua.")

	dong = frappe.db.get_all(
		"Purchase Invoice Item",
		filters={"docstatus": ["<", 2], "item_code": ["is", "set"]},
		fields=["parent", "item_code", "item_name", "uom", "conversion_factor",
			"stock_uom", "description", "qty"],
		order_by="creation desc",
		limit_page_length=flt(gioi_han) * 12 or 4800,
	)

	gom = {}
	for d in dong:
		dvt_ncc = dvt_mua.dvt_tren_hoa_don(d.get("description"))
		if not dvt_mua.don_vi_chua_khai(dvt_ncc, d.get("uom"), d.get("conversion_factor")):
			continue
		khoa = (d["item_code"], dvt_ncc)
		o = gom.setdefault(khoa, {
			"item_code": d["item_code"],
			"item_name": d.get("item_name") or d["item_code"],
			"dvt_ncc": dvt_ncc,
			"dvt_kho": d.get("stock_uom") or "",
			"goi_y": dvt_mua.goi_y_don_vi(dvt_ncc),
			"so_dong": 0,
			"vi_du_to": [],
		})
		o["so_dong"] += 1
		if len(o["vi_du_to"]) < 3 and d["parent"] not in o["vi_du_to"]:
			o["vi_du_to"].append(d["parent"])

	ra = sorted(gom.values(), key=lambda x: (-x["so_dong"], x["item_name"]))
	return {
		"dong": ra[: int(flt(gioi_han) or 400)],
		"so_cap": len(ra),
		"so_dong": sum(x["so_dong"] for x in ra),
		"da_co_goi_y": len([x for x in ra if x["goi_y"]]),
	}
