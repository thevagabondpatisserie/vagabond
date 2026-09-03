"""Chuyển cách nổ bán thành phẩm sang cờ Phantom CHÍNH THỨC của ERPNext.

Vì sao (rà soát 03/09/2026, đo trên site thật)
--------------------------------------------------------------------------
Ngày 25/08 tiệm chuyển 139 mã bán thành phẩm sang "phantom" theo cách tự
chế: đặt is_stock_item = 0 cho mã, dòng công thức cha giữ bom_no và
do_not_explode = 0. ERPNext không biết cách này. Khi lệnh sản xuất nổ MỘT
cấp (use_multi_level_bom = 0), hàm get_bom_items_as_dict của ERPNext lọc
theo điều kiện `item.is_stock_item = 1 OR bom_item.is_phantom_item = 1`, nên
mọi dòng bán thành phẩm bị BỎ IM LẶNG khỏi bảng nguyên liệu. Hoàn tất vẫn
báo thành công, bột trứng đường bên trong kem, nhân, cốt không bị trừ.

Đo ngày 03/09: cờ phantom.trang_thai đang trả 0 vì còn đúng MỘT mã
(BTPB00024) chưa chuyển, nên toàn bộ lệnh từ app đều nổ một cấp. Và 74 trên
116 công thức thành phẩm, ruột bánh, bánh khuôn có bảng nổ chứa lá là mã
không quản tồn hoặc mã đã tắt (Gelatine mass 62 lần, Egg yolk 13 lần...),
nên phiếu kho hoàn tất sẽ bị ERPNext từ chối. Chưa có lệnh nào từng hoàn
tất được trên hệ: 47 lệnh, 46 huỷ, 0 hoàn tất, 0 phiếu Manufacture ghi sổ.

Cách sửa: dùng đúng cờ của ERPNext. BOM của mã phantom mang is_phantom_bom
= 1, dòng công thức cha trỏ vào nó mang is_phantom_item = 1. Khi đó ERPNext
tự đệ quy vào công thức con ở CẢ HAI chế độ nổ (bom.py, nhánh
`if item.get("is_phantom_item")`), và Kế hoạch sản xuất tự bỏ mã phantom
khỏi bảng bán thành phẩm cần làm.

Bảng nổ (BOM Explosion Item) phải dựng lại TỪ DƯỚI LÊN: công thức cha đọc
bảng nổ đã lưu của công thức con chứ không tính lại, nên dựng cha trước con
là cha giữ lá cũ. Đợt 25/08 dựng theo thứ tự tên, đó là lý do Gelatine mass
nằm trong Mirror Glaze vẫn là lá của 62 bánh.

Hàm này LẶP LẠI ĐƯỢC: chạy lần hai không đổi gì thêm. Hỏng ở bước nào thì
ghi nhật ký rồi đi tiếp, KHÔNG ném lỗi ra ngoài để không chặn migrate.
"""

import frappe
from frappe.utils import cint


CHANG_BTP = "BTP thành phần"
CHANG_GIU_TON = ("Ruột bánh (C1)", "Bánh khuôn (C2)")
# Hai mã tách trứng. Đã bị tắt trước đây vì lệnh đòi tồn của chúng; nay là
# phantom nổ về trứng nguyên quả theo đúng tỷ lệ bếp khai trong công thức.
MA_TRUNG = ("BTPB00045", "BTPB00046")


# ------------------------------------------------------------- phép thuần


def thu_tu_dung_lai(con_cua):
	"""Thứ tự dựng lại bảng nổ: CON TRƯỚC, CHA SAU. THUẦN.

	`con_cua` là dict: tên BOM -> danh sách tên BOM con mà nó trỏ vào. Trả
	về danh sách tên BOM sao cho mọi BOM đứng sau tất cả BOM con của nó.
	Vòng lặp (A trỏ B, B trỏ A) thì không treo: mỗi BOM ra đúng một lần,
	BOM đang xét dở được coi như xong để cắt vòng.
	"""
	ra, xong, dang = [], set(), set()

	def di(b):
		if b in xong or b in dang:
			return
		dang.add(b)
		for c in con_cua.get(b) or []:
			if c in con_cua:
				di(c)
		dang.discard(b)
		xong.add(b)
		ra.append(b)

	for b in sorted(con_cua):
		di(b)
	return ra


def la_hong(la, phantom, tat):
	"""Lá nào của bảng nổ sẽ làm phiếu kho chết. THUẦN.

	`la` là danh sách mã trong bảng nổ, `phantom` là tập mã không quản tồn,
	`tat` là tập mã đã tắt. Trả về danh sách mã hỏng, giữ thứ tự, không lặp.
	"""
	ra, thay = [], set()
	for m in la or []:
		if (m in phantom or m in tat) and m not in thay:
			thay.add(m)
			ra.append(m)
	return ra


# ---------------------------------------------------------- chạm hệ thống


def _log(tieu_de, noi_dung):
	try:
		frappe.log_error(noi_dung, tieu_de)
	except Exception:
		pass


def _khong_co_so_kho(ma):
	return not frappe.db.exists("Stock Ledger Entry", {"item_code": ma, "is_cancelled": 0})


def _bom_mac_dinh(ma):
	return frappe.db.get_value("BOM", {"item": ma, "docstatus": 1, "is_active": 1,
		"is_default": 1}, "name")


def execute():
	kq = {"ma_doi": [], "trung": [], "bom_phantom": 0, "dong_phantom": 0,
		"dong_giu_ton": 0, "dung_lai": 0, "hong_dung_lai": [], "la_hong": {}}
	try:
		_chuyen_ma_con_lai(kq)
	except Exception:
		_log("patches: no phantom chuan - buoc ma", frappe.get_traceback())
	try:
		_mo_lai_trung(kq)
	except Exception:
		_log("patches: no phantom chuan - buoc trung", frappe.get_traceback())
	try:
		_gan_co_phantom(kq)
	except Exception:
		_log("patches: no phantom chuan - buoc co", frappe.get_traceback())
	try:
		_dung_lai_bang_no(kq)
	except Exception:
		_log("patches: no phantom chuan - buoc dung lai", frappe.get_traceback())
	try:
		_kiem_lai(kq)
	except Exception:
		_log("patches: no phantom chuan - buoc kiem", frappe.get_traceback())
	frappe.db.commit()
	frappe.clear_cache()
	_log("patches: no phantom chuan - ket qua", frappe.as_json(kq))


def _cac_bom_dang_chay():
	return frappe.get_all("BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["name", "item", "custom_chang", "is_phantom_bom"], limit_page_length=0)


def _chuyen_ma_con_lai(kq):
	"""Mã chặng BTP thành phần còn theo tồn, chưa có bút toán kho nào, thì
	chuyển sang không quản tồn. Đúng việc phantom.chuyen đang làm, chạy lại
	cho những mã lọt lưới (BTPB00024 ngày 03/09)."""
	for b in _cac_bom_dang_chay():
		if b.custom_chang != CHANG_BTP:
			continue
		if not cint(frappe.db.get_value("Item", b.item, "is_stock_item")):
			continue
		if not _khong_co_so_kho(b.item):
			continue
		frappe.db.set_value("Item", b.item, "is_stock_item", 0, update_modified=False)
		frappe.clear_document_cache("Item", b.item)
		kq["ma_doi"].append(b.item)


def _mo_lai_trung(kq):
	"""Egg white, Egg yolk: mở lại mã, không quản tồn, bật công thức tách
	trứng làm mặc định. Hai mã này đang bị tắt mà vẫn nằm trong công thức
	Castella, kéo theo 15 công thức bánh không hoàn tất được."""
	for ma in MA_TRUNG:
		if not frappe.db.exists("Item", ma):
			continue
		gt = {}
		if cint(frappe.db.get_value("Item", ma, "disabled")):
			gt["disabled"] = 0
		if cint(frappe.db.get_value("Item", ma, "is_stock_item")) and _khong_co_so_kho(ma):
			gt["is_stock_item"] = 0
		if gt:
			frappe.db.set_value("Item", ma, gt, update_modified=False)
			frappe.clear_document_cache("Item", ma)
		if not _bom_mac_dinh(ma):
			bom = frappe.db.get_value("BOM", {"item": ma, "docstatus": 1},
				"name", order_by="creation desc")
			if bom:
				frappe.db.set_value("BOM", bom, {"is_active": 1, "is_default": 1},
					update_modified=False)
				frappe.db.set_value("Item", ma, "default_bom", bom, update_modified=False)
		kq["trung"].append({"ma": ma, "doi": gt, "bom": _bom_mac_dinh(ma)})


def _gan_co_phantom(kq):
	"""Cờ phantom chính thức của ERPNext, ở BOM và ở dòng công thức cha."""
	boms = _cac_bom_dang_chay()
	phantom = {b.item for b in boms
		if not cint(frappe.db.get_value("Item", b.item, "is_stock_item"))}
	giu_ton = {b.item for b in boms if b.custom_chang in CHANG_GIU_TON}
	bom_cua = {}
	for b in boms:
		if b.item in phantom:
			bom_cua.setdefault(b.item, b.name)
			if not cint(b.is_phantom_bom):
				frappe.db.set_value("BOM", b.name, "is_phantom_bom", 1, update_modified=False)
				kq["bom_phantom"] += 1
	ten_bom = [b.name for b in boms]
	dong = frappe.get_all("BOM Item", filters={"parenttype": "BOM",
		"parent": ["in", ten_bom]},
		fields=["name", "parent", "item_code", "bom_no", "is_phantom_item", "do_not_explode"],
		limit_page_length=0)
	for d in dong:
		if d.item_code in phantom:
			bom_con = d.bom_no or _bom_mac_dinh(d.item_code) or bom_cua.get(d.item_code)
			if not bom_con:
				continue
			gt = {}
			if d.bom_no != bom_con:
				gt["bom_no"] = bom_con
			if not cint(d.is_phantom_item):
				gt["is_phantom_item"] = 1
			if cint(d.do_not_explode):
				gt["do_not_explode"] = 0
			if gt:
				frappe.db.set_value("BOM Item", d.name, gt, update_modified=False)
				kq["dong_phantom"] += 1
		elif d.item_code in giu_ton:
			gt = {}
			if not cint(d.do_not_explode):
				gt["do_not_explode"] = 1
			if d.bom_no:
				gt["bom_no"] = ""
			if cint(d.is_phantom_item):
				gt["is_phantom_item"] = 0
			if gt:
				frappe.db.set_value("BOM Item", d.name, gt, update_modified=False)
				kq["dong_giu_ton"] += 1


def _dung_lai_bang_no(kq):
	boms = _cac_bom_dang_chay()
	ten_bom = [b.name for b in boms]
	dong = frappe.get_all("BOM Item", filters={"parenttype": "BOM",
		"parent": ["in", ten_bom], "bom_no": ["!=", ""]},
		fields=["parent", "bom_no"], limit_page_length=0)
	con_cua = {t: [] for t in ten_bom}
	for d in dong:
		con_cua[d.parent].append(d.bom_no)
	for ten in thu_tu_dung_lai(con_cua):
		try:
			doc = frappe.get_doc("BOM", ten)
			doc.update_exploded_items(save=True)
			kq["dung_lai"] += 1
		except Exception as e:
			kq["hong_dung_lai"].append({"bom": ten, "vi_sao": str(e)[:160]})


def _kiem_lai(kq):
	"""Sau khi dựng lại, lá nào còn là mã không quản tồn hay mã đã tắt thì
	ghi ra để người sau nhìn thấy ngay, không phải đi dò từng công thức."""
	boms = [b for b in _cac_bom_dang_chay() if b.custom_chang != CHANG_BTP]
	if not boms:
		return
	la = frappe.get_all("BOM Explosion Item", filters={"parenttype": "BOM",
		"parent": ["in", [b.name for b in boms]]},
		fields=["parent", "item_code"], limit_page_length=0)
	ma = {x.item_code for x in la}
	if not ma:
		return
	ho_so = frappe.get_all("Item", filters={"name": ["in", list(ma)]},
		fields=["name", "is_stock_item", "disabled"], limit_page_length=0)
	phantom = {h.name for h in ho_so if not cint(h.is_stock_item)}
	tat = {h.name for h in ho_so if cint(h.disabled)}
	theo_bom = {}
	for x in la:
		theo_bom.setdefault(x.parent, []).append(x.item_code)
	for ten, cac in theo_bom.items():
		h = la_hong(cac, phantom, tat)
		if h:
			kq["la_hong"][ten] = h
