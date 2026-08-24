"""Kiem thu v296: gia don Pancake va ten phap nhan tren hoa don VAT.

Hai su co that trong cung mot ngay 22/08/2026, ca hai deu im lang tuyet doi
cho toi luc khach keu len.

SU CO MOT - gia don Pancake
    Don 91853. Pancake gui `discount_each_product = 5` kem co
    `is_discount_percent = true`, y la giam 5 PHAN TRAM. May doc thieu co
    nen tru 5 DONG. Phieu ghi 8.229.970, khach chuyen 7.820.000.
    Quet 2.623 don tu 01/07 den 24/08 thi co 6 don dinh.

SU CO HAI - ten phap nhan cut
    Don 92409, ma so thue 0108903529. Cong thong tin thue tra ve dung ba
    chu "CÔNG TY CỔ PHẦN". To hoa don so 10901 ra doi mang ten do, da ky,
    da gui co quan thue. Khach khieu nai, ke toan phai lap bien ban va xuat
    to thay the.

Cac ca duoi day deu lay so THAT tu hai su co do, khong bia so tron.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

from vagabond import gia_pancake, hoa_don_vat

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten, thu_muc=GOI):
	p = os.path.join(thu_muc, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


# ------------------------------------------------------- gia don Pancake

@ca("đơn 91853 thật: giảm 5 phần trăm chứ không phải 5 đồng")
def _():
	# Hai dong hang that cua don 91853, chep nguyen tu API Pancake.
	lapis = {"discount_each_product": 5, "is_discount_percent": True, "quantity": 2}
	garden = {"discount_each_product": 5, "is_discount_percent": True, "quantity": 4}
	ship = {"discount_each_product": 0, "is_discount_percent": False, "quantity": 1}

	la("hộp MOONLAPIS", gia_pancake.gia_mot_don_vi(2200000, lapis), 2090000.0)
	la("hộp MOONGARDEN", gia_pancake.gia_mot_don_vi(950000, garden), 902500.0)
	la("phí giao không giảm", gia_pancake.gia_mot_don_vi(30000, ship), 30000.0)

	tong = 2090000.0 * 2 + 902500.0 * 4 + 30000.0
	# 7.820.000 la so tien khach chuyen that, doc duoc trong sao ke SePay.
	la("tổng đơn khớp số khách đã chuyển", tong, 7820000.0)


@ca("không có cờ phần trăm thì con số vẫn là đồng, không đổi nghĩa sau lưng")
def _():
	# Don cu khong mang truong `is_discount_percent` phai giu nguyen cach
	# hieu cu. Doi nghia hang loat don cu la mot kieu ghi de du lieu.
	la("thiếu cờ", gia_pancake.gia_mot_don_vi(2200000, {"discount_each_product": 5}), 2199995.0)
	la("cờ tắt", gia_pancake.gia_mot_don_vi(
		2200000, {"discount_each_product": 5, "is_discount_percent": False}), 2199995.0)


@ca("cờ phần trăm nhận cả dạng chuỗi Pancake hay gửi")
def _():
	for v in (True, "true", "True", "1", 1):
		la("cờ %r là bật" % v, gia_pancake.la_phan_tram({"is_discount_percent": v}), True)
	for v in (False, "false", "0", 0, None, ""):
		la("cờ %r là tắt" % v, gia_pancake.la_phan_tram({"is_discount_percent": v}), False)


@ca("giảm quá tay bị chặn hai đầu, không bao giờ ra giá âm hay giá phồng")
def _():
	# Giam am se lam gia PHONG len, tuc ban dat hon gia niem yet ma khong ai
	# thay. Giam qua gia se ra gia am, va ERPNext nhan nguyen con so am do.
	la("giảm âm coi như không giảm", gia_pancake.giam_moi_don_vi(100000, -50), 0.0)
	la("giảm quá giá thì cắt bằng giá", gia_pancake.giam_moi_don_vi(100000, 200000), 100000.0)
	la("phần trăm quá 100 thì cắt", gia_pancake.giam_moi_don_vi(100000, 250, True), 100000.0)
	la("giá sau khi giảm không âm", gia_pancake.gia_mot_don_vi(
		100000, {"discount_each_product": 999, "is_discount_percent": True}), 0.0)


@ca("phép so lệch tổng: im khi khớp, kêu khi lệch, không bịa khi thiếu số")
def _():
	la("khớp thì im", gia_pancake.lech_tong(8230000.0, 8230000.0), 0.0)
	la("lệch thì kêu đúng con số", gia_pancake.lech_tong(8230000.0, 7820000.0), 410000.0)
	# Sai so lam tron cua so thuc khong duoc keu len.
	la("lệch nửa đồng bỏ qua", gia_pancake.lech_tong(7820000.5, 7820000.0), 0.0)
	la("thiếu tổng bên Pancake thì không bịa", gia_pancake.lech_tong(7820000.0, 0), 0.0)


@ca("lưới đối chiếu chạy ở mức GIÁ NIÊM YẾT, không phải mức đã trừ giảm")
def _():
	# v296 doi chieu o muc da tru giam gia va keu nham hang loat ngay trong
	# ngay. Ba so THAT doc duoc tren site sau khi deploy v296:
	#
	#   don 91853  ban tinh 7.820.000  total_price 8.230.000
	#   don 91391  ban tinh 3.800.000  total_price 3.850.000
	#   don 91511  ban tinh 4.532.500  total_price 4.770.000
	#
	# Ca ba deu la don DUNG. Truong `total_price` ma duong dong bo cua tiem
	# nhan duoc la tong TRUOC khi tru giam gia.
	niem_yet = 2200000.0 * 2 + 950000.0 * 4 + 30000.0
	la("tổng niêm yết của đơn 91853", niem_yet, 8230000.0)
	la("so với total_price thì khớp", gia_pancake.lech_tong(niem_yet, 8230000.0), 0.0)
	# Con so da tru giam thi KHONG duoc dem so voi total_price nua.
	da_tru = 2090000.0 * 2 + 902500.0 * 4 + 30000.0
	la("bản tính đã trừ giảm", da_tru, 7820000.0)
	dung("đem con số đã trừ đi so là kêu nhầm",
		gia_pancake.lech_tong(da_tru, 8230000.0) != 0)


@ca("bản tính sai của mã cũ ra đúng con số đã ghi vào phiếu 91853")
def _():
	# Giu lai day de doi sau con doi chieu duoc: 2 x 2.199.995 + 4 x 949.995
	# + 30.000 chinh la 8.229.970, dung con so nam trong phieu ngay 22/08.
	sai = 2199995.0 * 2 + 949995.0 * 4 + 30000.0
	la("bản tính sai", sai, 8229970.0)
	la("khách chuyển ít hơn đúng khoản này", sai - 7820000.0, 409970.0)


# ------------------------------------------------------ ten phap nhan cut

@ca("đúng chuỗi đã làm hỏng tờ hoá đơn 10901 bị chặn")
def _():
	dung("CÔNG TY CỔ PHẦN là tên cụt", hoa_don_vat.thieu_ten_rieng("CÔNG TY CỔ PHẦN"))
	dung("tên đầy đủ thì qua", not hoa_don_vat.thieu_ten_rieng(
		"CÔNG TY CỔ PHẦN MẠNG LƯỚI BÁN DẪN VIỆT NAM"))
	la("phần tên riêng đọc ra đúng",
		hoa_don_vat.phan_rieng("CÔNG TY CỔ PHẦN MẠNG LƯỚI BÁN DẪN VIỆT NAM"),
		"MANG LUOI BAN DAN VIET NAM")


@ca("ngưỡng 15 ký tự không bắt được ca này, nên không được dùng độ dài")
def _():
	# Anh Viet de xuat nguong "duoi 15 ky tu". Ca that lot dung ke: chuoi
	# "CÔNG TY CỔ PHẦN" dem duoc dung 15 ky tu. Ca kiem nay chot lai ly do
	# vi sao khong lam theo do dai, de phien sau khong quay ve cach do.
	la("chuỗi hỏng dài đúng 15 ký tự", len("CÔNG TY CỔ PHẦN"), 15)
	dung("ngưỡng dưới 15 sẽ để lọt", not (len("CÔNG TY CỔ PHẦN") < 15))
	dung("cách đang dùng thì bắt được", hoa_don_vat.thieu_ten_rieng("CÔNG TY CỔ PHẦN"))


@ca("tên thật ngắn trong sổ vẫn qua được, không báo động giả")
def _():
	# Bon ten nay lay tu chinh so hoa don cua tiem, deu la ten that va deu
	# ngan. Mot chot chan bao nham nhung ten nay la mot chot chan bi tat.
	for t in (
		"Công ty TNHH IMAE",
		"CÔNG TY TNHH LA SOL",
		"HỘ KINH DOANH RAVIE",
		"Công ty Cổ phần VNG",
		"CÔNG TY TNHH OSHIMA'S",
		"CÔNG TY LUẬT TNHH RHTLAW VIỆT NAM",
		"Công ty TNHH Nước Giải Khát Suntory PepsiCo Việt Nam",
	):
		dung("tên thật %r phải qua" % t, not hoa_don_vat.thieu_ten_rieng(t))


@ca("mọi biến thể chỉ có loại hình pháp lý đều bị chặn")
def _():
	for t in (
		"", "   ",
		"CÔNG TY", "CONG TY CO PHAN", "công ty tnhh",
		"CÔNG TY TNHH MỘT THÀNH VIÊN",
		"CÔNG TY TRÁCH NHIỆM HỮU HẠN",
		"CÔNG TY TRÁCH NHIỆM HỮU HẠN MỘT THÀNH VIÊN",
		"DOANH NGHIỆP TƯ NHÂN",
		"HỘ KINH DOANH",
		"CHI NHÁNH",
		"CHI NHÁNH CÔNG TY TNHH",
		"VĂN PHÒNG ĐẠI DIỆN",
		"HỢP TÁC XÃ",
		"TỔNG CÔNG TY",
		"CÔNG TY CỔ PHẦN.",
		"Công ty Cổ phần,",
	):
		dung("%r phải bị chặn" % t, hoa_don_vat.thieu_ten_rieng(t))


@ca("bóc theo cụm, không bóc theo từ, và không bóc ngành nghề")
def _():
	# Boc theo TU thi phai dua "VAN", "PHONG", "DAI", "DIEN" vao danh sach
	# de xu ly "van phong dai dien", ma nhung tu do nam trong ten that cua
	# nhieu cong ty. Boc theo CUM thi khong dinh.
	la("chi nhánh lồng công ty", hoa_don_vat.phan_rieng("CHI NHÁNH CÔNG TY TNHH ABC"), "ABC")
	la("văn phòng đại diện có tên riêng",
		hoa_don_vat.phan_rieng("VĂN PHÒNG ĐẠI DIỆN THIÊN LONG"), "THIEN LONG")
	# Nganh nghe KHONG bi boc: cong ty nao ten rieng la mot tu nganh nghe thi
	# van phai qua.
	dung("ngành nghề không bị bóc", not hoa_don_vat.thieu_ten_rieng("CÔNG TY TNHH THƯƠNG MẠI"))
	la("giữ nguyên ngành nghề", hoa_don_vat.phan_rieng("CÔNG TY TNHH THƯƠNG MẠI"), "THUONG MAI")
	# Duoi tieng Anh o cuoi cung khong phan biet ai voi ai.
	la("bóc đuôi tiếng Anh", hoa_don_vat.phan_rieng("VAGABOND COMPANY LIMITED"), "VAGABOND")
	dung("chỉ còn đuôi tiếng Anh thì chặn", hoa_don_vat.thieu_ten_rieng("COMPANY LIMITED"))


# ------------------------------------------------------ dien giai thay the

@ca("tách mẫu số và ký hiệu đúng theo Thông tư 78/2021")
def _():
	# Ban the hien in lien "1C26MPV": mau so 1, ky hieu C26MPV.
	la("chuỗi thật trên tờ 10901", hoa_don_vat.mau_va_ky_hieu("1C26MPV"), ("1", "C26MPV"))
	la("đọc không ra thì không đoán bừa", hoa_don_vat.mau_va_ky_hieu("C26MPV"), ("", "C26MPV"))
	la("rỗng", hoa_don_vat.mau_va_ky_hieu(""), ("", ""))


@ca("câu diễn giải trên tờ thay thế đúng chuẩn, thiếu phần nào thì bỏ phần đó")
def _():
	la("đủ bốn phần",
		hoa_don_vat.dien_giai_thay_the("10901", "1C26MPV", "2026-08-22"),
		"Thay thế cho hóa đơn số 10901, Mẫu số 1, Ký hiệu C26MPV, ngày 22/08/2026")
	la("thiếu ký hiệu thì bỏ hai phần giữa",
		hoa_don_vat.dien_giai_thay_the("10901", "", "2026-08-22"),
		"Thay thế cho hóa đơn số 10901, ngày 22/08/2026")
	la("thiếu số hoá đơn cũ thì câu này vô nghĩa, trả rỗng",
		hoa_don_vat.dien_giai_thay_the("", "1C26MPV", "2026-08-22"), "")


@ca("chèn diễn giải lặp lại được, xuất lại lần hai không nhân đôi câu")
def _():
	mot = hoa_don_vat.chen_dien_giai("Bánh Ổ Epi, size 16cm", "10901", "1C26MPV", "2026-08-22")
	la("lần một",
		mot,
		"Thay thế cho hóa đơn số 10901, Mẫu số 1, Ký hiệu C26MPV, ngày 22/08/2026. Bánh Ổ Epi, size 16cm")
	hai = hoa_don_vat.chen_dien_giai(mot, "10901", "1C26MPV", "2026-08-22")
	la("lần hai không đổi gì", hai, mot)
	la("không có tờ cũ thì giữ nguyên",
		hoa_don_vat.chen_dien_giai("Bánh Ổ Epi", ""), "Bánh Ổ Epi")


# --------------------------------------------- chot ma nguon, khong tuot

@ca("phép tính giá đơn Pancake đi qua gia_pancake, không tự trừ tay nữa")
def _():
	# Day la cho de tuot nhat: mot phien sau doc dong `rate` thay no goi ham
	# la, sua ve `max(gia - giam, 0)` cho "gon" la loi quay lai nguyen ven,
	# va khong ca kiem nao o tren bat duoc vi chung goi thang gia_pancake.
	bh = _doc("ban_hang.py")
	dung("có gọi gia_pancake.dong_gia", "gia_pancake.dong_gia(" in bh)
	dung("không còn phép trừ tay cũ", "max(gia - giam, 0)" not in bh)
	dung("có nhập gia_pancake", "import chiem_sao_ke, gia_pancake, hoa_don_vat" in bh)
	# v299: dong hang phai GIU phan giam gia chu khong nuot vao gia ban.
	dung("dòng hàng đi qua ô giữ giảm giá", "_dong_co_giam(ma, sl, bo_gia)" in bh)
	khuc = bh.split("def _dong_co_giam(")[1].split("\n\n\n")[0]
	dung("có khai giá gốc", '"price_list_rate"' in khuc)
	dung("có khai phần trăm giảm", '"discount_percentage"' in khuc)
	dung("có khai số tiền giảm", '"discount_amount"' in khuc)


@ca("bốn cửa ghi tên người mua đều gọi chốt chặn tên cụt")
def _():
	# Chan o mot cho la khong du: don 92409 vao he qua duong DONG BO, khong
	# qua man nhap nao. Va duong tu xuat hoa don luc 23h30 doc thang truong
	# da luu nen khong di qua cua nhap nao ca.
	bh = _doc("ban_hang.py")
	la("số lần gọi chốt chặn", bh.count("hoa_don_vat.thieu_ten_rieng("), 6)
	for ham in ("luu_xhd", "xhd_khach_luu"):
		khuc = bh.split("def %s(" % ham)[1].split("\n@frappe.whitelist()")[0]
		dung("%s có chặn tên cụt" % ham, "hoa_don_vat.thieu_ten_rieng(" in khuc)


@ca("cửa cuối cùng trước khi tờ hoá đơn rời hệ thống vẫn còn")
def _():
	# Ba cua nhap deu chan roi, nhung to da nam san trong co so du lieu tu
	# truoc thi van ra duoc. Cua nay chan lan cuoi.
	bh = _doc("ban_hang.py")
	khuc = bh.split("la_phan_nhan = bool(mst_mua)")[0] if False else bh
	dung("cửa cuối có mặt", "la_phap_nhan and hoa_don_vat.thieu_ten_rieng(ten_mua)" in khuc)


@ca("cổng tra mã số thuế không nhớ lại kết quả nghi ngờ")
def _():
	# Nho lai la giu cai sai them bay ngay, trong khi nguon co the da sua
	# xong sau vai gio. Dung la cho da xay ra: goi lai chinh ma 0108903529
	# ngay 24/08 thi cong thong tin da tra ve du ten.
	api = _doc("api.py")
	khuc = api.split("def tra_mst(")[1]
	vt_nghi = khuc.find("nghi_thieu")
	vt_nho = khuc.find("cache_set(ck")
	dung("có gắn cờ nghi ngờ", vt_nghi >= 0)
	dung("cờ nghi ngờ đặt TRƯỚC lệnh nhớ", 0 <= vt_nghi < vt_nho)
	dung("nhánh nghi ngờ thoát sớm", "out[\"canh_bao\"] = hoa_don_vat.CANH_BAO_TEN_CUT" in khuc)


@ca("màn hình nào tra mã số thuế cũng đọc cờ nghi ngờ")
def _():
	# May chu chan roi thi nguoi go van phai biet vi sao. Man nao tra ma so
	# thue ma khong doc co la man do de nguoi go dien tiep roi bi chan luc
	# bam Luu, khong hieu vi sao.
	thieu = []
	for t in ("08-doanh-so-sales.js", "09-tinh-tien-quay.js", "10-bill-quay.js"):
		if "nghi_thieu" not in _doc(t, BEP):
			thieu.append(t)
	if "nghi_thieu" not in _doc(os.path.join("trang", "xhd.js")):
		thieu.append("trang/xhd.js")
	if "nghi_thieu" not in _doc(os.path.join("trang", "banh.html")):
		thieu.append("trang/banh.html")
	la("không màn nào bỏ sót", thieu, [])


@ca("khối hoá đơn thay thế vẽ thumbnail qua ô dùng chung, có nút X")
def _():
	js = _doc("08-doanh-so-sales.js", BEP)
	dung("dùng ô chung oTep", "oTep({" in js)
	dung("nút X chỉ hiện khi gỡ được", "go: goDuoc ?" in js)
	dung("có cửa gỡ", "go_bien_ban_thay_the" in js)
	dung("có cửa đính", "dinh_bien_ban_thay_the" in js)


@ca("cửa gỡ biên bản chặn theo trạng thái và chỉ bỏ liên kết")
def _():
	bh = _doc("ban_hang.py")
	khuc = bh.split("def go_bien_ban_thay_the(")[1].split("\n@frappe.whitelist()")[0]
	# Do bang CHINH CAU DIEU KIEN chu khong do bang ten truong: ten truong
	# con nam trong danh sach cot cua get_value, va frappe.throw con nam o
	# hai nhanh loi khac, nen do long tay la ca kiem van xanh khi khoi chan
	# da bi go. Da mac dung bay nay trong lan do doi khang dau tien.
	dung("có chặn theo trạng thái",
		'if (d.custom_hddt_thay_the or "").strip():' in khuc)
	dung("chặn xong thì ném lỗi",
		'if (d.custom_hddt_thay_the or "").strip():' in khuc
		and "frappe.throw" in khuc.split('if (d.custom_hddt_thay_the or "").strip():')[1][:400])
	dung("không xoá tệp", "delete_doc" not in khuc and ".delete()" not in khuc)
	dung("chỉ bỏ liên kết", '"attached_to_doctype": None' in khuc)


@ca("dải băng lệch tổng Pancake có mặt trên màn Doanh số")
def _():
	js = _doc("08-doanh-so-sales.js", BEP)
	dung("màn đọc trường lệch", "vgb_lech_pancake" in js)
	bh = _doc("ban_hang.py")
	dung("máy chủ có khai trường", '"fieldname": "vgb_lech_pancake"' in bh)
	dung("nhịp đồng bộ có ghi", '"vgb_lech_pancake": lech_pk' in bh)
	dung("lưới KHÔNG chặn đồng bộ", "def _lech_pancake(" in bh)
	# Chot cho de tuot nhat cua v297: luoi phai chay o muc GIA NIEM YET.
	# Doi ve muc da tru giam gia la keu nham hang loat, va cong kiem khong
	# co cach nao khac de biet.
	khuc = bh.split("def _lech_pancake(")[1].split("\n\n\n")[0]
	dung("đối chiếu ở mức giá niêm yết", "_tong_niem_yet(o)" in khuc)
	dung("không trừ giảm cấp đơn vào bản tính đem so",
		"tong_minh -= flt(giam_don" not in khuc)
	dung("có hàm tổng niêm yết", "def _tong_niem_yet(" in bh)
