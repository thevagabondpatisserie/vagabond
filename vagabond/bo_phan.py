"""Cay bo phan (Cost Center) cua tiem - anh Viet chot 02/09/2026.

Vi sao phai co
--------------
Toi truoc hom nay ERPNext cua tiem co DUNG MOT trung tam chi phi la
`Main - TV`. Nghia la moi dong chi phi deu roi vao chung mot cho, va cau
hoi "thang nay Marketing tieu bao nhieu tien banh de chup anh" khong co
cach nao tra loi.

Ca cu that: banh cho Marketing chup anh dang phai lap phieu XUAT HUY voi
ly do "Mau thu, nem, chup hinh". Gia tri to banh do vao thang tai khoan
hao hut, va cuoi thang nhin bao cao thi Bep la ben lam hong nhieu. Do la
do oan, va no do oan mot cach co he thong.

Cay nay la dieu kien de man Xuat dung noi bo ghi duoc bo phan chiu chi phi.

Nguyen tac
----------
1. CHI THEM, khong bao gio sua va khong bao gio xoa. Trung tam chi phi da
   dung trong chung tu thi ERPNext khong cho xoa nua, va cung khong nen:
   xoa la lam mo coi moi but toan da tro toi no.
2. Dat duoi trung tam chi phi GOC cua cong ty, khong dat duoi `Main - TV`.
   `Main` la mot la binh thuong do ERPNext sinh ra luc lap cong ty, nhet
   ca cay vao duoi no la sai hinh.
3. Ten trong ERPNext luon la "<ten> - <viet tat cong ty>". Ma nguon chi
   giu phan ten, phan duoi do ham `ten_that` ghep vao, de doi cong ty hay
   doi viet tat thi khong phai sua ca file.

Cay nay bam theo 16 phong ban da co trong tai lieu master data ngay 12/08.
Chua co bo phan nao thi them mot dong vao CAY duoi day, deploy lai la may
tu dung, khong phai bam tay tren Desk.
"""

import frappe

# Cay bo phan. Moi phan tu: (ten nhom, [cac bo phan la trong nhom do]).
#
# Giu dung THU TU nay khi hien tren app: nguoi dung doc theo khoi chu khong
# doc theo van chu cai.
CAY = (
	(
		"Khối sản xuất",
		("Bếp Baker", "Bếp Pastry", "Sonneto Lab"),
	),
	(
		"Khối kinh doanh",
		(
			"Cửa hàng D1",
			"Cửa hàng NVHTN",
			"Sales và bán sỉ",
			"Marketing",
			"Giao hàng",
		),
	),
	(
		"Khối hỗ trợ",
		("Ban Giám đốc", "Kế toán", "Thu mua", "Kho"),
	),
)


# ------------------------------------------------------------- phần thuần


def ten_that(ten, viet_tat):
	"""Ten day du cua mot trung tam chi phi trong ERPNext. Ham THUAN.

	ERPNext luon dat ten trung tam chi phi la "<ten> - <viet tat cong ty>".
	Thieu duoi thi moi phep tra cuu deu truot, ma truot thi ham dung() lai
	tuong la chua co roi tao them mot cai nua.
	"""
	ten = (ten or "").strip()
	viet_tat = (viet_tat or "").strip()
	if not ten:
		return ""
	if not viet_tat:
		return ten
	if ten.endswith(" - %s" % viet_tat):
		return ten
	return "%s - %s" % (ten, viet_tat)


def cac_nhom():
	"""Ten cac nhom trong cay, theo dung thu tu. Ham THUAN."""
	return [nhom for nhom, _ in CAY]


def cac_la():
	"""Ten moi bo phan la, theo dung thu tu trong cay. Ham THUAN."""
	ra = []
	for _, la in CAY:
		ra.extend(la)
	return ra


def nhom_cua(bo_phan):
	"""Bo phan nay thuoc khoi nao. Ham THUAN. Khong biet thi tra None."""
	bo_phan = (bo_phan or "").strip()
	if not bo_phan:
		return None
	for nhom, la in CAY:
		if bo_phan in la:
			return nhom
	return None


def la_bo_phan_hop_le(bo_phan):
	"""Chuoi nay co phai mot bo phan LA trong cay khong. Ham THUAN.

	Chi la moi hop le. Nhom la cho de xep, khong ai chiu chi phi ca: gan
	chi phi vao mot nhom la ERPNext bao loi "khong ghi vao trung tam chi
	phi nhom duoc", ma loi do bung ra luc ghi so chu khong luc go.
	"""
	return (bo_phan or "").strip() in set(cac_la())


def khong_trung():
	"""Trong ca cay khong co hai ten giong nhau. Ham THUAN.

	Trung ten la hong that su: ERPNext lay ten lam khoa chinh, hai bo phan
	cung ten thi cai sau de len cai truoc va cay mat mot nhanh.
	"""
	het = cac_nhom() + cac_la()
	return len(het) == len(set(het))


# ------------------------------------------------ phần chạm Frappe


def _cong_ty():
	"""Cong ty dang dung, uu tien cong ty mac dinh cua phien lam viec."""
	ten = frappe.defaults.get_user_default("Company")
	if ten:
		return ten
	ds = frappe.get_all("Company", pluck="name", limit_page_length=2)
	return ds[0] if ds else None


def _goc(cong_ty):
	"""Trung tam chi phi GOC cua cong ty - cai khong co cha.

	Khong doan theo ten: moi ban ERPNext dat ten goc mot kieu. Tim theo
	dung dinh nghia la nhom va khong co cha.
	"""
	ds = frappe.get_all(
		"Cost Center",
		filters={"company": cong_ty, "is_group": 1, "parent_cost_center": ["in", ["", None]]},
		pluck="name",
		limit_page_length=2,
	)
	return ds[0] if ds else None


def dung():
	"""Dung cay bo phan. Goi tu after_migrate, chay lai bao nhieu lan cung duoc.

	Cai gi da co thi BO QUA, khong dung toi. Chay ham nay khong bao gio lam
	mat mot trung tam chi phi nao dang co, ke ca `Main - TV`.
	"""
	cong_ty = _cong_ty()
	if not cong_ty:
		return {"ok": 0, "vi_sao": "Chưa có công ty nào."}
	viet_tat = frappe.db.get_value("Company", cong_ty, "abbr") or ""
	goc = _goc(cong_ty)
	if not goc:
		return {"ok": 0, "vi_sao": "Chưa tìm thấy trung tâm chi phí gốc."}

	them = []
	for nhom, cac_la_trong_nhom in CAY:
		cha = ten_that(nhom, viet_tat)
		moi = _tao_mot(nhom, goc, cong_ty, viet_tat, la_nhom=1)
		if moi:
			them.append(moi)
		# KHONG duoc `continue` khi nhom da co. Lan deploy thu hai tro di
		# nhom nao cung da co, `_tao_mot` tra None, ma bo qua o day thi moi
		# bo phan la khong bao gio duoc dung. Da viet nham dung mot lan.
		if not frappe.db.exists("Cost Center", cha):
			continue
		for bp in cac_la_trong_nhom:
			moi = _tao_mot(bp, cha, cong_ty, viet_tat, la_nhom=0)
			if moi:
				them.append(moi)
	frappe.db.commit()
	return {"ok": 1, "them": them}


def _tao_mot(ten, cha, cong_ty, viet_tat, la_nhom=0):
	"""Tao mot trung tam chi phi neu chua co. Tra ve ten neu VUA tao.

	Hong mot bo phan khong duoc keo do ca lan deploy: bat ngoai le, ghi
	nhat ky, roi di tiep. Cay thieu mot nhanh thi lan deploy sau bu duoc,
	con deploy hong thi ca tiem dung.
	"""
	day_du = ten_that(ten, viet_tat)
	if frappe.db.exists("Cost Center", day_du):
		return None
	try:
		doc = frappe.new_doc("Cost Center")
		doc.cost_center_name = ten
		doc.parent_cost_center = cha
		doc.company = cong_ty
		doc.is_group = 1 if la_nhom else 0
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "bo_phan: tạo %s" % day_du)
		return None


@frappe.whitelist()
def danh_sach():
	"""Cac bo phan LA de app do vao o chon, xep theo khoi.

	Chi tra ve la: nhom khong nhan chi phi duoc. Bo phan nao chua duoc dung
	trong ERPNext thi khong hien, de nguoi dung khong chon phai mot cai ma
	luc ghi so may moi bao la khong ton tai.
	"""
	cong_ty = _cong_ty()
	viet_tat = frappe.db.get_value("Company", cong_ty, "abbr") or "" if cong_ty else ""
	co = set(
		frappe.get_all(
			"Cost Center",
			filters={"company": cong_ty, "is_group": 0, "disabled": 0},
			pluck="name",
			limit_page_length=0,
		)
	)
	ra = []
	for nhom, cac_la_trong_nhom in CAY:
		muc = []
		for bp in cac_la_trong_nhom:
			day_du = ten_that(bp, viet_tat)
			if day_du in co:
				muc.append({"ten": bp, "ma": day_du})
		if muc:
			ra.append({"nhom": nhom, "bo_phan": muc})
	return {"cong_ty": cong_ty, "khoi": ra}
