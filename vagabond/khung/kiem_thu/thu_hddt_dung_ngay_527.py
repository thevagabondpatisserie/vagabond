# -*- coding: utf-8 -*-
"""v527 phần A: hoá đơn của một ngày ký sang ngày hôm sau.

Chị Dung tổng hợp 25/09/2026, số đo lại trên site thật cùng ngày:

- 18/09: 217 tờ đẩy lên m-invoice từ 00:16 tới 00:20 ngày 19/09, ký 19/09.
  Cả ngày 18/09 máy ghi "HOÃN PHÁT HÀNH ... còn nợ ngày cũ". Nợ đó là
  HDB-26-09-03136 (17/09, 95.000 đ) giữ cờ "chưa rõ kết quả gửi" sau khi
  m-invoice trả Internal server error.
- 23/09: 201 tờ đẩy 00:16 tới 00:20 ngày 24/09, ký 01:08. Nợ là
  HDB-26-09-04263 (22/09) giữ cờ sau khi lượt xuất rải bị cắt 300 giây
  đúng lúc đang chờ m-invoice.
- 24/09: 15 bill quầy ghi sổ 23:05 mà 00:16 ngày 25/09 mới ra. Nhịp bù
  23:15 trượt khoá (Filelock 23:17) rồi bỏ đi lặng lẽ.
- 25/09: HDB-26-09-04733 (24/09, cắt 300 giây lúc 21:45) chặn cả ngày
  25/09 từ 11:40, gỡ tay lúc 12:59.

CẨN THẬN KHI SỬA: các ca dưới đây chạy hàm THẬT lấy từ mã nguồn, chỉ thay
phần chạm mạng và cơ sở dữ liệu. Đừng gọi thêm hàm nào "cho chắc" vào giữa
chuỗi (điều 15): chính hàm đó có thể gỡ cờ hộ trước khi ca kịp nhìn.
"""

import ast
import datetime
import sys
import unittest.mock
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond import hddt_bu, hddt_cho_xuat
from vagabond.khung.kiem_thu.nen import ca, dung, la

D = datetime.date
GOC = Path(__file__).resolve().parents[2]


def _nap(tep, ten, g):
	"""Nạp đúng MỘT hàm thật từ mã nguồn vào môi trường g, trả hàm đó."""
	cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
	fn = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)
	exec(compile(ast.Module(body=[fn], type_ignores=[]), str(GOC / tep), "exec"), g)
	return g[ten]


# ------------------------------------------------------------------ thuần


@ca("v527 ngày tự đối chiếu: chỉ ngày còn hạn ký và còn cửa m-invoice")
def _ngay_tu_doi_chieu():
	f = hddt_cho_xuat.ngay_tu_doi_chieu
	la("25/09 tự đối chiếu tờ 24/09 (ca thật GF-811)",
		f(["2026-09-24"], D(2026, 9, 25), D(2026, 9, 24)), [D(2026, 9, 24)])
	la("24/09 KHÔNG tự đối chiếu tờ 22/09 đã quá hạn (quá hạn là việc của người)",
		f(["2026-09-22"], D(2026, 9, 24), D(2026, 9, 23)), [])
	# Đột biến "bỏ hạn pháp lý" lần đầu không đổ ca nào (điều 17c): ca 22/09
	# ở trên có cửa m-invoice cũng đã đóng, lớp kia đỡ. Ca này cửa m-invoice
	# còn mở (chưa có tờ nào mang ngày mới hơn) mà hạn ký đã qua.
	la("hạn ký đã qua thì thôi, dù cửa m-invoice còn mở",
		f(["2026-09-22"], D(2026, 9, 24), D(2026, 9, 22)), [])
	la("cửa m-invoice đã đóng thì thôi",
		f(["2026-09-24"], D(2026, 9, 25), D(2026, 9, 25)), [])
	la("hôm nay được, trừ khi chỉ ngày cũ",
		(f(["2026-09-25"], D(2026, 9, 25), None), f(["2026-09-25"], D(2026, 9, 25), None, True)),
		([D(2026, 9, 25)], []))
	la("cũ trước mới sau, không trùng, bỏ ngày tương lai",
		f(["2026-09-25", "2026-09-24", "2026-09-24", "2026-09-26"], D(2026, 9, 25), None),
		[D(2026, 9, 24), D(2026, 9, 25)])


@ca("v527 lượt phát hành còn tờ chưa ra: tờ tìm thấy chưa tạo hoặc tờ cần ký chưa ký")
def _con_to_chua_ra():
	f = hddt_bu.con_to_chua_ra
	dung("tìm 15 tạo 0 là còn", f({"tim_thay": 15, "tao_ok": 0}, {"can_ky": 0, "da_ky": 0}))
	dung("ký thiếu là còn", f({"tim_thay": 0, "tao_ok": 0}, {"can_ky": 58, "da_ky": 57}))
	dung("đủ cả hai là hết", not f({"tim_thay": 58, "tao_ok": 58}, {"can_ky": 58, "da_ky": 58}))
	dung("công tắc tắt thì không nói gì", not f("bỏ qua (tắt ở m-invoice)", "bỏ qua (tắt ở m-invoice)"))


# ------------------------------------------------- hàng rào, chạy hàm thật


def _hang_rao(no_rong, no_hep, tu_doi):
	"""Chạy THẬT xuat_ngay_cu_truoc trên tình huống 23/09 (hôm nay 23/09,
	nợ là một tờ 22/09 giữ cờ). no_rong/no_hep là list để ca đổi được giữa
	chừng: tu_doi(g) giả lập m-invoice trả lời, rồi sửa tập nợ tương ứng."""
	vet = []
	bh = NS(_ngay_so_hddt_moi_nhat=lambda: D(2026, 9, 22),
		_khoa_hddt=lambda **kw: vet.append("khoa") or object(),
		_mo_khoa_dong_bo=lambda *a: vet.append("nha"), _cong_tac_minvoice=lambda: (1, 1),
		_phat_hanh_theo_lo=lambda d: vet.append(("phat_hanh", d)) or {"tim_thay": 0, "tao_ok": 0, "loi": []},
		_ky_theo_lo=lambda d: {"can_ky": 0, "da_ky": 0, "loi": []})
	moc = []

	def goi_tu_doi(**kw):
		vet.append(("tu_doi_chieu", kw))
		return tu_doi(no_rong, no_hep)

	g = dict(frappe=unittest.mock.MagicMock(), ngay_cu_can_bao_ve=lambda: list(no_rong),
		ngay_cu_dang_cho=lambda: list(no_hep), ngay_cu_con_mo=hddt_cho_xuat.ngay_cu_con_mo,
		getdate=lambda x: x, nowdate=lambda: D(2026, 9, 23), _ngay_xac_nhan_qua_han=lambda: (),
		cint=lambda x: int(x or 0), _ghi_moc_loi=lambda x: moc.append(x), tu_doi_chieu_co=goi_tu_doi)
	fn = _nap("hddt_cho_xuat.py", "xuat_ngay_cu_truoc", g)
	with unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		ra = fn()
	return ra, vet, moc


@ca("v527 hàng rào 23/09: tờ 22/09 giữ cờ mà m-invoice xác nhận chưa có thì tự gỡ và cho hôm nay đi")
def _hang_rao_tu_go():
	def m_invoice_chua_co(no_rong, no_hep):
		# chay_nen gỡ cờ, xuất tờ đó mang ngày 22/09: hết nợ.
		no_rong.clear()
		return 1
	ra, vet, moc = _hang_rao([D(2026, 9, 22)], [], m_invoice_chua_co)
	la("cho tờ hôm nay đi", ra, True)
	la("gọi đối chiếu đúng ngày nợ, chỉ ngày cũ",
		vet[0], ("tu_doi_chieu", {"chi_ngay": [D(2026, 9, 22)], "chi_ngay_cu": True}))
	la("hết nợ thì xoá mốc lỗi", moc, [False])


@ca("v527 hàng rào: m-invoice không trả lời chắc chắn thì VẪN chặn, không mở tay")
def _hang_rao_khong_chac():
	# Đối chiếu chạy nhưng giữ cờ: tập nợ không đổi. Hàng rào không được
	# tự tin là đã hết nợ chỉ vì vừa chạy đối chiếu.
	ra, vet, moc = _hang_rao([D(2026, 9, 22)], [], lambda no_rong, no_hep: 1)
	la("vẫn chặn tờ hôm nay", ra, False)
	dung("đối chiếu chạy NGOÀI khoá: trước khi lấy khoá phát hành",
		vet[0][0] == "tu_doi_chieu" and "khoa" in vet and vet.index("khoa") > 0)
	la("vẫn ghi mốc lỗi cho người trực", moc, [True])


@ca("v527 hàng rào: không có tờ giữ cờ thì đi đúng đường cũ, không gọi mạng thêm")
def _hang_rao_khong_co():
	ra, vet, moc = _hang_rao([D(2026, 9, 22)], [D(2026, 9, 22)], lambda no_rong, no_hep: 0)
	dung("vẫn phát hành tập hẹp như cũ", ("phat_hanh", "2026-09-22") in vet)
	la("tự đối chiếu gọi một lần, trả 0 (bên trong không gọi mạng)", sum(1 for v in vet if v[0] == "tu_doi_chieu"), 1)


# ----------------------------------------------- tu_doi_chieu_co, hàm thật


def _tu_doi(ngay_co, chi_ngay=None, chi_ngay_cu=False, chay_nen=None, doc_loi=False):
	goi, log = [], []

	def doc():
		if doc_loi:
			raise hddt_cho_xuat.KhongDocDuocNo("mất kết nối")
		# v527 vòng 2: nguồn trả cặp (ngày sổ, ngày lập); tờ chưa kéo ngày thì hai ngày trùng.
		return [(d, d) for d in ngay_co]

	nhap = []
	bh = NS(_ngay_so_hddt_moi_nhat=lambda: nhap.append(1) or D(2026, 9, 24))
	g = dict(frappe=NS(log_error=lambda *a, **k: log.append(a), get_traceback=lambda: ""),
		ngay_co_to_giu_co=doc, ke_hoach_tu_doi_chieu=hddt_cho_xuat.ke_hoach_tu_doi_chieu, _ngay=hddt_cho_xuat._ngay,
		getdate=lambda x: x, nowdate=lambda: D(2026, 9, 25), NGUOI_MAY="Máy",
		chay_nen=chay_nen or (lambda *a, **k: goi.append(a) or {"keo": 1}))
	fn = _nap("hddt_cho_xuat.py", "tu_doi_chieu_co", g)
	with unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		ra = fn(chi_ngay=chi_ngay, chi_ngay_cu=chi_ngay_cu)
	return ra, goi, log, nhap


@ca("v527 tự đối chiếu 25/09: đi đúng đường Cài đặt > Hoá đơn ngày cũ, giữ ngày 24/09")
def _tu_doi_24():
	ra, goi, log, _ = _tu_doi([D(2026, 9, 24), D(2026, 9, 25)], chi_ngay_cu=True)
	la("một ngày", ra, 1)
	la("chay_nen giữ đúng ngày bán, ngày tham chiếu hôm nay",
		goi, [("2026-09-24", "giu_ngay", "Máy", "2026-09-25", "2026-09-24")])


@ca("v527 tự đối chiếu: không có tờ giữ cờ thì trả 0 và KHÔNG đụng m-invoice")
def _tu_doi_rong():
	ra, goi, log, nhap = _tu_doi([])
	la("0", ra, 0)
	la("không gọi chay_nen", goi, [])
	la("không đọc cả mốc số mới nhất", nhap, [])


@ca("v527 tự đối chiếu: đọc lỗi thì 0 và ghi log; một ngày lỗi không kéo ngày khác")
def _tu_doi_loi():
	ra, goi, log, _ = _tu_doi([], doc_loi=True)
	la("đọc lỗi trả 0", ra, 0)
	la("có log", len(log), 1)

	def nen(*a, **k):
		if a[0] == "2026-09-24":
			raise RuntimeError("m-invoice sập")
		return {}
	ra, goi, log, _ = _tu_doi([D(2026, 9, 24), D(2026, 9, 25)], chay_nen=nen)
	la("ngày 25 vẫn chạy", ra, 1)
	la("ngày 24 có log", len(log), 1)


@ca("v527 tự đối chiếu: chi_ngay lọc đúng ngày được hỏi")
def _tu_doi_chi_ngay():
	ra, goi, log, _ = _tu_doi([D(2026, 9, 24), D(2026, 9, 25)], chi_ngay=["2026-09-25"])
	la("chỉ 25/09", [a[0] for a in goi], ["2026-09-25"])


# ------------------------------------------- chuỗi cuối ngày, nhịp bù, cron


def _phat_hanh_cuoi_ngay(ph):
	vet, log = [], []
	g = dict(
		frappe=NS(set_user=lambda *a: None, log_error=lambda *a, **k: log.append(k.get("title") or a),
			db=NS(set_single_value=lambda *a: None, commit=lambda: None)),
		hddt_cho_xuat=NS(tu_doi_chieu_co=lambda **kw: vet.append(("tu_doi_chieu", kw)),
			phat_hanh=lambda *a: {"tim_thay": 0, "tao_ok": 0, "loi": []},
			ky=lambda *a: {"can_ky": 0, "da_ky": 0, "loi": []}),
		_khoa_hddt=lambda **kw: vet.append("khoa") or object(), _mo_khoa_dong_bo=lambda *a: vet.append("nha"),
		_cong_tac_minvoice=lambda: (1, 1), _phat_hanh_theo_lo=lambda d: dict(ph),
		_ky_theo_lo=lambda d: {"can_ky": ph["tao_ok"], "da_ky": ph["tao_ok"], "loi": []},
		_gop_cho_xuat=lambda a, b: dict(a, loi_cho_xuat=[]), _goi_server_script=None,
		hddt_bu=hddt_bu, now_datetime=lambda: datetime.datetime(2026, 9, 24, 23, 6), cint=lambda x: int(x or 0))
	_nap("ban_hang.py", "phat_hanh_cuoi_ngay", g)("2026-09-24", 72, 0)
	return vet, log


@ca("v527 chuỗi cuối ngày: đối chiếu tờ giữ cờ CỦA NGÀY ĐÓ trước khi lấy khoá phát hành")
def _chuoi_doi_chieu_truoc():
	vet, log = _phat_hanh_cuoi_ngay({"tim_thay": 58, "tao_ok": 58, "loi": []})
	la("gọi đúng ngày của chuỗi", vet[0], ("tu_doi_chieu", {"chi_ngay": ["2026-09-24"]}))
	la("rồi mới lấy khoá", vet[1], "khoa")
	la("ra đủ thì không có log", log, [])


@ca("v527 chuỗi cuối ngày: còn tờ chưa ra mà không lỗi thì vẫn để lại dấu (ca 24/09)")
def _chuoi_con_to():
	vet, log = _phat_hanh_cuoi_ngay({"tim_thay": 15, "tao_ok": 0, "loi": []})
	la("có đúng một log còn tờ", log, ["Vagabond: phát hành cuối ngày 2026-09-24 còn tờ chưa ra"])


def _bu(ngay_duoc_bu, cho_khoa=5):
	vet = []
	g = dict(
		frappe=NS(set_user=lambda *a: None, log_error=lambda *a, **k: None, get_traceback=lambda: ""),
		_cong_tac_minvoice=lambda: (1, 1), getdate=lambda x: x, nowdate=lambda: D(2026, 9, 24),
		cfg=lambda: {"tu_ghi_so_lan_cuoi": "2026-09-24"},
		hddt_bu=NS(ngay_duoc_bu=lambda *a: list(ngay_duoc_bu)), _ngay_so_hddt_moi_nhat=lambda: None,
		hddt_cho_xuat=NS(ngay_cho_xuat_can_thu_lai=lambda d: {"con_han": [], "qua_han": []},
			tu_doi_chieu_co=lambda **kw: vet.append(("tu_doi_chieu", kw)),
			phat_hanh=lambda *a: {"tim_thay": 0, "tao_ok": 0, "loi": []},
			ky=lambda *a: {"can_ky": 0, "da_ky": 0, "loi": []}),
		_khoa_hddt=lambda cho=5: vet.append(("khoa", cho)) or None,
		_mo_khoa_dong_bo=lambda *a: None, cint=lambda x: int(x or 0))
	_nap("ban_hang.py", "xuat_hddt_con_thieu_tu_dong", g)(cho_khoa=cho_khoa)
	return vet


@ca("v527 nhịp bù: đối chiếu tờ giữ cờ của các ngày được bù, rồi đợi khoá đúng số giây được giao")
def _bu_doi_chieu():
	vet = _bu([D(2026, 9, 23), D(2026, 9, 24)], cho_khoa=120)
	la("đối chiếu đúng các ngày được bù", vet[0], ("tu_doi_chieu", {"chi_ngay": [D(2026, 9, 23), D(2026, 9, 24)]}))
	la("đợi khoá 120 giây", vet[1], ("khoa", 120))
	la("mặc định vẫn 5 giây", _bu([D(2026, 9, 24)])[1], ("khoa", 5))


def _vo(ten, enqueue_loi=False):
	goi, chay = [], []

	def enqueue(ham, **kw):
		if enqueue_loi:
			raise RuntimeError("Redis mất")
		goi.append((ham, kw))
	f = NS(enqueue=enqueue, log_error=lambda *a, **k: None, get_traceback=lambda: "",
		get_attr=lambda ham: (lambda **kw: chay.append((ham, kw))))
	g = dict(frappe=f)
	_nap("ban_hang.py", "_day_hang_doi_dai", g)
	_nap("ban_hang.py", ten, g)()
	return goi, chay


@ca("v527 vỏ hàng đợi dài: xuất rải, nhịp bù và vét trước 0h không còn chạy trong luồng 300 giây")
def _vo_hang_doi():
	for ten, ham, kw in (
			("xuat_rai_trong_ngay_tu_dong", "vagabond.ban_hang.xuat_rai_trong_ngay", {}),
			("bu_hddt_tu_dong", "vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong", {}),
			("bu_truoc_nua_dem", "vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong", {"cho_khoa": 120})):
		goi, chay = _vo(ten)
		la(ten + " đẩy đúng hàm thân", [g[0] for g in goi], [ham])
		o = goi[0][1]
		dung(ten + " hàng đợi long, hơn 300 giây", o["queue"] == "long" and o["timeout"] > 300)
		dung(ten + " chống chồng lượt", o["deduplicate"] is True and o["job_id"].startswith("vgb-"))
		la(ten + " tham số", {k: v for k, v in o.items() if k not in ("queue", "timeout", "job_id", "deduplicate")}, kw)
		goi, chay = _vo(ten, enqueue_loi=True)
		la(ten + " không đẩy được thì chạy tại chỗ", chay, [(ham, kw)])
	job = {_vo(t)[0][0][1]["job_id"] for t in ("bu_hddt_tu_dong", "bu_truoc_nua_dem")}
	la("vét trước 0h không bị nhịp bù giờ nuốt mất vì trùng mã việc", len(job), 2)


@ca("v527 bộ lập lịch: khai đúng ba vỏ và ba nhịp vét trước nửa đêm")
def _lich():
	h = (GOC / "hooks.py").read_text(encoding="utf-8")
	dung("xuất rải qua vỏ", '"10,40 * * * *": ["vagabond.ban_hang.xuat_rai_trong_ngay_tu_dong"]' in h)
	dung("bù mỗi giờ qua vỏ", '"15 * * * *": ["vagabond.ban_hang.bu_hddt_tu_dong"]' in h)
	dung("ba nhịp vét trước 0h", '"25,40,52 23 * * *": ["vagabond.ban_hang.bu_truoc_nua_dem"]' in h)
	dung("không còn khai thẳng thân chạy 300 giây",
		'["vagabond.ban_hang.xuat_rai_trong_ngay"]' not in h
		and '["vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong"]' not in h)


# --------------------------- Codex vòng 2 (#369) G1: tờ kéo ngày bị giữ cờ


class _R(dict):
	__getattr__ = dict.get


def _tu_doi_that(rows, moi_nhat=D(2026, 9, 24), **kw):
	"""Chạy ngay_co_to_giu_co + tu_doi_chieu_co THẬT. Chỉ giả câu SQL, cài
	đặt điểm bán và chay_nen (phần chạm m-invoice)."""
	goi = []
	f = NS(db=NS(sql=lambda *a, **k: [_R(r) for r in rows]),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")
	bh = NS(_ngay_so_hddt_moi_nhat=lambda: moi_nhat)
	with unittest.mock.patch.object(hddt_cho_xuat, "frappe", f), \
			unittest.mock.patch.object(hddt_cho_xuat, "_cai_dat_minvoice", lambda: ({}, {"Tại chỗ"}, [])), \
			unittest.mock.patch.object(hddt_cho_xuat, "nowdate", lambda: "2026-09-25"), \
			unittest.mock.patch.object(hddt_cho_xuat, "chay_nen", lambda *a, **k: goi.append((a, k)) or {}), \
			unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		ra = hddt_cho_xuat.tu_doi_chieu_co(**kw)
	return ra, goi


@ca("v527 Codex G1: tờ bán 10/09 đã kéo sang 24/09 mà bị giữ cờ thì tự đối chiếu theo NGÀY LẬP 24/09")
def _g1_keo_giu_co():
	# Ca thật dựng lại: tờ quá hạn được kế toán kéo sang ngày lập mới, lượt
	# gửi bị cắt giữa chừng nên giữ cờ. Ngày sổ 10/09 đã quá hạn mọi cửa,
	# nhưng ngày lập 24/09 thì còn.
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 10), "vgb_hddt_ngay_xuat": D(2026, 9, 24),
		"custom_nguon": "Tại chỗ", "vgb_quay": ""}])
	la("có chạy một lượt", ra, 1)
	la("kéo đúng: ngày sổ 10/09, ngày lập 24/09, chỉ tờ giữ cờ",
		goi, [(("2026-09-10", "keo", hddt_cho_xuat.NGUOI_MAY, "2026-09-25", "2026-09-24"), {"chi_giu_co": 1})])
	# Đối chứng: tờ không kéo ngày vẫn đi đường giữ ngày cũ, chữ ký gọi y như trước.
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 24), "vgb_hddt_ngay_xuat": None,
		"custom_nguon": "Tại chỗ", "vgb_quay": ""}])
	# Vòng 3 (H1): lượt giữ ngày của máy cũng chỉ đụng tờ giữ cờ đúng ngày lập.
	la("không kéo ngày: giữ ngày, chỉ tờ giữ cờ",
		goi, [(("2026-09-24", "giu_ngay", hddt_cho_xuat.NGUOI_MAY, "2026-09-25", "2026-09-24"), {"chi_giu_co": 1})])
	# Ngày lập cũng đã quá hạn thì máy không làm (việc của người).
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 10), "vgb_hddt_ngay_xuat": D(2026, 9, 20),
		"custom_nguon": "Tại chỗ", "vgb_quay": ""}])
	la("ngày lập quá hạn thì không tự làm", goi, [])
	# Hàng rào hỏi theo ngày sổ cũ: tờ kéo ngày vẫn phải được chọn khi ngày lập khớp.
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 10), "vgb_hddt_ngay_xuat": D(2026, 9, 24),
		"custom_nguon": "Tại chỗ", "vgb_quay": ""}], chi_ngay=["2026-09-24"])
	la("lọc theo ngày lập", len(goi), 1)
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 10), "vgb_hddt_ngay_xuat": D(2026, 9, 24),
		"custom_nguon": "Grab", "vgb_quay": ""}])
	la("điểm không bật xuất thì bỏ", goi, [])


def _nen_that(chon, che_do="keo", ngay="2026-09-10", dich="2026-09-24", **kw):
	"""Chạy _chay_nen_da_nang_quyen THẬT; giả m-invoice, khoá và câu ghi."""
	vet = {"dat": [], "go": [], "ph": [], "ky": []}
	f = unittest.mock.MagicMock()
	f.db.get_value.side_effect = lambda dt, ten, fields, as_dict=True: {
		k: next(r for r in chon if r["name"] == ten).get(k) for k in fields}
	bh = NS(_goi_server_script=None, _khoa_hddt=lambda cho=60: object(), _mo_khoa_dong_bo=lambda k: None,
		_cong_tac_minvoice=lambda: (1, 1), _phat_hanh_theo_lo=lambda d: vet["ph"].append(("lo", d)) or {},
		_ky_theo_lo=lambda d: vet["ky"].append(("lo", d)) or {})
	p = unittest.mock.patch.object
	with p(hddt_cho_xuat, "frappe", f), p(hddt_cho_xuat, "nowdate", lambda: "2026-09-25"), \
			p(hddt_cho_xuat, "_dem_theo_ngay", lambda d, h: ([_R(r) for r in chon], {})), \
			p(hddt_cho_xuat, "_dang_nhap_minvoice", lambda stg: ("http://x", {}, "")), \
			p(hddt_cho_xuat, "kiem_chung_api", lambda b, h: ({"so_hd": "1"}, "")), \
			p(hddt_cho_xuat, "_tra_minvoice", lambda b, h, ten, c: (True, "không có tờ")), \
			p(hddt_cho_xuat, "_go_co_neu_con_nguyen", lambda ten: vet["go"].append(ten) or True), \
			p(hddt_cho_xuat, "_dat_ngay_neu_con_nguyen", lambda ten, a, d: vet["dat"].append((ten, str(d))) or True), \
			p(hddt_cho_xuat, "_ngay_xac_nhan_qua_han", lambda *a: ()), \
			p(hddt_cho_xuat, "xuat_ngay_cu_truoc", lambda: True), \
			p(hddt_cho_xuat, "phat_hanh", lambda d, g: vet["ph"].append(("ngay", d)) or {}), \
			p(hddt_cho_xuat, "ky", lambda d, g: vet["ky"].append(("ngay", d)) or {}), \
			unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		kq = hddt_cho_xuat._chay_nen_da_nang_quyen(ngay, che_do, "Máy", "2026-09-25", dich, **kw)
	return kq, vet


@ca("v527 Codex G1: máy tự kéo tờ giữ cờ thì CHỈ đụng tờ giữ cờ, không kéo lây tờ khác của ngày sổ đó")
def _g1_chi_giu_co():
	chon = [
		{"name": "SI-CO", "vgb_hddt_cho_doi_chieu": 1, "vgb_hddt_ngay_xuat": D(2026, 9, 24),
			"custom_minvoice_id": "", "custom_hddt_id": "", "custom_hddt_so": "", "custom_pancake_display_id": ""},
		{"name": "SI-KHAC", "vgb_hddt_cho_doi_chieu": 0, "vgb_hddt_ngay_xuat": None,
			"custom_minvoice_id": "", "custom_hddt_id": "", "custom_hddt_so": "", "custom_pancake_display_id": ""},
	]
	kq, vet = _nen_that(chon, chi_giu_co=1)
	la("gỡ cờ đúng tờ giữ cờ", vet["go"], ["SI-CO"])
	la("không đặt ngày cho tờ khác", vet["dat"], [])
	la("phát hành theo ngày lập 24/09", vet["ph"], [("ngay", "2026-09-24")])
	# Đối chứng: người bấm tay (không chỉ tờ giữ cờ) thì vẫn kéo cả ngày như cũ.
	kq, vet = _nen_that(chon)
	la("bấm tay: kéo cả tờ khác như trước", vet["dat"], [("SI-KHAC", "2026-09-24")])



# ---------------------------------------------- Codex vòng 3 (#369) trên cbff7e2


def _to_co(ten, so, lap, co=1):
	return {"name": ten, "posting_date": so, "vgb_hddt_cho_doi_chieu": co, "vgb_hddt_ngay_xuat": lap,
		"custom_minvoice_id": "", "custom_hddt_id": "", "custom_hddt_so": "", "custom_pancake_display_id": ""}


@ca("v527 Codex H1: hai tờ giữ cờ cùng ngày sổ mà khác ngày lập thì mỗi lượt chỉ đụng tờ đúng ngày lập của nó")
def _h1_cung_ngay_so():
	chon = [_to_co("SI-24", D(2026, 9, 10), D(2026, 9, 24)), _to_co("SI-25", D(2026, 9, 10), D(2026, 9, 25))]
	kq, vet = _nen_that(chon, chi_giu_co=1)
	la("lượt kéo tới 24/09: chỉ gỡ cờ tờ ngày lập 24/09", vet["go"], ["SI-24"])
	# Lượt giữ ngày của máy cũng vậy: tờ ngày sổ 24/09 đã kéo sang 25/09 thì
	# lượt giữ ngày 24/09 không được đụng tới nó.
	chon = [_to_co("SI-GIU", D(2026, 9, 24), None), _to_co("SI-KEO", D(2026, 9, 24), D(2026, 9, 25))]
	kq, vet = _nen_that(chon, che_do="giu_ngay", ngay="2026-09-24", dich="2026-09-24", chi_giu_co=1)
	la("lượt giữ ngày 24/09: chỉ tờ ngày lập 24/09", vet["go"], ["SI-GIU"])


@ca("v527 Codex H1: máy tự đối chiếu đi lượt giữ ngày cũng chỉ đụng tờ giữ cờ")
def _h1_tu_doi_giu_ngay():
	ra, goi = _tu_doi_that([{"posting_date": D(2026, 9, 24), "vgb_hddt_ngay_xuat": None,
		"custom_nguon": "Tại chỗ", "vgb_quay": ""}])
	la("giữ ngày có chi_giu_co", goi, [(("2026-09-24", "giu_ngay", hddt_cho_xuat.NGUOI_MAY, "2026-09-25", "2026-09-24"), {"chi_giu_co": 1})])



# ---------------------------------------------- Codex vòng 4 (#369) trên cd8684c


def _sql_that(rows):
	"""db.sql chạy THẬT câu SQL trên sqlite trong bộ nhớ (điều 17a: đồ giả
	không tự áp điều kiện, câu SQL của hàm quyết định dòng nào ra)."""
	import re
	import sqlite3
	cot = ["name", "posting_date", "vgb_hddt_ngay_xuat", "custom_nguon", "vgb_quay", "docstatus", "vgb_huy",
		"vgb_tam_tinh", "grand_total", "custom_hddt_so", "custom_minvoice_id", "custom_hddt_id", "vgb_hddt_cho_doi_chieu"]
	con = sqlite3.connect(":memory:")
	con.row_factory = sqlite3.Row
	con.execute("create table `tabSales Invoice` (%s)" % ", ".join(cot))
	for r in rows:
		r = dict(dict(docstatus=1, vgb_huy=0, vgb_tam_tinh=0, grand_total=100000, custom_hddt_so="",
			custom_minvoice_id="", custom_hddt_id="", vgb_hddt_cho_doi_chieu=0, custom_nguon="Tại chỗ", vgb_quay=""), **r)
		con.execute("insert into `tabSales Invoice` values (%s)" % ", ".join("?" * len(cot)),
			[str(r.get(c)) if isinstance(r.get(c), datetime.date) else r.get(c) for c in cot])

	def sql(q, p=None, as_dict=False, **k):
		cur = con.execute(re.sub(r"%\((\w+)\)s", r":\1", q), {a: str(b) for a, b in (p or {}).items()})
		ra = []
		for x in cur:
			d = _R({c: x[c] for c in x.keys()})
			for c in ("posting_date", "vgb_hddt_ngay_xuat"):
				if d.get(c):
					d[c] = datetime.date.fromisoformat(d[c])
			ra.append(d)
		return ra
	return sql


def _hang_rao_that(rows):
	"""Hàng rào THẬT, hôm nay 25/09, tập nợ đọc bằng câu SQL thật trên sqlite,
	tự đối chiếu THẬT; chỉ giả m-invoice (chay_nen) và phát hành theo lô."""
	vet = []
	bh = NS(_ngay_so_hddt_moi_nhat=lambda: D(2026, 9, 24),
		_khoa_hddt=lambda **kw: vet.append("khoa") or object(),
		_mo_khoa_dong_bo=lambda *a: None, _cong_tac_minvoice=lambda: (1, 1),
		_phat_hanh_theo_lo=lambda d: vet.append(("phat_hanh", d)) or {"tim_thay": 0, "tao_ok": 0, "loi": []},
		_ky_theo_lo=lambda d: {"can_ky": 0, "da_ky": 0, "loi": []})
	f = NS(db=NS(sql=_sql_that(rows)), log_error=lambda *a, **k: None, get_traceback=lambda: "")
	moc = []
	with unittest.mock.patch.object(hddt_cho_xuat, "frappe", f), \
			unittest.mock.patch.object(hddt_cho_xuat, "_cai_dat_minvoice", lambda: ({}, {"Tại chỗ"}, [])), \
			unittest.mock.patch.object(hddt_cho_xuat, "nowdate", lambda: "2026-09-25"), \
			unittest.mock.patch.object(hddt_cho_xuat, "chay_nen", lambda *a, **k: vet.append(("chay_nen",) + a) or {}), \
			unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		g = dict(frappe=unittest.mock.MagicMock(), ngay_cu_can_bao_ve=hddt_cho_xuat.ngay_cu_can_bao_ve,
			ngay_cu_dang_cho=hddt_cho_xuat.ngay_cu_dang_cho, ngay_cu_con_mo=hddt_cho_xuat.ngay_cu_con_mo,
			getdate=hddt_cho_xuat._ngay, nowdate=lambda: "2026-09-25", _ngay_xac_nhan_qua_han=lambda: (),
			cint=lambda x: int(x or 0), _ghi_moc_loi=lambda x: moc.append(x),
			tu_doi_chieu_co=hddt_cho_xuat.tu_doi_chieu_co)
		fn = _nap("hddt_cho_xuat.py", "xuat_ngay_cu_truoc", g)
		ra = fn()
	return ra, vet, moc


@ca("v527 Codex vòng 4: tờ 24/09 đã kéo ngày lập sang hôm nay mà giữ cờ thì KHÔNG chặn tờ hôm nay (trước: chặn tới cuối ngày)")
def _v4_keo_hom_nay_khong_chan():
	ra, vet, moc = _hang_rao_that([{"name": "SI-KEO", "posting_date": D(2026, 9, 24),
		"vgb_hddt_ngay_xuat": D(2026, 9, 25), "vgb_hddt_cho_doi_chieu": 1}])
	la("cho tờ hôm nay đi", ra, True)
	la("không lấy khoá, không phát hành ngày cũ", [v for v in vet if v == "khoa" or v[0] == "phat_hanh"], [])
	# Đối chứng 1: tờ 24/09 giữ cờ, chưa kéo ngày: vẫn là nợ ngày cũ, máy
	# thử tự đối chiếu đúng ngày 24/09, m-invoice chưa trả lời thì vẫn chặn.
	ra, vet, moc = _hang_rao_that([{"name": "SI-GIU", "posting_date": D(2026, 9, 24),
		"vgb_hddt_ngay_xuat": None, "vgb_hddt_cho_doi_chieu": 1}])
	la("tờ cũ chưa kéo ngày vẫn chặn", ra, False)
	dung("và có thử tự đối chiếu 24/09", any(v[0] == "chay_nen" and v[1] == "2026-09-24" for v in vet if isinstance(v, tuple)))
	# Đối chứng 2: tờ 24/09 đã đặt ngày lập 24/09 (không phải hôm nay), chưa
	# ra: vẫn là nợ ngày cũ, và hàng rào phát hành đúng ngày 24/09.
	ra, vet, moc = _hang_rao_that([{"name": "SI-HQ", "posting_date": D(2026, 9, 24),
		"vgb_hddt_ngay_xuat": D(2026, 9, 24), "vgb_hddt_cho_doi_chieu": 0}])
	la("ngày lập 24/09 chưa ra: vẫn chặn, có phát hành 24/09", (ra, ("phat_hanh", "2026-09-24") in vet), (False, True))
