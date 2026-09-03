# -*- coding: utf-8 -*-
"""Kiem thu hai viec anh Viet chot ngay 03/09/2026 (dot hai).

1. CAI DAT TRANG DAT BANH WEB, NUT DONG BO TU PANCAKE
   *"Minh Vu da import hinh anh moi len tren pancake nhung ben web khong tu
   map hinh do ve. Em co the cho anh 1 nut cai dat web ben trong phan he
   cai dat va co nut nhan dong bo de ban ay tu nhan sau khi cai cac thu ben
   pancake de dong bo ve duoc khong?"*

   Nguyen nhan do ra: tab In season doc anh tu DONG bang mua vu, ma dong do
   chi duoc ghi luc keo DON ve. Khong co don moi cho ma do thi anh cu nam
   mai. Hai tab kia hoi Pancake nhung nho ket qua nua tieng.

   Ba hang rao cua nut dong bo:
     a. Khong ghi de anh mon ben Next da co. Danh muc Next la bo chuan, doi
        phai doi co chu dich o man Danh muc.
     b. Pancake khong co anh thi KHONG xoa anh dang giu. Mat anh ben Pancake
        khong duoc keo theo mat anh tren web.
     c. Ghi lai anh dong khong dung vao dau thoi gian cua phieu.

2. TAB IN STORE TREN TRANG DAT BANH
   *"em cho them 1 tab In Store ke ben tab In Season de dong bo nhung mon co
   the ban va so luong banh len tab do lay tu man kiem banh nhe de khach nao
   hoi thi gui cai link do de khach lua."*

   Bon hang rao:
     a. Chi bay dong DANG THEO DOI va con > 0. Dong chua ai khai ma bay ra
        so am hay so may la noi sai voi khach.
     b. Banh si (BAWS) va ma bi cong tac tay tat thi khong len, giong hai
        tab kia.
     c. Cua cho khach vang lai CHI DOC va chi tra ten, anh, gia, so con.
        Ton dau, da ban, hong, ghi chu la so noi bo cua quay.
     d. Khong co nut them vao gio. Gio la don online giao tu bep; banh tren
        tu quay thi khach toi lay. Tron hai thu la bep lam mot cai banh
        dang nam san o quay.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kiem_kho, web_dong_bo

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(duong):
	with io.open(os.path.join(GOC, duong), encoding="utf-8") as f:
		return f.read()


def _than(m, dau, cuoi=None):
	i = m.find(dau)
	dung("tim thay %s" % dau, i >= 0)
	j = m.find(cuoi, i + 1) if cuoi else -1
	return m[i:j] if j > 0 else m[i:]


# ------------------------------------------------- 1. dong bo web: phep thuan

@ca("dong bo web: gom ma bo trung, bo trong, bo banh si, giu thu tu")
def _():
	la("gom ba tab", web_dong_bo.gom_ma(["A", "B"], ["B", "", None, "C"], ["A"]), ["A", "B", "C"])
	la("banh si khong len web", web_dong_bo.gom_ma(["BAWS00001", "BAWC00001"]), ["BAWC00001"])
	la("cat khoang trang", web_dong_bo.gom_ma([" X "]), ["X"])
	la("rong thi rong", web_dong_bo.gom_ma([], None), [])


@ca("dong bo web: Pancake khong co anh thi KHONG xoa anh dang giu")
def _():
	dung("Pancake rong, giu nguyen", not web_dong_bo.can_doi_anh("", "/files/a.jpg"))
	dung("Pancake None, giu nguyen", not web_dong_bo.can_doi_anh(None, "/files/a.jpg"))
	dung("khac thi doi", web_dong_bo.can_doi_anh("https://p/moi.jpg", "https://p/cu.jpg"))
	dung("dang trong thi dien", web_dong_bo.can_doi_anh("https://p/moi.jpg", ""))
	dung("giong thi thoi", not web_dong_bo.can_doi_anh("https://p/a.jpg", " https://p/a.jpg "))


@ca("dong bo web: ban do anh tu danh muc, ma hau to size cho ma goc muon anh")
def _():
	bo = lambda m: m.replace("S16CM", "")
	dm = [
		{"ma": "BAWC00104S16CM", "anh": "https://p/104.jpg"},
		{"ma": "BAWC00105", "anh": ""},
		{"ma": "BAWC00106", "anh": "https://p/106a.jpg"},
		{"ma": "BAWC00106", "anh": "https://p/106b.jpg"},
		{"ma": "", "anh": "https://p/rac.jpg"},
	]
	bd = web_dong_bo.ban_do_anh(dm, bo_hau_to=bo)
	la("ma hau to giu anh", bd.get("BAWC00104S16CM"), "https://p/104.jpg")
	la("ma goc muon anh", bd.get("BAWC00104"), "https://p/104.jpg")
	dung("khong anh thi khong co", "BAWC00105" not in bd)
	la("giu anh gap truoc", bd.get("BAWC00106"), "https://p/106a.jpg")
	dung("ma rong bo qua", "" not in bd)


@ca("dong bo web: liet ke dung ma thieu anh ben Pancake")
def _():
	la("hai ma thieu, sap thu tu",
		web_dong_bo.ma_thieu_anh(["Z1", "A1", "M1"], {"M1": "https://p/m.jpg", "A1": " "}),
		["A1", "Z1"])
	la("rong", web_dong_bo.ma_thieu_anh([], {}), [])


@ca("dong bo web: anh rieng tu cua Next khong dung len web")
def _():
	dung("/private thi khong", not web_dong_bo.anh_dung_duoc("/private/files/a.jpg"))
	dung("/files thi duoc", web_dong_bo.anh_dung_duoc("/files/a.jpg"))
	dung("https thi duoc", web_dong_bo.anh_dung_duoc("https://p/a.jpg"))
	dung("rong thi khong", not web_dong_bo.anh_dung_duoc(""))


# ------------------------------------------------- 1. dong bo web: cham he

@ca("dong bo web: cua ngo dung, quyen dung, khong ghi de anh mon Next")
def _():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	la("hai cua ngo", sorted(thu_cua_ngo.CUA_NGO.get("web_dong_bo.py", [])), ["dong_bo", "tinh_hinh"])
	m = _doc("vagabond/web_dong_bo.py")
	dung("dong_bo co whitelist", "@frappe.whitelist()\ndef dong_bo(" in m)
	dung("tinh_hinh co whitelist", "@frappe.whitelist()\ndef tinh_hinh(" in m)
	for f in ("def dong_bo(", "def tinh_hinh("):
		dung("%s kiem quyen" % f, "_kiem_quyen()" in _than(m, f, "\n\n\n"))
	# Chi gan anh cho mon CHUA co anh. Doi bo loc nay la ghi de danh muc chuan.
	gan = _than(m, "def _gan_anh_mon_trong(", "def _doc_lan_cuoi(")
	dung("chi mon trong anh", '"image": ["in", ["", None]]' in gan)
	dung("gan qua duong da co cua doi_soat", "doi_soat._gan_anh_url(" in gan)
	ghi = _than(m, "def _ghi_lai_hinh(", "def _gan_anh_mon_trong(")
	dung("ghi anh khong dung dau thoi gian phieu", "update_modified=False" in ghi)
	dung("ghi anh qua phep thuan can_doi_anh", "can_doi_anh(" in ghi)
	dung("tinh_hinh khong hoi Pancake", "keo_san_pham_pancake" not in _than(m, "def tinh_hinh(", "def dong_bo("))


@ca("dong bo web: keo danh muc MOT LUOT, khong hoi Pancake tung ma")
def _():
	# 26/08 Pancake tra 403 hai ngay vi bi hoi nhieu. Nut nay phai keo danh
	# muc theo trang (vai lan goi), khong duoc lap tung ma.
	m = _doc("vagabond/web_dong_bo.py")
	than = _than(m, "def dong_bo(", None)
	dung("dung keo_san_pham_pancake", "doi_soat.keo_san_pham_pancake()" in than)
	dung("khong goi _sp_pancake tung ma", "_sp_pancake(" not in than and "_anh_pancake(" not in than)
	dung("xoa dem cho khach mo lan sau thay moi", "_xoa_dem(" in than)
	dung("luu lan cuoi", "set_default(KHOA_LAN_CUOI" in than)
	dung("Pancake hong thi noi ro bang loi", "Pancake không trả danh mục" in than)


@ca("dong bo web: tab In season lay anh danh muc Pancake truoc, don khong ghi de")
def _():
	m = _doc("vagabond/mua_vu.py")
	web = _than(m, "def hang_theo_mua(", None)
	dung("anh Pancake truoc", 'anh_pancake.get(d.ma_hang) or d.hinh or x.get("image")' in web)
	dung("qua bo dem cua kiem_banh", "kiem_banh._anh_pancake(" in _than(m, "def _anh_danh_muc_pancake(", "def hang_theo_mua("))
	dung("van la cua khach vang lai", "@frappe.whitelist(allow_guest=True)\ndef hang_theo_mua(" in m)
	# Don ve chi BU cho dong trong, khong ghi de: neu ghi de thi nut dong bo
	# bam xong, lan keo don ke tiep lai tra ve anh cu.
	keo = _than(m, "def _keo_that(", "@frappe.whitelist()")
	dung("don chi bu cho dong trong", 'if hinh.get(ma) and not str(d.hinh or "").strip():' in keo)
	dung("khong con dong ghi de cu", "hinh[ma] != d.hinh" not in keo)


@ca("dong bo web: co man trong Cai dat, co duong dan, co nhanh dieu huong")
def _():
	from vagabond import duong_app

	dung("co trong bang MAN", any(k == "CDWEB" for k, _t, _s in duong_app.MAN))
	dung("slug sinh dung", duong_app.DUONG.get("trang-dat-banh-web") == "CDWEB"
		or "trang-dat-banh-web" in str(duong_app.DUONG))
	tc = _doc("vagabond/public/js/bep/02-trang-chu.js")
	dung("co the tren man Cai dat", "'CDWEB')" in tc)
	dung("co nhanh dieu huong", "if (k === 'CDWEB') return go(scrCaiDatWeb);" in tc)
	dung("nam trong nhom KHAC", "'CDWEB'" in _than(tc, "{ k: 'KHAC'", "\n"))
	cd = _doc("vagabond/public/js/bep/17-cai-dat.js")
	dung("co man", "async function scrCaiDatWeb()" in cd)
	man = _than(cd, "async function scrCaiDatWeb()", None)
	dung("goi dung hai cua", "'vagabond.web_dong_bo.tinh_hinh'" in man and "'vagabond.web_dong_bo.dong_bo'" in man)
	dung("hien ma thieu anh ben Pancake", "thieu_anh_tren_pancake" in man)
	dung("noi ro khong ghi de", "không ghi đè" in man)


# ------------------------------------------------- 2. in store: phep thuan

def _dong(ma, ton_dau=0, nhap_1=0, hong=0, dieu_chinh=0, theo_doi=0):
	d = {"ma_hang": ma, "ton_dau": ton_dau, "hong": hong, "dieu_chinh": dieu_chinh, "theo_doi": theo_doi}
	for k in kiem_kho.O_NHAP:
		d[k] = 0
	d["nhap_1"] = nhap_1
	return d


@ca("in store: chi bay dong dang theo doi va con > 0")
def _():
	dong = [
		_dong("BAWC00001", ton_dau=5),                 # co khai, con 5
		_dong("BAWC00002"),                            # may tu them, chua ai khai
		_dong("BAWC00003", ton_dau=2),                 # ban het -> 0
		_dong("BAWC00004", nhap_1=3),                  # nhap dot 1, ban 1 -> 2
		_dong("BAWC00005", theo_doi=1),                # theo doi nhung 0
	]
	ban = {"BAWC00002": 4, "BAWC00003": 2, "BAWC00004": 1}
	la("dung hai ma", kiem_kho.dong_len_web(dong, ban), [("BAWC00001", 5), ("BAWC00004", 2)])
	# Hang rao "dang theo doi" phai nam trong code du phep con > 0 hien nay
	# da che duoc no: mai mot co them cot lam con > 0 ma chua ai khai (vi du
	# ton may tu dem) thi hang rao nay la cai chan cuoi.
	m = _doc("vagabond/kiem_kho.py")
	dung("hang rao theo doi nam trong phep", "if not dang_theo_doi(r):" in _than(m, "def dong_len_web(", "# Giờ sớm nhất"))


@ca("in store: banh si va ma bi tat khong len, du con hang")
def _():
	dong = [_dong("BAWS00001", ton_dau=9), _dong("BAWC00009", ton_dau=9), _dong("BAWC00010", ton_dau=9)]
	tat = {"BAWC00010": {"tat": True}}
	la("con dung mot", kiem_kho.dong_len_web(dong, {}, tat), [("BAWC00009", 9)])


@ca("in store: so am khong bao gio len web")
def _():
	dong = [_dong("BAWC00011", ton_dau=1)]
	la("ban lo thi khong bay", kiem_kho.dong_len_web(dong, {"BAWC00011": 3}), [])
	la("khong dong thi rong", kiem_kho.dong_len_web([], {}), [])
	la("None cung rong", kiem_kho.dong_len_web(None, None), [])


# ------------------------------------------------- 2. in store: cham he

@ca("in store: cua khach vang lai chi DOC, chi tra ten-anh-gia-so con")
def _():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	dung("da khai cua ngo", "con_tren_quay_web" in thu_cua_ngo.CUA_NGO.get("kiem_kho.py", []))
	m = _doc("vagabond/kiem_kho.py")
	dung("mo cho khach", "@frappe.whitelist(allow_guest=True)\ndef con_tren_quay_web(" in m)
	than = _than(m, "def con_tren_quay_web(", None)
	for cam in ("set_value", ".save(", ".insert(", "_luu_may(", "_lay_hoac_tao("):
		dung("khong %s" % cam, cam not in than)
	tra = _than(than, 'q["mon"].append({', "})")
	for cam in ('"ton_dau"', '"da_ban"', '"hong"', '"ghi_chu"', '"kiem_tay"', '"lech"'):
		dung("khong lo %s" % cam, cam not in tra)
	dung("qua phep thuan dong_len_web", "dong_len_web(dong, ban, tat)" in than)
	dung("co cong tac tay", "tat_ban_web.bang(" in than)
	dung("anh rieng tu khong len", 'startswith("/private")' in than)
	dung("mon da tat ben Next khong len", 'cint(x.get("disabled"))' in than)


@ca("in store: trang web co tab, co duong dan, KHONG co gio hang")
def _():
	w = _doc("vagabond/trang/banh.html")
	dung("co nut tab", 'data-tab="store" id="tabStore" hidden' in w)
	dung("co khoi", '<main id="store" hidden>' in w)
	dung("goi dung cua", '"/api/method/vagabond.kiem_kho.con_tren_quay_web"' in w)
	dung("co duong #/in-store", "'#/in-store'" in w and "isStore=/^\\/in-store/" in w)
	dung("setTab biet tab store", "mQ.hidden=t!=='store'" in w)
	khoi = _than(w, "var STORE={quay:[]};", "napTonQuay();\n/* Nhip")
	for cam in ("themHangMua", "CART.push", "onclick=", "moSheetMua", "Thêm vào giỏ"):
		dung("khong co %s" % cam, cam not in khoi)
	dung("het banh thi noi ro, khong an tab", "đã bán hết bánh trong tủ" in khoi)
	dung("co cach giu banh", "m.me/thevagabond.saigon" in _than(w, '<main id="store" hidden>', "</main>"))
	dung("tab cuon ngang khi bon tab", ".tabs{overflow-x:auto" in w)
	dung("nhip 60 giay", "setInterval(napTonQuay,60000)" in w)
