"""Kiem thu phep goi y so cho phieu YCSX (v285).

Anh Viet 23/08/2026: *"goi y cac mau can lam YCSX cho bep va so luong"*.

Cac ca duoi day soi PHAN THUAN cua vagabond/goi_y_ycsx.py: doi dau o CO THE
BAN, gop ba nguon theo ma hang, va tach mon khong co ma ra khoi mon co ma.

KHONG nap Frappe that. Chay duoc voi python3 tran, khong can requests,
khong can site.
"""

import ast
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _gy():
	from vagabond import goi_y_ycsx

	return goi_y_ycsx


# ------------------------------------------------------------ thieu_tu_o


@ca("thieu_tu_o() đổi dấu ô CÓ THỂ BÁN, dư hàng thì trả 0 chứ không trả số âm")
def _():
	gy = _gy()
	la("thiếu 22", gy.thieu_tu_o(-22), 22)
	la("vừa đủ", gy.thieu_tu_o(0), 0)
	la("dư 5 thì không gợi ý gì", gy.thieu_tu_o(5), 0)
	la("ô rỗng", gy.thieu_tu_o(None), 0)
	la("chuỗi số", gy.thieu_tu_o("-3"), 3)


@ca("bếp đã lên số rồi thì lần bấm gợi ý sau không ra số gấp đôi")
def _():
	# Bay lon nhat cua tinh nang nay: bam goi y hai lan trong mot ngay.
	# Vi phep tru dua tren CO THE BAN - cot da tru san o "sx" - nen sau khi
	# bep len 22 cai, o do ve 0 va lan bam thu hai khong con goi y gi.
	gy = _gy()
	da_dat, ton, sx_truoc = 25, 3, 0
	la("lần đầu thiếu 22", gy.thieu_tu_o(ton + sx_truoc - da_dat), 22)
	sx_sau = 22
	la("lần hai không còn thiếu", gy.thieu_tu_o(ton + sx_sau - da_dat), 0)


# --------------------------------------------------------- cau giai thich


@ca("câu giải thích của bảng theo NGÀY đọc ra đúng các số đã cộng trừ")
def _():
	gy = _gy()
	cau = gy.giai_thich_ngay({
		"da_dat": 25, "phat_sinh": 2, "cho_chot": 1, "don_khac": 0,
		"ton_cu": 1, "ton_d2": 2, "ton_d1": 0, "sx": 4,
	})
	dung("có số đã đặt", "Đã đặt 25" in cau)
	dung("có phát sinh", "phát sinh 2" in cau)
	dung("có chờ chốt", "chờ chốt 1" in cau)
	dung("kênh khác bằng 0 thì không nhắc tới", "kênh khác" not in cau)
	dung("gộp ba ô tồn thành một số 3", "trừ tồn 3" in cau)
	dung("nói rõ bếp đã lên", "trừ bếp đã lên 4" in cau)


@ca("câu giải thích của bảng theo MÙA dùng đúng tên cột của mùa vụ")
def _():
	gy = _gy()
	cau = gy.giai_thich_mua({"da_dat": 40, "ton_dau": 10, "bep_lam": 5, "cho_chot": 0})
	dung("có số đã đặt", "Đã đặt 40" in cau)
	dung("tồn đầu", "trừ tồn đầu 10" in cau)
	dung("bếp đã lên", "trừ bếp đã lên 5" in cau)
	dung("chờ chốt bằng 0 thì im", "chờ chốt" not in cau)


# ------------------------------------------------------------- gop_theo_ma


@ca("gộp theo mã: một món nằm ở hai nguồn thì cộng số và giữ cả hai dòng lý do")
def _():
	gy = _gy()
	ra = gy.gop_theo_ma([
		{"ma_hang": "BAWC00098", "ten_banh": "Tiramisu", "hinh": "", "can": 20,
			"nguon": {"ma": "ngay", "nhan": "Kiểm bánh ngày 24/08", "so": 20}},
		{"ma_hang": "BAWC00098", "ten_banh": "Tiramisu", "hinh": "/t.png", "can": 6,
			"nguon": {"ma": "hop_dong", "nhan": "HĐ 07", "so": 6}},
	])
	la("gộp còn một dòng", len(ra), 1)
	la("số cộng lại", ra[0]["can"], 26)
	la("giữ đủ hai nguồn", len(ra[0]["nguon"]), 2)
	la("hình rỗng ở nguồn đầu thì lấy hình của nguồn sau", ra[0]["hinh"], "/t.png")


@ca("gộp theo mã: xếp món thiếu nhiều lên trước, bằng nhau thì theo tên")
def _():
	gy = _gy()
	ra = gy.gop_theo_ma([
		{"ma_hang": "B", "ten_banh": "Bơ", "can": 5, "nguon": {}},
		{"ma_hang": "C", "ten_banh": "Cam", "can": 30, "nguon": {}},
		{"ma_hang": "A", "ten_banh": "Ai", "can": 5, "nguon": {}},
	])
	la("thứ tự", [x["ma_hang"] for x in ra], ["C", "A", "B"])


@ca("gộp theo mã: dòng thiếu mã hàng bị bỏ, không đẻ dòng rác")
def _():
	gy = _gy()
	la("bỏ dòng rỗng mã", len(gy.gop_theo_ma([{"ma_hang": "", "can": 9}])), 0)
	la("danh sách rỗng", gy.gop_theo_ma([]), [])
	la("None cũng chịu được", gy.gop_theo_ma(None), [])


@ca("gộp theo mã KHÔNG sửa các dòng đầu vào")
def _():
	gy = _gy()
	vao = [{"ma_hang": "X", "ten_banh": "X", "can": 3, "nguon": {"ma": "ngay"}}]
	gy.gop_theo_ma(vao)
	la("dòng gốc còn nguyên", vao[0]["can"], 3)
	dung("nguồn gốc vẫn là dict chứ không thành list", isinstance(vao[0]["nguon"], dict))


# ------------------------------------------------------- tach_dong_bao_gia


@ca("tách dòng báo giá: món có mã đi một đường, món không mã đi đường khác")
def _():
	gy = _gy()
	co, khong = gy.tach_dong_bao_gia([
		{"loai": "Món", "ma_mon": "BAWC00098", "ten_mon": "Tiramisu", "so_luong": 3},
		{"loai": "Món", "ma_mon": "", "ten_mon": "Set teabreak 30 khách", "so_luong": 1},
		{"loai": "Phí", "ma_mon": "", "ten_mon": "Phí giao hàng", "so_luong": 1},
	])
	la("một món có mã", len(co), 1)
	la("mã đúng", co[0]["ma_mon"], "BAWC00098")
	la("một món không mã", len(khong), 1)
	la("tên món không mã giữ nguyên", khong[0]["ten_mon"], "Set teabreak 30 khách")


@ca("tách dòng báo giá: dòng PHÍ không bao giờ rơi vào danh sách cần làm")
def _():
	# Phi giao hang, phi setup khong phai mon an. De lot vao muc "khong co
	# ma" la Loan Anh phai doc mot danh sach co ca phi van chuyen trong do.
	gy = _gy()
	co, khong = gy.tach_dong_bao_gia([
		{"loai": "Phí", "ten_mon": "Phí setup", "so_luong": 1},
		{"loai": "Phí", "ma_mon": "PHI001", "ten_mon": "Phí giao", "so_luong": 1},
	])
	la("không có món nào có mã", len(co), 0)
	la("không có món nào không mã", len(khong), 0)


@ca("tách dòng báo giá: số lượng lẻ làm tròn lên số nguyên cái")
def _():
	gy = _gy()
	co, _k = gy.tach_dong_bao_gia([
		{"loai": "Món", "ma_mon": "A", "ten_mon": "A", "so_luong": 2.0},
		{"loai": "Món", "ma_mon": "B", "ten_mon": "B", "so_luong": 2.6},
	])
	la("số chẵn", co[0]["so_luong"], 2)
	la("số lẻ", co[1]["so_luong"], 3)


@ca("tách dòng báo giá: dòng trống trơn không sinh mục nào")
def _():
	gy = _gy()
	co, khong = gy.tach_dong_bao_gia([{"loai": "Món", "ma_mon": "", "ten_mon": "", "so_luong": 5}])
	la("không mã không tên thì bỏ", (len(co), len(khong)), (0, 0))


# ------------------------------------------------------------ hang rao


@ca("mô đun gợi ý CHỈ ĐỌC: không có lệnh ghi hay xoá nào trong mã nguồn")
def _():
	# Man goi y ma ghi duoc vao he la sai thiet ke: sales bam thu de xem so,
	# khong ai ngo la he vua thay doi cai gi do. Ca kiem nay chot dieu do
	# bang cach doc ma nguon chu khong tin vao loi hua.
	src = io.open(os.path.join(GOI, "goi_y_ycsx.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	cam = {"save", "insert", "delete", "submit", "set_value", "commit", "db_set"}
	hong = []
	for nut in ast.walk(cay):
		if not isinstance(nut, ast.Call):
			continue
		f = nut.func
		ten = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
		if ten in cam:
			hong.append("dòng %d gọi %s" % (nut.lineno, ten))
	la("không có lệnh ghi nào", hong, [])


@ca("mô đun gợi ý không kéo theo thư viện mạng, CI tay không vẫn chạy được")
def _():
	# Ngay 20/08 CI do 3 ca vi mot ca kiem keo theo requests qua duong
	# nop_quy -> cong_no -> ban_hang. Ca nay chot rang goi_y_ycsx khong dam
	# vao bay do: moi import nang deu nam TRONG ham chu khong o dau tep.
	src = io.open(os.path.join(GOI, "goi_y_ycsx.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	tren_cung = []
	for nut in cay.body:
		if isinstance(nut, ast.Import):
			tren_cung += [a.name for a in nut.names]
		elif isinstance(nut, ast.ImportFrom):
			tren_cung.append(nut.module or "")
	nang = [t for t in tren_cung if t.split(".")[0] in ("requests", "vagabond")]
	la("đầu tệp không import mô đun nghiệp vụ nào", nang, [])


@ca("màn Chọn hàng hoá có nút gợi ý và chỉ hiện với phiếu YCSX")
def _():
	# Nut nay nam canh nut "Lay tu mau da luu". Neu phien khac doi ten id
	# hoac bo dieu kien Manufacture thi ca nay do, vi bam goi y tren phieu
	# mua hang se hoi so banh trung thu - vo nghia.
	p = os.path.join(GOI, "public", "js", "bep", "04-tao-phieu.js")
	src = io.open(p, encoding="utf-8").read()
	dung("có nút gợi ý", "id=\"p2goi\"" in src or "id='p2goi'" in src)
	dung("gắn tay bấm cho nút", "bgy.onclick" in src)
	dung("có hàm dựng bảng gợi ý", "function goiYSheet" in src)
	dung("chỉ dựng nút khi là phiếu sản xuất", "d.type === 'Manufacture'" in src)
	dung("gọi đúng cửa của máy chủ", "vagabond.goi_y_ycsx.goi_y" in src)


@ca("bước Tiếp tục mang theo số gợi ý chứ không đặt lại về 1")
def _():
	# Bay that: buildItems() lay qty tu req, ma p2next truoc day chi truyen
	# {item_code}. Goi y ra 22 cai ma phieu ghi 1 cai thi tinh nang nay vo
	# nghia, va khong lop nao khac bat duoc.
	p = os.path.join(GOI, "public", "js", "bep", "04-tao-phieu.js")
	src = io.open(p, encoding="utf-8").read()
	dung("có bảng số gợi ý theo mã", "pick.sl" in src)
	dung("p2next truyền số theo mã", "qty: pick.sl[c]" in src)
