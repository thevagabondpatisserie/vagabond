"""Kiem thu phep GHEP HOP TU RUOT (v294).

Vi sao co tep nay
-----------------
Anh Viet 24/08/2026, nhin man Kiem banh theo mua ngay 24/08:

    *"so ban duoc ma de la 1557 la sai ban chat roi, so ban duoc xem o tab
    Co the ban la so hop con du co the ban duoc trong ngay hom do ma thoi,
    tinh tu may cai banh san xuat ben duoi, ghep duoc tong bao nhieu hop,
    roi tru di cac so da dat."*

So that hom do la 15. Man hinh bay 1.557, lech 1.542 hop.

Nguyen nhan: `ghep_duoc_tu_ruot` bo qua MOI ruot mang co "khong dat tran".
Luc dat co do (18/08/2026) ly do la that - banh 80g chua co lo rieng nen
nguon cung bang 0, de vao phep lay nho nhat thi moi hop deu ra 0. Nhung tu
khi bep nhap san luong theo tung ngay thi nhung banh do CO so that, va bo
qua chung la bo qua dung cai rang buoc chat nhat.

Luat moi tach hai chuyen ma ban cu gop lam mot:

    chua khai nguon cung -> KHONG BIET -> bo qua, va dem vao ruot_thieu_nguon
    da khai nguon cung   -> BIET ro    -> chan, du con 0 hay am

Cac ca duoi day deu goi phep THUAN, khong can Frappe, khong can site.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _mv():
	from vagabond import mua_vu

	return mua_vu


# Hinh that cua HOP MOONGARDEN: 5 ruot, moi ruot mot cai.
RUOT = ["BASS00050", "BASS00051", "BASS00052", "BASS00053", "BASS00056"]
DM_MG = [{"ma_hop": "BASS00038", "ma_banh": r, "so_luong": 1} for r in RUOT]
KHONG_TRAN = set(RUOT)

# So that doc tu site ngay 24/08/2026.
CON_2408 = {
	"BASS00050": 16, "BASS00051": 16, "BASS00052": 16, "BASS00053": 16,
	"BASS00056": 15,
}
DONG_2408 = [
	{"ma_hang": "BASS00050", "san_xuat": 1771, "nha_in_giao": 0},
	{"ma_hang": "BASS00051", "san_xuat": 1771, "nha_in_giao": 0},
	{"ma_hang": "BASS00052", "san_xuat": 1771, "nha_in_giao": 0},
	{"ma_hang": "BASS00053", "san_xuat": 1771, "nha_in_giao": 0},
	{"ma_hang": "BASS00056", "san_xuat": 1658, "nha_in_giao": 0},
	{"ma_hang": "BASS00038", "san_xuat": 0, "nha_in_giao": 1600},
]


@ca("ca thật MOONGARDEN 24/08: vỏ hộp 1.557 mà ruột chỉ ghép được 15")
def _():
	mv = _mv()
	co_nguon = mv.ma_co_nguon_cung(DONG_2408)
	ghep = mv.ghep_duoc_tu_ruot(DM_MG, CON_2408, KHONG_TRAN, co_nguon)
	la("ghép được đúng bằng ruột ít nhất", ghep.get("BASS00038"), 15)
	la("bán được thật là 15 chứ không phải 1.557",
	   mv.con_hop_thuc_te(1557, ghep.get("BASS00038")), 15)
	la("không ruột nào bị bỏ qua", mv.ruot_thieu_nguon(DM_MG, KHONG_TRAN, co_nguon), {})


@ca("ruột mang cờ không đặt trần mà ĐÃ khai nguồn cung thì vẫn chặn được hộp")
def _():
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1}]
	co_nguon = mv.ma_co_nguon_cung([{"ma_hang": "LE1", "san_xuat": 900, "nha_in_giao": 0}])
	ghep = mv.ghep_duoc_tu_ruot(dm, {"LE1": 7}, {"LE1"}, co_nguon)
	la("cờ không đặt trần không còn miễn cho ruột này", ghep.get("HOPA"), 7)


@ca("ruột CHƯA khai nguồn cung thì vẫn bị bỏ qua, và được đếm ra")
def _():
	# Day la cai bay cu, van phai chua: ruot chua ai khai gi ca thi nguon cung
	# bang 0, de vao phep lay nho nhat la moi hop ra 0 va ca mua bi chan sai.
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1}]
	ghep = mv.ghep_duoc_tu_ruot(dm, {"LE1": 0}, {"LE1"}, set())
	dung("không ràng buộc nào, trả về rỗng", ghep == {})
	la("chỉ vỏ hộp chặn được", mv.con_hop_thuc_te(300, ghep.get("HOPA")), 300)
	la("và đếm được 1 ruột thiếu nguồn", mv.ruot_thieu_nguon(dm, {"LE1"}, set()),
	   {"HOPA": 1})


@ca("ruột đã khai nguồn mà bán hết thì hộp về 0, không rơi lại về số vỏ hộp")
def _():
	# Day chinh la cho ma ban cu ban lo: het ruot ma van bay so vo hop.
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1}]
	co_nguon = mv.ma_co_nguon_cung([{"ma_hang": "LE1", "san_xuat": 500, "nha_in_giao": 0}])
	ghep = mv.ghep_duoc_tu_ruot(dm, {"LE1": 0}, {"LE1"}, co_nguon)
	la("ghép được 0", ghep.get("HOPA"), 0)
	la("bán được thật 0 dù vỏ hộp còn 300", mv.con_hop_thuc_te(300, ghep.get("HOPA")), 0)


@ca("hộp nửa biết nửa không thì vẫn tính, nhưng phải đếm ra phần chưa biết")
def _():
	mv = _mv()
	dm = [
		{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1},
		{"ma_hop": "HOPA", "ma_banh": "LE2", "so_luong": 1},
	]
	co_nguon = mv.ma_co_nguon_cung([{"ma_hang": "LE1", "san_xuat": 900, "nha_in_giao": 0}])
	ghep = mv.ghep_duoc_tu_ruot(dm, {"LE1": 40, "LE2": 0}, {"LE1", "LE2"}, co_nguon)
	la("tính theo ruột đã biết", ghep.get("HOPA"), 40)
	la("và nói rõ còn 1 ruột chưa biết",
	   mv.ruot_thieu_nguon(dm, {"LE1", "LE2"}, co_nguon), {"HOPA": 1})


@ca("nguồn cung tính cả hai ô, bếp làm và nhà in giao")
def _():
	mv = _mv()
	co = mv.ma_co_nguon_cung([
		{"ma_hang": "A", "san_xuat": 0, "nha_in_giao": 0},
		{"ma_hang": "B", "san_xuat": 5, "nha_in_giao": 0},
		{"ma_hang": "C", "san_xuat": 0, "nha_in_giao": 9},
		{"ma_hang": "", "san_xuat": 9, "nha_in_giao": 9},
	])
	la("chỉ mã có số mới được coi là đã khai", sorted(co), ["B", "C"])


@ca("ruột không mang cờ không đặt trần thì luật cũ giữ nguyên")
def _():
	# Ruot binh thuong chua bao gio duoc mien, va khong duoc doi.
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 2}]
	la("hai cái một hộp, còn 9 thì ghép được 4",
	   mv.ghep_duoc_tu_ruot(dm, {"LE1": 9}, set(), set()).get("HOPA"), 4)


@ca("phép ghép đi qua cả đường theo ngày, không chỉ đường cả mùa")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-08-24"],
		{"BASS00038": 1600, "BASS00050": 71, "BASS00051": 71, "BASS00052": 71,
		 "BASS00053": 71, "BASS00056": 58},
		{},
		{("BASS00038", "2026-08-24"): {"da_dat": 41, "phat_sinh": 2}},
		DM_MG,
	)
	co_nguon = mv.ma_co_nguon_cung(DONG_2408)
	o = mv.ghep_theo_ngay(ra["2026-08-24"], DM_MG, KHONG_TRAN, co_nguon)
	h = o["BASS00038"]
	la("vỏ hộp còn 1.557", h["co_the_ban"], 1557)
	la("ruột ghép được 15", h["ghep_duoc"], 15)
	la("bán được thật 15", h["con_thuc_te"], 15)
	la("không còn bị coi là không ràng buộc", h["ruot_khong_rang_buoc"], 0)
	la("không ruột nào thiếu nguồn", h["ruot_thieu_nguon"], 0)
