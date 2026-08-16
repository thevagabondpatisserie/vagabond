#!/usr/bin/env python3
"""Cong kiem: moi the tren app phai co duong den mot man hinh.

    python3 kiem_dinh_tuyen.py

Ma tra ve 0 la moi the deu bam duoc. Khac 0 la co the CHET.

Vi sao co tep nay (16/08/2026)
------------------------------
Anh Viet bam the "Hoan tien / Tra hang" tren dien thoai, khong co phan ung
gi. Doc ma moi thay 02-trang-chu.js co HAI cho dinh tuyen chep gan nhu
nguyen si cua nhau: mot ban trong scrHome, mot ban la vgbGo. Em them nhanh
'HT' vao ban thu nhat, dung cau lenh Python co assert dem == 1 nen yen tam
la sua dung mot cho duy nhat. That ra hai ban da lech nhau tu truoc: ban
trong scrHome co 'HT' ma thieu 'XKH','XKD'; vgbGo co 'XKH','XKD' ma thieu
'HT'. Anh bam tu man phan he Ban hang, duong do di qua vgbGo.

Nay hai ban da gop lam mot. Nhung gop roi khong co nghia la khong tai dien:
ai them the moi ma quen them nhanh thi the do lai chet lang le, khong bao
loi, khong ghi log, khong co gi ngoai mot cai bam khong an. Dung loi cham
nhat de tim ra: phai co nguoi cam dien thoai bam thu.

Nen cong nay lam dung mot viec: gom moi khoa the trong ma, doi chieu voi
cac nhanh trong vgbGo, va bat cai nao khong co duong den.
"""

import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
BEP = os.path.join(GOC, "vagabond", "public", "js", "bep")
TRANG_CHU = os.path.join(BEP, "02-trang-chu.js")
KHUNG = os.path.join(BEP, "01-khung-app.js")


def doc(duong):
	with open(duong, encoding="utf-8") as f:
		return f.read()


def than_vgb_go(ma):
	"""Cat lay than ham vgbGo. Thieu ham nay la loi nang, khong bo qua."""
	i = ma.find("function vgbGo(k) {")
	if i < 0:
		raise SystemExit("KHONG TIM THAY ham vgbGo trong 02-trang-chu.js. "
			"Ai doi ten ham dinh tuyen thi sua lai ten trong kiem_dinh_tuyen.py.")
	sau = ma[i:]
	# Ham nay phang, khong co ham long nhau ngoai mot callback mot dong,
	# nen dem ngoac nhon la du.
	sau_ngoac = sau.find("{")
	muc = 0
	for vt in range(sau_ngoac, len(sau)):
		if sau[vt] == "{":
			muc += 1
		elif sau[vt] == "}":
			muc -= 1
			if muc == 0:
				return sau[:vt + 1]
	raise SystemExit("Ham vgbGo thieu dau dong ngoac.")


def khoa_co_duong(than):
	"""Cac khoa vgbGo xu ly duoc bang mot nhanh viet ro."""
	return set(re.findall(r"k === '([^']+)'", than))


def khoa_tien_to(than):
	"""Cac nhanh bat theo tien to, vi du BC: hay KT."""
	return re.findall(r"k\.indexOf\('([^']+)'\) === 0", than)


def khoa_cac_the(ma):
	"""Moi khoa gan vao mot the tren man, tu ham card(...) va vgbODong(...).

	card(icon, tieu de, mo ta, so dem, KHOA[, xanh])
	"""
	ra = set()
	for m in re.finditer(r"card\(([^;]*?)\)\s*\+", ma, re.S):
		phan = m.group(1)
		cac = re.findall(r"'((?:[^'\\]|\\.)*)'", phan)
		# Doi so thu 5 la khoa. Bat theo dang khoa: chu HOA va so, khong dau cach.
		for c in cac[3:]:
			if re.fullmatch(r"[A-Z][A-Z0-9:]{1,12}", c):
				ra.add(c)
				break
	return ra


def khoa_cac_nhom(ma):
	"""Moi khoa liet ke trong VGB_NHOM - do la cai hien tren man phan he."""
	i = ma.find("var VGB_NHOM = [")
	if i < 0:
		return set()
	doan = ma[i:ma.find("];", i)]
	ra = set()
	for m in re.finditer(r"keys:\s*\[([^\]]*)\]", doan):
		ra |= set(re.findall(r"'([^']+)'", m.group(1)))
	return ra


def khoa_TYPES(ma_khung):
	"""Cac khoa roi vao nhanh cuoi: go(scrMRList(TYPES[k]))."""
	i = ma_khung.find("var TYPES = {")
	if i < 0:
		return set()
	doan = ma_khung[i:ma_khung.find("\n};", i)]
	return set(re.findall(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:", doan, re.M)) | set(
		re.findall(r"'([^']+)'\s*:", doan))


def co_man_hinh(ten_man):
	"""Ham man hinh nay co that trong thu muc bep khong."""
	for t in sorted(os.listdir(BEP)):
		if t.endswith(".js") and re.search(
			r"function\s+%s\s*\(" % re.escape(ten_man), doc(os.path.join(BEP, t))
		):
			return True
	return False


def chay():
	ma = doc(TRANG_CHU)
	loi = []

	# --- 1. Chi duoc co MOT cho dinh tuyen -----------------------------
	so_cho_bat = len(re.findall(r"closest\('\[data-go\]'\)", ma))
	so_goi = len(re.findall(r"vgbGo\(", ma))
	than = than_vgb_go(ma)
	# Moi cho bat su kien phai goi vgbGo chu khong tu xu.
	for m in re.finditer(r"closest\('\[data-go\]'\)", ma):
		doan = ma[m.start():m.start() + 700]
		if "vgbGo(" not in doan:
			loi.append(
				"Co mot cho bat [data-go] ma KHONG goi vgbGo - lai chep them mot "
				"ban dinh tuyen nua. Xoa di, goi vgbGo."
			)
	print("      %d cho bat the, %d loi goi vgbGo, %d nhanh trong vgbGo"
		% (so_cho_bat, so_goi, len(khoa_co_duong(than))))

	# --- 2. Moi khoa the phai co duong ---------------------------------
	co = khoa_co_duong(than)
	tien_to = khoa_tien_to(than)
	qua_TYPES = khoa_TYPES(doc(KHUNG))
	can = khoa_cac_the(ma) | khoa_cac_nhom(ma)

	def duoc_xu(k):
		if k in co or k in qua_TYPES:
			return True
		return any(k.startswith(t) for t in tien_to)

	chet = sorted(k for k in can if not duoc_xu(k))
	for k in chet:
		loi.append(
			"The khoa '%s' co tren man nhung vgbGo khong co nhanh nao nhan no. "
			"Bam vao se khong co phan ung gi - dung cai loi 16/08." % k
		)

	# --- 3. Man hinh vgbGo tro toi phai ton tai ------------------------
	for m in re.finditer(r"k === '([^']+)'\) return go\((scr[A-Za-z0-9_]+)\)", than):
		if not co_man_hinh(m.group(2)):
			loi.append(
				"Khoa '%s' tro toi ham %s, ma khong tim thay ham do trong bep/. "
				"Bam vao se do loi truoc mat nguoi dung." % (m.group(1), m.group(2))
			)

	print("      %d khoa the doi chieu, %d khoa qua TYPES, %d tien to"
		% (len(can), len(qua_TYPES), len(tien_to)))

	if loi:
		print("")
		print("KHONG DAT - %d loi dinh tuyen:" % len(loi))
		for d in loi:
			print("  - " + d)
		return 1
	print("      DAT: moi the deu co duong den mot man hinh co that.")
	return 0


if __name__ == "__main__":
	sys.exit(chay())
