# -*- coding: utf-8 -*-
"""v646: Gom yêu cầu mua thành đơn mua theo nhà cung cấp (anh Việt 09/11/2026).

Anh Việt: *"Thu mua em làm luôn đi đâu cần hạn mức. Tổng hợp từ mấy cái đơn
yêu cầu mua hàng của các bộ phận gửi lên ấy. Rồi staff thu mua vào chỉ việc
sửa số rồi chốt."*

Trước bản này, thu mua duyệt từng dòng trên app (duyet_ycmh.py) rồi sang Desk
bấm một nút "Tách đơn theo NCC" nằm trong cơ sở dữ liệu. Năm phiếu xin cùng
một món là năm dòng phải duyệt riêng.

Màn Gom yêu cầu mua làm ngược lại: máy gom MỌI dòng yêu cầu mua đã gửi mà chưa
ai duyệt, chia theo nhà cung cấp mặc định của món, cộng các phiếu cùng món
thành một dòng. Số mua máy điền sẵn bằng tổng số xin (số ĐẶT, điền sẵn được).
Thu mua sửa số rồi bấm Chốt cho từng nhà cung cấp: máy ghi phần duyệt lên đúng
từng dòng phiếu xin (giữ nguyên số xin của nhân viên, luật PA-3) và lập đơn mua
nối về từng dòng đó, nên phiếu xin tự đóng khi hàng về.

Luật cũ giữ nguyên, không đi vòng:
  - Số xin `qty` không bao giờ bị sửa; phần duyệt nằm ở `sl_duyet`.
  - Mua 0 là từ chối, có lý do ghi sẵn để nhân viên biết vì sao.
  - Đơn mua đi qua đúng hai hàng rào của Desk (dong_bo_don_mua_theo_duyet,
    chan_don_mua_trai_duyet), không có đường riêng.
  - Gửi đơn cho nhà cung cấp vẫn là nút riêng (anh Việt 03/10/2026), chốt
    ở đây không tự gửi thư.

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

import json

import frappe
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

EPS = 0.0001
CHUA_CO_NCC = ""


# ================================================================== THUẦN


def chon_ncc(ma, mac_dinh=None, cung_cap=None, lan_cuoi=None):
	"""Nhà cung cấp cho một món: mặc định của món, rồi nhà cung cấp khai trên
	món, rồi nhà cung cấp của đơn mua gần nhất. Không có thì chuỗi rỗng. THUẦN."""
	for nguon in (mac_dinh, cung_cap, lan_cuoi):
		v = (nguon or {}).get(ma)
		if v:
			return v
	return CHUA_CO_NCC


def chia_so(cac_dong, tong):
	"""Chia số mua (đơn vị kho) xuống từng dòng phiếu xin, theo thứ tự đưa vào. THUẦN.

	cac_dong: [{"ten", "xin"}] với xin theo đơn vị kho. Mỗi dòng nhận tối đa
	số nó xin; mua nhiều hơn tổng xin (mua chẵn thùng) thì phần dôi vào dòng
	cuối, đúng luật "duyệt thêm" đã có từ 24/08/2026. Mua ít hơn thì dòng
	đầu (cần sớm nhất) được trước, dòng sau nhận phần còn lại hoặc 0.
	"""
	con = max(flt(tong), 0)
	ra = {}
	for i, d in enumerate(cac_dong or []):
		xin = max(flt(d.get("xin")), 0)
		if i == len(cac_dong) - 1:
			lay = con
		else:
			lay = min(xin, con)
		ra[d["ten"]] = round(lay, 6)
		con = round(con - lay, 6)
	return ra


def thue_cua_mon(mau_cua_mon, chi_tiet_mau, tk_vao="1331"):
	"""Thuế suất GTGT đầu vào (%) của từng món theo mẫu thuế khai trên món. THUẦN.

	mau_cua_mon: {ma: tên mẫu thuế}; chi_tiet_mau: {tên mẫu: [(tài khoản, thuế suất)]}.
	Lấy đúng dòng tài khoản 1331 (mẫu của site khai cả 1331 lẫn 33311). Món chưa
	khai mẫu, hay mẫu không có dòng 1331, thì không có trong kết quả."""
	ra = {}
	for ma, mau in (mau_cua_mon or {}).items():
		for tk, ts in (chi_tiet_mau or {}).get(mau) or []:
			if str(tk or "").split(" ")[0] == tk_vao:
				ra[ma] = flt(ts)
				break
	return ra


def gom(dong_yc, ncc_cua, boi_canh=None, gia=None, anh=None, ten_ncc=None, thue=None):
	"""Dòng phiếu xin -> nhóm theo nhà cung cấp, mỗi nhóm cộng theo món. THUẦN.

	dong_yc: [{ten, phieu, ma, ten_mon, xin (đơn vị kho), dvt (đơn vị kho), ngay,
	bo_phan}]. ncc_cua: {ma: nhà cung cấp}. Nhóm "chưa có nhà cung cấp" đứng
	cuối để thu mua chọn tay."""
	boi_canh, gia, anh, ten_ncc, thue = boi_canh or {}, gia or {}, anh or {}, ten_ncc or {}, thue or {}
	nhom = {}
	for d in sorted(dong_yc or [], key=lambda x: (str(x.get("ngay") or "9"), x.get("phieu") or "", x.get("ten") or "")):
		ncc = ncc_cua.get(d["ma"]) or CHUA_CO_NCC
		g = nhom.setdefault(ncc, {"ncc": ncc, "ten_ncc": ten_ncc.get(ncc) or ncc or "Chưa có nhà cung cấp",
			"mon": {}, "so_phieu": set()})
		m = g["mon"].setdefault(d["ma"], {"ma": d["ma"], "ten": d.get("ten_mon") or d["ma"], "dvt": d.get("dvt") or "",
			"xin": 0.0, "phieu": [], "ngay_can": "", "anh": anh.get(d["ma"]) or "",
			"ton": flt((boi_canh.get(d["ma"]) or {}).get("ton")),
			"cho_ve": flt((boi_canh.get(d["ma"]) or {}).get("cho_ve")),
			"gia": flt(gia.get(d["ma"])), "thue": thue.get(d["ma"])})
		m["xin"] = round(m["xin"] + flt(d.get("xin")), 6)
		m["phieu"].append({"phieu": d.get("phieu"), "bo_phan": d.get("bo_phan") or "", "xin": flt(d.get("xin")),
			"ngay": str(d.get("ngay") or "")})
		if d.get("ngay") and (not m["ngay_can"] or str(d["ngay"]) < m["ngay_can"]):
			m["ngay_can"] = str(d["ngay"])
		g["so_phieu"].add(d.get("phieu"))
	ra = []
	for ncc, g in nhom.items():
		mon = sorted(g["mon"].values(), key=lambda x: x["ten"])
		for m in mon:
			m["mua"] = m["xin"]
		ra.append({"ncc": ncc, "ten_ncc": g["ten_ncc"], "mon": mon, "so_mon": len(mon), "so_phieu": len(g["so_phieu"]),
			"tien": round(sum(m["mua"] * m["gia"] for m in mon)),
			"tien_thue": round(sum(m["mua"] * m["gia"] * flt(m.get("thue")) / 100 for m in mon))})
	ra.sort(key=lambda g: (g["ncc"] == CHUA_CO_NCC, g["ten_ncc"]))
	return ra


def doc_dong_chot(dong):
	"""Danh sách {ma, sl} gửi lên -> {ma: số mua}. Số âm, chữ hỏng bị từ chối. THUẦN."""
	if isinstance(dong, str):
		try:
			dong = json.loads(dong or "[]")
		except (ValueError, TypeError):
			return None, "Dữ liệu gửi lên không đọc được, thoát ra mở lại màn."
	ra = {}
	for x in dong or []:
		ma = str((x or {}).get("ma") or "").strip()
		if not ma:
			continue
		try:
			sl = float(str((x or {}).get("sl")).replace(",", "."))
		except (TypeError, ValueError):
			return None, "Số mua của %s chưa đúng." % ma
		if sl < 0:
			return None, "Số mua của %s không được âm." % ma
		ra[ma] = sl
	if not ra:
		return None, "Chưa có món nào để chốt."
	return ra, ""


# ============================================================ PHẦN CHẠM HỆ


def _kiem_quyen():
	from vagabond.quyen_phan_he import chan_neu_khong_thu_mua

	chan_neu_khong_thu_mua("gom yêu cầu mua thành đơn mua")


def dong_cho_gom(ma_hang=None):
	"""Dòng yêu cầu mua đã gửi, chưa ai duyệt, còn chưa đặt hết. Số quy về đơn vị kho."""
	dk, ts = "", {}
	if ma_hang:
		dk = " and mri.item_code in %(ma)s"
		ts["ma"] = tuple(ma_hang)
	rows = frappe.db.sql("""
		select mri.name as ten, mri.parent as phieu, mri.item_code as ma, mri.item_name as ten_mon,
			mri.qty, mri.ordered_qty, mri.conversion_factor as cf, mri.uom, mri.stock_uom as dvt,
			mri.warehouse as kho, mri.schedule_date as ngay, mr.company as cong_ty,
			mr.bo_phan_yeu_cau as bo_phan
		from `tabMaterial Request Item` mri
		join `tabMaterial Request` mr on mr.name = mri.parent
		where mr.material_request_type = 'Purchase' and mr.docstatus = 1
			and mr.status in ('Pending', 'Partially Ordered')
			and coalesce(mri.nguoi_duyet_dong, '') = ''
			and mri.qty > mri.ordered_qty""" + dk + """
		order by mri.schedule_date asc, mri.parent asc, mri.idx asc""", ts, as_dict=True)
	for r in rows:
		r["cf"] = flt(r.get("cf")) or 1
		r["xin"] = round((flt(r.get("qty")) - flt(r.get("ordered_qty"))) * r["cf"], 6)
	return rows


def _ncc_cua(cac_ma):
	if not cac_ma:
		return {}, {}
	mac = {r.parent: r.default_supplier for r in frappe.get_all("Item Default",
		filters={"parent": ["in", cac_ma], "parenttype": "Item"}, fields=["parent", "default_supplier"],
		limit_page_length=0) if r.get("default_supplier")}
	cung = {}
	for r in frappe.get_all("Item Supplier", filters={"parent": ["in", cac_ma], "parenttype": "Item"},
			fields=["parent", "supplier", "idx"], order_by="idx asc", limit_page_length=0):
		cung.setdefault(r.parent, r.supplier)
	cuoi = {}
	for r in frappe.db.sql("""select poi.item_code as ma, po.supplier as ncc
			from `tabPurchase Order Item` poi join `tabPurchase Order` po on po.name = poi.parent
			where po.docstatus = 1 and poi.item_code in %(ma)s
			order by po.transaction_date desc, po.creation desc""", {"ma": tuple(cac_ma)}, as_dict=True):
		cuoi.setdefault(r.ma, r.ncc)
	ncc = {m: chon_ncc(m, mac, cung, cuoi) for m in cac_ma}
	ten = {s.name: s.supplier_name for s in frappe.get_all("Supplier",
		filters={"name": ["in", sorted({v for v in ncc.values() if v})]}, fields=["name", "supplier_name"],
		limit_page_length=0)} if any(ncc.values()) else {}
	return ncc, ten


def _gia_anh(cac_ma):
	if not cac_ma:
		return {}, {}
	gia, anh = {}, {}
	for i in frappe.get_all("Item", filters={"name": ["in", cac_ma]}, fields=["name", "last_purchase_rate", "image"],
			limit_page_length=0):
		gia[i.name] = flt(i.get("last_purchase_rate"))
		anh[i.name] = i.get("image") or ""
	return gia, anh


def _thue(cac_ma):
	if not cac_ma:
		return {}
	mau = {}
	for r in frappe.get_all("Item Tax", filters={"parent": ["in", cac_ma], "parenttype": "Item"},
			fields=["parent", "item_tax_template", "idx"], order_by="idx asc", limit_page_length=0):
		if r.get("item_tax_template"):
			mau.setdefault(r.parent, r.item_tax_template)
	if not mau:
		return {}
	ct = {}
	for r in frappe.get_all("Item Tax Template Detail", filters={"parent": ["in", sorted(set(mau.values()))],
			"parenttype": "Item Tax Template"}, fields=["parent", "tax_type", "tax_rate"], limit_page_length=0):
		ct.setdefault(r.parent, []).append((r.tax_type, r.tax_rate))
	return thue_cua_mon(mau, ct)


@frappe.whitelist()
def ds():
	"""Màn Gom yêu cầu mua: nhóm theo nhà cung cấp, mỗi nhóm cộng theo món."""
	from vagabond import duyet_ycmh as dy

	_kiem_quyen()
	dong = dong_cho_gom()
	cac_ma = sorted({d["ma"] for d in dong})
	ncc, ten = _ncc_cua(cac_ma)
	gia, anh = _gia_anh(cac_ma)
	bc = {}
	try:
		# Codex #553 vòng 4: chip "Kho tổng" phải đếm đúng Kho tổng 307, không
		# cộng tồn bếp (hàng ở bếp không kéo ngược về kho tổng để bớt mua).
		from vagabond.kho_san_xuat import KHO_GOC

		bc = dy.boi_canh_hang(cac_ma, kho=KHO_GOC) if cac_ma else {}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gom_mua: bối cảnh hàng")
	thue = {}
	try:
		thue = _thue(cac_ma)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gom_mua: thuế của món")
	nhom = gom(dong, ncc, bc, gia, anh, ten, thue)
	return {"nhom": nhom, "so_dong": len(dong), "so_mon": len(cac_ma),
		"so_phieu": len({d["phieu"] for d in dong})}


def _ghi_duyet(dong_theo_phieu, nguoi, luc, ly_do_0):
	"""Ghi phần duyệt lên từng phiếu xin, dùng đúng luật soát của màn Duyệt."""
	from vagabond import duyet_ycmh as dy

	for phieu, chia in dong_theo_phieu.items():
		d = frappe.get_doc("Material Request", phieu, for_update=True)
		vet = []
		for r in d.items:
			if r.name not in chia:
				continue
			if (r.get("nguoi_duyet_dong") or "").strip():
				frappe.throw("Dòng %s của phiếu %s vừa được người khác duyệt. Tải lại màn rồi chốt lại."
					% (r.item_name or r.item_code, phieu))
			sl = round(flt(chia[r.name]) / (flt(r.conversion_factor) or 1), 6)
			sl_duyet = round(flt(r.ordered_qty) + sl, 6)
			ly = ly_do_0 if sl_duyet <= EPS else ""
			loi, _ = dy.soat_so_duyet(sl_duyet, r.qty, r.ordered_qty, ly, r.item_name or r.item_code)
			if loi:
				frappe.throw("<br>".join(loi))
			r.sl_duyet = sl_duyet
			r.ly_do_duyet = ly or None
			r.nguoi_duyet_dong = nguoi
			r.duyet_luc = luc
			if sl_duyet <= EPS:
				r.trang_thai_cung_ung = dy.TT_TU_CHOI
			vet.append("%s xin %s, duyệt %s" % (r.item_name or r.item_code, dy._so(r.qty), dy._so(sl_duyet)))
		d.flags.ignore_permissions = True
		d.save()
		if vet:
			dy._ghi_vet(phieu, "Gom yêu cầu mua: " + "; ".join(vet))


def _lap_don(ncc, dong, chia):
	"""Đơn mua cho một nhà cung cấp, mỗi dòng nối về đúng dòng phiếu xin."""
	po = frappe.new_doc("Purchase Order")
	po.supplier = ncc
	po.company = dong[0].get("cong_ty")
	po.transaction_date = getdate(nowdate())
	ngay = [getdate(d["ngay"]) for d in dong if d.get("ngay")]
	po.schedule_date = max(min(ngay), getdate(nowdate())) if ngay else getdate(nowdate())
	gia, _ = _gia_anh(sorted({d["ma"] for d in dong}))
	for d in dong:
		sl_kho = flt(chia.get(d["ten"]))
		if sl_kho <= EPS:
			continue
		cf = flt(d.get("cf")) or 1
		dong_po = {"item_code": d["ma"], "qty": round(sl_kho / cf, 6), "uom": d.get("uom") or d.get("dvt"),
			"stock_uom": d.get("dvt"), "conversion_factor": cf, "warehouse": d.get("kho"),
			"schedule_date": max(getdate(d["ngay"]), po.schedule_date) if d.get("ngay") else po.schedule_date,
			"material_request": d["phieu"], "material_request_item": d["ten"]}
		if gia.get(d["ma"]):
			dong_po["rate"] = round(gia[d["ma"]] * cf, 4)
		po.append("items", dong_po)
	return po


def loc_ncc(ds, tu_khoa=""):
	"""THUẦN: lọc danh mục nhà cung cấp cho ô chọn (Codex 549, AGENTS.md QT-31).

	Gõ không dấu vẫn ra ("nguyen bao" khớp "Nguyễn Bảo"), khớp cả mã danh mục
	và mã số thuế. Nhà chưa có tên thì hiện mã để vẫn chọn được."""
	from vagabond.duong_app import khong_dau

	tu = khong_dau(tu_khoa or "").lower().split()
	ra = []
	for x in ds or []:
		ten = (x.get("supplier_name") or "").strip() or x.get("name")
		chu = khong_dau(" ".join([x.get("name") or "", ten, x.get("tax_id") or ""])).lower()
		if all(t in chu for t in tu):
			ra.append({"ncc": x.get("name"), "ten": ten, "mst": x.get("tax_id") or ""})
	return ra


@frappe.whitelist()
def tim_ncc(tu_khoa=""):
	"""Danh mục nhà cung cấp đang dùng cho ô chọn khi chốt nhóm chưa có nhà cung cấp."""
	_kiem_quyen()
	ds = frappe.get_all("Supplier", filters={"disabled": 0}, fields=["name", "supplier_name", "tax_id"],
		order_by="supplier_name asc", limit_page_length=0)
	return {"ds": loc_ncc(ds, tu_khoa)}


@frappe.whitelist(methods=["POST"])
def chot(ncc, dong, ncc_chon=None):
	"""Chốt một nhóm: ghi phần duyệt lên phiếu xin rồi lập đơn mua cho nhà cung cấp.

	Đọc lại dòng phiếu xin NGAY LÚC CHỐT, không tin danh sách máy khách gửi
	lên: giữa lúc mở màn và lúc bấm, phiếu có thể đã được người khác duyệt.
	Mọi thứ trong một giao dịch: lập đơn hỏng thì phần duyệt cũng lùi."""
	_kiem_quyen()
	so, loi = doc_dong_chot(dong)
	if loi:
		frappe.throw(loi)
	ncc = (ncc or "").strip()
	ncc_that = (ncc_chon or "").strip() or ncc
	if not ncc_that:
		frappe.throw("Nhóm này chưa có nhà cung cấp. Chọn nhà cung cấp rồi chốt.")
	if not frappe.db.exists("Supplier", ncc_that):
		frappe.throw("Không tìm thấy nhà cung cấp %s trong danh mục." % ncc_that)

	dong_all = dong_cho_gom(sorted(so))
	cac_ma = sorted({d["ma"] for d in dong_all})
	ncc_cua, _ = _ncc_cua(cac_ma)
	dong = [d for d in dong_all if (ncc_cua.get(d["ma"]) or CHUA_CO_NCC) == ncc]
	thieu = sorted(set(so) - {d["ma"] for d in dong})
	if thieu:
		frappe.throw("Món %s không còn dòng chờ gom ở nhóm này (có thể vừa được duyệt). Tải lại màn rồi chốt lại."
			% ", ".join(thieu))

	chia = {}
	theo_phieu = {}
	for ma, sl in so.items():
		cac = [d for d in dong if d["ma"] == ma]
		phan = chia_so([{"ten": d["ten"], "xin": d["xin"]} for d in cac], sl)
		chia.update(phan)
		for d in cac:
			theo_phieu.setdefault(d["phieu"], {})[d["ten"]] = phan.get(d["ten"], 0)

	nguoi, luc = frappe.session.user, now_datetime()
	ly_do_0 = "Thu mua gom đơn %s: chưa mua đợt này" % getdate(nowdate()).strftime("%d/%m")
	frappe.db.savepoint("gom_mua_chot")
	try:
		_ghi_duyet(theo_phieu, nguoi, luc, ly_do_0)
		po = _lap_don(ncc_that, dong, chia)
		if not po.items:
			frappe.db.commit()
			return {"ok": 1, "don": "", "ghi_chu": "Đã ghi: mọi món nhóm này để 0, không lập đơn mua."}
		po.flags.ignore_permissions = True
		po.insert()
	except Exception:
		frappe.db.rollback(save_point="gom_mua_chot")
		raise
	frappe.db.commit()
	# Ghi sổ đơn là bước riêng: thiếu giá hay ngày thì đơn còn NHÁP, phần
	# duyệt và đơn nháp vẫn giữ, thu mua mở đơn sửa rồi xác nhận.
	frappe.db.savepoint("gom_mua_ghi_so")
	try:
		po.submit()
		frappe.db.commit()
		return {"ok": 1, "don": po.name, "da_xac_nhan": 1, "ghi_chu": "Đã lập và xác nhận đơn mua %s cho %s, %d dòng. "
			"Gửi đơn cho nhà cung cấp ở màn Đơn mua hàng." % (po.name, ncc_that, len(po.items))}
	except Exception as e:
		frappe.db.rollback(save_point="gom_mua_ghi_so")
		frappe.db.commit()
		return {"ok": 1, "don": po.name, "da_xac_nhan": 0, "ghi_chu": "Đã lập đơn mua %s ở dạng NHÁP, chưa xác nhận được: %s"
			% (po.name, frappe.utils.strip_html(str(e))[:300])}


def dem_cho_gom():
	"""Số món, số phiếu đang chờ gom (cho Việc cần làm và nhịp nhắc)."""
	dong = dong_cho_gom()
	return len({d["ma"] for d in dong}), len({d["phieu"] for d in dong})
