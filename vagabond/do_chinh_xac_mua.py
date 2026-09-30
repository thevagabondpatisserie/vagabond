"""HĐ11595: 1000 x925.9259 bị cắt giá thành925.93 rồi lệch4đ.

Chỉ giữ độ chính xác trong object PI có nguồn MInvoice bằng VND. Không
sửa metadata dùng chung, nguồn, số lượng, đơn giá hoặc ngưỡng đối chiếu.
ERPNext v16.28.0 taxes_and_totals.calculate_item_values gọi round_floats_in
trước phép nhân; Frappe f33ac3f document.round_floats_in đọc precision của
PARENT/items, các phép tính sau đọc precision ROW/main. Phải đặt cả hai.
"""
import json
from decimal import Decimal, InvalidOperation

GIA = ('rate', 'price_list_rate', 'net_rate', 'base_rate', 'base_price_list_rate',
       'base_net_rate', 'rate_with_margin', 'base_rate_with_margin')
TIEN = ('amount', 'base_amount', 'net_amount', 'base_net_amount')


def so_le_tien(goc):
    """Dùng độ lẻ tiền nguồn; nguồn có0.03đ không bị ép thành đồng nguyên."""
    dong = goc.get('chi_tiet') or []
    if isinstance(dong, str):
        dong = json.loads(dong)
    gia_tri = [goc.get(k) for k in ('tien_truoc_thue', 'tien_thue', 'tong_tien', 'chiet_khau')]
    for d in dong:
        gia_tri.extend(d.get(k) for k in ('thtien', 'stckhau', 'tthue'))
    so = 0
    for v in gia_tri:
        if v in (None, ''):
            continue
        try:
            n = Decimal(str(v))
            if not n.is_finite():
                raise ValueError('Tiền nguồn MInvoice không hữu hạn')
            so = max(so, -n.normalize().as_tuple().exponent)
        except (InvalidOperation, TypeError):
            raise ValueError('Tiền nguồn MInvoice không hợp lệ') from None
    if so > 9:
        raise ValueError('Tiền nguồn MInvoice vượt9 số lẻ mà trường tiền ERPNext lưu được')
    return so


def quy_uoc(doc, goc):
    if doc.get('doctype') != 'Purchase Invoice' or doc.get('currency') != 'VND' or not goc:
        return None
    return {'gia': 9, 'tien': so_le_tien(goc), 'sl': 9}


TIEN_DONG = ('amount', 'base_amount')
TIEN_RONG = ('net_amount', 'base_net_amount')


def bang_do_chinh_xac(qc, so_le_tong):
    """Độ lẻ gán cho từng dòng. THUẦN.

    Tiền DÒNG (amount) theo độ lẻ nguồn, để thành tiền ra đúng số nguyên như
    hoá đơn. Tiền SAU GIẢM (net_amount) thì KHÔNG được ít lẻ hơn tổng của cả
    tờ (`so_le_tong`, độ lẻ của net_total).

    Vì sao - ca thật GSM C26TBB/77683 ngày 30/09/2026: 889 dòng cước, chiết
    khấu 1.489.862 chia đều vào từng dòng. ERPNext (taxes_and_totals
    .apply_discount_amount) làm tròn net_amount từng dòng theo độ lẻ DÒNG,
    rồi bù phần chênh theo độ lẻ TỔNG. Dòng 0 lẻ mà tổng 2 lẻ thì phần bù
    0,3 đồng bị làm tròn mất ở dòng nhưng vẫn được cộng vào tổng, dồn qua
    889 dòng thành tờ thiếu 21 đồng, và hàng rào cuối "Không nhận".
    """
    tien = qc['tien']
    bang = {k: qc['gia'] for k in GIA}
    bang.update({k: tien for k in TIEN_DONG})
    bang.update({k: max(tien, so_le_tong or 0) for k in TIEN_RONG})
    bang['qty'] = qc['sl']
    return bang


def _gan(doc, khoa, bang):
    # Chỉ cache riêng object, không gán df.precision vào metadata/cache chung.
    import frappe
    if not hasattr(doc, '_precision'):
        doc._precision = frappe._dict()
    if khoa not in doc._precision:
        doc._precision[khoa] = frappe._dict()
    doc._precision[khoa].update(bang)


def truoc_khi_tinh(doc, method=None):
    from copy import deepcopy
    # Object có thể được dùng lại rồi bỏ nguồn/đổi tiền tệ trước lần save sau.
    for d, co, cu in getattr(doc, '_vgb_precision_mua_cu', []):
        if co:
            d._precision = cu
        elif hasattr(d, '_precision'):
            del d._precision
    doc._vgb_precision_mua_cu = []
    if doc.get('docstatus') == 2 or getattr(doc, '_action', None) == 'update_after_submit':
        return
    from vagabond.dung_lai_hddt import _goc
    goc = _goc(doc.get('custom_minvoice_id'))
    qc = quy_uoc(doc, goc)
    if not qc:
        return
    doc._vgb_precision_mua_cu = [(d, hasattr(d, '_precision'), deepcopy(getattr(d, '_precision', None)))
        for d in [doc] + list(doc.get('items') or []) + list(doc.get('taxes') or [])]
    # Đọc độ lẻ net_total TRƯỚC khi gán cho tờ; cùng công thức gán ở dưới.
    bang = bang_do_chinh_xac(qc, max(doc.precision('net_total') or 0, qc['tien']))
    _gan(doc, 'items', bang)
    for d in doc.get('items') or []:
        _gan(d, 'main', bang)
    # Nguồn có lẻ hơn cài đặt hiện hành vẫn phải được cộng đủ ở đầu phiếu.
    # Không hạ precision các trường đầu phiếu/thuế, giữ cách phân bổ thuế core.
    for d, khoa in [(doc, 'main')] + [(t, 'main') for t in doc.get('taxes') or []]:
        tien = {f.fieldname: max(d.precision(f.fieldname) or 0, qc['tien'])
                for f in d.meta.fields if f.fieldtype == 'Currency'}
        _gan(d, khoa, tien)
