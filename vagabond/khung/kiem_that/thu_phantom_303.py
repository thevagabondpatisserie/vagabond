"""#303: phantom phải trừ NVL thật ở cả hai chế độ nổ BOM.

Fixture độc lập, tỷ lệ minh hoạ không phải công thức Gelatine của tiệm.
Không đổi cấu hình/dữ liệu cũ. Savepoint và chặn gửi ngoài do nen quản lý.
Core de591661 bom.py get_bom_items_as_dict đệ quy is_phantom_item ngay
cả khi use_multi_level_bom=0; chỉ is_stock_item=0 là chưa đủ.
"""
import uuid
import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _uom


def _bom(ma, cty, so, dong, phantom=0):
    b = frappe.get_doc({'doctype': 'BOM', 'item': ma, 'company': cty,
        'quantity': so, 'is_active': 1, 'is_default': 1,
        'is_phantom_bom': phantom, 'rm_cost_as_per': 'Valuation Rate', 'items': dong})
    if phantom: b.custom_chang = 'BTP thành phần'
    b.insert(); nen._DA_TAO.append(('BOM', b.name)); b.submit(); b.reload()
    return b


def _chay(nhieu_cap):
    cty = cong_ty()
    kho = frappe.get_all('Warehouse', filters={'company': cty, 'is_group': 0,
        'disabled': 0}, pluck='name', limit_page_length=2)
    dung('fixture có hai kho', len(kho) == 2)
    tag = uuid.uuid4().hex[:10]
    bot, nuoc, mass, tp = [_mon_thu('KT303-' + loai + tag) for loai in ['BOT','NUOC','MASS','TP']]
    m = frappe.get_doc('Item', mass); m.is_stock_item = 0; m.save()
    uom = _uom()
    con = _bom(mass, cty, 4, [{'item_code': bot, 'qty': 1, 'uom': uom, 'rate': 1000},
        {'item_code': nuoc, 'qty': 3, 'uom': uom, 'rate': 2000}], phantom=1)
    cha = _bom(tp, cty, 1, [{'item_code': mass, 'qty': 4, 'uom': uom,
        'bom_no': con.name, 'is_phantom_item': 1, 'do_not_explode': 0}])
    for ma, gia in [(bot,1000),(nuoc,2000)]:
        d = nhap(item_code=ma, qty=10, company=cty, to_warehouse=kho[0], rate=gia, do_not_save=True)
        d.insert(); nen._DA_TAO.append(('Stock Entry', d.name)); d.submit()
    wo = frappe.get_doc({'doctype': 'Work Order', 'company': cty, 'production_item': tp,
        'bom_no': cha.name, 'qty': 2, 'source_warehouse': kho[0], 'wip_warehouse': kho[0],
        'fg_warehouse': kho[1], 'skip_transfer': 1, 'use_multi_level_bom': nhieu_cap})
    wo.insert(); nen._DA_TAO.append(('Work Order', wo.name)); wo.submit(); wo.reload()
    can = {d.item_code: float(d.required_qty) for d in wo.required_items}
    la('WO chỉ đòi NVL thô', can, {bot: 2.0, nuoc: 6.0})
    phieu = []
    for lan in range(2):
        d = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))
        d.insert(); nen._DA_TAO.append(('Stock Entry', d.name)); d.submit(); d.reload(); phieu.append(d)
        sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type':'Stock Entry',
            'voucher_no':d.name, 'is_cancelled':0}, fields=['item_code','warehouse','actual_qty','stock_value_difference'])
        dung('SLE không rỗng', bool(sle))
        for ma, so in [(bot,-1),(nuoc,-3)]:
            dong = [x for x in sle if x.item_code == ma]
            la('NVL chỉ xuất đúng kho', {x.warehouse for x in dong}, {kho[0]})
            la('số NVL mỗi lượt', sum(float(x.actual_qty) for x in dong), so)
        la('giá trị NVL mỗi lượt', sum(float(x.stock_value_difference) for x in sle if x.item_code in [bot,nuoc]), -7000)
        la('giá trị TP nhận', sum(float(x.stock_value_difference) for x in sle if x.item_code == tp), 7000)
        gl = so_cai_cua(d)
        la('GL cân', sum(float(x.debit) for x in gl), sum(float(x.credit) for x in gl))
        if not gl: la('không GL thì SLE ròng0', sum(float(x.stock_value_difference) for x in sle), 0)
    la('Mass không phát sinh SLE', frappe.db.count('Stock Ledger Entry', {'item_code': mass}), 0)
    la('Mass không phát sinh Bin', frappe.db.count('Bin', {'item_code': mass}), 0)
    for d in reversed(phieu): d.cancel()
    for ma in [bot, nuoc]:
        la('huỷ trả đủ NVL', float(frappe.db.get_value('Bin', {'item_code':ma,'warehouse':kho[0]}, 'actual_qty')), 10)
    wo.reload(); la('huỷ trả sản lượng', float(wo.produced_qty), 0)


@ca('#303 thật: phantom một cấp trừ NVL, không tồn Mass, huỷ trả đủ')
def _mot_cap():
    _chay(0)


@ca('#303 thật: phantom nhiều cấp trừ NVL, không tồn Mass, huỷ trả đủ')
def _nhieu_cap():
    _chay(1)
