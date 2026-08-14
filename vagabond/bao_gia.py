"""Phan he bao gia khach doanh nghiep, nam trong Quan ly hop dong mua ban.

Anh Viet 14/08/2026: *"Dang vao mua trung thu, cần báo giá cho khách doanh
nghiệp rất nhiều... thiết kế phân hệ này để tự động ra được file pdf báo giá
cho khách hàng theo đúng chuẩn branding của The Vagabond, các trường thông
tin, chip cần thiết để điền vào, sản phẩm cần báo giá thì chọn được từ danh
mục... làm sao để thuận tiện nhất cho công việc của Loan Anh."*

Ba thu lam cho man nay nhanh:
  1. Chon mon tu danh muc - gia ban tu dong dien tu bang gia ban mac dinh,
	 Loan Anh chi go so luong.
  2. Chip dieu khoan - dat coc, cong no, thoi gian giao, VAT deu la nut bam
	 mot cai an luon, khong phai go tay tung to bao gia.
  3. Bao gia chot duoc thi bam mot nut ra thang Hop dong ban hang, khong
	 phai nhap lai khach hang va gia tri.
"""

import base64
import json

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from vagabond.cong_no import (
	TEN_NGAN_HANG_DAY_DU,
	_chu_so_tien,
	_ngay_vn,
	_qr_data_uri,
	_tien_vn,
)

DT = "Bao Gia Ban Hang"

# Sales lam bao gia, thu mua va ke toan xem duoc. Anh Viet 14/08/2026:
# *"cấp quyền truy cập cho Loan Anh, thu mua và kế toán"*. Loan Anh dang co
# vai Sales User nen vao duoc ngay khong phai cap them gi.
QUYEN_XEM = {
	"System Manager",
	"Sales User",
	"Sales Manager",
	"Accounts User",
	"Accounts Manager",
	"Purchase User",
	"Purchase Manager",
	"Bộ phận đặt hàng",
}
# Sua va gui bao gia thi chi ben ban hang va ke toan. Thu mua chi xem, vi to
# bao gia la cam ket gia BAN ra ngoai, khong phai viec cua thu mua.
QUYEN_SUA = {
	"System Manager",
	"Sales User",
	"Sales Manager",
	"Accounts User",
	"Accounts Manager",
}

TRANG_THAI = [
	"Nháp",
	"Đã gửi khách",
	"Khách duyệt",
	"Khách từ chối",
	"Hết hiệu lực",
	"Đã lên hợp đồng",
]

# Chip bam mot cai an luon. Loan Anh khong phai go lai cau chu moi to.
CHIP_THANH_TOAN = [
	"Đặt cọc 50% khi ký, thanh toán phần còn lại trước ngày giao",
	"Đặt cọc 30% khi ký, thanh toán phần còn lại trước ngày giao",
	"Thanh toán 100% trước ngày giao hàng",
	"Công nợ 15 ngày kể từ ngày giao hàng",
	"Công nợ 30 ngày kể từ ngày giao hàng",
	"Thanh toán ngay khi nhận hàng",
]
CHIP_GIAO_HANG = [
	"Đặt trước tối thiểu 3 ngày, giao trong ngày hẹn",
	"Đặt trước tối thiểu 7 ngày, giao trong ngày hẹn",
	"Giao trong nội thành TP.HCM, miễn phí đơn từ 3.000.000 đ",
	"Khách nhận hàng tại cửa hàng 9 Trần Cao Vân, Phường Sài Gòn",
	"Giao theo lịch thoả thuận từng đợt",
]
CHIP_DONG_GOI = [
	"Hộp quà trung thu The Vagabond, kèm túi giấy thương hiệu",
	"Đóng gói tiêu chuẩn, kèm túi giấy thương hiệu",
	"In logo doanh nghiệp lên thiệp kèm hộp (phụ thu theo số lượng)",
	"Thiết kế hộp riêng theo yêu cầu (báo giá riêng)",
]
CHIP_HIEU_LUC = [7, 15, 30, 45]
CHIP_VAT = [0, 8, 10]

LOI_MO_MAC_DINH = (
	"The Vagabond Pâtisserie trân trọng cảm ơn Quý khách đã quan tâm đến sản "
	"phẩm của chúng tôi. Chúng tôi xin gửi Quý khách bảng báo giá với các nội "
	"dung chi tiết như sau."
)


# ------------------------------------------------------------------- quyen


def _quyen(sua=False):
	vai = set(frappe.get_roles())
	if sua:
		if not QUYEN_SUA & vai:
			frappe.throw("Chỉ bộ phận kinh doanh và kế toán được lập hoặc sửa báo giá.")
		return
	if not QUYEN_XEM & vai:
		frappe.throw("Không có quyền xem báo giá.")


def _bang_gia_ban():
	return (
		frappe.db.get_single_value("Selling Settings", "selling_price_list")
		or "Standard Selling"
	)


# ------------------------------------------------------------------- doc so


def _tinh(doc):
	"""Cong lai toan bo con so tren to bao gia.

	Tinh o may chu chu khong tin so app gui len: app co the cu, co the nguoi
	dung sua tay trong lúc mat song, ma to bao gia sai tien la mat mat that.
	"""
	tam = 0.0
	for d in doc.get("dong") or []:
		d.so_luong = flt(d.so_luong)
		d.don_gia = flt(d.don_gia)
		d.chiet_khau = flt(d.chiet_khau)
		goc = d.so_luong * d.don_gia
		d.thanh_tien = round(goc * (1 - d.chiet_khau / 100.0), 0)
		tam += d.thanh_tien
	doc.tam_tinh = tam
	doc.chiet_khau_tien = round(tam * flt(doc.chiet_khau_pt) / 100.0, 0)
	sau_ck = tam - doc.chiet_khau_tien
	doc.thue_tien = round(sau_ck * flt(doc.thue_pt) / 100.0, 0)
	doc.tong_cong = sau_ck + doc.thue_tien + flt(doc.phi_giao)
	doc.dat_coc_tien = round(doc.tong_cong * flt(doc.dat_coc_pt) / 100.0, 0)
	return doc


def _goi(doc):
	return {
		"name": doc.name,
		"ten": doc.ten or "",
		"trang_thai": doc.trang_thai or "Nháp",
		"khach_hang": doc.khach_hang or "",
		"ten_khach": doc.ten_khach or "",
		"ma_so_thue": doc.ma_so_thue or "",
		"dia_chi": doc.dia_chi or "",
		"nguoi_lien_he": doc.nguoi_lien_he or "",
		"chuc_vu": doc.chuc_vu or "",
		"dien_thoai": doc.dien_thoai or "",
		"email": doc.email or "",
		"ngay_bao_gia": str(doc.ngay_bao_gia or ""),
		"hieu_luc_den": str(doc.hieu_luc_den or ""),
		"hop_dong": doc.hop_dong or "",
		"loi_mo": doc.loi_mo or "",
		"thanh_toan": doc.thanh_toan or "",
		"giao_hang": doc.giao_hang or "",
		"dong_goi": doc.dong_goi or "",
		"ghi_chu": doc.ghi_chu or "",
		"ghi_chu_noi_bo": doc.ghi_chu_noi_bo or "",
		"chiet_khau_pt": flt(doc.chiet_khau_pt),
		"chiet_khau_tien": flt(doc.chiet_khau_tien),
		"thue_pt": flt(doc.thue_pt),
		"thue_tien": flt(doc.thue_tien),
		"phi_giao": flt(doc.phi_giao),
		"dat_coc_pt": flt(doc.dat_coc_pt),
		"dat_coc_tien": flt(doc.dat_coc_tien),
		"tam_tinh": flt(doc.tam_tinh),
		"tong_cong": flt(doc.tong_cong),
		"nguoi_lap": doc.nguoi_lap or "",
		"ten_nguoi_lap": frappe.db.get_value("User", doc.nguoi_lap, "full_name")
		if doc.nguoi_lap
		else "",
		"dt_nguoi_lap": doc.dt_nguoi_lap or "",
		"dong": [
			{
				"ma_mon": d.ma_mon or "",
				"ten_mon": d.ten_mon or "",
				"mo_ta": d.mo_ta or "",
				"dvt": d.dvt or "",
				"so_luong": flt(d.so_luong),
				"don_gia": flt(d.don_gia),
				"chiet_khau": flt(d.chiet_khau),
				"thanh_tien": flt(d.thanh_tien),
			}
			for d in (doc.get("dong") or [])
		],
	}


# ------------------------------------------------------------------ doc api


@frappe.whitelist()
def cai_dat():
	"""Chip va danh sach co dinh, app tai mot lan roi dung lai."""
	_quyen()
	return {
		"trang_thai": TRANG_THAI,
		"chip_thanh_toan": CHIP_THANH_TOAN,
		"chip_giao_hang": CHIP_GIAO_HANG,
		"chip_dong_goi": CHIP_DONG_GOI,
		"chip_hieu_luc": CHIP_HIEU_LUC,
		"chip_vat": CHIP_VAT,
		"loi_mo": LOI_MO_MAC_DINH,
		"duoc_sua": bool(QUYEN_SUA & set(frappe.get_roles())),
	}


@frappe.whitelist()
def danh_sach(trang_thai=None, tim=None):
	_quyen()
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tim:
		loc["ten"] = ["like", "%%%s%%" % tim]
	ds = frappe.get_all(
		DT,
		filters=loc,
		fields=[
			"name",
			"ten",
			"trang_thai",
			"khach_hang",
			"ten_khach",
			"ngay_bao_gia",
			"hieu_luc_den",
			"tong_cong",
			"hop_dong",
		],
		order_by="modified desc",
		limit_page_length=200,
	)
	hn = getdate(nowdate())
	for r in ds:
		r["het_han"] = bool(
			r.get("hieu_luc_den")
			and getdate(r["hieu_luc_den"]) < hn
			and r.get("trang_thai") in ("Nháp", "Đã gửi khách")
		)
	return ds


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	return _goi(frappe.get_doc(DT, name))


@frappe.whitelist()
def moi():
	"""Khung to bao gia trong, dien san nhung gi doan duoc."""
	_quyen(sua=True)
	nd = frappe.session.user
	return {
		"name": "",
		"ten": "",
		"trang_thai": "Nháp",
		"khach_hang": "",
		"ten_khach": "",
		"ma_so_thue": "",
		"dia_chi": "",
		"nguoi_lien_he": "",
		"chuc_vu": "",
		"dien_thoai": "",
		"email": "",
		"ngay_bao_gia": nowdate(),
		"hieu_luc_den": add_days(nowdate(), 15),
		"hop_dong": "",
		"loi_mo": LOI_MO_MAC_DINH,
		"thanh_toan": CHIP_THANH_TOAN[0],
		"giao_hang": CHIP_GIAO_HANG[0],
		"dong_goi": "",
		"ghi_chu": "",
		"ghi_chu_noi_bo": "",
		"chiet_khau_pt": 0,
		"chiet_khau_tien": 0,
		"thue_pt": 8,
		"thue_tien": 0,
		"phi_giao": 0,
		"dat_coc_pt": 50,
		"dat_coc_tien": 0,
		"tam_tinh": 0,
		"tong_cong": 0,
		"nguoi_lap": nd,
		"ten_nguoi_lap": frappe.db.get_value("User", nd, "full_name") or "",
		"dt_nguoi_lap": frappe.db.get_value("User", nd, "mobile_no") or "",
		"dong": [],
	}


@frappe.whitelist()
def luu(du_lieu):
	"""Tao moi hoac ghi de mot to bao gia. App gui nguyen cuc JSON len."""
	_quyen(sua=True)
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	if not (d.get("ten") or "").strip():
		frappe.throw("Nhập tiêu đề báo giá đã nhé.")
	if not (d.get("ten_khach") or d.get("khach_hang")):
		frappe.throw("Chọn khách hàng hoặc nhập tên công ty khách.")

	name = d.get("name") or ""
	if name:
		doc = frappe.get_doc(DT, name)
		if doc.trang_thai == "Đã lên hợp đồng":
			frappe.throw(
				"Báo giá này đã lên hợp đồng %s nên không sửa được nữa. "
				"Nếu cần đổi giá thì lập báo giá mới." % (doc.hop_dong or "")
			)
		doc.set("dong", [])
	else:
		doc = frappe.new_doc(DT)
		doc.nguoi_lap = frappe.session.user

	for f in (
		"ten",
		"khach_hang",
		"ten_khach",
		"ma_so_thue",
		"dia_chi",
		"nguoi_lien_he",
		"chuc_vu",
		"dien_thoai",
		"email",
		"loi_mo",
		"thanh_toan",
		"giao_hang",
		"dong_goi",
		"ghi_chu",
		"ghi_chu_noi_bo",
		"dt_nguoi_lap",
	):
		doc.set(f, d.get(f) or None)
	for f in ("ngay_bao_gia", "hieu_luc_den"):
		doc.set(f, d.get(f) or None)
	for f in ("chiet_khau_pt", "thue_pt", "phi_giao", "dat_coc_pt"):
		doc.set(f, flt(d.get(f)))
	if d.get("trang_thai") in TRANG_THAI:
		doc.trang_thai = d["trang_thai"]

	for x in d.get("dong") or []:
		if not (x.get("ten_mon") or x.get("ma_mon")):
			continue
		doc.append(
			"dong",
			{
				"ma_mon": x.get("ma_mon") or None,
				"ten_mon": x.get("ten_mon") or x.get("ma_mon"),
				"mo_ta": x.get("mo_ta") or None,
				"dvt": x.get("dvt") or None,
				"so_luong": flt(x.get("so_luong")),
				"don_gia": flt(x.get("don_gia")),
				"chiet_khau": flt(x.get("chiet_khau")),
			},
		)
	if not doc.get("dong"):
		frappe.throw("Báo giá phải có ít nhất một dòng sản phẩm.")

	_tinh(doc)
	doc.save(ignore_permissions=True)
	return _goi(doc)


@frappe.whitelist()
def doi_trang_thai(name, trang_thai):
	_quyen(sua=True)
	if trang_thai not in TRANG_THAI:
		frappe.throw("Trạng thái không hợp lệ.")
	frappe.db.set_value(DT, name, "trang_thai", trang_thai)
	return trang_thai


@frappe.whitelist()
def xoa(name):
	"""Chi xoa duoc to con o Nhap. To da gui khach thi chuyen trang thai
	Khach tu choi cho con dau vet, khong xoa mat."""
	_quyen(sua=True)
	tt = frappe.db.get_value(DT, name, "trang_thai")
	if tt != "Nháp":
		frappe.throw(
			"Báo giá đã ở trạng thái %s nên không xoá được. "
			"Chuyển sang Khách từ chối để lưu lại dấu vết." % tt
		)
	frappe.delete_doc(DT, name, ignore_permissions=True)
	return 1


@frappe.whitelist()
def nhan_ban(name):
	"""Nhan ban mot to bao gia. Mua trung thu Loan Anh gui gan giong nhau
	cho hang chuc cong ty, chi khac ten khach va so luong."""
	_quyen(sua=True)
	cu = frappe.get_doc(DT, name)
	moi_ = frappe.copy_doc(cu)
	moi_.trang_thai = "Nháp"
	moi_.hop_dong = None
	moi_.ngay_bao_gia = nowdate()
	moi_.hieu_luc_den = add_days(nowdate(), 15)
	moi_.nguoi_lap = frappe.session.user
	moi_.insert(ignore_permissions=True)
	return moi_.name


# ------------------------------------------------------------ chon san pham


@frappe.whitelist()
def nhom_mon():
	"""Cac nhom hang co the ban ra, kem so mon trong nhom."""
	_quyen()
	ds = frappe.db.sql(
		"""select i.item_group as nhom, count(*) as so
		from `tabItem` i
		where i.disabled = 0 and i.is_sales_item = 1
		group by i.item_group order by i.item_group""",
		as_dict=True,
	)
	return [x for x in ds if x["so"]]


@frappe.whitelist()
def mon_theo_nhom(nhom=None, tim=None, so_dong=200):
	"""Danh sach mon de chon vao bao gia, kem gia ban dang niem yet."""
	_quyen()
	dk = ["i.disabled = 0", "i.is_sales_item = 1"]
	tham = {}
	if nhom:
		dk.append("i.item_group = %(nhom)s")
		tham["nhom"] = nhom
	if tim:
		dk.append("(i.item_name like %(tim)s or i.name like %(tim)s)")
		tham["tim"] = "%%%s%%" % tim
	ds = frappe.db.sql(
		"""select i.name as ma_mon, i.item_name as ten_mon, i.stock_uom as dvt,
			i.item_group as nhom, i.description as mo_ta
		from `tabItem` i where %s
		order by i.item_name limit %d"""
		% (" and ".join(dk), int(so_dong or 200)),
		tham,
		as_dict=True,
	)
	if not ds:
		return []
	gia = {}
	for g in frappe.get_all(
		"Item Price",
		filters={
			"item_code": ["in", [x["ma_mon"] for x in ds]],
			"price_list": _bang_gia_ban(),
			"selling": 1,
		},
		fields=["item_code", "price_list_rate", "uom"],
		order_by="modified desc",
	):
		gia.setdefault(g["item_code"], g)
	for x in ds:
		g = gia.get(x["ma_mon"]) or {}
		x["don_gia"] = flt(g.get("price_list_rate"))
		if g.get("uom"):
			x["dvt"] = g["uom"]
		# Mo ta danh muc hay la mot cuc HTML dai, cat cho gon de app hien.
		mt = frappe.utils.strip_html(x.get("mo_ta") or "").strip()
		x["mo_ta"] = mt[:180]
	return ds


@frappe.whitelist()
def tim_khach(tim=None, so_dong=60):
	"""Chon khach co san, dien luon MST va dia chi de khoi go tay."""
	_quyen()
	loc = {"disabled": 0}
	if tim:
		loc["customer_name"] = ["like", "%%%s%%" % tim]
	return frappe.get_all(
		"Customer",
		filters=loc,
		fields=["name", "customer_name", "tax_id", "mobile_no", "customer_group"],
		order_by="customer_name",
		limit_page_length=int(so_dong or 60),
	)


@frappe.whitelist()
def thong_tin_khach(khach):
	"""MST, dia chi, nguoi lien he cua mot khach da co."""
	_quyen()
	kh = frappe.db.get_value(
		"Customer", khach, ["customer_name", "tax_id", "mobile_no"], as_dict=True
	) or {}
	dc = frappe.db.sql(
		"""select a.address_line1, a.address_line2, a.city, a.state
		from `tabAddress` a join `tabDynamic Link` l on l.parent = a.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by a.is_primary_address desc limit 1""",
		khach,
		as_dict=True,
	)
	dia_chi = ""
	if dc:
		dia_chi = ", ".join(
			[x for x in [dc[0].address_line1, dc[0].address_line2, dc[0].city, dc[0].state] if x]
		)
	lh = frappe.db.sql(
		"""select c.first_name, c.last_name, c.mobile_no, c.email_id, c.designation
		from `tabContact` c join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by c.is_primary_contact desc limit 1""",
		khach,
		as_dict=True,
	)
	ten_lh = dt = em = cv = ""
	if lh:
		ten_lh = (" ".join([x for x in [lh[0].first_name, lh[0].last_name] if x])).strip()
		dt = lh[0].mobile_no or ""
		em = lh[0].email_id or ""
		cv = lh[0].designation or ""
	return {
		"ten_khach": kh.get("customer_name") or khach,
		"ma_so_thue": kh.get("tax_id") or "",
		"dia_chi": dia_chi,
		"nguoi_lien_he": ten_lh,
		"chuc_vu": cv,
		"dien_thoai": dt or kh.get("mobile_no") or "",
		"email": em,
	}


# ------------------------------------------------------------------- to in


def _html(name):
	"""To bao gia gui khach, cung khuon ban in voi Don mua hang va Phieu de
	nghi thanh toan de ba to nhin ra mot nha."""
	d = chi_tiet(name)
	esc = frappe.utils.escape_html

	PHONG = "'DejaVu Sans','Liberation Sans',Arial,Helvetica,sans-serif"
	VIEN = "1px solid #c9c4bd"
	o_th = (
		'style="border:%s;padding:6px 7px;background:#f3f0ec;font-size:10.5px;'
		'font-weight:bold;text-align:center"' % VIEN
	)

	def _td(noi, canh="left", dam=False, khong_ngat=False):
		return (
			'<td style="border:%s;padding:5px 7px;font-size:10.5px;text-align:%s;%s%s">%s</td>'
			% (
				VIEN,
				canh,
				"font-weight:bold;" if dam else "",
				"white-space:nowrap;" if khong_ngat else "",
				noi,
			)
		)

	def _o_tt(nhan, gt, to=False):
		return (
			'<tr><td style="border:none;padding:3px 0;font-size:11px;color:#555;'
			'width:34%%;vertical-align:top">%s</td>'
			'<td style="border:none;padding:3px 0;font-size:%s;font-weight:bold;'
			'vertical-align:top">%s</td></tr>'
			% (nhan, "13.5px" if to else "11.5px", gt)
		)

	co_ck = any(flt(x["chiet_khau"]) for x in d["dong"])
	hang = []
	for i, x in enumerate(d["dong"], 1):
		ten = "<b>%s</b>" % esc(x["ten_mon"] or x["ma_mon"])
		if x.get("mo_ta"):
			ten += (
				'<div style="font-size:9.5px;color:#666;margin-top:2px">%s</div>'
				% esc(x["mo_ta"])
			)
		o = (
			"<tr>"
			+ _td(str(i), "center")
			+ _td(ten)
			+ _td(esc(x["dvt"] or "-"), "center", khong_ngat=True)
			+ _td(_tien_vn(x["so_luong"]), "center", khong_ngat=True)
			+ _td(_tien_vn(x["don_gia"]), "right", khong_ngat=True)
		)
		if co_ck:
			o += _td(
				("%g%%" % flt(x["chiet_khau"])) if flt(x["chiet_khau"]) else "-",
				"center",
				khong_ngat=True,
			)
		o += _td(_tien_vn(x["thanh_tien"]), "right", dam=True, khong_ngat=True) + "</tr>"
		hang.append(o)

	so_cot = 7 if co_ck else 6
	tieu_de_cot = (
		"<tr><th %s style='width:34px'>STT</th><th %s>Sản phẩm</th>"
		"<th %s>ĐVT</th><th %s>Số lượng</th><th %s>Đơn giá</th>%s"
		"<th %s>Thành tiền</th></tr>"
		% (
			o_th,
			o_th,
			o_th,
			o_th,
			o_th,
			("<th %s>CK</th>" % o_th) if co_ck else "",
			o_th,
		)
	)

	def _dong_cong(nhan, tien, dam=False, mau=None):
		return (
			'<tr><td colspan="%d" style="border:%s;padding:6px 7px;font-size:%s;'
			'text-align:right;%s">%s</td>'
			'<td style="border:%s;padding:6px 7px;font-size:%s;text-align:right;'
			'white-space:nowrap;%s%s">%s</td></tr>'
			% (
				so_cot - 1,
				VIEN,
				"11.5px" if dam else "11px",
				"font-weight:bold;" if dam else "",
				nhan,
				VIEN,
				"12.5px" if dam else "11px",
				"font-weight:bold;" if dam else "",
				("color:%s;" % mau) if mau else "",
				_tien_vn(tien),
			)
		)

	cuoi = _dong_cong("Cộng tiền hàng", d["tam_tinh"])
	if flt(d["chiet_khau_tien"]):
		cuoi += _dong_cong(
			"Chiết khấu %g%%" % flt(d["chiet_khau_pt"]), -flt(d["chiet_khau_tien"])
		)
	if flt(d["phi_giao"]):
		cuoi += _dong_cong("Phí giao hàng", d["phi_giao"])
	cuoi += _dong_cong("Thuế GTGT %g%%" % flt(d["thue_pt"]), d["thue_tien"])
	cuoi += _dong_cong("TỔNG CỘNG THANH TOÁN", d["tong_cong"], dam=True)

	# Khoi thong tin khach
	ben_nhan = (
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt("Kính gửi:", esc(d["ten_khach"] or d["khach_hang"] or ""), to=True)
		+ (_o_tt("Mã số thuế:", esc(d["ma_so_thue"])) if d["ma_so_thue"] else "")
		+ (_o_tt("Địa chỉ:", esc(d["dia_chi"])) if d["dia_chi"] else "")
		+ (
			_o_tt(
				"Người liên hệ:",
				esc(d["nguoi_lien_he"])
				+ (" - %s" % esc(d["chuc_vu"]) if d["chuc_vu"] else "")
				+ (" - %s" % esc(d["dien_thoai"]) if d["dien_thoai"] else ""),
			)
			if d["nguoi_lien_he"]
			else ""
		)
		+ _o_tt(
			"Báo giá có hiệu lực đến:",
			_ngay_vn(d["hieu_luc_den"]) or "...............",
			to=True,
		)
		+ "</table>"
	)

	loi_mo = (
		'<div style="margin-top:12px;font-size:11.5px;line-height:1.6;'
		'text-align:justify">%s</div>' % esc(d["loi_mo"] or LOI_MO_MAC_DINH)
	)

	# Dieu khoan
	dk = []
	for nhan, gt in (
		("Điều kiện thanh toán", d["thanh_toan"]),
		("Thời gian và địa điểm giao hàng", d["giao_hang"]),
		("Quy cách đóng gói", d["dong_goi"]),
		("Ghi chú", d["ghi_chu"]),
	):
		if (gt or "").strip():
			dk.append(
				'<tr><td style="border:none;padding:3px 0;font-size:11px;color:#555;'
				'width:34%%;vertical-align:top">%s:</td>'
				'<td style="border:none;padding:3px 0;font-size:11px;'
				'vertical-align:top;white-space:pre-wrap">%s</td></tr>' % (nhan, esc(gt))
			)
	if flt(d["dat_coc_tien"]):
		dk.insert(
			0,
			'<tr><td style="border:none;padding:3px 0;font-size:11px;color:#555;'
			'width:34%%;vertical-align:top">Số tiền đặt cọc (%g%%):</td>'
			'<td style="border:none;padding:3px 0;font-size:12.5px;font-weight:bold;'
			"vertical-align:top\">%s đ</td></tr>"
			% (flt(d["dat_coc_pt"]), _tien_vn(d["dat_coc_tien"])),
		)
	khoi_dk = (
		'<div style="border:1px solid #c9c4bd;padding:10px 12px;margin-top:14px">'
		'<div style="font-size:11px;font-weight:bold;letter-spacing:.5px;'
		'margin-bottom:6px">ĐIỀU KHOẢN BÁO GIÁ</div>'
		'<table style="width:100%%;border:none;border-collapse:collapse">%s</table>'
		"</div>" % "".join(dk)
	) if dk else ""

	# Khoi chuyen khoan kem QR so tien dat coc (hoac tong neu khong dat coc)
	from vagabond import tai_khoan

	try:
		qr = tai_khoan.tk_phieu_no() or {}
	except Exception:
		qr = {}
	tien_qr = flt(d["dat_coc_tien"]) or flt(d["tong_cong"])
	noi_dung_qr = "%s %s" % (d["name"], (d["ten_khach"] or "")[:30])
	anh_qr = _qr_data_uri(qr, tien_qr, noi_dung_qr) if qr.get("stk") else ""
	o_qr = (
		'<td style="border:none;width:160px;text-align:center;vertical-align:top;'
		'padding-left:12px">'
		'<img src="%s" width="140" height="140" '
		'style="width:140px !important;height:140px !important">'
		'<div style="font-size:9px;color:#555;margin-top:3px">Quét mã để chuyển '
		"khoản %s</div></td>"
		% (anh_qr, "đặt cọc" if flt(d["dat_coc_tien"]) else "thanh toán")
	) if anh_qr else ""
	khoi_ck = (
		'<div style="border:2px solid #1c1a17;padding:11px 13px;margin-top:12px">'
		'<div style="font-size:11px;font-weight:bold;letter-spacing:.5px;'
		'margin-bottom:6px">THÔNG TIN CHUYỂN KHOẢN</div>'
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;vertical-align:top">'
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt(
			"Ngân hàng:",
			esc(TEN_NGAN_HANG_DAY_DU.get(qr.get("bank") or "", qr.get("bank") or "")),
		)
		+ _o_tt("Số tài khoản:", esc(qr.get("stk") or ""), to=True)
		+ _o_tt("Tên tài khoản:", esc(qr.get("ten") or ""))
		+ _o_tt("Số tiền:", _tien_vn(tien_qr) + " đ", to=True)
		+ _o_tt("Nội dung chuyển khoản:", esc(noi_dung_qr), to=True)
		+ "</table></td>"
		+ o_qr
		+ "</tr></table></div>"
	) if qr.get("stk") else ""

	return (
		'<div style="font-family:%s;color:#1c1a17;font-size:12px;line-height:1.45">'
		'<table style="width:100%%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:45%%;vertical-align:middle">'
		'<img src="/files/vagabond_logo_print.png" width="150" height="62" '
		'style="width:150px !important;height:62px !important;object-fit:contain">'
		"</td>"
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9.5px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10.5px;color:#1c1a17">CÔNG TY TNHH PATISSERIE VAGABOND</b><br>'
		"MST: 0318561568<br>"
		"9 Trần Cao Vân, Phường Sài Gòn, TP.HCM<br>"
		"www.thevagabondpatisserie.com"
		"</td></tr></table>"
		'<div style="text-align:center;margin:14px 0 2px">'
		'<div style="font-size:19px;font-weight:bold;letter-spacing:1px">BÁO GIÁ</div>'
		'<div style="font-size:12px;color:#555;margin-top:2px">%s</div>'
		'<div style="font-size:11px;color:#555;margin-top:3px">'
		"Số: <b>%s</b> &nbsp;·&nbsp; Ngày %s</div></div>"
		"%s%s"
		'<table style="width:100%%;border-collapse:collapse;margin-top:12px">'
		"%s%s%s</table>"
		'<div style="margin-top:8px;font-size:11px">Tổng cộng bằng chữ: '
		"<i>%s</i></div>"
		"%s%s"
		'<table style="width:100%%;border:none;border-collapse:collapse;margin-top:22px">'
		'<tr><td style="border:none;width:50%%;text-align:center;font-size:11px">'
		'<b>ĐẠI DIỆN BÊN MUA</b><div style="font-size:10px;color:#666;margin-top:2px">'
		'(Ký, ghi rõ họ tên)</div><div style="height:56px"></div></td>'
		'<td style="border:none;width:50%%;text-align:center;font-size:11px">'
		"<b>THE VAGABOND PÂTISSERIE</b>"
		'<div style="font-size:10px;color:#666;margin-top:2px">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:56px"></div>'
		'<div style="font-size:10.5px;font-weight:bold">%s</div>'
		'<div style="font-size:9.5px;color:#666">%s</div></td></tr></table>'
		'<div style="margin-top:12px;font-size:9.5px;color:#777;text-align:center">'
		"Báo giá được lập từ hệ thống The Vagabond Pâtisserie. "
		"Giá trên đã bao gồm chi phí sản xuất theo quy cách mô tả. "
		"Sau ngày hết hiệu lực, vui lòng liên hệ để nhận báo giá cập nhật."
		"</div></div>"
	) % (
		PHONG,
		esc(d["ten"] or ""),
		esc(d["name"]),
		_ngay_vn(d["ngay_bao_gia"]),
		ben_nhan,
		loi_mo,
		tieu_de_cot,
		"".join(hang),
		cuoi,
		_chu_so_tien(d["tong_cong"]),
		khoi_dk,
		khoi_ck,
		esc(d["ten_nguoi_lap"] or ""),
		esc(d["dt_nguoi_lap"] or ""),
	)


@frappe.whitelist()
def xem_truoc(name):
	_quyen()
	return {"html": _html(name)}


@frappe.whitelist()
def xuat_pdf(name):
	"""To bao gia ra PDF A4 doc de gui khach."""
	_quyen()
	from frappe.utils.pdf import get_pdf

	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:12mm 10mm}body{margin:0}</style></head><body>"
		+ _html(name)
		+ "</body></html>"
	)
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	ten_kh = frappe.db.get_value(DT, name, "ten_khach") or ""
	from vagabond.danh_muc import khong_dau

	goi = khong_dau(ten_kh).replace(" ", "-")[:40] if ten_kh else ""
	return {
		"ten_file": ("Bao-gia-%s%s.pdf" % (name, ("-" + goi) if goi else "")),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}


@frappe.whitelist()
def gui_email(name, email=None, loi_nhan=None):
	"""Gui to bao gia PDF sang email khach, dong thoi doi trang thai."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name)
	toi = (email or doc.email or "").strip()
	if not toi:
		frappe.throw("Chưa có email khách để gửi. Nhập email vào rồi gửi lại nhé.")

	tep = xuat_pdf(name)
	nguoi = frappe.db.get_value("User", doc.nguoi_lap, "full_name") or ""
	than = (
		'<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
		'line-height:1.6;color:#1c1a17">'
		"<p>Kính gửi Quý khách %s,</p>"
		"<p>The Vagabond Pâtisserie trân trọng gửi Quý khách bảng báo giá "
		"<b>%s</b> theo nội dung trao đổi. Chi tiết vui lòng xem tệp PDF đính kèm.</p>"
		"<p>Báo giá có hiệu lực đến hết ngày <b>%s</b>. Tổng giá trị báo giá là "
		"<b>%s đ</b>.</p>"
		"%s"
		"<p>Quý khách cần điều chỉnh số lượng hoặc quy cách, xin vui lòng phản hồi "
		"lại email này hoặc liên hệ trực tiếp với chúng tôi để được hỗ trợ.</p>"
		"<p>Trân trọng,<br><b>%s</b><br>The Vagabond Pâtisserie<br>"
		"9 Trần Cao Vân, Phường Sài Gòn, TP.HCM<br>"
		"www.thevagabondpatisserie.com</p></div>"
	) % (
		frappe.utils.escape_html(doc.ten_khach or ""),
		frappe.utils.escape_html(doc.ten or ""),
		_ngay_vn(doc.hieu_luc_den) or "...",
		_tien_vn(doc.tong_cong),
		(
			"<p>%s</p>" % frappe.utils.escape_html(loi_nhan)
			if (loi_nhan or "").strip()
			else ""
		),
		frappe.utils.escape_html(nguoi),
	)
	frappe.sendmail(
		recipients=[toi],
		subject="Báo giá %s - The Vagabond Pâtisserie" % doc.name,
		message=than,
		attachments=[
			{"fname": tep["ten_file"], "fcontent": base64.b64decode(tep["b64"])}
		],
		reference_doctype=DT,
		reference_name=doc.name,
		now=True,
	)
	if doc.trang_thai == "Nháp":
		frappe.db.set_value(DT, name, "trang_thai", "Đã gửi khách")
	if not doc.email:
		frappe.db.set_value(DT, name, "email", toi)
	return {"ok": 1, "toi": toi}


# ------------------------------------------------------- chot thanh hop dong


@frappe.whitelist()
def tao_hop_dong(name, so_hop_dong=None, ngay_ky=None, ngay_su_kien=None):
	"""Bao gia khach duyet thi bam mot nut ra Hop dong ban hang, mang theo
	khach hang, gia tri va toan bo noi dung cac dong - khong go lai."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name)
	if doc.hop_dong and frappe.db.exists("Hop Dong Ban Hang", doc.hop_dong):
		frappe.throw("Báo giá này đã lên hợp đồng %s rồi." % doc.hop_dong)
	if not doc.khach_hang:
		frappe.throw(
			"Hợp đồng phải gắn với một khách hàng có trong hệ thống. "
			"Mở báo giá, chọn lại khách ở ô Khách hàng rồi thử lại nhé."
		)

	noi_dung = "\n".join(
		"%d. %s - %s %s x %s đ = %s đ"
		% (
			i,
			x.ten_mon or x.ma_mon,
			_tien_vn(x.so_luong),
			x.dvt or "",
			_tien_vn(x.don_gia),
			_tien_vn(x.thanh_tien),
		)
		for i, x in enumerate(doc.dong, 1)
	)
	if doc.thanh_toan:
		noi_dung += "\nĐiều kiện thanh toán: %s" % doc.thanh_toan
	if doc.giao_hang:
		noi_dung += "\nGiao hàng: %s" % doc.giao_hang

	hd = frappe.get_doc(
		{
			"doctype": "Hop Dong Ban Hang",
			"ten": doc.ten,
			"so_hop_dong": so_hop_dong or None,
			"loai": "B2B sỉ",
			"khach_hang": doc.khach_hang,
			"ngay_ky": ngay_ky or nowdate(),
			"ngay_su_kien": ngay_su_kien or None,
			"gia_tri": flt(doc.tong_cong),
			"mo_ta": noi_dung,
			"ghi_chu": "Lập từ báo giá %s" % doc.name,
		}
	)
	hd.insert(ignore_permissions=True)
	frappe.db.set_value(
		DT, name, {"hop_dong": hd.name, "trang_thai": "Đã lên hợp đồng"}
	)
	return hd.name
