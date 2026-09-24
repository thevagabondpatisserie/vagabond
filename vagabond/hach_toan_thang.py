"""Hạch toán từng dòng trước khi ghi sổ thẳng một hoá đơn mua (v526).

Vì sao có mô đun này (chị Dung 24/09/2026)
--------------------------------------------------------------------
Màn Đối chiếu hoá đơn mua có nút "Ghi sổ thẳng, không nối phiếu" cho hoá đơn
không qua kho: xăng dầu, dịch vụ, phí ship. Nút đó ghi sổ ngay, không cho
xem dòng nào đi tài khoản nào. Chị Dung ghi thử hoá đơn xăng HDM-26-09-00335
(Công ty Xăng dầu Khu vực II, 92.081 đ) thì dòng xăng rơi vào 632 giá vốn
hàng bán, vì dòng không gắn Món nên ERPNext lấy tài khoản chi phí mặc định
của công ty. Chị vào Desk sửa 632 thành 6417 thì bị chặn quyền.

Anh Việt chọn (24/09/2026): chọn tài khoản TỪNG DÒNG trước khi ghi sổ.

Cách làm
--------
1. Trước khi ghi sổ, màn hiện từng dòng chi phí kèm tài khoản máy gợi ý.
   Gợi ý theo thứ tự: khai trên danh mục Món, tài khoản đang có trên dòng
   nếu khác mặc định công ty, tài khoản LẦN TRƯỚC của đúng nhà cung cấp đó,
   cuối cùng mới là mặc định công ty (632, kèm nhắc đỏ).
   Nhờ "lần trước của nhà cung cấp", chị Dung sửa hoá đơn xăng một lần thì
   các hoá đơn xăng sau tự ra 6417.
2. Ghi sổ đặt đúng tài khoản người chọn lên dòng, và báo cho hai hook tự
   đặt tài khoản (khai trên Món, tài khoản đầu phiếu dịch vụ) đừng đè lên.
3. Chỉ đổi được dòng CHI PHÍ: chưa nối phiếu nhập và không phải hàng quản
   kho. Dòng hàng kho đi theo luật tài khoản chờ của kho, không đụng.

KHÔNG làm ở đây: không sửa hoá đơn đã ghi sổ. Tờ đã ghi sổ thì kế toán sửa
trên Desk (quyền mở ở quyen_ap.py, v526).
"""

import frappe
from frappe.utils import cint, flt

# Cờ trên doc báo hai hook tự đặt tài khoản bỏ qua các dòng người đã chọn.
CO_NGUOI_CHON = "vgb_tk_nguoi_chon"

# Loại tài khoản không nhận chi phí của một dòng hoá đơn mua.
LOAI_TK_CAM = ("Payable", "Receivable", "Bank", "Cash", "Stock",
	"Stock Received But Not Billed", "Tax")
GOC_TK_DUOC = ("Expense", "Asset")


# ------------------------------------------------------------ phần thuần

def so_hieu(tk):
	"""'6417 - Chi phí ... - TV' -> '6417'."""
	return (tk or "").split(" - ")[0].strip()


def canh_bao(tk):
	"""Câu nhắc khi tài khoản đang chọn dễ sai cho một dòng chi phí."""
	if so_hieu(tk).startswith("632"):
		return ("632 là giá vốn hàng bán. Xăng dầu, dịch vụ, phí ship "
			"thường vào nhóm 641 hoặc 642.")
	return ""


def goi_y(tk_hien, tk_mac_dinh, tk_lan_truoc, tk_mon):
	"""Tài khoản gợi ý cho một dòng và nguồn của nó. THUẦN.

	Trả (tài khoản, nguồn), nguồn là một trong: mon, dang_co, lan_truoc,
	mac_dinh."""
	if tk_mon:
		return tk_mon, "mon"
	if tk_hien and tk_hien != tk_mac_dinh:
		return tk_hien, "dang_co"
	if tk_lan_truoc:
		return tk_lan_truoc, "lan_truoc"
	return tk_hien or tk_mac_dinh or "", "mac_dinh"


NHAN_NGUON = {
	"mon": "khai trên danh mục Món",
	"dang_co": "đang có trên dòng",
	"lan_truoc": "lần trước của nhà cung cấp này",
	"mac_dinh": "mặc định của hệ thống",
}


def loi_chon(dong_chi_phi, dong_khac, chon):
	"""Soát bộ tài khoản người gửi lên. THUẦN.

	dong_chi_phi: {tên dòng: số thứ tự} các dòng được đổi.
	dong_khac: {tên dòng: số thứ tự} dòng hàng kho hoặc đã nối phiếu.
	chon: {tên dòng: tài khoản}.
	Trả danh sách câu lỗi, rỗng là hợp lệ."""
	loi = []
	for ten, tk in (chon or {}).items():
		if ten in dong_khac:
			loi.append("Dòng %s là hàng qua kho hoặc đã nối phiếu nhập, tài khoản đi theo kho, "
				"không đổi ở đây." % dong_khac[ten])
		elif ten not in dong_chi_phi:
			loi.append("Có một dòng không còn trên hoá đơn. Tải lại màn rồi chọn lại.")
	for ten, stt in sorted(dong_chi_phi.items(), key=lambda x: x[1]):
		if not (chon or {}).get(ten):
			loi.append("Dòng %s chưa chọn tài khoản hạch toán." % stt)
	return loi


def loi_tai_khoan(tk, cong_ty):
	"""tk: dict company, is_group, disabled, root_type, account_type. THUẦN."""
	if not tk:
		return "không tồn tại"
	if tk.get("company") != cong_ty:
		return "thuộc công ty khác"
	if cint(tk.get("is_group")):
		return "là tài khoản tổng hợp, chọn tài khoản chi tiết bên dưới"
	if cint(tk.get("disabled")):
		return "đã ngừng sử dụng"
	if (tk.get("account_type") or "") in LOAI_TK_CAM:
		return "là tài khoản %s, không nhận chi phí của hoá đơn mua" % tk.get("account_type")
	if (tk.get("root_type") or "") not in GOC_TK_DUOC:
		return "không phải tài khoản chi phí hay tài sản"
	return ""


# ------------------------------------------------------------ phần chạm hệ

def la_dong_chi_phi(d):
	"""Dòng đổi được tài khoản: chưa nối phiếu nhập, không phải hàng quản kho."""
	if (d.get("purchase_receipt") or "").strip():
		return False
	ma = (d.get("item_code") or "").strip()
	if not ma:
		return True
	return not cint(frappe.db.get_value("Item", ma, "is_stock_item"))


def _tk_mac_dinh(cong_ty):
	return frappe.get_cached_value("Company", cong_ty, "default_expense_account") or ""


def _tk_mon(ma, cong_ty):
	ma = (ma or "").strip()
	if not ma:
		return ""
	return frappe.db.get_value("Item Default", {"parent": ma, "company": cong_ty},
		"expense_account") or ""


def _anh_mon(ma):
	"""Ảnh món trên danh mục, rỗng thì app hiện ô 🍰 (AGENTS.md, ảnh món)."""
	ma = (ma or "").strip()
	return (frappe.db.get_value("Item", ma, "image") or "") if ma else ""


def tk_lan_truoc(ncc, cong_ty, bo_qua=""):
	"""Tài khoản của dòng chi phí gần nhất trên hoá đơn ĐÃ GHI SỔ của NCC này.

	Bỏ qua mặc định công ty (632): lấy nó làm gợi ý là lặp lại đúng cái sai
	đang muốn sửa."""
	if not ncc:
		return ""
	mac_dinh = _tk_mac_dinh(cong_ty)
	ds = frappe.db.sql(
		"""select i.expense_account, i.item_code
		from `tabPurchase Invoice Item` i
		inner join `tabPurchase Invoice` p on p.name = i.parent
		left join `tabItem` m on m.name = i.item_code
		where p.supplier = %s and p.company = %s and p.docstatus = 1
			and p.name != %s
			and ifnull(i.purchase_receipt, '') = ''
			and ifnull(m.is_stock_item, 0) = 0
			and ifnull(i.expense_account, '') != ''
		order by p.posting_date desc, p.modified desc
		limit 30""",
		(ncc, cong_ty, bo_qua or ""), as_dict=True)
	for r in ds:
		if r.expense_account != mac_dinh:
			return r.expense_account
	return ""


def dong_hach_toan(doc):
	"""Các dòng của tờ, kèm gợi ý tài khoản. Dùng cho màn và cho ca kiểm."""
	mac_dinh = _tk_mac_dinh(doc.company)
	lan_truoc = None
	ra = []
	for d in doc.get("items") or []:
		chi_phi = la_dong_chi_phi(d)
		o = {
			"ten": d.name, "idx": d.idx,
			"ten_hang": d.get("item_name") or d.get("item_code") or "",
			"ma": d.get("item_code") or "",
			"anh": _anh_mon(d.get("item_code")),
			"tien": flt(d.get("amount")),
			"tk": d.get("expense_account") or "",
			"sua_duoc": 1 if chi_phi else 0,
		}
		if chi_phi:
			if lan_truoc is None:
				lan_truoc = tk_lan_truoc(doc.supplier, doc.company, doc.name)
			tk, nguon = goi_y(o["tk"], mac_dinh, lan_truoc, _tk_mon(o["ma"], doc.company))
			o["goi_y"] = tk
			o["nguon"] = nguon
			o["nhan_nguon"] = NHAN_NGUON.get(nguon, "")
			o["canh_bao"] = canh_bao(tk)
		ra.append(o)
	return ra


def ap_tai_khoan(doc, chon):
	"""Đặt tài khoản người chọn lên dòng. Soát trước, sai là dừng, chưa đổi gì."""
	chon = {k: (v or "").strip() for k, v in (chon or {}).items()}
	dong_cp, dong_khac = {}, {}
	for d in doc.get("items") or []:
		(dong_cp if la_dong_chi_phi(d) else dong_khac)[d.name] = d.idx
	loi = loi_chon(dong_cp, dong_khac, chon)
	for tk in sorted(set(v for v in chon.values() if v)):
		ly_do = loi_tai_khoan(frappe.db.get_value("Account", tk,
			["company", "is_group", "disabled", "root_type", "account_type"], as_dict=True),
			doc.company)
		if ly_do:
			loi.append("Tài khoản %s %s." % (tk, ly_do))
	if loi:
		frappe.throw("Chưa ghi sổ được:<br>" + "<br>".join(loi), title="Kiểm lại hạch toán")
	for d in doc.get("items") or []:
		if d.name in chon:
			d.expense_account = chon[d.name]
	# Hai hook tự đặt tài khoản (khai trên Món, tài khoản đầu phiếu dịch vụ)
	# chạy trong validate và before_submit: báo chúng đừng đè lên.
	doc.flags.setdefault(CO_NGUOI_CHON, {})
	doc.flags[CO_NGUOI_CHON].update(chon)
	# Phiếu dịch vụ có ô tài khoản đầu phiếu: khớp nó theo người chọn để
	# lần lưu sau không đổi ngược lại.
	if doc.get("vgb_tk_chi_phi"):
		ds = set(chon.values())
		doc.vgb_tk_chi_phi = ds.pop() if len(ds) == 1 else None
	return chon


def nguoi_da_chon(doc, ten_dong):
	"""Hook tự đặt tài khoản gọi hàm này để biết có nên bỏ qua dòng không."""
	co = getattr(doc, "flags", None) or {}
	return bool((co.get(CO_NGUOI_CHON) or {}).get(ten_dong))


def soat_sau_ghi(ten_hd, chon):
	"""Đọc lại sau khi ghi sổ, cả DÒNG lẫn SỔ CÁI, trong cùng giao dịch.

	Codex #368 finding 1: bản đầu chỉ đọc ô tài khoản trên dòng. Hook on_submit
	hay luật ghi sổ của ERPNext mà Nợ tài khoản khác, để nguyên ô trên dòng, thì
	bản đầu vẫn chốt. Nay so thêm bút toán sổ cái thật của tờ (lech_so_cai)."""
	if not chon:
		return []
	dong = frappe.get_all("Purchase Invoice Item",
		filters={"parent": ten_hd, "parenttype": "Purchase Invoice"},
		fields=["name", "idx", "expense_account", "base_net_amount",
			"enable_deferred_expense", "deferred_expense_account"])
	lech = []
	theo_ten = {d.name: d for d in dong}
	for ten, tk in chon.items():
		d = theo_ten.get(ten)
		that = d.expense_account if d else None
		if that != tk:
			lech.append("dòng %s: chọn %s mà dòng ghi %s" % (d.idx if d else "?", tk, that))
	gl = {}
	for tk, so in frappe.db.sql("""select account, sum(debit - credit)
		from `tabGL Entry`
		where voucher_type = 'Purchase Invoice' and voucher_no = %s and is_cancelled = 0
		group by account""", ten_hd):
		gl[tk] = flt(so)
	cong_ty = frappe.db.get_value("Purchase Invoice", ten_hd, "company")
	return lech + lech_so_cai(chon, dong, gl, _tk_mac_dinh(cong_ty))


def _so_tien(v):
	return "{:,.0f}".format(flt(v)).replace(",", ".")


def lech_so_cai(chon, dong, gl, mac_dinh, sai_so=1.0):
	"""So bút toán sổ cái của tờ với các dòng người đã chọn tài khoản. THUẦN.

	chon: {tên dòng: tài khoản}. dong: dòng của tờ sau khi ghi sổ. gl: {tài
	khoản: Nợ trừ Có} của đúng tờ này. Hai luật:
	1. Mỗi tài khoản người chọn phải nhận ĐỦ, CÙNG CHIỀU với tổng tiền các dòng
	   chọn nó: tiền dương thì Nợ ít nhất bằng, tiền âm (tờ trả hàng, Codex
	   #368 vòng 3) thì Có ít nhất bằng. Nhận nhiều hơn cùng chiều thì được
	   (chiết khấu tách riêng, thuế tính vào chi phí, dòng khác cùng tài khoản).
	2. Tài khoản mặc định công ty (632) không dòng nào mang mà sổ cái vẫn phát
	   sinh, Nợ hay Có, đó chính là lỗi chị Dung gặp.
	Dòng chi phí trả trước (enable_deferred_expense) ERPNext Nợ tài khoản chờ
	phân bổ của dòng chứ không Nợ tài khoản chi phí, nên tính theo tài khoản đó."""
	can, tren_dong = {}, set()
	for d in dong or []:
		tk = d.get("deferred_expense_account") if cint(d.get("enable_deferred_expense")) else d.get("expense_account")
		tren_dong.add(tk)
		if d.get("name") in (chon or {}):
			can[tk] = can.get(tk, 0) + flt(d.get("base_net_amount"))
	lech = []
	for tk in sorted(can):
		that, mong = flt(gl.get(tk)), can[tk]
		thieu = (that + sai_so < mong) if mong >= 0 else (that - sai_so > mong)
		if thieu:
			lech.append("sổ cái ghi %s %s đ (Nợ trừ Có), các dòng chọn tài khoản này cộng %s đ" % (
				tk, _so_tien(that), _so_tien(mong)))
	if mac_dinh and mac_dinh not in tren_dong and abs(flt(gl.get(mac_dinh))) > sai_so:
		lech.append("sổ cái ghi %s %s đ (Nợ trừ Có) mà không dòng nào đi tài khoản này" % (
			mac_dinh, _so_tien(gl.get(mac_dinh))))
	return lech


@frappe.whitelist()
def xem(name):
	"""Màn hạch toán trước khi ghi sổ thẳng."""
	from vagabond.doi_chieu_mua import _kiem_quyen, _ghi_so_duoc
	_kiem_quyen()
	doc = frappe.get_doc("Purchase Invoice", name)
	doc.check_permission("read")
	return {
		"name": doc.name, "ncc": doc.supplier_name or doc.supplier,
		"docstatus": doc.docstatus, "tong": flt(doc.grand_total),
		"dong": dong_hach_toan(doc),
		"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,
	}
