"""Ca kiểm cho lõi kế toán mua hàng: gắn đối tác và cầu nối tài khoản cũ.

Mọi ca ở đây chạy trên phép THUẦN, không cần Frappe, không cần site, không
cần mạng - đúng yêu cầu của máy chạy CI.
"""

from vagabond import ke_toan_mua as km
from vagabond.khung.kiem_thu.nen import ca, dung, la

TK_MOI = "3311 - Phải trả người bán, hàng về chưa có hoá đơn - TV"
TK_CU = "335 - Chi phí phải trả - TV"
TK_KHO = "152 - Nguyên liệu, vật liệu - TV"


@ca("ke toan mua: gan doi tac vao dong tai khoan cho hoa don")
def _gan_dung_dong():
	dong = [
		{"account": TK_KHO, "debit": 8640000, "credit": 0},
		{"account": TK_MOI, "debit": 0, "credit": 8640000},
	]
	km.gan_doi_tac(dong, TK_MOI, "NCC-0007")
	la("ma ncc", dong[1].get("party"), "NCC-0007")
	la("loai doi tac", dong[1].get("party_type"), "Supplier")
	# Dong kho tuyet doi khong duoc dinh doi tac: 152 khong phai tai khoan
	# cong no, gan vao la bao cao tuoi no doc sai ngay.
	dung("dong kho khong co doi tac", not dong[0].get("party"))


@ca("ke toan mua: khong ghi de doi tac ERPNext da dien")
def _khong_ghi_de():
	dong = [{"account": TK_MOI, "debit": 0, "credit": 100,
		"party_type": "Supplier", "party": "NCC-CU"}]
	km.gan_doi_tac(dong, TK_MOI, "NCC-MOI")
	la("giu nguyen doi tac cu", dong[0]["party"], "NCC-CU")


@ca("ke toan mua: thieu ma nha cung cap thi khong gan bua")
def _thieu_ncc():
	dong = [{"account": TK_MOI, "debit": 0, "credit": 100}]
	km.gan_doi_tac(dong, TK_MOI, None)
	dung("khong gan bua", not dong[0].get("party"))


@ca("ke toan mua: doc so cai doan dung tai khoan cho cua phieu nhap")
def _doan_tk():
	dong = [
		{"account": TK_KHO, "debit": 8640000, "credit": 0},
		{"account": TK_CU, "debit": 0, "credit": 8640000},
	]
	la("tai khoan cho", km.tk_cho_theo_so_cai(dong, [TK_CU, TK_MOI]), TK_CU)


@ca("ke toan mua: chon tai khoan cho theo so tien lon nhat")
def _chon_theo_tien():
	# Phieu co mot dong le vao tai khoan moi va mot dong lon vao tai khoan
	# cu thi phai chot la phieu cu, khong duoc lay dong dau tien.
	dong = [
		{"account": TK_MOI, "debit": 0, "credit": 1000},
		{"account": TK_CU, "debit": 0, "credit": 8640000},
	]
	la("chon theo tien", km.tk_cho_theo_so_cai(dong, [TK_CU, TK_MOI]), TK_CU)


@ca("ke toan mua: phieu khong dung tai khoan cho nao thi tra None")
def _khong_dung_tk_cho():
	dong = [{"account": TK_KHO, "debit": 100, "credit": 0}]
	la("khong co", km.tk_cho_theo_so_cai(dong, [TK_CU, TK_MOI]), None)


@ca("ke toan mua: gom phieu nhap cua hoa don, bo trung")
def _gom_phieu():
	hang = [
		{"purchase_receipt": "PNK-0001"},
		{"purchase_receipt": "PNK-0001"},
		{"purchase_receipt": "PNK-0002"},
		{"purchase_receipt": None},
	]
	la("danh sach phieu", km.phieu_nhap_cua_hoa_don(hang),
		["PNK-0001", "PNK-0002"])


@ca("ke toan mua: hoa don cua phieu cu thi bac cau ve tai khoan cu")
def _bac_cau():
	la("bac cau", km.can_bac_cau(["PNK-0001"], {"PNK-0001": TK_CU}, TK_MOI),
		TK_CU)


@ca("ke toan mua: hoa don cua phieu moi thi khong bac cau")
def _khong_bac_cau():
	la("khong bac cau", km.can_bac_cau(["PNK-9"], {"PNK-9": TK_MOI}, TK_MOI),
		None)


@ca("ke toan mua: hoa don tron phieu cu va phieu moi thi KHONG doan")
def _tron_phieu():
	# Doan bua o day la de ra chenh lech ma khong ai biet. Tra None de
	# ERPNext lam mac dinh, ke toan tu tach hoa don.
	la("tron thi khong doan",
		km.can_bac_cau(["A", "B"], {"A": TK_CU, "B": TK_MOI}, TK_MOI), None)


@ca("ke toan mua: phieu khong doc duoc so cai thi khong bac cau")
def _khong_doc_duoc():
	la("khong doc duoc", km.can_bac_cau(["A"], {"A": None}, TK_MOI), None)


@ca("ke toan mua: loai tai khoan cho KHONG duoc la Payable")
def _khong_payable():
	# Chot bang ca kiem chu khong bang loi ghi chu: dat Payable vao day lam
	# so du hoa don mua bi tinh sai, ly do day du o dau ke_toan_mua.py.
	la("loai tai khoan", km.LOAI_TK, "Stock Received But Not Billed")
	dung("khong phai Payable", km.LOAI_TK != "Payable")
