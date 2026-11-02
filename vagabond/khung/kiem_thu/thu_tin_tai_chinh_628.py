# -*- coding: utf-8 -*-
"""v628: tin Zalo Tài chính và tin kiểm kê sáng của bếp (anh Việt duyệt mẫu 02/11/2026).

Số trong các ca lấy đúng số thật trên site sáng 02/11/2026 mà anh đã xem trên ảnh
mẫu, để chữ máy soạn được đối chiếu với chữ anh duyệt. Các ca chạm hệ chạy HÀM
THẬT, chỉ thay tầng Frappe và kênh Zalo bằng bản giả ghi lại lời gọi; không gọi
thêm hàm nào ngoài chuỗi máy chạy.
"""

import sys
import unittest.mock as um
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
# Bản Frappe giả chung chưa có get_url khi chạy lẻ tệp này (cùng cách thu_tin_zalo_604).
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import kiem_ke as kk  # noqa: E402
from vagabond import tai_chinh as tc  # noqa: E402
from vagabond import tin_tai_chinh as ttc  # noqa: E402
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap  # noqa: E402
from vagabond.patches import v628_tin_tai_chinh as pv  # noqa: E402

GOI = Path(__file__).resolve().parents[2]
EM = "—"
EN = "–"

KET_0111 = {
	"tong": {"tong": 977702455, "ngan_hang": 977702455, "tien_mat": 0, "tam_ung": 35714582, "chua_chot": 6, "loi": 0},
	"dong": [
		{"nguon": "nh:31561568", "ten": "MB Bank ···1568", "so_du": 698992276, "ghi": []},
		{"nguon": "nh:700037279585", "ten": "Shinhan Bank ···9585", "so_du": 242995597, "ghi": ["Số dư SePay báo"]},
		{"nguon": "nh:616066", "ten": "ACB ···6066 (tạm ứng)", "so_du": None, "ghi": ["Chưa chốt số dư đầu"]},
		{"nguon": "nh:612160615", "ten": "MB ···0615 (tạm ứng)", "so_du": 35714582, "ghi": []},
		{"nguon": "tm:TCV", "ten": "Két District 1", "so_du": None, "ghi": ["Chưa chốt số dư đầu"],
			"ca": {"luc": "2026-11-01 22:07:01", "dem": 4885000}},
		{"nguon": "tm:QUY", "ten": "Quỹ tiền mặt công ty", "so_du": None, "ghi": ["Chưa chốt số dư đầu"]},
	],
}
DT_0111 = {
	"vao": 48015374, "ra": 40538624, "rong": 7476750, "thieu": [],
	"ngay": [{"ngay": "2026-11-01", "vao_tm": 4478000}],
	"lon_nhat": {"ra": [
		{"ngay": "2026-11-01", "so": 15725120, "tk": "MB Bank ···1568", "mo_ta": "MBCT VAGABOND APP 26 10 123 THANH TOAN HD2151"},
		{"ngay": "2026-11-01", "so": 5062500, "tk": "MB Bank ···1568", "mo_ta": "VAGABOND APP.26.10.125 THANH TOAN HD28864"},
		{"ngay": "2026-11-01", "so": 4860000, "tk": "MB Bank ···1568", "mo_ta": "khoản thứ ba không được nêu"},
	]},
	"noi_bo": {"so": 2, "tien": 24956860},
}


def _khong_gach(nhan, chu):
	dung(nhan + ": không có em dash, en dash", EM not in chu and EN not in chu)


# ------------------------------------------------------------------ THUẦN

@ca("v628 tin 1: tiền cuối ngày đủ từng tài khoản, nguồn chưa chốt gom một dòng, số đếm chốt ca")
def _cuoi_ngay():
	td, dong = ttc.soan_cuoi_ngay("2026-11-01", KET_0111, DT_0111)
	la("tiêu đề", td, "Tiền cuối ngày 01/11/2026")
	la("các dòng", dong, [
		"Tổng tiền đang có: 977.702.455 đ",
		"MB Bank ···1568: 698.992.276 đ",
		"Shinhan Bank ···9585: 242.995.597 đ",
		"MB ···0615 (tạm ứng): 35.714.582 đ",
		"Chưa chốt số dư đầu: ACB ···6066 (tạm ứng), Két District 1, Quỹ tiền mặt công ty",
		"Số đếm lúc chốt ca gần nhất: District 1 4.885.000 đ",
		"Trong ngày: vào 48.015.374 đ, ra 40.538.624 đ, dư ra 7.476.750 đ",
		"Tiền mặt vào két và quỹ: 4.478.000 đ",
		"Chi lớn nhất: 15.725.120 đ (MB Bank ···1568) MBCT VAGABOND APP 26 10 123 THANH TOAN HD2151; "
		"5.062.500 đ (MB Bank ···1568) VAGABOND APP.26.10.125 THANH TOAN HD28864",
		"Chuyển nội bộ, không tính vào ra: 2 khoản, 24.956.860 đ",
	])
	chu = kz.soan_tin("ban_tin", td, dong, link="https://app.thevagabondpatisserie.com/tien-hien-co")
	dung("dưới trần một tin", len(chu) <= kz.TOI_DA_KY_TU)
	_khong_gach("tin 1", chu)


@ca("v628 tin 1: nguồn tính hỏng báo rõ, ngày hụt tiền ghi chữ hụt, dòng tiền đọc hỏng vẫn có số dư")
def _cuoi_ngay_hong():
	ket = {"tong": {"tong": 100, "loi": 1}, "dong": [{"ten": "Shinhan Bank ···9585", "so_du": None, "loi": 1,
		"ghi": ["Chưa đọc được số dư SePay lúc này"]}]}
	_, dong = ttc.soan_cuoi_ngay("2026-11-02", ket, {"vao": 10, "ra": 30, "rong": -20, "ngay": [], "thieu": ["Két NVHTN ngày 02/11"]})
	dung("tổng báo có nguồn chưa tính", "chưa tính được" in dong[0])
	dung("dòng Shinhan báo kỹ thuật", "Shinhan Bank ···9585: chưa tính được, báo kỹ thuật" in dong)
	dung("ngày âm ghi hụt", any("hụt 20 đ" in d for d in dong))
	dung("báo két chưa đọc được", any("Chưa đọc được tiền mặt: Két NVHTN" in d for d in dong))
	_, dong2 = ttc.soan_cuoi_ngay("2026-11-02", KET_0111, None)
	dung("không có dòng tiền vẫn có số dư", "MB Bank ···1568: 698.992.276 đ" in dong2 and not any("Trong ngày" in d for d in dong2))


@ca("v628 tin 2: chỉ tài khoản công ty, bỏ khoản đã gắn đủ, tổng đúng 5 khoản ngày 22-28/10")
def _tien_ra():
	cty = {"MB-CTY-31561568 - MB Bank"}
	gds = [
		{"ten": "B1", "tk": "MB-CTY-31561568 - MB Bank", "ra": 8053433, "con": 8053433, "ngay": "2026-10-28",
			"mo_ta": "MTC:00102026042973662800 MST:0318561568 CQT:1140957-Phuong Sai Gon - Thue co so 1 Thanh ph"},
		{"ten": "B2", "tk": "MB-CTY-31561568 - MB Bank", "ra": 5755504, "con": 5755504, "ngay": "2026-10-22",
			"mo_ta": "RetailVISADN-833082-222.22-USD-629507059552-ANTHROPIC  CLAUDE SUB"},
		{"ten": "B3", "tk": "MB-CTY-31561568 - MB Bank", "ra": 75973, "con": 75973, "ngay": "2026-10-22", "mo_ta": "phí"},
		{"ten": "B4", "tk": "MB-CTY-31561568 - MB Bank", "ra": 37213, "con": 37213, "ngay": "2026-10-28", "mo_ta": "thuế"},
		{"ten": "B5", "tk": "MB-CTY-31561568 - MB Bank", "ra": 35353, "con": 35353, "ngay": "2026-10-28", "mo_ta": "thuế"},
		{"ten": "B6", "tk": "MB-QUY-TAMUNG-612160615 - MB", "ra": 10000000, "con": 10000000, "ngay": "2026-10-30", "mo_ta": "tạm ứng"},
		{"ten": "B7", "tk": "MB-CTY-31561568 - MB Bank", "ra": 50000000, "con": 0, "ngay": "2026-10-27", "mo_ta": "đã gắn"},
		{"ten": "B8", "tk": "MB-CTY-31561568 - MB Bank", "ra": 900, "con": 0.5, "ngay": "2026-10-27", "mo_ta": "lẻ"},
	]
	ds = ttc.loc_tien_ra(gds, cty)
	la("đúng 5 khoản, lớn trước", [g["ten"] for g in ds], ["B1", "B2", "B3", "B4", "B5"])
	td, dong = ttc.soan_tien_ra(ds)
	la("tiêu đề", td, "Tiền ra khỏi tài khoản công ty chưa có chứng từ")
	la("dòng tổng", dong[0], "5 khoản, tổng 13.957.476 đ, ra khỏi tài khoản quá 24 giờ")
	dung("dòng thuế rút 60 ký tự", dong[1].startswith("28/10: 8.053.433 đ, MTC:") and dong[1].endswith("…"))
	la("dòng cuối là việc cần làm", dong[-1], "Kế toán lập phiếu chi hoặc bút toán cho từng khoản để sổ tiền khớp ngân hàng.")
	dung("không có khoản thì không soạn", ttc.soan_tien_ra([]) is None)
	nhieu = [dict(gds[0], ten="X%d" % i) for i in range(11)]
	_, d2 = ttc.soan_tien_ra(nhieu)
	la("quá 8 khoản thì gộp", d2[-2], "+3 khoản khác")


@ca("v628 tin 3: ngưỡng két lệch 50.000 đ hai chiều, ca quá 24 giờ")
def _nguong_ket():
	def bang(lech):
		return [{"phuong_thuc": "Chuyển khoản", "lech": 900000}, {"phuong_thuc": "Tiền mặt", "lech": lech}]
	la("49.999 không báo", ttc.can_bao_ket(bang(49999), "2026-11-01 07:00:00", "2026-11-01 22:00:00")[2], False)
	la("50.000 dư báo", ttc.can_bao_ket(bang(50000), "2026-11-01 07:00:00", "2026-11-01 22:00:00")[2], True)
	la("50.000 thiếu báo", ttc.can_bao_ket(bang(-50000), "2026-11-01 07:00:00", "2026-11-01 22:00:00")[2], True)
	la("chuyển khoản lệch không tính", ttc.can_bao_ket(bang(0), "2026-11-01 07:00:00", "2026-11-01 22:00:00")[2], False)
	la("đúng 24 giờ không báo", ttc.can_bao_ket(bang(0), "2026-11-01 07:00:00", "2026-11-02 07:00:00")[2], False)
	la("24 giờ 1 phút báo", ttc.can_bao_ket(bang(0), "2026-11-01 07:00:00", "2026-11-02 07:01:00")[2], True)


@ca("v628 tin 3: ca Sales Online 31/10 ra đúng chữ anh duyệt")
def _ket_lech_that():
	bang = [{"phuong_thuc": "Tiền mặt", "so_bill": 3, "may": 1420000, "phai_co": 2420000, "dem": 2744000, "lech": 324000},
		{"phuong_thuc": "Chuyển khoản", "so_bill": 83, "may": 76554000, "phai_co": 76554000, "dem": 76554000, "lech": 0}]
	td, dong = ttc.soan_ket_lech("Két Sales Online", "2026-10-31 06:56:11.947876", "2026-11-01 20:19:48.250891",
		1000000, bang, ".", "Lê Nguyễn Minh Quân")
	la("tiêu đề", td, "Két Sales Online lệch tiền mặt khi chốt ca")
	la("các dòng", dong, [
		"Ca mở 31/10 06:56, chốt 01/11 20:19: ca kéo dài 37 giờ, không chốt cuối ngày 31/10",
		"Tiền mặt phải có 2.420.000 đ (tiền lẻ đầu ca 1.000.000 đ, thu 3 bill 1.420.000 đ)",
		"Đếm được 2.744.000 đ, dư 324.000 đ",
		"Lý do người chốt ghi: \".\"",
		"Người chốt: Lê Nguyễn Minh Quân",
	])
	td2, d2 = ttc.soan_ket_lech("Két NVHTN", "2026-11-01 06:00:00", "2026-11-02 08:00:00", 2000000,
		[{"phuong_thuc": "Tiền mặt", "so_bill": 1, "may": 0, "phai_co": 2000000, "dem": 2000000, "lech": 0}], "", "")
	la("ca dài mà khớp: tiêu đề nói ca mở lâu", td2, "Két NVHTN: ca mở quá 24 giờ mới chốt")
	dung("khớp thì ghi khớp, không đòi lý do", "Đếm được 2.000.000 đ, khớp" in d2 and not any("lý do" in x.lower() for x in d2))
	_, d3 = ttc.soan_ket_lech("Két D1", "2026-11-01 07:00:00", "2026-11-01 22:00:00", 0,
		[{"phuong_thuc": "Tiền mặt", "so_bill": 2, "may": 500000, "phai_co": 500000, "dem": 400000, "lech": -100000}], "", "X")
	dung("thiếu ghi chữ thiếu", "Đếm được 400.000 đ, thiếu 100.000 đ" in d3)
	dung("lệch mà không lý do thì nói rõ", "Người chốt chưa ghi lý do" in d3)
	dung("lệch nhỏ ca ngắn thì không soạn", ttc.soan_ket_lech("K", "2026-11-01 07:00:00", "2026-11-01 22:00:00", 0,
		[{"phuong_thuc": "Tiền mặt", "lech": 1000}], "", "") is None)


@ca("v628 tin 4: bản tin tuần, nợ nhà cung cấp quá hạn toàn bộ và dự báo âm nói rõ lý do")
def _tuan():
	td, dong = ttc.soan_tuan("2026-10-26", "2026-11-01",
		{"vao": 405208222, "ra": 142119596, "rong": 263088626}, {"vao": 772885124, "ra": 575062253},
		{"phai_thu": 140618750, "ncc": (1538476487, 1538476487),
			"cho_chi": {"so": 15, "tien": 108715080, "so_cho_duyet": 0, "tien_cho_duyet": 0},
			"tra_truoc": 49176500,
			"du_bao": {"cuoi_ky": -350988019, "theo_tuan": {"qua_han": 1429761407}, "chua_chot": 6}})
	la("tiêu đề", td, "Tiền tuần 26/10 - 01/11")
	la("các dòng", dong, [
		"Tiền vào 405.208.222 đ, tiền ra 142.119.596 đ, dư ra 263.088.626 đ (tuần trước vào 772.885.124 đ, ra 575.062.253 đ)",
		"Khách còn nợ mình: 140.618.750 đ",
		"Mình còn nợ nhà cung cấp: 1.538.476.487 đ, máy đang coi toàn bộ là quá hạn",
		"Phiếu chi đã duyệt chờ chuyển tiền: 15 phiếu, 108.715.080 đ",
		"Tiền khách gửi trước (của khách, không phải của mình): 49.176.500 đ",
		"Dự báo 30 ngày tới: âm 350.988.019 đ, vì đang tính cả 1.429.761.407 đ nợ nhà cung cấp quá hạn; "
		"còn 6 nguồn chưa chốt số dư đầu",
	])
	_, d2 = ttc.soan_tuan("2026-10-26", "2026-11-01", None, None,
		{"phai_thu": None, "ncc": (100, 20), "cho_chi": None, "tra_truoc": None, "du_bao": None})
	la("phần hỏng ghi chưa đọc được", sum(1 for x in d2 if "chưa đọc được" in x), 5)
	dung("quá hạn một phần ghi số quá hạn", "Mình còn nợ nhà cung cấp: 100 đ, trong đó quá hạn 20 đ" in d2)


KY_10 = {"doanh_thu_thuan": 1965472643.47, "gia_von": 440111335.93, "food_cost": 22.4, "lai_gop": 1525361307.54,
	"ti_le_lai_gop": 77.6, "cp_ban_hang": 520362169.97, "cp_quan_ly": 340444908.92, "cp_san_xuat": 632536730.91,
	"lai_rong": 4748838.74, "ti_le_lai_rong": 0.2}
KY_9 = {"doanh_thu_thuan": 2652567074.13, "food_cost": 17, "lai_rong": 749349233.83, "ti_le_lai_rong": 28.2}


@ca("v628 tin 5: lãi lỗ tháng 10 so với tháng 9, hao hụt bất thường ghi chưa tin được")
def _thang():
	hh = {"dong": [{"kho": "Baker - Nguyên liệu - TV", "kho_ngan": "Baker nguyên liệu", "thieu": 301717252.89,
		"da_dung": 185710171.18, "bat_thuong": 1}], "ti_le_kiem_ke": 87.8, "ti_le_huy": 0.1}
	td, dong = ttc.soan_thang("2026-10", "2026-09", KY_10, KY_9, hh)
	la("tiêu đề", td, "Lãi lỗ tháng 10/2026 (so với tháng 9)")
	la("các dòng", dong, [
		"Doanh thu thuần: 1.965.472.643 đ (tháng 9: 2.652.567.074 đ, giảm 25,9%)",
		"Giá vốn: 440.111.336 đ, food cost 22,4% (tháng 9: 17,0%)",
		"Lãi gộp: 1.525.361.308 đ (77,6%)",
		"Chi phí bán hàng 520.362.170 đ, quản lý 340.444.909 đ, sản xuất 632.536.731 đ",
		"Lãi ròng: 4.748.839 đ (0,2%). Tháng 9: 749.349.234 đ (28,2%)",
		"Hao hụt kiểm kê: chưa tin được. Kho Baker nguyên liệu ghi thiếu 301.717.253 đ trên 185.710.171 đ đã dùng, "
		"vì bếp chưa kiểm kê đều",
	])
	_, d2 = ttc.soan_thang("2026-10", "2026-09", KY_10, KY_9, {"dong": [], "ti_le_kiem_ke": 2.5, "ti_le_huy": 0.4})
	la("đủ dữ liệu thì ra tỉ lệ", d2[-1], "Hao hụt kiểm kê: 2,5% giá trị nguyên liệu đã dùng; bánh huỷ 0,4% doanh thu")
	_, d3 = ttc.soan_thang("2026-01", "2025-12", KY_10, KY_9, None)
	dung("tháng 12 năm trước", d3[0].endswith("(tháng 12: 2.652.567.074 đ, giảm 25,9%)"))
	la("hao hụt đọc hỏng", d3[-1], "Hao hụt kiểm kê: chưa đọc được")


@ca("v628 tin 6: kiểm kê sáng nêu đủ món, không có số tiền, không món thì không soạn")
def _kiem_ke_sang():
	dong = [{"ten": "Chocolate trắng, White Chocolate 30%%, Metro Chef %d" % i, "dvt": "Gram"} for i in range(10)]
	td, d = ttc.soan_kiem_ke_sang("Pastry - Nguyên liệu - TV", dong, 188)
	la("tiêu đề", td, "Kiểm kê sáng nay, bếp Pastry (10 món, khoảng 10 phút)")
	la("mười dòng món", d[:10], ["Chocolate trắng, White Chocolate 30%%, Metro Chef %d (gram)" % i for i in range(10)])
	la("còn quá hạn", d[10], "Kho còn 188 món quá hạn đếm, mỗi sáng máy chia tiếp 10 món")
	dung("chỉ đúng nút trên app", "bấm \"Đếm hôm nay\" của bếp Pastry" in d[11])
	chu = kz.soan_tin("viec", td, d, han=ttc.HAN_DEM_SANG, link="https://app.thevagabondpatisserie.com/kiem-ke")
	la("tin bếp không có tiền", kz.bo_dong_tien(chu)[1], 0)
	la("tên bếp Lab", ttc.ten_bep("Kho Lab - TV"), "Lab")
	dung("không món thì không soạn", ttc.soan_kiem_ke_sang("Kho Lab - TV", [], 0) is None)
	_, d4 = ttc.soan_kiem_ke_sang("Kho Lab - TV", dong[:3], 3)
	dung("hết quá hạn thì không có dòng còn", not any("quá hạn" in x for x in d4))


@ca("v628 kho bếp đếm hằng ngày: chỉ kho nguyên liệu của ba bếp")
def _kho_bep():
	for k in ("Pastry - Nguyên liệu - TV", "Baker - Nguyên liệu - TV", "Kho Lab - TV"):
		dung("nhận %s" % k, kk.la_kho_bep_dem(k))
	for k in ("Pastry - Thành phẩm - TV", "Baker - Thành phẩm - TV", "Kho D1 - TV", "Kho tổng 307 - TV", "", None):
		dung("bỏ %r" % k, not kk.la_kho_bep_dem(k))
	t = kk.the_dem_hom_nay("Kho Lab - TV", None, 117)
	la("chưa có phiếu: 10 món", (t["bep"], t["phieu"], t["so_mon"]), ("Lab", "", 10))
	t2 = kk.the_dem_hom_nay("Pastry - Nguyên liệu - TV", {"name": "PKK-1", "trang_thai": "Đang kiểm", "so_mon": 10, "da_dem": 4}, 0)
	la("đã có phiếu: số đã đếm", (t2["bep"], t2["phieu"], t2["da_dem"], t2["so_mon"]), ("Pastry", "PKK-1", 4, 10))
	la("ít món đến hạn", kk.the_dem_hom_nay("Kho Lab - TV", None, 3)["so_mon"], 3)


@ca("v628 bản vá tích tin: đúng nhóm mốc, giữ mã cũ, chạy lại không đổi")
def _ban_va():
	bgd = pv.tin_them("bgd_bao_cao_ngay")
	la("nhóm Ban giám đốc", bgd, "bgd_bao_cao_ngay, bgd_tien_cuoi_ngay, bgd_ket_lech, bgd_tien_tuan, "
		"bgd_lai_lo_thang, kt_tien_ra_chua_gan, bgd_kiem_quy_lech")
	la("chạy lại không đổi", pv.tin_them(bgd), None)
	kt = pv.tin_them("hd_ket_ghi_so, hd_dau_vao, kt_du_lieu_hao_hut")
	la("nhóm Kế toán", kt, "hd_ket_ghi_so, hd_dau_vao, kt_du_lieu_hao_hut, kt_tien_ra_chua_gan, kt_tien_chua_gan, "
		"bgd_ket_lech, kt_nop_nh_chua_khop")
	la("nhóm Sản xuất", pv.tin_them("bep_lenh_chua_xong, bep_du_lieu_hao_hut"),
		"bep_lenh_chua_xong, bep_du_lieu_hao_hut, bep_kiem_ke_sang")
	la("nhóm Bán hàng không đụng", pv.tin_them("bh_dat_ban, hd_ket_ghi_so"), None)
	la("nhóm trống không đụng", pv.tin_them(""), None)
	dung("mọi mã mới có trong danh mục", all(m in kz.TIN for _, m in pv.THEO_MOC))
	dung("tin két lệch không vào nhóm cửa hàng", not kz.khong_duoc_tien("bgd_ket_lech"))
	dung("tin bếp bị lọc tiền", kz.khong_duoc_tien("bep_kiem_ke_sang"))
	src = (GOI / "patches.txt").read_text(encoding="utf-8")
	dung("bản vá có trong patches.txt", "vagabond.patches.v628_tin_tai_chinh" in src.split("[post_model_sync]")[1])


@ca("v628 lịch: đúng giờ, đúng hàm")
def _lich():
	ns = {}
	exec(compile((GOI / "hooks.py").read_text(encoding="utf-8"), "hooks.py", "exec"), ns)
	cron = ns["scheduler_events"]["cron"]

	def gio(ham):
		return [g for g, ds in cron.items() if ham in ds]
	la("kiểm kê sáng", gio("vagabond.tin_tai_chinh.nhac_kiem_ke_sang"), ["30 7 * * *"])
	la("tiền ra", gio("vagabond.tin_tai_chinh.nhac_tien_ra"), ["0 8 * * *"])
	la("tuần", gio("vagabond.tin_tai_chinh.gui_tuan"), ["0 8 * * 1"])
	la("tháng", gio("vagabond.tin_tai_chinh.gui_thang"), ["0 8 5 * *"])
	la("cuối ngày", gio("vagabond.tin_tai_chinh.gui_cuoi_ngay"), ["35 23 * * *"])


# ------------------------------------------------------------- chạm hệ (hàm thật)

class _Zalo:
	def __init__(self):
		self.goi = []

	def __call__(self, loai, chu_de, tieu_de, dong=None, **kw):
		self.goi.append(dict(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=list(dong or [])))
		return ["X"]


def _utils(**kw):
	u = sys.modules["frappe.utils"]
	cac = [um.patch.object(u, k, v, create=True) for k, v in kw.items()]
	return cac


@ca("v628 tin 2 chạy thật: câu đọc chỉ hỏi tài khoản công ty, khoản tạm ứng không lọt, báo đúng mã tin")
def _tien_ra_that():
	hoi = []

	def sql(q, a=None, **kw):
		hoi.append((q, a))
		return [D(name="B1", bank_account="MB-CTY", withdrawal=8053433, unallocated_amount=8053433, date="2026-10-28",
				description="thuế"),
			D(name="B2", bank_account="MB-CTY", withdrawal=500, unallocated_amount=None, date="2026-10-29", description="phí")]
	z = _Zalo()
	nguon = [{"loai": tc.LOAI_NH, "dong_bo": 1, "tam_ung": 0, "bank_account": "MB-CTY"},
		{"loai": tc.LOAI_NH, "dong_bo": 1, "tam_ung": 1, "bank_account": "MB-TAMUNG"},
		{"loai": tc.LOAI_NH, "dong_bo": 0, "tam_ung": 0, "bank_account": "SHINHAN"},
		{"loai": tc.LOAI_TM, "nguon": "tm:TCV"}]
	vat = [um.patch.object(_fr, "db", NS(sql=sql)), um.patch.object(tc, "_cac_nguon", lambda *a: nguon),
		um.patch.object(kz, "bao_hoac_ghi_loi", z)] + _utils(add_days=lambda d, n: "2026-10-03",
		add_to_date=lambda d, hours=0: "2026-11-01 08:00:00", now_datetime=lambda: "2026-11-02 08:00:00",
		nowdate=lambda: "2026-11-02")
	for v in vat:
		v.start()
	try:
		ttc.nhac_tien_ra()
	finally:
		for v in vat:
			v.stop()
	la("hỏi đúng tài khoản công ty", hoi[0][1][-1], ("MB-CTY",))
	la("mốc 24 giờ", hoi[0][1][1], "2026-11-01 08:00:00")
	la("một tin", len(z.goi), 1)
	g = z.goi[0]
	la("mã tin", g["ma_tin"], "kt_tien_ra_chua_gan")
	la("khoá theo ngày", g["khoa"], "tien-ra-chua-gan:2026-11-02")
	la("dòng tổng: ô trống coi như cả khoản chưa gắn", g["dong"][0], "2 khoản, tổng 8.053.933 đ, ra khỏi tài khoản quá 24 giờ")


@ca("v628 tin 3 chạy thật: chot_ca ghi tin két lệch SAU khi lưu ca và TRƯỚC commit")
def _chot_ca_that():
	vet = []

	class Ca(D):
		def save(self, **kw):
			vet.append("luu")

		def set(self, k, v):
			self[k] = v

		def append(self, k, v):
			self.setdefault(k, []).append(v)

	doc = Ca(name="CA-1", quay="SALES", mo_luc="2026-10-31 06:56:00", tien_le_dau_ca=1000000)
	tin = NS(bao_ket_lech=lambda d, b: vet.append(("tin", d.get("name"), b[0]["lech"], d.get("chot_luc"))))
	import vagabond
	g = dict(frappe=NS(get_doc=lambda *a: doc, db=NS(commit=lambda: vet.append("commit")), session=NS(user="q@x"),
			throw=_fr.throw),
		_kiem_quyen=lambda: None, _ca_dang_mo=lambda q: "CA-1", doc_tien_mat_dem=lambda x: 2744000.0,
		now_datetime=lambda: "2026-11-01 20:19:48", _doanh_thu_he_thong=lambda *a: ({"Tiền mặt": 1420000.0}, {"Tiền mặt": 3}),
		_pt_cua_diem=lambda q: ["Tiền mặt"], loc_trong_ket=lambda p, n: (p, {}), _ngoai_ket=lambda: [],
		ghep_chi_tien_mat=lambda *a: [{"phuong_thuc": "Tiền mặt", "so_bill": 3, "may": 1420000, "phai_co": 2420000,
			"dem": 2744000, "lech": 324000}],
		can_ly_do=lambda b: True, tong_lech=lambda b: 324000, flt=lambda x: float(x or 0), TT_DA_CHOT="Đã chốt",
		CA="Vagabond Ca Quay", NGUONG_LECH=1000.0)
	with um.patch.object(vagabond, "tin_tai_chinh", tin, create=True), \
			um.patch.dict(sys.modules, {"vagabond.tin_tai_chinh": tin}):
		kq = nap("ca_quay.py", "chot_ca", g)("SALES", "2744000", ly_do_lech=".")
	la("đã chốt", kq.get("da_chot"), 1)
	la("thứ tự", vet, ["luu", ("tin", "CA-1", 324000, "2026-11-01 20:19:48"), "commit"])
	vet.clear()
	doc2 = Ca(name="CA-2", quay="SALES", mo_luc="2026-11-01 06:56:00", tien_le_dau_ca=1000000)
	g["frappe"].get_doc = lambda *a: doc2
	with um.patch.object(vagabond, "tin_tai_chinh", tin, create=True), \
			um.patch.dict(sys.modules, {"vagabond.tin_tai_chinh": tin}):
		kq2 = nap("ca_quay.py", "chot_ca", g)("SALES", "2744000")
	la("lệch chưa có lý do: chưa chốt, không tin", (kq2.get("can_ly_do"), vet), (1, []))


@ca("v628 tin 3 chạy thật: bao_ket_lech đọc tên két, tên người chốt, khoá theo mã ca")
def _bao_ket_that():
	z = _Zalo()
	doc = D(name="CA-2026-05855", quay="SALES", mo_luc="2026-10-31 06:56:11", chot_luc="2026-11-01 20:19:48",
		tien_le_dau_ca=1000000, ly_do_lech=".", nguoi_chot="q@x")
	bang = [{"phuong_thuc": "Tiền mặt", "so_bill": 3, "may": 1420000, "phai_co": 2420000, "dem": 2744000, "lech": 324000}]
	vat = [um.patch.object(_fr, "db", NS(get_value=lambda dt, n, f: "Lê Nguyễn Minh Quân" if dt == "User" else None)),
		um.patch.object(tc, "_cac_nguon", lambda *a: [{"nguon": "tm:SALES", "ten": "Két Sales Online"}]),
		um.patch.object(kz, "bao_hoac_ghi_loi", z)]
	for v in vat:
		v.start()
	try:
		ttc.bao_ket_lech(doc, bang)
	finally:
		for v in vat:
			v.stop()
	la("một tin", len(z.goi), 1)
	g = z.goi[0]
	la("mã, loại, khoá, nguồn", (g["ma_tin"], g["loai"], g["khoa"], g["nguon"]),
		("bgd_ket_lech", "canh_bao", "ket-lech:CA-2026-05855", "CA-2026-05855"))
	la("tiêu đề có tên két", g["tieu_de"], "Két Sales Online lệch tiền mặt khi chốt ca")
	dung("người chốt có tên thật", "Người chốt: Lê Nguyễn Minh Quân" in g["dong"])


@ca("Codex #527: lỗi chết giao dịch khi ghi tin két lệch phải đi lên, lỗi thường chỉ ghi log")
def _ket_lech_chet_gd():
	doc = D(name="CA-1", quay="SALES", mo_luc="2026-10-31 06:56:11", chot_luc="2026-11-01 20:19:48",
		tien_le_dau_ca=1000000, ly_do_lech=".", nguoi_chot="")
	bang = [{"phuong_thuc": "Tiền mặt", "so_bill": 3, "may": 1420000, "phai_co": 2420000, "dem": 2744000, "lech": 324000}]

	class LoiCsdl(Exception):
		pass
	for loi, phai_nem in ((LoiCsdl(1213, "Deadlock found"), True), (RuntimeError("Zalo hỏng"), False)):
		ghi = []

		def nem(*a, **k):
			raise loi
		vat = [um.patch.object(tc, "_cac_nguon", lambda *a: [{"nguon": "tm:SALES", "ten": "Két Sales Online"}]),
			um.patch.object(kz, "bao_hoac_ghi_loi", nem), um.patch.object(ttc, "_ghi_loi", lambda p: ghi.append(p))]
		for v in vat:
			v.start()
		try:
			try:
				ttc.bao_ket_lech(doc, bang)
				nem_ra = False
			except Exception as e:
				nem_ra = e is loi
		finally:
			for v in vat:
				v.stop()
		la("ném tiếp: %s" % type(loi).__name__, (nem_ra, ghi), (phai_nem, [] if phai_nem else ["két lệch"]))


@ca("Codex #527: phiếu Đếm hôm nay không khoá nhập xuất, phiếu kiểm kê thường vẫn khoá")
def _dem_hang_ngay_khong_khoa():
	phieu = [
		{"name": "PKK-1", "kho": "Pastry - Nguyên liệu - TV", "trang_thai": "Đang kiểm", "ngay_kiem": "2026-11-02",
			"ghi_chu": kk.GHI_CHU_LICH % "2026-11-02"},
		{"name": "PKK-2", "kho": "Baker - Nguyên liệu - TV", "trang_thai": "Chờ duyệt", "ngay_kiem": "2026-11-02",
			"ghi_chu": "Kiểm kê cuối tháng"},
	]
	dong = [{"parent": "PKK-1", "item_code": "NVL-BO"}, {"parent": "PKK-2", "item_code": "NVL-BOT"}]

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Phieu Kiem Ke":
			return [dict(x) for x in phieu]
		ten = (filters or {}).get("parent", ["in", []])[1]
		return [d for d in dong if d["parent"] in ten]
	vat = [um.patch.object(_fr, "get_all", get_all), um.patch.object(kk, "nowdate", lambda: "2026-11-02"),
		um.patch.object(_fr, "db", NS(get_value=lambda *a, **k: "Bơ lạt"))]
	for v in vat:
		v.start()
	try:
		khoa = kk._phieu_dang_khoa()
		se_dem = NS(get=lambda k, d=None: {"items": [{"item_code": "NVL-BO", "s_warehouse": "Pastry - Nguyên liệu - TV"}]}.get(k, d))
		kk.chan_khi_dang_kiem(se_dem)
		qua = True
		se_thuong = NS(get=lambda k, d=None: {"items": [{"item_code": "NVL-BOT", "s_warehouse": "Baker - Nguyên liệu - TV"}]}.get(k, d))
		nem("phiếu thường vẫn chặn", lambda: kk.chan_khi_dang_kiem(se_thuong))
	finally:
		for v in vat:
			v.stop()
	la("chỉ phiếu thường khoá", [x["phieu"] for x in khoa], ["PKK-2"])
	dung("lệnh dùng món đang đếm hằng ngày đi qua", qua)
	la("nhận ra phiếu hằng ngày", (kk.la_phieu_dem_hang_ngay(kk.GHI_CHU_LICH % "2026-11-02"),
		kk.la_phieu_dem_hang_ngay("Kiểm kê cuối tháng"), kk.la_phieu_dem_hang_ngay(None)), (True, False, False))


@ca("v628 tin 6 chạy thật: mỗi kho bếp một tin, kho không món thì bỏ, một kho hỏng không chặn kho khác")
def _kiem_ke_sang_that():
	z = _Zalo()

	def lich(kho, n):
		la("chia 10 món", n, 10)
		if kho == "Baker - Nguyên liệu - TV":
			raise RuntimeError("hỏng")
		if kho == "Kho Lab - TV":
			return {"dong": [], "tong_den_han": 0}
		return {"dong": [{"ten": "Bơ lạt", "dvt": "Gram"}], "tong_den_han": 1}
	loi = []
	vat = [um.patch.object(kk, "kho_bep", lambda: ["Baker - Nguyên liệu - TV", "Kho Lab - TV", "Pastry - Nguyên liệu - TV"]),
		um.patch.object(kk, "lich_kho", lich), um.patch.object(kz, "bao_hoac_ghi_loi", z),
		um.patch.object(ttc, "_ghi_loi", lambda p: loi.append(p))] + _utils(nowdate=lambda: "2026-11-02")
	for v in vat:
		v.start()
	try:
		ttc.nhac_kiem_ke_sang()
	finally:
		for v in vat:
			v.stop()
	la("chỉ Pastry có tin", [g["tieu_de"] for g in z.goi], ["Kiểm kê sáng nay, bếp Pastry (1 món, khoảng 1 phút)"])
	la("mã, khoá, hạn", (z.goi[0]["ma_tin"], z.goi[0]["khoa"], z.goi[0]["han"]),
		("bep_kiem_ke_sang", "kiem-ke-sang:Pastry - Nguyên liệu - TV:2026-11-02", "11:00 hôm nay"))
	la("Baker hỏng có ghi lỗi", loi, ["kiểm kê sáng Baker - Nguyên liệu - TV"])


@ca("v628 tin 4 chạy thật: một phần đọc hỏng thì tin vẫn đi, phần đó ghi chưa đọc được")
def _tuan_that():
	z = _Zalo()

	def hong():
		raise RuntimeError("x")
	vat = [um.patch.object(tc, "dong_tien_khoang", lambda tu, den: {"vao": 1, "ra": 0, "rong": 1}),
		um.patch.object(tc, "_phai_thu", hong), um.patch.object(tc, "_ncc", lambda: ([], 10, 0)),
		um.patch.object(tc, "_cho_chi", lambda: {"so": 0, "tien": 0}), um.patch.object(tc, "_tra_truoc", lambda: (5, 1)),
		um.patch.object(tc, "du_bao_30_tinh", lambda: {"cuoi_ky": 9, "theo_tuan": {}}),
		um.patch.object(kz, "bao_hoac_ghi_loi", z), um.patch.object(ttc, "_ghi_loi", lambda p: None)] + _utils(
		nowdate=lambda: "2026-11-02", getdate=lambda d: __import__("datetime").date(2026, 11, 2),
		add_days=lambda d, n: d + __import__("datetime").timedelta(days=n))
	for v in vat:
		v.start()
	try:
		ttc.gui_tuan()
	finally:
		for v in vat:
			v.stop()
	la("một tin", len(z.goi), 1)
	g = z.goi[0]
	la("tuần trước", g["tieu_de"], "Tiền tuần 26/10 - 01/11")
	dung("phần hỏng ghi rõ", "Khách còn nợ mình: chưa đọc được" in g["dong"])
	la("mã tin", g["ma_tin"], "bgd_tien_tuan")


@ca("v628 nút Đếm hôm nay: đã có phiếu trong ngày thì mở lại, kho ngoài bếp bị từ chối, khoá dòng kho trước khi đọc")
def _mo_phieu_that():
	vet = []

	def sql(q, a=None, **kw):
		vet.append(q.split()[0] + (" for update" if "for update" in q else ""))
		return []
	co = {"p": {"name": "PKK-9", "so_mon": 10}}
	g = dict(frappe=NS(db=NS(sql=sql), throw=_fr.throw), _duoc_dem=lambda: None, la_kho_bep_dem=kk.la_kho_bep_dem,
		kho_bep=lambda: ["Pastry - Nguyên liệu - TV"], nowdate=lambda: "2026-11-02", cint=lambda x: int(x or 0),
		_phieu_hom_nay=lambda k, n: co["p"], tao_phieu_hom_nay=lambda k, n: {"ok": 1, "name": "MOI", "so_mon": n},
		MOI_NGAY_BEP=10)
	mo = nap("kiem_ke.py", "mo_phieu_hom_nay", g)
	la("mở lại phiếu có sẵn", mo("Pastry - Nguyên liệu - TV")["name"], "PKK-9")
	la("khoá trước khi đọc", vet, ["select for update"])
	co["p"] = None
	la("chưa có thì tạo 10 món", mo("Pastry - Nguyên liệu - TV"), {"ok": 1, "name": "MOI", "so_mon": 10})
	nem("kho thành phẩm bị từ chối", lambda: mo("Pastry - Thành phẩm - TV"))
	nem("kho cửa hàng bị từ chối", lambda: mo("Kho D1 - TV"))


@ca("v628 Dòng tiền và Dự báo vẫn kiểm quyền; bản không kiểm quyền không mở ra ngoài")
def _quyen():
	from vagabond.khung.kiem_thu.thu_cua_ngo import CUA_NGO
	mo = CUA_NGO.get("tai_chinh.py") or []
	dung("dong_tien_khoang không mở", "dong_tien_khoang" not in mo)
	dung("du_bao_30_tinh không mở", "du_bao_30_tinh" not in mo)
	goi = []
	with um.patch.object(tc, "_kiem", lambda: goi.append("kiem")), \
			um.patch.object(tc, "dong_tien_khoang", lambda tu, den: {"tu": str(tu)}), \
			um.patch.object(tc, "du_bao_30_tinh", lambda: {"x": 1}):
		tc.dong_tien(7)
		tc.du_bao_30()
	la("hai màn đều kiểm quyền", goi, ["kiem", "kiem"])


@ca("v628 màn Kiểm kê chạy thật trong node: thẻ Đếm hôm nay")
def _hanh_vi():
	import subprocess
	js = GOI / "khung" / "kiem_thu" / "hanh_vi" / "kiem_ke_hom_nay_628.js"
	r = subprocess.run(["node", str(js)], capture_output=True, text=True, timeout=60, cwd=str(GOI.parent))
	la(r.stdout + r.stderr, r.returncode, 0)
	dung("đủ 7 ca", "PASS 7 ca" in r.stdout)
