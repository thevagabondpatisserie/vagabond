"""Kiem thu hoa don AM: dieu chinh giam, tra hang, hoan tien.

Con so trong bo ca nay lay tu hoa don THAT, da ky va da gui co quan thue:

    Viet Thinh  C26TVT so 579  09/06/2026  hai ve SGN-SYD/MEL-SGN 36.700.000
    Viet Thinh  C26THV so 3    18/07/2026  hoan lai, giu phi huy 17.430.000
    Grab        C26THF so 511599  02/07/2026  -56.460.090
    Green Ball  C26MGB so 1430    28/07/2026  -402.600

Ba hoa don sau la ba kieu sai khac nhau, va bo ca nay chot rang may goi ten
dung tung kieu chu khong go chung mot cau "lech tong".
"""

from vagabond import doi_soat_chung_tu as ds
from vagabond import mua_dich_vu as md
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Dau hoa don hoan ve di Uc. Tien ve tai khoan MB dung 19.270.000.
UC_HOAN = {"so_hd": "3", "tien_truoc_thue": -36700000, "tien_thue": 0,
	"tong_tien": -19270000}

# Hoa don mua ve goc, thue suat 0% vi la van tai quoc te.
UC_MUA = {"so_hd": "579", "tien_truoc_thue": 36700000, "tien_thue": 0,
	"tong_tien": 36700000}

# Chi tiet hoa don hoan: mot dong dien giai 0 dong va mot dong ve am. Phi
# huy ve KHONG nam trong chi tiet, no o mot bang rieng ma m-invoice khong
# giu lai - dung y het ca ve may bay thuong.
UC_CHI_TIET = [
	{"tchat": 1, "thtien": 0, "ten": "Điều chỉnh giảm doanh thu do hoàn vé"},
	{"tchat": 1, "thtien": -36700000, "ten": "Vé SGN-SYD/MEL-SGN"},
]

# Grab: hoa don am ma chung tu lai ghi duong.
GRAB = {"so_hd": "511599", "tien_truoc_thue": -52277861, "tien_thue": -4182229,
	"tong_tien": -56460090}

# Ve may bay Viet Thinh 752, dung de doi chieu chieu nguoc lai.
VT752_DAU = {"so_hd": "752", "tien_truoc_thue": 1641499, "tien_thue": 131320,
	"tong_tien": 1850000}
VT752_CHI_TIET = [{"tchat": 1, "thtien": 1641499, "ten": "Vé DIN-HAN"}]

# Green Ball: cac dong hang dung so, chung tu chi thieu dong thue.
GB = {"so_hd": "1430", "tien_truoc_thue": -372778, "tien_thue": -29822,
	"tong_tien": -402600}


# ------------------------------------------------- nhan ra hoa don am

@ca("hoá đơn âm: nhận ra hoá đơn hoàn vé, và không nhầm hoá đơn mua")
def _():
	dung("hoá đơn hoàn là âm", md.la_hoa_don_am(UC_HOAN))
	dung("hoá đơn mua vé không phải âm", not md.la_hoa_don_am(UC_MUA))
	dung("hoá đơn Grab là âm", md.la_hoa_don_am(GRAB))
	dung("đầu hoá đơn rỗng thì không phải âm", not md.la_hoa_don_am({}))


@ca("hoá đơn âm: gốc dòng hàng vẫn là tổng tiền trừ thuế, không đổi công thức")
def _():
	la("gốc của hoá đơn hoàn", md.goc_dong_hang(UC_HOAN), -19270000)
	la("gốc của hoá đơn Grab", md.goc_dong_hang(GRAB), -52277861)
	la("gốc của hoá đơn Green Ball", md.goc_dong_hang(GB), -372778)


@ca("hoá đơn âm: phí huỷ vé suy ra đúng 17.430.000 và là số dương")
def _():
	# Tien ve tai khoan 19.270.000, tien ve hoan 36.700.000, hieu chinh la
	# phan Viet Thinh giu lai. Phi la tien MINH MAT nen luon duong, du hoa
	# don am.
	phi = md.phi_ngoai_thue(UC_HOAN)
	la("phí huỷ vé", phi, 17430000)
	dung("phí phải là số dương dù hoá đơn âm", phi > 0)
	la("hoá đơn mua vé gốc không có phí", md.phi_ngoai_thue(UC_MUA), 0)


@ca("hoá đơn âm: ba con số đầu hoá đơn phải tự khớp nhau")
def _():
	for ten, d in (("hoàn vé", UC_HOAN), ("Grab", GRAB), ("Green Ball", GB)):
		truoc, thue, tong = md.so_theo_dau_hoa_don(d)
		dung("gốc cộng thuế bằng tổng, hoá đơn %s" % ten,
			abs(md.goc_dong_hang(d) + thue - tong) <= 1)
		dung("gốc bằng trước thuế cộng phí, hoá đơn %s" % ten,
			abs(truoc + md.phi_ngoai_thue(d) - md.goc_dong_hang(d)) <= 1)


# --------------------------------------------- cach ghi dong cho ERPNext

@ca("hoá đơn âm: ghi số lượng âm chứ không ghi đơn giá âm")
def _():
	# ERPNext doi phieu tra lai phai co it nhat mot dong so luong am. Phieu
	# HDM-2026-00325 do chinh may sinh ra ghi so luong -5, don gia 69.000.
	sl, gia = md.so_dong_theo_dau(-36700000)
	la("số lượng", sl, -1)
	la("đơn giá", gia, 36700000)
	dung("nhân lại ra đúng số tiền ban đầu", abs(sl * gia + 36700000) < 1)


@ca("hoá đơn âm: tiền dương thì giữ nguyên cách ghi cũ")
def _():
	sl, gia = md.so_dong_theo_dau(1641499)
	la("số lượng", sl, 1)
	la("đơn giá", gia, 1641499)
	la("số không", md.so_dong_theo_dau(0), (1, 0))


@ca("hoá đơn âm: dòng vé ghi số lượng âm, dòng phí ghi số lượng dương")
def _():
	ve = md.dong_dich_vu("VIỆT THỊNH", "3", -36700000)
	phi = md.dong_phi("3", 17430000)
	la("số lượng dòng vé", ve["qty"], -1)
	la("thành tiền dòng vé", ve["amount"], -36700000)
	la("số lượng dòng phí", phi["qty"], 1)
	la("thành tiền dòng phí", phi["amount"], 17430000)
	dung("hai dòng cộng lại đúng bằng gốc",
		abs(ve["amount"] + phi["amount"] - md.goc_dong_hang(UC_HOAN)) < 1)


# ------------------------------------------------- goi ten kieu sai

@ca("chẩn đoán: hoá đơn Grab bị lật dấu thì gọi đúng tên dấu ngược")
def _():
	# Chung tu ACC-PINV-2026-02399 ghi +52.277.861 cho hoa don -56.460.090.
	la("Grab", md.chan_doan_lech(GRAB, 52277861, 0), "dau_nguoc")


@ca("chẩn đoán: Green Ball thiếu dòng thuế thì gọi đúng tên thiếu dòng thuế")
def _():
	# Chung tu HDM-2026-00325 ghi -372.778, dung bang cac dong hang, chi
	# thieu dong thue -29.822 nen tong khong ra -402.600.
	la("Green Ball", md.chan_doan_lech(GB, -372778, 0), "thieu_dong_thue")


@ca("chẩn đoán: có dòng thuế rồi mà vẫn lệch thì không đổ cho thiếu thuế")
def _():
	la("đã có dòng thuế", md.chan_doan_lech(GB, -372778, -29822), "lech_khac")


@ca("chẩn đoán: đúng số thì bảo khớp, lệch một đồng vẫn cho là khớp")
def _():
	la("đúng số", md.chan_doan_lech(UC_HOAN, -19270000, 0), "khop")
	la("lệch một đồng", md.chan_doan_lech(UC_HOAN, -19269999, 0), "khop")
	la("lệch hai đồng", md.chan_doan_lech(UC_HOAN, -19269998, 0), "lech_khac")


# ------------------------------------------------------- doi soat co

@ca("đối soát: đánh dấu đã tạo chứng từ mà không có chứng từ nào")
def _():
	# Dung ca cua hoa don hoan ve: co bat len ma trong ERP khong co gi.
	la("không có chứng từ", ds.xep_loai(UC_HOAN, []), ds.KHONG_CO)
	la("truyền None cũng vậy", ds.xep_loai(UC_HOAN, None), ds.KHONG_CO)


@ca("đối soát: chứng từ đã huỷ hết thì khác với chưa từng có chứng từ")
def _():
	la("đã huỷ", ds.xep_loai(UC_HOAN, [
		{"ten": "X", "tong": -19270000, "tong_thue": 0, "docstatus": 2}]),
		ds.DA_HUY)


@ca("đối soát: nhiều chứng từ cho một hoá đơn thì cộng lại rồi mới đối chiếu")
def _():
	# Ke toan tach mot hoa don thanh hai phieu theo tai khoan van hop le,
	# mien tong bang nhau.
	la("hai phiếu cộng lại vừa đủ", ds.xep_loai(UC_MUA, [
		{"ten": "A", "tong": 20000000, "tong_thue": 0, "docstatus": 1},
		{"ten": "B", "tong": 16700000, "tong_thue": 0, "docstatus": 1}]),
		ds.KHOP)
	la("phiếu huỷ không được tính vào", ds.xep_loai(UC_MUA, [
		{"ten": "A", "tong": 36700000, "tong_thue": 0, "docstatus": 1},
		{"ten": "B", "tong": 36700000, "tong_thue": 0, "docstatus": 2}]),
		ds.KHOP)


@ca("đối soát: xếp đúng loại cho ba ca thật Grab, Green Ball, hoàn vé")
def _():
	la("Grab lật dấu", ds.xep_loai(GRAB, [
		{"ten": "ACC-PINV-2026-02399", "tong": 52277861, "tong_thue": 0,
		 "docstatus": 0}]), ds.DAU_NGUOC)
	la("Green Ball thiếu thuế", ds.xep_loai(GB, [
		{"ten": "HDM-2026-00325", "tong": -372778, "tong_thue": 0,
		 "docstatus": 0}]), ds.THIEU_THUE)
	la("hoàn vé chưa có gì", ds.xep_loai(UC_HOAN, []), ds.KHONG_CO)


@ca("đối soát: chỉ mã khớp mới là yên, còn lại đều phải nhìn")
def _():
	dung("khớp thì yên", not ds.dang_lo(ds.KHOP))
	for ma in (ds.KHONG_CO, ds.DA_HUY, ds.DAU_NGUOC, ds.THIEU_THUE, ds.LECH_KHAC):
		dung("mã %s phải được coi là vấn đề" % ma, ds.dang_lo(ma))
		dung("mã %s phải có câu tiếng Việt" % ma, len(ds.mo_ta(ma)) > 10)


@ca("đối soát: bảng tóm tắt cộng tiền tuyệt đối, hoá đơn âm không triệt tiêu")
def _():
	bang = ds.gom_theo_ma([
		{"xep_loai": ds.KHONG_CO, "tong_tien": -19270000},
		{"xep_loai": ds.KHONG_CO, "tong_tien": -5760000},
		{"xep_loai": ds.DAU_NGUOC, "tong_tien": -56460090},
	])
	la("gom thành hai nhóm", len(bang), 2)
	la("nhóm to đứng trước", bang[0]["ma"], ds.DAU_NGUOC)
	la("đếm đúng số hoá đơn", bang[1]["so_hoa_don"], 2)
	la("cộng tuyệt đối, không triệt tiêu", bang[1]["tien"], 25030000)


# ------------------------------------------ luoi tu can tren hoa don am

@ca("tự cân: lưới hoá đơn hoàn vé thiếu đúng phần phí huỷ")
def _():
	# Chi tiet cong lai ra -36.700.000, goc phai la -19.270.000, nen thieu
	# dung 17.430.000. Phep tru nay khong phu thuoc dau.
	tong_dong = md.gom_dong_theo_tinh_chat(UC_CHI_TIET)
	la("cộng chi tiết", tong_dong, -36700000)
	thieu = md.goc_dong_hang(UC_HOAN) - tong_dong
	la("phần thiếu", thieu, 17430000)
	dung("phần thiếu đúng bằng phí ngoài thuế",
		abs(thieu - md.phi_ngoai_thue(UC_HOAN)) < 1)


@ca("tự cân: lưới đã đúng số rồi thì không cân thêm lần nữa")
def _():
	goc = md.goc_dong_hang(UC_HOAN)
	dung("đủ hai dòng là khớp", md.da_khop_roi(-36700000 + 17430000, goc))
	dung("mới có dòng vé thì chưa khớp", not md.da_khop_roi(-36700000, goc))


# ----------------------------------------- nguong cua bao cao doi soat

@ca("ngưỡng: cổng chặn ghi sổ vẫn soi gắt một đồng, không được nới")
def _():
	# Hoa don dien tu la so da gui co quan thue. Cho nay khong bao gio noi.
	la("lệch một đồng vẫn cho qua", md.chan_doan_lech(UC_MUA, 36700001, 0), "khop")
	la("lệch hai đồng là chặn", md.chan_doan_lech(UC_MUA, 36700002, 0), "lech_khac")


@ca("ngưỡng: báo cáo đối soát bỏ qua sai số làm tròn dưới 100 đồng")
def _():
	# Quet that 19/08/2026: 1.569 hoa don dau ra lech tu 1 den 100 dong, toan
	# bo la lam tron. De nguong 1 dong thi chung nhan chim 108 ca that.
	mot_phieu = lambda tong: [
		{"ten": "X", "tong": tong, "tong_thue": 0, "docstatus": 1}]
	la("lệch 7 đồng, báo cáo coi là khớp",
		ds.xep_loai(UC_MUA, mot_phieu(36699993)), ds.KHOP)
	la("lệch 99 đồng, vẫn khớp",
		ds.xep_loai(UC_MUA, mot_phieu(36699901)), ds.KHOP)
	la("lệch 150 đồng thì phải nhìn",
		ds.xep_loai(UC_MUA, mot_phieu(36699850)), ds.LECH_KHAC)


@ca("ngưỡng: gọi báo cáo với ngưỡng một đồng thì soi gắt như cổng")
def _():
	mot_phieu = [{"ten": "X", "tong": 36699993, "tong_thue": 0, "docstatus": 1}]
	la("ngưỡng mặc định bỏ qua", ds.xep_loai(UC_MUA, mot_phieu), ds.KHOP)
	la("ngưỡng một đồng thì bắt", ds.xep_loai(UC_MUA, mot_phieu, 1), ds.LECH_KHAC)


@ca("ngưỡng: dấu ngược và thiếu dòng thuế không bị ngưỡng che mất")
def _():
	# Hai kieu sai nay khong bao gio la chuyen lam tron, nen du nguong nao
	# cung phai loi ra.
	la("Grab lật dấu", ds.xep_loai(GRAB, [
		{"ten": "A", "tong": 52277861, "tong_thue": 0, "docstatus": 0}]),
		ds.DAU_NGUOC)
	la("Green Ball thiếu thuế", ds.xep_loai(GB, [
		{"ten": "B", "tong": -372778, "tong_thue": 0, "docstatus": 0}]),
		ds.THIEU_THUE)


# --------------------------------- khoan giam nam ngoai luoi dong hang

# Nha van hoa Thanh Nien TP.HCM, hoa don ban hang C26TVH so 187 ngay
# 02/08/2026, mau so 2 nen khong tach thue GTGT. Chi phi phoi hop dia diem
# hoat dong van hanh mo hinh quay banh Phap trong khuon kho du an
# "BOOK GARDEN 21", hop dong 76-HD/NVH.
#
#     dong hang             10.101.010
#     tong tien thanh toan  10.000.000
#     ----------------------------------
#     giam                     101.010
#
# Chan hoa don: "Da giam 101.010d tuong ung 20% muc ty le % de tinh thue gia
# tri gia tang theo Nghi quyet so 204/2025/QH15". Dung 1% cua 10.101.010.
#
# Kiem tren he 19/08/2026: o `tien_truoc_thue` cua ban ghi nay BANG 0. Day
# chinh la ly do phai do khoan giam bang phan chi tiet chu khong bang
# `phi_ngoai_thue`: neu do bang `tien_truoc_thue` thi
# `so_theo_dau_hoa_don` se bu o trong bang tong tru thue, ra dung 10.000.000,
# va phi ngoai thue thanh 0 - may se khong thay khoan giam nao ca.
NVH = {"so_hd": "187", "tien_truoc_thue": 0, "tien_thue": 0,
	"tong_tien": 10000000}
NVH_CHI_TIET = [
	{"tchat": 1, "thtien": 10101010,
	 "ten": "Chi phí phối hợp địa điểm hoạt động vận hành mô hình quầy"},
]


@ca("giảm ngoài dòng: đo đúng 101.010 của hoá đơn Nhà văn hoá Thanh Niên")
def _():
	giam = md.giam_ngoai_dong(NVH, NVH_CHI_TIET)
	la("khoản giảm", giam, 101010)
	dung("đúng 1% của dòng hàng, tức 20% mức tỷ lệ 5%",
		abs(giam - 10101010 * 0.01) < 1)


@ca("giảm ngoài dòng: hoá đơn không có khoản giảm thì bằng không")
def _():
	# Ve may bay Viet Thinh: chi tiet 1.641.499, goc 1.718.680, tuc chi tiet
	# THIEU chu khong thua. Ham phai ra so am, va nhanh can thua khong duoc
	# dung vao.
	dung("vé máy bay ra số âm vì thiếu chứ không thừa",
		md.giam_ngoai_dong(VT752_DAU, VT752_CHI_TIET) < 0)
	la("hoá đơn khớp sẵn thì bằng không",
		md.giam_ngoai_dong(UC_MUA, [{"tchat": 1, "thtien": 36700000}]), 0)


@ca("giảm ngoài dòng: dựng đúng kế hoạch đưa 101.010 vào ô Chiết khấu")
def _():
	la("phiếu đang ghi 10.101.010",
		md.ke_hoach_giam_ngoai_dong(10101010, NVH, NVH_CHI_TIET), 101010)


@ca("giảm ngoài dòng: lệch dưới 100 đồng vẫn cho, lệch nhiều thì không đụng")
def _():
	dung("lệch 50 đồng vẫn dựng được kế hoạch",
		md.ke_hoach_giam_ngoai_dong(10101060, NVH, NVH_CHI_TIET) is not None)
	dung("lệch 5.000 đồng thì không đụng vào phiếu",
		md.ke_hoach_giam_ngoai_dong(10106010, NVH, NVH_CHI_TIET) is None)


@ca("giảm ngoài dòng: phiếu đã đúng số rồi thì không tự bịa ra khoản giảm")
def _():
	# Day la cho nguy hiem nhat. May tuyet doi khong duoc tu tru bot tien
	# tren mot chung tu thue chi vi thay so khong khop.
	dung("phiếu đã bằng gốc thì không có kế hoạch nào",
		md.ke_hoach_giam_ngoai_dong(10000000, NVH, NVH_CHI_TIET) is None)
	dung("phiếu thiếu tiền thì cũng không",
		md.ke_hoach_giam_ngoai_dong(9000000, NVH, NVH_CHI_TIET) is None)
	dung("hoá đơn không có khoản giảm thì dù phiếu thừa cũng không đụng",
		md.ke_hoach_giam_ngoai_dong(
			37000000, UC_MUA, [{"tchat": 1, "thtien": 36700000}]) is None)


@ca("giảm ngoài dòng: không lẫn với đường chiết khấu thương mại của GSM")
def _():
	# Hoa don GSM thua tien vi co dong chiet khau tchat 3 bi cong thay vi
	# tru. Duong do da co san va phai duoc uu tien, duong giam ngoai dong
	# chi la duong hai.
	gsm_dau = {"so_hd": "57194", "tien_truoc_thue": 22068519,
		"tien_thue": 1765482, "tong_tien": 23834001}
	ct = [{"tchat": 1, "thtien": 24338889, "ten": "Cước phí vận chuyển"},
		{"tchat": 3, "thtien": 2270370, "ten": "Chiết khấu thương mại"}]
	# gom dung dau: 24.338.889 - 2.270.370 = 22.068.519, dung bang goc.
	la("cộng đúng dấu ra đúng gốc", md.gom_dong_theo_tinh_chat(ct), 22068519)
	la("nên không còn khoản giảm ngoài dòng nào",
		md.giam_ngoai_dong(gsm_dau, ct), 0)


@ca("giảm ngoài dòng: đo bằng chi tiết chứ không bằng ô tiền trước thuế")
def _():
	# Chot lai bang mot ca rieng vi day la ly do ton tai cua ham moi. Ban ghi
	# that cua hoa don 187 de trong o tien truoc thue, nen duong do cu tit.
	la("ô tiền trước thuế bị bù thành tổng trừ thuế",
		md.so_theo_dau_hoa_don(NVH)[0], 10000000)
	la("nên phí ngoài thuế bằng không, không thấy gì", md.phi_ngoai_thue(NVH), 0)
	la("còn đo bằng chi tiết thì ra đúng 101.010",
		md.giam_ngoai_dong(NVH, NVH_CHI_TIET), 101010)


# ------------------- v350: nan dau ngay tu luc dung chung tu, khong chi chan doan

# Truoc ban nay, may chi GOI TEN duoc cai sai ("dau_nguoc") chu khong sua
# duoc goc. Chung tu ACC-PINV-2026-02399 van nam do voi so +52.277.861
# trong khi hoa don Grab la -56.460.090.
#
# Goc nam o `minvoice_chung_tu.dong_tu_hoa_don`: nha phat hanh ghi CA so
# luong LAN don gia cung am, am nhan am ra duong. Anh Viet chot 29/08/2026
# rang to am la hop le, la hoa don thay the, nen phai vao so cho dung chieu
# chu khong phai bo qua.
#
# Nghi dinh 70/2025/ND-CP hieu luc 01/06/2025 cho phep hoa don dieu chinh
# ghi so am bang dau tru.

@ca("nắn dấu: dấu của cả tờ lấy theo tổng tiền")
def _():
	from vagabond import minvoice_chung_tu as mc

	la("tờ Grab là tờ âm", mc.dau_cua_to(GRAB["tong_tien"]), -1)
	la("tờ mua vé là tờ dương", mc.dau_cua_to(UC_MUA["tong_tien"]), 1)
	la("không tiền coi như dương", mc.dau_cua_to(0), 1)
	la("None coi như dương", mc.dau_cua_to(None), 1)
	la("chữ rác coi như dương", mc.dau_cua_to("abc"), 1)


@ca("nắn dấu: cả số lượng lẫn đơn giá cùng âm thì đơn giá phải dương lại")
def _():
	from vagabond import minvoice_chung_tu as mc

	# Day dung la cai bay da lam hong to Grab: -3 nhan -25.000 ra +75.000.
	sl, gia = mc.nan_dau_dong(-3, -25000, -75000)
	la("số lượng âm", sl, -3.0)
	la("đơn giá dương", gia, 25000.0)
	la("thành tiền âm", sl * gia, -75000.0)


@ca("nắn dấu: dấu nằm ở đâu cũng ra cùng một kết quả")
def _():
	from vagabond import minvoice_chung_tu as mc

	for ten, sl, gia in (("số lượng âm", -3, 25000),
			("đơn giá âm", 3, -25000),
			("cả hai cùng âm", -3, -25000)):
		a, b = mc.nan_dau_dong(sl, gia, -75000)
		la("số lượng âm, kiểu ghi %s" % ten, a, -3.0)
		la("đơn giá dương, kiểu ghi %s" % ten, b, 25000.0)
		la("thành tiền âm, kiểu ghi %s" % ten, a * b, -75000.0)


@ca("nắn dấu: giữ nguyên số lượng thật chứ không ép về một")
def _():
	from vagabond import minvoice_chung_tu as mc

	# Ep so luong ve 1 la mat thong tin: to hoan 1.500 qua trung phai con
	# thay 1.500 qua, khong phai mot dong gop 3,2 trieu.
	sl, gia = mc.nan_dau_dong(-1500, -2190.48, -3285720)
	la("giữ nguyên 1.500 quả", sl, -1500.0)
	la("đơn giá dương", gia, 2190.48)


@ca("nắn dấu: cùng quy ước với cách ghi dòng của mua dịch vụ")
def _():
	from vagabond import minvoice_chung_tu as mc

	# Hai mo dun cung ghi mot kieu: don gia KHONG BAO GIO am, dau nam o so
	# luong. Lech quy uoc la mot chung tu ra mot kieu.
	sl_md, gia_md = md.so_dong_theo_dau(-36700000)
	sl_mc, gia_mc = mc.nan_dau_dong(1, -36700000, -36700000)
	la("cùng số lượng", sl_mc, float(sl_md))
	la("cùng đơn giá", gia_mc, float(gia_md))


@ca("nắn dấu: không có thành tiền thì lấy dấu theo tích")
def _():
	from vagabond import minvoice_chung_tu as mc

	la("số lượng âm", mc.nan_dau_dong(-3, 25000, None)[0] * 25000.0, -75000.0)
	sl, gia = mc.nan_dau_dong(-3, -25000, None)
	# Ca hai cung am ma khong co thanh tien thi tich ra duong. Khong tu doan
	# thanh am: doan sai o day la lat nguoc mot to mua that.
	la("tích dương thì để dương", sl * gia, 75000.0)
	la("đơn giá vẫn phải dương", gia, 25000.0)


@ca("nắn dấu: tờ dương đi qua đường cũ, không đụng vào")
def _():
	from vagabond import minvoice_chung_tu as mc

	goc = {"dgia": 2190.48, "dvtinh": "Quả", "sluong": 1500,
		"ten": "Trứng gà", "thtien": 3285720}
	la("mặc định là tờ dương", mc.dong_tu_hoa_don(goc), mc.dong_tu_hoa_don(goc, 1))
	# Dong chiet khau ghi so am tren mot to DUONG: duong cu de don gia am,
	# so luong duong. Doi cach ghi do la tu nhien lam hong nhung to dang
	# chay tot.
	ck = {"ten": "Chiết khấu", "sluong": 1, "dgia": -50000, "thtien": -50000}
	x = mc.dong_tu_hoa_don(ck, 1)
	la("số lượng giữ dương", x["sl"], 1)
	la("đơn giá giữ âm", x["gia"], -50000)
	la("thành tiền vẫn âm", x["tien"], -50000)


@ca("nắn dấu: dòng đơn giá trống trên tờ âm vẫn ra thành tiền âm")
def _():
	from vagabond import minvoice_chung_tu as mc

	# Hoa don tien dien, phi dich vu chi co thanh tien. Ban hoan lai cua no
	# khong duoc lat nguoc thanh mot khoan chi.
	x = mc.dong_tu_hoa_don(
		{"ten": "Hoàn phí dịch vụ", "sluong": 0, "dgia": 0,
			"thtien": -1283500}, -1)
	la("số lượng âm một", x["sl"], -1.0)
	la("đơn giá dương", x["gia"], 1283500.0)
	la("thành tiền âm", x["tien"], -1283500.0)


@ca("nắn dấu: cân theo trị tuyệt đối rồi mới gắn dấu lại")
def _():
	from vagabond import minvoice_chung_tu as mc

	dau = -1
	viec, so_tien = mc.can_theo_truoc_thue(dau * -70000, dau * -75000)
	la("thiếu tiền thì thêm dòng phí", viec, "phi")
	la("thiếu 5.000", so_tien, 5000)
	la("dòng phí phải mang dấu âm", dau * so_tien, -5000)

	viec, so_tien = mc.can_theo_truoc_thue(dau * -80000, dau * -75000)
	la("thừa tiền thì ghi ô giảm giá", viec, "giam")
	la("ô giảm giá mang dấu âm", dau * so_tien, -5000)

	# To duong phai ra y nguyen ket qua cu.
	la("tờ dương khớp", mc.can_theo_truoc_thue(3285720, 3285720), ("khop", 0))
	la("tờ dương thiếu", mc.can_theo_truoc_thue(3650000, 3700000), ("phi", 50000))
	la("tờ dương thừa", mc.can_theo_truoc_thue(3700000, 3650000), ("giam", 50000))


@ca("nắn dấu: đường dựng chứng từ phải truyền dấu tờ xuống từng dòng")
def _():
	import inspect

	from vagabond import minvoice_chung_tu as mc

	c = inspect.getsource(mc.dung_hoa_don_mua)
	dung("có lấy dấu của tờ", 'dau_cua_to(r.get("tong_tien"))' in c)
	dung("có truyền xuống dòng", "dong_tu_hoa_don(it, dau)" in c)
	dung("có nhân dấu vào cả hai vế khi cân", "dau * tong_dong" in c)
	dung("dòng phí mang dấu của tờ", '"sl": dau' in c)
	dung("ô giảm giá mang dấu của tờ", "(dau * so_tien) if viec" in c)


@ca("nắn dấu: dòng thuế của tờ âm không được rơi mất")
def _():
	import inspect

	from vagabond import minvoice_chung_tu as mc

	# To Grab co tien thue -4.182.229. Xet "lon hon khong" la bo luon dong
	# thue, va tong chung tu lech dung bang tien thue do.
	c = inspect.getsource(mc.dung_hoa_don_mua)
	dung("xét khác không", 'flt(r.get("tien_thue")) != 0' in c)
	dung("không còn xét lớn hơn không", 'flt(r.get("tien_thue")) > 0' not in c)
	dung("tờ Grab có tiền thuế âm thật", GRAB["tien_thue"] < 0)
