# -*- coding: utf-8 -*-
"""Tai cau truc BOM va Item cua Bep, chay MOT LAN co kiem soat.

Bai anh Viet giao 20/08/2026, ba viec:

1. GIOI HAN "PHANTOM": chi cac ma BTP thuoc chang "BTP thành phần" duoc
   danh dau Lam tuoi (custom_lam_tuoi=1). Cac cap cao hon (Ruot banh C1,
   Banh khuon C2, Thanh pham) giu nguyen theo doi ton kho.

   VI SAO KHONG TAT is_stock_item NGAY: hai buc tuong that.
   - ERPNext CHAN doi is_stock_item khi ma hang da co but toan kho (SLE).
     Phan lon 140 ma BTP deu da co.
   - Luong "lam tuoi" cua app (05-san-xuat.js, mfgFreshPlan) tao Work
     Order con cho BTP thieu, ma Work Order doi production_item PHAI la
     stock item. Tat ton kho la luong san xuat dang chay gay ngay.
   Muon phantom that thi phai doi ca cach app no dinh muc (multi-level
   BOM), do la mot quyet dinh rieng cua anh Viet, khong phai viec mot
   kich ban don du lieu tu quyet. Che do "phantom" van co o day nhung
   phai goi ro rang, va bao cao tung ma bi ERPNext chan.

2. BO CHANG "So che": hai BOM so che (long trang, long do) ngung hoat
   dong, va xoa lua chon "Sơ chế" khoi truong phan chang tren BOM.

3. GOP NVL TRUNG: moi dong long do / long trang trong cac cong thuc thay
   bang Trung ga tuoi (NVLT00041) tinh theo Gram:
     long do  x 1.0      (BOM so che cu: 25g long do tu 25g trung)
     long trang x 32/30  (BOM so che cu: 30g long trang tu 32g trung)
   BOM da ghi so khong sua tai cho duoc, nen moi BOM dinh trung duoc tao
   BAN MOI (sao chep, thay dong, ghi so, dat lam mac dinh) va ban cu
   ngung hoat dong - dung duong chinh thong cua ERPNext, giu nguyen vet.

   KHONG DUNG VAO NVLT00042 (long do trung MUOI, Ami): do la hang MUA,
   khong phai trung tuoi tach ra.

Moi viec co xem_truoc (chi doc, tra ke hoach) va thuc_hien (ghi that).
Chi System Manager va Giam doc duoc chay, va nen chay ngoai gio ban hang.
"""

# ------------------------------------------------------------ phan thuan

CHANG_BTP = "BTP thành phần"
CHANG_SO_CHE = "Sơ chế"

# Ma trung: (ma long do), (ma long trang) - ca ma BTP moi lan ma cu.
MA_LONG_DO = ("BTPB00046", "5HVQDZAMZGB6")
MA_LONG_TRANG = ("BTPB00045", "8LGXD8J8TTA6")
MA_TRUNG_TUOI = "NVLT00041"
# Long do trung MUOI cua Ami la hang mua, khong lien quan trung tuoi.
MA_CAM = "NVLT00042"

# He so quy doi ra gram trung tuoi, doc tu chinh hai BOM so che dang chay:
# 25g long do can 25g trung (1.0), 30g long trang can 32g trung (32/30).
HE_SO_LONG_DO = 1.0
HE_SO_LONG_TRANG = 32.0 / 30.0


def he_so_cua(ma):
	"""He so doi mot gram long do/long trang ra gram trung tuoi."""
	if ma in MA_LONG_DO:
		return HE_SO_LONG_DO
	if ma in MA_LONG_TRANG:
		return HE_SO_LONG_TRANG
	return 0.0


def gop_dong_trung(cac_dong):
	"""Tinh tong gram trung tuoi tu cac dong long do/long trang cua MOT bom.

	cac_dong: [(ma, so_gram)]. Tra ve (tong_gram_trung, [ghi chu tung dong]).
	Lam tron 2 chu so cho khop kieu so luong tren BOM.
	"""
	tong = 0.0
	ghi = []
	for ma, gram in cac_dong:
		hs = he_so_cua(ma)
		if not hs:
			continue
		them = round(float(gram or 0) * hs, 2)
		tong = round(tong + them, 2)
		ghi.append("%s %sg x %.4f = %sg trung" % (ma, gram, hs, them))
	return tong, ghi


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import cint, flt

MA_TRUNG_HET = tuple(MA_LONG_DO) + tuple(MA_LONG_TRANG)


def _chan():
	if not {"System Manager", "Giám đốc", "AP Giám đốc"} & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý hệ thống hoặc giám đốc mới chạy tái cấu trúc BOM. "
			"Đây là thao tác đổi công thức hàng loạt."
		)


def _bom_chang(chang):
	"""BOM dang hoat dong cua mot chang."""
	return frappe.get_all(
		"BOM",
		filters={"docstatus": 1, "is_active": 1, "custom_chang": chang},
		fields=["name", "item", "item_name", "is_default", "quantity", "uom"],
		limit_page_length=0,
	)


def _co_sle(ma):
	return bool(frappe.db.exists("Stock Ledger Entry", {"item_code": ma, "is_cancelled": 0}))


# ------------------------------------------------ muc 1: danh dau lam tuoi


@frappe.whitelist()
def lam_tuoi_xem_truoc():
	"""Ke hoach muc 1: nhung ma BTP thanh phan se duoc danh dau Lam tuoi."""
	_chan()
	ra, da = [], set()
	for b in _bom_chang(CHANG_BTP):
		if b.item in da:
			continue
		da.add(b.item)
		it = frappe.db.get_value(
			"Item", b.item,
			["item_name", "is_stock_item", "custom_lam_tuoi", "disabled"],
			as_dict=True,
		) or {}
		ra.append({
			"ma": b.item, "ten": it.get("item_name") or b.item_name,
			"bom": b.name,
			"dang_lam_tuoi": cint(it.get("custom_lam_tuoi")),
			"dang_theo_ton": cint(it.get("is_stock_item")),
			"co_but_toan_kho": 1 if _co_sle(b.item) else 0,
		})
	return {
		"tong": len(ra),
		"se_danh_dau": len([x for x in ra if not x["dang_lam_tuoi"]]),
		"ds": sorted(ra, key=lambda x: x["ma"]),
	}


@frappe.whitelist()
def lam_tuoi_thuc_hien(che_do="lam_tuoi"):
	"""Muc 1 ghi that.

	che_do="lam_tuoi": chi bat custom_lam_tuoi=1 (mac dinh, an toan).
	che_do="phantom": bat lam tuoi VA thu tat is_stock_item tung ma qua
	duong validate cua ERPNext; ma nao bi chan (da co but toan kho) thi
	giu nguyen va ghi vao bao cao. CHI goi che do nay khi anh Viet da
	quyet, vi no dung cham luong san xuat lam tuoi dang chay.
	"""
	_chan()
	ke = lam_tuoi_xem_truoc()
	da_danh_dau, da_phantom, bi_chan = [], [], []
	for x in ke["ds"]:
		if not x["dang_lam_tuoi"]:
			frappe.db.set_value("Item", x["ma"], "custom_lam_tuoi", 1)
			da_danh_dau.append(x["ma"])
		if che_do == "phantom" and x["dang_theo_ton"]:
			try:
				it = frappe.get_doc("Item", x["ma"])
				it.is_stock_item = 0
				it.save(ignore_permissions=True)
				da_phantom.append(x["ma"])
			except Exception as e:
				bi_chan.append({"ma": x["ma"], "vi_sao": str(e)[:180]})
	frappe.db.commit()
	return {
		"ok": 1, "che_do": che_do,
		"da_danh_dau": da_danh_dau, "so_danh_dau": len(da_danh_dau),
		"da_phantom": da_phantom, "bi_chan": bi_chan,
		"tong_ma": ke["tong"],
	}


# --------------------------------------------------- muc 2: bo chang So che


@frappe.whitelist()
def so_che_xem_truoc():
	"""Ke hoach muc 2: BOM so che se ngung va lua chon se xoa."""
	_chan()
	return {
		"bom_ngung": _bom_chang(CHANG_SO_CHE),
		"xoa_lua_chon": CHANG_SO_CHE,
	}


@frappe.whitelist()
def so_che_thuc_hien():
	"""Muc 2 ghi that: ngung BOM so che, xoa lua chon "Sơ chế" khoi chang."""
	_chan()
	da_ngung = []
	for b in _bom_chang(CHANG_SO_CHE):
		frappe.db.set_value("BOM", b.name, {
			"is_active": 0, "is_default": 0, "custom_chang": "",
		})
		da_ngung.append(b.name)
	# Xoa lua chon khoi truong phan chang (Custom Field khai tren site).
	sua_truong = 0
	cf = frappe.db.get_value(
		"Custom Field", {"dt": "BOM", "fieldname": "custom_chang"},
		["name", "options"], as_dict=True,
	)
	if cf and cf.options:
		dong = [d for d in str(cf.options).split("\n") if d.strip() != CHANG_SO_CHE]
		if len(dong) != len(str(cf.options).split("\n")):
			frappe.db.set_value("Custom Field", cf.name, "options", "\n".join(dong))
			sua_truong = 1
			frappe.clear_cache(doctype="BOM")
	frappe.db.commit()
	return {"ok": 1, "da_ngung": da_ngung, "da_xoa_lua_chon": sua_truong}


# ------------------------------------------------------ muc 3: gop NVL trung


def _bom_dinh_trung():
	"""Cac BOM dang hoat dong co dong long do / long trang."""
	rows = frappe.db.sql(
		"""select distinct bi.parent from `tabBOM Item` bi
		join `tabBOM` b on b.name = bi.parent
		where bi.item_code in %(ma)s and b.docstatus = 1 and b.is_active = 1""",
		{"ma": MA_TRUNG_HET},
		as_dict=True,
	)
	return sorted(r.parent for r in rows)


def _ke_hoach_mot_bom(ten_bom):
	"""Doc mot BOM, tinh dong trung cu se bo va dong trung tuoi se them."""
	b = frappe.get_doc("BOM", ten_bom)
	dong_cu, giu_nguyen = [], []
	gram_trung_co_san = 0.0
	for it in (b.items or []):
		if it.item_code in MA_TRUNG_HET:
			# stock_qty la so luong theo don vi goc (Gram voi cac ma nay),
			# khong phu thuoc dong do khai theo don vi nao.
			dong_cu.append((it.item_code, flt(it.stock_qty) or flt(it.qty)))
		else:
			if it.item_code == MA_TRUNG_TUOI:
				gram_trung_co_san += flt(it.stock_qty)
			giu_nguyen.append(it.item_code)
	tong_gram, ghi = gop_dong_trung(dong_cu)
	return {
		"bom": ten_bom, "mon": b.item, "ten_mon": b.item_name,
		"chang": b.get("custom_chang") or "",
		"dong_bo": [{"ma": m, "gram": g} for m, g in dong_cu],
		"gram_trung_them": tong_gram,
		"gram_trung_co_san": gram_trung_co_san,
		"cach_tinh": ghi,
	}


@frappe.whitelist()
def trung_xem_truoc():
	"""Ke hoach muc 3, tung BOM mot: bo dong nao, them bao nhieu gram trung."""
	_chan()
	return {
		"he_so": {"long_do": HE_SO_LONG_DO, "long_trang": round(HE_SO_LONG_TRANG, 4)},
		"ds": [_ke_hoach_mot_bom(t) for t in _bom_dinh_trung()],
	}


def _he_so_gram():
	"""He so doi 1 Gram ra don vi goc (PCS) cua NVLT00041, neu co khai."""
	try:
		from erpnext.stock.get_item_details import get_conversion_factor

		return flt(get_conversion_factor(MA_TRUNG_TUOI, "Gram").get("conversion_factor")) or 0.0
	except Exception:
		return 0.0


def _thay_mot_bom(ten_bom):
	"""Tao BAN MOI cua mot BOM voi dong trung da gop. Tra ve ten ban moi.

	BOM da ghi so khong sua tai cho duoc; sao chep la duong chinh thong:
	ban moi mang du lich su nguoi doi, ban cu ngung hoat dong nhung van
	nam nguyen trong so de doi chieu.
	"""
	ke = _ke_hoach_mot_bom(ten_bom)
	if not ke["dong_bo"]:
		return {"bom": ten_bom, "bo_qua": 1}
	cu = frappe.get_doc("BOM", ten_bom)
	moi = frappe.copy_doc(cu)
	moi.set("items", [r for r in moi.items if r.item_code not in MA_TRUNG_HET])

	tong_gram = flt(ke["gram_trung_them"])
	# Da co san dong trung tuoi thi cong don vao dong do, khong de hai dong
	# cung mot ma trong mot cong thuc.
	dong_trung = None
	for r in moi.items:
		if r.item_code == MA_TRUNG_TUOI:
			dong_trung = r
			break
	cf = _he_so_gram()
	if dong_trung:
		if (dong_trung.uom or "").lower() == "gram":
			dong_trung.qty = flt(dong_trung.qty) + tong_gram
		else:
			# Dong cu khai theo don vi khac (PCS): cong theo stock_qty.
			dong_trung.qty = flt(dong_trung.qty) + (tong_gram * cf if cf else tong_gram)
	else:
		moi.append("items", {
			"item_code": MA_TRUNG_TUOI,
			"uom": "Gram",
			"qty": tong_gram,
			"conversion_factor": cf or 1.0,
		})
	moi.flags.ignore_permissions = True
	moi.insert(ignore_permissions=True)
	moi.submit()
	# Ban moi ke thua vi tri cua ban cu.
	frappe.db.set_value("BOM", moi.name, {
		"is_active": 1, "is_default": cint(cu.is_default),
	})
	frappe.db.set_value("BOM", ten_bom, {"is_active": 0, "is_default": 0})
	if cint(cu.is_default):
		frappe.db.set_value("Item", cu.item, "default_bom", moi.name)
	return {"bom": ten_bom, "bom_moi": moi.name, "gram_trung": tong_gram}


@frappe.whitelist()
def trung_thuc_hien():
	"""Muc 3 ghi that, tung BOM boc rieng de mot cong thuc hong khong do ca lo."""
	_chan()
	xong, loi = [], []
	for t in _bom_dinh_trung():
		try:
			xong.append(_thay_mot_bom(t))
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			loi.append({"bom": t, "vi_sao": str(e)[:200]})
			frappe.log_error(frappe.get_traceback(), "don_bep: thay trung o " + t)

	# Chi khi KHONG con BOM hoat dong nao dinh trung nua moi tat cac ma
	# long do / long trang, de khong chan nham mot cong thuc con dung.
	da_tat = []
	if not _bom_dinh_trung():
		for ma in MA_TRUNG_HET:
			if frappe.db.exists("Item", ma) and not cint(
				frappe.db.get_value("Item", ma, "disabled")
			):
				frappe.db.set_value("Item", ma, "disabled", 1)
				da_tat.append(ma)
		frappe.db.commit()
	return {"ok": 1, "xong": xong, "loi": loi, "da_tat_ma": da_tat}
