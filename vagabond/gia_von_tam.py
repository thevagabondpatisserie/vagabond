# -*- coding: utf-8 -*-
"""Giá vốn tạm tính cho kế toán giá thành (Issue #482).

Anh Việt 16/10/2026 hỏi ERPNext có sẵn chỗ tính giá vốn tạm làm cơ sở định
giá bán không, để làm nút cho Khải. Lõi ERPNext chỉ có nút "Cập nhật chi phí"
của BOM và Công cụ cập nhật ĐMNVL: cả hai GHI ĐÈ vào công thức thật, chỉ đi
xuống công thức con khi dòng có `bom_no` (trên site 480/2.055 dòng có), và
không có phép nào tính ra giá bán. Anh chốt ba điểm:

1. Chỉ tính nguyên liệu, cộng dồn qua từng lớp bán thành phẩm, theo giá kho.
2. Giá bán đề xuất = giá vốn tạm / tỷ lệ giá vốn mục tiêu của nhóm món, làm
   tròn LÊN tới nghìn.
3. Chốt thì lưu vào bảng giá riêng "Giá vốn tạm tính", mỗi ngày một dòng.

Mô-đun này KHÔNG ghi vào BOM, Item, Bin, sổ kho, sổ cái hay bảng giá bán.
Đường ghi duy nhất là Item Price của bảng "Giá vốn tạm tính" trong `chot()`.

Phần trên là phép THUẦN, kiểm được không cần site
(khung/kiem_thu/thu_gia_von_tam.py). Phần dưới đọc Frappe theo lô.
"""

import json
import math

import frappe
from frappe.utils import flt, getdate, nowdate, now_datetime

from vagabond.vai_cua_hang import VAI_QLCT

BANG_GIA = "Giá vốn tạm tính"
BANG_GIA_NHAP = "Bảng giá nhập"   # cùng tên với bang_gia_nhap.TEN_BANG_GIA
BANG_GIA_BAN_MAC_DINH = "Standard Selling"
KHOA_TY_LE = "vgb_gia_von_tam_ty_le"

# Nhóm bánh bán ra, cùng danh sách với xuat_phuc_vu_ban.NGOAI_PHAM_VI (ca kiểm
# chốt hai bên khớp). Thứ tự này là thứ tự bày trên màn.
NHOM_BAN = (
	"Bánh ổ sinh nhật", "Bánh lạnh", "Bánh nướng", "Bánh khô",
	"Hộp bánh theo mùa", "Bánh Wholesale", "BÁNH NHẸ / CONFECTIONERY",
	"Topping cho món bánh", "Thành phẩm Bánh",
)
# Nhãn chip, tối đa 16 ký tự (AGENTS.md 2b điều 18).
NHAN_NHOM = {
	"Bánh ổ sinh nhật": "Bánh ổ",
	"BÁNH NHẸ / CONFECTIONERY": "Bánh nhẹ",
	"Hộp bánh theo mùa": "Hộp theo mùa",
	"Topping cho món bánh": "Topping",
	"Thành phẩm Bánh": "Bánh khác",
	"Bánh Wholesale": "Wholesale",
}

QUYEN_XEM = {"Accounts Manager", "Accounts User", VAI_QLCT, "System Manager", "Giám đốc", "AP Giám đốc"}
QUYEN_CHOT = {"Accounts Manager", VAI_QLCT, "System Manager", "Giám đốc"}

NGUON_KHO = "Giá kho"
NGUON_ITEM = "Giá khai trên mặt hàng"
NGUON_NHAP = "Bảng giá nhập"
NGUON_THIEU = "Thiếu giá"
NGUON_CONG_THUC = "Công thức"

# Thứ tự bày trong nhóm: món cần xử lên trước.
THU_TU_TRANG_THAI = (
	"vuot_gia_ban", "vong", "thieu_gia", "cao_hon_muc_tieu",
	"chua_gia_ban", "chua_dat_ty_le", "dat",
)
TRANG_THAI_BO_QUA = {
	"chua_cong_thuc": "Chưa có công thức",
	"vong": "Công thức vòng lặp",
	"thieu_gia": "Thiếu giá nguyên liệu",
}

SIDEBAR_DESK = ("Invoicing", "Manufacturing")
DUONG_MAN = "/gia-von-tam-tinh"   # slug của ("GVT", "Giá vốn tạm tính") trong duong_app.MAN


# ============================================================ phép THUẦN


def nhan_nhom(nhom):
	return NHAN_NHOM.get(nhom, nhom)


def tien(x):
	"""1004000 -> "1.004.000". THUẦN."""
	return "{:,}".format(int(round(flt(x)))).replace(",", ".")


def gia_la(ton, gia_item, gia_nhap):
	"""Giá một đơn vị kho của nguyên liệu lá, trả (giá, nguồn). THUẦN.

	`ton` là các dòng Bin {actual_qty, stock_value}. Thứ tự ưu tiên:
	1. bình quân các kho đang có tồn = tổng giá trị / tổng số lượng tồn > 0;
	2. Item.valuation_rate;  3. bảng "Bảng giá nhập";  4. thiếu giá.
	"""
	q = v = 0.0
	for b in ton or []:
		if flt(b.get("actual_qty")) > 0:
			q += flt(b.get("actual_qty"))
			v += flt(b.get("stock_value"))
	binh_quan = v / q if q > 0 and v > 0 else 0
	for nguon, gia in ((NGUON_KHO, binh_quan), (NGUON_ITEM, gia_item), (NGUON_NHAP, gia_nhap)):
		if flt(gia) > 0:
			return flt(gia), nguon
	return 0.0, NGUON_THIEU


def chon_gia_ap_dung(dong, dvt, hom_nay):
	"""Chọn MỘT giá đang áp dụng trong các dòng Item Price của một mã. THUẦN.

	Codex #483 vòng 1: một mã có thể có nhiều dòng (hết hạn, tương lai, giá
	riêng khách hoặc nhà cung cấp, theo lô, đơn vị khác). Lấy đúng như
	ERPNext v16 tự tra: bỏ dòng gắn khách, nhà cung cấp, lô; chỉ dòng còn hiệu
	lực hôm nay; đúng đơn vị kho (dòng không ghi đơn vị xếp sau); rồi
	`valid_from` mới nhất. Không có dòng nào thì None."""
	hn = str(hom_nay)[:10]
	hop = []
	for p in dong or []:
		if p.get("customer") or p.get("supplier") or p.get("batch_no"):
			continue
		u = p.get("uom")
		if u and dvt and u != dvt:
			continue
		tu = str(p.get("valid_from") or "")[:10]
		den = str(p.get("valid_upto") or "")[:10]
		if (tu and tu > hn) or (den and den < hn):
			continue
		hop.append((1 if u else 0, tu, flt(p.get("price_list_rate"))))
	if not hop:
		return None
	hop.sort(reverse=True)
	return hop[0][2]


def chon_con(bom_no, mac_dinh, dang_chay):
	"""Dòng trỏ vào công thức con nào. THUẦN. Cùng luật với
	patches/no_phantom_chuan.chon_bom_con: `bom_no` đang chạy thì giữ, rỗng
	hoặc đã tắt thì lấy công thức mặc định của mã, không có thì là lá."""
	if bom_no and bom_no in dang_chay:
		return bom_no
	return mac_dinh or None


def bom_cua_ma(ds_bom):
	"""Mã -> công thức đang chạy, ưu tiên bản mặc định. THUẦN."""
	ra = {}
	for b in ds_bom or []:
		if b.get("item") not in ra or int(b.get("is_default") or 0):
			ra[b.get("item")] = b.get("name")
	return ra


def cong_don(thanh_phan, ma_bom, gia_la_cua):
	"""Giá một đơn vị của MỌI công thức, cộng dồn qua công thức con. THUẦN.

	`thanh_phan`: {bom: {"so_ra": BOM.quantity, "dong": [{ma, sl, bom_no}]}},
	`sl` là số lượng theo ĐƠN VỊ KHO (stock_qty).
	`ma_bom`: mã -> công thức mặc định đang chạy.
	`gia_la_cua(ma)` -> (giá, nguồn) cho nguyên liệu lá.

	Trả {bom: {"gia", "thieu": set mã lá thiếu giá ở mọi tầng, "vong",
	"so_ra_loi"}}. Gặp vòng A -> B -> A thì gắn cờ `vong` rồi dừng, không đệ
	quy vô tận.
	"""
	dang_chay = set(thanh_phan)
	nho = {}

	def tinh(bom, dang):
		if bom in nho:
			return nho[bom]
		if bom in dang:
			return {"gia": 0.0, "thieu": set(), "vong": True, "so_ra_loi": False}
		dang.add(bom)
		info = thanh_phan.get(bom) or {"so_ra": 1, "dong": []}
		tong, thieu, vong = 0.0, set(), False
		for d in info.get("dong") or []:
			con = chon_con(d.get("bom_no"), ma_bom.get(d.get("ma")), dang_chay)
			if con:
				k = tinh(con, dang)
				g = k["gia"]
				thieu |= k["thieu"]
				vong = vong or k["vong"]
			else:
				g, nguon = gia_la_cua(d.get("ma"))
				if nguon == NGUON_THIEU:
					thieu.add(d.get("ma"))
			tong += flt(g) * flt(d.get("sl"))
		so_ra = flt(info.get("so_ra"))
		so_ra_loi = so_ra <= 0
		if so_ra_loi:
			so_ra = 1.0
		dang.discard(bom)
		kq = {"gia": tong / so_ra, "thieu": thieu, "vong": vong, "so_ra_loi": so_ra_loi}
		nho[bom] = kq
		return kq

	for bom in sorted(thanh_phan):
		tinh(bom, set())
	return nho


def dong_chi_tiet(bom, thanh_phan, ma_bom, gia_la_cua, ket):
	"""Các dòng một tầng của công thức `bom`, cho sheet chi tiết. THUẦN."""
	dang_chay = set(thanh_phan)
	ra = []
	for d in (thanh_phan.get(bom) or {}).get("dong") or []:
		con = chon_con(d.get("bom_no"), ma_bom.get(d.get("ma")), dang_chay)
		if con:
			k = ket.get(con) or {}
			don_gia, nguon = flt(k.get("gia")), NGUON_CONG_THUC
			thieu = len(k.get("thieu") or ())
		else:
			don_gia, nguon = gia_la_cua(d.get("ma"))
			thieu = 1 if nguon == NGUON_THIEU else 0
		ra.append({
			"ma": d.get("ma"), "ten": d.get("ten") or d.get("ma"), "sl": flt(d.get("sl")),
			"dvt": d.get("dvt") or "", "don_gia": don_gia, "nguon": nguon,
			"thanh_tien": don_gia * flt(d.get("sl")), "bom_con": con, "thieu": thieu,
		})
	return ra


def gia_de_xuat(gia_von, ty_le_pct):
	"""Giá bán đề xuất = giá vốn / tỷ lệ, làm tròn LÊN tới nghìn. THUẦN.
	None khi giá vốn <= 0 hoặc tỷ lệ ngoài (0, 95]."""
	if flt(gia_von) <= 0:
		return None
	try:
		p = float(ty_le_pct)
	except (TypeError, ValueError):
		return None
	if not (0 < p <= 95):
		return None
	# round(.., 6) để 250000 / 0.25 không thành 1000.0000000001 nghìn.
	return int(math.ceil(round(flt(gia_von) / (p / 100.0) / 1000.0, 6))) * 1000


def ty_le_hien(gia_von, gia_ban):
	"""Giá vốn / giá bán, phần trăm một số lẻ. THUẦN."""
	if flt(gia_ban) <= 0 or flt(gia_von) <= 0:
		return None
	return round(flt(gia_von) * 100.0 / flt(gia_ban), 1)


def trang_thai(co_cong_thuc, vong, so_thieu, gia_von, gia_ban, ty_le_muc_tieu):
	"""Một món đang ở đâu. THUẦN. Thứ tự ưu tiên: chua_cong_thuc, vong,
	thieu_gia, vuot_gia_ban, chua_gia_ban, cao_hon_muc_tieu / dat,
	chua_dat_ty_le."""
	if not co_cong_thuc:
		return "chua_cong_thuc"
	if vong:
		return "vong"
	if so_thieu:
		return "thieu_gia"
	if flt(gia_ban) > 0 and flt(gia_von) >= flt(gia_ban):
		return "vuot_gia_ban"
	if flt(gia_ban) <= 0:
		return "chua_gia_ban"
	if gia_de_xuat(1, ty_le_muc_tieu) is None:
		return "chua_dat_ty_le"
	if (ty_le_hien(gia_von, gia_ban) or 0) > float(ty_le_muc_tieu):
		return "cao_hon_muc_tieu"
	return "dat"


def chuan_ty_le(vao, nhom_hop_le=NHOM_BAN):
	"""Làm sạch dict nhóm -> phần trăm khi Khải lưu. THUẦN.

	Ô trống thì bỏ tỷ lệ của nhóm đó. Nhận "25" hoặc "25,5". Ngoài 1..95 hoặc
	nhóm lạ thì ném ValueError bằng câu tiếng Việt."""
	if isinstance(vao, str):
		vao = json.loads(vao or "{}")
	ra = {}
	for nhom, gia_tri in (vao or {}).items():
		if nhom not in nhom_hop_le:
			raise ValueError("Nhóm món không thuộc danh sách bánh bán ra: %s" % nhom)
		if gia_tri in (None, ""):
			continue
		try:
			p = float(str(gia_tri).replace(",", "."))
		except ValueError:
			raise ValueError("Tỷ lệ của nhóm %s phải là số, ví dụ 25." % nhom)
		if not (1 <= p <= 95):
			raise ValueError("Tỷ lệ của nhóm %s phải từ 1 tới 95 phần trăm." % nhom)
		ra[nhom] = round(p, 1)
	return ra


def lan_truoc(gia_von, ngay, gia):
	"""Lần chốt gần nhất so với giá vốn bây giờ. THUẦN."""
	if not ngay or flt(gia) <= 0:
		return None
	return {"ngay": str(ngay), "gia": flt(gia),
		"chenh_pct": round((flt(gia_von) - flt(gia)) * 100.0 / flt(gia), 1)}


def trung_vi(so):
	so = sorted(x for x in so if x is not None)
	if not so:
		return None
	n = len(so)
	return so[n // 2] if n % 2 else round((so[n // 2 - 1] + so[n // 2]) / 2.0, 1)


def ghi_chu(d):
	"""Ghi chú trên dòng Item Price lúc chốt. THUẦN."""
	phan = []
	if d.get("ty_le_muc_tieu"):
		phan.append("Tỷ lệ mục tiêu %s%%." % ("%g" % d["ty_le_muc_tieu"]).replace(".", ","))
	else:
		phan.append("Chưa đặt tỷ lệ mục tiêu.")
	if d.get("gia_de_xuat"):
		phan.append("Giá bán đề xuất %s." % tien(d["gia_de_xuat"]))
	phan.append("Giá bán lúc chốt %s." % tien(d["gia_ban"]) if flt(d.get("gia_ban")) > 0 else "Chưa có giá bán.")
	phan.append("Chỉ gồm nguyên liệu.")
	return " ".join(phan)


def dong_bang_gia(dong, ngay):
	"""Từ các dòng màn hình ra payload Item Price để chốt. THUẦN.

	Bỏ qua món chưa công thức, vòng lặp, thiếu giá nguyên liệu, hoặc giá vốn
	0 (không có gì đúng để lưu). Trả (luu, bo_qua) với bo_qua là
	{lý do tiếng Việt: số món}."""
	luu, bo_qua = [], {}
	for d in dong or []:
		ly_do = TRANG_THAI_BO_QUA.get(d.get("trang_thai"))
		if not ly_do and flt(d.get("gia_von")) <= 0:
			ly_do = "Giá vốn bằng 0"
		if ly_do:
			bo_qua[ly_do] = bo_qua.get(ly_do, 0) + 1
			continue
		luu.append({
			"item_code": d["ma"], "uom": d.get("dvt"), "price_list_rate": round(flt(d["gia_von"]), 2),
			"valid_from": str(ngay), "note": ghi_chu(d),
		})
	return luu, bo_qua


def dung_bang(ban, ma_bom, ket, gia_ban, chot_truoc, ty_le, ton_nhom=None):
	"""Ghép mọi thứ thành dữ liệu màn hình. THUẦN.

	`ban`: các món bán ra {ma, ten, nhom, dvt, anh}. `ket`: kết quả cong_don.
	`gia_ban`: mã -> giá. `chot_truoc`: mã -> (ngày, giá). `ty_le`: nhóm -> %.
	`ton_nhom`: mã -> tên nguyên liệu (để nói tên NVL thiếu giá)."""
	ten_nl = ton_nhom or {}
	dong, chua = [], []
	for m in ban:
		bom = ma_bom.get(m["ma"])
		if not bom:
			chua.append(m)
			continue
		k = ket.get(bom) or {"gia": 0, "thieu": set(), "vong": False}
		gv = round(flt(k["gia"]))
		gb = flt(gia_ban.get(m["ma"]))
		muc = ty_le.get(m["nhom"])
		tt = trang_thai(True, k["vong"], len(k["thieu"]), gv, gb, muc)
		thieu = sorted(k["thieu"])
		ct = chot_truoc.get(m["ma"]) or (None, None)
		dong.append({
			"ma": m["ma"], "ten": m["ten"], "nhom": m["nhom"], "dvt": m.get("dvt"), "anh": m.get("anh"),
			"gia_von": gv, "gia_ban": gb, "ty_le": ty_le_hien(gv, gb), "ty_le_muc_tieu": muc,
			"gia_de_xuat": gia_de_xuat(gv, muc) if tt not in TRANG_THAI_BO_QUA else None,
			"trang_thai": tt, "thieu_so": len(thieu), "thieu_ten": [ten_nl.get(x, x) for x in thieu[:5]],
			"lan_truoc": lan_truoc(gv, ct[0], ct[1]),
		})
	thu_nhom = {n: i for i, n in enumerate(NHOM_BAN)}
	thu_tt = {t: i for i, t in enumerate(THU_TU_TRANG_THAI)}
	dong.sort(key=lambda d: (thu_nhom.get(d["nhom"], 99), thu_tt.get(d["trang_thai"], 99), d["ten"] or ""))
	nhom = []
	for n in NHOM_BAN:
		cua = [d for d in dong if d["nhom"] == n]
		so_chua = sum(1 for m in chua if m["nhom"] == n)
		if not cua and not so_chua:
			continue
		nhom.append({
			"ten": n, "nhan": nhan_nhom(n), "so_mon": len(cua), "chua_cong_thuc": so_chua,
			"ty_le_muc_tieu": ty_le.get(n),
			"trung_vi": trung_vi([d["ty_le"] for d in cua if d["trang_thai"] not in TRANG_THAI_BO_QUA]),
		})
	chua.sort(key=lambda m: (thu_nhom.get(m["nhom"], 99), m["ten"] or ""))
	return {
		"dong": dong, "nhom": nhom,
		"chua_cong_thuc": {"so": len(chua), "ten": [m["ten"] for m in chua[:30]]},
	}


def muc_sidebar():
	"""Lối vào trên sidebar Desk. THUẦN."""
	return {"type": "Link", "label": "Giá vốn tạm tính", "link_type": "URL", "url": DUONG_MAN, "child": 0}


# ============================================================ chạm Frappe


def _kiem(quyen, viec):
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _theo_lo(doctype, truong, gia_tri, fields, them=None, lo=300, **kw):
	gia_tri = list(gia_tri)
	ra = []
	for i in range(0, len(gia_tri), lo):
		loc = {truong: ["in", gia_tri[i:i + lo]]}
		loc.update(them or {})
		ra += frappe.get_all(doctype, filters=loc, fields=fields, limit_page_length=0, **kw)
	return ra


def _gia_ap_dung(cac_ma, bang_gia, dvt):
	"""Mã -> giá đang áp dụng hôm nay trong một bảng giá (chon_gia_ap_dung)."""
	theo_ma = {}
	for p in _theo_lo("Item Price", "item_code", cac_ma,
			["item_code", "price_list_rate", "uom", "valid_from", "valid_upto", "customer", "supplier", "batch_no"],
			them={"price_list": bang_gia}):
		theo_ma.setdefault(p.item_code, []).append(p)
	ra = {}
	hom_nay = nowdate()
	for ma, dong in theo_ma.items():
		g = chon_gia_ap_dung(dong, dvt.get(ma), hom_nay)
		if g is not None:
			ra[ma] = g
	return ra


def _ty_le_da_luu():
	try:
		return json.loads(frappe.defaults.get_global_default(KHOA_TY_LE) or "{}") or {}
	except ValueError:
		return {}


def _bang_gia_ban():
	return frappe.db.get_single_value("Selling Settings", "selling_price_list") or BANG_GIA_BAN_MAC_DINH


def _doc():
	"""Đọc một lượt mọi thứ cần cho cả màn. Không hỏi từng mã."""
	ds_bom = frappe.get_all("BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["name", "item", "quantity", "is_default"], limit_page_length=0)
	ma_bom = bom_cua_ma(ds_bom)
	thanh_phan = {b.name: {"so_ra": flt(b.quantity), "dong": []} for b in ds_bom}
	for d in _theo_lo("BOM Item", "parent", thanh_phan.keys(),
			["parent", "item_code", "item_name", "qty", "stock_qty", "stock_uom", "uom", "bom_no"],
			them={"parenttype": "BOM"}, order_by="parent, idx"):
		thanh_phan[d.parent]["dong"].append({
			"ma": d.item_code, "ten": d.item_name, "dvt": d.stock_uom or d.uom,
			"sl": flt(d.stock_qty) or flt(d.qty), "bom_no": d.bom_no,
		})
	ma_nl = {d["ma"] for t in thanh_phan.values() for d in t["dong"]}
	ton = {}
	for b in _theo_lo("Bin", "item_code", ma_nl, ["item_code", "actual_qty", "stock_value"]):
		ton.setdefault(b.item_code, []).append(b)
	mat_hang = {i.name: i for i in _theo_lo("Item", "name", ma_nl, ["name", "item_name", "stock_uom", "valuation_rate"])}
	gia_nhap = _gia_ap_dung(ma_nl, BANG_GIA_NHAP, {k: v.stock_uom for k, v in mat_hang.items()})

	def gia_la_cua(ma):
		i = mat_hang.get(ma)
		return gia_la(ton.get(ma), i.valuation_rate if i else 0, gia_nhap.get(ma))

	ket = cong_don(thanh_phan, ma_bom, gia_la_cua)
	ten_nl = {k: v.item_name for k, v in mat_hang.items()}
	return thanh_phan, ma_bom, gia_la_cua, ket, ten_nl


def _bang():
	thanh_phan, ma_bom, gia_la_cua, ket, ten_nl = _doc()
	ban = [{"ma": i.name, "ten": i.item_name, "nhom": i.item_group, "dvt": i.stock_uom, "anh": i.image}
		for i in frappe.get_all("Item", filters={"item_group": ["in", list(NHOM_BAN)], "disabled": 0},
			fields=["name", "item_name", "item_group", "stock_uom", "image"], limit_page_length=0)]
	ma_ban = [m["ma"] for m in ban]
	dvt = {m["ma"]: m["dvt"] for m in ban}
	gia_ban = _gia_ap_dung(ma_ban, _bang_gia_ban(), dvt)
	chot_truoc = {}
	for p in _theo_lo("Item Price", "item_code", ma_ban, ["item_code", "price_list_rate", "valid_from"],
			them={"price_list": BANG_GIA}, order_by="valid_from desc"):
		chot_truoc.setdefault(p.item_code, (p.valid_from, p.price_list_rate))
	ty_le = _ty_le_da_luu()
	return dung_bang(ban, ma_bom, ket, gia_ban, chot_truoc, ty_le, ten_nl), ty_le


@frappe.whitelist()
def tinh():
	"""Dữ liệu cả màn Giá vốn tạm tính. Chỉ đọc."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	bang, ty_le = _bang()
	bang.update({
		"ty_le": ty_le, "cap_nhat_luc": now_datetime().strftime("%H:%M"),
		"sua_duoc": bool(QUYEN_CHOT & set(frappe.get_roles())), "ngay": nowdate(),
	})
	return bang


@frappe.whitelist()
def chi_tiet(ma, bom=None):
	"""Các dòng nguyên liệu một tầng của một món (hoặc của một công thức con
	khi bấm xuống bán thành phẩm). Chỉ đọc."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	thanh_phan, ma_bom, gia_la_cua, ket, _ten = _doc()
	bom = bom or ma_bom.get(ma)
	if not bom or bom not in thanh_phan:
		frappe.throw("Món này chưa có công thức đang dùng.")
	k = ket.get(bom) or {}
	return {
		"ma": ma, "ten": frappe.db.get_value("Item", ma, "item_name") or ma, "bom": bom,
		"so_ra": flt(thanh_phan[bom]["so_ra"]), "gia": flt(k.get("gia")), "vong": bool(k.get("vong")),
		"dong": dong_chi_tiet(bom, thanh_phan, ma_bom, gia_la_cua, ket),
	}


@frappe.whitelist()
def luu_ty_le(ty_le):
	"""Lưu tỷ lệ giá vốn mục tiêu theo nhóm. Không đụng doctype nào."""
	_kiem(QUYEN_CHOT, "đặt tỷ lệ mục tiêu")
	try:
		sach = chuan_ty_le(ty_le)
	except ValueError as e:
		frappe.throw(str(e))
	frappe.defaults.set_global_default(KHOA_TY_LE, json.dumps(sach, ensure_ascii=False))
	return {"ty_le": sach}


def _bao_dam_bang_gia():
	if frappe.db.exists("Price List", BANG_GIA):
		return BANG_GIA
	d = frappe.get_doc({
		"doctype": "Price List", "price_list_name": BANG_GIA,
		"buying": 1, "selling": 0, "enabled": 1, "currency": "VND",
	})
	d.insert(ignore_permissions=True)
	return d.name


@frappe.whitelist(methods=["POST"])
def chot():
	"""Lưu giá vốn tạm hôm nay vào bảng giá "Giá vốn tạm tính". Tính lại ở máy
	chủ, không nhận số từ máy khách. Mỗi món mỗi ngày một dòng (ERPNext v16
	cho nhiều dòng khác `valid_from`); chốt lại trong ngày thì cập nhật."""
	_kiem(QUYEN_CHOT, "chốt giá vốn tạm tính")
	bang, _ty_le = _bang()
	ngay = getdate(nowdate())
	luu, bo_qua = dong_bang_gia(bang["dong"], ngay)
	ten_bang = _bao_dam_bang_gia()
	for p in luu:
		co = frappe.db.get_value("Item Price", {
			"price_list": ten_bang, "item_code": p["item_code"], "uom": p["uom"], "valid_from": ngay,
		})
		if co:
			d = frappe.get_doc("Item Price", co)
			d.price_list_rate = p["price_list_rate"]
			d.note = p["note"]
			d.save(ignore_permissions=True)
		else:
			frappe.get_doc(dict(p, doctype="Item Price", price_list=ten_bang, valid_from=ngay)).insert(ignore_permissions=True)
	return {"da_luu": len(luu), "bo_qua": bo_qua, "ngay": str(ngay), "bang_gia": ten_bang}


def dung_sidebar():
	"""Thêm lối vào sidebar Hoá đơn và Sản xuất trên Desk. Lặp lại được,
	không nhân mục; sidebar chưa có thì bỏ qua. Tự nuốt lỗi để không chặn
	migrate (cùng nếp với cong_thuc.dung_sidebar)."""
	them = 0
	m = muc_sidebar()
	for ten in SIDEBAR_DESK:
		try:
			if not frappe.db.exists("Workspace Sidebar", ten):
				continue
			sb = frappe.get_doc("Workspace Sidebar", ten)
			if any(x.get("type") == m["type"] and x.get("label") == m["label"] for x in sb.get("items") or []):
				continue
			sb.append("items", dict(m))
			sb.flags.ignore_permissions = True
			sb.save()
			them += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "gia_von_tam: dung sidebar " + ten)
	return them
