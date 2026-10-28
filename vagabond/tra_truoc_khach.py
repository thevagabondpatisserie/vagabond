# -*- coding: utf-8 -*-
"""Khách trả trước rồi trừ dần: số dư trả trước của khách (v607).

Anh Việt 20/10/2026:

    *"À cái đoạn thanh toán qua tài khoản anh Việt là chị ấy trả trước 50
    triệu rồi trừ dần. Em nghiên cứu luồng của SAP để ra hướng xử lý cho
    dạng này (sau này anh cũng có thể bán voucher để khách nạp vào xài rồi
    trừ dần chẳng hạn)."*

Ca thật: khách trả trước 50 triệu vào tài khoản cá nhân Giám đốc, đặt bánh
nhiều lần, mỗi lần trừ dần. Trước bản này không có chỗ ghi, nên các đơn đó
bị chọn nhầm "Hàng tặng" và rơi vào luồng duyệt đơn tặng.

KHÁC GÌ VỚI `tra_truoc.py` VÀ `dat_banh.py`
==========================================
`tra_truoc.py` là tiệm trả trước cho NHÀ CUNG CẤP. `dat_banh.py` là khách
trả trước cho MỘT phiếu đặt bánh ổ cụ thể, hoá đơn ngày giao mang phương
thức "Trả trước" và số phiếu đặt. Tệp này là khách nạp một khoản CHƯA gắn
đơn nào, rồi nhiều đơn sau đó trừ dần vào khoản đó.

ĐI THEO SAP, DÙNG ĐÚNG ĐƯỜNG LÕI CỦA ERPNext
============================================
SAP gọi đây là down payment của khách: F-29 ghi khoản nhận trước vào một tài
khoản công nợ đặc biệt (special G/L A), F-39 cấn khoản đó vào hoá đơn khi
giao hàng. Thẻ quà, voucher nạp tiền là stored value, cùng hình dạng.

ERPNext có sẵn đúng cặp đó:
  * NẠP = một Payment Entry nhận tiền của khách, KHÔNG gắn hoá đơn nào, tức
    một khoản ứng trước nằm bên Có tài khoản phải thu của khách. Riêng nguồn
    "Giám đốc thu hộ" là một bút toán Journal Entry Nợ phải thu Giám đốc / Có
    phải thu khách (ứng trước), vì Payment Entry chỉ nhận tài khoản tiền.
  * TRỪ = bảng "advances" của hoá đơn bán, cấn trừ lúc ghi sổ bằng chính
    `update_against_document_in_jv` của ERPNext. Không tự viết bút toán cấn
    trừ nào, không tự sửa `outstanding_amount`.

Chỉ những phiếu MANG CỜ nạp trả trước mới được cấn tự động. Khoản ứng trước
khác của khách (tiền cọc phiếu đặt bánh, tiền khách chuyển dư) đi đường của
nó, máy không tự lấy.

HOÁ ĐƠN ĐIỆN TỬ
===============
Mỗi đơn vẫn xuất hoá đơn như thường, đúng ngày giao, đủ giá. Với hàng hoá,
NĐ 123/2020 Điều 9 (sửa bởi NĐ 70/2025) lập hoá đơn khi chuyển giao, không
phân biệt đã thu tiền hay chưa. Riêng tiệc và dịch vụ thu trước thì thời
điểm lập là lúc thu tiền: chị Dung chốt trước khi dùng luồng này cho tiệc.

Ca kiểm ở khung/kiem_thu/thu_tra_truoc_khach_607.py.
"""

# ------------------------------------------------------------ phần thuần
#
# Đặt trên `import frappe` để bộ kiểm tầng khung chạy được ở CI tay không.

PT_SO_DU = "Số dư trả trước"

# Tiền nạp về đâu. (mã, nhãn, phương thức thu, bắt ảnh, bắt quầy, giải thích)
#
# Bắt ẢNH với mọi nguồn đi qua tài khoản (chuyển khoản, thẻ, Giám đốc thu
# hộ): không có ảnh thì kế toán không có gì để đối chiếu, và phiếu qua ngân
# hàng bị chặn ghi sổ khi thiếu tệp đính kèm (chung_tu_tien.chan_thieu_dinh_kem).
# Bắt QUẦY với tiền mặt và thẻ: tiền đó nằm trong két hoặc máy quẹt của một
# quầy, màn Chốt ca phải biết để không báo két thừa.
NGUON_NAP = (
	("ck_cty", "Chuyển khoản vào tài khoản công ty", "Chuyển khoản", 1, 0,
		"Khách chuyển vào tài khoản của tiệm. Đính ảnh chuyển khoản."),
	("tien_mat", "Tiền mặt tại quầy", "Tiền mặt", 0, 1,
		"Thu ngân nhận tiền mặt, tiền nằm trong két của quầy."),
	("the_payoo", "Quẹt thẻ Payoo", "Thẻ - Payoo", 1, 1,
		"Quẹt thẻ trên máy Payoo của quầy. Chụp bill cà thẻ."),
	("the_shinhan", "Quẹt thẻ ShinhanBank", "Thẻ - ShinhanBank", 1, 1,
		"Quẹt thẻ trên máy ShinhanBank của quầy. Chụp bill cà thẻ."),
	("gd_thu_ho", "Tài khoản cá nhân Giám đốc", "", 1, 0,
		"Giám đốc thu hộ, công ty ghi phải thu lại Giám đốc. Đính ảnh chuyển khoản."),
)

TIEN_TOI_THIEU = 10000


def chuoi(x):
	return str(x if x is not None else "").strip()


def so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tron(x):
	"""Làm tròn về đồng. Tiền Việt không có số lẻ."""
	return float(round(so(x)))


def nguon_theo_ma(ma):
	"""Một nguồn nạp theo mã, dạng dict. Không có thì None. THUẦN."""
	m = chuoi(ma)
	for k, nhan, pt, anh, quay, gt in NGUON_NAP:
		if k == m:
			return {"ma": k, "nhan": nhan, "pt": pt, "can_anh": anh,
				"can_quay": quay, "giai_thich": gt}
	return None


def kiem_nap(so_tien, ma_nguon, so_anh, quay):
	"""Câu lỗi của một lần nạp, rỗng là hợp lệ. THUẦN."""
	ng = nguon_theo_ma(ma_nguon)
	if not ng:
		return "Chọn tiền nạp về đâu."
	t = tron(so_tien)
	if t < TIEN_TOI_THIEU:
		return "Số tiền nạp phải từ %s đ trở lên." % "{:,.0f}".format(TIEN_TOI_THIEU).replace(",", ".")
	if ng["can_anh"] and int(so_anh or 0) <= 0:
		return "Nạp qua %s phải đính ảnh (ảnh chuyển khoản hoặc bill cà thẻ) để kế toán đối chiếu." % ng["nhan"].lower()
	if ng["can_quay"] and not chuoi(quay):
		return "Nạp bằng %s phải chọn quầy nhận tiền, để Chốt ca của quầy đó khớp két." % ng["nhan"].lower()
	return ""


def phan_tra_truoc(pt_chinh, dong, tong):
	"""Đơn này trả bằng số dư trả trước bao nhiêu. THUẦN.

	Có bảng dòng thanh toán thì chỉ cộng các dòng mang phương thức này. Không
	có bảng thì cả đơn trả bằng số dư nếu phương thức chính là số dư.
	"""
	co = [d for d in (dong or []) if isinstance(d, dict) and so(d.get("so_tien")) > 0]
	if co:
		return tron(sum(so(d.get("so_tien")) for d in co if chuoi(d.get("pt")) == PT_SO_DU))
	return tron(tong) if chuoi(pt_chinh) == PT_SO_DU else 0.0


def phan_bo(can, nguon):
	"""Cấn số tiền `can` vào các khoản nạp, khoản cũ trước (FIFO). THUẦN.

	`nguon` là list dict {loai, ten, con, ngay}. Trả (list {loai, ten, so},
	số còn thiếu). Không đụng khoản nào đã hết số dư.
	"""
	con_can = tron(can)
	ra = []
	for n in sorted(nguon or [], key=lambda x: (chuoi(x.get("ngay")), chuoi(x.get("ten")))):
		if con_can <= 0:
			break
		c = tron(n.get("con"))
		if c <= 0:
			continue
		lay = min(c, con_can)
		ra.append({"loai": n.get("loai"), "ten": n.get("ten"), "so": lay})
		con_can -= lay
	return ra, max(0.0, con_can)


def tong_so(nap, giu_cho):
	"""Gộp số dư của một khách. THUẦN.

	`nap` là list {docstatus, tong, con}: tổng tiền phiếu và phần chưa cấn.
	`giu_cho` là tổng các đơn nháp đang chọn trả bằng số dư.
	"""
	da_nap = sum(tron(x.get("tong")) for x in nap or [] if int(x.get("docstatus") or 0) == 1)
	con = sum(tron(x.get("con")) for x in nap or [] if int(x.get("docstatus") or 0) == 1)
	cho = sum(tron(x.get("tong")) for x in nap or [] if int(x.get("docstatus") or 0) == 0)
	g = tron(giu_cho)
	return {
		"da_nap": da_nap,
		"da_tru": max(0.0, da_nap - con),
		"con_chua_can": con,
		"cho_ghi_so": cho,
		"giu_cho": g,
		"kha_dung": max(0.0, con - g),
		# Dùng được NGAY khi chọn trên màn: tính cả phiếu nạp còn chờ kế toán
		# ghi sổ, để Sales không phải đứng chờ. Lúc ghi sổ đơn thì chỉ cấn
		# được vào phiếu đã ghi sổ, thiếu là chặn và nói rõ vì sao.
		"kha_dung_tam": max(0.0, con + cho - g),
	}


def ma_lan_hop_le(ma):
	"""Mã lần gửi của form nạp: chuỗi máy sinh, 16 tới 64 ký tự chữ thường, số, gạch. THUẦN."""
	import re

	return bool(re.fullmatch(r"[a-z0-9-]{16,64}", chuoi(ma)))


def chia_don(tong, so_du, pt_con_lai):
	"""Dòng thanh toán khi trả bằng số dư. THUẦN.

	Đủ số dư thì cả đơn một dòng. Thiếu thì phần còn lại trả bằng phương
	thức khác, bắt buộc phải chọn. Trả (list dòng, câu lỗi).
	"""
	t = tron(tong)
	d = max(0.0, tron(so_du))
	if t <= 0:
		return [], "Đơn chưa có tiền để trừ."
	if d <= 0:
		return [], "Khách chưa còn số dư trả trước nào để trừ."
	if d >= t:
		return [{"pt": PT_SO_DU, "so_tien": t}], ""
	p = chuoi(pt_con_lai)
	if not p or p == PT_SO_DU:
		return [], ("Số dư chỉ còn %s đ, chưa đủ đơn %s đ. Chọn phương thức trả "
			"phần còn lại %s đ." % (_vnd(d), _vnd(t), _vnd(t - d)))
	return [{"pt": PT_SO_DU, "so_tien": d}, {"pt": p, "so_tien": t - d}], ""


def ky_tach(dong):
	"""Dấu của một bảng tách đúng dạng `ap_dung` dựng. THUẦN.

	Hai dòng, một dòng số dư và một dòng phương thức khác: trả
	"<tiền số dư>|<phương thức khác>|<tiền khác>". Dạng khác trả "".
	"""
	ds = [d for d in (dong or []) if chuoi((d or {}).get("pt")) and so((d or {}).get("so_tien")) > 0]
	if len(ds) != 2:
		return ""
	sd = [d for d in ds if chuoi(d.get("pt")) == PT_SO_DU]
	if len(sd) != 1:
		return ""
	khac = ds[1] if ds[0] is sd[0] else ds[0]
	return "%d|%s|%d" % (tron(sd[0].get("so_tien")), chuoi(khac.get("pt")), tron(khac.get("so_tien")))


def khop_tach_so_du(dong, tong, ky=""):
	"""Bảng tách số dư khi tổng đơn đã đổi. THUẦN.

	Codex #493 vòng 7: `ap_dung` tách theo tổng đơn LÚC ÁP. Sau đó đơn còn
	sửa món, giảm giá (Bill quầy Sửa hoá đơn, Pancake đồng bộ lại) thì tổng
	đổi mà hai dòng vẫn cộng ra tổng cũ, tới lúc ghi sổ bị chặn lệch tổng.

	Chỉ xét bảng `ap_dung` dựng: `ky` là dấu máy ghi lúc dựng (ô
	`vgb_ky_tach_so_du`) và bảng hiện tại phải còn đúng dấu đó (Codex #493
	vòng 8: bảng kế toán nhập tay cùng hình dạng hai dòng không được đụng,
	vì dòng tiền mặt đó là tiền đã thu thật). Giữ nguyên phần trừ số dư
	(không trừ thêm của khách), phần còn lại theo tổng mới. Tổng mới không
	vượt phần số dư thì cả đơn trả bằng số dư.

	Trả None khi không cần đổi, hoặc danh sách dòng mới (rỗng là cả đơn số dư).
	"""
	if not chuoi(ky) or ky_tach(dong) != chuoi(ky):
		return None
	ds = [d for d in (dong or []) if chuoi((d or {}).get("pt")) and so((d or {}).get("so_tien")) > 0]
	sd = [d for d in ds if chuoi(d.get("pt")) == PT_SO_DU]
	khac = ds[1] if ds[0] is sd[0] else ds[0]
	t = tron(tong)
	a = tron(sd[0].get("so_tien"))
	if t <= 0 or abs(a + tron(khac.get("so_tien")) - t) <= 1:
		return None
	if a >= t:
		return []
	return [{"pt": PT_SO_DU, "so_tien": a}, {"pt": chuoi(khac.get("pt")), "so_tien": t - a}]


def _vnd(x):
	return "{:,.0f}".format(so(x)).replace(",", ".")


# v615 (Codex #507 P1): phép kiểm tài khoản Giám đốc thu hộ thuộc phần thuần, chạy
# được không cần Frappe như mọi phép thuần khác của tệp.

def _so_nguyen(x):
	"""THUẦN: 0/1 từ ô Check (số, chuỗi "1", None); chuỗi lạ là 0."""
	try:
		return int(float(x or 0))
	except (TypeError, ValueError):
		return 0


LOAI_CO_DOI_TUONG = ("Receivable", "Payable")


def loi_tk_gd(tk, cong_ty):
	"""THUẦN: câu lỗi nếu tài khoản tk (dict đọc từ Account) không dùng được làm tài khoản
	phải thu Giám đốc thu hộ; "" nếu dùng được."""
	if not tk:
		return "Không tìm thấy tài khoản này."
	ten = tk.get("name") or ""
	if cong_ty and tk.get("company") != cong_ty:
		return "Tài khoản %s thuộc công ty khác." % ten
	if _so_nguyen(tk.get("is_group")):
		return "Tài khoản %s là tài khoản tổng hợp. Chọn tài khoản chi tiết bên dưới nó." % ten
	if _so_nguyen(tk.get("disabled")):
		return "Tài khoản %s đang tắt." % ten
	if tk.get("root_type") != "Asset":
		return "Tài khoản %s không phải tài khoản tài sản (phải thu)." % ten
	if tk.get("account_type") in LOAI_CO_DOI_TUONG:
		return ("Tài khoản %s đang theo dõi theo đối tượng (khách, nhà cung cấp). Chọn tài khoản "
			"phải thu khác không theo dõi đối tượng, ví dụ tài khoản 1388 chi tiết cho Giám đốc." % ten)
	return ""


# ------------------------------------------------------- phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, flt, nowdate  # noqa: E402

SI = "Sales Invoice"
PE = "Payment Entry"
JE = "Journal Entry"
CO = "vgb_nap_tra_truoc"
O_NGUON = "vgb_nguon_nap"
O_MA_LAN = "vgb_ma_lan_nap"
DT_DONG = "Vagabond Dong Thanh Toan"
DT_BANG = "vgb_thanh_toan_nhieu"
# Codex #493 vòng 8: dấu bền của phép tách do `ap_dung` dựng. Chỉ bảng còn
# đúng như dấu này mới được máy chỉnh lại khi tổng đơn đổi; bảng kế toán nhập
# tay (`thanh_toan_nhieu.luu`, Desk) không mang dấu nên không bao giờ bị đụng.
O_KY_TACH = "vgb_ky_tach_so_du"

TRUONG_MOI = {
	PE: [
		{
			"fieldname": CO,
			"label": "Khách nạp số dư trả trước",
			"fieldtype": "Check",
			"insert_after": "vgb_phieu_dat",
			"read_only": 1,
			"description": "Máy đánh dấu. Phiếu này là tiền khách nạp trước, các đơn sau trừ dần.",
		},
		{
			"fieldname": O_NGUON,
			"label": "Tiền nạp về đâu",
			"fieldtype": "Data",
			"insert_after": CO,
			"read_only": 1,
		},
		{
			"fieldname": O_MA_LAN,
			"label": "Mã lần gửi phiếu nạp",
			"fieldtype": "Data",
			"insert_after": O_NGUON,
			"read_only": 1,
			"hidden": 1,
			"search_index": 1,
			"description": "Máy ghi. Form nạp gửi lại sau khi mất phản hồi thì trả về đúng phiếu này, không lập phiếu thứ hai.",
		},
	],
	JE: [
		{
			"fieldname": CO,
			"label": "Khách nạp số dư trả trước",
			"fieldtype": "Check",
			"insert_after": "voucher_type",
			"read_only": 1,
			"description": "Máy đánh dấu. Bút toán này là tiền khách nạp trước qua Giám đốc thu hộ.",
		},
		{
			"fieldname": O_NGUON,
			"label": "Tiền nạp về đâu",
			"fieldtype": "Data",
			"insert_after": CO,
			"read_only": 1,
		},
		{
			"fieldname": O_MA_LAN,
			"label": "Mã lần gửi phiếu nạp",
			"fieldtype": "Data",
			"insert_after": O_NGUON,
			"read_only": 1,
			"hidden": 1,
			"search_index": 1,
			"description": "Máy ghi. Form nạp gửi lại sau khi mất phản hồi thì trả về đúng phiếu này, không lập phiếu thứ hai.",
		},
	],
	SI: [
		{
			"fieldname": O_KY_TACH,
			"label": "Phép tách số dư máy dựng",
			"fieldtype": "Data",
			"insert_after": DT_BANG,
			"read_only": 1,
			"hidden": 1,
			"no_copy": 1,
			"description": (
				"Máy ghi khi áp số dư trả trước một phần. Đơn sửa món sau đó thì máy "
				"tính lại phần còn lại theo tổng mới, chỉ khi bảng dòng thanh toán "
				"còn đúng như lúc máy dựng."
			),
		},
	],
	"Vagabond Settings": [
		{
			# v615 (anh Việt 27/10/2026: "Không biết khai chỗ này ở đâu?"): ô này từng nằm
			# lẫn trong mục Hàng biếu tặng khách VIP. Tách ra mục riêng có tên đúng việc.
			"fieldname": "sec_tra_truoc_khach",
			"label": "Khách nạp tiền trả trước",
			"fieldtype": "Section Break",
			"insert_after": "tk_chi_phi_qua_tang",
		},
		{
			"fieldname": "tk_gd_thu_ho",
			"label": "Tài khoản phải thu Giám đốc thu hộ",
			"fieldtype": "Link",
			"options": "Account",
			"insert_after": "sec_tra_truoc_khach",
			"description": (
				"Khi khách chuyển tiền trả trước vào tài khoản cá nhân Giám đốc, "
				"công ty ghi Nợ tài khoản này (phải thu lại Giám đốc) và Có khách "
				"trả trước. Chọn tài khoản chi tiết, không theo dõi theo đối tượng. "
				"Chưa chọn thì nguồn nạp Giám đốc thu hộ chưa ghi sổ được. Kế toán "
				"chọn được ngay trên màn Số dư trả trước, không cần mở Cài đặt."
			),
		},
	],
}


def _quyen():
	from vagabond.ban_hang import _kiem_quyen_ban

	_kiem_quyen_ban()


def _la_ke_toan():
	from vagabond.thu_tien import la_ke_toan

	return la_ke_toan()


def _cong_ty():
	"""Công ty của phiếu nạp: ĐÚNG công ty mà app lập hoá đơn bán.

	Codex #493 vòng 3: trước đây lấy mặc định của người dùng trước. Người
	dùng có công ty mặc định khác Global Defaults thì phiếu nạp nằm ở công ty
	đó, còn hoá đơn app (`ban_hang._cong_ty`) nằm ở công ty chung; màn vẫn
	báo số dư mà ERPNext không cấn được. Không import ban_hang (kéo requests).
	"""
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _nap_pe(khach=None, cty=None):
	loc = {CO: 1, "docstatus": ["<", 2], "party_type": "Customer", "payment_type": "Receive",
		"company": cty or _cong_ty()}
	if khach:
		loc["party"] = khach
	return [
		dict(r, loai=PE, khach=r.get("party"), tong=flt(r.get("paid_amount")),
			con=flt(r.get("unallocated_amount")))
		for r in frappe.get_all(
			PE, filters=loc,
			fields=["name", "party", "party_name", "posting_date", "paid_amount",
				"unallocated_amount", "docstatus", "mode_of_payment", O_NGUON, "owner",
				"creation", "remarks", "vgb_quay"],
			order_by="posting_date asc, creation asc", limit_page_length=0,
		)
	]


def _nap_je(khach=None, cty=None):
	ds = frappe.get_all(
		JE, filters={CO: 1, "docstatus": ["<", 2], "company": cty or _cong_ty()},
		fields=["name", "posting_date", "docstatus", O_NGUON, "owner", "creation", "user_remark"],
		order_by="posting_date asc, creation asc", limit_page_length=0,
	)
	if not ds:
		return []
	dong = frappe.get_all(
		"Journal Entry Account",
		filters={"parent": ["in", [d.name for d in ds]], "party_type": "Customer"},
		fields=["parent", "party", "credit_in_account_currency", "debit_in_account_currency",
			"reference_name"],
		limit_page_length=0,
	)
	ra = []
	for d in ds:
		cac = [x for x in dong if x.parent == d.name]
		if not cac:
			continue
		kh = cac[0].party
		if khach and kh != khach:
			continue
		tong = sum(flt(x.credit_in_account_currency) - flt(x.debit_in_account_currency) for x in cac)
		con = sum(flt(x.credit_in_account_currency) - flt(x.debit_in_account_currency)
			for x in cac if not x.reference_name)
		ra.append(dict(d, loai=JE, khach=kh, tong=tong, con=con,
			party_name=frappe.db.get_value("Customer", kh, "customer_name")))
	return ra


def cac_phieu_nap(khach=None, cty=None):
	"""Phiếu nạp của một công ty. Không truyền thì là công ty app lập hoá đơn.

	Codex #493 vòng 3: mọi phép đọc số dư phải theo ĐÚNG công ty của hoá đơn
	đang xét, vì ERPNext chỉ cấn khoản ứng trước cùng công ty.
	"""
	cty = cty or _cong_ty()
	return _nap_pe(khach, cty) + _nap_je(khach, cty)


def _dong_giu_cho(khach=None, tru=None, cty=None):
	"""Các đơn NHÁP đang chọn trả bằng số dư, kèm số tiền đang giữ."""
	loc = {"docstatus": 0, "vgb_huy": 0, "company": cty or _cong_ty()}
	if khach:
		loc["customer"] = khach
	theo_bang = {}
	for r in frappe.get_all(
		DT_DONG, filters={"pt": PT_SO_DU, "parenttype": SI},
		fields=["parent", "pt", "so_tien"], limit_page_length=0,
	):
		theo_bang.setdefault(r.parent, []).append(r)
	ten = set(theo_bang)
	ds = frappe.get_all(
		SI, filters=dict(loc, vgb_pt_thanh_toan=PT_SO_DU),
		fields=["name", "customer", "grand_total", "vgb_pt_thanh_toan", "posting_date",
			"custom_pancake_display_id"], limit_page_length=0,
	)
	da = {d.name for d in ds}
	thieu = [t for t in ten if t not in da]
	if thieu:
		ds += frappe.get_all(
			SI, filters=dict(loc, name=["in", thieu]),
			fields=["name", "customer", "grand_total", "vgb_pt_thanh_toan", "posting_date",
				"custom_pancake_display_id"], limit_page_length=0,
		)
	ra = []
	for d in ds:
		if tru and d.name == tru:
			continue
		so_tien = phan_tra_truoc(d.vgb_pt_thanh_toan, theo_bang.get(d.name) or [], d.grand_total)
		if so_tien > 0:
			ra.append(dict(d, so=so_tien))
	return ra


def so_du_khach(khach, tru=None, cty=None):
	"""Số dư của một khách trong một công ty. `tru` là tên đơn đang xét, không
	tính giữ chỗ của chính nó. `cty` là công ty của đơn; không truyền thì là
	công ty app lập hoá đơn."""
	cty = cty or _cong_ty()
	nap = cac_phieu_nap(khach, cty)
	giu = _dong_giu_cho(khach, tru=tru, cty=cty)
	return tong_so(nap, sum(g["so"] for g in giu))


# ------------------------------------------------------------------- hooks


def _dong_cua(doc):
	return [{"pt": d.get("pt"), "so_tien": d.get("so_tien")}
		for d in (doc.get(DT_BANG) or [])]


def chon_pt_ca_don(doc, pt, ha_co_may=True, doi_pt=False):
	"""MỘT cửa gán ô phương thức từ các nút của người dùng (Codex #493 vòng 4, 5).

	`pos_chot`, `pos_luu_don`, `pos_sua_don`, `luu_thanh_toan`, `chot_mot_don`
	và `hang_tang.luu_tang` đều gọi hàm này thay vì tự gán ô phương thức. Ca
	`thu_tang_tra_truoc_607` chốt không còn cửa nào tự gán.

	`doi_pt`: người dùng VỪA BẤM chip phương thức trên màn (màn gửi `doi_pt=1`),
	tức chọn một phương thức cho cả đơn. Chỉ khi đó mới để dấu
	`flags.vgb_chon_pt_ca_don` cho hook `bo_dong_tach_khi_doi_pt` bỏ bảng tách
	số dư, kể cả khi phương thức chọn trùng dòng lớn nhất (100.000 số dư +
	600.000 tiền mặt, chọn Tiền mặt). Hai màn bán gửi kèm phương thức đang
	hiện trong MỌI lần lưu, ghi sổ, sửa đơn (vòng 5): coi mỗi lần gửi kèm đó
	là chọn lại thì bấm Ghi sổ một đơn đang tách là mất phần trừ số dư.
	"""
	doc.vgb_pt_thanh_toan = pt
	if ha_co_may:
		doc.vgb_pt_do_may = 0
	if doi_pt:
		doc.flags.vgb_chon_pt_ca_don = True


def co_dong_so_du(dong):
	"""Bảng dòng thanh toán có dòng số dư trả trước không. THUẦN."""
	return any(chuoi((d or {}).get("pt")) == PT_SO_DU and so((d or {}).get("so_tien")) > 0 for d in (dong or []))


def bo_dong_tach_khi_doi_pt(doc, method=None):
	"""Hook validate, ĐỨNG TRƯỚC `hang_tang.truoc_khi_luu` và `thanh_toan_nhieu.dat_pt_chinh`.

	Codex #493 vòng 3 và vòng 4: `ap_dung` tách đơn thành dòng số dư + dòng
	phần còn lại. Người dùng sau đó chọn MỘT phương thức cho cả đơn (Bill
	quầy, Doanh thu Sales, Hàng tặng) mà bảng tách cũ còn thì `dat_pt_chinh`
	dựng lại phép tách và số dư vẫn bị trừ lúc ghi sổ; màn quầy không có chỗ
	sửa bảng. Mọi cửa chọn phương thức đi qua `chon_pt_ca_don`, để lại dấu
	`flags.vgb_chon_pt_ca_don`; có dấu và bảng có dòng số dư thì bỏ bảng, kể
	cả khi phương thức chọn trùng dòng lớn nhất.

	KHÔNG đoán từ trạng thái (ô chính khác dòng lớn nhất): lần lưu ở Desk sửa
	tay bảng dòng cũng ra trạng thái đó, xoá bảng của họ là sai. Không có dấu
	thì giữ nguyên luật cũ, `dat_pt_chinh` lấy dòng lớn nhất.
	"""
	if cint(doc.get("docstatus")) != 0:
		return
	if not getattr(doc.flags, "vgb_chon_pt_ca_don", False):
		return
	dong = [{"pt": d.get("pt"), "so_tien": d.get("so_tien")} for d in (doc.get(DT_BANG) or [])]
	if co_dong_so_du(dong):
		doc.set(DT_BANG, [])
		doc.set(O_KY_TACH, "")


def khop_dong_tach_theo_tong(doc, method=None):
	"""Hook validate, sau `bo_dong_tach_khi_doi_pt`, trước `dat_pt_chinh`.

	Đơn tách số dư mà tổng đơn đã đổi thì chỉnh lại số tiền hai dòng theo
	`khop_tach_so_du` (Codex #493 vòng 7), chỉ khi bảng còn đúng dấu máy ghi
	lúc `ap_dung` (vòng 8). Sửa tại chỗ từng dòng để giữ mã tham chiếu của
	dòng phần còn lại, rồi ghi lại dấu theo bảng mới.
	"""
	if cint(doc.get("docstatus")) != 0 or cint(doc.get("vgb_huy")):
		return
	moi = khop_tach_so_du(_dong_cua(doc), doc.get("grand_total"), doc.get(O_KY_TACH))
	if moi is None:
		return
	if not moi:
		doc.set(DT_BANG, [])
		doc.vgb_pt_thanh_toan = PT_SO_DU
		doc.set(O_KY_TACH, "")
		return
	tien = {d["pt"]: d["so_tien"] for d in moi}
	for r in doc.get(DT_BANG) or []:
		p = chuoi(r.get("pt"))
		if p in tien and so(r.get("so_tien")) > 0:
			r.so_tien = tien[p]
	doc.set(O_KY_TACH, ky_tach(moi))


def kiem_khi_luu(doc, method=None):
	"""Hook validate của hoá đơn bán: đơn trả bằng số dư phải có khách thật và đủ số dư.

	Chỉ xét khi phần trả bằng số dư hoặc khách VỪA ĐỔI. Nhịp đồng bộ Pancake
	lưu lại đơn mỗi 30 phút mà không đổi gì, chặn nó là làm hỏng cả nhịp.
	"""
	if cint(doc.get("vgb_huy")) or cint(doc.get("docstatus")) != 0:
		return
	can = phan_tra_truoc(doc.get("vgb_pt_thanh_toan"), _dong_cua(doc), doc.get("grand_total"))
	if can <= 0:
		return
	cu = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	if cu is not None:
		can_cu = phan_tra_truoc(cu.get("vgb_pt_thanh_toan"), _dong_cua(cu), cu.get("grand_total"))
		if can_cu == can and cu.get("customer") == doc.get("customer"):
			return
	from vagabond.khach_hang import la_khach_gop

	if not doc.get("customer") or la_khach_gop(doc.get("customer")):
		frappe.throw(
			"Đơn trả bằng số dư trả trước phải gắn đúng khách đã nạp tiền. Bấm chip "
			"Số dư trả trước rồi chọn khách.", title="Chưa chọn khách trả trước")
	s = so_du_khach(doc.get("customer"), tru=doc.get("name"), cty=doc.get("company"))
	if can > s["kha_dung_tam"] + 1:
		frappe.throw(
			"Khách %s chỉ còn %s đ số dư trả trước, đơn này cần trừ %s đ. Chọn trả "
			"phần còn lại bằng phương thức khác, hoặc nhờ khách nạp thêm."
			% (doc.get("customer_name") or doc.get("customer"), _vnd(s["kha_dung_tam"]), _vnd(can)),
			title="Không đủ số dư trả trước")


def can_tru_khi_ghi_so(doc, method=None):
	"""Hook before_submit: cấn phần trả bằng số dư vào các phiếu nạp, cũ trước.

	Dựng bảng `advances` của ERPNext, CHỈ từ phiếu mang cờ nạp trả trước, rồi
	tính lại tổng. Lúc ghi sổ ERPNext tự cấn (update_against_document_in_jv).
	Không đủ thì chặn ghi sổ và nói rõ: thường là phiếu nạp còn chờ kế toán
	ghi sổ.
	"""
	if cint(doc.get("vgb_huy")):
		return
	can = phan_tra_truoc(doc.get("vgb_pt_thanh_toan"), _dong_cua(doc), doc.get("grand_total"))
	if can <= 0:
		return
	nap = {(n["loai"], n["name"]) for n in cac_phieu_nap(doc.get("customer"), cty=doc.get("company"))
		if int(n["docstatus"]) == 1}
	res = doc.get_advance_entries(include_unallocated=True)
	nguon = []
	theo = {}
	for r in res:
		k = (r.reference_type, r.reference_name)
		if k not in nap or flt(r.amount) <= 0:
			continue
		ngay = frappe.db.get_value(r.reference_type, r.reference_name, "posting_date")
		khoa = "%s|%s|%s" % (r.reference_type, r.reference_name, r.get("reference_row") or "")
		nguon.append({"loai": r.reference_type, "ten": khoa, "con": flt(r.amount), "ngay": str(ngay or "")})
		theo[khoa] = r
	chia, thieu = phan_bo(can, nguon)
	if thieu > 0:
		s = so_du_khach(doc.get("customer"), cty=doc.get("company"))
		frappe.throw(
			"Đơn %s cần trừ %s đ vào số dư trả trước nhưng khách %s mới có %s đ đã ghi "
			"sổ. %sNhờ kế toán ghi sổ phiếu nạp hoặc chọn trả phần thiếu bằng phương thức khác."
			% (doc.get("custom_pancake_display_id") or doc.name, _vnd(can),
				doc.get("customer_name") or doc.get("customer"), _vnd(can - thieu),
				("Còn %s đ đang chờ kế toán ghi sổ. " % _vnd(s["cho_ghi_so"])) if s["cho_ghi_so"] else ""),
			title="Chưa đủ số dư trả trước")
	doc.set("advances", [])
	for c in chia:
		r = theo[c["ten"]]
		dong = {
			"doctype": "Sales Invoice Advance",
			"reference_type": r.reference_type,
			"reference_name": r.reference_name,
			"reference_row": r.get("reference_row"),
			"remarks": r.get("remarks"),
			"advance_amount": flt(r.amount),
			"allocated_amount": c["so"],
			"ref_exchange_rate": flt(r.get("exchange_rate")) or 1,
			"difference_posting_date": doc.get("posting_date"),
		}
		if r.get("paid_from"):
			dong["account"] = r.paid_from
		if r.get("paid_to"):
			dong["account"] = r.paid_to
		doc.append("advances", dong)
	doc.calculate_taxes_and_totals()


# ------------------------------------------------------------------ cửa ngõ


def _ds_quay():
	try:
		from vagabond import diem_ban

		return [{"ma": d["quay"], "ten": d.get("ten_ngan") or d["quay"]}
			for d in diem_ban.ds(chi_bat=True) if d.get("quay")]
	except Exception:
		return []


@frappe.whitelist()
def cai_dat():
	"""Những gì màn Số dư trả trước cần để vẽ."""
	_quyen()
	from vagabond.lib import cfg

	return {
		"pt": PT_SO_DU,
		"nguon": [nguon_theo_ma(k) for k, *_r in NGUON_NAP],
		"quay": _ds_quay(),
		"la_ke_toan": 1 if _la_ke_toan() else 0,
		"thieu_tk_gd": 0 if chuoi((cfg() or {}).get("tk_gd_thu_ho")) else 1,
		"sua_tk_gd": 1 if _duoc_sua_tk_gd() else 0,
	}


# ------------------------------------------- v615: khai tài khoản Giám đốc thu hộ tại chỗ
# Anh Việt 27/10/2026: màn nạp báo "Chưa khai ... trong Cài đặt" mà kế toán không
# biết khai ở đâu (trang Cài đặt chỉ quản trị mở được). Mở ô chọn ngay cạnh lời báo,
# cho kế toán và quản trị; phạm vi chọn đúng như ô trên Cài đặt, cộng thêm: không nhận
# tài khoản theo dõi đối tượng (phải thu, phải trả), vì bút toán Giám đốc thu hộ không
# gắn đối tượng ở dòng này.

def _duoc_sua_tk_gd():
	return bool(_la_ke_toan() or "System Manager" in frappe.get_roles())


def _chan_sua_tk_gd():
	if not _duoc_sua_tk_gd():
		frappe.throw("Chỉ kế toán chọn được tài khoản phải thu Giám đốc thu hộ.", frappe.PermissionError)


O_TK = ["name", "account_name", "account_number", "company", "is_group", "disabled", "root_type", "account_type"]


@frappe.whitelist()
def tim_tk_gd(tu=""):
	"""Gợi ý tài khoản cho ô Tài khoản phải thu Giám đốc thu hộ (đúng phạm vi ô trên Cài đặt)."""
	import re

	_chan_sua_tk_gd()
	cty = _cong_ty()
	loc = {"company": cty, "is_group": 0, "disabled": 0, "root_type": "Asset",
		"account_type": ["not in", list(LOAI_CO_DOI_TUONG)]}
	tu = re.sub(r"[%_\\]", "", chuoi(tu))[:60]
	from vagabond import tim_kiem

	loc = tim_kiem.them_loc(loc, "Account", tu, ["name", "account_name", "account_number"])
	ds = frappe.get_all("Account", filters=loc, fields=["name", "account_name", "account_number"],
		order_by="lft asc", limit_page_length=30)
	return [{"name": r.name, "ten": r.account_name or r.name, "so": r.account_number or ""} for r in ds]


@frappe.whitelist(methods=["POST"])
def luu_tk_gd(tk=""):
	"""Kế toán chọn tài khoản phải thu Giám đốc thu hộ ngay trên màn nạp."""
	_chan_sua_tk_gd()
	tk = chuoi(tk)
	row = frappe.db.get_value("Account", tk, O_TK, as_dict=True) if tk else None
	loi = loi_tk_gd(row, _cong_ty())
	if loi:
		frappe.throw(loi, title="Chưa lưu được tài khoản")
	doc = frappe.get_doc("Vagabond Settings")
	doc.set("tk_gd_thu_ho", tk)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"ok": 1, "tk": tk}


@frappe.whitelist()
def ds(tim=""):
	"""Danh sách khách đang có tiền trả trước, số dư từng người."""
	_quyen()
	nap = cac_phieu_nap()
	giu = _dong_giu_cho()
	theo = {}
	for n in nap:
		o = theo.setdefault(n["khach"], {"khach": n["khach"], "ten": n.get("party_name") or n["khach"],
			"nap": [], "giu": 0.0, "lan_cuoi": ""})
		o["nap"].append(n)
		o["lan_cuoi"] = max(o["lan_cuoi"], str(n.get("posting_date") or ""))
	for g in giu:
		if g["customer"] in theo:
			theo[g["customer"]]["giu"] += g["so"]
	q = chuoi(tim).lower()
	ra = []
	for o in theo.values():
		if q and q not in (o["ten"] + " " + o["khach"]).lower():
			continue
		s = tong_so(o["nap"], o["giu"])
		s.update({"khach": o["khach"], "ten": o["ten"], "lan_cuoi": o["lan_cuoi"]})
		ra.append(s)
	ra.sort(key=lambda x: (-x["kha_dung_tam"], x["ten"]))
	return {"khach": ra, "la_ke_toan": 1 if _la_ke_toan() else 0}


@frappe.whitelist()
def so_khach(khach):
	"""Sổ của một khách: từng lần nạp, từng đơn đã trừ, từng đơn đang giữ chỗ."""
	_quyen()
	khach = chuoi(khach)
	if not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách %s." % khach)
	nap = cac_phieu_nap(khach)
	giu = _dong_giu_cho(khach)
	dong = []
	for n in nap:
		ng = nguon_theo_ma(n.get(O_NGUON)) or {}
		dong.append({
			"loai": "nap", "ngay": str(n.get("posting_date") or ""), "chung_tu": n["name"],
			"doctype": n["loai"], "so": tron(n["tong"]),
			"ghi_chu": ng.get("nhan") or n.get("mode_of_payment") or "",
			"trang_thai": "Đã ghi sổ" if int(n["docstatus"]) == 1 else "Chờ kế toán ghi sổ",
			"cho": 0 if int(n["docstatus"]) == 1 else 1,
		})
	ten_nap = [n["name"] for n in nap if int(n["docstatus"]) == 1]
	if ten_nap:
		for a in frappe.get_all(
			"Sales Invoice Advance",
			filters={"reference_name": ["in", ten_nap], "parenttype": SI, "docstatus": 1},
			fields=["parent", "allocated_amount"], limit_page_length=0,
		):
			hd = frappe.db.get_value(SI, a.parent, ["posting_date", "custom_pancake_display_id",
				"grand_total"], as_dict=True) or {}
			dong.append({
				"loai": "tru", "ngay": str(hd.get("posting_date") or ""), "chung_tu": a.parent,
				"doctype": SI, "so": tron(a.allocated_amount),
				"ghi_chu": ("Đơn #%s" % hd.get("custom_pancake_display_id"))
				if hd.get("custom_pancake_display_id") else "Đơn %s" % a.parent,
				"trang_thai": "Đã trừ", "cho": 0,
			})
	for g in giu:
		dong.append({
			"loai": "giu", "ngay": str(g.get("posting_date") or ""), "chung_tu": g["name"],
			"doctype": SI, "so": tron(g["so"]),
			"ghi_chu": ("Đơn #%s" % g.get("custom_pancake_display_id"))
			if g.get("custom_pancake_display_id") else "Đơn %s" % g["name"],
			"trang_thai": "Giữ chỗ, chờ ghi sổ đơn", "cho": 1,
		})
	dong.sort(key=lambda x: (x["ngay"], x["loai"]), reverse=True)
	s = tong_so(nap, sum(g["so"] for g in giu))
	s.update({"khach": khach, "ten": frappe.db.get_value("Customer", khach, "customer_name"),
		"dong": dong, "la_ke_toan": 1 if _la_ke_toan() else 0})
	return s


@frappe.whitelist()
def so_du(khach, si=None):
	"""Số dư của một khách cho chip Số dư trả trước trên màn bán."""
	_quyen()
	khach = chuoi(khach)
	if not khach:
		return tong_so([], 0)
	cty = (frappe.db.get_value(SI, chuoi(si), "company") if chuoi(si) else None) or _cong_ty()
	s = so_du_khach(khach, tru=chuoi(si) or None, cty=cty)
	s["khach"] = khach
	s["ten"] = frappe.db.get_value("Customer", khach, "customer_name") or khach
	return s


def _dinh_tep(doctype, name, anh):
	n = 0
	from vagabond.hang_tang import la_anh

	for a in (anh or []):
		try:
			ten = chuoi((a or {}).get("ten")) or "anh-nap-tien.jpg"
			if not la_anh(ten):
				continue
			noi = chuoi((a or {}).get("noi_dung"))
			if "," in noi and noi[:5].lower() == "data:":
				noi = noi.split(",", 1)[1]
			if not noi:
				continue
			f = frappe.get_doc({
				"doctype": "File", "file_name": ten,
				"attached_to_doctype": doctype, "attached_to_name": name,
				"content": noi, "decode": True, "is_private": 1,
			})
			f.insert(ignore_permissions=True)
			n += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tra_truoc_khach: dinh anh nap")
	return n


def thieu_anh_sau_dinh(ng, so_da_dinh):
	"""Nguồn bắt ảnh mà không đính được tệp nào. THUẦN (Codex #493 P1)."""
	return bool((ng or {}).get("can_anh")) and int(so_da_dinh or 0) <= 0


def _chan_thieu_anh(ng, so_da_dinh):
	"""Đính ảnh hỏng thì KHÔNG giữ phiếu nạp.

	`_dinh_tep` nuốt lỗi từng tệp để một tệp hỏng không làm đổ cả lô. Nhưng
	nguồn bắt ảnh mà không đính được tệp nào thì phiếu nạp thành phiếu
	không chứng cứ: phiếu ngân hàng không ghi sổ được, bút toán Giám đốc
	thu hộ thì ghi sổ được mà không có gì để đối chiếu. Ném lỗi TRƯỚC lúc
	commit để cả phiếu lùi theo, người lập chụp lại ảnh rồi lập lại.
	"""
	if thieu_anh_sau_dinh(ng, so_da_dinh):
		frappe.throw(
			"Không đính được ảnh chuyển khoản hoặc bill cà thẻ nên chưa lập phiếu nạp. "
			"Chụp lại ảnh (JPG hoặc PNG) rồi lập lại.", title="Chưa lập phiếu nạp")


def _so_anh(anh):
	from vagabond.hang_tang import la_anh

	return len([a for a in (anh or []) if isinstance(a, dict)
		and la_anh(a.get("ten")) and chuoi(a.get("noi_dung"))])


KHOA_NAP = "vgb_nap_tra_truoc:"


def _phieu_theo_ma_lan(ma_lan):
	"""Phiếu nạp (chưa huỷ) đã lập với mã lần gửi này: (doctype, {name, nguon, khach, so})."""
	loc = {O_MA_LAN: ma_lan, CO: 1, "docstatus": ["<", 2]}
	r = frappe.db.get_value(PE, loc, ["name", O_NGUON, "party", "paid_amount"], as_dict=True)
	if r:
		return PE, {"name": r.name, "nguon": r.get(O_NGUON), "khach": r.get("party"), "so": flt(r.get("paid_amount"))}
	r = frappe.db.get_value(JE, loc, ["name", O_NGUON], as_dict=True)
	if r:
		dong = frappe.get_all("Journal Entry Account", filters={"parent": r.name, "party_type": "Customer"},
			fields=["party", "credit_in_account_currency"], limit_page_length=0)
		return JE, {"name": r.name, "nguon": r.get(O_NGUON), "khach": dong[0].party if dong else None,
			"so": sum(flt(d.credit_in_account_currency) for d in dong)}
	return None, None


def _tra_phieu_cu(dt, cu, khach, tien, nguon):
	"""Gửi lại cùng mã lần: trả đúng phiếu cũ. Khác khách, số tiền hay nguồn thì chặn."""
	if cu["khach"] != khach or tron(cu["so"]) != tron(tien) or chuoi(cu["nguon"]) != chuoi(nguon):
		frappe.throw(
			"Form này đã lập phiếu nạp %s rồi. Mở lại màn Nạp tiền để lập phiếu mới." % cu["name"],
			title="Phiếu nạp đã lập")
	return {"ok": 1, "doctype": dt, "name": cu["name"], "trung": 1}


@frappe.whitelist()
def tao_phieu_nap(khach, so_tien, nguon, anh=None, ghi_chu="", quay="", ma_giao_dich="", ma_lan=""):
	"""Lập phiếu nạp số dư trả trước, ở trạng thái CHỜ KẾ TOÁN GHI SỔ.

	Thu ngân, Sales lập; kế toán đối chiếu tiền về rồi ghi sổ. Phiếu còn chờ
	vẫn được tính tạm vào số dư khi chọn trên màn, nhưng chỉ phiếu đã ghi sổ
	mới cấn được vào đơn lúc ghi sổ đơn.

	Codex #493 vòng 3: `ma_lan` là mã form nạp sinh MỘT lần (giữ cả trong bản
	nháp tự lưu). Lần đầu đã lập mà mất phản hồi, bấm lại thì trả về đúng phiếu
	cũ, không lập phiếu thứ hai làm số dư tạm nhân đôi. Khoá có tên theo mã
	lần giữ từ lúc tra tới sau commit, hai lần bấm sát nhau cũng chỉ ra một
	phiếu (cùng nếp `doi_soat_vendor`).
	"""
	_quyen()
	ma_lan = chuoi(ma_lan).lower()
	if not ma_lan_hop_le(ma_lan):
		frappe.throw("Tải lại app rồi lập lại phiếu nạp: màn đang mở là bản cũ.",
			title="Chưa lập phiếu nạp")
	khoa = KHOA_NAP + ma_lan
	r = frappe.db.sql("select get_lock(%s, %s)", (khoa, 15))
	if not r or r[0][0] != 1:
		frappe.throw("Phiếu nạp này đang được lập ở lần bấm trước. Đợi vài giây rồi mở sổ khách xem.",
			title="Đang lập phiếu nạp")
	try:
		# Mở ảnh dữ liệu mới sau khi có khoá, không dùng ảnh đọc từ trước khi chờ.
		frappe.db.commit()
		dt, cu = _phieu_theo_ma_lan(ma_lan)
		if cu:
			return _tra_phieu_cu(dt, cu, chuoi(khach), tron(so_tien), nguon)
		return _lap_phieu_nap(khach, so_tien, nguon, anh, ghi_chu, quay, ma_giao_dich, ma_lan)
	finally:
		frappe.db.sql("select release_lock(%s)", (khoa,))


def _lap_phieu_nap(khach, so_tien, nguon, anh, ghi_chu, quay, ma_giao_dich, ma_lan):
	khach = chuoi(khach)
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Chọn khách nạp tiền.")
	from vagabond.khach_hang import la_khach_gop

	if la_khach_gop(khach):
		frappe.throw("Không nạp trả trước cho khách lẻ dùng chung. Chọn đúng hồ sơ khách.")
	if isinstance(anh, str):
		anh = frappe.parse_json(anh or "[]") or []
	loi = kiem_nap(so_tien, nguon, _so_anh(anh), quay)
	if loi:
		frappe.throw(loi, title="Chưa lập phiếu nạp")
	ng = nguon_theo_ma(nguon)
	tien = tron(so_tien)
	cty = _cong_ty()
	ngay = nowdate()
	dien_giai = ("Khách %s nạp số dư trả trước %s đ, %s.%s" % (
		khach, _vnd(tien), ng["nhan"].lower(),
		(" " + chuoi(ghi_chu)) if chuoi(ghi_chu) else ""))[:1000]
	from vagabond.thu_tien import nang_quyen_lap_phieu, _giu_chu, tk_tien_thu, loi_chua_khai_tk

	if ng["ma"] == "gd_thu_ho":
		from vagabond.lib import cfg

		tk_gd = chuoi((cfg() or {}).get("tk_gd_thu_ho"))
		if not tk_gd:
			frappe.throw(
				"Chưa chọn Tài khoản phải thu Giám đốc thu hộ. Kế toán chọn ngay trên màn "
				"Nạp tiền trả trước (nút Chọn tài khoản dưới lựa chọn Tài khoản cá nhân Giám đốc), "
				"rồi lập lại phiếu nạp.", title="Thiếu tài khoản")
		from erpnext.accounts.party import get_party_account

		tk_kh = get_party_account("Customer", khach, cty)
		with nang_quyen_lap_phieu() as goc:
			je = frappe.new_doc(JE)
			je.voucher_type = "Journal Entry"
			je.company = cty
			je.posting_date = ngay
			je.set(CO, 1)
			je.set(O_NGUON, ng["ma"])
			je.set(O_MA_LAN, ma_lan)
			je.user_remark = dien_giai
			je.cheque_no = chuoi(ma_giao_dich) or None
			je.cheque_date = ngay if chuoi(ma_giao_dich) else None
			je.append("accounts", {"account": tk_gd, "debit_in_account_currency": tien})
			je.append("accounts", {
				"account": tk_kh, "party_type": "Customer", "party": khach,
				"credit_in_account_currency": tien, "is_advance": "Yes",
			})
			je.flags.ignore_permissions = True
			je.insert(ignore_permissions=True)
			_giu_chu(je, goc)
			_chan_thieu_anh(ng, _dinh_tep(JE, je.name, anh))
		frappe.db.commit()
		return {"ok": 1, "doctype": JE, "name": je.name}

	tk, ba = tk_tien_thu(cty, ng["pt"])
	if not tk:
		frappe.throw(loi_chua_khai_tk(ng["pt"]))
	with nang_quyen_lap_phieu() as goc:
		pe = frappe.new_doc(PE)
		pe.payment_type = "Receive"
		pe.company = cty
		pe.posting_date = ngay
		pe.party_type = "Customer"
		pe.party = khach
		pe.paid_amount = tien
		pe.received_amount = tien
		pe.reference_no = chuoi(ma_giao_dich) or ("NAP-%s-%s" % (khach, frappe.generate_hash(length=6)))
		pe.reference_date = ngay
		if frappe.db.exists("Mode of Payment", ng["pt"]):
			pe.mode_of_payment = ng["pt"]
		pe.paid_to = tk
		if ba:
			pe.bank_account = ba
		pe.set(CO, 1)
		pe.set(O_NGUON, ng["ma"])
		pe.set(O_MA_LAN, ma_lan)
		if ng["can_quay"]:
			pe.vgb_quay = chuoi(quay).upper()
		pe.remarks = dien_giai
		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		_giu_chu(pe, goc)
		_chan_thieu_anh(ng, _dinh_tep(PE, pe.name, anh))
	frappe.db.commit()
	return {"ok": 1, "doctype": PE, "name": pe.name}


@frappe.whitelist()
def ghi_so_phieu_nap(doctype, name):
	"""Kế toán ghi sổ một phiếu nạp sau khi đối chiếu tiền đã về."""
	if not _la_ke_toan():
		frappe.throw("Chỉ kế toán ghi sổ phiếu nạp trả trước, sau khi thấy tiền về.")
	if doctype not in (PE, JE):
		frappe.throw("Không phải phiếu nạp trả trước.")
	d = frappe.get_doc(doctype, name)
	if not cint(d.get(CO)):
		frappe.throw("%s không phải phiếu nạp trả trước." % name)
	if cint(d.docstatus) != 0:
		frappe.throw("%s đã ghi sổ hoặc đã huỷ rồi." % name)
	d.flags.ignore_permissions = True
	d.submit()
	frappe.db.commit()
	return {"ok": 1, "name": d.name}


@frappe.whitelist()
def ap_dung(si_name, khach, pt_con_lai="", ma_tham_chieu=""):
	"""Chọn trả bằng số dư trả trước cho một đơn nháp.

	Gắn đúng khách vào đơn (ERPNext chỉ cấn được khoản ứng trước của chính
	khách trên đơn), rồi đặt dòng thanh toán: đủ số dư thì cả đơn, thiếu thì
	tách phần còn lại sang phương thức Sales chọn.
	"""
	_quyen()
	from vagabond.ban_hang import _kiem_pt
	from vagabond.khach_hang import la_khach_gop

	si = frappe.get_doc(SI, si_name)
	if cint(si.docstatus) != 0:
		frappe.throw("Đơn %s đã ghi sổ, không đổi phương thức được nữa." % si_name)
	if cint(si.get("vgb_huy")):
		frappe.throw("Đơn %s đã huỷ." % si_name)
	khach = chuoi(khach)
	if not khach or not frappe.db.exists("Customer", khach) or la_khach_gop(khach):
		frappe.throw("Chọn đúng khách đã nạp tiền trả trước.")
	_kiem_pt(PT_SO_DU, si.get("custom_nguon"))
	if chuoi(pt_con_lai):
		pt_con_lai = _kiem_pt(pt_con_lai, si.get("custom_nguon"))
	s = so_du_khach(khach, tru=si.name, cty=si.company)
	dong, loi = chia_don(si.grand_total, s["kha_dung_tam"], pt_con_lai)
	if loi:
		frappe.throw(loi, title="Chưa áp số dư trả trước")
	if si.get("customer") != khach:
		for o in ("contact_person", "contact_display", "contact_mobile", "contact_email",
				"customer_address", "address_display"):
			si.set(o, None)
		si.customer = khach
	# KHÔNG đặt vgb_khach_no: ô đó là dấu của đơn công nợ, đặt vào thì màn
	# Công nợ phải thu đi đòi một đơn khách đã trả trước rồi.
	si.set("vgb_thanh_toan_nhieu", [])
	if len(dong) > 1:
		for d in dong:
			r = {"pt": d["pt"], "so_tien": d["so_tien"]}
			if d["pt"] != PT_SO_DU and chuoi(ma_tham_chieu):
				r["ma_tham_chieu"] = chuoi(ma_tham_chieu)
			si.append("vgb_thanh_toan_nhieu", r)
	# Dấu bền cho hook `khop_dong_tach_theo_tong` (Codex #493 vòng 8).
	si.set(O_KY_TACH, ky_tach(dong) if len(dong) > 1 else "")
	si.vgb_pt_thanh_toan = max(dong, key=lambda x: x["so_tien"])["pt"]
	si.vgb_pt_do_may = 0
	si.flags.ignore_permissions = True
	si.save()
	frappe.db.commit()
	return {"ok": 1, "dong": dong, "so_du": so_du_khach(khach, tru=si.name, cty=si.company)}


def thu_nap_tai_quay(quay, tu_luc, den_luc, theo_ngay=False):
	"""Tiền nạp trả trước đã vào két hoặc máy quẹt của một quầy trong ca.

	Cho màn Chốt ca, cùng nếp với `dat_banh.thu_ung_truoc`. Tính cả phiếu
	còn chờ kế toán ghi sổ: tiền đã nằm trong két rồi, chờ ghi sổ là việc
	của sổ sách chứ không làm két bớt đi. Không đếm hai lần: đơn trả bằng số
	dư mang phương thức thuộc nhóm tiền về ngày khác, đã rơi khỏi bảng két.
	"""
	loc = {
		CO: 1, "docstatus": ["<", 2], "payment_type": "Receive", "party_type": "Customer",
		"vgb_quay": chuoi(quay).upper(),
	}
	if not loc["vgb_quay"]:
		return {}
	from frappe.utils import getdate

	if theo_ngay:
		loc["posting_date"] = ["between", [str(getdate(tu_luc)), str(getdate(den_luc))]]
	else:
		loc["creation"] = ["between", [str(tu_luc), str(den_luc)]]
	ra = {}
	for r in frappe.get_all(PE, filters=loc, fields=["mode_of_payment", "paid_amount"],
			limit_page_length=0):
		k = chuoi(r.mode_of_payment) or "Chưa rõ"
		ra[k] = ra.get(k, 0.0) + flt(r.paid_amount)
	return ra
