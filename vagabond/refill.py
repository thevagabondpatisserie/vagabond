# -*- coding: utf-8 -*-
"""v646 Refill: mẻ bánh làm sẵn để nhận đơn giao những ngày sau.

Bếp báo 09/11/2026 sau vụ Roman De La Rose 18 đặt xa ngày: bếp tập trung sản
xuất một mẻ lớn (BTP sẵn và đủ decor) để trong tương lai có bánh bán, nhưng bảng
kiểm bánh không có ô để nhập, và không có ngày refill để mời khách mua, khớp
với lịch trên web. Anh Việt duyệt (09/11):
  - Refill có NGÀY CÓ BÁNH và NGÀY NHẬN ĐƠN TỚI (máy điền sẵn có bánh + 6 ngày).
  - Đơn của bánh đó giao trong khoảng refill TRỪ VÀO REFILL, không trừ Đủ decor.
  - Chỉ bếp nhập, như ô BTP sẵn và Đủ decor.

Số refill để NHẬN ĐƠN trước, không cộng vào tồn: đến ngày có bánh bếp vẫn nhập
Bếp làm như mọi ngày.

Phép thuần ở trên, phần chạm hệ ở dưới.
"""

from datetime import date, datetime, timedelta

TOI_DA_TRUOC = 30  # ngày có bánh xa nhất tính từ hôm nay
TOI_DA_KHOANG = 13  # nhận tới xa nhất tính từ ngày có bánh (web hiện 14 ngày)
MAC_DINH_KHOANG = 6  # nhận tới = có bánh + 6 ngày
SO_NGAY_GIU = 3  # hôm nay + 2 ngày kế: ô Còn nhận 3 ngày (btp.SO_NGAY_GIU)
BO_QUA_TT = frozenset({6, 7})  # đơn Pancake huỷ, trả (lib.PANCAKE_BO_QUA)
GIU_GIAY = 300  # đếm đơn tương lai giữ 5 phút, không gọi Pancake mỗi 30 giây


class LoiRefill(ValueError):
	"""Câu cho bếp đọc, đã là tiếng Việt."""


def ngay(v):
	"""Chuỗi, date, datetime -> date. Không đọc được thì None. THUẦN."""
	if v is None or v == "":
		return None
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	try:
		return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
	except ValueError:
		return None


def so_nguyen(v):
	"""Ô số người gõ -> int hoặc None khi để trống. THUẦN."""
	s = str(v if v is not None else "").strip().replace(".", "").replace(",", "")
	if s == "":
		return None
	try:
		return int(float(s))
	except ValueError:
		raise LoiRefill("Số bánh refill phải là số, ví dụ 20.")


def chuan_refill(so, tu, den, hom_nay):
	"""Ô người nhập -> (so, tu, den) để lưu. THUẦN.

	Số 0 là bỏ refill (trả 0, None, None). Số trống thì báo, vì ô đếm của bếp
	không có số mặc định.
	"""
	n = so_nguyen(so)
	if n is None:
		raise LoiRefill("Nhập số bánh refill bếp làm được. Muốn bỏ refill thì nhập 0.")
	if n < 0:
		raise LoiRefill("Số bánh refill không được âm.")
	if n == 0:
		return 0, None, None
	t = ngay(tu)
	if not t:
		raise LoiRefill("Chọn ngày có bánh.")
	if t < hom_nay:
		raise LoiRefill("Ngày có bánh đã qua. Chọn từ hôm nay trở đi.")
	if t > hom_nay + timedelta(days=TOI_DA_TRUOC):
		raise LoiRefill("Ngày có bánh xa quá %d ngày. Chọn ngày gần hơn." % TOI_DA_TRUOC)
	d = ngay(den) or (t + timedelta(days=MAC_DINH_KHOANG))
	if d < t:
		raise LoiRefill("Ngày nhận đơn tới phải từ ngày có bánh trở đi.")
	if d > t + timedelta(days=TOI_DA_KHOANG):
		raise LoiRefill("Nhận đơn tới tối đa %d ngày sau ngày có bánh." % TOI_DA_KHOANG)
	return n, t, d


def con_hieu_luc(so, tu, den, hom_nay):
	"""Refill còn nhận đơn không (chưa qua ngày nhận tới). THUẦN."""
	t, d = ngay(tu), ngay(den)
	return bool(int(so or 0) > 0 and t and d and d >= hom_nay)


def trong_khoang(ngay_giao, tu, den):
	"""Ngày giao có nằm trong khoảng refill không. THUẦN."""
	g, t, d = ngay(ngay_giao), ngay(tu), ngay(den)
	return bool(g and t and d and t <= g <= d)


def dem_theo_ngay(dons, ngay_cua, giu_cho=None):
	"""Đơn Pancake (+ giữ chỗ phiếu đặt) -> {mã: {ngày iso: số}}. THUẦN.

	ngay_cua: hàm đọc ngày giao Việt Nam của một đơn (ngay_pancake.ngay_tu_iso).
	giu_cho: {ngày iso: {mã: số}} của phiếu đặt tại quầy.
	"""
	ra = {}
	for o in dons or []:
		if o.get("status") in BO_QUA_TT:
			continue
		g = ngay(ngay_cua(o.get("estimate_delivery_date")))
		if not g:
			continue
		for it in o.get("items") or []:
			vi = it.get("variation_info") or {}
			ma = str(vi.get("display_id") or it.get("variation_id") or "").strip()
			if not ma:
				continue
			m = ra.setdefault(ma, {})
			m[g.isoformat()] = m.get(g.isoformat(), 0) + int(it.get("quantity") or 0)
	for g, theo_ma in (giu_cho or {}).items():
		for ma, n in (theo_ma or {}).items():
			m = ra.setdefault(ma, {})
			m[str(g)[:10]] = m.get(str(g)[:10], 0) + int(n or 0)
	return ra


def da_dat_trong(theo_ngay, tu, den):
	"""Tổng đơn của một mã giao trong khoảng refill. THUẦN."""
	return sum(n for g, n in (theo_ngay or {}).items() if trong_khoang(g, tu, den))


def dat_xa(theo_ngay, hom_nay):
	"""Đơn giao SAU cửa sổ Còn nhận 3 ngày: (tổng, [(ngày iso, số)]). THUẦN."""
	moc = hom_nay + timedelta(days=SO_NGAY_GIU)
	ds = sorted((g, n) for g, n in (theo_ngay or {}).items() if n and ngay(g) and ngay(g) >= moc)
	return sum(n for _, n in ds), ds


def ngay_cua_refill(refill, ma, ngay_giao):
	"""Ngày giao của mã này có thuộc khoảng refill đang hiệu lực không. THUẦN.

	refill: {mã: {so, tu, den}} đã lọc hiệu lực.
	"""
	r = (refill or {}).get(ma)
	return bool(r and trong_khoang(ngay_giao, r.get("tu"), r.get("den")))


def mo_ta(r):
	"""'có từ T6 14/11, nhận tới 20/11' cho màn bếp. THUẦN."""
	thu = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
	t, d = ngay(r.get("tu")), ngay(r.get("den"))
	if not t or not d:
		return ""
	return "có từ %s %s, nhận tới %s" % (thu[t.weekday()], t.strftime("%d/%m"), d.strftime("%d/%m"))


def kiem_don(hang, ngay_nhan, refill, con, decor_con=None):
	"""Câu nhắc cho đơn web với ngày nhận `ngay_nhan`. THUẦN.

	hang: [{variation_id, quantity}]; refill: {mã: {so, tu, den, ten}} hiệu lực;
	con: {mã: số còn nhận refill}; decor_con: {mã: còn theo Đủ decor} cho 3 ngày tới.
	Mã có refill mà ngày nhận ngoài khoảng và không còn decor thì nhắc chọn ngày.
	"""
	ra = []
	g = ngay(ngay_nhan)
	if not g:
		return ra
	for h in hang or []:
		ma = h.get("variation_id")
		r = (refill or {}).get(ma)
		if not r:
			continue
		ten = r.get("ten") or ma
		sl = int(h.get("quantity") or 0)
		if trong_khoang(g, r.get("tu"), r.get("den")):
			c = int((con or {}).get(ma, 0))
			if sl > c:
				ra.append("%s ngày %s chỉ còn %s cái, quý khách đang chọn %s cái."
					% (ten, g.strftime("%d/%m/%Y"), max(0, c), sl))
		elif not (decor_con and decor_con.get(ma) is not None):
			ra.append("%s nhận giao từ %s tới %s, quý khách chọn ngày nhận trong khoảng này."
				% (ten, ngay(r["tu"]).strftime("%d/%m"), ngay(r["den"]).strftime("%d/%m")))
	return ra


# ---------------------------------------------------------------- chạm hệ

def hieu_luc_tu_dong(dong, hom_nay):
	"""Dòng bảng BTP -> {mã: {so, tu, den, ten}} refill còn nhận đơn. THUẦN.

	Đọc bằng getattr: dòng có thể là Document, dict-chấm hay bản ghi SQL thiếu cột.
	"""
	ra = {}
	for d in dong or []:
		so, tu, den = getattr(d, "so_refill", None), getattr(d, "refill_tu", None), getattr(d, "refill_den", None)
		if con_hieu_luc(so, tu, den, hom_nay):
			ma = getattr(d, "ma_hang", None)
			ra[ma] = {"so": int(so or 0), "tu": ngay(tu), "den": ngay(den), "ten": getattr(d, "ten_banh", None) or ma}
	return ra


def ngay_bat_dau_dem(rf, hom_nay):
	"""Ngày bắt đầu đếm đơn cho các mẻ refill đang nhận. THUẦN.

	Codex 549 (1eefda8): mẻ đã chạy vài ngày thì đơn giao những ngày trước
	trong khoảng đã ăn vào mẻ. Đếm từ hôm nay là mở bán lại mẻ đã hết (mẻ 20,
	ngày 14 đặt đủ 20: ngày 14 còn 0 mà ngày 15 lại còn 20). Đếm từ ngày đầu
	mẻ sớm nhất."""
	return min([hom_nay] + [r["tu"] for r in (rf or {}).values() if r.get("tu")])


def id_da_dem(dons):
	"""Mã mọi đơn Pancake trong lần đếm (kể cả đơn huỷ: Pancake đã biết đơn đó). THUẦN."""
	return sorted({str(o.get("id")) for o in dons or [] if o.get("id") not in (None, "")})


def _refill_hieu_luc(hom_nay=None):
	"""{mã: {so, tu, den, ten}} từ bảng BTP, chỉ refill còn nhận đơn."""
	import frappe
	from frappe.utils import getdate

	return hieu_luc_tu_dong(frappe.get_single("BTP Banh O").dong, hom_nay or getdate())


def don_tuong_lai(hom_nay=None, moi=False, tu=None):
	"""{mã: {ngày: số}} đơn giao từ `tu` (mặc định hôm nay) tới 44 ngày sau hôm nay."""
	return dem_va_id(hom_nay, moi, tu)[0]


def dem_va_id(hom_nay=None, moi=False, tu=None):
	"""({mã: {ngày: số}}, [mã đơn Pancake đã đếm]) cùng MỘT lần kéo Pancake.

	Đếm từ `tu` (ngày đầu mẻ refill sớm nhất, xem ngay_bat_dau_dem) tới 44
	ngày sau hôm nay, cộng giữ chỗ phiếu đặt. Danh sách mã đơn đi kèm để cửa
	giữ suất biết đơn web nào Pancake chưa đếm (giu_ton_web). Giữ 5 phút.
	Gọi Pancake hỏng thì NÉM lỗi: bên gọi phải coi là chưa đếm được, không
	được coi là 0 đơn (nhận lố).
	"""
	import frappe
	from frappe.utils import getdate

	from vagabond import kiem_banh
	from vagabond.dat_banh import TIEN_TO_MA, dong_phieu_dat, gom_giu_cho
	from vagabond.lib import cfg, key
	from vagabond.ngay_pancake import ngay_tu_iso

	hn = hom_nay or getdate()
	bd = min(tu or hn, hn)
	khoa = "vgb_refill_dem:%s:%s" % (hn.isoformat(), bd.isoformat())
	nho = None if moi else frappe.cache().get_value(khoa)
	if nho:
		return nho["dem"], nho["ids"]
	c = cfg()
	k = key(c, "pancake_api_key")
	dau, _ = kiem_banh._khoang_unix(bd)
	_, cuoi = kiem_banh._khoang_unix(hn + timedelta(days=TOI_DA_TRUOC + TOI_DA_KHOANG + 1))
	dons = kiem_banh._keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	dong = dong_phieu_dat()
	giu = gom_giu_cho([dict(d, delivery_date=str(d.get("delivery_date") or "")) for d in dong], TIEN_TO_MA)
	ra = dem_theo_ngay(dons, ngay_tu_iso, giu)
	ids = id_da_dem(dons)
	frappe.cache().set_value(khoa, {"dem": ra, "ids": ids}, expires_in_sec=GIU_GIAY)
	return ra, ids


def tinh(hom_nay=None, moi=False, dong=None):
	"""Số refill cho màn bếp và web: {mã: {so, tu, den, ten, da_dat, con, mo_ta}}
	và đặt xa ngày {mã: (tổng, ds)}. Đếm đơn hỏng thì `loi` có câu, `con` None."""
	import frappe
	from frappe.utils import getdate

	hn = hom_nay or getdate()
	rf = hieu_luc_tu_dong(dong, hn) if dong is not None else _refill_hieu_luc(hn)
	ids = []
	loi = "Chưa đếm được đơn đặt xa ngày từ Pancake, máy thử lại sau ít phút."
	if not rf and moi:
		return {"refill": {}, "dat_xa": {}, "loi": ""}
	if frappe.cache().get_value("vgb_refill_loi") and not moi:
		# Vừa hỏng: nghỉ 1 phút, không để mỗi lượt làm tươi 30 giây gọi lại Pancake.
		don = None
	else:
		try:
			don, ids = dem_va_id(hn, moi=moi, tu=ngay_bat_dau_dem(rf, hn))
			loi = ""
		except Exception:
			frappe.cache().set_value("vgb_refill_loi", "1", expires_in_sec=60)
			frappe.log_error(title="Refill: chưa đếm được đơn tương lai", message=frappe.get_traceback())
			don = None
	ra = {}
	for ma, r in rf.items():
		dd = da_dat_trong((don or {}).get(ma), r["tu"], r["den"]) if don is not None else None
		ra[ma] = dict(r, tu=r["tu"].isoformat(), den=r["den"].isoformat(), da_dat=dd,
			con=(r["so"] - dd) if dd is not None else None, mo_ta=mo_ta(r))
	xa = {ma: dat_xa(tn, hn) for ma, tn in (don or {}).items()} if don is not None else {}
	return {"refill": ra, "dat_xa": {m: {"tong": v[0], "ds": v[1]} for m, v in xa.items() if v[0]}, "loi": loi,
		"ids": ids}
