"""Thư NCC: trước đây chỉ lấy email đầu tiên nên bỏ sót các liên hệ đã khai.

Gom địa chỉ đúng nhà cung cấp, bỏ trùng và tách bản sao kế toán. Không gửi
SMTP ở đây; hàng đợi lõi giữ trạng thái từng người nhận sau khi commit.
"""
import re
import hashlib
from email.utils import getaddresses


def tach_email(*nguon):
    ra=[]
    for chuoi in nguon:
        if not str(chuoi or '').strip():
            continue
        for _, dia_chi in getaddresses([str(chuoi or '').replace(';', ',').replace('\n', ',')]):
            dia_chi=dia_chi.strip().lower()
            if not dia_chi:
                raise ValueError('Email không hợp lệ. Sửa email nhà cung cấp rồi gửi lại.')
            if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+",dia_chi):
                raise ValueError('Email không hợp lệ: %s. Sửa email nhà cung cấp rồi gửi lại.' % dia_chi)
            if dia_chi not in ra:
                ra.append(dia_chi)
    return ra


def ma_thu(name,loai):
    return 'vgb-app-%s-%s@thevagabondpatisserie.com' % (hashlib.sha256(name.encode()).hexdigest()[:32],loai)


def ten_unc(name,stt,ten):
    duoi=(str(ten or '').rsplit('.',1)[-1] if '.' in str(ten or '') else 'bin')
    duoi=re.sub(r'[^a-zA-Z0-9]','',duoi)[:12] or 'bin'
    return 'UNC-%s-%s.%s' % (re.sub(r'[^a-zA-Z0-9_-]','-',name),stt,duoi)


def nguon_email_ncc(ma,*them):
    import frappe
    nguon=list(them)
    if ma:
        ncc=frappe.db.get_value('Supplier',ma,['email_id','supplier_primary_contact'],as_dict=True) or {}
        nguon.append(ncc.get('email_id'))
        if frappe.get_meta('Supplier').has_field('email_cc'):
            nguon.append(frappe.db.get_value('Supplier',ma,'email_cc'))
        # Dynamic Link được giới hạn cả DocType và mã NCC, không lấy liên hệ của NCC khác.
        ds=frappe.db.sql("""select distinct c.name,c.email_id from `tabContact` c
            left join `tabDynamic Link` l on l.parent=c.name and l.parenttype='Contact'
            where (l.link_doctype='Supplier' and l.link_name=%s) or c.name=%s
            order by c.name""",(ma,ncc.get('supplier_primary_contact') or ''),as_dict=True)
        nguon += [c.email_id for c in ds]
        if ds:
            nguon += frappe.get_all('Contact Email',filters={'parent':['in',[c.name for c in ds]],'parenttype':'Contact'},pluck='email_id',order_by='parent, idx',limit_page_length=0)
    return list(dict.fromkeys(str(x).strip() for x in nguon if str(x or "").strip()))


def dia_chi_ncc(ma,*them):
    return tach_email(*nguon_email_ncc(ma,*them))


def bang_chung(name):
    import frappe
    from email import message_from_string
    ra=[]
    for loai in ('ncc','ke-toan'):
        rows=frappe.get_all('Email Queue',filters={'reference_doctype':'Vagabond Ho So TT','reference_name':name,'message_id':ma_thu(name,loai)},fields=['name','status','creation','show_as_cc','message'],limit_page_length=0)
        for r in rows:
            ds=frappe.get_all('Email Queue Recipient',filters={'parent':r.name},fields=['recipient','status'],order_by='idx',limit_page_length=0)
            ra.append({'loai':loai,'ma':r.name,'trang_thai':r.status,'luc':str(r.creation),'cc':r.show_as_cc or '', 'nguoi_nhan':ds,'tep':[p.get_filename() for p in message_from_string(r.message or '').walk() if p.get_filename()]})
    return ra
