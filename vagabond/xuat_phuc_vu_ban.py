# -*- coding: utf-8 -*-
"""Xuat kho phuc vu ban hang: chot nhung gi diem ban da dung trong tuan.

Anh Viet giao 16/09/2026.

DO TREN SITE THAT TRUOC KHI VIET DONG NAO
------------------------------------------
Quet toan bo so kho cua hai kho diem ban trong mot thang, tu 16/08 toi
16/09/2026. Hang ra khoi Kho D1 va Kho Sales Online chi co DUNG 18 dong,
va ca 18 deu la dieu chuyen sang kho khac. Khong mot dong nao la hang da
dung hay da ban.

Nghia la hang di vao thi deu dan ngay nao cung co, con di ra thi khong co
duong nao. Dang treo o hai kho do:

    Nguyen lieu pha che tai quay    khoang  96 trieu
    Cong cu dung cu                 khoang  73 trieu
    Bao bi dung hang ngay           khoang 130 trieu
    Ban thanh pham                  khoang  21 trieu

Ton kho bao thua dung bang so do, va chi phi bao thieu dung bang so do.

VI SAO KHONG MUON MOT MAN CO SAN NAO
-------------------------------------
* Xuat huy danh cho hang HONG. Bao bi da goi cho khach khong hong, no lam
  duoc viec cua no. Day dung la cai loi ma man Xuat dung noi bo sinh ra de
  chua: truoc 02/09 banh Marketing chup anh phai bam nut Xuat huy, nen cuoi
  thang doc bao cao hao hut thi Bep mang tieng lam hong nhieu nhat.
* Xuat dung noi bo danh cho hang TIEM DUNG chu khong ban duoc: chup anh,
  mau thu, moi khach, an ca. Ca sau muc dich do deu vao 641x hoac 642x theo
  bo phan tieu. Bao bi goi cho khach thi khac han: no di kem mot to banh
  ban duoc tien.
* Kiem ke day chenh lech vao tai khoan hao hut 6328. Sai cho y het vay.

Nen phai co mot duong rieng, va day la duong do.

CACH LAM ANH VIET CHOT 16/09/2026
----------------------------------
Nhip:    cuoi tuan, moi diem ban mot phieu.
Lay so:  quay DEM CON LAI, may tu ra so da dung. Khong ai phai nho trong
         tuan da dung bao nhieu, va so ra khop voi thuc te tren ke.
Quyen:   quay lap, ke toan ghi so. Giong Xuat huy va Xuat dung noi bo, va
         co y giong: hang roi kho ma mat gia tri that thi nguoi lap va
         nguoi ghi so phai la hai nguoi.

HAI TAI KHOAN, VA NGUOI DUNG KHONG PHAI CHON
---------------------------------------------
Man nay ghi xuong hai tai khoan khac nhau, nhung NHOM MON quyet dinh chu
khong phai nguoi dung chon:

    Bao bi, cong cu dung cu, van phong pham  ->  641x chi phi ban hang
    Nguyen lieu, ban thanh pham              ->  632  gia von hang ban

Ly do: cai ly ca phe hay cai ruot banh do co ban ra that va thu duoc tien,
nen gia tri cua no la gia von. Con cai tui giay thi khong ban cho ai ca.
Bat nguoi dung chon tai khoan la bat ho lam viec cua ke toan, va chon sai
thi khong lop nao bao.

BANH THANH PHAM KHONG DI QUA DAY
---------------------------------
Anh Viet chot 16/09/2026: banh thanh pham de nguyen, xu bang viec bat tru
kho cho hoa don ban, lam mot lan cho ca POS lan ngoai POS.

Neu man nay tru luon phan banh thi no dang ganh ho cai viec do, va ngay
nao bat tru kho cho hoa don thi banh bi tru HAI LAN. Nen danh sach nhom mon
o duoi la danh sach DONG: nhom nao khong co ten trong do thi man khong liet
ke, va nguoi di tim se duoc noi ro vi sao cung cho can den.

DEM RA NHIEU HON SO TREN SO THI KHONG NHAN
-------------------------------------------
Dem ra 120 cai trong khi so ghi 100 khong phai la tieu dung, do la sai sot
nhap hoac sai sot dem. Bien no thanh mot dong xuat AM la lam hong so kho va
lam hong ca gia von binh quan. Cho do phai di duong kiem ke, noi ma chenh
lech duoc ghi dung ban chat va co nguoi soat.
"""

import frappe
from frappe.utils import cint, flt, nowdate

from vagabond import bo_phan, chung_tu, xuat_kho

# Ma nhan dien phieu cua man nay, nam trong o `vgb_muc_dich_xuat`.
#
# O do dung CHUNG voi man Xuat dung noi bo, nen moi man phai loc DUNG ma
# cua minh. Loc kieu "o nay co gia tri" la keo luon phieu cua man kia sang,
# va do chinh la cai loi ma man Xuat dung noi bo tung mac phai voi Xuat huy.
MA_MUC_DICH = xuat_kho.MA_PHUC_VU_BAN

# Nhan hai nhom tai khoan, hien thang tren man de khong ai phai doan.
NHAN_CHI_PHI = "Chi phí bán hàng"
NHAN_GIA_VON = "Giá vốn hàng bán"

# Nhom mon man nay lo, va tai khoan cua tung nhom.
#
# Uu tien tai khoan la mot DAY chu khong phai mot so, y het `xuat_noi_bo`:
# cay tai khoan cua tiem con dang hoan thien, khai mot so duy nhat thi hom
# nao ke toan chua tao tai khoan do la ca man chet.
#
# Ten nhom lay dung tu cay Nhom mon tren site, doc ngay 16/09/2026.
NHOM = (
	{
		"nhom": "Bao bì",
		"tk": ("6412", "641", "6413"),
		"nhan": NHAN_CHI_PHI,
		"mo": "Túi, hộp, ly, đế lót, ruy băng gói cho khách.",
	},
	{
		"nhom": "Công cụ Dụng cụ",
		"tk": ("6413", "641", "6412"),
		"nhan": NHAN_CHI_PHI,
		"mo": "Dao nĩa, khăn giấy, nến, đồ dùng phục vụ khách.",
	},
	{
		"nhom": "Công cụ dụng cụ Sonneto",
		"tk": ("6413", "641", "6412"),
		"nhan": NHAN_CHI_PHI,
		"mo": "Dụng cụ của Sonneto dùng tại điểm bán.",
	},
	{
		"nhom": "Văn phòng phẩm",
		"tk": ("6413", "641", "6428"),
		"nhan": NHAN_CHI_PHI,
		"mo": "Giấy in bill, bút, vật dụng văn phòng của quầy.",
	},
	{
		"nhom": "Nguyên vật liệu Thô",
		"tk": ("632", "621", "6278"),
		"nhan": NHAN_GIA_VON,
		"mo": "Sữa, cà phê, syrup pha tại quầy rồi bán ra.",
	},
	{
		"nhom": "Nguyên vật liệu Sonneto",
		"tk": ("632", "621", "6278"),
		"nhan": NHAN_GIA_VON,
		"mo": "Nguyên liệu của Sonneto dùng tại điểm bán.",
	},
	{
		"nhom": "Bán thành phẩm Bánh",
		"tk": ("632", "621", "6278"),
		"nhan": NHAN_GIA_VON,
		"mo": "Ruột bánh, topping bếp chuyển sang để hoàn thiện tại quầy.",
	},
	{
		"nhom": "Bán thành phẩm Nước",
		"tk": ("632", "621", "6278"),
		"nhan": NHAN_GIA_VON,
		"mo": "Bán thành phẩm pha chế bếp chuyển sang.",
	},
	{
		"nhom": "Nhân bán thành phẩm",
		"tk": ("632", "621", "6278"),
		"nhan": NHAN_GIA_VON,
		"mo": "Nhân bánh bếp chuyển sang để hoàn thiện tại quầy.",
	},
)

# Nhom mon CO Y de ngoai, kem cau noi ro di dau. Viet ra day chu khong de
# man im lang, vi nguoi di tim mot mon khong thay no se tu ket luan la may
# hong roi go bua vao mot dong khac.
#
# Ghi theo NHOM LA chu khong theo nhom cha, vi o `item_group` cua mot Mon
# luon la mot nhom la. Ghi "Thanh pham Banh" khong bat duoc mot mon thuoc
# "Banh lanh", va luc do nguoi dung chi nhan duoc cau chung chung.
NGOAI_PHAM_VI = (
	{
		"nhom": (
			"Thành phẩm Bánh", "Bánh ổ sinh nhật", "Bánh lạnh", "Bánh khô",
			"Bánh nướng", "Hộp bánh theo mùa", "Bánh Wholesale",
			"BÁNH NHẸ / CONFECTIONERY", "Topping cho món bánh",
		),
		"ten": "Bánh thành phẩm",
		"vi_sao": (
			"Bánh thành phẩm bán cho khách nên trừ kho theo hoá đơn bán, "
			"không khai tay ở đây. Khai cả hai chỗ là trừ kho hai lần."
		),
	},
	{
		"nhom": (
			"Thành phẩm Nước", "Cà phê", "Trà", "Matcha", "Cacao",
			"Ice Cream - Kem", "Topping cho món nước",
		),
		"ten": "Đồ uống thành phẩm",
		"vi_sao": (
			"Đồ uống bán cho khách nên trừ kho theo hoá đơn bán. Nguyên liệu "
			"pha ra ly nước đó thì khai ở đây."
		),
	},
	{
		"nhom": (
			"Phụ kiện cho bánh", "Event - Catering", "Khuyến mãi dạng Combo",
			"Dịch vụ Bán hàng", "Khoá học Sonneto",
		),
		"ten": "Hàng và dịch vụ bán ra khác",
		"vi_sao": (
			"Thứ này bán cho khách và có doanh thu, nên trừ kho theo hoá đơn "
			"bán chứ không khai tay ở đây."
		),
	},
	{
		"nhom": ("Tài sản Cố định",),
		"ten": "Tài sản cố định",
		"vi_sao": "Tài sản cố định đi đường khấu hao, không xuất dùng một lần.",
	},
)

# Doan bo phan chiu chi phi tu ten kho. Chi la GOI Y dien san, nguoi lap
# doi duoc, y het `xuat_noi_bo.bo_phan_goi_y`.
DOAN_BO_PHAN = (
	("d1", "Cửa hàng D1"),
	("nvhtn", "Cửa hàng NVHTN"),
	("sales", "Sales và bán sỉ"),
)


# ------------------------------------------------------------- phần thuần


def nhom_theo_ten(ten):
	"""Doc cau hinh cua mot nhom mon. THUAN. Ngoai pham vi thi tra None."""
	ten = (ten or "").strip()
	if not ten:
		return None
	for n in NHOM:
		if n["nhom"] == ten:
			return n
	return None


def trong_pham_vi(ten_nhom):
	"""Nhom mon nay co thuoc man nay khong. THUAN."""
	return nhom_theo_ten(ten_nhom) is not None


def vi_sao_ngoai_pham_vi(ten_nhom):
	"""Cau giai thich cho mot nhom mon bi de ngoai. THUAN.

	Nhom co ten trong bang thi tra dung cau da viet san. Nhom la khong biet
	thi tra mot cau chung, van hon la im lang.
	"""
	ten = (ten_nhom or "").strip()
	if trong_pham_vi(ten):
		return ""
	for n in NGOAI_PHAM_VI:
		if ten in n["nhom"]:
			return n["vi_sao"]
	return (
		"Nhóm %s không nằm trong màn này. Màn này chỉ chốt bao bì, công cụ "
		"dụng cụ, văn phòng phẩm, nguyên liệu và bán thành phẩm đã dùng tại "
		"điểm bán." % (ten or "này")
	)


def da_dung(ton_so, con_lai):
	"""So luong da dung trong ky. THUAN.

	Ton tren so tru con lai thuc te. Day la toan bo phep tinh cua man nay,
	de rieng ra mot ham de ca kiem soi duoc no chu khong phai soi qua mot
	man hinh.
	"""
	return flt(ton_so) - flt(con_lai)


def soat_mot_dong(d):
	"""Mot dong dem xong co dung khong. THUAN.

	Tra ve (viec, cau nhac):
	    ("ghi", "")      co hang di ra, ghi vao phieu
	    ("bo_qua", "")   chua dem, hoac dem ra dung bang so tren so
	    ("hong", cau)    dem sai, khong nhan

	Vi sao "chua dem" khong phai la loi: bang kiem liet ke MOI ma dang co
	ton, ma mot tuan thi khong phai ma nao cung dung toi. Bat go so cho ca
	nhung ma khong dung la buoc nguoi ta go bua cho xong man.
	"""
	ma = (d.get("ma") or "").strip()
	if not ma:
		return ("hong", "Có dòng không có mã hàng.")
	if not trong_pham_vi(d.get("nhom")):
		return ("hong", "%s: %s" % (ma, vi_sao_ngoai_pham_vi(d.get("nhom"))))

	con = d.get("con_lai")
	if con is None or (isinstance(con, str) and not con.strip()):
		return ("bo_qua", "")

	ton = flt(d.get("ton_so"))
	con = flt(con)
	if con < 0:
		return ("hong", "%s: số còn lại không thể là số âm." % ma)
	if con > ton:
		return (
			"hong",
			"%s: đếm ra %s mà sổ chỉ ghi %s. Đếm nhiều hơn sổ không phải là "
			"hàng đã dùng, đó là sai sót nhập hoặc sai sót đếm. Việc đó đi "
			"đường Kiểm kê, ở đó chênh lệch mới được ghi đúng bản chất."
			% (ma, flt(con), flt(ton)),
		)
	if da_dung(ton, con) <= 0:
		return ("bo_qua", "")
	return ("ghi", "")


def soat_bang_dem(dong):
	"""Soat ca bang dem. THUAN. Tra ve (dong se ghi, danh sach cau nhac).

	Soat HET moi dong roi moi tra loi, khong dung o dong hong dau tien:
	quay dem ca bang roi bam luu, bao tung loi mot la bat ho bam luu nam
	lan.
	"""
	se_ghi = []
	nhac = []
	for d in dong or []:
		viec, cau = soat_mot_dong(d or {})
		if viec == "hong":
			nhac.append(cau)
		elif viec == "ghi":
			se_ghi.append(
				{
					"ma": (d.get("ma") or "").strip(),
					"nhom": (d.get("nhom") or "").strip(),
					"sl": da_dung(d.get("ton_so"), d.get("con_lai")),
				}
			)
	if not se_ghi and not nhac:
		nhac.append(
			"Chưa đếm được dòng nào có hàng đi ra. Gõ số còn lại cho ít nhất "
			"một mã rồi lưu."
		)
	return se_ghi, nhac


def bo_phan_goi_y(ten_kho):
	"""Doan bo phan chiu chi phi tu ten kho. THUAN. Khong doan duoc thi rong."""
	t = (ten_kho or "").strip().lower()
	if not t:
		return ""
	for khoa, bp in DOAN_BO_PHAN:
		if khoa in t:
			return bp
	return ""


def ghi_chu_phieu(ten_kho, ten_bo_phan, ghi_chu):
	"""Dong dien giai in tren phieu. THUAN.

	Ghep san de doc duoc ngay tren ban may tinh, khong phai mo app moi hieu
	phieu nay la gi.
	"""
	phan = ["Xuất kho phục vụ bán hàng"]
	if (ten_kho or "").strip():
		phan.append(ten_kho.strip())
	if (ten_bo_phan or "").strip():
		phan.append("Bộ phận: %s" % ten_bo_phan.strip())
	dong = " - ".join(phan)
	if (ghi_chu or "").strip():
		dong += ". " + ghi_chu.strip()
	return dong


def thieu_gi(ten_bo_phan, so_dong):
	"""Phieu nay con thieu gi truoc khi luu. THUAN. Rong la du."""
	nhac = []
	if not bo_phan.la_bo_phan_hop_le(ten_bo_phan):
		nhac.append("Chưa chọn bộ phận chịu chi phí.")
	if cint(so_dong) <= 0:
		nhac.append("Chưa có dòng nào có hàng đi ra.")
	return nhac


# ------------------------------------------------ phần chạm Frappe


def _tk_theo_nhom(cong_ty, ten_nhom):
	"""Tai khoan chi phi hop voi nhom mon nay.

	Di theo day uu tien cua nhom; het day ma khong co tai khoan nao thi tut
	ve dung tai khoan Xuat huy dang dung chu KHONG nem loi. Nem loi o day la
	chan quay chot kho chi vi cay tai khoan chua day du, ma cai do khong
	phai loi cua ho.
	"""
	n = nhom_theo_ten(ten_nhom)
	uu_tien = tuple(n.get("tk") or ()) if n else ()
	ds = frappe.get_all(
		"Account",
		filters={
			"company": cong_ty,
			"is_group": 0,
			"root_type": ["in", ["Expense", "Income"]],
			"account_type": ["not in", ["Stock", "Stock Adjustment"]],
		},
		fields=["name", "account_number"],
		limit_page_length=0,
	)
	# 17/09/2026: khop CHINH XAC qua `xuat_kho.chon_tai_khoan`, khong con
	# startswith. Codex bat tren PR #341: startswith("632") nhan luon
	# "6328 - Hao hut" neu no dung truoc, nguyen lieu di thang vao hao hut.
	return xuat_kho.chon_tai_khoan(ds, uu_tien) or xuat_kho._tk_chi_phi(cong_ty)


@frappe.whitelist()
def khoi_dong():
	"""Moi thu app can de mo man, goi mot lan.

	Gom vao mot cua giong `xuat_kho.khoi_dong`, va vi cung mot ly do: vai
	Kiem ke vien khong doc duoc Warehouse hay Cost Center qua API chuan.
	"""
	xuat_kho._duoc_xuat()
	ct = xuat_kho._cong_ty()
	kho = xuat_kho._kho_that(ct)
	for k in kho:
		k["bo_phan_goi_y"] = bo_phan_goi_y(k.get("name"))
	return {
		"cong_ty": ct,
		"kho": kho,
		"bo_phan": bo_phan.danh_sach().get("khoi") or [],
		"nhom": [
			{"nhom": n["nhom"], "nhan": n["nhan"], "mo": n["mo"]} for n in NHOM
		],
		"ngoai_pham_vi": [
			{"ten": n["ten"], "vi_sao": n["vi_sao"]} for n in NGOAI_PHAM_VI
		],
		"duoc_duyet": 1 if xuat_kho.duoc_duyet() else 0,
		"toi": frappe.session.user,
	}


@frappe.whitelist()
def bang_dem(kho=None):
	"""Bang de quay dem: moi ma dang co ton trong pham vi man nay.

	Tra ve ton TREN SO de quay doi chieu, khong tra so da dung: so da dung
	la thu may tinh ra sau khi quay dem xong.
	"""
	xuat_kho._duoc_xuat()
	if not kho:
		frappe.throw("Chưa chọn kho.")
	ton = frappe.get_all(
		"Bin",
		filters={"warehouse": kho, "actual_qty": [">", 0]},
		fields=["item_code", "actual_qty", "stock_uom"],
		limit_page_length=0,
	)
	if not ton:
		return {"kho": kho, "dong": []}

	ma = [t["item_code"] for t in ton]
	mon = {
		m["name"]: m
		for m in frappe.get_all(
			"Item",
			filters={"name": ["in", ma]},
			fields=["name", "item_name", "item_group", "stock_uom", "image"],
			limit_page_length=0,
		)
	}
	nhan_nhom = {n["nhom"]: n["nhan"] for n in NHOM}
	dong = []
	for t in ton:
		m = mon.get(t["item_code"]) or {}
		g = m.get("item_group") or ""
		if not trong_pham_vi(g):
			continue
		dong.append(
			{
				"ma": t["item_code"],
				"ten": m.get("item_name") or t["item_code"],
				"nhom": g,
				"nhan": nhan_nhom.get(g, ""),
				"dvt": m.get("stock_uom") or t.get("stock_uom") or "",
				"ton_so": flt(t["actual_qty"]),
				"anh": m.get("image") or "",
			}
		)
	dong.sort(key=lambda d: (d["nhan"], d["nhom"], d["ten"]))
	return {"kho": kho, "dong": dong}


def _ton_that(kho, ds_ma):
	"""Ton THAT trong Bin cua tung ma o kho nay, {ma: so}.

	Codex bat tren PR #341: `luu` tin `ton_so` app gui len de tinh so da
	dung. Ton app gui co the cu (mo bang dem tu sang, chieu moi luu, giua
	chung co nhap them) hoac bi sua tay. `_chan_qua_ton` chi chan xuat VUOT
	ton, khong bat duoc xuat THIEU. Nen ton tren so phai doc lai tu Bin
	ngay luc luu, app gui gi cung bo.
	"""
	ma = sorted({m for m in (ds_ma or []) if m})
	if not ma:
		return {}
	return {
		r["item_code"]: flt(r["actual_qty"])
		for r in frappe.get_all(
			"Bin",
			filters={"warehouse": kho, "item_code": ["in", ma]},
			fields=["item_code", "actual_qty"],
			limit_page_length=0,
		)
	}


def _nhom_that(ds_ma):
	"""Nhom mon doc THANG tu co so du lieu, {ma: nhom}.

	KHONG tin nhom mon app gui len. App gui gi thi gui, cai quyet dinh tai
	khoan ghi so phai doc tu danh muc Mon. Tin app la mo duong cho mot dong
	banh thanh pham di vao phieu nay voi nhan "Bao bi".
	"""
	ma = sorted({m for m in (ds_ma or []) if m})
	if not ma:
		return {}
	return {
		r["name"]: r["item_group"]
		for r in frappe.get_all(
			"Item", filters={"name": ["in", ma]}, fields=["name", "item_group"],
			limit_page_length=0,
		)
	}


def _phieu_cho_cua_kho(kho):
	"""Ten phieu cua man nay dang cho ghi so o kho nay, hoac "" neu chua co."""
	ds = frappe.get_all(
		"Stock Entry",
		filters={
			"docstatus": 0,
			"vgb_huy": 0,
			"vgb_muc_dich_xuat": MA_MUC_DICH,
			"from_warehouse": kho,
		},
		fields=["name"],
		limit_page_length=1,
	)
	return ds[0]["name"] if ds else ""


@frappe.whitelist()
def luu(kho=None, bo_phan_chiu=None, ghi_chu=None, dong=None):
	"""Tao phieu o dang BAN NHAP, cho ke toan ghi so."""
	xuat_kho._duoc_xuat()
	if not kho:
		frappe.throw("Chưa chọn kho.")
	if isinstance(dong, str):
		import json

		dong = json.loads(dong or "[]")

	# Mot kho chi co MOT phieu cho ghi so (Codex bat tren PR #344). Nhip la
	# moi diem ban mot phieu moi tuan, nen phieu nhap thu hai cho cung kho
	# khong bao gio la y muon: no la mat phan hoi HTTP roi bam lai, hoac hai
	# nguoi cung chot mot kho. Hai phieu cung so da dung ma deu ghi so thi
	# ton 100 dem 80 bi tru hai lan con 60. Khoa dong Warehouse de hai lan
	# goi cung luc phai xep hang, roi moi doc xem da co phieu cho chua.
	frappe.db.get_value("Warehouse", kho, "name", for_update=True)
	da_co = _phieu_cho_cua_kho(kho)
	if da_co:
		frappe.throw(
			"Kho này đã có phiếu %s đang chờ ghi sổ. Ghi sổ hoặc bỏ phiếu đó "
			"trước, rồi mới lập phiếu mới." % da_co
		)

	# Dien lai nhom mon VA ton tren so tu co so du lieu truoc khi soat.
	# Xem `_nhom_that` va `_ton_that`: app gui gi cung khong tin.
	ds_ma = [(d or {}).get("ma") for d in (dong or [])]
	nhom_that = _nhom_that(ds_ma)
	ton_that = _ton_that(kho, ds_ma)
	for d in dong or []:
		if d:
			ma = (d.get("ma") or "").strip()
			d["nhom"] = nhom_that.get(ma, "")
			d["ton_so"] = ton_that.get(ma, 0)

	se_ghi, nhac = soat_bang_dem(dong)
	nhac += thieu_gi(bo_phan_chiu, len(se_ghi))
	if nhac:
		frappe.throw(" ".join(nhac))
	xuat_kho._chan_qua_ton(kho, se_ghi)

	ct = xuat_kho._cong_ty()
	viet_tat = frappe.db.get_value("Company", ct, "abbr") or ""
	ma_tt = bo_phan.ten_that(bo_phan_chiu, viet_tat)
	if not frappe.db.exists("Cost Center", ma_tt):
		frappe.throw(
			"Bộ phận %s chưa có trong hệ thống. Báo anh Việt để máy dựng lại "
			"cây bộ phận." % bo_phan_chiu
		)

	ten_kho = frappe.db.get_value("Warehouse", kho, "warehouse_name") or kho
	doc = frappe.new_doc("Stock Entry")
	doc.stock_entry_type = xuat_kho.LOAI["huy"]
	doc.purpose = xuat_kho.LOAI["huy"]
	doc.company = ct
	doc.posting_date = nowdate()
	doc.set_posting_time = 0
	doc.from_warehouse = kho
	doc.vgb_muc_dich_xuat = MA_MUC_DICH
	doc.remarks = ghi_chu_phieu(ten_kho, bo_phan_chiu, ghi_chu)

	tk_theo_nhom = {}
	for d in se_ghi:
		g = d["nhom"]
		if g not in tk_theo_nhom:
			tk_theo_nhom[g] = _tk_theo_nhom(ct, g)
		doc.append(
			"items",
			{
				"item_code": d["ma"],
				"qty": d["sl"],
				"s_warehouse": kho,
				"expense_account": tk_theo_nhom[g],
				"cost_center": ma_tt,
			},
		)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": 1,
		"name": doc.name,
		"so_dong": len(se_ghi),
		"trang_thai": "Chờ ghi sổ",
	}


@frappe.whitelist()
def ghi_so(name=None):
	"""Ke toan ghi so - toi day ton moi thuc su tru."""
	if not xuat_kho.duoc_duyet():
		frappe.throw(
			"Chỉ kế toán hoặc quản lý kho mới ghi sổ được phiếu xuất kho "
			"phục vụ bán hàng."
		)
	doc = frappe.get_doc("Stock Entry", name)
	if doc.docstatus != 0:
		frappe.throw("Phiếu này không còn ở trạng thái bản nháp.")
	if (doc.get("vgb_muc_dich_xuat") or "").strip() != MA_MUC_DICH:
		frappe.throw(
			"Phiếu này không phải phiếu xuất kho phục vụ bán hàng. Ghi sổ nó "
			"ở đúng màn đã lập ra nó."
		)
	if cint(doc.get("vgb_huy")):
		frappe.throw(
			"Phiếu này đã bỏ nên không ghi sổ được. Lý do: %s."
			% (doc.get("vgb_huy_ly_do") or "không ghi")
		)
	doc.flags.ignore_permissions = True
	doc.submit()
	frappe.db.commit()
	return {"ok": 1, "name": doc.name, "trang_thai": "Đã ghi sổ"}


@frappe.whitelist()
def ds_phieu(gioi_han=40):
	"""Danh sach phieu cua RIENG man nay.

	Loc bang dung ma cua man, khong loc kieu "o nay co gia tri": loc kieu do
	la keo luon phieu cua man Xuat dung noi bo sang.
	"""
	xuat_kho._duoc_xuat()
	ds = frappe.get_all(
		"Stock Entry",
		filters={
			"purpose": xuat_kho.LOAI["huy"],
			"docstatus": ["<", 2],
			"vgb_huy": 0,
			"vgb_muc_dich_xuat": MA_MUC_DICH,
		},
		fields=[
			"name",
			"posting_date",
			"docstatus",
			"from_warehouse",
			"total_outgoing_value",
			"owner",
			"remarks",
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
	"""Mot phieu kem cac dong hang."""
	xuat_kho._duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	tt = ""
	for d in doc.items:
		if d.get("cost_center"):
			tt = d.get("cost_center")
			break
	anh = xuat_kho.anh_theo_ma([d.item_code for d in doc.items])
	nhom = _nhom_that([d.item_code for d in doc.items])
	nhan_nhom = {n["nhom"]: n["nhan"] for n in NHOM}
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
		"bo_phan": tt,
		"ghi_chu": doc.remarks or "",
		"nguoi_tao": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		# Codex bat tren PR #341: khong co hai o nay thi man xem phieu
		# khong bao gio noi duoc ai da tru kho. Ghi so la lan sua cuoi cung
		# cua mot to da ghi so, nen modified_by/modified chinh la nguoi va luc.
		"nguoi_ghi_so": (
			(frappe.db.get_value("User", doc.modified_by, "full_name") or doc.modified_by)
			if doc.docstatus == 1 else ""
		),
		"luc_ghi_so": str(doc.modified or "")[:16] if doc.docstatus == 1 else "",
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
				"nhan": nhan_nhom.get(nhom.get(d.item_code, ""), ""),
				"anh": anh.get(d.item_code, ""),
			}
			for d in doc.items
		],
	}


@frappe.whitelist()
def bo_phieu(name=None, ly_do=None):
	"""Bo mot phieu nhap dang sai - chi nguoi tao hoac nguoi duoc ghi so.

	Khong xoa vinh vien, chi danh dau da huy: khong chung tu nao trong he
	thong nay duoc xoa han (QT-20).
	"""
	xuat_kho._duoc_xuat()
	doc = frappe.get_doc("Stock Entry", name)
	# Codex bat tren PR #341: khong co dong nay thi cua nay bo duoc ca
	# phieu xuat dung noi bo hay phieu dieu chuyen nhap cua nguoi khac.
	if (doc.get("vgb_muc_dich_xuat") or "").strip() != MA_MUC_DICH:
		frappe.throw(
			"Phiếu này không phải phiếu xuất kho phục vụ bán hàng. Bỏ nó ở "
			"đúng màn đã lập ra nó."
		)
	if doc.docstatus != 0:
		frappe.throw("Phiếu đã ghi sổ thì phải huỷ đúng nghiệp vụ bên máy tính.")
	if doc.owner != frappe.session.user and not xuat_kho.duoc_duyet():
		frappe.throw("Chỉ người tạo phiếu hoặc kế toán mới bỏ được phiếu này.")
	if cint(doc.get("vgb_huy") or 0):
		return {"ok": 1, "da_huy_tu_truoc": 1}
	chung_tu.danh_dau_huy(doc, ly_do or "Bỏ phiếu nháp sai")
	return {"ok": 1, "da_huy": 1}
