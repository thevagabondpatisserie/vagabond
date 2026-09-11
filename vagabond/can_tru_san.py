"""#262: cấn phí sàn đã giữ vào công nợ MTT, không ép số dư về không.

Core pin ERPNext de591661: journal_entry.validate_reference_doc yêu cầu
party/account trùng SI/PI; validate_invoices yêu cầu docstatus=1 và không
vượt outstanding. JE tạo qua insert/submit để GL/Payment Ledger chạy đủ.
Phiếu đối soát duyệt trước là quyền và căn cứ, không suy bù từ tên Grab.
"""
# phần thuần
from decimal import Decimal, InvalidOperation
from hashlib import sha256


def tien(so):
    try:
        kq = Decimal(str(so))
        if not kq.is_finite():
            raise ValueError()
        return kq
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Số tiền phải là số hữu hạn.')


def ket_qua(dau, doanh_thu, da_nhan, phi):
    du = tien(dau) + tien(doanh_thu) - tien(da_nhan) - tien(phi)
    return dict(du=float(du), trang_thai='Đã khớp' if du == 0 else ('Sàn còn phải trả' if du > 0 else 'Cần kiểm tra dư Có'))


def tong_dong(ds):
    da_co = set()
    tong = Decimal(0)
    for d in ds:
        ma = d.get('hoa_don')
        if not ma or ma in da_co:
            raise ValueError('Chọn mỗi hoá đơn đúng một lần trong bảng.')
        da_co.add(ma)
        so = tien(d.get('so_tien'))
        if so <= 0 or so != so.to_integral_value():
            raise ValueError('Tiền bù VND phải là số nguyên lớn hơn 0.')
        tong += so
    if not ds:
        raise ValueError('Khai đủ hoá đơn phí và hoá đơn bán trước khi duyệt.')
    return tong


import frappe
from frappe.utils import getdate

DT = 'Vagabond Can Tru San'
TRUONG_MOI = {'Journal Entry': [dict(fieldname='vgb_can_tru_san', label='Phiếu cấn trừ sàn',
    fieldtype='Link',options=DT,read_only=1,no_copy=1)]}


def kiem_quyen_duyet():
    if not set(frappe.get_roles()) & {'Accounts Manager','System Manager'}:
        frappe.throw('Chỉ kế toán trưởng hoặc quản trị được duyệt cấn trừ sàn.')


def kiem_phieu(d):
    from vagabond import diem_ban
    if not diem_ban.theo_ma(d.diem_ban):
        frappe.throw('Chọn điểm bán trong danh mục hiện hành.')
    if getdate(d.tu_ngay) > getdate(d.den_ngay) or getdate(d.ngay_bu) < getdate(d.den_ngay):
        frappe.throw('Kiểm lại kỳ đối soát và ngày bù: ngày bù không trước cuối kỳ.')
    if frappe.db.get_value('Company',d.company,'default_currency') != 'VND':
        frappe.throw('Cấn trừ tự động hiện hỗ trợ công ty dùng VND.')
    d.mst = str(frappe.db.get_value('Supplier',d.nha_cung_cap,'tax_id') or '').strip()
    if not d.mst:
        frappe.throw('Nhà cung cấp phí chưa có mã số thuế. Bổ sung trước khi duyệt.')
    try:
        a, b = tong_dong(d.phi), tong_dong(d.ban)
    except ValueError as e:
        frappe.throw(str(e))
    if a != b:
        frappe.throw('Tổng phí đã gồm VAT phải bằng tổng công nợ được bù. Kiểm các dòng, không tự xóa chênh lệch.')
    d.tong_bu = float(a)
    # Không giải phóng khoá khi huỷ: dùng amend cùng căn cứ, không tạo phiếu thứ hai.
    goc = d.amended_from
    while goc:
        cu = frappe.get_doc(DT,goc)
        if cu.docstatus != 2:
            frappe.throw('Chỉ sửa lại từ phiếu đối soát đã hủy.')
        goc = cu.amended_from
    d.tham_chieu = str(d.tham_chieu or '').strip()
    if not d.tham_chieu:
        frappe.throw('Nhập mã bảng đối soát của sàn.')
    d.khoa = sha256('\n'.join([d.company,d.san,d.diem_ban,d.nha_cung_cap,d.tham_chieu]).encode()).hexdigest()
    if d.amended_from:
        cu = frappe.get_doc(DT,d.amended_from)
        if cu.khoa.split(':')[0] != d.khoa:
            frappe.throw('Phiếu sửa lại phải giữ cùng công ty, sàn, điểm bán, nhà cung cấp và mã đối soát.')
        d.khoa += ':' + d.amended_from
    if d.docstatus == 0:
        d.trang_thai = 'Chờ duyệt đối soát'
        d.but_toan = None
    _doc_nguon(d, khoa=False)


def _doc_nguon(d, khoa=True):
    from vagabond import diem_ban
    ra = []
    for dt, bang, truong, doi_tac, tk in (
        ('Purchase Invoice',d.phi,'supplier',d.nha_cung_cap,'credit_to'),
        ('Sales Invoice',d.ban,'customer',d.khach_hang,'debit_to')):
        if khoa:
            # Khóa nguồn theo thứ tự cố định trước đọc outstanding/chống chạy đồng thời.
            for ma in sorted(x.hoa_don for x in bang):
                frappe.db.sql('select name from `tab%s` where name=%%s for update' % dt, (ma,))
        for x in bang:
            hd = frappe.get_doc(dt,x.hoa_don)
            if hd.company != d.company or hd.get(truong) != doi_tac:
                frappe.throw('Hoá đơn %s khác công ty hoặc pháp nhân đã chọn.' % hd.name)
            if hd.currency != 'VND' or hd.get('is_return'):
                frappe.throw('Hoá đơn %s phải là VND và không phải phiếu trả/điều chỉnh.' % hd.name)
            if dt == 'Sales Invoice':
                if hd.get('vgb_huy') or hd.get('vgb_tam_tinh'):
                    frappe.throw('Hoá đơn %s đã hủy hoặc còn tạm tính, không dùng để cấn trừ.' % hd.name)
                if hd.get('custom_nguon') != d.san or diem_ban.ma_theo_quay(hd.get('vgb_quay')) != d.diem_ban:
                    frappe.throw('Hoá đơn %s khác sàn hoặc điểm bán.' % hd.name)
                if not getdate(d.tu_ngay) <= getdate(hd.posting_date) <= getdate(d.den_ngay):
                    frappe.throw('Hoá đơn %s ngoài kỳ đối soát.' % hd.name)
            elif not hd.get('bill_no'):
                frappe.throw('Hoá đơn phí %s thiếu số hoá đơn nhà cung cấp.' % hd.name)
            # Cả hai bên phải có tài khoản VND hợp lệ, không tạo/đổi COA để lách core.
            tai_khoan = frappe.db.get_value('Account',hd.get(tk),['account_type','account_currency','company'],as_dict=True)
            if not tai_khoan or tai_khoan.company != d.company or tai_khoan.account_currency != 'VND' or tai_khoan.account_type != ('Payable' if dt == 'Purchase Invoice' else 'Receivable'):
                frappe.throw('Tài khoản công nợ của %s chưa đúng loại hoặc tiền VND.' % hd.name)
            ra.append((hd,x,tk))
    return ra


def _doi_trang_thai(d, trang_thai, ly_do='', but_toan=None):
    cap = dict(trang_thai=trang_thai,ly_do=ly_do)
    if but_toan is not None:
        cap['but_toan'] = but_toan
    d.db_set(cap)


def thu_bu(ten):
    frappe.db.sql('select name from `tabVagabond Can Tru San` where name=%s for update',(ten,))
    d = frappe.get_doc(DT,ten)
    if d.docstatus != 1 or not d.xac_nhan:
        return
    if d.but_toan:
        if frappe.db.get_value('Journal Entry',d.but_toan,'docstatus') == 1:
            return d.but_toan
        frappe.throw('Bút toán của %s không còn hiệu lực. Hủy/sửa phiếu đối soát để giữ dấu vết.' % ten)
    nguon = _doc_nguon(d)
    cho = []
    for hd,x,tk in nguon:
        if hd.docstatus != 1:
            cho.append('%s chưa ghi sổ hoặc đã hủy' % hd.name)
        elif hd.doctype == 'Sales Invoice' and not hd.get('custom_hddt_so'):
            cho.append('%s chưa có số MTT' % hd.name)
        elif getdate(hd.posting_date) > getdate(d.ngay_bu):
            cho.append('%s có ngày sau ngày bù' % hd.name)
        elif tien(hd.outstanding_amount) < tien(x.so_tien):
            cho.append('%s còn nợ %s, không đủ bù %s' % (hd.name,hd.outstanding_amount,x.so_tien))
    if cho:
        _doi_trang_thai(d,'Chờ đối soát','; '.join(cho))
        return
    # Hoá đơn cùng NCC/số/ngày không được tự bù hai lần dù là hai PI khác mã.
    for hd,x,tk in nguon:
        if hd.doctype == 'Purchase Invoice':
            trung = frappe.get_all('Purchase Invoice',filters={'supplier':hd.supplier,'company':hd.company,
                'bill_no':hd.bill_no,'bill_date':hd.bill_date,'docstatus':1,'name':['!=',hd.name]},pluck='name')
            if trung:
                _doi_trang_thai(d,'Cần kiểm tra','Hoá đơn phí có số trùng: '+', '.join([hd.name]+trung))
                return
    je = frappe.new_doc('Journal Entry')
    je.update(dict(voucher_type='Journal Entry',company=d.company,posting_date=d.ngay_bu,
        user_remark='Cấn trừ %s / %s / %s - căn cứ %s' % (d.san,d.diem_ban,d.mst,d.name),vgb_can_tru_san=d.name))
    for hd,x,tk in nguon:
        mua = hd.doctype == 'Purchase Invoice'
        je.append('accounts',dict(account=hd.get(tk),party_type='Supplier' if mua else 'Customer',
            party=hd.supplier if mua else hd.customer,reference_type=hd.doctype,reference_name=hd.name,
            debit_in_account_currency=float(x.so_tien) if mua else 0,
            credit_in_account_currency=0 if mua else float(x.so_tien),exchange_rate=1))
    # Không catch lỗi submit để request rollback cả PI/JE, không commit phần dở.
    co_cu = frappe.flags.get('vgb_dang_bu_san')
    try:
        frappe.flags.vgb_dang_bu_san = d.name
        je.insert(ignore_permissions=True)
        je.submit()
    finally:
        frappe.flags.vgb_dang_bu_san = co_cu
    _doi_trang_thai(d,'Đã cấn trừ','',je.name)
    return je.name


def _xep_sau_commit(ten):
    """Không để Redis lỗi sau commit báo ngược thành bill thất bại.

    Frappe background_jobs.enqueue_after_commit thêm callback rồi gọi
    enqueue khi commit. Bọc chính callback, không chỉ lời đăng ký nó.
    Scheduler sẽ tìm lại phiếu chưa có bút toán nếu hàng đợi đang lỗi.
    """
    try:
        frappe.enqueue('vagabond.can_tru_san.xu_ly_nen', ten=ten, queue='short')
    except Exception:
        frappe.logger('can_tru_san', allow_site=True).exception('Không xếp được phiếu %s; scheduler sẽ thử lại', ten)


def khi_ghi_so(doc, method=None):
    from functools import partial
    # Truy vấn nằm trong giao dịch ghi sổ nguồn. Deadlock có thể đã rollback
    # cả giao dịch; không được nuốt rồi báo hóa đơn đã ghi sổ thành công.
    bang = 'Vagabond Can Tru Phi' if doc.doctype == 'Purchase Invoice' else 'Vagabond Can Tru Ban'
    for ten in sorted(set(frappe.get_all(bang,filters={'hoa_don':doc.name,'parenttype':DT},pluck='parent'))):
        frappe.db.after_commit.add(partial(_xep_sau_commit, ten))


def xu_ly_nen(ten):
    """Một phiếu lỗi không chặn bill và không để lại nửa bút toán.

    Khóa phiếu trước savepoint, rollback toàn phần ghi sổ trước khi ghi
    Cần kiểm tra. Giữ hàng đợi callback cũ, bỏ callback của phần đã lùi.
    Lỗi DB phải đi ra worker để Frappe rollback/retry cả giao dịch.
    """
    try:
        frappe.db.sql('select name from `tabVagabond Can Tru San` where name=%s for update', (ten,))
    except (frappe.QueryDeadlockError, frappe.QueryTimeoutError) as e:
        raise frappe.RetryBackgroundJobError(str(e)) from e
    diem = 'can_tru_' + frappe.generate_hash(length=12)
    frappe.db.savepoint(diem)
    hang = {k: list(getattr(frappe.db, k)._functions) for k in
            ('before_commit', 'after_commit', 'before_rollback', 'after_rollback')}
    frappe.db._disable_transaction_control += 1
    try:
        return thu_bu(ten)
    except (frappe.QueryDeadlockError, frappe.QueryTimeoutError) as e:
        # Core f33ac3f execute_job chỉ tự thử lại RetryBackgroundJobError/InternalError.
        # Không rollback savepoint đã mất sau deadlock, để worker rollback toàn giao dịch.
        raise frappe.RetryBackgroundJobError(str(e)) from e
    except (frappe.db.InternalError, frappe.db.OperationalError):
        raise
    except Exception:
        loi = frappe.get_traceback()
        frappe.db.rollback(save_point=diem)
        for k, cu in hang.items():
            getattr(frappe.db, k)._functions.clear()
            getattr(frappe.db, k)._functions.extend(cu)
        d = frappe.get_doc(DT, ten)
        if d.docstatus == 1 and not d.but_toan:
            _doi_trang_thai(d, 'Cần kiểm tra', 'Tự cấn trừ gặp lỗi. Kế toán xem Error Log theo mã phiếu, sửa căn cứ rồi bấm Thử lại.')
        frappe.log_error(title='Cấn trừ sàn ' + ten, message=loi)
    finally:
        frappe.db._disable_transaction_control -= 1


def chan_huy_nguon(doc, method=None):
    bang = 'Vagabond Can Tru Phi' if doc.doctype == 'Purchase Invoice' else 'Vagabond Can Tru Ban'
    for ten in frappe.get_all(bang,filters={'hoa_don':doc.name,'parenttype':DT},pluck='parent'):
        if frappe.db.get_value(DT,ten,'docstatus') == 1:
            frappe.throw('Hủy phiếu đối soát %s trước khi hủy hoá đơn %s để đảo đúng công nợ.' % (ten,doc.name))


def chan_huy_but_toan(doc, method=None):
    if doc.get('vgb_can_tru_san') and frappe.db.get_value(DT,doc.vgb_can_tru_san,'docstatus') == 1:
        frappe.throw('Hủy phiếu đối soát %s để đảo cả bút toán cấn trừ.' % doc.vgb_can_tru_san)


def huy(d):
    # Đọc liên kết đã ghi, không tin payload form cũ khi đảo công nợ.
    d.but_toan = frappe.db.get_value(DT, d.name, 'but_toan')
    if d.but_toan:
        je = frappe.get_doc('Journal Entry',d.but_toan)
        if je.docstatus == 1:
            je.flags.ignore_permissions = True
            je.cancel()
    _doi_trang_thai(d,'Đã hủy','Giữ chứng từ và bút toán đảo để tra cứu.')


@frappe.whitelist()
def thu_lai(ten):
    kiem_quyen_duyet()
    d = frappe.get_doc(DT,ten)
    d.check_permission('write')
    thu_bu(ten)
    return frappe.get_doc(DT,ten).as_dict()


@frappe.whitelist()
def diem_ban():
    if not set(frappe.get_roles()) & {'Accounts User','Accounts Manager','System Manager'}:
        frappe.throw('Chỉ kế toán được đọc danh mục đối soát.')
    from vagabond.diem_ban import ds
    return ds(chi_bat=True)


@frappe.whitelist()
def doi_chieu(ten):
    """Đọc phân bổ PLE theo SI, không suy phân bổ từ GL tổng hợp của PE."""
    d = frappe.get_doc(DT,ten)
    d.check_permission('read')
    # ERPNext de591661 accounts/utils.py QueryPaymentLedger gom amount theo
    # against_voucher_no; GL của PE có thể gộp nhiều SI và mất liên kết từng tờ.
    dong = frappe.db.sql('''select ple.posting_date, ple.voucher_type, ple.voucher_no,
        greatest(ple.amount,0) as debit, greatest(-ple.amount,0) as credit,
        si.vgb_quay, je.vgb_can_tru_san as phieu_bu
        from `tabPayment Ledger Entry` ple
        join `tabSales Invoice` si on ple.against_voucher_type='Sales Invoice'
            and si.name=ple.against_voucher_no
        left join `tabJournal Entry` je on ple.voucher_type='Journal Entry' and je.name=ple.voucher_no
        where ple.company=%s and ple.party_type='Customer' and ple.party=%s
          and ple.account=si.debit_to and ple.delinked=0
          and si.custom_nguon=%s
          and ple.posting_date <= %s''',
        (d.company,d.khach_hang,d.san,d.den_ngay),as_dict=True)
    from vagabond.diem_ban import ma_theo_quay
    dong = [x for x in dong if ma_theo_quay(x.vgb_quay) == d.diem_ban]
    dau = gross = nhan = phi = khac = Decimal(0)
    for x in dong:
        no = tien(x.debit)-tien(x.credit)
        if getdate(x.posting_date) < getdate(d.tu_ngay):
            dau += no
        elif x.voucher_type == 'Sales Invoice':
            gross += no
        elif x.voucher_type == 'Payment Entry':
            nhan -= no
        elif x.phieu_bu:
            phi -= no
        else:
            khac += no
    kq = ket_qua(dau,gross,nhan,phi)
    kq.update(dau_ky=float(dau),doanh_thu=float(gross),da_nhan=float(nhan),phi_da_bu=float(phi),
        dieu_chinh=float(khac),du_cuoi=float(tien(kq['du'])+khac),dong=dong,
        ghi_chu='Số đã phân bổ vào hoá đơn của sàn/điểm bán. Khoản thu chưa phân bổ cần đối chiếu riêng với Merchant và ngân hàng.')
    if khac:
        kq['trang_thai']='Cần kiểm tra điều chỉnh'
    return kq


def kiem_but_toan(doc, method=None):
    if not doc.get('vgb_can_tru_san'):
        return
    d = frappe.get_doc(DT,doc.vgb_can_tru_san)
    if d.docstatus != 1:
        frappe.throw('Phiếu đối soát chưa được duyệt hoặc đã hủy.')
    if d.but_toan and d.but_toan != doc.name:
        frappe.throw('Phiếu đối soát đã có bút toán %s.' % d.but_toan)
    if not d.but_toan and frappe.flags.get('vgb_dang_bu_san') != d.name:
        frappe.throw('Bút toán cấn trừ phải tạo từ phiếu đối soát đã duyệt.')
    if doc.company != d.company or getdate(doc.posting_date) != getdate(d.ngay_bu):
        frappe.throw('Công ty/ngày bút toán khác căn cứ đối soát.')
    mong = []
    for hd,x,tk in _doc_nguon(d,khoa=False):
        mua=hd.doctype=='Purchase Invoice'
        mong.append((hd.doctype,hd.name,hd.get(tk),'Supplier' if mua else 'Customer',
            hd.supplier if mua else hd.customer,tien(x.so_tien) if mua else Decimal(0),Decimal(0) if mua else tien(x.so_tien)))
    that=[(x.reference_type,x.reference_name,x.account,x.party_type,x.party,
        tien(x.debit_in_account_currency or 0),tien(x.credit_in_account_currency or 0)) for x in doc.accounts]
    if sorted(mong) != sorted(that):
        frappe.throw('Dòng bút toán khác căn cứ. Hủy/sửa phiếu đối soát thay vì sửa riêng bút toán.')


def xep_hang_cho():
    """Nguồn MTT có thể cập nhật bằng db_set nên không phát sự kiện Document.

    Mỗi phiếu là một job/giao dịch riêng: lỗi một phiếu không commit phần
    dở hoặc giữ cả danh sách đứng lại. Khóa DB trong thu_bu chống job trùng.
    """
    for ten in frappe.get_all(DT,filters={'docstatus':1,'but_toan':['is','not set'],
                                     'trang_thai':['in',['Chờ duyệt đối soát','Chờ đối soát']]},
                             pluck='name',limit_page_length=0):
        from functools import partial
        frappe.db.after_commit.add(partial(_xep_sau_commit, ten))
