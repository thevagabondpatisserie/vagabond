# -*- coding: utf-8 -*-
"""Phieu thanh toan TRUOC cho nha cung cap, lap tu app Thu mua.

Ca that 21/08/2026: don in an phai tra truoc mot phan, moi co bao gia va
hop dong, nha in lam xong moi xuat hoa don. Bon luong cua man Ho so thanh
toan deu khong nhan: hai luong hoan ung la tra lai tien cho NGUOI da ung,
luong cong no doi phai co hoa don, con luong chi tu TK cong ty thi ghi
THANG vao tai khoan chi phi.

Tien tra truoc KHONG phai chi phi. No la khoan tra truoc cho nguoi ban,
nam ben No cua 331 cho toi khi hoa don ve thi can tru. Ghi vao chi phi la
sai ban chat, va don mua hang cung khong biet minh da duoc tra truoc bao
nhieu.

VI SAO KHONG TU DUNG BANG references
------------------------------------
Bang `references` cua Payment Entry khong phai mot bang phang: ERPNext con
tinh `outstanding_amount`, ty gia, va co `is_advance` de sau nay hoa don
biet ma keo khoan ung truoc ra can tru. Dung tay tung o la dung mot ban sao
cua logic do, va ban sao se lech khi ERPNext len phien ban.

Nen tep nay goi thang `get_payment_entry` cua ERPNext - dung ham ma nut
"Tao > Phieu thanh toan" tren Desk goi - roi chi doi nhung gi minh that su
can. Tinh nang can tru tu dong nho vay khong bao gio gay.

Import erpnext nam TRONG ham chu khong o dau tep: may chay CI khong co
erpnext, khong co Frappe, khong co site. De o dau tep la ca bo kiem thu
tang khung chet theo.

RANH GIOI VOI TIEN
------------------
Cua nay chi dung phieu o trang thai NHAP. No khong ghi so, khong chuyen mot
dong nao. Duong ghi so di qua workflow "Duyet phieu chi APP" da chay san:
Nhap -> Cho FIN kiem tra (chi Dung) -> Cho giam doc duyet -> Da duyet, da
ghi so. Hai cap duyet, dung nhu cac luong khac.
"""

import json

import frappe
from frappe.utils import cint, flt, nowdate

PO = "Purchase Order"
PE = "Payment Entry"

# Ai lap duoc phieu tra truoc. Thu mua lap vi ho la nguoi dam phan dieu
# khoan tra truoc; ke toan lap duoc de con lap ho khi Uyen nghi.
QUYEN_LAP = {
	"Purchase User", "Purchase Manager", "AP Officer",
	"Accounts User", "Accounts Manager", "System Manager",
}

# Vai nhan viec o buoc mot cua workflow. Doc dung ten trong workflow
# "Duyet phieu chi APP" chu khong tu dat ten moi.
VAI_FIN = {"AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User", "System Manager"}

# Trang thai don mua khong con nhan tra truoc nua.
TT_DONG = {"Closed", "Completed", "Delivered"}

# Trang thai dau tien cua workflow. Phai TRUNG voi ten trong workflow that,
# lech mot dau la phieu roi ra ngoai luong duyet va nam mai o do.
TT_NHAP = "Nháp"

CHUNG_TU = (
	"Bảng báo giá",
	"Hợp đồng mua bán hàng hóa giữa hai bên",
	"Đơn đặt hàng có điều khoản trả trước",
	"Biên bản thoả thuận",
	"Uỷ nhiệm chi đã chi tiền",
	"Khác",
)


# ------------------------------------------------------------ phep THUAN
#
# Bon ham duoi day khong cham Frappe, khong cham site, khong doc cau hinh.
# Chay duoc bang python tran nen kiem thu tang khung soi thang vao duoc.


def la_quy_tam_ung(so_hieu):
	"""Tai khoan nay co phai quy tam ung ca nhan khong. THUAN.

	Doc theo SO HIEU chu khong theo account_type cua ERPNext: tren he nay ca
	1411 lan 1412 deu duoc khai account_type "Bank" vi moi cai gan mot tai
	khoan ngan hang that, ma ban chat chung la tam ung ca nhan. Xet theo
	account_type thi chung thanh tien gui ngan hang cua cong ty.
	"""
	return str(so_hieu or "").strip().startswith("141")


def nhan_nguon(so_hieu, ten_tk=""):
	"""Ten hien tren app cho mot nguon tien. THUAN.

	Co y KHONG goi 1411 la "quy Purchasing". Tren he nay khong ton tai quy
	nao cua bo phan mua hang: 1411 va 1412 deu dung ten anh Viet. Goi sai
	ten thi nguoi dung tuong day la tien cua cong ty da giao cho bo phan, va
	quen mat rang chi phai hoan ung lai cho anh.
	"""
	ten = str(ten_tk or "").strip()
	if la_quy_tam_ung(so_hieu):
		return "Quỹ tạm ứng cá nhân · %s" % (ten or so_hieu)
	return "Tài khoản công ty · %s" % (ten or so_hieu)


def tran_tra_truoc(tong_don, da_tra_truoc, phan_tram_da_lap_hd=0):
	"""Duoc tra truoc bao nhieu nua cho don nay. THUAN.

	Tra ve (duoc_lap, tran, vi_sao). Tran la phan CON LAI, khong phai tong
	don: tra truoc hai lan ma lan nao cung lay tong don lam tran la ung
	vuot gia tri don, va luc hoa don ve thi ERPNext khong can tru het duoc,
	de lai mot khoan du No 331 khong ai giai thich noi.
	"""
	tong = flt(tong_don)
	da = flt(da_tra_truoc)
	if tong <= 0:
		return False, 0.0, (
			"Đơn mua này chưa có giá trị nào. Điền đơn giá trên đơn mua hàng "
			"trước rồi mới lập được phiếu trả trước."
		)
	if flt(phan_tram_da_lap_hd) >= 99.99:
		return False, 0.0, (
			"Đơn này đã có hoá đơn cho toàn bộ giá trị rồi. Trả tiền cho hoá "
			"đơn đó bằng luồng Công nợ nhà cung cấp, đừng lập phiếu trả trước."
		)
	con = round(tong - da, 0)
	if con <= 0.5:
		return False, 0.0, (
			"Đơn này đã trả trước đủ %s đ trên tổng %s đ, không còn phần nào "
			"để ứng thêm." % (tien_vn(da), tien_vn(tong))
		)
	return True, con, ""


def kiem_so_tien(so_tien, tran):
	"""So tien nguoi nhap co hop le khong. THUAN. Tra ve (duoc, vi_sao)."""
	tien = flt(so_tien)
	if tien <= 0:
		return False, "Số tiền trả trước phải lớn hơn 0."
	if tien > flt(tran) + 0.5:
		return False, (
			"Số tiền vượt phần còn lại của đơn. Nhiều nhất được ứng %s đ."
			% tien_vn(tran)
		)
	return True, ""


def tien_vn(x):
	"""Dinh dang tien kieu Viet cho cau bao loi. THUAN."""
	try:
		return "{:,.0f}".format(flt(x)).replace(",", ".")
	except Exception:
		return str(x)


# ------------------------------------------------------------------ chan


def _chan():
	if frappe.session.user == "Guest":
		frappe.throw("Phải đăng nhập.")
	if not set(frappe.get_roles()) & QUYEN_LAP:
		frappe.throw("Tài khoản này không lập được phiếu trả trước. Báo quản lý cấp vai.")


def _cong_ty():
	from vagabond.lib import cfg

	c = cfg()
	return (c.get("cong_ty") if hasattr(c, "get") else None) or frappe.defaults.get_user_default("Company")


# ------------------------------------------------------------------ cua ngo


@frappe.whitelist()
def ds_don_mua(tu_khoa="", gioi_han=40):
	"""Don mua da duyet, chua dong, con phan chua tra truoc.

	Chi liet ke don DA GHI SO: don con nhap thi chua ai cam ket gi, ung tien
	cho mot to giay chua duyet la mo duong cho chuyen ung roi moi di xin
	duyet sau.
	"""
	_chan()
	loc = {"docstatus": 1, "status": ["not in", sorted(TT_DONG)]}
	tu_khoa = (tu_khoa or "").strip()
	if tu_khoa:
		loc["supplier_name"] = ["like", "%" + tu_khoa + "%"]
	ra = []
	for d in frappe.get_all(
		PO, filters=loc,
		fields=[
			"name", "supplier", "supplier_name", "transaction_date",
			"grand_total", "advance_paid", "per_billed", "status", "currency",
		],
		order_by="transaction_date desc",
		limit_page_length=cint(gioi_han) or 40,
	):
		duoc, tran, vi_sao = tran_tra_truoc(
			d.get("grand_total"), d.get("advance_paid"), d.get("per_billed"))
		ra.append({
			"don": d["name"],
			"ncc": d.get("supplier"),
			"ten_ncc": d.get("supplier_name") or d.get("supplier"),
			"ngay": str(d.get("transaction_date") or ""),
			"tong": flt(d.get("grand_total")),
			"da_tra_truoc": flt(d.get("advance_paid")),
			"da_lap_hd": flt(d.get("per_billed")),
			"tien_te": d.get("currency") or "VND",
			"tran": tran,
			"lap_duoc": 1 if duoc else 0,
			"vi_sao": vi_sao,
		})
	return {"don": ra}


@frappe.whitelist()
def chi_tiet_don(don=None):
	"""Thong tin mot don mua kem ho so nha cung cap, de app bay ra cho nguoi soat.

	Ma so thue, dia chi va so tai khoan lay tu HO SO NHA CUNG CAP tren he,
	khong lay tu con nguoi go vao. Don da chot nha cung cap roi, hoi lai ma
	so thue de tu do suy ra nha cung cap la mo duong cho phieu tro vao mot
	nha cung cap khac voi don - ERPNext se tu choi, ma nguoi lap thi khong
	hieu vi sao.
	"""
	_chan()
	don = (don or "").strip()
	if not don or not frappe.db.exists(PO, don):
		frappe.throw("Không tìm thấy đơn mua hàng %s." % (don or ""))
	d = frappe.get_doc(PO, don)
	if cint(d.docstatus) != 1:
		frappe.throw(
			"Đơn %s chưa được duyệt gửi. Duyệt đơn trước rồi mới lập phiếu "
			"trả trước." % don)

	duoc, tran, vi_sao = tran_tra_truoc(d.grand_total, d.get("advance_paid"), d.get("per_billed"))

	ncc = {}
	if d.supplier and frappe.db.exists("Supplier", d.supplier):
		s = frappe.db.get_value(
			"Supplier", d.supplier,
			["supplier_name", "tax_id", "supplier_group"], as_dict=True) or {}
		ncc = {
			"ma": d.supplier,
			"ten": s.get("supplier_name") or d.supplier,
			"mst": s.get("tax_id") or "",
			"nhom": s.get("supplier_group") or "",
			"dia_chi": _dia_chi_ncc(d.supplier),
			"tai_khoan": _tk_ncc(d.supplier),
		}

	return {
		"don": d.name,
		"ngay": str(d.transaction_date or ""),
		"tong": flt(d.grand_total),
		"da_tra_truoc": flt(d.get("advance_paid")),
		"da_lap_hd": flt(d.get("per_billed")),
		"trang_thai": d.get("status"),
		"tien_te": d.get("currency") or "VND",
		"tran": tran,
		"lap_duoc": 1 if duoc else 0,
		"vi_sao": vi_sao,
		"ncc": ncc,
		"loai_chung_tu": list(CHUNG_TU),
	}


def _dia_chi_ncc(ma):
	try:
		lk = frappe.get_all(
			"Dynamic Link",
			filters={"link_doctype": "Supplier", "link_name": ma, "parenttype": "Address"},
			fields=["parent"], limit_page_length=3)
		for x in lk:
			a = frappe.db.get_value(
				"Address", x["parent"],
				["address_line1", "city", "state"], as_dict=True) or {}
			gom = ", ".join([v for v in (
				a.get("address_line1"), a.get("city"), a.get("state")) if v])
			if gom:
				return gom
	except Exception:
		pass
	return ""


def _tk_ncc(ma):
	"""So tai khoan nhan tien cua nha cung cap, doc tu Bank Account cua ho."""
	try:
		for b in frappe.get_all(
			"Bank Account",
			filters={"party_type": "Supplier", "party": ma},
			fields=["bank_account_no", "bank", "account_name"],
			limit_page_length=3,
		):
			if b.get("bank_account_no"):
				return {
					"so_tk": b["bank_account_no"],
					"ngan_hang": b.get("bank") or "",
					"chu_tk": b.get("account_name") or "",
				}
	except Exception:
		pass
	return {}


@frappe.whitelist()
def ds_nguon_tien():
	"""Cac tai khoan tien cua cong ty, tach hai nhom va goi dung ten.

	Nhom `cong_ty` la tien gui ngan hang that cua cong ty (112x). Nhom
	`tam_ung` la quy tam ung ca nhan (141x) - tra tu day nghia la ca nhan
	bo tien ra truoc va cong ty con no lai, phai di tiep duong hoan ung.
	"""
	_chan()
	ra = []
	for b in frappe.get_all(
		"Bank Account",
		filters={"is_company_account": 1},
		fields=["name", "account", "bank", "bank_account_no"],
		limit_page_length=0,
	):
		tk = b.get("account")
		if not tk:
			continue
		so_hieu = frappe.db.get_value("Account", tk, "account_number") or ""
		ra.append({
			"ma": b["name"],
			"tk_so_cai": tk,
			"so_hieu": so_hieu,
			"nhom": "tam_ung" if la_quy_tam_ung(so_hieu) else "cong_ty",
			"nhan": nhan_nguon(so_hieu, b.get("bank") or b["name"]),
			"so_tk": b.get("bank_account_no") or "",
		})
	ra.sort(key=lambda x: (x["nhom"] != "cong_ty", x["so_hieu"]))
	return {"nguon": ra}


@frappe.whitelist()
def tao_phieu(don=None, so_tien=None, nguon_tien=None, loai_chung_tu=None,
		tep=None, ghi_chu=""):
	"""Dung Payment Entry TRA TRUOC o trang thai nhap, roi giao cho ke toan.

	Khong ghi so, khong chuyen tien. Buoc ghi so nam trong workflow
	"Duyet phieu chi APP" da chay san.
	"""
	_chan()
	don = (don or "").strip()
	if not don or not frappe.db.exists(PO, don):
		frappe.throw("Chưa chọn đơn mua hàng, hoặc đơn không tồn tại.")

	d = frappe.get_doc(PO, don)
	if cint(d.docstatus) != 1:
		frappe.throw("Đơn %s chưa duyệt gửi, chưa lập phiếu trả trước được." % don)
	if (d.get("status") or "") in TT_DONG:
		frappe.throw(
			"Đơn %s đang ở trạng thái %s nên không nhận thêm khoản trả trước."
			% (don, d.get("status")))

	duoc, tran, vi_sao = tran_tra_truoc(d.grand_total, d.get("advance_paid"), d.get("per_billed"))
	if not duoc:
		frappe.throw(vi_sao)
	hop_le, ly_do = kiem_so_tien(so_tien, tran)
	if not hop_le:
		frappe.throw(ly_do)
	tien = round(flt(so_tien), 0)

	# Nguon tien
	nguon_tien = (nguon_tien or "").strip()
	if not nguon_tien or not frappe.db.exists("Bank Account", nguon_tien):
		frappe.throw("Chưa chọn nguồn tiền để chi.")
	tk_so_cai = frappe.db.get_value("Bank Account", nguon_tien, "account")
	if not tk_so_cai:
		frappe.throw(
			"Tài khoản %s chưa gắn tài khoản sổ cái nên chưa hạch toán được. Vui lòng mở Bank Account bên Desk điền ô Account." % nguon_tien)

	# Ho so dinh kem: bat buoc, vi day la khoan tien di ra ma CHUA co hoa
	# don. Khong co bao gia hay hop dong thi khong co gi chung minh khoan
	# nay la tra truoc chu khong phai tien bien mat.
	loai_chung_tu = (loai_chung_tu or "").strip()
	if loai_chung_tu not in CHUNG_TU:
		frappe.throw(
			"Chưa chọn loại chứng từ. Chọn một trong: %s." % ", ".join(CHUNG_TU))
	if isinstance(tep, str):
		tep = frappe.parse_json(tep) if tep.strip() else []
	tep = tep or []
	if not tep:
		frappe.throw(
			"Chưa đính kèm chứng từ nào. Khoản trả trước chưa có hoá đơn nên "
			"bắt buộc phải có báo giá hoặc hợp đồng làm căn cứ.")

	pe = _dung_phieu(d, tien, tk_so_cai)
	_ghi_chu(pe, d, tien, nguon_tien, loai_chung_tu, ghi_chu)
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)

	_gan_tep(pe.name, tep)
	_bao_ke_toan(pe.name, d, tien)

	return {
		"phieu": pe.name,
		"so_tien": tien,
		"tra_tu": pe.paid_from,
		"tra_vao": pe.paid_to,
		"don": don,
		"trang_thai": pe.get("workflow_state") or TT_NHAP,
		"nhan": "Đã lập phiếu trả trước %s, đang chờ kế toán kiểm tra." % pe.name,
	}


def _dung_phieu(d, tien, tk_so_cai):
	"""Goi dung ham ERPNext dung sau nut Tao > Phieu thanh toan tren Desk.

	`party_amount` la duong chinh thuc de ung MOT PHAN don: ERPNext tu tinh
	lai dong references, phan bo dung so tien, va giu nguyen co ung truoc.
	Tu tay dung dong references la tu viet lai doan logic nay.
	"""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	# `party_amount` PHAI la so, khong duoc la chuoi. Thu that tren site
	# 21/08/2026: goi qua HTTP voi chuoi "300000" thi ERPNext no
	# `TypeError: bad operand type for abs(): 'str'` ngay trong ham cua no.
	# `tien` o tren da qua flt roi nen an toan, ghi lai de doi sau khong ai
	# nghich thanh chuoi.
	pe = get_payment_entry(
		PO, d.name, party_amount=tien, bank_account=tk_so_cai)

	# MOT NET DE BI TUONG LA LOI, DUNG "SUA":
	# ngay sau loi goi nay, dong tham chieu co total_amount BANG so tien
	# tra truoc chu khong bang gia tri don - do la cach `party_amount`
	# hoat dong. Nhung luc `insert`, `set_missing_ref_details` cua ERPNext
	# doc lai don that va dat lai dung con so.
	# Da kiem tren site that 21/08/2026, phieu APP-26-08-533: don 933.120
	# ung 300.000, sau khi luu dong tham chieu ghi total 933.120,
	# outstanding 933.120, allocated 300.000. Dung het.
	# Ket luan: KHONG dung tay vao ba o do. Cham vao la pha dung cho
	# ERPNext dang tu tinh.
	pe.posting_date = nowdate()
	pe.reference_date = nowdate()
	if pe.get("workflow_state") is not None or _co_o_workflow():
		pe.workflow_state = TT_NHAP

	# Chot lai ba dieu truoc khi luu. Neu ERPNext doi cach dung phieu o phien
	# ban sau thi vo day chu khong vo lang le tren so.
	if (pe.get("payment_type") or "") != "Pay":
		frappe.throw("Máy dựng nhầm loại phiếu (%s), dừng lại." % pe.get("payment_type"))
	if (pe.get("party_type") or "") != "Supplier" or pe.get("party") != d.supplier:
		frappe.throw("Đối tác trên phiếu không khớp nhà cung cấp của đơn, dừng lại.")
	neo = [r for r in (pe.get("references") or [])
		if r.reference_doctype == PO and r.reference_name == d.name]
	if not neo:
		frappe.throw(
			"Máy không neo được phiếu vào đơn mua %s. Không lưu phiếu treo "
			"lơ lửng như vậy." % d.name)
	if flt(neo[0].allocated_amount) <= 0:
		frappe.throw("Số tiền phân bổ vào đơn bằng 0, dừng lại.")
	return pe


def _co_o_workflow():
	try:
		return bool(frappe.db.exists(
			"Workflow", {"document_type": PE, "is_active": 1}))
	except Exception:
		return False


def _ghi_chu(pe, d, tien, nguon_tien, loai_chung_tu, ghi_chu):
	"""Ghi ro tren phieu day la khoan tra truoc, va tra truoc cho cai gi."""
	them = (
		"Trả trước %s đ cho đơn mua %s (%s), tổng giá trị đơn %s đ. Khoản này "
		"KHÔNG phải chi phí: nó là tiền trả trước cho người bán, nằm bên Nợ "
		"331 cho tới khi hoá đơn về thì cấn trừ. Chứng từ kèm theo: %s. "
		"Nguồn tiền: %s."
		% (tien_vn(tien), d.name, d.get("supplier_name") or d.supplier,
			tien_vn(d.grand_total), loai_chung_tu, nguon_tien)
	)
	gc = (ghi_chu or "").strip()
	if gc:
		them += " Ghi chú người lập: %s" % gc
	# Đi qua chung_tu_tien chứ KHÔNG gán thẳng pe.remarks: ERPNext dựng lại ô
	# này trong validate và xoá mất câu của mình. Xem chung_tu_tien.dat_dien_giai.
	from vagabond.chung_tu_tien import them_dien_giai

	them_dien_giai(pe, them)


def _gan_tep(ten_phieu, tep):
	"""Gan tep da tai len vao phieu. Hong mot tep khong duoc lam hong ca phieu."""
	for t in tep:
		try:
			ma = (t or {}).get("ma")
			if not ma or not frappe.db.exists("File", ma):
				continue
			frappe.db.set_value("File", ma, {
				"attached_to_doctype": PE,
				"attached_to_name": ten_phieu,
			}, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tra_truoc: gan tep loi")


def _bao_ke_toan(ten_phieu, d, tien):
	"""Bao cho ke toan biet co phieu cho kiem, va giao viec dich danh.

	Khong bao gio nem loi: phieu da luu roi ma cai chuong lam hong ca thao
	tac thi mat mot viec that vi mot cai nhan.
	"""
	try:
		from vagabond import giao_viec

		nguoi = giao_viec._nguoi_theo_vai(VAI_FIN)
		if not nguoi:
			return
		mo_ta = "%s: phiếu trả trước %s đ cho %s, đơn %s" % (
			ten_phieu, tien_vn(tien), d.get("supplier_name") or d.supplier, d.name)
		giao_viec.giao(PE, ten_phieu, nguoi, mo_ta)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tra_truoc: bao ke toan loi")
