"""v648 phương án C (anh Việt chốt 11/11/2026), Codex #551: ca tích hợp THẬT.

Bếp chỉ bấm Hoàn tất món chính. Ruột bánh cấp 1, bánh khuôn cấp 2 còn thiếu tồn
thì máy tự tạo và hoàn tất lệnh của chúng trước món chính.

Ca này dựng đúng chuỗi lời gọi app gửi lên máy chủ khi bấm Hoàn tất
(05-san-xuat.js mfgHoanTatMot rồi mfgRunFresh), trên Work Order, Stock Entry,
SLE, GL thật của ERPNext:
  1. hỏi máy chủ món nào được tự làm: kho_san_xuat.mon_tu_lam (hàm thật);
  2. lệnh con: Work Order đúng các ô mfgCreateWO gửi (skip_transfer, nổ nhiều
     cấp, kho nguồn và kho nhập là kho nguyên liệu của bếp), insert rồi submit;
  3. lệnh con của lệnh con theo required_items của nó, cấp 1 trước cấp 2;
  4. mỗi lệnh: make_stock_entry Manufacture rồi kho_san_xuat.hoan_tat_phieu
     (cùng cửa của món chính, giờ máy chủ).
Phần "tính thiếu bao nhiêu" của app (mfgFreshPlan) đã có ca hành vi chạy thật mã
app (kiem_thu/hanh_vi/tu_lam_cap_duoi_648.js); ở đây chép lại đúng phép trừ đó
để ERPNext chấm chuỗi chứng từ, không thay ca hành vi.

Công thức giống bếp thật (phantom.py): dòng cấp 1, cấp 2 trong công thức cha
có do_not_explode = 1 để lệnh nổ nhiều cấp vẫn đòi đúng bánh khuôn, ruột bánh.
Mã thử ngẫu nhiên, savepoint của nen.py, không commit.
"""
import uuid

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _uom

GIA_NVL = 1000


def _bom(ma, cty, dong):
	b = frappe.get_doc({"doctype": "BOM", "item": ma, "company": cty, "quantity": 1, "is_active": 1,
		"is_default": 1, "rm_cost_as_per": "Valuation Rate", "items": dong})
	b.insert(); nen._DA_TAO.append(("BOM", b.name)); b.submit(); b.reload()
	return b


def _mon(tag, loai, chang=None):
	ma = _mon_thu("KT648-%s-%s" % (loai, tag))
	if chang:
		# Ô "Chặng bán thành phẩm" người khai trên hồ sơ món (nấc 1 của
		# chang_cua_mon). Ghi thẳng để không chạy hook gán tài khoản BTP.
		dung("bench có ô Chặng bán thành phẩm", frappe.get_meta("Item").has_field("custom_chang_btp"))
		frappe.db.set_value("Item", ma, "custom_chang_btp", chang, update_modified=False)
	return ma


def _the_gioi(ton_c1=0, cha_an_c1=0, nvl_bep=1000, nvl_tong=0):
	"""Bánh ổ TP cần 2 bánh khuôn C2 + 30 NVL; mỗi C2 cần 1 ruột C1 + 100 NVL;
	mỗi C1 cần 50 NVL. Kho bếp có 1000 NVL giá 1000.

	cha_an_c1: bánh ổ cần thêm từng ấy ruột C1 trực tiếp (Codex #551 vòng 3:
	C1 vừa là nguyên liệu của bánh ổ vừa là nguyên liệu của C2)."""
	from erpnext import is_perpetual_inventory_enabled
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	cty = cong_ty()
	dung("bench bật hạch toán kho", bool(is_perpetual_inventory_enabled(cty)))
	bep, tk_bep = _kho_rieng(cty, "648-BEP")
	kho_tp, tk_tp = _kho_rieng(cty, "648-TP")
	# Kho tổng thử phải dựng TRƯỚC phiếu kho đầu tiên: ERPNext giữ bản đồ
	# kho sang tài khoản trong request (frappe.flags), kho dựng sau phiếu đầu
	# sẽ báo "not linked to any account" (bench 24e6375e96).
	tong = _kho_rieng(cty, "648-TONG")[0] if nvl_tong else None
	tag = uuid.uuid4().hex[:10]
	nvl = _mon(tag, "NVL")
	c1 = _mon(tag, "C1", "BTP sơ cấp")
	c2 = _mon(tag, "C2", "BTP sẵn sàng")
	tp = _mon(tag, "TP")
	uom = _uom()
	# Dòng cấp 1, cấp 2 trong công thức cha: do_not_explode = 1, không bom_no
	# (bo_ao.viec_dong_cha, phantom.py mục 3), như 39 dòng thật của bếp.
	_bom(c1, cty, [{"item_code": nvl, "qty": 50, "uom": uom, "rate": GIA_NVL}])
	_bom(c2, cty, [{"item_code": c1, "qty": 1, "uom": uom, "do_not_explode": 1},
		{"item_code": nvl, "qty": 100, "uom": uom, "rate": GIA_NVL}])
	dong_cha = [{"item_code": c2, "qty": 2, "uom": uom, "do_not_explode": 1},
		{"item_code": nvl, "qty": 30, "uom": uom, "rate": GIA_NVL}]
	if cha_an_c1:
		# Dòng ruột bánh đứng TRƯỚC bánh khuôn như ca Codex (C1 đầu required_items).
		dong_cha.insert(0, {"item_code": c1, "qty": cha_an_c1, "uom": uom, "do_not_explode": 1})
	cha = _bom(tp, cty, dong_cha)
	d = nhap(item_code=nvl, qty=nvl_bep, company=cty, to_warehouse=bep, rate=GIA_NVL, do_not_save=True)
	d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	if nvl_tong:
		d = nhap(item_code=nvl, qty=nvl_tong, company=cty, to_warehouse=tong, rate=GIA_NVL, do_not_save=True)
		d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	if ton_c1:
		# Ruột bánh làm sẵn hôm trước, nhập tồn đúng giá vốn của nó (50 NVL).
		d = nhap(item_code=c1, qty=ton_c1, company=cty, to_warehouse=bep, rate=50 * GIA_NVL, do_not_save=True)
		d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	return frappe._dict(cty=cty, bep=bep, kho_tp=kho_tp, tong=tong, tk_bep=tk_bep, tk_tp=tk_tp, nvl=nvl, c1=c1, c2=c2, tp=tp, cha=cha)


def _lenh_nhu_app(cty, code, bom, qty, src, fg):
	"""Đúng các ô mfgCreateWO gửi qua frappe.client.insert rồi submit."""
	wo = frappe.get_doc({"doctype": "Work Order", "company": cty, "production_item": code, "bom_no": bom,
		"qty": qty, "fg_warehouse": fg, "source_warehouse": src, "skip_transfer": 1, "use_multi_level_bom": 1,
		"planned_start_date": frappe.utils.today() + " 05:00:00"})
	wo.insert(); nen._DA_TAO.append(("Work Order", wo.name)); wo.submit(); wo.reload()
	return wo


def _ton(ma, kho):
	return frappe.utils.flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty"))


def _giu_cua_lenh(mats, ratio, giu):
	"""Chép mfgGiuCuaLenh: phần giữ của ông cha cộng nhu cầu trực tiếp của lệnh này."""
	ra = dict(giu or {})
	for m in mats:
		ra[m.item_code] = round(ra.get(m.item_code, 0) + float(m.required_qty) * ratio, 3)
	return ra


def _ke_hoach(mats, ratio, src, giu=None):
	"""Chép phép trừ của mfgFreshPlan: món máy chủ cho tự làm,
	thiếu = cần - (tồn - phần đã giữ cho lệnh cấp trên)."""
	from vagabond.kho_san_xuat import mon_tu_lam
	import json
	giu = giu or {}
	ma = [m.item_code for m in mats]
	tu_lam = set(mon_tu_lam(json.dumps(ma)))
	giu_con = _giu_cua_lenh(mats, ratio, giu)
	ra = []
	for m in mats:
		if m.item_code not in tu_lam:
			continue
		co = max(0, _ton(m.item_code, src) - giu.get(m.item_code, 0))
		thieu = round(float(m.required_qty) * ratio - co, 3)
		if thieu > 0.0001:
			bom = frappe.db.get_value("BOM", {"item": m.item_code, "is_active": 1, "is_default": 1, "docstatus": 1}, "name")
			ra.append(frappe._dict(code=m.item_code, qty=thieu, bom=bom, giu=giu_con))
	return ra


def _hoan_tat(wo, q, lay_bu=0, nhat=None):
	"""make_stock_entry rồi hoan_tat_phieu: cửa của nút Hoàn tất (giờ máy chủ)."""
	from vagabond.kho_san_xuat import hoan_tat_phieu
	phieu = make_stock_entry(wo.name, "Manufacture", qty=q)
	if lay_bu:
		# Như mfgGhiLenh: hỏi trước, rồi ghi kèm đúng số đã duyệt (Codex #551 vòng 8).
		kq = hoan_tat_phieu(phieu, q=q, can=q, hoi_lay_bu=1)
		if kq.get("hoi_lay_bu"):
			toi = {}
			for x in kq["hoi_lay_bu"]:
				toi[x["ma"]] = toi.get(x["ma"], 0) + x["sl"]
			kq = hoan_tat_phieu(make_stock_entry(wo.name, "Manufacture", qty=q), q=q, can=q, lay_bu=1, lay_toi_da=frappe.as_json(toi))
	else:
		kq = hoan_tat_phieu(phieu, q=q, can=q, lay_bu=lay_bu)
	if kq.get("phieu_bu"):
		nen._DA_TAO.append(("Stock Entry", kq["phieu_bu"]))
		if nhat is not None:
			nhat.append(("bu", wo.production_item, kq["phieu_bu"]))
	nen._DA_TAO.append(("Stock Entry", kq["name"]))
	return frappe.get_doc("Stock Entry", kq["name"])


def _lam_con(cty, ke, src, nhat, cap=1, lay_bu=0):
	"""Chép mfgRunFresh: tạo lệnh, làm lệnh con của nó trước, rồi hoàn tất."""
	for f in ke:
		wo = _lenh_nhu_app(cty, f.code, f.bom, f.qty, src, src)
		nhat.append(("lenh", f.code, float(f.qty)))
		if cap < 3:
			con = _ke_hoach(wo.required_items, 1, wo.source_warehouse or src, f.giu)
			if con:
				_lam_con(cty, con, src, nhat, cap + 1, lay_bu)
		se = _hoan_tat(wo, f.qty, lay_bu, nhat)
		nhat.append(("phieu", f.code, se.name))


def _sle(phieu):
	return frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Stock Entry", "voucher_no": phieu,
		"is_cancelled": 0}, fields=["item_code", "warehouse", "actual_qty", "stock_value_difference"])


def _bam_hoan_tat(w, so_banh, doi=None):
	"""Bếp bấm Hoàn tất món chính so_banh cái trên lệnh 2 bánh."""
	cha = _lenh_nhu_app(w.cty, w.tp, w.cha.name, 2, w.bep, w.kho_tp)
	la("lệnh cha đòi bánh khuôn, không nổ xuyên xuống ruột bánh",
		sorted((d.item_code, float(d.required_qty)) for d in cha.required_items), sorted(doi or [(w.c2, 4.0), (w.nvl, 60.0)]))
	nhat = []
	ke = _ke_hoach(cha.required_items, so_banh / 2.0, w.bep)
	_lam_con(w.cty, ke, w.bep, nhat)
	se = _hoan_tat(cha, so_banh)
	return cha, nhat, se


@ca("v648 thật: hết tồn cấp 1, cấp 2: máy làm ruột bánh rồi bánh khuôn rồi bánh ổ, trừ đủ NVL, tồn trung gian về 0, GL cân")
def _het_ton():
	from vagabond.kho_san_xuat import mon_tu_lam
	import json
	w = _the_gioi()
	la("máy chủ chỉ cho tự làm cấp 1, cấp 2", sorted(mon_tu_lam(json.dumps([w.nvl, w.c1, w.c2, w.tp]))), sorted([w.c1, w.c2]))
	cha, nhat, se = _bam_hoan_tat(w, 2)
	la("thứ tự lệnh và phiếu: cấp 2 tạo trước, cấp 1 ghi sổ trước", [(x[0], x[1]) for x in nhat],
		[("lenh", w.c2), ("lenh", w.c1), ("phieu", w.c1), ("phieu", w.c2)])
	la("số lệnh con", [x[2] for x in nhat if x[0] == "lenh"], [4.0, 4.0])
	sle = _sle(se.name)
	la("phiếu món chính: trừ 4 bánh khuôn, 60 NVL, nhập 2 bánh ổ",
		sorted((d.item_code, d.warehouse, float(d.actual_qty)) for d in sle),
		sorted([(w.c2, w.bep, -4.0), (w.nvl, w.bep, -60.0), (w.tp, w.kho_tp, 2.0)]))
	la("NVL còn lại: 1000 - 4x50 - 4x100 - 60", _ton(w.nvl, w.bep), 340.0)
	la("ruột bánh làm ra bao nhiêu dùng hết bấy nhiêu", _ton(w.c1, w.bep), 0.0)
	la("bánh khuôn làm ra bao nhiêu dùng hết bấy nhiêu", _ton(w.c2, w.bep), 0.0)
	la("bánh ổ nhập kho", _ton(w.tp, w.kho_tp), 2.0)
	# Giá vốn đi trọn chuỗi: 660 NVL x 1000 thành 2 bánh ổ.
	la("giá trị bánh ổ nhận", sum(float(d.stock_value_difference) for d in sle if d.item_code == w.tp), 660000.0)
	for x in nhat + [("phieu", w.tp, se.name)]:
		if x[0] != "phieu":
			continue
		gl = so_cai_cua(frappe.get_doc("Stock Entry", x[2]))
		la("GL cân %s" % x[1], round(sum(float(d.debit) for d in gl), 2), round(sum(float(d.credit) for d in gl), 2))
	cha.reload()
	la("lệnh cha hoàn tất", (float(cha.produced_qty), cha.status), (2.0, "Completed"))


@ca("v648 thật: ruột bánh làm sẵn còn 1: máy chỉ làm phần thiếu, dùng tồn cho phần còn lại; hoàn tất một phần làm theo tỷ lệ")
def _con_ton():
	w = _the_gioi(ton_c1=1)
	cha, nhat, se = _bam_hoan_tat(w, 1)
	la("làm 2 bánh khuôn (1 trong 2 bánh ổ), 1 ruột bánh còn thiếu",
		[(x[1], x[2]) for x in nhat if x[0] == "lenh"], [(w.c2, 2.0), (w.c1, 1.0)])
	la("ruột bánh dùng cả tồn cũ", _ton(w.c1, w.bep), 0.0)
	la("bánh khuôn hết", _ton(w.c2, w.bep), 0.0)
	la("NVL: 1000 - 1x50 - 2x100 - 30", _ton(w.nvl, w.bep), 720.0)
	cha.reload()
	la("lệnh cha còn mở một bánh", (float(cha.produced_qty), cha.status), (1.0, "In Process"))


@ca("v648 thật: đủ tồn bánh khuôn thì không tạo lệnh con nào")
def _du_ton():
	w = _the_gioi()
	d = nhap(item_code=w.c2, qty=4, company=w.cty, to_warehouse=w.bep, rate=150 * GIA_NVL, do_not_save=True)
	d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	cha, nhat, se = _bam_hoan_tat(w, 2)
	la("không lệnh con", nhat, [])
	la("NVL chỉ trừ phần rắc mặt", _ton(w.nvl, w.bep), 940.0)


@ca("v648 thật, Codex #551 vòng 3: bánh ổ cần cả ruột bánh lẫn bánh khuôn (bánh khuôn cũng ăn ruột bánh): máy giữ phần ruột của bánh ổ, không báo thiếu sau khi lệnh con đã ghi sổ")
def _cha_an_ca_hai():
	w = _the_gioi(ton_c1=1, cha_an_c1=1)
	# Lệnh 2 bánh: 2 ruột C1 trực tiếp + 4 bánh khuôn + 60 NVL. Tồn ruột 1.
	cha, nhat, se = _bam_hoan_tat(w, 2, [(w.c1, 2.0), (w.c2, 4.0), (w.nvl, 60.0)])
	la("lệnh con: ruột thiếu cho bánh ổ, bánh khuôn, ruột cho bánh khuôn",
		sorted((x[1], x[2]) for x in nhat if x[0] == "lenh"), sorted([(w.c1, 1.0), (w.c2, 4.0), (w.c1, 4.0)]))
	sle = _sle(se.name)
	la("phiếu món chính trừ đủ 2 ruột, 4 bánh khuôn",
		sorted((d.item_code, float(d.actual_qty)) for d in sle if d.item_code in (w.c1, w.c2)),
		sorted([(w.c1, -2.0), (w.c2, -4.0)]))
	la("ruột bánh về 0", _ton(w.c1, w.bep), 0.0)
	la("bánh khuôn về 0", _ton(w.c2, w.bep), 0.0)
	la("NVL: 1000 - 5x50 - 4x100 - 60", _ton(w.nvl, w.bep), 290.0)
	cha.reload()
	la("lệnh cha hoàn tất", (float(cha.produced_qty), cha.status), (2.0, "Completed"))


@ca("v648 thật, cách 1 anh Việt chọn: kho bếp thiếu nguyên liệu thì máy lấy bù từ kho tổng ngay trước từng phiếu hoàn tất; chỉ hỏi thì không ghi gì")
def _lay_bu_kho_tong():
	from vagabond import kho_san_xuat as ksx
	w = _the_gioi(nvl_bep=300, nvl_tong=1000)
	tong = w.tong
	goc = ksx.KHO_GOC
	ksx.KHO_GOC = tong  # bench không có Kho tổng 307 - TV
	try:
		cha = _lenh_nhu_app(w.cty, w.tp, w.cha.name, 2, w.bep, w.kho_tp)
		ke = _ke_hoach(cha.required_items, 1, w.bep)
		nhat = []
		_lam_con(w.cty, ke, w.bep, nhat, lay_bu=1)
		# Lệnh con xong, bếp hết NVL; món chính cần 60. Chỉ hỏi (đường của nút
		# Hoàn tất khi không có hộp xác nhận): trả phần lấy, không ghi gì.
		truoc = frappe.db.count("Stock Entry", {"from_warehouse": tong})
		kq = ksx.hoan_tat_phieu(make_stock_entry(cha.name, "Manufacture", qty=2), q=2, can=2, hoi_lay_bu=1)
		la("chỉ hỏi: trả đúng 60", [(x["ma"], x["sl"]) for x in kq.get("hoi_lay_bu") or []], [(w.nvl, 60.0)])
		la("chỉ hỏi: không phiếu nào được lập", frappe.db.count("Stock Entry", {"from_warehouse": tong}), truoc)
		dung("chỉ hỏi: không ghi phiếu hoàn tất", not kq.get("name"))
		# Codex #551 vòng 8: số duyệt nhỏ hơn phần thiếu thì máy chủ không ghi.
		kq = ksx.hoan_tat_phieu(make_stock_entry(cha.name, "Manufacture", qty=2), q=2, can=2, lay_bu=1, lay_toi_da=frappe.as_json({w.nvl: 30}))
		la("duyệt 30 mà thiếu 60: hỏi lại, không lập phiếu", ([x["sl"] for x in kq.get("hoi_lay_bu") or []], frappe.db.count("Stock Entry", {"from_warehouse": tong})), ([60.0], truoc))
		se = _hoan_tat(cha, 2, 1, nhat)
	finally:
		ksx.KHO_GOC = goc
	bu = [x for x in nhat if x[0] == "bu"]
	# C1 x4 ăn 200 (bếp còn 100), C2 x4 cần 400 (lấy 300), bánh ổ cần 60 (lấy 60).
	la("phiếu lấy bù đúng lệnh", [x[1] for x in bu], [w.c2, w.tp])
	la("số lấy", [sorted((r.item_code, r.s_warehouse, r.t_warehouse, float(r.qty)) for r in frappe.get_doc("Stock Entry", x[2]).items) for x in bu],
		[[(w.nvl, tong, w.bep, 300.0)], [(w.nvl, tong, w.bep, 60.0)]])
	for x in bu:
		p = frappe.get_doc("Stock Entry", x[2])
		la("phiếu lấy bù đã ghi sổ", (p.docstatus, p.purpose), (1, "Material Transfer"))
		if frappe.get_meta("Stock Entry").has_field("vgb_nhan_tt"):
			la("ghi bếp đã nhận đủ", p.get("vgb_nhan_tt"), "Đã nhận đủ")
		gl = so_cai_cua(p)
		la("GL cân phiếu lấy bù", round(sum(float(g.debit) for g in gl), 2), round(sum(float(g.credit) for g in gl), 2))
	la("NVL bếp dùng hết", _ton(w.nvl, w.bep), 0.0)
	la("kho tổng còn 1000 - 360", _ton(w.nvl, tong), 640.0)
	la("bánh ổ nhập kho", _ton(w.tp, w.kho_tp), 2.0)
	la("phiếu món chính ghi sổ", se.docstatus, 1)
	cha.reload()
	la("lệnh cha hoàn tất", (float(cha.produced_qty), cha.status), (2.0, "Completed"))


@ca("v648 thật: lệnh con ghi sổ giờ máy chủ dù điện thoại nhanh 10 phút; phiếu món chính không đứng trước phiếu nhập bánh khuôn")
def _gio_may_chu():
	from frappe.utils import add_to_date, get_datetime, now_datetime
	from vagabond.kho_san_xuat import hoan_tat_phieu
	w = _the_gioi()
	d = nhap(item_code=w.c1, qty=4, company=w.cty, to_warehouse=w.bep, rate=50 * GIA_NVL, do_not_save=True)
	d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	cha = _lenh_nhu_app(w.cty, w.tp, w.cha.name, 2, w.bep, w.kho_tp)
	ke = _ke_hoach(cha.required_items, 1, w.bep)
	la("chỉ thiếu bánh khuôn", [(f.code, float(f.qty)) for f in ke], [(w.c2, 4.0)])
	con = _lenh_nhu_app(w.cty, w.c2, ke[0].bom, 4, w.bep, w.bep)
	phieu = make_stock_entry(con.name, "Manufacture", qty=4)
	nhanh = add_to_date(now_datetime(), minutes=10)
	# Đúng cái app cũ gửi: giờ điện thoại.
	phieu.update(set_posting_time=1, posting_date=str(nhanh.date()), posting_time=nhanh.strftime("%H:%M:%S"))
	kq = hoan_tat_phieu(phieu, q=4, can=4)
	nen._DA_TAO.append(("Stock Entry", kq["name"]))
	se_con = frappe.get_doc("Stock Entry", kq["name"])
	luc_con = get_datetime("%s %s" % (se_con.posting_date, se_con.posting_time))
	dung("lệnh con lấy giờ máy chủ, không lấy giờ điện thoại", luc_con < nhanh)
	se = _hoan_tat(cha, 2)
	luc_cha = get_datetime("%s %s" % (se.posting_date, se.posting_time))
	dung("phiếu món chính sau phiếu nhập bánh khuôn", luc_cha >= luc_con)
	la("bánh khuôn hết", _ton(w.c2, w.bep), 0.0)


@ca("v648 thật, đường cũ trước Codex #551: lệnh con ghi giờ điện thoại nhanh 10 phút thì ERPNext chặn phiếu món chính vì thiếu bánh khuôn")
def _duong_cu():
	from frappe.utils import add_to_date, now_datetime
	from vagabond.kho_san_xuat import hoan_tat_phieu
	w = _the_gioi()
	d = nhap(item_code=w.c1, qty=4, company=w.cty, to_warehouse=w.bep, rate=50 * GIA_NVL, do_not_save=True)
	d.insert(); nen._DA_TAO.append(("Stock Entry", d.name)); d.submit()
	cha = _lenh_nhu_app(w.cty, w.tp, w.cha.name, 2, w.bep, w.kho_tp)
	con = _lenh_nhu_app(w.cty, w.c2, frappe.db.get_value("BOM", {"item": w.c2, "docstatus": 1}, "name"), 4, w.bep, w.bep)
	# Đúng hai lời gọi của mfgRunFresh trước bản sửa: frappe.client.insert rồi submit, giờ điện thoại.
	phieu = make_stock_entry(con.name, "Manufacture", qty=4)
	nhanh = add_to_date(now_datetime(), minutes=10)
	phieu.update(set_posting_time=1, posting_date=str(nhanh.date()), posting_time=nhanh.strftime("%H:%M:%S"))
	se_con = frappe.get_doc(phieu)
	se_con.insert(); nen._DA_TAO.append(("Stock Entry", se_con.name)); se_con.submit()
	try:
		kq = hoan_tat_phieu(make_stock_entry(cha.name, "Manufacture", qty=2), q=2, can=2)
		nen._DA_TAO.append(("Stock Entry", kq["name"]))
		loi = None
	except Exception as e:
		loi = nen.cau_loi(e)
	# Chặn vì thiếu đúng bánh khuôn ở thời điểm phiếu món chính, không phải lỗi khác.
	dung("đường cũ bị ERPNext chặn vì thiếu bánh khuôn (nếu ca này đỏ: sửa lại mô tả Codex #551): %r" % loi,
		bool(loi) and w.c2 in loi)
