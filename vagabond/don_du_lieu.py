# -*- coding: utf-8 -*-
"""Bộ dọn dữ liệu sản xuất một lần, anh Việt giao 21/08/2026.

Năm việc, mỗi việc một cửa, và MỌI cửa đều `chay_that=0` mặc định: gọi
trống là chỉ đọc và trả về kế hoạch, phải truyền `chay_that=1` mới ghi.
Đây là các thao tác đổi dữ liệu hàng loạt trên hệ đang bán hàng, không có
nút hoàn tác, nên xem trước là bắt buộc chứ không phải lịch sự.

1. `nuoc_het_ton`     - NVLT00231 "Nước, ml" thôi giữ tồn kho. Nước máy
   không ai nhập kho, để nó là hàng tồn thì mọi lệnh sản xuất có nước đều
   báo thiếu 9.919 gram nước, nghe như chuyện đùa nhưng chặn bếp thật.
2. `don_kho_do_dang`  - xả tồn hai kho Dở dang về 0 rồi tắt kho. Chủ
   trương anh Việt chốt: gom dở dang vào kho thành phẩm, không theo tồn
   ở chặng giữa.
3. `doi_ten`          - máy đổi tên hàng loạt theo danh sách đã duyệt.
   Chỉ đổi item_name, KHÔNG đổi mã (mã là khoá, đổi là gãy tra cứu).
4. `ma_thay_the`      - khai mã thay thế cho nhóm bơ lạt, để hết bơ
   Avonmore thì máy lấy bơ Anchor thay vì bắt bếp đứng chờ.
5. `nap_bom_thu_vien` - nạp BOM nháp cho các khối thư viện Pastry từ file
   của Hân, phần đã ghép đủ mã và chưa có công thức đang chạy.

Kèm `dat_tran_vuot_lenh` cho Khối 3: mở trần vượt lệnh để bếp nhập số
cân thực tế lớn hơn số lý thuyết.

Vì sao ghi thẳng xuống bảng ở vài chỗ: ERPNext chặn đổi `is_stock_item`
khi mã còn BOM đã ghi sổ trỏ tới (nó đếm BOM là giao dịch), giống hệt bài
Phantom v250. Hàng rào thay thế nằm ngay trong từng hàm: còn tồn thì xả
bằng PHIẾU CÓ GHI SỔ (giữ vết, QT-20), còn lệnh treo thì DỪNG và chỉ
đường, không ghi đè trong im lặng.
"""

import json
import os
import re

# ------------------------------------------------------------ phần thuần

MA_NUOC = "NVLT00231"

KHO_DO_DANG = ("Baker - Dở dang - TV", "Pastry - Dở dang - TV")

# Nhóm bơ lạt thay thế được cho nhau: cùng là bơ khối không muối, khác
# thương hiệu và quy cách. Bơ TẤM cán lớp (Butter Sheet) cố ý KHÔNG nằm
# trong nhóm: bơ tấm cán croissant không thay bằng bơ khối được.
NHOM_BO_LAT = ("NVLT00242", "NVLT00020", "NVLT00230", "NVLT00235", "NVLT00382")

# Đơn vị trong file của Hân về đơn vị của hệ.
DVT_FILE = {"gr": "Gram", "gram": "Gram", "g": "Gram", "ml": "ML",
	"cái": "Cái", "cai": "Cái", "quả": "Quả", "qua": "Quả"}


def cap_thay_the(cac_ma):
	"""Các cặp mã thay thế hai chiều từ một nhóm. THUẦN.

	Nhóm 5 mã ra 10 cặp. Khai một chiều kèm cờ hai chiều, chiều ngược
	ERPNext tự hiểu, nên chỉ cần các cặp (a, b) với a đứng trước b.
	"""
	ra = []
	ds = [m for m in cac_ma if m]
	for i in range(len(ds)):
		for j in range(i + 1, len(ds)):
			ra.append((ds[i], ds[j]))
	return ra


def doi_ten_hop_le(ma, ten_moi, ten_cu):
	"""Một dòng đổi tên có nạp được không. Trả về (ok, vì_sao). THUẦN."""
	if not (ma or "").strip():
		return False, "thiếu mã"
	t = (ten_moi or "").strip()
	if not t:
		return False, "tên mới trống"
	if len(t) > 140:
		return False, "tên mới dài quá 140 ký tự"
	if t == (ten_cu or "").strip():
		return False, "tên mới trùng tên cũ, không có gì để đổi"
	return True, ""


def khoi_nap_duoc(khoi):
	"""Một khối thư viện có đủ dữ liệu dựng BOM mẻ không. THUẦN."""
	if not (khoi.get("ma_btp") or "").strip():
		return False, "chưa có mã BTP trên hệ, phải mở mã trước"
	if not khoi.get("me_gram"):
		return False, "file không ghi mẻ ra bao nhiêu gram"
	if khoi.get("thieu_ma"):
		return False, "còn nguyên liệu chưa ghép được mã: %s" % ", ".join(
			khoi["thieu_ma"][:3])
	if khoi.get("sl_hong"):
		return False, "có dòng nguyên liệu không đọc được số lượng"
	if not khoi.get("dong"):
		return False, "khối không có dòng nguyên liệu nào"
	return True, ""


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt


def _chan():
	if not {"System Manager", "Giám đốc", "AP Giám đốc"} & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý hệ thống hoặc giám đốc mới chạy được bộ dọn dữ liệu. "
			"Đây là thao tác đổi dữ liệu hàng loạt."
		)


def _ton_cua(ma):
	return frappe.get_all(
		"Bin", filters={"item_code": ma, "actual_qty": ["!=", 0]},
		fields=["warehouse", "actual_qty", "stock_uom"], limit_page_length=0,
	)


def _lenh_treo_dung(ma=None, cac_kho=None):
	"""Lệnh sản xuất còn treo có dính mã này hoặc các kho này."""
	from vagabond.phantom import wo_con_treo

	ds = frappe.get_all(
		"Work Order", filters={"docstatus": ["<", 2]},
		fields=["name", "production_item", "status", "docstatus",
			"source_warehouse", "wip_warehouse", "fg_warehouse"],
		limit_page_length=0,
	)
	treo = [x for x in ds if wo_con_treo(x.status, x.docstatus)]
	ra = []
	for x in treo:
		if cac_kho and {x.source_warehouse, x.wip_warehouse, x.fg_warehouse} & set(cac_kho):
			ra.append(x.name)
			continue
		if ma:
			co = frappe.db.exists(
				"Work Order Item", {"parent": x.name, "item_code": ma})
			if co:
				ra.append(x.name)
	return ra


def _xa_ton(ma_kho_ds, ly_do, that):
	"""Xả các cặp (mã, kho, số) về 0 bằng phiếu xuất kho CÓ GHI SỔ.

	Dùng Material Issue chứ không sửa thẳng bảng tồn: phiếu nằm lại trong
	sổ, ai thắc mắc ba tháng sau vẫn tra ra vì sao số về 0 (QT-20). Lô
	của dòng xuất do hook `lo_hang.gan_lo` tự chọn, không phải khai tay.
	"""
	phieu = []
	if not that:
		return phieu
	for ma, kho, so in ma_kho_ds:
		doc = frappe.new_doc("Stock Entry")
		doc.stock_entry_type = "Material Issue"
		doc.purpose = "Material Issue"
		doc.company = frappe.db.get_single_value("Global Defaults", "default_company")
		doc.append("items", {"item_code": ma, "qty": flt(so), "s_warehouse": kho})
		doc.remarks = ly_do
		doc.insert(ignore_permissions=True)
		doc.submit()
		phieu.append(doc.name)
	return phieu


@frappe.whitelist()
def nuoc_het_ton(chay_that=0):
	"""NVLT00231 thôi giữ tồn kho, thôi theo lô."""
	_chan()
	that = cint(chay_that)
	it = frappe.db.get_value(
		"Item", MA_NUOC,
		["item_name", "is_stock_item", "has_batch_no"], as_dict=True)
	if not it:
		frappe.throw("Không thấy mã %s trên hệ." % MA_NUOC)
	ke = {
		"chay_that": that, "ma": MA_NUOC, "ten": it.item_name,
		"dang_theo_ton": cint(it.is_stock_item),
		"dang_theo_lo": cint(it.has_batch_no),
		"ton_con": [(x.warehouse, x.actual_qty) for x in _ton_cua(MA_NUOC)],
		"lenh_treo_dinh": _lenh_treo_dung(ma=MA_NUOC),
	}
	am = [x for x in ke["ton_con"] if flt(x[1]) < 0]
	if am:
		ke["ghi_chu"] = ("Có kho đang tồn ÂM %s, phải kiểm kê cho hết âm rồi "
			"chạy lại, máy không tự xử số âm." % am)
		return ke
	if ke["lenh_treo_dinh"]:
		ke["ghi_chu"] = ("Còn %d lệnh sản xuất treo có dùng Nước: %s. Vào màn "
			"Dọn chứng từ thử đóng các lệnh đó rồi chạy lại."
			% (len(ke["lenh_treo_dinh"]), ", ".join(ke["lenh_treo_dinh"][:5])))
		return ke
	if not that:
		ke["ghi_chu"] = ("Chạy thử. Sẽ xả %d kho còn tồn về 0 bằng phiếu xuất, "
			"rồi tắt theo dõi tồn và theo lô cho %s. Muốn ghi thật thì truyền "
			"chay_that=1." % (len(ke["ton_con"]), MA_NUOC))
		return ke

	ke["phieu_xa"] = _xa_ton(
		[(MA_NUOC, k, so) for k, so in ke["ton_con"]],
		"Xả tồn Nước trước khi chuyển thành hàng không giữ tồn (don_du_lieu, 21/08/2026)",
		that)
	# ERPNext chặn đổi is_stock_item khi còn BOM trỏ tới, nên ghi thẳng
	# bảng. An toàn vì vừa kiểm: tồn 0, không lệnh treo.
	frappe.db.set_value("Item", MA_NUOC,
		{"is_stock_item": 0, "has_batch_no": 0}, update_modified=False)
	frappe.clear_document_cache("Item", MA_NUOC)
	frappe.db.commit()
	ke["ghi_chu"] = ("Đã xả %d phiếu và tắt tồn kho cho %s. Lệnh sản xuất từ "
		"giờ không đòi trừ Nước nữa." % (len(ke.get("phieu_xa") or []), MA_NUOC))
	return ke


@frappe.whitelist()
def don_kho_do_dang(chay_that=0):
	"""Xả tồn hai kho Dở dang về 0 rồi tắt kho."""
	_chan()
	that = cint(chay_that)
	ton = frappe.get_all(
		"Bin", filters={"warehouse": ["in", list(KHO_DO_DANG)],
			"actual_qty": ["!=", 0]},
		fields=["item_code", "warehouse", "actual_qty"], limit_page_length=0)
	ke = {
		"chay_that": that,
		"ton_con": [(x.item_code, x.warehouse, x.actual_qty) for x in ton],
		"lenh_treo_dinh": _lenh_treo_dung(cac_kho=KHO_DO_DANG),
		"kho_se_tat": [k for k in KHO_DO_DANG
			if not cint(frappe.db.get_value("Warehouse", k, "disabled") or 0)],
	}
	am = [x for x in ke["ton_con"] if flt(x[2]) < 0]
	if am:
		ke["ghi_chu"] = "Có tồn ÂM trong kho dở dang: %s. Kiểm kê trước đã." % am
		return ke
	if ke["lenh_treo_dinh"]:
		ke["ghi_chu"] = ("Còn %d lệnh sản xuất treo đang trỏ vào kho dở dang: %s. "
			"Vào màn Dọn chứng từ thử đóng các lệnh đó rồi chạy lại."
			% (len(ke["lenh_treo_dinh"]), ", ".join(ke["lenh_treo_dinh"][:5])))
		return ke
	if not that:
		ke["ghi_chu"] = ("Chạy thử. Sẽ xả %d dòng tồn về 0 rồi tắt %d kho dở "
			"dang. Muốn ghi thật thì truyền chay_that=1."
			% (len(ke["ton_con"]), len(ke["kho_se_tat"])))
		return ke

	ke["phieu_xa"] = _xa_ton(
		[(x[0], x[1], x[2]) for x in ke["ton_con"]],
		"Xả tồn kho dở dang theo chủ trương bỏ kho dở dang (don_du_lieu, 21/08/2026)",
		that)
	for k in ke["kho_se_tat"]:
		frappe.db.set_value("Warehouse", k, "disabled", 1)
	# Manufacturing Settings đang không khai Default WIP, đặt rỗng cho chắc.
	try:
		frappe.db.set_single_value("Manufacturing Settings", "default_wip_warehouse", "")
	except Exception:
		pass
	frappe.db.commit()
	ke["ghi_chu"] = ("Đã xả %d phiếu, tắt %d kho dở dang. Từ giờ lệnh sản xuất "
		"đi thẳng nguyên liệu sang thành phẩm, không ghé chặng giữa."
		% (len(ke.get("phieu_xa") or []), len(ke["kho_se_tat"])))
	return ke


@frappe.whitelist()
def doi_ten(chay_that=0, ds=None):
	"""Đổi item_name hàng loạt theo danh sách [{ma, ten_moi}] đã duyệt."""
	_chan()
	that = cint(chay_that)
	if isinstance(ds, str):
		ds = json.loads(ds or "[]")
	if not ds:
		frappe.throw(
			"Chưa có danh sách đổi tên. Truyền ds dạng [{\"ma\": ..., "
			"\"ten_moi\": ...}] lấy từ file đã duyệt.")
	se_doi, bo_qua = [], []
	for dong in ds:
		ma = (dong.get("ma") or "").strip()
		ten_cu = frappe.db.get_value("Item", ma, "item_name") if ma else None
		if ma and ten_cu is None:
			bo_qua.append({"ma": ma, "vi_sao": "mã không có trên hệ"})
			continue
		ok, vi_sao = doi_ten_hop_le(ma, dong.get("ten_moi"), ten_cu)
		if not ok:
			bo_qua.append({"ma": ma or "(trống)", "vi_sao": vi_sao})
			continue
		se_doi.append({"ma": ma, "cu": ten_cu, "moi": dong["ten_moi"].strip()})
	ke = {"chay_that": that, "se_doi": len(se_doi), "bo_qua": bo_qua,
		"vi_du": se_doi[:10]}
	if not that:
		ke["ghi_chu"] = ("Chạy thử. Sẽ đổi tên %d mã, bỏ qua %d dòng. Muốn ghi "
			"thật thì truyền chay_that=1." % (len(se_doi), len(bo_qua)))
		return ke
	for x in se_doi:
		frappe.db.set_value("Item", x["ma"], "item_name", x["moi"],
			update_modified=False)
		frappe.clear_document_cache("Item", x["ma"])
	frappe.db.commit()
	ke["ghi_chu"] = "Đã đổi tên %d mã, bỏ qua %d dòng." % (len(se_doi), len(bo_qua))
	return ke


@frappe.whitelist()
def ma_thay_the(chay_that=0):
	"""Khai mã thay thế hai chiều cho nhóm bơ lạt."""
	_chan()
	that = cint(chay_that)
	ds = frappe.get_all(
		"Item", filters={"name": ["in", list(NHOM_BO_LAT)]},
		fields=["name", "item_name", "stock_uom", "disabled",
			"allow_alternative_item"], limit_page_length=0)
	co = {x.name: x for x in ds}
	thieu = [m for m in NHOM_BO_LAT if m not in co]
	dvt = {x.stock_uom for x in ds}
	ke = {"chay_that": that, "nhom": list(NHOM_BO_LAT), "thieu_ma": thieu,
		"dvt": sorted(dvt)}
	if thieu:
		ke["ghi_chu"] = "Các mã %s không có trên hệ, kiểm lại nhóm." % thieu
		return ke
	if len(dvt) > 1:
		ke["ghi_chu"] = ("Nhóm đang lẫn đơn vị %s. Mã thay thế phải cùng đơn "
			"vị gốc, gỡ mã lệch ra rồi chạy lại." % sorted(dvt))
		return ke
	cap = cap_thay_the(NHOM_BO_LAT)
	cap_moi = []
	for a, b in cap:
		da_co = frappe.db.exists("Item Alternative",
			{"item_code": a, "alternative_item_code": b}) or frappe.db.exists(
			"Item Alternative", {"item_code": b, "alternative_item_code": a})
		if not da_co:
			cap_moi.append((a, b))
	ke["cap_moi"] = cap_moi
	ke["bat_co"] = [m for m in NHOM_BO_LAT
		if not cint(co[m].allow_alternative_item)]
	if not that:
		ke["ghi_chu"] = ("Chạy thử. Sẽ khai %d cặp thay thế hai chiều và bật cờ "
			"cho %d mã. Muốn ghi thật thì truyền chay_that=1."
			% (len(cap_moi), len(ke["bat_co"])))
		return ke
	for a, b in cap_moi:
		doc = frappe.new_doc("Item Alternative")
		doc.item_code = a
		doc.alternative_item_code = b
		doc.two_way = 1
		doc.insert(ignore_permissions=True)
	for m in ke["bat_co"]:
		frappe.db.set_value("Item", m, "allow_alternative_item", 1,
			update_modified=False)
	frappe.db.commit()
	ke["ghi_chu"] = ("Đã khai %d cặp, bật cờ %d mã. Từ giờ hết bơ chính thì "
		"máy tự lấy bơ thay thế cùng kho và ghi chú trên phiếu."
		% (len(cap_moi), len(ke["bat_co"])))
	return ke


@frappe.whitelist()
def nap_bom_thu_vien(chay_that=0):
	"""Nạp BOM nháp cho các khối thư viện Pastry đã ghép đủ mã."""
	_chan()
	that = cint(chay_that)
	duong = os.path.join(os.path.dirname(__file__), "du_lieu",
		"bom_thu_vien_pastry.json")
	du_lieu = json.load(open(duong, encoding="utf-8"))
	cong_ty = frappe.db.get_single_value("Global Defaults", "default_company")
	se_nap, bo_qua = [], []
	for khoi in du_lieu["khoi"]:
		ok, vi_sao = khoi_nap_duoc(khoi)
		ten_go = "%s (%s)" % (khoi["ten"], khoi.get("ma_btp") or "chưa có mã")
		if not ok:
			bo_qua.append({"khoi": ten_go, "vi_sao": vi_sao})
			continue
		ma = khoi["ma_btp"]
		if not frappe.db.exists("Item", ma):
			bo_qua.append({"khoi": ten_go, "vi_sao": "mã BTP không có trên hệ"})
			continue
		if frappe.db.exists("BOM", {"item": ma, "docstatus": 1, "is_active": 1}):
			bo_qua.append({"khoi": ten_go,
				"vi_sao": "đã có công thức đang chạy, không nạp đè"})
			continue
		if frappe.db.exists("BOM", {"item": ma, "docstatus": 0}):
			bo_qua.append({"khoi": ten_go,
				"vi_sao": "đã có bản nháp chờ duyệt, không nạp thêm"})
			continue
		thieu_nvl = [d["ma"] for d in khoi["dong"]
			if not frappe.db.exists("Item", d["ma"])]
		if thieu_nvl:
			bo_qua.append({"khoi": ten_go,
				"vi_sao": "nguyên liệu %s không có trên hệ" % thieu_nvl[:3]})
			continue
		se_nap.append(khoi)
	ke = {"chay_that": that, "se_nap": [k["ma_btp"] for k in se_nap],
		"bo_qua": bo_qua}
	if not that:
		ke["ghi_chu"] = ("Chạy thử. Sẽ nạp %d BOM nháp (bếp trưởng duyệt trong "
			"màn Danh mục công thức), bỏ qua %d khối kèm lý do. Muốn ghi thật "
			"thì truyền chay_that=1." % (len(se_nap), len(bo_qua)))
		return ke
	da_nap = []
	for khoi in se_nap:
		doc = frappe.new_doc("BOM")
		doc.item = khoi["ma_btp"]
		doc.company = cong_ty
		doc.quantity = flt(khoi["me_gram"])
		doc.uom = frappe.db.get_value("Item", khoi["ma_btp"], "stock_uom")
		doc.currency = "VND"
		doc.rm_cost_as_per = "Valuation Rate"
		doc.with_operations = 0
		doc.custom_chang = "BTP thành phần"
		for d in khoi["dong"]:
			doc.append("items", {
				"item_code": d["ma"], "qty": flt(d["sl"]),
				"uom": DVT_FILE.get((d.get("dvt") or "gr").lower(),
					frappe.db.get_value("Item", d["ma"], "stock_uom")),
			})
		doc.insert(ignore_permissions=True)  # để NHÁP, không submit
		da_nap.append(doc.name)
	frappe.db.commit()
	ke["da_nap"] = da_nap
	ke["ghi_chu"] = ("Đã nạp %d BOM nháp từ file của Hân. Bếp trưởng vào màn "
		"Danh mục công thức duyệt từng bản." % len(da_nap))
	return ke


@frappe.whitelist()
def dat_tran_vuot_lenh(phan_tram=50):
	"""Mở trần vượt lệnh để bếp nhập số cân thực tế lớn hơn lý thuyết.

	Trái dừa nạy ra lúc được 900 gram cùi lúc được 1.100, mẻ kem đánh bông
	lúc nở nhiều lúc nở ít. Trần 0%% nghĩa là cân dư một gram cũng bị máy
	đuổi về, và bếp sẽ khai man số cho khớp - số liệu chết từ đó.
	"""
	_chan()
	pt = max(0, min(cint(phan_tram), 100))
	frappe.db.set_single_value("Manufacturing Settings",
		"overproduction_percentage_for_work_order", pt)
	frappe.db.commit()
	return {"ok": 1, "phan_tram": pt,
		"ghi_chu": "Đã đặt trần vượt lệnh %d%%. Bếp cân được bao nhiêu khai "
			"bấy nhiêu, tối đa gấp rưỡi số lệnh." % pt}
