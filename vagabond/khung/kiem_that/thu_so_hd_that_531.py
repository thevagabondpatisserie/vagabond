"""v531: ca TÍCH HỢP số hoá đơn thật và gieo nháp chính sách, sổ cái THẬT.

Ca Tân Hoà 27/09/2026: tờ mang số "APP.26.08.004" (mã hồ sơ) được nối làm hoá
đơn đến sau và đẩy hồ sơ lên hợp lệ tính thuế. Ở đây chạy thật trên site:
hook Hoá đơn mua chặn ghi mã hồ sơ vào số hoá đơn; nối tờ số giả vẫn lập bút
toán bù trừ thật mà hồ sơ giữ Không hợp lệ; gieo nháp chính sách đi được nhánh
tạo mới (lỗi thật lúc deploy v529). Mọi thứ lùi về điểm lưu (nen.py).
"""
import json

import frappe

from vagabond.khung.kiem_that.nen import ca, cau_loi, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _luu, _phieu
from vagabond.khung.kiem_that.thu_noi_hd_sau_530 import TIEN, _dung


@ca("v531 hook Hoá đơn mua thật: tạo tờ mang số APP... thì chặn; để trống số thì lưu được")
def _hook_that():
	hd = _phieu([("Nước thử v531", 1, TIEN)])
	hd.bill_no = "APP.26.09.998"
	try:
		_luu(hd)
		loi = ""
	except frappe.ValidationError as e:
		loi = cau_loi(e)
	dung("chặn, gọi đúng số", "APP.26.09.998" in loi)
	hd2 = _phieu([("Nước thử v531", 1, TIEN)])
	hd2.bill_no = ""
	x = khong_nem("tờ trống số lưu được", lambda: _luu(hd2))
	dung("đã lưu", bool(x and x.name))


@ca("v531 nối tờ đã ghi sổ mang số APP trên site thật: bút toán bù trừ thật, công nợ về 0, hồ sơ giữ Không hợp lệ")
def _noi_gia_that():
	from vagabond import ho_so_bo_sung as bo
	x = _dung()
	if not x:
		return
	hd, ho_so, _tk, _chi = x
	# Tờ cũ mang số là mã hồ sơ (dữ liệu có sẵn trước v531, đặt thẳng trong
	# điểm lưu: hook mới chặn đường lưu thường, đúng như mong đợi).
	frappe.db.set_value("Purchase Invoice", hd.name, "bill_no", "APP.26.09.997", update_modified=False)
	kq = khong_nem("nối", lambda: bo.noi_nhieu(ho_so, json.dumps([hd.name]))) or {}
	dung("có bút toán bù trừ", bool(kq.get("but_toan")))
	la("báo tờ không có số thật", kq.get("khong_hoa_don_that"), [hd.name])
	la("công nợ tờ về 0", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
	la("hồ sơ giữ Không hợp lệ", frappe.db.get_value("Vagabond Ho So TT", ho_so, "loai_cp_thue"), "Chi phi khong hop le")


@ca("v531 gieo nháp chính sách trên site thật khi chưa có bản ghi: tạo được, ba trang vào nháp còn ẩn, bản công khai không có chính sách")
def _gieo_that():
	from vagabond import noi_dung_web as w
	if frappe.db.exists(w.DOCTYPE, w.TEN):
		frappe.delete_doc(w.DOCTYPE, w.TEN, ignore_permissions=True, force=True)
	dung("chưa có bản ghi trước khi gieo", not frappe.db.exists(w.DOCTYPE, w.TEN))
	khong_nem("gieo", lambda: w.gieo_tu_tep())
	dung("đã có bản ghi", frappe.db.exists(w.DOCTYPE, w.TEN))
	if not frappe.db.exists(w.DOCTYPE, w.TEN):
		return
	d = frappe.get_doc(w.DOCTYPE, w.TEN)
	cs = (json.loads(d.ban_nhap or "{}").get("chinh_sach") or {})
	la("đủ ba trang trong nháp", sorted(cs), sorted(w.CHINH_SACH))
	la("còn ẩn", sorted({bool(v.get("hien")) for v in cs.values()}), [False])
	la("bản công khai không có chính sách", json.loads(d.ban_cong_khai or "{}").get("chinh_sach") or {}, {})
