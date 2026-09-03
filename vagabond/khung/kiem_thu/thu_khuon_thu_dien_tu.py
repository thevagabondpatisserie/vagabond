# -*- coding: utf-8 -*-
"""Kiem thu khuon thu dien tu dung chung (vagabond/thu_khung.py), 03/09/2026.

Anh Viet: *"Em ra lai email de fix toan bo nhe."*

Ra lai 17 cho may gui thu thi thay bon kieu thu khac nhau, va mot thu dang
HONG (thu bao thanh toan cho nha cung cap, tu v369: bien phong `mc` duoc
tham chieu ngoai pham vi khai bao). Nay moi thu di qua MOT khuon.

Nhung dieu ca kiem nay chot:

  1. Khuon thu la phep THUAN: dung duoc khong can Frappe, nen xem truoc va
     kiem thu duoc tren may CI tay khong.
  2. Moi tep co goi gui thu deu phai di qua khuon. Them mot cho gui thu moi
     ma khong boc khuon thi ca kiem do - do la ca ly do khuon ton tai.
  3. Chan thu chon theo NGUOI NHAN: khach thay dia chi quay va hotline, nha
     cung cap thay phap nhan va ma so thue, nhan vien thay cho hoi ve app,
     thu noi bo noi ro la thu tu dong. Lech mot cai la khach doc duoc so
     Zalo cua anh Viet, hay ke toan doc duoc "dat banh online".
  4. Anh trong thu nam trong repo, khong tro ve mot tep ai do da upload len
     site roi mat dau. Tro ve tep ngoai repo la mot ngay nao do thu trong.
  5. Moi mang mau thuong hieu deu lot anh nen kem bgcolor du phong, vi Gmail
     che do toi dao mau mang sang thuan CSS.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import thu_khung as tk

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
GOI = os.path.join(GOC, "vagabond")


def _doc(*duong):
	with io.open(os.path.join(GOC, *duong), encoding="utf-8") as f:
		return f.read()


def _thu_mau(chan="khach", nhan="Báo giá", nut=True):
	return tk.khung_thuan(
		"Tiêu đề <thử>", tk.doan("Thân thư <b>đậm</b>"),
		nut_html=tk.nut("https://x.vn/a?b=1&c=2", "Mở app", goc_anh="https://app.x") if nut else "",
		chan=chan, nhan=nhan, goc_anh="https://app.x",
		cac_quay=["District 1: 9 Trần Cao Vân", "NVHTN: 21 Phạm Ngọc Thạch"],
	)


# --------------------------------------------------------------- phep thuan

@ca("khuon thu: dung duoc khong can Frappe, ra mot la thu 600px co logo")
def _():
	t = _thu_mau()
	dung("bang 600", 'width="600"' in t)
	dung("co dai dau thu tu repo", "/assets/vagabond/images/thu/dau.png" in t)
	dung("tieu de duoc thoat", "Tiêu đề &lt;thử&gt;" in t)
	dung("than thu giu HTML", "Thân thư <b>đậm</b>" in t)
	dung("co nhan HOA", "text-transform:uppercase" in t and "Báo giá" in t)
	dung("co nut", "Mở app" in t and 'href="https://x.vn/a?b=1&amp;c=2"' in t)
	dung("CSS inline, khong the style", "<style" not in t)
	dung("khong em dash", "—" not in t and "–" not in t)


@ca("khuon thu: mang mau thuong hieu lot anh nen kem bgcolor du phong")
def _():
	t = _thu_mau()
	dung("dai dau lot anh", 'background="https://app.x/assets/vagabond/images/thu/lot-xanh.png" bgcolor="%s"' % tk.XANH in t)
	n = tk.nut("https://x", "Mở", goc_anh="https://app.x")
	dung("nut lot anh", 'background="https://app.x/assets/vagabond/images/thu/lot-xanh.png"' in n)
	o = tk.o_kem("x", goc_anh="https://app.x")
	dung("o kem lot anh kem", "lot-kem.png" in o and 'bgcolor="%s"' % tk.KEM in o)
	dung("o kem co vach xanh", 'bgcolor="%s"' % tk.XANH in o)


@ca("khuon thu: chan thu chon theo nguoi nhan, khong lan nhau")
def _():
	k = _thu_mau("khach")
	dung("khach thay quay", "9 Trần Cao Vân" in k and "21 Phạm Ngọc Thạch" in k)
	dung("khach thay hotline", tk.HOTLINE in k)
	dung("khach thay web dat banh", tk.WEB_DAT_BANH in k)
	dung("khach KHONG thay Zalo anh Viet", "0901" not in k)
	dung("khach KHONG thay ma so thue", "0318561568" not in k)

	n = _thu_mau("ncc")
	dung("ncc thay phap nhan", "CÔNG TY TNHH PATISSERIE VAGABOND" in n)
	dung("ncc thay ma so thue", "0318561568" in n)
	dung("ncc KHONG thay dat banh online", tk.WEB_DAT_BANH not in n)
	dung("ncc KHONG thay Zalo", "0901" not in n)

	v = _thu_mau("nhan_vien")
	dung("nhan vien thay cho hoi app", "0901 486 556" in v)
	dung("nhan vien KHONG thay hotline khach", tk.HOTLINE not in v)

	b = _thu_mau("noi_bo")
	dung("noi bo noi ro thu tu dong", "thư tự động" in b)
	dung("noi bo khong can tra loi", "Không cần trả lời" in b)
	dung("noi bo KHONG thay hotline", tk.HOTLINE not in b)

	dung("chan la thi roi ve khach", tk.HOTLINE in _thu_mau("gi_do"))


@ca("khuon thu: khong nut thi khong de lo o trong, khong nhan thi khong de dong trong")
def _():
	t = _thu_mau(nut=False, nhan="")
	dung("khong co the a", "<a href" not in t)
	dung("khong co nhan hoa", "text-transform:uppercase" not in t.split("Tiêu đề")[0])


@ca("khuon thu: bang so lieu co dau bang, ke mang va dong tong")
def _():
	b = tk.bang([("Số hoá đơn", "left"), ("Số tiền", "right")],
		[["HD1", "1.000 đ"], ["HD2", "2.000 đ"]], tong=("Tổng cộng", "3.000 đ"))
	dung("hai dong", b.count("border-bottom:1px solid %s" % tk.KE) == 4)
	dung("dau bang nen kem", 'bgcolor="%s"' % tk.KEM in b)
	dung("cot tien canh phai", "text-align:right" in b)
	dung("co tong", "TỔNG CỘNG" in b.upper() and "3.000 đ" in b)
	la("tien", tk.tien(1234567.4), "1.234.567")
	la("tien hong", tk.tien("x"), "0")


@ca("khuon thu: cap nhan - gia tri va chu ky")
def _():
	c = tk.cap([("Phiếu", "<b>HT-1</b>"), ("Lý do", "móp")])
	dung("hai dong", c.count("<tr>") == 2)
	dung("nhan duoc thoat", "Phiếu" in c and "Lý do" in c)
	k = tk.chu_ky("Loan Anh <x>", "Sales", "0909")
	dung("ky ten thoat", "Loan Anh &lt;x&gt;" in k and "Trân trọng" in k)


# --------------------------------------------------------------- toan he

def _tep_gui_thu():
	ra = []
	for ten in sorted(os.listdir(GOI)):
		if not ten.endswith(".py"):
			continue
		m = _doc("vagabond", ten)
		if "frappe.sendmail(" in m:
			ra.append(ten)
	return ra


@ca("khuon thu: MOI tep co goi gui thu deu di qua khuon chung")
def _():
	ds = _tep_gui_thu()
	dung("tim thay cac tep gui thu", len(ds) >= 12)
	for ten in ds:
		m = _doc("vagabond", ten)
		qua_khuon = (
			"from vagabond import thu_khung" in m
			or "_khung_thu(" in m
			or "thu_moi_html(" in m
			or "thu_phan_cong_html(" in m
			or "thu_tai_xe_huy_html(" in m
			or ten == "thu_khung.py"
		)
		dung("%s boc khuon" % ten, qua_khuon)


@ca("khuon thu: khong con tep nao tu ve khung thu rieng")
def _():
	for ten in _tep_gui_thu():
		if ten in ("thu_khung.py",):
			continue
		m = _doc("vagabond", ten)
		dung("%s khong tu ve nen #F2FAFC" % ten, "#F2FAFC" not in m)
		dung("%s khong tro anh dau thu ngoai repo" % ten, "vgb_email_header.png" not in m)
		dung("%s khong ghep font-family Arial tay" % ten, 'font-family:Arial,sans-serif' not in m)


@ca("khuon thu: thu bao nha cung cap het loi bien phong ngoai pham vi")
def _():
	m = _doc("vagabond", "ho_so_tt.py")
	i = m.find("def _nut_doi_chieu(")
	than = m[i:m.find("\n\n\n", i)]
	dung("khong con mc.", "mc." not in than)
	dung("dung khuon chung", "_tk.nut(" in than)
	i = m.find("def _thu_html(")
	than = m[i:m.find("def _o_doi_chieu(")]
	dung("chan ncc", 'chan="ncc"' in than)
	dung("dung bang chung", "_tk.bang(" in than)


@ca("khuon thu: chan thu dung cho tung loai nguoi nhan o tung cho goi")
def _():
	# Khach
	for ten, ham in (("ban_hang.py", "def _xhd_mail_tiep_nhan("), ("bao_gia.py", "def gui_email("),
			("cong_no.py", "def _thu_da_nhan_html("), ("hop_dong_pdf.py", "def gui_email("),
			("thu_hop_dong.py", "def gui_email("), ("khuyen_mai.py", "def _gui_mail_lo(")):
		m = _doc("vagabond", ten)
		i = m.find(ham)
		than = m[i:m.find("\n\n\n", i)]
		dung("%s %s gui cho khach" % (ten, ham), 'chan="khach"' in than)
	# Noi bo
	for ten, ham in (("hoan_tien.py", "def _bao_ke_toan("), ("gui_thu.py", "def _khung_bao_dong("),
			("minvoice_chung_tu.py", "def _khung_chuong("), ("diem_han.py", "def _bao_nguoi(")):
		m = _doc("vagabond", ten)
		i = m.find(ham)
		than = m[i:m.find("\n\n\n", i)]
		dung("%s %s la thu noi bo" % (ten, ham), 'chan="noi_bo"' in than)
	m = _doc("vagabond", "ban_hang.py")
	dung("ba thu canh bao ban hang la noi bo", m.count('chan="noi_bo"') >= 3)
	# Nhan vien
	m = _doc("vagabond", "nhan_su.py")
	dung("thu moi la nhan vien", 'chan="nhan_vien"' in m[m.find("def thu_moi_html("):])


@ca("khuon thu: anh dung trong thu nam trong repo")
def _():
	thu_muc = os.path.join(GOI, "public", "images", "thu")
	for ten in (tk.ANH_DAU, tk.ANH_LOT_XANH, tk.ANH_LOT_KEM):
		duong = os.path.join(thu_muc, ten)
		dung("co %s" % ten, os.path.exists(duong) and os.path.getsize(duong) > 50)


@ca("khuon thu: mau trung voi bo nhan dien cua mau in")
def _():
	m = _doc("vagabond", "mau_in", "thuong_hieu.py")
	dung("robin egg trung", 'XANH = "%s"' % tk.XANH in m)
	dung("muc trung", 'MUC = "%s"' % tk.MUC in m)
	dung("kem trung", 'KEM = "%s"' % tk.KEM in m)
	dung("ke trung", 'KE = "%s"' % tk.KE in m)


@ca("bat nhan tien ra lai: ba cua hoa don thay the co import kiem quyen")
def _():
	# Khong lien quan khuon thu, nhung bat duoc trong cung lan ra 03/09/2026
	# khi soi ca tep bang pyflakes: ba ham goi _kiem_quyen() ma khong import,
	# bam nut tren app la NameError. Chot lai de khong tai dien.
	m = _doc("vagabond", "hoan_tien.py")
	for ham in ("def ghi_hddt_thay_the(", "def go_hddt_thay_the(", "def can_ghi_thay_the("):
		i = m.find(ham)
		than = m[i:m.find("\n\n\n", i)]
		if "_kiem_quyen()" in than:
			dung("%s co import kiem quyen" % ham, "import _kiem_quyen" in than)
