# -*- coding: utf-8 -*-
"""Dung bo phong chu Vagabond Sans tu Liberation Sans 2.1.5.

VI SAO CAN TEP NAY
Server Frappe Cloud co san Liberation Sans nhung la ban 1.07.4, ban do
KHONG co cac chu cai tieng Viet co dau thanh (bang Latin Extended
Additional, U+1EA0 den U+1EFF). Khi in hop dong, wkhtmltopdf lay
Liberation Sans cho chu khong dau roi tu dong muon DejaVu Sans cho rieng
chu co dau, nen trong cung mot tu ma hai kieu chu lech nhau. Do dung la
loi phong ma anh Viet nhin thay.

Ban Liberation Sans 2.1.5 thi co du tieng Viet. Nen cach chua la mang
han ban 2.1.5 theo trong ung dung. Nhung neu de nguyen ten ho "Liberation
Sans" thi tren server se co hai ban trung ten, fontconfig chon ban nao la
chuyen hen xui. Vi vay doi ten ho thanh "Vagabond Sans".

Giay phep: Liberation Fonts theo SIL Open Font License 1.1. Giay phep do
BAT BUOC ban sua doi phai bo ten danh rieng "Liberation", nen viec doi
ten o day vua la nhu cau ky thuat vua la dieu giay phep doi hoi. Toan van
giay phep nam tai vagabond/fonts/OFL.txt.

Chay lai khi nao: chi khi can dung lai bo phong, vi du nang len ban
Liberation moi hon. Binh thuong khong dong den.

	python3 dung_phong.py
"""
import os
import sys

HO_CU = "Liberation Sans"
HO_MOI = "Vagabond Sans"
PS_CU = "LiberationSans"
PS_MOI = "VagabondSans"

CAC_KIEU = (
	("Regular", "LiberationSans-Regular.ttf", "VagabondSans-Regular.ttf"),
	("Bold", "LiberationSans-Bold.ttf", "VagabondSans-Bold.ttf"),
	("Italic", "LiberationSans-Italic.ttf", "VagabondSans-Italic.ttf"),
	("Bold Italic", "LiberationSans-BoldItalic.ttf", "VagabondSans-BoldItalic.ttf"),
)

NGUON = "/usr/share/fonts/truetype/liberation"
DICH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vagabond", "fonts")


def doi_ten(tu, den):
	from fontTools.ttLib import TTFont

	f = TTFont(tu)
	for r in f["name"].names:
		v = str(r)
		if HO_CU in v:
			v = v.replace(HO_CU, HO_MOI)
		if PS_CU in v:
			v = v.replace(PS_CU, PS_MOI)
		if r.nameID == 3:
			# Unique ID: them hau to cho khoi trung voi ban goc.
			v = v + " (Vagabond)"
		if r.nameID == 7:
			# O nhan hieu ban goc ghi "Liberation is a trademark of Red Hat".
			# Giu nguyen cau do tren mot ban da doi ten la de nguoi doc hieu
			# nham. Thay bang mot cau noi ro day la ban dan xuat, van ghi
			# nhan nhan hieu cua Red Hat.
			v = ("Vagabond Sans la ban dan xuat cua Liberation Sans 2.1.5. "
			     "Liberation la nhan hieu cua Red Hat, Inc.")
		r.string = v
	f.save(den)
	f.close()


def main():
	if not os.path.isdir(NGUON):
		print("Khong thay thu muc phong nguon: %s" % NGUON)
		return 1
	if not os.path.isdir(DICH):
		os.makedirs(DICH)
	for ten, tu, den in CAC_KIEU:
		d1 = os.path.join(NGUON, tu)
		if not os.path.isfile(d1):
			print("Thieu tep nguon: %s" % d1)
			return 1
		doi_ten(d1, os.path.join(DICH, den))
		print("%-12s %s -> %s" % (ten, tu, den))
	return 0


if __name__ == "__main__":
	sys.exit(main())
