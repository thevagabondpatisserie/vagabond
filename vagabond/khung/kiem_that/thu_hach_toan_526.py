"""v526: ca TÍCH HỢP cho ghi sổ thẳng có hạch toán và hoá đơn đến sau.

Tầng khung đã chốt phần quyết định bằng dữ liệu giả. Câu chỉ tầng này trả
lời được: ERPNext THẬT (cả chuỗi hook validate/before_submit của repo) có
ghi sổ đúng tài khoản người chọn không, sổ cái Nợ đúng tài khoản đó thay vì
632; tờ đã nối làm hoá đơn đến sau có bị chặn ghi sổ không, màn Đối chiếu có
xếp nó đúng chỗ không; và patch quyền Repost có dựng được dòng quyền không.

Ca thật: hoá đơn xăng Xăng dầu Khu vực II. Mọi thứ lùi về điểm lưu, xem nen.py.
"""
import json

import frappe

from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _luu, _phieu


def _tk_chi_phi_khac():
	"""Một tài khoản chi phí chi tiết KHÁC mặc định công ty (632), vai 6417."""
	cty = nen.cong_ty()
	mac_dinh = frappe.get_cached_value("Company", cty, "default_expense_account")
	return frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0,
		"root_type": "Expense", "account_type": ["in", ["", None]], "name": ["!=", mac_dinh]}, "name")


@ca("#526 ca xăng: ghi sổ thẳng với tài khoản chọn từng dòng, sổ cái Nợ đúng tài khoản đó")
def _ghi_xang():
	from vagabond import doi_chieu_mua, hach_toan_thang
	tk = _tk_chi_phi_khac()
	dung("có tài khoản chi phí để chọn", bool(tk))
	if not tk:
		return
	hd = khong_nem("dựng tờ xăng", lambda: _luu(_phieu([("Xăng E10 RON 95", 1, 80000)])))
	if not hd:
		return
	xem = khong_nem("mở màn hạch toán", lambda: hach_toan_thang.xem(hd.name)) or {}
	dong = xem.get("dong") or []
	dung("có dòng chi phí đổi được", any(d.get("sua_duoc") for d in dong))
	chon = {d["ten"]: tk for d in dong if d.get("sua_duoc")}
	kq = khong_nem("ghi sổ thẳng", lambda: doi_chieu_mua.ghi_so_thang(hd.name, json.dumps(chon))) or {}
	la("đã ghi sổ", kq.get("da_ghi_so"), 1)
	hd.reload()
	la("dòng đi đúng tài khoản chọn", [d.expense_account for d in hd.items], [tk] * len(hd.items))
	gl = nen.so_cai_cua(hd)
	la("Nợ đúng tài khoản chọn", sum(d.debit - d.credit for d in gl if d.account == tk), 80000)
	mac_dinh = frappe.get_cached_value("Company", hd.company, "default_expense_account")
	la("không Nợ mặc định 632", sum(d.debit for d in gl if d.account == mac_dinh), 0)


@ca("#526 ghi sổ thẳng không gửi tài khoản thì dừng, tờ vẫn nháp")
def _ghi_khong_tk():
	from vagabond import doi_chieu_mua
	hd = khong_nem("dựng tờ", lambda: _luu(_phieu([("Phí dịch vụ", 1, 30000)])))
	if not hd:
		return
	try:
		doi_chieu_mua.ghi_so_thang(hd.name)
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo chưa chọn tài khoản", "Chưa chọn tài khoản" in loi)
	la("tờ vẫn nháp", frappe.db.get_value("Purchase Invoice", hd.name, "docstatus"), 0)


def _ho_so_cho(hd, trang_thai="Da thanh toan"):
	"""Hồ sơ chi từ TK công ty có một khoản đã nối tờ `hd` làm hoá đơn đến sau.
	Dựng thẳng bảng (db_insert) vì chỉ cần dấu nối, không cần cả luồng duyệt."""
	p = frappe.new_doc("Vagabond Ho So TT")
	p.name = "KT526-" + frappe.generate_hash(length=8)
	p.loai = "TK cong ty"
	p.trang_thai = trang_thai
	p.nha_cung_cap = hd.supplier
	p.loai_cp_thue = "Chi phi hop le"
	p.db_insert()
	d = frappe.new_doc("Vagabond Ho So TT Dong")
	d.parent, d.parenttype, d.parentfield, d.idx = p.name, "Vagabond Ho So TT", "dong", 1
	d.noi_dung, d.so_tien, d.cho_hoa_don, d.hoa_don_bo_sung = "Xăng", 80000, 1, hd.name
	d.db_insert()
	return p.name


@ca("#526 tờ đã nối làm hoá đơn đến sau: chặn ghi sổ mọi đường, màn Đối chiếu xếp vào Xong")
def _chan_ghi():
	from vagabond import doi_chieu_mua
	hd = khong_nem("dựng tờ", lambda: _luu(_phieu([("Xăng E10 RON 95", 1, 80000)])))
	if not hd:
		return
	ho_so = _ho_so_cho(hd)
	try:
		hd.submit()
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("chặn ghi sổ, gọi tên hồ sơ", ho_so in loi and "không ghi sổ" in loi)
	la("tờ vẫn nháp", frappe.db.get_value("Purchase Invoice", hd.name, "docstatus"), 0)
	xem = khong_nem("mở màn đối chiếu", lambda: doi_chieu_mua.xem(hd.name)) or {}
	la("màn biết tờ là chứng từ của hồ sơ", xem.get("ho_so_chi"), ho_so)
	ds = khong_nem("danh sách", lambda: doi_chieu_mua.danh_sach(so_ngay=5, tu_khoa=hd.name)) or {}
	dong = [o for o in ds.get("hd") or [] if o.get("name") == hd.name]
	la("xếp vào Xong kèm tên hồ sơ", [(o.get("nhom"), o.get("ho_so_chi")) for o in dong], [("xong", ho_so)])


@ca("#526 v2 tờ đang là hoá đơn đến sau của hồ sơ thì không đánh dấu huỷ được, dấu huỷ vẫn 0")
def _khong_huy_to_da_noi():
	from vagabond.chung_tu import danh_dau_huy
	hd = khong_nem("dựng tờ", lambda: _luu(_phieu([("Xăng E10 RON 95", 1, 80000)])))
	if not hd:
		return
	ho_so = _ho_so_cho(hd)
	try:
		danh_dau_huy(hd, "Ca thử 526")
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("chặn, gọi tên hồ sơ", ho_so in loi)
	la("dấu huỷ vẫn 0", int(frappe.db.get_value("Purchase Invoice", hd.name, "vgb_huy") or 0), 0)


@ca("#526 hồ sơ đã huỷ thì dấu nối hết hiệu lực, tờ hoá đơn ghi sổ lại bình thường")
def _ho_so_huy():
	hd = khong_nem("dựng tờ", lambda: _luu(_phieu([("Xăng E10 RON 95", 1, 80000)])))
	if not hd:
		return
	_ho_so_cho(hd, trang_thai="Huy")
	khong_nem("ghi sổ tờ của hồ sơ đã huỷ", hd.submit)
	la("đã ghi sổ", frappe.db.get_value("Purchase Invoice", hd.name, "docstatus"), 1)


@ca("#526 patch quyền Repost dựng đủ bốn quyền cho kế toán FIN, giữ dòng System Manager")
def _quyen():
	from vagabond import quyen_ap
	if not frappe.db.exists("Role", "AP Kiểm soát (FIN)"):
		frappe.get_doc({"doctype": "Role", "role_name": "AP Kiểm soát (FIN)"}).insert(ignore_permissions=True)
	khong_nem("patch cấp quyền", quyen_ap.cap_repost_v526)
	ten = frappe.db.get_value("Custom DocPerm", {"parent": "Repost Accounting Ledger",
		"role": "AP Kiểm soát (FIN)", "permlevel": 0, "if_owner": 0})
	dung("có dòng quyền FIN", bool(ten))
	if ten:
		la("đủ bốn quyền", [frappe.db.get_value("Custom DocPerm", ten, q) for q in ("read", "write", "create", "submit")], [1, 1, 1, 1])
	dung("giữ dòng System Manager", bool(frappe.db.exists("Custom DocPerm",
		{"parent": "Repost Accounting Ledger", "role": "System Manager"})))
	la("chạy lần hai không thêm gì", (quyen_ap.cap_repost_v526() or {}).get("them"), [])
