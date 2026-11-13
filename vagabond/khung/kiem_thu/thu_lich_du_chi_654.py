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
		um.patch.object(l, "getdate", lambda v: HOM), um.patch.object(ho_so_tt, "VAI_LAP", {"Purchase User"})]
	for v in vs:
		v.start()
	try:
		r = l.lich()
	finally:
		for v in reversed(vs):
			v.stop()
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
	import unittest.mock as um
	from vagabond import du_chi, tai_chinh

	fr = __import__("frappe")
	hoi = []

	def ga(dt_, filters=None, fields=None, **k):
		hoi.append((dt_, dict(filters or {})))
		return [Doi(r) for r in rows if r["tk_chi"] == (filters or {}).get("tk_chi")]
	for luc_bao, mong in (("2026-11-13 09:30:00", 11 * TR), (None, 0)):
		hoi.clear()
		with um.patch.object(du_chi, "_tk_chi_so_du", lambda: ("BA-CHI", 100 * TR)), \
				um.patch.object(tai_chinh, "_sepay_luc_bao", lambda: luc_bao), \
				um.patch.object(l, "now_datetime", lambda: dt.datetime(2026, 11, 13, 9, 31, 0)), \
				um.patch.object(fr, "get_all", ga):
			r = l.so_du_kha_dung()
		la("bản số dư đọc lúc %s: trừ %s" % (luc_bao or "ngay bây giờ", int(mong / TR)), (r["chi_sau"], r["luc"], r["tk"]),
			(float(mong), luc_bao or "2026-11-13 09:31:00", "BA-CHI"))
		la("chỉ hỏi APP đã trả của đúng tài khoản, sau giờ đọc", [(d, f.get("tk_chi"), f.get("modified")) for d, f in hoi],
			[("Vagabond Ho So TT", "BA-CHI", [">", luc_bao or "2026-11-13 09:31:00"])])
	with um.patch.object(du_chi, "_tk_chi_so_du", lambda: ("BA-CHI", None)):
		r = l.so_du_kha_dung()
	la("không đọc được số dư: không đoán", (r["so_tien"], r["chi_sau"]), (None, 0))


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
