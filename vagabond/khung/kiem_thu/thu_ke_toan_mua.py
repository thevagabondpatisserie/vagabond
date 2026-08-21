"""Ca kiểm cho lõi kế toán mua hàng: gắn đối tác và cầu nối tài khoản cũ.

Mọi ca ở đây chạy trên phép THUẦN, không cần Frappe, không cần site, không
cần mạng - đúng yêu cầu của máy chạy CI.
"""

from vagabond import ke_toan_mua as km
from vagabond.khung.kiem_thu.nen import ca, dung, la

TK_MOI = "3311 - Phải trả người bán, hàng về chưa có hoá đơn - TV"
TK_CU = "335 - Chi phí phải trả - TV"
TK_KHO = "152 - Nguyên liệu, vật liệu - TV"


@ca("ke toan mua: KHONG duoc gan doi tac vao tai khoan cho hoa don")
def _khong_gan_doi_tac():
	# Ngay 21/08/2026 Kien khong nhap kho duoc vi hai lop thay the cua v256
	# dinh doi tac vao dong so cua tai khoan 3311. ERPNext nem loi "Loai doi
	# tac va Doi tac chi co the duoc dat cho tai khoan Phai thu / Phai tra".
	# Ba ca duoi day chot lai de khong phien nao dung lai viec do.
	dung("Payable duoc gan", km.duoc_gan_doi_tac("Payable"))
	dung("Receivable duoc gan", km.duoc_gan_doi_tac("Receivable"))
	dung("SRBNB KHONG duoc gan", not km.duoc_gan_doi_tac(km.LOAI_TK))
	# Ham dinh doi tac cu phai bien mat han, khong duoc de lai de ai do goi.
	dung("khong con ham gan_doi_tac", not hasattr(km, "gan_doi_tac"))


@ca("ke toan mua: hooks KHONG duoc ghi de lop Phieu nhap va Hoa don mua")
def _hooks_sach():
	# Doc hooks.py bang chu chu KHONG import: hooks keo ca app, may chay CI
	# tay khong se no. Doc thang chuoi la du de chot.
	import os

	tep = os.path.join(os.path.dirname(os.path.abspath(km.__file__)), "hooks.py")
	noi_dung = open(tep, encoding="utf-8").read()
	dung("khong con lop_mua_hang", "lop_mua_hang" not in noi_dung)
	dung("khong ghi de Purchase Receipt",
		'"Purchase Receipt": "vagabond' not in noi_dung)
	dung("khong ghi de Purchase Invoice",
		'"Purchase Invoice": "vagabond' not in noi_dung)


@ca("ke toan mua: gom so cai tai khoan cho theo tung nha cung cap")
def _gom_ncc():
	dong = [
		{"voucher_type": "Purchase Receipt", "voucher_no": "PNK-1",
			"debit": 0, "credit": 5000000},
		{"voucher_type": "Purchase Receipt", "voucher_no": "PNK-2",
			"debit": 0, "credit": 3000000},
		{"voucher_type": "Purchase Invoice", "voucher_no": "HDM-1",
			"debit": 5000000, "credit": 0},
	]
	tra = {
		("Purchase Receipt", "PNK-1"): "NCC-0007",
		("Purchase Receipt", "PNK-2"): "NCC-0009",
		("Purchase Invoice", "HDM-1"): "NCC-0007",
	}
	bang = km.gom_theo_ncc(dong, tra)
	la("so nha cung cap", len(bang), 2)
	# NCC-0009 con no 3 trieu nen phai dung truoc, NCC-0007 da can bang.
	la("xep no nhieu truoc", bang[0]["ncc"], "NCC-0009")
	la("du co NCC-0009", bang[0]["du_co"], 3000000)
	la("du co NCC-0007", bang[1]["du_co"], 0)
	la("tong khop so du tai khoan", sum(x["du_co"] for x in bang), 3000000)


@ca("ke toan mua: chung tu khong tra ra NCC thi gom vao nhom rong")
def _ncc_khong_ro():
	# But toan tay chen vao tai khoan cho thi khong co nha cung cap. Phai
	# giu lai chu khong duoc bo di, neu khong tong bang lech so du tai khoan
	# ma khong ai biet.
	dong = [{"voucher_type": "Journal Entry", "voucher_no": "BT-1",
		"debit": 0, "credit": 700000}]
	bang = km.gom_theo_ncc(dong, {})
	la("van giu dong", len(bang), 1)
	la("nhom rong", bang[0]["ncc"], "")
	la("tong khong mat", bang[0]["du_co"], 700000)


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
