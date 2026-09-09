"""#252: PR sai hệ số đã kiểm kê, PI đúng quy cách, không sửa tồn lần hai.

Chỉ tạo chứng từ thử trong savepoint. Hàng rào quy cách cũ chỉ được bỏ
qua lúc dựng PR lịch sử; không mock phép đối chiếu, submit hay sổ kho.
"""
import frappe
from unittest.mock import patch
from frappe.utils import add_days, today
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _lo_thu


def _luu(doc):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    nen._DA_TAO.append((doc.doctype, doc.name))
    return doc


def _nen():
    ct = nen.cong_ty()
    kho = nen.mot_kho(ct)
    for field, val in [('enable_serial_and_batch_no_for_item', 1), ('use_serial_batch_fields', 1)]:
        frappe.db.set_single_value('Stock Settings', field, val)
    ma = _mon_thu('KT252-' + frappe.generate_hash(length=10), theo_lo=1)
    mon = frappe.get_doc('Item', ma)
    hop = 'KT252-Hop-' + frappe.generate_hash(length=8)
    _luu(frappe.get_doc(dict(doctype='UOM', uom_name=hop, must_be_whole_number=1)))
    mon.append('uoms', dict(uom=hop, conversion_factor=1000))
    mon.save(ignore_permissions=True)
    lo = _lo_thu(ma).name
    pr = frappe.get_doc(dict(doctype='Purchase Receipt', company=ct,
        supplier=nen.mot_nha_cung_cap(), currency='VND', conversion_rate=1,
        posting_date=add_days(today(), -3), posting_time='10:00:00', set_posting_time=1,
        items=[dict(item_code=ma, qty=18, uom=hop, conversion_factor=500,
            rate=300000, warehouse=kho, batch_no=lo, use_serial_batch_fields=1)]))
    # Tái hiện đúng lỗi trước khi hàng rào ngày 27/08 được triển khai.
    with patch('vagabond.gac_don_vi.chan_don_vi_la', lambda *a, **kw: None):
        _luu(pr); pr.submit()
    pr.reload()
    la('PR gốc giữ 500', pr.items[0].conversion_factor, 500)
    la('PR đã nhập 9000', pr.items[0].stock_qty, 9000)
    sr = frappe.get_doc(dict(doctype='Stock Reconciliation', company=ct,
        purpose='Stock Reconciliation', set_posting_time=1,
        posting_date=add_days(today(), -2), posting_time='10:00:00',
        expense_account=frappe.get_cached_value('Company', ct, 'stock_adjustment_account'),
        cost_center=frappe.get_cached_value('Company', ct, 'cost_center'),
        items=[dict(item_code=ma, warehouse=kho, qty=18000, valuation_rate=300,
            batch_no=lo, use_serial_batch_fields=1, reconcile_all_serial_batch=0)]))
    _luu(sr); sr.submit(); sr.reload()
    la('kiểm kê tăng đúng lượng', sum(d.actual_qty for d in _sle(ma) if d.voucher_no == sr.name), 9000)
    la('kiểm kê không đổi tiền', sum(d.stock_value_difference for d in _sle(ma) if d.voucher_no == sr.name), 0)
    la('không GL kiểm kê', len(_gl(sr)), 0)
    return pr, sr


def _xac_nhan(pr, sr, ghi_so=True, **doi):
    vals = dict(doctype='Vagabond Quy Cach Doi Chieu', phieu_nhap=pr.name,
        dong_nhap=pr.items[0].name, phieu_kiem_ke=sr.name, dong_kiem_ke=sr.items[0].name,
        he_so_cu=500, he_so_moi=1000, ly_do='Ca kiểm 252: kiểm kê đã sửa 9000 thành 18000, không đổi giá trị')
    vals.update(doi)
    doc = _luu(frappe.get_doc(vals))
    if ghi_so:
        doc.submit()
    return doc


def _pi(pr, hs=1000, qty=18):
    row = pr.items[0]
    return _luu(frappe.get_doc(dict(doctype='Purchase Invoice', company=pr.company,
        supplier=pr.supplier, currency='VND', conversion_rate=1, update_stock=0,
        bill_no='KT252-' + frappe.generate_hash(length=10), bill_date=add_days(today(), -1),
        posting_date=add_days(today(), -1), posting_time='10:00:00', set_posting_time=1,
        items=[dict(item_code=row.item_code, uom=row.uom, qty=qty, conversion_factor=hs,
            rate=300000, warehouse=row.warehouse, purchase_receipt=pr.name, pr_detail=row.name)])))


def _sle(ma):
    return frappe.get_all('Stock Ledger Entry', filters={'item_code': ma},
        fields=['name', 'voucher_type', 'voucher_no', 'actual_qty', 'qty_after_transaction',
                'stock_value_difference', 'stock_value', 'valuation_rate', 'is_cancelled'], order_by='name')


def _gl(doc):
    return frappe.get_all('GL Entry', filters={'voucher_type': doc.doctype, 'voucher_no': doc.name},
        fields=['account', 'debit', 'credit', 'is_cancelled'], order_by='name')


def _chay_repost(pr):
    """Chạy công việc core thật, không coi job vừa xếp hàng là đã kiểm xong."""
    from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost
    gioi_han = frappe.db.MAX_WRITES_PER_TRANSACTION
    co = frappe.flags.get('through_repost_item_valuation')
    try:
        for name in frappe.get_all('Repost Item Valuation', filters={
                'voucher_type': 'Purchase Receipt', 'voucher_no': pr.name,
                'docstatus': 1, 'status': ['!=', 'Completed']}, pluck='name'):
            doc = frappe.get_doc('Repost Item Valuation', name)
            repost(doc)
            la('repost core hoàn tất', frappe.db.get_value(doc.doctype, name, 'status'), 'Completed')
    finally:
        frappe.db.MAX_WRITES_PER_TRANSACTION = gioi_han
        frappe.flags.through_repost_item_valuation = co


def _ghi_va_huy(chinh_gia):
    frappe.db.set_single_value('Buying Settings', 'set_landed_cost_based_on_purchase_invoice_rate', chinh_gia)
    pr, sr = _nen()
    xac_nhan = _xac_nhan(pr, sr)
    ma = pr.items[0].item_code
    truoc = _sle(ma)
    gl_pr, gl_sr = _gl(pr), _gl(sr)
    hd = _pi(pr)
    trung = _pi(pr, qty=1)
    hd.submit(); hd.reload()
    _chay_repost(pr)
    la('PI đúng hệ số', hd.items[0].conversion_factor, 1000)
    la('PI đủ 18 hộp', hd.items[0].stock_qty, 18000)
    la('PI đúng tiền', hd.grand_total, 5400000)
    la('PI không nhập thêm kho', hd.update_stock, 0)
    la('SLE giữ nguyên cả tên và giá trị', _sle(ma), truoc)
    la('GL PR không đổi', _gl(pr), gl_pr)
    la('GL kiểm kê không đổi', _gl(sr), gl_sr)
    la('GL PI cân', sum(d.debit-d.credit for d in _gl(hd)), 0)
    dung('PI thực sự ghi GL', bool(_gl(hd)))
    pr.reload(); la('không sửa hệ số PR gốc', pr.items[0].conversion_factor, 500)
    # Gọi chính hàng rào dưới Document, không để overbilling bằng tiền
    # của ERPNext che một lỗi hạn mức lượng ở phần mở rộng.
    from vagabond.doi_chieu_mua import chan_vuot_luong_da_nhan
    try: chan_vuot_luong_da_nhan(trung)
    except frappe.ValidationError: pass
    else: dung('không còn lượng cho PI thứ hai', False)
    hd.cancel(); _chay_repost(pr)
    la('huỷ PI không đổi tồn đã kiểm kê', _sle(ma), truoc)
    la('huỷ đảo GL PI', sum(d.debit-d.credit for d in _gl(hd)), 0)
    # Hạn mức được trả lại khi PI đã huỷ.
    chan_vuot_luong_da_nhan(trung)
    xac_nhan.reload()
    xac_nhan.he_so_moi = 2000
    try: xac_nhan.save(ignore_permissions=True)
    except frappe.ValidationError: pass
    else: dung('xác nhận đã ghi sổ không được đổi', False)


@ca('#252 thật: PR500 đã kiểm kê, PI1000, không chỉnh giá nhập, ghi và huỷ không đổi SLE')
def _khong_chinh_gia():
    _ghi_va_huy(0)


@ca('#252 thật: bật chỉnh giá nhập, chạy repost thật, PI1000 không đổi PR/kiểm kê/SLE')
def _co_chinh_gia():
    _ghi_va_huy(1)


@ca('#252 thật: đã có PI500 thì không được xác nhận quy cách, không mở thêm hạn mức')
def _hoa_don_cu():
    frappe.db.set_single_value('Buying Settings', 'set_landed_cost_based_on_purchase_invoice_rate', 0)
    pr, sr = _nen()
    cu = _pi(pr, hs=500)
    moi = _pi(pr, hs=500, qty=1)
    cu.submit()
    truoc = _sle(pr.items[0].item_code)
    gl_cu = _gl(cu)
    try: _xac_nhan(pr, sr)
    except frappe.ValidationError as e:
        dung('nêu đúng hoá đơn đã ghi sổ', 'hoá đơn' in str(e) and 'ghi sổ' in str(e))
    else: dung('không xác nhận khi đã có PI lịch sử', False)
    la('tồn không đổi khi từ chối', _sle(pr.items[0].item_code), truoc)
    la('GL cũ không đổi', _gl(cu), gl_cu)
    from vagabond.doi_chieu_mua import chan_vuot_luong_da_nhan
    try: chan_vuot_luong_da_nhan(moi)
    except frappe.ValidationError: pass
    else: dung('PI cũ đã dùng hết 18 hộp, không cấp thêm', False)
    from vagabond.quy_cach_doi_chieu import luong_da_ghi
    # Phép chuẩn hoá phải an toàn với nháp cũ dù không cho xác nhận mới
    # trên dòng đã có PI ghi sổ. Gọi helper thật, không thay quy tắc.
    effective = frappe._dict(uom=pr.items[0].uom, conversion_factor=1000, can_cu_quy_cach='thu')
    la('cùng 18 hộp cũ chiếm đủ 18000', luong_da_ghi(cu.items[0], effective), 18000)


@ca('#252 thật: xác nhận sai dòng kiểm kê hoặc sai hệ số bị chặn')
def _sai_tham_chieu():
    pr, sr = _nen()
    for doi in ({'dong_kiem_ke': 'dong-khong-ton-tai'}, {'he_so_cu': 250}, {'he_so_moi': 2000}):
        try: _xac_nhan(pr, sr, **doi)
        except (frappe.ValidationError, frappe.DoesNotExistError): pass
        else: dung('không chấp nhận chứng cứ sai '+str(doi), False)
    _xac_nhan(pr, sr)
    try: _xac_nhan(pr, sr)
    except frappe.ValidationError: pass
    else: dung('một dòng nhập không được có hai căn cứ ghi sổ', False)


@ca('#252 thật: PI ghi sổ sau lúc lưu nháp căn cứ vẫn chặn lúc xác nhận')
def _pi_chen_giua():
    frappe.db.set_single_value('Buying Settings', 'set_landed_cost_based_on_purchase_invoice_rate', 0)
    pr, sr = _nen()
    xac_nhan = _xac_nhan(pr, sr, ghi_so=False)
    cu = _pi(pr, hs=500); cu.submit()
    try: xac_nhan.submit()
    except frappe.ValidationError as e:
        dung('chặn đúng PI chen giữa', 'hoá đơn' in str(e) and 'ghi sổ' in str(e))
    else: dung('submit căn cứ phải kiểm lại PI đã ghi', False)
    la('căn cứ vẫn nháp', frappe.db.get_value(xac_nhan.doctype, xac_nhan.name, 'docstatus'), 0)
