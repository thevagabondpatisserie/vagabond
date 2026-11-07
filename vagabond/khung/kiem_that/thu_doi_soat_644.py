"""v644 bench: Đọc lại thư gốc một nguồn ShopeeFood (tệp không in dòng tổng)
trên ERPNext thật.

Site thật 07/11/2026: nguồn DSN-2611-06355 bấm Đọc lại thư gốc hỏng
"Column 'tong_tep' cannot be null". Khung chỉ soi được dict db_set nhận; ở đây
chứng minh trên MariaDB thật (cột số NOT NULL): nhận thư account@ có tệp
ShopeeFood, đưa nguồn về Cần xử lý như trên site, bấm Đọc lại thư gốc đúng
cửa doc_lai_thu thì đọc lại xong, tổng trên tệp ghi 0.
"""
from unittest.mock import patch

import frappe

from vagabond import doi_soat_thu as dst
from vagabond import doi_soat_vendor as dv
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen
from vagabond.khung.kiem_that.thu_doi_soat_643 import _thu_account


@ca("v644 bench: Đọc lại thư gốc nguồn ShopeeFood không in dòng tổng chạy được trên cơ sở dữ liệu thật")
def _():
	cty, _tk, _mau = _nen()
	with patch.object(dv, "_cong_ty", return_value=cty):
		ten = dst._xu_ly(_thu_account(), "644", dst.cau_hinh())
	_DA_TAO.append((dst.DT_THU, ten))
	la("thư account@ nhận", frappe.db.get_value(dst.DT_THU, ten, "ket_qua"), dst.KQ_XAC_THUC)
	ng = frappe.get_all(dst.DT_NGUON, filters={"thu": ten}, pluck="name")
	for x in ng:
		_DA_TAO.append((dst.DT_NGUON, x))
	la("một nguồn", len(ng), 1)
	# Như DSN-2611-06355 trên site: nguồn đọc bằng mẫu cũ còn Cần xử lý.
	frappe.db.set_value(dst.DT_NGUON, ng[0], "trang_thai", "Cần xử lý", update_modified=False)
	with patch.object(dv, "_cong_ty", return_value=cty):
		r = dst.doc_lai_thu(ten)
	la("đọc lại xong, thư giữ Đã xác thực", r.ket_qua, dst.KQ_XAC_THUC)
	n = frappe.db.get_value(dst.DT_NGUON, ng[0], ["trang_thai", "so_dong", "tong_tep", "du_lieu"], as_dict=True)
	la("nguồn đọc lại về Đã nhận, đủ hai đơn, tổng trên tệp 0", (n.trang_thai, int(n.so_dong), float(n.tong_tep)),
		("Đã nhận", 2, 0.0))
	dung("ghi lịch sử lần đọc trước", "lan_doc_truoc" in (n.du_lieu or ""))
	la("không ghi lỗi đọc lại", frappe.db.count("Error Log", {"method": "Đối soát hộp thư: đọc lại thư %s" % ten}), 0)
