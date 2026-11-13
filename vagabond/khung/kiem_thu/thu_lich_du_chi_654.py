# -*- coding: utf-8 -*-
"""v654 Lịch dự chi: dự chi tay, tự xếp theo hạn, tiền khả dụng theo ngày, lịch
hằng tháng học từ dữ liệu thật (anh Việt 13/11/2026, ảnh đề xuất JPEG).

Ca chốt:
  - ca đầu cuối đúng số trên ảnh: 100 triệu, chi gấp 10 triệu ngày 15 nhập tay,
    công nợ 60 triệu đến hạn 18, tiền nhà 40 triệu ngày 20: màn báo ngày 20/11
    thiếu 10 triệu; mở lại tính lại vẫn một dòng ngày 15; ghi nhận khoản 18 đã
    trả thì lần tính sau khớp cả số dư lẫn công nợ;
  - Thu mua trả nhà cung cấp bằng ACB, công ty chỉ còn nợ hoàn ứng: một dòng
    hoàn ứng, không có dòng công nợ nhà cung cấp;
  - mỗi khoản đếm một lần: APP đang duyệt, dòng đợt, dự chi tay gắn hoá đơn, máy,
    lịch tháng đã có APP hay hoá đơn;
  - xếp theo hạn: quá hạn hôm nay, đến hạn 18 thì 18 (không dồn 20), đợt đã gửi
    duyệt sau hạn thì ghi trễ;
  - thiếu số dư thì không đoán khả năng chi;
  - học lịch: ba tháng mới gợi ý, bỏ hoàn ứng, gộp trả từng phần, nêu ngoại lệ;
  - kiểm ô nhập của form Thêm dự chi.
"""

import datetime as dt
from decimal import Decimal

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import lich_du_chi as l  # noqa: E402

D = dt.date
TR = Decimal(1000000)
HOM = D(2026, 11, 13)
DEN = HOM + dt.timedelta(days=35)
TIEN_NHA = {"name": "LC-00001", "khoa": "Nguyễn Hữu Phước", "noi_dung": "Tiền nhà Nguyễn Hữu Phước",
	"nguoi_nhan": "Nguyễn Hữu Phước", "so_tien": 40 * TR, "ngay_trong_thang": 20}
NO_18 = {"hoa_don": "HDM-26-10-00900", "ncc": "NCC-A", "ten_ncc": "Công nợ A", "co_the_tra": 60 * TR, "han": D(2026, 11, 18)}
CHI_GAP = {"name": "DCM-26-11-00001", "ngay": D(2026, 11, 15), "so_tien": 10 * TR, "noi_dung": "Chi gấp", "nguoi_nhan": "Chợ Bến Thành"}


def _lich(hd=None, dot=None, app=None, tay=None, lich=None, da_co=None, so_du=100 * TR):
	m = l.ghep_muc(HOM, DEN, hd or [], dot or [], app or [], tay or [], lich or [], da_co or set())
	return m, l.theo_ngay(so_du, m)


def _ngay_tien(kq):
	return [(g["ngay"].strftime("%d/%m"), [x["nguon"] for x in g["muc"]], int(g["con_lai"] / TR)) for g in kq["ngay"]
		if g["ngay"] <= D(2026, 11, 20)]


@ca("v654 ca đầu cuối theo ảnh: 100tr, chi gấp 10tr ngày 15, công nợ 60tr hạn 18, tiền nhà 40tr ngày 20: thiếu 10tr ngày 20/11")
def _anh():
	m, kq = _lich(hd=[NO_18], tay=[CHI_GAP], lich=[TIEN_NHA])
	la("ba ngày, đúng nguồn, đúng số còn lại", _ngay_tien(kq),
		[("15/11", ["tay"], 90), ("18/11", ["may"], 30), ("20/11", ["lich"], -10)])
	la("dòng cảnh báo: ngày 20/11 thiếu 10.000.000", (kq["thieu_dau"]["ngay"], kq["thieu_dau"]["so_tien"]), (D(2026, 11, 20), 10 * TR))
	la("khoản cần thương lượng là công nợ 60tr (tiền nhà, chi gấp không thương lượng)", [x["ma"] for x in kq["can_thuong_luong"]], ["HDM-26-10-00900"])
	la("công nợ hạn 18 xếp đúng ngày 18, cờ trả đúng hạn", [(x["ngay"], x.get("co")) for x in m if x["nguon"] == "may"], [(D(2026, 11, 18), "dung_han")])
	m2, kq2 = _lich(hd=[NO_18], tay=[CHI_GAP], lich=[TIEN_NHA])
	la("mở lại, tính lại: vẫn đúng một dòng ngày 15", len([x for x in m2 if x["nguon"] == "tay"]), 1)
	la("tính lại cho đúng cùng kết quả", _ngay_tien(kq2), _ngay_tien(kq))
	# Ghi nhận khoản 18 đã trả: hoá đơn hết nợ, số dư SePay đọc sau đó còn 40tr.
	_m3, kq3 = _lich(hd=[], tay=[CHI_GAP], lich=[TIEN_NHA], so_du=l.tien_kha_dung(40 * TR, 0))
	la("sau khi trả 18: còn 30 ngày 15, thiếu 10 ngày 20 (số dư và công nợ khớp nhau)", _ngay_tien(kq3), [("15/11", ["tay"], 30), ("20/11", ["lich"], -10)])
	# Số dư đọc TRƯỚC lúc trả (100tr) mà khoản 60tr vừa chi sau đó: trừ phần chi sau.
	_m4, kq4 = _lich(hd=[], tay=[CHI_GAP], lich=[TIEN_NHA], so_du=l.tien_kha_dung(100 * TR, 60 * TR))
	la("số dư đọc trước lúc trả: trừ phần đã chi sau, kết quả như trên", _ngay_tien(kq4), _ngay_tien(kq3))


@ca("v654 Thu mua đã trả nhà cung cấp bằng ACB, công ty chỉ còn nợ hoàn ứng: một dòng hoàn ứng, không còn dòng công nợ")
def _acb():
	hd = [dict(NO_18, co_the_tra=Decimal(0))]  # APP hoàn ứng đang giữ trọn hoá đơn
	app = [{"name": "APP.26.11.050", "ngay": D(2026, 11, 12), "so_tien": 60 * TR, "ten_nhan": "Thu mua (ACB)", "loai": "Hoan ung HD"}]
	m, kq = _lich(hd=hd, app=app)
	la("chỉ một dòng, là hoàn ứng cho Thu mua", [(x["nguon"], x["noi_dung"], x["nguoi_nhan"]) for x in m], [("app", "Hoàn ứng", "Thu mua (ACB)")])
	la("tính một lần 60tr", kq["tong"], 60 * TR)


@ca("v654 mỗi khoản đếm một lần: APP, đợt đã gửi duyệt, dự chi tay gắn hoá đơn, lịch tháng đã có hồ sơ")
def _mot_lan():
	dot = [{"dot": "DC-26-11-20", "ngay_dot": D(2026, 11, 20), "trang_thai": "Cho ke toan", "hoa_don": NO_18["hoa_don"],
		"so_tra": 50 * TR, "co_the_tra": 60 * TR, "hen_dot": None}]
	m, _kq = _lich(hd=[NO_18], dot=dot)
	la("đợt đã gửi: 50tr ngày đợt, 10tr gia hạn sang đợt kế (10/12)", sorted((x["nguon"], x["ngay"], int(x["so_tien"] / TR)) for x in m),
		[("dot", D(2026, 11, 20), 50), ("may", D(2026, 12, 10), 10)])
	la("đợt sau hạn 18: ghi trễ 2 ngày", [x["tre"] for x in m if x["nguon"] == "dot"], [2])
	nhap = [dict(dot[0], trang_thai="Nhap", so_tra=60 * TR)]
	m, _kq = _lich(hd=[NO_18], dot=nhap)
	la("đợt còn nháp, số máy điền sẵn, hạn 18: máy đề xuất ngày 18, không dồn 20", [(x["nguon"], x["ngay"], x.get("dot")) for x in m],
		[("may", D(2026, 11, 18), "DC-26-11-20")])
	tay = [dict(CHI_GAP, hoa_don=NO_18["hoa_don"], so_tien=25 * TR)]
	m, kq = _lich(hd=[NO_18], tay=tay)
	la("dự chi tay gắn hoá đơn: máy chỉ còn đề xuất phần còn lại", sorted((x["nguon"], int(x["so_tien"] / TR)) for x in m), [("may", 35), ("tay", 25)])
	la("tổng vẫn đúng dư nợ", kq["tong"], 60 * TR)
	m, _kq = _lich(lich=[TIEN_NHA], da_co={("Nguyễn Hữu Phước", "2026-11")})
	la("tháng 11 đã có APP tiền nhà, 20/12 ngoài khung 35 ngày: không dòng nào", [x["ngay"] for x in m], [])
	m = l.ghep_muc(HOM, D(2026, 12, 31), [], [], [], [], [TIEN_NHA], {("Nguyễn Hữu Phước", "2026-11")})
	la("khung tới cuối tháng 12: chỉ lần 20/12", [x["ngay"] for x in m], [D(2026, 12, 20)])


@ca("v654 xếp theo hạn: quá hạn lên đầu hôm nay, đến hạn trước đợt thì đúng hạn, sau đợt thì đợt gần nhất không sau hạn")
def _xep():
	la("quá hạn", l.xep_ngay_may(D(2026, 11, 2), HOM), (HOM, "qua_han"))
	la("hạn 18 (không có đợt nào từ 13 tới 18)", l.xep_ngay_may(D(2026, 11, 18), HOM), (D(2026, 11, 18), "dung_han"))
	la("hạn 25: đợt 20", l.xep_ngay_may(D(2026, 11, 25), HOM), (D(2026, 11, 20), "dot"))
	la("hạn đúng 20: đợt 20", l.xep_ngay_may(D(2026, 11, 20), HOM), (D(2026, 11, 20), "dot"))
	la("hạn 09/12: đợt 20/11 (10/12 đã sau hạn)", l.xep_ngay_may(D(2026, 12, 9), HOM), (D(2026, 11, 20), "dot"))
	la("không có hạn: hôm nay", l.xep_ngay_may(None, HOM), (HOM, "dung_han"))
	qua = dict(NO_18, hoa_don="HDM-QUA", han=D(2026, 10, 1), co_the_tra=5 * TR)
	m, _kq = _lich(hd=[NO_18, qua], tay=[dict(CHI_GAP, ngay=HOM)])
	la("cùng ngày: quá hạn đứng đầu", [x["ma"] for x in m if x["ngay"] == HOM][0], "HDM-QUA")
	la("lịch tháng 31 ở tháng hai lùi về 28", l.ngay_trong_thang(2027, 2, 31), D(2027, 2, 28))
	la("năm nhuận 29", l.ngay_trong_thang(2028, 2, 31), D(2028, 2, 29))
	la("đợt qua năm", l.cac_dot(D(2026, 12, 15), D(2027, 1, 12)), [D(2026, 12, 20), D(2027, 1, 10)])
	m = l.ghep_muc(D(2026, 11, 22), D(2026, 11, 30), [], [], [], [], [TIEN_NHA], set())
	la("đã qua ngày 20 mà tháng này chưa thấy hồ sơ tiền nhà: xếp hôm nay, cờ quá ngày", [(x["ngay"], x["qua_ngay"]) for x in m],
		[(D(2026, 11, 22), 1)])


@ca("v654 chưa đọc được số dư: không đoán khả năng chi, vẫn liệt kê khoản chi")
def _khong_so_du():
	m, kq = _lich(hd=[NO_18], tay=[CHI_GAP], so_du=None)
	la("không có số còn lại, không báo thiếu", ([g["con_lai"] for g in kq["ngay"]], kq["thieu_dau"]), ([None, None], None))
	la("vẫn có khoản chi", len(m), 2)
	la("tiền khả dụng None giữ None", l.tien_kha_dung(None, 5), None)


@ca("v654 học lịch hằng tháng từ dữ liệu thật: từ ba tháng, bỏ hoàn ứng, gộp trả từng phần, nêu ngoại lệ")
def _hoc():
	ls = [
		# Tiền nhà Nguyễn Hữu Phước: ba tháng, đúng số liệu site 13/11.
		{"khoa": "Nguyễn Hữu Phước", "ten": "Nguyễn Hữu Phước", "ngay": D(2026, 8, 20), "so_tien": 79 * TR, "loai": "TK cong ty"},
		{"khoa": "Nguyễn Hữu Phước", "ten": "Nguyễn Hữu Phước", "ngay": D(2026, 9, 21), "so_tien": Decimal("86900000"), "loai": "TK cong ty"},
		{"khoa": "Nguyễn Hữu Phước", "ten": "Nguyễn Hữu Phước", "ngay": D(2026, 10, 19), "so_tien": Decimal("86900000"), "loai": "TK cong ty"},
		# Một người nhận trả cố định 37,3tr ngày 5 tới 7, tháng 10 có thêm một khoản 180tr lẻ.
		{"khoa": "MA THANH SON", "ten": "MA THANH SON", "ngay": D(2026, 9, 7), "so_tien": Decimal("37300000"), "loai": "TK cong ty"},
		{"khoa": "MA THANH SON", "ten": "MA THANH SON", "ngay": D(2026, 10, 5), "so_tien": Decimal("37300000"), "loai": "TK cong ty"},
		{"khoa": "MA THANH SON", "ten": "MA THANH SON", "ngay": D(2026, 10, 16), "so_tien": 180 * TR, "loai": "TK cong ty"},
		{"khoa": "MA THANH SON", "ten": "MA THANH SON", "ngay": D(2026, 11, 5), "so_tien": Decimal("37300000"), "loai": "TK cong ty"},
		# Hoàn ứng quỹ tạm ứng: nhiều tháng nhưng không phải chi định kỳ.
		{"khoa": "MB-QUY", "ten": "Quỹ tạm ứng", "ngay": D(2026, 9, 15), "so_tien": TR, "loai": "Hoan ung HD"},
		{"khoa": "MB-QUY", "ten": "Quỹ tạm ứng", "ngay": D(2026, 10, 15), "so_tien": TR, "loai": "Hoan ung"},
		{"khoa": "MB-QUY", "ten": "Quỹ tạm ứng", "ngay": D(2026, 11, 2), "so_tien": TR, "loai": "Hoan ung"},
		# BHXH mới hai tháng: chưa gợi ý.
		{"khoa": "BHXH", "ten": "BHXH", "ngay": D(2026, 10, 13), "so_tien": 12 * TR, "loai": "TK cong ty"},
		{"khoa": "BHXH", "ten": "BHXH", "ngay": D(2026, 11, 5), "so_tien": 6 * TR, "loai": "TK cong ty"},
	]
	g = {x["khoa"]: x for x in l.hoc_lich(ls)}
	la("chỉ hai người nhận đủ ba tháng", sorted(g), ["MA THANH SON", "Nguyễn Hữu Phước"])
	la("tiền nhà: ba tháng, ngày 20, số trung vị 86,9tr", (g["Nguyễn Hữu Phước"]["so_thang"], g["Nguyễn Hữu Phước"]["ngay_goi_y"],
		g["Nguyễn Hữu Phước"]["so_tien_goi_y"]), (3, 20, Decimal("86900000")))
	le = g["MA THANH SON"]["ngoai_le"]
	dung("tháng 10 trả hai lần là ngoại lệ", any("10/2026 trả 2 lần" in x for x in le))
	dung("tháng 10 lệch số là ngoại lệ", any("10/2026 chi 217.300.000" in x for x in le))
	la("ngày gợi ý theo lần đầu mỗi tháng", g["MA THANH SON"]["ngay_goi_y"], 5)


@ca("v654 form Thêm dự chi: ngày, nội dung, số tiền bắt buộc; ô gõ hỏng báo việc cần làm")
def _kiem_form():
	x = l.kiem_muc({"ngay": "2026-11-15", "noi_dung": "  Chi gấp mua bơ ", "so_tien": "10,000,000", "nguoi_nhan": " Chợ ", "hoa_don": ""})
	la("chuẩn hoá", (x["ngay"], x["noi_dung"], x["so_tien"], x["nguoi_nhan"], x["hoa_don"]),
		(D(2026, 11, 15), "Chi gấp mua bơ", 10 * TR, "Chợ", None))
	nem("thiếu ngày", lambda: l.kiem_muc({"noi_dung": "a", "so_tien": 1}), ValueError)
	nem("thiếu nội dung", lambda: l.kiem_muc({"ngay": "2026-11-15", "so_tien": 1}), ValueError)
	nem("số 0", lambda: l.kiem_muc({"ngay": "2026-11-15", "noi_dung": "a", "so_tien": 0}), ValueError)
	nem("chữ", lambda: l.kiem_muc({"ngay": "2026-11-15", "noi_dung": "a", "so_tien": "mười triệu"}), ValueError)
	from vagabond.patches import v654_lich_chi_tien_nha as p
	la("gieo tiền nhà ngày 20 theo APP gần nhất", (p.dong_gieo(True, False, 86900000, 3) or {}).get("ngay_trong_thang"), 20)
	la("đã có lịch thì không gieo lại", p.dong_gieo(True, True, 86900000, 3), None)
	la("không có nhà cung cấp thì không gieo", p.dong_gieo(False, False, 0, 0), None)


@ca("v654 màn chạy thật trong node: Lịch dự chi theo ảnh, Thêm dự chi, gợi ý lịch; nhãn XML PDF; ô chọn từng hoá đơn và chọn hàng loạt theo lọc")
def _man():
	import os
	import subprocess

	goc = os.path.dirname(os.path.abspath(__file__))
	for t in ("lich_du_chi_654.js", "hd_tep_654.js", "du_chi_chon_654.js"):
		r = subprocess.run(["node", os.path.join(goc, "hanh_vi", t)], capture_output=True, text=True, timeout=120)
		la(t + " chạy xanh", (r.returncode, (r.stderr or "")[-400:]), (0, ""))


@ca("v654 chạm hệ: lich() ghép đúng nguồn; dự chi tay đã nối APP đang duyệt không đếm lại; tháng có APP tiền nhà thì lịch bỏ")
def _cham_he():
	import unittest.mock as um

	from vagabond.khung.kiem_thu.nen import Doi
	from vagabond import ho_so_tt

	fr = __import__("frappe")
	muc = [Doi(name="DCM-1", ngay=D(2026, 11, 15), so_tien=10 * TR, noi_dung="Chi gấp", nguoi_nhan="Chợ", nha_cung_cap=None,
		hoa_don=None, ho_so_app=None, lich=None, thang=None, nguon="Nhập tay"),
		Doi(name="DCM-2", ngay=D(2026, 11, 16), so_tien=5 * TR, noi_dung="Sửa máy", nguoi_nhan="Thợ", nha_cung_cap=None,
		hoa_don=None, ho_so_app="APP.26.11.077", lich=None, thang=None, nguon="Nhập tay")]
	app = [Doi(name="APP.26.11.077", ngay=D(2026, 11, 14), tong_tien=5 * TR, ten_nhan="Thợ", ten_ncc="", loai="TK cong ty", ghi_chu="", nha_cung_cap=None)]
	lich = [Doi(name="LC-00001", noi_dung="Tiền nhà", nguoi_nhan="Nguyễn Hữu Phước", nha_cung_cap="Nguyễn Hữu Phước", so_tien=40 * TR,
		ngay_trong_thang=20, so_thang_thay=3, ngoai_le="", bat=1),
		# Codex #561: lịch tạm thôi phải còn trên màn để bật lại, nhưng không tính tiền.
		Doi(name="LC-00009", noi_dung="Tiền điện", nguoi_nhan="EVN", nha_cung_cap=None, so_tien=3 * TR,
		ngay_trong_thang=16, so_thang_thay=3, ngoai_le="", bat=0)]

	def ga(dt_, filters=None, **k):
		if dt_ == l.DT_MUC:
			if filters.get("trang_thai") == l.MUC_NHAP:
				return muc
			return [Doi(name=m.name, lich=m.lich, thang=m.thang) for m in muc]
		if dt_ == "Vagabond Ho So TT":
			if filters.get("ngay"):
				return [Doi(nha_cung_cap="Nguyễn Hữu Phước", ten_nhan="Nguyễn Hữu Phước", ten_ncc="", ngay=D(2026, 10, 19))]
			return app
		if dt_ == l.DT_LICH:
			return lich
		return []
	vs = [um.patch.object(fr, "get_all", ga), um.patch.object(fr, "get_roles", lambda *a: ["Purchase User"], create=True),
		um.patch.object(l, "so_du_kha_dung", lambda: {"so_tien": 100 * TR, "luc": "2026-11-13 09:30:00", "nguon": "SePay", "chi_sau": 0}),
		um.patch.object(l, "_hd_no", lambda: [NO_18]), um.patch.object(l, "_dot_dong", lambda: []),
		um.patch.object(l, "getdate", lambda v: HOM), um.patch.object(ho_so_tt, "VAI_LAP", {"Purchase User"}),
		um.patch.object(l, "_phai_thu_hd", lambda: []), um.patch.object(l, "_tre_thanh_toan", lambda: {})]
	xem = {"v": True}
	vs.append(um.patch.object(l, "_xem_so_du", lambda: xem["v"]))
	for v in vs:
		v.start()
	try:
		r = l.lich()
		xem["v"] = False
		r_an = l.lich()
	finally:
		for v in reversed(vs):
			v.stop()
	# anh Việt 13/11: Thu mua không được biết số dư; máy vẫn báo ngày không đủ tiền.
	import json as _js
	chu = _js.dumps(r_an, default=str)
	la("người không xem được Tài chính: không có số dư, còn lại, số thiếu",
		(r_an["so_du"], r_an["du_kien_ve"], [g["con_lai"] for g in r_an["ngay"]], r_an["thieu_dau"], r_an["quyen"]["xem_so"]),
		({"an": 1}, {"an": 1}, [None] * len(r_an["ngay"]), {"ngay": "2026-11-20", "so_tien": None}, 0))
	dung("không lộ số 100 triệu ở đâu trong phản hồi", "100000000" not in chu and "1e8" not in chu)
	la("vẫn đánh dấu đúng ngày không đủ tiền", [g["ngay"] for g in r_an["ngay"] if g["khong_du"]], [g["ngay"] for g in r["ngay"] if g["thieu"]])
	la("người xem được Tài chính thấy số", r["quyen"]["xem_so"], 1)
	g = {x["ngay"]: [(m["nguon"], m["ma"]) for m in x["muc"]] for x in r["ngay"]}
	la("14: APP đang duyệt (ngày lập); 15: dự chi tay; 16 không có (đã nối APP); 18: công nợ; 20: tiền nhà (tháng 10 có APP không ảnh hưởng tháng 11)",
		(g.get("2026-11-14"), g.get("2026-11-15"), g.get("2026-11-16"), g.get("2026-11-18"), g.get("2026-11-20")),
		([("app", "APP.26.11.077")], [("tay", "DCM-1")], None, [("may", "HDM-26-10-00900")], [("lich", "LC-00001")]))
	la("thiếu đầu tiên 20/11, 15 triệu (thêm 5 triệu APP sửa máy)", (r["thieu_dau"]["ngay"], r["thieu_dau"]["so_tien"]), ("2026-11-20", 15000000.0))
	la("nguồn số dư và giờ đọc đi kèm", (r["so_du"]["nguon"], r["so_du"]["luc"]), ("SePay", "2026-11-13 09:30:00"))
	la("Codex #561: lịch tạm thôi vẫn trả về cho màn, kèm cờ", sorted((x["name"], x["bat"]) for x in r["lich_chi"]), [("LC-00001", 1), ("LC-00009", 0)])
	la("Codex #561: lịch tạm thôi không vào phép tính (16/11 không có dòng nào)",
		[m["ma"] for x in r["ngay"] for m in x["muc"] if m["nguon"] == "lich"], ["LC-00001"])


@ca("v654 Codex #561 loại 3: dự chi tay gắn hoá đơn đã có đợt hay APP chỉ đếm phần còn lại, một nghĩa vụ đếm một lần")
def _codex_tay_trung():
	no = dict(NO_18, co_the_tra=100 * TR)
	dot = [{"dot": "DC-26-11-20", "ngay_dot": D(2026, 11, 20), "trang_thai": "Cho ke toan", "hoa_don": no["hoa_don"],
		"so_tra": 100 * TR, "co_the_tra": 100 * TR, "hen_dot": None}]
	tay = [dict(CHI_GAP, hoa_don=no["hoa_don"], so_tien=100 * TR)]
	m, kq = _lich(hd=[no], dot=dot, tay=tay)
	la("dư nợ 100, đợt trả 100, dự chi tay 100: tổng 100 (Codex: trước đây 200)", kq["tong"], 100 * TR)
	t = [x for x in m if x["nguon"] == "tay"][0]
	la("dòng tay còn hiện, số đếm 0, ghi rõ đã tính nơi khác 100", (t["so_tien"], t["da_tinh_noi_khac"], t["so_tien_nhap"]), (0, 100 * TR, 100 * TR))
	# APP đang giữ trọn hoá đơn: _hd_no đã trừ phần APP giữ nên co_the_tra 0.
	app = [{"name": "APP.26.11.090", "ngay": D(2026, 11, 14), "so_tien": 100 * TR, "ten_nhan": "Công nợ A", "loai": "NCC"}]
	m, kq = _lich(hd=[dict(no, co_the_tra=0)], app=app, tay=tay)
	la("APP giữ trọn hoá đơn, dự chi tay 100 gắn hoá đơn đó: tổng 100", kq["tong"], 100 * TR)
	dot50 = [dict(dot[0], so_tra=50 * TR)]
	m, kq = _lich(hd=[no], dot=dot50, tay=[dict(tay[0], so_tien=30 * TR)])
	la("đợt 50, tay 30, máy đề xuất phần còn 20: tổng đúng dư nợ 100",
		(sorted((x["nguon"], int(x["so_tien"] / TR)) for x in m), kq["tong"]), ([("dot", 50), ("may", 20), ("tay", 30)], 100 * TR))
	m, kq = _lich(hd=[], tay=[dict(tay[0], hoa_don="HDM-DA-TRA", so_tien=40 * TR)])
	la("gắn hoá đơn không còn nợ: không đếm thêm", kq["tong"], 0)
	m, kq = _lich(hd=[no], tay=[dict(CHI_GAP)])
	la("dự chi tay không gắn hoá đơn vẫn đếm đủ (không đổi)", sorted((x["nguon"], int(x["so_tien"] / TR)) for x in m), [("may", 100), ("tay", 10)])


@ca("v654 Codex #561: tiền khả dụng chỉ trừ khoản chi SAU giờ đọc số dư, từ đúng tài khoản đã đọc")
def _codex_so_du_anh():
	luc = "2026-11-13 09:30:00"
	rows = [{"tong_tien": 5 * TR, "luc": "2026-11-13 09:29:40", "tk_chi": "BA-CHI"},  # trước giờ đọc: số dư đã gồm
		{"tong_tien": 7 * TR, "luc": "2026-11-13 09:30:00", "tk_chi": "BA-CHI"},  # đúng giờ đọc: đã gồm
		{"tong_tien": 11 * TR, "luc": "2026-11-13 09:30:20", "tk_chi": "BA-CHI"},  # sau giờ đọc: trừ
		{"tong_tien": 13 * TR, "luc": "2026-11-13 09:30:30", "tk_chi": "BA-KHAC"},  # tài khoản khác: không trừ
		{"tong_tien": 17 * TR, "luc": "2026-11-13 09:30:40", "tk_chi": ""}]  # tiền mặt: không trừ
	la("chỉ trừ 11 triệu", l.chi_sau_anh(rows, luc, "BA-CHI"), 11 * TR)
	la("không biết tài khoản: không trừ gì", l.chi_sau_anh(rows, luc, None), 0)
	la("không biết giờ đọc: không trừ gì", l.chi_sau_anh(rows, "", "BA-CHI"), 0)
	# Codex #561 vòng 3: so đủ phần lẻ giây. Bút toán 09:30:00.8 ghi SAU bản số dư 09:30:00
	# (cùng một giây) vẫn phải trừ; bản đọc lúc 09:30:00.9 thì đã gồm khoản đó.
	cung_giay = [{"tong_tien": 60 * TR, "luc": "2026-11-13 09:30:00.800000", "tk_chi": "BA-CHI"},
		{"tong_tien": 3 * TR, "luc": dt.datetime(2026, 11, 13, 9, 30, 0, 950000), "tk_chi": "BA-CHI"}]
	la("cùng giây, sau giờ đọc 09:30:00: trừ cả 63 triệu", l.chi_sau_anh(cung_giay, "2026-11-13 09:30:00", "BA-CHI"), 63 * TR)
	la("giờ đọc 09:30:00.900000: chỉ trừ 3 triệu ghi lúc .95", l.chi_sau_anh(cung_giay, "2026-11-13 09:30:00.900000", "BA-CHI"), 3 * TR)
	la("giờ đọc là datetime cũng so đúng", l.chi_sau_anh(cung_giay, dt.datetime(2026, 11, 13, 9, 30, 0, 900000), "BA-CHI"), 3 * TR)
	la("giờ hỏng: không trừ gì", l.chi_sau_anh(cung_giay, "hôm nay", "BA-CHI"), 0)
	import unittest.mock as um
	from vagabond import tai_chinh

	fr = __import__("frappe")
	# Codex #561 vòng 2: APP nhà cung cấp thường để trống tk_chi; tiền đi ra đọc theo
	# SỔ CÁI của đúng tài khoản ngân hàng (Payment Entry, Journal Entry đều ghi GL Entry).
	gl = [{"account": "1121 - MB", "credit": 5 * TR, "debit": 0, "creation": "2026-11-13 09:29:40", "is_cancelled": 0},  # trước giờ đọc
		{"account": "1121 - MB", "credit": 60 * TR, "debit": 0, "creation": "2026-11-13 09:30:20", "is_cancelled": 0},  # APP nhà cung cấp, tk_chi trống
		{"account": "1121 - MB", "credit": 9 * TR, "debit": 0, "creation": "2026-11-13 09:30:25", "is_cancelled": 1},  # đã huỷ
		{"account": "1121 - MB", "credit": 0, "debit": 20 * TR, "creation": "2026-11-13 09:30:30", "is_cancelled": 0},  # tiền vào
		{"account": "1122 - ACB", "credit": 13 * TR, "debit": 0, "creation": "2026-11-13 09:30:35", "is_cancelled": 0}]  # tài khoản khác

	def ga(dt_, filters=None, fields=None, **k):
		if dt_ != "GL Entry":
			return []
		f = filters or {}
		ra = []
		for r in gl:
			if r["account"] != f.get("account") or r["is_cancelled"] != f.get("is_cancelled", r["is_cancelled"]):
				continue
			if "creation" in f and not str(r["creation"]) > str(f["creation"][1]):
				continue
			if "credit" in f and not r["credit"] > f["credit"][1]:
				continue
			ra.append(Doi(tong_tien=r["credit"], luc=r["creation"], tk_chi=r["account"]))
		return ra

	def gv(dt_, ten, truong=None, *a, **k):
		return {"BA-CHI": "1121 - MB"}.get(ten) if (dt_, truong) == ("Bank Account", "account") else None

	def tinh(so_du=100 * TR, loi=0):
		# Đúng dòng của mục Tài chính: tài khoản chi lấy thẳng số SePay báo.
		return {"dong": [{"nguon": "nh:1", "loai": "Ngân hàng", "ten": "MB ···0001", "tam_ung": 0, "bank_account": "BA-CHI",
			"dong_bo": 0, "so_bao": float(so_du or 0), "so_du": None if loi else float(so_du), "loi": loi}]}
	for luc_bao, mong in (("2026-11-13 09:30:00", 60 * TR), (None, 0)):
		with um.patch.object(tai_chinh, "_tinh_tien", lambda: tinh()), \
				um.patch.object(tai_chinh, "_sepay_luc_bao", lambda: luc_bao), \
				um.patch.object(l, "now_datetime", lambda: dt.datetime(2026, 11, 13, 9, 31, 0)), \
				um.patch.object(fr, "get_all", ga), um.patch.object(fr.db, "get_value", gv):
			r = l.so_du_kha_dung()
		la("bản số dư đọc lúc %s: trừ %s triệu (APP nhà cung cấp trả sau giờ đọc, tk_chi trống)" % (luc_bao or "ngay bây giờ", int(mong / TR)),
			(r["chi_sau"], r["luc"], r["so_tien"]), (float(mong), luc_bao or "2026-11-13 09:31:00", 100 * TR - mong))
	with um.patch.object(tai_chinh, "_tinh_tien", lambda: tinh(loi=1)), um.patch.object(tai_chinh, "_sepay_luc_bao", lambda: None):
		r = l.so_du_kha_dung()
	la("không đọc được số dư: không đoán", (r["so_tien"], r["chi_sau"]), (None, 0))
	dung("nói rõ tài khoản đọc hỏng", "MB ···0001" in r["nguon"])


@ca("v654 anh Việt 13/11: Tiền khả dụng lấy đúng số dư ngân hàng của mục Tài chính")
def _kha_dung_tai_chinh():
	dong = [
		{"loai": "Ngân hàng", "ten": "MB chi", "bank_account": "BA-1", "dong_bo": 0, "so_bao": 80e6, "so_du": 80e6},  # SePay báo: trừ chi sau
		{"loai": "Ngân hàng", "ten": "Shinhan thu", "bank_account": "BA-2", "dong_bo": 1, "so_bao": 50e6, "so_du": 45e6},  # tính từ mốc + sổ: không trừ
		{"loai": "Ngân hàng", "ten": "TK tạm ứng", "bank_account": "BA-3", "tam_ung": 1, "so_du": 9e6},  # tiền cá nhân: bỏ
		{"loai": "Ngân hàng", "ten": "ACB chưa chốt", "bank_account": "BA-4", "so_du": None},  # chưa chốt: không cộng, nêu tên
		{"loai": "Tiền mặt", "ten": "Két Q1", "so_du": 7e6},  # két: bỏ
		{"loai": "Tiền mặt", "ten": "Đang nộp về quỹ", "so_du": 2e6, "dang_chuyen": 1}]
	kq = l.kha_dung_tai_chinh(dong, {"BA-1": 3 * TR, "BA-2": 4 * TR})
	la("80 - 3 + 45 = 122 triệu; tạm ứng, két, chưa chốt không cộng; tài khoản tính từ sổ không trừ thêm",
		(kq["so_tien"], kq["so_du_tk"], kq["chi_sau"], kq["chua_chot"]), (122 * TR, 125 * TR, 3 * TR, ["ACB chưa chốt"]))
	kq = l.kha_dung_tai_chinh(dong + [{"loai": "Ngân hàng", "ten": "VCB lỗi", "so_du": None, "loi": 1}], {})
	la("một tài khoản tính hỏng: không đoán", (kq["so_tien"], kq["hong"]), (None, ["VCB lỗi"]))
	la("chưa có tài khoản nào có số: không đoán", l.kha_dung_tai_chinh([dong[3], dong[4]], {})["so_tien"], None)


@ca("v654 anh Việt 13/11: tiền dự kiến về lấy từ công nợ cần thu, ngày về theo thói quen trả của từng khách")
def _du_kien_ve():
	la("trung vị", (l.trung_vi_ngay([30, 10, 20]), l.trung_vi_ngay([10, 20, 30, 41]), l.trung_vi_ngay([])), (20, 25, None))
	hd = [{"hoa_don": "HD-A1", "khach": "A", "ngay": D(2026, 11, 1), "so_tien": 10 * TR},   # A trả sau 20 ngày: 21/11
		{"hoa_don": "HD-B1", "khach": "B", "ngay": D(2026, 11, 5), "so_tien": 6 * TR},     # B một lần trả: theo chung 29 -> 04/12
		{"hoa_don": "HD-C1", "khach": "C", "ngay": D(2026, 9, 1), "so_tien": 7 * TR},      # đã qua 30/09: quá hạn, không tính ngày nào
		{"hoa_don": "HD-D1", "khach": "D", "ngay": D(2026, 12, 10), "so_tien": 5 * TR},    # 08/01: sau khung
		{"hoa_don": "HD-E1", "khach": "E", "ngay": D(2026, 11, 2), "so_tien": 0}]
	tre = {"A": [18, 20, 25], "B": [3], "X": [29, 29, 30, 40, 29]}
	kq = l.du_kien_ve(hd, tre, HOM, DEN)
	la("ngày về: A theo A (20 ngày), B theo trung vị chung (29 ngày)", [(v["hoa_don"], v["ngay"]) for v in kq["ve"]],
		[("HD-A1", D(2026, 11, 21)), ("HD-B1", D(2026, 12, 4))])
	la("tổng trong khung, quá hạn, sau khung", (kq["trong_khung"], kq["qua_han"], kq["sau_khung"], kq["tre_chung"]), (16 * TR, 7 * TR, 5 * TR, 29))
	la("chưa có lịch sử trả nào: 30 ngày", l.du_kien_ve(hd[:1], {}, HOM, DEN)["ve"][0]["ngay"], D(2026, 12, 1))
	# Tiền về được cộng trước khoản chi cùng ngày và mọi ngày sau.
	m = l.ghep_muc(HOM, DEN, [], [], [], [CHI_GAP, dict(CHI_GAP, name="DCM-2", ngay=D(2026, 11, 25), so_tien=30 * TR)], [], set())
	kq2 = l.theo_ngay(20 * TR, m, [{"ngay": D(2026, 11, 21), "so_tien": 10 * TR}, {"ngay": D(2026, 11, 14), "so_tien": 1 * TR}])
	la("15/11: 20 + 1 về - 10 = 11; 25/11: 11 + 10 về - 30 = -9", [(g["ngay"].day, int(g["ve"] / TR), int(g["con_lai"] / TR)) for g in kq2["ngay"]],
		[(15, 1, 11), (25, 10, -9)])
	la("thiếu đầu tiên 25/11, 9 triệu", (kq2["thieu_dau"]["ngay"], kq2["thieu_dau"]["so_tien"]), (D(2026, 11, 25), 9 * TR))


@ca("v654 anh Việt 13/11: Xoá dự chi nháp xoá hẳn bản ghi, chỉ khi còn nháp, chỉ qua nút của app")
def _xoa_muc():
	import types
	import unittest.mock as um
	from vagabond import ho_so_tt
	from vagabond.vagabond.doctype.vagabond_du_chi_muc import vagabond_du_chi_muc as dt_muc

	fr = __import__("frappe")
	kho = {"DCM-1": "Nhap", "DCM-2": "Huy"}
	xoa = []

	def xoa_doc(dt_, ten, **k):
		d = dt_muc.VagabondDuChiMuc.__new__(dt_muc.VagabondDuChiMuc)
		d.__dict__["name"] = ten
		d.on_trash()
		xoa.append(ten)
		kho.pop(ten)
	co = types.SimpleNamespace()
	vs = [um.patch.object(fr.db, "exists", lambda dt_, ten=None, *a, **k: ten in kho),
		um.patch.object(fr, "get_doc", lambda dt_, ten, **k: Doi(name=ten, trang_thai=kho[ten]), create=True),
		um.patch.object(fr, "delete_doc", xoa_doc, create=True), um.patch.object(fr, "flags", co),
		um.patch.object(fr, "get_roles", lambda *a: ["Purchase User"], create=True),
		um.patch.object(ho_so_tt, "VAI_LAP", {"Purchase User"})]
	for v in vs:
		v.start()
	try:
		la("xoá dự chi nháp", l.xoa_muc("DCM-1"), {"name": "DCM-1", "da_xoa": 1})
		la("đã xoá hẳn", (xoa, "DCM-1" in kho), (["DCM-1"], False))
		la("bấm lần hai: không lỗi, coi như đã xoá", l.xoa_muc("DCM-1"), {"name": "DCM-1", "da_xoa": 1})
		nem("không còn nháp thì không xoá", lambda: l.xoa_muc("DCM-2"))
		la("cờ xoá được trả về sau khi xoá", co.__dict__.get("vgb_xoa_du_chi"), None)
		d = dt_muc.VagabondDuChiMuc.__new__(dt_muc.VagabondDuChiMuc)
		d.__dict__["name"] = "DCM-9"
		nem("xoá trên Desk hay API (không qua nút) bị chặn", d.on_trash)
	finally:
		for v in reversed(vs):
			v.stop()


@ca("v654 Codex #561: nhà cung cấp lưu theo MÃ chọn từ danh mục, không đoán từ chữ gõ; hoá đơn phải cùng nhà")
def _codex_ncc_ma():
	import unittest.mock as um
	from vagabond import ho_so_tt

	fr = __import__("frappe")
	ncc = {"SUP-AN-PHU": "Bơ sữa An Phú", "Nguyễn Hữu Phước": "Nguyễn Hữu Phước"}
	pi = {"HDM-26-11-00195": "SUP-AN-PHU"}
	luu = []

	class Phieu(Doi):
		def save(self, **k):
			luu.append(dict(self))

	def gv(dt_, ten, truong=None, *a, **k):
		if dt_ == "Supplier" and truong == "supplier_name":
			return ncc.get(ten)
		if dt_ == "Purchase Invoice" and truong == "supplier":
			return pi.get(ten)
		return None

	def ex(dt_, ten=None, *a, **k):
		if dt_ == "Supplier":
			return ten if ten in ncc else None
		if dt_ == "Purchase Invoice":
			return (ten or {}).get("name") in pi if isinstance(ten, dict) else ten in pi
		return None
	vs = [um.patch.object(fr.db, "get_value", gv), um.patch.object(fr.db, "exists", ex),
		um.patch.object(fr, "new_doc", lambda dt_: Phieu(doctype=dt_, name="DCM-MOI", flags=__import__("types").SimpleNamespace()), create=True),
		um.patch.object(fr, "get_roles", lambda *a: ["Purchase User"], create=True),
		um.patch.object(ho_so_tt, "VAI_LAP", {"Purchase User"})]
	for v in vs:
		v.start()
	try:
		co = {"ngay": "2026-11-15", "noi_dung": "Trả bơ", "so_tien": "5000000"}
		l.luu_muc(nguoi_nhan="Bơ sữa An Phú", **co)
		la("gõ đúng tên một nhà cung cấp mà không chọn: KHÔNG tự gắn nhà cung cấp", (luu[-1]["nha_cung_cap"], luu[-1]["nguoi_nhan"]),
			(None, "Bơ sữa An Phú"))
		l.luu_muc(nha_cung_cap="SUP-AN-PHU", nguoi_nhan="gì cũng được", **co)
		la("chọn mã: lưu mã, người nhận là tên trong danh mục", (luu[-1]["nha_cung_cap"], luu[-1]["nguoi_nhan"]), ("SUP-AN-PHU", "Bơ sữa An Phú"))
		nem("mã không có trong danh mục", lambda: l.luu_muc(nha_cung_cap="SUP-GO-NHAM", **co))
		l.luu_muc(hoa_don="HDM-26-11-00195", **co)
		la("chỉ gắn hoá đơn: nhà cung cấp lấy theo hoá đơn", luu[-1]["nha_cung_cap"], "SUP-AN-PHU")
		nem("hoá đơn của nhà khác với nhà đã chọn", lambda: l.luu_muc(hoa_don="HDM-26-11-00195", nha_cung_cap="Nguyễn Hữu Phước", **co))
		l.luu_lich(noi_dung="Tiền nhà", nha_cung_cap="Nguyễn Hữu Phước", so_tien="86900000", ngay_trong_thang=20)
		la("lịch hằng tháng lưu theo mã", (luu[-1]["nha_cung_cap"], luu[-1]["nguoi_nhan"]), ("Nguyễn Hữu Phước", "Nguyễn Hữu Phước"))
		l.luu_lich(noi_dung="Tiền điện", nguoi_nhan="EVN", so_tien="3200000", ngay_trong_thang=7)
		la("lịch cho người nhận khác: không gắn nhà cung cấp", (luu[-1]["nha_cung_cap"], luu[-1]["nguoi_nhan"]), (None, "EVN"))
		nem("lịch không có nhà cung cấp, không có người nhận", lambda: l.luu_lich(noi_dung="Tiền điện", so_tien="1", ngay_trong_thang=7))
	finally:
		for v in reversed(vs):
			v.stop()
	# Trùng lịch theo MÃ: lịch gắn mã, APP tháng 11 của đúng mã đó thì lịch tháng 11 không đếm nữa.
	lc = [dict(TIEN_NHA, khoa=l._khoa_nhan("SUP-NHA", "Ông Phước (gõ khác tên)"), nha_cung_cap="SUP-NHA")]
	m = l.ghep_muc(HOM, DEN, [], [], [], [], lc, {("SUP-NHA", "2026-11")})
	la("khoá lịch là mã nhà cung cấp, không phải chữ hiển thị", [x["ngay"] for x in m], [D(2026, 12, 20)] if DEN >= D(2026, 12, 20) else [])


@ca("v654 Codex #561: hoá đơn tiền nhà còn NHÁP không làm mất lịch tháng đó (chưa có dòng nào khác thay)")
def _codex_hd_nhap():
	import unittest.mock as um

	fr = __import__("frappe")
	pi = [Doi(supplier="Nguyễn Hữu Phước", posting_date=D(2026, 11, 5), docstatus=0)]

	def khop(gt, dk):
		if isinstance(dk, (list, tuple)):
			op, v = dk
			if op == "<":
				return gt < v
			if op == "in":
				return gt in v
			return gt == v
		return gt == dk

	def ga(dt_, filters=None, **k):
		if dt_ != "Purchase Invoice":
			return []
		f = filters or {}
		return [r for r in pi if khop(r.docstatus, f.get("docstatus", 1)) and khop(r.supplier, f.get("supplier"))]
	lc = [dict(TIEN_NHA, khoa="Nguyễn Hữu Phước", nha_cung_cap="Nguyễn Hữu Phước")]
	with um.patch.object(fr, "get_all", ga):
		da_co = l._da_co(lc, [], [], HOM)
	m, kq = _lich(lich=lc, da_co=da_co, so_du=30 * TR)
	la("hoá đơn nháp: tiền nhà 20/11 vẫn tính, báo thiếu 10 triệu", ([x["ngay"] for x in m], kq["thieu_dau"] and kq["thieu_dau"]["so_tien"]),
		([D(2026, 11, 20)], 10 * TR))
	pi[0]["docstatus"] = 1
	with um.patch.object(fr, "get_all", ga):
		da_co = l._da_co(lc, [], [], HOM)
	la("hoá đơn đã ghi sổ: tháng 11 đã có (máy đề xuất công nợ thay hoặc đã trả)", ("Nguyễn Hữu Phước", "2026-11") in da_co, True)


@ca("v654 anh Việt 13/11: đợt dự chi dùng đúng một số dư (mục Tài chính) và Thu mua không thấy số đó")
def _dot_an_so_du():
	import unittest.mock as um
	from vagabond import du_chi, ho_so_tt

	with um.patch.object(l, "so_du_kha_dung", lambda: {"so_tien": 123 * TR}):
		la("số dư lúc soạn đợt lấy từ Tiền khả dụng của Lịch dự chi", du_chi._so_du_tk_chi(), float(123 * TR))
	with um.patch.object(l, "so_du_kha_dung", lambda: {"so_tien": None}):
		la("không đọc được: None", du_chi._so_du_tk_chi(), None)
	doc = Doi(name="DC-26-11-20", ngay_dot=D(2026, 11, 20), trang_thai="Nhap", tong_de_nghi=0, tong_tra=0, tong_gia_han=0,
		so_du_mb=500 * TR, nguoi_lap="", fin_boi="", gd_boi="", fin_luc="", gd_luc="", ly_do_tra_lai="", dong=[])
	fr = __import__("frappe")
	for xem, mong in ((True, (float(500 * TR), 0)), (False, (None, 1))):
		with um.patch.object(du_chi, "_xem_so_du", lambda: xem), um.patch.object(du_chi, "so_ngay_no_cua", lambda *a: {}), \
				um.patch.object(fr, "get_roles", lambda *a: ["Purchase User"], create=True), um.patch.object(ho_so_tt, "VAI_LAP", {"Purchase User"}):
			r = du_chi._cho_man(doc)
		la("người %s xem Tài chính: số dư đợt" % ("được" if xem else "không được"), (r["so_du"], r["an_so_du"]), mong)
