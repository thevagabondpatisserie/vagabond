# -*- coding: utf-8 -*-
"""v668 Gợi ý mua thêm (anh Việt duyệt 17/11/2026, phần F của prompt /banh).

Khách đã chọn bánh thì web gợi ý vài món dễ giao kèm:
  - giỏ đặt trước (cả giỏ có món Đặc biệt tuần này): bánh khô có hàng ở bếp
    trung tâm, viennoiserie (bếp làm theo đơn, luôn gợi ý được);
  - khung Đặt giao của tab Tại quầy: giỏ có bánh thì đồ uống, giỏ chỉ có đồ
    uống thì bánh còn trên tủ của đúng cửa hàng đang chọn.

Cách chọn: bảng "Món đi kèm" (Vagabond Mon Di Kem) do Marketing duyệt; web chỉ
dùng dòng Đã duyệt. Món chưa có cặp duyệt thì theo nhóm, câu lý do chung theo
nhóm (Cài đặt). Mỗi lần mở giỏ: lọc (tồn đúng nơi xuất, chưa có trong giỏ),
ghép (theo món trong giỏ), xếp hạng (ghim, hay mua cùng, tồn nhiều). Không gọi
dịch vụ ngoài, không gọi AI lúc khách đặt.

Tồn kho: mỗi bánh khô có ô Mức giữ tại bếp cho đơn web; phiếu chuyển từ bếp
ra cửa hàng làm tồn bếp xuống dưới mức giữ thì CẢNH BÁO, không chặn. Không tự
điều chuyển giữa các kho.

Đo kết quả: dòng thêm từ khối gợi ý ghi vào ảnh chụp đơn ("goi_y"), báo cáo
nhỏ chỉ đọc đơn mới (đơn cũ không có dấu này). Không sửa đơn, hoá đơn, chứng từ
đã ghi sổ.
"""

import json

import frappe

try:
	from frappe.rate_limiter import rate_limit
except Exception:  # bản giả trong ca kiểm
	def rate_limit(**_kw):
		return lambda f: f

DOCTYPE = "Vagabond Mon Di Kem"
NHAP, DA_DUYET, BO = "Nháp", "Đã duyệt", "Bỏ"
TRANG_THAI = (NHAP, DA_DUYET, BO)
NHOM_MAC_DINH = ("Bánh khô", "Bánh nướng")
NHOM_LAM_THEO_DON = ("Bánh nướng",)
KHO_BEP_MAC_DINH = ("Pastry - Thành phẩm - TV", "Baker - Thành phẩm - TV")
NGUONG_MAC_DINH = 3
TOI_DA_MAC_DINH = 4
TRAN_LY_DO = 40
LY_DO_NHOM_MAC_DINH = (
	("Bánh khô", "Giòn thơm, để được nhiều ngày", "Crisp, keeps for days"),
	("Bánh nướng", "Bếp nướng mới cho ngày giao", "Baked fresh for your delivery"),
	("Đồ uống", "Uống kèm cho hợp", "A drink to go with it"),
	("Bánh trên tủ", "Bánh còn trên tủ hôm nay", "On the counter today"),
)
QUYEN = ("Marketing", "System Manager", "Giám đốc", "AP Giám đốc")
QUYEN_KHO = QUYEN + ("Stock Manager", "Stock User", "VGB - Quản lý cửa hàng")

O = {
	"bat_gio": "goi_y_bat_gio", "bat_quay": "goi_y_bat_quay", "bat_dbt": "goi_y_bat_dbt",
	"thanh_mien_phi": "goi_y_thanh_mien_phi", "nhom": "goi_y_nhom", "toi_da": "goi_y_toi_da",
	"nguong": "goi_y_nguong_ton", "kho_bep": "goi_y_kho_bep", "ly_do_nhom": "goi_y_ly_do_nhom",
}
O_MUC_GIU = "vgb_muc_giu_web"
DA_GIEO = "vgb_goi_y_da_gieo_nhap"

TRUONG_MOI = {
	"Item": [
		{"fieldname": O_MUC_GIU, "label": "Mức giữ tại bếp cho đơn web", "fieldtype": "Int", "insert_after": "stock_uom",
			"description": "Bánh khô: số bếp trung tâm giữ lại cho đơn web. Phiếu chuyển ra cửa hàng làm tồn bếp xuống dưới số này thì "
				"hệ thống cảnh báo, không chặn. Để trống là không giữ."},
	],
	"Vagabond Settings": [
		{"fieldname": "sec_goi_y", "label": "Gợi ý mua thêm", "fieldtype": "Section Break", "insert_after": "weborder_tat_mien_phi", "collapsible": 1},
		{"fieldname": O["bat_gio"], "label": "Gợi ý ở giỏ đặt trước", "fieldtype": "Check", "default": "1", "insert_after": "sec_goi_y",
			"description": "Bật: giỏ đặt trước hiện khối Giao kèm cùng chuyến."},
		{"fieldname": O["bat_quay"], "label": "Gợi ý ở khung Đặt giao của Tại quầy", "fieldtype": "Check", "default": "1", "insert_after": O["bat_gio"],
			"description": "Bật: khung Đặt giao hiện khối Uống kèm hoặc Ăn kèm."},
		{"fieldname": O["bat_dbt"], "label": "Gợi ý khi giỏ có món Đặc biệt tuần này", "fieldtype": "Check", "default": "1", "insert_after": O["bat_quay"],
			"description": "Tắt: giỏ có món cuối tuần thì không hiện khối gợi ý."},
		{"fieldname": O["thanh_mien_phi"], "label": "Hiện thanh miễn phí giao", "fieldtype": "Check", "default": "1", "insert_after": O["bat_dbt"],
			"description": "Bật: giỏ giao tận nơi chưa đủ mốc miễn phí giao thì hiện số tiền còn thiếu và vạch tiến độ."},
		{"fieldname": "col_goi_y", "fieldtype": "Column Break", "insert_after": O["thanh_mien_phi"]},
		{"fieldname": O["nhom"], "label": "Nhóm món được đem ra gợi ý", "fieldtype": "Small Text", "insert_after": "col_goi_y",
			"description": "Mỗi dòng một nhóm món. Để trống là Bánh khô và Bánh nướng."},
		{"fieldname": O["toi_da"], "label": "Số món gợi ý tối đa", "fieldtype": "Int", "insert_after": O["nhom"],
			"description": "Từ 1 tới 6. Để trống là 4."},
		{"fieldname": O["nguong"], "label": "Ngưỡng tồn tối thiểu để gợi ý", "fieldtype": "Int", "insert_after": O["toi_da"],
			"description": "Chỉ gợi ý món còn từ số này trở lên ở đúng nơi xuất đơn. Để trống là 3."},
		{"fieldname": O["kho_bep"], "label": "Kho bếp xuất đơn đặt trước", "fieldtype": "Small Text", "insert_after": O["nguong"],
			"description": "Mỗi dòng một kho. Để trống là Pastry - Thành phẩm và Baker - Thành phẩm."},
		{"fieldname": O["ly_do_nhom"], "label": "Câu lý do chung theo nhóm", "fieldtype": "Small Text", "insert_after": O["kho_bep"],
			"description": "Mỗi dòng: Nhóm | câu tiếng Việt | câu tiếng Anh. Dùng khi món chưa có cặp Món đi kèm đã duyệt."},
	],
}


# ---------------------------------------------------------------- thuần

def _so(v, mac_dinh, nho=None, lon=None):
	try:
		n = int(float(str(v).replace(",", ".").strip()))
	except (TypeError, ValueError):
		return mac_dinh
	if nho is not None and n < nho:
		return mac_dinh
	if lon is not None and n > lon:
		n = lon
	return n


def _bat(v, mac_dinh=True):
	if v is None or str(v).strip() == "":
		return mac_dinh
	return str(v).strip().lower() in ("1", "true", "có", "bật", "yes")


def _dong(v):
	return [x.strip() for x in str(v or "").replace(";", "\n").split("\n") if x.strip()]


def chuan_cai_dat(raw):
	"""THUẦN: Cài đặt gợi ý từ các ô người điền tay, mọi cách điền hợp lý."""
	raw = raw or {}
	ly = {n: (vn, en) for n, vn, en in LY_DO_NHOM_MAC_DINH}
	for d in _dong(raw.get("ly_do_nhom")):
		p = [x.strip() for x in d.split("|")]
		if len(p) >= 2 and p[0] and p[1]:
			ly[p[0]] = (p[1][:TRAN_LY_DO + 20], (p[2] if len(p) > 2 else "")[:TRAN_LY_DO + 20] or p[1])
	return {
		"bat_gio": _bat(raw.get("bat_gio")), "bat_quay": _bat(raw.get("bat_quay")), "bat_dbt": _bat(raw.get("bat_dbt")),
		"thanh_mien_phi": _bat(raw.get("thanh_mien_phi")),
		"nhom": _dong(raw.get("nhom")) or list(NHOM_MAC_DINH),
		"toi_da": _so(raw.get("toi_da"), TOI_DA_MAC_DINH, 1, 6),
		"nguong": _so(raw.get("nguong"), NGUONG_MAC_DINH, 0),
		"kho_bep": _dong(raw.get("kho_bep")) or list(KHO_BEP_MAC_DINH),
		"ly_do_nhom": ly,
	}


def dang_ghim(cap, hom_nay):
	"""THUẦN: dòng đang trong khoảng ghim (có ít nhất một đầu mốc)."""
	tu, den = str(cap.get("ghim_tu") or "")[:10], str(cap.get("ghim_den") or "")[:10]
	if not tu and not den:
		return False
	return (not tu or tu <= hom_nay) and (not den or hom_nay <= den)


def xep_goi_y(gio, ung_vien, cap, ly_nhom, hom_nay, mua_cung=None, toi_da=TOI_DA_MAC_DINH, nhom_cua_gio=None):
	"""THUẦN: danh sách món gợi ý đã xếp hạng.

	gio: các món trong giỏ; mỗi món là một khoá hoặc danh sách khoá của CÙNG món
	  (mã size, tên bánh không size).
	ung_vien: {mã: {"ma", "ten", "anh", "gia", "nhom", "ton"}} đã LỌC đúng luật
	  tồn và giao được (ton None là bếp làm theo đơn).
	cap: dòng Đã duyệt [{"mon_goc", "nhom_goc", "mon_goi_y", "ly_do_vn", "ly_do_en",
	  "ghim_tu", "ghim_den", "uu_tien"}].
	ly_nhom: {nhóm: (vn, en)} câu chung khi không có cặp duyệt.
	nhom_cua_gio: các nhóm món của món trong giỏ (ghép dòng theo Nhóm món gốc).
	Trả tối đa toi_da * 3 món: trang khách bày toi_da, thêm một món thì món kế lên thay."""
	mon_gio = [set(str(k).strip().lower() for k in (x if isinstance(x, (list, tuple, set)) else [x]) if k) for x in (gio or [])]
	mon_gio = [m for m in mon_gio if m]
	gio = set().union(*mon_gio) if mon_gio else set()
	nhom_gio = set(nhom_cua_gio or [])
	mua_cung = mua_cung or {}
	chon = {}
	co_cap = set()
	for c in cap or []:
		goc = str(c.get("mon_goc") or "").strip().lower()
		khop = (goc and goc in gio) or (not goc and c.get("nhom_goc") and c.get("nhom_goc") in nhom_gio)
		if not khop:
			continue
		if goc:
			co_cap.add(goc)
		ma = c.get("mon_goi_y")
		if ma not in ung_vien or str(ma).lower() in gio:
			continue
		g = dang_ghim(c, hom_nay)
		cu = chon.get(ma)
		diem = (0 if g else 1, _so(c.get("uu_tien"), 10) if g else 99, 0 if goc else 1)
		if cu is None or diem < cu["_diem"]:
			chon[ma] = dict(ung_vien[ma], ly_do_vn=str(c.get("ly_do_vn") or "")[:TRAN_LY_DO + 20],
				ly_do_en=str(c.get("ly_do_en") or c.get("ly_do_vn") or "")[:TRAN_LY_DO + 20], ghim=1 if g else 0, _diem=diem)
	# Món trong giỏ chưa có cặp duyệt riêng: theo nhóm, câu chung theo nhóm.
	if any(not (m & co_cap) for m in mon_gio):
		for ma, u in ung_vien.items():
			if ma in chon or str(ma).lower() in gio:
				continue
			vn, en = ly_nhom.get(u.get("nhom")) or ("", "")
			chon[ma] = dict(u, ly_do_vn=vn, ly_do_en=en, ghim=0, _diem=(1, 99, 2))
	ds = sorted(chon.values(), key=lambda u: (u["_diem"][0], u["_diem"][1], -int(mua_cung.get(u["ma"], 0)),
		u["_diem"][2], -(u["ton"] if u.get("ton") is not None else 10 ** 6), u["ma"]))
	for u in ds:
		u.pop("_diem", None)
	return ds[:toi_da * 3]


def loc_ung_vien(mon, ton, nguong, lam_theo_don=NHOM_LAM_THEO_DON):
	"""THUẦN: món đủ điều kiện gợi ý cho đơn đặt trước. mon: [{"ma","ten","anh","gia","nhom"}];
	ton: {mã: số tồn ở kho bếp}. Nhóm làm theo đơn luôn được, không xét tồn.
	Không ảnh hay không giá thì không bày (thẻ cần ảnh, + cần giá)."""
	ra = {}
	for m in mon or []:
		if not m.get("anh") or not (float(m.get("gia") or 0) > 0):
			continue
		if m.get("nhom") in lam_theo_don:
			ra[m["ma"]] = dict(m, ton=None)
			continue
		so = float(ton.get(m["ma"]) or 0)
		if so >= nguong and so > 0:
			ra[m["ma"]] = dict(m, ton=so)
	return ra


def ma_goi_y(raw, ma_trong_don):
	"""THUẦN: mã khách thêm từ khối gợi ý mà còn trong đơn (đánh dấu dòng)."""
	co = set(ma_trong_don or [])
	ra = []
	for x in raw if isinstance(raw, list) else []:
		x = str(x or "").strip()
		if x and x in co and x not in ra:
			ra.append(x)
	return ra[:30]


def bao_cao(snaps, toi_da_mon=5):
	"""THUẦN: tỉ lệ đơn có món mua thêm, giá trị đơn trung bình, món được thêm nhiều nhất.
	snaps: ảnh chụp đơn MỚI (đã lọc theo ngày phát hành)."""
	so = co = 0
	tong = tong_co = 0
	mon = {}
	for s in snaps or []:
		try:
			s = json.loads(s) if isinstance(s, str) else (s or {})
		except ValueError:
			continue
		dong = s.get("mon") or []
		tien = sum(int(d.get("gia") or 0) * int(d.get("sl") or 0) for d in dong)
		so += 1
		tong += tien
		gy = set(s.get("goi_y") or [])
		if gy:
			co += 1
			tong_co += tien
			for d in dong:
				if d.get("ma") in gy:
					k = d.get("ma")
					x = mon.setdefault(k, {"ma": k, "ten": d.get("ten") or k, "sl": 0, "tien": 0})
					x["sl"] += int(d.get("sl") or 0)
					x["tien"] += int(d.get("gia") or 0) * int(d.get("sl") or 0)
	return {"so_don": so, "don_co_goi_y": co, "ti_le": round(co * 100.0 / so, 1) if so else 0,
		"gia_tri_tb": int(tong / so) if so else 0, "gia_tri_tb_co_goi_y": int(tong_co / co) if co else 0,
		"mon": sorted(mon.values(), key=lambda x: (-x["sl"], x["ma"]))[:toi_da_mon]}


def mua_cung_dem(snaps):
	"""THUẦN: {mã: số đơn mới có món này được thêm từ gợi ý} để xếp hạng."""
	ra = {}
	for s in snaps or []:
		try:
			s = json.loads(s) if isinstance(s, str) else (s or {})
		except ValueError:
			continue
		for m in set(s.get("goi_y") or []):
			ra[m] = ra.get(m, 0) + 1
	return ra


def canh_bao_xuat(dong, ton_bep, muc_giu, ten=None):
	"""THUẦN: dòng chuyển ra làm tồn bếp xuống dưới mức giữ. dong: [{"ma","sl"}] chỉ dòng
	xuất từ kho bếp; ton_bep: {mã: tồn hiện tại}; muc_giu: {mã: mức}."""
	tru = {}
	for d in dong or []:
		tru[d["ma"]] = tru.get(d["ma"], 0) + float(d.get("sl") or 0)
	ra = []
	for ma, sl in tru.items():
		muc = int(muc_giu.get(ma) or 0)
		if muc <= 0:
			continue
		con = float(ton_bep.get(ma) or 0) - sl
		if con < muc:
			ra.append({"ma": ma, "ten": (ten or {}).get(ma) or ma, "con": int(con) if con == int(con) else con, "muc": muc})
	return ra


def cau_canh_bao(ds):
	if not ds:
		return ""
	return ("Tồn bếp sẽ dưới mức giữ cho đơn web: " + "; ".join(
		"%s còn %s, mức giữ %s" % (x["ten"], x["con"], x["muc"]) for x in ds) +
		". Phiếu vẫn lưu được. Bếp cân nhắc giữ lại cho đơn web.")


def kiem_cap(d):
	"""THUẦN: lỗi của một dòng Món đi kèm, hoặc ""."""
	if not str(d.get("mon_goc") or "").strip() and not d.get("nhom_goc"):
		return "Chọn Món gốc hoặc Nhóm món gốc."
	if not d.get("mon_goi_y"):
		return "Chọn Món gợi ý."
	if d.get("trang_thai") not in TRANG_THAI:
		return "Trạng thái chỉ được Nháp, Đã duyệt hoặc Bỏ."
	for k in ("ly_do_vn", "ly_do_en"):
		if len(str(d.get(k) or "")) > TRAN_LY_DO + 20:
			return "Câu lý do dài quá, giữ dưới %d ký tự." % TRAN_LY_DO
	tu, den = str(d.get("ghim_tu") or "")[:10], str(d.get("ghim_den") or "")[:10]
	if tu and den and den < tu:
		return "Ngày ghim đến phải sau ngày ghim từ."
	return ""


# ---------------------------------------------------------------- Frappe

def kiem_dong(doc):
	loi = kiem_cap(doc.as_dict())
	if loi:
		frappe.throw(loi)
	doc.mon_goc = str(doc.mon_goc or "").strip().lower()


def cai_dat():
	from vagabond.lib import cfg_o

	return chuan_cai_dat({k: cfg_o(v) for k, v in O.items()})


def _hom_nay():
	from frappe.utils import nowdate

	return str(nowdate())


def _cap_duyet():
	return frappe.get_all(DOCTYPE, filters={"trang_thai": DA_DUYET},
		fields=["mon_goc", "nhom_goc", "mon_goi_y", "ly_do_vn", "ly_do_en", "ghim_tu", "ghim_den", "uu_tien"],
		limit_page_length=0, ignore_permissions=True)


def _snap_moi(ngay=60):
	from frappe.utils import add_days, nowdate

	from vagabond import don_web

	return [x.snapshot for x in frappe.get_all(don_web.DOCTYPE, filters={
		"creation": [">=", add_days(nowdate(), -ngay)], "trang_thai": ["in", list(don_web.TRANG_THAI_CON_HIEU_LUC)]},
		fields=["snapshot"], limit_page_length=0, ignore_permissions=True)]


def _anh(url):
	if not url:
		return ""
	return url if str(url).startswith(("http", "/")) else "/" + url


def _mon_nhom(nhom):
	return [{"ma": i.item_code, "ten": i.item_name, "anh": _anh(i.image), "gia": float(i.standard_rate or 0), "nhom": i.item_group}
		for i in frappe.get_all("Item", filters={"item_group": ["in", list(nhom)], "disabled": 0, "is_sales_item": 1, "has_variants": 0},
			fields=["item_code", "item_name", "image", "standard_rate", "item_group"], limit_page_length=0, ignore_permissions=True)]


def _ton(ma, kho):
	if not ma or not kho:
		return {}
	ra = {}
	for b in frappe.get_all("Bin", filters={"item_code": ["in", list(ma)], "warehouse": ["in", list(kho)]},
			fields=["item_code", "actual_qty"], limit_page_length=0, ignore_permissions=True):
		ra[b.item_code] = ra.get(b.item_code, 0) + float(b.actual_qty or 0)
	return ra


def _khoa_cua_ma(ma):
	"""{mã size: khoá bánh} theo thẻ Bánh của web."""
	from vagabond.banh_web import DT, tach_dong

	ra = {}
	for x in frappe.get_all(DT, fields=["khoa", "ma_hang"], limit_page_length=0, ignore_permissions=True):
		for m in tach_dong(x.ma_hang):
			if m in ma:
				ra[m] = x.khoa
	return ra


def _co_ma_pancake(ds):
	"""Chỉ giữ món Pancake có mã (thiếu mã thì cả đơn bị từ chối lúc gửi)."""
	from vagabond import don_hang
	from vagabond.lib import cfg, key

	try:
		c = cfg()
		k = key(c, "pancake_api_key")
	except Exception:
		return ds
	if not k or not c.pancake_shop_id:
		return ds
	return [u for u in ds if don_hang._uuid_tu_ma(c, k, u["ma"])]


def _ds(v):
	try:
		return [str(x)[:40] for x in (json.loads(v) if isinstance(v, str) else (v or []))][:40]
	except (ValueError, TypeError):
		return []


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=600)
def goi_y_dat_truoc(ma=None, bo=None):
	"""Khối Giao kèm cùng chuyến ở giỏ đặt trước. ma: JSON mã các BÁNH khách chọn
	(món gốc); bo: mọi mã đang trong giỏ, kể cả món vừa thêm từ gợi ý (không gợi ý lại,
	không coi là món gốc)."""
	ds_ma = _ds(ma)
	ds_bo = _ds(bo)
	cd = cai_dat()
	ra = {"bat": 1 if cd["bat_gio"] else 0, "toi_da": cd["toi_da"], "thanh_mien_phi": 1 if cd["thanh_mien_phi"] else 0, "mon": []}
	if not cd["bat_gio"] or not ds_ma:
		return ra
	if not cd["bat_dbt"]:
		from vagabond import dac_biet_tuan as dbt

		dot = dbt.dot_cong_khai()
		if dot and any(m in s for s in dbt.ma_theo_khoa(dot).values() for m in ds_ma):
			ra["bat"] = 0
			return ra
	mon = _mon_nhom(cd["nhom"])
	uv = loc_ung_vien(mon, _ton([m["ma"] for m in mon], cd["kho_bep"]), cd["nguong"])
	khoa = _khoa_cua_ma(set(ds_ma))
	gio = [[m, khoa.get(m) or ""] for m in ds_ma]
	nhom = {x.item_group for x in frappe.get_all("Item", filters={"item_code": ["in", ds_ma]}, fields=["item_group"],
		limit_page_length=0, ignore_permissions=True)}
	uv = {m: u for m, u in uv.items() if m not in set(ds_bo)}
	ds = xep_goi_y(gio, uv, _cap_duyet(), cd["ly_do_nhom"], _hom_nay(), mua_cung_dem(_snap_moi()), cd["toi_da"], nhom)
	ra["mon"] = [{k: u.get(k) for k in ("ma", "ten", "anh", "gia", "ly_do_vn", "ly_do_en", "ghim")} for u in _co_ma_pancake(ds)]
	return ra


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=600)
def cap_quay():
	"""Khung Đặt giao của Tại quầy: trang khách đã có món, tồn trên tủ của đúng
	cửa hàng; máy chủ chỉ trả cặp đã duyệt, câu chung và cài đặt."""
	from vagabond import don_quay

	cd = cai_dat()
	return {"bat": 1 if cd["bat_quay"] else 0, "toi_da": cd["toi_da"], "nguong": cd["nguong"],
		"thanh_mien_phi": 1 if cd["thanh_mien_phi"] else 0, "mien_phi_tu": don_quay.nguong_mien_phi(),
		"ly_do_nhom": {k: list(v) for k, v in cd["ly_do_nhom"].items()}, "hom_nay": _hom_nay(),
		"cap": [{k: c.get(k) for k in ("mon_goc", "nhom_goc", "mon_goi_y", "ly_do_vn", "ly_do_en", "uu_tien")}
			for c in _cap_duyet()] if cd["bat_quay"] else [],
		"ghim": [c.mon_goi_y for c in _cap_duyet() if dang_ghim(c, _hom_nay())]}


# ------------------------------------------------- màn Món đi kèm trong app

def _quyen(ds=QUYEN):
	if not set(frappe.get_roles()) & set(ds):
		frappe.throw("Chỉ Marketing hoặc giám đốc dùng được màn này.", frappe.PermissionError)


@frappe.whitelist()
def man_hinh(trang_thai=None, tim=None):
	"""Dữ liệu màn Món đi kèm: các cặp gom theo món gốc, cài đặt, món dưới mức giữ, báo cáo."""
	_quyen()
	loc = {"trang_thai": trang_thai} if trang_thai in TRANG_THAI else {}
	rows = frappe.get_all(DOCTYPE, filters=loc, fields=["name", "mon_goc", "nhom_goc", "mon_goi_y", "ten_goi_y", "ly_do_vn", "ly_do_en",
		"trang_thai", "ghim_tu", "ghim_den", "uu_tien", "nguon"], order_by="mon_goc asc, uu_tien asc, modified desc", limit_page_length=0)
	q = str(tim or "").strip().lower()
	if q:
		rows = [r for r in rows if q in " ".join(str(r.get(k) or "") for k in ("mon_goc", "nhom_goc", "ten_goi_y", "ly_do_vn")).lower()]
	dem = {t: frappe.db.count(DOCTYPE, {"trang_thai": t}) for t in TRANG_THAI}
	cd = cai_dat()
	return {"cap": rows, "dem": dem, "cai_dat": dict(cd, ly_do_nhom=[[k, v[0], v[1]] for k, v in cd["ly_do_nhom"].items()]),
		"hom_nay": _hom_nay(), "sua_cai_dat": 1}


@frappe.whitelist(methods=["POST"])
def doi_nhieu(ten=None, trang_thai=None):
	"""Duyệt hay bỏ nhiều dòng một lần. Chỉ đổi dòng đang khác trạng thái đích."""
	_quyen()
	if trang_thai not in TRANG_THAI:
		frappe.throw("Trạng thái chỉ được Nháp, Đã duyệt hoặc Bỏ.")
	ds = json.loads(ten) if isinstance(ten, str) else (ten or [])
	doi = 0
	for n in ds[:500]:
		cu = frappe.db.get_value(DOCTYPE, n, "trang_thai", for_update=True)
		if cu and cu != trang_thai:
			frappe.db.set_value(DOCTYPE, n, "trang_thai", trang_thai)
			doi += 1
	return {"ok": 1, "doi": doi}


@frappe.whitelist(methods=["POST"])
def luu_cap(du_lieu=None):
	"""Thêm hay sửa một dòng (sửa câu, ghim, thứ tự)."""
	_quyen()
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else (du_lieu or {})
	cho = ("mon_goc", "nhom_goc", "mon_goi_y", "ly_do_vn", "ly_do_en", "trang_thai", "ghim_tu", "ghim_den", "uu_tien")
	if d.get("name"):
		doc = frappe.get_doc(DOCTYPE, d["name"])
	else:
		doc = frappe.new_doc(DOCTYPE)
		doc.nguon = "Người thêm"
	for k in cho:
		if k in d:
			doc.set(k, d[k] or None if k in ("ghim_tu", "ghim_den", "nhom_goc") else d[k])
	doc.save()
	return {"ok": 1, "name": doc.name}


@frappe.whitelist(methods=["POST"])
def luu_cai_dat(du_lieu=None):
	"""Marketing, bếp sửa cài đặt gợi ý không cần mở Cài đặt lõi."""
	_quyen()
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else (du_lieu or {})
	for k, o in O.items():
		if k not in d:
			continue
		v = d[k]
		if k in ("bat_gio", "bat_quay", "bat_dbt", "thanh_mien_phi"):
			v = 1 if _bat(v, False) else 0
		elif isinstance(v, list):
			v = "\n".join(" | ".join(x) if isinstance(x, list) else str(x) for x in v)
		frappe.db.set_single_value("Vagabond Settings", o, v)
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	return {"ok": 1}


@frappe.whitelist()
def duoi_muc_giu():
	"""Danh sách món bánh khô đang dưới mức giữ tại bếp, để bếp theo dõi."""
	_quyen(QUYEN_KHO)
	cd = cai_dat()
	ds = frappe.get_all("Item", filters={O_MUC_GIU: [">", 0], "disabled": 0}, fields=["item_code", "item_name", O_MUC_GIU],
		limit_page_length=0)
	ton = _ton([x.item_code for x in ds], cd["kho_bep"])
	ra = [{"ma": x.item_code, "ten": x.item_name, "muc": int(x.get(O_MUC_GIU) or 0), "ton": ton.get(x.item_code, 0)}
		for x in ds if ton.get(x.item_code, 0) < int(x.get(O_MUC_GIU) or 0)]
	return {"mon": sorted(ra, key=lambda x: (x["ton"] - x["muc"], x["ma"])), "co_muc": len(ds)}


@frappe.whitelist(methods=["POST"])
def dat_muc_giu(ma=None, so=None):
	_quyen(QUYEN_KHO)
	if not ma or not frappe.db.exists("Item", ma):
		frappe.throw("Không thấy món này.")
	frappe.db.set_value("Item", ma, O_MUC_GIU, max(0, _so(so, 0)))
	return {"ok": 1}


@frappe.whitelist()
def bao_cao_goi_y(ngay=30):
	"""Báo cáo nhỏ: chỉ đơn mới (đơn trước bản v668 không có dấu thêm từ gợi ý)."""
	_quyen()
	n = _so(ngay, 30, 1, 365)
	return dict(bao_cao(_snap_moi(n)), ngay=n)


def canh_bao_muc_giu(doc, method=None):
	"""Hook Stock Entry validate: cảnh báo, KHÔNG chặn."""
	try:
		cd = cai_dat()
		kho = set(cd["kho_bep"])
		dong = [{"ma": r.item_code, "sl": float(r.transfer_qty or r.qty or 0)} for r in (doc.get("items") or [])
			if r.s_warehouse in kho and r.t_warehouse and r.t_warehouse not in kho]
		if not dong:
			return
		ma = list({d["ma"] for d in dong})
		muc = {x.name: x.get(O_MUC_GIU) for x in frappe.get_all("Item", filters={"name": ["in", ma]}, fields=["name", O_MUC_GIU],
			limit_page_length=0)}
		if not any(int(v or 0) > 0 for v in muc.values()):
			return
		ten = {x.name: x.item_name for x in frappe.get_all("Item", filters={"name": ["in", ma]}, fields=["name", "item_name"],
			limit_page_length=0)}
		cb = canh_bao_xuat(dong, _ton(ma, kho), muc, ten)
		if cb:
			frappe.msgprint(cau_canh_bao(cb), title="Dưới mức giữ cho đơn web", indicator="orange")
			doc.flags.vgb_canh_bao_muc_giu = cb
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: cảnh báo mức giữ tại bếp")


# ---------------------------------------------------------------- dựng

def dung():
	"""Gọi từ truong_tu_them.dung (after_migrate): ô mới và bản nháp lần đầu."""
	from vagabond.truong_tu_them import _dung_nhom

	_dung_nhom(TRUONG_MOI, "goi_y_mua")
	try:
		gieo_nhap()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: gieo bản nháp Món đi kèm")


def gieo_nhap():
	"""Nạp bản nháp Claude soạn (goi_y_nhap.NHAP) MỘT lần, trạng thái Nháp. Bảng đã có
	dòng thì không đụng. Món không còn trên site thì bỏ qua."""
	from vagabond.goi_y_nhap import NHAP as DS

	# Gieo MỘT lần trong đời site: Marketing xoá hết dòng thì lần deploy sau không gieo lại.
	if frappe.db.get_default(DA_GIEO) or frappe.db.count(DOCTYPE):
		return 0
	co = {x.name for x in frappe.get_all("Item", filters={"name": ["in", list({d[1] for d in DS})]}, fields=["name"], limit_page_length=0)}
	n = 0
	for goc, ma, vn, en, ut in DS:
		if ma not in co:
			continue
		doc = frappe.new_doc(DOCTYPE)
		if goc.startswith("@"):
			doc.nhom_goc = goc[1:] if frappe.db.exists("Item Group", goc[1:]) else None
			if not doc.nhom_goc:
				continue
		else:
			doc.mon_goc = goc
		doc.update({"mon_goi_y": ma, "ly_do_vn": vn, "ly_do_en": en, "trang_thai": NHAP, "uu_tien": ut, "nguon": "Bản nháp tự soạn 17/11/2026"})
		doc.insert(ignore_permissions=True)
		n += 1
	frappe.db.set_default(DA_GIEO, "1")
	return n
