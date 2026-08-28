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
from frappe.utils import cint, flt


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

	# Vai duoc phep ghi so hoa don mua co don gia khac phieu nhap
	# (anh Viet 26/08/2026).
	#
	# Ca that: Uyen dat hat de luc nha cung cap con khuyen mai 161.000 mot
	# tui, den luc ho xuat hoa don thi het chuong trinh nen ghi 280.000.
	# Hang da ve kho, hoa don la that, ma ERPNext chan cung khong cho ghi so
	# vi Buying Settings dang bat "maintain_same_rate" muc "Stop".
	#
	# Khong tat cai chan do: no van dang giu cho nhung ca go nham gia. Chi
	# khai VAI DUOC VUOT, dung co ma ERPNext thiet ke san. Ke toan vuot
	# duoc, thu mua thi khong - nguoi nhap gia khong tu duyet gia cua chinh
	# minh.
	#
	# Chay lai duoc: chi dat khi o do con trong, khong de len lua chon sau
	# nay cua anh Viet.
	try:
		if cint(frappe.db.get_single_value("Buying Settings", "maintain_same_rate")):
			dang = (
				frappe.db.get_single_value("Buying Settings", "role_to_override_stop_action") or ""
			).strip()
			if not dang:
				from vagabond import doi_chieu_mua

				vai = doi_chieu_mua.VAI_VUOT_GIA_MAC_DINH
				if frappe.db.exists("Role", vai):
					frappe.db.set_single_value("Buying Settings", "role_to_override_stop_action", vai)
					frappe.clear_cache(doctype="Buying Settings")
					frappe.logger().info(
						"dong_bo_cau_truc: khai vai vuot lech gia mua = %s" % vai
					)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: vai vuot lech gia mua")

	# Mo duong cho thu mua va thu kho o buoc nhap kho (anh Viet 26/08/2026).
	#
	# Uyen de xuat, anh Viet duyet: dat hang theo bang gia, giao toi moi biet
	# ben ban dang khuyen mai hoac co hang tang kem, nen gia thuc nhan khac
	# gia dat. Mua thit heo 3 kg thi ho giao 3,02 kg. ERPNext dang chan ca
	# hai, ma ngay nao cung gap.
	#
	# Doi "Stop" thanh "Warn" chu khong tat han: van hien canh bao de nguoi
	# ta biet minh vua doi gia. Con hang rao THAT nam o cho khac va manh hon
	# nhieu - `mua_dich_vu.chan_lech_tong` khong cho ghi so khi tong tien
	# phieu lech voi ban hoa don dien tu da gui co quan thue. Doc dau tep
	# `vagabond/gia_khi_nhan.py`.
	#
	# Chay lai duoc: chi doi khi o do dang o dung gia tri chan cu, khong de
	# len lua chon sau nay cua anh Viet.
	try:
		if (frappe.db.get_single_value("Buying Settings", "maintain_same_rate_action") or "") == "Stop":
			frappe.db.set_single_value("Buying Settings", "maintain_same_rate_action", "Warn")
			frappe.clear_cache(doctype="Buying Settings")
			frappe.logger().info("dong_bo_cau_truc: lech gia mua chuyen tu Stop sang Warn")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: noi chan lech gia mua")

	# Nhan du toi 10 phan tram khong bi chan. Du cho can dong (3 kg thanh
	# 3,02 kg la 0,7 phan tram) va cho khuyen mai mua muoi tang mot. Qua muoi
	# phan tram van chan, vi luc do nhieu kha nang la go nham so.
	try:
		from vagabond import gia_khi_nhan

		if not flt(frappe.db.get_single_value("Stock Settings", "over_delivery_receipt_allowance")):
			frappe.db.set_single_value(
				"Stock Settings", "over_delivery_receipt_allowance", gia_khi_nhan.NGUONG_NHAN_DU
			)
			frappe.clear_cache(doctype="Stock Settings")
			frappe.logger().info(
				"dong_bo_cau_truc: mo nguong nhan du %s phan tram" % gia_khi_nhan.NGUONG_NHAN_DU
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: nguong nhan du")

	# NGUONG VUOT HOA DON, day moi la nut that that su cua Uyen
	# (anh Viet 28/08/2026).
	#
	# Uyen bao: "khi gia hoa don thuc te khac gia tren PO/PNK, ke toan
	# khong the noi PNK vao Hoa don de hach toan", phai sua PO roi huy PNK
	# roi tao PNK moi.
	#
	# Da soi ky: KHONG PHAI do `maintain_same_rate`, o do dang de "Warn"
	# tu v318 nen chi nhac chu khong chan. Cai chan that la
	# `Accounts Settings.over_billing_allowance` dang bang 0 va
	# `role_allowed_to_over_bill` con trong. Voi hai o do, ERPNext chan
	# MOI to hoa don co so tien nhinh hon phieu nhap du chi mot dong:
	#
	#     Cannot overbill for Item ... more than ...
	#
	# Vi the ke toan thay "sua gia thi khong luu duoc" ma khong hieu vi
	# sao, boi cau bao nhac toi so tien chu khong nhac toi gia.
	#
	# Hai lop, co y de nhu vay:
	#   - Nguong 10 phan tram: cho moi nguoi, du cho lech gia thuong ngay
	#     (khuyen mai het han, can dong, phi giao hang gop vao).
	#   - Vai vuot: ke toan vuot duoc moi muc, vi to hoa don la giay to
	#     that da gui co quan thue, khong the bat no khop voi don dat hang.
	#
	# Van con hang rao: qua 10 phan tram thi thu mua bi chan, luc do nhieu
	# kha nang la go nham so chu khong phai gia doi that.
	#
	# Chay lai duoc: chi dat khi o do con trong hoac bang 0.
	try:
		if not flt(frappe.db.get_single_value("Accounts Settings", "over_billing_allowance")):
			frappe.db.set_single_value("Accounts Settings", "over_billing_allowance", 10)
			frappe.clear_cache(doctype="Accounts Settings")
			frappe.logger().info("dong_bo_cau_truc: mo nguong vuot hoa don 10 phan tram")
		if not (frappe.db.get_single_value("Accounts Settings", "role_allowed_to_over_bill") or "").strip():
			if frappe.db.exists("Role", "Accounts Manager"):
				frappe.db.set_single_value(
					"Accounts Settings", "role_allowed_to_over_bill", "Accounts Manager"
				)
				frappe.clear_cache(doctype="Accounts Settings")
				frappe.logger().info("dong_bo_cau_truc: khai vai vuot hoa don = Accounts Manager")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: nguong vuot hoa don")

	# Chenh lech gia giua phieu nhap va hoa don phai chay vao GIA TRI TON
	# KHO, khong duoc bo lo (anh Viet 28/08/2026, Khoi 1 muc 4).
	#
	# ERPNext co san o "Set Landed Cost Based on Purchase Invoice Rate".
	# Bat len thi khi hoa don ghi gia khac phieu nhap, may tu dieu chinh
	# gia tri ton kho theo gia hoa don, phan da xuat dung thi day sang tai
	# khoan dieu chinh cua cong ty. Tat thi ton kho giu mai gia tam tinh
	# cua don dat hang, va gia von thang sau sai theo.
	#
	# Chay lai duoc: chi bat khi dang tat.
	try:
		if not cint(frappe.db.get_single_value(
			"Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate"
		)):
			frappe.db.set_single_value(
				"Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate", 1
			)
			frappe.clear_cache(doctype="Buying Settings")
			frappe.logger().info("dong_bo_cau_truc: bat dieu chinh gia tri ton kho theo gia hoa don")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "patches: gia tri ton kho theo hoa don")
