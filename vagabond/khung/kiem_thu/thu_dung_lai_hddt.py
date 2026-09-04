# -*- coding: utf-8 -*-
"""Ca kiểm cho phép dựng lại hoá đơn mua theo hoá đơn điện tử gốc, và cho
phép sửa giá lúc nhận hàng.

Toàn phép thuần. Số liệu lấy nguyên từ hai ca thật ngày 26/08/2026:

  * HDM-26-08-00012, Thanh An Eggpack, hoá đơn giấy số 86: trứng gà 1.500
    quả đơn giá 2.190,48, tổng 3.450.000. Sau khi có người bấm nút "Nối
    phiếu nhập kho" bên Desk thì tụt còn 3.314.280.
  * Mua thịt heo 3 kg, nhà cung cấp giao 3,02 kg.
"""

from vagabond import dung_lai_hddt as D
from vagabond import gia_khi_nhan as G
from vagabond.khung.kiem_thu.nen import ca, dung, la


# ------------------------------------------- lech so voi hoa don dien tu

@ca("lech hoa don dien tu: bat dung huong va dung so")
def _huong_lech():
	# Ca that: phieu 3.314.280, hoa don dien tu 3.450.000.
	viec, so = D.huong_lech(3314280, 3450000)
	la("dang thieu", viec, "thieu")
	la("thieu 135.720", round(so), 135720)
	viec2, so2 = D.huong_lech(3450000, 3314280)
	la("nguoc lai la thua", viec2, "thua")
	la("thua 135.720", round(so2), 135720)


@ca("lech hoa don dien tu: bang nhau thi khong bao gi")
def _khop_thi_im():
	la("bang het", D.huong_lech(3450000, 3450000), ("khop", 0.0))
	# Duoi mot dong la lam tron, khong dang keu nguoi ta lai.
	la("lech nua dong", D.huong_lech(3450000.4, 3450000), ("khop", 0.0))


@ca("lech hoa don dien tu: cau canh bao noi du viec va du so")
def _cau_canh_bao():
	c = D.cau_canh_bao("HDM-26-08-00012", 3314280, 3450000)
	dung("co ten phieu", "HDM-26-08-00012" in c)
	dung("noi la thieu", "thiếu" in c)
	dung("co so lech", "135.720" in c)
	dung("co so cua phieu", "3.314.280" in c)
	dung("co so goc", "3.450.000" in c)
	dung("chi ra viec can lam", "Dựng lại theo hoá đơn điện tử" in c)
	# Cau nay phai chi dung thu pham, khong thi thang sau lai dinh y het.
	dung("chi ra nguyen nhan hay gap", "Nối phiếu nhập kho" in c)
	la("khop thi khong noi gi", D.cau_canh_bao("X", 100, 100), "")


@ca("quy uoc trinh bay: khong dau gach dai trong cau nguoi dung doc")
def _khong_gach_dai():
	c = D.cau_canh_bao("HDM-26-08-00012", 3314280, 3450000)
	dung("khong em dash", "—" not in c)
	dung("khong en dash", "–" not in c)


@ca("doc chi tiet hoa don dien tu: chuoi hong khong duoc lam chet ca nhip")
def _doc_chi_tiet():
	la("chuoi rong", D.doc_chi_tiet(""), [])
	la("None", D.doc_chi_tiet(None), [])
	la("chuoi hong", D.doc_chi_tiet("{khong phai json"), [])
	la("khong phai danh sach", D.doc_chi_tiet('{"a":1}'), [])
	ds = D.doc_chi_tiet('[{"dgia": 2190.48, "sluong": 1500}]')
	la("doc duoc mot dong", len(ds), 1)
	la("giu nguyen don gia", ds[0]["dgia"], 2190.48)
	la("nhan thang danh sach", D.doc_chi_tiet([{"a": 1}]), [{"a": 1}])


@ca("dinh dang so tien: cham ngan nghin, khong phan thap phan")
def _dinh_dang_so():
	la("trieu", D._so(3450000), "3.450.000")
	la("tram nghin", D._so(135720), "135.720")
	la("nho", D._so(720), "720")
	la("lam tron", D._so(2190.48), "2.190")
	la("rong", D._so(None), "0")
	la("am", D._so(-135720), "-135.720")


# ------------------------------------------------ sua gia luc nhan hang

@ca("gia luc nhan: lech qua nua dong moi tinh la doi")
def _gia_doi():
	dung("2.100 sang 2.190 la doi", G.gia_da_doi(2190.48, 2100))
	dung("bang nhau thi khong", not G.gia_da_doi(2100, 2100))
	dung("lech mot phan muoi thi khong", not G.gia_da_doi(2100.1, 2100))
	dung("thieu so dat thi khong ket luan", not G.gia_da_doi(2100, None))


@ca("nhan du: 3 kg dat ma giao 3,02 kg la du 0,67 phan tram")
def _nhan_du():
	la("3,02 tren 3", round(G.phan_tram_du(3.02, 3), 2), 0.67)
	la("dung bang", G.phan_tram_du(3, 3), 0.0)
	la("nhan thieu ra so am", round(G.phan_tram_du(2.9, 3), 2), -3.33)
	la("dat bang khong thi thoi", G.phan_tram_du(5, 0), 0.0)
	# Nguong 10 phan tram phai du cho ca can dong lan mua muoi tang mot.
	dung("can dong lot nguong", G.phan_tram_du(3.02, 3) < G.NGUONG_NHAN_DU)
	dung("mua muoi tang mot lot nguong", G.phan_tram_du(11, 10) <= G.NGUONG_NHAN_DU)
	dung("go nham gap doi thi khong lot", G.phan_tram_du(6, 3) > G.NGUONG_NHAN_DU)


@ca("ghi vet: noi ro doi gi, khong doi gi thi im")
def _ghi_vet():
	c = G.cau_ghi_vet(1, "Thịt heo", 100000, 100000, 3, 3.02)
	dung("co so dong", "Dòng 1" in c)
	dung("co ten mon", "Thịt heo" in c)
	dung("noi la nhan du", "dư" in c)
	dung("khong bia chuyen doi gia", "đơn giá" not in c)
	c2 = G.cau_ghi_vet(2, "Trứng gà", 2100, 1900, 100, 100)
	dung("noi gia giam", "giảm" in c2)
	dung("co ca hai gia", "2.100" in c2 and "1.900" in c2)
	dung("khong bia chuyen so luong", "so với đặt" not in c2)
	la("khong doi gi thi im", G.cau_ghi_vet(3, "Bơ", 5000, 5000, 2, 2), "")


@ca("ghi vet: doi ca gia lan so luong thi noi ca hai")
def _ghi_vet_ca_hai():
	c = G.cau_ghi_vet(1, "Sữa", 30000, 27000, 10, 11)
	dung("noi gia", "đơn giá" in c)
	dung("noi so luong", "dư" in c)
	dung("khong em dash", "—" not in c and "–" not in c)


# ------------------- chot cach dung chung voi mo dun dung chung tu hoa don

@ca("dung chung: ba ham cua minvoice_chung_tu phai giu nguyen chu ky")
def _chu_ky_ham():
	# `dung_lai` goi thang ba ham nay de hai duong dung chung tu khong bao
	# gio ra hai ket qua khac nhau. Doi chu ky ma khong sua `dung_lai` thi
	# nut Dung lai hong lang le, chi lo khi co nguoi bam.
	import inspect

	from vagabond import minvoice_chung_tu as mc

	# `dau_to` them 29/08/2026 cho to hoa don am. Tham so DAU van phai la
	# `it` va `dau_to` phai co mac dinh, vi `dung_lai` goi bang mot doi so.
	tham = inspect.signature(mc.dong_tu_hoa_don).parameters
	la("dong_tu_hoa_don(it, dau_to=1)", list(tham), ["it", "dau_to"])
	la("dau_to co mac dinh 1", tham["dau_to"].default, 1)
	la("_tra_ma_hang(x, goc_mst, ncc)",
		list(inspect.signature(mc._tra_ma_hang).parameters), ["x", "goc_mst", "ncc"])
	la("_dong_pi(x, tk_chi_phi, mapped, uom, he_so)",
		list(inspect.signature(mc._dong_pi).parameters),
		["x", "tk_chi_phi", "mapped", "uom", "he_so"])
	la("can_theo_truoc_thue(tong_dong, truoc_thue)",
		list(inspect.signature(mc.can_theo_truoc_thue).parameters),
		["tong_dong", "truoc_thue"])


@ca("dung chung: dong hoa don dien tu that cua Thanh An ra dung so")
def _dong_that():
	from vagabond import minvoice_chung_tu as mc

	# Nguyen van mot dong cua hoa don so 86 ngay 15/08/2026.
	x = mc.dong_tu_hoa_don({
		"dgia": 2190.48, "dvtinh": "Quả", "ltsuat": "5%", "sluong": 1500,
		"ten": "Trứng gà", "thtien": 3285720, "tsuat": 0.05,
	})
	la("so luong", x["sl"], 1500)
	la("don gia giu nguyen phan thap phan", x["gia"], 2190.48)
	la("thanh tien", round(x["tien"]), 3285720)
	# Va tong dong phai khop dung tien truoc thue cua to hoa don.
	la("khop tien truoc thue", mc.can_theo_truoc_thue(x["tien"], 3285720), ("khop", 0))


# ------------------------- v319: hai man phai chung mot ban chat o tang luu

@ca("dong bo hai man: hook dung lai phai nam tren duong luu cua hoa don mua")
def _hook_dong_bo():
	# Anh Viet 26/08/2026: "phai dong bo giua ca app va ca desktop ve tat ca
	# cac nut tinh nang". Ban v318 chi canh bao roi dan mieng, anh bac. Ca
	# nay chot bang van ban: hook dung lai phai duoc dang ky that trong
	# hooks.py, va ban canh-bao-suong cu phai bien mat han - con no la con
	# duong luu KHONG dung lai, tuc lai hai ban chat.
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	hooks = io.open(os.path.join(goc, "hooks.py"), encoding="utf-8").read()
	dung("hook dung lai co that", "vagabond.dung_lai_hddt.dong_bo_luc_luu" in hooks)
	dung("hook tai khoan theo mon co that", "vagabond.dung_lai_hddt.tk_theo_mon" in hooks)
	dung("ban canh bao suong cu phai bien mat", "canh_bao_lech" not in hooks)
	# Phai nam o before_validate: ERPNext tinh lai tong tien SAU buoc nay,
	# dat o validate la doi dong xong tong khong duoc tinh lai.
	truoc, sau = hooks.split("vagabond.dung_lai_hddt.dong_bo_luc_luu", 1)
	dung("nam trong khoi before_validate",
		truoc.rfind("before_validate") > truoc.rfind('"validate"'))


# --------- v321: neo vao tong tien, va khong ghi de khi chua chac dung

@ca("neo so: lay tong tien tru thue, KHONG lay thang o tien truoc thue")
def _neo_so():
	from vagabond import dung_lai_hddt as D

	# Ca that HDM-26-08-00096 Nha Sen: ban goc ghi tong 3.650.000 nhung o
	# tien_truoc_thue de 0. Ban v319 neo vao o do nen hieu la dong hang thua
	# ca to, dat giam gia bang ca to, tong ve 0 dong. Bon to bi ve 0 deu the.
	la("khong khai truoc thue thi lay tong tru thue",
		D.muc_tieu_truoc_thue({"tong_tien": 3650000, "tien_thue": 0, "tien_truoc_thue": 0}),
		3650000.0)
	# Ca that HDM-26-08-00124 Avanti.
	la("co thue thi tru thue ra",
		D.muc_tieu_truoc_thue({"tong_tien": 29369580, "tien_thue": 2416080,
			"tien_truoc_thue": 26953500}),
		26953500.0)
	# Ban goc khong ghi tong thi moi danh quay ve o cu.
	la("khong co tong thi dung o cu",
		D.muc_tieu_truoc_thue({"tong_tien": 0, "tien_thue": 0, "tien_truoc_thue": 111000}),
		111000.0)


@ca("ca that: bon to bi ve 0 dong phai duoc neo lai dung")
def _khong_con_ve_0():
	from vagabond import minvoice_chung_tu as mc
	from vagabond import dung_lai_hddt as D

	g = {"tong_tien": 3650000, "tien_thue": 0, "tien_truoc_thue": 0}
	muc_tieu = D.muc_tieu_truoc_thue(g)
	# Dong hang dung ra dung 3.650.000 (500 tui x 7.300).
	viec, so_tien = mc.can_theo_truoc_thue(3650000, muc_tieu)
	la("khong con coi la thua", viec, "khop")
	la("khong dat giam gia nao", so_tien, 0)
	# Con neu neo kieu cu thi no ra "giam" dung bang ca to - chinh la loi.
	viec_cu, so_cu = mc.can_theo_truoc_thue(3650000, g["tien_truoc_thue"])
	la("neo kieu cu ra giam", viec_cu, "giam")
	la("giam dung bang ca to", so_cu, 3650000)


# --------- v322: dung lai ca bang thue, va khong de don gia 0 bi dien lai

@ca("dung lai: co dung lai CA BANG THUE theo ban goc")
def _dung_ca_thue():
	import inspect

	from vagabond import dung_lai_hddt as D

	# Ca that 27/08/2026, nhom hoa don LARAFARM lech dung 51.200 dong: ban
	# goc ghi thue 0, dong hang dung ra dung 790.000, nhung tren chung tu
	# con sot hai dong thue "On Net Total" 1331 va 33311 moi dong 25.600 do
	# mau thue cua danh muc Mon ap vao luc to duoc sinh ra. Dung lai moi
	# dong hang thi tong van lech, vi phan lech nam o bang thue.
	dung("co ham dung lai bang thue", hasattr(D, "_dung_thue_tai_cho"))
	ma = inspect.getsource(D._dung_thue_tai_cho)
	dung("co xoa sach bang thue cu", 'doc.set("taxes", [])' in ma)
	dung("chi dung lai theo tien_thue cua ban goc", 'g.get("tien_thue")' in ma)
	dung("dat dong Actual chu khong phai On Net Total", '"Actual"' in ma)
	dung("co bo mau thue cua chung tu", "taxes_and_charges" in ma)

	goi = inspect.getsource(D._dung_dong_tai_cho)
	dung("duong dung duy nhat co goi no", "_dung_thue_tai_cho(doc, g)" in goi)


@ca("dung thu: uoc tong lay thue theo BAN GOC, khong lay thue dang co")
def _uoc_tong_lay_thue_goc():
	import inspect

	from vagabond import dung_lai_hddt as D

	ma = inspect.getsource(D.du_kien_tong)
	dung("lay thue tu ban goc", 'flt(g.get("tien_thue"))' in ma)
	dung("khong con lay thue dang co tren phieu",
		"_tong_thue_tren_phieu(doc)" not in ma)


@ca("dong hoa don: don gia 0 ma co thanh tien thi lay thanh tien")
def _don_gia_khong():
	import inspect

	from vagabond import minvoice_chung_tu as mc

	# Ca that 27/08/2026, hoa don tiep khach Avanti C26TAV/5019: dong "Phi
	# phuc vu" ghi sluong 0, dgia 0, thtien 1.283.500. De don gia 0 di vao
	# chung tu thi ERPNext dien lai theo Bang gia nhap cua mat hang
	# (4.500.000) va to hoa don phinh them dung 4,5 trieu.
	x = mc.dong_tu_hoa_don({"ten": "Phí phục vụ", "sluong": 0, "dgia": 0,
		"thtien": 1283500})
	la("so luong ve 1", x["sl"], 1)
	la("don gia la thanh tien", x["gia"], 1283500)

	ma = inspect.getsource(mc._dong_pi)
	dung("co ghim price_list_rate theo don gia hoa don",
		'"price_list_rate": x["gia"]' in ma)


# --------- v323: can theo con so may SE ghi, khong theo con so hoa don doc len

@ca("lam tron: tinh tien dong theo do chinh xac cua may")
def _tien_dong_may_ghi():
	from vagabond import dung_lai_hddt as D

	# Ca that ACC-PINV-2026-01427: hoa don ghi 420 don vi, don gia 5.136,683,
	# thanh tien 2.157.407. ERPNext chi giu don gia toi hai so le nen ghi
	# 5.136,68 va nhan ra 2.157.405,6, hut 1,4 dong. To do nam lai mai vi
	# cua chan ghi so lay nguong mot dong.
	la("theo con so may ghi",
		D.tien_dong_may_ghi(420, 5136.683, 2, 2), 2157405.6)
	la("con theo con so hoa don thi ra khac",
		round(420 * 5136.683, 2), 2157406.86)
	la("khong co so le thi khong doi",
		D.tien_dong_may_ghi(3, 25000, 2, 2), 75000.0)

	# Ca that HDM-2026-00398: hoa don ghi 2,762431 don vi, may chi giu ba so
	# le nen ghi 2,762, hut 9,36 dong. O SO LUONG cung bi cat y nhu o don gia.
	la("so luong cung bi cat theo do chinh xac cua may",
		D.tien_dong_may_ghi(2.762431, 21720, 2, 2, 3), 59990.64)
	la("khong cat so luong thi ra khac",
		round(2.762431 * 21720, 2), 60000.0)


@ca("lam tron: phan chenh vai dong duoc goi dung ten")
def _ten_dong_bu():
	from vagabond import dung_lai_hddt as D

	la("chenh nho la lam tron", D.ten_dong_bu(1.4),
		"Chênh lệch làm tròn theo hoá đơn điện tử")
	la("chenh lon van la phi", D.ten_dong_bu(1283500),
		"Phí khác theo hoá đơn")


@ca("lam tron: ca hai duong dung deu can theo con so may ghi")
def _hai_duong_cung_can():
	import inspect

	from vagabond import dung_lai_hddt as D

	for ham in (D._dung_dong_tai_cho, D.du_kien_tong):
		ma = inspect.getsource(ham)
		dung("%s can theo con so may ghi" % ham.__name__,
			"tien_dong_may_ghi(" in ma)
		dung("%s co hoi do chinh xac cua may" % ham.__name__,
			"_do_chinh_xac()" in ma)


# --------- v327: don vi cua nha cung cap chua khai thi khong duoc im lang

@ca("don vi chua khai: bat dung dau van tay cua duong ha ngam")
def _don_vi_chua_khai():
	from vagabond import minvoice_chung_tu as mc

	# Ca that HDM-26-08-00115: nha cung cap ghi "Gói", may ha ve "Gram" he
	# so 1. Tien van dung nhung so luong lech mot nghin lan.
	dung("Goi ma dang dung Gram he so 1",
		mc.don_vi_chua_khai("Gói", "Gram", 1))
	# Tra ra bang quy doi that thi he so khac 1, khong tinh la bia.
	dung("Goi va dang dung Goi he so 1000",
		not mc.don_vi_chua_khai("Gói", "Gói", 1000))
	dung("Kg ma dang dung Kg", not mc.don_vi_chua_khai("Kg", "Kg", 1000))
	# Cung mot don vi viet khac kieu thi khong phai loi.
	dung("tui va Tui la mot", not mc.don_vi_chua_khai("tui", "Túi", 1))
	# Nha cung cap khong ghi gi thi khong doan gia.
	dung("khong ghi don vi thi thoi", not mc.don_vi_chua_khai("", "Gram", 1))


@ca("nhip ra: soi ca DON VI chu khong chi soi tien")
def _nhip_ra_soi_don_vi():
	import inspect

	from vagabond import dung_lai_hddt as D

	dung("co cua soat don vi", hasattr(D, "soat_don_vi"))
	ma = inspect.getsource(D.soat_don_vi)
	dung("doc dau vet tu phan mo ta dong", "dvt_tren_hoa_don" in ma)
	dung("dung chung phep xet voi luc kéo hoá đơn", "don_vi_chua_khai" in ma)
	dung("tach rieng to da ghi so", "da_ghi_so" in ma)

	ra = inspect.getsource(D.soat)
	dung("nhip ra tra ve luon so to sai don vi", "so_lech_don_vi" in ra)


@ca("cua ngo: soat_don_vi da khai trong danh sach mo ra ngoai")
def _cua_ngo_soat_don_vi():
	import os

	goc = os.path.dirname(os.path.abspath(__file__))
	ma = open(os.path.join(goc, "thu_cua_ngo.py"), encoding="utf-8").read()
	# Cat den dau ngoac vuong DONG chu khong cat theo so ky tu. Ban cu cat
	# 200 ky tu, den 27/08/2026 them mot dong ghi chu vao danh sach la ca
	# kiem do ngay trong khi ma nguon hoan toan dung. Ca kiem noi doi thi
	# con te hon khong co ca kiem.
	doan = ma.split('"dung_lai_hddt.py"', 1)[1]
	doan = doan[: doan.index("]") + 1]
	for ten in ("soat_don_vi", "dung_lai_lech_don_vi", "soat_do_tam"):
		dung("co ten %s" % ten, ('"%s"' % ten) in doan)


# --------- v329: doc bang con thi dung frappe.db.get_all

@ca("soat don vi: doc bang con khong duoc dung tham so parent")
def _doc_bang_con():
	import inspect

	from vagabond import dung_lai_hddt as D

	ma = inspect.getsource(D.soat_don_vi)
	# v328 viet `parent=PI` nen nem TypeError ngay lan goi dau tren site that:
	# tham so do chi co o tang API, khong co trong DatabaseQuery.
	dung("khong con tham so parent", "parent=PI" not in ma)
	dung("doc bang frappe.db.get_all", "frappe.db.get_all(" in ma)


# =====================================================================
# GO NUT "LAY MAT HANG TU" - anh Viet hoi 31/08/2026
# =====================================================================
#
# *"Day la hoa don day ve sao lai phai lay mat hang tu? No noi phieu vao
# thoi roi anh xa chu nhi?"* Cau hoi dung, va la ly do co ban vá này.
#
# Ca that Kamereo 271846 ngay 27/08: hoa don dien tu 6 dong, 417.400 d.
# Co nguoi bam "Lay mat hang tu" chon bon phieu nhap kho cua ngay do, man
# hinh thanh: ca chua tach hai dong (hai phieu nhap rieng), mat han dong
# Phi dich vu 30.000 (phi khong di qua kho nen khong co phieu nhap), tong
# tut xuong 385.000.
#
# So sach KHONG sai vi ho chua bam Luu, va neu bam Luu thi hook
# `dong_bo_luc_luu` da dung lai. Nhung luoi do cuu duoc so sach chu khong
# cuu duoc nguoi: Uyen van thay man hinh sai va van bao len. Ba lan trong
# hai tuan. Nen ban nay bo han cai nut.

import io as _io
import os as _os

_GOI = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


def _doc_tep(*duong):
    p = _os.path.join(_GOI, *duong)
    return _io.open(p, encoding="utf-8").read() if _os.path.exists(p) else ""


MA_PI_JS = _doc_tep("public", "js", "purchase_invoice.js")
MA_HOOKS_PI = _doc_tep("hooks.py")


@ca("go nut Lay mat hang tu tren to sinh tu hoa don dien tu")
def _():
    dung("tep co that", bool(MA_PI_JS))
    # KHONG ghim nguyen van dong doctype_js nua. Ban v356 da vap dung cai
    # bay nay o doctype_list_js: them mot man moi la ca kiem do, trong khi
    # dieu can chot chi la "Hoa don mua co tep rieng, va khong ai dat tren
    # sao". v362 them Purchase Receipt vao cung o do.
    dung("Hoa don mua co tep JS rieng",
         '"Purchase Invoice": "public/js/purchase_invoice.js"' in MA_HOOKS_PI)
    dung("doctype_js khong dat tren sao",
         '"*"' not in MA_HOOKS_PI.split("doctype_js", 1)[1].split("}", 1)[0])
    # Quy tac 6: hook rong tren "*" ap len moi doctype ke ca ha tang Frappe.
    dung("khong bat tat bang sao", 'doctype_js = {"*"' not in MA_HOOKS_PI)
    # CHI go tren to sinh tu hoa don dien tu. To go tay khong co ban goc
    # nao de pha, go nut cua ho la lam ho mat mot duong lam viec that.
    dung("chi cham to co ma hoa don dien tu", "custom_minvoice_id" in MA_PI_JS)
    dung("to da ghi so thi khong dung toi", "docstatus !== 0" in MA_PI_JS)


@ca("go nut: go bang ca ten tieng Anh lan tieng Viet")
def _():
    # ERPNext them nhom bang add_custom_button(label, fn, __("Get Items
    # From")), tuc TEN NHOM DA DICH khi site chay tieng Viet. Go bang mot
    # ten la truot mot nua so truong hop.
    for ten in ("Get Items From", "Lấy mặt hàng từ"):
        dung("go theo ten nhom %r" % ten, ten in MA_PI_JS)
    for ten in ("Purchase Receipt", "Phiếu nhập kho"):
        dung("go theo ten nut %r" % ten, ten in MA_PI_JS)
    dung("co luoi do bang CSS phong khi ERPNext doi ten",
         ".inner-group-button" in MA_PI_JS)
    # BAN DAU GO NGAY TRONG refresh VA NUT VAN CON. `refresh` cua tep nay
    # chay TRUOC luc bo dieu khien ERPNext gan nut, nen go xong ho gan lai.
    # Do bang tay tren Desk: goi luc trang dung han thi so cum nut tut tu
    # 2 xuong 1, tuc phep go dung, chi sai thoi diem.
    dung("go lam nhieu nhip chu khong mot lan",
         MA_PI_JS.count("vgbGoNutLayMatHang(frm)") >= 3)
    dung("co nhip cham de bat luc ERPNext gan sau", "}, 400)" in MA_PI_JS)
    # AN chu khong XOA phan tu: xoa nham mot cum khac la hong nut cua nguoi
    # khac, con an nham thi chi mat mot nut.
    dung("chi an chu khong xoa phan tu", ".hide()" in MA_PI_JS)
    dung("khong goi remove tren DOM", ".remove()" not in MA_PI_JS)


@ca("go nut: phai noi ro bam nut nao thay the")
def _():
    # Khong noi thi ho di tim, va di tim thi lai mo Desk goc ra bam.
    dung("co cau chi duong", "Nối phiếu nhập kho" in MA_PI_JS)
    dung("noi ro nut kia chep de", "chép đè" in MA_PI_JS)
    dung("ke ra dong bi mat", "phí dịch vụ" in MA_PI_JS)
    dung("moi loi keo do man hinh deu duoc bat", MA_PI_JS.count("catch (e)") >= 2)


# ===================================================================
# GIU MA HANG NGUOI GAN TAY QUA LUOT DUNG LAI (04/09/2026)
#
# Ca that HDM-26-08-00149, CONG TY TNHH GREEN BALL, hoa don dien tu
# C26MGB/1661. Hai dong: "Tran chau khoai (o long)" 5 x 69.000 va
# "Phi van chuyen" 1 x 27.778, tien hang 372.778, thue 29.822, tong
# 402.600.
#
# Uyen gan ma hang cho hai dong do. Gan xong ERPNext lay lai don gia
# theo Bang gia nhap (69.000 thanh 74.556), tong to lech khoi hoa don
# dien tu, nhip luu thay lech nen dung lai ca bang dong hang - ma
# duong dung chi lay ma hang tu BANG ANH XA, khong nhin cai vua go.
# Ma bay mat, dong khong co ma thi khong noi duoc phieu nhap, khong
# noi duoc thi khong ghi so, khong ghi so thi khong sang buoc ke toan
# duyet. Mot loi, ba trieu chung.
# ===================================================================

MA_DUNG_LAI = _doc_tep("dung_lai_hddt.py")
MA_MC = _doc_tep("minvoice_chung_tu.py")
MA_DCM = _doc_tep("doi_chieu_mua.py")
MA_DCM_JS = _doc_tep("public", "js", "bep", "18-doi-chieu-may-in.js")


@ca("khoa ten: bo khoang trang thua, ha chu thuong, GIU NGUYEN dau")
def _():
	la("bo khoang trang hai dau", D.khoa_ten("  Phí vận chuyển  "), "phí vận chuyển")
	la("gop khoang trang giua", D.khoa_ten("Trân  châu\tkhoai"), "trân châu khoai")
	la("rong thi ra rong", D.khoa_ten(None), "")
	# Hai mon that su khac nhau cua chinh Green Ball. Bo dau la hai cai nay
	# van khac nhau, nhung "o long" va "ô long" thi khong duoc coi la mot
	# voi bat ky mon nao khac - nen o day KHONG bo dau.
	dung("hai ten khac nhau van khac nhau",
	     D.khoa_ten("Trân châu khoai (ô long)") != D.khoa_ten("Trân châu khoai (khoai môn)"))


@ca("ten nha cung cap ghi: doc o ten_hang_ncc truoc item_name")
def _():
	# Gan ma hang xong la ERPNext thay item_name bang ten Mon cua minh,
	# nen doc item_name khong thoi la mat dau ten goc.
	d = {"ten_hang_ncc": "Phí vận chuyển", "item_name": "Dịch vụ vận chuyển"}
	la("uu tien ten goc", D.ten_ncc_cua_dong(d), "Phí vận chuyển")
	la("khong co thi lui ve item_name",
	   D.ten_ncc_cua_dong({"item_name": "Dịch vụ vận chuyển"}), "Dịch vụ vận chuyển")
	la("khong co gi thi rong", D.ten_ncc_cua_dong({}), "")


@ca("nan don vi: chi nan khi may dang ha tam, khong de len khai bao cua nguoi")
def _():
	# Dong dang mang he so 1 (may ha tam), tra ra duoc he so that 1000.
	dung("ha tam thi nan", D.nen_nan_don_vi("Gram", 1, "Kg", 1000))
	# Nguoi da tu khai he so khac 1 thi de yen, do la khai bao cua ho.
	dung("nguoi khai roi thi de yen", not D.nen_nan_don_vi("Tui", 4000, "Kg", 1000))
	# Tra ra cung don vi dang dung thi khong co gi de nan.
	dung("cung don vi thi thoi", not D.nen_nan_don_vi("Kg", 1, "Kg", 1))
	dung("tra khong ra don vi thi thoi", not D.nen_nan_don_vi("Kg", 1, "", 1))


@ca("xep ma theo dong goc: ghep bang TEN truoc")
def _():
	goc = [D.khoa_ten("Trân châu khoai (ô long)"), D.khoa_ten("Phí vận chuyển")]
	# Uyen gan hai ma, thu tu tren to bi dao nguoc lai.
	to = [(D.khoa_ten("Phí vận chuyển"), "DVTI00003"),
	      (D.khoa_ten("Trân châu khoai (ô long)"), "NVLT00280")]
	ra = D.xep_ma_theo_dong_goc(to, goc, len(to))
	la("dong 1 cua ban goc lay dung ma", ra.get(0), "NVLT00280")
	la("dong 2 cua ban goc lay dung ma", ra.get(1), "DVTI00003")


@ca("xep ma theo dong goc: ten trung nhau trong mot to thi KHONG doan")
def _():
	goc = [D.khoa_ten("Phí vận chuyển"), D.khoa_ten("Phí vận chuyển")]
	to = [(D.khoa_ten("Phí vận chuyển"), "DVTI00003"),
	      (D.khoa_ten("Phí vận chuyển"), "DVTI00009")]
	la("khong xep dong nao", D.xep_ma_theo_dong_goc(to, goc, len(to)), {})


@ca("xep ma theo dong goc: dong mat ten thi ghep theo vi tri, nhung phai dung so dong")
def _():
	goc = ["a", "b"]
	# Dong khong con ten goc (to cu dung truoc 04/09/2026).
	to = [("", "M1"), ("", "M2")]
	la("dung so dong thi ghep theo vi tri",
	   D.xep_ma_theo_dong_goc(to, goc, 2), {0: "M1", 1: "M2"})
	# Them mot dong bu chenh lech thi van con ghep duoc.
	to3 = [("", "M1"), ("", "M2"), ("", "M3")]
	ra3 = D.xep_ma_theo_dong_goc(to3, goc, 3)
	la("dong bu khong lam hong phep ghep", ra3, {0: "M1", 1: "M2"})
	# Lech hon the la to da bi xao, doan vi tri luc do la gan nham ma.
	to9 = [("", "M%d" % i) for i in range(9)]
	la("to bi xao thi khong doan", D.xep_ma_theo_dong_goc(to9, goc, 9), {})


@ca("duong dung lai: tra anh xa khong ra thi lay ma dang co tren to")
def _():
	dung("co goi phep xep ma", "_ma_dang_gan(doc, dong_goc)" in MA_DUNG_LAI)
	dung("chi lay khi bang anh xa chiu", "if not ma and giu.get(vi_tri):" in MA_DUNG_LAI)
	dung("nan lai don vi cho ma vua lay",
	     "mc.don_vi_theo_ma(ma, x.get(\"dvt\"))" in MA_DUNG_LAI)
	dung("ghi lai ca that vao cho sua", "HDM-26-08-00149" in MA_DUNG_LAI)


@ca("nhip luu: hoc ma hang TRUOC roi moi tinh toi dung lai")
def _():
	# Chi soi THAN cua nhip luu, khong soi ca tep: ten ham nao cung xuat
	# hien o cho dinh nghia truoc, so vi tri tren ca tep la so nham.
	than = MA_DUNG_LAI[
		MA_DUNG_LAI.find("def dong_bo_luc_luu"):MA_DUNG_LAI.find("def tk_theo_mon")
	]
	i_hoc = than.find("hoc_ma_hang(doc, g)")
	i_ghim = than.find("da_ghim = ghim_lai_theo_goc(doc, g)")
	i_dung = than.find("nen, vi_sao = dung_lai_co_loi_khong(doc, g)")
	dung("co hoc ma hang", i_hoc > 0)
	dung("co buoc ghim nhe", i_ghim > 0)
	dung("hoc truoc khi ghim", i_hoc < i_ghim)
	dung("ghim truoc khi dung lai ca bang", i_ghim < i_dung)
	dung("hoc hong khong duoc lam chet luot luu",
	     "dung_lai_hddt: hoc ma hang" in than)
	# Da keo dong ve goc roi thi cau bao KHONG duoc noi la "giu nguyen to".
	dung("cau bao noi dung viec da lam", "Hệ thống đã kéo %d dòng" in than)


@ca("ghim lai theo goc: chi dung hai o lam sai tien, khong thay dong")
def _():
	i = MA_DUNG_LAI.find("def ghim_lai_theo_goc")
	j = MA_DUNG_LAI.find("def hoc_ma_hang")
	than = MA_DUNG_LAI[i:j]
	dung("co keo so luong ve goc", "d.qty = x.get(\"sl\")" in than)
	dung("co keo don gia ve goc", "d.rate = x.get(\"gia\")" in than)
	dung("ghim ca gia bang keo ERPNext khoi dien de",
	     "d.price_list_rate = x.get(\"gia\")" in than)
	dung("khong bao gio dung toi ma hang", "item_code =" not in than)
	dung("khong thay ca bang dong hang", "doc.set(\"items\"" not in than)
	dung("ten trung nhau thi bo qua, khong doan", "theo_khoa.pop(k, None)" in than)


@ca("hoc ma hang: khong bao gio de len mot anh xa da co")
def _():
	i = MA_DUNG_LAI.find("def hoc_ma_hang")
	j = MA_DUNG_LAI.find("def _tong_thue_tren_phieu")
	than = MA_DUNG_LAI[i:j]
	dung("o nho con trong moi ghi", "continue" in than and "item_code\") or \"\").strip():" in than)
	dung("cat duoi chi nhanh cua ma so thue", 'split("-")[0]' in than)
	dung("chi hoc tu dong co ten khop ban goc", "ten_goc.get(khoa_ten(" in than)
	# Ghi bang dung chu cua ban goc, khong phai chu dang nam tren chung tu:
	# phep tra anh xa so khop chinh xac, lech mot chu hoa la ghi xong khong
	# ai doc ra.
	dung("ghi bang chu cua ban goc", 'ten_goc.setdefault(khoa_ten(t), t[:140])' in than)
	dung("noi ro dieu 11 trong phan giai thich", "điều 11" in than)


@ca("dong hang nao cung phai giu ten nha cung cap ghi")
def _():
	# Truoc 04/09/2026 o nay chi ghi cho dong CHUA co ma hang. Gan ma vao la
	# ERPNext thay item_name bang ten Mon, ten goc bien mat, va mat ten goc
	# la mat khoa duy nhat de giu lai ma qua luot dung lai.
	i = MA_MC.find("def _dong_pi")
	j = MA_MC.find("def con_sot")
	than = MA_MC[i:j]
	dung("ghi ten goc ngoai nhanh if/else",
	     '\n\tdong["ten_hang_ncc"] = (x["ten"] or "")[:140]' in than)


@ca("nan don vi cua mot ma hang chi co MOT cho tinh")
def _():
	dung("co ham dung chung", "def don_vi_theo_ma(" in MA_MC)
	dung("duong tra ma hang goi ham do", "don_vi_theo_ma(mapped, uom)" in MA_MC)
	dung("duong dung lai cung goi ham do", "mc.don_vi_theo_ma(" in MA_DUNG_LAI)


@ca("ma so thue chi nhanh: ghi nho va tra cuu phai cung mot khoa")
def _():
	# MST chi nhanh co dang 0108269207-005. Duong tra anh xa luon cat o dau
	# gach, con `_mst_cua_to` truoc 04/09/2026 tra ve nguyen ca duoi, nen
	# cai ghi nho di vao mot khoa khong ai doc. He co 39 nha cung cap kieu
	# nay, va khong he bao loi mot cau nao.
	i = MA_DCM.find("def _mst_cua_to")
	j = MA_DCM.find("def goi_y_mon")
	than = MA_DCM[i:j]
	dung("cat duoi chi nhanh", 'return mst.split("-")[0]' in than)
	dung("cat dung mot cho cuoi ham", than.count('split("-")[0]') == 1)


@ca("bam nut xong phai xem lai tren to roi hay bao da lam duoc")
def _():
	# Nhip luu co quyen dung lai ca bang dong hang ngay trong luot bam, nen
	# cai dong cam tren tay chua chac con nam tren to. Bao "da gan" ma tren
	# to khong co ma nao la day nguoi ta di lam tiep tren mot thu khong that.
	for ten, moc in (
		("gan ma hang", "khong_giu_duoc"),
		("sua don vi", "khong_giu_duoc"),
	):
		dung("co duong bao that cho %s" % ten, moc in MA_DCM)
	dung("gan ma hang doc lai to sau khi luu",
	     MA_DCM.count('frappe.get_doc("Purchase Invoice", name)') >= 2)
	dung("noi phieu dem lai tren to", "that < cint(kq[\"da_noi\"])" in MA_DCM)
	dung("man hinh khong toast bua khi chua giu duoc",
	     "kq.khong_giu_duoc" in MA_DCM_JS)


@ca("cau dan nguoi dung khong duoc hua sai nua")
def _():
	# Ban cu doa "Nhung gi da sua tay tren dong hang se mat" - nay ma hang
	# thi giu, chi so luong va don gia moi ve so goc.
	dung("noi ro ma hang van giu", "Mã hàng đã gắn trên từng dòng thì vẫn giữ" in MA_DCM_JS)


@ca("quy uoc trinh bay: phan viet moi khong co dau gach dai")
def _():
	i = MA_DUNG_LAI.find("def khoa_ten")
	j = MA_DUNG_LAI.find("def _kiem_quyen")
	for ten, than in (("dung_lai_hddt", MA_DUNG_LAI[i:j]),):
		dung("%s khong em dash" % ten, "—" not in than)
		dung("%s khong en dash" % ten, "–" not in than)
