"""Kiem thu luong chung tu mua dich vu, va phep cong dung dau cua chi tiet.

Con so trong bo ca nay lay tu hoa don THAT: cuoc van chuyen GSM so 57194
ngay 31/07/2026, hoa don da ky va da gui co quan thue. Dau hoa don ghi tien
truoc thue 22.068.519, thue 1.765.482, tong 23.834.001. Phan chi tiet 929
dong cong tho ra 26.609.274 vi mot dong chiet khau thuong mai 2.270.370 bi
cong thay vi tru.

Kiem o day chu khong kiem tren site: bon ham nay thuan, dua vao chung so
tien ma khong dua vao Frappe, nen sai la biet ngay tu may lap trinh.
"""

from vagabond import mua_dich_vu as md
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Dau hoa don GSM 57194.
GSM_DAU = {"so_hd": "57194", "tien_truoc_thue": 22068519, "tien_thue": 1765482,
	"tong_tien": 23834001}

# Bon dong dau cua phan chi tiet, cong them dong chiet khau that.
GSM_CHI_TIET = [
	{"tchat": 1, "thtien": 120111, "ten": "Cước phí vận chuyển"},
	{"tchat": 1, "thtien": 7667, "ten": "Phí nền tảng"},
	{"tchat": 5, "thtien": 17278, "ten": "Cước phí vận chuyển"},
	{"tchat": 4, "thtien": 999999, "ten": "Ghi chú, không tính tiền"},
	{"tchat": 3, "thtien": 2270370, "ten": "Chiết khấu thương mại"},
]


# ------------------------------------------------- doc so o dau hoa don

@ca("mua dịch vụ: lấy đúng ba con số ở đầu hoá đơn điện tử")
def _():
	truoc, thue, tong = md.so_theo_dau_hoa_don(GSM_DAU)
	la("tiền trước thuế", truoc, 22068519)
	la("tiền thuế", thue, 1765482)
	la("tổng tiền", tong, 23834001)
	dung("ba số phải cộng khớp nhau", abs(truoc + thue - tong) <= 1)


@ca("mua dịch vụ: hoá đơn hộ kinh doanh để trống ô trước thuế thì lấy tổng tiền")
def _():
	# Nam hoa don kieu nay dang nam trong he: Abby E33, Trai cay nhap khau,
	# Nguyen Van Tien, Nha van hoa Thanh Nien. Ho kinh doanh khong co thue nen
	# m-invoice bo trong o tien_truoc_thue. Lay nguyen o trong la ghi so 0 dong.
	truoc, thue, tong = md.so_theo_dau_hoa_don(
		{"tien_truoc_thue": 0, "tien_thue": 0, "tong_tien": 320760})
	la("trước thuế lấy theo tổng", truoc, 320760)
	la("thuế bằng không", thue, 0)
	la("tổng giữ nguyên", tong, 320760)


@ca("mua dịch vụ: thiếu ô tổng tiền thì dựng lại từ trước thuế cộng thuế")
def _():
	truoc, thue, tong = md.so_theo_dau_hoa_don(
		{"tien_truoc_thue": 1000000, "tien_thue": 80000, "tong_tien": 0})
	la("tổng dựng lại", tong, 1080000)
	la("trước thuế giữ nguyên", truoc, 1000000)
	la("thuế giữ nguyên", thue, 80000)


@ca("mua dịch vụ: đầu hoá đơn rỗng thì trả về ba số không, không nổ")
def _():
	la("trước thuế", md.so_theo_dau_hoa_don(None)[0], 0)
	la("thuế", md.so_theo_dau_hoa_don({})[1], 0)
	la("tổng", md.so_theo_dau_hoa_don({})[2], 0)


# ------------------------------------------- cong chi tiet cho dung dau

@ca("chi tiết: dòng chiết khấu thương mại phải TRỪ, không được cộng")
def _():
	# Day dung la loi da lam hoa don GSM lech 4.540.755, tuc HAI LAN dong
	# chiet khau. Cong tho: 120111+7667+17278+2270370 = 2415426.
	# Cong dung dau:      120111+7667+17278-2270370 = -2125314.
	la("cộng đúng dấu", md.gom_dong_theo_tinh_chat(GSM_CHI_TIET), -2125314)
	tho = sum(d["thtien"] for d in GSM_CHI_TIET if d["tchat"] != 4)
	dung("cộng thô và cộng đúng dấu phải lệch đúng hai lần chiết khấu",
		abs(tho - md.gom_dong_theo_tinh_chat(GSM_CHI_TIET) - 2 * 2270370) < 1)


@ca("chi tiết: dòng ghi chú diễn giải không tính tiền")
def _():
	la("bỏ dòng tchat 4", md.gom_dong_theo_tinh_chat(
		[{"tchat": 4, "thtien": 999999}]), 0)
	la("giữ dòng tchat 1", md.gom_dong_theo_tinh_chat(
		[{"tchat": 1, "thtien": 500}]), 500)
	la("giữ dòng tchat 5 là dòng phí, vẫn tính tiền", md.gom_dong_theo_tinh_chat(
		[{"tchat": 5, "thtien": 700}]), 700)


@ca("chi tiết: tính chất đọc được dù m-invoice trả về số hay chuỗi")
def _():
	la("số 3", md.gom_dong_theo_tinh_chat([{"tchat": 3, "thtien": 100}]), -100)
	la("chuỗi 3", md.gom_dong_theo_tinh_chat([{"tchat": "3", "thtien": 100}]), -100)
	la("danh sách rỗng", md.gom_dong_theo_tinh_chat([]), 0)
	la("không có gì", md.gom_dong_theo_tinh_chat(None), 0)


# ------------------------------------------------------- cong chan lech

@ca("chặn lệch: một đồng vẫn cho qua, hai đồng thì chặn")
def _():
	dung("bằng nhau thì không lệch", not md.lech_qua_nguong(100, 100))
	dung("lệch một đồng vẫn cho qua", not md.lech_qua_nguong(101, 100))
	dung("lệch hai đồng là chặn", md.lech_qua_nguong(102, 100))
	dung("lệch âm cũng chặn", md.lech_qua_nguong(98, 100))
	dung("đúng số GSM sai thì phải chặn",
		md.lech_qua_nguong(28374756, 23834001))


# ------------------------------------------------------- gom mot lan thoi

@ca("gom dòng: lưu lại lần hai không gom đè lên lần một")
def _():
	dung("một dòng đúng số là đã gom rồi", md.da_gom_roi(1, 22068519, 22068519))
	dung("một dòng lệch một đồng vẫn coi là đã gom",
		md.da_gom_roi(1, 22068520, 22068519))
	dung("929 dòng thì chưa gom", not md.da_gom_roi(929, 120111, 22068519))
	dung("một dòng nhưng sai số thì gom lại",
		not md.da_gom_roi(1, 26609274, 22068519))
	dung("không dòng nào thì chưa gom", not md.da_gom_roi(0, 0, 22068519))


@ca("gom dòng: kế toán đã tách nhiều dòng theo tài khoản thì không gom đè")
def _():
	# Anh Viet muon cho tach dong tong thanh vai dong theo tai khoan, vi du
	# phan giao khach vao 6417 phan giao bep vao 6277. Gom de la mat cong do.
	dung("hai dòng là không gom nữa", not md.da_gom_roi(2, 11000000, 22068519))


# ---------------------------------------------------------- dung mot dong

@ca("dòng dịch vụ: dựng ra đúng một dòng số lượng 1, đơn giá bằng cả khoản")
def _():
	d = md.dong_dich_vu("GSM", "57194", 22068519, "6417 - Chi phí dịch vụ mua ngoài - TV",
		"Main - TV")
	la("số lượng", d["qty"], 1)
	la("đơn giá", d["rate"], 22068519)
	la("thành tiền", d["amount"], 22068519)
	la("tài khoản chi phí", d["expense_account"], "6417 - Chi phí dịch vụ mua ngoài - TV")
	la("trung tâm chi phí", d["cost_center"], "Main - TV")
	dung("mô tả có số hoá đơn", "57194" in d["description"])
	dung("mô tả có tên nhà cung cấp", "GSM" in d["description"])


@ca("dòng dịch vụ: chưa chọn tài khoản thì không gán bừa vào dòng")
def _():
	d = md.dong_dich_vu("GSM", "57194", 1000)
	dung("không có tài khoản chi phí", "expense_account" not in d)
	dung("không có trung tâm chi phí", "cost_center" not in d)
	dung("vẫn có tên món để lưu được", bool(d["item_name"]))


@ca("dòng dịch vụ: tên món không được dài quá giới hạn của ERPNext")
def _():
	d = md.dong_dich_vu("C" * 300, "57194", 1000)
	dung("tên món cắt còn tối đa 140 ký tự", len(d["item_name"]) <= 140)


# ------------------------------------------- chua dong chiet khau bi cong

# Ba dong hang nhu may da tao ra tu hoa don GSM, thu gon lai cho de doc.
# Tong tho 2.415.426, trong do 2.270.370 la dong chiet khau bi cong nham dau.
GSM_DONG = [
	{"ten": "Cước phí vận chuyển", "tien": 120111},
	{"ten": "Phí nền tảng", "tien": 7667},
	{"ten": "Chiết khấu thương mại", "tien": 2270370},
]


@ca("chữa chiết khấu: số suy ra lệch quá xa số ghi trên hoá đơn thì không đụng vào")
def _():
	# Hai dong con lai cong duoc 127.778. Neu dau hoa don cung ghi 127.778 thi
	# chiet khau suy ra bang 0, trong khi hoa don ghi dong chiet khau 2.270.370.
	# Lech the la co gi khac dang sai, khong phai chuyen lam tron - khong duoc
	# tu y dung vao phieu, de cong chan lech o buoc ghi so no chan.
	dung("chênh 2,27 triệu thì bỏ qua",
		md.ke_hoach_sua_chiet_khau(GSM_DONG, GSM_CHI_TIET, 127778) is None)


@ca("chữa chiết khấu: dựng đúng kế hoạch khi con số hợp lý")
def _():
	# Dong con lai 127.778. Neu dau hoa don ghi truoc thue = 127.778 - 2.270.370
	# thi so am, vo ly. Dung bo so that: lay tong dong con lai tru dung chiet khau.
	dong = [
		{"ten": "Cước phí vận chuyển", "tien": 24338904},
		{"ten": "Chiết khấu thương mại", "tien": 2270370},
	]
	kh = md.ke_hoach_sua_chiet_khau(dong, GSM_CHI_TIET, 22068519)
	dung("có kế hoạch chữa", kh is not None)
	la("bỏ đúng một dòng", len(kh["bo"]), 1)
	la("bỏ đúng dòng chiết khấu", kh["bo"][0], 1)
	la("dòng còn lại", kh["con_lai"], 24338904)
	# 24.338.904 - 22.068.519 = 2.270.385, tuc dong chiet khau 2.270.370 cong
	# them 15d m-invoice lam tron tung dong. Nuot ca vao chiet khau thi tong
	# tren ERP khop tuyet doi voi hoa don.
	la("chiết khấu nuốt luôn phần làm tròn", kh["chiet_khau"], 2270385)
	dung("sau khi chữa thì khớp tuyệt đối",
		not md.lech_qua_nguong(kh["con_lai"] - kh["chiet_khau"], 22068519))


@ca("chữa chiết khấu: dòng ghi chú diễn giải cũng bị bỏ khỏi lưới")
def _():
	dong = [
		{"ten": "Cước phí vận chuyển", "tien": 24338904},
		{"ten": "Ghi chú, không tính tiền", "tien": 999999},
		{"ten": "Chiết khấu thương mại", "tien": 2270370},
	]
	kh = md.ke_hoach_sua_chiet_khau(dong, GSM_CHI_TIET, 22068519)
	dung("có kế hoạch chữa", kh is not None)
	la("bỏ hai dòng", len(kh["bo"]), 2)
	la("dòng còn lại không tính dòng ghi chú", kh["con_lai"], 24338904)


@ca("chữa chiết khấu: hoá đơn không có dòng chiết khấu thì không đụng vào")
def _():
	sach = [{"tchat": 1, "thtien": 100}, {"tchat": 5, "thtien": 200}]
	dung("không có tchat 3 hay 4 thì bỏ qua",
		md.ke_hoach_sua_chiet_khau(GSM_DONG, sach, 100) is None)
	dung("chi tiết rỗng thì bỏ qua",
		md.ke_hoach_sua_chiet_khau(GSM_DONG, [], 100) is None)


@ca("chữa chiết khấu: ghép theo tên không ra thì không đụng vào")
def _():
	# Hoa don hang hoa co ma mat hang that: ten dong la ten cua Mat hang chu
	# khong phai ten tren hoa don dien tu, ghep khong ra. Khong duoc doan mo.
	dong = [{"ten": "Bột mì số 13", "tien": 24338904}]
	dung("không ghép được dòng nào thì trả về None",
		md.ke_hoach_sua_chiet_khau(dong, GSM_CHI_TIET, 22068519) is None)


@ca("chữa chiết khấu: chiết khấu ra số âm là dấu hiệu sai, không đụng vào")
def _():
	dong = [
		{"ten": "Cước phí vận chuyển", "tien": 1000},
		{"ten": "Chiết khấu thương mại", "tien": 2270370},
	]
	dung("dòng còn lại nhỏ hơn tiền trước thuế thì bỏ qua",
		md.ke_hoach_sua_chiet_khau(dong, GSM_CHI_TIET, 22068519) is None)


@ca("chữa chiết khấu: đọc đúng tập tên theo tính chất")
def _():
	ck, gc = md.ten_theo_tinh_chat(GSM_CHI_TIET)
	dung("tên dòng chiết khấu vào tập chiết khấu", "Chiết khấu thương mại" in ck)
	dung("tên dòng ghi chú vào tập ghi chú", "Ghi chú, không tính tiền" in gc)
	dung("dòng hàng thường không vào tập nào", "Cước phí vận chuyển" not in (ck | gc))
	la("chi tiết rỗng ra hai tập rỗng", len(md.ten_theo_tinh_chat([])[0]), 0)
