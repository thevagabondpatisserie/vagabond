"""Dung lai moi truong tu them do ma nguon khai. Chay moi lan Migrate.

Vi sao co tep nay - va vi sao dong tuong ung trong patches.txt PHAI DOI
sau moi lan deploy
------------------------------------------------------------------------
Frappe Cloud tu chon giua hai kieu cap nhat site: "Pull" (khoang 5 giay,
chi thay ma nguon) va "Migrate" (khoang 47 giay, co chay bench migrate).
No chon bang cach nhin danh sach TEP DA DOI giua hai ban dung, va chi chon
Migrate khi trong do co mot trong nhung duong dan sau:

    <app>/patches.txt
    <app>/hooks.py
    <app>/fixtures/
    <app>/<mo dun>/custom/
    <app>/<mo dun>/<doctype>/<ten>/<ten>.json
    frappe/geo/languages.json

Doi nhanh git cung ep Migrate.

Doi chieu voi lich su cua chinh minh thi khop tuyet doi: sau dot v179 man
Bao gia tra 500 vi thieu ba cot, va sau dot v177 man Bao gia chet han. Ca
hai dot do chi sua tep .py va .js, KHONG cham vao mot duong dan nao ben
tren, nen Frappe Cloud chon "Pull", after_migrate khong chay, va cac truong
tu them do ma nguon khai khong duoc dung. Anh Viet phai bam Migrate tay.

Nen thay vi dung CI/CD ben ngoai, cach chac an hon la LUON TAO MOT THAY
DOI trong patches.txt o moi lan deploy. Tep dat_phien_ban.py lam viec do tu
dong: no dong so phien ban vao cuoi dong patch, nen dong nay khac di sau
moi dot, Frappe Cloud luon thay patches.txt doi va luon chon Migrate.

Frappe nho patch da chay theo NGUYEN VAN ca dong ke ca phan ghi chu sau
dau thang, nen "vagabond.patches.dong_bo_cau_truc #v181" va "... #v182" la
hai dong khac nhau va deu duoc chay.

Ham nay phai LAP LAI DUOC khong gioi han lan: create_custom_fields voi
update=True la thao tac lap lai duoc, khai lai lan thu muoi cung khong doi
gi.
"""

import frappe


def execute():
	from vagabond import truong_tu_them

	try:
		truong_tu_them.dung()
	except Exception:
		# Patch hong KHONG duoc chan ca lan migrate: chan thi site khong len
		# duoc phien ban moi, ma loi that thi chi la thieu vai truong.
		frappe.log_error(frappe.get_traceback(), "patches: dong bo cau truc")

	# Danh muc 581 ngan hang theo tep chuyen tien lo cua MB Biz.
	#
	# Chay lai duoc, va chi THEM cai con thieu - khong dung vao ngan hang da
	# co, vi chung dang duoc cac Bank Account tro toi.
	try:
		from vagabond import ngan_hang

		kq = ngan_hang.nap_danh_muc()
		if kq.get("them"):
			frappe.logger().info("dong_bo_cau_truc: them %d ngan hang" % kq["them"])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: nap danh muc ngan hang")
