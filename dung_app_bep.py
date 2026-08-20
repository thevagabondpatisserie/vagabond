#!/usr/bin/env python3
"""May ghep app_bep.js tu cac phan trong vagabond/public/js/bep/.

    python3 dung_app_bep.py           ghep lai va ghi de app_bep.js
    python3 dung_app_bep.py --kiem    chi kiem, KHONG ghi. Lech thi tra ma loi 1

Vi sao co tep nay (B1, anh Viet duyet 15/08/2026)
-------------------------------------------------
app_bep.js tung la mot tep 20.216 dong. Sua mot chu la day lai ca 1,2 MB, va
da ba lan mat ma vi hai phien lam viec ghi de len nhau. Nay nguon that nam o
cac tep nho trong bep/, con app_bep.js chi la ket qua may ghep.

Luat cua giai doan 1
--------------------
  1. Tep sinh ra phai GIONG HET tep cu toi tung byte. Khong them mot dong
     chu thich nao, khong doi mot dau cach nao. Noi cac phan lai la xong.
  2. Vi vay MOI phan deu la mot manh cua mot ham lon, khong phan nao chay
     mot minh duoc, va node --check tung phan se bao loi. Chi tep ghep lai
     moi doc duoc. Do la co y, khong phai thieu sot.
  3. KHONG sua tay vao app_bep.js. Sua trong bep/ roi chay lai may ghep.
     Cong kiem tra truoc deploy se bat duoc neu ai quen.

Thu tu ghep la thu tu ten tep. Tien to hai chu so giu dung thu tu do, va
thu tu la thu quan trong nhat o day: doi cho hai phan la doi thu tu khai
bao trong mot ham, co the lam vo app ma khong bao gi.
"""

import hashlib
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
THU_MUC = os.path.join(GOC, "vagabond", "public", "js", "bep")
DICH = os.path.join(GOC, "vagabond", "public", "js", "app_bep.js")

# Chi nhan dung dang 00-ten-khong-dau.js. Loc chat de mot tep sao luu bo
# quen trong thu muc khong lang le chui vao ban ghep.
MAU_TEN = re.compile(r"^\d\d-[a-z0-9-]+\.js$")

# Phan dong vo ham, luon phai la phan cuoi cung. Xem hang rao trong cac_phan().
TEP_DONG_VO = "99-dong-vo.js"


def cac_phan():
	"""Danh sach duong dan cac phan, da xep dung thu tu ghep."""
	if not os.path.isdir(THU_MUC):
		raise SystemExit("Khong thay thu muc %s" % THU_MUC)
	ten = sorted(t for t in os.listdir(THU_MUC) if MAU_TEN.match(t))
	if not ten:
		raise SystemExit("Thu muc %s khong co phan nao." % THU_MUC)
	so = [t[:2] for t in ten]
	if len(set(so)) != len(so):
		raise SystemExit("Co hai phan trung so thu tu: %s" % ", ".join(ten))
	# HANG RAO DONG VO. Ca app nam trong mot vo ham do 00-nen.js mo ra va
	# 99-dong-vo.js dong lai. Phan nao ghep SAU dong vo thi nam ngoai vo,
	# khong thay `frame` hay `api` nua, va man hinh cua no chet ngay khi bam.
	#
	# Toi 20/08/2026 chuyen do xay ra that: phan 24-phantom.js moi them bi
	# ghep sau 23-dong-vo.js cu. `node --check` van dat, ca bo kiem thu van
	# dat, chi bam that moi thay "frame is not defined". Nen phep kiem phai
	# nam o day, cho ngay TRUOC luc ghep.
	if ten[-1] != TEP_DONG_VO:
		raise SystemExit(
			"Phan cuoi cung phai la %s, dang la %s.\n"
			"Phan nao ghep sau phan dong vo thi nam ngoai vo ham va man hinh "
			"cua no se chet. Doi so thu tu cua phan moi xuong duoi 99."
			% (TEP_DONG_VO, ten[-1])
		)
	return [os.path.join(THU_MUC, t) for t in ten]


def ghep():
	"""Noi cac phan lai thanh byte. Khong them gi vao giua."""
	ra = b""
	for d in cac_phan():
		with open(d, "rb") as f:
			ra += f.read()
	return ra


def bam(b):
	return hashlib.sha256(b).hexdigest()


def main():
	kiem = "--kiem" in sys.argv
	moi = ghep()
	cu = b""
	if os.path.exists(DICH):
		with open(DICH, "rb") as f:
			cu = f.read()

	ds = cac_phan()
	if not kiem:
		print("Ghep %d phan:" % len(ds))
		for d in ds:
			n = os.path.getsize(d)
			print("   %-26s %7s byte" % (os.path.basename(d), "{:,}".format(n)))
		print("")

	print("   mã băm bản đang có : %s  (%s byte)" % (bam(cu), "{:,}".format(len(cu))))
	print("   mã băm bản ghép ra : %s  (%s byte)" % (bam(moi), "{:,}".format(len(moi))))

	if cu == moi:
		print("   KHỚP TUYỆT ĐỐI, không lệch một byte.")
		return 0

	if kiem:
		print("")
		print("   LỆCH. app_bep.js không khớp với các phần trong bep/.")
		print("   Hoặc ai đó sửa tay vào app_bep.js, hoặc sửa phần rồi quên ghép lại.")
		print("   Chạy: python3 dung_app_bep.py")
		# Chi ra dung cho lech dau tien, de khoi mo tay.
		n = min(len(cu), len(moi))
		i = next((k for k in range(n) if cu[k] != moi[k]), n)
		print("   Lệch từ byte thứ %s, tức khoảng dòng %s."
			% ("{:,}".format(i), "{:,}".format(cu[:i].count(b"\n") + 1)))
		return 1

	with open(DICH, "wb") as f:
		f.write(moi)
	print("   Đã ghi %s, %s byte." % (os.path.relpath(DICH, GOC), "{:,}".format(len(moi))))
	return 0


if __name__ == "__main__":
	sys.exit(main())
