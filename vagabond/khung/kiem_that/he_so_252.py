"""Hệ số tại Document thật; không gửi HĐĐT, không sửa dữ liệu đã có."""
import frappe
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu
from vagabond.he_so_chung_tu import kiem


def _luu(doc):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    nen._DA_TAO.append((doc.doctype, doc.name))
    return doc


def _nen():
    ma = _mon_thu('KT-HS252-' + frappe.generate_hash(length=9))
    mon = frappe.get_doc('Item', ma)
    lon = 'Lon252-' + frappe.generate_hash(length=8)
    _luu(frappe.get_doc(dict(doctype='UOM', uom_name=lon, must_be_whole_number=1)))
    mon.append('uoms', dict(uom=lon, conversion_factor=550))
    mon.save(ignore_permissions=True)
    return mon, lon


def _pi(mon, lon, hs=550):
    return frappe.get_doc(dict(doctype='Purchase Invoice', company=nen.cong_ty(),
        supplier=nen.mot_nha_cung_cap(), currency='VND', conversion_rate=1,
        bill_no='KT-HS252-' + frappe.generate_hash(length=9), bill_date=frappe.utils.today(),
        posting_date=frappe.utils.today(), update_stock=0,
        items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=hs, rate=55000)]))


def _bi_chan(ham, nhan):
    try:
        ham()
    except frappe.ValidationError as e:
        dung(nhan + ' lỗi đúng hệ số', 'hệ số' in str(e) or 'quy cách' in str(e) or 'đơn vị' in str(e))
    else:
        dung(nhan + ' phải chặn', False)


@ca('#252 hệ số thật: PI Lon1 bị chặn, Lon550 lưu và reload giữ nguyên tiền')
def _pi_tay():
    mon, lon = _nen()
    truoc = frappe.db.count('Purchase Invoice')
    _bi_chan(lambda: _luu(_pi(mon, lon, 1)), 'insert API sai hệ số')
    la('không tạo PI sai', frappe.db.count('Purchase Invoice'), truoc)
    hd = _luu(_pi(mon, lon)); hd.reload()
    la('giữ hệ số đúng', hd.items[0].conversion_factor, 550)
    la('giữ lượng mua', hd.items[0].qty, 1)
    la('giữ tổng tiền', hd.grand_total, 55000)
    hd.items[0].conversion_factor = 1
    _bi_chan(lambda: hd.save(ignore_permissions=True), 'save Desk sai hệ số')
    hd.reload(); la('DB vẫn giữ quy cách đúng', hd.items[0].conversion_factor, 550)


@ca('#252 hệ số thật: giả stock_uom, hệ số âm/NaN/Inf và đơn vị kho khác1 không qua guard')
def _du_lieu_gia():
    mon, lon = _nen()
    hd = _pi(mon, lon)
    hd.items[0].stock_uom = lon
    _bi_chan(lambda: kiem(hd), 'không tin stock_uom của client')
    hd.items[0].stock_uom = mon.stock_uom
    for hs in (0, -1, float('nan'), float('inf')):
        hd.items[0].conversion_factor = hs
        _bi_chan(lambda: kiem(hd), 'số không hợp lệ')
    hd.items[0].uom = mon.stock_uom
    hd.items[0].conversion_factor = 550
    _bi_chan(lambda: kiem(hd), 'đơn vị kho phải là1')


@ca('#252 hệ số thật: danh mục đổi sau lưu nháp thì submit kiểm lại, không ghi GL dở')
def _doi_master():
    mon, lon = _nen()
    hd = _luu(_pi(mon, lon))
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    _bi_chan(lambda: hd.submit(), 'submit dùng danh mục mới')
    la('vẫn nháp', frappe.db.get_value(hd.doctype, hd.name, 'docstatus'), 0)
    la('không GL', frappe.db.count('GL Entry', {'voucher_type': hd.doctype, 'voucher_no': hd.name}), 0)


@ca('#252 hệ số thật: trả PI gốc giữ550 dù danh mục đã đổi1000')
def _tra_lich_su():
    mon, lon = _nen()
    hd = _luu(_pi(mon, lon)); hd.submit(); hd.reload()
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    tra = _pi(mon, lon)
    tra.is_return = 1; tra.return_against = hd.name
    tra.items[0].qty = -1
    _luu(tra); tra.submit(); tra.reload()
    la('phiếu trả ghi sổ', tra.docstatus, 1)
    la('trả đúng quy cách cũ', tra.items[0].conversion_factor, 550)
    la('trả đủ lượng cũ', tra.items[0].stock_qty, -550)
    la('PI gốc không bị sửa', frappe.db.get_value('Purchase Invoice Item', hd.items[0].name, 'conversion_factor'), 550)


@ca('#252 hệ số thật: nguồn PO khác master không tự hợp thức hoá PI, nguồn sai dòng bị chặn')
def _nguon():
    mon, lon = _nen()
    po = _luu(frappe.get_doc(dict(doctype='Purchase Order', company=nen.cong_ty(),
        supplier=nen.mot_nha_cung_cap(), schedule_date=frappe.utils.today(),
        items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=550,
            rate=55000, schedule_date=frappe.utils.today())])))
    po.submit(); po.reload()
    hd = _pi(mon, lon)
    hd.items[0].purchase_order = po.name
    hd.items[0].po_detail = po.items[0].name
    kiem(hd)
    # Đổi từ Lon sang đơn vị kho là nghiệp vụ core hợp lệ. Guard không
    # được so trực tiếp hệ số của hai đơn vị khác nhau rồi chặn nhầm.
    hd.items[0].uom = mon.stock_uom
    hd.items[0].stock_uom = mon.stock_uom
    hd.items[0].conversion_factor = 1
    hd.items[0].qty = 550
    kiem(hd)
    hd.items[0].uom = lon
    hd.items[0].conversion_factor = 550
    hd.items[0].qty = 1
    hd.items[0].po_detail = 'khong-thuoc-phieu'
    _bi_chan(lambda: kiem(hd), 'phải đúng dòng nguồn')
    hd.items[0].po_detail = po.items[0].name
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    _bi_chan(lambda: _luu(hd), 'không lấy nguồn cũ làm lý do bỏ qua chênh lệch')


@ca('#252 hệ số thật: SO/DN/SI/SE/PO/PR đều không nhận quy cách1 thay550')
def _cac_chung_tu():
    mon, lon = _nen()
    for loai in ('Sales Order', 'Delivery Note', 'Sales Invoice', 'Stock Entry', 'Purchase Order', 'Purchase Receipt'):
        doc = frappe.get_doc(dict(doctype=loai, company=nen.cong_ty(), items=[
            dict(item_code=mon.name, uom=lon, stock_uom=mon.stock_uom, conversion_factor=1, qty=1)]))
        _bi_chan(lambda: kiem(doc), loai)


@ca('#252 hệ số thật: alias NCC theo bảng Món, tên đơn vị lạ không rơi về1')
def _alias_ncc():
    from vagabond.minvoice_chung_tu import don_vi_theo_ma
    mon, _ = _nen()
    if not frappe.db.exists('UOM', 'Lon'):
        _luu(frappe.get_doc(dict(doctype='UOM', uom_name='Lon', must_be_whole_number=1)))
    mon.append('uoms', dict(uom='Lon', conversion_factor=550))
    mon.save(ignore_permissions=True)
    la('CAN dùng quy cách Lon của Món', don_vi_theo_ma(mon.name, 'CAN'), ('Lon', 550))
    la('tên đúng không bị hạ hệ số', don_vi_theo_ma(mon.name, 'Lon'), ('Lon', 550))
    _bi_chan(lambda: don_vi_theo_ma(mon.name, 'KIENTHU252-KHONG-BIET'), 'NCC ghi đơn vị chưa khai')


@ca('#252 hệ số thật: MInvoice cùng UOM1 được nắn550 qua hook mà không đổi tiền')
def _minvoice_cung_uom():
    from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon
    from vagabond import minvoice_chung_tu as mc
    from vagabond.dung_lai_hddt import nan_quy_cach_tu_goc
    mon, lon = _nen()
    ten = 'Cherry thử ' + frappe.generate_hash(length=8)
    raw = [{'ten': ten, 'dvtinh': lon, 'sluong': 1, 'dgia': 55000, 'thtien': 55000, 'tchat': '1'}]
    la('đọc đúng hình dạng nguồn thật', mc.dong_tu_hoa_don(mc.dong_hang_hoa(raw)[0])['dvt'], lon)
    goc = _nguon(raw, 0, 55000)
    hd = _pi(mon, lon, hs=1)
    hd.items[0].item_name = ten
    hd.items[0].ten_hang_ncc = ten
    hd.items[0].description = ten + ' (' + lon + ')'
    truoc = (hd.items[0].qty, hd.items[0].rate)
    nan_quy_cach_tu_goc(hd, goc.as_dict())
    la('hàm nắn cùng UOM sửa hệ số', hd.items[0].conversion_factor, 550)
    la('hàm nắn không đổi lượng/giá', (hd.items[0].qty, hd.items[0].rate), truoc)
    # Trả về lỗi đầu vào rồi để before_validate thật sửa lại trước guard.
    hd.items[0].conversion_factor = 1
    hd.custom_minvoice_id = goc.name
    _luu(hd); hd.reload()
    la('hook insert thực sự nắn550', hd.items[0].conversion_factor, 550)
    la('lượng kho đúng', hd.items[0].stock_qty, 550)
    la('không sửa lượng/giá qua insert', (hd.items[0].qty, hd.items[0].rate), truoc)
    la('tiền vẫn55000', hd.grand_total, 55000)
    hd.items[0].conversion_factor = 1
    hd.save(ignore_permissions=True); hd.reload()
    la('hook save vẫn sửa lại550', hd.items[0].conversion_factor, 550)
    la('save vẫn giữ tiền', hd.grand_total, 55000)


@ca('#252 quy cách NCC thật: đúng MST/tên dùng UOM đã chọn, sai món/UOM bị chặn')
def _quy_cach_ncc():
    from vagabond import quy_cach_ncc as qc
    mon, lon = _nen()
    mst = 'KT252' + frappe.generate_hash(length=8)
    ten = 'Chai riêng NCC ' + frappe.generate_hash(length=8)
    ban = _luu(frappe.get_doc(dict(doctype=qc.LOAI, supplier_mst=mst,
        ten_ncc=ten, item_code=mon.name, vgb_uom=lon)))
    la('đúng NCC và tên lấy quy cách', qc.lay(mon.name, mst, ten), lon)
    la('MST chi nhánh cùng quy cách gốc', qc.lay(mon.name, mst+'-005', ten), lon)
    ban.supplier_mst = mst+'-005'
    ban.save(ignore_permissions=True); ban.reload()
    la('lưu ánh xạ chuẩn hoá MST chi nhánh', ban.supplier_mst, mst)
    frappe.db.set_value(qc.LOAI, ban.name, 'supplier_mst', mst+'-005')
    la('ánh xạ chi nhánh cũ không bị bỏ qua', qc.lay(mon.name, mst, ten), lon)
    from vagabond.minvoice_chung_tu import _tra_ma_hang
    la('đường dựng tra cả món từ ánh xạ chi nhánh cũ',
       _tra_ma_hang({'ma':'','ten':ten,'dvt':mon.stock_uom}, mst, nen.mot_nha_cung_cap()),
       (mon.name, lon, 550))
    trung = _luu(frappe.get_doc(dict(doctype=qc.LOAI, supplier_mst=mst,
        ten_ncc=ten, item_code=mon.name, vgb_uom=lon)))
    _bi_chan(lambda: qc.lay(mon.name, mst, ten), 'hai ánh xạ gốc/chi nhánh phải đối chiếu')
    frappe.delete_doc(qc.LOAI, trung.name, ignore_permissions=True)
    ban.reload(); ban.save(ignore_permissions=True)
    la('khác NCC không mượn quy cách', qc.lay(mon.name, mst+'x', ten), None)
    la('khác tên không mượn quy cách', qc.lay(mon.name, mst, ten+'x'), None)
    khac, _ = _nen()
    _bi_chan(lambda: qc.lay(khac.name, mst, ten), 'ánh xạ chọn món khác')
    ban.vgb_uom = khac.uoms[-1].uom
    _bi_chan(lambda: ban.save(ignore_permissions=True), 'UOM chưa khai của món')
    ban.reload(); la('ánh xạ đúng vẫn nguyên', ban.vgb_uom, lon)
    from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon
    goc = _nguon([{'ten': ten, 'dvtinh': lon, 'sluong': 1, 'dgia': 55000, 'thtien': 55000}], 0, 55000)
    frappe.db.set_value(goc.doctype, goc.name, 'mst_doi_tac', mst+'-005')
    hd = _pi(mon, mon.stock_uom, 1)
    hd.custom_minvoice_id = goc.name
    hd.items[0].ten_hang_ncc = ten
    _bi_chan(lambda: kiem(hd), 'không đổi sang UOM khác dù hợp lệ trong master')
    hd.items[0].uom = lon; hd.items[0].conversion_factor = 550
    kiem(hd)


@ca('#252 sửa PI lịch sử thật: huỷ và amended_from giữ tiền/PR, sửa1 thành1000 không nhập kho lại')
def _sua_pi_da_ghi():
    _sua_pi_theo_cau_hinh(0)


@ca('#252 sửa PI lịch sử thật: bật điều chỉnh giá nhập, repost cả ba bước giữ giá trị PR')
def _sua_pi_da_ghi_co_repost():
    _sua_pi_theo_cau_hinh(1)


def _sua_pi_theo_cau_hinh(chinh_gia):
    from unittest.mock import patch
    from vagabond.khung.kiem_that.quy_cach_252 import _chay_repost
    frappe.db.set_single_value('Buying Settings', 'set_landed_cost_based_on_purchase_invoice_rate', chinh_gia)
    mon, kg = _nen()
    don_vi = frappe.get_doc('UOM', kg)
    don_vi.must_be_whole_number = 0; don_vi.save(ignore_permissions=True)
    gram = 'Gram252-' + frappe.generate_hash(length=8)
    _luu(frappe.get_doc(dict(doctype='UOM', uom_name=gram, must_be_whole_number=0)))
    mon.stock_uom = gram
    # Core Item.add_default_uom_in_conversion_factor_table xoá bảng quy đổi khi đổi stock_uom trên
    # Item đã có. Lưu đơn vị kho trước rồi mới khai hệ số mua cho ca thử.
    mon.save(ignore_permissions=True); mon.reload()
    mon.set('uoms', [dict(uom=gram, conversion_factor=1), dict(uom=kg, conversion_factor=1000)])
    mon.save(ignore_permissions=True)
    la('nền thực sự có hệ số mua1000', frappe.db.get_value('UOM Conversion Detail',
        {'parent': mon.name, 'parenttype': 'Item', 'uom': kg}, 'conversion_factor'), 1000)
    ct, kho = nen.cong_ty(), nen.mot_kho(nen.cong_ty())
    pr = _luu(frappe.get_doc(dict(doctype='Purchase Receipt', company=ct,
        supplier=nen.mot_nha_cung_cap(), posting_date=frappe.utils.today(),
        currency='VND', conversion_rate=1, items=[dict(item_code=mon.name,
            qty=6.13, uom=kg, conversion_factor=1000, rate=139500, warehouse=kho)])))
    pr.submit(); pr.reload()
    la('PR thật đủ6130', pr.items[0].stock_qty, 6130)
    def so_kho():
        return frappe.get_all('Stock Ledger Entry', filters={'item_code': mon.name},
            fields=['name', 'voucher_type', 'voucher_no', 'actual_qty', 'stock_value_difference',
                    'qty_after_transaction', 'stock_value', 'is_cancelled'], order_by='name')
    def so_cai(d):
        return frappe.get_all('GL Entry', filters={'voucher_type': d.doctype, 'voucher_no': d.name},
            fields=['account', 'debit', 'credit', 'is_cancelled'], order_by='name')
    sle_truoc, gl_pr = so_kho(), so_cai(pr)
    cu = _pi(mon, kg, hs=1)
    cu.items[0].qty = 6.13; cu.items[0].rate = 139500
    cu.items[0].purchase_receipt = pr.name; cu.items[0].pr_detail = pr.items[0].name
    # Đây là PI đã lọt trước khi có guard. Không vá SQL hoặc bỏ các kiểm
    # toán/ghi sổ core; guard được bật lại trước thao tác huỷ và sửa.
    with patch('vagabond.he_so_chung_tu.kiem', lambda *a, **kw: None):
        _luu(cu); cu.submit()
    _chay_repost(pr)
    cu.reload()
    la('PI cũ thực sự ghi sai1', cu.items[0].conversion_factor, 1)
    la('PI cũ giữ đúng tiền', cu.grand_total, 855135)
    la('PI cũ không tạo phiếu kho riêng', frappe.db.count('Stock Ledger Entry', {
        'voucher_type': 'Purchase Invoice', 'voucher_no': cu.name}), 0)
    la('PI cũ không nhân lượng đã nhận', sum(d.actual_qty for d in so_kho() if not d.is_cancelled), 6130)
    cu.cancel(); _chay_repost(pr); cu.reload()
    la('huỷ và repost giữ cơ sở PR đúng ban đầu', so_kho(), sle_truoc)
    moi = frappe.copy_doc(cu)
    moi.docstatus = 0; moi.amended_from = cu.name
    moi.items[0].conversion_factor = 1000
    _luu(moi); moi.submit(); _chay_repost(pr); moi.reload()
    la('phiếu cũ đã huỷ', cu.docstatus, 2)
    la('phiếu mới ghi sổ', moi.docstatus, 1)
    la('giữ đường sửa đổi', moi.amended_from, cu.name)
    la('đúng hệ số1000', moi.items[0].conversion_factor, 1000)
    la('giữ6.13đơn vị mua', moi.items[0].qty, 6.13)
    la('giữ tiền855135', moi.grand_total, 855135)
    la('giữ đúng PR', moi.items[0].purchase_receipt, pr.name)
    la('giữ đúng dòng PR', moi.items[0].pr_detail, pr.items[0].name)
    la('toàn bộ SLE không đổi', so_kho(), sle_truoc)
    la('GL của PR không đổi', so_cai(pr), gl_pr)
    gl_cu, gl_moi = so_cai(cu), so_cai(moi)
    for tk in {d.account for d in gl_cu}:
        la('huỷ đảo đủ tài khoản '+tk, sum(d.debit-d.credit for d in gl_cu if d.account == tk), 0)
    la('PI mới ghi nợ855135', sum(d.debit for d in gl_moi if not d.is_cancelled), 855135)
    la('PI mới ghi có855135', sum(d.credit for d in gl_moi if not d.is_cancelled), 855135)
    pr.reload()
    la('PR vẫn giữ1000', pr.items[0].conversion_factor, 1000)
    la('PR chỉ tính tiền một hoá đơn', pr.items[0].billed_amt, 855135)


@ca('#252 POS thật: Lon1 bị chặn, Lon550 ghi sổ và giữ chỗ550 trước consolidation')
def _pos():
    from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
    from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_pos_reserved_qty
    mon, lon = _nen()
    ct, kho = nen.cong_ty(), nen.mot_kho(nen.cong_ty())
    company = frappe.get_doc('Company', ct)
    frappe.db.set_single_value('POS Settings', 'invoice_type', 'POS Invoice')
    nhap = make_stock_entry(item_code=mon.name, qty=1100, company=ct,
        to_warehouse=kho, rate=10, do_not_save=True)
    _luu(nhap); nhap.submit()
    cash = frappe.db.get_value('Account', {'company': ct, 'account_type': 'Cash', 'is_group': 0}, 'name')
    if not cash:
        raise AssertionError('Bench cần tài khoản Cash để kiểm POS thật')
    pt = _luu(frappe.get_doc(dict(doctype='Mode of Payment',
        mode_of_payment='KT-POS252-'+frappe.generate_hash(length=8), type='Cash',
        accounts=[dict(company=ct, default_account=cash)])))
    profile = _luu(frappe.get_doc(dict(doctype='POS Profile',
        name='KT-POS252-'+frappe.generate_hash(length=8), company=ct, currency='VND',
        warehouse=kho, cost_center=company.cost_center,
        income_account=company.default_income_account, expense_account=company.default_expense_account,
        write_off_account=company.default_expense_account, write_off_cost_center=company.cost_center,
        write_off_limit=1,
        selling_price_list=frappe.db.get_value('Price List', {'selling': 1, 'enabled': 1}, 'name'),
        payments=[dict(mode_of_payment=pt.name, default=1)])))
    opening = _luu(frappe.get_doc(dict(doctype='POS Opening Entry', pos_profile=profile.name,
        company=ct, user=frappe.session.user, period_start_date=frappe.utils.now_datetime(),
        balance_details=[dict(mode_of_payment=pt.name, opening_amount=0)])))
    opening.submit()
    def phieu(hs):
        return frappe.get_doc(dict(doctype='POS Invoice', is_pos=1, update_stock=1,
            pos_profile=profile.name, company=ct, currency='VND', conversion_rate=1,
            customer=frappe.db.get_value('Customer', {'disabled': 0, 'is_internal_customer': 0}, 'name'),
            account_for_change_amount=cash, posting_date=frappe.utils.today(),
            items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=hs,
                rate=55000, warehouse=kho)],
            payments=[dict(mode_of_payment=pt.name, account=cash, amount=55000)]))
    truoc = frappe.db.count('POS Invoice')
    _bi_chan(lambda: _luu(phieu(1)), 'POS insert sai quy cách')
    la('không tạo POS sai', frappe.db.count('POS Invoice'), truoc)
    hd = _luu(phieu(550)); hd.submit(); hd.reload()
    la('POS đã ghi sổ', hd.docstatus, 1)
    la('POS giữ hệ số550', hd.items[0].conversion_factor, 550)
    la('POS lượng kho550', hd.items[0].stock_qty, 550)
    la('POS giữ tiền55000', hd.grand_total, 55000)
    # POSInvoice.on_submit không ghi SLE/GL như SalesInvoice. Core giữ
    # chỗ đến khi consolidation, nên không tuyên bố đã trừ sổ kho ở đây.
    la('core giữ chỗ550', get_pos_reserved_qty(mon.name, kho), 550)
    la('trước consolidation không SLE POS', frappe.db.count('Stock Ledger Entry',
        {'voucher_type': 'POS Invoice', 'voucher_no': hd.name}), 0)
    la('kho vật lý vẫn1100', frappe.db.get_value('Bin',
        {'item_code': mon.name, 'warehouse': kho}, 'actual_qty'), 1100)


@ca('#252 PR trả lịch sử: script cũ chặn, hook mới trả550 sau master1000 và giữ SLE')
def _pr_tra_lich_su():
    from vagabond.patches.pr_he_so_252 import TEN, nhan_dang, execute, ban_cu
    if not frappe.db.exists('Server Script', TEN):
        _luu(frappe.get_doc(dict(doctype='Server Script', name=TEN,
            script_type='DocType Event', reference_doctype='Purchase Receipt',
            doctype_event='Before Validate', disabled=1, script=ban_cu())))
    cu = frappe.get_doc('Server Script', TEN)
    dung('đúng script cũ đã lưu trữ', nhan_dang(cu) and cu.disabled)
    execute()  # Migrate lặp lại không xoá hoặc đổi script đã lưu trữ.
    la('nội dung lưu trữ nguyên trạng', frappe.get_doc('Server Script', TEN).script, cu.script)
    mon, lon = _nen()
    ct = nen.cong_ty()
    kho = nen.mot_kho(ct)
    def phieu(hs=550):
        return frappe.get_doc(dict(doctype='Purchase Receipt', company=ct,
            supplier=nen.mot_nha_cung_cap(), currency='VND', conversion_rate=1,
            posting_date=frappe.utils.today(), items=[dict(item_code=mon.name,
                uom=lon, stock_uom=mon.stock_uom, qty=1, conversion_factor=hs,
                rate=55000, warehouse=kho)]))
    pr = _luu(phieu()); pr.submit(); pr.reload()
    la('nhập thực550', pr.items[0].stock_qty, 550)
    mon.reload()
    next(d for d in mon.uoms if d.uom == lon).conversion_factor = 1000
    mon.save(ignore_permissions=True)
    tra = phieu()
    tra.is_return = 1
    tra.return_against = pr.name
    tra.items[0].qty = -1
    tra.items[0].purchase_receipt_item = pr.items[0].name
    # execute_doc gọi safe_exec trực tiếp, không xét disabled. Không bật lại
    # Server Script chung hoặc sửa map cache của site để tái hiện lỗi cũ.
    try:
        cu.execute_doc(tra)
    except frappe.ValidationError as e:
        dung('script cũ chặn đúng quy đổi', 'quy đổi' in str(e) and '1000' in str(e))
    else:
        dung('script cũ phải chặn trả lịch sử', False)
    _luu(tra); tra.submit(); tra.reload()
    la('trả PR ghi sổ', tra.docstatus, 1)
    la('giữ hệ số nguồn550', tra.items[0].conversion_factor, 550)
    la('trả đủ lượng nguồn', tra.items[0].stock_qty, -550)
    sle = frappe.get_all('Stock Ledger Entry', filters={'item_code': mon.name, 'is_cancelled': 0},
        fields=['voucher_no', 'actual_qty', 'stock_value_difference'])
    la('SLE nhập550', sum(d.actual_qty for d in sle if d.voucher_no == pr.name), 550)
    la('SLE trả âm550', sum(d.actual_qty for d in sle if d.voucher_no == tra.name), -550)
    la('giá trị nhập trả triệt tiêu', round(sum(d.stock_value_difference for d in sle), 2), 0)
    _bi_chan(lambda: _luu(phieu()), 'PR mới vẫn phải theo master1000')
    la('PR nguồn vẫn550', frappe.db.get_value('Purchase Receipt Item', pr.items[0].name, 'conversion_factor'), 550)
