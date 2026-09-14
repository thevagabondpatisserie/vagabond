"""#307: nạp một lần tài khoản tồn kho BTP theo ô Chặng đã khai. Idempotent.

Không sửa món chưa khai chặng, không đụng chứng từ, không bật cờ
Company.enable_item_wise_inventory_account (kế toán bật tay ngày cắt).

Dừng migrate rõ ràng nếu Item Default không có ô TRUONG_ITEM_DEFAULT: đó
là dấu hằng số chưa khớp lõi, không được để lên site mà im lặng.
"""
import frappe
from vagabond import tai_khoan_btp as tkb
from vagabond.kho_san_xuat import TIEN_TO_BTP


def _dat_mac_dinh():
	"""Hai ô trống thì trỏ 1552 nếu site có đúng một tài khoản con 1552 còn dùng."""
	cau_hinh = tkb.doc_cau_hinh()
	if all(cau_hinh.values()):
		return cau_hinh
	cac_tk = frappe.get_all("Account", filters={"account_number": ["like", tkb.SO_HIEU_BTP + "%"],
		"account_type": "Stock", "company": tkb.cong_ty_ap_dung(cau_hinh)}, fields=["name", "account_number", "is_group", "disabled"])
	mac_dinh = tkb.chon_mac_dinh(cac_tk)
	if not mac_dinh:
		return cau_hinh
	for o, v in cau_hinh.items():
		if not v:
			frappe.db.set_single_value("Vagabond Settings", o, mac_dinh)
			cau_hinh[o] = mac_dinh
	return cau_hinh


def execute():
	if not tkb.co_o_item_default():
		frappe.throw("Item Default không có ô %s. Đối chiếu lại lõi ERPNext trước khi "
			"phát hành #307." % tkb.TRUONG_ITEM_DEFAULT)
	cau_hinh = _dat_mac_dinh()
	if not all(cau_hinh.values()):
		print("tai_khoan_btp_307: ô cấu hình còn trống, chưa nạp; kế toán khai rồi lưu từng món.")
		return
	dieu_kien = [["custom_chang_btp", "!=", ""], ["is_stock_item", "=", 1]]
	dem = {tkb.GHI: 0, tkb.GIU: 0, tkb.XOA: 0, tkb.BO_QUA: 0, "loi": 0}
	for t in TIEN_TO_BTP:
		for ten in frappe.get_all("Item", filters=dieu_kien + [["item_code", "like", t + "%"]],
				pluck="name"):
			try:
				kq = tkb.ap_dung(frappe.get_doc("Item", ten), cau_hinh, ghi_db=True)
				dem[kq["hanh_dong"]] = dem.get(kq["hanh_dong"], 0) + 1
			except Exception:
				dem["loi"] += 1
				frappe.log_error(frappe.get_traceback(), "tai_khoan_btp_307 %s" % ten)
	frappe.clear_cache(doctype="Item")
	print("tai_khoan_btp_307: %s" % dem)
