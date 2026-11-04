"""v638: hoa hồng giới thiệu chạy trên ERPNext thật.

Dựng một nhân viên thử có số điện thoại, một hoá đơn tại bàn đi đúng cửa app
(tao_don_tay) có món bánh và dòng phí giao, gắn người giới thiệu bằng đúng
hàm đơn gọi món tại bàn gọi (gioi_thieu.gan_cho_hoa_don), rồi GHI SỔ thật:
hook on_submit phải ghi đúng hoa hồng (tiền bánh x %, không gồm phí giao) vào
Custom Field có cột thật. Đổi % trong Cài đặt sau đó không đổi đơn đã gắn.
Tờ trả hàng ghi sổ đưa hoa hồng tờ gốc về 0, huỷ tờ trả hàng thì tính lại,
huỷ tờ gốc thì về 0. Mọi thứ nằm trong điểm lưu của nen.py: không commit,
không gửi ra ngoài, không đụng hoá đơn điện tử.
"""
import frappe
from frappe.utils import flt

from vagabond import ban_hang
from vagabond import gioi_thieu as gt
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _app, _mon, _nen


def _nhan_vien():
	so = "0987" + "".join(ch for ch in frappe.generate_hash(length=24) if ch.isdigit())[:6].ljust(6, "7")
	u = frappe.get_doc({"doctype": "User", "email": "kt638-gt-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Giới Thiệu", "last_name": "Ngân", "enabled": 1, "send_welcome_email": 0,
		"mobile_no": so, "roles": [{"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u, so


@ca("v638 hoá đơn tại bàn có người giới thiệu: ghi sổ thật ra đúng hoa hồng (bỏ phí giao, % chốt lúc gắn); trả hàng về 0, huỷ trả hàng tính lại, huỷ hoá đơn về 0")
def _vong_doi():
	cty, tk, _mau = _nen()
	dung("đủ cột hoá đơn", all(frappe.db.has_column("Sales Invoice", o) for o in (gt.O_NGUOI, gt.O_PT, gt.O_HH)))
	frappe.db.set_single_value("Vagabond Settings", gt.O_BAT, 1)
	frappe.db.set_single_value("Vagabond Settings", gt.O_PT_TAI_BAN, 2)
	u, so = _nhan_vien()
	la("cửa kiem thấy tên gọi", gt.kiem("+84 " + so[1:]), {"ok": 1, "ten": "Ngân"})
	mon = _mon(tk)
	si = _app(cty, [dict(item_code=mon, qty=1, rate=500000), dict(item_code=ban_hang._item_phi_giao(), qty=1, rate=30000)])
	kq = gt.gan_cho_hoa_don(si, so, "tai_ban")
	la("gắn người giới thiệu", (kq.get("ok"), kq.get("nguoi")), (1, u.name))
	# Đổi % SAU khi gắn: đơn này vẫn giữ 2%.
	frappe.db.set_single_value("Vagabond Settings", gt.O_PT_TAI_BAN, 9)
	si.reload()
	la("ô trên hoá đơn", (si.get(gt.O_NGUOI), si.get(gt.O_LOAI), flt(si.get(gt.O_PT))), (u.name, "tai_ban", 2.0))
	# Thu ngân cố đổi người giới thiệu khi lưu: máy trả lại.
	si.set(gt.O_NGUOI, "Administrator")
	si.vgb_tam_tinh = 0
	si.vgb_pt_thanh_toan = "GrabFood"
	si.vgb_ma_tham_chieu = "KT638GT-" + frappe.generate_hash(length=8)
	khong_nem("lưu hoá đơn", lambda: si.save(ignore_permissions=True))
	si.reload()
	la("thu ngân không đổi được", si.get(gt.O_NGUOI), u.name)
	if not khong_nem("ghi sổ hoá đơn", lambda: si.submit()):
		return
	si.reload()
	la("ghi sổ: 2% của 500.000 (phí giao 30.000 không tính)", flt(si.get(gt.O_HH)), 10000.0)

	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
	tra = make_sales_return(si.name)
	for k in ("custom_hddt_so", "custom_hddt_id", "custom_minvoice_id", "custom_hddt_trang_thai", "vgb_hddt_cho_doi_chieu"):
		if tra.meta.has_field(k):
			tra.set(k, None)
	tra.vgb_ma_tham_chieu = "KT638GT-TRA-" + frappe.generate_hash(length=8)
	la("tờ trả hàng không chép người giới thiệu", tra.get(gt.O_NGUOI) or "", "")
	if not khong_nem("lập tờ trả hàng", lambda: tra.insert(ignore_permissions=True)):
		return
	_DA_TAO.append((tra.doctype, tra.name))
	if not khong_nem("ghi sổ tờ trả hàng", lambda: tra.submit()):
		return
	la("trả hàng: tờ gốc về 0", flt(frappe.db.get_value("Sales Invoice", si.name, gt.O_HH)), 0.0)
	tra.reload()
	khong_nem("huỷ tờ trả hàng", lambda: tra.cancel())
	la("huỷ trả hàng: tính lại", flt(frappe.db.get_value("Sales Invoice", si.name, gt.O_HH)), 10000.0)
	si.reload()
	khong_nem("huỷ hoá đơn", lambda: si.cancel())
	la("huỷ hoá đơn: về 0", flt(frappe.db.get_value("Sales Invoice", si.name, gt.O_HH)), 0.0)
