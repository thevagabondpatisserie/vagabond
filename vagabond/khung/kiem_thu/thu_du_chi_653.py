# -*- coding: utf-8 -*-
"""v653 Dự chi công nợ (issue #555, anh Việt duyệt bốn ảnh 12/11/2026).

Ca chốt:
  - THUẦN: ngày đợt 10 và 20 (qua tháng, qua năm, tháng Hai), ngày soạn 7 và 17,
    mã đợt, số ngày được nợ gợi từ lịch sử (dưới ba lần thì chưa gợi), hạn dự
    tính, số máy điền sẵn, ca 100/60/40 của bảng tay, hai người duyệt khác nhau;
  - lưu: khoá hoá đơn TRƯỚC khi đọc dư nợ và phần APP khác giữ (H8 loại 1),
    số vượt thì báo đúng hoá đơn, đợt đã gửi thì không sửa được;
  - duyệt: người lập không tự duyệt, hai cấp là hai người, trả lại phải có lý do;
  - chốt: giám đốc bấm duyệt thì APP vẫn lập đứng tên Uyên và phiên trả về
    giám đốc; một nhà cung cấp lỗi không chặn nhà khác, chốt lại không lập
    trùng APP (nhận lại APP đã lập theo ghi chú đợt);
  - nhịp ngày 7 và 17: chưa tới ngày thì không soạn, tới ngày thì soạn và nhắn
    nhóm Thu mua một lần;
  - Việc cần làm đúng bước của từng vai;
  - màn app: chạy THẬT 71-du-chi.js trong node (hanh_vi/du_chi_653.js).
"""

import datetime as dt
import os
import subprocess
import types
import unittest.mock as um
from decimal import Decimal

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

fr = gia_lap()
# Chạy riêng tệp này (không qua chay.py) thì bản giả chưa có get_url mà kenh_zalo cần.
if not hasattr(fr.utils, "get_url"):
	fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import du_chi as dc  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = dt.date


# ------------------------------------------------------------------ THUẦN

@ca("v653 ngày đợt 10 và 20: đúng ngày đợt vẫn là đợt đó, qua 20 sang 10 tháng sau, qua năm")
def _ngay_dot():
	la("12/11 tới đợt 20/11", dc.ngay_dot_ke_tiep(D(2026, 11, 12)), D(2026, 11, 20))
	la("đúng 10/11 là đợt 10/11", dc.ngay_dot_ke_tiep(D(2026, 11, 10)), D(2026, 11, 10))
	la("21/11 sang 10/12", dc.ngay_dot_ke_tiep(D(2026, 11, 21)), D(2026, 12, 10))
	la("31/12 sang 10/01 năm sau", dc.ngay_dot_ke_tiep(D(2026, 12, 31)), D(2027, 1, 10))
	la("28/02 sang 10/03", dc.ngay_dot_ke_tiep(D(2027, 2, 28)), D(2027, 3, 10))
	la("soạn đợt 10 ngày 7", dc.ngay_soan(D(2026, 12, 10)), D(2026, 12, 7))
	la("soạn đợt 20 ngày 17", dc.ngay_soan("2026-11-20"), D(2026, 11, 17))
	la("mã đợt", dc.ma_dot(D(2026, 12, 10)), "DC-26-12-10")


@ca("v653 số ngày được nợ: Uyên khai thì theo khai, chưa thì gợi theo lịch sử (từ ba lần), chưa có thì 30")
def _so_ngay_no():
	la("dưới ba lần trả thì chưa gợi", dc.goi_y_so_ngay_no([("2026-09-01", "2026-09-15"), ("2026-09-05", "2026-09-30")]), None)
	cap = [("2026-09-01", "2026-09-15"), ("2026-09-05", "2026-10-05"), ("2026-09-10", "2026-10-30"), ("2026-10-01", "2026-09-20")]
	la("trung vị 14, 30, 50 là 30; trả trước ngày hoá đơn không tính", dc.goi_y_so_ngay_no(cap), 30)
	la("đã khai 45", dc.so_ngay_dung(45, 30), (45, "khai"))
	la("khai 0 là theo gợi ý", dc.so_ngay_dung(0, 30), (30, "goi_y"))
	la("ô khai gõ hỏng không làm vỡ", dc.so_ngay_dung("abc", None), (30, "mac_dinh"))
	la("hạn dự tính = ngày hoá đơn + số ngày", dc.han_du_tinh("2026-10-20", 30), D(2026, 11, 19))
	la("không ngày hoá đơn thì không hạn", dc.han_du_tinh(None, 30), None)


@ca("v653 số máy điền sẵn và ca 100/60/40 của bảng tay anh Việt")
def _goi_y_tra():
	la("tới hạn trước ngày đợt thì đề nghị trả hết", dc.goi_y_tra(100, "2026-11-19", "2026-11-20"), Decimal(100))
	la("hạn đúng ngày đợt cũng trả hết", dc.goi_y_tra(100, "2026-11-20", "2026-11-20"), Decimal(100))
	la("chưa tới hạn để 0", dc.goi_y_tra(100, "2026-11-21", "2026-11-20"), Decimal(0))
	la("còn 100 triệu, trả 60 thì gia hạn 40", dc.kiem_so_tra(60000000, 100000000), (Decimal(60000000), Decimal(40000000)))
	la("trả 0 thì gia hạn cả", dc.kiem_so_tra("", 50), (Decimal(0), Decimal(50)))
	try:
		dc.kiem_so_tra(120, 100)
		loi = ""
	except ValueError as e:
		loi = str(e)
	dung("vượt thì câu lỗi nói việc làm tiếp", "giảm số trả" in loi and "120" in loi)
	nem("số âm bị chặn", lambda: dc.kiem_so_tra(-1, 100), ValueError)
	nem("chữ bị chặn", lambda: dc.kiem_so_tra("sáu mươi", 100), ValueError)
	dong = [{"nha_cung_cap": "A", "so_tra": 10}, {"nha_cung_cap": "B", "so_tra": 0},
		{"nha_cung_cap": "A", "so_tra": 5, "ho_so_app": "APP.1"}, {"nha_cung_cap": "C", "so_tra": 1}, {"nha_cung_cap": "A", "so_tra": 2}]
	la("gom theo nhà cung cấp: bỏ dòng trả 0 và dòng đã có APP", [(k, len(v)) for k, v in dc.gop_theo_ncc(dong)], [("A", 2), ("C", 1)])
	la("ba tổng", dc.tong([{"co_the_tra": 100, "so_tra": 60, "gia_han": 40}, {"co_the_tra": 30, "so_tra": 0, "gia_han": 30}]),
		(Decimal(130), Decimal(60), Decimal(70)))


@ca("v653 hai cấp duyệt là hai người, người lập không tự duyệt; kế toán gửi thì qua thẳng giám đốc")
def _nguoi_duyet():
	dung("người lập tự soát bị chặn", dc.kiem_nguoi_duyet("fin", "u", "u", None, False))
	dung("giám đốc trùng người soát bị chặn", dc.kiem_nguoi_duyet("gd", "k", "u", "k", False))
	la("hai người khác nhau thì được", dc.kiem_nguoi_duyet("gd", "g", "u", "k", False), None)
	la("quản trị hệ thống được", dc.kiem_nguoi_duyet("fin", "u", "u", None, True), None)
	la("thu mua gửi thì chờ kế toán", dc.buoc_gui({"Purchase User"}, {"Accounts User"}), dc.TT_CHO_FIN)
	la("kế toán gửi thì chờ giám đốc", dc.buoc_gui({"Accounts User"}, {"Accounts User"}), dc.TT_CHO_GD)


@ca("v653 soạn lại đợt: giữ số Uyên đã sửa, kẹp theo phần còn đề nghị được mới; dòng chưa sửa theo số máy mới")
def _giu():
	cu = {"PI-1": {"so_tra": 60, "ghi_chu": "chị Lan đồng ý", "hen_dot": "2026-12-10", "da_sua": 1},
		"PI-2": {"so_tra": 30, "da_sua": 0}}
	moi = [{"hoa_don": "PI-1", "co_the_tra": 50, "so_tra": 50}, {"hoa_don": "PI-2", "co_the_tra": 30, "so_tra": 0},
		{"hoa_don": "PI-3", "co_the_tra": 10, "so_tra": 10}]
	r = {x["hoa_don"]: x for x in dc.giu_lua_chon(cu, moi)}
	la("đã sửa 60 mà nay chỉ còn 50: kẹp về 50", (r["PI-1"]["so_tra"], r["PI-1"]["gia_han"]), (Decimal(50), Decimal(0)))
	la("giữ ghi chú, hẹn", (r["PI-1"]["ghi_chu"], r["PI-1"]["hen_dot"]), ("chị Lan đồng ý", "2026-12-10"))
	la("dòng chưa sửa theo số máy mới", (r["PI-2"]["so_tra"], r["PI-2"]["gia_han"]), (0, Decimal(30)))
	la("dòng mới vào đợt", r["PI-3"]["gia_han"], Decimal(0))


# ------------------------------------------------------------- CHẠM HỆ (giả)

class Dong(types.SimpleNamespace):
	def as_dict(self):
		return dict(self.__dict__)

	def get(self, k, d=None):
		return getattr(self, k, d)


class Dot(types.SimpleNamespace):
	def __init__(self, **k):
		super().__init__(flags=types.SimpleNamespace(), **k)
		self.luu = 0

	def save(self, **k):
		self.luu += 1

	def get(self, k, d=None):
		return getattr(self, k, d)

	def db_set(self, a, b=None):
		for x, y in (a.items() if isinstance(a, dict) else [(a, b)]):
			setattr(self, x, y)


def _dot(tt="Nhap", nguoi_lap="uyen", fin_boi=None):
	return Dot(name="DC-26-11-20", ngay_dot=D(2026, 11, 20), trang_thai=tt, nguoi_lap=nguoi_lap, fin_boi=fin_boi, fin_luc=None,
		gd_boi=None, gd_luc=None, ly_do_tra_lai="", tong_tra=0, tong_gia_han=0, tong_de_nghi=0, so_du_mb=None, dong=[
			Dong(name="r1", idx=1, nha_cung_cap="NCC-P", ten_ncc="Printeco", nhom_ncc="", hoa_don="PI-1", so_hd_ncc="0001234",
				ngay_hd=D(2026, 10, 20), han_du_tinh=D(2026, 11, 19), con_no=100, dang_giu=0, co_the_tra=100, so_tra=100, gia_han=0,
				ghi_chu="", hen_dot=None, ho_so_app="", ket_qua=""),
			Dong(name="r2", idx=2, nha_cung_cap="NCC-H", ten_ncc="Phương Hoàng Phát", nhom_ncc="", hoa_don="PI-3", so_hd_ncc="0000777",
				ngay_hd=D(2026, 10, 1), han_du_tinh=D(2026, 10, 31), con_no=50, dang_giu=0, co_the_tra=50, so_tra=50, gia_han=0,
				ghi_chu="", hen_dot=None, ho_so_app="", ket_qua="")])


def KHOA(q, *a, **k):
	"""SQL giả: khoá có tên luôn lấy được, còn lại rỗng."""
	return [(1,)] if "get_lock" in q else []


def _vai(*v):
	return lambda nguoi=None: set(v)


@ca("v653 lưu: khoá hoá đơn TRƯỚC khi đọc dư nợ và phần APP khác giữ; số vượt báo đúng hoá đơn; đợt đã gửi không sửa")
def _luu():
	doc, thu_tu = _dot(), []

	def sql(q, *a, **k):
		if "for update" in q:
			thu_tu.append("khoa")
		return []

	def get_all(dt_, **k):
		thu_tu.append("doc_du_no")
		return [fr._dict(name="PI-1", outstanding_amount=80)]

	def giu(ds, khoa=False):
		thu_tu.append("doc_giu:%s" % int(khoa))
		return {}

	with um.patch.object(dc, "_vai", _vai("Purchase User")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(fr.db, "sql", sql), um.patch.object(fr, "get_all", get_all), um.patch.object(dc, "_dang_giu", giu), \
			um.patch.object(dc, "_cho_man", lambda d: {"ok": 1}):
		nem("trả 90 khi chỉ còn 80 bị chặn", lambda: dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": 90}]))
		la("khoá trước, đọc sau, phần giữ đọc dưới khoá", thu_tu[:3], ["khoa", "doc_du_no", "doc_giu:1"])
		try:
			dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": 90}])
		except Exception as e:
			cau = str(e)
		dung("câu lỗi nêu số hoá đơn và nhà cung cấp", "0001234" in cau and "Printeco" in cau)
		dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": 60, "hen_dot": "2026-12-10"}])
		r = doc.dong[0]
		la("ghi số mới đọc dưới khoá", (r.con_no, r.co_the_tra, r.so_tra, r.gia_han, r.hen_dot), (80, 80, 60, 20, "2026-12-10"))
		la("dòng không gửi lên giữ nguyên", doc.dong[1].so_tra, 50)
		la("tổng đợt tính lại", (doc.tong_tra, doc.tong_gia_han), (110, 20))
		doc.trang_thai = "Cho ke toan"
		nem("đợt đã gửi duyệt thì không sửa được", lambda: dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": 1}]))


@ca("v653 Codex #560: lưu chỉ ghi chú hay ngày hẹn giữ số trả đang lưu; số 0 gửi rõ vẫn là 0")
def _luu_giu_so():
	doc = _dot()
	with um.patch.object(dc, "_vai", _vai("Purchase User")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(fr.db, "sql", lambda *a, **k: []), \
			um.patch.object(fr, "get_all", lambda dt_, **k: [fr._dict(name="PI-1", outstanding_amount=100)]), \
			um.patch.object(dc, "_dang_giu", lambda ds, khoa=False: {}), um.patch.object(dc, "_cho_man", lambda d: {"ok": 1}):
		dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "ghi_chu": "chị Lan hẹn tuần sau"}])
		r = doc.dong[0]
		la("chỉ ghi chú: số trả giữ 100", (r.so_tra, r.gia_han, r.ghi_chu), (100, 0, "chị Lan hẹn tuần sau"))
		dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "hen_dot": "2026-12-10"}])
		la("chỉ ngày hẹn: số trả giữ 100", (r.so_tra, r.hen_dot), (100, "2026-12-10"))
		dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": None, "ghi_chu": "x"}])
		la("so_tra rỗng như không gửi", r.so_tra, 100)
		dc.luu("DC-26-11-20", [{"hoa_don": "PI-1", "so_tra": 0}])
		la("số 0 gửi rõ là 0, hoãn cả", (r.so_tra, r.gia_han), (0, 100))
	dung("du_chi.py lưu đợt có dấu được phép", doc.flags.vgb_du_chi is True)


@ca("v653 Codex #560: sửa đợt thẳng trên Desk hay API bị chặn; chốt đợt Đã duyệt mà thiếu dấu giám đốc thì không lập APP")
def _chan_desk():
	from vagabond.vagabond.doctype.vagabond_dot_chi.vagabond_dot_chi import VagabondDotChi

	class LoiQuyen(Exception):
		pass

	def throw(m, exc=None, *a, **k):
		raise (exc or fr.ValidationError)(m)

	x = VagabondDotChi.__new__(VagabondDotChi)
	x.flags = fr._dict()
	with um.patch.object(fr, "PermissionError", LoiQuyen, create=True), um.patch.object(fr, "throw", throw):
		nem("lưu không qua du_chi.py (Desk, API, frappe.client.set_value) bị chặn bằng lỗi quyền", x.validate, LoiQuyen)
		x.flags = fr._dict(vgb_du_chi=True)
		x.validate()
	doc = _dot("Da duyet")
	ho = types.SimpleNamespace(tao=lambda **k: (_ for _ in ()).throw(AssertionError("không được lập APP")),
		VAI_LAP={"Purchase User"}, VAI_GD={"AP Giám đốc"})
	with um.patch.object(dc, "_ho_so", lambda: ho), um.patch.object(dc, "_vai", _vai("Purchase User")), \
			um.patch.object(fr, "get_doc", lambda *a, **k: doc), um.patch.object(fr.db, "sql", KHOA):
		nem("Thu mua tự đặt Đã duyệt trên Desk rồi bấm chốt: chặn", lambda: dc.chot("DC-26-11-20"))
	la("không lập APP nào", [d.ho_so_app for d in doc.dong], ["", ""])


@ca("v653 duyệt: người lập không tự soát, hai cấp hai người, trả lại phải có lý do và xoá dấu duyệt cũ")
def _duyet():
	doc = _dot("Cho ke toan")
	with um.patch.object(dc, "_vai", _vai("Accounts User", "Purchase User")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(dc, "_cho_man", lambda d: {"tt": d.trang_thai}), um.patch.object(fr.session, "user", "uyen"):
		nem("Uyên lập rồi tự soát bị chặn", lambda: dc.duyet("DC-26-11-20", "fin"))
	with um.patch.object(dc, "_vai", _vai("Accounts User")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(dc, "_cho_man", lambda d: {"tt": d.trang_thai}), um.patch.object(fr.session, "user", "dung"):
		la("kế toán Dung soát", dc.duyet("DC-26-11-20", "fin"), {"tt": "Cho giam doc"})
		la("ghi người soát", doc.fin_boi, "dung")
	with um.patch.object(dc, "_vai", _vai("AP Giám đốc", "Accounts User")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(dc, "_cho_man", lambda d: {"tt": d.trang_thai}), um.patch.object(fr.session, "user", "dung"):
		nem("cùng người soát rồi duyệt cấp giám đốc bị chặn", lambda: dc.duyet("DC-26-11-20", "gd"))
	with um.patch.object(dc, "_vai", _vai("AP Giám đốc")), um.patch.object(fr, "get_doc", lambda *a, **k: doc), \
			um.patch.object(dc, "_cho_man", lambda d: {"tt": d.trang_thai}), um.patch.object(fr.session, "user", "viet"):
		nem("trả lại không lý do bị chặn", lambda: dc.duyet("DC-26-11-20", "tra_lai", "  "))
		dc.duyet("DC-26-11-20", "tra_lai", "Printeco trả 60 thôi")
		la("về Uyên, xoá dấu soát cũ", (doc.trang_thai, doc.fin_boi, doc.ly_do_tra_lai), ("Nhap", None, "Printeco trả 60 thôi"))
		nem("đợt nháp thì không duyệt cấp giám đốc", lambda: dc.duyet("DC-26-11-20", "gd"))


@ca("v653 chốt: giám đốc bấm duyệt thì APP đứng tên Uyên, phiên trả về giám đốc; nhà lỗi không chặn nhà khác; chốt lại không trùng")
def _chot():
	doc = _dot("Da duyet")
	doc.gd_boi, doc.gd_luc = "viet", "2026-11-13 08:00:00"
	luu_dong = {d.name: d for d in doc.dong}
	da_lap, ghi = {}, []

	def tao(ncc=None, hoa_don=None, ghi_chu="", gui_luon=0, **k):
		ghi.append((ncc, fr.session.user, ghi_chu, gui_luon, [x["so_tien"] for x in hoa_don]))
		if ncc == "NCC-H" and not da_lap.get("cho_qua"):
			raise fr.ValidationError("Nhà cung cấp chưa có tài khoản nhận")
		ma = "APP.%s" % ncc
		da_lap[ncc] = ma
		return {"ma": ma}

	def set_value(dt_, ten, a, b=None):
		if dt_ == dc.DT_DONG:
			for x, y in (a.items() if isinstance(a, dict) else [(a, b)]):
				setattr(luu_dong[ten], x, y)

	ho = types.SimpleNamespace(tao=tao, VAI_LAP={"Purchase User"}, VAI_GD={"AP Giám đốc"})

	def set_user(u):
		fr.session.user = u

	with um.patch.object(dc, "_ho_so", lambda: ho), um.patch.object(dc, "_vai", _vai("AP Giám đốc")), \
			um.patch.object(fr, "get_doc", lambda *a, **k: doc), um.patch.object(fr.db, "set_value", set_value), \
			um.patch.object(fr.db, "sql", KHOA), \
			um.patch.object(fr, "set_user", set_user, create=True), um.patch.object(fr.session, "user", "viet"), \
			um.patch.object(dc, "_ap_dau_duyet", lambda app, dot: None), \
			um.patch.object(dc, "_app_da_lap", lambda ma, ds: None):
		k = dc.chot("DC-26-11-20")
		la("Printeco lập được, Hoàng Phát lỗi", (k["lap"], [x["ncc"] for x in k["loi"]]), (["APP.NCC-P"], ["NCC-H"]))
		la("APP lập đứng tên Uyên, đúng số trả, chưa tự gửi, có dấu đợt", ghi[0][:4] + (ghi[0][4],),
			("NCC-P", "uyen", "Theo đợt dự chi DC-26-11-20", 0, [100]))
		la("phiên trả về giám đốc kể cả khi nhà sau lỗi", fr.session.user, "viet")
		dung("dòng lỗi ghi lý do", "tài khoản nhận" in doc.dong[1].ket_qua)
		la("còn dòng chưa có APP thì chưa Đã chốt", doc.trang_thai, "Da duyet")
		da_lap["cho_qua"] = 1
		ghi.clear()
		k = dc.chot("DC-26-11-20")
		la("chốt lại chỉ lập phần còn lỗi", [x[0] for x in ghi], ["NCC-H"])
		la("đủ APP thì Đã chốt", doc.trang_thai, "Da chot")


@ca("v653 chốt: lượt khác đang lập APP của cùng đợt thì lượt sau dừng, không lập trùng")
def _chot_khoa():
	ho = types.SimpleNamespace(tao=lambda **k: (_ for _ in ()).throw(AssertionError("không được lập")), VAI_LAP={"Purchase User"},
		VAI_GD={"AP Giám đốc"})
	with um.patch.object(dc, "_ho_so", lambda: ho), um.patch.object(dc, "_vai", _vai("Purchase User")), \
			um.patch.object(fr.db, "sql", lambda q, *a, **k: [(0,)] if "get_lock" in q else []):
		nem("khoá đang bận thì báo chờ", lambda: dc.chot("DC-26-11-20"))


@ca("v653 chốt lại sau khi APP đã lập mà bước sau hỏng: nhận lại APP cũ, không lập lần hai")
def _chot_lai():
	doc = _dot("Da duyet")
	doc.gd_boi, doc.gd_luc = "viet", "2026-11-13 08:00:00"
	doc.dong = doc.dong[:1]
	ghi = []
	ho = types.SimpleNamespace(tao=lambda **k: ghi.append(1) or {"ma": "APP.MOI"}, VAI_LAP={"Purchase User"}, VAI_GD={"AP Giám đốc"})

	def set_value(dt_, ten, a, b=None):
		if dt_ == dc.DT_DONG:
			for x, y in (a.items() if isinstance(a, dict) else [(a, b)]):
				setattr(doc.dong[0], x, y)

	with um.patch.object(dc, "_ho_so", lambda: ho), um.patch.object(dc, "_vai", _vai("Purchase User")), \
			um.patch.object(fr, "get_doc", lambda *a, **k: doc), um.patch.object(fr.db, "set_value", set_value), \
			um.patch.object(fr.db, "sql", KHOA), \
			um.patch.object(dc, "_ap_dau_duyet", lambda app, dot: None), \
			um.patch.object(dc, "_app_da_lap", lambda ma, ds: "APP.CU"):
		dc.chot("DC-26-11-20")
	la("không gọi lập APP", ghi, [])
	la("dòng nhận APP cũ", doc.dong[0].ho_so_app, "APP.CU")


@ca("v653 nhịp ngày 7 và 17: chưa tới ngày không soạn; tới ngày, qua giờ thì soạn và nhắn nhóm Thu mua một lần")
def _nhip():
	from vagabond import kenh_zalo, viec_tu_dong as vtd

	soan, tin, bao = [], [], set()
	doc = types.SimpleNamespace(name="DC-26-11-20", tong_tra=110, tong_gia_han=40)

	def chay(ngay_nay, gio_qua=True):
		with um.patch.object(dc, "nowdate", lambda: ngay_nay), um.patch.object(dc, "soan", lambda nd, nguoi=None: soan.append(str(nd)) or doc), \
				um.patch.object(vtd, "da_qua", lambda g, b: gio_qua), um.patch.object(vtd, "_chua_bao", lambda k: k not in bao), \
				um.patch.object(vtd, "_da_bao", lambda k: bao.add(k)), um.patch.object(vtd, "_url", lambda p: p), \
				um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: tin.append(k.get("ma_tin"))):
			dc.lam_soan_tu_dong({"gio": "09:00", "han": "17:00"}, None)

	chay("2026-11-16")
	la("16/11 chưa soạn", soan, [])
	chay("2026-11-17", gio_qua=False)
	la("17/11 chưa tới giờ chưa soạn", soan, [])
	chay("2026-11-17")
	la("17/11 qua giờ soạn đợt 20/11", soan, ["2026-11-20"])
	la("nhắn nhóm Thu mua đúng mã tin", tin, ["tm_du_chi"])
	chay("2026-11-17")
	la("nhịp sau không soạn, không nhắn lại", (len(soan), len(tin)), (1, 1))
	chay("2026-11-18")
	la("lỡ ngày 17 (máy chủ tắt) thì ngày 18 vẫn soạn bù một lần", len(soan), 1)


@ca("v653 Việc cần làm: Uyên thấy đợt nháp, kế toán thấy đợt chờ soát, giám đốc thấy đợt chờ duyệt")
def _viec():
	ho = types.SimpleNamespace(VAI_LAP={"Purchase User"}, VAI_FIN={"Accounts User"}, VAI_GD={"AP Giám đốc"})
	loc = []

	def get_all(dt_, filters=None, **k):
		loc.append(filters["trang_thai"][1])
		return [fr._dict(name="DC-26-11-20", ngay_dot="2026-11-20", trang_thai=filters["trang_thai"][1][0], tong_tra=110, tong_gia_han=40)]

	with um.patch.object(dc, "_ho_so", lambda: ho), um.patch.object(fr, "get_all", get_all):
		la("thu mua", (dc.viec({"Purchase User"})[0]["loai"], loc[-1]), ("du_chi", ["Nhap"]))
		dc.viec({"Accounts User"})
		la("kế toán", loc[-1], ["Cho ke toan"])
		dc.viec({"AP Giám đốc"})
		la("giám đốc", loc[-1], ["Cho giam doc"])
		la("vai khác không thấy", dc.viec({"Sales User"}), [])


@ca("v653 màn Công nợ phải trả dùng chung hạn dự tính với Dự chi (một nguồn)")
def _mot_nguon():
	with um.patch.object(dc, "so_ngay_no_cua", lambda ds: {"NCC-P": (30, "mac_dinh", None)}):
		r = dc.gan_han_du_tinh([{"supplier": "NCC-P", "bill_date": "2026-10-01", "posting_date": "2026-10-03"}])
	la("hạn theo ngày hoá đơn NCC + 30", r[0]["han_du_tinh"], "2026-10-31")
	from vagabond import cong_no_ncc as cn

	hd = {"name": "PI-1", "supplier": "NCC-P", "supplier_name": "Printeco", "supplier_group": "", "posting_date": "2026-10-03",
		"bill_date": "2026-10-01", "bill_no": "1", "due_date": "2026-10-01", "grand_total": 100, "rounded_total": 100,
		"outstanding_amount": 100, "currency": "VND", "account_currency": "VND"}
	cu = cn.tong_hop([dict(hd)], "2026-10-20", "tat_ca")
	moi = cn.tong_hop([dict(hd, han_du_tinh="2026-10-31")], "2026-10-20", "tat_ca")
	la("hạn ghi sổ bằng ngày hoá đơn: trước đây báo Quá hạn, nay theo hạn dự tính thì chưa", (cu["dem"]["qua_han"], moi["dem"]["qua_han"]), (1, 0))
	ma = open(os.path.join(GOC, "cong_no_ncc.py"), encoding="utf-8").read()
	dung("màn Công nợ phải trả gọi đúng hàm của du_chi", "from vagabond.du_chi import gan_han_du_tinh" in ma and "gan_han_du_tinh([r for r in ds" in ma)
	dung("chip Quá hạn ưu tiên hạn dự tính", 'r.get("han_du_tinh") or r.get("due_date")' in ma)


@ca("v653 màn Dự chi công nợ chạy thật trong node: 100/60/40, tải lại trang, số vượt, trả hết, kế toán soát, tìm nhanh, chuẩn chạm")
def _man():
	r = subprocess.run(["node", os.path.join(GOC, "khung", "kiem_thu", "hanh_vi", "du_chi_653.js")], capture_output=True, text=True, timeout=120)
	la("du_chi_653.js chạy xanh", (r.returncode, (r.stderr or "")[-400:]), (0, ""))
