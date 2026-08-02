"""Bang BTP banh o - so hoa tam bang trang cua bep.

Bep moi ngay du tru so banh BTP cap 2 (dong lanh, cho finish) du dung cho
2-3 ngay, truoc gio viet whiteboard roi chup gui sales. Tu 01/08 bep nhap
thang vao day tren dien thoai (man hinh /btp), sales thay tuc thi.

So sales can la "CON NHAN" = BTP san - don da nhan ma bep chua finish
(chot voi anh Viet 01/08: tru don cua HOM NAY + 2 ngay ke chua chot so).
Con nhan ve 0 la sales lai khach sang mon con nhieu - dung nhu cach van
hanh cu, chi bo cong chup bang.
"""

import frappe
from frappe.utils import add_days, getdate, now_datetime

from vagabond.kiem_banh import TIEN_TO_MA, _tra_anh_ten
from vagabond.lib import cfg, key

SO_NGAY_GIU = 3  # hom nay + 2 ngay ke

# CHI BEP duoc sua so BTP (anh Viet chot 01/08: bep nhap thi bep chiu
# trach nhiem so). Giam doc / System Manager van sua duoc de go roi.
BEP_EMAILS = {
	"djvinci05@gmail.com",  # Duy
	"hieu0703573936@gmail.com",  # Hieu
	"lethilinh051996@gmail.com",  # Linh
	"ngochan41096@gmail.com",  # Han
}


# Vai tro bep - de sau nay them nguoi thi chi can gan role, khoi sua code.
BEP_ROLES = {"Bếp phó", "Bếp trưởng", "System Manager"}


def _duoc_sua_btp():
	user = frappe.session.user
	if user in BEP_EMAILS:
		return True
	return bool(BEP_ROLES & set(frappe.get_roles(user)))


@frappe.whitelist()
def quyen_btp():
	"""Man hinh hoi de biet co mo o sua BTP cho nguoi nay khong."""
	return {"sua": 1 if _duoc_sua_btp() else 0}


def _giu_ngay_mai():
	"""Don giao NGAY MAI (da dat + phat sinh + cho chot) neu so chua chot.

	Y Linh 01/08: sau 12h trua, do decor cho ngay mai khong kip chuan bi
	them - nen don giao ngay mai chi nhan trong pham vi so "du decor".
	"""
	giu = {}
	ma_doc = "KB-%s" % add_days(getdate(), 1)
	if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
		return giu
	kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
	if kb.tinh_trang == "Da chot":
		return giu
	for d in kb.dong:
		giu[d.ma_hang] = (
			giu.get(d.ma_hang, 0)
			+ (d.da_dat or 0)
			+ (d.phat_sinh or 0)
			+ (d.cho_chot or 0)
		)
	return giu


def _giu_theo_ma():
	"""Tong (da dat + phat sinh + cho chot) cac ngay CHUA CHOT trong cua so."""
	giu = {}
	hom_nay = getdate()
	for i in range(SO_NGAY_GIU):
		ma_doc = "KB-%s" % add_days(hom_nay, i)
		if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
			continue
		kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
		if kb.tinh_trang == "Da chot":
			continue
		for d in kb.dong:
			giu[d.ma_hang] = (
				giu.get(d.ma_hang, 0)
				+ (d.da_dat or 0)
				+ (d.phat_sinh or 0)
				+ (d.cho_chot or 0)
			)
	return giu


@frappe.whitelist()
def bang_btp():
	"""Du lieu cho man hinh /btp va nhan BTP tren man kiem banh."""
	doc = frappe.get_single("BTP Banh O")
	giu = _giu_theo_ma()
	giu_mai = _giu_ngay_mai()
	dong = []
	for d in doc.dong:
		decor = min(d.so_decor or 0, d.so_btp or 0)
		dong.append(
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or "",
				"so_btp": d.so_btp or 0,
				"so_decor": d.so_decor or 0,
				"dang_giu": giu.get(d.ma_hang, 0),
				"con_nhan": (d.so_btp or 0) - giu.get(d.ma_hang, 0),
				"giao_mai": decor - giu_mai.get(d.ma_hang, 0),
			}
		)
	return {"cap_nhat_luc": str(doc.cap_nhat_luc or ""), "dong": dong}


@frappe.whitelist()
def luu_btp(ma_hang, so_btp):
	"""Bep sua so BTP mot mon. Giu quyen that cua nguoi sua de con vet."""
	if not _duoc_sua_btp():
		frappe.throw("Cột BTP sẵn chỉ bếp được nhập - bếp nhập thì bếp chịu trách nhiệm số")
	doc = frappe.get_single("BTP Banh O")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			d.so_btp = max(0, int(so_btp or 0))
			doc.cap_nhat_luc = now_datetime()
			# Cong da khoa o _duoc_sua_btp roi. Doctype "BTP Banh O" chi cho
			# Sales User / Stock User ghi, bep khong co role do nen doc.save()
			# thuong se bao 403 va man hinh nhay so ve 0.
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			return bang_btp()
	frappe.throw("Khong thay ma %s trong bang BTP" % ma_hang)


@frappe.whitelist()
def luu_decor(ma_hang, so_decor):
	"""Bep sua so BTP da du do decor - so nay quyet dinh nhan don ngay mai."""
	if not _duoc_sua_btp():
		frappe.throw("Cột Đủ decor chỉ bếp được nhập - bếp nhập thì bếp chịu trách nhiệm số")
	doc = frappe.get_single("BTP Banh O")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			d.so_decor = max(0, int(so_decor or 0))
			doc.cap_nhat_luc = now_datetime()
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			return bang_btp()
	frappe.throw("Khong thay ma %s trong bang BTP" % ma_hang)


@frappe.whitelist()
def them_ma_btp(ma_hang):
	if not _duoc_sua_btp():
		frappe.throw("Bảng BTP chỉ bếp được thêm mã")
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	if not ma_hang.upper().startswith(TIEN_TO_MA):
		frappe.throw("Bang BTP chi theo doi banh o va banh si (ma %s...)" % "/".join(TIEN_TO_MA))
	doc = frappe.get_single("BTP Banh O")
	if any(d.ma_hang == ma_hang for d in doc.dong):
		frappe.throw("Ma nay da co trong bang")
	c = cfg()
	k = key(c, "pancake_api_key")
	ten, anh = _tra_anh_ten(c, k, ma_hang)
	doc.append("dong", {"ma_hang": ma_hang, "ten_banh": ten, "hinh": anh})
	doc.cap_nhat_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang_btp()


@frappe.whitelist()
def gieo_tu_kiem_banh():
	"""Do san cac ma dang co trong bang kiem 4 ngay toi - bep khoi go tay."""
	doc = frappe.get_single("BTP Banh O")
	co = {d.ma_hang for d in doc.dong}
	hom_nay = getdate()
	them = 0
	for i in range(4):
		ma_doc = "KB-%s" % add_days(hom_nay, i)
		if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
			continue
		kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
		for d in kb.dong:
			if d.ma_hang in co:
				continue
			doc.append("dong", {"ma_hang": d.ma_hang, "ten_banh": d.ten_banh, "hinh": d.hinh})
			co.add(d.ma_hang)
			them += 1
	if them:
		doc.cap_nhat_luc = now_datetime()
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	return {"them": them}
