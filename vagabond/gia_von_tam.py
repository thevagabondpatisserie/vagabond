# -*- coding: utf-8 -*-
"""Giá vốn tạm tính cho kế toán giá thành (Issue #482).

Anh Việt 16/10/2026 hỏi ERPNext có sẵn chỗ tính giá vốn tạm làm cơ sở định
giá bán không, để làm nút cho Khải. Lõi ERPNext chỉ có nút "Cập nhật chi phí"
của BOM và Công cụ cập nhật ĐMNVL: cả hai GHI ĐÈ vào công thức thật, chỉ đi
xuống công thức con khi dòng có `bom_no` (trên site 480/2.055 dòng có), và
không có phép nào tính ra giá bán. Anh chốt ba điểm:

1. Chỉ tính nguyên liệu, cộng dồn qua từng lớp bán thành phẩm, theo giá kho.
2. Giá bán đề xuất = giá vốn tạm NHÂN hệ số mục tiêu của nhóm món, làm tròn
   LÊN tới nghìn. Anh Việt 16/10 tối: tiệm đọc theo "lãi số lần" (giá bán
   gấp mấy lần giá vốn), nên mục tiêu và con số chính là hệ số, phần trăm
   giá vốn chỉ hiện kèm.
3. Chốt thì lưu vào bảng giá riêng "Giá vốn tạm tính", mỗi ngày một dòng.
4. Món R&D chưa bán: Phiếu tính giá thử (doctype Vagabond Gia Thu) nhập
   nguyên liệu tạm, tính bằng đúng phép cộng dồn của món đang bán. Không tạo
   Item, không tạo BOM.

Mô-đun này KHÔNG ghi vào BOM, Item, Bin, sổ kho, sổ cái hay bảng giá bán.
Đường ghi duy nhất là Item Price của bảng "Giá vốn tạm tính" trong `chot()`.

Phần trên là phép THUẦN, kiểm được không cần site
(khung/kiem_thu/thu_gia_von_tam.py). Phần dưới đọc Frappe theo lô.
"""

import json
import math

import frappe
from frappe.utils import flt, getdate, nowdate, now_datetime

from vagabond import tim_kiem
from vagabond.vai_cua_hang import VAI_QLCT

BANG_GIA = "Giá vốn tạm tính"
BANG_GIA_NHAP = "Bảng giá nhập"   # cùng tên với bang_gia_nhap.TEN_BANG_GIA
BANG_GIA_BAN_MAC_DINH = "Standard Selling"
KHOA_HE_SO = "vgb_gia_von_tam_he_so"
DT_THU = "Vagabond Gia Thu"
HE_SO_MIN, HE_SO_MAX = 1.0, 20.0   # hệ số phải > 1 (bán lỗ không phải mục tiêu) và <= 20
NGUON_TAY = "Nhập tay"

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
# Codex #486 v2: mã có từ hai công thức đang chạy mà chưa chọn mặc định thì
# phiếu thử KHÔNG lấy giá kho thay, coi là thiếu để nhập giá tay hoặc chọn
# công thức mặc định trên Desk (giống màn món đang bán).
NGUON_NHIEU_CT = "Nhiều công thức, chưa chọn mặc định"
# Codex #486 v3: mã đó nằm ở tầng dưới (dòng BOM không bom_no) cũng vậy. Một
# nguồn: `_doc` trả gia_la_cua đã biết mã mơ hồ; mọi nơi coi "thiếu" theo bộ này.
NGUON_LA_THIEU = (NGUON_THIEU, NGUON_NHIEU_CT)

# Thứ tự bày trong nhóm: món cần xử lên trước.
THU_TU_TRANG_THAI = (
	"vuot_gia_ban", "vong", "thieu_gia", "duoi_muc_tieu",
	"chua_gia_ban", "chua_dat_muc_tieu", "dat",
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


def chon_gia_ap_dung(dong, dvt, hom_nay, he_so=None):
	"""Chọn MỘT giá đang áp dụng trong các dòng Item Price của một mã. THUẦN.

	Codex #483 vòng 1: một mã có thể có nhiều dòng (hết hạn, tương lai, giá
	riêng khách hoặc nhà cung cấp, theo lô, đơn vị khác). Lấy đúng như
	ERPNext v16 tự tra: bỏ dòng gắn khách, nhà cung cấp, lô; chỉ dòng còn hiệu
	lực hôm nay; đúng đơn vị kho (dòng không ghi đơn vị xếp sau); rồi
	`valid_from` mới nhất. Không có dòng nào thì None.

	Codex #483 vòng 2: Bảng giá nhập ghi giá theo đơn vị MUA của hoá đơn
	(100.000 mỗi Kg cho mã tính kho bằng Gram). `he_so` là {đơn vị: số đơn vị
	kho} lấy từ UOM Conversion Detail của mã; dòng khác đơn vị kho mà có hệ
	số thì đổi về giá một đơn vị kho, không có hệ số mới bỏ. Thứ tự ưu tiên:
	đúng đơn vị kho, rồi đổi được qua hệ số, rồi dòng không ghi đơn vị."""
	hn = str(hom_nay)[:10]
	hop = []
	for p in dong or []:
		if p.get("customer") or p.get("supplier") or p.get("batch_no"):
			continue
		u = p.get("uom")
		gia = flt(p.get("price_list_rate"))
		hang = 2 if u else 0
		if u and dvt and u != dvt:
			hs = flt((he_so or {}).get(u))
			if hs <= 0:
				continue
			gia, hang = gia / hs, 1
		tu = str(p.get("valid_from") or "")[:10]
		den = str(p.get("valid_upto") or "")[:10]
		if (tu and tu > hn) or (den and den < hn):
			continue
		hop.append((hang, tu, gia))
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


def _bom_theo_ma(ds_bom):
	theo_ma = {}
	for b in ds_bom or []:
		theo_ma.setdefault(b.get("item"), []).append(b)
	return theo_ma


def bom_cua_ma(ds_bom):
	"""Mã -> công thức dùng để tính giá. THUẦN.

	Codex #483 vòng 3: có bản mặc định thì lấy bản mặc định; chỉ một bản đang
	chạy thì lấy bản đó; từ hai bản trở lên mà không bản nào mặc định thì KHÔNG
	đoán, vì thứ tự cơ sở dữ liệu trả về không phải luật nghiệp vụ. Mã đó nằm
	trong `ma_mo_ho` để màn hình nói rõ cần chọn công thức mặc định."""
	ra = {}
	for ma, ds in _bom_theo_ma(ds_bom).items():
		mac_dinh = sorted(b.get("name") for b in ds if int(b.get("is_default") or 0))
		if mac_dinh:
			ra[ma] = mac_dinh[0]
		elif len(ds) == 1:
			ra[ma] = ds[0].get("name")
	return ra


def ma_mo_ho(ds_bom):
	"""Mã có từ hai công thức đang chạy mà chưa bản nào mặc định -> tên các
	công thức, đã xếp. THUẦN."""
	ra = {}
	for ma, ds in _bom_theo_ma(ds_bom).items():
		if len(ds) > 1 and not any(int(b.get("is_default") or 0) for b in ds):
			ra[ma] = sorted(b.get("name") for b in ds)
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
				if nguon in NGUON_LA_THIEU:
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
			thieu = 1 if nguon in NGUON_LA_THIEU else 0
		ra.append({
			"ma": d.get("ma"), "ten": d.get("ten") or d.get("ma"), "sl": flt(d.get("sl")),
			"dvt": d.get("dvt") or "", "don_gia": don_gia, "nguon": nguon,
			"thanh_tien": don_gia * flt(d.get("sl")), "bom_con": con, "thieu": thieu,
		})
	return ra


def _so(x):
	"""Nhận số kiểu Việt ("5,5") hoặc số. None nếu không phải số. THUẦN."""
	if x in (None, ""):
		return None
	try:
		return float(str(x).replace(",", "."))
	except ValueError:
		return None


def he_so_hop_le(he_so):
	h = _so(he_so)
	return h is not None and HE_SO_MIN < h <= HE_SO_MAX


def gia_de_xuat(gia_von, he_so):
	"""Giá bán đề xuất = giá vốn x hệ số mục tiêu, làm tròn LÊN tới nghìn.
	THUẦN. None khi giá vốn <= 0 hoặc hệ số ngoài (1, 20]."""
	if flt(gia_von) <= 0 or not he_so_hop_le(he_so):
		return None
	# round(.., 6) để 250000 x 4 không thành 1000.0000000001 nghìn.
	return int(math.ceil(round(flt(gia_von) * _so(he_so) / 1000.0, 6))) * 1000


def ty_le_hien(gia_von, gia_ban):
	"""Giá vốn / giá bán, phần trăm một số lẻ (hiện kèm hệ số). THUẦN."""
	if flt(gia_ban) <= 0 or flt(gia_von) <= 0:
		return None
	return round(flt(gia_von) * 100.0 / flt(gia_ban), 1)


def he_so_hien(gia_von, gia_ban):
	"""Giá bán gấp mấy lần giá vốn, một số lẻ ("lãi số lần"). THUẦN."""
	if flt(gia_ban) <= 0 or flt(gia_von) <= 0:
		return None
	return round(flt(gia_ban) / flt(gia_von), 1)


def trang_thai(co_cong_thuc, vong, so_thieu, gia_von, gia_ban, he_so_muc_tieu):
	"""Một món đang ở đâu. THUẦN. Thứ tự ưu tiên: chua_cong_thuc, vong,
	thieu_gia, vuot_gia_ban, chua_gia_ban, chua_dat_muc_tieu, duoi_muc_tieu
	(giá bán chưa gấp đủ số lần mục tiêu) / dat. So bằng tỷ số thật, không so
	số đã làm tròn để x4,96 không lọt thành "đạt" x5."""
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
	if not he_so_hop_le(he_so_muc_tieu):
		return "chua_dat_muc_tieu"
	if flt(gia_von) > 0 and flt(gia_ban) / flt(gia_von) < _so(he_so_muc_tieu):
		return "duoi_muc_tieu"
	return "dat"


def chuan_he_so(vao, nhom_hop_le=NHOM_BAN):
	"""Làm sạch dict nhóm -> hệ số khi Khải lưu. THUẦN.

	Ô trống thì bỏ mục tiêu của nhóm đó. Nhận "5" hoặc "5,5". Không lớn hơn 1,
	quá 20 hoặc nhóm lạ thì ném ValueError bằng câu tiếng Việt."""
	if isinstance(vao, str):
		vao = json.loads(vao or "{}")
	ra = {}
	for nhom, gia_tri in (vao or {}).items():
		if nhom not in nhom_hop_le:
			raise ValueError("Nhóm món không thuộc danh sách bánh bán ra: %s" % nhom)
		if gia_tri in (None, ""):
			continue
		h = _so(gia_tri)
		if h is None:
			raise ValueError("Hệ số của nhóm %s phải là số, ví dụ 5." % nhom)
		if not (HE_SO_MIN < h <= HE_SO_MAX):
			raise ValueError("Hệ số của nhóm %s phải lớn hơn 1 và không quá 20 lần." % nhom)
		ra[nhom] = round(h, 2)
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


def _so_vn(x):
	return ("%g" % x).replace(".", ",")


def ghi_chu(d):
	"""Ghi chú trên dòng Item Price lúc chốt. THUẦN."""
	phan = []
	if d.get("he_so_muc_tieu"):
		phan.append("Hệ số mục tiêu x%s." % _so_vn(d["he_so_muc_tieu"]))
	else:
		phan.append("Chưa đặt hệ số mục tiêu.")
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


def dung_bang(ban, ma_bom, ket, gia_ban, chot_truoc, he_so, ton_nhom=None, mo_ho=None):
	"""Ghép mọi thứ thành dữ liệu màn hình. THUẦN.

	`ban`: các món bán ra {ma, ten, nhom, dvt, anh}. `ket`: kết quả cong_don.
	`gia_ban`: mã -> giá. `chot_truoc`: mã -> (ngày, giá). `he_so`: nhóm -> hệ số
	mục tiêu.
	`ton_nhom`: mã -> tên nguyên liệu (để nói tên NVL thiếu giá).
	`mo_ho`: mã -> các công thức đang chạy khi chưa chọn bản mặc định."""
	ten_nl = ton_nhom or {}
	mo_ho = mo_ho or {}
	dong, chua, nhieu = [], [], []
	for m in ban:
		bom = ma_bom.get(m["ma"])
		if not bom:
			(nhieu if m["ma"] in mo_ho else chua).append(m)
			continue
		k = ket.get(bom) or {"gia": 0, "thieu": set(), "vong": False}
		gv = round(flt(k["gia"]))
		gb = flt(gia_ban.get(m["ma"]))
		muc = he_so.get(m["nhom"])
		tt = trang_thai(True, k["vong"], len(k["thieu"]), gv, gb, muc)
		thieu = sorted(k["thieu"])
		ct = chot_truoc.get(m["ma"]) or (None, None)
		dong.append({
			"ma": m["ma"], "ten": m["ten"], "nhom": m["nhom"], "dvt": m.get("dvt"), "anh": m.get("anh"),
			"gia_von": gv, "gia_ban": gb, "he_so": he_so_hien(gv, gb), "ty_le": ty_le_hien(gv, gb),
			"he_so_muc_tieu": muc,
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
			"he_so_muc_tieu": he_so.get(n),
			"trung_vi": trung_vi([d["he_so"] for d in cua if d["trang_thai"] not in TRANG_THAI_BO_QUA]),
		})
	chua.sort(key=lambda m: (thu_nhom.get(m["nhom"], 99), m["ten"] or ""))
	nhieu.sort(key=lambda m: (thu_nhom.get(m["nhom"], 99), m["ten"] or ""))
	return {
		"dong": dong, "nhom": nhom,
		"chua_cong_thuc": {"so": len(chua), "ten": [m["ten"] for m in chua[:30]]},
		"nhieu_cong_thuc": {"so": len(nhieu), "ten": [m["ten"] for m in nhieu[:30]]},
	}


# ------------------------------------------------ phiếu tính giá thử (R&D)

MAX_DONG_THU = 150
TRANG_THU = 30   # số phiếu thử mỗi trang danh sách (Codex #486: không cắt im lặng)


def chuan_phieu(vao, nhom_hop_le=NHOM_BAN):
	"""Làm sạch phiếu tính giá thử từ máy khách. THUẦN.

	Mỗi dòng là một mã có sẵn (`item_code`) hoặc nguyên liệu chưa có mã (`ten`
	kèm `dvt`, giá nhập tay). Số lượng theo ĐƠN VỊ KHO của mã. Sai thì ném
	ValueError bằng câu tiếng Việt, nói đúng dòng nào."""
	if isinstance(vao, str):
		vao = json.loads(vao or "{}")
	vao = vao or {}
	ten = str(vao.get("ten_mon") or "").strip()
	if not ten:
		raise ValueError("Nhập tên món thử.")
	nhom = str(vao.get("nhom") or "").strip()
	if nhom and nhom not in nhom_hop_le:
		raise ValueError("Nhóm món không thuộc danh sách bánh bán ra: %s" % nhom)
	so_ra = _so(vao.get("so_ra"))
	if so_ra is None:
		so_ra = 1.0
	if so_ra <= 0:
		raise ValueError("Một mẻ phải ra hơn 0.")
	gia_ban = _so(vao.get("gia_ban_du_kien")) or 0.0
	if gia_ban < 0:
		raise ValueError("Giá bán dự kiến không được âm.")
	dong = []
	for i, d in enumerate(vao.get("dong") or [], 1):
		ma = str(d.get("item_code") or "").strip() or None
		ten_nl = str(d.get("ten") or "").strip()
		if not ma and not ten_nl:
			raise ValueError("Dòng %d chưa có nguyên liệu." % i)
		sl = _so(d.get("so_luong"))
		if sl is None or sl <= 0:
			raise ValueError("Dòng %d (%s): số lượng phải lớn hơn 0." % (i, ten_nl or ma))
		gia_tay = _so(d.get("don_gia_tay")) or 0.0
		if gia_tay < 0:
			raise ValueError("Dòng %d (%s): giá nhập tay không được âm." % (i, ten_nl or ma))
		dong.append({"item_code": ma, "ten": ten_nl, "dvt": str(d.get("dvt") or "").strip(),
			"so_luong": sl, "don_gia_tay": gia_tay})
	if len(dong) > MAX_DONG_THU:
		raise ValueError("Một phiếu tối đa %d dòng nguyên liệu." % MAX_DONG_THU)
	return {"name": vao.get("name") or None, "ten_mon": ten, "nhom": nhom, "so_ra": so_ra,
		"dvt_ra": str(vao.get("dvt_ra") or "").strip() or "Cái", "gia_ban_du_kien": gia_ban,
		"ghi_chu": str(vao.get("ghi_chu") or "").strip(), "dong": dong}


def noi_dung_phieu(d):
	"""Phần nội dung của một phiếu thử để so trước và sau khi lưu. THUẦN.
	`d` là dict hoặc Document; dòng là list dict hoặc dòng con."""
	g = (lambda o, k: o.get(k))
	return {
		"ten_mon": str(g(d, "ten_mon") or ""), "nhom": str(g(d, "nhom") or ""),
		"so_ra": flt(g(d, "so_ra")), "dvt_ra": str(g(d, "dvt_ra") or ""),
		"gia_ban_du_kien": flt(g(d, "gia_ban_du_kien")), "ghi_chu": str(g(d, "ghi_chu") or ""),
		"dong": [[g(r, "item_code") or None, str(g(r, "ten") or ""), str(g(r, "dvt") or ""),
			flt(g(r, "so_luong")), flt(g(r, "don_gia_tay"))] for r in (g(d, "dong") or [])],
	}


def quyet_luu_phieu(truoc, nay):
	"""Lưu phiếu thử thì làm gì. THUẦN. Codex #486 v2.

	`truoc`: None nếu phiếu mới, không thì {"da_bo", "noi_dung"} lúc đọc ra;
	`nay`: {"da_bo", "noi_dung"} sắp lưu. Trả "tinh" (tính lại ảnh chụp giá)
	hoặc "giu" (đang bỏ phiếu: giữ nguyên giá đã chụp để tra lại). Phiếu đã
	bỏ thì không sửa được nữa, kể cả từ Desk; bỏ phiếu không được kèm sửa
	nội dung. Sai thì ném ValueError bằng câu tiếng Việt."""
	if truoc and int(truoc.get("da_bo") or 0):
		raise ValueError("Phiếu này đã bỏ, không sửa được nữa. Bấm Phiếu tính giá thử mới để lập lại.")
	if int(nay.get("da_bo") or 0):
		if truoc is None:
			raise ValueError("Không lập phiếu mới ở trạng thái đã bỏ.")
		if truoc.get("noi_dung") != nay.get("noi_dung"):
			raise ValueError("Bỏ phiếu không kèm sửa nội dung. Lưu phần sửa trước, hoặc tải lại phiếu rồi mới bỏ.")
		return "giu"
	return "tinh"


def chuan_trang(tu_khoa, bat_dau):
	"""Tham số trang danh sách phiếu thử. THUẦN.

	Từ khoá bỏ khoảng trắng hai đầu, tối đa 80 ký tự (việc khớp chữ do
	tim_kiem lo). Vị trí bắt đầu là số nguyên >= 0, sai thì về 0."""
	tu = str(tu_khoa or "").strip()[:80]
	try:
		bd = int(bat_dau or 0)
	except (TypeError, ValueError):
		bd = 0
	return tu, max(bd, 0)


# Ba hàng chip của danh sách phiếu thử (Codex #486 v7, AGENTS.md 2b điều 3):
# trạng thái có đếm số, nhóm bán, khoảng ngày lập. Trạng thái tính theo giá
# HÔM NAY nên không lọc bằng SQL được: máy chủ tính cả tập (tối đa TOI_DA_THU
# phiếu mới sửa nhất) rồi lọc, đếm, chia trang trong python, để số trên chip
# luôn bằng số thẻ hiện ra và Xem thêm không trượt.
TOI_DA_THU = 500
CHUA_NHOM = "__chua_nhom"   # khoá chip "Chưa chọn nhóm"
KHOANG_THU = {"hom_nay": 0, "7_ngay": 6, "30_ngay": 29}   # số ngày lùi, tính cả hôm nay
TT_THU = ("vuot_gia_ban", "vong", "thieu_gia", "duoi_muc_tieu", "chua_dat_muc_tieu", "chua_gia_ban",
	"chua_nguyen_lieu", "dat")


def chuan_loc_thu(trang_thai, nhom, khoang, nhom_hop_le=NHOM_BAN):
	"""Bộ lọc chip của danh sách phiếu thử. THUẦN. Giá trị lạ về rỗng (tất cả)."""
	tt = str(trang_thai or "").strip()
	nh = str(nhom or "").strip()
	kh = str(khoang or "").strip()
	return (tt if tt in TT_THU else "", nh if (nh in nhom_hop_le or nh == CHUA_NHOM) else "",
		kh if kh in KHOANG_THU else "")


def moc_khoang(khoang, hom_nay):
	"""Ngày lập sớm nhất của khoảng, None là mọi ngày. THUẦN. `hom_nay` là date."""
	import datetime
	if khoang not in KHOANG_THU:
		return None
	return hom_nay - datetime.timedelta(days=KHOANG_THU[khoang])


def loc_trang_thu(ds, trang_thai="", nhom="", bat_dau=0, trang=TRANG_THU):
	"""Lọc theo chip, đếm chip, cắt trang. THUẦN. `ds` đã tính và xếp sẵn.

	Số trên chip trạng thái đếm trong nhóm đang chọn, số trên chip nhóm đếm
	trong trạng thái đang chọn: bấm chip nào cũng ra đúng số thẻ đã hiện."""
	def khop_nhom(p):
		return not nhom or (p.get("nhom") or CHUA_NHOM) == nhom

	def khop_tt(p):
		return not trang_thai or p.get("trang_thai") == trang_thai
	dem_tt, dem_nhom = {}, {}
	for p in ds:
		if khop_nhom(p):
			dem_tt[p.get("trang_thai")] = dem_tt.get(p.get("trang_thai"), 0) + 1
		if khop_tt(p):
			k = p.get("nhom") or CHUA_NHOM
			dem_nhom[k] = dem_nhom.get(k, 0) + 1
	hop = [p for p in ds if khop_nhom(p) and khop_tt(p)]
	bd = max(int(bat_dau or 0), 0)
	cat = hop[bd:bd + trang]
	return {"ds": cat, "dem_tt": dem_tt, "dem_nhom": dem_nhom, "so_hop": len(hop),
		"con_nua": bd + len(cat) < len(hop), "bat_dau_tiep": bd + len(cat)}


def tinh_phieu(phieu, gia_ma, he_so_nhom=None):
	"""Giá vốn của một phiếu thử bằng đúng nguồn giá của món đang bán. THUẦN.

	`gia_ma(ma)` -> {"gia", "nguon", "thieu", "vong"}: bán thành phẩm có công
	thức thì lấy giá cộng dồn, lá thì lấy giá kho / mặt hàng / bảng giá nhập.
	Giá nhập tay > 0 luôn thắng (NVL mới, hoặc mã đang thiếu giá). Dòng không
	mã mà không có giá tay là thiếu giá."""
	rows, tong, thieu, vong = [], 0.0, 0, False
	for d in phieu.get("dong") or []:
		if flt(d.get("don_gia_tay")) > 0:
			g = {"gia": flt(d["don_gia_tay"]), "nguon": NGUON_TAY, "thieu": 0, "vong": False}
		elif d.get("item_code"):
			g = gia_ma(d["item_code"])
		else:
			g = {"gia": 0.0, "nguon": NGUON_THIEU, "thieu": 1, "vong": False}
		tt = flt(g["gia"]) * flt(d.get("so_luong"))
		tong += tt
		if g.get("thieu"):
			thieu += 1
		vong = vong or bool(g.get("vong"))
		rows.append(dict(d, don_gia=flt(g["gia"]), nguon=g["nguon"], thieu=int(bool(g.get("thieu"))),
			thanh_tien=tt))
	so_ra = flt(phieu.get("so_ra")) or 1.0
	gv = round(tong / so_ra)
	muc = (he_so_nhom or {}).get(phieu.get("nhom"))
	gb = flt(phieu.get("gia_ban_du_kien"))
	if not rows:
		tt = "chua_nguyen_lieu"
	else:
		tt = trang_thai(True, vong, thieu, gv, gb, muc)
	return {
		"dong": rows, "tong_me": round(tong), "gia_von": gv, "thieu_so": thieu,
		"he_so_muc_tieu": muc,
		"gia_de_xuat": gia_de_xuat(gv, muc) if tt not in TRANG_THAI_BO_QUA and tt != "chua_nguyen_lieu" else None,
		"he_so": he_so_hien(gv, gb), "ty_le": ty_le_hien(gv, gb), "trang_thai": tt,
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
	he_so = {}
	for c in _theo_lo("UOM Conversion Detail", "parent", list(theo_ma), ["parent", "uom", "conversion_factor"],
			them={"parenttype": "Item"}):
		he_so.setdefault(c.parent, {})[c.uom] = flt(c.conversion_factor)
	ra = {}
	hom_nay = nowdate()
	for ma, dong in theo_ma.items():
		g = chon_gia_ap_dung(dong, dvt.get(ma), hom_nay, he_so.get(ma))
		if g is not None:
			ra[ma] = g
	return ra


def _he_so_da_luu():
	try:
		return json.loads(frappe.defaults.get_global_default(KHOA_HE_SO) or "{}") or {}
	except ValueError:
		return {}


def _bang_gia_ban():
	return frappe.db.get_single_value("Selling Settings", "selling_price_list") or BANG_GIA_BAN_MAC_DINH


def _doc(them_ma=()):
	"""Đọc một lượt mọi thứ cần cho cả màn. Không hỏi từng mã. `them_ma`: mã
	nguyên liệu của phiếu thử chưa nằm trong công thức nào, đọc giá cùng lô."""
	ds_bom = frappe.get_all("BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["name", "item", "quantity", "is_default"], limit_page_length=0)
	ma_bom = bom_cua_ma(ds_bom)
	mo_ho = ma_mo_ho(ds_bom)
	thanh_phan = {b.name: {"so_ra": flt(b.quantity), "dong": []} for b in ds_bom}
	for d in _theo_lo("BOM Item", "parent", thanh_phan.keys(),
			["parent", "item_code", "item_name", "qty", "stock_qty", "stock_uom", "uom", "bom_no"],
			them={"parenttype": "BOM"}, order_by="parent, idx"):
		thanh_phan[d.parent]["dong"].append({
			"ma": d.item_code, "ten": d.item_name, "dvt": d.stock_uom or d.uom,
			"sl": flt(d.stock_qty) or flt(d.qty), "bom_no": d.bom_no,
		})
	ma_nl = {d["ma"] for t in thanh_phan.values() for d in t["dong"]} | {m for m in them_ma if m}
	ton = {}
	for b in _theo_lo("Bin", "item_code", ma_nl, ["item_code", "actual_qty", "stock_value"]):
		ton.setdefault(b.item_code, []).append(b)
	mat_hang = {i.name: i for i in _theo_lo("Item", "name", ma_nl, ["name", "item_name", "stock_uom", "valuation_rate"])}
	gia_nhap = _gia_ap_dung(ma_nl, BANG_GIA_NHAP, {k: v.stock_uom for k, v in mat_hang.items()})

	def gia_la_cua(ma):
		# Mã có từ hai công thức chưa chọn mặc định: KHÔNG lấy giá kho thay,
		# ở bất kỳ tầng nào (Codex #486 v2, v3).
		if ma in mo_ho:
			return 0.0, NGUON_NHIEU_CT
		i = mat_hang.get(ma)
		return gia_la(ton.get(ma), i.valuation_rate if i else 0, gia_nhap.get(ma))

	ket = cong_don(thanh_phan, ma_bom, gia_la_cua)
	ten_nl = {k: v.item_name for k, v in mat_hang.items()}
	return thanh_phan, ma_bom, gia_la_cua, ket, ten_nl, mo_ho


def _bang():
	thanh_phan, ma_bom, gia_la_cua, ket, ten_nl, mo_ho = _doc()
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
	he_so = _he_so_da_luu()
	return dung_bang(ban, ma_bom, ket, gia_ban, chot_truoc, he_so, ten_nl, mo_ho), he_so


@frappe.whitelist()
def tinh():
	"""Dữ liệu cả màn Giá vốn tạm tính. Chỉ đọc."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	bang, he_so = _bang()
	bang.update({
		"he_so": he_so, "cap_nhat_luc": now_datetime().strftime("%H:%M"),
		"sua_duoc": bool(QUYEN_CHOT & set(frappe.get_roles())), "ngay": nowdate(),
	})
	return bang


@frappe.whitelist()
def chi_tiet(ma, bom=None):
	"""Các dòng nguyên liệu một tầng của một món (hoặc của một công thức con
	khi bấm xuống bán thành phẩm). Chỉ đọc."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	thanh_phan, ma_bom, gia_la_cua, ket, _ten, mo_ho = _doc()
	bom = bom or ma_bom.get(ma)
	if not bom and ma in mo_ho:
		frappe.throw("Món này có %d công thức đang dùng nhưng chưa chọn công thức mặc định. "
			"Mở công thức đúng trên Desk, tích Mặc định rồi tính lại." % len(mo_ho[ma]))
	if not bom or bom not in thanh_phan:
		frappe.throw("Món này chưa có công thức đang dùng.")
	k = ket.get(bom) or {}
	return {
		"ma": ma, "ten": frappe.db.get_value("Item", ma, "item_name") or ma, "bom": bom,
		"so_ra": flt(thanh_phan[bom]["so_ra"]), "gia": flt(k.get("gia")), "vong": bool(k.get("vong")),
		"dong": dong_chi_tiet(bom, thanh_phan, ma_bom, gia_la_cua, ket),
	}


@frappe.whitelist()
def luu_he_so(he_so):
	"""Lưu hệ số giá bán mục tiêu theo nhóm. Không đụng doctype nào."""
	_kiem(QUYEN_CHOT, "đặt hệ số mục tiêu")
	try:
		sach = chuan_he_so(he_so)
	except ValueError as e:
		frappe.throw(str(e))
	frappe.defaults.set_global_default(KHOA_HE_SO, json.dumps(sach, ensure_ascii=False))
	return {"he_so": sach}


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
	bang, _he_so = _bang()
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


# ------------------------------------------------ phiếu tính giá thử (R&D)


def _bo_gia_ma(cac_ma):
	"""Một lượt đọc -> hàm gia_ma(ma) cho tinh_phieu, kèm tên và đơn vị kho."""
	thanh_phan, ma_bom, gia_la_cua, ket, _ten, _mo = _doc(them_ma=cac_ma)
	mat_hang = {i.name: i for i in _theo_lo("Item", "name", [m for m in cac_ma if m], ["name", "item_name", "stock_uom"])}

	def gia_ma(ma):
		bom = ma_bom.get(ma)
		if bom and bom in ket:
			k = ket[bom]
			return {"gia": flt(k["gia"]), "nguon": NGUON_CONG_THUC, "thieu": len(k["thieu"]), "vong": k["vong"]}
		if ma not in mat_hang:
			return {"gia": 0.0, "nguon": NGUON_THIEU, "thieu": 1, "vong": False}
		g, nguon = gia_la_cua(ma)
		return {"gia": g, "nguon": nguon, "thieu": int(nguon in NGUON_LA_THIEU), "vong": False}
	return gia_ma, mat_hang


def _tinh_cac_phieu(cac_phieu):
	ma = {d["item_code"] for p in cac_phieu for d in p["dong"] if d.get("item_code")}
	gia_ma, mat_hang = _bo_gia_ma(ma)
	he_so = _he_so_da_luu()
	ra = []
	for p in cac_phieu:
		for d in p["dong"]:
			i = mat_hang.get(d.get("item_code"))
			if i:
				d["ten"] = i.item_name
				d["dvt"] = i.stock_uom
		ra.append(dict(p, **tinh_phieu(p, gia_ma, he_so)))
	return ra, he_so


def _doc_phieu(ten):
	d = frappe.get_doc(DT_THU, ten)
	return {
		"name": d.name, "ten_mon": d.ten_mon, "nhom": d.nhom or "", "so_ra": flt(d.so_ra) or 1.0,
		"dvt_ra": d.dvt_ra or "Cái", "gia_ban_du_kien": flt(d.gia_ban_du_kien), "ghi_chu": d.ghi_chu or "",
		"cap_nhat": str(d.modified)[:16], "nguoi": d.owner,
		"dong": [{"item_code": r.item_code or None, "ten": r.ten or "", "dvt": r.dvt or "",
			"so_luong": flt(r.so_luong), "don_gia_tay": flt(r.don_gia_tay)} for r in d.dong],
	}


def _nhom_ban():
	return [{"ten": n, "nhan": nhan_nhom(n)} for n in NHOM_BAN]


@frappe.whitelist()
def ds_thu(tu_khoa="", bat_dau=0, trang_thai="", nhom="", khoang=""):
	"""Danh sách phiếu tính giá thử chưa bỏ, mỗi trang TRANG_THU phiếu, tìm
	theo tên ở máy chủ, lọc theo ba hàng chip. Tính lại theo giá hôm nay.
	Chỉ đọc.

	Codex #486: bản đầu cắt cứng 200 phiếu mà màn không có cách xem phần còn
	lại. Giờ trả `con_nua` và `bat_dau_tiep` để màn nạp tiếp. Codex #486 v7:
	lọc trạng thái, nhóm, khoảng ngày lập và đếm chip ở máy chủ
	(loc_trang_thu), trả lại bộ lọc đã dùng để Xem thêm đi đúng bộ lọc đó."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	tu, bd = chuan_trang(tu_khoa, bat_dau)
	tt, nh, kh = chuan_loc_thu(trang_thai, nhom, khoang)
	loc = [["da_bo", "=", 0]]
	moc = moc_khoang(kh, getdate(nowdate()))
	if moc:
		loc.append(["creation", ">=", str(moc)])
	# Ô tìm đi qua MỘT nguồn tim_kiem (v583): gõ có dấu, không dấu, đảo thứ tự
	# chữ đều ra. Không tự viết like.
	loc = tim_kiem.them_loc(loc, DT_THU, tu, ["name", "ten_mon"])
	ten = [r.name for r in frappe.get_all(DT_THU, filters=loc, fields=["name"], order_by="modified desc",
		limit_page_length=TOI_DA_THU + 1)]
	vuot = len(ten) > TOI_DA_THU
	tat, he_so = _tinh_cac_phieu([_doc_phieu(t) for t in ten[:TOI_DA_THU]])
	ra = loc_trang_thu(tat, tt, nh, bd)
	ra.update({"he_so": he_so, "nhom_ban": _nhom_ban(), "tu_khoa": tu, "bat_dau": bd,
		"trang_thai": tt, "nhom": nh, "khoang": kh, "tong": len(tat), "vuot": vuot,
		"sua_duoc": bool(QUYEN_CHOT & set(frappe.get_roles()))})
	return ra


@frappe.whitelist()
def tinh_thu(phieu):
	"""Tính thử một phiếu chưa lưu (màn nhập gọi mỗi lần đổi). Chỉ đọc."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	try:
		p = chuan_phieu(phieu)
	except ValueError as e:
		frappe.throw(str(e))
	return _tinh_cac_phieu([p])[0][0]


def kiem_khi_luu(d):
	"""Gọi từ validate() của Vagabond Gia Thu: chặn sửa phiếu đã bỏ, bỏ
	phiếu thì giữ nguyên ảnh chụp, còn lại tính lại (tinh_lai_doc)."""
	cu = None if d.is_new() else d.get_doc_before_save()
	truoc = None if cu is None else {"da_bo": cu.get("da_bo"), "noi_dung": noi_dung_phieu(cu)}
	try:
		viec = quyet_luu_phieu(truoc, {"da_bo": d.get("da_bo"), "noi_dung": noi_dung_phieu(d)})
	except ValueError as e:
		frappe.throw(str(e))
	if viec == "tinh":
		return tinh_lai_doc(d)
	return None


def tinh_lai_doc(d):
	"""MỘT nguồn tính cho phiếu thử khi lưu, gọi từ validate() của doctype.

	Lưu qua app (luu_thu) hay sửa thẳng trên Desk đều đi qua đây, nên giá vốn
	và giá đề xuất lưu kèm không bao giờ là số cũ (Codex #486 P2). Dòng có mã
	lấy lại tên và đơn vị kho từ mặt hàng. Kết quả đầy đủ để ở
	`d.flags.kq_gia_thu` cho luu_thu trả về màn."""
	vao = {k: d.get(k) for k in ("ten_mon", "nhom", "so_ra", "dvt_ra", "gia_ban_du_kien", "ghi_chu")}
	vao["dong"] = [{"item_code": r.get("item_code"), "ten": r.get("ten"), "dvt": r.get("dvt"),
		"so_luong": r.get("so_luong"), "don_gia_tay": r.get("don_gia_tay")} for r in (d.get("dong") or [])]
	try:
		p = chuan_phieu(vao)
	except ValueError as e:
		frappe.throw(str(e))
	kq = _tinh_cac_phieu([p])[0][0]
	for r, k in zip(d.get("dong") or [], kq["dong"]):
		if r.get("item_code"):
			r.ten = k.get("ten")
			r.dvt = k.get("dvt")
	d.gia_von = kq["gia_von"]
	d.gia_de_xuat = kq["gia_de_xuat"] or 0
	d.flags.kq_gia_thu = kq
	return kq


@frappe.whitelist(methods=["POST"])
def luu_thu(phieu):
	"""Lưu phiếu tính giá thử. Chỉ ghi vào Vagabond Gia Thu, không đụng Item,
	BOM, kho hay sổ sách. Giá vốn lưu kèm chỉ là ảnh chụp lúc lưu, do
	validate() tính lại (tinh_lai_doc), không nhận số từ máy khách."""
	_kiem(QUYEN_CHOT, "lập phiếu tính giá thử")
	try:
		p = chuan_phieu(phieu)
	except ValueError as e:
		frappe.throw(str(e))
	if p["name"]:
		if not frappe.db.exists(DT_THU, p["name"]):
			frappe.throw("Không tìm thấy phiếu %s." % p["name"])
		d = frappe.get_doc(DT_THU, p["name"])
		d.set("dong", [])
	else:
		d = frappe.new_doc(DT_THU)
	for k in ("ten_mon", "nhom", "so_ra", "dvt_ra", "gia_ban_du_kien", "ghi_chu"):
		d.set(k, p[k])
	for r in p["dong"]:
		d.append("dong", {"item_code": r.get("item_code"), "ten": r.get("ten"), "dvt": r.get("dvt"),
			"so_luong": r["so_luong"], "don_gia_tay": r["don_gia_tay"]})
	d.flags.ignore_permissions = True
	d.save() if p["name"] else d.insert()
	kq = dict(d.flags.kq_gia_thu)
	kq["name"] = d.name
	return kq


@frappe.whitelist(methods=["POST"])
def bo_thu(name):
	"""Bỏ một phiếu thử: ẩn khỏi danh sách, KHÔNG xoá (QT-20, Codex #486 P1).
	Giữ nguyên dòng nguyên liệu và giá lúc lưu để tra lại, ghi ai bỏ lúc nào.
	validate() thấy đang bỏ nên không tính lại giá (Codex #486 v2)."""
	_kiem(QUYEN_CHOT, "bỏ phiếu tính giá thử")
	if not frappe.db.exists(DT_THU, name):
		frappe.throw("Không tìm thấy phiếu %s." % name)
	d = frappe.get_doc(DT_THU, name)
	if not d.get("da_bo"):
		d.da_bo = 1
		d.bo_luc = now_datetime()
		d.bo_boi = frappe.session.user
		d.flags.ignore_permissions = True
		d.save()
	return {"ok": 1}


@frappe.whitelist()
def tim_nl(tu_khoa):
	"""Tìm nguyên liệu, bán thành phẩm để thêm vào phiếu thử (trừ bánh bán ra)."""
	_kiem(QUYEN_XEM, "xem giá vốn tạm tính")
	tu = str(tu_khoa or "").strip()[:80]
	if len(tu) < 2:
		return []
	# Một nguồn tìm tim_kiem (v583), không tự viết like.
	loc = tim_kiem.them_loc({"disabled": 0, "item_group": ["not in", list(NHOM_BAN)]}, "Item", tu, ["name", "item_name"])
	ds = frappe.get_all("Item", filters=loc,
		fields=["name", "item_name", "stock_uom", "item_group"], order_by="item_name asc", limit_page_length=20)
	return [{"ma": i.name, "ten": i.item_name, "dvt": i.stock_uom, "nhom": i.item_group} for i in ds]


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
