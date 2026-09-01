# -*- coding: utf-8 -*-
"""Một đơn trả bằng nhiều phương thức, và cửa tải tệp của phiếu hoàn tiền.

Hai việc anh Việt giao 01/09/2026:

1. Khách trả một đơn bằng hai đường (chuyển khoản trước, tới cửa hàng đưa
   nốt tiền mặt). Đơn 92857 ngày 31/08 là ví dụ thật: 2.000.000 tiền mặt
   cộng 225.000 quẹt thẻ. Ô `vgb_pt_thanh_toan` chỉ chứa được một tên nên
   sổ ghi cả 2.225.000 vào tiền mặt, két cuối ca lệch đúng 225.000.

2. Sales, thu ngân, quản lý bấm vào uỷ nhiệm chi trên màn phiếu hoàn tiền
   thì Frappe trả 403 Forbidden, vì tệp đính trên Payment Entry mà họ
   không có quyền đọc doctype đó.
"""

import io
import os

from vagabond import thanh_toan_nhieu as ttn
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


# Dung so that cua don 92857 ngay 31/08/2026 lam moc cho ca bo kiem.
DON = [
	{"pt": "Tiền mặt", "so_tien": 2000000},
	{"pt": "Thẻ - Payoo", "so_tien": 225000},
]
TONG = 2225000


# ---------------------------------------------------- gom và chuẩn hoá dòng


@ca("gom dòng: bỏ dòng thiếu phương thức hoặc số tiền không dương")
def _():
	ra = ttn.gom_dong([
		{"pt": "", "so_tien": 100},
		{"pt": "Tiền mặt", "so_tien": 0},
		{"pt": "Tiền mặt", "so_tien": -5},
		{"pt": "Tiền mặt", "so_tien": 100},
	])
	la("chỉ còn một dòng", len(ra), 1)
	la("đúng số", ra[0]["so_tien"], 100.0)


@ca("hai dòng cùng phương thức thì cộng lại thành một")
def _():
	# Thu ngan go hai lan "Tien mat" la chuyen thuong. De hai dong thi man
	# chot ca dem hai lan mot ten, bang so trong nhu co loi.
	ra = ttn.gom_dong([
		{"pt": "Tiền mặt", "so_tien": 100},
		{"pt": "Tiền mặt", "so_tien": 50},
	])
	la("một dòng", len(ra), 1)
	la("cộng đủ", ra[0]["so_tien"], 150.0)


@ca("gom dòng giữ mã tham chiếu ĐẦU TIÊN, không ghép hai mã")
def _():
	# Ghep hai ma lai thanh mot chuoi thi phep kiem dinh dang ma o
	# ban_hang.py khong nhan ra nua.
	ra = ttn.gom_dong([
		{"pt": "Chuyển khoản", "so_tien": 100, "ma_tham_chieu": "AAA"},
		{"pt": "Chuyển khoản", "so_tien": 50, "ma_tham_chieu": "BBB"},
	])
	la("giữ mã đầu", ra[0]["ma_tham_chieu"], "AAA")


@ca("người gõ tay một dòng thì cả nhóm dòng đó hết là của máy")
def _():
	ra = ttn.gom_dong([
		{"pt": "Tiền mặt", "so_tien": 100, "do_may": 1},
		{"pt": "Tiền mặt", "so_tien": 50, "do_may": 0},
	])
	la("cờ máy tắt", ra[0]["do_may"], 0)


# ------------------------------------------------------- phương thức chính


@ca("phương thức chính là dòng có số tiền LỚN NHẤT")
def _():
	la("tiền mặt lớn hơn", ttn.chinh_cua(DON), "Tiền mặt")
	la("đảo thứ tự vẫn thế", ttn.chinh_cua(list(reversed(DON))), "Tiền mặt")


@ca("bằng nhau thì lấy dòng ĐỨNG TRƯỚC, không lấy theo bảng chữ cái")
def _():
	# Thu tu dong la thu tu khach tra. Chon theo chu cai thi cung mot don
	# nhap lai co the ra phuong thuc chinh khac, ma o do dang la can cu cho
	# chot ca va hoa don dien tu.
	d = [{"pt": "Tiền mặt", "so_tien": 500}, {"pt": "Chuyển khoản", "so_tien": 500}]
	la("lấy dòng trước", ttn.chinh_cua(d), "Tiền mặt")


@ca("không có dòng nào thì không có phương thức chính")
def _():
	la("rỗng", ttn.chinh_cua([]), "")


# ------------------------------------------------------------ khớp tổng đơn


@ca("các dòng phải cộng đủ tổng đơn")
def _():
	la("khớp", ttn.khop_tong(DON, TONG), True)
	la("thiếu 225.000", ttn.khop_tong(DON, 2450000), False)
	la("thừa", ttn.khop_tong(DON, 2000000), False)


@ca("lệch nói rõ thừa hay thiếu bằng dấu")
def _():
	la("ghi thừa thì dương", ttn.lech(DON, 2000000), 225000.0)
	la("ghi thiếu thì âm", ttn.lech(DON, 2450000), -225000.0)


@ca("số lẻ do thuế 8% không bị coi là lệch")
def _():
	# grand_total di qua phep tinh thue nen hay ra 2224999,9996. Chan mot
	# to vi lech 0,0004 dong la chan nham.
	d = [{"pt": "Tiền mặt", "so_tien": 2224999.9996}]
	la("vẫn khớp", ttn.khop_tong(d, TONG), True)


# --------------------------------------------------------- chia cho chốt ca


@ca("chốt ca chia đúng từng phương thức, không dồn cả tờ vào một tên")
def _():
	# Day la con so lam ket cuoi ca khop. Don ca to vao "Tien mat" thi ket
	# lech dung 225.000 ma khong ai truy ra, vi so noi la tien mat.
	ra = ttn.tach_theo_pt(DON, TONG)
	la("tiền mặt", ra.get("Tiền mặt"), 2000000.0)
	la("thẻ", ra.get("Thẻ - Payoo"), 225000.0)


@ca("không có dòng nào thì trả rỗng để người gọi lùi về cách cũ")
def _():
	la("rỗng", ttn.tach_theo_pt([], TONG), {})


@ca("dòng lệch tổng đơn thì vẫn chia đủ đúng tổng đơn")
def _():
	# Con so phai khop voi TO HOA DON chu khong khop voi bang nhap tay.
	ra = ttn.tach_theo_pt(DON, 4450000)
	la("cộng lại đúng tổng đơn", round(sum(ra.values()), 2), 4450000.0)


@ca("chia theo tỷ lệ không làm rơi mất đồng lẻ")
def _():
	d = [{"pt": "A", "so_tien": 1}, {"pt": "B", "so_tien": 1}, {"pt": "C", "so_tien": 1}]
	ra = ttn.tach_theo_pt(d, 100)
	la("cộng lại vẫn đủ 100", round(sum(ra.values()), 2), 100.0)


# ------------------------------------------------------- mã gửi cơ quan thuế


@ca("vừa tiền mặt vừa chuyển khoản thì mã thuế là TM/CK")
def _():
	# m-invoice da co san ma do, xem MA_THUE ben pt_thanh_toan.py. Truoc day
	# khong bao gio dung toi vi mot don chi mang duoc mot phuong thuc.
	la("trộn", ttn.ma_thue_cua(DON, {"Tiền mặt": "TM", "Thẻ - Payoo": "CK"}), "TM/CK")


@ca("cùng một mã thì trả đúng mã đó, không tự đổi thành TM/CK")
def _():
	d = [{"pt": "Chuyển khoản", "so_tien": 1}, {"pt": "OnePay", "so_tien": 1}]
	la("đều CK", ttn.ma_thue_cua(d, {"Chuyển khoản": "CK", "OnePay": "CK"}), "CK")


@ca("thiếu mã thuế của một phương thức thì KHÔNG đoán, trả rỗng")
def _():
	# Gui sai ma sang co quan thue thi loi hien o ben do, khong hien tren
	# man cua minh.
	la("thiếu", ttn.ma_thue_cua(DON, {"Tiền mặt": "TM"}), "")


# ------------------------------------------------- phép thuần, không Frappe


@ca("mọi phép chia tiền là PHÉP THUẦN, không chạm Frappe")
def _():
	m = _py("thanh_toan_nhieu.py")
	dau = m.split("# ------------------------------------------------------- phần cần Frappe")[0]
	la("phần thuần không gọi frappe", "frappe." in dau, False)
	for ten in ("gom_dong", "chinh_cua", "tach_theo_pt", "khop_tong", "ma_thue_cua"):
		dung("có phép %s" % ten, ("def %s(" % ten) in dau)


# --------------------------------------------------------- nối vào hệ đang chạy


@ca("ô phương thức CŨ vẫn giữ, không bỏ đi")
def _():
	# O do co 77 cho doc trong 13 tep. Doi no thanh bang con la phai sua ca
	# 77 cho trong mot lan deploy, ma day la tien.
	m = _py("thanh_toan_nhieu.py")
	dung("nói rõ ô cũ luôn mang dòng lớn nhất", "def dat_pt_chinh(" in m)
	dung("kể tên các chỗ chưa đọc bảng con", "CHƯA đọc bảng con" in m)


@ca("hook đặt phương thức chính chạy SAU luật bán hàng cũ")
def _():
	# Dat truoc thi luat cu doc o phuong thuc luc no con la gia tri nguoi
	# go, roi bang con doi no ngay sau, thanh ra to di vao so mang mot
	# phuong thuc chua qua phep kiem nao.
	# Cat dung khoi Sales Invoice: hooks.py co nhieu doctype, moi cai mot
	# day "validate" rieng.
	m = _py("hooks.py")
	khoi = m.split('\t"Sales Invoice": {')[1].split("\n\t},")[0]
	doan = khoi.split('"validate": [')[1].split("],")[0]
	la("đứng sau kiem_truoc_khi_luu",
		doan.index("thanh_toan_nhieu.dat_pt_chinh") > doan.index("ban_hang.kiem_truoc_khi_luu"),
		True)


@ca("ghi sổ bị chặn khi các dòng không cộng đủ tổng đơn")
def _():
	m = _py("hooks.py")
	dung("có chốt ở before_submit", "vagabond.thanh_toan_nhieu.kiem_truoc_ghi_so" in m)
	t = _py("thanh_toan_nhieu.py")
	dung("chặn bằng throw", "def kiem_truoc_ghi_so(" in t and "frappe.throw(" in t)


@ca("chốt ca đọc bảng con, và KHÔNG đếm một tờ thành hai bill")
def _():
	# Mot to tra hai duong van la MOT bill. Dem hai lan thi tong so bill cua
	# ca lon hon so to that va thu ngan tuong minh sot phieu.
	m = _py("ca_quay.py")
	dung("gọi phép tách", "ttn.tach_theo_pt(" in m)
	dung("đếm bill theo phương thức chính", "so_bill[chinh] = so_bill.get(chinh, 0) + 1" in m)
	dung("tờ một phương thức vẫn đi đường cũ", "if not tach:" in m)


@ca("máy điền bảng từ Pancake nhưng KHÔNG đè lên tay người")
def _():
	m = _py("ban_hang.py")
	doan = m.split("def _dien_dong_thanh_toan(")[1].split("\ndef ")[0]
	dung("chỉ điền khi mọi dòng đang có đều của máy",
		'if dang_co and not all(cint(d.get("do_may")) for d in dang_co):' in doan)
	dung("lệch tổng thì bỏ qua cả bảng", "if not ttn.khop_tong(moi," in doan)


@ca("dòng Pancake dựng từ LỊCH SỬ giao dịch, không từ các ô tiền")
def _():
	# Cac o tien cua Pancake chong cheo nhau - `cod` gom ca tien hang lan
	# phi ship tuy cach khai - nen cong chung lai ra so khong khop tong don.
	m = _py("ban_hang.py")
	doan = m.split("def dong_thanh_toan_pancake(")[1].split("\ndef ")[0]
	dung("đọc lịch sử giao dịch", "_lich_su_thanh_toan(o)" in doan)
	la("không đọc ô cod", '"cod"' in doan, False)
	dung("một kênh không đoán ra tên thì bỏ cả bảng", "return []" in doan)
	dung("dưới hai kênh thì không dựng bảng", "if len(dong) >= 2 else []" in doan)


# -------------------------------------- việc 2: tải tệp phiếu hoàn tiền


@ca("tệp của phiếu hoàn tiền KHÔNG còn trỏ thẳng vào /private/files")
def _():
	# Uy nhiem chi dinh tren Payment Entry, Sales khong co quyen doc doctype
	# do nen Frappe tra 403 Forbidden.
	m = _js("40-phieu-hoan-huy.js")
	la("không dựng thẻ img trỏ vào url tệp", '<img src="\' + h(t.url)' in m, False)
	la("không còn thẻ a href tới url tệp", '<a href="\' + h(t.url)' in m, False)
	dung("đi qua cửa tai_tep", "vagabond.don_huy.tai_tep" in m)


@ca("cửa tải tệp kiểm tệp phải thuộc ĐÚNG phiếu hoàn tiền đó")
def _():
	# Chong doc chui: dua ma File cua phieu khac la bi tu choi, du ma do co
	# that trong he.
	m = _py("don_huy.py")
	doan = m.split("def tai_tep(")[1].split("\n@frappe.whitelist")[0]
	dung("kiểm quyền trước", "_quyen_xem_phieu()" in doan)
	dung("chỉ nhận tệp của hồ sơ này", 'attached_to_name": ho_so' in doan)
	dung("hoặc của đúng phiếu chi của nó", '"attached_to_name": ma_pc' in doan)
	dung("không thấy thì từ chối", "frappe.throw(" in doan)


@ca("KHÔNG mở quyền đọc Payment Entry cho nhân viên bán hàng")
def _():
	# Mo quyen do la mo ca so phieu chi cua tiem.
	m = _py("don_huy.py")
	doan = m.split("def tai_tep(")[1].split("\n@frappe.whitelist")[0]
	dung("nói rõ vì sao không mở", "KHONG mo quyen doc Payment Entry" in doan)


@ca("màn CHỈ ĐỌC mở cho cả quản lý cửa hàng và kế toán")
def _():
	# Quan ly cua hang va ke toan truoc day khong co vai Sales User nen bi
	# chan ngay tu cua, du ho chinh la nguoi hay phai tra loi khach.
	m = _py("don_huy.py")
	dung("có cửa riêng cho màn chỉ đọc", "def _quyen_xem_phieu(" in m)
	dung("gộp thêm vai quản lý cửa hàng", "VAI_QLCH" in m)
	dung("gộp thêm vai kế toán", "VAI_KE_TOAN" in m)
	doan = m.split("def _vai_xem_phieu(")[1].split("\ndef ")[0]
	dung("có giám đốc", "Giám đốc" in doan)


@ca("luồng LẬP phiếu vẫn giữ cửa hẹp cũ, không nới theo")
def _():
	# Man chi doc thi noi rong duoc. Luong lap phieu la tien SE RA, khong
	# duoc di theo.
	m = _py("don_huy.py")
	doan = m.split("def tim_don_de_hoan(")[1].split("\n@frappe.whitelist")[0]
	dung("vẫn dùng cửa hẹp", "_quyen()" in doan)
	la("không dùng cửa rộng", "_quyen_xem_phieu()" in doan, False)


@ca("hàm đọc ruột tệp KHÔNG được mở ra ngoài")
def _():
	# Whitelist no la mo cua doc moi tep trong he.
	m = _py("hoan_tien.py")
	doan = m.split("def ruot_tep_b64(")[0]
	la("không có whitelist ngay trước nó", doan.rstrip().endswith("@frappe.whitelist()"), False)
	dung("nói rõ tuyệt đối không whitelist", "TUYET DOI\n\tkhong whitelist" in _py("hoan_tien.py"))


@ca("ảnh nạp sau khi vẽ, xin bản nhỏ để màn không đứng")
def _():
	m = _js("40-phieu-hoan-huy.js")
	dung("có hàm nạp ảnh", "async function phNapAnh(" in m)
	dung("xin bản nhỏ", "co: 'nho'" in m)
	dung("gọi sau khi vẽ xong", "phNapAnh(root);" in m)
	dung("tải về xin bản lớn", "co: 'lon'" in m)


# ---------------------------------------------------- màn nhập trên app


@ca("màn nhập KHÔNG điền sẵn tổng đơn vào dòng đầu")
def _():
	# Dien san thi bam Luu ngay la ghi mot dong bang ca don, tuc khong chia
	# gi ca ma nhin vao tuong da chia.
	m = _js("42-thanh-toan-nhieu.js")
	dung("dòng dựng sẵn để số 0",
		"dong = [{ pt: st.x.pt_chinh || '', so_tien: 0 }, { pt: '', so_tien: 0 }];" in m)


@ca("dưới hai đường thì không cho lưu")
def _():
	m = _js("42-thanh-toan-nhieu.js")
	dung("chặn ở màn", "if (sach.length < 2)" in m)
	# Chan o CA hai dau: man co the bi qua mat, may chu thi khong.
	t = _py("thanh_toan_nhieu.py")
	dung("máy chủ cũng chặn", "if len(moi) == 1:" in t)


@ca("lệch tổng đơn thì nút Lưu bị khoá")
def _():
	m = _js("42-thanh-toan-nhieu.js")
	dung("khoá nút", "(Math.abs(lech) > 1 ? ' disabled' : '')" in m)
	dung("nói rõ thừa hay thiếu", "(lech > 0 ? 'Thừa ' : 'Thiếu ')" in m)


@ca("đơn ĐÃ GHI SỔ thì chỉ xem, không sửa cách chia")
def _():
	# Doi cach chia tien cua mot to da vao so la doi so cua ca da chot.
	m = _js("42-thanh-toan-nhieu.js")
	dung("gỡ nút sửa khi đã ghi sổ", "if (x.da_ghi_so)" in m)
	t = _py("thanh_toan_nhieu.py")
	doan = t.split("def luu(")[1].split("\n@frappe.whitelist")[0]
	dung("máy chủ chặn cứng", 'if cint(doc.docstatus) != 0:' in doan)


@ca("gõ số không làm vẽ lại cả khối, con trỏ không nhảy khỏi ô")
def _():
	m = _js("42-thanh-toan-nhieu.js")
	doan = m.split("ov.addEventListener('input'")[1].split("});")[0]
	la("không gọi ve() trong lúc gõ", "ve();" in doan, False)


@ca("màn chi tiết đơn có chỗ cắm khối chia tiền")
def _():
	m = _js("08-doanh-so-sales.js")
	dung("có ô để cắm", 'id="dsvTtn"' in m)
	dung("gọi vẽ", "ttnVe('dsvTtn'" in m)
