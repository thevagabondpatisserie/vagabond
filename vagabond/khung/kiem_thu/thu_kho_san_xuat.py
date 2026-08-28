"""Ca kiểm cho cây kho bốn chặng và luật chọn kho nguồn.

Toàn phép thuần, chạy được không cần Frappe, không cần site.
"""

from vagabond import kho_san_xuat as ks
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("kho san xuat: tien to doan dung chang cua nguyen lieu va thanh pham")
def _tien_to():
	la("nvlt", ks.chang_theo_tien_to("NVLT00231"), ks.NGUYEN_LIEU)
	la("bao bi", ks.chang_theo_tien_to("BPKG00007"), ks.NGUYEN_LIEU)
	la("banh ban ra", ks.chang_theo_tien_to("BANU00015"), ks.THANH_PHAM)
	la("hop mua vu", ks.chang_theo_tien_to("BASS00038"), ks.THANH_PHAM)
	# Ban thanh pham PHAI tra None o buoc nay: con phai nhin cong thuc moi
	# biet so cap hay san sang.
	la("btp chua ro", ks.chang_theo_tien_to("BTPB00100"), None)


@ca("kho san xuat: BTP chi co nguyen lieu tho la SO CAP")
def _so_cap():
	la("so cap", ks.chang_cua_mon("BTPB00100", False), ks.BTP_SO_CAP)


@ca("kho san xuat: BTP an them BTP khac la SAN SANG")
def _san_sang():
	la("san sang", ks.chang_cua_mon("BTPB00100", True), ks.BTP_SAN_SANG)


@ca("kho san xuat: co btp con KHONG doi chang cua nguyen lieu")
def _khong_doi_nl():
	# Ma NVLT thi du co truyen co_btp_con=True cung van la nguyen lieu.
	la("van la nguyen lieu", ks.chang_cua_mon("NVLT00231", True), ks.NGUYEN_LIEU)


@ca("kho san xuat: ten kho lap dung theo bep va chang")
def _ten_kho():
	la("baker nl", ks.ten_kho_cua("baker", ks.NGUYEN_LIEU),
		"Baker - Nguyên liệu - TV")
	la("pastry so cap", ks.ten_kho_cua("pastry", ks.BTP_SO_CAP),
		"Pastry - BTP sơ cấp - TV")
	la("baker san sang", ks.ten_kho_cua("baker", ks.BTP_SAN_SANG),
		"Baker - BTP sẵn sàng - TV")
	la("pastry tp", ks.ten_kho_cua("pastry", ks.THANH_PHAM),
		"Pastry - Thành phẩm - TV")
	la("bep la", ks.ten_kho_cua("bep-khong-co", ks.NGUYEN_LIEU), None)


@ca("kho san xuat: doc nguoc ten kho ra ten bep")
def _bep_cua_kho():
	la("baker", ks.bep_cua_kho("Baker - BTP sơ cấp - TV"), "baker")
	la("pastry", ks.bep_cua_kho("Pastry - Thành phẩm - TV"), "pastry")
	la("kho tong", ks.bep_cua_kho("Kho tổng 307 - TV"), None)


@ca("kho san xuat: lam BTP so cap thi lay nguyen lieu o kho Nguyen lieu")
def _nguon_so_cap():
	la("nguon", ks.chon_kho_nguon(ks.BTP_SO_CAP, ks.NGUYEN_LIEU, "baker"),
		"Baker - Nguyên liệu - TV")


# DOI LUAT 28/08/2026, ca kiem cu doi theo. Bon kho trung gian bi tat vi
# chua bao gio co hang di qua; moi chang nay chi rut tu kho Nguyen lieu.
# Ca kiem cu doi "tu so cap" ra kho so cap - gio kho do da tat, doi nhu vay
# la doi mot kho khong con dung. Xem thu_kho_rut_tuot.py.
@ca("kho san xuat: lam BTP san sang chi lay tu kho Nguyen lieu")
def _nguon_san_sang():
	la("tu nguyen lieu", ks.chon_kho_nguon(ks.BTP_SAN_SANG, ks.NGUYEN_LIEU, "pastry"),
		"Pastry - Nguyên liệu - TV")
	la("kho so cap da tat, luat khong con phu",
		ks.chon_kho_nguon(ks.BTP_SAN_SANG, ks.BTP_SO_CAP, "pastry"), None)


@ca("kho san xuat: lam thanh pham cung chi lay tu kho Nguyen lieu")
def _nguon_thanh_pham():
	la("tu nguyen lieu", ks.chon_kho_nguon(ks.THANH_PHAM, ks.NGUYEN_LIEU, "baker"),
		"Baker - Nguyên liệu - TV")
	la("kho san sang da tat",
		ks.chon_kho_nguon(ks.THANH_PHAM, ks.BTP_SAN_SANG, "baker"), None)


@ca("kho san xuat: luat KHONG cho lay nguoc chang")
def _khong_lay_nguoc():
	# Lam BTP so cap ma doi lay tu BTP san sang la di nguoc day chuyen.
	la("di nguoc", ks.chon_kho_nguon(ks.BTP_SO_CAP, ks.BTP_SAN_SANG, "baker"), None)
	# Lam BTP so cap ma doi lay tu thanh pham cung vay.
	la("lay thanh pham", ks.chon_kho_nguon(ks.BTP_SO_CAP, ks.THANH_PHAM, "baker"), None)


@ca("kho san xuat: khong biet chang thi tra None, KHONG doan bua")
def _khong_doan():
	la("thieu chang nl", ks.chon_kho_nguon(ks.THANH_PHAM, None, "baker"), None)
	la("thieu chang ra", ks.chon_kho_nguon(None, ks.NGUYEN_LIEU, "baker"), None)


@ca("kho san xuat: chi con mot kho nguon nen khong con duong lui")
def _lui_kho():
	# Phep lui van con trong ham, de danh cho ngay bat lai bon chang. Nay
	# moi chang chi co mot kho nguon nen khong co gi de lui.
	ton = {"Baker - Nguyên liệu - TV": 500}
	la("van tra dung kho nguyen lieu",
		ks.chon_kho_nguon(ks.THANH_PHAM, ks.NGUYEN_LIEU, "baker", ton),
		"Baker - Nguyên liệu - TV")
	# Kho nguyen lieu het hang thi VAN tra ve kho do chu khong di tim kho
	# khac: het hang la chuyen phai bao, khong phai chuyen phai giau bang
	# cach lay tam o dau do.
	la("het hang van tra dung kho",
		ks.chon_kho_nguon(ks.THANH_PHAM, ks.NGUYEN_LIEU, "baker",
			{"Baker - Nguyên liệu - TV": 0}),
		"Baker - Nguyên liệu - TV")


@ca("kho san xuat: ban khai cay kho du tam kho la, moi bep bon chang")
def _khai_du():
	k = ks.khai_cay_kho()
	la("so kho", len(k), 8)
	la("so chang moi bep", len([x for x in k if x["bep"] == "baker"]), 4)
	# Kho nguyen lieu lay tu kho tong 307, khong lay tu bep nao ca.
	nl = [x for x in k if x["chang"] == ks.NGUYEN_LIEU][0]
	la("nguon cua kho nguyen lieu", nl["kho_nguon"], ks.KHO_GOC)
	tp = [x for x in k if x["bep"] == "pastry" and x["chang"] == ks.THANH_PHAM][0]
	# Tu 28/08/2026 thanh pham rut thang tu kho Nguyen lieu.
	la("nguon chinh cua thanh pham", tp["kho_nguon"], "Pastry - Nguyên liệu - TV")
	dung("cha dung kho nhom", tp["cha"] == "Bếp Pastry - TV")


@ca("kho san xuat: KHONG dat 307 lam kho cha")
def _307_khong_lam_cha():
	# Chot bang ca kiem chu khong bang loi ghi chu: 307 da co 775 dong so kho
	# nen ERPNext tu choi doi no thanh kho nhom. Ly do day du o dau tep.
	for x in ks.khai_cay_kho():
		dung("cha khong phai 307", x["cha"] != ks.KHO_GOC)


# ---------------------------------------------------------------------------
# Luat "Cap 1 = kho so cap, Cap 2 = kho san sang" - anh Viet chot 25/08/2026.
#
# 64 ma banh o nhom NBTP mang san chu cap trong ten. Truoc do may chi suy tu
# cau truc cong thuc, ma cach suy do doc duoc cau truc chu khong doc duoc y
# nguoi dat ten. Ket qua: mot "BTP Cap 1 Banh O Roman size 12" ma cong thuc
# lo an them mot BTP khac la may xep nham sang san sang, tru nham kho.
# ---------------------------------------------------------------------------


@ca("kho san xuat: chu cap trong ten doc ra dung chang")
def _chu_cap():
	la("cap 1", ks.chang_theo_ten("BTP Cấp 1 Bánh Ổ Roman size 12"),
		ks.BTP_SO_CAP)
	la("cap 2", ks.chang_theo_ten("BTP Cấp 2 Bánh Ổ Meraki size 18cm"),
		ks.BTP_SAN_SANG)
	la("khong hoa chu", ks.chang_theo_ten("btp cấp 2 bánh ổ epi"),
		ks.BTP_SAN_SANG)
	la("khong co chu cap", ks.chang_theo_ten("BTP Neutral glaze"), None)
	la("ten rong", ks.chang_theo_ten(""), None)
	la("ten None", ks.chang_theo_ten(None), None)


@ca("kho san xuat: ten noi cap 1 thi THANG cach suy tu cong thuc")
def _ten_thang_cong_thuc():
	# Day chinh la ca that: cong thuc co BTP con (co_btp_con=True) nen cach
	# suy cu se tra SAN SANG, nhung ten ghi ro Cap 1 nen phai la SO CAP.
	la("ten thang", ks.chang_cua_mon("NBTP00001", True, None,
		"BTP Cấp 1 Bánh Ổ Roman size 12"), ks.BTP_SO_CAP)
	# Va chieu nguoc lai: cong thuc chi co nguyen lieu tho nhung ten ghi
	# Cap 2 thi van la SAN SANG.
	la("chieu nguoc", ks.chang_cua_mon("NBTP00005", False, None,
		"BTP Cấp 2 Bánh Ổ Roman size 12"), ks.BTP_SAN_SANG)


@ca("kho san xuat: khai tay THANG ca chu cap trong ten")
def _khai_tay_thang():
	# Nguoi khai tay la nguoi da nhin thay mon that. Khai roi thi may im.
	la("khai tay thang ten", ks.chang_cua_mon("NBTP00001", True,
		ks.BTP_SAN_SANG, "BTP Cấp 1 Bánh Ổ Roman size 12"), ks.BTP_SAN_SANG)
	# Khai bay ba mot chuoi khong thuoc hai chang thi bo qua, khong nhan bua.
	la("khai bay bo qua", ks.chang_cua_mon("NBTP00001", True, "lung tung",
		"BTP Cấp 1 Bánh Ổ Roman size 12"), ks.BTP_SO_CAP)
	la("khai rong bo qua", ks.chang_cua_mon("NBTP00001", True, "",
		"BTP Cấp 1 Bánh Ổ Roman size 12"), ks.BTP_SO_CAP)


@ca("kho san xuat: chu cap KHONG chen vao nguyen lieu hay thanh pham")
def _chu_cap_khong_lan():
	# Tien to van thang chu cap. Mot NVL lo mang chu "cap 1" trong ten thi
	# van la nguyen lieu, khong duoc keo sang chang BTP.
	la("nvl van la nvl", ks.chang_cua_mon("NVLT00231", False, None,
		"Bột mì cấp 1"), ks.NGUYEN_LIEU)
	la("thanh pham van la tp", ks.chang_cua_mon("BAWC00066", False, None,
		"Bánh Ổ Roman cấp 2"), ks.THANH_PHAM)


@ca("kho san xuat: khong khai gi thi giu nguyen cach suy cu")
def _giu_nep_cu():
	# Ca kiem chan tai dien: them nac moi khong duoc lam doi ket qua cua cac
	# mon khong co chu cap trong ten.
	la("so cap nhu cu", ks.chang_cua_mon("BTPB00100", False, None,
		"BTP Pastry cream"), ks.BTP_SO_CAP)
	la("san sang nhu cu", ks.chang_cua_mon("BTPB00100", True, None,
		"BTP Pastry cream"), ks.BTP_SAN_SANG)
	la("khong truyen ten", ks.chang_cua_mon("BTPB00100", True), ks.BTP_SAN_SANG)


@ca("kho san xuat: o khai tay duoc khai dung mot lan tren ho so mon")
def _o_khai_tay():
	o = [x for x in ks.TRUONG_MOI.get("Item", [])
		if x["fieldname"] == "custom_chang_btp"]
	la("co dung mot o", len(o), 1)
	la("la o chon", o[0]["fieldtype"], "Select")
	# Hai gia tri phai TRUNG ten hai chang, lech mot dau la khai tay vo tac
	# dung ma khong ai bao.
	dung("o chon co du hai chang", ks.BTP_SO_CAP in o[0]["options"]
		and ks.BTP_SAN_SANG in o[0]["options"])
