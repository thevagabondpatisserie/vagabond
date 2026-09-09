"""BOM/Item thật: đổi nhãn Gram không đổi lượng kho hay tiền công thức."""
import frappe
from vagabond import gram_bom_252 as gram
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.he_so_252 import _luu, _bi_chan
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _lenh_thu


def _mon():
    for uom in ('ML', 'Gram'):
        if not frappe.db.exists('UOM', uom):
            _luu(frappe.get_doc(dict(doctype='UOM', uom_name=uom, must_be_whole_number=0)))
    ma = _mon_thu('KT-GRAM252-' + frappe.generate_hash(length=8))
    mon = frappe.get_doc('Item', ma)
    mon.stock_uom = 'ML'
    mon.set('uoms', [dict(uom='ML', conversion_factor=1)])
    mon.save(ignore_permissions=True)
    return mon


def _bom(mon, uom='ML', nhieu=False):
    tp = _mon_thu('KT-GRAMTP252-' + frappe.generate_hash(length=8))
    ds = [dict(item_code=mon.name, qty=330, uom=uom, conversion_factor=1, rate=2)]
    if nhieu:
        # Hai dòng cùng mã nhưng số riêng, đúng hình dạng Lescure.
        ds.append(dict(item_code=mon.name, qty=266, uom=uom, conversion_factor=1, rate=2))
    bom = _luu(frappe.get_doc(dict(doctype='BOM', item=tp, company=nen.cong_ty(),
        quantity=1, is_active=1, is_default=1,
        rm_cost_as_per='Valuation Rate', items=ds)))
    bom.submit(); bom.reload()
    return bom


def _so_bom(bom):
    bom.reload()
    return dict(items=[{k: d.get(k) for k in ('name', 'qty', 'conversion_factor', 'stock_qty',
        'stock_uom', 'rate', 'base_rate', 'amount', 'base_amount')} for d in bom.items],
        explosion=[d.as_dict() for d in bom.exploded_items], total_cost=bom.total_cost,
        raw_material_cost=bom.raw_material_cost)


@ca('#252 Gram thật: patch đổi BOM đã ghi sổ, bảo toàn số và chạy hai lần không thêm vết')
def _patch():
    mon = _mon(); bom = _bom(mon)
    truoc = _so_bom(bom)
    ma_cu = gram.MA_NGUYEN_LIEU
    try:
        gram.MA_NGUYEN_LIEU = (mon.name,)
        la('đổi đúng một dòng', gram.ap_dung(), {'mon_bo_sung': 1, 'dong_bom': 1, 'bom': 1})
        la('mọi số và explosion giữ nguyên', _so_bom(bom), truoc)
        la('nhãn Gram', bom.items[0].uom, 'Gram')
        mon.reload()
        la('kho vẫn ML', mon.stock_uom, 'ML')
        la('Gram1 đã lưu', [d.conversion_factor for d in mon.uoms if d.uom == 'Gram'], [1])
        so_vet = frappe.db.count('Comment', {'reference_doctype': 'BOM', 'reference_name': bom.name})
        la('chạy lần hai không đổi', gram.ap_dung(), {'mon_bo_sung': 0, 'dong_bom': 0, 'bom': 0})
        la('không comment trùng', frappe.db.count('Comment', {'reference_doctype': 'BOM', 'reference_name': bom.name}), so_vet)
    finally:
        gram.MA_NGUYEN_LIEU = ma_cu


@ca('#252 Gram thật: BOM mới qua hook và hai dòng330/266 cho lệnh đúng596ML')
def _bom_moi():
    mon = _mon()
    ma_cu = gram.MA_NGUYEN_LIEU
    try:
        gram.MA_NGUYEN_LIEU = (mon.name,)
        gram.ap_dung()
        bom = _bom(mon, nhieu=True)
        la('hai dòng được đổi sang Gram', [d.uom for d in bom.items], ['Gram', 'Gram'])
        la('giữ lượng từng dòng', [d.stock_qty for d in bom.items], [330, 266])
        wo = _lenh_thu(bom.item, bom, nen.mot_kho(nen.cong_ty()), nen.cong_ty())
        la('lệnh dùng596ML', sum(d.required_qty for d in wo.required_items if d.item_code == mon.name), 596)
        la('lưu BOM đã Gram không nhân lại', [d.stock_qty for d in bom.items], [330, 266])
        mon.reload()
        next(d for d in mon.uoms if d.uom == 'Gram').conversion_factor = 2
        _bi_chan(lambda: mon.save(ignore_permissions=True), 'không tự đổi quy ướcGram1')
    finally:
        gram.MA_NGUYEN_LIEU = ma_cu


@ca('#252 Gram thật: kiểm hết kế hoạch trước khi ghi, dòng kho lệch không được đổi nhãn')
def _chan_patch():
    mon = _mon(); bom = _bom(mon)
    frappe.db.set_value('BOM Item', bom.items[0].name, 'stock_qty', 330000)
    ma_cu = gram.MA_NGUYEN_LIEU
    try:
        gram.MA_NGUYEN_LIEU = (mon.name,)
        _bi_chan(gram.ap_dung, 'patch không che lượng sai')
        mon.reload(); bom.reload()
        la('chưa thêm Gram khi kế hoạch sai', [d.uom for d in mon.uoms], ['ML'])
        la('chưa đổi dòng BOM', bom.items[0].uom, 'ML')
    finally:
        gram.MA_NGUYEN_LIEU = ma_cu


def _kho_rieng(ct, nhan):
    """Hai tài khoản kho riêng để GL phải thể hiện chuyển giá vốn thực."""
    cha = frappe.db.get_value('Account',
        {'company': ct, 'root_type': 'Asset', 'is_group': 1}, 'name')
    dung('có tài khoản nhóm tài sản', bool(cha))
    tk = _luu(frappe.get_doc(dict(doctype='Account',
        account_name='KT-GRAM252-' + nhan + '-' + frappe.generate_hash(length=9),
        company=ct, parent_account=cha, account_type='Stock',
        account_currency='VND', is_group=0)))
    kho = _luu(frappe.get_doc(dict(doctype='Warehouse',
        warehouse_name='KT-GRAM252-' + nhan + '-' + frappe.generate_hash(length=9),
        company=ct, account=tk.name)))
    return kho.name, tk.name


def _so_kho(ma, kho):
    return frappe.utils.flt(frappe.db.get_value('Bin',
        {'item_code': ma, 'warehouse': kho}, 'actual_qty'))


def _gl_phieu(phieu):
    return frappe.get_all('GL Entry',
        filters={'voucher_type': phieu.doctype, 'voucher_no': phieu.name},
        fields=['account', 'debit', 'credit'])


def _san_xuat_thuc(nhieu_cap=False):
    """Core v16.28.0 work_order.make_stock_entry lấy kho từ WO và gọi
    StockEntry.get_items: ca này dùng cửa đó, không tự dựng dòng tiêu hao.
    Hai cấp dùng BOM con như bán thành phẩm để chốt explosion vẫn là ML.
    """
    from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
    from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry as lam_sx
    from erpnext import is_perpetual_inventory_enabled

    ct = nen.cong_ty()
    dung('bench phải bật hạch toán kho', bool(is_perpetual_inventory_enabled(ct)))
    kho_nvl, tk_nvl = _kho_rieng(ct, 'NVL')
    kho_tp, tk_tp = _kho_rieng(ct, 'TP')
    mon = _mon()
    cu = gram.MA_NGUYEN_LIEU
    try:
        gram.MA_NGUYEN_LIEU = (mon.name,)
        gram.ap_dung()
        ph = make_stock_entry(item_code=mon.name, qty=1000, company=ct,
            to_warehouse=kho_nvl, rate=2, do_not_save=True)
        _luu(ph); ph.submit()
        bom = _bom(mon, nhieu=True)
        if nhieu_cap:
            tp = _mon_thu('KT-GRAMTP-CAP2-' + frappe.generate_hash(length=8))
            bom = _luu(frappe.get_doc(dict(doctype='BOM', item=tp, company=ct,
                quantity=1, is_active=1, is_default=1, rm_cost_as_per='Valuation Rate',
                items=[dict(item_code=bom.item, bom_no=bom.name, qty=1,
                    uom=frappe.db.get_value('Item', bom.item, 'stock_uom'),
                    conversion_factor=1)])))
            bom.submit(); bom.reload()
        dong_no = [d for d in bom.exploded_items if d.item_code == mon.name]
        la('khai triển đúng596ML', sum(d.stock_qty for d in dong_no), 596)
        dung('đơn vị khai triển vẫn ML', bool(dong_no) and all(d.stock_uom == 'ML' for d in dong_no))
        wo = _luu(frappe.get_doc(dict(doctype='Work Order', company=ct,
            production_item=bom.item, bom_no=bom.name, qty=1,
            skip_transfer=1, source_warehouse=kho_nvl, wip_warehouse=kho_nvl,
            fg_warehouse=kho_tp, use_multi_level_bom=1)))
        wo.submit(); wo.reload()
        la('WO cần đúng596ML', sum(d.required_qty for d in wo.required_items
            if d.item_code == mon.name), 596)
        sx = frappe.get_doc(lam_sx(wo.name, 'Manufacture', qty=1))
        _luu(sx); sx.submit(); sx.reload()
        sle = frappe.get_all('Stock Ledger Entry',
            filters={'voucher_type': sx.doctype, 'voucher_no': sx.name, 'is_cancelled': 0},
            fields=['item_code', 'warehouse', 'actual_qty', 'stock_value_difference'])
        nvl = [d for d in sle if d.item_code == mon.name]
        tp = [d for d in sle if d.item_code == bom.item]
        la('SLE trừ đúng596ML', sum(d.actual_qty for d in nvl), -596)
        dung('trừ đúng kho NVL', bool(nvl) and all(d.warehouse == kho_nvl for d in nvl))
        la('SLE nhập một thành phẩm', sum(d.actual_qty for d in tp), 1)
        dung('nhập đúng kho TP', bool(tp) and all(d.warehouse == kho_tp for d in tp))
        la('giá vốn lấy đủ596 x2', sum(d.stock_value_difference for d in nvl), -1192)
        la('thành phẩm nhận cùng giá vốn', sum(d.stock_value_difference for d in tp), 1192)
        gl = _gl_phieu(sx)
        dung('sản xuất thực sự có GL', bool(gl))
        la('Có tài khoản NVL', sum(d.credit-d.debit for d in gl if d.account == tk_nvl), 1192)
        la('Nợ tài khoản TP', sum(d.debit-d.credit for d in gl if d.account == tk_tp), 1192)
        la('GL cân', sum(d.debit-d.credit for d in gl), 0)
        la('tồn NVL còn404ML', _so_kho(mon.name, kho_nvl), 404)
        la('tồn TP bằng1', _so_kho(bom.item, kho_tp), 1)
        wo.reload(); la('WO hoàn tất1', wo.produced_qty, 1)
        sx.cancel(); sx.reload()
        la('SE đã hủy', sx.docstatus, 2)
        la('hủy trả1000ML', _so_kho(mon.name, kho_nvl), 1000)
        la('hủy thu hồi TP', _so_kho(bom.item, kho_tp), 0)
        gl = _gl_phieu(sx)
        for tk in (tk_nvl, tk_tp):
            la('hủy đảo đủ tài khoản ' + tk, sum(d.debit-d.credit for d in gl if d.account == tk), 0)
        wo.reload(); la('hủy trả sản lượng WO về0', wo.produced_qty, 0)
    finally:
        gram.MA_NGUYEN_LIEU = cu


@ca('#252 Gram thật: WO và sản xuất596Gram trừ596ML, SLE/GL đúng và hủy đảo đủ')
def _sle_gl():
    _san_xuat_thuc()


@ca('#252 Gram thật: BOM hai cấp khai triển596ML và sản xuất không nhân hệ số lần nữa')
def _nhieu_cap():
    _san_xuat_thuc(nhieu_cap=True)
