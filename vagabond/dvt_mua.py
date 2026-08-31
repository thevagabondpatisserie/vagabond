# -*- coding: utf-8 -*-
"""Doi chieu DON VI giua hoa don mua va phieu nhap kho.

Vi sao co tep nay - ca that ngay 26/08/2026
------------------------------------------------------------------------
Hoa don dien tu HDM-26-08-00104 cua Thuc pham Ngon Co Dien ghi mot dong:

    Hat de dong lanh, so luong 4, don vi "BAG", don gia 280.000

Phieu nhap PNK-2026-00162 cua chinh lo hang do ghi:

    Hat de dong lanh, so luong 4, don vi "Tui" (1 Tui = 1.000 Gram),
    don gia 161.000

Mon nay khai don vi kho la Gram. Trong bang quy doi cua mon co "Tui" va
"Kg", KHONG co "BAG". May doc hoa don khong tra ra duoc "BAG" la gi nen
lui ve don vi kho, thanh ra dong hoa don la 4 GRAM chu khong phai 4 TUI.

Tien thi van dung, vi 4 nhan 280.000 deu ra 1.120.000 du don vi nao. Chi
co SO LUONG sai gap mot nghin lan. Man doi chieu thi so "4" voi "4" nen
bao la khop so luong, chi lech gia. Nghia la cai sai nguy hiem nhat lai
la cai duy nhat khong ai nhin thay.

Bai hoc: so luong khong so duoc neu chua quy ve cung mot don vi. Va don
gia cung vay - 280.000 mot gram voi 161.000 mot tui la hai con so khong
cung ho, dat canh nhau roi tru cho nhau la ra mot so vo nghia.

Tep nay THUAN, khong cham Frappe, de kiem thu duoc khong can site.
"""


# Don vi ma nha cung cap hay ghi bang tieng Anh hoac viet tat tren hoa don
# dien tu. Ben trai la thu doc duoc tren hoa don, ben phai la ten don vi
# ma he minh dang dung.
#
# Bang nay chi de GOI Y cho nguoi ta khai, KHONG tu dong sua chung tu. May
# doan don vi ho roi ghi thang vao so la dung cai sai da xay ra hom nay,
# chi khac chieu.
BANG_GOI_Y = {
	"BAG": "Túi",
	"SACK": "Túi",
	"POUCH": "Túi",
	"BOX": "Hộp",
	"CARTON": "Thùng",
	"CTN": "Thùng",
	"CASE": "Thùng",
	"CAN": "Lon",
	"TIN": "Lon",
	"BOTTLE": "Chai",
	"BTL": "Chai",
	"JAR": "Hũ",
	"PACK": "Gói",
	"PACKET": "Gói",
	"PKG": "Gói",
	"PCS": "Cái",
	"PC": "Cái",
	"PIECE": "Cái",
	"EA": "Cái",
	"EACH": "Cái",
	"UNIT": "Cái",
	"ROLL": "Cuộn",
	"SET": "Bộ",
	"TRAY": "Khay",
	"DOZEN": "Tá",
	"KG": "Kg",
	"KGS": "Kg",
	"KGM": "Kg",
	"G": "Gram",
	"GR": "Gram",
	"GRAM": "Gram",
	"GRM": "Gram",
	"L": "Lít",
	"LIT": "Lít",
	"LTR": "Lít",
	"LITRE": "Lít",
	"LITER": "Lít",
	"ML": "Ml",
	"MLT": "Ml",
}

DAU = (
	"àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩị"
	"òóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
)
KHONG_DAU = (
	"aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiii"
	"ooooooooooooooooouuuuuuuuuuuyyyyyd"
)


def bo_dau(s):
	"""Bo dau tieng Viet va ha ve chu thuong. THUAN."""
	s = str(s or "").lower()
	ra = []
	for c in s:
		i = DAU.find(c)
		ra.append(KHONG_DAU[i] if i >= 0 else c)
	return "".join(ra)


def chuan(s):
	"""Chuan hoa mot ten don vi de so sanh: bo dau, bo khoang trang, thuong."""
	return "".join(bo_dau(s).split())


def cung_don_vi(a, b):
	"""Hai ten don vi co phai la mot khong. THUAN."""
	ca, cb = chuan(a), chuan(b)
	return bool(ca) and ca == cb


def goi_y_don_vi(dvt_ncc):
	"""Ten don vi ben minh ma don vi cua nha cung cap co the la. '' neu chiu.

	Chi tra goi y, viec khai la cua nguoi.
	"""
	k = chuan(dvt_ncc).upper()
	if not k:
		return ""
	for nguon, dich in BANG_GOI_Y.items():
		if chuan(nguon).upper() == k:
			return dich
	return ""


def he_so(hs):
	"""He so quy doi ve don vi kho. Thieu hoac phi ly thi coi la 1."""
	try:
		v = float(hs or 0)
	except (TypeError, ValueError):
		return 1.0
	return v if v > 0 else 1.0


def ton(sl, hs):
	"""So luong quy ve DON VI KHO."""
	try:
		s = float(sl or 0)
	except (TypeError, ValueError):
		s = 0.0
	return s * he_so(hs)


def gia_moi_don_vi_kho(gia, hs):
	"""Don gia quy ve mot don vi kho.

	280.000 mot Tui 1.000 Gram la 280 dong mot gram. Chi khi ca hai ben
	deu quy ve day thi tru nhau moi co nghia.
	"""
	try:
		g = float(gia or 0)
	except (TypeError, ValueError):
		g = 0.0
	return g / he_so(hs)


def lech_don_vi(dvt_hd, hs_hd, dvt_pnk, hs_pnk):
	"""True khi hai ben khai don vi khac nhau THAT SU.

	Ten khac nhau ma he so bang nhau thi khong sao: "Kg" va "Ky" cung la
	1.000 gram, so luong ghi ra nhu nhau, khong viec gi phai chan.
	"""
	if cung_don_vi(dvt_hd, dvt_pnk):
		return False
	return abs(he_so(hs_hd) - he_so(hs_pnk)) > 1e-9


# Ba ket qua cua phep xet don vi giua mot dong hoa don va mot dong phieu nhap.
DVT_KHOP = "khop"        # cung ten, so luong nhu nhau
DVT_KHAC_TEN = "khac_ten"  # so luong quy ve kho nhu nhau, chi khac cai ten
DVT_LECH = "lech"        # he so khac nhau, so luong that lech


def xet_don_vi(dvt_hd, hs_hd, dvt_pnk, hs_pnk):
	"""Hai dong nay khop don vi tới mức nào. THUẦN. Trả một trong ba hằng trên.

	VÌ SAO PHẢI CÓ HÀM NÀY, ca thật 27/08/2026
	--------------------------------------------------------------------
	Trước đó màn Đối chiếu và phép nối xét khác nhau. Màn hình gọi
	`lech_don_vi`, hàm đó coi hai đơn vị là một khi hệ số bằng nhau, nên
	"Gói" 1.000 và "Kg" 1.000 được báo là KHỚP, hiện nút xanh Khớp và ghi
	sổ. Còn phép nối thì đòi thêm tên phải trùng, nên bấm vào lại bị từ
	chối. Màn hình bảo được, nút bảo không.

	Nay cả hai gọi chung hàm này. Trường hợp giữa - cùng số lượng nhưng
	khác tên - có tên riêng để mỗi bên xử đúng phần của mình: màn hình
	không coi là lệch, còn phép nối thì tự đổi tên cho khớp rồi đi tiếp,
	vì ERPNext đòi ô đơn vị của hai bên bằng nhau từng chữ.
	"""
	if cung_don_vi(dvt_hd, dvt_pnk):
		return DVT_KHOP
	if abs(he_so(hs_hd) - he_so(hs_pnk)) > 1e-9:
		return DVT_LECH
	return DVT_KHAC_TEN


def so_ton_khop(sl_hd, hs_hd, sl_pnk, hs_pnk, sai_so=0.0001):
	"""Hai ben co cung so luong khi da quy ve don vi kho khong."""
	return abs(ton(sl_hd, hs_hd) - ton(sl_pnk, hs_pnk)) <= sai_so


def loi_lech_don_vi(idx, ten_mon, sl_hd, dvt_hd, hs_hd, sl_pnk, dvt_pnk, hs_pnk, dvt_kho, dvt_ncc=""):
	"""Cau tieng Viet giai thich lech don vi, kem viec can lam.

	Viet han ra day thay vi de ERPNext nem mot cau tieng Anh, vi nguoi doc
	cau nay la Uyen va ke toan chu khong phai lap trinh vien.
	"""
	gy = goi_y_don_vi(dvt_ncc)
	cau = (
		"Dòng %d: món %s trên hoá đơn ghi %g %s, phiếu nhập ghi %g %s. "
		"Quy về %s thì hoá đơn là %g còn phiếu nhập là %g, chênh nhau nên chưa nối được."
		% (
			idx,
			ten_mon,
			float(sl_hd or 0),
			dvt_hd or dvt_kho,
			float(sl_pnk or 0),
			dvt_pnk or dvt_kho,
			dvt_kho,
			ton(sl_hd, hs_hd),
			ton(sl_pnk, hs_pnk),
		)
	)
	if dvt_ncc and not cung_don_vi(dvt_ncc, dvt_hd):
		cau += ' Nhà cung cấp ghi đơn vị "%s" trên hoá đơn điện tử' % dvt_ncc
		if gy:
			cau += ", nhiều khả năng là %s" % gy
		cau += ". Khai đơn vị đó vào bảng quy đổi của món rồi tải lại hoá đơn."
	return cau


def dong_dich_vu(item_code):
	"""Dong nay co phai dong dich vu chua anh xa vao Mon khong. THUAN.

	Hoa don dien tu hay co dong kieu "Chuyen", "Phieu", "Dich vu chiu thue"
	khong tra ra ma hang nao ca. Nhung dong do KHONG co don vi kho de doi
	chieu, nen dem chung vao con so lech don vi la dem nham.

	Ngay 27/08/2026 nhip ra keu 1.185 to lech don vi trong khi lech that
	chi 505 to. 3.798 tren 4.443 dong bi keu la dong dich vu kieu nay. Con
	so nhieu nhu vay thi vai hom la khong ai nhin nua, canh bao coi nhu
	chet. Nen tach hai loai ra, dem rieng, va con so dua ra man hinh chi
	dem dong co ma hang that.
	"""
	return not str(item_code or "").strip()


NGUONG_DO_TAM = 8


def mon_bi_do_tam(so_ten_ncc, nguong=NGUONG_DO_TAM):
	"""Mon nay co dang bi dung lam cho do tam khong. THUAN.

	Mot mon kho nhan qua nhieu TEN HANG khac nhau cua nha cung cap la dau
	hieu xau: nguoi ta khong tim ra mon dung nen tien tay gan dai vao mon
	nao ten na na.

	Ca that 27/08/2026: mon NVLT00231 "Nuoc, ml" - von la nuoc may de san
	xuat, khong theo doi ton, chi co don vi ml - dang nhan 18 ten hang khac
	nhau: nuoc da bao, nuoc suoi chai, nuoc sparkling, nuoc mam chay, va ca
	"Che troi nuoc" voi "nuoc tra bi dao" cua hoa don nha hang. Khop vi cung
	co chu "nuoc" trong ten, chu khong phai vi cung mot thu.

	Nguong 8 dat theo so lieu that: sau NVLT00231 (18 ten) va DVTI00017
	"Chi phi tiep khach" (11 ten, von la mon gom co chu y), mon dong thu ba
	chi co 7 ten. Nen 8 tach dung hai ca ngoai le ra khoi phan con lai.

	Mon gom co chu y thi khai vao `MON_GOM_CO_Y` de khoi bi keu mai.
	"""
	return int(so_ten_ncc or 0) >= int(nguong or NGUONG_DO_TAM)


# Nhung mon VON DI la cho gom nhieu thu, bi keu la keu oan.
MON_GOM_CO_Y = {"DVTI00017"}


def dang_do_tam(item_code, so_ten_ncc, nguong=NGUONG_DO_TAM):
	"""Nhu tren nhung tru san cac mon gom co chu y. THUAN."""
	if str(item_code or "").strip() in MON_GOM_CO_Y:
		return False
	return mon_bi_do_tam(so_ten_ncc, nguong)


def he_so_de_xuat(sl_hd, sl_pnk, hs_pnk):
	"""He so nen khai cho don vi la cua nha cung cap. 0 neu khong dam doan.

	Vi sao doan duoc, va vi sao chi doan duoc TRONG MOT TRUONG HOP
	--------------------------------------------------------------------
	Hoa don ghi "4 BAG", phieu nhap cung lo hang do ghi "4 Tui" voi 1 Tui
	la 1.000 Gram. Hai ben cung con so 4, tuc cai thung cua ho va cai tui
	cua minh la mot. Vay 1 BAG = 1.000 Gram.

	So luong hai ben KHAC nhau thi chiu. "4 BAG" voi "2 Tui" co the la mot
	BAG bang hai tui, cung co the la nha cung cap giao thieu. May khong
	phan biet duoc, ma doan sai o day la hong gia von, nen tra 0 va de
	nguoi go.
	"""
	try:
		a = float(sl_hd or 0)
		b = float(sl_pnk or 0)
	except (TypeError, ValueError):
		return 0.0
	if a <= 0 or b <= 0:
		return 0.0
	if abs(a - b) > 0.0001:
		return 0.0
	return he_so(hs_pnk)


def don_vi_chua_khai(dvt_ncc, dvt_dang_dung, he_so_dang_dung):
	"""Dong nay co dang mang don vi bia ra khong. THUAN.

	True khi nha cung cap co ghi don vi, ma don vi minh dang dung tren dong
	lai khac ten VA he so dang la 1. Do dung la dau van tay cua duong ha
	ngam: tra khong ra he so nen tam lay don vi kho voi he so 1.

	He so khac 1 thi khong tinh, vi luc do da tra ra bang quy doi that.

	Phep nay truoc nam trong `minvoice_chung_tu.py`. Dua ve day 31/08/2026
	de tang thuan giu tron mot phep, va de bo kiem chay duoc tren may CI
	tay khong - nap `minvoice_chung_tu` la keo theo ca Frappe.
	"""
	ncc = (dvt_ncc or "").strip()
	if not ncc:
		return False
	if cung_don_vi(ncc, dvt_dang_dung):
		return False
	return abs(he_so(he_so_dang_dung) - 1.0) < 1e-9


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import flt


def dvt_tren_hoa_don(mo_ta):
	"""Doc lai don vi goc nha cung cap ghi, neu con dau vet trong mo ta.

	Ban ghi hoa don dien tu dinh don vi vao cuoi mo ta trong ngoac don.
	Doc duoc thi noi ro cho nguoi ta, khong doc duoc thi thoi, KHONG doan.
	"""
	s = str(mo_ta or "").strip()
	if not s.endswith(")"):
		return ""
	i = s.rfind("(")
	if i < 0:
		return ""
	trong = s[i + 1 : -1].strip()
	if not trong or len(trong) > 20 or "(" in trong:
		return ""
	return trong


def he_so_cua_mon(item_code, dvt):
	"""He so quy doi cua mot don vi tren mot mon. 0 neu mon khong khai."""
	if not item_code or not dvt:
		return 0.0
	v = frappe.db.get_value(
		"UOM Conversion Detail", {"parent": item_code, "uom": dvt}, "conversion_factor"
	)
	return flt(v)
