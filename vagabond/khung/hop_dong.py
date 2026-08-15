"""HOP DONG DU LIEU cua man danh sach - ke thua tu bao_cao.py.

TANG THUAN. Khong import frappe. Chay duoc bang python3 tran.

Vi sao co file nay
------------------
Phan he Bao cao la cho DUY NHAT trong he da lam theo kieu thu vien: moi bao
cao tra ve cung mot hinh dang {cot, dong, cong, bieu_do}, nen man hinh chi
viet mot lan. Ket qua thay ro hom 14/08/2026: them bon bao cao BC13 den BC16
chi mat phan may chu, giao dien tu hien, khong sua mot dong JavaScript nao.

Cung tuan do, sua cach hien thi the thanh vien thi phai sua tay o hai cho
voi ma dan trung nhau, va chinh vi dan trung nen moi de ra loi cat mat chu.

Hai viec, hai ket cuc, khac nhau dung o cho co hop dong du lieu hay khong.
File nay dem hop dong cua Bao cao mo rong ra cho MOI man danh sach.

Hop dong
--------
Ham dung danh sach luon tra ve dung mot dictionary nhu sau, khong bao gio
them mot hinh dang thu hai:

    {
      "ma":        ma man, vi du "PO"
      "ten":       ten hien tren dau man
      "cot":       [ {k, nhan, kieu, kc?, rong?} ... ]   thu tu = thu tu cot
      "dong":      [ {khoa cot: gia tri} ... ]           DA cat con toi da tran
      "cong":      { khoa cot: tong so }                 dong TONG cuoi bang
      "tom_tat":   [ {k, nhan, kieu, gt} ... ]           the so lon tren dau
      "chip":      { "ds": [...], "chon": "", "dem": {...} }
      "loc":       [ khai bao bo loc kem gia tri dang ap ]
      "tong_dong": so dong that su khop dieu kien, TRUOC khi cat
      "bi_cat":    so dong bi giau di, 0 neu khong cat
      "gioi_han":  tran dong cua man nay
      "sap":       cau sap xep dang dung, de man hinh to mui ten len cot
      "bieu_do":   None hoac {kieu, nhan, gia_tri} - de trong cho sau nay
    }

Ba dieu bat buoc, khong duoc pha:

  1. TONG luon tinh trong TOAN BO tap khop dieu kien, roi moi cat dong.
     Neu cong sau khi cat thi ke toan doi chieu se thieu tien, ma khong ai
     nhin ra vi so nao cung "co ve dung".
  2. Cat dong phai BAO ra man hinh. Cat lang le la noi doi.
  3. Duong xuat Excel luon lay day du, khong bao gio bi tran chan.

Tu vung kieu cot
----------------
Dong lai dung sau kieu, khong duoc de moi man tu dat ten kieu moi:

    chu        canh trai
    tien       canh phai, dinh dang tien Viet, cong duoc
    so         canh phai, cong duoc
    phan_tram  canh phai, hau to %
    ngay       canh phai, dinh dang ngay Viet
    chip       o mau, gia tri la khoa chip, man hinh tra bang de lay ten

Co kc (khong cong) giu nguyen y nghia tu bao_cao.py: bo cot ra khoi dong
TONG. Can cho nhung cot ma cong lai la vo nghia - vi du don gia, cong don
gia cua ba mon khac nhau ra mot con so khong dai dien cho cai gi.

Tu vung kieu bo loc
-------------------
Sau kieu, khai bao chu khong viet tay (tieu chuan so 5):

    ngay        khoang tu ngay den ngay, hoac so ngay gan day
    chon_mot    mot gia tri trong danh sach
    chon_nhieu  nhieu gia tri trong danh sach
    tim_chu     go chu, may chu tim trong cac truong da khai
    khoang_so   tu so den so
    co          co bat tat, bat thi them dieu kien

Bo loc phai chay o MAY CHU (tieu chuan so 7). Keo het ve may khach roi loc
bang JavaScript la cach lam ra man 6.127 dong treo dien thoai hom 12/08.
"""

KIEU_COT = ("chu", "tien", "so", "phan_tram", "ngay", "chip")
KIEU_LOC = ("ngay", "chon_mot", "chon_nhieu", "tim_chu", "khoang_so", "co")

# Tran mac dinh. bao_cao.py da chay 600 dong tot tren dien thoai that.
# Man nao nang hon thi tu khai tran rieng, nhung khong duoc bo tran.
GIOI_HAN_DONG = 600


class LoiKhaiBao(Exception):
	"""Khai bao man sai. Nem ngay luc nap mo dun chu khong doi toi luc chay.

	Co y de vo khi deploy: mot cai typo ten kieu cot ma de no im lang thi
	11 gio dem ngoai quay moi phat hien, luc do khong con ai sua.
	"""


def cot(*bo):
	"""Dung danh sach cot.

	Moi cot nhan mot trong hai dang:
	  - tuple: (khoa, nhan, kieu) hoac (khoa, nhan, kieu, khong_cong)
	  - dict:  {k, nhan, kieu, kc?, rong?, bang?}

	Dang dict de danh cho cot chip can kem bang mau, va cho cot muon ghim
	chieu rong. Dang tuple cho phan con lai, vi 90% cot chi can ba thu.
	"""
	ra = []
	thay = set()
	for b in bo:
		c = dict(b) if isinstance(b, dict) else {
			"k": b[0],
			"nhan": b[1],
			"kieu": b[2],
		}
		if not isinstance(b, dict) and len(b) > 3 and b[3]:
			c["kc"] = 1
		if not c.get("k"):
			raise LoiKhaiBao("Cot thieu khoa k.")
		if c["k"] in thay:
			raise LoiKhaiBao("Cot %s khai hai lan." % c["k"])
		thay.add(c["k"])
		if c.get("kieu") not in KIEU_COT:
			raise LoiKhaiBao(
				"Cot %s co kieu %r khong nam trong %s."
				% (c["k"], c.get("kieu"), ", ".join(KIEU_COT))
			)
		ra.append(c)
	if not ra:
		raise LoiKhaiBao("Man danh sach phai co it nhat mot cot.")
	return ra


def loc(*bo):
	"""Dung danh sach bo loc.

	Moi bo loc la mot dict:
	  {k, nhan, kieu, truong?, tim?, nguon?, mac_dinh?, dk?}

	  k         ten tham so tren duong goi API
	  nhan      chu hien tren thanh loc
	  kieu      mot trong KIEU_LOC
	  truong    ten truong trong co so du lieu de dung dieu kien SQL
	  tim       rieng kieu tim_chu: danh sach truong de do chu vao
	  nguon     rieng chon_mot / chon_nhieu: ten mot ham tra ve danh sach
	  mac_dinh  gia tri khi nguoi dung chua chon gi
	  dk        rieng kieu co: dieu kien SQL ap khi co bat
	"""
	ra = []
	thay = set()
	for b in bo:
		c = dict(b)
		if not c.get("k"):
			raise LoiKhaiBao("Bo loc thieu khoa k.")
		if c["k"] in thay:
			raise LoiKhaiBao("Bo loc %s khai hai lan." % c["k"])
		thay.add(c["k"])
		if c.get("kieu") not in KIEU_LOC:
			raise LoiKhaiBao(
				"Bo loc %s co kieu %r khong nam trong %s."
				% (c["k"], c.get("kieu"), ", ".join(KIEU_LOC))
			)
		if c["kieu"] == "tim_chu" and not c.get("tim"):
			raise LoiKhaiBao("Bo loc tim chu %s phai khai truong tim." % c["k"])
		if c["kieu"] in ("ngay", "chon_mot", "chon_nhieu", "khoang_so") and not (
			c.get("truong") or c.get("tay")
		):
			raise LoiKhaiBao(
				"Bo loc %s phai khai truong, hoac danh dau tay=1 neu mo dun tu xu ly."
				% c["k"]
			)
		ra.append(c)
	return ra


def chip(*bo):
	"""Danh sach chip trang thai. Chip dau tien luon la Tat ca.

	Moi chip: {k, ten, ic}. Khoa rong nghia la khong loc gi.

	Chip "phu" (co phu=1) khong loai tru nhau voi cac chip khac. Vi du chip
	Da sua tren man hoa don: mot to vua Chua ghi so vua Da sua thi phai dem
	o ca hai cho. De no thanh chip loai tru la cuoi ngay bam Chua ghi so se
	bo sot dung may to dang nghi nhat.
	"""
	ra = [dict(b) for b in bo]
	if not ra or ra[0].get("k") not in ("", None):
		raise LoiKhaiBao("Chip dau tien phai la Tat ca voi khoa rong.")
	ra[0]["k"] = ""
	thay = set()
	for c in ra:
		if c["k"] in thay:
			raise LoiKhaiBao("Chip %s khai hai lan." % c["k"])
		thay.add(c["k"])
		if not c.get("ten"):
			raise LoiKhaiBao("Chip %s thieu ten." % c["k"])
	return ra


def bang(
	ma,
	ten,
	doctype,
	quyen,
	loi_quyen,
	cot,
	truong,
	loc=None,
	chip=None,
	xep=None,
	them=None,
	truoc=None,
	sap="modified desc",
	tran=GIOI_HAN_DONG,
	tinh_dong=None,
	tom_tat=None,
	tom_tat_theo_chip=0,
	dieu_kien=None,
):
	"""Khai bao mot man danh sach. Tra ve dictionary, kiem ngay luc nap.

	ma                ma ngan cua man, hien trong nhat ky loi
	ten               ten tieng Viet hien tren dau man
	doctype           bang du lieu goc trong ERPNext
	quyen             tap vai tro duoc vao
	loi_quyen         cau tieng Viet bao khi khong du quyen
	cot               danh sach cot, dung ham cot() o tren
	truong            danh sach truong lay tu co so du lieu
	loc               danh sach bo loc, dung ham loc()
	chip              danh sach chip trang thai, dung ham chip()
	xep(r, boi_canh)  ham THUAN xep mot dong vao mot chip
	them(r, boi_canh) ham THUAN tinh them cac o dan xuat cho mot dong
	truoc(dong, bc)   ham DUOC PHEP doc co so du lieu MOT lan cho ca tap,
	                  tra ve dict nhet them vao boi_canh
	sap               cau order_by gui xuong co so du lieu
	tran              so dong toi da tra ve man hinh
	tinh_dong(r)      ham THUAN: dong nay co duoc tinh vao tien that khong
	tom_tat           [(khoa, nhan, kieu)] cac the so lon tren dau man
	tom_tat_theo_chip 0 thi the so tinh tren ca tap, 1 thi tinh theo chip
	dieu_kien         dict dieu kien SQL luon ap, vi du docstatus < 3

	Ba tham so xep, them, tinh_dong phai la ham THUAN: nhan dictionary vao,
	tra gia tri ra, khong goi frappe, khong doc co so du lieu. Do la dieu
	kien de bo kiem thu A6 op vao duoc ma khong phai dung ca mot site.

	Rieng truoc() duoc phep doc co so du lieu, va la cho DUY NHAT duoc
	phep. Co man can mot mieng du lieu phu khong nam trong bang goc - vi du
	man hoa don mua phai biet to nao da co ban thay the, ma dieu do chi tra
	duoc bang mot cau hoi nua xuong co so du lieu. Cho no chay MOT lan cho
	ca tap roi nhet ket qua vao boi canh, thay vi de moi dong tu di hoi:
	mot cau hoi thay vi 600 cau, va them() van thuan nen van kiem thu duoc.
	"""
	if not ma or not ten or not doctype:
		raise LoiKhaiBao("Man danh sach phai co ma, ten va doctype.")
	if not quyen:
		raise LoiKhaiBao("Man %s chua khai quyen. Khong co man nao mo cho tat ca." % ma)
	kh_cot = {c["k"] for c in cot}
	for t in tom_tat or []:
		if t[2] not in KIEU_COT:
			raise LoiKhaiBao("The tom tat %s co kieu %r la." % (t[0], t[2]))
	if chip and not xep:
		raise LoiKhaiBao("Man %s co chip nhung chua khai ham xep." % ma)
	if xep and not chip:
		raise LoiKhaiBao("Man %s co ham xep nhung chua khai danh sach chip." % ma)
	return {
		"ma": ma,
		"ten": ten,
		"doctype": doctype,
		"quyen": set(quyen),
		"loi_quyen": loi_quyen,
		"cot": cot,
		"kh_cot": kh_cot,
		"truong": list(truong),
		"loc": loc or [],
		"chip": chip or [],
		"xep": xep,
		"them": them,
		"truoc": truoc,
		"sap": sap,
		"tran": int(tran),
		"tinh_dong": tinh_dong,
		"tom_tat": list(tom_tat or []),
		"tom_tat_theo_chip": int(tom_tat_theo_chip or 0),
		"dieu_kien": dict(dieu_kien or {}),
	}
