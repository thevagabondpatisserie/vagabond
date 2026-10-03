"""v559 (#410): bắn tin ERP vào nhóm Zalo qua Zalo Bot.

Anh Việt 02/10/2026 chọn thử Zalo trước Lark. Các ca theo danh sách Codex
góp ý trên #410: rollback không gửi, dịch vụ lỗi không chặn lưu, hai worker
không cùng claim, giờ im, khoá bí mật không lộ, timeout ghi Chưa rõ.
"""
import json
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, la, dung, nem, Doi
from vagabond import kenh_zalo as kz


@ca("v559 Zalo: soạn tin có loại, việc, phụ trách, hạn, đường mở; không quá 2000 ký tự")
def _soan():
	t = kz.soan_tin("viec", "Khoản trả trước chờ duyệt: PKT-1", ["HĐ 8", ""], "https://erp/cong-no-phai-tra",
		nguoi="Kế toán", han="Trong ngày")
	la("dòng đầu có loại", t.split("\n")[0], "✅ VIỆC CẦN LÀM: Khoản trả trước chờ duyệt: PKT-1")
	dung("bỏ dòng rỗng", "- \n" not in t and t.count("- ") == 1)
	dung("có phụ trách, hạn, đường mở", "Phụ trách: Kế toán" in t and "Hạn: Trong ngày" in t and t.endswith("Mở: https://erp/cong-no-phai-tra"))
	dai = kz.soan_tin("canh_bao", "x", ["y" * 3000], "https://erp/l")
	dung("cắt còn 2000 mà giữ đường mở", len(dai) <= 2000 and dai.endswith("Mở: https://erp/l"))
	la("loại lạ thành Thông báo", kz.soan_tin("la", "a").split(":")[0], "ℹ️ THÔNG BÁO")


@ca("v559 Zalo: giờ im theo nhóm, qua nửa đêm, để trống là không im")
def _gio_im():
	la("23:00 trong 22:00-07:00", kz.trong_gio_im("23:00", "22:00", "07:00"), True)
	la("06:59 trong 22:00-07:00", kz.trong_gio_im("06:59", "22:00", "07:00"), True)
	la("07:00 ngoài 22:00-07:00", kz.trong_gio_im("07:00", "22:00", "07:00"), False)
	la("12:30 trong 12:00-13:00", kz.trong_gio_im("12:30", "12:00", "13:00"), True)
	la("để trống", kz.trong_gio_im("23:00", "", ""), False)
	la("gõ sai", kz.trong_gio_im("23:00", "abc", "07:00"), False)


def nhom(**doi):
	r = {"ten_nhom": "Kế toán", "chat_id": "c1", "loai_tin": "", "chu_de": "", "im_tu": "", "im_den": "", "bat": 1}
	r.update(doi)
	return r


@ca("v559 Zalo: chọn nhóm theo loại tin và chủ đề; tắt hoặc thiếu mã chat thì bỏ")
def _chon():
	ds = [nhom(), nhom(ten_nhom="Kho", chat_id="c2", chu_de="kho"), nhom(ten_nhom="Tắt", bat=0),
		nhom(ten_nhom="Thiếu mã", chat_id=" "), nhom(ten_nhom="Chỉ cảnh báo", chat_id="c3", loai_tin="canh_bao")]
	la("việc công nợ", [r["ten_nhom"] for r in kz.chon_nhom(ds, "viec", "cong_no")], ["Kế toán"])
	la("cảnh báo kho", [r["ten_nhom"] for r in kz.chon_nhom(ds, "canh_bao", "kho")], ["Kế toán", "Kho", "Chỉ cảnh báo"])
	la("tách danh sách có khoảng trắng và chấm phẩy", kz.tach_ds(" viec ; canh_bao,,"), {"viec", "canh_bao"})


@ca("v559 Zalo: đọc kết quả Zalo; khoá chống trùng ổn định theo sự kiện và nhóm")
def _ket_qua():
	la("ok", kz.doc_ket_qua({"ok": True, "result": {}}), ("Đã gửi", ""))
	tt, loi = kz.doc_ket_qua({"ok": False, "error_code": 400, "description": "chat not found"})
	la("lỗi có mã và mô tả", (tt, "400" in loi and "chat not found" in loi), ("Lỗi", True))
	la("dữ liệu lạ", kz.doc_ket_qua("<html>")[0], "Chưa rõ")
	la("cùng sự kiện cùng nhóm cùng khoá", kz.khoa_tin("a:1", "Kế toán"), kz.khoa_tin("a:1", "Kế toán"))
	dung("khác nhóm khác khoá", kz.khoa_tin("a:1", "Kế toán") != kz.khoa_tin("a:1", "Kho"))
	dung("khoá ngắn", len(kz.khoa_tin("x" * 500, "y" * 500)) <= 140)


@ca("v559 Zalo: ghi mã chat khi có người @nhắc bot; bỏ trùng, giữ 20, không lưu nội dung")
def _chat_moi():
	cap = {"event_name": "message.text.received", "message": {"text": "@bot bí mật khách",
		"chat": {"id": "g9", "chat_type": "GROUP", "title": "Kế toán Vagabond"}, "from": {"display_name": "Dung"}}}
	ds, moi = kz.ghi_chat_moi([{"chat_id": "g9", "ten": "cũ"}, {"chat_id": "a"}], cap, "2026-10-02 18:00:01")
	la("đưa lên đầu, bỏ trùng", [x["chat_id"] for x in ds], ["g9", "a"])
	la("ghi tên nhóm và người", (moi["ten"], moi["nguoi"], moi["loai"]), ("Kế toán Vagabond", "Dung", "GROUP"))
	dung("không lưu nội dung tin nhắn", "bí mật" not in json.dumps(ds, ensure_ascii=False))
	ds2, _ = kz.ghi_chat_moi([{"chat_id": str(i)} for i in range(30)], cap, "x")
	la("giữ 20", len(ds2), 20)
	la("không có mã chat thì bỏ", kz.ghi_chat_moi([], {"message": {}}, "x")[1], None)


class _Trung(Exception):
	pass


def _chay(nhom_ds, tin, gio="10:00", gui=None, da_co=()):
	"""Chạy gui_hang_doi với Frappe giả; trả (danh sách gửi, bản ghi đã chèn, cập nhật)."""
	f = kz.frappe
	goi, chen, cap = [], [], []
	co = set(da_co)

	def get_doc(d):
		def insert(**k):
			if d["name"] in co:
				raise _Trung()
			co.add(d["name"])
			chen.append(dict(d))
		return types.SimpleNamespace(insert=insert)
	gui = gui or (lambda c, t: ("Đã gửi", ""))
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: nhom_ds), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append((c, t)), gui(c, t))[1]), \
			patch.object(kz, "now_datetime", lambda: types.SimpleNamespace(strftime=lambda fmt: gio)), \
			patch.object(f, "get_doc", get_doc), patch.object(f, "DuplicateEntryError", _Trung, create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), patch.object(f.db, "rollback", lambda: None, create=True), \
			patch.object(f.db, "set_value", lambda dt, ten, v: cap.append((ten, v)), create=True), \
			patch.object(kz, "_con_can", lambda k, n: True):
		kz.gui_hang_doi(tin)
	return goi, chen, cap


TIN = {"loai": "viec", "chu_de": "cong_no", "tieu_de": "Chờ duyệt PKT-1", "dong": ["a"], "link": "https://erp/x",
	"khoa": "cho_duyet:PKT-1"}


@ca("v559 Zalo: gửi đúng nhóm, ghi trạng thái; lần hai cùng sự kiện không gửi lại")
def _gui():
	goi, chen, cap = _chay([nhom(), nhom(ten_nhom="Kho", chat_id="c2", chu_de="kho")], TIN)
	la("gửi đúng một nhóm", [c for c, _ in goi], ["c1"])
	la("ghi một bản, đang gửi", [(r["nhom"], r["trang_thai"]) for r in chen], [("Kế toán", "Đang gửi")])
	la("cập nhật đã gửi", cap[0][1]["trang_thai"], "Đã gửi")
	goi2, chen2, _ = _chay([nhom()], TIN, da_co={chen[0]["name"]})
	la("worker thứ hai vấp khoá chính, không gửi", (goi2, chen2), ([], []))


@ca("v559 Zalo: giờ im hoãn tin thường, Cảnh báo vẫn gửi")
def _hoan():
	n = [nhom(im_tu="22:00", im_den="07:00")]
	goi, chen, _ = _chay(n, TIN, gio="23:10")
	la("tin việc bị hoãn, không gửi", (goi, chen[0]["trang_thai"]), ([], "Hoãn giờ im"))
	goi2, chen2, _ = _chay(n, dict(TIN, loai="canh_bao", khoa="cb:1"), gio="23:10")
	la("cảnh báo vẫn gửi", ([c for c, _ in goi2], chen2[0]["trang_thai"]), (["c1"], "Đang gửi"))


@ca("v559 Zalo: Zalo không trả lời thì ghi Chưa rõ, lỗi thì ghi Lỗi, không ném ra ngoài")
def _loi():
	_, _, cap = _chay([nhom()], TIN, gui=lambda c, t: ("Chưa rõ", "Zalo không trả lời trong 10 giây."))
	la("timeout", cap[0][1]["trang_thai"], "Chưa rõ")
	_, _, cap2 = _chay([nhom()], dict(TIN, khoa="k2"), gui=lambda c, t: ("Lỗi", "Zalo báo lỗi 400"))
	la("lỗi", cap2[0][1]["trang_thai"], "Lỗi")


@ca("v559 Zalo: gọi API không để lộ token; timeout thành Chưa rõ")
def _goi_api():
	class _Hong(Exception):
		pass

	class ReadTimeout(Exception):
		pass
	gia = types.ModuleType("requests")
	da = []

	def post(url, json=None, timeout=None):
		da.append(url)
		raise ReadTimeout("het gio " + url)
	gia.post = post
	with patch.object(kz, "_token", lambda: "123:BIMAT"), patch.dict("sys.modules", {"requests": gia}):
		tt, loi, _ = kz._goi("sendMessage", {"chat_id": "c", "text": "x"})
	la("timeout là Chưa rõ", tt, "Chưa rõ")
	dung("đúng đường API", da and da[0] == "https://bot-api.zaloplatforms.com/bot123:BIMAT/sendMessage")
	dung("lỗi trả về không chứa token", "BIMAT" not in loi)
	with patch.object(kz, "_token", lambda: ""):
		la("thiếu token", kz._goi("sendMessage", {})[0], "Lỗi")


@ca("v559 Zalo: bao() tắt thì không xếp; hàng đợi lỗi không làm hỏng chứng từ")
def _bao():
	f = kz.frappe
	da = []
	cm = types.SimpleNamespace(add=lambda fn: da.append(fn))
	with patch.object(kz, "_bat", lambda: 0), patch.object(f.db, "after_commit", cm, create=True):
		kz.bao("viec", "cong_no", "x")
	la("tắt thì không xếp", da, [])
	with patch.object(kz, "_bat", lambda: 1), patch.object(f.db, "after_commit", cm, create=True):
		kz.bao("viec", "cong_no", "x", khoa="k")
	la("bật thì xếp sau commit, chưa gửi ngay", len(da), 1)

	def hong(fn):
		raise RuntimeError("redis")
	loi = []
	with patch.object(kz, "_bat", lambda: 1), \
			patch.object(f.db, "after_commit", types.SimpleNamespace(add=hong), create=True), \
			patch.object(f, "log_error", lambda *a, **k: loi.append(a), create=True):
		kz.bao("viec", "cong_no", "TIEU-DE-RIENG", dong=["SO-TIEN-RIENG"])
	dung("không ném lỗi, có ghi log không lộ nội dung", len(loi) == 1 and "RIENG" not in str(loi[0]))


@ca("v559 Zalo: đường nhận chặn khoá bí mật sai, đúng khoá thì chỉ ghi mã chat")
def _nhan():
	f = kz.frappe
	ghi = {}
	cap = json.dumps({"message": {"chat": {"id": "g1", "chat_type": "GROUP", "title": "Kho"}, "from": {"display_name": "A"}}}).encode()

	def chay(header):
		resp = {}
		req = types.SimpleNamespace(data=cap)
		s = types.SimpleNamespace(get_password=lambda *a, **k: "khoa-bi-mat-16-ky-tu")
		with patch.object(f, "get_single", lambda *a: s, create=True), \
				patch.object(f, "request", req, create=True), \
				patch.object(f, "get_request_header", lambda k: header, create=True), \
				patch.object(f, "local", types.SimpleNamespace(response=resp), create=True), \
				patch.object(f.db, "get_single_value", lambda *a: "[]", create=True), \
				patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True), \
				patch.object(f.db, "commit", lambda: None, create=True), \
				patch.object(kz, "now_datetime", lambda: "2026-10-02 18:00"):
			return kz.nhan(), resp
	kq, resp = chay("sai")
	la("khoá sai bị 401", (kq, resp.get("http_status_code")), ({"ok": False}, 401))
	la("khoá sai không ghi gì", ghi, {})
	kq, resp = chay("khoa-bi-mat-16-ky-tu")
	la("khoá đúng", kq, {"ok": True})
	la("ghi mã nhóm", json.loads(ghi["zalo_chat_moi"])[0]["chat_id"], "g1")


@ca("v559 Zalo: chỉ quản trị nối bot, gửi thử, xem trước")
def _quyen():
	f = kz.frappe
	for ham, a in ((kz.gui_thu, ("c1",)), (kz.xem_truoc, ()), (kz.dang_ky_webhook, ())):
		with patch.object(f, "get_roles", lambda *x, **k: ["Accounts Manager"]), \
				patch.object(f, "PermissionError", Exception, create=True):
			try:
				ham(*a)
				dung("%s phải chặn người không phải quản trị" % ham.__name__, False)
			except Exception as e:
				dung("%s báo quyền" % ham.__name__, "quản trị" in str(e))


@ca("v559 Zalo: lap_truoc_erp báo nhóm Kế toán khi thu mua gửi, không báo khi kế toán tự ghi sổ")
def _noi_cong_no():
	import inspect
	from vagabond import cong_no_ncc as cn
	nguon = inspect.getsource(cn.lap_truoc_erp)
	i = nguon.find("kenh_zalo.bao(")
	dung("có gọi bao", i > 0)
	dung("nằm trong nhánh not ke_toan", "if not ke_toan:" in nguon[max(0, i - 300):i])
	dung("khoá chống trùng theo bút toán", '"cho_duyet:" + je.name' in nguon)


# ===================================================================
# Vòng 2 (Codex review #413 trên c4a7a89): bốn finding, mỗi ca dựng đúng
# chuỗi Codex mô tả, không gọi thêm hàm nào "cho chắc" (bài học #205).

class _Dong(dict):
	__getattr__ = dict.get


class _SoGia:
	"""Bảng Vagabond Tin Kenh giả, giữ đúng ngữ nghĩa câu UPDATE có điều kiện
	của _nhan_lo: chỉ dòng còn "Hoãn giờ im" mới đổi được, mỗi dòng một lần."""

	def __init__(self, dong):
		self.dong = [dict(d) for d in dong]
		self.commit_luc = []

	def sql(self, q, tham=None):
		if "update `tabVagabond Tin Kenh`" in q:
			ma, chat, gioi_han = tham
			assert "where chat_id=%s" in q, "claim phải theo mã chat (Codex #417)"
			n = 0
			for d in self.dong:
				if d["chat_id"] == chat and d["trang_thai"] == "Hoãn giờ im" and n < gioi_han:
					d["trang_thai"], d["ma_lo"] = "Đang gửi gộp", ma
					n += 1
			return []
		raise AssertionError("câu SQL lạ: " + q[:60])

	def get_all(self, dt, filters=None, fields=None, order_by=None, limit_page_length=None):
		ra = [_Dong(d) for d in self.dong if all(d.get(k) == v for k, v in (filters or {}).items())]
		return ra[:limit_page_length] if limit_page_length else ra

	def set_value(self, dt, ten, v):
		for d in self.dong:
			if d["name"] == ten:
				d.update(v)

	def commit(self):
		self.commit_luc.append(len(self.dong))

	def tim(self, ten):
		return next(d for d in self.dong if d["name"] == ten)


def _hoan(i, tieu_de, kiem="", nguon="", nhom_ten="Kế toán", chat_id="c1"):
	nd = kz.soan_tin("viec", tieu_de, ["dòng phụ"], "https://erp/viec/%s" % i)
	return {"name": "R%02d" % i, "nhom": nhom_ten, "chat_id": chat_id, "trang_thai": "Hoãn giờ im", "noi_dung": nd,
		"kiem": kiem, "nguon": nguon, "ma_lo": None}


_DEM_LO = [0]


def _xa(so, gui=None, con_can=None, nhom_ds=None):
	"""Chạy xa_gio_im với sổ giả. Trả danh sách tin đã gửi (chat_id, nội dung)."""
	f = kz.frappe
	da_gui = []

	def hash_(length=10):
		# Mã lượt phải khác nhau giữa các lượt như generate_hash thật; dùng
		# chung bộ đếm cho mọi lượt, kể cả lượt lồng nhau trong ca chạy chồng.
		_DEM_LO[0] += 1
		return "lo%04d" % _DEM_LO[0]
	gui = gui or (lambda c, t: ("Đã gửi", ""))
	db = types.SimpleNamespace(sql=so.sql, set_value=so.set_value, commit=so.commit)
	with patch.object(kz, "_bat", lambda: 1), \
			patch.object(kz, "_cac_nhom", lambda: nhom_ds or [nhom()]), \
			patch.object(kz, "_gui_zalo", lambda c, t: (da_gui.append((c, t)), gui(c, t))[1]), \
			patch.object(kz, "now_datetime", lambda: types.SimpleNamespace(strftime=lambda fmt: "10:00")), \
			patch.object(kz, "_con_can", con_can or (lambda k, n: True)), \
			patch.object(f, "db", db, create=True), patch.object(f, "get_all", so.get_all, create=True), \
			patch.object(f, "generate_hash", hash_, create=True):
		kz.xa_gio_im()
	return da_gui


@ca("v559 #413 P1 tái hiện Codex: 50 việc tiêu đề dài sau giờ im đều tới nhóm, không việc nào bị cắt mà vẫn ghi đã gửi")
def _gop_50():
	so = _SoGia([_hoan(i, "Khoản trả trước ERP chờ duyệt PKT-2026-%05d của nhà cung cấp tên rất dài số %02d" % (i, i))
		for i in range(50)])
	gui = _xa(so)
	la("mọi tin đều trong giới hạn 2.000 ký tự", [len(t) <= 2000 for _, t in gui], [True] * len(gui))
	dung("phải chia nhiều tin", len(gui) >= 2)
	gop = "\n".join(t for _, t in gui)
	la("việc CUỐI có mặt (Codex: last_task_present=False)", "PKT-2026-00049" in gop, True)
	la("mỗi việc xuất hiện đúng một lần", [gop.count("PKT-2026-%05d " % i) for i in range(50)], [1] * 50)
	dung("đường mở của từng việc còn trong tin gộp", "https://erp/viec/49" in gop)
	dung("không có dấu cắt …", "…" not in gop)
	la("50 dòng đều Đã gửi gộp", sorted({d["trang_thai"] for d in so.dong}), ["Đã gửi gộp"])


@ca("v559 #413 P1: một phần gộp lỗi thì chỉ các việc trong phần đó ghi Lỗi, phần đã gửi ghi đã gửi")
def _gop_mot_phan_loi():
	so = _SoGia([_hoan(i, "Việc dài số %02d " % i + "x" * 150) for i in range(30)])
	lan = [0]

	def gui(c, t):
		lan[0] += 1
		return ("Lỗi", "Zalo báo lỗi 500") if lan[0] == 2 else ("Đã gửi", "")
	tin = _xa(so, gui=gui)
	phan2 = [d["name"] for d in so.dong if d["trang_thai"] == "Lỗi"]
	dung("có phần thứ hai", len(tin) >= 2)
	la("dòng Lỗi đúng là dòng nằm trong tin thứ hai",
		sorted(phan2), sorted(d["name"] for d in so.dong if ("Việc dài số %s " % d["name"][1:]) in tin[1][1]))
	dung("phần còn lại vẫn Đã gửi gộp", all(d["trang_thai"] == "Đã gửi gộp" for d in so.dong if d["name"] not in phan2))


@ca("v559 #413 P2 tái hiện Codex: hai lượt xả chạy chồng chỉ gửi mỗi việc một lần")
def _gop_chong():
	so = _SoGia([_hoan(i, "Việc %02d" % i) for i in range(5)])
	vao = [0]
	tat_ca = []

	def gui(c, t):
		tat_ca.append(t)
		if not vao[0]:
			# Lượt thứ hai chen vào đúng lúc lượt đầu đang gọi Zalo (sau claim, trước cập nhật).
			vao[0] = 1
			tat_ca.extend(t2 for _, t2 in _xa(so))
		return "Đã gửi", ""
	_xa(so, gui=gui)
	la("Codex: concurrent_digest_sends phải là 1", ["\n".join(tat_ca).count("Việc %02d" % i) for i in range(5)], [1] * 5)


@ca("v559 #413 P2: worker chết sau khi gọi Zalo thì dòng kẹt Đang gửi gộp, lượt sau KHÔNG gửi lại")
def _gop_chet():
	so = _SoGia([_hoan(i, "Việc %02d" % i) for i in range(3)])

	class _Chet(BaseException):
		pass

	def gui(c, t):
		raise _Chet()
	try:
		_xa(so, gui=gui)
	except _Chet:
		pass
	la("kẹt ở Đang gửi gộp", sorted({d["trang_thai"] for d in so.dong}), ["Đang gửi gộp"])
	la("lượt sau không gửi gì", _xa(so), [])
	dung("claim đã commit trước khi gọi Zalo", len(so.commit_luc) >= 1)


@ca("v559 #413 P2: việc đã duyệt trong giờ im thì không nhắc; việc còn mở vẫn gửi")
def _gop_bo_qua():
	so = _SoGia([_hoan(0, "Chờ duyệt PKT-A", "cho_duyet_truoc_erp", "PKT-A"),
		_hoan(1, "Chờ duyệt PKT-B", "cho_duyet_truoc_erp", "PKT-B")])
	tin = _xa(so, con_can=lambda k, n: n != "PKT-A")
	gop = "\n".join(t for _, t in tin)
	dung("không nhắc việc đã duyệt", "PKT-A" not in gop)
	dung("vẫn nhắc việc còn mở", "PKT-B" in gop)
	la("trạng thái", [so.tim("R00")["trang_thai"], so.tim("R01")["trang_thai"]], [kz.BO_QUA, "Đã gửi gộp"])


@ca("v559 #413 P2: tin gửi ngay cũng hỏi lại việc còn mở trước khi gọi Zalo")
def _gui_ngay_bo_qua():
	f = kz.frappe
	goi, cap = [], []

	def get_doc(d):
		return types.SimpleNamespace(insert=lambda **k: None)
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: [nhom()]), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append(c), ("Đã gửi", ""))[1]), \
			patch.object(kz, "_con_can", lambda k, n: False), \
			patch.object(kz, "now_datetime", lambda: types.SimpleNamespace(strftime=lambda fmt: "10:00")), \
			patch.object(f, "get_doc", get_doc), patch.object(f, "DuplicateEntryError", _Trung, create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), \
			patch.object(f.db, "set_value", lambda dt, ten, v: cap.append(v), create=True):
		kz.gui_hang_doi(dict(TIN, kiem="cho_duyet_truoc_erp", nguon="PKT-1"))
	la("không gọi Zalo", goi, [])
	la("ghi Bỏ qua", cap[0]["trang_thai"], kz.BO_QUA)


@ca("v559 #413 P2: kiểm lại dùng bảng mã cố định; mã lạ hoặc hàm lỗi thì vẫn gửi và có log")
def _con_can():
	f = kz.frappe
	la("không mã kiểm", kz.con_can_lam("", "x", None), True)
	la("hàm trả False", kz.con_can_lam("k", "x", lambda n: False), False)
	log = []
	with patch.object(f, "log_error", lambda *a, **k: log.append(a), create=True):
		la("mã lạ vẫn gửi", kz._con_can("ma_la", "x"), True)
		with patch.object(f, "get_attr", lambda p: (lambda n: (_ for _ in ()).throw(RuntimeError("db"))), create=True):
			la("hàm lỗi vẫn gửi", kz._con_can("cho_duyet_truoc_erp", "x"), True)
		with patch.object(f, "get_attr", lambda p: (lambda n: n == "con"), create=True):
			la("gọi đúng hàm theo bảng", (kz._con_can("cho_duyet_truoc_erp", "con"), kz._con_can("cho_duyet_truoc_erp", "het")), (True, False))
	la("có log cho mã lạ và hàm lỗi", len(log), 2)
	la("bảng trỏ đúng hàm công nợ", kz.DIEU_KIEN["cho_duyet_truoc_erp"], "vagabond.cong_no_ncc.con_cho_duyet_truoc_erp")


@ca("v559 #413 P2: khoản trả trước còn chờ duyệt chỉ khi nháp và còn dấu luồng; đã duyệt, hủy, từ chối là hết việc")
def _cho_duyet():
	from vagabond import cong_no_ncc as cn
	d = cn.DAU_TRUOC_ERP + " Cấn hóa đơn X"
	la("nháp còn dấu", cn.la_cho_duyet_truoc_erp(0, d), True)
	la("đã ghi sổ", cn.la_cho_duyet_truoc_erp(1, d), False)
	la("đã hủy", cn.la_cho_duyet_truoc_erp(2, d), False)
	la("từ chối hoặc rút lại", cn.la_cho_duyet_truoc_erp(0, cn.DAU_DA_BO + " Cấn hóa đơn X"), False)
	nguon = __import__("inspect").getsource(cn.lap_truoc_erp)
	dung("lap_truoc_erp gắn mã kiểm và nguồn", 'kiem="cho_duyet_truoc_erp", nguon=je.name' in nguon)


@ca("v559 #413 P1: đọc kết quả xác minh đường nhận; ok:true ở ngoài không đủ")
def _xac_minh():
	la("setWebhook xác minh ok", kz.doc_xac_minh({"url": "u", "verification": {"ok": True, "hint": "fine"}}), ("ok", "fine"))
	la("setWebhook xác minh hỏng", kz.doc_xac_minh({"url": "u", "verification": {"ok": False, "outcome": "webhook.timeout"}}),
		("loi", "webhook.timeout"))
	la("testWebhook hỏng", kz.doc_xac_minh({"ok": False, "hint": "401"})[0], "loi")
	la("thiếu kết quả", kz.doc_xac_minh({"url": "u"})[0], "chua_ro")
	la("không phải dict", kz.doc_xac_minh(None)[0], "chua_ro")


def _noi(phan_hoi, bi_mat_cu="", test=None):
	"""Chạy dang_ky_webhook với Zalo giả. Trả (kết quả, nhật ký sự kiện theo thứ tự)."""
	f = kz.frappe
	nk = []

	class S:
		flags = types.SimpleNamespace()

		def get_password(self, *a, **k):
			return bi_mat_cu

		def save(self, **k):
			nk.append("save")

	def goi(m, body):
		nk.append(m)
		if m == "getMe":
			return "Đã gửi", "", {"account_name": "VGB"}
		if m == "setWebhook":
			return "Đã gửi", "", phan_hoi
		return test or ("Đã gửi", "", {"ok": True})
	with patch.object(kz, "_chi_quan_tri", lambda: None), patch.object(kz, "_goi", goi), \
			patch.object(kz, "_ghi_noi", lambda tt, g: nk.append("ghi:" + tt)), \
			patch.object(kz, "get_url", lambda p: "https://erp" + p), \
			patch.object(f, "get_single", lambda *a: S(), create=True), \
			patch.object(f.db, "commit", lambda: nk.append("commit"), create=True):
		return kz.dang_ky_webhook(), nk


@ca("v559 #413 P1 tái hiện Codex: xác minh thất bại thì KHÔNG báo đã nối (failed_verification_reported_success phải 0)")
def _noi_hong():
	kq, nk = _noi({"url": "u", "verification": {"ok": False, "hint": "Endpoint returned 401"}})
	la("không báo thành công", kq["ok"], 0)
	dung("nói rõ thất bại và lý do", "THẤT BẠI" in kq["loi_nhan"] and "401" in kq["loi_nhan"])
	dung("ghi kết quả vào Cài đặt", "ghi:loi" in nk)


@ca("v559 #413 P1: khoá bí mật mới được commit TRƯỚC khi gọi setWebhook")
def _noi_commit():
	kq, nk = _noi({"url": "u", "verification": {"ok": True}})
	la("thứ tự", [x for x in nk if x in ("save", "commit", "setWebhook")][:3], ["save", "commit", "setWebhook"])
	la("báo thành công khi Zalo xác minh ok", kq["ok"], 1)


@ca("v559 #413 P1: Zalo không trả kết quả xác minh thì gọi testWebhook kiểm lại, vẫn chưa rõ thì không báo đã nối")
def _noi_chua_ro():
	kq, nk = _noi({"url": "u"}, bi_mat_cu="x" * 40, test=("Đã gửi", "", {"ok": True, "hint": "ok"}))
	dung("có gọi testWebhook", "testWebhook" in nk)
	la("testWebhook ok thì báo đã nối", kq["ok"], 1)
	kq2, _ = _noi({"url": "u"}, bi_mat_cu="x" * 40, test=("Chưa rõ", "timeout", None))
	la("vẫn chưa rõ thì không báo đã nối", (kq2["ok"], kq2["xac_minh"]), (0, "chua_ro"))


# ===================================================================
# Vòng 3 (Codex review #417 trên 4ebb73e): khoá người nhận theo mã chat,
# sổ gửi không cho xoá.

def _gui_nhom(ds_nhom, tin=None):
	f = kz.frappe
	goi, co = [], set()

	def get_doc(d):
		def insert(**k):
			if d["name"] in co:
				raise _Trung()
			co.add(d["name"])
		return types.SimpleNamespace(insert=insert)
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: ds_nhom), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append(c), ("Đã gửi", ""))[1]), \
			patch.object(kz, "_con_can", lambda k, n: True), \
			patch.object(kz, "now_datetime", lambda: types.SimpleNamespace(strftime=lambda fmt: "10:00")), \
			patch.object(f, "get_doc", get_doc), patch.object(f, "DuplicateEntryError", _Trung, create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), patch.object(f.db, "rollback", lambda: None, create=True), \
			patch.object(f.db, "set_value", lambda *a: None, create=True):
		kz.gui_hang_doi(tin or TIN)
	return goi


@ca("v559 #417 tái hiện Codex: hai dòng trùng tên khác mã chat đều nhận tin (trước: 1 trên 2)")
def _trung_ten():
	la("cả hai mã chat đều được gửi", sorted(_gui_nhom([nhom(chat_id="c1"), nhom(chat_id="c2")])), ["c1", "c2"])
	la("cùng một mã chat hai dòng thì chỉ gửi một lần", _gui_nhom([nhom(chat_id="c1"), nhom(ten_nhom="Khác", chat_id="c1")]), ["c1"])
	la("khoá theo mã chat, bỏ khoảng trắng", kz.khoa_tin("a:1", " c1 "), kz.khoa_tin("a:1", "c1"))


@ca("v559 #417: đổi tên nhóm trong giờ im thì tin hoãn vẫn được xả theo mã chat")
def _doi_ten():
	so = _SoGia([_hoan(0, "Việc cũ", nhom_ten="Kế toán cũ", chat_id="c1")])
	tin = _xa(so, nhom_ds=[nhom(ten_nhom="Kế toán mới", chat_id="c1")])
	la("vẫn gửi đúng mã chat", [c for c, _ in tin], ["c1"])
	la("dòng hoãn đã gửi gộp", so.tim("R00")["trang_thai"], "Đã gửi gộp")
	la("nhóm thiếu mã chat thì bỏ qua, không claim", _xa(_SoGia([_hoan(1, "x")]), nhom_ds=[nhom(chat_id="")]), [])


@ca("v559 #417: Cài đặt chặn hai dòng nhóm trùng tên hoặc trùng mã chat")
def _kiem_trung():
	la("không trùng", kz.kiem_nhom_trung([nhom(), nhom(ten_nhom="Kho", chat_id="c2")]), "")
	dung("trùng tên (không phân biệt hoa thường)", "cùng tên" in kz.kiem_nhom_trung([nhom(), nhom(ten_nhom="kế toán", chat_id="c2")]))
	dung("trùng mã chat", "cùng mã chat" in kz.kiem_nhom_trung([nhom(), nhom(ten_nhom="Kho", chat_id=" c1 ")]))
	la("dòng chưa có mã chat không tính trùng mã", kz.kiem_nhom_trung([nhom(chat_id=""), nhom(ten_nhom="Kho", chat_id="")]), "")
	# Chạy thật validate của Cài đặt (không dò chuỗi): lưu bảng trùng phải bị chặn.
	from vagabond.vagabond.doctype.vagabond_settings import vagabond_settings as vs
	from vagabond import tai_khoan_btp

	class _Dong(dict):
		def as_dict(self):
			return dict(self)

	def cai_dat(ds):
		return types.SimpleNamespace(phu_thu=0, kitchen_lat=10.7, kitchen_lng=106.6,
			get=lambda k: [_Dong(r) for r in ds] if k == "zalo_nhom" else None)
	with patch.object(tai_khoan_btp, "kiem_o_cau_hinh", lambda doc: None):
		vs.VagabondSettings.validate(cai_dat([nhom(), nhom(ten_nhom="Kho", chat_id="c2")]))
		nem("lưu bảng trùng mã chat bị chặn", lambda: vs.VagabondSettings.validate(cai_dat([nhom(), nhom(ten_nhom="Kho")])))


@ca("v559 #417 tái hiện Codex: sổ gửi Zalo không vai nào được xoá (bằng chứng chống trùng phải còn)")
def _so_khong_xoa():
	import json
	import os
	p = os.path.join(os.path.dirname(kz.__file__), "vagabond", "doctype", "vagabond_tin_kenh", "vagabond_tin_kenh.json")
	d = json.load(open(p, encoding="utf-8"))
	la("không vai nào có quyền xoá", [x["role"] for x in d["permissions"] if x.get("delete")], [])
	la("không vai nào được sửa tay", [x["role"] for x in d["permissions"] if x.get("write")], [])
	dung("mã chat có chỉ mục để claim", any(x["fieldname"] == "chat_id" and x.get("search_index") for x in d["fields"]))
