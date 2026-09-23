"""Nhóm "CCDC dùng ngay": công cụ dụng cụ mua về dùng luôn, đi thẳng 242.

Vì sao có mô đun này (v524, anh Việt chốt 24/09/2026)
--------------------------------------------------------------------
Uyên mua quạt cho nhân viên (hoá đơn Điện Máy Xanh, Midea FS40-24EVN) và hỏi
có phải làm phiếu nhập kho, nối phiếu nhập kho không. Chị Dung: "CCDC chị hay
hạch toán vào 242 chứ không qua 153".

Trên site lúc đó cả 265 món nhóm Công cụ Dụng cụ đều là hàng quản kho, nhóm
mặc định tài khoản 153 và Kho tổng 307, nên mọi hoá đơn CCDC đều đòi phiếu
nhập kho. Không có loại món nào "mua về, không quản kho, vào 242".

Cách làm
--------
1. Một nhóm lá mới "CCDC dùng ngay" nằm THẲNG dưới "Mua vào", KHÔNG nằm dưới
   nhánh Công cụ Dụng cụ: lưới đỡ nhóm theo tồn (luoi_do_nhom.py) coi mọi
   nhóm con của nhánh CCDC là 153.
2. Món thuộc nhóm này luôn là món mua, không quản kho, và Item Default của
   từng công ty có tài khoản chi phí = tài khoản số 242 của công ty đó.
   Vì sao ghi trên TỪNG MÓN: hook tk_theo_mon (dung_lai_hddt.py) đọc Item
   Default của chính món, không đọc mặc định của nhóm.
3. Hàng không quản kho thì các cửa nối phiếu nhập kho đều bỏ qua dòng đó
   (doi_chieu_mua._khong_qua_kho, buoc_hoa_don_mua), nên không cần PNK.

KHÔNG làm ở đây
---------------
- Không chuyển các mã CCDC cũ (đã có tồn và lịch sử kho) sang nhóm mới. Món
  đã có sổ kho mà chuyển sang nhóm này thì chặn, mở mã mới.
- Không tự phân bổ 242 sang chi phí hàng tháng: kế toán vẫn làm bút toán
  phân bổ như đang làm.
"""

import frappe
from frappe.utils import cint

NHOM = "CCDC dùng ngay"
CHA = "Mua vào"
TIEN_TO = "CCDN"
SO_TK = "242"


# ------------------------------------------------------------ phần thuần

def dong_can_dat(hien_co, tk_theo_cty):
	"""Item Default cần sửa hoặc thêm để mọi công ty có 242 đều đi 242.

	hien_co: danh sách dict {company, expense_account} đang có trên món.
	tk_theo_cty: {công ty: tài khoản 242 của công ty đó}.
	Trả về danh sách (công ty, tài khoản, "sua" | "them"), theo tên công ty.
	"""
	co = {}
	for d in hien_co or []:
		cty = (d.get("company") or "").strip()
		if cty and cty not in co:
			co[cty] = (d.get("expense_account") or "").strip()
	ra = []
	for cty in sorted(tk_theo_cty or {}):
		tk = tk_theo_cty[cty]
		if not tk:
			continue
		if cty not in co:
			ra.append((cty, tk, "them"))
		elif co[cty] != tk:
			ra.append((cty, tk, "sua"))
	return ra


# ------------------------------------------------------------ phần chạm hệ

def tk_theo_cong_ty():
	ra = {}
	for cty in frappe.get_all("Company", pluck="name", limit_page_length=0):
		tk = frappe.db.get_value("Account", {"company": cty, "account_number": SO_TK,
			"is_group": 0, "disabled": 0}, "name")
		if tk:
			ra[cty] = tk
	return ra


def khi_luu_mon(doc, method=None):
	"""Hook validate Item: món nhóm CCDC dùng ngay luôn không quản kho, đi 242."""
	if (doc.get("item_group") or "").strip() != NHOM:
		return
	truoc = None if doc.is_new() else doc.get_doc_before_save()
	if truoc is not None and cint(truoc.get("is_stock_item")) and frappe.db.exists(
		"Stock Ledger Entry", {"item_code": doc.name, "is_cancelled": 0}
	):
		# Hook này chạy SAU phép chặn đổi cờ quản kho của ERPNext, nên phải tự
		# chặn: đặt về 0 ở đây là lách qua luật của lõi.
		frappe.throw(
			"Món %s đã có sổ kho nên không chuyển sang nhóm \"%s\" được. "
			"Mở một mã mới trong nhóm này cho lần mua sau." % (doc.name, NHOM)
		)
	doc.is_stock_item = 0
	doc.is_purchase_item = 1
	for cty, tk, viec in dong_can_dat(
		[{"company": d.get("company"), "expense_account": d.get("expense_account")}
			for d in doc.get("item_defaults") or []],
		tk_theo_cong_ty(),
	):
		if viec == "them":
			doc.append("item_defaults", {"company": cty, "expense_account": tk})
			continue
		for d in doc.get("item_defaults") or []:
			if (d.get("company") or "").strip() == cty:
				d.expense_account = tk
				break


def dung():
	"""Dựng nhóm CCDC dùng ngay và mặc định 242 của nhóm. Lặp lại được."""
	if not frappe.db.exists("Item Group", CHA):
		return {"nhom": 0, "ly_do": "chưa có nhóm cha %s" % CHA}
	tao = 0
	if not frappe.db.exists("Item Group", NHOM):
		g = frappe.get_doc({"doctype": "Item Group", "item_group_name": NHOM,
			"parent_item_group": CHA, "is_group": 0})
		g.flags.ignore_permissions = True
		g.insert()
		tao = 1
	g = frappe.get_doc("Item Group", NHOM)
	viec = dong_can_dat(
		[{"company": d.company, "expense_account": d.expense_account}
			for d in g.get("item_group_defaults") or []],
		tk_theo_cong_ty(),
	)
	for cty, tk, loai in viec:
		if loai == "them":
			g.append("item_group_defaults", {"company": cty, "expense_account": tk})
		else:
			for d in g.get("item_group_defaults") or []:
				if d.company == cty:
					d.expense_account = tk
	if viec:
		g.flags.ignore_permissions = True
		g.save()
	return {"nhom": tao, "mac_dinh": len(viec)}
