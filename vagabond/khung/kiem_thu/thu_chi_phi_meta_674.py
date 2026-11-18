# -*- coding: utf-8 -*-
"""v674 Chi phí quảng cáo Meta: đọc số đã tiêu (quang_cao_meta) và bút toán tháng theo
sao kê thẻ (chi_phi_meta).

Ca chốt theo danh sách tối thiểu trong prompt anh Việt dán 18/11/2026 (mục 5):
nhiều trang và lỗi trang cuối; qua ngày, qua tháng theo múi giờ tài khoản; giá trị 0,
rỗng, None; chạy lại; mã lỗi và che bí mật; hai tiền tệ; hoàn tiền và phí thẻ; một
giao dịch ở cả hai định dạng sao kê; sao kê lệch tháng; thiếu sao kê; chống ghi chi
phí hai lần. Phần quyền và bút toán sửa tay nằm ở thu_chi_phi_242_674 (khuôn chung).
"""

import unittest.mock as um
from datetime import date, datetime, timezone

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import chi_phi_meta as M  # noqa: E402
from vagabond import quang_cao_meta as Q  # noqa: E402
from vagabond.patches import v674_meta_doc_lai as P  # noqa: E402


# ------------------------------------------------------------ đọc số đã tiêu


@ca("v674 Meta cài đặt: 0 ở Đọc lại hợp lệ, None và rỗng báo thiếu, tắt thì không đòi gì, mã tài khoản sai dạng nêu đúng mã")
def _cai_dat():
	cfg, loi = Q.doc_cai_dat({"bat": 1, "co_ma": True, "tai_khoan": "act_123456\n 7654321 ,act_123456", "tu_ngay": "2026-11-01", "doc_lai": 0})
	la("không lỗi", loi, [])
	la("doc_lai 0 giữ là 0", cfg["doc_lai"], 0)
	la("tài khoản chuẩn hoá, bỏ trùng, giữ thứ tự", cfg["tai_khoan"], ["act_123456", "act_7654321"])
	_c, loi = Q.doc_cai_dat({"bat": 1, "co_ma": True, "tai_khoan": "act_123456", "tu_ngay": "2026-11-01", "doc_lai": None})
	dung("None báo thiếu", any("đọc lại" in x for x in loi))
	_c, loi = Q.doc_cai_dat({"bat": 1, "co_ma": True, "tai_khoan": "act_123456", "tu_ngay": "2026-11-01", "doc_lai": ""})
	dung("rỗng báo thiếu", any("đọc lại" in x for x in loi))
	_c, loi = Q.doc_cai_dat({"bat": 1, "co_ma": False, "tai_khoan": "abc", "tu_ngay": None, "doc_lai": 40})
	la("bốn lỗi", len(loi), 4)
	dung("nêu mã sai", any("abc" in x for x in loi))
	cfg, loi = Q.doc_cai_dat({"bat": 0})
	la("tắt thì không lỗi", (cfg["bat"], loi), (0, []))
	la("patch gieo 3 khi trống", (P.gia_tri_gieo(None), P.gia_tri_gieo("")), (3, 3))
	la("patch giữ 0", P.gia_tri_gieo("0"), None)
	la("patch giữ 7", P.gia_tri_gieo(7), None)


@ca("v674 Meta múi giờ: ngày đã xong cắt theo múi giờ tài khoản, qua ngày và qua tháng; múi giờ sai thì ném")
def _mui_gio():
	luc = datetime(2026, 12, 1, 3, 0, tzinfo=timezone.utc)  # 10:00 ngày 1/12 ở Sài Gòn, 19:00 ngày 30/11 ở Los Angeles
	la("Sài Gòn: hôm qua là 30/11", Q.ngay_da_xong(luc, "Asia/Ho_Chi_Minh"), date(2026, 11, 30))
	la("Los Angeles: hôm qua là 29/11", Q.ngay_da_xong(luc, "America/Los_Angeles"), date(2026, 11, 29))
	nem("múi giờ sai", lambda: Q.ngay_da_xong(luc, "Sao/Hoa"), ValueError)
	nem("giờ không có múi", lambda: Q.ngay_da_xong(datetime(2026, 12, 1), "Asia/Ho_Chi_Minh"), ValueError)


@ca("v674 Meta khoảng đọc: lần đầu từ ngày bắt đầu, đọc lại N ngày gần nhất, đọc bù ngày lỡ, không đọc trước ngày bắt đầu")
def _khoang():
	tn = date(2026, 11, 1)
	la("lần đầu", Q.khoang_doc(date(2026, 11, 17), tn, 3, None), (tn, date(2026, 11, 17)))
	la("đọc lại 3 ngày", Q.khoang_doc(date(2026, 11, 17), tn, 3, date(2026, 11, 16)), (date(2026, 11, 14), date(2026, 11, 17)))
	la("0 ngày: chỉ hôm qua", Q.khoang_doc(date(2026, 11, 17), tn, 0, date(2026, 11, 16)), (date(2026, 11, 17), date(2026, 11, 17)))
	la("lỡ 5 ngày: đọc bù", Q.khoang_doc(date(2026, 11, 17), tn, 1, date(2026, 11, 10)), (date(2026, 11, 11), date(2026, 11, 17)))
	la("chưa tới ngày bắt đầu", Q.khoang_doc(date(2026, 10, 31), tn, 3, None), None)
	la("đọc lại không lùi quá ngày bắt đầu", Q.khoang_doc(date(2026, 11, 2), tn, 5, date(2026, 11, 1)), (tn, date(2026, 11, 2)))
	la("cửa sổ 31 ngày", [(str(a), str(b)) for a, b in Q.chia_cua_so(date(2026, 10, 1), date(2026, 11, 5))],
		[("2026-10-01", "2026-10-31"), ("2026-11-01", "2026-11-05")])


def _trang(du_lieu, tiep=None):
	return {"data": du_lieu, "paging": ({"next": tiep} if tiep else {})}


def _dong(ngay, cd, tien, tt="VND"):
	return {"date_start": ngay, "date_stop": ngay, "campaign_id": cd, "campaign_name": "Chiến dịch " + cd, "spend": tien, "account_currency": tt}


@ca("v674 Meta nhiều trang: đọc hết mọi trang; trang cuối lỗi thì ném, không trả số một phần; trang kế ngoài máy chủ Meta thì dừng")
def _trang_meta():
	t1 = _trang([_dong("2026-11-16", "1", "100000")], "https://graph.facebook.com/v23.0/act_1/insights?after=X&access_token=EAAbimat")
	t2 = _trang([_dong("2026-11-17", "1", "0")])
	goi = []
	with um.patch.object(Q, "_goi", lambda url, params, ma: goi.append(url) or (t1 if len(goi) == 1 else t2)):
		d = Q.doc_insights("act_1", "EAAbimat", "v23.0", date(2026, 11, 16), date(2026, 11, 17))
	la("đủ hai trang", [(str(x["ngay"]), x["so_tien"]) for x in d], [("2026-11-16", 100000.0), ("2026-11-17", 0.0)])
	la("số 0 thật được giữ", d[1]["so_tien"], 0.0)

	def loi_trang_2(url, params, ma):
		goi.append(url)
		if len(goi) > 1:
			raise Q.LoiMeta(Q.LOI_MAY_CHU, "HTTP 500")
		return t1
	goi.clear()
	with um.patch.object(Q, "_goi", loi_trang_2):
		nem("trang cuối lỗi thì ném", lambda: Q.doc_insights("act_1", "m", "v23.0", date(2026, 11, 16), date(2026, 11, 17)), Q.LoiMeta)
	xau = _trang([_dong("2026-11-16", "1", "100")], "https://evil.example.com/x?access_token=m")
	with um.patch.object(Q, "_goi", lambda url, params, ma: xau):
		nem("trang kế ngoài máy chủ Meta", lambda: Q.doc_insights("act_1", "m", "v23.0", date(2026, 11, 16), date(2026, 11, 16)), Q.LoiMeta)
	la("url hợp lệ", Q.url_ke_hop_le("https://graph.facebook.com/v23.0/act_1/insights?after=1"), True)
	la("http thường", Q.url_ke_hop_le("http://graph.facebook.com/x"), False)
	la("máy chủ giả mạo", Q.url_ke_hop_le("https://graph.facebook.com.evil.com/x"), False)
	la("có tên đăng nhập", Q.url_ke_hop_le("https://u:p@graph.facebook.com/x"), False)


@ca("v674 Meta dòng dữ liệu: ngày bắt đầu khác ngày kết thúc, thiếu chiến dịch, số sai dạng hay âm đều ném; không đoán số")
def _dong_du_lieu():
	nem("hai ngày", lambda: Q.doc_dong({"date_start": "2026-11-16", "date_stop": "2026-11-17", "campaign_id": "1", "spend": "1"}), Q.LoiMeta)
	nem("thiếu chiến dịch", lambda: Q.doc_dong(_dong("2026-11-16", "", "1")), Q.LoiMeta)
	nem("số sai", lambda: Q.doc_dong(_dong("2026-11-16", "1", "abc")), Q.LoiMeta)
	nem("số âm", lambda: Q.doc_dong(_dong("2026-11-16", "1", "-5")), Q.LoiMeta)
	nem("thiếu số", lambda: Q.doc_dong({"date_start": "2026-11-16", "date_stop": "2026-11-16", "campaign_id": "1"}), Q.LoiMeta)
	la("làm tròn hai số lẻ", Q.doc_dong(_dong("2026-11-16", "1", "12.345"))["so_tien"], 12.35)


@ca("v674 Meta ghi lại: đọc lại cùng số thì không ghi gì; Meta điều chỉnh thì ghi thay; chiến dịch biến mất về 0; hai tiền tệ một chiến dịch thì ném")
def _ghi_lai():
	moi = [Q.doc_dong(_dong("2026-11-16", "1", "100")), Q.doc_dong(_dong("2026-11-16", "2", "50"))]
	cu = {"act_1:2026-11-16:1": (100.0, "VND"), "act_1:2026-11-16:2": (50.0, "VND")}
	ghi, ve0 = Q.ke_hoach_ghi(cu, moi, "act_1", date(2026, 11, 16), date(2026, 11, 16))
	la("chạy lại không đổi", (ghi, ve0), ([], []))
	moi2 = [Q.doc_dong(_dong("2026-11-16", "1", "120"))]
	ghi, ve0 = Q.ke_hoach_ghi(cu, moi2, "act_1", date(2026, 11, 16), date(2026, 11, 16))
	la("ghi thay số mới, không cộng dồn", [(g["khoa"], g["so_tien"]) for g in ghi], [("act_1:2026-11-16:1", 120.0)])
	la("chiến dịch Meta không còn trả về 0", ve0, ["act_1:2026-11-16:2"])
	hai = [Q.doc_dong(_dong("2026-11-16", "1", "100")), Q.doc_dong(_dong("2026-11-16", "1", "5", "USD"))]
	nem("hai tiền tệ", lambda: Q.ke_hoach_ghi({}, hai, "act_1", date(2026, 11, 16), date(2026, 11, 16)), Q.LoiMeta)
	g = Q.gop_theo_ngay([{"ngay": "2026-11-16", "tien_te": "VND", "so_tien": 100}, {"ngay": "2026-11-16", "tien_te": "USD", "so_tien": 5},
		{"ngay": "2026-11-16", "tien_te": "VND", "so_tien": 20}], date(2026, 11, 15), date(2026, 11, 16))
	la("không cộng hai tiền tệ, đủ mọi ngày", g, {"2026-11-15": {}, "2026-11-16": {"VND": 120.0, "USD": 5.0}})


@ca("v674 Meta lỗi: phân loại mã Graph API; che mã truy cập ở mọi chuỗi")
def _loi():
	la("190 hết hạn", Q.phan_loai_loi(190), Q.LOI_HET_HAN)
	la("200 thiếu quyền", Q.phan_loai_loi(200), Q.LOI_QUYEN)
	la("10 thiếu quyền", Q.phan_loai_loi(10), Q.LOI_QUYEN)
	la("17 giới hạn", Q.phan_loai_loi(17), Q.LOI_GIOI_HAN)
	la("mạng 503 không mã", Q.phan_loai_loi(None, None, 503), Q.LOI_MAY_CHU)
	la("100 từ chối", Q.phan_loai_loi(100), Q.LOI_TU_CHOI)
	dung("lỗi tạm tự thử lại", Q.LOI_GIOI_HAN in Q.LOI_TU_THU_LAI and Q.LOI_HET_HAN not in Q.LOI_TU_THU_LAI)
	s = Q.che("GET https://graph.facebook.com/x?access_token=EAAbimatdai123&after=1 lỗi với mã EAAbimatdai123 và EAA" + "x" * 30, "EAAbimatdai123")
	dung("không còn mã", "EAAbimatdai123" not in s and "EAAxxxx" not in s)
	dung("còn phần còn lại", "after=1" in s)
	s2 = Q.che("lỗi khi gọi https://graph.facebook.com/x?after=2&access_token=ABCxyz123")
	dung("không biết trước mã vẫn che tham số access_token", "ABCxyz123" not in s2 and "access_token=***" in s2)


@ca("v674 Meta trạng thái ngày: Chưa đọc, Còn điều chỉnh trong N ngày gần nhất, Đã chốt, Không chi")
def _tt_ngay():
	la("chưa đọc", Q.trang_thai_ngay("2026-11-18", "2026-11-17", 3, True), "Chưa đọc")
	la("còn điều chỉnh", Q.trang_thai_ngay("2026-11-15", "2026-11-17", 3, True), "Meta còn điều chỉnh")
	la("đã chốt", Q.trang_thai_ngay("2026-11-14", "2026-11-17", 3, True), "Đã chốt")
	la("không chi", Q.trang_thai_ngay("2026-11-10", "2026-11-17", 3, False), "Không chi")
	la("chưa đọc lần nào", Q.trang_thai_ngay("2026-11-10", None, 3, True), "Chưa đọc")


# ------------------------------------------------------------ bút toán theo sao kê thẻ


def _sk(nguon, the4, ngd, nbt, dv, tien, n=1, loai="phat_sinh", pi=""):
	ma = "%s:%s:%s:%s:%s:%d" % (the4, ngd, nbt, dv, tien, n)
	s = M.tach_su_kien(ma)
	return {"name": "%s-%s-%d-%s" % (nguon, ngd, n, dv[-4:]), "nguon": nguon, "the4": s["the4"], "ngay_gd": s["ngay_gd"], "ngay_bt": s["ngay_bt"],
		"dv": s["dv"], "tien": tien, "n": n, "phan_loai": M.phan_loai(loai, dv), "purchase_invoice": pi}


@ca("v674 Meta phân loại dòng thẻ: FACEBK là chi Meta; phí ghi FACEBK đi kèm; phí ngoại tệ không rõ để kế toán chọn; lãi, phí thường niên, chi khác không thuộc Meta")
def _phan_loai():
	la("chi", M.phan_loai("phat_sinh", "FACEBK *VKZTV66PJ4"), "meta")
	la("hoàn", M.phan_loai("hoan", "FACEBK *VKZTV66PJ4"), "meta")
	la("chi khác", M.phan_loai("phat_sinh", "ZaloPay*ZALOBUSINESSSO"), "khong")
	la("phí ghi FACEBK", M.phan_loai("phi", "FACEBK FOREIGN FEE"), "phi_meta")
	la("phí ngoại tệ không rõ", M.phan_loai("phi", "FOREIGN TRANSACTION FEE"), "phi_chua_ro")
	la("phí thường niên", M.phan_loai("phi", "Annual Fee"), "khong")
	la("lãi", M.phan_loai("lai", "Interest"), "khong")
	la("tách sự kiện có hai chấm trong đơn vị", M.tach_su_kien("0000:2026-11-01:2026-11-03:A:B:100:2")["dv"], "A:B")
	la("sự kiện hỏng", M.tach_su_kien("0000:abc"), None)


@ca("v674 Meta loại trùng: một giao dịch ở cả PDF lẫn bảng gõ tay tính MỘT lần, giữ cả hai bằng chứng; hai dòng thật trong một bản là hai giao dịch")
def _trung():
	d = [_sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *A1", 16500000), _sk("XLS", "0000", "2026-11-03", "2026-11-05", "FACEBK *A1", 16500000),
		_sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 1), _sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 2),
		_sk("XLS", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 1), _sk("XLS", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 2)]
	g = M.gop_giao_dich(d)
	la("ba giao dịch", len(g), 3)
	la("A1 giữ hai bằng chứng", len([x for x in g if "A1" in x["dv"]][0]["bang_chung"]), 2)
	la("B2 hai giao dịch thật", len([x for x in g if "B2" in x["dv"]]), 2)
	dung("không dòng nào chờ chọn", not any(x["can_quyet"] for x in g))


@ca("v674 Meta loại trùng: hai bản đếm lệch nhau thì phần thừa chờ kế toán chọn; chọn xong theo số kế toán")
def _dem_lech():
	d = [_sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 1), _sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 2),
		_sk("XLS", "0000", "2026-11-03", "2026-11-05", "FACEBK *B2", 4000000, 1)]
	g = M.gop_giao_dich(d)
	la("hai dòng, dòng hai chờ chọn", [bool(x["can_quyet"]) for x in g], [False, True])
	k = g[1]["can_quyet"]["khoa_quyet"]
	g = M.gop_giao_dich(d, {k: {"gia_tri": "1"}})
	la("kế toán chọn 1", len(g), 1)
	g = M.gop_giao_dich(d, {k: {"gia_tri": "2"}})
	la("kế toán chọn 2", (len(g), any(x["can_quyet"] for x in g)), (2, False))


@ca("v674 Meta nghi trùng khác chữ: cùng thẻ, ngày, số tiền mà chữ đơn vị khác giữa hai bản thì chờ chọn; chọn một thì tính một lần")
def _khac_chu():
	d = [_sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *A1B2", 900000), _sk("XLS", "0000", "2026-11-03", "2026-11-05", "FACEBK *AIB2", 900000)]
	g = M.gop_giao_dich(d)
	la("hai dòng đều chờ chọn", [x["can_quyet"]["loai"] for x in g], ["trung", "trung"])
	k = g[0]["can_quyet"]["khoa_quyet"]
	g1 = M.gop_giao_dich(d, {k: {"gia_tri": "mot"}})
	la("một giao dịch", (len(g1), len(g1[0]["bang_chung"])), (1, 2))
	g2 = M.gop_giao_dich(d, {k: {"gia_tri": "hai"}})
	la("hai giao dịch", (len(g2), any(x["can_quyet"] for x in g2)), (2, False))


@ca("v674 Meta chọn dòng: đã ghi sổ không lấy lại; đã có hoá đơn mua không lấy; phí không rõ chờ chọn; kế toán bỏ thì không vào")
def _chon():
	d = [_sk("PDF", "0000", "2026-11-03", "2026-11-05", "FACEBK *A1", 1000000), _sk("PDF", "0000", "2026-11-04", "2026-11-06", "FACEBK *C3", 2000000, pi="ACC-PINV-1"),
		_sk("PDF", "0000", "2026-11-05", "2026-11-07", "FACEBK *D4", 3000000), _sk("PDF", "0000", "2026-11-05", "2026-11-07", "FOREIGN TRANSACTION FEE", 30000, loai="phi")]
	g = M.gop_giao_dich(d)
	da = {[x for x in g if "D4" in x["dv"]][0]["khoa"]}
	vao = M.chon_giao_dich(g, {}, da)
	la("chỉ A1 vào", [x["dv"] for x in vao], ["FACEBK *A1"])
	la("trạng thái", sorted(x["trang_thai"] for x in g), sorted([M.GD_VAO, M.GD_CT_KHAC, M.GD_DA_GHI, M.GD_CHO]))
	phi = [x for x in g if x["phan_loai"] == "phi_chua_ro"][0]
	g = M.gop_giao_dich(d)
	vao = M.chon_giao_dich(g, {"chon:" + phi["khoa"]: {"gia_tri": "vao"}}, da)
	la("kế toán chọn phí vào", sorted(x["dv"] for x in vao), ["FACEBK *A1", "FOREIGN TRANSACTION FEE"])
	g = M.gop_giao_dich(d)
	vao = M.chon_giao_dich(g, {"chon:" + phi["khoa"]: {"gia_tri": "bo"}}, da)
	la("kế toán bỏ phí", [x["dv"] for x in vao], ["FACEBK *A1"])


@ca("v674 Meta bút toán: Nợ 6417 chi trừ hoàn, Nợ 6427 phí, Có 3411 tổng; tháng hoàn nhiều hơn chi thì đảo chiều đúng")
def _but_toan():
	vao = [{"phan_loai": "meta", "tien": 16500000}, {"phan_loai": "meta", "tien": -500000}, {"phan_loai": "phi_meta", "tien": 33000}]
	d, qc, phi = M.dong_but_toan(vao, "6417 - TV", "6427 - TV", "3411 - TV", "Marketing - TV", "2026-11")
	la("số", (qc, phi), (16000000, 33000))
	la("dòng", [(x["account"], x["debit"], x["credit"]) for x in d], [("6417 - TV", 16000000, 0), ("6427 - TV", 33000, 0), ("3411 - TV", 0, 16033000)])
	from vagabond import but_toan_nhap as BN

	la("cân", BN.kiem_can(d), "")
	d, qc, phi = M.dong_but_toan([{"phan_loai": "meta", "tien": -200000}], "6417", "6427", "3411", "", "2026-11")
	la("hoàn nhiều hơn chi", [(x["account"], x["debit"], x["credit"]) for x in d], [("6417", 0, 200000), ("3411", 200000, 0)])


@ca("v674 Meta thiếu sao kê: phủ theo chu kỳ ngân hàng, giao dịch tháng 11 cần sao kê tới 10 ngày sau cuối tháng; lệch tháng; chưa tới ngày thì thiếu")
def _thieu():
	ck = [(date(2026, 10, 1), date(2026, 10, 29)), (date(2026, 10, 30), date(2026, 11, 29)), (date(2026, 11, 30), date(2026, 12, 30))]
	la("tháng 11 đủ", M.thieu_sao_ke(ck, "2026-11", date(2027, 1, 5)), [])
	ck2 = ck[:2]
	la("thiếu từ 30/11 tới 10/12", [(str(a), str(b)) for a, b in M.thieu_sao_ke(ck2, "2026-11", date(2027, 1, 5))], [("2026-11-30", "2026-12-10")])
	la("tháng chưa qua đủ thì thiếu", bool(M.thieu_sao_ke(ck, "2026-11", date(2026, 12, 5))), True)
	ck3 = [(date(2026, 7, 31), date(2026, 9, 2)), (date(2026, 9, 3), date(2026, 9, 30))]
	la("sao kê lệch tháng vẫn phủ tháng 8", M.thieu_sao_ke(ck3, "2026-08", date(2026, 11, 18)), [])
	la("lỗ giữa hai sao kê", [(str(a), str(b)) for a, b in M.thieu_sao_ke([(date(2026, 9, 1), date(2026, 9, 10)), (date(2026, 9, 15), date(2026, 10, 31))], "2026-09", date(2026, 11, 18))],
		[("2026-09-11", "2026-09-14")])


@ca("v674 Meta trạng thái tháng: chưa có sao kê, thiếu chứng từ, khớp, lệch; đã ghi sổ không lấy lại")
def _tt_thang():
	la("chưa có sao kê", M.trang_thai_thang(False, [], [], [], 0, 0), M.TH_CHUA_SK)
	la("thiếu sao kê", M.trang_thai_thang(True, [("a", "b")], [], [], 0, 0), M.TH_CHUA_DU)
	la("còn dòng chờ", M.trang_thai_thang(True, [], [1], [], 0, 0), M.TH_CHUA_DU)
	la("chứng từ khác chưa xem", M.trang_thai_thang(True, [], [], [1], 0, 0), M.TH_CHUA_DU)
	la("khớp", M.trang_thai_thang(True, [], [], [], 100, 100), M.TH_KHOP)
	la("lệch", M.trang_thai_thang(True, [], [], [], 100, 0), M.TH_LECH)
	la("khoá đã ghi chỉ từ bút toán đã ghi sổ", M.khoa_da_ghi([{"je": "JE1", "khoa": ["a"]}, {"je": "JE2", "khoa": ["b"]}], {"JE1"}), {"a"})
