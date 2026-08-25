# -*- coding: utf-8 -*-
"""Doi don vi tinh cua mot mat hang trong TOAN BO cong thuc, khong doi gia von.

Viec anh Viet giao 25/08/2026
-----------------------------
*"Ben Khai can chuyen toan bo don vi tinh cua TRUNG trong BOM thanh Qua chu
khong de gram. Cung khong tinh he so cho long trang long do gi het."*


Hien trang do duoc tren site that
=================================
Quet 310 cong thuc con song (bo 67 ban da huy):

    95 dong co trung, tat ca deu la ma NVLT00041 Trung ga tuoi
    94 dong dang ghi Gram, 1 dong da la don vi dem
    Hai ma "Long do trung" va "Long trang trung" DA TAT tu truoc, khong
    cong thuc nao con dung. Nen phan "khong tinh he so long trang long do"
    thuc te da xong roi, khong phai lam gi them.

Mat hang trung tinh ton kho bang PCS, va da khai san quy doi Gram = 1/60.
Nghia la BOM ghi Gram moi la cai le loi, con kho va mua hang von da dem
bang qua. Doi BOM sang Qua la keo BOM ve dung voi kho.

Don vi "Qua" DA CO san trong he (203 don vi). Khong dat lai ten "PCS"
thanh "Qua" duoc: 38 mat hang khac dang dung PCS, va doi don vi kho cua
mot mat hang da co phat sinh kho thi ERPNext chan thang. Nen cach lam la
de kho giu PCS, con dong BOM ghi Qua voi he so 1.


Vi sao doi duoc ma khong lam lech mot dong nao
==============================================
ERPNext giu hai con so ma so sach dua vao tren moi dong BOM:

    stock_qty = qty * conversion_factor      (luong that, theo don vi kho)
    amount    = qty * rate                    (thanh tien)

Doi don vi la doi CACH VIET cua cung mot luong. Doi dong thoi ca bon con
so theo dung ty le thi hai con so tren khong nhuc nhich:

    qty_moi   = stock_qty_cu          (vi he so moi = 1)
    he_so_moi = 1
    rate_moi  = rate_cu / he_so_cu

Vi du that, dong trung cua BTP White Sponge:

    truoc:  8,3333 Gram * he so 0,016667 = 0,1389 PCS,    36,40 d/gram
    sau:    0,1389 Qua  * he so 1        = 0,1389 PCS,  2.184 d/qua

Mot cho tinh te: lay `stock_qty` lam so luong moi la CO Y, vi do la con so
ERPNext da chot va no phai khong doi. Doi lai, 0,1389 la ban da lam tron
cua 0,13888889, nen nhan lai voi don gia se lech vai xu so voi thanh tien
cu. Cho nen `doi_het` BE NGUYEN `amount` cu sang chu khong tinh lai: sai
so lam tron dung lai o day, khong troi sang so sach.


MOT PHAT HIEN PHAI BAO TRUOC KHI DOI
====================================
Sau cong thuc dang ghi SO QUA vao o gram, hut dung sau muoi lan. Doc chi
tiet o ham `soi_ghi_nham`.

Doi don vi KHONG sua duoc loi do, vi doi don vi la phep giu nguyen luong.
Te hon: doi xong thi con so sai se khoac ao "Qua" nhin rat that, cang kho
phat hien hon.

Nen `doi_het` CHAN san khi con cong thuc nghi ghi nham chua xu ly.

Anh Viet chot 25/08/2026: ban Khai vao sua tay sau cong thuc do trong
ERP, roi moi doi don vi. GIU NGUYEN cai chan nay chu khong go: khi Khai
sua xong thi phep soi tu tra ve rong va cai chan tu mo. No khong phai
hang rao can duong, no la cach may TU BIET Khai da sua xong hay chua.


Cach chay
=========
Mac dinh `chay_that=0`, chi tra ve ke hoach chu khong ghi gi. Doc ky roi
moi chay that. Giong cach `don_du_lieu.py` lam.
"""

# ------------------------------------------------------------ phan thuan

# Mat hang trung. De thanh danh sach vi sau nay co the them trung vit,
# trung cut, ma phep doi thi y het nhau.
MA_TRUNG = ("NVLT00041",)

# Don vi muon thay bang. Da co san trong he.
DVT_DICH = "Quả"

# Mot qua trung nang bao nhieu gram. Chi dung de SOI, khong dung de doi:
# phep doi lay he so that tren tung dong chu khong lay con so nay.
GRAM_MOI_QUA = 60.0


def doi_mot_dong(qty, he_so, rate, stock_qty=None):
	"""Doi mot dong BOM sang don vi kho. THUAN.

	Tra ve (qty_moi, he_so_moi, rate_moi). Ba con so nay thay vao dong cu
	thi `stock_qty` giu nguyen tuyet doi.

	`stock_qty` truyen vao de lay lam chuan neu co: con so do la cai
	ERPNext da chot, tin no hon la nhan lai qty voi he so roi sinh sai so
	lam tron.
	"""
	qty = float(qty or 0)
	he_so = float(he_so or 1)
	rate = float(rate or 0)
	if he_so <= 0:
		return (qty, 1.0, rate)
	moi = float(stock_qty) if stock_qty not in (None, "") else qty * he_so
	return (moi, 1.0, rate / he_so)


def can_doi(uom, stock_uom):
	"""Dong nay co can doi khong. THUAN.

	Da dung don vi kho roi thi thoi, dung dong vao. Doi mot dong dang dung
	cho sang cung mot thu la sinh mot ban ghi thay doi vo nghia trong lich
	su, ma lich su BOM la thu ke toan gia thanh se doc lai.
	"""
	uom = str(uom or "").strip()
	stock_uom = str(stock_uom or "").strip()
	return bool(uom) and bool(stock_uom) and uom != stock_uom


def nghi_ghi_nham(me, tong_dong_khac, qty_trung, gram_moi_qua=None):
	"""Dong trung nay co ve la ghi SO QUA vao o gram khong. THUAN.

	Phep soi: cong het cac dong khac lai, thieu bao nhieu gram thi so do
	phai la phan cua trung. Neu con so dang ghi nhan voi 60 mem vao dung
	cho thieu, con de nguyen thi hut mot khoang lon, thi gan nhu chac chan
	nguoi nhap go so QUA vao o GRAM.

	Tra ve (co_nghi, gram_dang_thieu, gram_neu_hieu_la_qua).

	Nguong: sai so cho phep 5 gram hoac 2 phan tram me, lay cai lon hon.
	Cong thuc bep hay lam tron nen doi khop tuyet doi la khong thuc te.
	"""
	gram_moi_qua = float(gram_moi_qua or GRAM_MOI_QUA)
	me = float(me or 0)
	tong_dong_khac = float(tong_dong_khac or 0)
	qty_trung = float(qty_trung or 0)
	thieu = me - tong_dong_khac - qty_trung
	nhu_qua = qty_trung * gram_moi_qua
	sai_so = max(5.0, me * 0.02)
	lech_neu_gram = abs(me - tong_dong_khac - qty_trung)
	lech_neu_qua = abs(me - tong_dong_khac - nhu_qua)
	co_nghi = (lech_neu_qua + 1.0) < lech_neu_gram and lech_neu_gram > sai_so
	return (co_nghi, thieu, nhu_qua)


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import flt

DVT_KHOI_LUONG = ("Gram", "ML")


def _vai():
	quyen = {"System Manager", "Manufacturing Manager", "Giám đốc", "AP Giám đốc"}
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Chỉ bếp trưởng hoặc giám đốc mới đổi được đơn vị hàng loạt.")


def _bom_con_song():
	return frappe.get_all(
		"BOM",
		filters={"docstatus": ["<", 2]},
		fields=["name", "item", "item_name", "quantity", "uom", "is_active", "is_default"],
		order_by="name asc",
		limit_page_length=0,
	)


def _dong(bom):
	return frappe.get_all(
		"BOM Item",
		filters={"parent": bom},
		fields=["name", "item_code", "item_name", "qty", "uom", "conversion_factor",
				"stock_qty", "stock_uom", "rate", "amount", "idx"],
		order_by="idx asc",
		limit_page_length=0,
	)


def _ma(ma_trung):
	if isinstance(ma_trung, str) and ma_trung.strip():
		return tuple(x.strip() for x in ma_trung.split(",") if x.strip())
	return MA_TRUNG


@frappe.whitelist()
def soi_ghi_nham(ma_trung=None):
	"""Liet ke cac cong thuc co ve ghi SO QUA vao o gram. CHI DOC.

	Theo dieu 11 khong tu sua du lieu cu, chi liet ke ra cho anh Viet.
	Ham nay khong ghi mot chu nao.
	"""
	_vai()
	ma_trung = _ma(ma_trung)
	ra = []
	for b in _bom_con_song():
		if b.uom not in DVT_KHOI_LUONG:
			continue
		ds = _dong(b.name)
		trung = [d for d in ds if d.item_code in ma_trung]
		if not trung:
			continue
		khac = sum(
			flt(d.stock_qty) for d in ds
			if d.item_code not in ma_trung and d.stock_uom in DVT_KHOI_LUONG
		)
		for t in trung:
			if t.uom != "Gram":
				continue
			co_nghi, thieu, nhu_qua = nghi_ghi_nham(b.quantity, khac, t.qty)
			if not co_nghi:
				continue
			ra.append({
				"bom": b.name, "mon": b.item_name, "me": flt(b.quantity), "dvt_me": b.uom,
				"dang_ghi": flt(t.qty), "tong_dong_khac": round(khac, 2),
				"gram_dang_thieu": round(thieu, 2), "neu_hieu_la_qua": round(nhu_qua, 2),
				"dang_dung_may_qua": flt(t.stock_qty),
			})
	return {"so_cong_thuc_nghi": len(ra), "danh_sach": ra}


@frappe.whitelist()
def xem_truoc(ma_trung=None):
	"""Ke hoach doi: dong nao doi, tu gi sang gi. CHI DOC."""
	_vai()
	return _dung_ke_hoach(ma_trung)


def _dung_ke_hoach(ma_trung=None):
	ma_trung = _ma(ma_trung)
	ke_hoach, bo_qua = [], []
	for b in _bom_con_song():
		for d in _dong(b.name):
			if d.item_code not in ma_trung:
				continue
			if not can_doi(d.uom, d.stock_uom):
				bo_qua.append({"bom": b.name, "dong": d.name, "ly_do": "đã đúng đơn vị kho"})
				continue
			qty_moi, hs_moi, rate_moi = doi_mot_dong(
				d.qty, d.conversion_factor, d.rate, d.stock_qty
			)
			ke_hoach.append({
				"bom": b.name, "mon": b.item_name, "dong": d.name, "idx": d.idx,
				"ma": d.item_code,
				"truoc": {"qty": flt(d.qty), "uom": d.uom, "he_so": flt(d.conversion_factor),
						  "rate": flt(d.rate), "stock_qty": flt(d.stock_qty)},
				"sau": {"qty": round(qty_moi, 6), "uom": DVT_DICH, "he_so": hs_moi,
						"rate": round(rate_moi, 6), "stock_qty": round(qty_moi, 6)},
				"amount_giu_nguyen": flt(d.amount),
			})
	return {"so_dong_se_doi": len(ke_hoach), "so_dong_bo_qua": len(bo_qua),
			"ke_hoach": ke_hoach, "bo_qua": bo_qua}


@frappe.whitelist()
def doi_het(chay_that=0, bo_qua_nghi=0, ma_trung=None):
	"""Doi don vi cho toan bo dong trung trong cong thuc.

	MAC DINH KHONG GHI GI. Phai truyen `chay_that=1` moi ghi.

	Chan san khi con cong thuc nghi ghi nham. Xem doan dai o dau tep de
	biet vi sao GIU cai chan nay ke ca sau khi anh Viet da chot phuong an.

	Vi sao ghi thang bang db.set_value chu khong mo tai lieu ra sua: cong
	thuc da ghi so (docstatus 1), ERPNext khong cho sua. Muon dung duong
	chinh thi phai huy roi dung ban moi cho ca 94 cong thuc, keo theo doi
	ten ban, dut lien ket voi lenh san xuat cu, va mat lich su. Phep doi
	nay giu NGUYEN `stock_qty` va `amount`, tuc khong dong vao con so nao
	ma so sach dua vao, nen ghi thang la duong it rui ro hon nhieu. Doi
	lai, phai tu tay dam bao cac con so kia dung, va do la viec cua
	`doi_mot_dong` cong bo ca kiem cua no.
	"""
	_vai()
	chay_that = int(chay_that or 0)
	bo_qua_nghi = int(bo_qua_nghi or 0)

	nghi = soi_ghi_nham(ma_trung)
	if nghi["so_cong_thuc_nghi"] and not bo_qua_nghi:
		frappe.throw(
			"Còn %d công thức nghi ghi nhầm số quả vào ô gram. Đổi đơn vị "
			"không sửa được lỗi đó, mà đổi xong thì con số sai sẽ khoác áo "
			"\"Quả\" nhìn rất thật. Xử lý chỗ sai trước đã. Muốn bỏ qua thì "
			"gọi lại với bo_qua_nghi=1." % nghi["so_cong_thuc_nghi"]
		)

	kh = _dung_ke_hoach(ma_trung)
	if not chay_that:
		kh["da_ghi"] = 0
		kh["ghi_chu"] = "Chạy thử, chưa ghi gì. Gọi lại với chay_that=1 để ghi thật."
		return kh

	_dam_bao_quy_doi(ma_trung)
	da = 0
	for k in kh["ke_hoach"]:
		frappe.db.set_value("BOM Item", k["dong"], {
			"uom": k["sau"]["uom"],
			"conversion_factor": k["sau"]["he_so"],
			"qty": k["sau"]["qty"],
			"rate": k["sau"]["rate"],
			# stock_qty va amount CO Y dat lai dung bang gia tri cu, de neu
			# co sai so lam tron o dau thi no dung o day chu khong troi
			# sang so sach.
			"stock_qty": k["sau"]["stock_qty"],
			"amount": k["amount_giu_nguyen"],
		}, update_modified=False)
		da += 1
	frappe.db.commit()
	kh["da_ghi"] = da
	return kh


def _dam_bao_quy_doi(ma_trung=None):
	"""Khai quy doi `Qua = 1` tren mat hang, neu chua co.

	Thieu dong nay thi man hinh va cac chung tu khac se bao don vi khong
	hop le khi nguoi dung chon Qua.
	"""
	for ma in _ma(ma_trung):
		if not frappe.db.exists("Item", ma):
			continue
		doc = frappe.get_doc("Item", ma)
		if any((u.uom or "").strip() == DVT_DICH for u in (doc.get("uoms") or [])):
			continue
		doc.append("uoms", {"uom": DVT_DICH, "conversion_factor": 1.0})
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
