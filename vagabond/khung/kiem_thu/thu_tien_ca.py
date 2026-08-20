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


@ca("số thành chữ kiểu kế toán: 1.234.567 đọc đúng")
def _():
	from vagabond.cong_no import _chu_so_tien

	la("số lẻ đủ hàng", _chu_so_tien(1234567),
		"Một triệu hai trăm ba mươi bốn nghìn năm trăm sáu mươi bảy đồng")
	la("mốt và lăm", _chu_so_tien(2125000),
		"Hai triệu một trăm hai mươi lăm nghìn đồng")
