"""Dat so phien ban cho mot dot deploy. Chay MOT lenh, khong sot buoc nao.

    python3 dat_phien_ban.py 181

Ba viec no lam, va vi sao phai la mot lenh chu khong phai ba thao tac tay:

1. Doi APPVER trong vagabond/public/js/bep/12-van-don.js.
   Quen buoc nay thi trinh duyet cua nhan vien giu ban cu trong bo nho dem,
   va ho bao "em deploy roi ma may chi khong thay gi".

2. Dong so phien ban vao cuoi dong patch trong vagabond/patches.txt.
   Day la buoc EP FRAPPE CLOUD CHAY MIGRATE. Frappe Cloud chon giua "Pull"
   (5 giay, khong migrate) va "Migrate" (47 giay) bang cach nhin danh sach
   tep da doi; patches.txt nam trong danh sach ep Migrate. Dong so phien
   ban vao thi dong patch khac di sau moi dot, nen lan nao cung Migrate.

   Truoc khi co tep nay, dot v177 va v179 deu chi sua .py va .js nen Frappe
   Cloud chon "Pull", after_migrate khong chay, va man Bao gia chet vi
   thieu cot. Anh Viet phai bam Migrate tay moi lan.

3. Dung lai vagabond/public/js/app_bep.js tu 24 phan trong bep/.
   Vi buoc 1 vua sua mot trong 24 phan do.

Sau khi chay xong van phai qua `sh kiem_truoc_deploy.sh` roi moi duoc day.
"""

import re
import subprocess
import sys

TEP_VER = "vagabond/public/js/bep/12-van-don.js"
TEP_PATCH = "vagabond/patches.txt"
DONG_PATCH = "vagabond.patches.dong_bo_cau_truc"


def doc_ver_dang_co():
	s = open(TEP_VER, encoding="utf-8").read()
	m = re.search(r"APPVER\s*=\s*'(\d+)'", s)
	return m.group(1) if m else None


def dat_appver(moi):
	s = open(TEP_VER, encoding="utf-8").read()
	moi_s, n = re.subn(r"(APPVER\s*=\s*')(\d+)(')", r"\g<1>%s\g<3>" % moi, s)
	if n != 1:
		print("HONG: tim thay %d cho khai APPVER trong %s, mong dung 1." % (n, TEP_VER))
		sys.exit(1)
	open(TEP_VER, "w", encoding="utf-8").write(moi_s)
	return True


def dat_patch(moi):
	"""Ghi dong patch mang so phien ban. Giu nguyen moi dong patch cu.

	Frappe nho patch da chay theo NGUYEN VAN ca dong, ke ca phan ghi chu sau
	dau thang. Nen "...dong_bo_cau_truc #v181" va "#v182" la hai dong khac
	nhau, deu duoc chay, va deu lap lai duoc.
	"""
	dong = open(TEP_PATCH, encoding="utf-8").read().splitlines()
	moi_dong = "%s #v%s" % (DONG_PATCH, moi)
	if moi_dong in dong:
		print("      dong patch cho v%s da co, khong them lai." % moi)
		return False
	# Bo cac dong dong_bo_cau_truc cua phien ban CU di, giu lai dung mot
	# dong moi nhat: giu het thi moi lan migrate lai chay lai ca chuc lan
	# cung mot viec, cham ma khong duoc gi.
	giu = [d for d in dong if not d.startswith(DONG_PATCH + " #v")]
	# Chen vao cuoi muc post_model_sync.
	if "[post_model_sync]" not in giu:
		giu.append("[post_model_sync]")
	giu.append(moi_dong)
	open(TEP_PATCH, "w", encoding="utf-8").write("\n".join(giu) + "\n")
	return True


def main():
	if len(sys.argv) != 2 or not sys.argv[1].isdigit():
		cu = doc_ver_dang_co()
		print(__doc__)
		print("Phien ban dang co: %s" % (cu or "khong doc duoc"))
		sys.exit(1)
	moi = sys.argv[1]
	cu = doc_ver_dang_co()
	if cu == moi:
		print("APPVER da la %s roi." % moi)
	else:
		dat_appver(moi)
		print("[1/3] APPVER: %s -> %s" % (cu, moi))
	if dat_patch(moi):
		print("[2/3] patches.txt: them \"%s #v%s\" - Frappe Cloud se chay Migrate." % (DONG_PATCH, moi))
	else:
		print("[2/3] patches.txt: khong doi.")
	print("[3/3] Dung lai app_bep.js...")
	r = subprocess.run([sys.executable, "dung_app_bep.py"], capture_output=True, text=True)
	print("      " + (r.stdout.strip().splitlines() or ["(khong co ket qua)"])[-1])
	if r.returncode != 0:
		print(r.stderr[-1500:])
		sys.exit(1)
	print("\nXong. Buoc tiep theo: sh kiem_truoc_deploy.sh")


if __name__ == "__main__":
	main()
