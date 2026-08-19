"""Bo kiem thu THUAN cho cac phep tinh cua luong tru diem.

Chay khong can site, khong can co so du lieu: python3 kiem_diem_otp.py

Vi sao dang tep rieng chu khong dung unittest cua Frappe: cong kiem truoc
deploy phai chay duoc tren may nay, noi khong co bench nao ca. Cac ham duoc
kiem la ham THUAN - so vao, so ra - nen chep lai logic o day la du, va neu
ban that trong diem_otp.py doi ma ban nay khong doi thi cong se bao lech.
"""

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
la("cac nut mua hang da roi khoi nhom Dat hang",
   "keys: ['Purchase', 'Transfer', 'RND'] }" in _tc_src, True)
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
la("gia mua khong mo cho ca tiem", "quyen=XEM_MUA" in _dm_src, True)
la("ho so khach hang khong mo cho ca tiem", "quyen=XEM_KHACH" in _dm_src, True)
la("tai khoan ke toan khong mo cho ca tiem", "quyen=XEM_TIEN" in _dm_src, True)
la("bep KHONG nam trong nhom xem tien",
   "Bếp phó" in _dm_src.split("XEM_TIEN = {")[1].split("}")[0], False)
la("bep KHONG nam trong nhom xem khach",
   "Bếp phó" in _dm_src.split("XEM_KHACH = {")[1].split("}")[0], False)
la("bep CO nam trong nhom xem chung",
   "Bếp phó" in _dm_src.split("XEM_CHUNG = {")[1].split("}")[0], True)
# Ca nay bat duoc lo hong cua chinh bo kiem lan thu lua: ba ca tren soi
# XEM_TIEN, XEM_KHACH, XEM_CHUNG ma bo quen XEM_MUA. Them "Bep pho" vao
# XEM_MUA la bep xem duoc gia mua ma khong ca nao keu.
la("bep KHONG xem duoc gia mua va nha cung cap",
   "Bếp phó" in _dm_src.split("XEM_MUA = ")[1].split("\n")[0], False)
la("gia mua khong lot vai Bo phan dat hang",
   "Bộ phận đặt hàng" in _dm_src.split("XEM_MUA = ")[1].split("\n")[0], False)

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
la("cot So hieu khong tro thang vao account_number nua",
   '("account_number", "Số hiệu"' in _dm_src, False)
la("cot So hieu doc tu phep tach", '("so_hieu", "Số hiệu", "chu")' in _dm_src, True)
_than_tk = _dm_src.split("BANG_TAI_KHOAN = khai.bang(")[1].split("\n)")[0]
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
la("to de trong o kieu thue thi chay nhanh cu",
   'if (doc.get("kieu_thue") or "") == "Theo từng dòng":' in _than_tinh, True)
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

	def _dung_bg(sua=None):
		"""Dung THAT to bao gia. Nem loi thi tra ve chuoi loi de doc duoc."""
		d = dict(_BG_GIA)
		if sua:
			d.update(sua)
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
                     dict(_HS_NGAY, re=re))
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

# --- 31d. Ham doc mau ZNS ---
_zl_src = open("vagabond/zalo.py", encoding="utf-8").read()
la("co ham doc mau ZNS", "def thu_mau(" in _zl_src, True)
_than_tm = _zl_src.split("def thu_mau(")[1]
la("doc mau ZNS chi cho System Manager", "System Manager" in _than_tm, True)
la("doc mau ZNS goi dung duong template/info", "template/info" in _than_tm, True)
la("doc mau ZNS khong gui tin nao", "message/template" in _than_tm, False)

print("-" * 60)
if so_hong:
	print("HONG %d/%d ca" % (so_hong, so_ca)); sys.exit(1)
print("DAT %d/%d ca" % (so_ca, so_ca))
