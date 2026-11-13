"""v654: gieo một dòng lịch chi hằng tháng cho tiền nhà Nguyễn Hữu Phước, ngày 20.

Dữ liệu thật 13/11/2026: APP loại Chi từ tài khoản công ty lập 20/08, 21/09,
19/10 (79.000.000 rồi 86.900.000). Anh Việt: mặc định ngày 20, sửa được.
Chỉ gieo khi có nhà cung cấp đó và chưa có lịch nào cho họ; số tiền lấy APP
gần nhất. Chạy lại không đổi gì. Không đụng chứng từ nào."""

NCC = "Nguyễn Hữu Phước"
NGAY = 20


def dong_gieo(ncc_co, da_co_lich, app_gan_nhat, so_thang):
	"""THUẦN: dict dòng cần gieo hoặc None."""
	if not ncc_co or da_co_lich:
		return None
	return {"noi_dung": "Tiền nhà", "nguoi_nhan": NCC, "nha_cung_cap": NCC, "ngay_trong_thang": NGAY, "bat": 1,
		"so_tien": float(app_gan_nhat or 0), "so_thang_thay": int(so_thang or 0)}


def execute():
	import frappe

	if not frappe.db.table_exists("Vagabond Lich Chi"):
		return
	ncc = frappe.db.exists("Supplier", NCC)
	co = frappe.db.exists("Vagabond Lich Chi", {"nha_cung_cap": NCC}) or frappe.db.exists("Vagabond Lich Chi", {"nguoi_nhan": NCC})
	app = frappe.get_all("Vagabond Ho So TT", filters={"nha_cung_cap": NCC, "trang_thai": "Da thanh toan"},
		fields=["ngay", "tong_tien"], order_by="ngay desc", limit_page_length=0) if ncc else []
	thang = {str(a.ngay)[:7] for a in app}
	d = dong_gieo(ncc, co, app[0].tong_tien if app else 0, len(thang))
	if not d:
		return
	doc = frappe.get_doc(dict(d, doctype="Vagabond Lich Chi"))
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.insert(ignore_permissions=True)
