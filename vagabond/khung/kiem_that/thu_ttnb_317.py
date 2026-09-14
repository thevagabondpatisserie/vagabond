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
