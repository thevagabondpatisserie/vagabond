"""Giữ chip APP không đánh đồng đã chi, chứng từ và cấn nợ (#263)."""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.chip_ho_so_tt import chip_cua_dong, NHAN, MO_TA


@ca("APP chip: da chi van cho hoa don, khong nhac chuyen tien lan nua")
def _():
	ra = chip_cua_dong({"trang_thai": "Da thanh toan", "so_cho_hoa_don": 2})
	la("hai viec doc lap", ra, ["cho_hoa_don", "da_chi"])


@ca("APP chip: nhieu dong vua cho vua da noi, khong khang dinh can no")
def _():
	ra = chip_cua_dong({"so_cho_hoa_don": 1, "so_da_noi_hoa_don": 2})
	la("khong mat nhom cho", ra, ["cho_hoa_don", "da_noi_hoa_don"])


@ca("APP chip: da duyet thieu UNC va sao ke, du lieu moi bo dung chip")
def _():
	d = {"trang_thai": "Da duyet", "co_unc": 0}
	la("hai viec thieu", chip_cua_dong(d), ["thieu_unc", "chua_noi_sao_ke"])
	d.update(co_unc=1, ma_giao_dich="BT1")
	la("doc lai da du", chip_cua_dong(d), [])


@ca("APP chip: phieu tra truoc khong suy thieu UNC tu gia tri mac dinh")
def _():
	la("chi nhac cho lau", chip_cua_dong({"trang_thai": "Da duyet", "la_phieu_chi": 1, "cho_ngay": 8}), ["cho_lau"])


@ca("APP chip: huy tu choi khong nhac chi, mo lai khong bao da chi")
def _():
	for tt in ("Huy", "Tu choi"):
		la(tt, chip_cua_dong({"trang_thai": tt, "tre_ngay": 9, "so_cho_hoa_don": 1}), [])
	ra = chip_cua_dong({"trang_thai": "Da thanh toan", "canh_bao_doi_chieu": "PE hủy"})
	la("can kiem", ra, ["kiem_lai"])


@ca("APP chip: moi loai ho so dung chung quy tac, nhap khong nhac sao ke")
def _():
	for loai in ("NCC", "Hoan ung", "Hoan ung HD", "TK cong ty"):
		la(loai, chip_cua_dong({"loai": loai, "trang_thai": "Nhap", "tre_ngay": 1}), ["qua_han"])


@ca("APP chip #476: moi chip loc co mot dong giai thich co dau, khong gach dai")
def _():
	la("du mo ta cho moi ma", sorted(MO_TA), sorted(NHAN))
	for ma, cau in MO_TA.items():
		dung(ma + " co cau giai thich", len(cau.strip()) > 20)
		dung(ma + " khong em/en dash", "\u2014" not in cau and "\u2013" not in cau)


@ca("APP chip #476: ghi nhan kem ly do chua du sao ke vao nhom Cho doi chieu sau")
def _():
	ra = chip_cua_dong({"trang_thai": "Da thanh toan", "cho_doi_chieu_sau": True})
	dung("co nhom cho", "cho_doi_chieu_sau" in ra)
	la("huy thi khong nhac", chip_cua_dong({"trang_thai": "Huy", "cho_doi_chieu_sau": True}), [])
