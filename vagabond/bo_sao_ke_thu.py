"""Chủ bộ công nợ của Payment Entry lấy từ DB, không nhận quyền qua flags.

Helper cho cửa công nợ đang triển khai; chưa mở endpoint mới. Phiếu nháp,
ghi sổ và hủy đều giữ nguyên kế hoạch cho tới khi người dùng bỏ cả bộ.
"""
import frappe
from vagabond import bo_sao_ke_db as bs

O_CHU = 'vgb_bo_cong_no'
TRUONG_MOI = {'Payment Entry': [{'fieldname': O_CHU, 'label': 'Chủ bộ công nợ',
    'fieldtype': 'Link', 'options': 'Vagabond Cong No', 'read_only': 1,
    'hidden': 1, 'no_copy': 1, 'search_index': 1}]}


def chu(ten_pe, khoa=False):
    if not ten_pe:
        return None
    if (frappe.flags.get('in_migrate') or frappe.flags.get('in_install')) and not frappe.db.has_column('Payment Entry',O_CHU):
        return None
    ma=frappe.db.get_value('Payment Entry',ten_pe,O_CHU)
    if not ma:
        return None
    if khoa:
        bs.khoa_phieu('Vagabond Cong No',ma)
    raw=frappe.db.get_value('Vagabond Cong No',ma,bs.O_BO,for_update=khoa)
    b=bs.doc_bo(raw)
    if not any(c['doctype']=='Payment Entry' and c['name']==ten_pe for c in b['chung_tu']):
        frappe.throw('Phiếu thu không còn thuộc bộ công nợ đã ghi; tải lại để kiểm.')
    return ma


def bao_ve(pe, method=None):
    # Link chỉ được ghi sau khi factory đã tạo đủ PE và luu đã ghi chủ bộ.
    # Không dùng cờ bỏ kiểm do API nhận được.
    ma=None if pe.is_new() else chu(pe.name)
    pe.set(O_CHU,ma)
    if ma:
        cu=pe.get_doc_before_save()
        if not cu:
            frappe.throw('Chưa đọc được bản phiếu thu trước sửa; tải lại để kiểm.')
        if cu.get('vgb_huy') and not pe.get('vgb_huy'):
            frappe.throw('Phiếu thu của bộ đã hủy. Bỏ bộ trên phiếu công nợ rồi khớp lại để lập phiếu mới, giữ nguyên lịch sử.')
        cot=('payment_type','party_type','party','company','paid_to',
             'paid_to_account_currency','paid_amount','received_amount','reference_no','bank_account')
        refs=lambda p: sorted((r.reference_doctype,r.reference_name,float(r.allocated_amount or 0))
                              for r in p.references or [])
        if any(pe.get(k)!=cu.get(k) for k in cot) or refs(pe)!=refs(cu):
            frappe.throw('Phiếu thu đang thuộc bộ công nợ; hủy và lập lại qua phiếu công nợ để đổi khách, hóa đơn hoặc tiền.')


def khi_ghi_so(pe, method=None):
    ma=chu(pe.name,khoa=True)
    if ma:
        bs.noi_tung_phieu_thu(frappe.get_doc('Vagabond Cong No',ma),pe.name)


def gan_chu(doc, cac_pe):
    """Factory nội bộ gọi sau khi đã lưu toàn bộ danh sách PE vào bộ."""
    b=bs.doc_bo(frappe.db.get_value(doc.doctype,doc.name,bs.O_BO,for_update=True))
    ct={(c['doctype'],c['name']) for c in b['chung_tu']}
    for ma in sorted(cac_pe):
        if ('Payment Entry',ma) not in ct:
            frappe.throw('Chưa lưu phiếu thu vào bộ; không gắn chủ riêng lẻ.')
        cu=frappe.db.get_value('Payment Entry',ma,[O_CHU,'docstatus'],as_dict=True,for_update=True)
        if not cu or cu.docstatus!=0 or (cu.get(O_CHU) and cu.get(O_CHU)!=doc.name):
            frappe.throw('Phiếu thu đã đổi chủ hoặc đã ghi sổ; tải lại để kiểm.')
        frappe.db.set_value('Payment Entry',ma,O_CHU,doc.name,update_modified=False)


def kiem_nguon(doc,g):
    """Cùng kiểm nguồn, chủ cũ và PE cho danh sách lẫn lúc ghi dưới khóa."""
    ba=frappe.db.get_value('Bank Account',g.bank_account,
        ['is_company_account','disabled','account'],as_dict=True) or {}
    if not ba.get('is_company_account') or ba.get('disabled') or not ba.get('account'):
        return 'Chọn tài khoản công ty đang hoạt động.'
    if not g.reference_number:
        return 'Sao kê chưa có tham chiếu ngân hàng.'
    cu=frappe.get_all('Payment Entry',filters={'reference_no':g.reference_number,
        'payment_type':'Receive','docstatus':['<',2],'vgb_huy':0},pluck='name',limit_page_length=0)
    da_giu={c['name'] for bo in bs._cac_bo(g.name,khoa=bool(g.flags.get('for_update')))
            for c in bo['chung_tu'] if c['doctype']=='Payment Entry'}
    if any(ma not in da_giu for ma in cu):
        return 'Sao kê còn phiếu thu khác ngoài bộ; xử lý phiếu đó trước.'
    from vagabond import doi_soat_sepay as dss
    loi=dss.ly_do_tai_khoan_sepay(g.bank_account)
    if loi:return loi
    cu=dss.chu_cua_giao_dich([g.name,g.reference_number],bo_qua_phieu=doc.name,cho_bo=True)
    if cu:return 'Sao kê đã được chứng từ cũ sử dụng: '+', '.join(sorted(set(cu.values())))
    return ''


def nguon_lap(doc):
    """Factory đọc lại bộ và phần chưa có PE sống, không dùng tổng client."""
    from frappe.utils import flt
    if doc.doctype!='Vagabond Cong No':
        frappe.throw('Chủ phiếu thu phải là phiếu công nợ.')
    bs.khoa_phieu(doc.doctype,doc.name)
    doc=frappe.get_doc(doc.doctype,doc.name,for_update=True)
    b=bs.doc_hien_tai(doc)
    ct={c['name'] for c in b['chung_tu'] if c['doctype']=='Payment Entry'}
    if len(ct)!=len(b['chung_tu']):
        frappe.throw('Bộ công nợ có chứng từ không phải phiếu thu.')
    tong=sum(flt(d['phan_bo']) for d in b['dong'])
    g=bs.chon(doc,b['dong'],tong,'vao',lambda g:kiem_nguon(doc,g),ghi=True)
    phu=0
    for ma in sorted(ct):
        p=frappe.db.get_value('Payment Entry',ma,['docstatus','received_amount'],as_dict=True,for_update=True)
        if not p:frappe.throw('Không còn phiếu thu trong bộ; tải lại để kiểm.')
        if p.docstatus<2:phu+=flt(p.received_amount)
    con=tong-phu
    if con<=0:
        frappe.throw('Bộ đã có phiếu thu phủ đủ; mở Tiền đã về để ghi sổ.')
    dau=g.flags.bo_sao_ke[0]
    return frappe._dict(name=dau.name,reference_number=dau.reference_number,date=g.date,
        docstatus=1,currency='VND',deposit=con,withdrawal=0,unallocated_amount=con,
        bank_account=dau.bank_account,payment_entries=[]),doc,b


def thong_tin(ten_pe):
    """Đọc xác minh cùng nguồn DB cho tab nháp; None nếu phiếu không dùng bộ."""
    from frappe.utils import flt
    ma=chu(ten_pe)
    if not ma:return None
    doc=frappe.get_doc('Vagabond Cong No',ma)
    b=bs.doc_hien_tai(doc)
    pe=frappe.get_doc('Payment Entry',ten_pe)
    def kiem(g):
        ba=frappe.db.get_value('Bank Account',g.bank_account,
            ['company','account','is_company_account','disabled'],as_dict=True) or {}
        if (not ba.get('is_company_account') or ba.get('disabled') or
                pe.company!=ba.get('company') or pe.paid_to!=ba.get('account')):
            return 'Nguồn bộ không khớp công ty/tài khoản nhận của phiếu thu.'
        return ''
    try:
        if pe.payment_type!='Receive' or pe.party_type!='Customer' or pe.paid_to_account_currency!='VND':
            frappe.throw('Phiếu trong bộ không phải thu công nợ khách bằng VND.')
        g=bs.chon(doc,b['dong'],sum(flt(d['phan_bo']) for d in b['dong']),'vao',kiem,ghi=False)
        tong=0
        for c in b['chung_tu']:
            if c['doctype']!='Payment Entry':frappe.throw('Bộ thu chứa loại chứng từ khác.')
            p=frappe.db.get_value('Payment Entry',c['name'],['docstatus','received_amount'],as_dict=True)
            if not p:frappe.throw('Bộ thiếu phiếu thu đã lưu.')
            if p.docstatus<2:tong+=flt(p.received_amount)
        if tong>g.deposit+0.001 or flt(pe.received_amount)<=0:
            frappe.throw('Tổng phiếu thu vượt tiền trong bộ.')
        return {'ok':1,'ly_do':'','g':g,'chu':ma}
    except frappe.ValidationError as e:
        return {'ok':0,'ly_do':str(e),'g':{},'chu':ma}


def khop(name,dong,ghi_chu,ma_lan):
    """Một kỳ thu có nhiều BT; caller đã kiểm quyền Công nợ trước vào đây."""
    import json,re
    from frappe.utils import flt,now_datetime,escape_html
    from vagabond import thu_tien as tt, chiem_sao_ke
    ma_lan=str(ma_lan or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',ma_lan):
        frappe.throw('Mở lại Khớp tay để lấy mã lần thao tác, tránh ghi trùng khi mất mạng.')
    moi=bs.doc_bo({'dong':json.loads(dong) if isinstance(dong,str) else dong,'chung_tu':[]})['dong']
    if not moi:frappe.throw('Chọn ít nhất một phần sao kê.')
    sp='thu_bo_'+frappe.generate_hash(length=8)
    frappe.db.savepoint(sp)
    try:
        bs.khoa_phieu('Vagabond Cong No',name,moi)
        doc=frappe.get_doc('Vagabond Cong No',name,for_update=True)
        if frappe.db.exists('Comment',{'reference_doctype':doc.doctype,'reference_name':name,
                'content':['like','%[lần khớp '+ma_lan+']%']}):
            return {'ok':1,'da_lam_roi':1,'pe':'','loi':[],
                    'loi_nhan':'Lần khớp này đã lập phiếu thu, không lập thêm.'}
        if doc.trang_thai=='Huy':frappe.throw('Phiếu đã hủy, không nhận thêm sao kê.')
        cu=bs.doc_hien_tai(doc)
        them=sum(flt(d['phan_bo']) for d in moi)
        da=set(chiem_sao_ke.tach_gd(doc.ma_gd))
        sua_cu=not cu['dong'] and (doc.trang_thai=='Da thu du' or all(d['name'] in da or
            frappe.db.get_value('Bank Transaction',d['name'],'reference_number') in da for d in moi))
        con=flt(doc.tong_tien) if sua_cu else flt(doc.tong_tien)-flt(doc.da_thu)
        if them>con+0.001:
            frappe.throw('Phần chọn vượt khoản còn phải thu của phiếu; chọn lại số phân bổ.')
        gop={d['name']:flt(d['phan_bo']) for d in cu['dong']}
        for d in moi:gop[d['name']]=gop.get(d['name'],0)+flt(d['phan_bo'])
        ds=[dict(name=ma,phan_bo=gop[ma]) for ma in sorted(gop)]
        # Chỉ lưu sau khi số dư lõi và chỗ giữ đã được kiểm dưới khóa BT.
        bs.chon(doc,ds,sum(gop.values()),'vao',lambda g:'',ghi=True,them_dot=True)
        lap=tt.lap_phieu_thu_theo_gd([d.hoa_don for d in doc.dong if d.hoa_don],
            None,0,'Theo phiếu công nợ '+(doc.ma_phieu or doc.name),tach_khach=True,chu_bo=doc)
        if abs(flt(lap['tien'])-them)>0.001:
            frappe.throw('Bộ cũ còn phần chưa có phiếu thu sống; xử lý phần cũ trước khi nhận kỳ mới.')
        doc.reload()
        doc.da_thu=flt(doc.da_thu)+(0 if sua_cu else flt(lap['tien']))
        doc.trang_thai='Da thu du' if doc.da_thu>=flt(doc.tong_tien)-0.001 else 'Thu thieu'
        refs=[]
        for d in moi:
            refs += [d['name'],frappe.db.get_value('Bank Transaction',d['name'],'reference_number') or '']
        doc.ma_gd=chiem_sao_ke.gom_gd(chiem_sao_ke.tach_gd(doc.ma_gd)+refs)
        doc.nguoi_khop_tay=frappe.session.user
        doc.ngay_khop_tay=now_datetime()
        doc.save(ignore_permissions=True)
        tien_chu=format(flt(lap['tien']),',.0f').replace(',','.')+' đ'
        doc.add_comment('Comment',escape_html('Khớp bộ sao kê '+tien_chu+', lập phiếu thu nháp '+lap['pe']+
            '. '+str(ghi_chu or '')+' [lần khớp '+ma_lan+']'))
        if doc.trang_thai=='Da thu du' and not sua_cu:
            cac_hd=[d.hoa_don for d in doc.dong if d.hoa_don]
            frappe.db.after_commit.add(lambda:tt.xep_gui_thu(cac_hd))
        return {'ok':1,'pe':lap['pe'],'tien':lap['tien'],'loi':[],
                'loi_nhan':'Đã lập phiếu thu nháp '+lap['pe']+' cho '+tien_chu+'. Kế toán đính UNC và ghi sổ ở Tiền đã về.'}
    except Exception:
        frappe.db.rollback(save_point=sp)
        raise


def ung_vien(doc,kq):
    """Kỳ mới chỉ chọn phần chưa nằm trong kế hoạch cũ, dù PE còn nháp."""
    from frappe.utils import flt
    cu={d['name']:flt(d['phan_bo']) for d in bs.doc_hien_tai(doc)['dong']}
    kq['so_tien']=max(0,flt(doc.tong_tien)-flt(doc.da_thu))
    for r in kq['rows']:
        g=frappe.get_doc('Bank Transaction',r['name'])
        loi=(r.get('vi_sao_khong') if r.get('dung_duoc')==0 else '') or kiem_nguon(doc,g)
        r['con_lai']=max(0,bs.con_lai(g,doc)-cu.get(g.name,0))
        loi=loi or ('Giao dịch đã phân bổ hết cho các kỳ thu.' if r['con_lai']<=0 else '')
        r.update(dung_duoc=int(not loi),vi_sao_khong=loi)
    kq['chon_bo']=1
    return kq


def bo(name):
    """Bỏ cả kế hoạch sau khi kế toán xử lý mọi PE; không tự hủy bút toán."""
    from frappe.utils import flt,escape_html
    from vagabond import thu_tien as tt,chiem_sao_ke
    if not tt.la_ke_toan():
        frappe.throw('Chỉ kế toán được bỏ bộ thu công nợ.')
    bs.khoa_phieu('Vagabond Cong No',name)
    doc=frappe.get_doc('Vagabond Cong No',name,for_update=True)
    b=bs.doc_hien_tai(doc)
    if not b['dong']:return dict(ok=1,da_lam_roi=1)
    ct={(c['doctype'],c['name']) for c in b['chung_tu']}
    for dt,ma in sorted(ct):
        if dt!='Payment Entry':frappe.throw('Bộ thu chứa chứng từ không phải phiếu thu.')
        pe=frappe.db.get_value(dt,ma,['docstatus','vgb_huy'],as_dict=True,for_update=True)
        if pe and (pe.docstatus==1 or (pe.docstatus==0 and not pe.get('vgb_huy'))):
            frappe.throw('Phiếu thu '+ma+' còn hiệu lực. Kế toán xử lý phiếu thu trước khi bỏ bộ.')
    refs=set()
    for d in b['dong']:
        if any((r.doctype,r.name) in ct for r in bs._loi(d['name'])):
            frappe.throw('Sao kê còn liên kết phiếu thu; chưa bỏ được bộ.')
        refs.update((d['name'],frappe.db.get_value('Bank Transaction',d['name'],'reference_number')))
    for dt,ma in sorted(ct):
        pe=frappe.db.get_value(dt,ma,['docstatus','vgb_huy'],as_dict=True,for_update=True)
        # Nháp hủy giữ chủ lịch sử để không thể gỡ hủy rồi ghi sổ bộ đã nhả.
        if pe and pe.docstatus==2:
            frappe.db.set_value(dt,ma,O_CHU,None,update_modified=False)
    bs.luu(doc,[])
    doc.da_thu=max(0,flt(doc.da_thu)-sum(flt(d['phan_bo']) for d in b['dong']))
    doc.ma_gd=chiem_sao_ke.gom_gd([ma for ma in chiem_sao_ke.tach_gd(doc.ma_gd) if ma not in refs])
    if doc.trang_thai!='Huy':doc.trang_thai='Thu thieu' if doc.da_thu else 'Cho thu'
    doc.save(ignore_permissions=True)
    doc.add_comment('Comment',escape_html('Bỏ cả bộ thu sau khi xử lý phiếu thu: '+
        ', '.join(d['name'] for d in b['dong'])+'. Không yêu cầu khách chuyển tiền thêm.'))
    return dict(ok=1,loi_nhan='Đã bỏ cả bộ để chọn lại. Không yêu cầu khách chuyển tiền thêm.')


def tu_dong(doc, cac_ma):
    """Chỉ tự nhận cả bộ cùng mã/cùng tài khoản và đúng khoản còn phải thu.

    Không sửa một lần khớp cũ thiếu PE. Dòng đã có trong kế hoạch không phải
    tiền mới. Khi cần chọn một phần, kế toán dùng màn Khớp tay.
    """
    from frappe.utils import flt
    from vagabond import chiem_sao_ke
    from vagabond.bo_sao_ke import de_xuat_bo
    import hashlib,json
    da=set(chiem_sao_ke.tach_gd(doc.ma_gd))
    cu={d['name'] for d in bs.doc_hien_tai(doc)['dong']}
    rows=[]
    can=max(0,flt(doc.tong_tien)-flt(doc.da_thu))
    if not can or doc.trang_thai=='Huy':return dict(ok=1,da_lam_roi=1,loi=[])
    for ma in sorted(set(cac_ma or [])-da-cu):
        g=frappe.get_doc('Bank Transaction',ma)
        if g.reference_number in da:continue
        loi=kiem_nguon(doc,g)
        if g.docstatus!=1 or g.currency!='VND' or flt(g.deposit)<=0 or flt(g.withdrawal):
            loi='Sao kê không phải tiền vào VND đã ghi sổ.'
        if loi:return dict(ok=0,loi=[g.name+': '+loi])
        rows.append(dict(name=g.name,bank_account=g.bank_account,description=g.description,
            reference_number=g.reference_number,tien=flt(g.deposit),chieu='vao',con_lai=bs.con_lai(g,doc)))
    if not rows:return dict(ok=1,da_lam_roi=1,loi=[])
    k=de_xuat_bo(rows,doc.ma_phieu,can,rows[0]['bank_account'],'vao')
    if k['ket_qua']!='du':
        return dict(ok=0,loi=['Các lệnh cùng mã chưa thành một bộ đúng tiền và tài khoản. Mở Khớp tay để chọn phần thu thực tế.'])
    ma_lan='auto'+hashlib.sha256(json.dumps(k['dong'],sort_keys=True).encode()).hexdigest()[:32]
    try:
        return khop(doc.name,k['dong'],'Máy dò bộ cùng mã công nợ.',ma_lan)
    except frappe.ValidationError as e:
        return dict(ok=0,loi=[str(e)])
