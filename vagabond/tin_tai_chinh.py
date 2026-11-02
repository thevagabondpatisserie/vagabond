# -*- coding: utf-8 -*-
"""v628: tin Zalo bot cho Tài chính và việc kiểm kê sáng của bếp.

Anh Việt duyệt 02/11/2026 (7 ảnh mẫu, số liệu thật trên site sáng 02/11):
  1. bgd_tien_cuoi_ngay  23:35 mỗi tối: tiền từng tài khoản, từng két, tiền vào
     ra trong ngày, khoản chi lớn nhất. Nhóm Ban giám đốc.
  2. kt_tien_ra_chua_gan 08:00 mỗi sáng: tiền ra khỏi tài khoản công ty quá 24
     giờ mà chưa thuộc chứng từ nào. Chiều ngược của kt_tien_chua_gan.
  3. bgd_ket_lech        ngay khi chốt ca: tiền mặt lệch từ 50.000 đ, hoặc ca mở
     quá 24 giờ mới chốt. Ban giám đốc và kế toán (nhóm cửa hàng không được
     thấy số tiền, luật v613).
  4. bgd_tien_tuan       thứ Hai 08:00: dòng tiền tuần trước, công nợ, chờ chi,
     tiền khách gửi trước, dự báo 30 ngày.
  5. bgd_lai_lo_thang    ngày 05 08:00: lãi lỗ tháng trước so với tháng liền trước.
  6. bep_kiem_ke_sang    07:30 mỗi sáng, mỗi bếp một tin: 10 món cần đếm hôm nay
     (lịch xoay vòng trong kiem_ke.py), không có số tiền.

Rà site 02/11/2026: từ 01/09 bếp Pastry mới đếm 15 món, Baker gần như chưa đếm,
Lab đếm 1 món; tồn trên máy chưa ai đếm xác nhận khoảng 2,17 tỷ. Lịch xoay vòng
đã có trên máy chủ từ 02/08 nhưng app chưa gọi, bếp phải lập phiếu cả kho
(Pastry 205 món) nên bỏ. Tin 6 đi kèm nút "Đếm hôm nay" trên màn Kiểm kê.

Phép soạn là hàm THUẦN (không chạm Frappe) để kiểm thử không cần site. Phần đọc
dữ liệu nuốt lỗi vào Error Log "Vagabond: tin tài chính", không làm hỏng lịch khác.
"""

import re
from datetime import datetime

NGUONG_KET = 50000.0
GIO_CA_TOI_DA = 24
GIO_CHUA_GAN = 24
NGAY_XET_TIEN_RA = 30
TOI_DA_DONG = 8
MON_DEM_SANG = 10
HAN_DEM_SANG = "11:00 hôm nay"
TIEN_MAT = "Tiền mặt"
CHUA_CHOT = "Chưa chốt số dư đầu"


# ------------------------------------------------------------------ THUẦN

def _f(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tien(x):
	"""THUẦN: 1234567.4 -> "1.234.567 đ" (cùng cách viết với các tin Zalo khác)."""
	return "{:,.0f}".format(round(_f(x))).replace(",", ".") + " đ"


def ngay_dm(x):
	"""THUẦN: "2026-11-01..." hoặc date -> "01/11"."""
	s = str(x or "")[:10]
	return "%s/%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def ngay_dmy(x):
	s = str(x or "")[:10]
	return "%s/%s/%s" % (s[8:10], s[5:7], s[:4]) if len(s) == 10 else s


def gio_dm(x):
	"""THUẦN: "2026-10-31 06:56:11.9" -> "31/10 06:56"."""
	s = str(x or "")
	return ("%s %s" % (ngay_dm(s), s[11:16])).strip() if len(s) >= 16 else ngay_dm(s)


def rut(s, n=60):
	"""THUẦN: gom khoảng trắng, cắt n ký tự."""
	s = re.sub(r"\s+", " ", str(s or "")).strip()
	return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def phan_tram(x):
	return ("%.1f%%" % _f(x)).replace(".", ",")


def thang_vn(t):
	"""THUẦN: "2026-10" -> "10/2026"; "2026-10" -> tháng số "10"."""
	t = str(t or "")
	return "%s/%s" % (t[5:7], t[:4]) if len(t) >= 7 else t


def _gio(a, b):
	"""THUẦN: số giờ từ a tới b (chuỗi hay datetime), không đọc được thì 0."""
	def doc(x):
		if isinstance(x, datetime):
			return x
		try:
			return datetime.strptime(str(x)[:19], "%Y-%m-%d %H:%M:%S")
		except (TypeError, ValueError):
			return None
	x, y = doc(a), doc(b)
	if not x or not y:
		return 0.0
	return (y - x).total_seconds() / 3600.0


# --- Tin 1: tiền cuối ngày

def soan_cuoi_ngay(ngay, ket, dt):
	"""THUẦN: (tiêu đề, các dòng) tin "Tiền cuối ngày".

	ket: kết quả tai_chinh._tinh_tien() ({"dong", "tong"}); dt: kết quả
	tai_chinh.dong_tien_khoang(ngay, ngay)."""
	tong = (ket or {}).get("tong") or {}
	dong_ket = (ket or {}).get("dong") or []
	ra = ["Tổng tiền đang có: %s%s" % (tien(tong.get("tong")),
		" (có nguồn chưa tính được, xem dưới)" if tong.get("loi") else "")]
	chua, dem_ca = [], []
	for d in dong_ket:
		ten = d.get("ten") or d.get("nguon") or ""
		if d.get("so_du") is not None:
			ra.append("%s: %s" % (ten, tien(d.get("so_du"))))
		elif d.get("loi"):
			ra.append("%s: chưa tính được, báo kỹ thuật" % ten)
		elif CHUA_CHOT in (d.get("ghi") or []):
			chua.append(ten)
			ca = d.get("ca") or {}
			if ca.get("luc"):
				dem_ca.append("%s %s" % (ten.replace("Két ", ""), tien(ca.get("dem"))))
		else:
			ra.append("%s: %s" % (ten, "; ".join(d.get("ghi") or []) or "chưa có số"))
	if chua:
		ra.append("%s: %s" % (CHUA_CHOT, ", ".join(chua)))
	if dem_ca:
		ra.append("Số đếm lúc chốt ca gần nhất: %s" % ", ".join(dem_ca))
	if dt:
		rong = _f(dt.get("rong"))
		ra.append("Trong ngày: vào %s, ra %s, %s %s" % (tien(dt.get("vao")), tien(dt.get("ra")),
			"dư ra" if rong >= 0 else "hụt", tien(abs(rong))))
		tm = sum(_f(x.get("vao_tm")) for x in dt.get("ngay") or [])
		if tm:
			ra.append("Tiền mặt vào két và quỹ: %s" % tien(tm))
		lon = ((dt.get("lon_nhat") or {}).get("ra") or [])[:2]
		if lon:
			ra.append("Chi lớn nhất: " + "; ".join("%s (%s) %s" % (tien(g.get("so")), g.get("tk") or "",
				rut(g.get("mo_ta"), 55)) for g in lon))
		nb = dt.get("noi_bo") or {}
		if nb.get("so"):
			ra.append("Chuyển nội bộ, không tính vào ra: %d khoản, %s" % (nb["so"], tien(nb.get("tien"))))
		if dt.get("thieu"):
			ra.append("Chưa đọc được tiền mặt: %s" % ", ".join(dt["thieu"][:4]))
	return "Tiền cuối ngày %s" % ngay_dmy(ngay), ra


# --- Tin 2: tiền ra chưa có chứng từ

def loc_tien_ra(gds, tk_cty):
	"""THUẦN: khoản ra khỏi tài khoản công ty (không tạm ứng) còn tiền chưa gắn
	chứng từ, lớn trước. gds: [{"ten","tk","ra","con","ngay","mo_ta"}]."""
	ra = [g for g in gds or [] if g.get("tk") in tk_cty and _f(g.get("ra")) > 0 and _f(g.get("con")) > 1]
	ra.sort(key=lambda g: (-_f(g.get("con")), str(g.get("ten"))))
	return ra


def soan_tien_ra(ds, toi_da=TOI_DA_DONG):
	"""THUẦN: (tiêu đề, các dòng) tin "Tiền ra chưa có chứng từ"; ds rỗng -> None."""
	if not ds:
		return None
	dong = ["%d khoản, tổng %s, ra khỏi tài khoản quá %d giờ" % (len(ds), tien(sum(_f(g.get("con")) for g in ds)),
		GIO_CHUA_GAN)]
	for g in ds[:toi_da]:
		dong.append("%s: %s, %s" % (ngay_dm(g.get("ngay")), tien(g.get("con")), rut(g.get("mo_ta"))))
	if len(ds) > toi_da:
		dong.append("+%d khoản khác" % (len(ds) - toi_da))
	dong.append("Kế toán lập phiếu chi hoặc bút toán cho từng khoản để sổ tiền khớp ngân hàng.")
	return "Tiền ra khỏi tài khoản công ty chưa có chứng từ", dong


# --- Tin 3: két lệch khi chốt ca

def dong_tien_mat(bang):
	for d in bang or []:
		if str(d.get("phuong_thuc") or "") == TIEN_MAT:
			return d
	return {}


def can_bao_ket(bang, mo_luc, chot_luc, nguong=NGUONG_KET, gio_toi_da=GIO_CA_TOI_DA):
	"""THUẦN: (lệch tiền mặt, số giờ ca, có báo không)."""
	lech = _f(dong_tien_mat(bang).get("lech"))
	gio = _gio(mo_luc, chot_luc)
	return lech, gio, abs(lech) >= _f(nguong) or gio > gio_toi_da


def soan_ket_lech(ten_ket, mo_luc, chot_luc, tien_le, bang, ly_do, nguoi_chot, nguong=NGUONG_KET):
	"""THUẦN: (tiêu đề, các dòng) tin "Két lệch khi chốt ca"; không cần báo -> None."""
	lech, gio, can = can_bao_ket(bang, mo_luc, chot_luc, nguong)
	if not can:
		return None
	d = dong_tien_mat(bang)
	if abs(lech) >= _f(nguong):
		tieu_de = "%s lệch tiền mặt khi chốt ca" % ten_ket
	else:
		tieu_de = "%s: ca mở quá %d giờ mới chốt" % (ten_ket, GIO_CA_TOI_DA)
	ca = "Ca mở %s, chốt %s" % (gio_dm(mo_luc), gio_dm(chot_luc))
	if gio > GIO_CA_TOI_DA:
		ca += ": ca kéo dài %d giờ, không chốt cuối ngày %s" % (int(gio), ngay_dm(mo_luc))
	ra = [ca]
	if d:
		ra.append("Tiền mặt phải có %s (tiền lẻ đầu ca %s, thu %d bill %s)" % (tien(d.get("phai_co")),
			tien(tien_le), int(_f(d.get("so_bill"))), tien(d.get("may"))))
		if lech > 0:
			ra.append("Đếm được %s, dư %s" % (tien(d.get("dem")), tien(lech)))
		elif lech < 0:
			ra.append("Đếm được %s, thiếu %s" % (tien(d.get("dem")), tien(-lech)))
		else:
			ra.append("Đếm được %s, khớp" % tien(d.get("dem")))
	ly = str(ly_do or "").strip()
	if lech:
		ra.append("Lý do người chốt ghi: \"%s\"" % rut(ly, 120) if ly else "Người chốt chưa ghi lý do")
	if nguoi_chot:
		ra.append("Người chốt: %s" % nguoi_chot)
	return tieu_de, ra


# --- Tin 4: bản tin tiền tuần

def soan_tuan(tu, den, dt, dt_truoc, phan):
	"""THUẦN: (tiêu đề, các dòng). phan: {"phai_thu", "ncc", "cho_chi", "tra_truoc", "du_bao"},
	phần nào đọc hỏng thì giá trị None và tin ghi "chưa đọc được"."""
	ra = []
	if dt:
		rong = _f(dt.get("rong"))
		s = "Tiền vào %s, tiền ra %s, %s %s" % (tien(dt.get("vao")), tien(dt.get("ra")),
			"dư ra" if rong >= 0 else "hụt", tien(abs(rong)))
		if dt_truoc:
			s += " (tuần trước vào %s, ra %s)" % (tien(dt_truoc.get("vao")), tien(dt_truoc.get("ra")))
		ra.append(s)
	else:
		ra.append("Dòng tiền: chưa đọc được")
	pt = phan.get("phai_thu")
	ra.append("Khách còn nợ mình: %s" % (tien(pt) if pt is not None else "chưa đọc được"))
	ncc = phan.get("ncc")
	if ncc is None:
		ra.append("Mình còn nợ nhà cung cấp: chưa đọc được")
	else:
		tong, qh = _f(ncc[0]), _f(ncc[1])
		s = "Mình còn nợ nhà cung cấp: %s" % tien(tong)
		if tong > 0 and qh >= tong - 1:
			s += ", máy đang coi toàn bộ là quá hạn"
		elif qh > 0:
			s += ", trong đó quá hạn %s" % tien(qh)
		ra.append(s)
	cc = phan.get("cho_chi")
	if cc is None:
		ra.append("Phiếu chi chờ chuyển tiền: chưa đọc được")
	else:
		s = "Phiếu chi đã duyệt chờ chuyển tiền: %d phiếu, %s" % (int(_f(cc.get("so"))), tien(cc.get("tien")))
		if _f(cc.get("so_cho_duyet")):
			s += "; đang chờ duyệt %d phiếu, %s" % (int(_f(cc.get("so_cho_duyet"))), tien(cc.get("tien_cho_duyet")))
		ra.append(s)
	tt = phan.get("tra_truoc")
	ra.append("Tiền khách gửi trước (của khách, không phải của mình): %s" % (
		tien(tt) if tt is not None else "chưa đọc được"))
	db = phan.get("du_bao")
	if db is None or db.get("cuoi_ky") is None:
		ra.append("Dự báo 30 ngày tới: chưa đọc được")
	else:
		ck = _f(db.get("cuoi_ky"))
		s = "Dự báo 30 ngày tới: %s %s" % ("còn" if ck >= 0 else "âm", tien(abs(ck)))
		qh = _f((db.get("theo_tuan") or {}).get("qua_han"))
		if ck < 0 and qh > 0:
			s += ", vì đang tính cả %s nợ nhà cung cấp quá hạn" % tien(qh)
		if db.get("chua_chot"):
			s += "; còn %d nguồn chưa chốt số dư đầu" % int(_f(db.get("chua_chot")))
		ra.append(s)
	return "Tiền tuần %s - %s" % (ngay_dm(tu), ngay_dm(den)), ra


# --- Tin 5: lãi lỗ tháng

def _so_sanh(a, b):
	a, b = _f(a), _f(b)
	if not b:
		return ""
	p = (a - b) / abs(b) * 100
	return ", %s %s" % ("tăng" if p >= 0 else "giảm", phan_tram(abs(p)))


def soan_thang(thang, thang_truoc, ky, ky_truoc, hh=None):
	"""THUẦN: (tiêu đề, các dòng) tin "Lãi lỗ tháng". ky, ky_truoc: tai_chinh.lai_lo();
	hh: tai_chinh.hao_hut() của tháng, None nếu đọc hỏng."""
	t2 = str(thang_truoc or "")[5:7].lstrip("0") or thang_vn(thang_truoc)
	k, c = ky or {}, ky_truoc or {}
	ra = [
		"Doanh thu thuần: %s (tháng %s: %s%s)" % (tien(k.get("doanh_thu_thuan")), t2, tien(c.get("doanh_thu_thuan")),
			_so_sanh(k.get("doanh_thu_thuan"), c.get("doanh_thu_thuan"))),
		"Giá vốn: %s, food cost %s (tháng %s: %s)" % (tien(k.get("gia_von")), phan_tram(k.get("food_cost")), t2,
			phan_tram(c.get("food_cost"))),
		"Lãi gộp: %s (%s)" % (tien(k.get("lai_gop")), phan_tram(k.get("ti_le_lai_gop"))),
		"Chi phí bán hàng %s, quản lý %s, sản xuất %s" % (tien(k.get("cp_ban_hang")), tien(k.get("cp_quan_ly")),
			tien(k.get("cp_san_xuat"))),
		"Lãi ròng: %s (%s). Tháng %s: %s (%s)" % (tien(k.get("lai_rong")), phan_tram(k.get("ti_le_lai_rong")), t2,
			tien(c.get("lai_rong")), phan_tram(c.get("ti_le_lai_rong"))),
	]
	if hh is None:
		ra.append("Hao hụt kiểm kê: chưa đọc được")
	else:
		la = [d for d in hh.get("dong") or [] if d.get("bat_thuong")]
		if la:
			d = la[0]
			ra.append("Hao hụt kiểm kê: chưa tin được. Kho %s ghi thiếu %s trên %s đã dùng, vì bếp chưa kiểm kê đều" % (
				d.get("kho_ngan") or d.get("kho"), tien(d.get("thieu")), tien(d.get("da_dung"))))
		elif hh.get("ti_le_kiem_ke") is not None:
			ra.append("Hao hụt kiểm kê: %s giá trị nguyên liệu đã dùng; bánh huỷ %s doanh thu" % (
				phan_tram(hh.get("ti_le_kiem_ke")), phan_tram(hh.get("ti_le_huy"))))
	return "Lãi lỗ tháng %s (so với tháng %s)" % (thang_vn(thang), t2), ra


# --- Tin 6: kiểm kê sáng của bếp

def ten_bep(kho):
	"""THUẦN: "Pastry - Nguyên liệu - TV" -> "Pastry"; "Kho Lab - TV" -> "Lab"."""
	t = str(kho or "").strip()
	if t.startswith("Kho "):
		t = t[4:]
	return t.split(" - ")[0].strip()


def soan_kiem_ke_sang(kho, dong, so_den_han=0):
	"""THUẦN: (tiêu đề, các dòng) tin kiểm kê sáng; dong: lich_hom_nay()["dong"]. Rỗng -> None."""
	if not dong:
		return None
	b = ten_bep(kho)
	n = len(dong)
	ra = []
	for d in dong:
		dvt = str(d.get("dvt") or "").strip()
		ra.append(rut(d.get("ten") or d.get("ma_hang"), 70) + (" (%s)" % dvt.lower() if dvt else ""))
	if so_den_han and int(so_den_han) > n:
		ra.append("Kho còn %d món quá hạn đếm, mỗi sáng máy chia tiếp %d món" % (int(so_den_han), MON_DEM_SANG))
	ra.append("Mở app, vào Kiểm kê, bấm \"Đếm hôm nay\" của bếp %s: phiếu tự điền sẵn %d món, chỉ cần cân và ghi số" % (b, n))
	return "Kiểm kê sáng nay, bếp %s (%d món, khoảng %d phút)" % (b, n, n), ra


# ------------------------------------------------------------- chạm Frappe

def _ghi_loi(phan):
	import frappe
	try:
		frappe.log_error(title="Vagabond: tin tài chính (%s)" % phan, message=frappe.get_traceback())
	except Exception:
		pass


def _link(duong):
	from vagabond import lien_ket_app
	return lien_ket_app.link(duong)


def gui_cuoi_ngay():
	"""Lịch 23:35: tin "Tiền cuối ngày" của hôm nay."""
	from frappe.utils import nowdate

	from vagabond import kenh_zalo, tai_chinh

	try:
		hom = nowdate()
		ket = tai_chinh._tinh_tien()
		try:
			dt = tai_chinh.dong_tien_khoang(hom, hom)
		except Exception:
			_ghi_loi("dòng tiền cuối ngày")
			dt = None
		tieu_de, dong = soan_cuoi_ngay(hom, ket, dt)
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "cong_no", tieu_de, dong, link=_link("/tien-hien-co"),
			khoa="tien-cuoi-ngay:%s" % hom, ma_tin="bgd_tien_cuoi_ngay")
	except Exception:
		_ghi_loi("tiền cuối ngày")


def _tk_cong_ty():
	from vagabond import tai_chinh
	return {n["bank_account"] for n in tai_chinh._cac_nguon({})
		if n.get("loai") == tai_chinh.LOAI_NH and n.get("dong_bo") and not n.get("tam_ung") and n.get("bank_account")}


def nhac_tien_ra():
	"""Lịch 08:00: tiền ra khỏi tài khoản công ty quá 24 giờ chưa thuộc chứng từ nào."""
	import frappe
	from frappe.utils import add_days, add_to_date, now_datetime, nowdate

	from vagabond import kenh_zalo

	try:
		tk = _tk_cong_ty()
		if not tk:
			return
		moc = add_to_date(now_datetime(), hours=-GIO_CHUA_GAN)
		rows = frappe.db.sql("""select name, bank_account, withdrawal, unallocated_amount, date, description
			from `tabBank Transaction` where docstatus = 1 and withdrawal > 0 and date >= %s and creation <= %s
			and ifnull(unallocated_amount, withdrawal) > 1 and bank_account in %s""",
			(add_days(nowdate(), -NGAY_XET_TIEN_RA), moc, tuple(tk)), as_dict=True)
		gds = [{"ten": r.name, "tk": r.bank_account, "ra": r.withdrawal,
			"con": r.unallocated_amount if r.unallocated_amount is not None else r.withdrawal,
			"ngay": str(r.date), "mo_ta": r.description} for r in rows]
		kq = soan_tien_ra(loc_tien_ra(gds, tk))
		if not kq:
			return
		kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", kq[0], kq[1], link=_link("/doi-soat-chuyen-khoan"),
			nguoi="Kế toán", han="trong ngày", khoa="tien-ra-chua-gan:%s" % nowdate(), ma_tin="kt_tien_ra_chua_gan")
	except Exception:
		_ghi_loi("tiền ra chưa gắn")


def _ten_ket(quay):
	try:
		from vagabond import tai_chinh
		for n in tai_chinh._cac_nguon({}):
			if n.get("nguon") == "tm:%s" % quay:
				return n.get("ten") or quay
	except Exception:
		pass
	return "Két %s" % quay


def bao_ket_lech(doc, bang):
	"""Gọi từ ca_quay.chot_ca, sau khi lưu ca và TRƯỚC commit: tin nằm cùng giao dịch
	với biên bản chốt ca. Không ném lỗi ra ngoài (bao() tự lo, phần soạn bọc try)."""
	import frappe

	from vagabond import kenh_zalo

	try:
		ten_nguoi = ""
		if doc.get("nguoi_chot"):
			ten_nguoi = frappe.db.get_value("User", doc.get("nguoi_chot"), "full_name") or doc.get("nguoi_chot")
		kq = soan_ket_lech(_ten_ket(doc.get("quay")), doc.get("mo_luc"), doc.get("chot_luc"), doc.get("tien_le_dau_ca"),
			bang, doc.get("ly_do_lech"), ten_nguoi)
		if not kq:
			return
		kenh_zalo.bao_hoac_ghi_loi("canh_bao", "ban_hang", kq[0], kq[1], link=_link("/tien-hien-co"),
			nguoi="Quản lý cửa hàng", han="trong ngày", khoa="ket-lech:%s" % doc.get("name"),
			nguon=doc.get("name"), ma_tin="bgd_ket_lech")
	except Exception:
		_ghi_loi("két lệch")


def _phan(ham):
	try:
		return ham()
	except Exception:
		_ghi_loi("bản tin tuần: %s" % getattr(ham, "__name__", ""))
		return None


def tin_tuan(hom_nay=None):
	"""(tiêu đề, dòng) của tuần thứ Hai tới Chủ nhật ngay trước hom_nay. Không gửi."""
	from frappe.utils import add_days, getdate, nowdate

	from vagabond import tai_chinh as tc

	hn = getdate(hom_nay or nowdate())
	tu, den = add_days(hn, -7), add_days(hn, -1)
	dt = _phan(lambda: tc.dong_tien_khoang(tu, den))
	dt_truoc = _phan(lambda: tc.dong_tien_khoang(add_days(tu, -7), add_days(tu, -1)))

	def ncc():
		_, tong, qh = tc._ncc()
		return tong, qh

	def tra_truoc():
		return tc._tra_truoc()[0]

	phan = {"phai_thu": _phan(tc._phai_thu), "ncc": _phan(ncc), "cho_chi": _phan(tc._cho_chi),
		"tra_truoc": _phan(tra_truoc), "du_bao": _phan(tc.du_bao_30_tinh)}
	return soan_tuan(tu, den, dt, dt_truoc, phan)


def gui_tuan():
	"""Lịch thứ Hai 08:00: bản tin tiền tuần trước."""
	from frappe.utils import nowdate

	from vagabond import kenh_zalo

	try:
		hom = nowdate()
		tieu_de, dong = tin_tuan(hom)
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "cong_no", tieu_de, dong, link=_link("/tong-quan-tai-chinh"),
			khoa="tien-tuan:%s" % hom, ma_tin="bgd_tien_tuan")
	except Exception:
		_ghi_loi("bản tin tuần")


def tin_thang(hom_nay=None):
	"""(tiêu đề, dòng) lãi lỗ của tháng trước hom_nay. Không gửi."""
	from frappe.utils import getdate, nowdate

	from vagabond import tai_chinh as tc
	from vagabond.tin_hao_hut import ten_kho_ngan

	hn = getdate(hom_nay or nowdate())
	t = tc.thang_truoc("%04d-%02d" % (hn.year, hn.month))
	tt = tc.thang_truoc(t)
	tu, den = tc.khoang_thang(t)
	tu2, den2 = tc.khoang_thang(tt)
	ky = tc.lai_lo(tc._gl_ky(tu, den))
	ky_truoc = tc.lai_lo(tc._gl_ky(tu2, den2))
	try:
		kk, dung, huy = tc._hao_hut_so(tu, den)
		hh = tc.hao_hut(kk, dung, huy, ky["doanh_thu_thuan"])
		for d in hh.get("dong") or []:
			d["kho_ngan"] = ten_kho_ngan(d.get("kho"))
	except Exception:
		_ghi_loi("hao hụt tháng")
		hh = None
	return soan_thang(t, tt, ky, ky_truoc, hh)


def gui_thang():
	"""Lịch ngày 05 lúc 08:00: lãi lỗ tháng trước."""
	from frappe.utils import nowdate

	from vagabond import kenh_zalo

	try:
		hom = nowdate()
		tieu_de, dong = tin_thang(hom)
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "cong_no", tieu_de, dong, link=_link("/lai-lo-thang"),
			khoa="lai-lo-thang:%s" % hom[:7], ma_tin="bgd_lai_lo_thang")
	except Exception:
		_ghi_loi("lãi lỗ tháng")


def nhac_kiem_ke_sang():
	"""Lịch 07:30: mỗi kho bếp một tin "việc cần làm" với các món máy chia hôm nay."""
	from frappe.utils import nowdate

	from vagabond import kenh_zalo, kiem_ke

	hom = nowdate()
	for kho in kiem_ke.kho_bep():
		try:
			lich = kiem_ke.lich_kho(kho, MON_DEM_SANG)
			kq = soan_kiem_ke_sang(kho, lich.get("dong"), lich.get("tong_den_han"))
			if not kq:
				continue
			kenh_zalo.bao_hoac_ghi_loi("viec", "kho", kq[0], kq[1], link=_link("/kiem-ke"), han=HAN_DEM_SANG,
				khoa="kiem-ke-sang:%s:%s" % (kho, hom), ma_tin="bep_kiem_ke_sang")
		except Exception:
			_ghi_loi("kiểm kê sáng %s" % kho)
