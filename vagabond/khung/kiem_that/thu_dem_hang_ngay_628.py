"""v628 Codex #527 vòng 5: phiếu Đếm hôm nay không khoá nhập xuất nên ghi sổ phải
đúng mốc bếp chốt đếm. Chạy thật trên ERPNext.

Chuỗi của khách: kho có 10, bếp lập phiếu đếm hằng ngày, đếm 10 rồi chốt; sau đó
bếp xuất 3 cho sản xuất; quản lý duyệt ghi sổ muộn hơn. Tồn cuối phải là 7, không
phải 10. Ca không gọi thêm hàm nào ngoài chuỗi đó, chỉ chạy hàng đợi đăng lại giá
trị tồn mà ERPNext tự tạo cho chứng từ ghi lùi giờ (trên site, việc này chạy nền).
"""
import time

import frappe
from frappe.utils import flt, get_datetime, nowdate, nowtime

from vagabond import kiem_ke
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.gia_von_kiem_ke_547 import _kho
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.tat_lo_545 import _phieu, _ton
from vagabond.khung.kiem_that.thu_kho_dich_512 import _mon


def _ton_so(ma, kho):
	r = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
		where item_code=%s and warehouse=%s and is_cancelled=0
		order by posting_date desc, posting_time desc, creation desc limit 1""", (ma, kho))
	return flt(r[0][0]) if r else 0.0


def _chay_hang_doi_dang_lai():
	from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost
	for ten in frappe.get_all("Repost Item Valuation", filters={"docstatus": 1, "status": ["in", ["Queued", "In Progress"]]},
			pluck="name"):
		repost(frappe.get_doc("Repost Item Valuation", ten))


@ca("v628 Codex #527 vòng 5 thật: đếm hằng ngày 10, chốt, xuất 3, quản lý ghi sổ sau đó thì tồn còn 7")
def _ghi_dung_moc():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT628D")
	if not khong_nem("nhập 10", lambda: _phieu(cty, kho, ma, 10, "Material Receipt", 400)):
		return
	time.sleep(1.2)
	doc = frappe.get_doc({"doctype": "Phieu Kiem Ke", "kho": kho, "ngay_kiem": nowdate(), "pham_vi": "Tất cả",
		"trang_thai": "Đang kiểm", "ghi_chu": kiem_ke.GHI_CHU_LICH % nowdate(),
		"items": [{"item_code": ma, "item_name": ma, "dvt": "Gram", "so_luong": 10, "da_dem": 1}]})
	doc.insert()
	nen._DA_TAO.append(("Phieu Kiem Ke", doc.name))
	doc.trang_thai = "Chờ duyệt"
	doc.save()
	doc.reload()
	moc = kiem_ke.moc_dem(doc)
	dung("chốt phiếu hằng ngày có mốc chụp tồn", bool(moc))
	la("tồn sổ chụp lúc chốt", flt(doc.items[0].ton_he_thong), 10)
	time.sleep(1.2)
	if not khong_nem("xuất 3 sau khi chốt (phiếu hằng ngày không khoá)", lambda: _phieu(cty, kho, ma, 3, "Material Issue")):
		return
	la("trước ghi sổ còn 7", _ton(ma, kho), 7)
	vao = {"purpose": "Stock Reconciliation", "posting_time": nowtime(),
		"expense_account": frappe.db.get_value("Company", cty, "stock_adjustment_account"),
		"cost_center": frappe.db.get_value("Company", cty, "cost_center"),
		"items": [{"item_code": ma, "qty": 10, "valuation_rate": 400}]}
	kq = khong_nem("quản lý ghi sổ", lambda: kiem_ke.ghi_so(doc.name, vao))
	if not kq:
		return
	if kq.get("name"):
		nen._DA_TAO.append(("Stock Reconciliation", kq["name"]))
		sr = frappe.get_doc("Stock Reconciliation", kq["name"])
		la("phiếu điều chỉnh đặt đúng mốc chốt", (str(sr.posting_date), str(get_datetime("%s %s" % (sr.posting_date, sr.posting_time)).time())[:8]),
			(moc[0], moc[1]))
	khong_nem("chạy hàng đợi đăng lại giá trị tồn", _chay_hang_doi_dang_lai)
	la("tồn cuối theo sổ kho giữ khoản xuất 3", _ton_so(ma, kho), 7)
	la("tồn cuối trong Bin", _ton(ma, kho), 7)
