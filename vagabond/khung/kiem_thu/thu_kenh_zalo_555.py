"""v555 (#410): bắn tin ERP vào nhóm Zalo qua Zalo Bot.

Anh Việt 02/10/2026 chọn thử Zalo trước Lark. Các ca theo danh sách Codex
góp ý trên #410: rollback không gửi, dịch vụ lỗi không chặn lưu, hai worker
không cùng claim, giờ im, khoá bí mật không lộ, timeout ghi Chưa rõ.
"""
import json
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, la, dung, Doi
from vagabond import kenh_zalo as kz


@ca("v555 Zalo: soạn tin có loại, việc, phụ trách, hạn, đường mở; không quá 2000 ký tự")
def _soan():
	t = kz.soan_tin("viec", "Khoản trả trước chờ duyệt: PKT-1", ["HĐ 8", ""], "https://erp/cong-no-phai-tra",
		nguoi="Kế toán", han="Trong ngày")
	la("dòng đầu có loại", t.split("\n")[0], "✅ VIỆC CẦN LÀM: Khoản trả trước chờ duyệt: PKT-1")
	dung("bỏ dòng rỗng", "- \n" not in t and t.count("- ") == 1)
	dung("có phụ trách, hạn, đường mở", "Phụ trách: Kế toán" in t and "Hạn: Trong ngày" in t and t.endswith("Mở: https://erp/cong-no-phai-tra"))
	dai = kz.soan_tin("canh_bao", "x", ["y" * 3000], "https://erp/l")
	dung("cắt còn 2000 mà giữ đường mở", len(dai) <= 2000 and dai.endswith("Mở: https://erp/l"))
	la("loại lạ thành Thông báo", kz.soan_tin("la", "a").split(":")[0], "ℹ️ THÔNG BÁO")


@ca("v555 Zalo: giờ im theo nhóm, qua nửa đêm, để trống là không im")
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


@ca("v555 Zalo: chọn nhóm theo loại tin và chủ đề; tắt hoặc thiếu mã chat thì bỏ")
def _chon():
	ds = [nhom(), nhom(ten_nhom="Kho", chat_id="c2", chu_de="kho"), nhom(ten_nhom="Tắt", bat=0),
		nhom(ten_nhom="Thiếu mã", chat_id=" "), nhom(ten_nhom="Chỉ cảnh báo", chat_id="c3", loai_tin="canh_bao")]
	la("việc công nợ", [r["ten_nhom"] for r in kz.chon_nhom(ds, "viec", "cong_no")], ["Kế toán"])
	la("cảnh báo kho", [r["ten_nhom"] for r in kz.chon_nhom(ds, "canh_bao", "kho")], ["Kế toán", "Kho", "Chỉ cảnh báo"])
	la("tách danh sách có khoảng trắng và chấm phẩy", kz.tach_ds(" viec ; canh_bao,,"), {"viec", "canh_bao"})


@ca("v555 Zalo: đọc kết quả Zalo; khoá chống trùng ổn định theo sự kiện và nhóm")
def _ket_qua():
	la("ok", kz.doc_ket_qua({"ok": True, "result": {}}), ("Đã gửi", ""))
	tt, loi = kz.doc_ket_qua({"ok": False, "error_code": 400, "description": "chat not found"})
	la("lỗi có mã và mô tả", (tt, "400" in loi and "chat not found" in loi), ("Lỗi", True))
	la("dữ liệu lạ", kz.doc_ket_qua("<html>")[0], "Chưa rõ")
	la("cùng sự kiện cùng nhóm cùng khoá", kz.khoa_tin("a:1", "Kế toán"), kz.khoa_tin("a:1", "Kế toán"))
	dung("khác nhóm khác khoá", kz.khoa_tin("a:1", "Kế toán") != kz.khoa_tin("a:1", "Kho"))
	dung("khoá ngắn", len(kz.khoa_tin("x" * 500, "y" * 500)) <= 140)


@ca("v555 Zalo: ghi mã chat khi có người @nhắc bot; bỏ trùng, giữ 20, không lưu nội dung")
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
			patch.object(f.db, "set_value", lambda dt, ten, v: cap.append((ten, v)), create=True):
		kz.gui_hang_doi(tin)
	return goi, chen, cap


TIN = {"loai": "viec", "chu_de": "cong_no", "tieu_de": "Chờ duyệt PKT-1", "dong": ["a"], "link": "https://erp/x",
	"khoa": "cho_duyet:PKT-1"}


@ca("v555 Zalo: gửi đúng nhóm, ghi trạng thái; lần hai cùng sự kiện không gửi lại")
def _gui():
	goi, chen, cap = _chay([nhom(), nhom(ten_nhom="Kho", chat_id="c2", chu_de="kho")], TIN)
	la("gửi đúng một nhóm", [c for c, _ in goi], ["c1"])
	la("ghi một bản, đang gửi", [(r["nhom"], r["trang_thai"]) for r in chen], [("Kế toán", "Đang gửi")])
	la("cập nhật đã gửi", cap[0][1]["trang_thai"], "Đã gửi")
	goi2, chen2, _ = _chay([nhom()], TIN, da_co={chen[0]["name"]})
	la("worker thứ hai vấp khoá chính, không gửi", (goi2, chen2), ([], []))


@ca("v555 Zalo: giờ im hoãn tin thường, Cảnh báo vẫn gửi")
def _hoan():
	n = [nhom(im_tu="22:00", im_den="07:00")]
	goi, chen, _ = _chay(n, TIN, gio="23:10")
	la("tin việc bị hoãn, không gửi", (goi, chen[0]["trang_thai"]), ([], "Hoãn giờ im"))
	goi2, chen2, _ = _chay(n, dict(TIN, loai="canh_bao", khoa="cb:1"), gio="23:10")
	la("cảnh báo vẫn gửi", ([c for c, _ in goi2], chen2[0]["trang_thai"]), (["c1"], "Đang gửi"))


@ca("v555 Zalo: Zalo không trả lời thì ghi Chưa rõ, lỗi thì ghi Lỗi, không ném ra ngoài")
def _loi():
	_, _, cap = _chay([nhom()], TIN, gui=lambda c, t: ("Chưa rõ", "Zalo không trả lời trong 10 giây."))
	la("timeout", cap[0][1]["trang_thai"], "Chưa rõ")
	_, _, cap2 = _chay([nhom()], dict(TIN, khoa="k2"), gui=lambda c, t: ("Lỗi", "Zalo báo lỗi 400"))
	la("lỗi", cap2[0][1]["trang_thai"], "Lỗi")


@ca("v555 Zalo: gọi API không để lộ token; timeout thành Chưa rõ")
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


@ca("v555 Zalo: bao() tắt thì không xếp; hàng đợi lỗi không làm hỏng chứng từ")
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


@ca("v555 Zalo: đường nhận chặn khoá bí mật sai, đúng khoá thì chỉ ghi mã chat")
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


@ca("v555 Zalo: chỉ quản trị nối bot, gửi thử, xem trước")
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


@ca("v555 Zalo: lap_truoc_erp báo nhóm Kế toán khi thu mua gửi, không báo khi kế toán tự ghi sổ")
def _noi_cong_no():
	import inspect
	from vagabond import cong_no_ncc as cn
	nguon = inspect.getsource(cn.lap_truoc_erp)
	i = nguon.find("kenh_zalo.bao(")
	dung("có gọi bao", i > 0)
	dung("nằm trong nhánh not ke_toan", "if not ke_toan:" in nguon[max(0, i - 300):i])
	dung("khoá chống trùng theo bút toán", '"cho_duyet:" + je.name' in nguon)
