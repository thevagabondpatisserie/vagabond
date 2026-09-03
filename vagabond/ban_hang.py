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

import base64
import hmac
import json
import re
import time
import unicodedata

import frappe
import requests
from frappe.utils import add_days, cint, flt, fmt_money, get_datetime, getdate, now_datetime, nowdate

from vagabond import chiem_sao_ke, gia_pancake, hoa_don_vat

# Khoa dung chung giua dong bo Pancake va chuoi cuoi ngay. Nhap phong thu:
# ten module nay tung doi giua cac ban Frappe, ma neu import hong thi CA
# module ban_hang chet theo - mat luon ban hang, cuoi ngay, hoa don. Thieu
# khoa chi la thinh thoang dinh mot don, khong dang doi lay rui ro do.
from contextlib import ExitStack

try:
	from frappe.utils.synchronization import LockTimeoutError, filelock
except Exception:  # pragma: no cover
	import contextlib

	class LockTimeoutError(Exception):
		pass

	@contextlib.contextmanager
	def filelock(ten, timeout=30, **kw):
		yield

from vagabond import chung_tu, diem_ban, mau_in_quay, may_in, noi_bo, pancake_nhip, pt_thanh_toan, quyen_quay, tai_khoan
from vagabond import ghi_so_dieu_kien, khop_tien, luat_thanh_toan, ma_bill
from vagabond.kiem_banh import _keo_don, _khoang_unix
from vagabond.vagabond.doctype.anh_xa_ma_si.anh_xa_ma_si import doi_ma as doi_ma_si
from vagabond.lib import TIMEOUT, cache_get, cache_set, cfg, giau_khoa, key

# Trang thai Pancake tinh vao doanh so: 3 da nhan, 16 da thu tien.
TT_DOANH_SO = {3, 16}

KHACH_LE = "Khách lẻ Online"
# DVBH00001 la item "Phí Dịch Vụ Vận Chuyển" co san ben Next (bo ma chuan).
MA_PHI_GIAO = "DVBH00001"

QUYEN_BAN_HANG = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}


def _kiem_quyen():
	if not QUYEN_BAN_HANG & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền ghi nhận doanh số.")


# ---------- Ma OTP quan ly (anh Viet 09/08/2026) ----------
# Hoa don quay la tien that da thu cua khach. De nhan vien tu do sua/xoa
# thi rat de gian lan, nen moi thao tac sua/xoa deu phai co ma OTP 6 so
# xin tu quan ly. Ma tu sinh theo dong ho (khong luu DB, khong ai doc trom
# duoc trong bang), 10 phut doi mot lan.
OTP_PHUT = 10
OTP_SEP = {
	"ntla.3008@gmail.com",  # Nguyen Thi Loan Anh
	"led70076@gmail.com",  # Le Hoang De
	"long.duyen211234@gmail.com",  # Tran Dinh Uyen Duyen
	"thevagabond.marketing@gmail.com",  # Nguyen Hoang Viet
	"mason110992@gmail.com",  # Ma Thanh Son
	"dung.ngo1587@gmail.com",  # Ngo Hoang Ngoc Dung
}


def _otp_la_sep(user=None):
	return (user or frappe.session.user) in OTP_SEP


def _otp_buoc(luc=None):
	return int((luc if luc is not None else time.time()) // (OTP_PHUT * 60))


def _otp_ma(buoc):
	"""Sinh 6 so tu khoa bi mat cua site - khong luu dau o dau."""
	bi_mat = frappe.local.conf.get("encryption_key") or frappe.local.conf.get("db_password") or "vagabond"
	h = hmac.new(
		str(bi_mat).encode("utf-8"), ("vgb-otp-%d" % buoc).encode("utf-8"), hashlib.sha256
	).hexdigest()
	return "%06d" % (int(h[:12], 16) % 1000000)


@frappe.whitelist()
def otp_hien_tai():
	"""Ma OTP dang hieu luc - chi quan ly duoc xem."""
	_kiem_quyen()
	if not _otp_la_sep():
		frappe.throw(
			"Chỉ quản lý được cấp mã OTP. Bạn cần sửa hoặc xoá hoá đơn thì "
			"liên hệ quản lý ca để xin mã."
		)
	buoc = _otp_buoc()
	con = int((buoc + 1) * OTP_PHUT * 60 - time.time())
	return {"ma": _otp_ma(buoc), "con_lai": max(0, con), "phut": OTP_PHUT}


def _otp_kiem(otp, viec=""):
	"""Sep tu thao tac thi khoi nhap ma; nhan vien phai co ma con hieu luc.
	Chap nhan ca ma cua chu ky truoc de nguoi doc ma qua dien thoai khong
	bi hut ma giua chung."""
	if _otp_la_sep():
		return "quản lý " + (frappe.session.user or "")
	ma = re.sub(r"\D", "", str(otp or ""))
	if not ma:
		frappe.throw(
			"Thao tác này cần mã OTP của quản lý. Bấm xin mã từ quản lý ca rồi nhập vào."
		)
	buoc = _otp_buoc()
	if ma not in (_otp_ma(buoc), _otp_ma(buoc - 1)):
		frappe.throw("Mã OTP không đúng hoặc đã hết hạn. Xin quản lý mã mới rồi nhập lại.")
	return "OTP"


def _ghi_vet(name, viec, cach):
	"""Luu dau vet ai sua/xoa hoa don nao, bang quyen gi."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Sales Invoice",
				"reference_name": name,
				"content": "%s - %s (%s)" % (viec, frappe.session.user, cach),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


def _cong_ty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def gan_khach_vao_dong(ds):
	"""Gan ten khach, so dien thoai va ma khach vao TUNG DONG don. Tai cho.

	Anh Viet 01/09/2026: *"don ma xem lai thi khong thay duoc thong tin khach
	hang hien thi tren don o moi man luon"*. Dung vay: du lieu von co san,
	nhung moi man tu doc mot kieu nen man nao quen doc la man do trang.

	MOT CHO TINH, MOI MAN DUNG CHUNG (QT-19). Truoc day man Sales tu
	`split(' - ')` tho ngay tren trinh duyet, ma khuon that con co duoi
	"Quay <ma>", nen bill quay hien nham chu "Quay TCV" vao o so dien thoai.
	`tach_ghi_chu_don` da xu ly dung cai duoi do roi, nen goi lai no chu dung
	viet lai phep tach lan thu hai.

	Sau khi chay, moi dong co them ba o:
	  ten_tren_don - ten khach doc duoc, roi ve customer_name neu ghi chu trong
	  sdt_tren_don - so dien thoai, chuoi rong neu khong co
	  ma_khach     - ma ho so khach de man hinh xin the thanh vien, rong voi
	                 don ban le chua gan ho so

	Sua ds tai cho va tra lai chinh no, de goi duoc theo kieu mot dong.
	"""
	try:
		from vagabond.hoan_tien import tach_ghi_chu_don
	except Exception:
		tach_ghi_chu_don = None
	for d in ds or []:
		ten, so = "", ""
		if tach_ghi_chu_don:
			try:
				ten, so = tach_ghi_chu_don(d.get("remarks"))
			except Exception:
				ten, so = "", ""
		d["ten_tren_don"] = ten or d.get("customer_name") or ""
		d["sdt_tren_don"] = so
		# Ma khach chi co nghia khi no tro toi mot ho so that. Khach gop dung
		# chung thi khong phai ho so cua ai, dua len man hinh se ra the thanh
		# vien cua mot nguoi khong ton tai.
		kh = str(d.get("vgb_khach_no") or "").strip()
		if not kh:
			c = str(d.get("customer") or "").strip()
			if c and not c.startswith(KHACH_LE) and c != "Khách bán lẻ":
				kh = c
		d["ma_khach"] = kh
	return ds


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


def _dong_co_giam(ma, sl, bo_gia):
	"""Mot dong hoa don GIU NGUYEN phan giam gia thay vi nuot vao gia ban.

	Anh Viet 24/08/2026: *"neu dong bo duoc dong giam gia ben Pancake ve erp
	tro thanh dong giam gia thi qua tot, thay vi giam luon vao gia ban giong
	nhu hien tai"*.

	Truoc day dong nay chi mang mot con so `rate` da tru giam. Hai cai gia
	phai tra:

	  - To hoa don ghi 2.090.000 va khong noi gi them. Nhin vao khong biet
	    day la hop banh 2.200.000 duoc giam 5 phan tram hay mot hop banh
	    khac gia 2.090.000. Mat han y nghia thuong mai cua don.
	  - `price_list_rate` khong duoc khai thi ERPNext tu keo gia tu bang gia
	    Standard Selling. Voi ma si duoc anh xa ve ma banh goc (xem doi_ma_si)
	    thi gia trong bang gia KHAC gia si tren dong don, nen cot "giam gia"
	    ERPNext tu tinh ra la mot con so vo nghia.

	Nay khai ro ba thu:
	  price_list_rate      gia goc CUA CHINH DONG DON, khong phai bang gia
	  discount_percentage  chi khai khi Pancake noi la phan tram
	  rate                 gia ban, van do minh tinh chu khong de ERPNext tinh

	Vi sao van tu tinh `rate` thay vi de ERPNext nhan gia goc voi phan tram:
	con so cuoi cung phai khop TUNG DONG voi so khach da chuyen. Cach lam
	tron cua ERPNext khong nhat thiet giong Pancake, va mot dong lech vi lam
	tron thi doi soat SePay bao thieu tien.
	"""
	dong = {
		"item_code": ma,
		"qty": sl,
		"rate": bo_gia["gia_ban"],
	}
	if bo_gia.get("co_giam"):
		dong["price_list_rate"] = bo_gia["gia_goc"]
		if bo_gia.get("giam_pt"):
			dong["discount_percentage"] = bo_gia["giam_pt"]
		else:
			dong["discount_amount"] = bo_gia["giam_tien"]
	return dong


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
		# Ba so cua mot dong hang: gia goc, phan giam, gia ban. Phai di qua
		# gia_pancake vi Pancake gui kem co `is_discount_percent`: con so 5
		# co the la 5 dong ma cung co the la 5 PHAN TRAM. Doc thieu co la don
		# 91853 (22/08/2026) ghi 8.229.970 trong khi khach chuyen dung
		# 7.820.000. Xem gia_pancake.py.
		bo_gia = gia_pancake.dong_gia(gia, it)
		# Anh xa ma si ve ma banh goc (anh Viet chot huong B 03/08/2026): moi
		# khach si co ma rieng tren Pancake nhung ve Next thi gop lai mot ma
		# banh that de ton kho va gia von khong bi chia vun. GIA giu nguyen
		# theo dong don, tuc dung gia si cua khach do, khong lay bang gia cua
		# ma goc. Dong nao chua tich "Dang ap dung" thi giu nguyen ma si.
		ma = doi_ma_si(ma)
		rows.append(_dong_co_giam(ma, sl, bo_gia))
	phi_giao = flt(o.get("shipping_fee") or 0)
	if phi_giao > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": phi_giao})
	return rows, thieu


def _tong_niem_yet(o):
	"""Tong don theo GIA NIEM YET, chua tru bat ky khoan giam nao.

	Cong gia niem yet nhan so luong cua tung dong hang, cong phi giao cap
	don. Bo qua dong khong doc duoc ma - chinh nhung dong do lam `_dong_hang`
	tra ve `thieu` va nhip dong bo dung lai truoc khi den day.
	"""
	tong = 0.0
	for it in (o or {}).get("items") or []:
		vi = it.get("variation_info") or {}
		tong += flt(vi.get("retail_price") or 0) * flt(it.get("quantity") or 0)
	phi = flt((o or {}).get("shipping_fee") or 0)
	if phi > 0:
		tong += phi
	return tong


def _lech_pancake(o, rows, giam_don=0):
	"""Doi chieu tong don theo GIA NIEM YET voi con so Pancake gui ve.

	Tra 0 khi hai ben khop. Khac 0 nghia la ma cua tiem doc sai gia niem yet,
	sai so luong, hoac bo sot mot dong hang.

	Vi sao doi chieu o MUC NIEM YET chu khong o muc da tru giam gia
	-----------------------------------------------------------------
	v296 doi chieu o muc da tru giam gia va da keu nham hang loat. Ly do:
	truong `total_price` ma duong dong bo cua tiem nhan duoc la tong TRUOC
	khi tru giam gia. Ba so THAT doc duoc tren site ngay 24/08/2026 ngay sau
	khi deploy v296:

	    don 91853  ban tinh 7.820.000  total_price 8.230.000
	    don 91391  ban tinh 3.800.000  total_price 3.850.000 (giam cap don 50.000)
	    don 91511  ban tinh 4.532.500  total_price 4.770.000 (giam cap don 237.500)

	Ca ba deu la don DUNG. Lay 8.230.000 tru di hai khoan giam thi ra dung
	7.820.000. Nghia la con so kia la tong niem yet, va dem ban tinh DA TRU
	giam ra so voi no la so hai thu khac nhau.

	Cong noi bo pos.pancake.vn tra `total_price` DA TRU giam, nen phep do
	tren 1.073 don qua trinh duyet hom truoc moi khop tuyet doi. Hai cong
	cung ten truong ma khac nghia. Bai hoc: phep doi chieu phai chay tren
	DUNG duong du lieu ma ma nguon dung, khong phai tren mot duong tuong tu.

	Vay luoi nay con bat duoc gi
	-----------------------------
	No chot rang gia niem yet va so luong doc ra dung, va khong dong hang
	nao bi bo sot. Rieng loi giam gia phan tram cua v296 thi da co ca kiem
	thu chot bang so that cua don 91853, khong can luoi nay canh nua.

	KHONG chan dong bo va KHONG chan ghi so, chi ghi lai con so de man hinh
	ve dai bang. Chan tu dong o day la mot ngay nao do ca tiem khong chot
	duoc don nao vi mot truong la ben Pancake.

	Bo qua khi Pancake khong gui `total_price`: khong co gi de doi chieu thi
	im lang, khong bia ra mot con so lech.
	"""
	tong_pk = flt((o or {}).get("total_price") or 0)
	if tong_pk <= 0:
		return 0.0
	d = flt(gia_pancake.lech_tong(_tong_niem_yet(o), tong_pk, nguong=1.0))
	if d:
		frappe.log_error(
			"Đơn %s lệch %s đồng. Tổng theo giá niêm yết của hệ thống %s, "
			"tổng bên Pancake %s. Phụ thu Pancake %s, giảm cấp đơn %s."
			% (
				(o or {}).get("display_id") or (o or {}).get("id") or "?",
				d, _tong_niem_yet(o), tong_pk,
				flt((o or {}).get("surcharge") or 0), flt(giam_don or 0),
			),
			"ban_hang: lech tong don Pancake",
		)
	return d


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
# Sau danh sach phuong thuc thanh toan cu (PT_THAM_CHIEU, PT_QUAY,
# PT_PANCAKE, PT_CHUA_VE_TIEN, PT_VE_SAU, PTTT_MINVOICE) da gom ve mot noi:
# xem vagabond/pt_thanh_toan.py. Them mot may ca the moi gio la them mot
# dong tren app, khong phai sua sau cho roi deploy.

# Pancake KHONG co cac phuong thuc cua san, an di cho sales khoi chon nham
# (anh Viet 02/08). Don san la don NHAP TAY, moi san chi mot phuong thuc.
# Dau nhan dien dong GHI CHU MON trong description cua dong hoa don. Chon
# ky tu nay vi khong ai go nham duoc, va tach bach voi [tuy chon pha che].
DAU_GC_MON = "\u203b"
# Dau nhan dien dong TEN COMBO tren dong hoa don (anh Viet 11/08/2026). Mon
# ra tu combo nao thi mang ten combo do, de bep va nguoi di lay mon biet gom
# du bo, va de cuoi ngay dem duoc ban bao nhieu bo combo. In len bill va len
# tem dan mon, nhung KHONG in ma combo.
DAU_COMBO = "\u25c8"


# Hinh anh va phuong thuc hop le cua tung nguon. Chi la BANG TRA - danh
# sach nguon that thi sinh tu diem ban, nguon nao khong co trong bang nay
# van dung duoc, chi la khong co logo rieng.
NGUON_META = {
	"GrabFood": {"lg": "/files/pt-grab.png", "pt": ["GrabFood"]},
	"BeFood": {"lg": "/files/pt-befood.png", "pt": ["BeFood"]},
	"GreenSM Food": {"lg": "/files/pt-greensm.png", "pt": ["GreenSM Food"]},
	"ShopeeFood": {"lg": "/files/pt-shopee4.png", "pt": ["ShopeeFood"]},
	"Khách sỉ": {"ic": "🏢", "pt": ["Chuyển khoản", "Tiền mặt"]},
}


def _nguon_don():
	"""Danh sach nguon don, sinh tu cau hinh diem ban.

	Truoc day day la mot danh sach cung liet ke ca "Tai cho - Tran Cao Van"
	lan "Mang ve - Nguyen Van Troi". Them chi nhanh moi la phai sua o day
	nua, quen thi nguon moi khong chon duoc tren man tinh tien - dung cai
	ma man Cai dat hua la "khong phai sua phan mem".
	"""
	ra, da_co = [], set()
	# Phuong thuc da tat ben man Cai dat thi khong duoc hien lai o day. Bang
	# NGUON_META goi thang ten phuong thuc nen neu khong loc, tat mot phuong
	# thuc xong no van con nam trong nguon "Khach si": man Cai dat noi mot
	# dang, man tinh tien lam mot dang.
	# Phuong thuc cua san (GrabFood, ShopeeFood...) deu de quay=0 online=0
	# vi khong hien ra cho ai chon tay - nen o day phai lay TAT CA phuong
	# thuc dang dung, khong duoc lay ten_quay() | ten_online().
	con_dung_thu_tu = [p["ten"] for p in pt_thanh_toan.ds(chi_dung=True)]
	con_dung = set(con_dung_thu_tu)
	# Mot nguon co the thuoc nhieu diem ("Tại chỗ" chung cho moi quay), nen
	# phai biet TAT CA diem cua no truoc khi dung dong nguon do.
	chu = {}
	co_quay_cua = {}
	for d in diem_ban.ds(chi_bat=True):
		co_quay_cua[d["ma"]] = 1 if d["quay"] else 0
		for n in d["nguon"]:
			chu.setdefault(n, []).append(d["ma"])
	for d in diem_ban.ds(chi_bat=True):
		for n in d["nguon"]:
			if n in da_co or n == "Pancake":
				continue
			da_co.add(n)
			m = dict(NGUON_META.get(n) or {})
			# Nguon cua san moi nguon di dung mot phuong thuc cung ten. Tat
			# phuong thuc do thi de danh sach RONG cho thu ngan thay ngay,
			# chu khong duoc roi ve danh sach chung: don GrabFood ma hien nut
			# "Tien mat" la sai tien that.
			co_pt_rieng = bool(m.get("pt"))
			if co_pt_rieng:
				m["pt"] = [p for p in m["pt"] if p in con_dung]
			if not m.get("lg") and not m.get("ic"):
				# Doan bieu tuong theo cach goi quen thuoc cua quay.
				thap = n.lower()
				m["ic"] = "🏬" if thap.startswith("tại chỗ") else (
					"🥡" if thap.startswith("mang về") else "🧾"
				)
			if not co_pt_rieng:
				# Mot nguon co the thuoc CA quay LAN diem online ("Tại chỗ"
				# ban tai quay, va Sales cung nhan don tai cho cho khach ky
				# hop dong). Lay HOP hai danh sach chu khong lay theo diem
				# dau tien tim thay: xep SALES len dau danh sach diem la
				# nguon "Tại chỗ" mat sach phuong thuc cua quay, thu ngan
				# dung tai quay khong bam duoc tien mat.
				ds_ma = chu.get(n) or [d["ma"]]
				nhan = set()
				if any(co_quay_cua.get(x) for x in ds_ma):
					nhan |= set(pt_thanh_toan.ten_quay())
				if any(not co_quay_cua.get(x) for x in ds_ma):
					nhan |= set(pt_thanh_toan.ten_online())
				# Giu dung thu tu da khai o man Cai dat phuong thuc.
				m["pt"] = [t for t in con_dung_thu_tu if t in nhan]
			# Nguon co danh sach phuong thuc RIENG cua no (GrabFood,
			# ShopeeFood...) thi may tu chon duoc khi danh sach con dung mot
			# cai. Nguon dung danh sach chung cua quay thi khong, du danh
			# sach chung co rut xuong con mot vi ai do tat bot o Cai dat.
			m["rieng"] = 1 if co_pt_rieng else 0
			m["v"] = n
			# Ma diem ban cua nguon nay. App can de dat noi dung chuyen khoan
			# (ma diem + so phieu) o nhung man khong biet minh dang o quay nao,
			# vi du man Chi tiet don ben Sales.
			#
			# Nguon dung chung nhieu diem thi KHONG doan bua mot ma: man nao
			# can biet diem thi phai hoi nguoi dung (man Nhap don tay co o
			# chon Diem ban), con man tinh tien quay thi tu biet minh o quay
			# nao roi.
			ds_diem = chu.get(n) or [d["ma"]]
			m["diem"] = ds_diem[0] if len(ds_diem) == 1 else ""
			m["diem_ds"] = list(ds_diem)
			ra.append(m)
	return ra

# Hai quay ban truc tiep, cho man Tinh tien quay tren app /bep (08/08/2026).
# Ten hien thi do anh Viet chot: D1 = THE VAGABOND DISTRICT 1 (9 Tran Cao Van),
# NVHTN = Nha Van Hoa Thanh Nien (nguon he thong dat theo dia chi Nguyen Van Troi).
def _quay():
	"""Cac quay ban tai cho, sinh tu cau hinh diem ban."""
	ra = []
	for d in diem_ban.ds(chi_bat=True):
		if not d["quay"]:
			continue
		ra.append({
			"ma": d["quay"],
			"ten": d["ten"],
			"phu": d["phu"] or d["dia_chi"],
			"anh": d["anh"] or ("/assets/vagabond/images/quay-%s.jpg" % d["ma"].lower()),
			"tai_cho": d["tai_cho"],
			"mang_ve": d["mang_ve"],
		})
	return ra

# Tai khoan nhan chuyen khoan khong con hardcode o day nua: gio khai o man
# Cai dat va tach duoc theo tung nguon don - xem tai_khoan.py. Noi dung
# chuyen khoan van la ma diem ban + so phieu, de doi soat SePay.


# Thu tu nhom mon o man chon mon, xep theo tan suat ban thuc te tai quay
# (anh Viet 10/08/2026) - banh o sinh nhat de cuoi vi quay ban rat it, chu
# yeu ben Sales ban. Nhom khong co trong danh sach nay rot xuong duoi va
# xep theo bang chu cai.
THU_TU_NHOM = [
	"Khuyến mãi dạng Combo",
	"Bánh mì",
	"Bánh nướng",
	"Bánh lạnh",
	"Bánh khô",
	"BÁNH NHẸ / CONFECTIONERY",
	"Cà phê",
	"Trà",
	"Matcha",
	"Cacao",
	"Ice Cream - Kem",
	"Topping cho món nước",
	"Topping cho món bánh",
	"Phụ kiện cho bánh",
	"Hộp bánh theo mùa",
	"Bánh ổ sinh nhật",
]

# Ten nguon cu tren cac hoa don da nhap truoc 02/08, giu de doc lai duoc.
# Tu 12/08/2026 gom them nguon quay: truoc day moi diem ban mot cap ten
# rieng ("Tại chỗ - Trần Cao Vân"), nay chi con "Tại chỗ" va "Mang về" dung
# chung, diem ban doc tu vgb_quay. Giu bang tra de hoa don cu va man hinh
# cu goi ten cach nao cung ra dung nguon.
NGUON_CU = {
	"Grab": "GrabFood",
	"Grab Online": "GrabFood",
	"Be": "BeFood",
	"GreenSM": "GreenSM Food",
	"Tại chỗ - Trần Cao Vân": "Tại chỗ",
	"Mang về - Trần Cao Vân": "Mang về",
	"Tại chỗ - Nguyễn Văn Trỗi": "Tại chỗ",
	"Mang về - Nguyễn Văn Trỗi": "Mang về",
	"Tại chỗ - Sales Online": "Tại chỗ",
	"Mang về - Sales Online": "Mang về",
}


def _quay_cua_nguon(nguon, quay):
	"""Ma quay cho mot don nhap tay, suy tu nguon don.

	Nguon gio dung chung giua cac quay nen ten nguon khong con noi duoc don
	nay cua diem nao. Man Nhap don tay phai gui kem ma quay; ba hoa don
	"Tại chỗ - Trần Cao Vân" nhap truoc 12/08 deu de trong vgb_quay, tuc ca
	he dang doc chung la don Sales Online - dung cai bay phai bit.
	"""
	q = str(quay or "").strip().upper()
	ds_diem = diem_ban.diem_cua_nguon(nguon)
	if q:
		d = diem_ban.theo_ma(q)
		if not d:
			frappe.throw("Mã điểm bán %s không có trong danh sách điểm bán." % q)
		# Diem nhan don online khong co ma quay. Truoc day cho nay chan
		# thang, nen chon "Sales Online" cho don "Tại chỗ" la bao loi. Nay
		# nhan: tra ve chuoi rong, tuc vgb_quay de trong, dung cach ca he
		# nhan ra don cua diem online (anh Viet 15/08/2026).
		if not d["quay"]:
			if ds_diem and d["ma"] not in ds_diem:
				frappe.throw(
					"Điểm bán %s không nhận đơn nguồn \"%s\". Các điểm đang "
					"nhận nguồn này: %s." % (d["ma"], nguon, ", ".join(ds_diem) or "(chưa khai)")
				)
			return ""
		if ds_diem and d["ma"] not in ds_diem:
			frappe.throw(
				"Điểm bán %s không nhận đơn nguồn \"%s\". Các điểm đang nhận "
				"nguồn này: %s." % (d["ma"], nguon, ", ".join(ds_diem) or "(chưa khai)")
			)
		return d["quay"]
	if len(ds_diem) == 1:
		d = diem_ban.theo_ma(ds_diem[0])
		return d["quay"] if d else ""
	if len(ds_diem) > 1:
		frappe.throw(
			"Nguồn \"%s\" đang dùng chung cho %s nên phải chọn điểm bán trước "
			"khi lưu đơn." % (nguon, ", ".join(ds_diem))
		)
	return ""


def _pt_cho_nguon(nguon):
	"""Danh sach phuong thuc thanh toan hop le cua mot nguon don."""
	return _pt_cho_nguon_kem_co(nguon)[0]


def _pt_cho_nguon_kem_co(nguon):
	"""Nhu tren, kem co bao nguon nay co danh sach phuong thuc RIENG khong.

	Tra (danh_sach, co_pt_rieng). Cai co do la thu quyet dinh may co duoc
	tu chon phuong thuc hay khong - xem `luat_thanh_toan.pt_theo_nguon`.
	"""
	nguon = NGUON_CU.get((nguon or "").strip(), (nguon or "").strip())
	if not nguon or nguon == "Pancake":
		return (pt_thanh_toan.ten_online(), False)
	for n in _nguon_don():
		if n["v"] == nguon:
			return (list(n["pt"]), bool(n.get("rieng")))
	return (pt_thanh_toan.ten_quay(), False)


def _chuan_ma_tham_chieu(pt, ma, bat_buoc=True):
	"""Chuan hoa va kiem ma tham chieu theo phuong thuc thanh toan.

	Sales go "689" cho GrabFood hay "#3621" cho ShopeeFood deu duoc, may tu
	them tien to va bo dau #. Sai dang thi bao ngay tai cho chu khong de
	den luc doi soat moi phat hien.
	"""
	q = pt_thanh_toan.theo_ten(pt) or {}
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
	"""KHONG con chan nua (anh Viet 10/08/2026).

	Cac san giao do quay vong ma don: GrabFood dung lai ma GF-572 cho don
	moi sau vai ngay, ma cu 07/08 van con trong so. Chan cung thi nhan vien
	khong nhap duoc don that, mat doanh thu - hai hon nhieu so voi cai loi
	bam trung thinh thoang moi co.

	Doi lai, cac man danh sach danh dau nhung don trung ma TRONG CUNG MOT
	NGAY (xem _ma_trung_trong_ngay) - do moi la dau hieu bam nham that.
	"""
	return


def _ma_trung_trong_ngay(ngay, ds_ma):
	"""Tap ma tham chieu bi dung cho tu hai hoa don tro len trong mot ngay."""
	ds_ma = [str(m).strip() for m in (ds_ma or []) if str(m or "").strip()]
	if not ds_ma:
		return set()
	dem = {}
	for m in ds_ma:
		k = m.upper()
		dem[k] = dem.get(k, 0) + 1
	return set(k for k, v in dem.items() if v > 1)


def _kiem_pt(pt, nguon):
	"""Phuong thuc thanh toan hop le cua mot don. MOI man tinh tien deu qua day.

	Cua duy nhat: man Sales, quay D1, quay NVHTN va moi quay mo sau nay deu
	goi ham nay, nen luat tu chon theo nguon don chi phai viet mot lan o day
	chu khong phai chep sang tung man (anh Viet chot 26/08/2026).
	"""
	hop_le, rieng = _pt_cho_nguon_kem_co(nguon)
	pt = luat_thanh_toan.pt_theo_nguon(pt, hop_le, rieng)
	if not pt:
		return ""
	if not pt_thanh_toan.theo_ten(pt):
		frappe.throw("Không có phương thức thanh toán %s." % pt)
	if pt not in hop_le:
		frappe.throw(
			"Đơn nguồn %s không dùng phương thức %s. Chọn trong: %s."
			% (nguon or "Pancake", pt, ", ".join(hop_le))
		)
	if not frappe.db.exists("Mode of Payment", pt):
		frappe.throw("Chưa khai phương thức thanh toán %s bên Next." % pt)
	return pt


def _nan_pt_theo_nguon(si):
	"""Nan phuong thuc ve dung nguon don, va GHI LAI viec da nan.

	Nan am tham thi ke toan cuoi thang thay con so la ma khong biet vi sao,
	nen moi lan nan deu de lai mot dong trong ghi chu doi soat.
	"""
	cu = (si.get("vgb_pt_thanh_toan") or "").strip()
	pt = _kiem_pt(cu, si.custom_nguon)
	if luat_thanh_toan.may_da_nan(cu, pt):
		dong = "Nguồn %s chỉ đi phương thức %s, máy đổi từ %s." % (
			si.custom_nguon or "Pancake", pt, cu)
		co = (si.get("vgb_ghi_chu_doi_soat") or "").strip()
		if dong not in co:
			si.vgb_ghi_chu_doi_soat = (co + " | " + dong) if co else dong
	return pt


def _nan_pt_tai_cho(si):
	"""Nan phuong thuc ve dung nguon don NGAY LUC SUA, khong doi den ghi so.

	BEN DE 01/09/2026: *"cac food app no khong co nut chon phuong thuc, khi
	luu hoa don no de la thanh toan chuyen khoan, cho tien ve"*.

	Da soi hai hoa don that (ShopeeFood ma o phuong thuc ghi "Chuyen khoan",
	31/08/2026). Phep nan `_nan_pt_theo_nguon` von da co, nhung truoc day chi
	chay luc GHI SO. Bill nam o trang thai nhap ca ngay thi cac ban nhin thay
	chip "Chuyen khoan - Cho tien ve" va tuong he thong hong, trong khi den
	23h may van ghi so dung.

	Nay nan ngay o cua sua, nen cai cac ban nhin thay chinh la cai se ghi so.

	KHONG dung cho bill TAM TINH: bill do co y de trong phuong thuc, nan vao
	la dat ho khach mot cach tra tien ma khach chua chon.
	"""
	if cint(si.get("vgb_tam_tinh")):
		return
	cu = (si.get("vgb_pt_thanh_toan") or "").strip()
	if not cu:
		return
	try:
		moi = _nan_pt_theo_nguon(si)
	except Exception:
		# Nan hong thi de nguyen, dung chan nguoi ta sua bill vi mot phep phu.
		frappe.log_error(frappe.get_traceback(), "ban_hang: nan phuong thuc tai cho")
		return
	if moi and moi != cu:
		si.vgb_pt_thanh_toan = moi


# Anh thumbnail cua tung quay: luu bang default toan he thong nen doi anh
# khong phai sua ma, khong phai migrate. Anh Viet tu tai anh len trong app
# la ca hai quay va man Sales doi theo (10/08/2026).
KHOA_ANH_QUAY = "vgb_anh_quay_"


def _anh_quay_da_luu(ma):
	try:
		return frappe.db.get_default(KHOA_ANH_QUAY + str(ma or "")) or ""
	except Exception:
		return ""


@frappe.whitelist()
def pos_anh_quay_luu(ma=None, url=None):
	"""Doi anh thumbnail cua mot quay. Chi sales va ke toan duoc doi."""
	_kiem_quyen()
	ma = (ma or "").strip()
	url = (url or "").strip()
	if not ma:
		frappe.throw("Thiếu mã quầy.")
	# Chi nhan duong dan tep tren chinh site nay - khong cho tro ra ngoai
	# de khoi bi nhet link la vao man hinh nhan vien.
	if url and not url.startswith("/"):
		frappe.throw("Đường dẫn ảnh phải là tệp đã tải lên hệ thống.")
	frappe.db.set_default(KHOA_ANH_QUAY + ma, url)
	frappe.db.commit()
	return {"ma": ma, "url": url}


@frappe.whitelist()
def cau_hinh_ban_hang():
	"""Nguon don, phuong thuc thanh toan, quy tac ma tham chieu cho app /bep.

	App KHONG hardcode danh sach nua - sua o day la ca app doi theo.
	"""
	_kiem_quyen()
	pt = []
	for ten, q in pt_thanh_toan.bang_tham_chieu().items():
		pt.append(
			{
				"v": ten,
				"lg": q.get("lg") or "",
				"ic": q.get("ic") or "",
				"bat": 1 if q.get("bat") else 0,
				"nhan": q.get("nhan") or "Mã tham chiếu",
				"vd": q.get("vd") or "",
			}
		)
	quay = []
	for q in _quay():
		q2 = dict(q)
		q2["anh"] = _anh_quay_da_luu(q["ma"]) or q.get("anh") or ""
		quay.append(q2)
	nguon = _nguon_don()
	# Toan bo diem ban dang bat, KE CA diem nhan don online. "quay" ben duoi
	# chi co diem co quay nen man Nhap don tay khong tra duoc ten cua Sales;
	# tu 15/08/2026 "Tại chỗ" va "Mang về" gan duoc cho Sales nen phai co
	# danh sach day du (anh Viet).
	diem_ds = [
		{
			"ma": d["ma"],
			"ten": d["ten"],
			"ten_ngan": d["ten_ngan"],
			"phu": d["phu"] or d["dia_chi"],
			"co_quay": d["co_quay"],
			"anh": _anh_quay_da_luu(d["ma"]) or d["anh"] or "",
			# Ba truong nay truoc day chi co trong danh sach "quay". Man tinh
			# tien nay dung chung cho MOI diem ban ke ca diem khong co quay
			# tien mat, nen no phai doc duoc nguon don va hai nhan Tai cho /
			# Mang ve tu chinh danh sach nay (anh Viet 24/08/2026).
			"quay": d["quay"],
			"tai_cho": d["tai_cho"],
			"mang_ve": d["mang_ve"],
			"nguon": d["nguon"],
		}
		for d in diem_ban.ds(chi_bat=True)
	]
	return {
		"pt": pt,
		"nguon": nguon,
		"pt_pancake": pt_thanh_toan.ten_online(),
		"quay": quay,
		"diem": diem_ds,
		# Anh chi nhanh Sales Online (307/1 Nguyen Van Troi) anh Viet gui
		# 11/08/2026. Doi anh trong app thi lay anh moi, chua doi thi dung
		# anh nay.
		"anh_sales": _anh_quay_da_luu("SALES") or "/assets/vagabond/images/quay-sales.jpg",
		# Bang tien to ma bill, MOT NOI GIU (`ma_bill.py`). Man hinh sinh ma
		# doc bang nay chu khong chep lai: chep lai la den luc them diem ban
		# thu ba, may chu doc duoc tien to moi ma man hinh van sinh VGB.
		"ma_tien_to": dict(ma_bill.TIEN_TO_DIEM),
		"ma_tien_to_cu": ma_bill.TIEN_TO_CU,
		"ma_chu_sinh": ma_bill.CHU_SINH,
		"ma_dai_duoi": ma_bill.DAI_DUOI,
		"qr_quay": tai_khoan.tk_cho(),
		# Tai khoan ao rieng cua tung nguon don, de man tinh tien sinh QR
		# vao dung tai khoan cua nguon do.
		"qr_nguon": tai_khoan.bang_theo_nguon(nguon),
		"thu_tu_nhom": THU_TU_NHOM,
		# Kho giay tung loai phieu, de app khong go cung 80mm nua. Doi may
		# in khac kho thi khai o man Cai dat, khong phai sua ma roi deploy.
		"kho_in": may_in.kho_theo_vai_tro(),
		# Kho giay RIENG cua tung diem ban. Hai diem co the dung hai kho tem
		# khac nhau, va truoc day bang chung o tren lay may dau tien trong ca
		# danh sach nen mot diem in tem theo kho cua diem kia (anh Viet
		# 24/08/2026). `kho_in` o tren giu lai lam luoi do cho man nao chua
		# biet minh dang o diem nao.
		"kho_in_diem": {d["ma"]: may_in.kho_theo_vai_tro(d["ma"]) for d in diem_ban.ds(chi_bat=True)},
		# Mau in tai quay: tren to giay do in nhung gi. Cung mot kieu chia
		# theo diem ban nhu kho giay o tren - hai quay khong bat buoc in
		# giong nhau (anh Viet 26/08/2026). `mau_in` la ban chung, dung cho
		# man nao chua biet minh dang o diem nao.
		"mau_in": mau_in_quay.theo_diem(),
		"mau_in_diem": {
			d["ma"]: mau_in_quay.theo_diem(d["ma"]) for d in diem_ban.ds(chi_bat=True)
		},
		"pt_chua_ve_tien": pt_thanh_toan.chua_ve_tien(),
		"pt_ve_sau": pt_thanh_toan.ve_sau(),
		# Nhom thu tu: tien KHONG BAO GIO ve (hang tang). Tra ve cung cho voi
		# hai nhom kia de man nao can cung doc duoc mot chuong.
		"pt_khong_thu": pt_thanh_toan.khong_thu(),
		# De app biet luc nao phai hoi ma OTP. May chu van kiem lai het, day
		# chi la de khoi bat thu ngan go ma cho mot viec ho duoc phep lam.
		"quyen_bo_mon": quyen_quay.muc(),
		"nguon_app": [n["v"] for n in nguon if n.get("lg")],
	}


# Cac o tien cu tren don Pancake. GIU LAI lam duong lui cho don cu: don
# truoc thang 8/2026 khong co payment_purchase_histories nen van phai doc o
# nay. Don moi thi doc lich su giao dich, chinh xac hon nhieu.
#
# Luu y da do tren du lieu that ngay 15/08/2026 (340 don, 7 ngay):
# charged_by_onepay va payment_purchase_method KHONG TON TAI trong du lieu
# Pancake tra ve - khong phai bang 0 ma la khong co truong do. Nen dong
# OnePay ben duoi tu truoc toi nay chua bao gio chay.
PT_KENH = (
	("cash", "Tiền mặt", "tiền mặt"),
	("transfer_money", "Chuyển khoản", "chuyển khoản"),
	("charged_by_onepay", "OnePay", "OnePay"),
	("charged_by_card", "", "cà thẻ (chọn máy Payoo/Shinhan)"),
	("charged_by_momo", "", "Momo"),
	("charged_by_vnpay", "", "VNPay"),
	("charged_by_qrpay", "", "QR Pay"),
)

# Ma ket qua bao GIAO DICH THANH CONG trong payment_purchase_histories.
#
# Day la chot chan quan trong nhat cua ca phan nay. Do tren 340 don that:
# onepay tra "0" khi thanh cong va "253" khi that bai, mbbank tra "00". Neu
# anh xa theo `type` ma quen loc ma ket qua thi 19 giao dich HONG trong bay
# ngay do se thanh 19 lan ghi nhan thu tien khong co that.
MA_THANH_CONG = {"0", "00", "000"}


def _giam_tu_diem(si):
	"""Phan giam gia den tu diem thanh vien tren mot to. Mac dinh 0.

	MOT CUA DUY NHAT de doc con so nay trong ban_hang.py. Bon cho dat lai
	discount_amount deu phai cong no vao, khong thi luot tru diem cua khach
	bi xoa am tham - xem ghi chu dai o _upsert_hoa_don.

	Doc bang .get() va roi ve 0 de con chay duoc TRUOC khi Migrate dung cot
	vgb_giam_diem: bai hoc v177, after_migrate KHONG chay sau moi lan deploy.
	"""
	try:
		return flt((si or {}).get("vgb_giam_diem") or 0)
	except Exception:
		return 0.0


# Truong tu them do ma nguon khai, dung lai moi lan deploy - xem
# vagabond/truong_tu_them.py.
TRUONG_MOI = {
	"Sales Invoice": [
		{
			"fieldname": "vgb_pt_do_may",
			"label": "Phương thức do máy đoán",
			"fieldtype": "Check",
			"insert_after": "vgb_pt_thanh_toan",
			"read_only": 1,
			"description": (
				"Máy đặt cờ này khi tự điền phương thức thanh toán từ Pancake. "
				"Người sửa tay thì cờ tắt, và từ đó máy không đè lên nữa."
			),
		},
		{
			"fieldname": "vgb_nghi_cong_no",
			"label": "Nghi công nợ",
			"fieldtype": "Check",
			"insert_after": "vgb_pt_do_may",
			"read_only": 1,
			"description": (
				"Đơn đã giao xong mà Pancake không ghi nhận khoản thanh toán "
				"nào. Máy chỉ gắn cờ để sales rà lại, KHÔNG tự ghi là công nợ."
			),
		},
		{
			"fieldname": "vgb_lech_pancake",
			"label": "Lệch so với tổng đơn Pancake",
			"fieldtype": "Currency",
			"insert_after": "vgb_nghi_cong_no",
			"read_only": 1,
			"description": (
				"Bằng 0 là bản tính của hệ thống khớp tổng đơn bên Pancake. "
				"Khác 0 là có một loại giá hoặc giảm giá chưa đọc đúng, cần "
				"báo bộ phận kỹ thuật trước khi ghi sổ."
			),
		},
		{
			"fieldname": "custom_hddt_sai_sot",
			"label": "Hoá đơn bị sai sót, cần thay thế",
			"fieldtype": "Check",
			"insert_after": "custom_hddt_so",
			"description": (
				"Kế toán bật cờ này khi hoá đơn điện tử đã phát hành bị sai "
				"thông tin. Bật xong thì điền số hoá đơn thay thế và đính "
				"biên bản thay thế vào ngay bên dưới."
			),
		},
		{
			"fieldname": "vgb_gd_sepay",
			"label": "Dòng sao kê đã gạch cho bill này",
			"fieldtype": "Small Text",
			"insert_after": "vgb_lech_pancake",
			"read_only": 1,
			"description": (
				"Mã các dòng sao kê ngân hàng đã được tính là tiền của bill này, "
				"mỗi mã một dòng. Một dòng sao kê chỉ được gạch cho một chứng từ."
			),
		},
		{
			"fieldname": "custom_hddt_ly_do_thay_the",
			"label": "Lý do phải thay thế",
			"fieldtype": "Small Text",
			"insert_after": "custom_hddt_sai_sot",
			"description": (
				"Ghi rõ sai ở chỗ nào, ví dụ tên người mua bị thiếu. Đây là "
				"phần giải trình khi cơ quan thuế hỏi lại."
			),
		},
	]
}


def _lich_su_thanh_toan(o):
	"""Cac giao dich THANH CONG trong payment_purchase_histories.

	Tra ve [{kieu, tien, luc}]. Giao dich hong bi loai ngay o day, khong de
	no di sau vao trong.
	"""
	ra = []
	for g in (o or {}).get("payment_purchase_histories") or []:
		if not isinstance(g, dict):
			continue
		kieu = str(g.get("type") or "").strip().lower()
		if not kieu:
			continue
		ma = g.get("result_code")
		# Khong co ma ket qua thi coi la xong: vai kenh khong tra ma. Co ma
		# ma khong nam trong danh sach thanh cong thi BO, du so tien co dep.
		if ma is not None and str(ma).strip() not in MA_THANH_CONG:
			continue
		try:
			tien = float(g.get("amount") or 0)
		except (TypeError, ValueError):
			tien = 0.0
		if tien <= 0:
			continue
		ra.append({"kieu": kieu, "tien": tien, "luc": str(g.get("date") or "")})
	return ra


def nghi_cong_no(o):
	"""Don da giao xong ma Pancake khong ghi nhan dong nao.

	CHI la co de sales ra lai. Anh Viet chot 15/08/2026: tuyet doi khong cho
	may tu gan Cong no. Do tren du lieu that: suy kieu nay ra 16 don trong 7
	ngay trong khi sales chi danh dau 3 don la cong no, chenh hon nam lan -
	khong the lay lam quy tac ghi so.
	"""
	if str((o or {}).get("status_name") or "").strip().lower() != "delivered":
		return 0
	if _lich_su_thanh_toan(o):
		return 0
	for truong in ("prepaid", "transfer_money", "cash", "cod", "charged_by_card"):
		try:
			if float((o or {}).get(truong) or 0) > 0:
				return 0
		except (TypeError, ValueError):
			continue
	return 1


def _vnd(so):
	return "{:,.0f}".format(so).replace(",", ".")


def _dien_dong_thanh_toan(si, o):
	"""Dien bang cac dong thanh toan tu don Pancake, KHONG de len tay nguoi.

	Bang chi duoc dien khi no dang trong, hoac moi dong dang co deu mang co
	`do_may`. Sales sua tay mot dong la ca bang thanh cua nguoi, va tu do
	nhip dong bo 30 phut mot lan khong dung vao nua.

	Tong cac dong phai KHOP tong don thi moi ghi. Lech thi bo qua ca bang -
	de trong con hon de mot bang sai roi chan luon duong ghi so cua sales.
	"""
	from vagabond import thanh_toan_nhieu as ttn

	moi = dong_thanh_toan_pancake(o)
	if not moi:
		return
	dang_co = list(si.get(ttn.BANG) or [])
	if dang_co and not all(cint(d.get("do_may")) for d in dang_co):
		return
	if not ttn.khop_tong(moi, flt(si.get("grand_total"))):
		return
	cu = [{"pt": d.get("pt"), "so_tien": d.get("so_tien")} for d in dang_co]
	if cu == [{"pt": d["pt"], "so_tien": d["so_tien"]} for d in moi]:
		return
	si.set(ttn.BANG, [])
	for d in moi:
		si.append(ttn.BANG, {"pt": d["pt"], "so_tien": d["so_tien"],
			"ma_tham_chieu": d.get("ma_tham_chieu") or "", "do_may": 1})


def dong_thanh_toan_pancake(o):
	"""Cac dong thanh toan doc tu lich su giao dich Pancake. THUAN doi voi o.

	Anh Viet 01/09/2026: khach tra mot don bang hai duong (chuyen khoan
	truoc mot phan, toi cua hang dua not tien mat) thi phai nhap cho dung
	ban chat. Don 92857 ngay 31/08 la vi du that.

	CHI dung tu lich su giao dich, khong dung tu cac o tien. Cac o tien cua
	Pancake chong cheo nhau - `cod` gom ca tien hang lan phi ship tuy cach
	khai - nen cong chung lai thi ra so khong khop tong don, ma bang nay
	bat buoc phai khop tong don moi ghi so duoc.

	Tra list rong khi khong doc duoc du HAI kenh ro rang: mot kenh thi
	duong cu da lo, khong can bang.
	"""
	ls = _lich_su_thanh_toan(o)
	if not ls:
		return []
	dong = []
	for g in ls:
		ten_pt = pt_thanh_toan.theo_khoa_pancake(g["kieu"])
		if not ten_pt:
			# Mot kenh khong doan ra ten thi BO CA BANG: ghi thieu mot dong
			# la tong khong khop, ma tu bia mot ten phuong thuc con te hon.
			return []
		try:
			so = float(g["tien"] or 0)
		except (TypeError, ValueError):
			so = 0
		if so > 0:
			dong.append({"pt": ten_pt, "so_tien": so, "do_may": 1})
	from vagabond import thanh_toan_nhieu as ttn

	dong = ttn.gom_dong(dong)
	return dong if len(dong) >= 2 else []


def _doan_thanh_toan(o):
	"""Doan phuong thuc thanh toan tu cac o tien cua don Pancake.

	Tra (pt, ghi_chu). pt rong = chua ro, sales chon tay o man doanh thu
	truoc khi ghi so. Ca the (charged_by_card) khong phan biet duoc may
	Payoo hay ShinhanBank nen khong tu dien - so tien van vao ghi chu de
	ke toan doi soat (anh Viet chot 02/08).
	"""
	# DUONG CHINH: doc lich su giao dich. Chinh xac hon han cac o tien vi no
	# noi ro KENH nao, SO TIEN bao nhieu, LUC MAY GIO, va giao dich do co
	# thanh cong hay khong.
	ls = _lich_su_thanh_toan(o)
	if ls:
		thay, pt_ro = [], []
		for g in ls:
			ten_pt = pt_thanh_toan.theo_khoa_pancake(g["kieu"])
			nhan = ten_pt or g["kieu"]
			thay.append("%s %s%s" % (nhan, _vnd(g["tien"]), (" lúc " + g["luc"][11:16]) if len(g["luc"]) >= 16 else ""))
			if ten_pt and ten_pt not in pt_ro:
				pt_ro.append(ten_pt)
		# Nhieu kenh khac nhau tren mot don thi o `vgb_pt_thanh_toan` van
		# chi mang duoc mot ten, nen van de trong cho sales quyet. NHUNG tu
		# 01/09/2026 may dung them BANG CAC DONG: moi kenh mot dong kem so
		# tien, va o cu se mang dong lon nhat. Xem thanh_toan_nhieu.py.
		pt = pt_ro[0] if len(pt_ro) == 1 else ""
		return pt, "Pancake: " + " + ".join(thay)

	# DUONG LUI: don cu chua co lich su giao dich thi van doc cac o tien.
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


def _chuan_mst(s):
	"""Chuan hoa ma so thue ve DUNG dinh dang cua Tong cuc Thue.

	- Doanh nghiep: 10 chu so.
	- Don vi phu thuoc (chi nhanh, van phong dai dien): 13 chu so, viet
	  CO DAU GACH NGANG dang 10 so - 3 so. Thong tu 86/2024/TT-BTC hieu luc
	  06/02/2025 quy dinh cau truc N1..N10-N11N12N13. Khong co dang 4 so
	  sau gach ngang.
	- Ho kinh doanh va ca nhan: 12 chu so, chinh la SO DINH DANH CA NHAN
	  (can cuoc cong dan) cua chu ho, giu nguyen khong gach.

	Ve 12 so: Dieu 5 Thong tu 86/2024/TT-BTC quy dinh tu 01/07/2025 so dinh
	danh ca nhan THAY CHO ma so thue 10 so cu cua ho kinh doanh va ca nhan;
	co quan thue tu chuyen doi neu du lieu khop Co so du lieu quoc gia ve
	dan cu. Loan Anh bi chan ngay 14/08/2026 khi nhap 079094025262 cua HO
	KINH DOANH RAVIE - luc do ham nay moi nhan 10 va 13 so nen tra rong.

	Truoc day may bo sach ky tu khong phai so nen "0311638525-027" bi luu
	thanh "0311638525027". Hai he thong ben ngoai deu tu choi dang do:
	  - VietQR tra code 52 "Ma so thue khong chinh xac" nen dong bo ve khong
	    ra duoc ten va dia chi cong ty;
	  - m-invoice tra code 296 "Create invoice fail" nen khong ghi so duoc.
	Bat duoc 12/08/2026 tren don HDB-2026-01520, chi nhanh ACV Long Thanh.

	Tra chuoi rong neu khong phai 10, 12 hoac 13 so.
	"""
	so = re.sub(r"\D", "", str(s or ""))
	if len(so) == 10:
		return so
	if len(so) == 12:
		return so
	if len(so) == 13:
		return so[:10] + "-" + so[10:]
	return ""


def _so_hop_le(m):
	return _chuan_mst(m)


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
			"vgb_xhd_mst": _chuan_mst(hd.ma_so_thue),
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
			# Ten chi co loai hinh phap ly ma khong co ten rieng thi COI NHU
			# KHONG TRA RA. Bo trong de sales buoc phai dien tay, con hon dien
			# san mot cai ten cut roi cuoi ngay may tu xuat hoa don mang cai
			# ten do. Day dung la duong da di cua don 92409 ngay 22/08/2026:
			# to 10901 ra doi voi ten nguoi mua la "CÔNG TY CỔ PHẦN".
			if hoa_don_vat.thieu_ten_rieng(tt.get("ten")):
				frappe.log_error(
					"MST %s tra ve ten cut: %r. Da bo trong de sales dien tay."
					% (mst, tt.get("ten")),
					"ban_hang: ten phap nhan cut",
				)
				continue
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
	# To DA HUY GHI SO that (docstatus 2) thi dung lai o day, du no co mang
	# danh dau huy mem hay khong.
	#
	# Vi sao phai xet rieng: doan tim ben duoi co dieu kien vgb_huy 0, nen
	# mot to vua bi huy ghi so hang loat la coi nhu khong ton tai, va nhip
	# dong bo sau se dung LAI mot to moi cho cung ma don. To moi do lai ghi
	# so cuoi ngay va XUAT HOA DON DIEN TU lan nua. Ngay 13/08/2026 huy 135
	# to (103 trieu) vi chung da xuat hoa don ben Fabi, anh Viet phai vao
	# m-invoice huy tay tung to; de ho cua nay la lam lai dung viec do.
	#
	# Huy ghi so la quyet dinh co chu y cua nguoi, may khong duoc lang le
	# dung lai.
	da_huy = frappe.db.get_value(
		"Sales Invoice",
		{"custom_pancake_id": pid, "docstatus": 2},
		["name"],
	)
	if da_huy:
		return "da_huy_si", da_huy

	# vgb_huy: 0 la bat buoc. Danh dau huy da nha ma Pancake ra roi nen bo
	# loc nay gan nhu khong bao gio dinh, nhung neu co mot to nao con giu ma
	# (danh dau tay, du lieu cu) thi lan dong bo sau se lay chinh no ra dung
	# lai - don thanh ra khong bao gio vao doanh thu ma khong ai bao loi.
	cu = frappe.db.get_value(
		"Sales Invoice",
		{"custom_pancake_id": pid, "vgb_huy": 0},
		["name", "docstatus"],
		as_dict=True,
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
	lech_pk = _lech_pancake(o, rows, giam_don)

	if cu:
		si = frappe.get_doc("Sales Invoice", cu.name)
		si.items = []
		# Phai xoa lich thanh toan cu truoc khi doi ngay. Bang payment_schedule
		# van giu han thanh toan cua ngay dong bo truoc; khach doi ngay giao
		# trong Pancake thi lan dong bo sau day posting_date sang ngay moi, con
		# lich cu o lai ngay cu, ERPNext so hai ngay roi nem "Due Date cannot be
		# before posting date" va CHAN LUON - don do im lang khong bao gio ve.
		# Bat duoc 11/08/2026: cu 15 phut mot ban ghi Error Log "ban_hang: don
		# None" tu 10h32, la don doi ngay giao tu 10/08 sang 11/08.
		si.payment_schedule = []
	else:
		si = frappe.new_doc("Sales Invoice")

	# Gan dung nguoi mua thay vi do het vao gio chung (anh Viet 12/08/2026).
	#
	# Truoc day moi don Pancake deu mang khach "Khach le Online", ten va so
	# dien thoai that chi nam trong o ghi chu. Khach mua ca nam khong tich
	# duoc diem nao, con nhan vien muon gan dung nguoi thi phai go tay lai.
	#
	# KHONG de len khach sales da sua tay: chi dien khi hoa don con dang
	# mang gio chung. Va khong bao gio de chuoi dong bo dung lai vi mot so
	# dien thoai la lung - khach_cho_don nuot loi va tra rong.
	khach_don = khach
	from vagabond.khach_hang import la_khach_gop

	if (not cu) or la_khach_gop(si.get("customer")):
		try:
			from vagabond import nhap_khach

			m = nhap_khach.khach_cho_don(sdt, ten_khach, "Pancake")
			if m:
				khach_don = m
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: gan khach cho don Pancake")

	# DOI KHACH THI PHAI XOA LIEN HE VA DIA CHI CUA KHACH CU.
	#
	# ERPNext kiem "Contact Person does not belong to the {party}" moi lan
	# luu. Hoa don cu mang lien he cua "Khach le Online"; doi customer sang
	# khach that ma giu nguyen o lien he thi ERPNext chan, va vi chan o buoc
	# save nen CA DON DO KHONG DONG BO DUOC NUA.
	#
	# Bat duoc 13/08/2026 luc nghiem thu: nhip dong bo bao "tao_moi 0,
	# cap_nhat 0" va Error Log day 400 dong tu trua. Loi nay den tu chinh
	# viec gan dung nguoi mua lam hom 12/08, khong phai tu ban vua deploy.
	#
	# Xoa trong bon o de ERPNext tu lay lai theo khach moi. Khong tu dien
	# lien he moi o day: khach_cho_don da tao Contact roi, ERPNext se keo
	# lien he chinh cua khach do khi luu.
	if (si.get("customer") or "") != khach_don:
		# KHONG dat ten bien vong lap la "o": "o" chinh la don hang Pancake,
		# tham so cua ham nay. Dat trung ten thi sau vong lap "o" thanh mot
		# chuoi, va loi chi bung ra o cho khac han - _doan_thanh_toan(o) nem
		# "'str' object has no attribute 'get'" (bat duoc 13/08/2026 ngay
		# trong lan nghiem thu ban va).
		for truong_xoa in (
			"contact_person", "contact_display", "contact_mobile", "contact_email",
			# Dia chi cung bi kiem cung mot cho (validate_party_address_and_contact),
			# nen xoa luon. Dia chi giao cua don online nam trong ghi chu va
			# ben Van Don chu khong nam o o nay, khong mat gi.
			"customer_address", "address_display",
		):
			si.set(truong_xoa, None)

	si.update(
		{
			"company": cong_ty,
			"customer": khach_don,
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": did,
			"custom_nguon": "Pancake",
			"apply_discount_on": "Grand Total",
			# GIU LAI phan giam gia den tu diem thanh vien.
			#
			# Dong nay truoc day ghi de discount_amount VO DIEU KIEN, va nhip
			# dong bo dong vao MOI hoa don con nhap, khoang 30 phut mot lan.
			# Nghia la: thu ngan tru diem cho khach xong, khach ve, 30 phut sau
			# may keo don tu Pancake roi dat lai discount_amount bang con so
			# Pancake bao. Giam gia tu diem bien mat, nhung but tru diem trong
			# so `Vagabond So Diem` thi van con - khach mat diem ma khong duoc
			# giam dong nao, va KHONG CO THONG BAO LOI NAO CA.
			#
			# Cung mot luat voi phuong thuc thanh toan va ban dich Gemini:
			# may khong de len chu nguoi that (anh Viet chot 15/08/2026).
			"discount_amount": giam_don + _giam_tu_diem(si),
			# Chenh lech giua ban tinh cua minh va tong don ben Pancake. Bang
			# 0 la khop. Khac 0 la co mot loai gia hoac giam gia ma minh chua
			# hieu - man Doanh so ve dai bang do de ke toan dung ghi so.
			"vgb_lech_pancake": lech_pk,
			"remarks": "Pancake #%s - %s%s" % (did, ten_khach or "Khách lẻ", " - " + sdt if sdt else ""),
		}
	)
	# MAY KHONG DE LEN CHU NGUOI THAT (anh Viet chot 15/08/2026).
	#
	# Truoc day dong nay ghi de vo dieu kien moi nhip dong bo. It hai vi may
	# gan nhu luon doan ra rong. Nay may doc duoc lich su giao dich nen doan
	# ra that, va cu 30 phut mot lan se de len lua chon tay cua sales neu
	# khong chan. Cung mot luat voi ban dich Gemini khong de len chu nguoi go.
	pt_tt, ghi_tt = _doan_thanh_toan(o)
	if pt_tt and frappe.db.exists("Mode of Payment", pt_tt):
		cu = (si.get("vgb_pt_thanh_toan") or "").strip()
		do_may = cint(si.get("vgb_pt_do_may") or 0)
		if not cu or do_may:
			si.vgb_pt_thanh_toan = pt_tt
			si.vgb_pt_do_may = 1
	elif not (si.get("vgb_pt_thanh_toan") or "").strip():
		si.vgb_pt_do_may = 0
	# Bang cac dong thanh toan cho don tra bang nhieu duong. Chi dien khi
	# bang dang TRONG hoac cac dong hien co deu do may dien: nguoi da go tay
	# thi may khong dung vao, cung mot luat voi o phuong thuc o tren.
	try:
		_dien_dong_thanh_toan(si, o)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: dien dong thanh toan")
	# Co "nghi cong no" chi de sales ra lai, khong bao gio tu ghi phuong thuc.
	si.vgb_nghi_cong_no = nghi_cong_no(o)
	if ghi_tt:
		si.vgb_ghi_chu_doi_soat = ghi_tt
	# Nguoi mua tren hoa don VAT. Dong bo chay lai KHONG duoc de len thong tin
	# sales da sua tay: chi dien khi o dang trong, dang la gia tri mac dinh,
	# hoac CHUA CO MA SO THUE.
	#
	# Cai ve khong co ma so thue la bai hoc cua don 91476 (12/08/2026): luc
	# don ve thi ghi chu "De in" ben Pancake chua co gi, sales dien thong tin
	# xuat hoa don SAU do. Truoc day may chi doc ghi chu dung mot lan luc tao
	# phieu nen thong tin dien sau khong bao gio ve, hoa don thieu ma so thue
	# va dia chi. Nay lan dong bo nao cung doc lai chung nao con thieu ma so
	# thue - da co ma so thue roi thi giu nguyen, khong de len tay nguoi sua.
	cu_ten = (si.get("vgb_xhd_ten") or "").strip()
	cu_mst = (si.get("vgb_xhd_mst") or "").strip()
	if not cu_ten or cu_ten == XHD_MAC_DINH or not cu_mst:
		moi = _thong_tin_xhd(o, did)
		trong_truoc = not cu_ten or cu_ten == XHD_MAC_DINH
		for truong, gt in moi.items():
			# Doc lai ma khong ra gi thi GIU NGUYEN cai dang co. Sales go tay
			# ten khach roi ma lan dong bo sau xoa trang thi con te hon la
			# khong doc lai.
			if not str(gt or "").strip() and not trong_truoc:
				continue
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
	return _dong_bo_doanh_so(ngay)


def _loi_pancake_nguoi_doc(e):
	"""Doi mot ngoai le cua thu vien mang thanh mot cau Sales doc duoc.

	Va GIAU KHOA. Thong diep goc cua thu vien mang cong nguyen ca duong dan,
	trong do co khoa API - ngay 26/08/2026 Sales chup duoc mot man hinh co
	khoa cua tiem hien chu to o giua.
	"""
	chuoi = giau_khoa(e)
	if "403" in chuoi or "Forbidden" in chuoi:
		return (
			"Pancake đang từ chối lượt gọi (mã 403). Thường là do gọi quá dày, "
			"đợi vài phút là hết. Nếu vài tiếng vẫn vậy thì khoá API Pancake "
			"trong Cài đặt đã hết hạn."
		)
	if "401" in chuoi or "Unauthorized" in chuoi:
		return "Pancake không nhận khoá API. Vào Cài đặt dán lại khoá Pancake."
	if "429" in chuoi:
		return "Pancake chặn vì gọi quá dày (mã 429). Đợi vài phút rồi thử lại."
	for m in ("500", "502", "503", "504"):
		if m in chuoi:
			return "Máy chủ Pancake đang trục trặc (mã %s). Lát nữa thử lại." % m
	return "Chưa kéo được đơn từ Pancake: %s" % chuoi[:120]


def _dong_bo_doanh_so(ngay=None, im_lang=False):
	"""Than that cua viec dong bo. KHONG whitelist va khong nhan co tu ngoai.

	Truoc day co "im lang" duoc dat thang lam tham so cua ham whitelist.
	Frappe anh xa moi khoa trong form_dict trung ten tham so vao ham, ke ca
	ten bat dau bang gach duoi - nghia la bat ky ai co quyen ban hang cung
	mo duoc URL kem co do de TAT KHOA. Hai tab nhu vay chay song song la
	quay lai dung vu 07/08: don 91475 sinh hai hoa don. Nen co dieu khien
	phai nam o ham noi bo, ngoai tam voi cua URL.
	"""
	ngay = getdate(ngay or nowdate())
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	khoa = _khoa_dong_bo(im_lang=im_lang)
	if khoa is None:
		return {"bo_qua": "Đang có việc khác chạm vào hoá đơn, để nhịp sau."}
	# Co cho hook kiem_truoc_khi_luu biet day la MAY dong bo chu khong phai
	# nguoi bam. Don Pancake ve truoc khi biet khach tra kieu gi, chan phuong
	# thuc o day la ca nhip dong bo nem loi va khong con don nao ve he.
	# Dat tren frappe.local chu khong phai frappe.flags: local tu sach sau
	# moi request, con flags thi nguoi ta hay quen tra ve.
	frappe.local.vgb_dong_bo = True
	try:
		dau, cuoi = _khoang_unix(ngay)
		dons = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
		dons = [o for o in dons if o.get("status") in TT_DOANH_SO]

		# Pancake tra ve trung mot don thi cung khong duoc tao hai hoa don.
		da_thay, sach = set(), []
		for o in dons:
			ma = str(o.get("id") or o.get("display_id") or "")
			if ma and ma in da_thay:
				continue
			da_thay.add(ma)
			sach.append(o)
		dons = sach

		cong_ty = _cong_ty()
		khach = _khach_le()
		# da_huy dem rieng chu khong im lang bo qua: don bien mat khoi doanh
		# thu ma khong ai biet vi sao chinh la kieu loi da lam 149 don nam
		# nhap nua thang hoi dau thang 8. Dem duoc thi man hinh con noi ra.
		kq = {"tao_moi": 0, "cap_nhat": 0, "da_chot": 0, "da_huy": 0, "loi": []}
		for o in dons:
			try:
				tt, ghi_chu = _upsert_hoa_don(o, ngay, cong_ty, khach)
				if tt in ("tao_moi", "cap_nhat", "da_chot"):
					kq[tt] += 1
				elif tt == "da_huy_si":
					kq["da_huy"] += 1
				elif tt == "thieu_ma":
					kq["loi"].append(ghi_chu)
				# Ghi that sau tung don: lan chay sau (hay lan chay song song)
				# nhin thay ngay hoa don vua tao, khoi tao trung.
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(frappe.get_traceback(), "ban_hang: don %s" % o.get("display_id"))
				kq["loi"].append("Đơn %s lỗi khi tạo, xem Error Log." % o.get("display_id"))
		frappe.db.commit()
	finally:
		_mo_khoa_dong_bo(khoa)
		# Tra co ve NGAY trong finally: de sot thi phan con lai cua request
		# nay van duoc mien kiem, ma request do co the la nguoi that dang
		# bam nut Dong bo roi sua don ngay sau do.
		frappe.local.vgb_dong_bo = False
	cache_set("bh_loi_%s" % ngay, json.dumps(kq["loi"]), 6 * 3600)
	cache_set("bh_luc_%s" % ngay, str(now_datetime())[:16], 6 * 3600)
	kq["so_don_pancake"] = len(dons)
	return kq


def _sepay_theo_don(shop_id, ma_dons):
	"""Tien SePay da nhan cho tung don, doc mot lan cho ca bang doanh so.

	Noi dung chuyen khoan do Pancake sinh ra co doan S<shop>O<so don>T, day
	la mach de rang buoc mot giao dich vao dung mot don. Man chi tiet don da
	doi soat kieu nay tu truoc (Server Script "VGB - Giao dich SePay cua
	don"), nhung danh sach thi khong, nen chi "SePay" ngoai danh sach chi
	sang khi ai do go tay ma tham chieu - ma voi Chuyen khoan thi truong do
	von de trong. Ket qua: don da nhan du tien van trong nhu chua nhan
	(chi Dung bao ngay 07/08/2026 voi don 91480).

	Gom mot cau truy van cho ca ngay thay vi hoi tung don, vi mot ngay co
	sau muoi may don.
	"""
	# Truoc 13/08/2026 cho nay loc "chi nhan ma TOAN CHU SO", nen moi don tu
	# website mang ma WOOxxxx bi loai thang tu dau va KHONG BAO GIO tu khop
	# duoc, du tien da ve. Bat duoc tu don WOO2749 (1.635.000 d): giao dich
	# ACC-BTN-2026-01971 co that, noi dung
	#   "... S67355O91498T1212515039 WOO2749 0707337039 ..."
	# Mach S<shop>O<so>T mang ID NOI BO 91498, con ma hien thi WOO2749 nam
	# rieng mot tu phia sau. Nay do CA HAI duong.
	ma_dons = [str(m).strip() for m in (ma_dons or []) if str(m or "").strip()]
	shop_id = str(shop_id or "").strip()
	if not (shop_id and ma_dons):
		return {}
	so = sorted({m for m in ma_dons if m.isdigit()})
	khac = sorted({m.upper() for m in ma_dons if not m.isdigit()})
	ve = []
	if so:
		ve.append("S%sO(%s)T" % (shop_id, "|".join(so)))
	for m in khac:
		# Chan hai dau bang ky tu khong phai chu so, de "WOO274" khong an
		# nham giao dich cua "WOO2749".
		ve.append("[^0-9A-Za-z]%s[^0-9A-Za-z]" % re.escape(m))
	mau = "(%s)" % "|".join(ve)
	try:
		gds = frappe.db.sql(
			"""select name, description, deposit, withdrawal, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and description regexp %s""",
			mau,
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc giao dich SePay")
		return {}
	re_don = re.compile(r"S%sO(\d+)T" % re.escape(shop_id), re.IGNORECASE)
	re_khac = {
		m: re.compile(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(m), re.IGNORECASE)
		for m in khac
	}
	ra = {}

	def _cong(khoa, g):
		# `gd` la TEN dong sao ke. Thieu no thi khong cho nao trong he biet
		# dong nao da gach cho don nao, va phep chan mot giao dich tra hai
		# chung tu khong co gi de dua vao. Ben ma bill VGB da giu tu 24/08,
		# ben Pancake thi chua, nen mot lan chuyen khoan Pancake van co the
		# duoc tinh cho hai bill khac nhau.
		o = ra.setdefault(khoa, {"nhan": 0.0, "ma": "", "so_gd": 0, "gd": []})
		o["nhan"] += flt(g.get("deposit")) - flt(g.get("withdrawal"))
		o["so_gd"] += 1
		if g.get("name"):
			o["gd"].append(g["name"])
		if not o["ma"]:
			o["ma"] = (g.get("reference_number") or "").strip()

	for g in gds:
		mo_ta = g.get("description") or ""
		# Mot giao dich chi duoc cong cho MOT don. Uu tien ma hien thi khong
		# phai so: don WOO co ca hai dau trong noi dung, cong ca hai la mot
		# giao dich duoc tinh hai lan.
		xong = False
		for m, rx in re_khac.items():
			if rx.search(mo_ta):
				_cong(m, g)
				xong = True
				break
		if xong:
			continue
		k = re_don.search(mo_ta)
		# Chi cong cho don DUOC HOI. Don WOO co mach S<shop>O<id noi bo>T
		# mang mot so KHAC ma hien thi, khong chan thi may de ra mot khoa
		# la lung khong ai tra cuu toi.
		if k and k.group(1) in set(so):
			_cong(k.group(1), g)
	return ra


# Ten khoa dung chung cho MOI viec cham vao hoa don Sales: dong bo Pancake
# (ca nut bam tay lan nhip 30 phut) va buoc ghi so cua chuoi cuoi ngay.
KHOA_DON_SALES = "vgb_don_sales"


def _khoa_dong_bo(cho=3, im_lang=False):
	"""Chi cho MOT viec cham vao hoa don Sales tai mot thoi diem.

	Ngay 07/08/2026 nut Dong bo bi bam hai lan cach nhau 2,3 giay. Hai yeu
	cau chay song song, chua ben nao commit nen ben nay khong nhin thay hoa
	don ben kia vua tao, the la don 91475 co hai hoa don HDB-2026-00893 va
	HDB-2026-00894. Kiem "da co hoa don chua" trong ma khong the chan duoc
	chuyen nay, phai chan tu ngoai.

	Dem 11/08/2026 lai dinh mot kieu khac: nhip dong bo 30 phut va chuoi
	cuoi ngay cung go cua luc 23:00, chuoi ghi so mot don trong khi dong bo
	dang giu ban cu cua chinh don do - ERPNext nem "has been modified after
	you have opened it" va bo qua don.

	Truoc day khoa bang bo nho dem. Nay doi sang khoa TEP cua he dieu hanh:
	tien trinh chet thi he dieu hanh tu tha khoa, con khoa bo nho dem chet
	giua chung se de lai chia khoa mo coi song 5 phut, chan sach moi duong
	dong bo trong 5 phut do ma khong ai hieu vi sao.

	Khoa tep KHONG tai nhap duoc: cung mot tien trinh xin hai lan la doi
	nhau den het gio. Nen tuyet doi khong duoc long hai khoi khoa vao nhau.

	Luu y: chinh filelock cua Frappe tu ghi mot dong Error Log truoc khi nem
	LockTimeoutError, tang tren khong ngan duoc. Nen "im_lang" chi la khong
	nem loi ra cho nguoi dung, chu Error Log van co mot dong.
	Tra ve mot ExitStack, dua thang cho _mo_khoa_dong_bo.
	"""
	pila = ExitStack()
	try:
		pila.enter_context(filelock(KHOA_DON_SALES, timeout=cho))
	except LockTimeoutError:
		pila.close()
		if im_lang:
			return None
		frappe.throw(
			"Máy đang đồng bộ dở đơn của ngày này. Anh chị chờ khoảng nửa phút "
			"rồi mở lại màn hình, đừng bấm thêm lần nữa."
		)
	except Exception:
		# Khong khoa duoc thi thoi, khong duoc vi the ma chan ca nghiep vu.
		frappe.log_error(frappe.get_traceback(), "ban_hang: khong lay duoc khoa don")
	return pila


def _mo_khoa_dong_bo(pila):
	if pila is None:
		return
	try:
		pila.close()
	except Exception:
		pass


@frappe.whitelist()
def bang_doanh_so(ngay=None):
	"""Du lieu cho man 'Doanh so ngay' cua app /bep.

	KHONG lay hoa don quay: cua hang nao thi cua hang do tu quan trong man
	Doanh thu Cua hang, khong gop chung dung (anh Viet nhac 10/08/2026).
	"""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	sis = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"posting_date": ngay,
			"custom_pancake_id": ["!=", ""],
			"vgb_quay": ["in", ["", None]],
			# To DA HUY GHI SO khong con la bill cua ngay nua: no khong phai
			# doanh thu, khong phai viec phai lam, va bay ra chi lam Sales roi
			# mat (anh Viet 13/08/2026, sau lo 135 don keo nham). Van tra cuu
			# duoc tren Desk va trong bao cao Sua va huy hoa don.
			"docstatus": ["<", 2],
			"vgb_huy": 0,
		},
		fields=[
			"name",
			"docstatus",
			"grand_total",
			"remarks",
			# Ba o khach cho man danh sach va man chi tiet don Sales. Ten
			# that cua khach le nam trong remarks, con customer chi la giu
			# cho, nen phai co ca hai moi hien dung (anh Viet 01/09/2026).
			"customer",
			"customer_name",
			"vgb_khach_no",
			"custom_pancake_id",
			"custom_pancake_display_id",
			"custom_hddt_trang_thai",
			"custom_hddt_so",
			"custom_nguon",
			"vgb_pt_thanh_toan",
			# Hai co do may dat: mot de biet phuong thuc la may doan hay
			# nguoi go, mot de day chip "Nghi cong no" cho sales ra lai.
			"vgb_pt_do_may",
			"vgb_nghi_cong_no",
			"vgb_ma_tham_chieu",
			"vgb_ghi_chu_doi_soat",
			"vgb_xhd_ten",
			"vgb_xhd_mst",
			"vgb_xhd_dia_chi",
			"vgb_xhd_email",
			# Con so ERPNext tu tinh khi dong hang mang gia goc khac gia ban.
			# Danh sach doc no de gan chip "Don co giam gia", khoi phai mo
			# tung don ra moi biet (anh Viet 24/08/2026).
			"vgb_lech_pancake",
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
	# Doi soat SePay ngay tren danh sach: don nao da vao tien thi thay lien,
	# khong phai mo tung don ra xem.
	tien_sepay = _sepay_theo_don(cfg().pancake_shop_id, [s.custom_pancake_display_id for s in sis])

	# Dem don trung: mot don Pancake ma co hai hoa don la co chuyen.
	dem = {}
	for s in sis:
		dem[s.custom_pancake_id] = dem.get(s.custom_pancake_id, 0) + 1
	# Ma tham chieu trung trong cung mot ngay: khong chan luc nhap nua nhung
	# van chi ra de ke toan soat lai.
	ma_trung = _ma_trung_trong_ngay(ngay, [s.vgb_ma_tham_chieu for s in sis])

	for s in sis:
		s["can_hddt"] = 1 if s.custom_pancake_display_id in hd_cty else 0
		s["trung"] = 1 if dem.get(s.custom_pancake_id, 0) > 1 else 0
		g = tien_sepay.get(str(s.custom_pancake_display_id or ""))
		s["sepay_nhan"] = int(g["nhan"]) if g else 0
		s["sepay_ma"] = (g or {}).get("ma") or ""
		s["sepay_du"] = 1 if g and g["nhan"] >= flt(s.grand_total) - 1 else 0
	# Tong phan giam TREN DONG HANG cua tung don. Doc mot luot cho ca ngay
	# thay vi mo tung don: mot cau truy van thay vi vai chuc.
	gan_khach_vao_dong(sis)
	_gan_giam_dong(sis)
	# Cung mot phep voi man tinh tien cua cac diem ban: chip "Khong ghi so
	# duoc" phai noi CUNG MOT CAU o moi man (anh Viet 27/08/2026).
	_gan_ly_do_treo(sis)

	return {
		"ngay": str(ngay),
		"dong_bo_luc": cache_get("bh_luc_%s" % ngay) or "",
		"rows": sis,
		"loi": loi,
		"tong_nhap": sum(s.grand_total for s in sis if s.docstatus == 0),
		"tong_chot": sum(s.grand_total for s in sis if s.docstatus == 1),
		"so_don_trung": len([1 for v in dem.values() if v > 1]),
		"ly_do_treo": dict(ghi_so_dieu_kien.LY_DO),
	}


def _gan_giam_dong(sis):
	"""Gan `giam_dong` cho tung hoa don: tong tien giam tren cac dong hang.

	Anh Viet 24/08/2026 muon NHIN RA don nao la don giam gia cho khach ngay
	tren danh sach. Con so nay la chenh lech giua gia goc va gia ban, cong
	het cac dong, chu KHONG phai `discount_amount` cap don (do la khoan giam
	cho ca hoa don, mot thu khac).
	"""
	for s in sis:
		s["giam_dong"] = 0
	ten = [s.name for s in sis]
	if not ten:
		return
	try:
		dong = frappe.db.get_all(
			"Sales Invoice Item",
			filters={"parent": ["in", ten]},
			fields=["parent", "qty", "rate", "price_list_rate"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc giam gia tren dong")
		return
	gom = {}
	for d in dong:
		goc, ban = flt(d.get("price_list_rate")), flt(d.get("rate"))
		if goc > ban:
			gom[d["parent"]] = gom.get(d["parent"], 0.0) + (goc - ban) * flt(d.get("qty"))
	for s in sis:
		s["giam_dong"] = int(gom.get(s.name, 0))


@frappe.whitelist()
def chot_doanh_so(ngay=None):
	"""Submit ca loat SI nhap cua ngay. Loan Anh bam sau khi ra soat."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	ds = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"posting_date": ngay,
			"custom_pancake_id": ["!=", ""],
			"docstatus": 0,
			"vgb_quay": ["in", ["", None]],
			"vgb_huy": 0,
		},
		pluck="name",
	)
	sepay = _sepay_theo_don(
		cfg().pancake_shop_id,
		frappe.db.get_all(
			"Sales Invoice",
			filters={"name": ["in", ds or [""]]},
			pluck="custom_pancake_display_id",
		),
	)
	xong, hddt, loi = 0, 0, []
	for ten in ds:
		si = frappe.get_doc("Sales Invoice", ten)
		nhan = si.custom_pancake_display_id or si.name
		try:
			_chuan_bi_ghi_so(si, sepay)
		except frappe.ValidationError as e:
			# Thieu phuong thuc hay ma tham chieu: bao ro don nao, khong ghi so.
			frappe.local.message_log = []
			loi.append("Đơn %s: %s" % (nhan, str(e)))
			continue
		try:
			si.flags.ignore_permissions = True
			si.submit()
			frappe.db.commit()
			xong += 1
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "ban_hang chot: %s" % ten)
			loi.append("Đơn %s ghi sổ lỗi, xem Error Log." % nhan)
			continue
		da_xuat, bao = _tu_xuat_hddt(si.name)
		if da_xuat:
			hddt += 1
		elif bao:
			loi.append("Đơn %s ghi sổ xong nhưng chưa xuất được hoá đơn điện tử, máy sẽ tự xuất lại sau." % nhan)
	frappe.db.commit()
	return {"da_chot": xong, "da_xuat_hddt": hddt, "loi": loi}


@frappe.whitelist()
def ds_don_trung(ngay=None):
	"""Tim don Pancake bi tao thanh hai hoa don tro len trong mot ngay.

	Cach chon phieu giu lai, theo thu tu:
	  1. Phieu da ghi so (docstatus 1) - so da vao so sach, khong dong den.
	  2. Phieu da co so hoa don dien tu - da phat hanh ra ngoai.
	  3. Phieu tao truoc (ma nho hon).
	Nhung phieu con lai chi go duoc khi con la nhap VA chua co hoa don dien
	tu. Neu ca hai phieu deu da ghi so thi may KHONG tu go, phai ke toan
	huy dung nghiep vu.
	"""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	sis = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"posting_date": ngay,
			"custom_pancake_id": ["!=", ""],
			"vgb_quay": ["in", ["", None]],
		},
		fields=[
			"name",
			"docstatus",
			"grand_total",
			"custom_pancake_id",
			"custom_pancake_display_id",
			"custom_hddt_so",
			"creation",
		],
		order_by="name",
	)
	nhom = {}
	for s in sis:
		nhom.setdefault(s.custom_pancake_id, []).append(s)

	ra = []
	for pid, ds in nhom.items():
		if len(ds) < 2:
			continue
		ds = sorted(ds, key=lambda x: (0 if x.docstatus == 1 else 1, 0 if x.custom_hddt_so else 1, x.name))
		giu = ds[0]
		go, ket = [], []
		for x in ds[1:]:
			if x.docstatus == 1:
				ket.append("%s đã ghi sổ rồi, phải nhờ kế toán huỷ đúng nghiệp vụ." % x.name)
			elif x.custom_hddt_so:
				ket.append("%s đã có hoá đơn điện tử số %s, không gỡ tự động được." % (x.name, x.custom_hddt_so))
			else:
				go.append(x.name)
		ra.append(
			{
				"don": ds[0].custom_pancake_display_id,
				"so_tien": ds[0].grand_total,
				"giu": giu.name,
				"go": go,
				"ket": ket,
			}
		)
	return {"ngay": str(ngay), "nhom": ra, "so_nhom": len(ra)}


@frappe.whitelist()
def go_don_trung(ngay=None):
	"""Go cac hoa don thua do dong bo tao trung.

	Truoc day ham nay xoa han phieu thua. Tu 11/08/2026 khong xoa nua ma
	danh dau da huy: phieu trung cung la chung tu, va chinh cai thoi quen
	"cai nay thua thi xoa cho gon" da lam mat 37 hoa don quay Tran Cao Van.
	Phieu thua nam lai thi cung khong hai ai - no bi loc khoi moi so lieu.
	"""
	_kiem_quyen()
	kq = ds_don_trung(ngay)
	da_go, ket = [], []
	for n in kq["nhom"]:
		ket.extend(n["ket"])
		for ten in n["go"]:
			try:
				si = frappe.get_doc("Sales Invoice", ten)
				if cint(si.get("vgb_huy") or 0):
					continue
				chung_tu.danh_dau_huy(
					si, "Đơn trùng do đồng bộ, giữ phiếu %s" % n["giu"]
				)
				da_go.append(ten)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ban_hang: go don trung %s" % ten)
				ket.append("%s không gỡ được, xem Error Log." % ten)
	frappe.db.commit()
	return {"da_go": da_go, "ket": ket}


def _nhom_trung(sis):
	"""Gom hoa don theo ma don Pancake, tra ve cac nhom co tu hai phieu."""
	nhom = {}
	for s in sis:
		nhom.setdefault(s.custom_pancake_id, []).append(s)
	ra = []
	for ds in nhom.values():
		if len(ds) < 2:
			continue
		ds = sorted(ds, key=lambda x: (0 if x.docstatus == 1 else 1, 0 if x.custom_hddt_so else 1, x.name))
		go, ket = [], []
		for x in ds[1:]:
			if x.docstatus == 1:
				ket.append("%s đã ghi sổ rồi, phải nhờ kế toán huỷ đúng nghiệp vụ." % x.name)
			elif x.custom_hddt_so:
				ket.append("%s đã có hoá đơn điện tử số %s, không gỡ tự động được." % (x.name, x.custom_hddt_so))
			else:
				go.append(x.name)
		ra.append(
			{
				"don": ds[0].custom_pancake_display_id,
				"ngay": str(ds[0].get("posting_date") or ""),
				"so_tien": ds[0].grand_total,
				"giu": ds[0].name,
				"go": go,
				"ket": ket,
			}
		)
	return ra


TRUONG_TRUNG = [
	"name",
	"docstatus",
	"posting_date",
	"grand_total",
	"custom_pancake_id",
	"custom_pancake_display_id",
	"custom_hddt_so",
]


@frappe.whitelist()
def ra_trung_toan_bo():
	"""Ra ca lich su, khong bo ngay nao. Chay truoc khi dat khoa duy nhat."""
	_kiem_quyen()
	sis = frappe.db.get_all(
		"Sales Invoice",
		filters={"custom_pancake_id": ["!=", ""], "docstatus": ["<", 2]},
		fields=TRUONG_TRUNG,
		order_by="name",
		limit_page_length=0,
	)
	nhom = _nhom_trung(sis)
	return {"xet": len(sis), "nhom": nhom, "so_nhom": len(nhom)}


def ra_trung_hang_dem():
	"""2h sang: ra don trung ca lich su, co thi gui thu bao.

	Khoa duy nhat duoi co so du lieu da chan tu goc roi, cai nay la luoi thu
	hai - de neu khoa bi go hay co duong nao lot thi van co nguoi biet.
	"""
	try:
		frappe.set_user("Administrator")
		sis = frappe.db.get_all(
			"Sales Invoice",
			filters={"custom_pancake_id": ["!=", ""], "docstatus": ["<", 2]},
			fields=TRUONG_TRUNG,
			order_by="name",
			limit_page_length=0,
		)
		nhom = _nhom_trung(sis)
		if not nhom:
			return
		dong = "".join(
			"<li>Đơn <b>%s</b> ngày %s (%s đ): giữ %s%s%s</li>"
			% (
				n["don"],
				n["ngay"],
				_tien(n["so_tien"]),
				n["giu"],
				(", gỡ được " + ", ".join(n["go"])) if n["go"] else "",
				("<br><i>" + "; ".join(n["ket"]) + "</i>") if n["ket"] else "",
			)
			for n in nhom
		)
		than = (
			"<p>Máy tìm thấy <b>%d đơn</b> đang có từ hai hoá đơn bán hàng trở lên. "
			"Ghi sổ như vậy là doanh thu bị tính đôi.</p><ul>%s</ul>"
			"<p>Mở app, vào Bán hàng, Doanh thu Sales, chọn đúng ngày rồi bấm "
			"<b>Rà và gỡ phiếu trùng</b>.</p>" % (len(nhom), dong)
		)
		nguoi = _nguoi_nhan_canh_bao()
		if not nguoi:
			frappe.log_error(than[:5000], "ban_hang: co don trung ma chua khai email canh bao")
			return
		frappe.sendmail(
			recipients=nguoi,
			subject="[Vagabond] %d đơn đang có hoá đơn trùng" % len(nhom),
			message=than,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang cron ra trung")


def _nguoi_nhan_canh_bao():
	"""Danh sach email nhan thu canh bao, khai o Vagabond Settings."""
	c = cfg()
	ds = [e.strip() for e in re.split(r"[,;\s]+", c.get("email_canh_bao") or "") if "@" in e]
	return ds


def kiem_truoc_khi_luu(doc, method=None):
	"""Hook validate Sales Invoice: chan sai NGAY LUC LUU, khong doi cuoi ngay.

	Anh Viet 13/08/2026: "em cai dat khong cho phep luu hoa don neu thieu
	phuong thuc thanh toan, thieu nguon don, va tao canh bao khi ma phuong
	thuc thanh toan khong khop voi nguon don de cac ban thao tac lai ngay
	luc ay, tranh canh sai sot".

	MOT NGOAI LE BAT BUOC: nhip dong bo Pancake tao hoa don TRUOC khi biet
	khach tra kieu gi - Pancake chua ghi nhan tien thi khong co phuong thuc
	nao de dien. Chan o day ma khong tru hao thi ca nhip dong bo nem loi,
	ket qua la KHONG CON DON NAO ve he, nang hon nhieu so voi cai loi dang
	muon chan. Nen nhip dong bo bat co vgb_dong_bo va di qua.

	Con lai deu bi chan: nhap tay, quay, va moi duong sua tren Desk.
	"""
	if getattr(frappe.local, "vgb_dong_bo", False):
		return
	if cint(doc.get("vgb_huy")):
		return
	# Hoa don khong phai doanh thu ban hang cua he (hoa don cu nhap tu Fabi,
	# hoa don ke toan lap tay) thi khong ep - chung khong co nguon don.
	la_don_he = bool(
		(doc.get("custom_pancake_id") or "").strip() or (doc.get("vgb_quay") or "").strip()
	)
	if not la_don_he:
		return

	nguon = (doc.get("custom_nguon") or "").strip()
	if not nguon:
		frappe.throw(
			"Hoá đơn chưa chọn <b>nguồn đơn</b>. Vui lòng chọn nguồn rồi lưu lại, không thì cuối ngày máy không biết đối soát với sàn nào.",
			title="Thiếu nguồn đơn",
		)

	pt = (doc.get("vgb_pt_thanh_toan") or "").strip()
	if pt:
		try:
			hop_le = _pt_cho_nguon(nguon)
		except Exception:
			hop_le = []
		if hop_le and pt not in hop_le:
			frappe.throw(
				"Đơn nguồn <b>%s</b> không dùng phương thức <b>%s</b>. "
				"Chọn lại trong: %s." % (nguon, pt, ", ".join(hop_le)),
				title="Phương thức không khớp nguồn đơn",
			)
	elif not cint(doc.get("vgb_tam_tinh")):
		# Phieu TAM TINH la phieu giu mon, khach chua tra nen chua co phuong
		# thuc - do la dung. Con lai thieu phuong thuc la chan.
		frappe.throw(
			"Hoá đơn chưa chọn <b>phương thức thanh toán</b>. Vui lòng chọn rồi lưu lại, không thì cuối ngày đơn này không ghi sổ được.",
			title="Thiếu phương thức thanh toán",
		)


def chan_trung_ma_pancake(doc, method=None):
	"""Hook truoc khi luu Sales Invoice: mot ma don chi duoc mot hoa don.

	Khoa duy nhat duoi co so du lieu da chan tu goc, nhung khoa do nem loi
	SQL kho hieu. Cho nay chan som hon de nguoi dung doc duoc cau tieng Viet,
	va con chuan hoa o rong ve NULL cho khoa duy nhat khong dinh cac hoa don
	binh thuong (mot ngan hoa don deu de trong o nay thi chung khong duoc coi
	la trung nhau).
	"""
	ma = (doc.get("custom_pancake_id") or "").strip()
	if not ma:
		doc.custom_pancake_id = None
		return
	cu = frappe.db.get_value(
		"Sales Invoice",
		{"custom_pancake_id": ma, "name": ["!=", doc.name or ""], "docstatus": ["<", 2]},
		["name", "custom_pancake_display_id"],
		as_dict=True,
	)
	if cu:
		frappe.throw(
			"Đơn %s đã có hoá đơn %s rồi, không lập thêm hoá đơn thứ hai cho cùng một đơn."
			% (cu.custom_pancake_display_id or ma, cu.name),
			title="Trùng đơn",
		)


def dong_bo_doanh_so_tu_dong():
	"""Cron: tu keo doanh so hom nay, sales chi viec ra soat cuoi ngay.

	im_lang: chuoi cuoi ngay dang giu khoa thi bo qua nhip nay, khong ghi
	Error Log - do khong phai loi, 30 phut nua keo lai cung chua muon.
	"""
	try:
		frappe.set_user("Administrator")
		# Ca he dang nghi vi Pancake vua tu choi thi bo qua nhip nay. Goi vao
		# dung cai cua dang dong chi lam no dong lau hon.
		if pancake_nhip.con_nghi():
			return
		_dong_bo_doanh_so(nowdate(), im_lang=True)
		pancake_nhip.ghi_ok()
	except Exception as e:
		# KHONG NUOT NUA. Truoc 27/08/2026 cho nay chi ghi nhat ky, va suot
		# hai ngay 26-27/08 khong man hinh nao noi mot cau nao trong khi don
		# Pancake khong ve: 45 don ngay 25, 12 don ngay 26, 1 don ngay 27.
		# Anh Viet tuong du lieu bi mat. Nay ghi vao mot cho ma MOI MAN deu
		# doc duoc, xem vagabond/pancake_nhip.py.
		pancake_nhip.ghi_hong(_loi_pancake_nguoi_doc(e))
		frappe.log_error(giau_khoa(frappe.get_traceback()), "ban_hang cron")


@frappe.whitelist()
def luu_thanh_toan(si_name, pt=None, ma_tham_chieu=None):
	"""Sales luu phuong thuc thanh toan + ma tham chieu, chua ghi so."""
	_kiem_quyen()
	si = frappe.db.get_value(
		"Sales Invoice", si_name,
		["name", "custom_nguon", "docstatus", "vgb_pt_thanh_toan", "vgb_ma_tham_chieu"],
		as_dict=True,
	)
	if not si:
		frappe.throw("Không có hoá đơn %s." % si_name)
	pt = _kiem_pt(pt, si.custom_nguon)
	# Man hinh khong gui ma thi GIU ma cu, khong xoa trang - xem
	# luat_thanh_toan.ma_can_ghi.
	ma_tham_chieu = luat_thanh_toan.ma_can_ghi(
		ma_tham_chieu, si.vgb_ma_tham_chieu, pt, si.vgb_pt_thanh_toan)
	# Luu nhap thi chua bat buoc, den luc ghi so moi bat.
	ma = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
	frappe.db.set_value(
		"Sales Invoice", si_name, {"vgb_pt_thanh_toan": pt, "vgb_ma_tham_chieu": ma}
	)
	frappe.db.commit()
	return {"ok": 1, "pt": pt, "ma_tham_chieu": ma}


def _tien(n):
	"""1234567 -> 1.234.567, cho cau bao loi doc duoc."""
	return "{:,.0f}".format(flt(n)).replace(",", ".")


def _soat_sepay(si, sepay=None):
	"""Don Chuyen khoan: ngan hang phai nhan du tien moi cho ghi so.

	Anh Viet chot 07/08/2026 la chan han chu khong chi canh bao. Ghi so nghia
	la so tien do vao doanh thu chinh thuc, ma tien chua ve thi chua phai
	doanh thu.

	Van co loi ra cho truong hop that: khach chuyen roi nhung go sai noi dung
	nen SePay khong khop duoc theo ma don. Luc ay ke toan tim giao dich trong
	sao ke, go ma vao o Ma tham chieu, ghi so se qua. Nguoc lai, don nao SePay
	khop san thi may tu dien ma giao dich vao, khoi go tay.
	"""
	if (si.vgb_pt_thanh_toan or "").strip() != "Chuyển khoản":
		return
	if sepay is None:
		sepay = _sepay_theo_don(cfg().pancake_shop_id, [si.custom_pancake_display_id])
	g = (sepay or {}).get(str(si.custom_pancake_display_id or "")) or {}
	nhan = flt(g.get("nhan"))
	if nhan >= flt(si.grand_total) - 1:
		if not (si.vgb_ma_tham_chieu or "").strip() and g.get("ma"):
			si.vgb_ma_tham_chieu = g["ma"]
		return
	if (si.vgb_ma_tham_chieu or "").strip():
		return
	frappe.throw(
		"Đơn %s ghi Chuyển khoản nhưng ngân hàng mới nhận %s đ trên tổng %s đ, "
		"chưa đủ tiền nên chưa ghi sổ được. Nếu khách đã chuyển mà ghi sai nội "
		"dung khiến SePay không khớp được, anh chị tìm giao dịch trong sao kê "
		"rồi gõ mã giao dịch vào ô Mã tham chiếu, ghi sổ sẽ qua."
		% (si.custom_pancake_display_id or si.name, _tien(nhan), _tien(si.grand_total))
	)


def _chuan_bi_ghi_so(si, sepay=None):
	"""Kiem cac dieu kien bat buoc truoc khi submit mot hoa don sales."""
	pt = _nan_pt_theo_nguon(si)
	if not pt:
		frappe.throw(
			"Đơn %s chưa chọn phương thức thanh toán."
			% (si.custom_pancake_display_id or si.name)
		)
	si.vgb_pt_thanh_toan = pt
	_soat_sepay(si, sepay)
	si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, si.vgb_ma_tham_chieu)
	_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
	# Ban cong no ma khong biet no cua AI thi cuoi thang khong doi duoc.
	# Bat buoc khai khach cho rieng phuong thuc Cong no; cac phuong thuc
	# khac van de trong, vi nhieu khach khong muon de lai thong tin
	# (anh Viet 12/08/2026 - bat duoc tu don 91513 cua OSHIMA).
	if pt == "Công nợ" and (not si.customer or si.customer == KHACH_LE):
		frappe.throw(
			"Đơn %s bán công nợ nên phải chọn khách công nợ trước khi ghi sổ, "
			"không thì cuối tháng không biết đòi ai."
			% (si.custom_pancake_display_id or si.name)
		)
	if not (si.vgb_xhd_ten or "").strip():
		si.vgb_xhd_ten = XHD_MAC_DINH


@frappe.whitelist()
def luu_khach_no(si_name, khach=None):
	"""Gan khach cong no cho mot don Sales.

	Don con nhap thi doi thang customer - do moi la chu no that trong so
	cai. Don da ghi so thi KHONG duoc doi customer (bút toán đã lên sổ,
	đổi party là sai sổ), chi ghi vao truong phu vgb_khach_no de man Cong
	no phai thu va phieu de nghi thanh toan goi dung ten nguoi phai tra.
	"""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	ma = (khach or "").strip()
	if ma and not frappe.db.exists("Customer", ma):
		frappe.throw("Không có khách hàng %s trong danh mục." % ma)
	if si.docstatus == 0:
		si.customer = ma or _khach_le()
		si.vgb_khach_no = ma
		si.flags.ignore_permissions = True
		si.save()
	else:
		frappe.db.set_value("Sales Invoice", si.name, "vgb_khach_no", ma)
		_ghi_vet(si.name, "Gắn khách công nợ %s cho đơn đã ghi sổ" % (ma or "(bỏ trống)"), "")
	frappe.db.commit()
	ten = frappe.db.get_value("Customer", ma, "customer_name") if ma else ""
	return {"ok": 1, "khach": ma, "ten": ten or ma}


@frappe.whitelist()
def chot_mot_don(si_name, pt=None, ma_tham_chieu=None, khach=None):
	"""Submit mot don le, sales ra soat xong don nao chot don do."""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	if not si.custom_pancake_id:
		frappe.throw("Phiếu này không phải doanh thu sales.")
	if si.docstatus != 0:
		frappe.throw("Đơn này đã chốt rồi.")
	if ma_tham_chieu is not None:
		si.vgb_ma_tham_chieu = luat_thanh_toan.ma_can_ghi(
			ma_tham_chieu, si.vgb_ma_tham_chieu, pt, si.vgb_pt_thanh_toan)
	if pt:
		si.vgb_pt_thanh_toan = pt
	ma_kh = (khach or "").strip()
	if ma_kh:
		if not frappe.db.exists("Customer", ma_kh):
			frappe.throw("Không có khách hàng %s trong danh mục." % ma_kh)
		si.customer = ma_kh
		si.vgb_khach_no = ma_kh
	_chuan_bi_ghi_so(si)
	si.flags.ignore_permissions = True
	si.submit()
	frappe.db.commit()
	# Ghi so xong day luon hoa don dien tu. Loi thi cron moi gio bu lai.
	da_xuat, _ = _tu_xuat_hddt(si.name)
	return {"ok": 1, "name": si.name, "da_xuat_hddt": 1 if da_xuat else 0}


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
	so_mst = _chuan_mst(mst)
	if (mst or "").strip() and not so_mst:
		frappe.throw(
			"Mã số thuế phải 10 số (doanh nghiệp), 12 số (hộ kinh doanh hoặc cá "
			"nhân, chính là số căn cước của chủ hộ), hoặc 13 số dạng 10 số - 3 "
			"số cho chi nhánh (ví dụ 0311638525-027)."
		)
	ten = (ten or "").strip()
	if so_mst and not ten:
		frappe.throw("Có mã số thuế thì phải có tên pháp nhân.")
	if so_mst and hoa_don_vat.thieu_ten_rieng(ten):
		frappe.throw(hoa_don_vat.LOI_TEN_CUT)
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


QUYEN_SUA_NGAY = {"System Manager", "Accounts Manager", "Accounts User", "Sales Manager"}


@frappe.whitelist()
def doi_ngay_hoa_don(si_name, ngay=None, otp=None, ly_do=""):
	"""Chuyen mot hoa don CHUA GHI SO sang ngay khac, mac dinh la hom nay.

	Vi sao can (chi Dung 12/08/2026): luat ke toan bat xuat hoa don dien tu
	NGAY TRONG NGAY ban hang. Mot don cua hom qua bi truc trac - sai ma so
	thue, chua ve tien, m-invoice loi - thi sua xong van khong xuat duoc hoa
	don mang ngay hom qua nua. Cach dung la keo don do sang ngay dang thao
	tac roi ghi so, hoa don dien tu se mang dung ngay xuat.

	Chi doi duoc hoa don CON NHAP. Hoa don da ghi so la so tien da vao so
	sach ngay do; muon doi ngay thi ke toan phai huy roi lap lai, khong the
	sua ngam ngay sau lung so cai.
	"""
	_kiem_quyen()
	if not QUYEN_SUA_NGAY & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý hoặc kế toán mới được đổi ngày hoá đơn. "
			"Bạn cần đổi thì báo chị Dung."
		)
	si = frappe.get_doc("Sales Invoice", si_name)
	if si.docstatus != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ nên không đổi ngày được. Số tiền đã vào sổ "
			"ngày %s rồi; muốn đổi thì phải huỷ hoá đơn rồi lập lại."
			% (si.name, si.posting_date)
		)
	if si.get("custom_hddt_so"):
		frappe.throw(
			"Hoá đơn %s đã xuất hoá đơn điện tử số %s nên không đổi ngày được."
			% (si.name, si.custom_hddt_so)
		)
	moi = getdate(ngay or nowdate())
	if moi > getdate(nowdate()):
		frappe.throw("Không đẩy hoá đơn sang ngày tương lai được.")
	cu = si.posting_date
	if getdate(cu) == moi:
		return {"ok": 1, "ngay": str(moi), "doi": 0}
	cach = _otp_kiem(otp, "đổi ngày hoá đơn")
	si.set_posting_time = 1
	si.posting_date = str(moi)
	# Phai XOA lich thanh toan cu truoc khi doi ngay. Cac dong payment_schedule
	# van giu han thanh toan cua ngay cu, ERPNext so han cu voi ngay moi roi
	# bao "Ngay den han khong the truoc Posting Date" va chan luon (bat duoc
	# 12/08/2026 tren don HDB-2026-01520). Xoa di thi may tu dung lai theo
	# dieu khoan thanh toan cua khach.
	si.payment_schedule = []
	si.due_date = str(moi)
	si.flags.ignore_permissions = True
	si.save()
	_ghi_vet(
		si.name,
		"Đổi ngày hoá đơn %s sang %s%s" % (cu, moi, (" - " + ly_do) if ly_do else ""),
		cach,
	)
	frappe.db.commit()
	return {"ok": 1, "ngay": str(moi), "ngay_cu": str(cu), "doi": 1}


# ------------------------------------------------- tu ghi so cuoi ngay 23h30

def _ghi_so_mot_don(si, sepay=None):
	"""Ghi so mot hoa don roi day hoa don dien tu. Tra (xong, hddt, loi)."""
	nhan = si.get("custom_pancake_display_id") or si.name
	try:
		_chuan_bi_ghi_so(si, sepay)
	except Exception as e:
		frappe.local.message_log = []
		return 0, 0, "Đơn %s: %s" % (nhan, str(e)[:220])
	try:
		si.flags.ignore_permissions = True
		si.submit()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "ban_hang tu ghi so: %s" % si.name)
		return 0, 0, "Đơn %s ghi sổ lỗi, xem Error Log." % nhan
	da_xuat, bao = _tu_xuat_hddt(si.name)
	if da_xuat:
		return 1, 1, ""
	return 1, 0, ("Đơn %s ghi sổ xong nhưng chưa xuất được hoá đơn điện tử: %s" % (nhan, bao)) if bao else ""


def _diem_ban_hddt():
	"""Diem ban doc tu Cai dat. Truoc day la mot danh sach cung o day, mot
	danh sach nua ben khuyen_mai va mot nua ben bao_cao - sua mot cho quen
	hai cho la ba noi noi khac nhau. Xem vagabond/diem_ban.py."""
	# CA diem, ke ca diem da tat. Man Cuoi ngay ghi de tu danh sach nay:
	# neu chi lay diem dang bat thi tat mot chi nhanh roi vao do sua gio la
	# tu ghi so va xuat hoa don cua chi nhanh do bien mat khoi cau hinh, ma
	# man tinh tien van ban duoc - bill nam nhap vinh vien khong ai biet.
	return diem_ban.ds()


def _gio_hop_le(g, mac_dinh="23:00"):
	"""Chuan hoa gio dang HH:MM. Sai dinh dang thi tra ve mac dinh chu khong
	nem loi - day la job chay dem, hong gio la ca ngay khong ai xuat hoa don."""
	g = str(g or "").strip()
	m = re.match(r"^(\d{1,2}):(\d{2})$", g)
	if not m:
		return mac_dinh
	gi, ph = int(m.group(1)), int(m.group(2))
	if gi > 23 or ph > 59:
		return mac_dinh
	return "%02d:%02d" % (gi, ph)


def _goi_server_script(ten, tham_so):
	"""Goi mot Server Script kieu API cua site.

	Bo phat hanh va ky hoa don m-invoice nam trong Server Script tren site
	chu khong nam trong repo. Truoc day moi cai co lich rieng, chay le nhau
	nen thu tu de sai. Nay chuoi cuoi ngay goi thang chung theo dung thu tu.
	"""
	cu = dict(frappe.form_dict)
	try:
		for k, v in tham_so.items():
			frappe.form_dict[k] = v
		frappe.get_doc("Server Script", ten).execute_method()
		return frappe.response.get("message")
	finally:
		frappe.local.form_dict = frappe._dict(cu)


def tu_ghi_so_cuoi_ngay(bo_qua_gio=False, chay_tay=False):
	"""Chuoi cuoi ngay: ghi so, phat hanh hoa don dien tu, roi ky.

	Ham nay chay 5 phut mot lan nhung MOI NGAY CHI LAM MOT LAN, vao dung
	gio khai trong Vagabond Settings (mac dinh 23:00). Lam vay de sep doi
	duoc gio ngay tren app ma khong phai sua code va deploy lai.

	Anh Viet chot 12/08/2026: gom ca ba buoc vao mot chuoi chay lien nhau,
	xong truoc 23h30. Chi Dung so xuat hoa don sat 24h, lo nghen mang mot
	cai la to hoa don lot sang ngay hom sau - sai luat ke toan.

	Hoa don TAM TINH khong dung vao: do la phieu giu mon, khach chua tra
	tien, chua phai doanh thu. Don nao thieu dieu kien (chua chon phuong
	thuc, chuyen khoan chua ve du tien) thi BO QUA chu khong ep ghi so - de
	sang hom sau nguoi that xu ly, va co the keo sang ngay moi bang nut
	Chuyen don sang hom nay.
	"""
	c = cfg()
	if not cint(c.get("tu_ghi_so_bat") if c.get("tu_ghi_so_bat") is not None else 1):
		return
	gio = _gio_hop_le(c.get("tu_ghi_so_gio"))
	bay_gio = now_datetime().strftime("%H:%M")
	if not bo_qua_gio and bay_gio < gio:
		return
	ngay = nowdate()

	# Truoc 13/08/2026 cho nay la "da chay hom nay thi thoi": chuoi lam dung
	# MOT lan roi nghi. Don nao luc 23h00 chua du dieu kien - tien chuyen
	# khoan ve luc 23h10, sales chon phuong thuc luc 23h20 - thi nam nhap
	# VINH VIEN, vi hom sau chuoi chi quet don cua hom sau, khong ai quay lai
	# nhat. Bat duoc 13/08/2026: 149 don tu 01-04/08, tong 114 trieu, SePay
	# bao nhan du tien tu lau ma van con nhap, khong ai hay.
	#
	# Nay cac nhip 5 phut con lai trong ngay VET tiep, chi bo hai buoc phat
	# hanh va ky hang loat vi da lam roi (moi don ghi so deu tu xuat hoa don
	# rieng ngay sau do). Nhip vet bat dau bang mot cau dem: khong con don
	# nao thi thoat luon, khong ton gi.
	da_du_chuoi = str(c.get("tu_ghi_so_lan_cuoi") or "") == ngay

	quay_bat = [
		q.strip().upper()
		for q in str(c.get("tu_ghi_so_quay") or "").replace(",", "\n").splitlines()
		if q.strip()
	]
	loc_sales = {
		"posting_date": ngay,
		"custom_pancake_id": ["!=", ""],
		"docstatus": 0,
		"vgb_quay": ["in", ["", None]],
		"vgb_huy": 0,
	}
	loc_quay = {
		"posting_date": ngay,
		"docstatus": 0,
		"vgb_quay": ["in", quay_bat or [""]],
		"vgb_tam_tinh": 0,
		"vgb_huy": 0,
	}
	if da_du_chuoi and not chay_tay:
		con = frappe.db.count("Sales Invoice", loc_sales)
		if not con and quay_bat:
			con = frappe.db.count("Sales Invoice", loc_quay)
		if not con:
			return

	# Chong chay chong bang KHOA chu khong bang co "da chay hom nay" ghi
	# truoc. Ghi co truoc nghe thi chac, nhung neu job chet giua chung -
	# RQ cat o 300 giay chang han - thi co da bat, moi nhip 5 phut con lai
	# trong dem deu quay dau, ket qua la ca dem khong ghi so to nao ma
	# khong ai biet. Nay lay khoa: khong lay duoc thi nhip sau lam tiep,
	# ma ghi so von lam lai duoc (chi bat don con nhap nen khong ghi hai
	# lan). Co chi dat khi buoc ghi so da xong.
	# Keo not don Pancake truoc khi ghi so: don ve luc 22h55 ma nhip dong bo
	# sau con cach 25 phut thi lot sang ngay mai. Goi TRUOC khi lay khoa ghi
	# so - ham nay tu lay khoa rieng, long hai khoi khoa vao nhau la treo.
	#
	# Nhip VET khong keo lai don: nhip dong bo rieng 30 phut mot lan da lo
	# viec do, keo them moi 5 phut chi lam nang Pancake khong duoc gi.
	if not da_du_chuoi or chay_tay:
		try:
			_dong_bo_doanh_so(ngay)
			pancake_nhip.ghi_ok()
		except Exception as e_kd:
			# Pancake hong hay thieu khoa API thi van ghi so nhung don da ve.
			# Nhung PHAI GHI LAI la da hong, khong duoc lang le chay tiep: mot
			# cai hong khong noi ra thi khong ai chua (bai hoc 26-27/08/2026).
			frappe.db.rollback()
			frappe.local.message_log = []
			pancake_nhip.ghi_hong(_loi_pancake_nguoi_doc(e_kd))
			frappe.log_error(
				giau_khoa(frappe.get_traceback()), "ban_hang cuoi ngay: keo don lan cuoi"
			)

	# Bam tay thi phai bao ro khi may dang ban: truoc day im lang tra ve,
	# nguoi bam nhin man hinh khong doi gi ma tuong da chay xong.
	khoa = _khoa_dong_bo(cho=30 if chay_tay else 10, im_lang=not chay_tay)
	if khoa is None:
		return

	# Bao try/finally quanh CA khoi ghi so: giua chung ma nem loi thi khoa
	# tep van con nam trong tay tien trinh worker (he dieu hanh chi tha khi
	# tien trinh chet). Ket khoa la ca dong bo lan chuoi cuoi ngay dung
	# hinh cho den khi ai do khoi dong lai may chu.
	try:
		ds = frappe.db.get_all("Sales Invoice", filters=loc_sales, pluck="name")
		if quay_bat:
			ds += frappe.db.get_all("Sales Invoice", filters=loc_quay, pluck="name")

		sepay = None
		if ds:
			try:
				sepay = _sepay_theo_don(
					c.pancake_shop_id,
					frappe.db.get_all(
						"Sales Invoice",
						filters={"name": ["in", ds]},
						pluck="custom_pancake_display_id",
					),
				)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ban_hang tu ghi so: doc SePay")

		xong, hddt, loi = 0, 0, []
		for ten in ds:
			try:
				si = frappe.get_doc("Sales Invoice", ten)
			except Exception:
				continue
			if cint(si.get("vgb_tam_tinh")) or cint(si.get("vgb_huy")):
				continue
			# Don hang tang chua duoc giam doc duyet thi BO QUA, khong ep ghi
			# so. Khong bo qua thi hook before_submit nem loi va dem nao chuoi
			# cuoi ngay cung bao mot danh sach loi dai bang so don dang cho -
			# tieng keu that chim trong tieng keu gia.
			if ghi_so_dieu_kien.ly_do({
				"docstatus": si.get("docstatus"),
				"vgb_huy": si.get("vgb_huy"),
				"vgb_tam_tinh": si.get("vgb_tam_tinh"),
				"vgb_pt_thanh_toan": si.get("vgb_pt_thanh_toan"),
				"vgb_tang_duyet": si.get("vgb_tang_duyet"),
			}) in ("tang_cho_duyet", "tang_tu_choi"):
				continue
			a, b, e = _ghi_so_mot_don(si, sepay if not (si.get("vgb_quay") or "").strip() else None)
			xong += a
			hddt += b
			if e:
				loi.append(e)
		frappe.db.commit()

		# Ghi so xong roi moi danh dau va nha khoa. Hai buoc sau chi goi mang
		# m-invoice, khong dung den si.save(), nen khong can giu khoa - giu thi
		# chan mat nhip dong bo suot luc doi m-invoice tra loi.
		#
		# Bam tay GIUA NGAY thi KHONG dat co: dat vao la 23h chuoi thay co
		# trung ngay roi quay dau, toan bo don ve tu luc bam den 23h khong
		# duoc ghi so, khong phat hanh, khong ky - ma khong ai duoc bao.
		if not (chay_tay and now_datetime().strftime("%H:%M") < gio):
			frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_lan_cuoi", ngay)
			frappe.db.commit()
	finally:
		_mo_khoa_dong_bo(khoa)

	# Ghi so xong moi phat hanh, phat hanh xong moi ky. Ba buoc lien nhau
	# trong mot lan chay nen khong con canh buoc sau chay truoc buoc truoc.
	#
	# Hai Server Script kieu API duoi day KHONG tu kiem cong tac goc: truoc
	# day cai lich rieng moi kiem ho chung. Nay lich do da tat, neu o day
	# khong kiem thi ke toan tat cong tac ben m-invoice ma may van cu xuat
	# va ky - dung canh hai cong tac noi khac nhau da gay ra vu 37 hoa don
	# hom 10/08. Kiem lai o day cho mot cua.
	#
	# Nhip VET bo qua ca hai buoc: da phat hanh va ky ca luot dau roi, ma
	# moi don vua ghi so o tren deu tu day hoa don rieng qua _tu_xuat_hddt.
	# Goi lai hang loat moi 5 phut chi lam m-invoice met.
	if da_du_chuoi and not chay_tay:
		nhat_ky = "%s vét lúc %s: ghi sổ thêm %d đơn, xuất hoá đơn %d.%s" % (
			ngay,
			now_datetime().strftime("%H:%M"),
			xong,
			hddt,
			(" Còn %d đơn cần xem lại." % len(loi)) if loi else "",
		)
		frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_nhat_ky", nhat_ky[:500])
		frappe.db.commit()
		if loi:
			frappe.log_error(
				title="Vagabond: vét cuối ngày %s" % ngay,
				message=nhat_ky + "\n\n" + "\n".join(loi),
			)
		return

	ph = ky = None
	bat_ph = bat_ky = 0
	try:
		stg = frappe.get_doc("MInvoice Phat Hanh Settings")
		bat_ph = cint(stg.get("enabled"))
		bat_ky = bat_ph and cint(stg.get("tu_ky_hang_loat"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang cuoi ngay: doc cai dat m-invoice")
	if bat_ph:
		try:
			ph = _goi_server_script(
				"MInvoice - Phat hanh HD Sales (API)",
				{"che_do": "day", "ngay": ngay, "so_luong": 0, "phieu": None, "khong_commit": 0},
			)
		except Exception:
			loi.append("Phát hành hoá đơn điện tử lỗi, xem Error Log.")
			frappe.log_error(frappe.get_traceback(), "ban_hang cuoi ngay: phat hanh HDDT")
	else:
		ph = {"bo_qua": "tắt ở m-invoice"}
	if bat_ky:
		try:
			ky = _goi_server_script(
				"MInvoice - Ky hang loat hoa don",
				{"ngay": ngay, "phieu": None, "so_luong": 0},
			)
		except Exception:
			loi.append("Ký hoá đơn hàng loạt lỗi, xem Error Log.")
			frappe.log_error(frappe.get_traceback(), "ban_hang cuoi ngay: ky HDDT")
	else:
		ky = {"bo_qua": "tắt ở m-invoice"}

	nhat_ky = "%s lúc %s: ghi sổ %d đơn. Phát hành: %s. Ký: %s.%s" % (
		ngay,
		now_datetime().strftime("%H:%M"),
		xong,
		_gon(ph),
		_gon(ky),
		(" Còn %d đơn cần xem lại." % len(loi)) if loi else "",
	)
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_nhat_ky", nhat_ky[:500])
	frappe.db.commit()

	if loi:
		frappe.log_error(
			title="Vagabond: chuỗi cuối ngày %s" % ngay,
			message=nhat_ky + "\n\n" + "\n".join(loi),
		)


# ------------------------------------------------------------ don con treo
#
# Anh Viet 13/08/2026: "tai sao lai khong ghi so va xuat hoa don cho cac don
# ay o nguon sales, toan bo hoa don cuoi ngay phai tu ghi so va tu xuat ma?"
#
# Chuoi cuoi ngay VAN chan dung: don chua chon phuong thuc, don chuyen khoan
# ma ngan hang chua nhan tien thi khong duoc ghi so - ghi so la ghi doanh
# thu, ma tien chua ve thi chua phai doanh thu.
#
# Cai sai KHONG nam o cho chan. Cai sai nam o cho CHAN XONG ROI IM LANG:
# loi chi rot vao Error Log ma khong ai mo Error Log bao gio, nen 149 don
# tu 01-04/08 nam nhap ca nua thang, tong 114 trieu, khong ai hay.
#
# Ba viec o day: don_treo() liet ke ra kem LY DO tung don; canh_bao_don_treo()
# gui thu moi dem khi con don treo; keo_va_ghi_so() xu ly ca loat.

# Cau chu lay tu `ghi_so_dieu_kien` chu KHONG chep lai o day: man "Don con
# treo" va chip "Khong ghi so duoc" tren cac man tinh tien phai noi y het
# nhau ve cung mot don. Hai bang chu song song thi mot ngay nao do sua mot
# ben quen ben kia, va hai man noi hai cau khac nhau (anh Viet 27/08/2026).
LY_DO_TREO = dict(ghi_so_dieu_kien.LY_DO)
LY_DO_TREO["san_sang"] = "Đã đủ điều kiện, chỉ chờ ghi sổ"


def _ly_do_treo(r, sepay):
	"""Vi sao mot don con nam nhap. Tra ma ly do trong LY_DO_TREO."""
	pt = (r.get("vgb_pt_thanh_toan") or "").strip()
	if not pt:
		return "chua_pt"
	if pt == ghi_so_dieu_kien.HANG_TANG:
		tt = (r.get("vgb_tang_duyet") or "").strip()
		if tt == ghi_so_dieu_kien.TANG_TU_CHOI:
			return "tang_tu_choi"
		return "san_sang" if tt == ghi_so_dieu_kien.TANG_DA_DUYET else "tang_cho_duyet"
	try:
		if pt not in _pt_cho_nguon(r.get("custom_nguon")):
			return "pt_sai_nguon"
	except Exception:
		pass
	if pt != "Chuyển khoản":
		return "san_sang"
	if (r.get("vgb_ma_tham_chieu") or "").strip():
		return "san_sang"
	g = (sepay or {}).get(str(r.get("custom_pancake_display_id") or "")) or {}
	if flt(g.get("nhan")) >= flt(r.get("grand_total")) - 1:
		return "san_sang"
	return "chua_ve_tien"


def _quet_don_treo(so_ngay=14):
	"""Cac don Pancake con nhap trong so_ngay ngay gan day, kem ly do.

	KHONG lay hoa don tam tinh (phieu giu mon, khach chua tra tien) va
	khong lay don da huy mem.
	"""
	tu = add_days(nowdate(), -int(so_ngay or 14))
	ds = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"posting_date": [">=", tu],
			"custom_pancake_id": ["!=", ""],
			"docstatus": 0,
			"vgb_quay": ["in", ["", None]],
			"vgb_huy": 0,
			"vgb_tam_tinh": 0,
		},
		fields=[
			"name", "posting_date", "grand_total", "customer",
			"custom_nguon", "custom_pancake_display_id",
			"vgb_pt_thanh_toan", "vgb_ma_tham_chieu", "remarks",
			"vgb_tang_duyet",
		],
		order_by="posting_date asc, name asc",
		limit_page_length=0,
	)
	sepay = {}
	if ds:
		try:
			sepay = _sepay_theo_don(
				cfg().pancake_shop_id, [r.custom_pancake_display_id for r in ds]
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang don treo: doc SePay")
	hom_nay = str(getdate(nowdate()))
	for r in ds:
		r["ly_do"] = _ly_do_treo(r, sepay)
		r["ly_do_chu"] = LY_DO_TREO.get(r["ly_do"], r["ly_do"])
		r["hom_nay"] = 1 if str(r.posting_date) == hom_nay else 0
		g = sepay.get(str(r.custom_pancake_display_id or "")) or {}
		r["sepay_nhan"] = int(flt(g.get("nhan")))
	return ds


@frappe.whitelist()
def don_treo(so_ngay=14):
	"""Man 'Đơn còn treo' tren app: don nao chua ghi so duoc, va vi sao."""
	_kiem_quyen()
	ds = _quet_don_treo(so_ngay)
	dem, tien = {}, {}
	for r in ds:
		dem[r["ly_do"]] = dem.get(r["ly_do"], 0) + 1
		tien[r["ly_do"]] = tien.get(r["ly_do"], 0) + flt(r.grand_total)
	return {
		"so_ngay": int(so_ngay or 14),
		"rows": ds,
		"tong": len(ds),
		"tong_tien": sum(flt(r.grand_total) for r in ds),
		"dem": dem,
		"tien": tien,
		"ly_do": LY_DO_TREO,
	}


@frappe.whitelist()
def keo_va_ghi_so(ds=None, so_ngay=14, chay_thu=1):
	"""Keo don treo sang ngay hom nay roi ghi so va xuat hoa don.

	Anh Viet chot 13/08/2026 cho lo 149 don ton tu 01-04/08: keo sang ngay
	dang thao tac roi ghi so, de hoa don dien tu mang dung ngay xuat - luat
	bat xuat hoa don trong ngay ban, khong xuat lui ngay duoc.

	Danh doi: bao cao doanh thu theo NGAY cua nhung ngay cu se thieu phan
	nay, nhung doanh thu thang van du va hoa don dien tu khong pham luat.
	Ngay ban that van con trong o ghi chu cua tung don.

	chay_thu=1 chi liet ke, khong ghi gi. Luon chay thu mot lan truoc.
	"""
	_kiem_quyen()
	if not QUYEN_SUA_NGAY & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới kéo được ngày hoá đơn.")
	chay_thu = cint(chay_thu)
	if isinstance(ds, str):
		ds = json.loads(ds) if ds.strip().startswith("[") else [x for x in ds.split(",") if x.strip()]

	treo = _quet_don_treo(so_ngay)
	nhan = set(ds or [])
	if nhan:
		# Chon tay tren app: lam dung nhung don duoc tick.
		cho = [r for r in treo if r.name in nhan]
	else:
		# Ca loat: chi dung toi don DA DU DIEU KIEN cua NGAY CU. Don hom nay
		# de chuoi cuoi ngay lo, khong keo ngay cua chinh no lam gi; don chua
		# du dieu kien thi keo sang hom nay cung van khong ghi so duoc.
		cho = [r for r in treo if r["ly_do"] == "san_sang" and not r["hom_nay"]]

	kq = {
		"chay_thu": chay_thu,
		"chon": len(cho),
		"keo": 0,
		"ghi_so": 0,
		"xuat_hddt": 0,
		"tien": sum(flt(r.grand_total) for r in cho),
		"loi": [],
		"vi_du": [
			{"don": r.name, "ngay_cu": str(r.posting_date), "ma": r.custom_pancake_display_id,
			 "tien": flt(r.grand_total)}
			for r in cho[:20]
		],
	}
	if chay_thu:
		return kq

	moi = nowdate()
	for r in cho:
		nhan_don = r.custom_pancake_display_id or r.name
		try:
			si = frappe.get_doc("Sales Invoice", r.name)
			if si.docstatus != 0 or cint(si.get("vgb_huy")) or si.get("custom_hddt_so"):
				continue
			cu = str(si.posting_date)
			if cu != moi:
				# Xoa lich thanh toan cu truoc khi doi ngay: cac dong
				# payment_schedule con giu han cua ngay cu, ERPNext so han cu
				# voi ngay moi roi chan luon.
				si.set_posting_time = 1
				si.posting_date = moi
				si.payment_schedule = []
				si.due_date = moi
			_chuan_bi_ghi_so(si)
			si.flags.ignore_permissions = True
			si.submit()
			frappe.db.commit()
			if cu != moi:
				kq["keo"] += 1
				_ghi_vet(si.name, "Kéo hoá đơn treo từ %s sang %s rồi ghi sổ" % (cu, moi), "hàng loạt")
			kq["ghi_so"] += 1
		except Exception as e:
			frappe.db.rollback()
			frappe.local.message_log = []
			if len(kq["loi"]) < 50:
				kq["loi"].append("Đơn %s: %s" % (nhan_don, str(e)[:200]))
			continue
		da_xuat, bao = _tu_xuat_hddt(r.name)
		if da_xuat:
			kq["xuat_hddt"] += 1
		elif bao and len(kq["loi"]) < 50:
			kq["loi"].append("Đơn %s ghi sổ xong nhưng chưa xuất được hoá đơn: %s" % (nhan_don, bao))
	frappe.db.commit()
	return kq


def _nguoi_nhan_don_treo():
	"""Ai nhan thu canh bao don treo: khai trong Cai dat, khong thi lay cac
	tai khoan dang bat co vai ke toan hoac quan ly.

	KHONG dat ten _nguoi_nhan_canh_bao: ten do da co san o tren cho thu bao
	don trung ma. Hai ham cung ten trong mot mo dun thi cai sau de len cai
	truoc, va cho goi o tren im lang doi hanh vi - kieu loi khong ai doc ma
	nhin ra (bat duoc khi ra soat 13/08/2026)."""
	tho = str(cfg().get("email_canh_bao") or "").strip()
	if tho:
		ra = [x.strip() for x in tho.replace(",", "\n").splitlines() if x.strip() and "@" in x]
		if ra:
			return ra
	ra = []
	for vai in ("Accounts Manager", "Accounts User", "System Manager"):
		for r in frappe.get_all("Has Role", filters={"role": vai, "parenttype": "User"}, pluck="parent"):
			if r in ("Administrator", "Guest") or r in ra:
				continue
			if frappe.db.get_value("User", r, "enabled") and "@" in r:
				ra.append(r)
	return ra[:10]


def canh_bao_don_treo():
	"""23h55 moi ngay: con don nao chua ghi so duoc thi gui thu bao ngay.

	Chay SAU chuoi cuoi ngay va sau cac nhip vet, nen con lai la nhung don
	that su can nguoi xu. Khong con don nao thi khong gui gi - khong ai
	muon moi dem nhan mot cai thu "khong co gi".
	"""
	try:
		ds = _quet_don_treo(14)
		ds = [r for r in ds if r["ly_do"] != "san_sang" or not r["hom_nay"]]
		if not ds:
			return
		from vagabond.nhan_su import _khung_thu, _nut_xanh, _o_nhat, link_app

		nhan = _nguoi_nhan_don_treo()
		if not nhan:
			return
		h = frappe.utils.escape_html
		nhom = {}
		for r in ds:
			nhom.setdefault(r["ly_do"], []).append(r)
		khoi = []
		for ma_ly_do, rows in sorted(nhom.items(), key=lambda x: -len(x[1])):
			dong = [
				"%s <b>#%s</b> - %s đ%s" % (
					"/".join(reversed(str(r.posting_date).split("-"))),
					h(r.custom_pancake_display_id or r.name),
					_tien(r.grand_total),
					(" - đã nhận %s đ" % _tien(r["sepay_nhan"])) if r["ly_do"] == "chua_ve_tien" else "",
				)
				for r in rows[:12]
			]
			if len(rows) > 12:
				dong.append("<i>... và %d đơn nữa</i>" % (len(rows) - 12))
			khoi.append(
				"<p style='margin:14px 0 6px'><b>%s</b> - %d đơn, %s đ</p>%s"
				% (
					h(LY_DO_TREO.get(ma_ly_do, ma_ly_do)),
					len(rows),
					_tien(sum(flt(r.grand_total) for r in rows)),
					_o_nhat("<br>".join(dong)),
				)
			)
		than = (
			"<p style='margin:0 0 14px'>Chuỗi cuối ngày đã chạy xong nhưng còn "
			"<b>%d đơn</b> chưa ghi sổ được, tổng <b>%s đ</b>. "
			"Anh chị mở app vào Bán hàng, mục <b>Đơn còn treo</b> để xử.</p>%s"
		) % (len(ds), _tien(sum(flt(r.grand_total) for r in ds)), "".join(khoi))
		frappe.sendmail(
			recipients=nhan,
			subject="Vagabond: còn %d đơn chưa ghi sổ ngày %s" % (len(ds), nowdate()),
			message=_khung_thu("Đơn chưa ghi sổ được", than, _nut_xanh(link_app(), "Mở app xử đơn")),
			delayed=False,
			retry=2,
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: canh bao don treo")


def _gon(kq):
	"""Rut ket qua tra ve cua Server Script thanh mot cau ngan de ghi nhat ky."""
	if not isinstance(kq, dict):
		return "không rõ"
	if kq.get("bo_qua"):
		return "bỏ qua (%s)" % kq["bo_qua"]
	for k in ("tao", "so_tao", "ok", "so_ky", "da_ky", "so_luong"):
		if k in kq:
			return "%s %s" % (k, kq[k])
	return str(kq)[:120]


# Khoa bat/tat xuat hoa don dien tu theo DIEM BAN, khong con theo ten nguon.
#
# Truoc 12/08/2026 moi diem mot bo ten nguon rieng ("Tại chỗ - Trần Cao Vân")
# nen danh sach nguon cung dong vai khoa diem ban. Nay hai quay dung chung
# "Tại chỗ" va "Mang về", bat cho quay nay la bat luon quay kia - khong con
# tat rieng duoc mot chi nhanh khi no chua du dieu kien xuat hoa don.
#
# Cat rieng mot danh sach ma quay. Diem nhan don online khong co ma quay
# nen ghi dau @; Server Script doc @ thanh "vgb_quay de trong".
TRUONG_HDDT_QUAY = "vgb_hddt_quay"
HDDT_QUAY_ONLINE = "@"


def _hddt_diem_dang_bat():
	"""Ma cac diem ban dang bat xuat hoa don dien tu.

	Tra None khi chua ai luu theo khoa nay bao gio - de noi goi con biet
	duong doc lai theo kieu cu thay vi hieu nham la tat het.
	"""
	tho = str(cfg().get(TRUONG_HDDT_QUAY) or "").strip()
	if not tho:
		return None
	nhan = {
		x.strip().upper()
		for x in tho.replace(",", "\n").splitlines()
		if x.strip()
	}
	ra = set()
	for d in _diem_ban_hddt():
		khoa = d["quay"].upper() if d["quay"] else HDDT_QUAY_ONLINE
		if khoa in nhan:
			ra.add(d["ma"])
	return ra


@frappe.whitelist()
def cai_dat_cuoi_ngay():
	"""Man Cai dat tren app doc cau hinh chuoi cuoi ngay theo tung diem ban."""
	_kiem_quyen()
	c = cfg()
	quay_bat = [
		q.strip().upper()
		for q in str(c.get("tu_ghi_so_quay") or "").replace(",", "\n").splitlines()
		if q.strip()
	]
	try:
		stg = frappe.get_doc("MInvoice Phat Hanh Settings")
		dang_bat = [
			x.strip()
			for x in str(stg.get("nguon") or "").replace(",", "\n").splitlines()
			if x.strip()
		]
		bat_chung = cint(stg.get("enabled"))
		bat_ky_chung = bat_chung and cint(stg.get("tu_ky_hang_loat"))
	except Exception:
		dang_bat, bat_chung, bat_ky_chung = [], 0, 0
	hddt_diem = _hddt_diem_dang_bat()
	diem = []
	for d in _diem_ban_hddt():
		if hddt_diem is None:
			# Chua ai luu theo khoa diem bao gio: doc lai theo kieu cu, tuc
			# suy tu danh sach nguon. d["nguon"] rong thi all(...) tra True -
			# se bao la dang xuat hoa don trong khi thuc te khong loc ra to
			# nao. Phai kiem rong.
			bat_hddt = 1 if (d["nguon"] and all(n in dang_bat for n in d["nguon"])) else 0
		else:
			bat_hddt = 1 if d["ma"] in hddt_diem else 0
		diem.append(
			{
				"ma": d["ma"],
				"ten": d["ten"],
				# Sales luon tu ghi so; hai quay bat rieng bang danh sach quay.
				"ghi_so": 1 if (d["ma"] == "SALES" or d["quay"] in quay_bat) else 0,
				"hddt": bat_hddt,
				"nguon": d["nguon"],
			}
		)
	return {
		"bat": cint(c.get("tu_ghi_so_bat") if c.get("tu_ghi_so_bat") is not None else 1),
		"gio": _gio_hop_le(c.get("tu_ghi_so_gio")),
		"bat_hddt_chung": bat_chung,
		"bat_ky_chung": cint(bat_ky_chung),
		"diem": diem,
		"lan_cuoi": c.get("tu_ghi_so_lan_cuoi") or "",
		"nhat_ky": c.get("tu_ghi_so_nhat_ky") or "",
	}


@frappe.whitelist()
def luu_cai_dat_cuoi_ngay(bat=None, gio=None, ghi_so=None, hddt=None):
	"""Luu cau hinh chuoi cuoi ngay tu app.

	ghi_so va hddt la danh sach ma diem ban (SALES, TCV, NVHTN). Doi voi
	hoa don dien tu, ma diem ban duoc dich sang danh sach NGUON DON ma bo
	Server Script m-invoice dung de loc.
	"""
	_kiem_quyen()
	if not QUYEN_SUA_NGAY & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới được đổi cấu hình cuối ngày.")
	if isinstance(ghi_so, str):
		ghi_so = frappe.parse_json(ghi_so or "[]")
	if isinstance(hddt, str):
		hddt = frappe.parse_json(hddt or "[]")
	ghi_so = [str(x).strip().upper() for x in (ghi_so or [])]
	hddt = [str(x).strip().upper() for x in (hddt or [])]

	if bat is not None:
		frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_bat", cint(bat))
	if gio is not None:
		frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_gio", _gio_hop_le(gio))
	# Sales khong nam trong danh sach quay: don Sales khong mang ma quay.
	quay = [d["quay"] for d in _diem_ban_hddt() if d["quay"] and d["ma"] in ghi_so]
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_quay", "\n".join(quay))

	nguon, khoa_quay = [], []
	for d in _diem_ban_hddt():
		if d["ma"] in hddt:
			nguon += d["nguon"]
			khoa_quay.append(d["quay"].upper() if d["quay"] else HDDT_QUAY_ONLINE)
	# Danh sach nguon van phai luu: Server Script loc BANG CA HAI dieu kien,
	# nguon de chan cac hoa don ke toan tu tao tren Desk (khong mang nguon
	# nao) khoi bi xuat hoa don dien tu ngoai y muon.
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG_HDDT_QUAY, "\n".join(dict.fromkeys(khoa_quay))
	)
	try:
		frappe.db.set_value(
			"MInvoice Phat Hanh Settings",
			"MInvoice Phat Hanh Settings",
			"nguon",
			"\n".join(nguon),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: luu nguon xuat HDDT")
	frappe.db.commit()
	_ghi_vet_cai_dat(
		"Cấu hình cuối ngày: %s giờ %s, tự ghi sổ [%s], xuất hoá đơn [%s]"
		% ("bật" if cint(bat) else "tắt", _gio_hop_le(gio), ", ".join(ghi_so), ", ".join(hddt))
	)
	return cai_dat_cuoi_ngay()


def _ghi_vet_cai_dat(viec):
	"""Doi mot cau hinh anh huong tien bac thi phai biet ai doi, luc nao."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


@frappe.whitelist()
def chay_cuoi_ngay_ngay_bay_gio():
	"""Nut chay tay tren app: lam ngay chuoi cuoi ngay, khong doi toi gio."""
	_kiem_quyen()
	if not QUYEN_SUA_NGAY & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới được chạy tay.")
	# Xoa co "da chay hom nay" de chuoi chiu chay lai, roi goi thang voi
	# bo_qua_gio. KHONG duoc meo bang cach doi tu_ghi_so_gio sang 00:00 nhu
	# truoc: yeu cau web chet giua chung la gio ket vinh vien o 00:00, hom
	# sau chuoi no ngay dau ngay - luc chua co don nao - roi dat co da chay,
	# ca ngay do khong ghi so to nao ma khong ai hieu vi sao.
	frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_lan_cuoi", "")
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
	tu_ghi_so_cuoi_ngay(bo_qua_gio=True, chay_tay=True)
	return cai_dat_cuoi_ngay()
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


def _khach_cong_no(khach_no, pt):
	"""Kiem khach cho hoa don cong no. Ban cong no BAT BUOC co khach."""
	khach_no = (khach_no or "").strip()
	if (pt or "").strip() != "Công nợ":
		return ""
	if not khach_no:
		frappe.throw("Bán công nợ phải chọn khách hàng để còn theo dõi và thu sau.")
	if not frappe.db.exists("Customer", khach_no):
		frappe.throw("Không có khách hàng %s trong danh mục." % khach_no)
	return khach_no


def _khach_chon(khach_ma):
	"""Khach thu ngan chon tay tren man tinh tien. Sai ma thi bo qua chu
	KHONG chan: tien da thu cua khach roi, khong duoc de mot ma khach hong
	lam ket ca hoa don."""
	ma = (khach_ma or "").strip()
	if not ma:
		return ""
	if not frappe.db.exists("Customer", ma):
		return ""
	return ma


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
	quay=None,
	ghi_chu="",
	tam_tinh=0,
	so_ban="",
	xhd_ten="",
	xhd_mst="",
	xhd_dia_chi="",
	xhd_email="",
	khach_no="",
	ctkm_ap=None,
	ma_voucher="",
	combo_ap=None,
	otp_km="",
	khach_ma="",
	ve_diem="",
):
	"""Nhap tay doanh thu tu kenh khong co API.

	Nguon don: 4 san (GrabFood, BeFood, GreenSM Food, ShopeeFood), Khach si,
	Tai cho tung chi nhanh. San co Giam gia (chiet khau san) nen nhan
	giam_gia rieng, tru vao Grand Total giong giam gia don Pancake.

	Don san: ma don ben app CHINH LA ma tham chieu doi soat, chi nhap mot lan.
	Don quay: sales chon phuong thuc rieng roi nhap so tham chieu bill.

	Khuyen mai (11/08/2026): may khach chi gui LEN ma chuong trinh, ma voucher
	va combo da bam. So tien giam do MAY CHU tu tinh lai tu gio hang - tuyet
	doi khong nhan so tien giam tu may khach, khong thi ai mo Devtools cung
	tu ha bill cua minh ve 0.
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
		d = {"item_code": ma, "qty": sl, "rate": flt(r.get("rate") or 0)}
		# Tuy chon pha che kieu Fabi (it duong, it da, da rieng...) - chi la
		# ghi chu 0 dong tren dong mon, khong doi tien (anh Viet 09/08/2026).
		tc = (r.get("tuy_chon") or "").strip()
		# Ghi chu RIENG cua tung mon (anh Viet 10/08/2026): truoc day chi co
		# mot o ghi chu chung ca hoa don, bep khong biet loi dan la cho mon
		# nao. Voi don food app thi day chinh la cho mang ma don, in len tem
		# dan mon de shipper doc ma nhan dung tui.
		gcm = (r.get("ghi_chu") or "").strip()
		cbo = (r.get("combo") or "").strip()
		if tc or gcm or cbo:
			ten_mon = frappe.db.get_value("Item", ma, "item_name") or ma
			d["description"] = ten_mon
			if cbo:
				d["description"] += "\n%s %s" % (DAU_COMBO, cbo[:120])
			if tc:
				d["description"] += "\n[%s]" % tc[:200]
			if gcm:
				d["description"] += "\n%s %s" % (DAU_GC_MON, gcm[:200])
		rows.append(d)
	if not rows:
		frappe.throw("Đơn chưa có món nào.")

	# Chot nguon va diem ban TRUOC khi tinh khuyen mai: chuong trinh co the
	# gioi han theo quay, ma neu doan quay sau khi da tinh thi hoa don mang
	# mot quay con khuyen mai lai xet mot quay khac.
	nguon = NGUON_CU.get((nguon or "").strip(), (nguon or "").strip())
	if nguon not in [n["v"] for n in _nguon_don()]:
		frappe.throw("Nguồn đơn %s không có trong danh mục." % (nguon or "(trống)"))
	quay = _quay_cua_nguon(nguon, quay)

	# --- Khuyen mai: may chu tu tinh lai, khong tin so tu may khach ---
	# Tinh trên gio hang GOC (chua co phi giao) - khong ai duoc giam gia
	# tren phi ship.
	km_kq, km_giam = None, 0.0
	if ctkm_ap or combo_ap or (ma_voucher or "").strip():
		from vagabond import khuyen_mai as _km

		km_kq = _km.tinh(
			items,
			ctkm=ctkm_ap,
			ma=ma_voucher,
			combo=combo_ap,
			quay=quay,
			nguon=nguon,
			khach=khach_no or None,
			sdt=dien_thoai,
			ngay=ngay,
		)
		km_giam = flt(km_kq.get("tong_giam"))
		if km_kq.get("can_otp"):
			_otp_kiem(otp_km, "áp khuyến mãi")
		if km_kq.get("bo"):
			# Chuong trinh bi loai o buoc chot ma tren man hinh van hien:
			# bao ro cho thu ngan biet, khong im lang thu it tien hon roi
			# de khach cai nhau o quay.
			frappe.msgprint(
				"Không áp được: "
				+ "; ".join(
					"%s (%s)" % (b.get("ten"), b.get("ly_do")) for b in km_kq["bo"]
				),
				indicator="orange",
			)

	if flt(phi_ship) > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": flt(phi_ship)})
	hop_le = _pt_cho_nguon(nguon)
	tam_tinh = frappe.utils.cint(tam_tinh)
	if tam_tinh:
		# Bill TAM TINH (y Felix 09/08/2026): khach chua thanh toan, chi in
		# phieu tam tinh giu mon - ban dat thanh toan chung cuoi buoi, hoac
		# don sale in kem QR cho khach xac nhan. Chua biet khach tra kieu gi
		# nen chua co phuong thuc; cashier chot sau bang pos_chot.
		pt = ""
		ma_don = (ma_don or "").strip()
		ma_tc = ""
	else:
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
	# Ma noi bo mang theo NGAY: cac san quay vong ma don (GrabFood dung lai
	# GF-572 sau vai ngay) nen neu chi lay <nguon>-<ma don> thi don moi dung
	# ma cu se vuong khoa duy nhat, nhan vien khong nhap duoc don that.
	pid = "%s-%s-%s" % (
		ma_nguon,
		str(ngay).replace("-", ""),
		ma_don or ma_tc or frappe.generate_hash(length=8),
	)
	# Trung ngay trung ma van cho luu (may tu them hau to) - khong chan tay
	# nhan vien nua; danh sach se hien chip "Trùng mã" de ke toan soat lai.
	goc, lan = pid, 1
	while frappe.db.exists("Sales Invoice", {"custom_pancake_id": pid}):
		lan += 1
		pid = "%s-%d" % (goc, lan)
	si = frappe.new_doc("Sales Invoice")
	si.update(
		{
			"company": _cong_ty(),
			# Ban cong no thi hoa don phai mang ten khach that, khong duoc
			# de "khach le" - khong thi cuoi thang khong biet doi ai (anh
			# Viet 11/08/2026). Cac truong hop con lai van la khach le.
			# Thu ngan chon duoc khach ngay tren man tinh tien (anh Viet
			# 11/08/2026): chon roi thi hoa don mang ten khach do, khong don
			# vao "Khach le Online" nua - co vay moi cham soc theo hang va
			# chuc mung sinh nhat duoc.
			"customer": _khach_cong_no(khach_no, pt) or _khach_chon(khach_ma) or _khach_le(),
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": ma_don,
			"custom_nguon": nguon,
			"vgb_pt_thanh_toan": pt,
			"vgb_ma_tham_chieu": ma_tc,
			"vgb_quay": (quay or "").strip(),
			"vgb_so_ban": str(so_ban or "").strip(),
			"vgb_tam_tinh": tam_tinh,
			"vgb_ghi_chu": (ghi_chu or "").strip(),
			"vgb_xhd_ten": XHD_MAC_DINH,
			"apply_discount_on": "Grand Total",
			# Cong phan giam tu diem vao - xem _giam_tu_diem.
			"discount_amount": flt(giam_gia) + km_giam + _giam_tu_diem(si),
			"remarks": "%s #%s - %s%s%s"
			% (
				nguon,
				ma_don or "?",
				(ten_khach or "Khách lẻ").strip(),
				" - " + dien_thoai.strip() if (dien_thoai or "").strip() else "",
				" - Quầy " + (quay or "").strip() if (quay or "").strip() else "",
			),
		}
	)
	for r in rows:
		si.append("items", r)
	# Khach can hoa don cong ty va doc thong tin ngay tai quay thi dien luon.
	so_mst = _chuan_mst(xhd_mst)
	if (xhd_mst or "").strip() and not so_mst:
		frappe.throw(
			"Mã số thuế phải 10 số (doanh nghiệp), 12 số (hộ kinh doanh hoặc cá "
			"nhân, chính là số căn cước của chủ hộ), hoặc 13 số dạng 10 số - 3 "
			"số cho chi nhánh (ví dụ 0311638525-027)."
		)
	if so_mst:
		if not (xhd_ten or "").strip():
			frappe.throw("Có mã số thuế thì phải có tên pháp nhân.")
		if hoa_don_vat.thieu_ten_rieng(xhd_ten):
			frappe.throw(hoa_don_vat.LOI_TEN_CUT)
		si.vgb_xhd_ten = (xhd_ten or "").strip()
		si.vgb_xhd_mst = so_mst
		si.vgb_xhd_dia_chi = (xhd_dia_chi or "").strip()
		si.vgb_xhd_email = (xhd_email or "").strip()
	# Luu vet cac chuong trinh da ap ngay tren hoa don de bill in ra co dong
	# "Khuyen mai" va ke toan mo hoa don len la thay ngay, khoi phai doi
	# chieu sang bang ghi vet.
	if km_kq and km_kq.get("ap"):
		try:
			si.vgb_km = json.dumps(km_kq["ap"], ensure_ascii=False)[:2000]
		except Exception:
			pass
	si.flags.ignore_permissions = True
	si.save()
	frappe.db.commit()

	# Tru diem cua khach, neu thu ngan da xin ma va khach da xac nhan ngay
	# tren man tinh tien (anh Viet chot luong nay 19/08/2026).
	#
	# Dat SAU si.save() chu khong truoc: so diem duoc kiem lai lan cuoi tren
	# grand_total THAT cua to hoa don vua luu, chu khong tren con so may
	# khach gui len - QT-19. Xem diem_otp.dung_ve.
	#
	# KHONG boc trong try. Tru diem hong ma van tra ve "da chot bill" thi
	# khach ra ve tuong da duoc giam, con bill thi thu du tien. Loi phai noi
	# ra tai quay, luc con sua duoc.
	diem_da_tru = None
	if (ve_diem or "").strip():
		from vagabond import diem_otp as _diem

		diem_da_tru = _diem.dung_ve(ve_diem.strip(), si.name)
		frappe.db.commit()
		si.reload()

	if km_kq and km_kq.get("ap"):
		try:
			from vagabond import khuyen_mai as _km

			_km.ghi_su_dung(
				km_kq,
				si_name=si.name,
				quay=quay,
				nguon=nguon,
				khach=khach_no or ten_khach,
				sdt=dien_thoai,
				ngay=ngay,
				cach_duyet=("OTP" if km_kq.get("can_otp") else ""),
			)
		except Exception:
			frappe.log_error(
				title="Vagabond: ghi vet khuyen mai sau don tay",
				message=frappe.get_traceback(),
			)

	# Don kenh khac co banh o thi tru ngay tren bang kiem banh, khong doi
	# lich 5 phut (y Loan Anh 08/08/2026 - truoc day phai tao them mot don
	# Pancake gia chi de tru so, thanh ra mot khach hai bill).
	try:
		from vagabond.kiem_banh import cap_nhat_don_khac

		if any(str(r["item_code"]).upper().startswith(("BAWC", "BAWS")) for r in rows):
			cap_nhat_don_khac(ngay)
	except Exception:
		frappe.log_error(title="Vagabond: tru kiem banh sau don tay", message=frappe.get_traceback())

	return {
		"name": si.name,
		"grand_total": si.grand_total,
		"tru_diem": diem_da_tru,
		# Khoi diem de IN LEN BILL (anh Viet 13/08/2026). Tinh o day chu
		# khong doi hook on_submit: luc in bill hoa don thuong con la ban
		# nhap chua ghi so, diem thuc su chi cong khi ghi so - nhung khach
		# dang dung o quay va can biet ngay minh duoc bao nhieu diem.
		"diem": _khoi_diem_bill(si),
	}


def _khoi_diem_bill(si):
	"""So diem khach duoc tich cua rieng hoa don nay, kem so du hien co.

	Dung DUNG cong thuc cua khach_hang.cong_diem_hoa_don de con so in tren
	bill khong bao gio lech voi so thuc cong vao so diem."""
	try:
		from vagabond import khach_hang as _kh

		kh = _kh._khach_that(si)
		if not kh:
			return None
		hang = _kh._hang_cua(kh)
		if not hang:
			return None
		ty_le = flt(hang.get("tich_diem"))
		ten = frappe.db.get_value("Customer", kh, "customer_name") or kh
		du = flt(frappe.db.get_value("Customer", kh, "vgb_diem"))
		tich = round(flt(si.grand_total) * ty_le / 100.0) if ty_le > 0 else 0

		# Hoa don DA ghi so thi diem da vao so du roi. Bill in lai phai lay
		# dung so da cong va KHONG cong them lan nua, khong thi to bill in
		# lai bao khach co gap doi diem thuc te (thay khi chay that
		# 13/08/2026 tren HDB-2026-01604).
		da = frappe.db.sql(
			"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s"
			% _kh.SO_DIEM,
			(si.name, "Tich tu hoa don"),
		)
		da_cong = flt((da or [[0]])[0][0])

		# Diem khach DA TRU vao chinh don nay (tinh nang tru diem co tu
		# v181). Khong doc con so nay thi bill in ra noi khach "duoc cong
		# 17.900 diem" ma khong he nhac toi 30.000 diem ho vua tieu, va so
		# du in ra cung khong khop voi so ho tu nham trong dau.
		dung = 0.0
		try:
			from vagabond import diem_otp as _dot

			dung = flt(
				(
					frappe.db.sql(
						"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s"
						% _kh.SO_DIEM,
						(si.name, _dot.LOAI_TRU),
					)
					or [[0]]
				)[0][0]
			)
		except Exception:
			dung = 0.0
		dung = abs(dung)

		chung = {
			"khach": kh,
			"ten": ten,
			"hang": hang.get("name") or "",
			"ty_le": ty_le,
			"dung": dung,
			"giam_diem": flt(si.get("vgb_giam_diem")),
		}
		if da_cong:
			# du la o tong hop, DA gom ca but tich lan but tru cua don nay.
			# Muon ra so du truoc don thi phai go CA HAI ra, khong thi con
			# so "truoc don" van con dinh phan khach vua tieu.
			chung.update({"tich": da_cong, "du_truoc": du - da_cong + dung, "du_sau": du})
			return chung
		chung.update({"tich": tich, "du_truoc": du + dung, "du_sau": du + tich})
		return chung
	except Exception:
		# In bill KHONG duoc hong vi khoi diem. Thieu thi bill van ra, chi
		# la khong co dong diem.
		frappe.log_error(frappe.get_traceback(), "ban_hang: khoi diem bill loi")
		return None


@frappe.whitelist()
def pos_bill_them(name=None):
	"""Phan in them cua mot bill da luu: diem thanh vien va ten thu ngan.

	Duong IN LAI khong di qua tao_don_tay nen khong co san hai thong tin
	nay. Quan trong nhat la THU NGAN: ban in lai phai ghi ten nguoi da bam
	bill, khong phai ten nguoi dang cam may in - neu khong thi in lai mot
	bill cua ca truoc se doi sang ten nguoi ca sau."""
	_kiem_quyen()
	name = (name or "").strip()
	if not name or not frappe.db.exists("Sales Invoice", name):
		return {"diem": None, "thu_ngan": ""}
	si = frappe.get_doc("Sales Invoice", name)
	from vagabond import ten_nguoi as _tn

	return {
		"diem": _khoi_diem_bill(si),
		"thu_ngan": _tn.ten(si.owner or ""),
		# Nguoi ban di kem BAN IN. Anh Viet chot 02/09/2026: to hoa don in
		# ra phai co ten nguoi ban, khong chi ten thu ngan. Hai vai thuong
		# la mot nguoi tai quay, nhung don online thi khac han nhau.
		"nguoi_ban": _tn.ten((si.get("vgb_nguoi_ban") or "").strip() or si.owner or ""),
	}


@frappe.whitelist()
def ai_lam_gi(name=None):
	"""Ai đã làm gì trên một hoá đơn: bán, sửa, huỷ, cấp mã dùng điểm.

	Anh Việt chốt 02/09/2026: *"Tên người huỷ, sửa, người cấp OTP cũng cần
	hiển thị trong hoá đơn trên app để quy trách nhiệm."*

	MỘT cửa duy nhất cho cả hai màn hoá đơn và cho bản in, thay vì mỗi màn
	tự đi tra một kiểu. Trả về TÊN người, không trả địa chỉ thư.

	Chỉ ĐỌC. Không sửa gì trên hoá đơn, nên gọi lúc nào cũng an toàn.
	"""
	_kiem_quyen()
	name = (name or "").strip()
	if not name:
		return {}
	si = frappe.db.get_value(
		"Sales Invoice", name,
		["name", "owner", "creation", "modified_by", "modified",
		 "vgb_huy", "vgb_huy_boi", "vgb_huy_luc", "vgb_huy_ly_do",
		 "vgb_lan_sua", "docstatus", "vgb_nguoi_ban"],
		as_dict=True,
	)
	if not si:
		return {}
	from vagabond import ten_nguoi as _tn

	ra = {
		"ma": si.name,
		# O nguoi ban dung TRUOC nguoi lap: nguoi lap chi la nguoi bam nut,
		# co the la tai khoan may. Xem vagabond/nguoi_ban.py.
		"nguoi_ban": _tn.ten((si.get("vgb_nguoi_ban") or "").strip() or si.owner),
		"nguoi_ban_ma": (si.get("vgb_nguoi_ban") or "").strip(),
		"nguoi_lap": _tn.ten(si.owner),
		"ban_luc": str(si.creation or "")[:16],
		"lan_sua": cint(si.get("vgb_lan_sua")),
		"nguoi_sua": "",
		"sua_luc": "",
		"nguoi_huy": "",
		"huy_luc": "",
		"huy_ly_do": (si.get("vgb_huy_ly_do") or "").strip(),
		"nguoi_cap_ma_diem": "",
		"cap_ma_luc": "",
		"diem_da_dung": 0,
	}

	# Người sửa gần nhất. Chỉ hiện khi KHÁC người bán: hoá đơn nào cũng có
	# `modified_by`, mà bằng chính người lập thì đó không phải một lần sửa
	# đáng kể ai, chỉ là tiếng ồn.
	# Hai co cho NUT GAN NGUOI BAN tren man hoa don (anh Viet 02/09/2026,
	# viec 4). `chua_gan` la to nay dang nam trong ro "chua gan nguoi ban"
	# cua phan he KPI; `gan_duoc` la nguoi DANG XEM co quyen gan hay khong.
	# Tach lam hai co chu khong gop: thu ngan van can THAY to nay chua co
	# nguoi ban, chi la khong duoc tu gan.
	from vagabond import nguoi_ban as _nb

	ra["chua_gan"] = 1 if _nb.chua_gan(si.get("vgb_nguoi_ban"), si.owner) else 0
	ra["gan_duoc"] = 1 if _nb.duoc_gan(frappe.get_roles()) else 0

	if si.modified_by and si.modified_by != si.owner:
		ra["nguoi_sua"] = _tn.ten(si.modified_by)
		ra["sua_luc"] = str(si.modified or "")[:16]

	if cint(si.get("vgb_huy")):
		ra["nguoi_huy"] = _tn.ten(si.get("vgb_huy_boi") or si.modified_by)
		ra["huy_luc"] = str(si.get("vgb_huy_luc") or "")[:16]

	# Người cấp mã dùng điểm. Bút trừ điểm nằm ở sổ điểm, người bấm xác
	# nhận mã chính là chủ của bút đó.
	try:
		bt = frappe.get_all(
			"Vagabond So Diem",
			filters={"hoa_don": name, "loai": "Dung diem tru vao don"},
			fields=["owner", "creation", "diem"],
			order_by="creation desc", limit_page_length=1,
			ignore_permissions=True,
		)
		if bt:
			ra["nguoi_cap_ma_diem"] = _tn.ten(bt[0].get("owner"))
			ra["cap_ma_luc"] = str(bt[0].get("creation") or "")[:16]
			ra["diem_da_dung"] = abs(cint(bt[0].get("diem")))
	except Exception:
		# Sổ điểm hỏng KHÔNG được chặn màn hoá đơn: thiếu một dòng còn hơn
		# không mở được tờ hoá đơn.
		pass
	return ra


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
	# Don noi bo hang OWNER: tuyet doi khong xuat hoa don dien tu.
	#
	# Chan o BACKEND chu khong chi an nut tren giao dien: nut an chan duoc
	# nguoi bam nut, con duong tu dong tu_xuat_hddt va duong goi ham thang
	# tu Desk thi khong. Hoa don da gui sang co quan thue rat kho go lai.
	noi_bo.chan_hoa_don_dien_tu(si)

	hd = frappe.db.get_value(
		"Vagabond Hoa Don",
		{"ma_don": si.custom_pancake_display_id},
		["ma_so_thue", "ten_cong_ty", "dia_chi", "email"],
		as_dict=True,
	)
	# Nguoi mua lay tu chinh hoa don nay. Mot don = mot hoa don VAT, khong gop.
	ten_mua = (si.vgb_xhd_ten or "").strip()
	# m-invoice nhan MST chi nhanh CO gach ngang, khong co thi tra loi 296.
	mst_mua = _chuan_mst(si.vgb_xhd_mst)
	dc_mua = (si.vgb_xhd_dia_chi or "").strip()
	em_mua = (si.vgb_xhd_email or "").strip()
	if not ten_mua and hd:
		# Hoa don cu tao truoc khi co bon truong nay
		ten_mua = (hd.ten_cong_ty or "").strip()
		mst_mua = _chuan_mst(hd.ma_so_thue)
		dc_mua = (hd.dia_chi or "").strip()
		em_mua = (hd.email or "").strip()
	if not ten_mua:
		frappe.throw(
			"Đơn %s chưa có tên khách xuất hoá đơn. Mở đơn ở màn Doanh số, "
			"điền khối Hoá đơn điện tử rồi xuất lại." % si_name
		)
	la_phap_nhan = bool(mst_mua)
	# CUA CUOI CUNG TRUOC KHI TO HOA DON RA KHOI HE THONG.
	#
	# Ba cua tren (dong bo Pancake, luu_xhd, xhd_khach_luu) deu da chan, cua
	# nay chan lan nua vi duong tu dong `tu_xuat_hddt` chay luc 23h30 khong
	# di qua ba cua kia: no doc thang truong da luu tu truoc. Don 92409 vao
	# he ngay 22/08 luc 19h32, den 23h01 moi ky - neu chi chan luc nhap thi
	# nhung to da nam san trong co so du lieu van ra duoc.
	#
	# Hoa don da gui co quan thue rat kho go lai, nen tha dung lai o day va
	# bat nguoi sua ten, con hon de mot to sai bay sang co quan thue.
	if la_phap_nhan and hoa_don_vat.thieu_ten_rieng(ten_mua):
		frappe.throw(
			"Đơn %s có mã số thuế %s nhưng tên người mua đang là %r, chuỗi này "
			"chỉ có loại hình doanh nghiệp chứ không có tên riêng. %s"
			% (si_name, mst_mua, ten_mua, hoa_don_vat.LOI_TEN_CUT)
		)

	c = cfg()
	ts = flt(c.minvoice_ma_thue or 8)
	host, token = _minvoice_login(c)

	# DIEN GIAI BAT BUOC TREN TO THAY THE (Khoi 3, anh Viet 24/08/2026).
	#
	# Nghi dinh 123/2020 buoc to thay the phai ghi ro no thay cho to nao.
	# Hom nay ke toan van xuat to thay the bang tay ben M-Invoice, va duong
	# nay dung lai truoc do vi `chan_hoa_don_dien_tu` khong cho xuat lai mot
	# don da co so hoa don. Nhung khi nao noi API xuat thay the thang tu ERP
	# thi cau nay phai co san, khong phai nho ra vao dung hom do.
	#
	# Khong can them truong nao: to thay the xuat tu CHINH don nay, nen to cu
	# la so hoa don dang nam tren don, va co `custom_hddt_sai_sot` la dau
	# hieu ke toan da xac nhan to cu sai.
	cau_thay_the = ""
	if cint(si.get("custom_hddt_sai_sot") or 0):
		_mau_cu, _kh_cu = hoa_don_vat.mau_va_ky_hieu(si.get("custom_hddt_ky_hieu"))
		cau_thay_the = hoa_don_vat.dien_giai_thay_the(
			si.get("custom_hddt_so"), _kh_cu, si.posting_date, _mau_cu
		)

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
				"inv_itemName": (
					hoa_don_vat.chen_dien_giai(r.item_name, si.get("custom_hddt_so"),
						_kh_cu, si.posting_date, _mau_cu)
					if (cau_thay_the and i == 1) else r.item_name
				),
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
				"inv_paymentMethodName": pt_thanh_toan.ma_minvoice(si.vgb_pt_thanh_toan),
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


def _tu_xuat_hddt(si_name):
	"""Day mot hoa don da ghi so sang m-invoice. Tra (thanh_cong, ghi_chu).

	KHONG duoc lam hong viec ghi so: hoa don da submit va commit roi, m-invoice
	loi thi chi ghi log de con bu sau, tuyet doi khong nem loi ra ngoai.

	Anh Viet chot 07/08/2026: MOI hoa don ban ra deu xuat, khong rieng don co
	yeu cau hoa don cong ty. Don khong khai nguoi mua thi mang ten mac dinh
	"Ban cho nguoi tieu dung".
	"""
	c = cfg()
	# O cai dat con de trong (chua ai vao tick) thi coi nhu bat, de lan deploy
	# dau tien da chay dung ngay.
	if c.get("tu_xuat_hddt") is not None and not int(c.get("tu_xuat_hddt") or 0):
		return False, ""
	if not (c.get("minvoice_host") or "").strip():
		return False, ""
	try:
		xuat_hoa_don_dien_tu(si_name)
		return True, ""
	except Exception as e:
		frappe.db.rollback()
		frappe.local.message_log = []
		frappe.log_error(frappe.get_traceback(), "ban_hang: tu xuat HDDT %s" % si_name)
		return False, "%s: %s" % (si_name, str(e)[:200])


@frappe.whitelist()
def xuat_hddt_con_thieu(ngay=None, so_ngay=7):
	"""Bu hoa don dien tu cho nhung don da ghi so ma chua xuat.

	Dung cho ba viec: don ghi so truoc khi co co che tu xuat; don ma
	m-invoice tu choi luc do (mat mang, het so); va cron chay lai moi gio.
	"""
	_kiem_quyen()
	return _xuat_hddt_con_thieu(ngay, so_ngay)


def _xuat_hddt_con_thieu(ngay=None, so_ngay=7):
	loc = {"docstatus": 1, "custom_pancake_id": ["!=", ""]}
	if ngay:
		loc["posting_date"] = getdate(ngay)
	else:
		loc["posting_date"] = [">=", add_days(nowdate(), -int(so_ngay or 7))]
	# Loc "chua co so hoa don" bang Python chu khong bang bo loc cua Frappe:
	# ["in", ["", None]] dich ra SQL la IN ('', NULL), ma trong SQL khong gia
	# tri nao "bang" NULL - dong nao de trong that su se bi bo sot.
	ds = [
		r.name
		for r in frappe.db.get_all(
			"Sales Invoice", filters=loc, fields=["name", "custom_hddt_so"], order_by="name"
		)
		if not (r.custom_hddt_so or "").strip()
	]
	xong, loi = [], []
	for ten in ds:
		ok, bao = _tu_xuat_hddt(ten)
		if ok:
			xong.append(ten)
		elif bao:
			loi.append(bao)
	return {"xet": len(ds), "da_xuat": xong, "loi": loi}


def xuat_hddt_con_thieu_tu_dong():
	"""Cron moi gio: don nao ghi so roi ma chua co hoa don dien tu thi xuat."""
	try:
		frappe.set_user("Administrator")
		kq = _xuat_hddt_con_thieu(None, 7)
		if kq["loi"]:
			frappe.log_error("\n".join(kq["loi"])[:5000], "ban_hang: bu HDDT con thieu")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang cron HDDT")


# ---------------------------------------------------------------- quay (POS)
# Vong doi bill quay, thay the Fabi tinh tien (anh Viet 09/08/2026).
# Moi quay tu quan bill cua minh: tu xem, tu sua, tu xoa, tu ghi so tai cho -
# hai quay o hai dia diem, khong di vong qua man Doanh thu Sales cua ai ca.

import hashlib

# Tien to ma bill KHONG con mot minh VGB nua (anh Viet 31/08/2026): bill moi
# o Tran Cao Van mang TCV, NVHTN mang NVH, Sales Online mang SOL. Bang tien to
# va bang chu sinh ma nam ben `ma_bill.py` - THUAN, kiem thu duoc khong can
# site - va CA man hinh lan may chu deu doc tu do, khong noi nao chep lai.
#
# VGB o lai trong bang doc vinh vien: hon hai nghin bill cu mang tien to do,
# bo ra la sao ke cu mat duong doi soat.
#
# Mau moi CHAT hon mau cu `VGB[A-Z0-9]{5}`: no chi nhan dung bang chu sinh ma,
# thieu B I O Z 0 1 2. Nho vay mot chuoi rac trong sao ke nhu "TCVB1OZ0" khong
# con khop bua. Da quet 2.914 giao dich thang 8: VGB khop 11 lan, deu la ma
# that; TCV, NVH, SOL khong khop nham lan nao.
RE_MA_BILL = ma_bill.RE_MA


def _sepay_theo_ma_bill(ds_ma, so_ngay=45):
	"""Tien SePay da nhan theo MA BILL QUAY (VGBxxxxx trong noi dung CK).

	Khac voi don Pancake khop mach S<shop>O<don>T, bill quay in ma VGB len
	ma QR nen ngan hang tra description chua nguyen ma do.

	Ba cho da sua ngay 24/08/2026, xem `chiem_sao_ke.py` cho ly do day du:

	  - GOM TRUNG mot ma xuat hien nhieu lan trong cung mot dong. Truoc day
	    `findall` khong gom nen ngan hang de ma o ca noi dung lan o tham
	    chieu la so tien duoc cong hai lan cho chinh bill do.
	  - BO QUA dong mang HAI ma bill khac nhau. Khach tra hai bill trong mot
	    lan chuyen thi may khong biet chia cho ai; cong du cho ca hai la nhan
	    doi tien. Nhung dong do tra ve trong `bo_qua` de man hinh chi ra cho
	    nguoi khop tay, chu khong im lang nuot mat.
	  - GIU LAI MA DONG SAO KE (`gd`). Truoc day cau SQL khong lay cot `name`
	    nen khong noi nao trong he biet dong nao da bi gach cho bill nao, va
	    khong the co bat ky phep chan trung nao.

	Them cua so ngay: mot ma bill sinh ngau nhien 5 ky tu se den luc lap lai.
	Khong gioi han ngay thi mot lan chuyen tu thang truoc van khop mai mai.

	Tra ve (theo_ma, bo_qua).
	"""
	ds_ma = [str(m).strip().upper() for m in (ds_ma or []) if RE_MA_BILL.fullmatch(str(m or "").strip().upper())]
	if not ds_ma:
		return {}, []
	from frappe.utils import add_days

	n = max(1, min(cint(so_ngay) or 45, 180))
	mau = "(%s)" % "|".join(sorted(set(ds_ma)))
	try:
		gds = frappe.db.sql(
			"""select name, description, deposit, withdrawal, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and date >= %s
			and (description regexp %s or reference_number regexp %s)""",
			(add_days(nowdate(), -n), mau, mau), as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc SePay theo ma bill")
		return {}, []
	dong = []
	for g in gds:
		dong.append({
			"ten": g.get("name"),
			# Ghep ca hai o: ngan hang doi khi day ma sang o tham chieu.
			"mo_ta": "%s %s" % (g.get("description") or "", g.get("reference_number") or ""),
			"tien": flt(g.get("deposit")) - flt(g.get("withdrawal")),
			"tham_chieu": (g.get("reference_number") or "").strip(),
		})
	theo_ma, bo_qua = chiem_sao_ke.cong_tien(dong, ds_ma, RE_MA_BILL)
	tc = {d["ten"]: d["tham_chieu"] for d in dong}
	for m, o in theo_ma.items():
		o["ma"] = next((tc.get(x) for x in o["gd"] if tc.get(x)), "")
	return theo_ma, bo_qua


def _sepay_bill(ma):
	"""Bang ket qua cua MOT ma bill. Duong tat cho cac cho chi can mot ma."""
	theo_ma, _bo = _sepay_theo_ma_bill([ma])
	return theo_ma.get(str(ma or "").strip().upper()) or {}


# ==================================================== KHOP THEO SO TIEN VA GIO
#
# ANH VIET 31/08/2026, 23h:
#
#   "Quá trời hoá đơn chuyển khoản bên điểm bán Quận 1 hôm nay sao cứ bị chờ
#    tiền về thế này? Hoá đơn chuyển khoản thì ngay lập tức đã có SePay đồng
#    bộ về để khớp trong vòng có mấy giây thôi mà."
#
# SePay khong hong. Hom do ve du 90 giao dich, dung gio dung so. Cai hong la
# PHEP KHOP: may chi biet tim ma bill ben trong noi dung chuyen khoan, ma quet
# ca thang 8 thi trong 2.914 giao dich chi 11 giao dich mang ma bill. Noi dung
# ngan hang tra ve co dang:
#
#   Q00033k5p6  VAGABOND1 1  QR   25622 5MQJ9- Ma GD ACSP/ XR703682
#
# Do la chuoi ngan hang tu sinh cho ma QR cua DIEM BAN, khong phai noi dung
# minh dat trong ma QR cua app. Nghia la duong khop theo ma gan nhu chua bao
# gio chay cho bill quay, khong phai hong rieng hom do.
#
# VI SAO KHONG GHI GI XUONG CO SO DU LIEU
# ---------------------------------------
# Phep nay chay luc DOC man hinh, khong luu ket qua. Gach nham mot giao dich
# vao sai bill la sai doanh thu cua CA HAI bill, ma sai doanh thu thi kho lan
# ra hon nhieu so voi de trong. Tinh lai moi lan mo man thi re, luon dung theo
# du lieu moi nhat, va sai thi tu het khi du lieu ve du.
#
# NO KHONG MO CONG GHI SO
# -----------------------
# `ghi_so_dieu_kien` giu nguyen: khop theo so tien chi lam SANG man hinh, chu
# khong bien mot bill dang treo thanh bill ghi so duoc. Mot noi tinh mot noi
# kiem (QT-19), va noi kiem van la `ghi_so_dieu_kien`.


def _phut_trong_ngay(moc):
	"""So phut ke tu dau ngay cua mot moc thoi gian. None neu khong doc duoc."""
	if not moc:
		return None
	try:
		d = get_datetime(moc)
	except Exception:
		return None
	return d.hour * 60 + d.minute + d.second / 60.0


def _gd_ngay(ngay):
	"""Moi khoan TIEN VE trong mot ngay, kem gio. [{ten, tien, phut, mo_ta}].

	Lay gio theo `creation` chu khong theo o `date`: `date` chi la ngay, con
	SePay day giao dich ve trong vai giay nen `creation` sat gio khach chuyen.
	Dong nao `creation` roi sang ngay khac (day bu, dong bo lai) thi bo ra chu
	khong doan gio, vi doan gio la gach nham.
	"""
	try:
		gds = frappe.db.sql(
			"""select name, description, reference_number, deposit, creation, date
			from `tabBank Transaction`
			where docstatus < 2 and date = %s and deposit > 0""",
			(str(getdate(ngay)),), as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc sao ke trong ngay")
		return []
	ra = []
	for g in gds:
		if str(getdate(g.get("creation"))) != str(getdate(ngay)):
			continue
		p = _phut_trong_ngay(g.get("creation"))
		if p is None:
			continue
		ra.append({
			"ten": g.get("name"),
			"tien": flt(g.get("deposit")),
			"phut": p,
			"mo_ta": "%s %s" % (g.get("description") or "", g.get("reference_number") or ""),
			"tham_chieu": (g.get("reference_number") or "").strip(),
		})
	return ra


def _khop_theo_tien(ds, ngay, theo_ma=None):
	"""Duong khop thu hai cho cac bill chuyen khoan CHUA khop duoc theo ma.

	Gan len tung dong cua `ds`:
	  sepay_duong     'ma' | 'so_tien' | 'phan_van' | ''
	  sepay_nhan      so tien coi nhu da nhan (chi tang khi khop chac chan)
	  sepay_gd        ten dong sao ke da gach, de nguoi con lan ra duoc
	  sepay_phan_van  so duong dang phan van, khi co tu hai

	Tra ve nhung giao dich KHONG bill nao nhan la cua minh.
	"""
	con_gd = _gd_ngay(ngay)
	if not con_gd:
		return []
	# Dong nao da bi mot bill gach theo MA thi tien do co chu roi.
	da_gach = set()
	for o in (theo_ma or {}).values():
		for t in ((o or {}).get("gd") or []):
			da_gach.add(t)
	# Va dong nao mang bat ky ma bill nao cung khong con tu do, ke ca ma cua
	# bill ngoai danh sach dang xem (ngay khac, quay khac).
	con_gd = [
		g for g in con_gd
		if g["ten"] not in da_gach and not RE_MA_BILL.search((g["mo_ta"] or "").upper())
	]
	if not con_gd:
		return []
	bills = []
	for r in ds or []:
		if (r.get("vgb_pt_thanh_toan") or "") != "Chuyển khoản":
			continue
		if r.get("vgb_huy") or r.get("sepay_du"):
			continue
		if flt(r.get("grand_total")) <= 0:
			continue
		p = _phut_trong_ngay(r.get("creation"))
		if p is None:
			continue
		bills.append({"ma": r.get("name"), "tien": flt(r.get("grand_total")), "phut": p})
	if not bills:
		return con_gd
	kq = khop_tien.de_xuat(bills, con_gd)
	chac, phan_van = kq.get("chac") or {}, kq.get("phan_van") or {}
	for r in ds or []:
		g = chac.get(r.get("name"))
		if g:
			r["sepay_nhan"] = flt(g.get("tien"))
			r["sepay_du"] = 1 if flt(g.get("tien")) >= flt(r.get("grand_total")) - 1 else 0
			r["sepay_duong"] = "so_tien"
			r["sepay_gd"] = g.get("ten")
		elif phan_van.get(r.get("name")):
			r["sepay_duong"] = "phan_van"
			r["sepay_phan_van"] = len(phan_van[r.get("name")])
	# Dong nao da co bill nhan, du la chac hay phan van, deu khong con tu do.
	het = set()
	for g in chac.values():
		het.add(g.get("ten"))
	for ds_g in phan_van.values():
		for g in ds_g:
			het.add(g.get("ten"))
	return [g for g in con_gd if g["ten"] not in het]


def _gd_chua_ai_nhan(ngay=None):
	"""Cac khoan tien ve trong ngay ma KHONG bill nao da luu nhan la cua minh.

	Man tinh tien hoi lien tuc trong luc cho khach chuyen, nen ket qua giu
	tam 8 giay: du de man hinh sang gan nhu tuc thi, va du ngan de khong bao
	tien ve muon.
	"""
	ngay = str(getdate(ngay or nowdate()))
	kh = "vgb:gd_chua_ai_nhan:%s" % ngay
	cu = cache_get(kh)
	if cu is not None:
		return cu
	ds = frappe.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay, "docstatus": ["<", 2], "vgb_pt_thanh_toan": "Chuyển khoản"},
		fields=["name", "creation", "grand_total", "vgb_pt_thanh_toan", "vgb_ma_tham_chieu", "vgb_huy"],
		limit_page_length=0,
	)
	theo_ma, _bo = _sepay_theo_ma_bill([r.vgb_ma_tham_chieu for r in ds])
	for r in ds:
		g = theo_ma.get(str(r.vgb_ma_tham_chieu or "").upper()) or {}
		r["sepay_du"] = 1 if flt(g.get("nhan")) >= flt(r.grand_total) - 1 else 0
	con = _khop_theo_tien(ds, ngay, theo_ma)
	cache_set(kh, con, 8)
	return con


# =========================================================== BA DUONG KHOP TIEN
#
# Anh Viet 27/08/2026, bill HDB-26-08-03877 cua don Pancake 92564:
#
#   "Bill HDB-26-08-03877 ghi Chuyen khoan nhung ngan hang moi nhan 0 d
#    tren tong 945.000 d."
#
# Tien ve THAT, tu 25/08 luc 14:47. Dong sao ke ACC-BTN-2026-03358, 945.000 d,
# noi dung "Qalmio7806 PANCAKE2278 4 S67355O92564T2506240563 92564 0776996585".
# Mach S67355O92564T nam ro rang trong do.
#
# VI SAO MAN QUAY DOC RA 0
# ========================
# `pos_ghi_so` hoi tien qua `_sepay_bill(ma_tham_chieu)`, ma duong do chi biet
# MOT kieu ma: ma bill quay dang VGBxxxxx in tren ma QR cua tiem. O ma tham
# chieu cua bill nay dang giu "VQRQALMIO7806" - so TAI KHOAN AO do Pancake xin
# MB cap rieng cho don. No khong khop `RE_MA_BILL`, nen danh sach ma rong,
# truy van khong chay, ket qua ve 0. KHONG PHAI ngan hang chua nhan, ma la man
# hinh hoi sai cau hoi.
#
# Don Pancake xua nay khop bang mach S<shop>O<don>T qua `_sepay_theo_don`, va
# duong do van chay dung o man Sales. Nhung man bill quay khong bao gio goi
# toi no, ke ca khi bill mang san `custom_pancake_display_id`.
#
# CAU BAO LOI CON CHI MOT DUONG THOAT KHONG TON TAI
# ================================================
# No bao "tim ma giao dich trong sao ke go vao o Ma tham chieu". Go
# "FT26237024746528" vao do cung ra 0 not, vi van chinh duong `_sepay_bill`
# ay soi bang `RE_MA_BILL`. Ben Sales co loi ra that (`_soat_sepay` cho qua
# khi da co ma tham chieu), ben quay thi khong. Bay mot canh cua roi khoa lai
# con te hon la khong bay.
#
# NAY HOI DU BA DUONG
# ===================
#   1. Ma bill quay VGBxxxxx, cho bill ban tai quay.
#   2. Mach S<shop>O<don>T theo so don Pancake, cho bill tu Pancake.
#   3. So tham chieu ngan hang go tay, cho truong hop khach chuyen sai noi
#      dung - dung cai canh cua ma cau bao loi da hua.
#
# Duong nao ra nhieu tien nhat thi lay, va LUON mang theo ten dong sao ke de
# `_chiem_gd_bill` van chan duoc mot giao dich tra hai bill.


RE_MA_NGAN_HANG = re.compile(r"[A-Z0-9]{6,40}")


def _sepay_theo_tham_chieu(ma, so_ngay=45):
	"""Tien theo SO THAM CHIEU ngan hang go tay vao o Ma tham chieu.

	Khop DUNG BANG o `reference_number`, khong dung regexp long: so tham
	chieu la ma dinh danh mot giao dich, gan dung khong phai la dung.
	"""
	ma = re.sub(r"\s+", "", str(ma or "")).upper()
	if not RE_MA_NGAN_HANG.fullmatch(ma):
		return {}
	from frappe.utils import add_days

	n = max(1, min(cint(so_ngay) or 45, 180))
	try:
		gds = frappe.db.sql(
			"""select name, deposit, withdrawal, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and date >= %s and upper(trim(reference_number)) = %s""",
			(add_days(nowdate(), -n), ma), as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc SePay theo tham chieu")
		return {}
	if not gds:
		return {}
	return {
		"nhan": sum(flt(g.get("deposit")) - flt(g.get("withdrawal")) for g in gds),
		"ma": ma,
		"so_gd": len(gds),
		"gd": [g["name"] for g in gds if g.get("name")],
	}


def _sepay_cho_bill(si):
	"""Tien ngan hang da nhan cho MOT bill, hoi du ba duong.

	Tra ve ket qua kem khoa `duong` de man hinh va nhat ky noi duoc no khop
	bang duong nao.
	"""
	ma = str(si.get("vgb_ma_tham_chieu") or "").strip().upper()
	don = str(si.get("custom_pancake_display_id") or "").strip()
	cac = [("ma_bill", _sepay_bill(ma) if ma else {})]
	if don:
		try:
			theo_don = _sepay_theo_don(cfg().pancake_shop_id, [don]) or {}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: doc SePay theo don cho bill")
			theo_don = {}
		cac.append(("so_don_pancake", theo_don.get(don) or {}))
	if ma and not RE_MA_BILL.fullmatch(ma):
		cac.append(("tham_chieu_ngan_hang", _sepay_theo_tham_chieu(ma)))
	ten, kq = chiem_sao_ke.chon_duong_khop(cac, flt(si.get("grand_total")))
	kq = dict(kq or {})
	kq["duong"] = ten
	return kq


@frappe.whitelist()
def pos_kiem_sepay(noi_dung=None, tien=0):
	"""Man tinh tien goi vai giay mot lan khi dang chia QR chuyen khoan:
	khach chuyen den noi la cashier thay ngay tren man hinh, khoi mo app
	ngan hang hay cho Lark."""
	_kiem_quyen()
	g = _sepay_bill(noi_dung)
	nhan = flt(g.get("nhan"))
	if nhan >= flt(tien) - 1:
		return {"nhan": nhan, "du": 1, "ma": g.get("ma") or "", "duong": "ma"}
	# DUONG HAI, them 31/08/2026. Noi dung chuyen khoan cua khach hau nhu
	# khong bao gio mang ma bill (11 tren 2.914 giao dich ca thang 8), nen
	# neu chi biet mot duong thi o QR nay gan nhu khong bao gio sang xanh va
	# thu ngan van phai ngoi nhin tin nhan bao chuyen khoan.
	#
	# Duong hai chi DEM xem co bao nhieu khoan tien dung bang so phai thu vua
	# ve trong khoang ba muoi phut va chua bill nao nhan. Dem xong thi man
	# hinh moi thu ngan bam nut do tien de tu nhin va tu chon.
	#
	# Truoc day cho nay tu bao xanh khi dung mot khoan. Anh Viet 01/09/2026
	# bo: khach A tra 85.000 luc 14h00 khong ai gach, khach B goi 85.000 luc
	# 14h20 la may xanh nham ngay, thu ngan tra banh ma tien chua ve.
	try:
		con = _gd_chua_ai_nhan(nowdate())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc sao ke chua ai nhan")
		con = []
	bay_gio = _phut_trong_ngay(now_datetime())
	hop = [
		c for c in con
		if khop_tien.cung_tien(c.get("tien"), tien)
		and khop_tien.trong_cua_so(bay_gio, c.get("phut"), 30, 2)
	] if (bay_gio is not None and flt(tien) > 0) else []
	# CHI DEM, KHONG TU NHAN. Man hinh dung con so nay de moi thu ngan bam
	# nut "Do tien chuyen khoan" chu may khong tu gach.
	return {
		"nhan": nhan, "du": 0, "ma": g.get("ma") or "",
		"duong": "", "goi_y": len(hop),
	}


# ============================================== NUT "DO TIEN CHUYEN KHOAN"
#
# ANH VIET 01/09/2026:
#
#   "Em cho them giup anh nut 'Do tien chuyen khoan' o man bam bill de thu
#    ngan co the nhan roi do thu cong."
#
# Day la ban thay cho phep doan tu dong da bo. Khac nhau o dung mot chuyen:
# MAY DE XUAT, NGUOI QUYET DINH. May liet ke cac khoan tien dung bang so
# phai thu ma chua bill nao nhan; thu ngan nhin gio, nhin so, doi chieu voi
# dien thoai khach roi chon. Chon xong may ghi SO THAM CHIEU NGAN HANG vao
# o Ma tham chieu cua bill, tu do tro di duong doi soat co san
# (`_sepay_theo_tham_chieu`) tu tim ra, khong can nho lai lan chon nay.
#
# Vi sao ghi so tham chieu chu khong ghi mot o rieng: so tham chieu la thu
# ke toan tra cuu duoc tren sao ke ngan hang. Mot o rieng chi co app doc
# duoc thi den luc doi soat cuoi thang lai phai mo app ra tra.


# Sai so tien cho nut do tay, tinh bang dong. Mot dong la de nuot sai so
# lam tron, khong phai de noi long phep so sanh.
SAI_SO_DO_TIEN = 1.0


def _dau_tk(stk):
	"""Dau nhan dien mot tai khoan ao trong noi dung sao ke. THUAN.

	Ngan hang ghi "Q00033k5p6" cho tai khoan "VQRQ00033k5p6": no cat ba chu
	VQR o dau. Nen doi chieu bang phan duoi chu khong doi chieu ca chuoi,
	khong thi khong dong sao ke nao khop.
	"""
	t = re.sub(r"\s+", "", str(stk or "")).upper()
	return t[3:] if t.startswith("VQR") else t


def _gd_cua_diem(ngay, diem):
	"""Moi khoan tien ve trong ngay CUA MOT DIEM BAN.

	ANH VIET 01/09/2026: *"Nut Do tay thi cai them de vua do tu dong, vua
	phai xo ra danh sach giao dich ngay hom do chuyen khoan vao tai khoan ao
	cua diem ban, nhan vien click vao roi chon tu danh sach de gan tay."*

	Tu 01/09/2026 moi diem mot tai khoan ao rieng, nen sao ke da tu tach san
	theo diem. O day chi loc lai: dong nao mang dau tai khoan cua diem thi la
	tien cua diem do.

	Diem chua khai tai khoan rieng thi KHONG loc, va noi ro ra cho man hinh
	de nguoi biet minh dang nhin ca sao ke chung chu khong phai cua rieng
	diem minh.

	Tra ve (danh_sach, tk) - tk de man hinh hien so tai khoan dang soi.
	"""
	ds = _gd_ngay(ngay)
	try:
		tk = tai_khoan.tk_cho("", str(diem or "").strip().upper())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc tai khoan cua diem")
		return ds, {}
	if not cint(tk.get("rieng")):
		return ds, tk
	dau = _dau_tk(tk.get("stk"))
	if not dau:
		return ds, tk
	return [g for g in ds if dau in (g.get("mo_ta") or "").upper()], tk


def _gd_da_co_chu(gds):
	"""Dong sao ke nao da duoc gan cho mot hoa don. Tra {ten_gd: ten_hoa_don}.

	Gan tay xong may ghi SO THAM CHIEU ngan hang vao o Ma tham chieu cua hoa
	don, nen chi can hoi nguoc lai theo so tham chieu la biet dong nao da co
	chu. Khong co bang phu nao de lech nhau.
	"""
	tc = {}
	for g in gds or []:
		t = re.sub(r"\s+", "", str((g or {}).get("tham_chieu") or "")).upper()
		if t:
			tc.setdefault(t, []).append(g.get("ten"))
	if not tc:
		return {}
	try:
		ds = frappe.get_all(
			"Sales Invoice",
			filters={"vgb_ma_tham_chieu": ["in", list(tc.keys())], "docstatus": ["<", 2]},
			fields=["name", "vgb_ma_tham_chieu"], limit_page_length=0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc hoa don da gan sao ke")
		return {}
	ra = {}
	for r in ds:
		for ten in tc.get(str(r.vgb_ma_tham_chieu or "").upper(), []):
			ra[ten] = r.name
	return ra


def _gd_thay_duoc(tien, ngay=None, sai_so=None):
	"""Cac khoan tien dung bang `tien` trong ngay ma chua bill nao nhan.

	Khong loc theo gio: nguoi dang nhin man hinh biet ro khach vua tra luc
	nao, chinh xac hon moi khung gio may tu dat. May chi lo phan may lam
	tot hon nguoi: doc het sao ke va loai nhung khoan da co chu.
	"""
	t = flt(tien)
	if t <= 0:
		return []
	con = _gd_chua_ai_nhan(ngay)
	sai = SAI_SO_DO_TIEN if sai_so is None else flt(sai_so)
	return [g for g in con if khop_tien.cung_tien(g.get("tien"), t, sai)]


@frappe.whitelist()
def pos_do_tien(tien=0, ngay=None, name=None, quay=None):
	"""Sao ke tien ve trong ngay CUA DIEM BAN nay. KHONG ghi gi.

	Tra ve CA HAI thu, vi anh Viet 01/09/2026 muon ca hai:

	  - Khoan nao DUNG BANG so phai thu va chua hoa don nao nhan: danh dau
	    `khop` de man hinh day len dau, do la de xuat cua may.
	  - VA toan bo giao dich trong ngay cua diem, ke ca da co chu hay lech
	    so tien, de nguoi tu nhin va tu chon khi may khong de xuat duoc.

	Goi duoc ca khi bill CHUA luu (man bam bill, truyen `tien` va `quay`)
	lan khi bill da luu (truyen `name`, may tu biet diem va so tien).
	"""
	_kiem_quyen()
	t = flt(tien)
	diem = str(quay or "").strip().upper()
	if name:
		si = frappe.db.get_value(
			"Sales Invoice", str(name),
			["grand_total", "vgb_quay", "custom_nguon", "posting_date"], as_dict=True) or {}
		if not t:
			t = flt(si.get("grand_total"))
		if not diem:
			diem = _diem_cua_bill(si) or ""
		if not ngay and si.get("posting_date"):
			ngay = si.get("posting_date")
	ngay = str(getdate(ngay or nowdate()))
	gds, tk = _gd_cua_diem(ngay, diem)
	co_chu = _gd_da_co_chu(gds)
	ra = []
	for g in gds:
		ten = g.get("ten")
		khop = bool(t) and khop_tien.cung_tien(g.get("tien"), t, SAI_SO_DO_TIEN)
		ra.append({
			"ten": ten,
			"tien": flt(g.get("tien")),
			"gio": _gio_hhmm(g.get("phut")),
			"mo_ta": (g.get("mo_ta") or "").strip()[:140],
			"khop": 1 if (khop and ten not in co_chu) else 0,
			"cua_bill": co_chu.get(ten) or "",
		})
	# Khoan khop va chua co chu len dau, roi den khoan chua co chu, cuoi cung
	# la khoan da gan cho hoa don khac. Trong tung nhom thi moi nhat len truoc.
	ra.sort(key=lambda g: (0 if g["khop"] else (1 if not g["cua_bill"] else 2), g["gio"]), reverse=False)
	ra.sort(key=lambda g: (0 if g["khop"] else (1 if not g["cua_bill"] else 2)))
	return {
		"tien": t,
		"ngay": ngay,
		"diem": diem,
		"tk_rieng": 1 if cint((tk or {}).get("rieng")) else 0,
		"tk_stk": str((tk or {}).get("stk") or ""),
		"so_khop": len([g for g in ra if g["khop"]]),
		"gd": ra,
	}


def _gio_hhmm(phut):
	"""Doi so phut ke tu dau ngay thanh chu '14:32'. THUAN."""
	try:
		p = int(round(float(phut)))
	except (TypeError, ValueError):
		return ""
	return "%02d:%02d" % ((p // 60) % 24, p % 60)


@frappe.whitelist()
def pos_gan_tien(name=None, gd=None):
	"""Thu ngan chon mot khoan tien la cua bill nay.

	Ghi so tham chieu ngan hang vao o Ma tham chieu, va de lai mot dong
	trong ghi chu doi soat. Gan tay ma khong ghi lai thi cuoi thang ke toan
	thay con so la khong biet ai gan, gan luc nao.
	"""
	_kiem_quyen()
	ten = str(name or "").strip()
	ma_gd = str(gd or "").strip()
	if not ten or not ma_gd:
		frappe.throw("Thiếu hoá đơn hoặc dòng sao kê cần gắn.")
	si = frappe.get_doc("Sales Invoice", ten)
	if si.docstatus == 2:
		frappe.throw("Hoá đơn %s đã huỷ, không gắn tiền được." % ten)
	g = frappe.db.get_value(
		"Bank Transaction", ma_gd,
		["name", "deposit", "reference_number", "date", "docstatus"], as_dict=True)
	if not g or cint(g.docstatus) == 2:
		frappe.throw("Không tìm thấy dòng sao kê %s." % ma_gd)
	tc = re.sub(r"\s+", "", str(g.reference_number or "")).upper()
	if not RE_MA_NGAN_HANG.fullmatch(tc):
		frappe.throw(
			"Dòng sao kê này không có số tham chiếu ngân hàng nên máy không "
			"gắn được. Báo anh Việt kiểm lại dòng %s." % ma_gd
		)
	# Khong de hai bill cung om mot so tham chieu.
	trung = frappe.get_all(
		"Sales Invoice",
		filters={"vgb_ma_tham_chieu": tc, "docstatus": ["<", 2], "name": ["!=", ten]},
		fields=["name"], limit_page_length=1)
	if trung:
		frappe.throw(
			"Khoản này đã gắn cho hoá đơn %s rồi. Một khoản tiền chỉ thuộc về "
			"một hoá đơn." % trung[0]["name"])
	# Lech so tien thi KHONG chan, nhung phai ghi ro ca hai con so.
	#
	# Chan la sai: khach tra du 65.000 bang mot lan chuyen 65.000 thi khop,
	# nhung khach tra gop hai bill, hay tra chan 70.000 cho tien le, la may
	# chan mat duong doi soat duy nhat con lai. Nguoi dung day nhin thay ca
	# hai con so, ho quyet dinh duoc. Viec cua may la ghi lai that ro de ke
	# toan cuoi thang doc ra hieu ngay.
	lech = flt(g.deposit) - flt(si.grand_total)
	dong = "Thu ngân dò tay: gắn khoản %s đ ngày %s, số tham chiếu %s.%s" % (
		fmt_money(flt(g.deposit)), g.date, tc,
		("" if abs(lech) <= SAI_SO_DO_TIEN else
		 " Lệch %s đ so với hoá đơn %s đ." % (fmt_money(lech), fmt_money(flt(si.grand_total)))))
	co = (si.get("vgb_ghi_chu_doi_soat") or "").strip()
	if si.docstatus == 0:
		si.vgb_ma_tham_chieu = tc
		if dong not in co:
			si.vgb_ghi_chu_doi_soat = (co + " | " + dong) if co else dong
		si.flags.ignore_permissions = True
		si.save()
	else:
		# Bill da ghi so thi khong mo ra sua ca chung tu, chi vet hai o.
		frappe.db.set_value("Sales Invoice", ten, {
			"vgb_ma_tham_chieu": tc,
			"vgb_ghi_chu_doi_soat": (co + " | " + dong) if co and dong not in co else (co or dong),
		}, update_modified=False)
	frappe.db.commit()
	return {"ma_tham_chieu": tc, "nhan": flt(g.deposit), "lech": lech}


@frappe.whitelist()
def pos_ds_bill(quay=None, ngay=None):
	"""Danh sach bill trong ngay cua MOT quay, kem tinh trang SePay va HDDT."""
	_kiem_quyen()
	quay = (quay or "").strip()
	if not quay:
		frappe.throw("Thiếu mã điểm bán.")
	# Loc theo DIEM BAN chu khong theo ma quay: diem khong co quay tien mat
	# van co bill cua no, chi khac cho `vgb_quay` de trong.
	loc = _loc_diem_ban(quay)
	if loc is None:
		frappe.throw("Mã điểm bán %s không có trong danh sách điểm bán." % quay)
	ngay = getdate(ngay or nowdate())
	loc.update({"posting_date": str(ngay), "docstatus": ["<", 2]})
	ds = frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=[
			"name", "creation", "docstatus", "grand_total", "discount_amount", "total_qty",
			"custom_nguon", "custom_pancake_display_id", "remarks", "owner",
			"vgb_tam_tinh", "vgb_pt_thanh_toan", "vgb_ma_tham_chieu", "vgb_ghi_chu",
			"vgb_xhd_ten", "vgb_xhd_mst", "vgb_so_ban",
			"vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi", "vgb_lan_sua",
			"custom_hddt_so", "custom_hddt_trang_thai",
			# Ba o duoi day chi phuc vu phep "ghi so duoc chua" ben duoi.
			"customer", "custom_pancake_id", "vgb_quay",
			# Thong tin khach cho man xem lai bill (anh Viet 01/09/2026).
			# Doc cung mot luot chu dung hoi tung don, mot ngay cao diem co
			# ca tram bill thi hoi tung don la ca tram luot.
			"customer_name", "vgb_khach_no",
			# Don hang tang: trang thai duyet quyet dinh don co ghi so duoc
			# khong, nen phai doc ve cung mot luot. Thieu o nay thi chip
			# "Khong ghi so duoc" im lang bo qua ca nhom don tang.
			"vgb_tang_duyet", "vgb_tang_loai", "vgb_tang_ly_do",
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	sepay, _bo_qua = _sepay_theo_ma_bill(
		[r.vgb_ma_tham_chieu for r in ds if (r.vgb_pt_thanh_toan or "") == "Chuyển khoản"]
	)
	# Don Pancake khop bang mach S<shop>O<don>T chu khong bang ma bill VGB.
	# Doc mot lan cho ca ngay, dung hoi tung dong.
	don_ck = [
		str(r.custom_pancake_display_id or "").strip() for r in ds
		if (r.vgb_pt_thanh_toan or "") == "Chuyển khoản"
		and str(r.custom_pancake_display_id or "").strip()
	]
	theo_don = {}
	if don_ck:
		try:
			theo_don = _sepay_theo_don(cfg().pancake_shop_id, don_ck) or {}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: doc SePay theo don cho danh sach bill")
	ma_trung = _ma_trung_trong_ngay(ngay, [r.vgb_ma_tham_chieu for r in ds])
	for r in ds:
		# Chip "Cho tien ve" tung sang do suot tren bill Pancake da tra du
		# tien, vi no chi ngo mot duong. Nay lay duong nao ra nhieu nhat.
		g = sepay.get(str(r.vgb_ma_tham_chieu or "").upper()) or {}
		gd = theo_don.get(str(r.custom_pancake_display_id or "").strip()) or {}
		r["sepay_nhan"] = max(flt(g.get("nhan")), flt(gd.get("nhan")))
		r["sepay_du"] = 1 if r["sepay_nhan"] >= flt(r.grand_total) - 1 else 0
		r["sepay_duong"] = "ma" if r["sepay_du"] else ""
		r["trung_ma"] = 1 if str(r.vgb_ma_tham_chieu or "").upper() in ma_trung else 0
	gan_khach_vao_dong(ds)
	# ANH VIET 01/09/2026: MAY KHONG DUOC TU DOAN.
	#
	#   "May cung khong can phai doan qua khung gio vi rat rui ro doan nham."
	#
	# Nen o day KHONG goi `_khop_theo_tien` nua. Phep do van con, nhung chi
	# chay khi thu ngan tu bam nut "Do tien chuyen khoan" va tu chon khoan
	# nao la cua bill nay - xem `pos_do_tien` va `pos_gan_tien`. May de xuat,
	# nguoi quyet dinh, va quyet dinh do duoc ghi lai.
	#
	# Duong doi soat that su phai sua nam o CHO KHAC: moi diem ban mot tai
	# khoan ao rieng, de sao ke tu no tach san theo diem. Xem `tai_khoan.py`.
	_gan_ly_do_treo(ds)
	# Tinh trang keo don Pancake. Man hinh dan cau nay len dau bang khi don
	# chua ve, thay vi de Sales nhin danh sach it hon roi tu doan (bai hoc
	# 26-27/08/2026: hai ngay don khong ve ma khong man nao noi mot cau).
	return {
		"ngay": str(ngay),
		"bill": ds,
		"pancake": pancake_nhip.tinh_trang(),
		"ly_do_treo": dict(ghi_so_dieu_kien.LY_DO),
	}


def _quay_tu_ghi_so():
	"""Tap ma quay duoc chuoi cuoi ngay ghi so, doc tu Cai dat.

	Doc y het cach chuoi cuoi ngay doc (xem `tu_ghi_so` phia tren): cung mot
	o cau hinh, cung phep tach dong va viet hoa. Doc khac di mot chut la man
	hinh noi mot dang ma may lam mot dang.
	"""
	try:
		tho = str(cfg().get("tu_ghi_so_quay") or "")
	except Exception:
		return set()
	return set(
		q.strip().upper()
		for q in tho.replace(",", "\n").splitlines()
		if q.strip()
	)


def _gan_ly_do_treo(ds):
	"""Gan `ly_do_treo` va `ly_do_treo_chu` cho tung dong bill.

	Anh Viet 27/08/2026: moi man tinh tien phai co chip loc "Khong ghi so
	duoc" de cac ban dien bo sung TRUOC 23h, thay vi den 23h may lang le bo
	qua roi sang hom sau khong ai biet don do o dau.

	Phep quyet dinh nam ben `ghi_so_dieu_kien`, la phep THUAN nen kiem thu
	duoc khong can site. O day chi lam viec doc du kien: phuong thuc hop le
	cua tung nguon, phuong thuc nao bat buoc co ma, va quay nao nam trong
	chuoi tu ghi so.
	"""
	if not ds:
		return
	try:
		can_ma = set(d["ten"] for d in pt_thanh_toan.ds(chi_dung=True) if d.get("bat"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc phuong thuc bat buoc ma")
		can_ma = set()
	quay_bat = _quay_tu_ghi_so()
	try:
		khach_le = _khach_le()
	except Exception:
		khach_le = ""
	theo_nguon = {}
	for r in ds:
		nguon = str(r.get("custom_nguon") or "")
		if nguon not in theo_nguon:
			try:
				theo_nguon[nguon] = set(_pt_cho_nguon(nguon))
			except Exception:
				# Doc khong duoc thi de None: `ly_do` se BO QUA phep kiem
				# nguon thay vi bao sai la "phuong thuc sai nguon".
				theo_nguon[nguon] = None
		q = str(r.get("vgb_quay") or "").strip().upper()
		if q:
			trong_chuoi = q in quay_bat
		else:
			# Diem khong co quay: chuoi cuoi ngay chi nhat don CO ma Pancake
			# (xem `loc_sales`). Don Sales nhap tay khong co ma do nen may
			# khong bao gio nhat, phai ghi so tay.
			trong_chuoi = bool(str(r.get("custom_pancake_id") or "").strip())
		ma = ghi_so_dieu_kien.ly_do(
			r,
			pt_hop_le=theo_nguon[nguon],
			pt_can_ma=can_ma,
			trong_chuoi=trong_chuoi,
			khach_le=khach_le,
		)
		r["ly_do_treo"] = ma
		r["ly_do_treo_chu"] = ghi_so_dieu_kien.chu(ma)


def _loc_diem_ban(ma):
	"""Bo loc frappe chon dung bill cua MOT diem ban.

	Diem CO quay thi bill mang ma quay do trong `vgb_quay`.

	Diem KHONG co quay (Sales Online) thi bill de trong `vgb_quay` - do la
	quy uoc cu cua he, khong doi duoc vi bao cao va doi soat deu dua vao no.
	Nen nhan dien theo NGUON DON cua diem: mot bill GrabFood, ShopeeFood hay
	BeFood khong mang ma quay thi chi co the la cua diem online.

	Truoc 24/08/2026 khong ham nao lam viec nay, nen diem Sales Online khong
	co man tinh tien: moi cau truy van cua man do deu loc theo `vgb_quay` va
	tra ve rong, con `_pos_lay` thi tu choi thang.
	"""
	d = diem_ban.theo_ma(str(ma or "").strip().upper())
	if not d:
		return None
	if d["quay"]:
		return {"vgb_quay": d["quay"]}
	nguon = [n for n in (d["nguon"] or []) if n]
	if not nguon:
		return None
	return {"vgb_quay": ["in", ["", None]], "custom_nguon": ["in", nguon]}


def _diem_cua_bill(si):
	"""Bill nay thuoc diem ban nao. Rong khi khong xac dinh duoc."""
	lay = si.get if hasattr(si, "get") else (lambda k: getattr(si, k, None))
	q = str(lay("vgb_quay") or "").strip()
	if q:
		return diem_ban.ma_theo_quay(q) or ""
	nguon = str(lay("custom_nguon") or "").strip()
	if not nguon:
		return ""
	for d in diem_ban.ds(chi_bat=True):
		if not d["quay"] and nguon in (d["nguon"] or []):
			return d["ma"]
	return ""


def _pos_lay(name):
	si = frappe.get_doc("Sales Invoice", name)
	if (si.get("vgb_quay") or "").strip():
		return si
	# Bill cua diem KHONG co quay (Sales Online) cung la bill cua man tinh
	# tien, chi khac cho no de trong `vgb_quay` theo quy uoc cu. Truoc day
	# cua nay tu choi thang, nen diem Sales lap duoc bill ma khong bao gio
	# chot, sua hay ghi so duoc tu app.
	if _diem_cua_bill(si):
		return si
	frappe.throw("Phiếu này không phải bill của điểm bán nào.")


def _huy_lay(name):
	"""Phieu de HUY. Nhan ca bill quay LAN don cua diem nhan don online.

	Truoc 15/08/2026 huy don phai di qua _pos_lay, ma ham do doi phieu co
	ma quay - don cua Sales Online de trong vgb_quay nen khong co duong nao
	huy tren app, ke toan phai vao ERP. Nay "Tại chỗ" va "Mang về" gan duoc
	cho ca Sales, tuc Sales nhap nham mot don la ket luon. Nhan het, cac
	chan khac (da ghi so, da co hoa don dien tu, OTP) van nguyen.
	"""
	return frappe.get_doc("Sales Invoice", name)


@frappe.whitelist()
def pos_chot(name, pt=None, ma_tham_chieu=None, giam_gia=None, ghi_chu=None, otp=None):
	"""Chot mot bill tam tinh: khach thanh toan xong, cashier chon phuong
	thuc, bill thanh bill thuong cho ghi so. Cung dung de sua pt/ghi chu
	cua bill nhap chua ghi so."""
	_kiem_quyen()
	si = _pos_lay(name)
	if si.docstatus != 0:
		frappe.throw("Hoá đơn này đã ghi sổ rồi, không sửa được nữa.")
	# Duong nay cung phai qua cua quyen bo mon, khong thi thu ngan chi can
	# in tam tinh xong bam Chot kem giam gia la lach duoc chot chan ben
	# pos_sua_don. Chon phuong thuc thanh toan van tu do - do la nghiep vu
	# binh thuong, khong dinh gi den tien cua bill.
	if quyen_quay.them_giam_gia(si, giam_gia):
		if not otp and not _otp_la_sep():
			frappe.throw(
				"Bill này đã in tạm tính đưa khách rồi, thêm giảm giá thì cần mã "
				"OTP của quản lý ca. Bấm xin mã rồi nhập vào."
			)
		_otp_kiem(otp, "thêm giảm giá khi chốt bill")
	if pt:
		pt = _kiem_pt(pt, si.custom_nguon)
		ma_tham_chieu = luat_thanh_toan.ma_can_ghi(
			ma_tham_chieu, si.vgb_ma_tham_chieu, pt, si.vgb_pt_thanh_toan)
		si.vgb_pt_thanh_toan = pt
		si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
		if si.vgb_ma_tham_chieu:
			_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
	_nan_pt_tai_cho(si)
	if ghi_chu is not None:
		si.vgb_ghi_chu = (ghi_chu or "").strip()
	if giam_gia is not None:
		si.apply_discount_on = "Grand Total"
		# Cong phan giam tu diem vao - xem _giam_tu_diem.
		si.discount_amount = flt(giam_gia) + _giam_tu_diem(si)
	si.vgb_tam_tinh = 0
	si.flags.ignore_permissions = True
	si.save()
	frappe.db.commit()
	return {"ok": 1, "name": si.name, "grand_total": si.grand_total}


@frappe.whitelist()
def pos_xoa(name, otp=None, ly_do=None):
	"""Huy mot bill quay bam nham. Ten ham giu nguyen cho app cu con goi duoc,
	nhung viec da doi han: KHONG con xoa nua, chi danh dau da huy.

	Anh Viet chot 11/08/2026 sau khi 37 hoa don quay Tran Cao Van bi xoa
	sach: "khong duoc phep xoa vinh vien bat cu hoa don nao o bat cu phan he
	nao". Bill huy van nam nguyen trong danh sach, xem lai duoc bang chip
	"Da huy", va van phai co OTP quan ly vi tien khach da tra roi.

	Tu 15/08/2026 huy duoc CA don cua diem nhan don online, khong chi bill
	quay: Sales gio nhap duoc don "Tại chỗ" va "Mang về" nen cung phai co
	duong huy khi bam nham.
	"""
	_kiem_quyen()
	si = _huy_lay(name)
	if si.docstatus != 0:
		frappe.throw(
			"Hoá đơn đã ghi sổ rồi nên không huỷ ở đây được. Báo kế toán huỷ "
			"đúng nghiệp vụ, phiếu vẫn còn nguyên trong hệ thống."
		)
	if cint(si.get("vgb_huy") or 0):
		return {"ok": 1, "da_huy_tu_truoc": 1}
	# Bill da co so hoa don dien tu thi bat buoc phai ghi ly do: to hoa don
	# thue da nam ben co quan the roi, ke toan can biet vi sao de con lam
	# hoa don thay the cho khop.
	so_hddt = (si.get("custom_hddt_so") or "").strip()
	if (so_hddt or (si.get("custom_minvoice_id") or "").strip()) and not (ly_do or "").strip():
		frappe.throw(
			"Bill %s đã có hoá đơn điện tử số %s nên phải ghi lý do huỷ. "
			"Tờ hoá đơn thuế đã nằm bên cơ quan thuế, kế toán cần biết vì sao "
			"để làm hoá đơn thay thế cho khớp."
			% (si.get("custom_pancake_display_id") or name, so_hddt or "(chưa rõ)")
		)
	cach = _otp_kiem(otp, "huỷ bill")
	_ghi_vet(
		name,
		"Huỷ bill %s (%s đ). Lý do: %s"
		% (
			si.get("custom_pancake_display_id") or name,
			_tien(si.grand_total),
			(ly_do or "").strip() or "không ghi",
		),
		cach,
	)
	chung_tu.danh_dau_huy(si, ly_do, ghi_vet=False)
	return {"ok": 1, "da_huy": 1, "name": name}


@frappe.whitelist()
def pos_sua_don(
	name,
	otp=None,
	items=None,
	giam_gia=None,
	pt=None,
	ma_tham_chieu=None,
	ghi_chu=None,
	so_ban=None,
	xhd_ten=None,
	xhd_mst=None,
	xhd_dia_chi=None,
	xhd_email=None,
):
	"""Sua lai hoa don da tinh tien cho khach - phai co ma OTP quan ly.

	Hoa don con nhap thi sua duoc het (mon, giam gia, phuong thuc, so ban,
	thong tin xuat hoa don). Hoa don DA GHI SO thi so tien da vao so sach,
	chi cho sua ghi chu - so ban - thong tin xuat hoa don; muon doi tien
	phai huy hoa don ben ke toan."""
	_kiem_quyen()
	si = _pos_lay(name)
	if cint(si.get("vgb_huy")):
		frappe.throw(
			"Bill này đã huỷ nên không sửa được. Muốn dùng lại thì báo kế toán "
			"gỡ dấu huỷ, hoặc lập bill mới."
		)
	if items is not None and isinstance(items, str):
		items = json.loads(items or "[]")
	da_ghi = si.docstatus == 1
	# Hoa don DA GHI SO thi luon phai co OTP, khong xet muc quyen: luc do
	# tien da nam trong so sach, khong con la chuyen cua quay nua.
	if da_ghi:
		can_otp, vi_sao = True, "hoá đơn đã ghi sổ"
	else:
		can_otp, vi_sao = quyen_quay.can_otp(si, items, giam_gia)
	if can_otp:
		if not otp and not _otp_la_sep():
			frappe.throw(
				"Thao tác này cần mã OTP của quản lý ca vì %s. Bấm xin mã rồi nhập vào."
				% (vi_sao or "quy định tại quầy")
			)
		cach = _otp_kiem(otp, "sửa hoá đơn")
	else:
		cach = "thu ngân " + (frappe.session.user or "")
	doi = []
	if da_ghi and (items is not None or giam_gia is not None or pt):
		frappe.throw(
			"Hoá đơn %s đã ghi sổ nên không sửa được món, giảm giá hay phương thức "
			"thanh toán. Cần đổi thì báo kế toán huỷ hoá đơn rồi bấm lại."
			% (si.get("custom_pancake_display_id") or name)
		)
	if items is not None:
		rows = []
		for r in items or []:
			ma = (r.get("item_code") or "").strip()
			if not ma or not frappe.db.exists("Item", ma):
				frappe.throw("Không có mã hàng %s trong hệ thống." % (ma or "(trống)"))
			sl = flt(r.get("qty") or 0)
			if sl <= 0:
				frappe.throw("Số lượng của %s phải lớn hơn 0." % ma)
			d = {"item_code": ma, "qty": sl, "rate": flt(r.get("rate") or 0)}
			tc = (r.get("tuy_chon") or "").strip()
			gcm = (r.get("ghi_chu") or "").strip()
			cbo = (r.get("combo") or "").strip()
			if tc or gcm or cbo:
				ten_mon = frappe.db.get_value("Item", ma, "item_name") or ma
				d["description"] = ten_mon
				if cbo:
					d["description"] += "\n%s %s" % (DAU_COMBO, cbo[:120])
				if tc:
					d["description"] += "\n[%s]" % tc[:200]
				if gcm:
					d["description"] += "\n%s %s" % (DAU_GC_MON, gcm[:200])
			rows.append(d)
		if not rows:
			frappe.throw("Hoá đơn phải còn ít nhất một món.")
		si.set("items", [])
		for d in rows:
			si.append("items", d)
		doi.append("món")
	if giam_gia is not None:
		si.apply_discount_on = "Grand Total"
		# Cong phan giam tu diem vao - xem _giam_tu_diem.
		si.discount_amount = flt(giam_gia) + _giam_tu_diem(si)
		doi.append("giảm giá")
	if pt:
		pt = _kiem_pt(pt, si.custom_nguon)
		ma_tham_chieu = luat_thanh_toan.ma_can_ghi(
			ma_tham_chieu, si.vgb_ma_tham_chieu, pt, si.vgb_pt_thanh_toan)
		si.vgb_pt_thanh_toan = pt
		si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
		if si.vgb_ma_tham_chieu:
			_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
		doi.append("phương thức thanh toán")
	_nan_pt_tai_cho(si)
	if ghi_chu is not None:
		si.vgb_ghi_chu = (ghi_chu or "").strip()
		doi.append("ghi chú")
	if so_ban is not None:
		si.vgb_so_ban = str(so_ban or "").strip()
		doi.append("số bàn")
	if xhd_mst is not None or xhd_ten is not None:
		so_mst = _chuan_mst(xhd_mst)
		if (xhd_mst or "").strip() and not so_mst:
			frappe.throw(
				"Mã số thuế phải 10 số (doanh nghiệp), 12 số (hộ kinh doanh hoặc cá "
				"nhân, chính là số căn cước của chủ hộ), hoặc 13 số dạng 10 số - 3 "
				"số cho chi nhánh (ví dụ 0311638525-027)."
			)
		if so_mst and hoa_don_vat.thieu_ten_rieng(xhd_ten):
			frappe.throw(hoa_don_vat.LOI_TEN_CUT)
		si.vgb_xhd_mst = so_mst
		si.vgb_xhd_ten = (xhd_ten or "").strip() or XHD_MAC_DINH
		if xhd_dia_chi is not None:
			si.vgb_xhd_dia_chi = (xhd_dia_chi or "").strip()
		if xhd_email is not None:
			si.vgb_xhd_email = (xhd_email or "").strip()
		doi.append("thông tin xuất hoá đơn")
	si.flags.ignore_permissions = True
	if da_ghi:
		si.save(ignore_version=True)
	else:
		si.save()
	frappe.db.commit()
	_ghi_vet(name, "Sửa hoá đơn: %s" % (", ".join(doi) or "không đổi gì"), cach)
	# Dem so lan sua de chip "Da sua" co cai ma loc: ban nhap sua tai cho
	# thi khong de lai dau vet nao o muc docstatus.
	if doi:
		chung_tu.ghi_nhan_sua("Sales Invoice", si.name)
	frappe.db.commit()
	return {"ok": 1, "name": si.name, "grand_total": si.grand_total}


def _chiem_gd_bill(si, ds_gd):
	"""Ghi nhan cac dong sao ke ma bill nay dang gach, sau khi chac chan
	khong dong nao da co chu.

	Nem loi neu co dong da thuoc ve chung tu khac. Nguoi doc phai biet CHINH
	XAC dong nao va ai dang giu, khong phai mot cau "co gi do khong on".
	"""
	ds_gd = chiem_sao_ke.tach_gd("\n".join(str(x or "") for x in (ds_gd or [])))
	if not ds_gd:
		return
	from vagabond import doi_soat_sepay as dss

	chu = dss.chu_cua_giao_dich(ds_gd, bo_qua_hoa_don=si.name)
	dung_hai = chiem_sao_ke.gd_dung_hai_lan(ds_gd, chu)
	if dung_hai:
		frappe.throw(
			"Không ghi sổ được bill %s: %s. Một lần chuyển khoản chỉ được tính "
			"cho một chứng từ. Vui lòng kiểm lại mã tham chiếu, hoặc báo bộ phận "
			"kế toán đối soát tay."
			% (si.name, "; ".join("giao dịch %s đã gạch cho %s" % (m, c) for m, c in dung_hai))
		)
	si.vgb_gd_sepay = chiem_sao_ke.gom_gd(ds_gd)


@frappe.whitelist()
def pos_ghi_so(name):
	"""Ghi so mot bill NGAY TAI QUAY. Chuyen khoan thi ngan hang phai nhan
	du tien theo ma bill VGB moi cho ghi (giong nguyen tac ben Sales)."""
	_kiem_quyen()
	si = _pos_lay(name)
	if si.docstatus != 0:
		frappe.throw("Bill này đã ghi sổ rồi.")
	if frappe.utils.cint(si.get("vgb_huy")):
		frappe.throw(
			"Bill này đã huỷ nên không ghi sổ được. Muốn dùng lại thì báo kế toán "
			"gỡ dấu huỷ, hoặc lập bill mới."
		)
	if frappe.utils.cint(si.get("vgb_tam_tinh")):
		frappe.throw("Bill còn tạm tính. Khách thanh toán xong thì bấm Chốt trước, rồi mới ghi sổ.")
	pt = _nan_pt_theo_nguon(si)
	if not pt:
		frappe.throw("Bill chưa chọn phương thức thanh toán.")
	si.vgb_pt_thanh_toan = pt
	if pt == "Chuyển khoản":
		# Hoi CA BA duong khop, xem doan mo ta cua `_sepay_cho_bill`. Truoc
		# 27/08/2026 cho nay chi hoi ma bill VGB, nen bill cua don Pancake
		# tra qua tai khoan ao MB vinh vien doc ra 0 du tien da ve.
		g = _sepay_cho_bill(si)
		nhan = flt(g.get("nhan"))
		if nhan < flt(si.grand_total) - 1:
			frappe.throw(
				"Bill %s ghi Chuyển khoản nhưng ngân hàng mới nhận %s đ trên tổng %s đ. "
				"Chờ tiền về rồi ghi sổ, hoặc khách chuyển sai nội dung thì tìm mã giao "
				"dịch trong sao kê gõ vào ô Mã tham chiếu."
				% (si.name, _tien(nhan), _tien(si.grand_total))
			)
		# MOT DONG SAO KE CHI DUOC GACH CHO MOT BILL.
		#
		# Truoc day bang ket qua gom theo MA chu khong theo bill, nen hai bill
		# mang cung mot ma tham chieu deu doc ra cung so tien va CA HAI deu
		# qua duoc cua ben tren roi ghi so. Mot lan khach chuyen 200.000 tra
		# duoc hai bill 200.000. Ma tham chieu thi cashier go tay duoc, va ma
		# bill sinh ngau nhien nam ky tu nen cung co ngay trung that.
		#
		# Nay ghi ro nhung dong sao ke da gach cho bill nay, va truoc khi ghi
		# so thi hoi lai xem dong nao da co chu chua - hoi ca cac luong khac
		# nhu phieu cong no, khong chi trong pham vi bill quay.
		_chiem_gd_bill(si, g.get("gd") or [])
	else:
		si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, si.vgb_ma_tham_chieu)
	if not (si.vgb_xhd_ten or "").strip():
		si.vgb_xhd_ten = XHD_MAC_DINH
	si.flags.ignore_permissions = True
	si.submit()
	frappe.db.commit()
	return {"ok": 1, "name": si.name}


# ------------------------------------------ khach tu nhap thong tin xuat HD

@frappe.whitelist()
def pos_ds_tuy_chon():
	"""Danh muc tuy chon pha che (it duong, it da...) kieu customization Fabi.

	Cau hinh trong doctype "Vagabond Tuy Chon Mon": ten nhom, cac lua chon
	(moi dong mot cai), nhom mon ap dung. Khach khong chon gi = mac dinh
	100% duong 100% da, khong ghi gi len bill.
	"""
	_kiem_quyen()
	try:
		ds = frappe.get_all(
			"Vagabond Tuy Chon Mon",
			filters={"bat": 1},
			fields=["nhom", "lua_chon", "nhom_mon"],
			limit_page_length=0,
		)
	except Exception:
		return {"tc": []}
	ra = []
	for r in ds:
		ra.append(
			{
				"nhom": r.nhom,
				"lua_chon": [x.strip() for x in str(r.lua_chon or "").splitlines() if x.strip()],
				"nhom_mon": [x.strip() for x in str(r.nhom_mon or "").splitlines() if x.strip()],
			}
		)
	return {"tc": ra}


@frappe.whitelist()
def pos_ds_khuyen_mai(quay=None):
	"""Danh muc chuong trinh khuyen mai cho man tinh tien (kieu Fabi).

	Cau hinh trong doctype "Vagabond Khuyen Mai" tren Desk: ten, loai
	(Phan tram / So tien), gia tri, quay ap dung (trong = moi quay), bat.
	Cashier chon voucher la may tu tinh o giam gia, ten voucher di vao
	ghi chu bill de doi soat.
	"""
	_kiem_quyen()
	quay = (quay or "").strip()
	try:
		ds = frappe.get_all(
			"Vagabond Khuyen Mai",
			filters={"bat": 1},
			fields=["name", "ten", "loai", "gia_tri", "quay"],
			order_by="ten asc",
			limit_page_length=0,
		)
	except Exception:
		return {"km": []}
	ra = []
	for r in ds:
		ap = (r.quay or "").strip()
		if ap and quay and ap != quay:
			continue
		ra.append({"ten": r.ten, "loai": r.loai, "gia_tri": flt(r.gia_tri)})
	return {"km": ra}


XHD_HAN_GIO = 2


def _xhd_kiem_han(creation):
	"""Ma QR tren bill ghi ro hieu luc 2 tieng - may phai giu dung loi hua.

	Qua han van con duong: khach lien he tiem, sales dien ho trong man
	Doanh thu Cua hang truoc 23h30 la hoa don van kip phat hanh trong dem.
	"""
	if not creation:
		return
	tuoi = (now_datetime() - creation).total_seconds()
	if tuoi > XHD_HAN_GIO * 3600:
		frappe.throw(
			"Mã QR này đã quá hiệu lực %s tiếng kể từ lúc in bill. "
			"Anh chị liên hệ tiệm (nhắn fanpage hoặc gọi quầy) để nhân viên "
			"điền thông tin xuất hoá đơn giúp mình trước 22h hôm nay."
			% XHD_HAN_GIO
		)


@frappe.whitelist()
def pos_chot_ca(quay=None, ngay=None):
	"""Bang tong ket cuoi ca cua MOT quay: tien mat phai co trong ket,
	chuyen khoan doi voi SePay da ve, the theo tung may - lech la thay ngay
	truoc khi giao ca, khoi cai nhau hom sau (anh Viet 09/08/2026)."""
	_kiem_quyen()
	quay = (quay or "").strip()
	if not quay:
		frappe.throw("Thiếu mã điểm bán.")
	# Loc theo DIEM BAN chu khong theo ma quay: diem khong co quay tien mat
	# van co bill cua no, chi khac cho `vgb_quay` de trong.
	loc = _loc_diem_ban(quay)
	if loc is None:
		frappe.throw("Mã điểm bán %s không có trong danh sách điểm bán." % quay)
	ngay = getdate(ngay or nowdate())
	loc.update({"posting_date": str(ngay), "docstatus": ["<", 2]})
	ds = frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=[
			"name", "grand_total", "docstatus", "custom_nguon",
			"vgb_tam_tinh", "vgb_pt_thanh_toan", "vgb_ma_tham_chieu", "vgb_huy",
		],
		limit_page_length=0,
	)
	# Bill da huy khong phai doanh thu, phai bo ra TRUOC khi cong. Bo o day
	# chu khong bo trong vong lap phia duoi de tong_bill va tong_tien cuoi
	# ham cung khong dinh phai no.
	ds = [r for r in ds if not frappe.utils.cint(r.get("vgb_huy"))]
	sepay, _bo_qua = _sepay_theo_ma_bill(
		[r.vgb_ma_tham_chieu for r in ds if (r.vgb_pt_thanh_toan or "") == "Chuyển khoản"]
	)
	pt_tong = {}
	tam_tinh = {"so": 0, "tien": 0.0}
	ck_ve = 0.0
	ck_thieu = []
	da_ghi = 0
	chua_ghi = 0
	for r in ds:
		if frappe.utils.cint(r.vgb_tam_tinh):
			tam_tinh["so"] += 1
			tam_tinh["tien"] += flt(r.grand_total)
			continue
		if r.docstatus == 1:
			da_ghi += 1
		else:
			chua_ghi += 1
		pt = (r.vgb_pt_thanh_toan or "").strip() or (r.custom_nguon or "Chưa rõ")
		o = pt_tong.setdefault(pt, {"so": 0, "tien": 0.0})
		o["so"] += 1
		o["tien"] += flt(r.grand_total)
		if (r.vgb_pt_thanh_toan or "") == "Chuyển khoản":
			g = sepay.get(str(r.vgb_ma_tham_chieu or "").upper()) or {}
			nhan = flt(g.get("nhan"))
			ck_ve += min(nhan, flt(r.grand_total))
			if nhan < flt(r.grand_total) - 1:
				ck_thieu.append(
					{"bill": r.vgb_ma_tham_chieu or r.name, "thieu": flt(r.grand_total) - nhan}
				)
	# Tien chua nam trong ket luc chot ca: Grab Dine-Out Grab giu den T+1,
	# Cong no khach si con thieu. Tach ra de thu ngan doi chieu tien mat
	# khong bi lech, va quan ly biet con bao nhieu phai di doi.
	# Doc bang phuong thuc MOT LAN roi dung lai, khong goi trong vong lap.
	cho_ve = set(pt_thanh_toan.chua_ve_tien()) | set(pt_thanh_toan.ve_sau())
	# Hang tang KHONG nam trong "cho ve": tien do khong bao gio ve. Gop chung
	# thi man Chot ca hien mot con so "con phai di doi" trong do co ca so
	# tiem da cho di, va thu ngan lai di doi mot mon qua.
	khong_thu_pt = set(pt_thanh_toan.khong_thu())
	chua_ve = {"so": 0, "tien": 0.0, "dong": []}
	khong_thu = {"so": 0, "tien": 0.0, "dong": []}
	for k, v in pt_tong.items():
		if k in khong_thu_pt:
			khong_thu["so"] += v["so"]
			khong_thu["tien"] += v["tien"]
			khong_thu["dong"].append({"pt": k, "so": v["so"], "tien": v["tien"]})
		elif k in cho_ve:
			chua_ve["so"] += v["so"]
			chua_ve["tien"] += v["tien"]
			chua_ve["dong"].append({"pt": k, "so": v["so"], "tien": v["tien"]})
	chua_ve["dong"].sort(key=lambda x: -x["tien"])
	khong_thu["dong"].sort(key=lambda x: -x["tien"])
	return {
		"quay": quay,
		"ngay": str(ngay),
		"chua_ve": chua_ve,
		"khong_thu": khong_thu,
		"pt": [
			{"pt": k, "so": v["so"], "tien": v["tien"]}
			for k, v in sorted(pt_tong.items(), key=lambda x: -x[1]["tien"])
		],
		"ck_ve": ck_ve,
		"ck_thieu": ck_thieu,
		"tam_tinh": tam_tinh,
		"da_ghi": da_ghi,
		"chua_ghi": chua_ghi,
		"tong_bill": len(ds) - tam_tinh["so"],
		"tong_tien": sum(flt(r.grand_total) for r in ds if not frappe.utils.cint(r.vgb_tam_tinh)),
	}


def _xhd_token(name):
	"""Token in trong ma QR tren bill giay - khach chi sua duoc DUNG bill
	cua minh, khong doan duoc bill nguoi khac."""
	muoi = frappe.local.conf.get("encryption_key") or frappe.local.site
	return hashlib.sha1(("vgbxhd|%s|%s" % (name, muoi)).encode()).hexdigest()[:12]


@frappe.whitelist()
def pos_link_xhd(name):
	"""Duong dan cho ma QR xuat hoa don in cuoi bill."""
	_kiem_quyen()
	return {"url": "/xhd?d=%s&t=%s" % (name, _xhd_token(name))}


@frappe.whitelist(allow_guest=True)
def xhd_khach_xem(d=None, t=None):
	"""Khach quet QR: xem bill cua minh truoc khi dien thong tin."""
	name = (d or "").strip()
	if not name or (t or "").strip() != _xhd_token(name):
		frappe.throw("Đường dẫn không hợp lệ.")
	si = frappe.db.get_value(
		"Sales Invoice", name,
		["name", "posting_date", "grand_total", "custom_hddt_so", "creation",
		 "vgb_xhd_ten", "vgb_xhd_mst", "vgb_xhd_dia_chi", "vgb_xhd_email"],
		as_dict=True,
	)
	if not si:
		frappe.throw("Không tìm thấy bill này.")
	_xhd_kiem_han(si.creation)
	si.pop("creation", None)
	si["da_xuat"] = 1 if si.custom_hddt_so else 0
	si["custom_hddt_so"] = ""  # so hoa don khong phai viec cua trang khach
	if si.vgb_xhd_ten == XHD_MAC_DINH:
		si["vgb_xhd_ten"] = ""
	return si


@frappe.whitelist(allow_guest=True)
def xhd_khach_luu(d=None, t=None, ten=None, mst=None, dia_chi=None, email=None):
	"""Khach dien MST - ten - dia chi - email; ERP tu map vao don ban hang.
	Cuoi ngay lich 23h30 tu tao hoa don cho ky ben m-invoice nhu moi don."""
	name = (d or "").strip()
	if not name or (t or "").strip() != _xhd_token(name):
		frappe.throw("Đường dẫn không hợp lệ.")
	si = frappe.db.get_value(
		"Sales Invoice", name, ["name", "custom_hddt_so", "creation"], as_dict=True
	)
	if not si:
		frappe.throw("Không tìm thấy bill này.")
	_xhd_kiem_han(si.creation)
	if si.custom_hddt_so:
		frappe.throw("Bill này đã xuất hoá đơn điện tử rồi, không sửa được nữa. Cần điều chỉnh thì liên hệ tiệm.")
	so_mst = _chuan_mst(mst)
	if not so_mst:
		frappe.throw(
			"Mã số thuế phải 10 số (công ty), 12 số (hộ kinh doanh hoặc cá nhân) "
			"hoặc 13 số (chi nhánh)."
		)
	ten = (ten or "").strip()
	if not ten:
		frappe.throw("Thiếu tên pháp nhân trên hoá đơn.")
	if hoa_don_vat.thieu_ten_rieng(ten):
		frappe.throw(hoa_don_vat.LOI_TEN_CUT)
	# Hoa don dien tu gui qua email, khong co email thi khach khong nhan
	# duoc gi ca -> bat buoc dien (anh Viet 09/08/2026).
	email = (email or "").strip()
	if not email or "@" not in email or "." not in email.split("@")[-1]:
		frappe.throw("Vui lòng nhập email để nhận hoá đơn điện tử.")
	frappe.db.set_value(
		"Sales Invoice", name,
		{
			"vgb_xhd_ten": ten,
			"vgb_xhd_mst": so_mst,
			"vgb_xhd_dia_chi": (dia_chi or "").strip(),
			"vgb_xhd_email": (email or "").strip(),
		},
	)
	frappe.db.commit()
	# Gui mail bao da tiep nhan - khach dien xong co ngay mot dong hoi am,
	# khoi thap thom khong biet may co nhan duoc khong (anh Viet 09/08/2026).
	# Loi gui mail khong duoc lam hong viec luu.
	try:
		_xhd_mail_tiep_nhan(name, email, ten, so_mst)
		# Trang /xhd goi API bang GET (tranh CSRF cho khach vang lai), ma
		# Frappe ROLLBACK cuoi moi request GET. Ban ghi Email Queue sinh ra
		# sau frappe.db.commit() o tren nam trong transaction moi nen bi xoa
		# sach - thu khong bao gio gui. Commit lan nua la giu duoc.
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: mail tiep nhan XHD")
		frappe.db.commit()
	return {"ok": 1}


def _xhd_mail_tiep_nhan(name, email, ten, so_mst):
	"""Thu bao tiep nhan thong tin xuat hoa don, gui tu erp@thevagabondpatisserie.com."""
	si = frappe.db.get_value(
		"Sales Invoice", name, ["posting_date", "grand_total", "custom_pancake_display_id"], as_dict=True
	) or {}
	ngay = str(si.get("posting_date") or "")
	ngay = "/".join(reversed(ngay.split("-"))) if ngay else ""
	ma = si.get("custom_pancake_display_id") or name
	noi_dung = """<div style="font-family:Arial,sans-serif;font-size:14px;color:#222;line-height:1.7;max-width:560px">
<p>Ch&agrave;o anh ch&#7883;,</p>
<p>The Vagabond P&acirc;tisserie &#273;&atilde; nh&#7853;n &#273;&#7911; th&ocirc;ng tin xu&#7845;t ho&aacute; &#273;&#417;n cho bill <b>%(ma)s</b> ng&agrave;y %(ngay)s, t&#7893;ng ti&#7873;n <b>%(tien)s &#273;</b>:</p>
<p style="background:#f6f6f6;border-radius:8px;padding:12px 16px;margin:8px 0">
T&ecirc;n ph&aacute;p nh&acirc;n: <b>%(ten)s</b><br>
M&atilde; s&#7889; thu&#7871;: <b>%(mst)s</b></p>
<p>Ho&aacute; &#273;&#417;n &#273;i&#7879;n t&#7917; s&#7869; &#273;&#432;&#7907;c ph&aacute;t h&agrave;nh v&agrave; g&#7917;i v&#7873; &#273;&uacute;ng &#273;&#7883;a ch&#7881; email n&agrave;y <b>trong ng&agrave;y</b>. N&#7871;u qu&aacute; 24 gi&#7901; ch&#432;a th&#7845;y, anh ch&#7883; ki&#7875;m tra gi&uacute;p m&#7909;c th&#432; r&aacute;c, ho&#7863;c nh&#7855;n l&#7841;i cho ti&#7879;m qua fanpage.</p>
<p>Th&ocirc;ng tin c&oacute; sai s&oacute;t th&igrave; anh ch&#7883; b&aacute;o l&#7841;i tr&#432;&#7899;c 22h h&ocirc;m nay &#273;&#7875; ti&#7879;m k&#7883;p s&#7917;a tr&#432;&#7899;c khi ph&aacute;t h&agrave;nh nh&eacute;.</p>
<p>C&#7843;m &#417;n anh ch&#7883; &#273;&atilde; gh&eacute; ti&#7879;m!</p>
<p style="color:#777;font-size:12.5px;margin-top:18px">The Vagabond P&acirc;tisserie<br>9 Tr&#7847;n Cao V&acirc;n, Qu&#7853;n 1, TP.HCM<br>thevagabondpatisserie.com</p>
</div>""" % {
		"ma": ma,
		"ngay": ngay,
		"tien": _tien(si.get("grand_total") or 0),
		"ten": ten,
		"mst": so_mst,
	}
	frappe.sendmail(
		recipients=[email],
		sender="erp@thevagabondpatisserie.com",
		subject="The Vagabond Pâtisserie - Đã nhận thông tin xuất hoá đơn (bill %s)" % ma,
		message=noi_dung,
	)


@frappe.whitelist(allow_guest=True)
def xhd_khach_tra_mst(mst=None):
	"""Trang khach tra MST ra ten + dia chi, dung chung nguon VietQR."""
	from vagabond.api import tra_mst
	return tra_mst(mst)


# ------------------------------------------------- Hoa don thay the (v296)
#
# Vi sao co khoi nay
# ------------------
# Ngay 22/08/2026 to hoa don so 10901 cua don 92409 ra doi voi ten nguoi mua
# la "CÔNG TY CỔ PHẦN", thieu han phan ten rieng. To da ky, da gui co quan
# thue. Ke toan phai lap Bien ban thoa thuan huy bo hoa don va xuat to thay
# the ben M-Invoice. Xong roi thi khong co cho nao trong ERP de ghi lai
# viec do: don hang van hien "Đã xuất HĐĐT số 10901", nhin vao khong biet
# to do da bi thay.
#
# Da co san mot luong ghi nhan hoa don thay the, nhung no bam vao PHIEU HOAN
# TIEN (`hoan_tien.ghi_hddt_thay_the`). Ca nay khong hoan tien dong nao, chi
# sai ten, nen khong lap phieu hoan tien duoc. Khoi nay dua dung luong do ve
# thang DON HANG, dung chung ba truong `custom_hddt_thay_the*` da co.
#
# Ba nguyen tac giu nguyen tu luong cu:
#   - Ke toan go tay so hoa don moi. He thong chua doc nguoc duoc thay doi
#     lam thang tren cong M-Invoice, nen doan bua la sai.
#   - QT-20: khong xoa gi. Go ra thi o trong lai nhung nhat ky tren don van
#     giu ca so cu lan ly do go.
#   - Khong dung vao du lieu qua khu cua to hoa don cu. To 10901 van la to
#     10901, chi ghi them ben canh no la da co to thay the.

QUYEN_HDDT_THAY_THE = {"System Manager", "Accounts Manager", "Accounts User"}

# Tien to ten tep cua bien ban thay the. Moi tep dinh vao don hang deu nam
# chung mot cho, nen phai co dau de biet to nao la bien ban thay the. Duong
# ghi la duong duy nhat trong ma nguon dat ten tep nay, nen dau nay chac.
DAU_BBTT = "BBTT-"


def _quyen_hddt_thay_the():
	return bool(QUYEN_HDDT_THAY_THE & set(frappe.get_roles()))


def _chan_khong_phai_ke_toan():
	_kiem_quyen()
	if not _quyen_hddt_thay_the():
		frappe.throw(
			"Chỉ kế toán hoặc quản trị mới ghi nhận được hoá đơn thay thế. "
			"Vui lòng nhờ bộ phận kế toán ghi giúp."
		)


def _don_da_xuat(si_name):
	"""Doc mot don DA co hoa don dien tu. Chua xuat thi khong co gi de thay."""
	d = frappe.db.get_value(
		"Sales Invoice", si_name,
		["name", "custom_hddt_so", "custom_hddt_ky_hieu", "posting_date",
		 "custom_hddt_thay_the", "custom_hddt_sai_sot"],
		as_dict=True,
	)
	if not d:
		frappe.throw("Không có đơn %s." % si_name)
	if not (d.custom_hddt_so or "").strip():
		frappe.throw(
			"Đơn %s chưa xuất hoá đơn điện tử nên chưa có tờ nào để thay thế. "
			"Sai thông tin thì sửa thẳng trong đơn rồi xuất, không cần biên bản."
			% si_name
		)
	return d


@frappe.whitelist()
def ghi_hoa_don_thay_the(si_name=None, so=None, ky_hieu=None, ly_do=None):
	"""Ghi nhan to hoa don thay the ma ke toan da xuat ben M-Invoice."""
	_chan_khong_phai_ke_toan()
	d = _don_da_xuat(si_name)
	so_moi = str(so or "").strip()
	if not so_moi:
		frappe.throw(
			"Chưa nhập số hoá đơn thay thế. Mở tờ hoá đơn mới bên M-Invoice, "
			"chép số hoá đơn rồi dán vào ô này."
		)
	if len(so_moi) > 30:
		frappe.throw(
			"Số hoá đơn dài bất thường (%d ký tự). Kiểm lại xem có dán nhầm cả "
			"dòng không." % len(so_moi)
		)
	cu = (d.custom_hddt_so or "").strip()
	if so_moi == cu:
		frappe.throw(
			"Số vừa nhập trùng đúng số hoá đơn cũ (%s). Tờ thay thế phải mang "
			"số khác. Kiểm lại bên M-Invoice xem đã chép đúng tờ mới chưa." % cu
		)
	kh = str(ky_hieu or "").strip()
	ly = str(ly_do or "").strip()
	if not ly:
		frappe.throw(
			"Phải ghi lý do phải thay thế. Đây là phần giải trình khi cơ quan "
			"thuế hỏi lại, để trống thì người sau không hiểu vì sao có hai tờ."
		)

	luc = now_datetime()
	frappe.db.set_value("Sales Invoice", d.name, {
		"custom_hddt_sai_sot": 1,
		"custom_hddt_ly_do_thay_the": ly,
		"custom_hddt_thay_the": ("%s %s" % (kh, so_moi)).strip(),
		"custom_hddt_thay_the_luc": luc,
	}, update_modified=False)
	_vet_don(d.name, (
		"Ghi nhận hoá đơn thay thế %s%s cho tờ cũ %s. Lý do: %s"
		% (so_moi, (" (ký hiệu %s)" % kh) if kh else "", cu, ly)
	))
	frappe.db.commit()
	return {
		"ok": 1, "so": so_moi, "ky_hieu": kh, "so_cu": cu,
		"loi_nhan": "Đã ghi nhận tờ thay thế %s cho đơn %s." % (so_moi, d.name),
	}


@frappe.whitelist()
def go_hoa_don_thay_the(si_name=None, ly_do=None):
	"""Go so hoa don thay the ghi nham. Bat buoc ghi ly do, khong xoa nhat ky."""
	_chan_khong_phai_ke_toan()
	d = _don_da_xuat(si_name)
	ly = str(ly_do or "").strip()
	if not ly:
		frappe.throw("Phải ghi lý do gỡ thì người sau mới hiểu vì sao ô này trống lại.")
	cu = (d.custom_hddt_thay_the or "").strip()
	if not cu:
		frappe.throw("Đơn này chưa ghi hoá đơn thay thế nào, không có gì để gỡ.")
	frappe.db.set_value("Sales Invoice", d.name, {
		"custom_hddt_thay_the": "",
	}, update_modified=False)
	_vet_don(d.name, "Gỡ hoá đơn thay thế %s. Lý do: %s" % (cu, ly))
	frappe.db.commit()
	return {"ok": 1, "loi_nhan": "Đã gỡ %s. Nhật ký trên đơn vẫn giữ lại vết." % cu}


def _vet_don(si_name, noi_dung):
	"""Mot dong nhat ky tren don hang. Hong cho nay khong duoc keo do viec chinh."""
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": "Sales Invoice", "reference_name": si_name,
			"content": noi_dung,
		}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: ghi vet hoa don thay the")


def _ds_bbtt(si_name):
	"""Cac to bien ban thay the dang dinh tren mot don."""
	ra = []
	for f in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Sales Invoice", "attached_to_name": si_name},
		fields=["name", "file_name", "file_url", "creation"],
		order_by="creation asc",
	):
		ten = str(f.file_name or "")
		if not ten.startswith(DAU_BBTT):
			continue
		thap = ten.lower()
		ra.append({
			"tep": f.name,
			"ten": ten[len(DAU_BBTT):] or ten,
			"anh": 1 if thap.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic")) else 0,
			"luc": str(f.creation or "")[:16],
		})
	return ra


@frappe.whitelist()
def bien_ban_thay_the(si_name=None):
	"""Khoi hoa don thay the cua mot don, cho man Chi tiet don ve lai."""
	_kiem_quyen()
	d = frappe.db.get_value(
		"Sales Invoice", si_name,
		["name", "custom_hddt_so", "custom_hddt_ky_hieu", "posting_date",
		 "custom_hddt_sai_sot", "custom_hddt_ly_do_thay_the",
		 "custom_hddt_thay_the", "custom_hddt_thay_the_luc"],
		as_dict=True,
	)
	if not d:
		frappe.throw("Không có đơn %s." % si_name)
	so_cu = (d.custom_hddt_so or "").strip()
	mau, kh = hoa_don_vat.mau_va_ky_hieu(d.custom_hddt_ky_hieu)
	return {
		"da_xuat": 1 if so_cu else 0,
		"so_cu": so_cu,
		"mau_cu": mau,
		"ky_hieu_cu": kh,
		"ngay_cu": str(d.posting_date or ""),
		"sai_sot": cint(d.custom_hddt_sai_sot or 0),
		"ly_do": (d.custom_hddt_ly_do_thay_the or "").strip(),
		"thay_the": (d.custom_hddt_thay_the or "").strip(),
		"thay_the_luc": str(d.custom_hddt_thay_the_luc or "")[:16],
		"sua_duoc": 1 if _quyen_hddt_thay_the() else 0,
		"tep": _ds_bbtt(si_name),
		# Cau bat buoc phai nam tren to thay the theo Nghi dinh 123/2020.
		# Hien san tren man de ke toan chep sang M-Invoice, khoi go tay.
		"dien_giai": hoa_don_vat.dien_giai_thay_the(so_cu, kh, d.posting_date, mau),
	}


@frappe.whitelist()
def dinh_bien_ban_thay_the(si_name=None, ten=None, noi_dung=None):
	"""Dinh to bien ban thay the vao don hang. Khong nen, khong doi dinh dang."""
	_chan_khong_phai_ke_toan()
	d = _don_da_xuat(si_name)
	ten = str(ten or "").strip() or "bien-ban-thay-the.pdf"
	noi = str(noi_dung or "").strip()
	if not noi:
		frappe.throw("Chưa chọn tệp biên bản. Vui lòng bấm Chọn tệp rồi thử lại.")
	if "," in noi and noi[:5].lower() == "data:":
		noi = noi.split(",", 1)[1]
	try:
		so_byte = len(base64.b64decode(noi))
	except Exception:
		frappe.throw(
			"Tệp gửi lên bị hỏng giữa đường nên máy không đọc được. Vui lòng "
			"chọn lại tệp và thử lần nữa."
		)
	if so_byte <= 0:
		frappe.throw("Tệp biên bản rỗng. Vui lòng kiểm lại tệp trên máy.")
	if so_byte > 12 * 1024 * 1024:
		frappe.throw(
			"Tệp biên bản nặng %s MB, quá 12 MB nên máy không nhận. Vui lòng "
			"xuất lại bản PDF hoặc chụp nhỏ hơn."
			% ("{:.1f}".format(so_byte / 1024.0 / 1024.0))
		)
	f = frappe.get_doc({
		"doctype": "File",
		"file_name": DAU_BBTT + ten,
		"attached_to_doctype": "Sales Invoice",
		"attached_to_name": d.name,
		"content": noi,
		"decode": True,
		"is_private": 1,
	})
	f.flags.ignore_permissions = True
	f.insert()
	frappe.db.set_value("Sales Invoice", d.name, {"custom_hddt_sai_sot": 1},
		update_modified=False)
	_vet_don(d.name, "Đính biên bản thay thế: %s" % ten)
	frappe.db.commit()
	return {"ok": 1, "tep": f.name, "ghi_chu": "Đã đính biên bản %s." % ten}


@frappe.whitelist()
def go_bien_ban_thay_the(si_name=None, tep=None):
	"""Go mot to bien ban dinh nham. CHI BO LIEN KET, khong xoa tep.

	Chan theo trang thai: don DA GHI SO va DA co so hoa don thay the nghia
	la ho so thay the da khep lai, to bien ban trong do la can cu giai trinh
	voi co quan thue. Go ra la lam thung ho so (QT-20).
	"""
	_chan_khong_phai_ke_toan()
	d = frappe.db.get_value(
		"Sales Invoice", si_name,
		["name", "docstatus", "custom_hddt_thay_the"], as_dict=True,
	)
	if not d:
		frappe.throw("Không có đơn %s." % si_name)
	if (d.custom_hddt_thay_the or "").strip():
		frappe.throw(
			"Đơn %s đã ghi nhận tờ thay thế %s nên hồ sơ đã khép lại, không gỡ "
			"biên bản ra được nữa. Đính nhầm thì đính thêm tờ đúng vào, và báo "
			"bộ phận kỹ thuật." % (d.name, (d.custom_hddt_thay_the or "").strip())
		)
	f = frappe.db.get_value(
		"File",
		{"name": tep, "attached_to_doctype": "Sales Invoice", "attached_to_name": d.name},
		["name", "file_name"], as_dict=True,
	)
	if not f or not str(f.file_name or "").startswith(DAU_BBTT):
		frappe.throw(
			"Tệp này không phải biên bản thay thế của đơn %s. Vui lòng tải lại "
			"trang rồi bấm lại." % d.name
		)
	frappe.db.set_value("File", f.name, {
		"attached_to_doctype": None, "attached_to_name": None,
	}, update_modified=False)
	_vet_don(d.name, "Gỡ biên bản thay thế: %s" % str(f.file_name)[len(DAU_BBTT):])
	frappe.db.commit()
	return {"ok": 1, "loi_nhan": "Đã gỡ biên bản khỏi đơn %s." % d.name}


@frappe.whitelist()
def tai_bien_ban_thay_the(si_name=None, tep=None, co="lon"):
	"""Ruot mot to bien ban, tra base64 de man hinh ve hinh thu nho va tai ve.

	Chong doc chui: tep phai dang dinh vao DUNG don nay va phai mang dau
	BBTT-. Dua ma File cua don khac la bi tu choi, du ma do co that.
	"""
	_kiem_quyen()
	f = frappe.db.get_value(
		"File",
		{"name": tep, "attached_to_doctype": "Sales Invoice", "attached_to_name": si_name},
		["name", "file_name", "file_url"], as_dict=True,
	)
	if not f or not str(f.file_name or "").startswith(DAU_BBTT):
		frappe.throw(
			"Tệp này không phải biên bản thay thế của đơn %s. Vui lòng tải lại "
			"trang rồi bấm lại." % si_name
		)
	doc_tep = frappe.get_doc("File", f.name)
	try:
		ruot = doc_tep.get_content()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc bien ban thay the")
		frappe.throw(
			"Tệp %s có trong sổ nhưng máy đọc không ra nội dung. Có thể tệp đã "
			"bị gỡ trên Desk; vui lòng đính lại." % (f.file_name or tep)
		)
	if isinstance(ruot, str):
		ruot = ruot.encode("utf-8")
	thap = str(f.file_name or f.file_url or "").lower()
	mime = "application/octet-stream"
	if thap.endswith((".jpg", ".jpeg")):
		mime = "image/jpeg"
	elif thap.endswith((".png", ".webp", ".gif")):
		mime = "image/" + thap.rsplit(".", 1)[-1]
	elif thap.endswith(".pdf"):
		mime = "application/pdf"

	if (co or "") == "nho" and mime.startswith("image/"):
		try:
			from io import BytesIO

			from PIL import Image

			im = Image.open(BytesIO(ruot))
			im.thumbnail((360, 360))
			if im.mode not in ("RGB", "L"):
				im = im.convert("RGB")
			ra = BytesIO()
			im.save(ra, format="JPEG", quality=80)
			ruot = ra.getvalue()
			mime = "image/jpeg"
		except Exception:
			pass
	return {
		"ok": 1,
		"ten": str(f.file_name or "bien-ban-thay-the")[len(DAU_BBTT):] or "bien-ban-thay-the",
		"mime": mime,
		"b64": base64.b64encode(ruot).decode("ascii"),
	}


# ---------------------------------------------------------- tim mot don
#
# Anh Viet 18/08/2026: *"em viet script de co them o Tim kiem... cho tat ca
# cac man tinh tien o moi diem ban luon. Nhap bat cu thong tin gi thi cung
# se co the tim ra duoc don ay nhanh, hien tai anh dang phai do bang tay neu
# muon kiem lai 1 don nao do"*.
#
# Man Doanh thu Sales va man Bill quay deu xem theo NGAY. Muon tim lai mot
# don cu ma khong nho ngay thi phai lat tung ngay mot, do dung la do tay.
# Nen phep tim nay co y KHONG gioi han ngay.
#
# Tim tren nhung o nguoi ta thuc su nho: ma don Pancake, ma don ERP, so
# dien thoai, ten khach, dia chi, ma tham chieu chuyen khoan, so hoa don
# dien tu. O remarks la cho chua nhieu nhat vi khuon cua no la
# "<nguon> #<ma don> - <ten khach> - <so dien thoai>", nen mot cau LIKE tren
# do bat duoc ca ten lan so dien thoai.


def chuan_tim(s):
	"""Chuan hoa tu khoa tim. THUAN.

	Bo khoang trang thua va cac dau cau hay dinh vao khi chep dan: dau
	ngoac, dau cham cuoi cau, dau thang o dau ma don Pancake.
	"""
	t = str(s or "").strip()
	t = re.sub(r"^[#\s]+", "", t)
	t = re.sub(r"[\s]+", " ", t)
	return t.strip(" .,;:()[]")


def la_so_dien_thoai(s):
	"""Tu khoa nay trong nhu mot so dien thoai khong. THUAN.

	Dung de biet co nen do them ban BO SO 0 O DAU hay khong: nguoi ta luu
	"0933751352" nhung go tim "933751352" la chuyen thuong.
	"""
	t = re.sub(r"[^0-9]", "", str(s or ""))
	return len(t) >= 8 and len(t) <= 11


@frappe.whitelist()
def tim_don(tu_khoa="", so_dong=40):
	"""Tim hoa don ban hang theo bat ky manh thong tin nao. KHONG theo ngay.

	Tra ve danh sach gon de man hinh bay ra, moi dong du de nhan ra don va
	bam vao mo chi tiet.
	"""
	_kiem_quyen()
	tu = chuan_tim(tu_khoa)
	if len(tu) < 3:
		return {"ds": [], "vi_sao": "Vui lòng gõ ít nhất 3 ký tự rồi tìm."}

	mau = ["%%%s%%" % tu]
	# So dien thoai: do them ban bo so 0 o dau va ban chi con chu so, vi
	# nguoi ta hay go thieu so 0 hoac go kem dau cach.
	if la_so_dien_thoai(tu):
		chi_so = re.sub(r"[^0-9]", "", tu)
		mau.append("%%%s%%" % chi_so)
		if chi_so.startswith("0"):
			mau.append("%%%s%%" % chi_so[1:])
		else:
			mau.append("%%0%s%%" % chi_so)
	mau = list(dict.fromkeys(mau))

	o_tim = (
		"name", "custom_pancake_display_id", "custom_pancake_id",
		"vgb_ma_tham_chieu", "custom_hddt_so", "customer_name", "remarks",
		"vgb_xhd_ten", "vgb_xhd_mst", "vgb_xhd_dia_chi",
	)
	dieu, gia_tri = [], []
	for m in mau:
		for o in o_tim:
			dieu.append("`tabSales Invoice`.`%s` like %%s" % o)
			gia_tri.append(m)

	ds = frappe.db.sql(
		"""select name, posting_date, docstatus, grand_total, customer_name,
		       remarks, custom_pancake_display_id, custom_nguon,
		       vgb_pt_thanh_toan, custom_hddt_so, vgb_huy, vgb_quay
		from `tabSales Invoice`
		where (%s)
		order by posting_date desc, creation desc
		limit %d""" % (" or ".join(dieu), max(1, min(200, cint(so_dong) or 40))),
		tuple(gia_tri),
		as_dict=True,
	)
	gan_khach_vao_dong(ds)
	for d in ds:
		d["ngay"] = str(d.get("posting_date") or "")
	return {"ds": ds, "tu_khoa": tu, "vi_sao": "" if ds else (
		'Không thấy đơn nào khớp "%s". Thử gõ mã đơn Pancake, số điện thoại khách, hoặc một phần tên khách.' % tu
	)}
