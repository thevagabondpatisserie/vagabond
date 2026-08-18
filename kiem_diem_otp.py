"""Bo kiem thu THUAN cho cac phep tinh cua luong tru diem.

Chay khong can site, khong can co so du lieu: python3 kiem_diem_otp.py

Vi sao dang tep rieng chu khong dung unittest cua Frappe: cong kiem truoc
deploy phai chay duoc tren may nay, noi khong co bench nao ca. Cac ham duoc
kiem la ham THUAN - so vao, so ra - nen chep lai logic o day la du, va neu
ban that trong diem_otp.py doi ma ban nay khong doi thi cong se bao lech.
"""

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

print("-" * 60)
if so_hong:
	print("HONG %d/%d ca" % (so_hong, so_ca)); sys.exit(1)
print("DAT %d/%d ca" % (so_ca, so_ca))
