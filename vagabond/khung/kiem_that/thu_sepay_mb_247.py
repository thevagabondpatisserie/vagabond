"""#247: Bank Account cá nhân MB đi trọn đường SePay trên ERPNext thật.

Ca kiểm dựng tài khoản cá nhân trong điểm lưu, không dùng số tài khoản hay
khoá thật và không gọi ra SePay. Giao dịch giả phải vào đúng Bank Account,
chạy lại không sinh đôi, còn tài khoản phải hiện đúng ở luồng hoàn ứng.
"""

from unittest.mock import patch

import frappe
from frappe.utils import now_datetime, today

from vagabond import de_nghi_chi, ho_so_tt, sepay
from vagabond.khung.kiem_that.nen import (
	_DA_TAO, _mot, ca, cong_ty, dung, la, mot_nha_cung_cap,
)


def _so_thu():
	"""Dãy số chỉ sống trong savepoint, đủ khác nhau giữa các lượt kiểm."""
	return "247" + now_datetime().strftime("%H%M%S%f")[-11:]


def _bank_mb():
	"""Lấy đúng danh mục MB; nếu bench thiếu thì dựng bằng nguồn Napas chuẩn."""
	from vagabond.ngan_hang import chuan_hoa_hoac_bao

	truoc = set(frappe.get_all("Bank", pluck="name", limit_page_length=0))
	ten = chuan_hoa_hoac_bao("MB")
	if ten not in truoc:
		_DA_TAO.append(("Bank", ten))
	return ten


def _tai_khoan_ca_nhan(so_tk, ncc):
	cty = cong_ty()
	tk_141 = _mot("Account", {
		"company": cty, "is_group": 0, "disabled": 0,
		"name": ["like", "141%"],
	})
	if not tk_141:
		cha = _mot("Account", {"company": cty, "root_type": "Asset", "is_group": 1}, "lft asc")
		if not cha:
			frappe.throw("Công ty thử chưa có nhóm tài sản để dựng tài khoản 141 trong điểm lưu.")
		ma = "141247" + frappe.generate_hash(length=5).upper()
		tk = frappe.get_doc({
			"doctype": "Account", "account_name": "Tạm ứng kiểm MB #247",
			"account_number": ma, "company": cty, "parent_account": cha,
			"root_type": "Asset", "is_group": 0, "account_currency": "VND",
		})
		tk.insert(ignore_permissions=True)
		_DA_TAO.append((tk.doctype, tk.name))
		tk_141 = tk.name
	b = frappe.get_doc({
		"doctype": "Bank Account",
		"account_name": "Kiểm MB cá nhân " + frappe.generate_hash(length=8),
		"bank": _bank_mb(),
		"bank_account_no": so_tk,
		"account": tk_141,
		"is_company_account": 0,
		"party_type": "Supplier",
		"party": ncc,
	})
	b.insert(ignore_permissions=True)
	_DA_TAO.append((b.doctype, b.name))
	return b


def _giao_dich(ba, tien, noi_dung):
	g = frappe.get_doc({
		"doctype": "Bank Transaction", "date": today(), "bank_account": ba,
		"deposit": 0, "withdrawal": tien, "currency": "VND",
		"description": noi_dung,
		"reference_number": "KIEM-247-" + frappe.generate_hash(length=7),
		"transaction_id": "KIEM-247-" + frappe.generate_hash(length=12),
	})
	g.insert(ignore_permissions=True)
	_DA_TAO.append((g.doctype, g.name))
	g.submit()
	return g


def _phieu_cho_chi(tien):
	d = frappe.get_doc({
		"doctype": de_nghi_chi.DT,
		"ten_khoan_chi": "Kiểm nguồn chi SePay #247",
		"loai_nghiep_vu": de_nghi_chi.NV_CHI_PHI,
		"ngay_can_tt": today(), "trang_thai": de_nghi_chi.TT_HOAN_TAT,
		"nguoi_tao": "Administrator", "company": cong_ty(),
		"hinh_thuc": de_nghi_chi.HT_NHAN_VIEN,
		"phuong_thuc": "Tiền mặt",
		"chung_tu_thue": de_nghi_chi.CT_KHONG_VAT,
		"cac_khoan": [{
			"noi_dung": "Kiểm nguồn chi SePay", "so_tien": tien,
			"phan_loai": "Chi phí quản lý doanh nghiệp",
		}],
	})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	frappe.db.set_value(d.doctype, d.name, "noi_dung_ck", de_nghi_chi.noi_dung_ck(d.name))
	d.reload()
	return d


@ca("#247 MB cá nhân: map, nạp bù và retry đi trọn ERPNext không sinh đôi")
def _mb_ca_nhan():
	cu = frappe.session.user
	frappe.set_user("Administrator")
	try:
		ncc = mot_nha_cung_cap()
		if not ncc:
			frappe.throw("Site thử chưa có Supplier để gắn người hoàn ứng MB.")
		so_tk = _so_thu()
		b = _tai_khoan_ca_nhan(so_tk, ncc)

		trang = sepay.tinh_trang()
		dong = [x for x in trang["ds_tai_khoan"] if x["ma"] == b.name]
		la("tài khoản cá nhân hiện trong bản đồ", len(dong), 1)
		la("bản đồ giữ đúng người", dong[0]["chu"], ncc)
		la("không biến thành tài khoản công ty", dong[0]["la_cong_ty"], 0)

		frappe.db.set_single_value(
			"Vagabond Settings", "sepay_chua_map", "000000,%s" % so_tk
		)
		kq_map = sepay.them_tai_khoan(" ".join((so_tk[:6], so_tk[6:])), b.name)
		la("map đúng Bank Account cá nhân", kq_map["ban_do"].get(so_tk), b.name)
		la("số vừa map rời danh sách chờ", so_tk in (sepay.cfg().get("sepay_chua_map") or ""), False)
		dung("tài khoản hiện ở luồng hoàn ứng", any(
			x["ma"] == b.name and x["nguoi"] == ncc
			for x in ho_so_tt.ds_tk_hoan_ung(ncc)["tk"]
		))

		ma_gd = int(now_datetime().strftime("%d%H%M%S%f")[-14:])
		giao_dich = [{
			"id": ma_gd,
			"account_number": " ".join((so_tk[:5], so_tk[5:])),
			"transaction_date": str(today()) + " 10:10:10",
			"amount_in": 0,
			"amount_out": 247000,
			"transaction_content": "KIEM THU MB HOAN UNG ISSUE 247",
			"reference_number": "KIEM-247",
		}]
		with patch.object(sepay, "_goi_userapi", return_value=giao_dich):
			lan_dau = sepay.nap_bu(
				so_tk=so_tk, tu_ngay=today(), den_ngay=today(), so_trang=1, that=1
			)
			lan_hai = sepay.nap_bu(
				so_tk=so_tk, tu_ngay=today(), den_ngay=today(), so_trang=1, that=1
			)

		ma = sepay.TIEN_TO + str(ma_gd)
		bt = frappe.db.get_value("Bank Transaction", {"transaction_id": ma}, "name")
		dung("lần đầu tạo sao kê", bool(bt))
		if bt:
			_DA_TAO.append(("Bank Transaction", bt))
			doc = frappe.get_doc("Bank Transaction", bt)
			la("sao kê vào đúng MB cá nhân", doc.bank_account, b.name)
			la("giữ đúng chiều tiền ra", float(doc.withdrawal), 247000.0)
			la("không đổi thành tiền vào", float(doc.deposit), 0.0)
		la("lần đầu thêm một dòng", lan_dau["them"], 1)
		la("retry không thêm dòng", lan_hai["them"], 0)
		la("retry nhận đúng giao dịch đã có", lan_hai["da_co"], 1)
		la("chỉ một transaction_id", frappe.db.count(
			"Bank Transaction", {"transaction_id": ma}
		), 1)

		# Hàng rào phải chạy bằng chính cửa lưu, không chỉ dò chữ trong mã.
		b2 = _tai_khoan_ca_nhan(so_tk, ncc)
		try:
			sepay.them_tai_khoan(so_tk, b2.name)
		except frappe.ValidationError as e:
			dung("lần hai nói rõ không ghi đè", "không tự ghi đè" in str(e))
		else:
			dung("không được ghi đè map bằng Bank Account khác", False)

		# Desk cũng không được đi vòng qua cửa app để lưu JSON xung đột.
		stg = frappe.get_doc(sepay.STG_SEPAY)
		stg.account_map = frappe.as_json({so_tk: b.name, " ".join((so_tk[:6], so_tk[6:])): b2.name})
		try:
			stg.save(ignore_permissions=True)
		except frappe.ValidationError as e:
			dung("Desk chặn cùng số trỏ hai túi", "nhiều Bank Account" in str(e))
		else:
			dung("Desk không được lưu bản đồ xung đột", False)
		stg.reload()
		la("DB giữ bản đồ trước lỗi", sepay._ban_do().get(so_tk), b.name)
	finally:
		frappe.set_user(cu)


@ca("#247 MB cá nhân: không tất toán phiếu chi công ty ở tự động hoặc chọn tay")
def _mb_khong_tat_toan_phieu_cong_ty():
	cu = frappe.session.user
	frappe.set_user("Administrator")
	try:
		ncc = mot_nha_cung_cap()
		so_tk = _so_thu()
		ca_nhan = _tai_khoan_ca_nhan(so_tk, ncc)
		cong_ty_ba = _mot("Bank Account", {
			"company": cong_ty(), "is_company_account": 1, "disabled": 0,
		})
		if not cong_ty_ba:
			frappe.throw("Bench chưa có Bank Account công ty để đối chứng nguồn chi.")
		tien = 247321
		p = _phieu_cho_chi(tien)
		gd_ca_nhan = _giao_dich(ca_nhan.name, tien, de_nghi_chi.noi_dung_ck(p.name))

		de_nghi_chi.khi_co_giao_dich(gd_ca_nhan.name)
		la("webhook cá nhân giữ phiếu chờ", frappe.db.get_value(p.doctype, p.name, "trang_thai"), de_nghi_chi.TT_HOAN_TAT)
		la("webhook cá nhân không gắn mã", frappe.db.get_value(p.doctype, p.name, "ma_gd") or "", "")
		de_nghi_chi.doi_soat()
		la("quét giờ giữ đúng phiếu đang thử", frappe.db.get_value(p.doctype, p.name, "trang_thai"), de_nghi_chi.TT_HOAN_TAT)
		la("quét giờ không gắn tiền cá nhân", frappe.db.get_value(p.doctype, p.name, "ma_gd") or "", "")
		try:
			de_nghi_chi.khop_tay(p.name, gd_ca_nhan.name)
		except frappe.ValidationError as e:
			dung("chọn tay nói rõ tài khoản cá nhân", "tài khoản cá nhân" in str(e))
		else:
			dung("chọn tay phải chặn tiền cá nhân", False)

		ung_vien = de_nghi_chi.tim_gd_ra(p.name, so_ngay=1)["rows"]
		dung("màn chọn không bày tiền cá nhân", all(x["name"] != gd_ca_nhan.name for x in ung_vien))

		gd_cong_ty = _giao_dich(cong_ty_ba, tien, de_nghi_chi.noi_dung_ck(p.name))
		de_nghi_chi.khi_co_giao_dich(gd_cong_ty.name)
		la("đối chứng tiền công ty tất toán", frappe.db.get_value(p.doctype, p.name, "trang_thai"), de_nghi_chi.TT_DA_CHI)
		la("đối chứng gắn đúng dòng công ty", frappe.db.get_value(p.doctype, p.name, "ma_gd"), gd_cong_ty.name)
	finally:
		frappe.set_user(cu)


@ca('#273 Desk: map sai số, ngưng dùng, thiếu chủ và ngoài141 đều không lưu')
def _desk_map_sai():
	b = _tai_khoan_ca_nhan(_so_thu(), mot_nha_cung_cap())
	stg = frappe.get_doc(sepay.STG_SEPAY)
	cu = stg.account_map
	for nhan, so, tk, doi in [
		('không tồn tại', b.bank_account_no, 'KHONG-CO-273', {}),
		('sai số', '000000273', b.name, {}),
		('ngưng dùng', b.bank_account_no, b.name, {'disabled': 1}),
		('thiếu chủ', b.bank_account_no, b.name, {'party': ''}),
		('ngoài141', b.bank_account_no, b.name, {'account': frappe.db.get_value('Company', cong_ty(), 'default_receivable_account')}),
	]:
		goc = {k: b.get(k) for k in doi}
		if doi:
			frappe.db.set_value(b.doctype, b.name, doi)
		stg.account_map = frappe.as_json({so: tk})
		try:
			stg.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			dung('Desk phải chặn '+nhan, False)
		la('DB không đổi khi '+nhan, frappe.db.get_single_value(sepay.STG_SEPAY, 'account_map'), cu)
		if doi:
			frappe.db.set_value(b.doctype, b.name, goc)
		stg.reload()
	stg.account_map = frappe.as_json({b.bank_account_no: b.name})
	stg.save(ignore_permissions=True)
	stg.reload()
	la('đối chứng map hợp lệ lưu được', frappe.parse_json(stg.account_map)[b.bank_account_no], b.name)


@ca('#273 quyền thật: Sales không đọc được tài khoản SePay, kế toán đọc được')
def _quyen_doc_sepay():
	cu = frappe.session.user
	u = frappe.get_doc({'doctype': 'User', 'email': 'kt273-'+frappe.generate_hash(length=10)+'@example.invalid',
		'first_name': 'Kiểm quyền SePay', 'enabled': 1, 'send_welcome_email': 0,
		'roles': [{'role': 'Sales User'}]})
	u.insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	try:
		frappe.set_user(u.name)
		try:
			sepay.tinh_trang()
		except frappe.PermissionError:
			pass
		else:
			dung('Sales không được nhận dữ liệu ngân hàng', False)
		frappe.set_user('Administrator')
		u.add_roles('Accounts User')
		frappe.set_user(u.name)
		dung('kế toán đọc được danh sách', 'ds_tai_khoan' in sepay.tinh_trang())
	finally:
		frappe.set_user(cu)
