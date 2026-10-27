# -*- coding: utf-8 -*-
"""v613: tin Zalo không mang tổng tiền đơn, tin tồn kho và sản xuất có ảnh bảng, tin duyệt chi.

Anh Việt 27/10/2026:
  - "Mẫu tin báo Zalo mà đơn đặt hàng em bỏ tổng tiền đơn đi dùm anh (nói chung là
    tổng tiền sẽ không hiển thị gì cả trong bất cứ tin nhắn)". Anh chọn: bỏ ở mọi tin
    đơn hàng; tin kế toán và báo cáo Ban giám đốc giữ số tiền. Luật gom về MỘT chỗ:
    tin của bộ phận ngoài BO_PHAN_DUOC_TIEN không mang số tiền, cửa ghi sổ tin lọc
    lần cuối.
  - Tồn bánh cuối ngày từng chi nhánh gửi bằng ẢNH bảng (Zalo Bot có sendPhoto).
  - Tin tồn âm, hàng nằm im 30 ngày; sản lượng cuối ngày (ảnh), thiếu nguyên liệu
    ngày mai, lệnh sản xuất quá ngày chưa xong.
  - Báo từng bước duyệt phiếu chi APP, đề nghị chi đã chi, đã hoàn tiền cho khách.

Ca chạy hàm THẬT (nạp từ mã nguồn hoặc import), chỉ thay tầng Frappe và kênh Zalo giả;
không gọi thêm hàm nào ngoài chuỗi máy chạy (điều 15).
"""
import ast
import sys
import types
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

import vagabond  # noqa: E402
from vagabond import anh_bang as ab  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import tin_kho as tk  # noqa: E402
from vagabond import tin_ton_sx as ts  # noqa: E402
from vagabond.khung.kiem_thu.thu_su_co_290 import nap  # noqa: E402

GOI = Path(__file__).resolve().parents[2]
TIEN = kz.MAU_TIEN


class D(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def _zalo():
	goi = []

	def ghi(loai, chu_de, tieu_de, dong=None, **kw):
		goi.append(D(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=list(dong or [])))
		return ["ZL-1"]
	return types.SimpleNamespace(bao=ghi, bao_hoac_ghi_loi=ghi, cat_dong=kz.cat_dong, chet_giao_dich=lambda e: False), goi


MOI = ("bgd_app_cho_duyet", "kt_app_da_duyet", "kt_app_tra_lai", "kt_app_da_chi", "kt_de_nghi_chi_da_chi", "bh_hoan_tien_xong",
	"bep_thieu_nvl_ngay_mai", "bep_san_luong_ngay", "bep_lenh_chua_xong", "kho_ton_quay_cuoi_ngay", "kho_ton_am", "kho_hang_nam_im")


@ca("v613 danh mục: đủ 12 tin mới, đúng bộ phận; tin Bán hàng, Thu mua, Kho, Bếp bị cấm số tiền, Kế toán và Ban giám đốc thì không")
def _danh_muc():
	la("có đủ tin mới", [m for m in MOI if m not in kz.TIN], [])
	la("bộ phận", [kz.TIN[m][0] for m in MOI], ["Ban giám đốc"] + ["Hoá đơn, kế toán"] * 4 + ["Bán hàng, cửa hàng"]
		+ ["Bếp"] * 3 + ["Kho"] * 3)
	cam = sorted(m for m in kz.TIN if kz.khong_duoc_tien(m))
	dung("mọi tin đơn hàng bị cấm tiền", all(m in cam for m in ("bh_don_web_moi", "bh_don_web_treo", "bh_pancake_lech_tong",
		"bh_ahamove_huy", "bh_tiec", "tm_don_mua_moi", "tm_don_mua_tre_hen", "tm_hang_ve_chua_hoa_don", "bh_hoan_tien_xong")))
	dung("tin kế toán, báo cáo giám đốc, phiếu chi chờ duyệt được mang tiền", not any(kz.khong_duoc_tien(m) for m in
		("kt_hoan_tien", "kt_de_nghi_chi", "hd_don_chua_ghi_so", "bgd_bao_cao_ngay", "bgd_app_cho_duyet", "kt_app_da_chi")))
	la("mã lạ không bị cấm (không có bộ phận)", kz.khong_duoc_tien("ma_la"), False)


@ca("v613 bo_dong_tien: tiêu đề chỉ xoá con số, dòng sau có tiền bỏ cả dòng; nhận 1.234.567 đ, 650.000đ, 50.000 VND")
def _bo_tien():
	t, bo = kz.bo_dong_tien("📊 ĐƠN WEB 650.000 đ: Khách A\n- Nhận 14:00\n- Tổng 650.000đ, tự lấy\n- 12 cái bánh\n- Phí 30.000 VND")
	la("tin sạch", t, "📊 ĐƠN WEB : Khách A\n- Nhận 14:00\n- 12 cái bánh")
	la("số chỗ đã bỏ", bo, 3)
	la("tin không tiền giữ nguyên", kz.bo_dong_tien("A\n- 3 cái, 16cm\n- ngày 27/10"), ("A\n- 3 cái, 16cm\n- ngày 27/10", 0))
	dung("không nhầm số lượng có đơn vị", not TIEN.search("Bột mì: 25 Kg") and not TIEN.search("đã làm 3/5 cái"))


@ca("v613 cửa ghi sổ tin: tin đơn hàng lọt tiền thì bỏ trước khi ghi và để Error Log; tin kế toán giữ nguyên số tiền")
def _cua_ghi():
	ghi, loi = [], []

	class Tin(dict):
		def insert(self, **k):
			ghi.append(dict(self))
	fr = types.SimpleNamespace(generate_hash=lambda length=8: "h" * length, db=types.SimpleNamespace(savepoint=lambda *a: None,
		rollback=lambda **k: None), get_doc=lambda d: Tin(d), log_error=lambda *a, **k: loi.append(a), DuplicateEntryError=KeyError)
	nhom = [{"ten_nhom": "VH Đơn hàng", "chat_id": "c1", "bat": 1, "tin_nhan": "bh_don_web_moi, kt_hoan_tien"}]
	with um.patch.object(kz, "frappe", fr), um.patch.object(kz, "_cac_nhom", lambda: nhom):
		kz._ghi_hop_thu({"loai": "thong_bao", "chu_de": "don_web", "tieu_de": "Đơn web mới", "ma_tin": "bh_don_web_moi",
			"dong": ["Khách A", "Tổng 650.000 đ, tự lấy"], "khoa": "k1", "anh": "https://x.test/a.png"})
		kz._ghi_hop_thu({"loai": "viec", "chu_de": "cong_no", "tieu_de": "Hoàn tiền 50.000 đ", "ma_tin": "kt_hoan_tien",
			"dong": ["Hoá đơn gốc SI-1 (tổng 100.000 đ)"], "khoa": "k2"})
	la("ghi hai dòng", len(ghi), 2)
	dung("đơn web không còn tiền", not TIEN.search(ghi[0]["noi_dung"]) and "Khách A" in ghi[0]["noi_dung"])
	la("ảnh vào sổ tin", (ghi[0]["anh"], ghi[1]["anh"]), ("https://x.test/a.png", ""))
	la("một Error Log cho nơi phát lọt tiền", [a[1] for a in loi], ["kenh_zalo: tin don hang lot tien"])
	dung("hoàn tiền giữ số", "50.000 đ" in ghi[1]["noi_dung"] and "100.000 đ" in ghi[1]["noi_dung"])


@ca("v613 nơi phát tin đơn hàng soạn KHÔNG tiền: đơn web mới (bốn kiểu phí), đơn web treo, tiệc, đơn mua, đơn trễ, hàng về chưa hoá đơn")
def _noi_phat_khong_tien():
	for phi in ({"trang_thai": "tu_lay"}, {"mien_phi": 1}, {"phi_khach": None}, {"phi_khach": 30000}):
		d = tk.dong_tien_don_web(650000, phi)
		dung("phí %r không có tiền: %s" % (phi, d), not TIEN.search(d) and "650" not in d and "30.000" not in d)
	la("bốn câu phí", [tk.dong_tien_don_web(1, p) for p in ({"trang_thai": "tu_lay"}, {"mien_phi": 1}, {"phi_khach": 5})],
		["Khách tự lấy", "Miễn phí giao", "Có phí giao, đã tính vào đơn"])
	from vagabond import don_web
	t = don_web.soan_tin_sales({"name": "DW-1", "ho_ten": "A", "dien_thoai": "09", "tien_banh": 650000, "ngay_nhan": "2026-10-28 14:00"})
	dung("đơn web treo không tiền", not TIEN.search(t) and "650" not in t)
	import re
	from datetime import datetime
	t = nap("tiec_web.py", "soan_tin", {"re": re, "datetime": datetime})({"ten_tiec": "Tiệc trà", "ten": "B", "sdt": "09", "so_ve": 2, "tong_tien": 900000, "url": "u"})
	dung("tiệc không tiền", not TIEN.search(t) and "900" not in t)
	gia, goi = _zalo()
	po = D(name="PO-1", supplier_name="Bơ Sữa", schedule_date="2026-10-29", grand_total=12500000, vgb_huy=0,
		items=[D(item_code="BO", item_name="Bơ lạt", qty=2, uom="Thùng")])
	with um.patch.object(tk, "kenh_zalo", gia):
		tk.khi_ghi_so_don_mua(po)
		with um.patch.object(tk.frappe, "get_all", lambda dt, **k: [D(name="PO-9", supplier_name="NCC", schedule_date="2026-10-20",
				posting_date="2026-10-20", per_received=50, grand_total=7000000)], create=True):
			tk.nhac_don_mua_tre_hen()
			tk.nhac_hang_ve_chua_hoa_don()
	la("ba tin thu mua", [g.ma_tin for g in goi], ["tm_don_mua_moi", "tm_don_mua_tre_hen", "tm_hang_ve_chua_hoa_don"])
	for g in goi:
		dung("%s không tiền" % g.ma_tin, not any(TIEN.search(x) or "12.500.000" in x or "7.000.000" in x for x in g.dong))
	nguon = (GOI / "don_hang.py").read_text(encoding="utf-8").split("def _bao_lech_tong_pancake")[1].split("\ndef ")[0]
	dung("lệch tổng Pancake không in số tiền (dò chuỗi: hàm chỉ ghi Zalo, không chạy được ngoài site)",
		"%s đ" not in nguon and "mong_doi)" not in nguon)


@ca("v613 gửi kèm ảnh: có ảnh thì sendPhoto, chữ thành chú thích tối đa 2.000 ký tự; không ảnh thì sendMessage như cũ")
def _gui_anh():
	la("không ảnh", kz.goi_gui("c1", "chào"), ("sendMessage", {"chat_id": "c1", "text": "chào"}))
	m, b = kz.goi_gui("c1", "x" * 2500, " https://a.test/b.png ")
	la("có ảnh", (m, b["photo"], len(b["caption"])), ("sendPhoto", "https://a.test/b.png", kz.TOI_DA_KY_TU))
	goi = []
	with um.patch.object(kz, "_bot_chat", lambda c: "1"), um.patch.object(kz, "_goi", lambda m, b, bot: goi.append((m, b)) or ("Đã gửi", "", {})):
		kz._gui_zalo("c1", "Tồn bánh", "https://a.test/t.png")
		kz._gui_zalo("c1", "Chữ")
	la("_gui_zalo gọi đúng hàm Zalo", [g[0] for g in goi], ["sendPhoto", "sendMessage"])
	src = (GOI / "kenh_zalo.py").read_text(encoding="utf-8")
	cay = ast.parse(src)
	ham = {n.name: ast.get_source_segment(src, n) for n in cay.body if isinstance(n, ast.FunctionDef)}
	dung("_nhan_mot đọc ô ảnh (dò chuỗi: hàm chạm cơ sở dữ liệu)", '"anh"]' in ham["_nhan_mot"])
	dung("_gui_mot truyền ảnh", 'r.get("anh")' in ham["_gui_mot"])
	dung("bao() nhận anh", "anh=None" in ham["bao"])


@ca("v613 ảnh bảng THUẦN: đủ cột, cắt ở 70 dòng kèm 'và N dòng nữa', cột tên nhận phần còn lại, cột số căn phải, cắt chữ có dấu …")
def _anh_thuan():
	cot, hang = ab.chuan_bang(["Bánh", "Còn"], [["A", 1], {"o": ["B"], "nhan": "do"}] + [["X%d" % i, i] for i in range(80)])
	la("70 dòng", len(hang), 70)
	la("dòng cuối nói phần còn lại", hang[-1], (["... và 13 dòng nữa", ""], "phu"))
	la("dòng thiếu ô được bù", hang[1], (["B", ""], "do"))
	do = lambda c, d=False: len(str(c)) * 10
	w = ab.do_cot(["Bánh", "Đầu ngày", "Còn"], [(["Tiramisu", "12", "3"], None)], do)
	la("tổng bề rộng đúng khung", sum(w), ab.RONG - 2 * ab.LE)
	dung("cột tên rộng nhất", w[0] > max(w[1:]))
	la("cột số", ab.cot_so(["Bánh", "ĐVT", "Còn"], [(["A", "Cái", "1.250"], None), (["... và 2", "", ""], "phu")]), {2})
	la("cắt chữ", ab.cat_chu("Hannari 16cm", 60, do), "Hanna…")
	t1, t2 = ab.ten_tep("ton-TCV"), ab.ten_tep("ton-TCV")
	dung("tên tệp khó đoán, đúng tiền tố", t1.startswith("zalo-ton-tcv-") and t1.endswith(".png") and t1 != t2 and len(t1) > 30)


@ca("v613 ảnh bảng VẼ THẬT bằng Pillow và phông Vagabond Sans (bỏ qua khi máy kiểm không có Pillow)")
def _anh_ve():
	try:
		import PIL  # noqa: F401
	except Exception:
		dung("máy không có Pillow: ca vẽ chạy trên site và máy làm việc", True)
		return
	png = ab.ve_bang("Tồn bánh cuối ngày 27/10/2026", "District 1", ["Bánh", "Đầu ngày", "Còn"],
		[["Hannari 16cm", "4", "2"], {"o": ["Kankin", "1", "-1"], "nhan": "do"}], "Còn 2 bánh.")
	la("là PNG", png[:8], b"\x89PNG\r\n\x1a\n")
	from io import BytesIO

	from PIL import Image
	im = Image.open(BytesIO(png))
	la("rộng 1080", im.size[0], ab.RONG)
	dung("có màu đỏ ở dòng âm", any(p[0] > 150 and p[1] < 80 for p in im.convert("RGB").getdata()))


@ca("v613 tồn quầy THUẦN: chỉ dòng đang theo dõi, còn = đầu + nhập - bán - hỏng + chỉnh, số âm đỏ lên đầu, cột Chỉnh chỉ khi có")
def _ton_quay():
	dong = [D(ma_hang="A", ten_banh="Hannari", ton_dau=4, nhap_1=6, hong=1, dieu_chinh=0),
		D(ma_hang="B", ten_banh="Kankin", ton_dau=1, hong=2),
		D(ma_hang="C", ten_banh="Bỏ qua", ton_dau=0)]
	cot, hang, tong = ts.hang_ton_quay(dong, {"A": 7})
	la("cột", cot, ["Bánh", "Đầu ngày", "Nhập", "Bán", "Hỏng", "Còn"])
	la("hàng", [(h["o"], h["nhan"]) for h in hang], [(["Kankin", "1", "0", "0", "2", "-1"], "do"), (["Hannari", "4", "6", "7", "1", "2"], None)])
	la("tổng", (tong["con"], tong["loai"], tong["ban"], tong["am"]), (2.0, 1, 7.0, ["Kankin"]))
	cot, hang, _ = ts.hang_ton_quay([D(ma_hang="A", ten_banh="A", ton_dau=1, dieu_chinh=-1)], {})
	dung("có cột Chỉnh khi có điều chỉnh", "Chỉnh" in cot)
	chu = ts.chu_ton_quay("District 1", "2026-10-27", tong)
	la("chú thích", chu[:3], ["District 1, ngày 27/10", "Còn 2 bánh, 1 loại", "Trong ngày: nhập 6, bán 7, hỏng 3"])
	dung("chú thích nhắc số âm, không tiền", "Kankin" in chu[3] and not any(TIEN.search(x) for x in chu))


@ca("v613 tồn quầy 23:00 chạy THẬT: mỗi chi nhánh có phiếu một tin kèm ảnh; vẽ hỏng thì tin chữ kê từng bánh")
def _ton_quay_gui():
	from vagabond import kiem_kho as that
	kk = types.SimpleNamespace(dang_theo_doi=that.dang_theo_doi, tinh_co_the_ban=that.tinh_co_the_ban, tong_nhap=that.tong_nhap,
		_diem_co_quay=lambda: [{"ma": "TCV", "ten": "District 1"}, {"ma": "NVHTN", "ten": "NVHTN"}],
		ten_phieu=lambda m, n: "KKD-%s-%s" % (m, n), DT="Vagabond Kiem Kho Diem", DT_DONG="Vagabond Kiem Kho Dong",
		O_NHAP=("nhap_1",), da_ban=lambda m, n: {"A": 2})
	for anh, mong in (("https://x.test/t.png", 3), (None, 4)):
		gia, goi = _zalo()
		ve = types.SimpleNamespace(anh_bang=lambda *a, _a=anh: _a)
		fr = sys.modules["frappe"]
		with um.patch.object(ts, "kenh_zalo", gia), um.patch.dict(sys.modules, {"vagabond.kiem_kho": kk, "vagabond.anh_bang": ve}), \
				um.patch.object(vagabond, "kiem_kho", kk, create=True), um.patch.object(vagabond, "anh_bang", ve, create=True), \
				um.patch.object(ts, "nowdate", lambda: "2026-10-27"), \
				um.patch.object(fr.db, "exists", lambda dt, n: n.startswith("KKD-TCV"), create=True), \
				um.patch.object(fr, "get_all", lambda *a, **k: [D(ma_hang="A", ten_banh="Hannari", ton_dau=3, nhap_1=1)], create=True):
			ts.gui_ton_quay_cuoi_ngay()
		la("một tin cho chi nhánh có phiếu (ảnh %s)" % bool(anh), [(g.ma_tin, g.loai, g.khoa) for g in goi],
			[("kho_ton_quay_cuoi_ngay", "ban_tin", "ton-quay:TCV:2026-10-27")])
		la("ảnh đi kèm", goi[0].anh, anh)
		la("số dòng chữ", len(goi[0].dong), mong)


@ca("v613 tồn âm, hàng nằm im THUẦN: gom theo kho; hàng mới nhập hay vừa xuất trong 30 ngày không bị kể")
def _ton_am_nam_im():
	r = ts.gom_ton_am([D(kho="K1", ma="A", ten="Bơ", dvt="Kg", sl=-2), D(kho="K1", ma="B", ten="Bột", dvt="Kg", sl=-5),
		D(kho="K2", ma="C", ten="Hộp", dvt="Cái", sl=3)])
	la("âm nhiều lên đầu, bỏ món dương", {k: [x["ten"] for x in v] for k, v in r.items()}, {"K1": ["Bột", "Bơ"]})
	ton = [D(kho="K", ma=m, ten=m, dvt="Kg", sl=1) for m in ("cu_chua_xuat", "cu_xuat_lau", "moi_nhap", "vua_xuat")]
	dau = {("cu_chua_xuat", "K"): "2026-08-01", ("cu_xuat_lau", "K"): "2026-08-01", ("moi_nhap", "K"): "2026-10-20",
		("vua_xuat", "K"): "2026-08-01"}
	xuat = {("cu_xuat_lau", "K"): "2026-09-01", ("vua_xuat", "K"): "2026-10-25"}
	r = ts.chon_nam_im(ton, xuat, dau, "2026-09-27")
	la("hai món nằm im, chưa xuất bao giờ lên đầu", [(x["ten"], x["ghi"]) for x in r["K"]],
		[("cu_chua_xuat", "chưa xuất lần nào"), ("cu_xuat_lau", "xuất lần cuối 01/09")])


@ca("v613 sản lượng và thiếu nguyên liệu THUẦN: món thiếu đỏ lên đầu, món ngoài yêu cầu ghi rõ; nguyên liệu nhân theo mẻ công thức")
def _san_xuat():
	cot, hang, tong = ts.bang_san_luong({"A": {"ten": "Hannari", "sl": 10, "dvt": "Cái"}, "B": {"ten": "Candle", "sl": 4, "dvt": "Cái"}},
		{"A": {"ten": "Hannari", "sl": 6}, "B": {"sl": 4}, "C": {"ten": "Bánh thử", "sl": 2, "dvt": "Cái"}})
	la("bảng", [(h["o"], h["nhan"]) for h in hang], [(["Hannari", "Cái", "10", "6", "4"], "do"),
		(["Bánh thử", "Cái", "0", "2", "ngoài yêu cầu"], None), (["Candle", "Cái", "4", "4", "0"], None)])
	la("tổng", (tong["mon"], tong["du"], tong["thieu"]), (2, 1, ["Hannari thiếu 4 Cái"]))
	thanh = {"BOM-A": {"so_ra": 10, "dong": [{"ma": "BO", "ten": "Bơ", "dvt": "Kg", "sl": 2}, {"ma": "BOT", "ten": "Bột", "dvt": "Kg", "sl": 1}]}}
	thieu, khong = ts.tinh_thieu_nvl([{"ma": "A", "ten": "Hannari", "sl": 20, "bom": "BOM-A"}, {"ma": "X", "ten": "Món mới", "sl": 1, "bom": None}],
		thanh, {"BO": 1.5, "BOT": 5})
	la("thiếu bơ 2,5 Kg (cần 4)", [(x["ten"], round(x["sl"], 3), x["ghi"]) for x in thieu], [("Bơ", 2.5, "cần 4, kho bếp còn 1,5")])
	la("món chưa có công thức", khong, ["Món mới"])
	la("tên bếp", [ts.bep_cua_ten("Bếp Pastry"), ts.bep_cua_ten("bếp baker"), ts.bep_cua_ten("Bếp Lab"), ts.ten_bep("pastry")],
		["pastry", "baker", None, "Bếp Pastry"])


@ca("v613 phiếu chi APP đổi bước chạy THẬT: chờ GĐ báo Ban giám đốc, duyệt, trả lại, đã chi báo kế toán; cùng bước hoặc phiếu khác thì im")
def _duyet_chi():
	from vagabond import duyet_chi as dc
	gia, goi = _zalo()
	loi = []
	fr = types.SimpleNamespace(session=types.SimpleNamespace(user="gd@x"), log_error=lambda *a, **k: loi.append(a),
		get_traceback=lambda: "", utils=types.SimpleNamespace(get_fullname=lambda u: "Anh Việt", get_url=lambda p: "https://e.test" + p))

	def doc(cu, moi, app=1):
		d = D(name="APP-1", workflow_state=moi, paid_amount=12500000, party_name="Bơ Sữa", modified="2026-10-27 10:00:00",
			vgb_chi_ma_gd="FT123", payment_type="Pay", party_type="Supplier",
			references=[D(reference_doctype="Purchase Order" if app else "Purchase Invoice")])
		d.get_doc_before_save = lambda: D(workflow_state=cu)
		return d
	with um.patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), um.patch.object(vagabond, "kenh_zalo", gia), \
			um.patch.object(dc, "frappe", fr):
		for cu, moi in (("Chờ FIN kiểm tra", dc.TT_CHO_GD), (dc.TT_CHO_GD, dc.TT_DA_DUYET_CHI),
				(dc.TT_CHO_GD, dc.TT_TRA_LAI), (dc.TT_DA_DUYET_CHI, dc.TT_DA_GHI_SO)):
			dc.bao_doi_buoc(doc(cu, moi))
		dc.bao_doi_buoc(doc(dc.TT_CHO_GD, dc.TT_CHO_GD))
		dc.bao_doi_buoc(doc(dc.TT_NHAP, dc.TT_CHO_GD, app=0))
		dc.bao_doi_buoc(doc(dc.TT_NHAP, dc.TT_CHO_FIN))
	la("không Error Log", loi, [])
	la("bốn tin đúng mã", [x.ma_tin for x in goi], ["bgd_app_cho_duyet", "kt_app_da_duyet", "kt_app_tra_lai", "kt_app_da_chi"])
	la("loại tin", [x.loai for x in goi], ["viec", "viec", "viec", "thong_bao"])
	la("dòng đầu có tiền và nhà cung cấp", goi[0].dong[0], "12.500.000 đ cho Bơ Sữa")
	la("bước cuối khoá theo phiếu (Desk và app không báo hai lần)", goi[3].khoa, "app-buoc:APP-1:" + dc.TT_DA_GHI_SO)
	dung("bước khác khoá kèm mốc sửa (trả lại nhiều lần vẫn báo)", goi[2].khoa.endswith("2026-10-27 10:00:00"))
	dung("đã chi nêu mã giao dịch", "FT123" in goi[3].dong[1])
	la("mọi bước báo đều có hàm gửi", sorted(t[0] for t in dc.TIN_BUOC.values() if not hasattr(dc, t[0])), [])


@ca("v613 hoàn tiền xong báo Sales KHÔNG tiền, không số tài khoản; đề nghị chi đã chi báo kế toán có số tiền")
def _hoan_va_de_nghi():
	tieu, dong = nap("hoan_tien.py", "soan_da_hoan", {})("HT-1", "Chị Lan", "SI-1", "Bánh hỏng")
	la("tiêu đề", tieu, "Đã hoàn tiền cho khách Chị Lan")
	dung("không tiền", not any(TIEN.search(x) for x in [tieu] + dong))
	gia, goi = _zalo()
	fr = types.SimpleNamespace(db=types.SimpleNamespace(commit=lambda: None), log_error=lambda *a, **k: goi.append("LOI"),
		get_traceback=lambda: "", utils=types.SimpleNamespace(get_fullname=lambda u: "Thu Mua A", get_url=lambda p: "https://e.test" + p))
	f = nap("de_nghi_chi.py", "_bao_da_chi", dict(frappe=fr, tien_phieu=lambda d: 1500000, _tien=lambda v: "1.500.000"))
	d = D(name="DNC-1", ten_khoan_chi="Mua bơ", nguoi_tao="tm@x")
	d.as_dict = lambda: dict(d)
	with um.patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), um.patch.object(vagabond, "kenh_zalo", gia):
		f(d, "FT9")
	la("đúng tin", [(x.ma_tin, x.khoa) for x in goi], [("kt_de_nghi_chi_da_chi", "de-nghi-chi-da-chi:DNC-1")])
	la("dòng", goi[0].dong, ["1.500.000 đ · Mua bơ", "Người lập: Thu Mua A", "Đã khớp giao dịch ngân hàng FT9"])
	src = (GOI / "hoan_tien.py").read_text(encoding="utf-8")
	dung("hoan_thanh gọi báo Sales trước commit (dò chuỗi: hàm cần site)",
		"_bao_sales_da_hoan(ho_so)" in src.split("def hoan_thanh(")[1].split("\ndef ")[0])
	src = (GOI / "de_nghi_chi.py").read_text(encoding="utf-8")
	dung("khớp sao kê gọi báo đã chi", "_bao_da_chi(doc, ma_gd)" in src.split("def _khi_khop_ttnb(")[1].split("\ndef ")[0])


@ca("v613 hooks: sáu lịch tin mới, lịch dọn ảnh và hai hook phiếu chi đã nối đúng hàm có thật")
def _hooks():
	src = (GOI / "hooks.py").read_text(encoding="utf-8")
	for ham in ("tin_ton_sx.gui_ton_quay_cuoi_ngay", "tin_ton_sx.nhac_ton_am", "tin_ton_sx.nhac_hang_nam_im",
			"tin_ton_sx.nhac_thieu_nvl_ngay_mai", "tin_ton_sx.gui_san_luong_bep", "tin_ton_sx.nhac_lenh_chua_xong",
			"anh_bang.don_anh_cu", "duyet_chi.bao_doi_buoc"):
		mod, ten = ham.split(".")
		dung("hooks nối %s" % ham, ("vagabond." + ham) in src)
		cay = ast.parse((GOI / (mod + ".py")).read_text(encoding="utf-8"))
		dung("hàm %s có thật" % ham, any(isinstance(n, ast.FunctionDef) and n.name == ten for n in cay.body))
	for gio, ham in (("0 23 * * *", "gui_ton_quay_cuoi_ngay"), ("5 8 * * 1", "nhac_hang_nam_im"), ("45 20 * * *", "nhac_thieu_nvl_ngay_mai"),
			("0 21 * * *", "gui_san_luong_bep")):
		dung("giờ %s cho %s" % (gio, ham), '("%s", "vagabond.tin_ton_sx.%s")' % (gio, ham) in src)
