"""Tra hang va hoan tien cho khach.

Chot voi anh Viet va chi Dung 16/08/2026.

Vi sao boc lai nut Return cua ERPNext chu khong viet lai tu dau
--------------------------------------------------------------
ERPNext da co san hoa don tra hang (is_return, return_against) va no dung
ve ke toan. Viet lai tu dau la tu de ra mot he ke toan thu hai chay song
song, va hai he do se lech nhau vao mot ngay khong ai doan truoc.

Nhung de nguyen thi thieu ba thu ma nghiep vu banh can:
  1. No tra hang ve DUNG KHO DA XUAT. Nghia la cai banh khach tra vi di
     ung se nam trong kho ban va duoc ban lai cho nguoi tiep theo. Voi
     nganh banh day khong phai loi so sach, day la chuyen co the lam ai
     do nhap vien.
  2. No khong hoi ly do.
  3. No khong biet gi ve so diem.

Nen ham o day lam ba viec do, roi giao phan ke toan lai cho ERPNext.

Dong tien (chi Dung chot 16/08/2026)
------------------------------------
Tien hoan cho khach di THANG tu tai khoan ngan hang cong ty (MB Bank),
KHONG di qua quy tam ung OCB nua. Ly do: quy OCB tro vao tai khoan 1411
Tam ung ca nhan, nen hoan tien qua do thi moi lan tra khach mot cai banh
hong lai thanh "anh Viet tam ung them mot khoan", va sau mot nam so du
1411 phinh len bang nhung thu khong phai tam ung.

Phieu chi de o trang thai NHAP. May khong ghi so ho: luc do tien chua that
su chuyen di. Ke toan mo phieu, chuyen khoan that, dinh kem uy nhiem chi,
roi moi ghi so.
"""

import json
import re

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate

from vagabond.lib import cfg, sdt

DT = "Vagabond Hoan Tien"
SI = "Sales Invoice"
PE = "Payment Entry"

TEN_KHO_HUY = "Kho Hàng Hủy"
# Cu phap noi dung chuyen khoan, anh Viet chot 16/08/2026.
#
# Doi tu "HT <ma>" sang chuoi day du: dong sao ke ngan hang chi co mot o
# noi dung, va do la thu duy nhat ke toan doc duoc sau ba thang. "HT" thi
# ngan gon nhung khong ai doan ra la gi; "THE VAGABOND HOAN TIEN" thi
# nhin phat biet ngay.
TIEN_TO_CK = "THE VAGABOND HOAN TIEN"

LY_DO = ("Khach doi y", "Banh hong", "Di ung", "Giao sai mon", "Giao tre", "Khac")

# Ly do nao thi hang chac chan KHONG dung lai duoc nua. Ca sau nay deu vao
# kho huy het, nhung ba ly do nay con dung de bao cao ty le hong cho bep.
LY_DO_HONG = {"Banh hong", "Di ung", "Giao sai mon"}

# --------------------------------------------------- tien nop thua
#
# Anh Viet 18/08/2026: *"anh nho em thiet ke luon 1 nut rieng ke ben nut
# Hoan tien do la nut Chuyen lai cho khach thanh toan du... cung co nhieu
# truong hop nhu vay, vi du khach chuyen bao gom ca tien ship nhung ma sau
# do doi y muon den tiem pickup, can chuyen lai cho khach phan tien ship bi
# du ra"*.
#
# VI SAO PHAI TACH RIENG KHOI LUONG HOAN TIEN
#
# Luong hoan tien hien co duoc dung cho TRA HANG: khach tra banh ve, minh
# tra tien lai, doanh thu phai khu di dung phan hang quay ve. Voi ca do thi
# lap hoa don tra hang la dung.
#
# Tien nop thua khong phai tra hang. Khach nhan du hang, gia dung, doanh
# thu dung. Khach chi chuyen du tien. Khoan du do la tien minh GIU HO khach
# va phai tra lai, khong phai doanh thu bi khu.
#
# Ca 91433 ngay 18/08/2026 la vi du: khach dat banh 18cm chuyen 1.100.000,
# bep thieu nguyen lieu nen xin doi xuong 16cm con 915.000, hoa don dien tu
# 10609 da xuat DUNG 915.000. Neu chay duong tra hang thi so ghi doanh thu
# 730.000 trong khi to hoa don ghi 915.000, lech dung 185.000, va tu do
# sinh ra ap luc di sua mot to hoa don DANG DUNG cho khop mot con so DANG
# SAI. Anh Viet da tu choi phieu do va chuyen sang duong nay.
LY_DO_DU = (
	"Doi size nho hon",
	"Khach tu den lay, khong giao",
	"Bo bot mon",
	"Chuyen du tien",
	"Khac",
)

LOAI_TRA_HANG = "Tra hang"
LOAI_TIEN_DU = "Tien nop thua"


def tran_tien_du(da_nhan, tong_don):
	"""So tien du toi da duoc phep chuyen lai. THUAN.

	Tra ve (duoc, tran, cau_nhac). Tran chinh la phan khach chuyen VUOT
	tong don. Chan cung o may chu chu khong tin o nhap tren man (QT-19).

	Vi sao khong lay tran bang tong don nhu luong tra hang: tra hang thi
	toi da tra lai ca don, con tien du thi toi da chi bang dung phan du.
	Cho vuot qua la chi mot khoan chua bao gio nhan duoc.
	"""
	nhan, tong = flt(da_nhan), flt(tong_don)
	du = round(nhan - tong, 0)
	if tong <= 0:
		return False, 0.0, "Đơn này tổng tiền bằng 0 nên không tính được phần dư."
	if du <= 0.5:
		return False, 0.0, (
			"Đơn này chưa nhận dư đồng nào: đã nhận %s đ, đơn %s đ. Nếu khách "
			"trả hàng thì dùng nút Hoàn tiền, còn nếu tiền vừa về mà máy chưa "
			"thấy thì chờ đối soát rồi mở lại màn này."
			% (_tien_vn(nhan), _tien_vn(tong))
		)
	return True, du, ""


def _tien_da_nhan(si):
	"""Tien SePay da nhan cho mot hoa don. Khong doc duoc thi tra 0."""
	try:
		from vagabond.ban_hang import _sepay_theo_don, cfg

		ma = str(si.get("custom_pancake_display_id") or "").strip()
		if not ma:
			return 0.0
		g = _sepay_theo_don(cfg().pancake_shop_id, [ma]).get(ma)
		return flt((g or {}).get("nhan"))
	except Exception:
		return 0.0


TRUONG_MOI = {
	# Tu choi hoan tien (anh Viet 18/08/2026): "phong truong hop khach doi y
	# hoac bang chung khong hop le". QT-20 cam xoa vinh vien, nen tu choi la
	# huy MEM co ghi vet: ai tu choi, luc nao, vi ly do gi. Ba truong nay
	# la ban ghi vet do.
	DT: [
		{
			# De trong doc la "Tra hang": moi phieu lap truoc 18/08/2026 deu
			# la phieu tra hang, va khong co lenh nao chay len du lieu cu.
			"fieldname": "loai_hoan", "label": "Loại phiếu",
			"fieldtype": "Select", "insert_after": "so_tien",
			"options": "\n".join(("", LOAI_TRA_HANG, LOAI_TIEN_DU)),
			"read_only": 1,
			"description": (
				"Trả hàng thì khử doanh thu bằng hoá đơn trả hàng. Tiền nộp thừa "
				"thì KHÔNG đụng doanh thu, chỉ trả lại khoản khách chuyển dư."
			),
		},
		{
			"fieldname": "sec_tc", "label": "Từ chối hoàn tiền",
			"fieldtype": "Section Break", "insert_after": "noi_dung_ck",
		},
		{
			"fieldname": "ly_do_tu_choi", "label": "Lý do từ chối",
			"fieldtype": "Small Text", "insert_after": "sec_tc", "read_only": 1,
			"description": "Bắt buộc điền khi bấm Từ chối. In lại trên màn chi tiết.",
		},
		{
			"fieldname": "nguoi_tu_choi", "label": "Người từ chối",
			"fieldtype": "Data", "insert_after": "ly_do_tu_choi", "read_only": 1,
		},
		{
			"fieldname": "ngay_tu_choi", "label": "Ngày từ chối",
			"fieldtype": "Datetime", "insert_after": "nguoi_tu_choi", "read_only": 1,
		},
	],
	"Payment Entry": [
		{
			"fieldname": "vgb_hoan_tien",
			"label": "Phiếu chi hoàn tiền khách",
			"fieldtype": "Link",
			"options": DT,
			"insert_after": "reference_no",
			"read_only": 1,
			"description": (
				"Phiếu chi sinh từ luồng hoàn tiền. Phiếu mang cờ này thì bắt buộc "
				"phải đính kèm uỷ nhiệm chi mới ghi sổ được."
			),
		}
	]
}


# ------------------------------------------------------------------ cai dat


def _cd():
	"""Kho huy va tai khoan chi. Roi ve mac dinh khi Cai dat chua khai."""
	try:
		c = cfg()
	except Exception:
		return {"kho_huy": "", "tk_chi": ""}
	return {
		"kho_huy": (c.get("kho_hang_huy") or "").strip(),
		"tk_chi": (c.get("tk_hoan_tien") or "").strip(),
	}


def _cong_ty(si=None):
	if si and si.get("company"):
		return si["company"]
	return frappe.defaults.get_global_default("company") or ""


def kho_huy(cong_ty=None):
	"""Kho Hang Huy dang dung. Tu tao neu chua co."""
	ten = _cd()["kho_huy"]
	if ten and frappe.db.exists("Warehouse", ten):
		return ten
	return dung_kho_huy(cong_ty)


def dung_kho_huy(cong_ty=None):
	"""Tao kho Hang Huy neu chua co. LAP LAI DUOC, goi bao nhieu lan cung duoc.

	Goi tu patch dong_bo_cau_truc nen moi lan Migrate deu duoc dung lai.

	Kho nam TRUC TIEP duoi All Warehouses chu khong duoi bep nao: hang huy
	khong thuoc bep nao ca, va de duoi mot bep thi bao cao ton kho cua bep
	do se mang theo hang da chet.
	"""
	cty = cong_ty or _cong_ty()
	if not cty:
		return ""
	viet_tat = frappe.db.get_value("Company", cty, "abbr") or ""
	ten_day_du = "%s - %s" % (TEN_KHO_HUY, viet_tat) if viet_tat else TEN_KHO_HUY
	if frappe.db.exists("Warehouse", ten_day_du):
		return ten_day_du
	# Co the ai do da tao tay voi ten khac hoa; tim theo warehouse_name truoc.
	cu = frappe.db.get_value("Warehouse", {"warehouse_name": TEN_KHO_HUY, "company": cty}, "name")
	if cu:
		return cu
	goc = frappe.db.get_value("Warehouse", {"company": cty, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": TEN_KHO_HUY,
			"company": cty,
			"is_group": 0,
			"parent_warehouse": goc,
			"disabled": 0,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.name


def tk_chi(cong_ty=None):
	"""Tai khoan ngan hang CONG TY dung de chi hoan tien.

	Chi Dung chot 16/08/2026: MB Bank, khong dung quy tam ung OCB.

	Neu Cai dat chua khai thi tu tim mot Bank Account cua cong ty. KHONG
	roi ve tai khoan bat ky: chi nham tai khoan la tien ra khoi mot noi
	khong ai theo doi.
	"""
	ten = _cd()["tk_chi"]
	if ten and frappe.db.exists("Bank Account", ten):
		return ten
	cty = cong_ty or _cong_ty()
	ds = frappe.get_all(
		"Bank Account",
		filters={"company": cty, "is_company_account": 1},
		fields=["name", "account"],
		limit_page_length=0,
	)
	# Uu tien tai khoan tro vao 112x (tien gui ngan hang) chu khong phai
	# 1411 (tam ung ca nhan) - day chinh la cho chi Dung vua be lai.
	for d in ds:
		if str(d.get("account") or "").strip().startswith("112"):
			return d["name"]
	return ds[0]["name"] if ds else ""


# --------------------------------------------------------------- phep tinh
#
# Hai ham THUAN, khong doc co so du lieu. Bo kiem thu chay duoc khong can site.


def noi_dung_ck(ma_hoa_don):
	"""Noi dung chuyen khoan ke toan go vao MB Biz. THUAN.

	Cu phap anh Viet chot 16/08/2026:

	    THE VAGABOND HOAN TIEN <ma hoa don goc>

	Vi sao mang ma HOA DON GOC chu khong mang ma phieu HT-: ke toan, khach,
	va ca nguoi doc sao ke sau nay deu tra cuu theo ma don. Mot dong sao ke
	ghi "HT-2026-00775" thi khong ai biet la cua don nao neu khong tra bang.

	Vi sao doi soat theo NOI DUNG chu khong theo SO TIEN: hai khach cung
	duoc hoan 250.000 d trong mot ngay la chuyen thuong, do theo so tien la
	khop nham.
	"""
	return "%s %s" % (TIEN_TO_CK, str(ma_hoa_don or "").strip())


# Ma hoa don tren he co HAI dang, va day la cho de sai nhat cua ca luong
# doi soat. Em dem 16/08/2026 tren 43.458 hoa don:
#
#     HDB-2026-01593     dang cu,  HAI nhom so   - chiem phan lon
#     HDB-26-08-00323    dang moi, BA nhom so
#
# Anh Viet dua regex HDB-\d+-\d+-\d+; regex do bat dung dang moi va BO SOT
# toan bo dang cu. Nen o day noi thanh 1 den 3 nhom so, va van chan hai dau
# de "HDB-2026-0160" khong an nham giao dich cua "HDB-2026-01604" - dung
# cai bay da gap voi ma WOO.
RX_MA_HD = re.compile(r"(?<![0-9A-Za-z])(HDB-[0-9]+(?:-[0-9]+){1,3})(?![0-9A-Za-z])", re.IGNORECASE)


def _got(chu):
	"""Bo moi ky tu khong phai chu hoac so, roi viet HOA. THUAN.

	Vi sao can: ngan hang khong tra lai noi dung y nguyen. Cung mot lenh
	chi, sao ke co the ve thanh "THE VAGABOND HOAN TIEN HDB 26 08 00323"
	(mat dau gach), hoac dinh them ma tham chieu o hai dau. So hai chuoi
	tho voi nhau la truot.
	"""
	return re.sub(r"[^0-9A-Za-z]+", "", str(chu or "")).upper()


def tim_ma_hoa_don(mo_ta):
	"""Doc mot dong sao ke, tra ve ma hoa don nam trong do. THUAN.

	Tra chuoi rong neu khong thay. Dung cho duong SePay quet tien RA: doc
	dong tien roi tu tim xem no thuoc phieu nao, khong can biet truoc.
	"""
	m = RX_MA_HD.search(str(mo_ta or ""))
	return m.group(1).upper() if m else ""


def khop_giao_dich(mo_ta, ma_hoa_don):
	"""Mot dong sao ke co phai la lenh chi cua don nay khong. THUAN.

	Xet HAI duong, trung mot duong la khop:
	  1. Doc thang ma hoa don trong mo ta, khi dau gach con nguyen.
	  2. So sau khi got het ky tu ngan cach, bat duoc ca dong bi ngan hang
	     lam mat dau gach.
	"""
	ma = str(ma_hoa_don or "").strip()
	if not ma:
		return False
	if tim_ma_hoa_don(mo_ta).upper() == ma.upper():
		return True
	g_ma, g_mo = _got(ma), _got(mo_ta)
	if not g_ma or g_ma not in g_mo:
		return False
	# Chan hai dau tren ban da got: ma ngan khong duoc an nham ma dai.
	vt = g_mo.find(g_ma)
	sau = g_mo[vt + len(g_ma):vt + len(g_ma) + 1]
	return not sau.isdigit()


def chon_ma_khop(mo_ta, ds_ma):
	"""Trong danh sach ma dang cho, ma nao khop voi dong sao ke nay. THUAN.

	Tra chuoi rong neu khong ma nao khop.

	Vi sao co ham nay, va day la lan thu BA trong ngay 16/08/2026
	------------------------------------------------------------
	Sang nay mat mot ban va vi hai cho dinh tuyen chep gan giong nhau roi
	lech nhau. Chieu nay lai suyt chep regex vao bo kiem. Va toi nay, khi
	chay thu tren he ngay sau khi deploy v192, phat hien dung cai do lan
	nua: hai duong doi soat cung mot viec nhung dung hai phep khac nhau.

	    doi_soat()       chay theo gio, doc Bank Transaction -> khop_giao_dich
	    sepay_tien_ra()  SePay goi thang                     -> tim_ma_hoa_don

	khop_giao_dich co duong got nen bat duoc dong bi ngan hang lam mat dau
	gach. tim_ma_hoa_don thi khong. Nen cung mot dong tien, vao duong nay
	thi khop, vao duong kia thi thanh mo coi.

	Nay ca hai duong deu di qua ham nay. Mot phep, mot cho.
	"""
	mo = str(mo_ta or "")
	if not mo:
		return ""
	# Uu tien doc thang ma trong mo ta: nhanh, va chac chan dung khi dau
	# gach con nguyen.
	ma = tim_ma_hoa_don(mo)
	if ma and ma in {str(x or "").upper() for x in (ds_ma or [])}:
		return ma
	# Khong doc duoc thi doi chieu tung ma dang cho, qua duong got.
	for x in ds_ma or []:
		if khop_giao_dich(mo, x):
			return str(x)
	return ""


def ty_le_hop_le(so_tien_hoan, tong_don):
	"""So tien hoan nay co nam trong tong don khong. THUAN.

	Tra (duoc, cau_nhac). Chan cung o may chu chu khong tin o nhap tren man
	(QT-19). Cau nhac viet theo QT-24: noi ro nguoi dung lam gi tiep.
	"""
	tien, tong = flt(so_tien_hoan), flt(tong_don)
	if tong <= 0:
		return False, "Đơn này tổng tiền bằng 0 nên không có gì để hoàn."
	if tien <= 0:
		return False, "Số tiền hoàn phải lớn hơn 0. Nhập lại giúp em."
	if tien > tong + 0.5:
		return False, (
			"Số tiền hoàn %s đ lớn hơn tổng đơn %s đ. Sửa lại số tiền cho nhỏ hơn "
			"hoặc bằng tổng đơn rồi gửi lại."
			% ("{:,.0f}".format(tien).replace(",", "."), "{:,.0f}".format(tong).replace(",", "."))
		)
	return True, ""


# --------------------------------------------------------------- viec chinh


@frappe.whitelist()
def tao(
	si_name=None,
	ly_do=None,
	dien_giai="",
	so_tien=0,
	ten_tk="",
	so_tk="",
	ngan_hang="",
	sdt_khach="",
	tep=None,
	otp=None,
):
	"""Sales gui YEU CAU hoan tien. Chua sinh chung tu, chua dong tien nao.

	Anh Viet chot 16/08/2026: doi tu luong "bam la xong" sang luong CO DUYET
	--------------------------------------------------------------------
	Truoc do mot cu bam la sinh ngay bon thu: hoa don tra, but diem, phieu
	kho, phieu chi. Doi lai bang mot ma PIN quan ly go tai quay.

	Nay tach lam hai nhip:
	  Nhip 1 (ham nay)  - Sales lap YEU CAU. Khong sinh chung tu nao het.
	  Nhip 2 (_sinh_chung_tu) - chi chay khi SePay bao TIEN DA RA THAT.

	Vi sao bo ma PIN: PIN o quay chan duoc mot nguoi go nham, nhung no khong
	chan duoc mot khoan chi sai - vi luc go PIN thi tien van chua di dau ca.
	Cua duyet that nam o ke toan, la nguoi cam tay chuyen khoan. Nen cai
	phai bat buoc khong phai ma PIN ma la BANG CHUNG: anh chup khach phan
	anh, anh banh hong. Khong co anh thi khong gui duoc yeu cau.

	Va vi sao chung tu doi den luc tien ra moi sinh: yeu cau bi tu choi giua
	chung la chuyen thuong. Sinh hoa don tra tu dau roi bi tu choi thi phai
	di huy mot to da ghi so, tuc la de lai vet trong so sach cho mot viec
	chua bao gio xay ra.
	"""
	from vagabond.ban_hang import _kiem_quyen

	# KHONG con hoi ma PIN (anh Viet chot 16/08/2026). Tham so otp giu lai
	# de man cu goi vao khong vo, nhung khong dung den.
	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_tra_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO:
		frappe.throw("Phải chọn lý do hoàn. Chọn một trong: %s." % ", ".join(LY_DO))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao hoàn. Gõ vào ô Diễn giải giúp em.")

	# TRAN SO TIEN TINH LAI O MAY CHU (QT-19). Man co chan roi, nhung con so
	# di qua duong mang thi khong tin duoc.
	tien = flt(so_tien) or flt(si.grand_total)
	duoc, nhac = ty_le_hop_le(tien, flt(si.grand_total))
	if not duoc:
		frappe.throw(nhac)

	tk = re.sub(r"\s+", "", str(so_tk or ""))
	if not tk or not (ten_tk or "").strip() or not (ngan_hang or "").strip():
		frappe.throw(
			"Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân hàng, số tài "
			"khoản và tên chủ tài khoản của khách rồi gửi lại."
		)

	# BANG CHUNG BAT BUOC. Ke toan ngoi xa quay, khong nhin thay cai banh
	# hong, nen cai duy nhat ho co de quyet la anh chup.
	anh = _doc_tep(tep)
	if not anh:
		frappe.throw(
			"Phải đính kèm ít nhất một ảnh làm căn cứ (ảnh khách phản ánh, hoặc ảnh "
			"bánh hỏng). Bấm nút thêm ảnh ở ô Bằng chứng rồi gửi lại."
		)

	ho_so = frappe.get_doc(
		{
			"doctype": DT,
			"hoa_don": si.name,
			"khach": si.customer,
			"so_tien": tien,
			"ly_do": ly_do,
			"dien_giai": (dien_giai or "").strip(),
			"trang_thai": "Cho chi",
			"ten_tk": (ten_tk or "").strip(),
			"so_tk": tk,
			"ngan_hang": (ngan_hang or "").strip() or None,
			"sdt": sdt(sdt_khach) or "",
			"nguoi_duyet": frappe.session.user,
			"cach_duyet": "Gui duyet tu man Chi tiet don",
			"noi_dung_ck": noi_dung_ck(si.name),
		}
	)
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	dinh = _dinh_kem(ho_so.name, anh)
	frappe.db.commit()

	da_gui, nguoi_nhan = _bao_ke_toan(ho_so, si)

	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"tong_don": flt(si.grand_total),
		"mot_phan": 1 if tien < flt(si.grand_total) - 0.5 else 0,
		"so_anh": dinh,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"da_bao_ke_toan": da_gui,
		"nguoi_nhan": nguoi_nhan,
		"canh_bao_hddt": (si.get("custom_hddt_so") or "").strip(),
	}


@frappe.whitelist()
def xem_tien_du(si_name=None):
	"""Don nay dang du bao nhieu tien. Cho man hinh hoi TRUOC khi mo form.

	Tra ve du con so de man hinh giai thich cho sales hieu vi sao duoc hoac
	khong duoc, thay vi chi bao mot cau cut ngun.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_tien_du(nhan, flt(si.grand_total))
	cu = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]},
		["name", "trang_thai", "so_tien", "loai_hoan"], as_dict=True,
	)
	return {
		"duoc": 1 if duoc and not cu else 0,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"ly_do": list(LY_DO_DU),
		"da_co": cu or None,
		"vi_sao": (
			("Đơn này đã có phiếu %s đang ở trạng thái \"%s\", xử lý xong phiếu đó rồi mới lập phiếu mới được."
			 % (cu["name"], cu["trang_thai"])) if cu else nhac
		),
		"canh_bao_hddt": (si.get("custom_hddt_so") or "").strip(),
	}


@frappe.whitelist()
def tao_tien_du(
	si_name=None,
	ly_do=None,
	dien_giai="",
	so_tien=0,
	ten_tk="",
	so_tk="",
	ngan_hang="",
	sdt_khach="",
	tep=None,
):
	"""Sales lap yeu cau CHUYEN LAI TIEN KHACH NOP THUA.

	Anh Viet 18/08/2026 chot: chi Dung duyet nhu hoan tien. Nen phieu nay di
	dung mot cua duyet voi phieu tra hang, cung vao mot danh sach cho chi,
	cung ra tien tu tai khoan MB cong ty, cung doi soat SePay.

	KHAC phieu tra hang o hai cho.

	Mot, TRAN. Tra hang thi toi da tra lai ca don. Tien du thi toi da chi
	bang dung phan khach chuyen VUOT tong don, tinh lai o may chu.

	Hai, ANH KHONG BAT BUOC. Voi tra hang thi anh chup la bang chung duy
	nhat ke toan co de quyet, vi ho ngoi xa quay khong nhin thay cai banh
	hong. Voi tien du thi bang chung nam ngay trong so sach: sao ke bao da
	nhan bao nhieu, hoa don ghi bao nhieu, phan chenh la con so may tu tinh
	ra chu khong ai khai. Bat anh o day la bat mot thu khong noi them dieu gi.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_tra_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO_DU:
		frappe.throw("Phải chọn lý do. Chọn một trong: %s." % ", ".join(LY_DO_DU))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao dư. Gõ vào ô Diễn giải giúp em.")

	# TRAN TINH LAI O MAY CHU (QT-19), khong tin con so man hinh gui len.
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_tien_du(nhan, flt(si.grand_total))
	if not duoc:
		frappe.throw(nhac)
	tien = flt(so_tien) or tran
	if tien > tran + 0.5:
		frappe.throw(
			"Số tiền chuyển lại (%s đ) lớn hơn phần khách nộp dư (%s đ). Đơn này "
			"đã nhận %s đ, giá trị đơn %s đ. Sửa lại số tiền cho đúng phần dư, "
			"hoặc nếu khách trả hàng thì dùng nút Hoàn tiền."
			% (_tien_vn(tien), _tien_vn(tran), _tien_vn(nhan), _tien_vn(si.grand_total))
		)

	tk = re.sub(r"\s+", "", str(so_tk or ""))
	if not tk or not (ten_tk or "").strip() or not (ngan_hang or "").strip():
		frappe.throw(
			"Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân hàng, số tài "
			"khoản và tên chủ tài khoản của khách rồi gửi lại."
		)

	ho_so = frappe.get_doc({
		"doctype": DT,
		"hoa_don": si.name,
		"khach": si.customer,
		"so_tien": tien,
		"loai_hoan": LOAI_TIEN_DU,
		"ly_do": "Khac",
		"dien_giai": ("[Tiền nộp thừa] %s. %s" % (ly_do, (dien_giai or "").strip())).strip(),
		"trang_thai": "Cho chi",
		"ten_tk": (ten_tk or "").strip(),
		"so_tk": tk,
		"ngan_hang": (ngan_hang or "").strip() or None,
		"sdt": sdt(sdt_khach) or "",
		"nguoi_duyet": frappe.session.user,
		"cach_duyet": "Gui duyet tu man Chi tiet don (tien nop thua)",
		"noi_dung_ck": noi_dung_ck(si.name),
	})
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	anh = _doc_tep(tep)
	dinh = _dinh_kem(ho_so.name, anh) if anh else 0
	frappe.db.commit()

	da_gui, nguoi_nhan = _bao_ke_toan(ho_so, si)
	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"so_anh": dinh,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"da_bao_ke_toan": da_gui,
		"nguoi_nhan": nguoi_nhan,
	}


def _doc_tep(tep):
	"""Chuan hoa danh sach tep tu man gui len. Tra list rong neu khong co."""
	if not tep:
		return []
	if isinstance(tep, str):
		try:
			tep = json.loads(tep)
		except Exception:
			return []
	if isinstance(tep, dict):
		tep = [tep]
	ra = []
	for t in tep or []:
		if not isinstance(t, dict):
			continue
		if (t.get("noi_dung") or "").strip():
			ra.append({"ten": (t.get("ten") or "bang-chung.jpg").strip(), "noi_dung": t["noi_dung"]})
	return ra


def _dinh_kem(ma_ho_so, anh):
	"""Ghi anh bang chung vao ho so. Tra so tep dinh duoc.

	Loi mot tep khong duoc lam do ca yeu cau: ho so da lap roi, va Sales
	dinh bu duoc tep con thieu tren man danh sach.
	"""
	n = 0
	for a in anh:
		try:
			noi = a["noi_dung"]
			if "," in noi and noi[:5] in ("data:", "DATA:"):
				noi = noi.split(",", 1)[1]
			f = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": a["ten"],
					"attached_to_doctype": DT,
					"attached_to_name": ma_ho_so,
					"content": noi,
					"decode": True,
					"is_private": 1,
				}
			)
			f.flags.ignore_permissions = True
			f.insert(ignore_permissions=True)
			n += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hoan_tien: dinh kem bang chung loi")
	return n


VAI_KE_TOAN = ("Accounts Manager", "Accounts User")


def _bao_ke_toan(ho_so, si):
	"""Gui thu bao ke toan co yeu cau hoan tien moi. Tra (da_gui, danh_sach).

	Anh Viet chot 16/08/2026: gui cho MOI nguoi mang vai tro ke toan tren
	he, khong khai dia chi co dinh. Ai duoc them vai tro sau nay thi tu
	dong nhan, khong phai sua ma.

	Ham nay KHONG BAO GIO nem loi: ho so da lap xong roi, may chu thu hong
	thi ke toan van thay yeu cau tren man danh sach. Nem loi o day la lam
	hong mot viec da thanh cong.
	"""
	try:
		nguoi = set()
		for vai in VAI_KE_TOAN:
			for u in frappe.get_all("Has Role", filters={"role": vai}, fields=["parent"], limit_page_length=0):
				nguoi.add(u["parent"])
		mail = []
		for u in nguoi:
			d = frappe.db.get_value("User", u, ["email", "enabled"], as_dict=True)
			if d and cint(d.get("enabled")) and (d.get("email") or "").strip():
				mail.append(d["email"].strip())
		mail = sorted(set(mail))
		if not mail:
			frappe.log_error(
				"Khong tim thay nguoi dung nao mang vai tro ke toan, nen khong gui duoc "
				"thu bao ho so %s." % ho_so.name,
				"hoan_tien: khong co nguoi nhan",
			)
			return 0, []

		tien = "{:,.0f}".format(flt(ho_so.so_tien)).replace(",", ".")
		tong = "{:,.0f}".format(flt(si.grand_total)).replace(",", ".")
		phan = "toàn bộ đơn" if flt(ho_so.so_tien) >= flt(si.grand_total) - 0.5 else "một phần đơn"
		than = (
			"<p>Có một yêu cầu hoàn tiền mới chờ chi.</p>"
			"<table cellpadding='6' style='border-collapse:collapse'>"
			"<tr><td><b>Phiếu</b></td><td>%s</td></tr>"
			"<tr><td><b>Hoá đơn gốc</b></td><td>%s (tổng %s đ)</td></tr>"
			"<tr><td><b>Số tiền hoàn</b></td><td><b>%s đ</b> - %s</td></tr>"
			"<tr><td><b>Lý do</b></td><td>%s%s</td></tr>"
			"<tr><td><b>Người gửi</b></td><td>%s</td></tr>"
			"<tr><td><b>Tài khoản nhận</b></td><td>%s - %s - %s</td></tr>"
			"<tr><td><b>Nội dung chuyển khoản</b></td><td><b>%s</b></td></tr>"
			"</table>"
			"<p>Mở app, vào Bán hàng, Hoàn tiền / Trả hàng để xem ảnh khách gửi kèm "
			"và bấm Xuất thông tin chuyển khoản MB Biz.</p>"
			"<p style='color:#92400e'>Tiền chỉ được ghi sổ sau khi có Uỷ nhiệm chi tải "
			"từ e-banking đính kèm. Dòng sao kê SePay chỉ để biết tiền đã đi chưa.</p>"
		) % (
			ho_so.name,
			si.name,
			tong,
			tien,
			phan,
			frappe.utils.escape_html(ho_so.ly_do or ""),
			(": " + frappe.utils.escape_html(ho_so.dien_giai)) if ho_so.dien_giai else "",
			frappe.utils.escape_html(ho_so.nguoi_duyet or ""),
			frappe.utils.escape_html(ho_so.ten_tk or ""),
			frappe.utils.escape_html(ho_so.so_tk or ""),
			frappe.utils.escape_html(str(ho_so.ngan_hang or "")),
			frappe.utils.escape_html(ho_so.noi_dung_ck or ""),
		)
		frappe.sendmail(
			recipients=mail,
			subject="[Vagabond] Yêu cầu hoàn tiền %s - %s đ - đơn %s" % (ho_so.name, tien, si.name),
			message=than,
			reference_doctype=DT,
			reference_name=ho_so.name,
			now=False,
		)
		return 1, mail
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: gui thu bao ke toan loi")
		return 0, []


def _kiem_tra_duoc(si):
	"""Hoa don nay con tra duoc khong. Nem loi theo QT-24 neu khong."""
	if cint(si.docstatus) != 1:
		frappe.throw(
			"Hoá đơn %s chưa ghi sổ nên không dùng luồng hoàn tiền. Bill chưa ghi sổ "
			"thì sửa hoặc huỷ thẳng là được." % si.name
		)
	if cint(si.get("vgb_huy")):
		frappe.throw("Hoá đơn %s đã mang dấu huỷ nên không hoàn tiền được." % si.name)
	cu = frappe.db.get_value(SI, {"return_against": si.name, "docstatus": 1}, "name")
	if cu:
		frappe.throw(
			"Hoá đơn %s đã có phiếu trả hàng %s rồi. Mở phiếu đó ra xem, đừng lập "
			"thêm phiếu thứ hai." % (si.name, cu)
		)
	# Yeu cau dang cho ke toan xu thi khong cho gui yeu cau thu hai. Khong
	# co chot nay thi Sales bam hai lan la ke toan nhan hai thu giong nhau
	# va chuyen tien hai lan.
	ho = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]}, ["name", "trang_thai"], as_dict=True
	)
	if ho:
		frappe.throw(
			"Đơn %s đã có yêu cầu hoàn tiền %s đang ở trạng thái \"%s\". Mở màn Hoàn "
			"tiền / Trả hàng để xem, đừng gửi thêm yêu cầu thứ hai."
			% (si.name, ho["name"], ho["trang_thai"])
		)


def _sinh_chung_tu(ho_so):
	"""Nhip 2: TIEN DA RA THAT roi thi moi sinh chung tu.

	Chay tu duong doi soat SePay, khong ai goi tay. Sinh theo dung thu tu:
	  1. Hoa don tra hang  - khu doanh thu dung bang so tien da hoan
	  2. But diem hai chieu - thu hoi diem tang, tra lai diem khach da tieu
	  3. Phieu chuyen kho sang Kho Hang Huy, de NHAP - chi khi hoan TOAN BO
	  4. Phieu chi, de NHAP - ke toan dinh UNC roi moi ghi so

	Vi sao hoan MOT PHAN thi khong lap phieu kho: hoan mot phan nghia la
	khach giu lai banh va duoc bu mot phan tien. Khong co cai banh nao di
	ve kho ca. Lap phieu kho luc do la khai mot duong hang khong ton tai.

	Vi sao phieu chi van de NHAP du tien da di roi: chi Dung chot 16/08 -
	dong sao ke SePay KHONG phai giay bao No hop le, ho so lam viec voi Cuc
	Thue bat buoc co tep Uy nhiem chi tai tu e-banking. Nen may dien san moi
	o, con nut ghi so van nam trong tay ke toan sau khi dinh kem UNC.

	Ham nay chay mot lan cho moi ho so. Da co hoa don tra thi thoat ngay.
	"""
	if ho_so.get("hoa_don_tra"):
		return {"bo_qua": 1, "vi_sao": "Hồ sơ này đã sinh chứng từ rồi."}
	si = frappe.get_doc(SI, ho_so.hoa_don)
	kho = kho_huy(si.company)
	if not kho:
		frappe.log_error("Chua dung duoc Kho Hang Huy", "hoan_tien: sinh chung tu loi")
		return {"bo_qua": 1, "vi_sao": "Chưa dựng được Kho Hàng Hủy."}

	tien = flt(ho_so.so_tien)

	# Phieu TIEN NOP THUA di duong khac han: khong lap hoa don tra hang,
	# khong thu hoi diem, khong phieu kho. Chi mot phieu chi.
	#
	# Vi sao khong khu doanh thu: khach nhan du hang, gia dung, doanh thu
	# dung. Khoan du la tien minh giu ho khach chu khong phai doanh thu.
	# Khu doanh thu de tra mot khoan nop thua la ghi sai ban chat, va se lam
	# so lech voi to hoa don dien tu dang DUNG.
	if (ho_so.get("loai_hoan") or "") == LOAI_TIEN_DU:
		pe = _lap_phieu_chi_du(si, ho_so)
		ho_so.phieu_chi = pe.name if pe else None
		ho_so.dien_giai = (
			(ho_so.dien_giai or "").strip()
			+ ("\n" if ho_so.dien_giai else "")
			+ ("Trả lại tiền khách nộp thừa. KHÔNG lập hoá đơn trả hàng, doanh thu "
			   "của đơn giữ nguyên %s đ và hoá đơn điện tử không phải điều chỉnh."
			   % _tien_vn(si.grand_total))
		).strip()
		ho_so.flags.ignore_permissions = True
		ho_so.save(ignore_permissions=True)
		return {
			"bo_qua": 0, "hoa_don_tra": "", "phieu_kho": "",
			"phieu_chi": ho_so.phieu_chi, "toan_bo": 0, "loai": LOAI_TIEN_DU,
		}

	toan_bo = tien >= flt(si.grand_total) - 0.5

	tra = _lap_hoa_don_tra(si, kho, ho_so.ly_do, ho_so.name, tien)
	ho_so.hoa_don_tra = tra.name

	_thu_hoi_diem(si, tra.name, ho_so.ly_do)

	phieu_kho = ""
	if toan_bo:
		phieu_kho = _chuyen_kho_huy(si, tra, kho, ho_so.ly_do)
	else:
		ho_so.dien_giai = (
			(ho_so.dien_giai or "").strip()
			+ ("\n" if ho_so.dien_giai else "")
			+ "Hoàn một phần nên khách giữ lại hàng, không lập phiếu chuyển Kho Hàng Hủy."
		).strip()

	pe = _lap_phieu_chi(si, tra, ho_so)
	ho_so.phieu_chi = pe.name if pe else None
	ho_so.flags.ignore_permissions = True
	ho_so.save(ignore_permissions=True)
	return {
		"bo_qua": 0,
		"hoa_don_tra": tra.name,
		"phieu_kho": phieu_kho,
		"phieu_chi": ho_so.phieu_chi,
		"toan_bo": 1 if toan_bo else 0,
	}


def _lap_hoa_don_tra(si, kho, ly_do, ma_ho_so, so_tien=0):
	"""Hoa don tra hang, hang ve KHO HANG HUY chu khong ve kho ban.

	Hoan MOT PHAN (anh Viet mo muc 50% ngay 16/08/2026)
	---------------------------------------------------
	Hoan mot phan thi khach GIU LAI banh, chi duoc bu mot phan tien. Nen to
	tra hang phai mang dung so tien hoan chu khong phai ca don.

	Cach lam: ha don gia tung dong theo dung ty le, GIU NGUYEN so luong.
	Co y KHONG dung o chiet khau tong, vi dung chiet khau thi to nay dinh
	dung cai loi em vua tim ra sang nay - duong xuat hoa don dien tu doc
	so tien TRUOC chiet khau, va da lam 213 to xuat cao hon so thuc thu.
	Ha don gia thi moi duong doc ra deu ra cung mot con so.
	"""
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

	tra = make_sales_return(si.name)
	tong = flt(si.grand_total)
	tien = flt(so_tien) or tong
	ty_le = (tien / tong) if tong > 0 else 1.0
	if ty_le < 0.9999:
		for d in tra.items:
			d.rate = flt(d.rate) * ty_le
			d.price_list_rate = flt(d.get("price_list_rate")) * ty_le
			d.discount_amount = 0
			d.discount_percentage = 0
	# update_stock = 0, GIONG HET moi hoa don khac cua he.
	#
	# Ban dau em dat 1 de hang tu chay thang vao kho huy. Chay thu that
	# ngay 16/08/2026 thi ERPNext tu choi:
	#
	#     'Cap nhat kho' khong the chon vi MH khong duoc giao qua HDB-...
	#
	# Doc lai moi hieu: CA HE nay chay update_stock = 0 co chu y - ghi chu
	# dau ban_hang.py noi ro "GIAI DOAN 1 KHONG cap nhat kho, chi ghi doanh
	# thu", kho do kiem banh lo rieng. Ban ra khong tru kho, nen tra ve ma
	# cong kho la CONG KHONG cua ai ca: ton kho phinh len bang so hang von
	# chua bao gio bi tru.
	#
	# Nen to tra hang theo dung nep cua he, con duong hang di vao kho huy
	# tach ra thanh mot phieu chuyen kho rieng - xem _chuyen_kho_huy.
	tra.update_stock = 0
	tra.set_posting_time = 1
	tra.posting_date = nowdate()
	for d in tra.items:
		# Van ghi kho huy len tung dong de doc to nay la biet hang di dau,
		# du dong nay khong sinh but kho nao.
		d.warehouse = kho
		d.target_warehouse = None
	# CHEP LAI CAC TRUONG TU THEM CUA HE.
	#
	# make_sales_return chi chep nhung truong ERPNext biet; cac truong do
	# minh tu them thi no khong biet, nen to tra hang ra doi TRONG khong.
	# Va hook kiem_truoc_khi_luu chan ngay: "Hoa don chua chon nguon don".
	# Bat duoc khi chay thu that 16/08/2026.
	#
	# Chep chu khong dat mac dinh: to tra hang phai doi soat ve dung cai san
	# va dung cai quay ma don goc da ban, khong thi cuoi thang so lieu tra
	# hang khong khop voi so lieu ban ra o bat ky kenh nao.
	for o in (
		"custom_nguon", "vgb_pt_thanh_toan", "vgb_quay", "vgb_khach_no",
		"vgb_so_ban", "vgb_xhd_ten", "vgb_ma_tham_chieu",
	):
		try:
			if si.get(o) is not None and tra.meta.has_field(o):
				tra.set(o, si.get(o))
		except Exception:
			pass
	tra.remarks = ("Trả hàng %s. Lý do: %s. Hồ sơ %s." % (si.name, ly_do, ma_ho_so))[:500]
	tra.flags.ignore_permissions = True
	# Nhip dong bo Pancake khoa mot ma don cho mot hoa don; to tra hang mang
	# cung ma se dinh chot do, nen bo ma di. To tra hang khong phai mot don
	# ban moi.
	tra.custom_pancake_id = None
	tra.insert(ignore_permissions=True)
	tra.submit()
	return tra


def _chuyen_kho_huy(si, tra, kho, ly_do):
	"""Phieu chuyen hang tu kho ban sang Kho Hang Huy. De o trang thai NHAP.

	Vi sao la mot phieu rieng chu khong nam trong hoa don tra
	---------------------------------------------------------
	He nay ban ra KHONG tru kho (update_stock = 0, xem ghi chu dau
	ban_hang.py). Nen neu to tra hang lai cong kho thi ton kho phinh len
	bang so hang von chua bao gio bi tru. Hang van dang nam o kho ban tren
	so sach, va viec dung la CHUYEN no sang kho huy - khong de ra so luong
	moi.

	Vi sao de NHAP: anh Viet viet "cho kiem ke tieu huy". Luc lap phieu thi
	banh con nam tren quay, chua ai dem va chua ai do bo. Kho bam ghi so khi
	that su nhan hang.

	Bo qua mat hang khong theo doi ton kho (ve workshop, phi giao...): ep
	chuyen kho nhung thu do la nem loi vo ich giua mot luong dang chay.
	"""
	try:
		dong = []
		for d in tra.items:
			ma = (d.get("item_code") or "").strip()
			if not ma:
				continue
			if not cint(frappe.db.get_value("Item", ma, "is_stock_item")):
				continue
			nguon = _kho_nguon(si, ma)
			if not nguon or nguon == kho:
				continue
			dong.append(
				{
					"item_code": ma,
					"qty": abs(flt(d.get("qty"))),
					"s_warehouse": nguon,
					"t_warehouse": kho,
				}
			)
		if not dong:
			return ""
		pk = frappe.new_doc("Stock Entry")
		pk.stock_entry_type = "Material Transfer"
		pk.company = si.company
		pk.set_posting_time = 1
		pk.posting_date = nowdate()
		pk.remarks = "Hàng khách trả từ %s (%s), chuyển sang %s chờ kiểm kê tiêu huỷ." % (
			si.name, ly_do, kho,
		)
		for r in dong:
			pk.append("items", r)
		pk.flags.ignore_permissions = True
		pk.insert(ignore_permissions=True)
		return pk.name
	except Exception:
		# Hoa don tra da ghi so roi. Phieu kho hong thi kho lap tay duoc,
		# KHONG duoc nem loi lam hong ca luong hoan tien.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chuyen kho huy loi")
		return ""


def _kho_nguon(si, ma_hang):
	"""Kho hang da nam truoc khi tra. Uu tien kho ghi tren chinh dong ban."""
	for d in si.get("items") or []:
		if (d.get("item_code") or "") == ma_hang and (d.get("warehouse") or ""):
			return d.get("warehouse")
	# Khong co thi lay kho dang con ton nhieu nhat cua mat hang do.
	r = frappe.db.sql(
		"""select warehouse from `tabBin` where item_code = %s and actual_qty > 0
		order by actual_qty desc limit 1""",
		(ma_hang,),
	)
	return r[0][0] if r else ""


def _thu_hoi_diem(si, ma_tra, ly_do):
	"""Rut ve diem quan da tang, va tra lai diem khach da tieu.

	Hai viec nguoc chieu nhau nen phai la hai buoc:
	  - diem quan TANG cho don do  -> rut ve (but am)
	  - diem khach da TIEU tren don -> tra lai (but duong)

	Bat loi rieng tung buoc: thu hoi diem hong khong duoc lam hong ca luong
	tra hang, vi luc do hoa don tra da ghi so roi.
	"""
	from vagabond import diem_otp
	from vagabond.khach_hang import SO_DIEM, _ghi_so_diem, _khach_that

	try:
		kh = _khach_that(si)
		if kh:
			da = frappe.db.sql(
				"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s" % SO_DIEM,
				(si.name, "Tich tu hoa don"),
			)
			diem = flt((da or [[0]])[0][0])
			if diem > 0 and not frappe.db.exists(
				SO_DIEM, {"hoa_don": si.name, "loai": "Hoan lai khi huy hoa don"}
			):
				_ghi_so_diem(
					kh, -diem, "Hoan lai khi huy hoa don", si.name,
					"Khách trả hàng (%s), thu hồi điểm đã tích. Phiếu %s." % (ly_do, ma_tra),
				)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: thu hoi diem tich loi")

	try:
		diem_otp.hoan_diem_don(si.name, "Khách trả hàng (%s), trả lại điểm đã dùng" % ly_do)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: tra lai diem da dung loi")


def _lap_phieu_chi_du(si, ho_so):
	"""Phieu chi tra lai tien khach nop thua, de o trang thai NHAP.

	Khac phieu chi cua luong tra hang o mot diem cot loi: KHONG tro vao mot
	hoa don nao ca. Khoan nay khong gan voi doanh thu cua to hoa don, no la
	tien minh giu ho khach.

	Sau khi ke toan ghi nhan phieu thu du so tien khach da chuyen, ba con so
	tu can: thu 1.100.000, hoa don 915.000, chi 185.000, con no bang 0. Nen
	ham nay khong dung toi doanh thu va khong dung toi to hoa don dien tu.

	De NHAP giong het luong tra hang: chi Dung chot 16/08 rang dong sao ke
	SePay khong phai giay bao No hop le, phai dinh kem uy nhiem chi roi ke
	toan moi bam ghi so.
	"""
	try:
		tk = tk_chi(si.company)
		if not tk:
			frappe.log_error(
				"Chua khai tai khoan ngan hang cong ty", "hoan_tien: khong lap duoc phieu chi du"
			)
			return None
		tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
		if not tk_ke_toan:
			return None
		pe = frappe.new_doc(PE)
		pe.payment_type = "Pay"
		pe.party_type = "Customer"
		pe.party = si.customer
		pe.company = si.company
		pe.posting_date = nowdate()
		pe.paid_from = tk_ke_toan
		pe.paid_amount = flt(ho_so.so_tien)
		pe.received_amount = flt(ho_so.so_tien)
		pe.reference_no = ho_so.noi_dung_ck or noi_dung_ck(si.name)
		pe.reference_date = nowdate()
		pe.vgb_hoan_tien = ho_so.name
		pe.remarks = (
			"Trả lại tiền khách nộp thừa cho đơn %s theo phiếu %s. Khách đã chuyển "
			"dư so với giá trị đơn; doanh thu của đơn giữ nguyên, KHÔNG lập hoá đơn "
			"trả hàng và KHÔNG điều chỉnh hoá đơn điện tử. Nội dung chuyển khoản: %s"
			% (si.name, ho_so.name, ho_so.noi_dung_ck)
		)
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		return pe
	except Exception:
		# Khong duoc nem loi lam hong ca luong: ke toan lap tay duoc.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chi tien du loi")
		return None


def _lap_phieu_chi(si, tra, ho_so):
	"""Phieu chi hoan tien, de o trang thai NHAP.

	Co y de nhap: luc nay tien chua that su chuyen di. May ghi so ho la so
	sach noi da tra tien trong khi tien con nam trong tai khoan.
	"""
	try:
		tk = tk_chi(si.company)
		if not tk:
			frappe.log_error("Chua khai tai khoan ngan hang cong ty", "hoan_tien: khong lap duoc phieu chi")
			return None
		tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
		if not tk_ke_toan:
			return None
		# DUNG get_payment_entry CUA ERPNEXT chu khong tu dung tay.
		#
		# Ban dau em tu dung: dat total_amount, outstanding_amount va
		# allocated_amount deu bang so DUONG. Chay thu that 16/08/2026 thi
		# ERPNext tu choi:
		#
		#     Dong #1: So tien phan bo khong duoc lon hon so du no.
		#
		# Ly do: to TRA HANG mang grand_total AM (-60.000), nen so du no cua
		# no cung am. Doi chieu mot so duong voi mot so am thi con so nao
		# cung "lon hon". Dau cua tung o tren Payment Entry co luat rieng
		# cho hoa don tra hang, va do la luat cua ERPNext chu khong phai cua
		# minh - nen giao lai cho no dung.
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry(SI, tra.name)
		tien = abs(flt(pe.paid_amount)) or abs(flt(tra.grand_total))
		pe.payment_type = "Pay"
		pe.posting_date = nowdate()
		pe.paid_from = tk_ke_toan
		pe.reference_no = ho_so.noi_dung_ck or noi_dung_ck(tra.name)
		pe.reference_date = nowdate()
		pe.vgb_hoan_tien = ho_so.name
		pe.remarks = "Hoàn tiền khách theo phiếu %s, nội dung chuyển khoản: %s" % (
			ho_so.name,
			ho_so.noi_dung_ck,
		)
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		return pe
	except Exception:
		# Hoa don tra da ghi so roi; phieu chi hong thi ke toan lap tay
		# duoc. KHONG duoc nem loi lam hong ca luong.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chi loi")
		return None


# ------------------------------------------------------- chan ghi so phieu chi


def chan_thieu_uy_nhiem_chi(doc, method=None):
	"""Hook before_submit cua Payment Entry.

	Phieu chi sinh tu luong hoan tien ma chua dinh kem uy nhiem chi thi
	khong ghi so duoc. Chan o BACKEND chu khong chi nhac tren man: nhac
	tren man thi bo qua duoc, ma day la chung tu goc de giai trinh.
	"""
	try:
		if not doc.get("vgb_hoan_tien"):
			return
		n = frappe.db.count(
			"File", {"attached_to_doctype": PE, "attached_to_name": doc.name}
		)
		if n:
			return
		from vagabond.chung_tu_tien import ten_chung_tu

		ten = ten_chung_tu(doc.get("payment_type"), doc.get("paid_from"))
		frappe.throw(
			"%s %s là chứng từ hoàn tiền cho khách nên bắt buộc phải có Uỷ nhiệm chi "
			"đính kèm mới ghi sổ được. Tải UNC từ e-banking về, bấm nút kẹp giấy ở góc "
			"phải để đính kèm, rồi ghi sổ lại." % (ten, doc.name)
		)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: kiem uy nhiem chi loi")


def khi_ghi_so_phieu_chi(doc, method=None):
	"""Hook on_submit cua Payment Entry: danh dau ho so da chi."""
	try:
		if not doc.get("vgb_hoan_tien"):
			return
		frappe.db.set_value(DT, doc.vgb_hoan_tien, "trang_thai", "Da chi")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: danh dau da chi loi")


# ------------------------------------------------------------ doi soat SePay


@frappe.whitelist()
def doi_soat(ho_so=None, so_ngay=30):
	"""Tim giao dich CHI tren sao ke ngan hang khop voi phieu hoan tien.

	SePay day sao ke vao `Bank Transaction` cua ERPNext, va cot `withdrawal`
	la tien RA. Duong ong nay da co san tu truoc, o day chi them mach buoc
	giao dich vao dung mot phieu.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	# Phieu da huy hoac bi tu choi KHONG duoc tu khop.
	#
	# Duong SePay goi thang (sepay_tien_ra) da loai "Da huy" tu 16/08, nhung
	# duong chay theo gio o day thi khong - nen mot phieu ke toan vua tu
	# choi ma ngan hang tinh co co dong tien ra trung so tien la may van
	# danh dau da doi soat va SINH LUON phieu chi. Hai duong phai giong
	# nhau, neu khong thi cai chat hon chi la trang tri.
	loc = {"da_doi_soat": 0, "trang_thai": ["!=", "Da huy"]}
	if ho_so:
		loc = {"name": ho_so, "trang_thai": ["!=", "Da huy"]}
	ds = frappe.get_all(
		DT,
		filters=loc,
		fields=["name", "hoa_don", "hoa_don_tra", "so_tien", "trang_thai"],
		limit_page_length=0,
	)
	# Do theo MA HOA DON GOC chu khong theo ma to tra hang.
	#
	# Doi tu 16/08/2026: truoc day noi dung chuyen khoan mang ma to tra hang,
	# nen phieu phai co to tra hang truoc thi moi doi soat duoc. Nay nguoc
	# lai - to tra hang chi sinh SAU khi tien ra - nen moc de do phai la thu
	# ton tai ngay tu luc Sales gui yeu cau, tuc ma hoa don goc.
	ds = [d for d in ds if d.get("hoa_don")]
	if not ds:
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Không có phiếu nào chờ đối soát."}

	try:
		gds = frappe.db.sql(
			"""select name, description, withdrawal, date, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and ifnull(withdrawal, 0) > 0
			  and date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)""",
			(cint(so_ngay) or 30,),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc sao ke loi")
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Chưa đọc được sao kê ngân hàng."}

	da, xem, sinh = 0, [], []
	for d in ds:
		for g in gds:
			mo_ta = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
			if not khop_giao_dich(mo_ta, d["hoa_don"]):
				continue
			# Khop noi dung roi van phai so TIEN. Noi dung dung ma so tien
			# lech nghia la ke toan chuyen thieu hoac thua, va do la viec
			# nguoi phai xem chu khong phai may tu dong danh dau xong.
			if abs(flt(g["withdrawal"]) - flt(d["so_tien"])) > 1:
				xem.append(
					{
						"ho_so": d["name"],
						"hoa_don": d["hoa_don"],
						"tien_phieu": flt(d["so_tien"]),
						"tien_chuyen": flt(g["withdrawal"]),
						"giao_dich": g["name"],
					}
				)
				continue
			frappe.db.set_value(
				DT,
				d["name"],
				{
					"da_doi_soat": 1,
					"ma_gd": g["name"],
					"ngay_doi_soat": now_datetime(),
					"trang_thai": "Da doi soat",
				},
			)
			da += 1
			# TIEN DA RA THAT. Day la moc duy nhat sinh chung tu.
			#
			# Boc rieng tung ho so: mot ho so hong khong duoc keo theo ca me
			# dang quet, vi cac ho so khac da duoc danh dau doi soat roi.
			try:
				ho = frappe.get_doc(DT, d["name"])
				kq = _sinh_chung_tu(ho)
				if not kq.get("bo_qua"):
					kq["ho_so"] = d["name"]
					sinh.append(kq)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(
					frappe.get_traceback(), "hoan_tien: sinh chung tu sau doi soat loi %s" % d["name"]
				)
			break
	frappe.db.commit()
	return {"da_khop": da, "xem_xet": xem[:50], "so_phieu_quet": len(ds), "da_sinh": sinh}


@frappe.whitelist()
def sepay_tien_ra(mo_ta="", so_tien=0, ma_gd=""):
	"""Duong SePay bao mot dong TIEN RA, may tu tim phieu hoan tien khop.

	Anh Viet 16/08/2026: "quet dong tien ra, neu noi dung chua ma hoa don
	thi tu map vao phieu HT- tuong ung".

	Ham nay lam dung viec do cho MOT dong, dung khi SePay goi thang vao.
	Con duong chay theo gio thi van la doi_soat() doc bang Bank Transaction.
	Hai duong dung chung mot phep khop va chung mot buoc sinh chung tu, nen
	khong the lech nhau.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	# Doi chieu voi cac phieu DANG CHO, qua chon_ma_khop - dung phep ma
	# duong chay theo gio dung, khong de hai duong lech nhau.
	cho = frappe.get_all(
		DT, filters={"da_doi_soat": 0, "trang_thai": ["!=", "Da huy"]},
		fields=["name", "hoa_don", "so_tien", "trang_thai"], limit_page_length=0,
	)
	ma = chon_ma_khop(mo_ta, [c["hoa_don"] for c in cho if c.get("hoa_don")])
	if not ma:
		doc_duoc = tim_ma_hoa_don(mo_ta)
		return {
			"khop": 0,
			"ma": doc_duoc,
			"vi_sao": (
				"Không có phiếu hoàn tiền nào đang chờ cho đơn %s." % doc_duoc
				if doc_duoc
				else "Nội dung chuyển khoản không chứa mã hoá đơn nào."
			),
		}
	d = next((c for c in cho if str(c["hoa_don"]).upper() == ma.upper()), None)
	if not d:
		return {"khop": 0, "ma": ma, "vi_sao": "Không có phiếu hoàn tiền nào đang chờ cho đơn %s." % ma}
	if flt(so_tien) and abs(flt(so_tien) - flt(d["so_tien"])) > 1:
		return {
			"khop": 0,
			"ma": ma,
			"ho_so": d["name"],
			"vi_sao": "Số tiền chuyển %s đ lệch với số trên phiếu %s đ. Kế toán mở phiếu ra "
			"xem lại rồi khớp tay." % (
				"{:,.0f}".format(flt(so_tien)).replace(",", "."),
				"{:,.0f}".format(flt(d["so_tien"])).replace(",", "."),
			),
		}
	frappe.db.set_value(
		DT,
		d["name"],
		{
			"da_doi_soat": 1,
			"ma_gd": (ma_gd or "").strip(),
			"ngay_doi_soat": now_datetime(),
			"trang_thai": "Da doi soat",
		},
	)
	ho = frappe.get_doc(DT, d["name"])
	kq = _sinh_chung_tu(ho)
	frappe.db.commit()
	kq["khop"] = 1
	kq["ho_so"] = d["name"]
	kq["ma"] = ma
	return kq


def doi_soat_tu_dong():
	"""Chay hang gio. Ham tu thoat neu khong co phieu nao cho."""
	try:
		frappe.set_user("Administrator")
		doi_soat()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doi soat tu dong loi")


# --------------------------------------------------------------- doc cho man


@frappe.whitelist()
def thong_tin_chuyen_khoan(ho_so=None):
	"""Cuc chu de ke toan copy mot phat vao MB Biz, khoi go tay tung o.

	Go tay so tai khoan la duong de sai nhat trong ca luong: sai mot chu so
	la tien di vao mot tai khoan khong quen biet, va lay lai rat kho.

	Tra ba dang cua cung mot thong tin, vi ba dang phuc vu ba viec khac
	nhau (dung y het nep ho so thanh toan APP dang chay):
	  chu      - doc bang mat, kiem truoc khi bam
	  dong_tab - dan thang vao tep lo cua MB, moi cot mot o
	  noi_dung - chuoi rieng de bam chep cho o Noi dung tren MB Biz
	"""
	from vagabond.ban_hang import _kiem_quyen
	from vagabond.ho_so_tt import _bo_dau

	_kiem_quyen()
	d = frappe.get_doc(DT, ho_so)
	ten_nh = ""
	if d.ngan_hang:
		ten_nh = frappe.db.get_value("Bank", d.ngan_hang, "bank_name") or d.ngan_hang

	# Phieu lap TRUOC 16/08/2026 mang noi dung theo cu phap cu "HT <ma to tra
	# hang>". Duong doi soat moi do theo MA HOA DON GOC, nen noi dung cu se
	# khong bao gio khop, va phieu nam mai o Cho chi ma khong ai biet vi sao.
	#
	# Bat duoc khi kiem tren he ngay sau khi deploy v192: phieu cu tra ve
	# "HT HDB-26-08-00341" - do la ma TO TRA HANG, khong phai ma don.
	#
	# Chi dung lai cho phieu CHUA doi soat. Phieu da doi soat thi noi dung do
	# la thu ke toan da go vao ngan hang that, sua no la sua lai qua khu.
	nd = d.noi_dung_ck or ""
	if not cint(d.da_doi_soat) and not khop_giao_dich(nd, d.hoa_don):
		nd = noi_dung_ck(d.hoa_don)
		frappe.db.set_value(DT, d.name, "noi_dung_ck", nd, update_modified=False)
		frappe.db.commit()
	tien_so = "%d" % int(round(flt(d.so_tien)))
	tien_dep = "{:,.0f}".format(flt(d.so_tien)).replace(",", ".")
	# Ten chu tai khoan phai BO DAU VIET HOA: ngan hang khong nhan tieng
	# Viet co dau o o nguoi thu huong, va go lai tay la them mot cho sai.
	ten_ck = _bo_dau(d.ten_tk or "").upper()

	dong = [
		"Ngân hàng: %s" % (ten_nh or "(chưa khai)"),
		"Số tài khoản: %s" % (d.so_tk or "(chưa khai)"),
		"Tên chủ tài khoản: %s" % (ten_ck or "(chưa khai)"),
		"Số tiền: %s" % tien_dep,
		"Nội dung: %s" % nd,
	]
	# Cau truc cot cua tep lo do ngan_hang.tep_lo quyet, KHONG dung o day.
	# Anh Viet chot 17/08/2026: moi nut Xuat MB Biz tren app deu goi chung
	# mot ham backend, khong cho nao tu dung cot rieng.
	from vagabond.ngan_hang import tep_lo

	lo = tep_lo(
		json.dumps(
			[
				{
					"so_tk": d.so_tk,
					"ten_nhan": d.ten_tk,
					"ngan_hang": ten_nh,
					"so_tien": flt(d.so_tien),
					"noi_dung": nd,
				}
			]
		)
	)
	cot = lo["cot"]
	gia_tri = [str(x) for x in lo["bang"][0]]

	thieu = [x for x in ("so_tk", "ten_tk", "ngan_hang") if not d.get(x)]
	ten_thieu = {"so_tk": "số tài khoản", "ten_tk": "tên chủ tài khoản", "ngan_hang": "ngân hàng"}
	return {
		"ma": d.name,
		"hoa_don": d.hoa_don,
		"chu": "\n".join(dong),
		"cot": cot,
		"gia_tri": gia_tri,
		"dong_tab": "\t".join(gia_tri),
		"tieu_de_tab": "\t".join(cot),
		"so_tien": flt(d.so_tien),
		"ten_ck": ten_ck,
		"so_tk": (d.so_tk or "").strip(),
		"ngan_hang": ten_nh,
		"tsv": lo["tsv"],
		"nhac_lo": lo.get("nhac", []),
		"thieu": thieu,
		"nhac": (
			"Còn thiếu %s. Bổ sung vào phiếu rồi bấm lại thì mới chuyển được."
			% ", ".join(ten_thieu[x] for x in thieu)
			if thieu
			else ""
		),
		"noi_dung_ck": nd,
		"da_doi_soat": cint(d.da_doi_soat),
	}


@frappe.whitelist()
def ds_ngan_hang(tim=""):
	"""Danh sach ngan hang cho o chon tren app."""
	loc = {}
	if (tim or "").strip():
		loc = {"name": ["like", "%%%s%%" % tim.strip()]}
	return frappe.get_all("Bank", filters=loc, fields=["name"], limit_page_length=60, order_by="name")


@frappe.whitelist()
def tinh_trang(si_name=None):
	"""Man Chi tiet don hoi: don nay hoan tien duoc khong, da hoan chua."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	d = frappe.db.get_value(
		SI, si_name, ["name", "docstatus", "vgb_huy", "grand_total", "custom_hddt_so"], as_dict=True
	)
	if not d:
		return {"duoc": 0, "vi_sao": "Không có hoá đơn này."}
	# Phieu DA BI TU CHOI thi khong duoc chan don nay nua.
	#
	# Anh Viet bat duoc 19/08/2026 tren don 91433: phieu HT-2026-00871 anh da
	# tu choi, vay ma man Chi tiet don van bao "Đã hoàn tiền ... đã huỷ" va
	# van khong cho lap phieu moi. Sales ket cung, khong hoan duoc dong nao
	# cho khach.
	#
	# Cho nay la mot cho lech cua chinh tep nay: cac ham khac (dong 545, 813,
	# 1262, 1364) deu da loai "Da huy" ra tu lau, rieng tinh_trang thi khong.
	# Nen day khong phai doi luat, day la sua cho quen.
	CON_SONG = ["name", "trang_thai", "so_tien", "da_doi_soat"]
	song = frappe.db.get_value(
		DT, {"hoa_don": si_name, "trang_thai": ["!=", "Da huy"]}, CON_SONG, as_dict=True
	)
	if song:
		return {
			"duoc": 0,
			"da_hoan": song,
			"vi_sao": "Đơn này đã có yêu cầu hoàn tiền %s, đang ở trạng thái \"%s\"."
			% (song["name"], song["trang_thai"]),
		}
	# Khong con phieu song. Van tra ve phieu bi tu choi gan nhat de man hinh
	# noi ro cho sales biet da tung co mot phieu va no bi tu choi, chu khong
	# im lang nhu chua tung co gi.
	bi_tu_choi = frappe.db.get_value(
		DT, {"hoa_don": si_name, "trang_thai": "Da huy"}, CON_SONG,
		as_dict=True, order_by="creation desc",
	)
	if cint(d.docstatus) != 1:
		return {"duoc": 0, "bi_tu_choi": bi_tu_choi, "vi_sao": "Đơn chưa ghi sổ nên sửa hoặc huỷ thẳng được, không cần hoàn tiền."}
	if cint(d.get("vgb_huy")):
		return {"duoc": 0, "bi_tu_choi": bi_tu_choi, "vi_sao": "Đơn đã mang dấu huỷ."}
	# Goi y san tai khoan khach da dung o lan truoc, neu co. Doc tu chinh
	# ho so hoan tien cu cua khach nay chu khong doan.
	goi_y = {}
	kh = frappe.db.get_value(SI, si_name, "customer")
	if kh:
		cu = frappe.db.get_value(
			DT, {"khach": kh, "so_tk": ["is", "set"]}, ["ten_tk", "so_tk", "ngan_hang"],
			as_dict=True, order_by="creation desc",
		)
		if cu:
			goi_y = {k: v for k, v in cu.items() if v}
	return {
		"duoc": 1,
		"bi_tu_choi": bi_tu_choi,
		"so_tien": flt(d.grand_total),
		"ly_do_co_the": list(LY_DO),
		"goi_y_tk": goi_y,
		"khach": _khach_tren_don(si_name, kh),
		"canh_bao_hddt": (d.get("custom_hddt_so") or "").strip(),
	}


KHACH_LE = "Khách lẻ Online"


def tach_ghi_chu_don(ghi_chu):
	"""Doc ten khach va so dien thoai tu o ghi chu cua hoa don. THUAN.

	ban_hang.tao_don_tay dung o remarks theo khuon:

	    <nguon> #<ma don> - <ten khach>[ - <so dien thoai>][ - Quay <ma>]

	Vi du that tren he:
	    "Pancake #91759 - Loan Anh - 0933751352"
	    "Mang về #TEST-HT-02 - Khách thử hoàn tiền 2 - Quầy TCV"

	Tra (ten, sdt), cai nao khong co thi la chuoi rong.

	Vi sao phai doc tu day chu khong doc mot o cho tu te: so dien thoai
	khach le KHONG duoc luu thanh truong rieng tren hoa don - kiem tren he
	17/08/2026 thi contact_mobile va contact_phone deu rong. Cho duy nhat
	con giu la o ghi chu. Doc no la hoi lai mot thu da co san, con hon bat
	nhan vien go lai mot so ma khach vua doc xong cach do ba phut.
	"""
	s = str(ghi_chu or "").strip()
	if " - " not in s:
		return "", ""
	# Bo phan dau "<nguon> #<ma don>", giu phan sau dau gach dau tien.
	phan = [x.strip() for x in s.split(" - ")]
	phan = phan[1:]
	# Bo duoi "Quay <ma>" neu co - do khong phai thong tin khach.
	phan = [x for x in phan if x and not x.lower().startswith("quầy") and not x.lower().startswith("quay")]
	ten, so = "", ""
	for x in phan:
		chi_so = re.sub(r"[^0-9]", "", x)
		# Mot manh toan chu so va dai bang mot so dien thoai thi la so.
		if chi_so and len(chi_so) >= 9 and len(chi_so) >= len(x) - 2:
			if not so:
				so = chi_so
		elif not ten:
			ten = x
	return ten, so


def _khach_tren_don(si_name, ma_khach=None):
	"""Ten va so dien thoai khach de dien san vao form. Tra dict.

	Anh Viet 17/08/2026: "nhan vien khong phai go lai".

	Doc theo thu tu tin cay giam dan:
	  1. Khach thanh vien tren don (vgb_khach_no) - chac nhat, co ho so
	  2. Ten khach tren don, neu khong phai ten khach le chung
	  3. O ghi chu cua don - noi duy nhat con giu so cua khach le

	KHONG tron nguon cho tung o: neu lay duoc ho so khach thanh vien thi
	lay ca ten lan so tu do. Tron ten cua nguoi nay voi so cua nguoi kia la
	dua ke toan mot dia chi nhan tien khong thuoc ve ai.
	"""
	ra = {"ten": "", "sdt": "", "nguon": ""}
	try:
		d = frappe.db.get_value(
			SI, si_name, ["customer_name", "vgb_khach_no", "remarks", "customer"], as_dict=True
		) or {}
		tv = d.get("vgb_khach_no") or (ma_khach if ma_khach and ma_khach != KHACH_LE else "")
		if tv:
			kh = frappe.db.get_value("Customer", tv, ["customer_name", "mobile_no"], as_dict=True) or {}
			if (kh.get("customer_name") or "").strip() and kh["customer_name"] != KHACH_LE:
				ra["ten"] = kh["customer_name"].strip()
				ra["sdt"] = sdt(kh.get("mobile_no") or "")
				ra["nguon"] = "hồ sơ khách thành viên"
		if not ra["ten"]:
			ten_don = (d.get("customer_name") or "").strip()
			if ten_don and ten_don != KHACH_LE:
				ra["ten"] = ten_don
				ra["nguon"] = "tên khách trên đơn"
		if not ra["ten"] or not ra["sdt"]:
			ten_gc, so_gc = tach_ghi_chu_don(d.get("remarks"))
			if not ra["ten"] and ten_gc:
				ra["ten"] = ten_gc
				ra["nguon"] = "ghi chú trên đơn"
			if not ra["sdt"] and so_gc:
				ra["sdt"] = sdt(so_gc) or so_gc
				if not ra["nguon"]:
					ra["nguon"] = "ghi chú trên đơn"
	except Exception:
		# Doc goi y hong thi form van mo duoc, nhan vien go tay. KHONG nem
		# loi lam chet ca man vi mot o dien san.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc khach tren don loi")
	return ra


@frappe.whitelist()
def ds(trang_thai="", so_dong=100, tim=""):
	"""Danh sach phieu hoan tien cho man Hoan tien tren app.

	Bo loc va o tim chay o MAY CHU (QT-19). Doanh so mot mua co the sinh vai
	tram phieu, keo het ve dien thoai roi loc bang JavaScript la treo may -
	va con sai, vi so tren chip se chi dem phan da keo ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	loc = {}
	tt = (trang_thai or "").strip()
	if tt and tt != "tat_ca":
		loc["trang_thai"] = tt
	tim = (tim or "").strip()
	if tim:
		# Ba cho nguoi ta go vao o tim: ten khach, ma phieu, ma hoa don.
		# frappe.get_all khong co "hoac" giua nhieu truong nen phai dung
		# or_filters.
		ma_kh_tim = [
			c["name"]
			for c in frappe.get_all(
				"Customer",
				filters={"customer_name": ["like", "%%%s%%" % tim]},
				fields=["name"],
				limit_page_length=200,
			)
		]
		hoac = [
			["name", "like", "%%%s%%" % tim],
			["hoa_don", "like", "%%%s%%" % tim],
			["ten_tk", "like", "%%%s%%" % tim],
			["so_tk", "like", "%%%s%%" % tim],
		]
		if ma_kh_tim:
			hoac.append(["khach", "in", ma_kh_tim])
	else:
		hoac = None

	ds_ = frappe.get_all(
		DT,
		filters=loc,
		or_filters=hoac,
		fields=[
			"name", "hoa_don", "hoa_don_tra", "phieu_chi", "khach", "so_tien",
			"ly_do", "trang_thai", "da_doi_soat", "noi_dung_ck", "creation",
			"ten_tk", "so_tk", "ngan_hang", "nguoi_duyet", "loai_hoan",
		],
		order_by="creation desc",
		limit_page_length=max(1, min(500, cint(so_dong) or 100)),
	)
	ma_kh = list({d["khach"] for d in ds_ if d.get("khach")})
	ten = {}
	if ma_kh:
		for c in frappe.get_all(
			"Customer", filters={"name": ["in", ma_kh]}, fields=["name", "customer_name"], limit_page_length=0
		):
			ten[c["name"]] = c["customer_name"]
	# Phieu chi da ghi so chua - de man hinh biet cai nao con cho ke toan.
	ma_pc = list({d["phieu_chi"] for d in ds_ if d.get("phieu_chi")})
	pc = {}
	if ma_pc:
		for p in frappe.get_all(
			PE, filters={"name": ["in", ma_pc]}, fields=["name", "docstatus"], limit_page_length=0
		):
			pc[p["name"]] = cint(p["docstatus"])
	# Anh bang chung: ke toan ngoi xa quay, cai duy nhat ho co de quyet la
	# anh Sales chup. Tra thang duong dan de man ve thanh o anh bam xem to.
	anh = {}
	if ds_:
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ["in", [d["name"] for d in ds_]]},
			fields=["attached_to_name", "file_url", "file_name"],
			limit_page_length=0,
		):
			anh.setdefault(f["attached_to_name"], []).append(
				{"url": f["file_url"], "ten": f["file_name"]}
			)
	for d in ds_:
		d["ten_khach"] = ten.get(d.get("khach") or "", d.get("khach") or "")
		d["phieu_chi_da_ghi"] = 1 if pc.get(d.get("phieu_chi") or "") == 1 else 0
		d["anh"] = anh.get(d["name"], [])
	# Con so tren chip la so THAT cua ca so, khong phai so dong dang hien.
	# Dem theo dung o tim dang go, neu khong thi go "Nhung" ra 3 dong ma
	# chip van bao 40, va ke toan khong biet tin cai nao.
	dem = {}
	for t in ("Cho chi", "Da chi", "Da doi soat", "Da huy"):
		l2 = dict(loc)
		l2["trang_thai"] = t
		dem[t] = len(
			frappe.get_all(DT, filters=l2, or_filters=hoac, fields=["name"], limit_page_length=0)
		)
	dem["tat_ca"] = sum(dem.values())
	return {
		"ds": ds_,
		"dem": dem,
		"kho_huy": _cd()["kho_huy"],
		"tk_chi": _cd()["tk_chi"],
		"duoc_tu_choi": 1 if _duoc_tu_choi() else 0,
	}


def _duoc_tu_choi(nguoi=None):
	"""Ai duoc bam Tu choi hoan tien. THUAN theo nghia khong ghi gi.

	Tu choi la chan MOT dong tien sap ra, nen dat cung mot cua voi nguoi
	quyet chi: ke toan va giam doc. Sales lap phieu duoc nhung khong tu
	quyet duoc phieu cua chinh minh.
	"""
	vai = set(frappe.get_roles(nguoi or frappe.session.user))
	return bool(vai & {"System Manager", "Accounts Manager", "Accounts User", "Giám đốc"})


@frappe.whitelist()
def dem_cho_chi():
	"""So phieu dang cho chi - de trang chu cham badge do tren o Ke toan.

	Anh Viet 18/08/2026: "neu co phieu o trang thai Cho chi, hien badge do
	bao so luong tren icon de chi Dung Ke toan truong de nhan biet".

	Ham nay co the bi goi moi lan mo trang chu nen phai re: mot phep dem,
	khong keo dong nao ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {"cho_chi": frappe.db.count(DT, {"trang_thai": "Cho chi"})}


@frappe.whitelist()
def chi_tiet(ho_so):
	"""Mot phieu hoan tien, du thu de ke toan quyet chi hay tu choi.

	Anh Viet 18/08/2026: "man danh sach khong click vao xem chi tiet duoc".
	Man danh sach chi bay duoc nhung gi nhin luot; con anh bang chung to,
	so tai khoan khach, hoa don goc gom nhung mon gi, ai lap luc nao thi
	phai co mot cho rieng.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, ho_so):
		frappe.throw(
			"Không tìm thấy phiếu hoàn tiền %s. Có thể phiếu đã bị xoá trên "
			"Desk; anh chị quay lại danh sách rồi mở phiếu khác giúp em." % ho_so
		)
	d = frappe.get_doc(DT, ho_so)
	ra = d.as_dict()
	for k in list(ra.keys()):
		if k.startswith("_"):
			ra.pop(k, None)

	ra["ten_khach"] = (
		frappe.db.get_value("Customer", d.khach, "customer_name") if d.khach else ""
	) or (d.khach or "")
	ra["anh"] = [
		{"url": f["file_url"], "ten": f["file_name"]}
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ho_so},
			fields=["file_url", "file_name"],
			limit_page_length=0,
		)
	]

	# Hoa don goc: ke toan can biet don nay ban gi, bao nhieu tien, da thu
	# chua - de doi chieu voi so tien dang doi hoan.
	ra["don"] = None
	if d.hoa_don and frappe.db.exists(SI, d.hoa_don):
		si = frappe.get_doc(SI, d.hoa_don)
		ra["don"] = {
			"name": si.name,
			"ngay": str(si.posting_date or ""),
			# Ke toan phai nhin thay CA HAI con so de quyet: tien SePay da
			# nhan va tong don. Voi phieu tien nop thua thi chenh lech giua
			# hai con so nay chinh la can cu duy nhat, khong co anh chup nao
			# thay the duoc.
			"da_nhan_sepay": _tien_da_nhan(si),
			"tong": flt(si.grand_total),
			"da_thu": flt(si.grand_total) - flt(si.outstanding_amount),
			"diem_ban": si.get("custom_diem_ban") or "",
			"mon": [
				{"ten": r.item_name, "sl": flt(r.qty), "tien": flt(r.amount)}
				for r in (si.items or [])
			][:40],
		}

	# Phieu chi: con so duy nhat noi len tien da that su ra khoi tai khoan.
	ra["phieu_chi_trang_thai"] = ""
	if d.phieu_chi and frappe.db.exists(PE, d.phieu_chi):
		ds_ = cint(frappe.db.get_value(PE, d.phieu_chi, "docstatus"))
		ra["phieu_chi_trang_thai"] = {0: "Bản nháp", 1: "Đã ghi sổ", 2: "Đã huỷ"}.get(ds_, "")

	ra["duoc_tu_choi"] = 1 if _duoc_tu_choi() else 0
	# Tien da ra roi thi khong con gi de tu choi nua, chi con duong lap
	# phieu thu lai. Tra thang co nay ra de man hinh khong bay nut vo nghia.
	ra["con_tu_choi_duoc"] = (
		1 if (d.trang_thai == "Cho chi" and not cint(d.da_doi_soat) and not d.phieu_chi) else 0
	)
	ra["kho_huy"] = _cd()["kho_huy"]
	ra["tk_chi"] = _cd()["tk_chi"]
	return ra


@frappe.whitelist()
def tu_choi(ho_so, ly_do=None):
	"""Tu choi mot phieu hoan tien. Huy MEM, co ghi vet (QT-20).

	Anh Viet 18/08/2026: "bo sung nut Tu choi hoan tien kem form dien ly do
	bat buoc phong truong hop khach doi y hoac bang chung khong hop le".

	Ba cai chan o day, va deu chan o MAY CHU chu khong o man hinh:

	  ai bam    chi ke toan va giam doc, vi day la chan mot dong tien
	  luc nao   chi khi tien CHUA ra; da doi soat thi tu choi la noi doi so
	  ly do gi  bat buoc, va phai la mot cau chu khong phai mot dau cham
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw(
			"Từ chối hoàn tiền là quyền của Kế toán và Giám đốc. Anh chị nhờ "
			"chị Dung hoặc anh Việt bấm giúp, hoặc báo em cấp thêm chức vụ "
			"trong màn Quản lý người dùng."
		)
	ly_do = (ly_do or "").strip()
	if len(ly_do) < 5:
		frappe.throw(
			"Phải ghi rõ lý do từ chối, ít nhất 5 ký tự. Câu này sẽ nằm lại "
			"trong hồ sơ và là thứ duy nhất giải thích được vì sao khách "
			"không nhận được tiền, nên anh chị viết đủ ý giúp em."
		)
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Anh chị mở lại danh sách giúp em." % ho_so)
	d = frappe.get_doc(DT, ho_so)
	if d.trang_thai == "Da huy":
		frappe.throw(
			"Phiếu này đã bị từ chối trước đó rồi%s. Không cần bấm lại."
			% ((" (lý do: %s)" % d.get("ly_do_tu_choi")) if d.get("ly_do_tu_choi") else "")
		)
	if cint(d.da_doi_soat) or d.phieu_chi:
		frappe.throw(
			"Tiền của phiếu này đã ra khỏi tài khoản công ty rồi, không từ "
			"chối được nữa. Muốn thu lại thì lập phiếu thu riêng và ghi rõ "
			"lý do, đừng sửa phiếu hoàn tiền cũ."
		)
	frappe.db.set_value(
		DT,
		ho_so,
		{
			"trang_thai": "Da huy",
			"ly_do_tu_choi": ly_do,
			"nguoi_tu_choi": frappe.session.user,
			"ngay_tu_choi": now_datetime(),
		},
	)
	# Ghi them mot dong vao so nhat ky cua chinh ho so, de nguoi doc sau
	# nay thay ca hai: truong da doi va mot dong ke chuyen.
	try:
		frappe.get_doc(DT, ho_so).add_comment(
			"Comment",
			"Từ chối hoàn tiền. Lý do: %s" % ly_do,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet tu choi")
	frappe.db.commit()
	return {
		"ok": 1,
		"ho_so": ho_so,
		"ghi_chu": "Đã từ chối phiếu %s. Phiếu chuyển sang Đã huỷ và không "
		"còn được máy tự đối soát nữa." % ho_so,
	}
