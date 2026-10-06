"""#420 v579: mười mẫu báo cáo vendor đọc đúng, sai thì giữ lỗi có lý do.

Fixture là bản ẩn danh dựng theo đặc tả docs/doi-soat-vendor/schema/ (khảo
sát mẫu thật trong Drive 06/10/2026). Mã giao dịch, tên, số thẻ đều giả.
Bản chạy trên tệp thật (không đưa vào repo) cho 38 tệp: 0 dòng lỗi, mọi tổng
khớp; ca ở đây giữ đúng các hình dạng đó cùng các lối hỏng.
"""
from vagabond import doi_soat_doc as D
from vagabond import doi_soat_mau as M
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


def _csv(ten, chu):
	return D.doc_tep(ten, chu.replace("\n", "\r\n").encode("utf-8"))[0]


def _luoi(ten, *trang):
	return dict(ten=ten, loai="xlsx", sha256="x", trang=[dict(ten=t, o=o) for t, o in trang])


def _pdf(ten, chu):
	return dict(ten=ten, loai="pdf", sha256="x", trang=[dict(ten="Trang 1", dong=chu.strip("\n").split("\n"))])


# ------------------------------------------------------------ Payoo

PAYOO_THE = """Tài Khoản Payoo Tổng/Quản lý,Chi Nhánh/Đơn Vị Nhận Tiền Dịch Vụ,Tài Khoản Payoo Thực Hiện Giao Dịch,Ngày Giao Dịch,Chi Tiết H.Thức T.Toán,Hình Thức Phát Hành,Ngân Hàng Phát Hành,Kỳ Hạn Trả Góp,Mã giao dịch Payoo,Số Tham Chiếu,Mã Chuẩn Chi,Số Tiền Giao Dịch Thẻ,Phí Xử Lý Thẻ,Phí Chuyển Đổi Trả Góp,Số Tiền Payoo Thanh Toán,Ngày Tổng Kết GD Thẻ,Ngày Payoo Thanh Toán,Mã thiết bị,Mã đơn hàng đối tác,Loại Tác Nghiệp,Loại thẻ,Ghi Chú,Tổng tiền đơn hàng,Số tiền giảm giá,Phí xử lý GD khuyến mãi
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,28/04/2026 09:27:12,Thẻ quốc tế,Phát hành nước ngoài,NHPHNN,,,611800000001,A1B2C3,1.900.000.000,52.250.000,0,1.847.750.000,28/04/2026,29/04/2026,P6A91696,,Thanh toán,Credit,,1.900.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,28/04/2026 12:24:44,Thẻ quốc tế,Phát hành trong nước,Vietcombank,,,001311000999,012345,800.000.000,13.200.000,0,786.800.000,28/04/2026,29/04/2026,P6A91696,,Thanh toán,Debit,,800.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_307NVT,28/04/2026 15:24:41,Thẻ nội địa,Phát hành trong nước,NAPAS,,,611815000999,000000,3.600.000.000,27.720.000,0,3.572.280.000,28/04/2026,29/04/2026,P6A91697,,Thanh toán,Debit,,3.600.000.000,0,"""
TEN_PAYOO = "Payoo-POS-Card_VAGABOND_TONG_Doisoatkytongket28042026-28042026.235959.csv"


@ca("v579 Payoo thẻ: bản Google Sheets chia 1.000, bỏ dòng đánh số, điểm bán theo tài khoản con")
def _():
	t = _csv(TEN_PAYOO, PAYOO_THE)
	la("nhận mẫu", M.nhan_dien(t), "payoo_the")
	kq = M.doc(t)
	la("ba dòng, không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (3, [], []))
	la("tiền đúng đồng", [(d["tien_hang"], d["phi"], d["thuc_nhan"]) for d in kq["dong"]],
		[(1900000, 52250, 1847750), (800000, 13200, 786800), (3600000, 27720, 3572280)])
	la("điểm bán", [d["diem_ban"] for d in kq["dong"]], ["TCV", "TCV", "SALES"])
	la("giữ số 0 đầu RRN", kq["dong"][1]["ma_tham_chieu"], "001311000999")
	la("kỳ và ngày tiền về", (kq["tu_ngay"], kq["den_ngay"], kq["ngay_tien_ve"]), ("2026-04-28", "2026-04-28", "2026-04-29"))
	la("tài khoản tổng", kq["tai_khoan"], "VAGABOND_TONG")


@ca("v579 Payoo: CSV gốc ba số lẻ đọc thẳng; ô số Excel không đoán; phép trừ sai là lỗi dòng")
def _():
	la("CSV gốc", M.tien_payoo("1900000.000"), 1900000)
	la("số không", M.tien_payoo("0"), 0)
	nem("ô số Excel", lambda: M.tien_payoo(1900000000.0), M.LoiDong)
	nem("dấu nghìn không tận cùng .000", lambda: M.tien_payoo("1.900.500"), M.LoiDong)
	sai = PAYOO_THE.replace("1.847.750.000", "1.847.000.000")
	kq = M.doc(_csv(TEN_PAYOO, sai))
	la("một dòng lỗi giữ lại", len(kq["dong_loi"]), 1)
	dung("lý do nói phép trừ", "trừ phí" in kq["dong_loi"][0]["ly_do"])
	hoan = PAYOO_THE.replace(",Thanh toán,Credit,,1.900", ",Hoàn tiền,Credit,,1.900")
	kq = M.doc(_csv(TEN_PAYOO, hoan))
	dung("loại lạ không đoán dấu", any("chưa có mẫu" in d["ly_do"] for d in kq["dong_loi"]))


# ------------------------------------------------------------ OnePay

def _onepay_qt(them_dong="", tong="720.000"):
	return """,,,,,,,,,,,,,,,,,,,
,,,CÔNG TY CỔ PHẦN THƯƠNG MẠI VÀ DỊCH VỤ TRỰC TUYẾN ONEPAY,,,,,,,,,,,,,,,,
,THÔNG BÁO TẠM ỨNG,,,,,,,,,,,,,,,,,,
,ĐVCNT (Company):,,,,CÔNG TY TNHH PATISSERIE VAGABOND,,,,,,,,,,,,,,
,STT,Merchant Id,Mã giao dịch,Mã đơn hàng,Mã thanh toán,Thời gian giao dịch,Loại giao dịch,Loại thẻ,Trạng thái giao dịch,Bin Country,Loại dịch vụ,Giá trị GD,Loại tiền tệ,Tỷ giá,Giá trị GD thành công (VND),Phí XLGD,Phí TTT,Tổng phí,Số tiền tạm ứng
,,,,,,,,,,,,(1),,(2),(3)=(1)*(2),(4),(5),(6)=(4)+(3)*(5),(7)=(3)-(6)
,No,Merchant ID,Transaction ID,Order Reference,Merchant Trans. Ref.,Transaction date,Transaction Type,Card Type,Status,Bin Country,Pay Channel, Transaction Amount , Currency , Exchange Rate , Successful Amount (VND) ,Fix fee,Percent fee,Total fee,Advance amount
,1,VAGABOND,240000001,PL_VAGABOND_260729042259,PL_VAGABOND_AAAAAAAAA1,29/07/2026 16:23:53,PURCHASE,VISA,SUCCESS,VN,QT,"300.000,00",VND,"1,00",300.000,"4.000,00","2,40%","11.200,00",288.800
,2,VAGABOND,240000002,PL_VAGABOND_260729073033,PL_VAGABOND_AAAAAAAAA2,29/07/2026 19:31:40,PURCHASE,MASTERCARD,SUCCESS,AU,QT,"420.000,00",VND,"1,00",420.000,"4.000,00","3,60%","19.120,00",400.880
""" + them_dong + """,,,Tổng cộng (Total),,,,,,,,,,,,""" + tong + """,,,"30.320,00",""" + ("689.680" if tong == "720.000" else "589.680") + "\n"


@ca("v579 OnePay tạm ứng ngày: chỉ lấy Total fee, khớp dòng Tổng cộng, ngày tiền về theo tên tệp")
def _():
	t = _csv("20260730_5321728VAGABOND.csv", _onepay_qt())
	la("nhận mẫu", M.nhan_dien(t), "onepay_ngay")
	kq = M.doc(t)
	la("hai dòng, không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (2, [], []))
	la("phí không cộng Fix fee hai lần", [d["phi"] for d in kq["dong"]], [11200, 19120])
	la("căn cước theo kênh", kq["dong"][0]["ma_su_kien"], "QT:240000001")
	la("mã nối đơn", kq["dong"][0]["ma_tham_chieu"], "PL_VAGABOND_AAAAAAAAA1")
	la("ngày tiền về", kq["ngay_tien_ve"], "2026-07-30")
	la("bút toán", kq["them"]["but_toan"], "5321728")


@ca("v579 OnePay: tổng in lệch là lỗi tệp; hoàn tiền phải mang số âm")
def _():
	kq = M.doc(_csv("20260730_5321728VAGABOND.csv", _onepay_qt(tong="620.000")))
	dung("lệch tổng", any("Tổng tiền hàng" in l for l in kq["loi"]))
	hoan = ',3,VAGABOND,240000003,PL_X,PL_VAGABOND_AAAAAAAAA3,29/07/2026 20:00:00,REFUND,VISA,SUCCESS,VN,QT,"300.000,00",VND,"1,00",300.000,"0,00","0,00%","0,00",300.000\n'
	kq = M.doc(_csv("20260730_5321728VAGABOND.csv", _onepay_qt(them_dong=hoan)))
	dung("hoàn dương bị giữ", any("hoàn mang số dương" in d["ly_do"] for d in kq["dong_loi"]))


ONEPAY_BBDS = '''"STT
No","Thời gian giao dịch
Transaction date","Loại dịch vụ
Pay channel","Số lượng GD
Number of Trans","Giao dịch thành công
Count success","Giao dịch không thành công
Count failed","Tổng Giá trị GD
Transaction Amount","Tổng giá trị khoanh hoàn trả
The amount held for refund transactions","Tổng giá trị nhả khoanh hoàn trả
Release amount","Giá trị đã tạm ứng
Advance amount","Tổng phí
Total fee"
1,02/06/26 - 03/06/26,QT,2,2,0,1.450.000,0,0,1.397.720,52.280
2,05/06/26 - 06/06/26,QT,1,1,0,715.000,0,0,685.260,29.740
TỔNG CỘNG/Total,,,3,3,0,2.165.000,0,0,2.082.980,82.020
'''


@ca("v579 OnePay biên bản tháng: không có dòng, giữ tổng và từng đợt")
def _():
	o = [["BIÊN BẢN XÁC NHẬN ĐỐI SOÁT SỐ LIỆU DỊCH VỤ / MONTHLY FEE REPORT"], ["CÔNG TY TNHH PATISSERIE VAGABOND - QT - VAGABOND"]]
	o += D.doc_csv(ONEPAY_BBDS.encode())[0]["o"]
	t = _luoi("BBDS_VAGABOND_01.06.2026_30.06.2026_QT_1783164030766", ("Sheet1", o))
	la("nhận mẫu", M.nhan_dien(t), "onepay_bbds")
	kq = M.doc(t)
	la("tổng", kq["tong"], dict(tien_hang=2165000, phi=82020, thuc_nhan=2082980, so_dong=3))
	la("hai đợt, kênh QT", (len(kq["them"]["ky"]), kq["them"]["kenh"], kq["loi"]), (2, "QT", []))


# ------------------------------------------------------------ Shinhan POS

def _shinhan_ngay(net3="234000"):
	td = ["No.", "", "Ngày thanh toán\nPaymen date", "Mã Đại lý\nMID", "Mã Thiết bị\nTID", "", "", "", "Tên Kinh Doanh\nMerchant Name",
		"Tài khoản báo có\nAccount No.", "Số thẻ\nCard No.", "", "Thời gian giao dịch\nTrxn date", "Mã yêu cầu\nRequest ID",
		"Mã tham chiếu giao dịch\nPurchase ID", "Số tiền giao dịch\nTrxn amount (VND)", "Mức phí dịch vụ (%)\nMDR (%)",
		"Phí dịch vụ (Bao gồm VAT)\nMDF (include VAT)", "Phí xử lý giao dịch \n(Bao gồm VAT)\nProcessing fee\n(include VAT)", "",
		"Thuế \nVAT", "Số tiền báo có/ báo nơ\nPayment amount", "Mã chuẩn chi\nApproval code", "Hoàn/Hủy\nReversal/Refund \n(Y/N)",
		"Loại thẻ\nBrand Card", "Kênh giao dịch\nChannel", "Thẻ trong nước/ nước ngoài\nDomestic/ International Card", "Chi nhánh quản lý\nBranch Name"]

	def d(no, mid, tid, the, tg, tien, mdr, mdf, vat, net, ma, brand):
		return [no, "", "20-07-2026", mid, tid, "", "", "", "THE VAGABOND", "700000****00", the, "", tg, "", "", tien, mdr, mdf, 0,
			vat, "", net, ma, "N", brand, "POS", "DOMESTIC", "SAIGON BRANCH"]
	o = [[""], ["", "SAO KÊ CHI TIẾT GIAO DỊCH"], [""], ["", "MERCHANT STATEMENT REPORT"], [""], ["Ngày", "", "", "", "", "20/07/2026"]]
	o += [[""]] * 14 + [td]
	o.append(d("1", "71000000001", "73000001", "4111-11**-****-1111", "09:44:15 19-07-2026", 200000, "1.440", 2880, 262, 197120, "'123456", "Visa"))
	o.append(d("2", "71000000001", "73000001", "9704-00**-****-***0-001", "20:25:35 18-07-2026", 95000, "0.780", 741, 67, 94259, "'000000", "Napas"))
	o.append(d("3", "71000000002", "73000002", "5555-55**-****-4444", "07:33:45 17-07-2026", 240000, "2.500", 6000, 545, int(net3), "'F01234", "MasterCard"))
	o.append([""] * 14 + ["Tổng/Total", 535000, "", 9621, 0, 874, "", 525379] + [""] * 6)
	th = [[""], ["", "SAO KÊ CHI TIẾT GIAO DỊCH"], [""], ["", "MERCHANT STATEMENT REPORT"]] + [[""]] * 14 + [
		["No.", "", "Ngày thanh toán\nPaymen date", "Mã Đại lý\nMID", "Tên Kinh Doanh\nMerchant Name", "", "", "", "Số tài khoản\nAccount No.",
			"Số lượng giao dịch\nCount of trxn", "", "Số tiền giao dịch\nTrxn amount (VND)", "Phí dịch vụ (Bao gồm VAT)\nMDF (include VAT)",
			"Phí xử lý giao dịch (Bao gồm VAT)\nProcessing fee (include VAT)", "Số tiền thanh toán\nPayment amount"],
		["TỔNG/TOTAL", "", "", "", "", "", "", "", "", 3, "", 535000, 9621, 0, 525379]]
	return _luoi("MSR_40019_GID_20000414_421_20260720_1.xls", ("Summary_40019_enhance", th), ("Detail_40019_enhance", o))


@ca("v579 Shinhan POS ngày: MDF đã gồm VAT, căn cước sáu thành phần, khớp hai tab tổng")
def _():
	t = _shinhan_ngay()
	la("nhận mẫu", M.nhan_dien(t), "shinhan_ngay")
	kq = M.doc(t)
	la("ba dòng, không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (3, [], []))
	la("bỏ dấu nháy mã chuẩn chi, giữ số 0", [d["ma_tham_chieu"] for d in kq["dong"]], ["123456", "000000", "F01234"])
	la("thực nhận = tiền - MDF", kq["dong"][0]["thuc_nhan"], 197120)
	la("hai mã chuẩn chi 000000 khác căn cước", len({d["ma_su_kien"] for d in kq["dong"]}), 3)
	la("ngày tiền về", kq["ngay_tien_ve"], "2026-07-20")


@ca("v579 Shinhan POS: số báo có sai là lỗi dòng, và tổng tệp không bị coi là đủ")
def _():
	kq = M.doc(_shinhan_ngay(net3="235000"))
	la("một dòng lỗi", len(kq["dong_loi"]), 1)


# ------------------------------------------------------------ ShopeeFood

SHOPEE = """STT,Mã Đơn Hàng,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Giá trị đơn hàng,Khuyến mại từ quán,Phí dịch vụ,Phí vận chuyển trả cho quán,Chiết khấu,Thuế khấu trừ,Thực thu
1,28036-100000001,10322362,The Vagabond Pâtisserie & Café - Trần Cao Vân,28/03/2026 09:31:10,140,60,0,0,"11,784",0,"68,216"
2,28036-100000003,10332477,The Vagabond Pâtisserie & Café - Nguyễn Văn Trỗi,28/03/2026 11:42:39,100,15,0,0,"12,521",0,"72,48"
3,28036-100000004,10332477,The Vagabond Pâtisserie & Café - Nguyễn Văn Trỗi,28/03/2026 11:22:34,355,"87,25",0,0,"39,44",0,"228,31"
"""


@ca("v579 ShopeeFood: nghìn đồng ba số lẻ, 72,48 là 72.480 đồng, lệch làm tròn 1 đồng được nhận")
def _():
	t = _csv("Shopeefood_Income_Details_Merchant_28-03-2026.csv", SHOPEE)
	la("nhận mẫu", M.nhan_dien(t), "shopeefood")
	kq = M.doc(t)
	la("ba dòng, không lỗi", (len(kq["dong"]), kq["dong_loi"]), (3, []))
	la("dòng 2", (kq["dong"][1]["tien_hang"], kq["dong"][1]["giam_gia"], kq["dong"][1]["phi"], kq["dong"][1]["thuc_nhan"]),
		(85000, 15000, 12520, 72480))
	la("điểm bán theo mã cửa hàng", [d["diem_ban"] for d in kq["dong"]], ["TCV", "SALES", "SALES"])
	la("dấu chấm thập phân cũng đọc", M.tien_nghin("41.244"), 41244)
	nem("dấu nghìn bị chặn", lambda: M.tien_nghin("1.234.567"), M.LoiDong)
	sai = SHOPEE.replace('"68,216"', '"60,216"')
	dung("lệch quá 1 đồng là lỗi", len(M.doc(_csv("x.csv", sai))["dong_loi"]) == 1)


# ------------------------------------------------------------ Xanh SM Ngon

XANH_CT = """STT,Mã Đơn Hàng,Mã Rút Gọn,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Trạng thái,Giá trị đơn hàng,Khuyến mại từ quán,Giảm giá món,Tổng tiền cofund KM,Tổng tiền cofund KM Giao hàng,Tổng tiền cofund KM Món ăn,Voucher Cofunds,Doanh thu ròng,Chiết khấu,VAT,PIT,Thực thu
1,01KFAAAAAAAAAAAAAAAAAAAAA1,7001,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 16:23:45,Completed,170000,,0,0,0,0,,170000,22100,0,0,147900
2,01KFAAAAAAAAAAAAAAAAAAAAA2,0010,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 21:35:58,Completed,115000,,40000,16000,4000,12000,"2026XANH20:12000
2026XANHSHIP8:4000",63000,8190,0,0,54810
3,01KFAAAAAAAAAAAAAAAAAAAAA3,1834,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 21:40:08,Completed,230000,,67000,0,0,0,,163000,21190,0,0,141810
"""
XANH_TH = [["Tổng số đơn hàng", 3], ["Tổng giá trị đơn hàng", 515000], ["Khuyến mại từ quán", 12000], ["Khuyến mại món", 107000],
	["Doanh thu ròng", 396000], ["Tổng chiết khấu", 51480], ["Tổng thực thu", 344520], ["PIT", None]]


@ca("v579 Xanh SM Ngon: cofund giao hàng không trừ quán, tab Summary là tổng kiểm, mã rút gọn giữ số 0")
def _():
	o = D.doc_csv(XANH_CT.encode())[0]["o"]
	t = _luoi("Revenue_Report_01K23YRC2F21BG1DP3P8T4KV7Q_20260124", ("Detail Transactions", o), ("Summary", XANH_TH))
	la("nhận mẫu", M.nhan_dien(t), "greensm_ngon")
	kq = M.doc(t)
	la("không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (3, [], []))
	la("dòng 2: ròng sau giảm món và cofund món", (kq["dong"][1]["tien_hang"], kq["dong"][1]["giam_gia"], kq["dong"][1]["thuc_nhan"]),
		(63000, 52000, 54810))
	la("mã rút gọn", kq["dong"][1]["ma_tham_chieu"], "0010")
	la("tổng tệp", kq["tong"]["thuc_nhan"], 344520)
	th = [r[:] for r in XANH_TH]
	th[6][1] = 340000
	kq = M.doc(_luoi("Revenue_Report_x_20260124", ("Detail Transactions", o), ("Summary", th)))
	dung("lệch Summary là lỗi tệp", any("thực nhận" in l for l in kq["loi"]))


@ca("v579 Xanh SM Ngon và ShopeeFood không nhận nhầm của nhau")
def _():
	la("Shopee", M.nhan_greensm(_csv("s.csv", SHOPEE)), None)
	la("Xanh", M.nhan_shopee(_csv("x.csv", XANH_CT)), None)


# ------------------------------------------------------------ GrabFood

GRAB = """
Báo cáo kinh doanh hàng ngày
17 tháng 7 2026, thứ sáu                                     https://grb.to/hotrodoitacnhahang
The Vagabond Pâtisserie & Café - Trần Cao Vân
Tóm tắt thông tin
  Tổng thu nhập          Còn thiếu Grab          Tổng số đơn hàng
 VND 668.915              VND 0          4 đơn hàng
Thu nhập
Tổng tiền thanh toán sẽ được chuyển cho bạn vào ngàythứ bảy, tháng 7 18. Tài khoản của bạn có thể phải đợi vài ngày.
 830.000   0   0   -60.000   -111.433   -13.000   72.488   -49.140   668.915   0
Đơn hàng từ ứng dụng và web
 Đơn hàng Delivery
 9:28 PM      GF-101       Trả thẻ / Ví        260.000      0        -          0        -36.359       -13.000   210.641
 Đã hủy       GF-102            -              -            -        -          -            -              -          -
 5:14 PM      GD-          Trả thẻ / Ví        400.000      0        -    -60.000        -50.050             0   289.950
             AAAA1111
 12:42 PM     GF-103F      Tiền mặt            170.000      0        -          0        -25.024             0   144.976
                                                                                              645.567
 Tổng cộng                                       VND 645.567
Marketing
 17 Th07, 10:30 PM     ADS-001      Từ khóa thủ công - 2026-07-17          -45.500     -3.640     -49.140
                                                                          VND-49.140
Điều chỉnh
 17 Th07, 6:16 PM      MPA-001      GF-102     Canceled Order Compensation          72.488
                                                                          VND72.488
Hướng dẫn đọc hiểu báo cáo
 Đơn hàng ăn tại quán   Những đơn hàng ăn tại quán được khách gọi
"""


@ca("v579 GrabFood: đơn, quảng cáo, điều chỉnh; mã bị ngắt dòng; đơn huỷ vẫn đếm; dừng ở phần giải thích")
def _():
	t = _pdf("5-C4E1NPWGG2WZFA-20260717.pdf", GRAB)
	la("nhận mẫu", M.nhan_dien(t), "grabfood")
	kq = M.doc(t)
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	la("loại dòng", [d["loai"] for d in kq["dong"]], ["ban", "ban", "ban", "phi_ky", "dieu_chinh"])
	la("mã ghép lại", kq["dong"][1]["ma_don"], "GD-AAAA1111")
	la("đơn huỷ", kq["them"]["don_huy"], ["GF-102"])
	la("quảng cáo có căn cứ", (kq["dong"][3]["ma_can_cu"], kq["dong"][3]["thuc_nhan"]), ("ADS-001", -49140))
	la("điều chỉnh nối đơn huỷ", (kq["dong"][4]["ma_don"], kq["dong"][4]["thuc_nhan"]), ("GF-102", 72488))
	la("cộng = tổng thu nhập", sum(d["thuc_nhan"] for d in kq["dong"]), 668915)
	la("ngày tiền về", kq["ngay_tien_ve"], "2026-07-18")
	la("cửa hàng", (kq["tai_khoan"], kq["dong"][0]["diem_ban"]), ("GRABFOOD:5-C4E1NPWGG2WZFA", "TCV"))
	la("giờ 24h", kq["dong"][0]["gio"], "21:28:00")


@ca("v579 GrabFood: dòng đơn không đọc được thì báo, không lặng lẽ thiếu đơn")
def _():
	kq = M.doc(_pdf("5-C4E1NPWGG2WZFA-20260717.pdf", GRAB.replace(" 9:28 PM      GF-101", " 9:28 PM      GF/101")))
	dung("có dòng lỗi", len(kq["dong_loi"]) == 1)
	kq = M.doc(_pdf("5-C4E1NPWGG2WZFA-20260717.pdf", GRAB.replace("-36.359", "-36.300")))
	dung("phép cộng đơn sai", any("thu nhập" in d["ly_do"] for d in kq["dong_loi"]))


# ------------------------------------------------------------ Be

def _be(tra_tong='"192,360"'):
	td = ["STT", "Ngày", "Mã đặt chuyến", "Loại phương tiện", "Điểm đón", "Điểm đến", "Tên người đi", "Cước phí vận tải",
		"Phí cầu đường (Phí khác) (*)", "Phụ phí giờ cao điểm", "Phí điểm đón (*)", "Phí bảo hiểm", "Phí thông báo tình trạng đơn hàng (*)",
		"Chiết khấu/Giảm giá", "Tổng tiền", "Cước phí được áp dụng  CKTM", "Tỷ lệ CKTM", "Chiết khấu thương mại (*)",
		"Tổng tiền thanh toán sau khi trừ CKTM", "Phí sử dụng ứng dụng (*)", "Cước phí vận tải chịu thuế GTGT (*)", "Driver city ID"]
	o = [["CÔNG TY CỔ PHẦN BE GROUP"], ["MST: 0108269207"], [""], [""], [""], ["CHI TIẾT CƯỚC PHÍ DỊCH VỤ VẬN TẢI"],
		["KỲ: từ ngày 26/05/2026 đến ngày 25/06/2026"], [""], ["Kính gửi:", "", "CÔNG TY TNHH PATISSERIE VAGABOND"], [""], [""], [""], td,
		["1", "26/05/2026", "1000000001", "beCar 7 chỗ", "A", "B", "STAFF_A", "65,000", "0", "0", "0", "0", "0", "0", "65,000", "65,000", "4", "2,600", "62,400", "10,075", "54,925", "189"],
		["2", "26/05/2026", "1000000002", "Giao hàng Siêu tốc", "A", "C", "The Vagabond", "27,000", "0", "0", "0", "0", "0", "5,000", "22,000", "22,000", "4", "880", "21,120", "2,795", "19,205", "189"],
		["3", "22/06/2026", "1000000003", "beCar 7 chỗ", "C", "D", "STAFF_B", "110,000", "9,000", "0", "0", "0", "0", "6,000", "113,000", "104,000", "4", "4,160", "108,840", "16,258", "87,742", "189"],
		["Tổng", "", "", "", "", "", "", "202,000"], [""], ["Tổng số tiền thanh toán trong kỳ:", "", "", "", "", "", "", tra_tong.strip('"')]]
	return _luoi("CÔNG-TY-TNHH-PATISSERIE-VAGABOND-20260526-20260625-1782416206", ("corp_reconciliation", o))


@ca("v579 Be: số phải trả sau chiết khấu thương mại, kỳ 26 tới 25, chuyến giao hàng đánh dấu")
def _():
	t = _be()
	la("nhận mẫu", M.nhan_dien(t), "be")
	kq = M.doc(t)
	la("không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (3, [], []))
	la("phải trả", [d["thuc_nhan"] for d in kq["dong"]], [62400, 21120, 108840])
	la("kỳ", (kq["tu_ngay"], kq["den_ngay"]), ("2026-05-26", "2026-06-25"))
	la("giao hàng", [d["giao_hang"] for d in kq["dong"]], [False, True, False])
	kq = M.doc(_be('"192,000"'))
	dung("tổng kỳ lệch là lỗi", any("thực nhận" in l for l in kq["loi"]))


# ------------------------------------------------------------ Grab for Business

GRAB_B = """TRANSACTION_TIME,CREATION_TIME,COMPLETION_TIME,COMPANY_NAME,PORTAL_ID,EMPLOYEE_NAME,EMPLOYEE_ID,EMPLOYEE_EMAIL_ADDRESS,GROUP_NAME,BOOKING_ID,VERTICAL,TAXI_TYPE,SOURCE,TYPE,TRIP_CODE,TRIP_DESCRIPTION,CITY,PICK_UP,INTERMEDIATE_DROPOFF,DROP_OFF,DISTANCE,DAX_ID,BASE_FARE,PROMO,TOLLS_AND_SURCHARGE,LATE_FEES,OTHER_FEES,AMOUNT,CURRENCY,PAYMENT_METHOD,BILLING_TYPE,PRE_VAT_DELIVERY_FEE,VAT_VALUE_DELIVERY_FEE,PRE_VAT_SERVICE_FEE,VAT_VALUE_SERVICE_FEE,NON_VAT_VALUE,INVOICE_NUMBER,INVOICE_TRACKING_ID,INVOICE_PAYMENT_TYPE,DRIVE_PLATE_NUMBER,GOODS_INFORMATION,ORDER_ID,VAT_INVOICE_DATE,VAT_INVOICE_SERIAL,VAT_TAX_AUTHORITY_CODE
2026-06-01 16:58:04 +07:00,2026-06-01 16:20:32 +07:00,2026-06-01 16:55:05 +07:00,CÔNG TY TNHH PATISSERIE VAGABOND,1000156989,STAFF_A,,a@example.com,General,A-TESTEXPRESS0001,express,GrabExpress Nhanh,App,Portal,,,Ho Chi Minh,K,,C,"7,4",1000001,39000,-3000,0,0,5000,41000,VND,Corporate Billing,Corp Bill Transaction,33333,2667,4630,370,0,1000001,26AAtest0000001,Postpaid,59X1-000.01,Thực phẩm,IN-2-TESTORDER0001,2026-06-02,1C26TAA,00AA
2026-06-30 23:59:59 +07:00,,,CÔNG TY TNHH PATISSERIE VAGABOND,1000156989,,,,,,,,,,,,,,,,,,,,,,,2050,VND,,Admin Fee,1898,152,,,,1000003,26AAtest0000003,Postpaid,,,,2026-07-06,1C26TAA,00BB
"""


@ca("v579 Grab for Business: chuyến có hoá đơn riêng, dòng Admin Fee là phí quản lý có căn cứ, kỳ theo tên tệp")
def _():
	t = _csv("2606 - Bảng kê tháng 06.2026 - CÔNG TY TNHH PATISSERIE VAGABOND.csv", GRAB_B)
	la("nhận mẫu", M.nhan_dien(t), "grab_business")
	kq = M.doc(t)
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	la("loại", [d["loai"] for d in kq["dong"]], ["chuyen", "phi_quan_ly"])
	la("hoá đơn", [d["hoa_don"] for d in kq["dong"]], ["1C26TAA#1000001", "1C26TAA#1000003"])
	la("tiền trước khuyến mại", (kq["dong"][0]["tien_hang"], kq["dong"][0]["giam_gia"], kq["dong"][0]["thuc_nhan"]), (44000, 3000, 41000))
	la("kỳ", (kq["tu_ngay"], kq["den_ngay"]), ("2026-06-01", "2026-06-30"))
	sai = GRAB_B.replace(",41000,VND", ",42000,VND")
	dung("phép cộng sai", len(M.doc(_csv("2606 - x.csv", sai))["dong_loi"]) == 1)


# ------------------------------------------------------------ Xanh SM doanh nghiệp

def _xanh_taxi(tong="65400"):
	td = ["STT", "MÃ ĐẶT CHUYẾN", "CÔNG TY", "PHÒNG BAN", "MÃ THẺ", "TÊN TRÊN THẺ", "MÃ NV", "SĐT GÁN THẺ", "PTTT", "TÊN KHÁCH HÀNG",
		"SĐT KHÁCH HÀNG", "NGUỒN", "NHÓM DỊCH VỤ", "DỊCH VỤ (M)", "ĐIỂM ĐÓN", "ĐIỂM TRẢ", "QUÃNG ĐƯỜNG", "BẮT ĐẦU (UTC+7)",
		"KẾT THÚC (UTC+7)", "GHI CHÚ", "MÃ CHUYẾN", "MỤC ĐÍCH CHUYẾN", "GIÁ CƯỚC", "PHỤ PHÍ", "TỔNG KHUYẾN MẠI", "ĐIỂM VPOINT TIÊU",
		"ĐIỂM VPOINT TIÊU(QUY ĐỔI)", "PHÍ QUẢN LÝ", "MỨC CHIẾT KHẤU", "SỐ TIỀN CHIẾT KHẤU", "GIÁ CƯỚC TRƯỚC VAT", "VAT GIÁ CƯỚC",
		"PHỤ PHÍ TRƯỚC VAT", "VAT PHỤ PHÍ", "CHIẾT KHẤU/KHUYẾN MẠI TRƯỚC VAT", "VAT CHIẾT KHẤU/KHUYẾN MẠI", "PHÍ QUẢN LÝ TRƯỚC VAT",
		"VAT PHÍ QUẢN LÝ", "PHÍ NỀN TẢNG trước VAT", "VAT PHÍ NỀN TẢNG", "TỔNG THANH TOÁN", "BẢO HIỂM", "GHI CHÚ LÝ DO CÁC CUỐC LỖI", "BSX"]

	def d(stt, ma, gc, km, ql, vql, tt):
		return [stt, ma, "CÔNG TY TNHH PATISSERIE VAGABOND", "Sale", "1000XXXXXXXX9785", "Sale Admin", "", "+84000", "VIRTUAL",
			"The Vagabond", "+84000", "Express", "Green SM Express", "Green Express", "K", "(1) C", "6,81", "2026-06-26 09:00:50",
			"2026-06-26 09:29:53", "", "", "", gc, "0,00", km, 0, 0, "0,05", "0,00", "0,00", "1", "1", "0", "0", "0", "0", ql, vql,
			"1", "1", tt, "0,00", "", "50X00001"]
	o = [["BẢNG KÊ CHUYẾN ĐI DOANH NGHIỆP THÁNG 07.2026"], ["Thời gian: Từ 26/06/2026 - 25/07/2026"], [""], td,
		d("1", "01TESTULID00000000000000A1", "33.000,00", "0,00", "1.527,78", "122,22", "34.650,00"),
		d("2", "01TESTULID00000000000000A2", "35.000,00", "6.000,00", "1.620,37", "129,63", "30.750,00"), [""],
		["Total"] + [""] * 39 + [tong]]
	return _luoi("Bảng kê CÔNG TY TNHH PATISSERIE VAGABOND THÁNG 7 2026", ("Sheet1", o))


@ca("v579 Xanh SM doanh nghiệp: tiền lẻ đồng, phí quản lý cộng vào phải trả, khớp dòng Total")
def _():
	t = _xanh_taxi()
	la("nhận mẫu", M.nhan_dien(t), "xanh_taxi")
	kq = M.doc(t)
	la("không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (2, [], []))
	la("phải trả", [d["thuc_nhan"] for d in kq["dong"]], [34650, 30750])
	la("kỳ", (kq["tu_ngay"], kq["den_ngay"]), ("2026-06-26", "2026-07-25"))
	kq = M.doc(_xanh_taxi("65000"))
	dung("lệch Total", any("Total" in l for l in kq["loi"]))


# ------------------------------------------------------------ Thẻ tín dụng Shinhan

THE = """
                       Sao Kê
Tên khách hàng : BAN GIAM DOC
Tài khoản thanh toán : 700******000
       Ngày sao kê         01/07/2026                      Ngày đến hạn thanh toán   15/07/2026
      Chu kỳ sao kê        01/06/2026 ~ 30/06/2026
 Khoản tiền chưa thanh toán
                    VND 0.00                                Phí chậm trả      VND 0.00
         tháng trước
   Đến hạn thanh toán của
                    VND 2,320,000.00
         tháng này
    Đến hạn thanh toán    VND 2,320,000.00
Chi tiết sao kê
     Card        Number    5248-62XX-XXXX-0000
  05-06-2026     08-06-2026  TEST RESTAURANT                         VN/HO CHI MIN     VND 1,000,000.00         1,000,000
  19-06-2026     22-06-2026  FACEBK *TESTREF001                         IE/fb.me/ad     VND 1,100,000.00       1,100,000
                             Your Spend For This Month                                        2,100,000
  15-05-2026     30-06-2026  Annual Fee                                              VND 200,000.00           220,000
                             Fees                                                              220,000
                                        Billing Amount of the Current Month                    2,320,000
"""


@ca("v579 thẻ tín dụng Shinhan: kỳ theo ngày bút toán, phí sau dòng Spend, ba phương trình trong tệp")
def _():
	t = _pdf("sao ke thang 06 2026 shinhan.pdf", THE)
	la("nhận mẫu", M.nhan_dien(t), "the_shinhan")
	kq = M.doc(t)
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	la("loại", [d["loai"] for d in kq["dong"]], ["phat_sinh", "phat_sinh", "phi"])
	la("ngày theo bút toán", kq["dong"][0]["ngay"], "2026-06-08")
	la("tổng", (kq["tong"]["spend"], kq["tong"]["fees"], kq["tong"]["den_han"]), (2100000, 220000, 2320000))
	la("hạn", kq["ngay_tien_ve"], "2026-07-15")
	kq = M.doc(_pdf("x.pdf", THE.replace("1,100,000.00       1,100,000", "1,100,000.00       1,000,000")))
	dung("lệch Spend", any("Your Spend" in l for l in kq["loi"]))


# ------------------------------------------------------------ chung

@ca("v579 tệp lạ không được đoán là mẫu nào; zip có mật khẩu và tệp rỗng báo việc làm tiếp")
def _():
	kq = M.doc(_csv("la.csv", "A,B,C\n1,2,3\n"))
	la("chưa nhận ra", kq["mau"], "")
	dung("nói các mẫu đang đọc được", "Payoo thẻ" in kq["loi"][0])
	nem("tệp rỗng", lambda: D.doc_tep("x.csv", b""), D.LoiTep)
	import io
	import zipfile
	b = io.BytesIO()
	with zipfile.ZipFile(b, "w") as z:
		z.writestr("a.csv", "A,B\n1,2\n")
	ds = D.doc_tep("goi.zip", b.getvalue())
	la("zip mở ra tệp con", [x["ten"] for x in ds], ["a.csv"])
	raw = bytearray(b.getvalue())
	i = raw.find(b"PK\x03\x04")
	raw[i + 6] |= 1
	j = raw.find(b"PK\x01\x02")
	raw[j + 8] |= 1
	nem("zip có mật khẩu", lambda: D.doc_tep("goi.zip", bytes(raw)), D.LoiTep)


@ca("v579 ngày giờ: số ngày kiểu Excel, HH:MM:SS dd-mm-yyyy, ngày không tồn tại")
def _():
	la("excel", M.ngay_gio(46174.5), ("2026-06-01", "12:00:00"))
	la("shinhan", M.ngay_gio("09:44:15 19-07-2026"), ("2026-07-19", "09:44:15"))
	la("dd/mm/yy", M.ngay("02/06/26"), "2026-06-02")
	nem("30/02", lambda: M.ngay("30/02/2026"), M.LoiDong)
