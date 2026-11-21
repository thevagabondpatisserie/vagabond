# -*- coding: utf-8 -*-
"""Sinh bốn tệp hoạ tiết vũ trụ cho app từ bản gốc của design system.

    python3 cong_cu/ui_b/sinh_hoa_tiet.py           ghi lại
    python3 cong_cu/ui_b/sinh_hoa_tiet.py --kiem    chỉ so, lệch trả mã 1

Bản gốc (bản vẽ của Gạo Muối) nằm ở cong_cu/ui_b/hoa_tiet/, chép NGUYÊN từng
byte từ design system "The Vagabond Pâtisserie", thư mục "Họa tiết vũ trụ";
mã băm SHA-256 ghi bên dưới để ai cũng đối chiếu lại được. Không vẽ lại,
không làm gần đúng.

Bản cho app (vagabond/public/images/ui/) chỉ khác bản gốc hai điều, đúng đặc
tả bản 4 mục 3:
  - đổi màu tô sang đen: app dùng hình làm mask rồi tô màu đậm của nhóm;
  - hình 14b bỏ đường elip mỏng nằm ngang, vì khi làm mask nó bị tô đặc thành vệt.
"""
import hashlib
import io
import os
import sys

O_DAY = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(os.path.dirname(O_DAY))
NGUON = os.path.join(O_DAY, "hoa_tiet")
DICH = os.path.join(GOC, "vagabond", "public", "images", "ui")

HINH = {
	"10c-elip-kinh-tuyen": "8752c3aa5c7b26aef007d8362df51d79017bb28cfee1b241be03b64a866fb0e1",
	"10d-qua-cau-luoi": "c139833d640b104383ad9bc60dc57978c83561bd3fad77b99df2bc66d0edd376",
	"14b-nguyen-tu": "bbfdf0a00d7a6a70a9254c2fd93351e993a15eb99dff50b3fc7e23eaff205181",
	"14f-quy-dao-elip-lech": "4d69455fbae05b334c6ba3e5839e91a69cf77e722ca5ac9ba39cd060a2345b4b",
}
# Đường elip nằm ngang của 14b: bắt đầu đúng bằng đoạn này.
ELIP_NGANG_14B = '    <path d="M5295.83,1073.34c'


def cho_app(ten, goc):
	s = goc.decode("utf-8")
	if s.count('fill="#273995"') != 1:
		raise ValueError("%s: không thấy đúng một màu tô gốc" % ten)
	s = s.replace('fill="#273995"', 'fill="#000"')
	if ten == "14b-nguyen-tu":
		dong = s.split("\n")
		con = [d for d in dong if not d.startswith(ELIP_NGANG_14B)]
		if len(con) != len(dong) - 1:
			raise ValueError("14b: không thấy đúng một đường elip nằm ngang để bỏ")
		s = "\n".join(con)
	return s + "\n"


def main(argv):
	kiem = "--kiem" in argv
	lech = 0
	if not kiem and not os.path.isdir(DICH):
		os.makedirs(DICH)
	for ten, bam in sorted(HINH.items()):
		goc = io.open(os.path.join(NGUON, ten + ".svg"), "rb").read()
		if hashlib.sha256(goc).hexdigest() != bam:
			print("LỆCH BẢN GỐC: %s không còn trùng mã băm của design system." % ten)
			lech += 1
			continue
		moi = cho_app(ten, goc)
		d = os.path.join(DICH, "hoa-tiet-%s.svg" % ten.split("-")[0])
		cu = io.open(d, encoding="utf-8").read() if os.path.exists(d) else None
		if cu == moi:
			continue
		if kiem:
			print("LỆCH: %s không khớp bản sinh từ bản gốc." % os.path.relpath(d, GOC))
			lech += 1
		else:
			io.open(d, "w", encoding="utf-8").write(moi)
			print("Đã ghi " + os.path.relpath(d, GOC))
	if kiem and not lech:
		print("Khớp: bốn hoạ tiết trùng bản gốc design system.")
	return 1 if lech else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
