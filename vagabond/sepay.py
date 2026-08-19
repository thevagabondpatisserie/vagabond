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
				"Chuỗi bí mật dán sang tab Bảo mật của webhook bên SePay. Không "
				"có khoá thì ai biết đường dẫn cũng bắn được giao dịch giả vào sổ."
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


def _khoa_gui_len():
	"""Khoa trong goi tin. Nhan ca ba cach SePay va cac he khac hay dung."""
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

	that = _khoa_that()
	if not that:
		return _tu_choi(403, "Chua dat khoa bao mat webhook trong Cai dat.")
	if not hmac.compare_digest(_khoa_gui_len(), that):
		return _tu_choi(401, "Khoa bao mat khong dung.")

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
	from urllib.parse import urlencode

	stg = frappe.get_doc(STG_SEPAY)
	tk = stg.get_password("api_token", raise_exception=False) or ""
	if not tk:
		frappe.throw(
			"SePay Settings chưa có api_token, không gọi được sang SePay. "
			"Vào SePay Settings dán token vào rồi chạy lại."
		)
	url = "%s?%s" % (USERAPI, urlencode(tham_so))
	res = frappe.make_get_request(
		url, headers={"Authorization": "Bearer " + tk, "Content-Type": "application/json"}
	)
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
	goc = (frappe.utils.get_url() or "").rstrip("/")
	ra = {
		"bat": cint(c.get("sepay_bat")),
		"co_khoa": 1 if _khoa_that() else 0,
		"duong_dan": goc + "/api/method/vagabond.sepay.webhook",
		"ban_do": _ban_do(),
		"chua_map": [x for x in str(c.get("sepay_chua_map") or "").split(",") if x.strip()],
		"sua_duoc": 1 if quan_ly else 0,
		"tai_khoan": [],
		"keo": {},
	}
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
	return {"khoa": moi, "duong_dan": (frappe.utils.get_url() or "").rstrip("/") + "/api/method/vagabond.sepay.webhook"}


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
