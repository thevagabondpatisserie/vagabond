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


def _tai_khoan_cong_ty_moi(goc):
	"""ERPNext bắt mỗi Bank Account công ty dùng một GL Account riêng."""
	ba = frappe.copy_doc(frappe.get_doc('Bank Account', goc))
	tk = frappe.copy_doc(frappe.get_doc('Account', ba.account))
	tk.account_name = 'Ngân hàng kiểm SePay ' + frappe.generate_hash(length=8)
	tk.account_number = '112' + _so_thu()
	tk.insert(ignore_permissions=True)
	_DA_TAO.append((tk.doctype, tk.name))
	ba.account = tk.name
	ba.account_name = 'Kiểm công ty SePay ' + frappe.generate_hash(length=8)
	ba.bank_account_no = _so_thu()
	ba.insert(ignore_permissions=True)
	_DA_TAO.append((ba.doctype, ba.name))
	return ba


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
	# #317 yêu cầu biên nhận ngay khi tạo. Dựng File thử thật trước phiếu,
	# cùng cách app tải tệp rồi gửi URL trong dòng; không tắt validator.
	f = frappe.get_doc({"doctype": "File", "file_name": "bien-nhan-kiem-317.txt",
		"content": "Biên nhận thử tích hợp, không phải chứng từ thanh toán.", "is_private": 1})
	f.insert(ignore_permissions=True)
	_DA_TAO.append((f.doctype, f.name))
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
			"noi_dung": "Kiểm nguồn chi SePay", "so_tien": tien, "tep": frappe.as_json([f.file_url]),
			"phan_loai": "Chi phí quản lý doanh nghiệp",
		}],
	})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	f.db_set({"attached_to_doctype": d.doctype, "attached_to_name": d.name})
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


@ca("#502 MB cá nhân thiếu chủ quỹ: không khớp TTNB tự động hoặc chọn tay")
def _mb_khong_tat_toan_phieu_cong_ty():
	cu = frappe.session.user
	frappe.set_user("Administrator")
	try:
		ncc = mot_nha_cung_cap()
		so_tk = _so_thu()
		ca_nhan = _tai_khoan_ca_nhan(so_tk, ncc)
		frappe.db.set_value("Bank Account", ca_nhan.name, "party", "", update_modified=False)
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
			dung("chọn tay nói rõ tài khoản cá nhân", "nguồn chi" in str(e))
		else:
			dung("chọn tay phải chặn tiền cá nhân", False)

		from vagabond import doi_soat_sepay as dss
		ung_vien = dss.ung_vien("ttnb", p.name, so_ngay=1, tai_khoan=ca_nhan.name)["rows"]
		dong_ca_nhan = [x for x in ung_vien if x["name"] == gd_ca_nhan.name]
		la("#328 màn chọn vẫn có tiền cá nhân", len(dong_ca_nhan), 1)
		la("#328 dòng chưa dùng được", dong_ca_nhan[0]["dung_duoc"], 0)
		dung("#328 giải thích nguồn", "nguồn chi" in dong_ca_nhan[0]["vi_sao_khong"])
		from vagabond import doi_soat_sepay as dss
		kq = dss.tu_dong("ttnb", p.name, so_ngay=1)
		la("#328 tự động không gắn", kq["da_khop"], 0)
		dung("#328 tự động báo nguồn", any("nguồn chi" in r["vi_sao"] for r in kq["xem_lai"]))

		# #327: đối chứng phải qua cấu hình SePay thật, không chỉ có Bank Account.
		# Tài khoản thử riêng để ca không phụ thuộc mapping của seed/ca trước.
		ba = _tai_khoan_cong_ty_moi(cong_ty_ba)
		gd_cong_ty = _giao_dich(ba.name, tien, de_nghi_chi.noi_dung_ck(p.name))
		de_nghi_chi.khi_co_giao_dich(gd_cong_ty.name)
		la("chưa mapping vẫn chờ", frappe.db.get_value(p.doctype, p.name, "trang_thai"), de_nghi_chi.TT_HOAN_TAT)
		la("chưa mapping không gắn", frappe.db.get_value(p.doctype, p.name, "ma_gd") or "", "")
		sepay.them_tai_khoan(ba.bank_account_no, ba.name)
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
	frappe.db.set_value(b.doctype,b.name,'disabled',1)
	stg.enabled = 1
	stg.save(ignore_permissions=True); stg.reload()
	la('map cũ ngưng dùng không chặn lưu công tắc',stg.enabled,1)
	moi = _tai_khoan_ca_nhan(_so_thu(), mot_nha_cung_cap())
	stg.account_map = frappe.as_json({b.bank_account_no:b.name,moi.bank_account_no:moi.name})
	stg.save(ignore_permissions=True); stg.reload()
	la('thêm tuyến hợp lệ dù tuyến cũ ngưng dùng',frappe.parse_json(stg.account_map)[moi.bank_account_no],moi.name)
	stg.account_map = frappe.as_json({b.bank_account_no:b.name,'000000273':'KHONG-CO-273'})
	try:
		stg.save(ignore_permissions=True)
	except frappe.ValidationError:
		pass
	else:
		dung('thêm map sai vẫn chặn dù có map cũ',False)


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
		u.set('roles', [{'role': 'Accounts User'}])
		u.save(ignore_permissions=True)
		frappe.clear_cache(user=u.name)
		frappe.set_user(u.name)
		dung('kế toán đọc được danh sách', 'ds_tai_khoan' in sepay.tinh_trang())
		frappe.set_user('Administrator')
		u.set('roles',[{'role':'Accounts Manager'}]); u.save(ignore_permissions=True)
		b = _tai_khoan_ca_nhan(_so_thu(),mot_nha_cung_cap())
		frappe.clear_cache(user=u.name); frappe.set_user(u.name)
		la('Accounts Manager độc lập khai map',sepay.them_tai_khoan(b.bank_account_no,b.name)['ok'],1)
		dung('Accounts Manager độc lập soi khóa',bool(sepay.soi_khoa()))
	finally:
		frappe.set_user(cu)


@ca('#327 hoàn tiền trực tiếp: kiểm mapping trên sao kê và hồ sơ thật trước ghi')
def _hoan_truc_tiep_mapping():
	from vagabond import hoan_tien, don_huy
	from vagabond.khung.kiem_that.thu_don_huy import _ho_so_thu
	cu = frappe.session.user
	frappe.set_user('Administrator')
	try:
		goc = _mot('Bank Account', {'company':cong_ty(), 'is_company_account':1, 'disabled':0})
		dung('bench có tài khoản công ty', bool(goc))
		ba = _tai_khoan_cong_ty_moi(goc)
		hs = _ho_so_thu(don_huy._khach_le_online())
		_DA_TAO.append((hs.doctype, hs.name))
		ma = '327' + frappe.generate_hash(length=8).upper()
		frappe.db.set_value(hs.doctype, hs.name, {'loai_hoan':hoan_tien.LOAI_HUY_PANCAKE, 'ma_don_pancake':ma, 'noi_dung_ck':'HOAN TIEN '+ma})
		gd = _giao_dich(ba.name, hs.so_tien, 'HOAN TIEN '+ma)
		# Chỉ thay bước phát sinh chứng từ: ca này kiểm ranh giới mapping/ghi DB.
		# Cặp Payment Entry thật đã được kiểm riêng trong thu_don_huy.
		with patch.object(hoan_tien, '_sinh_chung_tu', return_value={}) as sinh:
			kq = hoan_tien.sepay_tien_ra(ma_gd=gd.name)
			la('chưa nối không khớp', kq['khop'], 0)
			dung('có lý do cấu hình', bool(kq.get('vi_sao')))
			la('không ghi hồ sơ', frappe.db.get_value(hs.doctype,hs.name,'da_doi_soat'),0)
			la('không sinh chứng từ', sinh.call_count,0)
			sepay.them_tai_khoan(ba.bank_account_no,ba.name)
			kq = hoan_tien.sepay_tien_ra(mo_ta='payload giả',so_tien=1,ma_gd=gd.name)
			la('đã nối dùng đúng dữ liệu sao kê',kq['khop'],1)
			la('gắn đúng dòng',frappe.db.get_value(hs.doctype,hs.name,'ma_gd'),gd.name)
			la('gọi sinh một lần',sinh.call_count,1)
			lai = hoan_tien.sepay_tien_ra(ma_gd=gd.name)
			la('retry không khớp lại',lai['khop'],0)
			la('retry không sinh đôi',sinh.call_count,1)
	finally:
		frappe.set_user(cu)


@ca('#502 TTNB từ quỹ 141 nối APP cùng chủ, giữ chứng cứ và chống hoàn trùng FT/BT')
def _ttnb_hoan_ung_502():
	cu = frappe.session.user
	frappe.set_user('Administrator')
	try:
		ncc = mot_nha_cung_cap()
		b = _tai_khoan_ca_nhan(_so_thu(), ncc)
		sepay.them_tai_khoan(b.bank_account_no, b.name)
		p = _phieu_cho_chi(247502)
		g = _giao_dich(b.name, 247502, de_nghi_chi.noi_dung_ck(p.name))
		from vagabond import doi_soat_sepay as dss
		ra = dss.ung_vien('ttnb', p.name, so_ngay=1, tai_khoan=b.name)['rows']
		la('nguồn 141 được chọn', next(x for x in ra if x['name']==g.name)['dung_duoc'], 1)
		de_nghi_chi.khop_tay(p.name, g.name)
		p.reload()
		la('nhân viên đã nhận tiền', p.trang_thai, de_nghi_chi.TT_DA_CHI)
		la('bằng chứng là giao dịch cá nhân', p.ma_gd, g.name)
		de_nghi_chi.khi_co_giao_dich(g.name)
		la('webhook lặp giữ nguyên', frappe.db.get_value(p.doctype,p.name,'ma_gd'),g.name)
		goi_y = ho_so_tt.ds_phieu_noi_bo(ma_giao_dich=g.reference_number)['ds']
		la('gợi ý đúng phiếu trên đầu', goi_y[0]['ma'], p.name)
		la('lý do cùng giao dịch', goi_y[0]['goi_y'], 'Cùng giao dịch')
		dong = {'ngay_hd':today(),'noi_dung':'Kiểm TTNB hoàn ứng 502',
			'so_tien':247502,'ma_giao_dich':g.reference_number,'de_nghi_chi':p.name}
		kq = ho_so_tt.tao_hoan_ung(tk_hoan=b.name,dong=[dong],gui_luon=0)
		h = frappe.get_doc('Vagabond Ho So TT',kq['ma'])
		_DA_TAO.append((h.doctype,h.name))
		la('đúng người được hoàn',h.nha_cung_cap,ncc)
		la('đúng ngân hàng nhận',h.tk_nhan,b.name)
		la('chuẩn hóa chứng cứ',h.dong[0].ma_giao_dich,g.name)
		la('giữ TTNB',frappe.db.get_value(p.doctype,p.name,'ho_so_tt'),h.name)
		la('chưa ghi nhận công ty đã trả',h.ma_giao_dich or '', '')
		la('mới lập chưa sinh hóa đơn',h.dong[0].hoa_don or '', '')
		la('không dùng lại trong bảng sao kê',len([x for x in ho_so_tt.sepay_ocb(tai_khoan=b.name)['rows']
			if x['ma_giao_dich'] in (g.name,g.reference_number)]),0)
		# Đi thẳng Document, bỏ mã TTNB và đổi sang FT vẫn không hoàn trùng.
		frappe.db.savepoint('thu_trung_502')
		try:
			trung=frappe.copy_doc(h)
			trung.ma=ho_so_tt._sinh_ma()
			trung.dong[0].de_nghi_chi=None
			trung.dong[0].ma_giao_dich=g.reference_number
			trung.insert(ignore_permissions=True)
		except frappe.ValidationError as e:
			dung('FT gặp hồ sơ giữ BT', 'không hoàn ứng hai lần' in str(e))
		else:
			dung('không được tạo hồ sơ thứ hai',False)
		finally:
			frappe.db.rollback(save_point='thu_trung_502')
		# Một APP có hai dòng FT/BT cũng bị chặn trước khi tính hai lần hoàn.
		frappe.db.savepoint('thu_doi_502')
		try:
			h.append('dong',{'noi_dung':'Trùng mã khác','so_tien':247502,'ma_giao_dich':g.reference_number})
			h.save(ignore_permissions=True)
		except frappe.ValidationError as e:
			dung('bắt trùng trong hồ sơ', 'hai khoản' in str(e))
		else:
			dung('không được tăng gấp đôi hồ sơ',False)
		finally:
			frappe.db.rollback(save_point='thu_doi_502')
		# Đi tiếp đúng cửa duyệt, tạo PI thật rồi ghi PE từ sao kê công ty.
		from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _mon_dich_vu, _tk_ngan_hang, _unc_gia, _giao_dich_ngan_hang
		from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _ghi
		for ma_mon in (ho_so_tt.MON_CO_VAT, ho_so_tt.MON_KHONG_VAT):
			if not frappe.db.exists('Item', ma_mon):
				mon=frappe.copy_doc(frappe.get_doc('Item',_mon_dich_vu()))
				mon.item_code=ma_mon
				mon.item_name='Dịch vụ thử hoàn ứng'
				mon.insert(ignore_permissions=True)
				_DA_TAO.append(('Item',mon.name))
		h.reload()
		h.tk_chi=_tk_ngan_hang(cong_ty())
		h.save(ignore_permissions=True)
		ho_so_tt.duyet(h.name,'gui_fin')
		h.reload()
		if h.trang_thai==ho_so_tt.TT_CHO_FIN:
			ho_so_tt.duyet(h.name,'fin')
		ho_so_tt.duyet(h.name,'gd')
		h.reload()
		la('duyệt xong',h.trang_thai,ho_so_tt.TT_DA_DUYET)
		hd=h.dong[0].hoa_don
		dung('có hóa đơn mua thật',bool(hd))
		_DA_TAO.append(('Purchase Invoice',hd))
		la('đúng chi phí một lần',float(frappe.db.get_value('Purchase Invoice',hd,'grand_total')),247502.0)
		_unc_gia(h)
		g_ct=_giao_dich_ngan_hang(h.name,247502,cong_ty())
		_ghi(h,g_ct)
		h.reload()
		la('công ty trả bằng giao dịch khác',h.ma_giao_dich,g_ct.name)
		la('giữ chứng cứ trả nhân viên',h.dong[0].ma_giao_dich,g.name)
		la('công nợ đã hết',float(frappe.db.get_value('Purchase Invoice',hd,'outstanding_amount')),0.0)
		bo=ho_so_tt._but_toan_cua_ho_so(h.name)
		la('retry nhận ra đã làm',ho_so_tt.danh_dau_da_tra(h.name,gui_thu=0)['da_lam_roi'],1)
		la('không tạo thêm bút toán',ho_so_tt._but_toan_cua_ho_so(h.name),bo)
	finally:
		frappe.set_user(cu)


@ca('342 APP lập gửi ngay: dấu FIN lưu thật, không chỉ trạng thái chờ GD')
def _app_gui_fin_342():
	cu = frappe.session.user
	frappe.set_user('Administrator')
	try:
		ncc = mot_nha_cung_cap()
		b = _tai_khoan_ca_nhan(_so_thu(), ncc)
		# Khoản thử dưới ngưỡng chứng từ; ca này chỉ kiểm dấu duyệt lưu thật.
		kq = ho_so_tt.tao_hoan_ung(tk_hoan=b.name, gui_luon=1, dong=[{
			'noi_dung':'Kiểm dấu FIN gửi ngay', 'so_tien':342,
			'ngay_hd':today()}])
		h = frappe.get_doc('Vagabond Ho So TT', kq['ma'])
		_DA_TAO.append((h.doctype,h.name))
		la('chờ GD',h.trang_thai,ho_so_tt.TT_CHO_GD)
		la('FIN chính người gửi',h.fin_boi,'Administrator')
		dung('có giờ FIN',bool(h.fin_luc))
		la('chưa giả chữ ký GD',h.gd_boi or '','')
		la('chưa sinh hóa đơn',h.dong[0].hoa_don or '','')
	finally:
		frappe.set_user(cu)


def _nen_quy_342(tien=100000):
	from vagabond import tam_ung_app as tu
	b = _tai_khoan_ca_nhan(_so_thu(), mot_nha_cung_cap())
	# Lõi Bank Transaction chỉ đối chiếu GL có account_type Bank.
	quy = frappe.copy_doc(frappe.get_doc('Account', b.account))
	quy.account_name = 'Quỹ thử quyết toán '+frappe.generate_hash(length=6)
	quy.account_number = '141342'+frappe.generate_hash(length=5)
	quy.account_type = 'Bank'
	quy.insert(ignore_permissions=True);_DA_TAO.append((quy.doctype,quy.name))
	b.account=quy.name;b.save(ignore_permissions=True)
	cha = _mot('Account', {'company':cong_ty(),'root_type':'Asset','is_group':1}, 'lft asc')
	tk = frappe.get_doc({'doctype':'Account','company':cong_ty(),'parent_account':cha,
		'account_name':'Tiền mặt thử quỹ '+frappe.generate_hash(length=6),
		'account_number':'111342'+frappe.generate_hash(length=5), 'account_type':'Cash',
		'account_currency':'VND','is_group':0})
	tk.insert(ignore_permissions=True)
	_DA_TAO.append((tk.doctype,tk.name))
	g = frappe.get_doc({'doctype':'Bank Transaction','date':today(),'bank_account':b.name,
		'deposit':tien,'withdrawal':0,'currency':'VND','description':'Nộp tiền mặt thử quỹ',
		'reference_number':'KIEM-CAP-'+frappe.generate_hash(length=8)})
	g.insert(ignore_permissions=True)
	_DA_TAO.append((g.doctype,g.name));g.submit()
	ra = tu.ghi_nhan_cap(g.name,tk.name)
	_DA_TAO.append(('Journal Entry',ra['name']))
	return b,tk,g,frappe.get_doc('Journal Entry',ra['name'])


def _app_quy_342(b,tien):
	from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _tk_ngan_hang
	hd=_hoa_don_mua(tien)
	h=frappe.new_doc('Vagabond Ho So TT')
	h.ma,h.loai,h.ngay,h.trang_thai=ho_so_tt._sinh_ma(),'Hoan ung HD',today(),'Da duyet'
	h.nha_cung_cap=h.nguoi_ung=b.party
	h.tk_nhan=b.name
	h.tk_chi=_tk_ngan_hang(cong_ty())
	h.da_tam_ung=0
	h.append('dong',{'hoa_don':hd.name,'so_hd_ncc':hd.bill_no,'so_tien':tien,'con_no':tien})
	h.insert(ignore_permissions=True);_DA_TAO.append((h.doctype,h.name))
	return h,hd


@ca('342 Cấp quỹ bằng tiền vào, cấn đủ, retry và huỷ trả nguồn bằng GL lõi')
def _quy_day_du_342():
	from vagabond import tam_ung_app as tu
	cu=frappe.session.user;frappe.set_user('Administrator')
	try:
		b,tk,g,cap=_nen_quy_342()
		la('retry cấp cùng JE',tu.ghi_nhan_cap(g.name,tk.name)['name'],cap.name)
		g.reload();la('sao kê đã đối chiếu',g.status,'Reconciled')
		h,hd=_app_quy_342(b,70000)
		ra=tu.can(h.name,70000);_DA_TAO.append(('Journal Entry',ra['name']))
		h.reload();hd.reload()
		la('PI hết nợ do JE',float(hd.outstanding_amount),0.0)
		la('không phải chuyển thêm',float(h.con_lai),0.0)
		try:
			ho_so_tt.noi_dung_chuyen_khoan(h.name)
		except frappe.ValidationError as e:
			dung('không xuất lệnh chi toàn bộ lần nữa','không còn tiền phải chuyển' in str(e))
		else:
			dung('không tạo file chuyển tiền khi đã cấn đủ',False)
		la('còn nguồn cho lần sau',tu.danh_sach(b.name)['con_lai'],30000.0)
		la('retry cấn cùng JE',tu.can(h.name,70000)['name'],ra['name'])
		ho_so_tt.danh_dau_da_tra(h.name,gui_thu=0)
		la('retry hoàn tất',ho_so_tt.danh_dau_da_tra(h.name,gui_thu=0)['da_lam_roi'],1)
		la('không sinh PE tiền ra',frappe.db.count('Payment Entry',{'vgb_ho_so_tt':h.name}),0)
		gl=frappe.get_all('GL Entry',filters={'voucher_type':'Journal Entry','voucher_no':ra['name'],'is_cancelled':0},fields=['account','debit','credit'])
		la('có141 đúng khoản cấn',sum(float(x.credit)-float(x.debit) for x in gl if x.account==b.account),70000.0)
		try:
			cap.cancel()
		except frappe.ValidationError:
			pass
		else:
			dung('không huỷ nguồn đã cấn',False)
		tu.bo_can(h.name)
		h.reload();hd.reload()
		la('huỷ trả nguồn',tu.danh_sach(b.name)['con_lai'],100000.0)
		la('huỷ trả nợ',float(hd.outstanding_amount),70000.0)
		la('APP về đã duyệt',h.trang_thai,'Da duyet')
		la('retry bỏ cấn',tu.bo_can(h.name)['da_lam_roi'],1)
	finally:
		frappe.set_user(cu)


@ca('342 Cấn một phần: chỉ PE phần thiếu vào sao kê, đủ JE+PE mới hoàn tất')
def _quy_mot_phan_342():
	from vagabond import tam_ung_app as tu
	from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _unc_gia, _giao_dich_ngan_hang
	cu=frappe.session.user;frappe.set_user('Administrator')
	try:
		b,tk,g,cap=_nen_quy_342(30000)
		h,hd=_app_quy_342(b,70000)
		ra=tu.can(h.name,30000);_DA_TAO.append(('Journal Entry',ra['name']))
		_unc_gia(h)
		out=_giao_dich_ngan_hang(h.name,40000,cong_ty())
		ho_so_tt.danh_dau_da_tra(h.name,gui_thu=0)
		bo=ho_so_tt._but_toan_cua_ho_so(h.name)
		_DA_TAO.extend((x['doctype'],x['name']) for x in bo if x['doctype']=='Payment Entry')
		la('hai bút toán',len(bo),2)
		la('PE chỉ trả thêm',sum(float(x.get('paid_amount') or 0) for x in bo),40000.0)
		out.reload();la('sao kê chỉ nối PE',len(out.payment_entries),1)
		la('hết nợ',float(frappe.db.get_value('Purchase Invoice',hd.name,'outstanding_amount')),0.0)
		la('retry không trả thêm',ho_so_tt.danh_dau_da_tra(h.name,gui_thu=0)['da_lam_roi'],1)
	finally:
		frappe.set_user(cu)


@ca('342 Cấn lỗi giữa chừng rollback JE/nguồn; hai APP không dùng quá một nguồn')
def _quy_loi_342():
	from vagabond import tam_ung_app as tu
	from vagabond.vagabond.doctype.vagabond_ho_so_tt.vagabond_ho_so_tt import VagabondHoSoTT
	cu=frappe.session.user;frappe.set_user('Administrator')
	try:
		b,tk,g,cap=_nen_quy_342(100000)
		h,hd=_app_quy_342(b,70000)
		frappe.db.savepoint('kiem_loi_can342')
		try:
			with patch.object(VagabondHoSoTT,'save',side_effect=RuntimeError('loi luu thu')):
				tu.can(h.name,70000)
		except RuntimeError:
			frappe.db.rollback(save_point='kiem_loi_can342')
		else:
			dung('phải chịu lỗi sau khi đã submit JE',False)
		la('không JE dở',frappe.db.count('Journal Entry',{'vgb_ho_so_tt':h.name}),0)
		la('nguồn không mất',tu.danh_sach(b.name)['con_lai'],100000.0)
		la('PI không bị cấn dở',float(frappe.db.get_value('Purchase Invoice',hd.name,'outstanding_amount')),70000.0)
		ra=tu.can(h.name,70000);_DA_TAO.append(('Journal Entry',ra['name']))
		h2,hd2=_app_quy_342(b,40000)
		try:
			tu.can(h2.name,40000)
		except frappe.ValidationError as e:
			dung('lý do thiếu nguồn', 'còn lại' in str(e))
		else:
			dung('không dùng 110000 từ nguồn100000',False)
		la('APP hai không có JE',frappe.db.count('Journal Entry',{'vgb_ho_so_tt':h2.name}),0)
	finally:
		frappe.set_user(cu)
