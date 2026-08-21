"""Lõi kế toán mua hàng: hàng về chưa có hoá đơn theo dõi theo từng NCC.

Chị Dung chốt 21/08/2026: TK 335 là tài khoản TRÍCH TRƯỚC, không được dùng
làm chỗ chờ hoá đơn cho hàng đã nhập kho. Hàng về chưa hoá đơn là nợ phải
trả người bán, phải nằm trong nhóm 331 và phải theo dõi được theo từng mã
nhà cung cấp.

ERPNext gọi chỗ chờ này là "Stock Received But Not Billed" (viết tắt SRBNB
trong tệp này), khai ở Company. Mặc định ERPNext KHÔNG gắn đối tác vào dòng
sổ cái của tài khoản đó, nên sổ chi tiết công nợ không biết nợ ai. Tệp này
vá đúng chỗ đó.

VÌ SAO KHÔNG TRỎ THẲNG VÀO 331 - đọc trước khi định "sửa cho đúng đề bài"
------------------------------------------------------------------------
Đề bài ban đầu là trỏ SRBNB thẳng vào chính TK 331. Đã dò mã nguồn ERPNext
v16 và đường đó làm hỏng số dư hoá đơn, cụ thể:

1. `gl_entry.check_mandatory` NÉM LỖI nếu một dòng vào tài khoản có
   account_type Payable mà thiếu đối tác. Cái này hook bên dưới vá được.
2. Nhưng `accounts/utils.get_payment_ledger_entries` sinh Payment Ledger
   Entry cho MỌI dòng vào tài khoản Payable. Khi lập hoá đơn mua, dòng Nợ
   SRBNB và dòng Có phải trả cùng nằm trên 331, cùng đối tác, và dòng Nợ
   không có against_voucher nên máy tự quy nó về CHÍNH hoá đơn đó. Kết quả
   `update_voucher_outstanding` lấy hiệu hai dòng: hoá đơn 100 triệu hiện
   thành còn nợ mỗi phần thuế. Kế toán nhìn sổ tưởng đã trả gần hết.
3. Vá mục 2 phải đặt against_voucher trỏ về phiếu nhập, nhưng ERPNext gộp
   các dòng SRBNB bằng `merge_similar_entries` TRƯỚC khi mình chạm tới, nên
   một hoá đơn lập từ hai phiếu nhập là hết đường tách. Muốn đúng phải chép
   lại cả `make_item_gl_entries`, tức là ôm một bản sao mã nguồn ERPNext,
   mà site này đang chạy v16 và còn lên phiên bản nữa.

Nên đường đã chọn: mở MỘT tài khoản con trong nhóm 331, giữ account_type là
"Stock Received But Not Billed" để hệ thống thanh toán của ERPNext không
đụng vào, rồi gắn đối tác lên từng dòng bằng hook. Bản chất kế toán đúng ý
chị Dung (không dùng 335, nằm trong nhóm 331, chi tiết theo NCC), mà số dư
hoá đơn không bị máy tính sai.

CẦU NỐI CHO 113 PHIẾU NHẬP CŨ
-----------------------------
Tới sáng 21/08/2026 đang có 113 phiếu nhập chưa có hoá đơn, khoảng 204
triệu, đã ghi Có vào 335. ERPNext lập hoá đơn thì lấy tài khoản SRBNB HIỆN
TẠI của Company, nên đổi cấu hình xong là các hoá đơn về sau ghi Nợ tài
khoản mới, để 335 treo vĩnh viễn 189 triệu.

`giu_tk_theo_phieu_nhap` chặn đúng chỗ đó: hoá đơn lập từ phiếu nhập nào
thì đọc sổ cái của chính phiếu đó, phiếu cũ ghi ở 335 thì hoá đơn cũng ghi
Nợ 335. Không sửa một dòng sổ quá khứ nào (QT-11), chỉ đảm bảo đường ra
khớp đường vào.
"""

import frappe
from frappe.utils import flt

# Tài khoản đề nghị cho hàng về chưa hoá đơn. Số hiệu và tên có thể đổi
# theo ý chị Dung, cửa `dat_tk_hang_chua_hoa_don` nhận tham số.
TK_DE_NGHI_SO = "3311"
TK_DE_NGHI_TEN = "Phải trả người bán, hàng về chưa có hoá đơn"

# Loại tài khoản BẮT BUỘC của chỗ chờ hoá đơn. Đặt Payable vào đây là rơi
# đúng cái bẫy đã tả ở đầu tệp.
LOAI_TK = "Stock Received But Not Billed"

QUYEN_KT = ("System Manager", "Accounts Manager", "Giám đốc", "AP Giám đốc")


# ---------------------------------------------------------------- phép thuần


def gan_doi_tac(cac_dong, tk_cho, ma_ncc):
	"""Gắn đối tác vào các dòng sổ cái rơi vào tài khoản chờ hoá đơn.

	`cac_dong` là danh sách dòng sổ cái ERPNext vừa dựng (mỗi dòng là một
	từ điển có khoá `account`). Trả về CHÍNH danh sách đó sau khi sửa, để
	gọi được kiểu `return gan_doi_tac(super().get_gl_entries(), ...)`.

	Không đụng vào dòng đã có đối tác: dòng phải trả của hoá đơn mua cũng
	nằm trên nhóm 331 và ERPNext đã điền đúng rồi, ghi đè lên là hỏng.
	"""
	if not cac_dong or not tk_cho or not ma_ncc:
		return cac_dong
	for d in cac_dong:
		if d.get("account") != tk_cho:
			continue
		if d.get("party"):
			continue
		d["party_type"] = "Supplier"
		d["party"] = ma_ncc
	return cac_dong


def tk_cho_theo_so_cai(cac_dong_gl, cac_tk_ung_vien):
	"""Đọc sổ cái của một phiếu nhập, đoán nó đã dùng tài khoản chờ nào.

	`cac_dong_gl` là các dòng GL Entry của phiếu nhập, `cac_tk_ung_vien` là
	tập tài khoản chờ đã từng dùng (cũ và mới). Trả về tên tài khoản, hoặc
	None nếu phiếu không đụng tài khoản chờ nào.

	Chọn theo SỐ TIỀN lớn nhất chứ không lấy dòng đầu: một phiếu nhập có
	thể có dòng thuế lặt vặt vào tài khoản khác.
	"""
	if not cac_dong_gl:
		return None
	ung_vien = set(cac_tk_ung_vien or ())
	tong = {}
	for d in cac_dong_gl:
		tk = d.get("account")
		if tk not in ung_vien:
			continue
		tong[tk] = tong.get(tk, 0.0) + abs(flt(d.get("credit"))) + abs(flt(d.get("debit")))
	if not tong:
		return None
	return sorted(tong.items(), key=lambda x: (-x[1], x[0]))[0][0]


def phieu_nhap_cua_hoa_don(cac_dong_hang):
	"""Danh sách phiếu nhập mà một hoá đơn mua đang trỏ tới, không trùng."""
	ra = []
	for d in cac_dong_hang or ():
		ma = d.get("purchase_receipt")
		if ma and ma not in ra:
			ra.append(ma)
	return ra


def can_bac_cau(cac_phieu, tk_cua_phieu, tk_hien_tai):
	"""Có phải bắc cầu về tài khoản cũ không, và bắc về tài khoản nào.

	Trả về tên tài khoản phải dùng, hoặc None nếu cứ để ERPNext tự lo.

	Chỉ bắc cầu khi MỌI phiếu nhập của hoá đơn cùng ghi vào một tài khoản
	cũ khác tài khoản hiện tại. Hoá đơn trộn phiếu cũ với phiếu mới thì trả
	None và để người ta tự xử: máy đoán bừa ở đây là đẻ ra chênh lệch mà
	không ai biết.
	"""
	if not cac_phieu or not tk_hien_tai:
		return None
	da_dung = set()
	for ma in cac_phieu:
		tk = tk_cua_phieu.get(ma)
		if not tk:
			return None
		da_dung.add(tk)
	if len(da_dung) != 1:
		return None
	tk = da_dung.pop()
	return tk if tk != tk_hien_tai else None


# ------------------------------------------------------- phần chạm hệ thống


def _cong_ty_mac_dinh():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_value(
		"Company", {"name": ["!=", ""]}, "name")


def tk_cho_hien_tai(cong_ty):
	return frappe.get_cached_value("Company", cong_ty, "stock_received_but_not_billed")


def _cac_tk_ung_vien(cong_ty):
	"""Mọi tài khoản từng đóng vai chỗ chờ hoá đơn: đang khai và các loại cũ."""
	ra = set()
	tk = tk_cho_hien_tai(cong_ty)
	if tk:
		ra.add(tk)
	for r in frappe.get_all("Account", filters={
		"company": cong_ty, "account_type": LOAI_TK, "is_group": 0,
	}, pluck="name"):
		ra.add(r)
	# 335 đã đóng vai này từ đầu năm tới 21/08/2026, mà sau khi đổi cấu hình
	# thì account_type của nó không còn dấu vết gì. Phải nêu tên ra.
	for r in frappe.get_all("Account", filters={
		"company": cong_ty, "account_number": ["in", ["335", TK_DE_NGHI_SO]],
	}, pluck="name"):
		ra.add(r)
	return ra


def tk_cua_phieu_nhap(ten_phieu, cong_ty):
	"""Phiếu nhập này đã ghi hàng chưa hoá đơn vào tài khoản nào."""
	dong = frappe.get_all("GL Entry", filters={
		"voucher_type": "Purchase Receipt", "voucher_no": ten_phieu,
		"is_cancelled": 0,
	}, fields=["account", "debit", "credit"])
	return tk_cho_theo_so_cai(dong, _cac_tk_ung_vien(cong_ty))


def giu_tk_theo_phieu_nhap(doc, method=None):
	"""Hook validate Purchase Invoice: hoá đơn ghi về đúng tài khoản phiếu nhập.

	Chạy SAU `set_expense_account` của ERPNext (doc_events kiểu validate
	chạy sau phương thức cùng tên của lớp), nên ghi đè được con số nó vừa
	điền. Có bọc try/except: đây là lưới an toàn cho chuyện chuyển tài
	khoản, hỏng thì cứ để ERPNext làm mặc định chứ không được chặn kế toán
	lập hoá đơn.
	"""
	try:
		if doc.get("is_opening") == "Yes" or doc.get("update_stock"):
			return
		cac_phieu = phieu_nhap_cua_hoa_don(doc.get("items") or ())
		if not cac_phieu:
			return
		hien_tai = tk_cho_hien_tai(doc.company)
		if not hien_tai:
			return
		tk_cua_phieu = {}
		for ma in cac_phieu:
			tk_cua_phieu[ma] = tk_cua_phieu_nhap(ma, doc.company)
		tk_bac_cau = can_bac_cau(cac_phieu, tk_cua_phieu, hien_tai)
		if not tk_bac_cau:
			return
		for d in doc.get("items") or ():
			if d.get("purchase_receipt") and d.get("expense_account") == hien_tai:
				d.expense_account = tk_bac_cau
		doc.stock_received_but_not_billed = tk_bac_cau
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"vagabond: bac cau tai khoan hang chua hoa don")


# ------------------------------------------------------------------ cửa ngõ


def _chan():
	if not set(frappe.get_roles()) & set(QUYEN_KT):
		frappe.throw("Chỉ kế toán trưởng hoặc giám đốc mới chạy được việc này.")


@frappe.whitelist()
def kiem_tra(cong_ty=None):
	"""Bảng tình hình tài khoản hàng về chưa hoá đơn, không sửa gì cả."""
	_chan()
	cong_ty = cong_ty or _cong_ty_mac_dinh()
	hien_tai = tk_cho_hien_tai(cong_ty)
	ung_vien = sorted(_cac_tk_ung_vien(cong_ty))
	du = []
	for tk in ung_vien:
		dong = frappe.get_all("GL Entry", filters={
			"account": tk, "company": cong_ty, "is_cancelled": 0,
		}, fields=["debit", "credit", "party"])
		if not dong:
			continue
		du.append({
			"tai_khoan": tk,
			"so_dong": len(dong),
			"du_co": sum(flt(d.credit) - flt(d.debit) for d in dong),
			"dong_co_doi_tac": sum(1 for d in dong if d.party),
			"dang_khai": 1 if tk == hien_tai else 0,
		})
	chua_hoa_don = frappe.get_all("Purchase Receipt", filters={
		"docstatus": 1, "company": cong_ty,
		"status": ["in", ["To Bill", "Partly Billed"]],
	}, fields=["name", "supplier", "grand_total", "per_billed"])
	return {
		"cong_ty": cong_ty,
		"tk_dang_khai": hien_tai,
		"loai_tk_dang_khai": frappe.get_cached_value("Account", hien_tai, "account_type")
			if hien_tai else None,
		"cac_tai_khoan": du,
		"so_phieu_chua_hoa_don": len(chua_hoa_don),
		"tien_chua_hoa_don": sum(
			flt(p.grand_total) * (100 - flt(p.per_billed)) / 100 for p in chua_hoa_don),
		"so_nha_cung_cap": len({p.supplier for p in chua_hoa_don}),
	}


@frappe.whitelist()
def dat_tk_hang_chua_hoa_don(so_hieu=None, ten=None, cong_ty=None, chay_that=0):
	"""Mở tài khoản chờ hoá đơn trong nhóm 331 và khai vào Company.

	Gọi trống là chạy thử, chỉ trả kế hoạch. Truyền chay_that=1 mới ghi.
	Chạy lại lần hai không đổi gì thêm.
	"""
	_chan()
	chay_that = int(chay_that or 0)
	cong_ty = cong_ty or _cong_ty_mac_dinh()
	so_hieu = (so_hieu or TK_DE_NGHI_SO).strip()
	ten = (ten or TK_DE_NGHI_TEN).strip()
	viet_tat = frappe.get_cached_value("Company", cong_ty, "abbr")
	hien_tai = tk_cho_hien_tai(cong_ty)

	tk_331 = frappe.db.get_value("Account", {
		"company": cong_ty, "account_number": "331"}, ["name", "parent_account"], as_dict=True)
	if not tk_331:
		frappe.throw("Không tìm thấy TK 331 của công ty %s. Dừng, không đoán bừa." % cong_ty)

	ten_moi = "%s - %s - %s" % (so_hieu, ten, viet_tat)
	da_co = frappe.db.exists("Account", ten_moi)
	ke = {
		"chay_that": chay_that,
		"cong_ty": cong_ty,
		"tk_dang_khai": hien_tai,
		"tk_se_dung": ten_moi,
		"tk_da_ton_tai": 1 if da_co else 0,
		"cha": tk_331.parent_account,
	}
	if not chay_that:
		ke["ghi_chu"] = (
			"Chạy thử. Sẽ %s tài khoản %s (loại %s, cùng nhóm với %s) rồi khai "
			"vào ô Stock Received But Not Billed của công ty, thay cho %s. "
			"Sổ quá khứ KHÔNG bị đụng: hoá đơn của phiếu nhập cũ vẫn ghi về "
			"tài khoản cũ nhờ cầu nối giu_tk_theo_phieu_nhap."
			% ("dùng lại" if da_co else "mở mới", ten_moi, LOAI_TK,
				tk_331.name, hien_tai))
		return ke

	if not da_co:
		doc = frappe.new_doc("Account")
		doc.account_name = ten
		doc.account_number = so_hieu
		doc.company = cong_ty
		doc.parent_account = tk_331.parent_account
		doc.account_type = LOAI_TK
		doc.root_type = "Liability"
		doc.report_type = "Balance Sheet"
		doc.is_group = 0
		doc.insert(ignore_permissions=True)
		ke["tk_se_dung"] = doc.name
	else:
		loai = frappe.db.get_value("Account", ten_moi, "account_type")
		if loai != LOAI_TK:
			frappe.db.set_value("Account", ten_moi, "account_type", LOAI_TK)
			ke["da_sua_loai_tk"] = "%s -> %s" % (loai, LOAI_TK)

	frappe.db.set_value("Company", cong_ty, "stock_received_but_not_billed",
		ke["tk_se_dung"])
	frappe.clear_document_cache("Company", cong_ty)
	frappe.db.commit()
	ke["ghi_chu"] = (
		"Xong. Từ phiếu nhập tiếp theo, hàng về chưa hoá đơn ghi Có %s kèm mã "
		"nhà cung cấp trên từng dòng. Phiếu nhập cũ đã ghi ở %s thì hoá đơn "
		"của chúng vẫn ghi Nợ về đúng %s, không để lại số treo."
		% (ke["tk_se_dung"], hien_tai, hien_tai))
	return ke
