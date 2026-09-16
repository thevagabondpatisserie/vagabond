"""PR336: workflow Frappe thật trên bench dùng một lần, không production.

DDL của Workflow/Custom Field chạy trước fixture và savepoint. Sau phép thử
lùi toàn bộ chứng từ, tắt workflow thử để không ảnh hưởng bộ browser phía sau.
"""
import json
import os
import traceback
from pathlib import Path
from unittest.mock import patch
import frappe
from frappe.utils import today
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def chay():
    _mo()
    ten_w = 'CI workflow tra truoc 336'
    kq = {'dat': False}
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        from vagabond import tra_truoc as tt
        from vagabond.khung.kiem_that.nen import cong_ty, mot_nha_cung_cap
        from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _mon_dich_vu, _tk_ngan_hang
        create_custom_fields({'Payment Entry': [{'fieldname': 'workflow_state', 'fieldtype': 'Link',
            'options': 'Workflow State', 'label': 'Workflow State', 'insert_after': 'naming_series'}]})
        for dt, field, names in [('Role','role_name',['AP Officer','AP Kiểm soát (FIN)']),
                ('Workflow State','workflow_state_name',[tt.TT_NHAP,tt.TT_CHO_FIN]),
                ('Workflow Action Master','workflow_action_name',[tt.NUT_GUI])]:
            for ten in names:
                if not frappe.db.exists(dt,ten):
                    frappe.get_doc({'doctype':dt,field:ten}).insert(ignore_permissions=True)
        w=frappe.get_doc({'doctype':'Workflow','workflow_name':ten_w,'document_type':'Payment Entry',
            'is_active':1,'send_email_alert':0,'workflow_state_field':'workflow_state',
            'states':[{'state':tt.TT_NHAP,'doc_status':'0','allow_edit':'AP Officer'},
                {'state':tt.TT_CHO_FIN,'doc_status':'0','allow_edit':'AP Kiểm soát (FIN)'}],
            'transitions':[{'state':tt.TT_NHAP,'action':tt.NUT_GUI,'next_state':tt.TT_CHO_FIN,
                'allowed':'AP Officer','allow_self_approval':1}]})
        w.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.clear_cache()
        frappe.db.savepoint('fixture336')
        cty=cong_ty()
        po=frappe.get_doc({'doctype':'Purchase Order','company':cty,'supplier':mot_nha_cung_cap(),
            'transaction_date':today(),'schedule_date':today(),'currency':'VND','conversion_rate':1,
            'items':[{'item_code':_mon_dich_vu(),'qty':1,'rate':336000,'schedule_date':today()}]})
        po.insert(ignore_permissions=True);po.submit()
        ba=_tk_ngan_hang(cty)
        nguoi=[]
        for so,vai in enumerate((['Accounts User','Purchase User','AP Officer'],['Accounts User','Purchase User'])):
            u=frappe.get_doc({'doctype':'User','email':'ci336-%s@example.test'%so,'first_name':'CI336',
                'enabled':1,'send_welcome_email':0,'roles':[{'role':v} for v in vai]})
            u.insert(ignore_permissions=True);nguoi.append(u.name)
        def lap(user):
            frappe.set_user(user)
            f=frappe.get_doc({'doctype':'File','file_name':'bao-gia-ci336.txt',
                'content':'Chung tu thu CI336','is_private':1}).insert(ignore_permissions=True)
            r=tt.tao_phieu(don=po.name,so_tien=33600,nguon_tien=ba,
                loai_chung_tu='Bảng báo giá',tep=[{'ma':f.name}])
            p=frappe.get_doc('Payment Entry',r['phieu'])
            _dung(p.docstatus==0,'Không ghi sổ hoặc chi tiền')
            _dung(not frappe.db.exists('GL Entry',{'voucher_type':p.doctype,'voucher_no':p.name}),'Không sinh GL')
            _dung(frappe.db.get_value('File',f.name,'attached_to_name')==p.name,'Tệp vẫn gắn đúng phiếu')
            _dung(r['trang_thai']==p.workflow_state,'Thông báo khớp DB')
            return r,p
        r,p=lap(nguoi[0]);_dung(r['da_gui']==1 and p.workflow_state==tt.TT_CHO_FIN,'AP Officer gửi thành công')
        kq['ap_officer_gui']=True
        r,p=lap(nguoi[1]);_dung(r['da_gui']==0 and p.workflow_state==tt.TT_NHAP,'Người thiếu vai giữ Nháp')
        _dung(frappe.db.exists('ToDo',{'reference_type':'Payment Entry','reference_name':p.name,'allocated_to':nguoi[0]}),'Nháp giao đúng AP Officer')
        kq['nhap_giao_dung_vai']=True
        frappe.set_user(nguoi[0])
        from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
        luu=PaymentEntry.save
        def hong_sau_luu(doc,*a,**kw):
            ket=luu(doc,*a,**kw)
            if doc.name==p.name and doc.workflow_state==tt.TT_CHO_FIN:
                raise frappe.ValidationError('CI336 sau khi DB đã đổi trạng thái')
            return ket
        with patch.object(PaymentEntry,'save',hong_sau_luu):
            buoc,loi=tt._gui_kiem_tra(p)
        p.reload();_dung(buoc==tt.TT_NHAP and p.workflow_state==tt.TT_NHAP,'Rollback bước lưu dở')
        _dung(bool(loi),'Báo rõ chưa gửi')
        kq.update(dat=True,rollback_sau_luu=True)
    except Exception:
        kq['loi']=traceback.format_exc()
    finally:
        frappe.db.rollback()
        if frappe.db.exists('Workflow',ten_w):
            frappe.db.set_value('Workflow',ten_w,'is_active',0)
            frappe.db.commit()
            frappe.clear_cache()
        (Path(os.environ['VGB_ARTIFACTS'])/'tra-truoc-336.json').write_text(json.dumps(kq,ensure_ascii=False,indent=2))
        _dong()
    print(json.dumps(kq,ensure_ascii=False),flush=True)
    return kq['dat']


if __name__=='__main__':
    raise SystemExit(0 if chay() else 1)
