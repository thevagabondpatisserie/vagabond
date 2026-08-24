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

    nguoi_duyet_dong trong  chua ai duyet
    sl_duyet = 0            TU CHOI, bat buoc co ly do
    0 < sl_duyet < qty      duyet mot phan
    sl_duyet = qty          duyet du
    sl_duyet > qty          duyet THEM, tu 24/08/2026 (xem soat_so_duyet)

Luat "khong bao gio duyet qua so xin" da duoc noi long ngay 24/08/2026 theo
yeu cau cua anh Viet: mua chan thung thi so mua thuc te phai lon hon so xin.
Phan con giu nguyen la `qty` khong bao gio bi sua de len.

Su co 17/08/2026 va vi sao dau hieu "da duyet" nam o nguoi_duyet_dong
---------------------------------------------------------------------
Ban dau lay "sl_duyet de trong" lam dau hieu chua ai duyet. Sai: sl_duyet
la kieu Float, ma Float trong Frappe KHONG giu duoc gia tri trong, luon ve
0. Nen moi dong chua ai dung toi deu doc ra 0, tuc la "tu choi". Ket qua:
1.321 dong bi coi la da tu choi va khong ra duoc mot don mua nao trong hai
ngay 15 den 17/08.

Dau hieu dung la `nguoi_duyet_dong`, kieu Data, giu duoc chuoi rong that.
Ba cho phai dung chung mot dau hieu nay: chan_don_mua_trai_duyet, danh_sach
va chi_tiet. Dung bao gio quay lai kiem tra `sl_duyet is None`.

Luat da chot (PA A+, anh Viet 17/08/2026): mon nao chua co ten nguoi duyet
thi TUYET DOI khong keo len don mua duoc. De Uyen do mat thoi gian, co nut
"Duyet tat ca cac mon con lai" o cuoi man - xem ham duyet_het.

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

from vagabond.quyen_phan_he import QUYEN_THU_MUA

from frappe.utils import cint, flt, now_datetime

# Duyet yeu cau mua la quyet dinh MUA hay khong, va nhin thay ca gia. Do la
# viec cua Thu mua chu khong phai cua nguoi lap yeu cau - truoc 18/08/2026
# vai "Bo phan dat hang" nam trong day nen ai lap yeu cau cung tu duyet
# duoc yeu cau cua chinh minh.
QUYEN_DUYET = QUYEN_THU_MUA

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
			"Duyệt yêu cầu mua hàng chỉ mở cho Thu mua, Kế toán và Giám đốc. "
			"Cần vào đây thì báo anh Việt cấp thêm chức vụ Thu mua trong màn "
			"Quản lý người dùng."
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


# ------------------------------------------------------ phep thuan soat so


# Nguoi duyet duoc phep duyet CAO HON so nhan vien xin, ke tu 24/08/2026.
# Anh Viet: *"Cho phep nguoi co quyen duyet duoc phep chinh sua so luong
# duyet CAO HON so luong yeu cau (vi du: Quan ly yeu cau 5, Uyen co quyen
# sua thanh 6 de mua cho chan thung/don vi dong goi)."*
#
# Truoc do luat chan cung, va cai ly cua no van dung mot nua: so goc cua
# nhan vien phai con nguyen de doi chieu. Cho nen van KHONG sua `qty`, chi
# cho `sl_duyet` vuot len tren. Hai so nam canh nhau, chenh lech bao nhieu
# nhin la thay.
#
# Doi lai phai co ba lop de con lan ra ai da nang so:
#   1. man hinh hoi xac nhan truoc khi gui (16-mua-hang.js)
#   2. dong ghi vet ghi ro "nang tu X len Y" (xem duyet_dong)
#   3. nhan rieng mau tim tren the dong, khong lan vao mau "Duyet du"
TU_CHOI = "tu_choi"
CAT_BOT = "cat_bot"
DUYET_DU = "duyet_du"
DUYET_THEM = "duyet_them"


def soat_so_duyet(sl, xin, da_dat, ly_do, ten):
	"""Soat mot dong duyet. THUAN: khong doc co so du lieu, khong cham Frappe.

	Tra ve (danh_sach_loi, loai). Loi rong nghia la duyet duoc.

	Tach ra khoi `duyet_dong` de con kiem thu duoc ma khong can site. Truoc
	24/08/2026 ca luong duyet nay KHONG co lay mot ca kiem nao, nen moi lan
	sua luat la mot lan doan mo.
	"""
	sl, xin, da_dat = flt(sl), flt(xin), flt(da_dat)
	ly_do = str(ly_do or "").strip()
	loi = []

	if sl < -EPS:
		loi.append("Số lượng duyệt không được âm (%s)." % ten)
	if sl <= EPS and not ly_do:
		loi.append(
			"%s: từ chối thì phải ghi lý do, để nhân viên đặt hàng biết vì "
			"sao mà lần sau không đặt lại." % ten
		)
	# Da len don mua roi thi khong cho cat xuong duoi so da dat: hang da
	# tren duong ve, cat so tren giay khong lam hang quay dau lai.
	if sl < da_dat - EPS:
		loi.append(
			"%s: đã lên đơn mua %s rồi nên không duyệt xuống %s được. Muốn "
			"dừng thì huỷ hoặc đóng đơn mua trước." % (ten, _so(da_dat), _so(sl))
		)

	if sl <= EPS:
		loai = TU_CHOI
	elif sl < xin - EPS:
		loai = CAT_BOT
	elif sl > xin + EPS:
		loai = DUYET_THEM
	else:
		loai = DUYET_DU
	return loi, loai



# --------------------------------------------------------- ba con so nen


def boi_canh_hang(ma_hang, bo_qua_phieu=None, kho=None):
	"""Ba con so giup thu mua quyet dinh, quy ve DON VI KHO cua tung mat hang.

	Tra ve {ma_hang: {ton, ton_tat_ca, cho_ve, so_don_cho_ve, hen_gan_nhat,
	                  cho_duyet, so_phieu_cho_duyet}}

	`kho` la kho ma phieu yeu cau se nhan hang, thuong la "Kho tong 307 - TV".
	Truyen vao thi `ton` chi dem Bin cua dung kho do, con `ton_tat_ca` van la
	tong moi kho. Uyen can con so cua kho tong de quyet dinh, chu tong ca bep
	Pastry, Baker, Lab thi khong noi len dieu gi - hang o bep khong keo nguoc
	ve kho tong duoc.

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
			"ton_tat_ca": 0.0,
			"cho_ve": 0.0,
			"so_don_cho_ve": 0,
			"hen_gan_nhat": "",
			"cho_duyet": 0.0,
			"so_phieu_cho_duyet": 0,
		}
		for m in ds
	}

	# 1. TON KHO. Bin giu san so luong theo don vi kho nen chi phai cong.
	#    Dem hai con so: rieng kho nhan hang (thuong la Kho tong 307) va tong
	#    moi kho. Man duyet in con so cua kho nhan hang, vi do moi la so Uyen
	#    dung de quyet dinh co mua nua hay khong.
	for r in frappe.db.sql(
		"""select item_code, sum(actual_qty) as sl
		from `tabBin` where item_code in %(ds)s group by item_code""",
		{"ds": ds},
		as_dict=True,
	):
		ra[r["item_code"]]["ton_tat_ca"] = flt(r["sl"])

	kho = str(kho or "").strip()
	if kho:
		for r in frappe.db.sql(
			"""select item_code, sum(actual_qty) as sl
			from `tabBin`
			where item_code in %(ds)s and warehouse = %(kho)s
			group by item_code""",
			{"ds": ds, "kho": kho},
			as_dict=True,
		):
			ra[r["item_code"]]["ton"] = flt(r["sl"])
	else:
		for m in ds:
			ra[m]["ton"] = ra[m]["ton_tat_ca"]

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
			sum((""" + SQL_SO_HIEU_LUC + """ - mri.ordered_qty)
				* mri.conversion_factor) as sl,
			count(distinct mri.parent) as so_phieu
		from `tabMaterial Request Item` mri
		join `tabMaterial Request` mr on mr.name = mri.parent
		where mri.item_code in %(ds)s
			and mri.docstatus = 1
			and mr.material_request_type = %(loai)s
			and mr.status not in ('Stopped', 'Cancelled')
			and """ + SQL_SO_HIEU_LUC + """ - mri.ordered_qty > %(eps)s"""
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
		y.append("Kho tổng còn %s, đủ cho yêu cầu này" % _so(x["ton"]))
	elif x["ton"] > EPS:
		y.append("Kho tổng còn %s" % _so(x["ton"]))
	khac = flt(x.get("ton_tat_ca")) - flt(x["ton"])
	if khac > EPS:
		y.append("Các kho bếp còn thêm %s" % _so(khac))
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


def _da_duyet(r):
	"""Dong nay da co nguoi duyet chua.

	Doc `nguoi_duyet_dong` chu KHONG doc `sl_duyet`: xem phan dau tep.
	Nhan duoc ca Document lan dict nen dung chung cho moi cho.
	"""
	lay = r.get if hasattr(r, "get") else (lambda k, d=None: r[k] if k in r else d)
	return bool(str(lay("nguoi_duyet_dong") or "").strip())


# Bieu thuc SQL dung chung cho hai cho phai dem "chua duyet" trong mot cau.
SQL_CHUA_DUYET = "ifnull(mri.nguoi_duyet_dong, '') = ''"
# So thuc su se duoc dat mua: chua duyet thi tam lay so nhan vien xin.
SQL_SO_HIEU_LUC = (
	"case when ifnull(mri.nguoi_duyet_dong, '') = '' "
	"then mri.qty else ifnull(mri.sl_duyet, 0) end"
)


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
		"""select mri.parent as parent,
			count(*) as tong,
			sum(case when """ + SQL_CHUA_DUYET + """ then 1 else 0 end) as cho,
			sum(case when not (""" + SQL_CHUA_DUYET + """)
				and ifnull(mri.sl_duyet, 0) <= %(eps)s
				then 1 else 0 end) as tu_choi
		from `tabMaterial Request Item` mri
		where mri.parent in %(ds)s and mri.docstatus = 1
		group by mri.parent""",
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

	kho_nhan = d.get("set_warehouse") or ""
	if not kho_nhan:
		# Phieu khong dat kho chung thi lay kho cua dong dau tien co ghi.
		for r in d.items:
			if r.get("warehouse"):
				kho_nhan = r.warehouse
				break
	bc = boi_canh_hang(
		[r.item_code for r in d.items], bo_qua_phieu=name, kho=kho_nhan
	)
	mon = []
	for r in d.items:
		he_so = flt(r.conversion_factor) or 1.0
		# Quy ba con so ve DUNG DON VI cua dong yeu cau. Uyen so sanh "xin 20
		# kg, kho con 12 kg" chu khong so sanh hai don vi khac nhau.
		g = bc.get(r.item_code) or {}
		x = {
			"ton": flt(g.get("ton")) / he_so,
			"ton_tat_ca": flt(g.get("ton_tat_ca")) / he_so,
			"cho_ve": flt(g.get("cho_ve")) / he_so,
			"so_don_cho_ve": cint(g.get("so_don_cho_ve")),
			"hen_gan_nhat": g.get("hen_gan_nhat") or "",
			"cho_duyet": flt(g.get("cho_duyet")) / he_so,
			"so_phieu_cho_duyet": cint(g.get("so_phieu_cho_duyet")),
		}
		xin = flt(r.qty)
		# Chua co ten nguoi duyet nghia la chua ai dung toi, tra ve None de
		# app hien o trong. KHONG dua vao sl_duyet: xem phan dau tep.
		duyet = r.get("sl_duyet") if _da_duyet(r) else None
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
				"ton_tat_ca": x["ton_tat_ca"],
				"kho_ton": kho_nhan,
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
		"kho_nhan": kho_nhan,
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
			frappe.throw("Dữ liệu gửi lên không đọc được, vui lòng thoát ra mở lại phiếu.")
	if not dong:
		frappe.throw("Chưa có dòng nào để duyệt.")

	d = frappe.get_doc("Material Request", name)
	if d.material_request_type != LOAI:
		frappe.throw("Phiếu %s không phải yêu cầu mua hàng." % name)
	if d.docstatus != 1:
		frappe.throw("Phiếu %s chưa gửi duyệt nên chưa duyệt dòng được." % name)

	theo_ten = {r.name: r for r in d.items}
	dem = {DUYET_DU: 0, CAT_BOT: 0, TU_CHOI: 0, DUYET_THEM: 0}
	vet = []
	for x in dong:
		khoa = str((x or {}).get("dong") or "").strip()
		r = theo_ten.get(khoa)
		if not r:
			frappe.throw(
				"Có dòng không thuộc phiếu %s. Vui lòng thoát ra mở lại phiếu rồi duyệt lại." % name
			)
		sl = flt((x or {}).get("sl_duyet"))
		ly = str((x or {}).get("ly_do_duyet") or "").strip()

		ten_mon = r.item_name or r.item_code
		loi, loai = soat_so_duyet(sl, r.qty, r.ordered_qty, ly, ten_mon)
		if loi:
			frappe.throw("<br>".join(loi))

		r.sl_duyet = sl
		r.ly_do_duyet = ly
		r.nguoi_duyet_dong = frappe.session.user
		r.duyet_luc = now_datetime()
		dem[loai] += 1
		if loai == TU_CHOI:
			r.trang_thai_cung_ung = TT_TU_CHOI
			vet.append("từ chối %s (%s)" % (ten_mon, ly))
		elif loai == CAT_BOT:
			vet.append(
				"cắt %s từ %s xuống %s%s"
				% (ten_mon, _so(r.qty), _so(sl), (" (%s)" % ly) if ly else "")
			)
		elif loai == DUYET_THEM:
			# Ghi vet BAT BUOC cho truong hop nang so: day la lan duy nhat
			# con lan ra ai nang, nang bao nhieu. Ban Version cua Frappe chi
			# ghi so cu so moi, khong ghi so nhan vien xin.
			vet.append(
				"nâng %s từ %s lên %s%s"
				% (ten_mon, _so(r.qty), _so(sl), (" (%s)" % ly) if ly else "")
			)

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
def duyet_het(name):
	"""Duyet du moi dong CHUA AI DUNG TOI trong phieu.

	Vi sao co nut nay (anh Viet chot 17/08/2026): luat la bat buoc duyet
	tung dong, nhung mot phieu hai muoi lam dong thi Uyen bam hai muoi lam
	lan cho nhung dong khong co gi de ban. Cach lam dung: Uyen xu ly truoc
	may dong co van de - cat bot hoac tu choi kem ly do - roi bam nut nay
	de nhung dong con lai duoc duyet du mot luot.

	Nut nay KHONG dung toi dong da co nguoi duyet. Dong da tu choi van la
	tu choi, dong da cat bot van giu so da cat. Nho vay bam nham cung khong
	xoa mat quyet dinh nao da ghi.

	Cung khong dung toi `qty`: so nhan vien xin nam nguyen, dung rang buoc
	goc cua anh Viet.
	"""
	_kiem_quyen()
	d = frappe.get_doc("Material Request", name)
	if d.material_request_type != LOAI:
		frappe.throw("Phiếu %s không phải yêu cầu mua hàng." % name)
	if d.docstatus != 1:
		frappe.throw("Phiếu %s chưa gửi duyệt nên chưa duyệt dòng được." % name)

	nguoi = frappe.session.user
	luc = now_datetime()
	dem = 0
	ten = []
	for r in d.items:
		if _da_duyet(r):
			continue
		r.sl_duyet = flt(r.qty)
		r.ly_do_duyet = None
		r.nguoi_duyet_dong = nguoi
		r.duyet_luc = luc
		dem += 1
		if len(ten) < 12:
			ten.append(r.item_name or r.item_code)

	if not dem:
		return {"da_duyet": 0, "name": name}

	d.flags.ignore_permissions = True
	d.save()
	_ghi_vet(
		name,
		"Duyệt tất cả các món còn lại: %d dòng duyệt đủ (%s%s)."
		% (dem, ", ".join(ten), "..." if dem > len(ten) else ""),
	)
	frappe.db.commit()
	return {"da_duyet": dem, "name": name}


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
	cu = r.get("sl_duyet") if _da_duyet(r) else None
	# Dau hieu "chua duyet" nam o nguoi_duyet_dong. sl_duyet dat lai 0 chi
	# cho gon mat, mot minh no khong con y nghia gi.
	r.sl_duyet = 0
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
			fields=[
				"name", "item_name", "item_code", "qty",
				"sl_duyet", "ly_do_duyet", "nguoi_duyet_dong",
			],
			limit_page_length=0,
		)
	}
	loi = []
	for r in doc.get("items") or []:
		m = duyet.get(r.get("material_request_item"))
		if not m:
			continue
		ten = m.get("item_name") or m.get("item_code")
		# Luat A (anh Viet chot 17/08/2026): chua co ten nguoi duyet thi
		# khong len don duoc. Bao dung chu "chua duyet", dung bao "tu choi".
		if not _da_duyet(m):
			loi.append(
				"%s chưa được thu mua duyệt. Mở màn Duyệt yêu cầu mua, "
				"bấm Duyệt đủ hoặc Duyệt tất cả các món còn lại rồi quay "
				"lại tách đơn." % ten
			)
			continue
		cho = flt(m["sl_duyet"])
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
