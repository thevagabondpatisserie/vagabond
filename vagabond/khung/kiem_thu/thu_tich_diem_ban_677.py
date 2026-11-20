# -*- coding: utf-8 -*-
"""v677: tích điểm cho hoá đơn gọi món tại bàn (Dễ báo 20/11/2026, anh Việt
chọn phương án A: khách đăng nhập Zalo tự gắn, quầy gắn ở bill Tạm tính).

Ca chạm hệ chạy HÀM THẬT tich_diem_ban.gan, gan_quay và uu_dai_ban.ds, chỉ
thay tầng Frappe bằng hoá đơn giả (cùng lớp HoaDon của ca v643). ban_hang và
khach_hang nạp requests ở đầu tệp nên ca thay chúng bằng mô đun giả, để CI tay
không vẫn chạy.
"""

import contextlib
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import vagabond
from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import thanh_vien  # noqa: E402
from vagabond import tich_diem_ban as t  # noqa: E402
from vagabond import uu_dai_ban as u  # noqa: E402
from vagabond.khung.kiem_thu.thu_uu_dai_ban_643 import _ban, _hd  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
SDT = "0909123412"
KHACH = "CUST-0001"
KHACH_LE = "Khách lẻ Online"


def _gop(ma):
	m = (ma or "").strip()
	return (not m) or m in (KHACH_LE, "Khách bán lẻ")


class _Loi(Exception):
	pass


def _nem(msg, *a, **k):
	raise _Loi(msg)


@contextlib.contextmanager
def _khach(sdt=SDT, khach=KHACH, ly="", tao=None):
	"""Phiên Thành viên của sdt (None là chưa đăng nhập); _khach_hoac_tao trả
	(khach, ly) và ghi lại người đang đăng nhập lúc tạo."""
	goi = tao if tao is not None else []

	def kht(so, ten=""):
		goi.append(_fr.session.user)
		return (khach, ly) if khach else (None, ly or "khong_tao_duoc")
	dn = types.SimpleNamespace(_sdt_noi_dia=lambda so: so)
	with patch.object(thanh_vien, "_so_phien", return_value=sdt), \
			patch.object(thanh_vien, "_dn", return_value=dn), \
			patch.object(thanh_vien, "_khach_hoac_tao", side_effect=kht), \
			patch.object(t, "_la_gop", side_effect=_gop):
		yield goi


@ca("v677 tích điểm thuần: bill khách chung là còn trống, của tôi là đã gắn, của khách thật khác là khác; ưu đãi của số khác")
def _thuan():
	la("khách chung", [t.trang_thai(KHACH_LE, KHACH, True), t.trang_thai("", KHACH, False)], ["trong", "trong"])
	la("đã của tôi", t.trang_thai(KHACH, KHACH, False), "gan")
	la("của người khác", [t.trang_thai("CUST-0002", KHACH, False), t.trang_thai("CUST-0002", None, False)], ["khac", "khac"])
	la("ưu đãi số khác", [t.ud_cua_so_khac({"sdt": "0912000111"}, SDT), t.ud_cua_so_khac({"sdt": "+84 909 123 412"}, SDT),
		t.ud_cua_so_khac({}, SDT), t.ud_cua_so_khac(None, SDT)], [True, False, False, False])
	la("thẻ không lộ mã khách", t.the_tv("gan", SDT), {"trang_thai": "gan", "sdt": "0909 *** 412"})


@ca("v677 khách gắn số vào hoá đơn bàn: khoá hoá đơn trước khi đọc, lưu bằng quyền hệ thống, trả lại Guest, ghi vết; gọi lại không lưu nữa")
def _gan():
	si = _hd(customer=KHACH_LE)
	with _ban(si), _khach() as tao:
		goc = u._hoa_don_ban

		def doc(d, n, khoa=False):
			khoa_ds.append(khoa)
			return goc(d, n, khoa=khoa)
		khoa_ds = []
		with patch.object(u, "_hoa_don_ban", side_effect=doc):
			r = t.gan("TCV", 5, "k")
		la("gắn được", (r["ok"], r["tv"]), (1, {"trang_thai": "gan", "sdt": "0909 *** 412"}))
		la("đọc hoá đơn có khoá", khoa_ds, [True])
		la("bill đứng tên khách thành viên", (si.customer, si.luu), (KHACH, 1))
		la("lưu và tạo khách bằng quyền hệ thống", (si.luu_boi, tao), ("Administrator", ["Administrator"]))
		la("trả lại Guest", _fr.session.user, "Guest")
		la("ghi vết che số", si.ghi_chu, ["Khách tự gắn số 0909 *** 412 qua Zalo tại bàn 5 để tích điểm."])
		r = t.gan("TCV", 5, "k")
		la("bấm lại: vẫn đã gắn, không lưu thêm", (r["ok"], si.luu, len(si.ghi_chu)), (1, 1, 1))
	with _ban(si, sdt="0912000111", khach="CUST-0002"), _khach(sdt="0912000111", khach="CUST-0002"):
		r = t.gan("TCV", 5, "k")
	la("số khác sau đó: báo, không đổi", (r["ok"], r["tv"]["trang_thai"], si.customer, si.luu), (0, "khac", KHACH, 1))


@ca("v677 khách gắn số: link sai, chưa đăng nhập, bàn chưa có hoá đơn, số cần đối chiếu, hoá đơn đã dùng ưu đãi của số khác thì không gắn")
def _gan_chan():
	with _ban(None, link=False), _khach():
		la("link sai", t.gan("TCV", 5, "x")["cau"], t.CAU_LINK)
	si = _hd(customer=KHACH_LE)
	with _ban(si), _khach(sdt=None):
		r = t.gan("TCV", 5, "k")
	la("chưa đăng nhập", (r["ok"], r["dang_nhap"]), (0, 0))
	with _ban(None), _khach():
		r = t.gan("TCV", 5, "k")
	la("chờ quầy nhận món", (r["ok"], r["cho"], r["cau"]), (0, 1, t.CAU_CHO_HD))
	with _ban(si), _khach(khach=None, ly="can_doi_chieu"):
		r = t.gan("TCV", 5, "k")
	la("nhiều hồ sơ cùng số", (r["ok"], r["cau"]), (0, t.CAU_DOI_CHIEU))
	si2 = _hd(customer=KHACH_LE, vgb_ud_ban='{"loai":"ma","ma":"VC-8K2Q","sdt":"0912000111","khach":"CUST-0002","giam":18500}')
	with _ban(si2), _khach():
		r = t.gan("TCV", 5, "k")
	la("ưu đãi của số khác", (r["ok"], r["tv"]["trang_thai"]), (0, "khac"))
	la("không lưu gì", (si.luu, si.customer, si2.luu, si2.customer), (0, KHACH_LE, 0, KHACH_LE))
	si3 = _hd(customer=KHACH_LE, vgb_ud_ban='{"loai":"ma","ma":"VC-8K2Q","sdt":"%s","khach":"%s","giam":18500}' % (SDT, KHACH))
	with _ban(si3), _khach():
		r = t.gan("TCV", 5, "k")
	la("ưu đãi của chính số đó thì gắn", (r["ok"], si3.customer), (1, KHACH))


@ca("v677 danh sách ưu đãi kèm trạng thái tích điểm: chờ hoá đơn, còn trống, đã gắn, của số khác")
def _ds_tv():
	kq = []
	for si in (None, _hd(customer=KHACH_LE), _hd(customer=KHACH), _hd(customer="CUST-0002")):
		with _ban(si), _khach():
			kq.append(u.ds("TCV", 5, "k")["tv"]["trang_thai"])
	la("bốn trạng thái", kq, ["cho", "trong", "gan", "khac"])


@contextlib.contextmanager
def _quay(si, tim_sdt="", tao=""):
	bh = types.ModuleType("vagabond.ban_hang")
	bh.quyen = []
	bh._kiem_quyen_ban = lambda: bh.quyen.append(1)
	bh._khach_le = lambda: KHACH_LE
	nk = types.ModuleType("vagabond.nhap_khach")
	nk.goi = []

	def chuan(s):
		so = "".join(c for c in str(s or "") if c.isdigit())
		return so if len(so) == 10 and so.startswith("0") else ""
	nk.sdt_chuan = chuan

	def cho_don(sdt, ten="", nguon=""):
		nk.goi.append((sdt, ten, nguon))
		return tim_sdt or tao
	nk.khach_cho_don = cho_don
	co = {KHACH, "CUST-0002", "CUST-MOI", KHACH_LE}
	with patch.dict(sys.modules, {"vagabond.ban_hang": bh, "vagabond.nhap_khach": nk}), \
			patch.object(vagabond, "ban_hang", bh, create=True), patch.object(vagabond, "nhap_khach", nk, create=True), \
			patch.object(t, "_la_gop", side_effect=_gop), \
			patch.object(_fr, "get_doc", side_effect=lambda dt, n, for_update=False: (khoa.append(for_update), si)[1]), \
			patch.object(_fr.db, "exists", side_effect=lambda dt, n: n in co, create=True), \
			patch.object(_fr.db, "get_value", side_effect=lambda dt, n, f: {"CUST-MOI": "Chị Lan"}.get(n, n), create=True), \
			patch.object(_fr.db, "commit", lambda: None, create=True), \
			patch.object(_fr, "throw", side_effect=_nem):
		khoa = []
		yield bh, nk, khoa


@ca("v677 quầy gắn khách cho bill Tạm tính: chọn khách, tạo khách mới bằng số, gỡ về khách chung; chặn bill đã chốt, khách chung, số sai")
def _gan_quay():
	si = _hd(customer=KHACH_LE)
	with _quay(si) as (bh, nk, khoa):
		r = t.gan_quay(si.name, khach=KHACH)
		la("gắn khách có sẵn, có khoá, có kiểm quyền", (r["ok"], si.customer, si.luu, khoa, bh.quyen), (1, KHACH, 1, [True], [1]))
		la("ghi vết", si.ghi_chu[-1], "Quầy gắn khách %s để tích điểm." % KHACH)
		t.gan_quay(si.name, khach=KHACH)
		la("bấm lại cùng khách: không lưu thêm", si.luu, 1)
		r = t.gan_quay(si.name)
		la("gỡ: về khách chung", (r["khach"], si.customer, si.luu), ("", KHACH_LE, 2))
		nem("khách chung không gắn để tích điểm", lambda: t.gan_quay(si.name, khach="Khách bán lẻ"), _Loi)
		nem("mã không có", lambda: t.gan_quay(si.name, khach="CUST-LA"), _Loi)
		nem("số sai", lambda: t.gan_quay(si.name, sdt="0909"), _Loi)
	with _quay(si, tao="CUST-MOI") as (bh, nk, khoa):
		r = t.gan_quay(si.name, sdt="0912 345 678", ten="Chị Lan")
	la("số mới: tìm hoặc tạo khách theo số", (r, nk.goi, si.customer),
		({"ok": 1, "khach": "CUST-MOI", "ten": "Chị Lan"}, [("0912 345 678", "Chị Lan", "Quầy gắn bill tạm tính")], "CUST-MOI"))
	for x in (dict(docstatus=1), dict(vgb_huy=1), dict(vgb_tam_tinh=0)):
		si2 = _hd(customer=KHACH_LE, **x)
		with _quay(si2):
			nem("bill không phải Tạm tính đang mở %r" % x, lambda: t.gan_quay(si2.name, khach=KHACH), _Loi)
		la("không đổi %r" % x, (si2.customer, si2.luu), (KHACH_LE, 0))


@ca("v677 màn bill Tạm tính (node, mã nguồn thật): khối Khách thành viên tìm, gắn, tạo khách mới bằng số, gỡ, bỏ câu trả lời cũ")
def _bill_js():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/bill_tich_diem_677.js"], cwd=GOC, capture_output=True, text=True, timeout=90)
	la("bill_tich_diem_677.js\n" + r.stdout[-2500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) đạt, 0 hỏng", r.stdout)
	dung("đủ 8 ca", m and int(m.group(1)) >= 8)


UD_A = '{"loai":"ma","ma":"VC-8K2Q","sdt":"0909123412","khach":"CUST-0001","giam":18500}'


@ca("Codex #596 vòng 2: điểm và ưu đãi không thuộc hai người: quầy gắn khách khác chủ ưu đãi bị chặn (gợi bỏ ưu đãi trước); cùng chủ thì gắn; gỡ về khách chung vẫn được")
def _ud_cung_chu_quay():
	la("thuần", [t.lech_chu_ud({"khach": "CUST-0001"}, "CUST-0002"), t.lech_chu_ud({"khach": "CUST-0001"}, "CUST-0001"),
		t.lech_chu_ud({"khach": ""}, "CUST-0001"), t.lech_chu_ud({}, "CUST-0002"), t.lech_chu_ud({"khach": "CUST-0001"}, "")],
		[True, False, True, False, False])
	si = _hd(customer=KHACH_LE, vgb_ud_ban=UD_A)
	with _quay(si):
		try:
			t.gan_quay(si.name, khach="CUST-0002")
			la("phải chặn", 1, 0)
		except _Loi as e:
			la("câu gợi bỏ ưu đãi, che số", ("Bỏ ưu đãi" in str(e), "0909 *** 412" in str(e)), (True, True))
		la("không đổi", (si.customer, si.luu), (KHACH_LE, 0))
		t.gan_quay(si.name, khach=KHACH)
		la("cùng chủ thì gắn", (si.customer, si.luu), (KHACH, 1))
		t.gan_quay(si.name)
		la("gỡ về khách chung được", si.customer, KHACH_LE)
	si2 = _hd(customer=KHACH_LE, vgb_ud_ban=UD_A)
	with _quay(si2, tao="CUST-MOI"):
		nem("tạo khách mới bằng số khác chủ ưu đãi cũng chặn", lambda: t.gan_quay(si2.name, sdt="0912345678"), _Loi)
	la("không đổi", si2.customer, KHACH_LE)


@ca("Codex #596 vòng 2: chiều ngược lại: hoá đơn bàn đã tích điểm cho khách A thì số B không chọn được ưu đãi; khách chung hay chính A thì chọn được")
def _ud_cung_chu_khach():
	si = _hd(customer="CUST-0002")
	with _ban(si), patch.object(t, "_la_gop", side_effect=_gop):
		r = u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("số khác bị từ chối, không lưu", (r["ok"], "số khác" in r.get("cau", ""), si.luu, si.vgb_ud_ban), (0, True, 0, ""))
	for kh in (KHACH, KHACH_LE):
		si = _hd(customer=kh)
		with _ban(si), patch.object(t, "_la_gop", side_effect=_gop):
			r = u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
		la("chọn được khi bill của %s" % kh, (r["ok"], si.luu), (1, 1))


@ca("Codex #596 vòng 2: cửa ghi khách thứ ba (ban_hang.luu_khach_no) cũng giữ cùng chủ ưu đãi")
def _ud_cung_chu_cong_no():
	import ast
	cay = ast.parse((GOC / "vagabond/ban_hang.py").read_text())
	m = types.ModuleType("bh_677")
	gl = m.__dict__
	gl.update(frappe=_fr)
	for n in cay.body:
		if isinstance(n, ast.FunctionDef) and n.name == "luu_khach_no":
			n.decorator_list = []
			exec(compile(ast.Module(body=[n], type_ignores=[]), "ban_hang.py", "exec"), gl)
	gl.update(_kiem_quyen_doc_luu_don=lambda: None, _khach_le=lambda: KHACH_LE, _ghi_vet=lambda *a: None)
	si = _hd(customer=KHACH_LE, vgb_ud_ban=UD_A)
	with _quay(si):
		nem("công nợ gắn khách khác chủ ưu đãi", lambda: m.luu_khach_no(si.name, "CUST-0002"), _Loi)
		la("không đổi", si.customer, KHACH_LE)
		m.luu_khach_no(si.name, KHACH)
		la("cùng chủ được", si.customer, KHACH)
