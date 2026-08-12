"""Xep tuyen giao banh: gom don trong ngay thanh cac chuyen hop ly cho shipper.

Bai toan that cua tiem (do tren 292 don 26/07 - 04/08/2026):
- Ngay dong nhat 54 don, rai tren 32 phuong, trong do 22 phuong chi co 1 don.
  Nghia la LOC THEO PHUONG khong du de xep tuyen - phai gom theo cum toa do.
- 74% don co the khung gio 2 tieng (83..96). Don khong co the thi coi nhu ca buoi.
- Banh kem giao lien, khong de lau tren xe -> uu tien dung khung gio, roi moi
  toi quang duong.

Cach giai (du dung o quy mo vai chuc don, khong can solver nang):
1. Loc don theo ngay + buoi, lay toa do (geocode mot lan roi luu vao van don).
2. Dung ma tran thoi gian: mac dinh duong chim bay * he so 1.4 / toc do trung
   binh; bat co "dung Goong" thi goi Distance Matrix cho so lieu that.
3. Chen re nhat co rang buoc khung gio (cheapest insertion for VRPTW):
   don co han chot som duoc xep truoc, moi don thu chen vao moi vi tri cua moi
   tuyen, chon cho lam tang thoi gian it nhat ma khong lam tre don nao.
4. Cai thien tung tuyen bang 2-opt, van tinh phat neu tre khung gio.

Ket qua tra ve la DE XUAT - sales nhin, sua tay neu muon, roi bam chot.
"""

import json
import math

import frappe
import requests
from frappe.utils import cint, flt, nowdate

from vagabond.lib import GOONG, TIMEOUT, cfg, key

# Khung buoi (gio bat dau, gio ket thuc)
BUOI = {"Sáng": (7, 12), "Chiều": (12, 17), "Tối": (17, 22)}

# Phat moi phut tre khung gio, quy ra "phut di duong". Dat cao vi khach doi
# banh sinh nhat dung gio quan trong hon viec shipper chay them vai cay so.
PHAT_TRE = 12.0
# Toi da so vi tri thu 2-opt cho moi tuyen (chan vong lap qua lau).
VONG_2OPT = 30


# ------------------------------------------------------------- khung gio

def khung_gio(tag):
	"""'15h - 17h' -> (900, 1020) tinh bang phut tu 0h. Khong doc duoc tra None."""
	s = str(tag or "").strip().lower().replace("-", "-").replace("-", "-")
	if not s:
		return None
	phan = [p.strip() for p in s.split("-")]
	if len(phan) != 2:
		return None
	ra = []
	for p in phan:
		p = p.replace("h", ":").strip(": ")
		if not p:
			return None
		bit = p.split(":")
		try:
			gio = int(bit[0])
			phut = int(bit[1]) if len(bit) > 1 and bit[1] else 0
		except ValueError:
			return None
		ra.append(gio * 60 + phut)
	if ra[1] <= ra[0]:
		return None
	return (ra[0], ra[1])


def buoi_tu_khung(tag):
	"""Xep khung gio vao buoi theo GIO BAT DAU."""
	kg = khung_gio(tag)
	if not kg:
		return ""
	gio = kg[0] // 60
	for ten, (d, c) in BUOI.items():
		if d <= gio < c:
			return ten
	return "Tối" if gio >= 17 else "Sáng"


# ------------------------------------------------------------- khoang cach

def haversine(lat1, lng1, lat2, lng2):
	"""Duong chim bay, km."""
	r = 6371.0
	p1, p2 = math.radians(lat1), math.radians(lat2)
	dp = math.radians(lat2 - lat1)
	dl = math.radians(lng2 - lng1)
	a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
	return 2 * r * math.asin(math.sqrt(a))


def _ma_tran_uoc_luong(diem, he_so, toc_do):
	"""Ma tran (km, phut) uoc luong tu duong chim bay. Khong ton tien API."""
	n = len(diem)
	km = [[0.0] * n for _ in range(n)]
	phut = [[0.0] * n for _ in range(n)]
	for i in range(n):
		for j in range(n):
			if i == j:
				continue
			d = haversine(diem[i]["lat"], diem[i]["lng"], diem[j]["lat"], diem[j]["lng"]) * he_so
			km[i][j] = d
			phut[i][j] = d / max(toc_do, 5.0) * 60.0
	return km, phut


def _ma_tran_goong(diem, he_so, toc_do):
	"""Goi Goong Distance Matrix cho so lieu duong that.

	Goong nhan nhieu origins va destinations trong mot lan goi, ngan cach bang
	dau |. Hong hay thieu o nao thi lay so uoc luong bu vao, khong de tuyen
	chet vi mot phan tu loi.
	"""
	c = cfg()
	k = key(c, "goong_api_key")
	km, phut = _ma_tran_uoc_luong(diem, he_so, toc_do)
	if not k or len(diem) < 2:
		return km, phut
	toa = "|".join("%s,%s" % (d["lat"], d["lng"]) for d in diem)
	try:
		r = requests.get(
			GOONG + "/DistanceMatrix",
			params={"origins": toa, "destinations": toa, "vehicle": "bike", "api_key": k},
			timeout=TIMEOUT * 2,
		)
		r.raise_for_status()
		rows = (r.json() or {}).get("rows") or []
	except Exception:
		frappe.log_error(title="Vagabond: Goong DistanceMatrix loi", message=frappe.get_traceback())
		return km, phut
	for i, row in enumerate(rows[: len(diem)]):
		for j, o in enumerate((row.get("elements") or [])[: len(diem)]):
			if i == j or (o.get("status") or "OK") != "OK":
				continue
			d = ((o.get("distance") or {}).get("value") or 0) / 1000.0
			t = ((o.get("duration") or {}).get("value") or 0) / 60.0
			if d > 0:
				km[i][j] = d
			if t > 0:
				phut[i][j] = t
	return km, phut


# ------------------------------------------------------------- mo phong tuyen

def _chay_tuyen(seq, diem, phut, km, bat_dau, phut_dung):
	"""Mo phong mot tuyen. Tra (tong_phut_di, tong_tre, tong_km, moc_den).

	moc_den[i] la phut trong ngay luc toi diem seq[i]. Toi som hon khung gio
	thi shipper cho (khach chua san sang nhan banh), toi muon hon khung gio
	thi tinh la tre.
	"""
	t = float(bat_dau)
	truoc = 0
	di, tre, tong_km, moc = 0.0, 0.0, 0.0, []
	for i in seq:
		di += phut[truoc][i]
		tong_km += km[truoc][i]
		t += phut[truoc][i]
		kg = diem[i].get("kg")
		if kg:
			if t < kg[0]:
				t = kg[0]
			if t > kg[1]:
				tre += t - kg[1]
		moc.append(t)
		t += phut_dung
		truoc = i
	return di, tre, tong_km, moc


def _gia(seq, diem, phut, km, bat_dau, phut_dung):
	di, tre, _, _ = _chay_tuyen(seq, diem, phut, km, bat_dau, phut_dung)
	return di + PHAT_TRE * tre


def _hai_opt(seq, diem, phut, km, bat_dau, phut_dung):
	"""Dao doan de bot duong chay chong cheo, van giu rang buoc khung gio."""
	if len(seq) < 4:
		return seq
	tot = _gia(seq, diem, phut, km, bat_dau, phut_dung)
	for _ in range(VONG_2OPT):
		cai_thien = False
		for i in range(len(seq) - 1):
			for j in range(i + 2, len(seq)):
				thu = seq[:i + 1] + seq[i + 1:j + 1][::-1] + seq[j + 1:]
				g = _gia(thu, diem, phut, km, bat_dau, phut_dung)
				if g < tot - 0.01:
					seq, tot, cai_thien = thu, g, True
		if not cai_thien:
			break
	return seq


def xep(diem, so_tuyen, bat_dau, phut_dung, toi_da, phut, km):
	"""Chen re nhat co rang buoc khung gio. diem[0] la diem lay banh.

	Don co han chot som duoc xep truoc; moi don thu moi vi tri cua moi tuyen,
	chon cho lam tang gia it nhat. Het cho hop le thi van nhan vao cho re nhat
	va danh dau tre - khong bao gio bo roi don nao.
	"""
	con = list(range(1, len(diem)))
	con.sort(key=lambda i: ((diem[i].get("kg") or (9999, 9999))[1], (diem[i].get("kg") or (0, 0))[0]))
	tuyen = [[] for _ in range(max(1, so_tuyen))]
	for i in con:
		tot_t, tot_v, tot_g = None, None, None
		for ti, t in enumerate(tuyen):
			if len(t) >= toi_da:
				continue
			for vi in range(len(t) + 1):
				thu = t[:vi] + [i] + t[vi:]
				g = _gia(thu, diem, phut, km, bat_dau, phut_dung)
				# uu tien tuyen dang it don de khong don het vao mot nguoi
				g += len(t) * 0.4
				if tot_g is None or g < tot_g:
					tot_t, tot_v, tot_g = ti, vi, g
		if tot_t is None:  # moi tuyen deu day
			tot_t = min(range(len(tuyen)), key=lambda x: len(tuyen[x]))
			tot_v = len(tuyen[tot_t])
		tuyen[tot_t] = tuyen[tot_t][:tot_v] + [i] + tuyen[tot_t][tot_v:]
	return [_hai_opt(t, diem, phut, km, bat_dau, phut_dung) for t in tuyen if t]


# ------------------------------------------------------------- toa do van don

def _toa_do(doc_dict, c):
	"""Lay lat/lng cua van don; chua co thi geocode roi luu lai vao ban ghi."""
	if flt(doc_dict.get("lat")) and flt(doc_dict.get("lng")):
		return flt(doc_dict["lat"]), flt(doc_dict["lng"])
	dc = (doc_dict.get("dia_chi") or "").strip()
	if not dc:
		return None
	from vagabond.dia_chi import geocode

	toa = geocode(c, dc)
	if not toa or not toa.get("lat"):
		return None
	frappe.db.set_value("Van Don", doc_dict["name"], {"lat": toa["lat"], "lng": toa["lng"]}, update_modified=False)
	return flt(toa["lat"]), flt(toa["lng"])


def _diem_lay_cf(c, ten):
	if ten == "Tiệm":
		return {"lat": flt(c.store_lat), "lng": flt(c.store_lng), "ten": "Tiệm 9 Trần Cao Vân"}
	return {"lat": flt(c.kitchen_lat), "lng": flt(c.kitchen_lng), "ten": "Bếp Nguyễn Văn Trỗi"}


def _hhmm(phut):
	phut = int(round(phut))
	return "%02d:%02d" % ((phut // 60) % 24, phut % 60)


# ------------------------------------------------------------- endpoint

@frappe.whitelist()
def de_xuat_tuyen(ngay=None, buoi=None, so_tuyen=2, diem_lay="Bếp", chi_don_trong=1, dung_goong=None):
	"""De xuat cach chia don trong buoi thanh cac chuyen.

	chi_don_trong = 1: chi xep don CHUA gan shipper (khong dung vao chuyen
	dang chay cua ai). De 0 thi xep lai toan bo don chua giao cua buoi do.
	"""
	from vagabond.van_don import _la_sales

	if not _la_sales():
		frappe.throw("Chỉ sales xếp tuyến được.")
	ngay = ngay or nowdate()
	so_tuyen = max(1, cint(so_tuyen) or 2)
	c = cfg()
	toc_do = flt(c.get("toc_do_km_h")) or 20.0
	he_so = flt(c.get("he_so_duong_thuc")) or 1.4
	phut_dung = cint(c.get("phut_moi_diem")) or 6
	toi_da = cint(c.get("so_don_toi_da_chuyen")) or 12
	if dung_goong is None:
		dung_goong = cint(c.get("dung_goong_xep_tuyen"))

	loc = {"ngay_giao": ngay, "trang_thai": "Chờ giao", "kenh": "Shipper nội bộ"}
	ds = frappe.get_all(
		"Van Don", filters=loc,
		fields=["name", "ma_don", "khach", "sdt", "dia_chi", "phuong", "tag_gio", "buoi",
			"tien_thu_ho", "lat", "lng", "shipper", "chuyen", "goi_truoc", "chup_truoc", "ghi_chu_in"],
		limit_page_length=500,
	)
	if cint(chi_don_trong):
		ds = [d for d in ds if not d.shipper]
	if buoi:
		ds = [d for d in ds if (d.buoi or buoi_tu_khung(d.tag_gio) or "") == buoi]

	bo_qua = []
	diem = [dict(_diem_lay_cf(c, diem_lay), kg=None, don=None)]
	for d in ds:
		toa = _toa_do(d, c)
		if not toa:
			bo_qua.append({"ma_don": d.ma_don, "ly_do": "không tìm được toạ độ", "dia_chi": d.dia_chi})
			continue
		diem.append({"lat": toa[0], "lng": toa[1], "kg": khung_gio(d.tag_gio), "don": d})

	if len(diem) < 2:
		return {"ngay": str(ngay), "buoi": buoi or "", "tuyen": [], "bo_qua": bo_qua,
			"thong_bao": "Không có đơn nội bộ nào đang chờ giao để xếp tuyến."}

	km, phut = (_ma_tran_goong if dung_goong else _ma_tran_uoc_luong)(diem, he_so, toc_do)
	gio_bd = BUOI.get(buoi, (8, 22))[0] * 60
	som_nhat = [d["kg"][0] for d in diem[1:] if d["kg"]]
	if som_nhat:
		gio_bd = min(gio_bd, min(som_nhat) - 20)

	tuyen = xep(diem, so_tuyen, gio_bd, phut_dung, toi_da, phut, km)

	ra = []
	for idx, seq in enumerate(tuyen, 1):
		di, tre, tong_km, moc = _chay_tuyen(seq, diem, phut, km, gio_bd, phut_dung)
		diem_dung = []
		truoc = 0
		for k2, i in enumerate(seq):
			d = diem[i]["don"]
			kg = diem[i]["kg"]
			diem_dung.append({
				"name": d.name, "ma_don": d.ma_don, "khach": d.khach, "sdt": d.sdt,
				"dia_chi": d.dia_chi, "phuong": d.phuong, "tag_gio": d.tag_gio,
				"tien_thu_ho": flt(d.tien_thu_ho), "ghi_chu_in": d.ghi_chu_in,
				"goi_truoc": d.goi_truoc, "chup_truoc": d.chup_truoc,
				"thu_tu": k2 + 1, "gio_du_kien": _hhmm(moc[k2]),
				"km_chang": round(km[truoc][i], 2),
				"tre": 1 if (kg and moc[k2] > kg[1] + 0.5) else 0,
				"lat": diem[i]["lat"], "lng": diem[i]["lng"],
			})
			truoc = i
		ra.append({
			"tuyen": idx, "so_don": len(seq), "tong_km": round(tong_km, 1),
			"phut_di": int(round(di)), "phut_tre": int(round(tre)),
			"bat_dau": _hhmm(gio_bd), "ket_thuc": _hhmm(moc[-1] + phut_dung) if moc else _hhmm(gio_bd),
			"tong_cod": sum(x["tien_thu_ho"] for x in diem_dung),
			"diem_lay": diem[0]["ten"], "diem": diem_dung,
			"link_chi_duong": _link_maps(diem[0], diem_dung),
		})
	return {
		"ngay": str(ngay), "buoi": buoi or "cả ngày", "diem_lay": diem[0]["ten"],
		"nguon_khoang_cach": "Goong" if dung_goong else "ước lượng",
		"tuyen": ra, "bo_qua": bo_qua,
	}


def _link_maps(diem_lay, diem_dung):
	"""Link Google Maps chi duong ca tuyen theo dung thu tu - shipper bam mot
	phat la co ca lo trinh, khoi go tung dia chi."""
	if not diem_dung:
		return ""
	toa = ["%s,%s" % (diem_lay["lat"], diem_lay["lng"])] + ["%s,%s" % (d["lat"], d["lng"]) for d in diem_dung]
	u = "https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=%s&destination=%s" % (toa[0], toa[-1])
	giua = toa[1:-1]
	if giua:
		u += "&waypoints=" + "|".join(giua)
	return u


@frappe.whitelist()
def chot_tuyen(tuyen):
	"""Sales duyet de xuat: gan shipper + ghi thu tu, gio du kien vao tung don.

	tuyen: json list [{"shipper": "...", "chuyen": "" hoac ma chuyen dang chay,
	"diem": [{"name","thu_tu","gio_du_kien","km_chang","tre"}]}]
	"""
	from vagabond.van_don import _la_sales, gop_chuyen

	if not _la_sales():
		frappe.throw("Chỉ sales chốt tuyến được.")
	if isinstance(tuyen, str):
		tuyen = json.loads(tuyen)
	ra = []
	for t in tuyen or []:
		diem = t.get("diem") or []
		if not diem:
			continue
		if not t.get("shipper"):
			frappe.throw("Tuyến %s chưa chọn shipper." % (t.get("tuyen") or ""))
		kq = gop_chuyen([d["name"] for d in diem], t["shipper"], t.get("chuyen") or None)
		for d in diem:
			frappe.db.set_value("Van Don", d["name"], {
				"thu_tu": cint(d.get("thu_tu")),
				"gio_du_kien": d.get("gio_du_kien") or "",
				"km_chang": flt(d.get("km_chang")),
				"tre_khung_gio": cint(d.get("tre")),
			}, update_modified=False)
		ra.append(kq)
	frappe.db.commit()
	return ra
