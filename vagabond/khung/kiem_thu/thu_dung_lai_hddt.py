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

	la("dong_tu_hoa_don(it)", list(inspect.signature(mc.dong_tu_hoa_don).parameters), ["it"])
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
