"""Duyet tung dong tren Phieu yeu cau mua hang (anh Viet duyet 15/08/2026).

Bai toan cua Uyen
-----------------
Nhan vien cac bo phan dat trung mat hang: thu hai dat muoi chua ve, thu nam
lai dat tiep. Hoac dat du trong khi kho tong con day. Uyen muon tu choi
DUNG MOT DONG chu khong huy ca phieu.

Rang buoc anh Viet dat ra: tuyet doi khong sua de len so luong goc cua nhan
vien, va khong xoa vat ly dong nao.

Phuong an da chot (PA-3)
------------------------
Giu nguyen `qty`. Them `sl_duyet` va `ly_do_duyet` ben canh.

    sl_duyet de trong   chua ai duyet
    sl_duyet = 0        TU CHOI, bat buoc co ly do
    0 < sl_duyet < qty  duyet mot phan
    sl_duyet = qty      duyet du
    sl_duyet > qty      KHONG BAO GIO. Muon mua them thi lap phieu moi.

Hai phuong an bi loai: sua de len `qty` thi mat so goc va phai mo quyen sua
sau khi gui duyet ngay tren chinh o so luong; xoa dong thi vi pham QT-20.

Phan dang gia nhat cua man nay khong phai nut tu choi
----------------------------------------------------
Nut tu choi chi la hanh dong cuoi. Cai lam Uyen mat thoi gian la KHONG BIET
VI SAO NEN TU CHOI. Nen man nay in san ba con so tren tung dong:

    ton kho tong        hang dang nam trong kho
    dang cho ve         da dat don mua, nha cung cap chua giao
    dang cho duyet      cung mat hang dang nam o phieu khac chua xu ly

Ba con so do tinh bang BA cau hoi cho CA PHIEU, khong phai ba cau cho moi
dong - xem boi_canh_hang.
"""

import json

import frappe
from frappe.utils import cint, flt, now_datetime

QUYEN_DUYET = {
	"System Manager",
	"Purchase Manager",
	"Purchase User",
	"Accounts Manager",
	"Bộ phận đặt hàng",
}

# Sai so cho phep khi so sanh so luong co phan le (kg, lit).
EPS = 0.0001

LOAI = "Purchase"

# Trang thai cung ung san co tren dong, them mot gia tri cho dong bi tu choi.
TT_TU_CHOI = "Từ chối"

# Cac truong tu them, khai o day de after_migrate tu dung lai moi lan deploy.
# Tat ca deu allow_on_submit: phieu da gui duyet roi moi den luot thu mua
# duyet, neu khong cho sua sau khi gui thi khong lam gi duoc.
TRUONG_MOI = {
	"Material Request Item": [
		{
			"fieldname": "sec_duyet_mua",
			"label": "Thu mua duyệt dòng này",
			"fieldtype": "Section Break",
			"insert_after": "trang_thai_cung_ung",
			"collapsible": 0,
		},
		{
			"fieldname": "sl_duyet",
			"label": "Số lượng duyệt",
			"fieldtype": "Float",
			"insert_after": "sec_duyet_mua",
			"allow_on_submit": 1,
			"in_list_view": 0,
			"description": (
				"Để trống là chưa ai duyệt. Bằng 0 là từ chối dòng này. "
				"Không bao giờ được lớn hơn số lượng yêu cầu."
			),
		},
		{
			"fieldname": "ly_do_duyet",
			"label": "Lý do cắt hoặc từ chối",
			"fieldtype": "Small Text",
			"insert_after": "sl_duyet",
			"allow_on_submit": 1,
		},
		{
			"fieldname": "nguoi_duyet_dong",
			"label": "Người duyệt dòng",
			"fieldtype": "Data",
			"insert_after": "ly_do_duyet",
			"allow_on_submit": 1,
			"read_only": 1,
		},
		{
			"fieldname": "duyet_luc",
			"label": "Duyệt lúc",
			"fieldtype": "Datetime",
			"insert_after": "nguoi_duyet_dong",
			"allow_on_submit": 1,
			"read_only": 1,
		},
	]
}


def dam_bao_truong():
	"""Dung cac truong tu them, chay sau moi lan deploy.

	Khai bang ma nguon chu khong bam tay tren Desk: bam tay thi site thu va
	site that lech nhau, va khong ai doc lai duoc vi sao co truong do.
	"""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(TRUONG_MOI, update=True)
	_them_trang_thai_tu_choi()


def _them_trang_thai_tu_choi():
	"""Bo sung "Từ chối" vao o chon trang thai cung ung, giu nguyen cac gia
	tri cu. Khong ghi de ca danh sach: cac gia tri cu dang nam tren du lieu
	that, ghi de la hong het cac dong do."""
	for dt in ("Material Request Item", "Material Request"):
		ten = frappe.db.get_value(
			"Custom Field", {"dt": dt, "fieldname": "trang_thai_cung_ung"}, "name"
		)
		if not ten:
			continue
		cu = frappe.db.get_value("Custom Field", ten, "options") or ""
		if TT_TU_CHOI in [x.strip() for x in cu.split("\n")]:
			continue
		frappe.db.set_value("Custom Field", ten, "options", cu.rstrip("\n") + "\n" + TT_TU_CHOI)


def _kiem_quyen():
	if not QUYEN_DUYET & set(frappe.get_roles()):
		frappe.throw(
			"Duyệt yêu cầu mua hàng chỉ mở cho thu mua, kế toán và giám đốc. "
			"Cần vào đây thì báo quản lý cấp quyền Bộ phận đặt hàng."
		)


def _ghi_vet(name, viec):
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Material Request",
				"reference_name": name,
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "duyet_ycmh: ghi vet %s" % name)


# --------------------------------------------------------- ba con so nen


def boi_canh_hang(ma_hang, bo_qua_phieu=None):
	"""Ba con so giup thu mua quyet dinh, quy ve DON VI KHO cua tung mat hang.

	Tra ve {ma_hang: {ton, cho_ve, so_don_cho_ve, hen_gan_nhat,
	                  cho_duyet, so_phieu_cho_duyet}}

	Ba cau hoi cho CA PHIEU chu khong phai ba cau cho moi dong. Mot phieu
	hai muoi dong ma de moi dong tu di hoi la sau muoi cau hoi, man hinh
	treo va khong ai hieu vi sao cham.

	Con so tra ve nam o don vi kho cua mat hang. Doi sang don vi cua dong
	yeu cau la viec cua ham goi, vi he so quy doi nam tren chinh dong do.
	"""
	ds = sorted({str(x).strip() for x in (ma_hang or []) if str(x or "").strip()})
	if not ds:
		return {}
	ra = {
		m: {
			"ton": 0.0,
			"cho_ve": 0.0,
			"so_don_cho_ve": 0,
			"hen_gan_nhat": "",
			"cho_duyet": 0.0,
			"so_phieu_cho_duyet": 0,
		}
		for m in ds
	}

	# 1. TON KHO TONG. Bin giu san so luong theo don vi kho nen chi phai cong.
	for r in frappe.db.sql(
		"""select item_code, sum(actual_qty) as sl
		from `tabBin` where item_code in %(ds)s group by item_code""",
		{"ds": ds},
		as_dict=True,
	):
		ra[r["item_code"]]["ton"] = flt(r["sl"])

	# 2. DANG CHO VE. Da dat don mua, nha cung cap chua giao het.
	#    Bo don da huy mem va don da dong: hai loai do khong con hang se ve.
	#    Nhan he so quy doi vi qty tren don nam o don vi mua (thung, hop),
	#    con ton kho o tren nam o don vi kho (kg, cai).
	for r in frappe.db.sql(
		"""select poi.item_code,
			sum((poi.qty - poi.received_qty) * poi.conversion_factor) as sl,
			count(distinct poi.parent) as so_don,
			min(po.schedule_date) as hen
		from `tabPurchase Order Item` poi
		join `tabPurchase Order` po on po.name = poi.parent
		where poi.item_code in %(ds)s
			and poi.docstatus = 1
			and po.status not in ('Closed', 'Completed')
			and ifnull(po.vgb_huy, 0) = 0
			and poi.qty - poi.received_qty > %(eps)s
		group by poi.item_code""",
		{"ds": ds, "eps": EPS},
		as_dict=True,
	):
		o = ra[r["item_code"]]
		o["cho_ve"] = flt(r["sl"])
		o["so_don_cho_ve"] = cint(r["so_don"])
		o["hen_gan_nhat"] = str(r["hen"] or "")

	# 3. DANG CHO DUYET O PHIEU KHAC. Chinh la cai bay anh Viet mo ta: thu
	#    hai dat muoi chua ve, thu nam lai dat tiep. Dem theo SO DA DUYET neu
	#    thu mua da duyet roi, chua duyet thi dem theo so yeu cau.
	dk_bo_qua = " and mri.parent != %(bo_qua)s" if bo_qua_phieu else ""
	for r in frappe.db.sql(
		"""select mri.item_code,
			sum((ifnull(mri.sl_duyet, mri.qty) - mri.ordered_qty)
				* mri.conversion_factor) as sl,
			count(distinct mri.parent) as so_phieu
		from `tabMaterial Request Item` mri
		join `tabMaterial Request` mr on mr.name = mri.parent
		where mri.item_code in %(ds)s
			and mri.docstatus = 1
			and mr.material_request_type = %(loai)s
			and mr.status not in ('Stopped', 'Cancelled')
			and ifnull(mri.sl_duyet, mri.qty) - mri.ordered_qty > %(eps)s"""
		+ dk_bo_qua
		+ """
		group by mri.item_code""",
		{"ds": ds, "loai": LOAI, "eps": EPS, "bo_qua": bo_qua_phieu or ""},
		as_dict=True,
	):
		o = ra[r["item_code"]]
		o["cho_duyet"] = flt(r["sl"])
		o["so_phieu_cho_duyet"] = cint(r["so_phieu"])
	return ra


def _canh_bao(x, xin):
	"""Cau canh bao in tren dong, hoac chuoi rong khi khong co gi dang noi.

	Ham THUAN, khong doc co so du lieu, de kiem thu op vao duoc.
	"""
	if xin <= EPS:
		return ""
	y = []
	if x["ton"] >= xin - EPS:
		y.append("Kho còn %s, đủ cho yêu cầu này" % _so(x["ton"]))
	elif x["ton"] > EPS:
		y.append("Kho còn %s" % _so(x["ton"]))
	if x["cho_ve"] > EPS:
		y.append(
			"Đang có %s chờ về từ %d đơn đã đặt%s"
			% (
				_so(x["cho_ve"]),
				x["so_don_cho_ve"],
				(", hẹn %s" % _ngay_vn(x["hen_gan_nhat"])) if x["hen_gan_nhat"] else "",
			)
		)
	if x["cho_duyet"] > EPS:
		y.append(
			"Còn %s đang chờ duyệt ở %d phiếu khác"
			% (_so(x["cho_duyet"]), x["so_phieu_cho_duyet"])
		)
	return ". ".join(y)


def _muc_canh_bao(x, xin):
	"""Do gat: 0 khong co gi, 1 dang luu y, 2 gan nhu chac chan la dat thua.

	Ham THUAN. Muc 2 danh cho truong hop rieng ton kho da du, hoac ton cong
	hang dang cho ve da du - do la luc Uyen nen tu choi.
	"""
	if xin <= EPS:
		return 0
	if x["ton"] >= xin - EPS:
		return 2
	if x["ton"] + x["cho_ve"] >= xin - EPS and x["cho_ve"] > EPS:
		return 2
	if x["cho_ve"] > EPS or x["cho_duyet"] > EPS or x["ton"] > EPS:
		return 1
	return 0


def _so(v):
	v = flt(v)
	return str(int(v)) if abs(v - int(v)) < EPS else ("%.3f" % v).rstrip("0").rstrip(".")


def _ngay_vn(s):
	p = str(s or "").split("-")
	return "%s/%s/%s" % (p[2], p[1], p[0]) if len(p) == 3 else str(s or "")


# ------------------------------------------------------------- man hinh


@frappe.whitelist()
def danh_sach(so_ngay=45, chi_con_cho=1):
	"""Cac phieu yeu cau mua dang cho thu mua xu ly."""
	_kiem_quyen()
	from frappe.utils import add_days, nowdate

	loc = {"material_request_type": LOAI, "docstatus": 1}
	so_ngay = cint(so_ngay or 0)
	if so_ngay:
		loc["transaction_date"] = [">=", add_days(nowdate(), -so_ngay)]
	if cint(chi_con_cho):
		loc["status"] = ["in", ["Pending", "Partially Ordered"]]
	phieu = frappe.get_all(
		"Material Request",
		filters=loc,
		fields=[
			"name", "transaction_date", "schedule_date", "status",
			"bo_phan_yeu_cau", "nguoi_yeu_cau", "nguoi_lap_ten", "owner",
		],
		order_by="schedule_date asc, name asc",
		limit_page_length=0,
	)
	if not phieu:
		return {"phieu": [], "tong_dong": 0}

	# Dem dong da duyet va dong con cho, mot cau hoi cho ca tap.
	dem = {}
	for r in frappe.db.sql(
		"""select parent,
			count(*) as tong,
			sum(case when sl_duyet is null then 1 else 0 end) as cho,
			sum(case when sl_duyet is not null and sl_duyet <= %(eps)s
				then 1 else 0 end) as tu_choi
		from `tabMaterial Request Item`
		where parent in %(ds)s and docstatus = 1
		group by parent""",
		{"ds": [p["name"] for p in phieu], "eps": EPS},
		as_dict=True,
	):
		dem[r["parent"]] = r

	ra = []
	for p in phieu:
		d = dem.get(p["name"]) or {}
		ra.append(
			dict(
				p,
				ngay=str(p["transaction_date"] or ""),
				can_ngay=str(p["schedule_date"] or ""),
				so_dong=cint(d.get("tong")),
				con_cho=cint(d.get("cho")),
				da_tu_choi=cint(d.get("tu_choi")),
			)
		)
	# Phieu con dong chua duyet len dau, roi den phieu can gap nhat.
	ra.sort(key=lambda x: (0 if x["con_cho"] else 1, x["can_ngay"] or "9999-12-31"))
	return {"phieu": ra, "tong_dong": len(ra)}


@frappe.whitelist()
def chi_tiet(name):
	"""Mot phieu yeu cau, moi dong kem ba con so va cau canh bao."""
	_kiem_quyen()
	d = frappe.get_doc("Material Request", name)
	if d.material_request_type != LOAI:
		frappe.throw(
			"Phiếu %s không phải yêu cầu mua hàng nên không duyệt ở màn này." % name
		)
	if d.docstatus != 1:
		frappe.throw(
			"Phiếu %s chưa gửi duyệt nên chưa có gì để thu mua xem. "
			"Người lập bấm Gửi duyệt trước." % name
		)

	bc = boi_canh_hang([r.item_code for r in d.items], bo_qua_phieu=name)
	mon = []
	for r in d.items:
		he_so = flt(r.conversion_factor) or 1.0
		# Quy ba con so ve DUNG DON VI cua dong yeu cau. Uyen so sanh "xin 20
		# kg, kho con 12 kg" chu khong so sanh hai don vi khac nhau.
		g = bc.get(r.item_code) or {}
		x = {
			"ton": flt(g.get("ton")) / he_so,
			"cho_ve": flt(g.get("cho_ve")) / he_so,
			"so_don_cho_ve": cint(g.get("so_don_cho_ve")),
			"hen_gan_nhat": g.get("hen_gan_nhat") or "",
			"cho_duyet": flt(g.get("cho_duyet")) / he_so,
			"so_phieu_cho_duyet": cint(g.get("so_phieu_cho_duyet")),
		}
		xin = flt(r.qty)
		duyet = r.get("sl_duyet")
		mon.append(
			{
				"dong": r.name,
				"ma": r.item_code,
				"ten": r.item_name or r.item_code,
				"dvt": r.uom or r.stock_uom or "",
				"sl_yeu_cau": xin,
				"sl_duyet": None if duyet is None else flt(duyet),
				"ly_do_duyet": r.get("ly_do_duyet") or "",
				"nguoi_duyet_dong": r.get("nguoi_duyet_dong") or "",
				"duyet_luc": str(r.get("duyet_luc") or ""),
				"da_len_don": flt(r.ordered_qty),
				"trang_thai_cung_ung": r.get("trang_thai_cung_ung") or "",
				"can_ngay": str(r.schedule_date or ""),
				"mo_ta": frappe.utils.strip_html(r.description or "").strip()[:400],
				"ton": x["ton"],
				"cho_ve": x["cho_ve"],
				"so_don_cho_ve": x["so_don_cho_ve"],
				"hen_gan_nhat": x["hen_gan_nhat"],
				"cho_duyet": x["cho_duyet"],
				"so_phieu_cho_duyet": x["so_phieu_cho_duyet"],
				"canh_bao": _canh_bao(x, xin),
				"muc_canh_bao": _muc_canh_bao(x, xin),
			}
		)
	return {
		"name": d.name,
		"ngay": str(d.transaction_date or ""),
		"can_ngay": str(d.schedule_date or ""),
		"trang_thai": d.status,
		"bo_phan": d.get("bo_phan_yeu_cau") or "",
		"nguoi_yeu_cau": d.get("nguoi_yeu_cau") or d.get("nguoi_lap_ten") or d.owner,
		"kho_nhan": d.get("set_warehouse") or "",
		"mon": mon,
		"con_cho": len([x for x in mon if x["sl_duyet"] is None]),
		"da_tu_choi": len([x for x in mon if x["sl_duyet"] is not None and x["sl_duyet"] <= EPS]),
	}


# ---------------------------------------------------------------- ghi


@frappe.whitelist()
def duyet_dong(name, dong=None):
	"""Ghi so luong duyet cho mot hoac nhieu dong.

	KHONG dung den `qty`. So goc cua nhan vien nam nguyen, doi chieu duoc
	bat cu luc nao (rang buoc anh Viet dat ra).
	"""
	_kiem_quyen()
	if isinstance(dong, str):
		try:
			dong = json.loads(dong or "[]")
		except (ValueError, TypeError):
			frappe.throw("Dữ liệu gửi lên không đọc được, thoát ra mở lại phiếu giúp em.")
	if not dong:
		frappe.throw("Chưa có dòng nào để duyệt.")

	d = frappe.get_doc("Material Request", name)
	if d.material_request_type != LOAI:
		frappe.throw("Phiếu %s không phải yêu cầu mua hàng." % name)
	if d.docstatus != 1:
		frappe.throw("Phiếu %s chưa gửi duyệt nên chưa duyệt dòng được." % name)

	theo_ten = {r.name: r for r in d.items}
	dem = {"duyet_du": 0, "cat_bot": 0, "tu_choi": 0}
	vet = []
	for x in dong:
		khoa = str((x or {}).get("dong") or "").strip()
		r = theo_ten.get(khoa)
		if not r:
			frappe.throw(
				"Có dòng không thuộc phiếu %s. Thoát ra mở lại phiếu rồi duyệt "
				"lại giúp em." % name
			)
		sl = flt((x or {}).get("sl_duyet"))
		ly = str((x or {}).get("ly_do_duyet") or "").strip()

		if sl < -EPS:
			frappe.throw("Số lượng duyệt không được âm (%s)." % (r.item_name or r.item_code))
		if sl > flt(r.qty) + EPS:
			frappe.throw(
				"%s: duyệt %s nhưng nhân viên chỉ xin %s. Không duyệt quá số đã "
				"xin được - cần mua thêm thì lập phiếu yêu cầu mới, để số gốc "
				"còn đối chiếu."
				% (r.item_name or r.item_code, _so(sl), _so(r.qty))
			)
		if sl <= EPS and not ly:
			frappe.throw(
				"%s: từ chối thì phải ghi lý do, để nhân viên đặt hàng biết vì "
				"sao mà lần sau không đặt lại." % (r.item_name or r.item_code)
			)
		# Da len don mua roi thi khong cho cat xuong duoi so da dat: hang da
		# tren duong ve, cat so tren giay khong lam hang quay dau lai.
		if sl < flt(r.ordered_qty) - EPS:
			frappe.throw(
				"%s: đã lên đơn mua %s rồi nên không duyệt xuống %s được. Muốn "
				"dừng thì huỷ hoặc đóng đơn mua trước."
				% (r.item_name or r.item_code, _so(r.ordered_qty), _so(sl))
			)

		r.sl_duyet = sl
		r.ly_do_duyet = ly
		r.nguoi_duyet_dong = frappe.session.user
		r.duyet_luc = now_datetime()
		if sl <= EPS:
			r.trang_thai_cung_ung = TT_TU_CHOI
			dem["tu_choi"] += 1
			vet.append("từ chối %s (%s)" % (r.item_name or r.item_code, ly))
		elif sl < flt(r.qty) - EPS:
			dem["cat_bot"] += 1
			vet.append(
				"cắt %s từ %s xuống %s%s"
				% (r.item_name or r.item_code, _so(r.qty), _so(sl), (" (%s)" % ly) if ly else "")
			)
		else:
			dem["duyet_du"] += 1

	# save() tren phieu da ghi so: Frappe chi cho doi cac truong allow_on_submit
	# va tu ghi mot ban Version. Nho vay ghi vet co san, khong phai tu dung
	# bang nhat ky rieng (QT-20).
	d.flags.ignore_permissions = True
	d.save()
	if vet:
		_ghi_vet(name, "Duyệt yêu cầu mua: " + "; ".join(vet))
	frappe.db.commit()
	return dict(dem, name=name)


@frappe.whitelist()
def bo_duyet(name, dong_ten, ly_do=None):
	"""Go quyet dinh duyet cua mot dong, tra ve trang thai chua ai duyet.

	Bam nham thi phai sua duoc. Khong xoa gi, chi dua o duyet ve trong va
	ghi vet lai viec go.
	"""
	_kiem_quyen()
	d = frappe.get_doc("Material Request", name)
	r = {x.name: x for x in d.items}.get(str(dong_ten or "").strip())
	if not r:
		frappe.throw("Không thấy dòng này trên phiếu %s." % name)
	if flt(r.ordered_qty) > EPS:
		frappe.throw(
			"%s đã lên đơn mua rồi nên không gỡ duyệt được."
			% (r.item_name or r.item_code)
		)
	cu = r.get("sl_duyet")
	r.sl_duyet = None
	r.ly_do_duyet = None
	r.nguoi_duyet_dong = None
	r.duyet_luc = None
	if r.get("trang_thai_cung_ung") == TT_TU_CHOI:
		r.trang_thai_cung_ung = "Chờ mua"
	d.flags.ignore_permissions = True
	d.save()
	_ghi_vet(
		name,
		"Gỡ duyệt %s (đang là %s). Lý do: %s"
		% (
			r.item_name or r.item_code,
			"chưa duyệt" if cu is None else _so(cu),
			(ly_do or "").strip() or "không ghi",
		),
	)
	frappe.db.commit()
	return {"ok": 1}


# ------------------------------------------------- hang rao cho ha nguon


def chan_don_mua_trai_duyet(doc, method=None):
	"""Chan don mua hang dat qua so thu mua da duyet.

	Vi sao phai co: app khong tao don mua tu phieu yeu cau, nhung ERPNext
	tren Desk co nut "Create > Purchase Order" va nut do doc `qty`, khong
	biet gi ve `sl_duyet`. Neu khong chan o day thi mot dong da tu choi van
	len duoc don mua, va ca man duyet thanh vo nghia.

	Chan chu khong tu cat: cat lang le thi nguoi dat hang khong hieu vi sao
	so bi doi (QT-24).
	"""
	khoa = [r.material_request_item for r in (doc.get("items") or []) if r.get("material_request_item")]
	if not khoa:
		return
	duyet = {
		r["name"]: r
		for r in frappe.get_all(
			"Material Request Item",
			filters={"name": ["in", khoa]},
			fields=["name", "item_name", "item_code", "qty", "sl_duyet", "ly_do_duyet"],
			limit_page_length=0,
		)
	}
	loi = []
	for r in doc.get("items") or []:
		m = duyet.get(r.get("material_request_item"))
		if not m or m.get("sl_duyet") is None:
			continue
		cho = flt(m["sl_duyet"])
		ten = m.get("item_name") or m.get("item_code")
		if cho <= EPS:
			loi.append(
				"%s đã bị thu mua từ chối%s"
				% (ten, (": %s" % m["ly_do_duyet"]) if m.get("ly_do_duyet") else "")
			)
		elif flt(r.qty) > cho + EPS:
			loi.append(
				"%s: thu mua chỉ duyệt %s nhưng đơn đang đặt %s"
				% (ten, _so(cho), _so(r.qty))
			)
	if loi:
		frappe.throw(
			"Đơn mua không khớp với phần thu mua đã duyệt trên phiếu yêu cầu:"
			"<br>%s<br><br>Sửa lại số trên đơn cho khớp, hoặc mở màn Duyệt yêu "
			"cầu mua để duyệt lại dòng đó." % "<br>".join(loi)
		)
