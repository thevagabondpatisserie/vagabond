# -*- coding: utf-8 -*-
"""Màn Nguyên liệu thay thế trên Desk: cột tên, cột đếm BOM, chip cảnh báo.

Khải đề nghị 28/08/2026: bảng Mặt hàng thay thế chỉ hiện mã, không hiện
tên, nên phải mở từng dòng mới biết đang khai loại nào. Anh Việt giao thêm:
dựng luôn các cột và chip lọc hữu ích nhất để Khải làm nhanh và ít nhầm.

VÌ SAO CẦN NHIỀU HƠN MỘT CỘT TÊN
================================

Đo trên site ngày 28/08/2026, 11 cặp thay thế đang khai đều là bơ lạt và
kem tươi, bảy mã cả thảy. Bốn điều nhìn ra ngay từ dữ liệu thật:

* Chỉ HAI trong bảy mã còn tồn kho. Năm mã còn lại tồn 0, tức khai thay thế
  vào đó thì tới lúc cần thay vẫn không có hàng mà thay.
* BA mã chưa có giá vốn, nghĩa là chưa từng nhập lô nào. Thay một nguyên
  liệu đang có giá bằng một mã giá 0 là kéo giá vốn thành phẩm tụt xuống mà
  không ai thấy.
* Giá vốn giữa các mã chênh nhau thật: bơ Anchor 252 đồng một gram, bơ
  Avonmore 230, kem Lescure 165 so với kem Pauls 120. Thay xong giá vốn đổi
  vài phần trăm tới vài chục phần trăm.
* Mã NVLT00242 đang nằm trong 128 dòng công thức. Sửa một cặp thay thế của
  nó là chạm tới 128 chỗ.

Không cái nào trong bốn điều đó nhìn được từ màn danh sách cũ.

CÁCH LÀM, VÀ VÌ SAO KHÔNG DÙNG CLIENT SCRIPT
============================================

Cả bảng này chạy bằng TRƯỜNG TỰ THÊM khai trong mã nguồn, không một dòng
Client Script nào. Lý do đã ghi trong tài liệu rà soát 27/08: hệ đang có 43
Client Script sống trong cơ sở dữ liệu, git không quản, không ca kiểm nào
soi, và đó chính là nguồn của mọi vụ lệch giữa app và Desk.

Trường Data mang sẵn ký tự cảnh báo thì hiện thẳng ra danh sách mà không
cần vẽ gì, và trường có `in_standard_filter` thì thành chip lọc ngay trên
thanh bộ lọc của Desk. Đủ dùng, và git quản được trọn vẹn.

Số liệu được tính lại ở hai thời điểm: lúc lưu một cặp, và mỗi đêm một lần
cho cả bảng. Phải có nhịp đêm vì tồn kho, giá vốn và số công thức đổi hằng
ngày mà không ai mở lại cặp thay thế để lưu.
"""

import frappe
from frappe.utils import cint, flt

# Ngưỡng chênh giá vốn coi là đáng để người ta nhìn. Dưới mức này thì thay
# qua thay lại không làm giá thành phẩm nhúc nhích đáng kể.
NGUONG_LECH_GIA = 10.0

# Mức cảnh báo, xếp nặng dần. Tên tiếng Việt vì Khải đọc chứ không phải máy.
MUC_DUNG_DUOC = "Dùng được"
MUC_CAN_XEM = "Cần xem"
MUC_CHAN = "Không thay được"

MUC = (MUC_DUNG_DUOC, MUC_CAN_XEM, MUC_CHAN)

# Mã cảnh báo -> (câu cho người đọc, mức). Thứ tự trong bảng này cũng là
# thứ tự kể ra trong ô chi tiết.
CANH_BAO = {
	"lech_don_vi": ("Hai mã khác đơn vị tính, thay vào là sai số lượng", MUC_CHAN),
	"mon_tat": ("Món thay thế đã ngừng dùng trong danh mục", MUC_CHAN),
	"goc_khong_cho_thay": ("Món gốc chưa bật cho phép dùng hàng thay thế", MUC_CHAN),
	"het_hang": ("Món thay thế đang hết hàng ở mọi kho", MUC_CAN_XEM),
	"chua_co_gia": ("Món thay thế chưa có giá vốn, chưa từng nhập lô nào", MUC_CAN_XEM),
	"lech_gia": ("Giá vốn chênh trên %d phần trăm" % int(NGUONG_LECH_GIA), MUC_CAN_XEM),
	"chua_dung_bom": ("Món gốc chưa nằm trong công thức nào", MUC_CAN_XEM),
}


# ------------------------------------------------------------- phần thuần


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def lech_gia_phan_tram(gia_goc, gia_tt):
	"""Giá vốn món thay thế lệch bao nhiêu phần trăm so với món gốc. THUẦN.

	Trả None khi một trong hai bên chưa có giá - lúc đó không có gì để so,
	và nói "lệch 100 phần trăm" là nói sai bản chất.
	"""
	a, b = _so(gia_goc), _so(gia_tt)
	if a <= 0 or b <= 0:
		return None
	return (b - a) / a * 100.0


def soat_cap(goc, tt, so_bom=0):
	"""Soi một cặp thay thế, trả danh sách mã cảnh báo. THUẦN.

	goc, tt  dict một món: {uom, tat, gia, ton, cho_thay}
	so_bom   số dòng công thức đang dùng món gốc

	Thứ tự kể ra bám theo bảng CANH_BAO, không theo thứ tự phát hiện, để
	hai lần chạy trên cùng dữ liệu luôn cho ra cùng một chuỗi.
	"""
	goc = goc or {}
	tt = tt or {}
	co = set()
	u1 = str(goc.get("uom") or "").strip()
	u2 = str(tt.get("uom") or "").strip()
	if u1 and u2 and u1 != u2:
		co.add("lech_don_vi")
	if cint(tt.get("tat")):
		co.add("mon_tat")
	# Ô "cho phép dùng hàng thay thế" nằm trên món GỐC. Chưa bật thì ERPNext
	# không đề nghị hàng thay thế lúc phát lệnh, khai ở đây cũng nằm im.
	if goc.get("cho_thay") is not None and not cint(goc.get("cho_thay")):
		co.add("goc_khong_cho_thay")
	if _so(tt.get("ton")) <= 0:
		co.add("het_hang")
	if _so(tt.get("gia")) <= 0:
		co.add("chua_co_gia")
	else:
		l = lech_gia_phan_tram(goc.get("gia"), tt.get("gia"))
		if l is not None and abs(l) >= NGUONG_LECH_GIA:
			co.add("lech_gia")
	if not cint(so_bom):
		co.add("chua_dung_bom")
	return [m for m in CANH_BAO if m in co]


def muc_cua(ds_canh_bao):
	"""Mức nặng nhất trong đám cảnh báo. THUẦN."""
	muc = MUC_DUNG_DUOC
	for m in ds_canh_bao or []:
		if CANH_BAO.get(m, ("", MUC_DUNG_DUOC))[1] == MUC_CHAN:
			return MUC_CHAN
		muc = MUC_CAN_XEM
	return muc


def cau_tom_tat(ds_canh_bao):
	"""Một dòng ngắn hiện ngay trên danh sách. THUẦN."""
	if not ds_canh_bao:
		return "Dùng được"
	chu = {
		"lech_don_vi": "lệch đơn vị",
		"mon_tat": "món đã tắt",
		"goc_khong_cho_thay": "gốc chưa cho thay",
		"het_hang": "hết hàng",
		"chua_co_gia": "chưa có giá",
		"lech_gia": "lệch giá",
		"chua_dung_bom": "chưa vào công thức",
	}
	return ", ".join(chu.get(m, m) for m in ds_canh_bao)


def cau_chi_tiet(ds_canh_bao):
	"""Mỗi cảnh báo một dòng, cho ô chi tiết trong phiếu. THUẦN."""
	if not ds_canh_bao:
		return "Cặp thay thế này dùng được, không có gì phải xem lại."
	return "\n".join("- " + CANH_BAO[m][0] for m in ds_canh_bao if m in CANH_BAO)


def chu_ton(ton, uom):
	"""Con số tồn kho viết cho người đọc. THUẦN."""
	t = _so(ton)
	if t <= 0:
		return "Hết hàng"
	return "{:,.0f} {}".format(t, (uom or "").strip()).strip()


def chu_lech_gia(gia_goc, gia_tt):
	"""Chênh giá vốn viết cho người đọc. THUẦN."""
	if _so(gia_tt) <= 0:
		return "Chưa có giá"
	l = lech_gia_phan_tram(gia_goc, gia_tt)
	if l is None:
		return "Chưa so được"
	if abs(l) < 0.5:
		return "Ngang giá"
	return "%s%.1f%%" % ("+" if l > 0 else "", l)


# ------------------------------------------------------- phần chạm hệ


def _tin_mon(ds_ma):
	"""Đọc một lượt mọi thứ cần biết về các mã: đơn vị, giá, tồn, cờ."""
	ra = {}
	ds_ma = [m for m in set(ds_ma or []) if m]
	if not ds_ma:
		return ra
	for it in frappe.get_all(
		"Item",
		filters={"name": ["in", ds_ma]},
		fields=["name", "item_name", "stock_uom", "disabled",
			"allow_alternative_item", "valuation_rate", "last_purchase_rate"],
	):
		ra[it.name] = {
			"ten": it.item_name or it.name,
			"uom": it.stock_uom,
			"tat": it.disabled,
			"cho_thay": it.allow_alternative_item,
			"gia": flt(it.valuation_rate) or flt(it.last_purchase_rate),
			"ton": 0.0,
		}
	# Tồn cộng dồn mọi kho. Giá vốn thật của kho đè lên giá trên danh mục:
	# giá kho mới là con số đang đi vào giá thành phẩm.
	for b in frappe.get_all(
		"Bin",
		filters={"item_code": ["in", ds_ma]},
		fields=["item_code", "actual_qty", "valuation_rate"],
	):
		d = ra.get(b.item_code)
		if not d:
			continue
		d["ton"] = d["ton"] + flt(b.actual_qty)
		if flt(b.valuation_rate) > 0:
			d["gia"] = flt(b.valuation_rate)
	return ra


def _dem_bom(ds_ma):
	"""Mỗi mã nằm trong bao nhiêu công thức ĐANG DÙNG.

	Chỉ đếm BOM đã ghi sổ và còn hoạt động. Đếm cả bản nháp và bản cũ thì
	con số phồng lên, Khải nhìn tưởng sửa một cặp là chạm hàng trăm công
	thức trong khi phần lớn đã nghỉ.
	"""
	ra = dict((m, 0) for m in set(ds_ma or []) if m)
	if not ra:
		return ra
	dong = frappe.get_all(
		"BOM Item",
		filters={"item_code": ["in", list(ra)], "docstatus": 1},
		fields=["item_code", "parent"],
	)
	if not dong:
		return ra
	cha = set(d.parent for d in dong)
	song = set(
		frappe.get_all(
			"BOM",
			filters={"name": ["in", list(cha)], "docstatus": 1, "is_active": 1},
			pluck="name",
		)
	)
	for d in dong:
		if d.parent in song:
			ra[d.item_code] = ra.get(d.item_code, 0) + 1
	return ra


def _tinh_cho(doc, tin, dem):
	"""Điền các ô tính toán cho một bản ghi Item Alternative."""
	g = tin.get(doc.get("item_code")) or {}
	t = tin.get(doc.get("alternative_item_code")) or {}
	so_bom = dem.get(doc.get("item_code"), 0)
	ds = soat_cap(g, t, so_bom)
	doc.vgb_ten_mon = g.get("ten") or ""
	doc.vgb_ten_thay_the = t.get("ten") or ""
	doc.vgb_so_bom = so_bom
	doc.vgb_ton_thay_the = chu_ton(t.get("ton"), t.get("uom"))
	doc.vgb_lech_gia = chu_lech_gia(g.get("gia"), t.get("gia"))
	doc.vgb_muc = muc_cua(ds)
	doc.vgb_tom_tat = cau_tom_tat(ds)
	doc.vgb_chi_tiet = cau_chi_tiet(ds)
	doc.vgb_het_hang = 1 if "het_hang" in ds else 0
	doc.vgb_lech_don_vi = 1 if "lech_don_vi" in ds else 0
	return ds


def khi_luu(doc, method=None):
	"""Hook validate trên Item Alternative: tính lại ngay lúc lưu."""
	try:
		ma = [doc.get("item_code"), doc.get("alternative_item_code")]
		_tinh_cho(doc, _tin_mon(ma), _dem_bom([doc.get("item_code")]))
	except Exception:
		# Hỏng phép soi thì KHÔNG được chặn người ta lưu cặp thay thế. Đây
		# là ô trợ giúp, không phải hàng rào.
		frappe.log_error(frappe.get_traceback(), "nvl_thay_the: khi luu")


def quet_lai(im_lang=True):
	"""Tính lại cả bảng. Chạy mỗi đêm, và bấm tay được từ Desk.

	Tồn kho, giá vốn và số công thức đổi hằng ngày mà không ai mở lại cặp
	thay thế để lưu, nên không có nhịp này thì các ô tính toán đứng im ở
	con số của ngày khai.

	Ghi thẳng bằng db_set chứ không save(): các ô này đều là ô máy tính,
	không có luật nghiệp vụ nào bám vào, mà save() sẽ đội version và bắn
	thông báo cho mọi người theo dõi bản ghi.
	"""
	ds = frappe.get_all(
		"Item Alternative",
		fields=["name", "item_code", "alternative_item_code"],
		limit_page_length=0,
	)
	if not ds:
		return {"so_dong": 0}
	tin = _tin_mon([r.item_code for r in ds] + [r.alternative_item_code for r in ds])
	dem = _dem_bom([r.item_code for r in ds])
	dem_muc = {}
	for r in ds:
		try:
			doc = frappe.get_doc("Item Alternative", r.name)
			_tinh_cho(doc, tin, dem)
			for o in ("vgb_ten_mon", "vgb_ten_thay_the", "vgb_so_bom",
					"vgb_ton_thay_the", "vgb_lech_gia", "vgb_muc",
					"vgb_tom_tat", "vgb_chi_tiet", "vgb_het_hang",
					"vgb_lech_don_vi"):
				frappe.db.set_value("Item Alternative", r.name, o, doc.get(o),
					update_modified=False)
			dem_muc[doc.vgb_muc] = dem_muc.get(doc.vgb_muc, 0) + 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "nvl_thay_the: quet %s" % r.name)
	frappe.db.commit()
	return {"so_dong": len(ds), "theo_muc": dem_muc}


def quet_tu_dong():
	"""Nhịp đêm. Bọc lỗi để một bảng hỏng không kéo đổ cả lượt chạy lịch."""
	try:
		quet_lai()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nvl_thay_the: quet tu dong")


@frappe.whitelist()
def tinh_lai():
	"""Bấm tay từ Desk khi vừa nhập hàng xong và muốn thấy số mới ngay."""
	if not ({"System Manager", "Manufacturing Manager", "Stock Manager", "Item Manager"}
			& set(frappe.get_roles())):
		frappe.throw("Chỉ quản lý kho, sản xuất hoặc danh mục mới tính lại được bảng này.")
	return quet_lai()


# --------------------------------------------------------- trường tự thêm

TRUONG_MOI = {
	"Item Alternative": [
		{
			"fieldname": "vgb_ten_mon",
			"label": "Tên món",
			"fieldtype": "Data",
			"insert_after": "item_code",
			"read_only": 1,
			"in_list_view": 1,
			"in_standard_filter": 0,
			"no_copy": 1,
			"description": "Máy điền theo mã món, không gõ tay.",
		},
		{
			"fieldname": "vgb_ten_thay_the",
			"label": "Tên món thay thế",
			"fieldtype": "Data",
			"insert_after": "alternative_item_code",
			"read_only": 1,
			"in_list_view": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "vgb_sec_soat",
			"label": "Máy soát cặp thay thế này",
			"fieldtype": "Section Break",
			"insert_after": "two_way",
			"collapsible": 0,
		},
		{
			"fieldname": "vgb_muc",
			"label": "Tình trạng",
			"fieldtype": "Select",
			"options": "\n".join(("",) + MUC),
			"insert_after": "vgb_sec_soat",
			"read_only": 1,
			"in_list_view": 1,
			"in_standard_filter": 1,
			"no_copy": 1,
			"description": (
				"Không thay được nghĩa là khai xong cũng không dùng được. "
				"Cần xem nghĩa là thay được nhưng có chỗ phải cân nhắc."
			),
		},
		{
			"fieldname": "vgb_tom_tat",
			"label": "Máy soát thấy",
			"fieldtype": "Data",
			"insert_after": "vgb_muc",
			"read_only": 1,
			"in_list_view": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "vgb_ton_thay_the",
			"label": "Tồn món thay thế",
			"fieldtype": "Data",
			"insert_after": "vgb_tom_tat",
			"read_only": 1,
			"no_copy": 1,
			"description": "Cộng dồn mọi kho, tính lại mỗi đêm.",
		},
		{
			"fieldname": "vgb_col_soat",
			"fieldtype": "Column Break",
			"insert_after": "vgb_ton_thay_the",
		},
		{
			"fieldname": "vgb_lech_gia",
			"label": "Chênh giá vốn",
			"fieldtype": "Data",
			"insert_after": "vgb_col_soat",
			"read_only": 1,
			"no_copy": 1,
			"description": "Giá món thay thế so với món gốc.",
		},
		{
			"fieldname": "vgb_so_bom",
			"label": "Số công thức đang dùng món gốc",
			"fieldtype": "Int",
			"insert_after": "vgb_lech_gia",
			"read_only": 1,
			"no_copy": 1,
			"description": "Chỉ đếm công thức đã ghi sổ và còn hoạt động.",
		},
		{
			"fieldname": "vgb_het_hang",
			"label": "Món thay thế hết hàng",
			"fieldtype": "Check",
			"insert_after": "vgb_so_bom",
			"read_only": 1,
			"in_standard_filter": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "vgb_lech_don_vi",
			"label": "Lệch đơn vị tính",
			"fieldtype": "Check",
			"insert_after": "vgb_het_hang",
			"read_only": 1,
			"in_standard_filter": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "vgb_chi_tiet",
			"label": "Chi tiết",
			"fieldtype": "Small Text",
			"insert_after": "vgb_lech_don_vi",
			"read_only": 1,
			"no_copy": 1,
		},
	],
}
