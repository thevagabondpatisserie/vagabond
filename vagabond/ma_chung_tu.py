# -*- coding: utf-8 -*-
"""Mã chứng từ chung MÃ-yymmdd-nnnnnn, áp từ 01/12/2026.

Anh Việt chốt 21/11/2026 (PR #601): mọi phiếu theo MỘT chuẩn
"MÃ-yymmdd-xxxxxx": tiền tố, ngày tạo kiểu năm-tháng-ngày, sáu chữ số.
Số KHÔNG đánh lại mỗi ngày: mỗi tiền tố một dãy số tăng liên tục, giống
lệnh sản xuất và mã lô đã chạy từ 06/09/2026 (xem `ma_phieu_sx`).

    HDB-26-11-03963   ->  HDB-261201-000001, HDB-261201-000002, ...
    PXD-2026-03322    ->  PXD-261201-000001
    APP.26.11.027     ->  APP-261201-000123 (hồ sơ và phiếu chi chung dãy)

Trước 01/12/2026 không đổi gì: hook trả về ngay, Frappe đặt tên như cũ.
Phiếu cũ GIỮ NGUYÊN mã cũ. Đổi tên chứng từ đã ghi sổ, đã xuất hoá đơn điện
tử là sửa dữ liệu quá khứ.

VÌ SAO TỰ CẤP SỐ CHỨ KHÔNG ĐỔI CHUỖI naming_series
--------------------------------------------------
Chuỗi `HDB-.YY..MM..DD.-.######` của Frappe đếm theo TIỀN TỐ ĐÃ ĐIỀN, tức mỗi
ngày một dòng đếm, sang ngày về 1. Anh muốn số liên tục, nên phải tự cấp số
từ MỘT dòng đếm cho mỗi tiền tố (`VGBMA-HDB`) bằng `getseries`, đúng hàm
Frappe dùng cho mọi naming_series (khoá dòng, hai người lưu cùng lúc không
nhận trùng số). Cùng lý do và cùng cách với `ma_phieu_sx`.

VÌ SAO HỒ SƠ APP VÀ PHIẾU CHI APP CHUNG MỘT DÃY
-----------------------------------------------
Hai doctype khác nhau nhưng cùng tiền tố APP, và cả hai đều được dò trên sao
kê ngân hàng theo mã (`khop_sao_ke.co_ma`). Hai dãy riêng sẽ sinh ra cùng một
chuỗi APP-261201-000005 cho hai chứng từ, dòng sao kê khớp nhầm phiếu. Một
dãy chung thì mỗi chuỗi chỉ có một chủ. Dòng đếm theo TIỀN TỐ, không theo
doctype, nên luật này đúng cho mọi tiền tố dùng chung.

HỎNG THÌ LÙI VỀ CÁCH CŨ, KHÔNG CHẶN
-----------------------------------
Khác lệnh sản xuất: hoá đơn bán ở quầy không được phép đứng vì một lỗi cấp
số. Hook ghi Error Log rồi để Frappe đặt tên theo chuỗi cũ; mã kiểu cũ vẫn
duy nhất, chỉ khác hình dạng.

NGÀY TRONG MÃ LÀ NGÀY TẠO
-------------------------
Ngày theo múi giờ site lúc lưu lần đầu, không phải ngày chứng từ. Phiếu lập
lùi ngày vẫn mang ngày tạo, giống mã lệnh sản xuất.
"""

import datetime
import re

# Ngày bắt đầu áp mã mới (anh Việt chốt 21/11/2026).
NGAY_AP = "2026-12-01"

# Số chữ số TỐI THIỂU của đuôi. Qua 999999 thì dài ra, không quay vòng.
SO_CHU_SO = 6

# Tiền tố dòng đếm trong tabSeries. Không trùng dòng đếm nào của Frappe
# (Frappe dùng chính tiền tố đã điền, vd "HDB-26-11-").
KHOA = "VGBMA-"

# Doctype ERPNext và doctype site đặt tên bằng naming_series. Tiền tố lấy từ
# chuỗi đang chọn trên phiếu, vì Material Request, Stock Entry có nhiều tiền
# tố (YCSX, YCMH, YCDC; PXD, PDC, PSX...) do Server Script chọn theo loại.
# Work Order KHÔNG nằm đây: lệnh sản xuất có hook riêng (ma_phieu_sx).
DT_THEO_CHUOI = (
	"Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry",
	"Purchase Order", "Purchase Receipt", "Sales Order", "Delivery Note",
	"Material Request", "Stock Entry", "Stock Reconciliation",
	"Production Plan", "Job Card", "Landed Cost Voucher", "Packing Slip",
	"Pick List", "Quality Inspection", "Quotation", "Request for Quotation",
	"Supplier Quotation", "RnD Purchase Request", "Phieu Kiem Ke",
	"Vagabond Lo Voucher", "Vagabond Tang Qua VIP",
)

# Doctype của app đặt tên bằng chuỗi format: tiền tố cố định.
DT_TIEN_TO = {
	"Vagabond Phieu Quy": "PQ",
	"Vagabond De Nghi Chi": "TTNB",
	"Vagabond Du Chi Muc": "DCM",
	"Vagabond Moc So Du": "MSD",
	"Vagabond De Xuat Cong Thuc": "DXCT",
	"Chi Phi Shipper": "CPS",
	"Vagabond Ca Quay": "CA",
	"Vagabond Hoan Tien": "HT",
	"Vagabond Nop Quy": "NQ",
	"Van Don": "VD",
	"Hop Dong Ban Hang": "HDBH",
	"Vagabond Can Tru San": "CTSAN",
	"Vagabond Khoan 242": "CP242",
}

# Tiền tố cấp số ngoài hook chung: hồ sơ APP (`ho_so_tt._sinh_ma`), báo giá
# (`Bao Gia Ban Hang.autoname`), phiếu thu hợp đồng (`thu_hop_dong._sinh_ma`).
# Dựng sẵn dòng đếm cho cả ba.
TIEN_TO_RIENG = ("APP", "VGB-PQ", "PTHD")

# GIỮ NGUYÊN, không theo chuẩn chung (ghi để người sau khỏi thêm nhầm):
#   - Mã đơn khách: DW (đơn web), TQ (gọi món tại bàn), GNV, BSI (bánh sỉ),
#     mã thiết kế riêng, DNTT và CN (yêu cầu thanh toán công nợ). Các mã này
#     nằm trong nội dung chuyển khoản và mã giao dịch OnePay (onepay.RE_MA_GD,
#     cong_no.RE_MA_DNTT); đổi hình dạng là đứt đường khớp tiền.
#   - Mã lô LO-yymmdd-nnnnnn: đã đúng chuẩn từ 06/09/2026.
#   - Tên ghép từ dữ liệu (KB-ngày, HD-mã đơn, KKD-điểm-ngày, NB-, KPI-,
#     HDCB-, MENU-) và danh mục (bài đăng, ứng viên, chiến dịch, thư viện báo
#     giá, lịch chi, quy cách đối chiếu): không phải phiếu đánh số.
#   - Bản ghi máy (đối soát DSN, DST; giá thử GT) và Serial and Batch Bundle.

MAU_TIEN_TO = re.compile(r"^[A-Z][A-Z0-9]{1,7}(?:-[A-Z]{2,4})?$")


# ------------------------------------------------------------ phần thuần


def _ngay(x):
	if isinstance(x, datetime.datetime):
		return x.date()
	if isinstance(x, datetime.date):
		return x
	return datetime.date.fromisoformat(str(x or "")[:10])


def da_ap(ngay):
	"""Ngày này đã dùng mã mới chưa. THUẦN."""
	return _ngay(ngay) >= _ngay(NGAY_AP)


def yymmdd(ngay):
	"""01/12/2026 -> "261201". THUẦN."""
	d = _ngay(ngay)
	return "%02d%02d%02d" % (d.year % 100, d.month, d.day)


def duoi(so):
	"""Đuôi số, tối thiểu sáu chữ số, qua 999999 thì dài ra. Số rác thì ném
	lỗi chứ không đẻ ra "000000". THUẦN."""
	so = int(so)
	if so < 1:
		raise ValueError("số thứ tự phải từ 1: %r" % so)
	return str(so).zfill(SO_CHU_SO)


def ma(tien_to, ngay, so):
	"""HDB, 01/12/2026, 1 -> "HDB-261201-000001". THUẦN."""
	return "%s-%s-%s" % (tien_to, yymmdd(ngay), duoi(so))


def tien_to_tu_chuoi(chuoi):
	"""Tiền tố của một chuỗi naming_series. THUẦN.

	"HDB-.YY.-.MM.-.#####" -> "HDB", "PXD-.YYYY.-" -> "PXD", "PCV-.#####" ->
	"PCV". Chuỗi mặc định của ERPNext ("ACC-SINV-.YYYY.-", "MAT-STE-...")
	không phải tiền tố tiếng Việt của tiệm: trả "" để Frappe đặt như cũ.
	"""
	s = str(chuoi or "").strip().upper()
	if not s:
		return ""
	dau = s.split(".", 1)[0].rstrip("-")
	if "-" in dau or not MAU_TIEN_TO.match(dau):
		return ""
	return dau


def la_ma_moi(ten, tien_to=None):
	"""Mã này theo chuẩn mới chưa: TIỀN TỐ-yymmdd-sáu số trở lên. THUẦN."""
	ten = str(ten or "").strip().upper()
	m = re.match(r"^(.+)-(\d{6})-(\d{6,})$", ten)
	if not m:
		return False
	if tien_to and m.group(1) != str(tien_to).strip().upper():
		return False
	try:
		datetime.date(2000 + int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:]))
	except ValueError:
		return False
	return True


def khoa(tien_to):
	"""Dòng đếm của một tiền tố. THUẦN."""
	return KHOA + str(tien_to).strip().upper()


# ------------------------------------------------------- phần cần Frappe


def _hom_nay():
	from frappe.utils import nowdate

	return nowdate()


def cap_so(tien_to):
	"""Cấp số kế tiếp của tiền tố. Khoá dòng đếm tới hết giao dịch."""
	from frappe.model.naming import getseries

	return int(getseries(khoa(tien_to), SO_CHU_SO))


def cap_ma(tien_to, doctype, ngay=None, truong="name"):
	"""Cấp một mã mới chưa ai mang trong `doctype`. Năm số liên tiếp đều đã
	có người mang (dòng đếm bị ai sửa lùi) thì ném lỗi."""
	import frappe

	ngay = ngay or _hom_nay()
	for _ in range(5):
		ten = ma(tien_to, ngay, cap_so(tien_to))
		if not frappe.db.exists(doctype, {truong: ten}):
			return ten
	raise ValueError("Năm số liên tiếp của %s đều đã có người mang." % tien_to)


def tien_to_cua(doc):
	"""Tiền tố mã mới của một phiếu, "" nếu phiếu không thuộc chuẩn chung."""
	dt = getattr(doc, "doctype", "")
	if dt in DT_TIEN_TO:
		return DT_TIEN_TO[dt]
	if dt in DT_THEO_CHUOI:
		chuoi = doc.get("naming_series")
		if not chuoi:
			import frappe

			o = frappe.get_meta(dt).get_field("naming_series")
			chuoi = (o.default or "") if o else ""
		return tien_to_tu_chuoi(chuoi)
	return ""


def dat_ten(doc, method=None):
	"""Hook autoname: từ 01/12/2026 đặt tên MÃ-yymmdd-nnnnnn.

	Chạy sau autoname của lớp (frappe/model/naming.py `set_new_name`). Đã có
	tên (bản sửa đổi, luật đặt tên, nhập dữ liệu) thì không đụng. Hỏng thì ghi
	Error Log và để Frappe đặt theo chuỗi cũ, xem đầu tệp.
	"""
	import frappe

	try:
		if (getattr(doc, "name", None) or "").strip():
			return
		ngay = _hom_nay()
		if not da_ap(ngay):
			return
		tt = tien_to_cua(doc)
		if not tt:
			return
		doc.name = cap_ma(tt, doc.doctype, ngay)
	except Exception:
		doc.name = None
		frappe.log_error(frappe.get_traceback(), "ma_chung_tu: dat ten %s" % getattr(doc, "doctype", ""))


def dung():
	"""after_migrate: dựng sẵn dòng đếm (current 0) cho mọi tiền tố đã biết.

	Có sẵn dòng thì hai phiếu đầu tiên lưu cùng lúc không đụng nhau ở lệnh
	INSERT của `getseries`. Chạy lại không đổi gì: chỉ chèn dòng CHƯA có.
	"""
	import frappe

	try:
		ds = set(DT_TIEN_TO.values()) | set(TIEN_TO_RIENG)
		for dt in DT_THEO_CHUOI:
			if not frappe.db.exists("DocType", dt):
				continue
			o = frappe.get_meta(dt).get_field("naming_series")
			for c in str((o.options if o else "") or "").splitlines():
				tt = tien_to_tu_chuoi(c)
				if tt:
					ds.add(tt)
		for tt in sorted(ds):
			if not frappe.db.sql("select 1 from `tabSeries` where name=%s", (khoa(tt),)):
				frappe.db.sql("insert into `tabSeries` (`name`, `current`) values (%s, 0)", (khoa(tt),))
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ma_chung_tu: dung dong dem")
