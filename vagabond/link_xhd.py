"""#227: link gửi sau lúc bán phải có hạn riêng, ký cả bill lẫn hạn.

QR cũ giữ nguyên giao kèo 2 giờ từ lúc tạo bill. Link mới không dùng lại
mã cũ đã hết hạn, cũng không cho đổi mã bill hoặc kéo dài hạn trên URL.
"""

import hashlib
import hmac


def ky_link(ten, han, bi_mat):
	return hmac.new(str(bi_mat).encode(),
		("vgb-xhd-link|%s|%s" % (ten, han)).encode(), hashlib.sha256).hexdigest()


def link_hop_le(ten, han, chu_ky, bi_mat, bay_gio):
	han = str(han or "")
	chu_ky = str(chu_ky or "")
	if not han.isascii() or not han.isdigit() or len(han) > 12 or not chu_ky.isascii():
		return False
	con = int(han) - int(bay_gio)
	return 0 < con <= 7200 and hmac.compare_digest(
		chu_ky, ky_link(ten, han, bi_mat))
