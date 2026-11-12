# -*- coding: utf-8 -*-
"""v653 WhatsApp là đường phụ cho mã xác thực và ưu đãi (anh Việt chốt 12/11/2026).

Ca chốt (giả lập ZNS và Graph, chạy hàm thật):
  - Zalo gửi được thì không gọi WhatsApp; Zalo từ chối thì gửi WhatsApp đúng mẫu
    Xác thực, đúng nút Sao chép mã;
  - số Việt Nam không có Zalo vẫn rơi sang WhatsApp (chặn hồi quy "chỉ số nước
    ngoài");
  - cả hai hỏng: khách nhận câu dễ hiểu, không lộ lỗi kỹ thuật;
  - lượt gửi mã đếm chung hai kênh;
  - ưu đãi: chỉ khách đã đồng ý; lỗi riêng một khách thì rơi sang WhatsApp, lỗi
    cả lượt thì không;
  - điểm nhận sự kiện: sai chữ ký bị từ chối, Ngừng nhận ưu đãi thì gỡ đồng ý;
  - bản vá điền mặc định chỉ ô trống, thay ô đang là số điện thoại, không đụng token;
  - kiểm thử tích hợp không gửi tin thật;
  - không còn cửa nào tự gọi ZNS mã xác thực ngoài kenh_khach.gui_otp.
"""

import ast
import hashlib
import sys
import hmac
import io
import json
import os
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

fr = gia_lap()
if not hasattr(fr.utils, "get_url"):
	fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import kenh_khach as kk  # noqa: E402
from vagabond import whatsapp as wa  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = {"wa_phone_id": "1504016899452995", "wa_token": "x", "wa_template_otp": "vgb_otp_dang_nhap",
	"wa_template_uu_dai": "vgb_uu_dai", "wa_ngon_ngu": "vi", "zns_template_otp": "622530"}


def _key(c, k):
	return {"wa_token": "EAA" + "x" * 150, "wa_pin": "123456", "wa_app_secret": "bimat", "wa_verify_token": "vgb-xac-minh"}.get(k) \
		if c is not None else None


class Graph(object):
	"""Graph API giả: ghi lại mọi lần gọi, trả theo kịch bản."""

	def __init__(self, tra=None):
		self.goi = []
		self.tra = tra or (200, {"messages": [{"id": "wamid.1"}]})

	def __call__(self, pt, duong, tok, than=None, params=None):
		self.goi.append((pt, duong, than))
		return self.tra


def _vao(graph):
	return [um.patch.object(wa, "_goi", graph), um.patch.object(wa, "key", _key), um.patch.object(kk, "_wa", lambda: wa),
		um.patch("vagabond.lib.key", _key)]


def _chay(graph, ham):
	vs = _vao(graph)
	for v in vs:
		v.start()
	try:
		return ham()
	finally:
		for v in reversed(vs):
			v.stop()


# ------------------------------------------------------------------ THUẦN

@ca("v653 THUẦN: nút Sao chép mã, nút Ngừng nhận ưu đãi, chữ ký Meta, số xin ngừng, token sai dạng, ô mã là số điện thoại")
def _thuan():
	la("mẫu Xác thực: thân một tham số là mã, nút 0 kiểu url mang lại mã", wa.comp_otp("482913"), [
		{"type": "body", "parameters": [{"type": "text", "text": "482913"}]},
		{"type": "button", "sub_type": "url", "index": "0", "parameters": [{"type": "text", "text": "482913"}]}])
	u = wa.comp_uu_dai("Lan", "Giảm 20%, mã AB12", "31/12/2026")
	la("ưu đãi: thân ba tham số", [p["text"] for p in u[0]["parameters"]], ["Lan", "Giảm 20%, mã AB12", "31/12/2026"])
	la("ưu đãi: nút 1 trả lời nhanh mang payload cố định", u[1], {"type": "button", "sub_type": "quick_reply", "index": "1",
		"parameters": [{"type": "payload", "payload": "NGUNG_UU_DAI"}]})
	than = b'{"entry":[]}'
	ky = "sha256=" + hmac.new(b"bimat", than, hashlib.sha256).hexdigest()
	dung("chữ ký đúng", wa.chu_ky_dung(than, ky, "bimat"))
	dung("sai bí mật", not wa.chu_ky_dung(than, ky, "khac"))
	dung("thiếu chữ ký", not wa.chu_ky_dung(than, "", "bimat"))
	dung("chưa khai App Secret thì không nhận", not wa.chu_ky_dung(than, ky, ""))
	goi = {"entry": [{"changes": [{"value": {"messages": [
		{"from": "84903000111", "type": "button", "button": {"payload": "NGUNG_UU_DAI", "text": "Ngừng nhận ưu đãi"}},
		{"from": "84903000222", "type": "text", "text": {"body": " DỪNG "}},
		{"from": "84903000333", "type": "text", "text": {"body": "cho em hỏi giá"}}]}}]}]}
	la("số xin ngừng (nút và chữ DỪNG), bỏ tin thường", wa.so_xin_ngung(goi), ["84903000111", "84903000222"])
	dung("token kiểu mật khẩu", wa.token_sai_dang("Vagabond@2026"))
	la("token đúng dạng", wa.token_sai_dang("EAA" + "b" * 190), "")
	dung("ô mã là số điện thoại", wa.la_so_dien_thoai("+84703418349") and wa.la_so_dien_thoai("0703418349") and wa.la_so_dien_thoai("84703418349"))
	dung("ô mã đúng", not wa.la_so_dien_thoai("1504016899452995") and not wa.la_so_dien_thoai(" 1504 0168 9945 2995 "))
	la("dán có dấu cách vẫn nhận", wa.cau_hinh({"wa_phone_id": " 1504 0168 9945 2995 "})["phone_id"], "1504016899452995")
	la("che số", kk.che_so("84703418349"), "0703 418 349")
	la("nội dung ưu đãi", kk.noi_dung_uu_dai("Giảm 20% bánh ổ", "AB12", "đơn từ 300.000 đ"), "Giảm 20% bánh ổ (đơn từ 300.000 đ), mã AB12")
	la("trạng thái số", [wa.chu_trang_thai({"status": s})["nhan"] for s in ("CONNECTED", "PENDING", "FLAGGED")],
		["Đã kích hoạt", "Chưa kích hoạt", "Có sự cố"])


@ca("v653 bản vá điền mặc định: chỉ ô trống; ô mã đang là số điện thoại thì thay; ô đúng giữ nguyên; không đụng token")
def _ban_va():
	la("site 12/11: ô mã trống", wa.can_dien({"wa_phone_id": "", "wa_ngon_ngu": "vi"}), {
		"wa_phone_id": "1504016899452995", "wa_waba_id": "2041260756651836", "wa_template_otp": "vgb_otp_dang_nhap",
		"wa_template_uu_dai": "vgb_uu_dai"})
	la("ô mã là số điện thoại thì thay", wa.can_dien({"wa_phone_id": "+84703418349", "wa_waba_id": "1", "wa_template_otp": "a",
		"wa_template_uu_dai": "b", "wa_ngon_ngu": "en"}), {"wa_phone_id": "1504016899452995"})
	la("đã đúng hết thì không đổi gì", wa.can_dien({"wa_phone_id": "999999999999999", "wa_waba_id": "1", "wa_template_otp": "a",
		"wa_template_uu_dai": "b", "wa_ngon_ngu": "vi"}), {})
	dung("không bao giờ điền ô bí mật", not ({"wa_token", "wa_pin", "wa_app_secret", "wa_verify_token"} & set(wa.MAC_DINH)))


# ------------------------------------------------------------------ mã xác thực

def _gui_ma(zns, so="0903 000 111", da_gui=0):
	"""Chạy THẬT dang_nhap.gui_ma: ZNS giả trả `zns`, Graph giả ghi lại."""
	from vagabond import dang_nhap as dn

	g = Graph()
	loi = []
	vs = [um.patch.object(dn, "_gui_zns", lambda c, s, ma: zns), um.patch.object(dn, "cfg", lambda: dict(CFG)),
		um.patch.object(fr.db, "count", lambda *a, **k: da_gui, create=True),
		um.patch.object(fr, "new_doc", lambda dt_: types.SimpleNamespace(insert=lambda **k: None), create=True),
		um.patch.object(dn, "_bam", lambda x: "bam"),
		um.patch.object(fr, "log_error", lambda *a, **k: loi.append(k.get("message") or (a[0] if a else "")))]
	for v in vs:
		v.start()
	try:
		r = _chay(g, lambda: dn.gui_ma(so))
	finally:
		for v in reversed(vs):
			v.stop()
	return r, g, loi


@ca("v653 mã xác thực: Zalo gửi được thì KHÔNG gọi WhatsApp; Zalo từ chối thì gửi WhatsApp đúng mẫu, đúng nút Sao chép mã")
def _otp():
	r, g, _ = _gui_ma((True, ""))
	la("Zalo được", (r["ok"], r["kenh"], len(g.goi)), (1, "zalo", 0))
	r, g, _ = _gui_ma((False, "Số chưa dùng Zalo"))
	la("rơi sang WhatsApp", (r["ok"], r["kenh"], r["so"]), (1, "whatsapp", "0903 000 111"))
	pt, duong, than = g.goi[0]
	la("đúng đường gửi", (pt, duong), ("POST", "1504016899452995/messages"))
	la("đúng số, mẫu, ngôn ngữ", (than["to"], than["template"]["name"], than["template"]["language"]["code"]), ("84903000111", "vgb_otp_dang_nhap", "vi"))
	ma = than["template"]["components"][0]["parameters"][0]["text"]
	dung("mã 6 số", len(ma) == 6 and ma.isdigit())
	la("nút Sao chép mã mang đúng mã", than["template"]["components"][1], {"type": "button", "sub_type": "url", "index": "0",
		"parameters": [{"type": "text", "text": ma}]})


@ca("v653 số Việt Nam KHÔNG có Zalo vẫn nhận mã qua WhatsApp (không phải chỉ số nước ngoài)")
def _so_vn():
	r, g, _ = _gui_ma((False, "-118 user not exist"), so="0987654321")
	la("số Việt Nam rơi sang WhatsApp", (r["kenh"], g.goi[0][2]["to"]), ("whatsapp", "84987654321"))


@ca("v653 cả hai hỏng: khách nhận câu dễ hiểu, không lộ lỗi kỹ thuật; kỹ thuật đọc Error Log")
def _ca_hai_hong():
	from vagabond import dang_nhap as dn

	g = Graph(tra=(400, {"error": {"message": "(#131030) Recipient phone number not in allowed list"}}))
	loi = []
	vs = [um.patch.object(dn, "_gui_zns", lambda c, s, ma: (False, "-124 token hết hạn")), um.patch.object(dn, "cfg", lambda: dict(CFG)),
		um.patch.object(fr.db, "count", lambda *a, **k: 0, create=True),
		um.patch.object(fr, "new_doc", lambda dt_: types.SimpleNamespace(insert=lambda **k: None), create=True),
		um.patch.object(dn, "_bam", lambda x: "bam"),
		um.patch.object(fr, "log_error", lambda *a, **k: loi.append(str(k.get("message") or ""))),
		um.patch.object(wa.json, "dumps", json.dumps)]
	for v in vs:
		v.start()
	try:
		r = _chay(g, lambda: dn.gui_ma("0903000111"))
	finally:
		for v in reversed(vs):
			v.stop()
	la("trả lý do chung, không kèm lỗi kỹ thuật", r, {"ok": 0, "ly_do": "khong_gui_duoc"})
	dung("Error Log ghi lỗi cả hai kênh", any("token hết hạn" in x and "131030" in x for x in loi))
	js = io.open(os.path.join(GOC, "public", "web_order", "thanh-vien.js"), encoding="utf-8").read()
	dung("trang thành viên có câu cho khong_gui_duoc", "khong_gui_duoc" in js)


@ca("v653 lượt gửi mã đếm chung hai kênh: đủ 5 lần trong 30 phút thì không gửi kênh nào")
def _luot():
	r, g, _ = _gui_ma((False, "x"), da_gui=5)
	la("chặn", (r["ly_do"], len(g.goi)), ("gui_qua_nhieu", 0))


@ca("v653 kiểm thử tích hợp không gửi tin WhatsApp thật")
def _kiem_that():
	goi = []
	fr.flags["vagabond_kiem_that"] = True
	try:
		with um.patch.object(wa, "_goi", lambda *a, **k: goi.append(a)):
			ok, loi = wa.gui_mau(CFG, "84903000111", "vgb_otp_dang_nhap", None, components=wa.comp_otp("1"))
	finally:
		fr.flags.pop("vagabond_kiem_that", None)
	la("không gọi Graph", (ok, goi), (False, []))


@ca("v653 không còn cửa nào tự gọi ZNS mã xác thực ngoài kenh_khach.gui_otp")
def _mot_cua():
	def cua(tep, ten_goi):
		cay = ast.parse(io.open(os.path.join(GOC, tep), encoding="utf-8").read())
		cha = {}
		for n in ast.walk(cay):
			for c in ast.iter_child_nodes(n):
				cha[c] = n
		ra = []
		for n in ast.walk(cay):
			if isinstance(n, ast.Call) and ast.unparse(n.func) == ten_goi:
				p = cha.get(n)
				trong = False
				while p is not None:
					if isinstance(p, ast.Lambda) and isinstance(cha.get(p), ast.Call) and ast.unparse(cha[p].func).endswith("gui_otp"):
						trong = True
						break
					p = cha.get(p)
				ra.append(trong)
		return ra
	la("dang_nhap: mọi lần gọi _gui_zns nằm trong gui_otp", cua("dang_nhap.py", "_gui_zns"), [True])
	la("diem_otp: lần gọi zalo.gui_tin nằm trong gui_otp", cua("diem_otp.py", "zalo.gui_tin"), [True])
	for tep in ("thanh_vien.py", "banh_si.py", "don_dau_web.py", "uu_dai_ban.py"):
		p = os.path.join(GOC, tep)
		if os.path.exists(p):
			s = io.open(p, encoding="utf-8").read()
			dung("%s không tự gọi Zalo gửi mã" % tep, "zalo.gui_tin(" not in s and "_gui_zns(" not in s)


# ------------------------------------------------------------------ ưu đãi

@ca("v653 ưu đãi: khách chưa đồng ý thì KHÔNG gửi WhatsApp dù Zalo hỏng; đã đồng ý thì gửi đúng mẫu")
def _uu_dai():
	g = Graph()
	ok, loi = _chay(g, lambda: kk.gui_uu_dai(dict(CFG), "84903000111", "Lan", "Giảm 20%", "31/12/2026", False))
	la("chưa đồng ý", (ok, len(g.goi)), (False, 0))
	ok, loi = _chay(g, lambda: kk.gui_uu_dai(dict(CFG), "84903000111", "Lan", "Giảm 20%", "31/12/2026", True))
	la("đã đồng ý", (ok, g.goi[0][2]["template"]["name"]), (True, "vgb_uu_dai"))
	g2 = Graph(tra=(400, {"error": {"message": "Template is not approved"}}))
	ok, loi = _chay(g2, lambda: kk.gui_uu_dai(dict(CFG), "84903000111", "Lan", "Giảm 20%", "31/12/2026", True))
	la("mẫu chưa duyệt: coi như WhatsApp hỏng, không vỡ luồng", (ok, "not approved" in loi), (False, True))


@ca("v653 kịch bản ưu đãi Zalo: lỗi riêng khách thì gửi WhatsApp, giữ mã; lỗi cả lượt thì không gửi WhatsApp")
def _kich_ban():
	from vagabond import zalo_kich_ban as zk
	from vagabond.khung.kiem_thu import thu_voucher_tv_623 as tv623

	wa_goi = []

	def chay(loi_zalo, ok_wa=True):
		with um.patch.object(zk, "_gui_wa_uu_dai", lambda kh, gt: (wa_goi.append((kh["sdt84"], gt["ma_voucher"])) or (ok_wa, "" if ok_wa else "WhatsApp hỏng"))):
			return tv623._gui(tv623._ct("KMML01"), [], loi_zalo=loi_zalo)
	vet, kq = chay(-201)
	la("Zalo từ chối khách này: gửi WhatsApp, ghi Đã gửi, không huỷ mã", (kq, vet.xong[-1][0], vet.huy, wa_goi[-1]),
		(0, zk.TT_GUI, [], ("84909123412", "ZMOI01")))
	dung("ghi rõ đã gửi qua WhatsApp", "WhatsApp" in vet.xong[-1][1])
	n = len(wa_goi)
	vet, kq = chay(-124)
	la("lỗi cả lượt: không gửi WhatsApp", len(wa_goi), n)
	vet, kq = chay(-201, ok_wa=False)
	dung("cả hai hỏng: lý do ghi đủ hai kênh", "WhatsApp hỏng" in (vet.xong[-1][1] or ""))


# ------------------------------------------------------------------ điểm nhận sự kiện

class Req(object):
	def __init__(self, method, than=b""):
		self.method = method
		self._t = than

	def get_data(self, as_text=False):
		return self._t.decode() if as_text else self._t


@ca("v653 điểm nhận sự kiện: GET đúng verify token trả challenge; POST sai chữ ký 401; Ngừng nhận ưu đãi thì gỡ đồng ý, nơi ghi WhatsApp")
def _webhook():
	from vagabond import crm

	try:
		import werkzeug  # noqa: F401
	except ImportError:
		return  # CI tay không: phần thuần đã chốt ở trên
	ghi = []
	goi = json.dumps({"entry": [{"changes": [{"value": {"messages": [
		{"from": "84903000111", "type": "button", "button": {"payload": "NGUNG_UU_DAI"}}]}}]}]}).encode()
	ky = "sha256=" + hmac.new(b"bimat", goi, hashlib.sha256).hexdigest()

	def chay(req, fd=None, chu_ky=""):
		vs = [um.patch.object(wa, "key", _key), um.patch.object(wa, "_cfg", lambda: dict(CFG)),
			um.patch.object(fr, "request", req, create=True), um.patch.object(fr, "form_dict", fd or {}, create=True),
			um.patch.object(fr, "get_request_header", lambda h, *a: chu_ky, create=True),
			um.patch.object(fr, "get_all", lambda *a, **k: ["KL0412"]),
			um.patch.object(crm, "ghi_dong_y_noi", lambda kh, dat, noi, **k: ghi.append((kh, dat, noi, k.get("nguoi"))) or {"doi": 1})]
		for v in vs:
			v.start()
		try:
			return wa.webhook()
		finally:
			for v in reversed(vs):
				v.stop()
	r = chay(Req("GET"), {"hub.mode": "subscribe", "hub.verify_token": "vgb-xac-minh", "hub.challenge": "8812"})
	la("GET đúng verify token", (r.status_code, r.get_data(as_text=True)), (200, "8812"))
	r = chay(Req("GET"), {"hub.mode": "subscribe", "hub.verify_token": "sai", "hub.challenge": "8812"})
	la("GET sai verify token", r.status_code, 403)
	r = chay(Req("POST", goi), chu_ky="sha256=" + "0" * 64)
	la("POST sai chữ ký: 401, không gỡ gì", (r.status_code, ghi), (401, []))
	r = chay(Req("POST", goi), chu_ky=ky)
	la("POST đúng: gỡ đồng ý ưu đãi, nơi ghi WhatsApp, máy ghi", (r.status_code, ghi), (200, [("KL0412", {"Zalo": "Từ chối"}, "WhatsApp", "Guest")]))
	dung("WhatsApp là nơi ghi hợp lệ, chỉ máy ghi", "WhatsApp" in crm.NOI_GHI and "WhatsApp" in crm.NOI_GHI_MAY)


@ca("v653 kích hoạt số và trạng thái: chỉ quản trị hệ thống; không trả PIN hay token ra trình duyệt; PIN sai dạng báo việc cần làm")
def _kich_hoat():
	g = Graph(tra=(200, {"status": "PENDING", "display_phone_number": "+84 70 341 8349", "verified_name": "The Vagabond Pâtisserie"}))
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]):
		nem("vai khác bị chặn", lambda: _chay(g, wa.kich_hoat))
	with um.patch.object(fr, "get_roles", lambda *a: ["System Manager"]), um.patch.object(wa, "_cfg", lambda: dict(CFG)):
		r = _chay(g, wa.trang_thai)
		la("chưa kích hoạt", (r["nhan"], r["khai"]["pin"], r["khai"]["token"]), ("Chưa kích hoạt", 1, 1))
		dung("không lộ bí mật", "123456" not in json.dumps(r) and "EAA" not in json.dumps(r) and "bimat" not in json.dumps(r))
		g.goi.clear()
		_chay(g, wa.kich_hoat)
		la("gọi register với PIN đọc trong máy chủ", g.goi[0][:3], ("POST", "1504016899452995/register", {"messaging_product": "whatsapp", "pin": "123456"}))
		with um.patch.object(wa, "key", lambda c, k: "12" if k == "wa_pin" else _key(c, k)), um.patch.object(wa, "_goi", g):
			nem("PIN thiếu số", wa.kich_hoat)
