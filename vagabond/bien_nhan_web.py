"""Dữ liệu thẻ ĐƠN HÀNG và NHẬN BÁNH của biên nhận đơn web mới (BẢN 2 mục 3, v684). THUẦN.

Mọi chữ, giá, lựa chọn lấy từ ảnh chụp đơn (snapshot) đã lưu lúc khách đặt:
Marketing đổi tên món hay giá sau này KHÔNG làm biên nhận cũ đổi theo.

Mô đun chỉ trả GIÁ TRỊ đã lưu (có cờ không, mã thiệp, mã quà tặng), KHÔNG trả
câu chữ: chữ khách thấy ("Không cờ", "Thiệp nhỏ", "tặng kèm"...) do trang biên
nhận lấy từ bảng chữ Marketing sửa được (Codex #606).

Biên nhận mở được bằng đường dẫn (ai cầm link là xem được), nên vẫn GIẤU số
điện thoại và địa chỉ (anh Việt chốt 21/11/2026): chỉ có tên viết tắt và phường.
"""

MA_DIA = "BAPK00020"
MA_NIA = "BAPK00018"
MA_THIEP_EP_KIM = "BAPK00002"

MA_THIEP = ("nho", "ep_kim")


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
	  tang : MỘT dòng gộp dĩa, nĩa tặng kèm, dạng muc=[{"ma": "dia"|"nia", "sl"}];
	         trang biên nhận ghép chữ từ bảng chữ.
	Thiệp ép kim đã nằm trong từng chiếc nên không thành dòng riêng khi đơn có
	ghi từng chiếc VÀ thiệp miễn phí; thiệp có giá vẫn là một dòng có giá để các
	dòng cộng lại khớp tiền bánh. Đơn cũ (không có khoá chiec) giữ dòng như cũ.
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
		gia = _gia(m)
		# Dĩa, nĩa chỉ vào dòng tặng kèm khi miễn phí: có giá thì là một dòng có giá,
		# để các dòng cộng lại khớp tổng (Codex #606).
		if ma in (MA_DIA, MA_NIA) and not gia:
			tang.append({"ma": "dia" if ma == MA_DIA else "nia", "sl": sl})
			continue
		if ma in theo_ma:
			cs = theo_ma[ma]
			ten = cs[0].get("ten") or m.get("ten") or ma
			ra.append({"loai": "banh", "ma": ma, "ten": ten, "sl": sl, "gia": dinh_tien(gia * sl),
				"chiec": [_chiec(c) for c in cs]})
			continue
		# Thiệp ép kim đã ghi trong từng chiếc: miễn phí thì không thành dòng riêng;
		# có giá thì vẫn là dòng có giá, không để tiền thiệp biến mất khỏi biên nhận
		# (Codex #606: bánh 450.000 đ + thiệp 15.000 đ phải thấy đủ 465.000 đ).
		if ma == MA_THIEP_EP_KIM and co_chiec and not gia:
			continue
		ra.append({"loai": "them", "ma": ma, "ten": m.get("ten") or ma, "sl": sl,
			"gia": dinh_tien(gia * sl) if gia else ""})
	if tang:
		ra.append({"loai": "tang", "muc": tang})
	return ra


def _chiec(c):
	co = c.get("co") is not False
	loi_chuc = str(c.get("loi_chuc") or "").strip() if co else ""
	thiep = c.get("thiep") if c.get("thiep") in MA_THIEP else ""
	return {
		"co": co,
		"loi_chuc": loi_chuc,
		"thiep": thiep,
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
		"noi": (snap.get("diem_lay_ten") or "") if tu_lay else ((snap.get("phuong") or {}).get("ten") or ""),
		"nguoi_nhan": ten_nn or viet_tat((snap.get("nguoi_dat") or {}).get("ho_ten")),
		"la_nguoi_dat": not ten_nn,
	}
