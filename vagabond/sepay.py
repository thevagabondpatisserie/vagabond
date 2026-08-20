# -*- coding: utf-8 -*-
"""Nhan giao dich ngan hang tu SePay trong VAI GIAY thay vi cho tron mot gio.

Vi sao co tep nay
-----------------
Ngay 19/08/2026 Uyen bao sao ke OCB keo ve bi thieu giao dich. Doc lai moi
ra hai su that:

Mot, he thong khong he NHAN webhook. No KEO. Trong site co mot Server
Script "SePay - Dong bo giao dich (hang gio)" goi userapi cua SePay moi
gio mot lan. Bang chung khong the choi: trong 800 dong Bank Transaction
gan nhat, 671 dong sinh ra o phut 00 va 116 dong o phut 01. Webhook that
thi gio tao phai rai deu theo luc khach chuyen khoan.

Hai, kich ban keo do dung con tro since_id va day con tro cho MOI giao
dich trong lo, KE CA giao dich bi bo qua vi so tai khoan chua co trong
ban do. Tai khoan OCB chi duoc them vao ban do dau thang 8, nen toan bo
giao dich OCB cu hon da bi con tro vuot qua vinh vien. SePay giu 1.135
giao dich OCB, ERPNext chi co 63 dong va dong som nhat la 03/08.

Tep nay chua ca hai:
  webhook()  diem nhan that, SePay goi ngay khi tien ve
  nap_bu()   di lay lai nhung giao dich con tro da bo qua

Nguyen tac
----------
1. CHONG TRUNG DUNG MOT CACH voi kich ban keo: transaction_id la
   "SEPAY-<id>". Hai duong cung ghi mot khoa nen khong bao gio sinh hai
   dong cho mot giao dich, du webhook va nhip keo chay chong len nhau.
2. WEBHOOK KHONG BAO GIO TRA LOI 500 cho mot goi da doc duoc. SePay bat
   "tu dong gui lai khi server tra loi", nen mot loi that cua minh se
   thanh mot vong gui lai vo tan. Doc khong duoc thi ghi Error Log roi
   van tra ve success.
3. KHONG DUNG VAO last_since_id cua kich ban keo. Hai duong doc lap, moi
   duong giu con tro cua no, hong duong nay khong keo do duong kia.
"""

import hmac
import json

import frappe
from frappe.utils import cint, flt

from vagabond.lib import cfg, key

BT = "Bank Transaction"
STG_SEPAY = "SePay Settings"

# Moi dong Bank Transaction do SePay sinh ra deu mang tien to nay o
# transaction_id. Kich ban keo dung dung chuoi nay tu truoc, doi mot ky tu
# la mat toan bo phep chong trung.
TIEN_TO = "SEPAY-"

USERAPI = "https://my.sepay.vn/userapi/transactions/list"

# Duong dan diem nhan, khong kem ten mien. Man hinh ghep voi ten mien
# nguoi dung dang mo, vi ten mien noi bo cua Frappe Cloud khong phai cai
# de dan sang SePay.
DUONG_DAN = "/api/method/vagabond.sepay.webhook"


# --------------------------------------------------------------- cau hinh


TRUONG_MOI = {
	"Vagabond Settings": [
		{
			"fieldname": "sec_sepay", "label": "SePay - nhận giao dịch ngân hàng",
			"fieldtype": "Section Break", "insert_after": "tk_hoan_tien",
		},
		{
			"fieldname": "sepay_bat", "label": "Nhận webhook SePay",
			"fieldtype": "Check", "insert_after": "sec_sepay", "default": "0",
			"description": (
				"Bật thì SePay đẩy giao dịch về ngay khi tiền vào, thay vì chờ "
				"nhịp kéo hàng giờ. Tắt thì điểm nhận từ chối mọi gói."
			),
		},
		{
			"fieldname": "sepay_khoa", "label": "Khoá bảo mật webhook SePay",
			"fieldtype": "Password", "insert_after": "sepay_bat",
			"description": (
				"Chuỗi bí mật dán sang tab Bảo mật của webhook bên SePay, gửi ở "
				"header X-Api-Key (KHÔNG dùng Authorization, Frappe chặn header "
				"đó trước khi vào tới đây). Không có khoá thì ai biết đường dẫn "
				"cũng bắn được giao dịch giả vào sổ."
			),
		},
		{
			"fieldname": "sepay_hmac", "label": "Khoá HMAC-SHA256 của webhook SePay",
			"fieldtype": "Password", "insert_after": "sepay_khoa",
			"description": (
				"Secret Key dạng whsec_... lấy ở tab Bảo mật bên SePay khi chọn "
				"HMAC-SHA256. Đây là cách nên dùng: SePay ký cả gói tin nên đổi "
				"một đồng trong đó là chữ ký hỏng, và chữ ký đi ở header "
				"X-SePay-Signature mà Frappe không đụng tới."
			),
		},
		{
			"fieldname": "sepay_hmac_2", "label": "Khoá HMAC webhook thứ hai (ACB)",
			"fieldtype": "Password", "insert_after": "sepay_hmac",
			"description": (
				"Secret Key của webhook THỨ HAI bên SePay, dùng khi mỗi tài "
				"khoản ngân hàng (OCB, ACB...) có một webhook riêng và SePay "
				"sinh cho mỗi cái một khoá khác nhau. Cả hai webhook trỏ về "
				"cùng một đường dẫn, máy tự thử lần lượt từng khoá."
			),
		},
		{
			"fieldname": "sepay_khoa_2", "label": "Khoá dự phòng thứ hai (ACB)",
			"fieldtype": "Password", "insert_after": "sepay_hmac_2",
			"description": (
				"Khoá X-Api-Key dự phòng cho webhook thứ hai, chỉ dùng khi "
				"webhook đó không chọn được HMAC."
			),
		},
		{
			"fieldname": "sepay_chua_map", "label": "Số tài khoản SePay chưa khai",
			"fieldtype": "Small Text", "insert_after": "sepay_khoa", "read_only": 1,
			"description": (
				"Máy tự ghi vào đây khi nhận giao dịch của một số tài khoản chưa "
				"có trong account_map. Chưa khai thì giao dịch bị bỏ qua lặng lẽ, "
				"đúng vết xe đổ của OCB hồi đầu tháng 8."
			),
		},
	]
}


def _ban_do():
	"""Ban do so tai khoan -> Bank Account, doc chung voi kich ban keo."""
	try:
		stg = frappe.get_doc(STG_SEPAY)
		return json.loads(stg.get("account_map") or "{}") or {}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sepay: doc ban do tai khoan")
		return {}


def _khoa_that():
	try:
		return key(cfg(), "sepay_khoa")
	except Exception:
		return ""


def _cac_khoa(ten_goc):
	"""Ca hai khe khoa cua mot loai (sepay_khoa / sepay_hmac).

	Tu 20/08/2026 chay song song hai webhook - OCB va ACB - va SePay sinh
	cho moi webhook mot Secret Key rieng, nguoi dung khong tu chon duoc.
	Nen diem nhan phai thu lan luot tung khoa; khop mot cai la du.
	"""
	ra = []
	c = cfg()
	for ten in (ten_goc, ten_goc + "_2"):
		try:
			k = key(c, ten)
		except Exception:
			k = ""
		if k:
			ra.append(k)
	return ra


def _khoa_gui_len():
	"""Khoa trong goi tin. Nhan ca ba cach SePay va cac he khac hay dung.

	QUAN TRONG - KHONG DUNG HEADER "Authorization" voi diem nhan nay.
	Nghiem thu that ngay 19/08/2026 tren site: goi tin mang
	"Authorization: Apikey <khoa>" bi chinh FRAPPE tra 401 AuthenticationError
	TRUOC KHI vao den ham nay. Frappe doc header do de tim khoa API cua no,
	gap mot kieu la thi tu choi ca yeu cau. Goi tin mang "X-Api-Key" thi vao
	binh thuong va tra ve 200.

	Van doc "Authorization" o day de phong Frappe doi cach xu ly ve sau,
	nhung huong dan tren man Cai dat phai la X-Api-Key.
	"""
	try:
		h = frappe.request.headers
	except Exception:
		return ""
	for ten in ("Authorization", "X-Api-Key", "X-Sepay-Key"):
		v = (h.get(ten) or "").strip()
		if not v:
			continue
		for tien_to in ("Apikey ", "ApiKey ", "Bearer ", "Token "):
			if v.lower().startswith(tien_to.lower()):
				return v[len(tien_to):].strip()
		return v
	return ""


def _than_tho():
	"""Nguyen van goi tin, dang byte. HMAC phai ky tren dung chuoi nay."""
	try:
		return frappe.request.get_data() or b""
	except Exception:
		return b""


def _chu_ky_gui_len():
	"""Chu ky SePay gui kem. Header X-SePay-Signature, Frappe khong dung toi."""
	try:
		h = frappe.request.headers
	except Exception:
		return ""
	for ten in ("X-SePay-Signature", "X-Sepay-Signature", "X-Signature"):
		v = (h.get(ten) or "").strip()
		if v:
			return v
	return ""


def _tach_chu_ky(tho):
	"""Boc lay phan chu ky that trong mot header co the co nhieu dang.

	Cac dang gap ngoai doi: chu ky tran, "sha256=<chu ky>", va dang nhieu
	phan cach nhau bang dau phay kieu "t=<moc gio>,v1=<chu ky>". Nhan het
	de khong phai doan dung mot dang roi hong ca duong nhan.
	"""
	t = str(tho or "").strip()
	if not t:
		return []
	ra = []
	for phan in t.split(","):
		phan = phan.strip()
		if not phan:
			continue
		if "=" in phan:
			ten, _, gt = phan.partition("=")
			ten = ten.strip().lower()
			# "sha256=abc" hoac "v1=abc" thi lay phan sau; "t=1699" la moc
			# gio, bo qua.
			if ten in ("t", "timestamp"):
				continue
			ra.append(gt.strip())
			if ten in ("sha256", "v1", "signature", "sig"):
				continue
		ra.append(phan)
	return [x for x in dict.fromkeys(ra) if x]


def _moc_gio_gui_len():
	"""Moc gio SePay gui kem, header X-SePay-Timestamp.

	Nghiem thu 21/08/2026 tren nhat ky gui that cua SePay: moi goi tin deu
	mang ca X-SePay-Signature va X-SePay-Timestamp. Nhieu he ky tren chuoi
	GHEP moc gio voi than goi chu khong ky rieng than, nen phai giu lay con
	so nay de con thu.
	"""
	try:
		h = frappe.request.headers
	except Exception:
		return ""
	for ten in ("X-SePay-Timestamp", "X-Sepay-Timestamp", "X-Timestamp"):
		v = (h.get(ten) or "").strip()
		if v:
			return v
	return ""


def _cac_chuoi_ky(than, moc):
	"""Cac chuoi CO THE da duoc ky, thu lan luot.

	Vi sao phai thu nhieu: webhook "ERP Next" cua tiem tra 401 lien tuc 328
	lan trong ngay 20/08/2026, va tai lieu cong khai cua SePay khong noi ro
	chuoi ky gom nhung gi. Bon dang duoi day la bon cach cac cong thanh toan
	hay dung. Thu them mot dang khong lam yeu xac thuc: van phai co dung
	khoa bi mat moi tinh ra duoc chu ky, chi la minh khong con phai doan
	dung mot cach ghep.
	"""
	ra = [than]
	if moc:
		m = moc.encode("utf-8")
		ra.append(m + b"." + than)
		ra.append(m + than)
		ra.append(than + m)
	return ra


def _hmac_dung(khoa, than, moc=None):
	"""Cac dang chu ky hop le cho mot khoa va mot goi tin. Hex va base64."""
	import base64
	import hashlib

	ra = set()
	for chuoi in _cac_chuoi_ky(than, moc):
		tho = hmac.new(khoa.encode("utf-8"), chuoi, hashlib.sha256).digest()
		ra.add(tho.hex())
		ra.add(tho.hex().upper())
		ra.add(base64.b64encode(tho).decode())
	return ra


def _kiem_hmac():
	"""Xac thuc bang chu ky HMAC-SHA256 cua SePay.

	Tra ve (co_dung_duong_nay, dat_hay_khong). Chua khai khoa hoac goi tin
	khong mang chu ky thi tra (False, False) de duong X-Api-Key con co co
	hoi chay.
	"""
	cac_khoa = _cac_khoa("sepay_hmac")
	gui = _chu_ky_gui_len()
	if not cac_khoa or not gui:
		return False, False

	than = _than_tho()
	moc = _moc_gio_gui_len()
	dung = set()
	for khoa in cac_khoa:
		dung |= _hmac_dung(khoa, than, moc)
	for x in _tach_chu_ky(gui):
		for y in dung:
			if hmac.compare_digest(x, y):
				return True, True

	# Sai chu ky. Ghi lai DU de doi chieu ma KHONG ghi khoa: chu ky nhan
	# duoc, va vai ky tu dau cua chu ky minh tinh ra. Neu SePay ky tren mot
	# chuoi khac (vi du co them moc gio o dau) thi day la thu duy nhat noi
	# ra dieu do, khoi phai doan lan nua.
	try:
		frappe.log_error(
			"Chu ky nhan duoc: %s\nMoc gio nhan duoc: %s\n"
			"Do dai goi tin: %d byte\nSo khoa da thu: %d\n"
			"So cach ghep chuoi ky da thu: %d\n"
			"Chu ky may tinh ra (hex, 12 ky tu dau): %s\n\n"
			"Da thu ca bon cach ghep (than; moc.than; moc+than; than+moc) "
			"voi moi khoa dang khai. Van khong khop nghia la KHOA BI MAT "
			"dang luu trong Cai dat khac voi khoa ben SePay: vao Cai dat, "
			"the SePay, dan lai Secret Key cua webhook do."
			% (gui[:200], moc or "(khong co)", len(than), len(cac_khoa),
			   len(_cac_chuoi_ky(than, moc)), sorted(dung)[0][:12]),
			"sepay: chu ky HMAC khong khop",
		)
	except Exception:
		pass
	return True, False


# --------------------------------------------------------------- diem nhan


@frappe.whitelist(allow_guest=True)
def webhook():
	"""SePay goi vao day moi khi co giao dich. Tra ve trong vai chuc mili giay.

	Duong dan day du de dan sang SePay:
	  https://<ten mien>/api/method/vagabond.sepay.webhook
	"""
	try:
		return _webhook()
	except Exception:
		# Da vao duoc den day thi goi tin doc duoc, loi la loi cua minh.
		# Tra ve success de SePay dung gui lai vo tan; dau vet nam o Error Log.
		frappe.log_error(frappe.get_traceback(), "sepay: webhook vo loi")
		return {"success": True, "message": "Da ghi nhan, dang xu ly ben trong."}


def _tu_choi(ma, loi):
	frappe.local.response["http_status_code"] = ma
	return {"success": False, "message": loi}


def _webhook():
	if not cint(cfg().get("sepay_bat")):
		return _tu_choi(403, "Diem nhan SePay dang tat trong Cai dat.")

	# Hai duong xac thuc, thu HMAC truoc.
	#
	# Vi sao uu tien HMAC: SePay ky ca goi tin nen doi mot dong trong do la
	# chu ky hong, con khoa bi mat thi chi chung minh "nguoi goi biet khoa".
	# Va quan trong hon ve mat ky thuat, chu ky di o header
	# X-SePay-Signature ma Frappe khong dung toi - trong khi duong API Key
	# cua SePay bat buoc gui o header Authorization, va Frappe tra 401 cho
	# header do truoc khi goi tin vao toi day (nghiem thu 19/08/2026).
	co_hmac, hmac_dat = _kiem_hmac()
	if co_hmac:
		if not hmac_dat:
			return _tu_choi(401, "Chu ky HMAC khong dung.")
	else:
		cac = _cac_khoa("sepay_khoa")
		if not cac:
			return _tu_choi(
				403,
				"Chưa đặt khoá bảo mật webhook trong Cài đặt. Vào Cài đặt, thẻ "
				"SePay, dán Secret Key HMAC của SePay vào hoặc sinh khoá mới.",
			)
		gui_len = _khoa_gui_len()
		if not any(hmac.compare_digest(gui_len, k) for k in cac):
			return _tu_choi(401, "Khoá bảo mật không đúng.")

	goi = frappe.local.form_dict or {}
	try:
		if frappe.request and frappe.request.data:
			goi = json.loads(frappe.request.data) or goi
	except Exception:
		pass
	if not isinstance(goi, dict):
		return _tu_choi(400, "Goi tin khong phai JSON.")

	tid = str(goi.get("id") or "").strip()
	if not tid:
		return _tu_choi(400, "Goi tin thieu truong id cua giao dich.")

	ma = TIEN_TO + tid
	if frappe.db.exists(BT, {"transaction_id": ma}):
		# Nhip keo hang gio da lay truoc, hoac SePay gui lai. Ca hai truong
		# hop deu la binh thuong, khong phai loi.
		return {"success": True, "message": "Giao dich %s da co trong so." % ma}

	so_tk = str(goi.get("accountNumber") or "").strip()
	tk = _ban_do().get(so_tk)
	if not tk:
		# Tra ve success: day KHONG phai loi cua SePay, gui lai bao nhieu lan
		# cung the. Ghi lai de man Cai dat bay ra cho anh Viet khai bo sung.
		_ghi_chua_map(so_tk, tid)
		return {"success": True, "message": "So tai khoan %s chua khai trong ban do." % so_tk}

	vao = str(goi.get("transferType") or "").strip().lower() == "in"
	tien = abs(flt(goi.get("transferAmount")))
	bt = frappe.get_doc({
		"doctype": BT,
		"date": str(goi.get("transactionDate") or "")[:10],
		"bank_account": tk,
		"deposit": tien if vao else 0.0,
		"withdrawal": 0.0 if vao else tien,
		"currency": "VND",
		"description": goi.get("content") or goi.get("description") or "",
		"reference_number": goi.get("referenceCode") or "",
		"transaction_id": ma,
	})
	bt.insert(ignore_permissions=True)
	bt.submit()
	frappe.db.commit()

	# Doi soat ngay cho phieu thanh toan noi bo (anh Viet 20/08/2026): tien ra
	# tu OCB khop noi dung thi phieu chuyen sang "Da chi" trong vai giay, thay
	# vi cho toi nhip chay theo gio.
	#
	# Boc trong try o ben trong ham do: dong sao ke DA ghi xong roi, mot loi o
	# buoc doi soat khong duoc phep lam hong phan hoi tra ve cho SePay - hong
	# la ho gui lai mai.
	try:
		from vagabond import de_nghi_chi

		de_nghi_chi.khi_co_giao_dich(bt.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sepay: goi doi soat TTNB loi")
	return {"success": True, "message": "Da ghi %s." % bt.name}


def _ghi_chua_map(so_tk, tid):
	"""Nho lai cac so tai khoan chua khai, de man Cai dat noi ro thay vi im."""
	try:
		cu = [x for x in str(cfg().get("sepay_chua_map") or "").split(",") if x.strip()]
		if so_tk and so_tk not in cu:
			cu.append(so_tk)
			frappe.db.set_single_value("Vagabond Settings", "sepay_chua_map", ",".join(cu[:20]))
			frappe.db.commit()
	except Exception:
		frappe.log_error(
			"So tai khoan %s (giao dich %s) chua co trong account_map cua SePay Settings."
			% (so_tk, tid),
			"sepay: tai khoan chua khai",
		)


# ------------------------------------------------------------------ nap bu


def _goi_userapi(tham_so):
	"""Goi userapi cua SePay. Tra ve danh sach giao dich.

	frappe.make_get_request KHONG ton tai trong Python thuong. No chi co
	trong khong gian ten cua Server Script - Frappe tiem san vao do. Kich
	ban keo hang gio la Server Script nen goi thang duoc; tep nay la ma
	nguon that nen phai import cho tu te. Bat duoc luc chay thu nap bu tren
	site that ngay 19/08/2026, ngay sau khi deploy v229.
	"""
	from urllib.parse import urlencode

	stg = frappe.get_doc(STG_SEPAY)
	tk = stg.get_password("api_token", raise_exception=False) or ""
	if not tk:
		frappe.throw(
			"SePay Settings chưa có api_token, không gọi được sang SePay. "
			"Vào SePay Settings dán token vào rồi chạy lại."
		)
	url = "%s?%s" % (USERAPI, urlencode(tham_so))
	dau = {"Authorization": "Bearer " + tk, "Content-Type": "application/json"}
	try:
		from frappe.integrations.utils import make_get_request

		res = make_get_request(url, headers=dau)
	except ImportError:
		import requests

		r = requests.get(url, headers=dau, timeout=30)
		r.raise_for_status()
		res = r.json()
	return (res or {}).get("transactions") or []


@frappe.whitelist()
def nap_bu(so_tk="", tu_ngay="", den_ngay="", so_trang=40, that=0):
	"""Di lay lai nhung giao dich con tro since_id da bo qua.

	CHI THEM, khong sua va khong xoa dong nao: moi dong deu qua phep kiem
	transaction_id da ton tai chua. Chay lai lan thu muoi cung ra ket qua
	nhu lan dau.

	that=0 la chay thu, chi dem xem se them bao nhieu dong chu khong ghi gi.
	Bat that=1 moi ghi that.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới nạp bù sao kê được.")

	ban_do = _ban_do()
	if not ban_do:
		frappe.throw(
			"SePay Settings chưa khai account_map nên không biết giao dịch thuộc "
			"tài khoản ngân hàng nào trong ERPNext."
		)
	so_tk = str(so_tk or "").strip()
	if so_tk and so_tk not in ban_do:
		frappe.throw(
			"Số tài khoản %s chưa có trong account_map. Các số đang khai: %s."
			% (so_tk, ", ".join(sorted(ban_do)) or "(chưa có)")
		)

	moc = 0
	them, bo_qua, da_co, chua_map, tong = 0, 0, 0, {}, 0
	dong_moi = []
	for _ in range(max(1, min(cint(so_trang) or 40, 200))):
		ts = {"limit": 200, "since_id": moc}
		if so_tk:
			ts["account_number"] = so_tk
		if tu_ngay:
			ts["transaction_date_min"] = str(tu_ngay)[:10] + " 00:00:00"
		if den_ngay:
			ts["transaction_date_max"] = str(den_ngay)[:10] + " 23:59:59"
		lo = _goi_userapi(ts)
		if not lo:
			break
		tong += len(lo)
		for t in lo:
			tid = cint(t.get("id"))
			if tid > moc:
				moc = tid
			tk = ban_do.get(str(t.get("account_number") or "").strip())
			if not tk:
				chua_map[str(t.get("account_number") or "")] = chua_map.get(str(t.get("account_number") or ""), 0) + 1
				bo_qua += 1
				continue
			if frappe.db.exists(BT, {"transaction_id": TIEN_TO + str(tid)}):
				da_co += 1
				continue
			if not cint(that):
				them += 1
				if len(dong_moi) < 20:
					dong_moi.append({
						"ngay": str(t.get("transaction_date") or "")[:10],
						"vao": flt(t.get("amount_in")),
						"ra": flt(t.get("amount_out")),
						"noi_dung": (t.get("transaction_content") or "")[:120],
					})
				continue
			bt = frappe.get_doc({
				"doctype": BT,
				"date": str(t.get("transaction_date") or "")[:10],
				"bank_account": tk,
				"deposit": flt(t.get("amount_in")),
				"withdrawal": flt(t.get("amount_out")),
				"currency": "VND",
				"description": t.get("transaction_content") or "",
				"reference_number": t.get("reference_number") or "",
				"transaction_id": TIEN_TO + str(tid),
			})
			bt.insert(ignore_permissions=True)
			bt.submit()
			them += 1
		if cint(that):
			frappe.db.commit()
		if len(lo) < 200:
			break

	return {
		"that": 1 if cint(that) else 0,
		"tong_doc": tong,
		"them": them,
		"da_co": da_co,
		"bo_qua": bo_qua,
		"chua_map": chua_map,
		"vi_du": dong_moi,
	}


# --------------------------------------------------------------- tinh trang


@frappe.whitelist()
def tinh_trang():
	"""Man Cai dat: duong dan webhook, khoa, va so lieu tung tai khoan."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	quan_ly = bool({"System Manager", "Accounts Manager"} & set(frappe.get_roles()))
	c = cfg()
	# frappe.utils.get_url() tra ve ten mien NOI BO cua Frappe Cloud
	# (vagabond.s.frappe.cloud) chu khong phai ten mien anh Viet dang dung.
	# Ca hai deu vao dung mot site, nhung dan cho SePay thi phai la ten mien
	# that. Nen tra ve DUONG DAN khong co ten mien, de man hinh ghep voi
	# chinh ten mien nguoi dung dang mo.
	goc = (frappe.utils.get_url() or "").rstrip("/")
	ra = {
		"bat": cint(c.get("sepay_bat")),
		"co_khoa": 1 if _khoa_that() else 0,
		"co_hmac": 1 if (key(c, "sepay_hmac") if c else "") else 0,
		"co_hmac_2": 1 if (key(c, "sepay_hmac_2") if c else "") else 0,
		"co_khoa_2": 1 if (key(c, "sepay_khoa_2") if c else "") else 0,
		"duong_dan_path": DUONG_DAN,
		"duong_dan": goc + DUONG_DAN,
		"ban_do": _ban_do(),
		"chua_map": [x for x in str(c.get("sepay_chua_map") or "").split(",") if x.strip()],
		"sua_duoc": 1 if quan_ly else 0,
		"tai_khoan": [],
		"keo": {},
	}
	# Danh sach tai khoan ngan hang de o "Them vao ban do" co cai ma chon.
	try:
		ra["ds_tai_khoan"] = frappe.get_all(
			"Bank Account", filters={"is_company_account": 1},
			pluck="name", limit_page_length=50,
		) or frappe.get_all("Bank Account", pluck="name", limit_page_length=50)
	except Exception:
		ra["ds_tai_khoan"] = []
	try:
		stg = frappe.get_doc(STG_SEPAY)
		ra["keo"] = {
			"bat": cint(stg.get("enabled")),
			"lan_cuoi": str(stg.get("last_sync") or ""),
			"ket_qua": str(stg.get("last_error") or "")[:200],
			"con_tro": str(stg.get("last_since_id") or ""),
		}
	except Exception:
		pass
	try:
		rows = frappe.db.sql(
			"""select bank_account, count(*) so, min(date) dau, max(date) cuoi
			from `tabBank Transaction` where docstatus < 2 group by bank_account""",
			as_dict=True,
		)
		ra["tai_khoan"] = rows
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sepay: dem giao dich")
	return ra


def dau_khoa(k):
	"""Dau van tay cua mot khoa: dai bao nhieu, bon ky tu cuoi la gi. THUAN.

	KHONG BAO GIO tra ve ca khoa. Bon ky tu cuoi du de nguoi dung liec mat
	doi chieu voi ben SePay, ma lo ra thi khong ai doan nguoc duoc.
	"""
	k = str(k or "").strip()
	if not k:
		return {"co": 0, "dai": 0, "duoi": ""}
	return {"co": 1, "dai": len(k), "duoi": k[-4:] if len(k) > 8 else "..."}


@frappe.whitelist()
def soi_khoa():
	"""Bon o khoa dang giu gi, de doi chieu voi ben SePay ma khong lo khoa.

	Sinh ra toi 20/08/2026: webhook "ERP Next" tra 401 lien tuc, anh Viet
	bao da dan lai Secret Key roi. Doc log thi biet chu ky khong khop nhung
	khong biet vi sao. Cho de nham nhat la man Cai dat co HAI o khoa khac
	nhau - mot o cho X-Api-Key, mot o cho Secret Key HMAC - dan nham o thi
	duong HMAC van doc khoa cu.

	Man hinh bay bon van tay nay ra thi ba giay la biet dan dung o chua.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới soi được khoá bảo mật.")
	c = cfg()
	ra = {}
	for o in ("sepay_khoa", "sepay_khoa_2", "sepay_hmac", "sepay_hmac_2"):
		try:
			ra[o] = dau_khoa(key(c, o))
		except Exception:
			ra[o] = {"co": 0, "dai": 0, "duoi": ""}
	ra["duong_dang_chay"] = "HMAC" if (ra["sepay_hmac"]["co"] or ra["sepay_hmac_2"]["co"]) else "X-Api-Key"
	ra["ghi_chu"] = (
		"Secret Key bên SePay phải nằm ở ô HMAC. Đối chiếu bốn ký tự cuối "
		"với chuỗi bên SePay; lệch là dán nhầm ô."
	)
	return ra


@frappe.whitelist()
def dat_hmac(khoa=None, khe=1):
	"""Cat Secret Key HMAC do SePay sinh ra.

	Khoa nay do SePay sinh, nguoi dung tu dan vao - may khong tu lay duoc,
	va cung khong nen: no la khoa cua ben thu ba.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới đặt được khoá bảo mật.")
	# khe 2 la webhook thu hai (ACB): moi webhook ben SePay co mot Secret
	# Key rieng do ho sinh, nen phai co hai o chua.
	o = "sepay_hmac" if cint(khe) != 2 else "sepay_hmac_2"
	k = str(khoa or "").strip()
	if not k:
		frappe.db.set_single_value("Vagabond Settings", o, "")
		frappe.db.commit()
		frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
		return {"ok": 1, "co_hmac": 0, "khe": cint(khe) or 1}
	if len(k) < 12:
		frappe.throw(
			"Chuỗi này ngắn quá, không giống Secret Key của SePay. Khoá thật "
			"bắt đầu bằng whsec_ và dài vài chục ký tự. Anh chị copy lại từ tab "
			"Bảo mật bên SePay giúp em."
		)
	frappe.db.set_single_value("Vagabond Settings", o, k)
	frappe.db.set_single_value("Vagabond Settings", "sepay_bat", 1)
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	return {"ok": 1, "co_hmac": 1, "khe": cint(khe) or 1}


@frappe.whitelist()
def them_tai_khoan(so_tk=None, tai_khoan=None):
	"""Khai them mot so tai khoan (vd ACB) vao ban do ngay tren man Cai dat.

	Truoc day ban do chi sua duoc bang tay trong SePay Settings tren Desk,
	va OCB da tung mat ca thang giao dich chi vi chua ai khai. Gio man Cai
	dat khai duoc luon, va khai xong thi so tai khoan do bien khoi danh
	sach "chua khai".

	CHI THEM VA DOI, khong xoa: go mot dong khoi ban do la giao dich cua
	tai khoan do bat dau roi lang le, viec do phai lam co y thuc tren Desk.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới khai được bản đồ tài khoản.")
	so_tk = "".join(ch for ch in str(so_tk or "") if ch.isdigit())
	if not so_tk or len(so_tk) < 6:
		frappe.throw(
			"Số tài khoản trông chưa đúng (%s). Gõ đúng dãy số tài khoản như "
			"bên SePay hiển thị giúp em." % (so_tk or "trống")
		)
	tk = str(tai_khoan or "").strip()
	if not tk or not frappe.db.exists("Bank Account", tk):
		frappe.throw(
			"Chưa chọn tài khoản ngân hàng trong ERPNext để hứng giao dịch. "
			"Nếu ACB chưa có trong danh sách thì tạo Bank Account trên Desk "
			"trước rồi quay lại đây."
		)
	stg = frappe.get_doc(STG_SEPAY)
	ban_do = {}
	try:
		ban_do = json.loads(stg.get("account_map") or "{}") or {}
	except Exception:
		ban_do = {}
	ban_do[so_tk] = tk
	stg.account_map = json.dumps(ban_do, ensure_ascii=False, indent=1)
	stg.flags.ignore_permissions = True
	stg.save(ignore_permissions=True)
	# Ra khoi danh sach "chua khai" neu dang nam trong do.
	cu_ds = [x for x in str(cfg().get("sepay_chua_map") or "").split(",") if x.strip()]
	if so_tk in cu_ds:
		cu_ds.remove(so_tk)
		frappe.db.set_single_value("Vagabond Settings", "sepay_chua_map", ",".join(cu_ds))
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	return {"ok": 1, "ban_do": ban_do}


@frappe.whitelist()
def dat_khoa():
	"""Sinh mot khoa moi cho webhook. Tra ve nguyen van DUNG MOT LAN de dan."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới đặt được khoá bảo mật.")
	import secrets

	moi = secrets.token_urlsafe(32)
	frappe.db.set_single_value("Vagabond Settings", "sepay_khoa", moi)
	frappe.db.set_single_value("Vagabond Settings", "sepay_bat", 1)
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	return {
		"khoa": moi,
		"duong_dan_path": DUONG_DAN,
		"duong_dan": (frappe.utils.get_url() or "").rstrip("/") + DUONG_DAN,
	}


# ------------------------------------------------- doi chieu tay tien vao


@frappe.whitelist()
def tim_gd_vao(so_tien=0, ngay="", tu_khoa="", so_ngay=30):
	"""Cac giao dich TIEN VAO co the la khoan khach da chuyen cho mot don.

	Vi sao can den ban tay. Cach doi soat tu dong cua he dua HOAN TOAN vao
	noi dung chuyen khoan: no tim mach S<shop>O<so don>T do Pancake sinh ra
	trong ma QR. Khach nao tu go noi dung, vi du "TRUONG LINH GIANG chuyen
	tien", thi khong mach nao de bam, va don do mai mai trong nhu chua nhan
	dong nao - du tien da nam trong tai khoan cong ty.

	Man hinh khong duoc tu quyet. No chi bay ra cac giao dich gan dung so
	tien va gan dung ngay, roi de nguoi doc mat nhin va chon.
	"""
	from vagabond.ban_hang import _kiem_quyen
	from frappe.utils import add_days, nowdate

	_kiem_quyen()
	tien = flt(so_tien)
	moc = str(ngay or "")[:10] or nowdate()
	n = max(1, min(cint(so_ngay) or 30, 180))
	loc = [
		["date", "between", [add_days(moc, -n), add_days(moc, n)]],
		["deposit", ">", 0],
		["docstatus", "<", 2],
	]
	ds = frappe.get_all(
		BT, filters=loc,
		fields=["name", "date", "deposit", "description", "reference_number",
		        "transaction_id", "bank_account"],
		order_by="date desc", limit_page_length=400,
	)
	tk = str(tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		lech = abs(flt(r["deposit"]) - tien)
		if tien > 0 and lech > 0.5 and lech > tien * 0.02:
			continue
		if tk and tk not in (r.get("description") or "").lower():
			continue
		r["lech"] = lech
		r["cach_ngay"] = abs(frappe.utils.date_diff(r["date"], moc))
		ra.append(r)
	ra.sort(key=lambda r: (r["lech"], r["cach_ngay"]))
	return {"rows": ra[:40], "so_tien": tien, "moc": moc}
