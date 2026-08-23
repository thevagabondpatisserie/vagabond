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

	# Tra lai che do thue cho cac to bao gia bi cot "default" cua dot v228
	# ghi de. Chi sua o che do, khong dung vao mot o tien nao, va lap lai
	# duoc: chay lan thu hai thi khong con to nao thoa dieu kien.
	try:
		from vagabond import bao_gia

		kq = bao_gia.sua_kieu_thue_bi_dat_mac_dinh()
		if kq.get("sua"):
			frappe.logger().info(
				"dong_bo_cau_truc: tra lai cach tinh thue cho %d to bao gia"
				% len(kq["sua"])
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: sua kieu thue bao gia")

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

	# Danh muc loai chung tu dinh kem, va chuyen phieu de nghi chi mot dong
	# sang bang ke nhieu dong (anh Viet 19/08/2026).
	#
	# Chay lai duoc: chi tao dong danh muc con thieu, va chi chuyen phieu nao
	# CHUA co dong nao trong bang ke.
	try:
		from vagabond import de_nghi_chi

		de_nghi_chi.dung_danh_muc_chung_tu()
		kq = de_nghi_chi.chuyen_phieu_mot_dong()
		if kq.get("chuyen"):
			frappe.logger().info(
				"dong_bo_cau_truc: chuyen %d phieu de nghi chi sang bang ke"
				% kq["chuyen"]
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: chuyen de nghi chi sang bang ke")

	# Bieu mau in do ma nguon giu. Xem vagabond/mau_in/__init__.py.
	#
	# Chay lai duoc: chi ghi de khi noi dung tep .html trong repo KHAC voi
	# ban dang nam trong co so du lieu.
	try:
		from vagabond import mau_in

		kq = mau_in.dong_bo()
		if kq.get("da_sua"):
			frappe.logger().info(
				"dong_bo_cau_truc: cap nhat mau in %s" % ", ".join(kq["da_sua"])
			)
		if kq.get("chua_co"):
			frappe.logger().info(
				"dong_bo_cau_truc: chua co ban ghi Print Format cho %s"
				% ", ".join(kq["chua_co"])
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: dong bo mau in")

	# Web Page do ma nguon giu. Xem vagabond/trang/__init__.py.
	#
	# Chay lai duoc: chi ghi de khi noi dung trong repo KHAC voi ban dang nam
	# trong co so du lieu. Khong tu tao trang moi, khong ha so APPVER.
	#
	# Nuot loi: dinh tuyen hay noi dung mot trang hong thi cung lam mot trang
	# sai, con nem loi o day la HONG CA LAN MIGRATE, tuc la truong moi khong
	# duoc dung va ca tiem ket. Nen ghi nhat ky roi di tiep.
	try:
		from vagabond import trang

		kq = trang.dong_bo()
		for khoa, nhan in (("da_sua", "cap nhat"), ("chua_co", "chua co"),
				("bo_qua", "BO QUA")):
			if kq.get(khoa):
				frappe.logger().info(
					"dong_bo_cau_truc: trang web %s: %s"
					% (nhan, "; ".join(kq[khoa]))
				)
		if kq.get("bo_qua"):
			# Bo qua la chuyen phai co nguoi doc, khong duoc chim trong log.
			frappe.log_error(
				"\n".join(kq["bo_qua"]),
				"Web Page bi bo qua khi deploy, doc vagabond/trang/__init__.py",
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: dong bo Web Page")

	# Quyen doc Purchase Order cho ba vai duyet phieu chi (anh Viet 21/08/2026).
	#
	# Tu v265 phieu tra truoc neo vao Purchase Order, ma ERPNext doc lai
	# chung tu goc moi lan LUU phieu, nen ai khong doc duoc don mua hang thi
	# khong duyet duoc phieu. Doc `vagabond/quyen_ap.py` de biet vi sao phai
	# di qua ham cua Frappe chu khong chen tay dong Custom DocPerm.
	#
	# Chay lai duoc: chi cap cai con thieu.
	try:
		from vagabond import quyen_ap

		kq = quyen_ap.dung()
		if kq.get("them"):
			frappe.logger().info(
				"dong_bo_cau_truc: cap %d quyen cho vai duyet chi: %s"
				% (len(kq["them"]), ", ".join(kq["them"]))
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: quyen vai duyet chi")

	# Tach o "San xuat" cu thanh hai o: "San xuat" cua bep va "Tong nha in
	# giao" cua nha in (anh Viet chot 21/08/2026). Chuyen so cua cac dong HOP
	# sang o moi, dong banh le giu nguyen.
	#
	# Chay lai duoc: chi chuyen khi o moi dang bang 0.
	try:
		from vagabond import mua_vu

		kq = mua_vu.chuyen_so_nha_in()
		if kq.get("mua_da_doi"):
			frappe.logger().info(
				"dong_bo_cau_truc: chuyen so nha in cho %d mua vu" % kq["mua_da_doi"]
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: chuyen so nha in mua vu")

	# Mo so nhap san luong theo ngay (anh Viet 22/08/2026). O "San xuat" cu
	# vua la so go tay vua la tong cac dong bep nhap, va cai sau GHI DE cai
	# truoc - go 1700 cho ca mua roi bep nhap 120 mot ngay la mat 1700.
	#
	# Tu ban nay tach lam hai o va o San xuat la tong. Ham duoi dua so cu vao
	# o go tay moi. Chay lai duoc: chi dat khi o moi dang bang 0.
	try:
		from vagabond import mua_vu

		kq = mua_vu.mo_so_san_luong_ngay()
		if kq.get("mua_da_doi"):
			frappe.logger().info(
				"dong_bo_cau_truc: mo so san luong ngay cho %d mua vu" % kq["mua_da_doi"]
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: mo so san luong ngay mua vu")
