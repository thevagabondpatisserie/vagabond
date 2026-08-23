#!/usr/bin/env python3
"""May viet bang duong dan ben JavaScript tu danh muc ben Python.

    python3 sinh_duong.py           viet lai bang trong 02-trang-chu.js
    python3 sinh_duong.py --kiem    chi kiem, KHONG ghi. Lech thi tra ma loi 1

Vi sao co tep nay (v288, 23/08/2026)
------------------------------------
Ban dau co HAI bang gõ tay, mot ben Python mot ben JavaScript, va mot ca
kiem doi chieu chung. Ca kiem do chi bat duoc luc hai bang LECH nhau, khong
bat duoc luc ca hai cung SAI. Ngay 23/08 ca hai bang cung gan slug
`don-da-huy` cho khoa `DTREO`, ma `DTREO` la man "Don con treo". Ca kiem
xanh, nhan vien bam thi ra nham man.

Nay ban ben JavaScript do may viet, nen khong the lech. Xem duong_app.py.

Cach lam giong het `dung_app_bep.py`: may ghi vao giua hai dau moc, va ca
kiem doi chieu tung byte doan giua hai moc do.
"""

import io
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
if GOC not in sys.path:
	sys.path.insert(0, GOC)

TEP = os.path.join(GOC, "vagabond", "public", "js", "bep", "02-trang-chu.js")


def _doc():
	return io.open(TEP, encoding="utf-8").read()


def doan_dang_co(src=None):
	"""Doan giua hai dau moc dang nam trong tep. Rong neu chua co moc."""
	from vagabond.duong_app import MOC_CUOI, MOC_DAU

	s = src if src is not None else _doc()
	i = s.find(MOC_DAU)
	if i < 0:
		return ""
	j = s.find(MOC_CUOI, i)
	if j < 0:
		return ""
	return s[i:j + len(MOC_CUOI)]


def viet(kiem=False):
	from vagabond.duong_app import MOC_CUOI, MOC_DAU, sinh_js

	s = _doc()
	moi = sinh_js()
	i = s.find(MOC_DAU)
	if i < 0:
		print("Khong thay dau moc %s trong 02-trang-chu.js." % MOC_DAU)
		print("Dat hai dau moc quanh cho khai VGB_DUONG roi chay lai.")
		return 1
	j = s.find(MOC_CUOI, i)
	if j < 0:
		print("Thay moc dau nhung khong thay moc cuoi %s." % MOC_CUOI)
		return 1
	cu = s[i:j + len(MOC_CUOI)]
	if cu == moi:
		print("Bang duong dan da dung, khong phai viet lai. %d man." % moi.count("':"))
		return 0
	if kiem:
		print("LECH: bang trong 02-trang-chu.js khac ban may sinh ra.")
		print("Chay: python3 sinh_duong.py")
		return 1
	io.open(TEP, "w", encoding="utf-8").write(s[:i] + moi + s[j + len(MOC_CUOI):])
	print("Da viet lai bang duong dan, %d man." % moi.count("':"))
	return 0


if __name__ == "__main__":
	sys.exit(viet(kiem="--kiem" in sys.argv))
