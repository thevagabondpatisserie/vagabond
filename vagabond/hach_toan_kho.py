"""v542: hạch toán kho theo sơ đồ của Khải, áp dụng từ 01/10/2026.

VÌ SAO CÓ TỆP NÀY, 30/09/2026
--------------------------------------------------------------------
Khải (kế toán giá thành) mở Sổ cái 155 năm 2026 và thấy:

1. Phiếu Sản xuất đi tắt một bước: Nợ 1551 / Có 152. Không qua 621, không
   qua 154, nên xuất sổ 621 và 154 ra không thấy gì để tính giá thành và
   quyết toán. Cột "TK đối ứng" hiện 6328 chỉ vì lõi lấy ô expense_account
   của dòng làm nhãn: dòng nguyên liệu và dòng thành phẩm cùng một tài
   khoản chênh lệch nên hai chân triệt tiêu nhau (ERPNext v16.28.0,
   erpnext/controllers/stock_controller.py get_gl_entries: mỗi dòng ghi một
   chân vào tài khoản kho, một chân vào d.expense_account).
2. Bán hàng chưa bao giờ ghi giá vốn: mọi hoá đơn bán để update_stock = 0
   (ban_hang.py "GIAI DOAN 1"), nên không có Nợ 632 / Có 155 nào.

Anh Việt chốt 30/09/2026:
- Dùng chung 621 và 154, phân biệt bếp bằng Trung tâm chi phí.
- Giá vốn: máy trừ kho theo từng bill, bật từ 01/10/2026.
- Kết chuyển cuối kỳ Nợ 154 / Có 621 và mọi bút toán đặc thù là việc kế
  toán làm tay theo bản chất. Máy không tự kết chuyển.

CƠ CHẾ
--------------------------------------------------------------------
Sản xuất: không vá sổ cái. Chỉ đặt đúng ô expense_account của từng dòng
phiếu, lõi tự ghi:
    dòng nguyên liệu (có kho xuất, không kho nhập): expense_account = 621
        -> Nợ 621 / Có 152
    dòng thành phẩm, phế phẩm (is_finished_item, is_scrap_item): 154
        -> Nợ 1551 / Có 154
Mọi dòng mang Trung tâm chi phí của bếp theo kho (Baker, Pastry, Lab).
Lõi chặn ô chênh lệch là tài khoản loại Stock (stock_entry.py
validate_difference_account), nên 154 phải KHÔNG là loại Stock và không
gắn kho nào. Patch v542 gỡ 154 khỏi hai kho Dở dang (đang không tồn) rồi
bỏ loại Stock của 154. Nhờ vậy kế toán ghi tay Nợ 154 / Có 621 bằng bút
toán tổng hợp được, lõi không chặn "chỉ cập nhật qua giao dịch kho".

Bán hàng: bật update_stock cho hoá đơn bán từ ngày cắt, kho xuất là "Kho
xuất hàng tặng" của điểm bán (Cài đặt > Điểm bán, anh Việt chốt 09/09 bán
và tặng dùng cùng kho điểm bán), tài khoản giá vốn 632. Lô chia theo hạn
dùng như luồng hàng tặng.

KHÔNG BAO GIỜ CHẶN BÁN
--------------------------------------------------------------------
Luật không cho tồn âm vẫn giữ (Stock Settings allow_negative_stock = 0).
Nhưng thu ngân và nhịp Pancake không được đứng vì tồn chưa khớp: hoá đơn
không đủ hàng thì vẫn ghi sổ doanh thu như cũ, KHÔNG trừ kho, đánh dấu
"Chưa trừ kho" kèm lý do để Khải xử lý tay (lọc danh sách Hoá đơn bán theo
ô này). Hai lớp:
  1. Trước ghi sổ: đếm tồn tại ngày ghi, thiếu thì chuyển sang không trừ.
  2. Lõi vẫn báo lỗi kho (lô, tồn tương lai...): HoaDonHangTang._save lùi
     về điểm lưu, đánh dấu và ghi sổ lại MỘT lần không trừ kho. Lỗi lần hai
     là lỗi thật khác, trả nguyên cho người dùng.

Tắt khẩn cấp: xoá ngày trong Vagabond Settings > "Bán trừ kho từ ngày" hoặc
"Sản xuất qua 621/154 từ ngày". Chứng từ đã ghi giữ nguyên.

Phần thuần nằm trên vạch `import frappe` để bộ kiểm tầng khung chạy được
trên máy CI tay không.
"""

import datetime

# phần thuần

NGAY_CAT = "2026-10-01"

SO_621 = "621"
SO_154 = "154"
SO_632 = "632"

# Kho -> trung tâm chi phí. Tên kho bếp theo nếp "<Bếp> - <chức năng> - TV"
# (kho_san_xuat.TEN_KHO); Lab là kho lẻ "Kho Lab - TV".
TIEN_TO_BEP = (
	("baker -", "Bếp Baker"),
	("pastry -", "Bếp Pastry"),
	("kho lab", "Sonneto Lab"),
)

O_SX_TU = "vgb_sx_621_tu"
O_BAN_TU = "vgb_ban_tru_kho_tu"


def _ngay(v):
	if not v:
		return None
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	try:
		return datetime.date.fromisoformat(str(v)[:10])
	except ValueError:
		return None


def ap_dung(ngay_ghi, moc):
	"""Chứng từ ghi từ ngày mốc trở đi. Mốc trống là tắt."""
	m, n = _ngay(moc), _ngay(ngay_ghi)
	return bool(m and n and n >= m)


def ten_tt_chi_phi_bep(kho):
	"""Tên gốc (chưa hậu tố công ty) của trung tâm chi phí theo kho, hoặc None."""
	t = (kho or "").strip().lower()
	for tien_to, ten in TIEN_TO_BEP:
		if t.startswith(tien_to):
			return ten
	return None


def vai_dong_sx(dong):
	"""'nguyen_lieu', 'thanh_pham' hoặc None cho một dòng phiếu Sản xuất."""
	if dong.get("is_finished_item") or dong.get("is_scrap_item"):
		return "thanh_pham"
	if dong.get("s_warehouse") and not dong.get("t_warehouse"):
		return "nguyen_lieu"
	return None


def _dat(d, k, v):
	if isinstance(d, dict):
		d[k] = v
	else:
		d.set(k, v)


def gan_tai_khoan_sx(dong_ds, tk621, tk154, tt_theo_kho):
	"""Đặt expense_account và cost_center cho từng dòng phiếu Sản xuất.

	tt_theo_kho: hàm kho -> tên trung tâm chi phí đầy đủ hoặc None.
	Dòng không nhận ra vai trò thì để nguyên. Trả về số dòng đã đặt.
	Trung tâm của dòng thành phẩm theo kho nhập; không nhận ra thì theo bếp
	của nguyên liệu (một phiếu một bếp).
	"""
	tt_phieu = None
	for d in dong_ds:
		if vai_dong_sx(d) == "nguyen_lieu":
			tt_phieu = tt_phieu or tt_theo_kho(d.get("s_warehouse"))
	dem = 0
	for d in dong_ds:
		vai = vai_dong_sx(d)
		if not vai:
			continue
		_dat(d, "expense_account", tk621 if vai == "nguyen_lieu" else tk154)
		kho = d.get("s_warehouse") if vai == "nguyen_lieu" else d.get("t_warehouse")
		tt = tt_theo_kho(kho) or tt_phieu
		if tt:
			_dat(d, "cost_center", tt)
		dem += 1
	return dem


def tra_tai_khoan_cu(dong_ds, tk_moi, tai_khoan_cu):
	"""Codex #397: phiếu Sản xuất KHÔNG áp dụng 621/154 thì trả về tài khoản cũ.

	Nháp lưu lúc đang bật đã mang 621/154 trong từng dòng. Kế toán tắt khẩn
	(xoá ngày) hoặc đổi ngày ghi về trước mốc thì lần lưu/ghi sổ sau vẫn
	đi 621/154 nếu chỉ return sớm. Dòng nào đang mang một trong tk_moi thì
	đặt lại bằng tai_khoan_cu(dong) (cách lõi tự điền); trả None thì để nguyên.
	Trả về số dòng đã trả.
	"""
	dem = 0
	for d in dong_ds:
		if d.get("expense_account") not in tk_moi:
			continue
		cu = tai_khoan_cu(d)
		if cu and cu not in tk_moi:
			_dat(d, "expense_account", cu)
			dem += 1
	return dem


def thieu_hang(can, ton):
	"""can, ton: {(mã, kho): số}. Trả danh sách (mã, kho, cần, còn) còn thiếu."""
	ra = []
	for k in sorted(can):
		c, t = float(can[k] or 0), float(ton.get(k) or 0)
		if c > 0 and t + 0.000001 < c:
			ra.append((k[0], k[1], c, t))
	return ra


def ly_do_thieu(ds):
	return "; ".join("%s tại %s cần %g, còn %g" % (m, k, c, t) for m, k, c, t in ds[:8]) + (
		" (và %d món khác)" % (len(ds) - 8) if len(ds) > 8 else "")


def co_phieu_giao(dong_ds):
	"""Hoá đơn lập từ Phiếu giao hàng: kho và giá vốn đã ghi ở phiếu giao."""
	return any(d.get("delivery_note") or d.get("dn_detail") for d in dong_ds or [])


def du_dieu_kien_ban(hd, moc, la_tang, dong_ds=None):
	"""Hoá đơn bán thường, ghi từ ngày mốc, thì trừ kho.

	Codex #395 F1: hoá đơn lập từ Phiếu giao hàng (xuất bán sỉ, xuat_ban.py)
	đã trừ kho và ghi giá vốn ở phiếu giao; trừ lần nữa là trừ hai lần.
	"""
	if not ap_dung(hd.get("posting_date"), moc):
		return False
	if hd.get("is_return") or hd.get("is_debit_note") or hd.get("is_opening") == "Yes":
		return False
	if la_tang or hd.get("vgb_tang_kho_moi"):
		return False
	if co_phieu_giao(dong_ds if dong_ds is not None else hd.get("items")):
		return False
	return True


import frappe
from frappe.utils import cint, flt

TRUONG_MOI = {
	"Sales Invoice": [
		dict(fieldname="vgb_tru_kho_ban", label="Bán trừ kho (v542)", fieldtype="Check",
			read_only=1, no_copy=1, hidden=1, insert_after="vgb_tang_kho"),
		dict(fieldname="vgb_chua_tru_kho", label="Chưa trừ kho", fieldtype="Check",
			read_only=1, no_copy=1, in_standard_filter=1, insert_after="vgb_tru_kho_ban",
			description="Hoá đơn ghi sổ doanh thu nhưng không trừ kho vì thiếu hàng tại kho điểm bán. Kế toán xử lý tay."),
		dict(fieldname="vgb_ly_do_chua_tru_kho", label="Lý do chưa trừ kho", fieldtype="Small Text",
			read_only=1, no_copy=1, depends_on="eval:doc.vgb_chua_tru_kho", insert_after="vgb_chua_tru_kho"),
	],
	"Vagabond Settings": [
		dict(fieldname="vgb_sec_hach_toan_kho", label="Hạch toán kho (v542)", fieldtype="Section Break",
			insert_after="hang_tang_xuat_kho_that"),
		dict(fieldname=O_BAN_TU, label="Bán trừ kho từ ngày", fieldtype="Date",
			insert_after="vgb_sec_hach_toan_kho",
			description="Hoá đơn bán ghi từ ngày này tự trừ kho điểm bán và ghi giá vốn 632. Để trống là tắt."),
		dict(fieldname=O_SX_TU, label="Sản xuất qua 621/154 từ ngày", fieldtype="Date",
			insert_after=O_BAN_TU,
			description="Phiếu Sản xuất ghi từ ngày này: Nợ 621 / Có 152 và Nợ 155 / Có 154, trung tâm chi phí theo bếp. Để trống là tắt."),
	],
}


def _moc(o):
	try:
		return frappe.db.get_single_value("Vagabond Settings", o)
	except Exception:
		return None


def _tk(cong_ty, so, goc):
	from vagabond.hang_tang_so_cai import tai_khoan
	return tai_khoan(cong_ty, so, goc)


def _tt_theo_kho_cua(cong_ty):
	hau_to = frappe.get_cached_value("Company", cong_ty, "abbr")
	cache = {}

	def tra(kho):
		ten = ten_tt_chi_phi_bep(kho)
		if not ten:
			return None
		if ten not in cache:
			day_du = "%s - %s" % (ten, hau_to)
			cache[ten] = day_du if frappe.db.exists("Cost Center",
				{"name": day_du, "is_group": 0, "company": cong_ty}) else None
		return cache[ten]
	return tra


# ------------------------------------------------------------ sản xuất

def sx_gan_tai_khoan(doc, method=None):
	"""Hook validate của Stock Entry, chạy SAU validate của lõi.

	Codex #397: mọi nhánh không gắn 621/154 đều trả dòng về tài khoản cũ,
	để nháp lưu lúc đang bật rồi tắt ngày (hay lùi ngày ghi) không lọt 621/154.
	"""
	if doc.docstatus == 2 or doc.get("purpose") != "Manufacture":
		return
	if not _sx_gan_moi(doc):
		_tra_ve_luong_cu(doc)


def _tk_moi_cua(cong_ty):
	return set(frappe.get_all("Account", filters={"company": cong_ty,
		"account_number": ["in", [SO_621, SO_154]]}, pluck="name"))


def _tra_ve_luong_cu(doc):
	try:
		tk_moi = _tk_moi_cua(doc.company)
	except Exception:
		return 0
	if not tk_moi:
		return 0

	def cu(d):
		try:
			ct = doc.get_item_details(frappe._dict(item_code=d.get("item_code"), company=doc.company,
				project=doc.get("project"), uom=d.get("uom"), s_warehouse=d.get("s_warehouse"),
				is_finished_item=d.get("is_finished_item")))
		except Exception:
			return None
		return (ct or {}).get("expense_account")
	return tra_tai_khoan_cu(doc.get("items") or [], tk_moi, cu)


def _sx_gan_moi(doc):
	"""Gắn 621/154 nếu áp dụng được. Trả True khi đã gắn."""
	if not ap_dung(doc.get("posting_date"), _moc(O_SX_TU)):
		return False
	from erpnext import is_perpetual_inventory_enabled
	if not is_perpetual_inventory_enabled(doc.company):
		return False
	try:
		tk621 = _tk(doc.company, SO_621, "Expense")
		tk154 = _tk(doc.company, SO_154, "Asset")
	except frappe.ValidationError as loi:
		# Không bao giờ chặn sản xuất vì thiếu cấu hình tài khoản: giữ luồng
		# cũ và nhắc kế toán (bench CI 30/09: công ty không có 621).
		frappe.clear_last_message()
		frappe.msgprint("Phiếu này chưa ghi qua 621/154: %s" % loi, indicator="orange", alert=1)
		return False
	if frappe.db.get_value("Account", tk154, "account_type") == "Stock":
		# Lõi chặn ô chênh lệch loại Tồn kho. Không chặn sản xuất: giữ luồng
		# cũ và nhắc kế toán (patch v542 chưa gỡ được 154 vì kho còn tồn).
		frappe.msgprint("Tài khoản 154 còn là loại Tồn kho nên phiếu này chưa ghi qua 621/154. "
			"Kế toán gỡ 154 khỏi các kho Dở dang và bỏ loại Tồn kho của 154.", indicator="orange", alert=1)
		return False
	gan_tai_khoan_sx(doc.get("items") or [], tk621, tk154, _tt_theo_kho_cua(doc.company))
	return True


# ------------------------------------------------------------ bán hàng

def _kho_diem_ban(doc):
	from vagabond import diem_ban
	d = diem_ban.theo_ma(diem_ban.ma_theo_quay(doc.get("vgb_quay")))
	return (d or {}).get("kho_tang") or ""


def _hang_ton(doc):
	return [d for d in doc.get("items") or []
		if d.get("item_code") and frappe.get_cached_value("Item", d.item_code, "is_stock_item")]


def _bo_tru_kho(doc, ly_do):
	doc.update_stock = 0
	doc.vgb_chua_tru_kho = 1
	doc.vgb_ly_do_chua_tru_kho = (ly_do or "")[:1000]
	for d in doc.get("items") or []:
		if d.get("serial_and_batch_bundle"):
			d.serial_and_batch_bundle = None


def _la_tang(doc):
	from vagabond.minvoice_an_toan import la_hang_tang
	return la_hang_tang(doc)


def _ghi_so_lien_tuc(cong_ty):
	from erpnext import is_perpetual_inventory_enabled
	return bool(is_perpetual_inventory_enabled(cong_ty))


def _la_bo(ma):
	return bool(ma and frappe.db.exists("Product Bundle", {"new_item_code": ma, "disabled": 0}))


def _kiem_cau_hinh(kho, cong_ty):
	"""Tài khoản 632 nếu kho và tài khoản hợp lệ; lỗi thì ném."""
	from vagabond.hang_tang_kho import kiem_kho
	kiem_kho(kho, cong_ty)
	return _tk(cong_ty, SO_632, "Expense")


def ban_chuan_bi(doc):
	"""Gọi từ HoaDonHangTang.set_missing_values, SAU hang_tang_kho.chuan_bi."""
	if not doc.meta.has_field("vgb_tru_kho_ban"):
		return
	if doc.docstatus == 2 or getattr(doc, "_action", None) == "update_after_submit":
		return
	if not doc.is_new():
		cu = frappe.db.get_value("Sales Invoice", doc.name, "docstatus")
		if cu and cu != 0:
			return
	if doc.flags.get("vgb_lui_tru_kho"):
		# Lượt ghi sổ lại sau lỗi của lõi (HoaDonHangTang._save): giữ dấu.
		doc.update_stock = 0
		return
	if doc.get("vgb_chua_tru_kho"):
		# Codex #395 F4: dấu "Chưa trừ kho" chỉ chốt lúc ghi sổ. Tờ nháp lưu
		# lại thì tính lại từ đầu, cấu hình đã sửa thì trừ kho bình thường.
		doc.vgb_chua_tru_kho = 0
		doc.vgb_ly_do_chua_tru_kho = None
	if cint(doc.get("update_stock")) and not doc.get("vgb_tru_kho_ban"):
		# Người lập tự bật "Cập nhật kho" và chọn kho/lô trên Desk: tôn trọng,
		# không đổi kho, không đè tài khoản (bench 489: SI tự trừ kho có lô).
		return
	du = du_dieu_kien_ban(doc, _moc(O_BAN_TU), _la_tang(doc), doc.get("items") or [])
	if du:
		du = _ghi_so_lien_tuc(doc.company)
	if not du:
		dong_ds = doc.get("items") or []
		if (ap_dung(doc.get("posting_date"), _moc(O_BAN_TU)) and co_phieu_giao(dong_ds)
				and any(not (d.get("delivery_note") or d.get("dn_detail")) and d.get("item_code")
					and frappe.get_cached_value("Item", d.item_code, "is_stock_item") for d in dong_ds)):
			# Codex #395 F6: tờ trộn dòng từ Phiếu giao hàng với dòng thêm tay.
			# Không trừ kho cả tờ (tránh trừ hai lần dòng đã giao), nhưng đánh
			# dấu để kế toán xử lý dòng thêm tay, không để lọt im lặng.
			doc.vgb_chua_tru_kho = 1
			doc.vgb_ly_do_chua_tru_kho = ("Hoá đơn trộn dòng lập từ Phiếu giao hàng với dòng hàng thêm tay; "
				"dòng thêm tay chưa trừ kho, kế toán xử lý hoặc tách hoá đơn.")
		if doc.get("vgb_tru_kho_ban"):
			# Đổi ngày, đổi sang trả hàng hay hàng tặng: trả về luồng cũ.
			doc.vgb_tru_kho_ban = 0
			if not doc.get("vgb_tang_kho_moi"):
				doc.update_stock = 0
		return
	doc.vgb_tru_kho_ban = 1
	# Codex #395 F3: dòng bộ sản phẩm (món cha không theo tồn, thành phần
	# nằm ở packed_items) cũng phải trừ kho theo thành phần.
	hang = [d for d in doc.get("items") or [] if d.get("item_code") and (
		frappe.get_cached_value("Item", d.item_code, "is_stock_item") or _la_bo(d.item_code))]
	if not hang:
		doc.update_stock = 0
		return
	kho = _kho_diem_ban(doc)
	if not kho:
		_bo_tru_kho(doc, "Điểm bán chưa khai kho xuất (Cài đặt > Điểm bán).")
		return
	try:
		tk632 = _kiem_cau_hinh(kho, doc.company)
	except Exception as loi:
		frappe.clear_last_message()
		_bo_tru_kho(doc, "Cấu hình kho hoặc tài khoản giá vốn chưa hợp lệ: %s" % loi)
		return
	doc.update_stock = 1
	for d in hang:
		if d.warehouse != kho:
			d.warehouse = kho
			d.batch_no = None
			d.serial_and_batch_bundle = None
		d.expense_account = tk632


def ban_truoc_ghi_so(doc, method=None):
	"""before_submit: thiếu hàng thì ghi sổ không trừ kho, không chặn bán."""
	if not doc.get("vgb_tru_kho_ban"):
		return
	from vagabond.minvoice_an_toan import la_hang_tang
	if la_hang_tang(doc):
		# Phương thức vừa đổi sang Hàng tặng sau validate: trả về luồng tặng,
		# không để cờ bán trừ kho làm hang_tang_so_cai chặn ghi sổ.
		doc.vgb_tru_kho_ban = 0
		if not doc.get("vgb_tang_kho_moi"):
			doc.update_stock = 0
		return
	if not cint(doc.update_stock):
		return
	nhom = {}
	for d in _hang_ton(doc):
		nhom[(d.item_code, d.warehouse)] = nhom.get((d.item_code, d.warehouse), 0) + flt(d.stock_qty)
	for p in doc.get("packed_items") or []:
		if p.get("item_code") and frappe.get_cached_value("Item", p.item_code, "is_stock_item"):
			k = (p.item_code, p.warehouse)
			nhom[k] = nhom.get(k, 0) + flt(p.qty) * flt(p.get("conversion_factor") or 1)
	from erpnext.stock.utils import get_stock_balance
	ton = {}
	for (ma, kho) in sorted(nhom):
		frappe.db.sql("select name from `tabBin` where item_code=%s and warehouse=%s for update", (ma, kho))
		ton[(ma, kho)] = flt(get_stock_balance(ma, kho, doc.posting_date, doc.posting_time)) if kho else 0
	thieu = thieu_hang(nhom, ton)
	if thieu:
		_bo_tru_kho(doc, "Thiếu hàng: " + ly_do_thieu(thieu))
		return
	from vagabond.hang_tang_kho import chia_lo_xuat
	try:
		chia_lo_xuat(doc, {k for k in nhom if any(d.item_code == k[0] and d.warehouse == k[1]
			for d in doc.get("items") or [])})
	except frappe.ValidationError as loi:
		frappe.clear_last_message()
		_bo_tru_kho(doc, "Lô không đủ: %s" % loi)


def co_the_lui(doc, loi):
	"""Được ghi sổ lại một lần không trừ kho sau lỗi của lõi hay không."""
	if not doc.get("vgb_tru_kho_ban") or not cint(doc.get("update_stock")) or doc.get("vgb_chua_tru_kho"):
		return False
	ten = type(loi).__name__
	if ten in ("QueryDeadlockError", "QueryTimeoutError", "TimestampMismatchError",
			"PermissionError", "DocstatusTransitionError"):
		return False
	return True
