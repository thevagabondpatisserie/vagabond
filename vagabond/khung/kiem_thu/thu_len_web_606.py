"""v606 (Minh Vũ báo 20/10/2026, anh Việt giao sửa trong PR #492): trang đặt bánh

1. vẫn hiện Kankin ở tab Đặt bánh trước dù đã tắt: nút "Tắt bán web" của màn
   Kiểm bánh chỉ lọc tab bánh có sẵn hôm nay, tab Đặt bánh trước (đọc ô Đủ
   decor) không xét nút đó;
2. hiện "Tira-Missing-U 3.0 từ 0 đ" kèm ảnh nền bánh sừng bò: bếp khai Đủ decor
   cho mã phụ BAWC00080L20CM, mã này không có giá và không có ảnh.

Sửa bằng MỘT luật duoc_len_web cho cả hai tab. Các ca chạy hàm THẬT
(co_the_ban_hom_nay, _dat_truoc_theo_decor), chỉ thay tầng Frappe bằng bản giả.
"""
import datetime
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kiem_banh as kb

NGAY = datetime.date(2026, 10, 20)
ITEM = {
	"BAWC00124": {"item_code": "BAWC00124", "item_name": "Bánh Ổ Kankin, size 18cm", "image": "/files/k.jpg", "standard_rate": 1090000, "disabled": 0, "is_sales_item": 1},
	"BAWC00080L20CM": {"item_code": "BAWC00080L20CM", "item_name": "Bánh Ổ Tira-Missing-U 3.0, size 20cm", "image": None, "standard_rate": 0, "disabled": 0, "is_sales_item": 1},
	"BAWC00089": {"item_code": "BAWC00089", "item_name": "Bánh Ổ Very Berry, size 20cm", "image": "/files/v.png", "standard_rate": 1300000, "disabled": 0, "is_sales_item": 1},
	"BAWC00099": {"item_code": "BAWC00099", "item_name": "Bánh Ổ Cũ, size 16cm", "image": "/files/c.png", "standard_rate": 800000, "disabled": 1, "is_sales_item": 1},
}
TAT = {"BAWC00124": datetime.date(2026, 10, 20)}


def _dong(**k):
	return types.SimpleNamespace(**k)


def _get_all(dt, filters=None, fields=None, **kw):
	ma = (filters or {}).get("item_code", ["in", []])[1]
	ra = []
	for m in ma:
		x = ITEM.get(m)
		if not x:
			continue
		r = dict(x)
		r["custom_tat_ban_web_den"] = TAT.get(m)
		ra.append({k: r.get(k) for k in (fields or r)})
	return ra


def _chay(ham, kiem_hom_nay=None, decor=None):
	f = kb.frappe
	kho = types.SimpleNamespace(dong=decor or [], cap_nhat_luc="2026-10-20 08:00")
	ngay_kb = "KB-%s" % NGAY

	def exists(dt, ten):
		return kiem_hom_nay is not None and ten == ngay_kb

	def get_doc(dt, ten):
		return types.SimpleNamespace(dong=kiem_hom_nay or [])
	with patch.object(f, "get_all", _get_all, create=True), \
			patch.object(kb.tat_ban_web.frappe, "get_all", _get_all, create=True), \
			patch.object(f, "get_single", lambda dt: kho, create=True), \
			patch.object(f.db, "exists", exists, create=True), \
			patch.object(f, "get_doc", get_doc, create=True), \
			patch.object(kb, "getdate", lambda *a: NGAY), \
			patch.object(kb.tat_ban_web, "getdate", lambda *a: NGAY), \
			patch.object(kb, "cfg", lambda: types.SimpleNamespace(pancake_shop_id=None)), \
			patch.object(kb, "key", lambda c, k: ""):
		return ham()


@ca("v606 lên web: luật duoc_len_web (có Item, không ngừng dùng, là hàng bán, giá > 0, không tắt bán web)")
def _luat():
	la("bình thường", kb.duoc_len_web(ITEM["BAWC00089"]), True)
	la("không có Item", kb.duoc_len_web(None), False)
	la("giá 0", kb.duoc_len_web(ITEM["BAWC00080L20CM"]), False)
	la("giá hỏng", kb.duoc_len_web(dict(ITEM["BAWC00089"], standard_rate="x")), False)
	la("ngừng dùng", kb.duoc_len_web(ITEM["BAWC00099"]), False)
	la("không phải hàng bán", kb.duoc_len_web(dict(ITEM["BAWC00089"], is_sales_item=0)), False)
	la("thiếu cờ hàng bán thì coi là bán", kb.duoc_len_web({k: v for k, v in ITEM["BAWC00089"].items() if k != "is_sales_item"}), True)
	la("đang tắt bán web", kb.duoc_len_web(ITEM["BAWC00124"], {"BAWC00124": {"tat": 1}}), False)
	la("tắt mã khác không ảnh hưởng", kb.duoc_len_web(ITEM["BAWC00089"], {"BAWC00124": {"tat": 1}}), True)


DECOR = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", so_decor=1, hinh=""),
	_dong(ma_hang="BAWC00124", ten_banh="Kankin", so_decor=1, hinh=""),
	_dong(ma_hang="BAWC00080L20CM", ten_banh="Tira", so_decor=1, hinh=""),
	_dong(ma_hang="BAWC00099", ten_banh="Cũ", so_decor=2, hinh="")]


@ca("v606 tái hiện Minh Vũ: tab Đặt bánh trước không hiện Kankin đang tắt bán web, Tira mã phụ giá 0, mã ngừng dùng")
def _dat_truoc():
	# Trước bản sửa (98cfa887a, site thật 20/10): tab này trả Kankin BAWC00124 và
	# "Tira-Missing-U 3.0" BAWC00080L20CM giá 0 kèm ảnh nền.
	kq = _chay(kb._dat_truoc_theo_decor, decor=DECOR)
	la("chỉ còn Very Berry", [(g["ten"], [s["ma"] for s in g["sizes"]]) for g in kq["nhom"]], [("Very Berry", ["BAWC00089"])])
	dung("không size nào giá 0", all(s["gia"] > 0 for g in kq["nhom"] for s in g["sizes"]))
	TAT.pop("BAWC00124")
	try:
		kq = _chay(kb._dat_truoc_theo_decor, decor=DECOR)
	finally:
		TAT["BAWC00124"] = NGAY
	la("bật bán lại thì Kankin hiện lại", sorted(g["ten"] for g in kq["nhom"]), ["Kankin", "Very Berry"])


@ca("v606: tab bánh có sẵn hôm nay dùng CÙNG luật: mã giá 0 và mã ngừng dùng không hiện, mã thường vẫn hiện")
def _hom_nay():
	dong = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=2, hinh=""),
		_dong(ma_hang="BAWC00080L20CM", ten_banh="Tira", co_the_ban=1, hinh=""),
		_dong(ma_hang="BAWC00099", ten_banh="Cũ", co_the_ban=1, hinh=""),
		_dong(ma_hang="BAWC00124", ten_banh="Kankin", co_the_ban=1, hinh="")]
	kq = _chay(kb.co_the_ban_hom_nay, kiem_hom_nay=dong, decor=[])
	la("mã lên web", [m["ma"] for m in kq["mon"]], ["BAWC00089"])
	la("bảng số chỉ còn mã được bán", kq["banh"], {"BAWC00089": 2})
