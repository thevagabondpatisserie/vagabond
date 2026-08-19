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
