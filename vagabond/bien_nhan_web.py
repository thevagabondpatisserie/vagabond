"""Dữ liệu thẻ ĐƠN HÀNG và NHẬN BÁNH của biên nhận đơn web mới (BẢN 2 mục 3, v684). THUẦN.

Mọi chữ, giá, lựa chọn lấy từ ảnh chụp đơn (snapshot) đã lưu lúc khách đặt:
Marketing đổi tên món hay giá sau này KHÔNG làm biên nhận cũ đổi theo.

Biên nhận mở được bằng đường dẫn (ai cầm link là xem được), nên vẫn GIẤU số
điện thoại và địa chỉ (anh Việt chốt 21/11/2026): chỉ có tên viết tắt và phường.
"""

MA_DIA = "BAPK00020"
MA_NIA = "BAPK00018"
MA_THIEP_EP_KIM = "BAPK00002"

TEN_THIEP = {"nho": "Thiệp nhỏ", "ep_kim": "Thiệp ép kim"}


def dinh_tien(so):
	try:
		so = int(round(float(so or 0)))
	except (TypeError, ValueError):
		so = 0
	return "{:,}".format(so).replace(",", ".") + " đ"


def _sl(m):
	try:
		return max(int(float((m or {}).get("sl") or 0)), 0)
	except (TypeError, ValueError):
		return 0


def _gia(m):
	try:
		return int(float((m or {}).get("gia") or 0))
	except (TypeError, ValueError):
		return 0


def dong_don(snap):
	"""Các dòng của thẻ ĐƠN HÀNG theo đúng thứ tự trong đơn.

	  banh : món có chiếc bánh (lời chúc, cờ, thiệp theo từng chiếc).
	  them : hàng mua thêm, mỗi món một dòng có giá.
	  tang : MỘT dòng gộp dĩa, nĩa tặng kèm ("Dĩa giấy bã mía x5, nĩa gỗ x5").
	Thiệp ép kim đã nằm trong từng chiếc nên không thành dòng riêng khi đơn có
	ghi từng chiếc; đơn cũ (không có khoá chiec) giữ dòng như cũ.
	"""
	snap = snap or {}
	chiec = snap.get("chiec")
	co_chiec = isinstance(chiec, list)
	theo_ma = {}
	for c in chiec or []:
		theo_ma.setdefault(str(c.get("ma") or ""), []).append(c)
	ra, tang = [], []
	for m in snap.get("mon") or []:
		ma = str(m.get("ma") or "")
		sl = _sl(m)
		if not ma or sl < 1:
			continue
		if ma in (MA_DIA, MA_NIA):
			tang.append(("dĩa giấy bã mía" if ma == MA_DIA else "nĩa gỗ", sl))
			continue
		gia = _gia(m)
		if ma in theo_ma:
			cs = theo_ma[ma]
			ten = cs[0].get("ten") or m.get("ten") or ma
			ra.append({"loai": "banh", "ma": ma, "ten": ten, "sl": sl, "gia": dinh_tien(gia * sl),
				"chiec": [_chiec(c) for c in cs]})
			continue
		if ma == MA_THIEP_EP_KIM and co_chiec:
			continue
		ra.append({"loai": "them", "ma": ma, "ten": m.get("ten") or ma, "sl": sl,
			"gia": dinh_tien(gia * sl) if gia else ""})
	if tang:
		chu = ", ".join("%s x%d" % (t, s) for t, s in tang)
		ra.append({"loai": "tang", "ten": chu[:1].upper() + chu[1:], "gia": "tặng kèm"})
	return ra


def _chiec(c):
	co = c.get("co") is not False
	loi_chuc = str(c.get("loi_chuc") or "").strip() if co else ""
	thiep = c.get("thiep") if c.get("thiep") in TEN_THIEP else ""
	return {
		"co": "Cờ: “%s”" % loi_chuc if co and loi_chuc else ("Cờ chưa ghi lời chúc" if co else "Không cờ"),
		"thiep": TEN_THIEP.get(thiep, "Không thiệp"),
		"loi_thiep": str(c.get("loi_thiep") or "").strip() if thiep else "",
	}


def nhan_banh(snap, viet_tat):
	"""Thẻ NHẬN BÁNH: cách nhận, nơi nhận (phường, không địa chỉ), người nhận (tên viết tắt).

	`viet_tat` là hàm rút gọn tên (don_web.viet_tat_ten), truyền vào để mô đun thuần.
	"""
	snap = snap or {}
	tu_lay = bool(snap.get("tu_lay"))
	nn = snap.get("nguoi_nhan") or None
	ten_nn = viet_tat((nn or {}).get("ho_ten")) if nn else ""
	return {
		"tu_lay": tu_lay,
		"noi": (snap.get("diem_lay_ten") or "Cửa hàng The Vagabond") if tu_lay else ((snap.get("phuong") or {}).get("ten") or ""),
		"nguoi_nhan": ten_nn or viet_tat((snap.get("nguoi_dat") or {}).get("ho_ten")),
		"la_nguoi_dat": not ten_nn,
	}
