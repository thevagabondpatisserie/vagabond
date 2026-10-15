"""Cấp quỹ dùng Journal Entry lõi làm chủ bộ, NQ chỉ là tham chiếu."""
import hashlib
import json
import re
import frappe
from frappe.utils import flt
from vagabond import bo_sao_ke_db as bs
from vagabond.bo_sao_ke import so_tien as tien_hop_le

O_LAN='vgb_cap_ung_lan'
TRUONG_MOI={'Journal Entry':[{'fieldname':O_LAN,'label':'Lần ghi nhận cấp quỹ',
    'fieldtype':'Data','read_only':1,'hidden':1,'no_copy':1,'unique':1}]}


def ghi(giao_dich,tai_khoan_nguon,nop_quy='',so_tien=None,ma_lan=''):
    from vagabond import tam_ung_app as tu
    tu._quyen()
    ds=json.loads(giao_dich) if isinstance(giao_dich,str) and giao_dich.lstrip().startswith('[') else giao_dich
    nhieu=isinstance(ds,list)
    if nhieu:
        ds=bs.doc_bo({'dong':ds,'chung_tu':[]})['dong']
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',str(ma_lan or '')):
            frappe.throw('Mở lại Ghi nhận cấp quỹ để lấy mã lần thao tác.')
        can=float(tien_hop_le(so_tien))
    else:
        g=frappe.get_doc('Bank Transaction',str(giao_dich))
        ds=[dict(name=g.name,phan_bo=flt(g.deposit))]
        can=flt(g.deposit)
        ma_lan='cu:'+g.name
    if not ds:frappe.throw('Chọn ít nhất một dòng tiền vào.')
    sp='cap_bo_'+frappe.generate_hash(length=8)
    frappe.db.savepoint(sp)
    try:
        # BT -> quỹ -> JE. Cấn quỹ cũng khóa quỹ trước JE.
        for ten in sorted(d['name'] for d in ds):
            if not frappe.db.get_value('Bank Transaction',ten,'name',for_update=True):
                frappe.throw('Không còn dòng sao kê; tải lại để chọn.')
        bank=frappe.db.get_value('Bank Transaction',ds[0]['name'],'bank_account',for_update=True)
        b,a=tu._quy(bank)
        lan=hashlib.sha256((bank+'|'+ma_lan).encode()).hexdigest()
        cu=frappe.db.get_value('Journal Entry',{O_LAN:lan},'name',for_update=True)
        if not cu and not nhieu:
            cu=frappe.db.get_value('Journal Entry',{'vgb_cap_ung_bt':ds[0]['name'],'docstatus':1},'name')
        if cu:
            j=frappe.get_doc('Journal Entry',cu,for_update=True)
            old=bs.doc_hien_tai(j)['dong']
            if j.docstatus!=1 or (old and sorted(old,key=lambda d:d['name'])!=sorted(ds,key=lambda d:d['name'])) or \
                    (j.get('vgb_nq_tham_chieu') or '')!=(nop_quy or '') or \
                    flt(j.total_debit)!=can or not any(d.account==tai_khoan_nguon and flt(d.credit_in_account_currency)==can for d in j.accounts):
                frappe.throw('Lần cấp quỹ đã ghi với nội dung khác hoặc đã hủy. Mở bút toán '+j.name+' để kiểm.')
            return dict(name=j.name,da_lam_roi=1,so_tien=can)
        src=frappe.get_doc('Account',tai_khoan_nguon)
        if src.company!=a.company or src.is_group or src.disabled or src.account_currency!='VND' or not str(src.account_number or src.name).startswith('111'):
            frappe.throw('Nộp tiền mặt phải chọn quỹ tiền mặt 111 cùng công ty.')
        if nop_quy and not frappe.db.exists('Vagabond Nop Quy',nop_quy):
            frappe.throw('Không tìm thấy phiếu NQ tham chiếu; chọn lại hoặc để trống.')
        def kiem(g):
            if g.bank_account!=bank:return 'Các dòng cấp quỹ phải cùng tài khoản nhận.'
            from vagabond import doi_soat_sepay as dss
            loi=dss.ly_do_tai_khoan_sepay(bank)
            chu=dss.chu_cua_giao_dich([g.name,g.reference_number],cho_bo=True)
            return loi or ('Giao dịch đang thuộc '+next(iter(chu.values())) if chu else '')
        j=frappe.new_doc('Journal Entry')
        j.company,j.voucher_type=a.company,'Journal Entry'
        j.vgb_quy_ung,j.vgb_cap_ung_bt,j.vgb_nq_tham_chieu=bank,ds[0]['name'],nop_quy or ''
        j.set(O_LAN,lan)
        j.user_remark='Tiền mặt đã cấp vào quỹ tạm ứng; NQ chỉ tham chiếu, không khẳng định đã nộp hết quỹ.'
        j.posting_date=max(str(frappe.db.get_value('Bank Transaction',d['name'],'date',for_update=True)) for d in ds)
        j.append('accounts',dict(account=a.name,debit_in_account_currency=can))
        j.append('accounts',dict(account=src.name,credit_in_account_currency=can))
        j.flags.vgb_tam_ung=True
        j.insert(ignore_permissions=True)
        bo=bs.chon(j,ds,can,'vao',kiem,ghi=True)
        j.submit();j.reload()
        if flt(j.total_debit)!=can or len(j.accounts)!=2:
            frappe.throw('Bút toán cấp quỹ không còn đúng số tiền đã chọn.')
        bs.noi(j,bo,[dict(doctype=j.doctype,name=j.name)])
        return dict(name=j.name,so_tien=can)
    except Exception:
        frappe.db.rollback(save_point=sp)
        raise


@frappe.whitelist()
def ung_vien(quy, so_tien, tai_khoan='', so_ngay=45, tu_khoa='', thu_tu='moi_nhat', bat_dau=0):
    from vagabond import tam_ung_app as tu, doi_soat_sepay as dss
    tu._quyen()
    tu._quy(quy, khoa=False)
    can=float(tien_hop_le(so_tien))
    kq=dss.danh_sach_chon('vao','',can,so_ngay,tu_khoa,quy,thu_tu,bat_dau)
    chu=frappe._dict(doctype='Journal Entry',name='cap-quy-moi')
    for r in kq['rows']:
        g=frappe.get_doc('Bank Transaction',r['name'])
        con=float(bs.con_lai(g,chu))
        r['con_lai']=con
        if con<=0:
            r.update(dung_duoc=0,vi_sao_khong='Giao dịch đã được dùng hết; chọn dòng khác.')
    kq['chon_bo']=1
    kq['tai_khoan_sepay']=[r for r in kq['tai_khoan_sepay'] if r['ma']==quy]
    return kq


def sau_huy(doc, method=None):
    if doc.get('vgb_cap_ung_bt') and bs.doc_hien_tai(doc)['dong']:
        bs.luu(doc, [])
