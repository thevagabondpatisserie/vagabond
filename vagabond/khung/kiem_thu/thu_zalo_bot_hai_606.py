"""v606 (anh Việt 19/10/2026): thêm bot vào nhóm Zalo thứ ba thì Zalo báo "Bot đã
vượt quá số lượng nhóm có thể tham gia". Anh chọn thêm bot, rồi chốt 20/10: thêm
được NHIỀU bot, không chỉ hai. Mỗi nhóm gửi bằng bot đang ở trong nhóm đó.

Tên tệp giữ từ bản hai bot (đẩy qua trang GitHub không xoá được tệp). Các ca chạy
hàm THẬT (nhan, _gui_zalo, chao_nhom, luu_bot, dang_ky_webhook, validate của Cài
đặt), chỉ thay tầng Frappe và thư viện mạng bằng bản giả. Ca nào cũng có ít nhất
ba bot để không lọt cách làm cứng cho hai bot.
"""
import json
import os
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kenh_zalo as kz

GOC = os.path.dirname(kz.__file__)
CAP = lambda cid: json.dumps({"message": {"chat": {"id": cid, "chat_type": "GROUP"}, "from": {"display_name": "A"}}}).encode()
BA_BOT = [{"ma_bot": "2", "ten_bot": "Bot Bếp"}, {"ma_bot": "5", "ten_bot": ""}]


class _D(dict):
	"""Dòng bảng giả: đọc được cả kiểu thuộc tính lẫn as_dict như dòng Frappe."""
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)


@ca("v606 nhiều bot: số bot, danh sách bot, tên ô kho mật khẩu, tên đọc được")
def _so():
	la("số bot", [kz.ma_bot(x) for x in (1, "2", " 7 ", "", None, "x", 0, -3, "12")], ["1", "2", "7", "1", "1", "1", "1", "1", "12"])
	la("danh sách bot", kz.cac_bot(BA_BOT + [{"ma_bot": ""}, {"ma_bot": "2"}, {"ma_bot": "x"}]), ["1", "2", "5"])
	la("ô kho mật khẩu", [kz.o_mat("zalo_bot_token", m) for m in ("1", "2", "15")],
		["zalo_bot_token", "zalo_bot_token_2", "zalo_bot_token_15"])
	la("ô khoá bí mật", kz.o_mat("zalo_bi_mat", "5"), "zalo_bi_mat_5")
	la("tên bot", [kz.ten_cua_bot(m, BA_BOT) for m in ("1", "2", "5", "9")],
		["bot chính", "Bot Bếp", "bot số 5", "bot số 9"])


@ca("v606 nhiều bot: cấp số bot mới lớn hơn mọi số đang có và mọi số từng cấp, không cấp lại số đã xoá")
def _cap_so():
	la("chưa có bot thêm", kz.ma_bot_moi(["1"], None), "2")
	la("đang có 2, 5", kz.ma_bot_moi(["1", "2", "5"], 5), "6")
	la("bot 6 đã xoá, số cuối 6", kz.ma_bot_moi(["1", "2"], 6), "7")
	ds = [{"ma_bot": "2"}, {"ma_bot": ""}, {"ma_bot": ""}]
	la("dòng thêm tay ở lưới được cấp số, số cuối tăng", kz.gan_ma_bot(ds, 4), ([(1, "5"), (2, "6")], 6))
	la("không dòng mới thì số cuối giữ", kz.gan_ma_bot([{"ma_bot": "3"}], 9), ([], 9))


@ca("v606 nhiều bot: MỘT nguồn chọn bot cho chat: ô bot của dòng nhóm, rồi bot đã nhận cập nhật, rồi bot chính; bot đã xoá về bot chính")
def _chon():
	cac = ["1", "2", "5"]
	nhom = [{"chat_id": "g5", "bot": "5"}, {"chat_id": "g1", "bot": "1"}, {"chat_id": "g0", "bot": ""}, {"chat_id": "gx", "bot": "4"}]
	moi = [{"chat_id": "g1", "bot": "2"}, {"chat_id": "g0", "bot": "5"}, {"chat_id": "m2", "bot": "2"}, {"chat_id": "cu"}, {"chat_id": "m4", "bot": "4"}]
	la("dòng ghi bot 5", kz.bot_cua_chat("g5", nhom, moi, cac), "5")
	la("dòng ghi bot 1 thắng danh sách chat", kz.bot_cua_chat("g1", nhom, moi, cac), "1")
	la("dòng trống thì theo bot đã nhận", kz.bot_cua_chat("g0", nhom, moi, cac), "5")
	la("chưa có dòng, theo bot đã nhận", kz.bot_cua_chat(" m2 ", nhom, moi, cac), "2")
	la("chat cũ không ghi bot", kz.bot_cua_chat("cu", nhom, moi, cac), "1")
	la("không biết", kz.bot_cua_chat("la", nhom, moi, cac), "1")
	la("dòng trỏ bot 4 đã xoá", kz.bot_cua_chat("gx", nhom, moi, cac), "1")
	la("chat của bot 4 đã xoá", kz.bot_cua_chat("m4", nhom, moi, cac), "1")


@ca("v606 nhiều bot: Cài đặt tự điền ô bot theo bot đã nhận cập nhật; chat đã rơi khỏi danh sách thì giữ nguyên")
def _dien():
	ds = [{"chat_id": "g2", "bot": "1"}, {"chat_id": "g1", "bot": "1"}, {"chat_id": "xa", "bot": "5"}, {"chat_id": "moi", "bot": None}]
	moi = [{"chat_id": "g2", "bot": "5"}, {"chat_id": "g2", "bot": "1"}, {"chat_id": "g1"}]
	la("đổi đúng dòng", kz.dien_bot(ds, moi), [(0, "5"), (3, "1")])
	la("đã đúng thì không đổi", kz.dien_bot([{"chat_id": "g2", "bot": "5"}], moi), [])


@ca("v606 nhiều bot: khoá bí mật nào khớp là bot đó; không khớp, rỗng, quá ngắn thì không bot nào")
def _bi_mat():
	k = {"1": "a" * 20, "2": "b" * 20, "5": "e" * 20}
	la("bot chính", kz.bot_theo_bi_mat("a" * 20, k), "1")
	la("bot 2", kz.bot_theo_bi_mat("b" * 20, k), "2")
	la("bot 5", kz.bot_theo_bi_mat("e" * 20, k), "5")
	la("sai", kz.bot_theo_bi_mat("c" * 20, k), None)
	la("rỗng không khớp khoá rỗng", kz.bot_theo_bi_mat("", {"1": "", "2": ""}), None)
	la("khoá quá ngắn bỏ qua", kz.bot_theo_bi_mat("ngan", {"1": "ngan"}), None)


def _nhan(header, mat, bot_them, cu="[]"):
	"""Gọi nhan() thật; mat: {tên ô kho mật khẩu: giá trị}."""
	f = kz.frappe
	ghi, resp = {}, {}
	s = types.SimpleNamespace(get_password=lambda k, **kw: mat.get(k, ""), get=lambda k: [_D(x) for x in bot_them] if k == "zalo_bot_phu" else None)
	giai = types.ModuleType("frappe.utils.password")
	giai.get_decrypted_password = lambda dt, dn, k, **kw: mat.get(k, "")
	with patch.object(f, "get_single", lambda *a: s, create=True), \
			patch.dict("sys.modules", {"frappe.utils.password": giai}), \
			patch.object(f, "request", types.SimpleNamespace(data=CAP("zgr-ba")), create=True), \
			patch.object(f, "get_request_header", lambda k: header, create=True), \
			patch.object(f, "local", types.SimpleNamespace(response=resp), create=True), \
			patch.object(f.db, "sql", lambda q, *a, **k: [(cu,)] if "select value" in q else [], create=True), \
			patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), \
			patch.object(f, "enqueue", lambda *a, **k: None, create=True), \
			patch.object(kz, "now_datetime", lambda: "2026-10-20 09:00"):
		return kz.nhan(), resp, ghi


@ca("v606 tái hiện: đường nhận chỉ biết khoá bot chính, nên nhóm @nhắc bot khác bị 401 và không bao giờ hiện; giờ nhận và ghi đúng số bot")
def _nhan_nhieu():
	mat = {"zalo_bi_mat": "a" * 20, "zalo_bi_mat_2": "b" * 20, "zalo_bi_mat_5": "e" * 20}
	for khoa, so in (("b" * 20, "2"), ("e" * 20, "5"), ("a" * 20, "1")):
		kq, resp, ghi = _nhan(khoa, mat, BA_BOT)
		la("khoá bot %s được nhận" % so, kq, {"ok": True})
		la("ghi nhóm kèm bot %s" % so, [(x["chat_id"], x.get("bot")) for x in json.loads(ghi["zalo_chat_moi"])], [("zgr-ba", so)])
	kq, resp, ghi = _nhan("c" * 20, mat, BA_BOT)
	la("khoá lạ vẫn 401", (kq, resp.get("http_status_code"), ghi), ({"ok": False}, 401, {}))
	kq, resp, ghi = _nhan("e" * 20, mat, [BA_BOT[0]])
	la("bot 5 đã xoá khỏi bảng thì khoá của nó hết được nhận", (kq, resp.get("http_status_code")), ({"ok": False}, 401))
	kq, resp, ghi = _nhan("a" * 20, {"zalo_bi_mat": "a" * 20}, [])
	la("chưa có bot thêm, bot chính chạy như cũ", kq, {"ok": True})


def _mang(goi_url):
	gia = types.ModuleType("requests")

	def post(url, json=None, timeout=None):
		goi_url.append((url, json))
		return types.SimpleNamespace(status_code=200, json=lambda: {"ok": True, "result": {"message_id": "m"}})
	gia.post = post
	return gia


@ca("v606 nhiều bot: tin vào nhóm của bot nào đi bằng token bot đó (gửi ngay, trả lời mã nhóm); bot đã xoá về bot chính")
def _gui():
	url = []
	nhom = [{"chat_id": "g5", "bot": "5"}, {"chat_id": "g1", "bot": "1"}, {"chat_id": "g2", "bot": "2"}, {"chat_id": "g9", "bot": "9"}]
	moi = [{"chat_id": "m2", "bot": "2"}]
	tk = {"1": "111:CHINH", "2": "222:HAI", "5": "555:NAM"}
	with patch.object(kz, "_token", lambda bot="1": tk[kz.ma_bot(bot)]), patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz, "_bot_them", lambda: BA_BOT), \
			patch.object(kz, "_doc_chat_moi", lambda: moi), patch.dict("sys.modules", {"requests": _mang(url)}):
		la("nhóm bot 5", kz._gui_zalo("g5", "x")[0], "Đã gửi")
		kz._gui_zalo("g1", "x")
		kz._gui_zalo("g2", "x")
		kz._gui_zalo("g9", "x")
		kz.chao_nhom("m2")
	la("đúng token từng nhóm", [u.split("/")[3] for u, _ in url],
		["bot555:NAM", "bot111:CHINH", "bot222:HAI", "bot111:CHINH", "bot222:HAI"])
	la("đúng mã chat", [b["chat_id"] for _, b in url], ["g5", "g1", "g2", "g9", "m2"])


@ca("v606: chỉ một cửa gọi sendMessage (_gui_zalo), mọi đường gửi đi qua đó nên không chỗ nào tự chọn bot")
def _mot_cua():
	src = open(os.path.join(GOC, "kenh_zalo.py"), encoding="utf-8").read()
	la("một chỗ gọi sendMessage", src.count('_goi("sendMessage"'), 1)
	for ham in ("def _gui_mot", "def xa_gio_im", "def chao_nhom", "def gui_thu"):
		than = src.split(ham, 1)[1].split("\ndef ", 1)[0]
		dung(ham + " gửi qua _gui_zalo", "_gui_zalo(" in than and "_goi(" not in than)
	dung("không còn cách làm cứng hai bot", "BOT = (1, 2)" not in src and "_2\"" not in src and "TEN_BOT" not in src)


class _S:
	"""Cài đặt giả cho luu_bot và dang_ky_webhook."""
	def __init__(self, dong, cuoi=1, mat=None):
		self.flags = types.SimpleNamespace()
		self.zalo_bot_phu = [_D(x) for x in dong]
		self.zalo_bot_ma_cuoi = cuoi
		self.mat = dict(mat or {})
		self.luu = 0

	def get(self, k):
		return getattr(self, k, None)

	def get_password(self, k, **kw):
		return self.mat.get(k, "")

	def append(self, k, v):
		getattr(self, k).append(_D(v))

	def save(self, **k):
		self.luu += 1


def _he(s, goi_gia, ghi):
	f = kz.frappe
	giai = types.ModuleType("frappe.utils.password")
	giai.get_decrypted_password = lambda dt, dn, k, **kw: s.mat.get(k, "")
	giai.set_encrypted_password = lambda dt, dn, v, k: s.mat.__setitem__(k, v)
	return [patch.object(kz, "_chi_quan_tri", lambda: None), patch.object(kz, "_goi", goi_gia),
		patch.dict("sys.modules", {"frappe.utils.password": giai}),
		patch.object(kz, "get_url", lambda p: "https://erp" + p),
		patch.object(f, "get_single", lambda *a: s, create=True),
		patch.object(f, "throw", lambda m, *a: (_ for _ in ()).throw(ValueError(m)), create=True),
		patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True),
		patch.object(f.db, "set_value", lambda dt, loc, k, v: ghi.__setitem__((dt, loc["ma_bot"], k), v), create=True),
		patch.object(f.db, "commit", lambda: None, create=True),
		patch.object(kz, "now_datetime", lambda: "2026-10-20 09:00")]


def _chay(cac_patch, ham):
	from contextlib import ExitStack
	with ExitStack() as st:
		for p in cac_patch:
			st.enter_context(p)
		return ham()


@ca("v606 nhiều bot: Thêm bot kiểm token với Zalo trước, cấp số mới không trùng số đã xoá, cất token mã hoá ngoài bảng")
def _them():
	goi = []

	def gia(m, body, bot="1", token=None):
		goi.append((m, bot, token))
		if token == "SAI":
			return "Lỗi", "Unauthorized", None
		return "Đã gửi", "", {"account_name": "VGB Bep"}
	s = _S([{"ma_bot": "2", "ten_bot": "Bot Bếp", "co_token": 1}], cuoi=6,
		mat={"zalo_bot_token": "111:CHINH", "zalo_bot_token_2": "222:HAI"})
	kq = _chay(_he(s, gia, {}), lambda: kz.luu_bot(ten="", token=" 777:BAY "))
	la("cấp số 7 (bot 3..6 từng cấp rồi xoá)", kq["ma_bot"], "7")
	la("kiểm token mới, chưa lưu, bằng getMe", goi, [("getMe", "1", "777:BAY")])
	la("dòng mới lấy tên bot trên Zalo", [(r.ma_bot, r.ten_bot, r.co_token) for r in s.zalo_bot_phu], [("2", "Bot Bếp", 1), ("7", "VGB Bep", 1)])
	la("token cất ở ô kho mật khẩu có đuôi số", s.mat.get("zalo_bot_token_7"), "777:BAY")
	dung("token không nằm trong dòng bảng", all("777:BAY" not in json.dumps(r) for r in s.zalo_bot_phu))
	la("số cuối lên 7", s.zalo_bot_ma_cuoi, 7)
	for token, chu in (("SAI", "Unauthorized"), ("222:HAI", "Bot Bếp"), ("111:CHINH", "bot chính")):
		s2 = _S([{"ma_bot": "2", "ten_bot": "Bot Bếp", "co_token": 1}], mat={"zalo_bot_token": "111:CHINH", "zalo_bot_token_2": "222:HAI"})
		try:
			_chay(_he(s2, gia, {}), lambda: kz.luu_bot(token=token))
			loi = ""
		except ValueError as e:
			loi = str(e)
		dung("chặn token %s: %s" % (token, loi[:60]), chu in loi and len(s2.zalo_bot_phu) == 1 and s2.luu == 0)
	s3 = _S([{"ma_bot": "2", "ten_bot": "Bot Bếp", "co_token": 1, "trang_thai": "Đã xác minh lúc x"}], mat={"zalo_bot_token_2": "222:HAI"})
	kq = _chay(_he(s3, gia, {}), lambda: kz.luu_bot(ma="2", token="223:MOI"))
	la("đổi token bot 2: giữ số, xoá kết quả nối cũ", (kq["ma_bot"], s3.mat["zalo_bot_token_2"], s3.zalo_bot_phu[0].trang_thai, len(s3.zalo_bot_phu)),
		("2", "223:MOI", "", 1))


@ca("v606 nhiều bot: Nối bot N dùng token, khoá bí mật, ô kết quả riêng của bot N; bot chính giữ nguyên; bot không có trong bảng bị chặn")
def _noi():
	goi, ghi = [], {}

	def gia(m, body, bot="1", token=None):
		goi.append((m, bot, body.get("secret_token")))
		if m == "getMe":
			return "Đã gửi", "", {"account_name": "VGB5"}
		return "Đã gửi", "", {"url": "u", "verification": {"ok": True, "hint": "ok"}}
	s = _S(BA_BOT, cuoi=5, mat={"zalo_bi_mat": "a" * 40})
	kq = _chay(_he(s, gia, ghi), lambda: kz.dang_ky_webhook(bot="5"))
	la("mọi lời gọi bằng bot 5", [(m, b) for m, b, _ in goi], [("getMe", "5"), ("setWebhook", "5")])
	k5 = s.mat.get("zalo_bi_mat_5", "")
	dung("sinh khoá riêng cho bot 5, khác khoá bot chính", len(k5) >= 16 and k5 != "a" * 40 and s.mat["zalo_bi_mat"] == "a" * 40)
	la("đăng ký bằng khoá bot 5", goi[1][2], k5)
	la("ghi kết quả vào dòng bot 5, không đụng ô bot chính", [k for k in ghi], [("Vagabond Bot Zalo", "5", "trang_thai")])
	dung("lời báo nói thêm bot vào nhóm mới", kq["ok"] == 1 and "bot số 5" in kq["loi_nhan"] and "nhóm Zalo mới" in kq["loi_nhan"])
	try:
		_chay(_he(s, gia, ghi), lambda: kz.dang_ky_webhook(bot="9"))
		loi = ""
	except ValueError as e:
		loi = str(e)
	dung("bot 9 không có trong bảng thì chặn", "bot số 9" in loi)
	goi.clear()
	_chay(_he(s, gia, ghi), lambda: kz.dang_ky_webhook(bot="1"))
	la("bot chính vẫn ghi ô cũ", ("zalo_noi_trang_thai" in ghi, goi[1][2]), (True, "a" * 40))


@ca("v606 nhiều bot: lưu Cài đặt cấp số cho dòng bot thêm tay và điền ô bot của nhóm theo bot đã được @nhắc")
def _luu():
	from vagabond.vagabond.doctype.vagabond_settings import vagabond_settings as vs
	from vagabond import tai_khoan_btp

	dong = [_D(ten_nhom="Bếp", chat_id="g5", bot="1", loai_tin="", chu_de="", tin_nhan="", im_tu="", im_den="", bat=1),
		_D(ten_nhom="Kế toán", chat_id="g1", bot="1", loai_tin="", chu_de="", tin_nhan="", im_tu="", im_den="", bat=1),
		_D(ten_nhom="Kho", chat_id="g2", bot="1", loai_tin="", chu_de="", tin_nhan="", im_tu="", im_den="", bat=1)]
	them = [_D(ma_bot="2", ten_bot="B"), _D(ma_bot="5", ten_bot="C"), _D(ma_bot="", ten_bot="Thêm tay")]
	moi = json.dumps([{"chat_id": "g5", "loai": "GROUP", "bot": "5"}, {"chat_id": "g1", "loai": "GROUP", "bot": "1"},
		{"chat_id": "g2", "loai": "GROUP", "bot": "2"}])
	cai = _D(phu_thu=0, kitchen_lat=10.7, kitchen_lng=106.6, zalo_chat_moi=moi, zalo_bot_ma_cuoi=5, get_doc_before_save=lambda: None,
		zalo_nhom=dong, zalo_bot_phu=them)
	with patch.object(tai_khoan_btp, "kiem_o_cau_hinh", lambda doc: None):
		vs.VagabondSettings.validate(cai)
	la("nhóm theo đúng bot", [d.bot for d in dong], ["5", "1", "2"])
	la("dòng thêm tay được số 6", [r.ma_bot for r in them], ["2", "5", "6"])
	la("số cuối 6", cai.zalo_bot_ma_cuoi, 6)


@ca("v606 nhiều bot: ô Cài đặt, bảng Bot thêm và cột nhóm có thật, có lời dẫn tiếng Việt; Desk có Thêm bot, Nối lại, Đổi token theo số bot")
def _o():
	d = json.load(open(os.path.join(GOC, "vagabond/doctype/vagabond_settings/vagabond_settings.json"), encoding="utf-8"))
	f = {x["fieldname"]: x for x in d["fields"]}
	la("bảng Bot thêm", (f["zalo_bot_phu"]["fieldtype"], f["zalo_bot_phu"]["options"]), ("Table", "Vagabond Bot Zalo"))
	dung("lời dẫn nói khi nào cần", "vượt quá số lượng nhóm" in f["zalo_bot_phu"]["description"])
	la("số cuối ẩn, chỉ đọc", (f["zalo_bot_ma_cuoi"]["fieldtype"], f["zalo_bot_ma_cuoi"].get("hidden"), f["zalo_bot_ma_cuoi"].get("read_only")), ("Int", 1, 1))
	dung("không còn ô làm cứng bot thứ hai", not any(k.endswith("_2") and k.startswith("zalo") for k in f))
	fo = d["field_order"]
	la("bảng Bot thêm ngay sau token chính", fo[fo.index("zalo_bot_token") + 1], "zalo_bot_phu")
	dung("modified đã đẩy", d["modified"] >= "2026-10-20 12")
	b = json.load(open(os.path.join(GOC, "vagabond/doctype/vagabond_bot_zalo/vagabond_bot_zalo.json"), encoding="utf-8"))
	fb = {x["fieldname"]: x for x in b["fields"]}
	la("bảng con", (b["name"], b["istable"]), ("Vagabond Bot Zalo", 1))
	la("cột bảng Bot thêm", list(fb), ["ma_bot", "ten_bot", "co_token", "trang_thai"])
	dung("không cột mật khẩu nào trong bảng", all(x["fieldtype"] != "Password" for x in b["fields"]))
	dung("số bot, đã khai, kết quả chỉ đọc", all(fb[k].get("read_only") == 1 for k in ("ma_bot", "co_token", "trang_thai")))
	dung("mọi cột có nhãn và lời dẫn tiếng Việt", all(x.get("label") and x.get("description") for x in b["fields"]))
	c = json.load(open(os.path.join(GOC, "vagabond/doctype/vagabond_kenh_zalo/vagabond_kenh_zalo.json"), encoding="utf-8"))
	bc = [x for x in c["fields"] if x["fieldname"] == "bot"][0]
	la("cột bot của nhóm", (bc["fieldtype"], bc["default"], bc.get("read_only")), ("Data", "1", 1))
	dung("modified bảng nhóm đã đẩy", c["modified"] >= "2026-10-20 12")
	js = open(os.path.join(GOC, "vagabond/doctype/vagabond_settings/vagabond_settings.js"), encoding="utf-8").read()
	dung("nút Thêm bot", 'data-zl="thembot">Thêm bot (bot chính đầy nhóm)</button>' in js)
	dung("nút Nối lại và Đổi token theo số bot", 'data-zl="noi:\' + esc(r.ma_bot)' in js and 'data-zl="token:\' + esc(r.ma_bot)' in js)
	dung("hộp Thêm bot gọi luu_bot rồi nối luôn", "vagabond.kenh_zalo.luu_bot" in js and "return noiBot(frm, m.ma_bot)" in js)
	dung("không còn làm cứng bot thứ hai", "noi2" not in js and "zalo_bot_token_2" not in js)
	dung("lưới không cho thêm dòng tay", "set_df_property('zalo_bot_phu', 'cannot_add_rows', 1)" in js)


@ca("v606 Codex #492 P2 tái hiện: đọc Cài đặt lỗi khi chọn bot thì KHÔNG gửi bằng bot chính, trả gửi lại; lỗi chết giao dịch vẫn đi lên")
def _loi_doc():
	# Trước bản sửa (0a252627a): cả ba chỗ đọc lỗi đều gửi bằng token bot chính vào
	# nhóm của bot 5; Zalo từ chối vì bot chính không ở trong nhóm, tin ghi Lỗi và mất.
	url = []

	def hong():
		raise RuntimeError("doc Cai dat loi")
	tk = lambda bot="1": {"1": "111:CHINH", "5": "555:NAM"}[kz.ma_bot(bot)]
	cho = [("_cac_nhom", dict(_cac_nhom=hong, _doc_chat_moi=lambda: [{"chat_id": "g5", "bot": "5"}], _bot_them=lambda: [{"ma_bot": "5"}])),
		("_doc_chat_moi", dict(_cac_nhom=lambda: [], _doc_chat_moi=hong, _bot_them=lambda: [{"ma_bot": "5"}])),
		("_bot_them", dict(_cac_nhom=lambda: [{"chat_id": "g5", "bot": "5"}], _doc_chat_moi=lambda: [], _bot_them=hong))]
	# Thêm một lối: hàm đọc bảng Bot thêm THẬT, chính Frappe đọc lỗi.
	cho.append(("Cài đặt", dict(_cac_nhom=lambda: [{"chat_id": "g5", "bot": "5"}], _doc_chat_moi=lambda: [])))
	for ten, gia in cho:
		url.clear()
		with patch.multiple(kz, _token=tk, **gia), patch.dict("sys.modules", {"requests": _mang(url)}), \
				patch.object(kz.frappe, "get_single", lambda *a: hong(), create=True):
			tt, loi = kz._gui_zalo("g5", "x")
		la("%s lỗi: không gọi Zalo" % ten, url, [])
		la("%s lỗi: trả gửi lại" % ten, tt, kz.MANG_LOI)
		dung("%s lỗi: lời báo nói rõ" % ten, "bot gửi" in loi and "gửi lại" in loi)

	class QueryDeadlockError(Exception):
		pass

	def chet():
		raise QueryDeadlockError("deadlock")
	with patch.multiple(kz, _token=tk, _cac_nhom=chet, _doc_chat_moi=lambda: [], _bot_them=lambda: []), \
			patch.dict("sys.modules", {"requests": _mang(url)}):
		try:
			kz._gui_zalo("g5", "x")
			len_ = "khong"
		except QueryDeadlockError:
			len_ = "len"
	la("lỗi chết giao dịch đi lên", len_, "len")


@ca("v606 Codex #492 P2 (4324386326) tái hiện: đọc token lỗi tạm thời trước đây ghi Lỗi (mất tin); giờ không gọi Zalo, trả gửi lại; lỗi chết giao dịch đi lên")
def _loi_token():
	# Trên a9349cf96: cả bot 5 lẫn bot chính đều ra ("Lỗi", "Chưa ... token ...") khi
	# kho mật khẩu ném lỗi, và _gui_mot ghi Lỗi chứ không trả về Chờ gửi.
	url = []

	def hong(*a, **k):
		raise RuntimeError("kho mat khau loi")
	pw = types.ModuleType("frappe.utils.password")
	pw.get_decrypted_password = hong
	for bot, s in (("5", types.SimpleNamespace(get_password=lambda *a, **k: "x")), ("1", types.SimpleNamespace(get_password=hong))):
		url.clear()
		with patch.object(kz, "_bot_chat", lambda c: bot), patch.object(kz.frappe, "get_single", lambda *a: s, create=True), \
				patch.dict("sys.modules", {"requests": _mang(url), "frappe.utils.password": pw}):
			tt, loi = kz._gui_zalo("g", "x")
		la("bot %s: không gọi Zalo" % bot, url, [])
		la("bot %s: trả gửi lại" % bot, tt, kz.MANG_LOI)
		dung("bot %s: lời báo nói rõ" % bot, "token" in loi and "gửi lại" in loi)
	pw.get_decrypted_password = lambda *a, **k: None
	with patch.object(kz, "_bot_chat", lambda c: "5"), patch.dict("sys.modules", {"requests": _mang(url), "frappe.utils.password": pw}):
		la("chưa khai token thật thì vẫn là Lỗi rõ ràng", kz._gui_zalo("g", "x")[0], "Lỗi")

	class QueryDeadlockError(Exception):
		pass

	def chet(*a, **k):
		raise QueryDeadlockError("deadlock")
	pw.get_decrypted_password = chet
	with patch.object(kz, "_bot_chat", lambda c: "5"), patch.dict("sys.modules", {"requests": _mang(url), "frappe.utils.password": pw}):
		try:
			kz._gui_zalo("g", "x")
			len_ = "khong"
		except QueryDeadlockError:
			len_ = "len"
	la("lỗi chết giao dịch đi lên", len_, "len")
