"""#296: API lưu/duyệt thật, reload GL/SLE; chỉ giả cửa gửi ra nhà cung cấp."""
from unittest.mock import patch
import frappe
from frappe.utils import add_days, today
from vagabond import ban_hang, hang_tang
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don, _gl
from vagabond.khung.kiem_that.thu_hang_tang_kho_243 import _nen, _sle


@ca('#296 Lưu đơn qua API chỉ tạo nháp; thiếu phương thức không qua được')
def luu():
    hd=_hoa_don(False)
    hd.vgb_quay='TCV';hd.custom_nguon='Tại chỗ';hd.vgb_pt_thanh_toan='Tiền mặt'
    hd.save(ignore_permissions=True)
    with patch.object(ban_hang,'_tu_xuat_hddt',side_effect=AssertionError('Lưu không phát hành')):
        ket=ban_hang.pos_luu_don(hd.name,pt='Tiền mặt',ghi_chu='Lưu đơn fixture 296')
    hd.reload();la('nháp thật',hd.docstatus,0);la('API báo nháp',ket['docstatus'],0)
    la('không GL',_gl(hd),[]);la('không SLE',_sle(hd),[])
    # Dựng nháp thiếu ô đã tồn từ nguồn cũ; save hiện tại vốn đã chặn ô trống.
    hd.db_set('vgb_pt_thanh_toan','');hd.reload()
    try:ban_hang.pos_luu_don(hd.name)
    except frappe.ValidationError as e:dung('lý do đọc được','phương thức' in str(e))
    else:dung('phải chặn đơn thiếu phương thức',False)


@ca('#296 duyệt nháp ngày cũ: ngày mới, GL/SLE thật rồi mới một lời gọi phát hành')
def duyet_ngay_cu():
    hd,kho,lo=_nen()
    hd.set_posting_time=1;hd.posting_date=add_days(today(),-1)
    hd.due_date=hd.posting_date;hd.payment_schedule=[]
    hd.save(ignore_permissions=True)
    goi=[]
    def xuat(ten):
        doc=frappe.get_doc('Sales Invoice',ten)
        la('đã ghi sổ trước gửi',doc.docstatus,1)
        la('ngày hôm nay',str(doc.posting_date),today())
        dung('GL có thật',bool(_gl(doc)));dung('SLE có thật',bool(_sle(doc)))
        goi.append(ten);return True,''
    commit=frappe.db.commit
    goi_commit=[]
    def soat_commit(*a,**kw):
        # Đếm Ý ĐỊNH commit trước khi Database.commit gặp cờ cách ly bench.
        import inspect
        stack={f.function for f in inspect.stack()}
        dung('không commit trong save/submit',not stack.intersection({'_save','_submit','submit','save'}))
        goi_commit.append(1)
        return commit(*a,**kw)
    with patch.object(ban_hang,'_tu_xuat_hddt',side_effect=xuat), patch.object(frappe.db,'commit',side_effect=soat_commit):
        ket=hang_tang.duyet(hd.name,'Duyệt fixture cũ qua API thật')
    hd.reload();la('duyệt',hd.vgb_tang_duyet,hang_tang.TT_DUYET)
    la('kết quả', (ket['ghi_so'],ket['xuat_hddt'],ket['loi']),(1,1,''))
    la('một lần gọi',goi,[hd.name]);la('xuất đúng lượng',sum(d.actual_qty for d in _sle(hd)),-2)
    dung('GL cân',abs(sum(d.debit-d.credit for d in _gl(hd)))<0.01)
    la('chỉ commit quyết định và commit sổ',len(goi_commit),2)


@ca('#296 duyệt thiếu kho: giữ Đã duyệt và nháp, trả lỗi, không GL/SLE/phát hành')
def duyet_thieu_kho():
    hd,kho,lo=_nen();hd.items[0].qty=8;hd.save(ignore_permissions=True)
    with patch.object(ban_hang,'_tu_xuat_hddt',side_effect=AssertionError('Thiếu kho không phát hành')):
        ket=hang_tang.duyet(hd.name,'Duyệt fixture thiếu tồn thật')
    hd.reload();la('quyết định còn',hd.vgb_tang_duyet,hang_tang.TT_DUYET)
    la('nháp',hd.docstatus,0);la('chưa ghi sổ',ket['ghi_so'],0)
    dung('báo lỗi có nội dung',bool(ket['loi']) and 'Error Log' not in ket['loi'])
    la('không GL dở',_gl(hd),[]);la('không SLE dở',_sle(hd),[])


@ca('#296 lỗi sau khi core đã ghi GL/SLE cũng lùi hết và giữ quyết định duyệt')
def loi_sau_so():
    hd,kho,lo=_nen()
    lop=type(hd);goc=lop.submit
    def hong(doc):
        goc(doc)
        dung('đột biến đã chạm GL thật',bool(_gl(doc)))
        frappe.db.after_commit.add(viec_loi)
        raise frappe.ValidationError('Lỗi thử sau khi sổ đã ghi')
    def viec_loi():
        raise AssertionError('Callback của đơn lỗi không được chạy')
    with patch.object(lop,'submit',hong), patch.object(ban_hang,'_tu_xuat_hddt',side_effect=AssertionError('Không gửi')):
        ket=hang_tang.duyet(hd.name,'Duyệt fixture lỗi sau GL')
    hd.reload();la('nháp',hd.docstatus,0);la('giữ duyệt',hd.vgb_tang_duyet,hang_tang.TT_DUYET)
    dung('đúng điểm lỗi','Lỗi thử sau khi sổ đã ghi' in ket['loi'])
    la('GL đã lùi',_gl(hd),[]);la('SLE đã lùi',_sle(hd),[])
    dung('không sót callback',viec_loi not in frappe.db.after_commit._functions)


@ca('#298 R2 lưu chuyển khoản, huỷ mềm, bill thay thế được nhận cùng giao dịch')
def huy_nhap_nha_tien():
    from vagabond import doi_soat_sepay
    ds=[]
    for i in range(2):
        hd=_hoa_don(False);hd.vgb_quay='TCV';hd.custom_nguon='Tại chỗ'
        hd.vgb_pt_thanh_toan='Chuyển khoản';hd.vgb_ma_tham_chieu='VGB296R2'
        hd.save(ignore_permissions=True);ds.append(hd)
    cu,moi=ds
    gd='THU296-'+frappe.generate_hash(length=12)
    # Chỉ giả kết quả ngân hàng; cửa hỏi chủ, save, huỷ và DB đều là thật.
    with patch.object(ban_hang,'_sepay_cho_bill',return_value={'nhan':cu.grand_total,'gd':[gd]}):
        ban_hang.pos_luu_don(cu.name)
        cu.reload();dung('đã giữ giao dịch',gd in cu.vgb_gd_sepay)
        try:ban_hang.pos_luu_don(moi.name)
        except frappe.ValidationError as e:dung('chặn đúng chủ',cu.name in str(e))
        else:dung('hai nháp không cùng nhận tiền',False)
        with patch.object(ban_hang,'_otp_kiem',return_value='OTP fixture đã xác nhận'):
            ban_hang.pos_xoa(cu.name,otp='fixture',ly_do='Huỷ nháp fixture để lập bill thay thế')
        cu.reload();la('huỷ mềm',cu.vgb_huy,1);la('còn nháp',cu.docstatus,0)
        ban_hang.pos_luu_don(moi.name)
    moi.reload();la('bill mới giữ tiền',doi_soat_sepay.chu_cua_giao_dich([gd]).get(gd),'hoá đơn bán '+moi.name)
    from vagabond import chung_tu
    try:chung_tu.bo_danh_dau_huy('Sales Invoice',cu.name)
    except frappe.ValidationError as e:dung('phục hồi báo bill đang giữ',moi.name in str(e))
    else:dung('không phục hồi chủ thứ hai',False)
    cu.reload();la('vẫn giữ dấu hủy',cu.vgb_huy,1)
    la('không sổ cái',_gl(cu)+_gl(moi),[])


@ca('#298 kế toán chỉ có vai Accounts ghi sổ thật; Sales không được ghi')
def quyen_ke_toan_doc_lap():
    from vagabond.khung.kiem_that.nen import _DA_TAO
    cu=frappe.session.user
    u=frappe.get_doc({'doctype':'User','email':'kt298-'+frappe.generate_hash(length=10)+'@example.invalid','first_name':'Kiểm quyền ghi sổ','enabled':1,'send_welcome_email':0,'roles':[{'role':'Sales User'}]})
    u.insert(ignore_permissions=True);_DA_TAO.append(('User',u.name))
    try:
        for vai in ('Sales User','Accounts User','Accounts Manager'):
            frappe.set_user('Administrator')
            hd=_hoa_don(False);hd.vgb_quay='TCV';hd.custom_nguon='Tại chỗ';hd.vgb_pt_thanh_toan='Tiền mặt';hd.save(ignore_permissions=True)
            u.set('roles',[{'role':vai}]);u.save(ignore_permissions=True)
            frappe.clear_cache(user=u.name);frappe.set_user(u.name)
            if vai!='Sales User':
                dung('không có vai bán hàng ẩn',not ban_hang.QUYEN_BAN_HANG.intersection(frappe.get_roles()))
                ket=ban_hang.pos_ghi_so(hd.name)
                la('API ghi sổ',ket['ok'],1)
            else:
                try:ban_hang.pos_ghi_so(hd.name)
                except frappe.ValidationError as e:dung('đúng chốt kế toán','Chỉ kế toán' in str(e))
                else:dung('Sales phải bị chặn',False)
            frappe.set_user('Administrator');hd.reload()
            la('trạng thái thật',hd.docstatus,0 if vai=='Sales User' else 1)
            dung('GL theo quyền',bool(_gl(hd))==(vai!='Sales User'))
    finally:
        frappe.set_user(cu)
