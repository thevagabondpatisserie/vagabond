# -*- coding: utf-8 -*-
"""v619: tin tuần "Dữ liệu hao hụt" cho nhóm kế toán (anh Việt duyệt mẫu 28/10/2026).

Anh Việt muốn kế toán kiểm soát hao hụt (thực dùng so với công thức), vì hao hụt
chiếm phần lớn giá vốn. Rà site 28/10/2026 (claude/ra-du-lieu-hao-hut-bom): chưa
đủ dữ liệu để tính. Hoàn tất lệnh trừ nguyên liệu ĐÚNG theo công thức, nên hao
hụt thật chỉ đo được bằng kiểm kê kho bếp; mà kho bếp ít khi được đếm, bếp Pastry
ghi ít lệnh, bếp ghi số thực tế bằng đúng số làm, giá vốn một món lệch nhau giữa
các kho. Bước 1 (tin này): mỗi sáng thứ Hai báo kế toán các chỗ còn thiếu để Khải
và bếp sửa. Bước 2 (tin hao hụt quy ra tiền) chỉ làm khi đã có vài tuần đếm đều.

Năm phần, mỗi phần chỉ hiện khi có việc:
  1. Bánh bán ra trong tuần mà 14 ngày gần đây không có lệnh sản xuất.
  2. Lệnh hoàn tất ghi số thực tế bằng đúng số làm (từ 5 lệnh và 90% trở lên):
     cả bếp không cân, không phải một mẻ tình cờ đủ số.
  3. Kho bếp quá 7 ngày chưa kiểm kê, hay lần kiểm cuối dưới 5 dòng.
  4. Nguyên liệu trong công thức đang dùng có giá vốn lệch nhau từ 3 lần giữa các kho.
  5. Bán thành phẩm trong công thức mà chưa có công thức riêng; số công thức đã khai
     phần trăm hao hụt cho phép.
Tuần nào đủ hết thì tin chỉ còn một dòng "Dữ liệu tuần này đủ để tính hao hụt".

Mỗi phép tính là hàm THUẦN để kiểm thử không cần site. Phần đọc dữ liệu nuốt lỗi
(Error Log "Vagabond: tin kho hao hụt"), không làm hỏng lịch khác.
"""

from vagabond.tin_kho import ngay_vn, so

NGAY_SX_XET = 14
SO_LENH_TOI_THIEU = 5
TY_LE_KHONG_CAN = 0.9
NGAY_CHUA_DEM = 7
DONG_DEM_TOI_THIEU = 5
LAN_LECH_GIA = 3.0
LECH = 0.0005
TIEN_TO_KHO_BEP = ("Baker", "Pastry", "Kho Lab")
DVT_NGAN = {"gram": "g", "gam": "g", "g": "g", "ml": "ml", "milliliter": "ml", "kg": "kg", "lít": "lít", "lit": "lít"}


# ------------------------------------------------------------------ THUẦN

def _f(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def ten_kho_ngan(kho):
	"""THUẦN: "Pastry - Thành phẩm - TV" -> "Pastry thành phẩm"; "Kho Lab - TV" -> "Lab";
	"Kho tổng 307 - TV" -> "Kho tổng 307"."""
	t = str(kho or "").strip()
	if t.endswith(" - TV"):
		t = t[:-5]
	phan = [p.strip() for p in t.split(" - ") if p.strip()]
	if not phan:
		return ""
	# "Kho D1", "Kho Lab" bỏ chữ Kho; "Kho tổng 307" giữ nguyên (bỏ thì còn "tổng 307").
	dau = phan[0][4:] if phan[0].startswith("Kho ") and phan[0][4:5].isupper() else phan[0]
	return " ".join([dau] + [p[:1].lower() + p[1:] for p in phan[1:]])


def ten_bep_kho(kho):
	"""THUẦN: tên bếp (hay điểm) của một kho thành phẩm: "Baker - Thành phẩm - TV" -> "Baker"."""
	return ten_kho_ngan(kho).split(" ")[0] if ten_kho_ngan(kho) else ""


def la_kho_bep(kho):
	"""THUẦN: kho của ba bếp (Baker, Pastry, Lab), nơi cần đếm để biết thực dùng."""
	return str(kho or "").startswith(TIEN_TO_KHO_BEP)


def ten_gon(ten, toi_da=5, don_vi="món"):
	"""THUẦN: "A, B, C và 4 món khác" (tối đa toi_da tên)."""
	ds = [str(x) for x in (ten or []) if str(x or "").strip()]
	if len(ds) <= toi_da:
		return ", ".join(ds)
	return "%s và %d %s khác" % (", ".join(ds[:toi_da]), len(ds) - toi_da, don_vi)


def mon_ban_chua_lenh(ban, da_lam):
	"""THUẦN: món tự làm bán trong tuần mà không có lệnh sản xuất gần đây.

	ban: [{"ma","ten","sl"}] món có công thức đang dùng, đã bán trong tuần;
	da_lam: tập mã có phiếu hoàn tất lệnh trong NGAY_SX_XET ngày. Trả
	{"mon","cai","tong_mon","tong_cai","ds":[(tên, số)]}, bán nhiều nhất lên đầu."""
	gom = {}
	for b in ban or []:
		ma = b.get("ma")
		if not ma:
			continue
		o = gom.setdefault(ma, {"ten": (b.get("ten") or ma).strip(), "sl": 0.0})
		o["sl"] += _f(b.get("sl"))
	thieu = [(v["ten"], v["sl"]) for m, v in gom.items() if m not in (da_lam or set()) and v["sl"] > LECH]
	thieu.sort(key=lambda x: (-x[1], x[0]))
	return {"mon": len(thieu), "cai": sum(x[1] for x in thieu), "tong_mon": sum(1 for v in gom.values() if v["sl"] > LECH),
		"tong_cai": sum(v["sl"] for v in gom.values() if v["sl"] > LECH), "ds": thieu}


def lenh_khong_can(phieu):
	"""THUẦN: phiếu hoàn tất lệnh có số thực tế bằng đúng số làm.

	phieu: [{"kho","lam","thuc_te"}] với lam = số làm theo lệnh, thuc_te = số nhập kho.
	Trả None khi chưa đủ dấu hiệu (dưới SO_LENH_TOI_THIEU lệnh, hay dưới TY_LE_KHONG_CAN):
	vài mẻ đủ số là chuyện thường. Có thì {"bang","tong","theo_bep":[(bếp, số)]}."""
	ds = [p for p in phieu or [] if _f(p.get("lam")) > LECH]
	if len(ds) < SO_LENH_TOI_THIEU:
		return None
	bang = [p for p in ds if abs(_f(p.get("lam")) - _f(p.get("thuc_te"))) <= LECH]
	if len(bang) < TY_LE_KHONG_CAN * len(ds):
		return None
	dem = {}
	for p in bang:
		b = ten_bep_kho(p.get("kho")) or "Khác"
		dem[b] = dem.get(b, 0) + 1
	return {"bang": len(bang), "tong": len(ds), "theo_bep": sorted(dem.items(), key=lambda x: (-x[1], x[0]))}


def kho_chua_dem(kho_bep, lan_cuoi, moc):
	"""THUẦN: kho bếp chưa đếm đủ.

	kho_bep: [tên kho]; lan_cuoi: {kho: {"ngay", "dong"}} của lần kiểm kê đã ghi sổ gần nhất;
	moc: ngày cuối của tuần báo (Chủ nhật), để số trong tin khớp với tuần ghi ở tiêu đề.
	Một kho cần nhắc khi chưa đếm lần nào, lần cuối quá NGAY_CHUA_DEM ngày, hay lần cuối
	dưới DONG_DEM_TOI_THIEU dòng. Trả [chuỗi], kho chưa đếm lần nào lên đầu, rồi cũ nhất."""
	from datetime import date as _d

	def _ngay(x):
		if isinstance(x, _d):
			return x
		return _d.fromisoformat(str(x)[:10])

	hn = _ngay(moc)
	ra = []
	for k in kho_bep or []:
		lc = (lan_cuoi or {}).get(k) or {}
		ten = ten_kho_ngan(k)
		if not lc.get("ngay"):
			ra.append((0, _d.min, "%s chưa kiểm lần nào" % ten))
			continue
		n = _ngay(lc["ngay"])
		dong = int(_f(lc.get("dong")))
		if (hn - n).days > NGAY_CHUA_DEM:
			ra.append((1, n, "%s từ %s" % (ten, ngay_vn(n)) + (" (chỉ %d dòng)" % dong if dong < DONG_DEM_TOI_THIEU else "")))
		elif dong < DONG_DEM_TOI_THIEU:
			ra.append((1, n, "%s %s (chỉ %d dòng)" % (ten, ngay_vn(n), dong)))
	ra.sort(key=lambda x: (x[0], x[1], x[2]))
	return [x[2] for x in ra]


def _don_gia(gia, dvt):
	d = DVT_NGAN.get(str(dvt or "").strip().lower(), str(dvt or "").strip())
	g = _f(gia)
	return "%s đ/%s" % (so(round(g)) if g >= 1 else so(round(g, 2)), d)


def gia_lech_kho(bin_ds):
	"""THUẦN: nguyên liệu có giá vốn lệch nhau từ LAN_LECH_GIA lần giữa các kho.

	bin_ds: [{"ma","ten","dvt","kho","gia"}] dòng tồn dương, giá dương. Trả [chuỗi], lệch
	nhiều nhất lên đầu, dạng "Gelatin 13 đ/g (Baker, Pastry) và 333 đ/g (Lab)"."""
	gom = {}
	for b in bin_ds or []:
		if _f(b.get("gia")) <= 0 or not b.get("ma"):
			continue
		gom.setdefault(b["ma"], []).append(b)
	ra = []
	for ma, ds in gom.items():
		thap, cao = min(_f(x["gia"]) for x in ds), max(_f(x["gia"]) for x in ds)
		if thap <= 0 or cao < LAN_LECH_GIA * thap:
			continue
		# Kho nào gần giá thấp hay giá cao hơn thì xếp vào nhóm đó (lệch dưới 5% coi như một giá).
		kho_thap = sorted(ten_kho_ngan(x["kho"]) for x in ds if _f(x["gia"]) <= thap * 1.05)
		kho_cao = sorted(ten_kho_ngan(x["kho"]) for x in ds if _f(x["gia"]) >= cao * 0.95)
		ten, dvt = (ds[0].get("ten") or ma).strip(), ds[0].get("dvt")
		ra.append((cao / thap, "%s %s (%s) và %s (%s)" % (ten, _don_gia(thap, dvt), ", ".join(kho_thap),
			_don_gia(cao, dvt), ", ".join(kho_cao))))
	ra.sort(key=lambda x: (-x[0], x[1]))
	return [x[1] for x in ra]


def bo_tien_to_btp(ten):
	"""THUẦN: "BTP Brown Butter" -> "Brown Butter"."""
	t = str(ten or "").strip()
	for tt in ("NBTP ", "BTP "):
		if t.upper().startswith(tt):
			return t[len(tt):].strip()
	return t


def soan(tu, den, ban, khong_can, chua_dem, lech_gia, btp_khong_ct, so_ct, so_ct_co_hh, link=None):
	"""THUẦN: toàn văn tin (chuỗi). ban là kết quả mon_ban_chua_lenh, khong_can của lenh_khong_can,
	chua_dem của kho_chua_dem, lech_gia của gia_lech_kho, btp_khong_ct là [tên bán thành phẩm]."""
	dong = []
	if ban and ban.get("mon"):
		dong.append("Bánh bán ra chưa có lệnh sản xuất: %d/%d món, %s/%s cái. Nhiều nhất: %s." % (
			ban["mon"], ban["tong_mon"], so(ban["cai"]), so(ban["tong_cai"]),
			ten_gon(["%s %s" % (t, so(s)) for t, s in ban["ds"]], 5)))
	if khong_can:
		dong.append("Hoàn tất lệnh không cân: %d/%d lệnh ghi số cân bằng đúng số làm theo lệnh (%s)." % (
			khong_can["bang"], khong_can["tong"], ", ".join("%s %d" % x for x in khong_can["theo_bep"])))
	if chua_dem:
		dong.append("Kho bếp lâu chưa kiểm kê: %s." % "; ".join(chua_dem))
	if lech_gia:
		# Tên nguyên liệu có dấu phẩy ("Gelatin Powder A250 bloom, VMC") nên tách món bằng chấm phẩy.
		gia = "; ".join(lech_gia[:3]) + (" và %d món khác" % (len(lech_gia) - 3) if len(lech_gia) > 3 else "")
		dong.append("Giá vốn một món lệch nhau giữa các kho từ %d lần trở lên: %s." % (int(LAN_LECH_GIA), gia))
	thieu_hh = so_ct and so_ct_co_hh < so_ct
	if btp_khong_ct or thieu_hh:
		phan = []
		if btp_khong_ct:
			phan.append("%d bán thành phẩm chưa có công thức (%s)" % (len(btp_khong_ct),
				ten_gon([bo_tien_to_btp(x) for x in btp_khong_ct], 8)))
		if thieu_hh:
			phan.append("%d/%d công thức có %% hao hụt cho phép" % (so_ct_co_hh, so_ct))
		dong.append("Công thức: %s." % "; ".join(phan))

	ra = ["📊 BẢN TIN: Dữ liệu hao hụt tuần %s - %s" % (ngay_vn(tu), ngay_vn(den))]
	if not dong:
		ra.append("Dữ liệu tuần này đủ để tính hao hụt.")
	else:
		ra.append("Chưa đủ dữ liệu để tính hao hụt. Còn %d chỗ cần sửa:" % len(dong))
		ra += ["- " + d for d in dong]
		ra.append("Phụ trách: Khải (giá vốn, công thức); bếp Pastry, Baker (lệnh, số cân, kiểm kê)")
		ra.append("Hạn: trước bản tin thứ Hai tới")
	if link:
		ra.append("Mở: %s" % link)
	return "\n".join(ra)


# ------------------------------------------------------------- phần chạm Frappe

def _doc_du_lieu(tu, den):
	import frappe
	from frappe.utils import add_days

	ban = frappe.db.sql("""select sii.item_code ma, max(sii.item_name) ten, sum(sii.stock_qty) sl
		from `tabSales Invoice Item` sii join `tabSales Invoice` si on si.name = sii.parent
		where si.docstatus = 1 and si.posting_date between %(tu)s and %(den)s
			and exists (select 1 from `tabBOM` b where b.item = sii.item_code and b.is_default = 1
				and b.is_active = 1 and b.docstatus = 1)
		group by sii.item_code""", {"tu": tu, "den": den}, as_dict=True)
	da_lam = set(frappe.db.sql_list("""select distinct d.item_code from `tabStock Entry Detail` d
		join `tabStock Entry` s on s.name = d.parent
		where s.docstatus = 1 and s.purpose = 'Manufacture' and d.is_finished_item = 1
			and s.posting_date between %(tu)s and %(den)s""", {"tu": add_days(den, -(NGAY_SX_XET - 1)), "den": den}))
	phieu = frappe.db.sql("""select d.t_warehouse kho, s.fg_completed_qty lam, d.transfer_qty thuc_te
		from `tabStock Entry` s join `tabStock Entry Detail` d on d.parent = s.name and d.is_finished_item = 1
		where s.docstatus = 1 and s.purpose = 'Manufacture' and s.posting_date between %(tu)s and %(den)s""",
		{"tu": tu, "den": den}, as_dict=True)
	kho_bep = [k for k in frappe.get_all("Warehouse", filters={"is_group": 0, "disabled": 0}, pluck="name")
		if la_kho_bep(k)]
	lan_cuoi = {}
	for r in frappe.db.sql("""select i.warehouse kho, s.name, s.posting_date ngay, count(*) dong
			from `tabStock Reconciliation` s join `tabStock Reconciliation Item` i on i.parent = s.name
			where s.docstatus = 1 and s.purpose = 'Stock Reconciliation' and s.posting_date <= %(den)s
			group by i.warehouse, s.name, s.posting_date order by s.posting_date, s.name""", {"den": den}, as_dict=True):
		lan_cuoi[r.kho] = {"ngay": r.ngay, "dong": r.dong}
	bins = frappe.db.sql("""select x.item_code ma, i.item_name ten, i.stock_uom dvt, x.warehouse kho, x.valuation_rate gia
		from `tabBin` x join `tabItem` i on i.name = x.item_code
		where x.actual_qty > 0 and x.valuation_rate > 0 and x.item_code in (
			select bi.item_code from `tabBOM Item` bi join `tabBOM` b on b.name = bi.parent
			where b.is_default = 1 and b.is_active = 1 and b.docstatus = 1)
			and not exists (select 1 from `tabBOM` b2 where b2.item = x.item_code and b2.docstatus = 1)""", as_dict=True)
	btp = frappe.db.sql_list("""select distinct i.item_name from `tabBOM Item` bi
		join `tabBOM` b on b.name = bi.parent join `tabItem` i on i.name = bi.item_code
		where b.is_default = 1 and b.is_active = 1 and b.docstatus = 1
			and (bi.item_code like 'BTP%%' or bi.item_code like 'NBTP%%')
			and not exists (select 1 from `tabBOM` b2 where b2.item = bi.item_code and b2.is_active = 1
				and b2.docstatus = 1)
		order by i.item_name""")
	so_ct, co_hh = frappe.db.sql("""select count(*), sum(case when ifnull(process_loss_percentage, 0) > 0 then 1 else 0 end)
		from `tabBOM` where docstatus = 1 and is_active = 1""")[0]
	return {"ban": ban, "da_lam": da_lam, "phieu": phieu, "kho_bep": kho_bep, "lan_cuoi": lan_cuoi,
		"bins": bins, "btp": btp, "so_ct": int(so_ct or 0), "co_hh": int(co_hh or 0)}


def tin_tuan(hom_nay=None):
	"""Toàn văn tin của tuần (thứ Hai tới Chủ nhật) ngay trước hom_nay. Không gửi."""
	from frappe.utils import add_days, getdate, nowdate

	from vagabond import lien_ket_app

	hn = getdate(hom_nay or nowdate())
	tu, den = add_days(hn, -7), add_days(hn, -1)
	d = _doc_du_lieu(tu, den)
	return soan(tu, den, mon_ban_chua_lenh(d["ban"], d["da_lam"]), lenh_khong_can(d["phieu"]),
		kho_chua_dem(d["kho_bep"], d["lan_cuoi"], den), gia_lech_kho(d["bins"]), d["btp"], d["so_ct"], d["co_hh"],
		link=lien_ket_app.link("/bao-cao"))


def gui_tuan():
	"""Lịch thứ Hai 08:00: gửi tin "Dữ liệu hao hụt" của tuần trước vào nhóm đã tích tin này."""
	from frappe.utils import nowdate

	from vagabond import kenh_zalo
	from vagabond.tin_kho import _ghi_loi

	try:
		hom_nay = nowdate()
		chu = tin_tuan(hom_nay)
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "kho", "Dữ liệu hao hụt", [], noi_dung=chu,
			khoa="du-lieu-hao-hut:%s" % hom_nay, ma_tin="kt_du_lieu_hao_hut")
	except Exception:
		_ghi_loi("hao hụt")
