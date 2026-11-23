"""v687 (anh Viet 23/11/2026): go ma tin Zalo da bo khoi cac nhom, chay that tren MariaDB.

Su co 22/11: ban v678 bo ma tin "kt_ds_tep_loi" nhung nhom Ke toan tren site
con tich ma do; kiem_bo_loc chan luu ca trang Cai dat, token Zalo moi khong
ghi duoc, tin Zalo ngung. Tang khung da chot phep thuan go_ma_da_bo voi frappe
gia. Ca nay chung minh tren site: frappe.get_all loc dung dong con theo
parent/parenttype/parentfield, frappe.db.set_value ghi duoc vao bang con
"Vagabond Kenh Zalo", va dong cua Cai dat THAT khong bi dung toi.

Du lieu: dong con gia, parent la ten rieng cua ca (khong phai "Vagabond
Settings"), nam trong diem luu cua nen.py nen bien mat sau ca.
"""

import frappe

from vagabond import kenh_zalo as kz
from vagabond.khung.kiem_that.nen import ca, la, dung


def _dong(cha, ten, tin):
	d = frappe.get_doc(dict(doctype="Vagabond Kenh Zalo", parent=cha, parenttype="Vagabond Settings",
		parentfield="zalo_nhom", idx=1, ten_nhom=ten, tin_nhan=tin))
	d.name = frappe.generate_hash(length=10)
	d.db_insert()
	return d.name


def _that():
	return sorted((r.name, r.tin_nhan or "") for r in frappe.get_all("Vagabond Kenh Zalo", filters={
		"parent": "Vagabond Settings", "parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
		fields=["name", "tin_nhan"]))


@ca("v687 site: buoc don sau cap nhat app go ma tin da bo cua dung dong cua ca, khong dung Cai dat that")
def _():
	cha = "KT687-" + frappe.generate_hash(length=8)
	truoc = _that()
	cu = _dong(cha, "Nhom gia cu", "ht_ds_tep_loi, kt_ds_tep_loi")
	sach = _dong(cha, "Nhom gia sach", "ht_ds_tep_loi")
	ra = kz.don_tin_da_bo(cha=cha)
	la("bao lai nhom va ma da go", ra, [{"nhom": "Nhom gia cu", "bo": ["kt_ds_tep_loi"]}])
	la("dong cu da sach", frappe.db.get_value("Vagabond Kenh Zalo", cu, "tin_nhan"), "ht_ds_tep_loi")
	la("dong sach giu nguyen", frappe.db.get_value("Vagabond Kenh Zalo", sach, "tin_nhan"), "ht_ds_tep_loi")
	la("chay lai khong con gi de go", kz.don_tin_da_bo(cha=cha), [])
	la("dong cua Cai dat that giu nguyen", _that(), truoc)
	dung("bang nhom sau khi go qua duoc kiem luu", kz.kiem_bo_loc([{"ten_nhom": "Nhom gia cu",
		"tin_nhan": frappe.db.get_value("Vagabond Kenh Zalo", cu, "tin_nhan")}]) == "")
