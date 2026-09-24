"""Dấu tick "Đi 242" trên mã món: công cụ dụng cụ mua về dùng luôn đi thẳng 242.

Vì sao có mô đun này
--------------------------------------------------------------------
Uyên mua quạt cho nhân viên (hoá đơn Điện Máy Xanh) và hỏi có phải làm
phiếu nhập kho không. Chị Dung: "CCDC chị hay hạch toán vào 242 chứ không
qua 153". Trên site cả 265 mã CCDC đều là hàng quản kho, nên hoá đơn nào
cũng đòi phiếu nhập kho.

v524 làm một nhóm mới "CCDC dùng ngay" với tiền tố mã CCDN. Anh Việt không
duyệt cách đó (24/09/2026): không tạo mã mới, dùng lại mã cũ, và làm "thành
dấu tick thôi như kiểu chặng của bánh". v525 thay bằng đúng một ô tick trên
hồ sơ món, gỡ nhóm và tiền tố của v524.

Luật (anh Việt chốt 24/09/2026)
--------------------------------------------------------------------
- Tick "Đi 242": món thành món mua, không quản kho, không bán; Item Default
  mỗi công ty có tài khoản chi phí = tài khoản số 242 của công ty đó. Hoá đơn
  mua dựng từ hoá đơn điện tử đọc Item Default này (dung_lai_hddt.tk_theo_mon)
  nên dòng đi 242, và hàng không quản kho thì không cần phiếu nhập kho.
- Bỏ tick: gỡ tài khoản 242 khỏi Item Default. Cờ quản kho KHÔNG tự bật lại,
  kế toán tự quyết.
- Món ĐÃ có sổ kho (kể cả dòng đã huỷ) thì không tick được: ERPNext không cho
  đổi hàng đã có sổ kho sang không quản kho, và tiền nhập kho đi theo tài
  khoản của kho chứ không theo mã. 101 mã như vậy chờ chị Dung quyết.
- Mã mới mở trong hai nhóm CCDC tự được tick sẵn.
- Patch v525 tick sẵn mọi mã CCDC đang dùng mà chưa từng có sổ kho (164 mã
  trên site ngày 24/09/2026).

KHÔNG làm ở đây: không tự phân bổ 242 sang chi phí hằng tháng; không đụng
101 mã có sổ kho, không sửa số tồn cũ.
"""

from frappe.utils import cint, flt

import frappe

O_TICK = "custom_di_242"
SO_TK = "242"
NHOM_CCDC = ("Công cụ Dụng cụ", "Công cụ dụng cụ Sonneto")

TRUONG_MOI = {"Item": [
	{
		"fieldname": O_TICK, "label": "Đi 242 (CCDC dùng ngay)",
		"fieldtype": "Check", "default": "0",
		"insert_after": "custom_chang_btp",
		"description": "Công cụ dụng cụ mua về dùng luôn: hoá đơn mua đi thẳng "
			"tài khoản 242, không quản kho, không cần phiếu nhập kho. Mã đã có "
			"sổ kho thì không tick được.",
	},
]}

# Cờ của món đã tick. Theo lô và số sê-ri chỉ có nghĩa với hàng quản kho: để
# nguyên thì món không quản kho vẫn đòi lô khi lập chứng từ. Một nguồn cho cả
# hook lẫn patch.
CO_TICK = {"is_stock_item": 0, "is_purchase_item": 1, "is_sales_item": 0,
	"has_batch_no": 0, "has_serial_no": 0}

# Nhóm và tiền tố v524 bị gỡ. Patch v525 xoá nhóm nếu không có món nào.
NHOM_V524 = "CCDC dùng ngay"


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


def viec_khi_luu(moi, tick, tick_truoc, nhom, co_so_kho):
	"""Hook lưu món phải làm gì. THUẦN.

	Trả về một trong: "tick" (đặt món về không quản kho, 242), "go" (gỡ 242),
	"chan" (món có sổ kho mà bị tick), "" (không làm gì).
	moi: món mới tạo. tick / tick_truoc: ô tick bây giờ và trước khi lưu.
	"""
	if moi and not tick and (nhom or "").strip() in NHOM_CCDC:
		tick = 1  # mã mới trong nhóm CCDC: tick sẵn
	if tick:
		if co_so_kho:
			return "chan"
		return "tick"
	if tick_truoc:
		return "go"
	return ""


# ------------------------------------------------------------ phần chạm hệ

def tk_theo_cong_ty():
	ra = {}
	for cty in frappe.get_all("Company", pluck="name", limit_page_length=0):
		tk = frappe.db.get_value("Account", {"company": cty, "account_number": SO_TK,
			"is_group": 0, "disabled": 0}, "name")
		if tk:
			ra[cty] = tk
	return ra


def _co_so_kho(ma):
	# Xét cả dòng đã huỷ (Codex #364 v1): mã đã từng đi kho thì không đổi nghĩa.
	return bool(ma) and bool(frappe.db.exists("Stock Ledger Entry", {"item_code": ma}))


def khi_luu_mon(doc, method=None):
	"""Hook validate Item cho ô tick Đi 242."""
	moi = doc.is_new()
	truoc = None if moi else doc.get_doc_before_save()
	tick = cint(doc.get(O_TICK))
	tick_truoc = cint(truoc.get(O_TICK)) if truoc is not None else 0
	# Chỉ tra sổ kho khi cần, món không đụng ô tick thì không tốn truy vấn.
	can_tra = bool(tick) or (moi and (doc.get("item_group") or "").strip() in NHOM_CCDC)
	viec = viec_khi_luu(moi, tick, tick_truoc, doc.get("item_group"),
		_co_so_kho(doc.name) if (can_tra and not moi) else False)
	if viec == "chan":
		# Hook này chạy SAU phép chặn đổi cờ quản kho của ERPNext, nên phải tự
		# chặn: đặt về 0 ở đây là lách qua luật của lõi.
		frappe.throw("Món %s đã có sổ kho nên không tick \"Đi 242\" được. Mã đã từng "
			"nhập kho vẫn hạch toán theo kho; hỏi kế toán cách xử lý." % doc.name)
	tk = tk_theo_cong_ty() if viec in ("tick", "go") else {}
	if viec == "tick":
		if flt(doc.get("opening_stock")):
			# Lõi chỉ lập phiếu tồn đầu kỳ cho món quản kho: để nguyên thì số
			# tồn người vừa gõ biến mất không một lời.
			frappe.throw("Món %s được tick \"Đi 242\" nên không quản kho: bỏ ô Tồn "
				"đầu kỳ, hoặc bỏ tick nếu món này phải theo dõi tồn." % (doc.name or ""))
		doc.set(O_TICK, 1)
		for k, v in CO_TICK.items():
			doc.set(k, v)
		for cty, ten_tk, loai in dong_can_dat(
			[{"company": d.get("company"), "expense_account": d.get("expense_account")}
				for d in doc.get("item_defaults") or []], tk):
			if loai == "them":
				doc.append("item_defaults", {"company": cty, "expense_account": ten_tk})
				continue
			for d in doc.get("item_defaults") or []:
				if (d.get("company") or "").strip() == cty:
					d.expense_account = ten_tk
					break
	elif viec == "go":
		dat = set(tk.values())
		for d in doc.get("item_defaults") or []:
			if (d.get("expense_account") or "") in dat:
				d.expense_account = None


def _ma_can_tick():
	"""Mã CCDC đang dùng, chưa tick, chưa từng có sổ kho."""
	ds = frappe.get_all("Item", filters={"item_group": ["in", list(NHOM_CCDC)], "disabled": 0},
		fields=["name", O_TICK], limit_page_length=0)
	return [d.name for d in ds if not cint(d.get(O_TICK)) and not _co_so_kho(d.name)]


def dung():
	"""Patch v525. Lặp lại được. Lỗi thì làm hỏng migrate, không nuốt."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	# Patch chạy trước after_migrate, nên ô tick chưa có: dựng ở đây. Lượt
	# after_migrate (truong_tu_them) dựng lại, lặp lại được.
	create_custom_fields(TRUONG_MOI, update=True)
	frappe.db.updatedb("Item")
	frappe.clear_cache(doctype="Item")
	kq = tick_ma_cu()
	kq["xoa_nhom_v524"] = go_nhom_v524()
	return kq


def tick_ma_cu():
	"""Tick sẵn mọi mã CCDC đang dùng mà chưa từng có sổ kho. Không DDL."""
	tk = tk_theo_cong_ty()
	da_tick = []
	for ma in _ma_can_tick():
		# Ghi thẳng như luoi_do_nhom.ap_dung: không gọi save() để một luật lưu
		# món khác không liên quan làm hỏng cả lượt. Món chưa có sổ kho nên
		# đổi cờ quản kho không đụng tồn.
		frappe.db.set_value("Item", ma, dict(CO_TICK, **{O_TICK: 1}), update_modified=False)
		hien = frappe.get_all("Item Default", filters={"parent": ma, "parenttype": "Item"},
			fields=["name", "company", "expense_account"], limit_page_length=0)
		for cty, ten_tk, loai in dong_can_dat(hien, tk):
			if loai == "sua":
				ten = next(d.name for d in hien if (d.company or "").strip() == cty)
				frappe.db.set_value("Item Default", ten, "expense_account", ten_tk,
					update_modified=False)
			else:
				dong = frappe.new_doc("Item Default")
				dong.update({"parent": ma, "parenttype": "Item", "parentfield": "item_defaults",
					"company": cty, "expense_account": ten_tk,
					"idx": len(hien) + 1})
				dong.db_insert()
		da_tick.append(ma)
	frappe.clear_cache(doctype="Item")

	# Soát lại: mọi mã đã tick phải không quản kho và đủ 242.
	sai = []
	for ma in da_tick:
		if cint(frappe.db.get_value("Item", ma, "is_stock_item")):
			sai.append(ma)
			continue
		hien = frappe.get_all("Item Default", filters={"parent": ma, "parenttype": "Item"},
			fields=["company", "expense_account"], limit_page_length=0)
		if dong_can_dat(hien, tk):
			sai.append(ma)
	if sai:
		frappe.throw("Tick Đi 242 chưa đủ cho %d mã: %s" % (len(sai), ", ".join(sai[:20])))
	return {"tick": len(da_tick), "ma": da_tick}


def go_nhom_v524():
	"""Gỡ nhóm "CCDC dùng ngay" của v524 nếu không có món nào (site 24/09: 0 món)."""
	if frappe.db.exists("Item Group", NHOM_V524) and not frappe.db.exists(
			"Item", {"item_group": NHOM_V524}):
		frappe.delete_doc("Item Group", NHOM_V524, ignore_permissions=True, force=True)
		return 1
	return 0
