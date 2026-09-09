"""Định mức và yêu cầu mua cũng không được lưu quy đổi sai rồi truyền tiếp."""
import frappe
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.he_so_252 import _nen, _luu, _bi_chan
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu


@ca('#252 BOM thật: chặn hệ số1, lưu550 và định mức kho đúng550')
def _bom():
    mon, lon = _nen()
    tp = _mon_thu('KT-TP252-' + frappe.generate_hash(length=9))
    bom = frappe.get_doc(dict(doctype='BOM', item=tp, company=nen.cong_ty(),
        quantity=1, is_active=1, is_default=1, rm_cost_as_per='Valuation Rate',
        items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=1, rate=550)]))
    _bi_chan(lambda: _luu(bom), 'BOM sai hệ số không được lưu')
    bom.items[0].conversion_factor = 550
    _luu(bom); bom.submit(); bom.reload()
    la('BOM đúng đã submit', bom.docstatus, 1)
    la('BOM giữ hệ số550', bom.items[0].conversion_factor, 550)
    la('định mức nguyên liệu550 đơn vị kho', bom.items[0].stock_qty, 550)
    # Tái hiện BOM cũ đã lọt: giữ bản sai trong DB chỉ ở nền thử, rồi
    # gọi đường tạo lệnh thật. Không cho SE stock-UOM1 che sai định mức.
    frappe.db.set_value('BOM Item', bom.items[0].name, 'conversion_factor', 1)
    from vagabond.khung.kiem_that.thu_ma_cap_so import _lenh_thu
    _bi_chan(lambda: _lenh_thu(tp, bom, nen.mot_kho(nen.cong_ty()), nen.cong_ty()),
             'BOM lịch sử sai không được dùng tạo lệnh')
    from vagabond.he_so_chung_tu import kiem_bom_lenh
    se = frappe.get_doc(dict(doctype='Stock Entry', bom_no=bom.name))
    _bi_chan(lambda: kiem_bom_lenh(se), 'phiếu kho trực tiếp cũng kiểm BOM cũ')


@ca('#252 yêu cầu mua thật: chặn hệ số1, lưu550 và stock_qty đúng')
def _yeu_cau():
    mon, lon = _nen()
    mr = frappe.get_doc(dict(doctype='Material Request', company=nen.cong_ty(),
        material_request_type='Purchase', transaction_date=frappe.utils.today(),
        schedule_date=frappe.utils.today(), items=[dict(item_code=mon.name,
        qty=1, uom=lon, conversion_factor=1, warehouse=nen.mot_kho(nen.cong_ty()),
        schedule_date=frappe.utils.today())]))
    _bi_chan(lambda: _luu(mr), 'yêu cầu mua sai hệ số không được lưu')
    mr.items[0].conversion_factor = 550
    _luu(mr); mr.reload()
    la('yêu cầu mua giữ550', mr.items[0].conversion_factor, 550)
    la('yêu cầu mua lượng kho550', mr.items[0].stock_qty, 550)


@ca('#252 gia công dùng đơn vị kho: hệ sốẩn khác1 bị chặn tại hook chung')
def _gia_cong():
    from vagabond.he_so_chung_tu import kiem
    from vagabond import hooks
    mon, lon = _nen()
    for loai in ('Subcontracting Order', 'Subcontracting Receipt', 'Subcontracting Inward Order'):
        doc = frappe.get_doc(dict(doctype=loai, company=nen.cong_ty(),
            items=[dict(item_code=mon.name, stock_uom=mon.stock_uom, conversion_factor=550)]))
        _bi_chan(lambda: kiem(doc), loai+' không nhân thêm đơn vị kho')
        doc.items[0].conversion_factor = 1
        kiem(doc)
        for event in ('validate', 'before_submit'):
            handlers = hooks.doc_events[loai][event]
            if isinstance(handlers, str):
                handlers = [handlers]
            dung(loai+' '+event+' có hook', 'vagabond.he_so_chung_tu.kiem' in handlers)
