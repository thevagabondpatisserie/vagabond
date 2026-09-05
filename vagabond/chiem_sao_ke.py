"""Một dòng sao kê chỉ được gạch cho MỘT chứng từ. THUẦN, không chạm Frappe.

Vì sao có tệp này
-----------------
Một dòng sao kê là MỘT lần tiền vào hoặc rời tài khoản. Cho hai chứng từ
cùng trỏ vào nó là khai hai lần cho một lần chuyển tiền: sổ sách cộng ra
nhiều hơn số tiền có thật trong ngân hàng.

Tầng đối soát dùng chung `doi_soat_sepay.py` (v295) đã có cơ chế chiếm dụng
cho hai luồng tiền RA. Nhưng hai luồng tiền VÀO lớn nhất của tiệm thì chưa
có gì cả:

  ban_hang._sepay_theo_ma_bill   bill quầy, dò mã VGBxxxxx
  cong_no._sepay_theo_ma_cn      phiếu công nợ, dò mã CN và DNTT

Ba đường một dòng sao kê bị gạch hai lần
----------------------------------------
1. HAI CHỨNG TỪ MANG CÙNG MỘT MÃ. Bảng kết quả gom theo MÃ chứ không theo
   chứng từ, nên hai hoá đơn cùng mã tham chiếu đều đọc ra cùng một số tiền,
   và cả hai đều qua được cửa "đã nhận đủ tiền chưa" rồi ghi sổ.

2. MỘT DÒNG SAO KÊ MANG HAI MÃ KHÁC NHAU. Khách trả hai bill trong một lần
   chuyển, nội dung ghi "VGBAAAAA VGBBBBBB". Vòng lặp cũ cộng TOÀN BỘ số tiền
   cho từng mã tìm thấy, nên mỗi bill đều tưởng mình đã được trả đủ.

3. MỘT DÒNG SAO KÊ MANG CÙNG MỘT MÃ HAI LẦN. Ngân hàng đôi khi vừa để mã
   trong nội dung vừa để trong ô tham chiếu. `findall` không gộp trùng nên
   số tiền bị cộng hai lần cho chính chứng từ đó.

Ba phép ở dưới bịt cả ba, và kiểm thử được mà không cần site.
"""

import re


def ma_trong_dong(mo_ta, ds_ma_muon, mau):
	"""Các mã KHÁC NHAU xuất hiện trong một dòng sao kê.

	  mo_ta       nội dung chuyển khoản, đã ghép cả ô tham chiếu
	  ds_ma_muon  các mã đang đi tìm; rỗng nghĩa là nhận mọi mã đúng mẫu
	  mau         biểu thức chính quy nhận dạng một mã

	Trả về danh sách đã sắp xếp và ĐÃ GỘP TRÙNG. Gộp trùng là điều số 3 ở
	trên: cùng một mã nằm hai chỗ trong một dòng vẫn chỉ là một lần trả tiền.
	"""
	chu = str(mo_ta or "").upper()
	if isinstance(mau, str):
		mau = re.compile(mau)
	hop = {str(m).strip().upper() for m in (ds_ma_muon or []) if str(m or "").strip()}
	thay = set()
	for m in mau.findall(chu):
		m = str(m).strip().upper()
		if not m:
			continue
		if hop and m not in hop:
			continue
		thay.add(m)
	return sorted(thay)


def dong_nhap_nhang(ds_ma):
	"""Dòng sao kê này có mang nhiều hơn một mã chứng từ không?

	Mang hai mã nghĩa là máy KHÔNG biết chia số tiền đó cho ai. Cộng đủ cho
	cả hai là nhân đôi tiền; chia đôi là đoán bừa. Đường đúng là để nguyên
	cho người nhìn rồi khớp tay.
	"""
	return len(ds_ma or []) > 1


def tach_gd(chuoi):
	"""Đọc danh sách mã giao dịch từ một ô văn bản. Bỏ trùng, giữ thứ tự."""
	ra = []
	for d in str(chuoi or "").replace(",", "\n").splitlines():
		d = d.strip()
		if d and d not in ra:
			ra.append(d)
	return ra


def gom_gd(ds):
	"""Ghép danh sách mã giao dịch thành một ô văn bản, mỗi mã một dòng."""
	ra = []
	for d in ds or []:
		d = str(d or "").strip()
		if d and d not in ra:
			ra.append(d)
	return "\n".join(ra)


def gd_dung_hai_lan(dang_giu, da_co_chu):
	"""Những mã giao dịch mà chứng từ này định giữ nhưng người khác giữ rồi.

	  dang_giu    danh sách mã giao dịch chứng từ này định ghi nhận
	  da_co_chu   dict {ma_giao_dich: mô tả người đang giữ}

	Trả về danh sách [(ma_giao_dich, chủ hiện tại)], sắp xếp để câu báo lỗi
	không đổi thứ tự giữa hai lần chạy.
	"""
	ra = []
	for m in tach_gd("\n".join(str(x or "") for x in (dang_giu or []))):
		chu = (da_co_chu or {}).get(m)
		if chu:
			ra.append((m, chu))
	return sorted(ra)


def cong_tien(dong, ds_ma_muon, mau):
	"""Cộng tiền theo mã, bỏ qua dòng nhập nhằng. Phép THUẦN của cả hai luồng.

	  dong  danh sách dict, mỗi dict là một dòng sao kê:
	        {"ten": mã dòng, "mo_ta": nội dung, "tien": số tiền}

	Trả về (theo_ma, bo_qua):
	  theo_ma  {mã: {"nhan": tiền, "so_gd": số dòng, "gd": [mã dòng]}}
	  bo_qua   danh sách dòng bị bỏ vì mang nhiều mã, để màn hình chỉ ra cho
	           người khớp tay chứ không im lặng nuốt mất
	"""
	theo_ma, bo_qua = {}, []
	hop = {str(m).strip().upper() for m in (ds_ma_muon or []) if str(m or "").strip()}
	for g in dong or []:
		# Phải thấy mọi mã TRƯỚC khi lọc. Màn chi tiết chỉ hỏi một bill;
		# lọc trước sẽ giấu mã thứ hai và gạch trọn tiền cho bill đang mở.
		ds = ma_trong_dong(g.get("mo_ta"), [], mau)
		if not ds or (hop and not hop.intersection(ds)):
			continue
		if dong_nhap_nhang(ds):
			bo_qua.append({"ten": g.get("ten"), "ma": ds, "tien": g.get("tien")})
			continue
		m = ds[0]
		o = theo_ma.setdefault(m, {"nhan": 0.0, "so_gd": 0, "gd": []})
		o["nhan"] += float(g.get("tien") or 0)
		o["so_gd"] += 1
		if g.get("ten") and g["ten"] not in o["gd"]:
			o["gd"].append(g["ten"])
	return theo_ma, bo_qua


# ------------------------------------------------- chon duong khop cho mot bill
#
# Anh Viet 27/08/2026, bill HDB-26-08-03877 cua don Pancake 92564: man hinh
# bao "ngan hang moi nhan 0 d tren tong 945.000 d" trong khi tien da ve tu
# 25/08. Man quay chi biet hoi MOT duong la ma bill quay VGBxxxxx, con bill
# do tra qua tai khoan ao MB do Pancake cap, khop bang mach S<shop>O<don>T.
#
# Nay hoi nhieu duong roi chon. Phep chon nam o day vi no THUAN, va vi cai
# can canh khong phai la cach doc co so du lieu ma la LUAT chon: du tien thi
# lay duong gach IT DONG SAO KE NHAT.
#
# Vi sao it dong nhat chu khong phai nhieu tien nhat: gach dung mot dong
# 945.000 cho bill 945.000 la sach. Gach ba dong cong lai thanh 1.200.000 de
# tra bill 945.000 la keo them hai dong cua nguoi khac vao, va nhung dong do
# se thieu khi bill kia can den.


def chon_duong_khop(cac_duong, can):
	"""THUAN: trong cac duong khop, chon duong DU TIEN va it dong nhat.

	`cac_duong` la danh sach cap (ten_duong, ket_qua), moi ket qua co khoa
	`nhan` va `gd`. Khong duong nao du thi tra duong NHIEU TIEN NHAT, de cau
	bao loi noi dung con thieu bao nhieu chu khong noi bang 0.
	"""
	def _so(x):
		try:
			return float(x or 0)
		except (TypeError, ValueError):
			return 0.0

	co = [(t, k) for t, k in (cac_duong or []) if k and _so(k.get("nhan"))]
	if not co:
		return "", {}
	nguong = _so(can) - 1
	du = [(t, k) for t, k in co if _so(k.get("nhan")) >= nguong]
	if du:
		return min(du, key=lambda x: (len(x[1].get("gd") or []), -_so(x[1].get("nhan"))))
	return max(co, key=lambda x: _so(x[1].get("nhan")))
