# -*- coding: utf-8 -*-
"""v678: Chuyển khoản - Shinhan ở mọi điểm bán, khách tại bàn chuyển khoản ngay
trên điện thoại, tiền về đủ thì hệ thống tự chốt bill (anh Việt 20/11/2026).

Ca chạm hệ chạy HÀM THẬT tu_chot_ck.thu_chot, ck_ban.thong_tin, ck_ban.trang_thai,
ban_hang._kiem_tk_ck (nạp bằng ast vì ban_hang nạp requests ở đầu tệp), chỉ
thay tầng Frappe và mô đun nặng bằng bản giả, để CI tay không vẫn chạy.
"""

import ast
import contextlib
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch

import vagabond
from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

# Bản Frappe giả chung chưa có get_url khi chạy lẻ tệp này (cùng cách thu_tin_zalo_604).
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import ck_ban, ghi_so_dieu_kien, pt_ck, qr_chuyen_khoan, tai_khoan, tu_chot_ck  # noqa: E402
from vagabond import thanh_toan_nhieu as ttn  # noqa: E402
from vagabond import uu_dai_ban as u  # noqa: E402
from vagabond.khung.kiem_thu.thu_uu_dai_ban_643 import _hd  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
BA_MB = "MB-CTY-31561568 - MB Bank"
BA_SH = "SHINHAN-700037279585 - Shinhan Bank"
MA = "TCVQ4PFX"


class _Loi(Exception):
	pass


# ------------------------------------------------------------------ thuần

@ca("v678 phép thuần chuyển khoản: hai phương thức đối soát SePay; mở app ngân hàng đúng khuôn dl.vietqr.io; tiền về Shinhan là phương thức Shinhan; lệch thì báo đúng phương thức")
def _thuan():
	la("hai phương thức", [pt_ck.la_ck(x) for x in ("Chuyển khoản", " Chuyển khoản - Shinhan ", "Thẻ - ShinhanBank", "", None)],
		[True, True, False, False, False])
	la("link app tự điền", pt_ck.link_app("mb", "VQRQ00033k5p6", "mb", 45000.4, "TCV Q4PFX"),
		"https://dl.vietqr.io/pay?app=mb&ba=VQRQ00033k5p6@mb&am=45000&tn=TCV%20Q4PFX")
	la("app có gạch ngang giữ nguyên", pt_ck.link_app("vib-2", "1", "vib", 1, "x").split("&")[0], "https://dl.vietqr.io/pay?app=vib-2")
	la("thiếu số tài khoản, mã ngân hàng hay số tiền: không dựng", [pt_ck.link_app("mb", "", "mb", 1, "x"),
		pt_ck.link_app("mb", "1", "", 1, "x"), pt_ck.link_app("mb", "1", "mb", 0, "x"), pt_ck.link_app("", "1", "mb", 1, "x")], [""] * 4)
	la("mã ngân hàng vietqr", [pt_ck.ma_nh_vietqr(x) for x in ("MB", "shbvn", "XYZ", None)], ["mb", "shbvn", "", ""])
	la("tiền về đâu là phương thức nào", [pt_ck.ck_cua_tk(BA_SH, BA_SH), pt_ck.ck_cua_tk(BA_MB, BA_SH), pt_ck.ck_cua_tk(BA_SH, ""),
		pt_ck.ck_cua_tk("", BA_SH)], ["Chuyển khoản - Shinhan", "Chuyển khoản", "Chuyển khoản", ""])
	la("lệch tài khoản", [pt_ck.soat_tk_ck("Chuyển khoản", [(BA_SH, 1)], BA_SH), pt_ck.soat_tk_ck("Chuyển khoản - Shinhan", [(BA_MB, 1)], BA_SH),
		pt_ck.soat_tk_ck("Chuyển khoản", [(BA_MB, 1)], BA_SH), pt_ck.soat_tk_ck("Chuyển khoản", [], BA_SH),
		pt_ck.soat_tk_ck("Tiền mặt", [(BA_SH, 1)], BA_SH)],
		[("doi", "Chuyển khoản - Shinhan"), ("doi", "Chuyển khoản"), ("", None), ("", None), ("", None)])
	la("năm app tự điền đứng đầu", [a for a, _t, d in pt_ck.APP_NGAN_HANG if d], ["mb", "icb", "bidv", "acb", "ocb"])
	la("tên ngân hàng trên Bank Account ra mã", [tai_khoan.ma_theo_ten_ngan_hang(x) for x in ("Shinhan Bank", "mb bank", "SHBVN", "970424", "Ngân hàng lạ", "")],
		["SHBVN", "MB", "SHBVN", "SHBVN", "", ""])


@ca("v678 một nguồn: bản chép trong ghi_so_dieu_kien trùng pt_ck.DS_CK; bill Shinhan chưa đủ tiền là chờ tiền về; phần cần chuyển khoản cộng cả dòng Shinhan")
def _mot_nguon():
	la("bản chép", tuple(ghi_so_dieu_kien.CHUYEN_KHOAN_DS), pt_ck.DS_CK)
	b = {"docstatus": 0, "vgb_pt_thanh_toan": "Chuyển khoản - Shinhan", "vgb_ma_tham_chieu": "", "sepay_du": 0}
	la("Shinhan chưa đủ tiền", ghi_so_dieu_kien.ly_do(b), "chua_ve_tien")
	la("Shinhan đủ tiền", ghi_so_dieu_kien.ly_do(dict(b, sepay_du=1)), "")
	dong = [{"pt": "Chuyển khoản - Shinhan", "so_tien": 600000}, {"pt": "Tiền mặt", "so_tien": 100000}]
	la("phần cần chuyển khoản có dòng Shinhan", ttn.so_can_ck(dong, 700000), 600000.0)
	dong2 = [{"pt": "Chuyển khoản - Shinhan", "so_tien": 300000}, {"pt": "Chuyển khoản", "so_tien": 400000}]
	la("hai dòng chuyển khoản cộng lại", ttn.so_can_ck(dong2, 700000), 700000.0)


# Không còn chỗ nào so chữ "Chuyển khoản" trần ở luồng bill quầy (sổ mẫu lỗi loại 3).
_TEP_SO = ["vagabond/ban_hang.py", "vagabond/doi_soat_ck.py", "vagabond/bao_cao.py", "vagabond/ghi_so_dieu_kien.py",
	"vagabond/thanh_toan_nhieu.py", "vagabond/public/js/bep/08-doanh-so-sales.js", "vagabond/public/js/bep/09-tinh-tien-quay.js",
	"vagabond/public/js/bep/10-bill-quay.js", "vagabond/public/js/bep/25-man-hinh-khach.js"]
_MAU_SO = re.compile(r"""(?:[!=]==?\s*['"]Chuyển khoản['"])|(?:['"]Chuyển khoản['"]\s*[!=]==?)|(?:"vgb_pt_thanh_toan":\s*"Chuyển khoản")"""
	r"""|(?:get\(CHUYEN_KHOAN\))|(?:pt\s*==\s*CHUYEN_KHOAN\b)""")


def so_chu_tran(s):
	"""Các dòng còn so chữ "Chuyển khoản" trần. THUẦN, để ca kiểm chạy được trên chuỗi mẫu."""
	return [d.strip() for d in s.splitlines() if _MAU_SO.search(d)]


@ca("v678 không còn chỗ nào ở luồng bill quầy tự so chữ Chuyển khoản: mọi chỗ qua pt_ck.la_ck hay posLaCk")
def _khong_so_chu():
	la("mẫu dò bắt đúng chỗ so", [bool(so_chu_tran(x)) for x in ("if pt == \"Chuyển khoản\":", "x !== 'Chuyển khoản'",
		"'Chuyển khoản' === y", "\"vgb_pt_thanh_toan\": \"Chuyển khoản\",", "if pt in CHUYEN_KHOAN_DS:", "posLaCk(pt)", "x.get(CHUYEN_KHOAN)")],
		[True, True, True, True, False, False, True])
	for p in _TEP_SO:
		la(p + " không so chữ trần", so_chu_tran((GOC / p).read_text()), [])
	j = (GOC / "vagabond/public/js/bep/09-tinh-tien-quay.js").read_text()
	dung("màn tính tiền đọc danh sách từ máy chủ", "posCfgCk().pt_ck" in j and "posCfgCk().qr_pt" in j)
	b = (GOC / "vagabond/ban_hang.py").read_text()
	dung("máy chủ gửi danh sách và tài khoản QR", '"pt_ck": list(pt_ck.DS_CK)' in b and '"qr_pt": pt_thanh_toan.qr_pt()' in b)


@ca("v678 phương thức Shinhan: khai trong mã nguồn ngay sau Chuyển khoản, logo Shinhan, ở quầy, tên khoá; nâng cấp site đã lưu thì đứng cạnh Chuyển khoản, không đổi số dòng khác")
def _pt_thanh_toan():
	from vagabond import pt_thanh_toan as p

	ten = [d["ten"] for d in p.MAC_DINH]
	la("đứng sau Chuyển khoản", ten[ten.index("Chuyển khoản") + 1], "Chuyển khoản - Shinhan")
	d = p._chuan(next(x for x in p.MAC_DINH if x["ten"] == "Chuyển khoản - Shinhan"))
	la("cấu hình", (d["lg"], d["quay"], d["online"], d["tien_ve"], d["minvoice"], d["bat"]),
		("/files/pt-shinhan5.png", 1, 0, "ngay", "CK", 0))
	dung("tên khoá", "Chuyển khoản - Shinhan" in p.TEN_KHOA)
	dang = [p._chuan(x, i) for i, x in enumerate(p.MAC_DINH) if x["ten"] != "Chuyển khoản - Shinhan"]
	for i, x in enumerate(dang):
		x["thu_tu"] = (i + 1) * 10
	import json
	luu = {}
	with patch.object(p, "cfg_o", return_value=json.dumps(dang, ensure_ascii=False)), \
			patch.object(p, "_mo_loi_next", lambda ra: None), patch.object(p, "_ghi_vet", lambda v: None), \
			patch.object(_fr.db, "set_single_value", lambda dt, o, gt: luu.update(gt=gt), create=True):
		la("thêm một", p.bo_sung_mac_dinh(), 1)
	moi = json.loads(luu["gt"])
	ck = {x["ten"]: x["thu_tu"] for x in moi}
	la("cùng số thứ tự với Chuyển khoản", ck["Chuyển khoản - Shinhan"], ck["Chuyển khoản"])
	la("dòng cũ giữ số", [x["thu_tu"] for x in moi if x["ten"] != "Chuyển khoản - Shinhan"], [x["thu_tu"] for x in dang])
	sap = sorted(moi, key=lambda x: (x["thu_tu"], x["ten"]))
	la("hiện ngay sau Chuyển khoản", [x["ten"] for x in sap][[x["ten"] for x in sap].index("Chuyển khoản") + 1], "Chuyển khoản - Shinhan")


@ca("v678 tự chốt thuần: đọc mã bill trong nội dung; chỉ chốt bill tạm tính đủ tiền, một ngân hàng, chưa chia dòng, sao kê chưa có chủ")
def _tu_chot_thuan():
	la("mã trong nội dung", tu_chot_ck.ma_trong_mo_ta("NGUYEN VAN A chuyen tien TCV Q4PFX tcvq4pfx TCVQ4PFX FT2611"), ["TCVQ4PFX"])
	la("hai mã", tu_chot_ck.ma_trong_mo_ta("TCVQ4PFX NVHAC3DE"), ["TCVQ4PFX", "NVHAC3DE"])
	b = {"docstatus": 0, "vgb_tam_tinh": 1, "vgb_huy": 0, "grand_total": 180000}
	mot = {"Chuyển khoản"}
	la("đủ điều kiện", tu_chot_ck.ly_do_khong_chot(b, 180000, 0, mot, False), "")
	la("sai số một đồng", tu_chot_ck.ly_do_khong_chot(b, 179999.5, 0, mot, False), "")
	la("các lý do", [tu_chot_ck.ly_do_khong_chot(dict(b, docstatus=1), 9e9, 0, mot, False),
		tu_chot_ck.ly_do_khong_chot(dict(b, vgb_huy=1), 9e9, 0, mot, False),
		tu_chot_ck.ly_do_khong_chot(dict(b, vgb_tam_tinh=0), 9e9, 0, mot, False),
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 2, mot, False),
		tu_chot_ck.ly_do_khong_chot(dict(b, grand_total=0), 9e9, 0, mot, False),
		tu_chot_ck.ly_do_khong_chot(b, 100000, 0, mot, False),
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 0, mot, True),
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 0, {"Chuyển khoản", "Chuyển khoản - Shinhan"}, False),
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 0, set(), False),
		# Codex #597 vòng 1 (quét cùng loại): một giao dịch thiếu tài khoản thì không tự chốt.
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 0, {"Chuyển khoản", ""}, False),
		tu_chot_ck.ly_do_khong_chot(b, 9e9, 0, {""}, False)],
		["khong_mo", "khong_mo", "da_chot", "chia_dong", "khong_tien", "chua_du", "gd_co_chu", "nhieu_tk", "nhieu_tk",
			"nhieu_tk", "nhieu_tk"])
	dung("ghi chú không tên người, có giao dịch", tu_chot_ck.ghi_chu_chot(180000, ["ACC-BTN-1"], "10:05")
		== "Hệ thống tự chốt lúc 10:05: ngân hàng nhận đủ 180.000 đ (giao dịch ACC-BTN-1).")


# ------------------------------------------------------------ chạm hệ

@contextlib.contextmanager
def _chot_gia(si, nhan=None, gd=("ACC-BTN-1",), tk=(BA_MB,), chu=None, dong=(), ud_doi=False, pt_nguon=None):
	"""Hệ giả quanh tu_chot_ck.thu_chot: bill si, SePay nhận `nhan` cho mã bill
	qua các dòng gd ở các tài khoản tk."""
	vet = {"khoa": [], "chot": [], "zalo": [], "sau": [], "commit": 0}
	bh = types.ModuleType("vagabond.ban_hang")
	bh._sepay_bill = lambda ma: ({"nhan": si.grand_total if nhan is None else nhan, "gd": list(gd)} if ma == MA else {})
	bh._pt_cho_nguon = lambda n: pt_nguon if pt_nguon is not None else ["Tiền mặt", "Chuyển khoản", "Chuyển khoản - Shinhan"]
	bh._ghi_vet = lambda n, v, c: vet["chot"].append(v)
	dss = types.ModuleType("vagabond.doi_soat_sepay")
	dss.chu_cua_giao_dich = lambda ds, bo_qua_hoa_don=None: dict(chu or {})
	ptt = types.ModuleType("vagabond.pt_thanh_toan")
	ptt.ba_shinhan = lambda: BA_SH
	trtk = types.ModuleType("vagabond.tra_truoc_khach")

	def chon(doc, pt, ha_co_may=True, doi_pt=False):
		doc.vgb_pt_thanh_toan = pt
	trtk.chon_pt_ca_don = chon

	def get_doc(dt, n, for_update=False):
		vet["khoa"].append(for_update)
		return si

	def truoc(s, giam_tay=None):
		if ud_doi:
			raise u.UuDaiDoi("đổi")
		return None
	with patch.dict(sys.modules, {"vagabond.ban_hang": bh, "vagabond.doi_soat_sepay": dss, "vagabond.pt_thanh_toan": ptt,
			"vagabond.tra_truoc_khach": trtk}), \
			patch.object(vagabond, "ban_hang", bh, create=True), patch.object(vagabond, "doi_soat_sepay", dss, create=True), \
			patch.object(vagabond, "pt_thanh_toan", ptt, create=True), patch.object(vagabond, "tra_truoc_khach", trtk, create=True), \
			patch.object(_fr, "get_doc", side_effect=get_doc), \
			patch.object(_fr.db, "sql", side_effect=lambda q, p=None, **k: [(b,) for b in tk], create=True), \
			patch.object(_fr.db, "commit", lambda: vet.__setitem__("commit", vet["commit"] + 1), create=True), \
			patch.object(ttn, "dong_cua", lambda n: list(dong)), \
			patch.object(u, "truoc_chot", side_effect=truoc), \
			patch.object(u, "sau_chot", side_effect=lambda s, kq: vet["sau"].append(kq)), \
			patch.object(tu_chot_ck, "_bao_quay", side_effect=lambda s, pt: vet["zalo"].append(pt)), \
			patch.object(_fr, "session", _fr._dict(user="Guest"), create=True), \
			patch.object(_fr, "set_user", lambda nd: setattr(_fr.session, "user", nd), create=True):
		yield vet


@ca("v678 tự chốt (tu_chot_ck.thu_chot thật): khoá bill trước khi đọc; tiền MB đủ thì chốt Chuyển khoản, mã tham chiếu là mã bill, bỏ tạm tính, ghi chú, lưu bằng quyền hệ thống, báo quầy; tiền về Shinhan thì chốt Chuyển khoản - Shinhan")
def _tu_chot():
	si = _hd(custom_pancake_display_id=MA, vgb_ghi_chu_doi_soat="")
	goc = _fr.session.user
	with _chot_gia(si) as vet:
		r = tu_chot_ck.thu_chot(si.name)
		trong = _fr.session.user
	la("chốt", (r["ok"], r["pt"]), (1, "Chuyển khoản"))
	la("đọc bill có khoá", vet["khoa"], [True])
	la("bill sau chốt", (si.vgb_pt_thanh_toan, si.vgb_ma_tham_chieu, si.vgb_tam_tinh, si.luu), ("Chuyển khoản", MA, 0, 1))
	dung("ghi chú đối soát", si.vgb_ghi_chu_doi_soat.startswith("Hệ thống tự chốt lúc") and "ACC-BTN-1" in si.vgb_ghi_chu_doi_soat)
	la("lưu bằng quyền hệ thống, trả lại khách (Guest)", (si.luu_boi, trong, _fr.session.user), ("Administrator", "Guest", goc))
	la("ghi vết, báo quầy, ghi lượt ưu đãi, commit", (len(vet["chot"]), vet["zalo"], vet["sau"], vet["commit"]), (1, ["Chuyển khoản"], [None], 1))
	si2 = _hd(custom_pancake_display_id=MA)
	with _chot_gia(si2, tk=(BA_SH,)) as vet:
		r = tu_chot_ck.thu_chot(si2.name)
	la("tiền về Shinhan", (r["pt"], si2.vgb_pt_thanh_toan, vet["zalo"]), ("Chuyển khoản - Shinhan", "Chuyển khoản - Shinhan", ["Chuyển khoản - Shinhan"]))


@ca("v678 tự chốt KHÔNG chốt: chưa đủ tiền, hai ngân hàng, đã chia dòng, sao kê có chủ, bill đã chốt, mã lạ, phương thức không mở cho nguồn, ưu đãi đổi số; không lưu, không báo")
def _tu_chot_chan():
	kq = []
	for k in ({"nhan": 100000}, {"tk": (BA_MB, BA_SH)}, {"dong": [{"pt": "Tiền mặt", "so_tien": 1}]},
			{"chu": {"ACC-BTN-1": "Phiếu thu PT-1"}}, {"ud_doi": True}, {"pt_nguon": ["Tiền mặt"]}):
		si = _hd(custom_pancake_display_id=MA)
		with _chot_gia(si, **k) as vet:
			r = tu_chot_ck.thu_chot(si.name)
		kq.append((r["ly_do"], si.luu, si.vgb_tam_tinh, vet["zalo"]))
	la("các ca", kq, [("chua_du", 0, 1, []), ("nhieu_tk", 0, 1, []), ("chia_dong", 0, 1, []), ("gd_co_chu", 0, 1, []),
		("ud_doi", 0, 1, []), ("pt_sai_nguon", 0, 1, [])])
	si = _hd(custom_pancake_display_id=MA, vgb_tam_tinh=0, vgb_pt_thanh_toan="Tiền mặt")
	with _chot_gia(si):
		la("bill đã chốt bằng tiền mặt: không đổi", (tu_chot_ck.thu_chot(si.name)["ly_do"], si.vgb_pt_thanh_toan, si.luu), ("da_chot", "Tiền mặt", 0))
	si = _hd(custom_pancake_display_id="HDB-1")
	with _chot_gia(si):
		la("mã không phải mã bill", tu_chot_ck.thu_chot(si.name)["ly_do"], "khong_ma")


@ca("v678 webhook SePay: tiền vào có mã bill thì xếp đúng một việc tự chốt mỗi mã sau commit; tiền ra, không mã thì không xếp; lỗi không ném ra webhook")
def _webhook():
	xep = []
	g = {"deposit": 180000, "description": "chuyen tien TCVQ4PFX", "reference_number": "FT1"}
	with patch.object(_fr.db, "get_value", side_effect=lambda *a, **k: g, create=True), \
			patch.object(_fr, "enqueue", side_effect=lambda f, **k: xep.append((f, k["ma"], k["job_id"], k["enqueue_after_commit"])), create=True):
		la("xếp việc", tu_chot_ck.khi_co_giao_dich("ACC-BTN-1"), [MA])
		g.update(deposit=0, withdrawal=5)
		la("tiền ra không xếp", tu_chot_ck.khi_co_giao_dich("ACC-BTN-2"), [])
		g.update(deposit=10, description="khong co ma")
		la("không mã không xếp", tu_chot_ck.khi_co_giao_dich("ACC-BTN-3"), [])
	la("một việc, sau commit, chống trùng theo mã", xep, [("vagabond.tu_chot_ck.chot_theo_ma", MA, "tu_chot_ck:" + MA, True)])
	with patch.object(_fr.db, "get_value", side_effect=RuntimeError("hỏng"), create=True):
		la("lỗi không ném", tu_chot_ck.khi_co_giao_dich("ACC-BTN-4"), [])
	s = (GOC / "vagabond/sepay.py").read_text()
	dung("webhook gọi sau khi ghi sao kê", s.index("tu_chot_ck.khi_co_giao_dich(bt.name)") > s.index("bt.submit()"))
	n = (GOC / "vagabond/nhap_sao_ke.py").read_text()
	dung("nạp bù sao kê tay không tự chốt", "tu_chot_ck" not in n)


@ca("v678 cửa ghi sổ: bill ghi Chuyển khoản mà tiền về Shinhan (hay ngược lại) thì chặn, câu chỉ đổi phương thức; khớp thì qua (ban_hang._kiem_tk_ck thật)")
def _kiem_tk_ck():
	src = (GOC / "vagabond/ban_hang.py").read_text()
	cay = ast.parse(src)
	fn = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_kiem_tk_ck")
	m = ast.Module(body=[fn], type_ignores=[])
	from vagabond import chiem_sao_ke

	ptt = types.SimpleNamespace(ba_shinhan=lambda: BA_SH)
	g = {"frappe": _fr, "chiem_sao_ke": chiem_sao_ke, "pt_ck": pt_ck, "pt_thanh_toan": ptt, "flt": _fr.utils.flt}
	exec(compile(m, "ban_hang._kiem_tk_ck", "exec"), g)
	kiem = g["_kiem_tk_ck"]
	si = _hd(custom_pancake_display_id=MA)
	loi = []
	for pt, tk in (("Chuyển khoản", BA_SH), ("Chuyển khoản - Shinhan", BA_MB), ("Chuyển khoản", BA_MB), ("Chuyển khoản - Shinhan", BA_SH)):
		with patch.object(_fr.db, "sql", side_effect=lambda q, p=None, **k: [(tk, 100000)], create=True), \
				patch.object(ttn, "dong_cua", lambda n: []):
			try:
				kiem(si, pt, ["ACC-BTN-1"])
				loi.append("")
			except _fr.ValidationError as e:
				loi.append(str(e))
	dung("MB ghi mà tiền về Shinhan: chặn " + loi[0], "đổi phương thức thanh toán sang Chuyển khoản - Shinhan" in loi[0] and MA in loi[0])
	dung("Shinhan ghi mà tiền về MB: chặn", "sang Chuyển khoản rồi" in loi[1])
	la("khớp thì qua", loi[2:], ["", ""])
	with patch.object(_fr.db, "sql", side_effect=AssertionError("không được đọc")):
		kiem(si, "Chuyển khoản", [])
	dung("cửa ghi sổ quầy gọi kiểm trước khi chiếm giao dịch",
		src.index("_kiem_tk_ck(si, pt, g.get(\"gd\") or [])") < src.index("_chiem_gd_bill(si, g.get(\"gd\") or [])"))


@contextlib.contextmanager
def _khach_ban(si, link=True):
	from vagabond import goi_mon_ban

	with patch.object(goi_mon_ban, "_kiem_link", return_value=({"ma": "TCV", "ten": "District 1"}, "5") if link else (None, None)), \
			patch.object(u, "_hoa_don_ban", side_effect=lambda d, n, khoa=False: si), \
			patch.object(ttn, "dong_cua", lambda n: []), \
			patch.object(_fr, "session", _fr._dict(user="Guest"), create=True), \
			patch.object(_fr, "set_user", lambda nd: setattr(_fr.session, "user", nd), create=True):
		yield


@ca("v678 khách lấy thông tin chuyển khoản (ck_ban.thong_tin thật): số tiền hoá đơn bàn, tài khoản của điểm, nội dung là mã bill, ảnh QR dựng tại máy chủ, nút app; link sai, chưa có hoá đơn, chia dòng thì báo")
def _thong_tin():
	si = _hd(custom_pancake_display_id=MA)
	tk = {"bank": "MB", "bin": "970422", "stk": "VQRQ00033k5p6", "ten": "PATISSERIE VAGABOND", "rieng": 1}
	anh = []
	with _khach_ban(si), patch.object(tai_khoan, "tk_cho", side_effect=lambda n, d: (anh.append(("tk", n, d)), tk)[1]), \
			patch.object(qr_chuyen_khoan, "anh_qr", side_effect=lambda t, tien, nd: (anh.append((t["stk"], tien, nd)), "data:image/svg+xml,x")[1]):
		r = ck_ban.thong_tin("TCV", 5, "k")
	la("thông tin", (r["ok"], r["ma"], r["tien"], r["noi_dung"], r["ngan_hang"], r["stk"]), (1, MA, 185000, MA, "MB Bank", "VQRQ00033k5p6"))
	la("tài khoản theo nguồn và điểm của bill; ảnh QR dựng tại máy chủ đúng số và nội dung", (anh, r["anh"]),
		([("tk", si.custom_nguon, "TCV"), ("VQRQ00033k5p6", 185000, MA)], "data:image/svg+xml,x"))
	la("nút app đầu", r["app"][0], {"ma": "mb", "ten": "MB Bank", "tu_dien": 1,
		"link": "https://dl.vietqr.io/pay?app=mb&ba=VQRQ00033k5p6@mb&am=185000&tn=" + MA})
	dung("không lộ tên hoá đơn nội bộ", si.name not in str(r))
	with _khach_ban(si, link=False):
		dung("link sai", ck_ban.thong_tin("TCV", 5, "x")["ok"] == 0)
	with _khach_ban(None):
		dung("chưa có hoá đơn", "chờ quầy nhận món" in ck_ban.thong_tin("TCV", 5, "k")["cau"])
	with _khach_ban(si), patch.object(ttn, "dong_cua", lambda n: [{"pt": "Tiền mặt"}]):
		dung("chia dòng", "chia nhiều cách trả" in ck_ban.thong_tin("TCV", 5, "k")["cau"])
	la("nội dung cùng luật màn tính tiền", [ck_ban.noi_dung_ck(MA, "TCV", 0), ck_ban.noi_dung_ck("VGBACDEF", "TCV", 0),
		ck_ban.noi_dung_ck("VGBACDEF", "TCV", 1), ck_ban.noi_dung_ck("", "TCV", 0)], [MA, "TCV VGBACDEF", "VGBACDEF", ""])


@ca("v678 khách hỏi tiền đã về (ck_ban.trang_thai thật): bill còn tạm tính thì thử tự chốt; chốt được là đã trả; quầy chốt cách khác, huỷ; số tiền mới khi chờ; mã lạ thì không trả gì")
def _trang_thai():
	hang = {}

	def gv(dt, loc, f=None, as_dict=False):
		if f == "grand_total":
			return hang.get("tong", 0)
		return hang.get("r")
	goi = []
	with _khach_ban(None), patch.object(_fr.db, "get_value", side_effect=gv, create=True), \
			patch.object(tu_chot_ck, "thu_chot", side_effect=lambda n: (goi.append((n, _fr.session.user)), hang.get("kq"))[1]):
		hang.update(r=_fr._dict(name="ACC-SINV-1", docstatus=0, vgb_tam_tinh=1, vgb_huy=0, vgb_pt_thanh_toan=""), kq={"ok": 0}, tong=75000)
		la("chờ, kèm số tiền mới", ck_ban.trang_thai("TCV", 5, "k", MA), {"ok": 1, "tt": "cho", "tien": 75000})
		la("thử chốt bằng quyền hệ thống", goi, [("ACC-SINV-1", "Administrator")])
		hang.update(kq={"ok": 1})
		la("vừa tự chốt", ck_ban.trang_thai("TCV", 5, "k", MA), {"ok": 1, "tt": "da_tra"})
		hang.update(r=_fr._dict(name="ACC-SINV-1", docstatus=0, vgb_tam_tinh=0, vgb_huy=0, vgb_pt_thanh_toan="Tiền mặt"))
		la("quầy chốt tiền mặt", ck_ban.trang_thai("TCV", 5, "k", MA), {"ok": 1, "tt": "da_chot"})
		hang.update(r=_fr._dict(name="ACC-SINV-1", docstatus=1, vgb_tam_tinh=0, vgb_huy=0, vgb_pt_thanh_toan="Chuyển khoản - Shinhan"))
		la("đã chốt chuyển khoản", ck_ban.trang_thai("TCV", 5, "k", MA), {"ok": 1, "tt": "da_tra"})
		hang.update(r=_fr._dict(name="ACC-SINV-1", docstatus=0, vgb_tam_tinh=1, vgb_huy=1, vgb_pt_thanh_toan=""))
		la("huỷ", ck_ban.trang_thai("TCV", 5, "k", MA), {"ok": 1, "tt": "huy"})
		la("chỉ thử chốt khi còn tạm tính", len(goi), 2)
		la("mã lạ", ck_ban.trang_thai("TCV", 5, "k", "HDB-26-1"), {"ok": 0})
	with _khach_ban(None, link=False):
		la("link sai", ck_ban.trang_thai("TCV", 5, "x", MA), {"ok": 0})


@ca("v678 tin Zalo bàn đã chuyển khoản: có trong danh mục, mốc tin gọi món tại bàn, bản sao màn Cài đặt trùng chữ, bản vá tích theo mốc; tin không có số tiền")
def _tin():
	from vagabond import kenh_zalo

	la("danh mục", kenh_zalo.TIN["bh_ban_da_chuyen_khoan"][:2], ("Bán hàng, cửa hàng", "Bàn đã chuyển khoản, bill tự chốt"))
	la("mốc", kenh_zalo.TIN_MOC["bh_ban_da_chuyen_khoan"], "bh_goi_mon_tai_ban")
	j = (GOC / "vagabond/public/js/cai_dat_loi_chung.js").read_text()
	dung("bản sao màn Cài đặt", "bh_ban_da_chuyen_khoan: ['Bán hàng, cửa hàng', 'Bàn đã chuyển khoản, bill tự chốt', '"
		+ kenh_zalo.TIN["bh_ban_da_chuyen_khoan"][2] + "']" in j)
	p = (GOC / "vagabond/patches.txt").read_text()
	dung("bản vá có trong patches.txt", "vagabond.patches.v678_tin_chuyen_khoan" in p)
	s = (GOC / "vagabond/tu_chot_ck.py").read_text()
	fn = s[s.index("def _bao_quay"):]
	dung("tin không mang số tiền", "nhan" not in fn.split("kenh_zalo.bao")[0].replace("Ngân hàng đã nhận đủ", ""))


# ------------------------------------------- khuyến mãi trên bill tạm tính (v678)
# Dễ báo 20/11/2026: bill gọi QR không có mục Chương trình, Nhập mã; ra quầy
# Sửa hoá đơn cũng không có. Quầy áp đi chung đường ưu đãi tại bàn (v643).

from vagabond import khuyen_mai  # noqa: E402
from vagabond.khung.kiem_thu.nen import nem  # noqa: E402
from vagabond.khung.kiem_thu.thu_uu_dai_ban_643 import CTKM, _nap_pos_chot, _nem_dung_lop, km_gia  # noqa: E402


@contextlib.contextmanager
def _quay(si, sep=False, otp_dung="123456", muc="tu_do"):
	"""Thu ngân trên màn bill: get_doc trả hoá đơn giả, ban_hang giả có cổng
	quyền, OTP; khuyến mãi giả của ca 643 (CTKM-10 giảm 10%, CTKM-OTP cần OTP)."""
	def otp_kiem(otp, viec=""):
		if sep:
			return "quản lý sep@vgb"
		if str(otp or "") != otp_dung:
			raise _fr.ValidationError("Mã OTP không đúng hoặc đã hết hạn.")
		return "OTP"

	def ma_hay_ctkm(items, ctkm=None, ma=None, **k):
		if ma == "VC-QUAY":
			ma, ctkm = None, ["CTKM-10"]
		if "CTKM-OTP" in (ctkm or []):
			ma = "VC-OTP"
		return km_gia(items, ctkm=ctkm, ma=ma, **k)

	bh = types.SimpleNamespace(_kiem_quyen_ban=lambda: None, _otp_la_sep=lambda: sep, _otp_kiem=otp_kiem)
	tdb = types.SimpleNamespace(_la_gop=lambda kh: not kh or kh.startswith("Khách lẻ"))
	ds = {"km": [dict(c, dung_duoc=1, ly_do="") for c in CTKM if c.name in ("CTKM-10", "CTKM-OTP", "CTKM-MA")]
		+ [dict(name="CTKM-HET", ten="Giảm 15% hoá đơn từ 1.000.000 đ", cach_ma="Khong can ma", can_otp=0, dung_duoc=0,
			ly_do="hoá đơn chưa đủ 1.000.000 đ")]}
	with patch.dict(sys.modules, {"vagabond.ban_hang": bh, "vagabond.tich_diem_ban": tdb}), \
			patch.object(vagabond, "ban_hang", bh, create=True), patch.object(vagabond, "tich_diem_ban", tdb, create=True), \
			patch.object(_fr, "get_doc", return_value=si), \
			patch.object(_fr.db, "get_value", return_value="0909000111"), \
			patch.object(_fr.db, "commit", lambda: None), \
			patch.object(khuyen_mai, "ds_ctkm", return_value=ds), \
			patch.object(khuyen_mai, "tinh", side_effect=ma_hay_ctkm), \
			patch.object(khuyen_mai, "tinh_co_khoa", side_effect=ma_hay_ctkm), \
			patch.object(vagabond.quyen_quay, "muc", return_value=muc), \
			patch.object(_fr, "session", _fr._dict(user="thungan@vgb"), create=True):
		yield


@ca("v678 phép thuần quầy áp khuyến mãi: chỉ bill nháp chưa huỷ, chưa có khuyến mãi lúc tạo, chưa có ưu đãi khác; OTP quầy đã nhập thì chương trình cần OTP vẫn trừ")
def _ap_quay_thuan():
	la("bill tạm tính trống: được", u.chan_ap_quay(_hd()), "")
	la("đã ghi sổ", "đã ghi sổ" in u.chan_ap_quay(_hd(docstatus=1)), True)
	la("đã huỷ", "huỷ" in u.chan_ap_quay(_hd(vgb_huy=1)), True)
	la("có khuyến mãi lúc tạo", "lúc tạo đơn" in u.chan_ap_quay(_hd(vgb_km='[{"ten":"X"}]')), True)
	la("vgb_km rỗng dạng [] vẫn được", u.chan_ap_quay(_hd(vgb_km="[]")), "")
	la("đã có ưu đãi khách chọn", "Bỏ ưu đãi" in u.chan_ap_quay(_hd(vgb_ud_ban='{"loai":"ma","ma":"VC-8K2Q","ten":"Giảm 10%"}')), True)
	kq = {"tong_hd": 300000, "ap": [{"loai": "ctkm", "giam": 90000, "can_otp": 1}]}
	la("cần OTP, chưa nhập: 0", u.giam_tu_kq(kq)[0], 0)
	la("quầy đã nhập OTP: trừ", u.giam_tu_kq(kq, cho_otp=True), (90000.0, ""))


@ca("v678 quầy áp chương trình trên bill gọi QR (uu_dai_ban.ap_quay thật): trừ ngay, ghi cách duyệt, khách không đè được; chốt bill ghi lượt với cách duyệt của quầy")
def _ap_quay_that():
	si = _hd()
	with _quay(si):
		r = u.ds_quay(si.name)
		la("danh sách: có giảm dự kiến, chương trình chưa đủ điều kiện xếp cuối", [(x["ma"], x["dung_duoc"]) for x in r["ds"]][-1], ("CTKM-HET", 0))
		la("CTKM-10 dự kiến 18.500 đ", [x["giam"] for x in r["ds"] if x["ma"] == "CTKM-10"], [18500])
		r = u.ap_quay(si.name, "ctkm", "CTKM-10")
	la("áp xong", (r["ok"], r["giam"], si.vgb_giam_ud, si.grand_total), (1, 18500, 18500.0, 166500.0))
	ud = u.doc_ud(si.vgb_ud_ban)
	la("ghi cách duyệt quầy, người áp", (ud["cach"], ud["nguoi"], ud.get("otp")), (u.CACH_QUAY, "thungan@vgb", None))
	la("lịch sử hoá đơn có dòng áp", any("Quầy áp khuyến mãi" in c for c in si.ghi_chu), True)
	with _quay(si):
		r2 = u.ap_quay(si.name, "ctkm", "CTKM-10")
	la("áp lần hai: chặn, không trừ chồng", (r2["ok"], si.vgb_giam_ud), (0, 18500.0))
	# Khách đăng nhập Zalo trên trang bàn không đè, không bỏ được khuyến mãi quầy
	# áp, kể cả khi chính là khách đứng tên bill (cùng số): chỉ cửa "quầy áp" chặn.
	from vagabond.khung.kiem_thu.thu_uu_dai_ban_643 import KHACH, SDT, _ban
	sk = _hd(customer=KHACH)
	tdb = types.SimpleNamespace(_la_gop=lambda kh: not kh)
	with _quay(sk), patch.object(_fr.db, "get_value", return_value=SDT):
		u.ap_quay(sk.name, "ctkm", "CTKM-10")
	la("quầy áp cho bill đứng tên khách", (u.doc_ud(sk.vgb_ud_ban)["sdt"], sk.vgb_giam_ud > 0), (SDT, True))
	giam_quay = sk.vgb_giam_ud
	with _ban(sk), patch.dict(sys.modules, {"vagabond.tich_diem_ban": tdb}), patch.object(vagabond, "tich_diem_ban", tdb, create=True):
		r3 = u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
		r4 = u.bo("TCV", 5, "k")
	la("khách không đè, không bỏ", (r3["ok"], r4["ok"], sk.vgb_giam_ud, u.doc_ud(sk.vgb_ud_ban)["cach"]), (0, 0, giam_quay, u.CACH_QUAY))
	s0 = _hd()
	with _quay(s0):
		r5 = u.ap_quay(s0.name, "ctkm", "CTKM-MA")
	la("chương trình không giảm gì: báo, không ghi", (r5["ok"], s0.vgb_ud_ban, s0.luu), (0, "", 0))

	bh = _nap_pos_chot()
	ghi = []
	with _quay(si), patch.object(bh, "_pos_lay", return_value=si), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda kq, ten, **k: ghi.append((kq, k))), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, ten, f, v, **k: si.__setitem__(f, v)), \
			patch.object(vagabond.quyen_quay, "muc", return_value="duyet"), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		bh.pos_chot(si.name)
	la("chốt: thu đúng, ghi lượt theo cách quầy", (si.grand_total, si.vgb_tam_tinh, ghi[0][1]["cach_duyet"], ghi[0][1]["ghi_chu"]),
		(166500.0, 0, u.CACH_QUAY, "Bàn 5"))


@ca("Codex PR #597 vòng 3 (loại 4, 7): bill đã chốt (hết tạm tính) thì quầy không áp, không bỏ ưu đãi được; quyền quầy gioi_han, duyet bắt OTP khi áp lên bill tạm tính, tu_do thì không")
def _codex597_v3_ap_quay():
	la("phép thuần: hết tạm tính thì chặn", "đã chốt" in u.chan_ap_quay(_hd(vgb_tam_tinh=0)), True)
	si = _hd(vgb_tam_tinh=0)
	with _quay(si):
		r = u.ap_quay(si.name, "ma", "VC-QUAY")
	la("sheet cũ áp sau khi bill đã chốt: từ chối, không trừ", (r["ok"], si.vgb_giam_ud, si.luu), (0, 0, 0))
	sb = _hd()
	with _quay(sb):
		u.ap_quay(sb.name, "ctkm", "CTKM-10")
	sb["vgb_tam_tinh"] = 0
	with _quay(sb):
		nem("bỏ ưu đãi sau khi bill đã chốt: chặn", lambda: u.bo_quay(sb.name, "khách đổi ý"), _fr.ValidationError)
	la("bỏ bị chặn: ưu đãi còn nguyên", sb.vgb_giam_ud, 18500.0)
	for muc in ("duyet", "gioi_han"):
		s1 = _hd()
		with _quay(s1, muc=muc):
			r = u.ap_quay(s1.name, "ctkm", "CTKM-10")
			la(muc + ": chương trình thường, thiếu OTP: hỏi, chưa trừ", (r["ok"], r.get("can_otp"), "quản lý ca" in r["cau"], s1.vgb_giam_ud), (0, 1, True, 0))
			nem(muc + ": OTP sai: chặn", lambda: u.ap_quay(s1.name, "ctkm", "CTKM-10", otp="000000"), _fr.ValidationError)
			r = u.ap_quay(s1.name, "ctkm", "CTKM-10", otp="123456")
		la(muc + ": OTP đúng: trừ, ghi OTP", (r["ok"], s1.vgb_giam_ud, u.doc_ud(s1.vgb_ud_ban)["cach"]), (1, 18500.0, u.CACH_QUAY + " (OTP)"))
	s2 = _hd()
	with _quay(s2, sep=True, muc="duyet"):
		r = u.ap_quay(s2.name, "ctkm", "CTKM-10")
	la("duyet: quản lý tự áp khỏi OTP", (r["ok"], s2.vgb_giam_ud), (1, 18500.0))
	s3 = _hd()
	with _quay(s3, muc="tu_do"):
		r = u.ap_quay(s3.name, "ctkm", "CTKM-10")
	la("tu_do: thu ngân áp không cần OTP", (r["ok"], s3.vgb_giam_ud), (1, 18500.0))


@ca("v678 quầy nhập mã và chương trình cần OTP: thiếu OTP thì hỏi, OTP sai thì chặn, đúng thì trừ và GIỮ khi gọi thêm món hay chốt (không về 0 vì cờ OTP)")
def _ap_quay_otp():
	si = _hd()
	with _quay(si):
		r = u.ap_quay(si.name, "ctkm", "CTKM-OTP")
		la("thiếu OTP: hỏi", (r["ok"], r.get("can_otp"), si.vgb_giam_ud), (0, 1, 0))
		nem("OTP sai: chặn", lambda: u.ap_quay(si.name, "ctkm", "CTKM-OTP", otp="000000"), _fr.ValidationError)
		la("sai thì chưa trừ", si.vgb_giam_ud, 0)
		r = u.ap_quay(si.name, "ctkm", "CTKM-OTP", otp="123456")
	la("OTP đúng: trừ 30%", (r["ok"], si.vgb_giam_ud), (1, 55500.0))
	la("cách duyệt ghi OTP", u.doc_ud(si.vgb_ud_ban)["cach"], u.CACH_QUAY + " (OTP)")
	si["items"].append(_fr._dict(item_code="NUTR00021", qty=1, rate=45000))
	with _quay(si):
		u.tinh_lai(si)
	la("gọi thêm món: tính lại, vẫn trừ", si.vgb_giam_ud, 69000.0)
	si.save()
	with _quay(si):
		kq = u.truoc_chot(si)
	la("lúc chốt: vẫn trừ, có lượt để ghi", (si.vgb_giam_ud, bool(kq)), (69000.0, True))
	si2 = _hd()
	with _quay(si2, sep=True):
		r = u.ap_quay(si2.name, "ma", "vc-quay")
	la("quản lý tự áp mã (chữ thường): khỏi OTP", (r["ok"], si2.vgb_giam_ud), (1, 18500.0))
	with _quay(_hd()):
		r = u.ap_quay("X", "ma", "??")
	la("mã sai khuôn: báo, không lỗi", r["ok"], 0)


@ca("v678 màn bill Tạm tính: khối Khuyến mãi (Chương trình, Nhập mã) hiện ở bill nháp chưa có ưu đãi, cả lúc Sửa hoá đơn (nhắc lưu món trước); khối ưu đãi quầy áp nói rõ quầy áp")
def _man_bill_km():
	js = (GOC / "vagabond/public/js/bep/10-bill-quay.js").read_text()
	m = re.search(r"\n  if \(udBan\) html \+= posKhoiUdBan\(udBan, nhap && tamTinh && !udBan\.da_ghi\);\n  else if \(([^\n]+)\) html \+= pbKhoiKm\(suaMo\);", js)
	la("điều kiện hiện khối", m and m.group(1), "tamTinh && nhap && !d.vgb_huy && !pbCoKm(d)")
	la("gọi đúng hai hàm", ("vagabond.uu_dai_ban.ds_quay" in js, "vagabond.uu_dai_ban.ap_quay" in js), (True, True))
	la("nút đủ 44 điểm", "min-height:44px" in js[js.index("function pbKhoiKm"):js.index("function pbDongKm")], True)


# ----------------------------------------- voucher Grab Dine-Out, phương án A (v678)
# Anh Việt chốt 20/11/2026: chương trình voucher Grab chỉ giảm PHẦN TIỆM CHỊU (đo
# trên site: voucher 200.000 đ tiệm chịu 40.000 đ, 300.000 đ chịu 60.000 đ), đối
# soát so phần giảm trên bill với cột khuyến mãi của báo cáo Grab.

import importlib  # noqa: E402

from vagabond import doi_soat_khop as dk  # noqa: E402


def _gd(ma, tien_hang, giam_gia, ngay="2026-11-21"):
	return dict(loai="ban", ngay=ngay, ma_tham_chieu=ma, ma_don=ma, tien_hang=tien_hang, giam_gia=giam_gia,
		thuc_nhan=int(tien_hang * 0.85), phi=0)


def _bill(name, tien_goc, giam, ma, ngay="2026-11-21"):
	return dict(name=name, ngay=ngay, tien=tien_goc - giam, tien_goc=tien_goc, ma=[ma])


@ca("v678 bước nâng voucher Grab: chỉ chương trình Grab Dine-Out còn đúng giá cũ 200.000/300.000 đổi thành phần tiệm chịu 40.000/60.000, tên ghi rõ; chạy lại không đổi")
def _grab_nang():
	vg = importlib.import_module("vagabond.patches.v678_voucher_grab")
	a = dict(ten="VOUCHER 200.000 GRAB DINE OUT", kieu_giam="So tien", gia_tri=200000.0)
	b = dict(ten="VOUCHER 300.000 GRAB DINE OUT", kieu_giam="So tien", gia_tri=300000.0)
	la("200k -> 40k", vg.nang(a), {"gia_tri": 40000, "ten": "VOUCHER 200.000 GRAB DINE OUT (tiệm chịu 40.000)"})
	la("300k -> 60k", vg.nang(b)["gia_tri"], 60000)
	la("đã nâng thì thôi", vg.nang(dict(a, gia_tri=40000, ten=vg.nang(a)["ten"])), None)
	la("có người sửa giá khác thì để nguyên", vg.nang(dict(a, gia_tri=180000)), None)
	la("không phải Grab Dine-Out", vg.nang(dict(a, ten="Giảm 200.000 sinh nhật")), None)
	la("giảm theo % thì để nguyên", vg.nang(dict(a, kieu_giam="Phan tram", gia_tri=200000)), None)


@ca("v678 đối soát Grab Dine-Out (khop_hoa_don thật): từ 21/11 bill phải giảm đúng phần tiệm chịu; giảm đủ giá voucher là Lệch tiền kèm số; bill thấp hơn giá voucher vẫn nối, ghi Grab trả thêm; bill trước 21/11 giữ luật cũ")
def _grab_doi_soat():
	dong = [_gd("GD-AAA", 195000, 40000), _gd("GD-BBB", 195000, 40000), _gd("GD-CCC", 160000, 40000),
		_gd("GD-DDD", 195000, 40000, ngay="2026-11-20"), _gd("GD-EEE", 205000, 0)]
	ung = [_bill("SI-A", 235000, 40000, "GD-AAA"), _bill("SI-B", 235000, 200000, "GD-BBB"),
		_bill("SI-C", 195000, 40000, "GD-CCC"), _bill("SI-D", 235000, 200000, "GD-DDD", ngay="2026-11-20"),
		_bill("SI-E", 205000, 0, "GD-EEE")]
	kq = dk.khop_hoa_don("grab", dong, ung)
	la("giảm đúng 40.000: Đã nối", (kq[0]["trang_thai"], kq[0]["ghi_chu"]), ("Đã nối", ""))
	la("giảm đủ 200.000: Lệch tiền", kq[1]["trang_thai"], "Lệch tiền")
	dung("ghi chú nói bill giảm và phần tiệm chịu: " + kq[1]["ghi_chu"], "200.000" in kq[1]["ghi_chu"] and "40.000" in kq[1]["ghi_chu"])
	la("bill 195.000 dùng voucher 200.000: Đã nối", kq[2]["trang_thai"], "Đã nối")
	dung("ghi chú Grab trả thêm 5.000: " + kq[2]["ghi_chu"], "5.000" in kq[2]["ghi_chu"])
	la("bill trước 21/11 giữ luật cũ", kq[3]["trang_thai"], "Đã nối")
	la("Grab Dine-Out không voucher", kq[4]["trang_thai"], "Đã nối")
	# Một nguồn (loại 3): màn Bill chưa khớp đối tác dùng chung cung_tien, không
	# xếp dòng Lệch tiền vì voucher thành khớp.
	b = dict(ung[1], kieu="grab", diem="TCV")
	d = dict(dong[1], trang_thai_khop="Lệch tiền", tien=235000)
	r = dk.doi_chieu_bill([b], {("SI-B", "grab"): d}, {}, hom_nay="2026-11-22")
	dung("màn bill vẫn lệch: " + r[0]["trang_thai"], r[0]["trang_thai"] != dk.TT_BILL_KHOP)
	# Nới "bill thấp hơn giá voucher" chỉ cho bill mang mã GD-: không nối theo tiền vào bill khác.
	la("bill không mã GD- không cùng tiền theo luật nới",
		dk.cung_tien("grab", _gd("GD-ZZZ", 160000, 40000), _bill("SI-X", 195000, 40000, "")), False)


@ca("v678 báo cáo GrabFood: dòng Grab Dine-Out mã dính giờ ('GD-2:01 PM ... QPJRSHRM', site 20/11 DSN-2611-07964 bốn dòng) đọc đủ mã và 7 cột tiền")
def _grab_dong_dinh():
	from vagabond import doi_soat_mau as m

	tho = ["GD-2:01 PM                    Trả thẻ / Ví       400.000      0                     -         -60.000          -50.050                0   289.950            QPJRSHRM",
		"GD-10:05 AM                  Trả thẻ / Ví       205.000      0                     -         -40.000          -24.289                0   140.711             I277C4ES",
		"GD-10:03 AM                  Trả thẻ / Ví       205.000      0                     -              0          -30.177                0   174.823             SBXFJS6X",
		"GD-9:35 AM                    Trả thẻ / Ví       205.000      0                     -         -40.000          -24.289                0   140.711           H5BN2GLV"]
	ra = [m.chuan_dong_don_grab(x) for x in tho]
	la("bốn dòng thành dòng đủ mã", [m.loai_manh_grab(x) for x in ra], ["du"] * 4)
	la("mã đúng", [m._RE_DON.match(x).group(2).replace(" ", "") for x in ra], ["GD-QPJRSHRM", "GD-I277C4ES", "GD-SBXFJS6X", "GD-H5BN2GLV"])
	la("dòng chuẩn không đổi", m.chuan_dong_don_grab("2:01 PM GD-QPJRSHRM Trả thẻ / Ví 400.000 0 - -60.000 -50.050 0 289.950"),
		"2:01 PM GD-QPJRSHRM Trả thẻ / Ví 400.000 0 - -60.000 -50.050 0 289.950")


@ca("v678 tin Zalo đối soát: thư lịch nghỉ lễ OnePay không là thư báo cáo; bỏ lịch thư Payoo (mặc định và bước nâng); tệp đọc lỗi gửi nhóm Hệ thống, không gửi nhóm Kế toán")
def _tin_doi_soat():
	from vagabond import doi_soat_thu as T
	from vagabond import doi_soat_vendor as dsv
	from vagabond import kenh_zalo as kz

	for td, than in (("OnePay - Thông báo lịch tạm ứng doanh số dịp nghỉ lễ Ngày văn hóa Việt Nam", "tạm ứng doanh số thanh toán"),
			("[OnePay Thong bao]: Lich nghi le Ngay Van hoa Viet Nam 24/11/2026", "thanh toan")):
		la("không phải báo cáo: " + td[:30], dsv.thu_co_bao_cao(td, than), False)
	la("báo cáo thật vẫn nhận", dsv.thu_co_bao_cao("Payoo-POS-Card_ĐỐI SOÁT KỲ 13.11_15.11.2026", ""), True)
	# Anh Việt 20/11/2026: không dùng Payoo nữa, không chờ thư Payoo, không báo động.
	la("lịch mặc định không còn Payoo", [v for v, *_ in T.LICH_MAC_DINH if v == "Payoo"], [])
	la("bước nâng bỏ đúng dòng lịch Payoo", T.bo_payoo_v678([dict(name="r1", nguon="Payoo"), dict(name="r2", nguon="OnePay"),
		dict(name="r3", nguon=" payoo ")]), ["r1", "r3"])
	cay = ast.parse((GOC / "vagabond/doi_soat_thu.py").read_text(encoding="utf-8"))
	goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and any(k.arg == "ma_tin" and getattr(k.value, "value", "") == "ht_ds_tep_loi" for k in n.keywords)]
	la("gửi nhóm Hệ thống", [(n.args[0].value, n.args[1].value) for n in goi], [("canh_bao", "he_thong")])
	ma = {k.value.value for n in ast.walk(cay) if isinstance(n, ast.Call) for k in n.keywords if k.arg == "ma_tin" and isinstance(k.value, ast.Constant)}
	la("không còn gửi kt_ds_tep_loi", "kt_ds_tep_loi" in ma, False)
	la("tin có trong danh mục, mốc nhóm hộp thư lỗi", (kz.TIN["ht_ds_tep_loi"][4], kz.TIN_MOC["ht_ds_tep_loi"]), ("he_thong", "ht_ds_hop_thu_loi"))
	vt = importlib.import_module("vagabond.patches.v678_tin_chuyen_khoan")
	la("bản vá tích tin mới", "ht_ds_tep_loi" in vt.TIN_MOI, True)
	dung("tin không bảo Kế toán báo kỹ thuật", "Kế toán" not in " ".join(T.tin_tep_loi("A", "b", "c")[1]))


@ca("Codex #597 vòng 1: tiền về CẢ MB và Shinhan cho một bill thì cửa ghi sổ chặn, trừ khi dòng thanh toán chia đúng số từng ngân hàng (ban_hang._kiem_tk_ck thật)")
def _codex597_hai_ngan_hang():
	src = (GOC / "vagabond/ban_hang.py").read_text()
	fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_kiem_tk_ck")
	from vagabond import chiem_sao_ke

	g = {"frappe": _fr, "chiem_sao_ke": chiem_sao_ke, "pt_ck": pt_ck, "pt_thanh_toan": types.SimpleNamespace(ba_shinhan=lambda: BA_SH),
		"thanh_toan_nhieu": ttn, "flt": _fr.utils.flt}
	exec(compile(ast.Module(body=[fn], type_ignores=[]), "ban_hang._kiem_tk_ck", "exec"), g)
	kiem = g["_kiem_tk_ck"]
	si = _hd(custom_pancake_display_id=MA, items=[{"item_code": "BANH", "qty": 1, "rate": 100000}])
	gd = [(BA_MB, 60000), (BA_SH, 40000)]

	def chay(pt, dong):
		with patch.object(_fr.db, "sql", side_effect=lambda q, p=None, **k: list(gd), create=True), \
				patch.object(ttn, "dong_cua", lambda n: dong):
			try:
				kiem(si, pt, ["ACC-BTN-1", "ACC-BTN-2"])
				return ""
			except _fr.ValidationError as e:
				return str(e)

	loi = chay("Chuyển khoản", [])
	dung("một phương thức mà tiền về hai ngân hàng: chặn, nói số từng nơi " + loi,
		"hai ngân hàng" in loi and "60.000" in loi and "40.000" in loi and MA in loi)
	la("dòng thanh toán chia đúng: qua", chay("Chuyển khoản", [{"pt": "Chuyển khoản", "so_tien": 60000},
		{"pt": "Chuyển khoản - Shinhan", "so_tien": 40000}]), "")
	dung("dòng chia sai số: chặn", chay("Chuyển khoản", [{"pt": "Chuyển khoản", "so_tien": 50000},
		{"pt": "Chuyển khoản - Shinhan", "so_tien": 50000}]) != "")
	la("phép thuần", [pt_ck.soat_tk_ck("Chuyển khoản", [(BA_MB, 1), (BA_SH, 2)], BA_SH, {})[0],
		pt_ck.soat_tk_ck("Chuyển khoản", [(BA_SH, 5)], BA_SH, {})[0], pt_ck.soat_tk_ck("Chuyển khoản", [(BA_MB, 5)], BA_SH, {})[0],
		pt_ck.soat_tk_ck("Tiền mặt", [(BA_SH, 5)], BA_SH, {})[0], pt_ck.soat_tk_ck("Chuyển khoản", [("", 5)], BA_SH, {})[0]],
		["nhieu", "doi", "", "", ""])
	la("tiền về một ngân hàng mà dòng chia hai phương thức chuyển khoản: chặn",
		pt_ck.soat_tk_ck("Chuyển khoản", [(BA_MB, 100000)], BA_SH, {"Chuyển khoản": 60000, "Chuyển khoản - Shinhan": 40000})[0], "nhieu")
	la("tiền về Shinhan, dòng chuyển khoản là Shinhan cạnh tiền mặt: qua",
		pt_ck.soat_tk_ck("Chuyển khoản - Shinhan", [(BA_SH, 40000)], BA_SH, {"Tiền mặt": 60000, "Chuyển khoản - Shinhan": 40000}), ("", None))


@ca("Codex PR #597 vòng 3 (loại 5, 12): Bank Account khai theo tên chuẩn trong danh mục ngân hàng chung (SHBVN - Ngân hàng TNHH MTV Shinhan Việt Nam) vẫn ra mã, qr_pt() thật vẽ QR Shinhan; mọi tên trong danh mục có cùng ngân hàng trong bảng QR đều ra đúng mã")
def _codex597_v3_ten_napas():
	import io
	import json as _json
	import os
	from vagabond import pt_thanh_toan
	ten = "SHBVN - Ngân hàng TNHH MTV Shinhan Việt Nam"
	with io.open(os.path.join(os.path.dirname(tai_khoan.__file__), "du_lieu", "napas.json"), encoding="utf-8") as f:
		ds = [x[0] for x in _json.load(f)]
	dung("tên lấy thật từ danh mục", ten in ds)
	la("tên chuẩn Shinhan ra mã", tai_khoan.ma_theo_ten_ngan_hang(ten), "SHBVN")
	la("tên chuẩn có mã khác bảng QR", [tai_khoan.ma_theo_ten_ngan_hang(x) for x in (
		"VIETINBANK - Ngân hàng TMCP Công thương Việt Nam", "ABBANK - Ngân hàng TMCP An Bình", "MB - Ngân hàng TMCP Quân đội",
		"SGB - Ngân hàng TMCP Sài Gòn Công Thương", "NASB - Ngân hàng TMCP Bắc Á", "  shbvn - ngân hàng tnhh mtv shinhan việt nam ")],
		["ICB", "ABB", "MB", "SGICB", "BAB", "SHBVN"])
	la("tên lạ có dấu gạch: không đoán", [tai_khoan.ma_theo_ten_ngan_hang(x) for x in ("XYZ - Ngân hàng lạ", " - ", "PVCOMBANK PAY - PVcomBank Pay")], ["", "", ""])
	# Mọi tên trong danh mục mà mã đầu tên trùng mã hay bí danh của bảng QR đều ra đúng BIN.
	lech = [x for x in ds if tai_khoan.ma_theo_ten_ngan_hang(x) and not tai_khoan.bin_cho(tai_khoan.ma_theo_ten_ngan_hang(x))]
	la("không tên nào ra mã mà thiếu BIN", lech, [])
	with patch.object(pt_thanh_toan, "ba_cua_pt", side_effect=lambda pt, *a: "BA-SH" if pt == "Chuyển khoản - Shinhan" else ""), \
			patch.object(_fr.db, "get_value", return_value=_fr._dict(bank_account_no="700012345678", bank=ten)), \
			patch.object(tai_khoan, "cai", return_value={"mac_dinh": {"ten": "THE VAGABOND"}}):
		q = pt_thanh_toan.qr_pt()
	la("qr_pt thật: có QR Shinhan đúng BIN", (q.get("Chuyển khoản - Shinhan") or {}).get("bin"), "970424")
