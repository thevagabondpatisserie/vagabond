"""#243: xuất hàng tặng một lần bằng SI, giá vốn lấy từ sổ kho của core.

Không biến kiểm bánh thành chứng từ. Dấu chính sách chỉ cấp cho SI mới;
phiếu cũ không tự bật kho khi migrate, huỷ hoặc tính lại giá vốn.
"""
import frappe
import math
from frappe.utils import cint, flt

TRUONG = {
    'Sales Invoice': [
        dict(fieldname='vgb_tang_kho_moi', label='Luồng xuất kho hàng tặng mới',
             fieldtype='Check', read_only=1, hidden=1, no_copy=1, insert_after='vgb_tang_cho_gia_von'),
        dict(fieldname='vgb_tang_kho', label='Kho xuất hàng tặng', fieldtype='Link',
             options='Warehouse', read_only=1, no_copy=1, insert_after='vgb_tang_kho_moi'),
    ],
    'Stock Entry': [dict(fieldname='vgb_hoa_don_tang', label='Hoá đơn hàng tặng liên quan',
        fieldtype='Link', options='Sales Invoice', no_copy=1, insert_after='purpose',
        description='Hoá đơn đã tự xuất kho thì không lập thêm phiếu xuất cho cùng hàng tặng.')],
}


def kiem_kho(kho, cong_ty):
    d = frappe.get_cached_doc('Warehouse', kho)
    if d.company != cong_ty or d.is_group or d.disabled:
        frappe.throw('Kho %s phải là kho chi tiết còn dùng của %s. Kiểm Cài đặt > Điểm bán.' % (kho, cong_ty))
    # StockController.get_inventory_account_map lấy tài khoản theo kho.
    # Không đoán 155 hoặc lấy 152 từ Item Default cho bánh thành phẩm.
    if not d.account:
        frappe.throw('Kế toán gắn tài khoản tồn kho thành phẩm cho kho %s trước khi dùng xuất hàng tặng.' % kho)
    tk = frappe.get_cached_doc('Account', d.account)
    if (tk.company != cong_ty or tk.is_group or tk.disabled or tk.root_type != 'Asset'
            or tk.account_type != 'Stock' or tk.account_currency != 'VND'):
        frappe.throw('Tài khoản kho %s chưa hợp lệ. Kế toán kiểm tài khoản tồn kho VND của công ty.' % kho)
    if not str(tk.account_number or '').startswith('155'):
        frappe.throw('Kho %s chưa gắn tài khoản thành phẩm 155/1551. Chọn kho bánh thực giao; '
            'không dùng kho nguyên liệu 152 cho hàng tặng.' % kho)
    return d


def kiem_lo_da_chon(doc):
    """get_item_details.get_basic_details xoá ctx.batch_no khi sai món.

    Phải kiểm trước super().set_missing_values: sau đó lựa chọn tay đã
    mất, phần tự chia lô không còn biết người dùng chọn nhầm. Áp dụng
    cho cả SI bán thường và tặng, giữ nguyên chứng từ đã ghi sổ/huỷ.
    """
    if doc.docstatus == 2 or getattr(doc, '_action', None) == 'update_after_submit':
        return
    for d in doc.get('items') or []:
        if not d.get('batch_no') or not d.get('item_code'):
            continue
        ma_lo = frappe.get_cached_value('Batch', d.batch_no, 'item')
        if ma_lo != d.item_code:
            frappe.throw('Dòng %s, món %s: lô %s thuộc món %s. Chọn lại đúng lô của món này '
                'trước khi lưu hoặc ghi sổ; máy không tự đổi lô đã chọn.'
                % (d.idx, d.item_code, d.batch_no, ma_lo or 'không còn tồn tại'))


def chuan_bi(doc):
    """Gọi sau set_missing_values, trước core kiểm kho và tính giá.

    Không tin marker client. Chỉ SI mới sau patch nhận chính sách mới;
    bản sao là chứng từ mới, SI đã ghi sổ luôn giữ dấu đã lưu.
    """
    if not doc.meta.has_field('vgb_tang_kho_moi'):
        return
    if doc.docstatus == 2 or getattr(doc, '_action', None) == 'update_after_submit':
        return
    cu = None if doc.is_new() else frappe.db.get_value('Sales Invoice', doc.name,
        ['docstatus', 'vgb_tang_kho_moi'], as_dict=True)
    doc.vgb_tang_kho_moi = 1 if doc.is_new() else cint(cu and cu.vgb_tang_kho_moi)
    if cu and cu.docstatus != 0:
        return
    from vagabond.minvoice_an_toan import la_hang_tang
    if not doc.vgb_tang_kho_moi:
        return
    if not la_hang_tang(doc):
        if doc.get('vgb_tang_kho'):
            # Đổi đơn nháp từ tặng sang bán thường phải trả lại luồng cũ.
            # Không để 64181 và cờ xuất kho tự động đi theo bill thu tiền.
            doc.update_stock = 0
            for d in doc.items:
                if d.get('expense_account') and frappe.get_cached_value('Account', d.expense_account, 'account_number') == '64181':
                    d.expense_account = None
            doc.vgb_tang_kho = None
        return
    if doc.get('is_return') or doc.get('is_debit_note'):
        frappe.throw('Hàng tặng cần xử lý huỷ đúng hoá đơn gốc, không tạo phiếu trả hàng độc lập.')
    if doc.get('packed_items') or any(frappe.db.exists('Product Bundle', d.item_code) for d in doc.items):
        frappe.throw('Đơn tặng có bộ sản phẩm. Tách thành các món tồn kho thực giao trước khi duyệt '
            'để ghi đúng lượng và giá vốn từng món.')
    hang = [d for d in doc.items if frappe.get_cached_value('Item', d.item_code, 'is_stock_item')]
    doc.update_stock = int(bool(hang))
    if not hang:
        doc.vgb_tang_kho = None
        return
    from vagabond import diem_ban
    ma = diem_ban.ma_theo_quay(doc.get('vgb_quay'))
    diem = diem_ban.theo_ma(ma)
    kho = diem and diem.get('kho_tang')
    if not kho:
        frappe.throw('Điểm bán %s chưa có Kho xuất hàng tặng. Kế toán vào Cài đặt > Điểm bán, '
            'chọn kho thành phẩm thực xuất rồi lưu lại hoá đơn.' % ma)
    kiem_kho(kho, doc.company)
    from vagabond.hang_tang_so_cai import tai_khoan
    tk = tai_khoan(doc.company, '64181', 'Expense')
    doc.vgb_tang_kho = kho
    for d in hang:
        if d.get('delivery_note') or d.get('is_fixed_asset'):
            frappe.throw('Dòng %s đã có phiếu giao hàng hoặc tài sản. Kế toán đối chiếu chứng từ gốc trước.' % d.idx)
        if d.warehouse and d.warehouse != kho and (d.get('batch_no') or d.get('serial_and_batch_bundle')):
            frappe.throw('Dòng %s đổi kho xuất: chọn lại lô tại %s trước khi lưu.' % (d.idx, kho))
        d.warehouse = kho
        d.expense_account = tk
        d.cost_center = d.cost_center or doc.cost_center or frappe.get_cached_value('Company', doc.company, 'cost_center')
        d.allow_zero_valuation_rate = 0


def truoc_ghi_so(doc):
    """SellingController.update_stock_ledger rồi StockController.get_gl_entries.

    Giữ lõi chọn/kiểm lô, không cho lượng âm dù cấu hình chung đang cho phép.
    Khoá Bin theo thứ tự cố định trước khi kiểm tổng của các dòng trùng mã.
    """
    if not doc.get('vgb_tang_kho_moi'):
        return
    # Hook thanh_toan_nhieu đặt lại phương thức sau validate của core.
    # Không cho thay loại muộn khiến phiếu tặng bỏ qua kiểm kho bên trên.
    hang = [d for d in doc.items if frappe.get_cached_value('Item', d.item_code, 'is_stock_item')]
    if hang and (not doc.update_stock or not doc.get('vgb_tang_kho')):
        frappe.throw('Phương thức thanh toán vừa đổi sang Hàng tặng. Lưu lại đơn nháp để máy '
            'kiểm kho xuất và giá vốn trước khi ghi sổ.')
    from vagabond.hang_tang_so_cai import tai_khoan
    if hang:
        tk = tai_khoan(doc.company, '64181', 'Expense')
        kiem_kho(doc.vgb_tang_kho, doc.company)
        if any(d.warehouse != doc.vgb_tang_kho or d.expense_account != tk for d in hang):
            frappe.throw('Kho hoặc tài khoản hàng tặng vừa thay đổi. Lưu lại đơn nháp để kiểm cấu hình trước khi ghi sổ.')
    from erpnext import is_perpetual_inventory_enabled
    if doc.update_stock and not is_perpetual_inventory_enabled(doc.company):
        frappe.throw('Kế toán bật kế toán kho liên tục cho công ty trước khi ghi giá vốn hàng tặng.')
    nhom = {}
    for d in doc.items:
        if frappe.get_cached_value('Item', d.item_code, 'is_stock_item'):
            nhom[(d.item_code, d.warehouse)] = nhom.get((d.item_code, d.warehouse), 0) + flt(d.stock_qty)
    from erpnext.stock.utils import get_stock_balance
    for (ma, kho), sl in sorted(nhom.items()):
        frappe.db.sql('select name from `tabBin` where item_code=%s and warehouse=%s for update', (ma, kho))
        ton = get_stock_balance(ma, kho, doc.posting_date, doc.posting_time)
        if not math.isfinite(sl) or sl <= 0 or flt(ton) + 0.000001 < sl:
            frappe.throw('Món %s tại %s còn %s, cần %s. Nhập hoặc chuyển hàng thật vào đúng kho rồi ghi sổ; '
                'không xuất âm hàng tặng.' % (ma, kho, ton, sl))
    from erpnext.stock.serial_batch_bundle import SerialBatchCreation
    from erpnext.stock.doctype.batch.batch import get_available_batches
    lo_con = {}
    for ma, kho in sorted(nhom):
        if frappe.get_cached_value('Item', ma, 'has_batch_no'):
            lo_con[(ma, kho)] = dict(get_available_batches(frappe._dict(item_code=ma,
                warehouse=kho, qty=0, based_on='Expiry', posting_date=doc.posting_date,
                posting_time=doc.posting_time)))
    # Trừ phần đã chọn tay trước, rồi chia phần tự chọn cho cả hoá đơn.
    # Hai dòng cùng mã không được cùng lấy nguyên một lượng của lô đầu.
    for d in doc.items:
        con = lo_con.get((d.item_code, d.warehouse))
        if con is None:
            continue
        da_chon = []
        if d.get('batch_no'):
            da_chon = [(d.batch_no, flt(d.stock_qty))]
        elif d.get('serial_and_batch_bundle'):
            goi_cu = frappe.get_doc('Serial and Batch Bundle', d.serial_and_batch_bundle)
            da_chon = [(r.batch_no, abs(flt(r.qty))) for r in goi_cu.entries if r.batch_no]
        for lo, sl in da_chon:
            con[lo] = flt(con.get(lo)) - sl
            if con[lo] < -0.000001:
                frappe.throw('Dòng %s: lô %s tại %s không đủ lượng đã chọn hoặc hết hạn. Chọn lại lô đúng.' % (d.idx, lo, d.warehouse))
    for d in doc.items:
        if not frappe.get_cached_value('Item', d.item_code, 'has_batch_no'):
            continue
        if d.get('batch_no') or d.get('serial_and_batch_bundle'):
            continue  # lõi kiểm lô đã chọn, không âm thầm đổi sang lô khác
        con = lo_con[(d.item_code, d.warehouse)]
        chon, can = {}, flt(d.stock_qty)
        for lo, sl in con.items():
            lay = min(max(0, flt(sl)), can)
            if lay:
                chon[lo] = lay
                con[lo] -= lay
                can -= lay
            if can < 0.000001:
                break
        if can > 0.000001:
            frappe.throw('Dòng %s, món %s tại %s thiếu %s theo lô còn dùng. Kiểm lô trước khi ghi sổ.' % (d.idx, d.item_code, d.warehouse, can))
        goi = SerialBatchCreation(dict(item_code=d.item_code, warehouse=d.warehouse,
            company=doc.company, voucher_type=doc.doctype, voucher_no=doc.name,
            voucher_detail_no=d.name, posting_date=doc.posting_date, posting_time=doc.posting_time,
            posting_datetime='%s %s' % (doc.posting_date, doc.posting_time),
            actual_qty=-flt(d.stock_qty), qty=flt(d.stock_qty), batches=chon, type_of_transaction='Outward',
            do_not_submit=True)).make_serial_and_batch_bundle()
        if not goi.get('name'):
            frappe.throw('Món %s tại %s chưa đủ lô còn dùng. Kiểm lô và hạn dùng trước khi ghi sổ.' % (d.item_code, d.warehouse))
        d.serial_and_batch_bundle = goi.name


def chan_xuat_tay(doc, method=None):
    """Chặn cả Desk/API ở Document, không chỉ giấu nút của app.

    Không thể suy ra phiếu xuất không khai nguồn là của khách nào. Vì vậy
    phiếu dùng 64181 phải dẫn về hoá đơn; SI mới tự xuất thì không xuất lại.
    """
    if doc.docstatus == 2:
        return
    tk = {d.expense_account for d in doc.items if d.get('s_warehouse') and d.get('expense_account')}
    la_tang = any(frappe.get_cached_value('Account', t, 'account_number') == '64181' for t in tk)
    ten = doc.get('vgb_hoa_don_tang')
    if not la_tang and not ten:
        return
    if not ten:
        frappe.throw('Phiếu xuất dùng 64181 cần chọn Hoá đơn hàng tặng liên quan. '
            'Hoá đơn đã tự xuất kho thì không lập thêm phiếu xuất tay.')
    hd = frappe.get_doc('Sales Invoice', ten)
    if hd.company != doc.company:
        frappe.throw('Hoá đơn hàng tặng và phiếu kho phải cùng công ty.')
    if hd.get('vgb_tang_kho_moi'):
        frappe.throw('Hoá đơn %s dùng luồng tự xuất kho khi ghi sổ. Không xuất tay thêm cho cùng hàng; '
            'kiểm Sổ kho từ hoá đơn.' % ten)
    # Phiếu cũ chỉ đối chiếu, không tự lập hoặc sửa chứng từ quá khứ.
    from vagabond.minvoice_an_toan import la_hang_tang
    if not la_hang_tang(hd) or hd.docstatus != 1:
        frappe.throw('Chọn đúng hoá đơn hàng tặng cũ đã ghi sổ để kế toán đối chiếu phiếu xuất riêng.')
    frappe.db.get_value('Sales Invoice', ten, 'name', for_update=True)
    trung = frappe.db.get_value('Stock Entry', {'vgb_hoa_don_tang': ten,
        'docstatus': ['!=', 2], 'name': ['!=', doc.name or '']}, 'name')
    if trung:
        frappe.throw('Hoá đơn %s đã có phiếu xuất %s. Mở phiếu đó để đối chiếu, không lập thêm lần xuất.' % (ten, trung))
