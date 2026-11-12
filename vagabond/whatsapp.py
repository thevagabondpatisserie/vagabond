"""Gui tin WhatsApp Business qua WhatsApp Cloud API cua Meta.

Anh Viet 07/08/2026: "Whatsapp Business co lam duoc khong thi lam them".

Noi thang truoc khi dung: khach Viet gan nhu khong dung WhatsApp, Zalo moi la
kenh chinh. Kenh nay dang de danh cho khach nuoc ngoai va khach o nuoc ngoai
dat banh gui ve. Vi vay he thong LUON gui Zalo truoc, chi gui WhatsApp khi
duoc yeu cau ro hoac khi Zalo tu choi.

Dieu kien de chay duoc, anh chi phai lam ben Meta Business:
1. Co tai khoan WhatsApp Business (WABA) va mot so dien thoai da xac thuc.
2. Lay Phone Number ID cua so do.
3. Tao mot System User token vinh vien co quyen whatsapp_business_messaging.
4. Tao mau tin (message template) loai UTILITY va cho Meta duyet. Mau phai co
   dung 3 tham so trong than tin theo thu tu: ma don, so tien, duong dan.

Ngoai cua so 24 tieng ke tu tin cuoi cua khach, Meta CHI cho gui tin theo mau
da duyet - khong gui duoc tin tu do. Nen bat buoc phai co mau.
"""

import hashlib
import hmac
import json
import re

import frappe

try:  # CI tay không có requests (mục E): nạp mềm, gọi mạng mới cần.
	import requests
except ImportError:  # pragma: no cover
	requests = None

from vagabond.lib import TIMEOUT, key

GRAPH = "https://graph.facebook.com/v21.0"

# v653 (anh Việt chốt 12/11/2026): WhatsApp là ĐƯỜNG PHỤ cho mã xác thực và
# ưu đãi, với MỌI số kể cả số Việt Nam: luôn gửi Zalo trước, Zalo hỏng mới
# gửi WhatsApp (vagabond/kenh_khach.py). Nhiều người ở Việt Nam không dùng
# Zalo, nên câu "chủ yếu cho khách nước ngoài" ở trên không còn đúng.
MAC_DINH = {
	"wa_phone_id": "1504016899452995",
	"wa_waba_id": "2041260756651836",
	"wa_template_otp": "vgb_otp_dang_nhap",
	"wa_template_uu_dai": "vgb_uu_dai",
	"wa_ngon_ngu": "vi",
}
NUT_NGUNG = "NGUNG_UU_DAI"
CHU_NGUNG = ("dừng", "dung", "ngừng", "ngung", "stop", "ngừng nhận ưu đãi", "ngung nhan uu dai")


# ------------------------------------------------------------------ THUẦN

def chi_so(v):
	"""Ô mã số người dán tay: bỏ dấu cách, dấu chấm, dấu cộng. THUẦN."""
	return re.sub(r"\D", "", str(v or ""))


def la_so_dien_thoai(v):
	"""Ô Phone Number ID đang chứa số điện thoại (84..., 0..., +84...) thay vì
	mã số Meta cấp (15 tới 17 chữ số). THUẦN."""
	x = chi_so(v)
	return bool(x) and (str(v or "").strip().startswith(("+", "0")) or (x.startswith("84") and len(x) in (11, 12)))


def token_sai_dang(tok):
	"""Câu báo nếu token trông như mật khẩu, không phải token Meta. THUẦN."""
	t = str(tok or "")
	if not t:
		return ""
	if re.search(r"\s", t) or len(t) < 60:
		return "Token WhatsApp sai dạng: token Meta dài trên 100 ký tự, không có dấu cách. Dán lại token của System User Vagabond ERP."
	return ""


def cau_hinh(c):
	"""Các ô WhatsApp đã làm sạch từ Vagabond Settings. THUẦN với `c` là dict."""
	c = c or {}
	return {
		"phone_id": chi_so(c.get("wa_phone_id")),
		"waba_id": chi_so(c.get("wa_waba_id")),
		"mau_otp": str(c.get("wa_template_otp") or "").strip(),
		"mau_uu_dai": str(c.get("wa_template_uu_dai") or "").strip(),
		"ngon_ngu": str(c.get("wa_ngon_ngu") or "vi").strip() or "vi",
	}


def can_dien(hien_tai):
	"""Ô WhatsApp bản vá v653 điền: chỉ ô ĐANG TRỐNG nhận mặc định; riêng ô
	Phone Number ID đang chứa số điện thoại (+84703418349) thì thay bằng mã Meta
	(anh Việt chọn A 12/11/2026). Ô đã có giá trị đúng không đụng; không bao giờ
	đụng token. THUẦN."""
	ra = {}
	for k, v in MAC_DINH.items():
		cu = str((hien_tai or {}).get(k) or "").strip()
		if not cu or (k == "wa_phone_id" and la_so_dien_thoai(cu)):
			ra[k] = v
	return ra


def than_tin(sdt84, ten_mau, ngon_ngu, components):
	"""Thân JSON gửi một tin theo mẫu. THUẦN."""
	return {
		"messaging_product": "whatsapp",
		"to": str(sdt84),
		"type": "template",
		"template": {"name": ten_mau, "language": {"code": ngon_ngu or "vi"}, "components": components or []},
	}


def comp_than(tham_so):
	return {"type": "body", "parameters": [{"type": "text", "text": str(v)} for v in (tham_so or [])]}


def comp_otp(ma):
	"""Mẫu Xác thực có nút Sao chép mã: thân một tham số là mã, nút index 0 kiểu
	url mang lại đúng mã (tài liệu Meta, Copy code authentication templates)."""
	return [comp_than([ma]), {"type": "button", "sub_type": "url", "index": "0",
		"parameters": [{"type": "text", "text": str(ma)}]}]


def comp_uu_dai(ten, noi_dung, han):
	"""Mẫu vgb_uu_dai: thân ba tham số; nút 0 là URL tĩnh (không gửi gì), nút 1
	trả lời nhanh mang payload cố định để điểm nhận sự kiện gỡ đồng ý."""
	return [comp_than([ten or "bạn", noi_dung, han]), {"type": "button", "sub_type": "quick_reply", "index": "1",
		"parameters": [{"type": "payload", "payload": NUT_NGUNG}]}]


def chu_ky_dung(than, chu_ky, bi_mat):
	"""X-Hub-Signature-256 = "sha256=" + HMAC-SHA256(app secret, thân thô). THUẦN."""
	if not (bi_mat and chu_ky and str(chu_ky).startswith("sha256=")):
		return False
	b = than if isinstance(than, bytes) else str(than or "").encode()
	mong = hmac.new(str(bi_mat).encode(), b, hashlib.sha256).hexdigest()
	return hmac.compare_digest(mong, str(chu_ky)[7:])


def so_xin_ngung(goi):
	"""Các số (84...) bấm Ngừng nhận ưu đãi hoặc nhắn "DỪNG" trong một gói sự
	kiện Meta. THUẦN."""
	ra = []
	for e in (goi or {}).get("entry") or []:
		for ch in e.get("changes") or []:
			for m in ((ch.get("value") or {}).get("messages") or []):
				so = chi_so(m.get("from"))
				t = m.get("type")
				nut = ((m.get("button") or {}).get("payload") or "") if t == "button" else ""
				tl = (((m.get("interactive") or {}).get("button_reply") or {}).get("id") or "") if t == "interactive" else ""
				chu = str(((m.get("text") or {}).get("body") or "")).strip().lower() if t == "text" else ""
				if so and (nut == NUT_NGUNG or tl == NUT_NGUNG or chu in CHU_NGUNG):
					ra.append(so)
	return ra


def chu_trang_thai(j):
	"""Trạng thái số từ GET /{phone_id}: nhãn người đọc và màu chip. THUẦN."""
	st = str((j or {}).get("status") or "").upper()
	if st == "CONNECTED":
		return {"nhan": "Đã kích hoạt", "chip": "ok"}
	if st == "PENDING":
		return {"nhan": "Chưa kích hoạt", "chip": "off"}
	return {"nhan": "Có sự cố", "chip": "err"}


# ------------------------------------------------------------- CHẠM HỆ

def _goi(phuong_thuc, duong, tok, than=None, params=None):
	if requests is None:
		return 0, {"error": {"message": "Máy chủ thiếu thư viện gọi mạng"}}
	try:
		r = requests.request(phuong_thuc, "%s/%s" % (GRAPH, duong), headers={"Authorization": "Bearer " + tok,
			"Content-Type": "application/json"}, json=than, params=params, timeout=TIMEOUT)
		return r.status_code, (r.json() if r.content else {})
	except Exception:
		frappe.log_error(title="Vagabond: WhatsApp loi mang", message=frappe.get_traceback())
		return 0, {"error": {"message": "Không gọi được WhatsApp"}}


def gui_mau(c, sdt84, ten_mau, tham_so, ngon_ngu=None, components=None):
	"""Gui mot tin theo mau da duyet. Tra ve (thanh_cong, loi).

	sdt84 dang 84xxxxxxxxx, khong dau cong - Meta nhan ca hai nhung de mot
	kieu cho khoi lech khi doi chieu.

	v653: `components` (nút Sao chép mã, nút trả lời nhanh) thay cho chỉ tham
	số thân khi được truyền.
	"""
	# Cung cai chan nhu ben Zalo, them 25/08/2026. `thanh_toan.py` goi CA HAI
	# duong cho mot tin yeu cau thanh toan, nen chan mot ben ma bo ben kia
	# thi ca kiem tich hop van ban tin that ra dien thoai khach that.
	#
	# Diem luu cua co so du lieu lui lai duoc mot chung tu ao. No khong lui
	# lai duoc mot tin nhan da toi tay nguoi ta.
	if frappe.flags.get("vagabond_kiem_that"):
		return False, "Dang chay kiem thu tich hop nen khong gui WhatsApp"
	phone_id = chi_so(c.get("wa_phone_id"))
	tok = key(c, "wa_token")
	if not (phone_id and tok):
		return False, "Chưa điền Phone Number ID hoặc token WhatsApp trong Vagabond Settings"
	if not ten_mau:
		return False, "Chưa khai tên mẫu tin WhatsApp trong Vagabond Settings"
	than = than_tin(sdt84, ten_mau, (ngon_ngu or c.get("wa_ngon_ngu") or "vi").strip(),
		components if components is not None else [comp_than(tham_so)])
	ma, j = _goi("POST", "%s/messages" % phone_id, tok, than)
	if ma not in (200, 201) or (j or {}).get("error"):
		frappe.log_error(title="Vagabond: WhatsApp tu choi tin", message=json.dumps(j)[:1000])
		loi = ((j or {}).get("error") or {}).get("message") or "WhatsApp từ chối tin"
		return False, loi
	return True, ""


def _chi_quan_tri():
	if "System Manager" not in set(frappe.get_roles()):
		frappe.throw("Chỉ quản trị hệ thống (System Manager) làm việc này.", frappe.PermissionError)


def _cfg():
	from vagabond.lib import cfg

	return cfg()


@frappe.whitelist()
def trang_thai():
	"""Trạng thái số WhatsApp cho màn Cài đặt lõi: một lần GET /{phone_id}.
	Không bao giờ trả token, PIN hay app secret ra trình duyệt; chỉ chip đã
	khai hay chưa."""
	_chi_quan_tri()
	c = _cfg()
	h = cau_hinh(c)
	tok = key(c, "wa_token")
	ra = {"khai": {"token": 1 if tok else 0, "pin": 1 if key(c, "wa_pin") else 0,
		"app_secret": 1 if key(c, "wa_app_secret") else 0, "verify_token": 1 if key(c, "wa_verify_token") else 0},
		"token_loi": token_sai_dang(tok), "so_la_sdt": 1 if la_so_dien_thoai(c.get("wa_phone_id")) else 0}
	if not (h["phone_id"] and tok) or ra["token_loi"] or ra["so_la_sdt"]:
		ra.update(nhan="Chưa đủ thông tin", chip="off")
		return ra
	ma, j = _goi("GET", h["phone_id"], tok, params={"fields": "status,name_status,quality_rating,display_phone_number,verified_name"})
	if (j or {}).get("error"):
		ra.update(nhan="Có sự cố", chip="err", loi=((j.get("error") or {}).get("message") or "")[:300])
		return ra
	ra.update(chu_trang_thai(j), so=(j or {}).get("display_phone_number") or "", ten=(j or {}).get("verified_name") or "")
	return ra


@frappe.whitelist(methods=["POST"])
def kich_hoat():
	"""Nút "Kích hoạt số WhatsApp": POST /{phone_id}/register với PIN hai bước
	đọc trong máy chủ. Chạy lại được (Meta trả thành công khi đã đăng ký)."""
	_chi_quan_tri()
	c = _cfg()
	h = cau_hinh(c)
	tok, pin = key(c, "wa_token"), chi_so(key(c, "wa_pin"))
	if not (h["phone_id"] and tok):
		frappe.throw("Điền Phone Number ID và token WhatsApp, bấm Lưu, rồi bấm lại.")
	if len(pin) != 6:
		frappe.throw("Điền PIN 6 số xác minh hai bước vào ô PIN WhatsApp, bấm Lưu, rồi bấm lại.")
	ma, j = _goi("POST", "%s/register" % h["phone_id"], tok, {"messaging_product": "whatsapp", "pin": pin})
	if (j or {}).get("error") or ma not in (200, 201):
		frappe.log_error(title="Vagabond: kich hoat so WhatsApp", message=json.dumps(j)[:1000])
		frappe.throw("Meta chưa nhận kích hoạt: %s. Kiểm lại PIN hai bước rồi bấm lại." % ((j.get("error") or {}).get("message") or "lỗi không rõ"))
	return trang_thai()


@frappe.whitelist(methods=["POST"])
def dang_ky_su_kien():
	"""Nút "Đăng ký nhận sự kiện": POST /{waba_id}/subscribed_apps."""
	_chi_quan_tri()
	c = _cfg()
	h = cau_hinh(c)
	tok = key(c, "wa_token")
	if not (h["waba_id"] and tok):
		frappe.throw("Điền mã tài khoản WhatsApp Business (WABA ID) và token, bấm Lưu, rồi bấm lại.")
	ma, j = _goi("POST", "%s/subscribed_apps" % h["waba_id"], tok)
	if (j or {}).get("error") or not (j or {}).get("success"):
		frappe.throw("Meta chưa nhận đăng ký sự kiện: %s." % (((j or {}).get("error") or {}).get("message") or "lỗi không rõ"))
	return {"ok": 1}


def ngung_uu_dai(so84, luc=None):
	"""Gỡ đồng ý nhận tin ưu đãi của số này bằng đúng hàm đồng ý của CRM, nơi
	ghi WhatsApp. Không có hồ sơ khách thì không có gì để gỡ."""
	from vagabond import crm
	from vagabond.lib import sdt

	so0 = sdt(so84)
	if not so0:
		return 0
	n = 0
	for kh in frappe.get_all(crm.DT_HO_SO, filters={"sdt": ["in", [so0, chi_so(so84)]]}, pluck="name", limit_page_length=20):
		r = crm.ghi_dong_y_noi(kh, {"Zalo": "Từ chối"}, "WhatsApp", cau_hoi=crm.CAU_HOI_NGUNG_WA, nguoi="Guest")
		n += int(r.get("doi") or 0)
	return n


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def webhook(**_ts):
	"""Điểm nhận sự kiện WhatsApp của Meta.

	GET: Meta kiểm đường dẫn, trả hub.challenge khi hub.verify_token khớp ô
	Verify token. POST: kiểm X-Hub-Signature-256 bằng App Secret, sai thì 401
	không ghi gì; đúng thì gỡ đồng ý ưu đãi của số bấm Ngừng nhận ưu đãi. Lỗi
	xử lý thì ghi Error Log và vẫn trả 200 để Meta không bắn lại mãi."""
	from werkzeug.wrappers import Response

	c = _cfg()
	req = frappe.request
	if req is not None and req.method == "GET":
		fd = frappe.form_dict or {}
		vt = key(c, "wa_verify_token")
		if vt and fd.get("hub.mode") == "subscribe" and hmac.compare_digest(str(fd.get("hub.verify_token") or ""), str(vt)):
			return Response(str(fd.get("hub.challenge") or ""), mimetype="text/plain")
		return Response("forbidden", status=403, mimetype="text/plain")
	than = req.get_data() if req is not None else b""
	if not chu_ky_dung(than, frappe.get_request_header("X-Hub-Signature-256") or "", key(c, "wa_app_secret")):
		return Response("chu ky sai", status=401, mimetype="text/plain")
	try:
		goi = json.loads(than.decode("utf-8") or "{}")
		for so in so_xin_ngung(goi):
			ngung_uu_dai(so)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Vagabond: WhatsApp xử lý sự kiện", message=frappe.get_traceback())
	return Response("ok", mimetype="text/plain")
