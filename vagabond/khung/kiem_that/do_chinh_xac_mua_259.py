"""11595: chạy đúng dựng PI rồi save/submit, không làm tròn đơn giá trước nhân."""
from unittest.mock import patch
import frappe
from vagabond import minvoice_chung_tu as mv, dung_lai_hddt as dl, do_chinh_xac_mua as cx
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon, _phieu
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu


def _mon():
    mon = frappe.get_doc('Item', _mon_thu('KT-GIA259-' + frappe.generate_hash(length=9)))
    if not frappe.db.exists('UOM', 'Gram'):
        d = frappe.get_doc(dict(doctype='UOM', uom_name='Gram', must_be_whole_number=0))
        d.insert(ignore_permissions=True); nen._DA_TAO.append((d.doctype, d.name))
    mon.is_stock_item = 0
    mon.stock_uom = 'Gram'
    mon.set('uoms', [dict(uom='Gram', conversion_factor=1)])
    mon.save(ignore_permissions=True)
    return mon


def _doi_chung_tat_ban_sua(goc):
    """Tắt riêng policy mới trên core hiện tại, không nhận là checkout main.

Lỗi phải đúng tổng1.000.004/lệch4đ. Một lỗi setup khác vẫn làm ca đỏ.
Điểm lưu riêng dọn PI nháp do đường dựng đã insert trước khi báo lệch.
"""
    ten_diem = 'gia259_doi_chung'
    truoc = frappe.db.count('Purchase Invoice')
    with nen._cach_ly():
        frappe.db.savepoint(ten_diem)
        try:
            with patch.object(cx, 'quy_uoc', return_value=None):
                try:
                    mv.dung_hoa_don_mua(goc.as_dict())
                except frappe.ValidationError as e:
                    dung('đối chứng phải đúng tổng sai1000004', 'tổng 1,000,004 đ' in str(e))
                    dung('đối chứng phải đúng lệch4đ', 'lệch 4 đ' in str(e))
                else:
                    dung('tắt bản sửa phải tái hiện lỗi lõi cắt đơn giá', False)
        finally:
            # PI lỗi chưa được hàm dựng trả tên nên chưa vào _DA_TAO.
            # Xóa cache riêng các PI fixture trước rollback, không xóa chứng từ.
            for ma in frappe.get_all('Purchase Invoice',
                    filters={'custom_minvoice_id': goc.name}, pluck='name'):
                frappe.clear_document_cache('Purchase Invoice', ma)
            frappe.db.rollback(save_point=ten_diem)
    la('đối chứng không để thêm PI nháp', frappe.db.count('Purchase Invoice'), truoc)
    la('nguồn đối chứng không có PI sót', frappe.db.count('Purchase Invoice',
        {'custom_minvoice_id': goc.name}), 0)


def _luong(qty, rate, net, tax, doi_chung=False):
    mon = _mon()
    raw = [dict(ten='Decal thử259', sluong=qty, dgia=rate,
        thtien=net, dvtinh='Gram', tchat=1, stckhau=0)]
    goc = _nguon(raw, tax, net+tax)
    du_nguon = goc.chi_tiet
    ncc = nen.mot_nha_cung_cap()
    # Chỉ định tuyến mã/NCC fixture; toàn bộ dựng dòng, tính tiền và GL là core thật.
    with patch.object(mv, '_tim_ncc', return_value=(ncc, '')), \
         patch.object(mv, '_tra_ma_hang', return_value=(mon.name, 'Gram', 1)):
        if doi_chung:
            _doi_chung_tat_ban_sua(goc)
        ma = mv.dung_hoa_don_mua(goc.as_dict())
        nen._DA_TAO.append(('Purchase Invoice', ma))
        hd = frappe.get_doc('Purchase Invoice', ma)
        for lan in range(2):
            hd.save(ignore_permissions=True); hd.reload()
            la('giữ đơn giá nguồn sau reload/save', hd.items[0].rate, rate)
            la('giữ số lượng nguồn', hd.items[0].qty, qty)
            la('một dòng, không thêm phí để bù', len(hd.items), 1)
            la('không chiết khấu để bù', hd.discount_amount, 0)
            la('thành tiền đúng nguồn', hd.items[0].amount, net)
            la('net đúng nguồn', hd.net_total, net)
            la('gross đúng nguồn', hd.grand_total, net+tax)
        la('dự kiến cũng dùng đúng precision', dl.du_kien_tong(hd, goc.as_dict()), net+tax)
        # Nhánh dựng lại phải dùng cùng phép tính, không sinh khoản phí/giảm bù4đ.
        thu = frappe.copy_doc(hd)
        dl._dung_dong_tai_cho(thu, goc.as_dict())
        la('dựng lại đúng một dòng', len(thu.items), 1)
        la('dựng lại giữ qty/rate', (thu.items[0].qty, thu.items[0].rate), (qty, rate))
        la('dựng lại không giảm bù', thu.discount_amount, 0)
        hd.flags.ignore_permissions = True
        hd.submit(); hd.reload()
        la('submit giữ giá nguồn', hd.items[0].rate, rate)
        la('submit giữ gross', hd.grand_total, net+tax)
        gl = nen.so_cai_cua(hd)
        dung('có GL thật', bool(gl))
        la('GL cân', round(sum(d.debit-d.credit for d in gl), 2), 0)
        la('GL chi phí bằng tiền nguồn', round(sum(d.debit-d.credit for d in gl
            if d.account == hd.items[0].expense_account), 2), net)
        la('không ghi kho', frappe.db.count('Stock Ledger Entry',
            {'voucher_type': hd.doctype, 'voucher_no': hd.name}), 0)
        hd.cancel()
        gl = frappe.get_all('GL Entry', filters={'voucher_type': hd.doctype, 'voucher_no': hd.name},
            fields=['account', 'debit', 'credit'])
        for tk in {d.account for d in gl}:
            la('hủy đảo đủ tài khoản ' + tk, round(sum(d.debit-d.credit for d in gl if d.account == tk), 2), 0)
    goc.reload(); la('không sửa nguồn hóa đơn', goc.chi_tiet, du_nguon)


@ca('#259 MInvoice giá lẻ: 1000 x925.9259 ra đúng1000000 qua dựng/save/submit/GL/hủy')
def _11595():
    _luong(1000, 925.9259, 925926, 74074, doi_chung=True)


@ca('#259 MInvoice giá lẻ: tờ trả âm giữ giá dương và GL đảo đúng tiền nguồn')
def _tra_am():
    _luong(-1000, 925.9259, -925926, -74074)


@ca('#259 MInvoice giá lẻ: số lượng phân số không bị cắt trước nhân')
def _qty_le():
    _luong(0.125, 7407407.4072, 925926, 74074)


@ca('#259 MInvoice giá lẻ: nguồn có0.03đ giữ đủ, không ép tiền nguồn thành số nguyên')
def _tien_le():
    _luong(3, 333.343333333, 1000.03, 80)


@ca('#259 precision: PI thường/nguồn mất không bị đổi, cache chỉ ở object hiện hành')
def _pham_vi():
    mon = _mon()
    hd = _phieu([('Dòng thường259', 1, 925.9259)], mon=mon.name)
    cu = (hd.precision('rate', 'items'), hd.items[0].precision('rate'))
    cx.truoc_khi_tinh(hd)
    la('PI thường giữ precision', (hd.precision('rate', 'items'), hd.items[0].precision('rate')), cu)
    hd.custom_minvoice_id = 'KT-NGUON-KHONG-TON-TAI-259'
    cx.truoc_khi_tinh(hd)
    la('nguồn mất giữ precision', (hd.precision('rate', 'items'), hd.items[0].precision('rate')), cu)
    goc = _nguon([dict(ten='Thử259', thtien=926)], 0, 926)
    hd.custom_minvoice_id = goc.name
    cx.truoc_khi_tinh(hd)
    la('có nguồn thì cả hai cửa dùng9', (hd.precision('rate', 'items'), hd.items[0].precision('rate')), (9, 9))
    khac = _phieu([('PI khác259', 1, 925.9259)], mon=mon.name)
    la('không lan metadata sang PI khác', (khac.precision('rate', 'items'), khac.items[0].precision('rate')), cu)
    hd.custom_minvoice_id = None
    cx.truoc_khi_tinh(hd)
    la('bỏ nguồn trả cache về cũ', (hd.precision('rate', 'items'), hd.items[0].precision('rate')), cu)
