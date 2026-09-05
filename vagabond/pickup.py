# -*- coding: utf-8 -*-
"""Pickup: khach ra tan diem nhan hang, khong co shipper nao chay xe.

Vi sao co tep nay (anh Viet 05/09/2026)
---------------------------------------
O o phan cong truoc day chi co hai loai nguoi giao: shipper noi bo, hoac
mot don vi ngoai (Ahamove, Grab, BE...). Don nao khach hen ra tiem lay thi
sales khong biet gan cho ai. Hai cach chua chay deu hong:

  - Gan tam mot shipper roi nho mieng "don nay khach tu lay". Ban shipper
    mo app ra thay mot don khong biet di dau, con don thi nam trong tab
    Dang giao suot ngay.
  - De trong. Don nam mai o tab "Can phan cong" lam roi danh sach, va
    nguoi truc quay khong he biet co mot hop banh dang cho khach toi lay.

Nay them loai thu ba: gan cho mot DIEM. Ba diem lay chinh la ba diem ban
da khai o vagabond/diem_ban.py. KHONG go lai ten diem o day: go lai la co
ngay hai noi noi khac nhau, dung cai bay da lam mat 37 hoa don hom 10/08.
Cho nay chi giu them mot thu ma diem_ban khong co, la ten ngan de doc tren
o phan cong: "Pickup tai 9TCV" de hon "Pickup tai The Vagabond District 1".

Don da gan diem thi:
  - roi khoi tab "Can phan cong", sang tab rieng "Khach tu lay"
  - mang trang thai "Cho khach lay", khong phai "Dang giao" - khong ai
    dang chay xe ca, noi Dang giao la noi sai voi nguoi doc man hinh
  - hien chip theo tung diem de nguoi truc quay loc ra dung phan cua minh
  - van dung y nguyen ba buoc cua shipper: chup anh, lay chu ky khach, bam
    hoan tat. Bam hoan tat thi Pancake nhan trang thai da nhan nhu moi don
    khac, khong co duong rieng nao.

Phan THUAN o day khong cham Frappe, de bo kiem thu chay duoc khong can
site. Phan doc cau hinh diem nam duoi cung, mot ham.
"""

TRANG_THAI = "Chờ khách lấy"

# Ten ngan cho o phan cong. Chi la NHAN HIEN THI; ma diem van la ma cua
# diem_ban. Diem moi khong khai o day thi roi ve ten ngan cua diem do,
# nen mo chi nhanh thu tu khong phai sua tep nay.
NHAN_NGAN = {
	"SALES": "307/1",
	"TCV": "9TCV",
	"NVHTN": "NVHTN",
}

TIEN_TO = "Pickup tại "


def chuan_ma(ma):
	"""Chuan hoa ma diem: bo khoang trang, viet hoa. Rong tra ve rong."""
	return str(ma or "").strip().upper()


def ngan_cua(d):
	"""Ten ngan cua mot diem (dict tu diem_ban.ds())."""
	if not isinstance(d, dict):
		return ""
	ma = chuan_ma(d.get("ma"))
	if ma in NHAN_NGAN:
		return NHAN_NGAN[ma]
	return str(d.get("ten_ngan") or d.get("ten") or ma or "").strip()


def nhan_cua(d):
	"""Nhan day du hien tren o phan cong: 'Pickup tai 9TCV'."""
	ng = ngan_cua(d)
	return (TIEN_TO + ng) if ng else ""


def tu_ds(ds_diem):
	"""Doi danh sach diem ban thanh danh sach lua chon pickup.

	Moi phan tu: {ma, nhan, ngan, dia_chi}. Giu nguyen thu tu cua diem_ban
	de o phan cong xep giong moi man khac.
	"""
	ra = []
	for d in ds_diem or []:
		if not isinstance(d, dict):
			continue
		ma = chuan_ma(d.get("ma"))
		if not ma:
			continue
		ra.append({
			"ma": ma,
			"nhan": nhan_cua(d),
			"ngan": ngan_cua(d),
			"dia_chi": str(d.get("dia_chi") or "").strip(),
		})
	return ra


def hop_le(ma, ds_pickup):
	"""Ma diem co nam trong danh sach pickup khong."""
	m = chuan_ma(ma)
	return bool(m) and any(x.get("ma") == m for x in (ds_pickup or []))


def tim(ma, ds_pickup):
	m = chuan_ma(ma)
	for x in ds_pickup or []:
		if x.get("ma") == m:
			return x
	return None


def loi_ma_la(ma, ds_pickup):
	"""Cau bao loi theo QT-24: noi ro sai cai gi va chon lai o dau."""
	ten = ", ".join([x.get("ngan") or x.get("ma") for x in (ds_pickup or [])])
	return (
		"Không có điểm pickup nào mang mã %s. Các điểm đang bật: %s. "
		"Mở lại ô Phân công rồi chọn trong danh sách." % (chuan_ma(ma) or "(rỗng)", ten or "(chưa khai điểm nào)")
	)


# ------------------------------------------------------------- doc cau hinh

def ds():
	"""Danh sach diem pickup, lay tu diem_ban dang bat."""
	from vagabond import diem_ban

	return tu_ds(diem_ban.ds(chi_bat=True))
