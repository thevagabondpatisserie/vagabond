"""Kiem ke xoay vong hang ngay (anh Viet chot 02/08/2026).

Y anh Viet: cho MOI nhan vien di kiem hang moi ngay de khong bi don viec cuoi
thang. Hai rang buoc anh chot:

1. Nhan vien chi DEM va chot phieu; MOI dieu chinh ton kho deu phai qua quan
   ly duyet (trang thai "Cho duyet" -> quan ly ghi so). Server chan them mot
   lop: chi Stock Manager moi tao duoc Stock Reconciliation.
2. May tu chia lich xoay vong, nhan vien mo app la thay hom nay dem gi, khong
   phai tu nghi - trong thang di het mot vong kho, hang dat tien dem day hon.

Cach chia hang (kieu ABC theo gia tri ton):
- Xep moi ma theo gia tri ton (so luong x gia von) giam dan trong tung kho.
- Cong don den 70% gia tri = hang A, den 90% = hang B, con lai hang C.
- Chu ky dem: A moi 7 ngay, B 15 ngay, C 30 ngay.
- Moi ngay chi liet ke toi da MOI_NGAY ma qua han lau nhat, de mot ca lam
  duoc trong 15-20 phut chu khong thanh gong ganh.
"""

import frappe
from frappe.utils import cint, flt, getdate, nowdate

VAI_DEM = {
	"System Manager",
	"Stock Manager",
	"Stock User",
	"Kiểm kê viên",
	"Bộ phận đặt hàng",
	"Manufacturing User",
}
VAI_DUYET = {"System Manager", "Stock Manager"}

CHU_KY = {"A": 7, "B": 15, "C": 30}
NGUONG_A = 0.70
NGUONG_B = 0.90
MOI_NGAY = 40


def _duoc_dem():
	if not VAI_DEM & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền kiểm kê.")


def duoc_duyet():
	return bool(VAI_DUYET & set(frappe.get_roles()))


def _ngay_dem_gan_nhat(kho):
	"""Ma hang -> ngay duoc dem gan nhat trong kho do."""
	rows = frappe.db.sql(
		"""
		select ct.item_code as ma, max(p.ngay_kiem) as ngay
		from `tabChi Tiet Kiem Ke` ct
		join `tabPhieu Kiem Ke` p on p.name = ct.parent
		where p.kho = %s
		  and p.trang_thai in ('Đã chốt', 'Đã ghi sổ')
		  and ct.da_dem = 1
		group by ct.item_code
		""",
		(kho,),
		as_dict=True,
	)
	return {r["ma"]: getdate(r["ngay"]) for r in rows if r.get("ngay")}


def _ton_theo_kho(kho):
	"""Cac ma con ton trong kho kem gia tri ton."""
	return frappe.db.sql(
		"""
		select b.item_code as ma, b.actual_qty as sl, b.stock_value as gia_tri,
		       i.item_name as ten, i.item_group as nhom, i.stock_uom as dvt
		from `tabBin` b
		join `tabItem` i on i.name = b.item_code
		where b.warehouse = %s and b.actual_qty != 0 and i.disabled = 0
		""",
		(kho,),
		as_dict=True,
	)


def _xep_hang(ds):
	"""Gan hang A/B/C cho tung ma theo gia tri ton luy ke."""
	ds = sorted(ds, key=lambda x: flt(x.get("gia_tri")), reverse=True)
	tong = sum(flt(x.get("gia_tri")) for x in ds) or 1.0
	luy = 0.0
	for x in ds:
		luy += flt(x.get("gia_tri"))
		ty = luy / tong
		x["hang"] = "A" if ty <= NGUONG_A else ("B" if ty <= NGUONG_B else "C")
	return ds


@frappe.whitelist()
def lich_hom_nay(kho=None, gioi_han=None):
	"""Danh sach ma can dem hom nay cua mot kho.

	Tra ca ma chua bao gio duoc dem (uu tien cao nhat) lan ma da qua chu ky.
	"""
	_duoc_dem()
	if not kho:
		frappe.throw("Chưa chọn kho.")
	gioi_han = int(gioi_han or MOI_NGAY)
	hom_nay = getdate(nowdate())

	ds = _xep_hang(_ton_theo_kho(kho))
	lan_cuoi = _ngay_dem_gan_nhat(kho)

	den_han = []
	for x in ds:
		ngay = lan_cuoi.get(x["ma"])
		chu_ky = CHU_KY[x["hang"]]
		if ngay is None:
			qua_han = 9999  # chua bao gio dem
		else:
			qua_han = (hom_nay - ngay).days - chu_ky
		if qua_han >= 0:
			x["ngay_dem_cuoi"] = str(ngay) if ngay else ""
			x["qua_han"] = qua_han
			x["chu_ky"] = chu_ky
			den_han.append(x)

	# Qua han lau nhat len truoc; cung muc thi hang dat tien truoc.
	den_han.sort(key=lambda x: (-x["qua_han"], -flt(x.get("gia_tri"))))
	chon = den_han[:gioi_han]
	return {
		"kho": kho,
		"ngay": str(hom_nay),
		"tong_ma_ton": len(ds),
		"tong_den_han": len(den_han),
		"gioi_han": gioi_han,
		"duoc_duyet": 1 if duoc_duyet() else 0,
		"dong": [
			{
				"ma_hang": x["ma"],
				"ten": x.get("ten") or "",
				"nhom": x.get("nhom") or "",
				"dvt": x.get("dvt") or "",
				"hang": x["hang"],
				"ton": flt(x.get("sl")),
				"ngay_dem_cuoi": x.get("ngay_dem_cuoi") or "",
				"qua_han": 0 if x["qua_han"] == 9999 else x["qua_han"],
				"chua_dem_bao_gio": 1 if x["qua_han"] == 9999 else 0,
			}
			for x in chon
		],
	}


@frappe.whitelist()
def tao_phieu_hom_nay(kho=None, gioi_han=None):
	"""Tao san mot Phieu Kiem Ke chua danh sach may chia cho hom nay.

	Nhan vien khong phai tu chon mon: mo app, bam mot nut la co phieu voi
	dung nhung ma den han, di dem roi dien so.
	"""
	_duoc_dem()
	lich = lich_hom_nay(kho, gioi_han)
	if not lich["dong"]:
		return {"ok": 0, "ly_do": "Hôm nay kho này không có mã nào đến hạn đếm."}

	doc = frappe.new_doc("Phieu Kiem Ke")
	doc.ngay_kiem = lich["ngay"]
	doc.kho = kho
	doc.pham_vi = "Tất cả"
	doc.trang_thai = "Đang kiểm"
	doc.nguoi_kiem = frappe.session.user
	doc.ghi_chu = "Máy chia lịch xoay vòng ngày %s" % lich["ngay"]
	for d in lich["dong"]:
		doc.append(
			"items",
			{
				"item_code": d["ma_hang"],
				"item_name": d["ten"],
				"item_group": d["nhom"],
				"dvt": d["dvt"],
				"ton_he_thong": d["ton"],
				"da_dem": 0,
			},
		)
	doc.so_mon = len(doc.items)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "so_mon": doc.so_mon}


@frappe.whitelist()
def phieu_cho_duyet():
	"""Danh sach phieu dang cho quan ly duyet."""
	_duoc_dem()
	return frappe.get_all(
		"Phieu Kiem Ke",
		filters={"trang_thai": "Chờ duyệt"},
		fields=["name", "ngay_kiem", "kho", "nguoi_kiem", "so_mon"],
		order_by="ngay_kiem desc, name desc",
		limit_page_length=100,
	)


# ================================================================ SAP: ba
# nut kiem ke anh Viet duyet 03/09/2026. Phep thuan nam o `kho_sap.py`,
# duoi day chi la phan cham Frappe.

# O them tren phieu va tren dong. Doc dau `kho_sap.py` de biet vi sao.
TRUONG_MOI = {
	"Phieu Kiem Ke": [
		{
			"fieldname": "vgb_chup_luc",
			"label": "Chụp tồn sổ lúc",
			"fieldtype": "Datetime",
			"read_only": 1,
			"description": (
				"Thời điểm máy chụp tồn sổ của các mã trong phiếu. Chênh lệch "
				"đếm ra là chênh lệch so với thời điểm này."
			),
		},
	],
	"Chi Tiet Kiem Ke": [
		{
			"fieldname": "vgb_ly_do_lech",
			"label": "Lý do chênh lệch",
			"fieldtype": "Data",
			"description": "Mã lý do chuẩn, xem danh sách trong vagabond/kho_sap.py.",
		},
	],
}


def _phieu_dang_khoa():
	"""Cac phieu kiem dang khoa ma, kem danh sach ma cua tung phieu."""
	from vagabond import kho_sap

	phieu = frappe.get_all(
		"Phieu Kiem Ke",
		filters={"trang_thai": ["in", list(kho_sap.TRANG_THAI_KHOA)]},
		fields=["name", "kho", "trang_thai", "ngay_kiem"],
		limit_page_length=0,
	)
	if not phieu:
		return []
	hom_nay = getdate(nowdate())
	ten = [p["name"] for p in phieu]
	dong = frappe.get_all(
		"Chi Tiet Kiem Ke",
		filters={"parent": ["in", ten]},
		fields=["parent", "item_code"],
		limit_page_length=0,
	)
	ma_cua = {}
	for d in dong:
		ma_cua.setdefault(d["parent"], []).append(d["item_code"])
	return [
		{
			"phieu": p["name"],
			"kho": p["kho"],
			"trang_thai": p["trang_thai"],
			"ma": ma_cua.get(p["name"]) or [],
			"con_hieu_luc": kho_sap.con_hieu_luc_khoa(
				getdate(p["ngay_kiem"]) if p.get("ngay_kiem") else None, hom_nay
			),
		}
		for p in phieu
	]


def _dong_chung_tu(doc):
	"""Cac dong cua mot chung tu kho, dua ve dang {ma, kho} de doi chieu."""
	ra = []
	for r in doc.get("items") or []:
		kho = []
		for t in ("warehouse", "s_warehouse", "t_warehouse", "source_warehouse"):
			v = r.get(t)
			if v:
				kho.append(v)
		if not kho and doc.get("set_warehouse"):
			kho.append(doc.get("set_warehouse"))
		ra.append({"ma": r.get("item_code"), "kho": kho})
	return ra


def chan_khi_dang_kiem(doc, method=None):
	"""Chan moi chung tu cham vao ma dang duoc kiem tai kho do.

	SAP dong bang so sach khi lap phieu kiem: dem xong ban them ba cai la
	con so chenh lech thanh so cua mot thoi diem khac, ma nguoi ghi so
	chenh lech thi khong con cach nao biet.

	Dat o `before_submit`: luu nhap thi cu cho luu, chi chan dung luc con so
	sap cham vao ton kho. Phieu kiem bo quen qua hai ngay thi het quyen
	khoa - xem `kho_sap.con_hieu_luc_khoa`.
	"""
	from vagabond import kho_sap

	try:
		mo = _phieu_dang_khoa()
		if not mo:
			return
		khoa = kho_sap.khoa_dang_kiem(mo)
		if not khoa:
			return
		vuong = kho_sap.dong_bi_khoa(_dong_chung_tu(doc), khoa)
	except Exception:
		# Hang rao nay KHONG duoc keo do ca he thong: hong thi ghi lai roi cho
		# chung tu di tiep, vi chan nham con te hon khong chan.
		frappe.log_error(frappe.get_traceback(), "kiem_ke: soat khoa dang kiem")
		return
	if not vuong:
		return
	ten = {}
	for v in vuong:
		ten[v["ma"]] = frappe.db.get_value("Item", v["ma"], "item_name") or v["ma"]
	frappe.throw(kho_sap.cau_bi_khoa(vuong, ten))


def _la_quan_ly():
	return bool(VAI_DUYET & set(frappe.get_roles()))


@frappe.whitelist()
def mo_phieu(name):
	"""Mo mot phieu kiem cho app, co CHE TON SO khi dang dem mu.

	Nguoi di dem chi thay so minh dem duoc; quan ly moi thay ca hai cot. Che
	o may chu chu khong chi giau tren man hinh: giau tren man thi mo Desk ra
	van thay, va thoi quen "dem cho khop" hinh thanh tu do.

	Tra ve DUNG khuon cua `frappe.client.get` (co doctype, modified, cac dong
	con nguyen ban ghi) de man hinh giu nguyen duong luu cu, chi khac o cho
	vai o so bi bo trong.
	"""
	from vagabond import kho_sap

	_duoc_dem()
	doc = frappe.get_doc("Phieu Kiem Ke", name)
	quan_ly = _la_quan_ly()
	hien = kho_sap.duoc_thay_ton_so(doc.trang_thai, quan_ly)
	ra = doc.as_dict()
	ra["items"] = kho_sap.che_ton_so(ra.get("items") or [], hien)
	ra["dem_mu"] = 0 if hien else 1
	ra["duoc_duyet"] = 1 if quan_ly else 0
	ra["ly_do_lech"] = kho_sap.LY_DO_LECH
	return ra


@frappe.whitelist()
def ghi_ly_do(name, dong, ly_do=None):
	"""Ghi ly do chenh lech cho MOT dong cua phieu kiem."""
	from vagabond import kho_sap

	_duoc_dem()
	ma = str(ly_do or "").strip()
	if ma and not kho_sap.ly_do_theo_ma(ma):
		frappe.throw("Lý do chênh lệch không nằm trong danh sách chuẩn.")
	cha = frappe.db.get_value("Chi Tiet Kiem Ke", dong, "parent")
	if cha != name:
		frappe.throw("Dòng này không thuộc phiếu đang mở.")
	frappe.db.set_value("Chi Tiet Kiem Ke", dong, "vgb_ly_do_lech", ma)
	frappe.db.commit()
	return {"ok": 1, "ly_do": ma}


def soat_truoc_khi_chot(doc, method=None):
	"""Ghi so chenh lech thi moi dong lech phai co ly do chuan.

	SAP bat khai ly do (reason for movement) khi ghi so chenh lech, vi cuoi
	thang bao cao lech theo ly do moi noi duoc nen sua quy trinh nao. Khong
	bat luc dem, chi bat luc chot: dang dem ma bat khai la vuong tay.
	"""
	from vagabond import kho_sap

	# CHI SOAT O BUOC CUA QUAN LY. Nguoi dem dang dem mu thi khong thay
	# chenh lech, bat ho khai ly do la bat khai cai ho khong nhin thay. Ho
	# chot phieu sang "Cho duyet" nhu cu; quan ly mo ra thay hai cot, khai ly
	# do roi moi ghi so duoc.
	if doc.trang_thai not in ("Đã chốt", "Đã ghi sổ"):
		return
	cu = doc.get_doc_before_save()
	if cu and cu.trang_thai == doc.trang_thai:
		return
	dong = [
		{
			"ma": r.item_code,
			"ten": r.item_name or r.item_code,
			"lech": flt(r.so_luong) - flt(r.ton_he_thong),
			"ly_do": r.get("vgb_ly_do_lech") or "",
		}
		for r in (doc.get("items") or [])
		if cint(r.da_dem)
	]
	kq = kho_sap.soat_ly_do(dong)
	if kq["thieu"]:
		frappe.throw(
			"Những dòng sau lệch so với tồn sổ mà chưa chọn lý do:<br>%s<br><br>"
			"Chọn lý do rồi chốt lại. Cuối tháng đọc báo cáo lệch theo lý do là "
			"biết nên sửa chỗ nào trong quy trình." % "<br>".join(kq["thieu"][:12])
		)
	if kq["nguoc"]:
		frappe.throw(
			"Lý do chọn ngược chiều với chênh lệch:<br>%s<br><br>Thiếu hàng thì "
			"chọn lý do của bên thiếu, thừa hàng thì chọn lý do của bên thừa."
			% "<br>".join(kq["nguoc"][:12])
		)


def chup_ton_so(doc, method=None):
	"""Ghi lai thoi diem chup ton so cua phieu kiem, mot lan luc phieu sinh ra."""
	if doc.get("vgb_chup_luc"):
		return
	try:
		doc.db_set("vgb_chup_luc", frappe.utils.now(), update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "kiem_ke: chup ton so")


@frappe.whitelist()
def ly_do_ds():
	"""Danh sach ly do chenh lech chuan cho man hinh."""
	from vagabond import kho_sap

	_duoc_dem()
	return {"ly_do": kho_sap.LY_DO_LECH, "can_duyet": sorted(kho_sap.LY_DO_CAN_DUYET)}


@frappe.whitelist()
def phieu_dang_khoa():
	"""Cac phieu kiem dang khoa ma, cho man Cai dat va man kiem ke soi."""
	_duoc_dem()
	return _phieu_dang_khoa()
