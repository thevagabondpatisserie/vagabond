# -*- coding: utf-8 -*-
"""Khớp tiền chuyển khoản khi nội dung KHÔNG mang mã bill.

ANH VIỆT 31/08/2026, 23h
------------------------
*"Quá trời hoá đơn chuyển khoản bên điểm bán Quận 1 hôm nay sao cứ bị chờ
tiền về thế này? Hoá đơn chuyển khoản thì ngay lập tức đã có SePay đồng bộ
về để khớp trong vòng có mấy giây thôi mà."*

SỰ THẬT ĐÃ ĐO ĐƯỢC ĐÊM ĐÓ
-------------------------
SePay không hỏng: hôm đó về 90 giao dịch, đúng giờ đúng số. Cái hỏng là phép
khớp. Máy tìm mã bill bên trong nội dung chuyển khoản, mà quét cả tháng 8 thì
trong 2.914 giao dịch chỉ có 11 giao dịch thật sự mang mã bill.

Nội dung ngân hàng trả về có dạng:

    Q00033k5p6  VAGABOND1 1  QR   25622 5MQJ9- Ma GD ACSP/ XR703682

Đó là chuỗi do ngân hàng tự sinh, không phải nội dung mình đặt trong mã QR.
Nghĩa là đường khớp theo mã gần như CHƯA BAO GIỜ chạy cho bill quầy, không
phải hỏng hôm đó.

VÌ SAO KHÔNG GHI GÌ XUỐNG CƠ SỞ DỮ LIỆU
---------------------------------------
Phép trong tệp này chạy lúc ĐỌC màn hình, không lưu kết quả. Gạch nhầm một
giao dịch vào sai bill là sai doanh thu của cả hai bill, mà sai doanh thu thì
khó lần ra hơn nhiều so với để trống. Tính lại mỗi lần mở màn thì rẻ, luôn
đúng theo dữ liệu mới nhất, và sai thì tự hết khi dữ liệu đủ.

BA TẦNG CHẶT DẦN
----------------
1. CHỈ xét giao dịch cùng SỐ TIỀN, sai lệch không quá một đồng.
2. CHỈ xét giao dịch nằm trong KHUNG GIỜ quanh lúc chốt bill.
3. CHỈ nhận khi CHẮC CHẮN MỘT MỘT: đúng một giao dịch hợp lệ cho bill này,
   và giao dịch đó cũng chỉ hợp với đúng bill này. Hai bill cùng 230.000
   trong cùng khung giờ thì máy KHÔNG chọn bừa, trả về dạng đề xuất để người
   nhìn.

Tệp này THUẦN, không chạm Frappe.
"""

# Khung giờ quanh lúc chốt bill, tính bằng phút. Khách quét mã rồi mới bấm
# chuyển, hoặc thu ngân chốt bill sau khi tiền đã về, nên nới cả hai chiều.
CUA_SO_TRUOC = 45
CUA_SO_SAU = 20

# Sai lệch tiền cho phép, tính bằng đồng. Một đồng là để nuốt sai số làm tròn.
SAI_SO_TIEN = 1.0


def _so(v):
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0


def cung_tien(a, b, sai_so=SAI_SO_TIEN):
	"""Hai số tiền coi là một. THUẦN."""
	return abs(_so(a) - _so(b)) <= float(sai_so)


def trong_cua_so(phut_bill, phut_gd, truoc=CUA_SO_TRUOC, sau=CUA_SO_SAU):
	"""Giao dịch có nằm trong khung giờ quanh bill không. THUẦN.

	Tham số tính bằng SỐ PHÚT kể từ đầu ngày, để phép này thuần hoàn toàn,
	không phải nghĩ về múi giờ hay kiểu ngày tháng.
	"""
	try:
		d = float(phut_gd) - float(phut_bill)
	except (TypeError, ValueError):
		return False
	return -float(truoc) <= d <= float(sau)


def de_xuat(bills, giao_dich, truoc=CUA_SO_TRUOC, sau=CUA_SO_SAU):
	"""Ghép bill với giao dịch ngân hàng theo số tiền và khung giờ. THUẦN.

	bills       [{"ma", "tien", "phut"}]  các bill CHƯA khớp được theo mã
	giao_dich   [{"ten", "tien", "phut"}] các giao dịch CHƯA bị bill nào
	            khớp theo mã

	Trả {"chac": {ma_bill: giao_dich}, "phan_van": {ma_bill: [giao_dich...]}}

	`chac` là những cặp một một, màn hình được phép coi như đã về tiền.
	`phan_van` là chỗ có từ hai đường trở lên, để người nhìn và chọn.
	"""
	ung_vien = {}
	for b in bills or []:
		ma = str((b or {}).get("ma") or "").strip().upper()
		if not ma:
			continue
		hop = [
			g for g in (giao_dich or [])
			if cung_tien(b.get("tien"), (g or {}).get("tien"))
			and trong_cua_so(b.get("phut"), (g or {}).get("phut"), truoc, sau)
		]
		ung_vien[ma] = hop

	# Mot giao dich duoc bao nhieu bill nhan la cua minh.
	dem_gd = {}
	for ma, hop in ung_vien.items():
		for g in hop:
			t = str((g or {}).get("ten") or "")
			dem_gd[t] = dem_gd.get(t, 0) + 1

	chac, phan_van = {}, {}
	for ma, hop in ung_vien.items():
		if not hop:
			continue
		# Dung mot ung vien, VA ung vien do khong bi bill nao khac nhan.
		if len(hop) == 1 and dem_gd.get(str(hop[0].get("ten") or ""), 0) == 1:
			chac[ma] = hop[0]
		else:
			phan_van[ma] = hop
	return {"chac": chac, "phan_van": phan_van}
