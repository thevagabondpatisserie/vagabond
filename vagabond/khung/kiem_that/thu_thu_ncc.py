"""#298 thư NCC: Queue/MIME thật, không kết nối SMTP hoặc gửi tới người thật."""
from unittest.mock import patch
from email import message_from_string
from email.utils import getaddresses
import frappe
from vagabond import ho_so_tt as hs, thu_ncc
from vagabond.khung.kiem_that.nen import ca,la,dung,_DA_TAO
from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _nen,_ghi


def nen_thu():
    h,g=_nen();_ghi(h,g);h.reload()
    n=frappe.get_doc({'doctype':'Supplier','supplier_name':'KTTHU-'+frappe.generate_hash(length=10),'supplier_type':'Company'})
    n.insert(ignore_permissions=True);_DA_TAO.append(('Supplier',n.name))
    c=frappe.get_doc({'doctype':'Contact','first_name':'KTTHU','email_ids':[{'email_id':'chinh@example.com','is_primary':1},{'email_id':'phu@example.com'},{'email_id':'ba@example.com'}], 'links':[{'link_doctype':'Supplier','link_name':n.name}]})
    c.insert(ignore_permissions=True);_DA_TAO.append(('Contact',c.name))
    h.db_set('nha_cung_cap',n.name);h.db_set('email_ncc','chinh@example.com; phu@example.com')
    return h


@ca('#298 gửi NCC đủ To/CC, bản sao riêng và retry không tạo thêm thư')
def gui_du():
    from frappe.email.doctype.email_queue.email_queue import QueueBuilder,EmailQueue
    h=nen_thu()
    with patch.object(QueueBuilder,'get_outgoing_email_account',return_value=None),patch.object(EmailQueue,'send',side_effect=AssertionError('Cấm SMTP trong bench')):
        k=hs.gui_email_ncc(h.name)
        la('xếp hàng',k['xep_hang'],1)
        rows=frappe.get_all('Email Queue',filters={'reference_name':h.name},fields=['name','message','message_id'])
        la('hai thư',len(rows),2)
        for r in rows:
            _DA_TAO.append(('Email Queue',r.name))
            m=message_from_string(r.message)
            ds={x[1] for x in getaddresses(m.get_all('To',[])+m.get_all('Cc',[]))}
            if r.message_id==thu_ncc.ma_thu(h.name,'ncc'):
                la('đủ ba email NCC',ds,{'chinh@example.com','phu@example.com','ba@example.com'})
                la('hai CC',len(getaddresses(m.get_all('Cc',[]))),2)
            else:la('kế toán riêng',ds,{hs.EMAIL_KE_TOAN})
            tep=[p for p in m.walk() if p.get_filename()]
            dung('có UNC thật trong MIME',len(tep)>0)
            dung('tên UNC nhận diện',all(p.get_filename().startswith('UNC-'+h.name+'-') for p in tep))
        hs.gui_email_ncc(h.name)
        la('retry không thêm',frappe.db.count('Email Queue',{'reference_name':h.name}),2)
        la('đủ bằng chứng',len(thu_ncc.bang_chung(h.name)),2)


@ca('#298 lỗi tạo bản sao rollback cả thư NCC; thử chỉ một địa chỉ và không dấu thật')
def loi_va_thu():
    from frappe.email.doctype.email_queue.email_queue import QueueBuilder,EmailQueue
    h=nen_thu();goc=frappe.sendmail;lan=[]
    def gui(**kw):
        lan.append(1)
        if len(lan)==2:raise RuntimeError('Lỗi bản sao fixture')
        return goc(**kw)
    with patch.object(QueueBuilder,'get_outgoing_email_account',return_value=None),patch.object(EmailQueue,'send',side_effect=AssertionError('Cấm SMTP')):
        with patch.object(frappe,'sendmail',side_effect=gui):
            try:hs.gui_email_ncc(h.name)
            except RuntimeError:pass
            else:dung('phải báo lỗi',False)
        la('không thư dở',frappe.db.count('Email Queue',{'reference_name':h.name}),0)
        h.reload();la('chưa dấu thật',h.email_da_gui,0)
        hs.gui_email_ncc(h.name,email='thu@example.com',thu_nghiem=1)
        ds=frappe.get_all('Email Queue',filters={'reference_name':h.name},fields=['name','message'])
        la('một thư thử',len(ds),1)
        for r in ds:
            _DA_TAO.append(('Email Queue',r.name));m=message_from_string(r.message)
            la('chỉ địa chỉ thử',{x[1] for x in getaddresses(m.get_all('To',[])+m.get_all('Cc',[]))},{'thu@example.com'})
        la('thư thử không là bằng chứng thật',thu_ncc.bang_chung(h.name),[])
        h.reload();la('không đánh dấu',h.email_da_gui,0)
