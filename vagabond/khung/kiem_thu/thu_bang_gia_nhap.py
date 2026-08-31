# -*- coding: utf-8 -*-
"""Ca kiểm cho bảng giá nhập đuổi theo hoá đơn, và cho phép khai đơn vị.

Anh Việt hỏi 31/08/2026: giá 420.000 trên phiếu nhập PNK-2026-00164 ở đâu
ra, trong khi hoá đơn 6921 của Hộ kinh doanh trái cây nhập khẩu An Phú ghi
480.000. Số liệu trong bộ kiểm này lấy nguyên từ ca đó.

Toàn phép thuần, chạy được trên máy CI tay không.
"""

import io
import os

from vagabond import bang_gia_nhap as B
from vagabond import dvt_mua as D
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Bon lan dirname tu tep nay ra dung GOC REPO, tuc cho dat vagabond/ va
# kiem_truoc_deploy.sh. Ba lan chi ra toi thu muc goi `vagabond/`.
GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(duong):
	with io.open(os.path.join(GOC, duong), encoding="utf-8") as f:
		return f.read()


MA_HOOKS = _doc("vagabond/hooks.py")
MA_PR_JS = _doc("vagabond/public/js/purchase_receipt.js")
MA_DCM = _doc("vagabond/doi_chieu_mua.py")
MA_MC = _doc("vagabond/minvoice_chung_tu.py")
MA_DCM_JS = _doc("vagabond/public/js/bep/18-doi-chieu-may-in.js")


@ca("don vi chua khai: phep xet da ve dvt_mua, minvoice chi con chuyen tiep")
def _phep_ve_mot_cho():
	# Ca that 27/08: nha cung cap ghi "Goi", mon chua khai nen ha ve Gram
	# he so 1. Do la dau van tay phai bat.
	dung("Goi ma dang dung Gram he so 1", D.don_vi_chua_khai("Gói", "Gram", 1))
	dung("Goi da khai that thi thoi", not D.don_vi_chua_khai("Gói", "Gói", 1000))
	dung("tui va Tui la mot", not D.don_vi_chua_khai("tui", "Túi", 1))
	dung("khong ghi don vi thi thoi", not D.don_vi_chua_khai("", "Gram", 1))
	# QT-19: mot cho tinh. minvoice_chung_tu phai goi sang chu khong chep lai.
	dung("minvoice goi sang dvt_mua", "dvt_mua.don_vi_chua_khai" in MA_MC)


@ca("dich don vi nha cung cap truoc khi ha ve don vi kho")
def _dich_truoc():
	# Bang goi y von co tu 26/08 nhung chi dung de HIEN. Nay noi vao duong
	# dung chung tu: "BAG" cua ho la "Tui" cua minh.
	la("BAG", D.goi_y_don_vi("BAG"), "Túi")
	dung("duong dung chung tu co goi bang goi y", "goi_y_don_vi" in MA_MC)
	# Chi dich khi mon DA KHAI don vi tieng Viet do, khong duoc bia he so.
	dung("van tra bang quy doi cua mon", 'UOM Conversion Detail' in MA_MC)


@ca("he so de xuat: chi doan khi hai ben cung so luong")
def _he_so_de_xuat():
	# 4 BAG tren hoa don doi dien 4 Tui tren phieu nhap, 1 Tui la 1.000 Gram.
	# Vay 1 BAG la 1.000 Gram.
	la("cung so luong", D.he_so_de_xuat(4, 4, 1000), 1000.0)
	# Khac so luong thi chiu. Co the mot BAG bang hai tui, cung co the nha
	# cung cap giao thieu. Doan sai o day la hong gia von.
	la("khac so luong thi chiu", D.he_so_de_xuat(4, 2, 1000), 0.0)
	la("khong co phieu nhap", D.he_so_de_xuat(4, 0, 1000), 0.0)
	la("so luong am", D.he_so_de_xuat(-4, -4, 1000), 0.0)
	la("chu", D.he_so_de_xuat("a", "b", 1000), 0.0)


@ca("bang gia: dong nao duoc ghi, dong nao bo qua")
def _duoc_ghi():
	# Ca that: cherry 480.000 mot Kg, don vi sach.
	la("dong sach thi ghi", B.ly_do_bo_qua("NVLT00116", "Kg", 1000, 480000, "Kg"), "")
	la("khong ma hang", B.ly_do_bo_qua("", "Kg", 1000, 480000, "Kg"), B.BO_KHONG_MA)
	la("gia bang 0", B.ly_do_bo_qua("X", "Kg", 1000, 0, "Kg"), B.BO_GIA_KHONG)
	la("gia am", B.ly_do_bo_qua("X", "Kg", 1000, -5, "Kg"), B.BO_GIA_KHONG)
	la("khong don vi", B.ly_do_bo_qua("X", "", 1, 100, ""), B.BO_KHONG_DON_VI)
	# Day la dong nguy hiem nhat: 4 BAG bi doc thanh 4 Gram. Ghi vao bang gia
	# la bang gia sai gap mot nghin lan.
	la("don vi chua khai thi KHONG ghi",
		B.ly_do_bo_qua("X", "Gram", 1, 280000, "BAG"), B.BO_DON_VI_CHUA_KHAI)


@ca("bang gia: khong ghi chu lai khi gia khong doi")
def _dang_ke():
	dung("420.000 sang 480.000 la co doi", B.dang_ke(420000, 480000))
	dung("y het thi thoi", not B.dang_ke(480000, 480000))
	dung("lech nua xu la lam tron", not B.dang_ke(480000, 480000.001))
	dung("chu thi coi nhu khong doi", not B.dang_ke("a", "b"))


@ca("bang gia: chi nghe hoa don luc ghi so, khong nghe don mua hay phieu nhap")
def _chi_nghe_hoa_don():
	dung("moc on_submit cua Hoa don mua",
		'"on_submit": "vagabond.bang_gia_nhap.cap_nhat_tu_hoa_don"' in MA_HOOKS)
	# Don mua va phieu nhap lay gia TU bang gia, nghe chung la vong tron.
	dung("khong moc vao Purchase Order",
		"bang_gia_nhap" not in MA_HOOKS.split('"Purchase Order"')[-1].split("},")[0]
		if '"Purchase Order"' in MA_HOOKS else True)
	dung("hong khong duoc chan ke toan ghi so", "def cap_nhat_tu_hoa_don" in _doc(
		"vagabond/bang_gia_nhap.py") and "except Exception" in _doc("vagabond/bang_gia_nhap.py"))


@ca("phieu nhap kho: an o gia voi nguoi thuan lam kho, ke toan van thay")
def _man_phieu_nhap():
	dung("co khai hook", '"Purchase Receipt": "public/js/purchase_receipt.js"' in MA_HOOKS)
	dung("giu nguyen hook Hoa don mua cua v360",
		'"Purchase Invoice": "public/js/purchase_invoice.js"' in MA_HOOKS)
	for vai in ["Accounts Manager", "Accounts User", "Purchase Manager", "System Manager"]:
		dung("%s van thay gia" % vai, vai in MA_PR_JS)
	for o in ["rate", "amount", "price_list_rate"]:
		dung("an cot %s" % o, "'%s'" % o in MA_PR_JS)
	# Bai hoc v361: goi mot lan trong refresh la go truot.
	dung("goi nhieu nhip", MA_PR_JS.count("vgbAnCotGia(frm)") >= 3)
	dung("co nhip cham", "}, 400)" in MA_PR_JS)
	# Dong chu giai thich hien cho MOI NGUOI, ke ca ke toan.
	dung("noi ro gia von cuoi cung theo hoa don", "hoá đơn" in MA_PR_JS)
	dung("noi ro thu kho khong phai go gia", "thủ kho gõ" in MA_PR_JS)


@ca("nut khai don vi: co cua, co nut, va khong tu dat he so")
def _khai_don_vi():
	dung("co cua khai_don_vi", "def khai_don_vi(" in MA_DCM)
	dung("cua co whitelist", "@frappe.whitelist()\ndef khai_don_vi(" in MA_DCM)
	# He so la con so cua nguoi. May khong duoc bia.
	dung("tu choi he so khong duong", "Hệ số quy đổi phải là số lớn hơn 0" in MA_DCM)
	# Ghi de he so da co la doi so luong quy ve kho cua MOI chung tu cu.
	dung("khong ghi de he so da khai", '"da_co": 1' in MA_DCM)
	dung("man hinh co nut", "data-dcmkhai" in MA_DCM_JS)
	dung("man hinh co ham", "async function dcmKhaiDonVi(" in MA_DCM_JS)
	dung("man hinh de xuat he so tu phieu nhap", "hs_pnk" in MA_DCM and "data-hspnk" in MA_DCM_JS)


@ca("dong chua gan ma hang: bao dung benh chu khong bao nham la chua nhap kho")
def _chua_gan_ma():
	# Ca that HDM-26-08-00042 hoa don 6921 cua An Phu: ca ba dong co
	# item_code RONG. Ban cu bao "hang chua duoc nhap kho tren he thong",
	# trong khi PNK-2026-00171 nam ngay do, da xac nhan, co 2 Kg cherry.
	dung("co nhanh rieng cho dong chua gan ma",
		'if not (d.get("item_code") or "").strip():' in MA_DCM)
	dung("cau bao noi dung benh", "chưa gắn mã hàng" in MA_DCM)
	# Cau cu chi con dung cho dong DA co ma hang.
	dung("cau cu da them ve dieu kien", "có mã hàng rồi nhưng không nằm trong" in MA_DCM)
	dung("khong con cau chan doan sai",
		"tức là hàng chưa được nhập kho trên hệ" not in MA_DCM)
	# Chan TRUOC moi phep so sanh: tra bang item_code rong thi khong bao gio
	# ra gi, moi ket luan phia sau deu vo nghia.
	i_chan = MA_DCM.find('if not (d.get("item_code") or "").strip():')
	i_tra = MA_DCM.find('ds = kho.get(d.item_code) or []', i_chan)
	dung("chan truoc khi tra phieu", 0 < i_chan < i_tra)


@ca("gan ma hang: gan mot lan, nho mai, va nan lai don vi")
def _gan_ma_hang():
	dung("co cua goi y", "@frappe.whitelist()\ndef goi_y_mon(" in MA_DCM)
	dung("co cua gan", "@frappe.whitelist()\ndef gan_ma_hang(" in MA_DCM)
	# Xep theo phieu nhap chua thanh toan cua chinh NCC do: hang da ve kho
	# roi thi gan nhu chac chan la lo hang cua to hoa don nay.
	dung("goi y tu phieu nhap cua chinh NCC", "_phieu_ung_vien" in MA_DCM)
	dung("con duong cho hang khong qua kho", '"MInvoice NCC Map"' in MA_DCM)
	# Phan chua goc: ghi nho de lan sau may tu nhan.
	dung("co ghi nho", '"doctype": "MInvoice NCC Map"' in MA_DCM)
	dung("khong ghi de anh xa da co", "elif not (frappe.db.get_value" in MA_DCM)
	# Nan lai don vi, dung chung phep dich voi duong dung chung tu (QT-19).
	dung("nan lai don vi khi gan", "goi_y_don_vi(dvt_ncc)" in MA_DCM)
	dung("bao lai khi don vi chua khai", "chua_khai_don_vi" in MA_DCM)
	# KHONG dong toi tien: do la so cua ban goc da gui co quan thue.
	dung("khong sua so luong", "d.qty =" not in MA_DCM)
	dung("khong sua don gia", "d.rate =" not in MA_DCM)
	# To da ghi so thi khong duoc dong vao.
	dung("chan to da ghi so", "đã ghi sổ rồi, không gắn mã hàng được" in MA_DCM)
	dung("man hinh co nut", "data-dcmgan" in MA_DCM_JS)
	dung("man hinh co ham", "async function dcmGanMaHang(" in MA_DCM_JS)


@ca("mot dong phi ship khong duoc chan ca to hoa don")
def _phi_ship_khong_chan():
	# Anh Viet 31/08/2026: *"Chi can co dong phi dich vu van chuyen la da bi
	# lech ngay roi va he thong khong cho phep noi hoa don voi PNK do vi ben
	# PNK khong co dong phi dich vu van chuyen?"* Dung y nguyen.
	#
	# Hoa don 7100 cua An Phu dung hai dong: mot dong cherry, mot dong phi
	# ship 40.000. Phieu nhap kho khong bao gio chua phi ship. Ban cu nem loi
	# cho ca to nen to do vinh vien khong noi duoc.
	dung("co phep xet dong khong qua kho", "def _khong_qua_kho(" in MA_DCM)
	# Buoc NOI khong duoc chan nua.
	dung("bo cau chan cu", 'Chưa nối được, mấy dòng này chưa khớp' not in MA_DCM)
	# Hang rao chi con o buoc GHI SO, va chi cho dong hang that.
	dung("van chan ghi so khi thieu phieu", "chưa có \n\t\t\t\"" not in MA_DCM
		and "ghi sổ luôn thì giá vốn sai" in MA_DCM)
	dung("chan ghi so chi tinh dong qua kho",
		'[x for x in xep if x["qua_kho"]]' in MA_DCM)
	dung("dong khong qua kho de rieng, khong chan",
		'[x for x in xep if not x["qua_kho"]]' in MA_DCM)
	# Duong cu cua dung_lai_hddt van doc duoc danh sach cau chu.
	dung("giu duoc duong goi cu", "if not chi_tiet:" in MA_DCM)
	dung("mac dinh van tra danh sach", "def _noi(doc, phieu, chi_tiet=False):" in MA_DCM)


@ca("dong khong qua kho: phi va dich vu khong doi phieu nhap")
def _xet_khong_qua_kho():
	i = MA_DCM.find("def _khong_qua_kho(")
	than = MA_DCM[i:MA_DCM.find("\ndef _noi(", i)]
	# Chua gan ma hang thi chua biet la gi, khong doan la hang.
	dung("chua co ma thi cho di tiep", "if not ma:" in than and "return True" in than)
	# Co ma thi hoi danh muc Mon xem co quan kho khong.
	dung("hoi is_stock_item", "is_stock_item" in than)
	# Hoi khong duoc thi nghieng ve phia COI LA HANG, tuc van chan ghi so.
	# An toan hon: tha chan nham con hon de gia von sai am tham.
	dung("hong thi nghieng ve phia an toan", "except Exception:" in than
		and than.rstrip().endswith("return False"))
