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


@ca('#227 hóa đơn âm: dòng quà giá0 và mô tả không bị đảo dấu, PI thật lưu được')
def _am_co_dong_khong_tien():
    dong = [mv.dong_tu_hoa_don(x, -1) for x in [
        {'ten': 'Quà thử giá0', 'sluong': -1, 'dgia': 0, 'thtien': 0, 'tchat': 2},
        {'ten': 'Mô tả điều chỉnh', 'sluong': None, 'dgia': None, 'thtien': 0},
        {'ten': 'Dòng hoàn thử', 'sluong': -1, 'dgia': 100000, 'thtien': -100000}]]
    hd = _phieu([('Dòng hoàn thử', -1, 100000)])
    hd.is_return = 1
    tk = frappe.db.get_value('Company', hd.company, 'default_expense_account')
    if not tk:
        frappe.throw('Ca hóa đơn âm cần tài khoản chi phí mặc định của công ty bench.')
    hd.set('items', [mv._dong_pi(x, tk) for x in dong])
    for d in hd.items:
        d.cost_center = hd.cost_center
    _luu(hd)
    hd.reload()
    la('core lưu đúng dấu cả3dòng', [d.qty for d in hd.items], [-1, -1, -1])
    la('không phát sinh tiền ở dòng0', [d.amount for d in hd.items], [0, 0, -100000])
    la('tổng tiền âm giữ nguyên', hd.grand_total, -100000)
    la('chỉ nháp, không ghi sổ', hd.docstatus, 0)
    la('không SLE', frappe.db.count('Stock Ledger Entry', {'voucher_no': hd.name}), 0)
    la('không GL', frappe.db.count('GL Entry', {'voucher_no': hd.name}), 0)
