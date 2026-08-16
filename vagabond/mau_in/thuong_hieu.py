"""Font va logo theo bo nhan dien Vagabond, dung chung cho moi mau in.

Vi sao NHUNG THANG vao to chu khong tro duong dan
--------------------------------------------------
Luat nay he da hoc mot lan roi va ghi lai o hai cho: _qr_data_uri trong
cong_no.py va _anh_data trong bao_gia.py. wkhtmltopdf chay mot tien trinh
rieng; tro src toi duong dan tuong doi hay toi mot may chu ngoai thi co
luc no khong tai duoc, va to gui khach ma trong khung anh hay mat font thi
hong. Doc thang tu dia roi nhung dang data URI la chac an.

Bo nhan dien (theo goi thiet ke story cua Vagabond)
---------------------------------------------------
  Vagabond Sans  chi dung cho tieu de, luon VIET HOA
  Qualy          dung cho van xuoi, KHONG dung cho tieu de
  #4FDCF2        mau chu dao
  #1A1A1A        chu tren nen sang
  #FAF7F2        nen kem

Ca hai font da duoc kiem: du 100% dau tieng Viet va du chu so.
"""

import base64
import os

import frappe

THU_MUC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "mau_in")

# Mau theo bo nhan dien. Khai o day de nam mau muon doi thi doi mot cho.
XANH = "#4FDCF2"
MUC = "#1A1A1A"
KEM = "#FAF7F2"
XAM = "#8C857B"
KE = "#D9D2C7"


def _doc(ten):
	duong = os.path.join(THU_MUC, ten)
	if not os.path.exists(duong):
		return b""
	with open(duong, "rb") as f:
		return f.read()


def _b64(ten):
	noi = _doc(ten)
	return base64.b64encode(noi).decode() if noi else ""


def logo():
	"""Logo den tren nen trong, dang data URI. Rong rong cho to in tren giay trang."""
	def _lam():
		b = _b64("logo-den.png")
		return ("data:image/png;base64," + b) if b else ""

	return frappe.cache().get_value("vgb:mau_in:logo", _lam)


def font_css():
	"""Khoi @font-face nhung san hai font cua bo nhan dien."""
	def _lam():
		ra = []
		for ten_font, tep in (
			("Vagabond Sans", "VagabondSans-Regular.otf"),
			("Qualy", "Qualy.otf"),
		):
			b = _b64(tep)
			if not b:
				continue
			ra.append(
				"@font-face{font-family:'%s';font-style:normal;font-weight:400;"
				"src:url(data:font/otf;base64,%s) format('opentype');}" % (ten_font, b)
			)
		return "".join(ra)

	return frappe.cache().get_value("vgb:mau_in:font", _lam)


def co_du_bo():
	"""Da co du font va logo chua. Dung de chan doan, KHONG chan viec in."""
	return {
		"logo": bool(_doc("logo-den.png")),
		"vagabond_sans": bool(_doc("VagabondSans-Regular.otf")),
		"qualy": bool(_doc("Qualy.otf")),
		"thu_muc": THU_MUC,
	}
