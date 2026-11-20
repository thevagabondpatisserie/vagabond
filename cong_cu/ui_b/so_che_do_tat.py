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
import json
import os
import shutil
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def tham_so(ten, mac_dinh):
	return sys.argv[sys.argv.index(ten) + 1] if ten in sys.argv else mac_dinh


def ket_luan(ma_goc, ma_moi, ten_goc, ten_moi, mong, khac):
	"""Có được kết luận "không khác" hay không. THUẦN. Trả về danh sách lý do chặn; rỗng là đạt.

	Codex #599: máy chụp trả lỗi mà vẫn so số ảnh còn lại thì cổng xanh khi chưa chụp đủ màn.
	Phải đủ cả bốn điều: hai lượt chụp cùng trả 0; hai tập ảnh trùng tên nhau; đúng bằng tập
	ảnh mong đợi (màn x khung của máy chụp); không cặp nào khác.
	"""
	chan = []
	if ma_goc != 0:
		chan.append("lượt chụp bản gốc trả mã %s" % ma_goc)
	if ma_moi != 0:
		chan.append("lượt chụp bản đang làm trả mã %s" % ma_moi)
	ten_goc, ten_moi, mong = set(ten_goc), set(ten_moi), set(mong)
	if not mong:
		chan.append("không có ảnh mong đợi nào")
	if ten_goc != mong:
		chan.append("bản gốc thiếu %d ảnh, thừa %d ảnh so với tập mong đợi" % (len(mong - ten_goc), len(ten_goc - mong)))
	if ten_moi != mong:
		chan.append("bản đang làm thiếu %d ảnh, thừa %d ảnh so với tập mong đợi" % (len(mong - ten_moi), len(ten_moi - mong)))
	if khac:
		chan.append("%d ảnh khác nhau" % len(khac))
	return chan


def anh_mong_doi(bang):
	"""Tên ảnh máy chụp phải sinh ra, đọc từ ket-qua.json của chính lượt chụp. THUẦN."""
	return ["%s__%s__%s__%s.png" % (o["man"], o["che_do"], o["khung"], o["may"]) for o in bang]


def main():
	try:
		from PIL import Image, ImageChops
	except ImportError:
		print("THIẾU Pillow, chưa so được")
		return 2
	goc = tham_so("--goc", "origin/main")
	ra = tham_so("--ra", "/tmp/so-tat")
	# Thư mục đầu ra SẠCH: ảnh của lượt trước không được che một màn chụp hỏng.
	for ten in ("goc", "moi"):
		shutil.rmtree(os.path.join(ra, ten), ignore_errors=True)
	os.makedirs(ra, exist_ok=True)
	app_goc = os.path.join(ra, "app_bep_goc.js")
	with open(app_goc, "wb") as f:
		f.write(subprocess.check_output(["git", "show", goc + ":vagabond/public/js/app_bep.js"], cwd=GOC))
	sha = subprocess.check_output(["git", "rev-parse", "--short", goc], cwd=GOC).decode().strip()
	chup = os.path.join(GOC, "cong_cu", "ui_b", "chup.cjs")
	ma = {}
	mong = {}
	for ten, them in (("goc", ["--app", app_goc]), ("moi", [])):
		r = subprocess.run(["node", chup, "--ra", os.path.join(ra, ten), "--che-do", "tat"] + them, cwd=GOC, capture_output=True)
		ma[ten] = r.returncode
		if r.returncode == 2:
			print(r.stdout.decode("utf-8", "replace")[-300:])
			return 2
		if r.returncode != 0:
			print("Lượt chụp %s trả mã %d:\n%s" % (ten, r.returncode, r.stdout.decode("utf-8", "replace")[-1200:]))
		kq = os.path.join(ra, ten, "ket-qua.json")
		mong[ten] = anh_mong_doi(json.load(open(kq, encoding="utf-8"))["bang"]) if os.path.exists(kq) else []
	khac, tong = [], 0
	ten_anh = dict((t, [os.path.basename(f) for f in glob.glob(os.path.join(ra, t, "*.png"))]) for t in ("goc", "moi"))
	ds = sorted(os.path.join(ra, "moi", t) for t in set(ten_anh["moi"]) & set(ten_anh["goc"]))
	for f in ds:
		g = os.path.join(ra, "goc", os.path.basename(f))
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
	chan = ket_luan(ma["goc"], ma["moi"], ten_anh["goc"], ten_anh["moi"], mong["moi"], khac)
	if set(mong["goc"]) != set(mong["moi"]):
		chan.append("hai lượt chụp không cùng tập màn và khung")
	for c in chan:
		print("CHẶN  " + c)
	print("So chế độ tắt với %s (%s): %d ảnh mong đợi, %d cặp đã so, %d ảnh khác, %d điểm ảnh khác. %s" % (
		goc, sha, len(mong["moi"]), len(ds), len(khac), tong, "KHÔNG ĐẠT" if chan else "ĐẠT"))
	return 1 if chan else 0


if __name__ == "__main__":
	sys.exit(main())
