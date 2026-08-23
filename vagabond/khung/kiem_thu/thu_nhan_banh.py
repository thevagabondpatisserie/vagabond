"""Kiem thu so NHAN BANH dau ngay cua cua hang (v288).

Anh Viet 23/08/2026: bo cai bang Excel ma D1 phai go tay roi chup gui Zalo.

Cac ca duoi day soi PHAN THUAN cua vagabond/nhan_banh.py: rut ma ngan tu ten
kho, dem so dot, gop ton dau voi cac lan nhan thanh bang, va goi y ton dau.

KHONG nap Frappe that. Chay duoc voi python3 tran, khong can requests, khong
can site.
"""

import ast
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _nb():
	from vagabond import nhan_banh

	return nhan_banh


# ------------------------------------------------------------- ma_ngan


@ca("ma_ngan() rút tên kho dài thành mã ngắn đặt được tên bản ghi")
def _():
	nb = _nb()
	la("kho D1", nb.ma_ngan("Kho D1 - TV"), "D1")
	la("kho tổng, bỏ dấu tiếng Việt", nb.ma_ngan("Kho tổng 307 - TV"), "TONG307")
	la("bếp Baker", nb.ma_ngan("Bếp Baker - TV"), "BEPBAKER")
	la("kho Sales Online", nb.ma_ngan("Kho Sales Online - TV"), "SALESONLINE")
	la("chuỗi rỗng", nb.ma_ngan(""), "")
	la("None", nb.ma_ngan(None), "")


@ca("ma_ngan() không bao giờ trả ra dấu cách, tên bản ghi Frappe không chứa được")
def _():
	nb = _nb()
	for ten in ("Kho D1 - TV", "Kho tổng 307 - TV", "Pastry - Thành phẩm - TV", "Bếp Baker - TV"):
		ra = nb.ma_ngan(ten)
		dung("không có dấu cách trong %r" % ra, " " not in ra)
		dung("không rỗng cho %r" % ten, len(ra) > 0)
		# Ten ban ghi di thang vao URL cua Desk. Con mot ky tu ngoai ASCII la
		# duong dan bien thanh chuoi phan tram khong ai doc duoc.
		dung("thuần ASCII cho %r" % ten, ra.isascii())


# ------------------------------------------------------------ dot_ke_tiep


@ca("dot_ke_tiep() đếm theo SỐ ĐỢT chứ không đếm số dòng")
def _():
	# Bay that: bep giao mot dot muoi mon la muoi dong nhung van la dot 1.
	# Dem so dong thi lan giao sau se thanh dot 11.
	nb = _nb()
	la("chưa có dòng nào", nb.dot_ke_tiep([]), 1)
	la("None", nb.dot_ke_tiep(None), 1)
	mot_dot_muoi_mon = [{"dot": 1, "ma_hang": "M%d" % i} for i in range(10)]
	la("mười món cùng đợt 1 thì đợt sau là 2", nb.dot_ke_tiep(mot_dot_muoi_mon), 2)
	la("đã có đợt 3 thì đợt sau là 4",
		nb.dot_ke_tiep([{"dot": 1}, {"dot": 3}, {"dot": 2}]), 4)


# --------------------------------------------------------------- gop_bang


@ca("gộp bảng: tồn đầu cộng các đợt ra đúng số ĐANG CÓ")
def _():
	nb = _nb()
	dong, so_dot = nb.gop_bang(
		[{"ma_hang": "A", "ten_banh": "Croissant", "so_luong": 24}],
		[
			{"ma_hang": "A", "ten_banh": "Croissant", "so_luong": 14, "dot": 1},
			{"ma_hang": "A", "ten_banh": "Croissant", "so_luong": 6, "dot": 2},
		],
	)
	la("gộp còn một dòng", len(dong), 1)
	la("tồn đầu", dong[0]["ton_dau"], 24)
	la("tổng nhận", dong[0]["tong_nhan"], 20)
	la("đang có", dong[0]["tong_co"], 44)
	la("hai đợt", so_dot, 2)
	la("đợt 1", dong[0]["cac_dot"]["1"], 14)
	la("đợt 2", dong[0]["cac_dot"]["2"], 6)


@ca("gộp bảng: món chỉ có tồn đầu, chưa nhận đợt nào, vẫn phải hiện ra")
def _():
	# Mon con ton ma sang nay bep khong giao thi van phai nam trong bang,
	# vi quay van ban duoc no. Bo di la bao thieu hang.
	nb = _nb()
	dong, so_dot = nb.gop_bang([{"ma_hang": "B", "ten_banh": "Tart", "so_luong": 6}], [])
	la("vẫn có dòng", len(dong), 1)
	la("đang có bằng tồn đầu", dong[0]["tong_co"], 6)
	la("chưa đợt nào", so_dot, 0)


@ca("gộp bảng: món mới giao lần đầu, chưa có tồn đầu, tồn đầu là 0 chứ không lỗi")
def _():
	nb = _nb()
	dong, _sd = nb.gop_bang([], [{"ma_hang": "C", "ten_banh": "Focaccia", "so_luong": 5, "dot": 1}])
	la("một dòng", len(dong), 1)
	la("tồn đầu 0", dong[0]["ton_dau"], 0)
	la("đang có 5", dong[0]["tong_co"], 5)


@ca("gộp bảng: hai lần ghi cùng món cùng đợt thì CỘNG chứ không đè")
def _():
	# Bep giao thieu roi bu them trong cung dot: hai dong cung dot 1. Neu de
	# thi con so bi nuot mat ma khong ai biet.
	nb = _nb()
	dong, _sd = nb.gop_bang([], [
		{"ma_hang": "D", "ten_banh": "Danish", "so_luong": 10, "dot": 1},
		{"ma_hang": "D", "ten_banh": "Danish", "so_luong": 4, "dot": 1},
	])
	la("đợt 1 cộng lại", dong[0]["cac_dot"]["1"], 14)
	la("tổng nhận", dong[0]["tong_nhan"], 14)


@ca("gộp bảng: dòng thiếu mã hàng bị bỏ, không đẻ dòng rác")
def _():
	nb = _nb()
	dong, _sd = nb.gop_bang([{"ma_hang": "", "so_luong": 9}], [{"ma_hang": None, "so_luong": 3, "dot": 1}])
	la("không dòng nào", len(dong), 0)
	la("rỗng hết", nb.gop_bang([], []), ([], 0))
	la("None cũng chịu được", nb.gop_bang(None, None), ([], 0))


@ca("gộp bảng: đợt để trống hiểu là đợt 1, không rơi vào đợt 0")
def _():
	nb = _nb()
	dong, so_dot = nb.gop_bang([], [{"ma_hang": "E", "ten_banh": "E", "so_luong": 3}])
	la("vào đợt 1", dong[0]["cac_dot"].get("1"), 3)
	la("số đợt là 1", so_dot, 1)


@ca("gộp bảng: xếp theo tên món cho dễ dò mắt")
def _():
	nb = _nb()
	dong, _sd = nb.gop_bang([], [
		{"ma_hang": "X", "ten_banh": "Yuzu Apple", "so_luong": 1, "dot": 1},
		{"ma_hang": "Y", "ten_banh": "Brioche", "so_luong": 1, "dot": 1},
		{"ma_hang": "Z", "ten_banh": "Croissant", "so_luong": 1, "dot": 1},
	])
	la("thứ tự theo tên", [d["ten_banh"] for d in dong], ["Brioche", "Croissant", "Yuzu Apple"])


@ca("gộp bảng KHÔNG sửa các dòng đầu vào")
def _():
	nb = _nb()
	ton = [{"ma_hang": "A", "ten_banh": "A", "so_luong": 5}]
	dong = [{"ma_hang": "A", "ten_banh": "A", "so_luong": 3, "dot": 1}]
	nb.gop_bang(ton, dong)
	la("tồn gốc còn nguyên", ton[0]["so_luong"], 5)
	la("dòng gốc còn nguyên", dong[0]["so_luong"], 3)


# ----------------------------------------------------------- goi_y_ton_dau


@ca("gợi ý tồn đầu lấy đúng số ĐANG CÓ của hôm qua")
def _():
	nb = _nb()
	hom_qua, _sd = nb.gop_bang(
		[{"ma_hang": "A", "ten_banh": "A", "so_luong": 24}],
		[{"ma_hang": "A", "ten_banh": "A", "so_luong": 14, "dot": 1}],
	)
	la("gợi ý bằng tồn đầu cộng nhận", nb.goi_y_ton_dau(hom_qua), {"A": 38})
	la("bảng rỗng", nb.goi_y_ton_dau([]), {})
	la("None", nb.goi_y_ton_dau(None), {})


# ---------------------------------------------------------------- hang rao


@ca("mô đun sổ nhận bánh KHÔNG đụng tới tồn kho hay bút toán của ERPNext")
def _():
	# Day la loi hua chinh cua ban nay voi anh Viet: so ghi rieng, khong sinh
	# but toan vao 632, khong doi ton kho. Ca kiem doc thang ma nguon chu
	# khong tin vao loi hua.
	src = io.open(os.path.join(GOI, "nhan_banh.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	cam = ("Stock Entry", "Stock Reconciliation", "Purchase Receipt", "Delivery Note", "Bin")
	hong = []
	for nut in ast.walk(cay):
		if isinstance(nut, ast.Constant) and isinstance(nut.value, str):
			if nut.value in cam:
				hong.append("dòng %d nhắc doctype %s" % (nut.lineno, nut.value))
	la("không chạm doctype kho nào", hong, [])


@ca("mô đun sổ nhận bánh không kéo theo thư viện mạng, CI tay không vẫn chạy")
def _():
	# Ngay 20/08 CI do 3 ca vi mot ca kiem keo theo requests qua duong
	# nop_quy -> cong_no -> ban_hang. Ca nay chot rang nhan_banh khong dam
	# vao bay do: moi import nang deu nam TRONG ham chu khong o dau tep.
	src = io.open(os.path.join(GOI, "nhan_banh.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	tren_cung = []
	for nut in cay.body:
		if isinstance(nut, ast.Import):
			tren_cung += [a.name for a in nut.names]
		elif isinstance(nut, ast.ImportFrom):
			tren_cung.append(nut.module or "")
	nang = [t for t in tren_cung if t.split(".")[0] in ("requests", "vagabond")]
	la("đầu tệp không import mô đun nghiệp vụ nào", nang, [])


@ca("mọi cửa ghi của sổ nhận bánh đều đi qua chốt quyền")
def _():
	# Bo sot _quyen() o mot cua la ai co duong dan cung ghi duoc vao so.
	src = io.open(os.path.join(GOI, "nhan_banh.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	thieu = []
	for nut in cay.body:
		if not isinstance(nut, ast.FunctionDef):
			continue
		co_wl = any(
			(isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "whitelist")
			or getattr(d, "attr", "") == "whitelist"
			for d in nut.decorator_list
		)
		if not co_wl:
			continue
		goi_quyen = any(
			isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_quyen"
			for n in ast.walk(nut)
		)
		if not goi_quyen:
			thieu.append(nut.name)
	la("không cửa nào quên chốt quyền", thieu, [])


@ca("màn Nhận bánh có thẻ trên trang chủ và bấm được")
def _():
	# Cong cong doan 7 soi the -> man hinh, nhung the moi ma quen dinh tuyen
	# thi cong do bat duoc. Ca nay chot them phia man hinh.
	tc = io.open(os.path.join(GOI, "public", "js", "bep", "02-trang-chu.js"), encoding="utf-8").read()
	man = io.open(os.path.join(GOI, "public", "js", "bep", "31-nhan-banh.js"), encoding="utf-8").read()
	dung("có thẻ trên trang chủ", "'NBANH'" in tc)
	dung("có dòng định tuyến", "k === 'NBANH'" in tc)
	dung("có hàm màn hình", "function scrNhanBanh" in man)
	dung("gọi đúng cửa bảng", "vagabond.nhan_banh.bang" in man)
	dung("gọi đúng cửa ghi nhận", "vagabond.nhan_banh.ghi_nhan" in man)
