# -*- coding: utf-8 -*-
"""Bỏ ảo (bỏ phantom) một mã hàng để nó có tồn kho trở lại (v564).

Anh Việt chốt 03/10/2026 (bảng duyệt sổ tay, việc số 2): làm công cụ bỏ
ảo trên cả Desk và app; mã đã có giao dịch mà ERPNext chặn thì "báo để làm
tay, vượt chặn của Next cũng được".

Bỏ ảo là làm NGƯỢC đúng những gì patches/no_phantom_chuan.py đã làm cho mã
đó, không hơn:

  1. Mã hàng: is_stock_item = 1. ERPNext chặn đổi ô này khi mã đã có giao
     dịch hay còn công thức đã ghi sổ trỏ tới, nên ghi thẳng xuống bảng (anh
     Việt cho phép vượt chặn). Hàng rào thay thế ở `soat`: mã đang theo lô
     hay theo số máy thì dừng.
  2. Công thức của chính mã: is_phantom_bom = 0.
  3. Mọi dòng công thức cha đang dùng mã: do_not_explode = 1, bỏ bom_no,
     is_phantom_item = 0. Từ đó lệnh của món cha lấy mã này từ kho như bánh
     khuôn, ruột bánh, không trừ thẳng nguyên liệu thô nữa.
  4. Dựng lại bảng nổ của các công thức cha và mọi tầng trên nó, CON TRƯỚC
     CHA SAU (cùng lý do với no_phantom_chuan: cha đọc bảng nổ đã lưu của con).
  5. Ghi mã vào danh sách GIỮ TỒN để phantom.chuyen() hay patch phantom chạy
     lại không biến nó về ảo.

Chỉ áp từ nay: lệnh sản xuất và phiếu kho đã có giữ nguyên. Mặc định chỉ
xem kế hoạch, phải gọi chay_that=1 mới ghi.
"""

import json

import frappe
from frappe.utils import cint

KHOA_GIU_TON = "vgb_phantom_giu_ton"


# ------------------------------------------------------------ phần thuần


def viec_dong_cha(do_not_explode, bom_no, is_phantom_item):
	"""Giá trị phải ghi cho một dòng cha đang dùng mã vừa bỏ ảo. THUẦN.

	Trả dict rỗng nếu dòng đã đúng (chặn nổ, không trỏ công thức con, không
	mang cờ phantom), để chạy lại lần hai không đổi gì.
	"""
	gt = {}
	if not cint(do_not_explode):
		gt["do_not_explode"] = 1
	if (bom_no or "").strip():
		gt["bom_no"] = ""
	if cint(is_phantom_item):
		gt["is_phantom_item"] = 0
	return gt


def cau_chan(ma, co_lo, co_so_may, khong_co):
	"""Câu dừng, nói rõ làm gì tiếp. Rỗng là được làm. THUẦN."""
	if khong_co:
		return "Không tìm thấy mã hàng %s." % ma
	if co_lo or co_so_may:
		return ("Mã %s đang %s nên công cụ không tự bỏ ảo. Báo kỹ thuật làm tay."
			% (ma, "theo lô" if co_lo else "theo số máy"))
	return ""


def tong_ket(ma, da_la_hang_ton, so_bom_rieng, so_dong, so_dung_lai, vuot_chan):
	"""Một câu cho người bấm. THUẦN."""
	if da_la_hang_ton and not (so_bom_rieng or so_dong):
		return "Mã %s đã có tồn kho từ trước, không cần bỏ ảo." % ma
	cau = ("Bỏ ảo %s: bật quản lý tồn kho, %d công thức của mã thôi là công thức ảo, "
		"%d dòng công thức cha chuyển sang lấy từ kho, dựng lại %d công thức."
		% (ma, so_bom_rieng, so_dong, so_dung_lai))
	if vuot_chan:
		cau += (" Mã đã từng có giao dịch kho nên máy ghi thẳng, vượt chặn của "
			"ERPNext (anh Việt cho phép 03/10/2026).")
	return cau


def doc_giu_ton(chuoi):
	try:
		ds = json.loads(chuoi or "[]")
	except (TypeError, ValueError):
		return []
	return sorted({str(x) for x in ds if x}) if isinstance(ds, list) else []


def them_giu_ton(ds, ma):
	return sorted(set(ds or []) | {ma})


# ------------------------------------------------------- phần cần Frappe


def danh_sach_giu_ton():
	"""Mã đã bỏ ảo, phantom.chuyen và patch phantom phải để yên."""
	try:
		return doc_giu_ton(frappe.db.get_default(KHOA_GIU_TON))
	except Exception:
		return []


def _chan():
	vai = {"System Manager", "Giám đốc", "AP Giám đốc", "Manufacturing Manager"}
	if not vai & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý sản xuất hoặc giám đốc mới bỏ ảo mã hàng.")


def _to_tien(bom_goc):
	"""Mọi công thức đang chạy nằm phía trên các công thức này, kèm chính chúng."""
	dang = {b.name for b in frappe.get_all("BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["name"], limit_page_length=0)}
	cha_cua = {}
	for d in frappe.get_all("BOM Item", filters={"parenttype": "BOM", "parent": ["in", list(dang)],
			"bom_no": ["!=", ""]}, fields=["parent", "bom_no"], limit_page_length=0):
		cha_cua.setdefault(d.bom_no, set()).add(d.parent)
	thay, hang = set(bom_goc), list(bom_goc)
	while hang:
		b = hang.pop()
		for c in cha_cua.get(b, ()):
			if c not in thay:
				thay.add(c)
				hang.append(c)
	return thay & dang


def _ke_hoach(ma):
	it = frappe.db.get_value("Item", ma, ["name", "item_name", "is_stock_item",
		"has_batch_no", "has_serial_no"], as_dict=True)
	chan = cau_chan(ma, it and cint(it.has_batch_no), it and cint(it.has_serial_no), not it)
	if chan:
		return {"ma": ma, "chan": chan}
	bom_rieng = [b.name for b in frappe.get_all("BOM", filters={"item": ma, "docstatus": 1,
		"is_active": 1, "is_phantom_bom": 1}, fields=["name"], limit_page_length=0)]
	dong = []
	for d in frappe.get_all("BOM Item", filters={"parenttype": "BOM", "item_code": ma, "docstatus": 1},
			fields=["name", "parent", "do_not_explode", "bom_no", "is_phantom_item"], limit_page_length=0):
		if not frappe.db.get_value("BOM", d.parent, "is_active"):
			continue
		gt = viec_dong_cha(d.do_not_explode, d.bom_no, d.is_phantom_item)
		if gt:
			dong.append({"dong": d.name, "bom_cha": d.parent, "gt": gt})
	cha = sorted({d["bom_cha"] for d in dong})
	co_giao_dich = bool(frappe.db.exists("Stock Ledger Entry", {"item_code": ma})
		or frappe.db.exists("BOM Item", {"item_code": ma, "docstatus": 1}))
	return {
		"ma": ma, "ten": it.item_name, "chan": "",
		"da_la_hang_ton": cint(it.is_stock_item),
		"bom_rieng": bom_rieng, "dong": dong, "bom_cha": cha,
		"vuot_chan": bool(co_giao_dich and not cint(it.is_stock_item)),
	}


@frappe.whitelist()
def xem(ma=None):
	"""Xem trước: sẽ đổi gì. Không ghi."""
	_chan()
	ma = (ma or "").strip()
	ke = _ke_hoach(ma)
	if not ke["chan"]:
		ke["tong_ket"] = tong_ket(ma, ke["da_la_hang_ton"], len(ke["bom_rieng"]), len(ke["dong"]),
			len(ke["bom_cha"]), ke["vuot_chan"])
	return ke


@frappe.whitelist()
def chay(ma=None, ly_do=None, chay_that=0):
	"""Bỏ ảo thật khi chay_that=1. Phải ghi lý do."""
	_chan()
	ma = (ma or "").strip()
	if not cint(chay_that):
		return xem(ma)
	if not (ly_do or "").strip():
		frappe.throw("Ghi lý do bỏ ảo thì sau này còn giải trình được.")
	ke = _ke_hoach(ma)
	if ke["chan"]:
		frappe.throw(ke["chan"])
	# Thu tu co y: danh sach giu ton va ma hang truoc, dong cha sau. Hong giua
	# chung thi ma da co ton ma cong thuc cha van no xuong nguyen lieu, lenh
	# van chay duoc; nguoc lai thi cha doi ton cua mot ma chua co ton.
	frappe.db.set_default(KHOA_GIU_TON, json.dumps(them_giu_ton(danh_sach_giu_ton(), ma)))
	frappe.db.set_value("Item", ma, "is_stock_item", 1, update_modified=False)
	frappe.clear_document_cache("Item", ma)
	for b in ke["bom_rieng"]:
		frappe.db.set_value("BOM", b, "is_phantom_bom", 0, update_modified=False)
	for d in ke["dong"]:
		frappe.db.set_value("BOM Item", d["dong"], d["gt"], update_modified=False)
	from vagabond.patches.no_phantom_chuan import thu_tu_dung_lai

	can = _to_tien(ke["bom_cha"])
	con_cua = {t: [] for t in can}
	for d in frappe.get_all("BOM Item", filters={"parenttype": "BOM", "parent": ["in", list(can)],
			"bom_no": ["!=", ""]}, fields=["parent", "bom_no"], limit_page_length=0):
		con_cua[d.parent].append(d.bom_no)
	da, hong = [], []
	for ten in thu_tu_dung_lai(con_cua):
		try:
			frappe.get_doc("BOM", ten).update_exploded_items(save=True)
			da.append(ten)
		except Exception as e:
			hong.append({"bom": ten, "vi_sao": str(e)[:160]})
			frappe.log_error(frappe.get_traceback(), "bo_ao: dung lai %s" % ten)
	try:
		frappe.get_doc("Item", ma).add_comment("Comment", "Bỏ ảo, có tồn kho trở lại. Lý do: %s" % ly_do.strip())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "bo_ao: ghi chu")
	frappe.db.commit()
	frappe.clear_cache()
	ke["da_dung_lai"], ke["hong"] = da, hong
	ke["tong_ket"] = tong_ket(ma, 0, len(ke["bom_rieng"]), len(ke["dong"]), len(da), ke["vuot_chan"])
	if hong:
		ke["tong_ket"] += " Có %d công thức dựng lại hỏng, báo kỹ thuật." % len(hong)
	return ke
