"""v674 ca TÍCH HỢP: Bảng kê 242 và bút toán chi phí Meta theo sao kê thẻ.

Tầng khung chốt phép tính bằng bản giả. Tầng này hỏi điều bản giả không trả lời:
ERPNext có THẬT SỰ nhận bút toán nháp máy lập (dòng có ô khoản 242, tài khoản 242 hay
3411 không phải phải thu, phải trả), ghi sổ ra đúng Nợ, Có, số tiền; lập lại thì
cập nhật tại chỗ, không sinh tờ thứ hai; bản nháp bị sửa tay thì máy không ghi đè;
hook chặn phân bổ vượt nguyên giá có chạy ở bước ghi sổ thật không; một giao dịch
có ở hai bản sao kê chỉ vào sổ một lần.
Mọi thứ lùi về điểm lưu, xem nen.py. Không chạm hoá đơn điện tử, không sửa dữ liệu cũ.
"""

from unittest.mock import patch

import frappe
from frappe.utils import flt, nowdate

from vagabond import but_toan_nhap as BN
from vagabond import chi_phi_242 as C
from vagabond import chi_phi_meta as M
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.he_so_252 import _luu
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la


def _tk(ct, so, goc, ten):
	"""Tài khoản lá theo số hiệu; bench dựng từ sơ đồ chuẩn có thể thiếu thì dựng
	trong điểm lưu, lùi cùng mọi thứ khác. Site thật đã có sẵn."""
	tk = frappe.db.get_value("Account", {"company": ct, "account_number": so, "is_group": 0, "disabled": 0}, "name")
	if tk:
		return tk
	cha = frappe.db.get_value("Account", {"company": ct, "root_type": goc, "is_group": 1}, "name", order_by="lft desc")
	dung("có nhóm tài khoản %s" % goc, bool(cha))
	return _luu(frappe.get_doc(dict(doctype="Account", company=ct, account_name=ten, account_number=so,
		parent_account=cha, account_currency="VND", is_group=0))).name


def _tien_mat(ct):
	return (frappe.db.get_value("Account", {"company": ct, "account_type": "Cash", "is_group": 0, "disabled": 0}, "name")
		or frappe.db.get_value("Account", {"company": ct, "account_type": "Bank", "is_group": 0, "disabled": 0}, "name"))


def _so_cai(je):
	return sorted((r.account, flt(r.debit), flt(r.credit)) for r in frappe.get_all(
		"GL Entry", filters={"voucher_type": "Journal Entry", "voucher_no": je, "is_cancelled": 0},
		fields=["account", "debit", "credit"]))


def _khoan_242(ct, so_tien):
	"""Một khoản 242 thật: bút toán Nợ 242 / Có tiền mặt đã ghi sổ, rồi quét bảng kê."""
	tk242 = _tk(ct, "242", "Asset", "KT674 Chi phí chờ phân bổ")
	cc = frappe.db.get_value("Company", ct, "cost_center")
	je = frappe.get_doc(dict(doctype="Journal Entry", company=ct, posting_date=nowdate(), voucher_type="Journal Entry",
		user_remark="KT674 ghi nhận khuôn inox vào 242", accounts=[
			dict(account=tk242, debit_in_account_currency=so_tien, cost_center=cc),
			dict(account=_tien_mat(ct), credit_in_account_currency=so_tien, cost_center=cc)]))
	_luu(je)
	khong_nem("ghi sổ bút toán ghi nhận 242", je.submit)
	C.quet(ct)
	ten = frappe.db.get_value(C.DT, {"khoa": "Journal Entry:%s" % je.name}, "name")
	dung("bảng kê có khoản cho bút toán ghi nhận", ten)
	return ten, tk242, cc


@ca("v674 thật: khoản 242 khai 3 tháng, lập nháp tháng (lập lại cập nhật tại chỗ), ghi sổ Nợ 6273 / Có 242; tháng đó không phân bổ trùng; phân bổ tay vượt bị chặn ở ghi sổ")
def _phan_bo():
	ct = nen.cong_ty()
	ky = BN.ky_cua(nowdate())
	tkcp = _tk(ct, "6273", "Expense", "KT674 Chi phí dụng cụ sản xuất")
	with patch.object(C, "_cty", lambda cty=None: ct):
		ten, tk242, cc = _khoan_242(ct, 300000)
		if not ten:
			return
		khong_nem("khai 3 tháng", lambda: C.khai(ten, so_ky=3, ky_bat_dau=ky, bo_phan=cc, tk_chi_phi=tkcp, da_phan_bo_truoc=0))
		kq = khong_nem("lập nháp tháng", lambda: C.lap_thang(ky))
		if not kq:
			return
		je = frappe.get_doc("Journal Entry", kq["journal_entry"])
		la("nháp: hai dòng gắn khoản", sorted((r.account, flt(r.debit_in_account_currency), flt(r.credit_in_account_currency), r.vgb_khoan_242) for r in je.accounts),
			sorted([(tkcp, 100000.0, 0.0, ten), (tk242, 0.0, 100000.0, ten)]))
		la("chưa ghi sổ", je.docstatus, 0)
		kq2 = khong_nem("lập lại", lambda: C.lap_thang(ky))
		la("lập lại cập nhật đúng tờ cũ", (kq2 or {}).get("journal_entry"), je.name)
		la("lập lại là cập nhật", (kq2 or {}).get("cap_nhat"), 1)
		khong_nem("ghi sổ tháng", lambda: C.ghi_so_thang(ky))
		la("sổ cái", _so_cai(je.name), sorted([(tkcp, 100000.0, 0.0), (tk242, 0.0, 100000.0)]))
		la("số đã phân bổ đọc từ sổ", C.da_phan_bo_theo_khoan([ten]).get(ten), 100000)
		try:
			C.lap_thang(ky)
			dung("lập lại tháng đã ghi sổ phải báo không còn khoản", False)
		except Exception as e:
			dung("báo không còn khoản: %s" % nen.cau_loi(e), "không còn khoản" in nen.cau_loi(e))
		try:
			C.phan_bo_tay(ten, ky, 250000)
			dung("phân bổ tay vượt phải bị chặn", False)
		except Exception as e:
			dung("chặn vượt: %s" % nen.cau_loi(e), "vượt" in nen.cau_loi(e))
		# Đường Desk: tự lập bút toán gắn khoản, vượt nguyên giá thì hook chặn ở submit.
		tay = frappe.get_doc(dict(doctype="Journal Entry", company=ct, posting_date=nowdate(), voucher_type="Journal Entry",
			user_remark="KT674 phân bổ tay trên Desk", accounts=[
				dict(account=tkcp, debit_in_account_currency=250000, cost_center=cc, vgb_khoan_242=ten),
				dict(account=tk242, credit_in_account_currency=250000, cost_center=cc, vgb_khoan_242=ten)]))
		_luu(tay)
		try:
			tay.submit()
			dung("hook phải chặn bút toán Desk vượt nguyên giá", False)
		except Exception as e:
			dung("hook chặn vượt khi ghi sổ thật: %s" % nen.cau_loi(e), "chỉ còn" in nen.cau_loi(e))
		kq3 = khong_nem("phân bổ tay phần còn lại", lambda: C.phan_bo_tay(ten, ky, 200000, ghi_so=1))
		la("đã phân bổ đủ nguyên giá", C.da_phan_bo_theo_khoan([ten]).get(ten), 300000)
		la("ghi sổ ngay", (kq3 or {}).get("da_ghi_so"), 1)


@ca("v674 thật: bút toán nháp phân bổ bị kế toán sửa tay thì lập lại không ghi đè; bỏ nháp rồi lập lại được")
def _sua_tay():
	ct = nen.cong_ty()
	ky = BN.ky_cua(nowdate())
	tkcp = _tk(ct, "6273", "Expense", "KT674 Chi phí dụng cụ sản xuất")
	with patch.object(C, "_cty", lambda cty=None: ct):
		ten, tk242, cc = _khoan_242(ct, 600000)
		if not ten:
			return
		khong_nem("khai 6 tháng", lambda: C.khai(ten, so_ky=6, ky_bat_dau=ky, bo_phan=cc, tk_chi_phi=tkcp, da_phan_bo_truoc=0))
		kq = khong_nem("lập nháp", lambda: C.lap_thang(ky))
		if not kq:
			return
		je = frappe.get_doc("Journal Entry", kq["journal_entry"])
		for r in je.accounts:
			if flt(r.debit_in_account_currency):
				r.debit_in_account_currency = 90000
			else:
				r.credit_in_account_currency = 90000
		je.flags.ignore_permissions = True
		khong_nem("kế toán sửa tay bản nháp", lambda: je.save(ignore_permissions=True))
		try:
			C.lap_thang(ky)
			dung("lập lại phải dừng vì bản nháp đã sửa tay", False)
		except Exception as e:
			dung("dừng vì sửa tay: %s" % nen.cau_loi(e), "sửa tay" in nen.cau_loi(e))
		la("bản sửa tay giữ nguyên", sorted(flt(r.debit_in_account_currency) + flt(r.credit_in_account_currency) for r in frappe.get_doc("Journal Entry", je.name).accounts), [90000.0, 90000.0])
		khong_nem("bỏ bản nháp", lambda: C.bo_nhap_thang(ky))
		kq2 = khong_nem("lập lại sau khi bỏ", lambda: C.lap_thang(ky))
		dung("lập tờ mới", kq2 and kq2["journal_entry"] != je.name)


def _nguon(ct, mau, tu, den):
	n = frappe.get_doc(dict(doctype="Vagabond Doi Soat Nguon", company=ct, nhom="Thẻ tín dụng", vendor="Shinhan", mau=mau,
		tu_ngay=tu, den_ngay=den, trang_thai="Đã nhận", kenh_nhan="Hộp thư đối soát", duong_vao="Từ thư"))
	return _luu(n).name


def _dong_the(ct, nguon, ngd, nbt, dv, tien, n=1):
	d = frappe.get_doc(dict(doctype="Vagabond Doi Soat Dong", nguon=nguon, company=ct, nhom="Thẻ tín dụng", vendor="Shinhan",
		khoa="KT674-" + frappe.generate_hash(length=12), ma_su_kien="0000:%s:%s:%s:%d:%d" % (ngd, nbt, dv, tien, n),
		ngay=nbt, loai="phat_sinh", ma_don=dv, mo_ta=dv, thuc_nhan=tien))
	return _luu(d).name


@ca("v674 thật: chi phí Meta tháng từ hai bản sao kê vào sổ MỘT lần, Nợ 6417 / Có 3411; lập lại cập nhật tại chỗ; giao dịch về sau lập bút toán bổ sung chỉ phần mới")
def _meta():
	ct = nen.cong_ty()
	ky = BN.cong_thang(BN.ky_cua(nowdate()), -2)
	tkqc = _tk(ct, "6417", "Expense", "KT674 Chi phí dịch vụ mua ngoài bán hàng")
	_tk(ct, "6427", "Expense", "KT674 Chi phí dịch vụ mua ngoài quản lý")
	tkthe = _tk(ct, "3411", "Liability", "KT674 Các khoản đi vay")
	dau, cuoi = BN.ngay_dau_thang(ky), BN.ngay_cuoi_thang(ky)
	from datetime import timedelta

	pdf = _nguon(ct, M.MAU_PDF, dau, cuoi + timedelta(days=15))
	bang = _nguon(ct, M.MAU_BANG, dau, cuoi)
	n5, n7 = str(dau + timedelta(days=4)), str(dau + timedelta(days=6))
	n18, n20 = str(dau + timedelta(days=17)), str(dau + timedelta(days=19))
	for ng in (pdf, bang):
		_dong_the(ct, ng, n5, n7, "FACEBK *KT674A", 16500000)
		_dong_the(ct, ng, n18, n20, "FACEBK *KT674B", 4057590)
	_dong_the(ct, pdf, n18, n20, "ZaloPay*KT674", 99000)
	with patch.object(M, "_cty", lambda cty=None: ct):
		kq = khong_nem("lập nháp Meta", lambda: M.lap(ky))
		if not kq:
			return
		je = frappe.get_doc("Journal Entry", kq["journal_entry"])
		la("nháp: Nợ 6417 hai giao dịch, Có 3411", sorted((r.account, flt(r.debit_in_account_currency), flt(r.credit_in_account_currency)) for r in je.accounts),
			sorted([(tkqc, 20557590.0, 0.0), (tkthe, 0.0, 20557590.0)]))
		kq2 = khong_nem("lập lại", lambda: M.lap(ky))
		la("lập lại cùng tờ", (kq2 or {}).get("journal_entry"), je.name)
		khong_nem("ghi sổ", lambda: M.ghi_so(ky))
		la("sổ cái", _so_cai(je.name), sorted([(tkqc, 20557590.0, 0.0), (tkthe, 0.0, 20557590.0)]))
		ct_thang = khong_nem("đọc đối soát", lambda: M.chi_tiet_thang(ky)) or {}
		la("ba con số: đã trừ thẻ bằng đã ghi sổ", (ct_thang.get("da_tru"), ct_thang.get("da_ghi_so"), ct_thang.get("trang_thai")), (20557590, 20557590, M.TH_KHOP))
		try:
			M.lap(ky)
			dung("không còn giao dịch mới thì không lập", False)
		except Exception as e:
			dung("báo không còn giao dịch: %s" % nen.cau_loi(e), "không còn giao dịch" in nen.cau_loi(e))
		_dong_the(ct, pdf, str(dau + timedelta(days=24)), str(dau + timedelta(days=26)), "FACEBK *KT674C", 1100000)
		kq3 = khong_nem("lập bổ sung", lambda: M.lap(ky))
		if kq3:
			dung("tờ bổ sung khác tờ đã ghi sổ", kq3["journal_entry"] != je.name)
			la("bổ sung chỉ phần mới", sorted(flt(r.debit_in_account_currency) for r in frappe.get_doc("Journal Entry", kq3["journal_entry"]).accounts if flt(r.debit_in_account_currency)), [1100000.0])
			# Codex #590: bấm lập lại tờ bổ sung không được lấy lại giao dịch của tờ đã ghi sổ.
			kq4 = khong_nem("lập lại tờ bổ sung", lambda: M.lap(ky))
			la("lập lại tờ bổ sung cùng tờ", (kq4 or {}).get("journal_entry"), kq3["journal_entry"])
			la("lập lại tờ bổ sung vẫn chỉ phần mới", sorted(flt(r.debit_in_account_currency) for r in frappe.get_doc("Journal Entry", kq3["journal_entry"]).accounts if flt(r.debit_in_account_currency)), [1100000.0])
