"""Ca kiem cho ba viec sua ngay 03/09/2026 sau khi anh Viet bao loi.

1. QR xuat hoa don in mien app.* nen khach quet bi da ve app noi bo.
2. Man hinh khach (CFD) toi den va de len man thu ngan.
3. Thong bao day dien thoai chet im vi khoa VAPID dua sai dang.
Va mot loi cua chinh phien v387: man Xuat ban si doc o `remarks` khong co.

Toan phep thuan cong voi doc ma nguon, khong can Frappe, khong can site.
"""

import io
import json
import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(
		os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	)


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


def _www(ten):
	return io.open(os.path.join(_goc(), "vagabond", "www", ten), encoding="utf-8").read()


def _node(ma):
	"""Chay mot doan JavaScript bang node, tra ve stdout da cat khoang trang."""
	r = subprocess.run(["node", "-e", ma], capture_output=True, text=True, timeout=20)
	if r.returncode != 0:
		raise AssertionError("node loi: " + (r.stderr or "").strip()[:400])
	return (r.stdout or "").strip()


def _ham_js(tep, ten):
	"""Cat nguyen mot ham `function ten(...) {...}` o dau dong ra khoi tep."""
	src = _js(tep)
	m = re.search(r"\nfunction %s\([^)]*\) \{.*?\n\}" % re.escape(ten), src, re.S)
	if not m:
		raise AssertionError("khong thay ham %s trong %s" % (ten, tep))
	return m.group(0)


# ============================================================ 1. QR xuat hoa don


@ca("qr xhd: /xhd di qua MOI ten mien, khong bi da")
def _xhd_moi_mien():
	from vagabond.ten_mien import MIEN_APP, MIEN_DESK, MIEN_KHACH, dich_chuyen_huong

	for m in (MIEN_APP, MIEN_DESK, MIEN_KHACH):
		la("%s cho /xhd di" % m, dich_chuyen_huong(m, "/xhd", ()), "")
		la("%s cho /xhd/ di" % m, dich_chuyen_huong(m, "/xhd/", ()), "")
	# Luat cu cho cac trang khach KHAC van nguyen: chi /xhd duoc mo rong,
	# khong phai mo toang ca nhom.
	la("app vao /banh van bi da", dich_chuyen_huong(MIEN_APP, "/banh", ()), "/bep")
	la("erp vao /tt van bi da", dich_chuyen_huong(MIEN_DESK, "/tt", ()), "/app")


@ca("qr xhd: link_khach ra dia chi tuyet doi tren mien khach")
def _link_khach():
	from vagabond.ten_mien import MIEN_KHACH, link_khach

	la("co query", link_khach("/xhd?d=HDB-1&t=abc"),
		"https://%s/xhd?d=HDB-1&t=abc" % MIEN_KHACH)
	la("thieu gach dau", link_khach("xhd"), "https://%s/xhd" % MIEN_KHACH)
	la("goc", link_khach("/"), "https://%s" % MIEN_KHACH)
	dung("khong bao gio la mien app", "app." not in link_khach("/xhd"))


@ca("qr xhd: pos_link_xhd tra dia chi TUYET DOI, khong con tuong doi")
def _pos_link():
	m = _py("ban_hang.py")
	than = m.split("def pos_link_xhd(")[1].split("\n@frappe.whitelist")[0]
	dung("dung link_khach", "link_khach(" in than)
	la("khong tra thang chuoi tuong doi nua", '"url": "/xhd?' in than, False)


@ca("qr xhd: man in bill khong ghep location.origin lam duong chinh nua")
def _bill_khong_origin():
	j = _js("10-bill-quay.js")
	than = j.split("d.xhd_url && M.qr_xhd")[1].split("qrKhoi =")[0]
	dung("nhan dia chi tuyet doi tu may chu", "/^https?:\\/\\//.test(d.xhd_url)" in than)
	# Van giu nhanh cu cho may chu cu, nhung KHONG duoc la nhanh duy nhat.
	la("khong con dong ghep tran", "var ulink = location.origin + d.xhd_url;" in j, False)


# ============================================================ 2. man hinh khach


@ca("cfd: chon man phu uu tien man KHONG chinh, mot man thi null")
def _chon_man_phu():
	ham = _ham_js("25-man-hinh-khach.js", "cfdChonManPhu")
	ra = _node(ham + """
var a = cfdChonManPhu([{isPrimary:true,availLeft:0},{isPrimary:false,availLeft:1920}]);
var b = cfdChonManPhu([{isPrimary:true}]);
var c = cfdChonManPhu([]);
var d = cfdChonManPhu(null);
var e = cfdChonManPhu([{availLeft:0},{availLeft:1920}]);
console.log(JSON.stringify([a && a.availLeft, b, c, d, e && e.availLeft]));
""")
	la("ket qua", json.loads(ra), [1920, None, None, None, 1920])


@ca("cfd: dac tinh cua so dat TRON trong man phu")
def _dac_tinh():
	ham = _ham_js("25-man-hinh-khach.js", "cfdDacTinhCuaSo")
	ra = _node(ham + """
console.log(cfdDacTinhCuaSo({availLeft:1920,availTop:0,availWidth:1366,availHeight:728}));
console.log(cfdDacTinhCuaSo(null));
""")
	dong = ra.split("\n")
	la("chuoi", dong[0], "popup=1,left=1920,top=0,width=1366,height=728")
	la("khong man thi rong", dong[1] if len(dong) > 1 else "", "")


@ca("cfd: may mot man hinh thi noi Duplicate va KHONG mo cua so")
def _mot_man_khong_mo():
	j = _js("25-man-hinh-khach.js")
	than = j.split("async function cfdMo(")[1].split("\nfunction cfdGan(")[0]
	dung("kiem screen.isExtended truoc", "window.screen.isExtended === false" in than)
	dung("bao dung chu Duplicate", "Duplicate" in than)
	dung("bao cach sua Win+P", "Win+P" in than)
	# Sau khi bao thi PHAI return, khong duoc roi xuong window.open.
	doan = than.split("isExtended === false")[1].split("getScreenDetails")[0]
	dung("return ngay sau khi bao", "return;" in doan)
	# Va tra tieu diem ve man thu ngan sau khi mo.
	dung("tra tieu diem ve", "window.focus()" in than)


@ca("cfd: nut Mo di qua cfdMo, khong con window.open tran")
def _nut_mo():
	j = _js("25-man-hinh-khach.js")
	gan = j.split("function cfdGan(")[1]
	dung("goi cfdMo", "cfdMo()" in gan)
	la("khong con window.open thang trong cfdGan", "window.open(" in gan, False)


@ca("cfd: trang man hinh khach giu man sang bang Wake Lock")
def _wake_lock():
	h = _www("man-hinh-khach.html")
	dung("xin wakeLock", "navigator.wakeLock.request('screen')" in h)
	# Khoa bi thu khi trang bi che, phai xin lai luc hien tro lai.
	dung("xin lai khi hien tro lai", "addEventListener('visibilitychange', giuSang)" in h)
	dung("xin lai dinh ky", "setInterval(giuSang" in h)
	# Trinh duyet khong co API thi khong duoc vo: phai co bao ve.
	than = h.split("function giuSang()")[1].split("giuSang();")[0]
	dung("chan khi khong co API", "!navigator.wakeLock" in than)


@ca("cfd: cham mot lan la phong to, va chi mot lan")
def _cham_mot_lan():
	h = _www("man-hinh-khach.html")
	dung("bat pointerdown", "document.addEventListener('pointerdown', chamDau)" in h)
	dung("go ngay sau lan dau", "document.removeEventListener('pointerdown', chamDau)" in h)
	# Trang nay quay ra khach: khong duoc doi hoi mot cu cham NUA moi phong to.
	dung("khong phong to khi da toan man", "if (!document.fullscreenElement) toanMan();" in h)


@ca("cfd: ranh gioi rieng tu van nguyen sau khi sua")
def _rieng_tu_nguyen():
	# Sua chuyen mo cua so KHONG duoc lam goi tin phinh them mot o nao.
	ham = _ham_js("25-man-hinh-khach.js", "cfdDungGoi")
	for cam in ("sdt", "so_dien_thoai", "ma_khach", "hang_the", "diem", "cong_no", "mst"):
		la("goi tin khong co o %s" % cam, re.search(r"\b%s\s*:" % cam, ham) is not None, False)


# ============================================================ 3. thong bao day


@ca("thong bao: nhan dang khoa rieng dang luu")
def _dang_khoa():
	from vagabond.thong_bao import dang_khoa_rieng

	# 32 byte base64url, dung dang _sinh_khoa sinh ra (43 ky tu, khong dau bang).
	raw = "A" * 43
	la("raw", dang_khoa_rieng(raw), "raw")
	la("pem", dang_khoa_rieng("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"), "pem")
	la("rong", dang_khoa_rieng(""), "hong")
	la("ngan", dang_khoa_rieng("abc"), "hong")
	la("khong phai base64", dang_khoa_rieng("!!!!" * 11), "hong")


@ca("thong bao: dua DOI TUONG Vapid cho pywebpush, khong dua chuoi PEM")
def _doi_tuong_vapid():
	# pywebpush 2.x chi doc PEM khi chuoi la DUONG DAN TEP. Dua nguyen van
	# PEM thi no goi Vapid.from_string, ham do base64 giai ma ca "-----BEGIN"
	# roi nem "ASN.1 parsing error". 53 lan tu 31/08, khong mot thong bao
	# nao di duoc. Chot bang ma nguon de khong ai "toi uu" lai thanh PEM.
	m = _py("thong_bao.py")
	la("ham _pem khong con", "def _pem(" in m, False)
	than = m.split("def _khoa_vapid(")[1].split("\ndef ")[0]
	dung("from_raw cho khoa 32 byte", "Vapid.from_raw(" in than)
	dung("from_pem cho ai lo dan PEM", "Vapid.from_pem(" in than)
	gui = m.split("def gui(")[1]
	dung("gui() dung _khoa_vapid", "_khoa_vapid(rieng)" in gui)
	dung("chan khoa hong truoc khi gui", 'dang_khoa_rieng(rieng) == "hong"' in gui)
	dung("khoa dua vao webpush la doi tuong", "vapid_private_key=khoa," in gui)


# ============================================================ 4. loi v387


@ca("xuat ban si: Delivery Note khong co remarks, phai dung o rieng")
def _khong_remarks():
	# Loi cua chinh phien v387: ghi doc.remarks (Frappe im lang bo qua) va
	# doc `remarks` trong get_all (MariaDB nem Unknown column). Chot bang
	# ma nguon: ngoai ghi chu ra, khong con chu "remarks" nao dung lam TEN O.
	m = _py("xuat_ban.py")
	khong_ghi_chu = re.sub(r"#.*", "", m)
	la("khong doc.remarks", "doc.remarks" in khong_ghi_chu, False)
	la("khong lay cot remarks", '"remarks",' in khong_ghi_chu, False)
	dung("co o dien giai rieng", '"fieldname": "vgb_dien_giai"' in m)
	dung("luu vao o rieng", "doc.set(O_DIEN_GIAI," in m)
	dung("danh sach doc o rieng", "O_DIEN_GIAI,\n\t\t]," in m)


@ca("xuat kho them: ba man danh sach KHONG nuot loi may chu")
def _khong_nuot_loi():
	# Ban v387 nuot im, nen khi may chu do thi man hien "chua co phieu nao".
	# Nhin nhu binh thuong, va loi nam do ba ngay.
	j = _js("45-xuat-kho-them.js")
	la("khong con catch rong sau ds_phieu", "ds_phieu', { gioi_han: 40 })) || []; } catch (e) { }" in j, False)
	la("ba man deu bat loi", j.count("catch (e) { loiDs = errMsg(e)"), 3)
	dung("co khoi bao loi", "function xktLoiHtml(loi)" in j)
	# v397 gom ba man vao mot ham ve chung xktManDanhSach, nen loi di qua
	# cfg.loi roi ham chung ve khoi do (ghep lai 03/09 sau khi v397 merge).
	la("ba man deu dua loi vao man chung", j.count("loi: loiDs,"), 3)
	dung("man chung ve khoi loi", "rows = xktLoiHtml(cfg.loi);" in j)


# ============================================ 5. dong bo Pancake xoa mat khach


def _ham_py(tep, ten):
	"""Cat mot ham THUAN ra khoi tep Python roi nap, khong keo theo frappe."""
	m = _py(tep)
	than = m.split("\ndef %s(" % ten)[1]
	than = "def %s(" % ten + than.split("\n\n\n")[0]
	kho = {}
	exec(than, kho)
	return kho[ten]


@ca("dong bo Pancake: don da mang khach that thi GIU, khong dat lai ve gio chung")
def _giu_khach():
	# Don 92862 ngay 01/09/2026: 18:32 nhip dong bo gan dung KL028403 theo so
	# dien thoai, 19:00 nhip sau doi ve "Khach le Online", 23:32 vet cuoi ngay
	# chan vi "ban cong no phai chon khach". May tim ra dung nguoi roi tu xoa
	# di, Loan Anh phai chon tay lai.
	giu = _ham_py("ban_hang.py", "giu_khach_cua_don")
	gop = lambda k: k in ("Khách lẻ Online", "Khách bán lẻ")
	la("don cu, khach that: giu", giu(object(), "KL028403", gop), True)
	la("don cu, gio chung: tim lai", giu(object(), "Khách lẻ Online", gop), False)
	la("don cu, gio ban le: tim lai", giu(object(), "Khách bán lẻ", gop), False)
	la("don cu, trong: tim lai", giu(object(), "", gop), False)
	la("don cu, None: tim lai", giu(object(), None, gop), False)
	la("don moi: luon tim", giu(None, "KL028403", gop), False)


@ca("dong bo Pancake: _upsert_hoa_don di qua giu_khach_cua_don, khong con dat khach_don = gio")
def _upsert_dung_ham_giu():
	m = _py("ban_hang.py")
	than = m.split("\ndef _upsert_hoa_don(")[1].split("\n\n\ndef ")[0]
	khong_ghi_chu = re.sub(r"#.*", "", than)
	dung("co goi ham giu", "if giu_khach_cua_don(cu, si.get(\"customer\"), la_khach_gop):" in khong_ghi_chu)
	dung("giu thi lay khach dang co", "khach_don = si.get(\"customer\")" in khong_ghi_chu)
	la("khong con dieu kien cu", "if (not cu) or la_khach_gop(si.get(\"customer\")):" in khong_ghi_chu, False)
