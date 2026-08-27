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
import re
import unicodedata

import frappe
from frappe.utils import add_days, cint, flt, nowdate

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


# Bao nhieu ma keo ve mot luot truoc khi loc trong Python. Kho cua tiem
# khong bao gio co toi ngan nay ma con ton, nen day la luoi chan cho truong
# hop bat thuong chu khong phai muc cat binh thuong.
TRAN_KEO = 4000


def _bo_dau(t):
	"""Bo dau tieng Viet va ha thuong. Ham THUAN, kiem thu duoc khong can site."""
	t = unicodedata.normalize("NFD", str(t or ""))
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("\u0111", "d").replace("\u0110", "d").lower()


def _khop(hang, tu):
	"""Mot dong co khop het cac tu da go khong.

	Moi TU phai co mat, o ma hoac o ten, khong can dung thu tu. Nho vay
	"o roman" tim ra "Banh O Roman De La Rose", ma "roman o" cung ra.

	So bang ban DA BO DAU ca hai phia. Ly do that: kho hang go tren may tinh
	o quay thuong go khong dau, ma phep `like` cua co so du lieu thi "banh o"
	KHONG khop "Bánh Ổ" - hai chuoi do khac nhau tung ky tu. Sales go "banh
	o" ra rong, nhin danh sach mac dinh khong thay banh o dau, va ket luan
	la he thong thieu ma.
	"""
	kho_chu = _bo_dau(hang.get("ma")) + " " + _bo_dau(hang.get("ten"))
	return all(_co_tu(kho_chu, t) for t in tu)


def _co_tu(kho_chu, t):
	"""Mot tu da go co nam trong chuoi khong.

	TU NGAN PHAI DUNG DAU MOT TIENG, khong duoc nam giua long tu khac. Neu
	khong thi go "banh o" se ra ca "Banh Croissant Avocado" - chu "o" nam
	trong "croissant" - va danh sach loc ra y het danh sach chua loc, tuc la
	o tim khong lam gi ca. Da vap dung cai nay khi viet ham nay.

	Tu tu ba ky tu tro len thi cho khop o bat ky dau, de con go duoc mot
	manh giua ma hang nhu "wc000".
	"""
	if len(t) >= 3:
		return t in kho_chu
	return re.search(r"(?<![a-z0-9])" + re.escape(t), kho_chu) is not None


def _diem_khop(hang, tu_khoa_sach):
	"""Do gan: khop cang sat cang dung truoc. So NHO la dung truoc.

	Vi sao phai xep hang thay vi cu theo van chu cai: danh sach bi cat bot o
	`gioi_han`, nen thu tu quyet dinh cai gi bi cat. Xep theo van chu cai ma
	cat thi ma go dung y het van co the bi cat mat, con mot ma chi trung mot
	chu lai duoc giu.
	"""
	ma = _bo_dau(hang.get("ma"))
	ten = _bo_dau(hang.get("ten"))
	if not tu_khoa_sach:
		return 9
	if ma == tu_khoa_sach or ten == tu_khoa_sach:
		return 0
	if ma.startswith(tu_khoa_sach):
		return 1
	if ten.startswith(tu_khoa_sach):
		return 2
	if tu_khoa_sach in ma:
		return 3
	return 4


@frappe.whitelist()
def tim_hang(kho=None, tu_khoa=None, gioi_han=200):
	"""Cac ma dang CON TON trong kho do, loc theo tu khoa.

	Chi liet ke ma con ton that: xuat mon khong co ton la chac chan sai, chan
	tu day cho nhan vien khoi mat cong dien roi bi bao loi luc ghi so.

	BA CHO DA SUA NGAY 26/08/2026, sau khi Sales bao *"ben xuat huy dang bi
	thieu ma cac san pham nhu banh o, banh nuong"*:

	  1. TRAN CU LA 60 DONG, XEP THEO VAN CHU CAI. Kho banh cua tiem co hon
	     sau chuc ma con ton, va ten ma nao cung bat dau bang chu "Banh".
	     Sau chuc dong dau tien la het sach Croissant, con Banh O va Banh
	     Nuong nam qua khoi vach cat nen khong bao gio hien ra. Khong phai
	     thieu ma, ma la bi cat. Nay tran la 200 va man hinh noi ro khi
	     danh sach bi cat.
	  2. TIM CO PHAN BIET DAU. Phep `like` cua co so du lieu coi "banh o" va
	     "Bánh Ổ" la hai chuoi khac nhau. Nay so bang ban da bo dau ca hai
	     phia, va tach tung tu nen khong can go dung thu tu.
	  3. XEP HANG. Danh sach bi cat thi thu tu quyet dinh cai gi bi cat, nen
	     ma khop sat nhat phai dung truoc.

	Loc trong Python chu khong trong cau lenh SQL vi phep bo dau tieng Viet
	khong co san trong co so du lieu, va vi so ma con ton trong mot kho la
	con so nho - vai tram - nen keo ve roi loc la re.
	"""
	_duoc_xuat()
	if not kho:
		return []
	tu_khoa = (tu_khoa or "").strip()
	tho = frappe.db.sql(
		"""
		select b.item_code as ma, i.item_name as ten, i.item_group as nhom,
		       i.stock_uom as dvt, b.actual_qty as ton,
		       b.stock_value / nullif(b.actual_qty, 0) as gia_von
		from `tabBin` b
		join `tabItem` i on i.name = b.item_code
		where b.warehouse = %(kho)s and b.actual_qty > 0 and i.disabled = 0
		order by i.item_name
		limit %(tran)s
		""",
		{"kho": kho, "tran": TRAN_KEO},
		as_dict=True,
	)
	return loc_va_xep(tho, tu_khoa, gioi_han)


def loc_va_xep(tho, tu_khoa, gioi_han=200):
	"""Phep THUAN: vao la danh sach dong, ra la danh sach da loc va xep.

	Tach rieng khoi `tim_hang` de bo kiem thu tang khung do duoc ma khong
	can co so du lieu - dung cach ca repo nay van lam.
	"""
	sach = _bo_dau(tu_khoa)
	tu = [t for t in sach.split() if t]
	ra = [d for d in tho if not tu or _khop(d, tu)]
	ra.sort(key=lambda d: (_diem_khop(d, sach), str(d.get("ten") or "")))
	gh = int(gioi_han or 200)
	return ra[:gh] if gh > 0 else ra


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
def go_anh_xuat_huy(name=None):
	"""Go anh dinh nham khoi phieu xuat huy con ban nhap. KHONG xoa tep.

	Anh Viet 24/08/2026 yeu cau moi hinh thu nho phai co nut X. Man nay
	truoc do khong go duoc: chup nham mot tam la phai bo ca phieu lam lai.

	Khac hai cua go ben ho so thanh toan mot cho: anh o day khong phai tep
	dinh kem ma la mot duong dan nam trong o `vgb_anh_xuat`. Nen "go" o day
	la xoa duong dan trong o, con tep van nam nguyen trong Trinh quan ly tep
	- van dung tinh than khong xoa chung tu (QT-20).

	Chi go duoc khi phieu CHUA ghi so. Ghi so roi thi ton kho da tru that va
	tam anh la can cu cua lan tru do.
	"""
	_duoc_xuat()
	if not name or not frappe.db.exists("Stock Entry", name):
		frappe.throw("Không tìm thấy phiếu %s." % (name or "(trống)"))
	d = frappe.db.get_value(
		"Stock Entry", name, ["docstatus", "vgb_huy", "vgb_anh_xuat"], as_dict=True
	)
	if cint(d.get("docstatus")) != 0:
		frappe.throw(
			"Phiếu %s đã ghi sổ nên không gỡ ảnh ra được nữa. Tồn kho đã trừ thật, "
			"và tấm ảnh là căn cứ của lần trừ đó." % name
		)
	if cint(d.get("vgb_huy")):
		frappe.throw("Phiếu %s đã bị bỏ, không sửa được nữa." % name)
	if not (d.get("vgb_anh_xuat") or "").strip():
		frappe.throw("Phiếu %s chưa có ảnh nào để gỡ." % name)
	frappe.db.set_value("Stock Entry", name, "vgb_anh_xuat", None, update_modified=False)
	try:
		frappe.get_doc("Stock Entry", name).add_comment("Comment", "Gỡ ảnh xuất huỷ khỏi phiếu.")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "xuat_kho: ghi vet go anh")
	frappe.db.commit()
	return {"ok": 1, "name": name}


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


# ===================================================================
# HANG CHUYEN VE KHO MINH (anh Viet 18/08/2026)
# ===================================================================
#
# Anh Viet: "cac ban nhan su Bep (Hieu baker, Han bep pho...) dang bi nghen
# o khau nhan hang".
#
# Doc lai luong thi thay khong ai chan ho ca. Cai thieu la mot cho DE NHIN:
# phieu dieu chuyen o he nay ghi so MOT BUOC ben kho xuat (xem luu_dieu_chuyen
# tren kia), nen hang vao kho bep ngay lap tuc ma ben bep khong co man nao
# thay no da ve, ve luc nao, ai chuyen, gom nhung gi.
#
# Man nay lap dung cho trong do. No CHI DOC, khong sinh chung tu nao: buoc
# "xac nhan da nhan" va xu ly nhan thieu (chenh lech sinh but toan hao hut)
# la viec dung vao gia von, phai cho anh Viet duyet phuong an truoc.


def _gio_hhmm(v):
	"""Gio dang HH:MM. posting_time cua Frappe la timedelta hoac "9:33:00",
	cat cung 5 ky tu thi ra "9:33:" - thua mot dau hai cham."""
	t = str(v or "").strip()
	if not t:
		return ""
	p = t.split(":")
	if len(p) < 2:
		return t[:5]
	return "%02d:%02d" % (cint(p[0]), cint(p[1]))


def _kho_phu_trach(nguoi=None):
	"""Cac kho nguoi nay phu trach, doc tu o Kho phu trach tren User."""
	nguoi = nguoi or frappe.session.user
	tho = frappe.db.get_value("User", nguoi, "custom_kho_phu_trach") or ""
	return [x.strip() for x in str(tho).split(",") if x.strip()]


@frappe.whitelist()
def hang_chuyen_ve(so_ngay=14, kho=None):
	"""Cac phieu dieu chuyen da ghi so co kho NHAN la kho minh phu trach.

	Tra ve kem so dong va tong so luong de nhin phat biet phieu to hay nho,
	khong phai mo tung cai.
	"""
	so_ngay = max(1, min(cint(so_ngay) or 14, 90))
	cua_toi = _kho_phu_trach()
	# Chua khai kho phu trach thi KHONG duoc truyen kho tuy y. Bo qua cho
	# nay la ai chua khai cung xem duoc moi kho, tuc la man khoa nguoc: nguoi
	# duoc khai thi bi gioi han, nguoi chua khai thi mo toang.
	if kho:
		if kho not in cua_toi:
			frappe.throw(
				"Kho này không nằm trong các kho bạn phụ trách. Cần xem kho khác "
				"thì báo anh Việt khai thêm ở màn Quản lý người dùng."
			)
		cua_toi = [kho]
	if not cua_toi:
		# Khong doan bua kho nao: tra rong kem loi nhac theo QT-24.
		return {
			"co_kho": 0,
			"ds": [],
			"nhac": "Tài khoản của bạn chưa khai Kho phụ trách nên máy chưa biết "
			"lấy hàng về kho nào. Báo anh Việt khai giúp ở màn Quản lý người dùng.",
		}

	tu = add_days(nowdate(), -so_ngay)
	dong = frappe.get_all(
		"Stock Entry Detail",
		filters={"t_warehouse": ["in", cua_toi], "docstatus": 1},
		fields=["parent", "item_code", "item_name", "qty", "uom", "s_warehouse", "t_warehouse"],
		limit_page_length=0,
	)
	if not dong:
		return {"co_kho": 1, "ds": [], "kho": cua_toi}

	cac_phieu = sorted({d["parent"] for d in dong})
	dau = {
		p["name"]: p
		for p in frappe.get_all(
			"Stock Entry",
			filters={
				"name": ["in", cac_phieu],
				"docstatus": 1,
				"stock_entry_type": "Material Transfer",
				"posting_date": [">=", tu],
			},
			fields=["name", "posting_date", "posting_time", "owner", "remarks"],
			limit_page_length=0,
		)
	}
	gop = {}
	for d in dong:
		p = dau.get(d["parent"])
		if not p:
			continue
		o = gop.setdefault(
			d["parent"],
			{
				"ma": d["parent"],
				"ngay": str(p["posting_date"]),
				"gio": _gio_hhmm(p["posting_time"]),
				"nguoi": p["owner"],
				"ghi_chu": p.get("remarks") or "",
				"kho_xuat": d.get("s_warehouse") or "",
				"kho_nhan": d.get("t_warehouse") or "",
				"so_dong": 0,
				"tong_sl": 0.0,
				"hang": [],
			},
		)
		o["so_dong"] += 1
		o["tong_sl"] += flt(d.get("qty"))
		o["hang"].append(
			{
				"ma": d["item_code"],
				"ten": d.get("item_name") or d["item_code"],
				"sl": flt(d.get("qty")),
				"dvt": d.get("uom") or "",
			}
		)

	ten = {}
	for u in {x["nguoi"] for x in gop.values()}:
		ten[u] = frappe.db.get_value("User", u, "full_name") or u
	ds = sorted(gop.values(), key=lambda x: (x["ngay"], x["gio"]), reverse=True)
	for x in ds:
		x["nguoi_ten"] = ten.get(x["nguoi"], x["nguoi"])
		x["tong_sl"] = round(x["tong_sl"], 3)
	return {"co_kho": 1, "ds": ds, "kho": cua_toi, "so_ngay": so_ngay}
