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
	return {
		"cap_nhat_luc": str(doc.cap_nhat_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or "",
				"so_btp": d.so_btp or 0,
				"dang_giu": giu.get(d.ma_hang, 0),
				"con_nhan": (d.so_btp or 0) - giu.get(d.ma_hang, 0),
			}
			for d in doc.dong
		],
	}


@frappe.whitelist()
def luu_btp(ma_hang, so_btp):
	"""Bep sua so BTP mot mon. Giu quyen that cua nguoi sua de con vet."""
	doc = frappe.get_single("BTP Banh O")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			d.so_btp = max(0, int(so_btp or 0))
			doc.cap_nhat_luc = now_datetime()
			doc.save()
			frappe.db.commit()
			return bang_btp()
	frappe.throw("Khong thay ma %s trong bang BTP" % ma_hang)


@frappe.whitelist()
def them_ma_btp(ma_hang):
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	if not ma_hang.upper().startswith(TIEN_TO_MA):
		frappe.throw("Bang BTP chi theo doi banh o (ma %s...)" % TIEN_TO_MA)
	doc = frappe.get_single("BTP Banh O")
	if any(d.ma_hang == ma_hang for d in doc.dong):
		frappe.throw("Ma nay da co trong bang")
	c = cfg()
	k = key(c, "pancake_api_key")
	ten, anh = _tra_anh_ten(c, k, ma_hang)
	doc.append("dong", {"ma_hang": ma_hang, "ten_banh": ten, "hinh": anh})
	doc.cap_nhat_luc = now_datetime()
	doc.save()
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
