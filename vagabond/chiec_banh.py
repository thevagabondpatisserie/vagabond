"""v681 (BẢN 2 mục 2.0, 2.1, 2.5, anh Việt duyệt 21/11/2026): lời chúc, cờ, thiệp
theo TỪNG CHIẾC bánh và ghi chú chọn nhanh của đơn web. THUẦN, không chạm Frappe.

Pancake gộp các dòng cùng mã món (đơn chỉ có "BAWC00139 x2"), nên nội dung của
từng chiếc không nằm được ở dòng món. Nó đi ba đường:
  - ghi chú in (note_print): mỗi chiếc một dòng, trang khách dựng, bếp và vận
    đơn đọc như cũ;
  - bản ghi Vagabond Don Web (ảnh chụp lúc đặt, khoá "chiec"): biên nhận và
    đối soát đọc lại, không phụ thuộc Pancake;
  - dòng thiệp ép kim BAPK00002: số lượng do máy chủ CHỐT bằng đúng số chiếc
    chọn ép kim, không tin số trình duyệt gửi.
"""

MA_THIEP_EP_KIM = "BAPK00002"
LOAI_THIEP = ("khong", "nho", "ep_kim")
LOI_CHUC_TOI_DA = 60
LOI_THIEP_TOI_DA = 80
SO_CHIEC_TOI_DA = 200

# Mã cố định của các viên Ghi chú chọn nhanh (trùng GHI_CHU_NHANH ở
# web_vue/banh/du-lieu.js; ca thu_chiec_banh_681 chốt hai bên khớp).
MA_GHI_CHU_NHANH = ("goi_truoc", "gui_le_tan", "chup_hinh", "gio_tre_nhat", "di_ung")
MA_GHI_CHU_GIAO = ("goi_truoc", "gui_le_tan", "chup_hinh", "gio_tre_nhat")


def _chu(v, toi_da):
	return " ".join(str(v or "").split())[:toi_da]


def chuan_chiec(ds, hang):
	"""Danh sách chiếc hợp lệ theo giỏ đã làm sạch.

	ds: danh sách trình duyệt gửi ({ma, co, loi_chuc, thiep, loi_thiep}).
	hang: giỏ đã làm sạch [{"variation_id", "quantity"}].
	Mỗi mã chỉ giữ tối đa đúng số lượng của mã đó trong giỏ; chiếc của mã không
	có trong giỏ bị bỏ. Trả None khi trình duyệt không gửi khoá chiec (trang cũ
	còn mở trong máy khách): khi đó không đụng tới giỏ."""
	if ds is None:
		return None
	if not isinstance(ds, list):
		return []
	con = {}
	for h in hang or []:
		con[h["variation_id"]] = con.get(h["variation_id"], 0) + int(h.get("quantity") or 0)
	ra = []
	for x in ds[:SO_CHIEC_TOI_DA]:
		if not isinstance(x, dict):
			continue
		ma = str(x.get("ma") or "").strip()
		if ma == MA_THIEP_EP_KIM or con.get(ma, 0) < 1:
			continue
		con[ma] -= 1
		co = x.get("co") is not False
		thiep = x.get("thiep") if x.get("thiep") in LOAI_THIEP else "khong"
		ra.append({
			"ma": ma,
			"co": co,
			"loi_chuc": _chu(x.get("loi_chuc"), LOI_CHUC_TOI_DA) if co else "",
			"thiep": thiep,
			"loi_thiep": _chu(x.get("loi_thiep"), LOI_THIEP_TOI_DA) if thiep != "khong" else "",
			# Tên như trên web lúc đặt ("Epi · Ø 12cm"), chỉ để hiện lại ở biên nhận.
			"ten_web": _chu(x.get("ten"), 120),
		})
	return ra


def so_ep_kim(chiec):
	return sum(1 for c in chiec or [] if c.get("thiep") == "ep_kim")


def so_thiep_nho(chiec):
	return sum(1 for c in chiec or [] if c.get("thiep") == "nho")


def chot_thiep_ep_kim(hang, chiec):
	"""Giỏ với dòng BAPK00002 bằng ĐÚNG số chiếc chọn ép kim (tính lại từ đầu).

	chiec None (trang cũ): giữ nguyên giỏ. Không chiếc nào ép kim: bỏ dòng."""
	if chiec is None:
		return [dict(h) for h in hang]
	n = so_ep_kim(chiec)
	ra = [dict(h) for h in hang if h["variation_id"] != MA_THIEP_EP_KIM]
	if n:
		ra.append({"variation_id": MA_THIEP_EP_KIM, "quantity": n})
	return ra


def chuan_ghi_chu_nhanh(ds, tu_lay):
	"""Mã viên ghi chú hợp lệ, đúng thứ tự cố định, bỏ viên giao hàng khi Tự lấy."""
	if not isinstance(ds, list):
		return []
	co = {str(x) for x in ds}
	return [m for m in MA_GHI_CHU_NHANH if m in co and not (tu_lay and m in MA_GHI_CHU_GIAO)]


def chuan_gio_tre(v, ma):
	"""Giờ trễ nhất "HH:MM" khi khách chọn viên gio_tre_nhat, ngược lại chuỗi rỗng."""
	if "gio_tre_nhat" not in (ma or []):
		return ""
	s = str(v or "").strip()
	if len(s) == 5 and s[2] == ":" and s[:2].isdigit() and s[3:].isdigit() and int(s[:2]) < 24 and int(s[3:]) < 60:
		return s
	return ""


def anh_chup_chiec(chiec, ten_mon):
	"""Chiếc kèm tên món lúc đặt, để biên nhận cũ không đổi theo tên mới."""
	return [dict(c, ten=c.get("ten_web") or (ten_mon or {}).get(c["ma"]) or c["ma"]) for c in chiec or []]
