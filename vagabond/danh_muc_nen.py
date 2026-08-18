# -*- coding: utf-8 -*-
"""PHAN HE DANH MUC - du lieu nen cua ca he thong.

Anh Viet 18/08/2026: "de dam bao moi phan he hoat dong tron tru ma khong bi
rac du lieu, anh muon quy hoach lai toan bo du lieu nen tang".

Vi sao gom vao mot cho
----------------------
Truoc hom nay, danh muc nam rai rac: nha cung cap o phan he Thu mua, tai
khoan ke toan o Cai dat, hang khach o Cai dat, san pham thi chi co nut TAO
chu khong co cho XEM. Muon tra mot ma hang phai mo Desk.

Rac du lieu sinh ra chinh o cho do: khong ai nhin thay toan bo danh muc thi
khong ai biet no dang co bao nhieu dong trung, bao nhieu dong chet. Vi du
tra ra hom nay: doctype UOM co 203 don vi tinh, cho mot tiem banh.

Cach lam
--------
KHONG viet man hinh moi. Tang khung danh sach (A2/B3, anh Viet duyet
15/08/2026) da lo san: khai bao cot va bo loc o day, giao dien tu hien, va
bo loc chay o MAY CHU chu khong keo het ve dien thoai roi loc bang
JavaScript. Dieu do la bat buoc chu khong phai cho dep: doctype Customer
cua tiem dang co 43.220 dong.

Quyen (anh Viet chot 18/08/2026)
--------------------------------
"Phan he Danh muc chua du lieu song con, chi mo quyen Xem Sua Xoa cho role
Giam doc va System Manager. Cac role khac chi co quyen Xem o mot so danh
muc lien quan."

Moi man o day la CHI DOC - khung danh sach khong co duong ghi nao. Sua va
xoa van di qua cac man cu, moi man da co bo quyen rieng chat hon. Nen o day
chi con phai chia XEM, va chia theo dung viec that:

    XEM_CHUNG  san pham, nhom, don vi tinh, kho, cong thuc - bep va kho tra
               hang ngay, dong lai la chan viec
    XEM_MUA    nha cung cap va gia mua - gia mua la thong tin nhay cam
    XEM_KHACH  khach hang - so dien thoai khach, khong mo cho ca tiem
    XEM_TIEN   tai khoan ke toan, thue, ngan hang, phuong thuc thanh toan
"""

import frappe

from vagabond.khung import hop_dong as khai
from vagabond.quyen_phan_he import QUYEN_THU_MUA, ROLE_GIAM_DOC, ROLE_THU_MUA

QT = "System Manager"

# Danh muc dung hang ngay o moi bo phan. Dong lai la chan viec cua bep va
# kho, nen mo rong - nhung van la mot danh sach co ten, khong phai mo cho
# tat ca (khung tu choi khai bao thieu quyen).
XEM_CHUNG = {
	QT, ROLE_GIAM_DOC, ROLE_THU_MUA,
	"Stock Manager", "Stock User", "Kiểm kê viên",
	"Manufacturing Manager", "Manufacturing User", "Bếp phó",
	"Sales Manager", "Sales User",
	"Accounts Manager", "Accounts User",
	"Purchase Manager", "Purchase User",
	"Bộ phận đặt hàng",
}

# Gia mua va nha cung cap: khop voi phan he Thu mua, cong thu kho vi thu
# kho phai doi chieu gia luc nhan hang.
XEM_MUA = QUYEN_THU_MUA | {"Stock Manager"}

# Ho so khach hang co so dien thoai, khong mo cho ca tiem.
XEM_KHACH = {QT, ROLE_GIAM_DOC, "Sales Manager", "Sales User",
             "Accounts Manager", "Accounts User"}

# Tai khoan ke toan, thue, ngan hang, phuong thuc thanh toan.
XEM_TIEN = {QT, ROLE_GIAM_DOC, "Accounts Manager", "Accounts User",
            "AP Kiểm soát (FIN)"}

LOI_CHUNG = (
	"Danh mục này chưa mở cho tài khoản của bạn. Cần xem thì báo anh Việt "
	"cấp thêm chức vụ trong màn Quản lý người dùng."
)


# ===================================================================
# 1. SAN PHAM va NHOM SAN PHAM
# ===================================================================
#
# Anh Viet: "Hien tai App chi co nut tao mon. Em phai viet bo sung man hinh
# Danh sach mon, cho phep tim kiem va loc theo Nhom san pham."
#
# 1.473 mon tren he. Tran 600 va bo loc chay o may chu, khong keo het ve.

CHIP_SP = khai.chip(
	{"k": "", "ten": "Tất cả", "ic": "📦"},
	{"k": "tp", "ten": "Thành phẩm", "ic": "🎂"},
	{"k": "btp", "ten": "Bán thành phẩm", "ic": "🥣"},
	{"k": "nl", "ten": "Nguyên liệu", "ic": "🌾"},
	{"k": "khac", "ten": "Khác", "ic": "📎"},
	{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
)


def _xep_sp(r, bc=None):
	"""Mot mon thuoc nhom nao. THUAN."""
	if r.get("disabled"):
		return "ngung"
	loai = str(r.get("custom_loai_hang") or "").strip().lower()
	if "bán thành" in loai or "ban thanh" in loai:
		return "btp"
	if "thành phẩm" in loai or "thanh pham" in loai:
		return "tp"
	if "nguyên" in loai or "nguyen" in loai:
		return "nl"
	return "khac"


BANG_SP = khai.bang(
	ma="DMSP",
	ten="Danh mục sản phẩm",
	doctype="Item",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	truong=[
		"name", "item_name", "item_group", "stock_uom", "custom_loai_hang",
		"disabled", "is_stock_item", "is_sales_item", "is_purchase_item",
		"standard_rate", "modified",
	],
	cot=khai.cot(
		("name", "Mã hàng", "chu"),
		("item_name", "Tên món", "chu"),
		("_chip", "Loại", "chip"),
		("item_group", "Nhóm", "chu"),
		("stock_uom", "ĐVT kho", "chu"),
		# Cong don gia cua nhieu mon khac nhau ra mot so vo nghia.
		("standard_rate", "Giá chuẩn", "tien", True),
	),
	loc=khai.loc(
		{"k": "nhom", "nhan": "Nhóm sản phẩm", "kieu": "chon_mot", "truong": "item_group"},
		{"k": "dvt", "nhan": "Đơn vị tính", "kieu": "chon_mot", "truong": "stock_uom"},
		{"k": "tu_khoa", "nhan": "mã hàng hoặc tên món", "kieu": "tim_chu",
			"tim": ["name", "item_name"]},
	),
	chip=CHIP_SP,
	xep=_xep_sp,
	sap="item_group asc, item_name asc",
	tom_tat=[("_dong", "Số mặt hàng", "so")],
)


BANG_NHOM_SP = khai.bang(
	ma="DMNSP",
	ten="Nhóm sản phẩm",
	doctype="Item Group",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	truong=["name", "item_group_name", "parent_item_group", "is_group", "lft"],
	cot=khai.cot(
		("ten_cay", "Nhóm", "chu"),
		("parent_item_group", "Thuộc nhóm", "chu"),
		("_chip", "Loại", "chip"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên nhóm", "kieu": "tim_chu",
			"tim": ["name", "item_group_name"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🗂️"},
		{"k": "nhom", "ten": "Nhóm cha", "ic": "📁"},
		{"k": "la", "ten": "Nhóm lá", "ic": "📄"},
	),
	xep=lambda r, bc=None: "nhom" if r.get("is_group") else "la",
	them=lambda r, bc=None: {"ten_cay": _thut_cay(r, bc, "item_group_name", "parent_item_group")},
	# lft la thu tu duyet cay cua Frappe: sap theo no la ra dung thu tu cha
	# truoc con sau, khong phai tu dung lai cay o man hinh.
	sap="lft asc",
	tom_tat=[("_dong", "Số nhóm", "so")],
)


def _thut_cay(r, bc, truong_ten, truong_cha):
	"""Thut ten theo cap de bang phang doc ra hinh cay. THUAN.

	Khung danh sach la bang phang, khong ve duoc cay thu muc. Nhung sap theo
	lft roi thut dau dong theo cap thi mat van doc ra quan he cha con, ma
	khong phai dung mot man hinh rieng chi de ve cay.
	"""
	ten = str(r.get(truong_ten) or r.get("name") or "")
	cap = 0
	cha = str(r.get(truong_cha) or "")
	moc = ((bc or {}).get("cay") or {})
	da_qua = set()
	while cha and cha in moc and cha not in da_qua:
		da_qua.add(cha)
		cap += 1
		cha = moc[cha]
		if cap > 8:
			break
	return ("　" * cap) + ten


def _cay_cha(doctype, truong_cha):
	"""Dung ham truoc(): doc MOT lan ban do con -> cha cho ca tap.

	Khung cho phep truoc() cham co so du lieu, va day la cho duy nhat duoc
	phep. Mot cau hoi cho ca tap, thay vi moi dong tu di hoi.
	"""

	def _lam(dong, bc=None):
		ds = frappe.get_all(doctype, fields=["name", truong_cha], limit_page_length=0)
		return {"cay": {d["name"]: d.get(truong_cha) or "" for d in ds}}

	return _lam


BANG_NHOM_SP["truoc"] = _cay_cha("Item Group", "parent_item_group")


# ===================================================================
# 2. DON VI TINH va QUY DOI
# ===================================================================
#
# 203 don vi tinh cho mot tiem banh - dung la cho rac nhat cua danh muc.
# Mo ra nhin duoc thi moi don duoc.

BANG_DVT = khai.bang(
	ma="DMDVT",
	ten="Đơn vị tính",
	doctype="UOM",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	truong=["name", "uom_name", "must_be_whole_number", "enabled"],
	cot=khai.cot(
		("name", "Đơn vị tính", "chu"),
		("_chip", "Số lẻ", "chip"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên đơn vị tính", "kieu": "tim_chu",
			"tim": ["name", "uom_name"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "📏"},
		{"k": "nguyen", "ten": "Chỉ số nguyên", "ic": "🔢"},
		{"k": "le", "ten": "Cho số lẻ", "ic": "⚖️"},
	),
	xep=lambda r, bc=None: "nguyen" if r.get("must_be_whole_number") else "le",
	sap="name asc",
	tom_tat=[("_dong", "Số đơn vị tính", "so")],
)


BANG_QUY_DOI = khai.bang(
	ma="DMQD",
	ten="Quy đổi đơn vị tính",
	doctype="UOM Conversion Factor",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	truong=["name", "from_uom", "to_uom", "value", "category"],
	cot=khai.cot(
		("from_uom", "Từ đơn vị", "chu"),
		("to_uom", "Sang đơn vị", "chu"),
		# Cong he so quy doi lai ra mot so vo nghia.
		("value", "Hệ số", "so", True),
		("category", "Nhóm", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên đơn vị tính", "kieu": "tim_chu",
			"tim": ["from_uom", "to_uom"]},
	),
	sap="from_uom asc, to_uom asc",
	tom_tat=[("_dong", "Số cặp quy đổi", "so")],
)


# ===================================================================
# 3. KHO HANG (hien cay thu muc)
# ===================================================================

BANG_KHO = khai.bang(
	ma="DMKHO",
	ten="Kho hàng",
	doctype="Warehouse",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	truong=["name", "warehouse_name", "parent_warehouse", "is_group",
	        "disabled", "company", "lft"],
	cot=khai.cot(
		("ten_cay", "Kho", "chu"),
		("_chip", "Loại", "chip"),
		("parent_warehouse", "Thuộc kho", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên kho", "kieu": "tim_chu",
			"tim": ["name", "warehouse_name"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🏬"},
		{"k": "nhom", "ten": "Kho cha", "ic": "📁"},
		{"k": "la", "ten": "Kho chứa hàng", "ic": "📦"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: (
		"ngung" if r.get("disabled") else ("nhom" if r.get("is_group") else "la")
	),
	them=lambda r, bc=None: {
		"ten_cay": _thut_cay(r, bc, "warehouse_name", "parent_warehouse")
	},
	truoc=_cay_cha("Warehouse", "parent_warehouse"),
	sap="lft asc",
	tom_tat=[("_dong", "Số kho", "so")],
)


# ===================================================================
# 4. CONG THUC DINH MUC (BOM)
# ===================================================================
#
# Anh Viet danh dau "rat quan trong cho viec tru kho nguyen lieu". 325 cong
# thuc tren he.

BANG_BOM = khai.bang(
	ma="DMBOM",
	ten="Công thức định mức",
	doctype="BOM",
	quyen=XEM_CHUNG,
	loi_quyen=LOI_CHUNG,
	dieu_kien={"docstatus": ["<", 3]},
	truong=["name", "item", "item_name", "quantity", "uom", "is_active",
	        "is_default", "docstatus", "total_cost", "modified"],
	cot=khai.cot(
		("item_name", "Món", "chu"),
		("_chip", "Trạng thái", "chip"),
		# Cong san luong cua nhieu cong thuc khac nhau ra so vo nghia.
		("quantity", "Ra bao nhiêu", "so", True),
		("uom", "ĐVT", "chu"),
		("total_cost", "Giá thành", "tien", True),
		("name", "Mã công thức", "chu"),
	),
	loc=khai.loc(
		{"k": "mon", "nhan": "Món", "kieu": "chon_mot", "truong": "item"},
		{"k": "tu_khoa", "nhan": "mã công thức hoặc tên món", "kieu": "tim_chu",
			"tim": ["name", "item", "item_name"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🧪"},
		{"k": "mac_dinh", "ten": "Đang dùng chính", "ic": "⭐"},
		{"k": "chay", "ten": "Đang hiệu lực", "ic": "✅"},
		{"k": "nhap", "ten": "Bản nháp", "ic": "📝"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: (
		"nhap" if not r.get("docstatus")
		else "mac_dinh" if r.get("is_default")
		else "chay" if r.get("is_active")
		else "ngung"
	),
	sap="item_name asc, is_default desc",
	tom_tat=[("_dong", "Số công thức", "so")],
)


# ===================================================================
# 5. NHA CUNG CAP va NHOM
# ===================================================================

BANG_NCC = khai.bang(
	ma="DMNCC",
	ten="Nhà cung cấp",
	doctype="Supplier",
	quyen=XEM_MUA,
	loi_quyen=(
		"Danh mục nhà cung cấp chỉ mở cho Thu mua, Kế toán, Giám đốc và thủ kho."
	),
	truong=["name", "supplier_name", "supplier_group", "supplier_type",
	        "mobile_no", "disabled", "modified"],
	cot=khai.cot(
		("supplier_name", "Nhà cung cấp", "chu"),
		("_chip", "Trạng thái", "chip"),
		("supplier_group", "Nhóm", "chu"),
		("mobile_no", "Điện thoại", "chu"),
	),
	loc=khai.loc(
		{"k": "nhom", "nhan": "Nhóm nhà cung cấp", "kieu": "chon_mot",
			"truong": "supplier_group"},
		{"k": "tu_khoa", "nhan": "tên hoặc số điện thoại", "kieu": "tim_chu",
			"tim": ["name", "supplier_name", "mobile_no"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🏭"},
		{"k": "dang", "ten": "Đang dùng", "ic": "✅"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: "ngung" if r.get("disabled") else "dang",
	sap="supplier_name asc",
	tom_tat=[("_dong", "Số nhà cung cấp", "so")],
)


BANG_NHOM_NCC = khai.bang(
	ma="DMNNCC",
	ten="Nhóm nhà cung cấp",
	doctype="Supplier Group",
	quyen=XEM_MUA,
	loi_quyen=LOI_CHUNG,
	truong=["name", "supplier_group_name", "parent_supplier_group", "is_group", "lft"],
	cot=khai.cot(
		("ten_cay", "Nhóm", "chu"),
		("parent_supplier_group", "Thuộc nhóm", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên nhóm", "kieu": "tim_chu",
			"tim": ["name", "supplier_group_name"]},
	),
	them=lambda r, bc=None: {
		"ten_cay": _thut_cay(r, bc, "supplier_group_name", "parent_supplier_group")
	},
	truoc=_cay_cha("Supplier Group", "parent_supplier_group"),
	sap="lft asc",
	tom_tat=[("_dong", "Số nhóm", "so")],
)


# ===================================================================
# 6. BANG GIA MUA VAO
# ===================================================================
#
# Anh Viet: "de Thu mua so sanh gia". Chi lay bang gia MUA - gia ban khong
# lien quan, va tron hai thu vao la nguoi doc so sanh nham.

BANG_GIA_MUA = khai.bang(
	ma="DMGIA",
	ten="Bảng giá mua vào",
	doctype="Item Price",
	quyen=XEM_MUA,
	loi_quyen="Giá mua chỉ mở cho Thu mua, Kế toán, Giám đốc và thủ kho.",
	dieu_kien={"buying": 1},
	truong=["name", "item_code", "item_name", "price_list", "price_list_rate",
	        "uom", "supplier", "valid_from", "valid_upto", "modified"],
	cot=khai.cot(
		("item_name", "Món", "chu"),
		# Cong don gia cua nhieu mon ra mot so vo nghia.
		("price_list_rate", "Giá mua", "tien", True),
		("uom", "ĐVT mua", "chu"),
		("supplier", "Nhà cung cấp", "chu"),
		("price_list", "Bảng giá", "chu"),
		("valid_from", "Áp từ", "ngay"),
	),
	loc=khai.loc(
		{"k": "bang", "nhan": "Bảng giá", "kieu": "chon_mot", "truong": "price_list"},
		{"k": "ncc", "nhan": "Nhà cung cấp", "kieu": "chon_mot", "truong": "supplier"},
		{"k": "tu_khoa", "nhan": "mã hàng hoặc tên món", "kieu": "tim_chu",
			"tim": ["item_code", "item_name"]},
	),
	sap="item_name asc, price_list asc",
	tom_tat=[("_dong", "Số dòng giá", "so")],
)


# ===================================================================
# 7. KHACH HANG va NHOM (B2B / B2C)
# ===================================================================
#
# 43.220 khach hang tren he. Day chinh la man anh Viet lo "do app khi load
# hang ngan khach hang". Bo loc chay o may chu, tran 600, va man tu bao khi
# cat bot - khung lo san ca ba.

# Nhom khach cua tiem: "Khach si B2B", "Khach doanh nghiep va qua tang",
# "San giao do an" la ban buon; con lai la ban le.
NHOM_B2B = ("Khách sỉ B2B", "Khách doanh nghiệp và quà tặng", "Commercial",
            "Government", "Non Profit", "Sàn giao đồ ăn", "Nội bộ")


def _xep_khach(r, bc=None):
	"""Khach nay la B2B hay B2C. THUAN.

	Xep theo NHOM khach chu khong theo customer_type: tren he nay chi 8
	khach co customer_type, con nhom thi khach nao cung co.
	"""
	if r.get("disabled"):
		return "ngung"
	return "b2b" if str(r.get("customer_group") or "") in NHOM_B2B else "b2c"


BANG_KHACH = khai.bang(
	ma="DMKH",
	ten="Danh mục khách hàng",
	doctype="Customer",
	quyen=XEM_KHACH,
	loi_quyen="Hồ sơ khách hàng chỉ mở cho Sales, Kế toán và Giám đốc.",
	truong=["name", "customer_name", "customer_group", "customer_type",
	        "mobile_no", "disabled", "territory", "modified"],
	cot=khai.cot(
		("customer_name", "Khách hàng", "chu"),
		("_chip", "Phân loại", "chip"),
		("customer_group", "Nhóm", "chu"),
		("mobile_no", "Điện thoại", "chu"),
	),
	loc=khai.loc(
		{"k": "nhom", "nhan": "Nhóm khách hàng", "kieu": "chon_mot",
			"truong": "customer_group"},
		{"k": "tu_khoa", "nhan": "tên khách hoặc số điện thoại", "kieu": "tim_chu",
			"tim": ["name", "customer_name", "mobile_no"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "👥"},
		{"k": "b2b", "ten": "Khách sỉ B2B", "ic": "🏢"},
		{"k": "b2c", "ten": "Khách lẻ B2C", "ic": "🧍"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=_xep_khach,
	sap="modified desc",
	tom_tat=[("_dong", "Số khách hàng", "so")],
)


BANG_NHOM_KHACH = khai.bang(
	ma="DMNKH",
	ten="Nhóm khách hàng",
	doctype="Customer Group",
	quyen=XEM_KHACH,
	loi_quyen=LOI_CHUNG,
	truong=["name", "customer_group_name", "parent_customer_group", "is_group", "lft"],
	cot=khai.cot(
		("ten_cay", "Nhóm", "chu"),
		("parent_customer_group", "Thuộc nhóm", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên nhóm", "kieu": "tim_chu",
			"tim": ["name", "customer_group_name"]},
	),
	them=lambda r, bc=None: {
		"ten_cay": _thut_cay(r, bc, "customer_group_name", "parent_customer_group")
	},
	truoc=_cay_cha("Customer Group", "parent_customer_group"),
	sap="lft asc",
	tom_tat=[("_dong", "Số nhóm", "so")],
)


# ===================================================================
# 8. NAM DANH MUC THAM CHIEU HE THONG
# ===================================================================

BANG_PT_THANH_TOAN = khai.bang(
	ma="DMPT",
	ten="Phương thức thanh toán",
	doctype="Mode of Payment",
	quyen=XEM_TIEN,
	loi_quyen="Danh mục này chỉ mở cho Kế toán và Giám đốc.",
	truong=["name", "mode_of_payment", "type", "enabled"],
	cot=khai.cot(
		("name", "Phương thức", "chu"),
		("_chip", "Trạng thái", "chip"),
		("type", "Kiểu", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên phương thức", "kieu": "tim_chu",
			"tim": ["name", "mode_of_payment"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "💳"},
		{"k": "dang", "ten": "Đang dùng", "ic": "✅"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: "dang" if r.get("enabled") else "ngung",
	sap="name asc",
	tom_tat=[("_dong", "Số phương thức", "so")],
)


# Danh muc ngan hang NAPAS 581 dong, nap tu vagabond/ngan_hang.py vao
# doctype Bank chuan. Dung chung voi luong xuat tep MB Biz.
BANG_NGAN_HANG = khai.bang(
	ma="DMNH",
	ten="Danh mục ngân hàng",
	doctype="Bank",
	quyen=XEM_TIEN | XEM_MUA,
	loi_quyen=LOI_CHUNG,
	truong=["name", "bank_name", "swift_number", "modified"],
	cot=khai.cot(
		("bank_name", "Ngân hàng", "chu"),
		("swift_number", "Mã SWIFT", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên hoặc mã ngân hàng", "kieu": "tim_chu",
			"tim": ["name", "bank_name", "swift_number"]},
	),
	sap="bank_name asc",
	tom_tat=[("_dong", "Số ngân hàng", "so")],
)


# Anh Viet: "Chart of Accounts - Chi hien thi cac tai khoan hay dung: 111,
# 112, 1411...". 270 tai khoan tren he ma tiem chi dung chung 20 cai, nen
# chip HAY DUNG dat lam mac dinh, con lai van tra duoc bang chip Tat ca.
TK_HAY_DUNG = (
	"111", "112", "131", "1388", "1411", "133", "331", "3331", "3388",
	"511", "515", "632", "641", "642", "156", "152", "155", "153",
)


def _xep_tk(r, bc=None):
	"""Tai khoan nay thuoc nhom nao. THUAN."""
	so = str(r.get("account_number") or "").strip()
	if not so:
		so = str(r.get("name") or "").split(" - ")[0].strip()
	if r.get("is_group"):
		return "nhom"
	if so.startswith("111") or so.startswith("112"):
		return "tien"
	if so.startswith("131") or so.startswith("331") or so.startswith("14") or so.startswith("33"):
		return "cong_no"
	if so.startswith("5"):
		return "doanh_thu"
	if so.startswith("6"):
		return "chi_phi"
	if so.startswith("15") or so.startswith("152") or so.startswith("156"):
		return "kho"
	return "khac"


BANG_TAI_KHOAN = khai.bang(
	ma="DMTK",
	ten="Tài khoản kế toán",
	doctype="Account",
	quyen=XEM_TIEN,
	loi_quyen="Hệ thống tài khoản chỉ mở cho Kế toán và Giám đốc.",
	truong=["name", "account_name", "account_number", "account_type",
	        "root_type", "is_group", "disabled", "parent_account", "lft"],
	cot=khai.cot(
		("account_number", "Số hiệu", "chu"),
		("ten_cay", "Tên tài khoản", "chu"),
		("_chip", "Nhóm", "chip"),
		("root_type", "Loại", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "số hiệu hoặc tên tài khoản", "kieu": "tim_chu",
			"tim": ["name", "account_name", "account_number"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🧮"},
		{"k": "tien", "ten": "Tiền mặt, ngân hàng", "ic": "💵"},
		{"k": "cong_no", "ten": "Công nợ, tạm ứng", "ic": "🤝"},
		{"k": "kho", "ten": "Hàng tồn kho", "ic": "📦"},
		{"k": "doanh_thu", "ten": "Doanh thu", "ic": "📈"},
		{"k": "chi_phi", "ten": "Chi phí", "ic": "📉"},
		{"k": "nhom", "ten": "Tài khoản cha", "ic": "📁"},
		{"k": "khac", "ten": "Khác", "ic": "📎"},
	),
	xep=_xep_tk,
	them=lambda r, bc=None: {"ten_cay": _thut_cay(r, bc, "account_name", "parent_account")},
	truoc=_cay_cha("Account", "parent_account"),
	sap="lft asc",
	tom_tat=[("_dong", "Số tài khoản", "so")],
)


BANG_THUE = khai.bang(
	ma="DMTHUE",
	ten="Danh mục thuế bán ra",
	doctype="Sales Taxes and Charges Template",
	quyen=XEM_TIEN,
	loi_quyen="Cấu hình thuế chỉ mở cho Kế toán và Giám đốc.",
	truong=["name", "title", "is_default", "disabled", "company", "modified"],
	cot=khai.cot(
		("title", "Mẫu thuế", "chu"),
		("_chip", "Trạng thái", "chip"),
		("company", "Công ty", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên mẫu thuế", "kieu": "tim_chu",
			"tim": ["name", "title"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🧾"},
		{"k": "mac_dinh", "ten": "Đang dùng mặc định", "ic": "⭐"},
		{"k": "dang", "ten": "Đang dùng", "ic": "✅"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: (
		"ngung" if r.get("disabled")
		else "mac_dinh" if r.get("is_default")
		else "dang"
	),
	sap="title asc",
	tom_tat=[("_dong", "Số mẫu thuế", "so")],
)


BANG_THUE_MUA = khai.bang(
	ma="DMTHUEM",
	ten="Danh mục thuế mua vào",
	doctype="Purchase Taxes and Charges Template",
	quyen=XEM_TIEN | XEM_MUA,
	loi_quyen="Cấu hình thuế chỉ mở cho Kế toán, Thu mua và Giám đốc.",
	truong=["name", "title", "is_default", "disabled", "company", "modified"],
	cot=khai.cot(
		("title", "Mẫu thuế", "chu"),
		("_chip", "Trạng thái", "chip"),
		("company", "Công ty", "chu"),
	),
	loc=khai.loc(
		{"k": "tu_khoa", "nhan": "tên mẫu thuế", "kieu": "tim_chu",
			"tim": ["name", "title"]},
	),
	chip=khai.chip(
		{"k": "", "ten": "Tất cả", "ic": "🧾"},
		{"k": "mac_dinh", "ten": "Đang dùng mặc định", "ic": "⭐"},
		{"k": "dang", "ten": "Đang dùng", "ic": "✅"},
		{"k": "ngung", "ten": "Ngừng dùng", "ic": "🚫"},
	),
	xep=lambda r, bc=None: (
		"ngung" if r.get("disabled")
		else "mac_dinh" if r.get("is_default")
		else "dang"
	),
	sap="title asc",
	tom_tat=[("_dong", "Số mẫu thuế", "so")],
)


# Danh sach cac man cua phan he, de app dung menu va de bo kiem doi chieu.
# Thu tu o day la thu tu hien tren app.
CAC_BANG = (
	BANG_SP, BANG_NHOM_SP, BANG_DVT, BANG_QUY_DOI, BANG_KHO, BANG_BOM,
	BANG_NCC, BANG_NHOM_NCC, BANG_GIA_MUA, BANG_KHACH, BANG_NHOM_KHACH,
	BANG_PT_THANH_TOAN, BANG_NGAN_HANG, BANG_TAI_KHOAN, BANG_THUE,
	BANG_THUE_MUA,
)
