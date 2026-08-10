"""Kiem banh ngay: thay bang Lark ghi tay bang so dem tu Pancake.

Nguyen tac cot loi (chot voi anh Viet 01/08/2026):
- KHONG co cot sua tay "phat sinh". Chot khach nao la tao don Pancake ngay
  cho khach do - don chinh la "giu cho". May dem, khong ai phai nho.
- "Da dat"    = don giao hom nay, tao TRUOC hom nay.
- "Phat sinh" = don giao hom nay, tao TRONG hom nay.
- "Cho chot"   = don giao hom nay con trang thai Moi (0) - khach dang nhan
  tin tu van, sales tao don giu cho mem, TRU AO vao co the ban (y Loan Anh
  01/08). Khach huy thi huy don, so tu tra lai; chot xong thi don doi trang
  thai, tu nhay sang Da dat / Phat sinh - tru that.
- "Kenh khac" = banh ban qua Grab, Shopee, Be, GreenSM, khach si, quay -
  nhung kenh khong di qua Pancake nen khong co don Pancake de dem. Dem
  thang tu hoa don ban ra trong ngay (08/08/2026, y Loan Anh: truoc day
  phai tao mot don Pancake gia de tru so, thanh ra mot khach hai bill).
- Co the ban  = ton dau + bep san xuat - da dat - phat sinh - cho chot
                - kenh khac.

Ky thuat da do that:
- Loc don theo ngay giao: updateStatus=estimate_delivery_date kem
  startDateTime/endDateTime la UNIX GIAY (truyen ISO thi Pancake tra 0 don
  ma khong bao loi - nga o day mot lan roi).
- Trang thai loai khoi phep dem: 6 canceled, 7 removed.
"""

import json
import re
from datetime import datetime, timedelta

import frappe
import requests
from frappe.utils import add_days, getdate, now_datetime

from vagabond.lib import PANCAKE, TIMEOUT, cache_get, cache_set, cfg, key

BO_QUA_TT = {6, 7}  # da huy, da xoa
MAX_TRANG = 10

# Theo doi banh o (BAWC) va banh si (BAWS) - anh Viet mo them BAWS 02/08.
# Phu kien, phi giao, hop nen... khong thuoc bang kiem banh.
TIEN_TO_MA = ("BAWC", "BAWS")

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

	Tra ve (dem, ten, hinh, khach) - ten, anh va TEN KHACH lay ngay tu don,
	khoi ton them luot goi nao. Ten khach de sales ban giao ca cho nhau.
	"""
	dem, ten, hinh, khach = {}, {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		ten_khach = (o.get("bill_full_name") or "").strip()
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
			if ten_khach and ten_khach not in khach.setdefault(ma, []):
				khach[ma].append(ten_khach)
	return dem, ten, hinh, khach


def _tra_anh_ten(c, k, ma):
	"""Tra anh + ten cua mot ma tu danh muc Pancake, thieu thi lay ben Next.

	Nhieu ma (vi du BAWC00053) co anh o cap SAN PHAM nhung variation nam
	trong don hang lai KHONG nhung anh - dem tu don thi thieu. Ham nay tra
	thang danh muc: uu tien anh cua variation, thieu thi lay anh san pham.

	Ma khong co tren Pancake thi lui ve danh muc Hang hoa ben Next. Han bao
	03/08/2026: BAWC00025 hien tren man kiem banh khong co ten - ly do la
	ma do CHI ton tai ben Next (Banh O Hokkaido, size 16cm), Pancake khong
	co variation nao mang ma nay nen ham tra ve rong, man hinh in ra trong.
	"""
	try:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() == ma.lower():
				ten = ((v.get("product") or {}).get("name")) or v.get("name") or ""
				ds = v.get("images") or ((v.get("product") or {}).get("images")) or []
				return ten, (ds[0] if ds else "")
	except Exception:
		pass
	return _tra_ben_next(ma)


def _tra_ben_next(ma):
	"""Lui ve danh muc Hang hoa ben Next khi Pancake khong co ma."""
	it = frappe.db.get_value("Item", ma, ["item_name", "image"], as_dict=True)
	if not it:
		return "", ""
	anh = it.image or ""
	if anh.startswith("/private"):
		anh = ""
	return it.item_name or "", anh


def _dang_ma_dung(ma):
	"""BAWC/BAWS + it nhat 5 chu so. Chan ma cut kieu "BAWC" go nham.

	Van cho hau to size cu (BAWC00114MINI12CM) vi don cu con mang ma do.
	"""
	return bool(re.match(r"^(BAWC|BAWS)\d{5}", str(ma or "").strip().upper()))


def _co_that(c, k, ma):
	"""Ma co that: co tren Pancake, hoac co trong danh muc Hang hoa ben Next."""
	if frappe.db.exists("Item", ma):
		return True
	ten, _anh = _tra_anh_ten(c, k, ma)
	return bool(ten)


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

	# Chia ba ro (y Loan Anh 01/08):
	# - CHO CHOT: don con trang thai Moi (0) - sales dang tu van, giu cho mem.
	# - DA DAT / PHAT SINH: don DA CHOT (khac Moi), chia theo tao truoc hay
	#   tao trong ngay giao. Chot xong don tu nhay tu Cho chot sang day.
	moi_don = [o for o in giao_hom_nay if o.get("status") == 0]
	chot_don = [o for o in giao_hom_nay if o.get("status") != 0]
	ps_don = [o for o in chot_don if o.get("id") in ma_tao_hom_nay]
	dd_don = [o for o in chot_don if o.get("id") not in ma_tao_hom_nay]
	dem_dd, ten1, hinh1, _k1 = _dem_banh(dd_don)
	dem_ps, ten2, hinh2, khach_ps = _dem_banh(ps_don)
	dem_cho, ten3, hinh3, khach_cho = _dem_banh(moi_don)
	ten1.update(ten2)
	ten1.update(ten3)
	hinh1.update(hinh2)
	hinh1.update(hinh3)

	doc = _lay_hoac_tao(ngay)
	# Don dong khong phai banh o (phi giao, phu kien) lot vao tu ban truoc.
	doc.dong = [d for d in doc.dong if str(d.ma_hang or "").upper().startswith(TIEN_TO_MA)]
	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_dd) + list(dem_ps) + list(dem_cho)):
		if ma not in co:
			d = doc.append("dong", {"ma_hang": ma, "ten_banh": ten1.get(ma, "")})
			co[ma] = d
		elif ten1.get(ma) and not co[ma].ten_banh:
			co[ma].ten_banh = ten1[ma]
	# Don kenh khac (Grab, Shopee, quay...) khong nam trong Pancake, dem
	# rieng tu hoa don ban ra. Chay o day de moi lan dong bo la so dung.
	_ghi_don_khac(doc, ngay)
	co = {d.ma_hang: d for d in doc.dong}

	for ma, d in co.items():
		d.da_dat = dem_dd.get(ma, 0)
		d.phat_sinh = dem_ps.get(ma, 0)
		d.cho_chot = dem_cho.get(ma, 0)
		d.ten_khach_ps = ", ".join(khach_ps.get(ma, []))
		d.ten_khach_cho = ", ".join(khach_cho.get(ma, []))
		# Anh moi ben Pancake phai de len anh cu. Truoc day chi nhan khi o
		# anh con trong nen doi anh ben Pancake xong web van anh cu
		# (Minh Vu bao 10/08/2026).
		if hinh1.get(ma) and hinh1[ma] != d.hinh:
			d.hinh = hinh1[ma]

	# Bu anh cho dong con thieu: don khong nhung anh thi tra danh muc.
	# Moi ma toi da mot lan moi 6 tieng (cache) de khoi goi Pancake vo ich
	# voi ma that su khong co anh; anh da luu thi khong bao gio tra lai.
	nho = frappe.cache()
	for ma, d in co.items():
		if d.hinh:
			continue
		khoa = "kb_tra_anh:%s" % ma
		if nho.get_value(khoa):
			continue
		nho.set_value(khoa, "1", expires_in_sec=6 * 3600)
		ten_p, anh_p = _tra_anh_ten(c, k, ma)
		if anh_p:
			d.hinh = anh_p
		if ten_p and not d.ten_banh:
			d.ten_banh = ten_p

	doc.dong_bo_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(ngay)




# Nguon don KHONG di qua Pancake: don ban tay cua sales (Grab, Shopee, Be,
# GreenSM, khach si) va don tinh tien tai quay. Don Pancake da duoc dem tu
# API o tren roi, dem lai o day la tru hai lan.
NGUON_PANCAKE = ("", "pancake")


def _dem_don_khac(ngay):
	"""Dem banh o da ban qua kenh khac Pancake trong ngay, tu hoa don ban ra.

	Loan Anh 08/08/2026: khach dat gap qua Grab thi sales bam don tay ben
	Doanh thu Sales; truoc day phai tao them mot don Pancake gia chi de tru
	so tren bang kiem banh, thanh ra mot khach hai bill. Nay dem thang.

	Tra ve (dem, mo_ta): dem[ma hang] = so luong, mo_ta[ma hang] = danh sach
	"GrabFood #GF-441" de sales biet so do tu don nao ra.
	"""
	ngay = getdate(ngay)
	sis = frappe.get_all(
		"Sales Invoice",
		filters={"posting_date": str(ngay), "docstatus": ["<", 2]},
		fields=["name", "custom_nguon", "custom_pancake_display_id"],
		limit_page_length=0,
	)
	theo_ten = {}
	for si in sis:
		if str(si.custom_nguon or "").strip().lower() in NGUON_PANCAKE:
			continue
		theo_ten[si.name] = si
	if not theo_ten:
		return {}, {}

	dong = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": ["in", sorted(theo_ten)]},
		fields=["parent", "item_code", "qty"],
		limit_page_length=0,
	)
	dem, mo_ta = {}, {}
	for r in dong:
		ma = str(r.item_code or "").strip()
		if not ma.upper().startswith(TIEN_TO_MA):
			continue
		sl = int(r.qty or 0)
		if sl <= 0:
			continue
		dem[ma] = dem.get(ma, 0) + sl
		si = theo_ten[r.parent]
		nhan = "%s%s" % (
			si.custom_nguon or "Kenh khac",
			" #" + str(si.custom_pancake_display_id) if si.custom_pancake_display_id else "",
		)
		if sl > 1:
			nhan += " (%d)" % sl
		ds = mo_ta.setdefault(ma, [])
		if nhan not in ds:
			ds.append(nhan)
	return dem, mo_ta


def _ghi_don_khac(doc, ngay):
	"""Do cot "Kenh khac" vao mot ban ghi kiem banh. KHONG tu save.

	Ngay da chot so thi khong dung vao nua - so cua ngay do da khoa, ton
	con lai da chay sang ngay mai theo con so luc chot.
	"""
	if doc.tinh_trang == "Da chot":
		return {}
	dem, mo_ta = _dem_don_khac(ngay)
	co = {d.ma_hang: d for d in doc.dong}
	thieu = [ma for ma in dem if ma not in co]
	ten_moi = {}
	if thieu:
		for it in frappe.get_all(
			"Item",
			filters={"name": ["in", sorted(thieu)]},
			fields=["name", "item_name", "image"],
			limit_page_length=0,
		):
			ten_moi[it.name] = it
	for ma in thieu:
		x = ten_moi.get(ma) or {}
		d = doc.append(
			"dong",
			{
				"ma_hang": ma,
				"ten_banh": x.get("item_name") or ma,
				"hinh": (x.get("image") or "") if not str(x.get("image") or "").startswith("/private") else "",
			},
		)
		co[ma] = d
	for ma, d in co.items():
		d.don_khac = dem.get(ma, 0)
		d.ten_khach_khac = ", ".join(mo_ta.get(ma, []))
	return dem


@frappe.whitelist()
def cap_nhat_don_khac(ngay=None):
	"""Do lai rieng cot "Kenh khac" cho mot ngay, khong dung den Pancake.

	Goi ngay sau khi sales bam xong mot don tay, de so tren man kiem banh
	tru lien chu khong doi lich 5 phut.
	"""
	ngay = getdate(ngay) if ngay else getdate()
	ma = "KB-%s" % ngay
	dem, _ = _dem_don_khac(ngay)
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		if not dem:
			return {"ok": 1, "bo_qua": 1}
	doc = _lay_hoac_tao(ngay)
	if doc.tinh_trang == "Da chot":
		return {"ok": 1, "da_chot": 1}
	_ghi_don_khac(doc, ngay)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma_hang": len(dem)}


def khi_doi_hoa_don(doc, method=None):
	"""Hook Sales Invoice: huy hoac xoa hoa don thi tra so lai bang kiem banh."""
	try:
		if str(doc.get("custom_nguon") or "").strip().lower() in NGUON_PANCAKE:
			return
		if not any(
			str(r.item_code or "").upper().startswith(TIEN_TO_MA) for r in (doc.get("items") or [])
		):
			return
		cap_nhat_don_khac(doc.posting_date)
	except Exception:
		frappe.log_error(title="Vagabond: cap nhat kiem banh khi doi hoa don", message=frappe.get_traceback())


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
				"phat_sinh": d.phat_sinh or 0, "ten_khach_ps": d.ten_khach_ps or "",
				"cho_chot": d.cho_chot or 0, "ten_khach_cho": d.ten_khach_cho or "",
				"don_khac": d.don_khac or 0, "ten_khach_khac": d.ten_khach_khac or "",
				"co_the_ban": d.co_the_ban or 0,
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
	if not _dang_ma_dung(ma_hang):
		frappe.throw(
			"Mã %s không đúng dạng. Bảng này chỉ theo dõi bánh ổ và bánh sỉ, "
			"mã phải là BAWC hoặc BAWS kèm 5 chữ số, ví dụ BAWC00098." % ma_hang
		)
	doc = _lay_hoac_tao(ngay)
	if any(d.ma_hang == ma_hang for d in doc.dong):
		frappe.throw("Ma nay da co trong bang")
	if not _co_that(c, k, ma_hang):
		frappe.throw(
			"Không tìm thấy mã %s ở cả Pancake lẫn danh mục Hàng hoá bên Next. "
			"Anh chị kiểm tra lại mã, hoặc tạo mã đó trước rồi thêm sau." % ma_hang
		)
	ten, anh = _tra_anh_ten(c, k, ma_hang)
	doc.append("dong", {"ma_hang": ma_hang, "ten_banh": ten, "hinh": anh})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ten_banh": ten}


SO_PHAI_RONG = ("ton_cu", "ton_d2", "ton_d1", "sx", "da_dat", "phat_sinh", "cho_chot", "don_khac")


@frappe.whitelist()
def xoa_dong(ngay, ma_hang):
	"""Go mot dong go nham khoi bang - chi khi dong do trang tron.

	Han bao 03/08/2026 co hai dong rac trong so: BAWC00025 va mot dong ten
	dung "BAWC". Truoc day khong co duong nao go ra, phai vao Desk. Gio man
	hinh co dau x tren the nao chua co so nao.
	"""
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % getdate(ngay))
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngày này đã chốt sổ, không xoá dòng được nữa")
	for d in doc.dong:
		if d.ma_hang != ma_hang:
			continue
		co_so = [t for t in SO_PHAI_RONG if int(d.get(t) or 0)]
		if co_so:
			frappe.throw("Mã %s đang có số, không xoá được. Xoá số về 0 trước đã." % ma_hang)
		doc.remove(d)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"ok": 1}
	frappe.throw("Khong thay ma hang %s" % ma_hang)


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
		ban = (d.da_dat or 0) + (d.phat_sinh or 0) + (d.don_khac or 0)
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

	# Tru kho BTP cap 2: moi banh giao xong hom nay von da an mot vo BTP
	# luc bep lay ra trang tri toi hom truoc (quy trinh Han 01/08). Tru
	# TAP TRUNG luc chot so de bep khong bao gio phai tru tay - trong ngay,
	# phan da lay ra van duoc "don dang giu" tru ho nen CON NHAN luon dung.
	try:
		kho = frappe.get_single("BTP Banh O")
		co_btp = {b.ma_hang: b for b in kho.dong}
		doi = False
		for d in doc.dong:
			b = co_btp.get(d.ma_hang)
			if not b:
				continue
			an = (d.da_dat or 0) + (d.phat_sinh or 0) + (d.don_khac or 0)
			if an and ((b.so_btp or 0) or (b.so_decor or 0)):
				b.so_btp = max(0, (b.so_btp or 0) - an)
				# Banh ban ra la banh DA du decor - tru luon so du decor
				b.so_decor = max(0, (b.so_decor or 0) - an)
				doi = True
		if doi:
			kho.cap_nhat_luc = now_datetime()
			kho.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Vagabond: tru BTP khi chot ngay loi", message=frappe.get_traceback())

	doc.tinh_trang = "Da chot"
	doc.chot_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ngay_mai": str(add_days(ngay, 1))}


RE_SIZE = re.compile(r"^(.*?)[,\s]*\bsize\b\s*(\d+)\s*cm\b.*$", re.IGNORECASE)
# Ten ben Next deu bat dau bang "Banh O ..."; trang ban hang goi ten ngan.
RE_TIEN_TO = re.compile(r"^b[áa]nh\s+[ổo]\s+", re.IGNORECASE)


def _tach_ten_size(ten):
	"""Bánh Ổ Kankin, size 12cm  ->  ("Kankin", 12).

	Ten khong co size thi tra size 0, trang ban hang tu hieu la banh mot co.
	"""
	t = str(ten or "").strip()
	m = RE_SIZE.match(t)
	if not m:
		return RE_TIEN_TO.sub("", t).strip(), 0
	goc = (m.group(1) or "").replace(",", " ").strip()
	return RE_TIEN_TO.sub("", goc).strip(), int(m.group(2))


# Anh va mo ta tren web phai bam theo danh muc Pancake. Sales thay anh
# hay sua mo ta ben do thi web doi theo trong vong nua tieng (Minh Vu bao
# 10/08/2026: anh banh Hannari doi roi ma web van anh cu).
CACHE_SP_GIAY = 1800


def _sach_html(s):
	"""Mo ta Pancake la HTML. Doi <br>, </p>, <li> thanh xuong dong roi bo
	het the, de web hien duoc thanh tung dong tang huong lop vi."""
	s = str(s or "")
	if not s:
		return ""
	s = re.sub(r"(?i)<\s*br\s*/?>", "\n", s)
	s = re.sub(r"(?i)</\s*(p|div|li|tr|h[1-6])\s*>", "\n", s)
	s = re.sub(r"(?i)<\s*li[^>]*>", "\n", s)
	s = re.sub(r"<[^>]+>", " ", s)
	s = (
		s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
		.replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
	)
	dong = [re.sub(r"[ \t]+", " ", d).strip() for d in s.split("\n")]
	return "\n".join([d for d in dong if d])


def _mo_ta_san_pham(c, k, sp_id):
	"""Mo ta cua mot SAN PHAM ben Pancake theo id.

	Endpoint bien the chi tra ban rut gon nen phai hoi rieng trang san pham
	moi lay duoc mo ta sales viet.
	"""
	if not sp_id:
		return ""
	try:
		r = requests.get(
			"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, sp_id),
			params={"api_key": k},
			timeout=TIMEOUT,
		)
		d = (r.json() or {})
		d = d.get("data") if isinstance(d.get("data"), dict) else d
		for truong in (
			"description", "note_product", "note", "content", "detail", "summary",
		):
			gt = _sach_html(d.get(truong) or "")
			if gt:
				return gt
	except Exception:
		pass
	return ""


def _sp_pancake(c, k, ma):
	"""Anh + mo ta cua mot ma ben Pancake. Tra {"anhs": [...], "mo_ta": "..."}.

	Trang dat banh co day 5 o anh (anh chinh, can canh, mat cat, chi tiet,
	dong goi) va khoi mo ta - tat ca lay tu danh muc Pancake, sales sua ben
	do la web tu doi, khong phai sua ma. Nho cache nua tieng vi ham nay chay
	trong endpoint khach vang lai goi.
	"""
	ck = "vgb:sp:" + str(ma)
	hit = cache_get(ck)
	if hit is not None:
		try:
			return json.loads(hit) if isinstance(hit, str) else hit
		except Exception:
			pass
	ra = {"anhs": [], "mo_ta": "", "khoa_bt": [], "khoa_sp": []}
	try:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() != str(ma).lower():
				continue
			sp = v.get("product") or {}
			ra["khoa_bt"] = sorted(list(v.keys()))
			ra["khoa_sp"] = sorted(list(sp.keys()))
			for u in (v.get("images") or []) + (sp.get("images") or []):
				u = str(u or "").strip()
				if u and u not in ra["anhs"]:
					ra["anhs"].append(u)
			ra["mo_ta"] = _sach_html(
				sp.get("description")
			or v.get("description")
			or sp.get("note_product")
			or sp.get("note")
			or ""
			)
			# API bien the tra ban RUT GON cua san pham, thuong khong kem mo
			# ta. Chua co mo ta thi hoi thang trang san pham (Minh Vu bao
			# 10/08/2026: sua mo ta ben Pancake ma web khong doi).
			if not ra["mo_ta"]:
				ra["mo_ta"] = _mo_ta_san_pham(c, k, sp.get("id") or v.get("product_id"))
			break
	except Exception:
		return {"anhs": [], "mo_ta": ""}
	ra["anhs"] = ra["anhs"][:5]
	cache_set(ck, json.dumps(ra), CACHE_SP_GIAY)
	return ra


def _anh_pancake(c, k, ma):
	"""Danh sach anh cua mot ma - giu ten cu cho cac cho dang goi."""
	return (_sp_pancake(c, k, ma) or {}).get("anhs") or []


@frappe.whitelist()
def tra_sp_pancake(ma=None, moi=0, soi=0):
	"""Xem Pancake dang giu anh va mo ta gi cho mot ma hang.

	Dung khi trang dat banh hien sai anh hay sai mo ta: goi ham nay ra la
	biet ngay loi o Pancake (sales chua sua) hay o he thong minh. Truyen
	moi=1 de bo qua bo nho dem, hoi thang Pancake.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Cần đăng nhập.")
	ma = (ma or "").strip()
	if not ma:
		frappe.throw("Thiếu mã hàng.")
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")
	if frappe.utils.cint(moi):
		try:
			frappe.cache().delete_value("vgb:sp:" + ma)
		except Exception:
			pass
	sp = _sp_pancake(c, k, ma) or {}
	dong = [d for d in (sp.get("mo_ta") or "").split("\n") if d.strip()]
	return {
		"ma": ma,
		"anhs": sp.get("anhs") or [],
		"mo_ta": dong[0] if dong else "",
		"tang": dong[1:][:12],
		"khoa_bien_the": sp.get("khoa_bt") or [],
		"khoa_san_pham": sp.get("khoa_sp") or [],
		"soi": _soi_pancake(c, k, ma) if frappe.utils.cint(soi) else {},
	}


def _soi_pancake(c, k, ma):
	"""Do het cac truong CHU cua mot ma ben Pancake ra de tim xem mo ta nam o
	dau. Chi dung khi go loi, khong goi trong luong chay thuong."""
	def chu(d, tien):
		ra = {}
		for k2, v2 in (d or {}).items():
			if isinstance(v2, str) and v2.strip():
				ra[tien + k2] = v2.strip()[:400]
		return ra
	ra = {}
	try:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() != str(ma).lower():
				continue
			sp = v.get("product") or {}
			ra.update(chu(v, "bt."))
			ra.update(chu(sp, "sp."))
			sp_id = sp.get("id") or v.get("product_id")
			ra["_sp_id"] = str(sp_id or "")
			if sp_id:
				r2 = requests.get(
					"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, sp_id),
					params={"api_key": k},
					timeout=TIMEOUT,
				)
				ra["_http"] = str(r2.status_code)
				d2 = (r2.json() or {})
				d2 = d2.get("data") if isinstance(d2.get("data"), dict) else d2
				ra.update(chu(d2, "ep."))
				ra["_khoa_ep"] = ", ".join(sorted(list((d2 or {}).keys())))
			break
	except Exception:
		ra["_loi"] = frappe.get_traceback()[-400:]
	return ra


@frappe.whitelist(allow_guest=True)
def co_the_ban_hom_nay():
	"""Cho trang dat banh order.thevagabondpatisserie.com.

	Truoc 06/08/2026 ham nay chi tra cap ma - so luong, con ten, anh, gia thi
	trang ban hang giu cung trong bien CAKES. Hau qua do that: hom 06/08 tu co
	4 ma con ban (6 banh) nhung web chi hien duoc 1 ma, vi 3 ma kia khong nam
	trong CAKES. Rieng Roman De La Rose trong CAKES con mang ma tu bia
	BAWC00901-903 - ma khong ton tai o dau ca, nen mai mai khong bao gio khop.

	Nay tra ve luon ten - gia - anh, de bat ky ma nao bep them tay o man kiem
	banh (khach bom hang, bep du do) cung tu len web, khong phai sua code.
	"""
	ngay = getdate()
	ma = "KB-%s" % ngay
	rong = {"ngay": str(ngay), "banh": {}, "mon": [], "nhom": [], "dat_truoc": _dat_truoc_theo_decor()}
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		return rong
	doc = frappe.get_doc("Kiem Banh Ngay", ma)
	# Trang nay ban LE. Ma BAWS la banh si, chi bep va sales nam voi nhau
	# ben man kiem banh, khong duoc bay len web (anh Viet 10/08/2026).
	dong = [
		d for d in doc.dong
		if (d.co_the_ban or 0) > 0
		and not str(d.ma_hang or "").upper().startswith("BAWS")
	]
	if not dong:
		return rong

	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", [d.ma_hang for d in dong]]},
		fields=["item_code", "item_name", "image", "standard_rate"],
		limit_page_length=0,
	)
	it = {x["item_code"]: x for x in ds}

	mon = []
	for d in dong:
		x = it.get(d.ma_hang) or {}
		ten_day = x.get("item_name") or d.ten_banh or d.ma_hang
		goc, cm = _tach_ten_size(ten_day)
		anh = d.hinh or x.get("image") or ""
		if str(anh).startswith("/private"):
			anh = ""
		mon.append(
			{
				"ma": d.ma_hang,
				"ten": goc,
				"ten_day": ten_day,
				"cm": cm,
				"gia": int(x.get("standard_rate") or 0),
				"anh": anh,
				"con": int(d.co_the_ban or 0),
			}
		)

	# Gom cac size cua cung mot banh lai cho web khoi phai tu doan.
	nhom, thu_tu = {}, []
	for m in mon:
		k = m["ten"].lower()
		if k not in nhom:
			nhom[k] = {"ten": m["ten"], "anh": m["anh"], "anhs": [], "sizes": []}
			thu_tu.append(k)
		g = nhom[k]
		if not g["anh"] and m["anh"]:
			g["anh"] = m["anh"]
		g["sizes"].append({"ma": m["ma"], "cm": m["cm"], "gia": m["gia"], "con": m["con"]})
	for k in nhom:
		nhom[k]["sizes"].sort(key=lambda s: (s["cm"] or 999))

	# Bo anh va mo ta cho tung banh, lay tu danh muc Pancake theo size nho
	# nhat tro di. Mo ta lay dong dau lam gioi thieu, cac dong sau thanh
	# tang huong lop vi (Minh Vu bao 10/08/2026).
	c = cfg()
	khoa = key(c, "pancake_api_key")
	if khoa and c.pancake_shop_id:
		for k in nhom:
			g = nhom[k]
			anhs, mo_ta = [], ""
			for s in g["sizes"]:
				sp = _sp_pancake(c, khoa, s["ma"]) or {}
				for u in sp.get("anhs") or []:
					if u not in anhs:
						anhs.append(u)
				if not mo_ta and (sp.get("mo_ta") or "").strip():
					mo_ta = sp["mo_ta"].strip()
				if len(anhs) >= 5 and mo_ta:
					break
			# Anh dau tien cua Pancake la anh dang dung; anh luu trong dong
			# kiem banh chi de lui ve khi Pancake khong tra gi.
			if not anhs and g["anh"]:
				anhs = [g["anh"]]
			if anhs:
				g["anh"] = anhs[0]
			g["anhs"] = anhs[:5]
			dong_mo_ta = [d for d in (mo_ta or "").split("\n") if d.strip()]
			g["mo_ta"] = dong_mo_ta[0] if dong_mo_ta else ""
			g["tang"] = [d.strip() for d in dong_mo_ta[1:]][:12]

	return {
		"ngay": str(ngay),
		"banh": {d.ma_hang: d.co_the_ban for d in dong},
		"mon": mon,
		"nhom": [nhom[k] for k in thu_tu],
		"dat_truoc": _dat_truoc_theo_decor(),
	}


def _dat_truoc_theo_decor():
	"""Danh muc tab DAT BANH TRUOC cua trang order, lay theo o DU DECOR
	ma bep dien trong /kiem-banh (kho BTP Banh O). Chot voi anh Viet
	07/08/2026: so decor la so banh con nhieu, nhan don duoc cho 3 ngay,
	nen tab dat truoc chi hien dung nhung banh nay kem so luong con nhan.
	"""
	try:
		kho = frappe.get_single("BTP Banh O")
	except Exception:
		return {"cap_nhat_luc": None, "nhom": []}
	dong = [b for b in (kho.dong or []) if (b.so_decor or 0) > 0]
	if not dong:
		return {"cap_nhat_luc": str(kho.cap_nhat_luc or "") or None, "nhom": []}

	# Tru don DA DAT trong 3 ngay toi (da_dat cua phieu kiem banh ngay mai,
	# mot va hai ngay sau) de so "con nhan" tren web khong nhan lo.
	ngay = getdate()
	da_dat = {}
	for i in (1, 2, 3):
		ma_kb = "KB-%s" % add_days(ngay, i)
		if not frappe.db.exists("Kiem Banh Ngay", ma_kb):
			continue
		for d in frappe.get_doc("Kiem Banh Ngay", ma_kb).dong:
			da_dat[d.ma_hang] = da_dat.get(d.ma_hang, 0) + int(d.da_dat or 0)

	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", [b.ma_hang for b in dong]]},
		fields=["item_code", "item_name", "image", "standard_rate"],
		limit_page_length=0,
	)
	it = {x["item_code"]: x for x in ds}

	nhom, thu_tu = {}, []
	for b in dong:
		x = it.get(b.ma_hang)
		if not x:
			# Ma trong kho BTP khong co Item ben Next (vd go nham ma):
			# khong dua len trang khach keo hien nguyen cuc ma va gia 0.
			continue
		con = int(b.so_decor or 0) - int(da_dat.get(b.ma_hang, 0))
		if con <= 0:
			continue
		ten_day = x.get("item_name") or b.ten_banh or b.ma_hang
		goc, cm = _tach_ten_size(ten_day)
		anh = b.hinh or x.get("image") or ""
		if str(anh).startswith("/private"):
			anh = ""
		k = goc.lower()
		if k not in nhom:
			nhom[k] = {"ten": goc, "anh": anh, "sizes": []}
			thu_tu.append(k)
		g = nhom[k]
		if not g["anh"] and anh:
			g["anh"] = anh
		g["sizes"].append(
			{
				"ma": b.ma_hang,
				"cm": cm,
				"gia": int(x.get("standard_rate") or 0),
				"con": con,
			}
		)
	for k in nhom:
		nhom[k]["sizes"].sort(key=lambda s: (s["cm"] or 999))
	return {
		"cap_nhat_luc": str(kho.cap_nhat_luc or "") or None,
		"nhom": [nhom[k] for k in thu_tu],
	}


@frappe.whitelist()
def tim_mon(tu_khoa="", ngay=None):
	"""Bang tim mon cho nut "Them ma" - tra ve ma, ten, anh, da co trong bang chua.

	Anh Viet 03/08/2026: nut Them ma dang bat go tay vao window.prompt, sales
	tren dien thoai go nham hoai. Doi thanh bang tim co ten, ma va anh giong
	bang chon mon luc chot doanh thu.
	"""
	q = str(tu_khoa or "").strip()
	dk = {"disabled": 0, "item_code": ["like", "BAW%"]}
	if q:
		ds = frappe.get_all(
			"Item",
			filters=dk,
			or_filters={
				"item_code": ["like", "%" + q + "%"],
				"item_name": ["like", "%" + q + "%"],
			},
			fields=["item_code", "item_name", "image"],
			order_by="item_code",
			limit_page_length=80,
		)
	else:
		ds = frappe.get_all(
			"Item",
			filters=dk,
			fields=["item_code", "item_name", "image"],
			order_by="item_code",
			limit_page_length=80,
		)
	da_co = set()
	if ngay:
		ten_bang = "KB-%s" % getdate(ngay)
		if frappe.db.exists("Kiem Banh Ngay", ten_bang):
			da_co = {
				r.ma_hang
				for r in frappe.get_doc("Kiem Banh Ngay", ten_bang).dong
			}
	ra = []
	for it in ds:
		ma = it.get("item_code") or ""
		if not _dang_ma_dung(ma):
			continue
		anh = it.get("image") or ""
		if anh.startswith("/private"):
			anh = ""
		ra.append(
			{
				"ma": ma,
				"ten": it.get("item_name") or "",
				"anh": anh,
				"da_co": 1 if ma in da_co else 0,
			}
		)
	return ra
