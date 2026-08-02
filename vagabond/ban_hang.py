"""Ban hang: doanh so ngay tu Pancake thanh Hoa don ban hang (Sales Invoice).

Chot voi anh Viet 01/08/2026:
- MOI don Pancake giao THANH CONG trong ngay (status 3 da nhan, 16 da thu tien,
  loc theo ngay giao estimate_delivery_date) thanh MOT Sales Invoice nhap.
- GIAI DOAN 1 KHONG cap nhat kho (update_stock = 0), chi ghi doanh thu.
- Loan Anh ra soat tren man "Doanh so ngay" cua app /bep roi bam Chot,
  may submit ca loat.
- Don co yeu cau hoa don cong ty (Vagabond Hoa Don) day sang m-invoice
  o che do CHO KY (InvoiceApi78/Save), ke toan ky tay giai doan dau.

LUAT KE TOAN HIEN HANH (anh Viet chot 02/08/2026): MOI don hang phai tuong
ung MOT hoa don VAT. TUYET DOI KHONG gop nhieu don thanh mot hoa don, ke ca
gop cuoi ngay. Vi vay moi Sales Invoice mang san thong tin nguoi mua rieng
cua no o bon truong vgb_xhd_ten / vgb_xhd_mst / vgb_xhd_dia_chi /
vgb_xhd_email, khong dung chung mot ban ghi nguoi mua cho nhieu don.

Chong trung: SI mang custom_pancake_id (id noi bo cua Pancake). Dong bo
chay lai bao nhieu lan cung chi co mot hoa don cho mot don.
"""

import json
import re
import unicodedata

import frappe
import requests
from frappe.utils import flt, getdate, now_datetime, nowdate

from vagabond.kiem_banh import _keo_don, _khoang_unix
from vagabond.lib import TIMEOUT, cache_get, cache_set, cfg, key

# Trang thai Pancake tinh vao doanh so: 3 da nhan, 16 da thu tien.
TT_DOANH_SO = {3, 16}

KHACH_LE = "Khách lẻ Online"
# DVBH00001 la item "Phí Dịch Vụ Vận Chuyển" co san ben Next (bo ma chuan).
MA_PHI_GIAO = "DVBH00001"

QUYEN_BAN_HANG = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}


def _kiem_quyen():
	if not QUYEN_BAN_HANG & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền ghi nhận doanh số.")


def _cong_ty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _khach_le():
	"""Khach le online dung chung. Ten that cua khach nam o remarks tung hoa don."""
	if frappe.db.exists("Customer", KHACH_LE):
		return KHACH_LE
	nhom = (
		frappe.db.get_single_value("Selling Settings", "customer_group")
		or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	)
	vung = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value(
		"Territory", {"is_group": 0}, "name"
	)
	kh = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": KHACH_LE,
			"customer_type": "Individual",
			"customer_group": nhom,
			"territory": vung,
		}
	)
	kh.insert(ignore_permissions=True)
	return kh.name


def _item_phi_giao():
	"""Item dich vu phi giao hang thu cua khach - khong ton kho."""
	if frappe.db.exists("Item", MA_PHI_GIAO):
		return MA_PHI_GIAO
	nhom = None
	for ung_vien in ("Dịch vụ", "Services"):
		if frappe.db.exists("Item Group", ung_vien):
			nhom = ung_vien
			break
	if not nhom:
		nhom = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	it = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": MA_PHI_GIAO,
			"item_name": "Phí giao hàng",
			"item_group": nhom,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_purchase_item": 0,
		}
	)
	it.insert(ignore_permissions=True)
	return it.name


def _dong_hang(o):
	"""Dich items cua don Pancake sang dong hoa don. Tra (rows, thieu_ma)."""
	rows, thieu = [], []
	for it in o.get("items") or []:
		vi = it.get("variation_info") or {}
		ma = str(vi.get("display_id") or "").strip()
		sl = flt(it.get("quantity") or 0)
		if not sl:
			continue
		if ma and not frappe.db.exists("Item", ma):
			# Pancake tu sinh hau to size cho mau ma (vd BAWC00115S16CM,
			# BAWC00127MINI12CM); thu bo hau to de khop ma goc ben Next.
			goc = re.sub(r"(MINI|[SML])\d{1,2}CM$", "", ma, flags=re.IGNORECASE)
			if goc != ma and frappe.db.exists("Item", goc):
				ma = goc
		if not ma or not frappe.db.exists("Item", ma):
			# Nhieu san pham Pancake bi dat ma "1"/"2": thu khop dung ten mon
			# voi item_name ben Next (khong phan biet hoa thuong).
			ten = (vi.get("name") or it.get("product_name") or "").strip()
			ma_theo_ten = frappe.db.get_value("Item", {"item_name": ten}, "name") if ten else None
			if ma_theo_ten:
				ma = ma_theo_ten
			else:
				thieu.append("%s (%s)" % (ma or "(trống)", ten or "?"))
				continue
		gia = flt(vi.get("retail_price") or 0)
		giam = flt(it.get("discount_each_product") or 0)
		rows.append(
			{
				"item_code": ma,
				"qty": sl,
				"rate": max(gia - giam, 0),
			}
		)
	phi_giao = flt(o.get("shipping_fee") or 0)
	if phi_giao > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": phi_giao})
	return rows, thieu


# Bill ca the: Payoo va ShinhanBank deu in "So tham chieu" (12 chu so) va
# "Ma chuan chi" (6 ky tu chu + so, vi du F62221). Bill KHONG co ma vach nen
# sales phai go tay - nhan ca hai dang de sales go cai nao ngan hon cung duoc,
# den luc doi soat thi do ca hai cot (anh Viet gui bill mau 02/08/2026).
MAU_BILL = r"^[A-Z0-9]{4,20}$"
LOI_BILL = (
	"Nhập Số tham chiếu (chỉ chữ số, ví dụ 621416783893) hoặc Mã chuẩn chi "
	"(chữ và số, ví dụ F62221) in trên bill cà thẻ."
)


# ------------------------------------------------ ma tham chieu doi soat
# Moi phuong thuc thanh toan bam vao mot chung tu khac nhau. Bat sales ghi
# dung ma nay NGAY LUC chot don thi doi soat tu dong sau nay khop duoc TUNG
# giao dich thay vi chi so tong ngay (anh Viet chot 02/08/2026).
# bat = 1 nghia la thieu ma thi KHONG cho ghi so.
PT_THAM_CHIEU = {
	"Tiền mặt": {"lg": "/files/pt-tienmat.png"},
	"Chuyển khoản": {
		"lg": "/files/pt-mb.png",
		"nhan": "Nội dung chuyển khoản (SePay tự khớp, để trống cũng được)",
	},
	"OnePay": {
		"lg": "/files/pt-onepay.png",
		"nhan": "Order Reference của OnePay",
		"vd": "PL_VAGABOND_260801143012",
	},
	"Thẻ - Payoo": {
		"lg": "/files/pt-payoo5.png",
		"bat": 1,
		"nhan": "Số tham chiếu trên bill cà thẻ Payoo",
		"vd": "249853",
		"mau": MAU_BILL,
		"loi": LOI_BILL,
	},
	"Thẻ - ShinhanBank": {
		"lg": "/files/pt-shinhan5.png",
		"bat": 1,
		"nhan": "Số tham chiếu hoặc mã chuẩn chi trên bill ShinhanBank",
		"vd": "621416783893 hoặc F62221",
		"mau": MAU_BILL,
		"loi": LOI_BILL,
	},
	"GrabFood": {
		"lg": "/files/pt-grab.png",
		"bat": 1,
		"nhan": "Mã đơn GrabFood",
		"vd": "GF-689",
		"mau": r"^GF-\d{1,10}$",
		"loi": "Mã đơn GrabFood có dạng GF- rồi tới số, ví dụ GF-689.",
	},
	"BeFood": {
		"lg": "/files/pt-befood.png",
		"bat": 1,
		"nhan": "Mã đơn BeFood (8 số)",
		"vd": "76481763",
		"mau": r"^\d{8}$",
		"loi": "Mã đơn BeFood gồm đúng 8 chữ số, ví dụ 76481763.",
	},
	"GreenSM Food": {
		"lg": "/files/pt-greensm.png",
		"bat": 1,
		"nhan": "Mã đơn GreenSM",
		"vd": "XSM-3621",
		"mau": r"^XSM-[A-Z0-9]{1,12}$",
		"loi": "Mã đơn GreenSM có dạng XSM- rồi tới mã, ví dụ XSM-3621.",
	},
	"ShopeeFood": {
		"lg": "/files/pt-shopee3.png",
		"bat": 1,
		"nhan": "Mã đơn ShopeeFood (4 số)",
		"vd": "3621",
		"mau": r"^\d{4}$",
		"loi": "Mã đơn ShopeeFood gồm đúng 4 chữ số, ví dụ 3621.",
	},
}

# Pancake KHONG co cac phuong thuc cua san, an di cho sales khoi chon nham
# (anh Viet 02/08). Don san la don NHAP TAY, moi san chi mot phuong thuc.
PT_QUAY = ["Tiền mặt", "Chuyển khoản", "Thẻ - Payoo", "Thẻ - ShinhanBank", "OnePay"]
PT_PANCAKE = ["Tiền mặt", "Chuyển khoản", "OnePay", "Thẻ - Payoo", "Thẻ - ShinhanBank"]

NGUON_DON = [
	{"v": "GrabFood", "lg": "/files/pt-grab.png", "pt": ["GrabFood"]},
	{"v": "BeFood", "lg": "/files/pt-befood.png", "pt": ["BeFood"]},
	{"v": "GreenSM Food", "lg": "/files/pt-greensm.png", "pt": ["GreenSM Food"]},
	{"v": "ShopeeFood", "lg": "/files/pt-shopee3.png", "pt": ["ShopeeFood"]},
	{"v": "Khách sỉ", "ic": "🏢", "pt": ["Chuyển khoản", "Tiền mặt"]},
	{"v": "Tại chỗ - Nguyễn Văn Trỗi", "ic": "🏬", "pt": PT_QUAY},
	{"v": "Tại chỗ - Trần Cao Vân", "ic": "🏬", "pt": PT_QUAY},
]

# Ten nguon cu tren cac hoa don da nhap truoc 02/08, giu de doc lai duoc.
NGUON_CU = {"Grab": "GrabFood", "Grab Online": "GrabFood", "Be": "BeFood", "GreenSM": "GreenSM Food"}


def _pt_cho_nguon(nguon):
	"""Danh sach phuong thuc thanh toan hop le cua mot nguon don."""
	nguon = NGUON_CU.get((nguon or "").strip(), (nguon or "").strip())
	if not nguon or nguon == "Pancake":
		return list(PT_PANCAKE)
	for n in NGUON_DON:
		if n["v"] == nguon:
			return list(n["pt"])
	return list(PT_QUAY)


def _chuan_ma_tham_chieu(pt, ma, bat_buoc=True):
	"""Chuan hoa va kiem ma tham chieu theo phuong thuc thanh toan.

	Sales go "689" cho GrabFood hay "#3621" cho ShopeeFood deu duoc, may tu
	them tien to va bo dau #. Sai dang thi bao ngay tai cho chu khong de
	den luc doi soat moi phat hien.
	"""
	q = PT_THAM_CHIEU.get((pt or "").strip()) or {}
	ma = re.sub(r"\s+", "", (ma or "").strip()).lstrip("#").upper()
	if ma and pt == "GrabFood" and re.match(r"^\d{1,10}$", ma):
		ma = "GF-" + ma
	if ma and pt == "GreenSM Food" and re.match(r"^[A-Z0-9]{1,12}$", ma) and not ma.startswith("XSM"):
		ma = "XSM-" + ma
	if not ma:
		if q.get("bat") and bat_buoc:
			frappe.throw(
				"Phương thức %s bắt buộc phải có: %s%s"
				% (pt, q.get("nhan") or "mã tham chiếu", (" (ví dụ %s)" % q["vd"]) if q.get("vd") else "")
			)
		return ""
	mau = q.get("mau")
	if mau and not re.match(mau, ma):
		frappe.throw(q.get("loi") or ("Mã tham chiếu %s không đúng dạng." % ma))
	return ma


def _kiem_trung_ma(pt, ma, bo_qua=None):
	"""Hai don khong the mang cung mot ma tham chieu.

	Sales hay copy so bill cua don truoc, hoac go nham mot chu so. Bat ngay
	luc ghi so thi doi soat khong bi hai don doi mot giao dich.
	"""
	if not ma or not pt:
		return
	loc = {
		"vgb_ma_tham_chieu": ma,
		"vgb_pt_thanh_toan": pt,
		"docstatus": ["<", 2],
	}
	if bo_qua:
		loc["name"] = ["!=", bo_qua]
	cu = frappe.db.get_value("Sales Invoice", loc, ["name", "custom_pancake_display_id"], as_dict=True)
	if cu:
		frappe.throw(
			"Mã tham chiếu %s của %s đã dùng cho đơn %s rồi. Kiểm lại bill, "
			"hai đơn không thể chung một mã." % (ma, pt, cu.custom_pancake_display_id or cu.name)
		)


def _kiem_pt(pt, nguon):
	pt = (pt or "").strip()
	if not pt:
		return ""
	if pt not in PT_THAM_CHIEU:
		frappe.throw("Không có phương thức thanh toán %s." % pt)
	hop_le = _pt_cho_nguon(nguon)
	if pt not in hop_le:
		frappe.throw(
			"Đơn nguồn %s không dùng phương thức %s. Chọn trong: %s."
			% (nguon or "Pancake", pt, ", ".join(hop_le))
		)
	if not frappe.db.exists("Mode of Payment", pt):
		frappe.throw("Chưa khai phương thức thanh toán %s bên Next." % pt)
	return pt


@frappe.whitelist()
def cau_hinh_ban_hang():
	"""Nguon don, phuong thuc thanh toan, quy tac ma tham chieu cho app /bep.

	App KHONG hardcode danh sach nua - sua o day la ca app doi theo.
	"""
	_kiem_quyen()
	pt = []
	for ten, q in PT_THAM_CHIEU.items():
		pt.append(
			{
				"v": ten,
				"lg": q.get("lg") or "",
				"bat": 1 if q.get("bat") else 0,
				"nhan": q.get("nhan") or "Mã tham chiếu",
				"vd": q.get("vd") or "",
			}
		)
	return {"pt": pt, "nguon": NGUON_DON, "pt_pancake": PT_PANCAKE}


PT_KENH = (
	("cash", "Tiền mặt", "tiền mặt"),
	("transfer_money", "Chuyển khoản", "chuyển khoản"),
	("charged_by_onepay", "OnePay", "OnePay"),
	("charged_by_card", "", "cà thẻ (chọn máy Payoo/Shinhan)"),
	("charged_by_momo", "", "Momo"),
	("charged_by_vnpay", "", "VNPay"),
	("charged_by_qrpay", "", "QR Pay"),
)


def _vnd(so):
	return "{:,.0f}".format(so).replace(",", ".")


def _doan_thanh_toan(o):
	"""Doan phuong thuc thanh toan tu cac o tien cua don Pancake.

	Tra (pt, ghi_chu). pt rong = chua ro, sales chon tay o man doanh thu
	truoc khi ghi so. Ca the (charged_by_card) khong phan biet duoc may
	Payoo hay ShinhanBank nen khong tu dien - so tien van vao ghi chu de
	ke toan doi soat (anh Viet chot 02/08).
	"""
	thay = []
	pt_ro = []
	mo_ho = 0
	for truong, ten_pt, nhan in PT_KENH:
		try:
			so = float(o.get(truong) or 0)
		except (TypeError, ValueError):
			so = 0
		if so <= 0:
			continue
		thay.append("%s %s" % (nhan, _vnd(so)))
		if ten_pt:
			if ten_pt not in pt_ro:
				pt_ro.append(ten_pt)
		else:
			mo_ho += 1
	try:
		tra_truoc = float(o.get("prepaid") or 0)
	except (TypeError, ValueError):
		tra_truoc = 0
	if tra_truoc > 0 and not thay:
		thay.append("trả trước %s (chưa rõ kênh)" % _vnd(tra_truoc))
	pt = pt_ro[0] if (len(pt_ro) == 1 and not mo_ho) else ""
	ghi = ("Pancake: " + " + ".join(thay)) if thay else ""
	return pt, ghi


# ------------------------------------------- nguoi mua tren hoa don VAT
# Mac dinh khi khach khong yeu cau xuat cho phap nhan.
XHD_MAC_DINH = "Bán cho người tiêu dùng"

# So 10 chu so cua VN vua co the la ma so thue vua co the la SO DIEN THOAI
# (ca hai deu bat dau bang 0). Chi nhan la MST khi dung sau mot tu khoa hoa
# don, VA tra cong thong tin thue ra dung mot doanh nghiep.
RE_MOC_MST = re.compile(
	r"(?:mst|ma so thue|tax code|xuat hoa don|xuat hd|xhd|hoa don vat|hoa don do|vat)"
	r"[^0-9]{0,40}(\d{10}(?:[-\s]?\d{3})?)"
)
# Luoi an toan: khi don DA nhac chuyen hoa don ma so khong dung ngay sau tu
# khoa, quet moi so 10/13 chu so va chi nhan so nao tra cong thong tin thue
# ra dung mot doanh nghiep. So dien thoai khong tra ra doanh nghiep nen rot.
RE_MOI_SO = re.compile(r"(?<!\d)(\d{10}(?:[-\s]?\d{3})?)(?!\d)")
# So sanh tren text DA BO DAU (_bo_dau) nen chi can ban khong dau.
TU_KHOA_XHD = ("xuat hoa don", "xuat hd", "xhd", "ma so thue", "mst", "hoa don vat", "hoa don do")

# Email nhan hoa don dien tu. Tra cong thong tin thue KHONG bao gio tra ra
# email, nen cho nao khach tu ghi email trong ghi chu don thi phai nhat lay -
# khong thi ke toan lai go tay tung don (don 91145 ngay 02/08).
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# Email cua chinh minh: khach dan lai mail cua shop trong ghi chu thi bo qua,
# gui hoa don ve chinh minh la vo nghia.
MIEN_CUA_MINH = ("thevagabondpatisserie.com",)


def _text_don(o):
	"""Gom moi cho khach co the ghi yeu cau xuat hoa don trong don Pancake."""
	phan = [o.get("note") or "", o.get("note_print") or ""]
	for t in o.get("tags") or []:
		phan.append((t.get("name") or "") if isinstance(t, dict) else str(t))
	for k in ("bill_full_name", "customer_note", "extra_note"):
		if o.get(k):
			phan.append(str(o.get(k)))
	return "\n".join(p for p in phan if p)


def _bo_dau(t):
	"""Bo dau tieng Viet va ha thuong. Giu nguyen do dai tung ky tu."""
	t = unicodedata.normalize("NFD", t or "")
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("\u0111", "d").replace("\u0110", "d").lower()


def _so_hop_le(m):
	so = re.sub(r"\D", "", m or "")
	return so if len(so) in (10, 13) else ""


def _tach_mst(txt):
	"""Tim ma so thue trong text.

	Tra DANH SACH so dung sau tu khoa hoa don (MST, ma so thue, xuat hoa
	don...), theo thu tu xuat hien. Khong quet bua moi so 10 chu so vi so dien
	thoai khach cung 10 chu so va cung bat dau bang 0 - tung bat nham
	0989937939 cua don 91060 (02/08). Nguoi goi con phai tra cong thong tin
	thue de chac chan la doanh nghiep.
	"""
	ra = []
	for m in RE_MOC_MST.finditer(_bo_dau(txt)):
		so = _so_hop_le(m.group(1))
		if so and so not in ra:
			ra.append(so)
	return ra


def _tach_email(txt):
	"""Email dau tien khach ghi trong don. Bo email cua chinh shop.

	Khach thuong go kem kieu "xuat hoa don cong ty ..., mail nhan hoa don
	ketoan@abc.vn". Chuoi email hay dinh dau cau nen phai got dau cuoi.
	"""
	for m in RE_EMAIL.finditer(txt or ""):
		e = m.group(0).strip(" .,;:)]}>").lower()
		if not e:
			continue
		if any(e.endswith("@" + d) or e.endswith("." + d) for d in MIEN_CUA_MINH):
			continue
		return e
	return ""


def _thong_tin_xhd(o, did):
	"""Bon truong nguoi mua cho mot don.

	Uu tien 1: ban ghi Vagabond Hoa Don (khach da dien tren portal dat hang).
	Uu tien 2: MST doc duoc trong ghi chu / the cua don Pancake, tra cong
	           thong tin thue de tu dien ten cong ty va dia chi.
	Neu khach co nhac xuat hoa don ma khong ghi MST thi de TRONG de sales
	buoc phai dien tay, khong am tham ghi "nguoi tieu dung".
	"""
	txt = _text_don(o)
	mail = _tach_email(txt)

	hd = frappe.db.get_value(
		"Vagabond Hoa Don",
		{"ma_don": did},
		["ma_so_thue", "ten_cong_ty", "dia_chi", "email"],
		as_dict=True,
	)
	if hd and (hd.ten_cong_ty or hd.ma_so_thue):
		return {
			"vgb_xhd_ten": hd.ten_cong_ty or "",
			"vgb_xhd_mst": re.sub(r"\D", "", hd.ma_so_thue or ""),
			"vgb_xhd_dia_chi": hd.dia_chi or "",
			"vgb_xhd_email": hd.email or mail,
		}

	low = _bo_dau(txt)
	co_nhac = any(t in low for t in TU_KHOA_XHD)
	ung_vien = _tach_mst(txt)
	if co_nhac:
		# Luoi an toan: so khong dung ngay sau tu khoa van xet, nhung phai qua
		# duoc cua tra cong thong tin thue moi duoc nhan.
		for m in RE_MOI_SO.finditer(low):
			so = _so_hop_le(m.group(1))
			if so and so not in ung_vien:
				ung_vien.append(so)

	for mst in ung_vien:
		tt = {}
		try:
			from vagabond.api import tra_mst

			tt = tra_mst(mst) or {}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: tra MST %s" % mst)
		if tt.get("ok") and tt.get("ten"):
			return {
				"vgb_xhd_ten": tt.get("ten"),
				"vgb_xhd_mst": mst,
				"vgb_xhd_dia_chi": tt.get("dia_chi") or "",
				"vgb_xhd_email": mail,
			}

	if ung_vien or co_nhac:
		# Khach co nhac hoa don nhung khong ra duoc doanh nghiep nao (hay gap
		# nhat: so do la so dien thoai). De TRONG de sales buoc phai dien tay,
		# nhung email nhat duoc thi van dien san cho do mat cong.
		return {"vgb_xhd_ten": "", "vgb_xhd_mst": "", "vgb_xhd_dia_chi": "", "vgb_xhd_email": mail}

	return {"vgb_xhd_ten": XHD_MAC_DINH, "vgb_xhd_mst": "", "vgb_xhd_dia_chi": "", "vgb_xhd_email": ""}


def _upsert_hoa_don(o, ngay, cong_ty, khach):
	"""Mot don Pancake = mot Sales Invoice nhap. Tra (trang_thai, ghi_chu)."""
	pid = str(o.get("id") or "")
	did = str(o.get("display_id") or o.get("id") or "")
	cu = frappe.db.get_value(
		"Sales Invoice", {"custom_pancake_id": pid}, ["name", "docstatus"], as_dict=True
	)
	if cu and cu.docstatus == 1:
		return "da_chot", cu.name
	if cu and cu.docstatus == 2:
		return "da_huy_si", cu.name

	rows, thieu = _dong_hang(o)
	if thieu:
		return "thieu_ma", "Đơn %s thiếu mã: %s" % (did, ", ".join(sorted(set(thieu))))
	if not rows:
		return "rong", did

	ten_khach = (o.get("bill_full_name") or "").strip()
	sdt = (o.get("bill_phone_number") or "").strip()
	giam_don = flt(o.get("total_discount") or o.get("discount") or 0)

	if cu:
		si = frappe.get_doc("Sales Invoice", cu.name)
		si.items = []
	else:
		si = frappe.new_doc("Sales Invoice")

	si.update(
		{
			"company": cong_ty,
			"customer": khach,
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": did,
			"custom_nguon": "Pancake",
			"apply_discount_on": "Grand Total",
			"discount_amount": giam_don,
			"remarks": "Pancake #%s - %s%s" % (did, ten_khach or "Khách lẻ", " - " + sdt if sdt else ""),
		}
	)
	pt_tt, ghi_tt = _doan_thanh_toan(o)
	if pt_tt and frappe.db.exists("Mode of Payment", pt_tt):
		si.vgb_pt_thanh_toan = pt_tt
	if ghi_tt:
		si.vgb_ghi_chu_doi_soat = ghi_tt
	# Nguoi mua tren hoa don VAT. Dong bo chay lai KHONG duoc de len thong tin
	# sales da sua tay: chi dien khi o dang trong hoac dang la gia tri mac dinh.
	cu_ten = (si.get("vgb_xhd_ten") or "").strip()
	if not cu_ten or cu_ten == XHD_MAC_DINH:
		for truong, gt in _thong_tin_xhd(o, did).items():
			si.set(truong, gt)
	elif not (si.get("vgb_xhd_email") or "").strip():
		# Ten nguoi mua da co (sales sua tay hoac lan dong bo truoc tra cong
		# thong tin thue ra) nhung con thieu moi email - chi bu rieng o email,
		# khong dung den ba truong kia.
		mail = _tach_email(_text_don(o))
		if mail:
			si.vgb_xhd_email = mail
	for r in rows:
		si.append("items", r)
	si.flags.ignore_permissions = True
	si.save()
	return ("tao_moi" if not cu else "cap_nhat"), si.name


@frappe.whitelist()
def dong_bo_doanh_so(ngay=None):
	"""Keo don Pancake giao thanh cong cua mot ngay ve thanh SI nhap."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	dau, cuoi = _khoang_unix(ngay)
	dons = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	dons = [o for o in dons if o.get("status") in TT_DOANH_SO]

	cong_ty = _cong_ty()
	khach = _khach_le()
	kq = {"tao_moi": 0, "cap_nhat": 0, "da_chot": 0, "loi": []}
	for o in dons:
		try:
			tt, ghi_chu = _upsert_hoa_don(o, ngay, cong_ty, khach)
			if tt in ("tao_moi", "cap_nhat", "da_chot"):
				kq[tt] += 1
			elif tt == "thieu_ma":
				kq["loi"].append(ghi_chu)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: don %s" % o.get("display_id"))
			kq["loi"].append("Đơn %s lỗi khi tạo, xem Error Log." % o.get("display_id"))
	frappe.db.commit()
	cache_set("bh_loi_%s" % ngay, json.dumps(kq["loi"]), 6 * 3600)
	cache_set("bh_luc_%s" % ngay, str(now_datetime())[:16], 6 * 3600)
	kq["so_don_pancake"] = len(dons)
	return kq


@frappe.whitelist()
def bang_doanh_so(ngay=None):
	"""Du lieu cho man 'Doanh so ngay' cua app /bep."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	sis = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay, "custom_pancake_id": ["!=", ""]},
		fields=[
			"name",
			"docstatus",
			"grand_total",
			"remarks",
			"custom_pancake_display_id",
			"custom_hddt_trang_thai",
			"custom_hddt_so",
			"custom_nguon",
			"vgb_pt_thanh_toan",
			"vgb_ma_tham_chieu",
			"vgb_ghi_chu_doi_soat",
			"vgb_xhd_ten",
			"vgb_xhd_mst",
			"vgb_xhd_dia_chi",
			"vgb_xhd_email",
		],
		order_by="custom_pancake_display_id",
	)
	loi = json.loads(cache_get("bh_loi_%s" % ngay) or "[]")
	hd_cty = {
		r.ma_don: r
		for r in frappe.db.get_all(
			"Vagabond Hoa Don",
			fields=["ma_don", "ten_cong_ty", "tinh_trang"],
			filters={"ma_don": ["in", [s.custom_pancake_display_id for s in sis] or [""]]},
		)
	}
	for s in sis:
		s["can_hddt"] = 1 if s.custom_pancake_display_id in hd_cty else 0
	return {
		"ngay": str(ngay),
		"dong_bo_luc": cache_get("bh_luc_%s" % ngay) or "",
		"rows": sis,
		"loi": loi,
		"tong_nhap": sum(s.grand_total for s in sis if s.docstatus == 0),
		"tong_chot": sum(s.grand_total for s in sis if s.docstatus == 1),
	}


@frappe.whitelist()
def chot_doanh_so(ngay=None):
	"""Submit ca loat SI nhap cua ngay. Loan Anh bam sau khi ra soat."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	ds = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay, "custom_pancake_id": ["!=", ""], "docstatus": 0},
		pluck="name",
	)
	xong, loi = 0, []
	for ten in ds:
		si = frappe.get_doc("Sales Invoice", ten)
		nhan = si.custom_pancake_display_id or si.name
		try:
			_chuan_bi_ghi_so(si)
		except frappe.ValidationError as e:
			# Thieu phuong thuc hay ma tham chieu: bao ro don nao, khong ghi so.
			frappe.local.message_log = []
			loi.append("Đơn %s: %s" % (nhan, str(e)))
			continue
		try:
			si.flags.ignore_permissions = True
			si.submit()
			xong += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang chot: %s" % ten)
			loi.append("Đơn %s ghi sổ lỗi, xem Error Log." % nhan)
	frappe.db.commit()
	return {"da_chot": xong, "loi": loi}


def dong_bo_doanh_so_tu_dong():
	"""Cron: tu keo doanh so hom nay, sales chi viec ra soat cuoi ngay."""
	try:
		frappe.set_user("Administrator")
		dong_bo_doanh_so(nowdate())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang cron")


@frappe.whitelist()
def luu_thanh_toan(si_name, pt=None, ma_tham_chieu=None):
	"""Sales luu phuong thuc thanh toan + ma tham chieu, chua ghi so."""
	_kiem_quyen()
	si = frappe.db.get_value(
		"Sales Invoice", si_name, ["name", "custom_nguon", "docstatus"], as_dict=True
	)
	if not si:
		frappe.throw("Không có hoá đơn %s." % si_name)
	pt = _kiem_pt(pt, si.custom_nguon)
	# Luu nhap thi chua bat buoc, den luc ghi so moi bat.
	ma = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
	frappe.db.set_value(
		"Sales Invoice", si_name, {"vgb_pt_thanh_toan": pt, "vgb_ma_tham_chieu": ma}
	)
	frappe.db.commit()
	return {"ok": 1, "pt": pt, "ma_tham_chieu": ma}


def _chuan_bi_ghi_so(si):
	"""Kiem cac dieu kien bat buoc truoc khi submit mot hoa don sales."""
	pt = _kiem_pt(si.vgb_pt_thanh_toan, si.custom_nguon)
	if not pt:
		frappe.throw(
			"Đơn %s chưa chọn phương thức thanh toán."
			% (si.custom_pancake_display_id or si.name)
		)
	si.vgb_pt_thanh_toan = pt
	si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, si.vgb_ma_tham_chieu)
	_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
	if not (si.vgb_xhd_ten or "").strip():
		si.vgb_xhd_ten = XHD_MAC_DINH


@frappe.whitelist()
def chot_mot_don(si_name, pt=None, ma_tham_chieu=None):
	"""Submit mot don le, sales ra soat xong don nao chot don do."""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	if not si.custom_pancake_id:
		frappe.throw("Phiếu này không phải doanh thu sales.")
	if si.docstatus != 0:
		frappe.throw("Đơn này đã chốt rồi.")
	if pt:
		si.vgb_pt_thanh_toan = pt
	if ma_tham_chieu is not None:
		si.vgb_ma_tham_chieu = ma_tham_chieu
	_chuan_bi_ghi_so(si)
	si.flags.ignore_permissions = True
	si.submit()
	frappe.db.commit()
	return {"ok": 1, "name": si.name}


@frappe.whitelist()
def luu_xhd(si_name, ten=None, mst=None, dia_chi=None, email=None):
	"""Sales sua thong tin nguoi mua tren hoa don VAT.

	Sua duoc ca khi don da ghi so, mien la CHUA day sang m-invoice - vi
	moi don la mot hoa don rieng, sai thong tin nguoi mua thi phai sua trong
	don do chu khong the gop sang don khac.
	"""
	_kiem_quyen()
	si = frappe.db.get_value(
		"Sales Invoice", si_name, ["name", "custom_hddt_so"], as_dict=True
	)
	if not si:
		frappe.throw("Không có hoá đơn %s." % si_name)
	if si.custom_hddt_so:
		frappe.throw(
			"Đơn này đã xuất hoá đơn điện tử số %s nên không sửa được nữa." % si.custom_hddt_so
		)
	so_mst = re.sub(r"\D", "", mst or "")
	if so_mst and len(so_mst) not in (10, 13):
		frappe.throw("Mã số thuế phải 10 hoặc 13 số.")
	ten = (ten or "").strip()
	if so_mst and not ten:
		frappe.throw("Có mã số thuế thì phải có tên pháp nhân.")
	gt = {
		"vgb_xhd_ten": ten or XHD_MAC_DINH,
		"vgb_xhd_mst": so_mst,
		"vgb_xhd_dia_chi": (dia_chi or "").strip(),
		"vgb_xhd_email": (email or "").strip(),
	}
	frappe.db.set_value("Sales Invoice", si_name, gt)
	frappe.db.commit()
	gt["ok"] = 1
	return gt


@frappe.whitelist()
def bu_email_xhd(ngay=None):
	"""Bu email nhan hoa don cho cac don DA dong bo ve ma con trong email.

	Dot dong bo dau (truoc 02/08/2026) khong nhat email trong ghi chu don nen
	nhung don kieu 91145 ve day du ten - MST - dia chi ma trong moi o email.
	Ham nay keo lai don Pancake cua ngay do va chi ghi DUNG o email, khong
	dung den ba truong con lai de khong de len thong tin sales sua tay.

	Chay lai bao nhieu lan cung duoc: don nao co email roi thi bo qua.
	"""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	ds = frappe.get_all(
		"Sales Invoice",
		filters={
			"posting_date": str(ngay),
			"custom_nguon": "Pancake",
			"docstatus": ["<", 2],
			"vgb_xhd_email": ["in", ["", None]],
		},
		fields=["name", "custom_pancake_id", "custom_hddt_so"],
	)
	if not ds:
		return {"xet": 0, "bu": 0, "ngay": str(ngay)}

	c = cfg()
	k = key(c, "pancake_api_key")
	dau, cuoi = _khoang_unix(str(ngay))
	theo_id = {}
	for o in _keo_don(c, k, "estimate_delivery_date", dau, cuoi):
		theo_id[str(o.get("id"))] = o

	bu = 0
	danh_sach = []
	for si in ds:
		if si.custom_hddt_so:
			continue  # da xuat hoa don dien tu roi thi khong dong vao nua
		o = theo_id.get(str(si.custom_pancake_id or ""))
		if not o:
			continue
		mail = _tach_email(_text_don(o))
		if not mail:
			continue
		frappe.db.set_value("Sales Invoice", si.name, "vgb_xhd_email", mail)
		bu += 1
		danh_sach.append(si.name)
	frappe.db.commit()
	return {"xet": len(ds), "bu": bu, "ngay": str(ngay), "don": danh_sach}


@frappe.whitelist()
def tao_don_tay(
	ngay=None,
	nguon="GrabFood",
	ma_don="",
	ten_khach="",
	dien_thoai="",
	items=None,
	giam_gia=0,
	phi_ship=0,
	pt=None,
	ma_tham_chieu=None,
):
	"""Nhap tay doanh thu tu kenh khong co API.

	Nguon don: 4 san (GrabFood, BeFood, GreenSM Food, ShopeeFood), Khach si,
	Tai cho tung chi nhanh. San co Giam gia (chiet khau san) nen nhan
	giam_gia rieng, tru vao Grand Total giong giam gia don Pancake.

	Don san: ma don ben app CHINH LA ma tham chieu doi soat, chi nhap mot lan.
	Don quay: sales chon phuong thuc rieng roi nhap so tham chieu bill.
	"""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	if isinstance(items, str):
		items = json.loads(items or "[]")
	rows = []
	for r in items or []:
		ma = (r.get("item_code") or "").strip()
		if not ma or not frappe.db.exists("Item", ma):
			frappe.throw("Không có mã hàng %s trong hệ thống." % (ma or "(trống)"))
		sl = flt(r.get("qty") or 0)
		if sl <= 0:
			frappe.throw("Số lượng của %s phải lớn hơn 0." % ma)
		rows.append({"item_code": ma, "qty": sl, "rate": flt(r.get("rate") or 0)})
	if not rows:
		frappe.throw("Đơn chưa có món nào.")
	if flt(phi_ship) > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": flt(phi_ship)})
	nguon = NGUON_CU.get((nguon or "").strip(), (nguon or "").strip())
	if nguon not in [n["v"] for n in NGUON_DON]:
		frappe.throw("Nguồn đơn %s không có trong danh mục." % (nguon or "(trống)"))
	hop_le = _pt_cho_nguon(nguon)
	# San chi mot phuong thuc, may tu chon cho sales khoi bam thua.
	pt = _kiem_pt(pt or (hop_le[0] if len(hop_le) == 1 else ""), nguon)
	if not pt:
		frappe.throw("Chưa chọn phương thức thanh toán cho đơn %s." % nguon)
	ma_don = (ma_don or "").strip()
	if len(hop_le) == 1:
		# Don san: ma don ben app chinh la ma tham chieu.
		ma_tc = _chuan_ma_tham_chieu(pt, ma_tham_chieu or ma_don)
		ma_don = ma_tc
	else:
		ma_tc = _chuan_ma_tham_chieu(pt, ma_tham_chieu)
	_kiem_trung_ma(pt, ma_tc)
	ma_nguon = re.sub(r"[^A-Z0-9]", "", _bo_dau(nguon).upper())[:14] or "KHAC"
	pid = "%s-%s" % (ma_nguon, ma_don or ma_tc or frappe.generate_hash(length=8))
	if frappe.db.exists("Sales Invoice", {"custom_pancake_id": pid}):
		frappe.throw("Mã đơn %s của %s đã nhập rồi, không nhập trùng." % (ma_don or ma_tc, nguon))
	si = frappe.new_doc("Sales Invoice")
	si.update(
		{
			"company": _cong_ty(),
			"customer": _khach_le(),
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": ma_don,
			"custom_nguon": nguon,
			"vgb_pt_thanh_toan": pt,
			"vgb_ma_tham_chieu": ma_tc,
			"vgb_xhd_ten": XHD_MAC_DINH,
			"apply_discount_on": "Grand Total",
			"discount_amount": flt(giam_gia),
			"remarks": "%s #%s - %s%s"
			% (nguon, ma_don or "?", (ten_khach or "Khách lẻ").strip(), " - " + dien_thoai.strip() if (dien_thoai or "").strip() else ""),
		}
	)
	for r in rows:
		si.append("items", r)
	si.flags.ignore_permissions = True
	si.save()
	frappe.db.commit()
	return {"name": si.name, "grand_total": si.grand_total}


# ---------------------------------------------------------------- m-invoice

def _minvoice_login(c):
	host = (c.minvoice_host or "").strip().rstrip("/")
	if not host:
		frappe.throw("Chưa điền host m-invoice trong Vagabond Settings.")
	if not host.startswith("http"):
		host = "https://" + host
	mk = key(c, "minvoice_password")
	r = requests.post(
		host + "/api/Account/Login",
		json={
			"username": (c.minvoice_username or "").strip(),
			"password": mk,
			"ma_dvcs": (c.minvoice_ma_dvcs or "VP").strip(),
		},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	j = r.json() or {}
	if not j.get("ok"):
		frappe.throw("m-invoice từ chối đăng nhập: %s" % j.get("message"))
	return host, j.get("token")


# Ma phuong thuc thanh toan m-invoice chap nhan. Cac kenh khac (the, vi, san)
# deu la tien ve tai khoan nen ghi CK.
PTTT_MINVOICE = {
	"Tiền mặt": "TM",
	"Chuyển khoản": "CK",
	"OnePay": "CK",
	"Thẻ - Payoo": "CK",
	"Thẻ - ShinhanBank": "CK",
	"GrabFood": "CK",
	"BeFood": "CK",
	"GreenSM Food": "CK",
	"ShopeeFood": "CK",
}


def _tach_thue(gross, ts):
	"""Gia Pancake da gom VAT. Tach nguoc: (chua_thue, tien_thue)."""
	chua = round(gross / (1 + ts / 100.0))
	return chua, round(gross - chua)


@frappe.whitelist()
def xuat_hoa_don_dien_tu(si_name):
	"""Day mot SI sang m-invoice o trang thai CHO KY. Khong ky tu dong."""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	if si.docstatus != 1:
		frappe.throw("Hoá đơn %s chưa chốt, chốt doanh số trước rồi mới xuất HĐĐT." % si_name)
	if si.custom_hddt_so:
		frappe.throw("Hoá đơn %s đã xuất HĐĐT số %s rồi." % (si_name, si.custom_hddt_so))

	hd = frappe.db.get_value(
		"Vagabond Hoa Don",
		{"ma_don": si.custom_pancake_display_id},
		["ma_so_thue", "ten_cong_ty", "dia_chi", "email"],
		as_dict=True,
	)
	# Nguoi mua lay tu chinh hoa don nay. Mot don = mot hoa don VAT, khong gop.
	ten_mua = (si.vgb_xhd_ten or "").strip()
	mst_mua = re.sub(r"\D", "", si.vgb_xhd_mst or "")
	dc_mua = (si.vgb_xhd_dia_chi or "").strip()
	em_mua = (si.vgb_xhd_email or "").strip()
	if not ten_mua and hd:
		# Hoa don cu tao truoc khi co bon truong nay
		ten_mua = (hd.ten_cong_ty or "").strip()
		mst_mua = re.sub(r"\D", "", hd.ma_so_thue or "")
		dc_mua = (hd.dia_chi or "").strip()
		em_mua = (hd.email or "").strip()
	if not ten_mua:
		frappe.throw(
			"Đơn %s chưa có tên khách xuất hoá đơn. Mở đơn ở màn Doanh số, "
			"điền khối Hoá đơn điện tử rồi xuất lại." % si_name
		)
	la_phap_nhan = bool(mst_mua)

	c = cfg()
	ts = flt(c.minvoice_ma_thue or 8)
	host, token = _minvoice_login(c)

	dong, t_chua, t_thue = [], 0, 0
	for i, r in enumerate(si.items, 1):
		gross = flt(r.amount)
		chua, thue = _tach_thue(gross, ts)
		t_chua += chua
		t_thue += thue
		dong.append(
			{
				"tchat": 1,
				"stt_rec0": i,
				"inv_itemCode": r.item_code,
				"inv_itemName": r.item_name,
				"inv_unitCode": r.uom or "Cái",
				"inv_quantity": flt(r.qty),
				"inv_unitPrice": round(chua / flt(r.qty)) if r.qty else chua,
				"inv_discountPercentage": 0,
				"inv_discountAmount": 0,
				"inv_TotalAmountWithoutVat": chua,
				"ma_thue": ts,
				"inv_vatAmount": thue,
				"inv_TotalAmount": chua + thue,
			}
		)

	than = {
		"editmode": 1,
		"data": [
			{
				"inv_invoiceSeries": (c.minvoice_series or "").strip(),
				"inv_invoiceIssuedDate": str(si.posting_date),
				"inv_currencyCode": "VND",
				"inv_exchangeRate": 1,
				"inv_buyerDisplayName": ""
				if la_phap_nhan
				else ten_mua,
				"inv_buyerLegalName": ten_mua if la_phap_nhan else "",
				"inv_buyerTaxCode": mst_mua,
				"inv_buyerAddressLine": dc_mua,
				"inv_buyerEmail": em_mua,
				"inv_paymentMethodName": PTTT_MINVOICE.get(si.vgb_pt_thanh_toan or "", "TM/CK"),
				"inv_discountAmount": 0,
				"inv_TotalAmountWithoutVat": t_chua,
				"inv_vatAmount": t_thue,
				"inv_TotalAmount": t_chua + t_thue,
				"key_api": si.custom_pancake_display_id or si.name,
				"details": [{"data": dong}],
			}
		],
	}
	r = requests.post(
		host + "/api/InvoiceApi78/Save",
		json=than,
		headers={"Authorization": "Bear " + token},
		timeout=30,
	)
	r.raise_for_status()
	j = r.json() or {}
	if not j.get("ok"):
		frappe.throw("m-invoice báo lỗi: %s" % json.dumps(j.get("message"), ensure_ascii=False))
	d = j.get("data") or {}
	frappe.db.set_value(
		"Sales Invoice",
		si.name,
		{
			"custom_hddt_trang_thai": d.get("tthai") or "Chờ ký",
			"custom_hddt_so": str(d.get("inv_invoiceNumber") or ""),
			"custom_hddt_id": d.get("inv_invoiceAuth_id") or "",
			"custom_hddt_sobaomat": d.get("sobaomat") or "",
		},
	)
	if hd:
		frappe.db.set_value(
			"Vagabond Hoa Don", {"ma_don": si.custom_pancake_display_id}, "tinh_trang", "Đã xuất"
		)
	frappe.db.commit()
	return d
