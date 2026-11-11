"""v649: đơn còn phải giữ vỏ BTP (một nguồn cho bảng BTP, web, cửa nhận đơn).

Tách riêng, không chạm Frappe, để btp, kiem_banh, ton_don_web, giu_ton_web cùng
gọi mà không vòng import (btp nạp kiem_banh)."""


DON_GIU = ("da_dat", "phat_sinh", "cho_chot")
LAY_BANH_KHAC = ("huy", "don_khac", "giu_cho")


def _o_so(d, ten):
	v = d.get(ten) if hasattr(d, "get") else getattr(d, ten, 0)
	return int(v or 0)


def don_con_giu_vo(d, gom=DON_GIU):
	"""v649: số đơn (các cột `gom`) của MỘT dòng Kiểm bánh còn phải giữ vỏ BTP.

	Bếp nhập Bếp làm là máy trừ vỏ ngay (tru_vo_theo_sx), ở bảng hôm nay hay
	bảng ngày tới. Đơn đã có bánh làm xong thì không giữ vỏ lần nữa. Nhưng bánh
	làm xong trước hết bị huỷ, kênh khác, giữ chỗ (và các đơn không nằm trong
	`gom`) lấy, chỉ phần còn lại mới coi là bánh cho đơn (Codex #552 vòng 7).
	Bánh tồn ngày trước không tính ở đây (giữ cẩn thận như cũ). Đơn âm hay 0
	trả nguyên như cũ. Mọi chỗ trừ đơn vào BTP sẵn, Đủ decor gọi đúng hàm này.
	Thuần, đọc được cả dict lẫn dòng Frappe."""
	don = sum(_o_so(d, c) for c in gom)
	sx = max(0, _o_so(d, "sx"))
	if don <= 0 or not sx:
		return don
	khac = sum(max(0, _o_so(d, c)) for c in LAY_BANH_KHAC + tuple(c for c in DON_GIU if c not in gom))
	return max(0, don - max(0, sx - khac))
