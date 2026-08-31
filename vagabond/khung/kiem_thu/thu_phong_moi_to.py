# -*- coding: utf-8 -*-
"""Kiem thu: MOI to PDF phai dung bo phong co du dau tieng Viet.

Anh Viet 31/08/2026, khi xuat to Bien ban ban giao tien mat: *"file PDF anh
xuat ra thi van bi loi font tum lum, em vui long ghi vao backend de tu nay
ve sau khong bi loi font bat cu file nao nua."*

GOC CUA LOI, tim ra lan nay
---------------------------
`nop_quy._html_bien_ban` khai mot phong co chan ma may chu Frappe Cloud
KHONG co. wkhtmltopdf lay mot phong thay the khong du dau tieng Viet, roi
muon mot phong khac cho rieng chu co dau. Hai kieu chu lech nhau ngay trong
cung mot tu - dung cai anh Viet nhin thay. Cung mot benh voi v223, khac cho.

VI SAO PHAI CO BO CA KIEM NAY chu khong chi sua mot cho
-------------------------------------------------------
Truoc ban nay, xau phong bi CHEP TAY o NAM noi khac nhau va khong noi nao
biet noi nao. Sua mot cho thi bon cho kia van hong, va lan sau ai them mot
to PDF moi lai chep tay mot xau nua.

Nay chi con HAI nguon: `phong_chu.NGAN_XEP` cho BAN IN va
`mau_chuan.PHONG_THU` cho THU DIEN TU. Bo ca kiem duoi day quet CA THU MUC,
nen them mot to moi ma quen phong thi cong kiem do ngay.

VI SAO TACH PHONG THU RA RIENG
------------------------------
Thu hien tren may NGUOI NHAN, khong di qua wkhtmltopdf, nen no khong dinh
chuyen may chu thieu phong. Nguoc lai, nhet mot cai ten phong may nguoi ta
khong co vao thu thi hop thu nao cung tu chon mot phong khac. Hai viec nguoc
nhau, nen phai hai xau phong.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.phong_chu import NGAN_XEP, css_ep

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
THU_MUC = os.path.join(GOI, "vagabond")

# Phong KHONG duoc khai THANG trong ma nguon. Times New Roman thi may chu
# khong co. Arial thi may chu cung khong co, va no la cai bay lon nhat vi ai
# cung tuong may nao cung co Arial.
PHONG_CAM = ("Times New Roman", "font-family:Arial", "font-family: Arial")

BA_NHAY = chr(34) * 3
BA_NHAY_DON = chr(39) * 3


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _cac_tep_py():
	ra = []
	for goc, _tm, tep in os.walk(THU_MUC):
		if "__pycache__" in goc or os.sep + "khung" + os.sep in goc + os.sep:
			continue
		for t in tep:
			if t.endswith(".py"):
				ra.append(os.path.join(goc, t))
	return sorted(ra)


def _tep_sinh_pdf():
	"""Tep nao goi get_pdf. Do bang cach DOC ma nguon, khong doan theo ten."""
	ra = []
	for p in _cac_tep_py():
		s = io.open(p, encoding="utf-8").read()
		if "get_pdf(" in s and "def get_pdf" not in s:
			ra.append((os.path.relpath(p, GOI), s))
	return ra


def _dong_ma(s):
	"""Cac dong ma THAT: bo dong trong, dong ghi chu, va than docstring.

	Vi sao can. Ban dau ca kiem quet ca tep, nen chinh CAU GHI CHU giai
	thich "khong duoc dung phong nay" cung bi tinh la vi pham. Ca kiem bat
	nham chinh loi giai thich cua no la ca kiem vo dung.
	"""
	ra, trong_doc, dau = [], False, ""
	for d in (s or "").splitlines():
		t = d.strip()
		if trong_doc:
			if dau in t:
				trong_doc = False
			continue
		if not t or t.startswith("#"):
			continue
		mo = False
		for q in (BA_NHAY, BA_NHAY_DON):
			if q in t:
				# Mot dong mo va dong luon thi khong phai khoi nhieu dong.
				if t.count(q) % 2 == 1:
					trong_doc, dau, mo = True, q, True
				break
		if mo:
			continue
		ra.append(d)
	return "\n".join(ra)


@ca("phông: phép lọc dòng ghi chú của chính bộ ca kiểm này chạy đúng")
def _():
	la("bỏ dòng ghi chú", _dong_ma("# font-family:Arial\nx = 1"), "x = 1")
	la("bỏ thân docstring nhiều dòng",
		_dong_ma("def f():\n\t" + BA_NHAY + "font-family:Arial\n\tcòn nữa\n\t"
			+ BA_NHAY + "\n\treturn 1"),
		"def f():\n\treturn 1")
	la("giữ nguyên dòng mã thật",
		_dong_ma('a = "font-family:Arial"'), 'a = "font-family:Arial"')


@ca("phông: mọi tệp sinh PDF đều lấy xâu phông từ một nguồn duy nhất")
def _():
	tep = _tep_sinh_pdf()
	dung("có tìm thấy tệp sinh PDF để kiểm", len(tep) >= 4)
	for ten, s in tep:
		co_nguon = (
			"phong_chu import" in s
			or "mau_chuan import PHONG" in s
			or "mau_chuan.khung_trang" in s
			or "mc.PHONG" in s
		)
		dung("%s có lấy phông từ nguồn chung" % ten, co_nguon)


@ca("phông: không tệp nào của ứng dụng khai thẳng phông máy chủ không có")
def _():
	# Quet CA THU MUC chu khong chi cac tep sinh PDF: mot tep hom nay chi
	# soan thu, ngay mai co the them mot to in, va luc do cai xau phong go
	# tay nam san o do se di theo vao to in.
	for p in _cac_tep_py():
		ten = os.path.relpath(p, GOI)
		ma = _dong_ma(io.open(p, encoding="utf-8").read())
		for cam in PHONG_CAM:
			dung("%s không khai %s" % (ten, cam), cam not in ma)


@ca("phông: xâu phông bản in có đủ hai phông chắc chắn dựng được dấu tiếng Việt")
def _():
	# Vagabond Sans la ban Liberation Sans 2.1.5 mang theo ung dung, xem
	# vagabond/fonts/README.md. DejaVu Sans la phong duy nhat chac chan co
	# san tren may chu. Mat ca hai la to in vo dau.
	dung("có Vagabond Sans", "Vagabond Sans" in NGAN_XEP)
	dung("có DejaVu Sans", "DejaVu Sans" in NGAN_XEP)
	dung("Vagabond Sans đứng trước Arial",
		NGAN_XEP.index("Vagabond Sans") < NGAN_XEP.index("Arial"))
	dung("DejaVu Sans đứng trước Arial",
		NGAN_XEP.index("DejaVu Sans") < NGAN_XEP.index("Arial"))
	la("câu CSS ép phông", css_ep(), "*{font-family:%s}" % NGAN_XEP)


@ca("phông: khung trang chuẩn tự chép phông và tự ép phông")
def _():
	s = _doc("vagabond", "mau_chuan.py")
	i = s.find("def khung_trang(")
	j = s.find("\ndef ", i + 10)
	than = s[i:j]
	dung("khung chuẩn có gọi chép phông", "bao_dam_phong()" in than)
	dung("khung chuẩn ép phông bằng dấu sao", "*{font-family:" in than)
	# Chep phong hong thi to van phai in ra duoc.
	dung("chép phông hỏng không được làm đổ tờ in", "except Exception:" in than)
	dung("xâu phông bản in không còn viết tay trong mau_chuan",
		"'DejaVu Sans','Liberation Sans',Arial" not in s)


@ca("phông: tờ biên bản bàn giao tiền mặt đã hết phông có chân")
def _():
	s = _doc("vagabond", "nop_quy.py")
	dung("không còn phông có chân trong mã",
		"Times New Roman" not in _dong_ma(s))
	dung("đi qua khung chuẩn", "mau_chuan.khung_trang(" in s)


@ca("phông: thư điện tử có xâu phông riêng, khai một nơi")
def _():
	from vagabond.mau_chuan import PHONG_THU

	dung("phông thư là phông máy nào cũng có", PHONG_THU.startswith("Arial"))
	dung("phông thư khác phông bản in", PHONG_THU != NGAN_XEP)
	for t in ("bao_gia.py", "hop_dong_pdf.py", "cong_no.py", "ho_so_tt.py"):
		dung("%s dùng phông thư từ nguồn chung" % t,
			"PHONG_THU" in _doc("vagabond", t))


@ca("phông: khung lề chung nhận được xâu phông từ nơi gọi")
def _():
	s = _doc("vagabond", "mau_in", "le_in.py")
	dung("css_trang có tham số phông", "def css_trang(le_mm=LE_MM, phong=" in s)
	# Tep le_in phai giu tinh thuan: khong import gi cua Frappe.
	dung("le_in vẫn không import frappe", "import frappe" not in s)
	h = _doc("vagabond", "ho_so_tt.py")
	dung("bộ hồ sơ thanh toán có truyền phông vào", "css_trang(phong=mc.PHONG)" in h)
	dung("bộ hồ sơ thanh toán có chép phông trước khi in", "bao_dam_phong()" in h)


@ca("phông: bốn tệp phông vẫn nằm trong ứng dụng")
def _():
	from vagabond.phong_chu import CAC_TEP

	for t in CAC_TEP:
		p = os.path.join(GOI, "vagabond", "fonts", t)
		dung("còn tệp %s" % t, os.path.exists(p))
		if os.path.exists(p):
			dung("tệp %s không rỗng" % t, os.path.getsize(p) > 100000)
