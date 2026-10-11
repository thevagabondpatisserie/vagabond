"""Chuong trinh khuyen mai, combo va ma voucher (anh Viet chot 11/08/2026).

NGUYEN TAC SO MOT: may chu KHONG BAO GIO tin so tien giam do may khach gui
len. May khach chi gui LEN danh sach ma chuong trinh va ma voucher; may chu
tu doc gio hang, tu tinh lai tu dau roi moi ghi vao hoa don. Neu tin so tien
tu may khach thi bat ky ai mo Devtools cung tu giam bill cua minh ve 0.

Bay cach thuc anh Viet liet ke, may deu tinh o mot cho duy nhat la _tinh_mot:
  1. Giam tong hoa don   - % hoac so tien tren tong (hoac tren mot nhom mon)
  2. Giam gia mon        - giam tren tung dong mon chi dinh
  3. Mua A giam B        - mua du mon A thi mon B duoc giam
  4. Mua X tang Y        - mua du X phan thi Y phan mien phi
  5. Tang mon            - dat dieu kien thi tang han mot mon
  6. Dong gia            - keo mon ve mot muc gia co dinh
  7. Giam luy ke         - bac thang, hoa don cang lon giam cang sau

COMBO tach rieng khoi bay cach thuc tren vi cach hoat dong khac han: cashier
bam ma combo thi may RA combo thanh tung mon thanh phan roi dat mot dong giam
gia ben duoi. Bill in ra khong he co chu "combo" - bep va tem dan mon van
thay ten mon that, kiem banh van tru dung tung ma banh.
"""

import csv
import io
import json
import re

import frappe

from vagabond import diem_ban
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, nowdate

# ------------------------------------------------------------------ tien ich

CHU_MA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # bo O/0 va I/1 cho khoi doc nham
DAI_MA = 6

QUYEN_KM = {"System Manager", "Sales User", "Sales Manager"}  # 01/10: gỡ Bộ phận đặt hàng (vai thu mua)
# "VGB - Quan ly khuyen mai" la vai tro rieng cua tiem, dat ra 12/08/2026 cho
# quan ly cua hang. Khong cap thang Sales Manager vi vai tro do con mo them
# ca sua diem ban, sua phuong thuc thanh toan (ke ca ma gui co quan thue) va
# tu ha muc quyen bo mon cua chinh nhan vien minh - quan ly cua hang khong
# nen cam ba thu do.
QUYEN_SUA_KM = {"System Manager", "Sales Manager", "VGB - Quản lý khuyến mãi"}

# Nhan hien thi cho nguoi dung. Trong DB luu khong dau de khoi vo Select khi
# doi encoding, con ra man hinh thi phai co dau cho de doc.
NHAN_CACH_THUC = {
	"Giam tong hoa don": "Giảm tổng hoá đơn",
	"Giam gia mon": "Giảm giá món",
	"Mua A giam B": "Mua A giảm B",
	"Mua X tang Y": "Mua X tặng Y",
	"Tang mon": "Tặng món",
	"Dong gia": "Đồng giá",
	"Giam luy ke": "Giảm luỹ kế",
}


def _kiem_quyen():
	if not QUYEN_KM & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền dùng chương trình khuyến mãi.")


def _kiem_quyen_sua():
	if not QUYEN_SUA_KM & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý mới được tạo và sửa chương trình khuyến mãi. "
			"Bạn cần thay đổi thì báo quản lý ca."
		)


def _dong(s):
	"""Mot o Small Text nhieu dong -> danh sach da bo dong trong."""
	return [x.strip() for x in str(s or "").splitlines() if x.strip()]


def _vnd(n):
	return int(round(flt(n)))


def _nhom_cua_mon(ds_ma):
	"""Nhom mon (Item Group) cua mot loat ma hang, doc mot lan cho ca gio."""
	ds_ma = [m for m in set(ds_ma) if m]
	if not ds_ma:
		return {}
	ds = frappe.get_all(
		"Item",
		filters={"name": ["in", ds_ma]},
		fields=["name", "item_group", "item_name"],
		limit_page_length=0,
	)
	return {r.name: {"nhom": r.item_group, "ten": r.item_name} for r in ds}


def _gio_hang(items):
	"""Chuan hoa gio hang tu may khach thanh danh sach dong co du thong tin."""
	if isinstance(items, str):
		items = json.loads(items or "[]")
	gio = []
	for i, r in enumerate(items or []):
		ma = str(r.get("item_code") or "").strip()
		if not ma:
			continue
		sl = flt(r.get("qty") or 0)
		gia = flt(r.get("rate") or 0)
		if sl <= 0:
			continue
		gio.append(
			{
				"i": i,
				"item_code": ma,
				"qty": sl,
				"rate": gia,
				"tien": sl * gia,
				"nhom": "",
				"ten": ma,
			}
		)
	tt = _nhom_cua_mon([d["item_code"] for d in gio])
	for d in gio:
		o = tt.get(d["item_code"]) or {}
		d["nhom"] = o.get("nhom") or ""
		d["ten"] = o.get("ten") or d["item_code"]
	return gio


# --------------------------------------------------------- dieu kien ap dung

THU_TRONG_TUAN = ["thu_2", "thu_3", "thu_4", "thu_5", "thu_6", "thu_7", "thu_cn"]


def _hop_thoi_gian(km, luc=None):
	"""Ngay, thu trong tuan va khung gio."""
	luc = get_datetime(luc) if luc else now_datetime()
	ngay = luc.date()
	if km.get("tu_ngay") and ngay < getdate(km["tu_ngay"]):
		return False, "chương trình chưa tới ngày bắt đầu"
	if km.get("den_ngay") and ngay > getdate(km["den_ngay"]):
		return False, "chương trình đã hết hạn"
	co_chon_thu = any(cint(km.get(t)) for t in THU_TRONG_TUAN)
	if co_chon_thu and not cint(km.get(THU_TRONG_TUAN[luc.weekday()])):
		return False, "hôm nay không nằm trong các thứ áp dụng"
	gt, gd = km.get("gio_tu"), km.get("gio_den")
	if gt and gd:
		gio = luc.strftime("%H:%M:%S")
		t1, t2 = str(gt), str(gd)
		if t1 <= t2:
			trong = t1 <= gio <= t2
		else:
			# Khung gio vat qua nua dem, vi du 21:00 - 02:00 (ca dem).
			trong = gio >= t1 or gio <= t2
		if not trong:
			return False, "ngoài khung giờ %s - %s" % (t1[:5], t2[:5])
	return True, ""


def _hop_kenh(km, nguon, quay):
	ds_kenh = _dong(km.get("kenh"))
	if ds_kenh and (nguon or "").strip() not in ds_kenh:
		return False, "không áp dụng cho nguồn đơn %s" % (nguon or "(trống)")
	ds_quay = [q.upper() for q in _dong(km.get("quay"))]
	# Don ban online cua Sales khong mang ma quay (o vgb_quay de trong), nen
	# quy uoc quay rong la SALES. Nho vay man cau hinh moi co du ba diem ban
	# de tick, khong bi thieu quay Sales (anh Viet 12/08/2026).
	this = (quay or "").strip().upper() or "SALES"
	if ds_quay and this not in ds_quay:
		return False, "không áp dụng cho quầy %s" % (quay or "Sales")
	return True, ""


def _hop_doi_tuong(km, khach, sdt):
	dt = km.get("doi_tuong") or "Moi khach"
	if dt == "Moi khach":
		return True, ""
	if dt == "Nhan vien":
		if not _la_sdt_nhan_vien(sdt):
			return False, "số điện thoại này không nằm trong danh sách nhân viên"
		return True, ""
	if not khach:
		return False, "chương trình này phải chọn khách hàng trước"
	if dt == "Theo hang khach":
		hang = frappe.db.get_value("Customer", khach, "vgb_hang") or ""
		ds = [h.strip().upper() for h in _dong(km.get("hang_khach"))]
		if hang.upper() not in ds:
			return False, "khách này hạng %s, không nằm trong hạng áp dụng" % (hang or "chưa xếp")
		return True, ""
	if dt == "Theo nhom khach":
		nhom = frappe.db.get_value("Customer", khach, "customer_group") or ""
		if nhom not in _dong(km.get("nhom_khach")):
			return False, "khách này thuộc nhóm %s, không nằm trong nhóm áp dụng" % (nhom or "?")
		return True, ""
	if dt == "Khach chi dinh":
		co = frappe.db.exists(
			"Vagabond CTKM Khach", {"parent": km["name"], "khach": khach}
		)
		if not co:
			return False, "khách này không nằm trong danh sách chỉ định"
		return True, ""
	return True, ""


def _la_sdt_nhan_vien(sdt):
	"""Hang FAMILY giam 20% cho so dien thoai nhan vien (anh Viet 11/08/2026).
	Nhan dien qua so dien thoai tren ho so nhan su, khong phai tu khai."""
	so = re.sub(r"\D", "", str(sdt or ""))
	if len(so) < 9:
		return False
	duoi = so[-9:]
	try:
		ds = frappe.get_all(
			"Employee",
			filters={"status": "Active"},
			fields=["cell_number", "personal_email"],
			limit_page_length=0,
		)
	except Exception:
		return False
	for r in ds:
		s2 = re.sub(r"\D", "", str(r.cell_number or ""))
		if s2 and s2[-9:] == duoi:
			return True
	return False


# ------------------------------------------------------------ han muc dung

def _dem_da_dung(ma_ctkm, ngay=None, thu_ngan=None, sdt=None):
	"""Dem so lan mot chuong trinh da duoc ap - de chan vuot han muc."""
	# Codex #460 (QT-20): lượt đã trả (đơn web bị từ chối hoặc huỷ) giữ lại để
	# tra, nhưng không còn tính vào hạn mức.
	loc = {"ctkm": ma_ctkm, "da_tra": 0}
	if ngay:
		loc["ngay"] = str(getdate(ngay))
	if thu_ngan:
		loc["thu_ngan"] = thu_ngan
	if sdt:
		so = re.sub(r"\D", "", str(sdt))
		if not so:
			return 0
		loc["sdt"] = so
	try:
		return frappe.db.count("Vagabond CTKM Su Dung", loc)
	except Exception:
		return 0


def _hop_han_muc(km, sdt=None, ngay=None):
	"""Tra (duoc_hay_khong, ly_do). Day la lop chan gian lan quan trong nhat:
	mot chuong trinh giam sau ma khong co han muc thi mot thu ngan co the bam
	ca tram lan trong mot ca."""
	ma = km["name"]
	ngay = ngay or nowdate()
	if cint(km.get("so_lan_toi_da")):
		if _dem_da_dung(ma) >= cint(km["so_lan_toi_da"]):
			return False, "chương trình đã dùng hết %d lượt" % cint(km["so_lan_toi_da"])
	if cint(km.get("lan_moi_ngay")):
		if _dem_da_dung(ma, ngay=ngay) >= cint(km["lan_moi_ngay"]):
			return False, "hôm nay đã dùng hết %d lượt của chương trình" % cint(km["lan_moi_ngay"])
	if cint(km.get("lan_moi_ca")):
		if _dem_da_dung(ma, ngay=ngay, thu_ngan=frappe.session.user) >= cint(km["lan_moi_ca"]):
			return False, "bạn đã dùng hết %d lượt của mình hôm nay" % cint(km["lan_moi_ca"])
	if cint(km.get("lan_moi_khach")) and sdt:
		if _dem_da_dung(ma, sdt=sdt) >= cint(km["lan_moi_khach"]):
			return False, "số điện thoại này đã dùng hết %d lượt" % cint(km["lan_moi_khach"])
	return True, ""


# ------------------------------------------------------------- doc chuong trinh

def _doc_ctkm(ma):
	d = frappe.get_doc("Vagabond CTKM", ma)
	o = d.as_dict()
	o["name"] = d.name
	o["dong_mon"] = [x.as_dict() for x in (d.dong_mon or [])]
	o["dong_bac"] = [x.as_dict() for x in (d.dong_bac or [])]
	return o


def _mon_theo_vai_tro(km, vai_tro):
	return [d for d in (km.get("dong_mon") or []) if (d.get("vai_tro") or "") == vai_tro]


def _dong_trong_pham_vi(km, gio):
	"""Nhung dong hang ma chuong trinh duoc phep dong toi."""
	pv = km.get("pham_vi") or "Ca hoa don"
	if pv == "Ca hoa don":
		return list(gio)
	if pv == "Nhom mon chi dinh":
		nhom = set(_dong(km.get("nhom_mon")))
		return [d for d in gio if d["nhom"] in nhom]
	ma_mon = {m.get("item_code") for m in _mon_theo_vai_tro(km, "Uu dai")}
	return [d for d in gio if d["item_code"] in ma_mon]


def _giam_theo_kieu(kieu, gia_tri, goc):
	if kieu == "So tien":
		return min(flt(gia_tri), flt(goc))
	return flt(goc) * flt(gia_tri) / 100.0


# -------------------------------------------------------------- bay cach thuc

def _tinh_mot(km, gio, tong_hd):
	"""Tinh so tien giam cua MOT chuong trinh tren gio hang.

	Tra ve dict: {giam, dien_giai, them_mon}. them_mon la mon duoc tang ma
	trong gio chua co - may khach se tu them dong do voi gia 0.
	"""
	cach = km.get("cach_thuc") or "Giam tong hoa don"
	kieu = km.get("kieu_giam") or "Phan tram"
	gt = flt(km.get("gia_tri"))
	them = []

	# Dieu kien chung: hoa don toi thieu va so luong mon toi thieu.
	if flt(km.get("hd_toi_thieu")) and tong_hd < flt(km["hd_toi_thieu"]):
		return {
			"giam": 0,
			"dien_giai": "hoá đơn chưa đạt %s" % _tien_chu(km["hd_toi_thieu"]),
			"them_mon": [],
		}
	if cint(km.get("sl_toi_thieu")) and sum(d["qty"] for d in gio) < cint(km["sl_toi_thieu"]):
		return {
			"giam": 0,
			"dien_giai": "hoá đơn chưa đủ %d món" % cint(km["sl_toi_thieu"]),
			"them_mon": [],
		}

	if cach == "Giam luy ke":
		bac = sorted(
			[b for b in (km.get("dong_bac") or []) if tong_hd >= flt(b.get("tu_tien"))],
			key=lambda b: flt(b.get("tu_tien")),
		)
		if not bac:
			return {"giam": 0, "dien_giai": "hoá đơn chưa đạt bậc thấp nhất", "them_mon": []}
		b = bac[-1]
		giam = _giam_theo_kieu(b.get("kieu_giam"), b.get("gia_tri"), tong_hd)
		if flt(b.get("tran")):
			giam = min(giam, flt(b["tran"]))
		return {
			"giam": giam,
			"dien_giai": "đạt bậc từ %s" % _tien_chu(b.get("tu_tien")),
			"them_mon": [],
		}

	if cach in ("Giam tong hoa don", "Giam gia mon"):
		dong = _dong_trong_pham_vi(km, gio)
		if not dong:
			return {"giam": 0, "dien_giai": "hoá đơn không có món nào thuộc phạm vi", "them_mon": []}
		# Dong nao co muc rieng thi theo muc rieng, phan con lai gop lai roi
		# moi ap muc chung MOT LAN.
		#
		# Phai gop truoc khi ap, khong duoc ap len tung dong: giam "50.000d
		# ca hoa don" ma chay tung dong thi hoa don ba mon thanh giam
		# 150.000d. Bat duoc luc nghiem thu tren may that 11/08/2026 - bill
		# 300.000d ra con 85.000d thay vi 250.000d.
		rieng = {
			m.get("item_code"): m
			for m in _mon_theo_vai_tro(km, "Uu dai")
			if m.get("kieu_giam") and flt(m.get("gia_tri"))
		}
		giam = 0.0
		goc_chung = 0.0
		for d in dong:
			r = rieng.get(d["item_code"])
			if r:
				giam += _giam_theo_kieu(r.get("kieu_giam"), r.get("gia_tri"), d["tien"])
			else:
				goc_chung += d["tien"]
		if goc_chung > 0:
			giam += _giam_theo_kieu(kieu, gt, goc_chung)
		nen = "cả hoá đơn" if (km.get("pham_vi") or "Ca hoa don") == "Ca hoa don" else "%d món trong phạm vi" % len(dong)
		return {"giam": giam, "dien_giai": "giảm trên %s" % nen, "them_mon": []}

	if cach == "Dong gia":
		dong = _dong_trong_pham_vi(km, gio)
		gd = flt(km.get("gia_dong"))
		giam = 0.0
		so = 0
		for d in dong:
			if d["rate"] > gd:
				giam += (d["rate"] - gd) * d["qty"]
				so += 1
		if not so:
			return {"giam": 0, "dien_giai": "không có món nào đang cao hơn giá đồng", "them_mon": []}
		return {"giam": giam, "dien_giai": "%d món về đồng giá %s" % (so, _tien_chu(gd)), "them_mon": []}

	# --- ba cach thuc con lai deu xoay quanh "mua du dieu kien thi duoc gi" ---
	uu_dai = _mon_theo_vai_tro(km, "Uu dai")
	if not uu_dai:
		return {"giam": 0, "dien_giai": "chương trình chưa khai món ưu đãi", "them_mon": []}
	dieu_kien = _mon_theo_vai_tro(km, "Dieu kien")

	con = {}
	for d in gio:
		con[d["item_code"]] = con.get(d["item_code"], 0) + d["qty"]
	# Lay gia THUC TE tren dong hang, khong lay gia bang gia: neu mon dang
	# duoc ban gia khac (mon le, mon test) thi tang mien phi phai tra dung
	# so tien do. Mon khong co trong gio moi tra ve bang gia.
	gia_mon = {}
	for d in gio:
		if d["item_code"] not in gia_mon:
			gia_mon[d["item_code"]] = d["rate"]

	def gia_cua(ma):
		return flt(gia_mon[ma] if ma in gia_mon else _gia_ban(ma))

	# Chia suat theo VONG, moi vong an mot bo dieu kien roi moi phat uu dai
	# tu phan CON LAI trong gio. Phai lam kieu nay vi mon tang thuong chinh
	# la mon dieu kien: "su kem mua 2 tang 1" voi 6 cai la 2 cai mien phi
	# (moi bo an 3 cai), khong phai 3 cai - neu tinh so bo trên rieng mon
	# dieu kien roi moi tru thi ra 3 bo ma khong con cai nao de tang, chuong
	# trinh thanh vo tac dung (bat duoc luc chay thu 11/08/2026).
	tran_vong = int(sum(d["qty"] for d in gio)) + 10
	so_bo = 0
	giam = 0.0
	tang_dem, giam_dem, thieu_dem = {}, {}, {}
	for _ in range(tran_vong):
		if dieu_kien:
			du = True
			for m in dieu_kien:
				can = flt(m.get("so_luong") or 1)
				if can <= 0:
					continue
				if con.get(m.get("item_code"), 0) < can - 0.0001:
					du = False
					break
			if not du:
				break
			for m in dieu_kien:
				ma = m.get("item_code")
				con[ma] = con.get(ma, 0) - flt(m.get("so_luong") or 1)
		so_bo += 1
		for m in uu_dai:
			ma = m.get("item_code")
			can = flt(m.get("so_luong") or 1)
			k = m.get("kieu_giam") or (
				"Tang mien phi" if cach in ("Mua X tang Y", "Tang mon") else kieu
			)
			v = flt(m.get("gia_tri")) or gt
			co = min(con.get(ma, 0), can)
			if co > 0:
				if k == "Tang mien phi":
					giam += gia_cua(ma) * co
					tang_dem[ma] = tang_dem.get(ma, 0) + co
				else:
					giam += _giam_theo_kieu(k, v, gia_cua(ma) * co)
					giam_dem[ma] = giam_dem.get(ma, 0) + co
				con[ma] = con.get(ma, 0) - co
			thieu = can - co
			if thieu > 0 and k == "Tang mien phi" and cach in ("Mua X tang Y", "Tang mon"):
				thieu_dem[ma] = thieu_dem.get(ma, 0) + thieu
		if not dieu_kien:
			break  # Tang mon: chi mot suat cho moi hoa don

	if so_bo < 1:
		return {"giam": 0, "dien_giai": "chưa mua đủ món điều kiện", "them_mon": []}

	ten_uu_dai = []
	for ma, n in tang_dem.items():
		ten_uu_dai.append("tặng %s x%g" % (_ten_mon(ma), n))
	for ma, n in giam_dem.items():
		ten_uu_dai.append("giảm %s x%g" % (_ten_mon(ma), n))
	for ma, n in thieu_dem.items():
		# Mon tang ma khach chua goi: bao may khach them dong do vao gio voi
		# GIA GOC, khong phai gia 0. Vong tinh sau se giam 100% dong do. Lam
		# vay de bill in ra thay "Su kem 25.000" va mot dong "Khuyen mai
		# -25.000", va de bao cao biet nhan vien da tang di bao nhieu TIEN.
		# Neu them dong gia 0 thi moi mon tang deu ghi nhan 0d, ai tang bao
		# nhieu cung khong soi ra duoc.
		them.append({"item_code": ma, "qty": n, "rate": _gia_ban(ma), "tang": 1})
		ten_uu_dai.append("được tặng %s x%g (chưa có trong đơn)" % (_ten_mon(ma), n))

	if not giam and not them:
		return {"giam": 0, "dien_giai": "hoá đơn chưa có món ưu đãi của chương trình", "them_mon": []}
	return {"giam": giam, "dien_giai": ", ".join(ten_uu_dai) or "đủ điều kiện", "them_mon": them}


def _ten_mon(ma):
	return frappe.db.get_value("Item", ma, "item_name") or ma


def _gia_ban(ma):
	return flt(
		frappe.db.get_value(
			"Item Price",
			{"item_code": ma, "selling": 1},
			"price_list_rate",
			order_by="valid_from desc, modified desc",
		)
	)


def _tien_chu(n):
	return "{:,.0f}đ".format(flt(n)).replace(",", ".")


# ------------------------------------------------------------------- combo

def nhom_combo(cb):
	"""Bang ten nhom -> {toi_thieu, toi_da, mo_ta, dong}."""
	from vagabond.vagabond.doctype.vagabond_combo.vagabond_combo import nhom_cua

	return nhom_cua(cb)


def _doc_combo(ma):
	d = frappe.get_doc("Vagabond Combo", ma)
	o = d.as_dict()
	o["name"] = d.name
	o["dong"] = [x.as_dict() for x in (d.dong or [])]
	o["nhom"] = [x.as_dict() for x in (d.get("nhom") or [])]
	return o


def _dong_bat_buoc(cb):
	"""Cac mon luon vao bill: dong khong ghi ten nhom."""
	return [d for d in cb["dong"] if not str(d.get("nhom") or "").strip()]


def _chon_dong(cb, chon):
	"""Doi lua chon cua khach thanh cac DONG trong combo. Tra (dong, loi).

	chon la danh sach {nhom, item_code}. Phai gui ca ten nhom chu khong chi
	ma mon: mot mon duoc phep nam trong hai nhom khac nhau, chi gui ma mon
	thi may khong biet no dang dai dien cho nhom nao.

	May chu kiem lai het thay vi tin con so app gui len: chon thieu, chon
	thua hay chon mon khong thuoc nhom deu la sai so tien cua bill.
	"""
	nh = nhom_combo(cb)
	if not nh:
		return [], ""
	if isinstance(chon, str):
		chon = json.loads(chon or "[]")
	theo_nhom = {}
	for x in chon or []:
		if not isinstance(x, dict):
			continue
		n = str(x.get("nhom") or "").strip()
		m = str(x.get("item_code") or "").strip()
		if n and m:
			theo_nhom.setdefault(n, []).append(m)
	ra = []
	for ten in sorted(nh.keys()):
		g = nh[ten]
		da_chon = theo_nhom.get(ten) or []
		if len(da_chon) < g["toi_thieu"]:
			return [], "nhóm \"%s\" phải chọn ít nhất %d món, đang chọn %d" % (
				ten, g["toi_thieu"], len(da_chon)
			)
		if len(da_chon) > g["toi_da"]:
			return [], "nhóm \"%s\" chỉ được chọn tối đa %d món, đang chọn %d" % (
				ten, g["toi_da"], len(da_chon)
			)
		bang = {}
		for d in g["dong"]:
			bang.setdefault(d.get("item_code"), d)
		da_lay = set()
		for m in da_chon:
			if m not in bang:
				return [], "món %s không thuộc nhóm \"%s\"" % (_ten_mon(m), ten)
			if m in da_lay:
				return [], "nhóm \"%s\" đang chọn trùng món %s" % (ten, _ten_mon(m))
			da_lay.add(m)
			ra.append(bang[m])
	# Nhom khai trong bang ma app khong gui gi len: neu nhom do bat buoc thi
	# vong tren da chan; con nhom khong bat buoc thi bo qua la dung.
	for ten in theo_nhom:
		if ten not in nh:
			return [], "combo không có nhóm \"%s\"" % ten
	return ra, ""


def _tien_dong(d):
	return flt(d.get("thanh_tien")) or flt(d.get("gia_goc")) * flt(d.get("so_luong"))


def _tiet_kiem_bo(cb, goc):
	"""Tien giam cua MOT bo, tinh tren gia goc THUC TE khach da chon.

	Khong dung lai truong tiet_kiem cat san: combo co nhom chon thi moi
	phuong an chon mot gia goc khac nhau, dung con so cat san la khach chon
	mon dat lai duoc giam it hon phan phai giam.
	"""
	kieu = cb.get("kieu") or "Gia tron goi"
	if kieu == "Gia tron goi":
		giam = goc - flt(cb.get("gia_combo"))
	elif kieu == "Giam phan tram":
		giam = goc * flt(cb.get("gia_tri")) / 100.0
	else:
		giam = flt(cb.get("gia_tri"))
	return max(0.0, min(giam, goc))


def _giam_combo(cb, gio, so_bo, chon=None, con_lai=None):
	"""Kiem gio hang co du mon thanh phan cho so_bo bo combo khong.

	Day la cho chan gian lan cua combo: may khach da RA combo thanh mon roi,
	nhung khong the tin no ra dung. May chu dem lai tung mon.

	con_lai la so luong CON CHUA BI BO COMBO NAO CHIEM, truyen vao va bi tru
	di. Combo co nhom chon thi mot bill co the mang hai dong cung mot combo
	voi hai lua chon khac nhau; neu moi dong deu do lai gio hang tu dau thi
	mot ly ca phe duy nhat nuoi duoc ca hai bo (De feedback 12/08/2026).
	"""
	so_bo = max(1, cint(so_bo))
	co = con_lai
	if co is None:
		co = {}
		for d in gio:
			co[d["item_code"]] = co.get(d["item_code"], 0) + d["qty"]
	dong_chon, loi = _chon_dong(cb, chon)
	if loi:
		return 0, loi
	dong = _dong_bat_buoc(cb) + dong_chon
	for d in dong:
		can = flt(d.get("so_luong")) * so_bo
		if co.get(d.get("item_code"), 0) < can - 0.0001:
			return 0, "hoá đơn thiếu %s (cần %g)" % (_ten_mon(d.get("item_code")), can)
	for d in dong:
		ma = d.get("item_code")
		co[ma] = co.get(ma, 0) - flt(d.get("so_luong")) * so_bo
	goc = sum(_tien_dong(d) for d in dong)
	return _tiet_kiem_bo(cb, goc) * so_bo, ""


# ------------------------------------------------------------------- API doc

# Ba diem ban. Don Sales online khong mang ma quay nen quy uoc la SALES.
def _quay_ds():
	"""Quay/diem ban doc tu Cai dat, xem vagabond/diem_ban.py."""
	return [{"ma": d["ma"], "ten": d["ten_ngan"]} for d in diem_ban.ds(chi_bat=True)]


@frappe.whitelist()
def danh_muc():
	"""Danh muc de man cau hinh khuyen mai bay ra thanh CHIP cho bam.

	Anh Viet 12/08/2026: "Lam thanh chip de chon het dum anh, hien khong
	chon duoc tu o nay" - truoc day hang khach va nhom khach la o go tay,
	go sai mot chu la chuong trinh khong bao gio ap duoc ma khong ai biet.
	"""
	_kiem_quyen()
	hang = frappe.get_all(
		"Vagabond Hang Khach", fields=["name"], order_by="idx asc, name asc", limit_page_length=0
	)
	nhom = frappe.get_all(
		"Customer Group", filters={"is_group": 0}, fields=["name"], order_by="name asc", limit_page_length=0
	)
	nhom_mon = frappe.get_all(
		"Item Group", filters={"is_group": 0}, fields=["name"], order_by="name asc", limit_page_length=0
	)
	return {
		"hang": [r.name for r in hang],
		"nhom_khach": [r.name for r in nhom],
		"nhom_mon": [r.name for r in nhom_mon],
		"quay": _quay_ds(),
	}


@frappe.whitelist()
def ds_ctkm(quay=None, nguon=None, khach=None, sdt=None, ngay=None, tat_ca=0):
	"""Chuong trinh dang bat, kem co du dieu kien luc nay khong.

	Van tra ve ca chuong trinh khong du dieu kien, kem ly do - de cashier
	biet "chuong trinh nay co that nhung hom nay khong ap duoc" thay vi
	tuong he thong hong.
	"""
	_kiem_quyen()
	loc = {} if cint(tat_ca) else {"bat": 1}
	ds = frappe.get_all(
		"Vagabond CTKM",
		filters=loc,
		fields=[
			"name", "ten", "cach_thuc", "kieu_giam", "gia_tri", "gia_dong",
			"bat", "uu_tien", "cach_ma", "ma_co_dinh", "can_otp", "cong_don",
			"hd_toi_thieu", "sl_toi_thieu", "giam_toi_da", "pham_vi",
			"tu_ngay", "den_ngay", "gio_tu", "gio_den", "kenh", "quay",
			"doi_tuong", "hang_khach", "nhom_khach", "nhom_mon", "da_dung",
			"lan_moi_ngay", "lan_moi_ca", "lan_moi_khach", "so_lan_toi_da",
			"hien_web", "web_anh", "web_mo_ta",
		] + THU_TRONG_TUAN,
		order_by="uu_tien asc, ten asc",
		limit_page_length=0,
	)
	# Man CAU HINH goi ham nay khong kem don hang nao (tat_ca=1, khong co
	# nguon lan quay). Luc do khong duoc phep phan xet "dung duoc hay khong"
	# theo kenh: khong co don thi kenh nao cung khong khop, va man hinh bao
	# "khong ap dung cho nguon don (trong)" trong khi nguoi ta khai dung -
	# De bao ngay 12/08/2026. Chi kiem THOI GIAN, la thu doc duoc mot minh.
	co_don = bool((nguon or "").strip() or (quay or "").strip())
	ra = []
	for km in ds:
		o = dict(km)
		o["nhan_cach"] = NHAN_CACH_THUC.get(km.cach_thuc, km.cach_thuc)
		# Tach san danh sach de man cau hinh bay ra thanh chip, thay vi bat
		# nguoi doc tu doan tu mot o van ban nhieu dong.
		o["kenh_ds"] = _dong(km.get("kenh"))
		o["quay_ds"] = [q.upper() for q in _dong(km.get("quay"))]
		ok, ly_do = _hop_thoi_gian(km)
		if ok and co_don:
			ok, ly_do = _hop_kenh(km, nguon, quay)
		if ok and (co_don or khach or sdt):
			ok, ly_do = _hop_doi_tuong(km, khach, sdt)
		if ok:
			ok, ly_do = _hop_han_muc(km, sdt=sdt, ngay=ngay)
		o["dung_duoc"] = 1 if ok else 0
		o["ly_do"] = ly_do
		# v589: man cau hinh noi luon chuong trinh co dung duoc tren web khong.
		o["ly_do_web"] = ly_do_khong_web(km)
		ra.append(o)
	return {"km": ra}


@frappe.whitelist()
def ds_combo(quay=None, nguon=None, tat_ca=0):
	_kiem_quyen()
	loc = {} if cint(tat_ca) else {"bat": 1}
	ds = frappe.get_all(
		"Vagabond Combo",
		filters=loc,
		fields=[
			"name", "ma_hang", "ten", "kieu", "gia_combo", "gia_tri", "gia_goc", "tiet_kiem",
			"bat", "uu_tien", "tu_ngay", "den_ngay", "kenh", "quay", "anh",
			"mo_ta", "can_otp", "gioi_han_bill", "lan_moi_ngay", "da_dung",
		],
		order_by="uu_tien asc, ten asc",
		limit_page_length=0,
	)
	co_don = bool((nguon or "").strip() or (quay or "").strip())
	ra = []
	for cb in ds:
		o = dict(cb)
		o["kenh_ds"] = _dong(cb.get("kenh"))
		o["quay_ds"] = [q.upper() for q in _dong(cb.get("quay"))]
		ok, ly_do = _hop_thoi_gian(cb)
		if ok and co_don:
			ok, ly_do = _hop_kenh(cb, nguon, quay)
		o["dung_duoc"] = 1 if ok else 0
		o["ly_do"] = ly_do
		o["dong"] = frappe.get_all(
			"Vagabond Combo Dong",
			filters={"parent": cb.name},
			fields=["item_code", "ten_mon", "so_luong", "gia_goc", "thanh_tien", "nhom", "chon_trong_nhom"],
			order_by="idx asc",
			limit_page_length=0,
		)
		# Bang nhom phai keo theo, khong thi nhom_cua roi ve duong suy nguoc
		# tu tung dong va mat con so "chon toi thieu".
		o["nhom"] = frappe.get_all(
			"Vagabond Combo Nhom",
			filters={"parent": cb.name},
			fields=["ten", "chon_toi_thieu", "chon_toi_da", "mo_ta"],
			order_by="idx asc",
			limit_page_length=0,
		)
		# Nhom mon cho khach chon. App dung cai nay de bay hop chon mon truoc
		# khi do combo vao bill - khong co thi thu ngan bam combo la ca bon
		# mon banh nhay het vao hoa don (De feedback 12/08/2026).
		nh = nhom_combo(o)
		o["nhom_ds"] = [
			{
				"ten": ten,
				"toi_thieu": nh[ten]["toi_thieu"],
				"toi_da": nh[ten]["toi_da"],
				# Giu ten cu "chon" cho ban app doi, khong thi thu ngan dang
				# ban giua chung ma man chon mon trong tron.
				"chon": nh[ten]["toi_da"],
				"mo_ta": nh[ten]["mo_ta"],
				"mon": [
					{
						"item_code": d.get("item_code"),
						"ten_mon": d.get("ten_mon") or _ten_mon(d.get("item_code")),
						"so_luong": flt(d.get("so_luong")),
						"gia_goc": flt(d.get("gia_goc")),
					}
					for d in nh[ten]["dong"]
				],
			}
			for ten in sorted(nh.keys())
		]
		o["co_nhom"] = 1 if nh else 0
		o["bat_buoc"] = [
			{
				"item_code": d.get("item_code"),
				"ten_mon": d.get("ten_mon") or _ten_mon(d.get("item_code")),
				"so_luong": flt(d.get("so_luong")),
				"gia_goc": flt(d.get("gia_goc")),
			}
			for d in _dong_bat_buoc(o)
		]
		# So bo da ban HOM NAY: anh Viet 11/08/2026 muon dem duoc combo ban
		# trong ngay ngay tren man chon mon, khong phai mo bao cao.
		try:
			o["so_hom_nay"] = frappe.db.count(
				"Vagabond CTKM Su Dung",
				{"combo": cb.name, "ngay": nowdate(), "loai": "Combo"},
			)
		except Exception:
			o["so_hom_nay"] = 0
		ra.append(o)
	return {"combo": ra}


@frappe.whitelist()
def ra_combo(ma_combo, so_bo=1, chon=None):
	"""Cashier bam mot combo -> tra ve danh sach mon de may khach do vao gio.

	KHONG tra ve dong nao ten "combo": bill, tem dan mon va bep chi duoc
	thay ten mon that (anh Viet 11/08/2026).

	chon la lua chon cua khach o cac nhom, dang [{nhom, item_code}]. Combo
	khong co nhom nao thi bo trong.
	"""
	_kiem_quyen()
	cb = _doc_combo(ma_combo)
	if not cint(cb.get("bat")):
		frappe.throw("Combo %s đang tắt." % cb.get("ten"))
	ok, ly_do = _hop_thoi_gian(cb)
	if not ok:
		frappe.throw("Combo %s: %s." % (cb.get("ten"), ly_do))
	so_bo = max(1, cint(so_bo))
	dong_chon, loi = _chon_dong(cb, chon)
	if loi:
		frappe.throw("Combo %s: %s." % (cb.get("ten"), loi))
	dong = _dong_bat_buoc(cb) + dong_chon
	mon = []
	for d in dong:
		mon.append(
			{
				"item_code": d.get("item_code"),
				"ten": d.get("ten_mon") or _ten_mon(d.get("item_code")),
				"qty": flt(d.get("so_luong")) * so_bo,
				"rate": flt(d.get("gia_goc")),
			}
		)
	goc = sum(_tien_dong(d) for d in dong)
	tiet_kiem = _tiet_kiem_bo(cb, goc)
	return {
		"ma": cb["name"],
		"ten": cb.get("ten"),
		"mon": mon,
		"gia_goc": goc * so_bo,
		"tiet_kiem": tiet_kiem * so_bo,
		"gia_combo": (goc - tiet_kiem) * so_bo,
		"so_bo": so_bo,
		"chon": [
			{"nhom": str(d.get("nhom") or "").strip(), "item_code": d.get("item_code")}
			for d in dong_chon
		],
	}


@frappe.whitelist()
def tra_ma(ma, quay=None, nguon=None):
	"""Cashier go mot ma vao o voucher. Ma co the la ma co dinh cua chuong
	trinh, hoac ma dung mot lan xuat theo lo."""
	_kiem_quyen()
	return _tra_ma(ma, quay=quay, nguon=nguon)


def _tra_ma(ma, quay=None, nguon=None):
	"""Than cua tra_ma, khong soi quyen nhan vien: trang dat banh (khach vang
	lai) cung tra ma qua day, qua cua ap_web ben duoi (v589)."""
	ma = str(ma or "").strip().upper()
	if not ma:
		frappe.throw("Chưa nhập mã.")
	# 1. Ma co dinh cua chuong trinh
	ten = frappe.db.get_value("Vagabond CTKM", {"ma_co_dinh": ma, "bat": 1}, ["name", "ten"])
	if ten:
		km = _doc_ctkm(ten[0])
		ok, ly_do = _hop_thoi_gian(km)
		if ok:
			ok, ly_do = _hop_kenh(km, nguon, quay)
		return {
			"loai": "co_dinh",
			"ctkm": km["name"],
			"ten": km.get("ten"),
			"dung_duoc": 1 if ok else 0,
			"ly_do": ly_do,
		}
	# 2. Ma dung mot lan
	if not frappe.db.exists("Vagabond Voucher", ma):
		frappe.throw("Không có mã %s trong hệ thống. Vui lòng kiểm tra lại." % ma)
	v = frappe.db.get_value(
		"Vagabond Voucher",
		ma,
		["ctkm", "trang_thai", "han_dung", "hoa_don", "ngay_dung", "gui_cho"],
		as_dict=True,
	)
	if v.trang_thai == "Da dung":
		frappe.throw(
			"Mã %s đã dùng rồi (hoá đơn %s, lúc %s)."
			% (ma, v.hoa_don or "?", v.ngay_dung or "?")
		)
	if v.trang_thai == "Da huy":
		frappe.throw("Mã %s đã bị huỷ." % ma)
	if v.han_dung and getdate(v.han_dung) < getdate(nowdate()):
		frappe.throw("Mã %s hết hạn ngày %s." % (ma, v.han_dung))
	km = _doc_ctkm(v.ctkm)
	if not cint(km.get("bat")):
		frappe.throw("Chương trình của mã %s đang tắt." % ma)
	ok, ly_do = _hop_thoi_gian(km)
	if ok:
		ok, ly_do = _hop_kenh(km, nguon, quay)
	return {
		"loai": "mot_lan",
		"ma": ma,
		"ctkm": km["name"],
		"ten": km.get("ten"),
		"gui_cho": v.gui_cho,
		"han_dung": v.han_dung,
		"dung_duoc": 1 if ok else 0,
		"ly_do": ly_do,
	}


# ---------------------------------------------------------------- tinh giam

def tinh(items, ctkm=None, ma=None, combo=None, quay=None, nguon=None,
         khach=None, sdt=None, ngay=None, bo_qua_han_muc=0):
	"""Tinh toan bo phan giam cua mot gio hang. Dung chung cho ca man tinh
	tien (xem truoc) va luc luu hoa don (chot that) - mot cong thuc duy nhat
	nen so tren man hinh va so tren bill khong bao gio lech nhau."""
	gio = _gio_hang(items)
	tong_hd = sum(d["tien"] for d in gio)
	if isinstance(ctkm, str):
		ctkm = json.loads(ctkm or "[]")
	if isinstance(combo, str):
		combo = json.loads(combo or "[]")
	ctkm = [c for c in (ctkm or []) if c]
	combo = combo or []
	ma = str(ma or "").strip().upper()

	ap, bo, them_mon = [], [], []
	can_otp = 0
	tong_giam = 0.0

	# --- combo truoc: no dong vao gia goc cua mon, cac chuong trinh khac
	# tinh sau tren phan con lai ---
	# So luong con chua bi bo combo nao chiem. Mot bill co the mang nhieu
	# dong cua CUNG mot combo voi lua chon khac nhau, nen phai tru dan.
	con_lai = {}
	for d in gio:
		con_lai[d["item_code"]] = con_lai.get(d["item_code"], 0) + d["qty"]
	# Gioi han "toi da moi hoa don" phai dem TONG so bo cua ca bill, khong
	# dem tung dong: tach 3 bo thanh ba dong 1 bo la lach duoc gioi han.
	tong_bo = {}
	for c in combo:
		if isinstance(c, str):
			c = {"ma": c, "so_bo": 1}
		mc0 = str(c.get("ma") or "").strip()
		if mc0:
			tong_bo[mc0] = tong_bo.get(mc0, 0) + max(1, cint(c.get("so_bo") or 1))
	for c in combo:
		if isinstance(c, str):
			c = {"ma": c, "so_bo": 1}
		mc = str(c.get("ma") or "").strip()
		if not mc:
			continue
		cb = _doc_combo(mc)
		if not cint(cb.get("bat")):
			bo.append({"ten": cb.get("ten"), "ly_do": "combo đang tắt"})
			continue
		ok, ly_do = _hop_thoi_gian(cb)
		if ok:
			ok, ly_do = _hop_kenh(cb, nguon, quay)
		if not ok:
			bo.append({"ten": cb.get("ten"), "ly_do": ly_do})
			continue
		so_bo = max(1, cint(c.get("so_bo") or 1))
		if cint(cb.get("gioi_han_bill")) and tong_bo.get(mc, so_bo) > cint(cb["gioi_han_bill"]):
			bo.append({
				"ten": cb.get("ten"),
				"ly_do": "một hoá đơn chỉ được tối đa %d combo" % cint(cb["gioi_han_bill"]),
			})
			continue
		giam, loi = _giam_combo(cb, gio, so_bo, c.get("chon"), con_lai)
		if not giam:
			bo.append({"ten": cb.get("ten"), "ly_do": loi or "không đủ điều kiện"})
			continue
		tong_giam += giam
		can_otp = can_otp or cint(cb.get("can_otp"))
		ap.append({
			"loai": "combo",
			"ma": cb["name"],
			"ten": cb.get("ten"),
			"so_bo": so_bo,
			"giam": _vnd(giam),
			"dien_giai": "%d bộ" % so_bo,
			"can_otp": cint(cb.get("can_otp")),
		})

	# --- ma voucher: keo theo chuong trinh cua no ---
	ma_ctkm_tu_voucher = ""
	if ma:
		tt = _tra_ma(ma, quay=quay, nguon=nguon)
		if not tt.get("dung_duoc"):
			frappe.throw("Mã %s: %s." % (ma, tt.get("ly_do") or "không dùng được lúc này"))
		ma_ctkm_tu_voucher = tt["ctkm"]
		if ma_ctkm_tu_voucher not in ctkm:
			ctkm.append(ma_ctkm_tu_voucher)

	# --- cac chuong trinh: chay theo uu tien ---
	ds_km = []
	for c in ctkm:
		if not frappe.db.exists("Vagabond CTKM", c):
			bo.append({"ten": c, "ly_do": "không có chương trình này"})
			continue
		ds_km.append(_doc_ctkm(c))
	ds_km.sort(key=lambda k: (cint(k.get("uu_tien")), k.get("ten") or ""))

	# Chuong trinh khong cho cong don thi phai dung mot minh.
	khong_cong_don = [k for k in ds_km if not cint(k.get("cong_don"))]
	if khong_cong_don and len(ds_km) > 1:
		frappe.throw(
			'Chương trình "%s" không cộng dồn được với chương trình khác. Vui lòng bỏ bớt rồi bấm lại.' % khong_cong_don[0].get("ten")
		)

	for km in ds_km:
		if not cint(km.get("bat")):
			bo.append({"ten": km.get("ten"), "ly_do": "chương trình đang tắt"})
			continue
		ok, ly_do = _hop_thoi_gian(km)
		if ok:
			ok, ly_do = _hop_kenh(km, nguon, quay)
		if ok:
			ok, ly_do = _hop_doi_tuong(km, khach, sdt)
		if ok and not cint(bo_qua_han_muc):
			ok, ly_do = _hop_han_muc(km, sdt=sdt, ngay=ngay)
		if not ok:
			bo.append({"ten": km.get("ten"), "ly_do": ly_do})
			continue
		kq = _tinh_mot(km, gio, tong_hd)
		giam = flt(kq.get("giam"))
		if flt(km.get("giam_toi_da")) and giam > flt(km["giam_toi_da"]):
			giam = flt(km["giam_toi_da"])
			kq["dien_giai"] = (kq.get("dien_giai") or "") + " (chạm trần %s)" % _tien_chu(km["giam_toi_da"])
		if giam <= 0 and not kq.get("them_mon"):
			bo.append({"ten": km.get("ten"), "ly_do": kq.get("dien_giai") or "không đủ điều kiện"})
			continue
		tong_giam += giam
		can_otp = can_otp or cint(km.get("can_otp"))
		them_mon.extend(kq.get("them_mon") or [])
		ap.append({
			"loai": "ctkm",
			"ma": km["name"],
			"ten": km.get("ten"),
			"cach_thuc": km.get("cach_thuc"),
			"nhan_cach": NHAN_CACH_THUC.get(km.get("cach_thuc"), km.get("cach_thuc")),
			"giam": _vnd(giam),
			"dien_giai": kq.get("dien_giai") or "",
			"can_otp": cint(km.get("can_otp")),
			"voucher": ma if km["name"] == ma_ctkm_tu_voucher else "",
		})

	# Khong bao gio de bill am. Neu cong don vuot tong thi cat ve tong.
	if tong_giam > tong_hd:
		tong_giam = tong_hd
	return {
		"tong_hd": _vnd(tong_hd),
		"tong_giam": _vnd(tong_giam),
		"con_lai": _vnd(tong_hd - tong_giam),
		"ap": ap,
		"bo": bo,
		"them_mon": them_mon,
		"can_otp": cint(can_otp),
		"voucher": ma,
	}


@frappe.whitelist()
def xem_truoc(items, ctkm=None, ma=None, combo=None, quay=None, nguon=None,
              khach=None, sdt=None, ngay=None):
	"""Ban cho may khach goi de hien so giam truoc khi chot."""
	_kiem_quyen()
	return tinh(
		items, ctkm=ctkm, ma=ma, combo=combo, quay=quay, nguon=nguon,
		khach=khach, sdt=sdt, ngay=ngay,
	)


# --------------------------------------------------------------- ghi vet dung

def ghi_su_dung(kq, si_name=None, quay=None, nguon=None, khach=None, sdt=None,
                ngay=None, cach_duyet="", ghi_chu=""):
	"""Ghi vet moi chuong trinh da ap len mot hoa don, va tieu ma voucher.

	Goi tu ban_hang.tao_don_tay SAU khi hoa don da luu thanh cong. Neu ghi vet
	loi thi chi log, khong lam hong hoa don - tien da thu cua khach roi.
	"""
	ngay = str(getdate(ngay or nowdate()))
	so = re.sub(r"\D", "", str(sdt or ""))
	for a in (kq or {}).get("ap") or []:
		try:
			frappe.get_doc({
				"doctype": "Vagabond CTKM Su Dung",
				"ngay": ngay,
				"luc": now_datetime(),
				"loai": "Combo" if a.get("loai") == "combo" else "CTKM",
				"ctkm": a.get("ma") if a.get("loai") != "combo" else None,
				"combo": a.get("ma") if a.get("loai") == "combo" else None,
				"ten_ctkm": a.get("ten"),
				"voucher": a.get("voucher") or "",
				"hoa_don": si_name,
				"tien_giam": flt(a.get("giam")),
				"thu_ngan": frappe.session.user,
				"quay": (quay or "").strip(),
				"kenh": (nguon or "").strip(),
				"khach": (khach or "").strip(),
				"sdt": so,
				"cach_duyet": cach_duyet or "",
				"ghi_chu": ghi_chu or "",
			}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="Vagabond: ghi vet khuyen mai", message=frappe.get_traceback())
		try:
			dt = "Vagabond Combo" if a.get("loai") == "combo" else "Vagabond CTKM"
			frappe.db.set_value(
				dt, a.get("ma"), "da_dung",
				cint(frappe.db.get_value(dt, a.get("ma"), "da_dung")) + 1,
				update_modified=False,
			)
		except Exception:
			pass

	ma = str((kq or {}).get("voucher") or "").strip().upper()
	if ma and frappe.db.exists("Vagabond Voucher", ma):
		try:
			tien = sum(
				flt(a.get("giam")) for a in (kq.get("ap") or []) if a.get("voucher") == ma
			)
			v = frappe.get_doc("Vagabond Voucher", ma)
			v.trang_thai = "Da dung"
			v.ngay_dung = now_datetime()
			v.hoa_don = si_name
			v.tien_giam = tien
			v.thu_ngan = frappe.session.user
			v.quay = (quay or "").strip()
			v.khach = (khach or "").strip()
			v.sdt = so
			if ghi_chu:
				v.ghi_chu = ghi_chu
			v.flags.ignore_permissions = True
			v.save()
			if v.lo:
				_dem_lai_lo(v.lo)
		except Exception:
			frappe.log_error(title="Vagabond: tieu ma voucher", message=frappe.get_traceback())
	frappe.db.commit()


def _dem_lai_lo(lo):
	try:
		tong = frappe.db.count("Vagabond Voucher", {"lo": lo})
		dung = frappe.db.count("Vagabond Voucher", {"lo": lo, "trang_thai": "Da dung"})
		frappe.db.set_value(
			"Vagabond Lo Voucher", lo,
			{"da_dung": dung, "con_lai": tong - dung},
			update_modified=False,
		)
	except Exception:
		pass


# --------------------------------------------------------------- sinh ma lo

def _sinh_ma_moi(so_luong):
	"""Sinh du so_luong ma 6 ky tu KHAC NHAU va chua ton tai trong DB.

	Doc truoc mot lan cac ma da co roi loc trong bo nho: neu hoi DB tung ma
	mot thi xuat 2000 ma la 2000 luot truy van, xuat mot lo mat ca phut.
	"""
	so_luong = cint(so_luong)
	da_co = set(
		r[0] for r in frappe.db.sql("select name from `tabVagabond Voucher`")
	)
	ra = []
	vong = 0
	while len(ra) < so_luong:
		vong += 1
		if vong > so_luong * 50 + 1000:
			frappe.throw("Không sinh đủ mã, vui lòng thử lại với số lượng nhỏ hơn.")
		ma = "".join(
			CHU_MA[int(c, 16) % len(CHU_MA)] for c in frappe.generate_hash(length=DAI_MA)
		)
		if ma in da_co:
			continue
		da_co.add(ma)
		ra.append(ma)
	return ra


@frappe.whitelist()
def xuat_lo(ctkm, so_luong, email, gui_cho=None, han_dung=None, ghi_chu=None, gui_mail=1):
	"""Xuat mot lo ma voucher dung mot lan roi gui file CSV ve email.

	Anh Viet 11/08/2026: nguoi thao tac tu dien email cua minh va so luong ma
	muon nhan; danh sach nay thuong de gui cho doi tac, brand collab.
	"""
	_kiem_quyen_sua()
	so_luong = cint(so_luong)
	if so_luong <= 0:
		frappe.throw("Số lượng mã phải lớn hơn 0.")
	if so_luong > 5000:
		frappe.throw("Một lô tối đa 5.000 mã. Cần nhiều hơn thì xuất thành nhiều lô.")
	email = str(email or "").strip()
	if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
		frappe.throw("Email nhận danh sách mã chưa đúng định dạng.")
	if not frappe.db.exists("Vagabond CTKM", ctkm):
		frappe.throw("Không có chương trình %s." % ctkm)
	km = frappe.db.get_value("Vagabond CTKM", ctkm, ["ten", "cach_ma", "han_ma"], as_dict=True)
	if km.cach_ma != "Ma dung mot lan":
		frappe.throw(
			'Chương trình "%s" đang để cách phát mã là "%s". Vui lòng đổi sang "Mã dùng một lần" rồi xuất lô.' % (km.ten, km.cach_ma)
		)
	han = han_dung or km.han_ma

	lo = frappe.get_doc({
		"doctype": "Vagabond Lo Voucher",
		"ctkm": ctkm,
		"so_luong": so_luong,
		"email_nhan": email,
		"gui_cho": (gui_cho or "").strip(),
		"han_dung": han,
		"ghi_chu": (ghi_chu or "").strip(),
		"nguoi_tao": frappe.session.user,
		"ngay_tao": now_datetime(),
		"trang_thai": "Cho gui",
		"con_lai": so_luong,
	})
	lo.flags.ignore_permissions = True
	lo.insert()

	ds_ma = _sinh_ma_moi(so_luong)
	for m in ds_ma:
		frappe.get_doc({
			"doctype": "Vagabond Voucher",
			"ma": m,
			"ctkm": ctkm,
			"lo": lo.name,
			"trang_thai": "Chua dung",
			"han_dung": han,
			"email_nhan": email,
			"gui_cho": (gui_cho or "").strip(),
		}).insert(ignore_permissions=True)
	frappe.db.commit()

	loi, tt = "", "Cho gui"
	if cint(gui_mail):
		loi = _gui_mail_lo(lo.name, km.ten, ds_ma, email, gui_cho, han)
		tt = "Loi gui" if loi else "Da gui"
	frappe.db.set_value(
		"Vagabond Lo Voucher", lo.name,
		{"trang_thai": tt, "loi_gui": loi},
		update_modified=False,
	)
	frappe.db.commit()
	return {
		"lo": lo.name,
		"so_luong": so_luong,
		"email": email,
		"da_gui": 0 if loi else 1,
		"loi": loi,
		"ma_dau": ds_ma[:10],
	}


def _csv_lo(ten_ctkm, ds_ma, han):
	buf = io.StringIO()
	w = csv.writer(buf)
	w.writerow(["Ma voucher", "Chuong trinh", "Han dung"])
	for m in ds_ma:
		w.writerow([m, ten_ctkm, str(han or "")])
	return buf.getvalue().encode("utf-8-sig")


def _gui_mail_lo(lo, ten_ctkm, ds_ma, email, gui_cho, han):
	"""Tra ve chuoi loi neu gui that bai, chuoi rong neu gui duoc."""
	try:
		from vagabond import thu_khung as _tk

		e = _tk.h
		than = (
			_tk.doan("Chào anh chị,")
			+ _tk.doan(
				"Đây là danh sách <b>%d mã ưu đãi</b> của chương trình <b>%s</b> tại %s."
				% (len(ds_ma), e(ten_ctkm or ""), _tk.TEN_TIEM)
			)
			+ _tk.o_kem(
				"Hạn dùng: <b>%s</b><br>Mã lô: <b>%s</b>%s"
				% (e(han or "không giới hạn"), e(lo),
				   ("<br>Gửi cho: " + e(gui_cho)) if gui_cho else ""),
				goc_anh=_tk.goc_anh(),
			)
			+ _tk.doan(
				"Mỗi mã chỉ dùng được <b>một lần</b>. Khách đọc mã cho thu ngân tại quầy, "
				"máy tự kiểm tra và trừ ưu đãi trên hoá đơn."
			)
			+ _tk.doan("Danh sách mã đầy đủ nằm trong tệp CSV đính kèm thư này.", cach=0)
		)
		noi_dung = _tk.khung("%d mã ưu đãi cho anh chị" % len(ds_ma), than, chan="khach", nhan="Ưu đãi")
		frappe.sendmail(
			recipients=[email],
			subject="[The Vagabond] %d mã ưu đãi - %s" % (len(ds_ma), ten_ctkm or ""),
			message=noi_dung,
			attachments=[{
				"fname": "ma-uu-dai-%s.csv" % lo,
				"fcontent": _csv_lo(ten_ctkm, ds_ma, han),
			}],
			now=True,
		)
		return ""
	except Exception as e:
		frappe.log_error(title="Vagabond: gui lo voucher", message=frappe.get_traceback())
		return str(e)[:400]


@frappe.whitelist()
def gui_lai_lo(lo):
	"""Lo bi loi mail thi gui lai, khong phai sinh ma moi."""
	_kiem_quyen_sua()
	d = frappe.get_doc("Vagabond Lo Voucher", lo)
	ds_ma = [
		r.name for r in frappe.get_all(
			"Vagabond Voucher", filters={"lo": lo}, fields=["name"],
			order_by="name asc", limit_page_length=0,
		)
	]
	if not ds_ma:
		frappe.throw("Lô %s không có mã nào." % lo)
	ten = frappe.db.get_value("Vagabond CTKM", d.ctkm, "ten")
	loi = _gui_mail_lo(lo, ten, ds_ma, d.email_nhan, d.gui_cho, d.han_dung)
	frappe.db.set_value(
		"Vagabond Lo Voucher", lo,
		{"trang_thai": "Loi gui" if loi else "Da gui", "loi_gui": loi},
		update_modified=False,
	)
	frappe.db.commit()
	return {"da_gui": 0 if loi else 1, "loi": loi, "so_luong": len(ds_ma)}


@frappe.whitelist()
def ds_lo(ctkm=None):
	_kiem_quyen()
	loc = {}
	if ctkm:
		loc["ctkm"] = ctkm
	ds = frappe.get_all(
		"Vagabond Lo Voucher",
		filters=loc,
		fields=[
			"name", "ctkm", "ten_ctkm", "so_luong", "email_nhan", "gui_cho",
			"han_dung", "trang_thai", "da_dung", "con_lai", "ngay_tao",
			"nguoi_tao", "loi_gui", "ghi_chu",
		],
		order_by="creation desc",
		limit_page_length=200,
	)
	for r in ds:
		_dem_lai_lo(r.name)
	return {"lo": ds}


@frappe.whitelist()
def ds_ma_cua_lo(lo, trang_thai=None, gioi_han=500):
	_kiem_quyen()
	loc = {"lo": lo}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	tong = frappe.db.count("Vagabond Voucher", loc)
	ds = frappe.get_all(
		"Vagabond Voucher",
		filters=loc,
		fields=["name", "trang_thai", "han_dung", "ngay_dung", "hoa_don", "tien_giam", "thu_ngan"],
		order_by="name asc",
		limit_page_length=cint(gioi_han) or 500,
	)
	return {"ma": ds, "tong_so": tong}


@frappe.whitelist()
def huy_ma(ma, ly_do=None):
	"""Huy mot ma (lo dan sai, doi tac tra lai...). Ma da dung thi khong huy."""
	_kiem_quyen_sua()
	ma = str(ma or "").strip().upper()
	v = frappe.get_doc("Vagabond Voucher", ma)
	if v.trang_thai == "Da dung":
		frappe.throw("Mã %s đã dùng cho hoá đơn %s, không huỷ được nữa." % (ma, v.hoa_don or "?"))
	v.trang_thai = "Da huy"
	v.ghi_chu = (v.ghi_chu or "") + "\nHuỷ bởi %s: %s" % (frappe.session.user, ly_do or "")
	v.flags.ignore_permissions = True
	v.save()
	if v.lo:
		_dem_lai_lo(v.lo)
	frappe.db.commit()
	return {"ok": 1}


# ------------------------------------------------------------------ bao cao

@frappe.whitelist()
def bao_cao(tu=None, den=None, quay=None):
	"""Tien da giam trong ky, xep hang thu ngan va chuong trinh.

	Bao cao nay la de SOI: mot thu ngan bong nhien giam gap nhieu lan nguoi
	khac la co chuyen (anh Viet 11/08/2026).
	"""
	_kiem_quyen()
	den = str(getdate(den or nowdate()))
	tu = str(getdate(tu or frappe.utils.add_days(den, -29)))
	loc = {"ngay": ["between", [tu, den]]}
	if quay:
		loc["quay"] = quay
	loc["da_tra"] = 0  # lượt đã trả của đơn web bị huỷ không tính (QT-20)
	ds = frappe.get_all(
		"Vagabond CTKM Su Dung",
		filters=loc,
		fields=["ngay", "loai", "ten_ctkm", "ctkm", "combo", "hoa_don",
		        "tien_giam", "thu_ngan", "quay", "voucher", "sdt"],
		order_by="ngay desc",
		limit_page_length=0,
	)
	theo_nguoi, theo_ct, theo_ngay = {}, {}, {}
	tong = 0.0
	for r in ds:
		t = flt(r.tien_giam)
		tong += t
		o = theo_nguoi.setdefault(r.thu_ngan or "?", {"nguoi": r.thu_ngan or "?", "so": 0, "tien": 0.0})
		o["so"] += 1
		o["tien"] += t
		k = r.ten_ctkm or r.ctkm or r.combo or "?"
		o2 = theo_ct.setdefault(k, {"ten": k, "loai": r.loai, "so": 0, "tien": 0.0})
		o2["so"] += 1
		o2["tien"] += t
		o3 = theo_ngay.setdefault(str(r.ngay), {"ngay": str(r.ngay), "so": 0, "tien": 0.0})
		o3["so"] += 1
		o3["tien"] += t
	return {
		"tu": tu,
		"den": den,
		"tong_giam": _vnd(tong),
		"so_luot": len(ds),
		"theo_nguoi": sorted(theo_nguoi.values(), key=lambda x: -x["tien"]),
		"theo_ct": sorted(theo_ct.values(), key=lambda x: -x["tien"]),
		"theo_ngay": sorted(theo_ngay.values(), key=lambda x: x["ngay"]),
		"dong": ds[:300],
	}


# --------------------------------------------------------- tao / sua tu app

TRUONG_CTKM = [
	"ten", "cach_thuc", "bat", "uu_tien", "cong_don", "kieu_giam", "gia_tri",
	"gia_dong", "giam_toi_da", "hd_toi_thieu", "sl_toi_thieu", "pham_vi",
	"nhom_mon", "tu_ngay", "den_ngay", "gio_tu", "gio_den", "kenh", "quay",
	"doi_tuong", "hang_khach", "nhom_khach", "cach_ma", "ma_co_dinh",
	"han_ma", "can_otp", "lan_moi_ngay", "lan_moi_ca", "lan_moi_khach",
	"so_lan_toi_da", "ghi_chu", "hien_web", "web_anh", "web_mo_ta",
] + THU_TRONG_TUAN


@frappe.whitelist()
def luu_ctkm(du_lieu, ma=None):
	"""Tao moi hoac sua mot chuong trinh tu man khuyen mai trong app."""
	_kiem_quyen_sua()
	if isinstance(du_lieu, str):
		du_lieu = json.loads(du_lieu or "{}")
	d = frappe.get_doc("Vagabond CTKM", ma) if ma else frappe.new_doc("Vagabond CTKM")
	for t in TRUONG_CTKM:
		if t in du_lieu:
			d.set(t, du_lieu.get(t))
	if "dong_mon" in du_lieu:
		d.dong_mon = []
		for r in du_lieu.get("dong_mon") or []:
			d.append("dong_mon", {
				"vai_tro": r.get("vai_tro") or "Uu dai",
				"item_code": r.get("item_code"),
				"so_luong": flt(r.get("so_luong") or 1),
				"kieu_giam": r.get("kieu_giam") or "",
				"gia_tri": flt(r.get("gia_tri") or 0),
			})
	if "dong_bac" in du_lieu:
		d.dong_bac = []
		for r in du_lieu.get("dong_bac") or []:
			d.append("dong_bac", {
				"tu_tien": flt(r.get("tu_tien")),
				"kieu_giam": r.get("kieu_giam") or "Phan tram",
				"gia_tri": flt(r.get("gia_tri")),
				"tran": flt(r.get("tran") or 0),
			})
	if "dong_khach" in du_lieu:
		d.dong_khach = []
		for r in du_lieu.get("dong_khach") or []:
			d.append("dong_khach", {
				"khach": r.get("khach"),
				"dien_thoai": r.get("dien_thoai") or "",
			})
	d.flags.ignore_permissions = True
	d.save()
	frappe.db.commit()
	return {"ma": d.name, "ten": d.ten}


@frappe.whitelist()
def xem_ctkm(ma):
	_kiem_quyen()
	km = _doc_ctkm(ma)
	km["nhan_cach"] = NHAN_CACH_THUC.get(km.get("cach_thuc"), km.get("cach_thuc"))
	km["dong_khach"] = frappe.get_all(
		"Vagabond CTKM Khach",
		filters={"parent": ma},
		fields=["khach", "ten_khach", "dien_thoai"],
		order_by="idx asc",
		limit_page_length=0,
	)
	for r in km.get("dong_mon") or []:
		if not r.get("ten_mon"):
			r["ten_mon"] = _ten_mon(r.get("item_code"))
	return {"km": km}


@frappe.whitelist()
def bat_tat_ctkm(ma, bat):
	_kiem_quyen_sua()
	d = frappe.get_doc("Vagabond CTKM", ma)
	d.bat = cint(bat)
	d.flags.ignore_permissions = True
	d.save()
	frappe.db.commit()
	return {"bat": cint(d.bat)}


TRUONG_COMBO = [
	"ten", "ma_hang", "bat", "uu_tien", "kieu", "gia_combo", "gia_tri", "tu_ngay",
	"den_ngay", "kenh", "quay", "gioi_han_bill", "lan_moi_ngay", "can_otp",
	"mo_ta", "anh",
]


@frappe.whitelist()
def luu_combo(du_lieu, ma=None):
	_kiem_quyen_sua()
	if isinstance(du_lieu, str):
		du_lieu = json.loads(du_lieu or "{}")
	d = frappe.get_doc("Vagabond Combo", ma) if ma else frappe.new_doc("Vagabond Combo")
	for t in TRUONG_COMBO:
		if t in du_lieu:
			d.set(t, du_lieu.get(t))
	if "nhom" in du_lieu:
		d.nhom = []
		for g in du_lieu.get("nhom") or []:
			d.append("nhom", {
				"ten": str(g.get("ten") or "").strip(),
				"chon_toi_thieu": cint(g.get("chon_toi_thieu") or 0),
				"chon_toi_da": cint(g.get("chon_toi_da") or 0),
				"mo_ta": str(g.get("mo_ta") or "").strip(),
			})
	if "dong" in du_lieu:
		d.dong = []
		for r in du_lieu.get("dong") or []:
			d.append("dong", {
				"item_code": r.get("item_code"),
				"so_luong": flt(r.get("so_luong") or 1),
				"gia_goc": flt(r.get("gia_goc") or 0),
				"nhom": str(r.get("nhom") or "").strip(),
				"chon_trong_nhom": cint(r.get("chon_trong_nhom") or 0),
			})
	d.flags.ignore_permissions = True
	d.save()
	frappe.db.commit()
	return {"ma": d.name, "ten": d.ten, "tiet_kiem": flt(d.tiet_kiem), "gia_goc": flt(d.gia_goc)}


@frappe.whitelist()
def bat_tat_combo(ma, bat):
	_kiem_quyen_sua()
	d = frappe.get_doc("Vagabond Combo", ma)
	d.bat = cint(bat)
	d.flags.ignore_permissions = True
	d.save()
	frappe.db.commit()
	return {"bat": cint(d.bat)}



# ------------------------------------------------------------------ website
#
# v589 (anh Viet 09/10/2026): ERP la NGUON DUY NHAT cua uu dai. Nhan vien tao
# chuong trinh tren app (Ban hang > Chuong trinh khuyen mai), tich "Hien tren
# website" la trang khach tu hien, tat chuong trinh la tu an. Trang dat banh
# dung CHUNG bo tinh `tinh` voi quay, khong co cong thuc thu hai.
#
# Web chi nhan nhung chuong trinh chac chan khong lach duoc khi khach tu khai:
# khong can OTP, doi tuong "Moi khach" (hang, nhom, nhan vien deu dua tren thu
# khach tu go nen khong kiem duoc tren web), va chi giam tien (tang mon thi
# phai co nguoi bo mon vao hop, de tai quay).

NGUON_WEB = "Website"
CACH_THUC_WEB = ("Giam tong hoa don", "Giam gia mon", "Mua A giam B", "Dong gia", "Giam luy ke")
TRUONG_WEB = [
	"name", "ten", "cach_thuc", "kieu_giam", "gia_tri", "gia_dong", "giam_toi_da",
	"bat", "cach_ma", "ma_co_dinh", "can_otp", "doi_tuong", "kenh", "quay",
	"hd_toi_thieu", "sl_toi_thieu", "tu_ngay", "den_ngay", "gio_tu", "gio_den",
	"hien_web", "web_mo_ta", "web_anh", "uu_tien", "cong_don",
] + THU_TRONG_TUAN
TEN_THU = {"thu_2": "T2", "thu_3": "T3", "thu_4": "T4", "thu_5": "T5", "thu_6": "T6", "thu_7": "T7", "thu_cn": "CN"}


def ly_do_khong_web(km):
	"""THUAN. Rong la chuong trinh dung duoc khi dat banh tren web; khac rong
	la cau noi vi sao chi dung tai quay (hien ca o man ERP lan tren web)."""
	if km.get("cach_thuc") not in CACH_THUC_WEB:
		return "Chương trình tặng món chỉ dùng tại cửa hàng."
	if cint(km.get("can_otp")):
		return "Chương trình cần mã OTP quản lý nên chỉ dùng tại cửa hàng."
	if (km.get("doi_tuong") or "Moi khach") != "Moi khach":
		return "Chương trình theo hạng hoặc nhóm khách chỉ dùng tại cửa hàng."
	kenh = _dong(km.get("kenh"))
	if kenh and NGUON_WEB not in kenh:
		return "Chương trình không mở cho kênh Website."
	quay = [q.upper() for q in _dong(km.get("quay"))]
	if quay and "SALES" not in quay:
		return "Chương trình chỉ áp dụng tại quầy."
	return ""


def _gio_phut(v):
	v = str(v or "")
	return v[:5] if v else ""


def mo_ta_muc_giam(km):
	"""THUAN. Mot cau ngan noi muc giam, dung cho the uu dai tren web."""
	ct = km.get("cach_thuc")
	if ct == "Dong gia":
		return "Đồng giá %s" % _tien_chu(km.get("gia_dong"))
	if ct == "Giam luy ke":
		return "Giảm luỹ kế theo giá trị đơn"
	if km.get("kieu_giam") == "So tien":
		cau = "Giảm %s" % _tien_chu(km.get("gia_tri"))
	else:
		cau = "Giảm %s%%" % (("%g" % flt(km.get("gia_tri"))).replace(".", ","))
	if flt(km.get("giam_toi_da")) > 0:
		cau += ", tối đa %s" % _tien_chu(km.get("giam_toi_da"))
	if ct == "Giam gia mon":
		cau += " cho món áp dụng"
	elif ct == "Mua A giam B":
		cau += " khi mua kèm món chỉ định"
	return cau


def the_web(km, hom_nay=None):
	"""THUAN. Mot chuong trinh ERP -> mot the uu dai dung dinh dang cua trang
	khach (chuyen-muc.js). None khi khong duoc hien: chua bat, chua tich hien
	web, hoac da qua ngay ket thuc."""
	if not cint(km.get("bat")) or not cint(km.get("hien_web")):
		return None
	hn = str(hom_nay or nowdate())
	den = str(km.get("den_ngay") or "")
	if den and den < hn:
		return None
	ma = ""
	dk = [mo_ta_muc_giam(km)]
	if km.get("cach_ma") == "Ma co dinh" and km.get("ma_co_dinh"):
		ma = str(km["ma_co_dinh"]).strip().upper()
	elif km.get("cach_ma") == "Ma dung mot lan":
		dk.append("Mã dùng một lần, tiệm gửi riêng cho từng khách.")
	if cint(km.get("sl_toi_thieu")) > 0:
		dk.append("Đơn từ %d món." % cint(km["sl_toi_thieu"]))
	thu = [TEN_THU[t] for t in THU_TRONG_TUAN if cint(km.get(t))]
	if thu:
		dk.append("Áp dụng " + ", ".join(thu) + ".")
	ly_do = ly_do_khong_web(km)
	if ly_do:
		dk.append(ly_do)
	elif ma:
		dk.append("Đặt bánh trên web: nhập mã ở bước thanh toán.")
	else:
		dk.append("Đặt bánh trên web: tự áp khi đơn đủ điều kiện.")
	return {
		"id": "erp-" + str(km.get("name")),
		"loai": "uu_dai",
		"vi_tri": "uu_dai",
		"hien": True,
		"nguon": "erp",
		"tieu_de": km.get("ten") or km.get("name"),
		"noi_dung": (km.get("web_mo_ta") or "").strip(),
		"anh": km.get("web_anh") or "",
		"mo_ta_anh": km.get("ten") or "",
		"nhom": "Mã giảm giá" if (ma or km.get("cach_ma") == "Ma dung mot lan") else "Ưu đãi",
		"ma_uu_dai": ma,
		"don_toi_thieu": int(flt(km.get("hd_toi_thieu"))) or "",
		"bat_dau": str(km.get("tu_ngay") or ""),
		"ket_thuc": den,
		"gio_bat_dau": _gio_phut(km.get("gio_tu")),
		"gio_ket_thuc": _gio_phut(km.get("gio_den")),
		"dieu_kien": "\n".join(dk),
		"dung_web": 0 if ly_do else 1,
	}


def _ds_web_tho(chi_bat=True):
	loc = {"hien_web": 1}
	if chi_bat:
		loc["bat"] = 1
	try:
		return frappe.get_all("Vagabond CTKM", filters=loc, fields=TRUONG_WEB,
			order_by="uu_tien asc, ten asc", limit_page_length=100)
	except Exception:
		# Site chua migrate (chua co o hien_web): trang khach van phai len.
		frappe.log_error(title="Vagabond: doc uu dai web", message=frappe.get_traceback())
		return []


def the_web_dang_hien(hom_nay=None):
	"""Cac the uu dai trang khach dang hien, theo thu tu uu tien."""
	ra = []
	for km in _ds_web_tho():
		t = the_web(km, hom_nay)
		if t:
			ra.append(t)
	return ra


def ds_web_bien_tap(hom_nay=None):
	"""Cho trinh bien tap web: moi chuong trinh tich hien web, ke ca dang tat
	hay het han, kem trang thai, de Marketing biet vi sao khach chua thay."""
	hn = str(hom_nay or nowdate())
	ra = []
	for km in _ds_web_tho(chi_bat=False):
		the = the_web(dict(km, bat=1, den_ngay=""), hn)
		the["ket_thuc"] = str(km.get("den_ngay") or "")
		thay = the_web(km, hn) is not None
		if not cint(km.get("bat")):
			tt = "Đang tắt trên ERP, khách không thấy"
		elif not thay:
			tt = "Đã hết hạn, khách không thấy"
		else:
			tt = "Khách đang thấy"
		ra.append(dict(the, ma_ctkm=km.get("name"), khach_thay=1 if thay else 0, trang_thai_erp=tt))
	return ra


def _tu_ap_web():
	"""Chuong trinh hien web, khong can ma, dung duoc tren web: tu ap."""
	return [km for km in _ds_web_tho()
		if (km.get("cach_ma") or "Khong can ma") == "Khong can ma" and not ly_do_khong_web(km)]


def bo_thu_web(tu_ap, bo_ra=None):
	"""THUAN. Cac bo chuong trinh tu ap can thu, theo thu tu: tat ca, roi bo
	cac chuong trinh cong don duoc voi nhau (Codex #460 vong 3: mot chuong
	trinh khong cong don lam ca bo "tat ca" bi tu choi, nhung bo cong don van
	hop le va co the loi hon tung cai le), roi tung cai mot."""
	ten = [k["name"] for k in tu_ap if k["name"] != bo_ra]
	cong = [k["name"] for k in tu_ap if k["name"] != bo_ra and cint(k.get("cong_don"))]
	ra = []
	for ds in [ten, cong] + [[t] for t in ten]:
		if ds and ds not in ra:
			ra.append(ds)
	return ra


def ap_web(gio_co_gia, ma=None, sdt=None, ngay=None):
	"""Tinh giam cho mot don web. gio_co_gia: [{item_code, qty, rate}] voi gia
	do MAY CHU doc (QT-19). Tra {tong_giam, ap, ma, ly_do}. Ma sai thi ly_do
	khac rong va tong_giam = 0, KHONG nem: trang khach can cau de hien.

	Thu tu: ma khach go truoc (khach chu dong chon), roi cac chuong trinh tu
	ap cong don duoc voi no. Khong co ma thi lay cach co loi nhat cho khach
	trong cac chuong trinh tu ap."""
	ma = str(ma or "").strip().upper()
	tu_ap = _tu_ap_web()
	rong = {"tong_giam": 0, "ap": [], "ma": ma, "ly_do": "", "kq": None}

	def _thu(ctkm, ma_go):
		try:
			kq = tinh(gio_co_gia, ctkm=list(ctkm), ma=ma_go or None, quay="", nguon=NGUON_WEB,
				sdt=sdt, ngay=ngay)
		except Exception as e:
			return None, str(getattr(e, "message", "") or e).strip() or "không dùng được lúc này"
		# Chot lan cuoi: moi chuong trinh da ap phai dung duoc tren web.
		for a in kq.get("ap") or []:
			if a.get("loai") != "ctkm":
				return None, "không dùng được khi đặt trên web"
			km = _doc_ctkm(a["ma"])
			lydo = ly_do_khong_web(km)
			if lydo:
				return None, lydo
		if kq.get("them_mon") or cint(kq.get("can_otp")):
			return None, "chỉ dùng tại cửa hàng"
		return kq, ""

	if ma:
		kq, loi = _thu([], ma)
		if not kq:
			return dict(rong, ly_do=loi)
		if not kq.get("ap"):
			ly = "; ".join(b.get("ly_do") or "" for b in kq.get("bo") or []) or "đơn chưa đủ điều kiện"
			return dict(rong, ly_do="Mã %s: %s." % (ma, ly.rstrip(".")))
		# Ma cong them chuong trinh tu ap: thu ca bo, bo cong don, tung cai.
		for ds in bo_thu_web(tu_ap, bo_ra=kq["ap"][0]["ma"]):
			k2, _ = _thu(ds, ma)
			if k2 and flt(k2["tong_giam"]) > flt(kq["tong_giam"]):
				kq = k2
	else:
		kq = None
		# Khong ma: lay bo co loi nhat cho khach (ca bo, bo cong don, tung cai).
		for ds in bo_thu_web(tu_ap):
			k1, _ = _thu(ds, None)
			if k1 and k1.get("ap") and (not kq or flt(k1["tong_giam"]) > flt(kq["tong_giam"])):
				kq = k1
		if not kq or not kq.get("ap"):
			return rong
	return {
		"tong_giam": _vnd(kq["tong_giam"]),
		"ap": [{"ma": a["ma"], "ten": a.get("ten"), "giam": a.get("giam"), "dien_giai": a.get("dien_giai") or ""}
			for a in kq.get("ap") or []],
		"ma": ma,
		"ly_do": "",
		"kq": kq,
	}


def ma_dung_mot_lan(ma):
	"""Ma nay co phai ma dung mot lan (bang Vagabond Voucher) khong."""
	ma = str(ma or "").strip().upper()
	return bool(ma) and bool(frappe.db.exists("Vagabond Voucher", ma))


def giu_ma_mot_lan(ma, ghi_chu):
	"""Khoa hang ma voucher dung mot lan va danh dau Da dung TRUOC khi goi
	Pancake: hai don web cung go mot ma cung luc thi don sau bi chan. Tra
	True neu giu duoc."""
	ma = str(ma or "").strip().upper()
	hang = frappe.db.sql("select trang_thai from `tabVagabond Voucher` where name=%s for update", (ma,))
	if not hang or hang[0][0] != "Chua dung":
		return False
	frappe.db.sql("update `tabVagabond Voucher` set trang_thai='Da dung', ngay_dung=%s, ghi_chu=%s where name=%s",
		(now_datetime(), ghi_chu, ma))
	return True


def tra_ma_mot_lan(ma, ghi_chu):
	"""Pancake tu choi don: tra ma ve Chua dung de khach gui lai duoc."""
	ma = str(ma or "").strip().upper()
	frappe.db.sql("update `tabVagabond Voucher` set trang_thai='Chua dung', ngay_dung=NULL, ghi_chu=%s "
		"where name=%s and trang_thai='Da dung' and hoa_don is null", (ghi_chu, ma))


def khoa_ctkm(ds_ma):
	"""Codex #460: khoá hàng các chương trình sắp áp cho một đơn web, giữ tới
	commit. Hai đơn cùng tranh lượt cuối thì đơn sau chờ ở đây."""
	ds = sorted({str(m) for m in (ds_ma or []) if m})
	if not ds:
		return
	frappe.db.sql("select name from `tabVagabond CTKM` where name in (%s) for update"
		% ", ".join(["%s"] * len(ds)), tuple(ds))


def tra_luot_web(ghi_chu):
	"""Pancake từ chối đơn web: đánh dấu đã trả các lượt đã giữ cho đơn đó (nhận theo ghi
	chú "Đơn web <mã>", kênh Website, chưa gắn hoá đơn) và trừ lại số đã dùng.
	Khoá dòng (FOR UPDATE) trước: lần trả ngay và việc định kỳ chạy chồng thì
	lần sau chờ, rồi thấy dòng đã trả, không trừ hai lần (Codex #460 vòng 3).
	Không xoá dòng (QT-20, Codex #460 vòng 4)."""
	hang = frappe.db.sql(
		"select name, ctkm, combo from `tabVagabond CTKM Su Dung` "
		"where ghi_chu=%s and kenh=%s and ifnull(hoa_don, '')='' and ifnull(da_tra, 0)=0 for update",
		(ghi_chu, NGUON_WEB), as_dict=True)
	for h in hang:
		dt, ma = ("Vagabond Combo", h.get("combo")) if h.get("combo") else ("Vagabond CTKM", h.get("ctkm"))
		if ma:
			frappe.db.sql("update `tab%s` set da_dung=greatest(ifnull(da_dung, 0) - 1, 0) where name=%%s" % dt, (ma,))
		# QT-20: không xoá, chỉ đánh dấu đã trả (vẫn tra được đơn, chương trình,
		# số giảm, khách).
		frappe.db.sql("update `tabVagabond CTKM Su Dung` set da_tra=1 where name=%s", (h["name"],))
	# Mã dùng một lần đã giữ cho đúng đơn này (giu_ma_mot_lan ghi cùng ghi chú).
	frappe.db.sql("update `tabVagabond Voucher` set trang_thai='Chua dung', ngay_dung=NULL "
		"where ghi_chu=%s and trang_thai='Da dung' and hoa_don is null", (ghi_chu,))
	return len(hang)


def giu_luot_web(kq, khach=None, sdt=None, ngay=None, ghi_chu=""):
	"""Codex #460 vòng 2: giữ lượt cho đơn web TRƯỚC khi gửi Pancake. Khác
	ghi_su_dung (ghi vết sau khi đã thu tiền, lỗi chỉ log): đây là phép CHẶT,
	lỗi nào cũng ném ra để bên gọi rollback và không gửi đơn, và không tự
	commit (bên gọi commit cùng bản ghi đơn). Mã dùng một lần do
	giu_ma_mot_lan giữ riêng."""
	ngay = str(getdate(ngay or nowdate()))
	so = re.sub(r"\D", "", str(sdt or ""))
	for a in (kq or {}).get("ap") or []:
		if a.get("loai") != "ctkm" or not a.get("ma"):
			raise ValueError("đơn web chỉ giữ lượt chương trình khuyến mãi")
		frappe.get_doc({
			"doctype": "Vagabond CTKM Su Dung",
			"ngay": ngay,
			"luc": now_datetime(),
			"loai": "CTKM",
			"ctkm": a["ma"],
			"ten_ctkm": a.get("ten"),
			"voucher": a.get("voucher") or "",
			"hoa_don": None,
			"tien_giam": flt(a.get("giam")),
			"thu_ngan": frappe.session.user,
			"quay": "",
			"kenh": NGUON_WEB,
			"khach": (khach or "").strip(),
			"sdt": so,
			"cach_duyet": "Web",
			"ghi_chu": ghi_chu or "",
		}).insert(ignore_permissions=True)
		frappe.db.sql("update `tabVagabond CTKM` set da_dung=ifnull(da_dung, 0)+1 where name=%s", (a["ma"],))


def tinh_co_khoa(items, **kw):
	"""Codex #460 vòng 3: quầy dùng CHUNG giao thức giữ lượt với đơn web. Tính
	một lần để biết chương trình nào áp, commit để kết thúc giao dịch đọc cũ,
	khoá hàng các chương trình đó, rồi tính lại trên ảnh chụp mới. Bên gọi giữ
	khoá tới khi ghi lượt xong (ghi_su_dung tự commit)."""
	kq = tinh(items, **kw)
	ds = [a["ma"] for a in (kq or {}).get("ap") or [] if a.get("loai") == "ctkm" and a.get("ma")]
	if not ds:
		return kq
	frappe.db.commit()
	khoa_ctkm(ds)
	return tinh(items, **kw)
