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

import re

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate

from vagabond.lib import cfg, sdt

DT = "Vagabond Hoan Tien"
SI = "Sales Invoice"
PE = "Payment Entry"

TEN_KHO_HUY = "Kho Hàng Hủy"
TIEN_TO_CK = "HT"

LY_DO = ("Khach doi y", "Banh hong", "Di ung", "Giao sai mon", "Giao tre", "Khac")

# Ly do nao thi hang chac chan KHONG dung lai duoc nua. Ca sau nay deu vao
# kho huy het, nhung ba ly do nay con dung de bao cao ty le hong cho bep.
LY_DO_HONG = {"Banh hong", "Di ung", "Giao sai mon"}


TRUONG_MOI = {
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


def noi_dung_ck(ma_hoa_don_tra):
	"""Noi dung chuyen khoan de doi soat SePay. THUAN.

	Vi sao doi soat theo NOI DUNG chu khong theo SO TIEN: hai khach cung
	duoc hoan 250.000 d trong mot ngay la chuyen thuong, do theo so tien
	la khop nham. Day cung dung nep mach S<shop>O<don>T ma Pancake dang
	dung cho tien vao.
	"""
	return "%s %s" % (TIEN_TO_CK, str(ma_hoa_don_tra or "").strip())


def khop_giao_dich(mo_ta, ma_hoa_don_tra):
	"""Mot dong sao ke co phai la lenh chi cua don nay khong. THUAN.

	Chan hai dau bang ky tu khong phai chu-so, de "HDB-2026-0160" khong an
	nham giao dich cua "HDB-2026-01604" - dung bay da gap voi ma WOO.
	"""
	ma = str(ma_hoa_don_tra or "").strip()
	if not ma:
		return False
	rx = re.compile(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(ma), re.IGNORECASE)
	return bool(rx.search(str(mo_ta or "")))


# --------------------------------------------------------------- viec chinh


@frappe.whitelist()
def tao(si_name=None, ly_do=None, dien_giai="", otp=None, ten_tk="", so_tk="", ngan_hang="", sdt_khach=""):
	"""Tra hang va lap ho so hoan tien cho mot hoa don DA GHI SO."""
	from vagabond.ban_hang import _kiem_quyen, _otp_kiem

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_tra_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO:
		frappe.throw("Phải chọn lý do hoàn. Chọn một trong: %s." % ", ".join(LY_DO))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao hoàn. Gõ vào ô Diễn giải giúp em.")

	# Ma PIN quan ly: dung LAI dung co che dang chay cho sua va xoa hoa don,
	# khong de them mot he ma thu hai de roi quan ly phai nho hai thu.
	cach = _otp_kiem(otp, "hoàn tiền cho khách")

	cty = si.company
	kho = kho_huy(cty)
	if not kho:
		frappe.throw("Chưa dựng được Kho Hàng Hủy. Báo em để kiểm tra lại cấu hình kho.")

	ho_so = frappe.get_doc(
		{
			"doctype": DT,
			"hoa_don": si.name,
			"khach": si.customer,
			"so_tien": flt(si.grand_total),
			"ly_do": ly_do,
			"dien_giai": (dien_giai or "").strip(),
			"trang_thai": "Cho chi",
			"ten_tk": (ten_tk or "").strip(),
			"so_tk": re.sub(r"\s+", "", str(so_tk or "")),
			"ngan_hang": (ngan_hang or "").strip() or None,
			"sdt": sdt(sdt_khach) or "",
			"nguoi_duyet": frappe.session.user,
			"cach_duyet": cach,
		}
	)
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	tra = _lap_hoa_don_tra(si, kho, ly_do, ho_so.name)
	ho_so.hoa_don_tra = tra.name
	ho_so.noi_dung_ck = noi_dung_ck(tra.name)

	_thu_hoi_diem(si, tra.name, ly_do)
	phieu_kho = _chuyen_kho_huy(si, tra, kho, ly_do)

	pe = _lap_phieu_chi(si, tra, ho_so)
	ho_so.phieu_chi = pe.name if pe else None
	ho_so.flags.ignore_permissions = True
	ho_so.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"hoa_don_tra": tra.name,
		"phieu_kho": phieu_kho,
		"phieu_chi": ho_so.phieu_chi,
		"so_tien": flt(si.grand_total),
		"kho_huy": kho,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"canh_bao_hddt": (si.get("custom_hddt_so") or "").strip(),
	}


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


def _lap_hoa_don_tra(si, kho, ly_do, ma_ho_so):
	"""Hoa don tra hang, hang ve KHO HANG HUY chu khong ve kho ban."""
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

	tra = make_sales_return(si.name)
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
	loc = {"da_doi_soat": 0}
	if ho_so:
		loc = {"name": ho_so}
	ds = frappe.get_all(
		DT,
		filters=loc,
		fields=["name", "hoa_don_tra", "so_tien", "trang_thai"],
		limit_page_length=0,
	)
	ds = [d for d in ds if d.get("hoa_don_tra")]
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

	da, xem = 0, []
	for d in ds:
		for g in gds:
			mo_ta = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
			if not khop_giao_dich(mo_ta, d["hoa_don_tra"]):
				continue
			# Khop noi dung roi van phai so TIEN. Noi dung dung ma so tien
			# lech nghia la ke toan chuyen thieu hoac thua, va do la viec
			# nguoi phai xem chu khong phai may tu dong danh dau xong.
			if abs(flt(g["withdrawal"]) - flt(d["so_tien"])) > 1:
				xem.append(
					{
						"ho_so": d["name"],
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
			break
	frappe.db.commit()
	return {"da_khop": da, "xem_xet": xem[:50], "so_phieu_quet": len(ds)}


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
	"""Cuc chu de chi Dung copy mot phat, khoi go tay tung o.

	Go tay so tai khoan la duong de sai nhat trong ca luong: sai mot chu so
	la tien di mat vao mot tai khoan khong quen biet, va lay lai rat kho.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	d = frappe.get_doc(DT, ho_so)
	ten_nh = ""
	if d.ngan_hang:
		ten_nh = frappe.db.get_value("Bank", d.ngan_hang, "bank_name") or d.ngan_hang
	dong = [
		"Ngân hàng: %s" % (ten_nh or "(chưa khai)"),
		"Số tài khoản: %s" % (d.so_tk or "(chưa khai)"),
		"Tên chủ tài khoản: %s" % (d.ten_tk or "(chưa khai)"),
		"Số tiền: %s" % "{:,.0f}".format(flt(d.so_tien)).replace(",", "."),
		"Nội dung: %s" % (d.noi_dung_ck or noi_dung_ck(d.hoa_don_tra)),
	]
	thieu = [x for x in ("so_tk", "ten_tk", "ngan_hang") if not d.get(x)]
	return {
		"chu": "\n".join(dong),
		"thieu": thieu,
		"nhac": (
			"Còn thiếu %s. Bổ sung vào phiếu rồi bấm lại thì mới chuyển được."
			% ", ".join({"so_tk": "số tài khoản", "ten_tk": "tên chủ tài khoản", "ngan_hang": "ngân hàng"}[x] for x in thieu)
			if thieu
			else ""
		),
		"noi_dung_ck": d.noi_dung_ck or noi_dung_ck(d.hoa_don_tra),
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
	da = frappe.db.get_value(DT, {"hoa_don": si_name}, ["name", "trang_thai", "so_tien"], as_dict=True)
	if da:
		return {"duoc": 0, "da_hoan": da, "vi_sao": "Đơn này đã có phiếu hoàn tiền %s." % da["name"]}
	if cint(d.docstatus) != 1:
		return {"duoc": 0, "vi_sao": "Đơn chưa ghi sổ nên sửa hoặc huỷ thẳng được, không cần hoàn tiền."}
	if cint(d.get("vgb_huy")):
		return {"duoc": 0, "vi_sao": "Đơn đã mang dấu huỷ."}
	return {
		"duoc": 1,
		"so_tien": flt(d.grand_total),
		"ly_do_co_the": list(LY_DO),
		"canh_bao_hddt": (d.get("custom_hddt_so") or "").strip(),
	}


@frappe.whitelist()
def ds(trang_thai="", so_dong=100):
	"""Danh sach phieu hoan tien cho man Hoan tien tren app."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	loc = {}
	if (trang_thai or "").strip() and trang_thai != "tat_ca":
		loc["trang_thai"] = trang_thai
	ds_ = frappe.get_all(
		DT,
		filters=loc,
		fields=[
			"name", "hoa_don", "hoa_don_tra", "phieu_chi", "khach", "so_tien",
			"ly_do", "trang_thai", "da_doi_soat", "noi_dung_ck", "creation",
			"ten_tk", "so_tk", "ngan_hang", "nguoi_duyet",
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
	for d in ds_:
		d["ten_khach"] = ten.get(d.get("khach") or "", d.get("khach") or "")
		d["phieu_chi_da_ghi"] = 1 if pc.get(d.get("phieu_chi") or "") == 1 else 0
	dem = {"tat_ca": len(ds_)}
	for t in ("Cho chi", "Da chi", "Da doi soat"):
		dem[t] = frappe.db.count(DT, {"trang_thai": t})
	return {"ds": ds_, "dem": dem, "kho_huy": _cd()["kho_huy"], "tk_chi": _cd()["tk_chi"]}
