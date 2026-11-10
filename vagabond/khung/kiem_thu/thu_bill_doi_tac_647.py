# -*- coding: utf-8 -*-
"""v647 (anh Việt 10/11/2026): đối soát từng bill với báo cáo đối tác.

"Giao dịch thu ngân chọn là Shinhan POS, nhập mã chuẩn chi, thì phải dò giao
dịch đó trong bảng Shinhan gửi về cho ngày hôm đó để tự map xem có đúng không."

Chiều xuôi (dòng báo cáo tìm bill, khop_hoa_don) đã có. Ở đây là chiều ngược:
mỗi bill chọn thẻ/sàn phải có dòng trong báo cáo đối tác đúng ngày. Các ca chạy
THẬT khop_hoa_don (chiều xuôi) rồi doi_soat_vendor.du_lieu_bill (chiều ngược),
chỉ thay tầng truy vấn bằng kho trong bộ nhớ.
"""
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_khop as K
from vagabond.khung.kiem_thu.nen import ca, dung, la

HOM = "2026-11-10"


def _b(name, kieu, ngay, tien, ma, diem="TCV"):
	return dict(name=name, kieu=kieu, ngay=ngay, tien=tien, ma=[ma], diem=diem)


# ------------------------------------------------------------ phần thuần

@ca("v647 bill: báo cáo đã về đủ chưa (phủ mọi điểm, theo cửa hàng, lệch ngày thẻ quẹt đêm)")
def _():
	phu = {("shinhan", "2026-11-08", "*"), ("shinhan", "2026-11-09", "*")}
	la("Shinhan 08/11 có báo cáo 08 và 09", K.phu_bill("shinhan", "2026-11-08", "TCV", phu, HOM), True)
	la("Shinhan 09/11 chưa có báo cáo 10 (còn mới): chờ", K.phu_bill("shinhan", "2026-11-09", "TCV", phu, HOM), False)
	la("Shinhan 09/11, đã quá 3 ngày: đủ", K.phu_bill("shinhan", "2026-11-09", "TCV", phu, "2026-11-14"), True)
	la("không có báo cáo ngày đó", K.phu_bill("shinhan", "2026-11-07", "TCV", phu, HOM), False)
	g = {("grab", "2026-11-09", "SALES")}
	la("Grab: báo cáo cửa hàng khác không phủ TCV", K.phu_bill("grab", "2026-11-09", "TCV", g | {("grab", "2026-11-01", "TCV")}, HOM), False)
	la("Grab: đúng cửa hàng", K.phu_bill("grab", "2026-11-09", "SALES", g, HOM), True)
	la("Grab: điểm đối tác không biết thì có báo cáo trong ngày là đủ", K.phu_bill("grab", "2026-11-09", "NVHTN", g, HOM), True)


@ca("v647 bill: sáu kết luận, ghi chú nói việc cần làm và hai con số")
def _():
	phu = {("shinhan", d, "*") for d in ("2026-11-07", "2026-11-08", "2026-11-09")}
	bill = [_b("B1", "shinhan", "2026-11-08", 450000, "A1B2C3"), _b("B2", "shinhan", "2026-11-08", 210000, "ZZ0001"),
		_b("B3", "shinhan", "2026-11-08", 300000, "A1B2C9"), _b("B4", "shinhan", "2026-11-08", 320000, "QQ1234"),
		_b("B5", "shinhan", "2026-11-07", 100000, "XX0001"), _b("B6", "shinhan", "2026-11-09", 120000, "YY0001")]
	noi = {("B1", "shinhan"): dict(trang_thai_khop="Đã nối", tien=450000, ma="A1B2C3"),
		("B2", "shinhan"): dict(trang_thai_khop="Lệch tiền", tien=200000, ma="ZZ0001"),
		("B3", "shinhan"): dict(trang_thai_khop="Nối theo tiền", tien=300000, ma="A1B2C3")}
	cho = [dict(kieu="shinhan", ngay="2026-11-07", ma_tham_chieu="XX0001", tien_hang=100000, giam_gia=0)]
	kq = {x["name"]: x for x in K.doi_chieu_bill(bill, noi, phu, cho, HOM)}
	la("kết luận", {k: v["trang_thai"] for k, v in kq.items()}, {"B1": "Khớp", "B2": "Lệch tiền", "B3": "Sai mã",
		"B4": "Không có trên báo cáo", "B5": "Chờ kế toán chọn", "B6": "Chờ báo cáo"})
	dung("lệch có hai số", "210.000" in kq["B2"]["ghi_chu"] and "200.000" in kq["B2"]["ghi_chu"])
	dung("sai mã có mã đối tác và mã bill", "A1B2C3" in kq["B3"]["ghi_chu"] and "A1B2C9" in kq["B3"]["ghi_chu"])
	dung("không có: nói việc thu ngân cần làm", "kiểm lại phương thức và mã" in kq["B4"]["ghi_chu"])
	la("ba trạng thái cần xử lý", K.TT_BILL_CAN_XU_LY, ("Lệch tiền", "Sai mã", "Không có trên báo cáo"))


# ------------------------------------------------------------ chuỗi thật: chiều xuôi rồi chiều ngược

# Báo cáo Shinhan POS ngày 08/11 (mã chuẩn chi 6 ký tự) và các bill thu ngân bấm.
DONG_SHINHAN = [("A1B2C3", 450000), ("ZZ0001", 200000), ("K9K9K9", 300000)]
BILL_SHINHAN = [("HDB-1", 450000, "A1B2C3", "Q1"), ("HDB-2", 210000, "ZZ0001", "Q1"), ("HDB-3", 300000, "K9K9K8", "Q1"),
	("HDB-4", 320000, "QQ1234", "")]


class Kho:
	"""bill: (tên, tiền, mã, quầy[, pháp nhân]); nguồn mang company (mặc định CT).
	Chiều xuôi chạy THẬT cho bill của pháp nhân CT, như _noi_hoa_don_ban (ứng
	viên chỉ của pháp nhân nguồn)."""

	def __init__(self, dong_bao_cao, bill, nguon):
		self.bill = [tuple(b) + (("CT",) if len(b) == 4 else ()) for b in bill]
		self.nguon = [dict(dict(company="CT"), **n) for n in nguon]
		# Chiều xuôi THẬT: dòng báo cáo nối bill bằng khop_hoa_don.
		dong = [dict(loai="ban", ngay="2026-11-08", ma_tham_chieu=m, tien_hang=t, giam_gia=0) for m, t in dong_bao_cao]
		uv = [dict(name=n, ngay="2026-11-08", tien=t, ma=[m]) for n, t, m, q, ct in self.bill if ct == "CT"]
		kq = K.khop_hoa_don("shinhan", dong, uv)
		self.dong = [dict(nguon="DSN-SH-0811", sales_invoice=kq[i]["hoa_don"] or None, trang_thai_khop=kq[i]["trang_thai"],
			tien_hang=d["tien_hang"], giam_gia=0, ma_tham_chieu=d["ma_tham_chieu"], vendor="Shinhan", ngay="2026-11-08",
			diem_ban="") for i, d in enumerate(dong)]

	def ung_vien(self, kieu, tu, den, ct):
		if kieu != "shinhan":
			return []
		return [dict(name=n, ngay="2026-11-08", tien=t, ma=[m], quay=q) for n, t, m, q, c in self.bill if c == ct]

	def get_all(self, dt, filters=None, fields=None, **k):
		if dt == "Vagabond Doi Soat Dong":
			f = filters or {}
			ra = self.dong
			if "sales_invoice" in f:
				ra = [d for d in ra if d["sales_invoice"] in f["sales_invoice"][1] and d["trang_thai_khop"] in f["trang_thai_khop"][1]]
			elif f.get("trang_thai_khop") == ["in", ["Nhiều chứng từ"]]:
				ra = [d for d in ra if d["trang_thai_khop"] == "Nhiều chứng từ" and d["nguon"] in f["nguon"][1]]
			else:
				ra = []
			return [NS(**d) for d in ra]
		if dt == "Vagabond Doi Soat Nguon":
			maus = filters["mau"][1]
			ct = filters.get("company")
			ct = ct[1] if isinstance(ct, list) else ([ct] if ct else None)
			return [NS(**n) for n in self.nguon if n["mau"] in maus and (ct is None or n["company"] in ct)]
		raise AssertionError(dt)

	def chay(self, ham):
		import datetime

		from vagabond import diem_ban
		from vagabond import doi_soat_vendor as V
		cong = lambda d, n: str(datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=n))
		with ExitStack() as st:
			st.enter_context(patch.object(V, "_ung_vien_hd", self.ung_vien))
			st.enter_context(patch.object(V, "_kieu_nguon", lambda ten: "shinhan"))
			st.enter_context(patch.object(V.frappe, "get_all", self.get_all, create=True))
			st.enter_context(patch.object(V.frappe.utils, "add_days", cong, create=True))
			st.enter_context(patch.object(V.frappe.utils, "nowdate", lambda: HOM, create=True))
			st.enter_context(patch.object(diem_ban, "ma_theo_quay", lambda q: {"Q1": "TCV"}.get(q, "SALES")))
			return ham()


def _nguon_sh(ngay):
	return dict(name="DSN-SH-" + ngay[8:] + ngay[5:7], mau="shinhan_ngay", tu_ngay=ngay, den_ngay=ngay, tai_khoan="SHINHAN",
		duong_vao="Từ thư")


@ca("v647 chuỗi thật Shinhan POS: báo cáo 08/11 nối bill (chiều xuôi), rồi từng bill dò ngược: khớp, lệch, sai mã, không có")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho(DONG_SHINHAN, BILL_SHINHAN, [_nguon_sh("2026-11-08"), _nguon_sh("2026-11-09")])
	kq = {x["name"]: x for x in k.chay(lambda: V.du_lieu_bill("2026-11-08", "2026-11-08", ["CT"], HOM))}
	la("kết luận", {n: x["trang_thai"] for n, x in kq.items()}, {"HDB-1": "Khớp", "HDB-2": "Lệch tiền", "HDB-3": "Sai mã",
		"HDB-4": "Không có trên báo cáo"})
	la("điểm bán theo quầy", (kq["HDB-1"]["diem"], kq["HDB-4"]["diem"]), ("TCV", "SALES"))
	dung("sai mã chỉ ra mã đối tác", "K9K9K9" in kq["HDB-3"]["ghi_chu"] and "K9K9K8" in kq["HDB-3"]["ghi_chu"])
	dung("lệch tiền đúng số đối tác ghi", "200.000" in kq["HDB-2"]["ghi_chu"])


@ca("v647 chuỗi thật: báo cáo ngày sau chưa về thì bill chưa bị kết luận Không có (thẻ quẹt đêm vào lô hôm sau)")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho(DONG_SHINHAN, BILL_SHINHAN, [_nguon_sh("2026-11-08")])
	kq = {x["name"]: x["trang_thai"] for x in k.chay(lambda: V.du_lieu_bill("2026-11-08", "2026-11-08", ["CT"], HOM))}
	la("HDB-4 chờ báo cáo 09/11", kq["HDB-4"], "Chờ báo cáo")
	la("bill đã nối vẫn kết luận", (kq["HDB-1"], kq["HDB-3"]), ("Khớp", "Sai mã"))
	k = Kho(DONG_SHINHAN, BILL_SHINHAN, [dict(_nguon_sh("2026-11-08"), duong_vao="Từ chối"), _nguon_sh("2026-11-09")])
	kq = {x["name"]: x["trang_thai"] for x in k.chay(lambda: V.du_lieu_bill("2026-11-08", "2026-11-08", ["CT"], HOM))}
	la("báo cáo bị giám đốc từ chối không tính là đã về", kq["HDB-4"], "Chờ báo cáo")


# ------------------------------------------------------------ tin Zalo 08:30

@ca("v647 tin Zalo bill không khớp: một tin mỗi kênh mỗi ngày, khoá theo kênh và ngày, chỉ ba trạng thái cần xử lý")
def _():
	import sys

	import vagabond
	from vagabond import diem_ban
	from vagabond import doi_soat_thu as T
	from vagabond import doi_soat_vendor as V
	ds = [dict(_b("B1", "shinhan", "2026-11-08", 450000, "A"), trang_thai="Sai mã", ghi_chu=""),
		dict(_b("B2", "shinhan", "2026-11-08", 210000, "B"), trang_thai="Lệch tiền", ghi_chu=""),
		dict(_b("B3", "payoo", "2026-11-08", 320000, "C", diem="SALES"), trang_thai="Không có trên báo cáo", ghi_chu=""),
		dict(_b("B4", "payoo", "2026-11-09", 1, "D"), trang_thai="Chờ báo cáo", ghi_chu=""),
		dict(_b("B5", "grab", "2026-11-09", 1, "E"), trang_thai="Khớp", ghi_chu="")]
	gui, hoi = [], []
	gia = NS(bao_hoac_ghi_loi=lambda loai, cd, t, d, **k: gui.append((k["khoa"], k["ma_tin"], t, d)))
	gia_f = NS(utils=NS(add_days=lambda d, n: "2026-11-%02d" % (int(d[8:]) + n)), get_all=lambda *a, **k: ["CT"],
		defaults=NS(get_global_default=lambda k: "CT"))
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), patch.object(vagabond, "kenh_zalo", gia, create=True), \
			patch.object(T, "_frappe", lambda: gia_f), patch.object(T, "_link", lambda: "/bep/doi-soat"), \
			patch.object(V, "_cong_ty_demo", lambda: ""), \
			patch.object(V, "du_lieu_bill", lambda tu, den, ct, hom: hoi.append((tu, den, ct)) or ds), \
			patch.object(diem_ban, "ten_diem", lambda: {"TCV": "Trần Cao Vân", "SALES": "Sales Online"}):
		T.bao_bill_lech(HOM)
	la("dò 7 ngày tới hôm qua", hoi, [("2026-11-03", "2026-11-09", ["CT"])])
	la("hai tin, khoá theo kênh và ngày", [(g[0], g[1]) for g in gui], [("ds_bill:payoo:2026-11-08", "kt_ds_bill_lech"),
		("ds_bill:shinhan:2026-11-08", "kt_ds_bill_lech")])
	t, d = gui[1][2], gui[1][3]
	dung("tiêu đề nói số bill, kênh, ngày", t == "2 bill Thẻ Shinhan POS ngày 08/11 không khớp báo cáo đối tác")
	dung("dòng có điểm, mã bill, trạng thái", any("Trần Cao Vân B1" in x and "sai mã" in x for x in d))
	dung("dòng cuối nói ai làm gì", "Điểm bán kiểm phương thức" in d[-1])


@ca("v647 nhac_sang 08:30 gọi bao_bill_lech; lỗi ở phần bill không chặn hai tin trước, chỉ ghi Error Log")
def _():
	from vagabond import doi_soat_thu as T
	loi, goi = [], []
	gia_f = NS(utils=NS(nowdate=lambda: HOM, add_days=lambda d, n: d), get_all=lambda *a, **k: [],
		log_error=lambda title=None, **k: loi.append(title))
	with patch.object(T, "_frappe", lambda: gia_f), patch.object(T, "bao_bill_lech", lambda hom: goi.append(hom) or 1 / 0):
		T.nhac_sang()
	la("đã gọi đúng ngày", goi, [HOM])
	la("chỉ một lỗi, đúng tên", loi, ["Đối soát: nhắc bill không khớp báo cáo đối tác"])


# ------------------------------------------------------------ Codex PR #550 (4f0894ab21), ba góp ý

@ca("Codex #550: báo cáo của pháp nhân A không làm bill của pháp nhân B thành Không có trên báo cáo")
def _():
	from vagabond import doi_soat_vendor as V
	bill = BILL_SHINHAN + [("HDB-B1", 99000, "BB0001", "Q1", "CT-B")]
	k = Kho(DONG_SHINHAN, bill, [_nguon_sh("2026-11-08"), _nguon_sh("2026-11-09")])
	kq = {x["name"]: x["trang_thai"] for x in k.chay(lambda: V.du_lieu_bill("2026-11-08", "2026-11-08", ["CT", "CT-B"], HOM))}
	la("bill pháp nhân B chưa có báo cáo nào: chờ", kq["HDB-B1"], "Chờ báo cáo")
	la("bill pháp nhân A vẫn kết luận", kq["HDB-4"], "Không có trên báo cáo")


@ca("Codex #550: dòng đối tác nhiều ứng viên chỉ giữ chờ chọn cho bill là ứng viên, bill khác vẫn Không có")
def _():
	from vagabond import doi_soat_vendor as V
	# Đúng chuỗi Codex mô tả: báo cáo một giao dịch 100, ba bill 100, 100, 300 không có mã chung.
	k = Kho([("", 100)], [("HDB-A", 100, "", "Q1"), ("HDB-B", 100, "", "Q1"), ("HDB-C", 300, "", "Q1")],
		[_nguon_sh("2026-11-08"), _nguon_sh("2026-11-09")])
	la("chiều xuôi thật: dòng 100 có nhiều chứng từ", [d["trang_thai_khop"] for d in k.dong], ["Nhiều chứng từ"])
	kq = {x["name"]: x["trang_thai"] for x in k.chay(lambda: V.du_lieu_bill("2026-11-08", "2026-11-08", ["CT"], HOM))}
	la("hai bill 100 chờ chọn, bill 300 không có", kq, {"HDB-A": "Chờ kế toán chọn", "HDB-B": "Chờ kế toán chọn",
		"HDB-C": "Không có trên báo cáo"})


def _bill_gia(n):
	return [dict(name="HDB-%04d" % i, kieu="shinhan", ngay="2026-11-08", tien=1000, ma=["M%04d" % i], diem="TCV",
		company="CT", trang_thai="Không có trên báo cáo", ghi_chu="") for i in range(1, n + 1)]


def _goi_bill(**k):
	from vagabond import diem_ban
	from vagabond import doi_soat_vendor as V
	hoi = []
	with ExitStack() as st:
		st.enter_context(patch.object(V, "_chan", lambda *a: None))
		st.enter_context(patch.object(V, "_cong_ty_xem", lambda: ["CT"]))
		st.enter_context(patch.object(V, "du_lieu_bill", lambda tu, den, ct, hom: hoi.append((tu, den)) or _bill_gia(501)))
		st.enter_context(patch.object(V.frappe.utils, "nowdate", lambda: HOM, create=True))
		st.enter_context(patch.object(V.frappe.utils, "add_days", lambda d, n: __import__("datetime").date.fromordinal(
			__import__("datetime").date.fromisoformat(str(d)[:10]).toordinal() + n).isoformat(), create=True))
		st.enter_context(patch.object(V.frappe.utils, "cint", lambda x: int(x or 0), create=True))
		st.enter_context(patch.object(diem_ban, "ten_diem", lambda: {}))
		return V.bill_doi_tac(**k), hoi


@ca("Codex #550: hơn một trang bill vẫn mở được bill cuối (trang sau, ô tìm), có lọc khoảng ngày gửi xuống máy chủ")
def _():
	r, hoi = _goi_bill()
	la("trang đầu 200 bill, còn 301", (len(r["hang"]), r["con"]), (200, 301))
	r, hoi = _goi_bill(trang=2)
	la("trang ba có bill 501 (mới trước, nên là HDB-0001)", (len(r["hang"]), r["hang"][-1]["name"], r["con"]), (101, "HDB-0001", 0))
	r, hoi = _goi_bill(tim="hdb-0001")
	la("ô tìm theo mã bill", [x["name"] for x in r["hang"]], ["HDB-0001"])
	r, hoi = _goi_bill(tim="M0002")
	la("ô tìm theo mã chuẩn chi", [x["name"] for x in r["hang"]], ["HDB-0002"])
	r, hoi = _goi_bill(ky="tuy_chon", tu="2026-11-01", den="2026-11-05")
	la("khoảng ngày tuỳ chọn tới máy chủ", hoi, [("2026-11-01", "2026-11-05")])
	r, hoi = _goi_bill(ky="thang_truoc")
	la("chip Tháng trước", hoi, [("2026-10-01", "2026-10-31")])
	r, hoi = _goi_bill()
	la("Mọi ngày: 14 ngày tới hôm qua", hoi, [("2026-10-27", "2026-11-09")])
	r, hoi = _goi_bill(ky="tuy_chon", tu="2026-01-01", den="2026-11-09")
	la("khoảng quá 92 ngày thì cắt, báo lại khoảng thật", (hoi, r["cat"]), ([("2026-08-10", "2026-11-09")], 1))


# ------------------------------------------------------------ Codex PR #550 (a6af8eabd4): phạm vi cửa hàng

class KhoGrab(Kho):
	"""Thêm một bill GrabFood của TCV và các báo cáo GrabFood theo từng cửa hàng
	(tài khoản nguồn là mã cửa hàng Grab thật trong danh mục ánh xạ)."""

	def __init__(self, cua_hang_co_bao_cao):
		from vagabond.doi_soat_mau import GRAB_DIEM
		ma = {v: k for k, v in GRAB_DIEM.items()}
		super().__init__(DONG_SHINHAN, BILL_SHINHAN, [_nguon_sh("2026-11-08"), _nguon_sh("2026-11-09")] + [
			dict(name="DSN-GF-%s" % d, mau="grabfood", tu_ngay="2026-11-09", den_ngay="2026-11-09",
				tai_khoan="grab:" + ma[d], duong_vao="Từ thư") for d in cua_hang_co_bao_cao])

	def ung_vien(self, kieu, tu, den, ct):
		if kieu == "grab":
			return [dict(name="HDG-TCV", ngay="2026-11-09", tien=150000, ma=["GF-123"], quay="Q1")] if ct == "CT" else []
		return super().ung_vien(kieu, tu, den, ct)


@ca("Codex #550: báo cáo GrabFood của SALES không làm bill GrabFood của TCV thành Không có (cả màn lẫn tin Zalo)")
def _():
	from vagabond import doi_soat_vendor as V
	from vagabond.doi_soat_mau import GRAB_DIEM
	# Đúng chuỗi Codex mô tả: bill TCV ngày 09/11, chỉ có báo cáo SALES cùng ngày.
	la("thuần, danh mục thật: chờ báo cáo TCV", K.doi_chieu_bill([_b("HDG", "grab", "2026-11-09", 150000, "GF-1")], {},
		{("grab", "2026-11-09", "SALES")}, (), HOM, V.diem_doi_tac())[0]["trang_thai"], "Chờ báo cáo")
	la("danh mục lấy từ ánh xạ cửa hàng Grab (một nguồn)", V.diem_doi_tac()["grab"], set(GRAB_DIEM.values()))
	g = {("grab", "2026-11-09", "SALES")}
	la("NVHTN có trong danh mục: báo cáo SALES không phủ", K.phu_bill("grab", "2026-11-09", "NVHTN", g, HOM, V.diem_doi_tac()), False)
	la("điểm không có cửa hàng Grab riêng: báo cáo trong ngày vẫn đủ", K.phu_bill("grab", "2026-11-09", "KHO", g, HOM, V.diem_doi_tac()), True)
	kq = {x["name"]: x["trang_thai"] for x in KhoGrab(["SALES"]).chay(
		lambda: V.du_lieu_bill("2026-11-08", "2026-11-09", ["CT"], HOM))}
	la("chuỗi thật, chỉ báo cáo SALES: bill TCV chờ", kq["HDG-TCV"], "Chờ báo cáo")
	la("Shinhan vẫn kết luận như cũ", kq["HDB-4"], "Không có trên báo cáo")
	kq = {x["name"]: x["trang_thai"] for x in KhoGrab(["SALES", "TCV"]).chay(
		lambda: V.du_lieu_bill("2026-11-08", "2026-11-09", ["CT"], HOM))}
	la("báo cáo TCV về mà không có giao dịch: Không có", kq["HDG-TCV"], "Không có trên báo cáo")
