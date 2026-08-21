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


@ca("kho san xuat: lam BTP san sang lay ca hai chang")
def _nguon_san_sang():
	la("tu so cap", ks.chon_kho_nguon(ks.BTP_SAN_SANG, ks.BTP_SO_CAP, "pastry"),
		"Pastry - BTP sơ cấp - TV")
	la("tu nguyen lieu", ks.chon_kho_nguon(ks.BTP_SAN_SANG, ks.NGUYEN_LIEU, "pastry"),
		"Pastry - Nguyên liệu - TV")


@ca("kho san xuat: lam thanh pham lay tu BTP san sang va nguyen lieu")
def _nguon_thanh_pham():
	la("tu san sang", ks.chon_kho_nguon(ks.THANH_PHAM, ks.BTP_SAN_SANG, "baker"),
		"Baker - BTP sẵn sàng - TV")
	la("tu nguyen lieu", ks.chon_kho_nguon(ks.THANH_PHAM, ks.NGUYEN_LIEU, "baker"),
		"Baker - Nguyên liệu - TV")


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


@ca("kho san xuat: het ton o kho dung luat thi lui ve kho tiep theo")
def _lui_kho():
	ton = {"Baker - BTP sẵn sàng - TV": 0, "Baker - BTP sơ cấp - TV": 500}
	la("lui mot bac",
		ks.chon_kho_nguon(ks.THANH_PHAM, ks.BTP_SAN_SANG, "baker", ton),
		"Baker - BTP sơ cấp - TV")


@ca("kho san xuat: ban khai cay kho du tam kho la, moi bep bon chang")
def _khai_du():
	k = ks.khai_cay_kho()
	la("so kho", len(k), 8)
	la("so chang moi bep", len([x for x in k if x["bep"] == "baker"]), 4)
	# Kho nguyen lieu lay tu kho tong 307, khong lay tu bep nao ca.
	nl = [x for x in k if x["chang"] == ks.NGUYEN_LIEU][0]
	la("nguon cua kho nguyen lieu", nl["kho_nguon"], ks.KHO_GOC)
	tp = [x for x in k if x["bep"] == "pastry" and x["chang"] == ks.THANH_PHAM][0]
	la("nguon chinh cua thanh pham", tp["kho_nguon"], "Pastry - BTP sẵn sàng - TV")
	la("nguon phu cua thanh pham", tp["kho_nguon_phu"], "Pastry - BTP sơ cấp - TV")
	dung("cha dung kho nhom", tp["cha"] == "Bếp Pastry - TV")


@ca("kho san xuat: KHONG dat 307 lam kho cha")
def _307_khong_lam_cha():
	# Chot bang ca kiem chu khong bang loi ghi chu: 307 da co 775 dong so kho
	# nen ERPNext tu choi doi no thanh kho nhom. Ly do day du o dau tep.
	for x in ks.khai_cay_kho():
		dung("cha khong phai 307", x["cha"] != ks.KHO_GOC)
