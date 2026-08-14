"""Phan he bao gia khach doanh nghiep, song ngu Viet - Anh.

Dung theo dung to Loan Anh dang gui khach (file VGB-PQ-2026-0011 anh Viet gui
ngay 14/08/2026): 9 muc, song ngu toan bo, menu co hinh mon va thong tin di
ung, bang bao gia tam tinh, dich vu them gia bang chu, timeline van hanh,
yeu cau van hanh, dieu khoan thanh toan, chinh sach huy, luu y, hai o ky.

Ba cho giu du lieu:
  - Bao Gia Thu Vien: mon thiet ke rieng va moi khoan phi (nhan cong, van
    chuyen, set up, gia cong khuon, thu banh), co hinh va song ngu, sua gia
    duoc. Anh Viet 14/08: *"phải lưu vào đâu để sau này thao tác nhanh"*.
  - Bao Gia Cai Dat: cau chu khung to, khai mot lan dung cho moi to.
  - vagabond.chon_mon: bang chon mon dung chung, luon kem hinh anh.
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
DT_TV = "Bao Gia Thu Vien"
DT_CD = "Bao Gia Cai Dat"

QUYEN_XEM = {
	"System Manager", "Sales User", "Sales Manager", "Accounts User",
	"Accounts Manager", "Purchase User", "Purchase Manager", "Bộ phận đặt hàng",
}
QUYEN_SUA = {
	"System Manager", "Sales User", "Sales Manager", "Accounts User",
	"Accounts Manager",
}

TRANG_THAI = [
	"Nháp", "Đã gửi khách", "Khách duyệt", "Khách từ chối",
	"Hết hiệu lực", "Đã lên hợp đồng",
]

CHIP_HIEU_LUC = [7, 15, 30, 45]
CHIP_VAT = [0, 8, 10]

# Cau chu mac dinh, dung khi Bao Gia Cai Dat chua duoc khai.
MAC_DINH = {
	"loi_mo_vi": (
		"Từ năm 2015, The Vagabond Pâtisserie làm bánh thủ công với nguyên liệu "
		"cao cấp, trong đó có bơ AOP Échiré vùng Charentes-Poitou, Pháp. Mọi món "
		"trong thực đơn catering đều giữ đúng tiêu chuẩn và sự tỉ mỉ đó."
	),
	"loi_mo_en": (
		"Since 2015, The Vagabond Pâtisserie has been crafting artisan pastries "
		"with premium ingredients, including AOP Échiré butter from "
		"Charentes-Poitou, France. Every item in our catering menu reflects the "
		"same dedication to quality and craftsmanship that defines our patisserie."
	),
	"thanh_toan_vi": (
		"Đặt cọc 50% khi ký xác nhận báo giá.\n"
		"Thanh toán 50% còn lại trong vòng 3 ngày làm việc sau khi bàn giao.\n"
		"Phương thức thanh toán: chuyển khoản ngân hàng."
	),
	"thanh_toan_en": (
		"A 50% deposit is required upon confirmation.\n"
		"The remaining 50% is due within 3 business days after delivery.\n"
		"Payment method: bank transfer."
	),
	"yeu_cau_vi": (
		"Bàn giao khu vực chuẩn bị và khu vực trưng bày bánh 2 tiếng trước khi "
		"sự kiện bắt đầu.\n"
		"Mặt bằng setup tối thiểu: 2m x 3m cho khu vực trưng bày.\n"
		"Lối đi cho xe giao hàng và thang máy (nếu venue ở tầng cao)."
	),
	"yeu_cau_en": (
		"Preparation and display area must be handed over 2 hours before the "
		"event.\nMinimum display area: 2m x 3m.\n"
		"Vehicle access and elevator required if venue is on upper floors."
	),
	"chinh_sach_huy_vi": (
		"Huỷ trước 7 ngày: hoàn 100% tiền cọc.\n"
		"Huỷ trong vòng 3 tới 7 ngày: hoàn 50% tiền cọc.\n"
		"Huỷ trong vòng 3 ngày: không hoàn cọc.\n"
		"Thay đổi số lượng: chấp nhận tăng giảm 10% nếu báo trước 3 ngày làm việc.\n"
		"Thay đổi menu: chấp nhận nếu báo trước 7 ngày làm việc, sau đó sẽ báo giá riêng."
	),
	"chinh_sach_huy_en": (
		"Cancellation 7+ days prior: 100% deposit refund.\n"
		"Cancellation 3 to 7 days prior: 50% deposit refund.\n"
		"Cancellation within 3 days: no refund.\n"
		"Quantity changes: 10% accepted if notified 3 business days prior.\n"
		"Menu changes accepted if notified 7 business days prior; later changes "
		"will be quoted separately."
	),
	"luu_y_vi": (
		"Linh hoạt: menu có thể điều chỉnh theo yêu cầu; phục vụ được thực đơn "
		"riêng cho khách dị ứng hoặc ăn kiêng nếu báo trước.\n"
		"Ràng buộc: giá có thể thay đổi tuỳ số lượng cuối cùng. Giá dựa trên giá "
		"nguyên liệu thị trường hiện tại; nếu có biến động lớn, Vagabond sẽ thông "
		"báo và thương lượng lại."
	),
	"luu_y_en": (
		"Flexible: menu can be adjusted upon request; special dietary or allergy "
		"menus available upon prior notice.\n"
		"Binding: prices may vary depending on final count. Prices are based on "
		"current market ingredient costs; in case of significant fluctuations, "
		"Vagabond will notify and renegotiate."
	),
	"ten_ban": "CÔNG TY TNHH PATISSERIE VAGABOND",
	"mst_ban": "0318561568",
	"dia_chi_ban": "307/1 Nguyễn Văn Trỗi, P. Tân Sơn Hoà, TP.HCM",
	"web_ban": "www.thevagabondpatisserie.com",
	"dai_dien_ban": "",
	"chuc_vu_ban": "",
	"dt_ban": "",
	"email_ban": "",
}

MOC_MAC_DINH = [
	{
		"moc_vi": "T-10 ngày", "moc_en": "T-10 days",
		"noi_dung_vi": "Hoàn thiện thiết kế và sản xuất khuôn bánh.",
		"noi_dung_en": "Finalize mold design and production.",
		"trach_nhiem": "Vagabond / Seller",
	},
	{
		"moc_vi": "Trước ngày thử bánh ít nhất 07 ngày",
		"moc_en": "At least 07 days before the sample tasting",
		"noi_dung_vi": "Khách hàng đăng ký lịch thử bánh để Vagabond chuẩn bị mẫu thử.",
		"noi_dung_en": "The Buyer schedules the sample tasting so Vagabond can prepare samples.",
		"trach_nhiem": "Bên mua / Buyer",
	},
	{
		"moc_vi": "Theo lịch đã thống nhất", "moc_en": "Per agreed schedule",
		"noi_dung_vi": "Bàn giao hàng theo số đợt hai bên thống nhất.",
		"noi_dung_en": "Deliver in the number of batches agreed by both parties.",
		"trach_nhiem": "Vagabond / Seller",
	},
]


# ------------------------------------------------------------------- quyen


def _quyen(sua=False):
	vai = set(frappe.get_roles())
	if sua:
		if not QUYEN_SUA & vai:
			frappe.throw("Chỉ bộ phận kinh doanh và kế toán được lập hoặc sửa báo giá.")
		return
	if not QUYEN_XEM & vai:
		frappe.throw("Không có quyền xem báo giá.")


def _cd():
	"""Cai dat bao gia, tra ve dict da chen san mac dinh cho o con trong."""
	try:
		d = frappe.get_single(DT_CD).as_dict()
	except Exception:
		d = {}
	ra = {}
	for k, v in MAC_DINH.items():
		ra[k] = (d.get(k) or "").strip() or v
	ra["moc_mau"] = [
		{
			"moc_vi": m.get("moc_vi"), "moc_en": m.get("moc_en"),
			"noi_dung_vi": m.get("noi_dung_vi"), "noi_dung_en": m.get("noi_dung_en"),
			"trach_nhiem": m.get("trach_nhiem"),
		}
		for m in (d.get("moc_mau") or [])
	] or MOC_MAC_DINH
	ra["ngan_hang_vi"] = (d.get("ngan_hang_vi") or "").strip()
	ra["ngan_hang_en"] = (d.get("ngan_hang_en") or "").strip()
	return ra


# ------------------------------------------------------------------- doc so


def _tinh(doc):
	"""Cong lai toan bo con so tren to bao gia, tinh o may chu.

	Don gia tren to Loan Anh gui khach la gia DA BAO GOM VAT (nhu file Elle
	ghi ro "Đơn giá (đã bao gồm VAT)"). Nen mac dinh khong cong them thue
	len tong; tat o gia_da_gom_vat thi moi cong.
	"""
	tam = 0.0
	for d in doc.get("dong") or []:
		d.so_luong = flt(d.so_luong)
		d.don_gia = flt(d.don_gia)
		d.chiet_khau = flt(d.chiet_khau)
		d.thanh_tien = round(d.so_luong * d.don_gia * (1 - d.chiet_khau / 100.0), 0)
		tam += d.thanh_tien
	doc.tam_tinh = tam
	doc.chiet_khau_tien = round(tam * flt(doc.chiet_khau_pt) / 100.0, 0)
	sau_ck = tam - doc.chiet_khau_tien
	if doc.gia_da_gom_vat:
		doc.thue_tien = 0
		doc.tong_cong = sau_ck + flt(doc.phi_giao)
	else:
		doc.thue_tien = round(sau_ck * flt(doc.thue_pt) / 100.0, 0)
		doc.tong_cong = sau_ck + doc.thue_tien + flt(doc.phi_giao)
	doc.dat_coc_tien = round(doc.tong_cong * flt(doc.dat_coc_pt) / 100.0, 0)
	return doc


F_CHU = (
	"ten", "ten_en", "khach_hang", "ten_khach", "ma_so_thue", "dia_chi",
	"nguoi_lien_he", "chuc_vu", "dien_thoai", "email", "loi_mo", "loi_mo_en",
	"thanh_toan", "thanh_toan_en", "yeu_cau_vi", "yeu_cau_en",
	"chinh_sach_huy_vi", "chinh_sach_huy_en", "luu_y_vi", "luu_y_en",
	"giao_hang", "dong_goi", "ghi_chu", "ghi_chu_noi_bo",
	"ten_nguoi_lap_in", "chuc_vu_lap", "dt_nguoi_lap", "email_lap",
)
F_SO = ("chiet_khau_pt", "thue_pt", "phi_giao", "dat_coc_pt")
F_CO = ("song_ngu", "gia_da_gom_vat")
F_DONG = (
	"loai", "ma_mon", "ma_tv", "ten_mon", "ten_en", "dvt", "dvt_en", "hinh",
	"kich_thuoc", "mo_ta", "mo_ta_en", "di_ung_vi", "di_ung_en",
	"danh_muc_vi", "danh_muc_en",
)


def _goi(doc):
	ra = {"name": doc.name}
	for f in F_CHU:
		ra[f] = doc.get(f) or ""
	for f in F_SO:
		ra[f] = flt(doc.get(f))
	for f in F_CO:
		ra[f] = 1 if doc.get(f) else 0
	ra.update({
		"trang_thai": doc.trang_thai or "Nháp",
		"ngay_bao_gia": str(doc.ngay_bao_gia or ""),
		"hieu_luc_den": str(doc.hieu_luc_den or ""),
		"hieu_luc_ngay": int(doc.hieu_luc_ngay or 30),
		"hop_dong": doc.hop_dong or "",
		"nguoi_lap": doc.nguoi_lap or "",
		"tam_tinh": flt(doc.tam_tinh),
		"chiet_khau_tien": flt(doc.chiet_khau_tien),
		"thue_tien": flt(doc.thue_tien),
		"tong_cong": flt(doc.tong_cong),
		"dat_coc_tien": flt(doc.dat_coc_tien),
	})
	ra["dong"] = []
	for d in doc.get("dong") or []:
		x = {f: d.get(f) or "" for f in F_DONG}
		x.update({
			"so_luong": flt(d.so_luong),
			"don_gia": flt(d.don_gia),
			"chiet_khau": flt(d.chiet_khau),
			"thanh_tien": flt(d.thanh_tien),
		})
		ra["dong"].append(x)
	ra["dich_vu"] = [
		{
			"ten_vi": d.ten_vi or "", "ten_en": d.ten_en or "",
			"gia_vi": d.gia_vi or "", "gia_en": d.gia_en or "",
		}
		for d in (doc.get("dich_vu") or [])
	]
	ra["moc"] = [
		{
			"moc_vi": d.moc_vi or "", "moc_en": d.moc_en or "",
			"noi_dung_vi": d.noi_dung_vi or "", "noi_dung_en": d.noi_dung_en or "",
			"trach_nhiem": d.trach_nhiem or "",
		}
		for d in (doc.get("moc") or [])
	]
	return ra


# ------------------------------------------------------------------ doc api


@frappe.whitelist()
def cai_dat():
	_quyen()
	return {
		"trang_thai": TRANG_THAI,
		"chip_hieu_luc": CHIP_HIEU_LUC,
		"chip_vat": CHIP_VAT,
		"duoc_sua": bool(QUYEN_SUA & set(frappe.get_roles())),
		"mac_dinh": _cd(),
	}


@frappe.whitelist()
def danh_sach(trang_thai=None, loc=None, tim=None):
	"""Danh sach bao gia kem so dem cho tung chip loc."""
	_quyen()
	ds = frappe.get_all(
		DT,
		fields=[
			"name", "ten", "trang_thai", "khach_hang", "ten_khach",
			"ngay_bao_gia", "hieu_luc_den", "tong_cong", "hop_dong",
			"nguoi_lap", "modified",
		],
		order_by="modified desc",
		limit_page_length=400,
	)
	hn = getdate(nowdate())
	toi = frappe.session.user
	for r in ds:
		hl = getdate(r["hieu_luc_den"]) if r.get("hieu_luc_den") else None
		con = (hl - hn).days if hl else None
		r["con_ngay"] = con
		r["dang_mo"] = r["trang_thai"] in ("Nháp", "Đã gửi khách")
		r["qua_han"] = bool(r["dang_mo"] and con is not None and con < 0)
		r["sap_het"] = bool(r["dang_mo"] and con is not None and 0 <= con <= 3)
		r["cua_toi"] = r.get("nguoi_lap") == toi

	dem = {
		"tat_ca": len(ds),
		"cho_khach": len([x for x in ds if x["trang_thai"] == "Đã gửi khách"]),
		"nhap": len([x for x in ds if x["trang_thai"] == "Nháp"]),
		"sap_het": len([x for x in ds if x["sap_het"]]),
		"qua_han": len([x for x in ds if x["qua_han"]]),
		"cua_toi": len([x for x in ds if x["cua_toi"] and x["dang_mo"]]),
		"duyet": len([x for x in ds if x["trang_thai"] == "Khách duyệt"]),
	}
	for t in TRANG_THAI:
		dem["tt:" + t] = len([x for x in ds if x["trang_thai"] == t])

	ra = ds
	if trang_thai:
		ra = [x for x in ra if x["trang_thai"] == trang_thai]
	if loc == "cho_khach":
		ra = [x for x in ra if x["trang_thai"] == "Đã gửi khách"]
	elif loc == "sap_het":
		ra = [x for x in ra if x["sap_het"]]
	elif loc == "qua_han":
		ra = [x for x in ra if x["qua_han"]]
	elif loc == "cua_toi":
		ra = [x for x in ra if x["cua_toi"] and x["dang_mo"]]
	elif loc == "gia_tri":
		ra = sorted(ra, key=lambda x: -flt(x["tong_cong"]))
	if tim:
		t = str(tim).lower()
		ra = [
			x for x in ra
			if t in ((x.get("ten") or "") + " " + (x.get("ten_khach") or "")
					 + " " + x["name"]).lower()
		]
	return {"dem": dem, "ds": ra[:200]}


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	return _goi(frappe.get_doc(DT, name))


@frappe.whitelist()
def moi():
	"""Khung to bao gia trong, chep san cau chu tu Cai dat bao gia."""
	_quyen(sua=True)
	nd = frappe.session.user
	c = _cd()
	u = frappe.db.get_value("User", nd, ["full_name", "mobile_no"], as_dict=True) or {}
	return {
		"name": "", "trang_thai": "Nháp", "song_ngu": 1, "gia_da_gom_vat": 1,
		"ten": "", "ten_en": "", "khach_hang": "", "ten_khach": "",
		"ma_so_thue": "", "dia_chi": "", "nguoi_lien_he": "", "chuc_vu": "",
		"dien_thoai": "", "email": "",
		"ngay_bao_gia": nowdate(), "hieu_luc_ngay": 30,
		"hieu_luc_den": add_days(nowdate(), 30),
		"hop_dong": "",
		"loi_mo": c["loi_mo_vi"], "loi_mo_en": c["loi_mo_en"],
		"thanh_toan": c["thanh_toan_vi"], "thanh_toan_en": c["thanh_toan_en"],
		"yeu_cau_vi": c["yeu_cau_vi"], "yeu_cau_en": c["yeu_cau_en"],
		"chinh_sach_huy_vi": c["chinh_sach_huy_vi"],
		"chinh_sach_huy_en": c["chinh_sach_huy_en"],
		"luu_y_vi": c["luu_y_vi"], "luu_y_en": c["luu_y_en"],
		"giao_hang": "", "dong_goi": "", "ghi_chu": "", "ghi_chu_noi_bo": "",
		"chiet_khau_pt": 0, "chiet_khau_tien": 0, "thue_pt": 8, "thue_tien": 0,
		"phi_giao": 0, "dat_coc_pt": 50, "dat_coc_tien": 0,
		"tam_tinh": 0, "tong_cong": 0,
		"nguoi_lap": nd,
		"ten_nguoi_lap_in": c["dai_dien_ban"] or u.get("full_name") or "",
		"chuc_vu_lap": c["chuc_vu_ban"] or "",
		"dt_nguoi_lap": c["dt_ban"] or u.get("mobile_no") or "",
		"email_lap": c["email_ban"] or nd,
		"dong": [], "dich_vu": [], "moc": list(c["moc_mau"]),
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
		for b in ("dong", "dich_vu", "moc"):
			doc.set(b, [])
	else:
		doc = frappe.new_doc(DT)
		doc.nguoi_lap = frappe.session.user

	for f in F_CHU:
		doc.set(f, d.get(f) or None)
	for f in ("ngay_bao_gia", "hieu_luc_den"):
		doc.set(f, d.get(f) or None)
	for f in F_SO:
		doc.set(f, flt(d.get(f)))
	for f in F_CO:
		doc.set(f, 1 if d.get(f) else 0)
	doc.hieu_luc_ngay = int(flt(d.get("hieu_luc_ngay")) or 30)
	if d.get("trang_thai") in TRANG_THAI:
		doc.trang_thai = d["trang_thai"]

	for x in d.get("dong") or []:
		if not (x.get("ten_mon") or x.get("ma_mon")):
			continue
		row = {f: (x.get(f) or None) for f in F_DONG}
		row["ten_mon"] = x.get("ten_mon") or x.get("ma_mon")
		row["loai"] = x.get("loai") or "Món"
		row["so_luong"] = flt(x.get("so_luong")) or 1
		row["don_gia"] = flt(x.get("don_gia"))
		row["chiet_khau"] = flt(x.get("chiet_khau"))
		doc.append("dong", row)
	if not doc.get("dong"):
		frappe.throw("Báo giá phải có ít nhất một dòng sản phẩm.")

	for x in d.get("dich_vu") or []:
		if not (x.get("ten_vi") or "").strip():
			continue
		doc.append("dich_vu", {
			"ten_vi": x.get("ten_vi"), "ten_en": x.get("ten_en") or None,
			"gia_vi": x.get("gia_vi") or None, "gia_en": x.get("gia_en") or None,
		})
	for x in d.get("moc") or []:
		if not (x.get("moc_vi") or "").strip():
			continue
		doc.append("moc", {
			"moc_vi": x.get("moc_vi"), "moc_en": x.get("moc_en") or None,
			"noi_dung_vi": x.get("noi_dung_vi") or None,
			"noi_dung_en": x.get("noi_dung_en") or None,
			"trach_nhiem": x.get("trach_nhiem") or "Vagabond / Seller",
		})

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
	"""Nhan ban mot to. Mua trung thu Loan Anh gui gan giong nhau cho hang
	chuc cong ty, chi khac ten khach va so luong."""
	_quyen(sua=True)
	cu = frappe.get_doc(DT, name)
	moi_ = frappe.copy_doc(cu)
	moi_.trang_thai = "Nháp"
	moi_.hop_dong = None
	moi_.ngay_bao_gia = nowdate()
	moi_.hieu_luc_den = add_days(nowdate(), int(cu.hieu_luc_ngay or 30))
	moi_.nguoi_lap = frappe.session.user
	moi_.insert(ignore_permissions=True)
	return moi_.name


# --------------------------------------------------------------- thu vien


@frappe.whitelist()
def tv_danh_sach(loai=None, tim=None):
	_quyen()
	loc = {}
	if loai:
		loc["loai"] = loai
	ds = frappe.get_all(
		DT_TV,
		filters=loc,
		fields=[
			"name", "loai", "nhom", "ten_vi", "ten_en", "hinh", "don_gia",
			"dvt_vi", "gia_chu_vi", "kich_thuoc", "dung", "ma_item",
		],
		order_by="loai asc, thu_tu asc, ten_vi asc",
		limit_page_length=0,
	)
	if tim:
		t = str(tim).lower()
		ds = [
			x for x in ds
			if t in ((x.get("ten_vi") or "") + " " + (x.get("ten_en") or "")
					 + " " + (x.get("nhom") or "")).lower()
		]
	dem = {}
	for x in ds:
		dem[x["loai"]] = dem.get(x["loai"], 0) + 1
	return {"ds": ds, "dem": dem, "so_thieu_anh": len([x for x in ds if not x["hinh"]])}


@frappe.whitelist()
def tv_chi_tiet(name):
	_quyen()
	return frappe.get_doc(DT_TV, name).as_dict()


@frappe.whitelist()
def tv_luu(du_lieu):
	_quyen(sua=True)
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	if not (d.get("ten_vi") or "").strip():
		frappe.throw("Nhập tên tiếng Việt đã nhé.")
	name = d.get("name") or ""
	doc = frappe.get_doc(DT_TV, name) if name else frappe.new_doc(DT_TV)
	for f in (
		"loai", "nhom", "ten_vi", "ten_en", "ma_item", "hinh", "kich_thuoc",
		"dvt_vi", "dvt_en", "gia_chu_vi", "gia_chu_en", "mo_ta_vi", "mo_ta_en",
		"di_ung_vi", "di_ung_en", "ghi_chu_noi_bo",
	):
		if f in d:
			doc.set(f, d.get(f) or None)
	doc.don_gia = flt(d.get("don_gia"))
	doc.thu_tu = int(flt(d.get("thu_tu")))
	doc.dung = 0 if d.get("dung") in (0, "0", False) else 1
	doc.save(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def tv_xoa(name):
	_quyen(sua=True)
	frappe.delete_doc(DT_TV, name, ignore_permissions=True)
	return 1


@frappe.whitelist()
def tv_tu_dong(name_bao_gia, dong_idx):
	"""Luu mot dong dang soan tren to bao gia vao thu vien de lan sau chon lai."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name_bao_gia)
	i = int(dong_idx)
	if i < 0 or i >= len(doc.dong):
		frappe.throw("Không có dòng này.")
	d = doc.dong[i]
	tv = frappe.new_doc(DT_TV)
	tv.loai = d.loai or "Món"
	tv.nhom = d.danh_muc_vi or ("Món thiết kế riêng" if not d.ma_mon else "")
	tv.ten_vi = d.ten_mon
	tv.ten_en = d.ten_en
	tv.ma_item = d.ma_mon
	tv.hinh = d.hinh
	tv.kich_thuoc = d.kich_thuoc
	tv.don_gia = flt(d.don_gia)
	tv.dvt_vi = d.dvt
	tv.dvt_en = d.dvt_en
	tv.mo_ta_vi = d.mo_ta
	tv.mo_ta_en = d.mo_ta_en
	tv.di_ung_vi = d.di_ung_vi
	tv.di_ung_en = d.di_ung_en
	tv.insert(ignore_permissions=True)
	frappe.db.set_value("Bao Gia Dong", d.name, "ma_tv", tv.name)
	return tv.name


@frappe.whitelist()
def cd_luu(du_lieu):
	"""Ghi lai cau chu khung to bao gia."""
	_quyen(sua=True)
	if "Sales Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản lý kinh doanh mới sửa được câu chữ khung tờ báo giá.")
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	doc = frappe.get_single(DT_CD)
	for f in (
		"ten_ban", "mst_ban", "dia_chi_ban", "web_ban", "dai_dien_ban",
		"chuc_vu_ban", "dt_ban", "email_ban", "loi_mo_vi", "loi_mo_en",
		"thanh_toan_vi", "thanh_toan_en", "ngan_hang_vi", "ngan_hang_en",
		"yeu_cau_vi", "yeu_cau_en", "chinh_sach_huy_vi", "chinh_sach_huy_en",
		"luu_y_vi", "luu_y_en",
	):
		if f in d:
			doc.set(f, d.get(f) or None)
	doc.save(ignore_permissions=True)
	return 1


@frappe.whitelist()
def cd_doc():
	_quyen()
	return _cd()


# ------------------------------------------------------------ chon khach


@frappe.whitelist()
def tim_khach(tim=None, so_dong=300):
	_quyen()
	loc = {"disabled": 0}
	if tim:
		loc["customer_name"] = ["like", "%%%s%%" % tim]
	return frappe.get_all(
		"Customer",
		filters=loc,
		fields=["name", "customer_name", "tax_id", "mobile_no", "customer_group"],
		order_by="customer_name",
		limit_page_length=int(so_dong or 300),
	)


@frappe.whitelist()
def thong_tin_khach(khach):
	_quyen()
	kh = frappe.db.get_value(
		"Customer", khach, ["customer_name", "tax_id", "mobile_no"], as_dict=True
	) or {}
	dc = frappe.db.sql(
		"""select a.address_line1, a.address_line2, a.city, a.state
		from `tabAddress` a join `tabDynamic Link` l on l.parent = a.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by a.is_primary_address desc limit 1""",
		khach, as_dict=True,
	)
	dia_chi = ""
	if dc:
		dia_chi = ", ".join([
			x for x in [dc[0].address_line1, dc[0].address_line2, dc[0].city, dc[0].state] if x
		])
	lh = frappe.db.sql(
		"""select c.first_name, c.last_name, c.mobile_no, c.email_id, c.designation
		from `tabContact` c join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by c.is_primary_contact desc limit 1""",
		khach, as_dict=True,
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

PHONG = "'DejaVu Sans','Liberation Sans',Arial,Helvetica,sans-serif"
VIEN = "1px solid #c9c4bd"
LA_MA = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def _esc(s):
	return frappe.utils.escape_html(str(s or ""))


def _br(s):
	"""Doi xuong dong thanh <br>, giu nguyen phan con lai da escape."""
	return _esc(s).replace("\n", "<br>")


def _anh_data(url):
	"""Doc anh tren dia may chu thanh data URI de nhung thang vao PDF.

	wkhtmltopdf chay tien trinh rieng, tro src toi duong dan tuong doi thi co
	luc no khong tai duoc - to gui khach ma trong khung anh thi hong. Doc
	thang tu dia chac an hon.
	"""
	if not url:
		return ""
	if str(url).startswith("data:"):
		return url
	try:
		import os

		from frappe.utils import get_files_path

		u = str(url).split("?")[0]
		ten = os.path.basename(u)
		rieng = "/private/" in u
		duong = get_files_path(ten, is_private=rieng)
		if not os.path.exists(duong):
			return ""
		# LUON thu nho lai truoc khi nhung. Anh mon chup marketing hay nang 5
		# toi 6 MB moi tam, bon tam la to PDF hon 20 MB, gui email khong noi.
		# Cot Minh hoa chi in rong 80px nen 520px la du net.
		try:
			import io

			from PIL import Image

			im = Image.open(duong)
			if im.mode in ("RGBA", "LA", "P"):
				nen = Image.new("RGB", im.size, (255, 255, 255))
				im = im.convert("RGBA")
				nen.paste(im, mask=im.split()[-1])
				im = nen
			else:
				im = im.convert("RGB")
			im.thumbnail((520, 520))
			bo = io.BytesIO()
			im.save(bo, "JPEG", quality=84)
			return "data:image/jpeg;base64," + base64.b64encode(bo.getvalue()).decode()
		except Exception:
			pass
		if os.path.getsize(duong) > 2 * 1024 * 1024:
			return ""
		kieu = "image/png" if ten.lower().endswith(".png") else "image/jpeg"
		with open(duong, "rb") as f:
			return "data:%s;base64,%s" % (kieu, base64.b64encode(f.read()).decode())
	except Exception:
		return ""


def _html(name):
	"""To bao gia song ngu, dung khuon to Loan Anh dang gui khach."""
	d = chi_tiet(name)
	c = _cd()
	sng = bool(d.get("song_ngu"))
	ra = []
	so_muc = [0]

	def muc(vi, en):
		so_muc[0] += 1
		nhan = LA_MA[min(so_muc[0] - 1, len(LA_MA) - 1)]
		t = "%s. %s" % (nhan, _esc(vi))
		if sng and en:
			t += " / " + _esc(en)
		ra.append(
			'<div style="font-size:13px;font-weight:bold;margin:16px 0 7px;'
			'border-bottom:2px solid #1c1a17;padding-bottom:3px">%s</div>' % t
		)

	def sn(vi, en, co=None, tho=False):
		"""Mot o song ngu: tieng Viet tren, tieng Anh nghieng nho ben duoi.

		tho = True khi vi va en DA la HTML dung san (co the <b>), luc do
		khong escape nua - neu escape thi khach nhin thay chu <b> tren to.
		"""
		lam = (lambda x: str(x or "").replace("\n", "<br>")) if tho else _br
		o = '<div style="font-size:%s">%s</div>' % (co or "10.5px", lam(vi))
		if sng and (en or "").strip():
			o += (
				'<div style="font-size:9.5px;color:#666;font-style:italic;'
				'margin-top:1px">%s</div>' % lam(en)
			)
		return o

	def th(vi, en, rong=None):
		return (
			'<th style="border:%s;padding:5px 6px;background:#f3f0ec;font-size:10px;'
			'font-weight:bold;text-align:center;%s">%s%s</th>'
			% (
				VIEN,
				("width:%s;" % rong) if rong else "",
				_esc(vi),
				('<div style="font-weight:normal;font-style:italic;color:#555">%s</div>' % _esc(en))
				if (sng and en) else "",
			)
		)

	def td(noi, canh="left", dam=False, ngat=True):
		return (
			'<td style="border:%s;padding:4px 6px;font-size:10.5px;text-align:%s;'
			'vertical-align:top;%s%s">%s</td>'
			% (VIEN, canh, "font-weight:bold;" if dam else "",
			   "" if ngat else "white-space:nowrap;", noi)
		)

	# ------------------------------------------------------------ dau to
	ra.append(
		'<div style="font-family:%s;color:#1c1a17;font-size:11px;line-height:1.4">' % PHONG
	)
	ra.append(
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:42%;vertical-align:middle">'
		'<img src="/files/vagabond_logo_print.png" width="145" height="60" '
		'style="width:145px !important;height:60px !important;object-fit:contain"></td>'
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10px;color:#1c1a17">' + _esc(c["ten_ban"]) + "</b><br>"
		"MST: " + _esc(c["mst_ban"]) + "<br>"
		+ _esc(c["dia_chi_ban"]) + "<br>" + _esc(c["web_ban"])
		+ "</td></tr></table>"
	)
	tieu_de = "BẢNG BÁO GIÁ SẢN PHẨM"
	ra.append(
		'<div style="text-align:center;margin:12px 0 3px">'
		'<div style="font-size:18px;font-weight:bold;letter-spacing:1px">%s</div>%s%s</div>'
		% (
			tieu_de,
			'<div style="font-size:11px;color:#555;font-style:italic">Production Price Quotation</div>'
			if sng else "",
			('<div style="font-size:12px;margin-top:4px">%s</div>' % sn(d["ten"], d.get("ten_en"), "12px"))
			if d.get("ten") else "",
		)
	)
	hl = d.get("hieu_luc_ngay") or 30
	ra.append(
		'<table style="width:100%%;border-collapse:collapse;margin-top:8px">'
		"<tr>%s%s</tr><tr>%s</tr></table>"
		% (
			td(sn("Mã báo giá: <b>%s</b>" % _esc(d["name"]), "Quotation No.", tho=True)),
			td(sn("Ngày báo giá: <b>%s</b>" % _ngay_vn(d["ngay_bao_gia"]), "Date", tho=True)),
			'<td colspan="2" style="border:%s;padding:4px 6px;font-size:10.5px">%s</td>'
			% (VIEN, sn(
				"Báo giá có hiệu lực trong vòng %d ngày kể từ ngày báo giá (đến hết %s)."
				% (hl, _ngay_vn(d["hieu_luc_den"])),
				"This quotation is valid for %d days from the date of issue." % hl,
			)),
		)
	)
	if (d.get("loi_mo") or "").strip():
		ra.append(
			'<div style="border:%s;padding:8px 10px;margin-top:8px;background:#faf8f5">%s</div>'
			% (VIEN, sn(d["loi_mo"], d.get("loi_mo_en")))
		)

	# --------------------------------------------- I. Thong tin dai dien
	muc("Thông tin đại diện", "Representative Information")
	def _ben(nhan_vi, nhan_en, ds):
		o = ['<div style="font-weight:bold;font-size:10.5px;margin-bottom:3px">%s%s</div>'
			 % (_esc(nhan_vi), (" / " + _esc(nhan_en)) if sng else "")]
		for nvi, nen, gt in ds:
			if not (gt or "").strip():
				continue
			o.append(
				'<div style="font-size:10px;margin-top:2px"><span style="color:#666">%s%s:</span> '
				'<b>%s</b></div>' % (_esc(nvi), (" / " + _esc(nen)) if sng else "", _esc(gt))
			)
		return "".join(o)

	mua = _ben("Bên mua", "Buyer", [
		("Đơn vị", "Company", d.get("ten_khach")),
		("Mã số thuế", "Tax code", d.get("ma_so_thue")),
		("Đại diện", "Representative", d.get("nguoi_lien_he")),
		("Chức vụ", "Title", d.get("chuc_vu")),
		("Địa chỉ", "Address", d.get("dia_chi")),
		("Điện thoại", "Tel", d.get("dien_thoai")),
		("Email", "Email", d.get("email")),
	])
	ban = _ben("Bên bán", "Seller", [
		("Đơn vị", "Company", c["ten_ban"]),
		("Mã số thuế", "Tax code", c["mst_ban"]),
		("Đại diện", "Representative", d.get("ten_nguoi_lap_in")),
		("Chức vụ", "Title", d.get("chuc_vu_lap")),
		("Địa chỉ", "Address", c["dia_chi_ban"]),
		("Điện thoại", "Tel", d.get("dt_nguoi_lap")),
		("Email", "Email", d.get("email_lap")),
	])
	ra.append(
		'<table style="width:100%%;border-collapse:collapse"><tr>'
		'<td style="border:%s;padding:7px 9px;width:50%%;vertical-align:top">%s</td>'
		'<td style="border:%s;padding:7px 9px;width:50%%;vertical-align:top">%s</td>'
		"</tr></table>" % (VIEN, mua, VIEN, ban)
	)

	# ------------------------------------------------ II. Menu de xuat
	mons = [x for x in d["dong"] if (x.get("loai") or "Món") == "Món"]
	co_menu = any(
		(x.get("mo_ta") or x.get("hinh") or x.get("di_ung_vi") or x.get("kich_thuoc"))
		for x in mons
	)
	if mons and co_menu:
		muc("Các món đề xuất", "Proposed Menu")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("No.", "", "30px") + th("Tên món", "Name")
			+ th("Mô tả", "Description") + th("Danh mục", "Category")
			+ th("Dị ứng", "Allergen") + th("Kích thước", "Size", "62px")
			+ th("Minh hoạ", "Image", "88px") + "</tr>"
		)
		for i, x in enumerate(mons, 1):
			anh = _anh_data(x.get("hinh"))
			o_anh = (
				'<img src="%s" style="width:80px;height:auto;max-height:70px;'
				'object-fit:contain">' % anh
			) if anh else '<span style="color:#bbb;font-size:9px">-</span>'
			ra.append(
				"<tr>" + td(str(i), "center") + td(sn(x["ten_mon"], x.get("ten_en")))
				+ td(sn(x.get("mo_ta"), x.get("mo_ta_en")))
				+ td(sn(x.get("danh_muc_vi"), x.get("danh_muc_en")))
				+ td(sn(x.get("di_ung_vi"), x.get("di_ung_en")))
				+ td(_esc(x.get("kich_thuoc")), "center")
				+ td(o_anh, "center") + "</tr>"
			)
		ra.append("</table>")

	# --------------------------------------------- III. Bao gia tam tinh
	muc("Báo giá tạm tính", "Estimated Quotation")
	ghi_vat = (
		"Đơn giá đã bao gồm VAT."
		if d.get("gia_da_gom_vat") else "Đơn giá chưa bao gồm VAT."
	)
	ghi_vat_en = (
		"Unit prices include VAT."
		if d.get("gia_da_gom_vat") else "Unit prices exclude VAT."
	)
	ra.append('<div style="margin-bottom:4px">%s</div>' % sn(ghi_vat, ghi_vat_en, "10px"))
	ra.append('<table style="width:100%;border-collapse:collapse">')
	co_ck = any(flt(x["chiet_khau"]) for x in d["dong"])
	ra.append(
		"<tr>" + th("No.", "", "30px") + th("Hạng mục", "Description")
		+ th("Đơn giá", "Unit price", "92px") + th("Số lượng", "Qty", "58px")
		+ (th("CK", "Disc.", "44px") if co_ck else "")
		+ th("Thành tiền", "Amount", "104px") + "</tr>"
	)
	for i, x in enumerate(d["dong"], 1):
		o = "<tr>" + td(str(i), "center") + td(sn(x["ten_mon"], x.get("ten_en")))
		o += td(_tien_vn(x["don_gia"]), "right", ngat=False)
		o += td(
			_tien_vn(x["so_luong"]) + (" " + _esc(x.get("dvt")) if x.get("dvt") else ""),
			"center", ngat=False,
		)
		if co_ck:
			o += td(("%g%%" % flt(x["chiet_khau"])) if flt(x["chiet_khau"]) else "-", "center")
		o += td(_tien_vn(x["thanh_tien"]), "right", dam=True, ngat=False) + "</tr>"
		ra.append(o)

	so_cot = 5 + (1 if co_ck else 0)

	def dong_cong(vi, en, tien, dam=False):
		return (
			'<tr><td colspan="%d" style="border:%s;padding:5px 6px;text-align:right;'
			'font-size:%s;%s">%s</td>'
			'<td style="border:%s;padding:5px 6px;text-align:right;white-space:nowrap;'
			'font-size:%s;%s">%s</td></tr>'
			% (
				so_cot - 1, VIEN, "11px" if dam else "10.5px",
				"font-weight:bold;" if dam else "",
				(_esc(vi) + (" / " + _esc(en) if (sng and en) else "")),
				VIEN, "12px" if dam else "10.5px",
				"font-weight:bold;" if dam else "", _tien_vn(tien),
			)
		)

	if flt(d["chiet_khau_tien"]) or flt(d["phi_giao"]) or flt(d["thue_tien"]):
		ra.append(dong_cong("Cộng tiền hàng", "Subtotal", d["tam_tinh"]))
	if flt(d["chiet_khau_tien"]):
		ra.append(dong_cong(
			"Chiết khấu %g%%" % flt(d["chiet_khau_pt"]), "Discount", -flt(d["chiet_khau_tien"])
		))
	if flt(d["phi_giao"]):
		ra.append(dong_cong("Phí giao hàng", "Delivery fee", d["phi_giao"]))
	if flt(d["thue_tien"]):
		ra.append(dong_cong("Thuế GTGT %g%%" % flt(d["thue_pt"]), "VAT", d["thue_tien"]))
	ra.append(dong_cong("TỔNG TIỀN TẠM TÍNH", "Estimated Total", d["tong_cong"], dam=True))
	ra.append("</table>")
	ra.append(
		'<div style="margin-top:5px;font-size:10.5px">%s</div>'
		% sn("Bằng chữ: <i>%s</i>" % _esc(_chu_so_tien(d["tong_cong"])), "", tho=True)
	)

	# ----------------------------------------------- IV. Dich vu them
	if d.get("dich_vu"):
		muc("Dịch vụ thêm", "Additional Services")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("No.", "", "30px") + th("Hạng mục", "Description")
			+ th("Đơn giá", "Unit price", "190px") + "</tr>"
		)
		for i, x in enumerate(d["dich_vu"], 1):
			ra.append(
				"<tr>" + td(str(i), "center") + td(sn(x["ten_vi"], x.get("ten_en")))
				+ td(sn(x.get("gia_vi"), x.get("gia_en"))) + "</tr>"
			)
		ra.append("</table>")

	# --------------------------------------------- V. Quy trinh van hanh
	if d.get("moc"):
		muc("Quy trình vận hành", "Operation Process")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("Mốc thời gian", "Timeline", "150px")
			+ th("Nội dung", "Action") + th("Trách nhiệm", "Responsibility", "120px") + "</tr>"
		)
		for x in d["moc"]:
			ra.append(
				"<tr>" + td(sn(x["moc_vi"], x.get("moc_en")))
				+ td(sn(x.get("noi_dung_vi"), x.get("noi_dung_en")))
				+ td(_esc(x.get("trach_nhiem")), "center") + "</tr>"
			)
		ra.append("</table>")

	def khoi(vi_key, en_key, nhan_vi, nhan_en):
		if not (d.get(vi_key) or "").strip():
			return
		muc(nhan_vi, nhan_en)
		ra.append(
			'<div style="border:%s;padding:7px 9px">%s</div>'
			% (VIEN, sn(d[vi_key], d.get(en_key)))
		)

	khoi("yeu_cau_vi", "yeu_cau_en", "Yêu cầu vận hành", "Operation Requirements")

	# ------------------------------------------ Dieu khoan thanh toan
	muc("Điều khoản thanh toán", "Payment Terms")
	from vagabond import tai_khoan

	try:
		qr = tai_khoan.tk_phieu_no() or {}
	except Exception:
		qr = {}
	tien_qr = flt(d["dat_coc_tien"]) or flt(d["tong_cong"])
	def _rut(ten, con):
		"""Cat ten khach theo TU cho du con, khong cat giua chung mot chu."""
		ra = []
		for tu in str(ten or "").split():
			if len(" ".join(ra + [tu])) > con:
				break
			ra.append(tu)
		return " ".join(ra)

	nd_qr = ("%s %s" % (d["name"], _rut(d.get("ten_khach"), 22))).strip()
	anh_qr = _qr_data_uri(qr, tien_qr, nd_qr) if qr.get("stk") else ""
	tt = []
	if (d.get("thanh_toan") or "").strip():
		tt.append(sn(d["thanh_toan"], d.get("thanh_toan_en")))
	if flt(d["dat_coc_tien"]):
		tt.append(
			'<div style="margin-top:5px;font-size:11.5px"><b>%s: %s đ</b></div>'
			% (
				"Số tiền đặt cọc (%g%%)" % flt(d["dat_coc_pt"])
				+ (" / Deposit" if sng else ""),
				_tien_vn(d["dat_coc_tien"]),
			)
		)
	if qr.get("stk"):
		tt.append(
			'<div style="margin-top:6px;font-size:10.5px;line-height:1.6">'
			'<b>%s</b><br>%s<br>%s: <b>%s</b> &nbsp; %s: %s<br>%s: <b>%s</b></div>'
			% (
				_esc(c["ten_ban"]),
				_esc(TEN_NGAN_HANG_DAY_DU.get(qr.get("bank") or "", qr.get("bank") or "")),
				"Số tài khoản" + (" / Account No." if sng else ""),
				_esc(qr.get("stk") or ""),
				"Số tiền" + (" / Amount" if sng else ""),
				_tien_vn(tien_qr) + " đ",
				"Nội dung" + (" / Reference" if sng else ""),
				_esc(nd_qr),
			)
		)
	o_qr = (
		'<td style="border:none;width:130px;text-align:center;vertical-align:top;'
		'padding-left:10px"><img src="%s" width="118" height="118" '
		'style="width:118px !important;height:118px !important">'
		'<div style="font-size:8.5px;color:#666;margin-top:2px">%s</div></td>'
		% (anh_qr, "Quét mã để chuyển khoản" + ("<br>Scan to pay" if sng else ""))
	) if anh_qr else ""
	ra.append(
		'<table style="width:100%%;border:%s;border-collapse:collapse"><tr>'
		'<td style="border:none;padding:7px 9px;vertical-align:top">%s</td>%s</tr></table>'
		% (VIEN, "".join(tt), o_qr)
	)

	khoi("chinh_sach_huy_vi", "chinh_sach_huy_en",
		 "Chính sách huỷ và thay đổi", "Cancellation & Amendment Policy")
	khoi("luu_y_vi", "luu_y_en", "Lưu ý", "Notes")

	them = []
	for nvi, nen, gt in (
		("Thời gian và địa điểm giao hàng", "Delivery", d.get("giao_hang")),
		("Quy cách đóng gói", "Packaging", d.get("dong_goi")),
		("Ghi chú", "Notes", d.get("ghi_chu")),
	):
		if (gt or "").strip():
			them.append(
				'<div style="margin-bottom:4px"><b>%s%s:</b> %s</div>'
				% (_esc(nvi), (" / " + _esc(nen)) if sng else "", _br(gt))
			)
	if them:
		muc("Nội dung khác", "Other Details")
		ra.append('<div style="border:%s;padding:7px 9px;font-size:10.5px">%s</div>'
				  % (VIEN, "".join(them)))

	# ------------------------------------------------------------ chu ky
	ngay = getdate(d["ngay_bao_gia"]) if d.get("ngay_bao_gia") else getdate(nowdate())
	ra.append(
		'<div style="text-align:right;margin-top:16px;font-size:10.5px">%s</div>'
		% sn(
			"Thành phố Hồ Chí Minh, ngày %02d tháng %02d năm %d" % (ngay.day, ngay.month, ngay.year),
			"Ho Chi Minh City, %s %d, %d" % (ngay.strftime("%B"), ngay.day, ngay.year),
		)
	)
	ra.append(
		'<table style="width:100%%;border:none;border-collapse:collapse;margin-top:8px">'
		'<tr><td style="border:none;width:50%%;text-align:center;font-size:10.5px">'
		"<b>Đại diện bên mua%s</b>"
		'<div style="font-size:9px;color:#666">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>_____________________</td>'
		'<td style="border:none;width:50%%;text-align:center;font-size:10.5px">'
		"<b>Đại diện bên bán%s</b>"
		'<div style="font-size:9px;color:#666">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>_____________________'
		'<div style="font-weight:bold;margin-top:3px">%s</div>'
		'<div style="font-size:9.5px;color:#555">%s</div></td></tr></table>'
		% (
			" / Buyer" if sng else "", " / Seller" if sng else "",
			_esc(d.get("ten_nguoi_lap_in")), _esc(d.get("chuc_vu_lap")),
		)
	)
	ra.append(
		'<div style="margin-top:10px;font-size:9px;color:#777;text-align:center">%s</div>'
		% (
			"Khi ký vào bảng báo giá này, hai bên đồng ý với toàn bộ điều khoản nêu trên."
			+ ("<br><i>By signing, both parties agree to the terms and conditions stated "
			   "in this quotation.</i>" if sng else "")
		)
	)
	ra.append("</div>")
	return "".join(ra)


@frappe.whitelist()
def xem_truoc(name):
	_quyen()
	return {"html": _html(name)}


def _ten_tep(name):
	ten_kh = frappe.db.get_value(DT, name, "ten_khach") or ""
	from vagabond.danh_muc import khong_dau

	goi = khong_dau(ten_kh).replace(" ", "-")[:40] if ten_kh else ""
	return "%s%s" % (name, ("-" + goi) if goi else "")


@frappe.whitelist()
def xuat_pdf(name):
	"""To bao gia ra PDF A4 doc de gui khach."""
	_quyen()
	from frappe.utils.pdf import get_pdf

	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:11mm 9mm}body{margin:0}"
		"table{page-break-inside:auto}tr{page-break-inside:avoid}</style>"
		"</head><body>" + _html(name) + "</body></html>"
	)
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Bao-gia-%s.pdf" % _ten_tep(name),
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
	than = (
		'<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
		'line-height:1.6;color:#1c1a17">'
		"<p>Kính gửi Quý khách %s,</p>"
		"<p>The Vagabond Pâtisserie trân trọng gửi Quý khách bảng báo giá "
		"<b>%s</b> theo nội dung trao đổi. Chi tiết vui lòng xem tệp PDF đính kèm.</p>"
		"<p>Báo giá có hiệu lực đến hết ngày <b>%s</b>. Tổng giá trị tạm tính là "
		"<b>%s đ</b>.</p>%s"
		"<p>Quý khách cần điều chỉnh số lượng hoặc quy cách, xin vui lòng phản hồi "
		"lại email này hoặc liên hệ trực tiếp với chúng tôi.</p>"
		"<p>Trân trọng,<br><b>%s</b><br>%s<br>The Vagabond Pâtisserie<br>%s</p></div>"
	) % (
		_esc(doc.ten_khach or ""), _esc(doc.ten or ""),
		_ngay_vn(doc.hieu_luc_den) or "...", _tien_vn(doc.tong_cong),
		("<p>%s</p>" % _esc(loi_nhan)) if (loi_nhan or "").strip() else "",
		_esc(doc.ten_nguoi_lap_in or ""), _esc(doc.chuc_vu_lap or ""),
		_esc(_cd()["web_ban"]),
	)
	frappe.sendmail(
		recipients=[toi],
		subject="Báo giá %s - The Vagabond Pâtisserie" % doc.name,
		message=than,
		attachments=[{"fname": tep["ten_file"], "fcontent": base64.b64decode(tep["b64"])}],
		reference_doctype=DT,
		reference_name=doc.name,
		now=True,
	)
	if doc.trang_thai == "Nháp":
		frappe.db.set_value(DT, name, "trang_thai", "Đã gửi khách")
	if not doc.email:
		frappe.db.set_value(DT, name, "email", toi)
	return {"ok": 1, "toi": toi}


@frappe.whitelist()
def tao_hop_dong(name, so_hop_dong=None, ngay_ky=None, ngay_su_kien=None):
	"""Bao gia khach duyet thi bam mot nut ra Hop dong ban hang."""
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
		% (i, x.ten_mon or "", _tien_vn(x.so_luong), x.dvt or "",
		   _tien_vn(x.don_gia), _tien_vn(x.thanh_tien))
		for i, x in enumerate(doc.dong, 1)
	)
	if doc.thanh_toan:
		noi_dung += "\nĐiều kiện thanh toán: %s" % doc.thanh_toan
	if doc.giao_hang:
		noi_dung += "\nGiao hàng: %s" % doc.giao_hang
	hd = frappe.get_doc({
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
	})
	hd.insert(ignore_permissions=True)
	frappe.db.set_value(DT, name, {"hop_dong": hd.name, "trang_thai": "Đã lên hợp đồng"})
	return hd.name
