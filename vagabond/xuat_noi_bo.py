"""Xuat dung noi bo: hang ra khoi kho de TIEM dung, khong phai de ban.

Anh Viet giao 02/09/2026.

Vi sao tach khoi Xuat huy
-------------------------
Toi truoc hom nay, banh cho Marketing chup anh, banh moi doi tac, mau thu
R&D, banh nhan vien an ca deu phai lap phieu XUAT HUY voi ly do "Mau thu,
nem, chup hinh". Ba cai gia phai tra:

1. Gia tri to banh do vao cung mot tai khoan voi hang hong. Cuoi thang doc
   bao cao hao hut thi Bep la ben lam hong nhieu nhat, trong khi mot phan
   trong do la banh Marketing mang di chup. Do oan mot cach co he thong.
2. Khong biet bo phan nao tieu. "Thang nay Marketing tieu bao nhieu tien
   banh" khong co cach nao tra loi.
3. Nguoi lap phieu phai noi doi voi chinh minh: bam vao mot cai nut ghi
   chu "Xuat huy" trong khi banh khong he bi huy. Nut sai lam nen nep sai.

Man nay dung ra de cai gi ra khoi kho ma tiem VAN DUNG thi ghi la dung,
kem bo phan chiu chi phi. Hang hong that thi van di duong Xuat huy.

Luat phan quyen
---------------
Giong Xuat huy, va co y giong: hang roi khoi kho ma mat gia tri that thi
NGUOI LAP va NGUOI GHI SO phai la hai nguoi. Khac Dieu chuyen noi bo - cai
do hang chi doi kho nen cho ghi so ngay.

Anh chung minh KHONG bat buoc o day, khac Xuat huy. Ly do that: banh mang
di chup anh thi tam anh chup san pham chinh la bang chung, bat chup them
mot tam nua chi de luu ho so la them mot buoc vo ich. Con hang huy thi
khong ai chup, nen phai bat.

Ghi xuong dau
-------------
Stock Entry loai Material Issue, y het Xuat huy, chi khac ba cho: muc dich
nam o `vgb_muc_dich_xuat`, bo phan nam o `cost_center` cua tung dong, va
tai khoan chi phi chon theo muc dich chu khong dung chung mot tai khoan.
Khong de them doctype rieng, de bao cao ton kho va so ke toan cua ERPNext
van dung nguyen.
"""

import frappe
from frappe.utils import cint, flt, nowdate

from vagabond import bo_phan, chung_tu, xuat_kho

# Muc dich xuat dung noi bo. Moi muc: (ma, ten hien tren app, uu tien tai
# khoan).
#
# Vi sao moi muc dich mot bo tai khoan rieng: do moi la ly do ton tai cua
# man nay. Banh Marketing mang di chup phai vao chi phi ban hang (641),
# khong duoc vao gia von hang ban (632) nhu hang hong.
#
# Uu tien la MOT DAY chu khong phai mot so: cay tai khoan cua tiem con dang
# hoan thien, khai bao mot so duy nhat thi hom nao ke toan chua tao tai
# khoan do la ca man chet. Day cho phep tut xuong cai gan dung nhat.
MUC_DICH = (
	{
		"ma": "marketing",
		"ten": "Marketing chụp ảnh, quay phim",
		"mo": "Bánh và nguyên liệu mang đi chụp sản phẩm, quay clip.",
		"tk": ("6417", "641", "6418", "642"),
		"bo_phan": "Marketing",
	},
	{
		"ma": "rnd",
		"ten": "Mẫu thử, nghiên cứu công thức",
		"mo": "Bếp làm thử công thức mới, nếm thử trước khi lên menu.",
		"tk": ("6278", "627", "632", "642"),
		"bo_phan": "Sonneto Lab",
	},
	{
		"ma": "doi_tac",
		"ten": "Mời khách, tặng đối tác",
		"mo": "Bánh mời khách tại quầy, gửi tặng đối tác và báo chí.",
		"tk": ("6428", "642", "641"),
		"bo_phan": "Ban Giám đốc",
	},
	{
		"ma": "nhan_vien",
		"ten": "Nhân viên ăn ca",
		"mo": "Bánh và đồ uống cho nhân viên dùng trong ca.",
		"tk": ("6428", "642", "6278"),
		"bo_phan": "",
	},
	{
		"ma": "dao_tao",
		"ten": "Đào tạo, huấn luyện",
		"mo": "Nguyên liệu dùng để dạy nghề, tập tay nghề cho nhân viên mới.",
		"tk": ("6278", "627", "642"),
		"bo_phan": "",
	},
	{
		# v674 (Khải báo anh Việt 18/11/2026): CCDC mua về nhập kho Tổng, bếp
		# xin xuất ra dùng. Không có tài khoản cố định: chọn phân bổ một lần thì
		# vào thẳng chi phí theo khối của bộ phận (6273, 6413, 6423), phân bổ
		# nhiều tháng thì vào 242 và lên Bảng kê 242 (chi_phi_242).
		"ma": "ccdc",
		"ten": "Đưa công cụ dụng cụ vào dùng",
		"mo": "Khuôn, dụng cụ, thiết bị lấy từ kho ra dùng. Chọn phân bổ một lần hay nhiều tháng.",
		"tk": (),
		"bo_phan": "",
	},
	{
		"ma": "khac",
		"ten": "Việc nội bộ khác",
		"mo": "Việc nội bộ chưa có mục nào ở trên. Nhớ ghi rõ ở ô Ghi chú.",
		"tk": ("6428", "642"),
		"bo_phan": "",
	},
)

TRUONG_MOI = {
	"Stock Entry": [
		{
			"fieldname": "vgb_muc_dich_xuat",
			"label": "Mục đích xuất dùng nội bộ",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "purpose",
			"description": (
				"Máy điền khi lập phiếu trên app. Ô này phân biệt phiếu xuất "
				"dùng nội bộ với phiếu xuất huỷ - hai thứ cùng là Material "
				"Issue nhưng bản chất khác hẳn nhau."
			),
		}
	]
}


# ------------------------------------------------------------- phần thuần


def muc_dich_theo_ma(ma):
	"""Doc mot muc dich theo ma. Ham THUAN. Khong co thi tra None."""
	ma = (ma or "").strip().lower()
	if not ma:
		return None
	for m in MUC_DICH:
		if m["ma"] == ma:
			return m
	return None


def la_muc_dich_hop_le(ma):
	"""Ham THUAN."""
	return muc_dich_theo_ma(ma) is not None


def bo_phan_goi_y(ma_muc_dich):
	"""Bo phan doan san cho mot muc dich. Ham THUAN. Khong doan duoc thi rong.

	Chi la GOI Y de dien san o chon, nguoi lap doi duoc. Vi du banh mang
	di chup anh thuong la Marketing, nhung co hom la cua hang tu chup de
	dang Facebook cua quay.
	"""
	m = muc_dich_theo_ma(ma_muc_dich)
	if not m:
		return ""
	goi = m.get("bo_phan") or ""
	return goi if bo_phan.la_bo_phan_hop_le(goi) else ""


def ghi_chu_phieu(ten_muc_dich, ten_bo_phan, ghi_chu):
	"""Dong dien giai in tren phieu. Ham THUAN.

	Ghep san o day de phieu doc duoc ngay tren ban may tinh, khong phai mo
	app ra moi hieu phieu nay la gi.
	"""
	phan = ["Xuất dùng nội bộ"]
	if (ten_muc_dich or "").strip():
		phan.append(ten_muc_dich.strip())
	if (ten_bo_phan or "").strip():
		phan.append("Bộ phận: %s" % ten_bo_phan.strip())
	dong = " - ".join(phan)
	if (ghi_chu or "").strip():
		dong += ". " + ghi_chu.strip()
	return dong


MA_CCDC = "ccdc"
PB_MOT_LAN = "mot_lan"
PB_NHIEU_KY = "nhieu_ky"
CACH_PHAN_BO = (
	{"ma": PB_MOT_LAN, "ten": "Phân bổ một lần",
		"mo": "Giá trị hàng vào thẳng chi phí tháng này của bộ phận dùng. Hợp với đồ rẻ, dùng nhanh hỏng."},
	{"ma": PB_NHIEU_KY, "ten": "Phân bổ nhiều tháng",
		"mo": "Giá trị vào 242, Kế toán chia dần vào chi phí từng tháng theo Bảng kê 242. Hợp với khuôn, thiết bị dùng lâu."},
)


def thieu_phan_bo(ma_muc_dich, cach_phan_bo, so_ky):
	"""Câu nhắc riêng cho mục đích Đưa CCDC vào dùng. Hàm THUẦN.

	so_ky đọc đúng nghĩa: None hay chuỗi rỗng là chưa chọn, không thay bằng số
	mặc định nào (H8 loại 14)."""
	if (ma_muc_dich or "").strip().lower() != MA_CCDC:
		return []
	if cach_phan_bo not in (PB_MOT_LAN, PB_NHIEU_KY):
		return ["Chưa chọn cách phân bổ công cụ dụng cụ."]
	if cach_phan_bo == PB_NHIEU_KY:
		from vagabond.chi_phi_242 import SO_KY_TOI_DA

		try:
			n = int(so_ky)
		except (TypeError, ValueError):
			return ["Chưa chọn số tháng phân bổ."]
		if n < 2 or n > SO_KY_TOI_DA:
			return ["Số tháng phân bổ phải từ 2 tới %d. Một tháng thì chọn Phân bổ một lần." % SO_KY_TOI_DA]
	return []


def mon_khong_phai_ccdc(dong_mon):
	"""Các món trong phiếu không thuộc nhóm công cụ dụng cụ. Hàm THUẦN.

	dong_mon: [{ma, ten, nhom}]. Trả danh sách tên để câu báo lỗi kể đúng món."""
	from vagabond.ccdc_dung_ngay import NHOM_CCDC

	return [d.get("ten") or d.get("ma") for d in dong_mon if (d.get("nhom") or "").strip() not in NHOM_CCDC]


def thieu_gi(ma_muc_dich, ten_bo_phan, so_dong):
	"""Phieu nay con thieu gi truoc khi luu. Ham THUAN.

	Tra ve DANH SACH cau nhac, rong la du. Viet thuan de ca kiem chay duoc
	khong can site, va de man hinh dung chung mot bo luat voi may chu thay
	vi moi ben tu che mot bo.
	"""
	nhac = []
	if not la_muc_dich_hop_le(ma_muc_dich):
		nhac.append("Chưa chọn mục đích xuất dùng.")
	if not bo_phan.la_bo_phan_hop_le(ten_bo_phan):
		nhac.append("Chưa chọn bộ phận chịu chi phí.")
	if cint(so_dong) <= 0:
		nhac.append("Chưa có món nào trong phiếu.")
	return nhac


# ------------------------------------------------ phần chạm Frappe


def _tk_theo_muc_dich(cong_ty, ma_muc_dich):
	"""Tai khoan chi phi hop voi muc dich nay.

	Di theo day uu tien cua muc dich; het day ma van khong co tai khoan nao
	thi tut ve dung tai khoan ma Xuat huy dang dung, chu KHONG nem loi.
	Nem loi o day la chan nguoi ta lap phieu chi vi cay tai khoan chua day
	du, ma cai do khong phai loi cua ho.
	"""
	m = muc_dich_theo_ma(ma_muc_dich)
	uu_tien = tuple(m.get("tk") or ()) if m else ()
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
	# 17/09/2026: khop CHINH XAC qua `xuat_kho.chon_tai_khoan`, khong con
	# startswith. Xem docstring ham do ve ca 632 bi 6328 cuop cho.
	return xuat_kho.chon_tai_khoan(ds, uu_tien) or xuat_kho._tk_chi_phi(cong_ty)


def _chon_so_ky():
	from vagabond.chi_phi_242 import CHON_SO_KY

	return list(CHON_SO_KY)


def _tk_ccdc(cong_ty, cach_phan_bo, ten_bo_phan):
	"""Tài khoản ghi Nợ cho phiếu Đưa CCDC vào dùng."""
	from vagabond import chi_phi_242

	if cach_phan_bo == PB_NHIEU_KY:
		return chi_phi_242.tk_242_chinh(cong_ty)
	ds = frappe.get_all(
		"Account",
		filters={"company": cong_ty, "is_group": 0, "disabled": 0, "root_type": "Expense",
			"account_type": ["not in", ["Stock", "Stock Adjustment"]]},
		fields=["name", "account_number"],
		limit_page_length=0,
	)
	tk = xuat_kho.chon_tai_khoan(ds, chi_phi_242.tk_uu_tien_theo_khoi(bo_phan.nhom_cua(ten_bo_phan)))
	if not tk:
		frappe.throw("Công ty chưa có tài khoản chi phí dụng cụ (6273, 6413 hoặc 6423). Báo Kế toán dựng tài khoản rồi lập lại.")
	return tk


def _kiem_mon_ccdc(sach):
	"""Máy chủ kiểm món của phiếu CCDC cho mọi đường gọi, không chỉ màn app."""
	nhom = {}
	for r in frappe.get_all("Item", filters={"name": ["in", [d["ma"] for d in sach]]},
			fields=["name", "item_name", "item_group"], limit_page_length=0):
		nhom[r.name] = r
	sai = mon_khong_phai_ccdc([{"ma": d["ma"], "ten": (nhom.get(d["ma"]) or {}).get("item_name"),
		"nhom": (nhom.get(d["ma"]) or {}).get("item_group")} for d in sach])
	if sai:
		ke = ", ".join(sai[:5]) + (" và %d món nữa" % (len(sai) - 5) if len(sai) > 5 else "")
		frappe.throw(
			"Mục đích Đưa công cụ dụng cụ vào dùng chỉ dành cho món nhóm Công cụ Dụng cụ. Món khác nhóm: %s. "
			"Bỏ các món đó hoặc chọn mục đích khác." % ke
		)


@frappe.whitelist()
def khoi_dong():
	"""Moi thu app can de mo man Xuat dung noi bo, goi mot lan.

	Gom vao mot cua giong `xuat_kho.khoi_dong`, va vi cung mot ly do: vai
	Kiem ke vien khong doc duoc Warehouse hay Cost Center qua API chuan.
	"""
	xuat_kho._duoc_xuat()
	ct = xuat_kho._cong_ty()
	return {
		"cong_ty": ct,
		"kho": xuat_kho._kho_that(ct),
		"muc_dich": [
			{"ma": m["ma"], "ten": m["ten"], "mo": m["mo"], "bo_phan": bo_phan_goi_y(m["ma"])}
			for m in MUC_DICH
		],
		"bo_phan": bo_phan.danh_sach().get("khoi") or [],
		"cach_phan_bo": [dict(c) for c in CACH_PHAN_BO],
		"chon_so_ky": _chon_so_ky(),
		"duoc_duyet": 1 if xuat_kho.duoc_duyet() else 0,
		"toi": frappe.session.user,
	}


@frappe.whitelist()
def luu(kho=None, muc_dich=None, bo_phan_chiu=None, ghi_chu=None, dong=None, anh=None, cach_phan_bo=None, so_ky=None):
	"""Tao phieu xuat dung noi bo o dang BAN NHAP, cho quan ly kho ghi so."""
	xuat_kho._duoc_xuat()
	if not kho:
		frappe.throw("Chưa chọn kho xuất.")
	sach = xuat_kho._doc_dong(dong)
	nhac = thieu_gi(muc_dich, bo_phan_chiu, len(sach)) + thieu_phan_bo(muc_dich, cach_phan_bo, so_ky)
	if nhac:
		frappe.throw(" ".join(nhac))
	la_ccdc = (muc_dich or "").strip().lower() == MA_CCDC
	if la_ccdc:
		_kiem_mon_ccdc(sach)
	xuat_kho._chan_qua_ton(kho, sach)

	ct = xuat_kho._cong_ty()
	viet_tat = frappe.db.get_value("Company", ct, "abbr") or ""
	ma_tt = bo_phan.ten_that(bo_phan_chiu, viet_tat)
	if not frappe.db.exists("Cost Center", ma_tt):
		frappe.throw(
			"Bộ phận %s chưa có trong hệ thống. Báo quản trị hệ thống để dựng lại "
			"cây bộ phận." % bo_phan_chiu
		)

	m = muc_dich_theo_ma(muc_dich)
	doc = frappe.new_doc("Stock Entry")
	doc.stock_entry_type = xuat_kho.LOAI["huy"]
	doc.purpose = xuat_kho.LOAI["huy"]
	doc.company = ct
	doc.posting_date = nowdate()
	doc.set_posting_time = 0
	doc.from_warehouse = kho
	doc.vgb_muc_dich_xuat = m["ma"]
	if anh:
		doc.vgb_anh_xuat = anh
	ten_md = m["ten"]
	if la_ccdc:
		doc.vgb_so_ky_phan_bo = int(so_ky) if cach_phan_bo == PB_NHIEU_KY else 0
		ten_md = "%s, %s" % (ten_md, ("phân bổ %d tháng" % int(so_ky)) if cach_phan_bo == PB_NHIEU_KY else "phân bổ một lần")
		tk = _tk_ccdc(ct, cach_phan_bo, bo_phan_chiu)
	else:
		tk = _tk_theo_muc_dich(ct, m["ma"])
	doc.remarks = ghi_chu_phieu(ten_md, bo_phan_chiu, ghi_chu)
	for d in sach:
		doc.append(
			"items",
			{
				"item_code": d["ma"],
				"qty": d["sl"],
				"s_warehouse": kho,
				"expense_account": tk,
				"cost_center": ma_tt,
			},
		)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Chờ ghi sổ"}


@frappe.whitelist()
def ghi_so(name=None):
	"""Quan ly kho ghi so - toi day ton moi thuc su tru."""
	if not xuat_kho.duoc_duyet():
		frappe.throw("Chỉ quản lý kho mới được ghi sổ phiếu xuất dùng nội bộ.")
	doc = frappe.get_doc("Stock Entry", name)
	if doc.docstatus != 0:
		frappe.throw("Phiếu này không còn ở trạng thái bản nháp.")
	ma = (doc.get("vgb_muc_dich_xuat") or "").strip()
	if not ma:
		frappe.throw(
			"Phiếu này không phải phiếu xuất dùng nội bộ. Phiếu xuất huỷ thì "
			"ghi sổ ở màn Xuất huỷ."
		)
	if ma == xuat_kho.MA_PHUC_VU_BAN:
		frappe.throw(
			"Phiếu này là phiếu xuất kho phục vụ bán hàng. Ghi sổ nó ở đúng "
			"màn đã lập ra nó."
		)
	if cint(doc.get("vgb_huy")):
		frappe.throw(
			"Phiếu này đã bỏ nên không ghi sổ được. Lý do: %s."
			% (doc.get("vgb_huy_ly_do") or "không ghi")
		)
	doc.flags.ignore_permissions = True
	doc.submit()
	khoan = ""
	if ma == MA_CCDC and cint(doc.get("vgb_so_ky_phan_bo")) > 0:
		# Dựng dòng Bảng kê 242 ngay trong giao dịch ghi sổ. Lỗi ở đây không được
		# chặn bếp ghi sổ phiếu: nhịp quét đêm dựng lại từ sổ cái, cùng một đường.
		from vagabond import chi_phi_242

		try:
			frappe.db.savepoint("vgb_bang_ke_242")
			chi_phi_242.khi_ghi_so_xuat(doc.name)
			khoan = frappe.db.get_value(chi_phi_242.DT, {"khoa": "Stock Entry:%s" % doc.name}, "name") or ""
		except Exception:
			frappe.db.rollback(save_point="vgb_bang_ke_242")
			frappe.log_error(frappe.get_traceback(), "Dựng Bảng kê 242 sau phiếu xuất CCDC lỗi")
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Đã ghi sổ", "khoan_242": khoan}


@frappe.whitelist()
def ds_phieu(gioi_han=40):
	"""Danh sach phieu xuat dung noi bo gan day.

	Loc bang `vgb_muc_dich_xuat` co gia tri: day chinh la thu phan biet no
	voi phieu xuat huy, vi ca hai cung la Material Issue.

	Va tu 16/09/2026 phai TRU ma cua man Xuat kho phuc vu ban hang ra, vi
	man do cung ghi vao chinh o nay. Khong tru thi danh sach cua man nay
	keo luon phieu chot kho cua quay sang, dung cai loi ma man nay sinh ra
	de chua voi Xuat huy.
	"""
	xuat_kho._duoc_xuat()
	ds = frappe.get_all(
		"Stock Entry",
		filters={
			"purpose": xuat_kho.LOAI["huy"],
			"docstatus": ["<", 2],
			"vgb_huy": 0,
			"vgb_muc_dich_xuat": ["not in", ["", xuat_kho.MA_PHUC_VU_BAN]],
		},
		fields=[
			"name",
			"posting_date",
			"docstatus",
			"from_warehouse",
			"total_outgoing_value",
			"owner",
			"remarks",
			"vgb_muc_dich_xuat",
		],
		order_by="creation desc",
		limit_page_length=int(gioi_han or 40),
	)
	ten = {}
	for u in {d.owner for d in ds}:
		ten[u] = frappe.db.get_value("User", u, "full_name") or u
	for d in ds:
		m = muc_dich_theo_ma(d.get("vgb_muc_dich_xuat"))
		d["nguoi_tao"] = ten.get(d.owner, d.owner)
		d["ten_muc_dich"] = m["ten"] if m else (d.get("vgb_muc_dich_xuat") or "")
		d["trang_thai"] = "Chờ ghi sổ" if d.docstatus == 0 else "Đã ghi sổ"
		d["so_dong"] = frappe.db.count("Stock Entry Detail", {"parent": d.name})
	return ds


@frappe.whitelist()
def chi_tiet(name=None):
	"""Mot phieu xuat dung noi bo kem cac dong hang."""
	xuat_kho._duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	m = muc_dich_theo_ma(doc.get("vgb_muc_dich_xuat"))
	tt = ""
	for d in doc.items:
		if d.get("cost_center"):
			tt = d.get("cost_center")
			break
	anh = xuat_kho.anh_theo_ma([d.item_code for d in doc.items])
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
		"kho_xuat": doc.from_warehouse,
		"muc_dich": doc.get("vgb_muc_dich_xuat") or "",
		"ten_muc_dich": m["ten"] if m else "",
		"so_ky_phan_bo": cint(doc.get("vgb_so_ky_phan_bo")),
		"khoan_242": _khoan_cua(doc) if (doc.get("vgb_muc_dich_xuat") or "") == MA_CCDC else "",
		"bo_phan": tt,
		"anh": doc.get("vgb_anh_xuat") or "",
		"ghi_chu": doc.remarks or "",
		"nguoi_tao": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"tong_tien": flt(doc.total_outgoing_value),
		"duoc_duyet": 1 if xuat_kho.duoc_duyet() else 0,
		"la_cua_toi": 1 if doc.owner == frappe.session.user else 0,
		"dong": [
			{
				"ma": d.item_code,
				"ten": d.item_name,
				"dvt": d.uom,
				"sl": flt(d.qty),
				"tien": flt(d.amount),
				"anh": anh.get(d.item_code, ""),
			}
			for d in doc.items
		],
	}


@frappe.whitelist()
def bo_phieu(name=None, ly_do=None):
	"""Bo mot phieu nhap dang sai - chi nguoi tao hoac quan ly kho.

	Khong xoa vinh vien, chi danh dau da huy: khong chung tu nao trong he
	thong nay duoc xoa han (QT-20).
	"""
	xuat_kho._duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	if doc.docstatus != 0:
		frappe.throw("Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính.")
	if doc.owner != frappe.session.user and not xuat_kho.duoc_duyet():
		frappe.throw("Chỉ người tạo phiếu hoặc quản lý kho mới bỏ được phiếu này.")
	if cint(doc.get("vgb_huy") or 0):
		return {"ok": 1, "da_huy_tu_truoc": 1}
	chung_tu.danh_dau_huy(doc, ly_do or "Bỏ phiếu nháp sai")
	return {"ok": 1, "da_huy": 1}


def _khoan_cua(doc):
	if doc.docstatus != 1 or not cint(doc.get("vgb_so_ky_phan_bo")):
		return ""
	return frappe.db.get_value("Vagabond Khoan 242", {"khoa": "Stock Entry:%s" % doc.name}, "name") or ""
