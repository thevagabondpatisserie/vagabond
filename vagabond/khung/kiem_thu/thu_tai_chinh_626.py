# -*- coding: utf-8 -*-
"""v626: phân hệ Tài chính.

Anh Việt 31/10/2026: tổng tiền mặt, tổng tiền ngân hàng (qua SePay, số dư đầu
anh đưa tại thời điểm chốt, app tự tính), tỉ lệ hao hụt, cùng các nút khảo sát
từ phần mềm hàng đầu. Chỉ Giám đốc và kế toán trưởng thấy; tiền mặt tách từng
két và quỹ công ty; tài khoản tạm ứng tính vào tổng nhưng tách dòng.

Số liệu mẫu lấy đúng hình dạng đọc trên site 31/10/2026: account_map SePay bốn
tài khoản (MB công ty, OCB, ACB, MB tạm ứng), Shinhan công ty không đồng bộ
giao dịch nhưng SePay báo số dư 242.995.597, MB SePay báo 0; sổ cái tháng 10;
kho Baker kiểm kê thiếu 301.717.253 trên 185.710.171 nguyên liệu dùng.

Mọi ca chạy THẬT các phép của tai_chinh, không dò chuỗi mã nguồn, trừ ca chốt
hai bản danh sách vai JS và máy chủ.
"""

import datetime as dt
import os
import re
import sys
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr, "PermissionError"):
	class _PE(Exception):
		pass
	_fr.PermissionError = _PE

from vagabond import tai_chinh as tc  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOM = dt.date(2026, 8, 15)

BAN_DO = {
	"31561568": "MB-CTY-31561568 - MB Bank",
	"0901486556": "OCB-QUY-TAMUNG-6556 - OCB - Ngân hàng TMCP Phương Đông",
	"616066": "ACB-QUY-TAMUNG-616066 - ACB - Ngân hàng TMCP Á Châu",
	"612160615": "MB-QUY-TAMUNG-612160615 - MB - Ngân hàng TMCP Quân đội",
}
TK = [
	{"name": "MB-CTY-31561568 - MB Bank", "account": "11211 - Tiền gửi MB Bank 31561568 - TV", "bank": "MB Bank",
		"bank_account_no": "31561568", "is_company_account": 1},
	{"name": "OCB-QUY-TAMUNG-6556 - OCB - Ngân hàng TMCP Phương Đông", "account": "1411 - Tạm ứng - Nguyễn Hoàng Việt (OCB) - TV",
		"bank": "OCB - Ngân hàng TMCP Phương Đông", "bank_account_no": "0901486556", "is_company_account": 1},
	{"name": "ACB-QUY-TAMUNG-616066 - ACB - Ngân hàng TMCP Á Châu", "account": "1412 - Tạm ứng - Nguyễn Hoàng Việt (ACB) - TV",
		"bank": "ACB - Ngân hàng TMCP Á Châu", "bank_account_no": "616066", "is_company_account": 1},
	{"name": "MB-QUY-TAMUNG-612160615 - MB - Ngân hàng TMCP Quân đội", "account": "1413 - Tạm ứng - Nguyễn Hoàng Việt (MB) - TV",
		"bank": "MB - Ngân hàng TMCP Quân đội", "bank_account_no": "612160615", "is_company_account": 0},
	{"name": "SHINHAN-700037279585 - Shinhan Bank", "account": "11212 - Tiền gửi Shinhan 700037279585 - TV", "bank": "Shinhan Bank",
		"bank_account_no": "700037279585", "is_company_account": 1},
]
SO_BAO = {"700037279585": 242995597.0, "612160615": 0.0, "616066": 0.0, "31561568": 0.0, "0901486556": 0.0}
DIEM = [{"ma": "SALES", "ten": "Sales Online", "ten_ngan": "Sales Online", "quay": ""},
	{"ma": "TCV", "ten": "The Vagabond District 1", "ten_ngan": "District 1", "quay": "TCV"},
	{"ma": "NVHTN", "ten": "NVHTN", "ten_ngan": "NVHTN", "quay": "NVHTN"}]


def _nguon():
	return tc.nguon_ngan_hang(BAN_DO, TK, SO_BAO) + tc.nguon_tien_mat(DIEM)


@ca("v626 người được xem: ô cấu hình chịu mọi cách gõ, chỉ nhận email và Administrator")
def _nguoi_xem():
	la("tách dòng, phẩy, chấm phẩy, khoảng trắng; hạ chữ; bỏ trùng",
		tc.doc_nguoi_xem("Dung@Vagabond.vn,  son@vagabond.vn;\nDUNG@vagabond.vn  <khai@vagabond.vn>"),
		["dung@vagabond.vn", "son@vagabond.vn", "khai@vagabond.vn"])
	la("bỏ chữ không phải email", tc.doc_nguoi_xem("Dung kế toán trưởng"), [])
	la("Administrator giữ nguyên", tc.doc_nguoi_xem("administrator"), ["Administrator"])
	la("rỗng", tc.doc_nguoi_xem(None), [])


@ca("v626 quyền xem: Giám đốc, quản trị và người được chọn; kế toán viên, AP Giám đốc (quản lý cửa hàng) không")
def _quyen():
	xem = ["dung@vagabond.vn"]
	dung("Giám đốc", tc.duoc_xem("viet@x", ["Giám đốc"], []))
	dung("quản trị", tc.duoc_xem("a@x", ["System Manager"], []))
	dung("kế toán trưởng được chọn, khác chữ hoa", tc.duoc_xem("Dung@Vagabond.vn", ["Accounts Manager"], xem))
	la("kế toán viên có Accounts Manager mà không được chọn", tc.duoc_xem("khai@vagabond.vn", ["Accounts Manager", "Accounts User",
		"AP Kiểm soát (FIN)"], xem), False)
	la("quản lý cửa hàng có AP Giám đốc", tc.duoc_xem("de@vagabond.vn", ["AP Giám đốc", "VGB - Quản lý cửa hàng"], xem), False)
	la("khách chưa đăng nhập", tc.duoc_xem("Guest", [], ["guest"]), False)


@ca("v626 số tiền và ngày gõ tay: dấu chấm, phẩy, chữ đ, số âm, ngày hai dạng")
def _so_ngay():
	la("chấm", tc.doc_so_tien("1.628.400.000"), 1628400000.0)
	la("phẩy", tc.doc_so_tien("1,628,400,000"), 1628400000.0)
	la("chữ đ và khoảng trắng", tc.doc_so_tien(" 52 100 000 đ "), 52100000.0)
	la("âm", tc.doc_so_tien("-5.000"), -5000.0)
	la("rỗng", tc.doc_so_tien(""), None)
	la("chữ", tc.doc_so_tien("năm triệu"), None)
	la("ISO", tc.doc_ngay("2026-10-31"), dt.date(2026, 10, 31))
	la("ngày Việt", tc.doc_ngay("31/10/2026"), dt.date(2026, 10, 31))
	la("hỏng", tc.doc_ngay("31-13-2026"), None)


@ca("v626 kiểm mốc chốt: nguồn lạ, ngày tương lai, ngày quá xa, số không đọc được")
def _kiem_moc():
	ds = {"nh:31561568": 1}
	la("đạt", tc.kiem_moc("nh:31561568", dt.date(2026, 8, 14), 5.0, ds, HOM), "")
	dung("nguồn lạ", "Chọn lại" in tc.kiem_moc("nh:999", dt.date(2026, 8, 14), 5.0, ds, HOM))
	dung("chưa chọn ngày", "ngày chốt" in tc.kiem_moc("nh:31561568", None, 5.0, ds, HOM))
	dung("ngày sau hôm nay", "sau hôm nay" in tc.kiem_moc("nh:31561568", dt.date(2026, 8, 16), 5.0, ds, HOM))
	dung("quá xa", "quá xa" in tc.kiem_moc("nh:31561568", dt.date(2024, 12, 31), 5.0, ds, HOM))
	dung("số hỏng", "bằng số" in tc.kiem_moc("nh:31561568", dt.date(2026, 8, 14), None, ds, HOM))
	dung("thừa chữ số", "quá lớn" in tc.kiem_moc("nh:31561568", dt.date(2026, 8, 14), 1e14, ds, HOM))


@ca("v626 mốc mới nhất: chốt lại là thêm mốc, ngày sau thắng, cùng ngày lưu sau thắng")
def _moc():
	moc = [
		{"name": "MSD-1", "nguon": "tm:TCV", "ngay_chot": "2026-08-01", "so_du": 5000000, "luc": "2026-08-01 22:00"},
		{"name": "MSD-3", "nguon": "tm:TCV", "ngay_chot": "2026-08-10", "so_du": 7000000, "luc": "2026-08-10 22:00"},
		{"name": "MSD-4", "nguon": "tm:TCV", "ngay_chot": "2026-08-10", "so_du": 6500000, "luc": "2026-08-10 23:10"},
		{"name": "MSD-2", "nguon": "nh:31561568", "ngay_chot": "2026-08-05", "so_du": 1e9, "luc": "2026-08-05 08:00"},
	]
	m = tc.moc_moi_nhat(moc)
	la("két lấy lần đếm lại cuối ngày 10", m["tm:TCV"]["name"], "MSD-4")
	la("ngân hàng", m["nh:31561568"]["name"], "MSD-2")
	la("chưa chốt thì không có", tc.so_du_tu_moc(None, 5, 1), None)
	la("số dư = mốc + vào - ra", tc.so_du_tu_moc(m["tm:TCV"], 2000000, 500000), 8000000.0)


@ca("v626 đối chiếu SePay: khớp dưới 1.000 đ, lệch, SePay không báo (MB luôn 0) thì không kết luận")
def _doi_chieu():
	la("khớp", tc.doi_chieu(242995000, 242995597)["tt"], "khop")
	l = tc.doi_chieu(243195597, 242995597)
	la("lệch", l["tt"], "lech")
	la("số lệch", l["lech"], 200000.0)
	la("MB báo 0", tc.doi_chieu(1e9, 0)["tt"], "khong_bao")
	la("chưa chốt", tc.doi_chieu(None, 5)["tt"], "chua_chot")


@ca("v626 nguồn ngân hàng: bốn tài khoản SePay đồng bộ, Shinhan công ty lấy số SePay báo, tạm ứng tách dòng, chỉ hiện bốn số cuối")
def _nguon_nh():
	nh = tc.nguon_ngan_hang(BAN_DO, TK, SO_BAO)
	theo = {x["nguon"]: x for x in nh}
	la("đủ năm tài khoản, không trùng", sorted(theo), sorted(["nh:31561568", "nh:0901486556", "nh:616066", "nh:612160615", "nh:700037279585"]))
	la("Shinhan không đồng bộ", theo["nh:700037279585"]["dong_bo"], 0)
	la("Shinhan SePay báo", theo["nh:700037279585"]["so_bao"], 242995597.0)
	la("MB công ty đồng bộ", theo["nh:31561568"]["dong_bo"], 1)
	la("MB công ty không phải tạm ứng", theo["nh:31561568"]["tam_ung"], 0)
	for k in ("nh:0901486556", "nh:616066", "nh:612160615"):
		la("tạm ứng %s" % k, theo[k]["tam_ung"], 1)
		dung("nhãn ghi tạm ứng %s" % k, "(tạm ứng)" in theo[k]["ten"])
	la("nhãn MB công ty", theo["nh:31561568"]["ten"], "MB Bank ···1568")
	la("nhãn OCB ngắn", theo["nh:0901486556"]["ten"], "OCB ···6556 (tạm ứng)")
	for x in nh:
		dung("không lộ số tài khoản đầy đủ: %s" % x["ten"], x["nguon"][3:] not in x["ten"] or len(x["nguon"][3:]) <= 4)
	la("công ty xếp trước tạm ứng", [x["tam_ung"] for x in nh], [0, 0, 1, 1, 1])


@ca("v626 nguồn tiền mặt: két từng điểm bán đang bật rồi quỹ công ty")
def _nguon_tm():
	tm = tc.nguon_tien_mat(DIEM)
	la("thứ tự", [x["nguon"] for x in tm], ["tm:SALES", "tm:TCV", "tm:NVHTN", "tm:QUY"])
	la("tên két", tm[1]["ten"], "Két District 1")
	la("quỹ", tm[-1]["ten"], "Quỹ tiền mặt công ty")


@ca("v626 tổng tiền: nguồn chưa chốt không cộng nhưng được đếm, tạm ứng cộng vào ngân hàng và báo riêng")
def _tong():
	t = tc.tong_tien([
		{"loai": "Ngân hàng", "so_du": 1000000000, "tam_ung": 0},
		{"loai": "Ngân hàng", "so_du": 52100000, "tam_ung": 1},
		{"loai": "Ngân hàng", "so_du": None, "tam_ung": 1},
		{"loai": "Tiền mặt", "so_du": 8450000},
		{"loai": "Tiền mặt", "so_du": None},
	])
	la("tổng", t["tong"], 1060550000.0)
	la("ngân hàng", t["ngan_hang"], 1052100000.0)
	la("tạm ứng", t["tam_ung"], 52100000.0)
	la("tiền mặt", t["tien_mat"], 8450000.0)
	la("chưa chốt", t["chua_chot"], 2)


@ca("v626 dòng tiền: chuyển nội bộ MB công ty sang OCB tạm ứng không tính vào hay ra")
def _noi_bo():
	gd = [
		{"ten": "A", "tk": "MB", "ngay": "2026-08-10", "vao": 0, "ra": 10000000, "tham_chieu": "FT26222001"},
		{"ten": "B", "tk": "OCB", "ngay": "2026-08-10", "vao": 10000000, "ra": 0, "tham_chieu": "FT26222001"},
		{"ten": "C", "tk": "MB", "ngay": "2026-08-10", "vao": 10000000, "ra": 0},
		{"ten": "D", "tk": "MB", "ngay": "2026-08-11", "vao": 0, "ra": 3000000},
		{"ten": "E", "tk": "ACB", "ngay": "2026-08-12", "vao": 3000000, "ra": 0},
		{"ten": "F", "tk": "MB", "ngay": "2026-08-12", "vao": 0, "ra": 499000},
		{"ten": "G", "tk": "OCB", "ngay": "2026-08-12", "vao": 500000, "ra": 0},
	]
	ngoai, nb = tc.tach_noi_bo(gd)
	la("một cặp nội bộ", len(nb), 1)
	la("cặp đúng hai tài khoản", (nb[0]["tu"], nb[0]["den"]), ("MB", "OCB"))
	la("còn lại", sorted(g["ten"] for g in ngoai), ["C", "D", "E", "F", "G"])
	kq = tc.gom_ngay(ngoai, {"2026-08-10": 2500000}, {"2026-08-11": 1000000}, dt.date(2026, 8, 9), dt.date(2026, 8, 12))
	la("đủ bốn ngày kể cả ngày trống", [x["ngay"] for x in kq["ngay"]], ["2026-08-09", "2026-08-10", "2026-08-11", "2026-08-12"])
	la("ngày 10 vào", kq["ngay"][1]["vao"], 12500000.0)
	la("ngày 11 ra", kq["ngay"][2]["ra"], 4000000.0)
	la("tổng vào", kq["vao"], 16000000.0)
	la("tổng ra", kq["ra"], 4499000.0)
	la("còn lại", kq["rong"], 11501000.0)
	# Khoản vào CÙNG tài khoản đứng trước (khách hoàn tiền đúng số đó vào MB):
	# không được ghép với khoản ra của chính MB, phải ghép sang OCB.
	gd2 = [
		{"ten": "A2", "tk": "MB", "ngay": "2026-08-13", "vao": 0, "ra": 7000000, "mo_ta": "VAGABOND NAP QUY TAM UNG T8"},
		{"ten": "C2", "tk": "MB", "ngay": "2026-08-13", "vao": 7000000, "ra": 0, "mo_ta": "VAGABOND NAP QUY TAM UNG T8"},
		{"ten": "B2", "tk": "OCB", "ngay": "2026-08-13", "vao": 7000000, "ra": 0, "mo_ta": "VAGABOND NAP QUY TAM UNG T8"},
	]
	ngoai2, nb2 = tc.tach_noi_bo(gd2)
	la("ghép sang tài khoản khác", (nb2[0]["tu"], nb2[0]["den"]) if nb2 else None, ("MB", "OCB"))
	la("giữ khoản vào cùng tài khoản", [g["ten"] for g in ngoai2], ["C2"])
	ln = tc.lon_nhat(ngoai, 2)
	la("vào lớn nhất", [x["so"] for x in ln["vao"]], [10000000.0, 3000000.0])


@ca("v626 Codex #524: cùng ngày cùng số tiền mà không chung lệnh thì KHÔNG phải chuyển nội bộ (dữ liệu site 29/10, 27/10, 05/08)")
def _noi_bo_bang_chung():
	# Hình dạng đọc trên site 31/10/2026: từ 01/08 có 99 cặp vào ra cùng ngày
	# cùng số tiền giữa hai tài khoản của mình, chỉ khoảng một phần tư là chuyển
	# thật. Ghép theo số tiền thì khách chuyển 665.000 vào MB công ty và quỹ tạm
	# ứng trả NCC 665.000 cùng ngày bị coi là chuyển nội bộ, mất cả hai.
	gd = [
		{"ten": "KH", "tk": "MB-CTY", "ngay": "2026-10-29", "vao": 665000, "ra": 0,
			"mo_ta": "Qanehu5840  PANCAKE2278 4 S67355O96630T2909380955 96630 0902162418- Ma GD ACSP/ vv639846",
			"tham_chieu": "FT26302717455878"},
		{"ten": "NCC", "tk": "MB-TU", "ngay": "2026-10-29", "vao": 0, "ra": 665000,
			"mo_ta": "VGB TT DH NA244698 NAM AN", "tham_chieu": "FT26302255898648"},
		# Hoàn ứng MB công ty sang MB tạm ứng: hai vế chung mã FT.
		{"ten": "HU-RA", "tk": "MB-CTY", "ngay": "2026-10-27", "vao": 0, "ra": 490000,
			"mo_ta": "VAGABOND APP.26.10.118 HOAN UNG", "tham_chieu": "FT26301316599360"},
		{"ten": "HU-VAO", "tk": "MB-TU", "ngay": "2026-10-27", "vao": 490000, "ra": 0,
			"mo_ta": "VAGABOND APP.26.10.118 HOAN UNG", "tham_chieu": "FT26301316599360"},
		# Khác ngân hàng MB sang OCB: mã FT khác nhau, ngân hàng nhận thêm tiền tố
		# MBCT, hậu tố mã giao dịch và gộp một dấu cách.
		{"ten": "OCB-VAO", "tk": "OCB", "ngay": "2026-08-05", "vao": 12272961, "ra": 0,
			"mo_ta": "VAGABOND HOAN UNG NGUYEN HOANG VIET HD 805 238237 42013 339 3715 239599 893 35683 35237 189 79865404",
			"tham_chieu": "FT26217Z3MJ4"},
		{"ten": "MB-RA", "tk": "MB-CTY", "ngay": "2026-08-05", "vao": 0, "ra": 12272961,
			"mo_ta": "MBCT VAGABOND HOAN UNG NGUYEN HOANG VIET HD 805 238237 42013 339 3715239599 893 35683 35237 189 79865404 D2X6NRU4/539808",
			"tham_chieu": "FT26217690780621"},
		# MB công ty sang MB tạm ứng khác mã FT, bên nhận cắt bớt đuôi (07/09).
		{"ten": "CAT-RA", "tk": "MB-CTY", "ngay": "2026-09-07", "vao": 0, "ra": 7000599,
			"mo_ta": "VAGABOND APP2609015 HOAN UNG HD1224 HD1661 HD3513 HD170828 HD82396 HD82422 HD82621 HD82 GD 6250MSCBD2IFTL26 070926-18:34:47"},
		{"ten": "CAT-VAO", "tk": "MB-TU", "ngay": "2026-09-07", "vao": 7000599, "ra": 0,
			"mo_ta": "MBCT VAGABOND APP 26 09 015 HOAN UNG HD1224 HD1661 HD3513 HD170828 HD82396 HD82422 HD82621 HD82 D2IFTL26/120902"},
		# Một người chuyển vào và quỹ tạm ứng trả đúng người đó đúng số (01/10):
		# chung mỗi cái tên 13 ký tự, không phải chuyển nội bộ.
		{"ten": "TEN-VAO", "tk": "MB-CTY", "ngay": "2026-10-01", "vao": 1200000, "ra": 0,
			"mo_ta": "BUI NGOC YEN NHI chuyen tien"},
		{"ten": "TEN-RA", "tk": "MB-TU", "ngay": "2026-10-01", "vao": 0, "ra": 1200000,
			"mo_ta": "VAGABOND APP.26.10.013 THANH TOAN BUI NGOC YEN NHI"},
		# Nội dung quá ngắn không đủ làm bằng chứng.
		{"ten": "N-RA", "tk": "MB-CTY", "ngay": "2026-08-06", "vao": 0, "ra": 100000, "mo_ta": "CK", "tham_chieu": ""},
		{"ten": "N-VAO", "tk": "OCB", "ngay": "2026-08-06", "vao": 100000, "ra": 0, "mo_ta": "CK", "tham_chieu": None},
	]
	ngoai, nb = tc.tach_noi_bo(gd)
	la("chỉ ba cặp có bằng chứng", sorted((x["tu"], x["den"], x["so"]) for x in nb),
		[("MB-CTY", "MB-TU", 490000.0), ("MB-CTY", "MB-TU", 7000599.0), ("MB-CTY", "OCB", 12272961.0)])
	la("khách và NCC cùng số tiền vẫn là tiền vào, tiền ra", sorted(g["ten"] for g in ngoai),
		["KH", "N-RA", "N-VAO", "NCC", "TEN-RA", "TEN-VAO"])
	kq = tc.gom_ngay(ngoai, {}, {}, dt.date(2026, 10, 29), dt.date(2026, 10, 29))
	la("ngày 29/10 đủ tiền vào và ra", (kq["vao"], kq["ra"]), (665000.0, 665000.0))
	la("mã tham chiếu lệch hoa thường, dấu cách vẫn là một lệnh",
		tc.cung_lenh({"tham_chieu": " ft2630 1316599360 "}, {"tham_chieu": "FT26301316599360"}), True)
	la("hai vế không mã, không nội dung", tc.cung_lenh({}, {}), False)


@ca("v626 Codex #524: quỹ công ty và chi quỹ theo ngày đọc CÙNG một điều kiện, bỏ hoá đơn bán và phiếu thu tại quầy")
def _dk_quy():
	cau = []

	def sql(q, *a, **k):
		cau.append(q)
		return [(0, 0)]
	with um.patch.object(tc.frappe.db, "sql", sql, create=True):
		tc._so_cai_quy(HOM)
		tc._chi_quy_theo_ngay(HOM, HOM)
	la("hai câu đọc sổ cái quỹ", len(cau), 2)
	la("cả hai dùng chung điều kiện quỹ công ty", [tc.DK_QUY_CONG_TY in q for q in cau], [True, True])
	dk = re.sub(r"\s+", " ", tc.DK_QUY_CONG_TY)
	dung("bỏ hoá đơn bán", "not in ('Sales Invoice','POS Invoice')" in dk)
	dung("bỏ phiếu thu mang ô quầy", "g.voucher_type='Payment Entry' and exists" in dk and "coalesce(pe.vgb_quay,'')!=''" in dk)


@ca("v626 Codex #524: Khách nợ mình gồm cả hoá đơn đã nằm trong phiếu đòi nợ chờ thu")
def _tong_con_doi():
	from vagabond.thu_tien import tong_con_doi
	rows = [{"name": "HD1", "con_doi": 5000000}, {"name": "HD3", "con_doi": None}, {"name": "HD2", "con_doi": 1250000.5}]
	la("cộng mọi tờ, kể cả tờ đã gom", tong_con_doi(rows), 6250000.5)
	la("rỗng", tong_con_doi(None), 0)
	with um.patch.dict(sys.modules, {"vagabond.cong_no": type(sys)("vagabond.cong_no")}):
		sys.modules["vagabond.cong_no"].ds_khach_no = lambda: {"tong": 111973500, "tong_ca_phieu": 176112000}
		import vagabond
		with um.patch.object(vagabond, "cong_no", sys.modules["vagabond.cong_no"], create=True):
			la("Tài chính đọc tổng kể cả phiếu", tc._phai_thu(), 176112000.0)
			sys.modules["vagabond.cong_no"].ds_khach_no = lambda: {"tong": 111973500}
			try:
				tc._phai_thu()
				loi = ""
			except Exception as e:
				loi = str(e)
			dung("màn Công nợ cũ không trả tổng kể cả phiếu thì báo lỗi, không lấy số thiếu", "phiếu đòi nợ" in loi)


# Sổ cái tháng 10/2026 trên site (Có trừ Nợ), thêm hai tài khoản nhân viên.
GL_T10 = [
	{"so_hieu": "5111", "loai": "Income", "co_tru_no": 1953867209},
	{"so_hieu": "6321", "loai": "Expense", "co_tru_no": -439381018},
	{"so_hieu": "6211", "loai": "Expense", "co_tru_no": -207625971},
	{"so_hieu": "6271", "loai": "Expense", "co_tru_no": -424910760},
	{"so_hieu": "6411", "loai": "Expense", "co_tru_no": -120000000},
	{"so_hieu": "6418", "loai": "Expense", "co_tru_no": -400362170},
	{"so_hieu": "6421", "loai": "Expense", "co_tru_no": -80000000},
	{"so_hieu": "6428", "loai": "Expense", "co_tru_no": -260444909},
	{"so_hieu": "811", "loai": "Expense", "co_tru_no": -26678103},
	{"so_hieu": None, "loai": "Expense", "co_tru_no": -590556},
]


@ca("v626 lãi lỗ tháng 10 theo sổ cái: doanh thu thuần, lãi gộp, food cost, prime cost")
def _lai_lo():
	ll = tc.lai_lo(GL_T10)
	la("doanh thu thuần", ll["doanh_thu_thuan"], 1953867209.0)
	la("giá vốn", ll["gia_von"], 439381018.0)
	la("lãi gộp", ll["lai_gop"], 1514486191.0)
	la("chi phí bán hàng", ll["cp_ban_hang"], 520362170.0)
	la("chi phí quản lý", ll["cp_quan_ly"], 340444909.0)
	la("chi phí sản xuất chưa kết chuyển", ll["cp_san_xuat"], 632536731.0)
	la("khác gồm 811 và tài khoản chưa số hiệu", ll["khac"], -27268659.0)
	la("lãi ròng", ll["lai_rong"], 1514486191.0 - 520362170.0 - 340444909.0 - 632536731.0 - 27268659.0)
	la("food cost", ll["food_cost"], 22.5)
	la("nhân viên", ll["nhan_vien"], 200000000.0)
	la("prime cost", ll["prime_cost"], round((439381018 + 200000000) / 1953867209 * 100, 1))
	la("không doanh thu thì tỉ lệ chưa có", tc.lai_lo([])["food_cost"], None)


@ca("v626 hao hụt tháng 10: kho Baker kiểm kê thiếu quá nguyên liệu dùng là bất thường, xuất huỷ chia doanh thu")
def _hao_hut():
	kk = {"Baker - Nguyên liệu - TV": -301717253, "Kho Lab - TV": 23200000, "Pastry - Nguyên liệu - TV": -1868661}
	dung_ = {"Baker - Nguyên liệu - TV": 185710171, "Pastry - Nguyên liệu - TV": 93430060, "Kho D1 - TV": 69380292}
	huy = {"Kho D1 - TV": 1109141}
	hh = tc.hao_hut(kk, dung_, huy, 1953867209)
	theo = {d["kho"]: d for d in hh["dong"]}
	la("Baker tỉ lệ", theo["Baker - Nguyên liệu - TV"]["ti_le_kiem_ke"], 162.5)
	la("Baker bất thường", theo["Baker - Nguyên liệu - TV"]["bat_thuong"], 1)
	la("Pastry bình thường", theo["Pastry - Nguyên liệu - TV"]["bat_thuong"], 0)
	la("Pastry tỉ lệ", theo["Pastry - Nguyên liệu - TV"]["ti_le_kiem_ke"], 2.0)
	la("Lab thừa không tính thiếu", (theo["Kho Lab - TV"]["thieu"], theo["Kho Lab - TV"]["thua"]), (0.0, 23200000.0))
	la("tỉ lệ huỷ", hh["ti_le_huy"], 0.1)
	la("tổng thiếu", hh["thieu"], 303585914.0)
	la("kho thiếu nhiều nhất lên đầu", hh["dong"][0]["kho"], "Baker - Nguyên liệu - TV")
	la("thiếu mà chưa dùng gì: bất thường", tc.hao_hut({"K": -5}, {}, {}, 0)["dong"][0]["bat_thuong"], 1)


@ca("v626 dự báo 30 ngày: nợ NCC đã nằm trong hồ sơ thanh toán chỉ trừ một lần, chia theo tuần")
def _du_bao():
	ncc = [
		{"name": "PI-1", "han": "2026-08-10", "con_no": 10000000},
		{"name": "PI-2", "han": "2026-08-16", "con_no": 20000000},
		{"name": "PI-3", "han": "2026-08-25", "con_no": 30000000},
		{"name": "PI-4", "han": "2026-09-13", "con_no": 5000000},
		{"name": "PI-5", "han": "2026-09-14", "con_no": 7000000},
		{"name": "PI-6", "han": "", "con_no": 1000000},
		{"name": "PI-7", "han": "2026-08-20", "con_no": 8000000},
	]
	giu = {"PI-7": 8000000, "PI-3": 10000000}
	kq = tc.du_bao(100000000, 15000000, ncc, giu, 8000000, 2000000, HOM)
	la("quá hạn gồm khoản không hạn", kq["theo_tuan"]["qua_han"], 11000000.0)
	la("tuần 1", kq["theo_tuan"]["tuan_1"], 20000000.0)
	la("tuần 2: PI-3 trừ phần hồ sơ giữ, PI-7 giữ hết", kq["theo_tuan"]["tuan_2"], 20000000.0)
	la("tuần 4 gồm ngày thứ 30", kq["theo_tuan"]["tuan_4"], 5000000.0)
	la("sau 30 ngày không trừ", kq["sau_30"], 7000000.0)
	la("tổng trả NCC", kq["tra_ncc"], 56000000.0)
	la("cuối kỳ", kq["cuoi_ky"], 100000000 + 15000000 - 56000000 - 8000000 - 2000000.0)
	la("nếu khách chưa trả", kq["cuoi_ky_khong_thu"], 34000000.0)
	la("chưa chốt số dư thì không đoán cuối kỳ", tc.du_bao(None, 5, [], {}, 0, 0, HOM)["cuoi_ky"], None)


def _du_bao_30(hong=()):
	"""Chạy THẬT du_bao_30; nguồn nằm trong `hong` thì ném lỗi như mất kết nối."""
	def _ne(ten, gia_tri):
		def f(*a, **k):
			if ten in hong:
				raise RuntimeError("mất kết nối " + ten)
			return gia_tri
		return f
	tien = {"dong": [{"so_du": 100000000.0}], "tong": {"tong": 100000000.0, "chua_chot": 0}}
	ncc = ([{"name": "PI-1", "han": "2026-08-20", "con_no": 30000000, "account_currency": "VND"}], 30000000.0, 0.0)
	with um.patch.object(tc, "_kiem", lambda: None), \
		um.patch.object(tc, "_tinh_tien", lambda: tien), \
		um.patch.object(tc, "_phai_thu", _ne("phai_thu", 15000000.0)), \
		um.patch.object(tc, "_ncc", _ne("ncc", ncc)), \
		um.patch.object(tc, "_giu_boi_app", _ne("giu", {})), \
		um.patch.object(tc, "_cho_chi", lambda: {"tien": 0.0, "tien_cho_duyet": 0.0}), \
		um.patch.object(tc, "nowdate", lambda: "2026-08-15"):
		return tc.du_bao_30()


@ca("v626 Codex #524: dự báo 30 ngày không coi nguồn đọc hỏng là 0, không kết luận số cuối kỳ")
def _du_bao_hong():
	du = _du_bao_30()
	la("đủ nguồn: kết luận cuối kỳ", (du["cuoi_ky"], du["thieu"]), (85000000.0, []))
	for nguon, nhan in (("ncc", "Nợ nhà cung cấp"), ("phai_thu", "Khách nợ mình"),
			("giu", "Hồ sơ thanh toán đang giữ hoá đơn")):
		kq = _du_bao_30(hong=(nguon,))
		la("hỏng %s: không có số cuối kỳ" % nguon, (kq["cuoi_ky"], kq["cuoi_ky_khong_thu"]), (None, None))
		la("hỏng %s: báo đúng phần thiếu" % nguon, kq["thieu"], [nhan])
		hong_ncc = nguon in ("ncc", "giu")
		la("hỏng %s: các tuần nợ NCC %s" % (nguon, "không hiện số" if hong_ncc else "vẫn có số"),
			(kq["theo_tuan"] is None, kq["sau_30"] is None, kq["tra_ncc"] is None), (hong_ncc, hong_ncc, hong_ncc))
	kq = _du_bao_30(hong=("ncc", "phai_thu"))
	la("hỏng hai nguồn báo cả hai", kq["thieu"], ["Khách nợ mình", "Nợ nhà cung cấp"])
	la("phần đọc hỏng không hiện thành 0", (kq["phai_thu"], kq["tra_ncc"]), (None, None))


@ca("v626 chọn tháng: tháng sau hôm nay về tháng này, gõ thiếu số 0 vẫn nhận, tháng trước của tháng 1")
def _thang():
	la("rỗng", tc.doc_thang("", HOM), "2026-08")
	la("tương lai", tc.doc_thang("2026-09", HOM), "2026-08")
	la("thiếu số 0", tc.doc_thang("2026-7", HOM), "2026-07")
	la("tháng 13", tc.doc_thang("2026-13", HOM), "2026-08")
	la("tháng trước của tháng 1", tc.thang_truoc("2026-01"), "2025-12")
	la("khoảng tháng 2", tc.khoang_thang("2028-02"), (dt.date(2028, 2, 1), dt.date(2028, 2, 29)))


def _tinh(moc, nop_quy_cho=0.0, ps=None):
	"""Chạy THẬT _tinh_tien với nguồn, mốc và phát sinh giả."""
	def _ps(ba, sau):
		return {"MB-CTY-31561568 - MB Bank": (300000000.0, 120000000.0, 42)}.get(ba, (0.0, 0.0, 0))
	_ps = ps or _ps

	def _nq(diem=None, trang_thai=("Đã nộp quỹ",), sau_ngay=None, theo="giao"):
		if trang_thai == ("Chờ ký nhận",):
			if nop_quy_cho == "hong":
				raise RuntimeError("mất kết nối phiếu nộp quỹ")
			return nop_quy_cho, 1 if nop_quy_cho else 0
		if diem == "TCV":
			return 3000000.0, 1
		if diem is None and theo == "nhan":
			return 3000000.0, 1
		return 0.0, 0

	with um.patch.object(tc, "_sepay_so_bao", lambda: dict(SO_BAO)), \
		um.patch.object(tc, "_cac_nguon", lambda so_bao=None: tc.nguon_ngan_hang(BAN_DO, TK, so_bao or {}) + tc.nguon_tien_mat(DIEM)), \
		um.patch.object(tc, "_cac_moc", lambda: moc), \
		um.patch.object(tc, "_phat_sinh_nh", _ps), \
		um.patch.object(tc, "_tien_mat_vao_ket", lambda diem, tu, den=None: {"TCV": 4500000.0}.get(diem, 0.0)), \
		um.patch.object(tc, "_nop_quy", _nq), \
		um.patch.object(tc, "_so_cai_quy", lambda sau: (0.0, 1500000.0)), \
		um.patch.object(tc, "_ca_gan_nhat", lambda d: {"chot_luc": "2026-08-14 22:10:00", "tien_mat_dem": 4560000} if d == "TCV" else None):
		return tc._tinh_tien()


MOC = [
	{"name": "MSD-1", "nguon": "nh:31561568", "ngay_chot": "2026-08-01", "so_du": 1000000000, "luc": "2026-08-02 08:00"},
	{"name": "MSD-2", "nguon": "tm:TCV", "ngay_chot": "2026-08-10", "so_du": 5000000, "luc": "2026-08-10 23:00"},
	{"name": "MSD-3", "nguon": "tm:QUY", "ngay_chot": "2026-08-10", "so_du": 100000000, "luc": "2026-08-10 23:00"},
]


@ca("v626 tiền hiện có: MB tính từ mốc, Shinhan lấy số SePay báo, két trừ nộp quỹ, quỹ cộng nộp quỹ và trừ chi sổ cái")
def _tien():
	kq = _tinh(MOC)
	theo = {d["nguon"]: d for d in kq["dong"]}
	la("MB = mốc + vào - ra", theo["nh:31561568"]["so_du"], 1180000000.0)
	la("MB SePay báo 0: không kết luận", theo["nh:31561568"]["doi_chieu"]["tt"], "khong_bao")
	la("Shinhan lấy số SePay báo", theo["nh:700037279585"]["so_du"], 242995597.0)
	dung("Shinhan ghi rõ nguồn số", "Số dư SePay báo" in theo["nh:700037279585"]["ghi"])
	la("OCB tạm ứng chưa chốt", theo["nh:0901486556"]["so_du"], None)
	la("két TCV = 5tr + 4,5tr vào - 3tr nộp quỹ", theo["tm:TCV"]["so_du"], 6500000.0)
	la("két TCV kèm chốt ca gần nhất", theo["tm:TCV"]["ca"]["dem"], 4560000.0)
	la("quỹ = 100tr + 3tr nhận - 1,5tr chi", theo["tm:QUY"]["so_du"], 101500000.0)
	la("két chưa chốt", theo["tm:SALES"]["so_du"], None)
	la("tổng chỉ cộng nguồn đã có số", kq["tong"]["tong"], 1180000000.0 + 242995597.0 + 6500000.0 + 101500000.0)
	la("đếm chỗ chưa chốt", kq["tong"]["chua_chot"], 5)
	la("không có phiếu chờ ký nhận thì không có dòng đang chuyển", "tm:DANG" in theo, False)


@ca("v626 tiền hiện có: phiếu nộp quỹ chờ ký nhận đã rời két thì hiện dòng Đang nộp về quỹ, vẫn tính vào tổng")
def _tien_dang():
	kq = _tinh(MOC, nop_quy_cho=2000000.0)
	theo = {d["nguon"]: d for d in kq["dong"]}
	la("dòng đang chuyển", theo["tm:DANG"]["so_du"], 2000000.0)
	la("cộng vào tiền mặt", kq["tong"]["tien_mat"], 6500000.0 + 101500000.0 + 2000000.0)


@ca("v626 tiền hiện có: SePay báo số dư MB lệch số tự tính thì chip lệch kèm số")
def _tien_lech():
	so_bao = dict(SO_BAO, **{"31561568": 1179800000.0})
	n = [x for x in tc.nguon_ngan_hang(BAN_DO, TK, so_bao) if x["nguon"] == "nh:31561568"][0]
	la("so_bao vào nguồn", n["so_bao"], 1179800000.0)
	dc = tc.doi_chieu(1180000000.0, n["so_bao"])
	la("lệch 200.000", (dc["tt"], dc["lech"]), ("lech", 200000.0))


class _Doc(dict):
	DA = []

	def insert(self, **k):
		_Doc.DA.append(dict(self))
		self["name"] = "MSD-26-08-00001"
		return self

	def __getattr__(self, k):
		return self.get(k)


def _chay_luu(vai, nguoi="dung@vagabond.vn", xem=("dung@vagabond.vn",), **ts):
	_Doc.DA = []
	with um.patch.object(_fr, "get_roles", lambda *a, **k: list(vai)), \
		um.patch.object(_fr.session, "user", nguoi), \
		um.patch.object(tc, "_nguoi_xem", lambda: list(xem)), \
		um.patch.object(tc, "_cac_nguon", lambda so_bao=None: _nguon()), \
		um.patch.object(_fr, "get_doc", lambda d=None, *a, **k: _Doc(d) if isinstance(d, dict) else _Doc()):
		try:
			return tc.luu_moc(**ts), None
		except Exception as e:
			return None, e


@ca("v626 cửa ghi mốc chốt: kế toán viên không được chọn bị chặn, không ghi gì")
def _luu_chan():
	kq, loi = _chay_luu(["Accounts Manager", "Accounts User"], nguoi="khai@vagabond.vn",
		nguon="nh:31561568", ngay_chot="2026-08-14", so_du="1.000.000.000")
	# Bản giả frappe.throw không giữ lớp lỗi; Frappe thật ném PermissionError.
	dung("chặn: %r" % loi, loi is not None and "chỉ mở cho Giám đốc" in str(loi))
	la("không ghi", _Doc.DA, [])


@ca("v626 cửa ghi mốc chốt: kế toán trưởng được chọn lưu đúng nguồn, tên, loại, số đã đọc, người lưu")
def _luu_dat():
	kq, loi = _chay_luu(["Accounts Manager"], nguon="nh:0901486556", ngay_chot="14/08/2026", so_du="52.100.000 đ", ghi_chu="theo sao kê")
	la("không lỗi", loi, None)
	la("ghi một mốc", len(_Doc.DA), 1)
	d = _Doc.DA[0]
	la("trường", (d["doctype"], d["nguon"], d["ten_nguon"], d["loai"], d["ngay_chot"], d["so_du"], d["nguoi"]),
		("Vagabond Moc So Du", "nh:0901486556", "OCB ···6556 (tạm ứng)", "Ngân hàng", "2026-08-14", 52100000.0, "dung@vagabond.vn"))
	kq2, loi2 = _chay_luu(["Giám đốc"], nguoi="viet@vagabond.vn", nguon="tm:TCV", ngay_chot="2026-08-16", so_du="5.000.000")
	dung("ngày sau hôm nay bị chặn: %r" % loi2, loi2 is not None and "sau hôm nay" in str(loi2))
	la("không ghi", _Doc.DA, [])
	kq3, loi3 = _chay_luu(["Giám đốc"], nguoi="viet@vagabond.vn", nguon="tm:TCV", ngay_chot="2026-08-14", so_du="năm triệu")
	dung("số chữ bị chặn: %r" % loi3, loi3 is not None and "bằng số" in str(loi3))
	la("không ghi", _Doc.DA, [])


@ca("v626 chọn người xem: chỉ Giám đốc lưu được; chỉ giữ tài khoản đang bật")
def _nguoi_xem_luu():
	ghi = {}
	with um.patch.object(_fr, "get_roles", lambda *a, **k: ["Accounts Manager"]), \
		um.patch.object(_fr.session, "user", "dung@vagabond.vn"), \
		um.patch.object(tc, "_nguoi_xem", lambda: ["dung@vagabond.vn"]):
		try:
			tc.luu_nguoi_xem('["son@vagabond.vn"]')
			loi = None
		except Exception as e:
			loi = e
		dung("kế toán trưởng không tự thêm người: %r" % loi, loi is not None and "Chỉ Giám đốc" in str(loi))
	db = _fr.db
	with um.patch.object(_fr, "get_roles", lambda *a, **k: ["Giám đốc"]), \
		um.patch.object(_fr.session, "user", "viet@vagabond.vn"), \
		um.patch.object(tc, "_nguoi_xem", lambda: []), \
		um.patch.object(_fr, "get_all", lambda dt, **k: ["dung@vagabond.vn"] if dt == "User" else []), \
		um.patch.object(db, "set_single_value", lambda d, f, v: ghi.update({(d, f): v}), create=True):
		kq = tc.luu_nguoi_xem('["Dung@vagabond.vn", "nguoi.da.nghi@vagabond.vn"]')
	la("chỉ giữ người đang bật", kq["nguoi_xem"], ["dung@vagabond.vn"])
	la("ghi vào cài đặt", ghi.get(("Vagabond Tai Chinh Cai Dat", "nguoi_xem")), "dung@vagabond.vn")


def _doc(*p):
	with open(os.path.join(GOC, *p), encoding="utf-8") as f:
		return f.read()


@ca("v626 danh sách vai luôn xem: JS và máy chủ trùng từng chữ")
def _vai_trung():
	js = _doc("public", "js", "bep", "61-tai-chinh.js")
	m = re.search(r"var TC_VAI_LUON_XEM = \[([^\]]*)\];", js)
	dung("có dòng TC_VAI_LUON_XEM", m)
	ds = re.findall(r"'([^']+)'", m.group(1)) if m else []
	la("trùng máy chủ", tuple(ds), tc.VAI_LUON_XEM)


@ca("v626 trang chủ: mọi ô Tài chính chỉ dựng dưới coQuyenTaiChinh, khoá riêng không mượn CN, SODU")
def _trang_chu():
	js = _doc("public", "js", "bep", "02-trang-chu.js")
	i = js.index("if (coQuyenTaiChinh()) {")
	j = js.index("}", js.index("'TCCD')", i))
	khoi = js[i:j]
	khoa = re.findall(r"card\([^;]*?, (?:0|[a-zA-Z]+), '([A-Z:]+)'\)", khoi)
	la("đủ mười một ô", sorted(khoa), sorted(["TCTQ", "TCTIEN", "TCDONG", "TCDB", "TCLL", "TCTL", "TCPT", "TCPTR", "TCCHO", "TCTT", "TCCD"]))
	nhom = re.search(r"k: 'TC', ten: 'Tài chính'[^\n]*\n\s*keys: \[([^\]]*)\]", js)
	dung("có phân hệ TC", nhom)
	la("phân hệ chỉ chứa khoá TC", sorted(re.findall(r"'([A-Z]+)'", nhom.group(1))) if nhom else [], sorted(khoa))
	for k in khoa:
		la("khoá %s chỉ dựng một lần trên trang chủ" % k, len(re.findall(r", '%s'\)" % k, js)), 1)


class _CacheGia:
	def __init__(self):
		self.d = {}

	def get_value(self, k):
		return self.d.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		self.d[k] = v


@ca("v626 Codex #524 vòng 3: một tài khoản tính hỏng thì dự báo không kết luận, Tiền hiện có báo đúng là lỗi chứ không phải chưa chốt")
def _du_bao_so_du_hong():
	def _ps(ba, sau):
		raise RuntimeError("mất kết nối sổ ngân hàng")
	# MB công ty có mốc chốt, đọc phát sinh hỏng; két District 1 và quỹ vẫn đọc được.
	kq = _tinh(MOC, ps=_ps)
	mb = next(d for d in kq["dong"] if d["nguon"] == "nh:31561568")
	la("MB: không có số, ghi rõ lỗi", (mb["so_du"], mb.get("loi")), (None, 1))
	la("tổng đếm riêng chỗ lỗi, không lẫn vào chưa chốt", (kq["tong"]["loi"], kq["tong"]["chua_chot"]), (1, 5))
	with um.patch.object(tc, "_kiem", lambda: None), \
		um.patch.object(tc, "_tinh_tien", lambda: kq), \
		um.patch.object(tc, "_phai_thu", lambda: 0.0), \
		um.patch.object(tc, "_ncc", lambda: ([], 0.0, 0.0)), \
		um.patch.object(tc, "_giu_boi_app", lambda: {}), \
		um.patch.object(tc, "_cho_chi", lambda: {"tien": 0.0, "tien_cho_duyet": 0.0}), \
		um.patch.object(tc, "nowdate", lambda: "2026-08-15"):
		du = tc.du_bao_30()
	la("dự báo không có số cuối kỳ", (du["cuoi_ky"], du["cuoi_ky_khong_thu"]), (None, None))
	la("dự báo báo đúng phần thiếu", du["thieu"], ["Số dư tài khoản, két"])
	# SePay không đọc được: Shinhan sống nhờ số SePay báo nên cũng là lỗi.
	with um.patch.object(tc, "_sepay_so_bao", lambda: {}):
		kq2 = _tinh_khong_sepay(MOC)
	sh = next(d for d in kq2["dong"] if d["nguon"] == "nh:700037279585")
	la("Shinhan khi SePay không đọc được: lỗi, không phải chưa chốt", (sh["so_du"], sh.get("loi")), (None, 1))
	kq3 = _tinh(MOC, nop_quy_cho="hong")
	dang = [d for d in kq3["dong"] if d["nguon"] == "tm:DANG"]
	la("phiếu nộp quỹ chờ ký nhận đọc hỏng: có dòng lỗi, tổng đếm lỗi",
		([(d["so_du"], d.get("loi")) for d in dang], kq3["tong"]["loi"]), ([(None, 1)], 1))


def _tinh_khong_sepay(moc):
	def _ps(ba, sau):
		return {"MB-CTY-31561568 - MB Bank": (300000000.0, 120000000.0, 42)}.get(ba, (0.0, 0.0, 0))

	def _nq(diem=None, trang_thai=("Đã nộp quỹ",), sau_ngay=None, theo="giao"):
		return 0.0, 0
	with um.patch.object(tc, "_cac_nguon", lambda so_bao=None: tc.nguon_ngan_hang(BAN_DO, TK, so_bao or {}) + tc.nguon_tien_mat(DIEM)), \
		um.patch.object(tc, "_cac_moc", lambda: moc), \
		um.patch.object(tc, "_phat_sinh_nh", _ps), \
		um.patch.object(tc, "_tien_mat_vao_ket", lambda diem, tu, den=None: 0.0), \
		um.patch.object(tc, "_nop_quy", _nq), \
		um.patch.object(tc, "_so_cai_quy", lambda sau: (0.0, 0.0)), \
		um.patch.object(tc, "_ca_gan_nhat", lambda d: None):
		return tc._tinh_tien()


@ca("v626 Codex #524 vòng 3: một két đọc hỏng thì dòng tiền báo thiếu, không lưu số thiếu vào bộ nhớ đệm")
def _tien_mat_ngay_hong():
	cache = _CacheGia()
	hong = {"on": True}

	def _vk(diem, tu, den=None):
		if diem == "NVHTN" and hong["on"]:
			raise RuntimeError("mất kết nối")
		return {"TCV": 1000000.0, "NVHTN": 2000000.0}.get(diem, 0.0)
	tm = tc.nguon_tien_mat(DIEM)
	with um.patch.object(tc.frappe, "cache", lambda: cache, create=True), \
		um.patch.object(tc, "_tien_mat_vao_ket", _vk), \
		um.patch.object(tc, "nowdate", lambda: "2026-08-15"):
		ra, thieu = tc._tien_mat_theo_ngay(dt.date(2026, 8, 13), dt.date(2026, 8, 14), tm)
		la("ngày còn đọc được phần két đúng", ra, {"2026-08-13": 1000000.0, "2026-08-14": 1000000.0})
		la("báo đúng két và ngày thiếu", thieu, [("NVHTN", "2026-08-13"), ("NVHTN", "2026-08-14")])
		la("không lưu số thiếu vào bộ nhớ đệm", cache.d, {})
		hong["on"] = False
		ra2, thieu2 = tc._tien_mat_theo_ngay(dt.date(2026, 8, 13), dt.date(2026, 8, 14), tm)
		la("hết lỗi thì đọc lại đủ", (ra2, thieu2), ({"2026-08-13": 3000000.0, "2026-08-14": 3000000.0}, []))
		la("ngày đủ mới lưu bộ nhớ đệm", sorted(cache.d.values()), [3000000.0, 3000000.0])
