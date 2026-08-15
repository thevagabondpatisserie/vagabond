"""Tinh toan cua man danh sach: dem, loc, cong, cat.

TANG THUAN. Khong import frappe. Nhan list va dict vao, tra list va dict ra.

Vi sao tach han ra file rieng (tieu chuan so 8, anh Viet nhan manh)
-------------------------------------------------------------------
Hom 13/08/2026 bill in lai cong trung diem thanh vien: khach co 21.200 diem
ma bill in ra 42.400. Loi khong nam o cho goi co so du lieu, no nam o mot
phep cong. Nhung vi phep cong do nam lan trong ham co goi frappe nen muon
thu lai phai dung ca mot site, va vi kho thu nen khong ai thu, va vi khong
ai thu nen no lot ra toi tay khach.

Moi phep tinh dung toi tien trong file nay deu chay duoc bang:

    python3 -c "from vagabond.khung import tinh; ..."

khong can Frappe, khong can co so du lieu, khong can site. Do la dieu kien
de bo kiem thu A6 op vao. Da them mot lenh frappe vao file nay la mat het.

Quy uoc so hoc
--------------
Khong dung frappe.utils.flt trong file nay, dung ham so() ben duoi. Hai ham
phai cho cung ket qua tren du lieu that: so tien tu co so du lieu ve la
float hoac Decimal, ca hai deu qua float() duoc. Truong hop None va chuoi
rong deu ra 0,0 dung nhu flt.
"""


def so(v):
	"""Doc mot gia tri ra so thuc. Doc khong duoc thi tra 0,0.

	Doi ung voi frappe.utils.flt nhung khong can Frappe. Tra 0,0 chu khong
	nem loi: mot o trong trong bang khong duoc lam sap ca man danh sach.
	"""
	if v is None or v == "":
		return 0.0
	if isinstance(v, bool):
		return 1.0 if v else 0.0
	try:
		return float(v)
	except (TypeError, ValueError):
		pass
	try:
		return float(str(v).replace(",", "").strip())
	except (TypeError, ValueError):
		return 0.0


def co(v):
	"""Gia tri nay co bat khong. Doi ung voi frappe.utils.cint dang dung lam co."""
	if v is None or v == "":
		return 0
	if isinstance(v, bool):
		return 1 if v else 0
	try:
		return 1 if int(float(v)) else 0
	except (TypeError, ValueError):
		return 1 if str(v).strip() else 0


def chu(v):
	"""Doc ra chuoi thuong, da bo khoang trang hai dau. None thanh chuoi rong."""
	return ("" if v is None else str(v)).strip()


def ngay_chu(v):
	"""Mot ngay ve dang 2026-08-15 de so sanh bang phep so sanh chuoi.

	Frappe tra ve khi thi datetime.date, khi thi chuoi, khi thi chuoi co
	ca gio. Cat 10 ky tu dau la ra ngay, va vi dang nam-thang-ngay nen so
	sanh chuoi cho dung ket qua nhu so sanh ngay - khong can getdate, tuc
	khong can Frappe.
	"""
	s = chu(v)
	return s[:10] if len(s) >= 10 else s


# --------------------------------------------------------------- tim chu

def hop_chu(r, khoa):
	"""Gop cac o can tim cua mot dong thanh mot chuoi thuong de do chu."""
	return " ".join(chu(r.get(k)) for k in khoa).lower()


def tim(dong, q, khoa):
	"""Giu lai nhung dong co chua tu khoa trong cac o da khai.

	Go nhieu tu cach nhau bang khoang trang thi phai co DU tat ca cac tu,
	khong can dung thu tu. Uyen go "hung phat 21" de tim don so 21 cua Hung
	Phat, neu doi dung nguyen cum thi khong bao gio ra.
	"""
	q = chu(q).lower()
	if not q or not khoa:
		return list(dong)
	tu = [t for t in q.split() if t]
	ra = []
	for r in dong:
		s = hop_chu(r, khoa)
		if all(t in s for t in tu):
			ra.append(r)
	return ra


# ------------------------------------------------------------ chip va dem

def dat_chip(dong, xep, boi_canh=None):
	"""Gan o _chip cho tung dong bang ham xep da khai.

	Ghi thang vao dong chu khong tao ban sao: dong o day la dictionary vua
	doc tu co so du lieu, khong ai giu tham chieu khac.
	"""
	if not xep:
		return dong
	for r in dong:
		r["_chip"] = xep(r, boi_canh)
	return dong


def phu_cua(ds_chip):
	"""Danh sach khoa cua cac chip phu - loai khong loai tru nhau."""
	return [c["k"] for c in ds_chip if c.get("phu")]


def dem_chip(dong, ds_chip):
	"""Dem so dong cua tung chip, tren TOAN BO tap khop dieu kien.

	Khoa rong la tong so dong. Chip phu dem theo o cung ten cua dong chu
	khong theo _chip, vi mot dong vua thuoc chip chinh vua co co phu.
	"""
	dem = {"": len(dong)}
	phu = set(phu_cua(ds_chip))
	for c in ds_chip:
		if c["k"] and c["k"] not in phu:
			dem[c["k"]] = 0
	for r in dong:
		k = r.get("_chip")
		if k:
			dem[k] = dem.get(k, 0) + 1
	for k in phu:
		dem[k] = sum(1 for r in dong if co(r.get(k)))
	return dem


def loc_chip(dong, chon, ds_chip):
	"""Giu lai nhung dong thuoc chip dang chon. Chon rong thi giu het."""
	chon = chu(chon)
	if not chon:
		return list(dong)
	if chon in set(phu_cua(ds_chip)):
		return [r for r in dong if co(r.get(chon))]
	return [r for r in dong if r.get("_chip") == chon]


# ------------------------------------------------------------------- cong

def cong(cot, dong):
	"""Dong TONG cuoi bang: cong dung nhung dong dang hien trong bang.

	Day la phep cong SO HOC cua cot, khong loai tru gi ca - nguoi dung nhin
	thay bao nhieu dong thi tong phai bang tong cua bay nhieu dong, neu
	khong ho lay may tinh bam lai se thay lech va mat long tin vao ca man.

	Con so "tien that" da loai don huy nam o cac the tom tat tren dau man,
	co nhan rieng. Hai con so khac nhau va deu dung, mien la noi ro.
	"""
	ra = {}
	for c in cot:
		if c["kieu"] in ("tien", "so") and not c.get("kc"):
			ra[c["k"]] = sum(so(r.get(c["k"])) for r in dong)
	return ra


def tom_tat(khai, dong, tinh_dong=None):
	"""Cac the so lon tren dau man.

	khai: danh sach (khoa, nhan, kieu). Khoa "_dong" nghia la dem so dong.

	tinh_dong la ham loc dong duoc tinh - vi du chi tinh to da ghi so va
	chua huy. Don da huy khong con la tien phai chi, cong vao la bao cao sai
	so no cua cong ty.
	"""
	dung = [r for r in dong if tinh_dong(r)] if tinh_dong else list(dong)
	ra = []
	for k, nhan, kieu in khai:
		gt = len(dung) if k == "_dong" else sum(so(r.get(k)) for r in dung)
		ra.append({"k": k, "nhan": nhan, "kieu": kieu, "gt": gt})
	return ra


# -------------------------------------------------------------- cat dong

def cat(dong, tran, day_du=0):
	"""Cat bot dong cho vua man hinh. Tra (dong da cat, tong dong, so bi cat).

	Bang ke mot thang co the len hang nghin dong. Gui het xuong dien thoai
	la treo may - man hoa don 30 ngay ra 6.127 dong da treo that hom
	12/08/2026. Ma cat mat cua ke toan thi danh sach vo dung.

	Cach xu ly: MAN HINH chi nhan toi tran, con duong xuat Excel goi voi
	day_du=1 nen luon day du. Va so bi cat phai duoc bao ra man hinh.
	"""
	tong = len(dong)
	if day_du or tran <= 0 or tong <= tran:
		return list(dong), tong, 0
	return list(dong[:tran]), tong, tong - tran


# ---------------------------------------------------------------- rap lai

def dung_bang(
	dong,
	cot_khai,
	ds_chip=None,
	chon="",
	tran=600,
	day_du=0,
	tinh_dong=None,
	tom_tat_khai=None,
	tom_tat_theo_chip=0,
):
	"""Rap tat ca lai thanh dung hop dong du lieu. Thuan tu dau den cuoi.

	Thu tu cac buoc o day la phan quan trong nhat cua ca tang khung, va no
	KHONG duoc doi:

	  1. Dem chip tren toan bo tap, truoc khi loc chip. Neu dem sau khi loc
	     thi bam vao chip Tre hen xong cac chip khac deu ve 0.
	  2. Loc theo chip dang chon.
	  3. Cong tong tren toan bo phan da loc, TRUOC khi cat dong.
	  4. Cat dong sau cung, va bao so bi cat ra ngoai.

	Buoc 3 truoc buoc 4 la luat cung. Cong sau khi cat la con so thieu tien
	ma nhin khong ra, vi no van "co ve dung".
	"""
	ds_chip = ds_chip or []
	dem = dem_chip(dong, ds_chip) if ds_chip else {"": len(dong)}
	da_loc = loc_chip(dong, chon, ds_chip) if ds_chip else list(dong)
	nen = da_loc if tom_tat_theo_chip else dong
	the = tom_tat(tom_tat_khai or [], nen, tinh_dong)
	tong_cot = cong(cot_khai, da_loc)
	hien, tong_dong, bi_cat = cat(da_loc, tran, day_du)
	return {
		"cot": cot_khai,
		"dong": hien,
		"cong": tong_cot,
		"tom_tat": the,
		"chip": {"ds": ds_chip, "chon": chu(chon), "dem": dem},
		"tong_dong": tong_dong,
		"bi_cat": bi_cat,
		"gioi_han": tran,
		"bieu_do": None,
	}
