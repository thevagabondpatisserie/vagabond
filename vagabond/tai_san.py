# -*- coding: utf-8 -*-
"""Tai san co dinh va cong cu dung cu phan bo dan, lam tren app cho chi Dung.

Anh Viet 14/08/2026: "chi Dung ke toan cung mong muon co the thao tac hach
toan, dinh khoan, phan bo tai san (anh khong ranh nghiep vu nay)".

Do that truoc khi lam: bang he thong tai khoan cua cong ty da san sang tu
truoc - co du 2111 TSCD huu hinh, 2141 Hao mon TSCD huu hinh, 2411 Mua sam
TSCD, 242 Chi phi tra truoc, 153 Cong cu dung cu, va ba tai khoan chi phi
khau hao 6274 (san xuat), 6414 (ban hang), 6424 (quan ly). Nhung co KHONG
MOT tai san nao duoc khai, khong mot nhom tai san nao duoc lap. Nghia la
viec thieu khong phai bang tai khoan ma la du lieu tai san.

Vi sao khong bao chi Dung vao Desk khai thang: mot Asset cua ERPNext bat
buoc phai co Item (is_fixed_asset), Location va Asset Category dung san.
Ba thu do la khai niem cua phan mem chu khong phai cua ke toan Viet Nam.
Man nay hoi chi Dung dung nam thu chi ay biet - ten tai san, nhom, ngay
dua vao su dung, nguyen gia, so nam, bo phan dung - roi may tu dung ba
thu kia o duoi.

Cong cu dung cu: ke toan Viet Nam phan bo dan qua 242 chu khong khau hao
qua 214. ERPNext khong co khai niem CCDC rieng, nen o day CCDC cung la mot
Asset nhung nhom cua no tro vao 242 va 6423, khong tro vao 2111 va 2141.
Ket qua ghi so ra dung nhu but toan tay, ma chi Dung khong phai nho.
"""

import json

import frappe
from frappe.utils import add_months, cint, flt, getdate, nowdate, today

CTY_TRUONG = "company"

QUYEN_XEM = {
	"System Manager", "Accounts Manager", "Accounts User",
	"AP Kiểm soát (FIN)", "AP Giám đốc", "Vagabond Bao cao",
}
QUYEN_SUA = {"System Manager", "Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)"}

NHOM_HANG_TS = "Tài sản Cố định"

# Nam nhom mau. So nam mac dinh lay trong khung cua Thong tu 45/2013/TT-BTC
# roi chon mot con so hop ly cho tiem banh, chi Dung sua duoc tung tai san.
#
# tk_ts    - tai khoan giu nguyen gia
# tk_hao   - tai khoan hao mon luy ke (CCDC de trong vi 242 tu giam dan)
# tk_cp    - tai khoan chi phi nhan khau hao moi ky
NHOM_MAU = [
	{
		"k": "nhaxuong",
		"ten": "Nhà xưởng và cải tạo mặt bằng",
		"icon": "🏗️",
		"mo_ta": "Sửa chữa lớn mặt bằng, hệ thống điện nước, trần sàn, biển hiệu gắn cố định.",
		"nam": 10,
		"bo_phan": "Quản lý",
		"tk_ts": "2111 - TSCĐ hữu hình",
		"tk_hao": "2141 - Hao mòn TSCĐ hữu hình",
		"tk_cp": "6424 - Chi phí khấu hao TSCĐ",
	},
	{
		"k": "maybep",
		"ten": "Máy móc thiết bị bếp",
		"icon": "🥐",
		"mo_ta": "Lò nướng, máy trộn, tủ ủ, tủ đông, máy đánh kem, bếp công nghiệp.",
		"nam": 7,
		"bo_phan": "Sản xuất",
		"tk_ts": "2111 - TSCĐ hữu hình",
		"tk_hao": "2141 - Hao mòn TSCĐ hữu hình",
		"tk_cp": "6274 - Chi phí khấu hao TSCĐ",
	},
	{
		"k": "thietbiban",
		"ten": "Thiết bị quầy và bán hàng",
		"icon": "🧾",
		"mo_ta": "Tủ trưng bày, máy tính tiền, máy in bill, máy cà thẻ, tủ mát quầy.",
		"nam": 5,
		"bo_phan": "Bán hàng",
		"tk_ts": "2111 - TSCĐ hữu hình",
		"tk_hao": "2141 - Hao mòn TSCĐ hữu hình",
		"tk_cp": "6414 - Chi phí khấu hao TSCĐ",
	},
	{
		"k": "vanphong",
		"ten": "Thiết bị văn phòng và công nghệ",
		"icon": "💻",
		"mo_ta": "Máy tính, máy in, camera, máy chấm công, thiết bị mạng.",
		"nam": 4,
		"bo_phan": "Quản lý",
		"tk_ts": "2111 - TSCĐ hữu hình",
		"tk_hao": "2141 - Hao mòn TSCĐ hữu hình",
		"tk_cp": "6424 - Chi phí khấu hao TSCĐ",
	},
	{
		"k": "xecoi",
		"ten": "Phương tiện vận tải",
		"icon": "🛵",
		"mo_ta": "Xe máy, xe tải nhỏ, thùng giao hàng gắn xe.",
		"nam": 6,
		"bo_phan": "Bán hàng",
		"tk_ts": "2111 - TSCĐ hữu hình",
		"tk_hao": "2141 - Hao mòn TSCĐ hữu hình",
		"tk_cp": "6414 - Chi phí khấu hao TSCĐ",
	},
	{
		"k": "ccdc",
		"ten": "Công cụ dụng cụ phân bổ dần",
		"icon": "🍳",
		"mo_ta": "Khuôn, khay, nồi, bàn ghế, đồ dùng dưới 30 triệu - phân bổ qua 242, không khấu hao qua 214.",
		"nam": 2,
		"bo_phan": "Quản lý",
		"tk_ts": "242 - Chi phí trả trước",
		"tk_hao": "242 - Chi phí trả trước",
		"tk_cp": "6423 - Chi phí đồ dùng văn phòng",
	},
]

NHOM_THEO_KEY = {n["k"]: n for n in NHOM_MAU}

NOI_DE_MAC_DINH = "The Vagabond Pâtisserie"


# ------------------------------------------------------------------ nen


def _cty():
	c = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if not c:
		frappe.throw("Chưa đặt công ty mặc định.")
	return c


def _viet_tat(cty=None):
	return frappe.db.get_value("Company", cty or _cty(), "abbr")


def _tk(ten_ngan, cty=None):
	"""Doi '2111 - TSCD huu hinh' thanh ten Account that co duoi ma cong ty."""
	cty = cty or _cty()
	day_du = "%s - %s" % (ten_ngan, _viet_tat(cty))
	if frappe.db.exists("Account", day_du):
		return day_du
	# Phong khi ten tai khoan bi sua chut it: tim theo so hieu dau chuoi.
	so = ten_ngan.split(" ")[0]
	ra = frappe.get_all(
		"Account",
		filters={"company": cty, "is_group": 0, "account_name": ["like", so + " %"]},
		pluck="name",
		limit=1,
	)
	return ra[0] if ra else None


def _kiem(quyen, viec):
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _sua_duoc():
	return bool(QUYEN_SUA & set(frappe.get_roles()))


# ------------------------------------------------------------ cai dat nen


def _bao_dam_location(ten=None):
	ten = (ten or NOI_DE_MAC_DINH).strip()
	if frappe.db.exists("Location", ten):
		return ten
	d = frappe.get_doc({"doctype": "Location", "location_name": ten})
	d.insert(ignore_permissions=True)
	return d.name


def _bao_dam_item(nhom):
	"""Moi nhom tai san mot ma hang. Chi Dung khong phai biet toi cho nay."""
	ma = "TSCD-" + nhom["k"].upper()
	if frappe.db.exists("Item", ma):
		return ma
	d = frappe.get_doc({
		"doctype": "Item",
		"item_code": ma,
		"item_name": nhom["ten"],
		"item_group": NHOM_HANG_TS if frappe.db.exists("Item Group", NHOM_HANG_TS) else "All Item Groups",
		"stock_uom": "Nos" if frappe.db.exists("UOM", "Nos") else "Cái",
		"is_stock_item": 0,
		"is_fixed_asset": 1,
		"is_purchase_item": 1,
		"is_sales_item": 0,
		"asset_category": nhom["ten"],
		"description": nhom["mo_ta"],
	})
	d.insert(ignore_permissions=True)
	return d.name


def _bao_dam_nhom(nhom, cty=None):
	"""Tao Asset Category neu chua co. Idempotent - chay lai khong sinh trung."""
	cty = cty or _cty()
	ten = nhom["ten"]
	tk_ts, tk_hao, tk_cp = _tk(nhom["tk_ts"], cty), _tk(nhom["tk_hao"], cty), _tk(nhom["tk_cp"], cty)
	thieu = [
		n for n, v in (
			(nhom["tk_ts"], tk_ts), (nhom["tk_hao"], tk_hao), (nhom["tk_cp"], tk_cp)
		) if not v
	]
	if thieu:
		return {"k": nhom["k"], "ten": ten, "ket_qua": "thiếu tài khoản: " + ", ".join(thieu)}

	if frappe.db.exists("Asset Category", ten):
		return {"k": nhom["k"], "ten": ten, "ket_qua": "đã có"}

	d = frappe.get_doc({
		"doctype": "Asset Category",
		"asset_category_name": ten,
		"enable_cwip_accounting": 0,
		"total_number_of_depreciations": int(nhom["nam"]) * 12,
		"frequency_of_depreciation": 1,
		"accounts": [{
			"company_name": cty,
			"fixed_asset_account": tk_ts,
			"accumulated_depreciation_account": tk_hao,
			"depreciation_expense_account": tk_cp,
		}],
	})
	d.insert(ignore_permissions=True)
	return {"k": nhom["k"], "ten": ten, "ket_qua": "đã tạo"}


@frappe.whitelist()
def cai_dat(that_su=0):
	"""Lap nam nhom tai san mau. that_su=0 chi tra ve se lam gi."""
	_kiem(QUYEN_SUA, "cài đặt nhóm tài sản")
	cty = _cty()
	ra = []
	for n in NHOM_MAU:
		if not cint(that_su):
			co = frappe.db.exists("Asset Category", n["ten"])
			thieu = [
				x for x in (n["tk_ts"], n["tk_hao"], n["tk_cp"]) if not _tk(x, cty)
			]
			ra.append({
				"k": n["k"], "ten": n["ten"],
				"ket_qua": "thiếu tài khoản: " + ", ".join(thieu) if thieu
				else ("đã có" if co else "sẽ tạo"),
			})
			continue
		try:
			ra.append(_bao_dam_nhom(n, cty))
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "vagabond: lap nhom tai san loi")
			ra.append({"k": n["k"], "ten": n["ten"], "ket_qua": "lỗi: %s" % str(e)[:120]})
	return {"rows": ra, "that_su": cint(that_su)}


# ------------------------------------------------------------------ doc


def _nhom_cua(ten_nhom):
	for n in NHOM_MAU:
		if n["ten"] == ten_nhom:
			return n
	return None


@frappe.whitelist()
def danh_sach(chip=None, tu_khoa=None, nhom=None):
	_kiem(QUYEN_XEM, "xem sổ tài sản")
	cty = _cty()
	rows = frappe.get_all(
		"Asset",
		filters={"company": cty, "docstatus": ["<", 2]},
		fields=[
			"name", "asset_name", "asset_category", "gross_purchase_amount",
			"available_for_use_date", "status", "docstatus", "location",
			"custodian", "asset_quantity", "opening_accumulated_depreciation",
		],
		limit_page_length=0,
		order_by="available_for_use_date desc",
	)
	# Hao mon luy ke that: cong cac ky da ghi so.
	for r in rows:
		r["da_khau_hao"] = flt(
			frappe.db.sql(
				"""select sum(depreciation_amount) from `tabDepreciation Schedule`
				where parent in (select name from `tabAsset Depreciation Schedule`
					where asset = %s and docstatus = 1) and journal_entry is not null""",
				(r["name"],),
			)[0][0] or 0
		) + flt(r.get("opening_accumulated_depreciation"))
		r["con_lai"] = flt(r["gross_purchase_amount"]) - r["da_khau_hao"]
		n = _nhom_cua(r.get("asset_category"))
		r["icon"] = n["icon"] if n else "📦"
		r["bo_phan"] = n["bo_phan"] if n else ""
		r["la_ccdc"] = 1 if (n and n["k"] == "ccdc") else 0

	dem = {
		"dang_dung": len([r for r in rows if r["status"] in ("Submitted", "Partially Depreciated", "Fully Depreciated")]),
		"nhap": len([r for r in rows if r["docstatus"] == 0]),
		"het_khau_hao": len([r for r in rows if r["status"] == "Fully Depreciated"]),
		"da_thanh_ly": len([r for r in rows if r["status"] in ("Sold", "Scrapped")]),
	}
	tat_ca = len(rows)

	if chip == "dang_dung":
		rows = [r for r in rows if r["status"] in ("Submitted", "Partially Depreciated")]
	elif chip == "nhap":
		rows = [r for r in rows if r["docstatus"] == 0]
	elif chip == "het_khau_hao":
		rows = [r for r in rows if r["status"] == "Fully Depreciated"]
	elif chip == "da_thanh_ly":
		rows = [r for r in rows if r["status"] in ("Sold", "Scrapped")]

	if nhom:
		rows = [r for r in rows if r["asset_category"] == nhom]
	if tu_khoa:
		k = tu_khoa.strip().lower()
		rows = [
			r for r in rows
			if k in (r["asset_name"] or "").lower() or k in (r["name"] or "").lower()
		]

	return {
		"rows": rows,
		"dem": dem,
		"tat_ca": tat_ca,
		"tong_nguyen_gia": sum(flt(r["gross_purchase_amount"]) for r in rows),
		"tong_con_lai": sum(flt(r["con_lai"]) for r in rows),
		"nhom": [
			{"k": n["k"], "ten": n["ten"], "icon": n["icon"], "mo_ta": n["mo_ta"],
			 "nam": n["nam"], "bo_phan": n["bo_phan"],
			 "co_roi": 1 if frappe.db.exists("Asset Category", n["ten"]) else 0}
			for n in NHOM_MAU
		],
		"sua_duoc": 1 if _sua_duoc() else 0,
		"chua_cai_dat": 1 if not frappe.db.exists("Asset Category", NHOM_MAU[0]["ten"]) else 0,
	}


@frappe.whitelist()
def chi_tiet(ma):
	_kiem(QUYEN_XEM, "xem tài sản")
	d = frappe.db.get_value(
		"Asset", ma,
		["name", "asset_name", "asset_category", "gross_purchase_amount", "status",
		 "available_for_use_date", "purchase_date", "location", "custodian",
		 "docstatus", "opening_accumulated_depreciation", "cost_center"],
		as_dict=True,
	)
	if not d:
		frappe.throw("Không thấy tài sản %s." % ma)
	lich = frappe.db.sql(
		"""select s.schedule_date, s.depreciation_amount, s.accumulated_depreciation_amount,
			s.journal_entry
		from `tabDepreciation Schedule` s
		inner join `tabAsset Depreciation Schedule` p on p.name = s.parent
		where p.asset = %s and p.docstatus = 1
		order by s.schedule_date asc""",
		(ma,), as_dict=True,
	)
	da = sum(flt(x["depreciation_amount"]) for x in lich if x["journal_entry"])
	da += flt(d.opening_accumulated_depreciation)
	n = _nhom_cua(d.asset_category)
	return {
		"ma": d.name,
		"ten": d.asset_name,
		"nhom": d.asset_category,
		"icon": n["icon"] if n else "📦",
		"bo_phan": n["bo_phan"] if n else "",
		"la_ccdc": 1 if (n and n["k"] == "ccdc") else 0,
		"nguyen_gia": flt(d.gross_purchase_amount),
		"da_khau_hao": da,
		"con_lai": flt(d.gross_purchase_amount) - da,
		"trang_thai": d.status,
		"ngay_dung": d.available_for_use_date,
		"ngay_mua": d.purchase_date,
		"noi_de": d.location,
		"nguoi_giu": d.custodian,
		"nhap": 1 if d.docstatus == 0 else 0,
		"so_ky": len(lich),
		"so_ky_da_chay": len([x for x in lich if x["journal_entry"]]),
		"lich": [
			{
				"ngay": x["schedule_date"],
				"so_tien": flt(x["depreciation_amount"]),
				"luy_ke": flt(x["accumulated_depreciation_amount"]),
				"da_ghi": 1 if x["journal_entry"] else 0,
				"but_toan": x["journal_entry"],
			}
			for x in lich
		],
		"sua_duoc": 1 if _sua_duoc() else 0,
	}


# ------------------------------------------------------------------ ghi


@frappe.whitelist()
def khai(ten, nhom, nguyen_gia, ngay_dung, so_nam=None, noi_de=None,
         nguoi_giu=None, ngay_mua=None, da_khau_hao=0, ghi_so=1):
	"""Khai mot tai san da co san hoac vua mua.

	da_khau_hao: tai san mua truoc khi len he, da trich khau hao bao nhieu roi.
	"""
	_kiem(QUYEN_SUA, "khai tài sản")
	n = NHOM_THEO_KEY.get(nhom) or _nhom_cua(nhom)
	if not n:
		frappe.throw("Không có nhóm tài sản %s." % nhom)
	if not frappe.db.exists("Asset Category", n["ten"]):
		frappe.throw(
			"Nhóm %s chưa được lập. Vào màn Tài sản bấm Lập nhóm tài sản trước." % n["ten"]
		)
	nguyen_gia = flt(nguyen_gia)
	if nguyen_gia <= 0:
		frappe.throw("Nguyên giá phải lớn hơn 0.")
	da = flt(da_khau_hao)
	if da < 0 or da > nguyen_gia:
		frappe.throw("Đã khấu hao phải nằm trong khoảng 0 tới nguyên giá.")

	cty = _cty()
	so_thang = int(flt(so_nam or n["nam"]) * 12)
	if so_thang < 1:
		frappe.throw("Số năm sử dụng phải lớn hơn 0.")

	d = frappe.get_doc({
		"doctype": "Asset",
		"asset_name": (ten or "").strip(),
		"item_code": _bao_dam_item(n),
		"asset_category": n["ten"],
		"company": cty,
		"location": _bao_dam_location(noi_de),
		"custodian": (nguoi_giu or "").strip() or None,
		"gross_purchase_amount": nguyen_gia,
		"asset_quantity": 1,
		"purchase_date": getdate(ngay_mua or ngay_dung),
		"available_for_use_date": getdate(ngay_dung),
		"is_existing_asset": 1,
		"opening_accumulated_depreciation": da,
		"calculate_depreciation": 1,
		"finance_books": [{
			"depreciation_method": "Straight Line",
			"total_number_of_depreciations": so_thang,
			"frequency_of_depreciation": 1,
			"depreciation_start_date": getdate(ngay_dung),
			"expected_value_after_useful_life": 0,
		}],
	})
	d.flags.ignore_permissions = True
	d.insert(ignore_permissions=True)
	if cint(ghi_so):
		d.submit()
	return {
		"ok": 1,
		"ma": d.name,
		"loi_nhan": "Đã khai %s, nguyên giá %s đ, khấu hao %d tháng.%s"
		% (d.asset_name, "{:,.0f}".format(nguyen_gia), so_thang,
		   " Đã ghi sổ." if cint(ghi_so) else " Còn ở dạng nháp."),
	}


@frappe.whitelist()
def ghi_so(ma):
	_kiem(QUYEN_SUA, "ghi sổ tài sản")
	d = frappe.get_doc("Asset", ma)
	if d.docstatus != 0:
		frappe.throw("Tài sản này đã ghi sổ rồi.")
	d.submit()
	return {"ok": 1, "loi_nhan": "Đã ghi sổ %s." % d.asset_name}


@frappe.whitelist()
def xem_truoc_khau_hao(den_ngay=None):
	"""Ky nao den han ma chua ghi so. Xem truoc, khong ghi gi ca."""
	_kiem(QUYEN_XEM, "xem khấu hao")
	den = getdate(den_ngay or today())
	rows = frappe.db.sql(
		"""select a.name, a.asset_name, a.asset_category,
			s.schedule_date, s.depreciation_amount
		from `tabDepreciation Schedule` s
		inner join `tabAsset Depreciation Schedule` p on p.name = s.parent
		inner join `tabAsset` a on a.name = p.asset
		where p.docstatus = 1 and a.docstatus = 1
			and s.journal_entry is null and s.schedule_date <= %s
		order by s.schedule_date asc, a.asset_name asc""",
		(den,), as_dict=True,
	)
	gom = {}
	for r in rows:
		n = _nhom_cua(r["asset_category"])
		bp = n["bo_phan"] if n else "Khác"
		gom[bp] = gom.get(bp, 0.0) + flt(r["depreciation_amount"])
	return {
		"den_ngay": str(den),
		"so_ky": len(rows),
		"tong": sum(flt(r["depreciation_amount"]) for r in rows),
		"theo_bo_phan": [{"bo_phan": k, "so_tien": v} for k, v in sorted(gom.items())],
		"rows": [
			{
				"ma": r["name"], "ten": r["asset_name"], "nhom": r["asset_category"],
				"ngay": r["schedule_date"], "so_tien": flt(r["depreciation_amount"]),
			}
			for r in rows[:200]
		],
		"con_nua": max(0, len(rows) - 200),
		"sua_duoc": 1 if _sua_duoc() else 0,
	}


@frappe.whitelist()
def chay_khau_hao(den_ngay=None):
	"""Ghi so khau hao cho moi ky da den han tinh toi den_ngay."""
	_kiem(QUYEN_SUA, "chạy khấu hao")
	truoc = xem_truoc_khau_hao(den_ngay)
	if not truoc["so_ky"]:
		return {"ok": 1, "so_ky": 0, "tong": 0, "loi_nhan": "Không có kỳ nào tới hạn."}
	from erpnext.assets.doctype.asset.depreciation import post_depreciation_entries

	post_depreciation_entries(date=getdate(den_ngay or today()))
	frappe.db.commit()  # nosemgrep - can chot truoc khi doc lai de bao dung so
	sau = xem_truoc_khau_hao(den_ngay)
	da_chay = truoc["so_ky"] - sau["so_ky"]
	return {
		"ok": 1,
		"so_ky": da_chay,
		"con_sot": sau["so_ky"],
		"tong": truoc["tong"] - sau["tong"],
		"loi_nhan": "Đã ghi sổ khấu hao %d kỳ, tổng %s đ.%s"
		% (da_chay, "{:,.0f}".format(truoc["tong"] - sau["tong"]),
		   " Còn %d kỳ chưa chạy được, xem Error Log." % sau["so_ky"] if sau["so_ky"] else ""),
	}


@frappe.whitelist()
def so_tai_san():
	"""So tong: nguyen gia, hao mon luy ke, gia tri con lai theo nhom."""
	_kiem(QUYEN_XEM, "xem sổ tài sản")
	ds = danh_sach()
	gom = {}
	for r in ds["rows"]:
		k = r["asset_category"] or "Chưa xếp nhóm"
		g = gom.setdefault(k, {"nhom": k, "so_tai_san": 0, "nguyen_gia": 0.0,
		                       "da_khau_hao": 0.0, "con_lai": 0.0,
		                       "icon": r.get("icon") or "📦"})
		g["so_tai_san"] += 1
		g["nguyen_gia"] += flt(r["gross_purchase_amount"])
		g["da_khau_hao"] += flt(r["da_khau_hao"])
		g["con_lai"] += flt(r["con_lai"])
	rows = sorted(gom.values(), key=lambda x: -x["nguyen_gia"])
	return {
		"rows": rows,
		"tong_nguyen_gia": sum(x["nguyen_gia"] for x in rows),
		"tong_da_khau_hao": sum(x["da_khau_hao"] for x in rows),
		"tong_con_lai": sum(x["con_lai"] for x in rows),
		"so_tai_san": sum(x["so_tai_san"] for x in rows),
	}
