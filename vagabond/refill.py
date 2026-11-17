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


def chuan_refill(so, tu, den, hom_nay, tu_cu=None):
	"""Ô người nhập -> (so, tu, den) để lưu. THUẦN.

	Số 0 là bỏ refill (trả 0, None, None). Số trống thì báo, vì ô đếm của bếp
	không có số mặc định. v660: sửa một đợt đang chạy thì ngày có bánh đã qua
	vẫn nhận nếu giữ đúng ngày cũ `tu_cu` (chỉ sửa số hay ngày nhận tới).
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
	if t < hom_nay and t != ngay(tu_cu):
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


def dot_cua(refill, ma, ngay_giao):
	"""Đợt refill của mã có khoảng ngày chứa ngày giao, hoặc None. THUẦN.

	refill: {mã: [đợt {so, tu, den}, ...]} đã lọc hiệu lực (v660: một bánh nhiều
	đợt, các đợt không trùng ngày nên mỗi ngày giao thuộc nhiều nhất một đợt).
	Còn nhận cả dạng cũ {mã: đợt} để chỗ gọi chưa đổi không vỡ.
	"""
	ds = (refill or {}).get(ma)
	if isinstance(ds, dict):
		ds = [ds]
	for r in ds or []:
		if trong_khoang(ngay_giao, r.get("tu"), r.get("den")):
			return r
	return None


def ngay_cua_refill(refill, ma, ngay_giao):
	"""Ngày giao của mã này có thuộc một đợt refill đang hiệu lực không. THUẦN."""
	return dot_cua(refill, ma, ngay_giao) is not None


def theo_ngay(refill, ngay_giao):
	"""{mã: đợt chứa ngày giao}: dùng cho cửa nhận đơn của MỘT ngày nhận. THUẦN."""
	ra = {}
	for ma in refill or {}:
		r = dot_cua(refill, ma, ngay_giao)
		if r:
			ra[ma] = r
	return ra


def doc_dot(d):
	"""Các đợt refill ghi trên một dòng bảng BTP. THUẦN.

	v660: ô `refill_dot` là danh sách JSON [{id, so, tu, den, da_dat}]. Dòng
	chưa nâng (ô trống) thì đọc ba ô cũ so_refill, refill_tu, refill_den thành
	một đợt mang id "cu". Ô đã có chữ, kể cả "[]", thì KHÔNG đọc ba ô cũ nữa:
	một nguồn. Đọc bằng getattr: dòng có thể là Document, dict-chấm hay SQL.
	"""
	import json

	tho = getattr(d, "refill_dot", None)
	if tho is None and isinstance(d, dict):
		tho = d.get("refill_dot")
	if str(tho or "").strip():
		try:
			ds = json.loads(tho)
		except ValueError:
			ds = []
		ra = []
		for x in ds if isinstance(ds, list) else []:
			if isinstance(x, dict) and ngay(x.get("tu")) and ngay(x.get("den")):
				ra.append({"id": str(x.get("id") or ""), "so": int(x.get("so") or 0), "tu": ngay(x.get("tu")),
					"den": ngay(x.get("den")), "da_dat": x.get("da_dat")})
		return ra
	so = getattr(d, "so_refill", None) if not isinstance(d, dict) else d.get("so_refill")
	tu = getattr(d, "refill_tu", None) if not isinstance(d, dict) else d.get("refill_tu")
	den = getattr(d, "refill_den", None) if not isinstance(d, dict) else d.get("refill_den")
	if int(so or 0) > 0 and ngay(tu) and ngay(den):
		return [{"id": "cu", "so": int(so), "tu": ngay(tu), "den": ngay(den), "da_dat": None}]
	return []


def ghi_dot(ds):
	"""Danh sách đợt -> chuỗi JSON để lưu vào ô refill_dot. THUẦN."""
	import json

	return json.dumps([{"id": x["id"], "so": int(x["so"]), "tu": ngay(x["tu"]).isoformat(), "den": ngay(x["den"]).isoformat(),
		"da_dat": x.get("da_dat")} for x in sorted(ds, key=lambda x: (ngay(x["tu"]), x["id"]))], ensure_ascii=False)


def dot_trung(ds, tu, den, bo_id=None):
	"""Đợt trong `ds` có khoảng ngày chạm vào [tu, den], bỏ qua đợt `bo_id`. THUẦN."""
	t, d = ngay(tu), ngay(den)
	for x in ds or []:
		if x.get("id") == bo_id:
			continue
		if ngay(x["tu"]) <= d and t <= ngay(x["den"]):
			return x
	return None


def mo_ta_dot(x):
	"""'20 bánh 14/11 tới 20/11' cho nhật ký và câu báo. THUẦN."""
	if not x:
		return ""
	return "%d bánh %s tới %s" % (int(x["so"]), ngay(x["tu"]).strftime("%d/%m"), ngay(x["den"]).strftime("%d/%m"))


def luu_dot(ds, id_dot, so, tu, den, hom_nay, id_moi=None):
	"""Thêm, sửa hoặc bỏ MỘT đợt trong danh sách đợt của một bánh. THUẦN.

	id_dot trống là thêm đợt mới (mang id `id_moi`); có id là sửa đúng đợt đó,
	số 0 là bỏ đợt đó. Anh Việt chọn 15/11/2026: hai đợt của cùng một bánh
	KHÔNG được trùng ngày, để mỗi ngày giao chỉ thuộc một đợt và số Còn của
	từng đợt luôn rõ. Đợt đã qua ngày không sửa được. Trả (ds mới, đợt trước,
	đợt sau) với đợt trước, sau là None khi thêm, bỏ.
	"""
	ds = [dict(x) for x in ds or []]
	cu = None
	if id_dot:
		cu = next((x for x in ds if x["id"] == id_dot), None)
		if not cu:
			raise LoiRefill("Đợt refill này không còn trên bảng. Tải lại màn rồi thử lại.")
		if ngay(cu["den"]) < hom_nay:
			raise LoiRefill("Đợt refill này đã qua ngày nhận đơn, không sửa được nữa. Thêm đợt mới.")
	n, t, d = chuan_refill(so, tu, den, hom_nay, tu_cu=cu["tu"] if cu else None)
	if n == 0:
		if not cu:
			raise LoiRefill("Nhập số bánh refill bếp làm được, lớn hơn 0.")
		return [x for x in ds if x["id"] != id_dot], cu, None
	trung = dot_trung([x for x in ds if ngay(x["den"]) >= hom_nay], t, d, bo_id=id_dot)
	if trung:
		raise LoiRefill("Bánh này đã có đợt refill %s tới %s, hai đợt không được trùng ngày. "
			"Làm thêm bánh cho khoảng ngày đó thì sửa số của chính đợt đó, hoặc chọn ngày có bánh sau ngày %s."
			% (ngay(trung["tu"]).strftime("%d/%m"), ngay(trung["den"]).strftime("%d/%m"), ngay(trung["den"]).strftime("%d/%m")))
	moi = {"id": id_dot or id_moi or "", "so": n, "tu": t, "den": d, "da_dat": None}
	if not moi["id"]:
		raise LoiRefill("Thiếu mã đợt refill.")
	return [x for x in ds if x["id"] != id_dot] + [moi], cu, moi


def mo_ta(r):
	"""'có từ T6 14/11, nhận tới 20/11' cho màn bếp. THUẦN."""
	thu = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
	t, d = ngay(r.get("tu")), ngay(r.get("den"))
	if not t or not d:
		return ""
	return "có từ %s %s, nhận tới %s" % (thu[t.weekday()], t.strftime("%d/%m"), d.strftime("%d/%m"))


def kiem_don(hang, ngay_nhan, refill, con, decor_con=None):
	"""Câu nhắc cho đơn web với ngày nhận `ngay_nhan`. THUẦN.

	hang: [{variation_id, quantity}]; refill: {mã: [đợt {so, tu, den, ten}]} hiệu
	lực; con: {mã: số còn của ĐỢT CHỨA ngày nhận}; decor_con: {mã: còn theo Đủ
	decor} cho 3 ngày tới. Mã có refill mà ngày nhận ngoài mọi đợt và không còn
	decor thì nhắc chọn ngày, kể đủ các khoảng đang nhận.
	"""
	ra = []
	g = ngay(ngay_nhan)
	if not g:
		return ra
	for h in hang or []:
		ma = h.get("variation_id")
		ds = (refill or {}).get(ma)
		if isinstance(ds, dict):
			ds = [ds]
		if not ds:
			continue
		ten = ds[0].get("ten") or ma
		sl = int(h.get("quantity") or 0)
		if dot_cua(refill, ma, g):
			c = int((con or {}).get(ma, 0) or 0)
			if sl > c:
				ra.append("%s ngày %s chỉ còn %s cái, quý khách đang chọn %s cái."
					% (ten, g.strftime("%d/%m/%Y"), max(0, c), sl))
		elif not (decor_con and decor_con.get(ma) is not None):
			khoang = " hoặc ".join("từ %s tới %s" % (ngay(r["tu"]).strftime("%d/%m"), ngay(r["den"]).strftime("%d/%m")) for r in ds)
			ra.append("%s nhận giao %s, quý khách chọn ngày nhận trong khoảng này." % (ten, khoang))
	return ra


# ---------------------------------------------------------------- chạm hệ

def hieu_luc_tu_dong(dong, hom_nay):
	"""Dòng bảng BTP -> {mã: [đợt {id, so, tu, den, ten}]} còn nhận đơn, xếp
	theo ngày có bánh. THUẦN. v660: một bánh nhiều đợt (xem doc_dot).

	Đọc bằng getattr: dòng có thể là Document, dict-chấm hay bản ghi SQL thiếu cột.
	"""
	ra = {}
	for d in dong or []:
		ma = getattr(d, "ma_hang", None)
		ten = getattr(d, "ten_banh", None) or ma
		ds = [dict(x, ten=ten) for x in doc_dot(d) if con_hieu_luc(x["so"], x["tu"], x["den"], hom_nay)]
		if ds:
			ra[ma] = sorted(ds, key=lambda x: (x["tu"], x["id"]))
	return ra


def da_qua_tu_dong(dong, hom_nay, so_ngay=60):
	"""Các đợt đã qua ngày nhận đơn trong `so_ngay` gần đây, mới nhất trước. THUẦN.
	Mỗi đợt kèm ma_hang, ten; da_dat là số đã chốt (None: máy chưa chốt số)."""
	moc = hom_nay - timedelta(days=so_ngay)
	ra = []
	for d in dong or []:
		ma = getattr(d, "ma_hang", None)
		for x in doc_dot(d):
			if x["so"] > 0 and moc <= x["den"] < hom_nay:
				ra.append(dict(x, ma_hang=ma, ten=getattr(d, "ten_banh", None) or ma))
	return sorted(ra, key=lambda x: (x["den"], x["ma_hang"]), reverse=True)


def ngay_bat_dau_dem(rf, hom_nay):
	"""Ngày bắt đầu đếm đơn cho các mẻ refill đang nhận. THUẦN.

	Codex 549 (1eefda8): mẻ đã chạy vài ngày thì đơn giao những ngày trước
	trong khoảng đã ăn vào mẻ. Đếm từ hôm nay là mở bán lại mẻ đã hết (mẻ 20,
	ngày 14 đặt đủ 20: ngày 14 còn 0 mà ngày 15 lại còn 20). Đếm từ ngày đầu
	mẻ sớm nhất."""
	return min([hom_nay] + [r["tu"] for ds in (rf or {}).values() for r in ([ds] if isinstance(ds, dict) else ds) if r.get("tu")])


def tieu_thu_phieu_dat(dong, tien_to):
	"""{ngày iso: {mã: số}} bánh ổ phiếu đặt tại quầy ĐÃ ĂN vào mẻ. THUẦN.

	Codex 549 (58ba797): phiếu còn mở tính cả số đặt (phần đã giao lẫn phần còn
	giữ); phiếu đã đóng chỉ tính phần đã giao (lấy số lớn hơn giữa đã giao và
	đã xuất hoá đơn, cùng luật dat_banh.con_giu_cho). Trước đây chỉ đếm phần
	còn giữ chỗ, nên phiếu 20 bánh giao xong là mẻ lại "còn 20"."""
	from vagabond.dat_banh import TT_NHA_CHO, la_banh_o

	def so(x):
		try:
			return max(0, int(float(x or 0)))
		except (TypeError, ValueError):
			return 0

	ra = {}
	for d in dong or []:
		ma = str(d.get("item_code") or "").strip().upper()
		g = ngay(d.get("delivery_date"))
		if not g or not la_banh_o(ma, tien_to):
			continue
		da = max(so(d.get("delivered_qty")), so(d.get("da_xuat_hd")))
		n = da if str(d.get("trang_thai") or "").strip() in TT_NHA_CHO else max(da, so(d.get("qty")))
		if n > 0:
			m = ra.setdefault(g.isoformat(), {})
			m[ma] = m.get(ma, 0) + n
	return ra


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
	from vagabond import dat_banh
	from vagabond.dat_banh import TIEN_TO_MA
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
	giu = tieu_thu_phieu_dat(dat_banh.dong_tieu_thu(bd, hn + timedelta(days=TOI_DA_TRUOC + TOI_DA_KHOANG + 1)), TIEN_TO_MA)
	ra = dem_theo_ngay(dons, ngay_tu_iso, giu)
	ids = id_da_dem(dons)
	frappe.cache().set_value(khoa, {"dem": ra, "ids": ids}, expires_in_sec=GIU_GIAY)
	return ra, ids


def tinh(hom_nay=None, moi=False, dong=None):
	"""Số refill cho màn bếp và web: {mã: [đợt {id, so, tu, den, ten, da_dat, con,
	mo_ta}]} và đặt xa ngày {mã: (tổng, ds)}. Đếm đơn hỏng thì `loi` có câu, `con`
	None. Số của một ngày nhận lấy bằng con_theo_ngay."""
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
	for ma, ds in rf.items():
		ra[ma] = []
		for r in ds:
			dd = da_dat_trong((don or {}).get(ma), r["tu"], r["den"]) if don is not None else None
			ra[ma].append(dict(r, tu=r["tu"].isoformat(), den=r["den"].isoformat(), da_dat=dd,
				con=(r["so"] - dd) if dd is not None else None, mo_ta=mo_ta(r)))
	xa = {ma: dat_xa(tn, hn) for ma, tn in (don or {}).items()} if don is not None else {}
	return {"refill": ra, "dat_xa": {m: {"tong": v[0], "ds": v[1]} for m, v in xa.items() if v[0]}, "loi": loi,
		"ids": ids}


def con_theo_ngay(so, ngay_giao):
	"""Từ kết quả `tinh`: {mã: số còn của đợt chứa ngày giao}. THUẦN.
	Mã không có đợt nào chứa ngày đó thì không có khoá; chưa đếm được thì None."""
	ra = {}
	for ma, ds in ((so or {}).get("refill") or {}).items():
		r = dot_cua({ma: ds}, ma, ngay_giao)
		if r:
			ra[ma] = r.get("con")
	return ra


def chot_dot_da_qua(hom_nay=None):
	"""Nhịp mỗi ngày: đợt vừa qua ngày nhận đơn thì đếm lại đơn trong khoảng một
	lần và ghi số đã nhận vào chính đợt đó, để mục Đợt đã xong giữ được số làm,
	số đã nhận, số còn. Giữ 60 ngày rồi gỡ khỏi dòng. Pancake lỗi thì để nhịp
	hôm sau làm, không ghi số đoán."""
	import frappe
	from frappe.utils import getdate

	hn = hom_nay or getdate()
	rows = frappe.db.sql("""select name, ma_hang, ten_banh, so_refill, refill_tu, refill_den, refill_dot
		from `tabBTP Banh O Dong` where parent = 'BTP Banh O' and parenttype = 'BTP Banh O'
		and ifnull(refill_dot, '') != ''""", as_dict=True)
	can = [(r, x) for r in rows for x in doc_dot(r) if x["den"] < hn and x.get("da_dat") is None]
	moc = hn - timedelta(days=60)
	cu = [r for r in rows if any(x["den"] < moc for x in doc_dot(r))]
	if not can and not cu:
		return 0
	don = None
	if can:
		don = dem_va_id(hn, moi=True, tu=min(x["tu"] for _, x in can))[0]
	n = 0
	for r in rows:
		if not any(r is a for a, _ in can) and r not in cu:
			continue
		# Khoá đúng dòng rồi đọc lại: bếp có thể vừa sửa đợt khác của mã này.
		kh = frappe.db.sql("select name, ma_hang, refill_dot from `tabBTP Banh O Dong` where name = %s for update", r.name, as_dict=True)
		if not kh:
			continue
		ds = doc_dot(kh[0])
		moi = []
		for x in ds:
			if x["den"] < moc:
				continue
			if x["den"] < hn and x.get("da_dat") is None and don is not None:
				x = dict(x, da_dat=da_dat_trong(don.get(r.ma_hang), x["tu"], x["den"]))
			moi.append(x)
		chuoi = ghi_dot(moi)
		if chuoi != ghi_dot(ds):
			frappe.db.sql("update `tabBTP Banh O Dong` set refill_dot = %s where name = %s", (chuoi, r.name))
			n += 1
	frappe.db.commit()
	return n


def chot_dot_da_qua_nen():
	"""Cho scheduler gọi: nuốt lỗi, ghi Error Log, nhịp hôm sau làm lại."""
	import frappe

	try:
		chot_dot_da_qua()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Refill: chưa chốt được số đợt đã qua", message=frappe.get_traceback())
