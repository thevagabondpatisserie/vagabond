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
