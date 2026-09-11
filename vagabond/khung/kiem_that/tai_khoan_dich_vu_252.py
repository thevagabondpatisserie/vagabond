"""#252: Dung chọn tài khoản đầu phiếu nhưng dòng đã khớp tiền không đổi.

Kiểm bằng PI thật qua save/submit và GL. Core v16.28.0 PurchaseInvoice
validate_expense_account kiểm tài khoản từng dòng; set_against_expense_account
gom đầu phiếu từ các dòng. Tài khoản mặc định Món không được lấn lựa chọn
của kế toán trên phiếu dịch vụ. Tất cả fixture nằm trong điểm lưu của nen.
"""
import frappe
from vagabond import mua_dich_vu
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.he_so_252 import _luu
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _phieu, _nguon


def _tai_khoan(nhan):
    ct = nen.cong_ty()
    cha = frappe.db.get_value('Account',
        {'company': ct, 'root_type': 'Expense', 'is_group': 1}, 'name')
    dung('có nhóm tài khoản chi phí', bool(cha))
    return _luu(frappe.get_doc(dict(doctype='Account', company=ct,
        account_name='KT-DV252-' + nhan + '-' + frappe.generate_hash(length=8),
        parent_account=cha, account_currency='VND', is_group=0))).name


def _mon_dich_vu(tk):
    mon = frappe.get_doc('Item', _mon_thu('KT-DV252-' + frappe.generate_hash(length=9)))
    mon.is_stock_item = 0
    mon.set('item_defaults', [dict(company=nen.cong_ty(), expense_account=tk,
        buying_cost_center=frappe.db.get_value('Company', nen.cong_ty(), 'cost_center'))])
    mon.save(ignore_permissions=True)
    return mon


def _cac_so(hd):
    return dict(net_total=hd.net_total, grand_total=hd.grand_total,
        taxes=hd.total_taxes_and_charges,
        items=[(d.name, d.item_code, d.qty, d.rate, d.amount,
            d.uom, d.conversion_factor, d.stock_qty) for d in hd.items])


def _luong_dich_vu(so_dong):
    tk_mon, tk_dau, tk_doi = [_tai_khoan(nhan) for nhan in ('MON', 'DAU', 'DOI')]
    mon = _mon_dich_vu(tk_mon)
    ds = [('Dịch vụ thử252 dòng%s' % i, 1, 10000 + i * 1000)
        for i in range(1, so_dong + 1)]
    tong = sum(d[1] * d[2] for d in ds)
    goc = _nguon([dict(ten=ten, sluong=sl, dgia=gia, thtien=sl*gia,
        dvtinh=mon.stock_uom, tchat=1) for ten, sl, gia in ds], 0, tong)
    hd = _phieu(ds, mon=mon.name)
    _luu(hd)
    hd.custom_minvoice_id = goc.name
    hd.save(); hd.reload()
    la('trước chọn dịch vụ tiền đã khớp nguồn', hd.grand_total, tong)
    la('đủ dòng chưa gom', len(hd.items), so_dong)
    truoc = _cac_so(hd)
    hd.vgb_loai_chung_tu = mua_dich_vu.LOAI_DICH_VU
    hd.vgb_tk_chi_phi = tk_dau
    hd.save(); hd.reload()
    la('tài khoản đầu phiếu xuống toàn bộ dòng', [d.expense_account for d in hd.items], [tk_dau] * so_dong)
    la('đầu phiếu đồng bộ từ dòng', hd.against_expense_account, tk_dau)
    la('chọn dịch vụ không đổi số hoặc danh sách dòng', _cac_so(hd), truoc)
    hd.save(); hd.reload()
    la('lưu lặp không bị mặc định Món đè', [d.expense_account for d in hd.items], [tk_dau] * so_dong)
    hd.vgb_tk_chi_phi = tk_doi
    hd.save(); hd.reload()
    la('đổi lựa chọn cập nhật tất cả dòng', [d.expense_account for d in hd.items], [tk_doi] * so_dong)
    la('đầu phiếu theo lựa chọn mới', hd.against_expense_account, tk_doi)
    la('đổi tài khoản không đổi tiền', _cac_so(hd), truoc)
    hd.submit(); hd.reload()
    la('đã ghi sổ', hd.docstatus, 1)
    la('ghi sổ không mất lựa chọn', [d.expense_account for d in hd.items], [tk_doi] * so_dong)
    la('ghi sổ giữ tiền nguồn', hd.grand_total, tong)
    gl = nen.so_cai_cua(hd)
    dung('có GL thật', bool(gl))
    la('GL ghi chi phí vào lựa chọn mới', sum(d.debit-d.credit for d in gl if d.account == tk_doi), tong)
    la('không ghi vào mặc định Món', sum(d.debit-d.credit for d in gl if d.account == tk_mon), 0)
    la('không ghi vào lựa chọn đã bỏ', sum(d.debit-d.credit for d in gl if d.account == tk_dau), 0)
    la('GL cân', sum(d.debit-d.credit for d in gl), 0)
    la('dịch vụ không sinh SLE', frappe.db.count('Stock Ledger Entry',
        {'voucher_type': hd.doctype, 'voucher_no': hd.name}), 0)


@ca('#252 dịch vụ thật: hai dòng đã khớp tiền nhận tài khoản đầu phiếu và ghi GL đúng')
def _hai_dong():
    _luong_dich_vu(2)


@ca('#252 dịch vụ thật: tám dòng giữ nguyên tiền, đổi tài khoản và submit không bị Món đè')
def _tam_dong():
    _luong_dich_vu(8)


@ca('#252 dịch vụ thật: hook không đổi tài khoản dòng hàng kho hoặc dòng nối PNK')
def _giu_nguon_kho():
    tk_mon, tk_dau = _tai_khoan('GIU'), _tai_khoan('CHON')
    mon = _mon_dich_vu(tk_mon)
    ma_kho = _mon_thu('KT-DV252-KHO-' + frappe.generate_hash(length=8))
    # PR thật dạng nháp đủ để giữ quan hệ nguồn trong phép kiểm hook này;
    # không nhận là kiểm toàn luồng nối/ghi sổ PR, ca #227 đã giữ cửa đó.
    pr = _luu(frappe.get_doc(dict(doctype='Purchase Receipt', company=nen.cong_ty(),
        supplier=nen.mot_nha_cung_cap(), posting_date=frappe.utils.today(),
        items=[dict(item_code=mon.name, qty=1, rate=1000, expense_account=tk_mon)])))
    hd = _phieu([('Dịch vụ giữ nguồn', 1, 1000)], mon=mon.name, ncc=pr.supplier)
    hd.vgb_loai_chung_tu = mua_dich_vu.LOAI_DICH_VU
    hd.vgb_tk_chi_phi = tk_dau
    hd.items[0].purchase_receipt = pr.name
    hd.items[0].pr_detail = pr.items[0].name
    hd.items[0].expense_account = tk_mon
    hd.append('items', dict(item_code=ma_kho, qty=1, rate=1000, expense_account=tk_mon))
    hd.append('items', dict(item_code=mon.name, qty=1, rate=1000, expense_account=tk_mon))
    mua_dich_vu.gan_tai_khoan_chi_phi(hd, 'validate')
    la('dòng nối PNK giữ tài khoản', hd.items[0].expense_account, tk_mon)
    la('dòng kho giữ tài khoản', hd.items[1].expense_account, tk_mon)
    la('chỉ dịch vụ không có nguồn đổi', hd.items[2].expense_account, tk_dau)
    la('nguồn PR giữ nguyên', (hd.items[0].purchase_receipt, hd.items[0].pr_detail),
        (pr.name, pr.items[0].name))
    la('hai tài khoản đều hiện đầu phiếu', {t.strip() for t in hd.against_expense_account.split(',')}, {tk_mon, tk_dau})
