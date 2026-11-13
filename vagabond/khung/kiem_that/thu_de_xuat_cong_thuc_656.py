"""v656 Phiếu đề xuất công thức: ca tích hợp THẬT trên ERPNext.

Tầng khung chốt phép thuần (kế hoạch cấp, gợi ý size, giá vốn dự kiến). Tầng
này hỏi điều bản giả không trả lời được: Item, BOM THẬT do Khải bấm tạo có qua
được validation của ERPNext, ghi sổ từ dưới lên có thành bản đang dùng, phiếu
điều chỉnh ra phiên bản mới và bản cũ lui về.

Chuỗi đúng như app gửi: luu, gui (bếp), tao_nhap, ghi_so_tat_ca (Khải); phiếu
điều chỉnh: tu_cong_thuc, luu, gui, duyet_dieu_chinh. Tin Zalo cho Khải thay bằng
hàm rỗng (không gửi ra ngoài). Mã thử ngẫu nhiên, điểm lưu của nen.py.
"""

import json
import unittest.mock as um
import uuid

import frappe

from vagabond import de_xuat_cong_thuc as dx
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu


def _uom(ten):
	if not frappe.db.exists("UOM", ten):
		u = frappe.get_doc({"doctype": "UOM", "uom_name": ten, "must_be_whole_number": 0})
		u.insert(ignore_permissions=True)
		nen._DA_TAO.append(("UOM", u.name))
	return ten


def _nhom(ten, tien_to):
	"""Nhóm hàng như trên site. Bench có ô Mã master thì khai tiền tố thử riêng
	để mã máy tạo không đụng mã sẵn có."""
	if not frappe.db.exists("Item Group", ten):
		g = frappe.get_doc({"doctype": "Item Group", "item_group_name": ten, "is_group": 0,
			"parent_item_group": frappe.db.get_value("Item Group", {"is_group": 1}, "name", order_by="lft asc")})
		g.insert(ignore_permissions=True)
		nen._DA_TAO.append(("Item Group", g.name))
	if frappe.get_meta("Item Group").has_field("custom_ma_master"):
		frappe.db.set_value("Item Group", ten, "custom_ma_master", tien_to, update_modified=False)
		return tien_to
	return dx.TIEN_TO_MAC_DINH[ten]


def _the_gioi():
	_uom("Gram"); _uom("Cái")
	tag = uuid.uuid4().hex[:4].upper()
	tt_thanh_phan = _nhom(dx.NHOM_THANH_PHAN, "KTA" + tag)
	tt_cap = _nhom(dx.NHOM_CAP, "KTB" + tag)
	bo = _mon_thu("KT656-BO-" + tag)
	duong = _mon_thu("KT656-DUONG-" + tag)
	hoa = _mon_thu("KT656-HOA-" + tag)
	tp = {s: _mon_thu("KT656-TP%s-%s" % (s, tag)) for s in ("16", "20")}
	for m in (bo, duong, hoa):
		frappe.db.set_value("Item", m, "valuation_rate", 100, update_modified=False)
	dvt = frappe.db.get_value("Item", bo, "stock_uom")
	du_lieu = {"sizes": ["16", "20"], "dong": [
		{"id": "a", "ma": bo, "ten": "Bơ", "dvt": dvt, "dich": dx.CAP1, "gram": {"16": 100, "20": 156}},
		{"id": "b", "ten": "Mousse thử " + tag, "dvt": "Gram", "dich": dx.CAP2, "gram": {"16": 200, "20": 312},
			"con": {"me": 500, "dong": [{"ma": duong, "ten": "Đường", "sl": 400, "dvt": dvt}]}},
		{"id": "c", "ma": hoa, "ten": "Hoa", "dvt": dvt, "dich": dx.THANH_PHAM, "gram": {"16": 3, "20": 3}},
	]}
	return {"tag": tag, "tt": (tt_thanh_phan, tt_cap), "bo": bo, "duong": duong, "hoa": hoa, "tp": tp, "du_lieu": du_lieu}


def _dong(bom):
	return sorted((r.item_code, float(r.qty)) for r in frappe.get_doc("BOM", bom).items)


@ca("v656 bánh mới: bếp gửi, Khải tạo mã và công thức nháp, ghi sổ tất cả từ dưới lên trên ERPNext thật")
def _banh_moi():
	w = _the_gioi()
	with um.patch.object(dx, "_bao_khai", lambda doc: None):
		r = dx.luu(None, "Bánh thử " + w["tag"], json.dumps(w["du_lieu"]), dx.LOAI_MOI)
		r = dx.gui(r["name"])
	la("gửi xong thành Chờ Khải", r["trang_thai"], dx.TT_CHO)
	r = dx.tao_nhap(r["name"], json.dumps(w["tp"]))
	la("tạo xong thành Đã tạo nháp", r["trang_thai"], dx.TT_DA_TAO)
	kq = r["ket_qua"]
	ma_moi = kq["ma_moi"]["b"]
	dung("mã thành phần mới theo tiền tố nhóm", ma_moi.startswith(w["tt"][0]))
	la("mã thành phần mới nằm nhóm BTP thành phần", frappe.db.get_value("Item", ma_moi, "item_group"), dx.NHOM_THANH_PHAN)
	la("7 công thức nháp: 1 thành phần, cấp 1, cấp 2, thành phẩm cho 2 size", len(kq["bom"]), 7)
	for b in kq["bom"]:
		la("%s là nháp" % b["bom"], frappe.db.get_value("BOM", b["bom"], "docstatus"), 0)
	c1, c2 = kq["cap"]["16"][dx.CAP1], kq["cap"]["16"][dx.CAP2]
	dung("mã cấp theo tiền tố nhóm cấp", c1.startswith(w["tt"][1]) and c2.startswith(w["tt"][1]))
	theo_ma = {b["ma"]: b["bom"] for b in kq["bom"]}
	la("công thức thành phần mới: 400 đường cho mẻ 500", (_dong(theo_ma[ma_moi]), frappe.db.get_value("BOM", theo_ma[ma_moi], "quantity")),
		([(w["duong"], 400.0)], 500.0))
	la("cấp 1 size 16: 100 bơ", _dong(theo_ma[c1]), [(w["bo"], 100.0)])
	la("cấp 2 size 16: một ruột cấp 1 cộng 200 mousse", _dong(theo_ma[c2]), sorted([(c1, 1.0), (ma_moi, 200.0)]))
	la("thành phẩm size 16: một bánh khuôn cấp 2 cộng 3 hoa", _dong(theo_ma[w["tp"]["16"]]), sorted([(c2, 1.0), (w["hoa"], 3.0)]))
	la("cấp 2 size 20: 312 mousse", [q for m, q in _dong(theo_ma[kq["cap"]["20"][dx.CAP2]]) if m == ma_moi], [312.0])
	r = dx.ghi_so_tat_ca(r["name"])
	la("ghi sổ xong thành Đã ghi sổ", r["trang_thai"], dx.TT_XONG)
	for b in kq["bom"]:
		la("%s đã ghi sổ và là bản đang dùng" % b["bom"], frappe.db.get_value("BOM", b["bom"], ["docstatus", "is_default"]), (1, 1))
	dung("giá vốn thành phẩm tính từ cấp dưới (lớn hơn 0)", frappe.db.get_value("BOM", theo_ma[w["tp"]["16"]], "total_cost") > 0)
	# Codex #563: công thức thành phần mới là phantom; dòng của nó trong cấp 2
	# trỏ công thức con; dòng cấp 1 trong cấp 2 chặn nổ. Bảng nguyên liệu lệnh
	# sản xuất cấp 2 (ERPNext thật, nổ một cấp lẫn nhiều cấp) phải trừ ĐƯỜNG bên
	# trong thành phần mới (200 g mousse, mẻ 500 g ra từ 400 g đường: 160 g)
	# và đòi đúng một ruột cấp 1, không đòi chính mã thành phần mới.
	from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
	la("công thức thành phần mới là phantom", frappe.db.get_value("BOM", theo_ma[ma_moi], "is_phantom_bom"), 1)
	dong_c2 = {r.item_code: r for r in frappe.get_doc("BOM", theo_ma[c2]).items}
	la("dòng thành phần mới trong cấp 2: phantom, trỏ công thức con",
		(dong_c2[ma_moi].is_phantom_item, dong_c2[ma_moi].bom_no, dong_c2[ma_moi].do_not_explode), (1, theo_ma[ma_moi], 0))
	la("dòng cấp 1 trong cấp 2: chặn nổ", (dong_c2[c1].do_not_explode, dong_c2[c1].bom_no or ""), (1, ""))
	dong_tp = {r.item_code: r for r in frappe.get_doc("BOM", theo_ma[w["tp"]["16"]]).items}
	la("dòng cấp 2 trong thành phẩm: chặn nổ", dong_tp[c2].do_not_explode, 1)
	for nhieu in (0, 1):
		nl = get_bom_items_as_dict(theo_ma[c2], nen.cong_ty(), qty=1, fetch_exploded=nhieu)
		la("lệnh cấp 2 (nổ %s): trừ 160 đường và đòi 1 ruột cấp 1, không đòi mã thành phần mới" % ("nhiều cấp" if nhieu else "một cấp"),
			sorted((k, round(float(v.get("qty")), 3)) for k, v in nl.items()),
			sorted([(w["duong"], 160.0), (c1, 1.0)]))
	try:
		dx.ghi_so_tat_ca(r["name"])
		dung("bấm Ghi sổ tất cả lần hai bị chặn", False)
	except frappe.ValidationError:
		dung("bấm Ghi sổ tất cả lần hai bị chặn", True)


@ca("v656 đề xuất điều chỉnh: Khải duyệt ra phiên bản mới, bản cũ lui về, lịch sử ghi người đề xuất, người duyệt, lý do")
def _dieu_chinh():
	w = _the_gioi()
	tp = w["tp"]["16"]
	dvt = frappe.db.get_value("Item", w["bo"], "stock_uom")
	cu = frappe.get_doc({"doctype": "BOM", "item": tp, "company": nen.cong_ty(), "quantity": 1, "is_active": 1, "is_default": 1,
		"rm_cost_as_per": "Valuation Rate", "items": [{"item_code": w["bo"], "qty": 200, "uom": dvt}]})
	cu.insert(ignore_permissions=True); nen._DA_TAO.append(("BOM", cu.name)); cu.submit()
	t = dx.tu_cong_thuc(cu.name)
	t["du_lieu"]["dong"][0]["gram"][""] = 180
	with um.patch.object(dx, "_bao_khai", lambda doc: None):
		r = dx.luu(None, None, json.dumps(t["du_lieu"]), dx.LOAI_DIEU_CHINH, cu.name, "Bớt béo")
		la("bảng trước sau: bơ 200 thành 180", [(x["cu"], x["moi"], x["kieu"]) for x in r["doi_chieu"]["bang"]], [(200.0, 180.0, "doi")])
		r = dx.gui(r["name"])
	r = dx.duyet_dieu_chinh(r["name"])
	la("duyệt xong thành Đã ghi sổ", r["trang_thai"], dx.TT_XONG)
	moi = r["ket_qua"]["bom"][0]["bom"]
	la("bản mới đang dùng, 180 bơ", (frappe.db.get_value("BOM", moi, ["docstatus", "is_default"]), _dong(moi)), ((1, 1), [(w["bo"], 180.0)]))
	la("bản cũ lui về", frappe.db.get_value("BOM", cu.name, "is_default"), 0)
	cmt = frappe.get_all("Comment", filters={"reference_doctype": "BOM", "reference_name": moi, "comment_type": "Comment"}, pluck="content")
	dung("lịch sử ghi lý do và phiếu", any("Bớt béo" in (c or "") and r["name"] in (c or "") for c in cmt))
