# -*- coding: utf-8 -*-
"""Báo cáo cuối ngày cho chủ qua nhóm Zalo (v606).

Anh Việt 20/10/2026: "Tin nhắn báo doanh thu, tiền giảm giá,... ý là cái báo
cáo cuối ngày cho owner nhìn. Em thiết kế tin nhắn đó rồi cho anh duyệt."
Anh duyệt mẫu (số thật 19/10), gửi 23:30, vào nhóm Zalo anh tự tích tin
"Báo cáo cuối ngày" ở Cài đặt > Nhóm nhận tin.

Số đọc THẲNG từ hoá đơn qua đúng các hàm của phân hệ Báo cáo (bao_cao.py),
không tính lại theo cách khác: tin nhắn và màn Báo cáo luôn ra cùng một số.
Đơn chưa ghi sổ được tính như màn Báo cáo mặc định, và tin nói rõ có bao
nhiêu đơn như vậy.

Phần soạn chữ là phép THUẦN (soan_bao_cao), kiểm thử được không cần site.
"""

import frappe
from frappe.utils import add_days, getdate

MA_TIN = "bgd_bao_cao_ngay"
THU = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")
TOI_DA = 2000
# Ngưỡng của mục "Cần để ý". Đổi ở đây, không rải số trong hàm.
NGUONG_GIAM_DIEM = 20      # một điểm bán giảm từ 20% so với hôm trước
NGUONG_GIAM_TONG = 15      # cả ngày giảm từ 15%
NGUONG_GIAM_GIA = 8        # giảm giá chiếm từ 8% doanh thu
NGUONG_HUY_SO = 3          # từ 3 hoá đơn bị huỷ
NGUONG_HUY_TIEN = 1000000  # hoặc tiền huỷ từ 1 triệu
KENH_NHO = 1.0             # kênh dưới 1% doanh thu gộp chung một mục


# ------------------------------------------------------------- phép thuần

def tien_gon(x):
	"""THUẦN: 123039344 -> "123,0 tr"; 945000 -> "945k"; 500 -> "500 đ"."""
	try:
		x = float(x or 0)
	except (TypeError, ValueError):
		x = 0.0
	am = "-" if x < 0 else ""
	x = abs(x)
	if x >= 1000000:
		return am + ("%.1f tr" % (x / 1000000)).replace(".", ",")
	if x >= 1000:
		return am + "%dk" % int(round(x / 1000))
	return am + "%d đ" % int(round(x))


def phan_tram(x, le=0):
	"""THUẦN: 7.53 -> "+7,5%" (le=1); -33.4 -> "-33%". None -> ""."""
	if x is None:
		return ""
	dau = "+" if x > 0 else ("-" if x < 0 else "")
	s = ("%." + str(le) + "f") % abs(x)
	return dau + s.replace(".", ",") + "%"


def ty_le(phan, tong):
	"""THUẦN: phần trăm, None khi tổng không dương."""
	try:
		tong = float(tong or 0)
		return float(phan or 0) / tong * 100 if tong > 0 else None
	except (TypeError, ValueError):
		return None


def chenh(nay, truoc):
	"""THUẦN: phần trăm thay đổi so với trước, None khi trước không có số."""
	try:
		truoc = float(truoc or 0)
		return (float(nay or 0) - truoc) / truoc * 100 if truoc > 0 else None
	except (TypeError, ValueError):
		return None


def ngay_vn(d):
	"""THUẦN: date -> "CN 19/10"."""
	d = getdate(d)
	return "%s %s" % (THU[d.weekday()], d.strftime("%d/%m"))


def nhom_thanh_toan(ten):
	"""THUẦN: gom phương thức thanh toán về năm nhóm đọc được trong một dòng."""
	t = str(ten or "").strip().lower()
	if "chuyển khoản" in t or "chuyen khoan" in t:
		return "Chuyển khoản"
	if t.startswith("thẻ") or t.startswith("the ") or "pos" in t:
		return "Thẻ"
	if "tiền mặt" in t or "tien mat" in t:
		return "Tiền mặt"
	for k in ("grab", "shopee", "befood", "be food", "greensm", "onepay", "momo", "zalopay", "vnpay", "ví", "xanh sm"):
		if k in t:
			return "Sàn, ví"
	return "Khác"


def ten_mon_gon(ten, toi_da=30):
	"""THUẦN: tên món cho một dòng tin: bỏ khoảng trắng thừa, viết tắt bánh trung thu."""
	t = " ".join(str(ten or "").split())
	t = t.replace("Bánh trung thu", "BTT").replace("Bánh Trung Thu", "BTT")
	return t if len(t) <= toi_da else t[:toi_da - 1].rstrip() + "…"


def gop_kenh(kenh, tong):
	"""THUẦN: [(tên, tiền)] giảm dần; kênh dưới KENH_NHO% gộp thành một mục tên ghép."""
	lon, nho = [], []
	for ten, tien in sorted(kenh or [], key=lambda x: -float(x[1] or 0)):
		if float(tien or 0) <= 0:
			continue
		p = ty_le(tien, tong)
		(nho if p is not None and p < KENH_NHO else lon).append((ten, tien))
	if len(nho) == 1:
		lon.append(nho[0])
	elif nho:
		lon.append((", ".join(t for t, _ in nho), sum(float(x or 0) for _, x in nho)))
	return lon


def can_de_y(sl):
	"""THUẦN: các dòng "Cần để ý" theo ngưỡng ở đầu tệp."""
	ra = []
	c = chenh(sl.get("tong"), sl.get("tong_truoc"))
	if c is not None and c <= -NGUONG_GIAM_TONG:
		ra.append("Doanh thu cả ngày giảm %s so với hôm trước" % phan_tram(-c).lstrip("+"))
	for d in sl.get("diem") or []:
		cd = chenh(d.get("tien"), d.get("truoc"))
		if cd is not None and cd <= -NGUONG_GIAM_DIEM:
			ra.append("%s giảm %s so với hôm trước" % (d.get("ten"), phan_tram(-cd).lstrip("+")))
	g = ty_le(sl.get("giam"), sl.get("tong"))
	if g is not None and g >= NGUONG_GIAM_GIA:
		ra.append("Giảm giá chiếm %s doanh thu" % phan_tram(g, 1).lstrip("+"))
	huy = sl.get("huy") or {}
	if int(huy.get("so") or 0) >= NGUONG_HUY_SO or float(huy.get("tien") or 0) >= NGUONG_HUY_TIEN:
		ra.append("%s hoá đơn bị huỷ (%s)" % (int(huy.get("so") or 0), tien_gon(huy.get("tien"))))
	nh = sl.get("nhap") or {}
	if int(nh.get("so") or 0) > 0:
		ra.append("%s đơn chưa ghi sổ (%s) đã tính vào số trên" % (int(nh["so"]), tien_gon(nh.get("tien"))))
	return ra


def _ghep(muc, ngan="\n"):
	return ngan.join(x for x in muc if x)


def soan_bao_cao(sl):
	"""THUẦN: dict số liệu một ngày -> tin chữ theo mẫu anh Việt duyệt 20/10/2026.

	sl: ngay, ngay_truoc, tong, so_hd, tong_truoc, diem [{ten, tien, so_hd, truoc,
	giam}], kenh [(tên, tiền)], thanh_toan [(tên, tiền)], giam, ctkm {tien, luot,
	top: (tên, tiền)}, huy {so, tien}, sua, ban_chay [{ten, sl, tien}], nhap {so, tien}.
	"""
	ngay = ngay_vn(sl["ngay"])
	tong = float(sl.get("tong") or 0)
	so_hd = int(sl.get("so_hd") or 0)
	dau = "📊 Vagabond | Báo cáo cuối ngày %s" % ngay
	if so_hd <= 0:
		return dau + "\nHôm nay chưa có hoá đơn nào.\n\nChi tiết: app > Báo cáo"
	khoi = []
	c = chenh(tong, sl.get("tong_truoc"))
	khoi.append(_ghep([
		dau,
		"Doanh thu %s · %s hoá đơn · bình quân %s" % (tien_gon(tong), so_hd, tien_gon(tong / so_hd)),
		("So với %s: %s" % (ngay_vn(sl["ngay_truoc"]), phan_tram(c, 1))) if c is not None else "",
	]))
	diem = [d for d in (sl.get("diem") or []) if float(d.get("tien") or 0) > 0 or int(d.get("so_hd") or 0) > 0]
	if diem:
		dong = []
		for d in diem:
			cd = chenh(d.get("tien"), d.get("truoc"))
			p = ty_le(d.get("tien"), tong)
			dong.append("• %s %s (%s) · %s HĐ%s" % (d["ten"], tien_gon(d.get("tien")), phan_tram(p).lstrip("+") if p is not None else "0%",
				int(d.get("so_hd") or 0), (" · " + phan_tram(cd)) if cd is not None else ""))
		khoi.append(_ghep(["🏠 Theo điểm bán"] + dong))
	kenh = gop_kenh(sl.get("kenh"), tong)
	if kenh:
		muc = ["%s %s" % (t, tien_gon(x)) for t, x in kenh]
		khoi.append(_ghep(["🛵 Theo kênh", "• " + " · ".join(muc[:2]), ("• " + " · ".join(muc[2:])) if muc[2:] else ""]))
	tt = {}
	for ten, x in sl.get("thanh_toan") or []:
		n = nhom_thanh_toan(ten)
		tt[n] = tt.get(n, 0.0) + float(x or 0)
	if tt:
		thu_tu = ["Chuyển khoản", "Thẻ", "Tiền mặt", "Sàn, ví", "Khác"]
		muc = ["%s %s" % (n, tien_gon(tt[n])) for n in thu_tu if tt.get(n, 0) > 0]
		khoi.append(_ghep(["💳 Tiền về", "• " + " · ".join(muc[:3]), ("• " + " · ".join(muc[3:])) if muc[3:] else ""]))
	giam = float(sl.get("giam") or 0)
	ct = sl.get("ctkm") or {}
	if giam > 0 or float(ct.get("tien") or 0) > 0:
		p = ty_le(giam, tong)
		dong = ["🎫 Giảm giá %s%s" % (tien_gon(giam), (" (%s doanh thu)" % phan_tram(p, 1).lstrip("+")) if p is not None else "")]
		gd = sorted([d for d in diem if float(d.get("giam") or 0) > 0], key=lambda d: -float(d["giam"]))
		if gd:
			dong.append("• " + " · ".join("%s %s" % (d["ten"], tien_gon(d["giam"])) for d in gd))
		if float(ct.get("tien") or 0) > 0:
			top = ct.get("top")
			dong.append("• Khuyến mãi %s / %s lượt%s" % (tien_gon(ct["tien"]), int(ct.get("luot") or 0),
				(", nhiều nhất %s (%s)" % (top[0], tien_gon(top[1]))) if top else ""))
		khoi.append(_ghep(dong))
	huy = sl.get("huy") or {}
	sua = int(sl.get("sua") or 0)
	dong = []
	if int(huy.get("so") or 0) or sua:
		dong.append("✂️ Sửa, huỷ: %s huỷ%s, %s sửa" % (int(huy.get("so") or 0),
			(" (%s)" % tien_gon(huy.get("tien"))) if float(huy.get("tien") or 0) > 0 else "", sua))
	if dong:
		khoi.append(_ghep(dong))
	bc = [m for m in (sl.get("ban_chay") or []) if float(m.get("tien") or 0) > 0][:3]
	if bc:
		khoi.append(_ghep(["🍰 Bán chạy"] + ["• %s: %s (%s)" % (ten_mon_gon(m["ten"], 36),
			("%g" % float(m.get("sl") or 0)).replace(".", ","), tien_gon(m["tien"])) for m in bc]))
	de_y = can_de_y(sl)
	khoi.append(_ghep(["⚠️ Cần để ý"] + ["• " + x for x in de_y]) if de_y else "✅ Không có gì bất thường.")
	khoi.append("Chi tiết: app > Báo cáo")
	tin = "\n\n".join(khoi)
	if len(tin) > TOI_DA:
		tin = tin[:TOI_DA - 1].rstrip() + "…"
	return tin


# ------------------------------------------------------------- chạm hệ

def lay_so_lieu(ngay):
	"""Số một ngày, đọc qua đúng các hàm của phân hệ Báo cáo."""
	from vagabond import bao_cao as bc

	ngay = getdate(ngay)
	truoc = add_days(ngay, -1)
	hd = bc._hoa_don(ngay, ngay)
	hd_truoc = bc._hoa_don(truoc, truoc)
	tong_dt = bc._bc_tong_doanh_thu(hd)["dong"]
	cu = {d["diem"]: d["tien"] for d in bc._bc_tong_doanh_thu(hd_truoc)["dong"]}
	diem = [{"ten": d["diem"], "tien": d["tien"], "so_hd": d["so_hd"], "giam": d["giam"],
		"truoc": cu.get(d["diem"], 0)} for d in tong_dt]
	km = bc._bc_khuyen_mai(hd, tu=ngay, den=ngay)["dong"]
	sh = bc._bc_sua_huy(hd, tu=ngay, den=ngay)["dong"]
	huy = [d for d in sh if str(d.get("viec") or "").startswith("Huỷ")]
	mon = sorted(bc._bc_mon_ban_chay(hd)["dong"], key=lambda m: -float(m.get("tien") or 0))
	so_nhap, tien_nhap = bc._do_nhap(hd)
	return {
		"ngay": ngay, "ngay_truoc": truoc,
		# Tổng cộng thẳng từ hoá đơn (như màn Báo cáo), không cộng từ các điểm bán:
		# hoá đơn mang mã quầy lạ vẫn phải nằm trong tổng.
		"tong": sum(float(r.get("grand_total") or 0) for r in hd), "so_hd": len(hd),
		"tong_truoc": sum(float(r.get("grand_total") or 0) for r in hd_truoc),
		"diem": diem,
		"kenh": [(d["nguon"], d["tien"]) for d in bc._bc_nguon_don(hd)["dong"]],
		"thanh_toan": [(d["pt"], d["tien"]) for d in bc._bc_thanh_toan(hd)["dong"]],
		"giam": sum(float(d["giam"] or 0) for d in diem),
		"ctkm": {"tien": sum(float(d["giam"] or 0) for d in km), "luot": sum(int(d["so_lan"] or 0) for d in km),
			"top": (km[0]["ctkm"], km[0]["giam"]) if km else None},
		"huy": {"so": len(huy), "tien": sum(float(d.get("tien") or 0) for d in huy)},
		"sua": len(sh) - len(huy),
		"ban_chay": [{"ten": m["mon"], "sl": m["sl"], "tien": m["tien"]} for m in mon[:3]],
		"nhap": {"so": so_nhap, "tien": tien_nhap},
	}


def gui_cuoi_ngay(ngay=None):
	"""Nhịp 23:30 mỗi tối. Một tin một ngày (khoá theo ngày), nhóm nào tích tin
	"Báo cáo cuối ngày" thì nhận. Lỗi đọc số thì ghi Error Log, không gửi số dở."""
	from vagabond import kenh_zalo

	ngay = getdate(ngay) if ngay else getdate()
	try:
		tin = soan_bao_cao(lay_so_lieu(ngay))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "bao_cao_chu: chua doc duoc so %s" % ngay)
		return None
	kenh_zalo.bao_hoac_ghi_loi("ban_tin", "ban_hang", "Báo cáo cuối ngày %s" % ngay_vn(ngay),
		khoa="bao_cao_ngay:%s" % ngay, ma_tin="bgd_bao_cao_ngay", noi_dung=tin)
	frappe.db.commit()
	return tin


@frappe.whitelist()
def xem_truoc(ngay=None):
	"""Quản trị xem trước tin của một ngày, không gửi."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị được xem trước báo cáo này.", frappe.PermissionError)
	return {"tin": soan_bao_cao(lay_so_lieu(getdate(ngay) if ngay else getdate()))}
