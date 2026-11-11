"""v649 đối soát GrabFood: phí quảng cáo không mã, đơn mã dài ngắt dòng.

Site thật 11/11/2026, báo cáo ngày 10/11 cả ba cửa hàng:
- Mục Marketing in cột Mã giao dịch là "-" (DSN-2611-06815 NVHTN: 6 đơn cộng
  447.292, Tổng thu nhập 398.153, chênh 49.139 đúng bằng dòng quảng cáo). Mẫu
  cũ bắt buộc ADS-số và bỏ qua dòng lặng lẽ.
- Ô Mã đơn căn giữa theo chiều dọc: mã dài (GD-3O7K2M7B, GF-255F) xuống hai dòng,
  tiền tố nằm TRÊN dòng đơn, phần sau nằm DƯỚI (toạ độ đọc từ PDF thật: GD- y=78,
  dòng đơn y=75, 3O7K2M7B y=72). PyMuPDF có thể trả ba mảnh theo thứ tự nào cũng
  được nên ca kiểm thử MỌI thứ tự.
Dòng chữ dưới đây chép từ PDF thật, cửa hàng và số tiền giữ nguyên.
"""
from itertools import permutations

from vagabond import doi_soat_mau as M
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _pdf(ten, chu):
	return dict(ten=ten, loai="pdf", sha256="x", trang=[dict(ten="Trang 1", dong=chu.strip("\n").split("\n"))])


DAU = """Báo cáo kinh doanh hàng ngày
10 tháng 11 2026, thứ ba                                     https://grb.to/hotrodoitacnhahang
The Vagabond Pâtisserie Brasserie - Nhà Văn Hóa Thanh Niên
Tóm tắt thông tin
  Tổng thu nhập          Còn thiếu Grab          Tổng số đơn hàng
 VND {tong}              VND 0          {so} đơn hàng
Thu nhập
Tổng tiền thanh toán sẽ được chuyển cho bạn vào ngàythứ tư, tháng 11 11. Tài khoản của bạn có thể phải đợi vài ngày.
Đơn hàng từ ứng dụng và web
 Đơn hàng Delivery
"""

NVHTN_DON = """ 5:28 PM      GF-591       Trả thẻ / Ví        115.000      0        -    -17.250        -14.389             0    83.361
 3:49 PM      GF-451       Trả thẻ / Ví         90.000      0        -          0        -13.248             0    76.752
 12:04 PM     GF-101       Trả thẻ / Ví        160.000      0        -    -24.000        -20.020             0   115.980
 10:03 AM     GF-052       Trả thẻ / Ví        110.000      0        -     -9.750        -14.757             0    85.493
 9:06 AM      GF-523       Trả thẻ / Ví         45.000      0        -          0         -6.624             0    38.376
 8:28 AM      GF-027       Trả thẻ / Ví         60.000      0        -     -4.500         -8.170             0    47.330
                                                                                              447.292
 Tổng cộng                                       VND 447.292
"""

MKT = """Marketing
 10 Th11, 12:04 PM     -      Tự động tìm từ khoá - 2026-11-10          -45.500     -3.639     -49.139
                                                                          VND-49.139
Hướng dẫn đọc hiểu báo cáo
"""


def _nvhtn(don=NVHTN_DON, mkt=MKT, tong="398.153", so=6):
	return _pdf("5-C8BKA3MZMEW1CA-20261110.pdf", DAU.format(tong=tong, so=so) + don + mkt)


@ca("v649 GrabFood: dòng quảng cáo mã '-' được đọc, tổng khớp Tổng thu nhập (NVHTN 10/11 thật)")
def _():
	kq = M.doc(_nvhtn())
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	qc = [d for d in kq["dong"] if d["loai"] == "phi_ky"]
	la("một dòng quảng cáo", len(qc), 1)
	la("tiền quảng cáo", (qc[0]["thuc_nhan"], qc[0]["phi"], qc[0]["thue"]), (-49139, 49139, 3639))
	dung("có căn cứ đọc từ PDF", "Tự động tìm từ khoá" in qc[0]["ma_can_cu"])
	la("cộng = Tổng thu nhập", sum(d["thuc_nhan"] for d in kq["dong"]), 398153)


@ca("v649 GrabFood: hai khoản quảng cáo cùng giờ cùng tiền khác mô tả không bị coi là trùng (Sales Online 10/11)")
def _():
	mkt = """Marketing
 10 Th11, 11:00 AM     -      Từ khóa thủ công - 2026-11-10          -45.500     -3.639     -49.139
 10 Th11, 3:09 PM      -      Đồng tài trợ đa tầng - Tiêu Chuẩn - 2026-11-10          -600     -48     -648
 10 Th11, 3:09 PM      -      Đồng tài trợ đa tầng - Riêng cho bạ - 2026-11-10          -600     -48     -648
Hướng dẫn đọc hiểu báo cáo
"""
	kq = M.doc(_nvhtn(mkt=mkt, tong=str(447292 - 49139 - 648 - 648)[:3] + "." + str(447292 - 49139 - 648 - 648)[3:]))
	qc = [d for d in kq["dong"] if d["loai"] == "phi_ky"]
	la("ba dòng", len(qc), 3)
	la("căn cước khác nhau", len({d["ma_su_kien"] for d in qc}), 3)
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))


@ca("v649 GrabFood: dòng quảng cáo mở đầu đúng dạng mà không đọc được thì báo lỗi, không bỏ qua lặng lẽ")
def _():
	mkt = MKT.replace("-3.639     -49.139", "-3.639     -49,139")
	kq = M.doc(_nvhtn(mkt=mkt))
	dung("có dòng lỗi", len(kq["dong_loi"]) == 1)
	dung("lỗi nói quảng cáo", "quảng cáo" in kq["dong_loi"][0]["ly_do"])


@ca("v649 GrabFood: mẫu cũ có mã ADS vẫn đọc như trước")
def _():
	kq = M.doc(_nvhtn(mkt=MKT.replace("     -      Tự", "     ADS-77      Tự")))
	qc = [d for d in kq["dong"] if d["loai"] == "phi_ky"][0]
	la("căn cứ là mã ADS", qc["ma_can_cu"], "ADS-77")
	la("không lỗi", kq["dong_loi"], [])


# Đơn GD-3O7K2M7B của TCV 10/11 (210.000, thu nhập 144.975) bị ngắt ba mảnh.
TIEN_TO = "                    GD-"
DONG_KHONG_MA = " 12:25 PM                  Trả thẻ / Ví        210.000      0        -    -40.000        -25.025             0   144.975"
DUOI = "                    3O7K2M7B"
DONG_CUT = " 12:25 PM     GD-          Trả thẻ / Ví        210.000      0        -    -40.000        -25.025             0   144.975"


def _voi_don_ngat(manh):
	don = NVHTN_DON.replace(
		"                                                                                              447.292\n",
		"\n".join(manh) + "\n                                                                                              592.267\n",
	).replace("VND 447.292", "VND 592.267")
	return _nvhtn(don=don, tong="543.128", so=7)


@ca("v649 GrabFood: đơn mã dài ngắt ba mảnh ghép lại đúng với MỌI thứ tự mảnh")
def _():
	for thu_tu in permutations([TIEN_TO, DONG_KHONG_MA, DUOI]):
		kq = M.doc(_voi_don_ngat(list(thu_tu)))
		la("không lỗi %s" % [m.strip()[:8] for m in thu_tu], (kq["dong_loi"], kq["loi"]), ([], []))
		gd = [d for d in kq["dong"] if d["ma_don"] == "GD-3O7K2M7B"]
		la("có đơn GD-3O7K2M7B", [(d["thuc_nhan"], d["gio"]) for d in gd], [(144975, "12:25:00")])


@ca("v649 GrabFood: dòng đơn có mã cụt 'GD-' cùng phần sau nằm trước hay sau đều ghép được")
def _():
	for manh in ([DONG_CUT, DUOI], [DUOI, DONG_CUT]):
		kq = M.doc(_voi_don_ngat(manh))
		la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
		dung("có GD-3O7K2M7B", any(d["ma_don"] == "GD-3O7K2M7B" for d in kq["dong"]))


@ca("v649 GrabFood: hai đơn liền nhau cùng bị ngắt (Sales Online 10/11: GF-255F rồi đơn huỷ) ghép đúng từng đơn")
def _():
	manh = ["                    GF-",
		" 2:24 PM                   Trả thẻ / Ví        215.000      0        -    -50.500        -24.215             0   140.285",
		"                    255F",
		"                    GF-",
		" Đã hủy                    -              -            -        -          -            -              -          -",
		"                    9AB2"]
	don = NVHTN_DON.replace(
		"                                                                                              447.292\n",
		"\n".join(manh) + "\n                                                                                              587.577\n",
	).replace("VND 447.292", "VND 587.577")
	kq = M.doc(_nvhtn(don=don, tong="538.438", so=8))
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	dung("đơn GF-255F", any(d["ma_don"] == "GF-255F" and d["thuc_nhan"] == 140285 for d in kq["dong"]))
	la("đơn huỷ", kq["them"]["don_huy"], ["GF-9AB2"])


@ca("v649 GrabFood: mảnh không ghép được vẫn báo lỗi kèm chữ gốc, không mất lặng lẽ")
def _():
	kq = M.doc(_voi_don_ngat([TIEN_TO, DONG_KHONG_MA]))
	la("một lỗi", len(kq["dong_loi"]), 1)
	dung("giữ chữ gốc của mảnh", any("GD-" in t for t in kq["dong_loi"][0]["tho"]))
	kq = M.doc(_voi_don_ngat([DONG_KHONG_MA]))
	la("dòng đơn thiếu mã một mình là lỗi", len(kq["dong_loi"]), 1)


@ca("v649 GrabFood: ghep_don_grab thuần, mảnh mâu thuẫn thì báo")
def _():
	la("chưa đủ mảnh", M.ghep_don_grab([TIEN_TO]), None)
	la("đủ", M.ghep_don_grab([TIEN_TO, DUOI, DONG_KHONG_MA]).split()[:3], ["12:25", "PM", "GD-3O7K2M7B"])
	try:
		M.ghep_don_grab([DONG_KHONG_MA, DONG_CUT])
		dung("hai dòng đơn phải lỗi", False)
	except M.LoiDong:
		dung("hai dòng đơn phải lỗi", True)


@ca("v649 OnePay: thư thông báo bảo trì ngân hàng không phải thư báo cáo (thư thật 11/11/2026)")
def _():
	from vagabond.doi_soat_vendor import thu_co_bao_cao
	than = "<p>OnePay thong bao: he thong thanh toan qua the Ngan hang VietinBank va SeABank tam gian doan...</p>"
	la("thư bảo trì", thu_co_bao_cao(
		"[OnePay Thong bao]: Thong bao bao tri he thong Ngan hang VietinBank và SeABank", than), False)
	la("thư tạm ứng vẫn là báo cáo", thu_co_bao_cao("[OnePay] Thong bao tam ung ngay 10/11/2026", than), True)
	la("báo cáo đối soát có chữ bảo trì vẫn là báo cáo",
		thu_co_bao_cao("Bao cao doi soat ngay 10/11 (sau bao tri)", than), True)


@ca("v649 tin Zalo đối soát ghi tên cửa hàng: ba báo cáo GrabFood cùng ngày ra ba tiêu đề khác nhau")
def _():
	from vagabond import doi_soat_thu as T
	la("mã điểm Grab TCV", T.ma_diem_nguon("GRABFOOD:5-C4E1NPWGG2WZFA"), "TCV")
	la("mã điểm Shopee Sales", T.ma_diem_nguon("10332477"), "SALES")
	la("OnePay không có điểm", T.ma_diem_nguon("ONEPAY:VAGABONDWEB"), "")
	ten = {"TCV": "Trần Cao Vân", "SALES": "Sales Online", "NVHTN": "Nhà Văn Hoá Thanh Niên"}
	tieu_de = {T.tin_tep_loi(T.ten_vendor_diem("GrabFood", ten[T.ma_diem_nguon("GRABFOOD:" + tk)]), "ngày 10/11", "x")[0]
		for tk in ("5-C4E1NPWGG2WZFA", "5-C4E1NPWGMGBGNX", "5-C8BKA3MZMEW1CA")}
	la("ba tiêu đề khác nhau", len(tieu_de), 3)
	dung("tiêu đề có tên cửa hàng", any("Trần Cao Vân" in t for t in tieu_de))
	la("không có điểm thì giữ tên đối tác", T.ten_vendor_diem("OnePay", ""), "OnePay")
