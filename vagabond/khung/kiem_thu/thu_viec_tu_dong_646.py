# -*- coding: utf-8 -*-
"""v646 Cài đặt tự động hoá: việc máy soạn sẵn (anh Việt duyệt bản vẽ 09/11/2026).

Ca chốt:
  - ô giờ, ô số giờ người gõ tay: mọi cách gõ hợp lý đều nhận, gõ hỏng thì báo
    lỗi rõ ở cửa lưu và dùng mặc định ở cửa đọc (không chạy với giờ rỗng);
  - việc tắt thì nhịp không chạy, việc đã có màn riêng thì luôn bật;
  - nhịp 15 phút: một việc lỗi không chặn việc sau và giao dịch của nó được lùi;
  - quá hạn chỉ báo MỘT lần cho mỗi khoá dù nhịp gọi lại nhiều lượt;
  - phiếu kiểm kê chờ duyệt: quá bậc 1 nhắn nhóm Kho, quá bậc 2 thêm Ban giám đốc
    (đúng chuỗi của vụ Pastry KK-26-00072 tới 00080);
  - tắt việc trong Cài đặt thì nhịp 0h không lập kế hoạch, nhịp 7:30 không nhắn;
  - việc mới trong Việc cần làm đúng vai, mở được trên app;
  - màn app: chạy THẬT mã 69-tu-dong-hoa.js và hàm khsxConLam trong node.
"""

import datetime as dt
import json
import os
import re
import subprocess
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import duong_app  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import viec_can_lam as vcl  # noqa: E402
from vagabond import viec_tu_dong as vtd  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOC, "public", "js", "bep")


def _gio(h, m=0):
	return dt.datetime(2026, 11, 9, h, m)


class BoNho:
	"""Bộ nhớ đệm giả dùng chung giữa các lượt nhịp trong một ca."""

	def __init__(self):
		self.d = {}

	def get_value(self, k, *a, **kw):
		return self.d.get(k)

	def set_value(self, k, v, *a, **kw):
		self.d[k] = v


def _cfg(**sua):
	"""Cấu hình dùng thật với vài giá trị đổi theo mã."""
	dong = [dict(ma=ma, **v) for ma, v in sua.items()]
	return {c["ma"]: c for c in vtd.gop_cau_hinh(dong)}


# ---------------------------------------------------------------- THUẦN


@ca("v646 ô giờ gõ tay: nhận 7, 07, 7h, 7g, 7:5, 19h30, 19g30, 7.30; hỏng thì rỗng")
def _gio_go_tay():
	for vao, ra in (("7", "07:00"), ("07", "07:00"), ("7h", "07:00"), ("7g", "07:00"), ("7:5", "07:05"),
			("19h30", "19:30"), ("19g30", "19:30"), ("7.30", "07:30"), (" 7 : 30 ", "07:30"), ("00:15", "00:15"),
			("22H", "22:00")):
		la("giờ %r" % vao, vtd.chuan_gio(vao), ra)
	for vao in ("24:00", "25:00", "7:60", "abc", "", None, "7h30p30", "-1"):
		la("giờ hỏng %r" % (vao,), vtd.chuan_gio(vao), "")
	for vao, ra in (("24", 24), ("24h", 24), ("24 giờ", 24), ("2 ngày", 48), ("48 tiếng", 48)):
		la("số giờ %r" % vao, vtd.chuan_so_gio(vao), ra)
	for vao in ("0", "", "abc", "-5", "99999"):
		la("số giờ hỏng %r" % vao, vtd.chuan_so_gio(vao), 0)


@ca("v646 cửa sổ chạy: từ đúng giờ hẹn tới trước 60 phút sau, nhịp 15 phút có bốn lượt cơ hội")
def _cua_so():
	dung("đúng giờ", vtd.den_gio("07:00", _gio(7, 0)))
	dung("45 phút sau vẫn trong cửa sổ", vtd.den_gio("07:00", _gio(7, 45)))
	la("60 phút sau đã ngoài", vtd.den_gio("07:00", _gio(8, 0)), False)
	la("trước giờ", vtd.den_gio("07:00", _gio(6, 59)), False)
	la("giờ hỏng không bao giờ chạy", vtd.den_gio("", _gio(7, 0)), False)
	dung("đã qua giờ", vtd.da_qua("19:00", _gio(19, 1)))
	la("chưa qua giờ", vtd.da_qua("19:00", _gio(18, 59)), False)


@ca("v646 cấu hình: ô trống hay gõ hỏng dùng mặc định, việc có màn riêng luôn bật, bậc 2 luôn sau bậc 1")
def _gop():
	c = _cfg()
	la("đủ mười việc", len(c), 10)
	la("mặc định ghi nhận 19:00", c["ghi_nhan_cuoi_ca"]["gio"], "19:00")
	la("yêu cầu mua theo lượng dùng mặc định bật (không cần hạn mức)", c["ycmh_tu_dong"]["bat"], 1)
	la("ngưỡng 3 ngày, mua đủ 7 ngày", (c["ycmh_tu_dong"]["nguong"], c["ycmh_tu_dong"]["du"]), (3, 7))
	c = _cfg(ycmh_tu_dong={"so_ngay_con": 5, "so_ngay_du": 4})
	dung("mua đủ dùng luôn dài hơn ngưỡng", c["ycmh_tu_dong"]["du"] > 5)
	c = _cfg(ghi_nhan_cuoi_ca={"bat": 0, "gio": "18h", "han": "abc"})
	la("tắt", c["ghi_nhan_cuoi_ca"]["bat"], 0)
	la("giờ gõ 18h", c["ghi_nhan_cuoi_ca"]["gio"], "18:00")
	la("hạn gõ hỏng về mặc định", c["ghi_nhan_cuoi_ca"]["han"], "22:00")
	c = _cfg(lenh_tu_ke_hoach={"gio": "03:00"})
	la("giờ cố định không đổi theo bảng", c["lenh_tu_ke_hoach"]["gio"], "00:00")
	c = _cfg(chot_ca={"bat": 0}, khop_tien={"bat": 0})
	la("chốt ca luôn bật", c["chot_ca"]["bat"], 1)
	la("khớp tiền luôn bật", c["khop_tien"]["bat"], 1)
	c = _cfg(duyet_kiem_ke={"han": "36", "han2": "24"})
	la("bậc 1 theo bảng", c["duyet_kiem_ke"]["han"], "36")
	dung("bậc 2 bị đẩy ra sau bậc 1", int(c["duyet_kiem_ke"]["han2"]) > 36)
	la("mã lạ trong bảng bị bỏ", len(vtd.gop_cau_hinh([{"ma": "la", "bat": 1}])), 10)


@ca("v646 cửa lưu: gõ hỏng thì báo lỗi rõ, không lặng lẽ thay bằng mặc định")
def _kiem_luu():
	la("19h", vtd.kiem_luu("ghi_nhan_cuoi_ca", gio="19h"), ({"gio": "19:00"}, ""))
	dung("25:00 bị từ chối", "chưa đúng" in vtd.kiem_luu("ghi_nhan_cuoi_ca", gio="25:00")[1])
	dung("giờ cố định không sửa được", "cố định" in vtd.kiem_luu("lenh_tu_ke_hoach", gio="03:00")[1])
	dung("bậc 2 trước bậc 1 bị từ chối", "phải sau" in vtd.kiem_luu("duyet_kiem_ke", han="48", han2="24")[1])
	la("2 ngày", vtd.kiem_luu("duyet_kiem_ke", han2="2 ngày"), ({"han2": "48"}, ""))
	dung("mã lạ", "Không có" in vtd.kiem_luu("khong_co", gio="7h")[1])


@ca("v646 yêu cầu mua theo lượng dùng: còn đủ dưới 3 ngày thì xin đủ 7 ngày, tính cả hàng đang về, món không ai dùng không xin")
def _can_mua():
	# Dùng 2 kg/ngày, tồn 4 kg: còn 2 ngày (dưới 3) -> xin 7*2 - 4 = 10 kg.
	la("sắp hết", vtd.can_mua_them(4, 0, 2, 3, 7), 10)
	la("hàng đang về đã đủ thì thôi", vtd.can_mua_them(4, 4, 2, 3, 7), 0)
	la("đang về chưa đủ thì xin phần còn thiếu", vtd.can_mua_them(1, 2, 2, 3, 7), 11)
	la("còn đủ đúng 3 ngày thì chưa xin", vtd.can_mua_them(6, 0, 2, 3, 7), 0)
	la("món không ai dùng không bao giờ xin", vtd.can_mua_them(0, 0, 0, 3, 7), 0)
	la("tồn âm trên máy vẫn tính đúng", vtd.can_mua_them(-2, 0, 1, 3, 7), 9)
	la("cửa lưu: 5 và 10 ngày", vtd.kiem_luu("ycmh_tu_dong", so_ngay_con="5", so_ngay_du="10 ngày"),
		({"so_ngay_con": 5, "so_ngay_du": 10}, ""))
	dung("đủ dùng ngắn hơn ngưỡng bị từ chối", "phải lớn hơn" in vtd.kiem_luu("ycmh_tu_dong", so_ngay_con="7", so_ngay_du="5")[1])
	dung("việc khác không có ô số ngày", "không có ô số ngày" in vtd.kiem_luu("chuyen_nvl", so_ngay_con="3")[1])


@ca("v646 sổ đăng ký: chữ tiếng Việt có dấu, không em dash, màn mở có thật trong danh mục màn app")
def _so_dang_ky():
	man = {m[0] for m in duong_app.MAN}
	for v in vtd.VIEC:
		for k in ("ten", "mo", "may", "nguoi"):
			dung("%s.%s có dấu" % (v["ma"], k), any(ord(ch) > 127 for ch in v[k]))
			dung("%s.%s không em dash" % (v["ma"], k), "–" not in v[k] and "—" not in v[k])
		dung("%s mở màn có thật (%s)" % (v["ma"], v["man"]), v["man"] in man)
		dung("%s thuộc bộ phận đã khai" % v["ma"], v["bo_phan"] in vtd.BO_PHAN)
	dung("màn Cài đặt tự động hoá có địa chỉ riêng", "CDTDH" in man)


# ------------------------------------------------------------ PHẦN CHẠM HỆ


def _chay_nhip(cfg, bay, bo_nho, **va):
	"""Chạy một lượt nhịp với cấu hình, đồng hồ, bộ nhớ đệm và các hàm thay cho dữ liệu."""
	tin = []
	vao = dict(va)
	with um.patch.object(vtd, "cau_hinh", lambda: cfg), um.patch.object(vtd, "now_datetime", lambda: bay), \
			um.patch.object(vtd, "_gieo_bang", lambda: 0), \
			um.patch.object(vtd.frappe, "cache", lambda: bo_nho), \
			um.patch.object(vtd.frappe, "set_user", lambda *a: None, create=True), \
			um.patch.object(kz, "bao_hoac_ghi_loi", lambda *a, **k: tin.append(k.get("ma_tin"))):
		with um.patch.multiple(vtd, **vao) if vao else um.MagicMock():
			vtd.chay()
	return tin


@ca("v646 Chốt kế hoạch: quá 07:00 chưa ra lệnh nào thì nhắn nhóm Bếp MỘT lần, đã ra lệnh thì im")
def _chua_chot():
	bo = BoNho()
	cfg = _cfg(chuyen_nvl={"bat": 0}, ycsx_thieu={"bat": 0}, duyet_kiem_ke={"bat": 0}, ghi_nhan_cuoi_ca={"bat": 0})
	kh = lambda: ("MFG-PP-2026-00110", 6, 0)  # noqa: E731
	la("06:55 chưa tới hạn", _chay_nhip(cfg, _gio(6, 55), bo, _ke_hoach_hom_nay=kh), [])
	la("07:00 nhắn", _chay_nhip(cfg, _gio(7, 0), bo, _ke_hoach_hom_nay=kh), ["bep_chua_chot_ke_hoach"])
	la("07:15 không nhắn lại", _chay_nhip(cfg, _gio(7, 15), bo, _ke_hoach_hom_nay=kh), [])
	la("đã ra lệnh thì im", _chay_nhip(cfg, _gio(7, 0), BoNho(), _ke_hoach_hom_nay=lambda: ("P", 6, 3)), [])
	tat = _cfg(lenh_tu_ke_hoach={"bat": 0}, chuyen_nvl={"bat": 0}, ycsx_thieu={"bat": 0},
		duyet_kiem_ke={"bat": 0}, ghi_nhan_cuoi_ca={"bat": 0})
	la("việc tắt thì không nhắn", _chay_nhip(tat, _gio(7, 0), BoNho(), _ke_hoach_hom_nay=kh), [])


@ca("v646 phiếu kiểm kê chờ duyệt (chuỗi vụ Pastry): quá 24 giờ nhắn Kho, quá 48 giờ thêm Ban giám đốc, mỗi bậc một lần")
def _kiem_ke_qua_han():
	bay = _gio(10, 0)
	phieu = [
		{"name": "KK-26-00080", "kho": "Pastry - Nguyên liệu - TV", "ngay_kiem": "2026-11-09", "modified": bay - dt.timedelta(hours=6)},
		{"name": "KK-26-00078", "kho": "Pastry - Nguyên liệu - TV", "ngay_kiem": "2026-11-08", "modified": bay - dt.timedelta(hours=30)},
		{"name": "KK-26-00072", "kho": "Pastry - Nguyên liệu - TV", "ngay_kiem": "2026-11-05", "modified": bay - dt.timedelta(hours=96)},
	]
	from vagabond.khung.kiem_thu.nen import Doi
	cfg = _cfg(lenh_tu_ke_hoach={"bat": 0}, chuyen_nvl={"bat": 0}, ycsx_thieu={"bat": 0}, ghi_nhan_cuoi_ca={"bat": 0})
	bo = BoNho()
	with um.patch.object(vtd.frappe, "get_all", lambda dt_, **k: [Doi(p) for p in phieu] if dt_ == "Phieu Kiem Ke" else []), \
			um.patch.object(vtd, "get_datetime", lambda v: v):
		tin = _chay_nhip(cfg, bay, bo)
		la("00078 nhắn Kho; 00072 nhắn cả Ban giám đốc và Kho; 00080 chưa tới hạn", sorted(tin),
			sorted(["kho_kiem_ke_qua_han", "bgd_kiem_ke_qua_han", "kho_kiem_ke_qua_han"]))
		la("lượt sau không nhắn lại", _chay_nhip(cfg, bay + dt.timedelta(minutes=15), bo), [])


@ca("v646 nhịp: một việc lỗi thì lùi giao dịch của nó và vẫn chạy việc sau")
def _loi_mot_viec():
	goi, lui = [], []

	def hong(c, bay):
		goi.append("hong")
		raise RuntimeError("thu")

	def tot(c, bay):
		goi.append("tot")

	cfg = _cfg()
	with um.patch.object(vtd, "HANH_DONG", (("lenh_tu_ke_hoach", hong), ("ghi_nhan_cuoi_ca", tot), ("don_mua_nhap", tot))), \
			um.patch.object(vtd.frappe.db, "rollback", lambda *a: lui.append(1), create=True):
		_chay_nhip(cfg, _gio(9, 0), BoNho())
	la("việc hỏng chạy, việc sau vẫn chạy, việc đang tắt (yêu cầu mua) không chạy", goi, ["hong", "tot"])
	la("lùi đúng một lần", len(lui), 1)


@ca("v646 tắt việc trong Cài đặt: nhịp 0h không lập kế hoạch, nhịp 7:30 không nhắn đếm")
def _cong_nhip_cu():
	from vagabond import ke_hoach_sx as khsx
	from vagabond import tin_tai_chinh as ttc

	from vagabond import kiem_ke as kk

	# Hai pha dựng CÙNG môi trường (set_user, logger có thật), chỉ khác công tắc.
	# Bản đầu chỉ dựng ở pha bật: pha tắt ném lỗi ở set_user trước khi tới lap
	# nên ca xanh cả khi gỡ cổng (đột biến M7 lọt, sửa ngay trong PR này).
	def _nua_dem(bat):
		lap = []
		with um.patch.object(vtd, "bat", lambda ma: bat), um.patch.object(khsx, "lap", lambda *a, **k: lap.append(1) or {}), \
				um.patch.object(khsx.frappe, "set_user", lambda *a: None, create=True), \
				um.patch.object(khsx.frappe, "logger", lambda *a: um.MagicMock(), create=True):
			khsx.tu_lap_nua_dem()
		return lap

	la("tắt: không lập", _nua_dem(False), [])
	la("bật: lập như cũ", _nua_dem(True), [1])

	def _dem_sang(bat):
		nhan = []
		lich = {"dong": [{"ma_hang": "NVLT00089", "ten": "Bơ lạt", "hang": "A"}], "tong_den_han": 1}
		with um.patch.object(vtd, "bat", lambda ma: bat), um.patch.object(kk, "kho_bep", lambda: ["Pastry - Nguyên liệu - TV"]), \
				um.patch.object(kk, "lich_kho", lambda *a, **k: lich), \
				um.patch.object(ttc, "soan_kiem_ke_sang", lambda *a, **k: ("Kiểm kê sáng", ["Bơ lạt"])), \
				um.patch.object(kz, "bao_hoac_ghi_loi", lambda *a, **k: nhan.append(k.get("ma_tin"))):
			ttc.nhac_kiem_ke_sang()
		return nhan

	la("tắt: không nhắn đếm", _dem_sang(False), [])
	la("bật: nhắn như cũ", _dem_sang(True), ["bep_kiem_ke_sang"])
	with um.patch.object(vtd, "_doc_bang", lambda: (_ for _ in ()).throw(RuntimeError("hong"))):
		dung("đọc cài đặt hỏng thì coi như đang bật", vtd.bat("lenh_tu_ke_hoach"))


@ca("v646 Việc cần làm: chốt kế hoạch cho bếp trưởng, ghi nhận cho tổ bếp, bánh thiếu cho Sales, đúng vai")
def _dung_vai():
	dung("bếp trưởng thấy Chốt kế hoạch", vcl.thay_duoc("ke_hoach_sx", {"Manufacturing Manager"}))
	la("Sales không thấy Chốt kế hoạch", vcl.thay_duoc("ke_hoach_sx", {"Sales User"}), False)
	la("bếp phó không ra lệnh được nên không thấy Chốt", vcl.thay_duoc("ke_hoach_sx", {"Bếp phó"}), False)
	dung("bếp phó thấy Ghi nhận sản lượng", vcl.thay_duoc("ghi_nhan_sx", {"Bếp phó"}))
	dung("Sales thấy Bánh thiếu", vcl.thay_duoc("ycsx_thieu", {"Sales User"}))
	la("kho không thấy Bánh thiếu", vcl.thay_duoc("ycsx_thieu", {"Stock User"}), False)
	la("giám đốc không bị đổ việc bếp", vcl.thay_duoc("ke_hoach_sx", {"AP Giám đốc", "Manufacturing Manager"}), False)
	loai = [x[0] for x in vcl.LOAI_PHIEU]
	for k in ("ke_hoach_sx", "ghi_nhan_sx", "ycsx_thieu"):
		dung("%s có chip" % k, k in loai)


@ca("v646 việc Chốt kế hoạch: có món chưa lệnh thì hiện, quá hạn thì đỏ; việc tắt thì không hiện")
def _viec_ke_hoach():
	with um.patch.object(vtd, "_ke_hoach_hom_nay", lambda: ("PP-1", 4, 0)), um.patch.object(vtd, "_doc_bang", lambda: []):
		with um.patch.object(vtd, "now_datetime", lambda: _gio(6, 0)):
			v = vtd.viec_ke_hoach()
			la("một việc", [x["loai"] for x in v], ["ke_hoach_sx"])
			la("chưa quá hạn", v[0]["tt"], "cho_lam")
		with um.patch.object(vtd, "now_datetime", lambda: _gio(7, 30)):
			la("quá hạn", vtd.viec_ke_hoach()[0]["tt"], "qua_han")
	with um.patch.object(vtd, "_ke_hoach_hom_nay", lambda: ("PP-1", 4, 0)), \
			um.patch.object(vtd, "_doc_bang", lambda: [{"ma": "lenh_tu_ke_hoach", "bat": 0}]):
		la("tắt thì không hiện", vtd.viec_ke_hoach(), [])
	with um.patch.object(vtd, "_ke_hoach_hom_nay", lambda: ("PP-1", 0, 9)), um.patch.object(vtd, "_doc_bang", lambda: []):
		la("đủ lệnh thì không hiện", vtd.viec_ke_hoach(), [])


@ca("v646 việc Ghi nhận sản lượng: chỉ hiện từ giờ chạy và lọc theo bếp của người xem")
def _viec_ghi_nhan():
	bep_nhan = []

	def lenh(bep=""):
		bep_nhan.append(bep)
		return [{"name": "LSX-1"}, {"name": "LSX-2"}]

	with um.patch.object(vtd, "_lenh_hom_nay_chua_ghi", lenh), um.patch.object(vtd, "_doc_bang", lambda: []):
		with um.patch.object(vtd, "now_datetime", lambda: _gio(18, 0)):
			la("18:00 chưa hiện", vtd.viec_ghi_nhan("Bếp Pastry"), [])
		with um.patch.object(vtd, "now_datetime", lambda: _gio(19, 5)):
			v = vtd.viec_ghi_nhan("Bếp Pastry")
	la("19:05 hiện", [x["loai"] for x in v], ["ghi_nhan_sx"])
	dung("ghi số lệnh", "2 lệnh" in v[0]["phu"])
	la("lọc đúng bếp Pastry", bep_nhan, ["pastry"])


# ------------------------------------------------------------- MÀN APP (node)


def _node(ma):
	r = subprocess.run(["node", "-e", ma], capture_output=True, text=True, timeout=30)
	if r.returncode:
		raise AssertionError(r.stderr[-800:])
	return json.loads(r.stdout)


def _nen_js():
	nen = open(os.path.join(BEP, "00-nen.js"), encoding="utf-8").read()
	return re.search(r"^function h\(s\) \{.*\}$", nen, re.M).group(0)


@ca("v646 màn Cài đặt tự động hoá: chạy thật mã app, công tắc chỉ cho người được sửa, việc có màn riêng ghi Luôn chạy")
def _man_app():
	tep = os.path.join(BEP, "69-tu-dong-hoa.js")
	ma = ("var vm=require('vm');var fs=require('fs');var c={};vm.createContext(c);"
		"vm.runInContext(%s,c);vm.runInContext(fs.readFileSync(%s,'utf8'),c);"
		"var x=%s;var y=%s;"
		"process.stdout.write(JSON.stringify({sua:c.tdhThe(x,1),xem:c.tdhThe(x,0),luon:c.tdhThe(y,1),"
		"dem:c.tdhDem([x,y,{bat:0,mau:'r'}]),loc:c.tdhLoc([x,y],'Bếp').map(function(v){return v.ma;})}))") % (
		json.dumps(_nen_js()), json.dumps(tep),
		json.dumps({"ma": "ghi_nhan_cuoi_ca", "bo_phan": "Bếp", "ten": "Ghi nhận sản lượng cuối ca", "mo": "m", "may": "<b>x</b>",
			"nguoi": "n", "o": "trong", "gio": "19:00", "gio_sua": 1, "han_kieu": "luc", "han": "22:00", "mo_ta_han": "Quá 22:00",
			"bat": 1, "man": "MFG", "tinh_hinh": "3 lệnh hôm nay chưa ghi", "mau": "y", "co_san": 0}),
		json.dumps({"ma": "chot_ca", "bo_phan": "Quầy", "ten": "Chốt ca", "mo": "m", "may": "m", "nguoi": "n", "o": "trong",
			"chi_xem": 1, "bat": 1, "man": "POS", "mau": "g", "co_san": 1}))
	r = _node(ma)
	dung("người sửa thấy công tắc", 'data-tdhbat="ghi_nhan_cuoi_ca"' in r["sua"])
	dung("người sửa thấy nút Sửa giờ, hạn", 'data-tdhsua="ghi_nhan_cuoi_ca"' in r["sua"])
	la("người xem không thấy công tắc", 'data-tdhbat' in r["xem"], False)
	la("người xem không thấy nút sửa", 'data-tdhsua' in r["xem"], False)
	dung("nhãn ô số để trống", "Ô số để trống, người nhập" in r["sua"])
	dung("chữ máy chủ được thoát HTML", "&lt;b&gt;x&lt;/b&gt;" in r["sua"])
	dung("việc có màn riêng ghi Luôn chạy", "Luôn chạy" in r["luon"] and "data-tdhbat" not in r["luon"])
	dung("có nút mở màn làm việc", 'data-tdhmo="MFG"' in r["sua"])
	la("đếm bật tắt, đỏ", r["dem"], {"bat": 2, "tat": 1, "do_": 1, "vang": 1})
	la("chip Bếp", r["loc"], ["ghi_nhan_cuoi_ca"])


@ca("v646 nút Chốt kế hoạch: chạy thật khsxConLam, bán thành phẩm trước, lọc theo chip bếp, bỏ món đủ")
def _chot_ke_hoach():
	tep = os.path.join(BEP, "38-ke-hoach-sx.js")
	d = {"co_phieu": 1,
		"thanh_pham": [{"khoa": "t1", "con_lam": 6, "bep": "pastry"}, {"khoa": "t2", "con_lam": 0, "bep": "pastry"},
			{"khoa": "t3", "con_lam": 2, "bep": "baker"}],
		"btp": [{"khoa": "b1", "con_lam": 1.5, "bep": "pastry"}]}
	ma = ("var vm=require('vm');var fs=require('fs');var c={};vm.createContext(c);"
		"vm.runInContext(fs.readFileSync(%s,'utf8'),c);var d=%s;"
		"process.stdout.write(JSON.stringify({ca:c.khsxConLam(d,''),pastry:c.khsxConLam(d,'pastry'),"
		"trong:c.khsxConLam({co_phieu:0},'')}))") % (json.dumps(tep), json.dumps(d))
	r = _node(ma)
	la("cả hai bếp, bán thành phẩm trước", r["ca"], [{"khoa": "b1", "loai": "btp"}, {"khoa": "t1", "loai": "tp"},
		{"khoa": "t3", "loai": "tp"}])
	la("chip Pastry", [x["khoa"] for x in r["pastry"]], ["b1", "t1"])
	la("chưa có phiếu", r["trong"], [])


@ca("v646 ô Thực tế cân được để trống, bấm Hoàn thành khi trống thì bị giữ lại (luật ô số anh duyệt)")
def _o_can_trong():
	m = open(os.path.join(BEP, "05-san-xuat.js"), encoding="utf-8").read()
	doan = m.split("function mfgSheetHoanTat(")[1].split("\n}\n")[0]
	# Chạy thật tấm nhập số với DOM giả tối thiểu: bấm Hoàn thành khi ô cân trống.
	ma = r"""
var vm=require('vm');var c={};vm.createContext(c);
var nut={};function El(id,val){this.id=id;this.value=val;this.style={};this.textContent='';}
El.prototype.focus=function(){};
var dsEl={};
c.toast=function(t){c._toast=t;};c.h=function(s){return String(s==null?'':s);};c.num=function(x){return String(x);};
c.r3=function(x){return Math.round(x*1000)/1000;};c.mfgNhoCua=function(){return null;};
c.document={createElement:function(){var ov={className:'',innerHTML:'',remove:function(){ov.da=1;},
  querySelector:function(q){var id=q.replace('#','');if(!dsEl[id]){var m=new RegExp('id="'+id+'" value="([^"]*)"').exec(ov.innerHTML);dsEl[id]=new El(id,m?m[1]:'');}return dsEl[id];},
  addEventListener:function(){} };c._ov=ov;return ov;},body:{appendChild:function(){}}};
vm.runInContext('function mfgSheetHoanTat('+%s+'\n}',c);
var p=c.mfgSheetHoanTat(5,'Cái',null,'M');
var ov=c._ov;
function bam(attr){var t={hasAttribute:function(a){return a===attr;},closest:function(){return null;}};ov.onclick({target:t});}
bam('data-y');
var giu={toast:c._toast||'',dong:!!ov.da,can:dsEl.htCan.value,lenh:dsEl.htLenh.value};
dsEl.htCan.value='4.5';bam('data-y');
p.then(function(r){process.stdout.write(JSON.stringify({giu:giu,ra:r}));});
""" % json.dumps(doan)
	r = _node(ma)
	la("ô cân mở ra trống", r["giu"]["can"], "")
	la("ô số theo lệnh vẫn là số còn lại", r["giu"]["lenh"], "5")
	dung("trống thì nhắc nhập", "Nhập số cân" in r["giu"]["toast"])
	la("trống thì tấm chưa đóng", r["giu"]["dong"], False)
	la("nhập rồi mới trả số", r["ra"], {"theo_lenh": 5, "thuc_te": 4.5, "dvt": "Cái", "he_so": 1})


# ------------------------------------------------- THU MUA: gom yêu cầu mua (v646)

from vagabond import gom_mua as gm  # noqa: E402


@ca("v646 gom mua: chia số mua xuống từng phiếu xin, cần sớm được trước, mua dôi vào dòng cuối, 0 là cả nhóm 0")
def _chia_so():
	ds = [{"ten": "a", "xin": 5}, {"ten": "b", "xin": 3}, {"ten": "c", "xin": 2}]
	la("đúng tổng xin", gm.chia_so(ds, 10), {"a": 5, "b": 3, "c": 2})
	la("mua ít hơn: dòng đầu trước", gm.chia_so(ds, 6), {"a": 5, "b": 1, "c": 0})
	la("mua chẵn thùng: dôi vào dòng cuối", gm.chia_so(ds, 12), {"a": 5, "b": 3, "c": 4})
	la("mua 0", gm.chia_so(ds, 0), {"a": 0, "b": 0, "c": 0})
	la("một dòng nhận hết", gm.chia_so([{"ten": "a", "xin": 5}], 7), {"a": 7})


@ca("v646 gom mua: nhóm theo nhà cung cấp, cộng các phiếu cùng món, số mua điền sẵn bằng tổng xin, nhóm chưa có nhà cung cấp đứng cuối")
def _gom():
	dong = [
		{"ten": "r1", "phieu": "YCMH-1", "ma": "BO", "ten_mon": "Bơ lạt", "xin": 5000, "dvt": "Gram", "ngay": "2026-11-11", "bo_phan": "Bếp Pastry"},
		{"ten": "r2", "phieu": "YCMH-2", "ma": "BO", "ten_mon": "Bơ lạt", "xin": 3000, "dvt": "Gram", "ngay": "2026-11-10", "bo_phan": "Bếp Baker"},
		{"ten": "r3", "phieu": "YCMH-2", "ma": "LY", "ten_mon": "Ly giấy", "xin": 200, "dvt": "Cái", "ngay": "2026-11-12", "bo_phan": "Quầy"},
		{"ten": "r4", "phieu": "YCMH-3", "ma": "XX", "ten_mon": "Món lạ", "xin": 1, "dvt": "Cái", "ngay": "", "bo_phan": ""},
	]
	g = gm.gom(dong, {"BO": "NCC-A", "LY": "NCC-B"}, {"BO": {"ton": 1200, "cho_ve": 0}}, {"BO": 0.25}, {}, {"NCC-A": "Nhà A", "NCC-B": "Nhà B"})
	la("ba nhóm, chưa có nhà cung cấp cuối", [x["ncc"] for x in g], ["NCC-A", "NCC-B", ""])
	bo = g[0]["mon"][0]
	la("cộng hai phiếu", bo["xin"], 8000)
	la("số mua điền sẵn bằng tổng xin", bo["mua"], 8000)
	la("ngày cần sớm nhất", bo["ngay_can"], "2026-11-10")
	la("giữ từng phiếu xin, cần sớm trước", [p["phieu"] for p in bo["phieu"]], ["YCMH-2", "YCMH-1"])
	la("tồn kho tổng", bo["ton"], 1200)
	la("tạm tính", g[0]["tien"], 2000)
	la("tên nhóm chưa có nhà cung cấp", g[2]["ten_ncc"], "Chưa có nhà cung cấp")
	la("nhà cung cấp: mặc định trước", gm.chon_ncc("BO", {"BO": "A"}, {"BO": "B"}, {"BO": "C"}), "A")
	la("rồi nhà cung cấp khai trên món", gm.chon_ncc("BO", {}, {"BO": "B"}, {"BO": "C"}), "B")
	la("rồi đơn mua gần nhất", gm.chon_ncc("BO", {}, {}, {"BO": "C"}), "C")
	la("số gửi lên hỏng", gm.doc_dong_chot('[{"ma":"BO","sl":"abc"}]')[0], None)
	la("số âm", gm.doc_dong_chot([{"ma": "BO", "sl": -1}])[0], None)
	la("dấu phẩy thập phân", gm.doc_dong_chot([{"ma": "BO", "sl": "2,5"}]), ({"BO": 2.5}, ""))


class _Dong(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


class _Phieu:
	def __init__(self, ten, items):
		self.name, self.items = ten, items
		self.flags = _Dong()
		self.luu = 0

	def save(self):
		self.luu += 1


class _Don:
	def __init__(self, hong_ghi_so=False, hong_lap=False):
		self.items, self.flags, self.name = [], _Dong(), "PUR-ORD-2026-00999"
		self.hong_ghi_so, self.hong_lap = hong_ghi_so, hong_lap
		self.da_ghi_so = 0

	def append(self, bang, d):
		self.items.append(_Dong(d))

	def insert(self):
		if self.hong_lap:
			raise RuntimeError("lap hong")

	def submit(self):
		if self.hong_ghi_so:
			raise RuntimeError("Thiếu giá")
		self.da_ghi_so = 1


def _chot(dong, ncc_map, phieu, don, so, ncc="NCC-A"):
	lui, vet = [], []
	from vagabond import duyet_ycmh as dy
	with um.patch.object(gm, "_kiem_quyen", lambda: None), \
			um.patch.object(gm, "dong_cho_gom", lambda ma=None: [dict(d) for d in dong]), \
			um.patch.object(gm, "_ncc_cua", lambda m: (ncc_map, {})), \
			um.patch.object(gm, "_gia_anh", lambda m: ({"BO": 0.25}, {})), \
			um.patch.object(gm.frappe, "get_doc", lambda dt_, ten, **k: phieu[ten]), \
			um.patch.object(gm.frappe, "new_doc", lambda dt_: don), \
			um.patch.object(gm.frappe.db, "exists", lambda *a, **k: True), \
			um.patch.object(gm.frappe.db, "rollback", lambda *a, **k: lui.append(k.get("save_point")), create=True), \
			um.patch.object(gm.frappe.utils, "strip_html", lambda x: x, create=True), \
			um.patch.object(dy, "_ghi_vet", lambda ten, viec: vet.append((ten, viec))):
		try:
			return gm.chot(ncc, json.dumps(so)), lui, vet
		except Exception as e:
			return {"loi": str(e)}, lui, vet


def _du_lieu():
	dong = [
		{"ten": "r2", "phieu": "YCMH-2", "ma": "BO", "xin": 3000, "cf": 1000, "uom": "Kg", "dvt": "Gram", "kho": "Kho tổng 307 - TV",
			"ngay": "2026-11-10", "cong_ty": "TV"},
		{"ten": "r1", "phieu": "YCMH-1", "ma": "BO", "xin": 5000, "cf": 1000, "uom": "Kg", "dvt": "Gram", "kho": "Kho tổng 307 - TV",
			"ngay": "2026-11-11", "cong_ty": "TV"},
	]
	phieu = {
		"YCMH-1": _Phieu("YCMH-1", [_Dong(name="r1", qty=5, ordered_qty=0, conversion_factor=1000, item_code="BO", item_name="Bơ lạt")]),
		"YCMH-2": _Phieu("YCMH-2", [_Dong(name="r2", qty=3, ordered_qty=0, conversion_factor=1000, item_code="BO", item_name="Bơ lạt")]),
	}
	return dong, phieu


@ca("v646 gom mua Chốt: ghi phần duyệt lên đúng từng dòng phiếu xin (giữ số xin), lập đơn mua nối về từng dòng, xác nhận đơn")
def _chot_dung():
	dong, phieu = _du_lieu()
	don = _Don()
	r, lui, vet = _chot(dong, {"BO": "NCC-A"}, phieu, don, [{"ma": "BO", "sl": 6000}])
	r1, r2 = phieu["YCMH-1"].items[0], phieu["YCMH-2"].items[0]
	la("phiếu cần sớm (YCMH-2) được đủ 3 kg", r2.sl_duyet, 3)
	la("phiếu sau nhận phần còn lại 3 kg", r1.sl_duyet, 3)
	la("số xin của nhân viên giữ nguyên", (r1.qty, r2.qty), (5, 3))
	dung("có người duyệt", bool(r1.nguoi_duyet_dong) and bool(r2.nguoi_duyet_dong))
	la("đơn hai dòng, mỗi dòng nối về đúng dòng xin", sorted((x.material_request, x.material_request_item, x.qty) for x in don.items),
		[("YCMH-1", "r1", 3), ("YCMH-2", "r2", 3)])
	la("giá theo đơn vị mua (0,25 đ/gram x 1000)", don.items[0].rate, 250)
	la("đơn cho đúng nhà cung cấp", don.supplier, "NCC-A")
	la("đã xác nhận", (r.get("da_xac_nhan"), don.da_ghi_so), (1, 1))
	la("ghi vết hai phiếu", sorted(v[0] for v in vet), ["YCMH-1", "YCMH-2"])


@ca("v646 gom mua Chốt: gõ 0 là từ chối có lý do, không lập đơn; đơn thiếu giá thì để NHÁP chứ không mất phần duyệt")
def _chot_0_va_nhap():
	dong, phieu = _du_lieu()
	r, lui, vet = _chot(dong, {"BO": "NCC-A"}, phieu, _Don(), [{"ma": "BO", "sl": 0}])
	la("từ chối cả hai dòng", [phieu[p].items[0].sl_duyet for p in ("YCMH-1", "YCMH-2")], [0, 0])
	dung("có lý do", "chưa mua đợt này" in (phieu["YCMH-1"].items[0].ly_do_duyet or ""))
	la("không lập đơn", r.get("don"), "")
	dong, phieu = _du_lieu()
	don = _Don(hong_ghi_so=True)
	r, lui, vet = _chot(dong, {"BO": "NCC-A"}, phieu, don, [{"ma": "BO", "sl": 8000}])
	la("đơn còn nháp", (r.get("da_xac_nhan"), r.get("don")), (0, "PUR-ORD-2026-00999"))
	dung("nói rõ lý do", "NHÁP" in r.get("ghi_chu", "") and "Thiếu giá" in r.get("ghi_chu", ""))
	la("chỉ lùi bước xác nhận", lui, ["gom_mua_ghi_so"])
	la("phần duyệt vẫn giữ", phieu["YCMH-1"].items[0].sl_duyet, 5)


@ca("v646 gom mua Chốt: lập đơn hỏng thì lùi cả phần duyệt; dòng vừa có người duyệt thì từ chối chốt; món không thuộc nhóm thì từ chối")
def _chot_hong():
	dong, phieu = _du_lieu()
	r, lui, vet = _chot(dong, {"BO": "NCC-A"}, phieu, _Don(hong_lap=True), [{"ma": "BO", "sl": 8000}])
	dung("báo lỗi", "loi" in r)
	la("lùi về trước lúc ghi duyệt", lui, ["gom_mua_chot"])
	dong, phieu = _du_lieu()
	phieu["YCMH-2"].items[0].nguoi_duyet_dong = "uyen@vagabond"
	r, lui, vet = _chot(dong, {"BO": "NCC-A"}, phieu, _Don(), [{"ma": "BO", "sl": 8000}])
	dung("dòng vừa được duyệt thì dừng", "vừa được người khác duyệt" in r.get("loi", ""))
	dong, phieu = _du_lieu()
	r, lui, vet = _chot(dong, {"BO": "NCC-B"}, phieu, _Don(), [{"ma": "BO", "sl": 8000}], ncc="NCC-A")
	dung("món đã sang nhóm khác thì dừng", "không còn dòng chờ gom ở nhóm này" in r.get("loi", ""))


@ca("v646 Việc cần làm Thu mua: gom yêu cầu mua cho thu mua, phiếu máy soạn cho người giữ kho")
def _vai_thu_mua():
	dung("thu mua thấy Gom", vcl.thay_duoc("gom_mua", {"Purchase User"}))
	la("kho không thấy Gom", vcl.thay_duoc("gom_mua", {"Stock User"}), False)
	dung("kho thấy phiếu máy soạn", vcl.thay_duoc("ycmh_nhap", {"Stock User"}))
	la("Sales không thấy", vcl.thay_duoc("ycmh_nhap", {"Sales User"}), False)
	with um.patch.object(vtd, "_doc_bang", lambda: []):
		la("không giữ kho, không phải thu mua: không có việc", vtd.viec_ycmh_nhap([], False), [])


@ca("v646 màn Gom yêu cầu mua: chạy thật mã app, số gõ thắng số máy, chốt gửi đúng mã món và số")
def _man_gom():
	tep = os.path.join(BEP, "70-gom-mua.js")
	nhom = {"ncc": "NCC-A", "mon": [{"ma": "BO", "mua": 8000, "xin": 8000, "gia": 0.25}, {"ma": "SUA", "mua": 12, "xin": 12, "gia": 30000}]}
	ma = ("var vm=require('vm');var fs=require('fs');var c={};vm.createContext(c);"
		"vm.runInContext(fs.readFileSync(%s,'utf8'),c);var g=%s;"
		"var a=c.gmDongChot(g),ta=c.gmTien(g);c.GM.sua.BO=6000;c.GM.sua.SUA=0;"
		"process.stdout.write(JSON.stringify({a:a,ta:ta,b:c.gmDongChot(g),tb:c.gmTien(g)}))") % (json.dumps(tep), json.dumps(nhom))
	r = _node(ma)
	la("chưa gõ: theo số máy", r["a"], [{"ma": "BO", "sl": 8000}, {"ma": "SUA", "sl": 12}])
	la("tạm tính", r["ta"], 362000)
	la("gõ rồi: theo số gõ, kể cả 0", r["b"], [{"ma": "BO", "sl": 6000}, {"ma": "SUA", "sl": 0}])
	la("tạm tính theo số gõ", r["tb"], 1500)
