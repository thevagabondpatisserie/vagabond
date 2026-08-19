# -*- coding: utf-8 -*-
"""Dam bao server co bo phong chu tieng Viet dung Arial khi in PDF.

CAU CHUYEN
Anh Viet bao to hop dong in ra "khong phai font Arial". Em tai mot to PDF
that ve, doc bang phong nhung trong do va doc luon bang ma nguoi dung
(ToUnicode CMap) thi ra ket qua nay:

	LiberationSans, LiberationSans-Bold, LiberationSans-Italic,
	LiberationSans-BoldItalic, DejaVuSans, DejaVuSans-Bold

Bang ma cua DejaVuSans liet ke dung 46 chu: 1ED1 1ED9 1EAD 1EF1 1EE7
01B0 1EDB 1EC7 01A1 1EA1 ... nghia la toan bo cho DejaVu gach ra deu la
chu cai tieng Viet co dau thanh. Server co Liberation Sans, nhung la ban
1.07.4 khong co bang Latin Extended Additional, nen wkhtmltopdf lay
Liberation cho chu khong dau roi muon DejaVu cho rieng chu co dau. Hai
kieu chu lech nhau ngay trong cung mot tu. Do la loi anh Viet nhin thay,
chu khong phai loi cau CSS.

CACH CHUA
Mang han ban Liberation Sans 2.1.5 theo trong ung dung, doi ten ho thanh
"Vagabond Sans" roi chep vao thu muc phong cua nguoi dung tren server.
fontconfig se thay no va wkhtmltopdf dung duoc ngay, khong can quyen root
va khong can sua anh Docker. Xem them vagabond/fonts/README.md.

VI SAO CHEP LUC IN CHU KHONG PHAI LUC MIGRATE
Moi lan deploy la mot container moi. Neu chi chep trong patch thi lan nao
Frappe Cloud dung lai container ma khong chay migrate la mat phong. Kiem
"thu muc da co chua" ton mot lenh os.path.isdir, re, nen goi thang truoc
moi lan dung PDF la chac an nhat.

KHONG BAO GIO NEM LOI
Ham nay hong thi to PDF van phai in ra duoc, chi la xau phong tro lai nhu
cu. Vi vay moi loi deu nuot, va ghi mot dong log de con lan ra.
"""
import os
import shutil

import frappe

HO_PHONG = "Vagabond Sans"

# Xau phong dung cho MOI to PDF cua bao gia va hop dong. Vagabond Sans
# dung dau vi do la ban duy nhat chac chan co du tieng Viet. Arial va
# Liberation Sans dung sau lam luoi do phong, phong khi thu muc phong
# chua chep kip.
NGAN_XEP = "'Vagabond Sans',Arial,'Liberation Sans',Helvetica,sans-serif"

CAC_TEP = (
	"VagabondSans-Regular.ttf",
	"VagabondSans-Bold.ttf",
	"VagabondSans-Italic.ttf",
	"VagabondSans-BoldItalic.ttf",
)


def thu_muc_nguon():
	"""Thu muc chua bon tep .ttf di kem ung dung."""
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def cac_thu_muc_dich():
	"""Hai cho fontconfig tren Debian doc phong cua nguoi dung.

	Ghi ca hai vi khong doan duoc anh Docker cua Frappe Cloud cau hinh
	kieu nao. Chep hai lan ton them 1,6 MB dia, doi lai khoi phai doan.
	"""
	nha = os.path.expanduser("~")
	if not nha or nha == "~":
		return []
	xdg = os.environ.get("XDG_DATA_HOME") or os.path.join(nha, ".local", "share")
	return [
		os.path.join(xdg, "fonts", "vagabond"),
		os.path.join(nha, ".fonts", "vagabond"),
	]


def da_du(thu_muc):
	"""Thu muc dich da co du bon tep va dung kich thuoc chua."""
	nguon = thu_muc_nguon()
	for t in CAC_TEP:
		a = os.path.join(thu_muc, t)
		b = os.path.join(nguon, t)
		if not os.path.isfile(a):
			return False
		try:
			if os.path.getsize(a) != os.path.getsize(b):
				return False
		except OSError:
			return False
	return True


def bao_dam_phong():
	"""Chep bo phong sang thu muc nguoi dung neu chua co. Nuot moi loi.

	Tra ve so thu muc da san sang. 0 nghia la khong chep duoc cho nao,
	luc do to PDF roi ve xau phong cu chu khong hong.
	"""
	nguon = thu_muc_nguon()
	dem = 0
	moi = False
	for dich in cac_thu_muc_dich():
		try:
			if da_du(dich):
				dem += 1
				continue
			if not os.path.isdir(dich):
				os.makedirs(dich)
			for t in CAC_TEP:
				shutil.copyfile(os.path.join(nguon, t), os.path.join(dich, t))
			dem += 1
			moi = True
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chep phong chu that bai")
	if moi:
		_nap_lai_bo_dem()
	return dem


def _nap_lai_bo_dem():
	"""Goi fc-cache neu co. Khong co cung khong sao.

	fontconfig van quet thu muc khi thieu bo dem, chi cham hon mot chut.
	Nen day chi la toi uu, khong phai dieu kien bat buoc.
	"""
	try:
		import subprocess

		subprocess.call(
			["fc-cache", "-f"] + cac_thu_muc_dich(),
			stdout=open(os.devnull, "w"),
			stderr=open(os.devnull, "w"),
			timeout=30,
		)
	except Exception:
		pass


@frappe.whitelist()
def thu_phong():
	"""Bao cao tinh trang phong tren server. Chi de soi khi co su co.

	Tra ve: thu muc nguon, tung thu muc dich va da du chua, HOME dang la
	gi, va danh sach phong ho "Vagabond" ma fontconfig nhin thay.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ System Manager mới xem được. Nhờ anh Việt mở giúp.")
	ra = {
		"ho_phong": HO_PHONG,
		"ngan_xep": NGAN_XEP,
		"nguon": thu_muc_nguon(),
		"nha": os.path.expanduser("~"),
		"da_chep": bao_dam_phong(),
		"dich": [],
		"fc_list": "",
	}
	for d in cac_thu_muc_dich():
		ra["dich"].append({"duong_dan": d, "co": os.path.isdir(d), "du": da_du(d)})
	try:
		import subprocess

		ra["fc_list"] = subprocess.check_output(
			["fc-list", ":family"], timeout=30
		).decode("utf-8", "ignore")[:4000]
	except Exception as e:
		ra["fc_list"] = "khong chay duoc fc-list: %s" % e
	return ra
