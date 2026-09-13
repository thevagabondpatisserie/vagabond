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
    n.db_set('email_cc','bon@email-nha-cung-cap.example.com; phu@email-nha-cung-cap.example.com')
    c=frappe.get_doc({'doctype':'Contact','first_name':'KTTHU','email_ids':[{'email_id':'chinh@email-nha-cung-cap.example.com','is_primary':1},{'email_id':'phu@email-nha-cung-cap.example.com'},{'email_id':'ba@email-nha-cung-cap.example.com'}], 'links':[{'link_doctype':'Supplier','link_name':n.name}]})
    c.insert(ignore_permissions=True);_DA_TAO.append(('Contact',c.name))
    h.db_set('nha_cung_cap',n.name);h.db_set('email_ncc','chinh@email-nha-cung-cap.example.com; phu@email-nha-cung-cap.example.com')
    return h


@ca('#298 gửi NCC đủ To/CC, bản sao riêng và retry không tạo thêm thư')
def gui_du():
    from frappe.email.doctype.email_queue.email_queue import QueueBuilder,EmailQueue
    h=nen_thu()
    with patch.object(QueueBuilder,'get_outgoing_email_account',return_value=frappe.get_doc({'doctype':'Email Account','email_id':'fixture@example.com'})),patch.object(EmailQueue,'send',side_effect=AssertionError('Cấm SMTP trong bench')):
        k=hs.gui_email_ncc(h.name)
        la('xếp hàng',k['xep_hang'],1)
        h.reload();dung('lưu đủ người nhận quá 140 ký tự',len(h.email_gui_toi)>140)
        rows=frappe.get_all('Email Queue',filters={'reference_name':h.name},fields=['name','message','message_id'])
        la('hai thư',len(rows),2)
        for r in rows:
            _DA_TAO.append(('Email Queue',r.name))
            m=message_from_string(r.message)
            ds={x[1] for x in getaddresses(m.get_all('To',[])+m.get_all('Cc',[]))}
            if r.message_id==thu_ncc.ma_thu(h.name,'ncc'):
                la('đủ bốn email NCC',ds,{'chinh@email-nha-cung-cap.example.com','phu@email-nha-cung-cap.example.com','ba@email-nha-cung-cap.example.com','bon@email-nha-cung-cap.example.com'})
                la('ba CC',len(getaddresses(m.get_all('Cc',[]))),3)
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
    with patch.object(QueueBuilder,'get_outgoing_email_account',return_value=frappe.get_doc({'doctype':'Email Account','email_id':'fixture@example.com'})),patch.object(EmailQueue,'send',side_effect=AssertionError('Cấm SMTP')):
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


@ca('#298 email CC sai không khóa hồ sơ; gửi thật chặn, xem thử không cần UNC')
def email_sai():
    from frappe.email.doctype.email_queue.email_queue import QueueBuilder,EmailQueue
    h=nen_thu();frappe.db.set_value('Supplier',h.nha_cung_cap,'email_cc','ketoan@abc')
    dung('đọc nguồn không ném',bool(thu_ncc.nguon_email_ncc(h.nha_cung_cap)))
    hs._email_ncc(h.nha_cung_cap)
    hs.chi_tiet(h.name)
    with patch.object(frappe,'log_error') as log:
        cu=list(frappe.local.message_log or [])
        k=hs._tu_gui_thu_bao(h)
        la('gửi thật bị chặn',k['gui'],0);dung('nói địa chỉ sai','Email không hợp lệ' in k['vi_sao'])
        la('không traceback kỳ vọng',log.call_count,0)
        la('không thừa popup',frappe.local.message_log,cu)
    with patch('vagabond.tra_tien_app.ds_unc_tho',return_value=[]),patch.object(QueueBuilder,'get_outgoing_email_account',return_value=frappe.get_doc({'doctype':'Email Account','email_id':'fixture@example.com'})),patch.object(EmailQueue,'send',side_effect=AssertionError('Cấm SMTP')):
        k=hs.gui_email_ncc(h.name,gui_that=0)
        dung('xem được khi chưa UNC','BẢN XEM THỬ' in k['html'])
        hs.gui_email_ncc(h.name,email='thu@example.com',thu_nghiem=1)
        ds=frappe.get_all('Email Queue',filters={'reference_name':h.name},pluck='name')
        la('một thư thử không UNC',len(ds),1)
        _DA_TAO.extend(('Email Queue',n) for n in ds)
