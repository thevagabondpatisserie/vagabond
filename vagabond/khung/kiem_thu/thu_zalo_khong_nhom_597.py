"""v597 vòng Codex #481 (248498a): ba finding, mỗi finding một nhóm ca.

F1 (dat_ban.py, tiec_web.py): kenh_zalo.bao() trả None (Zalo tắt) hoặc [] (chưa
   có nhóm bật nhận Việc + Đặt bàn) mà KHÔNG ném lỗi. Hook chỉ chạy lúc tạo
   phiếu, nên gán nhóm sau cũng không báo lại phiếu đó. Phải có Error Log nêu
   tên phiếu để người trực báo tay.
F2 (gui_thu.py): còi báo động thư hỏng đóng dấu "đã hú" kể cả khi không đường
   nào nhận (Zalo không ghi được dòng nào, thư dự phòng không gửi được), rồi
   im 180 phút. Không có đường thì không đóng dấu và ghi Error Log (giãn 3 giờ).
F3 (banh.html): ô khách nhập là "Số dĩa bã mía" nhưng phiếu bếp và giỏ vẫn ghi
   "dĩa giấy". Phiếu bếp và giỏ phải ghi đúng "dĩa bã mía".

Ca kiểm gọi hàm THẬT của dat_ban, tiec_web, kenh_zalo, gui_thu; chỉ thay tầng
Frappe và đường gửi. Không gọi thêm hàm nào ngoài chuỗi máy chạy (điều 15).
"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_su_co_290 import D
from vagabond.khung.kiem_thu.thu_dat_ban_web import nd

if "frappe.rate_limiter" not in sys.modules:
	import types as _t
	sys.modules["frappe.rate_limiter"] = _t.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

# Bản Frappe giả chung chưa có get_url khi chạy lẻ tệp này (cùng cách thu_bo_phan_583).
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import dat_ban, gui_thu, kenh_zalo, tiec_web  # noqa: E402

GOC = Path(__file__).resolve().parents[2]


def _fr(ghi):
	"""Frappe giả tối thiểu: ghi lại log_error, cờ trống."""
	def log_error(title=None, message=None, *a, **k):
		ghi.append(("log", title, message))
	return NS(flags=NS(), log_error=log_error,
		utils=NS(get_url_to_form=lambda dt, n: "https://fixture.invalid/app/x/" + n))


def _chay_hook(mod, ham, doc, ket_bao):
	ghi = []
	fr = _fr(ghi)
	goi = []

	def bao(*a, **k):
		goi.append((a, k))
		return ket_bao

	with patch.object(mod, "frappe", fr), patch.object(kenh_zalo, "frappe", fr), \
			patch.object(kenh_zalo, "bao", bao), \
			patch.object(__import__("vagabond"), "diem_ban", NS(theo_ma=lambda ma: {"ten": "Tiệm A"}), create=True), \
			patch.dict(sys.modules, {"vagabond.diem_ban": NS(theo_ma=lambda ma: {"ten": "Tiệm A"})}):
		getattr(mod, ham)(doc)
	return goi, [x for x in ghi if x[0] == "log"]


def _doc(ten, du):
	d = D(name=ten)
	d.as_dict = lambda: dict(du, name=ten)
	return d


@ca("v597 F1 Codex #481: đặt bàn mà Zalo tắt hoặc chưa có nhóm nhận thì có Error Log nêu tên phiếu, có nhóm thì im")
def _dat_ban():
	for ket, mong in ((None, 1), ([], 1), (["Z1"], 0)):
		goi, log = _chay_hook(dat_ban, "bao_dat_ban_moi", _doc("DB-1", nd), ket)
		la("đã gọi đường Zalo (bao=%r)" % (ket,), len(goi), 1)
		la("số Error Log (bao=%r)" % (ket,), len(log), mong)
		if log:
			dung("tiêu đề nói rõ chưa có nhóm nhận", "Zalo" in log[0][1] and "nhóm" in log[0][1])
			dung("nêu tên phiếu để báo tay", "DB-1" in (log[0][2] or ""))
			dung("chỉ chỗ gán nhóm", "Cài đặt lõi" in (log[0][2] or ""))
			dung("không đưa số điện thoại khách vào log", str(nd.get("sdt") or "@@") not in (log[0][2] or ""))


@ca("v597 F1 Codex #481: đăng ký tiệc mà chưa có nhóm Zalo nhận thì có Error Log nêu tên phiếu")
def _tiec():
	du = {"ho_ten": "Khách", "sdt": "0900000000", "so_ve": 2, "trang_thai": "Chờ xác nhận"}
	with patch.object(tiec_web, "soan_tin", lambda d: "ĐĂNG KÝ TIỆC MỚI\nDòng 1"):
		for ket, mong in ((None, 1), ([], 1), (["Z1"], 0)):
			goi, log = _chay_hook(tiec_web, "bao_moi", _doc("TW-1", du), ket)
			la("đã gọi đường Zalo (bao=%r)" % (ket,), len(goi), 1)
			la("số Error Log (bao=%r)" % (ket,), len(log), mong)
			if log:
				dung("nêu tên phiếu", "TW-1" in (log[0][2] or ""))
				dung("không đưa số điện thoại khách vào log", "0900000000" not in (log[0][2] or ""))


@ca("v597 F1: lời Error Log thiếu nhóm là hàm THUẦN, nói đúng loại và chủ đề bằng chữ có dấu")
def _loi_thuan():
	t, m = kenh_zalo.chu_chua_nhom("viec", "dat_ban", "DB-9")
	dung("tiêu đề không quá 140 ký tự (giới hạn ô Error Log)", len(t) <= 140)
	for chu in ("Việc cần làm", "Đặt bàn", "DB-9", "Cài đặt lõi"):
		dung("có " + chu, chu in t + m)
	t2, m2 = kenh_zalo.chu_chua_nhom("canh_bao", "he_thong", None)
	dung("không nguồn thì không ghi chữ None", "None" not in t2 + m2)


def _chay_coi(ket_zalo, co_log_gan_day=False):
	ghi, dau = [], []
	fr = _fr(ghi)
	fr.get_all = lambda *a, **k: [{"name": "Q%d" % i, "error": "SMTP 535 auth"} for i in range(6)]
	fr.db = NS(get_single_value=lambda dt, f: None,
		set_single_value=lambda dt, f, v: dau.append(f),
		commit=lambda: ghi.append(("commit",)),
		exists=lambda dt, flt=None: co_log_gan_day)
	fr.get_traceback = lambda: "TB"
	goi = []

	def bao(*a, **k):
		goi.append((a, k))
		return ket_zalo

	with patch.object(gui_thu, "frappe", fr), patch.object(kenh_zalo, "frappe", fr), \
			patch.object(kenh_zalo, "bao", bao):
		gui_thu.canh_bao_email_loi()
	return goi, dau, [x for x in ghi if x[0] == "log"]


@ca("v597 F2 Codex #481: còi thư chỉ đóng dấu đã hú khi có đường nhận; không đường thì ghi Error Log, giãn 3 giờ")
def _coi():
	# v604: anh Việt 18/10/2026 bỏ email, báo Zalo. Thư dự phòng đã gỡ nên Zalo là
	# đường duy nhất: Zalo không ghi được dòng nào thì không đóng dấu, có Error Log.
	for kz, mong_dau in ((["Z1"], 1), ([], 0), (None, 0)):
		goi, dau, log = _chay_coi(kz)
		la("đã thử Zalo (zalo=%r)" % (kz,), len(goi), 1)
		la("báo đúng tin thư hỏng (zalo=%r)" % (kz,), [k.get("ma_tin") for _, k in goi], ["ht_email_loi"])
		la("đóng dấu đã hú (zalo=%r)" % (kz,), dau.count(gui_thu.TRUONG_LAN_HU), mong_dau)
		if not mong_dau:
			dung("có Error Log hành động được", any("báo động" in (x[1] or "").lower() for x in log))
			dung("Error Log chỉ đúng tin cần tích", any("Email của tiệm không gửi được" in (x[2] or "") for x in log))
	dung("đã gỡ đường thư dự phòng", not hasattr(gui_thu, "_bao_bang_thu"))
	goi, dau, log = _chay_coi([], co_log_gan_day=True)
	la("đã có log trong 3 giờ thì không ghi thêm", [x for x in log if "không có đường" in (x[1] or "")], [])
	la("vẫn không đóng dấu để nhịp sau thử lại", dau, [])


def _chay_trang(kich):
	r = subprocess.run(["node", str(GOC / "khung/kiem_thu/gia_lap_trang.js"), str(GOC / "trang/banh.html"),
		"2026-10-16T08:00:00+07:00", kich], capture_output=True, text=True, timeout=30)
	if r.returncode:
		raise AssertionError(r.stderr[-800:])
	return json.loads(r.stdout)


@ca("v597 F3 Codex #481: khách nhập Số dĩa bã mía thì giỏ và phiếu bếp đều ghi dĩa bã mía, không còn dĩa giấy")
def _dia():
	d = _chay_trang(r"""
const c=CAKES[0]; const s=c.sizes[0]; TODAY[s.id]=5; renderSheet(c); setSize(s.id);
EL('#s-dia').value='2'; EL('#s-nia').value='1'; addToCart();
const gio=EL('#cartList').innerHTML; CART[0].qty=2;
RA({gio, bep:chuDungCu(CART[0])});
""")
	dung("giỏ ghi dĩa bã mía", "2 dĩa bã mía" in d["gio"])
	dung("giỏ không còn dĩa giấy", "dĩa giấy" not in d["gio"])
	la("phiếu bếp nhân số lượng, đúng chất liệu", d["bep"], "2 nĩa gỗ, 4 dĩa bã mía")
	mau = json.loads((GOC / "public/web_order/chu-mac-dinh.json").read_text())
	la("chữ mặc định của giỏ trong sổ nhãn Editor", mau["dung_cu_gio"]["mac_dinh"], "{nia} nĩa gỗ, {dia} dĩa bã mía")
	s = (GOC / "trang/banh.html").read_text()
	la("trang đặt bánh không còn chữ dĩa giấy", s.count("dĩa giấy"), 0)
