"""Kiem banh ngay: thay bang Lark ghi tay bang so dem tu Pancake.

Nguyen tac cot loi (chot voi anh Viet 01/08/2026):
- KHONG co cot sua tay "phat sinh". Chot khach nao la tao don Pancake ngay
  cho khach do - don chinh la "giu cho". May dem, khong ai phai nho.
- "Da dat"    = don giao hom nay, tao TRUOC hom nay.
- "Phat sinh" = don giao hom nay, tao TRONG hom nay.
- Co the ban  = ton dau + bep san xuat - da dat - phat sinh.

Ky thuat da do that:
- Loc don theo ngay giao: updateStatus=estimate_delivery_date kem
  startDateTime/endDateTime la UNIX GIAY (truyen ISO thi Pancake tra 0 don
  ma khong bao loi - nga o day mot lan roi).
- Trang thai loai khoi phep dem: 6 canceled, 7 removed.
"""

import json
from datetime import datetime, timedelta

import frappe
import requests
from frappe.utils import add_days, getdate, now_datetime

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

BO_QUA_TT = {6, 7}  # da huy, da xoa
MAX_TRANG = 10

# Chi theo doi banh o (ma BAWC...). Phu kien, phi giao, hop nen... khong
# thuoc bang kiem banh - anh Viet chot 01/08.
TIEN_TO_MA = "BAWC"

# Man hinh tu goi dong bo lien tuc; chan doi lai Pancake day hon muc nay.
GIAN_CACH_DONG_BO = 12  # giay


def _khoang_unix(ngay):
	"""Nua dem den nua dem cua mot ngay theo gio Viet Nam, ra unix giay."""
	from zoneinfo import ZoneInfo

	d = getdate(ngay)
	dau = datetime(d.year, d.month, d.day, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
	return int(dau.timestamp()), int((dau + timedelta(days=1)).timestamp()) - 1


def _keo_don(c, k, update_status, dau, cuoi):
	"""Keo het don trong khoang thoi gian, lat qua tung trang."""
	ra = []
	for trang in range(1, MAX_TRANG + 1):
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
			params={
				"api_key": k,
				"updateStatus": update_status,
				"startDateTime": dau,
				"endDateTime": cuoi,
				"page_size": 100,
				"page_number": trang,
			},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
		ds = (r.json() or {}).get("data") or []
		ra.extend(ds)
		if len(ds) < 100:
			break
	return ra


def _dem_banh(dons):
	"""Gop so luong theo ma hang, chi lay banh o BAWC.

	Tra ve (dem, ten, hinh) - ten va anh lay ngay tu variation_info trong
	don, khoi ton them luot goi nao.
	"""
	dem, ten, hinh = {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		for it in o.get("items") or []:
			vi = it.get("variation_info") or {}
			ma = str(vi.get("display_id") or it.get("variation_id") or "").strip()
			if not ma.upper().startswith(TIEN_TO_MA):
				continue
			dem[ma] = dem.get(ma, 0) + int(it.get("quantity") or 0)
			if vi.get("name"):
				ten[ma] = vi["name"]
			anh = vi.get("images") or []
			if anh and anh[0]:
				hinh[ma] = anh[0]
	return dem, ten, hinh


def _lay_hoac_tao(ngay):
	ma = "KB-%s" % getdate(ngay)
	if frappe.db.exists("Kiem Banh Ngay", ma):
		return frappe.get_doc("Kiem Banh Ngay", ma)
	doc = frappe.new_doc("Kiem Banh Ngay")
	doc.ngay = getdate(ngay)
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def dong_bo(ngay=None):
	"""Dem lai "da dat" va "phat sinh" cua mot ngay tu Pancake.

	Chay tay bang nut tren man hinh, va tu dong 5 phut mot lan.
	"""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chua dien khoa Pancake trong Vagabond Settings")

	ngay = getdate(ngay) if ngay else getdate()

	# Man hinh cua moi nhan vien tu goi ham nay lien tuc. Vua dong bo xong
	# trong vong GIAN_CACH_DONG_BO giay thi tra bang luon, khong goi lai
	# Pancake - vua nhanh vua khoi lam phien API cua nguoi ta.
	ma_doc = "KB-%s" % ngay
	if frappe.db.exists("Kiem Banh Ngay", ma_doc):
		luc = frappe.db.get_value("Kiem Banh Ngay", ma_doc, "dong_bo_luc")
		if luc and (now_datetime() - luc).total_seconds() < GIAN_CACH_DONG_BO:
			return bang(ngay)

	dau, cuoi = _khoang_unix(ngay)

	giao_hom_nay = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	tao_hom_nay = _keo_don(c, k, "inserted_at", dau, cuoi)
	ma_tao_hom_nay = {o.get("id") for o in tao_hom_nay}

	# Phat sinh la don GIAO hom nay nam trong nhom TAO hom nay; con lai la da dat.
	ps_don = [o for o in giao_hom_nay if o.get("id") in ma_tao_hom_nay]
	dd_don = [o for o in giao_hom_nay if o.get("id") not in ma_tao_hom_nay]
	dem_dd, ten1, hinh1 = _dem_banh(dd_don)
	dem_ps, ten2, hinh2 = _dem_banh(ps_don)
	ten1.update(ten2)
	hinh1.update(hinh2)

	doc = _lay_hoac_tao(ngay)
	# Don dong khong phai banh o (phi giao, phu kien) lot vao tu ban truoc.
	doc.dong = [d for d in doc.dong if str(d.ma_hang or "").upper().startswith(TIEN_TO_MA)]
	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_dd) + list(dem_ps)):
		if ma not in co:
			d = doc.append("dong", {"ma_hang": ma, "ten_banh": ten1.get(ma, "")})
			co[ma] = d
		elif ten1.get(ma) and not co[ma].ten_banh:
			co[ma].ten_banh = ten1[ma]
	for ma, d in co.items():
		d.da_dat = dem_dd.get(ma, 0)
		d.phat_sinh = dem_ps.get(ma, 0)
		if hinh1.get(ma) and not d.hinh:
			d.hinh = hinh1[ma]

	doc.dong_bo_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(ngay)


def dong_bo_tu_dong():
	"""Cho scheduler goi. Nuot loi de khong lam ban nhat ky he thong moi 5 phut."""
	try:
		dong_bo()
	except Exception:
		frappe.log_error(title="Vagabond: dong bo kiem banh loi", message=frappe.get_traceback())


@frappe.whitelist()
def bang(ngay=None):
	"""Du lieu cho man hinh dien thoai."""
	ngay = getdate(ngay) if ngay else getdate()
	ma = "KB-%s" % ngay
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		return {"ngay": str(ngay), "co_so": 0, "dong": []}
	doc = frappe.get_doc("Kiem Banh Ngay", ma)
	return {
		"ngay": str(ngay),
		"co_so": 1,
		"tinh_trang": doc.tinh_trang,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"chot_luc": str(doc.chot_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang, "ten_banh": d.ten_banh, "hinh": d.hinh or "",
				"ton_cu": d.ton_cu or 0, "nsx_cu": str(d.nsx_cu or ""),
				"ton_d2": d.ton_d2 or 0, "nsx_d2": str(d.nsx_d2 or ""),
				"ton_d1": d.ton_d1 or 0, "nsx_d1": str(d.nsx_d1 or ""),
				"sx": d.sx or 0, "da_dat": d.da_dat or 0,
				"phat_sinh": d.phat_sinh or 0, "co_the_ban": d.co_the_ban or 0,
			}
			for d in doc.dong
		],
	}


SUA_DUOC = {"ton_cu", "ton_d2", "ton_d1", "sx"}


@frappe.whitelist()
def luu_o(ngay, ma_hang, truong, gia_tri):
	"""Sua mot o tu dien thoai: ton dau (sales kiem tu) hoac san xuat (bep).

	Cac cot may dem (da dat, phat sinh, co the ban) KHONG sua duoc tu day -
	do la ca ly do phan he nay ton tai.
	"""
	if truong not in SUA_DUOC:
		frappe.throw("Cot nay may tu dem, khong sua tay duoc")
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % getdate(ngay))
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngay nay da chot so, khong sua nua")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			d.set(truong, max(0, int(gia_tri or 0)))
			doc.save()  # giu quyen that cua nguoi dang sua, de con vet ai sua gi
			frappe.db.commit()
			return {"ok": 1, "co_the_ban": d.co_the_ban}
	frappe.throw("Khong thay ma hang %s" % ma_hang)


@frappe.whitelist()
def them_dong(ngay, ma_hang):
	"""Bep them banh se lam hom nay ma chua co don nao."""
	c = cfg()
	k = key(c, "pancake_api_key")
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	if not ma_hang.upper().startswith(TIEN_TO_MA):
		frappe.throw("Bang nay chi theo doi banh o (ma %s...)" % TIEN_TO_MA)
	doc = _lay_hoac_tao(ngay)
	if any(d.ma_hang == ma_hang for d in doc.dong):
		frappe.throw("Ma nay da co trong bang")
	ten, anh = "", ""
	try:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma_hang, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() == ma_hang.lower():
				ten = ((v.get("product") or {}).get("name")) or v.get("name") or ""
				ds_anh = v.get("images") or ((v.get("product") or {}).get("images")) or []
				anh = ds_anh[0] if ds_anh else ""
				break
	except Exception:
		pass
	doc.append("dong", {"ma_hang": ma_hang, "ten_banh": ten, "hinh": anh})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ten_banh": ten}


@frappe.whitelist()
def chot_ngay(ngay=None):
	"""Chot so cuoi ngay: so con lai chay sang ton dau ngay mai, theo lo cu truoc.

	Ban truoc lay hang cu truoc (dung nhu sales tu van clear hang ton), nen
	phep tru cung an vao lo cu truoc: ton_cu -> ton_d2 -> ton_d1 -> sx.
	Phan con du doi sang ngay mai lui mot bac tuoi.
	"""
	ngay = getdate(ngay) if ngay else getdate()
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % ngay)
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngay %s da chot roi" % ngay)

	# Dong bo lan cuoi cho so moi nhat truoc khi khoa.
	dong_bo(ngay)
	doc.reload()

	mai = _lay_hoac_tao(add_days(ngay, 1))
	co_mai = {d.ma_hang: d for d in mai.dong}

	for d in doc.dong:
		ban = (d.da_dat or 0) + (d.phat_sinh or 0)
		lo = [
			[d.ton_cu or 0, d.nsx_cu],
			[d.ton_d2 or 0, d.nsx_d2],
			[d.ton_d1 or 0, d.nsx_d1],
			[d.sx or 0, ngay],
		]
		for cap in lo:
			an = min(cap[0], ban)
			cap[0] -= an
			ban -= an
		# lo[0]+lo[1] don thanh "cu hon" cua ngay mai, lay NSX cu nhat lam moc
		cu = lo[0][0] + lo[1][0]
		nsx_cu = lo[0][1] if lo[0][0] else (lo[1][1] if lo[1][0] else None)
		if not (cu or lo[2][0] or lo[3][0]):
			continue
		m = co_mai.get(d.ma_hang)
		if not m:
			m = mai.append("dong", {"ma_hang": d.ma_hang, "ten_banh": d.ten_banh})
			co_mai[d.ma_hang] = m
		m.ton_cu = cu
		m.nsx_cu = nsx_cu
		m.ton_d2 = lo[2][0]
		m.nsx_d2 = lo[2][1]
		m.ton_d1 = lo[3][0]
		m.nsx_d1 = ngay if lo[3][0] else None

	mai.save(ignore_permissions=True)
	doc.tinh_trang = "Da chot"
	doc.chot_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ngay_mai": str(add_days(ngay, 1))}


@frappe.whitelist(allow_guest=True)
def co_the_ban_hom_nay():
	"""Cho trang dat banh: chi tra cap ma - so luong, khong lo gi khac."""
	ngay = getdate()
	ma = "KB-%s" % ngay
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		return {"ngay": str(ngay), "banh": {}}
	doc = frappe.get_doc("Kiem Banh Ngay", ma)
	return {
		"ngay": str(ngay),
		"banh": {d.ma_hang: d.co_the_ban for d in doc.dong if (d.co_the_ban or 0) > 0},
	}
