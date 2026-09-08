"""#225: chốt số nguyên từng dòng trước khi lõi cộng thuế và dựng sổ cái.

ERPNext de59166 controllers/taxes_and_totals.py _calculate gọi lần lượt
update_item_tax_map, determine_exclusive_rate, calculate_taxes, calculate_totals.
Can thiệp tại dòng hàng, giữ validation và ghi sổ chuẩn của Sales Invoice.
"""
from copy import deepcopy
import frappe
from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from vagabond.thue_vnd import tinh_dong, doc_dong


def ap_dung(doc):
    if not doc.meta.has_field('vgb_thue_vnd') or not doc.get('items'):
        return False
    if doc.get('docstatus') != 0 and getattr(doc, '_action', None) != 'submit':
        return False
    if not doc.is_new() and frappe.db.get_value('Sales Invoice', doc.name, 'docstatus') != 0:
        return False
    if doc.currency != 'VND' or flt(doc.conversion_rate) != 1:
        return False
    if frappe.get_cached_value('Company', doc.company, 'default_currency') != 'VND':
        return False
    if any(doc.get(k) for k in ('is_return', 'is_debit_note', 'is_cash_or_non_trade_discount',
                                'shipping_rule', 'is_internal_customer')):
        return False
    thue = doc.get('taxes') or []
    return (len(thue) == 1 and thue[0].charge_type == 'On Net Total'
            and thue[0].get('add_deduct_tax') != 'Deduct'
            and thue[0].get('category') != 'Valuation'
            and not thue[0].get('dont_recompute_tax'))


def do_chinh_xac(doc):
    # BaseDocument.precision (Frappe f33ac3f) lưu cache theo parentfield.
    # Chỉ số tiền tính ra của đúng Document này; giá và số lượng giữ số lẻ.
    truong = {
        'Sales Invoice': ('total', 'base_total', 'net_total', 'base_net_total',
            'grand_total', 'base_grand_total', 'rounded_total', 'base_rounded_total',
            'rounding_adjustment', 'base_rounding_adjustment',
            'total_taxes_and_charges', 'base_total_taxes_and_charges',
            'discount_amount', 'base_discount_amount'),
        'Sales Invoice Item': ('amount', 'base_amount', 'net_amount', 'base_net_amount',
            'distributed_discount_amount'),
        'Sales Taxes and Charges': ('tax_amount', 'base_tax_amount', 'net_amount',
            'base_net_amount', 'tax_amount_after_discount_amount',
            'base_tax_amount_after_discount_amount', 'total', 'base_total'),
    }
    for d in [doc] + list(doc.items) + list(doc.taxes):
        for ten in truong.get(d.doctype, ()):
            if d.meta.has_field(ten):
                d.precision(ten)
                d._precision['main'][ten] = 0


class ThueVnd(calculate_taxes_and_totals):
    def determine_exclusive_rate(self):
        thue = self.doc.taxes[0]
        ts = [self._load_item_tax_rate(d.item_tax_rate).get(thue.account_head, thue.rate)
              for d in self._items]
        truoc = tinh_dong([d.amount for d in self._items], ts, thue.included_in_print_rate)
        self.chia = tinh_dong([d.amount for d in self._items], ts, thue.included_in_print_rate,
            self.doc.discount_amount if self.discount_amount_applied else 0, self.doc.apply_discount_on)
        for d, x, cu in zip(self._items, self.chia, truoc):
            d.net_amount = d.base_net_amount = x['net']
            d.net_rate = d.base_net_rate = flt(x['net'] / d.qty, d.precision('net_rate')) if d.qty else 0
            d.distributed_discount_amount = cu['net'] - x['net']
            d._unrounded_net_amount = x['net']

    def get_current_tax_and_net_amount(self, item, tax, item_tax_map):
        x = self.chia[self._items.index(item)]
        self.set_item_wise_tax(item, tax, x['rate'], x['vat'], x['net'])
        return x['net'], x['vat']

    def adjust_grand_total_for_inclusive_tax(self):
        # Tổng đã là tổng các dòng nguyên đồng, không sinh khoản bù 6428.
        self.grand_total_diff = 0


def tinh(doc):
    dong = [doc] + list(doc.items) + list(doc.taxes)
    cache_cu = [(d, deepcopy(getattr(d, '_precision', None))) for d in dong]
    do_chinh_xac(doc)
    # Constructor lõi thay hai cờ dùng chung; không để lan sang chứng từ sau.
    ten = ('round_row_wise_tax', 'round_off_applicable_accounts')
    cu = {k: frappe.flags.get(k) for k in ten}
    try:
        ThueVnd(doc)
        doc_dong(doc)
    except ValueError as loi:
        frappe.throw(str(loi) + ' Kế toán kiểm bảng thuế và giá từng dòng trước khi ghi sổ.')
    finally:
        # Một script có thể đổi tiền tệ trên chính object rồi tính tiếp.
        # Không để cache VND lọt sang lần tính bằng chính sách core.
        for d, cache in cache_cu:
            d._precision = cache
        for k, v in cu.items():
            frappe.flags[k] = v
    doc.vgb_thue_vnd = 1
    doc.calculate_commission()
    doc.calculate_contribution()
