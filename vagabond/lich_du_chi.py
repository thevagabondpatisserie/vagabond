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
from datetime import date, timedelta
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
		st = _tien(m.get("so_tien"))
		if hd and hd in con:
			con[hd] = max(Decimal(0), con[hd] - st)
		ra.append({"khoa": "tay:" + m["name"], "nguon": "tay", "ngay": max(_ngay(m.get("ngay")) or t, t), "so_tien": st,
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
	ra = [x for x in ra if x["ngay"] <= den and x["so_tien"] > 0]
	ra.sort(key=lambda x: (x["ngay"], 0 if x.get("co") == "qua_han" else 1, THU_TU[x["nguon"]], str(x.get("han") or ""), x["khoa"]))
	return ra


def theo_ngay(so_du, muc):
	"""Gom khoản chi theo ngày và tính tiền còn lại sau mỗi ngày. THUẦN.

	so_du: số tiền khả dụng (Decimal) hoặc None khi chưa đọc được. Trả dict:
	ngay [{ngay, muc, tong, con_lai, thieu}], tong, thieu_dau (ngày thiếu đầu
	tiên hoặc None), can_thuong_luong (khoản công nợ tới ngày đó, khoản dời được
	nhất đứng trước)."""
	ngay = []
	for x in muc:
		if not ngay or ngay[-1]["ngay"] != x["ngay"]:
			ngay.append({"ngay": x["ngay"], "muc": [], "tong": Decimal(0)})
		ngay[-1]["muc"].append(x)
		ngay[-1]["tong"] += x["so_tien"]
	con = so_du
	dau = None
	for g in ngay:
		if con is None:
			g["con_lai"], g["thieu"] = None, None
			continue
		con = con - g["tong"]
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
	"""Số dư tài khoản chi lúc đọc (SePay), nguồn, giờ đọc, và phần đã chi sau đó."""
	from vagabond import du_chi

	v = du_chi._so_du_tk_chi()
	luc = now_datetime()
	if v is None:
		return {"so_tien": None, "luc": "", "nguon": "Chưa đọc được số dư tài khoản chi từ SePay", "chi_sau": 0}
	# SePay báo số dư mới tối đa một phút (tai_chinh.SEPAY_DEM_GIAY): coi như số
	# dư lúc này, trừ các APP vừa trả trong một phút đó để không đếm thiếu.
	chi = frappe.db.sql("""select ifnull(sum(tong_tien),0) from `tabVagabond Ho So TT`
		where trang_thai='Da thanh toan' and modified > %s""", (luc - timedelta(minutes=1),))[0][0]
	return {"so_tien": flt(v), "luc": str(luc)[:19], "nguon": "Số dư tài khoản chi theo SePay", "chi_sau": flt(chi)}


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
	return [dict(r, khoa=_khoa_nhan(r.nha_cung_cap, r.nguoi_nhan)) for r in frappe.get_all(DT_LICH, filters={"bat": 1},
		fields=["name", "noi_dung", "nguoi_nhan", "nha_cung_cap", "so_tien", "ngay_trong_thang", "so_thang_thay", "ngoai_le"],
		limit_page_length=0)]


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
		for r in frappe.get_all("Purchase Invoice", filters={"docstatus": ["<", 2], "supplier": ["in", ds_ncc],
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
		"qua_ngay": x.get("qua_ngay") or 0, "thang": x.get("thang") or "", "dot": x.get("dot") or ""}


@frappe.whitelist()
def lich(so_ngay=SO_NGAY_XEM):
	"""Màn Lịch dự chi: tiền khả dụng, các khoản theo ngày, cảnh báo thiếu."""
	ho = _ho()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi")
	t = getdate(nowdate())
	den = t + timedelta(days=max(7, min(cint(so_ngay) or SO_NGAY_XEM, 120)))
	sd = so_du_kha_dung()
	hd = _hd_no()
	app = _app_song()
	tay_tat_ca = [dict(r) for r in frappe.get_all(DT_MUC, filters={"trang_thai": ["!=", MUC_HUY]},
		fields=["name", "lich", "thang"], limit_page_length=0)]
	tay = _tay(app)
	lc = _lich()
	muc = ghep_muc(t, den, hd, _dot_dong(), app, tay, lc, _da_co(lc, hd, tay_tat_ca, t))
	kd = tien_kha_dung(sd["so_tien"], sd["chi_sau"])
	kq = theo_ngay(kd, muc)
	return {
		"hom_nay": str(t), "den": str(den),
		"so_du": {"so_tien": flt(kd) if kd is not None else None, "so_du_tk": sd["so_tien"], "chi_sau": sd["chi_sau"],
			"luc": sd["luc"], "nguon": sd["nguon"]},
		"du_kien_ve": {"so_tien": None, "ghi_chu": "Chưa tính tiền dự kiến về: chưa có nguồn số liệu tin được (doanh thu sàn, công nợ khách)."},
		"ngay": [{"ngay": str(g["ngay"]), "tong": flt(g["tong"]), "con_lai": flt(g["con_lai"]) if g["con_lai"] is not None else None,
			"thieu": flt(g["thieu"]) if g["thieu"] is not None else None, "muc": [_cho_man_muc(x) for x in g["muc"]]} for g in kq["ngay"]],
		"tong": flt(kq["tong"]),
		"thieu_dau": {"ngay": str(kq["thieu_dau"]["ngay"]), "so_tien": flt(kq["thieu_dau"]["so_tien"])} if kq["thieu_dau"] else None,
		"can_thuong_luong": [_cho_man_muc(x) for x in kq["can_thuong_luong"][:8]],
		"lich_chi": [{"name": l["name"], "noi_dung": l["noi_dung"], "nguoi_nhan": l["nguoi_nhan"], "so_tien": flt(l["so_tien"]),
			"ngay_trong_thang": cint(l["ngay_trong_thang"]), "so_thang_thay": cint(l.get("so_thang_thay")),
			"ngoai_le": l.get("ngoai_le") or ""} for l in lc],
		"quyen": {"sua": 1 if (_vai() & ho.VAI_LAP) else 0},
	}


def _ncc_theo_ten(ten):
	ten = (ten or "").strip()
	if not ten:
		return None
	if frappe.db.exists("Supplier", ten):
		return ten
	return frappe.db.get_value("Supplier", {"supplier_name": ten}, "name")


@frappe.whitelist(methods=["POST"])
def luu_muc(name=None, ngay=None, noi_dung=None, so_tien=None, nguoi_nhan=None, ly_do=None, hoa_don=None):
	"""Nút Lưu dự chi nháp: thêm mới hoặc sửa một dự chi tay còn nháp."""
	ho = _ho()
	_chan(ho.VAI_LAP, "thêm dự chi")
	try:
		x = kiem_muc({"ngay": ngay, "noi_dung": noi_dung, "so_tien": so_tien, "nguoi_nhan": nguoi_nhan, "ly_do": ly_do, "hoa_don": hoa_don})
	except ValueError as e:
		frappe.throw(str(e))
	if x["hoa_don"] and not frappe.db.exists("Purchase Invoice", {"name": x["hoa_don"], "docstatus": 1}):
		frappe.throw("Không có hoá đơn mua đã ghi sổ mã %s. Để trống ô hoá đơn nếu khoản này chưa có hoá đơn." % x["hoa_don"])
	ncc = _ncc_theo_ten(x["nguoi_nhan"])
	if x["hoa_don"] and not ncc:
		ncc = frappe.db.get_value("Purchase Invoice", x["hoa_don"], "supplier")
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
def huy_muc(name, ly_do=""):
	ho = _ho()
	_chan(ho.VAI_LAP, "huỷ dự chi")
	doc = frappe.get_doc(DT_MUC, name, for_update=True)
	if doc.trang_thai != MUC_NHAP:
		return {"name": doc.name, "trang_thai": doc.trang_thai}
	doc.trang_thai = MUC_HUY
	doc.ly_do = ((doc.ly_do or "") + ("\nHuỷ: " + ly_do.strip() if (ly_do or "").strip() else "")).strip()
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "trang_thai": doc.trang_thai}


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
def chi_tiet_muc(name):
	ho = _ho()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi")
	d = frappe.get_doc(DT_MUC, name)
	return {"name": d.name, "ngay": _str(d.ngay), "noi_dung": d.noi_dung, "so_tien": flt(d.so_tien), "nguoi_nhan": d.nguoi_nhan or "",
		"ly_do": d.ly_do or "", "hoa_don": d.hoa_don or "", "trang_thai": d.trang_thai, "ho_so_app": d.ho_so_app or "",
		"nguon": d.nguon or NGUON_TAY}


@frappe.whitelist()
def chon_hoa_don(tu_khoa=""):
	"""Hoá đơn mua còn nợ để gắn vào dự chi (ô Hoá đơn công nợ)."""
	ho = _ho()
	_chan(ho.VAI_LAP, "chọn hoá đơn công nợ")
	q = (tu_khoa or "").strip()
	f = {"docstatus": 1, "outstanding_amount": [">", 0]}
	rows = frappe.get_all("Purchase Invoice", filters=f, or_filters=[["name", "like", "%" + q + "%"], ["supplier_name", "like", "%" + q + "%"],
		["bill_no", "like", "%" + q + "%"]] if q else None, fields=["name", "supplier_name", "bill_no", "outstanding_amount"],
		order_by="posting_date desc", limit_page_length=30)
	return [{"name": r.name, "ten": r.supplier_name, "so": r.bill_no or "", "con_no": flt(r.outstanding_amount)} for r in rows]


@frappe.whitelist(methods=["POST"])
def luu_lich(name=None, noi_dung=None, nguoi_nhan=None, so_tien=None, ngay_trong_thang=20, bat=1, ngoai_le=None, so_thang_thay=None):
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
	doc.update({"noi_dung": noi_dung.strip()[:140], "nguoi_nhan": (nguoi_nhan or "").strip()[:140],
		"nha_cung_cap": _ncc_theo_ten(nguoi_nhan), "so_tien": flt(so), "ngay_trong_thang": n, "bat": cint(bat)})
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
	co = {_khoa_nhan(r.nha_cung_cap, r.nguoi_nhan) for r in frappe.get_all(DT_LICH, fields=["nha_cung_cap", "nguoi_nhan"], limit_page_length=0)}
	thang = sorted({thang_cua(r["ngay"]) for r in ls if r.get("ngay")})
	return {"thang_doc_duoc": thang, "goi_y": [dict(x, so_tien_goi_y=flt(x["so_tien_goi_y"]), da_co=1 if x["khoa"] in co else 0)
		for x in hoc_lich(ls)][:40]}


