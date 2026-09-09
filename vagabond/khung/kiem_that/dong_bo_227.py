"""Tái hiện dấu xong sai: chỉ đưa tờ thiếu chứng từ thật về hàng đợi."""
import frappe
from vagabond import minvoice_chung_tu as mv
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon, _phieu, _luu


@ca('#227 nguồn thật: dấu xong sai được mở lại, không dựng lại tờ đã có PI hoặc đã hủy')
def _dau_sai():
    ds = [_nguon([], 8000, 108000) for _ in range(4)]
    for d in ds:
        frappe.db.set_value('MInvoice Invoice', d.name, dict(da_tao_chung_tu=1,
            trang_thai='Gốc', ly_do_bo_qua='Item Wise Tax Details lỗi cũ'))
    hd = _phieu([('Dòng thử giữ liên kết', 1, 100000)])
    hd.custom_minvoice_id = ds[1].name
    _luu(hd)
    frappe.db.set_value('MInvoice Invoice', ds[2].name, 'trang_thai', 'Đã huỷ')
    frappe.db.set_value('MInvoice Invoice', ds[3].name, 'loai', 'Đầu ra')
    ngay = frappe.utils.today()
    la('chỉ mở một tờ thiếu PI', mv._mo_lai_dau_sai(ngay, ngay, 10, [d.name for d in ds]), 1)
    la('giữ ba trường hợp còn lại', [frappe.db.get_value('MInvoice Invoice', d.name,
        'da_tao_chung_tu') for d in ds], [0, 1, 1, 1])
    la('giữ lỗi cũ làm căn cứ', frappe.db.get_value('MInvoice Invoice', ds[0].name,
        'ly_do_bo_qua'), 'Item Wise Tax Details lỗi cũ')
    la('chạy lại không mở lặp', mv._mo_lai_dau_sai(ngay, ngay, 10, [d.name for d in ds]), 0)
    la('không tạo thêm PI', frappe.db.count('Purchase Invoice', {'custom_minvoice_id': ds[0].name}), 0)
