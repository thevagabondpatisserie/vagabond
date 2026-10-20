"""v591: nối được nhiều nhóm Zalo, mỗi nhóm có mã nhóm để đối chiếu.

Ca thật 12/10/2026 (anh Việt): thêm bot vào nhóm "Sales Vagabond - Nhóm Bán
hàng", @nhắc bot, nhưng hộp "Chọn nhóm đã nhắn bot" chỉ có MỘT dòng tên "Viet
Nguyen". Đọc site: nhóm mới ĐÃ vào danh sách lúc 18:56 (mã ...4436), nhưng:
  1. Zalo không gửi tên nhóm, chỉ tên người nhắc, nên mọi nhóm đều hiện
     "Viet Nguyen", không phân biệt được;
  2. hộp chọn đọc bản Cài đặt tải lúc mở màn, nhóm nhắc bot sau đó không hiện;
  3. chọn xong máy lấy tên người nhắc làm tên nhóm.
Sửa: mã nhóm 4 ký tự cuối, bot trả lời mã đó trong nhóm, hộp chọn đọc mới từ
máy chủ và báo nhóm nào đang gán cho dòng nào. Dữ liệu mẫu dưới đây là đúng
hình dạng danh sách đọc trên site (đã bỏ bớt chat riêng).
"""
import json
import sys
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, la, dung

# Frappe giả của bộ kiểm chưa có get_url (cùng cách thu_bo_phan_583 làm).
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"
from vagabond import kenh_zalo as kz  # noqa: E402

SITE = [
	{"chat_id": "zgr-50abae45f4271d794436", "loai": "GROUP", "luc": "2026-10-12 18:56", "nguoi": "Viet Nguyen", "ten": "Viet Nguyen"},
	{"chat_id": "8825bdfe3da9d4f78db8", "loai": "PRIVATE", "luc": "2026-10-12 18:55", "nguoi": "Viet Nguyen", "ten": "Viet Nguyen"},
	{"chat_id": "4b73b314f841111f4850", "loai": "PRIVATE", "luc": "2026-10-06 18:10", "nguoi": "Quang Khải", "ten": "Quang Khải"},
	{"chat_id": "zgr-ddb5915c2431cd6f9420", "loai": "GROUP", "luc": "2026-10-04 12:23", "nguoi": "Viet Nguyen", "ten": "Viet Nguyen"},
]
BANG = [
	{"ten_nhom": "ERP Văn Phòng - Kế Toán - Thu Mua", "chat_id": "zgr-ddb5915c2431cd6f9420"},
	{"ten_nhom": "Sales Vagabond - Nhóm Bán hàng", "chat_id": None},
]


@ca("v591 Zalo: mã nhóm là 4 ký tự cuối, viết hoa, bỏ tiền tố zgr-")
def _ma():
	la("nhóm ERP", kz.ma_ngan("zgr-ddb5915c2431cd6f9420"), "9420")
	la("nhóm Bán hàng", kz.ma_ngan("zgr-50abae45f4271d794436"), "4436")
	la("chữ thường thành hoa", kz.ma_ngan("zgr-0000abcd"), "ABCD")
	la("rỗng", kz.ma_ngan(None), "")


@ca("v591 Zalo: danh sách chọn có đủ hai nhóm của site, mới nhất trước, bỏ chat riêng, báo nhóm đang gán")
def _ds():
	ds = kz.ds_nhom_chon(SITE, BANG)
	la("hai nhóm, nhóm Bán hàng vừa nhắc đứng đầu", [x["ma"] for x in ds], ["4436", "9420"])
	la("nhóm ERP đang gán cho dòng ERP", ds[1]["dang_gan"], ["ERP Văn Phòng - Kế Toán - Thu Mua"])
	la("nhóm Bán hàng chưa gán", ds[0]["dang_gan"], [])
	dung("không có chat riêng", all(not x["chat_id"].startswith(("8825", "4b73")) for x in ds))
	la("dòng hỏng bị bỏ qua", kz.ds_nhom_chon([None, {"loai": "GROUP"}, "x"], []), [])


@ca("v591 Zalo: bot trả lời mã nhóm lần đầu, không trả lời lại trong 60 phút")
def _can_chao():
	la("chưa trả lời bao giờ", kz.can_chao(SITE, "zgr-50abae45f4271d794436", "2026-10-12 19:00"), True)
	da = [dict(SITE[0], chao="2026-10-12 18:56")]
	la("24 phút sau thì không", kz.can_chao(da, "zgr-50abae45f4271d794436", "2026-10-12 19:20"), False)
	la("đủ 60 phút thì lại trả lời", kz.can_chao(da, "zgr-50abae45f4271d794436", "2026-10-12 19:56"), True)
	la("mốc hỏng thì trả lời", kz.can_chao([dict(SITE[0], chao="abc")], "zgr-50abae45f4271d794436", "2026-10-12 19:00"), True)


@ca("v591 Zalo: tin trả lời có mã nhóm và đường đi trong ERP, không lộ mã chat đầy đủ, không gạch dài")
def _soan():
	t = kz.soan_chao("4436")
	dung("có mã nhóm hai lần", t.count("4436") == 2)
	dung("chỉ đúng nút trên màn", "Chọn nhóm đã nhắn bot" in t and "Zalo bắn tin nhóm" in t)
	dung("ngắn", len(t) <= kz.TOI_DA_KY_TU)
	dung("không em dash, en dash", "\u2014" not in t and "\u2013" not in t)


def _goi_nhan(cu, cap, luc, enq=None, loi=None):
	"""Gọi đúng cửa webhook nhan() như Zalo gọi; trả (danh sách đã ghi, các lần xếp việc)."""
	f = kz.frappe
	ghi, xep = {}, []
	s = types.SimpleNamespace(get_password=lambda *a, **k: "khoa-bi-mat-16-ky-tu")
	req = types.SimpleNamespace(data=json.dumps(cap).encode())

	def enqueue(ham, **kw):
		if enq:
			raise enq
		xep.append((ham, kw))
	with patch.object(f, "get_single", lambda *a: s, create=True), \
			patch.object(f, "request", req, create=True), \
			patch.object(f, "get_request_header", lambda k: "khoa-bi-mat-16-ky-tu", create=True), \
			patch.object(f, "local", types.SimpleNamespace(response={}), create=True), \
			patch.object(f.db, "sql", lambda q, *a, **k: [(json.dumps(cu),)] if "select value" in q else [], create=True), \
			patch.object(f.db, "set_single_value", lambda dt, k, v: ghi.__setitem__(k, v), create=True), \
			patch.object(f.db, "commit", lambda: None, create=True), \
			patch.object(f, "enqueue", enqueue, create=True), \
			patch.object(f, "log_error", lambda *a, **k: (loi if loi is not None else []).append(a), create=True), \
			patch.object(kz, "now_datetime", lambda: luc):
		kz.nhan()
	return json.loads(ghi.get("zalo_chat_moi") or "[]"), xep


def _cap(chat_id, loai="GROUP"):
	return {"message": {"chat": {"id": chat_id, "chat_type": loai}, "from": {"display_name": "Viet Nguyen"}}}


@ca("v591 Zalo: nhóm nhắc bot qua webhook thì xếp đúng một tin trả lời, nhắc lại ngay thì không")
def _webhook():
	ds, xep = _goi_nhan([], _cap("zgr-50abae45f4271d794436"), "2026-10-12 18:56:30")
	la("xếp một việc trả lời đúng nhóm", xep, [("vagabond.kenh_zalo.chao_nhom", {"queue": "short", "chat_id": "zgr-50abae45f4271d794436"})])
	la("ghi mốc đã trả lời", ds[0].get("chao"), "2026-10-12 18:56")
	ds2, xep2 = _goi_nhan(ds, _cap("zgr-50abae45f4271d794436"), "2026-10-12 19:05:00")
	la("nhắc lại sau 9 phút không trả lời nữa", xep2, [])
	la("vẫn giữ mốc cũ", ds2[0].get("chao"), "2026-10-12 18:56")
	_, xep3 = _goi_nhan([], _cap("8825bdfe3da9d4f78db8", "PRIVATE"), "2026-10-12 18:55:00")
	la("chat riêng không trả lời", xep3, [])


@ca("v591 Zalo: xếp việc trả lời lỗi thì webhook vẫn ghi nhóm, log chỉ có mã ngắn")
def _webhook_loi():
	loi = []
	ds, _ = _goi_nhan([], _cap("zgr-50abae45f4271d794436"), "2026-10-12 18:56:30", enq=RuntimeError("redis"), loi=loi)
	la("nhóm vẫn được ghi", ds[0]["chat_id"], "zgr-50abae45f4271d794436")
	dung("có log", len(loi) == 1)
	dung("log có mã ngắn, không có mã chat đầy đủ", "4436" in str(loi[0]) and "50abae45" not in str(loi[0]))


@ca("v591 Zalo: worker gửi tin trả lời vào đúng nhóm; lỗi gửi chỉ log mã ngắn")
def _chao():
	f = kz.frappe
	goi, loi = [], []

	def go(method, body, *a):
		goi.append((method, body))
		return "Lỗi", "Bot chưa vào nhóm", None
	# v606 Codex #492: _gui_zalo đọc bot của nhóm trước khi gọi; ca này cho bản đọc trả bot chính.
	with patch.object(kz, "_goi", go), patch.object(kz, "_bot_chat", lambda c: "1"), \
			patch.object(f, "log_error", lambda *a, **k: loi.append(a), create=True):
		kz.chao_nhom("zgr-50abae45f4271d794436")
	la("gửi sendMessage đúng nhóm", (goi[0][0], goi[0][1]["chat_id"]), ("sendMessage", "zgr-50abae45f4271d794436"))
	dung("nội dung có mã nhóm", "Mã nhóm: 4436" in goi[0][1]["text"])
	dung("log lỗi có mã ngắn, không mã đầy đủ", "4436" in str(loi[0]) and "50abae45" not in str(loi[0]))


@ca("v591 Zalo: hộp chọn đọc danh sách MỚI từ bảng, chỉ quản trị gọi được")
def _doc_moi():
	f = kz.frappe
	cau = []

	def sql(q, *a, **k):
		cau.append(q)
		return [(json.dumps(SITE),)]
	nhom = [types.SimpleNamespace(as_dict=lambda r=r: r) for r in BANG]
	with patch.object(f, "get_roles", lambda *a, **k: ["System Manager"], create=True), \
			patch.object(f.db, "sql", sql, create=True), \
			patch.object(f, "get_single", lambda *a: types.SimpleNamespace(get=lambda k: nhom), create=True):
		ds = kz.nhom_da_nhan_bot()
	dung("đọc thẳng bảng Singles, không qua bộ nhớ đệm", any("tabSingles" in q and "zalo_chat_moi" in q for q in cau))
	la("đủ hai nhóm", [x["ma"] for x in ds], ["4436", "9420"])
	with patch.object(f, "get_roles", lambda *a, **k: ["Sales User"], create=True), \
			patch.object(f, "PermissionError", Exception, create=True):
		try:
			kz.nhom_da_nhan_bot()
			dung("phải chặn người không phải quản trị", False)
		except Exception as e:
			dung("báo quyền", "quản trị" in str(e))
