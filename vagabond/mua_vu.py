"""Kiem banh theo MUA: hang san xuat mot lo, ban het la thoi.

Anh Viet dat ngay 17/08/2026, mua Trung thu 2026.

Vi sao khong dung duoc bang kiem banh theo ngay
-----------------------------------------------
Bang theo ngay tra loi cau hoi "hom nay con bao nhieu cai de ban". Moi
sang dem lai tu dau, vi bep lam moi ngay.

Hang mua vu tra loi mot cau khac han: "ca mua nay con bao nhieu cai".
Hop MOONLAPIS in 100 hop la 100, khong co chuyen mai lam them. Khach dat
giao ngay 25/09 va khach dat giao ngay 02/10 deu an vao cung mot con so
100 do. Nen:

  - Nguon hang khong phai ton dau cong bep lam, ma la MOT HAN MUC nhap tay.
    Nha in giao them thi sua len, hop hong thi sua xuong - anh Viet noi ro
    "de cac ban tu nhap tu theo doi".
  - Pham vi dem khong phai mot ngay ma la CA KHOANG MUA.
  - Va can them mot thu bang ngay khong co: LICH THEO NGAY, de sales nhin
    ra ngay nao dang don nhieu ma con lieu chia banh.

Ke thua nguyen si tu bang theo ngay (chot voi anh Viet 01/08, van dung):
  - "Da dat"   = don DA CHOT trong khoang mua.
  - "Cho chot" = don con trang thai Moi - sales dang tu van, giu cho mem.
    TRU AO vao con ban duoc. Voi hang gioi han thi cang phai tru: mot don
    giu cho chua chot van la mot hop khong con de ban cho nguoi khac.
  - "Kenh khac" = ban qua Grab, Shopee, quay - khong di qua Pancake nen
    dem thang tu hoa don ban ra.
  - Trang thai 6 (huy) va 7 (xoa) khong dem.
  - Loc don theo ngay giao bang updateStatus=estimate_delivery_date, moc
    thoi gian la UNIX GIAY (truyen ISO thi Pancake tra 0 don ma khong bao
    loi - he nay da nga o do mot lan).

Ma hang mua vu mang tien to BASS
--------------------------------
Kiem tren he 17/08/2026: toan bo hang mua vu deu la BASS - hai hop
MOONGARDEN va MOONLAPIS, tam banh le 110g, hai banh deo 150g, va ca banh
Ba Trang, Khuc Cay, Panettone cua cac mua truoc.

Nghia la bang kiem banh theo ngay (chi dem BAWC va BAWS) chua bao gio dem
banh trung thu, va do chinh la cho trong ma bang nay lap vao.
"""

import json
from datetime import datetime, timedelta

import frappe
import requests
from frappe.utils import cint, getdate, now_datetime

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

DT = "Vagabond Mua Vu"
BO_QUA_TT = {6, 7}  # da huy, da xoa

# Hang mua vu tren he deu mang tien to BASS. Van cho ca BAWC va BAWS vao vi
# mot mua co the ban kem banh thuong (vi du hop qua co mot banh o nho), va
# luc do sales van muon dem chung o mot cho.
TIEN_TO_MA = ("BASS", "BAWC", "BAWS")

MAX_TRANG = 30  # ca mua vai thang, nhieu don hon mot ngay
GIAN_CACH_DONG_BO = 30  # giay. Keo ca mua nang hon keo mot ngay nen gian ra.

# Tran ngay cua mot mua. Mot mua dai hon nua nam thi gan nhu chac la go
# nham ngay, va keo Pancake ca nam la mot cu goi rat nang.
SO_NGAY_TOI_DA = 200


def _khoang_unix(tu_ngay, den_ngay):
	"""Tu 0h ngay dau den 23h59 ngay cuoi, gio Viet Nam, ra unix giay."""
	from zoneinfo import ZoneInfo

	vn = ZoneInfo("Asia/Ho_Chi_Minh")
	a, b = getdate(tu_ngay), getdate(den_ngay)
	dau = datetime(a.year, a.month, a.day, tzinfo=vn)
	cuoi = datetime(b.year, b.month, b.day, tzinfo=vn) + timedelta(days=1)
	return int(dau.timestamp()), int(cuoi.timestamp()) - 1


def _keo_don(c, k, dau, cuoi):
	"""Keo het don giao trong khoang mua, lat qua tung trang."""
	ra = []
	for trang in range(1, MAX_TRANG + 1):
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
			params={
				"api_key": k,
				"updateStatus": "estimate_delivery_date",
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


def _ngay_giao(o):
	"""Ngay giao cua mot don Pancake, dang YYYY-MM-DD. Rong neu khong doc duoc."""
	for o_ten in ("estimate_delivery_date", "time_delivery_at", "inserted_at"):
		v = o.get(o_ten)
		if not v:
			continue
		try:
			return str(getdate(str(v)[:10]))
		except Exception:
			continue
	return ""


def _dem(dons):
	"""Gop don thanh bon bang. THUAN tren du lieu Pancake, khong doc CSDL.

	Tra ve:
	  dem_chot  {ma: so}          don da chot
	  dem_cho   {ma: so}          don con trang thai Moi
	  theo_ngay {(ma, ngay): {"chot": n, "cho": n, "khach": [..]}}
	  ten, hinh {ma: ...}
	"""
	dem_chot, dem_cho, theo_ngay, ten, hinh = {}, {}, {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		cho = o.get("status") == 0
		ngay = _ngay_giao(o)
		ten_khach = (o.get("bill_full_name") or "").strip()
		for it in o.get("items") or []:
			vi = it.get("variation_info") or {}
			ma = str(vi.get("display_id") or it.get("variation_id") or "").strip()
			if not ma.upper().startswith(TIEN_TO_MA):
				continue
			sl = int(it.get("quantity") or 0)
			if cho:
				dem_cho[ma] = dem_cho.get(ma, 0) + sl
			else:
				dem_chot[ma] = dem_chot.get(ma, 0) + sl
			if vi.get("name"):
				ten[ma] = vi["name"]
			anh = vi.get("images") or []
			if anh and anh[0]:
				hinh[ma] = anh[0]
			if ngay:
				o_l = theo_ngay.setdefault((ma, ngay), {"chot": 0, "cho": 0, "khach": []})
				o_l["cho" if cho else "chot"] += sl
				if ten_khach and ten_khach not in o_l["khach"]:
					o_l["khach"].append(ten_khach)
	return dem_chot, dem_cho, theo_ngay, ten, hinh


def _dem_kenh_khac(tu_ngay, den_ngay):
	"""Banh mua vu ban qua kenh khong di qua Pancake, dem tu hoa don ban ra.

	Giong het cach bang theo ngay dang lam, va co y giong den tung dieu kien:

	  docstatus < 2  - bill con NHAP cung tru. Sales bam don giu cho khach
	                   thi cai hop do khong con de ban cho nguoi khac, du
	                   ke toan chua ghi so.
	  vgb_huy = 0    - bill da huy khong con la hang ban ra, khong duoc tru,
	                   khong thi sales dem thieu hang trong kho.
	  nguon khac Pancake - don Pancake da dem tu API o tren roi, dem lai o
	                   day la tru hai lan.
	"""
	try:
		r = frappe.db.sql(
			"""select sii.item_code as ma, sum(sii.qty) as sl
			from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where si.docstatus < 2
			  and ifnull(si.vgb_huy, 0) = 0
			  and si.posting_date between %s and %s
			  and lower(ifnull(si.custom_nguon, '')) not in ('', 'pancake')
			group by sii.item_code""",
			(getdate(tu_ngay), getdate(den_ngay)),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mua_vu: dem kenh khac loi")
		return {}
	return {
		d["ma"]: cint(d["sl"])
		for d in r
		if str(d.get("ma") or "").upper().startswith(TIEN_TO_MA)
	}


# ------------------------------------------------------------------ mua vu


@frappe.whitelist()
def danh_sach():
	"""Cac mua vu da lap, mua dang chay len dau."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ds = frappe.get_all(
		DT,
		fields=["name", "ten_mua", "tu_ngay", "den_ngay", "tinh_trang", "dong_bo_luc"],
		order_by="tu_ngay desc",
		limit_page_length=50,
	)
	hom_nay = getdate()
	for d in ds:
		d["dang_chay"] = 1 if (d["tu_ngay"] <= hom_nay <= d["den_ngay"]) else 0
		d["so_sp"] = frappe.db.count("Vagabond Mua Vu Dong", {"parent": d["name"]})
	return {"ds": ds}


@frappe.whitelist()
def tao_mua(ten_mua=None, tu_ngay=None, den_ngay=None):
	"""Lap mot mua vu moi."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ten = (ten_mua or "").strip()
	if not ten:
		frappe.throw("Đặt tên cho mùa vụ giúp em, ví dụ \"Trung thu 2026\".")
	if frappe.db.exists(DT, ten):
		frappe.throw(
			"Đã có mùa vụ tên \"%s\" rồi. Mở mùa đó ra dùng tiếp, hoặc đặt tên khác." % ten
		)
	a, b = getdate(tu_ngay), getdate(den_ngay)
	if b < a:
		frappe.throw("Ngày kết thúc đang trước ngày bắt đầu. Chọn lại hai mốc ngày giúp em.")
	if (b - a).days > SO_NGAY_TOI_DA:
		frappe.throw(
			"Mùa vụ dài %d ngày, quá %d ngày nên nhiều khả năng gõ nhầm năm. Chọn lại "
			"ngày kết thúc giúp em." % ((b - a).days, SO_NGAY_TOI_DA)
		)
	doc = frappe.get_doc(
		{"doctype": DT, "ten_mua": ten, "tu_ngay": a, "den_ngay": b, "tinh_trang": "Dang ban"}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "mua": doc.name}


@frappe.whitelist()
def dong_bo(mua=None):
	"""Dem lai ca mua tu Pancake: theo san pham va theo tung ngay giao."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)

	# Man hinh cua nhieu nguoi tu goi lien tuc. Vua dong bo trong vong
	# GIAN_CACH_DONG_BO giay thi tra bang luon - keo ca mua nang hon keo
	# mot ngay nhieu, khong nen goi Pancake lien tuc.
	if doc.dong_bo_luc and (now_datetime() - doc.dong_bo_luc).total_seconds() < GIAN_CACH_DONG_BO:
		return bang(mua)

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Cài đặt. Báo em để kiểm tra lại.")

	dau, cuoi = _khoang_unix(doc.tu_ngay, doc.den_ngay)
	dons = _keo_don(c, k, dau, cuoi)
	dem_chot, dem_cho, theo_ngay, ten, hinh = _dem(dons)
	khac = _dem_kenh_khac(doc.tu_ngay, doc.den_ngay)

	# Giu nguyen dong san pham nguoi da them va SO LUONG SAN XUAT ho da go.
	# Day la o duy nhat nguoi go, dong bo ma xoa mat no la xoa cong viec
	# cua ho.
	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_chot) + list(dem_cho) + list(khac)):
		if ma not in co:
			d = doc.append("dong", {"ma_hang": ma, "ten_banh": ten.get(ma, ""), "san_xuat": 0})
			co[ma] = d
		elif ten.get(ma) and not co[ma].ten_banh:
			co[ma].ten_banh = ten[ma]

	for ma, d in co.items():
		d.da_dat = dem_chot.get(ma, 0)
		d.cho_chot = dem_cho.get(ma, 0)
		d.don_khac = khac.get(ma, 0)
		if hinh.get(ma) and hinh[ma] != d.hinh:
			d.hinh = hinh[ma]
		kh = []
		for (m, _ng), o_l in theo_ngay.items():
			if m == ma and o_l["cho"]:
				kh.extend(o_l["khach"])
		d.ten_khach_cho = ", ".join(sorted(set(kh)))[:1000]

	# Dung lai bang lich tu dau moi lan dong bo: don doi ngay giao la
	# chuyen thuong, giu dong cu lai thi bang lich ke ra mot ngay khong con
	# don nao.
	doc.set("lich", [])
	for (ma, ngay), o_l in sorted(theo_ngay.items(), key=lambda x: (x[0][1], x[0][0])):
		if not (o_l["chot"] or o_l["cho"]):
			continue
		doc.append(
			"lich",
			{
				"ngay": ngay,
				"ma_hang": ma,
				"so_luong": o_l["chot"],
				"cho_chot": o_l["cho"],
				"ten_khach": ", ".join(o_l["khach"])[:500],
			},
		)

	doc.dong_bo_luc = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def bang(mua=None):
	"""Du lieu cho man hinh dien thoai."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, mua):
		return {"co_so": 0}
	doc = frappe.get_doc(DT, mua)

	# Bang lich: moi ngay mot dong, cot la san pham. Dung o may chu chu
	# khong o man hinh, de man chi viec ve.
	ngay_co, theo_ngay = [], {}
	for l in doc.lich:
		ng = str(l.ngay)
		if ng not in theo_ngay:
			theo_ngay[ng] = {}
			ngay_co.append(ng)
		theo_ngay[ng][l.ma_hang] = {
			"chot": l.so_luong or 0,
			"cho": l.cho_chot or 0,
			"khach": l.ten_khach or "",
		}

	return {
		"co_so": 1,
		"mua": doc.name,
		"ten_mua": doc.ten_mua,
		"tu_ngay": str(doc.tu_ngay),
		"den_ngay": str(doc.den_ngay),
		"tinh_trang": doc.tinh_trang,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or "",
				"san_xuat": d.san_xuat or 0,
				"da_dat": d.da_dat or 0,
				"cho_chot": d.cho_chot or 0,
				"don_khac": d.don_khac or 0,
				"co_the_ban": d.co_the_ban or 0,
				"ten_khach_cho": d.ten_khach_cho or "",
				"ghi_chu": d.ghi_chu or "",
			}
			for d in doc.dong
		],
		"lich": {"ngay": sorted(ngay_co), "o": theo_ngay},
	}


SUA_DUOC = {"san_xuat", "ghi_chu"}


@frappe.whitelist()
def luu_o(mua=None, ma_hang=None, truong=None, gia_tri=None):
	"""Sua o So luong san xuat hoac Ghi chu.

	Cac cot may dem KHONG sua tay duoc tu day - do la ca ly do phan he nay
	ton tai, y het bang kiem banh theo ngay.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if truong not in SUA_DUOC:
		frappe.throw(
			"Cột này máy tự đếm từ đơn Pancake nên không sửa tay được. Chỉ sửa được "
			"ô Số lượng sản xuất và ô Ghi chú."
		)
	doc = frappe.get_doc(DT, mua)
	if doc.tinh_trang == "Da dong":
		frappe.throw("Mùa vụ này đã đóng nên không sửa nữa. Mở lại mùa rồi sửa.")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			if truong == "san_xuat":
				d.san_xuat = max(0, cint(gia_tri))
			else:
				d.ghi_chu = str(gia_tri or "")[:140]
			doc.save()  # giu quyen that cua nguoi dang sua, de con vet ai sua gi
			frappe.db.commit()
			return {"ok": 1, "co_the_ban": d.co_the_ban, "san_xuat": d.san_xuat}
	frappe.throw("Không thấy mã hàng %s trong mùa này. Bấm Đồng bộ rồi thử lại." % ma_hang)


@frappe.whitelist()
def them_dong(mua=None, ma_hang=None):
	"""Them mot san pham chua co don nao - de sales dat han muc san xuat truoc."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ma = str(ma_hang or "").strip().upper()
	if not ma:
		frappe.throw("Chọn sản phẩm rồi bấm thêm giúp em.")
	doc = frappe.get_doc(DT, mua)
	if any(d.ma_hang == ma for d in doc.dong):
		frappe.throw("Sản phẩm %s đã có trong mùa này rồi." % ma)
	ten = frappe.db.get_value("Item", ma, "item_name") or ""
	doc.append("dong", {"ma_hang": ma, "ten_banh": ten, "san_xuat": 0})
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def xoa_dong(mua=None, ma_hang=None):
	"""Bo mot san pham khoi mua. Chi bo duoc khi CHUA co don nao.

	Co don roi ma bo di la giau mat mot con so dang co that: khach van dat,
	don van chay, ma bang khong con dong nao de tru.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	giu = []
	for d in doc.dong:
		if d.ma_hang != ma_hang:
			giu.append(d)
			continue
		if (d.da_dat or 0) or (d.cho_chot or 0) or (d.don_khac or 0):
			frappe.throw(
				"Sản phẩm %s đã có %d đơn nên không bỏ khỏi mùa được. Muốn ngừng bán "
				"thì đặt Số lượng sản xuất về 0."
				% (ma_hang, (d.da_dat or 0) + (d.cho_chot or 0) + (d.don_khac or 0))
			)
	doc.set("dong", giu)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def doi_tinh_trang(mua=None, tinh_trang=None):
	"""Dong mua khi ban xong, hoac mo lai de sua."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	tt = str(tinh_trang or "").strip()
	if tt not in ("Dang ban", "Da dong"):
		frappe.throw("Tình trạng phải là Đang bán hoặc Đã đóng.")
	frappe.db.set_value(DT, mua, "tinh_trang", tt)
	frappe.db.commit()
	return {"ok": 1, "tinh_trang": tt}


@frappe.whitelist()
def tim_san_pham(tu_khoa="", mua=None):
	"""Goi y san pham de them vao mua. Uu tien hang mua vu (BASS)."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	q = str(tu_khoa or "").strip()
	loc = {"disabled": 0}
	if q:
		loc["item_name"] = ["like", "%%%s%%" % q]
	else:
		loc["item_code"] = ["like", "BASS%"]
	ds = frappe.get_all(
		"Item",
		filters=loc,
		fields=["name", "item_name"],
		limit_page_length=40,
		order_by="name desc",
	)
	da_co = set()
	if mua and frappe.db.exists(DT, mua):
		da_co = {
			d["ma_hang"]
			for d in frappe.get_all(
				"Vagabond Mua Vu Dong", filters={"parent": mua}, fields=["ma_hang"], limit_page_length=0
			)
		}
	return {
		"ds": [
			{"ma": d["name"], "ten": d["item_name"], "da_co": 1 if d["name"] in da_co else 0}
			for d in ds
			if str(d["name"]).upper().startswith(TIEN_TO_MA)
		]
	}
