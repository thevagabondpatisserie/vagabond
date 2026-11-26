"""v693 bench: tab In season cho Panettone và Bûche trên ERPNext thật.

Tầng khung đã kiểm các phép thuần. Ở đây chứng minh trên site dựng thật: doctype
Mùa vụ nhận các ô mới sau migrate (bảng con Sốt, ba ô của dòng, bốn ô lịch); lưu
Mùa vụ có ô lịch ghi sai bị chặn; lưu hợp lệ thì tạo đúng một thẻ nội dung cho
mỗi nhóm và không tạo trùng; hang_theo_mua trả nhóm đã gộp size kèm sốt, luật và
nội dung; phép kiểm lúc tạo đơn từ chối ngày sai.

Dữ liệu trong ca là GIẢ (mã, tên, giá). Ca KHÔNG đọc mùa thật của site: hàm chọn
mùa cho web được thay bằng bản ghi của ca, và có phép kiểm chứng minh danh sách
mùa đang bán của site không đổi.
"""
import datetime
from unittest.mock import patch

import frappe

from vagabond import banh_web as bw
from vagabond import mua_vu as mv
from vagabond import mua_vu_web as mw
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la

TEN_MUA = "Mua Kiem Thu Web 693"


def _mon(ma, ten, gia):
	from vagabond.khung.kiem_that import nen

	d = frappe.get_doc({"doctype": "Item", "item_code": ma, "item_name": ten,
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_sales_item": 1, "standard_rate": gia})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


def _ma_thu():
	return (_mon("BASS-KIEM-693-P1", "Panettone Thử 693, 680gr", 780000), _mon("BASS-KIEM-693-P2", "Panettone Thử 693 Mini, 250gr", 320000),
		_mon("BASS-KIEM-693-B1", "Bûche Thử 693", 990000), _mon("BASS-KIEM-693-S1", "Sốt Thử 693", 45000))


def _mua(ma=None, **them):
	hn = frappe.utils.getdate(frappe.utils.nowdate())
	p1, p2, b1, s1 = ma or _ma_thu()
	doc = frappe.get_doc(dict({"doctype": mv.DT, "ten_mua": TEN_MUA, "tinh_trang": "Dang ban",
		"tu_ngay": hn, "den_ngay": frappe.utils.add_days(hn, 30),
		"dong": [
			{"ma_hang": p1, "ten_banh": "Panettone Thử 693", "sx_dau_mua": 9, "nhom_web": "Panettone Thử 693", "nhan_size": "Bánh lớn 680gr", "loai_web": "Panettone"},
			{"ma_hang": p2, "ten_banh": "Panettone Thử 693 Mini", "sx_dau_mua": 4, "nhom_web": "Panettone Thử 693", "nhan_size": "Bánh Mini 250gr", "loai_web": "Panettone"},
			{"ma_hang": b1, "ten_banh": "Bûche Thử 693", "sx_dau_mua": 3, "loai_web": "Bûche"}],
		"sot_web": [{"ma_hang": s1}]}, **them))
	return doc, (p1, p2, b1, s1)


@ca("v693 bench: Mùa vụ có đủ ô mới sau migrate; ô lịch ghi sai bị chặn lúc lưu; lưu hợp lệ tạo một thẻ nội dung mỗi nhóm, lưu lại không tạo trùng")
def _():
	m, md = frappe.get_meta(mv.DT), frappe.get_meta("Vagabond Mua Vu Dong")
	dung("ô của Mùa vụ", all(m.has_field(f) for f in ("sot_web", "panettone_thu", "panettone_truoc", "buche_thu", "buche_truoc")))
	dung("ô của dòng", all(md.has_field(f) for f in ("nhom_web", "nhan_size", "loai_web")))
	dung("thẻ Bánh có cờ mùa vụ", frappe.get_meta(bw.DT).has_field("mua_vu"))
	mua_that = sorted(mv.mua_dang_chay())
	truoc = frappe.db.count(bw.DT)
	ma = _ma_thu()
	sai, _ma = _mua(ma, panettone_thu="thứ hai")
	loi = ""
	try:
		sai.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		loi = str(e)
	dung("ô thứ ghi sai bị chặn, câu nói cách ghi đúng: " + loi[:80], "2,4,6" in loi)
	doc, (p1, p2, _b1, _s1) = _mua(ma, panettone_truoc="0", buche_thu="7,CN")
	doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	khoa_p, khoa_b = bw.khoa_banh("Panettone Thử 693"), bw.khoa_banh("Bûche Thử 693")
	for k in (khoa_p, khoa_b):
		_DA_TAO.append((bw.DT, k))
	la("hai nhóm, hai thẻ nội dung mới", frappe.db.count(bw.DT) - truoc, 2)
	bg = frappe.get_doc(bw.DT, khoa_p)
	la("thẻ mùa vụ: cờ, không chờ ảnh, đủ hai mã size", (int(bg.mua_vu), bg.trang_thai, bw.tach_dong(bg.ma_hang)), (1, bw.DA_AN, [p1, p2]))
	doc.reload()
	doc.save(ignore_permissions=True)
	la("lưu lại không tạo trùng", frappe.db.count(bw.DT) - truoc, 2)
	la("số 0 và ô đã điền được giữ đúng, ô trống là None hoặc rỗng", (doc.panettone_truoc, doc.buche_thu, doc.panettone_thu or "", doc.buche_truoc or ""), ("0", "7,CN", "", ""))
	la("mùa đang bán thật của site chỉ thêm mùa của ca", sorted(mv.mua_dang_chay()), sorted(mua_that + [doc.name]))


@ca("v693 bench: hang_theo_mua gộp size, kèm sốt theo giá hồ sơ món, luật theo ô cài đặt, nội dung thẻ Bánh; lúc tạo đơn ngày sai và quá 2 hũ sốt bị từ chối")
def _():
	doc, (p1, p2, b1, s1) = _mua(panettone_truoc="1", buche_thu="7,CN")
	doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	khoa_p = bw.khoa_banh("Panettone Thử 693")
	for k in (khoa_p, bw.khoa_banh("Bûche Thử 693")):
		_DA_TAO.append((bw.DT, k))
	frappe.db.set_value(bw.DT, khoa_p, {"mo_ta": "Mô tả thử 693.", "tang": "Men tự nhiên\nBơ", "di_ung": "Gluten", "bao_quan": ""})
	doc.reload()
	with patch.object(mv, "mua_cho_web", lambda: doc), patch.object(bw, "dang_dung", lambda: True):
		kq = mv.hang_theo_mua()
		la("có mùa của ca", (kq["co"], kq["ten_mua"]), (1, TEN_MUA))
		g = next(x for x in kq["nhom"] if x["ten"] == "Panettone Thử 693")
		la("một thẻ hai size, size lớn trước", [(s["ma"], s["nhan"], s["gia"]) for s in g["sizes"]], [(p1, "Bánh lớn 680gr", 780000), (p2, "Bánh Mini 250gr", 320000)])
		la("loại và nội dung của thẻ", (g["loai"], g["mo_ta"], g["tang"], g["di_ung"], g["bao_quan"]), ("panettone", "Mô tả thử 693.", ["Men tự nhiên", "Bơ"], "Gluten", ""))
		dung("Bûche đứng một thẻ, mang loại", any(x["loai"] == "buche" and len(x["sizes"]) == 1 and x["sizes"][0]["ma"] == b1 for x in kq["nhom"]))
		la("danh sách phẳng cũ còn nguyên ba mã cho trang đang mở", sorted(x["ma"] for x in kq["mon"]), sorted([p1, p2, b1]))
		la("sốt theo giá hồ sơ món", [(x["ma"], x["gia"]) for x in kq["sot"]], [(s1, 45000)])
		la("luật theo ô cài đặt", kq["luat"], {"panettone": {"truoc": 1, "thu": [2, 4, 6]}, "buche": {"truoc": 2, "thu": [7, 8]}})
		mua = mw.doc_mua_web()
		hn = frappe.utils.getdate(frappe.utils.nowdate())
		tot = next(hn + datetime.timedelta(days=i) for i in range(1, 9) if mw.thu_cua_ngay(hn + datetime.timedelta(days=i)) in (2, 4, 6))
		xau = next(hn + datetime.timedelta(days=i) for i in range(1, 9) if mw.thu_cua_ngay(hn + datetime.timedelta(days=i)) in (3, 5))
		h = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
		la("Panettone ngày đúng thứ: nhận", mw.kiem_don(h(**{p1: 1}), str(tot) + "T13:00:00", mua), None)
		la("Panettone ngày sai thứ: từ chối", (mw.kiem_don(h(**{p1: 1}), str(xau) + "T13:00:00", mua) or {}).get("ly_do"), "ngay_mua_vu")
		la("Panettone nhận hôm nay khi cài trước 1 ngày: từ chối", (mw.kiem_don(h(**{p2: 1}), str(hn), mua) or {}).get("ly_do"), "ngay_mua_vu")
		la("1 bánh 3 hũ sốt: từ chối", (mw.kiem_don(h(**{p1: 1, s1: 3}), str(tot), mua) or {}).get("ly_do"), "sot_qua_so")
		la("mã Panettone không tính dĩa nĩa", mw.ma_khong_dung_cu(), {p1, p2})
