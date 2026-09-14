"""#317: duyệt qua Document thật, không gọi ngân hàng hoặc phát lệnh chuyển tiền."""
import frappe
from vagabond import de_nghi_chi as dc
from vagabond.khung.kiem_that.nen import ca, la
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _phieu_cho_chi


@ca('#317 chi phí qua kế toán, lưu lại vẫn chờ ngân hàng xác nhận')
def duyet_chi_phi():
	p = _phieu_cho_chi(317123)
	frappe.db.set_value(p.doctype, p.name, {'trang_thai': dc.TT_CHO_DUYET,
		'quy_tac_317': 0, 'phuong_thuc': 'Tiền mặt'})
	dc.duyet(p.name)
	p.reload()
	la('người phụ trách đưa về kế toán', p.trang_thai, dc.TT_CHO_KE_TOAN)
	dc.duyet(p.name)
	p.reload()
	la('kế toán duyệt chưa phải ngân hàng đã chi', p.trang_thai, dc.TT_HOAN_TAT)
	la('không tự sinh giao dịch ngân hàng', p.ma_gd or '', '')


@ca('#317 hoàn ứng cũ: kế toán phải ghi lý do, phiếu mới không được miễn YCPS')
def hoan_ung_cu():
	tu = _phieu_cho_chi(617123)
	frappe.db.set_value(tu.doctype, tu.name, {'loai_nghiep_vu': dc.NV_TAM_UNG,
		'trang_thai': dc.TT_DA_CHI, 'quy_tac_317': 0, 'yeu_cau_phat_sinh': None})
	p = _phieu_cho_chi(617123)
	frappe.db.set_value(p.doctype, p.name, {'loai_nghiep_vu': dc.NV_HOAN_UNG,
		'thuoc_tam_ung': tu.name, 'trang_thai': dc.TT_CHO_KE_TOAN, 'quy_tac_317': 1})
	p.reload()
	la('DB xác nhận nguồn cũ', dc._phieu_kiem_317(p).get('_hoan_ung_cu'), True)
	try:
		dc.duyet(p.name)
	except frappe.ValidationError as e:
		la('chặn vì thiếu lý do', 'lý do' in str(e), True)
	else:
		raise AssertionError('Không được duyệt ngoại lệ thiếu lý do')
	p.reload(); la('chưa đổi trạng thái', p.trang_thai, dc.TT_CHO_KE_TOAN)
	# Đổi nguồn sang quy tắc mới phải mất ngoại lệ, dù client gửi cờ giả.
	frappe.db.set_value(tu.doctype, tu.name, 'quy_tac_317', 1)
	p._hoan_ung_cu = True
	la('nguồn mới không được miễn', dc._phieu_kiem_317(p).get('_hoan_ung_cu'), False)
	frappe.db.set_value(tu.doctype, tu.name, 'quy_tac_317', 0)
	dc.duyet(p.name, ghi_chu='Đã kiểm biên nhận, đối chiếu khoản tạm ứng lịch sử.')
	p.reload(); la('chờ ngân hàng sau duyệt', p.trang_thai, dc.TT_HOAN_TAT)
	la('có lịch sử ngoại lệ', bool(frappe.db.exists('Comment', {'reference_doctype': p.doctype,
		'reference_name': p.name, 'content': ['like', '%thiếu YCPS%']})), True)


@ca('#317 tạm ứng nhỏ mới: chi thực tế vượt ứng vẫn tới kế toán kiểm ngoại lệ')
def hoan_ung_nho():
	tu = _phieu_cho_chi(400000)
	frappe.db.set_value(tu.doctype, tu.name, {'loai_nghiep_vu': dc.NV_TAM_UNG,
		'trang_thai': dc.TT_DA_CHI, 'quy_tac_317': 1, 'yeu_cau_phat_sinh': None})
	p = _phieu_cho_chi(600000)
	frappe.db.set_value(p.doctype, p.name, {'loai_nghiep_vu': dc.NV_HOAN_UNG,
		'thuoc_tam_ung': tu.name, 'trang_thai': dc.TT_CHO_KE_TOAN, 'quy_tac_317': 1})
	p.reload(); p.save(ignore_permissions=True)
	la('nguồn nhỏ hợp lệ không YCPS', dc._phieu_kiem_317(p).get('_hoan_ung_cu'), True)
	try:
		dc.duyet(p.name)
	except frappe.ValidationError as e:
		la('vẫn bắt lý do', 'lý do' in str(e), True)
	else:
		raise AssertionError('Thiếu lý do vẫn duyệt được')
	dc.duyet(p.name, ghi_chu='Đã kiểm chứng từ chi thực tế vượt số tạm ứng nhỏ.')
	p.reload(); la('chờ chi sau kiểm', p.trang_thai, dc.TT_HOAN_TAT)


@ca('#317 YCPS mất: vẫn mở chi tiết và trả ngữ cảnh không hợp lệ')
def ycps_da_mat():
	p = _phieu_cho_chi(617123)
	frappe.db.set_value(p.doctype, p.name, {'loai_nghiep_vu': dc.NV_TAM_UNG,
		'yeu_cau_phat_sinh': 'YCPS-KIEM-DA-MAT-317', 'quy_tac_317': 1})
	p.reload()
	la('YCPS mất không hợp lệ', dc._phieu_kiem_317(p).get('_ycps_hop_le'), False)
	ra = dc.chi_tiet(p.name)
	la('vẫn mở đúng phiếu', ra.get('name'), p.name)


@ca('#317 nguồn mới trên trần thiếu YCPS: không miễn và không lưu hoàn ứng')
def nguon_moi_vuot_tran():
	tu = _phieu_cho_chi(800000)
	frappe.db.set_value(tu.doctype, tu.name, {'loai_nghiep_vu': dc.NV_TAM_UNG,
		'trang_thai': dc.TT_DA_CHI, 'quy_tac_317': 1, 'yeu_cau_phat_sinh': None})
	p = _phieu_cho_chi(900000)
	frappe.db.set_value(p.doctype, p.name, {'loai_nghiep_vu': dc.NV_HOAN_UNG,
		'thuoc_tam_ung': tu.name, 'quy_tac_317': 1})
	p.reload()
	la('không miễn trần nguồn mới', dc._phieu_kiem_317(p).get('_hoan_ung_cu'), False)
	try:
		p.save(ignore_permissions=True)
	except frappe.ValidationError as e:
		la('lỗi đúng trần', '500.000' in str(e), True)
	else:
		raise AssertionError('Nguồn mới vượt trần thiếu YCPS vẫn lưu được')
