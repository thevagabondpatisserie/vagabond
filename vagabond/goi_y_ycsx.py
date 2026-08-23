"""Goi y mon can lam YCSX cho bep, gom ba nguon ve mot cho.

Vi sao co tep nay
-----------------
Anh Viet 23/08/2026, nhin man Loan Anh lap phieu YCSX: *"khong thay co goi y
so tu he thong gi ca"*. Dung vay - buoc "Chon hang hoa" cua man tao phieu chi
la danh sach Item tron, sales phai tu nho hom nay thieu banh gi, thieu bao
nhieu, roi go tay tung con so. Ba nguon so dang nam san trong he ma khong ai
noi chung lai:

  1. Kiem banh THEO NGAY  - cot "Da dat" cua ngay ke tiep.
  2. Kiem banh THEO MUA   - so banh trung thu khach da dat trong khoang mua.
  3. HOP DONG da len voi khach - catering, event, teabreak. Cho nay co cai
     hai nguon kia khong co: mon KHONG CO MA hang hoa.

Phep tinh
---------
Ca hai bang kiem banh deu da co san cot CO THE BAN, chinh la:

    ton + bep da len - da dat - phat sinh - cho chot - kenh khac

Cot do AM bao nhieu thi thieu bay nhieu. Nen phep goi y o day khong phat
minh cong thuc moi, chi doi dau con so da co:

    can lam = -co_the_ban   (khi co_the_ban < 0)

Lam vay co mot cai loi lon: bep da len bao nhieu thi tru bay nhieu, nen bam
goi y hai lan trong mot ngay khong ra so gap doi.

Ba nguon gop lai THEO MA HANG chu khong de rieng ba danh sach. Mot ma nam o
ca hai nguon thi cong so lai va giu nguyen ca hai dong giai thich, de Loan Anh
nhin ra so tu dau ma co. De rieng ba danh sach thi cung ma xuat hien hai lan,
tich ca hai la sinh hai dong trong mot phieu - Frappe khong chan, bep lam gap
doi.

MON KHONG CO MA thi tach han ra mot muc rieng: mot dong Material Request BAT
BUOC co item_code, khong the tao dong cho "Set teabreak 30 khach" duoc. Nen
danh sach do chi de ĐỌC, kem ten hop dong va ngay su kien, de Loan Anh biet
duong ma mo ma hang hoac ghi vao ghi chu phieu.
"""

import frappe
from frappe.utils import cint, flt, getdate

# Trang thai hop dong CHUA chac chan nhung van dang song. Van goi y, nhung
# gan co chac_chan = 0 de man hinh xep xuong duoi va noi ro cho Loan Anh.
HD_CHAC_CHAN = ("Đang thực hiện",)
HD_CON_SONG = ("Đã gửi khách", "Đang thương thảo", "Đang thực hiện")

# Su kien thuong phai lam truoc vai ngay. Lay rong ra sau ngay ke ngay can,
# de phieu lap hom nay con kip don su kien cuoi tuan.
SO_NGAY_HOP_DONG = 3


# --------------------------------------------------------------- phep thuan


def thieu_tu_o(co_the_ban):
	"""Mot o CO THE BAN am bao nhieu thi thieu bay nhieu. THUAN.

	Duong hoac bang 0 la du hang, tra ve 0 chu khong tra ve so am.
	"""
	so = cint(co_the_ban)
	return -so if so < 0 else 0


def giai_thich_ngay(d):
	"""Cau giai thich so cho mot dong bang kiem banh theo NGAY. THUAN."""
	cau = "Đã đặt %d" % cint(d.get("da_dat"))
	if cint(d.get("phat_sinh")):
		cau += ", phát sinh %d" % cint(d.get("phat_sinh"))
	if cint(d.get("cho_chot")):
		cau += ", chờ chốt %d" % cint(d.get("cho_chot"))
	if cint(d.get("don_khac")):
		cau += ", kênh khác %d" % cint(d.get("don_khac"))
	ton = cint(d.get("ton_cu")) + cint(d.get("ton_d2")) + cint(d.get("ton_d1"))
	if ton:
		cau += ", trừ tồn %d" % ton
	if cint(d.get("sx")):
		cau += ", trừ bếp đã lên %d" % cint(d.get("sx"))
	return cau


def giai_thich_mua(d):
	"""Cau giai thich so cho mot dong bang kiem banh theo MUA. THUAN."""
	cau = "Đã đặt %d" % cint(d.get("da_dat"))
	if cint(d.get("phat_sinh")):
		cau += ", phát sinh %d" % cint(d.get("phat_sinh"))
	if cint(d.get("cho_chot")):
		cau += ", chờ chốt %d" % cint(d.get("cho_chot"))
	if cint(d.get("don_khac")):
		cau += ", kênh khác %d" % cint(d.get("don_khac"))
	if cint(d.get("ton_dau")):
		cau += ", trừ tồn đầu %d" % cint(d.get("ton_dau"))
	if cint(d.get("bep_lam")):
		cau += ", trừ bếp đã lên %d" % cint(d.get("bep_lam"))
	return cau


def gop_theo_ma(cac_dong):
	"""Gop cac dong goi y CUNG MA HANG lam mot, cong so va giu het nguon. THUAN.

	cac_dong: list dict co ma_hang, ten_banh, hinh, can, nguon (mot dict).

	Tra ve list moi, xep theo so can giam dan roi den ten cho de doc. Khong
	sua cac dong dau vao.

	Vi sao KHONG de rieng ba danh sach: cung mot ma nam o hai nguon, tich ca
	hai la sinh hai dong trong mot Material Request. Frappe nhan ca hai dong
	do khong bao gi, bep doc phieu thay hai dong cung ten roi lam gap doi.
	"""
	ban = {}
	thu_tu = []
	for d in cac_dong or []:
		ma = str((d or {}).get("ma_hang") or "").strip()
		if not ma:
			continue
		if ma not in ban:
			ban[ma] = {
				"ma_hang": ma,
				"ten_banh": d.get("ten_banh") or ma,
				"hinh": d.get("hinh") or "",
				"can": 0,
				"nguon": [],
			}
			thu_tu.append(ma)
		o = ban[ma]
		o["can"] += cint(d.get("can"))
		if d.get("nguon"):
			o["nguon"].append(d["nguon"])
		# Ten va hinh: giu cai dau tien co that, dung de nguon sau ghi de
		# bang chuoi rong.
		if not o["hinh"] and d.get("hinh"):
			o["hinh"] = d["hinh"]
	ra = [ban[m] for m in thu_tu]
	ra.sort(key=lambda x: (-x["can"], x["ten_banh"]))
	return ra


def tach_dong_bao_gia(dong, chi_mon=True):
	"""Chia dong bao gia thanh (co ma, khong ma). THUAN.

	dong: list dict kieu Bao Gia Dong (loai, ma_mon, ten_mon, so_luong, dvt).

	Dong "Phi" (phi giao, phi setup) khong phai mon an, khong bao gio la
	YCSX, nen bi loai han chu khong roi vao muc khong ma.
	"""
	co, khong = [], []
	for d in dong or []:
		d = d or {}
		if chi_mon and str(d.get("loai") or "Món").strip() == "Phí":
			continue
		sl = cint(round(flt(d.get("so_luong"))))
		ten = str(d.get("ten_mon") or "").strip()
		ma = str(d.get("ma_mon") or "").strip()
		if ma:
			co.append({"ma_mon": ma, "ten_mon": ten, "so_luong": sl, "dvt": d.get("dvt") or ""})
		elif ten:
			khong.append({"ten_mon": ten, "so_luong": sl, "dvt": d.get("dvt") or ""})
	return co, khong


# ---------------------------------------------------------- phan cham he


def _tu_kiem_banh_ngay(ngay):
	"""Nguon 1: bang kiem banh theo NGAY cua dung ngay can hang."""
	from vagabond import kiem_banh

	try:
		bang = kiem_banh.bang(str(ngay))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_y_ycsx kiem banh ngay")
		return [], "Không đọc được bảng kiểm bánh theo ngày %s" % ngay
	if not cint(bang.get("co_so")):
		return [], "Ngày %s chưa có bảng kiểm bánh, chưa có số đã đặt để gợi ý" % ngay
	ra = []
	for d in bang.get("dong") or []:
		can = thieu_tu_o(d.get("co_the_ban"))
		if can <= 0:
			continue
		ra.append({
			"ma_hang": d.get("ma_hang"),
			"ten_banh": d.get("ten_banh") or d.get("ma_hang"),
			"hinh": d.get("hinh") or "",
			"can": can,
			"nguon": {
				"ma": "ngay",
				"nhan": "Kiểm bánh ngày %s" % _dmy(ngay),
				"so": can,
				"giai_thich": giai_thich_ngay(d),
			},
		})
	return ra, ""


def _mua_dang_chay(ngay):
	"""Cac mua vu dang ban co khoang phu ngay can hang."""
	from vagabond.mua_vu import DT, TT_DANG_BAN

	return frappe.get_all(
		DT,
		filters={
			"tinh_trang": TT_DANG_BAN,
			"tu_ngay": ["<=", ngay],
			"den_ngay": [">=", ngay],
		},
		fields=["name", "ten_mua"],
		limit_page_length=20,
	)


def _tu_mua_vu(ngay):
	"""Nguon 2: bang kiem banh theo MUA, moi mua dang chay mot lan."""
	from vagabond import mua_vu

	ra, ghi_chu = [], []
	for m in _mua_dang_chay(ngay):
		try:
			bang = mua_vu.bang_ngay(m["name"], str(ngay))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "goi_y_ycsx mua vu")
			ghi_chu.append("Không đọc được mùa %s" % (m.get("ten_mua") or m["name"]))
			continue
		if not cint(bang.get("co_so")):
			continue
		for d in bang.get("dong") or []:
			can = thieu_tu_o(d.get("co_the_ban"))
			if can <= 0:
				continue
			gt = giai_thich_mua(d)
			# Hop ma ruot dang chan thi noi ra, vi lam them vo hop khong go
			# duoc nut that: ruot moi la cho tac.
			if cint(d.get("la_hop")) and not cint(d.get("ruot_khong_rang_buoc")):
				gt += ". Hộp này ruột chỉ ghép được %d" % cint(d.get("ghep_duoc"))
			ra.append({
				"ma_hang": d.get("ma_hang"),
				"ten_banh": d.get("ten_banh") or d.get("ma_hang"),
				"hinh": d.get("hinh") or "",
				"can": can,
				"nguon": {
					"ma": "mua",
					"nhan": "Mùa %s" % (m.get("ten_mua") or m["name"]),
					"so": can,
					"giai_thich": gt,
				},
			})
	return ra, ghi_chu


def _hop_dong_trong_khoang(ngay):
	"""Hop dong con song co ngay su kien roi vao khoang can chuan bi."""
	from frappe.utils import add_days

	return frappe.get_all(
		"Hop Dong Ban Hang",
		filters={
			"trang_thai": ["in", HD_CON_SONG],
			"ngay_su_kien": ["between", [str(ngay), str(add_days(ngay, SO_NGAY_HOP_DONG))]],
		},
		fields=["name", "ten", "so_hop_dong", "loai", "trang_thai", "ngay_su_kien", "bao_gia"],
		order_by="ngay_su_kien asc",
		limit_page_length=50,
	)


def _tu_hop_dong(ngay):
	"""Nguon 3: hop dong da len voi khach. Tra (co ma, khong ma, ghi chu)."""
	co_ma, khong_ma, ghi_chu = [], [], []
	for hd in _hop_dong_trong_khoang(ngay):
		nhan = "HĐ %s %s" % (hd.get("so_hop_dong") or hd["name"], hd.get("ten") or "")
		nhan = nhan.strip()
		if not hd.get("bao_gia"):
			ghi_chu.append("%s chưa gắn báo giá nên không đọc được danh sách món" % nhan)
			continue
		try:
			bg = frappe.get_doc("Bao Gia Ban Hang", hd["bao_gia"])
		except Exception:
			ghi_chu.append("%s có báo giá %s nhưng không mở được" % (nhan, hd["bao_gia"]))
			continue
		co, khong = tach_dong_bao_gia([d.as_dict() for d in bg.get("dong") or []])
		chac = 1 if hd.get("trang_thai") in HD_CHAC_CHAN else 0
		phu = "%s, sự kiện %s, %s" % (
			hd.get("loai") or "Hợp đồng", _dmy(hd.get("ngay_su_kien")), hd.get("trang_thai") or ""
		)
		for d in co:
			if d["so_luong"] <= 0:
				continue
			co_ma.append({
				"ma_hang": d["ma_mon"],
				"ten_banh": d["ten_mon"] or d["ma_mon"],
				"hinh": "",
				"can": d["so_luong"],
				"nguon": {
					"ma": "hop_dong",
					"nhan": nhan,
					"so": d["so_luong"],
					"giai_thich": phu,
					"chac_chan": chac,
					"hop_dong": hd["name"],
				},
			})
		for d in khong:
			khong_ma.append({
				"ten_mon": d["ten_mon"],
				"so_luong": d["so_luong"],
				"dvt": d["dvt"],
				"hop_dong": hd["name"],
				"nhan": nhan,
				"ngay_su_kien": str(hd.get("ngay_su_kien") or ""),
				"trang_thai": hd.get("trang_thai") or "",
			})
	return co_ma, khong_ma, ghi_chu


def _dmy(ngay):
	try:
		return getdate(ngay).strftime("%d/%m")
	except Exception:
		return str(ngay or "")


@frappe.whitelist()
def goi_y(ngay=None):
	"""Mon can lam YCSX cho mot ngay, gom ca ba nguon.

	Chi ĐỌC, khong ghi gi. Bam bao nhieu lan cung ra cung mot ket qua.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ng = getdate(ngay) if ngay else getdate()

	tho, ghi_chu = [], []
	d1, c1 = _tu_kiem_banh_ngay(ng)
	tho += d1
	if c1:
		ghi_chu.append(c1)
	d2, c2 = _tu_mua_vu(ng)
	tho += d2
	ghi_chu += c2
	d3, khong_ma, c3 = _tu_hop_dong(ng)
	tho += d3
	ghi_chu += c3

	dong = gop_theo_ma(tho)
	return {
		"ngay": str(ng),
		"dong": dong,
		"khong_ma": khong_ma,
		"ghi_chu": ghi_chu,
		"tong": len(dong),
	}
