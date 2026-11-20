# -*- coding: utf-8 -*-
"""So chế độ TẮT của nhánh đang làm với bản gốc (mặc định origin/main), từng điểm ảnh.

    python3 cong_cu/ui_b/so_che_do_tat.py [--goc origin/main] [--ra /tmp/so-tat]

Cùng một máy, cùng trình duyệt, cùng dữ liệu thử, cùng giờ giả, cùng khung nhìn: chụp mọi
màn của máy chụp hai lần, một lần với app_bep.js của bản gốc, một lần với bản đang làm ở chế
độ tắt, rồi so. Trong MỘT môi trường cố định như vậy thì đòi 0 điểm ảnh khác (bản 4 mục 7).
Khác một điểm ảnh là phải giải thích, không tự nhận ảnh mới làm chuẩn.

Mã trả 0: không khác điểm ảnh nào; 1: có khác; 2: thiếu Playwright, trình duyệt hoặc Pillow.
"""
import glob
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def tham_so(ten, mac_dinh):
	return sys.argv[sys.argv.index(ten) + 1] if ten in sys.argv else mac_dinh


def main():
	try:
		from PIL import Image, ImageChops
	except ImportError:
		print("THIẾU Pillow, chưa so được")
		return 2
	goc = tham_so("--goc", "origin/main")
	ra = tham_so("--ra", "/tmp/so-tat")
	os.makedirs(ra, exist_ok=True)
	app_goc = os.path.join(ra, "app_bep_goc.js")
	with open(app_goc, "wb") as f:
		f.write(subprocess.check_output(["git", "show", goc + ":vagabond/public/js/app_bep.js"], cwd=GOC))
	sha = subprocess.check_output(["git", "rev-parse", "--short", goc], cwd=GOC).decode().strip()
	chup = os.path.join(GOC, "cong_cu", "ui_b", "chup.cjs")
	for ten, them in (("goc", ["--app", app_goc]), ("moi", [])):
		r = subprocess.run(["node", chup, "--ra", os.path.join(ra, ten), "--che-do", "tat"] + them, cwd=GOC, capture_output=True)
		if r.returncode == 2:
			print(r.stdout.decode("utf-8", "replace")[-300:])
			return 2
	khac, tong = [], 0
	ds = sorted(glob.glob(os.path.join(ra, "moi", "*.png")))
	for f in ds:
		g = os.path.join(ra, "goc", os.path.basename(f))
		if not os.path.exists(g):
			khac.append((os.path.basename(f), "bản gốc không có ảnh này"))
			continue
		a, b = Image.open(f).convert("RGB"), Image.open(g).convert("RGB")
		if a.size != b.size:
			khac.append((os.path.basename(f), "khác cỡ ảnh"))
			continue
		d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
		n = sum(d.histogram()[1:])
		tong += n
		if n:
			khac.append((os.path.basename(f), "%d điểm ảnh, vùng %s" % (n, d.getbbox())))
	for ten, ly_do in khac:
		print("KHÁC  %s: %s" % (ten, ly_do))
	print("So chế độ tắt với %s (%s): %d ảnh, %d ảnh khác, %d điểm ảnh khác." % (goc, sha, len(ds), len(khac), tong))
	return 1 if khac or not ds else 0


if __name__ == "__main__":
	sys.exit(main())
