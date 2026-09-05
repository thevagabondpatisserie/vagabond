"""Luat chu nghia tren to hoa don VAT. THUAN, khong cham Frappe.

Hai viec, ca hai deu sinh ra tu mot su co that ngay 22/08/2026.

1. TEN PHAP NHAN CO BI CUT KHONG
   Don 92409, ma so thue 0108903529. To hoa don so 10901 da ky, da gui co
   quan thue, mang ten nguoi mua dung ba chu: "CONG TY CO PHAN". Ten that
   la "CONG TY CO PHAN MANG LUOI BAN DAN VIET NAM". Khach khieu nai, ke
   toan phai lap bien ban va xuat to thay the.

   Ra soat lai thi ma cua tiem KHONG cat chuoi o cho nao ca. Goi lai VietQR
   hom 24/08 thi no tra ve du ten. Nhung dia chi dang luu trong phieu co
   duoi ", Viet Nam" ma ban VietQR hom nay khong co - tuc ban ghi ben Cuc
   Thue da doi giua hai ngay. Ngay 22/08 no tra ve ten cut, va minh luu y
   nguyen vi khong co chot chan nao.

   Ket luan: nguon ben ngoai co the tra ve ten cut bat cu luc nao, va minh
   khong sua duoc dieu do. Cai minh lam duoc la KHONG NHAN mot cai ten chi
   co loai hinh phap ly ma khong co ten rieng.

   Vi sao khong do theo DO DAI. Anh Viet de xuat nguong 15 ky tu. Ca nay
   lot dung ke: "CÔNG TY CỔ PHẦN" dem duoc đúng 15 ky tu. Ma quet 86 phieu
   co ma so thue thi thay nhieu ten THAT cung rat ngan, "Công ty TNHH IMAE",
   "CÔNG TY TNHH LA SOL", "HỘ KINH DOANH RAVIE". Do theo do dai la vua lot
   luoi vua bao dong gia.

   Cach o day: boc cac CUM chi loai hinh phap ly ra khoi dau chuoi, xem con
   lai chu nao khong. "CONG TY TNHH IMAE" con "IMAE" nen qua. "CONG TY CO
   PHAN" khong con gi nen chan. Chay thu tren 86 phieu that: bat dung mot
   ca, dung ca cua don 92409, khong bao nham ca nao.

   Boc theo CUM chu khong theo TU la co chu y. Boc theo tu thi phai dua ca
   "VAN", "PHONG", "DAI", "DIEN" vao danh sach de xu ly "van phong dai
   dien", ma nhung tu do lai nam trong ten that cua nhieu cong ty.

2. DIEN GIAI TREN TO THAY THE
   Nghi dinh 123/2020 buoc to thay the phai ghi ro no thay cho to nao. Khi
   nao ERP tu xuat hoa don thay the thang sang M-Invoice thi cau nay phai
   nam san o dau dien giai. Viet truoc va kiem thu truoc, de luc noi API
   khong phai nho ra.
"""

import re
import unicodedata

# ---------------------------------------------------------------- ten rieng

# Cac CUM chi loai hinh phap ly, viet khong dau va hoa het. Xep CUM DAI
# TRUOC: "CONG TY TNHH MOT THANH VIEN" phai boc truoc "CONG TY TNHH", khong
# thi boc xong con lai "MOT THANH VIEN" va tuong do la ten rieng.
CUM_LOAI_HINH = (
	"CONG TY TRACH NHIEM HUU HAN MOT THANH VIEN",
	"CONG TY TRACH NHIEM HUU HAN",
	"CONG TY TNHH MOT THANH VIEN",
	"CONG TY TNHH MTV",
	"CONG TY CO PHAN TAP DOAN",
	"TONG CONG TY CO PHAN",
	"TONG CONG TY",
	"CONG TY CO PHAN",
	"CONG TY TNHH",
	"CONG TY CP",
	"CONG TY",
	"LIEN HIEP HOP TAC XA",
	"HOP TAC XA",
	"DOANH NGHIEP TU NHAN",
	"VAN PHONG DAI DIEN",
	"VAN PHONG LUAT SU",
	"CHI NHANH",
	"HO KINH DOANH CA THE",
	"HO KINH DOANH",
	"TAP DOAN",
	"TRACH NHIEM HUU HAN",
	"MOT THANH VIEN",
	"CO PHAN",
	"TNHH",
	"MTV",
)

# Duoi tieng Anh hay dinh sau ten, khong phan biet ai voi ai.
DUOI_TIENG_ANH = (
	"COMPANY LIMITED", "CO LTD", "CO., LTD", "CO.,LTD",
	"JOINT STOCK COMPANY", "CORPORATION", "LIMITED",
	"JSC", "LTD", "LLC", "INC", "CORP",
)

LOI_TEN_CUT = (
	"Tên pháp nhân đang thiếu, chuỗi này chỉ có loại hình doanh nghiệp mà "
	"không có tên riêng. Vui lòng mở tra cứu mã số thuế hoặc xem giấy phép "
	"kinh doanh của khách rồi điền đầy đủ trước khi xuất hoá đơn."
)

CANH_BAO_TEN_CUT = (
	"Hệ thống nghi ngờ tên công ty bị thiếu. Vui lòng kiểm tra lại thông tin!"
)


def bo_dau(s):
	"""Bo dau tieng Viet, giu nguyen do dai tung ky tu."""
	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D")


def _got(ten):
	"""Chuan hoa de so khop cum: bo dau, hoa het, gom khoang trang."""
	t = bo_dau(ten).upper()
	t = re.sub(r"[.,;:()\-_/\\\"']+", " ", t)
	return re.sub(r"\s+", " ", t).strip()


def phan_rieng(ten):
	"""Phan con lai sau khi boc het loai hinh phap ly. Chuoi da got.

	"CONG TY TNHH IMAE"                 -> "IMAE"
	"CONG TY CO PHAN"                   -> ""
	"CHI NHANH CONG TY TNHH ABC"        -> "ABC"
	"CONG TY TNHH THUONG MAI"           -> "THUONG MAI"

	Chu y truong hop cuoi: nganh nghe KHONG bi boc. Chi boc loai hinh phap
	ly. Boc them nganh nghe se de bao nham nhung cong ty ma ten rieng cua ho
	chinh la mot tu nganh nghe.
	"""
	t = _got(ten)
	if not t:
		return ""
	# Boc tu DAU chuoi, lap lai chung nao con boc duoc. Lap la de xu ly
	# "CHI NHANH CONG TY TNHH ABC" - hai cum lien tiep.
	doi = True
	while doi:
		doi = False
		for cum in CUM_LOAI_HINH:
			if t == cum:
				return ""
			if t.startswith(cum + " "):
				t = t[len(cum) + 1:].strip()
				doi = True
				break
	# Boc duoi tieng Anh o CUOI chuoi.
	doi = True
	while doi:
		doi = False
		for cum in DUOI_TIENG_ANH:
			c = _got(cum)
			if t == c:
				return ""
			if t.endswith(" " + c):
				t = t[: -(len(c) + 1)].strip()
				doi = True
				break
	return t


def thieu_ten_rieng(ten):
	"""True khi chuoi nay chi co loai hinh phap ly, khong co ten rieng.

	Chuoi rong cung tra True: khong co ten thi cung khong xuat hoa don duoc.
	"""
	return not phan_rieng(ten)


# ------------------------------------------------------- dien giai thay the

# ------------------------------------------------------------- o dia chi

# Ky tu gach dau dong hay dinh theo khi dan mot dong tu khoi thong tin khach
# gui qua Pancake hay Zalo. Viet bang ma escape chu khong go thang, de tep
# nay khong chua dau gach dai (quy uoc trinh bay cua tiem).
KY_TU_DAU_DONG = "-+*>\u2022\u00b7\u2013\u2014\u25cf\u25aa"

# Nhan dung truoc dau hai cham. Da got: bo dau, hoa het, gom khoang trang.
NHAN_DIA_CHI = ("DIA CHI", "DC", "D C", "ADDRESS", "ADD", "DIACHI")

# Nhan chi duoc coi la nhan khi nam gan dau chuoi. Dia chi that co the co
# dau hai cham o giua ("Lo A: 12 Nguyen Van Cu"), va boc cai do la an mat
# mot phan dia chi.
XA_NHAT_CUA_NHAN = 24


def _boc_mot_lop_dia_chi(t):
	"""Boc MOT lop gach dau dong hoac MOT nhan o dau chuoi. THUAN."""
	t = t.lstrip(KY_TU_DAU_DONG + " \t")
	i = t.find(":")
	if 0 < i <= XA_NHAT_CUA_NHAN and _got(t[:i]) in NHAN_DIA_CHI:
		t = t[i + 1:]
	return t.strip()


def sach_dia_chi_xhd(chuoi):
	"""Boc tien to gach dau dong va nhan "Dia chi:" dinh o DAU o dia chi. THUAN.

	Vi sao can. Ngay 05/09/2026 ra soat thay nam to hoa don DA PHAT HANH mang
	o dia chi nguoi mua bat dau bang chinh cai nhan, vi du:

	    "- Dia chi: Tang Tret Phoenix 1A, 547-549 duong Ta Quang Buu, ..."
	    "+ Dia chi :Tang 10, Sofic Tower, So 10 Duong Mai Chi Tho, ..."

	Khach nhan mot khoi thong tin xuat hoa don qua Pancake, sales chep nguyen
	mot dong dan vao o, va o do truoc nay chi `.strip()` khoang trang nen chu
	"Dia chi" di thang len to hoa don dien tu.

	Chi boc o DAU chuoi va chi boc nhan khop TUYET DOI. Dia chi that bat dau
	bang so nha, bang "Tang", bang "Lo" thi khong bi dung toi.

	Boc toi da hai lop, du cho truong hop vua co gach dau dong vua co nhan.
	Khong boc vong vo han: chuoi la chi toan dau gach thi phai tra ve rong
	chu khong duoc chay mai.
	"""
	t = str(chuoi or "").strip()
	for _ in range(2):
		moi = _boc_mot_lop_dia_chi(t)
		if moi == t:
			break
		t = moi
	return t


def mau_va_ky_hieu(ky_hieu):
	"""Tach "mau so" va "ky hieu" tu chuoi in tren to hoa don.

	Thong tu 78/2021/TT-BTC: ky hieu MAU SO hoa don la MOT chu so, ky hieu
	hoa don la SAU ky tu. Tren ban the hien hai phan nay in lien nhau, vi du
	"1C26MPV" nghia la mau so 1, ky hieu C26MPV.

	Nhan ca hai dang. Doc khong ra thi tra ("", chuoi da got) chu khong doan
	bua: mot con so mau sai tren to thay the la mot to sai luat.
	"""
	kh = _got(ky_hieu).replace(" ", "")
	if len(kh) == 7 and kh[0].isdigit():
		return kh[0], kh[1:]
	return "", kh


def _ngay_vn(ngay):
	"""Ngay ve dang dd/mm/yyyy. Nhan ISO, nhan doi tuong ngay, nhan san dd/mm/yyyy."""
	s = str(ngay or "").strip()
	if not s:
		return ""
	m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
	if m:
		return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1))
	m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
	if m:
		return "%02d/%02d/%s" % (int(m.group(1)), int(m.group(2)), m.group(3))
	return s


def dien_giai_thay_the(so_cu, ky_hieu_cu=None, ngay_cu=None, mau_cu=None):
	"""Cau bat buoc tren to hoa don thay the.

	"Thay thế cho hóa đơn số 10901, Mẫu số 1, Ký hiệu C26MPV, ngày 22/08/2026"

	Thieu phan nao thi BO phan do di chu khong in cai o trong: mot to hoa
	don ghi "Mẫu số [trống]" con te hon la khong ghi. Thieu so hoa don cu
	thi tra RONG han, vi cau nay khong con nghia gi nua.
	"""
	so = str(so_cu or "").strip()
	if not so:
		return ""
	mau = str(mau_cu or "").strip()
	kh = str(ky_hieu_cu or "").strip()
	if not mau:
		mau, kh = mau_va_ky_hieu(kh)
	phan = ["Thay thế cho hóa đơn số %s" % so]
	if mau:
		phan.append("Mẫu số %s" % mau)
	if kh:
		phan.append("Ký hiệu %s" % kh)
	ng = _ngay_vn(ngay_cu)
	if ng:
		phan.append("ngày %s" % ng)
	return ", ".join(phan)


def chen_dien_giai(dien_giai_goc, so_cu, ky_hieu_cu=None, ngay_cu=None, mau_cu=None):
	"""Chen cau thay the vao NGAY DAU dien giai cua to moi.

	Khong co so cu thi tra nguyen dien giai goc, khong dong them gi. Da co
	san cau do o dau roi thi khong chen lan hai - ham nay phai lap lai duoc,
	vi mot lan xuat lai la mot lan chay lai.
	"""
	goc = str(dien_giai_goc or "").strip()
	cau = dien_giai_thay_the(so_cu, ky_hieu_cu, ngay_cu, mau_cu)
	if not cau:
		return goc
	if goc.startswith(cau):
		return goc
	return cau + (". " + goc if goc else "")
