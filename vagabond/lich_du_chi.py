# -*- coding: utf-8 -*-
"""Lịch dự chi: thêm dự chi tay, tự xếp công nợ theo hạn, tiền khả dụng theo ngày,
lịch chi hằng tháng học từ dữ liệu thật (v654, anh Việt 13/11/2026).

Vì sao có tệp này
-----------------
Màn Dự chi công nợ v653 chỉ có hai đợt 10 và 20 dựng từ hoá đơn mua. Ảnh đề
xuất anh Việt gửi 13/11 cần thêm: một khoản chi gấp ngày 15 nhập tay, một khoản
công nợ đến hạn ngày 18 máy đề xuất trả đúng hạn (không dồn sang 20), tiền nhà
ngày 20 theo lịch hằng tháng, và một dòng cảnh báo "Ngày 20/11 còn thiếu
10.000.000 đ" tính từ tiền khả dụng.

Đo dữ liệu thật 13/11 (chỉ đọc):
- Hồ sơ APP đọc được từ 08/2026 tới 11/2026 (336 hồ sơ còn hiệu lực), Payment
  Entry trả nhà cung cấp từ 07/2026 (341 lần). Ngày trả thật dồn quanh 2 tới 5,
  9 tới 14, 20 tới 22 và cuối tháng, không chỉ đúng 10 và 20.
- Tiền nhà Nguyễn Hữu Phước: APP loại Chi từ tài khoản công ty lập 20/08 (trả
  24/08), 21/09, 19/10 (trả 20/10); 79.000.000 rồi 86.900.000. Ba tháng.
- Khoản định kỳ khác đủ ba tháng: điện, internet, nước, SePay, hai khoản trả
  người cố định ngày 5 tới 7, Adecco ngày 5 tới 7 (có tháng trả trễ tới 15).

Luật (anh Việt duyệt theo ảnh đề xuất 13/11, chỗ còn phải chọn ghi ở PR)
------------------------------------------------------------------------
1. Mỗi khoản chỉ đếm MỘT lần. Thứ tự ưu tiên khi cùng một khoản có nhiều dấu:
   hồ sơ APP đang duyệt > dòng đợt dự chi > dự chi nhập tay > máy đề xuất từ dư
   nợ hoá đơn > lịch hằng tháng. Dự chi tay gắn hoá đơn thì trừ phần đó khỏi số
   máy đề xuất cho hoá đơn ấy. Tháng đã có APP hay hoá đơn mua của đúng người
   nhận thì lịch hằng tháng tháng đó không đếm nữa.
2. Máy xếp công nợ theo hạn dự tính (một nguồn: du_chi.han_du_tinh): quá hạn
   lên đầu, xếp hôm nay; còn hạn thì xếp đợt 10/20 gần nhất KHÔNG SAU hạn; không
   có đợt nào trước hạn thì xếp đúng ngày hạn (ví dụ 18/11), không dồn sang 20.
   Dòng đợt có ngày đợt sau hạn thì ghi rõ trễ mấy ngày.
3. Tiền khả dụng = số dư tài khoản chi (SePay) lúc đọc, trừ các khoản đã chi
   SAU lúc đọc số dư. Thiếu số dư thì nói rõ chưa xác định được khả năng chi.
   Tiền dự kiến về chưa có nguồn số liệu nên tách riêng, không cộng vào.
4. Máy chỉ tạo dự chi nháp. Duyệt và chi đi theo hồ sơ APP như cũ; dự chi tay
   nối với APP thì APP là dòng được đếm.

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

DT_MUC = "Vagabond Du Chi Muc"
DT_LICH = "Vagabond Lich Chi"

MUC_NHAP, MUC_HUY = "Nhap", "Huy"
NGUON_TAY, NGUON_LICH = "Nhập tay", "Theo lịch hằng tháng"
SO_NGAY_XEM = 35
SO_THANG_TOI_THIEU = 3
LECH_TOI_DA = Decimal("0.25")

NHAN_NGUON = {
	"app": "Hồ sơ APP đang duyệt",
	"dot": "Đợt dự chi",
	"tay": "Nhập tay",
	"may": "Máy đề xuất",
	"lich": "Theo lịch hằng tháng",
}
THU_TU = {"app": 0, "dot": 1, "tay": 2, "may": 3, "lich": 4}


# ================================================================== THUẦN


def _tien(v):
	from vagabond.du_chi import tien

	return tien(v)


def _ngay(v):
	from vagabond.du_chi import ngay

	return ngay(v)


def cac_dot(tu, den):
	"""Mọi ngày đợt 10 và 20 từ `tu` tới `den`. THUẦN."""
	from vagabond.du_chi import NGAY_DOT

	ra = []
	y, m = tu.year, tu.month
	while date(y, m, 1) <= den:
		for d in NGAY_DOT:
			x = date(y, m, d)
			if tu <= x <= den:
				ra.append(x)
		y, m = (y + 1, 1) if m == 12 else (y, m + 1)
	return ra


def xep_ngay_may(han, hom_nay):
	"""Ngày máy đề xuất trả một hoá đơn còn nợ. THUẦN.

	Trả (ngày, cờ): cờ "qua_han" (xếp hôm nay), "dot" (đợt gần nhất không sau
	hạn), "dung_han" (không có đợt nào trước hạn: trả đúng ngày hạn)."""
	h, t = _ngay(han), _ngay(hom_nay)
	if not h:
		return t, "dung_han"
	if h < t:
		return t, "qua_han"
	dot = cac_dot(t, h)
	if dot:
		return dot[-1], "dot"
	return h, "dung_han"


def ngay_trong_thang(nam, thang, ngay):
	"""Ngày `ngay` của tháng, kẹp về cuối tháng (31 thành 30, 28, 29). THUẦN."""
	n = calendar.monthrange(nam, thang)[1]
	return date(nam, thang, max(1, min(int(ngay or 1), n)))


def thang_cua(d):
	d = _ngay(d)
	return "%04d-%02d" % (d.year, d.month) if d else ""


def lan_lich(lich, hom_nay, den, da_co):
	"""Các lần chi của một lịch hằng tháng trong khung [đầu tháng này, den].

	da_co: tập (khoá người nhận, tháng) đã có APP, hoá đơn mua hay dự chi tay.
	Tháng này mà ngày đã qua và chưa thấy hồ sơ thì xếp hôm nay, cờ "qua_ngay".
	THUẦN. Trả [(ngày, tháng, cờ)]."""
	t = _ngay(hom_nay)
	ra = []
	y, m = t.year, t.month
	k = lich.get("khoa")
	while date(y, m, 1) <= den:
		d = ngay_trong_thang(y, m, lich.get("ngay_trong_thang") or 20)
		th = "%04d-%02d" % (y, m)
		if (k, th) not in da_co and d <= den:
			if d >= t:
				ra.append((d, th, ""))
			elif (y, m) == (t.year, t.month):
				ra.append((t, th, "qua_ngay"))
		y, m = (y + 1, 1) if m == 12 else (y, m + 1)
	return ra


def ghep_muc(hom_nay, den, hd_no, dot_dong, app_song, tay, lich, da_co):
	"""Dựng danh sách khoản chi, mỗi khoản đếm MỘT lần (luật 1). THUẦN.

	hd_no: hoá đơn còn nợ, số đã trừ phần APP khác đang giữ
	  [{hoa_don, ncc, ten_ncc, co_the_tra, han}]
	dot_dong: dòng đợt còn sống chưa có APP [{dot, ngay_dot, hoa_don, so_tra, hen_dot}]
	app_song: APP đang duyệt chưa trả [{name, ngay, so_tien, ten_nhan, dot_ngay, loai}]
	tay: dự chi nhập tay còn nháp, chưa nối APP [{name, ngay, so_tien, noi_dung, nguoi_nhan, hoa_don}]
	lich: lịch hằng tháng đang bật [{name, khoa, noi_dung, nguoi_nhan, so_tien, ngay_trong_thang}]
	da_co: tập (khoá người nhận, tháng) đã có hồ sơ (cho lịch)."""
	t = _ngay(hom_nay)
	ra = []
	for a in app_song or []:
		nd = _ngay(a.get("dot_ngay")) or max(t, _ngay(a.get("ngay")) or t)
		ra.append({"khoa": "app:" + a["name"], "nguon": "app", "ngay": max(nd, t), "so_tien": _tien(a.get("so_tien")),
			"noi_dung": a.get("noi_dung") or ("Hoàn ứng" if str(a.get("loai") or "").startswith("Hoan ung") else "Hồ sơ thanh toán"),
			"nguoi_nhan": a.get("ten_nhan") or "", "ma": a["name"], "thuong_luong": 0})
	con = {r["hoa_don"]: _tien(r.get("co_the_tra")) for r in hd_no or []}
	ve = {r["hoa_don"]: r for r in hd_no or []}
	hen = {}
	for d in dot_dong or []:
		hd = d.get("hoa_don")
		if hd not in con:
			continue
		r = ve[hd]
		st = min(_tien(d.get("so_tra")), con[hd])
		nd = _ngay(d.get("ngay_dot"))
		h = _ngay(r.get("han"))
		nhap = d.get("trang_thai") == "Nhap"
		if nhap and st > 0 and h and h < nd and st >= _tien(d.get("co_the_tra") or st):
			# Đợt còn nháp, số trả là số máy điền sẵn, hạn trước ngày đợt (ca 18/11
			# trong đợt 20/11): máy đề xuất trả đúng hạn, không dồn sang ngày đợt.
			# Thu mua sửa số hay gửi đợt đi duyệt thì ngày đợt mới là kế hoạch.
			continue
		con[hd] -= st
		if st < _tien(d.get("co_the_tra") or 0) or st <= 0:
			if d.get("hen_dot"):
				hen[hd] = _ngay(d.get("hen_dot"))
			elif not nhap or st > 0:
				# Đợt đã gửi duyệt mà phần này gia hạn, hay Thu mua đã gõ trả một phần:
				# phần gia hạn dời sang đợt kế sau đợt đó. Dòng nháp số 0 (chưa
				# thương lượng) thì máy xếp theo hạn như thường.
				from vagabond.du_chi import ngay_dot_ke_tiep
				hen[hd] = ngay_dot_ke_tiep(nd + timedelta(days=1))
		if st <= 0:
			continue
		ra.append({"khoa": "dot:%s:%s" % (d.get("dot"), hd), "nguon": "dot", "ngay": max(nd, t), "so_tien": st,
			"noi_dung": "Đợt %s · %s" % (nd.strftime("%d/%m"), r.get("ten_ncc") or hd),
			"nguoi_nhan": r.get("ten_ncc") or "", "ma": hd, "dot": d.get("dot"), "han": h,
			"tre": (nd - h).days if (h and nd > h) else 0, "thuong_luong": 1})
	for m in tay or []:
		hd = m.get("hoa_don")
		nhap_so = _tien(m.get("so_tien"))
		st = nhap_so
		if hd:
			# Codex #561: dự chi tay gắn hoá đơn chỉ được đếm phần hoá đơn CÒN lại sau
			# APP đang giữ (đã trừ trong hd_no) và dòng đợt (vừa trừ ở trên). Hoá đơn
			# không còn trong danh sách nợ (đã trả, cấn trừ sàn) thì không đếm thêm.
			st = min(nhap_so, con.get(hd, Decimal(0)))
			if hd in con:
				con[hd] -= st
		ra.append({"khoa": "tay:" + m["name"], "nguon": "tay", "ngay": max(_ngay(m.get("ngay")) or t, t), "so_tien": st,
			"so_tien_nhap": nhap_so, "da_tinh_noi_khac": nhap_so - st,
			"noi_dung": m.get("noi_dung") or "", "nguoi_nhan": m.get("nguoi_nhan") or "", "ma": m["name"],
			"qua_ngay": 1 if (_ngay(m.get("ngay")) and _ngay(m.get("ngay")) < t) else 0, "thuong_luong": 0})
	for hd, so in con.items():
		if so <= 0:
			continue
		r = ve[hd]
		if hd in hen and hen[hd]:
			nd, co = max(hen[hd], t), "hen"
		else:
			nd, co = xep_ngay_may(r.get("han"), t)
		trong = next((d.get("dot") for d in dot_dong or [] if d.get("hoa_don") == hd and d.get("trang_thai") == "Nhap"), "")
		ra.append({"khoa": "may:" + hd, "nguon": "may", "ngay": nd, "so_tien": so, "co": co, "dot": trong,
			"noi_dung": "Công nợ %s" % (r.get("ten_ncc") or r.get("ncc") or hd), "nguoi_nhan": r.get("ten_ncc") or "",
			"ma": hd, "han": _ngay(r.get("han")), "thuong_luong": 1})
	for l in lich or []:
		for nd, th, co in lan_lich(l, t, den, da_co or set()):
			ra.append({"khoa": "lich:%s:%s" % (l["name"], th), "nguon": "lich", "ngay": nd, "so_tien": _tien(l.get("so_tien")),
				"noi_dung": l.get("noi_dung") or "", "nguoi_nhan": l.get("nguoi_nhan") or "", "ma": l["name"], "thang": th,
				"qua_ngay": 1 if co == "qua_ngay" else 0, "thuong_luong": 0})
	# Dự chi tay đã tính hết ở đợt hay APP vẫn hiện (số 0 kèm ghi chú) để người lập thấy vì sao.
	ra = [x for x in ra if x["ngay"] <= den and (x["so_tien"] > 0 or (x["nguon"] == "tay" and x.get("so_tien_nhap", 0) > 0))]
	ra.sort(key=lambda x: (x["ngay"], 0 if x.get("co") == "qua_han" else 1, THU_TU[x["nguon"]], str(x.get("han") or ""), x["khoa"]))
	return ra


def theo_ngay(so_du, muc, ve=()):
	"""Gom khoản chi theo ngày và tính tiền còn lại sau mỗi ngày. THUẦN.

	so_du: số tiền khả dụng (Decimal) hoặc None khi chưa đọc được.
	ve: tiền dự kiến về [{ngay, so_tien}] (công nợ khách theo ngày dự kiến trả,
	    xem du_kien_ve). Tiền về ngày D được cộng trước khi trừ khoản chi ngày D.
	Trả dict: ngay [{ngay, muc, tong, ve, con_lai, thieu}], tong, thieu_dau
	(ngày thiếu đầu tiên hoặc None), can_thuong_luong (khoản công nợ tới ngày
	đó, khoản dời được nhất đứng trước)."""
	ngay = []
	for x in muc:
		if not ngay or ngay[-1]["ngay"] != x["ngay"]:
			ngay.append({"ngay": x["ngay"], "muc": [], "tong": Decimal(0)})
		ngay[-1]["muc"].append(x)
		ngay[-1]["tong"] += x["so_tien"]
	cho_ve = sorted(((_ngay(v.get("ngay")), _tien(v.get("so_tien"))) for v in ve or () if _ngay(v.get("ngay"))), key=lambda v: v[0])
	con = so_du
	dau = None
	i = 0
	for g in ngay:
		g["ve"] = Decimal(0)
		while i < len(cho_ve) and cho_ve[i][0] <= g["ngay"]:
			g["ve"] += cho_ve[i][1]
			i += 1
		if con is None:
			g["con_lai"], g["thieu"] = None, None
			continue
		con = con + g["ve"] - g["tong"]
		g["con_lai"] = con
		g["thieu"] = -con if con < 0 else Decimal(0)
		if con < 0 and dau is None:
			dau = g
	can = []
	if dau:
		can = [x for g in ngay if g["ngay"] <= dau["ngay"] for x in g["muc"] if x.get("thuong_luong")]
		can.sort(key=lambda x: (str(x.get("han") or "9999"), -x["so_tien"]), reverse=True)
	return {"ngay": ngay, "tong": sum((g["tong"] for g in ngay), Decimal(0)),
		"thieu_dau": {"ngay": dau["ngay"], "so_tien": dau["thieu"]} if dau else None, "can_thuong_luong": can}


def moc_gio(v):
	"""THUẦN: mốc giờ đủ phần lẻ giây (datetime) từ datetime hay chuỗi ISO; None khi trống hay hỏng."""
	if not v:
		return None
	if isinstance(v, datetime):
		return v
	try:
		return datetime.fromisoformat(str(v).strip())
	except ValueError:
		return None


def chi_sau_anh(rows, luc_anh, tk):
	"""Tổng tiền ĐI RA khỏi tài khoản đã đọc số dư, ghi sổ SAU giờ đọc. THUẦN.

	rows: [{tong_tien, luc (giờ ghi sổ), tk_chi (tài khoản sổ cái)}]. Khoản ghi
	trước hay đúng giờ đọc đã nằm trong số dư nên không trừ lại; khoản của tài
	khoản khác hay tiền mặt không làm đổi số dư tài khoản này. So đủ phần lẻ
	giây: khoản ghi sau giờ đọc trong cùng một giây vẫn được trừ. Không biết
	tài khoản hay giờ đọc thì không trừ gì (Codex #561)."""
	moc = moc_gio(luc_anh)
	if not tk or moc is None:
		return Decimal(0)
	ra = Decimal(0)
	for r in rows or []:
		g = moc_gio(r.get("luc"))
		if (r.get("tk_chi") or "") == tk and g is not None and g > moc:
			ra += _tien(r.get("tong_tien"))
	return ra


TRE_MAC_DINH = 30  # ngày, khi chưa có lịch sử trả nào để học


def trung_vi_ngay(ds):
	"""THUẦN: trung vị số ngày (số nguyên), None khi rỗng."""
	ds = sorted(int(x) for x in ds or () if x is not None)
	if not ds:
		return None
	n = len(ds)
	return ds[n // 2] if n % 2 else (ds[n // 2 - 1] + ds[n // 2]) // 2


def du_kien_ve(hd_no, tre_theo_khach, hom_nay, den):
	"""Tiền dự kiến về từ CÔNG NỢ CẦN THU (anh Việt 13/11). THUẦN.

	hd_no: hoá đơn bán còn phải đòi [{hoa_don, khach, ngay (ngày hoá đơn), so_tien}].
	tre_theo_khach: {khách: [số ngày từ ngày hoá đơn tới ngày trả]} học từ các
	hoá đơn công nợ đã trả. Hạn trên hoá đơn bán của Vagabond trùng ngày hoá đơn
	(117/117 tờ còn nợ ngày 13/11) nên không dùng được làm ngày về.
	Ngày dự kiến về = ngày hoá đơn + trung vị số ngày trả của chính khách đó (từ
	hai lần trả trở lên), không đủ thì trung vị chung, chưa có gì thì 30 ngày.
	Đã qua ngày dự kiến mà chưa trả thì KHÔNG tính vào ngày nào (không đoán khách
	trả hôm nay), chỉ cộng vào ô "quá hạn chưa thu". Sau khung xem cũng chỉ cộng tổng.
	Trả {ve [{ngay, so_tien, hoa_don, khach}], trong_khung, qua_han, sau_khung, tre_chung}."""
	t, den = _ngay(hom_nay), _ngay(den)
	chung = trung_vi_ngay([x for v in (tre_theo_khach or {}).values() for x in v])
	if chung is None:
		chung = TRE_MAC_DINH
	ve, qua, sau = [], Decimal(0), Decimal(0)
	for r in hd_no or ():
		so = _tien(r.get("so_tien"))
		ngay_hd = _ngay(r.get("ngay"))
		if so <= 0 or not ngay_hd:
			continue
		rieng = (tre_theo_khach or {}).get(r.get("khach")) or []
		tre = trung_vi_ngay(rieng) if len(rieng) >= 2 else chung
		d = ngay_hd + timedelta(days=tre)
		if d < t:
			qua += so
		elif d > den:
			sau += so
		else:
			ve.append({"ngay": d, "so_tien": so, "hoa_don": r.get("hoa_don"), "khach": r.get("khach")})
	ve.sort(key=lambda v: (v["ngay"], str(v["hoa_don"])))
	return {"ve": ve, "trong_khung": sum((v["so_tien"] for v in ve), Decimal(0)), "qua_han": qua, "sau_khung": sau, "tre_chung": chung}


def kha_dung_tai_chinh(dong, chi_sau_theo_ba):
	"""Tiền khả dụng = số dư NGÂN HÀNG đúng như mục Tài chính (anh Việt 13/11). THUẦN.

	dong: các dòng `tai_chinh._tinh_tien()["dong"]`. Chỉ lấy tài khoản ngân hàng
	của công ty (bỏ tài khoản tạm ứng đứng tên cá nhân, bỏ két, quỹ tiền mặt).
	Dòng lấy thẳng số SePay báo (không đồng bộ giao dịch về app) thì trừ thêm
	tiền đã ghi sổ ra khỏi tài khoản đó SAU giờ đọc (chi_sau_theo_ba {Bank
	Account: tiền}); dòng tính từ mốc chốt cộng phát sinh sổ đã gồm mọi bút toán.
	Một tài khoản tính hỏng thì KHÔNG đoán (trả None, nêu tên); tài khoản chưa
	chốt số dư thì không cộng, nêu tên."""
	tong, chi, co, hong, chua = Decimal(0), Decimal(0), 0, [], []
	for d in dong or ():
		if d.get("loai") != "Ngân hàng" or d.get("tam_ung") or d.get("dang_chuyen"):
			continue
		if d.get("so_du") is None:
			(hong if d.get("loi") else chua).append(d.get("ten") or d.get("nguon") or "")
			continue
		co += 1
		tong += _tien_am(d.get("so_du"))
		if not d.get("dong_bo") and _tien(d.get("so_bao") or 0) > 0:
			chi += _tien((chi_sau_theo_ba or {}).get(d.get("bank_account")) or 0)
	if hong or not co:
		return {"so_tien": None, "so_du_tk": None, "chi_sau": Decimal(0), "hong": hong, "chua_chot": chua}
	return {"so_tien": tong - chi, "so_du_tk": tong, "chi_sau": chi, "hong": [], "chua_chot": chua}


def an_so_tien(kq):
	"""Người không được xem Tài chính (Thu mua): bỏ mọi con số lộ tiền trong tài
	khoản, giữ ngày không đủ tiền và khoản cần thương lượng (anh Việt 13/11). THUẦN."""
	kq = dict(kq)
	kq["so_du"] = {"an": 1}
	kq["du_kien_ve"] = {"an": 1}
	kq["ngay"] = [dict(g, con_lai=None, thieu=None, ve=None, khong_du=1 if g.get("thieu") else 0) for g in kq.get("ngay") or ()]
	if kq.get("thieu_dau"):
		kq["thieu_dau"] = {"ngay": kq["thieu_dau"]["ngay"], "so_tien": None}
	return kq


def tien_kha_dung(so_du_tk, chi_sau_luc):
	"""Số dư lúc đọc trừ phần đã chi sau lúc đó (chưa vào số dư). None giữ None. THUẦN."""
	if so_du_tk is None:
		return None
	return _tien_am(so_du_tk) - _tien(chi_sau_luc or 0)


def _tien_am(v):
	return Decimal(str(v or 0))


def trung_vi(ds):
	ds = sorted(ds)
	if not ds:
		return None
	g = len(ds) // 2
	return ds[g] if len(ds) % 2 else (ds[g - 1] + ds[g]) / 2


def hoc_lich(lich_su):
	"""Gợi ý lịch chi hằng tháng từ lịch sử chi thật. THUẦN.

	lich_su: [{khoa, ten, ngay, so_tien, loai}] (loai: "TK cong ty", "NCC",
	"Hoan ung", "Hoan ung HD"...). Hoàn ứng bỏ ra (trả lại người ứng, không phải
	chi định kỳ). Mỗi người nhận: số tháng thấy, ngày điển hình (trung vị ngày
	trong tháng), số tiền điển hình (trung vị theo tháng, gộp các lần trả từng
	phần trong tháng), và các ngoại lệ (lệch số trên 25%, trả nhiều lần trong
	tháng, lệch ngày trên 5 ngày). Chỉ gợi ý khi thấy ít nhất ba tháng."""
	nhom = {}
	for r in lich_su or []:
		if str(r.get("loai") or "").startswith("Hoan ung"):
			continue
		d = _ngay(r.get("ngay"))
		if not d or not r.get("khoa"):
			continue
		g = nhom.setdefault(r["khoa"], {"ten": r.get("ten") or r["khoa"], "thang": {}})
		g["thang"].setdefault(thang_cua(d), []).append((d, _tien_am(r.get("so_tien"))))
	ra = []
	for k, g in nhom.items():
		if len(g["thang"]) < SO_THANG_TOI_THIEU:
			continue
		tong_thang = {th: sum((x[1] for x in v), Decimal(0)) for th, v in g["thang"].items()}
		ngay_thang = {th: min(x[0] for x in v).day for th, v in g["thang"].items()}
		so = trung_vi(list(tong_thang.values()))
		ng = int(trung_vi(list(ngay_thang.values())))
		le = []
		for th in sorted(g["thang"]):
			v = g["thang"][th]
			if len(v) > 1:
				le.append("Tháng %s trả %d lần (từng phần hoặc khoản lẻ)" % (th[5:] + "/" + th[:4], len(v)))
			if so and abs(tong_thang[th] - so) > so * LECH_TOI_DA:
				le.append("Tháng %s chi %s, lệch số thường lệ" % (th[5:] + "/" + th[:4], format(int(tong_thang[th]), ",").replace(",", ".")))
			if abs(ngay_thang[th] - ng) > 5:
				le.append("Tháng %s chi ngày %d" % (th[5:] + "/" + th[:4], ngay_thang[th]))
		ra.append({"khoa": k, "ten": g["ten"], "so_thang": len(g["thang"]), "thang": sorted(g["thang"]),
			"ngay_goi_y": ng, "so_tien_goi_y": so, "ngoai_le": le})
	ra.sort(key=lambda x: -x["so_tien_goi_y"])
	return ra


def kiem_muc(x):
	"""Kiểm một dự chi tay trước khi lưu; trả dict đã chuẩn hoá hoặc ném
	ValueError có câu nói việc cần làm. THUẦN."""
	d = _ngay(x.get("ngay")) if x.get("ngay") else None
	if not d:
		raise ValueError("Chọn ngày cần chi.")
	nd = str(x.get("noi_dung") or "").strip()
	if not nd:
		raise ValueError("Ghi nội dung khoản chi, ví dụ: Chi gấp mua bơ.")
	try:
		so = _tien(x.get("so_tien"))
	except ValueError:
		raise ValueError("Số tiền phải là số, ví dụ 10000000.") from None
	if so <= 0:
		raise ValueError("Số tiền phải lớn hơn 0.")
	return {"ngay": d, "noi_dung": nd[:140], "so_tien": so, "nguoi_nhan": str(x.get("nguoi_nhan") or "").strip()[:140],
		"ly_do": str(x.get("ly_do") or "").strip()[:1000], "hoa_don": str(x.get("hoa_don") or "").strip() or None}


# ================================================================== CHẠM HỆ

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime, nowdate  # noqa: E402


def _ho():
	from vagabond import ho_so_tt
	return ho_so_tt


def _vai():
	return set(frappe.get_roles(frappe.session.user))


def _chan(nhom, viec):
	if not (set(nhom) & _vai()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _str(d):
	return str(d) if d else ""


def so_du_kha_dung():
	"""Tiền khả dụng lấy đúng số dư ngân hàng của mục Tài chính (anh Việt 13/11):
	cùng hàm `tai_chinh._tinh_tien`, không tự đọc SePay riêng. Dòng lấy thẳng số
	SePay báo thì trừ thêm tiền ghi sổ ra khỏi tài khoản đó sau giờ SePay đọc."""
	from vagabond import tai_chinh

	tien = tai_chinh._tinh_tien()
	luc = tai_chinh._sepay_luc_bao() or str(now_datetime())
	dong = tien.get("dong") or []
	chi_sau = {}
	for d in dong:
		ba = d.get("bank_account")
		if d.get("loai") != tai_chinh.LOAI_NH or d.get("dong_bo") or not ba or flt(d.get("so_bao")) <= 0:
			continue
		tk_gl = frappe.db.get_value("Bank Account", ba, "account")
		if not tk_gl:
			continue
		# Đọc theo SỔ CÁI của đúng tài khoản (Codex #561 vòng 2): Payment Entry và
		# Journal Entry đều ghi GL Entry, hồ sơ APP để trống tài khoản cũng không lọt.
		rows = frappe.get_all("GL Entry", filters={"account": tk_gl, "is_cancelled": 0, "credit": [">", 0], "creation": [">", luc]},
			fields=["credit as tong_tien", "creation as luc", "account as tk_chi"], limit_page_length=0)
		chi_sau[ba] = chi_sau_anh([dict(r) for r in rows], luc, tk_gl)
	kq = kha_dung_tai_chinh(dong, chi_sau)
	if kq["so_tien"] is None:
		nguon = ("Chưa đọc được số dư: " + ", ".join(kq["hong"])) if kq["hong"] else "Chưa có số dư ngân hàng nào trong mục Tài chính"
	else:
		nguon = "Số dư ngân hàng theo mục Tài chính" + ((" (chưa chốt: " + ", ".join(kq["chua_chot"]) + ")") if kq["chua_chot"] else "")
	return {"so_tien": kq["so_tien"], "so_du_tk": kq["so_du_tk"], "chi_sau": flt(kq["chi_sau"]), "luc": luc, "nguon": nguon}


def _phai_thu_hd():
	"""Hoá đơn bán còn phải đòi, kể cả tờ đã gom vào phiếu đòi nợ: cùng phép tính
	của màn Công nợ phải thu (cong_no.hd_con_doi)."""
	from vagabond import cong_no

	return [{"hoa_don": r.get("name"), "khach": r.get("vgb_khach_no") or r.get("customer") or "", "ngay": r.get("posting_date"),
		"so_tien": r.get("con_doi")} for r in cong_no.hd_con_doi()]


def _tre_thanh_toan(so_ngay=180):
	"""{khách: [số ngày từ ngày hoá đơn tới ngày trả]} của hoá đơn công nợ đã trả đủ
	trong 180 ngày, đọc theo Payment Ledger (phiếu thu và bút toán đều ghi vào đó)."""
	tu = getdate(nowdate()) - timedelta(days=so_ngay)
	rows = frappe.db.sql("""select coalesce(nullif(si.vgb_khach_no, ''), si.customer) khach, si.posting_date ngay, max(ple.posting_date) tra
		from `tabPayment Ledger Entry` ple join `tabSales Invoice` si on si.name = ple.against_voucher_no
		where ple.against_voucher_type = 'Sales Invoice' and ple.voucher_type in ('Payment Entry', 'Journal Entry')
			and ple.delinked = 0 and ple.amount < 0 and si.docstatus = 1 and si.vgb_pt_thanh_toan = 'Công nợ'
			and si.outstanding_amount <= 0 and si.posting_date >= %s
		group by si.name, khach, si.posting_date""", (tu,), as_dict=True)
	ra = {}
	for r in rows:
		if r.get("tra") and r.get("ngay"):
			ra.setdefault(r["khach"], []).append(max(0, (getdate(r["tra"]) - getdate(r["ngay"])).days))
	return ra


def _xem_so_du():
	"""Chỉ người được xem mục Tài chính thấy con số (anh Việt 13/11: Thu mua không biết số này)."""
	from vagabond import tai_chinh

	return tai_chinh.co_quyen()


def _hd_no():
	from vagabond import du_chi

	san = du_chi.ncc_can_tru_san()
	pi = frappe.get_all("Purchase Invoice", filters={"docstatus": 1, "outstanding_amount": [">", 0], "is_return": 0},
		fields=["name", "supplier", "supplier_name", "posting_date", "bill_date", "outstanding_amount"],
		order_by="posting_date asc", limit_page_length=0)
	pi = [r for r in pi if r.supplier not in san]
	giu = du_chi._dang_giu([r.name for r in pi])
	so = du_chi.so_ngay_no_cua({r.supplier for r in pi})
	ra = []
	for r in pi:
		ct = max(Decimal(0), Decimal(str(r.outstanding_amount or 0)) - giu.get(r.name, Decimal(0)))
		h = du_chi.han_du_tinh(r.bill_date or r.posting_date, so.get(r.supplier, (du_chi.SO_NGAY_NO_MAC_DINH,))[0])
		ra.append({"hoa_don": r.name, "ncc": r.supplier, "ten_ncc": r.supplier_name or r.supplier, "co_the_tra": ct,
			"han": h, "thang": thang_cua(r.posting_date)})
	return ra


def _dot_dong():
	from vagabond import du_chi

	return [dict(r) for r in frappe.db.sql("""select p.name dot, p.ngay_dot, p.trang_thai, d.hoa_don, d.so_tra, d.co_the_tra, d.hen_dot
		from `tabVagabond Dot Chi Dong` d join `tabVagabond Dot Chi` p on p.name=d.parent
		where p.trang_thai in %s and ifnull(d.hoa_don,'')!='' and ifnull(d.ho_so_app,'')=''""",
		(du_chi.TT_SONG,), as_dict=True)]


def _app_song():
	from vagabond import du_chi, phan_bo_app

	rows = frappe.get_all("Vagabond Ho So TT", filters={"trang_thai": ["in", list(phan_bo_app.GIU)]},
		fields=["name", "ngay", "tong_tien", "ten_nhan", "ten_ncc", "loai", "ghi_chu", "nha_cung_cap"], limit_page_length=0)
	dot = {}
	for r in rows:
		g = r.ghi_chu or ""
		if g.startswith(du_chi.ghi_chu_app("")):
			ma = g[len(du_chi.ghi_chu_app("")):].strip()
			dot[r.name] = frappe.db.get_value(du_chi.DT, ma, "ngay_dot") if ma else None
	return [{"name": r.name, "ngay": r.ngay, "so_tien": r.tong_tien, "ten_nhan": r.ten_nhan or r.ten_ncc or "",
		"loai": r.loai or "", "dot_ngay": dot.get(r.name), "ncc": r.nha_cung_cap} for r in rows]


def _tay(app_song):
	song = {a["name"] for a in app_song}
	ra = []
	for r in frappe.get_all(DT_MUC, filters={"trang_thai": MUC_NHAP}, fields=["name", "ngay", "so_tien", "noi_dung",
			"nguoi_nhan", "nha_cung_cap", "hoa_don", "ho_so_app", "lich", "thang", "nguon"], limit_page_length=0):
		if r.ho_so_app and r.ho_so_app in song:
			continue  # APP nối với dự chi này đang duyệt: APP là dòng được đếm
		if r.ho_so_app and frappe.db.get_value("Vagabond Ho So TT", r.ho_so_app, "trang_thai") == "Da thanh toan":
			continue
		ra.append(dict(r))
	return ra


def _khoa_nhan(ncc, ten):
	return (ncc or ten or "").strip()


def _lich():
	"""MỌI lịch hằng tháng, kể cả đang tạm thôi (Codex #561: lịch tạm thôi phải còn
	trên màn để bật lại). Chỉ lịch đang bật mới vào phép tính tiền."""
	return [dict(r, khoa=_khoa_nhan(r.nha_cung_cap, r.nguoi_nhan), bat=cint(r.bat)) for r in frappe.get_all(DT_LICH,
		fields=["name", "noi_dung", "nguoi_nhan", "nha_cung_cap", "so_tien", "ngay_trong_thang", "so_thang_thay", "ngoai_le", "bat"],
		order_by="bat desc, ngay_trong_thang asc", limit_page_length=0)]


def lich_dang_bat(ds):
	"""THUẦN: lịch đang bật, đúng thứ tự."""
	return [x for x in ds or [] if cint(x.get("bat"))]


def _da_co(lich, hd_no, tay_tat_ca, hom_nay):
	"""(khoá người nhận, tháng) đã có hồ sơ: APP đang duyệt hay đã trả, hoá đơn mua
	của đúng nhà cung cấp, dự chi tay gắn lịch đó."""
	ra = set()
	if not lich:
		return ra
	from vagabond import phan_bo_app

	tu = date(hom_nay.year, hom_nay.month, 1)
	ds_ncc = [l["nha_cung_cap"] for l in lich if l.get("nha_cung_cap")]
	ds_ten = [l["nguoi_nhan"] for l in lich if l.get("nguoi_nhan")]
	for r in frappe.get_all("Vagabond Ho So TT", filters={"trang_thai": ["in", list(phan_bo_app.GIU) + ["Da thanh toan"]],
			"ngay": [">=", str(tu - timedelta(days=5))]}, fields=["nha_cung_cap", "ten_nhan", "ten_ncc", "ngay"], limit_page_length=0):
		for k in (r.nha_cung_cap, r.ten_nhan, r.ten_ncc):
			if k and (k in ds_ncc or k in ds_ten):
				ra.add((k, thang_cua(r.ngay)))
	if ds_ncc:
		# Chỉ hoá đơn ĐÃ GHI SỔ: còn nợ thì máy đề xuất công nợ thay (_hd_no), đã trả
		# thì xong. Hoá đơn nháp chưa thay được dòng nào, lịch tháng đó vẫn tính (Codex #561).
		for r in frappe.get_all("Purchase Invoice", filters={"docstatus": 1, "supplier": ["in", ds_ncc],
				"posting_date": [">=", str(tu)]}, fields=["supplier", "posting_date"], limit_page_length=0):
			ra.add((r.supplier, thang_cua(r.posting_date)))
	ten_lich = {l["name"]: l["khoa"] for l in lich}
	for m in tay_tat_ca:
		if m.get("lich") and m.get("thang") and m["lich"] in ten_lich:
			ra.add((ten_lich[m["lich"]], m["thang"]))
	return ra


def _cho_man_muc(x):
	return {"khoa": x["khoa"], "nguon": x["nguon"], "nhan_nguon": NHAN_NGUON[x["nguon"]], "ngay": _str(x["ngay"]),
		"so_tien": flt(x["so_tien"]), "noi_dung": x.get("noi_dung") or "", "nguoi_nhan": x.get("nguoi_nhan") or "",
		"ma": x.get("ma") or "", "han": _str(x.get("han")), "tre": x.get("tre") or 0, "co": x.get("co") or "",
		"qua_ngay": x.get("qua_ngay") or 0, "thang": x.get("thang") or "", "dot": x.get("dot") or "",
		"da_tinh_noi_khac": flt(x.get("da_tinh_noi_khac") or 0)}


@frappe.whitelist()
def lich(so_ngay=SO_NGAY_XEM):
	"""Màn Lịch dự chi: tiền khả dụng, các khoản theo ngày, cảnh báo thiếu."""
	ho = _ho()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi")
	t = getdate(nowdate())
	den = t + timedelta(days=max(7, min(cint(so_ngay) or SO_NGAY_XEM, 120)))
	sd = so_du_kha_dung()
	try:
		dv = du_kien_ve(_phai_thu_hd(), _tre_thanh_toan(), t, den)
		dv_loi = ""
	except Exception:
		frappe.log_error(frappe.get_traceback(), "lich_du_chi: tien du kien ve")
		dv, dv_loi = {"ve": [], "trong_khung": 0, "qua_han": 0, "sau_khung": 0, "tre_chung": 0}, "Chưa đọc được công nợ cần thu"
	hd = _hd_no()
	app = _app_song()
	tay_tat_ca = [dict(r) for r in frappe.get_all(DT_MUC, filters={"trang_thai": ["!=", MUC_HUY]},
		fields=["name", "lich", "thang"], limit_page_length=0)]
	tay = _tay(app)
	ca_lich = _lich()
	lc = lich_dang_bat(ca_lich)
	muc = ghep_muc(t, den, hd, _dot_dong(), app, tay, lc, _da_co(lc, hd, tay_tat_ca, t))
	kd = tien_kha_dung(sd["so_tien"], sd["chi_sau"])
	kq = theo_ngay(kd, muc, dv["ve"])
	ra = {
		"hom_nay": str(t), "den": str(den),
		"so_du": {"so_tien": flt(kd) if kd is not None else None, "so_du_tk": sd["so_tien"], "chi_sau": sd["chi_sau"],
			"luc": sd["luc"], "nguon": sd["nguon"]},
		"du_kien_ve": {"trong_khung": flt(dv["trong_khung"]), "qua_han": flt(dv["qua_han"]), "sau_khung": flt(dv["sau_khung"]),
			"tre_chung": cint(dv["tre_chung"]), "loi": dv_loi},
		"ngay": [{"ngay": str(g["ngay"]), "tong": flt(g["tong"]), "ve": flt(g["ve"]), "con_lai": flt(g["con_lai"]) if g["con_lai"] is not None else None,
			"thieu": flt(g["thieu"]) if g["thieu"] is not None else None, "muc": [_cho_man_muc(x) for x in g["muc"]]} for g in kq["ngay"]],
		"tong": flt(kq["tong"]),
		"thieu_dau": {"ngay": str(kq["thieu_dau"]["ngay"]), "so_tien": flt(kq["thieu_dau"]["so_tien"])} if kq["thieu_dau"] else None,
		"can_thuong_luong": [_cho_man_muc(x) for x in kq["can_thuong_luong"][:8]],
		"lich_chi": [{"name": l["name"], "noi_dung": l["noi_dung"], "nguoi_nhan": l["nguoi_nhan"], "nha_cung_cap": l.get("nha_cung_cap") or "",
			"so_tien": flt(l["so_tien"]), "ngay_trong_thang": cint(l["ngay_trong_thang"]), "so_thang_thay": cint(l.get("so_thang_thay")),
			"ngoai_le": l.get("ngoai_le") or "", "bat": cint(l.get("bat"))} for l in ca_lich],
		"quyen": {"sua": 1 if (_vai() & ho.VAI_LAP) else 0},
	}
	if not _xem_so_du():
		ra = an_so_tien(ra)
	ra["quyen"]["xem_so"] = 0 if ra["so_du"].get("an") else 1
	return ra


def _ncc_chon(ma):
	"""Mã nhà cung cấp chọn từ ô chọn (Codex #561, AGENTS QT-31): phải có thật
	trong danh mục; để trống là người nhận không phải nhà cung cấp. Không bao giờ
	đoán nhà cung cấp từ chữ gõ tay."""
	ma = (ma or "").strip()
	if not ma:
		return None, ""
	ten = frappe.db.get_value("Supplier", ma, "supplier_name")
	if ten is None and not frappe.db.exists("Supplier", ma):
		frappe.throw("Không có nhà cung cấp mã %s trong danh mục. Bấm Chọn nhà cung cấp để chọn lại." % ma)
	return ma, (ten or ma)


@frappe.whitelist()
def chon_ncc(tu_khoa=""):
	"""Ô chọn nhà cung cấp của form Thêm dự chi và Lịch hằng tháng: tìm theo tên, mã, MST."""
	ho = _ho()
	_chan(ho.VAI_LAP, "chọn nhà cung cấp")
	q = (tu_khoa or "").strip()
	rows = frappe.get_all("Supplier", filters={"disabled": 0}, or_filters=[["name", "like", "%" + q + "%"],
		["supplier_name", "like", "%" + q + "%"], ["tax_id", "like", "%" + q + "%"]] if q else None,
		fields=["name", "supplier_name", "tax_id"], order_by="supplier_name asc", limit_page_length=20)
	return [{"name": r.name, "ten": r.supplier_name or r.name, "mst": r.tax_id or ""} for r in rows]


@frappe.whitelist(methods=["POST"])
def luu_muc(name=None, ngay=None, noi_dung=None, so_tien=None, nguoi_nhan=None, ly_do=None, hoa_don=None, nha_cung_cap=None):
	"""Nút Lưu dự chi nháp: thêm mới hoặc sửa một dự chi tay còn nháp."""
	ho = _ho()
	_chan(ho.VAI_LAP, "thêm dự chi")
	try:
		x = kiem_muc({"ngay": ngay, "noi_dung": noi_dung, "so_tien": so_tien, "nguoi_nhan": nguoi_nhan, "ly_do": ly_do, "hoa_don": hoa_don})
	except ValueError as e:
		frappe.throw(str(e))
	if x["hoa_don"] and not frappe.db.exists("Purchase Invoice", {"name": x["hoa_don"], "docstatus": 1}):
		frappe.throw("Không có hoá đơn mua đã ghi sổ mã %s. Để trống ô hoá đơn nếu khoản này chưa có hoá đơn." % x["hoa_don"])
	ncc, ten_ncc = _ncc_chon(nha_cung_cap)
	if x["hoa_don"]:
		ncc_hd = frappe.db.get_value("Purchase Invoice", x["hoa_don"], "supplier")
		if ncc and ncc_hd and ncc != ncc_hd:
			frappe.throw("Hoá đơn %s là của nhà cung cấp %s, không phải nhà cung cấp đã chọn. Chọn lại một trong hai." % (x["hoa_don"], ncc_hd))
		if not ncc and ncc_hd:
			ncc, ten_ncc = _ncc_chon(ncc_hd)
	if ncc:
		x["nguoi_nhan"] = ten_ncc
	if name:
		doc = frappe.get_doc(DT_MUC, name, for_update=True)
		if doc.trang_thai != MUC_NHAP:
			frappe.throw("Dự chi %s đã %s, không sửa được." % (doc.name, "huỷ" if doc.trang_thai == MUC_HUY else "đóng"))
	else:
		doc = frappe.new_doc(DT_MUC)
		doc.trang_thai = MUC_NHAP
		doc.nguon = NGUON_TAY
		doc.nguoi_lap = frappe.session.user
	doc.update({"ngay": x["ngay"], "noi_dung": x["noi_dung"], "so_tien": flt(x["so_tien"]), "nguoi_nhan": x["nguoi_nhan"],
		"nha_cung_cap": ncc, "ly_do": x["ly_do"], "hoa_don": x["hoa_don"]})
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
def xoa_muc(name):
	"""Nút Xoá dự chi nháp (anh Việt 13/11): xoá hẳn một dự chi tay còn nháp. Chỉ là
	bản ghi kế hoạch của app, không có chứng từ, sổ sách nào trỏ vào."""
	ho = _ho()
	_chan(ho.VAI_LAP, "xoá dự chi")
	if not frappe.db.exists(DT_MUC, name):
		return {"name": name, "da_xoa": 1}
	doc = frappe.get_doc(DT_MUC, name, for_update=True)
	if doc.trang_thai != MUC_NHAP:
		frappe.throw("Dự chi %s không còn nháp nên không xoá được." % doc.name)
	frappe.flags.vgb_xoa_du_chi = doc.name
	try:
		frappe.delete_doc(DT_MUC, doc.name, ignore_permissions=True, force=True)
	finally:
		frappe.flags.vgb_xoa_du_chi = None
	frappe.db.commit()
	return {"name": name, "da_xoa": 1}


@frappe.whitelist(methods=["POST"])
def noi_app(name, ho_so_app):
	"""Nối dự chi tay với hồ sơ APP đã lập theo luồng duyệt hiện có. Từ lúc nối,
	APP là dòng được đếm trên lịch (không đếm hai lần)."""
	ho = _ho()
	_chan(ho.VAI_LAP, "nối dự chi với hồ sơ thanh toán")
	if not frappe.db.exists("Vagabond Ho So TT", ho_so_app):
		frappe.throw("Không có hồ sơ thanh toán %s." % ho_so_app)
	doc = frappe.get_doc(DT_MUC, name, for_update=True)
	if doc.trang_thai != MUC_NHAP:
		frappe.throw("Dự chi %s không còn nháp." % doc.name)
	doc.ho_so_app = ho_so_app
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "ho_so_app": ho_so_app}


@frappe.whitelist()
def chon_app(tu_khoa=""):
	"""Ô chọn hồ sơ thanh toán để nối với dự chi tay (QT-31: chọn, không gõ mã).
	Chỉ hồ sơ còn hiệu lực: nháp, đang duyệt, đã duyệt, đã thanh toán."""
	ho = _ho()
	_chan(ho.VAI_LAP, "nối dự chi với hồ sơ thanh toán")
	from vagabond.ho_so_tt import NHAN, TT_DA_TRA, TT_NHAP
	from vagabond.phan_bo_app import GIU

	q = (tu_khoa or "").strip()
	rows = frappe.get_all("Vagabond Ho So TT", filters={"trang_thai": ["in", [TT_NHAP, TT_DA_TRA] + list(GIU)]},
		or_filters=[["name", "like", "%" + q + "%"], ["ten_nhan", "like", "%" + q + "%"], ["ten_ncc", "like", "%" + q + "%"]] if q else None,
		fields=["name", "ngay", "ten_nhan", "ten_ncc", "tong_tien", "trang_thai"], order_by="modified desc", limit_page_length=20)
	return [{"name": r.name, "ten": r.ten_nhan or r.ten_ncc or "", "ngay": _str(r.ngay), "so_tien": flt(r.tong_tien),
		"trang_thai": NHAN.get(r.trang_thai, r.trang_thai or "")} for r in rows]


@frappe.whitelist()
def chi_tiet_muc(name):
	ho = _ho()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi")
	d = frappe.get_doc(DT_MUC, name)
	return {"name": d.name, "ngay": _str(d.ngay), "noi_dung": d.noi_dung, "so_tien": flt(d.so_tien), "nguoi_nhan": d.nguoi_nhan or "",
		"ly_do": d.ly_do or "", "hoa_don": d.hoa_don or "", "trang_thai": d.trang_thai, "ho_so_app": d.ho_so_app or "",
		"nguon": d.nguon or NGUON_TAY, "nha_cung_cap": d.nha_cung_cap or "",
		"ten_ncc": (d.nguoi_nhan or d.nha_cung_cap or "") if d.nha_cung_cap else ""}


@frappe.whitelist()
def chon_hoa_don(tu_khoa=""):
	"""Hoá đơn mua còn nợ để gắn vào dự chi (ô Hoá đơn công nợ)."""
	ho = _ho()
	_chan(ho.VAI_LAP, "chọn hoá đơn công nợ")
	q = (tu_khoa or "").strip()
	f = {"docstatus": 1, "outstanding_amount": [">", 0]}
	rows = frappe.get_all("Purchase Invoice", filters=f, or_filters=[["name", "like", "%" + q + "%"], ["supplier_name", "like", "%" + q + "%"],
		["bill_no", "like", "%" + q + "%"]] if q else None, fields=["name", "supplier", "supplier_name", "bill_no", "outstanding_amount"],
		order_by="posting_date desc", limit_page_length=30)
	return [{"name": r.name, "ncc": r.supplier, "ten": r.supplier_name, "so": r.bill_no or "", "con_no": flt(r.outstanding_amount)} for r in rows]


@frappe.whitelist(methods=["POST"])
def luu_lich(name=None, noi_dung=None, nguoi_nhan=None, so_tien=None, ngay_trong_thang=20, bat=1, ngoai_le=None, so_thang_thay=None,
		nha_cung_cap=None):
	"""Thêm hoặc sửa một lịch chi hằng tháng (ví dụ tiền nhà ngày 20)."""
	ho = _ho()
	_chan(ho.VAI_LAP, "sửa lịch chi hằng tháng")
	n = cint(ngay_trong_thang)
	if not 1 <= n <= 31:
		frappe.throw("Ngày trong tháng từ 1 tới 31 (31 thì tháng ngắn tự lùi về cuối tháng).")
	if not (noi_dung or "").strip():
		frappe.throw("Ghi nội dung, ví dụ: Tiền nhà.")
	try:
		so = _tien(so_tien)
	except ValueError:
		frappe.throw("Số tiền phải là số.")
	doc = frappe.get_doc(DT_LICH, name, for_update=True) if name else frappe.new_doc(DT_LICH)
	ncc, ten_ncc = _ncc_chon(nha_cung_cap)
	nhan = ten_ncc if ncc else (nguoi_nhan or "").strip()
	if not nhan:
		frappe.throw("Chọn nhà cung cấp, hoặc ghi tên người nhận khác.")
	doc.update({"noi_dung": noi_dung.strip()[:140], "nguoi_nhan": nhan[:140],
		"nha_cung_cap": ncc, "so_tien": flt(so), "ngay_trong_thang": n, "bat": cint(bat)})
	if ngoai_le is not None and not name:
		# Thêm từ gợi ý của máy: giữ ngoại lệ và số tháng máy đã thấy để người sau đọc.
		doc.ngoai_le = str(ngoai_le)[:2000]
		doc.so_thang_thay = cint(so_thang_thay)
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name}


def lich_su_chi(tu=None):
	"""Lịch sử chi thật để học lịch: APP đã trả (theo người nhận) và Payment Entry
	trả nhà cung cấp không qua APP. Chỉ đọc."""
	ra = []
	for r in frappe.get_all("Vagabond Ho So TT", filters={"trang_thai": "Da thanh toan"},
			fields=["name", "loai", "nha_cung_cap", "ten_nhan", "ten_ncc", "ngay", "tong_tien"], limit_page_length=0):
		ra.append({"khoa": _khoa_nhan(r.nha_cung_cap, r.ten_nhan or r.ten_ncc), "ten": r.ten_nhan or r.ten_ncc or r.nha_cung_cap,
			"ngay": r.ngay, "so_tien": r.tong_tien, "loai": r.loai or ""})
	co_app = frappe.get_meta("Payment Entry").has_field("vgb_ho_so_tt")
	f = {"docstatus": 1, "payment_type": "Pay", "party_type": "Supplier"}
	if co_app:
		f["vgb_ho_so_tt"] = ["in", ["", None]]
	for r in frappe.get_all("Payment Entry", filters=f, fields=["party", "party_name", "posting_date", "paid_amount"], limit_page_length=0):
		ra.append({"khoa": r.party, "ten": r.party_name or r.party, "ngay": r.posting_date, "so_tien": r.paid_amount, "loai": "NCC"})
	return ra


@frappe.whitelist()
def goi_y_lich():
	"""Máy gợi ý lịch chi hằng tháng từ mọi tháng đọc được. Chỉ gợi ý, người chọn."""
	ho = _ho()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem gợi ý lịch chi")
	ls = lich_su_chi()
	co = {}
	for r in frappe.get_all(DT_LICH, fields=["name", "nha_cung_cap", "nguoi_nhan", "bat"], limit_page_length=0):
		co[_khoa_nhan(r.nha_cung_cap, r.nguoi_nhan)] = r
	thang = sorted({thang_cua(r["ngay"]) for r in ls if r.get("ngay")})
	gy = hoc_lich(ls)[:40]
	la_ncc = {r.name for r in frappe.get_all("Supplier", filters={"name": ["in", [x["khoa"] for x in gy] or [""]]},
		fields=["name"], limit_page_length=0)}
	ra = []
	for x in gy:
		c = co.get(x["khoa"])
		# Đã có lịch mà đang tạm thôi: trả mã lịch để màn mở đúng lịch đó bật lại (Codex #561).
		ra.append(dict(x, so_tien_goi_y=flt(x["so_tien_goi_y"]), da_co=1 if c else 0, da_tat=1 if (c and not cint(c.bat)) else 0,
			lich=c.name if c else "", ncc=x["khoa"] if x["khoa"] in la_ncc else ""))
	return {"thang_doc_duoc": thang, "goi_y": ra}


