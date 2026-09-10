"""#262: PI/SI và JE thật, đọc GL/Payment Ledger rồi hủy và thử lại."""
import frappe
from frappe.utils import today
from vagabond import can_tru_san as ct
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
    so=frappe.get_doc(dict(doctype=ct.DT,company=cong_ty,san='GrabFood',diem_ban=si.vgb_quay or 'SALES',
        khach_hang=si.customer,nha_cung_cap=ncc.name,tu_ngay=today(),den_ngay=today(),ngay_bu=today(),
        tham_chieu='KIEM262-'+frappe.generate_hash(length=8),can_cu='/private/files/doi-soat-kiem-262.pdf',xac_nhan=1,
        phi=[dict(hoa_don=pi.name,so_tien=200000)],ban=[dict(hoa_don=si.name,so_tien=200000)]))
    so.insert(ignore_permissions=True); _DA_TAO.append((so.doctype,so.name))
    return so,pi,si


@ca('#262 bu tu dong: GL dung tung ben, outstanding, retry va huy dao')
def _bu():
    so,pi,si=_phieu()
    so.submit(); so.reload()
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
    ct.khi_ghi_so(si); so.reload()
    dung('có JE sau đủ căn cứ',bool(so.but_toan))
    _DA_TAO.append(('Journal Entry',so.but_toan))
