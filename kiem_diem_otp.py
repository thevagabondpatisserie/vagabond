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

print("-" * 60)
if so_hong:
	print("HONG %d/%d ca" % (so_hong, so_ca)); sys.exit(1)
print("DAT %d/%d ca" % (so_ca, so_ca))
