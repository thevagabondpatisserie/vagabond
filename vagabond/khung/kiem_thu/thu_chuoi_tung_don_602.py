# -*- coding: utf-8 -*-
"""v602: chuỗi ghi sổ cuối ngày, xuất rải và kéo đơn treo đi TỪNG ĐƠN.

Sự cố gốc, đêm 17/10/2026 (đọc trên site thật sáng 18/10): chuỗi 23h ghi sổ
và xuất xong 4 đơn lúc 23:03:25-23:03:36, rồi không ghi thêm đơn nào nhưng
vẫn giữ khoá đơn Sales (nhịp đồng bộ trượt khoá lúc 23:04, 23:32, 00:00),
tới khi hàng đợi dài cắt ở 3600 giây. Cờ ngày vẫn là 16/10, nhật ký vẫn là
của 16/10. Còn nháp: 62 đơn Sales (40.059.778 đ, cả 62 "đủ điều kiện"), 26
bill Trần Cao Vân, 2 bill Nguyễn Văn Trỗi.

Các ca dưới đây dựng ĐÚNG đường đi đó bằng hàm thật nạp từ ban_hang.py, chỉ
thay phần chạm hệ (cơ sở dữ liệu, hàng đợi, m-invoice) bằng bản giả. Ca
"đơn thứ hai kẹt" dựng lại vụ 17/10: trên mã cũ cả lô dừng ở đơn kẹt và cờ
không bao giờ được đặt; trên mã mới các đơn khác vẫn được ghi sổ.
"""

import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
SRC = GOC / "ban_hang.py"


class D(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def nap(ten, g):
	"""Nạp đúng MỘT hàm từ ban_hang.py vào không gian tên giả."""
	fn = next(n for n in ast.parse(SRC.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == ten)
	exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SRC), "exec"), g)
	return g[ten]


def _than(ten):
	s = SRC.read_text()
	i = s.find("def %s(" % ten)
	return s[i:s.find("\ndef ", i + 10)]


class Ket(Exception):
	"""Giả lập một đơn đứng yên tới lúc hàng đợi cắt lượt chạy."""


# ---------------------------------------------------------------- THUẦN


@ca("v602 thuần: mã lượt ghi sổ cố định theo tên đơn, để chống xếp trùng")
def _job():
	la("mã", hddt_bu.job_ghi_so("HDB-26-10-03421"), "vgb-ghi-so-HDB-26-10-03421")
	la("bỏ khoảng trắng", hddt_bu.job_ghi_so(" HDB-1 "), "vgb-ghi-so-HDB-1")
	dung("trần một đơn ngắn hơn hẳn một giờ", hddt_bu.GIAY_MOI_DON <= 300)
	dung("chờ khoá dòng ngắn hơn 50 giây mặc định", hddt_bu.GIAY_CHO_KHOA_DONG < 50)


@ca("v602 thuần: chọn đơn để xếp bỏ đơn cần người xử, bỏ trùng, giữ thứ tự")
def _chon():
	rows = [D(name="A", ly="san_sang"), D(name="B", ly="chua_pt"), D(name="A", ly=""),
		D(name="C", ly="chua_ve_tien"), D(name="", ly=""), D(name="E", ly="tang_cho_duyet")]
	la("chỉ A, C", hddt_bu.chon_de_xep(rows, lambda r: r.ly), ["A", "C"])
	la("rỗng", hddt_bu.chon_de_xep([], lambda r: ""), [])


@ca("v602 thuần: lượt chạy tới muộn thì bỏ đơn đã ghi sổ, đã huỷ, tạm tính hay đã đổi ngày")
def _con_duoc():
	ok = D(docstatus=0, vgb_huy=0, vgb_tam_tinh=0, posting_date="2026-10-17")
	dung("đơn nháp đúng ngày", hddt_bu.con_duoc_ghi_so(ok, "2026-10-17"))
	for mo, sua in (("đã ghi sổ", {"docstatus": 1}), ("đã huỷ", {"vgb_huy": 1}),
			("tạm tính", {"vgb_tam_tinh": 1}), ("đã kéo sang ngày khác", {"posting_date": "2026-10-18"})):
		dung(mo + " thì bỏ", not hddt_bu.con_duoc_ghi_so(D(ok, **sua), "2026-10-17"))


@ca("v602 thuần: tin báo động nói số đơn, số tiền, lý do; không còn đơn thì im")
def _bao_dong_thuan():
	la("không còn đơn", hddt_bu.soan_bao_dong("2026-10-17", "23:20", {}, {}, {}), None)
	t = hddt_bu.soan_bao_dong("2026-10-17", "23:20", {"san_sang": 62, "chua_ve_tien": 2},
		{"san_sang": 40059778, "chua_ve_tien": 500000}, {"chua_ve_tien": "Chuyển khoản chưa về tiền"})
	la("tiêu đề", t[0], "Ngày 17/10/2026 lúc 23:20 còn 64 đơn chưa ghi sổ, 40.559.778 đ")
	dung("đơn đủ điều kiện nói trước, chỉ nút Chạy ngay", t[1][0].startswith("62 đơn đủ điều kiện") and "Chạy ngay" in t[1][0])
	dung("lý do cần người xử có câu tiếng Việt", "2 đơn: Chuyển khoản chưa về tiền (500.000 đ)" in t[1])
	dung("chỉ chỗ xem từng đơn", "Đơn còn treo" in t[1][-1])


# ------------------------------------------------- chuỗi 23h: dựng lại vụ 17/10


def _g_chuoi(rows, xep, moc, ghi_inline):
	"""Không gian tên giả cho tu_ghi_so_cuoi_ngay lượt chính trên hàng đợi."""
	f = NS(set_user=lambda *a: None, log_error=lambda *a, **kw: None, local=NS(message_log=[]),
		db=NS(commit=lambda: None, rollback=lambda: None, count=lambda *a, **kw: len(rows),
			get_all=lambda *a, **kw: [], set_single_value=lambda *a: moc.append(a)),
		enqueue=lambda *a, **kw: None)
	g = dict(frappe=f, cfg=lambda: D(tu_ghi_so_bat=1, tu_ghi_so_gio="23:00", tu_ghi_so_quay="TCV\nNVHTN"),
		cint=lambda x: int(x or 0), nowdate=lambda: "2026-10-17",
		now_datetime=lambda: datetime(2026, 10, 17, 23, 1), _gio_hop_le=lambda x: x or "23:00",
		hddt_cho_xuat=NS(xuat_ngay_cu_truoc=lambda: True), _dong_bo_doanh_so=lambda *a: None,
		pancake_nhip=NS(ghi_ok=lambda: None), _khach_le=lambda: "Khách lẻ",
		_con_nhap=lambda ngay, quay: rows, _ly_do_xep=lambda r, k="": "", hddt_bu=hddt_bu,
		_xep_ghi_so=lambda ds, ngay, cho_xuat=True, nguon="": xep.append((list(ds), ngay, cho_xuat, nguon)) or len(ds),
		_ghi_so_mot_don=ghi_inline, _khoa_dong_bo=lambda **kw: object(), _mo_khoa_dong_bo=lambda *a: None,
		_bao_hoan_phat_hanh=lambda *a: None, phat_hanh_cuoi_ngay=lambda *a, **kw: None)
	return g


@ca("v602 chuỗi 23h (vụ 17/10): xếp MỌI đơn thành lượt riêng, không ghi sổ lần lượt dưới một khoá, đặt cờ ngày")
def _chuoi_xep_het():
	rows = [D(name="HDB-%d" % i) for i in range(1, 91)]
	xep, moc, inline = [], [], []
	g = _g_chuoi(rows, xep, moc, lambda *a, **kw: inline.append(a) or (1, 1, ""))
	nap("tu_ghi_so_cuoi_ngay", g)(bo_qua_gio=True, tren_hang_doi=True)
	la("xếp một lần đủ 90 đơn", (len(xep), len(xep[0][0]) if xep else 0), (1, 90))
	la("ngày và nguồn", (xep[0][1], xep[0][3]), ("2026-10-17", "cuoi-ngay"))
	la("không ghi sổ đơn nào ngay trong lượt chính", inline, [])
	dung("đặt cờ ngày sau khi xếp", ("Vagabond Settings", "tu_ghi_so_lan_cuoi", "2026-10-17") in moc)


@ca("v602 vụ 17/10: đơn thứ hai đứng yên tới lúc bị cắt, các đơn còn lại vẫn ghi sổ, khoá được nhả")
def _don_ket():
	# Đúng chuỗi của lượt chạy riêng: mỗi đơn gọi ghi_so_mot_don_nen một lần.
	# Đơn HDB-2 đứng yên (Ket), như đơn thứ năm đêm 17/10. Trên mã cũ cả vòng
	# dừng ở đây; trên mã mới chỉ lượt của HDB-2 dừng.
	so = {"HDB-1": D(name="HDB-1", docstatus=0, posting_date="2026-10-17", vgb_quay="", custom_pancake_display_id="1"),
		"HDB-2": D(name="HDB-2", docstatus=0, posting_date="2026-10-17", vgb_quay="", custom_pancake_display_id="2"),
		"HDB-3": D(name="HDB-3", docstatus=0, posting_date="2026-10-17", vgb_quay="TCV")}
	da_ghi, khoa, sql = [], [], []

	def ghi(si, sepay=None, cho_xuat=True):
		if si.name == "HDB-2":
			raise Ket()
		da_ghi.append((si.name, sepay))
		return 1, 1, ""
	f = NS(set_user=lambda *a: None, get_doc=lambda dt, ten: so[ten], log_error=lambda *a, **kw: None,
		db=NS(sql=lambda q: sql.append(q)))
	g = dict(frappe=f, hddt_bu=hddt_bu, _khoa_dong_bo=lambda **kw: khoa.append("lay") or "K",
		_mo_khoa_dong_bo=lambda k: khoa.append("nha"), _ly_do_xep=lambda *a, **kw: "",
		_sepay_theo_don=lambda shop, ma: {"tu": ma}, cfg=lambda: D(pancake_shop_id="S"), _ghi_so_mot_don=ghi)
	fn = nap("ghi_so_mot_don_nen", g)
	for ten in ("HDB-1", "HDB-2", "HDB-3"):
		try:
			fn(ten, "2026-10-17")
		except Ket:
			pass
	la("hai đơn còn lại vẫn ghi sổ", [x[0] for x in da_ghi], ["HDB-1", "HDB-3"])
	la("khoá lấy và nhả đủ ba lần, kể cả lượt kẹt", khoa, ["lay", "nha"] * 3)
	la("đơn Sales hỏi SePay riêng, bill quầy không", [x[1] for x in da_ghi], [{"tu": ["1"]}, None])
	dung("mỗi lượt đặt trần chờ khoá dòng", len(sql) == 3 and all("innodb_lock_wait_timeout = 20" in q for q in sql))


@ca("v602 lượt riêng: không lấy được khoá thì không làm gì; đơn đã ghi sổ, khác ngày, tặng chờ duyệt thì bỏ")
def _luot_bo():
	goi = []
	f = NS(set_user=lambda *a: None, db=NS(sql=lambda q: None), log_error=lambda *a, **kw: None,
		get_doc=lambda dt, ten: D(name=ten, docstatus=1 if ten == "DA" else 0,
			posting_date="2026-10-16" if ten == "CU" else "2026-10-17", vgb_quay="TCV"))
	g = dict(frappe=f, hddt_bu=hddt_bu, _mo_khoa_dong_bo=lambda k: None,
		_ly_do_xep=lambda si, *a: "tang_cho_duyet" if si.name == "TANG" else "",
		_sepay_theo_don=lambda *a: None, cfg=lambda: D(), _ghi_so_mot_don=lambda *a, **kw: goi.append(a[0].name) or (1, 0, ""))
	g["_khoa_dong_bo"] = lambda **kw: None
	la("không khoá thì thôi", nap("ghi_so_mot_don_nen", dict(g))("OK", "2026-10-17"), (0, 0, ""))
	g["_khoa_dong_bo"] = lambda **kw: "K"
	fn = nap("ghi_so_mot_don_nen", g)
	for ten in ("DA", "CU", "TANG", "OK"):
		fn(ten, "2026-10-17")
	la("chỉ đơn hợp lệ được ghi", goi, ["OK"])


@ca("v602 xếp: mỗi đơn một lượt hàng đợi default, trần riêng, mã cố định, chống trùng; hỏng hàng đợi thì làm tại chỗ")
def _xep():
	xep, tai_cho = [], []
	f = NS(enqueue=lambda ham, **kw: xep.append((ham, kw)), log_error=lambda *a, **kw: None, get_traceback=lambda: "")
	g = dict(frappe=f, hddt_bu=hddt_bu, ghi_so_mot_don_nen=lambda *a, **kw: tai_cho.append(a))
	la("trả số đã xếp", nap("_xep_ghi_so", g)(["A", "B"], "2026-10-17", cho_xuat=False, nguon="vet"), 2)
	ham, kw = xep[0]
	la("hàm", ham, "vagabond.ban_hang.ghi_so_mot_don_nen")
	la("tham số lượt", (kw["queue"], kw["timeout"], kw["job_id"], kw["deduplicate"], kw["ten"], kw["cho_xuat"], kw["nguon"]),
		("default", hddt_bu.GIAY_MOI_DON, "vgb-ghi-so-A", True, "A", False, "vet"))

	def hong(*a, **kw):
		raise RuntimeError("redis")
	f.enqueue = hong
	la("hỏng hàng đợi vẫn đếm", nap("_xep_ghi_so", g)(["C"], "2026-10-17"), 1)
	la("và làm tại chỗ", tai_cho, [("C", "2026-10-17")])


@ca("v602 vét 5 phút: còn đơn nháp thì xếp lại, không ghi sổ trong lượt; không còn thì im")
def _vet():
	for so_con, mong in ((3, 1), (0, 0)):
		rows = [D(name="X%d" % i) for i in range(so_con)]
		xep, moc, inline = [], [], []
		g = _g_chuoi(rows, xep, moc, lambda *a, **kw: inline.append(a) or (1, 1, ""))
		g["cfg"] = lambda: D(tu_ghi_so_bat=1, tu_ghi_so_gio="23:00", tu_ghi_so_quay="", tu_ghi_so_lan_cuoi="2026-10-17")
		g["now_datetime"] = lambda: datetime(2026, 10, 17, 23, 30)
		nap("tu_ghi_so_cuoi_ngay", g)()
		la("%d đơn còn: số lần xếp" % so_con, len(xep), mong)
		la("không ghi sổ tại chỗ", inline, [])
		if so_con:
			la("nguồn vét", xep[0][3], "vet")
			dung("không đặt lại cờ ngày", not any(m[1] == "tu_ghi_so_lan_cuoi" for m in moc))


@ca("v602 mã nguồn: không đường ghi sổ tự động nào còn gọi _ghi_so_mot_don trong vòng lặp")
def _mot_nguon():
	for ten in ("tu_ghi_so_cuoi_ngay", "xuat_rai_trong_ngay", "keo_va_ghi_so"):
		than = _than(ten)
		dung(ten + " không tự ghi sổ", "_ghi_so_mot_don(" not in than and ".submit()" not in than)
		dung(ten + " đi qua _xep_ghi_so", "_xep_ghi_so(" in than)
	dung("chỉ lượt riêng gọi _ghi_so_mot_don", "_ghi_so_mot_don(" in _than("ghi_so_mot_don_nen"))


# -------------------------------------------------------- xuất rải và kéo


@ca("v602 xuất rải: đơn Sales đã giao đủ 2 giờ được xếp cùng bill quầy, cùng một đường")
def _rai_sales():
	xep = []
	f = NS(set_user=lambda *a: None, log_error=lambda *a, **kw: None, get_traceback=lambda: "",
		db=NS(get_all=lambda *a, **kw: [D(name="Q1", vgb_quay="TCV")]))
	g = dict(frappe=f, cfg=lambda: D(tu_ghi_so_bat=1, tu_ghi_so_gio="23:00"), cint=lambda x: int(x or 0),
		hddt_cho_xuat=NS(xuat_ngay_cu_truoc=lambda: True), nowdate=lambda: "2026-10-18",
		now_datetime=lambda: datetime(2026, 10, 18, 15, 10), _gio_hop_le=lambda x: x, hddt_bu=hddt_bu,
		_quay_tu_ghi_so=lambda: ["TCV"], _sales_da_giao_du_gio=lambda ngay, truong: [D(name="S1", vgb_quay="")],
		_khach_le=lambda: "", _ly_do_xep=lambda r, k="": "",
		_xep_ghi_so=lambda ds, ngay, cho_xuat=True, nguon="": xep.append((list(ds), nguon)) or len(ds),
		_bao_hoan_phat_hanh=lambda *a: None)
	nap("xuat_rai_trong_ngay", g)()
	la("xếp cả bill quầy lẫn đơn Sales đã giao", xep, [(["Q1", "S1"], "xuat-rai")])


@ca("v602 đơn Sales đã giao: lọc vận đơn Đã giao, đủ 2 giờ, đúng ngày; chưa có vận đơn nào thì trả rỗng")
def _sales_da_giao():
	goi = []

	def get_all(dt, **kw):
		goi.append((dt, kw.get("filters")))
		return ["HDB-9"] if dt == "Van Don" else [D(name="HDB-9")]
	f = NS(db=NS(get_all=get_all), log_error=lambda *a, **kw: None, get_traceback=lambda: "")
	from datetime import timedelta
	g = dict(frappe=f, hddt_bu=hddt_bu, now_datetime=lambda: datetime(2026, 10, 18, 15, 0), timedelta=timedelta)
	kq = nap("_sales_da_giao_du_gio", g)("2026-10-18", ["name"])
	la("trả đơn", [r.name for r in kq], ["HDB-9"])
	vd = goi[0][1]
	la("lọc vận đơn", (vd["trang_thai"], vd["giao_luc"], vd["ngay_giao"]), ("Đã giao", ["<=", datetime(2026, 10, 18, 13, 0)], "2026-10-18"))
	si = goi[1][1]
	dung("chỉ đơn Sales nháp đúng ngày", si["docstatus"] == 0 and si["posting_date"] == "2026-10-18" and si["vgb_quay"] == ["in", ["", None]])
	goi.clear()
	f.db.get_all = lambda dt, **kw: []
	la("không vận đơn thì rỗng", nap("_sales_da_giao_du_gio", dict(g))("2026-10-18", ["name"]), [])


@ca("v602 kéo đơn treo: đổi ngày qua cửa giữ ngày bán gốc, rồi xếp ghi sổ; bill quầy gọi đích danh cũng kéo được")
def _keo():
	da_doi, xep = [], []
	si = {"HDB-1": D(name="HDB-1", docstatus=0, posting_date="2026-10-17"),
		"Q-1": D(name="Q-1", docstatus=0, posting_date="2026-10-17")}
	f = NS(get_doc=lambda dt, ten: si[ten], local=NS(message_log=[]), get_roles=lambda: ["Accounts Manager"],
		whitelist=lambda *a, **kw: (lambda h: h),
		throw=lambda m: (_ for _ in ()).throw(Exception(m)), db=NS(commit=lambda: None, rollback=lambda: None))
	treo = [D(name="HDB-1", posting_date="2026-10-17", grand_total=100, custom_pancake_display_id="91", ly_do="san_sang", hom_nay=0)]
	g = dict(frappe=f, cint=lambda x: int(x or 0), flt=float, json=__import__("json"), nowdate=lambda: "2026-10-18",
		_kiem_quyen_ghi_so=lambda: None, QUYEN_SUA_NGAY={"Accounts Manager"}, _quet_don_treo=lambda n: treo,
		_bill_quay_nhap_cu=lambda ten, n: [D(name=t, posting_date="2026-10-17", grand_total=50, custom_pancake_display_id="") for t in ten],
		hddt_cho_xuat=NS(xuat_ngay_cu_truoc=lambda: True),
		_doi_ngay_ban_nhap=lambda s, ngay, ly_do, cach: da_doi.append((s.name, ngay)),
		_xep_ghi_so=lambda ds, ngay, cho_xuat=True, nguon="": xep.append((list(ds), ngay, nguon)) or len(ds))
	kq = nap("keo_va_ghi_so", g)(ds='["HDB-1","Q-1"]', chay_thu=0)
	la("đổi ngày qua cửa chung", da_doi, [("HDB-1", "2026-10-18"), ("Q-1", "2026-10-18")])
	la("xếp ghi sổ đủ hai", xep, [(["HDB-1", "Q-1"], "2026-10-18", "keo")])
	la("đếm", (kq["keo"], kq["da_xep"], kq["loi"]), (2, 2, []))
	dung("không tự ghi sổ trong yêu cầu web", "si.submit()" not in _than("keo_va_ghi_so"))


# ------------------------------------------------------------- báo động


@ca("v602 báo động: còn đơn hôm nay chưa ghi sổ thì báo Zalo chủ đề Hoá đơn, loại Cảnh báo; không còn thì im")
def _bao_dong():
	import sys
	from unittest.mock import patch
	gui = []
	kz = NS(bao_hoac_ghi_loi=lambda *a, **kw: gui.append((a, kw)) or ["Z1"])
	for rows, mong in (([D(name="S1", vgb_quay="", grand_total=100, custom_pancake_display_id="91"),
			D(name="Q1", vgb_quay="TCV", grand_total=50)], 1), ([], 0)):
		gui.clear()
		f = NS(set_user=lambda *a: None, db=NS(commit=lambda: None), log_error=lambda *a, **kw: None, get_traceback=lambda: "")
		g = dict(frappe=f, cfg=lambda: D(tu_ghi_so_bat=1, tu_ghi_so_quay="TCV", pancake_shop_id="S"),
			cint=lambda x: int(x or 0), flt=float, _khach_le=lambda: "", _con_nhap=lambda ngay, q: rows,
			_quay_bat_cfg=lambda c: ["TCV"], _sepay_theo_don=lambda *a: {}, _ly_do_treo=lambda r, s: "san_sang",
			ghi_so_dieu_kien=NS(ly_do=lambda r, **kw: "chua_ve_tien"), hddt_bu=hddt_bu,
			now_datetime=lambda: datetime(2026, 10, 17, 23, 20), LY_DO_TREO={"chua_ve_tien": "Chưa về tiền"})
		with patch.dict(sys.modules, {"vagabond.kenh_zalo": kz}):
			import vagabond
			co = hasattr(vagabond, "kenh_zalo")
			cu = getattr(vagabond, "kenh_zalo", None)
			vagabond.kenh_zalo = kz
			try:
				nap("bao_dong_ghi_so", g)("2026-10-17")
			finally:
				if co:
					vagabond.kenh_zalo = cu
				else:
					delattr(vagabond, "kenh_zalo")
		la("%d đơn: số tin" % len(rows), len(gui), mong)
		if mong:
			a, kw = gui[0]
			la("loại, chủ đề", a[:2], ("canh_bao", "hoa_don"))
			dung("tiêu đề có số đơn", "còn 2 đơn chưa ghi sổ" in a[2])
			la("chống trùng theo ngày giờ", kw["khoa"], "ghi-so-ket:2026-10-17:23:20")


@ca("v602 lịch: báo động 23:20, 23:45 và 07:30; chủ đề Hoá đơn có ở máy chủ và màn Cài đặt")
def _lich():
	h = (GOC / "hooks.py").read_text()
	dung("23:20 và 23:45", '"20,45 23 * * *", []).append("vagabond.ban_hang.bao_dong_ghi_so_toi")' in h)
	dung("07:30 sáng", '"30 7 * * *", []).append("vagabond.ban_hang.bao_dong_ghi_so_sang")' in h)
	# Đọc hằng số từ mã nguồn, không import (kenh_zalo cần frappe.utils thật).
	kz = {}
	for n in ast.parse((GOC / "kenh_zalo.py").read_text()).body:
		if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("CHU_DE", "TEN_CHU_DE"):
			kz[n.targets[0].id] = ast.literal_eval(n.value)
	dung("máy chủ có chủ đề hoa_don", "hoa_don" in kz["CHU_DE"] and kz["TEN_CHU_DE"]["hoa_don"] == "Hoá đơn")
	js = (GOC / "public" / "js" / "cai_dat_loi_chung.js").read_text()
	dung("màn Cài đặt có chủ đề và dòng giải thích", "'hoa_don'" in js and "hoa_don: ['🧾', 'Hoá đơn'," in js)
