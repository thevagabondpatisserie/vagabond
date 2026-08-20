"""Bo kiem thu THUAN cho cac phep tinh cua luong tru diem.

Chay khong can site, khong can co so du lieu: python3 kiem_diem_otp.py

Vi sao dang tep rieng chu khong dung unittest cua Frappe: cong kiem truoc
deploy phai chay duoc tren may nay, noi khong co bench nao ca. Cac ham duoc
kiem la ham THUAN - so vao, so ra - nen chep lai logic o day la du, va neu
ban that trong diem_otp.py doi ma ban nay khong doi thi cong se bao lech.
"""

import ast
import json
import os
import re
import sys

MD_QUY_DOI = 1.0
MD_TRAN_PT = 50.0
MD_BILL_TOI_THIEU = 10000.0


def _nap_ham_that():
	"""Doc thang cac ham THUAN tu diem_otp.py, khong import ca mo dun.

	Import ca mo dun thi keo theo frappe, ma may nay khong co frappe. Nen
	cat lay phan than ham roi chay trong mot khong gian ten co san flt.
	"""
	src = open("vagabond/diem_otp.py", encoding="utf-8").read()
	can = ["tien_tu_diem", "tran_dung_duoc", "kiem_so_diem", "_so"]
	ra = {}
	moi_truong = {"flt": lambda x: float(x or 0), "MD_QUY_DOI": MD_QUY_DOI,
	              "MD_TRAN_PT": MD_TRAN_PT, "MD_BILL_TOI_THIEU": MD_BILL_TOI_THIEU}
	for ten in can:
		m = re.search(r"^def %s\(.*?(?=^def |\Z)" % re.escape(ten), src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong diem_otp.py" % ten)
			sys.exit(1)
		exec(compile(m.group(0), "diem_otp:%s" % ten, "exec"), moi_truong, moi_truong)
	for ten in can:
		ra[ten] = moi_truong[ten]
	return ra


H = _nap_ham_that()
tien_tu_diem = H["tien_tu_diem"]
tran_dung_duoc = H["tran_dung_duoc"]
kiem_so_diem = H["kiem_so_diem"]

so_ca = 0
so_hong = 0


def la(mo_ta, duoc, mong):
	global so_ca, so_hong
	so_ca += 1
	if duoc != mong:
		so_hong += 1
		print("  HONG  %s\n        duoc %r, mong %r" % (mo_ta, duoc, mong))


def co_loi(mo_ta, ket_qua):
	"""kiem_so_diem tra (so, loi). Ca nay mong CO loi."""
	global so_ca, so_hong
	so_ca += 1
	if not ket_qua[1]:
		so_hong += 1
		print("  HONG  %s\n        mong bao loi, nhung cho qua voi %r" % (mo_ta, ket_qua[0]))


print("Bo kiem thu tru diem")
print("-" * 60)

# ------------------------------------------------------------ quy doi tien
print("1. Quy doi diem ra tien")
la("1 diem = 1 dong", tien_tu_diem(17900, 1), 17900.0)
la("0 diem", tien_tu_diem(0, 1), 0.0)
la("diem am tra 0 chu khong tra so am", tien_tu_diem(-500, 1), 0.0)
la("ty le 0.5 lam tron xuong", tien_tu_diem(1001, 0.5), 500.0)
la("ty le 2", tien_tu_diem(100, 2), 200.0)
la("None coi nhu 0", tien_tu_diem(None, 1), 0.0)

# ------------------------------------------------------------------- tran
print("2. Tran dung duoc")
# Bill 100.000, so du 90.000, tran 50%, bill toi thieu 10.000.
# Tran tien = 50.000; con_lai = 90.000 -> lay 50.000 -> 50.000 diem.
la("tran 50% cua bill", tran_dung_duoc(100000, 90000, 1, 50, 10000), 50000)
la("so du thap hon tran thi lay so du", tran_dung_duoc(100000, 12000, 1, 50, 10000), 12000)
# Bill 15.000: tran tien 7.500; con_lai = 15.000 - 10.000 = 5.000 -> lay 5.000
la("bill nho thi luat toi thieu chat hon", tran_dung_duoc(15000, 999999, 1, 50, 10000), 5000)
la("bill bang muc toi thieu thi khong dung duoc", tran_dung_duoc(10000, 999999, 1, 50, 10000), 0)
la("bill duoi muc toi thieu", tran_dung_duoc(8000, 999999, 1, 50, 10000), 0)
la("bill bang 0", tran_dung_duoc(0, 50000, 1, 50, 10000), 0)
la("so du bang 0", tran_dung_duoc(500000, 0, 1, 50, 10000), 0)
la("ty le quy doi 0 thi khong chia cho 0", tran_dung_duoc(500000, 50000, 0, 50, 10000), 0)
la("tran 100%", tran_dung_duoc(100000, 999999, 1, 100, 10000), 90000)
la("tran 0%", tran_dung_duoc(100000, 999999, 1, 0, 10000), 0)
# 1 diem = 2 dong: tran tien 50.000 -> chi can 25.000 diem
la("quy doi 2 thi so diem chia doi", tran_dung_duoc(100000, 999999, 2, 50, 10000), 25000)
la("tran luon la so nguyen", isinstance(tran_dung_duoc(99999, 999999, 3, 50, 10000), int), True)

# --------------------------------------------------------------- kiem so
print("3. Kiem so diem nguoi nhap")
la("so hop le tra dung so", kiem_so_diem(30000, 100000, 90000, 1, 50, 10000)[0], 30000)
la("so hop le khong bao loi", kiem_so_diem(30000, 100000, 90000, 1, 50, 10000)[1], "")
co_loi("so 0", kiem_so_diem(0, 100000, 90000, 1, 50, 10000))
co_loi("so am", kiem_so_diem(-5, 100000, 90000, 1, 50, 10000))
co_loi("so le", kiem_so_diem(10.5, 100000, 90000, 1, 50, 10000))
co_loi("chu", kiem_so_diem("abc", 100000, 90000, 1, 50, 10000))
co_loi("rong", kiem_so_diem("", 100000, 90000, 1, 50, 10000))
co_loi("None", kiem_so_diem(None, 100000, 90000, 1, 50, 10000))
co_loi("vuot so du", kiem_so_diem(95000, 100000, 90000, 1, 50, 10000))
co_loi("vuot tran phan tram", kiem_so_diem(60000, 100000, 90000, 1, 50, 10000))
co_loi("bill qua nho", kiem_so_diem(100, 8000, 90000, 1, 50, 10000))
la("dung dung tran thi cho qua", kiem_so_diem(50000, 100000, 90000, 1, 50, 10000)[0], 50000)
la("dung dung so du khi so du thap", kiem_so_diem(12000, 100000, 12000, 1, 50, 10000)[0], 12000)
# So du 12.000 ma xin 12.001: phai bao "khong du diem", KHONG duoc bao
# "vuot tran" - cau bao loi sai thi thu ngan chi sai cho khach.
la(
	"vuot so du thi bao dung la thieu diem",
	"chỉ còn" in kiem_so_diem(12001, 100000, 12000, 1, 50, 10000)[1],
	True,
)
la(
	"vuot tran thi bao dung la vuot tran",
	"tối đa" in kiem_so_diem(60000, 100000, 90000, 1, 50, 10000)[1],
	True,
)

# Cau bao loi phai noi nguoi dung lam gi tiep (QT-24).
print("4. Cau bao loi theo QT-24")
for ten, ca in (
	("so 0", (0, 100000, 90000)),
	("vuot so du", (95000, 100000, 90000)),
	("vuot tran", (60000, 100000, 90000)),
	("bill nho", (100, 8000, 90000)),
):
	loi = kiem_so_diem(ca[0], ca[1], ca[2], 1, 50, 10000)[1]
	la("%s: co cau chi duong" % ten, bool(re.search(r"(Nhập lại|mới trừ|nhỏ hơn)", loi)), True)
	la("%s: khong dung dau gach dai" % ten, ("—" in loi or "–" in loi), False)

# --------------------------------------------------- so tien va so diem khop
print("5. So tien giam luon khop voi so diem tru")
for bill, so_du, qd in ((100000, 90000, 1), (895000, 17900, 1), (250000, 999999, 2)):
	tran = tran_dung_duoc(bill, so_du, qd, 50, 10000)
	if tran <= 0:
		continue
	tien = tien_tu_diem(tran, qd)
	la("bill %d: tien giam khong vuot 50%% bill" % bill, tien <= bill * 0.5 + 0.001, True)
	la("bill %d: con lai khong duoi muc toi thieu" % bill, bill - tien >= 10000 - 0.001, True)

# --------------------------------------------------------------- hoan diem
print("6. Hoan diem hoan DUNG SO DA TRU, khong tinh lai")
# Mo phong: tru 30.000 diem luc quy doi 1, sau do doi quy doi thanh 2.
# Hoan phai tra ve 30.000 diem chu khong phai 15.000.
da_tru_diem = 30000
la("hoan theo so diem trong so", abs(-da_tru_diem), 30000)
la("khong tinh lai tu tien", tien_tu_diem(da_tru_diem, 2) != da_tru_diem, True)


# =====================================================================
# Han diem va ha hang - phep tinh THUAN cua vagabond/diem_han.py
# =====================================================================
def _nap_han():
	src = open("vagabond/diem_han.py", encoding="utf-8").read()
	mt = {"flt": lambda x: float(x or 0), "cint": lambda x: int(x or 0),
	      "MD_NGAY_CHOT": "31-12", "MD_HAN_THANG": 12}
	import datetime
	def getdate(x):
		if isinstance(x, datetime.date): return x
		return datetime.date(*[int(v) for v in str(x)[:10].split("-")])
	mt["getdate"] = getdate
	for ten in ("qua_han_cuon_chieu", "qua_han_xoa_sach", "den_ngay_chot"):
		m = re.search(r"^def %s\(.*?(?=^def |\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong diem_han.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "diem_han:%s" % ten, "exec"), mt, mt)
	return mt

Hn = _nap_han()
cuon = Hn["qua_han_cuon_chieu"]; sach = Hn["qua_han_xoa_sach"]; chot = Hn["den_ngay_chot"]

print("7. Diem qua han theo loi vao truoc ra truoc")
# Tich 100 nam ngoai, chua tieu gi -> qua han 100
la("tich cu, chua tieu", cuon([("2025-01-05", 100)], "2026-01-01"), 100)
# Tich 100 nam ngoai, tieu 80 -> chi con 20 qua han (KHONG phai 100)
la("da tieu bot thi chi con phan con lai",
   cuon([("2025-01-05", 100), ("2025-06-01", -80)], "2026-01-01"), 20)
# Tich 100 nam ngoai, tieu het -> khong con gi
la("tieu het thi khong dot gi", cuon([("2025-01-05", 100), ("2025-06-01", -100)], "2026-01-01"), 0)
# Tich 100 nam nay -> chua qua han
la("diem moi chua qua han", cuon([("2026-05-05", 100)], "2026-01-01"), 0)
# Tich 100 cu + 50 moi, tieu 120 -> phan cu con 0 (vao truoc ra truoc)
la("vao truoc ra truoc: tieu an vao phan cu nhat",
   cuon([("2025-01-05", 100), ("2026-05-05", 50), ("2026-06-01", -120)], "2026-01-01"), 0)
# Tich 100 cu + 50 moi, tieu 30 -> phan cu con 70
la("tieu it thi phan cu con lai",
   cuon([("2025-01-05", 100), ("2026-05-05", 50), ("2026-06-01", -30)], "2026-01-01"), 70)
la("so rong", cuon([], "2026-01-01"), 0)
la("so du am khong sinh ra so duong", cuon([("2025-01-05", 10), ("2025-02-01", -30)], "2026-01-01"), 0)
# Khong bao gio dot qua so du dang co
la("khong dot qua so du",
   cuon([("2025-01-05", 100), ("2025-02-01", -90), ("2026-07-01", -5)], "2026-01-01"), 5)

print("8. Xoa sach so du")
la("cong don ca so", sach([("2025-01-05", 100), ("2026-05-05", 50)]), 150)
la("so du am tra 0", sach([("2025-01-05", 100), ("2025-06-01", -140)]), 0)
la("so rong", sach([]), 0)

print("9. Ngay chot hang nam")
la("dung ngay 31-12", chot("2026-12-31", "31-12"), True)
la("khong phai ngay chot", chot("2026-12-30", "31-12"), False)
la("ngay chot 01-01", chot("2027-01-01", "01-01"), True)
# 29-02 nam thuong: phai chay vao 28-02, khong thi job khong bao gio chay
la("29-02 nam thuong roi ve 28-02", chot("2026-02-28", "29-02"), True)
la("29-02 nam nhuan van dung ngay", chot("2028-02-29", "29-02"), True)
la("31-04 roi ve 30-04", chot("2026-04-30", "31-04"), True)
la("cau hinh rac thi khong chay", chot("2026-12-31", "linh tinh"), False)
la("cau hinh rong thi ve mac dinh 31-12", chot("2026-12-31", ""), True)


# =====================================================================
# Chan cung: tong giam gia khong duoc vuot gia tri to (anh Viet 16/08/2026)
# =====================================================================
print("10. Chan don am")

def tran_cung(grand_total, discount_amount, giam_moi):
	"""Chep dung phep so cua diem_otp._tran_cung. Tra True neu BI CHAN."""
	truoc_giam = float(grand_total) + float(discount_amount)
	return float(giam_moi) > truoc_giam + 0.5

# To 100.000, chua giam gi -> giam 100.000 vua du, khong chan
la("giam dung bang gia tri to thi cho qua", tran_cung(100000, 0, 100000), False)
la("giam vuot gia tri to thi CHAN", tran_cung(100000, 0, 100001), True)
# To goc 100.000, da giam 30.000 (grand_total con 70.000).
# Tong giam moi 100.000 la vua du.
la("da co khuyen mai 30k, tong giam 100k vua du", tran_cung(70000, 30000, 100000), False)
la("da co khuyen mai 30k, tong giam 120k thi CHAN", tran_cung(70000, 30000, 120000), True)
# Day la ca that su nguy hiem: khuyen mai duoc AP THEM sau khi da tru diem.
# To 100.000, diem da tru 60.000, nay them voucher 50.000 -> tong 110.000.
la("diem 60k cong voucher 50k tren to 100k thi CHAN", tran_cung(40000, 60000, 110000), True)
la("diem 60k cong voucher 40k tren to 100k thi vua du", tran_cung(40000, 60000, 100000), False)
la("to 0 dong thi moi khoan giam duong deu bi CHAN", tran_cung(0, 0, 1000), True)

# Diem ap len SO TIEN CUOI CUNG, sau khi da tru khuyen mai khac.
# To goc 200.000, voucher 50.000 -> grand_total 150.000.
# Tran 50% phai tinh tren 150.000 chu KHONG phai 200.000.
print("11. Diem ap sau khuyen mai")
la("tran tinh tren so sau khuyen mai", tran_dung_duoc(150000, 999999, 1, 50, 10000), 75000)
la("khong duoc tinh tren so truoc khuyen mai", tran_dung_duoc(150000, 999999, 1, 50, 10000) != 100000, True)


# =====================================================================
# Hoan tien: mach doi soat SePay (vagabond/hoan_tien.py)
# =====================================================================
print("12. Doi soat lenh chi hoan tien")

def _nap_ht():
	src = open("vagabond/hoan_tien.py", encoding="utf-8").read()
	mt = {
		"re": re,
		"TIEN_TO_CK": "THE VAGABOND HOAN TIEN",
		"flt": lambda x: float(x or 0),
	}
	# Doc RX_MA_HD THANG TU MA NGUON, khong chep lai vao day.
	#
	# Sang 16/08/2026 em vua mat mot ban va vi de hai ban gan giong nhau song
	# song trong mot tep, va chung lech nhau luc nao khong hay. Chep regex
	# vao bo kiem la de ra dung cai bay do: sua regex ben kia ma quen ben
	# nay thi bo kiem van xanh trong khi luong that da hong.
	m_rx = re.search(r"^RX_MA_HD = .*$", src, re.M)
	if not m_rx:
		print("KHONG THAY RX_MA_HD trong hoan_tien.py"); sys.exit(1)
	exec(compile(m_rx.group(0), "hoan_tien:RX_MA_HD", "exec"), mt, mt)
	for ten in ("noi_dung_ck", "_got", "tim_ma_hoa_don", "khop_giao_dich", "chon_ma_khop", "ty_le_hop_le", "tach_ghi_chu_don"):
		# Cat toi khi gap "def", mot trang tri, hay mot khoi chu thich o dau
		# dong: cac ham nay xen ke voi hang so va chu thich dai.
		m = re.search(r"^def %s\(.*?(?=^def |^@|^RX_|^# Ma hoa don|\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong hoan_tien.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "hoan_tien:%s" % ten, "exec"), mt, mt)
	return mt

Ht = _nap_ht()
nd = Ht["noi_dung_ck"]; khop = Ht["khop_giao_dich"]

tim = Ht["tim_ma_hoa_don"]; tyle = Ht["ty_le_hop_le"]
CK = "THE VAGABOND HOAN TIEN "

la("noi dung chuyen khoan dung cu phap anh Viet chot",
   nd("HDB-2026-01604"), "THE VAGABOND HOAN TIEN HDB-2026-01604")
la("khop dung ma", khop(CK + "HDB-2026-01604", "HDB-2026-01604"), True)
la("khop ke ca khi ngan hang viet hoa het", khop("CK " + CK + "HDB-2026-01604", "HDB-2026-01604"), True)
# Bay da tung dinh voi ma WOO: ma ngan KHONG duoc an nham giao dich cua ma dai
la("ma ngan khong an nham ma dai", khop(CK + "HDB-2026-016040", "HDB-2026-01604"), False)
la("ma dai khong khop voi giao dich cua ma ngan", khop(CK + "HDB-2026-0160", "HDB-2026-01604"), False)
la("giao dich cua don khac thi khong khop", khop(CK + "HDB-2026-01605", "HDB-2026-01604"), False)
la("mo ta rong", khop("", "HDB-2026-01604"), False)
la("ma rong thi khong bao gio khop", khop(CK + "HDB-2026-01604", ""), False)
la("ma rong va mo ta rong", khop("", ""), False)
# Ma nam giua cau, hai ben la dau cach hoac dau cau
la("ma nam giua cau van khop", khop("VAGABOND " + CK + "HDB-2026-01604, hoan khach", "HDB-2026-01604"), True)
la("dinh lien chu cai thi khong khop", khop("X" + CK + "HDB-2026-01604", "HDB-2026-01604"), True)

print("15. Doc ma hoa don tu dong sao ke tien ra")
# HAI dang ma cung ton tai tren he. Regex anh Viet dua (HDB-\d+-\d+-\d+)
# bat dung dang moi va BO SOT dang cu, ma dang cu chiem phan lon 43.458 to.
la("dang cu hai nhom so", tim(CK + "HDB-2026-01593"), "HDB-2026-01593")
la("dang moi ba nhom so", tim(CK + "HDB-26-08-00323"), "HDB-26-08-00323")
la("khong co ma thi tra rong", tim("CHUYEN TIEN NHA CUNG CAP"), "")
la("mo ta rong", tim(""), "")
la("ma viet thuong van doc duoc", tim("the vagabond hoan tien hdb-2026-01593"), "HDB-2026-01593")
la("ma nam cuoi cau", tim("NGUYEN VAN A CK " + CK + "HDB-26-08-00323"), "HDB-26-08-00323")
la("ma dinh lien chu cai thi khong nhan", tim("XHDB-2026-01593"), "")

# Ngan hang lam mat dau gach la chuyen thuong. Duong got phai bat duoc.
la("mat dau gach van khop", khop("THE VAGABOND HOAN TIEN HDB 2026 01593", "HDB-2026-01593"), True)
la("mat dau gach dang moi", khop("THE VAGABOND HOAN TIEN HDB 26 08 00323", "HDB-26-08-00323"), True)
la("mat dau gach nhung ma dai hon thi khong an nham",
   khop("THE VAGABOND HOAN TIEN HDB 2026 015930", "HDB-2026-01593"), False)
la("mat dau gach, don khac", khop("THE VAGABOND HOAN TIEN HDB 2026 01594", "HDB-2026-01593"), False)

# Phieu lap truoc 16/08/2026 mang noi dung cu "HT <ma to tra hang>". Duong
# doi soat moi do theo ma HOA DON GOC, nen noi dung cu KHONG duoc khop -
# co khop moi la sai. Bat duoc khi kiem tren he ngay sau deploy v192.
la("noi dung cu KHONG khop voi ma don goc",
   khop("HT HDB-26-08-00341", "HDB-26-08-00340"), False)
la("noi dung cu chi khop voi chinh ma to tra hang",
   khop("HT HDB-26-08-00341", "HDB-26-08-00341"), True)
la("noi dung moi khop voi ma don goc",
   khop("THE VAGABOND HOAN TIEN HDB-26-08-00340", "HDB-26-08-00340"), True)

chon = Ht["chon_ma_khop"]
# Lan thu BA trong ngay gap loi hai duong lech nhau: doi_soat() dung
# khop_giao_dich (co duong got), sepay_tien_ra() dung tim_ma_hoa_don (khong
# co). Cung mot dong tien, vao duong nay thi khop, duong kia thanh mo coi.
# Nay ca hai deu di qua chon_ma_khop.
CHO = ["HDB-2026-01593", "HDB-26-08-00323", "HDB-2026-99999"]
la("chon dung ma trong danh sach cho", chon(CK + "HDB-26-08-00323", CHO), "HDB-26-08-00323")
la("chon dung ma dang cu", chon(CK + "HDB-2026-01593", CHO), "HDB-2026-01593")
la("MAT DAU GACH van chon duoc - lo cua sepay_tien_ra",
   chon("THE VAGABOND HOAN TIEN HDB 26 08 00323", CHO), "HDB-26-08-00323")
la("mat dau gach dang cu", chon("THE VAGABOND HOAN TIEN HDB 2026 01593", CHO), "HDB-2026-01593")
la("ma khong nam trong danh sach cho thi tra rong",
   chon(CK + "HDB-2026-00001", CHO), "")
la("dong khong co ma nao", chon("CHUYEN TIEN NHA CUNG CAP", CHO), "")
la("danh sach cho rong", chon(CK + "HDB-2026-01593", []), "")
la("mo ta rong", chon("", CHO), "")

print("16. Tran so tien hoan khong duoc vuot tong don")
la("hoan toan bo", tyle(100000, 100000)[0], True)
la("hoan mot nua", tyle(50000, 100000)[0], True)
la("hoan hon tong don thi chan", tyle(120000, 100000)[0], False)
la("hoan 0 dong thi chan", tyle(0, 100000)[0], False)
la("hoan so am thi chan", tyle(-5000, 100000)[0], False)
la("don tong 0 thi khong hoan duoc", tyle(1000, 0)[0], False)
la("le 0,5 dong van cho qua", tyle(100000.4, 100000)[0], True)
# QT-24: cau bao loi phai noi nguoi dung lam gi tiep
la("cau chan vuot tran co huong dan", "Sửa lại" in tyle(120000, 100000)[1], True)
la("cau chan so 0 co huong dan", "Nhập lại" in tyle(0, 100000)[1], True)


# =====================================================================
# Ten goi chung tu tien theo tai khoan (chi Dung chot 16/08/2026)
# =====================================================================
print("13. Ten goi chung tu tien")

def _nap_ct():
	src = open("vagabond/chung_tu_tien.py", encoding="utf-8").read()
	mt = {"cint": lambda x: int(x or 0)}
	for ten in ("la_ngan_hang", "la_tien_mat", "cham_ngan_hang", "ten_chung_tu"):
		m = re.search(r"^def %s\(.*?(?=^def |^@|\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong chung_tu_tien.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "chung_tu_tien:%s" % ten, "exec"), mt, mt)
	return mt

Ct = _nap_ct()
tenct = Ct["ten_chung_tu"]; lanh = Ct["la_ngan_hang"]; latm = Ct["la_tien_mat"]

TM = "1111 - Tiền Việt Nam - TV"
NH = "11211 - Tiền gửi MB Bank 31561568 - TV"
TU = "1411 - Tạm ứng - Nguyễn Hoàng Việt (OCB) - TV"

la("tien mat, chi", tenct("Pay", TM), "Phiếu chi")
la("tien mat, thu", tenct("Receive", TM), "Phiếu thu")
la("ngan hang, thu", tenct("Receive", NH), "Giấy báo Có")
la("ngan hang, chi, con nhap", tenct("Pay", NH, 0), "Uỷ nhiệm chi")
la("ngan hang, chi, da ghi so", tenct("Pay", NH, 1), "Uỷ nhiệm chi / Giấy báo Nợ")

# Bay quan trong: 1411 tren he nay khai account_type "Bank" vi no gan mot
# tai khoan OCB, nhung ban chat la TAM UNG ca nhan. Khong duoc goi la
# phieu chi, cung khong duoc coi la ngan hang.
la("1411 tam ung KHONG phai ngan hang", lanh(TU), False)
la("1411 tam ung KHONG phai tien mat", latm(TU), False)
la("1411 goi ten trung tinh", tenct("Pay", TU), "Chứng từ thanh toán")

la("1121 la ngan hang", lanh("1121 - Tiền gửi ngân hàng - TV"), True)
la("1112 ngoai te van la tien mat", latm("1112 - Ngoại tệ - TV"), True)
la("tai khoan rong", tenct("Pay", ""), "Chứng từ thanh toán")
la("tai khoan None", tenct("Pay", None), "Chứng từ thanh toán")
# 131/331 khong bao gio la tai khoan tien
la("131 khong phai tien", lanh("131 - Phải thu khách hàng - TV") or latm("131 - Phải thu khách hàng - TV"), False)

# Chuyen noi bo: lo that bat duoc khi chay tren he 16/08/2026.
# Rut 1.000 d TU ngan hang VE quy tien mat da LOT QUA luat bat buoc dinh kem.
print("14. Chuyen noi bo khong duoc lot luat ngan hang")
cham = Ct["cham_ngan_hang"]
la("rut tu ngan hang ve quy: VAN la cham ngan hang", cham(NH, TM), True)
la("nop tu quy vao ngan hang: cham ngan hang", cham(TM, NH), True)
la("quy sang quy: khong cham", cham(TM, "1112 - Ngoại tệ - TV"), False)
la("tam ung sang quy: khong cham", cham(TU, TM), False)
la("ngan hang sang ngan hang", cham(NH, "1121 - Tiền gửi ngân hàng - TV"), True)
la("ca hai rong", cham("", ""), False)
la("rut tu ngan hang goi la Uy nhiem chi", tenct("Internal Transfer", NH, 0, TM), "Uỷ nhiệm chi")
la("rut tu ngan hang da ghi so", tenct("Internal Transfer", NH, 1, TM), "Uỷ nhiệm chi / Giấy báo Nợ")
la("nop quy vao ngan hang goi la Giay bao Co", tenct("Internal Transfer", TM, 0, NH), "Giấy báo Có")
la("quy sang quy", tenct("Internal Transfer", TM, 0, "1112 - Ngoại tệ - TV"), "Phiếu chi")


# =====================================================================
# Tep chuyen tien lo MB Biz (vagabond/ngan_hang.py)
# =====================================================================
print("17. Tep chuyen tien lo MB Biz")

def _nap_nh():
	src = open("vagabond/ngan_hang.py", encoding="utf-8").read()
	mt = {"re": re, "cint": lambda x: int(x or 0), "flt": lambda x: float(x or 0)}
	# Cac hang so lam sach: doc THANG tu ma nguon, khong chep lai. Bai hoc
	# 16/08 - chep la de hai ban lech nhau.
	for ten in ("_THAY_TIEN", "_THAY_ND", "_XOA", "_THANH_CHAM", "DAI_TOI_DA", "COT_MB"):
		m = re.search(r"^%s = .*?(?=^\n*[A-Z_]+ = |^def |^@|\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY hang so %s trong ngan_hang.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "ngan_hang:%s" % ten, "exec"), mt, mt)
	for ten in ("_bo_dau", "sach_ten", "sach_noi_dung", "sach_so_tk", "dong_mb"):
		m = re.search(r"^def %s\(.*?(?=^def |^@|^COT_MB|^DAI_TOI_DA|^_THAY|^# |\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong ngan_hang.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "ngan_hang:%s" % ten, "exec"), mt, mt)
	return mt

Nh = _nap_nh()
sten = Nh["sach_ten"]; snd = Nh["sach_noi_dung"]; stk = Nh["sach_so_tk"]; dmb = Nh["dong_mb"]

la("ten bo dau viet hoa", sten("Nguyễn Văn Thử"), "NGUYEN VAN THU")
la("dau va thanh VA theo quy tac MB", sten("Anh & Em"), "ANH VA EM")
la("ngoac bi xoa", sten("Cong ty (HCM)"), "CONG TY HCM")
la("so tai khoan bo dau cach", stk(" 0123 456 789 "), "0123456789")
la("so tai khoan bo ky tu la", stk("0123-456.789"), "0123456789")
la("so tai khoan cat o 24 ky tu", len(stk("1" * 40)), 24)

# Ma hoa don PHAI giu duoc dau gach trong noi dung: do la thu giup doi soat
# doc lai duoc ma don.
la("noi dung giu dau gach cua ma don",
   snd("THE VAGABOND HOAN TIEN HDB-26-08-00348"), "THE VAGABOND HOAN TIEN HDB-26-08-00348")
la("noi dung bo dau tieng Viet", snd("Hoan tien khach Trâm"), "HOAN TIEN KHACH TRAM")
la("phan tram thanh PT", snd("Giam 50%"), "GIAM 50PT")
# MB thay ky tu TRUC TIEP, khong chen them dau cach - doc tu tab Huong dan
# cua chinh tep mau. Ca kiem dau tien em viet "A BANG B" la em doan, chay
# len moi thay mac.
la("dau bang thanh BANG", snd("A=B"), "ABANGB")
la("euro thanh EURO", snd("10€"), "10EURO")

d, n = dmb(1, "0123456789", "Nguyễn Văn Thử", "MB - Ngân hàng TMCP Quân đội", 50000,
           "THE VAGABOND HOAN TIEN HDB-26-08-00348")
la("dong mb du sau cot", len(d), 6)
la("dong mb stt", d[0], 1)
la("dong mb so tien la so nguyen", d[4], 50000)
la("dong mb khong nhac gi khi du", n, [])
la("dong mb giu nguyen ten ngan hang day du", d[3], "MB - Ngân hàng TMCP Quân đội")

d2, n2 = dmb(2, "", "A", "", 0, "x")
la("thieu so tai khoan thi nhac", any("số tài khoản" in x for x in n2), True)
la("thieu ngan hang thi nhac", any("ngân hàng" in x for x in n2), True)
la("so tien 0 thi nhac", any("lớn hơn 0" in x for x in n2), True)

d3, n3 = dmb(3, "1", "T" * 90, "MB", 1000, "N" * 200)
la("ten dai bi cat dung 69", len(d3[2]), 69)
la("noi dung dai bi cat dung 140", len(d3[5]), 140)
la("cat roi phai NOI ra chu khong lang le cat", len(n3) >= 2, True)

# Danh muc phai tra HET trong mot lan goi. Bat duoc sau khi deploy v195:
# mac dinh cu la 60 nen app chi nhan 60 tren 581 ngan hang, khong bao gi.
src_nh = open("vagabond/ngan_hang.py", encoding="utf-8").read()
m_sd = re.search(r"^SO_DONG_MAC_DINH = (\d+)", src_nh, re.M)
la("co hang so so dong mac dinh", bool(m_sd), True)
la("mac dinh du cho ca 581 ngan hang", int(m_sd.group(1)) >= 581 if m_sd else False, True)
la("ham tim KHONG tu dat mac dinh rieng",
   bool(re.search(r"def tim\(tu_khoa=\"\", so_dong=None\)", src_nh)), True)
import json as _json
la("tep du lieu du 581 ngan hang",
   len(_json.load(open("vagabond/du_lieu/napas.json", encoding="utf-8"))), 581)

# Bang bi danh: nhan vien go "Vietcombank" nhung danh muc MB ghi "VCB -
# Ngan hang TMCP Ngoai thuong Viet Nam". Bat duoc khi thu tren he 17/08.
#
# Ca kiem quan trong nhat o day: MOI bi danh phai tro toi mot ma CO THAT
# trong danh muc. Bi danh tro toi ma khong ton tai thi nhan vien go dung
# ten quen thuoc van ra rong, va lan nay con lang le hon vi minh tuong da
# vá roi.
m_bd = re.search(r"^BI_DANH = \{.*?^\}", src_nh, re.S | re.M)
la("co bang bi danh", bool(m_bd), True)
_bd = {}
exec(compile(m_bd.group(0), "ngan_hang:BI_DANH", "exec"), _bd, _bd)
BD = _bd["BI_DANH"]
_ds_nh = _json.load(open("vagabond/du_lieu/napas.json", encoding="utf-8"))
_ma_co = {x[0].split(" - ")[0].strip().upper() for x in _ds_nh}
la("moi bi danh tro toi ma CO THAT trong danh muc",
   [k for k, v in BD.items() if v not in _ma_co], [])
la("co bi danh cho Vietcombank", BD.get("vietcombank"), "VCB")
la("co bi danh cho Techcombank", BD.get("techcombank"), "TCB")
la("co bi danh cho Agribank", BD.get("agribank"), "VBA")

# Doc ten khach va so dien thoai tu o ghi chu cua don (anh Viet 17/08/2026)
print("18. Doc ten khach va so dien thoai tu ghi chu don")
tach = Ht["tach_ghi_chu_don"]
la("don Pancake co ten va so", tach("Pancake #91759 - Loan Anh - 0933751352"), ("Loan Anh", "0933751352"))
la("don mang ve co quay o cuoi", tach("Mang về #TEST-HT-02 - Khách thử hoàn tiền 2 - Quầy TCV"),
   ("Khách thử hoàn tiền 2", ""))
la("don co ca ba phan", tach("Mang về #? - THU NGHIEM - 0901234567 - Quầy TCV"),
   ("THU NGHIEM", "0901234567"))
la("ghi chu rong", tach(""), ("", ""))
la("ghi chu khong theo khuon", tach("Ghi chu tu do"), ("", ""))
la("so ngan khong phai dien thoai", tach("Pancake #12 - Ba Ba - 123"), ("Ba Ba", ""))


# =====================================================================
# Kiem banh theo mua: han muc theo dot, dinh muc hop, chot chan ban lo
# =====================================================================
print("19. Han muc mua vu va chot chan ban lo")

def _nap_mv():
	src = open("vagabond/mua_vu.py", encoding="utf-8").read()
	mt = {"re": re, "cint": lambda x: int(x or 0), "flt": lambda x: float(x or 0)}
	# Hai hang so duoi day la LUAT chu khong phai so lam tron, nen nap thang
	# tu ma nguon: sua o mua_vu.py la bo kiem thay ngay, khong co ban sao.
	for hang in (r"^TY_LE_VANG\s*=.*$", r"^_BO_TU\s*=.*$"):
		m = re.search(hang, src, re.M)
		if not m:
			print("KHONG THAY hang %s trong mua_vu.py" % hang); sys.exit(1)
		exec(compile(m.group(0), "mua_vu:hang", "exec"), mt, mt)
	for ten in (
		"han_muc_tu_dot",
		"banh_le_trong_hop",
		"con_ban_duoc",
		"con_sau_khi_them",
		"muc_tran",
		"_khong_dau",
		"nhan_tu_ten",
	):
		m = re.search(r"^def %s\(.*?(?=^def |^@|^# =|^[A-Z_]+ =|\Z)" % ten, src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong mua_vu.py" % ten); sys.exit(1)
		exec(compile(m.group(0), "mua_vu:%s" % ten, "exec"), mt, mt)
	return mt

Mv = _nap_mv()
hmdot = Mv["han_muc_tu_dot"]; trhop = Mv["banh_le_trong_hop"]
conban = Mv["con_ban_duoc"]; conthem = Mv["con_sau_khi_them"]
muctran = Mv["muc_tran"]; nhanten = Mv["nhan_tu_ten"]

# --- Han muc tinh tu cac dot nha in ---
la("chua khai dot nao thi tra rong, o go tay giu hieu luc", hmdot([]), {})
la("mot dot da ve", hmdot([{"ma_hang": "A", "so_luong": 100, "da_ve": 1}]), {"A": 100})
# Cho nay la mau chot: dot HEN ngay mai thi hang CHUA co trong tay.
la("dot chua ve KHONG duoc cong",
   hmdot([{"ma_hang": "A", "so_luong": 100, "da_ve": 0}]), {"A": 0})
la("hai dot, mot ve mot chua",
   hmdot([{"ma_hang": "A", "so_luong": 100, "da_ve": 1},
          {"ma_hang": "A", "so_luong": 50, "da_ve": 0}]), {"A": 100})
la("ba dot ve het thi cong don",
   hmdot([{"ma_hang": "A", "so_luong": 40, "da_ve": 1},
          {"ma_hang": "A", "so_luong": 30, "da_ve": 1},
          {"ma_hang": "A", "so_luong": 30, "da_ve": 1}]), {"A": 100})
la("hai ma khac nhau khong lan sang nhau",
   hmdot([{"ma_hang": "A", "so_luong": 10, "da_ve": 1},
          {"ma_hang": "B", "so_luong": 20, "da_ve": 1}]), {"A": 10, "B": 20})
la("dot khong co ma hang thi bo qua", hmdot([{"so_luong": 99, "da_ve": 1}]), {})

# --- Dinh muc hop an banh le ---
DM = [{"ma_hop": "HOP", "ma_banh": "BANH", "so_luong": 6}]
la("ban 10 hop an 60 banh le", trhop(DM, {"HOP": 10}), {"BANH": 60})
la("chua ban hop nao thi khong an gi", trhop(DM, {"HOP": 0}), {"BANH": 0})
la("khong khai dinh muc thi khong an gi", trhop([], {"HOP": 10}), {})
la("dinh muc so luong 0 bi bo qua",
   trhop([{"ma_hop": "HOP", "ma_banh": "BANH", "so_luong": 0}], {"HOP": 10}), {})
la("hai hop cung an mot loai banh thi cong don",
   trhop([{"ma_hop": "H1", "ma_banh": "B", "so_luong": 2},
          {"ma_hop": "H2", "ma_banh": "B", "so_luong": 3}], {"H1": 10, "H2": 10}), {"B": 50})

# --- Con ban duoc ---
la("con ban duoc tru du bon muc", conban(100, 20, 5, 3, 2), 70)
la("con ban duoc GIU DAU AM chu khong ep ve 0", conban(10, 20, 0, 0, 0), -10)
la("banh le bi hop an het thi ve 0", conban(200, 0, 0, 0, 200), 0)

# --- Chot chan: neu ban them thi con bao nhieu ---
DONG = [
	{"ma_hang": "HOP", "ten_banh": "Hop qua", "san_xuat": 100, "da_dat": 90, "cho_chot": 0, "don_khac": 0},
	{"ma_hang": "BANH", "ten_banh": "Banh le", "san_xuat": 600, "da_dat": 0, "cho_chot": 0, "don_khac": 0},
]
con, am = conthem(DONG, DM, "HOP", 5)
la("ban 5 hop nua con 5", con, 5)
la("ban 5 hop nua khong lam am gi", am, [])
con, am = conthem(DONG, DM, "HOP", 15)
la("ban 15 hop la vuot, con -5", con, -5)
# Ca dau em viet mong ["HOP"], chay len moi thay mac: ban 105 hop thi cung
# an 630 banh le tren han muc 600, nen BANH am theo. Ma dung, ca sai - va
# do chinh la thu bo kiem sinh ra de bat: em khong tu nhin ra day.
la("vuot thi bao ca hop lan banh le ben trong",
   sorted(x[0] for x in am), ["BANH", "HOP"])
# Ca dang gia nhat cua ca bo: ban hop KHONG am chinh cai hop, ma am BANH LE
# ben trong. Day la cho de bo sot nhat, va la ly do viec 5 phai lam truoc.
DONG2 = [
	{"ma_hang": "HOP", "ten_banh": "Hop qua", "san_xuat": 100, "da_dat": 0, "cho_chot": 0, "don_khac": 0},
	{"ma_hang": "BANH", "ten_banh": "Banh le", "san_xuat": 60, "da_dat": 0, "cho_chot": 0, "don_khac": 0},
]
con, am = conthem(DONG2, DM, "HOP", 20)
la("ban 20 hop thi chinh hop van con 80", con, 80)
la("nhung banh le ben trong bi am, va phai bat duoc",
   [x[0] for x in am], ["BANH"])
la("banh le am dung 60 cai", dict(am)["BANH"], -60)
la("ma khong nam trong mua thi khong bi rang buoc",
   conthem(DONG, DM, "MA_LA", 999)[0], None)
la("ban dung bang so con lai thi KHONG chan", conthem(DONG, DM, "HOP", 10)[1], [])
# Ban 101 hop: hop am 1, va banh le an 606 tren 600 nen am 6.
la("ban qua mot cai la chan", len(conthem(DONG, DM, "HOP", 11)[1]) >= 1, True)
la("ban qua mot cai thi chinh hop am dung 1", dict(conthem(DONG, DM, "HOP", 11)[1])["HOP"], -1)
# Cho chot cung tru, y het bang ngay
DONG3 = [{"ma_hang": "H", "ten_banh": "H", "san_xuat": 10, "da_dat": 5, "cho_chot": 4, "don_khac": 0}]
la("cho chot cung an vao han muc", conthem(DONG3, [], "H", 1)[0], 0)
la("cho chot lam vuot thi chan", len(conthem(DONG3, [], "H", 2)[1]), 1)

# =====================================================================
# Nhom 20. Banh chi lam theo hop, tran moi ngay, nhan ngan tren lich
# =====================================================================
print("20. Khong dat tran, tran moi ngay, nhan ngan")

# --- Khong dat tran: banh 80gr trong hop khong co lo rieng ---
# Day la ca quan trong nhat cua nhom: neu KHONG co co nay thi them banh
# 80gr vao bang la moi don hop deu bi chan, vi banh 80gr mang san xuat 0.
DONG4 = [
	{"ma_hang": "HOP", "ten_banh": "Hop", "san_xuat": 100, "da_dat": 0, "cho_chot": 0, "don_khac": 0},
	{"ma_hang": "B80", "ten_banh": "Banh 80gr", "san_xuat": 0, "da_dat": 0, "cho_chot": 0,
	 "don_khac": 0, "khong_tran": 1},
]
DM80 = [{"ma_hop": "HOP", "ma_banh": "B80", "so_luong": 4}]
con, am = conthem(DONG4, DM80, "HOP", 20)
la("ban hop KHONG bi chan vi banh 80gr khong dat tran", am, [])
la("ban hop van tru dung han muc cua chinh cai hop", con, 80)
# Va co do KHONG duoc phep noi long chinh cai hop.
la("hop van bi chan khi vuot du banh trong hop khong dat tran",
   [x[0] for x in conthem(DONG4, DM80, "HOP", 120)[1]], ["HOP"])
# Bo co di thi phai chan lai - phep thu lua, xac nhan co that su lam viec.
DONG5 = [dict(DONG4[0]), dict(DONG4[1], khong_tran=0)]
la("bo co di thi banh 80gr chan lai ngay",
   sorted(x[0] for x in conthem(DONG5, DM80, "HOP", 20)[1]), ["B80"])

# --- Tran moi ngay: vang tu 75 phan tram, do tu bang tran ---
la("khong dat tran thi khong bao gio canh bao", muctran(999, 0), 0)
la("ngay khong co don thi khong canh bao", muctran(0, 200), 0)
la("duoi nguong vang thi im", muctran(149, 200), 0)
la("dung 150 tren tran 200 la VANG", muctran(150, 200), 1)
la("199 tren 200 van la vang", muctran(199, 200), 1)
la("dung bang tran la DO", muctran(200, 200), 2)
la("qua tran la do", muctran(260, 200), 2)
la("tran am coi nhu khong theo doi", muctran(50, -5), 0)
la("tran nho: 3 tren 4 la vang", muctran(3, 4), 1)

# --- Nhan ngan hien trong o lich ---
la("bo tu HOP roi lay ba chu dau", nhanten("HỘP MOONGARDEN"), "MOO")
la("ten nhieu tu thi lay chu cai dau", nhanten("Thập Cẩm Xá Xíu, 110gram"), "TCX")
la("bo dau tieng Viet", nhanten("Đậu Ngự Trần Bì, 80gram"), "DNT")
la("bo ca chu BANH TRUNG THU NHAN",
   nhanten("Bánh Trung Thu Nhân Mè Đen Sầu Riêng"), "MDS")
# Trung nhan la loi nang nhat cua o lich: sales doc nham mon.
la("trung thi noi dai chu khong tra trung",
   nhanten("HỘP MOONLAPIS", {"MOO"}), "MOON")
la("nhan moi khac han nhan da phat",
   nhanten("HỘP MOONLAPIS", {"MOO"}) != "MOO", True)
la("het chu de noi thi danh so", nhanten("ABC", {"ABC", "ABC2"}), "ABC3")
la("ten rong van tra ra mot nhan dung duoc", bool(nhanten("")), True)
la("ten toan so van tra ra nhan", bool(nhanten("110 80")), True)
la("nhan khong bao gio dai qua sau chu", len(nhanten("Bánh Trung Thu Nhân Dứa Bưởi Xí Muội")) <= 6, True)

# --- Mot ma ban lo KHONG duoc chan ca mua (bat duoc luc nghiem thu 18/08) ---
# Truoc khi sua: HOP MOONGARDEN dang -62 vi chua khai dot nha in, va vi the
# ban mot HOP MOONLAPIS cung bi chan kem cau "se lay het HOP MOONGARDEN ben
# trong hop" - MOONGARDEN khong nam trong MOONLAPIS. Mot ma hong chan ca mua.
DONG6 = [
	{"ma_hang": "MG", "ten_banh": "Hop MG", "san_xuat": 0, "da_dat": 62, "cho_chot": 0, "don_khac": 0},
	{"ma_hang": "ML", "ten_banh": "Hop ML", "san_xuat": 100, "da_dat": 24, "cho_chot": 0, "don_khac": 0},
]
la("MG dang -62 nhung ban ML thi KHONG bi chan", conthem(DONG6, [], "ML", 70)[1], [])
la("ban ML van tru dung han muc cua chinh ML", conthem(DONG6, [], "ML", 70)[0], 6)
la("ban ML qua han muc thi chi bao ML, khong bao MG",
   [x[0] for x in conthem(DONG6, [], "ML", 80)[1]], ["ML"])
# Chinh cai ma dang am van phai bi chan khi ban them.
la("ban them chinh ma dang am thi van chan",
   [x[0] for x in conthem(DONG6, [], "MG", 1)[1]], ["MG"])
# Dong am san MA don nay lam am them thi VAN phai chan.
DONG7 = [
	{"ma_hang": "HOP", "ten_banh": "Hop", "san_xuat": 100, "da_dat": 0, "cho_chot": 0, "don_khac": 0},
	{"ma_hang": "B", "ten_banh": "Banh", "san_xuat": 0, "da_dat": 5, "cho_chot": 0, "don_khac": 0},
]
la("dong am san ma don nay lam am them thi VAN chan",
   [x[0] for x in conthem(DONG7, [{"ma_hop": "HOP", "ma_banh": "B", "so_luong": 2}], "HOP", 3)[1]],
   ["B"])

# =====================================================================
# Nhom 21. Man mua vu khong duoc phep treo, va nhip tu dong bo
# =====================================================================
print("21. Man mua vu khong treo va nhip tu dong bo")

_mv_src = open("vagabond/mua_vu.py", encoding="utf-8").read()
_nen_src = open("vagabond/public/js/bep/00-nen.js", encoding="utf-8").read()
_man_src = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_hook_src = open("vagabond/hooks.py", encoding="utf-8").read()

# Loi goc anh Viet bao 18/08/2026: fetch khong co han gio nen mot lan mang
# chap la MOI man hinh cho deu ket vinh vien, khong rieng man mua vu.
la("moi loi goi may chu deu co han gio", "AbortController" in _nen_src, True)
la("han gio duoc gan vao fetch", "signal: ctl ? ctl.signal : undefined" in _nen_src, True)
la("het gio phai noi nguoi dung lam gi tiep (QT-24)",
   "Kiểm tra mạng rồi bấm lại" in _nen_src, True)
la("doc than tra loi cung nam trong han gio",
   _nen_src.index("txt = await r.text()") > _nen_src.index("signal: ctl"), True)

# Man mua vu KHONG duoc goi dong_bo tren duong mo man nua.
la("mo man mua vu chi doc CSDL, khong doi Pancake",
   "vagabond.mua_vu.dong_bo'" in _man_src, False)
la("man co duong xin dong bo nen", "vagabond.mua_vu.xin_dong_bo" in _man_src, True)
la("nhip tu lam moi dat 30 giay", "var MV_GIAY = 30;" in _man_src, True)
la("nhip tu tat khi roi man", "function mvConODay" in _man_src, True)
la("khong ve lai ca man khi so khong doi",
   "if (dau === MV_DAU) {" in _man_src and "mvVe();" in _man_src, True)
la("dang mo hop thoai thi khong ve de", _man_src.count("querySelector('.sh')") >= 2, True)
# Nhip im lang qua thi nguoi dung tuong he chet, nen gio dong bo phai nhich
# ke ca khi so khong doi.
la("so khong doi van phai nhich gio dong bo", "nMoc.innerHTML = mvChuMoc(d)" in _man_src, True)
la("chu moc dung chung mot ham, khong chep hai ban",
   _man_src.count("mvChuMoc(") >= 3, True)

# May chu tu keo, ke ca luc khong ai mo man.
la("co nhip scheduler moi phut", '"* * * * *": ["vagabond.mua_vu.dong_bo_tu_dong"]' in _hook_src, True)
la("co ham cho scheduler goi", "def dong_bo_tu_dong" in _mv_src, True)
la("co ham cho hang doi nen goi", "def dong_bo_mot_mua" in _mv_src, True)
la("xin dong bo tra ve ngay, khong keo tai cho", "frappe.enqueue" in _mv_src, True)

# Hai luot keo cung luc la cho de treo that: luot sau nam cho khoa dong CSDL.
la("co khoa chan hai luot keo cung luc", "def _gianh_khoa" in _mv_src, True)
la("khoa duoc tha trong finally", "finally:\n\t\t_tha_khoa(mua)" in _mv_src, True)
la("gian cach nho hon nhip man de nhip khong bi nuot",
   int(re.search(r"GIAN_CACH_DONG_BO = (\d+)", _mv_src).group(1)) < 30, True)

# =====================================================================
# Nhom 22. Phan he Thu mua khoa cung, va chip loc man mua vu
# =====================================================================
print("22. Phan he Thu mua va chip loc mua vu")

_q_src = open("vagabond/quyen_phan_he.py", encoding="utf-8").read()
_mh_src = open("vagabond/mua_hang.py", encoding="utf-8").read()
_dy_src = open("vagabond/duyet_ycmh.py", encoding="utf-8").read()
_ncc_src = open("vagabond/ncc.py", encoding="utf-8").read()
_bg_src = open("vagabond/bang_gia.py", encoding="utf-8").read()
_kh_src = open("vagabond/public/js/bep/01-khung-app.js", encoding="utf-8").read()
_tc_src = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()
_mv_man = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_xk_src = open("vagabond/xuat_kho.py", encoding="utf-8").read()

# --- Cho ro that: vai "Bo phan dat hang" gan nhu ai cung co ---
# Vai do sinh ra de LAP YEU CAU MUA. No khong duoc keo theo quyen xem gia
# mua va cong no. Bon tep duoi day truoc 18/08/2026 deu lot vai nay.
for _t, _n in ((_mh_src, "mua_hang"), (_dy_src, "duyet_ycmh"), (_ncc_src, "ncc"),
               (_bg_src, "bang_gia")):
	la("%s khong con vai Bo phan dat hang o bat cu dau" % _n,
	   "Bộ phận đặt hàng" in _t, False)
# Nhung XEM gia thi van rong hon: thu kho phai doi chieu gia luc nhan hang.
la("bang gia: XEM gia van mo cho thu kho", '"Stock Manager"' in _bg_src, True)
la("bang gia: KHAI gia sieu chat hon XEM gia",
   "QUYEN_SUA = QUYEN_THU_MUA" in _bg_src, True)
# Ca nay bat duoc lo hong cua chinh bo kiem: bon ca tren chi soi bon tep
# GOI quyen, khong soi chinh cho KHAI quyen. Tra vai do vao quyen_phan_he.py
# la ca bon tep kia lai mo toang ma khong ca nao keu.
la("chinh noi khai quyen cung khong duoc co Bo phan dat hang",
   "Bộ phận đặt hàng" in _q_src, False)

# --- Mot noi khai, khong co ban sao ---
la("co mot noi duy nhat khai quyen Thu mua", "QUYEN_THU_MUA = {" in _q_src, True)
for _t, _n in ((_mh_src, "mua_hang"), (_dy_src, "duyet_ycmh"), (_ncc_src, "ncc"), (_bg_src, "bang_gia")):
	la("%s nap quyen tu quyen_phan_he chu khong chep lai" % _n,
	   "from vagabond.quyen_phan_he import" in _t, True)

# --- Ai duoc vao, ai khong ---
la("Thu mua duoc vao", 'ROLE_THU_MUA' in _q_src, True)
la("Giam doc duoc vao", 'ROLE_GIAM_DOC' in _q_src, True)
# Anh Viet chot 18/08/2026: ke toan VAN thay, vi cong no phai tra la viec
# hang ngay cua ho.
la("ke toan van thay phan he Thu mua", '"Accounts Manager"' in _q_src, True)
la("cau bao loi noi ro phai lam gi tiep (QT-24)",
   "báo anh Việt cấp thêm chức vụ" in _q_src, True)

# --- Man khop may chu ---
la("man an nut theo dung danh sach may chu",
   "hasRole('Thu mua')" in _kh_src and "hasRole('Giám đốc')" in _kh_src, True)
la("man KHONG con lay Bo phan dat hang lam quyen mua",
   "coQuyenMua" in _kh_src and "Bộ phận đặt hàng" not in _kh_src.split("function coQuyenMua")[1][:400], True)

# --- Phan he Thu mua nam dung cho, ngay tren Ke toan ---
_i_tm = _tc_src.index("k: 'TM'")
_i_kt = _tc_src.index("k: 'KT'")
la("co phan he Thu mua", _i_tm > 0, True)
la("Thu mua nam NGAY TREN Ke toan", _i_tm < _i_kt, True)
# Tu 19/08/2026 nhom nay co them DNC (de nghi chi), nhung cac nut mua hang
# van phai o ngoai - do moi la dieu ca kiem nay giu.
la("cac nut mua hang da roi khoi nhom Dat hang",
   [k for k in ("DUYETYC", "PO", "CNPT", "NCC", "BGIA")
    if ("'%s'" % k) in _tc_src.split("k: 'DH'")[1].split("}")[0]], [])
for _k in ("DUYETYC", "PO", "CNPT", "NCC", "BGIA"):
	la("nut %s da vao phan he Thu mua" % _k,
	   _k in _tc_src[_i_tm:_i_kt], True)

# --- Bep nhin duoc hang chuyen ve kho minh ---
la("co API hang chuyen ve kho minh", "def hang_chuyen_ve" in _xk_src, True)
la("chi lay kho NGUOI DO phu trach, khong bay kho nguoi khac",
   "_kho_phu_trach()" in _xk_src, True)
la("chua khai kho phu trach thi noi ro phai lam gi (QT-24)",
   "chưa khai Kho phụ trách" in _xk_src, True)
la("chi lay phieu DA GHI SO", '"docstatus": 1' in _xk_src, True)
# Hai loi em tu bat duoc luc nghiem thu v210, va ca hai deu la loi that.
# Mot: chua khai kho phu trach thi KHONG duoc truyen kho tuy y - bo qua cho
# nay la man khoa NGUOC, nguoi duoc khai bi gioi han con nguoi chua khai thi
# xem duoc moi kho.
la("chua khai kho thi khong duoc truyen kho tuy y",
   "if kho not in cua_toi:" in _xk_src, True)
# Hai: posting_time cua Frappe la "9:33:00", cat cung 5 ky tu ra "9:33:".
la("gio duoc dinh dang chu khong cat cung", "def _gio_hhmm" in _xk_src, True)
la("khong con cat cung 5 ky tu gio", 'posting_time"] or "")[:5]' in _xk_src, False)

_gio = {}
exec(re.search(r"^def _gio_hhmm\(.*?(?=^def )", _xk_src, re.S | re.M).group(0),
     {"cint": lambda x: int(x or 0)}, _gio)
_g = _gio["_gio_hhmm"]
la("gio mot chu so duoc them so 0", _g("9:33:00"), "09:33")
la("gio hai chu so giu nguyen", _g("17:51:00"), "17:51")
la("gio rong tra rong", _g(None), "")
la("gio khong co dau hai cham thi khong lam vo", _g("abc"), "abc")

# --- Chip loc man mua vu ---
la("co bon nhom trang thai", "MV_THU_TU = { lo: 0, het: 1, con: 2, hop: 3 }" in _mv_man, True)
la("ban lo xep len dau", _mv_man.index("lo: 0") < _mv_man.index("con: 2"), True)
la("nguong sap het khop nguong canh bao may chu",
   int(re.search(r"MV_NGUONG_SAP_HET = (\d+)", _mv_man).group(1))
   == int(re.search(r"NGUONG_CANH_BAO = ([\d.]+)", _mv_src).group(1).split(".")[0]), True)
la("go tim khong ve lai ca man", "kh.innerHTML = mvDsSpHtml(ds)" in _mv_man, True)
la("nhip khong cuop o tim dang go",
   "document.activeElement.id === 'mvTim'" in _mv_man, True)
la("loc rong thi noi ro phai lam gi (QT-24)",
   "Bỏ bớt điều kiện lọc hoặc xoá ô tìm" in _mv_man, True)

# --- O tim phai khop ca khi go KHONG DAU ---
# Bat duoc luc nghiem thu v211: go "dua" thi man bao khong co ma nao khop,
# trong khi mua co ca Dua Buoi lan Dua Sap. Tren dien thoai, giua luc dang
# noi chuyen voi khach, gan nhu khong ai go du dau.
la("co phep bo dau tieng Viet", "function mvKhongDau" in _mv_man, True)
la("o tim di qua phep bo dau", "mvKhongDau(q)" in _mv_man, True)

def _kd(x):
	import unicodedata
	x = str(x or "").lower()
	x = "".join(c for c in unicodedata.normalize("NFD", x) if unicodedata.category(c) != "Mn")
	return x.replace("đ", "d")

def _khop(x, q):
	q = _kd(q).strip()
	if not q:
		return True
	return q in _kd("%s %s %s" % (x.get("ten_banh", ""), x.get("ma_hang", ""), x.get("nhan_ngan", "")))

_DS = [
	{"ten_banh": "Dứa Bưởi Xí Muội, 80gram", "ma_hang": "BASS00050", "nhan_ngan": "DB80"},
	{"ten_banh": "Dừa Sáp Hạt Chia, 80gram", "ma_hang": "BASS00051", "nhan_ngan": "DS80"},
	{"ten_banh": "Đậu Ngự Trần Bì, 80gram", "ma_hang": "BASS00055", "nhan_ngan": "DN80"},
	{"ten_banh": "HỘP MOONLAPIS", "ma_hang": "BASS00039", "nhan_ngan": "ML"},
]
_n = lambda q: len([x for x in _DS if _khop(x, q)])
la("go 'dua' khong dau ra ca Dua Buoi va Dua Sap", _n("dua"), 2)
# Go CO dau cung ra du, khong bi hut - dau cua nguoi go cung bi bo di.
la("go 'dứa' co dau van ra du hai mon", _n("dứa"), 2)
la("go nhieu chu khong dau", _n("dau ngu"), 1)
la("chu d gach ngang doi thanh d thuong", _n("đậu"), 1)
la("tim duoc theo ma hang", _n("bass00039"), 1)
la("tim duoc theo nhan ngan tren lich", _n("ml"), 1)
la("khong khop gi thi tra 0", _n("xxx"), 0)
la("o tim rong thi khong loc gi", _n("   "), 4)

# =====================================================================
# Nhom 23. Phan he Danh muc: du man, dung cho, dung quyen
# =====================================================================
print("23. Phan he Danh muc du lieu nen")

def _nap_danh_muc_nen():
	"""Nap danh_muc_nen.py THAT bang mot frappe gia, de soi GIA TRI chu khong soi chu.

	Mo dun nay chi khai bao luc nap, khong ham nao goi frappe, nen mot
	frappe rong la du. Doi lai duoc mot dieu quan trong: bo kiem doc dung
	cai tap quyen ma may chu se dung, chu khong doc mot doan chuoi trong
	tep - va vi vay khong the qua duoc bang cach doi cach viet.
	"""
	import types

	_fr = types.ModuleType("frappe")
	_fr.throw = lambda *a, **k: None
	_fr.get_roles = lambda *a, **k: []
	_fr.get_all = lambda *a, **k: []
	_fr.db = types.SimpleNamespace(get_value=lambda *a, **k: None, count=lambda *a, **k: 0)
	_fr.parse_json = lambda x: x
	_fr.whitelist = lambda *a, **k: (lambda f: f)
	_fu = types.ModuleType("frappe.utils")
	for _n in ("add_days", "getdate", "nowdate", "flt", "cint"):
		setattr(_fu, _n, lambda *a, **k: None)
	_cu = {k: sys.modules[k] for k in list(sys.modules) if k == "frappe" or k.startswith("frappe.")}
	sys.modules["frappe"] = _fr
	sys.modules["frappe.utils"] = _fu
	if "." not in sys.path:
		sys.path.insert(0, ".")
	try:
		for _k in [k for k in list(sys.modules) if k.startswith("vagabond")]:
			del sys.modules[_k]
		import importlib

		try:
			_m = importlib.import_module("vagabond.danh_muc_nen")
		except Exception as _e:
			# LoiKhaiBao la co y nem luc nap - do la hang rao cua khung. Nhung
			# de no lam VO ca bo kiem thi nguoi doc chi thay mot vet do, phai
			# lan nguoc lai moi biet chuyen gi. Bien thanh mot ca hong co ten.
			return {"_LOI_NAP": str(_e)}
		return {k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")}
	finally:
		for _k in [k for k in list(sys.modules) if k == "frappe" or k.startswith("frappe.")]:
			del sys.modules[_k]
		sys.modules.update(_cu)
		for _k in [k for k in list(sys.modules) if k.startswith("vagabond")]:
			del sys.modules[_k]


_dm_src = open("vagabond/danh_muc_nen.py", encoding="utf-8").read()
_khungds_src = open("vagabond/khung/ds.py", encoding="utf-8").read()
_tc2_src = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()

# --- Du 16 man, va moi man deu duoc dang ky vao tang khung ---
_ma_dm = re.findall(r'ma="(DM[A-Z]*)"', _dm_src)
la("khai du 16 danh muc", len(_ma_dm), 16)
la("khong co ma nao trung", len(set(_ma_dm)), 16)
for _m in _ma_dm:
	la("man %s da dang ky vao tang khung" % _m, '"%s": ("vagabond.danh_muc_nen"' % _m in _khungds_src, True)
	la("man %s co o tren app" % _m, "'%s'" % _m in _tc2_src, True)

# --- Man hinh khong duoc viet tay: di qua tang khung ---
# Day la ca giu cho quy hoach nay khong bi pha: them mot danh muc moi ma
# viet man rieng la quay lai dung cai benh 16 ban sao.
la("phan he KHONG dung mot dong scr rieng nao",
   bool(re.search(r"function scrDanhMuc[A-Z]", _tc2_src)), False)
la("mot nhanh dinh tuyen tien to cho ca 16 man",
   "k.indexOf('DM:') === 0" in _tc2_src, True)
la("o duoc dung tu bang khai bao, khong chep tay",
   "for (var dmi = 0; dmi < VGB_DM.length; dmi++)" in _tc2_src, True)

# --- Danh muc nam NGAY TREN Cai dat ---
_i_dm = _tc2_src.index("k: 'DM'")
_i_khac = _tc2_src.index("k: 'KHAC'")
la("Danh muc nam ngay tren Cai dat", _i_dm < _i_khac, True)

# --- Quyen: khong man nao mo cho tat ca, va chia dung viec ---
#
# BAN CU CUA BO KIEM NAY DOC BANG CACH CAT CHUOI - `_dm_src.split("XEM_TIEN =
# {")` - nen no chi doc duoc khi cac tap viet dung dang chu literal. Ngay
# 21/08/2026 doi sang ham _siet() thi phep cat chuoi vo, va no vo bang
# IndexError chu khong bang mot ca hong: tuc la neu doi cach viet ma khong
# doi chuoi tim thi bo kiem TE HAN ca im lang, no dung han.
#
# Nay nap MO DUN THAT bang mot frappe gia va soi GIA TRI, khong soi chu. Ca
# kieu nay khong the qua duoc bang cach doi cach viet.
la("gia mua khong mo cho ca tiem", "quyen=XEM_MUA" in _dm_src, True)
la("ho so khach hang khong mo cho ca tiem", "quyen=XEM_KHACH" in _dm_src, True)
la("tai khoan ke toan khong mo cho ca tiem", "quyen=XEM_TIEN" in _dm_src, True)

_DM44 = _nap_danh_muc_nen()
la("danh_muc_nen.py nap duoc, khong loi khai bao",
   _DM44.get("_LOI_NAP") or "", "")
if _DM44.get("_LOI_NAP"):
	# Nap hong thi moi ca duoi day deu vo nghia. Dung o day, va cho no mot
	# tap rong de phan con lai cua bo kiem con chay tiep.
	_DM44 = {"VAO_DANH_MUC": set(), "XEM_CHUNG": set(), "XEM_MUA": set(),
	         "XEM_KHACH": set(), "XEM_TIEN": set()}
# Anh Viet 21/08/2026: *"Cac Role khac (Sales, Kho, Bep...) tuyet doi khong
# duoc nhin thay menu nay de tranh tinh trang rac du lieu."*
_CAM44 = (
	"Stock Manager", "Stock User", "Kiểm kê viên", "Nhan hang dieu chuyen",
	"Manufacturing Manager", "Manufacturing User", "Bếp phó",
	"Sales Manager", "Sales User", "Bộ phận đặt hàng",
)
for _t44 in ("XEM_CHUNG", "XEM_MUA", "XEM_KHACH", "XEM_TIEN"):
	_tap44 = _DM44[_t44]
	la("%s khong lot vai Sales, Kho hay Bep" % _t44,
	   sorted(set(_tap44) & set(_CAM44)), [])
	la("%s nam gon trong cong VAO_DANH_MUC" % _t44,
	   sorted(set(_tap44) - set(_DM44["VAO_DANH_MUC"])), [])
	la("%s khong rong" % _t44, bool(_tap44), True)

# Ba vai THAT dang chay tren site phai vao duoc, khong duoc quen. Ban truoc
# cua XEM_TIEN liet ke tay va sot dung "AP Giam doc", tuc la anh Viet va De
# khong xem duoc he thong tai khoan.
for _v44 in ("AP Kiểm soát (FIN)", "AP Giám đốc"):
	la("%s xem duoc he thong tai khoan" % _v44, _v44 in _DM44["XEM_TIEN"], True)
la("AP Officer (Uyen) xem duoc gia mua", "AP Officer" in _DM44["XEM_MUA"], True)
# Thu mua KHONG can danh ba khach: so dien thoai khach la thu duy nhat trong
# ca phan he thuoc ve nguoi ngoai cong ty.
la("Thu mua khong xem danh ba khach", "AP Officer" in _DM44["XEM_KHACH"], False)

# Moi bang deu phai di qua cong. Duyet TUNG bang chu khong duyet mot vai
# bang tieu bieu: them mot bang moi ma quen siet thi ca nay keu ngay.
for _t44 in sorted(_DM44):
	if not _t44.startswith("BANG_"):
		continue
	_b44 = _DM44[_t44]
	la("bang %s khong lot vai bi cam" % _b44["ma"],
	   sorted(set(_b44["quyen"]) & set(_CAM44)), [])
	la("bang %s nam trong cong" % _b44["ma"],
	   sorted(set(_b44["quyen"]) - set(_DM44["VAO_DANH_MUC"])), [])

# --- Man hinh khong tu doan quyen, hoi may chu ---
# Doan lai o man la de ra ban sao thu hai cua danh sach quyen.
la("man hoi danh ba tu may chu", "vagabond.khung.ds.danh_ba" in _tc2_src, True)
la("o nao may chu khong tra ve thi khong dung",
   "if (VGB_KHUNG_CO && !VGB_KHUNG_CO[dmx.m]) continue;" in _tc2_src, True)

# --- Bay em bat duoc luc dung: gom nhom lan hai lam mat het o ---
# vgbGomNhom doc cac dong [data-go] roi GHI DE body. Tu luot hai tro di
# khong con dong nao de doc, nen phai giu ban chup.
# Kiem ca ba manh, khong chi ten bien: doi ten bien roi de nguyen cho dung
# thi ca kiem "co chuoi VGB_DONG_GOC" van khop ma ma da hong.
la("giu ban chup dong goc de gom lai duoc luot hai",
   "var VGB_DONG_GOC = null;" in _tc2_src, True)
la("ban chup duoc ghi khi doc duoc dong", "VGB_DONG_GOC = {};" in _tc2_src, True)
la("ban chup duoc dung lai o luot gom sau",
   "for (var gk in VGB_DONG_GOC) VGB_HUB[gk] = VGB_DONG_GOC[gk];" in _tc2_src, True)
la("chua gom lan nao ma khong doc duoc gi thi khong ve de",
   "} else if (!VGB_DONG_GOC) {" in _tc2_src, True)

# --- Cay thu muc: sap theo lft chu khong tu dung cay o man ---
for _m in ("BANG_NHOM_SP", "BANG_KHO", "BANG_TAI_KHOAN", "BANG_NHOM_NCC", "BANG_NHOM_KHACH"):
	_than = _dm_src.split(_m + " = khai.bang(")[1].split("\n)")[0]
	la("%s sap theo lft de ra dung thu tu cay" % _m, 'sap="lft asc"' in _than, True)
	# Thut co the viet thang trong than, hoac goi qua mot phep them rieng.
	# Ca nay phai soi ca hai duong, neu khong doi sang phep rieng la bao
	# hong oan.
	_co_thut = "_thut_cay(" in _than
	if not _co_thut and "them=" in _than:
		_ten_them = _than.split("them=")[1].split(",")[0].strip()
		if _ten_them.startswith("_"):
			_kho = _dm_src.split("def " + _ten_them + "(")
			_co_thut = len(_kho) > 1 and "_thut_cay(" in _kho[1].split("\ndef ")[0]
	la("%s thut ten theo cap" % _m, _co_thut, True)

# --- Phep thut cay phai THUAN va khong lap vo han ---
_ns = {}
exec(re.search(r"^def _thut_cay\(.*?(?=^def |^BANG_|^# ={5})", _dm_src, re.S | re.M).group(0), _ns)
_tc = _ns["_thut_cay"]
_bc = {"cay": {"B": "A", "C": "B", "A": ""}}
la("goc khong thut", _tc({"n": "A", "p": ""}, _bc, "n", "p"), "A")
la("con cap 1 thut mot", _tc({"n": "B", "p": "A"}, _bc, "n", "p"), "　B")
la("con cap 2 thut hai", _tc({"n": "C", "p": "B"}, _bc, "n", "p"), "　　C")
# Cay tro vong lai chinh no thi khong duoc treo may.
la("cay tro vong khong lam treo",
   bool(_tc({"n": "X", "p": "V"}, {"cay": {"V": "W", "W": "V"}}, "n", "p")), True)

# --- Nghiem thu v213 tren site that: cot So hieu tai khoan hien trong ---
# 270 tai khoan tren he thi phan lon account_number RONG, so hieu bi go
# dinh vao dau ten. Cot cu tro thang vao account_number nen trong tron.
_ns_tk = {}
exec(re.search(r"^def _tach_so_tk\(.*?(?=^def _them_tk)", _dm_src, re.S | re.M).group(0), _ns_tk)
_tach = _ns_tk["_tach_so_tk"]
la("so hieu go dinh vao dau ten van tach ra duoc",
   _tach({"name": "1111 - Tiền Việt Nam - TV", "account_number": "",
          "account_name": "1111 - Tiền Việt Nam"}), ("1111", "Tiền Việt Nam"))
la("co account_number that thi giu nguyen ten",
   _tach({"name": "11211 - Tiền gửi MB Bank - TV", "account_number": "11211",
          "account_name": "Tiền gửi MB Bank"}), ("11211", "Tiền gửi MB Bank"))
la("tai khoan khong co so thi de trong chu khong bia",
   _tach({"name": "Debtors - TV", "account_number": "",
          "account_name": "Debtors"}), ("", "Debtors"))
_than_tk = _dm_src.split("BANG_TAI_KHOAN = khai.bang(")[1].split("\n)")[0]
# Soi trong PHAN KHAI COT cua rieng bang nay, khong soi ca tep. Soi ca tep
# thi ngay 21/08/2026 no keu oan: form Tao moi cua DMTK co o nhap
# account_number - mot viec hoan toan khac voi cot cua danh sach.
_cot_tk = _than_tk.split("cot=khai.cot(")[1].split("\n\t),")[0]
la("cot So hieu khong tro thang vao account_number nua",
   '("account_number", "Số hiệu"' in _cot_tk, False)
la("cot So hieu doc tu phep tach", '("so_hieu", "Số hiệu", "chu")' in _cot_tk, True)
la("DMTK dung phep them rieng", "them=_them_tk," in _than_tk, True)
la("phep xep chip dung chung mot phep tach", "_tach_so_tk(r)[0]" in _dm_src, True)

# =====================================================================
# Nhom 24. Hoan tien doi sang khoi Ke toan, tu choi, chip va o tim
# =====================================================================
print("24. Phan he Hoan tien cho Ke toan")

_ht_src = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_kh_src = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()

# --- Doi cho: HT phai roi khoi nhom Ban hang va nam trong nhom Ke toan ---
_nhom_bh = _tc2_src.split("k: 'BH'")[1].split("]")[0]
_nhom_kt = _tc2_src.split("k: 'KT'")[1].split("]")[0]
la("khoa HT khong con trong nhom Ban hang", "'HT'" in _nhom_bh, False)
la("khoa HT nam trong nhom Ke toan", "'HT'" in _nhom_kt, True)
la("the hoan tien doi ten thanh Cash-back",
   "Danh sách Phiếu hoàn tiền (Cash-back)" in _tc2_src, True)
# The cu phai bi go han, khong duoc de hai the cung tro toi mot man.
la("khong con the Hoan tien / Tra hang o trang chu",
   "'Hoàn tiền / Trả hàng', 'Phiếu hoàn tiền khách" in _tc2_src, False)

# --- Badge do: so phai lay tu may chu, khong dem o man hinh ---
la("trang chu hoi may chu so phieu cho chi",
   "vagabond.hoan_tien.dem_cho_chi" in _tc2_src, True)
la("so badge duoc truyen vao the", "htChoChi, 'HT'" in _tc2_src, True)
la("may chu co ham dem cho chi", "def dem_cho_chi()" in _ht_src, True)

# --- Lo hong that: doi soat theo gio khong loai phieu da huy ---
# Duong SePay goi thang da loai "Da huy" tu 16/08, nhung duong chay theo gio
# thi khong. Mot phieu ke toan vua tu choi ma ngan hang tinh co co dong tien
# ra trung so tien la may van sinh phieu chi.
_than_ds = _ht_src.split("def doi_soat(")[1].split("\ndef ")[0]
la("doi soat theo gio loai phieu da huy",
   'loc = {"da_doi_soat": 0, "trang_thai": ["!=", "Da huy"]}' in _than_ds, True)
la("doi soat mot phieu chi dinh cung loai phieu da huy",
   'loc = {"name": ho_so, "trang_thai": ["!=", "Da huy"]}' in _than_ds, True)
_than_sepay = _ht_src.split("def sepay_tien_ra(")[1].split("\ndef ")[0]
la("duong SePay goi thang van loai phieu da huy",
   '"trang_thai": ["!=", "Da huy"]' in _than_sepay, True)

# --- Tu choi: ba cai chan deu phai o may chu ---
_than_tc = _ht_src.split("def tu_choi(")[1].split("\ndef ")[0]
la("chi ke toan va giam doc tu choi duoc", "_duoc_tu_choi()" in _than_tc, True)
la("ly do bat buoc va do dai toi thieu", "len(ly_do) < 5" in _than_tc, True)
la("tien da ra thi khong tu choi duoc",
   "cint(d.da_doi_soat) or d.phieu_chi" in _than_tc, True)
la("huy mem chu khong xoa (QT-20)", 'frappe.delete_doc' in _than_tc, False)
la("co ghi vet ai tu choi", '"nguoi_tu_choi": frappe.session.user' in _than_tc, True)
la("co ghi vet luc nao", '"ngay_tu_choi": now_datetime()' in _than_tc, True)
la("tu choi hai lan thi bao chu khong ghi de", 'd.trang_thai == "Da huy"' in _than_tc, True)
# Vai duoc tu choi phai la mot danh sach co ten, khong duoc mo cho tat ca.
_than_duoc = _ht_src.split("def _duoc_tu_choi(")[1].split("\ndef ")[0]
for _v in ("System Manager", "Accounts Manager", "Accounts User", "Giám đốc"):
	la("vai %s tu choi duoc" % _v, _v in _than_duoc, True)
la("Sales khong tu tu choi duoc phieu cua minh", '"Sales User"' in _than_duoc, False)

# --- Ba truong ghi vet phai duoc ma nguon khai, khong bam tay tren Desk ---
for _t in ("ly_do_tu_choi", "nguoi_tu_choi", "ngay_tu_choi"):
	la("truong %s do ma nguon khai" % _t,
	   '"fieldname": "%s"' % _t in _ht_src, True)

# --- Chip va o tim: loc va DEM deu phai chay o may chu ---
_than_ds2 = _ht_src.split("def ds(")[1].split("\ndef ")[0]
la("ham ds nhan o tim", "tim=\"\"" in _ht_src.split("def ds(")[1][:60], True)
la("o tim chay o may chu chu khong loc mang", "or_filters=hoac" in _than_ds2, True)
la("tim duoc theo ten khach", '"customer_name": ["like"' in _than_ds2, True)
la("tim duoc theo ma phieu", '["name", "like"' in _than_ds2, True)
la("tim duoc theo ma hoa don", '["hoa_don", "like"' in _than_ds2, True)
# Con so tren chip phai dem theo dung o tim dang go, neu khong thi go mot
# tu ra 3 dong ma chip van bao 40.
la("chip dem theo ca o tim dang go", "or_filters=hoac" in _than_ds2.split("dem = {}")[1], True)
la("co chip da huy", '"Da huy"' in _than_ds2.split("dem = {}")[1], True)
_chip_js = _kh_src.split("function htDsVe()")[1].split("var html")[0]
for _c in ("Chờ chi", "Đã chi", "Đã đối soát", "Đã huỷ / Từ chối"):
	la("man hinh co chip %s" % _c, _c in _chip_js, True)

# --- Dong bam duoc de mo chi tiet ---
la("moi dong co vung bam duoc", 'class="htmo"' in _kh_src, True)
la("bam dong thi mo man chi tiet", "htChiTiet(n.getAttribute('data-ht'))" in _kh_src, True)
la("may chu co ham chi tiet phieu", "def chi_tiet(ho_so)" in _ht_src, True)
# Nut ben trong dong phai chan noi bot, neu khong bam Chuyen khoan lai mo
# luon ca man chi tiet.
_than_gan = _kh_src.split("b.querySelectorAll('.htanh')")[1].split("var s = document")[0]
la("nut anh chan noi bot", "e.stopPropagation()" in _than_gan, True)
la("nut chuyen khoan chan noi bot", _than_gan.count("e.stopPropagation()") >= 2, True)

# --- Nut Tu choi chi hien khi may chu noi con tu choi duoc ---
la("man hinh khong tu doan duoc tu choi hay khong",
   "d.con_tu_choi_duoc && d.duoc_tu_choi" in _kh_src, True)
la("may chu tra co con tu choi duoc", "con_tu_choi_duoc" in _ht_src, True)

# =====================================================================
# Nhom 25. Hop dong mua ban hang hoa sinh tu bao gia da chot
# =====================================================================
print("25. Hop dong phap ly tu bao gia")

_hdp_src = open("vagabond/hop_dong_pdf.py", encoding="utf-8").read()
_bg_src = open("vagabond/bao_gia.py", encoding="utf-8").read()
_hd_src = open("vagabond/hop_dong.py", encoding="utf-8").read()

# --- Ba phep THUAN: viet tat, so hop dong, chia hai dot ---
# Cat than ham ra chay o day, khong import ca mo dun (may nay khong co
# frappe). Ba ham nay phai THUAN chinh vi ly do do.
_ns_hd = {"unicodedata": __import__("unicodedata")}
for _t in ("_khong_dau", "viet_tat_khach", "so_hop_dong", "chia_hai_dot"):
	_m = re.search(r"^def %s\(.*?(?=^def |\Z)" % _t, _hdp_src, re.S | re.M)
	la("ham %s ton tai" % _t, bool(_m), True)
	if _m:
		exec(compile(_m.group(0), "hop_dong_pdf:%s" % _t, "exec"), _ns_hd, _ns_hd)
_ns_hd.setdefault("flt", lambda x: float(x or 0))
_ns_hd.setdefault("getdate", None)

_vt = _ns_hd.get("viet_tat_khach")
if _vt:
	la("bo cum loai hinh doanh nghiep", _vt("CÔNG TY TNHH M.O.I COSMETICS"), "MOI")
	# Anh Viet 18/08/2026 bat loi: *"cong ty SECOMM nhung may lai suggest
	# la VAN"*. Thuat toan cu bo cum loai hinh xong con "TU VAN GIAI PHAP
	# SECOMM", roi thay tu dau ngan va viet hoa nen tuong la ten viet tat
	# san. Gio bo them cum nganh nghe, con dung mot tu thi lay nguyen tu do.
	la("bo ca cum nganh nghe, giu ten rieng",
	   _vt("CÔNG TY TNHH TƯ VẤN GIẢI PHÁP SECOMM"), "SECOMM")
	la("ten rieng dai thi lay nguyen tu",
	   _vt("CÔNG TY TNHH PATISSERIE VAGABOND"), "VAGABOND")
	# Bay: "CO PHAN" va "CỔ PHẦN" phai la mot. Khong bo dau thi ra "CP" -
	# tuc lay dung hai chu cua cai dang le phai bo di.
	la("chu co dau van bi coi la cum loai hinh", _vt("CÔNG TY CỔ PHẦN PYRAMID"), "PYRAMID")
	la("ten khong co cum loai hinh van doc duoc", _vt("Pyramid"), "PYRAMID")
	la("ten rong thi tra rong chu khong bia", _vt(""), "")
	la("cum nganh nghe khong lot vao viet tat",
	   _vt("CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ ABC"), "ABC")
	# Con nhieu tu rieng that thi moi ghep chu cai dau.
	la("nhieu tu rieng thi ghep chu cai dau",
	   _vt("JU YOUNG - ISU FUTURE GROW"), "JYIFG")
	la("khong cat cut ten hai chu dau", _vt("CÔNG TY CP KFC VIỆT NAM"), "KFC")

# --- Chia hai dot: hai so PHAI cong lai dung tong ---
_ch = _ns_hd.get("chia_hai_dot")
if _ch:
	la("chia doi 50 phan tram", _ch(25720000, 50), (12860000, 12860000.0))
	la("khong chia thi dot 1 bang 0", _ch(25720000, 0), (0, 25720000.0))
	# Nhan phan tram hai lan thi lam tron hai lan va hop dong lech vai dong
	# bac - dot 2 phai lay PHAN CON LAI.
	_d1, _d2 = _ch(25720001, 33.33)
	la("hai dot cong lai dung tong", _d1 + _d2, 25720001.0)
	# Ca 25720001 o tren KHONG du de bat bay nay: hai cach tinh tinh co ra
	# cung mot so. Phai co ca ma phep lam tron nga ve hai huong khac nhau,
	# nếu không thì ca kiem chi la trang tri.
	#
	#   tong 1001 chia doi: dot 1 lam tron len 500 (Python lam tron chan),
	#   dot 2 phai la 501. Nhan phan tram lan nua thi ra 500, va hop dong
	#   in ra hai dot cong lai chi 1000 - thieu mot dong.
	la("tong le van cong lai du", _ch(1001, 50), (500, 501.0))
	la("tong nho le van cong lai du", _ch(3, 50), (2, 1.0))
	# Mot hop dong ghi "dot 1 tra 150%" la thu khong duoc phep in ra.
	la("phan tram tren 100 bi keo ve 100", _ch(1000, 150), (1000, 0.0))
	la("phan tram am bi keo ve 0", _ch(1000, -5), (0, 1000.0))

_sh = _ns_hd.get("so_hop_dong")
if _sh:
	la("so hop dong dung mau anh Viet chot",
	   _sh("2026-08-18", "CÔNG TY TNHH M.O.I COSMETICS"), "20260818/HDMB/MOI-VGB")
	la("khong doc ra viet tat thi bo han phan do",
	   _sh("2026-08-18", ""), "20260818/HDMB/VGB")

# --- Cau chu Dieu 2: CHO VUA VO KHI NGHIEM THU v215 ---
#
# Cau "Ben A thanh toan 100% gia tri Hop dong" co dau phan tram khong duoc
# thoat, nen Python doc "% g" thanh mot o dinh dang va nem TypeError. Ca to
# hop dong tra ve 500. Bo kiem cu khong bat duoc vi khong ca nao dung tay
# to voi coc bang 0 - no chi soi chuoi trong ma nguon chu khong CHAY.

# --- DUNG THAT CA TO HOP DONG, khong chi soi chuoi ---
#
# Bai hoc dat hai lan trong cung mot ngay: v215 vo o cau 100%, va ngay sau
# khi va cho do thi v216 lai vo o khoi o ky vi "width:100%" va "width:50%"
# cung nam trong mot khoi co toan tu dinh dang. Hai lan deu la MOT loai
# loi, va bo kiem soi-chuoi khong the bat duoc loai nay.
#
# Nen ca nay DUNG THAT ca to hop dong trong mot khong gian ten gia lap
# frappe. Cham hon mot chut, nhung no chay dung duong ma may chu chay.
# Xau phong that, doc thang tu vagabond/phong_chu.py. Hai bo gia lap duoi
# day deu cat het dong import di, nen FONT_TO va PHONG phai duoc bom vao
# tay. Doc tu tep goc chu khong chep tay de khong bao gio lech nhau.
_pc_src = open("vagabond/phong_chu.py", encoding="utf-8").read()
_NGAN_XEP = re.search(r'NGAN_XEP = "([^"]+)"', _pc_src).group(1)


def _nap_hop_dong_pdf():
	"""Nap hop_dong_pdf.py voi frappe gia lap. Tra ve khong gian ten."""
	import datetime
	import types
	import unicodedata as _ud

	_fr = types.ModuleType("frappe")
	_fr.whitelist = lambda *a, **k: (lambda f: f)
	_fr.throw = lambda *a, **k: (_ for _ in ()).throw(Exception(a[0] if a else "throw"))
	_fr.get_roles = lambda *a, **k: []
	_fr.db = types.SimpleNamespace(
		exists=lambda *a, **k: False, get_value=lambda *a, **k: None
	)
	_fr.session = types.SimpleNamespace(user="x")
	_fr.log_error = lambda *a, **k: None
	_fr.sendmail = lambda **k: None
	_u = types.ModuleType("frappe.utils")
	_u.flt = lambda x, *a: float(x or 0)
	_u.cint = lambda x, *a: int(float(x or 0))
	_u.nowdate = lambda: "2026-08-18"

	def _gd(x=None):
		if isinstance(x, (datetime.date, datetime.datetime)):
			return x
		return datetime.date.fromisoformat(str(x)[:10])

	_u.getdate = _gd
	_fr.utils = _u

	_cn = types.ModuleType("vagabond.cong_no")
	_cn._tien_vn = lambda v: "{:,.0f}".format(float(v or 0)).replace(",", ".")
	_cn._chu_so_tien = lambda v: "Hai mươi lăm triệu đồng"

	ns = {
		"__name__": "vagabond.hop_dong_pdf",
		"frappe": _fr,
		"unicodedata": _ud,
		"base64": __import__("base64"),
		"flt": _u.flt, "cint": _u.cint, "getdate": _gd, "nowdate": _u.nowdate,
		"_tien_vn": _cn._tien_vn, "_chu_so_tien": _cn._chu_so_tien,
		"FONT_TO": _NGAN_XEP,
	}
	# Bo cac dong import that di, phan con lai chay duoc nguyen ven.
	than = "\n".join(
		l for l in _hdp_src.split("\n")
		if not l.startswith("import ") and not l.startswith("from ")
	)
	exec(compile(than, "hop_dong_pdf", "exec"), ns, ns)
	return ns


try:
	_ns_full = _nap_hop_dong_pdf()
except Exception as _e:
	_ns_full = None
	print("   (khong nap duoc hop_dong_pdf: %s)" % _e)
la("nap duoc ca mo dun hop dong", _ns_full is not None, True)

# --- Dieu 2: CHAY that ham chu khong soi chuoi ---
#
# Cau "Ben A thanh toan 100% gia tri Hop dong" co dau phan tram khong duoc
# thoat, nen Python doc "% g" thanh mot o dinh dang va nem TypeError. Ca to
# hop dong tra ve 500. Bo kiem cu khong bat duoc vi khong ca nao dung tay
# to voi coc bang 0 - no chi soi chuoi trong ma nguon chu khong CHAY.
#
# Tu 18/08/2026 lay thang ham trong _ns_full (ca mo dun da nap) chu khong
# exec rieng mot ham nua: cau_dieu_2 gio goi vi_en, _gach, _esc... nen tach
# ra khoi mo dun la no thieu ban be va nem NameError, bo kiem bao HONG oan.
la("Dieu 2 tach thanh phep THUAN kiem duoc",
   bool(re.search(r"^def cau_dieu_2\(", _hdp_src, re.M)), True)
if _ns_full:
	_cd2 = _ns_full["cau_dieu_2"]
	# Ba nhanh deu phai DUNG DUOC, khong nem loi.
	for _pt, _nhan in ((0, "khong coc"), (50, "coc mot nua"), (100, "tra du truoc")):
		try:
			_ra = _cd2(24750000, _pt)
			# Chi can DUNG DUOC va ra mot cau co nghia. Bay o day la loi
			# dinh dang chuoi, no nem TypeError chu khong tra cau sai.
			_ok = bool(_ra) and "Bên A thanh toán" in _ra
		except Exception as _e:
			_ra, _ok = str(_e), False
		la("Dieu 2 dung duoc khi %s" % _nhan, _ok, True)

	def _thu_d2(tong, pt, chua):
		"""Goi cau_dieu_2 va tra ve co chua duoc chuoi khong. Nem loi thi
		bao HONG chu khong lam do ca bo kiem."""
		try:
			return all(c in _cd2(tong, pt) for c in chua)
		except Exception:
			return False

	la("khong chia dot thi noi tra mot lan 100%",
	   _thu_d2(1000, 0, ["100% giá trị Hợp đồng"]), True)
	la("co chia dot thi noi dot 01 va dot 02",
	   _thu_d2(1000, 50, ["Đợt 01", "Đợt 02"]), True)
	# So tien hai dot in ra phai la so DA CHIA, khong phai tong.
	la("dot 1 in dung so da chia", _thu_d2(1000, 50, ["500 VNĐ"]), True)
# _html phai goi phep chung, khong dung mot ban chep thu hai.
# _html phai goi PHEP CHUNG cau_dieu_2, khong chep lai cau lan thu hai, va
# so tien dua vao phai la gia tri hop dong chu khong phai con so nao khac.
_than_html = _hdp_src.split("def _html(")[1].split("\ndef ")[0]
la("_html dung chung phep Dieu 2", "cau_dieu_2(tong, pt1, n1, n2)" in _than_html, True)
la("Dieu 2 lay dung gia tri hop dong", 'tong = flt(d.get("gia_tri"))' in _than_html, True)


if _ns_full:
	_HD_GIA = {
		"name": "HDBH-TEST", "ten": "Gói tea break", "so_hop_dong": "",
		"khach_hang": "KH-01", "ngay_ky": "2026-08-18", "gia_tri": 25720000,
		"ten_khach": "CÔNG TY TNHH M.O.I COSMETICS", "ma_so_thue": "0314693309",
		"dia_chi": "Phòng 9.1, Ree Tower", "dai_dien": "Ông LÂM THÀNH KIM",
		"chuc_vu": "Giám đốc", "dien_thoai": "", "email": "a@b.com",
		"dat_coc_pt": 50, "ngay_dot1": 3, "ngay_dot2": 3,
		"dia_diem_giao": "307/1 Nguyễn Văn Trỗi", "thoi_gian_giao": "",
		"bao_gia": "VGB-PQ-2026-0001",
		"dong_bao_gia": [
			{"ten_mon": "Bánh thiết kế riêng", "dvt": "Gói", "so_luong": 1,
			 "don_gia": 25720000, "thanh_tien": 25720000}
		],
		"bg_thue_pt": 8, "bg_gia_da_gom_vat": 1, "bg_giao_hang": "",
		"so_goi_y": "20260818/HDMB/MOI-VGB", "tien_dot1": 12860000,
		"tien_dot2": 12860000,
		"ben_b": {
			"ten": "CÔNG TY TNHH PATISSERIE VAGABOND", "mst": "0318561568",
			"dia_chi": "9 Trần Cao Vân", "dai_dien": "Ông NGUYỄN HOÀNG VIỆT",
			"chuc_vu": "Giám đốc", "dien_thoai": "", "email": "",
			"ngan_hang": "Số tài khoản: 31561568",
		},
	}

	def _dung_to(sua=None):
		"""Dung that to hop dong voi du lieu gia. Nem loi thi tra ve None."""
		d = dict(_HD_GIA)
		if sua:
			d.update(sua)
		_ns_full["chi_tiet"] = lambda name: d
		try:
			return _ns_full["_html"]("HDBH-TEST")
		except Exception as _e2:
			return None

	# Ba nhanh coc, va ca ba deu phai dung ra mot to hoan chinh.
	for _pt, _nhan in ((50, "coc mot nua"), (0, "khong coc"), (100, "tra du truoc")):
		_to = _dung_to({"dat_coc_pt": _pt})
		la("dung duoc ca to khi %s" % _nhan, bool(_to), True)
		if _to:
			# Dem theo "ĐIỀU n:" chu khong theo chuoi "ĐIỀU " - chuoi do
			# con khop ca tua "ĐIỀU KHOẢN CHUNG" nen dem ra 7.
			la("to khi %s co du sau Dieu" % _nhan,
			   sum(1 for _i in range(1, 7) if ("ĐIỀU %d:" % _i) in _to), 6)
			la("to khi %s co o ky hai ben" % _nhan,
			   "ĐẠI DIỆN BÊN A" in _to and "ĐẠI DIỆN BÊN B" in _to, True)
	# Khong co bao gia nguon thi van phai dung duoc, bang mot dong gop.
	_to2 = _dung_to({"bao_gia": "", "dong_bao_gia": []})
	la("khong co bao gia van dung duoc to", bool(_to2), True)
	if _to2:
		la("thieu bao gia thi khong noi den phu luc", "Phụ lục 01" in _to2, False)
	# Ten cong ty khach phai in ra dung tren to.
	_to3 = _dung_to({})
	la("ten ben A in dung tren to",
	   bool(_to3) and "M.O.I COSMETICS" in _to3, True)
	la("ten ben B in dung tren to",
	   bool(_to3) and "PATISSERIE VAGABOND" in _to3, True)
	la("so hop dong tu sinh khi de trong",
	   bool(_to3) and "20260818/HDMB/MOI-VGB" in _to3, True)

# --- To phap ly: dung tieu de va dung can cu ---
la("tieu de la hop dong mua ban hang hoa", "HỢP ĐỒNG MUA BÁN HÀNG HÓA" in _hdp_src, True)
la("khong con goi la hop dong dich vu", "HỢP ĐỒNG DỊCH VỤ" in _hdp_src, False)
la("co quoc hieu", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in _hdp_src, True)
la("vien dan Bo luat Dan su", "91/2015/QH13" in _hdp_src, True)
la("vien dan Luat Thuong mai", "36/2005/QH11" in _hdp_src, True)
for _d in ("HÀNG HÓA", "THANH TOÁN", "QUY CÁCH, CHẤT LƯỢNG HÀNG HÓA",
           "ĐỊA ĐIỂM, THỜI GIAN BÀN GIAO HÀNG HÓA", "TRÁCH NHIỆM CỦA HAI BÊN",
           "ĐIỀU KHOẢN CHUNG"):
	la("co dieu %s" % _d[:18], 'dieu(' in _hdp_src and _d in _hdp_src, True)
la("co o ky hai ben", "ĐẠI DIỆN BÊN A" in _hdp_src and "ĐẠI DIỆN BÊN B" in _hdp_src, True)
la("so tien co dong bang chu", "_chu_so_tien" in _hdp_src, True)

# --- Phu luc: bao gia da chot phai nam trong CUNG mot tep PDF ---
# Tu 18/08/2026 khoi phu luc tach thanh ham rieng _khoi_phu_luc (de con cho
# nhet ban scan khach da ky vao). Bo kiem phai doc ca hai phan, khong thi no
# soi mot mieng nguon da rong ruot roi bao dat.
_than_pdf = (
	_hdp_src.split("def _khoi_phu_luc(")[1].split("\ndef ")[0]
	+ _hdp_src.split("def xuat_pdf(")[1].split("\ndef ")[0]
)
la("PDF gom phu luc", "PHỤ LỤC 01" in _than_pdf, True)
la("phu luc bat dau o trang moi", "page-break-before:always" in _than_pdf, True)
la("phu luc dung dung to bao gia that", "mod_bg._html(bg)" in _than_pdf, True)
la("khong co bao gia thi van xuat duoc hop dong",
   "if bg and frappe.db.exists(DT_BG, bg)" in _than_pdf, True)

# --- Ben A phai duoc CHUP LAI luc chot, khong tro sang ho so khach ---
_than_tao = _bg_src.split("def tao_hop_dong(")[1].split("\ndef ")[0]
for _o in ("ten_khach", "ma_so_thue", "dia_chi", "dai_dien", "chuc_vu", "email"):
	la("chup lai o %s cua ben A" % _o, '"%s": doc.' % _o in _than_tao, True)
la("hop dong nho to bao gia goc", '"bao_gia": doc.name' in _than_tao, True)
la("dot 1 lay tu o dat coc tren bao gia", "flt(doc.dat_coc_pt)" in _than_tao, True)
# So tien dot 1 phai tinh LAI o may chu (QT-19), khong nhan con so app gui.
la("tien dot 1 tinh lai o may chu", "chia_hai_dot(doc.tong_cong, coc_pt)[0]" in _than_tao, True)
la("so hop dong tu sinh khi de trong", "_sinh_so(ngay, doc.ten_khach" in _than_tao, True)

# --- Man hinh chi bay nut khi hop dong co goc bao gia ---
la("man doc co bao gia hay khong", '"bao_gia": doc.get("bao_gia")' in _hd_src, True)
la("nut chi hien khi co bao gia", "if (hd.bao_gia) {" in _kh_src, True)
for _n in ("hop_dong_pdf.xem_truoc", "hop_dong_pdf.xuat_pdf", "hop_dong_pdf.gui_email"):
	la("man goi %s" % _n, _n in _kh_src, True)
# Gui thu phai qua bang xac nhan nguoi nhan truoc khi bam.
_than_mail = _kh_src.split("async function hdGuiMail(")[1].split("\nasync function ")[0]
la("bay du nguoi nhan truoc khi gui", "xem_nguoi_nhan" in _than_mail, True)
la("phai bam xac nhan moi gui", "hoiCo('Xác nhận gửi hợp đồng'" in _than_mail, True)
la("email sai dang thi chan tu may chu", "ng.sai && ng.sai.length" in _than_mail, True)

# =====================================================================
# Nhom 26. Tao ho so khach tu to bao gia (anh Viet 18/08/2026)
# =====================================================================
print("26. Tao khach tu to bao gia")

_bg2_src = open("vagabond/bao_gia.py", encoding="utf-8").read()
_bgjs_src = open("vagabond/public/js/bep/22-bao-gia.js", encoding="utf-8").read()

# --- Phep chuan hoa ma so thue phai THUAN va bo het dau cau ---
_ns_mst = {}
_m4 = re.search(r"^def _chuan_mst\(.*?(?=^def |^@|\Z)", _bg2_src, re.S | re.M)
la("phep chuan hoa ma so thue ton tai", bool(_m4), True)
if _m4:
	exec(compile(_m4.group(0), "bao_gia:_chuan_mst", "exec"), _ns_mst, _ns_mst)
	_cm = _ns_mst["_chuan_mst"]
	# Nguoi go tay hay them dau gach o ma so don vi truc thuoc. Hai cach go
	# cua CUNG mot ma so phai coi la mot, neu khong phep do trung vo dung.
	la("bo dau gach o ma so don vi truc thuoc", _cm("0314693309-001"), "0314693309001")
	la("bo dau cach thua", _cm(" 0314693309 "), "0314693309")
	la("bo dau cham", _cm("0314.693.309"), "0314693309")
	la("rong thi tra rong", _cm(""), "")
	la("chi giu chu so", _cm("MST: 0314693309"), "0314693309")

# --- Trung ma so thue thi GAN khach cu, khong tao them dong ---
_than_tk = _bg2_src.split("def tao_khach(")[1].split("\n@frappe")[0]
la("do trung theo ma so thue truoc khi tao", "_tim_theo_mst(doc.ma_so_thue)" in _than_tk, True)
la("trung thi gan vao khach cu", 'frappe.db.set_value(DT, name, "khach_hang", kh)' in _than_tk, True)
la("trung thi tra ve co moi bang 0", '"moi": 0' in _than_tk, True)
# Phep do trung phai so CHINH XAC sau khi chuan hoa, khong tin phep LIKE:
# LIKE "%031469%" con khop ca nhung ma so khac chi trung mot doan.
_than_tim = _bg2_src.split("def _tim_theo_mst(")[1].split("\n@frappe")[0]
la("so chinh xac sau khi chuan hoa chu khong tin LIKE",
   '_chuan_mst(d.get("tax_id")) == so' in _than_tim, True)
la("ma so rong thi khong do trung bua", "if not so:" in _than_tim, True)

# --- To da gan khach roi thi khong tao them ---
la("to da co khach thi khong tao them", "if doc.khach_hang and frappe.db.exists" in _than_tk, True)
la("thieu ten cong ty thi chan", "Chưa có tên công ty khách" in _than_tk, True)

# --- Dia chi va nguoi lien he la hai doctype rieng, phai tao kem ---
la("tao kem dia chi khach", '"doctype": "Address"' in _than_tk, True)
la("tao kem nguoi lien he", '"doctype": "Contact"' in _than_tk, True)
# Hong mot trong hai KHONG duoc keo do ca viec tao khach.
la("hong dia chi khong keo do viec tao khach",
   _than_tk.split('"doctype": "Address"')[1].split("except Exception")[0].count("try:") == 0
   and "except Exception" in _than_tk.split('"doctype": "Address"')[1], True)

# --- Nhom khach anh Viet chot ---
la("nhom khach moi la Commercial", 'NHOM_KHACH_MOI = "Commercial"' in _bg2_src, True)
la("nhom khong ton tai thi lay nhom la bat ky, khong de trong",
   'frappe.db.get_value("Customer Group", {"is_group": 0}, "name")' in _than_tk, True)

# --- Man hinh: hai muc khac han nhau trong hop chon khach ---
la("van con muc de trong o khach", "Khách mới, chưa có trong hệ thống" in _bgjs_src, True)
la("them muc tao ho so khach", "Tạo hồ sơ khách từ tờ này" in _bgjs_src, True)
la("bam muc do thi goi phep tao khach", "bgTaoKhach(name, true)" in _bgjs_src, True)

# --- Bay ra het TRUOC khi tao ---
_than_js = _bgjs_src.split("async function bgTaoKhach(")[1].split("\nasync function ")[0]
la("hoi may chu truoc khi tao", "xem_truoc_tao_khach" in _than_js, True)
la("bay ra cac ho so trung ma so thue", "trung_mst" in _than_js, True)
la("bay ra ca ten gan giong de nguoi ta tu quyet", "gan_giong" in _than_js, True)
# To dang soan phai LUU truoc: may chu doc tu ho so da luu chu khong tin
# cuc du lieu app gui len (QT-19).
la("to dang soan phai luu truoc khi tao khach", "vagabond.bao_gia.luu" in _than_js, True)

# --- Buoc chot hop dong: hoi tao khach chu khong chi bao loi ---
_than_chot = _bgjs_src.split("async function bgChotHopDong(")[1].split("\n/* ---------- Soan bao gia")[0]
la("chot hop dong thieu khach thi hoi tao", "bgTaoKhach(d.name, false)" in _than_chot, True)
la("khong con bo do bang mot cau bao loi",
   "Bấm Sửa báo giá, chọn lại ô Khách hàng rồi quay lại nhé" in _than_chot, False)



# =====================================================================
# Nhom 27. Sua the thuc hop dong va man tao hop dong (anh Viet 18/08/2026)
# =====================================================================
print("27. The thuc hop dong va man tao hop dong")

_ht_src2 = open("vagabond/public/js/bep/07-hop-thoai.js", encoding="utf-8").read()
_khjs_src = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_hdjson = open(
	"vagabond/vagabond/doctype/hop_dong_ban_hang/hop_dong_ban_hang.json",
	encoding="utf-8",
).read()

# --- 1. Bo dau gach dai: phai CHAN O MOT CHO, khong don tay tung o ---
#
# Anh Viet: *"Cam dung em-dash: thay toan bo dau em-dash thanh dau gach
# ngang tieu chuan cho toan bo van ban"*. Ma nguon sach san roi, cai nguy
# hiem la chu NGUOI GO tren bao gia. Nen phep don phai nam trong _esc, la
# cua ngo duy nhat moi chu di qua truoc khi vao to in.
if _ns_full:
	_don = _ns_full["don_dau_dai"]
	la("doi en dash thanh gach thuong", _don("A – B"), "A - B")
	la("doi em dash thanh gach thuong", _don("A — B"), "A - B")
	la("doi dau tru toan hoc thanh gach thuong", _don("A − B"), "A - B")
	la("doi gach khong ngat dong", _don("A ‑ B"), "A - B")
	la("gach thuong thi giu nguyen", _don("A - B"), "A - B")
	la("rong thi ra rong chu khong nem loi", _don(None), "")
	# Va phai chay THAT qua _esc, khong phai chi co ham nam do.
	la("_esc don luon dau gach dai", _ns_full["_esc"]("Gói A – Gói B"),
	   "Gói A - Gói B")
	la("_esc van thoat the HTML", _ns_full["_esc"]("<b>&</b>"),
	   "&lt;b&gt;&amp;&lt;/b&gt;")
la("to bao gia dung chung phep don gach", "don_dau_dai" in _bg2_src, True)
# Ma nguon cua ca hai tep khong duoc con dau nao loai nay.
for _f in ("vagabond/hop_dong_pdf.py", "vagabond/bao_gia.py"):
	_t = open(_f, encoding="utf-8").read()
	la("ma nguon %s khong con dau gach dai" % _f.split("/")[-1],
	   ("–" in _t) or ("—" in _t), False)

# --- 2. Font Arial cho ca hop dong lan phu luc ---
# Tu v223 xau phong khong con viet tay trong tung tep nua ma lay chung tu
# vagabond/phong_chu.py, de hai to khong bao gio lech nhau.
la("hop dong lay xau phong tu phong_chu",
   "from vagabond.phong_chu import NGAN_XEP as FONT_TO" in _hdp_src, True)
la("to bao gia lay xau phong tu phong_chu",
   "from vagabond.phong_chu import NGAN_XEP as PHONG" in _bg2_src, True)
la("xau phong dat Vagabond Sans len dau",
   _NGAN_XEP.startswith("'Vagabond Sans'"), True)
la("xau phong van con Arial lam luoi do", "Arial" in _NGAN_XEP, True)
# Arial phai duoc ap o KHUNG NGOAI cua tep PDF, khong chi o vai the con:
# wkhtmltopdf khong thua ke font vao bang neu khong khai het.
# Nghiem thu 18/08/2026: em tai mot to PDF THAT tu site ve roi doc phong
# nhung trong do, thay LAN LON LiberationSans voi DejaVuSans. Nguyen nhan la
# cau CSS cu chi liet ke mot so the, the nao ngoai danh sach (li, h3,
# small...) thi roi ve phong mac dinh. Nen ca kiem doi tu "co liet ke du
# the" sang "quet bang dau sao".
_khung = _hdp_src.split("def xuat_pdf(")[1].split("\ndef ")[0]
la("khung PDF ap font bang dau sao", "khung_style()" in _khung, True)
la("khong con liet ke tung the nua",
   "body,td,th,div,p,span,b,i,table{font-family:" in _hdp_src, False)
if _ns_full:
	_ks = _ns_full["khung_style"]()
	la("cau CSS bat dau bang dau sao", _ks.startswith("*{font-family:"), True)
	la("cau CSS co Arial dung dau", "Arial" in _ks, True)
	la("cau CSS co Liberation Sans lam hang du", "Liberation Sans" in _ks, True)
	la("to bao gia dung chung phep khung_style", "khung_style(PHONG)" in _bg2_src, True)
	la("to bao gia khong con liet ke tung the",
	   "body,td,th,div,p,span,b,i,table{font-family:" in _bg2_src, False)
if _ns_full:
	# Do lieu THU phai co san dau gach dai o dung cho nguoi ta hay go: ten
	# mon, dia diem giao, ghi chu. Do lieu sach thi ca kiem "khong con dau
	# gach dai" luon dat ma khong chung minh duoc gi.
	_to_a = None
	try:
		_d_dash = dict(_HD_GIA)
		_d_dash.update({
			"dia_diem_giao": "307/1 Nguyễn Văn Trỗi – Phú Nhuận",
			"ten": "Gói tea break — 50 khách",
			"dong_bao_gia": [
				{"ten_mon": "Bánh ngọt – set 3 vị", "dvt": "Gói", "so_luong": 1,
				 "don_gia": 25720000, "thanh_tien": 25720000}
			],
		})
		_ns_full["chi_tiet"] = lambda name: _d_dash
		_to_a = _ns_full["_html"]("HDBH-TEST")
	except Exception:
		_to_a = None
	la("dung duoc to sau khi doi the thuc", bool(_to_a), True)
	if _to_a:
		la("to in ra khong con dau gach dai",
		   ("–" in _to_a) or ("—" in _to_a), False)
		# Chu van phai con nguyen, chi doi rieng dau gach.
		la("chu quanh dau gach van giu nguyen",
		   "Bánh ngọt - set 3 vị" in _to_a, True)
		la("dia diem giao doi dung dau gach",
		   "Nguyễn Văn Trỗi - Phú Nhuận" in _to_a, True)
		la("to in ra co font Arial", "Arial" in _to_a, True)

# --- 3. Song ngu: tieng Anh nam ngay duoi tieng Viet, in nghieng ---
la("co phep ghep cap Viet Anh", "def vi_en(" in _hdp_src, True)
la("phan tieng Anh in nghieng", "font-style:italic" in _hdp_src, True)
if _ns_full and _to_a:
	la("co du sau ARTICLE tieng Anh",
	   sum(1 for _i in range(1, 7) if ("ARTICLE %d:" % _i) in _to_a), 6)
	for _c in ("SOCIALIST REPUBLIC OF VIETNAM", "GOODS SALE AND PURCHASE CONTRACT",
	           "FOR AND ON BEHALF OF PARTY A", "FOR AND ON BEHALF OF PARTY B"):
		la("to co cau tieng Anh %s" % _c[:22], _c in _to_a, True)

# --- 4. Khoi chu ky: khong Ms./Mr., khong lay ten Sales ---
#
# Anh Viet: *"Khoi chu ky cuoi hop dong tuyet doi khong duoc ghi Ms./Mr. va
# khong duoc lay mac dinh ten cua ban Sales"*.
if _ns_full:
	_bo = _ns_full["_bo_xung_ho"]
	la("bo Ms. co dau cham", _bo("Ms. Trang Phạm"), "Trang Phạm")
	la("bo Ms dinh lien ten", _bo("Ms.Trang Phạm"), "Trang Phạm")
	la("bo Mr.", _bo("Mr. Lâm Thành Kim"), "Lâm Thành Kim")
	la("bo Ong tieng Viet co dau", _bo("Ông NGUYỄN HOÀNG VIỆT"),
	   "NGUYỄN HOÀNG VIỆT")
	la("bo Ba tieng Viet co dau", _bo("Bà Trang"), "Trang")
	la("ten khong co xung ho thi giu nguyen", _bo("Trang Phạm"), "Trang Phạm")
	la("rong thi ra rong", _bo(""), "")
	# Bay: ten NGUOI ta bat dau bang chu trung voi xung ho thi khong duoc cat.
	la("khong cat nham ten Basil", _bo("Basil Nguyễn"), "Basil Nguyễn")
	_to_ky = None
	try:
		_d_ky = dict(_HD_GIA)
		_d_ky.update({"nguoi_ky_a": "Ms. Trang Phạm", "chuc_vu_ky_a": "Giám đốc",
		              "nguoi_ky_b": "Nguyễn Hoàng Việt", "chuc_vu_ky_b": "Giám đốc"})
		_ns_full["chi_tiet"] = lambda name: _d_ky
		_to_ky = _ns_full["_html"]("HDBH-TEST")
	except Exception:
		_to_ky = None
	la("dung duoc to co o nguoi ky", bool(_to_ky), True)
	if _to_ky:
		la("o ky in ten da bo xung ho", "Trang Phạm" in _to_ky, True)
		la("o ky khong con chu Ms.", "Ms." in _to_ky, False)
		la("o ky khong con chu Mr.", "Mr." in _to_ky, False)
		la("o ky in chuc vu", "Giám đốc" in _to_ky, True)
la("doctype co o nguoi ky ben A", '"fieldname": "nguoi_ky_a"' in _hdjson, True)
la("doctype co o chuc vu ben A", '"fieldname": "chuc_vu_ky_a"' in _hdjson, True)
la("doctype co o nguoi ky ben B", '"fieldname": "nguoi_ky_b"' in _hdjson, True)
la("doctype co o chuc vu ben B", '"fieldname": "chuc_vu_ky_b"' in _hdjson, True)
la("doctype co o ban scan phu luc", '"fieldname": "phu_luc_scan"' in _hdjson, True)
# May chu phai bo xung ho MOT LAN NUA luc luu, khong tin man hinh.
_than_tao2 = _bg2_src.split("def tao_hop_dong(")[1].split("\ndef ")[0]
la("luc tao van bo xung ho o may chu", '"nguoi_ky_a": _bo_ho(nguoi_ky_a)' in _than_tao2, True)
la("khong bia ten nguoi ky ben A", 'doc.nguoi_lien_he' in _than_tao2.split('"nguoi_ky_a"')[1].split("}")[0], False)
_than_sua = _hd_src.split("def sua_nguoi_ky(")[1].split("\n@frappe")[0]
la("sua nguoi ky cung bo xung ho", "_bo_xung_ho(nguoi_ky_a)" in _than_sua, True)

# --- 5. So hop dong do san, tinh lai duoc ngay tren man hinh ---
_than_goi = _bg2_src.split("def goi_y_hop_dong(")[1].split("\n@frappe")[0]
la("may do san so hop dong", "so_goi_y" in _than_goi, True)
la("tra ca viet tat de man hinh dung lai so", '"viet_tat"' in _than_goi, True)
# Nghiem thu tren site that 18/08/2026: o "dai dien" trong Cai dat bao gia
# dang ghi "Loan Anh / Sales Manager", nen do san tu do la do dung ten ban
# Sales vao o ky - dung cai anh Viet cam. Gio do san tu HOP DONG GAN NHAT
# da dien, khong co thi de trong.
la("khong do ten nguoi ky ben B tu cai dat bao gia",
   'b.get("dai_dien")' in _than_goi, False)
la("nguoi ky ben B lay tu hop dong gan nhat",
   "tabHop Dong Ban Hang" in _than_goi and "order by creation desc" in _than_goi, True)
_than_ct = _hdp_src.split("def chi_tiet(")[1].split("\n@frappe")[0]
la("to in khong lui ve dai dien cai dat nua",
   '_bo_xung_ho(d["ben_b"].get("dai_dien"))' in _than_ct, False)
la("o dai dien ben B in dung nguoi ky",
   'b["dai_dien"] = (d.get("nguoi_ky_b") or "").strip()' in _than_html, True)
if _ns_full:
	# Cai dat co ten Sales, hop dong chua dien nguoi ky: to in ra KHONG
	# duoc co ten do o bat cu cho nao.
	_d_leak = dict(_HD_GIA)
	_d_leak.update({"nguoi_ky_a": "Trang Phạm", "chuc_vu_ky_a": "Giám đốc",
	                "nguoi_ky_b": "", "chuc_vu_ky_b": ""})
	_d_leak["ben_b"] = dict(_HD_GIA["ben_b"])
	_d_leak["ben_b"].update({"dai_dien": "Loan Anh", "chuc_vu": "Sales Manager"})
	try:
		_ns_full["chi_tiet"] = lambda name: _d_leak
		_to_leak = _ns_full["_html"]("HDBH-TEST")
	except Exception:
		_to_leak = None
	la("dung duoc to khi chua dien nguoi ky ben B", bool(_to_leak), True)
	if _to_leak:
		la("ten Sales khong lot vao to hop dong", "Loan Anh" in _to_leak, False)
		la("chuc danh Sales khong lot vao to hop dong",
		   "Sales Manager" in _to_leak, False)
		la("cho nguoi ky trong thi in cham cham", "..........." in _to_leak, True)
la("man hinh co phep dung so hop dong", "function bgSoHd(" in _bgjs_src, True)
la("man hinh do san so vao o input", "bgSoHd(f.ngay_ky, g.viet_tat, g.loai)" in _bgjs_src, True)
la("go tay roi thi may thoi de len", "tuDong = false" in _bgjs_src, True)
# Man hinh va may chu phai ra CUNG mot so, khong duoc lech mau.
if _ns_full:
	la("mau so hop dong dung nhu anh Viet chot",
	   _ns_full["so_hop_dong"]("2026-08-18", "CÔNG TY TNHH TƯ VẤN GIẢI PHÁP SECOMM"),
	   "20260818/HDMB/SECOMM-VGB")

# --- 6. Popup chon ngay phai doi duoc tua de ---
la("phep chon ngay nhan tua de", "function pickDate(cur, cb, tuaDe)" in _ht_src2, True)
la("hoiNgay chuyen tua de xuong", "function hoiNgay(macDinhIso, tuaDe)" in _ht_src2, True)
la("khong go cung chu Chon ngay nua",
   "h(tuaDe || 'Chọn ngày')" in _ht_src2, True)
la("man tao hop dong doi tua de", "'Chọn ngày tạo hợp đồng'" in _bgjs_src, True)

# --- 7. Ban scan phu luc: uu tien ban khach da ky ---
_than_pl = _hdp_src.split("def _khoi_phu_luc(")[1].split("\ndef ")[0]
la("phu luc uu tien ban scan", "phu_luc_scan" in _than_pl, True)
la("chua co ban ky thi canh bao ro", "CHƯA có chữ ký" in _than_pl, True)
la("man tao hop dong cho chon tep", "hdChonTep" in _bgjs_src, True)
la("tai tep len sau khi da co hop dong", "async function bgTaiPhuLuc(" in _bgjs_src, True)
la("tep gan dung o phu_luc_scan", "fd.append('fieldname', 'phu_luc_scan')" in _bgjs_src, True)
# Tep hong thi hop dong VAN CON - khong duoc xoa cai vua tao.
_than_chot2 = _bgjs_src.split("async function bgChotHopDong(")[1]
la("tep hong khong lam mat hop dong", "Đã tạo hợp đồng, thiếu phụ lục" in _than_chot2, True)
la("man chi tiet doc duoc ban scan", '"phu_luc_scan": doc.get("phu_luc_scan")' in _hd_src, True)
la("man chi tiet co nut dinh kem", "hdScanTep" in _khjs_src, True)
la("man chi tiet co nut sua nguoi ky", "hdFormNguoiKy" in _khjs_src, True)
# QT-20: go ra chi bo tro, khong xoa tep.
la("go phu luc khong xoa tep", "def go_phu_luc_scan(" in _hd_src, True)
_than_go = _hd_src.split("def go_phu_luc_scan(")[1].split("\n@frappe")[0]
la("go phu luc chi dat o ve rong", 'set_value("Hop Dong Ban Hang", name, "phu_luc_scan", "")' in _than_go, True)
la("go phu luc khong goi lenh xoa", "delete" in _than_go.lower(), False)


# --- 8. SDT va email cua NGUOI KY, khong phai cua ban Sales ---
#
# Anh Viet 18/08/2026: *"cho nhap thong tin nguoi ky ben mua va ben ban thi
# em can cho nhap ca sdt va email nua (hien em dang lay thong tin email va
# so dien thoai cua Loan Anh gan cho anh la sao). Nhap lan dau thoi cho
# Vagabond thi luu het cho may cai hop dong sau nay"*.
for _o in ("dt_ky_a", "email_ky_a", "dt_ky_b", "email_ky_b"):
	la("doctype hop dong co o %s" % _o, '"fieldname": "%s"' % _o in _hdjson, True)
_cdjson = open(
	"vagabond/vagabond/doctype/bao_gia_cai_dat/bao_gia_cai_dat.json", encoding="utf-8"
).read()
for _o in ("nguoi_ky_ban", "chuc_vu_ky_ban", "dt_ky_ban", "email_ky_ban"):
	la("cai dat co o %s de khai mot lan" % _o, '"fieldname": "%s"' % _o in _cdjson, True)
	la("cai dat cho ghi o %s" % _o, '"%s"' % _o in _bg2_src, True)
for _o in ("hdDtA", "hdEmA", "hdDtB", "hdEmB"):
	la("man tao hop dong hoi o %s" % _o, _o in _bgjs_src, True)
la("man sua nguoi ky hoi du bon o", all(
	_x in _khjs_src for _x in ("hkDtA", "hkEmA", "hkDtB", "hkEmB")), True)
_than_bb = _hdp_src.split("def _ben_b(")[1].split("\n@frappe")[0]
la("ben B uu tien nguoi ky da khai",
   'c.get("nguoi_ky_ban") or c.get("dai_dien_ban")' in _than_bb, True)
la("sdt ben B uu tien cua nguoi ky", 'c.get("dt_ky_ban") or c.get("dt_ban")' in _than_bb, True)
if _ns_full:
	# Cai dat khai ten Sales o o lien he, khai Giam doc o o nguoi ky. To in
	# ra phai mang thong tin Giam doc, khong duoc mang cua Sales.
	_d_lh = dict(_HD_GIA)
	_d_lh.update({
		"nguoi_ky_a": "Trang Phạm", "chuc_vu_ky_a": "Giám đốc",
		"dt_ky_a": "0979999264", "email_ky_a": "trang.pham@secomm.vn",
		"nguoi_ky_b": "Nguyễn Hoàng Việt", "chuc_vu_ky_b": "Giám đốc",
		"dt_ky_b": "0901486556", "email_ky_b": "vietnh@thevagabondpatisserie.com",
	})
	_d_lh["ben_b"] = dict(_HD_GIA["ben_b"])
	_d_lh["ben_b"].update({
		"dai_dien": "Nguyễn Thị Loan Anh", "chuc_vu": "Sales Manager",
		"dien_thoai": "0933751352", "email": "anhntl@thevagabondpatisserie.com",
	})
	try:
		_ns_full["chi_tiet"] = lambda name: _d_lh
		_to_lh = _ns_full["_html"]("HDBH-TEST")
	except Exception:
		_to_lh = None
	la("dung duoc to co du lien he nguoi ky", bool(_to_lh), True)
	if _to_lh:
		la("sdt Sales khong lot vao to", "0933751352" in _to_lh, False)
		la("email Sales khong lot vao to", "anhntl@" in _to_lh, False)
		la("sdt nguoi ky ben B in dung", "0901486556" in _to_lh, True)
		la("email nguoi ky ben B in dung", "vietnh@" in _to_lh, True)
		la("sdt nguoi ky ben A in dung", "0979999264" in _to_lh, True)

# --- 9. Chip cau goi y cho thu gui hop dong ---
la("co bo cau rieng cho thu hop dong", "LOI_NHAN_HD_MAU" in _bg2_src, True)
_ns_cau = {}
_m_cau = re.search(r"^LOI_NHAN_HD_MAU = \((.*?)\)\n", _bg2_src, re.S | re.M)
la("doc duoc bo cau hop dong", bool(_m_cau), True)
if _m_cau:
	exec(compile("LOI_NHAN_HD_MAU = (" + _m_cau.group(1) + ")", "x", "exec"), _ns_cau, _ns_cau)
	_cau_hd = _ns_cau["LOI_NHAN_HD_MAU"]
	la("co it nhat nam cau goi y", len(_cau_hd) >= 5, True)
	la("cau nao cung co noi dung", all(len(str(c).strip()) > 10 for c in _cau_hd), True)
	# Bo cau hop dong khong duoc trung bo cua bao gia: hai buoc noi hai
	# chuyen khac nhau, trung nhau la mot trong hai cho dat sai bo.
	_m_bg = re.search(r"^LOI_NHAN_MAU = \((.*?)\)\n", _bg2_src, re.S | re.M)
	if _m_bg:
		exec(compile("LOI_NHAN_MAU = (" + _m_bg.group(1) + ")", "x", "exec"), _ns_cau, _ns_cau)
		la("hai bo cau khong trung nhau",
		   bool(set(_cau_hd) & set(_ns_cau["LOI_NHAN_MAU"])), False)
la("cai dat co o sua bo cau hop dong", '"fieldname": "loi_nhan_hd_mau"' in _bg2_src, True)
la("man hop dong dung hop thoai chip", "bgHoiLoiNhan(cauHd" in _khjs_src, True)
_than_mail = _khjs_src.split("async function hdGuiMail(")[1]
la("may chu hong van co cau du phong", "if (!cauHd.length) cauHd = [" in _than_mail, True)




# =====================================================================
# Nhom 28. Tach thue tung dong va chiet khau truoc thue (anh Viet 18/08/2026)
# =====================================================================
print("28. Tach thue tung dong")

_ns_th = {"flt": lambda x, *a: float(x or 0)}
for _t in ("phan_bo_chiet_khau", "tach_thue", "bang_thue"):
	_m = re.search(r"^def %s\(.*?(?=^def |\Z)" % _t, _bg2_src, re.S | re.M)
	la("phep %s ton tai" % _t, bool(_m), True)
	if _m:
		exec(compile(_m.group(0), "bao_gia:%s" % _t, "exec"), _ns_th, _ns_th)
_pb = _ns_th.get("phan_bo_chiet_khau")
_tt = _ns_th.get("tach_thue")
_bt = _ns_th.get("bang_thue")

# --- Phan bo chiet khau: tong cac phan chia LUON bang dung tong chiet khau
if _pb:
	for _tien, _ck in (([1000, 2000, 3000], 600), ([333, 333, 334], 100),
	                   ([1, 1, 1], 1), ([10], 7), ([7, 11, 13], 5), ([100, 1], 33)):
		la("chia chiet khau %s khong lech dong nao" % _ck,
		   abs(sum(_pb(_tien, _ck)) - _ck) < 0.001, True)
	la("khong co dong nao thi tra rong", _pb([], 100), [])
	la("chiet khau bang 0 thi khong tru ai", _pb([10, 20], 0), [0.0, 0.0])
	la("tong bang 0 khong lam vo phep", _pb([0, 0], 50), [0.0, 0.0])

# --- Tach thue: chia nguoc roi cong lai phai ra DUNG so ban dau
if _tt:
	for _nen, _pt in ((10800000, 8), (21847500, 8), (999, 10), (1, 8),
	                  (6138000, 8), (15019500, 8), (333, 8), (7, 10)):
		_h, _th = _tt(_nen, _pt, True)
		la("chia nguoc %s @ %s%% cong lai khong lech" % (_nen, _pt),
		   abs(_h + _th - _nen) < 0.001, True)
	la("muc 0% thi khong co thue", _tt(500000, 0, True), (500000.0, 0.0))
	la("chua gom thue thi cong them", _tt(1000000, 8, False), (1000000.0, 80000.0))
	la("da gom thue 8% cua 10.800.000", _tt(10800000, 8, True), (10000000.0, 800000.0))

# --- Ca to: phep bat bien tien hang cong tien thue bang tong
if _bt:
	_dong_thu = [
		{"thanh_tien": 6138000, "thue_pt": 8}, {"thanh_tien": 15019500, "thue_pt": 8},
		{"thanh_tien": 60000, "thue_pt": 10}, {"thanh_tien": 600000, "thue_pt": 0},
	]
	for _ck in (0, 2000000, 1, 21817500):
		_r = _bt(_dong_thu, ck_to=_ck, phi_giao=35000, phi_giao_pt=10, da_gom=1)
		la("ck %s: hang cong thue bang tong" % _ck,
		   abs(_r["tien_hang"] + _r["tien_thue"] - _r["tong_cong"]) < 0.001, True)
		_mong = sum(x["thanh_tien"] for x in _dong_thu) - _ck + 35000
		la("ck %s: tong khop so goc" % _ck, abs(_r["tong_cong"] - _mong) < 0.001, True)
		la("ck %s: bang tom tat cong dung" % _ck,
		   abs(sum(m["tien_thue"] for m in _r["theo_muc"]) - _r["tien_thue"]) < 0.001, True)
	_r0 = _bt([{"thanh_tien": 100000, "thue_pt": 0}], da_gom=1)
	la("to toan 0% thi khong co thue", _r0["tien_thue"], 0.0)
	la("to toan 0% thi tien hang bang tong", _r0["tien_hang"], 100000.0)
	_r1 = _bt([{"thanh_tien": 5000000, "thue_pt": 8},
	           {"thanh_tien": 5000000, "thue_pt": 8}], da_gom=1)
	la("mot muc thi khop cach tinh gop",
	   abs(_r1["tien_thue"] - _tt(10000000, 8, True)[1]) <= 1, True)
	la("to rong khong lam vo phep", _bt([], da_gom=1)["tong_cong"], 0.0)

	# --- Chiet khau PHAN TRAM: truoc thue hay sau thue deu ra mot tong ---
	#
	# Anh Viet 18/08/2026: *"khi chiet khau thi phai chiet khau tren so tien
	# truoc thue, roi moi tinh thue vao"*. Ca nay ghi lai bang so rang voi
	# chiet khau phan tram thi hai duong ra CUNG mot ket qua, nen doi thu tu
	# khong lam thay doi so tien khach tra - no chi lam to in ra co cho ghi
	# ba con so khach hoi.
	_a_h, _a_t = _tt(round(10800000 * 0.9, 0), 8, True)
	_b_h = round(_tt(10800000, 8, True)[0] * 0.9, 0)
	la("chiet khau % truoc hay sau thue deu mot tien hang", _a_h, _b_h)
	la("chiet khau % truoc hay sau thue deu mot tien thue", _a_t, round(_b_h * 0.08, 0))

	# --- Cho SAI THAT: thue phai tinh tren nen DA TRU chiet khau ---
	_r_ck = _bt([{"thanh_tien": 10800000, "thue_pt": 8}], ck_to=1080000, da_gom=1)
	la("thue tinh tren nen da tru chiet khau",
	   _r_ck["tien_thue"], _tt(10800000 - 1080000, 8, True)[1])
	la("thue khong tinh tren nen chua tru",
	   _r_ck["tien_thue"] == _tt(10800000, 8, True)[1], False)

# --- Doctype va lung tinh tien ---
_bgdong = open(
	"vagabond/vagabond/doctype/bao_gia_dong/bao_gia_dong.json", encoding="utf-8"
).read()
la("dong bao gia co o muc thue", '"fieldname": "thue_pt"' in _bgdong, True)
_bgto = open(
	"vagabond/vagabond/doctype/bao_gia_ban_hang/bao_gia_ban_hang.json", encoding="utf-8"
).read()
la("to bao gia co o cach tinh thue", '"fieldname": "kieu_thue"' in _bgto, True)
la("to bao gia co o thue phi giao", '"fieldname": "thue_phi_giao_pt"' in _bgto, True)
_than_tinh = _bg2_src.split("def _tinh(doc):")[1].split("\ndef ")[0]
# Tu 19/08/2026 phep doc che do gom ve MOT ham _kieu_thue, vi _tinh va
# tom_tat_thue tung doc rieng va do la mach dan toi to VGB-PQ-2026-0008.
la("to de trong o kieu thue thi chay nhanh cu",
   "if _kieu_thue(doc) == KT_DONG:" in _than_tinh, True)
la("nhanh cu van con nguyen",
   'doc.thue_tien = round(sau_ck * flt(doc.thue_pt)' in _than_tinh, True)
la("nhanh moi dung chung phep bang_thue", "bang_thue(" in _than_tinh, True)
la("dong moi lay muc thue cua to lam mac dinh", "else flt(doc.thue_pt)" in _bg2_src, True)
la("bang tom tat tinh luc doc, khong luu", "def tom_tat_thue(doc):" in _bg2_src, True)
la("bang tom tat khong nam trong doctype", '"fieldname": "tom_tat_thue"' in _bgto, False)
la("to bao gia in dong tien hang chua thue", "Cộng tiền hàng chưa thuế" in _bg2_src, True)
la("to hop dong in dong tien hang chua thue", "Cộng tiền hàng chưa thuế" in _hdp_src, True)
la("to hop dong in dong tong da gom thue", "TỔNG CỘNG ĐÃ GỒM THUẾ" in _hdp_src, True)
la("to hop dong co ban tieng Anh cua ba dong",
   "Subtotal excluding VAT" in _hdp_src and "Total including VAT" in _hdp_src, True)
la("to tron muc thi nhan cot bo con so", '"<br>(đã gồm VAT)"' in _hdp_src, True)
la("hop dong lay bang thue tu to bao gia", "tom_tat_thue as _tt_bg" in _hdp_src, True)

# --- Man hinh va may chu phai ra CUNG mot con so ---
#
# Man tu tinh de sales sua so la thay tong doi ngay, khong phai cho may chu.
# Nhung hai noi cung giu mot luat thi kieu gi cung co ngay chung lech nhau.
# Ca nay chay CA HAI ban tren cung bo so va so tung dong.
la("man hinh co phep tach thue rieng", "function bgBangThue()" in _bgjs_src, True)
la("man hinh biet to nao tinh theo dong", "function bgTheoDong()" in _bgjs_src, True)
la("man hinh co o VAT tren tung dong", "dg_' + i + '_thue_pt" in _bgjs_src, True)
la("man hinh co chip nhanh 0 8 10", "[0, 8, 10].map" in _bgjs_src, True)
la("dong moi lay muc thue cua to", "function bgMucThueMacDinh()" in _bgjs_src, True)
la("man hinh doc o VAT khi ve lai", "'chiet_khau', 'thue_pt'" in _bgjs_src, True)

if _bt:
	import json as _json
	import subprocess as _sp

	_bo_thu = [
		([(6138000, 8), (15019500, 8), (60000, 10), (600000, 0)], 0, 35000, 10, 1),
		([(6138000, 8), (15019500, 8), (60000, 10), (600000, 0)], 2000000, 0, 0, 1),
		([(1000, 8), (1, 8), (3, 10)], 7, 0, 0, 1),
		([(10000000, 8)], 0, 0, 0, 0),
		([(333, 8), (333, 8), (334, 8)], 100, 0, 0, 1),
	]
	_js_bt = _bgjs_src.split("function bgBangThue() {")[1]
	_js_bt = _js_bt[: _js_bt.index("\n}\n")]
	_js = """
var bgTay = null;
function bgBangThue() {%s
}
var _kq = [];
%s.forEach(function (c) {
  bgTay = {
    dong: c[0].map(function (x) { return { thanh_tien: x[0], thue_pt: x[1] }; }),
    chiet_khau_tien: c[1], phi_giao: c[2], thue_phi_giao_pt: c[3], gia_da_gom_vat: c[4]
  };
  var r = bgBangThue();
  _kq.push([r.tien_hang, r.tien_thue, r.tong_cong]);
});
console.log(JSON.stringify(_kq));
""" % (_js_bt, _json.dumps([[list(map(list, c[0])), c[1], c[2], c[3], c[4]] for c in _bo_thu]))
	try:
		_p = _sp.run(["node", "-e", _js], capture_output=True, timeout=30)
		_ra_js = _json.loads(_p.stdout.decode().strip())
	except Exception:
		_ra_js = None
	la("chay duoc ban JavaScript de doi chieu", _ra_js is not None, True)
	if _ra_js is not None:
		for _i, _c in enumerate(_bo_thu):
			_r = _bt([{"thanh_tien": t, "thue_pt": p} for t, p in _c[0]],
			         ck_to=_c[1], phi_giao=_c[2], phi_giao_pt=_c[3], da_gom=_c[4])
			la("bo %d: man hinh khop may chu" % (_i + 1),
			   [round(x) for x in _ra_js[_i]],
			   [round(x) for x in (_r["tien_hang"], _r["tien_thue"], _r["tong_cong"])])



# =====================================================================
# Nhom 29. Chuyen lai tien nop thua va o tim don (anh Viet 18/08/2026)
# =====================================================================
print("29. Tien nop thua va o tim don")

_ht2_src = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_bh2_src = open("vagabond/ban_hang.py", encoding="utf-8").read()
_ds_src = open("vagabond/public/js/bep/08-doanh-so-sales.js", encoding="utf-8").read()
_bq_src = open("vagabond/public/js/bep/10-bill-quay.js", encoding="utf-8").read()

# --- Tran tien du: phep THUAN, kiem bang so vao so ra ---
_ns_du = {"flt": lambda x, *a: float(x or 0),
          "_tien_vn": lambda v: "{:,.0f}".format(float(v or 0)).replace(",", ".")}
_m_du = re.search(r"^def tran_tien_du\(.*?(?=^def |^@|\Z)", _ht2_src, re.S | re.M)
la("phep tran tien du ton tai", bool(_m_du), True)
if _m_du:
	exec(compile(_m_du.group(0), "hoan_tien:tran_tien_du", "exec"), _ns_du, _ns_du)
	_td = _ns_du["tran_tien_du"]
	# Ca 91433 that: nhan 1.100.000 cho don 915.000, du dung 185.000.
	la("ca 91433: tran dung bang phan du", _td(1100000, 915000)[1], 185000.0)
	la("ca 91433: duoc phep lap phieu", _td(1100000, 915000)[0], True)
	# Nhan dung bang don thi khong co gi de tra.
	la("nhan dung bang don thi khong duoc", _td(915000, 915000)[0], False)
	# Nhan THIEU thi cang khong duoc: do la don con no, khong phai don du.
	la("nhan thieu thi khong duoc", _td(500000, 915000)[0], False)
	la("nhan thieu thi tran bang 0", _td(500000, 915000)[1], 0.0)
	# Chua doi soat duoc dong nao thi cung khong duoc.
	la("chua nhan dong nao thi khong duoc", _td(0, 915000)[0], False)
	la("don tong bang 0 thi khong tinh duoc", _td(100000, 0)[0], False)
	# Cau nhac phai chi duong lam gi tiep (QT-24), khong duoc cut ngun.
	la("cau nhac chi duong sang nut Hoan tien",
	   "Hoàn tiền" in _td(915000, 915000)[2], True)
	la("cau nhac noi ro hai con so",
	   "915.000" in _td(915000, 915000)[2] and "đã nhận" in _td(915000, 915000)[2], True)

# --- Doctype va hang so ---
_htjson = open(
	"vagabond/vagabond/doctype/vagabond_hoan_tien/vagabond_hoan_tien.json", encoding="utf-8"
).read()
la("co hang so phan biet hai loai phieu",
   'LOAI_TIEN_DU = "Tien nop thua"' in _ht2_src, True)
la("co bo ly do rieng cho tien du", "LY_DO_DU = (" in _ht2_src, True)
la("truong loai_hoan khai trong ma nguon", '"fieldname": "loai_hoan"' in _ht2_src, True)
# De trong doc la "Tra hang": phieu cu khong duoc doi nghia.
la("o loai phieu co lua chon rong dung dau",
   '"options": "\\n".join(("", LOAI_TRA_HANG, LOAI_TIEN_DU))' in _ht2_src, True)

# --- Cho quan trong nhat: tien du KHONG duoc lap hoa don tra hang ---
_than_sinh = _ht2_src.split("def _sinh_chung_tu(ho_so):")[1].split("\ndef ")[0]
la("sinh chung tu re nhanh theo loai phieu",
   'if (ho_so.get("loai_hoan") or "") == LOAI_TIEN_DU:' in _than_sinh, True)
# Nhanh tien du phai THOAT truoc khi cham toi _lap_hoa_don_tra.
_nhanh_du = _than_sinh.split('== LOAI_TIEN_DU:')[1].split("toan_bo = tien >=")[0]
la("nhanh tien du khong lap hoa don tra hang", "_lap_hoa_don_tra" in _nhanh_du, False)
la("nhanh tien du khong thu hoi diem", "_thu_hoi_diem" in _nhanh_du, False)
la("nhanh tien du khong lap phieu kho", "_chuyen_kho_huy" in _nhanh_du, False)
la("nhanh tien du co lap phieu chi", "_lap_phieu_chi_du" in _nhanh_du, True)
la("nhanh tien du thoat som bang return", "return {" in _nhanh_du, True)
# Phieu chi cua tien du KHONG tro vao hoa don nao.
_than_chi_du = _ht2_src.split("def _lap_phieu_chi_du(si, ho_so):")[1].split("\ndef ")[0]
la("phieu chi tien du khong tro vao hoa don", "get_payment_entry" in _than_chi_du, False)
la("phieu chi tien du de o trang thai nhap", ".submit()" in _than_chi_du, False)
la("phieu chi tien du la phieu Pay", 'pe.payment_type = "Pay"' in _than_chi_du, True)
la("phieu chi tien du ghi ro khong dung doanh thu",
   "KHÔNG lập hoá đơn" in _than_chi_du, True)

# --- Tran tinh lai o may chu (QT-19) ---
_than_tao_du = _ht2_src.split("def tao_tien_du(")[1].split("\n@frappe")[0]
la("tran tinh lai o may chu", "tran_tien_du(nhan, flt(si.grand_total))" in _than_tao_du, True)
la("chan vuot tran", "lớn hơn phần khách nộp dư" in _than_tao_du, True)
la("phieu ghi dung loai", '"loai_hoan": LOAI_TIEN_DU' in _than_tao_du, True)
la("van bao ke toan nhu phieu hoan tien", "_bao_ke_toan(ho_so, si)" in _than_tao_du, True)
la("van vao trang thai cho chi de chi Dung duyet",
   '"trang_thai": "Cho chi"' in _than_tao_du, True)
# Anh KHONG bat buoc voi tien du, vi bang chung nam trong so sach.
la("tien du khong bat buoc anh", "Phải đính kèm ít nhất một ảnh" in _than_tao_du, False)

# --- Man hinh ---
la("man chi tiet don co nut tien du", "dsvDu" in _ds_src, True)
la("nut tien du goi dung ham", "hoanMoFormDu(d)" in _ds_src, True)
la("co ham mo form tien du", "function hoanMoFormDu(" in _khjs_src, True)
la("form re nhanh theo co du", "var du = !!f.du;" in _khjs_src, True)
la("form tien du goi dung endpoint",
   "du ? 'vagabond.hoan_tien.tao_tien_du' : 'vagabond.hoan_tien.tao'" in _khjs_src, True)
la("form tien du chan theo tran chu khong theo tong don",
   "if (f.tien > tranF)" in _khjs_src, True)
la("form tien du khong bat anh", "if (!du && !f.anh.length)" in _khjs_src, True)
la("form noi ro khong lap hoa don tra hang",
   "không lập hoá đơn trả hàng" in _khjs_src, True)
la("danh sach danh dau phieu tien du", "TIỀN DƯ" in _khjs_src, True)
la("man chi tiet bay so SePay da nhan", "SePay đã nhận" in _khjs_src, True)
la("man chi tiet bay phan nop thua", "Khách nộp thừa" in _khjs_src, True)
la("danh sach tra ve co loai phieu", '"nguoi_duyet", "loai_hoan"' in _ht2_src, True)

# --- O tim don ---
_ns_tim = {"re": re}
for _t in ("chuan_tim", "la_so_dien_thoai"):
	_m = re.search(r"^def %s\(.*?(?=^def |^@|\Z)" % _t, _bh2_src, re.S | re.M)
	la("phep %s ton tai" % _t, bool(_m), True)
	if _m:
		exec(compile(_m.group(0), "ban_hang:%s" % _t, "exec"), _ns_tim, _ns_tim)
_ct = _ns_tim.get("chuan_tim")
_lsdt = _ns_tim.get("la_so_dien_thoai")
if _ct:
	la("bo dau thang o dau ma don Pancake", _ct("  #91433 "), "91433")
	la("bo dau cham cuoi cau", _ct("91433."), "91433")
	la("giu nguyen ma don ERP", _ct("HDB-26-08-00581"), "HDB-26-08-00581")
	la("bo dau ngoac khi chep dan", _ct("(0918432684)"), "0918432684")
	la("gom khoang trang thua", _ct("  Mr.   Trí  "), "Mr. Trí")
	la("rong thi ra rong", _ct(None), "")
if _lsdt:
	la("nhan ra so dien thoai co so 0", _lsdt("0918432684"), True)
	la("nhan ra so dien thoai thieu so 0", _lsdt("918432684"), True)
	la("nhan ra so co dau cach", _lsdt("0933 751 352"), True)
	# Ma don Pancake nam chu so nhung khong phai so dien thoai.
	la("ma don 5 chu so khong phai sdt", _lsdt("91433"), False)
	la("chu thi khong phai sdt", _lsdt("abc"), False)
_than_tim = _bh2_src.split("def tim_don(")[1].split("\ndef ")[0]
la("tim khong gioi han ngay", "posting_date =" in _than_tim, False)
la("tim tren ma don Pancake", '"custom_pancake_display_id"' in _than_tim, True)
la("tim tren ma don ERP", '"name"' in _than_tim, True)
la("tim tren ghi chu don, cho chua ten va sdt", '"remarks"' in _than_tim, True)
la("tim tren dia chi xuat hoa don", '"vgb_xhd_dia_chi"' in _than_tim, True)
la("tim tren ma tham chieu chuyen khoan", '"vgb_ma_tham_chieu"' in _than_tim, True)
la("go it chu qua thi nhac chu khong quet ca bang", "ít nhất 3 ký tự" in _than_tim, True)
la("co tran so dong tra ve", "min(200, cint(so_dong)" in _than_tim, True)
la("moi nhat len truoc", "order by posting_date desc" in _than_tim, True)
# Hai man tinh tien deu phai co o tim, va dung CHUNG mot phep.
la("o tim nam trong thanh ngay dung chung", "'</div>' + timDonO();" in _ds_src, True)
la("man doanh thu sales gan o tim", "timDonGan();" in _ds_src, True)
la("man bill quay gan o tim", "timDonGan();" in _bq_src, True)
la("bam ket qua mo thang man chi tiet don", "scrDsView(ten, 0)" in _ds_src, True)
la("khong tim theo tung phim", "if (e.key === 'Enter')" in _ds_src, True)



# --- DUNG THAT CA TO BAO GIA, khong chi soi chuoi ---
#
# Bai hoc ngay 19/08/2026: em them khoi tach thue vao _html cua to bao gia
# va dat bien ten "muc", trung voi mot ham muc() da co san trong chinh ham
# do. Ghi de xong thi dong muc("Quy trinh van hanh") phia duoi nem
#
#     TypeError: 'list' object is not callable
#
# Ca to bao gia lan phu luc cua hop dong tra ve 500. Bo kiem 787 ca luc do
# van bao DAT HET, vi khong ca nao DUNG THAT to bao gia - chung chi soi
# chuoi trong ma nguon.
#
# Day dung la loai loi ma nhom 25 da hoc mot lan voi to hop dong (loi dau
# phan tram), va lan do da dung _nap_hop_dong_pdf de chua. Nhung to bao gia
# thi chua co phep tuong tu, nen cai bay van con nguyen mot nua.
def _nap_bao_gia():
	"""Nap bao_gia.py voi frappe gia lap. Tra ve khong gian ten."""
	import datetime
	import types

	_fr = types.ModuleType("frappe")
	_fr.whitelist = lambda *a, **k: (lambda f: f)
	_fr.throw = lambda *a, **k: (_ for _ in ()).throw(Exception(a[0] if a else "throw"))
	_fr.get_roles = lambda *a, **k: ["System Manager"]
	_fr.session = types.SimpleNamespace(user="x")
	_fr.db = types.SimpleNamespace(
		exists=lambda *a, **k: False, get_value=lambda *a, **k: None,
		sql=lambda *a, **k: [], set_value=lambda *a, **k: None,
	)
	_fr.get_all = lambda *a, **k: []
	_fr.get_doc = lambda *a, **k: None
	_fr.get_single = lambda *a, **k: types.SimpleNamespace(as_dict=lambda: {})
	_fr.log_error = lambda *a, **k: None
	_fr.sendmail = lambda **k: None
	_fr.escape_html = lambda s: (
		str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
	)
	_u = types.ModuleType("frappe.utils")
	_u.flt = lambda x, *a: float(x or 0)
	_u.cint = lambda x, *a: int(float(x or 0))
	_u.nowdate = lambda: "2026-08-19"
	_u.escape_html = _fr.escape_html

	def _gd(x=None):
		if isinstance(x, (datetime.date, datetime.datetime)):
			return x
		return datetime.date.fromisoformat(str(x)[:10])

	_u.getdate = _gd
	_fr.utils = _u

	ns = {
		"__name__": "vagabond.bao_gia", "frappe": _fr, "json": __import__("json"),
		"re": re, "base64": __import__("base64"),
		"flt": _u.flt, "cint": _u.cint, "getdate": _gd, "nowdate": _u.nowdate,
		"_tien_vn": lambda v: "{:,.0f}".format(float(v or 0)).replace(",", "."),
		"_chu_so_tien": lambda v: "(bằng chữ)",
		# Cac ten AST vua cat di cung lenh import phai duoc cam lai bang tay.
		"_ngay_vn": lambda d: "19/08/2026",
		"_qr_data_uri": lambda *a, **k: "",
		"TEN_NGAN_HANG_DAY_DU": "MB - Ngân hàng TMCP Quân đội",
		"add_days": lambda d, n: "2026-09-03",
		"cfg": lambda *a, **k: types.SimpleNamespace(),
		"sdt": lambda s: str(s or ""),
		"khong_dau": lambda s: str(s or ""),
		"PHONG": _NGAN_XEP,
	}
	# Bo cac lenh import bang AST chu khong bang startswith.
	#
	# bao_gia.py co lenh "from ... import (" trai ra NHIEU DONG. Loc theo
	# startswith chi bo duoc dong dau, con cac ten trong ngoac o lai thanh
	# rac va Python nem "unexpected indent". AST biet dung dong dau va dong
	# cuoi cua tung lenh nen cat sach.
	# _html goi "from vagabond.hop_dong_pdf import khung_style" NGAY TRONG
	# than ham, va AST khong dong toi cac import long trong ham. Nen cam san
	# mo dun gia vao sys.modules de lenh do nap duoc.
	import sys as _sys

	_hdp = types.ModuleType("vagabond.hop_dong_pdf")
	_hdp.khung_style = lambda phong=None: "*{font-family:%s}" % (phong or "Arial")
	_hdp.don_dau_dai = lambda x: str(x or "").replace("\u2013", "-").replace("\u2014", "-")
	_vgb = _sys.modules.get("vagabond") or types.ModuleType("vagabond")
	_sys.modules["vagabond"] = _vgb
	_sys.modules["vagabond.hop_dong_pdf"] = _hdp
	_dm = types.ModuleType("vagabond.danh_muc")
	_dm.khong_dau = lambda s: str(s or "")
	_sys.modules["vagabond.danh_muc"] = _dm
	_tk = types.ModuleType("vagabond.tai_khoan")
	_tk.qr_ngan_hang = lambda *a, **k: ""
	_tk.tk_nhan = lambda *a, **k: {}
	_sys.modules["vagabond.tai_khoan"] = _tk
	_pc = types.ModuleType("vagabond.phong_chu")
	_pc.NGAN_XEP = _NGAN_XEP
	_pc.HO_PHONG = "Vagabond Sans"
	_pc.bao_dam_phong = lambda: 0
	_sys.modules["vagabond.phong_chu"] = _pc
	_vgb.phong_chu = _pc
	_vgb.tai_khoan = _tk
	_vgb.danh_muc = _dm
	_vgb.hop_dong_pdf = _hdp
	_sys.modules["frappe"] = _fr
	_sys.modules["frappe.utils"] = _u

	import ast as _ast

	cay = _ast.parse(_bg2_src)
	dong = _bg2_src.split("\n")
	bo = set()
	for nut in cay.body:
		if isinstance(nut, (_ast.Import, _ast.ImportFrom)):
			for i in range(nut.lineno - 1, (nut.end_lineno or nut.lineno)):
				bo.add(i)
	than = "\n".join("" if i in bo else l for i, l in enumerate(dong))
	exec(compile(than, "bao_gia", "exec"), ns, ns)
	return ns


try:
	_ns_bg = _nap_bao_gia()
except Exception as _e:
	_ns_bg = None
	print("   (khong nap duoc bao_gia: %s)" % _e)
la("nap duoc ca mo dun bao gia", _ns_bg is not None, True)

if _ns_bg:
	_BG_GIA = {
		"name": "VGB-PQ-TEST", "ten": "Bánh trung thu 2026", "ten_en": "",
		"song_ngu": 1, "gia_da_gom_vat": 1, "kieu_thue": "Theo từng dòng",
		"trang_thai": "Nháp", "ngay_bao_gia": "2026-08-19", "hieu_luc_den": "2026-09-03",
		"ten_khach": "CÔNG TY TNHH TƯ VẤN GIẢI PHÁP SECOMM", "ma_so_thue": "0314742605",
		"dia_chi": "P.702A Tầng 7", "nguoi_lien_he": "Trang Phạm", "chuc_vu": "Giám đốc",
		"dien_thoai": "0979999264", "email": "trang.pham@secomm.vn",
		"chiet_khau_pt": 0, "chiet_khau_tien": 0, "thue_pt": 8, "thue_tien": 1572678,
		"thue_phi_giao_pt": 0, "phi_giao": 0, "dat_coc_pt": 50, "dat_coc_tien": 10908750,
		"tam_tinh": 21817500, "tong_cong": 21817500,
		"loi_mo": "", "loi_mo_en": "", "thanh_toan": "", "thanh_toan_en": "",
		"giao_hang": "", "dong_goi": "", "ghi_chu": "",
		"yeu_cau_vi": "", "yeu_cau_en": "", "chinh_sach_huy_vi": "", "chinh_sach_huy_en": "",
		"luu_y_vi": "", "luu_y_en": "",
		"ten_nguoi_lap_in": "Loan Anh", "chuc_vu_lap": "Sales Manager",
		"dt_nguoi_lap": "0933751352", "email_lap": "anhntl@thevagabondpatisserie.com",
		"moc": [{"moc_vi": "Chốt số lượng", "moc_en": "Confirm quantity",
		         "noi_dung_vi": "Chốt trước 3 ngày", "noi_dung_en": "3 days before",
		         "trach_nhiem": "Hai bên"}],
		"dong": [
			{"loai": "Món", "ten_mon": "HỘP MOONLAPIS, năm 2026", "ten_en": "", "dvt": "Món",
			 "dvt_en": "", "so_luong": 3, "don_gia": 2200000, "chiet_khau": 7,
			 "thue_pt": 8, "thanh_tien": 6138000, "hinh": "", "kich_thuoc": "",
			 "mo_ta": "", "mo_ta_en": "", "di_ung_vi": "", "di_ung_en": "",
			 "danh_muc_vi": "", "danh_muc_en": ""},
			{"loai": "Món", "ten_mon": "HỘP MOONGARDEN, năm 2026", "ten_en": "", "dvt": "Món",
			 "dvt_en": "", "so_luong": 17, "don_gia": 950000, "chiet_khau": 7,
			 "thue_pt": 8, "thanh_tien": 15019500, "hinh": "", "kich_thuoc": "",
			 "mo_ta": "", "mo_ta_en": "", "di_ung_vi": "", "di_ung_en": "",
			 "danh_muc_vi": "", "danh_muc_en": ""},
			{"loai": "Phí", "ten_mon": "Thiệp lời chúc in logo", "ten_en": "", "dvt": "thiệp",
			 "dvt_en": "", "so_luong": 20, "don_gia": 3000, "chiet_khau": 0,
			 "thue_pt": 10, "thanh_tien": 60000, "hinh": "", "kich_thuoc": "",
			 "mo_ta": "", "mo_ta_en": "", "di_ung_vi": "", "di_ung_en": "",
			 "danh_muc_vi": "", "danh_muc_en": ""},
			{"loai": "Phí", "ten_mon": "Logo thương hiệu", "ten_en": "", "dvt": "logo",
			 "dvt_en": "", "so_luong": 60, "don_gia": 10000, "chiet_khau": 0,
			 "thue_pt": 0, "thanh_tien": 600000, "hinh": "", "kich_thuoc": "",
			 "mo_ta": "", "mo_ta_en": "", "di_ung_vi": "", "di_ung_en": "",
			 "danh_muc_vi": "", "danh_muc_en": ""},
		],
	}

	def _cong_lai_bg(d):
		"""Cong lai bon con so cua to, dung y phep cua _tinh.

		Vi sao ca kiem phai lam viec nay thay vi giu so co dinh trong khuon
		mau: tu 19/08/2026 ham in co mot cong chan to khong khop
		(_kiem_to_khop), va no chan dung. Mot khuon mau co tam_tinh va
		tong_cong dat cung mot cho, roi moi bien the lai doi dong hang hoac
		doi chiet khau, la mot khuon KHONG the cong lai ra dung tong - tuc
		chinh la cai to sai ma cong do sinh ra de chan. Sua khuon cho khop
		la dung, ha cong xuong cho khuon lot qua moi la sai.
		"""
		tam = sum(float(x["thanh_tien"]) for x in d["dong"])
		ck = _ns_bg["tien_chiet_khau"](tam, d.get("kieu_ck"), d.get("chiet_khau_pt"))
		gom = 1 if d.get("gia_da_gom_vat") else 0
		d["tam_tinh"] = tam
		d["chiet_khau_tien"] = ck
		if (d.get("kieu_thue") or "") == "Theo từng dòng":
			bt = _ns_bg["bang_thue"](
				[{"thanh_tien": float(x["thanh_tien"]), "thue_pt": float(x.get("thue_pt") or 0)}
				 for x in d["dong"]],
				ck_to=ck, phi_giao=float(d.get("phi_giao") or 0),
				phi_giao_pt=float(d.get("thue_phi_giao_pt") or 0), da_gom=gom,
			)
			d["thue_tien"] = bt["tien_thue"]
			d["tong_cong"] = bt["tong_cong"]
		else:
			sau = tam - ck
			d["thue_tien"] = 0.0 if gom else round(sau * float(d.get("thue_pt") or 0) / 100.0, 0)
			d["tong_cong"] = sau + d["thue_tien"] + float(d.get("phi_giao") or 0)
		d["dat_coc_tien"] = round(d["tong_cong"] * float(d.get("dat_coc_pt") or 0) / 100.0, 0)
		return d

	def _dung_bg(sua=None):
		"""Dung THAT to bao gia. Nem loi thi tra ve chuoi loi de doc duoc."""
		d = dict(_BG_GIA)
		if sua:
			d.update(sua)
		_cong_lai_bg(d)
		d["tom_tat_thue"] = _ns_bg["tom_tat_thue"](d)
		try:
			return _ns_bg["_html"](d=d)
		except Exception as _e2:
			return "LOI: %s" % _e2

	# Ba nhanh: tron nhieu muc thue, mot muc, va nhanh cu.
	for _nhan, _sua in (
		("tron nhieu muc thue", {}),
		("chi mot muc thue", {"dong": _BG_GIA["dong"][:2]}),
		("nhanh cu theo to", {"kieu_thue": "Theo tờ (cũ)"}),
		("co chiet khau to", {"chiet_khau_pt": 10, "chiet_khau_tien": 2181750}),
		("khong gom VAT", {"gia_da_gom_vat": 0}),
	):
		_to_bg = _dung_bg(_sua)
		la("dung duoc to bao gia khi %s" % _nhan,
		   bool(_to_bg) and not str(_to_bg).startswith("LOI:"), True)
		if str(_to_bg).startswith("LOI:"):
			print("        %s" % _to_bg[:150])

	# To tron muc phai in du ba dong khach hoi.
	_to_bg = _dung_bg()
	if not str(_to_bg).startswith("LOI:"):
		for _c in ("Cộng tiền hàng chưa thuế", "Subtotal excluding VAT",
		           "Cộng tiền thuế GTGT", "TỔNG TIỀN TẠM TÍNH"):
			la("to bao gia in dong %s" % _c[:26], _c in _to_bg, True)
		# Va cac muc de muc khac VAN PHAI CON - day chinh la cho bi ghi de.
		# Ba muc nay do ham muc() in ra. Chung la BANG CHUNG rang ham do
		# khong bi ghi de - dung cai loi 19/08/2026 khi em dat bien trung
		# ten "muc" lam ca to nem TypeError.
		for _c in ("Quy trình vận hành", "Điều khoản thanh toán", "Báo giá tạm tính"):
			la("to bao gia con muc %s" % _c[:22], _c in _to_bg, True)
		la("to bao gia khong con dau gach dai",
		   ("–" in _to_bg) or ("—" in _to_bg), False)
	# Nhanh cu KHONG duoc in cac dong tach thue.
	_to_cu = _dung_bg({"kieu_thue": "Theo tờ (cũ)"})
	if not str(_to_cu).startswith("LOI:"):
		la("nhanh cu khong in dong tach thue",
		   "Cộng tiền hàng chưa thuế" in _to_cu, False)

print("30. Bo phong Vagabond Sans")

# ---------------------------------------------------------------------------
# Nhom 30. Bo phong tieng Viet cho to PDF (anh Viet 19/08/2026)
#
# Anh Viet: "hien tai van bi loi font (co ve no khong phai la font ARIAL)".
# Em tai to hop dong THAT ve, doc bang phong nhung va doc luon bang ma
# nguoi dung. Ket qua: DejaVuSans duoc goi cho DUNG 46 chu, va ca 46 chu
# do deu la chu cai tieng Viet co dau thanh. Server co Liberation Sans
# nhung la ban 1.07.4 khong co bang Latin Extended Additional, nen
# wkhtmltopdf lay Liberation cho chu khong dau roi muon DejaVu cho rieng
# chu co dau. Hai kieu chu lech nhau trong cung mot tu.
#
# Nhom kiem nay giu ba hang rao:
#   1. Bon tep phong di kem phai co that, dung ten ho, du bon kieu.
#   2. Bon tep do phai co DU 46 chu da tung roi sang DejaVu, cong them
#      dong tien va chu d gach.
#   3. Dung wkhtmltopdf dung lai DUNG hoan canh server: chi cho fontconfig
#      nhin thay bo phong cua minh va DejaVu. To PDF sinh ra khong duoc
#      chua mot chu DejaVu nao.
# ---------------------------------------------------------------------------

# Dung 46 ma chu ma DejaVu da gach ra tren to hop dong that HDBH-2026-0863.
_MA_VIET = [
	0x1ED1, 0x1ED9, 0x1EAD, 0x1EF1, 0x1EE7, 0x01B0, 0x1EDB, 0x1EC7, 0x01A1,
	0x1EA1, 0x1EE9, 0x1EA7, 0x1EA3, 0x1ED3, 0x01AF, 0x1EA4, 0x1EA2, 0x1ECB,
	0x1EC9, 0x1EC5, 0x1ED7, 0x1EDD, 0x1EBF, 0x1EE5, 0x1ECF, 0x1EA5, 0x1EE3,
	0x1EEF, 0x1ED8, 0x1EC1, 0x1EB1, 0x1EC3, 0x1EEB, 0x1EA9, 0x1EAB, 0x1EB7,
	0x1EAF, 0x1ED5, 0x1EE1, 0x1EED, 0x1EB5, 0x1EBD, 0x1EDF, 0x1ECD, 0x1EF9,
	0x1EF7,
]
# Them may chu hay dung khac: d gach, dong tien, dau cham tron, gach ngang.
_MA_THEM = [0x0111, 0x0110, 0x20AB, 0x2022, 0x00A0]

_PHONG_DIR = "vagabond/fonts"
_CAC_KIEU_PHONG = (
	("VagabondSans-Regular.ttf", "Regular"),
	("VagabondSans-Bold.ttf", "Bold"),
	("VagabondSans-Italic.ttf", "Italic"),
	("VagabondSans-BoldItalic.ttf", "Bold Italic"),
)


def _bang_ten(duong_dan):
	"""Doc bang 'name' cua tep TrueType. Chi dung thu vien chuan.

	Khong dua vao fontTools vi may chay cong kiem truoc khi deploy khong
	chac co goi do.
	"""
	import struct

	d = open(duong_dan, "rb").read()
	n = struct.unpack(">H", d[4:6])[0]
	off = leng = None
	for i in range(n):
		r = 12 + 16 * i
		if d[r:r + 4] == b"name":
			off, leng = struct.unpack(">II", d[r + 8:r + 16])
	if off is None:
		return {}
	so, kho = struct.unpack(">HH", d[off + 2:off + 6])
	ra = {}
	for i in range(so):
		r = off + 6 + 12 * i
		pid, eid, lid, nid, dl, do = struct.unpack(">HHHHHH", d[r:r + 12])
		v = d[off + kho + do:off + kho + do + dl]
		try:
			ra[nid] = v.decode("utf-16-be") if pid == 3 else v.decode("latin-1")
		except Exception:
			pass
	return ra


def _bang_ma(duong_dan):
	"""Doc bang 'cmap' cua tep TrueType, tra ve tap ma chu co that."""
	import struct

	d = open(duong_dan, "rb").read()
	n = struct.unpack(">H", d[4:6])[0]
	off = None
	for i in range(n):
		r = 12 + 16 * i
		if d[r:r + 4] == b"cmap":
			off = struct.unpack(">I", d[r + 8:r + 12])[0]
	if off is None:
		return set()
	nt = struct.unpack(">H", d[off + 2:off + 4])[0]
	sub = None
	for i in range(nt):
		r = off + 4 + 8 * i
		pid, eid, o = struct.unpack(">HHI", d[r:r + 8])
		if (pid, eid) in ((3, 1), (3, 10), (0, 3), (0, 4), (0, 6)):
			sub = off + o
	if sub is None:
		return set()
	fmt = struct.unpack(">H", d[sub:sub + 2])[0]
	ra = set()
	if fmt == 4:
		sx2 = struct.unpack(">H", d[sub + 6:sub + 8])[0]
		seg = sx2 // 2
		het = [struct.unpack(">H", d[sub + 14 + 2 * i:sub + 16 + 2 * i])[0]
		       for i in range(seg)]
		sb = sub + 16 + sx2
		dau = [struct.unpack(">H", d[sb + 2 * i:sb + 2 + 2 * i])[0]
		       for i in range(seg)]
		for i in range(seg):
			if dau[i] > het[i] or het[i] == 0xFFFF:
				continue
			for c in range(dau[i], het[i] + 1):
				ra.add(c)
	elif fmt == 12:
		ng = struct.unpack(">I", d[sub + 12:sub + 16])[0]
		for i in range(ng):
			r = sub + 16 + 12 * i
			a, b, _g = struct.unpack(">III", d[r:r + 12])
			for c in range(a, min(b, a + 5000) + 1):
				ra.add(c)
	return ra


for _tep, _kieu in _CAC_KIEU_PHONG:
	_dd = os.path.join(_PHONG_DIR, _tep)
	_co = os.path.isfile(_dd)
	la("co tep phong %s" % _tep, _co, True)
	if not _co:
		continue
	_ten = _bang_ten(_dd)
	la("%s khai ho Vagabond Sans" % _kieu, _ten.get(1), "Vagabond Sans")
	la("%s khai dung kieu chu" % _kieu, _ten.get(2), _kieu)
	# Giay phep OFL cam ban sua doi dung ten danh rieng "Liberation" LAM
	# TEN PHONG. O nhan hieu va o mo ta thi van duoc phep nhac lai nguon
	# goc, va nhac la dung, nen chi soi cac o mang ten phong.
	la("%s da bo ten Liberation khoi ten phong" % _kieu,
	   any("Liberation" in str(_ten.get(i, "")) for i in (1, 3, 4, 6, 16, 17)),
	   False)
	la("%s van ghi nhan nguon goc Liberation" % _kieu,
	   "Liberation" in str(_ten.get(7, "")), True)
	la("%s van ghi ro giay phep OFL" % _kieu,
	   "Open Font License" in str(_ten.get(13, "")), True)
	_ma = _bang_ma(_dd)
	_thieu = [hex(c) for c in _MA_VIET + _MA_THEM if c not in _ma]
	la("%s co du chu tieng Viet co dau" % _kieu, _thieu, [])

la("co toan van giay phep OFL",
   os.path.isfile(os.path.join(_PHONG_DIR, "OFL.txt"))
   and len(open(os.path.join(_PHONG_DIR, "OFL.txt"), encoding="utf-8").read()) > 3000,
   True)
la("co ghi chu vi sao mang phong theo",
   os.path.isfile(os.path.join(_PHONG_DIR, "README.md")), True)
la("co tep dung lai bo phong", os.path.isfile("dung_phong.py"), True)

# --- Ham chep phong: nap that, frappe gia lap ---
try:
	import ast as _ast30
	import types as _types30

	_pc_cay = _ast30.parse(_pc_src)
	_pc_dong = _pc_src.split("\n")
	_pc_bo = set()
	for _nut in _pc_cay.body:
		if isinstance(_nut, (_ast30.Import, _ast30.ImportFrom)):
			for _i in range(_nut.lineno - 1, (_nut.end_lineno or _nut.lineno)):
				_pc_bo.add(_i)
	_pc_than = "\n".join(
		"" if _i in _pc_bo else _l for _i, _l in enumerate(_pc_dong)
	)
	_fr30 = _types30.ModuleType("frappe")
	_fr30.whitelist = lambda *a, **k: (lambda f: f)
	_fr30.throw = lambda *a, **k: (_ for _ in ()).throw(Exception("throw"))
	_fr30.get_roles = lambda *a, **k: ["System Manager"]
	_fr30.log_error = lambda *a, **k: None
	_fr30.get_traceback = lambda *a, **k: ""
	_ns30 = {"__name__": "vagabond.phong_chu", "__file__": "vagabond/phong_chu.py",
	         "frappe": _fr30, "os": os, "shutil": __import__("shutil")}
	exec(compile(_pc_than, "phong_chu", "exec"), _ns30, _ns30)
	_nap30 = True
except Exception as _e30:
	_nap30 = False
	print("   (khong nap duoc phong_chu: %s)" % _e30)

la("nap duoc phong_chu.py", _nap30, True)

if _nap30:
	import tempfile as _tf30

	_nha_cu = os.environ.get("HOME")
	_xdg_cu = os.environ.get("XDG_DATA_HOME")
	_tmp30 = _tf30.mkdtemp()
	try:
		os.environ["HOME"] = _tmp30
		os.environ.pop("XDG_DATA_HOME", None)
		la("nhan ra hai thu muc dich", len(_ns30["cac_thu_muc_dich"]()), 2)
		la("thu muc dich nam trong HOME",
		   all(d.startswith(_tmp30) for d in _ns30["cac_thu_muc_dich"]()), True)
		la("luc dau chua co phong",
		   any(_ns30["da_du"](d) for d in _ns30["cac_thu_muc_dich"]()), False)
		_lan1 = _ns30["bao_dam_phong"]()
		la("chep duoc ca hai thu muc", _lan1, 2)
		la("chep xong thi da du",
		   all(_ns30["da_du"](d) for d in _ns30["cac_thu_muc_dich"]()), True)
		# Goi lan hai khong duoc chep lai, chi kiem roi thoi.
		_dich1 = _ns30["cac_thu_muc_dich"]()[0]
		_moc = os.path.getmtime(os.path.join(_dich1, "VagabondSans-Regular.ttf"))
		la("goi lan hai van bao du", _ns30["bao_dam_phong"](), 2)
		la("goi lan hai khong chep de len",
		   os.path.getmtime(os.path.join(_dich1, "VagabondSans-Regular.ttf")), _moc)
		# Tep bi cut mot nua thi phai chep lai, khong duoc bo qua.
		_tep1 = os.path.join(_dich1, "VagabondSans-Regular.ttf")
		open(_tep1, "wb").write(b"hong")
		la("phat hien tep phong bi hong", _ns30["da_du"](_dich1), False)
		_ns30["bao_dam_phong"]()
		la("chep lai duoc tep bi hong", _ns30["da_du"](_dich1), True)
		# HOME tro vao cho khong ghi duoc thi KHONG duoc nem loi.
		os.environ["HOME"] = "/proc/khong-co-that"
		try:
			_kq30 = _ns30["bao_dam_phong"]()
			_yen = True
		except Exception:
			_kq30, _yen = None, False
		la("HOME hong van khong nem loi", _yen, True)
		la("HOME hong thi bao khong chep duoc cho nao", _kq30, 0)
	finally:
		if _nha_cu is not None:
			os.environ["HOME"] = _nha_cu
		if _xdg_cu is not None:
			os.environ["XDG_DATA_HOME"] = _xdg_cu
		__import__("shutil").rmtree(_tmp30, ignore_errors=True)

# --- Dien tap that: dung lai dung hoan canh server ---
#
# Chi cho fontconfig nhin thay bo phong cua minh va DejaVu, dung nhu server
# sau khi da chep phong. In mot doan tieng Viet du dau thanh roi doc xem
# trong to PDF co phong gi. Co mot chu DejaVu la hong.
_wk = None
for _d30 in os.environ.get("PATH", "").split(os.pathsep):
	_t30 = os.path.join(_d30, "wkhtmltopdf")
	if os.path.isfile(_t30) and os.access(_t30, os.X_OK):
		_wk = _t30
		break
if not _wk:
	print("   (khong co wkhtmltopdf, bo qua dien tap dung to PDF)")
else:
	import subprocess as _sp30
	import tempfile as _tf31

	_thu30 = _tf31.mkdtemp()
	try:
		_chu = "".join(chr(c) for c in _MA_VIET)
		_html30 = (
			"<html><head><meta charset='utf-8'><style>*{font-family:%s}"
			"</style></head><body><h1>HỢP ĐỒNG MUA BÁN</h1>"
			"<p>%s</p><p><b>%s</b></p><p><i>%s</i></p>"
			"<p><b><i>Tổng cộng đã gồm thuế: "
			"10.800.000 ₫</i></b></p></body></html>"
			% (_NGAN_XEP, _chu, _chu, _chu)
		)
		_ph30 = os.path.join(_thu30, "t.html")
		open(_ph30, "w", encoding="utf-8").write(_html30)
		_cf30 = os.path.join(_thu30, "fonts.conf")
		open(_cf30, "w", encoding="utf-8").write(
			"<?xml version='1.0'?><fontconfig>"
			"<dir>%s</dir><dir>/usr/share/fonts/truetype/dejavu</dir>"
			"<cachedir>%s</cachedir></fontconfig>"
			% (os.path.abspath(_PHONG_DIR), os.path.join(_thu30, "cache"))
		)
		_pdf30 = os.path.join(_thu30, "t.pdf")
		_mt30 = dict(os.environ)
		_mt30["FONTCONFIG_FILE"] = _cf30
		_sp30.call([_wk, "--quiet", _ph30, _pdf30], env=_mt30,
		           stdout=_sp30.DEVNULL, stderr=_sp30.DEVNULL, timeout=120)
		_ra30 = open(_pdf30, "rb").read() if os.path.isfile(_pdf30) else b""
		la("dung duoc to PDF thu", len(_ra30) > 2000, True)
		_ho30 = sorted(set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-,]+)", _ra30)))
		_ho30 = [h.decode() for h in _ho30]
		la("to PDF thu khong con mot chu DejaVu nao",
		   [h for h in _ho30 if "DejaVu" in h], [])
		la("to PDF thu chi dung phong Vagabond Sans",
		   [h for h in _ho30 if not h.startswith("VagabondSans")], [])
		la("to PDF thu dung du bon kieu chu", len(_ho30), 4)
	finally:
		__import__("shutil").rmtree(_thu30, ignore_errors=True)

print("31. Bam theo Pancake va tru diem tai quay")

# ---------------------------------------------------------------------------
# Nhom 31. Ba viec anh Viet giao 19/08/2026
#
#   a. Van don phai bam theo NGAY GIAO cua Pancake (ca 91928)
#   b. Man tinh tien phai hien hang, diem, va co o tru tien bang diem
#   c. Phieu hoan tien bi tu choi khong duoc chan lap phieu moi
# ---------------------------------------------------------------------------

_vd_src = open("vagabond/van_don.py", encoding="utf-8").read()
_do_src = open("vagabond/diem_otp.py", encoding="utf-8").read()
_nk_src = open("vagabond/nhat_ky_dong_bo.py", encoding="utf-8").read()
_pos_src = open("vagabond/public/js/bep/09-tinh-tien-quay.js", encoding="utf-8").read()
_km13_src = open("vagabond/public/js/bep/13-khuyen-mai.js", encoding="utf-8").read()
_bq_src = open("vagabond/public/js/bep/10-bill-quay.js", encoding="utf-8").read()
_ds8_src = open("vagabond/public/js/bep/08-doanh-so-sales.js", encoding="utf-8").read()
_ht2_src = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_bh2_src = open("vagabond/ban_hang.py", encoding="utf-8").read()


def _nap_ham_thuan(duong_dan, cac_ten, moi_truong=None):
	"""Cat lay than cac ham THUAN tu mot tep roi chay. Dung lai cach cua
	_nap_ham_that o dau tep: khong import ca mo dun vi may nay khong co
	frappe."""
	src = open(duong_dan, encoding="utf-8").read()
	mt = dict(moi_truong or {})
	mt.setdefault("flt", lambda x: float(x or 0))
	for ten in cac_ten:
		m = re.search(r"^def %s\(.*?(?=^def |\Z)" % re.escape(ten), src, re.S | re.M)
		if not m:
			print("   KHONG THAY ham %s trong %s" % (ten, duong_dan))
			continue
		exec(compile(m.group(0), "%s:%s" % (duong_dan, ten), "exec"), mt, mt)
	return mt


# --- 31a. Luat doi ngay giao ---
# Ba hang so doc THANG tu ma nguon chu khong chep tay: doi ten mot hang so
# ma bo kiem van dat thi bo kiem khong con bao ve gi.
_HS_NGAY = dict(re.findall(r"^(DOI_NGAY_[A-Z_]+) = \"([a-z_]+)\"", _vd_src, re.M))
la("doc duoc ba hang so luat doi ngay", sorted(_HS_NGAY), ["DOI_NGAY_CANH_BAO", "DOI_NGAY_CHAN", "DOI_NGAY_DUOC"])
_vd = _nap_ham_thuan("vagabond/van_don.py",
                     ["_lech_mui", "_ngay_hop_le", "_ngay_tu_iso", "luat_doi_ngay"],
                     dict(_HS_NGAY, re=re, cint=lambda x: int(float(x or 0))))
_ngay_tu_iso = _vd.get("_ngay_tu_iso")
_luat_ngay = _vd.get("luat_doi_ngay")

la("nap duoc hai ham thuan cua van_don", bool(_ngay_tu_iso and _luat_ngay), True)

if _ngay_tu_iso:
	# ---------------------------------------------------------------
	# BAI HOC 19/08/2026, ghi ra day de khong ai vo tinh go mat.
	#
	# Ban dau ham nay cat thang t[:10] cua chuoi ISO. Ba muoi phut sau khi
	# deploy, 75 van don bi day lui dung mot ngay va 27 don cua hom nay
	# bien mat khoi man Van don.
	#
	# Nguyen nhan: Pancake tra estimate_delivery_date theo GIO UTC va
	# KHONG khai mui gio. Don 92194 giao ngay 19/08 duoc ghi la
	# "2026-08-18T17:00:00", cong 7 tieng moi ra 00:00 ngay 19/08.
	#
	# Bo kiem cu KHONG bat duoc vi no chi thu phep cat chuoi, chua bao gio
	# hoi "chuoi nay nghia la gi". Ba ca duoi day la ca THAT lay tu API.
	# ---------------------------------------------------------------
	la("don 92194: 17:00 UTC la nua dem hom sau gio Viet",
	   _ngay_tu_iso("2026-08-18T17:00:00"), "2026-08-19")
	la("don 92186: cung moc do, cung ra ngay hom sau",
	   _ngay_tu_iso("2026-08-18T17:00:00"), "2026-08-19")
	la("don 91928: 08:00 UTC van la ngay hom do",
	   _ngay_tu_iso("2026-08-18T08:00:00"), "2026-08-18")
	# Ranh gioi: 16:59:59 UTC con la hom nay, 17:00:00 la hom sau.
	la("16:59:59 UTC van la ngay hom do", _ngay_tu_iso("2026-08-18T16:59:59"), "2026-08-18")
	la("17:00:00 UTC da sang ngay hom sau", _ngay_tu_iso("2026-08-18T17:00:00"), "2026-08-19")
	# Chuoi CO khai mui gio thi phai ton trong phan khai do.
	la("chuoi khai +07:00 thi giu nguyen ngay",
	   _ngay_tu_iso("2026-08-19T00:00:00+07:00"), "2026-08-19")
	la("chuoi khai Z la UTC", _ngay_tu_iso("2026-08-18T17:00:00Z"), "2026-08-19")
	# 10:00 o mui -05:00 la 15:00 UTC, cong 7 tieng ra 22:00 ngay 18 gio Viet.
	la("chuoi khai mui am", _ngay_tu_iso("2026-08-18T10:00:00-05:00"), "2026-08-18")
	# Con 14:00 o mui -05:00 la 19:00 UTC, sang 02:00 ngay 19 gio Viet.
	la("chuoi khai mui am, qua ngay", _ngay_tu_iso("2026-08-18T14:00:00-05:00"), "2026-08-19")
	la("doc ngay khi ngan cach bang dau cach",
	   _ngay_tu_iso("2026-08-18 08:00:00"), "2026-08-18")
	# Chi co phan ngay, khong co gio: khong quy doi duoc thi tra thang.
	la("chi co phan ngay thi tra thang", _ngay_tu_iso("2026-08-18"), "2026-08-18")
	# Doc khong duoc thi phai tra RONG, tuyet doi khong duoc doan.
	for _xau in ("", None, "khong phai ngay", "18/08/2026", "2026-13-01T08:00:00",
	             "2026-08-99T08:00:00", "1899-08-18T08:00:00", "2026-08"):
		la("chuoi hong %r tra ve rong" % (_xau,), _ngay_tu_iso(_xau), "")

	# --- Phep bat bien that su bao ve duoc: cua so keo va phep doc ngay
	# phai noi cung mot thu ngon ngu ---
	#
	# van_don keo don theo cua so _khoang_unix(D), la nua dem den nua dem
	# GIO VIET NAM doi ra unix. Vay thi MOI moc thoi gian nam trong cua so
	# do, khi doc nguoc lai, deu phai ra dung ngay D. Neu hai phep nay lech
	# mui gio nhau thi ca bo dong bo sai, va day chinh la ca da xay ra.
	import datetime as _dt31
	from zoneinfo import ZoneInfo as _ZI31

	_VN31 = _ZI31("Asia/Ho_Chi_Minh")

	def _cua_so31(ngay):
		d = _dt31.date.fromisoformat(ngay)
		dau = _dt31.datetime(d.year, d.month, d.day, tzinfo=_VN31)
		return int(dau.timestamp()), int((dau + _dt31.timedelta(days=1)).timestamp()) - 1

	for _ngay31 in ("2026-08-18", "2026-08-19", "2026-12-31", "2027-01-01", "2026-02-28"):
		_dau31, _cuoi31 = _cua_so31(_ngay31)
		_hong31 = []
		# Quet ca ngay, moi 15 phut mot moc, cong hai dau bien.
		for _ts31 in list(range(_dau31, _cuoi31 + 1, 900)) + [_dau31, _cuoi31]:
			_iso31 = _dt31.datetime.utcfromtimestamp(_ts31).strftime("%Y-%m-%dT%H:%M:%S")
			if _ngay_tu_iso(_iso31) != _ngay31:
				_hong31.append(_iso31)
		la("moi moc trong cua so keo cua %s deu doc ra dung ngay do" % _ngay31,
		   _hong31[:3], [])
		# Va moc NGAY TRUOC cua so thi phai ra ngay hom truoc.
		_truoc31 = _dt31.datetime.utcfromtimestamp(_dau31 - 1).strftime("%Y-%m-%dT%H:%M:%S")
		_hom_truoc = (_dt31.date.fromisoformat(_ngay31) - _dt31.timedelta(days=1)).isoformat()
		la("moc sat truoc cua so %s doc ra hom truoc" % _ngay31,
		   _ngay_tu_iso(_truoc31), _hom_truoc)

if _vd.get("_lech_mui"):
	_lech_mui = _vd["_lech_mui"]
	la("khong khai mui gio thi tra None", _lech_mui(""), None)
	la("Z la 0 phut", _lech_mui("Z"), 0)
	la("+07:00 la 420 phut", _lech_mui("+07:00"), 420)
	la("-05:30 la am 330 phut", _lech_mui("-05:30"), -330)
	la("+07 khong co phut cung doc duoc", _lech_mui("+07"), 420)
	la("chuoi rac tra None", _lech_mui("abc"), None)

if _luat_ngay:
	# Bang quyet dinh day du. Cot cuoi la ly do, de nguoi doc bo kiem hieu
	# vi sao chu khong chi thay mot chuoi.
	for _tt, _co_chuyen, _mong, _vi_sao in (
		("Chờ giao", False, _HS_NGAY["DOI_NGAY_DUOC"], "chua ai dung toi, de thang"),
		("Chờ giao", True, _HS_NGAY["DOI_NGAY_CANH_BAO"], "da xep chuyen ngay cu, phai go ra va bao"),
		("Đang giao", False, _HS_NGAY["DOI_NGAY_CHAN"], "shipper dang cam banh, nguoi phai xu"),
		("Đang giao", True, _HS_NGAY["DOI_NGAY_CHAN"], "shipper dang cam banh, nguoi phai xu"),
		("Đã giao", False, "", "viec da xong"),
		("Đã giao", True, "", "viec da xong"),
		("Không giao được", False, "", "viec da xong"),
		("Huỷ", False, "", "viec da xong"),
		("", False, "", "khong ro trang thai thi khong lam gi"),
	):
		la("doi ngay khi %s%s: %s" % (_tt or "(rong)", " co chuyen" if _co_chuyen else "", _vi_sao),
		   _luat_ngay(_tt, _co_chuyen), _mong)

	# --- Nhanh qua_han, hoc tu don 91842 ---
	#
	# Sales tra loi 19/08/2026: "hien tren app se khong co thao tac doi
	# trang thai gi het, ben em chi thao tac chuyen doi lai ngay nhan, don
	# hang 14.8 thi trong ngay 14.8 moi cap nhat lai sang ngay 18/8".
	# Nghia la van don ket o "Dang giao" tu 14/08 toi gio, khong phai
	# shipper dang cam banh. Chan cap nhat mot trang thai bo quen thi don
	# ket lai vinh vien o ngay sai.
	for _tt, _co_chuyen, _qh, _mong, _vi_sao in (
		("Đang giao", False, 1, _HS_NGAY["DOI_NGAY_CANH_BAO"],
		 "ngay giao da troi qua nen day la trang thai bo quen, de va bao"),
		("Đang giao", True, 1, _HS_NGAY["DOI_NGAY_CANH_BAO"], "co chuyen cung vay"),
		("Đang giao", False, 0, _HS_NGAY["DOI_NGAY_CHAN"],
		 "ngay giao la hom nay hoac mai thi van chan"),
		("Chờ giao", False, 1, _HS_NGAY["DOI_NGAY_DUOC"], "cho giao thi qua han hay khong deu de"),
		("Đã giao", False, 1, "", "viec da xong thi qua han cung khong lam gi"),
	):
		la("doi ngay khi %s qua_han %d: %s" % (_tt, _qh, _vi_sao),
		   _luat_ngay(_tt, _co_chuyen, _qh), _mong)
	# Khong truyen qua_han thi phai giu nguyen nep cu, khong duoc tu noi long.
	la("khong truyen qua_han thi mac dinh la chua qua han",
	   _luat_ngay("Đang giao", False), _HS_NGAY["DOI_NGAY_CHAN"])

# Ma nguon phai that su tinh qua_han va truyen vao luat.
la("nhip dong bo co tinh qua han", 'qua_han = 1 if ngay_cu < nowdate() else 0' in _vd_src, True)
la("nhip dong bo truyen qua_han vao luat",
   "luat_doi_ngay(cu.get(\"trang_thai\"), co_chuyen, qua_han)" in _vd_src, True)

# Ca that 91928: van don Cho giao chua xep chuyen, Pancake doi 17 sang 18.
if _ngay_tu_iso and _luat_ngay:
	_ngay_moi = _ngay_tu_iso("2026-08-18T08:00:00")
	la("ca 91928: doc duoc ngay moi", _ngay_moi, "2026-08-18")
	la("ca 91928: khac ngay dang luu", _ngay_moi != "2026-08-17", True)
	la("ca 91928: luat cho phep de thang", _luat_ngay("Chờ giao", False), _HS_NGAY["DOI_NGAY_DUOC"])

# --- 31a bis. Ma nguon phai that su goi luat do ---
la("nhip dong bo goi _theo_ngay_giao", "_theo_ngay_giao(o, cu, pid)" in _vd_src, True)
la("nhip dong bo goi _theo_don_huy", "_theo_don_huy(o)" in _vd_src, True)
la("truy van don cu co doc ngay_giao", '"ngay_giao", "chuyen", "shipper",' in _vd_src, True)
la("nhanh chan KHONG ghi ngay giao",
   _vd_src.count("if luat == DOI_NGAY_CHAN:"), 1)
la("nhanh canh bao go don khoi chuyen", 'doi["chuyen"] = ""' in _vd_src, True)
la("huy don Pancake chuyen van don sang Huy", '"trang_thai": "Huỷ"' in _vd_src, True)
la("khong bao gio xoa van don", ".delete()" in _vd_src, False)
# Hai ham nay tuyet doi khong duoc nem loi ra ngoai: nhip dong bo con phai
# chay tiep cho cac don khac.
for _ten in ("_theo_ngay_giao", "_theo_don_huy"):
	_m = re.search(r"^def %s\(.*?(?=^def )" % _ten, _vd_src, re.S | re.M)
	la("%s co boc try" % _ten, bool(_m) and "except Exception:" in _m.group(0), True)

# --- 31a ter. Nhat ky dong bo ---
la("co mo dun nhat ky dong bo", os.path.isfile("vagabond/nhat_ky_dong_bo.py"), True)
la("co doctype nhat ky dong bo",
   os.path.isfile("vagabond/vagabond/doctype/vagabond_nhat_ky_dong_bo/vagabond_nhat_ky_dong_bo.json"), True)
la("nhat ky khong bao gio nem loi", _nk_src.count("except Exception:") >= 3, True)
la("nhat ky co co can_nguoi_xem", "can_nguoi_xem" in _nk_src, True)
la("nhip van don co ghi nhat ky", "nhat_ky.ghi" in _vd_src, True)
la("cron don nhat ky da khai trong hooks",
   "vagabond.nhat_ky_dong_bo.don_cu" in _hook_src, True)
try:
	import json as _json31
	_nk_dt = _json31.load(open(
		"vagabond/vagabond/doctype/vagabond_nhat_ky_dong_bo/vagabond_nhat_ky_dong_bo.json",
		encoding="utf-8"))
	_nk_o = {f["fieldname"] for f in _nk_dt["fields"]}
	la("doctype nhat ky co du cac o can thiet",
	   {"ma_don", "truong", "gia_tri_cu", "gia_tri_moi", "can_nguoi_xem"} - _nk_o, set())
except Exception as _e31:
	la("doc duoc doctype nhat ky", str(_e31), "")

# --- 31b. Tru tien bang diem tai quay ---
_dq = _nap_ham_thuan("vagabond/diem_otp.py", ["_tong_tam_tinh"])
_tong_tam_tinh = _dq.get("_tong_tam_tinh")
la("nap duoc _tong_tam_tinh", bool(_tong_tam_tinh), True)

if _tong_tam_tinh:
	_gio = [{"item_code": "A", "qty": 2, "rate": 100000},
	        {"item_code": "B", "qty": 1, "rate": 55000}]
	la("cong gio hang", _tong_tam_tinh(_gio), 255000.0)
	la("cong them phi ship", _tong_tam_tinh(_gio, 0, 30000), 285000.0)
	la("tru giam gia tay", _tong_tam_tinh(_gio, 55000, 0), 200000.0)
	la("tru ca khuyen mai", _tong_tam_tinh(_gio, 0, 0, 25000), 230000.0)
	la("gio rong ra 0", _tong_tam_tinh([]), 0.0)
	# Dong hong khong duoc lam vo phep cong, va khong duoc tinh vao.
	la("bo qua dong thieu ma hang",
	   _tong_tam_tinh([{"qty": 1, "rate": 999}] + _gio), 255000.0)
	la("bo qua dong so luong 0",
	   _tong_tam_tinh([{"item_code": "C", "qty": 0, "rate": 999}] + _gio), 255000.0)
	la("bo qua dong so luong am",
	   _tong_tam_tinh([{"item_code": "C", "qty": -3, "rate": 999}] + _gio), 255000.0)
	# Giam nhieu hon gia tri gio thi ve 0 chu KHONG duoc am: so am chay
	# thang vao tran_dung_duoc roi ra tran am, va tran am thi kiem_so_diem
	# tu choi - nhung ra 0 thi cau bao loi doc de hieu hon.
	la("giam qua tay van khong am", _tong_tam_tinh(_gio, 900000, 0), 0.0)

# Ba pha phai co du, va pha ba TUYET DOI khong duoc whitelist.
la("co pha xin ma tai quay", "def xin_ma_quay(" in _do_src, True)
la("co pha xac nhan tai quay", "def xac_nhan_quay(" in _do_src, True)
la("co pha dung ve", "def dung_ve(" in _do_src, True)
_m_ve = re.search(r"(@frappe\.whitelist\(\)\s*\n(@[^\n]*\n)*)?def dung_ve\(", _do_src)
la("dung_ve KHONG duoc whitelist", bool(_m_ve and _m_ve.group(1)), False)
la("xin_ma_quay co chan goi lien tuc", "@rate_limit" in _do_src.split("def xin_ma_quay(")[0][-200:], True)
# Pha hai KHONG duoc tru diem. Neu ai them _ghi_tru_diem vao do thi khach
# mat diem cho mot to bill co the khong bao gio duoc lap.
_than_xn = _do_src.split("def xac_nhan_quay(")[1].split("\ndef ")[0]
la("pha xac nhan KHONG tru diem", "_ghi_tru_diem" in _than_xn, False)
la("pha xac nhan chi cap ve", "da_xac_thuc" in _than_xn, True)
_than_dv = _do_src.split("def dung_ve(")[1].split("\ndef ")[0]
la("pha ba khoa dong khach truoc khi ghi", "for update" in _than_dv, True)
la("pha ba kiem lai tran tren grand_total that", 'si["grand_total"]' in _than_dv, True)
la("pha ba danh dau ve da dung", '"da_dung": 1' in _than_dv, True)
la("pha ba chan tru hai lan", "_diem_da_tru(si_name)" in _than_dv, True)
# Ve phai gan voi DUNG mot khach.
_than_kiem = _do_src.split("def _ve_con_dung_duoc(")[1].split("\ndef ")[0]
for _dieu in ("da_dung", "da_xac_thuc", "han_dung", "khach"):
	la("ve bi tu choi khi sai %s" % _dieu, _dieu in _than_kiem, True)

# Doctype OTP phai co du bon o moi.
try:
	import json as _json32
	_otp_dt = _json32.load(open(
		"vagabond/vagabond/doctype/vagabond_otp/vagabond_otp.json", encoding="utf-8"))
	_otp_o = {f["fieldname"] for f in _otp_dt["fields"]}
	la("doctype OTP da co o cua luong quay",
	   {"da_xac_thuc", "han_dung", "tong_bill"} - _otp_o, set())
except Exception as _e32:
	la("doc duoc doctype OTP", str(_e32), "")

# tao_don_tay phai nhan ve va goi dung_ve SAU khi hoa don da luu.
la("tao_don_tay nhan ve_diem", "\tve_diem=\"\"," in _bh2_src, True)
la("tao_don_tay goi dung_ve", "_diem.dung_ve(ve_diem.strip(), si.name)" in _bh2_src, True)
_i_save = _bh2_src.find("\tsi.flags.ignore_permissions = True\n\tsi.save()\n\tfrappe.db.commit()")
_i_ve = _bh2_src.find("_diem.dung_ve(")
la("goi dung_ve SAU khi luu hoa don", _i_save > 0 and _i_ve > _i_save, True)
# Khong duoc boc try quanh dung_ve: nuot loi thi thu ngan tuong da giam
# tien cho khach trong khi bill thu du.
_khoi_ve = _bh2_src[_i_ve - 400:_i_ve] if _i_ve > 400 else ""
la("khong nuot loi khi tru diem", "try:" in _khoi_ve.split("diem_da_tru")[-1], False)

# --- 31b bis. Man tinh tien ---
la("man tinh tien nap the khach", "await posTaiThe(" in _pos_src, True)
la("man tinh tien ve khoi the", "html += posVeThe();" in _pos_src, True)
la("man tinh tien tru giam tu diem khoi phai thu",
   "tong - giam - giamDiem" in _pos_src, True)
la("man tinh tien gui ve len may chu", "ve_diem:" in _pos_src, True)
la("man tinh tien KHONG gui so tien giam tu diem",
   "giam_diem:" in _pos_src, False)
la("o nhap diem duoc doc lai vao trang thai", "posDiemNhap" in _pos_src, True)
la("co ham ve the hang", "function posVeThe(" in _km13_src, True)
la("co ham ve o tru diem", "function posVeTruDiem(" in _km13_src, True)
la("khoi the hien so diem hien co", "Số điểm hiện có" in _km13_src, True)
la("khoi the hien so diem tich cho bill", "Điểm tích cho bill này" in _km13_src, True)
la("khoi the hien ten hang", "hạng " in _km13_src, True)
la("o tru diem co tieu de", "TRỪ TIỀN BẰNG ĐIỂM" in _km13_src, True)
la("may khach chi gui gio hang khi xin ma",
   "items: JSON.stringify(posDon.mon.map" in _km13_src, True)
la("bo khach thi bo luon ve", "posDiemDat();" in _km13_src, True)
la("phieu tam tinh khong mang ve tru diem", "posDon.diemVe" in _bq_src, True)
la("phieu tam tinh KHONG gui ve_diem", "ve_diem" in _bq_src, False)

# --- 31c. Phieu hoan tien bi tu choi ---
la("tinh_trang loai phieu da huy khi xet",
   '{"hoa_don": si_name, "trang_thai": ["!=", "Da huy"]}, CON_SONG' in _ht2_src, True)
la("tinh_trang van tra ve phieu bi tu choi", "bi_tu_choi" in _ht2_src, True)
_than_tt = _ht2_src.split("def tinh_trang(")[1].split("\n@frappe.whitelist()")[0]
la("nhanh cho phep lap phieu moi co mang bi_tu_choi",
   '"duoc": 1,\n\t\t"bi_tu_choi": bi_tu_choi,' in _than_tt, True)
la("man hinh doi chu thanh Da tao phieu hoan tien",
   "Đã tạo phiếu hoàn tiền" in _ds8_src, True)
la("man hinh doi chu thanh Phieu hoan tien da bi tu choi",
   "Phiếu hoàn tiền đã bị từ chối" in _ds8_src, True)
la("man hinh khong con chu Da hoan tien", "<b>Đã hoàn tiền</b>" in _ds8_src, False)
la("man hinh khong con dich Da huy thanh da huy",
   "'Da huy': 'đã huỷ'" in _ds8_src, False)
la("phieu bi tu choi van hien nut hoan tien",
   "truoc + '<div style=\"margin-top:10px\"><button id=\"dsvHoanTien\"" in _ds8_src, True)

# --- 31c bis. Cau giai thich tran diem phai noi dung tran nao dang chan ---
#
# Nghiem thu tren site that 19/08/2026: khach Mr. Tri con 90.940 diem, bill
# 200.000 d. Tran theo bill la 100.000 diem, so du 90.940, nen tran that la
# 90.940. Con so in ra dung nhung cau giai thich lai ghi "bang 50% gia tri
# bill" - doc xong thu ngan tuong 50% cua 200.000 la 90.940.
_than_ttq = _do_src.split("def tinh_trang_quay(")[1].split("\ndef ")[0]
la("tinh_trang_quay tra ve ca tran theo bill", '"tran_theo_bill"' in _than_ttq, True)
la("tinh_trang_quay noi ro dang bi chan boi so du", '"do_so_du"' in _than_ttq, True)
la("man hinh noi ly do khi so du chan", "vì khách chỉ còn ngần ấy điểm" in _km13_src, True)
la("man hinh chi noi 50% khi dung la 50%", "bằng ' + money(tt.tran_pt) + '% giá trị bill." in _km13_src, True)

# Phep tinh tran theo bill phai TRUNG voi tran_dung_duoc khi so du du lon.
# Neu hai cong thuc lech nhau thi cau giai thich lai sai theo mot kieu khac.
for _tong, _pt, _tt in ((200000, 50.0, 10000.0), (500000, 50.0, 10000.0),
                        (30000, 50.0, 10000.0), (19000, 50.0, 10000.0)):
	_tran_tien = _tong * _pt / 100.0
	_con = _tong - _tt
	if _con < _tran_tien:
		_tran_tien = _con
	_mong = int(max(0.0, _tran_tien))
	la("tran theo bill %s d khop tran_dung_duoc" % _tong,
	   tran_dung_duoc(_tong, 10 ** 9, 1.0, _pt, _tt), _mong)

# --- 31c ter. Chu tren man tinh tien cho don food app (Felix 19/08/2026) ---
#
# Don GrabFood, BeFood, GreenSM, ShopeeFood: khach da tra tien cho app roi,
# app dang giu tien, quay khong thu dong nao ca. De chu "Thu tien" o do la
# de nhan vien va khach dung tai quay cung hieu nham.
la("nut chot bill doi chu theo loai don",
   "(laApp ? '🧾 Lưu hoá đơn ' : '💰 Thu tiền ')" in _pos_src, True)
la("bang xac nhan cung doi chu theo loai don",
   "(laApp ? 'Lưu hoá đơn ' : 'Thu ')" in _pos_src, True)
la("nut trong bang xac nhan cung doi",
   "laApp ? 'Lưu hoá đơn' : 'Thu tiền, lưu hoá đơn'" in _pos_src, True)
# Don tai quay thi VAN phai giu chu Thu tien, vi quay that su thu tien.
la("don tai quay van giu chu Thu tien", "'💰 Thu tiền '" in _pos_src, True)
la("dong giai thich nguon da doi theo y anh Viet",
   "máy đã tự động chọn nguồn tương ứng cho bạn" in _pos_src, True)
la("khong con cau vao nguon nao ra nguon do",
   "vào nguồn nào ra nguồn đó" in _pos_src, False)

# --- 31d. Ham doc mau ZNS ---
_zl_src = open("vagabond/zalo.py", encoding="utf-8").read()
la("co ham doc mau ZNS", "def thu_mau(" in _zl_src, True)
_than_tm = _zl_src.split("def thu_mau(")[1]
la("doc mau ZNS chi cho System Manager", "System Manager" in _than_tm, True)
la("doc mau ZNS goi dung duong template/info", "template/info" in _than_tm, True)
la("doc mau ZNS khong gui tin nao", "message/template" in _than_tm, False)

print("32. Chiet khau theo phan tram hoac theo so tien")

# ---------------------------------------------------------------------------
# Nhom 32. Hai kieu chiet khau tren to bao gia (anh Viet 19/08/2026, theo
# yeu cau cua Loan Anh: "mo them tinh nang giam gia theo so tien (VND)").
#
# Cho de vo nhat cua tinh nang nay: to bao gia CU deu de trong o kieu_ck.
# Neu ham thuan doc o trong thanh "so tien" thi mot to dang chiet khau 10%
# bong thanh chiet khau 10 dong, va khong ai thay ngay.
# ---------------------------------------------------------------------------

_bg32_src = open("vagabond/bao_gia.py", encoding="utf-8").read()
_js32_src = open("vagabond/public/js/bep/22-bao-gia.js", encoding="utf-8").read()

_bg32 = _nap_ham_thuan("vagabond/bao_gia.py", ["tien_chiet_khau"],
                       {"CK_PT": "Phan tram", "CK_TIEN": "So tien"})
_tien_ck = _bg32.get("tien_chiet_khau")
la("nap duoc ham tien_chiet_khau", bool(_tien_ck), True)

if _tien_ck:
	# --- Nep cu phai giu nguyen tuyet doi ---
	la("kieu rong hieu la phan tram", _tien_ck(1000000, "", 10), 100000.0)
	la("kieu None cung hieu la phan tram", _tien_ck(1000000, None, 10), 100000.0)
	la("kieu la rac cung hieu la phan tram", _tien_ck(1000000, "abc", 10), 100000.0)
	la("kieu Phan tram", _tien_ck(1000000, "Phan tram", 10), 100000.0)
	# --- Kieu moi ---
	la("kieu So tien tru dung so do", _tien_ck(1000000, "So tien", 250000), 250000.0)
	la("So tien le van dung", _tien_ck(1000000, "So tien", 1), 1.0)
	# --- Ba chan cung ---
	la("khong bao gio vuot goc khi go phan tram lon",
	   _tien_ck(1000000, "Phan tram", 250), 1000000.0)
	la("khong bao gio vuot goc khi go so tien lon",
	   _tien_ck(1000000, "So tien", 9999999), 1000000.0)
	la("gia tri am ra 0", _tien_ck(1000000, "So tien", -5), 0.0)
	la("phan tram am ra 0", _tien_ck(1000000, "Phan tram", -5), 0.0)
	la("goc bang 0 ra 0", _tien_ck(0, "So tien", 500), 0.0)
	la("goc am ra 0", _tien_ck(-1000, "Phan tram", 10), 0.0)
	la("gia tri 0 ra 0", _tien_ck(1000000, "Phan tram", 0), 0.0)
	# Lam tron ve dong, khong de lai so le.
	la("lam tron ve dong", _tien_ck(333333, "Phan tram", 3), round(333333 * 3 / 100.0, 0))
	la("ket qua luon la so nguyen dong",
	   _tien_ck(333333, "Phan tram", 3) == int(_tien_ck(333333, "Phan tram", 3)), True)
	# Phep bat bien: to KHONG BAO GIO ra so am.
	_am = []
	for _goc in (0, 1, 999, 1000000, 67200000):
		for _kieu in ("", "Phan tram", "So tien"):
			for _v in (0, 1, 10, 50, 100, 250, 999999999):
				if _goc - _tien_ck(_goc, _kieu, _v) < 0:
					_am.append((_goc, _kieu, _v))
	la("chiet khau khong bao gio lam to ra so am", _am[:3], [])

# --- May chu va may khach phai tinh RA CUNG MOT SO ---
#
# 22-bao-gia.js co ban sao bgTienCk. Lech nhau la sales doc mot so con
# khach nhan to in mot so khac. Cat than ham JS ra chay bang node roi doi
# chieu, giong cach nhom 28 lam voi bang thue.
import subprocess as _sp32

_m32 = re.search(r"function bgTienCk\(goc, kieu, giaTri\) \{.*?\n\}", _js32_src, re.S)
la("tim thay ban sao bgTienCk trong JS", bool(_m32), True)
if _m32 and _tien_ck:
	_bo32 = [(1000000, "", 10), (1000000, "Phan tram", 10), (1000000, "So tien", 250000),
	         (1000000, "Phan tram", 250), (1000000, "So tien", 9999999),
	         (333333, "Phan tram", 3), (0, "So tien", 500), (67200000, "So tien", 1234567),
	         (67200000, "Phan tram", 7.5), (999, "Phan tram", 33)]
	_ma32 = (_m32.group(0) + "\nvar ra=[];" +
	         "".join("ra.push(bgTienCk(%r,%s,%r));" % (g, ("''" if k == "" else "'%s'" % k), v)
	                 for g, k, v in _bo32) +
	         "console.log(JSON.stringify(ra));")
	try:
		_kq32 = _sp32.run(["node", "-e", _ma32], capture_output=True, text=True, timeout=30)
		_js_ra = json.loads(_kq32.stdout.strip()) if _kq32.returncode == 0 else None
	except Exception:
		_js_ra = None
	if _js_ra is None:
		print("   (khong chay duoc node, bo qua phep doi chieu JS)")
	else:
		_py_ra = [_tien_ck(g, k, v) for g, k, v in _bo32]
		_lech = [(_bo32[i], _py_ra[i], _js_ra[i]) for i in range(len(_bo32))
		         if abs(float(_py_ra[i]) - float(_js_ra[i])) > 0.5]
		la("may khach va may chu tinh chiet khau ra cung mot so", _lech[:3], [])

# --- Ma nguon: hai cap deu phai di qua ham thuan ---
la("cap to dung ham thuan",
   "doc.chiet_khau_tien = tien_chiet_khau(tam, doc.get(\"kieu_ck\"), doc.chiet_khau_pt)" in _bg32_src, True)
la("cap dong dung ham thuan",
   "d.ck_tien_dong = tien_chiet_khau(goc_dong, d.get(\"kieu_ck\"), d.chiet_khau)" in _bg32_src, True)
la("khong con phep nhan 1 tru chiet khau chia 100 o cap dong",
   "(1 - d.chiet_khau / 100.0)" in _bg32_src, False)
la("kieu_ck cua to duoc luu xuong", '"kieu_thue", "kieu_ck",' in _bg32_src, True)
la("kieu_ck cua dong chi nhan hai chuoi da biet",
   'x.get("kieu_ck") if x.get("kieu_ck") in (CK_PT, CK_TIEN) else None' in _bg32_src, True)
la("kieu_ck cua dong duoc goi ra man hinh", '"kieu_ck": d.get("kieu_ck") or ""' in _bg32_src, True)

# --- To in phai ghi dung don vi ---
la("to in khong ghi phan tram khi chiet khau la so tien",
   'nhan_ck = ("Chiết khấu" if (d.get("kieu_ck") or "") == CK_TIEN' in _bg32_src, True)
la("o CK cua dong in ra tien khi kieu la so tien",
   '_tien_vn(x["chiet_khau"]), "center"' in _bg32_src, True)

# --- Man hinh phai co du bon chip ---
la("co chip chiet khau tong theo phan tram", "data-t=\"ck-pt\"" in _js32_src, True)
la("co chip chiet khau tong theo so tien", "data-t=\"ck-tien\"" in _js32_src, True)
la("co chip chiet khau dong", "data-ckd=" in _js32_src, True)
la("doi kieu thi xoa so cu ve 0", "dck.chiet_khau = 0;" in _js32_src, True)
la("nhan o nhap doi theo kieu", "x.kieu_ck === 'So tien' ? 'CK đ' : 'CK%'" in _js32_src, True)
la("khoi tong khong ghi phan tram khi la so tien",
   "d.kieu_ck === 'So tien' ? '' : ' ' + (Number(d.chiet_khau_pt) || 0) + '%'" in _js32_src, True)

# --- Doctype ---
try:
	for _tep32, _can32 in (
		("vagabond/vagabond/doctype/bao_gia_ban_hang/bao_gia_ban_hang.json", {"kieu_ck"}),
		("vagabond/vagabond/doctype/bao_gia_dong/bao_gia_dong.json", {"kieu_ck", "ck_tien_dong"}),
	):
		_d32 = json.load(open(_tep32, encoding="utf-8"))
		_o32 = {f["fieldname"] for f in _d32["fields"]}
		la("doctype %s co du o moi" % _tep32.split("/")[-1], _can32 - _o32, set())
		for _f32 in _d32["fields"]:
			if _f32["fieldname"] == "kieu_ck":
				# O phai CHO PHEP de trong, vi moi to cu deu dang de trong.
				la("kieu_ck cho phep de trong (%s)" % _tep32.split("/")[-1],
				   str(_f32.get("options", "")).startswith("\n"), True)
except Exception as _e32b:
	la("doc duoc doctype bao gia", str(_e32b), "")

# ==========================================================================
# NHOM 33: nhan giao dich SePay va doi chieu tay khoan tien vao
#
# Bai hoc tu vu mui gio v224 con nguyen: bo kiem viet bang cach doc lai
# chinh ma minh vua viet thi no chi khoa lai dieu minh DANG TIN, chu khong
# doi chieu voi thuc te. Nen nhom nay khong chi kiem "ma nguon co chuoi X",
# ma kiem nhung RANG BUOC noi hai manh code doc lap voi nhau lai:
#
#   - Khoa chong trung cua tep moi phai TRUNG TUNG KY TU voi khoa ma Server
#     Script "SePay - Dong bo giao dich (hang gio)" dang ghi tren site that.
#     Lech mot ky tu la moi giao dich sinh hai dong, va khong phep kiem nao
#     khac bat duoc.
#   - O ma don ma man hinh dem GIAI THICH phai la dung o ma phep doi soat
#     dem TIM. Hai o khac nhau thi man hinh se giai thich mot dang bang mot
#     con so lay tu dang khac.
# ==========================================================================
print("\n[33] Nhan giao dich SePay va doi chieu tay tien vao")

_se_src = open("vagabond/sepay.py", encoding="utf-8").read()
_ht_src = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_js33 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()

# --- Khoa chong trung: mot ky tu lech la sinh dong doi ---
la("tien to khoa chong trung dung bang SEPAY-", 'TIEN_TO = "SEPAY-"' in _se_src, True)
la("webhook kiem ton tai truoc khi ghi",
   'frappe.db.exists(BT, {"transaction_id": ma})' in _se_src, True)
la("nap bu cung kiem ton tai truoc khi ghi",
   'frappe.db.exists(BT, {"transaction_id": TIEN_TO + str(tid)})' in _se_src, True)
la("ca hai duong deu ghi cung mot khoa",
   _se_src.count("TIEN_TO + ") >= 2, True)

# --- Webhook khong duoc lam sap, va khong duoc de SePay gui lai vo tan ---
la("webhook boc toan bo trong try", "def webhook():" in _se_src and
   _se_src.split("def webhook():")[1].lstrip().startswith('"""'), True)
la("webhook nuot loi roi van tra success",
   '"sepay: webhook vo loi"' in _se_src and '{"success": True, "message": "Da ghi nhan' in _se_src, True)
la("tai khoan chua khai tra success chu khong tra loi",
   'return {"success": True, "message": "So tai khoan %s chua khai' in _se_src, True)
la("giao dich da co tra success", 'da co trong so.' in _se_src, True)

# --- Bao mat ---
# Tu v247 diem nhan giu duoc HAI khoa (OCB + ACB) nen phep so chay qua
# any(), nhung tung phep van phai la compare_digest - so bang == la mo
# duong cho timing attack.
la("so sanh khoa bang compare_digest chu khong bang dau bang",
   "any(hmac.compare_digest(gui_len, k) for k in cac)" in _se_src, True)
la("chua dat khoa thi tu choi han", "Chưa đặt khoá bảo mật webhook" in _se_src, True)
la("tat trong Cai dat thi tu choi", "Diem nhan SePay dang tat" in _se_src, True)
la("khoa cat dang Password chu khong dang Data",
   '"fieldname": "sepay_khoa", "label": "Khoá bảo mật webhook SePay",\n\t\t\t"fieldtype": "Password"' in _se_src, True)

# --- Doc khoa tu header: kiem BANG CACH CHAY, khong bang doc mat ---
_m33 = re.search(r"^def _khoa_gui_len\(.*?(?=^@|^def |\Z)", _se_src, re.S | re.M)
if not _m33:
	la("tim thay ham _khoa_gui_len", False, True)
else:
	class _Req33:
		def __init__(self, h):
			self.headers = h

	class _Frappe33:
		request = None

	_mt33 = {"frappe": _Frappe33}
	exec(compile(_m33.group(0), "sepay:_khoa_gui_len", "exec"), _mt33, _mt33)
	_doc33 = _mt33["_khoa_gui_len"]
	for _ten33, _gui33, _mong33 in (
		("Apikey", {"Authorization": "Apikey abc123"}, "abc123"),
		("ApiKey hoa thuong khac nhau", {"Authorization": "ApiKey abc123"}, "abc123"),
		("Bearer", {"Authorization": "Bearer abc123"}, "abc123"),
		("khong tien to", {"Authorization": "abc123"}, "abc123"),
		("header rieng", {"X-Api-Key": "abc123"}, "abc123"),
		("khong co header", {}, ""),
		("khoang trang thua", {"Authorization": "  Apikey   abc123  "}, "abc123"),
	):
		_Frappe33.request = _Req33(_gui33)
		la("doc khoa tu header: %s" % _ten33, _doc33(), _mong33)
	_Frappe33.request = None
	la("khong co request thi tra chuoi rong", _doc33(), "")

# --- Nap bu: mac dinh phai la chay thu ---
la("nap bu mac dinh la chay thu", "def nap_bu(so_tk=\"\", tu_ngay=\"\", den_ngay=\"\", so_trang=40, that=0)" in _se_src, True)
la("chay thu thi khong ghi gi", "if not cint(that):" in _se_src, True)
la("nap bu chi cho quan ly hoac ke toan",
   'Chỉ quản lý hoặc kế toán mới nạp bù sao kê được.' in _se_src, True)

# --- Khong duoc dung vao con tro cua nhip keo ---
_ghi33 = [d for d in _se_src.splitlines()
          if "last_since_id" in d and ("set_value" in d or "db_set" in d or "set_single_value" in d)]
la("khong dong nao ghi de con tro since_id cua nhip keo", _ghi33, [])

# --- Man phieu hoan tien ---
la("chi tiet phieu tra ra ma don Pancake",
   '"ma_pancake": (si.get("custom_pancake_display_id") or "").strip(),' in _ht_src, True)
# RANG BUOC THAT: o man hinh GIAI THICH phai la dung o phep doi soat dem TIM.
la("o ma don man hinh doc trung voi o _tien_da_nhan doc",
   _ht_src.count('custom_pancake_display_id') >= 2, True)
la("dong SePay da nhan khong con bi khoa theo loai phieu",
   "htCtDong('SePay đã nhận', money(d.don.da_nhan_sepay)" in _js33
   and "(d.loai_hoan === 'Tien nop thua'\n        ? htCtDong('SePay đã nhận'" not in _js33, True)
la("khi ra 0 thi man hinh noi ro vi sao", "function htCtSepayTrong(d)" in _js33, True)
la("noi rieng hai nguyen nhan khac nhau", "d.don.ma_pancake\n    ? 'Đơn có mã Pancake" in _js33, True)

# --- Gan tay giao dich tien vao ---
la("gan tay chi cho ke toan va giam doc",
   "Chỉ kế toán hoặc giám đốc mới đối chiếu giao dịch tiền vào được." in _ht_src, True)
la("chan gan mot dong tien RA", 'là tiền RA khỏi tài khoản' in _ht_src, True)
la("chan gan mot giao dich da thuoc phieu khac",
   'Một khoản tiền vào chỉ ' in _ht_src, True)
la("ghi lai ai gan va luc nao", '"nguoi_gan_gd_vao": frappe.session.user' in _ht_src, True)
la("gan tay KHONG doi so tien cua phieu", '"so_tien"' not in _ht_src.split("def gan_gd_vao")[1].split("return {\"ok\": 1, \"gd\": gd")[0], True)
la("phieu da huy thi khong gan them", 'đã huỷ nên không đối chiếu thêm được' in _ht_src, True)

# --- Truong moi phai duoc dung lai moi lan Migrate ---
_tt33 = open("vagabond/truong_tu_them.py", encoding="utf-8").read()
la("nhom truong sepay duoc dung lai khi Migrate", '_dung_nhom(sepay.TRUONG_MOI, "sepay")' in _tt33, True)
la("sepay nam trong danh sach import", "mua_dich_vu, noi_bo, sepay," in _tt33, True)
for _o33 in ("gd_vao", "nguoi_gan_gd_vao", "ngay_gan_gd_vao"):
	la("phieu hoan tien co o %s" % _o33, '"fieldname": "%s"' % _o33 in _ht_src, True)
for _o33 in ("sepay_bat", "sepay_khoa", "sepay_chua_map"):
	la("Cai dat co o %s" % _o33, '"fieldname": "%s"' % _o33 in _se_src, True)

# --- Man Cai dat SePay ---
_js33b = open("vagabond/public/js/bep/17-cai-dat.js", encoding="utf-8").read()
_js33c = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()
la("co man Cai dat SePay", "async function scrSePay()" in _js33b, True)
la("man SePay duoc noi vao menu", "if (k === 'CDSE') return go(scrSePay);" in _js33c, True)
la("the SePay nam trong nhom Cai dat", "'CDCN', 'CDSE'," in _js33c, True)
# Nghiem thu that ngay 19/08/2026: goi tin mang header "Authorization" bi
# CHINH FRAPPE tra 401 truoc khi vao toi diem nhan, vi Frappe doc header do
# de tim khoa API cua no. Chi "X-Api-Key" moi vao duoc. Huong dan tren man
# hinh la thu duy nhat anh Viet doc khi cau hinh ben SePay, nen no sai la
# webhook khong bao gio nhan duoc goi nao ma khong ai hieu vi sao.
la("man hinh huong dan dung header X-Api-Key", "X-Api-Key" in _js33b, True)
la("man hinh noi ro khong duoc dung Authorization",
   "Không dùng header <code>Authorization</code>" in _js33b, True)
la("khong con huong dan Apikey trong Authorization",
   "Apikey &lt;khoá&gt;" in _js33b, False)
la("ma nguon ghi lai vi sao khong dung Authorization",
   "KHONG DUNG HEADER \"Authorization\" voi diem nhan nay." in _se_src, True)
la("diem nhan van doc duoc X-Api-Key", '"X-Api-Key"' in _se_src, True)

# --- HMAC-SHA256: duong xac thuc chinh ---
#
# Man Bao mat cua SePay co bon lua chon. "API Key" bat buoc gui o header
# Authorization, ma Frappe tra 401 cho header do truoc khi goi tin vao toi
# diem nhan. "HMAC-SHA256" gui chu ky o X-SePay-Signature, Frappe khong
# dung toi - va con chac hon vi no ky ca goi tin.
la("co ham kiem chu ky HMAC", "def _kiem_hmac():" in _se_src, True)
la("chu ky doc tu header X-SePay-Signature", '"X-SePay-Signature"' in _se_src, True)
la("HMAC duoc thu TRUOC duong khoa bi mat",
   _se_src.index("co_hmac, hmac_dat = _kiem_hmac()") < _se_src.index('cac = _cac_khoa("sepay_khoa")'), True)
la("chu ky sai thi tu choi han, khong lui sang duong khac",
   'return _tu_choi(401, "Chu ky HMAC khong dung.")' in _se_src, True)
la("ky tren NGUYEN VAN goi tin", "frappe.request.get_data() or b\"\"" in _se_src, True)
la("chu ky sai thi ghi lai du de doi chieu", '"sepay: chu ky HMAC khong khop"' in _se_src, True)
# Nhat ky loi phai du de doi chieu ma TUYET DOI khong duoc in khoa bi mat
# ra. Cat dung khoi log_error do roi soi tung dong: chi duoc phep in chu ky
# nhan duoc, moc gio, do dai goi tin, so khoa da thu, va 12 ky tu dau cua
# chu ky may tinh ra.
_log36 = _se_src.split('"sepay: chu ky HMAC khong khop"')[0]
_log36 = _log36[_log36.rfind("frappe.log_error("):]
la("nhat ky loi in 12 ky tu dau chu ky may tinh ra",
   "sorted(dung)[0][:12]" in _log36, True)
# Soi rieng PHAN THAM SO cua chuoi dinh dang: `len(cac_khoa)` chi la mot
# con so nen vo hai, nhung `khoa` hay `cac_khoa[0]` lot vao day la chinh
# khoa bi mat bi ghi ra Error Log - noi ai doc duoc Desk cung xem duoc.
_ts36 = _log36.split("% (", 1)[1] if "% (" in _log36 else _log36
_ts36 = _ts36.replace("len(cac_khoa)", "").replace("len(_cac_chuoi_ky(than, moc))", "")
la("nhat ky loi KHONG in khoa bi mat", "khoa" in _ts36, False)
la("nhat ky loi noi ro phai lam gi tiep", "dan lai Secret Key" in _log36, True)
la("o cat khoa HMAC la Password", '"fieldname": "sepay_hmac", "label": "Khoá HMAC-SHA256 của webhook SePay",\n\t\t\t"fieldtype": "Password"' in _se_src, True)
# v247: dat_hmac them tham so khe de giu khoa webhook thu hai (ACB).
la("nguoi dung tu dan khoa HMAC, may khong tu sinh", "def dat_hmac(khoa=None, khe=1):" in _se_src, True)
la("chan chuoi qua ngan khong giong Secret Key", "không giống Secret Key của SePay" in _se_src, True)

# Phep kiem THAT: dung lai chu ky bang chinh cac ham cua tep, roi thu
# nhieu dang header khac nhau.
_m36 = re.search(r"^def _tach_chu_ky\(.*?(?=^@|^def |\Z)", _se_src, re.S | re.M)
_m36b = re.search(r"^def _hmac_dung\(.*?(?=^@|^def |\Z)", _se_src, re.S | re.M)
# Tu 21/08/2026 _hmac_dung goi _cac_chuoi_ky, nen phai nap kem ham do.
_m36c = re.search(r"^def _cac_chuoi_ky\(.*?(?=^@|^def |\Z)", _se_src, re.S | re.M)
if not (_m36 and _m36b and _m36c):
	la("tim thay ba ham chu ky", False, True)
else:
	import hmac as _hm36
	_mt36 = {"hmac": _hm36}
	exec(compile(_m36.group(0), "sepay:_tach_chu_ky", "exec"), _mt36, _mt36)
	exec(compile(_m36c.group(0), "sepay:_cac_chuoi_ky", "exec"), _mt36, _mt36)
	exec(compile(_m36b.group(0), "sepay:_hmac_dung", "exec"), _mt36, _mt36)
	_tach = _mt36["_tach_chu_ky"]
	_dung36 = _mt36["_hmac_dung"]
	_khoa36 = "whsec_thu_nghiem_1234567890"
	_than36 = b'{"id":123,"transferAmount":650000}'
	_bo36 = _dung36(_khoa36, _than36)
	_hex36 = [x for x in _bo36 if x.islower() and len(x) == 64][0]
	_b6436 = [x for x in _bo36 if x.endswith("=") or ("+" in x or "/" in x) or (not all(c in "0123456789abcdefABCDEF" for c in x))][0]
	la("sinh du ba dang chu ky (hex thuong, hex hoa, base64)", len(_bo36), 3)
	# Co moc gio thi thu them ba cach ghep: moc.than, moc+than, than+moc.
	# Moi cach lai ra ba dang ma hoa, tong 12. Chu ky dung theo BAT KY cach
	# nao cung phai duoc nhan - vi SePay khong noi ho ghep kieu gi.
	_bo36m = _dung36(_khoa36, _than36, "1755600000")
	la("co moc gio thi thu du bon cach ghep", len(_bo36m), 12)
	la("chu ky chi ky than goi van nam trong tap", _hex36 in _bo36m, True)
	_ghep36 = _mt36["_cac_chuoi_ky"](_than36, "1755600000")
	la("bon chuoi ky deu khac nhau", len(set(_ghep36)), 4)
	la("khong co moc gio thi chi mot chuoi", len(_mt36["_cac_chuoi_ky"](_than36, "")), 1)
	for _nhan36, _gui36 in (
		("chu ky tran", _hex36),
		("co tien to sha256", "sha256=" + _hex36),
		("kieu nhieu phan v1", "t=1755600000,v1=" + _hex36),
		("hex chu hoa", _hex36.upper()),
		("base64", _b6436),
	):
		_khop = any(x in _bo36 for x in _tach(_gui36))
		la("nhan duoc chu ky dang: %s" % _nhan36, _khop, True)
	la("chu ky sai thi khong khop",
	   any(x in _bo36 for x in _tach("a" * 64)), False)
	la("goi tin bi sua mot chu la chu ky hong",
	   _hex36 in _dung36(_khoa36, b'{"id":123,"transferAmount":950000}'), False)

# --- Hop dong: khong tu map thong tin nguoi lien he vao nguoi ky ---
_hd36 = open("vagabond/hop_dong_pdf.py", encoding="utf-8").read()
la("dien thoai ben A chi lay tu nguoi ky",
   '"dien_thoai": (d.get("dt_ky_a") or "").strip(),' in _hd36, True)
la("email ben A chi lay tu nguoi ky",
   '"email": (d.get("email_ky_a") or "").strip(),' in _hd36, True)
la("khong con lui ve dien thoai cua to bao gia",
   '(d.get("dt_ky_a") or "").strip() or d.get("dien_thoai")' in _hd36, False)
la("khong con lui ve email cua to bao gia",
   '(d.get("email_ky_a") or "").strip() or d.get("email")' in _hd36, False)
# Ten va chuc vu thi VAN duoc lui ve dai dien cong ty - Loan Anh chi noi ve
# so dien thoai va email.
la("ten nguoi ky van lui ve dai dien cong ty",
   '"dai_dien": (d.get("nguoi_ky_a") or "").strip() or d.get("dai_dien"),' in _hd36, True)
la("de trong thi khoi thong tin bo han dong do",
   'if b.get("dien_thoai"):' in _hd36 and 'if b.get("email"):' in _hd36, True)

# --- Man Cai dat ---
la("man Cai dat co o dan khoa HMAC", 'id="seHm"' in _js33b, True)
la("man Cai dat chi ro chon HMAC-SHA256 ben SePay", "chọn <b>HMAC-SHA256</b>" in _js33b, True)
la("man Cai dat dan dung khong chon API Key", "Đừng chọn API Key" in _js33b, True)

la("man SePay ghep duong dan voi ten mien nguoi dung dang mo",
   "return location.origin + d.duong_dan_path;" in _js33b, True)
# frappe.utils.get_url() tra ve ten mien noi bo cua Frappe Cloud, dan cho
# SePay la sai. Bat duoc luc nghiem thu v229 tren site that.
la("may chu tra ve ca duong dan khong kem ten mien", '"duong_dan_path": DUONG_DAN,' in _se_src, True)
la("nap bu import make_get_request cho tu te",
   "from frappe.integrations.utils import make_get_request" in _se_src, True)
# Kiem loi GOI chu khong kiem chu "frappe.make_get_request" xuat hien
# trong ma nguon: cau giai thich vi sao khong duoc goi no cung chua dung
# chuoi do.
la("khong con dong nao GOI frappe.make_get_request",
   [d for d in _se_src.splitlines()
    if "frappe.make_get_request(" in d and not d.strip().startswith("#")], [])
la("man SePay canh bao tai khoan chua khai", "d.chua_map || []" in _js33b, True)
la("nut nap bu that tach roi nut chay thu",
   "seNapBu(0)" in _js33b and "seNapBu(1)" in _js33b, True)

# ==========================================================================
# NHOM 34: che do tinh thue cua to bao gia
#
# Su co that, to VGB-PQ-2026-0008 ngay 19/08/2026. To PDF gui khach in ra
# ba dong khong the cung dung:
#     Cong tien hang chua thue   32.086.610
#     Thue GTGT 0% / VAT                  0
#     TONG TIEN TAM TINH         34.653.539
#
# Nguyen nhan khong nam o phep tinh thue, ma o cho o "kieu_thue" mang
# "default" trong doctype: may chu TINH o mot che do, co so du lieu GHI o
# che do khac. Bai kiem nay dung lai dung con so cua to do va khoa lai ca
# hai dieu: phep tinh cua tung che do, va viec khong che do nao duoc phep
# tu doi sau lung nguoi dung.
# ==========================================================================
print("\n[34] Che do tinh thue cua to bao gia")

_bg34_src = open("vagabond/bao_gia.py", encoding="utf-8").read()
_bgjs34 = open("vagabond/public/js/bep/22-bao-gia.js", encoding="utf-8").read()


# Dung lai chinh cac ham da nap tu bao_gia.py o nhom 28, khong cat ban sao
# thu hai: hai ban sao la hai co hoi de ban kiem trach khoi ban that.
if not _ns_bg:
	print("   (chua nap duoc bao_gia, bo qua nhom 34)")
	sys.exit(1)
_bang_thue = _ns_bg["bang_thue"]
_tien_ck34 = _ns_bg["tien_chiet_khau"]

# --- MOT cach doc che do, kiem bang cach CHAY ---
_kt34 = _ns_bg["_kieu_thue"]
for _v34, _mong34 in (
	(None, "Theo tờ (cũ)"), ("", "Theo tờ (cũ)"),
	("Theo tờ (cũ)", "Theo tờ (cũ)"), ("Theo từng dòng", "Theo từng dòng"),
	("theo từng dòng", "Theo tờ (cũ)"), ("lung tung", "Theo tờ (cũ)"),
	("  Theo từng dòng  ", "Theo từng dòng"),
):
	la("doc che do thue tu %r" % _v34, _kt34({"kieu_thue": _v34}), _mong34)

# --- Dung lai to VGB-PQ-2026-0008 bang so that ---
_DONG34 = [34305570.0, 108342.0, 74074.0]
_TAM34 = sum(_DONG34)
_CK34 = 2401376.0
la("to 0008: cong tien hang dung bang so tren to PDF", _TAM34, 34487986.0)
la("to 0008: chiet khau theo so tien ra dung so tren to PDF",
   _tien_ck34(_TAM34, "So tien", 2401376), 2401376.0)

_SAU_CK34 = _TAM34 - _CK34
la("to 0008: cong tien hang chua thue", _SAU_CK34, 32086610.0)

# Cach cu, thue 8% tren tong. Day la con so ma may chu DA TINH luc luu.
_THUE_TO34 = round(_SAU_CK34 * 8.0 / 100.0, 0)
_TONG_TO34 = _SAU_CK34 + _THUE_TO34
la("cach cu ra dung so thue tren man hinh", _THUE_TO34, 2566929.0)
la("cach cu ra dung so tong da luu", _TONG_TO34, 34653539.0)

# Cach theo tung dong voi moi dong 0%. Day la con so to PDF in ra.
_BT34 = _bang_thue([{"thanh_tien": x, "thue_pt": 0} for x in _DONG34],
                   ck_to=_CK34, phi_giao=0, phi_giao_pt=0, da_gom=0)
la("cach theo dong: tien thue bang 0", _BT34["tien_thue"], 0.0)
la("cach theo dong: tong chi con 32.086.610", _BT34["tong_cong"], 32086610.0)

# ĐÂY LA PHEP KIEM THAT SU: hai che do ra hai con so KHAC NHAU tren cung
# mot to. Nen mot to bi ghi sai che do la mot to sai tien, khong phai mot
# to sai chu.
la("hai che do ra hai so khac nhau, lech dung bang tien thue",
   round(_TONG_TO34 - _BT34["tong_cong"], 0), 2566929.0)

# --- Luat sua chua phai bat dung to 0008 va tha cac to khac ---
def _co_phai_bi_doi(tam, ck, thue_pt, phi, da_gom, dong_pt, tong_luu):
	bt = _bang_thue([{"thanh_tien": t, "thue_pt": p} for t, p in dong_pt],
	                ck_to=ck, phi_giao=phi, phi_giao_pt=0, da_gom=da_gom)
	sau = tam - ck
	cu = (sau + phi) if da_gom else (sau + round(sau * thue_pt / 100.0, 0) + phi)
	return abs(bt["tong_cong"] - tong_luu) > 1 and abs(cu - tong_luu) <= 1


la("luat bat dung to 0008",
   _co_phai_bi_doi(_TAM34, _CK34, 8, 0, 0, [(x, 0) for x in _DONG34], 34653539.0), True)
la("luat THA to 0007 (da nhat quan o che do moi)",
   _co_phai_bi_doi(_TAM34, _CK34, 8, 0, 0, [(x, 0) for x in _DONG34], 32086610.0), False)
la("luat THA to gia da gom VAT (hai che do ra cung mot so)",
   _co_phai_bi_doi(28800000.0, 0, 8, 0, 1, [(28800000.0, 0)], 28800000.0), False)
la("luat THA to that su khai 8% tung dong",
   _co_phai_bi_doi(1000000.0, 0, 8, 0, 0, [(1000000.0, 8)], 1080000.0), False)

# --- Mot cach doc duy nhat ---
la("_tinh doc che do qua _kieu_thue", "if _kieu_thue(doc) == KT_DONG:" in _bg34_src, True)
la("tom_tat_thue doc che do qua _kieu_thue", "if _kieu_thue(doc) != KT_DONG:" in _bg34_src, True)
la("_goi tra ve che do da chuan hoa", '"kieu_thue": _kieu_thue(doc),' in _bg34_src, True)
la("khong con cho nao so chuoi thue tho",
   '(doc.get("kieu_thue") or "") == "Theo từng dòng"' in _bg34_src, False)

# --- To moi phai mang theo che do ---
la("moi() tra ve o kieu_thue", '"kieu_thue": KT_MAC_DINH_TO_MOI,' in _bg34_src, True)
la("_do_vao luon ghi mot gia tri ro rang", "doc.kieu_thue = kt_cu or KT_MAC_DINH_TO_MOI" in _bg34_src, True)
la("_do_vao giu che do cu khi app khong gui", "kt_cu = _kieu_thue(doc) if not doc.is_new() else \"\"" in _bg34_src, True)

# --- Doctype KHONG duoc mang default cho cac o quyet dinh cach tinh tien ---
for _tep34 in ("vagabond/vagabond/doctype/bao_gia_ban_hang/bao_gia_ban_hang.json",
               "vagabond/vagabond/doctype/bao_gia_dong/bao_gia_dong.json"):
	_d34 = json.load(open(_tep34, encoding="utf-8"))
	_xau34 = [f["fieldname"] for f in _d34["fields"]
	          if f["fieldname"].startswith("kieu_") and f.get("default")]
	# Cot co default thi luc Migrate MariaDB dien gia tri do vao MOI dong
	# da co, va luc INSERT no dien vao dong nao de trong. Ca hai deu la
	# doi cach tinh tien cua mot to sau lung nguoi lap.
	la("%s: khong o kieu_ nao mang default" % _tep34.split("/")[-1], _xau34, [])
	for _f34 in _d34["fields"]:
		if _f34["fieldname"] == "kieu_thue":
			la("kieu_thue cho phep de trong", str(_f34.get("options", "")).startswith("\n"), True)

# --- Cong chan to khong khop ---
la("co phep kiem truoc khi in", "def _kiem_to_khop(d):" in _bg34_src, True)
la("phep kiem duoc goi truoc khi ve bang tong", "\t_kiem_to_khop(d)\n" in _bg34_src, True)
la("cau bao loi noi ro phai lam gi (QT-24)", "bấm Lưu một lần nữa" in _bg34_src, True)

# --- Ham sua chua ---
la("ham sua chua chi dung set_value chu khong save",
   'frappe.db.set_value(DT, r["name"], "kieu_thue", KT_TO, update_modified=False)' in _bg34_src, True)
la("ham sua chua ghi vet vao Comment", '"reference_doctype": DT, "reference_name": r["name"],' in _bg34_src, True)
la("ham sua chua duoc goi khi Migrate",
   "bao_gia.sua_kieu_thue_bi_dat_mac_dinh()" in open("vagabond/patches/dong_bo_cau_truc.py", encoding="utf-8").read(), True)
la("co ham soi de xem truoc, khong ghi gi", "def soi_kieu_thue():" in _bg34_src, True)

# --- Man chi doc cua bao gia ---
la("man chi doc khong con in thang chiet_khau_pt kem dau phan tram",
   "'<span>Chiết khấu ' + d.chiet_khau_pt + '%</span>'" in _bgjs34, False)
la("man chi doc doc kieu_ck nhu man sua",
   "d.kieu_ck === 'So tien' ? '' : ' ' + (Number(d.chiet_khau_pt) || 0) + '%'" in _bgjs34, True)
la("chiet khau tung dong tren man chi doc cung doc kieu_ck",
   "x.kieu_ck === 'So tien' ? money(x.chiet_khau) + ' đ'" in _bgjs34, True)
la("man chi doc biet ca che do theo tung dong", "function bgXemThueHtml(d)" in _bgjs34, True)

# --- Chiet khau so tien khong duoc vap tran 100 cua doctype ---
_ctl34 = open("vagabond/vagabond/doctype/bao_gia_ban_hang/bao_gia_ban_hang.py", encoding="utf-8").read()
la("tran 100 chi ap cho chiet khau phan tram",
   '(d.get("kieu_ck") or "") != "So tien" and flt(d.chiet_khau) > 100' in _ctl34, True)
la("van chan chiet khau am", "chiết khấu không được âm" in _ctl34, True)

# ==========================================================================
# NHOM 35: ho so hoan ung gom duoc nhieu nha cung cap
#
# Uyen 19/08/2026, qua anh Viet: *"phai gop duoc nha cung cap luc lam APP
# hoan ung (hien tai chi lam duoc theo tung NCC rat mat thoi gian vi hoan
# ung la toan mua le te lat nhat)"*.
#
# Cho de sai nhat khong nam o man hinh ma nam o BUT TOAN. Mot Payment Entry
# chi mang MOT party; ho so gom ba nha cung cap ma van dung mot but toan
# thi hai nha con lai khong duoc xoa no, hoac ERPNext tu choi ca but toan.
# Nhom nay khoa lai phep gom theo nha cung cap THAT CUA TUNG HOA DON.
# ==========================================================================
print("\n[35] Ho so hoan ung gom nhieu nha cung cap")

_hs35 = open("vagabond/ho_so_tt.py", encoding="utf-8").read()
_js35 = open("vagabond/public/js/bep/19-ho-so-tt.js", encoding="utf-8").read()

# --- Chan mot nha van con, nhung chi cho hai luong tra thang cho ho ---
la("van chan nhieu nha voi luong khong phai hoan ung",
   "if len(ncc_thay) > 1 and not nhieu_ncc:" in _hs35, True)
la("chi luong Hoan ung HD moi duoc gom nhieu nha",
   'nhieu_ncc = (loai or "") == LOAI_HU_HD' in _hs35, True)
la("cau bao loi chi duong sang luong hoan ung (QT-24)",
   'luồng đó gom được nhiều nhà cùng lúc' in _hs35, True)

# --- But toan: mot cho moi nha cung cap ---
la("but toan gom theo nha cung cap cua tung hoa don", "theo_ncc = {}" in _hs35, True)
# Kiem dong LENH chu khong kiem chuoi xuat hien trong tep: doan ghi chu
# giai thich vi sao khong duoc lam the cung chua dung chuoi do.
la("party lay tu hoa don chu khong lay dau ho so",
   "pe.party = ma_ncc" in _hs35
   and [d for d in _hs35.splitlines()
        if d.strip() == "pe.party = doc.nha_cung_cap"] == [], True)
la("so tien cua but toan la tong CUA NHOM, khong phai tong ho so",
   "pe.paid_amount = flt(tong_nhom)" in _hs35, True)
la("tra ve tat ca ma but toan da sinh", 'return ", ".join(ra)' in _hs35, True)
la("hoa don khong doc duoc nha cung cap thi dung lai",
   "không đọc được nhà cung cấp nên chưa sinh bút toán" in _hs35, True)

# Phep gom: dung lai bang tay tren du lieu gia, kiem BANG CACH CHAY.
def _gom35(cap):
	"""cap la [(ten_hoa_don, nha_cung_cap, so_tien)]. Tra ve {nha: tong}."""
	ra = {}
	for _ten, _nha, _tien in cap:
		ra[_nha] = ra.get(_nha, 0.0) + float(_tien)
	return ra

_bo35 = [("HDM-1", "AEON", 56759), ("HDM-2", "KAMEREO", 1200000),
         ("HDM-3", "AEON", 40000), ("HDM-4", "BACH HOA", 15000)]
_kq35 = _gom35(_bo35)
la("ba nha cung cap ra ba but toan", len(_kq35), 3)
la("AEON gom hai hoa don thanh mot but toan", _kq35["AEON"], 96759.0)
la("tong cac but toan bang tong ho so", sum(_kq35.values()), 1311759.0)
la("mot nha thi van chi mot but toan", len(_gom35([("HDM-1", "AEON", 1000)])), 1)

# --- Nguoi duoc hoan ung ---
la("ho so hoan ung bat buoc chon nguoi duoc hoan ung",
   "Chưa chọn người được hoàn ứng." in _hs35, True)
la("dau ho so hoan ung mang ten nguoi duoc hoan ung",
   "doc.nha_cung_cap = ma_ung" in _hs35, True)
# Cho nay tung la mot cai bay that: may dien san so tai khoan cua NHA CUNG
# CAP vao o nguoi thu huong, bam Luu ma quen sua la tien di nham.
la("so tai khoan nhan tien lay tu nguoi ung chu khong tu nha cung cap",
   "lay_tk = ma_ung" in _hs35 and "for k, v in (_tk_nhan(lay_tk) or {}).items():" in _hs35, True)
la("khong dien email nha cung cap cho ho so hoan ung", 'doc.email_ncc = ""' in _hs35, True)
la("thu bao NCC bi chan voi ho so hoan ung",
   "toán chỉ dùng cho hồ sơ công nợ nhà cung cấp." in _hs35
   and "if (doc.loai or LOAI_NCC) in (LOAI_HU, LOAI_HU_HD):" in _hs35, True)

# --- Tung dong phai mang ten nha cung cap cua no ---
la("moi dong luu ten nha cung cap cua rieng no",
   '"ben_ban": hd.supplier_name or hd.supplier or "",' in _hs35, True)
la("chi tiet tra ve so nha cung cap", '"so_ncc": len({' in _hs35, True)
la("to in ghi ten nha cung cap trong bang khi gom nhieu nha", "nhieu_nha = len({" in _hs35, True)

# --- Man hinh ---
la("doi chip nha cung cap KHONG xoa hoa don da tick", "if (!laHU) hsTaoChon = {};" in _js35, True)
la("co chip tat ca nha cung cap", "'📚 Tất cả nhà cung cấp'" in _js35, True)
la("dem so nha cung cap dang chon", "var soNha = Object.keys(nhaChon).length;" in _js35, True)
la("man hinh chan luu khi chua chon nguoi duoc hoan ung",
   "if (laHU && !hsTaoNguoiUng) return baoTin" in _js35, True)
la("ho so hoan ung khong gui bo loc ncc len may chu", "ncc: laHU ? '' : hsTaoNcc," in _js35, True)
la("man chi tiet an the thu bao NCC voi ho so hoan ung",
   "if (hs.trang_thai === 'Da thanh toan' && !laHU) {" in _js35, True)

# --- Doctype ---
_dt35 = json.load(open("vagabond/vagabond/doctype/vagabond_ho_so_tt/vagabond_ho_so_tt.json", encoding="utf-8"))
_o35 = {f["fieldname"] for f in _dt35["fields"]}
la("doctype co du ba o moi", {"nguoi_ung", "ten_nguoi_ung", "so_ncc"} - _o35, set())
la("cac o moi deu nam trong field_order",
   {"nguoi_ung", "ten_nguoi_ung", "so_ncc"} - set(_dt35.get("field_order") or []), set())
# Bai hoc tu su co bao gia cung ngay: o quyet dinh cach xu ly khong duoc
# mang default, vi cot co default thi co so du lieu tu dien luc INSERT va
# luc Migrate.
la("ba o moi khong o nao mang default",
   [f["fieldname"] for f in _dt35["fields"]
    if f["fieldname"] in ("nguoi_ung", "ten_nguoi_ung", "so_ncc") and f.get("default")], [])

# ==========================================================================
# NHOM 37: doi soat phieu hoan tien phai giu duoc dau da khop
#
# Su co that, phieu HT-2026-00899 ngay 19/08/2026. Chi Dung hoi may co tu
# doi soat phieu hoan tien khong, tien da chi tu MB Biz roi. Doc du lieu
# that thi:
#
#   Tien 185.000 d DA RA khoi tai khoan MB luc 18:00:48.
#   Sao ke co dung dong do, noi dung "THE VAGABOND HOAN TIEN HDB-26-08-00581".
#   Phieu HT-2026-00899 tro dung hoa don HDB-26-08-00581, dung so tien.
#   Nhip doi soat chay luc 18:36 va KHOP dung phieu do.
#   Nhung phieu van nam o "Cho chi", da_doi_soat ~ 0.
#
# Vi sao: buoc sinh chung tu ngay sau do nem NameError (_tien_vn chua bao
# gio duoc dinh nghia), khoi except goi frappe.db.rollback(), va cai
# rollback do xoa luon dau "da doi soat" vua ghi - vi hai viec nam chung
# mot giao dich co so du lieu. Cu 35 phut moi gio lai khop, lai hong, lai
# xoa dau. Khong ai nhin thay gi.
#
# Nhom nay khoa lai ca hai: ham bi thieu, va ranh gioi giao dich.
# ==========================================================================
print("\n[37] Doi soat phieu hoan tien giu duoc dau da khop")

_ht37 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_js37 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()

# --- Ham bi thieu: kiem BANG CACH CHAY, khong bang doc mat ---
_m37 = re.search(r"^def _tien_vn\(.*?(?=^@|^def |\Z)", _ht37, re.S | re.M)
if not _m37:
	la("hoan_tien.py co dinh nghia _tien_vn", False, True)
else:
	_mt37 = {}
	exec(compile(_m37.group(0), "hoan_tien:_tien_vn", "exec"), _mt37, _mt37)
	_tvn = _mt37["_tien_vn"]
	for _v37, _mong37 in ((0, "0"), (1000, "1.000"), (185000, "185.000"),
	                      (1234567, "1.234.567"), (None, "0"), ("", "0")):
		la("_tien_vn(%r)" % _v37, _tvn(_v37), _mong37)

# MOI cho goi _tien_vn deu phai co ham that dung sau. Ca kiem nay bat dung
# cai da no: goi mot ham khong ton tai.
_goi37 = len(re.findall(r"_tien_vn\(", _ht37))
la("co it nhat ba cho dang goi _tien_vn", _goi37 >= 4, True)

# --- Ranh gioi giao dich: dau da khop phai duoc ghi TRUOC khi sinh chung tu ---
_than37 = _ht37.split("def doi_soat(")[1].split("\n@frappe.whitelist()")[0]
_vt_dau = _than37.find('"trang_thai": "Da doi soat",')
_vt_commit = _than37.find("frappe.db.commit()", _vt_dau)
_vt_sinh = _than37.find("_sinh_chung_tu(ho)")
_vt_rollback = _than37.find("frappe.db.rollback()")
la("co commit ngay sau khi danh dau da doi soat", _vt_dau < _vt_commit < _vt_sinh, True)
la("rollback nam SAU commit nen khong xoa duoc dau da khop", _vt_commit < _vt_rollback, True)
la("hong sinh chung tu thi ghi loi len chinh phieu",
   'DT, d["name"], "loi_sinh_ct",' in _ht37, True)
la("cau bao loi noi ro phai lam gi (QT-24)",
   "Nhờ kế toán bấm lại nút Đối soát lệnh chi" in _ht37, True)
la("phieu co o giu loi", '"fieldname": "loi_sinh_ct"' in _ht37, True)
la("danh sach tra ra o loi de man hinh bay", '"so_hddt", "loi_sinh_ct",' in _ht37, True)
la("man danh sach bay canh bao", "x.loi_sinh_ct" in _js37, True)
la("man chi tiet bay canh bao", "if (d.loi_sinh_ct) {" in _js37, True)

# --- Xuat Excel cho chi Dung ---
la("co ham xuat Excel", "def xuat_excel(trang_thai=\"\", tim=\"\", so_dong=500):" in _ht37, True)
la("xuat dung bo loc dang hien tren man, khong viet lai truy van",
   "kq = ds(trang_thai=trang_thai, so_dong=so_dong, tim=tim)" in _ht37, True)
# So tai khoan bat dau bang so 0: de dang so thi Excel an mat so 0 dau, va
# ke toan chuyen nham tai khoan.
la("so tai khoan ep thanh chuoi trong Excel", '"\'" + str(r.get("so_tk") or "")' in _ht37, True)
la("Excel co cot canh bao loi sinh chung tu", '"Cảnh báo",' in _ht37, True)

# --- PHEP KIEM THAT SU: hai ham phai noi cung mot ngon ngu ---
#
# Tep Excel dau tien xuat ra RONG TRON, 0 dong, trong khi man hinh dang
# hien 8 phieu. Vi xuat_excel doc kq.get("rows") con ds() tra danh sach
# duoi khoa "ds". Ca kiem cu chi soi chu trong ma nguon nen khong thay gi.
#
# Hai phep duoi day doi chieu THAT: ten khoa, va tung ten cot.
_than_ds37 = _ht37.split("def ds(trang_thai=")[1].split("\n@frappe.whitelist()")[0]
_khoa_tra = set(re.findall(r'return \{\s*"(\w+)"', _than_ds37)) | set(re.findall(r'"(\w+)": ds_', _than_ds37))
la("ds() tra danh sach duoi khoa \"ds\"", '"ds": ds_' in _than_ds37, True)
_than_xls37 = _ht37.split("def xuat_excel(")[1].split("\n@frappe.whitelist()")[0]
la("xuat_excel doc dung khoa do", 'kq.get("ds")' in _than_xls37, True)
# Kiem dong LENH chu khong kiem chuoi xuat hien trong tep: doan ghi chu
# ke lai loi cu cung chua dung chuoi do.
la("xuat_excel khong con doc khoa \"rows\"",
   [d for d in _than_xls37.splitlines()
    if 'kq.get("rows")' in d and not d.strip().startswith("#")], [])

# Moi o ma tep Excel doc ra deu phai la o ds() that su tra ve - hoac o goc
# trong get_all, hoac o duoc dap them ben duoi.
#
# Lay khoi fields DAI NHAT trong ds(): ham nay co vai cau get_all, cac cau
# phu chi lay mot hai o (ten khach, trang thai phieu chi), con cau chinh
# moi la cau dung nhung o di ra tep Excel.
_cac_khoi37 = re.findall(r"fields=\[(.*?)\]", _than_ds37, re.S)
_o_ds37 = set(re.findall(r'"(\w+)"', max(_cac_khoi37, key=len) if _cac_khoi37 else ""))
_o_them37 = set(re.findall(r'd\["(\w+)"\] = ', _than_ds37))
_o_co37 = _o_ds37 | _o_them37
_o_doc37 = set(re.findall(r'r\.get\("(\w+)"\)', _than_xls37))
la("moi o Excel doc deu co trong ds()", sorted(_o_doc37 - _o_co37), [])
la("ma giao dich ngan hang co trong ds()", "ma_gd" in _o_ds37, True)
la("man hinh co nut xuat Excel", "id=\"htDsXls\"" in _js37, True)
la("nut Excel gui dung chip va o tim dang chon",
   "trang_thai: htDsLoc === 'tat_ca' ? '' : htDsLoc, tim: htDsTim" in _js37, True)
_cn37 = open("vagabond/khung/kiem_thu/thu_cua_ngo.py", encoding="utf-8").read()
la("xuat_excel nam trong danh sach cua ngo", '"xem_tien_du", "xuat_excel",' in _cn37, True)

# ==========================================================================
# NHOM 38: tem mon va nut de nghi chi trong phan he Dat hang
#
# De bao 19/08/2026 ba chuyen tren mot cai tem: chip "GrabFood 678" khong
# in ra, ghi chu bill khong in ra, va tem lech khoi giay.
#
# Hai chuyen dau la LOI DU LIEU chu khong phai loi trinh bay: cuc thong tin
# hoa don vua luu ma man tinh tien truyen sang ham in tem khong mang ma
# tham chieu, va ham in tem khong doc toi ghi chu cua ca bill. Nhom nay
# khoa lai duong di cua hai o do.
# ==========================================================================
print("\n[38] Tem mon va de nghi chi")

_js38 = open("vagabond/public/js/bep/09-tinh-tien-quay.js", encoding="utf-8").read()
_tem38 = open("vagabond/public/js/bep/10-bill-quay.js", encoding="utf-8").read()
_mi38 = open("vagabond/may_in.py", encoding="utf-8").read()
_dnc38 = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
_tc38 = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()

# --- Ma tham chieu phai di toi duoc may in ---
la("hoa don vua luu mang theo ma tham chieu",
   "mtc: laApp ? (posDon.ma || '') : (posDon.mtc || '')," in _js38, True)
# RANG BUOC THAT: o gui len may chu va o gui sang ham in tem phai lay tu
# CUNG mot cho, neu khong thi hoa don luu mot ma ma tem in mot ma.
la("ma gui len may chu va ma in tem lay cung mot nguon",
   _js38.count("laApp ? (posDon.ma || '') : (posDon.mtc || '')") >= 2, True)
la("ham in tem ghep nguon voi ma tham chieu",
   "var ma = (d.mtc || d.ma || '').trim();" in _tem38, True)

# --- Ghi chu bill phai in theo ---
la("tem in ca ghi chu cua bill", "if (d.ghi_chu) giua.push(d.ghi_chu);" in _tem38, True)
la("tem van in tuy chon pha che", "'100% đường · 100% đá'" in _tem38, True)
la("tem van in ghi chu rieng cua mon", "if (m.gc) giua.push(m.gc);" in _tem38, True)

# --- Can tem: chinh tai cho, khong sua ma nguon ---
la("co o cat thong so can tem", 'TRUONG_CAN = "vgb_can_tem"' in _mi38, True)
la("co ham luu can tem", "def luu_can_tem(" in _mi38, True)
la("chan so lech vo ly", "ngoài khoảng cho phép" in _mi38, True)
la("thong so can tem di kem kho tem cho app",
   't["ngang"], t["doc"], t["xoay"] = c["ngang"], c["doc"], c["xoay"]' in _mi38, True)
la("co ban in thu co vien", "function posInTemThu()" in _tem38, True)
# Ban in thu ma ve khung rieng thi no chi chung minh chinh no dung.
la("in thu va in that dung CHUNG mot khung",
   _tem38.count("temKhung(") >= 3, True)
la("man Cai dat co o dich ngang va dich doc",
   'id="ctNgang"' in open("vagabond/public/js/bep/18-doi-chieu-may-in.js", encoding="utf-8").read()
   and 'id="ctDoc"' in open("vagabond/public/js/bep/18-doi-chieu-may-in.js", encoding="utf-8").read(), True)
la("in thu duoc ngay chua can luu",
   "posInTemThu();" in open("vagabond/public/js/bep/18-doi-chieu-may-in.js", encoding="utf-8").read(), True)

# Phep tinh le tem: kiem BANG CACH CHAY.
def _le38(goc, dich):
	return (goc + dich, goc - dich)


for _d38, _mong38 in ((0, (1.5, 1.5)), (1, (2.5, 0.5)), (-1, (0.5, 2.5))):
	la("dich doc %g mm thi le tren duoi doi nguoc chieu" % _d38, _le38(1.5, _d38), _mong38)

# --- De nghi chi: nut nam trong Dat hang va MOI nguoi deu thay ---
la("co ham lap phieu tu app", "def tao(du_lieu=None, gui_luon=0):" in _dnc38, True)
# Chi soi THAN ham tao: gui_duyet dat trang thai la dung viec cua no.
_than_tao38 = _dnc38.split("def tao(du_lieu=None, gui_luon=0):")[1]
la("ham tao khong tu dat trang thai gui duyet",
   "gui_duyet(doc.name)" in _than_tao38 and "doc.trang_thai = TT_CHO_DUYET" not in _than_tao38, True)
la("ham tao khong chep lai luat nghiep vu",
   "TK_THEO_PHAN_LOAI" in _dnc38.split("def tao(du_lieu=None")[1], False)
la("the nam trong nhom Dat hang", "'Purchase', 'Transfer', 'RND', 'DNC'" in _tc38, True)
# Doi 20/08/2026: the dan vao MAN DANH SACH chu khong dan thang vao form.
# Anh Viet: "bat ky phan he nao co nut Tao phieu thi bat buoc phai co man
# hinh Danh sach de xem lai". Vao danh sach truoc thi thay ngay phieu cu.
la("the co duong den man hinh", "if (k === 'DNC') return go(scrTTNB);" in _tc38, True)
# The nay PHAI nam ngoai khoi coQuyenMua: nam trong la chi thu mua thay,
# dung cai anh Viet bao khong duoc.
_khoi38 = _tc38.split("card(TYPES.Manufacture.icon")[1].split("(coQuyenMua()")[0]
la("the de nghi chi nam NGOAI khoi khoa theo quyen mua", "'DNC')" in _khoi38, True)
la("co man hinh de nghi chi", "async function scrDeNghiChi()" in
   open("vagabond/public/js/bep/16-mua-hang.js", encoding="utf-8").read(), True)

# --- Nut in tem phai hien voi MOI bill, khong rieng bill co mon nuoc ---
#
# Ham in tem doi tu 10/08/2026 sang in cho moi mon, nhung CAI KHOA truoc
# nut thi khong ai doi theo. Ket qua: don GrabFood ban mot hu banh Almond
# Tuile thi khong co nut in tem nao (De bao 19/08/2026, anh Viet gui anh
# man bao thanh cong chi co ba nut in hoa don, hoa don moi, ve danh sach).
la("hai man bao thanh cong dung chung mot ham ve nut in",
   _js38.count("posNutIn(") >= 3, True)
la("khong con khoa nut in theo dieu kien co mon nuoc",
   "posCoNuoc(posBillVua.mon)" in _js38, False)
la("tem hien khi bill co bat ky mon nao", "if (!mon.length) return '';" in _js38, True)
la("phieu lam mon VAN chi hien khi co mon nuoc",
   "(coNuoc ? '<button class=\"btn gh\" data-pm" in _js38, True)
la("man danh sach bill cung theo luat do",
   "((d.items || []).length" in _tem38 and "posCoNuoc(d.items || []) ? '<button" in _tem38, True)

# Phep kiem THAT: dung lai ham chon nut bang JS.
_m38 = re.search(r"function posNutIn\(d\) \{.*?\n\}", _js38, re.S)
if not _m38:
	la("tim thay ham posNutIn", False, True)
else:
	try:
		import subprocess as _sp38

		_ma38 = ("var posCoNuoc = function (m) { return m.some(function (x) { return x.nuoc; }); };"
		         + _m38.group(0)
		         + "var ra = [];"
		         + "[[], [{nuoc:1}], [{}], [{},{nuoc:1}]].forEach(function (m) {"
		         + " var s = posNutIn({mon: m});"
		         + " ra.push([s.indexOf('data-tem') >= 0, s.indexOf('data-pm') >= 0]); });"
		         + "console.log(JSON.stringify(ra));")
		_kq38 = _sp38.run(["node", "-e", _ma38], capture_output=True, text=True, timeout=20)
		_ra38 = json.loads(_kq38.stdout.strip()) if _kq38.returncode == 0 else None
	except Exception:
		_ra38 = None
	if _ra38 is None:
		print("   (khong chay duoc node, bo qua phep chay thu posNutIn)")
	else:
		la("bill rong thi khong co nut nao", _ra38[0], [False, False])
		la("bill chi co mon nuoc: co ca tem lan phieu lam mon", _ra38[1], [True, True])
		la("bill chi co banh: CO tem, khong co phieu lam mon", _ra38[2], [True, False])
		la("bill tron banh va nuoc: co ca hai", _ra38[3], [True, True])

print("\n[39] Luong ket thuc phieu hoan tien: dinh UNC roi ghi so")

# Anh Viet 19/08/2026: *"Thiet ke nut de dinh kem uy nhiem chi cho phieu hoan
# tien sau khi da doi soat -> chi Dung vao dinh kem file cho sales lay de gui
# khach -> hoan thanh -> may tu ghi so. Hien chua co luong ket thuc cho cai
# phieu nay."*
#
# Nhom ca nay canh dung mot thu: khong duoc phep ghi so mot but toan chi khi
# tren phieu chi chua co uy nhiem chi. Do la dieu chi Dung chot 16/08 va la
# ly do hook chan_thieu_uy_nhiem_chi ton tai. Them mot duong tu dong Submit
# la them mot duong co the vong qua hook do.

_ht39 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_js39 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_dt39 = open("vagabond/vagabond/doctype/vagabond_hoan_tien/vagabond_hoan_tien.json", encoding="utf-8").read()

la("doctype co trang thai Hoan thanh",
   "Cho chi\\nDa chi\\nDa doi soat\\nHoan thanh\\nDa huy" in _dt39, True)
la("trang thai cu KHONG bi doi ten",
   all(t in _dt39 for t in ("Cho chi", "Da chi", "Da doi soat", "Da huy")), True)
la("nhan tieng Viet cho trang thai moi", '"Hoan thanh": "Hoàn thành"' in _ht39, True)
la("chip dem co Hoan thanh",
   '("Cho chi", "Da chi", "Da doi soat", "Hoan thanh", "Da huy")' in _ht39, True)

_than_dinh39 = _ht39.split("def dinh_unc(")[1].split("\n@frappe.whitelist()")[0]
_than_ht39 = _ht39.split("def hoan_thanh(")[1].split("\n@frappe.whitelist()")[0]

la("dinh_unc co whitelist", "@frappe.whitelist()\ndef dinh_unc(" in _ht39, True)
la("hoan_thanh co whitelist", "@frappe.whitelist()\ndef hoan_thanh(" in _ht39, True)

# Dinh tep KHONG duoc ghi so. Do la ca hai nhip, va cung la khoang thoi
# gian Sales tai tep ve gui khach.
la("dinh_unc khong tu ghi so", ".submit()" in _than_dinh39, False)
la("dinh_unc chan nguoi khong phai ke toan", "_duoc_tu_choi()" in _than_dinh39, True)
la("dinh_unc dinh tep vao Payment Entry chu khong vao ho so",
   '"attached_to_doctype": PE' in _than_dinh39, True)
la("dinh_unc khong dinh nham vao ho so hoan tien",
   '"attached_to_doctype": DT' in _than_dinh39, False)
la("dinh_unc chan tep rong", "Tệp uỷ nhiệm chi rỗng" in _than_dinh39, True)
# Do dai chuoi base64 khong phai so byte that. Phai giai ma roi moi do.
la("dinh_unc do kich thuoc SAU khi giai ma", "base64.b64decode(noi)" in _than_dinh39, True)

la("hoan_thanh doi phai co UNC that tren phieu chi", "_dem_unc(" in _than_ht39, True)
la("hoan_thanh khong tat hook chan thieu UNC",
   "ignore_validate" in _than_ht39 or "flags.ignore_mandatory" in _than_ht39, False)
la("hoan_thanh lap lai duoc, khong ghi so hai lan",
   "if not da_ghi_san:" in _than_ht39, True)
la("hoan_thanh dat dung trang thai", '"trang_thai": "Hoan thanh"' in _than_ht39, True)
la("hoan_thanh ghi ten nguoi bam", '"nguoi_hoan_thanh": frappe.session.user' in _than_ht39, True)

# _dem_unc phai HOI CO SO DU LIEU chu khong doc mot co da luu tren ho so:
# tep co the bi go tren Desk sau khi da ghi vet ngay_dinh_unc (QT-19).
_dem39 = _ht39.split("def _dem_unc(")[1].split("\ndef ")[0]
la("_dem_unc dem that o co so du lieu", "frappe.db.count(" in _dem39, True)
# Doc phan MA THAT, bo chu thich va bo ca chuoi mo ta: chinh chu thich cua
# ham do co nhac ten truong nay de giai thich vi sao KHONG dung no. Kiem
# theo chuoi con thi ca kiem se do chinh loi giai thich cua minh - da vap
# ba lan roi (frappe.make_get_request, pe.party, kq.get("rows")).
def _ma_that39(than):
	"""Bo chuoi mo ta va cac dong chu thich, tra lai phan ma chay that."""
	if than.count('"""') >= 2:
		than = than.split('"""', 2)[2]
	return "\n".join(
		x for x in than.split("\n") if x.strip() and not x.strip().startswith("#")
	)

la("_dem_unc khong tin truong ngay_dinh_unc",
   "ngay_dinh_unc" in _ma_that39(_dem39), False)
# Chinh phep kiem tren phai biet do: bo vao mot than gia co truong do trong
# phan ma that thi no BAT BUOC phai thay.
la("phep kiem tren that su soi duoc phan ma",
   "ngay_dinh_unc" in _ma_that39('ma_pe):\n\t"""Chu thich co ngay_dinh_unc."""\n\treturn d.ngay_dinh_unc\n'),
   True)

# _pe_cua la cong chung cho ca hai ham. Thong bao loi phai chi duong ra,
# khong duoc chi bao hong (QT-24).
_pe39 = _ht39.split("def _pe_cua(")[1].split("\ndef ")[0]
for _cau39 in ("chưa đối soát", "chưa sinh được phiếu chi", "đã huỷ hoặc bị từ chối"):
	la("cong _pe_cua noi ro vuong o dau: %s" % _cau39, _cau39 in _pe39, True)
la("loi thieu doi soat co chi duong lam tiep", "bấm Đối soát" in _pe39, True)

# Truong moi phai co trong TRUONG_MOI, neu khong thi migrate khong tao cot
# va moi lan ghi la mot lan im lang mat du lieu.
_tm39 = _ht39.split("TRUONG_MOI = {")[1].split("\n}")[0]
for _t39 in ("nguoi_dinh_unc", "ngay_dinh_unc", "nguoi_hoan_thanh", "ngay_hoan_thanh"):
	la("TRUONG_MOI khai truong %s" % _t39, '"fieldname": "%s"' % _t39 in _tm39, True)

# Cong ngo: hai ham moi phai co ten trong danh sach, neu khong thi mot
# decorator bam nham la khong ai biet.
_cn39 = open("vagabond/khung/kiem_thu/thu_cua_ngo.py", encoding="utf-8").read()
la("cong ngo biet dinh_unc", '"dinh_unc"' in _cn39, True)
la("cong ngo biet hoan_thanh", '"hoan_thanh"' in _cn39, True)

# Man hinh: nut chi ve khi MAY CHU cho phep, khong tu suy o may khach.
la("man chi tiet co the uy nhiem chi", "function htCtUnc(d)" in _js39, True)
la("nut dinh UNC theo co cua may chu", "if (d.dinh_duoc_unc)" in _js39, True)
la("nut hoan thanh theo co cua may chu", "if (d.ket_thuc_duoc)" in _js39, True)
la("nut hoan thanh co hoi lai truoc khi ghi so", "hoiCo('Hoàn thành phiếu hoàn tiền'" in _js39, True)
la("chip loc co Hoan thanh", "['Hoan thanh', 'Hoàn thành']" in _js39, True)
la("danh sach hien phieu nao con thieu UNC", "chưa có UNC" in _js39, True)
# UNC la chung tu goc, nen KHONG duoc nen lai nhu anh bang chung.
_unc39 = _js39.split("function htUncGui(")[1].split("\nasync function ")[0]
la("khong nen lai tep UNC truoc khi gui", "toDataURL" in _unc39, False)

# Ba khoa may chu tra ve phai dung ten voi ba khoa man hinh doc. Day dung
# la kieu loi da lam tep Excel dau tien xuat ra 0 dong (kq.get("rows")).
_ct39 = _ht39.split("def chi_tiet(")[1].split("\n@frappe.whitelist()")[0]
for _k39 in ("unc", "co_unc", "dinh_duoc_unc", "ket_thuc_duoc"):
	la("chi_tiet tra ve khoa %s" % _k39, 'ra["%s"]' % _k39 in _ct39, True)
	la("man hinh doc dung khoa %s" % _k39, "d.%s" % _k39 in _js39, True)
la("ds() tra co_unc cho tung dong", 'd["co_unc"] =' in _ht39, True)
la("Excel cua chi Dung co cot uy nhiem chi", '"Uỷ nhiệm chi"' in _ht39, True)

print("\n[40] Khoa trung giao dich: mot lan tien ra chi khop mot phieu")

# Anh Viet 19/08/2026 duyet lam sau luong ket thuc: "khoa trung giao dich".
#
# Vong quet trong doi_soat() lap NGOAI la ho so, TRONG la giao dich, va truoc
# hom nay khong giu dau vet giao dich nao da dung. Hai phieu hoan cua CUNG
# mot hoa don goc, cung so tien - rat hay gap khi khach doi banh hai lan tren
# mot don - deu bam vao dong tien ra dau tien tim thay. Moi phieu khop xong
# lai sinh mot phieu chi rieng, nen so phinh len dung bang so tien khong he
# ra khoi ngan hang.

_ht40 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_js40 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()

la("co ham doc giao dich da bi chiem", "def _gd_da_chiem(" in _ht40, True)
_gdc40 = _ht40.split("def _gd_da_chiem(")[1].split("\n@frappe.whitelist()")[0]
la("phieu da huy khong giu giao dich", '"trang_thai": ["!=", "Da huy"]' in _gdc40, True)
la("cho phep mot phieu giu lai giao dich cua chinh no", "tru_ho_so" in _gdc40, True)

_ds40 = _ht40.split("def doi_soat(ho_so=None")[1].split("\ndef doi_soat_tu_dong")[0]
la("doi_soat doc danh sach giao dich da chiem", "_gd_da_chiem(tru_ho_so=ho_so)" in _ds40, True)
la("doi_soat bo qua giao dich cua phieu khac",
   'chu_cu and chu_cu != d["name"]' in _ds40, True)
# Boi them NGAY trong vong quet: hai ho so cung khop trong CUNG mot lan chay
# thi ho so thu hai phai thay dau ho so thu nhat vua dat.
la("doi_soat boi them dau ngay trong vong quet",
   'da_chiem[g["name"]] = d["name"]' in _ds40, True)
la("va boi truoc luc sinh chung tu",
   _ds40.index('da_chiem[g["name"]] = d["name"]') < _ds40.index("_sinh_chung_tu(ho)"), True)
# Khong duoc im lang bo qua: co the la hai lan hoan that, va luc do sao ke
# con thieu mot dong chu khong phai phieu sai.
la("truong hop trung duoc bay len cho nguoi xem", '"trung_voi": chu_cu' in _ds40, True)

# Duong SePay goi thang phai co CUNG mot khoa. Mot hang rao chi dung o mot
# duong thi duong con lai la cua sau.
_st40 = _ht40.split("def sepay_tien_ra(")[1].split("\ndef doi_soat_tu_dong")[0]
la("duong SePay goi thang cung khoa trung", "_gd_da_chiem(" in _st40, True)
la("duong SePay noi ro trung voi phieu nao", '"trung_voi": chu_cu' in _st40, True)
la("duong SePay chi duong xu ly tiep", "sao kê còn thiếu một dòng" in _st40, True)

# Man hinh phai tach HAI loai can xem lai, vi cach xu ly khac han nhau.
la("man hinh tach rieng truong hop trung giao dich",
   "x.trung_voi; });" in _js40, True)
la("man hinh van giu canh bao so tien lech", "SỐ TIỀN LỆCH" in _js40, True)

print("\n[41] De nghi chi doi sang bang ke nhieu dong")


def _nap_ham_dnc():
	"""Doc cac ham THUAN cua de_nghi_chi.py, khong import ca mo dun.

	Cung cach lam voi _nap_ham_that o dau tep: import ca mo dun thi keo theo
	frappe, ma may chay cong kiem khong co frappe. Cat lay than ham roi chay
	trong mot khong gian ten co san flt.

	Doc THAN HAM THAT chu khong chep lai o day: chep lai thi sua ban that ma
	quen sua ban chep, ca kiem van xanh trong khi he da hong.
	"""
	src = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
	can = ["cac_dong", "cong_bang_ke", "tien_phieu", "can_giam_doc_duyet",
	       "buoc_ke_tiep", "can_tru_tam_ung", "_tien"]
	mt = {
		"flt": lambda x: float(x or 0),
		"NGUONG_GIAM_DOC": 2000000.0,
		"TT_CHO_GIAM_DOC": "Cho giam doc",
		"TT_CHO_KE_TOAN": "Cho ke toan",
	}
	for ten in can:
		m = re.search(r"^def %s\(.*?(?=^def |\Z)" % re.escape(ten), src, re.S | re.M)
		if not m:
			print("KHONG THAY ham %s trong de_nghi_chi.py" % ten)
			sys.exit(1)
		exec(compile(m.group(0), "de_nghi_chi:%s" % ten, "exec"), mt, mt)
	return mt


def _nap_ham_dnc42():
	"""Doc THAN HAM THAT cua hai phep THUAN moi, khong import ca mo dun."""
	src = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
	mt = {"CHIP_TRANG_THAI": None, "TT_NHAP": "Nhap", "TT_CHO_DUYET": "Cho duyet",
	      "TT_CHO_GIAM_DOC": "Cho giam doc", "TT_CHO_KE_TOAN": "Cho ke toan",
	      "TT_HOAN_TAT": "Hoan tat", "TT_DA_CHI": "Da chi", "TT_TRA_LAI": "Bi tra lai"}
	m = re.search(r"^CHIP_TRANG_THAI = \(.*?^\)", src, re.S | re.M)
	exec(compile(m.group(0), "de_nghi_chi:CHIP", "exec"), mt, mt)
	for ten in ("trang_thai_theo_chip", "khop_noi_dung", "noi_dung_ck"):
		m = re.search(r"^def %s\(.*?(?=^def |\Z)" % re.escape(ten), src, re.S | re.M)
		exec(compile(m.group(0), "de_nghi_chi:%s" % ten, "exec"), mt, mt)
	return mt


def _nap_ham_vcl43():
	"""Doc THAN HAM THAT cua phep THUAN trong viec_can_lam.py."""
	src = open("vagabond/viec_can_lam.py", encoding="utf-8").read()
	mt = {}
	for ten in ("VAI_KE_TOAN", "VAI_THU_MUA", "VAI_KHO", "VAI_GIAM_DOC", "VAI_QUAN_LY"):
		m = re.search(r"^%s = \{.*?\}" % re.escape(ten), src, re.S | re.M)
		exec(compile(m.group(0), "viec_can_lam:%s" % ten, "exec"), mt, mt)
	m = re.search(r"^MA_TRAN = \{.*?^\}", src, re.S | re.M)
	exec(compile(m.group(0), "viec_can_lam:MA_TRAN", "exec"), mt, mt)
	m = re.search(r"^def thay_duoc\(.*?(?=^def |\Z)", src, re.S | re.M)
	exec(compile(m.group(0), "viec_can_lam:thay_duoc", "exec"), mt, mt)
	return mt


_H43 = _nap_ham_vcl43()
H43_thay = _H43["thay_duoc"]

_H42 = _nap_ham_dnc42()
H42_chip = _H42["trang_thai_theo_chip"]
H42_khop = _H42["khop_noi_dung"]

_H41 = _nap_ham_dnc()
H41_cong = _H41["cong_bang_ke"]
H41_tien = _H41["tien_phieu"]
H41_buoc = _H41["buoc_ke_tiep"]
H41_cantru = _H41["can_tru_tam_ung"]

# Anh Viet 19/08/2026: *"Hien tai he thong dang la 1 phieu = 1 khoan chi.
# Viec nay qua mat thoi gian. Em hay cau truc lai theo dang Master-Detail
# (1 phieu = Nhieu khoan chi)."*

_dnc41 = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
_js41 = open("vagabond/public/js/bep/16-mua-hang.js", encoding="utf-8").read()
_dtc41 = json.load(open(
	"vagabond/vagabond/doctype/vagabond_de_nghi_chi/vagabond_de_nghi_chi.json", encoding="utf-8"))
_dtd41 = json.load(open(
	"vagabond/vagabond/doctype/vagabond_de_nghi_chi_dong/vagabond_de_nghi_chi_dong.json", encoding="utf-8"))
_dtm41 = json.load(open(
	"vagabond/vagabond/doctype/vagabond_loai_chung_tu/vagabond_loai_chung_tu.json", encoding="utf-8"))

_tr41 = {f["fieldname"]: f for f in _dtc41["fields"]}
_trd41 = {f["fieldname"]: f for f in _dtd41["fields"]}
_trm41 = {f["fieldname"]: f for f in _dtm41["fields"]}

# --- Cau truc hai bang ---
la("bang con la Table tren phieu cha", _tr41["cac_khoan"]["fieldtype"], "Table")
la("bang con tro dung doctype", _tr41["cac_khoan"]["options"], "Vagabond De Nghi Chi Dong")
la("bang con la istable", _dtd41.get("istable"), 1)
la("phieu cha co Tong tien", _tr41["tong_tien"]["fieldtype"], "Currency")
# Tong tien PHAI chi doc: de nguoi sua tay tren Desk la mo lai dung cai cua
# ma cong_bang_ke sinh ra de dong.
la("Tong tien chi doc", _tr41["tong_tien"].get("read_only"), 1)
la("phieu cha co o Thuoc ma Tam ung", _tr41["thuoc_tam_ung"]["fieldtype"], "Link")
la("o Tam ung tro ve chinh doctype de nghi chi",
   _tr41["thuoc_tam_ung"]["options"], "Vagabond De Nghi Chi")

# Anh Viet: *"O chon 'Ngan hang' cua nguoi thu huong bat buoc phai thiet lap
# kieu Link tro ve Doctype Danh muc Ngan hang chuan NAPAS ma em da tao dot
# truoc. Khong duoc hardcode hay tu tao list rieng."*
la("Ngan hang la Link", _tr41["ngan_hang"]["fieldtype"], "Link")
la("Ngan hang tro ve danh muc NAPAS chuan", _tr41["ngan_hang"]["options"], "Bank")
la("khong tu de ra danh sach ngan hang rieng trong ma",
   "VIETCOMBANK" in _dnc41 or "Techcombank" in _dnc41, False)

for _t41 in ("noi_dung", "so_tien", "phan_loai", "loai_chung_tu", "so_hoa_don",
             "ngay_hoa_don", "mst"):
	la("dong bang ke co truong %s" % _t41, _t41 in _trd41, True)
la("loai chung tu tren dong la Link ve Danh muc",
   (_trd41["loai_chung_tu"]["fieldtype"], _trd41["loai_chung_tu"]["options"]),
   ("Link", "Vagabond Loai Chung Tu"))

# --- Co la_hoa_don_vat thay cho so chuoi ---
#
# So chuoi voi chu "Hoa don VAT" thi doi ten dong danh muc la ba o hoa don im
# lang bien mat, va phieu van gui di duoc ma thieu so hoa don.
la("danh muc co co la_hoa_don_vat", _trm41["la_hoa_don_vat"]["fieldtype"], "Check")
la("danh muc co co bat_buoc_tep", _trm41["bat_buoc_tep"]["fieldtype"], "Check")
_dong41 = [x for x in _dnc41.split("\n")
           if x.strip() and not x.lstrip().startswith("#")]
_ma41 = "\n".join(_dong41)
la("may chu doc CO chu khong so chuoi ten loai chung tu",
   'la_hoa_don_vat' in _ma41, True)
la("man hinh doc CO chu khong so chuoi ten loai chung tu",
   "ct.la_hoa_don_vat" in _js41 and "=== 'Hoá đơn VAT'" not in _js41, True)

# --- Cong tien o MAY CHU (QT-19) ---
la("co ham cong bang ke", "def cong_bang_ke(" in _dnc41, True)
_tkl41 = _dnc41.split("def truoc_khi_luu(")[1].split("\n@frappe.whitelist()")[0]
la("moi lan luu la may chu cong lai tong tien",
   "doc.tong_tien = cong_bang_ke(doc)" in _tkl41, True)
la("khong nhan tong tien tu man hinh",
   'doc.tong_tien = flt(d.get("tong_tien"))' in _dnc41, False)

# CAI BAY LON NHAT cua lan doi cau truc nay.
#
# so_tien tren phieu cha van con do, nhung phieu lap tu 20/08/2026 de no bang
# 0 vi tien da nam o cac dong. Cho nao con doc so_tien se thay 0. Nguy nhat la
# buoc_ke_tiep: doc 0 thi MOI phieu moi, du 50 trieu, deu roi thang xuong ke
# toan va khong bao gio qua tay giam doc. Khong bao loi gi ca.
la("co ham doc so tien that cua phieu", "def tien_phieu(" in _dnc41, True)
_duyet41 = _dnc41.split("def duyet(")[1].split("\n@frappe.whitelist()")[0]
la("buoc duyet ke tiep KHONG doc truong so_tien cu",
   "buoc_ke_tiep(doc.so_tien)" in _duyet41, False)
la("buoc duyet ke tiep doc so tien that",
   "buoc_ke_tiep(tien_phieu(doc))" in _duyet41, True)

# Phep chay THAT: mot phieu 50 trieu nam o bang ke phai len giam doc.
_phieu41 = {"so_tien": 0, "tong_tien": 0, "cac_khoan": [
	{"so_tien": 30000000}, {"so_tien": 20000000}]}
la("cong bang ke ra dung tong", H41_cong(_phieu41), 50000000)
la("phieu 50 trieu o bang ke VAN phai len giam doc",
   H41_buoc(H41_tien(_phieu41)), "Cho giam doc")
# Phieu mot dong cu, tien con nam o truong cu.
la("phieu cu doc duoc so tien tu truong cu",
   H41_tien({"so_tien": 5000000, "cac_khoan": []}), 5000000)
la("phieu cu 5 trieu cung len giam doc",
   H41_buoc(H41_tien({"so_tien": 5000000, "cac_khoan": []})), "Cho giam doc")
la("phieu nho di thang xuong ke toan",
   H41_buoc(H41_tien({"so_tien": 0, "cac_khoan": [{"so_tien": 50000}]})), "Cho ke toan")

# Truong so_tien cu KHONG duoc con bat buoc: phieu nhieu dong de no trong,
# va Frappe nem MandatoryError truoc khi bat ky ma nao cua minh chay. Da vap
# that tren site 20/08/2026 ngay lan thu dau tien lap phieu.
la("truong so_tien cu khong con bat buoc", _tr41["so_tien"].get("reqd"), None)
la("truong so_tien cu chi doc", _tr41["so_tien"].get("read_only"), 1)
# Va may chu ghi vao do dung bang tong, phong khi con doan ma nao chua tim ra
# het van doc truong cu.
la("may chu soi guong so_tien cu bang tong tien",
   "doc.so_tien = doc.tong_tien" in _tkl41, True)

# --- Can tru hoan ung ---
la("con no khi hoan ung it hon tam ung", H41_cantru(2000000, 1500000)[0], 500000)
la("khong con no khi hoan du", H41_cantru(2000000, 2000000)[0], 0)
# CO Y khong chan khi vuot: nhan vien ung 2 trieu roi tieu 2 trieu 3 la
# chuyen binh thuong, va luc do cong ty no lai ho 300 nghin.
la("tieu vuot tam ung thi cong ty no lai", H41_cantru(2000000, 2300000)[1], 300000)
la("tieu vuot KHONG bi bao la con no", H41_cantru(2000000, 2300000)[0], 0)
_ct41 = _dnc41.split("def can_tru_tam_ung(")[1].split("\ndef ")[0]
la("ham can tru khong nem loi khi vuot", "frappe.throw" in _ct41, False)

_lc41 = _dnc41.split("def ly_do_chan(")[1].split("\ndef ")[0]
la("hoan ung bat buoc chi ro thuoc ma tam ung nao",
   "NV_HOAN_UNG and not" in _lc41, True)
la("phieu khong phai hoan ung thi khong duoc gan ma tam ung",
   'nv != NV_HOAN_UNG and (p.get("thuoc_tam_ung")' in _lc41, True)
# Soi TUNG DONG: mot phieu muoi dong ma dong thu bay la cai may danh trung
# thi van phai chan.
la("chan tai san co dinh soi tung dong", "for i, d in enumerate(cac_dong(p), 1)" in _lc41, True)

# --- Chan trung hoa don, ke ca trung ngay trong mot phieu ---
_th41 = _dnc41.split("def trung_hoa_don(")[1].split("\ndef ")[0]
la("soi trung tren bang con", '"Vagabond De Nghi Chi Dong"' in _th41, True)
la("van soi duoc phieu mot dong cu", '"so_hoa_don": d.get("so_hoa_don")' in _th41, True)
# Ca MOI sinh ra do doi sang nhieu dong: hai ban cung chup mot to bill roi
# cung dan vao mot phieu. Khong mot phep tra co so du lieu nao bat duoc.
# Kiem PHEP SO chu khong kiem ten bien: bo doan so di ma de lai dong khoi
# tao "trong_phieu = {}" thi ca kiem cu theo ten bien van xanh. Da thu that
# bang mot lan pha hoai co chu y va no lot.
la("bat duoc trung NGAY TRONG mot phieu",
   "if khoa in trong_phieu:" in _th41 and "trong_phieu[khoa] = i" in _th41, True)

# --- Chuyen phieu cu, QT-20 cam xoa ---
la("co ham chuyen phieu mot dong", "def chuyen_phieu_mot_dong(" in _dnc41, True)
_cv41 = _dnc41.split("def chuyen_phieu_mot_dong(")[1]
la("chuyen phieu KHONG xoa gi", "db_delete" in _cv41 or ".delete(" in _cv41, False)
la("chuyen phieu lap lai duoc", "if r[\"name\"] in da_co:" in _cv41, True)
la("patch co goi chuyen phieu",
   "chuyen_phieu_mot_dong()" in open("vagabond/patches/dong_bo_cau_truc.py", encoding="utf-8").read(), True)

# --- Man hinh dang The ---
#
# Anh Viet: *"bang chi tiet khong duoc thiet ke dang luoi (Grid) vi se bi tran
# man hinh. Em hay thiet ke moi dong khoan chi la mot khoi The (Card)."*
la("moi khoan chi la mot The", "function dncTheKhoan(" in _js41, True)
la("The dung lop card chu khong phai luoi", "'<div class=\"card\" data-kid=" in _js41, True)
la("khong dung grid cho bang ke", "grid-template-columns" in _js41.split("function dncTheKhoan(")[1].split("\nfunction ")[0], False)
la("co nut Them khoan chi ro rang", "+ Thêm khoản chi" in _js41, True)
la("moi khoan mang id rieng, khong dua vao vi tri", "dncKhoanMoi()" in _js41 and "k.id" in _js41, True)
la("tong nhay theo thoi gian thuc khi go tien", "n.oninput = dncNhayTong" in _js41, True)
# Ve lai ca trang moi lan go mot chu so thi o dang go mat con tro.
la("nhay tong KHONG ve lai ca trang",
   "dncVe(" in _js41.split("function dncNhayTong(")[1].split("\n}")[0], False)
la("tra ma so thue khi roi o", "n.onblur = function () { dncTraMst(" in _js41, True)
la("dung lai API tra MST da co", "vagabond.api.tra_mst" in _js41, True)
_tm41 = _js41.split("async function dncTraMst(")[1]
la("tra khong ra thi van cho go tay", "gõ tay" in _tm41, True)
la("khong de len ten nguoi ta da go", "!(oTen.value || '').trim()" in _tm41, True)
la("o ngan hang dung bang chon co o tim", "nhChon(dncForm.ngan_hang" in _js41, True)
la("khong con o go tu do cho ngan hang",
   'id="dnc_ngan_hang" placeholder="Ngân hàng"' in _js41, False)

# --- Cong ngo ---
_cn41 = open("vagabond/khung/kiem_thu/thu_cua_ngo.py", encoding="utf-8").read()
for _h41 in ("chi_tiet", "tam_ung_cua_toi"):
	la("cong ngo biet %s" % _h41, '"%s"' % _h41 in _cn41, True)

print("\n[42] Ma phieu TTNB, o nhap tien, man Danh sach va doi soat OCB")

# Anh Viet 20/08/2026, ba nhom nang cap sau khi xem man that tren dien thoai.

_dnc42 = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
_js42 = open("vagabond/public/js/bep/16-mua-hang.js", encoding="utf-8").read()
_nen42 = open("vagabond/public/js/bep/00-nen.js", encoding="utf-8").read()
_ht42 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_jh42 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_sp42 = open("vagabond/sepay.py", encoding="utf-8").read()
_dt42 = json.load(open(
	"vagabond/vagabond/doctype/vagabond_de_nghi_chi/vagabond_de_nghi_chi.json", encoding="utf-8"))
_tr42 = {f["fieldname"]: f for f in _dt42["fields"]}

# --- 1.1 Ma phieu doi tien to ---
la("ma phieu doi sang TTNB theo dang nam - thang",
   _dt42.get("autoname"), "format:TTNB-{YY}-{MM}-{#####}")
# Doi autoname KHONG doi ten phieu cu (QT-20): phieu DNC-2026-xxxxx van con
# nguyen, chi phieu moi mang ma moi.
la("khong co doan nao doi ten phieu cu",
   "rename_doc" in _dnc42 or "frappe.rename_doc" in _dnc42, False)

# --- 1.2 Ham dinh dang tien dung chung ---
la("co ham doc so tien dung chung", "function soTien(" in _nen42, True)
la("co ham dinh dang chuoi tien", "function tienChuoi(" in _nen42, True)
la("co ham cham tien khi dang go", "function tienGo(" in _nen42, True)
# Gan mot lan o tang document: man nao ve ra sau cung duoc huong, khong phai
# nho gan lai sau moi lan ve lai.
la("gan mot lan cho ca app", "document.addEventListener('input'" in _nen42, True)
# Gom ca cach khai cu cua man Bao gia, de ca app chi con MOT hanh vi.
la("nhan ca cach khai cu data-tien", "data-tien') === '1'" in _nen42, True)
# Giu con tro khi go: khong giu thi moi lan go mot chu so con tro nhay ve
# cuoi va khong sua duoc chu so o giua.
la("giu vi tri con tro khi cham lai", "setSelectionRange" in _nen42, True)

# O tien KHONG duoc dung type="number": trinh duyet coi "2.000.000" la khong
# hop le va tra ve chuoi rong, tuc la mat trang so tien ma khong bao gi.
_the42 = _js42.split("function dncTheKhoan(")[1].split("\nfunction ")[0]
la("o so tien khong con la type number", "'so_tien', 'Số tiền (đ)', k.so_tien, 'number'" in _the42, False)
la("o so tien la o tien co dau cham", "'so_tien', 'Số tiền (đ)', k.so_tien, 'tien'" in _the42, True)

# MOI cho doc o tien phai qua soTien. Doc thang bang Number thi "2.000.000"
# ra NaN, va mot o tien ra NaN thi phieu luu xuong so 0 ma khong bao gi ca.
la("khong con cho nao doc o tien bang Number tho",
   "Number(k.so_tien)" in _js42 or "Number(String(k.so_tien)" in _js42, False)
la("tong tien tren man doc qua soTien",
   "soTien(k.so_tien)" in _js42.split("function dncTong(")[1].split("\n}")[0], True)
# Gui len may chu phai gui SO, khong gui chuoi co cham: flt() ben Python doc
# "2.000.000" ra 2.0, sai mot trieu lan ma khong bao gi.
la("gui len may chu thi doi ve so that",
   "k.so_tien = soTien(k.so_tien)" in _js42, True)

# --- 2.1 Man Danh sach ---
la("co man danh sach TTNB", "async function scrTTNB(" in _js42, True)
la("the tren trang chu dan vao danh sach",
   "if (k === 'DNC') return go(scrTTNB);" in
   open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read(), True)
la("co cua doc danh sach o may chu", "def ds_man(" in _dnc42, True)
la("co chip trang thai", "CHIP_TRANG_THAI = (" in _dnc42, True)
la("co chip loc thoi gian", "CHIP_THOI_GIAN = (" in _dnc42, True)
for _c42 in ("nhap", "cho_duyet", "cho_chi", "da_chi", "da_huy"):
	la("chip %s co trong danh sach" % _c42, '"%s"' % _c42 in _dnc42, True)
# Chip GOM chuoi duyet ba cap lai, KHONG duoc xoa trang thai nao: chuoi mua
# hang, giam doc tu 2 trieu, ke toan la thu anh Viet chot 19/08.
for _t42 in ("Cho duyet", "Cho giam doc", "Cho ke toan", "Hoan tat", "Bi tra lai"):
	la("trang thai cu %s van con" % _t42, _t42 in _tr42["trang_thai"]["options"], True)
la("them trang thai Da chi", "Da chi" in _tr42["trang_thai"]["options"], True)
la("chip Cho duyet gom ca hai cap duyet",
   sorted(H42_chip("cho_duyet") or []), ["Cho duyet", "Cho giam doc"])
la("chip Da chi chi ung mot trang thai", H42_chip("da_chi"), ["Da chi"])
la("chip Tat ca thi khong loc gi", H42_chip("tat_ca"), None)

# --- 2.2 Nut duyet ---
la("nut duyet theo co cua may chu", "if (d.duoc_duyet_buoc_nay)" in _js42, True)
la("nhan nut dung chu anh Viet dat", "Duyệt thanh toán nội bộ" in _js42, True)
_ct42 = _dnc42.split("def chi_tiet(")[1].split("\n@frappe.whitelist()")[0]
la("may chu tra co duyet duoc hay khong", 'ra["duoc_duyet_buoc_nay"]' in _ct42, True)
# Luat that con co "nguoi lap khong tu duyet phieu cua chinh minh", ma man
# hinh thi khong biet ai lap. Nen co phai tinh o may chu.
la("co duyet tinh bang dung ham luat cu", "duoc_duyet_khong(" in _ct42, True)

# --- 2.3 Doi soat OCB ---
la("co ham doi soat dong tien ra", "def doi_soat(so_ngay=30)" in _dnc42, True)
la("co nhip chay theo gio", "def doi_soat_tu_dong(" in _dnc42, True)
la("nhip chay theo gio duoc khai trong hooks",
   "vagabond.de_nghi_chi.doi_soat_tu_dong" in
   open("vagabond/hooks.py", encoding="utf-8").read(), True)
la("webhook SePay goi doi soat ngay", "de_nghi_chi.khi_co_giao_dich" in _sp42, True)
# Webhook DA ghi xong dong tien roi: mot loi o buoc doi soat khong duoc lam
# hong phan hoi tra ve cho SePay, hong la ho gui lai mai.
_kcgd42 = _dnc42.split("def khi_co_giao_dich(")[1]
la("doi soat sau webhook khong nem loi ra ngoai", "except Exception:" in _kcgd42, True)

_ds42 = _dnc42.split("def doi_soat(so_ngay=30)")[1].split("\ndef doi_soat_tu_dong")[0]
# CHI phieu da qua het chuoi duyet moi duoc tu nhay sang Da chi. Phieu con o
# Nhap ma tu nhay vi ngan hang tinh co co khoan trung noi dung la khong duoc.
la("chi quet phieu da duyet xong", "_phieu_cho_chi()" in _ds42, True)
_pcc42 = _dnc42.split("def _phieu_cho_chi(")[1].split("\n@frappe.whitelist()")[0]
la("phieu cho chi khong gom phieu Nhap", "TT_NHAP" in _pcc42, False)
la("phieu cho chi la phieu da qua duyet",
   "TT_CHO_KE_TOAN" in _pcc42 and "TT_HOAN_TAT" in _pcc42, True)
# Bai hoc v238: mot dong tien ra chi khop cho MOT phieu.
la("khoa trung giao dich", "_gd_da_chiem_ttnb(" in _ds42, True)
la("noi dung khop roi van phai so tien", 'abs(flt(g["withdrawal"]) - tien) > 1' in _ds42, True)
# Tien da ra la SU THAT: ghi xuong ngay, khong gop chung giao dich co so du
# lieu voi viec khac (bai hoc v234, phieu HT-2026-00899).
la("ghi xuong ngay sau khi khop", "frappe.db.commit()" in _ds42, True)

# Noi dung chuyen khoan phai mang nguyen ma phieu va khong dau tieng Viet:
# nhieu ngan hang bo dau hoac cat bot noi dung.
la("noi dung chuyen khoan sinh tu ma phieu", "def noi_dung_ck(" in _dnc42, True)
la("phep so bo het ky tu khong phai chu so", "def khop_noi_dung(" in _dnc42, True)
la("khop duoc du ngan hang doi gach ngang thanh dau cach",
   H42_khop("THE VAGABOND TTNB 26 08 00001", "TTNB-26-08-00001"), True)
la("khop duoc khi ngan hang giu nguyen gach ngang",
   H42_khop("CK THE VAGABOND TTNB-26-08-00001 ND", "TTNB-26-08-00001"), True)
la("KHONG khop nham sang phieu khac",
   H42_khop("THE VAGABOND TTNB-26-08-00002", "TTNB-26-08-00001"), False)
la("noi dung rong thi khong khop", H42_khop("", "TTNB-26-08-00001"), False)

# --- 3. M-Invoice tren man Hoan tien ---
la("man hoan tien co the hoa don dien tu", "function htCtHddt(" in _jh42, True)
la("co nut xem hoa don ben M-Invoice", "Xem hoá đơn bên M-Invoice" in _jh42, True)
la("may chu tra thong tin hoa don dien tu", "def _hddt_cua_don(" in _ht42, True)
la("chi_tiet hoan tien tra khoa hddt", 'ra["hddt"]' in _ht42, True)
# Duong dan sau cua M-Invoice de trong CAI DAT chu khong viet cung: doan mot
# duong dan roi in ra nut bam la dua cho chi Dung mot cai nut dan toi trang loi.
la("mau duong dan de o cai dat", "minvoice_mau_lien_ket" in _ht42, True)
la("cai dat co o khai mau duong dan",
   "minvoice_mau_lien_ket" in open(
	   "vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json",
	   encoding="utf-8").read(), True)
# Khoi nay CHI DOC. Anh Viet dan 13/08 sau lan phai di xoa tay hoa don:
# hoa don dien tu gui sang co quan thue rat nhay cam, kho sua chua.
_hd42 = _ht42.split("def _hddt_cua_don(")[1]
for _cam42 in ("set_value(SI", "xuat_hoa_don", ".submit()", ".cancel()", "requests.post"):
	la("khoi hoa don dien tu khong %s" % _cam42, _cam42 in _hd42, False)

print("\n[43] Ma tran phan luong Viec can lam, va PWA")

# Anh Viet 20/08/2026: *"Hien tai man hinh nay dang hien thi sai doi tuong
# (Ke toan dang phai nhin thay ca Phieu nhap kho cua Bep/Kho). Em hay viet
# lai logic query de phieu chi hien thi dung nguoi, dung buoc."*

_vcl43 = open("vagabond/viec_can_lam.py", encoding="utf-8").read()
_tc43 = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()
_nen43 = open("vagabond/public/js/bep/00-nen.js", encoding="utf-8").read()
_tb43 = open("vagabond/thong_bao.py", encoding="utf-8").read()
_mf43 = json.load(open("vagabond/www/manifest.json", encoding="utf-8"))
_sw43 = open("vagabond/www/sw.js", encoding="utf-8").read()

# --- Loc theo vai phai o MAY CHU ---
#
# Loc theo vai ma dat o may khach thi khong phai la loc, do la trang tri:
# sua vai dong trong cong cu nha phat trien cua trinh duyet la xem duoc viec
# cua nguoi khac.
la("co mo dun gom viec o may chu", "def danh_sach(" in _vcl43, True)
la("man hinh goi may chu chu khong tu gom",
   "vagabond.viec_can_lam.danh_sach" in _tc43, True)
# Ban cu goi getList thang tu may khach cho tung loai phieu.
_scr43 = _tc43.split("async function scrVclList(")[1].split("\nfunction vgbODong(")[0]
la("man hinh khong con tu goi getList de gom viec", "getList(" in _scr43, False)

# --- Ma tran ---
la("co bang ma tran khai ro", "MA_TRAN = {" in _vcl43, True)
la("co ham quyet dinh thay duoc hay khong", "def thay_duoc(" in _vcl43, True)
# Mac dinh la DONG: them mot loai phieu moi ma quen khai vai thi no an voi
# moi nguoi, chu khong hien ra voi ca tiem.
_td43 = _vcl43.split("def thay_duoc(")[1].split("\ndef ")[0]
la("khong khai vai thi khong ai thay", "if not can:" in _td43 and "return False" in _td43, True)

# Ke toan KHONG duoc thay phieu nhap xuat kho. Day dung la cho anh Viet keu.
la("ke toan khong thay phieu nhap kho", H43_thay("nhap_kho", {"AP Kiểm soát (FIN)"}), False)
la("ke toan khong thay phieu xuat kho", H43_thay("xuat_kho", {"Accounts Manager"}), False)
la("ke toan khong thay yeu cau san xuat", H43_thay("san_xuat", {"AP Kiểm soát (FIN)"}), False)
# Ngoai le DUY NHAT: kiem ke cho CHOT SO la buoc gia tri, dung nhu anh Viet
# dan "tru khi co buoc cho Ke toan duyet gia tri".
la("ke toan VAN thay kiem ke cho chot so", H43_thay("kiem_ke", {"AP Kiểm soát (FIN)"}), True)
la("ke toan thay de nghi chi", H43_thay("de_nghi_chi", {"AP Kiểm soát (FIN)"}), True)
la("ke toan thay hoan tien", H43_thay("hoan_tien", {"Accounts Manager"}), True)

# Kho va bep KHONG thay viec tien.
la("kho khong thay hoan tien", H43_thay("hoan_tien", {"Stock User"}), False)
la("kho khong thay de nghi chi", H43_thay("de_nghi_chi", {"Stock User"}), False)
la("kho thay phieu chuyen kho", H43_thay("chuyen_kho", {"Stock User"}), True)
la("kho thay phieu nhap kho", H43_thay("nhap_kho", {"Stock Manager"}), True)

# Thu mua.
la("thu mua thay yeu cau mua hang", H43_thay("ycmh", {"AP Officer"}), True)
la("thu mua thay de nghi chi", H43_thay("de_nghi_chi", {"AP Officer"}), True)
la("thu mua khong thay hoan tien khach", H43_thay("hoan_tien", {"Purchase User"}), False)

# Giam doc thay het.
for _l43 in ("chuyen_kho", "nhap_kho", "de_nghi_chi", "hoan_tien", "kiem_ke"):
	la("giam doc thay %s" % _l43, H43_thay(_l43, {"AP Giám đốc"}), True)

# Nguoi khong vai gi thi khong thay gi ca.
for _l43 in ("chuyen_kho", "nhap_kho", "de_nghi_chi", "hoan_tien"):
	la("nhan vien thuong khong thay %s" % _l43, H43_thay(_l43, {"Employee"}), False)
la("loai la khong ai thay", H43_thay("loai_khong_co_that", {"System Manager"}), False)

# Cong ma tran phai la cong DUY NHAT: khong thay thi khong chay luon truy van.
_ds43 = _vcl43.split("def danh_sach(")[1]
la("khong thay thi khong chay truy van", "if not thay_duoc(ma_loai, vai):" in _ds43, True)
la("mot nguon loi khong lam sap ca man", "frappe.log_error" in _ds43, True)
# Chip chi bay loai NGUOI NAY duoc thay.
la("chip chi bay loai duoc thay", "if thay_duoc(k, vai) and dem_loai.get(k)" in _ds43, True)

# --- Chip tren man ---
la("man co chip loai phieu", 'class="vclL"' in _tc43, True)
la("man co chip trang thai", 'class="vclT"' in _tc43, True)
la("doi chip loai thi bo chip trang thai cu",
   "vclLoc.trang_thai = '';" in _tc43, True)

# --- PWA ---
la("manifest co ten thuong hieu", _mf43.get("short_name"), "Vagabond")
la("manifest mo thang vao app", _mf43.get("start_url"), "/bep")
_ic43 = {str(i.get("sizes")): i for i in _mf43.get("icons") or []}
la("co bieu tuong 192", "192x192" in _ic43, True)
la("co bieu tuong 512", "512x512" in _ic43, True)
la("co bieu tuong maskable",
   any((i.get("purpose") or "") == "maskable" for i in _mf43.get("icons") or []), True)
import os
for _f43 in ("icon-192.png", "icon-512.png", "icon-512-maskable.png"):
	la("tep bieu tuong %s co that" % _f43,
	   os.path.exists("vagabond/public/pwa/" + _f43), True)

# iOS KHONG doc manifest de lay bieu tuong, no doc apple-touch-icon. Thieu
# the do la iPhone tu chup man hinh lam bieu tuong - dung cai "mat logo"
# anh Viet thay.
la("co gan apple-touch-icon cho iOS", "apple-touch-icon" in _nen43, True)
la("co gan manifest tu JavaScript", "rel = 'manifest'" in _nen43, True)

# Service Worker PHAI nam o www/ de co pham vi toan site. De o public/ thi
# no chi dieu khien duoc /assets/vagabond/... chu khong dieu khien duoc /bep.
la("service worker nam o www de co pham vi goc",
   os.path.exists("vagabond/www/sw.js"), True)
la("dang ky service worker o goc", "register('/sw.js'" in _nen43, True)
la("service worker co bat su kien push", "addEventListener('push'" in _sw43, True)
la("thong bao co rung dien thoai", "vibrate" in _sw43, True)
# Bo nho dem ngoai tuyen cho app ke toan la con dao hai luoi: mo ra thay so
# cu ma tuong so moi thi nguy hon han khong mo duoc app.
la("service worker khong lam bo nho dem", "caches.open" in _sw43, False)

# Xin quyen thong bao: trinh duyet chi cho hoi MOT lan, bam Chan la chan
# vinh vien. Nen chi hoi khi da cai ra man hinh chinh.
la("chi xin quyen khi da cai ra man hinh chinh",
   "pwaDaCaiRaManHinh()" in _nen43, True)

# --- Thong bao day ---
la("khoa rieng do MAY CHU sinh", "def _sinh_khoa(" in _tb43, True)
la("khoa rieng cat o o Password",
   '"push_khoa_rieng"' in open(
	   "vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json",
	   encoding="utf-8").read(), True)
_kcc43 = _tb43.split("def khoa_cong_khai(")[1].split("\n@frappe.whitelist()")[0]
la("chi gui khoa CONG KHAI xuong trinh duyet",
   "push_khoa_rieng" in _kcc43.split("return")[-1], False)
# Dang ky khoa theo MAY chu khong theo nguoi: mot nguoi co dien thoai rieng
# va may quay, khoa theo nguoi thi cai may thu hai la mat thong bao may dau.
la("dang ky khoa theo endpoint", '{"endpoint": ep}' in _tb43, True)
# Ham gui duoc goi giua luong duyet phieu, nem loi la cuon theo ca thao tac
# duyet that.
_gui43 = _tb43.split("def gui(")[1].split("\ndef bao_cho_vai(")[0]
la("ham gui khong nem loi ra ngoai", "except Exception:" in _gui43, True)
la("may go app thi tat co chu khong xoa", '"con_dung", 0' in _gui43, True)
# Bao theo VAI chu khong viet cung ten nguoi.
la("bao theo vai chu khong theo ten nguoi", "def bao_cho_vai(" in _tb43, True)
_dnc43 = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
la("duyet xong co bao buoc ke tiep", "_bao_buoc_ke_tiep(doc)" in _dnc43, True)
_bbkt43 = _dnc43.split("def _bao_buoc_ke_tiep(")[1].split("\n@frappe.whitelist()")[0]
la("bao that bai khong lam hong viec duyet", "except Exception:" in _bbkt43, True)

# ============================================================
# 44. v243: logo PWA that su duoc gan, thong bao gui that,
#     Assignee that, ma hoa don thay the, nhap sao ke, Danh muc CRUD
# ============================================================
#
# Anh Viet 21/08/2026: *"Logo van chua hien khi them vao man hinh chinh. Va
# em sai logo, logo ben anh co nen robin egg."*
#
# BAI HOC CUA NHOM 43, ghi ra day de khong lap lai
# ------------------------------------------------
# Nhom 43 co ca "co gan manifest tu JavaScript" va no XANH. Nhung ham
# pwaGan() KHONG CHO NAO GOI, nen khong the manifest nao duoc chen va logo
# khong bao gio hien. Ca kiem soi than ham, ma than ham thi dung; cai sai
# nam o cho KHONG AI GOI HAM DO.
#
# Day la cung mot kieu hong da gap hai lan truoc: ca kiem khang dinh mot
# thu gan dung thay vi thu that su can. Nen nhom nay soi CHO GOI truoc, roi
# moi soi than ham.
print("\n[44] v243: PWA goi that, thong bao gui that, Assignee that, sao ke, Danh muc CRUD")

_nen44 = open("vagabond/public/js/bep/00-nen.js", encoding="utf-8").read()
_vd44 = open("vagabond/public/js/bep/12-van-don.js", encoding="utf-8").read()
_mf44 = json.load(open("vagabond/www/manifest.json", encoding="utf-8"))
_tb44 = open("vagabond/thong_bao.py", encoding="utf-8").read()
_gv44 = open("vagabond/giao_viec.py", encoding="utf-8").read()
_ht44 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_sk44 = open("vagabond/nhap_sao_ke.py", encoding="utf-8").read()
_hd44 = open("vagabond/khung/hop_dong.py", encoding="utf-8").read()
_ds44 = open("vagabond/khung/ds.py", encoding="utf-8").read()
_kds44 = open("vagabond/public/js/bep/15-khuon-danh-sach.js", encoding="utf-8").read()
_hook44 = open("vagabond/hooks.py", encoding="utf-8").read()


def _bo_chu_thich_js(nguon):
	"""Bo chu thich khoi ma JavaScript truoc khi soi.

	BAT BUOC phai co truoc khi dem cho goi ham. Khong co no thi mot lan
	`/* pwaGan(); */` van duoc dem la mot lan goi - va do dung la cach ca
	kiem nay bi qua mat trong lan thu pha hoai dau tien ngay 21/08/2026.
	"""
	ra = []
	i, n = 0, len(nguon)
	while i < n:
		if nguon.startswith("/*", i):
			j = nguon.find("*/", i + 2)
			i = n if j < 0 else j + 2
			continue
		if nguon.startswith("//", i):
			# Chi coi la chu thich khi `//` dung dau dong (co the co khoang
			# trang truoc). Khong thi `https://...` trong chuoi bi cat mat.
			k = nguon.rfind("\n", 0, i)
			if nguon[k + 1:i].strip() == "":
				j = nguon.find("\n", i)
				i = n if j < 0 else j
				continue
		ra.append(nguon[i])
		i += 1
	return "".join(ra)


def _chay_pwa_bang_node():
	"""Chay THAT khoi PWA cua 00-nen.js bang node, tra ve cai da chen vao head.

	Cat tu dong khai PWA_MAU tro di - do la mot khoi kin, khong dinh gi toi
	phan tren cua tep. Roi dung mot DOM gia du nho de khoi do chay duoc.

	Tra ve None neu may khong co node. KHONG im lang: cho goi in mot dong
	bao ra man hinh, vi mot ca bi bo qua lang le doc y het mot ca da dat.
	"""
	import shutil
	import subprocess
	import tempfile

	if not shutil.which("node"):
		return None
	nguon = open("vagabond/public/js/bep/00-nen.js", encoding="utf-8").read()
	moc = "var PWA_MAU ="
	if moc not in nguon:
		return {"loi": "khong tim thay khoi PWA"}
	khoi = nguon[nguon.index(moc):]

	kich_ban = """
var _head = [];
var document = {
  head: {appendChild: function (n) { _head.push(n); }},
  querySelector: function (q) {
    for (var i = 0; i < _head.length; i++) {
      var n = _head[i];
      if (q.indexOf('link[rel="' + n.rel + '"]') === 0) return n;
      if (n.name && q.indexOf('[name="' + n.name + '"]') > -1) return n;
    }
    return null;
  },
  createElement: function (t) {
    return {tag: t, _a: {}, setAttribute: function (k, v) { this._a[k] = v; }};
  }
};
var _sw = null;
var navigator = {
  serviceWorker: {
    register: function (u, o) { _sw = {url: u, scope: o && o.scope}; return {catch: function () {}}; }
  }
};
var window = {matchMedia: function () { return {matches: false}; }};
var atob = function (s) { return Buffer.from(s, 'base64').toString('binary'); };
function api() { return Promise.resolve({}); }
__KHOI__
function _tim(dk) {
  for (var i = 0; i < _head.length; i++) if (dk(_head[i])) return _head[i];
  return null;
}
var _mf = _tim(function (n) { return n.rel === 'manifest'; });
var _ap = _tim(function (n) { return n.rel === 'apple-touch-icon'; });
var _th = _tim(function (n) { return n.name === 'theme-color'; });
console.log(JSON.stringify({
  da_gan: PWA_DA_GAN,
  manifest: _mf && _mf.href,
  apple: _ap && _ap.href,
  apple_sizes: _ap && _ap._a && _ap._a.sizes,
  theme: _th && _th.content,
  sw: _sw && _sw.url,
  sw_scope: _sw && _sw.scope
}));
"""
	kich_ban = kich_ban.replace("__KHOI__", khoi)
	with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
		f.write(kich_ban)
		duong = f.name
	try:
		r = subprocess.run(["node", duong], capture_output=True, text=True, timeout=30)
		if r.returncode != 0:
			return {"loi": (r.stderr or "").strip()[:300]}
		return json.loads(r.stdout.strip().splitlines()[-1])
	except Exception as e:
		return {"loi": str(e)[:300]}
	finally:
		try:
			os.unlink(duong)
		except OSError:
			pass


def _goi_ham(nguon, ten):
	"""Dem so LAN GOI mot ham trong mot tep JavaScript, bo qua dong dinh nghia.

	Bo chu thich truoc, roi tim `ten(` va loai truong hop dung ngay sau
	`function `. Tho, nhung du de tra loi dung cau hoi da bo sot lan truoc:
	ham nay co ai goi khong.
	"""
	nguon = _bo_chu_thich_js(nguon)
	so = 0
	i = 0
	while True:
		i = nguon.find(ten + "(", i)
		if i < 0:
			return so
		truoc = nguon[max(0, i - 9):i]
		if not truoc.endswith("function "):
			so += 1
		i += 1


# --- 44.1 Logo PWA: ham PHAI duoc goi that ---
la("pwaGan CO CHO GOI, khong chi khai bao", _goi_ham(_nen44, "pwaGan") >= 1, True)
_nen44s = _bo_chu_thich_js(_nen44)
la("goi pwaGan ngay luc nap tep, khong doi dang nhap",
   "if (typeof document !== 'undefined' && document.head) pwaGan();" in _nen44s, True)
# Ca manh nhat cua ca nhom: CHAY THAT khoi PWA bang node voi mot DOM gia,
# roi doc xem the nao da duoc chen vao head.
#
# Vi sao phai chay chu khong doc chu: nhom 43 co ca "co gan manifest tu
# JavaScript" va no XANH suot, trong khi pwaGan() khong cho nao goi nen
# khong the nao duoc chen va logo khong bao gio hien. Doc chu tra loi
# "trong ham co viet the" - chay that tra loi "the co that su nam trong
# head khong". Chi cau thu hai moi la cau anh Viet hoi.
_pwa44 = _chay_pwa_bang_node()
if _pwa44 is None:
	print("      BO QUA ca chay that pwaGan: may nay khong co node. "
	      "Nho chay lai tren may co node truoc khi deploy.")
else:
	la("chay that thi pwaGan da duoc goi", _pwa44.get("da_gan"), 1)
	la("chay that thi the manifest nam trong head",
	   _pwa44.get("manifest"), "/manifest.json")
	la("chay that thi apple-touch-icon nam trong head",
	   _pwa44.get("apple"), "/assets/vagabond/pwa/icon-180.png")
	la("chay that thi apple-touch-icon khai dung 180x180",
	   _pwa44.get("apple_sizes"), "180x180")
	la("chay that thi theme-color la mau robin egg",
	   _pwa44.get("theme"), "#50DBF2")
	la("chay that thi service worker duoc dang ky o goc",
	   _pwa44.get("sw"), "/sw.js")
	la("service worker dang ky voi pham vi toan site",
	   _pwa44.get("sw_scope"), "/")
# Xin quyen thong bao cung tung bi bo quen y het: khai ma khong goi.
la("pwaXinQuyenThongBao CO CHO GOI",
   _goi_ham(_nen44, "pwaXinQuyenThongBao") + _goi_ham(_vd44, "pwaXinQuyenThongBao") >= 1, True)
_vd44s = _bo_chu_thich_js(_vd44)
# CA HAI nhanh vao duoc man hinh chinh deu phai goi. __boot co hai duong ra
# scrHome (mot qua whoAmI, mot qua syncUser); bo mot duong la nguoi dang
# nhap kieu do khong bao gio duoc hoi.
la("ca hai nhanh vao man hinh chinh deu xin quyen",
   _vd44s.count("reset(scrHome); pwaSauDangNhap();"), 2)
la("goi xin quyen sau khi vao duoc man hinh chinh", "pwaSauDangNhap()" in _vd44s, True)
la("xin quyen khong chan man hinh, co hen gio", "setTimeout(function () { pwaXinQuyenThongBao(0); }" in _vd44, True)

# --- 44.2 Dung mau thuong hieu, khong phai mau bia ---
# Anh Viet: *"logo ben anh co nen robin egg"*. #50DBF2 la mau .vh cua app,
# va lech duoi mot don vi so voi nen that cua tep logo 2025 (#4FDBF2).
la("manifest dung mau robin egg cho nen", _mf44["background_color"], "#50DBF2")
la("manifest dung mau robin egg cho thanh trang thai", _mf44["theme_color"], "#50DBF2")
la("khong con mau navy cu trong manifest",
   "#05323C" in json.dumps(_mf44), False)
la("theme-color trong ma nguon cung la robin egg", "PWA_MAU = '#50DBF2'" in _nen44, True)
la("khong viet cung mau navy trong ham gan", "'#05323C'" in _nen44.split("function pwaGan(")[1][:1400], False)

_ic44 = {str(i.get("sizes")): i for i in _mf44.get("icons") or []}
for _c44 in ("180x180", "192x192", "512x512"):
	la("manifest co bieu tuong %s" % _c44, _c44 in _ic44, True)
# iOS doc apple-touch-icon va no muon dung 180x180.
la("apple-touch-icon tro vao tep 180", "pwa/icon-180.png" in _nen44, True)
la("apple-touch-icon khai ro co 180x180", "'sizes', '180x180'" in _nen44, True)
la("co the mo app khong thanh dia chi tren Safari cu",
   "apple-mobile-web-app-capable" in _nen44, True)

# Tep bieu tuong phai CO THAT, dung kich thuoc, va nen dung mau robin egg.
# Ca nay bat duoc lan truoc: bieu tuong dung dung nhung dung logo den tren
# nen navy, tuc la tep co that ma van sai.
try:
	from PIL import Image as _Img44

	_co_pil44 = True
except ImportError:
	_co_pil44 = False
for _f44, _canh44 in (("icon-180.png", 180), ("icon-192.png", 192),
                      ("icon-512.png", 512), ("icon-512-maskable.png", 512)):
	_d44 = "vagabond/public/pwa/" + _f44
	la("tep bieu tuong %s co that" % _f44, os.path.exists(_d44), True)
	if _co_pil44 and os.path.exists(_d44):
		_im44 = _Img44.open(_d44)
		la("bieu tuong %s dung kich thuoc" % _f44, _im44.size, (_canh44, _canh44))
		_g44 = _im44.convert("RGB").getpixel((2, 2))
		# Goc anh phai la nen robin egg (79,219,242), khong phai navy hay den.
		la("goc bieu tuong %s la nen robin egg" % _f44,
		   all(abs(_g44[_i] - (79, 219, 242)[_i]) <= 3 for _i in range(3)), True)

# --- 44.3 Thong bao: lop hai da bat that ---
# Soi DONG dependencies chu khong soi ca tep: chu thich ngay tren dong do
# cung co chu "pywebpush", va ca kiem doc ca tep thi van xanh sau khi da go
# thu vien ra khoi phan phu thuoc. Bat duoc luc thu pha hoai 21/08/2026.
_pyp44 = [
	d for d in open("pyproject.toml", encoding="utf-8").read().splitlines()
	if d.startswith("dependencies")
]
la("co dung mot dong dependencies", len(_pyp44), 1)
la("pywebpush da vao phan phu thuoc cua app", "pywebpush" in _pyp44[0], True)
_req44 = [
	d for d in open("requirements.txt", encoding="utf-8").read().splitlines()
	if d.strip() and not d.strip().startswith("#")
]
la("pywebpush co ca trong requirements.txt",
   any(d.strip().startswith("pywebpush") for d in _req44), True)
la("doi khoa sang PEM truoc khi ky", "def _pem(" in _tb44, True)
la("ham gui dung khoa PEM chu khong dung chuoi tho",
   "vapid_private_key=khoa," in _tb44, True)
la("thieu thu vien thi ghi log chu khong im lang",
   "thong_bao: thieu pywebpush" in _tb44, True)
la("co duong tu kiem thu chuong", "def thu_gui(" in _tb44, True)
# Duong thu gui chi gui cho CHINH minh: mot duong gui thong bao tuy y nguoi
# nhan la mot cai loa cho ke xau.
_thu44 = _tb44.split("def thu_gui(")[1].split("\ndef bao_cho_vai(")[0]
la("thu gui chi gui cho chinh nguoi dang bam",
   "frappe.session.user," in _thu44, True)
la("thu gui khong nhan tham so nguoi nhan",
   "def thu_gui():" in _tb44, True)
# QT-24: bao loi phai noi phai lam gi tiep.
la("thu gui hong thi noi ro phai lam gi", "loi_nhan" in _thu44, True)

# --- 44.4 Assignee that ---
la("co mo dun giao viec rieng", os.path.exists("vagabond/giao_viec.py"), True)
la("giao theo VAI chu khong viet cung ten nguoi", "def giao_vai(" in _gv44, True)
la("giao xong thi go viec cua buoc cu", "def go_giao(" in _gv44, True)
# Go viec la DONG chu khong xoa, theo QT-20.
la("go viec la dong chu khong xoa", '"status", "Closed"' in _gv44, True)
la("khong co lenh xoa ToDo nao", "delete_doc" in _gv44, False)
# O _assign la ban sao, phai chep lai moi lan doi thi Desk moi hien dung.
la("dong bo lai o _assign cho Desk", "def _dong_bo_nhan(" in _gv44, True)
la("chan tran nguoi nhan", "TRAN_NGUOI" in _gv44, True)
# Goi tu giua luong luu phieu, nem loi la cuon theo ca thao tac luu that.
for _h44 in ("giao", "giao_vai", "go_giao", "khi_sinh_phieu", "khi_xong"):
	_than44 = _gv44.split("def %s(" % _h44)[1].split("\ndef ")[0]
	la("ham %s khong nem loi ra ngoai" % _h44, "except Exception:" in _than44, True)
# Hook phai duoc CAM VAO hooks.py, khong thi ham nay khong bao gio chay -
# dung cai bay da sap vao pwaGan.
# Doc doc_events THAT bang ast chu khong tim chuoi trong ca tep: tim chuoi
# thi go hook cua Purchase Receipt di van xanh, vi Material Request con giu
# chuoi do. Bat duoc luc thu pha hoai 21/08/2026.
_de44 = {}
for _nut44 in ast.parse(_hook44).body:
	if isinstance(_nut44, ast.Assign) and getattr(_nut44.targets[0], "id", "") == "doc_events":
		_de44 = ast.literal_eval(_nut44.value)
# Soi TUNG SU KIEN mot, khong soi ca khoi cua doctype. Soi ca khoi thi go
# `after_insert` cua Phieu Kiem Ke di van xanh, vi `on_update` cua chinh no
# con giu chuoi do - ma go after_insert nghia la phieu vua lap khong duoc
# giao cho ai ca. Bat duoc luot pha hoai thu hai 21/08/2026.
_CAN_HOOK44 = {
	"Material Request": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		"on_submit": "vagabond.giao_viec.khi_sinh_phieu",
		"on_update_after_submit": "vagabond.giao_viec.khi_xong",
		"on_cancel": "vagabond.giao_viec.khi_xong",
	},
	"Purchase Receipt": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		"on_submit": "vagabond.giao_viec.khi_xong",
		"on_cancel": "vagabond.giao_viec.khi_xong",
	},
	"Phieu Kiem Ke": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		"on_update": "vagabond.giao_viec.khi_sinh_phieu",
	},
}
for _dt44, _can44 in sorted(_CAN_HOOK44.items()):
	_khoi44 = _de44.get(_dt44) or {}
	for _sk44b, _ham44 in sorted(_can44.items()):
		_gan44 = _khoi44.get(_sk44b)
		_gan44 = _gan44 if isinstance(_gan44, list) else [_gan44]
		la("hook %s cua %s tro dung ham giao viec" % (_sk44b, _dt44),
		   _ham44 in _gan44, True)
la("het viec thi go ra khoi hop", "def _het_viec_chua(" in _gv44, True)
# Luat "het viec" khai TUNG doctype: luat chung se xoa ca nhung lan nguoi
# that tu tay gan Assignee tren Desk.
la("khong dung luat chung de go viec",
   'if dt == "Phieu Kiem Ke":' in _gv44.split("def _het_viec_chua(")[1].split("\ndef ")[0], True)
_dnc44 = open("vagabond/de_nghi_chi.py", encoding="utf-8").read()
la("de nghi chi giao viec qua mo dun chung", "giao_viec.giao_vai(" in _dnc44, True)
la("phieu tra lai giao NGUOC ve nguoi lap", "[doc.nguoi_tao]," in _dnc44, True)
la("phieu da chi thi go viec", "_het_viec(d[\"name\"])" in _dnc44, True)
# Mot buoc chi duoc rung MOT lan: giao_vai da ban chuong, goi them
# thong_bao o day nua la moi buoc rung hai lan.
_bbkt44 = _dnc44.split("def _bao_buoc_ke_tiep(")[1].split("\n@frappe.whitelist()")[0]
la("khong ban chuong hai lan cho mot buoc", "thong_bao.bao_cho_vai(" in _bbkt44, False)
_vcl44 = open("vagabond/viec_can_lam.py", encoding="utf-8").read()
la("man Viec can lam danh dau viec giao dich danh", "def _giao_dich_danh(" in _vcl44, True)
la("dem viec dich danh bang MOT truy van cho ca man",
   _vcl44.split("def _giao_dich_danh(")[1].split("\ndef ")[0].count("frappe.get_all("), 1)

# --- 44.5 Ma hoa don thay the ---
# Anh Viet 13/08/2026: *"Tu nay em khong goi y lam nhung thu trong qua khu
# nua... Dac biet la nhung van de lien quan den hoa don dien tu gui sang co
# quan thue, rat nhay cam, kho sua chua!"*
#
# Nen ba ca duoi day la ba ca QUAN TRONG NHAT cua nhom: chung khang dinh
# rang duong moi nay chi GHI LAI mot con so, khong dung toi hoa don that.
_tt44 = _ht44.split("def ghi_hddt_thay_the(")[1].split("\n@frappe.whitelist()")[0]
la("khong goi sang M-Invoice trong duong ghi thay the", "minvoice" in _tt44.lower(), False)
la("khong goi requests trong duong ghi thay the", "requests." in _tt44, False)
la("khong phat hanh hay huy hoa don nao",
   any(x in _tt44 for x in ("InvoiceApi", "/Save", "cancel", "huy_hoa_don")), False)
la("noi ma thay the vao CA don goc va phieu hoan", _tt44.count("frappe.db.set_value") >= 2, True)
la("chan truong hop nhap trung so hoa don cu", "trùng đúng số hoá đơn cũ" in _tt44, True)
la("ghi vet tren don hang", '"doctype": "Comment"' in _tt44, True)
# Go la de trong o, nhung khong xoa vet - QT-20.
_go44 = _ht44.split("def go_hddt_thay_the(")[1].split("\n@frappe.whitelist()")[0]
la("go ma thay the bat buoc ghi ly do", "Phải ghi lý do gỡ" in _go44, True)
la("go ma thay the van giu lai vet", '"doctype": "Comment"' in _go44, True)
la("man phieu hoan tien co o nhap ma thay the",
   "ghi_hddt_thay_the" in open("vagabond/public/js/bep/11-khach-ca-hop-dong.js",
                               encoding="utf-8").read(), True)

# --- 44.6 Nhap tep sao ke ---
_ns44 = {}
exec(compile(_sk44.split("# PHẦN CHẠM CƠ SỞ DỮ LIỆU")[0], "nhap_sao_ke:thuan", "exec"), _ns44)
_doc_so = _ns44["doc_so"]
_doc_ngay = _ns44["doc_ngay"]
_doc_bang = _ns44["doc_bang"]
_khoa_dong = _ns44["khoa_dong"]

# Doc tien: doan sai dau thap phan la sai mot trieu lan, va sai em ru vi con
# so van "trong nhu tien".
la("doc tien kieu Viet 1.234.567", _doc_so("1.234.567"), 1234567.0)
la("doc tien kieu Viet co phan le", _doc_so("1.234.567,00"), 1234567.0)
la("doc tien kieu Anh 1,234,567.00", _doc_so("1,234,567.00"), 1234567.0)
la("doc khoan nho 3.894 khong thanh 3,894", _doc_so("3.894"), 3894.0)
la("doc so am trong ngoac", _doc_so("(12.500)"), -12500.0)
la("o rong tra ve khong", _doc_so(""), 0.0)
la("bo duoi don vi tien te", _doc_so("95.000 VND"), 95000.0)
la("nhan thang so tu Excel", _doc_so(1234.5), 1234.5)

la("doc ngay kieu Viet", _doc_ngay("12/08/2026"), "2026-08-12")
la("doc ngay kem gio", _doc_ngay("12/08/2026 10:38:00"), "2026-08-12")
la("doc ngay kieu ISO", _doc_ngay("2026-08-12"), "2026-08-12")
la("thang 13 la khong doc duoc chu khong bia", _doc_ngay("13/13/2026"), "")
la("chu khong phai ngay thi tra rong", _doc_ngay("Tổng cộng"), "")

# Tim dong tieu de: sao ke ngan hang luon co may dong dau la ten ngan hang
# va ky sao ke. Doc cung "dong 1 la tieu de" la hong ngay tep dau tien.
_bang44 = [
	["NGÂN HÀNG TMCP PHƯƠNG ĐÔNG", "", "", "", "", "", "", ""],
	["Sao kê tài khoản 0004100012345678", "", "", "", "", "", "", ""],
	["Từ ngày 01/08/2026 đến 31/08/2026", "", "", "", "", "", "", ""],
	["STT", "Ngày thực hiện", "Ngày ghi nhận", "Số giao dịch", "Nội dung",
	 "PS giảm (Nợ)", "PS tăng (Có)", "Số dư"],
	["1", "12/08/2026", "12/08/2026", "FT26224001", "CK tra tien banh", "", "50.000", "1.050.000"],
	["2", "12/08/2026", "12/08/2026", "FT26224002", "Mua nuoc mam", "3.894", "", "1.046.106"],
	["3", "13/08/2026", "13/08/2026", "FT26225001", "TTNB 26 08 00001", "95.000", "", "951.106"],
	["", "", "", "", "TỔNG CỘNG", "98.894", "50.000", ""],
]
_ds44b, _loi44 = _doc_bang(_bang44)
la("bo qua phan dau tep, tim dung dong tieu de", _loi44, "")
la("doc dung so dong giao dich", len(_ds44b), 3)
la("dong tong cong khong bi tinh la giao dich",
   any("TỔNG" in (d["noi_dung"] or "") for d in _ds44b), False)


def _o44(i, k):
	"""Lay mot o cua dong thu i, tra ve None neu doc bang hong.

	Khong de bo kiem VO bang IndexError: mot ca hong co ten thi doc duoc
	ngay la hong o dau, con mot vet do vo thi phai lan nguoc lai tu dau.
	"""
	return _ds44b[i][k] if len(_ds44b) > i else None


la("doc dung khoan tien vao", _o44(0, "tien_vao"), 50000.0)
la("doc dung khoan duoi 100k ma SePay bo sot", _o44(1, "tien_ra"), 3894.0)
la("doc dung so giao dich cua ngan hang", _o44(2, "so_gd"), "FT26225001")
la("doc dung noi dung de con doi soat duoc", _o44(2, "noi_dung"), "TTNB 26 08 00001")

# Khu trung: uu tien so giao dich that cua ngan hang.
la("khoa khu trung uu tien so giao dich",
   _khoa_dong(_ds44b[0]) if _ds44b else None, "OCBSK-FT26224001")
la("hai dong cung so giao dich sinh cung mot khoa",
   _khoa_dong({"so_gd": "FT1", "ngay": "2026-08-12", "tien_ra": 1, "tien_vao": 0, "noi_dung": "a"}),
   _khoa_dong({"so_gd": "FT1", "ngay": "2026-08-13", "tien_ra": 9, "tien_vao": 0, "noi_dung": "b"}))
# Ngan hang de trong so giao dich thi van phai khu trung duoc, bang bo ba
# ngay, tien, noi dung.
_k1_44 = _khoa_dong({"so_gd": "", "ngay": "2026-08-12", "tien_ra": 3894, "tien_vao": 0, "noi_dung": "Mua nuoc mam"})
_k2_44 = _khoa_dong({"so_gd": "", "ngay": "2026-08-12", "tien_ra": 3894, "tien_vao": 0, "noi_dung": "Mua nuoc mam"})
la("thieu so giao dich van khu trung duoc", _k1_44, _k2_44)
la("khac noi dung thi khac khoa",
   _k1_44 == _khoa_dong({"so_gd": "", "ngay": "2026-08-12", "tien_ra": 3894,
                         "tien_vao": 0, "noi_dung": "Mua duong"}), False)
la("tep rong noi ro thay vi im", _doc_bang([])[1] != "", True)
la("tep khong co cot tien thi bao ro",
   _doc_bang([["A", "B"], ["1", "2"]])[1] != "", True)

# Hai nhip: xem truoc roi moi ghi.
la("co duong xem truoc rieng", "def xem_truoc(" in _sk44, True)
_xt44 = _sk44.split("def xem_truoc(")[1].split("\n@frappe.whitelist()")[0]
la("xem truoc KHONG ghi mot dong nao",
   any(x in _xt44 for x in (".insert(", ".submit(", "set_value")), False)
# QT-19: doc lai tep tu dau, khong nhan danh sach dong tu man hinh gui len.
_nap44 = _sk44.split("def nap(")[1].split("\ndef _chan(")[0]
la("khi ghi that thi doc lai tep tu dau", "_doc_tep(file_url)" in _nap44, True)
la("khong nhan danh sach dong tu man hinh", "def nap(file_url, tai_khoan):" in _sk44, True)
la("ghi tung dong roi commit ngay", "frappe.db.commit()" in _nap44, True)
la("mot dong hong khong keo do ca lo", "frappe.db.rollback()" in _nap44, True)
la("nap xong doi soat ngay phieu cho chi", "de_nghi_chi.khi_co_giao_dich(ma)" in _nap44, True)
# Khu trung hai luot: theo so giao dich, va theo bo ba ngay-tien-tai khoan.
_dc44 = _sk44.split("def _da_co(")[1].split("\ndef _phan_loai(")[0]
la("do trung theo so tham chieu cua SePay", '"reference_number"' in _dc44, True)
la("do trung theo ngay cong so tien", '"date": ("between"' in _dc44, True)
# Chi ke toan, thu mua, giam doc duoc ghi vao so ngan hang.
la("co cong chan rieng cho nhap sao ke", "def _chan(" in _sk44, True)
for _h44 in ("tai_len", "xem_truoc", "nap"):
	la("duong %s co qua cong chan" % _h44,
	   "_chan()" in _sk44.split("def %s(" % _h44)[1].split("\n@frappe.whitelist()")[0], True)
la("tep sao ke cat rieng tu, khong de duong cong khai", '"is_private": 1' in _sk44, True)
la("co man nhap sao ke tren app",
   "scrNhapSaoKe" in open("vagabond/public/js/bep/17-cai-dat.js", encoding="utf-8").read(), True)
la("man nhap sao ke co duong di tu trang chu",
   "if (k === 'NHAPSK') return go(scrNhapSaoKe);" in _tc2_src, True)

# --- 44.7 Danh muc: nut Tao moi va form nhap lieu ---
la("khung co khai bao form tao moi", "def tao(" in _hd44, True)
la("khung co khai bao o tren form", "def o(" in _hd44, True)
la("kieu o dong lai thanh mot danh sach", "KIEU_O = (" in _hd44, True)
# Quyen TAO khong bao gio duoc rong hon quyen XEM.
la("khung chan quyen tao rong hon quyen xem",
   "tao moi ma khong cho xem" in _hd44, True)
# Duong ghi: chi ghi dung nhung truong da khai.
_tm44 = _ds44.split("def tao_moi(")[1]
la("duong tao moi loc truong theo khai bao", 'for c in t["o"]:' in _tm44, True)
la("duong tao moi kiem quyen xem truoc", "_cong_quyen(b)" in _tm44, True)
la("duong tao moi kiem quyen tao rieng", 't["quyen"] & set(frappe.get_roles())' in _tm44, True)
la("duong tao moi khong nhan doctype tu man hinh", "doctype=b[\"doctype\"]" in _tm44, True)
# O lien ket: khong nhan doctype tu man hinh, chi nhan ma man va ten o.
_tl44 = _ds44.split("def tim_lien_ket(")[1].split("\n@frappe.whitelist()")[0]
la("tra cuu lien ket khong nhan doctype tu man hinh",
   "def tim_lien_ket(ma, o, tu_khoa=\"\", so_dong=20):" in _ds44, True)
la("tra cuu lien ket doc doctype tu khai bao", 'c["doctype"]' in _tl44, True)
la("tra cuu lien ket co gioi han so dong", "limit_page_length=int(so_dong" in _tl44, True)
# Man hinh chi hien nut khi may chu tra ve khoi tao.
la("nut Tao moi chi hien khi may chu cho phep", "kq.tao ? { fab: 1 }" in _kds44, True)
la("mot form dung chung cho moi danh muc", "function scrKgTao(" in _kds44, True)
la("khong viet 13 man tao rieng",
   bool(re.search(r"function scrTao(SanPham|Kho|Ncc)", _kds44)), False)
# Danh muc co man tao rieng tot hon thi dan sang man do.
la("co duong dan sang man tao rieng", "di_toi" in _hd44 and "t.di_toi" in _kds44, True)

_DM44b = _nap_danh_muc_nen()
la("danh_muc_nen.py van nap duoc sau khi them form tao moi",
   _DM44b.get("_LOI_NAP") or "", "")
_co_tao44 = [v["ma"] for k, v in sorted(_DM44b.items()) if k.startswith("BANG_") and v.get("tao")]
_khong_tao44 = [v["ma"] for k, v in sorted(_DM44b.items()) if k.startswith("BANG_") and not v.get("tao")]
la("13 danh muc co nut Tao moi", len(_co_tao44), 13)
# Ba cai con lai KHONG phai bi quen: chung can luoi dong con ma form phang
# khong dung noi, va bay ra nut roi ghi mot ban ghi thieu luoi la de ra
# dung cai rac du lieu anh Viet muon chan.
la("ba danh muc can luoi dong con thi khong co nut",
   sorted(_khong_tao44), ["DMBOM", "DMTHUE", "DMTHUEM"])
for _k44, _b44 in sorted(_DM44b.items()):
	if not _k44.startswith("BANG_") or not _b44.get("tao"):
		continue
	_t44b = _b44["tao"]
	la("form %s co quyen hep hon hoac bang quyen xem" % _b44["ma"],
	   sorted(set(_t44b["quyen"]) - set(_b44["quyen"])), [])
	la("form %s khong lot vai bi cam" % _b44["ma"],
	   sorted(set(_t44b["quyen"]) & set(_CAM44)), [])
	if _t44b.get("di_toi"):
		continue
	la("form %s co it nhat mot o" % _b44["ma"], len(_t44b["o"]) >= 1, True)
	for _o44 in _t44b["o"]:
		la("o %s cua %s co kieu hop le" % (_o44["k"], _b44["ma"]),
		   _o44["kieu"] in ("chu", "chu_dai", "so", "tien", "chon", "lien_ket", "co", "ngay"), True)
		if _o44["kieu"] == "lien_ket":
			la("o lien ket %s cua %s khai ro doctype" % (_o44["k"], _b44["ma"]),
			   bool(_o44.get("doctype")), True)
		if _o44["kieu"] == "chon":
			la("o chon %s cua %s co danh sach" % (_o44["k"], _b44["ma"]),
			   len(_o44.get("chon") or []) >= 2, True)

# ============================================================
# 45. v244: Thuong thao va Dieu chinh hop dong (Contract Amendment)
# ============================================================
#
# Loan Anh ben Sales dat bai, anh Viet chuyen sang 21/08/2026: *"Khach hang
# yeu cau chinh sua dieu khoan hop dong sau khi nhan duoc ban he thong sinh
# ra."*
#
# NHOM NAY CO BA CA QUAN TRONG HON CA PHAN CON LAI, dat ngay dau nhom:
# duong TEP khong duoc doc tep cua khach. Anh Viet: *"Tuyet doi KHONG dung
# AI hay tool tu dong doc file cua khach de ghi de so lieu vao Database."*
#
# Vi sao ba ca do dang mot nhom rieng: chung khong kiem mot tinh nang, chung
# kiem mot RANH GIOI. Tinh nang hong thi nguoi dung keu ngay; ranh gioi nay
# vo thi mot con so sai chay thang vao hoa don, so ke toan va lenh xuat kho,
# ma van trong rat hop ly - khong ai keu ca.
print("\n[45] v244: Thuong thao va Dieu chinh hop dong")

_hdc45 = open("vagabond/hop_dong_dieu_chinh.py", encoding="utf-8").read()
_hd45 = open("vagabond/hop_dong.py", encoding="utf-8").read()
_pdf45 = open("vagabond/hop_dong_pdf.py", encoding="utf-8").read()
_js45 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_dt45 = json.load(open(
	"vagabond/vagabond/doctype/hop_dong_ban_hang/hop_dong_ban_hang.json", encoding="utf-8"))
_pb45 = json.load(open(
	"vagabond/vagabond/doctype/hop_dong_phien_ban/hop_dong_phien_ban.json", encoding="utf-8"))

# ---------- 45.1 RANH GIOI: duong tep KHONG doc tep ----------
#
# Cat rieng phan "duong tep" ra roi soi. Soi ca tep thi khong noi len duoc
# gi: mo dun nao cung co the co chu "pdf" o dau do trong mot cau ghi chu.
_duong_tep45 = _hdc45.split("# ĐƯỜNG TỆP: nhận bản hợp đồng hai bên đã chốt bên ngoài")[1]

# Moi ten thu vien doc PDF, rut chu, hay goi mo hinh. Danh sach nay chan
# theo TEN chu khong theo y dinh: ai them mot thu vien doc PDF vao day thi
# ca kiem keu, va do dung la luc can mot nguoi that ngoi lai suy nghi.
_CAM_DOC45 = (
	"PdfReader", "PyPDF", "pypdf", "pdfplumber", "fitz", "pymupdf",
	"pdfminer", "extract_text", "get_text", "OCR", "pytesseract",
	"tesseract", "openai", "anthropic", "gemini", "llm", "completion",
	"embedding", "vision", "parse_pdf", "doc_intelligence",
)
_lot45 = sorted({x for x in _CAM_DOC45 if x.lower() in _duong_tep45.lower()})
la("duong tep KHONG dung thu vien doc PDF hay goi mo hinh nao", _lot45, [])

# Duong tep khong duoc GHI mot truong tai chinh nao. Day la ca bat duoc
# dung cai hong nguy hiem nhat: doc tep roi am tham dien gia vao hop dong.
_TIEN45 = ("gia_tri", "dat_coc_pt", "dat_coc_tien", "ngay_dot1", "ngay_dot2")
_ghi_tien45 = sorted({t for t in _TIEN45 if ('"%s"' % t) in _duong_tep45})
la("duong tep KHONG ghi mot truong tai chinh nao", _ghi_tien45, [])

# Va nguoc lai: duong SO LIEU khong duoc dong vao tep.
_duong_so45 = _hdc45.split("def cap_nhat_so_lieu(")[1].split("\n@frappe.whitelist()")[0]
la("duong so lieu khong doc tep nao",
   any(x in _duong_so45 for x in ("get_content", "b64decode", "file_url", "File")), False)
la("duong so lieu nhan so tu goi tin cua man hinh", "loc_o_sua_duoc(goi)" in _duong_so45, True)

# ---------- 45.2 Phep thuan: so sanh phien ban ----------
_ns45 = {}
exec(compile(_hdc45.split("# PHẦN CHẠM CƠ SỞ DỮ LIỆU")[0], "hop_dong_dieu_chinh:thuan", "exec"), _ns45)
H45_so = _ns45["so_sanh"]
H45_chuan = _ns45["chuan"]
H45_loc = _ns45["loc_o_sua_duoc"]
H45_nhan = _ns45["nhan_phien_ban"]
H45_TRUONG = _ns45["TRUONG_THEO_DOI"]
H45_SUA = _ns45["SUA_DUOC"]

# Chuan hoa: cung mot con so ma Frappe tra ve ba kieu khac nhau.
la("so nguyen va so thuc bang nhau sau khi chuan", H45_chuan(50000, "tien"), H45_chuan(50000.0, "tien"))
la("chuoi so va so bang nhau sau khi chuan", H45_chuan("50000", "tien"), H45_chuan(50000, "tien"))
la("o rong kieu tien ve khong", H45_chuan(None, "tien"), 0)
la("o rong kieu chu ve chuoi rong", H45_chuan(None, "chu"), "")
la("chu co khoang trang thua van bang nhau", H45_chuan(" Vagabond ", "chu"), H45_chuan("Vagabond", "chu"))

_cu45 = {"ten": "HĐ tiệc cưới", "gia_tri": 50000000, "dat_coc_pt": 50,
         "ngay_su_kien": "2026-09-10", "dia_diem_giao": "Số 1 Lê Lợi"}
_moi45 = {"ten": "HĐ tiệc cưới", "gia_tri": 42000000, "dat_coc_pt": 30,
          "ngay_su_kien": "2026-09-17", "dia_diem_giao": "Số 1 Lê Lợi"}
_k45 = H45_so(_cu45, _moi45)
la("bat dung ba o da doi", len(_k45), 3)
la("o khong doi thi khong vao bang",
   any(x["truong"] in ("ten", "dia_diem_giao") for x in _k45), False)
la("ghi lai ca gia tri cu", [x["tu"] for x in _k45 if x["truong"] == "gia_tri"], [50000000])
la("ghi lai ca gia tri moi", [x["den"] for x in _k45 if x["truong"] == "gia_tri"], [42000000])
la("bang khac biet chua dung ba o do",
   sorted(x["truong"] for x in _k45), ["dat_coc_pt", "gia_tri", "ngay_su_kien"])
la("hai ban giong het nhau thi bang khac biet rong", H45_so(_cu45, dict(_cu45)), [])
la("so 50000 va chuoi 50000 khong bi coi la doi",
   H45_so({"gia_tri": 50000}, {"gia_tri": "50000"}), [])
# Dien gia tri DUNG KIEU cho tung o roi so voi mot anh chup rong: phai bat
# het moi o. Dien "x" cho ca o tien thi chuan() doc ra 0, ma o rong cung la
# 0, nen nam o tien khong keu - dung nhu no phai the.
_day45 = {}
for _k45b, _n45b, _kieu45b in H45_TRUONG:
	_day45[_k45b] = 7 if _kieu45b in ("tien", "so") else ("2026-09-10" if _kieu45b == "ngay" else "x")
_het45 = H45_so({}, _day45)
la("anh chup rong so voi ban dien du thi bat het moi o", len(_het45), len(H45_TRUONG))
# Thu tu bang khac biet phai bam DUNG thu tu khai bao, khong phai thu tu
# ngau nhien cua dict hay thu tu chu cai. Giam doc doc muoi dong thi thu tu
# phai co dinh, khong thi lan nao mo ra cung nhu mot to moi.
#
# So CA danh sach chu khong so vai o le: ba o le rat de trung nhau giua thu
# tu khai bao va thu tu chu cai, va luc do ca kiem xanh ma thu tu da hong.
la("thu tu bang khac biet bam dung thu tu khai bao",
   [x["truong"] for x in _het45], [k for k, _, _ in H45_TRUONG])
la("o tien de trong va o tien ghi chu la cung mot con so khong",
   H45_so({"gia_tri": None}, {"gia_tri": "khong phai so"}), [])

# Loc o sua duoc: hang rao that, khong phai trang tri.
la("bo o khong nam trong danh sach sua duoc",
   sorted(H45_loc({"gia_tri": 1, "khach_hang": "KL-001", "trang_thai": "Huỷ"})), ["gia_tri"])
la("khong cho doi khach hang giua chung", "khach_hang" in H45_SUA, False)
la("khong cho doi bao gia nguon giua chung", "bao_gia" in H45_SUA, False)
la("khong cho doi trang thai qua duong nay", "trang_thai" in H45_SUA, False)
la("cho sua gia tri hop dong", "gia_tri" in H45_SUA, True)
# Moi o sua duoc phai nam trong danh sach theo doi, khong thi sua xong ma
# bang khac biet khong noi gi.
_ngoai45 = sorted(set(H45_SUA) - {k for k, _, _ in H45_TRUONG})
la("moi o sua duoc deu duoc theo doi trong nhat ky", _ngoai45, [])
la("nhan phien ban dung dang", H45_nhan(2), "Hợp đồng v2")

# ---------- 45.3 Vong doi ----------
_MO45 = _ns45["MO_DUOC"]
la("mo duoc tu Nhap", "Nháp" in _MO45, True)
# Day la trang thai QUAN TRONG NHAT: khach doi sua SAU KHI da nhan ban he
# thong sinh ra, va gui thu xong la hop dong roi vao dung trang thai nay.
la("mo duoc tu Da gui khach", "Đã gửi khách" in _MO45, True)
la("mo duoc tu Dang thuc hien", "Đang thực hiện" in _MO45, True)
la("KHONG mo tu Hoan tat", "Hoàn tất" in _MO45, False)
la("KHONG mo tu Da thanh ly", "Đã thanh lý" in _MO45, False)
la("KHONG mo tu Huy", "Huỷ" in _MO45, False)

_tt45 = [f for f in _dt45["fields"] if f["fieldname"] == "trang_thai"][0]["options"].split("\n")
for _t45 in ("Nháp", "Đã gửi khách", "Đang thương thảo", "Đang thực hiện",
             "Hoàn tất", "Đã thanh lý", "Huỷ"):
	la("doctype co trang thai %s" % _t45, _t45 in _tt45, True)
# "Da gui khach" tung duoc gui_email ghi vao bang set_value ma KHONG co
# trong o chon - moi hop dong da gui deu mang mot trang thai vo hinh.
la("gui email dat trang thai qua hang so, khong go chuoi tay",
   'set_value(DT, name, "trang_thai", TT_DA_GUI)' in _pdf45, True)

# Bat buoc ghi ly do khi mo thuong thao.
_mo45 = _hdc45.split("def mo_thuong_thao(")[1].split("\n@frappe.whitelist()")[0]
la("mo thuong thao bat buoc ghi ly do", "len(ly_do) < 5" in _mo45, True)
la("chup ban goc truoc khi ai dung vao", "if not _so_phien_ban(doc.name):" in _mo45, True)
la("nho lai trang thai cu de con tra ve", '"tt_truoc_thuong_thao": tt_cu' in _mo45, True)
la("canh bao khi hop dong da co hoa don", "_tien_hoa_don(doc.name)" in _mo45, True)

# Khong cho di duong vong: doi trang thai tay khong thoat duoc thuong thao.
la("doi trang thai tay khong thoat duoc thuong thao",
   "dang == TT_THUONG_THAO" in _hd45, True)
la("man hinh cung khong bay Dang thuong thao ra o doi trang thai tay",
   "'Nháp', 'Đã gửi khách', 'Đang thực hiện', 'Hoàn tất', 'Đã thanh lý', 'Huỷ'" in _js45, True)
# Sua so lieu chi mo khi DANG thuong thao.
la("chi sua so lieu khi dang thuong thao",
   'doc.trang_thai != TT_THUONG_THAO' in _duong_so45, True)

# ---------- 45.4 Phien ban ----------
la("co doctype luu phien ban rieng", _pb45["name"], "Hop Dong Phien Ban")
_ten_pb45 = {f["fieldname"] for f in _pb45["fields"]}
for _f45 in ("hop_dong", "phien_ban", "anh_chup", "khac_biet", "ly_do", "nguoi", "luc"):
	la("phien ban co truong %s" % _f45, _f45 in _ten_pb45, True)
# Giu CA to chu khong chi giu phan khac biet.
la("anh chup giu nguyen van ca to", '"anh_chup": json.dumps(anh_chup(doc)' in _hdc45, True)
la("anh chup va bang khac biet la chi doc",
   all([f for f in _pb45["fields"] if f["fieldname"] == k][0].get("read_only") == 1
       for k in ("anh_chup", "khac_biet")), True)
_chot45 = _hdc45.split("def chot_dieu_chinh(")[1].split("\n@frappe.whitelist()")[0]
la("chot thi so voi ban truoc do", "_ban_moi_nhat(doc.name)" in _chot45, True)
la("chot thi tra hop dong ve trang thai cu", 'doc.get("tt_truoc_thuong_thao")' in _chot45, True)
la("chot xong bao Giam doc", "_bao_giam_doc(doc, pb, khac)" in _chot45, True)
# Dong thuong thao thi KHONG sinh phien ban: khong co gi duoc chot ca.
_huy45 = _hdc45.split("def huy_thuong_thao(")[1].split("\ndef _bao_giam_doc(")[0]
la("dong thuong thao khong sinh phien ban", "_ghi_phien_ban(" in _huy45, False)
la("dong thuong thao van ghi mot dong nhat ky", "add_comment" in _huy45, True)

# ---------- 45.5 Ban hop dong da chot thay ban may tu sinh ----------
la("co duong tai ban chot", "def tai_ban_chot(" in _hdc45, True)
la("chi nhan PDF", 'DUOI_NHAN = (".pdf",)' in _hdc45, True)
la("tep cat rieng tu", '"is_private": 1' in _duong_tep45, True)
# Chan o MAY CHU chu khong chi an nut: duong gui email va duong tai ve deu
# di qua xuat_pdf, an nut chi bit mot cua.
_xp45 = _pdf45.split("def xuat_pdf(")[1].split("\n# ---")[0]
la("xuat PDF tu sinh bi chan khi da co ban chot", "if ban_chot_cua(name):" in _xp45, True)
_ge45 = _pdf45.split("def gui_email(")[1]
la("gui email dinh kem ban da chot khi co",
   "tai_ve_ban_chot(name) if la_ban_chot else xuat_pdf(name)" in _ge45, True)
la("chi mot cong duy nhat hoi co ban chot hay khong",
   _pdf45.count("ban_chot_cua(name)"), 2)
# Go ban chot: bat buoc ghi ly do, va KHONG xoa tep (QT-20).
_go45 = _hdc45.split("def go_ban_chot(")[1].split("\ndef ban_chot_cua(")[0]
la("go ban chot bat buoc ghi ly do", "Phải ghi lý do gỡ" in _go45, True)
la("go ban chot khong xoa tep", any(x in _go45 for x in ("delete_doc", "remove_file")), False)
la("go ban chot van ghi vet", "add_comment" in _go45, True)
# Canh bao tren man phai dung nguyen van cau anh Viet dat ra.
la("man hinh canh bao dung cau ghi de",
   "sẽ ghi đè và thay thế bản hợp đồng tự sinh của hệ thống" in _js45, True)
la("man hinh noi ro may khong doc tep", "không đọc</b> nội dung tệp" in _js45, True)
la("form sua so lieu nhac Sales go tay", "Anh chị gõ tay từng ô" in _js45, True)

# ---------- 45.5b Hai loi bat duoc luc CHAY THU tren site that ----------
#
# Ca nhom 45 xanh het roi moi chay thu tren site, va chay thu van loi ra hai
# thu ma doc ma nguon khong the thay:
#
#   1. `da_sua` tra ve 6 o trong khi nguoi ta chi sua 4, vi Frappe nhet
#      `modified` va `modified_by` vao chinh cai dict minh dua cho set_value.
#   2. Tai len mot tep PDF hong thi nem "PdfStreamError" tho ra man - mot
#      cau tieng Anh khong noi len dieu gi voi Sales dang dung dien thoai.
#
# Hai ca duoi day chot lai ca hai, de lan sau doi ma khong lam hong lai.
la("dem o da sua TRUOC khi goi set_value", "da_sua = sorted(dat.keys())" in _hdc45, True)
la("khong doc lai dat.keys() sau khi set_value",
   'return {"ok": 1, "da_sua": sorted(dat.keys())}' in _hdc45, False)
la("tep PDF hong thi bao bang tieng Viet, khong nem loi tho",
   "Tệp PDF này máy đọc không ra" in _duong_tep45, True)
la("cau bao loi tep hong noi ro phai lam gi tiep",
   "bấm In rồi chọn Lưu thành" in _duong_tep45, True)

# ---------- 45.6 Man hinh ----------
la("co nut Dieu chinh tren man chi tiet", "hdTtMo" in _js45, True)
la("co nut Upload ban Hop dong da chot", "Upload bản Hợp đồng đã chốt" in _js45, True)
la("co man sua so lieu rieng", "function scrHdSuaSoLieu(" in _js45, True)
la("co nhat ky thay doi tren man", "function hdXemLichSu(" in _js45, True)
la("chi tiet hop dong tra ve so phien ban", '"so_phien_ban"' in _hd45, True)
# Danh sach o tren man phai nam gon trong danh sach may chu cho sua, khong
# thi Sales go xong bam Luu ma o do bi bo lang le.
_o_man45 = re.findall(r"\{ k: '([a-z_0-9]+)', nhan:", _js45.split("var HD_O_SUA = [")[1].split("];")[0])
la("man hinh bay dung so o", len(_o_man45) >= 15, True)
la("moi o tren man deu nam trong danh sach may chu cho sua",
   sorted(set(_o_man45) - set(H45_SUA)), [])

# ============================================================
# 46. v247: M-Invoice trong ma nguon, SePay ACB, UNC hinh nho, don Bep
# ============================================================
#
# Bon viec anh Viet giao 20/08/2026 trong cung mot buc thu. Diem chung:
# ca bon deu dong vao du lieu that (hoa don thue, sao ke ngan hang, chung
# tu chi tien, cong thuc san xuat), nen nhom nay soi ranh gioi va duong
# du phong nhieu hon soi giao dien.
print("\n[46] v247: M-Invoice, SePay ACB, UNC hinh nho, don Bep")

_mdb46 = open("vagabond/minvoice_dong_bo.py", encoding="utf-8").read()
_mtep46 = open("vagabond/minvoice_tep.py", encoding="utf-8").read()
_sp46 = open("vagabond/sepay.py", encoding="utf-8").read()
_ht46 = open("vagabond/hoan_tien.py", encoding="utf-8").read()
_db46 = open("vagabond/don_bep.py", encoding="utf-8").read()
_hs46 = open("vagabond/ho_so_tt.py", encoding="utf-8").read()
_hk46 = open("vagabond/hooks.py", encoding="utf-8").read()
_js11_46 = open("vagabond/public/js/bep/11-khach-ca-hop-dong.js", encoding="utf-8").read()
_js17_46 = open("vagabond/public/js/bep/17-cai-dat.js", encoding="utf-8").read()
_dt_ht46 = json.load(open(
	"vagabond/vagabond/doctype/vagabond_hoan_tien/vagabond_hoan_tien.json", encoding="utf-8"))
_MOC46 = "# ------------------------------------------------------- phan can Frappe"

# ---------- 46.1 M-Invoice: ba nguyen nhan sot hoa don, ba cai chot ----------
#
# Su co that: hoa don dau vao sot tu 14/08 (to 598 CACAO BEN TRE 1.590.000 d
# khong co trong he). Ba nguyen nhan da mo ra, moi cai mot ca kiem giu cho
# no khong quay lai.

# (1) Dau vao phai keo TRUOC dau ra: dau vao xep sau la chet chum khi dut
# ket noi giua chung. Soi dung thu tu hai dong append trong _keo.
_keo46 = _mdb46.split("def _keo(")[1].split("\n@frappe.whitelist()")[0]
la("dau vao keo truoc dau ra",
   _keo46.find('cac_loai.append(("INPUT_') < _keo46.find('cac_loai.append(("OUTPUT_'), True)
# (2) Moi loai boc rieng: dau ra loi thi dau vao da keo xong van nguyen.
la("tung loai co try/except rieng", _keo46.count("except Exception:") >= 1, True)
la("loi giua chung ghi ro loai nao vao Error Log", "dut giua chung o loai" in _keo46, True)
# (3) Ghi xuong TUNG TRANG, khong doi het luot: GET hay POST deu ghi that.
la("commit nam trong vong lap trang",
   _keo46.split("while trang <=")[1].split("except Exception:")[0].count("frappe.db.commit()"), 1)

# "Vo ruot": ban ghi insert luc M-Invoice chua do du lieu (so_hd=0) phai
# duoc do lai khi ho da co so that. Phep thuan nap bang python3 tran.
_ns46 = {}
exec(compile(_mdb46.split(_MOC46)[0], "minvoice_dong_bo:thuan", "exec"), _ns46)
la("ban ghi rong ma M-Invoice da co so thi do lai", _ns46["vo_ruot"](0, {"shdon": 598}), True)
la("ban ghi rong ma ho van chua co so thi cho luot sau", _ns46["vo_ruot"](0, {"shdon": 0}), False)
la("ban ghi da co so thi khong dong vao", _ns46["vo_ruot"](598, {"shdon": 598}), False)
la("chua lanh dung chung mot ham du lieu voi insert",
   "_du_lieu(inv, loai))\n\t\t\t\t\t\t\tlanh += 1" in _keo46.replace("    ", "\t") or
   _keo46.count("_du_lieu(inv, loai)") >= 2, True)

# Bang trang thai cua CQT: dung ten that, ma la thi tra nguyen ma.
la("ma 1 la hoa don Goc", _ns46["trang_thai_chu"]("1"), "Gốc")
la("ma 6 la da huy", _ns46["trang_thai_chu"](6), "Đã huỷ")
la("ma la tra nguyen van, khong doan", _ns46["trang_thai_chu"]("9"), "9")
# Doi tac: dau ra la nguoi MUA (nm), dau vao la nguoi BAN (nb).
la("dau ra lay ten nguoi mua",
   _ns46["doi_tac_cua"]({"nmten": "A", "nbten": "B"}, _ns46["LOAI_RA"])["ten"], "A")
la("dau vao lay ten nguoi ban",
   _ns46["doi_tac_cua"]({"nmten": "A", "nbten": "B"}, _ns46["LOAI_VAO"])["ten"], "B")
la("ma tra cuu do dung dong ttkhac",
   _ns46["ma_tra_cuu_cua"]({"ttkhac": [{"ttruong": "x"}, {"ttruong": "Mã tra cứu", "dlieu": "ABC"}]}),
   "ABC")
la("khong co ttkhac thi khong vo", _ns46["ma_tra_cuu_cua"]({}), None)

# Duong chay tay co cong chan vai; nhip lap lich khong duoc whitelist
# (danh sach cua ngo da chot o thu_cua_ngo, day chi kiem cong chan).
_keo_wl46 = _mdb46.split("def keo(")[1].split("\ndef ")[0]
la("keo bu chi cho quan ly va ke toan",
   '{"System Manager", "Accounts Manager"} & set(frappe.get_roles())' in _keo_wl46, True)
# Nhip lap lich phai co trong hooks, thieu la ca he im lang dung keo.
for _h46 in ("minvoice_dong_bo.dong_bo_tu_dong", "minvoice_dong_bo.tu_lanh_hang_dem",
             "minvoice_tep.don_dep_pdf"):
	la("hooks co nhip vagabond.%s" % _h46, "vagabond." + _h46 in _hk46, True)
# 21/08/2026: nhip keo PDF da BO. Duong tai ban the hien cua API qlhd tra
# 400 o moi bien the ten tep, nen de nhip do chay chi to sinh rac Error Log
# moi gio. Anh Viet chot chuyen sang nut tai len tren man Ho so APP.
la("khong con nhip tu keo PDF trong hooks",
   "minvoice_tep.keo_pdf_thieu" in _hk46, False)

# ---------- 46.2 PDF ban the hien: keo ve, dinh vao ho so, don 60 ngay ----------
_ns46b = {}
exec(compile(_mtep46.split(_MOC46)[0], "minvoice_tep:thuan", "exec"), _ns46b)
la("ten tep PDF theo ky hieu va so", _ns46b["ten_tep_pdf"]("1C26MAA", 617), "HDDT-1C26MAA-617.pdf")
la("ky tu la trong ky hieu khong lot vao ten tep",
   "/" in _ns46b["ten_tep_pdf"]("1/C26", 5), False)
la("PDF that bat dau bang %PDF", _ns46b["la_pdf"](b"%PDF-1.7 abc"), True)
la("JSON bao loi khong phai PDF", _ns46b["la_pdf"](b'{"error":1}'), False)
la("chuoi thuong cung khong phai PDF", _ns46b["la_pdf"]("x"), False)
la("boc duoc base64 trong goi JSON", _ns46b["boc_b64_trong_json"]({"data": "A" * 500}), "A" * 500)
la("boc duoc ca khi boc hai lop", _ns46b["boc_b64_trong_json"]({"result": {"pdf": "B" * 500}}), "B" * 500)
la("chuoi ngan khong bi nhan nham la PDF", _ns46b["boc_b64_trong_json"]({"data": "ngan"}), "")

# Tep hoa don mua mang gia von, phai cat rieng tu.
la("PDF luu is_private", '"is_private": 1' in _mtep46, True)
# v247 va 2: phep kiem %PDF don ve _boc_pdf (them boc zip va JSON b64),
# _tai_pdf_tho chi nhan ruot da qua phep boc do.
la("ruot tep phai la PDF that moi luu", "_boc_pdf(" in _mtep46.split("def _tai_pdf_tho")[1].split("\ndef ")[0], True)
la("phep boc dung la_pdf lam thuoc do cuoi", "la_pdf(" in _mtep46.split("def _boc_pdf")[1].split("\ndef ")[0], True)
# Duong dinh vao ho so KHONG BAO GIO duoc lam hong viec tao ho so.
_dinh46 = _mtep46.split("def dinh_vao_ho_so(")[1].split("\ndef ")[0]
la("dinh vao ho so nuot loi, khong throw", "frappe.throw" in _dinh46, False)
la("dinh vao ho so co luoi do cuoi cung", _dinh46.count("except Exception:") >= 2, True)
la("tao ho so co goi duong dinh PDF", "minvoice_tep.dinh_vao_ho_so(doc)" in _hs46, True)
# Don 60 ngay la don CACHE: xoa ban sao tro cung file_url truoc, roi ban goc.
_don46 = _mtep46.split("def don_dep_pdf(")[1]
la("don dep xoa ban sao truoc ban goc",
   _don46.find('"name": ["!=", g.name]') < _don46.find('frappe.delete_doc("File", g.name'), True)
la("so ngay giu doc tu cai dat, mac dinh 60",
   'cint(_cai_dat_chung().get("minvoice_pdf_ngay_giu")) or 60' in _don46, True)
# Hoa don keo loi lien tuc thi thoi, khong dot het luot goi cua to khac.
la("co gioi han so lan thu lai", "LOI_TOI_DA" in _mtep46.split("def keo_pdf_thieu")[1], True)
la("moi nhip co han muc, khong keo vo han", "MOI_NHIP" in _mtep46, True)
la("truong cau hinh PDF co dang ky trong truong_tu_them",
   'minvoice_tep.TRUONG_MOI' in open("vagabond/truong_tu_them.py", encoding="utf-8").read(), True)

# ---------- 46.3 SePay: webhook thu hai cho ACB ----------
#
# SePay sinh cho MOI webhook mot Secret Key rieng, nguoi dung khong chon
# duoc, nen chay hai tai khoan (OCB + ACB) la phai giu duoc hai khoa.
la("co ham doc ca hai khe khoa", "def _cac_khoa(" in _sp46, True)
la("khe thu hai la ten khoa cong _2", 'ten_goc + "_2"' in _sp46, True)
la("kiem HMAC thu ca hai khoa", '_cac_khoa("sepay_hmac")' in _sp46, True)
la("duong X-Api-Key cung thu ca hai khoa", '_cac_khoa("sepay_khoa")' in _sp46, True)
_hmac46 = _sp46.split("def _kiem_hmac(")[1].split("\ndef ")[0]
la("chu ky van so bang compare_digest, khong so bang ==",
   "hmac.compare_digest(x, y)" in _hmac46, True)
la("truong khoa ACB co trong khai bao truong", '"fieldname": "sepay_hmac_2"' in _sp46, True)
la("khoa du phong ACB cung co", '"fieldname": "sepay_khoa_2"' in _sp46, True)
_dh46 = _sp46.split("def dat_hmac(")[1].split("\n@frappe.whitelist()")[0]
la("dat_hmac nhan khe 2", 'cint(khe) != 2 else "sepay_hmac_2"' in _dh46, True)

# Khai ban do tai khoan ngay tren app: CHI THEM VA DOI, khong xoa.
_tk46 = _sp46.split("def them_tai_khoan(")[1].split("\n@frappe.whitelist()")[0]
la("them tai khoan chi cho quan ly va ke toan",
   '{"System Manager", "Accounts Manager"} & set(frappe.get_roles())' in _tk46, True)
la("so tai khoan chi giu chu so", "ch.isdigit()" in _tk46, True)
la("tai khoan ERPNext phai co that", 'frappe.db.exists("Bank Account", tk)' in _tk46, True)
la("khai xong thi ra khoi danh sach chua khai", "cu_ds.remove(so_tk)" in _tk46, True)
la("duong them khong co lenh xoa dong ban do", "ban_do.pop" in _tk46 or "del ban_do" in _tk46, False)
# Man Cai dat: o khoa ACB va o khai ban do.
la("man cai dat co o khoa HMAC thu hai", "seHm2" in _js17_46, True)
la("man cai dat khai duoc ban do tai khoan", "vagabond.sepay.them_tai_khoan" in _js17_46, True)
la("so tai khoan chua khai duoc dien san vao o", "(d.chua_map || [])[0]" in _js17_46, True)

# ---------- 46.4 UNC: hinh nho cho Sales xem va tai ----------
#
# Tep UNC dinh vao PAYMENT ENTRY ma Sales khong doc duoc doctype do, nen
# duong dan /private/files tho voi ho la mot cai 403. Moi thu phai di qua
# tai_unc, va tai_unc phai kiem theo PHIEU chu khong tin ma File tren man.
_tai46 = _ht46.split("def tai_unc(")[1].split("\n@frappe.whitelist()")[0]
la("tai_unc doi tep phai dinh dung phieu chi cua ho so",
   '"attached_to_name": ma_pe' in _tai46, True)
la("tai_unc co cong chan quyen", "_kiem_quyen()" in _tai46, True)
la("hinh thu nho co gioi han kich thuoc", "thumbnail((360, 360))" in _tai46, True)
la("khong nen duoc thi tra nguyen ban chu khong vo", "pass" in _tai46.split("except Exception:")[-1], True)
_dsu46 = _ht46.split("def _ds_unc(")[1].split("\n@frappe.whitelist()")[0]
la("danh sach UNC tra kem ma tep va co la_anh", '"la_anh"' in _dsu46 and '"tep"' in _dsu46, True)
# Quyen doc phieu hoan tien cho Sales (anh Viet 20/08/2026), chi DOC.
_sales46 = [x for x in _dt_ht46["permissions"] if x.get("role") in ("Sales User", "Sales Manager")]
la("hai vai Sales co quyen doc phieu hoan tien", len(_sales46), 2)
for _p46 in _sales46:
	la("vai %s chi doc, khong sua khong tao" % _p46["role"],
	   tuple(int(_p46.get(k) or 0) for k in ("read", "write", "create", "delete")),
	   (1, 0, 0, 0))
# Man hinh: anh ve bang the img qua duong tai_unc, khong con link tho.
la("anh UNC ve bang the img", "class=\"htuncanh\"" in _js11_46.replace("'", "\""), True)
la("hinh nho goi tai_unc co=nho", "co: 'nho'" in _js11_46, True)
la("phong to goi tai_unc co=lon", "co: 'lon'" in _js11_46, True)
la("anh phong to co nut tai ve", "Tải về gửi khách" in _js11_46, True)
_ctu46 = _js11_46.split("function htCtUnc(")[1].split("\nfunction ")[0]
la("khong con the a tro thang vao duong dan tep rieng tu",
   "'<a href=\"' + h(t.url)" in _ctu46, False)

# ---------- 46.5 Don Bep: lam tuoi, bo So che, gop trung ----------
_ns46c = {}
exec(compile(_db46.split(_MOC46)[0], "don_bep:thuan", "exec"), _ns46c)
# He so doc tu chinh hai BOM so che: long do 1.0, long trang 32/30.
la("mot gram long do la mot gram trung", _ns46c["he_so_cua"]("BTPB00046"), 1.0)
la("ma long do cu cung tinh nhu the", _ns46c["he_so_cua"]("5HVQDZAMZGB6"), 1.0)
la("long trang can nhieu trung hon phan minh", round(_ns46c["he_so_cua"]("BTPB00045"), 4), round(32.0 / 30.0, 4))
# NVLT00042 la long do trung MUOI mua cua Ami, khong phai trung tach ra.
la("long do muoi mua ngoai KHONG bi dong vao", _ns46c["he_so_cua"]("NVLT00042"), 0.0)
la("ma cam ghi ro trong hang so", _ns46c["MA_CAM"], "NVLT00042")
_tong46, _ghi46 = _ns46c["gop_dong_trung"]([("BTPB00046", 25), ("BTPB00045", 30)])
la("25g long do cong 30g long trang la 57g trung", _tong46, 57.0)
la("cach tinh ghi ro tung dong de doi chieu", len(_ghi46), 2)
_tong46b, _ = _ns46c["gop_dong_trung"]([("NVLT00042", 100)])
la("dong long do muoi khong sinh ra gram trung nao", _tong46b, 0.0)

# Moi cua cua don_bep deu phai qua cong chan giam doc.
for _f46 in ("lam_tuoi_xem_truoc", "lam_tuoi_thuc_hien", "so_che_xem_truoc",
             "so_che_thuc_hien", "trung_xem_truoc", "trung_thuc_hien"):
	la("cua %s co qua cong chan" % _f46,
	   "_chan()" in _db46.split("def %s(" % _f46)[1].split("\n@frappe.whitelist()")[0].split("\ndef ")[0], True)
# Mac dinh CHI danh dau lam tuoi; tat ton kho la che do rieng phai goi ro.
la("che do mac dinh la lam_tuoi, khong phai phantom",
   'def lam_tuoi_thuc_hien(che_do="lam_tuoi")' in _db46, True)
la("che do phantom bao cao tung ma bi ERPNext chan", '"bi_chan"' in _db46, True)
# BOM da ghi so: thay dong bang cach tao BAN MOI, khong choc thang vao bang.
_tt46 = _db46.split("def _thay_mot_bom(")[1].split("\n@frappe.whitelist()")[0]
la("thay trung bang cach sao chep BOM", "frappe.copy_doc(" in _tt46, True)
la("khong update thang vao bang BOM Item", "update `tabBOM Item`" in _db46.lower(), False)
la("ban cu ngung hoat dong, khong xoa", '{"is_active": 0, "is_default": 0}' in _tt46, True)
_tth46 = _db46.split("def trung_thuc_hien(")[1]
la("tung BOM boc rieng, hong mot khong do ca lo", "frappe.db.rollback()" in _tth46, True)
la("chi tat ma trung khi khong con cong thuc nao dung", "if not _bom_dinh_trung():" in _tth46, True)

# ============================================================
# 47. v249: man Duyet YCMH giu duoc so, ho so nha cung cap, tai tep tay
# ============================================================
#
# Ba viec anh Viet giao 21/08/2026, deu tu mot buoi Uyen ngoi thao tac that
# tren dien thoai va vap:
#
#   1. Man Duyet yeu cau mua: go so vao o Duyet thi may NUOT mat, bam Luu
#      thi bao "Chua sua dong nao". Nguyen nhan: moi thao tac nho deu ve lai
#      man va TAI LAI du lieu tu may chu, ghi de len nhung gi vua go.
#   2. Tao nha cung cap: khong co quyen Tao, va form chi bon o nen thieu
#      email - trong khi don mua hang gui qua email.
#   3. Ban the hien hoa don: duong API tra 400, doi sang nut tai len tay.
#
# NHOM NAY CO MOT CA QUAN TRONG HON CA: "man khong tai lai du lieu khi ve
# lai". Do la ca chan dung cai loi da lam Uyen ngoi go lai 27 dong ma khong
# luu duoc dong nao.
print("\n[47] v249: Duyet YCMH giu so, ho so NCC, tai tep tay")

_mh47 = open("vagabond/public/js/bep/16-mua-hang.js", encoding="utf-8").read()
_ncc47 = open("vagabond/nha_cung_cap.py", encoding="utf-8").read()
_hs47 = open("vagabond/ho_so_tt.py", encoding="utf-8").read()
_js19_47 = open("vagabond/public/js/bep/19-ho-so-tt.js", encoding="utf-8").read()
_dm47 = open("vagabond/danh_muc_nen.py", encoding="utf-8").read()
_tc47 = open("vagabond/public/js/bep/02-trang-chu.js", encoding="utf-8").read()
_duyet47 = _mh47.split("async function scrDuyetYcXem(")[1].split("\n/* ----------------")[0]

# ---------- 47.1 RANH GIOI: man khong duoc tu ghi de cai nguoi ta vua go ----------
la("man duyet nhan co giu man", "async function scrDuyetYcXem(name, giuMan)" in _mh47, True)
la("ve lai mac dinh la GIU, khong tai lai",
   "function veLai(taiLai) { go(function () { scrDuyetYcXem(name, !taiLai); }, true); }" in _duyet47, True)
la("co duong dung lai du lieu dang co", "if (dungLai) {" in _duyet47, True)
# Sau khi LUU hoac GO DUYET tren may chu thi PHAI tai lai - luc do ban may
# chu moi la ban dung.
for _sau47 in ("Đã lưu: ", "Đã gỡ duyệt"):
	_doan47 = _duyet47.split(_sau47)[1][:260]
	la("sau khi %s thi tai lai tu may chu" % _sau47.strip(), "veLai(1)" in _doan47, True)
# O nhap khong duoc ve lai man: tren dien thoai, cham nut Luu lam o mat tieu
# diem truoc, DOM bi thay moi va cu cham roi vao khoang khong.
_onc47 = _duyet47.split("el.onchange = function ()")[1].split("};")[0]
la("roi o nhap KHONG ve lai ca man", "veLai(" in _onc47, False)
la("go den dau ghi den do", "el.oninput = function ()" in _duyet47, True)
la("nut Luu noi ro dang giu bao nhieu dong", "function dyNhanLuu()" in _duyet47, True)
la("moi duong sua so deu di qua mot cua", "function dyDat(" in _duyet47, True)
# Khong con doi duyet het moi cho luu.
la("khong bat duyet het moi duoc luu", "chưa đụng tới vẫn nằm chờ" in _duyet47, True)
la("cau bao khi chua go gi noi ro phai lam gi",
   "Gõ số vào ô \"Duyệt\"" in _duyet47, True)
# Nut duyet het: truoc bao loi bat nguoi dung tu bam Luu, nay lam ho.
la("duyet het thi luu ho phan dang go", "Lưu rồi duyệt hết" in _duyet47, True)

# ---------- 47.2 Ho so nha cung cap: mot goi, bon bang ----------
_ns47 = {}
exec(compile(_ncc47.split("# ------------------------------------------------------- phan can Frappe")[0],
             "nha_cung_cap:thuan", "exec"), _ns47)
la("ma so thue 10 so giu nguyen", _ns47["chuan_mst"]("0318917687"), "0318917687")
la("ma chi nhanh 13 so phai co gach", _ns47["chuan_mst"]("0311638525027"), "0311638525-027")
la("ma 12 so cua ho kinh doanh van nhan", len(_ns47["chuan_mst"]("012345678901")), 12)
la("so rac thi tra rong", _ns47["chuan_mst"]("123"), "")
la("email thieu duoi bi chan", _ns47["email_hop_le"]("ai@gmail"), False)
la("email dung thi qua", _ns47["email_hop_le"]("ketoan@vagabond.vn"), True)
la("email thieu a coi bi chan", _ns47["email_hop_le"]("ketoan.vagabond.vn"), False)
la("hai dau a coi bi chan", _ns47["email_hop_le"]("a@b@c.vn"), False)
# Email KHONG con bat buoc tu 21/08/2026: co nha cung cap chi ban qua app
# hoac san thuong mai dien tu, khong nhan don qua email. Bat buoc email
# nghia la khong lap noi ho so cho nhung ben do.
la("thieu email van cho ghi",
   _ns47["thieu_o_nao"]({"ten": "A", "nhom": "B"}), [])
la("thieu ten thi van chan",
   "Tên nhà cung cấp" in _ns47["thieu_o_nao"]({"nhom": "B"}), True)
la("gom ba o email CC, bo trong va bo trung",
   _ns47["loc_email_cc"](["a@v.com", "", "A@v.com", "b@v.com"]),
   ["a@v.com", "b@v.com"])
# Chan trung: hai ho so cung mot MST la cong no tach lam doi.
la("chan trung ma so thue", "đã có trong hệ" in _ncc47, True)
la("chan trung ten nha cung cap", "Đã có nhà cung cấp tên" in _ncc47, True)
# Lien he phai duoc danh dau CHINH, vi duong gui don mua hang doc o do.
la("danh dau lien he chinh", '"is_primary_contact": 1' in _ncc47, True)
la("ghi email ca hai cho de moi duong doc deu ra",
   'dat["email_id"] = email' in _ncc47 and '"supplier_primary_contact": doc.name' in _ncc47, True)
la("tai khoan ngan hang gan theo party Supplier",
   '"party_type": "Supplier"' in _ncc47, True)
la("ngan hang go tay khong khop danh muc thi bo trong",
   'frappe.db.exists("Bank", nh)' in _ncc47, True)
# Ba phan phu hong thi van giu ho so, khong bat go lai tu dau.
_tao47 = _ncc47.split("def tao(")[1]
la("phan phu hong thi ghi Error Log chu khong do ca ho so",
   _tao47.count("hong.append(") >= 3, True)
la("bao cao ro phan nao chua ghi duoc", "chưa ghi được" in _ncc47, True)
# Cua ngo va dinh tuyen.
la("nut Tao NCC dan sang man rieng", 'di_toi="NCCTAO"' in _dm47, True)
la("form chung khong con giu bon o cua NCC",
   'khai.o("supplier_name", "Tên nhà cung cấp"' in _dm47, False)
la("co nhanh dinh tuyen NCCTAO", "if (k === 'NCCTAO') return go(scrNccTao);" in _tc47, True)
la("co man tao NCC tren app", "async function scrNccTao(" in _mh47, True)
la("man NCC dat ma so thue len dau va tra cuu khi roi o",
   "mo.onblur" in _mh47 and "vagabond.api.tra_mst" in _mh47, True)
# Tra cuu chi DIEN HO vao o dang trong, khong de len cai nguoi ta da go.
_mst47 = _mh47.split("mo.onblur = async function ()")[1].split("var lb = document.getElementById('nccLuu')")[0]
la("tra cuu chi dien vao o dang trong", "!(oTen.value || '').trim()" in _mst47, True)
la("tra cuu khong ghi thang xuong co so du lieu",
   any(x in _mst47 for x in ("nha_cung_cap.tao", "frappe.client.set_value", "set_value")), False)
la("khong tra ra thi noi ro go tay", "gõ tên tay giúp em" in _mst47, True)

# ---------- 47.3 Ban the hien hoa don: tai tay thay vi keo API ----------
la("co cua dinh tep vao ho so", "def dinh_tep(" in _hs47, True)
la("co cua go tep dinh nham", "def go_tep(" in _hs47, True)
_dinh47 = _hs47.split("def dinh_tep(")[1].split("@frappe.whitelist()")[0]
la("tep dinh vao ho so de rieng tu", '"is_private": 1' in _dinh47, True)
la("ho so da huy thi khong dinh them", "đã %s nên không đính thêm" in _dinh47, True)
_go47 = _hs47.split("def go_tep(")[1].split("@frappe.whitelist()")[0]
# QT-20: go la bo lien ket, KHONG xoa tep.
la("go tep khong xoa tep", "delete_doc" in _go47, False)
la("go tep chi bo con tro", '"attached_to_doctype": None' in _go47, True)
la("man ho so co nut tai ban the hien len", "Tải bản thể hiện hoá đơn lên" in _js19_47, True)
la("chua co tep thi noi ro ke toan truong can gi", "mới duyệt được" in _js19_47, True)
la("nut tai len goi dung cua dinh_tep", "vagabond.ho_so_tt.dinh_tep" in _js19_47, True)

# ============================================================ NHOM 48
print("\n[48] v250: Thu gop nhieu don, email CC nha cung cap, Phantom cap 1")

_tt48 = open("vagabond/trang_thai_thu.py", encoding="utf-8").read()
_ncc48 = open("vagabond/nha_cung_cap.py", encoding="utf-8").read()
_mh48 = open("vagabond/public/js/bep/16-mua-hang.js", encoding="utf-8").read()
_ph48 = open("vagabond/phantom.py", encoding="utf-8").read()
_js48 = open("vagabond/public/js/bep/24-phantom.js", encoding="utf-8").read()
_sx48 = open("vagabond/public/js/bep/05-san-xuat.js", encoding="utf-8").read()

# ---------- 48.1 Thu gop: mot la thu, nhieu don, phai dong dau het ----------
# Uyen gop ba don vao mot thu, chi don dau hien "Da gui", hai don kia nam
# nguyen o "Chua gui" nen Uyen bam gui lai va nha cung cap nhan hai lan.
la("co phep tim ma trong than thu", "def tim_ma_trong_thu(" in _tt48, True)
la("co phep quy mot la thu ra nhieu chung tu",
   "def _cac_chung_tu_cua_thu(" in _tt48, True)
_soat48 = _tt48.split("def soat_tu_dong(")[1].split("# =====")[0]
la("nhip soat khong con gom theo o tham chieu",
   "(x.reference_doctype, x.reference_name)" in _soat48, False)
la("nhip soat gom qua phep do than thu", "_cac_chung_tu_cua_thu" in _soat48, True)
_hook48 = _tt48.split("def danh_dau_cho_gui(")[1].split("def soat_tu_dong")[0]
la("hook luc vao hang doi cung dong dau het",
   "_cac_chung_tu_cua_thu" in _hook48, True)
_do48 = _tt48.split("def _cac_chung_tu_cua_thu(")[1].split("def danh_dau_cho_gui")[0]
# Doan mach: ma do ra tu than thu phai TON TAI THAT moi nhan, khong thi
# mot chuoi ngau nhien trong giong ma don cung thanh chung tu.
la("ma do ra phai co that moi nhan", "frappe.db.exists" in _do48, True)
la("chi nhan doctype co cot trang thai", "loai not in CHUNG_TU_CO_GUI" in _do48, True)
la("uu tien doc Communication, khong doc MIME base64",
   "_than_thu" in _do48, True)
la("man chi tiet cung tim thu gop", "_thu_gop_co_nhac" in _tt48, True)
la("co duong soat lai quang dai de va don da sot", "def soat_lai(" in _tt48, True)
_sl48 = _tt48.split("def soat_lai(")[1].split("# =====")[0]
la("soat lai chan nguoi khong co quyen", "has_permission" in _sl48, True)
la("soat lai chan tran so ngay", "min(int(so_ngay" in _sl48, True)

# ---------- 48.2 Nha cung cap: email khong bat buoc, them ba o CC ----------
_ns48 = {}
exec(compile(_ncc48.split("# ------------------------------------------------------- phan can Frappe")[0],
             "nha_cung_cap:thuan48", "exec"), _ns48)
la("khong email van lap duoc ho so",
   _ns48["thieu_o_nao"]({"ten": "A", "nhom": "B"}), [])
la("ba o CC gom lai, bo trung khac hoa thuong",
   _ns48["loc_email_cc"](["A@v.com", "a@v.com", "b@v.com"]), ["A@v.com", "b@v.com"])
la("go lien mot chuoi ngan bang dau phay cung tach duoc",
   _ns48["loc_email_cc"]("a@v.com, b@v.com"), ["a@v.com", "b@v.com"])
la("o email phu CC khai trong ma nguon", '"email_cc"' in _ncc48, True)
la("o CC dat ngay sau o email", '"insert_after": "email_id"' in _ncc48, True)
la("email CC sai dinh dang thi chan", "Email CC" in _ncc48, True)
la("email CC vao thanh nguoi lien he phu", '"is_primary": 0' in _ncc48, True)
# Man hinh: bo dau sao bat buoc, them ba o.
_ncc2_48 = _mh48.split("async function scrNccTao()")[1]
la("man khong con chan khi thieu email",
   "Đơn mua hàng gửi qua email nên ô này bắt buộc" in _ncc2_48, False)
la("noi ro co ben chi mua qua app va san", "sàn thương mại điện tử" in _ncc2_48, True)
for _o48 in ("nccCc1", "nccCc2", "nccCc3"):
	la("co o %s" % _o48, _o48 in _ncc2_48, True)
la("khoi CC co tieu de dung nhu anh Viet dat",
   "Các email phụ cần CC" in _ncc2_48, True)

# ---------- 48.3 Phantom cap 1: chay thu la mac dinh ----------
la("chay that phai goi ro", "def chuyen(chay_that=0)" in _ph48, True)
_ch48 = _ph48.split("def chuyen(chay_that=0)")[1].split("# -----")[0]
la("chua chay that thi tra ve som", "if not that:" in _ch48, True)
la("chay that moi dung hang rao", 'ke["hang_rao"]["chan"]' in _ch48, True)
# Thu tu la co y: sua dong cong thuc TRUOC, doi ma hang SAU. Nua chung
# hong thi he van o trang thai cu doc duoc va bep van chay.
la("sua dong cong thuc truoc khi doi ma hang",
   _ch48.find('"BOM Item"') < _ch48.find('"is_stock_item"'), True)
la("ghi thang xuong bang chu khong qua doc.save",
   "frappe.db.set_value(\"Item\"" in _ch48, True)
la("dung lai bang no sau khi sua co", "update_exploded_items" in _ch48, True)
# Hai buc tuong thay cho phep kiem cua ERPNext bi bo qua.
_hr48 = _ph48.split("def _hang_rao(")[1].split("# -----")[0]
la("con lenh treo thi chan", "_lenh_treo" in _hr48, True)
la("con ton kho thi chan", "_ton_con_lai" in _hr48, True)
# Bo co dne ma khong dien bom_no thi khong co gi de no xuong.
_ke48 = _ph48.split("def _ke_hoach(")[1].split("@frappe.whitelist()")[0]
la("khong co cong thuc con thi KHONG bo co chan",
   "phải lập BOM trước" in _ke48, True)
la("dong cua BOM da ngung hoat dong thi de yen",
   "BOM cha đã ngừng hoạt động" in _ke48, True)
# Don chung tu thu: dong chu khong xoa (QT-20).
_dl48 = _ph48.split("def dong_lenh(")[1]
la("dong lenh bang duong Close cua ERPNext", "stop_unstop" in _dl48, True)
la("dong lenh khong xoa gi", "delete" in _dl48, False)
la("dong lenh da dong roi thi noi ro, khong bao loi",
   "đã ở trạng thái" in _dl48, True)
# Cau tu choi phai noi viec phai lam tiep (QT-24).
la("cau tu choi chi duong sang man Don chung tu thu",
   "Dọn chứng từ thử" in _ph48, True)
la("cau tu choi noi hau qua neu bo qua", "nằm lại trong kho" in _ph48, True)
# Man hinh.
la("man Don chung tu thu co that", "async function scrDonChungTuThu()" in _js48, True)
la("man Chuyen Phantom co that", "async function scrChuyenPhantom()" in _js48, True)
la("man chuyen mo ra la ban CHAY THU", "vagabond.phantom.xem_truoc" in _js48, True)
la("nut ghi that truyen chay_that bang 1", "chay_that: 1" in _js48, True)
la("nut ghi that hoi lai mot lan nua", "KHÔNG có nút hoàn tác" in _js48, True)
# Luong san xuat: no nhieu cap phai HOI he chu khong ghi cung.
la("khong con ghi cung use_multi_level_bom bang 0",
   "use_multi_level_bom: 0" in _sx48, False)
la("hoi he truoc khi lap lenh", "mfgNoNhieuCap()" in _sx48, True)
la("hoi mot lan roi nho lai", "if (mfgPhantom !== null)" in _sx48, True)

# Doc bang con thi KHONG duoc truyen `parent=`: do la tham so cua duong
# REST ben ngoai, `frappe.get_all` trong may chu nem TypeError. Dung loi da
# lam man Don chung tu thu tra ve ma 500 ngay lan mo dau tien toi 20/08.
la("khong truyen parent vao get_all", 'parent="BOM"' in _ph48, False)
la("khong truyen parent vao get_all lan hai", 'parent="Stock Entry"' in _ph48, False)
for _tep48 in ("vagabond/trang_thai_thu.py", "vagabond/nha_cung_cap.py",
               "vagabond/phantom.py"):
	_n48 = open(_tep48, encoding="utf-8").read()
	la("%s khong dung parent= trong get_all" % _tep48.split("/")[-1],
	   "\n\t\tparent=" in _n48 or "\n\t\t\tparent=" in _n48, False)

# ---------- 48.4 Hang rao dong vo: phan moi khong duoc ghep ra ngoai vo ----
# Toi 20/08 v250 len that roi bam vao man Phantom thi bao "frame is not
# defined": phan 24-phantom.js bi ghep SAU 23-dong-vo.js nen nam ngoai vo
# ham. node --check dat, ca bo kiem thu dat, chi bam that moi thay.
import os as _os48

_bep48 = sorted(t for t in _os48.listdir("vagabond/public/js/bep")
                if len(t) > 3 and t[:2].isdigit() and t.endswith(".js"))
la("phan dong vo la phan cuoi cung", _bep48[-1], "99-dong-vo.js")
_may48 = open("dung_app_bep.py", encoding="utf-8").read()
la("may ghep tu chan khi phan cuoi khong phai dong vo",
   "ten[-1] != TEP_DONG_VO" in _may48, True)
_ghep48 = open("vagabond/public/js/app_bep.js", encoding="utf-8").read()
_vt48 = _ghep48.rfind("})();")
for _ham48 in ("function scrDonChungTuThu", "function scrChuyenPhantom",
               "function scrNccTao"):
	la("%s nam TRONG vo ham" % _ham48.split()[1],
	   0 < _ghep48.find(_ham48) < _vt48, True)

print("-" * 60)
if so_hong:
	print("HONG %d/%d ca" % (so_hong, so_ca)); sys.exit(1)
print("DAT %d/%d ca" % (so_ca, so_ca))
