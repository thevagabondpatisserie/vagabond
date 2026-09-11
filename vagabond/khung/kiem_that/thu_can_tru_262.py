"""#262: PI/SI và JE thật, đọc GL/Payment Ledger rồi hủy và thử lại."""
import frappe
from unittest.mock import patch
from frappe.utils import today
from vagabond import can_tru_san as ct
from vagabond import diem_ban as dban
from vagabond.khung.kiem_that.nen import ca,la,dung,_DA_TAO
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen,_mon,_app


def _phieu(tien_pos=0):
    cong_ty,tk,mau=_nen()
    ncc=frappe.get_doc(dict(doctype='Supplier',supplier_name='NCC kiểm 262 '+frappe.generate_hash(length=8),
        supplier_group=frappe.db.get_value('Supplier Group',{'is_group':0},'name'),supplier_type='Company',tax_id='KIEM262'))
    ncc.insert(ignore_permissions=True); _DA_TAO.append((ncc.doctype,ncc.name))
    pi=_hoa_don_mua(200000,ncc.name)
    si=_app(cong_ty,[dict(item_code=_mon(tk),qty=1,rate=1000000)])
    si.vgb_tam_tinh=0
    si.vgb_pt_thanh_toan='GrabFood'
    si.vgb_ma_tham_chieu='KT262-'+frappe.generate_hash(length=8)
    if tien_pos:
        from vagabond.khung.kiem_that.nen import _mot
        tk_tien = _mot('Account', {'company':cong_ty,'account_type':'Cash','is_group':0})
        mop = frappe.get_doc(dict(doctype='Mode of Payment',mode_of_payment='KT265-'+frappe.generate_hash(length=8),
            type='Cash',accounts=[dict(company=cong_ty,default_account=tk_tien)]))
        mop.insert(ignore_permissions=True); _DA_TAO.append((mop.doctype,mop.name))
        si.is_pos = 1
        si.set('payments',[dict(mode_of_payment=mop.name,account=tk_tien,amount=tien_pos)])
    si.save(ignore_permissions=True)
    si.submit(); si.reload()
    # Chỉ dấu số MTT trong fixture, không gọi dịch vụ phát hành bên ngoài.
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','KIEM-262')
    so=frappe.get_doc(dict(doctype=ct.DT,company=cong_ty,san='GrabFood',diem_ban=dban.ma_theo_quay(si.vgb_quay),
        khach_hang=si.customer,nha_cung_cap=ncc.name,tu_ngay=today(),den_ngay=today(),ngay_bu=today(),
        tham_chieu='KIEM262-'+frappe.generate_hash(length=8),can_cu='/private/files/doi-soat-kiem-262.pdf',xac_nhan=1,
        phi=[dict(hoa_don=pi.name,so_tien=200000)],ban=[dict(hoa_don=si.name,so_tien=200000)]))
    so.insert(ignore_permissions=True); _DA_TAO.append((so.doctype,so.name))
    return so,pi,si


@ca('#262 bu tu dong: GL dung tung ben, outstanding, retry va huy dao')
def _bu():
    so,pi,si=_phieu()
    so.submit()
    la('form sau duyệt đồng bộ trạng thái', so.trang_thai, 'Đã cấn trừ')
    dung('tự tạo JE',bool(so.but_toan))
    _DA_TAO.append(('Journal Entry',so.but_toan))
    je=frappe.get_doc('Journal Entry',so.but_toan)
    la('JE ghi sổ',je.docstatus,1)
    pi.reload(); si.reload()
    la('331 hết nợ',pi.outstanding_amount,0)
    la('131 còn lại',si.outstanding_amount,800000)
    gl=frappe.get_all('GL Entry',filters={'voucher_type':'Journal Entry','voucher_no':je.name,'is_cancelled':0},
        fields=['account','party_type','party','debit','credit','against_voucher'])
    la('đúng hai tài khoản và tiền',sorted((x.account,x.party_type,x.party,float(x.debit),float(x.credit),x.against_voucher) for x in gl),
        sorted([(pi.credit_to,'Supplier',pi.supplier,200000.0,0.0,pi.name),(si.debit_to,'Customer',si.customer,0.0,200000.0,si.name)]))
    la('retry cùng JE',ct.thu_bu(so.name),je.name)
    la('chỉ một JE',frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name,'docstatus':1}),1)
    try: ct.chan_huy_nguon(pi)
    except frappe.ValidationError as e: dung('chỉ rõ phiếu',so.name in str(e))
    else: dung('phải chặn hủy nguồn',False)
    so.cancel(); pi.reload(); si.reload(); je.reload()
    la('form sau hủy đồng bộ trạng thái',so.trang_thai,'Đã hủy')
    la('JE đảo',je.docstatus,2)
    la('331 hồi lại',pi.outstanding_amount,200000)
    la('131 hồi lại',si.outstanding_amount,1000000)


@ca('#262 thieu MTT giu cho; sau cap nhat so MTT moi tu bu')
def _cho():
    so,pi,si=_phieu()
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','')
    so.submit(); so.reload()
    la('chưa đủ căn cứ',so.trang_thai,'Chờ đối soát')
    dung('không tạo JE',not so.but_toan)
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','KIEM-262')
    cu = len(frappe.db.after_commit._functions)
    ct.khi_ghi_so(si); so.reload()
    dung('hook chỉ xếp sau commit', len(frappe.db.after_commit._functions) > cu)
    dung('hook không ghi JE trong bill', not so.but_toan)
    ct.xu_ly_nen(so.name); so.reload()
    dung('có JE sau đủ căn cứ',bool(so.but_toan))
    _DA_TAO.append(('Journal Entry',so.but_toan))


@ca('#262 lỗi sau submit JE: rollback GL và nợ, ghi cần kiểm tra, thử lại được')
def _loi_giua():
    so, pi, si = _phieu()
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','')
    so.submit()
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','KIEM-262')
    goc = ct._doi_trang_thai
    def loi(d, trang_thai, *args, **kwargs):
        if trang_thai == 'Đã cấn trừ':
            raise ValueError('Lỗi thử sau JE submit trước gắn phiếu')
        return goc(d, trang_thai, *args, **kwargs)
    with patch.object(ct, '_doi_trang_thai', loi):
        ct.xu_ly_nen(so.name)
    so.reload(); pi.reload(); si.reload()
    la('kế toán thấy lỗi',so.trang_thai,'Cần kiểm tra')
    la('không còn JE dở',frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name}),0)
    la('331 chưa bị cấn',pi.outstanding_amount,200000)
    la('131 chưa bị cấn',si.outstanding_amount,1000000)
    ct.xu_ly_nen(so.name); so.reload()
    dung('thử lại sinh đúng JE',bool(so.but_toan))
    _DA_TAO.append(('Journal Entry',so.but_toan))
    la('một JE',frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name}),1)


@ca('#262 Redis lỗi sau commit không báo bill thất bại, scheduler còn đường thử lại')
def _loi_hang():
    with patch.object(frappe, 'enqueue', side_effect=RuntimeError('Redis thử bị ngắt')):
        ct._xep_sau_commit('KIEM262-HANG')


@ca('#262 báo cáo dùng mã điểm bán khác mã quầy, đọc GL thật')
def _bao_cao_diem():
    so, pi, si = _phieu()
    so.submit()
    _DA_TAO.append(('Journal Entry',so.but_toan))
    ma = 'DIEM-KIEM-262'
    frappe.db.set_value(ct.DT,so.name,'diem_ban',ma)
    # Chỉ giả lập danh mục điểm bán; SI/JE/GL và cửa báo cáo chạy thật.
    with patch.object(dban,'ds',return_value=[dict(ma=ma,quay=str(si.vgb_quay or '').strip().upper())]):
        kq = ct.doi_chieu(so.name)
    la('doanh thu điểm đã ánh xạ',kq['doanh_thu'],1000000)
    la('phí đã bù đúng điểm',kq['phi_da_bu'],200000)
    la('dư cuối đúng GL',kq['du_cuoi'],800000)
    dung('có dòng GL',bool(kq['dong']))


@ca('#262 lỗi khóa đi ra worker bằng RetryBackgroundJobError, không đóng dấu nghiệp vụ')
def _loi_khoa_worker():
    so, pi, si = _phieu()
    frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','')
    so.submit()
    cu = so.trang_thai
    for loai in (frappe.QueryDeadlockError,frappe.QueryTimeoutError):
        with patch.object(ct,'thu_bu',side_effect=loai('khóa thử')):
            try:
                ct.xu_ly_nen(so.name)
            except frappe.RetryBackgroundJobError as e:
                dung('giữ nguyên nguyên nhân',isinstance(e.__cause__,loai))
            else:
                dung('worker phải nhận lỗi retry',False)
        so.reload()
        la('không đổi thành lỗi nghiệp vụ',so.trang_thai,cu)
        la('không tạo JE',frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name}),0)
    # Đây chỉ kiểm ánh xạ exception, không thay hai kết nối DB thật.


@ca('#265 báo cáo nhận tiền PE phân bổ hai SI và hủy trả lại dư')
def _thu_tien_phan_bo(phan_bo_sau=False):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    from vagabond.khung.kiem_that.nen import _mot
    so, pi, si = _phieu()
    so2, pi2, si2 = _phieu()
    la('hai SI cùng khách', si2.customer, si.customer)
    tk = _mot('Account', {'company': so.company, 'account_type': 'Bank', 'is_group': 0})
    dung('có tài khoản ngân hàng thử', bool(tk))
    pe = get_payment_entry('Sales Invoice', si.name, party_amount=600000, bank_account=tk)
    pe.references[0].allocated_amount = 300000
    pe.append('references', dict(reference_doctype='Sales Invoice', reference_name=si2.name,
        total_amount=si2.grand_total, outstanding_amount=si2.outstanding_amount, allocated_amount=300000))
    if phan_bo_sau:
        pe.set('references', [])
    pe.paid_amount = pe.received_amount = 600000
    pe.reference_no = 'KT265-THU'
    pe.reference_date = today()
    pe.insert(ignore_permissions=True); _DA_TAO.append((pe.doctype,pe.name))
    tep = frappe.get_doc(dict(doctype='File', file_name='KT265-bao-co.txt',
        content='Giay bao Co thu tren bench', is_private=1,
        attached_to_doctype=pe.doctype, attached_to_name=pe.name))
    # Savepoint không chạy after_rollback watchers của File (Frappe f33ac3f).
    # Tệp thử có nội dung riêng, dọn qua File ngay cả khi submit ném lỗi.
    tep.content += frappe.generate_hash(length=16)
    try:
        tep.insert(ignore_permissions=True); _DA_TAO.append((tep.doctype,tep.name))
        pe.submit()
    finally:
        if tep.name and frappe.db.exists('File',tep.name):
            from pathlib import Path
            duong = Path(tep.get_full_path())
            tep.delete(ignore_permissions=True)
            dung('tệp báo Có thử đã dọn trên đĩa',not duong.exists())
        elif tep.flags.new_file:
            tep.on_rollback()
    pe.reload(); si.reload(); si2.reload()
    if phan_bo_sau:
        la('thu trước còn nguyên khả dụng', pe.unallocated_amount, 600000)
        rec = frappe.new_doc('Payment Reconciliation')
        rec.company, rec.party_type, rec.party = so.company, 'Customer', si.customer
        rec.receivable_payable_account = si.debit_to
        rec.invoice_limit = rec.payment_limit = 0
        rec.get_unreconciled_entries()
        hoa_don = [x.as_dict() for x in rec.invoices if x.invoice_number in (si.name, si2.name)]
        khoan_thu = [x.as_dict() for x in rec.payments if x.reference_name == pe.name]
        la('lấy đủ hai SI đích', len(hoa_don), 2)
        la('lấy đúng một PE', len(khoan_thu), 1)
        for x in hoa_don:
            x['outstanding_amount'] = 300000
        rec.allocate_entries(dict(invoices=hoa_don, payments=khoan_thu))
        rec.reconcile()
        pe.reload(); si.reload(); si2.reload()
        la('phân bổ hết khoản thu', pe.unallocated_amount, 0)
        # Core utils.reconcile_against_document cập nhật PLE, giữ GL đã ghi.
        # Join GL cũ vì vậy bỏ rơi khoản này dù SI đã giảm nợ thật.
        gl_cu = frappe.db.sql('''select coalesce(sum(credit-debit),0)
            from `tabGL Entry` where voucher_type='Payment Entry' and voucher_no=%s
            and against_voucher_type='Sales Invoice' and against_voucher in %s
            and is_cancelled=0''', (pe.name, (si.name, si2.name)))[0][0]
        la('tái hiện GL cũ không thấy phân bổ sau', gl_cu, 0)
    la('SI thứ nhất giảm nợ', si.outstanding_amount, 700000)
    la('SI thứ hai giảm nợ', si2.outstanding_amount, 700000)
    kq = ct.doi_chieu(so.name)
    la('nhận đủ phân bổ hai SI', kq['da_nhan'], 600000)
    la('dư còn đúng hai SI', kq['du_cuoi'], 1400000)
    pe.cancel(); si.reload(); si2.reload()
    kq = ct.doi_chieu(so.name)
    la('hủy PE không còn tiền nhận', kq['da_nhan'], 0)
    la('hủy PE khôi phục dư', kq['du_cuoi'], 2000000)


@ca('#265 thu trước rồi đối chiếu hai SI: GL cũ bỏ sót, PLE đúng')
def _thu_truoc_doi_chieu_sau():
    _thu_tien_phan_bo(phan_bo_sau=True)


@ca('#265 trả hàng nằm ở điều chỉnh, không làm mất gross hóa đơn gốc')
def _bao_cao_tra_hang():
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    so, pi, si = _phieu()
    tra = make_sales_return(si.name)
    # Phiếu trả thử nối bằng return_against, không giả làm lần nhập lại
    # cùng mã đơn Pancake (mapper lõi sao chép cả custom field của fixture).
    tra.custom_pancake_order_id = None
    tra.custom_pancake_display_id = None
    tra.update_outstanding_for_self = 0
    tra.items[0].qty = -0.2
    tra.vgb_ma_tham_chieu = 'KT265-TRA-'+frappe.generate_hash(length=8)
    tra.insert(ignore_permissions=True); _DA_TAO.append((tra.doctype,tra.name))
    tra.submit(); tra.reload(); si.reload()
    la('phiếu trả ghi thật 200000',tra.grand_total,-200000)
    la('SI còn nợ 800000',si.outstanding_amount,800000)
    kq = ct.doi_chieu(so.name)
    la('giữ gross gốc',kq['doanh_thu'],1000000)
    la('tách trả hàng khỏi gross',kq['dieu_chinh'],-200000)
    la('dư khớp core',kq['du_cuoi'],si.outstanding_amount)
    tra.cancel(); si.reload()
    kq = ct.doi_chieu(so.name)
    la('hủy trả hàng giữ gross',kq['doanh_thu'],1000000)
    la('hủy trả hàng hết điều chỉnh',kq['dieu_chinh'],0)
    la('hủy trả hàng hồi đủ dư',kq['du_cuoi'],1000000)


@ca('#265 thu trên SI tách khỏi gross và chỉ rõ dư hóa đơn hủy mềm')
def _bao_cao_thu_pos():
    so, pi, si = _phieu(tien_pos=300000)
    la('POS thật còn nợ',si.outstanding_amount,700000)
    kq = ct.doi_chieu(so.name)
    la('gross không trừ POS',kq['doanh_thu'],1000000)
    la('thu ngay trên SI ở điều chỉnh',kq['dieu_chinh'],-300000)
    la('dư POS khớp core',kq['du_cuoi'],700000)
    # Dựng dấu hủy mềm lịch sử trong fixture; không loại khoản còn ở sổ 131.
    frappe.db.set_value('Sales Invoice',si.name,'vgb_huy',1)
    kq = ct.doi_chieu(so.name)
    la('dư hủy mềm được chỉ riêng',kq['du_huy_mem'],700000)
    la('không làm mất công nợ thật',kq['du_cuoi'],700000)
    la('không khẳng định sàn sẽ trả',kq['trang_thai'],'Cần kiểm tra điều chỉnh')


@ca('#265 hook nguồn trả nguyên lỗi DB cho caller rollback')
def _hook_db():
    so, pi, si = _phieu()
    for loai in (frappe.QueryDeadlockError, frappe.QueryTimeoutError):
        loi = loai('KT265 truy vấn nguồn lỗi')
        with patch.object(ct.frappe, 'get_all', side_effect=loi):
            try:
                ct.khi_ghi_so(si)
            except loai as e:
                dung('không đổi hoặc nuốt lỗi DB', e is loi)
            else:
                dung('hook phải ném lỗi DB', False)
