"""Đổi họ màu teal cũ (#29BDB3) của web sang Robin egg #4FDBF2 (v662).

Anh Việt duyệt 15/11/2026: teal dùng từ ngày đầu là sai màu thương hiệu, màu
đúng là Robin egg của design system "The Vagabond Pâtisserie". Quy tắc:
- Ánh xạ cố định cho các màu chính (bảng CO_DINH).
- Màu xanh cùng họ khác (hue 150 tới 200 độ, độ bão hoà trên 15%): hue cộng
  12.5 độ (tối đa 200); L >= 20% thì L x1.4 (tối đa 85%), S x1.34 (tối đa
  100%); L < 20% thì giữ L, S x1.2.
- Chữ trên nền xanh #00201D đổi sang Ink #1A1A1A (CSS dùng biến --ink-on-cyan).
Chạy: python3 cong_cu/doi_mau_robin_662.py <tệp>... (ghi đè tại chỗ, in số chỗ đổi).
"""
import colorsys
import re
import sys

CO_DINH = {
	"29bdb3": "4FDBF2", "3fd8cd": "8EEAF8", "1b6f69": "129AAF", "2abfb3": "54DEF2",
}
CO_DINH_RGB = {(41, 189, 179): (79, 219, 242), (63, 216, 205): (142, 234, 248)}
INK_CU = ("00201d",)
INK = "1A1A1A"


def doi_hsl(r, g, b):
	"""(r,g,b) 0-255 -> (r,g,b) mới hoặc None nếu không thuộc họ teal. THUẦN."""
	h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
	hd = h * 360
	# Spec 150 tới 200 độ, nhưng: dưới 160 là xanh lá báo thành công (#3ECF8E,
	# #05603A) chứ không phải teal; trên 186 là màu Robin egg đã đổi sẵn
	# (#4FDBF2, #50DBF2) mà đổi lần nữa là lệch. Hai dải đó giữ nguyên.
	if not (160 <= hd <= 186 and s > 0.15):
		return None
	hd = min(hd + 12.5, 200)
	if l >= 0.20:
		l, s = min(l * 1.4, 0.85), min(s * 1.34, 1.0)
	else:
		s = min(s * 1.2, 1.0)
	rr, gg, bb = colorsys.hls_to_rgb(hd / 360.0, l, s)
	return tuple(int(round(x * 255)) for x in (rr, gg, bb))


def doi_hex(hx):
	"""'29bdb3' -> chuỗi hex mới (chữ hoa) hoặc None. Nhận 3 hoặc 6 ký tự. THUẦN."""
	k = hx.lower()
	if len(k) == 3:
		k = "".join(c * 2 for c in k)
	if k in CO_DINH:
		return CO_DINH[k]
	if k in INK_CU:
		return INK
	r, g, b = int(k[0:2], 16), int(k[2:4], 16), int(k[4:6], 16)
	m = doi_hsl(r, g, b)
	return None if m is None else "%02X%02X%02X" % m


# Chỉ mã 6 ký tự: "#367", "#489" trong chú thích là số issue, không phải màu.
MAU_HEX = re.compile(r"(?<![&\w])#([0-9a-fA-F]{6})(?![0-9a-fA-F])")
MAU_RGB = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(,\s*[\d.]+\s*)?\)")


def doi_chu(s, la_css=False):
	"""Đổi mọi màu trong một chuỗi; trả (chuỗi mới, số chỗ đổi). THUẦN."""
	dem = [0]

	def _hex(m):
		k = m.group(1)
		if la_css and k.lower() in INK_CU:
			dem[0] += 1
			return "var(--ink-on-cyan,#1A1A1A)"
		moi = doi_hex(k)
		if moi is None or moi.lower() == (k.lower() if len(k) == 6 else "".join(c * 2 for c in k.lower())):
			return m.group(0)
		dem[0] += 1
		return "#" + moi

	def _rgb(m):
		r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
		a = m.group(4)
		moi = CO_DINH_RGB.get((r, g, b))
		if moi is None:
			if (r, g, b) == (0, 32, 29):
				moi = (26, 26, 26)
			else:
				moi = doi_hsl(r, g, b)
		if moi is None or moi == (r, g, b):
			return m.group(0)
		dem[0] += 1
		if a:
			return "rgba(%d,%d,%d%s)" % (moi[0], moi[1], moi[2], a.replace(" ", ""))
		return "rgb(%d,%d,%d)" % moi

	# Không đụng tham chiếu var(--x,#hex) của biến khác? Có: giá trị dự phòng cũng là màu cũ, đổi luôn.
	s2 = MAU_HEX.sub(_hex, s)
	s2 = MAU_RGB.sub(_rgb, s2)
	return s2, dem[0]


def main(tep):
	tong = 0
	for p in tep:
		with open(p, encoding="utf-8") as f:
			s = f.read()
		moi, n = doi_chu(s, la_css=p.endswith(".css"))
		if n:
			with open(p, "w", encoding="utf-8") as f:
				f.write(moi)
		print("%5d  %s" % (n, p))
		tong += n
	print("%5d  tổng" % tong)


if __name__ == "__main__":
	main(sys.argv[1:])
