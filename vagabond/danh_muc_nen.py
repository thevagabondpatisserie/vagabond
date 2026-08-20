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

Quyen - SIET LAI 21/08/2026
---------------------------
Anh Viet 18/08/2026 mo tuong doi rong: "cac role khac chi co quyen Xem o mot
so danh muc lien quan". Ba ngay sau anh siet han lai:

    "Danh muc la Nguon su that duy nhat. Chi nhung tai khoan so huu Role la
    Ke toan, Thu mua va Giam doc moi duoc phep nhin thay phan he Danh muc
    nay tren man hinh chinh cua App va co quyen thao tac them/sua du lieu.
    Cac Role khac (Sales, Kho, Bep...) tuyet doi khong duoc nhin thay menu
    nay de tranh tinh trang rac du lieu."

Nen mot CONG DUY NHAT: VAO_DANH_MUC. Moi bang trong tep nay deu phai giao
voi tap do, khong bang nao duoc mo rong hon. Cac tap XEM_* ben duoi chi con
lam viec CHIA NHO trong pham vi da siet, chu khong con mo them ai.

Cai gia phai tra, noi thang cho anh Viet biet
---------------------------------------------
Bep va kho MAT duong tra ma hang, don vi tinh, kho va cong thuc tren man
Danh muc. Ho van chon duoc mon trong luc lap phieu (o chon mon di duong
khac, khong qua tep nay), nhung khong con man tra cuu rieng.

Do la doi lay dieu anh Viet muon: khong ai ngoai ba vai do cham vao du lieu
nen. Neu sau nay bep keu thi mo lai o XEM_CHUNG - mot dong sua, va khi do la
mot quyet dinh co y chu khong phai mot cho so hut.

Ba tap chia nho trong pham vi da siet:

    XEM_CHUNG  san pham, nhom, don vi tinh, kho, cong thuc
    XEM_MUA    nha cung cap va gia mua - gia mua la thong tin nhay cam
    XEM_KHACH  khach hang - so dien thoai khach
    XEM_TIEN   tai khoan ke toan, thue, ngan hang, phuong thuc thanh toan

Quyen TAO MOI (21/08/2026)
--------------------------
Anh Viet: "Xay dung Form nhap lieu (Form View) tuong ung... toi uu voi giao
dien Mobile App". Duong tao nam o khung danh sach (khung/ds.py), khai bang
ham khai.tao() ngay trong tung bang duoi day, va chan bang tap SUA_DM - hep
hon ca VAO_DANH_MUC vi xem mot danh muc khac han voi de ra mot dong moi
trong do.

BA danh muc CO Y khong co nut Tao moi
-------------------------------------
Cong thuc dinh muc (BOM), Thue ban ra va Thue mua vao. Ca ba deu khong dung
duoc neu chi dien mot form phang: BOM phai co luoi nguyen lieu, hai mau thue
phai co luoi dong thue. Bay ra mot nut Tao moi roi ghi xuong mot ban ghi
thieu luoi con la de ra dung cai rac du lieu anh Viet dang muon chan.

Cong thuc thi da co man rieng trong luong san xuat. Hai mau thue mot nam khai
mot lan, van khai tren Desk.
"""

import frappe

from vagabond.khung import hop_dong as khai
from vagabond.quyen_phan_he import QUYEN_THU_MUA, ROLE_GIAM_DOC, ROLE_THU_MUA

QT = "System Manager"

# ==================================================== CONG DUY NHAT
#
# Ke toan, Thu mua, Giam doc. Ten vai lay tu site that, khong bia: Uyen giu
# "AP Officer", chi Dung giu "AP Kiem soat (FIN)", anh Viet va De giu
# "AP Giam doc". Hai vai ERPNext (Accounts/Purchase) giu lai de khong ai
# dang lam viec bi mat quyen giua chung.
#
# "Bo phan dat hang" CO Y khong nam trong day. Vai do gan nhu ai cung co -
# Hieu baker, Han bep pho, Uyen Duyen sales, De, Kien thu kho deu co - nen
# de no vao la mo lai dung cai cua anh Viet vua dong.
VAI_KE_TOAN_DM = {"AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User"}
VAI_THU_MUA_DM = {ROLE_THU_MUA, "AP Officer", "Purchase Manager", "Purchase User"}
VAI_GIAM_DOC_DM = {ROLE_GIAM_DOC, "AP Giám đốc", QT}

VAO_DANH_MUC = VAI_KE_TOAN_DM | VAI_THU_MUA_DM | VAI_GIAM_DOC_DM


def _siet(*tap):
	"""Giao voi VAO_DANH_MUC. Khong bang nao duoc rong hon cong.

	Vi sao la mot HAM chu khong phai viet tay phep giao o tung cho: viet tay
	thi hom nao them mot bang moi la quen mot lan, va quen o day nghia la
	Sales lai nhin thay danh muc. Ham nay khong quen duoc.
	"""
	ra = set()
	for t in tap:
		ra |= set(t)
	return ra & VAO_DANH_MUC


# Danh muc dung hang ngay. Truoc 21/08 mo cho ca bep, kho va sales; nay
# siet ve trong cong.
XEM_CHUNG = _siet(
	VAO_DANH_MUC,
)

# Gia mua va nha cung cap. Ca ba nhom trong cong deu can: thu mua khai gia,
# ke toan doi chieu hoa don mua, giam doc duyet.
#
# QUYEN_THU_MUA cua quyen_phan_he.py CO Y duoc gop vao day chu khong dung mot
# minh: tap do viet bang ten vai ERPNext (Purchase User, Accounts Manager) va
# thieu han ba vai THAT dang chay tren site - Uyen giu "AP Officer", chi Dung
# giu "AP Kiem soat (FIN)", anh Viet va De giu "AP Giam doc". Dung mot minh
# tap cu thi dung ba nguoi lam viec do hang ngay bi khoa ra ngoai.
XEM_MUA = _siet(VAO_DANH_MUC, QUYEN_THU_MUA, {"Stock Manager"})

# Ho so khach hang co so dien thoai cua khach. Sales tung co phan, nay bi cong
# siet ra ngoai. Trong cong thi van chia tiep: THU MUA khong can danh ba khach,
# nen khong mo. Chia nho o day khong phai de kho nhau, ma vi so dien thoai
# khach la thu duy nhat trong ca phan he Danh muc thuoc ve NGUOI NGOAI cong ty.
XEM_KHACH = _siet(VAI_KE_TOAN_DM, VAI_GIAM_DOC_DM)

# Tai khoan ke toan, thue, ngan hang, phuong thuc thanh toan. Ke toan va giam
# doc. Thu mua khong mo: sua he thong tai khoan la sua so sach ca cong ty.
#
# Viet bang VAI_* chu khong liet ke tay: ban cu liet ke tay va SOT "AP Giam
# doc", tuc la anh Viet va De - hai nguoi duy nhat le ra phai thay het - lai
# khong vao duoc. Bo kiem khai bao cua khung bat duoc ngay hom nay.
XEM_TIEN = _siet(VAI_KE_TOAN_DM, VAI_GIAM_DOC_DM)

# ==================================================== QUYEN TAO MOI
#
# Hep hon quyen XEM. Xem mot danh muc va de ra mot dong moi trong do la hai
# viec khac han: rac du lieu sinh ra o ve thu hai chu khong phai ve thu nhat.
#
# Ke toan va Thu mua tao duoc danh muc thuoc viec cua ho, Giam doc tao duoc
# tat ca. Chia nho o tung bang ben duoi bang tham so quyen_tao.
SUA_DM = VAO_DANH_MUC
SUA_TIEN = _siet(VAI_KE_TOAN_DM, VAI_GIAM_DOC_DM)
SUA_MUA = _siet(VAI_THU_MUA_DM, VAI_KE_TOAN_DM, VAI_GIAM_DOC_DM)
SUA_KHACH = XEM_KHACH

LOI_CHUNG = (
	"Phân hệ Danh mục chỉ mở cho Kế toán, Thu mua và Giám đốc, vì đây là dữ "
	"liệu nền của cả hệ thống. Cần xem thì báo anh Việt cấp thêm chức vụ "
	"trong màn Quản lý người dùng."
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
	tao=khai.tao(
		nhan="Tạo mặt hàng mới",
		quyen=SUA_DM,
		# Đi tới màn Danh mục sản phẩm đã có: màn đó tự đặt mã theo nhóm và
		# cảnh báo trùng tên, form chung ở đây không biết làm hai việc ấy.
		di_toi="CDSP",
	),
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
	tao=khai.tao(
		nhan="Tạo nhóm sản phẩm",
		quyen=SUA_DM,
		o=[
			khai.o("item_group_name", "Tên nhóm", "chu", bat_buoc=1,
			       goi_y="Ví dụ: Bánh mì, Nguyên liệu khô"),
			khai.o("parent_item_group", "Thuộc nhóm cha", "lien_ket",
			       doctype="Item Group", loc={"is_group": 1}, bat_buoc=1,
			       mo_ta="Cây nhóm hàng phải có gốc. Chưa rõ thì chọn nhóm tổng."),
			khai.o("is_group", "Là nhóm cha, chứa nhóm con", "co"),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo đơn vị tính",
		quyen=SUA_DM,
		ghi_chu=(
			"Hệ đang có hơn 200 đơn vị tính cho một tiệm bánh. Tra kỹ danh sách "
			"trước khi thêm: mỗi đơn vị trùng nghĩa là một chỗ tồn kho chia đôi."
		),
		o=[
			khai.o("uom_name", "Tên đơn vị", "chu", bat_buoc=1, goi_y="Ví dụ: Khay, Vỉ"),
			khai.o("must_be_whole_number", "Chỉ nhận số nguyên", "co",
			       mo_ta="Bật cho cái, hộp, khay. Tắt cho kg, lít."),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo quy đổi đơn vị",
		quyen=SUA_DM,
		o=[
			khai.o("from_uom", "Từ đơn vị", "lien_ket", doctype="UOM", bat_buoc=1),
			khai.o("to_uom", "Sang đơn vị", "lien_ket", doctype="UOM", bat_buoc=1),
			khai.o("value", "Hệ số quy đổi", "so", bat_buoc=1,
			       mo_ta="Một đơn vị ở trên bằng bao nhiêu đơn vị ở dưới. Ví dụ 1 kg bằng 1000 gram thì điền 1000."),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo kho hàng",
		quyen=SUA_DM,
		o=[
			khai.o("warehouse_name", "Tên kho", "chu", bat_buoc=1),
			khai.o("parent_warehouse", "Thuộc kho cha", "lien_ket",
			       doctype="Warehouse", loc={"is_group": 1}, bat_buoc=1),
			khai.o("is_group", "Là kho cha, chứa kho con", "co",
			       mo_ta="Kho cha không chứa hàng, chỉ để gom. Hàng chỉ nằm ở kho con."),
		],
	),
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
	# Nut Tao moi dan sang man RIENG (NCCTAO) chu khong dung form chung.
	#
	# Vi sao: form chung chi ghi duoc cac truong nam tren chinh bang
	# Supplier. Ma ho so mot nha cung cap nam o BON bang - dia chi o
	# Address, email o Contact, so tai khoan o Bank Account. Uyen tao bang
	# form chung ngay 21/08/2026 thi ra mot cai ten trong danh sach, den luc
	# gui don mua hang moi phat hien khong co email de gui.
	tao=khai.tao(
		nhan="Tạo nhà cung cấp",
		quyen=SUA_MUA,
		di_toi="NCCTAO",
	),
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
	tao=khai.tao(
		nhan="Tạo nhóm nhà cung cấp",
		quyen=SUA_MUA,
		o=[
			khai.o("supplier_group_name", "Tên nhóm", "chu", bat_buoc=1),
			khai.o("parent_supplier_group", "Thuộc nhóm cha", "lien_ket",
			       doctype="Supplier Group", loc={"is_group": 1}, bat_buoc=1),
			khai.o("is_group", "Là nhóm cha", "co"),
		],
	),
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
	tao=khai.tao(
		nhan="Khai giá mua vào",
		quyen=SUA_MUA,
		ghi_chu=(
			"Giá khai ở đây là giá máy gợi ý lúc lập đơn mua. Nó KHÔNG tự sửa "
			"giá trên đơn đã lập."
		),
		o=[
			khai.o("item_code", "Mặt hàng", "lien_ket", doctype="Item", bat_buoc=1),
			khai.o("price_list", "Bảng giá", "lien_ket", doctype="Price List",
			       loc={"buying": 1}, bat_buoc=1),
			khai.o("supplier", "Nhà cung cấp", "lien_ket", doctype="Supplier",
			       mo_ta="Để trống là giá chung, không riêng nhà nào."),
			khai.o("uom", "Đơn vị tính", "lien_ket", doctype="UOM"),
			khai.o("price_list_rate", "Đơn giá", "tien", bat_buoc=1),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo khách hàng",
		quyen=SUA_KHACH,
		ghi_chu="Mã khách máy tự đặt theo nhóm (KL, SI, DN, SA, NB), không phải điền.",
		o=[
			khai.o("customer_name", "Tên khách", "chu", bat_buoc=1),
			khai.o("customer_group", "Nhóm khách", "lien_ket",
			       doctype="Customer Group", bat_buoc=1),
			khai.o("customer_type", "Loại", "chon",
			       chon=[("Company", "Công ty"), ("Individual", "Cá nhân")],
			       mac_dinh="Individual"),
			khai.o("tax_id", "Mã số thuế", "chu"),
			khai.o("mobile_no", "Số điện thoại", "chu"),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo nhóm khách hàng",
		quyen=SUA_KHACH,
		o=[
			khai.o("customer_group_name", "Tên nhóm", "chu", bat_buoc=1),
			khai.o("parent_customer_group", "Thuộc nhóm cha", "lien_ket",
			       doctype="Customer Group", loc={"is_group": 1}, bat_buoc=1),
			khai.o("is_group", "Là nhóm cha", "co"),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo phương thức thanh toán",
		quyen=SUA_TIEN,
		ghi_chu=(
			"Khai xong nhớ vào màn Phương thức thanh toán ở Cài đặt gán mã gửi "
			"cơ quan thuế và tài khoản ghi sổ, không thì phương thức này chưa "
			"dùng được ngoài quầy."
		),
		o=[
			khai.o("mode_of_payment", "Tên phương thức", "chu", bat_buoc=1),
			khai.o("type", "Loại", "chon",
			       chon=[("Cash", "Tiền mặt"), ("Bank", "Ngân hàng"),
			             ("General", "Khác"), ("Phone", "Ví điện thoại")],
			       mac_dinh="Bank"),
			khai.o("enabled", "Đang dùng", "co", mac_dinh=1),
		],
	),
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
	tao=khai.tao(
		nhan="Tạo ngân hàng",
		quyen=SUA_TIEN,
		ghi_chu=(
			"Danh mục này đã có 581 ngân hàng NAPAS. Tra kỹ trước khi thêm, "
			"gần như chắc chắn ngân hàng cần dùng đã có sẵn."
		),
		o=[
			khai.o("bank_name", "Tên ngân hàng", "chu", bat_buoc=1),
			khai.o("swift_number", "Mã SWIFT hoặc BIN", "chu"),
		],
	),
)


# Anh Viet: "Chart of Accounts - Chi hien thi cac tai khoan hay dung: 111,
# 112, 1411...". 270 tai khoan tren he ma tiem chi dung chung 20 cai, nen
# chip HAY DUNG dat lam mac dinh, con lai van tra duoc bang chip Tat ca.
TK_HAY_DUNG = (
	"111", "112", "131", "1388", "1411", "133", "331", "3331", "3388",
	"511", "515", "632", "641", "642", "156", "152", "155", "153",
)


def _tach_so_tk(r):
	"""Tach so hieu va ten that cua mot tai khoan. THUAN.

	Nghiem thu v213 tren site that bat duoc: trong 270 tai khoan thi phan
	lon co truong account_number RONG, so hieu bi go dinh vao dau ten, vi du
	account_name la "1111 - Tien Viet Nam". Cot So hieu vi vay hien trong
	trang mot mang.

	Do la rac du lieu that, se don rieng. Nhung man Danh muc phai doc duoc
	ca hai kieu ghi chu khong duoc de cot trong, nen o day tach tay: uu tien
	account_number, khong co thi lay cum so o dau ten, va bo cum so do khoi
	ten de khong hien lap hai lan.
	"""
	so = str(r.get("account_number") or "").strip()
	ten = str(r.get("account_name") or "").strip()
	if not ten:
		ten = str(r.get("name") or "").strip()
	dau = ten.split(" - ")[0].strip()
	la_so = bool(dau) and dau.replace(".", "").isdigit()
	if la_so:
		if not so:
			so = dau
		if dau == so:
			con = ten[len(dau):].lstrip(" -").strip()
			if con:
				ten = con
	if not so:
		dau2 = str(r.get("name") or "").split(" - ")[0].strip()
		if dau2 and dau2.replace(".", "").isdigit():
			so = dau2
	return so, ten


def _them_tk(r, bc=None):
	"""So hieu va ten da thut theo cap. THUAN."""
	so, ten = _tach_so_tk(r)
	ban = dict(r)
	ban["account_name"] = ten
	return {
		"so_hieu": so,
		"ten_cay": _thut_cay(ban, bc, "account_name", "parent_account"),
	}


def _xep_tk(r, bc=None):
	"""Tai khoan nay thuoc nhom nao. THUAN."""
	so = _tach_so_tk(r)[0]
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
		("so_hieu", "Số hiệu", "chu"),
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
	them=_them_tk,
	truoc=_cay_cha("Account", "parent_account"),
	sap="lft asc",
	tom_tat=[("_dong", "Số tài khoản", "so")],
	tao=khai.tao(
		nhan="Tạo tài khoản kế toán",
		quyen=SUA_TIEN,
		ghi_chu=(
			"Thêm một tài khoản là sửa hệ thống tài khoản của cả công ty. Chỉ "
			"thêm khi chị Dung đã chốt số hiệu và tài khoản cha."
		),
		o=[
			khai.o("account_name", "Tên tài khoản", "chu", bat_buoc=1),
			khai.o("account_number", "Số hiệu", "chu", bat_buoc=1,
			       goi_y="Ví dụ 1311"),
			khai.o("parent_account", "Thuộc tài khoản cha", "lien_ket",
			       doctype="Account", loc={"is_group": 1}, bat_buoc=1,
			       mo_ta="Loại và tính chất tài khoản kế thừa từ tài khoản cha."),
			khai.o("is_group", "Là tài khoản tổng hợp", "co"),
		],
	),
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
