# -*- coding: utf-8 -*-
"""v613: tin Zalo tồn kho và sản xuất (anh Việt duyệt 27/10/2026).

Anh Việt chọn sáu tin:
  - Kho: tồn bánh cuối ngày từng chi nhánh (23:00, ẢNH bảng), tồn âm trên máy
    (08:00), hàng nằm im 30 ngày (Thứ Hai 08:05).
  - Bếp: thiếu nguyên liệu cho yêu cầu ngày mai (20:45, ngay sau tin tổng yêu cầu
    20:30), sản lượng cuối ngày từng bếp (21:00, ẢNH bảng), lệnh sản xuất quá
    ngày chưa ghi hoàn tất (08:00).

Luật chung (kenh_zalo.BO_PHAN_DUOC_TIEN): tin Kho, Bếp không mang số tiền.
Mỗi phép tính là một hàm THUẦN để kiểm thử không cần site; phần đọc dữ liệu và
gửi tin nuốt lỗi lẻ (Error Log "Vagabond: tin kho ..."), không làm hỏng lịch khác.
Ảnh vẽ hỏng thì tin vẫn đi bằng chữ: chú thích tự đủ ý.
"""

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from vagabond import kenh_zalo
from vagabond.tin_kho import _ghi_loi, _url, dong_hang, ngay_vn, so, ten_kho

SO_NGAY_NAM_IM = 30
NHOM_NAM_IM = ("Nguyên vật liệu Thô", "Bao bì")
LECH = 0.0005


# ------------------------------------------------------------------ THUẦN

def bep_cua_ten(ten):
	"""THUẦN: mã bếp ("pastry", "baker") từ tên bếp nhận của YCSX ("Bếp Pastry"); Lab và tên lạ thì None."""
	t = str(ten or "").lower()
	for ma in ("pastry", "baker"):
		if ma in t:
			return ma
	return None


def ten_bep(ma):
	"""THUẦN: "Bếp Pastry" từ mã bếp; mã lạ trả "Chưa rõ bếp"."""
	return {"pastry": "Bếp Pastry", "baker": "Bếp Baker"}.get(ma or "", "Chưa rõ bếp")


def hang_ton_quay(dong, ban):
	"""THUẦN: bảng tồn cuối ngày của một quầy từ dòng phiếu kiểm kho và số đã bán.

	dong: dòng "Vagabond Kiem Kho Dong" (ma_hang, ten_banh, theo_doi, ton_dau, nhap_1..6, hong, dieu_chinh);
	ban: {ma: số đã bán} (kiem_kho.da_ban). Chỉ dòng đang theo dõi. Trả (cột, hàng, tổng) với
	tổng = {"con","loai","ban","hong","nhap","am"}. Có điều chỉnh tay thì thêm cột "Chỉnh"."""
	from vagabond.kiem_kho import dang_theo_doi, tinh_co_the_ban, tong_nhap

	ds = []
	for d in dong or []:
		if not dang_theo_doi(d):
			continue
		ma = d.get("ma_hang")
		nhap = tong_nhap(d)
		b = flt((ban or {}).get(ma))
		con = tinh_co_the_ban(d.get("ton_dau"), nhap, b, d.get("hong"), d.get("dieu_chinh"))
		ds.append({"ten": (d.get("ten_banh") or ma or "").strip(), "dau": flt(d.get("ton_dau")), "nhap": nhap, "ban": b,
			"hong": flt(d.get("hong")), "chinh": flt(d.get("dieu_chinh")), "con": flt(con)})
	co_chinh = any(abs(x["chinh"]) > LECH for x in ds)
	cot = ["Bánh", "Đầu ngày", "Nhập", "Bán", "Hỏng"] + (["Chỉnh"] if co_chinh else []) + ["Còn"]
	ds.sort(key=lambda x: (x["con"] >= 0, -x["con"], x["ten"]))
	hang = []
	for x in ds:
		o = [x["ten"], so(x["dau"]), so(x["nhap"]), so(x["ban"]), so(x["hong"])] + ([so(x["chinh"])] if co_chinh else []) + [so(x["con"])]
		# Âm đỏ (quầy kiểm lại), hết hàng xám, còn hàng chữ thường: nhìn một giây thấy chỗ cần làm.
		hang.append({"o": o, "nhan": "do" if x["con"] < -LECH else (None if x["con"] > LECH else "xam")})
	tong = {"con": sum(max(0.0, x["con"]) for x in ds), "loai": sum(1 for x in ds if x["con"] > LECH),
		"ban": sum(x["ban"] for x in ds), "hong": sum(x["hong"] for x in ds), "nhap": sum(x["nhap"] for x in ds),
		"am": [x["ten"] for x in ds if x["con"] < -LECH]}
	return cot, hang, tong


def chu_ton_quay(ten_quay, ngay, tong):
	"""THUẦN: các dòng chú thích (chữ) của tin tồn quầy, đủ ý khi ảnh không tải được."""
	dong = ["%s, ngày %s" % (ten_quay, ngay_vn(ngay)),
		"Còn %s bánh, %d loại" % (so(tong["con"]), tong["loai"]),
		"Trong ngày: nhập %s, bán %s, hỏng %s" % (so(tong["nhap"]), so(tong["ban"]), so(tong["hong"]))]
	if tong["am"]:
		dong.append("Âm (bán hoặc hỏng nhiều hơn có): %s. Quầy kiểm lại số nhập, số hỏng." % ", ".join(tong["am"][:6]))
	return dong


def gom_ton_am(dong):
	"""THUẦN: {kho: [{"ten","sl","dvt"}]} các món đang âm, sắp âm nhiều nhất lên đầu.

	dong: [{"kho","ma","ten","dvt","sl"}] với sl < 0."""
	ra = {}
	for d in dong or []:
		if flt(d.get("sl")) < -LECH:
			ra.setdefault(d.get("kho") or "", []).append({"ten": d.get("ten") or d.get("ma") or "", "sl": flt(d.get("sl")),
				"dvt": d.get("dvt") or ""})
	for k in ra:
		ra[k].sort(key=lambda x: (x["sl"], x["ten"]))
	return ra


def chon_nam_im(ton, cuoi_xuat, dau_tien, moc):
	"""THUẦN: món còn tồn mà không xuất lần nào từ moc, và đã có trong kho từ trước moc.

	ton: [{"kho","ma","ten","dvt","sl"}] (sl > 0); cuoi_xuat, dau_tien: {(ma, kho): ngày}. Trả {kho: [...]},
	món nằm lâu nhất (chưa xuất bao giờ) lên đầu."""
	moc = getdate(moc)
	ra = {}
	for d in ton or []:
		if flt(d.get("sl")) <= LECH:
			continue
		k = (d.get("ma"), d.get("kho"))
		dau = dau_tien.get(k)
		if not dau or getdate(dau) >= moc:
			continue
		xuat = cuoi_xuat.get(k)
		if xuat and getdate(xuat) >= moc:
			continue
		ghi = ("xuất lần cuối %s" % ngay_vn(xuat)) if xuat else "chưa xuất lần nào"
		ra.setdefault(d.get("kho") or "", []).append({"ten": d.get("ten") or d.get("ma") or "", "sl": flt(d.get("sl")),
			"dvt": d.get("dvt") or "", "ghi": ghi, "_xep": getdate(xuat) if xuat else getdate("1900-01-01")})
	for k in ra:
		ra[k].sort(key=lambda x: (x["_xep"], x["ten"]))
	return ra


def bang_san_luong(yeu_cau, da_lam):
	"""THUẦN: bảng sản lượng một bếp. yeu_cau, da_lam: {ma: {"ten","sl","dvt"}}.

	Trả (cột, hàng, tổng) với tổng = {"mon","du","thieu":[tên]}; món thiếu (đỏ) lên đầu, món làm
	ngoài yêu cầu ghi "ngoài yêu cầu"."""
	ma = sorted(set(yeu_cau or {}) | set(da_lam or {}))
	ds = []
	for m in ma:
		y, l = (yeu_cau or {}).get(m) or {}, (da_lam or {}).get(m) or {}
		sy, sl = flt(y.get("sl")), flt(l.get("sl"))
		ds.append({"ten": y.get("ten") or l.get("ten") or m, "dvt": y.get("dvt") or l.get("dvt") or "",
			"yc": sy, "lam": sl, "thieu": max(0.0, sy - sl)})
	ds.sort(key=lambda x: (-(x["thieu"] > LECH), -x["thieu"], x["ten"]))
	hang = []
	for x in ds:
		con = so(x["thieu"]) if x["yc"] > LECH else "ngoài yêu cầu"
		hang.append({"o": [x["ten"], x["dvt"], so(x["yc"]), so(x["lam"]), con],
			"nhan": "do" if x["thieu"] > LECH else None})
	tong = {"mon": sum(1 for x in ds if x["yc"] > LECH), "du": sum(1 for x in ds if x["yc"] > LECH and x["thieu"] <= LECH),
		"thieu": ["%s thiếu %s %s" % (x["ten"], so(x["thieu"]), x["dvt"]) for x in ds if x["thieu"] > LECH]}
	return ["Món", "ĐVT", "Yêu cầu", "Đã làm", "Còn thiếu"], hang, tong


def no_thanh_phan(bom, sl, thanh_phan, sau=0):
	"""THUẦN (Codex #504 P2): các dòng nguyên liệu thật để làm sl đơn vị theo công thức bom.

	Dòng bán thành phẩm phantom (is_phantom_item, có bom_no) không quản tồn: nổ tiếp vào
	công thức con theo đúng tỷ lệ, như lệnh sản xuất của ERPNext (patches/no_phantom_chuan).
	Bán thành phẩm CÓ quản tồn giữ nguyên một dòng, so với tồn kho của chính nó.
	Trả [(dòng, số lượng)]. Công thức tự trỏ vào mình hoặc sâu quá 10 tầng thì dừng ở dòng đó."""
	ct = (thanh_phan or {}).get(bom or "")
	if not ct:
		return []
	he = flt(sl) / (flt(ct.get("so_ra")) or 1.0)
	ra = []
	for d in ct.get("dong") or []:
		con = d.get("bom_no") if cint(d.get("phantom")) else None
		if con and con in (thanh_phan or {}) and con != bom and sau < 10:
			ra += no_thanh_phan(con, flt(d.get("sl")) * he, thanh_phan, sau + 1)
		else:
			ra.append((d, flt(d.get("sl")) * he))
	return ra


def tinh_thieu_nvl(can_lam, thanh_phan, ton):
	"""THUẦN: nguyên liệu thiếu cho các món cần làm.

	can_lam: [{"ma","ten","sl","bom"}] (sl theo đơn vị kho của món);
	thanh_phan: {bom: {"so_ra","dong":[{ma,ten,dvt,sl,phantom,bom_no}]}} (_cay_bom, gồm cả công thức
	con của dòng phantom); ton: {ma: tồn trong kho nguyên liệu của bếp}.
	Trả (thiếu [{"ten","sl","dvt","ghi"}], món không có công thức [tên])."""
	can, khong_ct = {}, []
	for m in can_lam or []:
		ct = (thanh_phan or {}).get(m.get("bom") or "")
		if not ct:
			khong_ct.append(m.get("ten") or m.get("ma") or "")
			continue
		for d, sl in no_thanh_phan(m.get("bom"), flt(m.get("sl")), thanh_phan):
			o = can.setdefault(d.get("ma"), {"ten": d.get("ten") or d.get("ma"), "dvt": d.get("dvt") or "", "sl": 0.0})
			o["sl"] += sl
	thieu = []
	for ma, o in can.items():
		co = flt((ton or {}).get(ma))
		if o["sl"] - co > LECH:
			thieu.append({"ten": o["ten"], "sl": o["sl"] - co, "dvt": o["dvt"],
				"ghi": "cần %s, kho bếp còn %s" % (so(o["sl"]), so(max(co, 0.0)))})
	thieu.sort(key=lambda x: (-x["sl"], x["ten"]))
	return thieu, sorted({x for x in khong_ct if x})


# --------------------------------------------------------- Kho: tồn quầy 23:00

def gui_ton_quay_cuoi_ngay():
	"""Lịch 23:00: mỗi chi nhánh có quầy một ẢNH bảng tồn bánh cuối ngày, chú thích đủ ý."""
	try:
		from vagabond import anh_bang, kiem_kho

		ngay = nowdate()
		for d in kiem_kho._diem_co_quay():
			try:
				ma_phieu = kiem_kho.ten_phieu(d["ma"], ngay)
				if not frappe.db.exists(kiem_kho.DT, ma_phieu):
					continue
				dong = frappe.get_all(kiem_kho.DT_DONG, filters={"parent": ma_phieu, "parenttype": kiem_kho.DT},
					fields=["ma_hang", "ten_banh", "theo_doi", "ton_dau", "hong", "dieu_chinh"] + list(kiem_kho.O_NHAP),
					limit_page_length=0, ignore_permissions=True)
				cot, hang, tong = hang_ton_quay(dong, kiem_kho.da_ban(d["ma"], ngay))
				if not hang:
					continue
				ten = d.get("ten") or d["ma"]
				chu = chu_ton_quay(ten, ngay, tong)
				anh = anh_bang.anh_bang("ton-%s" % d["ma"], "Tồn bánh cuối ngày %s" % getdate(ngay).strftime("%d/%m/%Y"),
					" · ".join([x for x in (ten, d.get("dia_chi") or "") if x]), cot, hang,
					"Còn %s bánh, %d loại. Dòng đỏ: số âm, quầy kiểm lại." % (so(tong["con"]), tong["loai"]))
				if not anh:
					chu += [("%s: %s" % (h["o"][0], h["o"][-1])) for h in hang[:15]]
				kenh_zalo.bao_hoac_ghi_loi("ban_tin", "kho", "Tồn bánh cuối ngày", chu,
					link=_url("/app/vagabond-kiem-kho-diem/%s" % ma_phieu), khoa="ton-quay:%s:%s" % (d["ma"], ngay),
					ma_tin="kho_ton_quay_cuoi_ngay", anh=anh)
			except Exception as e:
				if kenh_zalo.chet_giao_dich(e):
					raise
				_ghi_loi("tồn quầy cuối ngày %s" % d.get("ma"))
	except Exception:
		_ghi_loi("tồn quầy cuối ngày")


# ------------------------------------------------------- Kho: tồn âm 08:00

def nhac_ton_am():
	"""Lịch 08:00: món đang âm kho trên máy, một tin gộp theo kho."""
	try:
		hom_nay = nowdate()
		rows = frappe.db.sql("""select b.warehouse as kho, b.item_code as ma, i.item_name as ten, i.stock_uom as dvt,
			b.actual_qty as sl from `tabBin` b join `tabItem` i on i.name = b.item_code
			where b.actual_qty < -0.0005 order by b.warehouse, b.actual_qty""", as_dict=True)
		theo_kho = gom_ton_am(rows)
		if not theo_kho:
			return
		so_mon = sum(len(v) for v in theo_kho.values())
		dong = []
		for kho, ds in sorted(theo_kho.items()):
			dong.append("Kho %s, %d món" % (ten_kho(kho), len(ds)))
			dong += ["  " + x for x in dong_hang(ds, toi_da=6)]
		dong = kenh_zalo.cat_dong(dong, 30, "dòng")
		dong.append("Âm kho là đã xuất nhiều hơn đã nhập trên máy: kiểm phiếu nhập, sản xuất, điều chuyển chưa ghi sổ.")
		kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "%d món đang âm kho" % so_mon, dong,
			link=_url("/app/query-report/Stock Balance"), khoa="ton-am:%s" % hom_nay, ma_tin="kho_ton_am")
	except Exception:
		_ghi_loi("tồn âm")


# ------------------------------------------------ Kho: hàng nằm im (Thứ Hai)

def nhac_hang_nam_im():
	"""Lịch Thứ Hai 08:05: nguyên liệu, bao bì còn tồn mà SO_NGAY_NAM_IM ngày không xuất."""
	try:
		hom_nay = nowdate()
		moc = add_days(hom_nay, -SO_NGAY_NAM_IM)
		ton = frappe.db.sql("""select b.warehouse as kho, b.item_code as ma, i.item_name as ten, i.stock_uom as dvt,
			b.actual_qty as sl from `tabBin` b join `tabItem` i on i.name = b.item_code
			where b.actual_qty > 0.0005 and i.item_group in %s""", (NHOM_NAM_IM,), as_dict=True)
		if not ton:
			return
		mocs = frappe.db.sql("""select item_code, warehouse, min(posting_date) as dau,
			max(case when actual_qty < 0 then posting_date end) as xuat
			from `tabStock Ledger Entry` where is_cancelled = 0 and item_code in %s group by item_code, warehouse""",
			(tuple(sorted({t.ma for t in ton})),), as_dict=True)
		dau = {(m.item_code, m.warehouse): m.dau for m in mocs}
		xuat = {(m.item_code, m.warehouse): m.xuat for m in mocs if m.xuat}
		theo_kho = chon_nam_im(ton, xuat, dau, moc)
		if not theo_kho:
			return
		so_mon = sum(len(v) for v in theo_kho.values())
		dong = []
		for kho, ds in sorted(theo_kho.items()):
			dong.append("Kho %s, %d món" % (ten_kho(kho), len(ds)))
			dong += ["  " + x for x in dong_hang(ds, toi_da=8)]
		dong = kenh_zalo.cat_dong(dong, 40, "dòng")
		dong.append("Thu mua bớt đặt các món này; bếp xem dùng được vào món nào trước khi hết hạn.")
		kenh_zalo.bao_hoac_ghi_loi("thong_bao", "kho", "%d món nằm im %d ngày" % (so_mon, SO_NGAY_NAM_IM), dong,
			link=_url("/app/query-report/Stock Balance"), khoa="nam-im:%s" % hom_nay, ma_tin="kho_hang_nam_im")
	except Exception:
		_ghi_loi("hàng nằm im")


# -------------------------------------------- Bếp: đọc yêu cầu và sản lượng

def _yeu_cau_ngay(ngay, chi_mo=False):
	"""{mã bếp: {ma: {"ten","sl","dvt","bom"}}} từ YCSX đã gửi, các DÒNG cần đúng ngày đó (số theo đơn vị kho).

	Codex #504 P2: lọc ngày cần trên từng dòng (Material Request Item.schedule_date), như
	ke_hoach_sx.ycsx_can_lam; một phiếu có thể gom món cần nhiều ngày khác nhau."""
	from vagabond.tin_kho import TT_MR_XONG

	dong = frappe.get_all("Material Request Item", filters={"schedule_date": ngay, "docstatus": 1},
		fields=["parent", "item_code", "item_name", "stock_qty", "qty", "stock_uom"], limit_page_length=0)
	ra = {}
	if not dong:
		return ra
	loc = {"name": ["in", sorted({i.parent for i in dong})], "material_request_type": "Manufacture", "docstatus": 1}
	if chi_mo:
		loc["status"] = ["not in", list(TT_MR_XONG)]
	else:
		loc["status"] = ["not in", ["Stopped", "Cancelled"]]
	phieu = {p.name: p.custom_bep_nhan for p in frappe.get_all("Material Request", filters=loc,
		fields=["name", "custom_bep_nhan"], limit_page_length=0)}
	for i in dong:
		if i.parent not in phieu:
			continue
		bep = bep_cua_ten(phieu.get(i.parent)) or ""
		o = ra.setdefault(bep, {}).setdefault(i.item_code, {"ten": i.item_name or i.item_code, "sl": 0.0,
			"dvt": i.stock_uom or ""})
		o["sl"] += flt(i.stock_qty) or flt(i.qty)
	return ra


def _da_lam_ngay(ngay):
	"""{mã bếp: {ma: {"ten","sl","dvt"}}} thành phẩm của phiếu sản xuất (Manufacture) ghi sổ trong ngày."""
	from vagabond.kho_san_xuat import bep_cua_kho

	ra = {}
	for d in frappe.db.sql("""select d.item_code, d.item_name, d.transfer_qty, d.stock_uom, d.t_warehouse
			from `tabStock Entry Detail` d join `tabStock Entry` e on e.name = d.parent
			where e.docstatus = 1 and e.purpose = 'Manufacture' and e.posting_date = %s and d.is_finished_item = 1""",
			(ngay,), as_dict=True):
		bep = bep_cua_kho(d.t_warehouse) or ""
		o = ra.setdefault(bep, {}).setdefault(d.item_code, {"ten": d.item_name or d.item_code, "sl": 0.0,
			"dvt": d.stock_uom or ""})
		o["sl"] += flt(d.transfer_qty)
	return ra


def gui_san_luong_bep():
	"""Lịch 21:00: mỗi bếp một ẢNH bảng yêu cầu hôm nay, số đã làm, món còn thiếu."""
	try:
		from vagabond import anh_bang

		ngay = nowdate()
		yc, lam = _yeu_cau_ngay(ngay), _da_lam_ngay(ngay)
		for bep in sorted((set(yc) | set(lam)) - {""}):
			try:
				cot, hang, tong = bang_san_luong(yc.get(bep), lam.get(bep))
				if not hang:
					continue
				ten = ten_bep(bep)
				chu = ["%s, ngày %s" % (ten, ngay_vn(ngay)),
					"%d món có yêu cầu, %d món đã đủ, %d món còn thiếu" % (tong["mon"], tong["du"], len(tong["thieu"]))]
				chu += kenh_zalo.cat_dong(tong["thieu"], 8, "món")
				anh = anh_bang.anh_bang("sx-%s" % bep, "Sản lượng %s %s" % (ten, getdate(ngay).strftime("%d/%m/%Y")),
					"Yêu cầu sản xuất cần hôm nay so với phiếu sản xuất đã ghi sổ", cot, hang,
					"Dòng đỏ: còn thiếu, bếp báo Sales nếu không kịp.")
				kenh_zalo.bao_hoac_ghi_loi("ban_tin", "san_xuat", "Sản lượng cuối ngày", chu,
					link=_url("/app/work-order"), khoa="san-luong:%s:%s" % (bep, ngay), ma_tin="bep_san_luong_ngay", anh=anh)
			except Exception as e:
				if kenh_zalo.chet_giao_dich(e):
					raise
				_ghi_loi("sản lượng %s" % bep)
	except Exception:
		_ghi_loi("sản lượng cuối ngày")


def _cay_bom(cac_bom):
	"""{bom: {"so_ra","dong":[{ma,ten,dvt,sl,phantom,bom_no}]}} cho các công thức và MỌI công thức con
	mà dòng phantom trỏ vào (đọc theo tầng, mỗi tầng một lượt, tối đa 10 tầng)."""
	ra, can_doc = {}, sorted({b for b in (cac_bom or []) if b})
	for _ in range(10):
		if not can_doc:
			break
		for b in frappe.get_all("BOM", filters={"name": ["in", can_doc]}, fields=["name", "quantity"], limit_page_length=0):
			ra[b.name] = {"so_ra": flt(b.quantity) or 1.0, "dong": []}
		con = set()
		for d in frappe.get_all("BOM Item", filters={"parent": ["in", can_doc]}, fields=["parent", "item_code", "item_name",
				"qty", "uom", "stock_uom", "stock_qty", "is_phantom_item", "bom_no"], order_by="idx", limit_page_length=0):
			o = ra.get(d.parent)
			if o is None:
				continue
			o["dong"].append({"ma": d.item_code, "ten": d.item_name or d.item_code, "dvt": d.stock_uom or d.uom or "",
				"sl": flt(d.stock_qty) or flt(d.qty), "phantom": cint(d.is_phantom_item), "bom_no": d.bom_no or ""})
			if cint(d.is_phantom_item) and d.bom_no:
				con.add(d.bom_no)
		can_doc = sorted(con - set(ra))
	return ra


def nhac_thieu_nvl_ngay_mai():
	"""Lịch 20:45: nguyên liệu trong kho bếp không đủ làm các yêu cầu cần ngày mai (một tin mỗi bếp)."""
	try:
		from vagabond.kho_san_xuat import NGUYEN_LIEU, ten_kho_cua

		mai = add_days(nowdate(), 1)
		yc = _yeu_cau_ngay(mai, chi_mo=True)
		ma = sorted({m for v in yc.values() for m in v})
		if not ma:
			return
		bom = {i.name: i.default_bom for i in frappe.get_all("Item", filters={"name": ["in", ma]}, fields=["name", "default_bom"])}
		thanh_phan = _cay_bom([b for b in bom.values() if b])
		for bep, mon in sorted(yc.items()):
			kho = ten_kho_cua(bep, NGUYEN_LIEU) if bep else None
			if not kho:
				continue
			can = [{"ma": m, "ten": o["ten"], "sl": o["sl"], "bom": bom.get(m)} for m, o in mon.items()]
			thanh = {d["ma"] for x in can if x["bom"] for d, _ in no_thanh_phan(x["bom"], 1, thanh_phan)}
			ton = {b.item_code: flt(b.actual_qty) for b in frappe.get_all("Bin", filters={"warehouse": kho,
				"item_code": ["in", sorted(thanh) or [""]]}, fields=["item_code", "actual_qty"])}
			thieu, khong_ct = tinh_thieu_nvl(can, thanh_phan, ton)
			if not thieu and not khong_ct:
				continue
			dong = ["%s, ngày %s, kho %s" % (ten_bep(bep), ngay_vn(mai), ten_kho(kho))]
			if thieu:
				dong.append("%d nguyên liệu thiếu:" % len(thieu))
				dong += ["  " + x for x in dong_hang(thieu, toi_da=12)]
			if khong_ct:
				dong.append("Chưa có công thức nên máy chưa tính được: %s" % ", ".join(khong_ct[:8]))
			dong.append("Xin chuyển từ Kho tổng 307 ngay tối nay hoặc báo thu mua.")
			kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Thiếu nguyên liệu cho ngày mai", dong,
				link=_url("/app/material-request/new"), khoa="thieu-nvl:%s:%s" % (bep, mai), ma_tin="bep_thieu_nvl_ngay_mai")
	except Exception:
		_ghi_loi("thiếu nguyên liệu ngày mai")


def nhac_lenh_chua_xong():
	"""Lịch 08:00: lệnh sản xuất bắt đầu từ hôm qua trở về trước mà chưa ghi làm xong (một tin mỗi bếp)."""
	try:
		from vagabond.ke_hoach_sx import TRANG_THAI_XONG
		from vagabond.kho_san_xuat import bep_cua_kho

		hom_nay = nowdate()
		ds = frappe.get_all("Work Order", filters={"docstatus": 1, "status": ["not in", list(TRANG_THAI_XONG)],
			"planned_start_date": ["<", hom_nay]},
			fields=["name", "production_item", "item_name", "qty", "produced_qty", "stock_uom", "fg_warehouse",
				"source_warehouse", "planned_start_date"], order_by="planned_start_date asc", limit_page_length=0)
		theo_bep = {}
		for w in ds:
			if flt(w.produced_qty) >= flt(w.qty) - LECH:
				continue
			bep = bep_cua_kho(w.fg_warehouse) or bep_cua_kho(w.source_warehouse) or ""
			theo_bep.setdefault(bep, []).append("%s: %s, đã làm %s/%s %s, từ %s" % (w.name, w.item_name or w.production_item,
				so(w.produced_qty), so(w.qty), w.stock_uom or "", ngay_vn(w.planned_start_date)))
		for bep, dong in sorted(theo_bep.items()):
			noi = ["%s: %d lệnh" % (ten_bep(bep), len(dong))] + kenh_zalo.cat_dong(dong, 10, "lệnh")
			noi.append("Chưa ghi hoàn tất thì kho chưa có hàng, phiếu xuất sau sẽ báo thiếu tồn. Làm xong thì bấm Hoàn thành phiếu; không làm nữa thì dừng lệnh.")
			kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Lệnh sản xuất quá ngày chưa ghi hoàn tất", noi,
				link=_url("/app/work-order?status=In%20Process"), khoa="lenh-chua-xong:%s:%s" % (bep or "khac", hom_nay),
				ma_tin="bep_lenh_chua_xong")
	except Exception:
		_ghi_loi("lệnh sản xuất chưa xong")
