"""Kiem thu luong dong tien: ca lam viec tai quay va phieu nop quy.

Con so trong bo ca lay tu mot ngay ban hang gia dinh nhung sat thuc te
quay D1: tien le dau ca 500k, doanh thu tien mat 4.850.000, chuyen khoan
3.200.000, the 950.000.

Hai tang lech phai TACH BACH: lech ca (thu ngan dem so voi may) bat o
ca_quay, lech ban giao (bang ke menh gia so voi tien dem luc chot) bat o
nop_quy. Bo ca nay chot rang khong tang nao nuot so cua tang kia.
"""

from vagabond import ca_quay as cq
from vagabond import nop_quy as nq
from vagabond.khung.kiem_thu.nen import ca, dung, la

MAY = {"Tiền mặt": 4850000.0, "Chuyển khoản": 3200000.0, "Quẹt thẻ": 950000.0}
SO_BILL = {"Tiền mặt": 41, "Chuyển khoản": 18, "Quẹt thẻ": 5}


# ==================================================== doi soat ca


@ca("đối soát ca: tiền lẻ đầu ca chỉ cộng vào dòng Tiền mặt, không dòng nào khác")
def _():
	bang = cq.ghep_doi_soat(MAY, {"Tiền mặt": 5350000, "Chuyển khoản": 3200000, "Quẹt thẻ": 950000}, 500000, SO_BILL)
	tm = [d for d in bang if d["phuong_thuc"] == "Tiền mặt"][0]
	ck = [d for d in bang if d["phuong_thuc"] == "Chuyển khoản"][0]
	la("phải có tiền mặt = máy + tiền lẻ", tm["phai_co"], 5350000.0)
	la("tiền mặt khớp", tm["lech"], 0.0)
	la("chuyển khoản không dính tiền lẻ", ck["phai_co"], 3200000.0)
	la("số bill đi theo dòng", tm["so_bill"], 41)


@ca("đối soát ca: Tiền mặt luôn đứng đầu bảng")
def _():
	bang = cq.ghep_doi_soat(MAY, {}, 0)
	la("dòng đầu", bang[0]["phuong_thuc"], "Tiền mặt")


@ca("đối soát ca: máy có mà không đếm, hay đếm ra thứ máy không có, đều phải lộ")
def _():
	bang = cq.ghep_doi_soat({"Tiền mặt": 100000.0}, {"VNPay": 50000.0}, 0)
	ten = [d["phuong_thuc"] for d in bang]
	dung("có dòng Tiền mặt", "Tiền mặt" in ten)
	dung("có dòng VNPay", "VNPay" in ten)
	tm = [d for d in bang if d["phuong_thuc"] == "Tiền mặt"][0]
	vp = [d for d in bang if d["phuong_thuc"] == "VNPay"][0]
	la("tiền mặt thiếu cả dòng", tm["lech"], -100000.0)
	la("VNPay thừa không rõ nguồn", vp["lech"], 50000.0)


@ca("đối soát ca: xét lệch TỪNG dòng, thừa bên này không bù được thiếu bên kia")
def _():
	bang = cq.ghep_doi_soat(
		{"Tiền mặt": 1000000.0, "Chuyển khoản": 1000000.0},
		{"Tiền mặt": 500000.0, "Chuyển khoản": 1500000.0}, 0)
	la("tổng lệch cộng dồn tuyệt đối", cq.tong_lech(bang), 1000000.0)
	dung("vẫn bắt gõ lý do dù tổng đại số bằng 0", cq.can_ly_do(bang))


@ca("đối soát ca: lệch dưới 1.000đ coi như tròn số, không bắt lý do")
def _():
	bang = cq.ghep_doi_soat({"Tiền mặt": 100000.0}, {"Tiền mặt": 100500.0}, 0)
	dung("không cần lý do", not cq.can_ly_do(bang))
	bang2 = cq.ghep_doi_soat({"Tiền mặt": 100000.0}, {"Tiền mặt": 101000.0}, 0)
	dung("đúng 1.000đ là phải có lý do", cq.can_ly_do(bang2))


@ca("số đếm: nhận JSON, chặn số âm ngay cửa")
def _():
	la("đọc chuỗi", cq.doc_so_dem('{"Tiền mặt": "500000"}'), {"Tiền mặt": 500000.0})
	try:
		cq.doc_so_dem({"Tiền mặt": -1})
		dung("phải ném lỗi số âm", False)
	except ValueError:
		dung("đã chặn số âm", True)


# ==================================================== nop quy


@ca("bảng kê: mệnh giá nhân số tờ, sắp từ lớn tới nhỏ, bỏ dòng 0 tờ")
def _():
	bang = nq.doc_bang_ke({"20000": 3, "500000": 2, "1000": 0})
	la("hai dòng", len(bang), 2)
	la("dòng đầu là 500k", bang[0]["menh_gia"], 500000)
	la("thành tiền", bang[0]["thanh_tien"], 1000000.0)
	la("tổng", nq.tong_bang_ke(bang), 1060000.0)


@ca("bảng kê: mệnh giá lạ hay số tờ âm là gõ nhầm, chặn thẳng")
def _():
	for tho in ({"333": 1}, {"500000": -2}):
		try:
			nq.doc_bang_ke(tho)
			dung("phải ném lỗi với %s" % tho, False)
		except ValueError:
			dung("đã chặn", True)


@ca("kỳ vọng nộp: tổng tiền đếm các ca trừ tiền lẻ để lại")
def _():
	la("hai ca", nq.tinh_ky_vong([5350000, 2100000], 500000), 6950000.0)
	la("không để lại", nq.tinh_ky_vong([5350000], 0), 5350000.0)


@ca("kỳ vọng nộp: để lại nhiều hơn tiền có là gõ nhầm, chặn thẳng")
def _():
	try:
		nq.tinh_ky_vong([1000000], 2000000)
		dung("phải ném lỗi", False)
	except ValueError:
		dung("đã chặn", True)


@ca("lệch bàn giao: từ 1.000đ là bắt lý do, cùng ngưỡng với tầng ca")
def _():
	dung("500đ cho qua", not nq.can_ly_do(500))
	dung("thiếu 1.000đ phải giải thích", nq.can_ly_do(-1000))
	la("ngưỡng hai tầng bằng nhau", nq.NGUONG_LECH, cq.NGUONG_LECH)


@ca("ký nhận: chỉ kế toán và giám đốc, chặn theo vai")
def _():
	dung("kế toán FIN ký được", nq.duoc_ky_nhan(["AP Kiểm soát (FIN)", "Employee"]))
	dung("giám đốc ký được", nq.duoc_ky_nhan(["AP Giám đốc"]))
	dung("sales không ký được", not nq.duoc_ky_nhan(["Sales User", "Sales Manager"]))
	dung("không vai không ký", not nq.duoc_ky_nhan([]))


@ca("chữ ký: chỉ nhận ảnh ký tay data URL, không nhận chữ gõ hay đường dẫn")
def _():
	dung("ảnh PNG hợp lệ", nq.la_chu_ky("data:image/png;base64,iVBORw0KGgo="))
	dung("chữ thường bị chặn", not nq.la_chu_ky("Nguyễn Văn A"))
	dung("đường dẫn bị chặn", not nq.la_chu_ky("/files/chuky.png"))
	dung("rỗng bị chặn", not nq.la_chu_ky(""))


@ca("mệnh giá: đủ chín tờ từ 500k tới 1k, đúng thứ tự lớn tới nhỏ")
def _():
	la("chín mệnh giá", list(nq.MENH_GIA),
		[500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000])


# ==================================================== bien ban PDF


@ca("biên bản: có quốc hiệu, tên biên bản, tiền bằng số và bằng chữ, hai bên ký")
def _():
	html = nq._html_bien_ban({
		"ma": "NQ-2026-00001", "ngay": "2026-08-20",
		"ten_nguoi_giao": "Trần Huỳnh Như Uyên", "ten_nguoi_nhan": "Chị Dung",
		"giao_luc": "2026-08-20 18:05:00", "nhan_luc": "2026-08-20 18:40:00",
		"tien_le_giu_lai": 500000, "tien_ky_vong": 4850000,
		"tong_thuc_nhan": 4850000, "lech": 0, "ly_do_lech": "",
		"ca": [{"ca": "CA-2026-00001", "quay": "D1", "ngay": "2026-08-20", "tien_mat_dem": 5350000}],
		"menh_gia": [{"menh_gia": 500000, "so_to": 9, "thanh_tien": 4500000},
			{"menh_gia": 50000, "so_to": 7, "thanh_tien": 350000}],
		"chu_ky_ben_giao": "data:image/png;base64,AAA",
		"chu_ky_ben_nhan": "data:image/png;base64,BBB",
	})
	dung("quốc hiệu", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in html)
	dung("tiêu ngữ", "Độc lập - Tự do - Hạnh phúc" in html)
	dung("tên biên bản", "BIÊN BẢN BÀN GIAO TIỀN MẶT" in html)
	dung("tiền bằng số có chấm ngăn", "4.850.000" in html)
	dung("tiền bằng chữ", "Bốn triệu tám trăm năm mươi nghìn đồng" in html)
	dung("bên giao", "BÊN GIAO" in html)
	dung("bên nhận", "BÊN NHẬN" in html)
	dung("ảnh chữ ký bên giao được nhúng", "data:image/png;base64,AAA" in html)
	dung("ngày tháng kiểu hành chính", "20 tháng 08 năm 2026" in html)


@ca("biên bản: lệch thì in khối chênh lệch kèm lý do, khớp thì không in")
def _():
	goc = {
		"ma": "NQ-2026-00002", "ngay": "2026-08-20", "ten_nguoi_giao": "A",
		"ten_nguoi_nhan": "B", "tien_le_giu_lai": 0, "tien_ky_vong": 1000000,
		"tong_thuc_nhan": 950000, "lech": -50000, "ly_do_lech": "Rơi 50k lúc kiểm đếm",
		"ca": [], "menh_gia": [], "chu_ky_ben_giao": "", "chu_ky_ben_nhan": "",
	}
	html = nq._html_bien_ban(goc)
	dung("có khối chênh lệch", "Chênh lệch so với kỳ vọng" in html)
	dung("nêu rõ thiếu", "thiếu" in html)
	dung("có lý do", "Rơi 50k lúc kiểm đếm" in html)
	goc2 = dict(goc, lech=0, tong_thuc_nhan=1000000, ly_do_lech="")
	dung("khớp thì im", "Chênh lệch" not in nq._html_bien_ban(goc2))


@ca("số thành chữ kiểu kế toán: 1.234.567 đọc đúng, không kéo thư viện mạng")
def _():
	# Doc tu nop_quy chu KHONG tu cong_no: cong_no keo ban_hang keo requests,
	# ma may CI cua GitHub khong cai goi ngoai. Bai hoc PR #2 do 3 ca.
	la("số lẻ đủ hàng", nq.chu_so_tien(1234567),
		"Một triệu hai trăm ba mươi bốn nghìn năm trăm sáu mươi bảy đồng")
	la("mốt và lăm", nq.chu_so_tien(2125000),
		"Hai triệu một trăm hai mươi lăm nghìn đồng")


# =========== v351: bien nhan nop tien theo DIEM BAN va NGAY

# Anh Viet dat 30/08/2026. Duong nay khong can mo ca chot ca, vi kiem tren
# site that cung ngay thi bang ca RONG: ba diem ban chua ai mo ca, nen ca
# man nop quy cu chua ai dung duoc.
#
# So lieu duoi day lay theo mau phieu Lark anh Viet gui: phieu
# 202607290002, doanh thu ngay 28/07/2026 cua diem D1, 7 to 500k, 1 to
# 50k, 1 to 20k, 1 to 10k, 1 to 5k, 2 to 2k, tong 3.589.000.

LARK_BANG_KE = {"500000": 7, "50000": 1, "20000": 1, "10000": 1, "5000": 1, "2000": 2}


@ca("biên nhận: bảng kê của phiếu Lark cộng đúng 3.589.000")
def _():
	bang = nq.doc_bang_ke(LARK_BANG_KE)
	la("tổng thực nhận", nq.tong_bang_ke(bang), 3589000.0)
	la("số dòng có tờ", len(bang), 6)
	la("dòng đầu là mệnh giá lớn nhất", bang[0]["menh_gia"], 500000)
	la("bảy tờ năm trăm", bang[0]["thanh_tien"], 3500000.0)


@ca("biên nhận: mệnh giá lạ và số tờ âm bị chặn thẳng")
def _():
	for xau, mo_ta in ((({"300000": 1}), "mệnh giá không lưu hành"),
			(({"500000": -2}), "số tờ âm")):
		try:
			nq.doc_bang_ke(xau)
			dung("phải chặn %s" % mo_ta, False)
		except ValueError:
			dung("chặn %s" % mo_ta, True)


@ca("biên nhận: đọc ngày chỉ nhận dạng chuẩn, không đoán hộ")
def _():
	la("ngày chuẩn", str(nq.doc_ngay("2026-07-28")), "2026-07-28")
	la("cắt phần giờ", str(nq.doc_ngay("2026-07-28 15:09:00")), "2026-07-28")
	for xau in ("", None, "28/07/2026", "hôm qua"):
		try:
			nq.doc_ngay(xau)
			dung("phải chặn %r" % xau, False)
		except ValueError:
			dung("chặn %r" % xau, True)


@ca("biên nhận: đếm ngày tính cả hai đầu")
def _():
	la("một ngày", nq.dem_ngay("2026-07-28", "2026-07-28"), 1)
	la("một tuần", nq.dem_ngay("2026-07-28", "2026-08-03"), 7)
	la("bắc qua tháng", nq.dem_ngay("2026-07-30", "2026-08-02"), 4)


@ca("biên nhận: phạm vi Một ngày BỎ QUA ô đến ngày còn sót lại")
def _():
	# Nguoi dung chon Khoang ngay, go den ngay, roi doi y ve Mot ngay. Gia
	# tri cu van nam trong o kia. Tin vao no la lap phieu trum sang ngay
	# khong dinh nop, va ngay do coi nhu da nop.
	la("một ngày bỏ qua đến ngày",
		nq.chuan_khoang(nq.PV_NGAY, "2026-07-28", "2026-08-15"),
		("2026-07-28", "2026-07-28", 1))
	la("khoảng ngày thì dùng cả hai ô",
		nq.chuan_khoang(nq.PV_KHOANG, "2026-07-28", "2026-07-30"),
		("2026-07-28", "2026-07-30", 3))


@ca("biên nhận: khoảng ngày ngược và khoảng dài quá đều bị chặn")
def _():
	try:
		nq.chuan_khoang(nq.PV_KHOANG, "2026-07-30", "2026-07-28")
		dung("phải chặn đến ngày sớm hơn từ ngày", False)
	except ValueError:
		dung("chặn đến ngày sớm hơn từ ngày", True)
	try:
		nq.chuan_khoang(nq.PV_KHOANG, "2025-07-28", "2026-07-28")
		dung("phải chặn khoảng một năm", False)
	except ValueError:
		dung("chặn khoảng dài quá, gõ nhầm năm", True)
	try:
		nq.chuan_khoang("Cả tháng", "2026-07-28")
		dung("phải chặn phạm vi lạ", False)
	except ValueError:
		dung("chặn phạm vi lạ", True)


@ca("biên nhận: hai khoảng ngày trùm nhau thì nhận ra")
def _():
	dung("trùng khít", nq.trum_nhau("2026-07-28", "2026-07-28", "2026-07-28", "2026-07-28"))
	dung("nằm trong", nq.trum_nhau("2026-07-27", "2026-07-30", "2026-07-28", "2026-07-28"))
	dung("gối một đầu", nq.trum_nhau("2026-07-27", "2026-07-29", "2026-07-29", "2026-08-02"))
	dung("liền kề mà không chạm", not nq.trum_nhau("2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30"))
	dung("cách xa", not nq.trum_nhau("2026-07-01", "2026-07-02", "2026-08-01", "2026-08-02"))


@ca("biên nhận: bill huỷ và bill tạm tính không được tính vào tiền mặt")
def _():
	dung("bill tiền mặt bình thường",
		nq.la_tien_mat({"vgb_pt_thanh_toan": "Tiền mặt", "grand_total": 100000}))
	dung("bill đã huỷ thì không",
		not nq.la_tien_mat({"vgb_pt_thanh_toan": "Tiền mặt", "vgb_huy": 1}))
	dung("bill tạm tính thì không",
		not nq.la_tien_mat({"vgb_pt_thanh_toan": "Tiền mặt", "vgb_tam_tinh": 1}))
	dung("chuyển khoản thì không",
		not nq.la_tien_mat({"vgb_pt_thanh_toan": "Chuyển khoản"}))
	dung("bill chưa ghi phương thức thì không",
		not nq.la_tien_mat({}))


@ca("biên nhận: gom tiền mặt theo ngày, xếp theo ngày và cộng đúng")
def _():
	rows = [
		{"posting_date": "2026-07-29", "grand_total": 200000, "vgb_pt_thanh_toan": "Tiền mặt"},
		{"posting_date": "2026-07-28", "grand_total": 3589000, "vgb_pt_thanh_toan": "Tiền mặt"},
		{"posting_date": "2026-07-28", "grand_total": 900000, "vgb_pt_thanh_toan": "Chuyển khoản"},
		{"posting_date": "2026-07-28", "grand_total": 500000, "vgb_pt_thanh_toan": "Tiền mặt", "vgb_huy": 1},
	]
	ds, tong = nq.gom_tien_mat(rows)
	la("hai ngày có tiền mặt", len(ds), 2)
	la("ngày cũ đứng trước", ds[0]["ngay"], "2026-07-28")
	la("ngày 28 chỉ tính bill tiền mặt chưa huỷ", ds[0]["tien"], 3589000.0)
	la("đếm đúng số bill", ds[0]["so_bill"], 1)
	la("tổng hai ngày", tong, 3789000.0)
	la("không có bill nào thì rỗng", nq.gom_tien_mat([]), ([], 0))


@ca("biên nhận: ngưỡng bắt lý do lệch dùng chung với tầng ca")
def _():
	la("cùng một ngưỡng", nq.NGUONG_LECH, cq.NGUONG_LECH)
	dung("lệch 1.000đ là phải có lý do", nq.can_ly_do(1000))
	dung("lệch 999đ thì thôi", not nq.can_ly_do(999))
	dung("lệch âm cũng tính", nq.can_ly_do(-2000))


@ca("biên nhận: câu Nội dung nộp tiền gợi theo điểm bán và khoảng ngày")
def _():
	# Anh Viet 31/08/2026 chot cau: "Nop quy tien mat doanh thu cua hang
	# (ten cua hang) tu ngay ... den ngay ...". Cau nay di thang len to bien
	# ban va len so quy, nen phai mang khoang ngay - khong thi hai to cua
	# hai ngay khac nhau doc len y het nhau.
	la("một ngày thì viết ngày đó",
		nq.noi_dung_mac_dinh("District 1", "2026-08-30", "2026-08-30"),
		"Nộp quỹ tiền mặt doanh thu cửa hàng District 1 ngày 30/08/2026")
	la("nhiều ngày thì viết từ đến",
		nq.noi_dung_mac_dinh("District 1", "2026-08-28", "2026-08-30"),
		"Nộp quỹ tiền mặt doanh thu cửa hàng District 1 "
		"từ ngày 28/08/2026 đến ngày 30/08/2026")
	la("không có ngày thì bỏ vế ngày",
		nq.noi_dung_mac_dinh("District 1"),
		"Nộp quỹ tiền mặt doanh thu cửa hàng District 1")
	la("trống tên thì có câu chung",
		nq.noi_dung_mac_dinh(""), "Nộp quỹ tiền mặt doanh thu")
	la("None cũng vậy",
		nq.noi_dung_mac_dinh(None), "Nộp quỹ tiền mặt doanh thu")
	# Ngay hong thi in nguyen, khong doan hộ va cung khong lam vo ham.
	la("ngày hỏng thì in nguyên",
		nq.noi_dung_mac_dinh("D1", "khong-phai-ngay", "khong-phai-ngay"),
		"Nộp quỹ tiền mặt doanh thu cửa hàng D1 ngày khong-phai-ngay")


def _goc_app():
	"""Thư mục gói `vagabond` trong cây mã nguồn. Dùng cho các ca đọc tệp."""
	import os

	return os.path.dirname(os.path.abspath(nq.__file__))


@ca("biên nhận: hai cửa mới phải nạp ban_hang TRONG hàm, không ở đầu tệp")
def _():
	import io
	import os

	p = os.path.join(_goc_app(), "nop_quy.py")
	c = io.open(p, encoding="utf-8").read()
	dau = c.split("# ============================================================ phép THUẦN")[0]
	# `ban_hang` mo dau bang `import requests`, may chay CI cua GitHub tay
	# khong. Nap o dau tep la do ca bo kiem thu tang khung. Da xay ra
	# ngay 20/08/2026 voi day chuyen nop_quy -> cong_no -> ban_hang.
	dung("đầu tệp không nạp ban_hang", "ban_hang" not in dau)
	dung("đầu tệp không nạp diem_ban", "import diem_ban" not in dau)
	dung("có nạp ban_hang trong hàm", "from vagabond.ban_hang import _loc_diem_ban" in c)


@ca("biên nhận: mọi mệnh giá trên màn phải khớp bảng của máy chủ")
def _():
	import io
	import os

	p = os.path.join(_goc_app(), "public", "js", "bep", "39-bien-nhan-tien.js")
	c = io.open(p, encoding="utf-8").read()
	# Man dem thieu mot menh gia la thu ngan khong go duoc so to cua menh
	# gia do, va tien nop thieu di dung bay nhieu.
	for mg in nq.MENH_GIA:
		dung("màn có mệnh giá %s" % mg, str(mg) in c)
	dung("không dùng dấu em dash", "—" not in c and "–" not in c)


@ca("biên nhận: hai đường lập phiếu cùng ghi nguồn kỳ vọng")
def _():
	import io
	import os

	p = os.path.join(_goc_app(), "nop_quy.py")
	c = io.open(p, encoding="utf-8").read()
	# Doc lai mot phieu cu ma khong biet so ky vong tu dau ra thi khong
	# biet tin no toi dau.
	la("hai nguồn, không hơn", sorted([nq.NG_CA, nq.NG_NGAY]),
		sorted(["Ca đã chốt", "Doanh thu tiền mặt theo ngày"]))
	dung("đường ca ghi nguồn", '"nguon_ky_vong": NG_CA' in c)
	dung("đường ngày ghi nguồn", '"nguon_ky_vong": NG_NGAY' in c)
	dung("đường ngày chặn phiếu trùm", "_phieu_trum(" in c)


@ca("biên nhận: ô trạng thái và phạm vi trên doctype khớp hằng số Python")
def _():
	import io
	import json
	import os

	p = os.path.join(_goc_app(), "vagabond", "doctype", "vagabond_nop_quy",
		"vagabond_nop_quy.json")
	d = json.load(io.open(p, encoding="utf-8"))
	o = {f["fieldname"]: f for f in d["fields"]}
	# Frappe kiem gia tri o Select theo dung danh sach options. Lech mot
	# dau thanh la ghi khong vao, ma loi chi lo luc co nguoi bam nut.
	la("phạm vi", o["pham_vi"]["options"].split("\n"), [nq.PV_NGAY, nq.PV_KHOANG])
	la("nguồn kỳ vọng", o["nguon_ky_vong"]["options"].split("\n"), [nq.NG_CA, nq.NG_NGAY])
	la("trạng thái", o["trang_thai"]["options"].split("\n"),
		[nq.TT_NHAP, nq.TT_CHO_KY, nq.TT_DA_NOP])
	for t in ("diem_ban", "tu_ngay", "den_ngay", "so_ngay", "noi_dung",
			"noi_giao_nhan", "anh_minh_chung"):
		dung("doctype có ô %s" % t, t in o)
	la("thứ tự ô khớp danh sách ô",
		[f["fieldname"] for f in d["fields"]], d["field_order"])
