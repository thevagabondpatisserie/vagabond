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

import hmac
import json
import re
import time
import unicodedata

import frappe
import requests
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

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

from vagabond import chung_tu, diem_ban, pt_thanh_toan, quyen_quay, tai_khoan
from vagabond.kiem_banh import _keo_don, _khoang_unix
from vagabond.vagabond.doctype.anh_xa_ma_si.anh_xa_ma_si import doi_ma as doi_ma_si
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
		# Anh xa ma si ve ma banh goc (anh Viet chot huong B 03/08/2026): moi
		# khach si co ma rieng tren Pancake nhung ve Next thi gop lai mot ma
		# banh that de ton kho va gia von khong bi chia vun. GIA giu nguyen
		# theo dong don, tuc dung gia si cua khach do, khong lay bang gia cua
		# ma goc. Dong nao chua tich "Dang ap dung" thi giu nguyen ma si.
		ma = doi_ma_si(ma)
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
	con_dung = {p["ten"] for p in pt_thanh_toan.ds(chi_dung=True)}
	# Mot nguon co the thuoc nhieu diem ("Tại chỗ" chung cho moi quay), nen
	# phai biet TAT CA diem cua no truoc khi dung dong nguon do.
	chu = {}
	for d in diem_ban.ds(chi_bat=True):
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
				m["pt"] = pt_thanh_toan.ten_quay() if d["quay"] else pt_thanh_toan.ten_online()
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
		if not d or not d["quay"]:
			frappe.throw("Mã quầy %s không có trong danh sách điểm bán." % q)
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
	nguon = NGUON_CU.get((nguon or "").strip(), (nguon or "").strip())
	if not nguon or nguon == "Pancake":
		return pt_thanh_toan.ten_online()
	for n in _nguon_don():
		if n["v"] == nguon:
			return list(n["pt"])
	return pt_thanh_toan.ten_quay()


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
	pt = (pt or "").strip()
	if not pt:
		return ""
	if not pt_thanh_toan.theo_ten(pt):
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
	return {
		"pt": pt,
		"nguon": nguon,
		"pt_pancake": pt_thanh_toan.ten_online(),
		"quay": quay,
		# Anh chi nhanh Sales Online (307/1 Nguyen Van Troi) anh Viet gui
		# 11/08/2026. Doi anh trong app thi lay anh moi, chua doi thi dung
		# anh nay.
		"anh_sales": _anh_quay_da_luu("SALES") or "/assets/vagabond/images/quay-sales.jpg",
		"qr_quay": tai_khoan.tk_cho(),
		# Tai khoan ao rieng cua tung nguon don, de man tinh tien sinh QR
		# vao dung tai khoan cua nguon do.
		"qr_nguon": tai_khoan.bang_theo_nguon(nguon),
		"thu_tu_nhom": THU_TU_NHOM,
		"pt_chua_ve_tien": pt_thanh_toan.chua_ve_tien(),
		"pt_ve_sau": pt_thanh_toan.ve_sau(),
		# De app biet luc nao phai hoi ma OTP. May chu van kiem lai het, day
		# chi la de khoi bat thu ngan go ma cho mot viec ho duoc phep lam.
		"quyen_bo_mon": quyen_quay.muc(),
		"nguon_app": [n["v"] for n in nguon if n.get("lg")],
	}


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


def _chuan_mst(s):
	"""Chuan hoa ma so thue ve DUNG dinh dang cua Tong cuc Thue.

	- Doanh nghiep: 10 chu so.
	- Don vi phu thuoc (chi nhanh, van phong dai dien): 13 chu so, viet
	  CO DAU GACH NGANG dang 10 so - 3 so. Thong tu 86/2024/TT-BTC hieu luc
	  06/02/2025 quy dinh cau truc N1..N10-N11N12N13. Khong co dang 4 so
	  sau gach ngang.

	Truoc day may bo sach ky tu khong phai so nen "0311638525-027" bi luu
	thanh "0311638525027". Hai he thong ben ngoai deu tu choi dang do:
	  - VietQR tra code 52 "Ma so thue khong chinh xac" nen dong bo ve khong
	    ra duoc ten va dia chi cong ty;
	  - m-invoice tra code 296 "Create invoice fail" nen khong ghi so duoc.
	Bat duoc 12/08/2026 tren don HDB-2026-01520, chi nhanh ACV Long Thanh.

	Tra chuoi rong neu khong phai 10 hoac 13 so.
	"""
	so = re.sub(r"\D", "", str(s or ""))
	if len(so) == 10:
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
		kq = {"tao_moi": 0, "cap_nhat": 0, "da_chot": 0, "loi": []}
		for o in dons:
			try:
				tt, ghi_chu = _upsert_hoa_don(o, ngay, cong_ty, khach)
				if tt in ("tao_moi", "cap_nhat", "da_chot"):
					kq[tt] += 1
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
	ma_dons = [str(m).strip() for m in (ma_dons or []) if str(m or "").strip().isdigit()]
	shop_id = str(shop_id or "").strip()
	if not (shop_id and ma_dons):
		return {}
	mau = "S%sO(%s)T" % (shop_id, "|".join(sorted(set(ma_dons))))
	try:
		gds = frappe.db.sql(
			"""select description, deposit, withdrawal, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and description regexp %s""",
			mau,
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc giao dich SePay")
		return {}
	re_don = re.compile(r"S%sO(\d+)T" % re.escape(shop_id), re.IGNORECASE)
	ra = {}
	for g in gds:
		m = re_don.search(g.get("description") or "")
		if not m:
			continue
		o = ra.setdefault(m.group(1), {"nhan": 0.0, "ma": "", "so_gd": 0})
		o["nhan"] += flt(g.get("deposit")) - flt(g.get("withdrawal"))
		o["so_gd"] += 1
		if not o["ma"]:
			o["ma"] = (g.get("reference_number") or "").strip()
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
		},
		fields=[
			"name",
			"docstatus",
			"grand_total",
			"remarks",
			"custom_pancake_id",
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

	return {
		"ngay": str(ngay),
		"dong_bo_luc": cache_get("bh_luc_%s" % ngay) or "",
		"rows": sis,
		"loi": loi,
		"tong_nhap": sum(s.grand_total for s in sis if s.docstatus == 0),
		"tong_chot": sum(s.grand_total for s in sis if s.docstatus == 1),
		"so_don_trung": len([1 for v in dem.values() if v > 1]),
	}


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
		_dong_bo_doanh_so(nowdate(), im_lang=True)
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
	pt = _kiem_pt(si.vgb_pt_thanh_toan, si.custom_nguon)
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
	if pt:
		si.vgb_pt_thanh_toan = pt
	if ma_tham_chieu is not None:
		si.vgb_ma_tham_chieu = ma_tham_chieu
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
			"Mã số thuế phải 10 số, hoặc 13 số dạng 10 số - 3 số cho chi nhánh "
			"(ví dụ 0311638525-027)."
		)
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
	if str(c.get("tu_ghi_so_lan_cuoi") or "") == ngay:
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
	try:
		_dong_bo_doanh_so(ngay)
	except Exception:
		# Pancake hong hay thieu khoa API thi van ghi so nhung don da ve.
		frappe.db.rollback()
		frappe.local.message_log = []
		frappe.log_error(frappe.get_traceback(), "ban_hang cuoi ngay: keo don lan cuoi")

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
		ds = frappe.db.get_all("Sales Invoice", filters=loc_sales, pluck="name")
		if quay_bat:
			ds += frappe.db.get_all(
				"Sales Invoice",
				filters={
					"posting_date": ngay,
					"docstatus": 0,
					"vgb_quay": ["in", quay_bat],
					"vgb_tam_tinh": 0,
					"vgb_huy": 0,
				},
				pluck="name",
			)

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
			"discount_amount": flt(giam_gia) + km_giam,
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
			"Mã số thuế phải 10 số, hoặc 13 số dạng 10 số - 3 số cho chi nhánh "
			"(ví dụ 0311638525-027)."
		)
	if so_mst:
		if not (xhd_ten or "").strip():
			frappe.throw("Có mã số thuế thì phải có tên pháp nhân.")
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

RE_MA_BILL = re.compile(r"VGB[A-Z0-9]{5}")


def _sepay_theo_ma_bill(ds_ma):
	"""Tien SePay da nhan theo MA BILL QUAY (VGBxxxxx trong noi dung CK).

	Khac voi don Pancake khop mach S<shop>O<don>T, bill quay in ma VGB len
	ma QR nen ngan hang tra description chua nguyen ma do.
	"""
	ds_ma = [str(m).strip().upper() for m in (ds_ma or []) if RE_MA_BILL.fullmatch(str(m or "").strip().upper())]
	if not ds_ma:
		return {}
	mau = "(%s)" % "|".join(sorted(set(ds_ma)))
	try:
		gds = frappe.db.sql(
			"""select description, deposit, withdrawal, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and description regexp %s""",
			mau, as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang: doc SePay theo ma bill")
		return {}
	ra = {}
	for g in gds:
		for m in RE_MA_BILL.findall((g.get("description") or "").upper()):
			if m not in ds_ma:
				continue
			o = ra.setdefault(m, {"nhan": 0.0, "ma": "", "so_gd": 0})
			o["nhan"] += flt(g.get("deposit")) - flt(g.get("withdrawal"))
			o["so_gd"] += 1
			if not o["ma"]:
				o["ma"] = (g.get("reference_number") or "").strip()
	return ra


@frappe.whitelist()
def pos_kiem_sepay(noi_dung=None, tien=0):
	"""Man tinh tien goi vai giay mot lan khi dang chia QR chuyen khoan:
	khach chuyen den noi la cashier thay ngay tren man hinh, khoi mo app
	ngan hang hay cho Lark."""
	_kiem_quyen()
	g = _sepay_theo_ma_bill([noi_dung]).get(str(noi_dung or "").strip().upper()) or {}
	nhan = flt(g.get("nhan"))
	return {"nhan": nhan, "du": 1 if nhan >= flt(tien) - 1 else 0, "ma": g.get("ma") or ""}


@frappe.whitelist()
def pos_ds_bill(quay=None, ngay=None):
	"""Danh sach bill trong ngay cua MOT quay, kem tinh trang SePay va HDDT."""
	_kiem_quyen()
	quay = (quay or "").strip()
	if not quay:
		frappe.throw("Thiếu mã quầy.")
	ngay = getdate(ngay or nowdate())
	ds = frappe.get_all(
		"Sales Invoice",
		filters={"vgb_quay": quay, "posting_date": str(ngay), "docstatus": ["<", 2]},
		fields=[
			"name", "creation", "docstatus", "grand_total", "discount_amount", "total_qty",
			"custom_nguon", "custom_pancake_display_id", "remarks", "owner",
			"vgb_tam_tinh", "vgb_pt_thanh_toan", "vgb_ma_tham_chieu", "vgb_ghi_chu",
			"vgb_xhd_ten", "vgb_xhd_mst", "vgb_so_ban",
			"vgb_huy", "vgb_huy_ly_do", "vgb_huy_boi", "vgb_lan_sua",
			"custom_hddt_so", "custom_hddt_trang_thai",
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	sepay = _sepay_theo_ma_bill(
		[r.vgb_ma_tham_chieu for r in ds if (r.vgb_pt_thanh_toan or "") == "Chuyển khoản"]
	)
	ma_trung = _ma_trung_trong_ngay(ngay, [r.vgb_ma_tham_chieu for r in ds])
	for r in ds:
		g = sepay.get(str(r.vgb_ma_tham_chieu or "").upper()) or {}
		r["sepay_nhan"] = flt(g.get("nhan"))
		r["sepay_du"] = 1 if r["sepay_nhan"] >= flt(r.grand_total) - 1 else 0
		r["trung_ma"] = 1 if str(r.vgb_ma_tham_chieu or "").upper() in ma_trung else 0
	return {"ngay": str(ngay), "bill": ds}


def _pos_lay(name):
	si = frappe.get_doc("Sales Invoice", name)
	if not (si.get("vgb_quay") or "").strip():
		frappe.throw("Phiếu này không phải bill quầy.")
	return si


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
		si.vgb_pt_thanh_toan = pt
		si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
		if si.vgb_ma_tham_chieu:
			_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
	if ghi_chu is not None:
		si.vgb_ghi_chu = (ghi_chu or "").strip()
	if giam_gia is not None:
		si.apply_discount_on = "Grand Total"
		si.discount_amount = flt(giam_gia)
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
	"""
	_kiem_quyen()
	si = _pos_lay(name)
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
		si.discount_amount = flt(giam_gia)
		doi.append("giảm giá")
	if pt:
		pt = _kiem_pt(pt, si.custom_nguon)
		si.vgb_pt_thanh_toan = pt
		si.vgb_ma_tham_chieu = _chuan_ma_tham_chieu(pt, ma_tham_chieu, bat_buoc=False)
		if si.vgb_ma_tham_chieu:
			_kiem_trung_ma(pt, si.vgb_ma_tham_chieu, bo_qua=si.name)
		doi.append("phương thức thanh toán")
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
				"Mã số thuế phải 10 số, hoặc 13 số dạng 10 số - 3 số cho chi nhánh "
				"(ví dụ 0311638525-027)."
			)
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
	pt = _kiem_pt(si.vgb_pt_thanh_toan, si.custom_nguon)
	if not pt:
		frappe.throw("Bill chưa chọn phương thức thanh toán.")
	if pt == "Chuyển khoản":
		ma = str(si.vgb_ma_tham_chieu or "").strip().upper()
		g = _sepay_theo_ma_bill([ma]).get(ma) or {}
		nhan = flt(g.get("nhan"))
		if nhan < flt(si.grand_total) - 1:
			frappe.throw(
				"Bill %s ghi Chuyển khoản nhưng ngân hàng mới nhận %s đ trên tổng %s đ. "
				"Chờ tiền về rồi ghi sổ, hoặc khách chuyển sai nội dung thì tìm mã giao "
				"dịch trong sao kê gõ vào ô Mã tham chiếu."
				% (si.name, _tien(nhan), _tien(si.grand_total))
			)
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
		frappe.throw("Thiếu mã quầy.")
	ngay = getdate(ngay or nowdate())
	ds = frappe.get_all(
		"Sales Invoice",
		filters={"vgb_quay": quay, "posting_date": str(ngay), "docstatus": ["<", 2]},
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
	sepay = _sepay_theo_ma_bill(
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
	chua_ve = {"so": 0, "tien": 0.0, "dong": []}
	for k, v in pt_tong.items():
		if k in cho_ve:
			chua_ve["so"] += v["so"]
			chua_ve["tien"] += v["tien"]
			chua_ve["dong"].append({"pt": k, "so": v["so"], "tien": v["tien"]})
	chua_ve["dong"].sort(key=lambda x: -x["tien"])
	return {
		"quay": quay,
		"ngay": str(ngay),
		"chua_ve": chua_ve,
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
		frappe.throw("Mã số thuế phải 10 hoặc 13 số.")
	ten = (ten or "").strip()
	if not ten:
		frappe.throw("Thiếu tên pháp nhân trên hoá đơn.")
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
