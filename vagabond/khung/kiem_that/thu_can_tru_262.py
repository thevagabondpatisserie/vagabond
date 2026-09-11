"""#262: PI/SI và JE thật, đọc GL/Payment Ledger rồi hủy và thử lại."""
import frappe
from unittest.mock import patch
from frappe.utils import today
from vagabond import can_tru_san as ct
from vagabond import diem_ban as dban
from vagabond.khung.kiem_that.nen import ca,la,dung,_DA_TAO
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen,_mon,_app


def _phieu():
    cong_ty,tk,mau=_nen()
    ncc=frappe.get_doc(dict(doctype='Supplier',supplier_name='NCC kiểm 262 '+frappe.generate_hash(length=8),
        supplier_group=frappe.db.get_value('Supplier Group',{'is_group':0},'name'),supplier_type='Company',tax_id='KIEM262'))
    ncc.insert(ignore_permissions=True); _DA_TAO.append((ncc.doctype,ncc.name))
    pi=_hoa_don_mua(200000,ncc.name)
    si=_app(cong_ty,[dict(item_code=_mon(tk),qty=1,rate=1000000)])
    si.vgb_tam_tinh=0
    si.vgb_pt_thanh_toan='GrabFood'
    si.vgb_ma_tham_chieu='KT262-'+frappe.generate_hash(length=8)
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
def _thu_tien_phan_bo():
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
    pe.paid_amount = pe.received_amount = 600000
    pe.reference_no = 'KT265-THU'
    pe.reference_date = today()
    pe.insert(ignore_permissions=True); _DA_TAO.append((pe.doctype,pe.name))
    pe.submit(); pe.reload(); si.reload(); si2.reload()
    la('SI thứ nhất giảm nợ', si.outstanding_amount, 700000)
    la('SI thứ hai giảm nợ', si2.outstanding_amount, 700000)
    kq = ct.doi_chieu(so.name)
    la('nhận đủ phân bổ hai SI', kq['da_nhan'], 600000)
    la('dư còn đúng hai SI', kq['du_cuoi'], 1400000)
    pe.cancel(); si.reload(); si2.reload()
    kq = ct.doi_chieu(so.name)
    la('hủy PE không còn tiền nhận', kq['da_nhan'], 0)
    la('hủy PE khôi phục dư', kq['du_cuoi'], 2000000)


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
