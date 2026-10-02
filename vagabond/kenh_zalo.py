# -*- coding: utf-8 -*-
"""Bắn tin ERP vào nhóm Zalo qua Zalo Bot (#410, bản thử v555).

Anh Việt 02/10/2026: muốn ERP tự bắn tin vào nhóm của từng bộ phận, có chỗ
điền nhóm, tin chia loại. Ban đầu bàn Lark, sau chọn Zalo vì nhân viên quen
dùng. Codex góp ý thiết kế trên #410; tệp này làm phần lõi theo góp ý đó:

  - MỘT hàm `bao()` cho mọi nơi trong app gọi; gửi SAU commit qua hàng đợi,
    Zalo lỗi không bao giờ làm hỏng chứng từ (khuôn của dat_ban.py).
  - Năm loại tin, mỗi loại một biểu tượng đầu tin (Zalo Bot chỉ gửi chữ).
  - Giờ im theo từng nhóm: chỉ Cảnh báo vượt giờ im; tin khác hoãn, hết giờ
    im thì gửi MỘT tin tổng hợp còn tồn, không xả từng tin cũ.
  - Chống trùng: khoá = sự kiện + nhóm, ghi vào "Vagabond Tin Kenh" với tên
    bản ghi CHÍNH LÀ khoá, nên hai worker cùng claim thì một bên vấp khoá
    chính và bỏ qua. Timeout ghi "Chưa rõ", không hứa tuyệt đối không trùng
    vì Zalo không có khoá idempotency.
  - Token bot nằm ở ô Password; không đưa token, nội dung tin hay chat_id
    vào Error Log.

Zalo Bot API (bot.zaloplatforms.com): gọi `https://bot-api.zaloplatforms.com
/bot<token>/<method>`, trả {ok, result | error_code, description}. Nhận cập
nhật qua webhook có header `X-Bot-Api-Secret-Token`. Nhóm: thêm bot vào
nhóm, ai đó @nhắc bot một lần để máy biết mã nhóm. Chưa có tài liệu chính
thức đọc được trong phiên làm (trang docs chặn đọc tự động); các điểm trên
đối chiếu từ SDK và tài liệu tích hợp bên thứ ba, cần kiểm bằng gửi thử.
"""

import hmac
import json
import secrets

import frappe
from frappe.utils import cint, get_url, now_datetime

API = "https://bot-api.zaloplatforms.com"
TIMEOUT = 10
TOI_DA_KY_TU = 2000
GIU_CHAT_MOI = 20

# Mã loại -> (biểu tượng, tên). Thứ tự là thứ tự hiện trong Cài đặt.
LOAI = {
	"thong_bao": ("ℹ️", "Thông báo"),
	"viec": ("✅", "Việc cần làm"),
	"canh_bao": ("🚨", "Cảnh báo"),
	"ban_tin": ("📊", "Bản tin"),
	"phat_hanh": ("🚀", "Phát hành"),
}
CHU_DE = ("kho", "san_xuat", "cong_no", "ban_hang", "don_web", "dat_ban", "phat_hanh")


# ------------------------------------------------------------------ THUẦN

def tach_ds(s):
	"""THUẦN: "viec, canh_bao" -> {"viec", "canh_bao"}; rỗng -> set()."""
	return {x.strip() for x in str(s or "").replace(";", ",").split(",") if x.strip()}


def soan_tin(loai, tieu_de, dong=None, link=None, nguoi=None, han=None):
	"""THUẦN: một tin chữ cho Zalo, không quá TOI_DA_KY_TU ký tự.

	Codex #410: tin nói rõ việc gì, ai phụ trách, hạn, một đường mở đúng màn."""
	bt, ten = LOAI.get(loai, ("ℹ️", "Thông báo"))
	ra = ["%s %s: %s" % (bt, ten.upper(), (tieu_de or "").strip())]
	for d in (dong or []):
		d = str(d or "").strip()
		if d:
			ra.append("- " + d)
	if nguoi:
		ra.append("Phụ trách: %s" % nguoi)
	if han:
		ra.append("Hạn: %s" % han)
	if link:
		ra.append("Mở: %s" % link)
	tin = "\n".join(ra)
	if len(tin) > TOI_DA_KY_TU:
		duoi = ("\nMở: %s" % link) if link else ""
		tin = tin[:TOI_DA_KY_TU - len(duoi) - 2].rstrip() + "…" + duoi
	return tin


def _phut(hhmm):
	s = str(hhmm or "").strip()
	if not s:
		return None
	try:
		p = s.split(":")
		return int(p[0]) * 60 + int(p[1] if len(p) > 1 else 0)
	except Exception:
		return None


def trong_gio_im(gio, im_tu, im_den):
	"""THUẦN: gio "HH:MM" có nằm trong [im_tu, im_den) không; qua nửa đêm được."""
	a, b, g = _phut(im_tu), _phut(im_den), _phut(gio)
	if a is None or b is None or g is None or a == b:
		return False
	return a <= g < b if a < b else (g >= a or g < b)


def chon_nhom(ds, loai, chu_de):
	"""THUẦN: các dòng nhóm nhận tin (loai, chu_de). Dòng là dict.

	Loại hoặc chủ đề để trống = nhận tất. Thiếu mã chat hoặc tắt thì bỏ."""
	ra = []
	for r in ds or []:
		if not cint(r.get("bat")) or not str(r.get("chat_id") or "").strip():
			continue
		lt, cd = tach_ds(r.get("loai_tin")), tach_ds(r.get("chu_de"))
		if lt and loai not in lt:
			continue
		if cd and chu_de and chu_de not in cd:
			continue
		ra.append(r)
	return ra


def khoa_tin(khoa_su_kien, nhom):
	"""THUẦN: tên bản ghi chống trùng, gọn trong 140 ký tự."""
	import hashlib
	tho = "%s|%s" % (khoa_su_kien or "", nhom or "")
	return "ZL-" + hashlib.sha1(tho.encode("utf-8")).hexdigest()[:24]


def doc_ket_qua(goi):
	"""THUẦN: (trạng thái, lỗi) từ JSON Zalo trả về."""
	if isinstance(goi, dict) and goi.get("ok") is True:
		return "Đã gửi", ""
	if isinstance(goi, dict):
		return "Lỗi", ("Zalo báo lỗi %s: %s" % (goi.get("error_code", "?"), goi.get("description", "")))[:300]
	return "Chưa rõ", "Zalo trả về dữ liệu lạ."


def ghi_chat_moi(ds, cap_nhat, luc):
	"""THUẦN: thêm cuộc chat vừa nhắn bot vào đầu danh sách, bỏ trùng, giữ 20."""
	msg = (cap_nhat or {}).get("message") or (cap_nhat or {}).get("result", {}).get("message") or {}
	chat = msg.get("chat") or {}
	cid = str(chat.get("id") or "").strip()
	if not cid:
		return ds or [], None
	nguoi = (msg.get("from") or {}).get("display_name") or ""
	moi = {"chat_id": cid, "loai": chat.get("chat_type") or chat.get("type") or "",
		"ten": chat.get("title") or chat.get("display_name") or nguoi, "nguoi": nguoi, "luc": str(luc)[:16]}
	con = [x for x in (ds or []) if x.get("chat_id") != cid]
	return ([moi] + con)[:GIU_CHAT_MOI], moi


# --------------------------------------------------------------- CHẠM HỆ

def _token():
	try:
		return frappe.get_single("Vagabond Settings").get_password("zalo_bot_token", raise_exception=False) or ""
	except Exception:
		return ""


def _bat():
	return cint(frappe.db.get_single_value("Vagabond Settings", "zalo_bot_bat"))


def _cac_nhom():
	return [r.as_dict() for r in (frappe.get_single("Vagabond Settings").get("zalo_nhom") or [])]


def _goi(method, body):
	"""Gọi Zalo Bot API. Trả (trạng thái, lỗi, kết quả). Không ghi token ra đâu."""
	tk = _token()
	if not tk:
		return "Lỗi", "Chưa điền token Zalo Bot trong Cài đặt.", None
	try:
		import requests
		r = requests.post("%s/bot%s/%s" % (API, tk, method), json=body, timeout=TIMEOUT)
		try:
			goi = r.json()
		except Exception:
			return "Lỗi", "Zalo trả HTTP %s không đọc được." % r.status_code, None
		tt, loi = doc_ket_qua(goi)
		return tt, loi, (goi.get("result") if isinstance(goi, dict) else None)
	except Exception as e:
		# Timeout: tin có thể đã tới; ghi Chưa rõ để người đối chiếu, không gửi lại tự động.
		if "Timeout" in type(e).__name__:
			return "Chưa rõ", "Zalo không trả lời trong %s giây." % TIMEOUT, None
		return "Lỗi", "Không gọi được Zalo (%s)." % type(e).__name__, None


def _gui_zalo(chat_id, tin):
	tt, loi, _ = _goi("sendMessage", {"chat_id": str(chat_id), "text": tin})
	return tt, loi


def bao(loai, chu_de, tieu_de, dong=None, link=None, khoa=None, nguoi=None, han=None):
	"""Điểm gọi DUY NHẤT cho mọi nơi trong app. Không bao giờ ném lỗi ra ngoài.

	khoa: mã sự kiện để chống trùng (ví dụ "cho_duyet:PKT-2026-00067").
	Thiếu khoa thì không chống trùng (chỉ dùng cho tin một lần)."""
	try:
		if getattr(frappe.flags, "vagabond_kiem_that", False) or not _bat():
			return
		tin = {"loai": loai, "chu_de": chu_de, "tieu_de": tieu_de, "dong": list(dong or []),
			"link": link, "khoa": khoa, "nguoi": nguoi, "han": han}
		frappe.db.after_commit.add(lambda: _xep(tin))
	except Exception:
		frappe.log_error("Chưa xếp được tin Zalo loại %s." % loai, "kenh_zalo: bao loi")


def _xep(tin):
	try:
		frappe.enqueue("vagabond.kenh_zalo.gui_hang_doi", queue="short", tin=tin)
	except Exception:
		frappe.log_error("Chưa xếp được tin Zalo loại %s vào hàng đợi." % tin.get("loai"), "kenh_zalo: hang doi loi")
		frappe.db.commit()


def gui_hang_doi(tin):
	"""Chạy trong worker: mỗi nhóm khớp một bản ghi, claim bằng khoá chính rồi gửi."""
	if not _bat():
		return
	gio = now_datetime().strftime("%H:%M")
	noi_dung = soan_tin(tin.get("loai"), tin.get("tieu_de"), tin.get("dong"), tin.get("link"),
		tin.get("nguoi"), tin.get("han"))
	for n in chon_nhom(_cac_nhom(), tin.get("loai"), tin.get("chu_de")):
		ten = khoa_tin(tin.get("khoa") or frappe.generate_hash(length=12), n.get("ten_nhom"))
		hoan = tin.get("loai") != "canh_bao" and trong_gio_im(gio, n.get("im_tu"), n.get("im_den"))
		try:
			frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": ten, "khoa": ten,
				"nhom": n.get("ten_nhom"), "chat_id": n.get("chat_id"), "loai": tin.get("loai"),
				"chu_de": tin.get("chu_de"), "noi_dung": noi_dung,
				"trang_thai": "Hoãn giờ im" if hoan else "Đang gửi"}).insert(ignore_permissions=True)
			frappe.db.commit()
		except frappe.DuplicateEntryError:
			frappe.db.rollback()
			continue
		if hoan:
			continue
		tt, loi = _gui_zalo(n.get("chat_id"), noi_dung)
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": tt, "loi": loi, "luc_gui": now_datetime()})
		frappe.db.commit()


def xa_gio_im():
	"""Mỗi giờ: nhóm nào hết giờ im mà còn tin hoãn thì gửi MỘT tin tổng hợp."""
	if not _bat():
		return
	gio = now_datetime().strftime("%H:%M")
	for n in _cac_nhom():
		if not cint(n.get("bat")) or trong_gio_im(gio, n.get("im_tu"), n.get("im_den")):
			continue
		ds = frappe.get_all("Vagabond Tin Kenh", filters={"nhom": n.get("ten_nhom"), "trang_thai": "Hoãn giờ im"},
			fields=["name", "noi_dung"], order_by="creation asc", limit_page_length=50)
		if not ds:
			continue
		dong = [str(r.noi_dung or "").split("\n")[0] for r in ds]
		tin = soan_tin("ban_tin", "%s tin trong giờ im" % len(ds), dong)
		tt, loi = _gui_zalo(n.get("chat_id"), tin)
		for r in ds:
			frappe.db.set_value("Vagabond Tin Kenh", r.name, {"trang_thai": tt if tt != "Đã gửi" else "Đã gửi gộp",
				"loi": loi, "luc_gui": now_datetime()})
		frappe.db.commit()


# ------------------------------------------------------------ CỬA NGÕ

def _chi_quan_tri():
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị được cài kênh Zalo.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def nhan():
	"""Zalo gọi khi có người nhắn hoặc @nhắc bot. Chỉ ghi lại mã chat để
	quản trị gán vào nhóm; không lưu nội dung tin nhắn."""
	bi_mat = ""
	try:
		bi_mat = frappe.get_single("Vagabond Settings").get_password("zalo_bi_mat", raise_exception=False) or ""
	except Exception:
		pass
	gui_len = (frappe.get_request_header("X-Bot-Api-Secret-Token") or "") if frappe.request else ""
	if not bi_mat or not hmac.compare_digest(str(gui_len), str(bi_mat)):
		frappe.local.response["http_status_code"] = 401
		return {"ok": False}
	try:
		goi = json.loads(frappe.request.data or b"{}")
	except Exception:
		goi = {}
	cu = []
	try:
		cu = json.loads(frappe.db.get_single_value("Vagabond Settings", "zalo_chat_moi") or "[]")
	except Exception:
		cu = []
	ds, moi = ghi_chat_moi(cu, goi, now_datetime())
	if moi:
		frappe.db.set_single_value("Vagabond Settings", "zalo_chat_moi", json.dumps(ds, ensure_ascii=False))
		frappe.db.commit()
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def dang_ky_webhook():
	"""Quản trị bấm một lần: kiểm token, sinh khoá bí mật, đăng ký đường nhận."""
	_chi_quan_tri()
	tt, loi, toi = _goi("getMe", {})
	if tt != "Đã gửi":
		frappe.throw("Token Zalo Bot chưa đúng. %s" % loi)
	s = frappe.get_single("Vagabond Settings")
	bi_mat = s.get_password("zalo_bi_mat", raise_exception=False) or ""
	if len(bi_mat) < 16:
		bi_mat = secrets.token_urlsafe(32)
		s.zalo_bi_mat = bi_mat
		s.flags.ignore_permissions = True
		s.save(ignore_permissions=True)
	duong = get_url("/api/method/vagabond.kenh_zalo.nhan")
	tt, loi, _ = _goi("setWebhook", {"url": duong, "secret_token": bi_mat})
	if tt != "Đã gửi":
		frappe.throw("Chưa đăng ký được đường nhận. %s" % loi)
	ten_bot = (toi or {}).get("account_name") or (toi or {}).get("display_name") or ""
	return {"ok": 1, "bot": ten_bot, "duong": duong,
		"loi_nhan": "Đã nối bot %s. Thêm bot vào nhóm Zalo rồi @nhắc bot một lần, mã nhóm sẽ hiện trong ô Chat vừa nhắn bot." % ten_bot}


@frappe.whitelist(methods=["POST"])
def gui_thu(chat_id, loai="thong_bao"):
	"""Gửi một tin mẫu tới đúng một mã chat; không chống trùng, không ghi sổ."""
	_chi_quan_tri()
	if loai not in LOAI:
		loai = "thong_bao"
	tin = soan_tin(loai, "Tin thử từ ERP Vagabond", ["Nếu nhóm thấy tin này là kênh đã nối đúng."],
		get_url("/bep"))
	tt, loi = _gui_zalo(chat_id, tin)
	if tt != "Đã gửi":
		frappe.throw("Gửi thử chưa được (%s). %s" % (tt, loi))
	return {"ok": 1, "loi_nhan": "Đã gửi tin thử."}


@frappe.whitelist()
def xem_truoc(loai="viec"):
	"""Xem trước nội dung một tin mẫu, KHÔNG gửi (Codex #410: tách xem trước với gửi thử)."""
	_chi_quan_tri()
	return {"tin": soan_tin(loai if loai in LOAI else "viec", "Khoản trả trước ERP chờ duyệt: PKT-2026-00000",
		["HĐ 8 của Công ty mẫu, 37.584.000 đ", "Gửi bởi Thu mua lúc 09:30"],
		get_url("/cong-no-phai-tra"), nguoi="Kế toán", han="Trong ngày")}
