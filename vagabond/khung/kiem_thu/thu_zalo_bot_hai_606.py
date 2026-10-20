"""v606 (anh Việt 19/10/2026): thêm bot vào nhóm Zalo thứ ba thì Zalo báo "Bot đã
vượt quá số lượng nhóm có thể tham gia". Anh chọn thêm bot thứ hai: mỗi nhóm gửi
bằng bot đang ở trong nhóm đó.

Các ca chạy hàm THẬT (nhan, _gui_zalo, chao_nhom, dang_ky_webhook, validate của
Cài đặt), chỉ thay tầng Frappe và thư viện mạng bằng bản giả.
"""
import json
import os
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kenh_zalo as kz

GOC = os.path.dirname(kz.__file__)
CAP = lambda cid: json.dumps({"message": {"chat": {"id": cid, "chat_type": "GROUP"}, "from": {"display_name": "A"}}}).encode()


@ca("v606 bot: số bot hợp lệ, đuôi ô Cài đặt, bot lạ về bot chính")
def _so():
	la("số", [kz.so_bot(x) for x in (1, "2", " 2 ", "", None, "3", "x", 0)], [1, 2, 2, 1, 1, 1, 1, 1])
	la("đuôi", [kz.hau_bot(x) for x in (1, 2, "2", 9)], ["", "_2", "_2", ""])


@ca("v606 bot: MỘT nguồn chọn bot cho chat: ô bot của dòng nhóm, rồi bot đã nhận cập nhật, rồi bot chính")
def _chon():
	nhom = [{"chat_id": "g2", "bot": "2"}, {"chat_id": "g1", "bot": "1"}, {"chat_id": "g0", "bot": ""}]
	moi = [{"chat_id": "g1", "bot": 2}, {"chat_id": "g0", "bot": 2}, {"chat_id": "m2", "bot": 2}, {"chat_id": "cu"}]
	la("dòng ghi bot 2", kz.bot_cua_chat("g2", nhom, moi), 2)
	la("dòng ghi bot 1 thắng danh sách chat", kz.bot_cua_chat("g1", nhom, moi), 1)
	la("dòng trống thì theo bot đã nhận", kz.bot_cua_chat("g0", nhom, moi), 2)
	la("chưa có dòng, theo bot đã nhận", kz.bot_cua_chat(" m2 ", nhom, moi), 2)
	la("chat cũ không ghi bot", kz.bot_cua_chat("cu", nhom, moi), 1)
	la("không biết", kz.bot_cua_chat("la", nhom, moi), 1)


@ca("v606 bot: Cài đặt tự điền ô bot theo bot đã nhận cập nhật; chat đã rơi khỏi danh sách thì giữ nguyên")
def _dien():
	ds = [{"chat_id": "g2", "bot": "1"}, {"chat_id": "g1", "bot": "1"}, {"chat_id": "xa", "bot": "2"}, {"chat_id": "moi", "bot": None}]
	moi = [{"chat_id": "g2", "bot": 2}, {"chat_id": "g2", "bot": 1}, {"chat_id": "g1"}]
	la("đổi đúng dòng", kz.dien_bot(ds, moi), [(0, 2), (3, 1)])
	la("đã đúng thì không đổi", kz.dien_bot([{"chat_id": "g2", "bot": "2"}], moi), [])


@ca("v606 bot: khoá bí mật nào khớp là bot đó; không khớp, rỗng, quá ngắn thì không bot nào")
def _bi_mat():
	k = {1: "a" * 20, 2: "b" * 20}
	la("bot chính", kz.bot_theo_bi_mat("a" * 20, k), 1)
	la("bot thứ hai", kz.bot_theo_bi_mat("b" * 20, k), 2)
	la("sai", kz.bot_theo_bi_mat("c" * 20, k), None)
	la("rỗng không khớp khoá rỗng", kz.bot_theo_bi_mat("", {1: "", 2: ""}), None)
	la("khoá quá ngắn bỏ qua", kz.bot_theo_bi_mat("ngan", {1: "ngan"}), None)


def _nhan(header, bi_mat, cu="[]"):
	f = kz.frappe
	ghi, resp = {}, {}
	s = types.SimpleNamespace(get_password=lambda k, **kw: bi_mat.get(k, ""))
	with patch.object(f, "get_single", lambda *a: s, create=True), \
			patch.object(f, "request", types.SimpleNamespace(data=CAP("zgr-ba")), create=True), \
			patch.object(f, "get_request_header", lambda k: header, create=True), \
			patch.object(f, "local", types.SimpleNamespace(response=resp), create=True), \
			patch.object(f.db, "sql", lambda q, *a, **k: [(cu,)] if "select value" in q else [], create=True), \
			patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), \
			patch.object(f, "enqueue", lambda *a, **k: None, create=True), \
			patch.object(kz, "now_datetime", lambda: "2026-10-20 09:00"):
		return kz.nhan(), resp, ghi


@ca("v606 tái hiện: đường nhận chỉ biết một khoá, nên nhóm @nhắc bot thứ hai bị 401 và không bao giờ hiện; giờ nhận và ghi bot 2")
def _nhan_bot2():
	k = {"zalo_bi_mat": "a" * 20, "zalo_bi_mat_2": "b" * 20}
	kq, resp, ghi = _nhan("b" * 20, k)
	la("khoá bot thứ hai được nhận", kq, {"ok": True})
	la("ghi nhóm kèm bot 2", [(x["chat_id"], x.get("bot")) for x in json.loads(ghi["zalo_chat_moi"])], [("zgr-ba", 2)])
	kq, resp, ghi = _nhan("a" * 20, k)
	la("khoá bot chính ghi bot 1", json.loads(ghi["zalo_chat_moi"])[0].get("bot"), 1)
	kq, resp, ghi = _nhan("c" * 20, k)
	la("khoá lạ vẫn 401", (kq, resp.get("http_status_code"), ghi), ({"ok": False}, 401, {}))
	kq, resp, ghi = _nhan("a" * 20, {"zalo_bi_mat": "a" * 20})
	la("chưa có bot thứ hai, bot chính chạy như cũ", kq, {"ok": True})


def _mang(goi_url):
	gia = types.ModuleType("requests")

	def post(url, json=None, timeout=None):
		goi_url.append((url, json))
		return types.SimpleNamespace(status_code=200, json=lambda: {"ok": True, "result": {"message_id": "m"}})
	gia.post = post
	return gia


@ca("v606: tin vào nhóm của bot thứ hai đi bằng token bot thứ hai, nhóm khác vẫn bằng bot chính (gửi ngay, trả lời mã nhóm)")
def _gui():
	url = []
	nhom = [{"chat_id": "g2", "bot": "2"}, {"chat_id": "g1", "bot": "1"}]
	moi = [{"chat_id": "m2", "bot": 2}]
	tk = {1: "111:CHINH", 2: "222:HAI"}
	with patch.object(kz, "_token", lambda bot=1: tk[kz.so_bot(bot)]), patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz, "_doc_chat_moi", lambda: moi), patch.dict("sys.modules", {"requests": _mang(url)}):
		la("nhóm bot 2", kz._gui_zalo("g2", "x")[0], "Đã gửi")
		kz._gui_zalo("g1", "x")
		kz.chao_nhom("m2")
	la("đúng token từng nhóm", [u.split("/")[3] for u, _ in url], ["bot222:HAI", "bot111:CHINH", "bot222:HAI"])
	la("đúng mã chat", [b["chat_id"] for _, b in url], ["g2", "g1", "m2"])


@ca("v606: chỉ một cửa gọi sendMessage (_gui_zalo), mọi đường gửi đi qua đó nên không chỗ nào tự chọn bot")
def _mot_cua():
	src = open(os.path.join(GOC, "kenh_zalo.py"), encoding="utf-8").read()
	la("một chỗ gọi sendMessage", src.count('_goi("sendMessage"'), 1)
	for ham in ("def _gui_mot", "def xa_gio_im", "def chao_nhom", "def gui_thu"):
		than = src.split(ham, 1)[1].split("\ndef ", 1)[0]
		dung(ham + " gửi qua _gui_zalo", "_gui_zalo(" in than and "_goi(" not in than)


@ca("v606: Nối bot thứ hai dùng token, khoá bí mật, ô kết quả riêng của bot thứ hai; bot chính giữ nguyên")
def _noi():
	f = kz.frappe
	goi, ghi = [], {}

	class S:
		flags = types.SimpleNamespace()
		zalo_bi_mat_2 = ""

		def get_password(self, k, **kw):
			return {"zalo_bi_mat": "a" * 40}.get(k, "")

		def set(self, k, v):
			setattr(self, k, v)

		def save(self, **k):
			ghi["luu"] = 1

	s = S()

	def gia(m, body, bot=1):
		goi.append((m, bot, body.get("secret_token")))
		if m == "getMe":
			return "Đã gửi", "", {"account_name": "VGB2"}
		return "Đã gửi", "", {"url": "u", "verification": {"ok": True, "hint": "ok"}}
	with patch.object(kz, "_chi_quan_tri", lambda: None), patch.object(kz, "_goi", gia), \
			patch.object(kz, "get_url", lambda p: "https://erp" + p), \
			patch.object(f, "get_single", lambda *a: s, create=True), \
			patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), \
			patch.object(kz, "now_datetime", lambda: "2026-10-20 09:00"):
		kq = kz.dang_ky_webhook(bot=2)
	la("mọi lời gọi bằng bot 2", [(m, b) for m, b, _ in goi], [("getMe", 2), ("setWebhook", 2)])
	dung("sinh khoá riêng cho bot 2, khác khoá bot chính", len(s.zalo_bi_mat_2) >= 16 and s.zalo_bi_mat_2 != "a" * 40)
	la("đăng ký bằng khoá bot 2", goi[1][2], s.zalo_bi_mat_2)
	la("ghi vào ô kết quả của bot 2", [k for k in ghi if k.startswith("zalo_noi")], ["zalo_noi_trang_thai_2"])
	dung("lời báo nói thêm bot vào nhóm mới", kq["ok"] == 1 and "bot thứ hai" in kq["loi_nhan"] and "nhóm Zalo mới" in kq["loi_nhan"])


@ca("v606: lưu Cài đặt tự điền ô bot của nhóm theo bot đã được @nhắc trong nhóm")
def _luu():
	from vagabond.vagabond.doctype.vagabond_settings import vagabond_settings as vs
	from vagabond import tai_khoan_btp

	class _D(dict):
		def as_dict(self):
			return dict(self)
	dong = [_D(ten_nhom="Bếp", chat_id="g2", bot="1", loai_tin="", chu_de="", tin_nhan="", im_tu="", im_den="", bat=1),
		_D(ten_nhom="Kế toán", chat_id="g1", bot="1", loai_tin="", chu_de="", tin_nhan="", im_tu="", im_den="", bat=1)]
	moi = json.dumps([{"chat_id": "g2", "loai": "GROUP", "bot": 2}, {"chat_id": "g1", "loai": "GROUP", "bot": 1}])
	cai = types.SimpleNamespace(phu_thu=0, kitchen_lat=10.7, kitchen_lng=106.6, zalo_chat_moi=moi,
		get=lambda k: dong if k == "zalo_nhom" else None)
	with patch.object(tai_khoan_btp, "kiem_o_cau_hinh", lambda doc: None):
		vs.VagabondSettings.validate(cai)
	la("nhóm Bếp sang bot 2, Kế toán giữ bot 1", [getattr(d, "bot", d.get("bot")) for d in dong], ["2", "1"])


@ca("v606: ô Cài đặt và cột bảng có thật, có lời dẫn tiếng Việt; Desk có nút Nối bot thứ hai gọi đúng bot")
def _o():
	d = json.load(open(os.path.join(GOC, "vagabond/doctype/vagabond_settings/vagabond_settings.json"), encoding="utf-8"))
	f = {x["fieldname"]: x for x in d["fields"]}
	la("ba ô bot thứ hai", [f[k]["fieldtype"] for k in ("zalo_bot_token_2", "zalo_bi_mat_2", "zalo_noi_trang_thai_2")],
		["Password", "Password", "Small Text"])
	dung("khoá và kết quả chỉ đọc", f["zalo_bi_mat_2"].get("read_only") == 1 and f["zalo_noi_trang_thai_2"].get("read_only") == 1)
	dung("lời dẫn nói khi nào cần", "vượt quá số lượng nhóm" in f["zalo_bot_token_2"]["description"])
	fo = d["field_order"]
	la("token bot 2 ngay sau token chính", fo[fo.index("zalo_bot_token") + 1], "zalo_bot_token_2")
	dung("modified đã đẩy", d["modified"] >= "2026-10-20")
	c = json.load(open(os.path.join(GOC, "vagabond/doctype/vagabond_kenh_zalo/vagabond_kenh_zalo.json"), encoding="utf-8"))
	b = [x for x in c["fields"] if x["fieldname"] == "bot"][0]
	la("cột bot", (b["fieldtype"], b["options"], b["default"], b.get("read_only")), ("Select", "1\n2", "1", 1))
	dung("modified bảng đã đẩy", c["modified"] >= "2026-10-20")
	js = open(os.path.join(GOC, "vagabond/doctype/vagabond_settings/vagabond_settings.js"), encoding="utf-8").read()
	dung("nút Nối bot thứ hai", 'data-zl="noi2">Nối bot thứ hai</button>' in js)
	dung("gọi đăng ký với bot 2", "args: { bot: v === 'noi2' ? 2 : 1 }" in js)
