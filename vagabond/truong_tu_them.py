"""Cac truong tu them do MA NGUON khai, dung lai sau moi lan deploy.

Vi sao co file nay
------------------
Toan bo truong tu them cua he tu truoc toi nay deu bam tay tren Desk. Hai
cai gia phai tra: site thu va site that lech nhau ma khong ai biet, va doc
ma nguon khong bao gio hieu duoc vi sao co truong do.

Tu 15/08/2026 truong moi khai o day. Ham dung() chay trong after_migrate
nen moi lan deploy la Frappe tu dung lai; khai lai lan hai khong sao vi
create_custom_fields la thao tac lap lai duoc.

KHONG dua cac truong cu vao day. Chung dang chay that, khai lai chi de ra
rui ro ghi de nham. File nay chi giu truong sinh ra tu hom nay tro di.
"""

import frappe


def dung():
	"""Dung moi truong tu them do ma nguon khai. Goi tu after_migrate."""
	# Vai "Quan ly cua hang" dung TRUOC moi thu khac: cac bo QUYEN_* ben
	# duoi tham chieu toi no, ma vai chua ton tai thi phep kiem im lang
	# cho khong ai vao duoc.
	from vagabond import vai_cua_hang

	vai_cua_hang.dung()

	# Hien HO TEN thay cho dia chi thu o moi o Link tro toi User, trong toan
	# bo ERPNext ban may tinh. Anh Viet chot 02/09/2026. Mot dong, va moi o
	# them sau nay cung tu dung, khong phai nho.
	from vagabond import ten_nguoi

	try:
		ten_nguoi.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: hien ten nguoi")

	# Dong bo TEN mon luu san trong cong thuc voi ten trong danh muc, chi cho
	# nhung ma anh Viet chi dich danh. Chay lai nhieu lan khong sao. Doc dau
	# tep vagabond/dong_bo_ten_bom.py de biet vi sao KHONG dong bo tat ca.
	from vagabond import dong_bo_ten_bom

	dong_bo_ten_bom.dung()

	# Ban in Huong dan che bien: tao ban ghi Print Format lan dau neu chua
	# co. Dat sau vai vi ban ghi do co khai quyen theo vai.
	from vagabond import huong_dan_che_bien

	huong_dan_che_bien.dung_mau_in()

	# Danh muc phan he CRM. O Phan loai khach la o BAT BUOC tren phieu tang
	# qua, nen danh muc rong nghia la Sales mo form ra khong luu duoc mot
	# dong nao. Nap CHI THEM, khong bao gio sua va khong bao gio xoa.
	from vagabond import tang_qua

	try:
		tang_qua.nap_danh_muc()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: nap danh muc CRM")

	# Ma phieu ke hoach san xuat va lenh san xuat: KHSX-26-08-0001 va
	# LSX-26-08-0001. Chi doi chuoi dat ten cho phieu SINH RA TU DAY VE
	# SAU; phieu cu giu nguyen ma cu, xem dau tep ma_phieu_sx.py.
	from vagabond import ma_phieu_sx

	try:
		ma_phieu_sx.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: ma phieu san xuat")

	from vagabond import (
		ban_hang, bao_gia, buoc_hoa_don_mua, chung_tu_tien, diem_otp,
		duyet_ycmh, hoan_tien, mua_dich_vu, noi_bo, sepay,
	)

	_dung_nhom(duyet_ycmh.TRUONG_MOI, "duyet_ycmh")
	_dung_nhom(ban_hang.TRUONG_MOI, "ban_hang")
	_dung_nhom(diem_otp.TRUONG_MOI, "diem_otp")
	_dung_nhom(noi_bo.TRUONG_MOI, "noi_bo")
	_dung_nhom(hoan_tien.TRUONG_MOI, "hoan_tien")
	_dung_nhom(chung_tu_tien.TRUONG_MOI, "chung_tu_tien")
	_dung_nhom(bao_gia.TRUONG_MOI, "bao_gia")
	_dung_nhom(bao_gia.TRUONG_CAI_DAT, "bao_gia_cai_dat")
	_dung_nhom(bao_gia.TRUONG_MAU, "bao_gia_mau_in")
	_dung_nhom(mua_dich_vu.TRUONG_MOI, "mua_dich_vu")
	_dung_nhom(buoc_hoa_don_mua.TRUONG_MOI, "buoc_hoa_don_mua")
	_dung_nhom(sepay.TRUONG_MOI, "sepay")
	# O tat chot chan lo qua han (them 03/09/2026). Doc dau tep
	# vagabond/lo_het_han.py de biet ba lop chan da lam bep dung im ra sao.
	from vagabond import lo_het_han

	_dung_nhom(lo_het_han.TRUONG_MOI, "lo_het_han")
	# O nguoi ban tren hoa don (them 02/09/2026). Doc dau tep
	# vagabond/nguoi_ban.py de biet vi sao may CO Y de trong voi don dong bo.
	from vagabond import nguoi_ban

	_dung_nhom(nguoi_ban.TRUONG_MOI, "nguoi_ban")
	# M-Invoice: cau hinh keo PDF ban the hien (them 20/08/2026).
	from vagabond import minvoice_tep

	_dung_nhom(minvoice_tep.TRUONG_MOI, "minvoice_tep")
	# Cong no: o ghi dong sao ke da gach cho phieu, va vet nguoi khop tay
	# (them 24/08/2026, dot 2 cua tang doi soat dung chung).
	from vagabond import cong_no

	_dung_nhom(cong_no.TRUONG_MOI, "cong_no")
	# Tiec va B2B: neo but toan gia von ve hop dong (them 25/08/2026).
	from vagabond import tiec

	_dung_nhom(tiec.TRUONG_MOI, "tiec")
	# Nha cung cap: o "Email phu can CC" (them 21/08/2026).
	from vagabond import nha_cung_cap

	_dung_nhom(nha_cung_cap.TRUONG_MOI, "nha_cung_cap")
	# Danh muc cong thuc: o "Ban truoc" tren BOM (them 21/08/2026).
	from vagabond import cong_thuc

	_dung_nhom(cong_thuc.TRUONG_MOI, "cong_thuc")
	# Cay kho bon chang: nguoi phu trach, chang, kho nguon (them 21/08/2026).
	from vagabond import kho_san_xuat

	_dung_nhom(kho_san_xuat.TRUONG_MOI, "kho_san_xuat")
	# Tuy bien ruot hop qua tren dong bao gia (them 21/08/2026).
	from vagabond import hop_qua

	_dung_nhom(hop_qua.TRUONG_MOI, "hop_qua")
	# Hoa don hang bieu tang khach VIP (them 26/08/2026): o gan phieu qua tren
	# Sales Invoice, o hoa don tren phieu qua, va o tai khoan chi phi bieu
	# tang trong Cai dat.
	from vagabond import qua_tang_hoa_don

	_dung_nhom(qua_tang_hoa_don.TRUONG_MOI, "qua_tang_hoa_don")
	# O dem so lan da thu dung chung tu tu hoa don dien tu (them 26/08/2026).
	# Khong co o nay thi to hong hoac chiem cho mai trong hang doi, hoac bi
	# dong dau "xong roi" nhu ban cu - ca hai deu la mat hoa don.
	from vagabond import minvoice_chung_tu

	_dung_nhom(minvoice_chung_tu.TRUONG_MOI, "minvoice_chung_tu")
	# Cong tac tam ngung ban mot ma tren web dat banh (them 27/08/2026).
	# Luu NGAY tat den het chu khong phai o co / khong - xem ly do trong
	# vagabond/tat_ban_web.py.
	from vagabond import tat_ban_web

	_dung_nhom(tat_ban_web.TRUONG_MOI, "tat_ban_web")
	# Bang Nguyen lieu thay the: cot ten, cot dem cong thuc, chip canh bao
	# (Khai de nghi 28/08/2026). Toan truong may dien, khong ai go tay.
	from vagabond import nvl_thay_the

	_dung_nhom(nvl_thay_the.TRUONG_MOI, "nvl_thay_the")
	# Ke hoach san xuat trong ngay (anh Viet giao 28/08/2026). Ba o them vao
	# Production Plan CO SAN cua ERPNext, khong de them doctype nao.
	from vagabond import ke_hoach_sx

	_dung_nhom(ke_hoach_sx.TRUONG_MOI, "ke_hoach_sx")
	# Hang tang khong thu tien va luong giam doc duyet (anh Viet 31/08/2026).
	from vagabond import hang_tang

	_dung_nhom(hang_tang.TRUONG_MOI, "hang_tang")
	# Bang cac dong thanh toan: mot don tra bang nhieu duong (anh Viet
	# 01/09/2026). O `vgb_pt_thanh_toan` cu VAN GIU va van la o chinh, xem
	# dau tep thanh_toan_nhieu.py.
	from vagabond import thanh_toan_nhieu

	_dung_nhom(thanh_toan_nhieu.TRUONG_MOI, "thanh_toan_nhieu")
	# Nhet phuong thuc thanh toan moi cua ma nguon vao cau hinh DA LUU tren
	# site. Khong co buoc nay thi them mot dong vao MAC_DINH chi co tac dung
	# tren site trong - xem `pt_thanh_toan.bo_sung_mac_dinh`.
	try:
		from vagabond import pt_thanh_toan

		pt_thanh_toan.bo_sung_mac_dinh()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: bo sung phuong thuc")
	try:
		ke_hoach_sx.dung_mau_in()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: mau in ke hoach")
	# Kho Hang Huy: dung lai moi lan Migrate, lap lai duoc.
	try:
		hoan_tien.dung_kho_huy()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: kho hang huy")
	try:
		from vagabond import hop_thu

		hop_thu.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: hop thu")
	# Cot trang thai gui email: CHEN THEM lua chon "Dang cho gui" vao truong
	# cu, khong khai lai ca truong. Xem tai lieu trong trang_thai_thu.dung.
	try:
		from vagabond import trang_thai_thu

		trang_thai_thu.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: trang thai thu")
	try:
		duyet_ycmh._them_trang_thai_tu_choi()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: trang thai tu choi")

	# Phan he Xuat kho day du (anh Viet chot 02/09/2026). Bon man moi, va
	# cay bo phan de biet chi phi thuoc ve ai.
	#
	# CAY BO PHAN DUNG TRUOC: man Xuat dung noi bo bat buoc chon bo phan,
	# ma cay chua co thi o chon rong va khong ai luu duoc mot phieu nao.
	from vagabond import bo_phan

	try:
		bo_phan.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: cay bo phan")
	# O muc dich xuat dung noi bo tren Stock Entry. Chinh o nay phan biet
	# phieu noi bo voi phieu xuat huy - hai thu cung la Material Issue.
	from vagabond import xuat_noi_bo

	_dung_nhom(xuat_noi_bo.TRUONG_MOI, "xuat_noi_bo")
	# O ly do tra va anh hang loi tren phieu nhap mua tra lai.
	from vagabond import tra_ncc

	_dung_nhom(tra_ncc.TRUONG_MOI, "tra_ncc")
	# O nguoi nhan va hop dong tren phieu giao hang ban si.
	from vagabond import xuat_ban

	_dung_nhom(xuat_ban.TRUONG_MOI, "xuat_ban")
	# Cac o ghi vet xac nhan nhan hang dieu chuyen. TOAN o ghi vet, khong o
	# nao dung toi so kho - xem doan dai o dau nhan_dieu_chuyen.py.
	from vagabond import nhan_dieu_chuyen

	_dung_nhom(nhan_dieu_chuyen.TRUONG_MOI, "nhan_dieu_chuyen")
	# O chua cau hinh tai khoan nhan chuyen khoan theo diem ban. Doc dau
	# tai_khoan.TRUONG_MOI de biet vi sao o nay tung mat hai lan.
	from vagabond import tai_khoan

	_dung_nhom(tai_khoan.TRUONG_MOI, "tai_khoan")
	# Bay o Cai dat cu, truoc day bam tay tren Desk. Doc dau o_cai_dat.py.
	from vagabond import o_cai_dat

	_dung_nhom(o_cai_dat.TRUONG_MOI, "o_cai_dat")
	# So ngay han dung toi thieu khi nhan hang, khai theo tung mon.
	from vagabond import kho_cai_dat

	_dung_nhom(kho_cai_dat.TRUONG_MOI, "kho_cai_dat")
	# O chup ton so tren phieu kiem va o ly do chenh lech tren tung dong.
	from vagabond import kiem_ke

	_dung_nhom(kiem_ke.TRUONG_MOI, "kiem_ke")

	# Phieu chi: o ghi vet nguoi xac nhan da chuyen tien va to uy nhiem chi
	# cua rieng phieu. Doc dau tep duyet_chi.py.
	from vagabond import duyet_chi

	_dung_nhom(duyet_chi.TRUONG_MOI, "duyet_chi")
	# Duong duyet phieu chi: tach buoc duyet ra khoi buoc ghi so.
	try:
		duyet_chi.dung_workflow()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: dung duong duyet chi")


def _dung_nhom(khai, ten_nhom):
	"""Dung mot nhom truong. Hong nhom nay khong duoc keo do ca lan deploy."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	try:
		create_custom_fields(khai, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: %s" % ten_nhom)
