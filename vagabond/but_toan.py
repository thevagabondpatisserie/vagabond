# -*- coding: utf-8 -*-
"""Hach toan tay va dinh khoan mau, lam tren app cho chi Dung.

Anh Viet 14/08/2026: "chi Dung ke toan cung mong muon co the thao tac hach
toan, dinh khoan... (anh khong ranh nghiep vu nay)".

Do that truoc khi lam: cong ty co 174 tai khoan tieng Viet theo Thong tu
200 va 2.888 but toan so cai, nhung chi co DUNG HAI Journal Entry go tay.
Nghia la moi but toan trong so deu do may sinh ra tu hoa don va phieu kho;
nhung viec ke toan phai tu go - trich luong, trich bao hiem, phan bo chi
phi tra truoc, ket chuyen thue - chua tung duoc ghi lan nao.

Vi sao khong bao chi Dung mo Journal Entry ben Desk: mot but toan ben do
la bang trong voi cot Account, Debit, Credit, Party Type, Cost Center. Go
dung thi phai nho so hieu tai khoan doi ung. Man nay lam nguoc lai: chon
DINH KHOAN MAU theo viec that ("trich luong thang", "phan bo chi phi tra
truoc"), may bay san cap tai khoan No va Co, chi Dung chi dien so tien.

Van giu duong tu do: ai muon go tay tung dong van chon duoc tai khoan bat
ky. Mau chi la loi tat, khong phai hang rao.
"""

import json

import frappe
from frappe.utils import cint, flt, getdate, nowdate, today

QUYEN_XEM = {
	"System Manager", "Accounts Manager", "Accounts User",
	"AP Kiểm soát (FIN)", "AP Giám đốc", "Vagabond Bao cao",
}
QUYEN_LAP = {"System Manager", "Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)"}
QUYEN_GHI = {"System Manager", "Accounts Manager", "AP Kiểm soát (FIN)"}


# Dinh khoan mau. Moi dong: (so hieu tai khoan, "no" hoac "co", nhan hien
# tren man, co bat buoc dien khong).
#
# So hieu ghi bang DAU CHUOI ten tai khoan trong bang he thong tai khoan cua
# cong ty, vi ben do ten day du la "3341 - Phai tra cong nhan vien".
MAU = [
	{
		"k": "luong",
		"ten": "Trích lương phải trả nhân viên",
		"icon": "💰",
		"mo_ta": "Ghi nhận lương tháng vào chi phí, chưa trả tiền.",
		"dong": [
			{"tk": "6271", "ben": "no", "nhan": "Lương bộ phận bếp và sản xuất"},
			{"tk": "6411", "ben": "no", "nhan": "Lương bộ phận bán hàng"},
			{"tk": "6421", "ben": "no", "nhan": "Lương bộ phận quản lý"},
			{"tk": "3341", "ben": "co", "nhan": "Phải trả công nhân viên", "tu_tinh": 1},
		],
	},
	{
		"k": "baohiem_dn",
		"ten": "Trích bảo hiểm phần công ty chịu",
		"icon": "🩺",
		"mo_ta": "Phần bảo hiểm doanh nghiệp đóng, tính vào chi phí.",
		"dong": [
			{"tk": "6421", "ben": "no", "nhan": "Chi phí bảo hiểm công ty chịu"},
			{"tk": "3383", "ben": "co", "nhan": "Bảo hiểm xã hội"},
			{"tk": "3384", "ben": "co", "nhan": "Bảo hiểm y tế"},
			{"tk": "3386", "ben": "co", "nhan": "Bảo hiểm thất nghiệp"},
		],
	},
	{
		"k": "baohiem_nld",
		"ten": "Khấu trừ bảo hiểm vào lương nhân viên",
		"icon": "✂️",
		"mo_ta": "Phần người lao động chịu, trừ thẳng vào lương phải trả.",
		"dong": [
			{"tk": "3341", "ben": "no", "nhan": "Trừ vào lương phải trả"},
			{"tk": "3383", "ben": "co", "nhan": "Bảo hiểm xã hội"},
			{"tk": "3384", "ben": "co", "nhan": "Bảo hiểm y tế"},
			{"tk": "3386", "ben": "co", "nhan": "Bảo hiểm thất nghiệp"},
		],
	},
	{
		"k": "tra_luong",
		"ten": "Chi trả lương",
		"icon": "🏦",
		"mo_ta": "Chuyển khoản hoặc chi tiền mặt trả lương đã trích.",
		"dong": [
			{"tk": "3341", "ben": "no", "nhan": "Trả lương công nhân viên"},
			{"tk": "1121", "ben": "co", "nhan": "Chuyển khoản ngân hàng"},
			{"tk": "1111", "ben": "co", "nhan": "Chi tiền mặt"},
		],
	},
	{
		"k": "tra_truoc_ghi",
		"ten": "Ghi nhận chi phí trả trước",
		"icon": "📅",
		"mo_ta": "Tiền thuê mặt bằng, bảo hiểm, phí trả một lần cho nhiều tháng.",
		"dong": [
			{"tk": "242", "ben": "no", "nhan": "Chi phí trả trước"},
			{"tk": "1121", "ben": "co", "nhan": "Chuyển khoản ngân hàng"},
			{"tk": "1111", "ben": "co", "nhan": "Chi tiền mặt"},
			{"tk": "331", "ben": "co", "nhan": "Còn nợ nhà cung cấp"},
		],
	},
	{
		"k": "tra_truoc_pb",
		"ten": "Phân bổ chi phí trả trước hàng tháng",
		"icon": "🧮",
		"mo_ta": "Mỗi tháng đưa một phần từ 242 vào chi phí.",
		"dong": [
			{"tk": "6271", "ben": "no", "nhan": "Phân bổ cho bếp và sản xuất"},
			{"tk": "6417", "ben": "no", "nhan": "Phân bổ cho bán hàng"},
			{"tk": "6427", "ben": "no", "nhan": "Phân bổ cho quản lý"},
			{"tk": "242", "ben": "co", "nhan": "Chi phí trả trước", "tu_tinh": 1},
		],
	},
	{
		"k": "khau_tru_gtgt",
		"ten": "Khấu trừ thuế GTGT cuối kỳ",
		"icon": "🏛️",
		"mo_ta": "Bù thuế đầu vào với thuế đầu ra trước khi nộp.",
		"dong": [
			{"tk": "33311", "ben": "no", "nhan": "Thuế GTGT đầu ra"},
			{"tk": "1331", "ben": "co", "nhan": "Thuế GTGT được khấu trừ"},
		],
	},
	{
		"k": "nop_thue",
		"ten": "Nộp thuế vào ngân sách",
		"icon": "🧾",
		"mo_ta": "Nộp GTGT, thuế thu nhập cá nhân, thuế môn bài.",
		"dong": [
			{"tk": "33311", "ben": "no", "nhan": "Thuế GTGT phải nộp"},
			{"tk": "3335", "ben": "no", "nhan": "Thuế thu nhập cá nhân"},
			{"tk": "3338", "ben": "no", "nhan": "Thuế môn bài và thuế khác"},
			{"tk": "1121", "ben": "co", "nhan": "Chuyển khoản ngân hàng", "tu_tinh": 1},
		],
	},
	{
		"k": "phi_ngan_hang",
		"ten": "Phí ngân hàng và phí dịch vụ nhỏ",
		"icon": "💳",
		"mo_ta": "Phí chuyển khoản, phí quản lý tài khoản, phí máy cà thẻ.",
		"dong": [
			{"tk": "6428", "ben": "no", "nhan": "Chi phí bằng tiền khác"},
			{"tk": "1121", "ben": "co", "nhan": "Trừ vào tài khoản ngân hàng"},
		],
	},
	{
		"k": "rut_tien",
		"ten": "Rút tiền gửi về quỹ tiền mặt",
		"icon": "🏧",
		"mo_ta": "Chuyển tiền từ ngân hàng về két.",
		"dong": [
			{"tk": "1111", "ben": "no", "nhan": "Nhập quỹ tiền mặt"},
			{"tk": "1121", "ben": "co", "nhan": "Rút từ ngân hàng"},
		],
	},
	{
		"k": "nop_tien",
		"ten": "Nộp tiền mặt vào ngân hàng",
		"icon": "🏦",
		"mo_ta": "Mang tiền quầy đi nộp vào tài khoản.",
		"dong": [
			{"tk": "1121", "ben": "no", "nhan": "Vào tài khoản ngân hàng"},
			{"tk": "1111", "ben": "co", "nhan": "Xuất quỹ tiền mặt"},
		],
	},
	{
		"k": "ket_chuyen_gia_thanh",
		"ten": "Kết chuyển chi phí sản xuất vào giá thành",
		"icon": "🥐",
		"mo_ta": "Dồn nguyên liệu, nhân công, sản xuất chung vào 154 cuối kỳ.",
		"dong": [
			{"tk": "154", "ben": "no", "nhan": "Chi phí sản xuất dở dang", "tu_tinh": 1},
			{"tk": "621", "ben": "co", "nhan": "Chi phí nguyên vật liệu trực tiếp"},
			{"tk": "622", "ben": "co", "nhan": "Chi phí nhân công trực tiếp"},
			{"tk": "6271", "ben": "co", "nhan": "Chi phí sản xuất chung"},
		],
	},
]

MAU_THEO_KEY = {m["k"]: m for m in MAU}


def _cty():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)


def _kiem(quyen, viec):
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _tim_tk(so, cty=None):
	"""Tim Account theo so hieu dat o dau ten. Tra ve None neu khong thay."""
	cty = cty or _cty()
	ra = frappe.get_all(
		"Account",
		filters={"company": cty, "is_group": 0, "account_name": ["like", so + " %"]},
		fields=["name", "account_name", "account_type"],
		limit=1,
	)
	return ra[0] if ra else None


@frappe.whitelist()
def danh_sach_mau():
	_kiem(QUYEN_XEM, "xem định khoản mẫu")
	cty = _cty()
	ra = []
	for m in MAU:
		dong = []
		thieu = []
		for d in m["dong"]:
			tk = _tim_tk(d["tk"], cty)
			if not tk:
				thieu.append(d["tk"])
			dong.append({
				"tk": d["tk"],
				"tk_day_du": tk["name"] if tk else None,
				"ten_tk": tk["account_name"] if tk else None,
				"ben": d["ben"],
				"nhan": d["nhan"],
				"tu_tinh": cint(d.get("tu_tinh")),
				"can_ben": 1 if tk and tk.get("account_type") in ("Receivable", "Payable") else 0,
			})
		ra.append({
			"k": m["k"], "ten": m["ten"], "icon": m["icon"], "mo_ta": m["mo_ta"],
			"dong": dong, "thieu_tk": thieu,
		})
	return {"mau": ra, "lap_duoc": 1 if (QUYEN_LAP & set(frappe.get_roles())) else 0}


@frappe.whitelist()
def tim_tai_khoan(tu_khoa="", so_dong=40):
	"""Goi y tai khoan de go tay. Chi tra ve tai khoan chi tiet, khong nhom."""
	_kiem(QUYEN_XEM, "tra cứu tài khoản")
	cty = _cty()
	dk = {"company": cty, "is_group": 0, "disabled": 0}
	if (tu_khoa or "").strip():
		dk["account_name"] = ["like", "%" + tu_khoa.strip() + "%"]
	ds = frappe.get_all(
		"Account", filters=dk, fields=["name", "account_name", "account_type", "root_type"],
		order_by="account_name asc", limit_page_length=cint(so_dong) or 40,
	)
	return {
		"rows": [
			{
				"ma": x["name"], "ten": x["account_name"],
				"kieu": x["account_type"] or "", "loai": x["root_type"] or "",
				"can_ben": 1 if x["account_type"] in ("Receivable", "Payable") else 0,
			}
			for x in ds
		]
	}


@frappe.whitelist()
def danh_sach(so_ngay=60, chip=None, tu_khoa=None):
	"""Cac but toan go tay. Khong lay but toan may sinh tu hoa don."""
	_kiem(QUYEN_XEM, "xem bút toán")
	from frappe.utils import add_days

	cty = _cty()
	rows = frappe.get_all(
		"Journal Entry",
		filters={
			"company": cty,
			"posting_date": [">=", add_days(nowdate(), -int(so_ngay or 60))],
		},
		fields=["name", "posting_date", "voucher_type", "total_debit", "user_remark",
		        "docstatus", "title", "owner", "cheque_no"],
		order_by="posting_date desc, creation desc",
		limit_page_length=0,
	)
	dem = {
		"nhap": len([r for r in rows if r["docstatus"] == 0]),
		"da_ghi": len([r for r in rows if r["docstatus"] == 1]),
		"da_huy": len([r for r in rows if r["docstatus"] == 2]),
	}
	tat_ca = len(rows)
	if chip == "nhap":
		rows = [r for r in rows if r["docstatus"] == 0]
	elif chip == "da_ghi":
		rows = [r for r in rows if r["docstatus"] == 1]
	elif chip == "da_huy":
		rows = [r for r in rows if r["docstatus"] == 2]
	if tu_khoa:
		k = tu_khoa.strip().lower()
		rows = [
			r for r in rows
			if k in (r["user_remark"] or "").lower() or k in (r["name"] or "").lower()
			or k in (r["title"] or "").lower()
		]
	return {
		"rows": rows[:200],
		"dem": dem,
		"tat_ca": tat_ca,
		"con_nua": max(0, len(rows) - 200),
		"tong": sum(flt(r["total_debit"]) for r in rows if r["docstatus"] == 1),
		"lap_duoc": 1 if (QUYEN_LAP & set(frappe.get_roles())) else 0,
		"ghi_duoc": 1 if (QUYEN_GHI & set(frappe.get_roles())) else 0,
	}


@frappe.whitelist()
def xem(ma):
	_kiem(QUYEN_XEM, "xem bút toán")
	d = frappe.get_doc("Journal Entry", ma)
	return {
		"ma": d.name,
		"ngay": d.posting_date,
		"dien_giai": d.user_remark or d.title or "",
		"trang_thai": {0: "Nháp", 1: "Đã ghi sổ", 2: "Đã huỷ"}.get(d.docstatus, ""),
		"nhap": 1 if d.docstatus == 0 else 0,
		"tong": flt(d.total_debit),
		"dong": [
			{
				"tk": x.account,
				"ten_tk": frappe.db.get_value("Account", x.account, "account_name"),
				"no": flt(x.debit_in_account_currency),
				"co": flt(x.credit_in_account_currency),
				"ben": x.party or "",
				"dien_giai": x.user_remark or "",
			}
			for x in d.accounts
		],
		"ghi_duoc": 1 if (QUYEN_GHI & set(frappe.get_roles())) else 0,
	}


@frappe.whitelist()
def tao(dong, ngay=None, dien_giai=None, mau=None, ghi_so=0):
	"""Tao mot but toan tay.

	dong: [{tk, no, co, ben_loai, ben, dien_giai}]. Chi nhan dong co so tien.
	"""
	_kiem(QUYEN_LAP, "lập bút toán")
	if isinstance(dong, str):
		dong = json.loads(dong)
	dong = [d for d in (dong or []) if flt(d.get("no")) or flt(d.get("co"))]
	if len(dong) < 2:
		frappe.throw("Bút toán phải có ít nhất hai dòng có số tiền.")

	tong_no = sum(flt(d.get("no")) for d in dong)
	tong_co = sum(flt(d.get("co")) for d in dong)
	if abs(tong_no - tong_co) > 1:
		frappe.throw(
			"Bút toán chưa cân: bên Nợ %s đ, bên Có %s đ, lệch %s đ."
			% ("{:,.0f}".format(tong_no), "{:,.0f}".format(tong_co),
			   "{:,.0f}".format(abs(tong_no - tong_co)))
		)

	cty = _cty()
	d = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": cty,
		"posting_date": getdate(ngay or today()),
		"user_remark": (dien_giai or "").strip()
		or (MAU_THEO_KEY.get(mau or "", {}).get("ten") or "Bút toán tay"),
		"accounts": [],
	})
	for x in dong:
		tk = x.get("tk")
		if not tk or not frappe.db.exists("Account", tk):
			frappe.throw("Không thấy tài khoản %s." % tk)
		if frappe.db.get_value("Account", tk, "is_group"):
			frappe.throw("Tài khoản %s là tài khoản nhóm, không hạch toán thẳng vào được." % tk)
		hang = {
			"account": tk,
			"debit_in_account_currency": flt(x.get("no")),
			"credit_in_account_currency": flt(x.get("co")),
			"user_remark": (x.get("dien_giai") or "").strip() or None,
		}
		kieu = frappe.db.get_value("Account", tk, "account_type")
		if kieu in ("Receivable", "Payable"):
			bl = x.get("ben_loai") or ("Customer" if kieu == "Receivable" else "Supplier")
			if not x.get("ben"):
				frappe.throw(
					"Tài khoản %s là tài khoản công nợ, phải chọn %s."
					% (tk, "khách hàng" if kieu == "Receivable" else "nhà cung cấp")
				)
			hang["party_type"] = bl
			hang["party"] = x.get("ben")
		d.append("accounts", hang)

	d.flags.ignore_permissions = True
	d.insert(ignore_permissions=True)
	if cint(ghi_so):
		_kiem(QUYEN_GHI, "ghi sổ bút toán")
		d.submit()
	return {
		"ok": 1,
		"ma": d.name,
		"loi_nhan": "Đã lập bút toán %s, tổng %s đ.%s"
		% (d.name, "{:,.0f}".format(tong_no),
		   " Đã ghi sổ." if cint(ghi_so) else " Còn ở dạng nháp, bấm Ghi sổ khi soát xong."),
	}


@frappe.whitelist()
def ghi_so(ma):
	_kiem(QUYEN_GHI, "ghi sổ bút toán")
	d = frappe.get_doc("Journal Entry", ma)
	if d.docstatus != 0:
		frappe.throw("Bút toán này không còn ở dạng nháp.")
	d.submit()
	return {"ok": 1, "loi_nhan": "Đã ghi sổ bút toán %s." % ma}


@frappe.whitelist()
def huy(ma, ly_do=None):
	"""Huy but toan da ghi so. KHONG xoa - de nguyen dau vet trong so."""
	_kiem(QUYEN_GHI, "huỷ bút toán")
	d = frappe.get_doc("Journal Entry", ma)
	if d.docstatus != 1:
		frappe.throw("Chỉ huỷ được bút toán đã ghi sổ.")
	d.cancel()
	if (ly_do or "").strip():
		try:
			d.add_comment("Comment", "Huỷ: %s" % ly_do.strip())
		except Exception:
			pass
	return {"ok": 1, "loi_nhan": "Đã huỷ bút toán %s. Tờ vẫn nằm trong sổ ở trạng thái đã huỷ." % ma}
