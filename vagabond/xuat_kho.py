"""Xuat kho: xuat huy va xuat dieu chuyen noi bo (anh Viet dat ngay 03/08/2026).

Hai nghiep vu, hai luat khac nhau vi rui ro khac nhau:

1. XUAT HUY - hang roi khoi cong ty, gia tri mat that. Nhan vien chi TAO
   phieu nhap (ban nhap) kem ly do va anh chup; phai quan ly kho bam Ghi so
   thi ton moi tru. Giong nguyen tac anh Viet chot cho kiem ke: nguoi dem va
   nguoi ghi so khong duoc la mot.

2. XUAT DIEU CHUYEN NOI BO - hang chi doi kho, tong tai san khong doi, va kho
   nhan con phai dem lai luc nhan. Nen cho ghi so ngay de bep khong phai cho
   quan ly moi giao duoc banh.

Ca hai deu de xuong Stock Entry chuan cua ERPNext (Material Issue /
Material Transfer) chu khong de ra doctype rieng, de bao cao ton kho, gia von
va so ke toan cua ERPNext van dung nguyen.
"""

import json

import frappe
from frappe.utils import cint, flt, nowdate

from vagabond import chung_tu

# Ai duoc tao phieu xuat.
VAI_XUAT = {
	"System Manager",
	"Stock Manager",
	"Stock User",
	"Kiểm kê viên",
	"Bộ phận đặt hàng",
	"Manufacturing User",
}

# Ai duoc ghi so phieu xuat huy.
VAI_DUYET = {"System Manager", "Stock Manager"}

# Ly do huy - de o day de sua mot cho la app doi theo.
LY_DO_HUY = [
	"Hỏng, vỡ trong quá trình làm",
	"Hết hạn sử dụng",
	"Không đạt chất lượng",
	"Mẫu thử, nếm, chụp hình",
	"Bánh trưng bày hết ngày",
	"Thất thoát chưa rõ nguyên nhân",
	"Khác",
]

LOAI = {
	"huy": "Material Issue",
	"chuyen": "Material Transfer",
}


def _duoc_xuat():
	if not VAI_XUAT & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền xuất kho.")


def duoc_duyet():
	return bool(VAI_DUYET & set(frappe.get_roles()))


def _cong_ty():
	"""Cong ty dang dung, uu tien cong ty mac dinh cua phien lam viec."""
	ten = frappe.defaults.get_user_default("Company")
	if ten:
		return ten
	ds = frappe.get_all("Company", pluck="name", limit_page_length=2)
	return ds[0] if ds else None


def _kho_that(cong_ty):
	"""Kho la vi tri that (khong phai nhom), thuoc cong ty dang dung."""
	return frappe.get_all(
		"Warehouse",
		filters={"is_group": 0, "disabled": 0, "company": cong_ty},
		fields=["name", "warehouse_name"],
		order_by="name",
		limit_page_length=0,
	)


@frappe.whitelist()
def khoi_dong():
	"""Moi thu app can de mo man xuat kho, goi mot lan.

	Gom vao mot endpoint vi vai Kiem ke vien / Shipper khong co quyen doc
	Warehouse qua API chuan - bai hoc tu vu app shipper treo dong ho cat.
	"""
	_duoc_xuat()
	ct = _cong_ty()
	return {
		"cong_ty": ct,
		"kho": _kho_that(ct),
		"ly_do": LY_DO_HUY,
		"duoc_duyet": 1 if duoc_duyet() else 0,
		"toi": frappe.session.user,
	}


@frappe.whitelist()
def tim_hang(kho=None, tu_khoa=None, gioi_han=60):
	"""Cac ma dang CON TON trong kho do, loc theo tu khoa.

	Chi liet ke ma con ton that: xuat mon khong co ton la chac chan sai, chan
	tu day cho nhan vien khoi mat cong dien roi bi bao loi luc ghi so.
	"""
	_duoc_xuat()
	if not kho:
		return []
	tu_khoa = (tu_khoa or "").strip()
	dieu_kien = ""
	tham_so = {"kho": kho, "gh": int(gioi_han or 60)}
	if tu_khoa:
		dieu_kien = " and (b.item_code like %(q)s or i.item_name like %(q)s)"
		tham_so["q"] = "%" + tu_khoa + "%"
	return frappe.db.sql(
		"""
		select b.item_code as ma, i.item_name as ten, i.item_group as nhom,
		       i.stock_uom as dvt, b.actual_qty as ton,
		       b.stock_value / nullif(b.actual_qty, 0) as gia_von
		from `tabBin` b
		join `tabItem` i on i.name = b.item_code
		where b.warehouse = %(kho)s and b.actual_qty > 0 and i.disabled = 0
		"""
		+ dieu_kien
		+ """
		order by i.item_name
		limit %(gh)s
		""",
		tham_so,
		as_dict=True,
	)


def _doc_dong(dong):
	"""Doc danh sach dong tu app, chan cac loi de thay truoc khi ghi so."""
	if isinstance(dong, str):
		dong = json.loads(dong or "[]")
	sach = []
	for d in dong or []:
		ma = (d.get("ma") or d.get("item_code") or "").strip()
		sl = flt(d.get("sl") or d.get("qty"))
		if not ma or sl <= 0:
			continue
		sach.append({"ma": ma, "sl": sl, "ghi_chu": (d.get("ghi_chu") or "").strip()})
	if not sach:
		frappe.throw("Phiếu chưa có dòng hàng nào có số lượng lớn hơn 0.")
	return sach


def _chan_qua_ton(kho, sach):
	"""Khong cho xuat qua ton dang co - he thong dang chan ton am."""
	thieu = []
	for d in sach:
		ton = flt(
			frappe.db.get_value("Bin", {"item_code": d["ma"], "warehouse": kho}, "actual_qty")
		)
		if d["sl"] > ton:
			thieu.append("%s (tồn %s, xuất %s)" % (d["ma"], ton, d["sl"]))
	if thieu:
		frappe.throw("Số lượng xuất vượt quá tồn kho: " + "; ".join(thieu))


def _phieu_moi(loai, cong_ty):
	doc = frappe.new_doc("Stock Entry")
	doc.stock_entry_type = LOAI[loai]
	doc.purpose = LOAI[loai]
	doc.company = cong_ty
	doc.posting_date = nowdate()
	doc.set_posting_time = 0
	return doc


# Uu tien tai khoan nao khi ghi gia tri hang huy. Theo che do ke toan Viet Nam,
# hao hut trong dinh muc tinh vao gia von hang ban (632); ngoai dinh muc thi
# ke toan chuyen tay sang 811. Dat 632 lam mac dinh cho dung ban chat nhat.
UU_TIEN_TK = ("632", "811", "6278", "642")


def _tk_chi_phi(cong_ty):
	"""Tai khoan ghi gia tri hang huy.

	KHONG duoc lay tai khoan mac dinh cua cong ty: cau hinh hien tai dang tro
	'TK chenh lech' vao 152 (tai khoan loai kho), ERPNext chan thang - bao
	'TK chenh lech khong duoc la TK loai kho'. Nen phai tu chon mot tai khoan
	chi phi that.
	"""
	ds = frappe.get_all(
		"Account",
		filters={
			"company": cong_ty,
			"is_group": 0,
			"root_type": "Expense",
			"account_type": ["not in", ["Stock", "Stock Adjustment"]],
		},
		fields=["name", "account_number"],
		limit_page_length=0,
	)
	for so in UU_TIEN_TK:
		for a in ds:
			if (a.get("account_number") or "").startswith(so) or a["name"].startswith(so):
				return a["name"]
	if ds:
		return ds[0]["name"]
	frappe.throw("Chưa có tài khoản chi phí nào để ghi giá trị hàng huỷ, nhờ kế toán khai thêm.")


@frappe.whitelist()
def luu_xuat_huy(kho=None, ly_do=None, ghi_chu=None, dong=None, anh=None):
	"""Tao phieu xuat huy o dang BAN NHAP, cho quan ly kho ghi so.

	Nguoi tao khong tu ghi so duoc, ke ca khi ho co quyen: muon ghi so thi
	vao lai phieu bam Ghi so, de con luu ai la nguoi duyet.
	"""
	_duoc_xuat()
	if not kho:
		frappe.throw("Chưa chọn kho xuất.")
	if not ly_do:
		frappe.throw("Chưa chọn lý do huỷ.")
	sach = _doc_dong(dong)
	_chan_qua_ton(kho, sach)

	ct = _cong_ty()
	doc = _phieu_moi("huy", ct)
	doc.from_warehouse = kho
	doc.vgb_ly_do_huy = ly_do
	if anh:
		doc.vgb_anh_xuat = anh
	doc.remarks = "Xuất huỷ - %s%s" % (ly_do, (". " + ghi_chu) if ghi_chu else "")
	tk = _tk_chi_phi(ct)
	for d in sach:
		doc.append(
			"items",
			{
				"item_code": d["ma"],
				"qty": d["sl"],
				"s_warehouse": kho,
				"expense_account": tk,
			},
		)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Chờ ghi sổ"}


@frappe.whitelist()
def ghi_so_xuat_huy(name=None):
	"""Quan ly kho ghi so phieu huy - toi day ton moi thuc su tru."""
	if not duoc_duyet():
		frappe.throw("Chỉ quản lý kho mới được ghi sổ phiếu xuất huỷ.")
	doc = frappe.get_doc("Stock Entry", name)
	if doc.docstatus != 0:
		frappe.throw("Phiếu này không còn ở trạng thái bản nháp.")
	if doc.purpose != LOAI["huy"]:
		frappe.throw("Phiếu này không phải phiếu xuất huỷ.")
	if cint(doc.get("vgb_huy")):
		frappe.throw(
			"Phiếu này đã bỏ nên không ghi sổ được. Lý do: %s. Muốn dùng lại thì "
			"báo kế toán gỡ dấu huỷ, hoặc lập phiếu mới."
			% (doc.get("vgb_huy_ly_do") or "không ghi")
		)
	doc.flags.ignore_permissions = True
	doc.submit()
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Đã ghi sổ"}


@frappe.whitelist()
def xoa_ban_nhap(name=None, ly_do=None):
	"""Bo mot phieu nhap dang sai - chi nguoi tao hoac quan ly kho.

	Ten ham giu nguyen cho app cu con goi duoc, nhung tu 11/08/2026 khong
	xoa nua ma danh dau da huy: khong chung tu nao trong he thong nay duoc
	xoa vinh vien, phieu kho cung the.
	"""
	_duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	if doc.docstatus != 0:
		frappe.throw("Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính.")
	if doc.owner != frappe.session.user and not duoc_duyet():
		frappe.throw("Chỉ người tạo phiếu hoặc quản lý kho mới bỏ được phiếu này.")
	if cint(doc.get("vgb_huy") or 0):
		return {"ok": 1, "da_huy_tu_truoc": 1}
	chung_tu.danh_dau_huy(doc, ly_do or "Bỏ phiếu nháp sai")
	return {"ok": 1, "da_huy": 1}


@frappe.whitelist()
def luu_dieu_chuyen(kho_xuat=None, kho_nhan=None, ghi_chu=None, dong=None, yeu_cau=None):
	"""Chuyen hang giua hai kho noi bo, ghi so ngay.

	Ghi so ngay vi tong tai san khong doi va kho nhan con dem lai luc nhan.
	Neu sau nay anh Viet chot luong hai buoc co kho Hang dang di duong thi
	sua o day, app khong phai doi.
	"""
	_duoc_xuat()
	if not kho_xuat or not kho_nhan:
		frappe.throw("Phải chọn cả kho xuất và kho nhận.")
	if kho_xuat == kho_nhan:
		frappe.throw("Kho xuất và kho nhận không được trùng nhau.")
	sach = _doc_dong(dong)
	_chan_qua_ton(kho_xuat, sach)

	ct = _cong_ty()
	doc = _phieu_moi("chuyen", ct)
	doc.from_warehouse = kho_xuat
	doc.to_warehouse = kho_nhan
	doc.remarks = "Điều chuyển nội bộ%s" % ((". " + ghi_chu) if ghi_chu else "")
	# Phieu chuyen kho khong ghi chi phi, nhung ERPNext van kiem tra o "TK chenh
	# lech" cua tung dong nen van phai dien mot tai khoan chi phi that.
	tk = _tk_chi_phi(ct)
	for d in sach:
		hang = {
			"item_code": d["ma"],
			"qty": d["sl"],
			"s_warehouse": kho_xuat,
			"t_warehouse": kho_nhan,
			"expense_account": tk,
		}
		if yeu_cau:
			hang["material_request"] = yeu_cau
		doc.append("items", hang)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Đã ghi sổ"}


@frappe.whitelist()
def yeu_cau_cho_chuyen(kho_xuat=None):
	"""Cac phieu Dat hang noi bo dang cho kho nay giao.

	De kho xuat mo man dieu chuyen la thay ngay ai dang xin hang, khoi phai
	nho, va so lieu dien san theo phieu.
	"""
	_duoc_xuat()
	dieu_kien = {
		"material_request_type": "Material Transfer",
		"docstatus": 1,
		"status": ["in", ["Pending", "Partially Ordered"]],
	}
	if kho_xuat:
		dieu_kien["set_from_warehouse"] = kho_xuat
	return frappe.get_all(
		"Material Request",
		filters=dieu_kien,
		fields=["name", "transaction_date", "schedule_date", "set_warehouse", "status"],
		order_by="transaction_date desc",
		limit_page_length=30,
	)


@frappe.whitelist()
def dong_cua_yeu_cau(name=None):
	"""Cac dong con thieu cua mot phieu Dat hang noi bo."""
	_duoc_xuat()
	doc = frappe.get_doc("Material Request", name)
	ra = []
	for d in doc.items:
		con = flt(d.qty) - flt(d.ordered_qty)
		if con <= 0:
			continue
		ra.append(
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"sl": con,
				"kho_nhan": d.warehouse,
			}
		)
	return {
		"name": doc.name,
		"kho_xuat": doc.set_from_warehouse,
		"kho_nhan": doc.set_warehouse,
		"dong": ra,
	}


@frappe.whitelist()
def ds_phieu(loai="huy", gioi_han=40):
	"""Danh sach phieu xuat gan day, kem so dong va tong tien."""
	_duoc_xuat()
	if loai not in LOAI:
		frappe.throw("Loại phiếu không hợp lệ.")
	ds = frappe.get_all(
		"Stock Entry",
		# vgb_huy 0: phieu da bo phai loai o DAY, truoc khi cat 40 dong. Loc
		# sau khi cat thi phieu bo chiem cho, day phieu that ra ngoai danh
		# sach - bai hoc cu cua du an, khong duoc lap lai.
		filters={"purpose": LOAI[loai], "docstatus": ["<", 2], "vgb_huy": 0},
		fields=[
			"name",
			"posting_date",
			"docstatus",
			"from_warehouse",
			"to_warehouse",
			"total_outgoing_value",
			"owner",
			"remarks",
			"vgb_huy",
			"vgb_huy_ly_do",
		],
		order_by="creation desc",
		limit_page_length=int(gioi_han or 40),
	)
	ten = {}
	for u in {d.owner for d in ds}:
		ten[u] = frappe.db.get_value("User", u, "full_name") or u
	for d in ds:
		d["nguoi_tao"] = ten.get(d.owner, d.owner)
		d["trang_thai"] = "Chờ ghi sổ" if d.docstatus == 0 else "Đã ghi sổ"
		d["so_dong"] = frappe.db.count("Stock Entry Detail", {"parent": d.name})
	return ds


@frappe.whitelist()
def chi_tiet(name=None):
	"""Mot phieu xuat kem cac dong hang."""
	_duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	return {
		"name": doc.name,
		"ngay": str(doc.posting_date),
		"docstatus": doc.docstatus,
		"trang_thai": (
			"Đã bỏ"
			if cint(doc.get("vgb_huy"))
			else ("Chờ ghi sổ" if doc.docstatus == 0 else "Đã ghi sổ")
		),
		"vgb_huy": cint(doc.get("vgb_huy")),
		"vgb_huy_ly_do": doc.get("vgb_huy_ly_do") or "",
		"vgb_huy_boi": doc.get("vgb_huy_boi") or "",
		"loai": doc.purpose,
		"kho_xuat": doc.from_warehouse,
		"kho_nhan": doc.to_warehouse,
		"ly_do": doc.get("vgb_ly_do_huy") or "",
		"anh": doc.get("vgb_anh_xuat") or "",
		"ghi_chu": doc.remarks or "",
		"nguoi_tao": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"tong_tien": flt(doc.total_outgoing_value),
		"duoc_duyet": 1 if duoc_duyet() else 0,
		"la_cua_toi": 1 if doc.owner == frappe.session.user else 0,
		"dong": [
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"sl": flt(d.qty),
				"tien": flt(d.amount),
				"kho_xuat": d.s_warehouse,
				"kho_nhan": d.t_warehouse,
			}
			for d in doc.items
		],
	}
