"""Doc gia mot dong hang tren don Pancake. THUAN, khong cham Frappe.

Vi sao tach ra mot tep rieng
----------------------------
Cong kiem truoc deploy (`kiem_diem_otp.py`) boc ma nguon cua tung ham roi
chay tran, khong co Frappe, khong co site. Phep tinh gia ma nam trong
`ban_hang.py` thi khong kiem duoc, vi tep do `import frappe` ngay dong dau.
Cung ly do da tach `khop_sao_ke.py` ra khoi `doi_soat_sepay.py` o v295.

Loi da xay ra that, don 91853 ngay 22/08/2026
---------------------------------------------
Pancake gui ve HAI truong di cung nhau tren moi dong hang:

    discount_each_product   con so giam
    is_discount_percent     con so do la PHAN TRAM hay la DONG

Tu truoc toi nay ma cua tiem chi doc con so, khong doc co. Don 91853 co
`discount_each_product = 5` kem `is_discount_percent = true`, y la giam 5
PHAN TRAM. May tru thang 5 DONG:

    dung : 2.200.000 - 5%  = 2.090.000
    sai  : 2.200.000 - 5đ  = 2.199.995

Khach chuyen dung 7.820.000, phieu ben minh ghi 8.229.970. Chenh 409.970.

Quet 2.623 don tu 01/07 den 24/08/2026 thi co 6 don dinh, trong do hai don
si banh trung thu chua dong bo ve (63 hop giam 10%, 39 hop giam 7%) - neu
khong sua truoc khi dong bo thi hai don do sai gan chin trieu.

Vi sao KHONG dung thang truong `discount` cua Pancake
----------------------------------------------------
Pancake co san truong `discount` la so tien giam moi don vi (110.000 cho
dong 2.200.000 giam 5%). Dung no thi ngan hon that. Nhung do la con so
Pancake TU TINH, minh khong biet no gom nhung gi: co tinh ca khuyen mai
cap don khong, co tru truoc thue khong. Doc hai truong goc roi tu tinh thi
minh biet chinh xac minh dang tinh gi. Con `discount` thi dung lam phep
DOI CHIEU o `lech_tong` ben duoi - hai duong tinh doc lap gap nhau moi tin.
"""


def _so(v):
	"""Doi ve so thuc. Doc khong ra thi tra 0, khong nem loi.

	Khong dung frappe.utils.flt: tep nay phai chay duoc khi khong co Frappe.
	"""
	try:
		return float(v)
	except (TypeError, ValueError):
		return 0.0


def la_phan_tram(dong):
	"""Dong hang nay dang giam theo phan tram hay theo so tien?

	Nhan ca dict lan doi tuong co thuoc tinh. Thieu co thi coi nhu KHONG
	phai phan tram, tuc giu nguyen cach hieu cu - mot don cu khong co truong
	nay khong duoc doi nghia sau lung.
	"""
	if isinstance(dong, dict):
		v = dong.get("is_discount_percent")
	else:
		v = getattr(dong, "is_discount_percent", None)
	if isinstance(v, str):
		return v.strip().lower() in ("1", "true", "yes", "t")
	return bool(v)


def giam_moi_don_vi(gia, giam, phan_tram=False):
	"""So tien giam cho MOT don vi hang.

	gia        gia niem yet mot don vi (retail_price)
	giam       con so Pancake gui (discount_each_product)
	phan_tram  con so do la phan tram hay la dong

	Chan hai dau:
	  - Giam am thi coi nhu khong giam. Mot con so am o day se lam gia
	    PHONG len, tuc ban dat hon gia niem yet ma khong ai thay.
	  - Giam qua gia thi cat bang gia. Gia am khong ton tai, va ERPNext se
	    nhan nguyen con so am do vao so cai.
	"""
	gia = _so(gia)
	giam = _so(giam)
	if giam <= 0:
		return 0.0
	if phan_tram:
		if giam > 100:
			giam = 100.0
		giam = gia * giam / 100.0
	if giam > gia:
		giam = gia
	return giam


def gia_mot_don_vi(gia, dong):
	"""Gia ban thuc te mot don vi, sau khi tru phan giam.

	dong la dict cua mot dong hang Pancake. Tra ve so khong am.
	"""
	gia = _so(gia)
	giam_raw = dong.get("discount_each_product") if isinstance(dong, dict) else getattr(dong, "discount_each_product", 0)
	giam = giam_moi_don_vi(gia, giam_raw, la_phan_tram(dong))
	con = gia - giam
	return con if con > 0 else 0.0


def lech_tong(tong_minh, tong_pancake, nguong=1.0):
	"""So tien lech giua ban tinh cua minh va tong don ben Pancake.

	Tra 0 khi hai ben khop trong nguong cho phep. Nguong mac dinh 1 dong,
	du de bo qua sai so lam tron cua so thuc.

	Day la luoi cuoi cung, va no bat duoc ca nhung loi CHUA XAY RA: hom nay
	la truong `is_discount_percent`, mai kia Pancake them mot loai giam gia
	khac thi con so nay lech ngay, khong phai cho toi luc khach goi dien.
	"""
	pk = _so(tong_pancake)
	if pk <= 0:
		# Khong co gi de doi chieu thi im lang. Tra ve con so lech o day la
		# bia ra mot canh bao tu con so 0, va man hinh se ve dai bang do cho
		# moi don ma Pancake khong gui tong.
		return 0.0
	d = _so(tong_minh) - pk
	return 0.0 if abs(d) <= _so(nguong) else d
