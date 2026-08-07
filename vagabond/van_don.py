"""Van don giao banh: sales phan don, shipper giao va bao ket qua, book xe app ngoai.

Chot voi anh Viet 02/08/2026:
- Shipper bam "Da giao" kem ANH chup tai cho (client nen anh truoc khi
  upload, luu private). Cron xoa anh giao sau 30 ngay cho nhe he thong;
  anh hoa don chi phi (chung tu) thi giu nguyen.
- Giao xong tu day trang thai "da nhan" (status 3) sang Pancake.
- Book xe: Ahamove chay that (dung san client giao_hang). GreenSM va BE
  dung khung cho key: GreenSM xac thuc OAuth2 client credentials, scope
  express.trips, base https://api-partner.vn.gsm-api.net/v1/express/
  (sandbox rieng), nho whitelist IP server. Dien key vao Vagabond Settings
  la chay, khong phai sua code.
- Chi phi shipper (xang, bao tri...): shipper khai kem anh hoa don,
  Thu mua / Ke toan duyet roi danh dau hoan ung.
"""

import json
import re

import frappe
import requests
from frappe.utils import add_days, cint, flt, get_datetime, now_datetime, nowdate

from vagabond.kiem_banh import BO_QUA_TT, _keo_don, _khoang_unix
from vagabond.lib import PANCAKE, TIMEOUT, cache_get, cache_set, cfg, key

QUYEN_SALES = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}
QUYEN_KE_TOAN = {"System Manager", "Accounts User", "Purchase User"}


def _roles():
	return set(frappe.get_roles())


def _la_sales():
	return bool(QUYEN_SALES & _roles())


def _la_shipper():
	return "Shipper" in _roles()


def _la_ke_toan():
	return bool(QUYEN_KE_TOAN & _roles())


def _kiem_quyen_xem():
	if not (_la_sales() or _la_shipper() or _la_ke_toan()):
		frappe.throw("Tài khoản chưa được cấp quyền dùng phân hệ vận đơn.")


# ---------------------------------------------------------------- Pancake

def _don_pancake(pid):
	"""Doc mot don Pancake de lay dia chi giao, ten, sdt, COD."""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id and pid):
		return {}
	try:
		r = requests.get(
			"%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid),
			params={"api_key": k},
			timeout=TIMEOUT,
		)
		return (r.json() or {}).get("data") or {}
	except Exception:
		return {}


def _day_trang_thai_pancake(pid, status=3):
	"""Day trang thai don sang Pancake (3 = da nhan). Tra True/False."""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id and pid):
		return False
	try:
		r = requests.put(
			"%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid),
			params={"api_key": k},
			json={"status": status},
			timeout=TIMEOUT,
		)
		return r.status_code == 200
	except Exception:
		frappe.log_error(title="Vagabond: day trang thai Pancake loi", message=frappe.get_traceback())
		return False


# ---------------------------------------------------------------- Van don

@frappe.whitelist()
def tao_van_don(si_name=None, ma_don=None, khach=None, sdt=None, dia_chi=None,
	ngay_giao=None, gio_giao=None, kenh=None, tien_thu_ho=0, ghi_chu=None,
	nguoi_nhan=None, sdt_nhan=None, tag_gio=None, lat=None, lng=None):
	"""Tao van don, uu tien keo thong tin tu hoa don + don Pancake goc.

	tag_gio la khung gio sales chon tren app, dang "9h - 11h". Ghi luon vao
	tag_gio va buoi de don tay vao duoc xep tuyen ngay, khong phai cho the
	ben Pancake. lat/lng la toa do Goong tra ve luc sales chon dia chi goi y,
	co san thi xep tuyen khoi ton mot luot geocode.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales tạo được vận đơn.")
	pid = ""
	if si_name:
		si = frappe.db.get_value(
			"Sales Invoice", si_name,
			["custom_pancake_id", "custom_pancake_display_id", "remarks", "grand_total", "outstanding_amount"],
			as_dict=True,
		)
		if not si:
			frappe.throw("Không thấy hoá đơn %s" % si_name)
		pid = si.custom_pancake_id or ""
		ma_don = ma_don or si.custom_pancake_display_id
		kh = (si.remarks or "").split(" - ")
		khach = khach or (kh[1] if len(kh) > 1 else "")
		sdt = sdt or (kh[2] if len(kh) > 2 else "")
		if not tien_thu_ho:
			tien_thu_ho = si.outstanding_amount if si.outstanding_amount else si.grand_total
		if pid and not dia_chi:
			o = _don_pancake(pid)
			sa = o.get("shipping_address") or {}
			dia_chi = sa.get("full_address") or sa.get("address") or ""
			khach = khach or (o.get("bill_full_name") or "")
			sdt = sdt or (o.get("bill_phone_number") or "")
			nguoi_nhan = (sa.get("full_name") or "").strip()
			sdt_nhan = (sa.get("phone_number") or "").strip()
	from vagabond.xep_tuyen import buoi_tu_khung

	tag_gio = (tag_gio or "").strip()
	if not tag_gio and RE_TAG_GIO.match(str(gio_giao or "")):
		tag_gio = str(gio_giao).strip()
	doc = frappe.get_doc(
		{
			"doctype": "Van Don",
			"hoa_don": si_name or None,
			"ma_don": ma_don,
			"khach": khach,
			"sdt": sdt,
			"nguoi_nhan": nguoi_nhan,
			"sdt_nhan": sdt_nhan,
			"dia_chi": dia_chi,
			"ngay_giao": ngay_giao or nowdate(),
			"gio_giao": gio_giao,
			"tag_gio": tag_gio or None,
			"buoi": buoi_tu_khung(tag_gio) if tag_gio else None,
			"lat": flt(lat) or None,
			"lng": flt(lng) or None,
			"kenh": kenh or "Shipper nội bộ",
			"tien_thu_ho": flt(tien_thu_ho),
			"ghi_chu": ghi_chu,
			"pancake_id": pid,
		}
	)
	doc.insert(ignore_permissions=True)
	mon = _mon_tu_pancake(_don_pancake(pid)) if pid else []
	if not mon:
		mon = _mon_tu_hoa_don(si_name)
	if mon:
		_ghi_mon(doc.name, mon)
	return doc.name


def _gio_tu_iso(s):
	"""Lay HH:mm tu chuoi ISO datetime cua Pancake, khong co thi tra rong."""
	s = str(s or "")
	if "T" in s and len(s) >= 16:
		return s[11:16]
	if " " in s and len(s) >= 16:
		return s[11:16]
	return ""


# The khung gio cua tiem co dang "15h - 17h"; the con lai la the van hanh
# (Goi truoc khi giao, Chup anh gui truoc khi giao, Cho banh, Xuat hoa don...).
RE_TAG_GIO = re.compile(r"^\s*\d{1,2}\s*h")
THE_GOI_TRUOC = "Gọi trước khi giao"
THE_CHUP_TRUOC = "Chụp ảnh gửi trước khi giao"


def _tach_the(o):
	"""Tra (khung_gio, danh_sach_the_van_hanh).

	Luu y: luc GHI sang Pancake thi tags la mang so; luc DOC ve thi Pancake
	tra mang object {id, name}. Ham nay chiu ca hai kieu.
	"""
	gio, khac = "", []
	for t in (o.get("tags") or []):
		ten = (t.get("name") if isinstance(t, dict) else str(t)) or ""
		ten = ten.strip()
		if not ten:
			continue
		if RE_TAG_GIO.match(ten):
			if not gio:
				gio = ten
		elif ten not in khac:
			khac.append(ten)
	return gio, khac


def _phuong(sa):
	"""Ten phuong / xa theo dia gioi MOI. Pancake da cap nhat sau khi bo cap
	quan huyen nen commune_name la ten moi (vd 'Phuong An Khanh'), dung duoc
	ngay - khong phai tu dung bang doi ten cu sang moi.
	"""
	return (sa.get("commune_name") or sa.get("commnue_name") or "").strip()


def _tu_pancake(o):
	"""Gom cac truong lay tu don Pancake ve dang truong cua Van Don.

	Nguoi DAT va nguoi NHAN hay la hai nguoi khac nhau (banh sinh nhat, banh
	tang). Pancake tach san: bill_full_name / bill_phone_number la nguoi dat
	(nguoi tra tien, nguoi sales noi chuyen), con shipping_address.full_name /
	phone_number la nguoi nhan tai dia chi giao. Goi nguoi nhan khong duoc thi
	shipper goi nguoi dat de thuong luong, nen phai giu ca hai.
	"""
	from vagabond.xep_tuyen import buoi_tu_khung

	sa = o.get("shipping_address") or {}
	gio, the = _tach_the(o)
	return {
		"khach": (o.get("bill_full_name") or sa.get("full_name") or "").strip(),
		"sdt": (o.get("bill_phone_number") or sa.get("phone_number") or "").strip(),
		"nguoi_nhan": (sa.get("full_name") or "").strip(),
		"sdt_nhan": (sa.get("phone_number") or "").strip(),
		"tag_gio": gio,
		"buoi": buoi_tu_khung(gio),
		"phuong": _phuong(sa),
		"the_don": ", ".join(the),
		"goi_truoc": 1 if THE_GOI_TRUOC in the else 0,
		"chup_truoc": 1 if THE_CHUP_TRUOC in the else 0,
		"ghi_chu_in": (o.get("note_print") or "").strip(),
	}


# Pancake ghi phi giao hang thanh mot "mon" trong don (vd PHI-GIAO-HANG,
# 60 x 1.000d). Do khong phai hang de shipper cam di, hien ra chi tro roi mat.
MA_KHONG_PHAI_HANG = ("PHI-", "PHU-THU", "PHUTHU")


def _la_hang_that(ma, ten):
	ma = (ma or "").upper()
	for tien_to in MA_KHONG_PHAI_HANG:
		if ma.startswith(tien_to):
			return False
	return bool(ma or ten)


def _mon_tu_pancake(o):
	"""Danh sach mon trong don Pancake, dua ve dang dong cua bang Van Don Mon.

	Ma hang nam o variation_info.display_id (dung ma tiem dat, khop voi Item
	ben ERPNext), ten mon o variation_info.name. note_product la loi nhan cho
	tung banh - shipper can doc nen phai giu.
	"""
	ra = []
	for it in (o.get("items") or []):
		vi = it.get("variation_info") or {}
		ten = (vi.get("name") or "").strip()
		ma = (vi.get("display_id") or "").strip()
		if not _la_hang_that(ma, ten):
			continue
		ra.append({
			"ma_hang": ma,
			"ten": ten,
			"so_luong": flt(it.get("quantity") or 0),
			"gia": flt(vi.get("retail_price") or 0),
			"tang": 1 if it.get("is_bonus_product") else 0,
			"ghi_chu": (it.get("note_product") or "").strip(),
		})
	return ra


def _mon_tu_hoa_don(si_name):
	"""Danh sach mon lay tu hoa don ban hang, dung khi don khong co ben Pancake."""
	if not si_name:
		return []
	return [
		{
			"ma_hang": r.item_code,
			"ten": r.item_name,
			"so_luong": flt(r.qty),
			"gia": flt(r.rate),
			"tang": 0,
			"ghi_chu": "",
		}
		for r in frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": si_name},
			fields=["item_code", "item_name", "qty", "rate"],
			order_by="idx asc",
			limit_page_length=100,
		)
	]


def _ghi_mon(doc_name, dong):
	"""Ghi de bang mon cua mot van don. Khong co dong nao thi de nguyen bang cu."""
	if not dong:
		return 0
	doc = frappe.get_doc("Van Don", doc_name)
	doc.set("mon", [])
	for d in dong:
		doc.append("mon", d)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return len(dong)


def _cod_tu_don(o, si):
	"""Tien shipper phai thu. Uu tien so con lai tren hoa don ERPNext."""
	if si:
		return flt(si.outstanding_amount or 0)
	tong = flt(
		o.get("total_price_after_sub_discount")
		or o.get("total_price")
		or 0
	)
	da_tra = flt(o.get("prepaid") or 0)
	for truong in ("cash", "transfer_money", "charged_by_onepay", "charged_by_card",
		"charged_by_momo", "charged_by_vnpay", "charged_by_qrpay"):
		da_tra += flt(o.get(truong) or 0)
	return max(0, tong - da_tra)


@frappe.whitelist()
def dong_bo_pancake(ngay=None):
	"""Keo don Pancake giao trong NGAY ve thanh van don de sales phan shipper.

	Loc theo ngay giao du kien (updateStatus=estimate_delivery_date, moc thoi
	gian phai la UNIX GIAY - truyen ISO thi Pancake tra 0 don ma khong bao
	loi). Bo don da huy (6) va da xoa (7). Chong trung theo pancake_id: don
	da keo ve roi thi khong dung toi, tranh de len tay sales da sua.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales và kế toán đồng bộ được vận đơn.")
	ngay = ngay or nowdate()
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	dau, cuoi = _khoang_unix(ngay)
	try:
		ds = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: dong bo Pancake")
		frappe.throw("Pancake chưa trả dữ liệu, anh chị thử lại sau ít phút giúp em.")

	them, da_co, bo_qua, lam_moi = 0, 0, 0, 0
	for o in ds:
		if (o.get("status") or 0) in BO_QUA_TT:
			bo_qua += 1
			continue
		pid = str(o.get("id") or "")
		if not pid:
			bo_qua += 1
			continue
		cu = frappe.db.get_value(
			"Van Don", {"pancake_id": pid},
			["name", "trang_thai", "tag_gio", "phuong", "ghi_chu_in", "the_don", "khach", "sdt", "nguoi_nhan", "sdt_nhan"],
			as_dict=True,
		)
		if cu:
			da_co += 1
			# Sales gan the khung gio o Pancake vao khoang 8h sang, sau luc keo
			# don ve. Nen don da co van phai lam moi phan lay tu Pancake -
			# nhung KHONG dung toi shipper, chuyen, trang thai da sales dat.
			if cu.trang_thai in ("Chờ giao", "Đang giao"):
				moi = _tu_pancake(o)
				if any((cu.get(k2) or "") != (moi.get(k2) or "") for k2 in
					("tag_gio", "phuong", "ghi_chu_in", "the_don", "khach", "sdt", "nguoi_nhan", "sdt_nhan")):
					frappe.db.set_value("Van Don", cu.name, moi, update_modified=False)
					lam_moi += 1
			# Don keo ve truoc luc co bang mon thi nap bu ngay o day.
			if not frappe.db.exists("Van Don Mon", {"parent": cu.name}):
				_ghi_mon(cu.name, _mon_tu_pancake(o))
			continue
		sa = o.get("shipping_address") or {}
		if str(o.get("received_at_shop") or "").lower() in ("true", "1"):
			kenh = "Khách tự lấy"
		else:
			kenh = "Shipper nội bộ"
		si = frappe.db.get_value(
			"Sales Invoice",
			{"custom_pancake_id": pid, "docstatus": ["<", 2]},
			["name", "grand_total", "outstanding_amount"],
			as_dict=True,
		)
		moi_vd = frappe.get_doc(
			dict(
				{
					"doctype": "Van Don",
					"hoa_don": si.name if si else None,
					"ma_don": str(o.get("display_id") or pid),
					"dia_chi": (sa.get("full_address") or sa.get("address") or "").strip(),
					"ngay_giao": ngay,
					"gio_giao": _gio_tu_iso(o.get("estimate_delivery_date")),
					"kenh": kenh,
					"tien_thu_ho": _cod_tu_don(o, si),
					"ghi_chu": (o.get("note") or "").strip(),
					"pancake_id": pid,
				},
				**_tu_pancake(o)
			)
		)
		moi_vd.insert(ignore_permissions=True)
		mon = _mon_tu_pancake(o) or _mon_tu_hoa_don(si.name if si else None)
		if mon:
			_ghi_mon(moi_vd.name, mon)
		them += 1
	frappe.db.commit()
	return {"them": them, "da_co": da_co, "lam_moi": lam_moi, "bo_qua": bo_qua,
		"tong": len(ds), "ngay": str(ngay)}


TRUONG_DS = [
	"name", "ma_don", "khach", "sdt", "dia_chi", "gio_giao", "trang_thai",
	"kenh", "shipper", "tien_thu_ho", "phi_giao", "anh_giao", "booking_id", "tracking_url",
	"ly_do_loi", "chuyen", "da_doi_soat", "nguoi_nhan", "sdt_nhan",
	"tag_gio", "buoi", "phuong", "the_don", "goi_truoc", "chup_truoc", "ghi_chu_in",
	"thu_tu", "gio_du_kien", "km_chang", "tre_khung_gio", "lat", "lng",
]


@frappe.whitelist()
def danh_sach(ngay=None, trang_thai=None, phuong=None, tag_gio=None, buoi=None,
	chuyen=None, shipper=None, chua_gan=None):
	"""Danh sach van don theo ngay, loc them theo phuong / khung gio / buoi /
	chuyen de sales xep tuyen. Shipper (khong phai sales) chi thay don cua
	minh hoac don noi bo chua ai nhan."""
	_kiem_quyen_xem()
	loc = {"ngay_giao": ngay or nowdate()}
	for truong, gt in (("trang_thai", trang_thai), ("phuong", phuong),
		("tag_gio", tag_gio), ("buoi", buoi), ("chuyen", chuyen), ("shipper", shipper)):
		if gt:
			loc[truong] = gt
	if cint(chua_gan):
		loc["shipper"] = ["in", ["", None]]
	ds = frappe.get_all(
		"Van Don",
		filters=loc,
		fields=TRUONG_DS,
		order_by="thu_tu asc, tag_gio asc, gio_giao asc, creation asc",
		limit_page_length=500,
	)
	if _la_shipper() and not _la_sales():
		# Anh Viet 03/08/2026: man hinh shipper chi hien dung don duoc phan cong,
		# khong hien don chua ai nhan nua cho do roi.
		toi = frappe.session.user
		ds = [d for d in ds if d.shipper == toi]
	_gan_tom_tat_mon(ds)
	return ds


def _gan_tom_tat_mon(ds):
	"""Gan so mon va dong tom tat mon vao tung van don trong danh sach.

	Doc mot lan cho ca danh sach chu khong doc tung don - danh sach mot ngay
	co the toi 500 don, doc tung don la app dung hinh.
	"""
	if not ds:
		return
	ten = [d["name"] for d in ds]
	rows = frappe.get_all(
		"Van Don Mon",
		filters={"parent": ["in", ten]},
		fields=["parent", "ten", "ma_hang", "so_luong", "tang"],
		order_by="parent asc, idx asc",
		limit_page_length=0,
	)
	theo_don = {}
	for r in rows:
		theo_don.setdefault(r.parent, []).append(r)
	for d in ds:
		mon = theo_don.get(d["name"], [])
		d["so_mon"] = len(mon)
		d["so_luong_mon"] = sum(flt(m.so_luong) for m in mon)
		d["mon_tat"] = " · ".join(
			"%s%s%s" % (
				("%g× " % flt(m.so_luong)) if flt(m.so_luong) != 1 else "",
				m.ten or m.ma_hang or "",
				" (tặng)" if m.tang else "",
			)
			for m in mon[:6]
		) + (" ..." if len(mon) > 6 else "")


@frappe.whitelist()
def bo_loc(ngay=None):
	"""Cac gia tri co that trong ngay de dung menu loc: khung gio, phuong,
	chuyen, va so don con thieu the khung gio (sales phai gan them ben Pancake).
	"""
	_kiem_quyen_xem()
	ds = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate()},
		fields=["tag_gio", "buoi", "phuong", "chuyen", "shipper", "trang_thai", "ma_don"],
		limit_page_length=500,
	)
	gio, phuong, chuyen, thieu = {}, {}, {}, []
	for d in ds:
		if d.trang_thai in ("Huỷ",):
			continue
		if (d.tag_gio or "").strip():
			gio[d.tag_gio] = gio.get(d.tag_gio, 0) + 1
		elif d.trang_thai == "Chờ giao":
			thieu.append(d.ma_don)
		if (d.phuong or "").strip():
			phuong[d.phuong] = phuong.get(d.phuong, 0) + 1
		if (d.chuyen or "").strip():
			chuyen[d.chuyen] = chuyen.get(d.chuyen, 0) + 1
	sxg = sorted(gio.items(), key=lambda x: x[0])
	return {
		"khung_gio": [{"v": k, "n": v} for k, v in sxg],
		"phuong": [{"v": k, "n": v} for k, v in sorted(phuong.items(), key=lambda x: -x[1])],
		"chuyen": [{"v": k, "n": v} for k, v in sorted(chuyen.items(), reverse=True)],
		"thieu_the_gio": thieu[:80],
		"so_thieu_the_gio": len(thieu),
		"tong": len(ds),
	}


def _qr_svg(noi_dung):
	"""Ma QR dang SVG noi thang vao HTML - khong can tep anh, in ra net.

	Dung pyqrcode co san trong Frappe (module xac thuc hai lop dung no).
	Khong co thi tra chuoi rong, phieu van in binh thuong.
	"""
	try:
		import pyqrcode
	except Exception:
		return ""
	try:
		qr = pyqrcode.create(noi_dung, error="M")
		luoi = qr.code  # list cac hang, 1 la o den
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: dung ma QR loi")
		return ""
	vien = 2
	n = len(luoi) + vien * 2
	o = []
	for y, hang in enumerate(luoi):
		x = 0
		while x < len(hang):
			if hang[x]:
				x2 = x
				while x2 + 1 < len(hang) and hang[x2 + 1]:
					x2 += 1
				o.append('<rect x="%d" y="%d" width="%d" height="1"/>' % (x + vien, y + vien, x2 - x + 1))
				x = x2 + 1
			else:
				x += 1
	return (
		'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges">'
		'<rect width="%d" height="%d" fill="#ffffff"/><g fill="#000000">%s</g></svg>'
	) % (n, n, n, n, "".join(o))


@frappe.whitelist()
def phieu_in(names):
	"""Du lieu day du de in phieu giao hang cho cac van don duoc chon.

	Ngoai truong cua van don, keo them danh sach mon tu hoa don ban hang de
	shipper doi chieu hop banh truoc khi roi tiem, va ten nguoi tao don.
	"""
	_kiem_quyen_xem()
	if isinstance(names, str):
		names = json.loads(names)
	if not names:
		frappe.throw("Chưa chọn vận đơn nào để in.")
	ra = []
	for nm in names[:60]:
		d = frappe.db.get_value("Van Don", nm, TRUONG_DS + ["hoa_don", "ngay_giao", "ghi_chu", "owner"], as_dict=True)
		if not d:
			continue
		d["ten_shipper"] = frappe.db.get_value("User", d.shipper, "full_name") if d.shipper else ""
		d["nguoi_tao"] = frappe.db.get_value("User", d.owner, "full_name") or d.owner or ""
		# Uu tien bang mon cua chinh van don: don keo tu Pancake ve thuong chua
		# co hoa don ban hang, lay theo hoa don la phieu in ra trang tron.
		d["mon"] = [
			{"item_code": m.ma_hang, "item_name": m.ten, "qty": m.so_luong,
				"amount": flt(m.so_luong) * flt(m.gia), "ghi_chu": m.ghi_chu,
				"tang": m.tang}
			for m in frappe.get_all(
				"Van Don Mon",
				filters={"parent": d.name},
				fields=["ma_hang", "ten", "so_luong", "gia", "ghi_chu", "tang"],
				order_by="idx asc",
				limit_page_length=100,
			)
		]
		if not d["mon"] and d.hoa_don:
			d["mon"] = frappe.get_all(
				"Sales Invoice Item",
				filters={"parent": d.hoa_don},
				fields=["item_code", "item_name", "qty", "amount"],
				order_by="idx asc",
				limit_page_length=100,
			)
		d["duong_dan"] = "%s/bep?vd=%s" % (frappe.utils.get_url().rstrip("/"), d.name)
		d["qr"] = _qr_svg(d["duong_dan"])
		ra.append(d)
	# giu dung thu tu tuyen de shipper cam xap giay la chay theo thu tu
	ra.sort(key=lambda x: (x.get("chuyen") or "", x.get("thu_tu") or 999, x.get("tag_gio") or ""))
	return ra


@frappe.whitelist()
def chuyen_cua_toi(ngay=None):
	"""Man hinh cua shipper: chuyen duoc giao hom nay, da sap dung thu tu.

	Thay cho to A4 in san dau ngay - shipper mo dien thoai la thay het."""
	_kiem_quyen_xem()
	toi = frappe.session.user
	ds = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "shipper": toi},
		fields=TRUONG_DS,
		order_by="thu_tu asc, tag_gio asc, creation asc",
		limit_page_length=200,
	)
	gom = {}
	for d in ds:
		g = gom.setdefault(d.chuyen or "(chưa gộp chuyến)", {"chuyen": d.chuyen or "", "don": []})
		g["don"].append(d)
	ra = []
	for ten, g in gom.items():
		don = g["don"]
		ra.append({
			"chuyen": ten,
			"so_don": len(don),
			"con_lai": len([x for x in don if x.trang_thai in ("Chờ giao", "Đang giao")]),
			"tong_cod": sum(flt(x.tien_thu_ho) for x in don if x.trang_thai != "Đã giao"),
			"link_chi_duong": _maps_tu_don(don),
			"don": don,
		})
	return sorted(ra, key=lambda x: x["chuyen"])


def _maps_tu_don(don):
	"""Link Google Maps ca chuyen theo dung thu tu, mo mot phat di het tuyen."""
	from vagabond.xep_tuyen import _diem_lay_cf

	toa = [d for d in don if flt(d.lat) and flt(d.lng) and d.trang_thai in ("Chờ giao", "Đang giao")]
	if not toa:
		return ""
	c = cfg()
	d0 = _diem_lay_cf(c, "Bếp")
	diem = ["%s,%s" % (d0["lat"], d0["lng"])] + ["%s,%s" % (d.lat, d.lng) for d in toa]
	u = "https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=%s&destination=%s" % (diem[0], diem[-1])
	giua = diem[1:-1]
	if giua:
		u += "&waypoints=" + "|".join(giua)
	return u


@frappe.whitelist()
def nhan_don(name):
	"""Shipper nhan don ve minh, chuyen Dang giao."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai not in ("Chờ giao", "Đang giao"):
		frappe.throw("Đơn đang ở trạng thái %s, không nhận được." % doc.trang_thai)
	doc.shipper = frappe.session.user
	doc.trang_thai = "Đang giao"
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.name


@frappe.whitelist()
def giao_xong(name, file_url=None):
	"""Shipper bao giao thanh cong, kem anh da upload (file_url).
	Tu day trang thai da nhan sang Pancake neu co pancake_id."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai in ("Đã giao", "Huỷ"):
		frappe.throw("Đơn đã ở trạng thái %s." % doc.trang_thai)
	doc.trang_thai = "Đã giao"
	doc.giao_luc = now_datetime()
	if not doc.shipper and _la_shipper():
		doc.shipper = frappe.session.user
	if file_url:
		doc.anh_giao = file_url
	bao = False
	if doc.pancake_id:
		bao = _day_trang_thai_pancake(doc.pancake_id, 3)
		doc.da_bao_pancake = 1 if bao else 0
		if not bao:
			doc.ghi_chu = ((doc.ghi_chu or "") + "\nChưa đẩy được trạng thái sang Pancake, sales kiểm lại.").strip()
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "da_bao_pancake": bao}


@frappe.whitelist()
def giao_loi(name, ly_do):
	"""Danh dau KHONG GIAO DUOC (khach khong nghe may, sai dia chi...).
	Khong dung den trang thai Pancake - sales tu xu ly don goc."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	doc.trang_thai = "Không giao được"
	doc.ly_do_loi = ly_do
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.name


@frappe.whitelist()
def huy_van_don(name):
	if not _la_sales():
		frappe.throw("Chỉ sales huỷ được vận đơn.")
	frappe.db.set_value("Van Don", name, "trang_thai", "Huỷ")
	return name


# ---------------------------------------------------------------- Gop chuyen

@frappe.whitelist()
def ds_shipper():
	"""Danh sach user co role Shipper de gan chuyen."""
	_kiem_quyen_xem()
	ds = frappe.get_all(
		"Has Role",
		filters={"role": "Shipper", "parenttype": "User"},
		fields=["parent"],
	)
	ra = []
	for r in ds:
		if r.parent in ("Administrator", "Guest"):
			continue
		if not frappe.db.get_value("User", r.parent, "enabled"):
			continue
		ra.append({"user": r.parent, "ten": frappe.db.get_value("User", r.parent, "full_name") or r.parent})
	return ra


# Don vi giao hang ngoai. Co API thi app tu goi xe duoc, khong co API thi
# chi danh dau de nhan vien tu dat tren app cua ho roi ghi nhan lai.
KENH_NGOAI = {
	"Ahamove": {"api": 1},
	"GreenSM": {"api": 1},
	"Grab": {"api": 0},
	"BE": {"api": 0},
	"Lalamove": {"api": 0},
}


@frappe.whitelist()
def gan_shipper(name, shipper=None, kenh=None):
	"""Sales chi dinh nguoi giao cho MOT van don.

	- shipper = email nhan vien: don hien ngay tren man hinh shipper do,
	  va he thong gui email bao cho ban ay.
	- kenh = ten don vi ngoai (Ahamove, GreenSM, Grab, BE, Lalamove): danh dau
	  don di app ngoai. Don vi co API thi de trang thai Cho giao cho sales bam
	  Goi xe; don vi khong co API thi chuyen thang Dang giao vi nhan vien tu
	  dat tren app cua ho.
	- ca hai rong: go ra, tra ve Cho giao.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales chỉ định người giao được.")
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai in ("Đã giao", "Huỷ"):
		frappe.throw("Đơn đã ở trạng thái %s, không đổi người giao được." % doc.trang_thai)
	cu = doc.shipper
	if kenh:
		if kenh not in KENH_NGOAI:
			frappe.throw("Không biết đơn vị giao hàng %s." % kenh)
		doc.shipper = None
		doc.chuyen = ""
		doc.thu_tu = 0
		doc.kenh = kenh
		doc.trang_thai = "Chờ giao" if KENH_NGOAI[kenh]["api"] else "Đang giao"
	elif shipper:
		doc.shipper = shipper
		doc.trang_thai = "Đang giao"
		if doc.kenh != "Shipper nội bộ":
			doc.kenh = "Shipper nội bộ"
	else:
		doc.shipper = None
		doc.chuyen = ""
		doc.thu_tu = 0
		doc.trang_thai = "Chờ giao"
	doc.flags.ignore_permissions = True
	doc.save()
	if doc.shipper and doc.shipper != cu:
		_mail_phan_cong(doc)
	return {"name": doc.name, "shipper": doc.shipper, "kenh": doc.kenh,
		"trang_thai": doc.trang_thai}


def _mail_phan_cong(doc):
	"""Bao cho shipper biet vua co don moi. Hong thi bo qua, khong chan viec gan."""
	try:
		from vagabond.nhan_su import thu_phan_cong_html

		email = frappe.db.get_value("User", doc.shipper, "email") or doc.shipper
		ten = frappe.db.get_value("User", doc.shipper, "full_name") or ""
		frappe.sendmail(
			recipients=email,
			subject="Đơn giao mới: %s - %s" % (doc.ma_don or doc.name, doc.khach or ""),
			message=thu_phan_cong_html(ten, doc),
			delayed=False,
			retry=2,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: mail phan cong loi")


@frappe.whitelist()
def chuyen_dang_chay(ngay=None):
	"""Cac chuyen con don Dang giao trong ngay - de chen don moi vao
	chuyen dang chay thay vi tao chuyen moi."""
	_kiem_quyen_xem()
	rows = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "trang_thai": "Đang giao", "chuyen": ["!=", ""]},
		fields=["chuyen", "shipper"],
		limit_page_length=300,
	)
	gom = {}
	for r in rows:
		g = gom.setdefault(r.chuyen, {"chuyen": r.chuyen, "shipper": r.shipper, "so_don": 0})
		g["so_don"] += 1
	ra = sorted(gom.values(), key=lambda x: x["chuyen"], reverse=True)
	for g in ra:
		g["ten_shipper"] = frappe.db.get_value("User", g["shipper"], "full_name") or g["shipper"] or ""
	return ra


@frappe.whitelist()
def gop_chuyen(names, shipper, chuyen=None):
	"""Gop nhieu van don thanh mot chuyen cho shipper noi bo - thao tac
	mot phat cho nhanh vi don hay phat sinh chen ngang (y Loan Anh).

	names: json list ten Van Don. chuyen bo trong = tao chuyen moi;
	truyen ma chuyen dang chay = chen them don vao chuyen do."""
	if not _la_sales():
		frappe.throw("Chỉ sales gộp chuyến được.")
	if isinstance(names, str):
		names = json.loads(names)
	if not names:
		frappe.throw("Chưa chọn đơn nào.")
	if not shipper:
		frappe.throw("Chưa chọn shipper.")
	if not chuyen:
		d = now_datetime().strftime("%d%m")
		n = 1
		while True:
			chuyen = "CH-%s-%d" % (d, n)
			if not frappe.db.exists("Van Don", {"chuyen": chuyen}):
				break
			n += 1
	bo_qua = []
	gan = 0
	for nm in names:
		doc = frappe.get_doc("Van Don", nm)
		if doc.trang_thai not in ("Chờ giao", "Đang giao"):
			bo_qua.append("%s (%s)" % (doc.ma_don or nm, doc.trang_thai))
			continue
		doc.shipper = shipper
		doc.chuyen = chuyen
		doc.trang_thai = "Đang giao"
		if doc.kenh != "Shipper nội bộ":
			doc.kenh = "Shipper nội bộ"
		doc.flags.ignore_permissions = True
		doc.save()
		gan += 1
	return {"chuyen": chuyen, "so_don": gan, "bo_qua": bo_qua}


# ---------------------------------------------------------------- Doi soat COD

@frappe.whitelist()
def doi_soat_cod(ngay=None):
	"""Tong COD da giao theo tung shipper trong ngay, tach phan chua
	doi soat de ke toan thu tien shipper nop ve cuoi ngay."""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales hoặc kế toán xem đối soát COD.")
	rows = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "trang_thai": "Đã giao"},
		fields=["name", "ma_don", "khach", "shipper", "kenh", "tien_thu_ho", "da_doi_soat", "chuyen"],
		order_by="shipper asc, creation asc",
		limit_page_length=500,
	)
	gom = {}
	for r in rows:
		ai = r.shipper or ("(app ngoài: %s)" % (r.kenh or "?") if r.kenh != "Shipper nội bộ" else "(chưa gán shipper)")
		g = gom.setdefault(ai, {
			"shipper": ai, "ten": "", "so_don": 0, "tong_cod": 0,
			"chua_doi_soat": 0, "so_don_chua": 0, "don": [],
		})
		g["so_don"] += 1
		g["tong_cod"] += flt(r.tien_thu_ho)
		if not r.da_doi_soat:
			g["chua_doi_soat"] += flt(r.tien_thu_ho)
			g["so_don_chua"] += 1
		g["don"].append({
			"name": r.name, "ma_don": r.ma_don, "khach": r.khach,
			"cod": flt(r.tien_thu_ho), "da_doi_soat": r.da_doi_soat, "chuyen": r.chuyen,
		})
	for ai, g in gom.items():
		if "@" in ai:
			g["ten"] = frappe.db.get_value("User", ai, "full_name") or ai
		else:
			g["ten"] = ai
	return sorted(gom.values(), key=lambda x: -x["tong_cod"])


@frappe.whitelist()
def xac_nhan_cod(shipper, ngay=None):
	"""Ke toan xac nhan DA NHAN DU tien COD shipper nop ve cho ngay do.
	Danh dau da_doi_soat len toan bo don Da giao cua shipper trong ngay."""
	if not _la_ke_toan():
		frappe.throw("Chỉ kế toán / thu mua xác nhận được tiền COD.")
	rows = frappe.get_all(
		"Van Don",
		filters={
			"ngay_giao": ngay or nowdate(), "trang_thai": "Đã giao",
			"shipper": shipper, "da_doi_soat": 0,
		},
		fields=["name", "tien_thu_ho"],
		limit_page_length=500,
	)
	tong = 0
	for r in rows:
		frappe.db.set_value("Van Don", r.name, "da_doi_soat", 1)
		tong += flt(r.tien_thu_ho)
	return {"so_don": len(rows), "tong": tong}


# ---------------------------------------------------------------- Book xe

def _diem_lay(c):
	return {
		"lat": flt(c.kitchen_lat), "lng": flt(c.kitchen_lng),
		"dia_chi": c.kitchen_address or "", "ten": "The Vagabond Patisserie",
	}


def _ahamove_dat_don(doc, service_id=None, them_reqs=None):
	from vagabond.dia_chi import geocode
	from vagabond.giao_hang import _token as _aha_token

	c = cfg()
	if not (key(c, "ahamove_api_key") and c.ahamove_base and c.ahamove_mobile):
		frappe.throw("Chưa cấu hình Ahamove trong Vagabond Settings.")
	if not (doc.dia_chi or "").strip():
		frappe.throw("Vận đơn chưa có địa chỉ giao.")
	toa = geocode(c, doc.dia_chi)
	if not toa or not toa.get("lat"):
		frappe.throw("Không tìm được toạ độ cho địa chỉ này, sửa lại địa chỉ giúp em.")
	dv = (service_id or c.ma_dich_vu or "").strip()
	if them_reqs is None:
		reqs = []
		if c.dung_dich_vu_de_vo:
			reqs.append({"_id": dv + "-FRAGILE"})
	else:
		reqs = [{"_id": r} for r in them_reqs if r]
	body = {
		"order_time": 0,
		"path": [
			dict(_diem_lay(c), mobile=c.ahamove_mobile, name="The Vagabond", address=c.kitchen_address or ""),
			{
				"lat": toa["lat"], "lng": toa["lng"], "address": doc.dia_chi,
				"name": doc.khach or "Khách", "mobile": doc.sdt or c.ahamove_mobile,
				"cod": flt(doc.tien_thu_ho) or 0,
			},
		],
		# TAO don dung service_id (chuoi) + requests o cap cao nhat.
		# HOI PHI (/v3/orders/estimates) moi dung services: [{_id, requests}].
		# Truyen nham kieu cua endpoint hoi phi sang endpoint tao don thi Ahamove
		# tra 404 SERVICE_NOT_FOUND "Service does not exist" - loi anh Viet gap
		# 02/08/2026, du ma SGN-BIKE hoan toan hop le.
		"service_id": dv,
		"requests": reqs,
		"payment_method": "BALANCE",
		"remarks": "Đơn %s - %s" % (doc.ma_don or doc.name, doc.tag_gio or doc.gio_giao or ""),
	}
	body["path"][0].pop("dia_chi", None)
	body["path"][0].pop("ten", None)
	r = requests.post(
		(c.ahamove_base or "").rstrip("/") + "/v3/orders",
		json=body,
		headers={"Authorization": "Bearer " + _aha_token(c)},
		timeout=TIMEOUT,
	)
	if r.status_code != 200:
		frappe.log_error(title="Vagabond: Ahamove dat don loi", message=r.text[:1000])
		frappe.throw("Ahamove từ chối đơn: %s" % r.text[:200])
	d = r.json() or {}
	oid = d.get("order_id") or (d.get("order") or {}).get("_id") or ""
	don = d.get("order") or {}
	phi = flt(don.get("total_fee") or don.get("total_pay") or 0)
	return oid, ("https://cloud.ahamove.com/share-order/%s" % oid if oid else ""), phi


def _greensm_token(c):
	"""OAuth2 client credentials, scope express.trips (sandbox.express.trips)."""
	ck = "vgb:gsm:token"
	hit = cache_get(ck)
	if hit:
		return hit
	scope = "sandbox.express.trips" if c.get("greensm_sandbox") else "express.trips"
	r = requests.post(
		(c.greensm_token_url or "").strip(),
		data={
			"grant_type": "client_credentials",
			"client_id": c.greensm_client_id,
			"client_secret": key(c, "greensm_client_secret"),
			"scope": scope,
		},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	tok = (r.json() or {}).get("access_token")
	if not tok:
		frappe.throw("GreenSM không trả access_token, kiểm lại client_id/secret.")
	cache_set(ck, tok, 1500)
	return tok


def _greensm_base(c):
	if c.get("greensm_sandbox"):
		return "https://api-sandbox.vn.gsm-api.net/v1/sandbox/express"
	return "https://api-partner.vn.gsm-api.net/v1/express"


def _greensm_dat_don(doc):
	"""Khung tao don GreenSM Express. Payload chi tiet ho chua cong bo
	(trang create-order dang 'being prepared'), co key + spec thi chinh
	MAP_GSM ben duoi la chay."""
	c = cfg()
	if not (c.get("greensm_client_id") and key(c, "greensm_client_secret") and c.get("greensm_token_url")):
		frappe.throw(
			"GreenSM chưa có API key (đang chờ ký NDA). Khung đã dựng sẵn: "
			"ký xong anh điền Client ID, Client Secret, Token URL vào Vagabond Settings "
			"và nhớ đăng ký IP server với GreenSM (họ bắt whitelist IP)."
		)
	from vagabond.dia_chi import geocode

	toa = geocode(c, doc.dia_chi or "")
	diem = _diem_lay(c)
	MAP_GSM = {
		"pickup": {"lat": diem["lat"], "lng": diem["lng"], "address": diem["dia_chi"], "contact_name": "The Vagabond", "contact_phone": c.ahamove_mobile or ""},
		"dropoff": {"lat": (toa or {}).get("lat"), "lng": (toa or {}).get("lng"), "address": doc.dia_chi, "contact_name": doc.khach or "Khách", "contact_phone": doc.sdt or ""},
		"cod_amount": flt(doc.tien_thu_ho) or 0,
		"note": "Đơn %s - %s" % (doc.ma_don or doc.name, doc.gio_giao or ""),
	}
	r = requests.post(
		_greensm_base(c) + "/create-order",
		json=MAP_GSM,
		headers={"Authorization": "Bearer " + _greensm_token(c)},
		timeout=TIMEOUT,
	)
	if r.status_code not in (200, 201):
		frappe.log_error(title="Vagabond: GreenSM dat don loi", message=r.text[:1000])
		frappe.throw("GreenSM từ chối đơn: %s" % r.text[:200])
	d = r.json() or {}
	oid = str(d.get("id") or d.get("order_id") or "")
	return oid, str(d.get("tracking_url") or ""), flt(d.get("total_fee") or 0)


@frappe.whitelist()
def book_xe(name, kenh, service_id=None, requests_them=None):
	"""Dat xe cho van don qua app ngoai.

	service_id va requests_them den tu man xac nhan trong app: nhan vien chon
	loai xe va tick add-on (giao tan tay, hang de vo...) roi moi bam Goi xe.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales book xe được.")
	doc = frappe.get_doc("Van Don", name)
	if doc.booking_id:
		frappe.throw("Đơn này đã book rồi (%s). Huỷ bên app kia trước nếu muốn book lại." % doc.booking_id)
	if isinstance(requests_them, str):
		requests_them = json.loads(requests_them or "[]")
	if kenh == "Ahamove":
		oid, link, phi = _ahamove_dat_don(doc, service_id, requests_them)
	elif kenh == "GreenSM":
		oid, link, phi = _greensm_dat_don(doc)
	elif kenh == "BE":
		frappe.throw("BE Delivery chưa cấp API (anh Việt đang xin). Có key là em nối, khung dùng chung với GreenSM.")
	else:
		frappe.throw("Kênh %s không book qua API được." % kenh)
	doc.kenh = kenh
	doc.booking_id = oid
	doc.tracking_url = link
	if phi:
		doc.phi_giao = phi
	doc.trang_thai = "Đang giao"
	doc.flags.ignore_permissions = True
	doc.save()
	return {"booking_id": oid, "tracking_url": link, "phi_giao": phi}


# ------------------------------------------------- Man xac nhan goi xe Ahamove

# Add-on bay ra nhieu, nhan vien khong can thay het. Day la nhung cai thuc su
# dung khi giao banh; con lai (SMS, khai gia, chung tu, quay dau...) an di.
AHA_ADDON_HIEN = ("D2D", "FRAGILE", "BULKY", "BAGA", "TIP")


def _aha_goi(c, duong_dan, phuong_thuc="GET", body=None):
	from vagabond.giao_hang import _token as _aha_token

	url = (c.ahamove_base or "").rstrip("/") + duong_dan
	dau = {"Authorization": "Bearer " + _aha_token(c)}
	if phuong_thuc == "POST":
		r = requests.post(url, json=body or {}, headers=dau, timeout=TIMEOUT)
	else:
		r = requests.get(url, headers=dau, timeout=TIMEOUT)
	if r.status_code != 200:
		frappe.log_error(title="Vagabond: Ahamove %s loi" % duong_dan, message=r.text[:1000])
		frappe.throw("Ahamove trả lỗi: %s" % r.text[:200])
	return r.json()


@frappe.whitelist()
def aha_dich_vu():
	"""Loai xe va add-on that cua Ahamove tai TPHCM, de app dung man goi xe."""
	if not _la_sales():
		frappe.throw("Chỉ sales gọi xe được.")
	c = cfg()
	if not (key(c, "ahamove_api_key") and c.ahamove_base):
		frappe.throw("Chưa cấu hình Ahamove trong Vagabond Settings.")
	ck = "vgb:aha:dichvu2"
	hit = cache_get(ck)
	if hit:
		# Phai nho ca goi {dich_vu, mac_dinh}, khong nho moi danh sach dich vu:
		# nho thieu thi lan goi sau app nhan ve mang tran, doc .dich_vu ra rong
		# va bao "Ahamove khong tra ve loai xe nao".
		return json.loads(hit)
	ds = _aha_goi(c, "/v3/services?city_id=SGN") or []
	ra = []
	for sv in ds:
		ma = sv.get("_id") or ""
		if "TRUCK" in ma:
			continue
		addon = []
		for rq in sv.get("requests") or []:
			duoi = (rq.get("_id") or "").replace(ma + "-", "")
			if duoi not in AHA_ADDON_HIEN:
				continue
			addon.append({
				"id": rq.get("_id"),
				"ten": (rq.get("name") or "").strip(),
				"gia": flt(rq.get("price") or 0),
			})
		ra.append({"id": ma, "ten": sv.get("name") or ma, "addon": addon})
	mac_dinh = (c.ma_dich_vu or "SGN-BIKE").strip()
	ra.sort(key=lambda x: 0 if x["id"] == mac_dinh else 1)
	goi = {"dich_vu": ra, "mac_dinh": mac_dinh}
	cache_set(ck, json.dumps(goi), 3600)
	return goi


@frappe.whitelist()
def aha_bao_gia(name, service_id=None, requests_them=None):
	"""Gia that cua Ahamove cho dung don nay, kem add-on da tick.

	Endpoint hoi phi dung `services: [{_id, requests}]`, KHAC endpoint tao don
	(dung service_id + requests o cap cao nhat). Truyen nham la 404.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales gọi xe được.")
	from vagabond.dia_chi import geocode

	if isinstance(requests_them, str):
		requests_them = json.loads(requests_them or "[]")
	c = cfg()
	doc = frappe.get_doc("Van Don", name)
	if not (doc.dia_chi or "").strip():
		frappe.throw("Vận đơn chưa có địa chỉ giao.")
	toa = geocode(c, doc.dia_chi)
	if not toa or not toa.get("lat"):
		frappe.throw("Không tìm được toạ độ cho địa chỉ này, sửa lại địa chỉ giúp em.")
	diem = _diem_lay(c)
	body = {
		"order_time": 0,
		"path": [
			{"lat": diem["lat"], "lng": diem["lng"], "address": c.kitchen_address or ""},
			{"lat": toa["lat"], "lng": toa["lng"], "address": doc.dia_chi,
				"cod": flt(doc.tien_thu_ho) or 0},
		],
		"services": [{
			"_id": (service_id or c.ma_dich_vu or "SGN-BIKE").strip(),
			"requests": [{"_id": r} for r in (requests_them or []) if r],
		}],
		"payment_method": "BALANCE",
	}
	kq = _aha_goi(c, "/v3/orders/estimates", "POST", body)
	# Endpoint nay tra ve MANG: [{service_id, data:{...}, error}].
	# Truoc day doc thang .get() nen no van ra AttributeError 'list' object.
	if isinstance(kq, list):
		dau = (kq[0] if kq else {}) or {}
		loi = dau.get("error")
		if loi:
			frappe.throw("Ahamove: %s" % (loi if isinstance(loi, str) else str(loi))[:200])
		d = dau.get("data") or {}
	else:
		d = (kq or {}).get("data") or kq or {}
	# total_pay bang 0 khi tai khoan tra sau, nen lay total_fee lam gia chinh.
	tong = flt(d.get("total_fee") or d.get("total_pay") or 0)
	return {
		"tong": tong,
		"km": flt(d.get("distance") or 0),
		"phut": int(flt(d.get("duration") or 0) / 60),
		"phi_duong": flt(d.get("distance_fee") or 0),
		"phi_them": flt(d.get("request_fee") or 0),
		"giam": flt(d.get("discount") or 0),
	}


@frappe.whitelist(allow_guest=True)
def aha_webhook():
	"""Ahamove bao trang thai don. Quan tam nhat la tai xe huy.

	Khong xac thuc duoc bang chu ky nen chi tin phan doc: tra cuu lai don theo
	booking_id da luu, khong lay so lieu tien tu webhook.
	"""
	try:
		d = frappe.local.form_dict or {}
		if isinstance(d.get("data"), dict):
			d = d["data"]
		oid = str(d.get("_id") or d.get("order_id") or "").strip()
		tt = (d.get("status") or "").upper()
		if not oid:
			return {"ok": 0}
		name = frappe.db.get_value("Van Don", {"booking_id": oid}, "name")
		if not name:
			return {"ok": 0}
		if tt in ("CANCELLED", "CANCELED", "FAILED"):
			doc = frappe.get_doc("Van Don", name)
			if doc.trang_thai in ("Đã giao", "Huỷ"):
				return {"ok": 1}
			doc.booking_id = ""
			doc.tracking_url = ""
			doc.trang_thai = "Chờ giao"
			doc.ly_do_loi = "Tài xế Ahamove huỷ đơn"
			doc.flags.ignore_permissions = True
			doc.save()
			frappe.db.commit()
			_mail_tai_xe_huy(doc)
		return {"ok": 1}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: aha webhook loi")
		return {"ok": 0}


def _mail_tai_xe_huy(doc):
	"""Bao sales de phan cong lai ngay, khong de don nam im."""
	try:
		ds = frappe.get_all(
			"Has Role",
			filters={"role": "Sales User", "parenttype": "User"},
			fields=["parent"],
		)
		nhan = [r.parent for r in ds if r.parent not in ("Administrator", "Guest")
			and frappe.db.get_value("User", r.parent, "enabled")]
		if not nhan:
			return
		from vagabond.nhan_su import thu_tai_xe_huy_html

		frappe.sendmail(
			recipients=nhan,
			subject="Tài xế huỷ đơn: %s - %s" % (doc.ma_don or doc.name, doc.khach or ""),
			message=thu_tai_xe_huy_html(doc),
			delayed=False,
			retry=2,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: mail tai xe huy loi")


# ---------------------------------------------------------------- Chi phi shipper

@frappe.whitelist()
def tao_chi_phi(loai, so_tien, ngay=None, so_hoa_don=None, nha_cung_cap=None, ghi_chu=None, file_url=None):
	if not (_la_shipper() or _la_sales() or _la_ke_toan()):
		frappe.throw("Tài khoản chưa được cấp quyền khai chi phí.")
	doc = frappe.get_doc(
		{
			"doctype": "Chi Phi Shipper",
			"shipper": frappe.session.user,
			"ngay": ngay or nowdate(),
			"loai": loai,
			"so_tien": flt(so_tien),
			"so_hoa_don": so_hoa_don,
			"nha_cung_cap": nha_cung_cap,
			"ghi_chu": ghi_chu,
			"anh_hoa_don": file_url,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def gan_anh(doctype, name, fieldname, file_url):
	"""Gan anh vua upload vao truong Attach (anh_giao / anh_hoa_don)."""
	_kiem_quyen_xem()
	if doctype not in ("Van Don", "Chi Phi Shipper") or fieldname not in ("anh_giao", "anh_hoa_don", "chu_ky"):
		frappe.throw("Không hợp lệ.")
	frappe.db.set_value(doctype, name, fieldname, file_url)
	return name


@frappe.whitelist()
def chi_phi_danh_sach(trang_thai=None, tu_ngay=None):
	"""Ke toan / thu mua thay het; shipper chi thay cua minh."""
	if not (_la_shipper() or _la_ke_toan() or _la_sales()):
		frappe.throw("Không có quyền.")
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tu_ngay:
		loc["ngay"] = [">=", tu_ngay]
	if _la_shipper() and not _la_ke_toan():
		loc["shipper"] = frappe.session.user
	return frappe.get_all(
		"Chi Phi Shipper",
		filters=loc,
		fields=["name", "shipper", "ngay", "loai", "so_tien", "so_hoa_don", "nha_cung_cap",
			"anh_hoa_don", "ghi_chu", "trang_thai", "ghi_chu_duyet", "ngay_hoan_ung"],
		order_by="ngay desc, creation desc",
		limit_page_length=200,
	)


@frappe.whitelist()
def duyet_chi_phi(name, hanh_dong, ghi_chu=None):
	"""hanh_dong: duyet / tu_choi / hoan_ung. Chi Thu mua / Ke toan."""
	if not _la_ke_toan():
		frappe.throw("Chỉ Thu mua hoặc Kế toán duyệt được.")
	doc = frappe.get_doc("Chi Phi Shipper", name)
	if hanh_dong == "duyet":
		doc.trang_thai = "Đã duyệt"
	elif hanh_dong == "tu_choi":
		doc.trang_thai = "Từ chối"
	elif hanh_dong == "hoan_ung":
		doc.trang_thai = "Đã hoàn ứng"
		doc.ngay_hoan_ung = nowdate()
	else:
		frappe.throw("Hành động không hợp lệ.")
	doc.nguoi_duyet = frappe.session.user
	if ghi_chu:
		doc.ghi_chu_duyet = ghi_chu
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.trang_thai


# ---------------------------------------------------------------- Don dep anh

def don_dep_anh_giao():
	"""Cron chay hang ngay: xoa anh giao hang cua van don qua 30 ngay.
	Chi dong vao anh_giao cua Van Don; anh hoa don chi phi giu nguyen."""
	moc = add_days(nowdate(), -30)
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Van Don",
			"creation": ["<", moc],
		},
		fields=["name", "attached_to_name", "file_url"],
		limit_page_length=500,
	)
	for f in files:
		try:
			vd = frappe.db.get_value("Van Don", f.attached_to_name, "anh_giao")
			frappe.delete_doc("File", f.name, ignore_permissions=True, force=True)
			if vd and vd == f.file_url:
				frappe.db.set_value("Van Don", f.attached_to_name, "anh_giao", None)
		except Exception:
			frappe.log_error(title="Vagabond: don dep anh giao loi", message=frappe.get_traceback())
	frappe.db.commit()


@frappe.whitelist()
def mon_van_don(name=None):
	"""Danh sach mon day du cua mot van don, cho man chi tiet.

	Bang mon trong van don la nguon chinh. Chua co dong nao (van don keo ve
	tu truoc khi co bang nay) thi tu nap mot lan tu Pancake roi luu lai, lan
	sau khoi phai goi ra ngoai nua.
	"""
	_kiem_quyen_xem()
	d = frappe.db.get_value("Van Don", name, ["name", "pancake_id", "hoa_don"], as_dict=True)
	if not d:
		frappe.throw("Không thấy vận đơn %s" % name)
	mon = frappe.get_all(
		"Van Don Mon",
		filters={"parent": d.name},
		fields=["ma_hang", "ten", "so_luong", "gia", "tang", "ghi_chu"],
		order_by="idx asc",
		limit_page_length=0,
	)
	if mon:
		return mon
	nap = _mon_tu_pancake(_don_pancake(d.pancake_id)) if d.pancake_id else []
	if not nap:
		nap = _mon_tu_hoa_don(d.hoa_don)
	if nap:
		_ghi_mon(d.name, nap)
	return nap


@frappe.whitelist()
def nap_mon_thieu(ngay=None, gioi_han=60, lam_lai=0):
	"""Nap bu danh sach mon cho cac van don cu chua co.

	Chay tay mot lan cho du lieu cu. Moi don goi Pancake mot lan nen co gioi
	han so don moi luot, chay lai vai luot la het.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales và kế toán nạp được danh sách món.")
	loc = {}
	if ngay:
		loc["ngay_giao"] = ngay
	ds = frappe.get_all("Van Don", filters=loc, fields=["name", "pancake_id", "hoa_don"],
		order_by="ngay_giao desc", limit_page_length=500)
	xong, bo_qua = 0, 0
	for d in ds:
		if xong >= int(gioi_han or 60):
			break
		if not cint(lam_lai) and frappe.db.exists("Van Don Mon", {"parent": d.name}):
			continue
		nap = _mon_tu_pancake(_don_pancake(d.pancake_id)) if d.pancake_id else []
		if not nap:
			nap = _mon_tu_hoa_don(d.hoa_don)
		if nap:
			_ghi_mon(d.name, nap)
			xong += 1
		else:
			bo_qua += 1
	frappe.db.commit()
	return {"da_nap": xong, "khong_co_du_lieu": bo_qua, "tong_xet": len(ds)}


@frappe.whitelist()
def luu_chu_ky(name=None, anh=None, nguoi_ky=None):
	"""Luu chu ky khach ky tay tren man hinh cam ung vao van don.

	Anh gui len la data URL PNG cua the canvas. Luu thanh TEP dinh kem chu
	khong nhet chuoi base64 vao truong Data - de con mo lai, in ra, va de
	khong phinh bang du lieu.

	Chu ky la chung tu giao nhan nen KHONG nam trong dien don dep anh sau 30
	ngay (cron chi dong vao anh_giao).
	"""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if not anh or "," not in anh:
		frappe.throw("Chưa có nét ký nào.")
	dau, phan = anh.split(",", 1)
	if "image/png" not in dau:
		frappe.throw("Chữ ký phải là ảnh PNG.")
	if len(phan) > 900000:
		frappe.throw("Chữ ký nặng quá, ký lại giúp em.")

	tep = frappe.get_doc({
		"doctype": "File",
		"file_name": "chu-ky-%s.png" % doc.name,
		"attached_to_doctype": "Van Don",
		"attached_to_name": doc.name,
		"attached_to_field": "chu_ky",
		"is_private": 0,
		"content": phan,
		"decode": True,
	})
	tep.flags.ignore_permissions = True
	tep.insert(ignore_permissions=True)

	doc.chu_ky = tep.file_url
	doc.nguoi_ky = (nguoi_ky or doc.nguoi_nhan or doc.khach or "").strip()
	doc.ky_luc = now_datetime()
	doc.khong_ky = ""
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "chu_ky": doc.chu_ky, "nguoi_ky": doc.nguoi_ky, "ky_luc": str(doc.ky_luc)}


@frappe.whitelist()
def khach_khong_ky(name=None, ly_do=None):
	"""Khach khong ky duoc (gui bao ve, giao qua cua, khach ban tay).

	Van cho hoan thanh don - chan shipper lai vi mot chu ky la ket ca tuyen.
	Chi ghi lai ly do de sau con doi chieu.
	"""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	doc.khong_ky = (ly_do or "Khách không ký").strip()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "khong_ky": doc.khong_ky}
