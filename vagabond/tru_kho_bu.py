# -*- coding: utf-8 -*-
"""v550: trừ kho từng món và trừ bù khi hàng về (anh Việt chốt 01/10/2026).

VÌ SAO CÓ TỆP NÀY
-----------------
v542 trừ kho theo cả tờ: một món thiếu là cả hoá đơn ghi sổ không trừ kho
("Chưa trừ kho"), kể cả những món còn đủ. Ngày 01/10 ở District 1 có 18 tờ
như vậy, phần lớn vì hoá đơn bán lúc 10:10 mà phiếu điều chuyển từ NVHTN tới
14:09 mới nhập. Kho ERP lệch kho thật cho tới khi kế toán xử lý tay.

Anh Việt chọn cách B: trừ kho ngay khi ghi sổ, món nào còn thì trừ món đó,
món nào chưa có thì trừ bù khi hàng về, kèm nút trừ bù bấm tay.

CÁCH LÀM
--------
Hoá đơn bán vẫn đi đúng đường v542 (đủ hàng thì chính hoá đơn trừ kho, giá
vốn 632). Thiếu hàng thì hoá đơn ghi sổ không trừ kho như cũ, rồi NGAY SAU
khi ghi sổ máy lập một Phiếu xuất dùng (Material Issue, mã PXD-) gắn với hoá đơn, xuất
từ kho điểm bán những món đang có, Nợ 632. Phần còn thiếu chờ hàng về:

  - Phiếu kho hay phiếu kiểm kê nhập vào kho điểm bán: máy xếp việc trừ bù
    cho kho đó sau khi phiếu ghi sổ xong (enqueue_after_commit).
  - Nhịp mỗi giờ quét lại phòng khi hàng về bằng đường không có hook.
  - Nút "Trừ bù" trên từng hoá đơn và "Trừ bù cả điểm" trên màn
    Hoá đơn chưa trừ kho.

Số đã trừ của một hoá đơn = tổng các Phiếu xuất dùng còn hiệu lực gắn với nó.
Số cần trừ = nhu_cau_kho của chính hoá đơn. Không lưu số đã trừ ở chỗ thứ hai
(bài học #205: một nguồn, không phải thêm chỗ nhớ gọi).

KHÔNG BAO GIỜ CHẶN BÁN. Mọi lỗi của trừ bù chỉ ghi lý do lên hoá đơn và Error
Log, lùi điểm lưu, hoá đơn vẫn ghi sổ.

WEBSITE
-------
Tab "In store" và tab bánh của order.thevagabondpatisserie.com KHÔNG đọc tồn
ERP. Chúng đọc phiếu Kiểm kho / Kiểm bánh, đếm cả hoá đơn nháp vừa lưu, nên
đã giữ hàng tạm theo thời gian thực từ trước. Trừ bù ở đây không làm website
trừ thêm lần nữa (ca kiểm thu_tru_kho_bu_550 chốt điều này).
"""

# ------------------------------------------------------------ phần thuần

SAI_SO = 0.000001

# Ô vgb_tru_bu trên hoá đơn bán.
BU_MOT_PHAN = "Một phần"
BU_DU = "Đủ"
BU_GO_TAY = "Gỡ tay"
GIA_TRI_BU = ("", BU_MOT_PHAN, BU_DU, BU_GO_TAY)

# Một nguồn cho chip trạng thái trên mọi màn (POS, Doanh thu Sales, Hoá đơn
# bán ra, Hoá đơn chưa trừ kho). Màn hình chỉ đọc khoá, không tự suy.
TT_DA_TRU = "da_tru"
TT_CHUA_TRU = "chua_tru"
TT_MOT_PHAN = "mot_phan"
TT_DA_TRU_BU = "da_tru_bu"

# Tình trạng kho hiện tại của phần còn thiếu, cho màn Hoá đơn chưa trừ kho.
KHO_DU = "kho_du"
KHO_MOT_PHAN = "kho_mot_phan"
KHO_HET = "kho_het"


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def trang_thai_kho(r):
	"""Khoá trạng thái kho của một hoá đơn bán. THUẦN.

	"" là không có chip: nháp, hoá đơn không qua luồng bán trừ kho, hoặc tờ
	không có món theo dõi tồn. Thứ tự xét: còn thiếu trước, rồi mới đến đã
	trừ bù, để tờ đã trừ một phần không bao giờ hiện như đã xong.
	"""
	if not r or int(_so(r.get("docstatus"))) != 1:
		return ""
	bu = (r.get("vgb_tru_bu") or "").strip()
	if int(_so(r.get("vgb_chua_tru_kho"))):
		return TT_MOT_PHAN if bu == BU_MOT_PHAN else TT_CHUA_TRU
	if bu == BU_DU:
		return TT_DA_TRU_BU
	if int(_so(r.get("vgb_tru_kho_ban"))) and int(_so(r.get("update_stock"))):
		return TT_DA_TRU
	return ""


def con_thieu(can, da):
	"""{(mã, kho): số còn phải trừ} sau khi bớt phần đã trừ. THUẦN."""
	ra = {}
	for k in sorted(can):
		c = _so(can[k]) - _so((da or {}).get(k))
		if c > SAI_SO:
			ra[k] = round(c, 6)
	return ra


def ke_hoach(thieu, ton):
	"""Món nào trừ được bao nhiêu ngay lúc này. THUẦN.

	Trừ min(còn thiếu, tồn hiện tại), không bao giờ trừ quá tồn: kho không
	cho âm (Stock Settings allow_negative_stock = 0) và không được làm âm.
	"""
	ra = {}
	for k in sorted(thieu):
		lay = min(_so(thieu[k]), max(0.0, _so((ton or {}).get(k))))
		if lay > SAI_SO:
			ra[k] = round(lay, 6)
	return ra


def gia_tri_bu(da_co_phieu, con_lai):
	"""Giá trị ô vgb_tru_bu sau một lượt trừ bù. THUẦN."""
	if not da_co_phieu:
		return ""
	return BU_MOT_PHAN if con_lai else BU_DU


def nhan_dong(can, da, ton):
	"""Nhãn một món trên màn Hoá đơn chưa trừ kho. THUẦN."""
	thieu = _so(can) - _so(da)
	if thieu <= SAI_SO:
		return "da_tru"
	t = _so(ton)
	if t + SAI_SO >= thieu:
		return "du"
	if t > SAI_SO:
		return "mot_phan"
	return "het"


def nhan_hoa_don(nhan_cac_dong):
	"""Tình trạng kho của cả tờ từ nhãn các món còn thiếu. THUẦN."""
	con = [n for n in nhan_cac_dong if n != "da_tru"]
	if not con:
		return ""
	if all(n == "du" for n in con):
		return KHO_DU
	if any(n in ("du", "mot_phan") for n in con):
		return KHO_MOT_PHAN
	return KHO_HET


def gan_trang_thai(ds):
	"""Gắn khoá tt_kho cho từng dòng danh sách hoá đơn. THUẦN."""
	for r in ds or []:
		r["tt_kho"] = trang_thai_kho(r)
	return ds


def kho_bi_cham(dong_ds, kho_diem):
	"""Kho điểm bán vừa có hàng NHẬP vào từ một phiếu. THUẦN.

	dong_ds: các dòng phiếu (t_warehouse cho Phiếu kho, warehouse cho Phiếu
	kiểm kê, Phiếu nhập kho). Chỉ lấy kho thuộc danh sách kho điểm bán.
	"""
	ra = set()
	for d in dong_ds or []:
		for o in ("t_warehouse", "warehouse"):
			k = d.get(o)
			if k and k in kho_diem:
				ra.add(k)
	return sorted(ra)


# Chip chặng của màn Hoá đơn chưa trừ kho. Hai họ tên khác hẳn nhau để không
# nhầm: "Đã/Chưa trừ" là việc đã xảy ra trên sổ kho của hoá đơn; "Kho ..." là
# tồn HIỆN TẠI của phần còn thiếu, tức bấm Trừ bù lúc này thì được tới đâu.
CHANG = (
	("cho", "Chưa trừ kho", "📦"),
	("kho_du", "Kho đủ để trừ bù", "✅"),
	("kho_mot_phan", "Kho đủ một phần", "🟠"),
	("kho_het", "Kho chưa có hàng", "⛔"),
	("mot_phan", "Đã trừ một phần", "📦"),
	("go_tay", "Phiếu bù bị gỡ tay", "✋"),
	("da_tru_bu", "Đã trừ bù", "🔁"),
)


def thuoc_chang(o, k):
	"""Một tờ (đã gắn tt_kho, kho_nay) có thuộc chip chặng k không. THUẦN."""
	cho = o.get("tt_kho") in (TT_CHUA_TRU, TT_MOT_PHAN)
	if not k:
		return True
	if k == "cho":
		return cho
	if k in (KHO_DU, KHO_MOT_PHAN, KHO_HET):
		return cho and o.get("kho_nay") == k
	if k == "mot_phan":
		return o.get("tt_kho") == TT_MOT_PHAN
	if k == "go_tay":
		return cho and (o.get("vgb_tru_bu") or "") == BU_GO_TAY
	if k == "da_tru_bu":
		return o.get("tt_kho") == TT_DA_TRU_BU
	return False


def dem_chang(ds):
	ra = {"": len(ds or [])}
	for k, _, _ in CHANG:
		ra[k] = len([o for o in ds or [] if thuoc_chang(o, k)])
	return ra


# Hai lớp quyền. Xem: ai làm việc với hoá đơn bán. Trừ bù: người chịu trách
# nhiệm kho và sổ (kế toán, quản lý cửa hàng, giám đốc). Thu ngân xem được
# danh sách của quầy mình nhưng không bấm trừ bù.
QUYEN_TRU = frozenset({"System Manager", "Giám đốc", "Accounts User", "Accounts Manager",
	"VGB - Quản lý cửa hàng"})
QUYEN_XEM = QUYEN_TRU | frozenset({"Sales User", "Sales Manager"})


def duoc(vai, tap):
	return bool(set(vai or ()) & set(tap))


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt, now_datetime

TRUONG_MOI = {
	"Sales Invoice": [
		dict(fieldname="vgb_tru_bu", label="Trừ bù kho", fieldtype="Select",
			options="\n" + "\n".join(GIA_TRI_BU[1:]), read_only=1, no_copy=1,
			in_standard_filter=1, insert_after="vgb_ly_do_chua_tru_kho",
			description="Máy lập Phiếu xuất dùng bù cho món bán lúc kho chưa có hàng. "
				"Một phần: còn món chờ hàng về. Đủ: đã trừ hết. Gỡ tay: có người huỷ phiếu bù, máy không tự trừ lại."),
	],
	"Stock Entry": [
		dict(fieldname="vgb_hd_tru_bu", label="Hoá đơn được trừ bù", fieldtype="Link",
			options="Sales Invoice", read_only=1, no_copy=1, search_index=1,
			insert_after="remarks",
			description="Phiếu xuất dùng máy lập để trừ kho cho hoá đơn bán lúc kho chưa có hàng."),
	],
}


def _kho_diem_ban(si):
	from vagabond import hach_toan_kho as hk
	return hk._kho_diem_ban(si)


def tat_ca_kho_diem():
	from vagabond import diem_ban
	return {d.get("kho_tang") for d in diem_ban.ds() if d.get("kho_tang")}


def _la_hang_ton(ma):
	return bool(ma and frappe.get_cached_value("Item", ma, "is_stock_item"))


def can_cua(si, kho):
	"""Lượng phải trừ theo (mã, kho điểm bán), đúng đơn vị kho của lõi."""
	from vagabond.hach_toan_kho import nhu_cau_kho
	dong = [frappe._dict(item_code=d.item_code, warehouse=kho, stock_qty=d.stock_qty)
		for d in si.get("items") or [] if _la_hang_ton(d.get("item_code"))]
	tp = [frappe._dict(item_code=p.item_code, warehouse=kho, qty=p.qty)
		for p in si.get("packed_items") or [] if _la_hang_ton(p.get("item_code"))]
	return nhu_cau_kho(dong, tp)


def da_tru_cua(ten_si):
	"""{(mã, kho): số} đã trừ qua các Phiếu xuất dùng còn hiệu lực gắn hoá đơn."""
	ra = {}
	for r in frappe.db.sql("""select d.item_code, d.s_warehouse, sum(d.transfer_qty)
		from `tabStock Entry Detail` d join `tabStock Entry` s on s.name = d.parent
		where s.vgb_hd_tru_bu = %s and s.docstatus = 1 and ifnull(d.s_warehouse, '') != ''
		group by d.item_code, d.s_warehouse""", (ten_si,)):
		ra[(r[0], r[1])] = flt(r[2])
	return ra


def _ton(cap, khoa=False):
	from erpnext.stock.utils import get_stock_balance
	ra = {}
	for (ma, kho) in sorted(cap):
		if khoa:
			frappe.db.sql("select name from `tabBin` where item_code=%s and warehouse=%s for update", (ma, kho))
		ra[(ma, kho)] = flt(get_stock_balance(ma, kho))
	return ra


def _ghi_hd(si, gia_tri):
	"""Ghi trạng thái lên hoá đơn đã ghi sổ, cả bản trong bộ nhớ nếu có."""
	frappe.db.set_value("Sales Invoice", si.name, gia_tri, update_modified=False)
	for k, v in gia_tri.items():
		si.set(k, v)


def _tt_chi_phi(si):
	for d in si.get("items") or []:
		if d.get("cost_center"):
			return d.cost_center
	return si.get("cost_center") or frappe.get_cached_value("Company", si.company, "cost_center")


def _lap_phieu(si, kho, tk632, lay, nguon):
	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Issue"
	se.purpose = "Material Issue"
	se.company = si.company
	se.from_warehouse = kho
	se.vgb_hd_tru_bu = si.name
	se.remarks = ("Trừ kho bù cho hoá đơn %s (bán lúc kho chưa có hàng). Lập bởi: %s." % (si.name, nguon))[:1000]
	tt = _tt_chi_phi(si)
	for (ma, k), sl in sorted(lay.items()):
		dvt = frappe.get_cached_value("Item", ma, "stock_uom")
		se.append("items", {"item_code": ma, "s_warehouse": k, "qty": sl, "uom": dvt, "stock_uom": dvt,
			"conversion_factor": 1, "transfer_qty": sl, "expense_account": tk632, "cost_center": tt})
	se.flags.ignore_permissions = True
	se.insert()
	se.submit()
	return se.name


def _lap_cac_phieu(si, kho, tk632, lay, nguon):
	"""Lập phiếu bù cho cả nhóm món; lõi từ chối thì thử TỪNG MÓN một.

	Một món lỗi lô (lô tắt, lô không đủ) không được kéo các món khác về
	"chưa trừ" như v542. Trả về (danh sách phiếu, {(mã, kho): đã lấy}, lỗi).
	"""
	def mot_lan(phan):
		moc = "vgb_bp_" + frappe.generate_hash(length=10)
		frappe.db.savepoint(moc)
		try:
			return _lap_phieu(si, kho, tk632, phan, nguon), None
		except Exception as loi:
			frappe.db.rollback(save_point=moc)
			frappe.clear_last_message()
			if not isinstance(loi, frappe.ValidationError):
				raise
			return None, str(loi) or type(loi).__name__
	ten, loi = mot_lan(lay)
	if ten:
		return [ten], dict(lay), []
	if len(lay) == 1:
		return [], {}, [loi]
	phieu, da_lay, cac_loi = [], {}, []
	for k in sorted(lay):
		ten, loi = mot_lan({k: lay[k]})
		if ten:
			phieu.append(ten)
			da_lay[k] = lay[k]
		else:
			cac_loi.append("%s: %s" % (k[0], loi))
	return phieu, da_lay, cac_loi


def tru_bu(ten_si, nguon="máy", tay=False):
	"""Trừ phần còn thiếu của một hoá đơn bằng tồn hiện có. Không bao giờ ném.

	tay=True: người bấm nút, được trừ lại cả tờ "Gỡ tay". Lượt tự động bỏ
	qua tờ đó để không lập lại phiếu kế toán vừa huỷ có chủ ý.
	"""
	from vagabond import hach_toan_kho as hk
	if frappe.flags.get("vgb_dang_tru_bu"):
		return {"ok": 0, "loi": "Đang trừ bù trong cùng lượt."}
	moc = "vgb_bu_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(moc)
	frappe.flags.vgb_dang_tru_bu = True
	try:
		frappe.db.sql("select name from `tabSales Invoice` where name=%s for update", (ten_si,))
		si = frappe.get_doc("Sales Invoice", ten_si)
		if si.docstatus != 1 or not cint(si.get("vgb_tru_kho_ban")) or not cint(si.get("vgb_chua_tru_kho")):
			return {"ok": 1, "bo_qua": "Hoá đơn không còn chờ trừ kho."}
		bu_cu = si.get("vgb_tru_bu") or ""
		if bu_cu == BU_GO_TAY and not tay:
			return {"ok": 1, "bo_qua": "Phiếu bù đã bị gỡ tay, chờ người bấm Trừ bù."}
		kho = _kho_diem_ban(si)
		if not kho:
			return {"ok": 0, "loi": "Điểm bán chưa khai kho xuất (Cài đặt > Điểm bán)."}
		try:
			tk632 = hk._kiem_cau_hinh(kho, si.company)
		except Exception as loi:
			frappe.clear_last_message()
			return {"ok": 0, "loi": "Cấu hình kho hoặc tài khoản giá vốn chưa hợp lệ: %s" % loi}
		da = da_tru_cua(si.name)
		thieu = con_thieu(can_cua(si, kho), da)
		ton = _ton(thieu, khoa=True)
		lay = ke_hoach(thieu, ton)
		phieu, da_lay, cac_loi = _lap_cac_phieu(si, kho, tk632, lay, nguon) if lay else ([], {}, [])
		con = con_thieu(thieu, da_lay)
		if phieu or not con:
			bu = gia_tri_bu(bool(da) or bool(phieu), con)
		else:
			bu = bu_cu
		gia_tri = {"vgb_tru_bu": bu}
		if con:
			cau = "Còn chờ hàng về: " + hk.ly_do_thieu(
				[(m, k, c, max(0.0, ton.get((m, k), 0) - da_lay.get((m, k), 0))) for (m, k), c in sorted(con.items())])
			if cac_loi:
				cau += ". Lỗi lúc trừ: " + "; ".join(cac_loi)
			gia_tri["vgb_ly_do_chua_tru_kho"] = cau[:1000]
		else:
			gia_tri["vgb_chua_tru_kho"] = 0
			gia_tri["vgb_ly_do_chua_tru_kho"] = "Đã trừ bù đủ lúc %s." % str(now_datetime())[:16]
		_ghi_hd(si, gia_tri)
		return {"ok": 1, "phieu": phieu, "da_tru": {"%s|%s" % k: v for k, v in da_lay.items()},
			"con_thieu": {"%s|%s" % k: v for k, v in con.items()}, "loi_mon": cac_loi}
	except Exception as loi:
		frappe.db.rollback(save_point=moc)
		frappe.clear_last_message()
		cau = str(loi) or type(loi).__name__
		try:
			frappe.db.set_value("Sales Invoice", ten_si, "vgb_ly_do_chua_tru_kho",
				("Trừ bù chưa được: %s" % cau)[:1000], update_modified=False)
		except Exception:
			pass
		if not isinstance(loi, frappe.ValidationError):
			frappe.log_error(frappe.get_traceback(), "tru_kho_bu: %s" % ten_si)
		return {"ok": 0, "loi": cau}
	finally:
		frappe.flags.vgb_dang_tru_bu = False


def _hd_cho(kho=None, tu_dong=True, gioi_han=300):
	"""Hoá đơn đã ghi sổ còn chờ trừ kho, cũ trước, tuỳ chọn theo một kho."""
	from vagabond import hach_toan_kho as hk
	loc = {"docstatus": 1, "vgb_tru_kho_ban": 1, "vgb_chua_tru_kho": 1}
	moc = hk._moc(hk.O_BAN_TU)
	if moc:
		loc["posting_date"] = [">=", moc]
	ds = frappe.get_all("Sales Invoice", filters=loc, fields=["name", "vgb_quay", "vgb_tru_bu"],
		order_by="posting_date asc, posting_time asc, name asc", limit_page_length=gioi_han)
	# Lọc "Gỡ tay" bằng Python: ô Select để trống là NULL, phép != của SQL
	# loại luôn NULL, tức là loại cả những tờ chưa trừ bù lần nào.
	if tu_dong:
		ds = [r for r in ds if (r.vgb_tru_bu or "") != BU_GO_TAY]
	if not kho:
		return [r.name for r in ds]
	return [r.name for r in ds if _kho_diem_ban(r) == kho]


def tru_bu_kho(kho=None, nguon="máy: hàng về kho"):
	"""Việc nền: trừ bù cho mọi hoá đơn chờ của một kho (hoặc mọi kho).

	Ghi sổ từng hoá đơn một lần commit: hỏng tờ sau không làm mất tờ trước.
	"""
	kq = {"xong": 0, "mot_phan": 0, "loi": 0}
	for ten in _hd_cho(kho):
		r = tru_bu(ten, nguon=nguon)
		if not r.get("ok"):
			kq["loi"] += 1
		elif r.get("phieu") and r.get("con_thieu"):
			kq["mot_phan"] += 1
		elif r.get("phieu"):
			kq["xong"] += 1
		frappe.db.commit()
	return kq


def quet_moi_gio():
	tru_bu_kho(None, nguon="máy: nhịp mỗi giờ")


# ------------------------------------------------------------ hook

def khi_ghi_so_hd(doc, method=None):
	"""on_submit Sales Invoice: thiếu hàng thì trừ ngay những món đang có."""
	if not cint(doc.get("vgb_tru_kho_ban")) or not cint(doc.get("vgb_chua_tru_kho")):
		return
	try:
		tru_bu(doc.name, nguon="máy: lúc ghi sổ hoá đơn")
		# Đọc lại trạng thái vào bản trong bộ nhớ cho các hook sau.
		for o in ("vgb_chua_tru_kho", "vgb_ly_do_chua_tru_kho", "vgb_tru_bu"):
			doc.set(o, frappe.db.get_value("Sales Invoice", doc.name, o))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tru_kho_bu: on_submit %s" % doc.name)


def khi_huy_hd(doc, method=None):
	"""on_cancel Sales Invoice: huỷ theo các Phiếu xuất dùng bù, trả hàng về kho.

	Chạy ở on_cancel, trước phép kiểm liên kết ngược của Frappe, nên hoá đơn
	huỷ được mà không bắt người dùng đi huỷ từng phiếu bù.
	"""
	ds = frappe.get_all("Stock Entry", filters={"vgb_hd_tru_bu": doc.name, "docstatus": 1}, pluck="name")
	if not ds:
		return
	frappe.flags.vgb_huy_theo_hd = doc.name
	try:
		for ten in ds:
			se = frappe.get_doc("Stock Entry", ten)
			se.flags.ignore_permissions = True
			se.cancel()
	finally:
		frappe.flags.vgb_huy_theo_hd = None


def khi_huy_phieu(doc, method=None):
	"""on_cancel Stock Entry: phiếu bù bị huỷ tay thì hoá đơn về Chưa trừ kho."""
	ten = doc.get("vgb_hd_tru_bu")
	if not ten or frappe.flags.get("vgb_huy_theo_hd") == ten:
		return
	si = frappe.get_doc("Sales Invoice", ten)
	if si.docstatus != 1:
		return
	kho = _kho_diem_ban(si)
	con = con_thieu(can_cua(si, kho), da_tru_cua(ten)) if kho else {"?": 1}
	gia_tri = {"vgb_tru_bu": BU_GO_TAY}
	if con:
		gia_tri["vgb_chua_tru_kho"] = 1
		gia_tri["vgb_ly_do_chua_tru_kho"] = ("Phiếu xuất dùng bù %s đã bị huỷ lúc %s. Bấm Trừ bù khi cần trừ lại."
			% (doc.name, str(now_datetime())[:16]))
	_ghi_hd(si, gia_tri)


def khi_nhap_kho(doc, method=None):
	"""on_submit Phiếu kho / Phiếu kiểm kê / Phiếu nhập kho vào kho điểm bán.

	Chỉ xếp việc, chạy sau khi phiếu commit xong. Không làm chậm phiếu nhập,
	không để lỗi trừ bù làm hỏng phiếu nhập.
	"""
	if doc.get("vgb_hd_tru_bu"):
		return
	try:
		kho_ds = kho_bi_cham(doc.get("items") or [], tat_ca_kho_diem())
	except Exception:
		return
	for kho in kho_ds:
		frappe.enqueue("vagabond.tru_kho_bu.tru_bu_kho", queue="short", kho=kho,
			job_id="vgb_tru_bu_" + frappe.scrub(kho), deduplicate=True, enqueue_after_commit=True)


# ------------------------------------------------------------ app

def _vai():
	return set(frappe.get_roles())


def _kiem_xem():
	if not duoc(_vai(), QUYEN_XEM):
		frappe.throw("Bạn chưa có quyền xem hoá đơn chưa trừ kho.", frappe.PermissionError)


def _kiem_tru():
	if not duoc(_vai(), QUYEN_TRU):
		frappe.throw("Chỉ kế toán, quản lý cửa hàng hoặc giám đốc được bấm trừ bù.", frappe.PermissionError)


_O_DS = ["name", "posting_date", "posting_time", "customer_name", "grand_total", "vgb_quay",
	"vgb_chua_tru_kho", "vgb_ly_do_chua_tru_kho", "vgb_tru_bu", "vgb_tru_kho_ban", "update_stock", "docstatus"]


def _dung(rows):
	"""Từng tờ kèm từng món: cần, đã trừ, tồn hiện tại, nhãn. Đọc tồn một lượt."""
	from vagabond import diem_ban
	ten_diem = diem_ban.ten_diem()
	tam, cap_ton = [], set()
	for r in rows:
		si = frappe.get_doc("Sales Invoice", r.name)
		kho = _kho_diem_ban(si)
		can = can_cua(si, kho) if kho else {}
		cap_ton.update(can)
		tam.append((r, kho, can, da_tru_cua(r.name)))
	ton = _ton(cap_ton)
	ra = []
	for r, kho, can, da in tam:
		dong = []
		for (ma, k) in sorted(can):
			dong.append({"ma": ma, "ten": frappe.get_cached_value("Item", ma, "item_name") or ma,
				"dvt": frappe.get_cached_value("Item", ma, "stock_uom") or "",
				"can": can[(ma, k)], "da_tru": flt(da.get((ma, k))), "ton": ton.get((ma, k), 0),
				"nhan": nhan_dong(can[(ma, k)], da.get((ma, k)), ton.get((ma, k)))})
		o = dict(r)
		o["tt_kho"] = trang_thai_kho(r)
		o["kho_nay"] = nhan_hoa_don([d["nhan"] for d in dong]) if cint(r.vgb_chua_tru_kho) else ""
		o["diem"] = diem_ban.ma_theo_quay(r.vgb_quay) or "SALES"
		o["ten_diem"] = ten_diem.get(o["diem"], o["diem"])
		o["kho"] = kho
		o["dong"] = dong
		o["phieu"] = frappe.get_all("Stock Entry", filters={"vgb_hd_tru_bu": r.name, "docstatus": 1}, pluck="name")
		ra.append(o)
	return ra


def _tap(diem=None, ky=None, tu=None, den=None, tim=None, tran=None):
	"""Tập đã lọc điểm, ngày, ô tìm; CHƯA lọc chặng (để đếm chip).

	Lọc điểm và ô tìm TRƯỚC khi cắt TRAN dòng: lọc trên tập đã cắt thì tìm
	một hoá đơn cũ sẽ ra rỗng dù nó có thật (bài học #380). Chỉ phần đọc từng
	món (nặng) mới làm trên tập đã cắt.
	"""
	from frappe.utils import nowdate
	from vagabond import diem_ban
	from vagabond import hach_toan_kho as hk
	from vagabond.khung.cong_cu_ds import khoang_ky
	a, b = khoang_ky(ky, nowdate(), tu, den)
	loc = {"docstatus": 1, "vgb_tru_kho_ban": 1}
	moc = hk._moc(hk.O_BAN_TU)
	tu_ngay = max(str(a or ""), str(moc or "")[:10]) or None
	if tu_ngay and b:
		loc["posting_date"] = ["between", [tu_ngay, b]]
	elif tu_ngay:
		loc["posting_date"] = [">=", tu_ngay]
	elif b:
		loc["posting_date"] = ["<=", b]
	q = (tim or "").strip()
	if q:
		mau = "%" + q + "%"
		ten = set(frappe.db.sql_list("""select name from `tabSales Invoice`
			where name like %s or customer_name like %s""", (mau, mau)))
		ten.update(frappe.db.sql_list("""select distinct parent from `tabSales Invoice Item`
			where item_code like %s or item_name like %s""", (mau, mau)))
		loc["name"] = ["in", sorted(ten) or [""]]
	ds = frappe.get_all("Sales Invoice", filters=loc,
		or_filters={"vgb_chua_tru_kho": 1, "vgb_tru_bu": ["in", [BU_DU, BU_MOT_PHAN, BU_GO_TAY]]},
		fields=_O_DS, order_by="posting_date desc, posting_time desc", limit_page_length=0)
	chon = (diem or "").strip().upper()
	if chon:
		ds = [r for r in ds if (diem_ban.ma_theo_quay(r.vgb_quay) or "SALES") == chon]
	tran = TRAN if tran is None else tran
	if not tran:
		return _dung(ds), False
	return _dung(ds[:tran]), len(ds) > tran


TRAN = 500


@frappe.whitelist()
def ds_chua_tru_kho(diem=None, chang="cho", ky=None, tu=None, den=None, tim=None):
	"""Màn Hoá đơn chưa trừ kho: tờ còn chờ, tờ đã trừ bù, tờ gỡ tay."""
	from vagabond import diem_ban
	_kiem_xem()
	tap, bi_cat = _tap(diem, ky, tu, den, tim)
	return {"hd": [o for o in tap if thuoc_chang(o, chang)], "dem": dem_chang(tap), "bi_cat": 1 if bi_cat else 0,
		"chang": [{"k": k, "ten": t, "ic": ic} for k, t, ic in CHANG],
		"duoc_tru": 1 if duoc(_vai(), QUYEN_TRU) else 0,
		"diem": [{"ma": d["ma"], "ten": d["ten_ngan"]} for d in diem_ban.ds(chi_bat=True)]}


def xuat_ds(diem=None, chang="cho", ky=None, tu=None, den=None, tim=None, **khac):
	"""Adapter Xuất Excel: một dòng một món, đúng tập đang lọc trên màn."""
	_kiem_xem()
	# Xuất Excel lấy ĐỦ dòng, không cắt TRAN như màn hình.
	tap, _ = _tap(diem, ky, tu, den, tim, tran=0)
	nhan_tt = {TT_DA_TRU: "Đã trừ kho", TT_CHUA_TRU: "Chưa trừ kho", TT_MOT_PHAN: "Đã trừ một phần",
		TT_DA_TRU_BU: "Đã trừ bù"}
	nhan_mon = {"da_tru": "Đã trừ", "du": "Đủ để trừ", "mot_phan": "Trừ được một phần", "het": "Kho chưa có"}
	dong = []
	for o in tap:
		if not thuoc_chang(o, chang):
			continue
		for d in o["dong"] or [{}]:
			dong.append({"hd": o["name"], "ngay": o["posting_date"], "gio": str(o.get("posting_time") or "")[:5],
				"diem": o["ten_diem"], "tt": nhan_tt.get(o["tt_kho"], ""), "ma": d.get("ma"), "ten": d.get("ten"),
				"dvt": d.get("dvt"), "can": d.get("can"), "da_tru": d.get("da_tru"), "ton": d.get("ton"),
				"mon": nhan_mon.get(d.get("nhan"), ""), "phieu": ", ".join(o["phieu"]),
				"ly_do": o.get("vgb_ly_do_chua_tru_kho") or ""})
	cot = [{"k": "hd", "nhan": "Hoá đơn"}, {"k": "ngay", "nhan": "Ngày", "kieu": "ngay"}, {"k": "gio", "nhan": "Giờ"},
		{"k": "diem", "nhan": "Điểm bán"}, {"k": "tt", "nhan": "Trạng thái kho"}, {"k": "ma", "nhan": "Mã món"},
		{"k": "ten", "nhan": "Tên món"}, {"k": "dvt", "nhan": "Đơn vị"}, {"k": "can", "nhan": "Bán", "kieu": "so"},
		{"k": "da_tru", "nhan": "Đã trừ", "kieu": "so"}, {"k": "ton", "nhan": "Tồn kho hiện tại", "kieu": "so"},
		{"k": "mon", "nhan": "Tình trạng món"}, {"k": "phieu", "nhan": "Phiếu xuất dùng bù"},
		{"k": "ly_do", "nhan": "Lý do"}]
	return "Hoa don chua tru kho", cot, dong


@frappe.whitelist()
def tt_hoa_don(hoa_don):
	"""Khối Kho trên màn chi tiết một hoá đơn."""
	_kiem_xem()
	ds = frappe.get_all("Sales Invoice", filters={"name": hoa_don}, fields=_O_DS)
	if not ds:
		frappe.throw("Không thấy hoá đơn %s." % hoa_don)
	o = _dung(ds)[0]
	o["duoc_tru"] = 1 if duoc(_vai(), QUYEN_TRU) else 0
	return o


@frappe.whitelist()
def dem_chua_tru_kho(diem=None):
	"""Số tờ còn chờ trừ kho, cho huy hiệu trên trang chủ và màn quầy."""
	from vagabond import diem_ban
	_kiem_xem()
	ds = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "vgb_tru_kho_ban": 1, "vgb_chua_tru_kho": 1},
		fields=["vgb_quay"], limit_page_length=0)
	chon = (diem or "").strip().upper()
	if not chon:
		return {"so": len(ds)}
	return {"so": len([r for r in ds if (diem_ban.ma_theo_quay(r.vgb_quay) or "SALES") == chon])}


@frappe.whitelist(methods=["POST"])
def tru_bu_hd(hoa_don):
	"""Nút Trừ bù trên một hoá đơn."""
	_kiem_tru()
	r = tru_bu(hoa_don, nguon=frappe.session.user, tay=True)
	if not r.get("ok"):
		frappe.throw(r.get("loi") or "Chưa trừ bù được.")
	return r


@frappe.whitelist(methods=["POST"])
def tru_bu_diem(diem):
	"""Nút Trừ bù cả điểm: mọi tờ đang chờ của một điểm bán, kể cả tờ gỡ tay."""
	from vagabond import diem_ban
	_kiem_tru()
	d = diem_ban.theo_ma(diem)
	kho = (d or {}).get("kho_tang")
	if not kho:
		frappe.throw("Điểm bán %s chưa khai kho xuất." % (diem or ""))
	kq = {"xong": 0, "mot_phan": 0, "khong_doi": 0, "loi": 0}
	for ten in _hd_cho(kho, tu_dong=False):
		r = tru_bu(ten, nguon=frappe.session.user, tay=True)
		if not r.get("ok"):
			kq["loi"] += 1
		elif r.get("phieu") and r.get("con_thieu"):
			kq["mot_phan"] += 1
		elif r.get("phieu"):
			kq["xong"] += 1
		else:
			kq["khong_doi"] += 1
	return kq
