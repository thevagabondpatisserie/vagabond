"""#261: mã KMCB đi qua API bán thật, lưu/reload và đếm theo ba điểm bán."""
import frappe
from unittest.mock import patch
from vagabond import ban_hang, kiem_kho, diem_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon


def _bill_hoan(giam=0):
    ct,tk,_ = _nen()
    a,b = _mon(tk),_mon(tk)
    cha=frappe.copy_doc(frappe.get_doc('Item',a))
    cha.item_code='KMCB-KIEM-'+frappe.generate_hash(length=8)
    cha.insert(ignore_permissions=True); nen._DA_TAO.append((cha.doctype,cha.name))
    cb=frappe.get_doc(dict(doctype='Vagabond Combo',ten='Combo kiểm hoàn tiền',ma_hang=cha.name,bat=1,
        kieu='Gia tron goi',gia_combo=155000,dong=[dict(item_code=a,so_luong=3,gia_goc=45000),
        dict(item_code=b,so_luong=1,gia_goc=60000)]))
    cb.insert(ignore_permissions=True); nen._DA_TAO.append((cb.doctype,cb.name))
    hd=frappe.get_doc(dict(doctype='Sales Invoice',company=ct,currency='VND',conversion_rate=1,
        customer=frappe.db.get_value('Customer',{'disabled':0,'is_internal_customer':0},'name'),
        apply_discount_on='Grand Total',discount_amount=giam,
        items=[dict(item_code=a,qty=1,rate=10000),dict(item_code=cha.name,qty=1,rate=155000)]))
    hd.insert(ignore_permissions=True); nen._DA_TAO.append((hd.doctype,hd.name))
    hd.flags.ignore_permissions=True; hd.submit(); hd.reload()
    la('bill nguồn đúng tiền',hd.grand_total,165000-giam)
    return hd


@ca('#265 C2 F1 hoàn tiền 50 phần trăm qua đúng cửa app không hoàn đủ combo')
def _hoan_nua():
    from vagabond.hoan_tien import _lap_hoa_don_tra
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    for giam in (0,5000):
        hd=_bill_hoan(giam)
        tien=hd.grand_total/2
        nhap=make_sales_return(hd.name)
        nhap.vgb_combo_hoan_tien=tien
        nhap.insert(ignore_permissions=True); nen._DA_TAO.append((nhap.doctype,nhap.name))
        nhap.vgb_combo_hoan_tien=0
        try:
            nhap.save(ignore_permissions=True)
        except frappe.ValidationError as e:
            dung('không xóa dấu để tăng tiền hoàn','số tiền hoàn đã lưu' in str(e))
        else:
            dung('phải chặn bỏ dấu bồi hoàn tiền',False)
        kho=frappe.db.get_value('Warehouse',{'company':hd.company,'is_group':0},'name')
        tra=_lap_hoa_don_tra(hd,kho,'Kiểm hoàn nửa bill','KIEM265',so_tien=tien)
        nen._DA_TAO.append((tra.doctype,tra.name)); tra.reload()
        la('hoàn đúng50% sau reload',tra.grand_total,-tien)
        la('giữ số tiền yêu cầu để tính lại',tra.vgb_combo_hoan_tien,tien)


@ca('#265 C2 F2 credit note tay phải nối đúng dòng combo gốc')
def _tra_thieu_dong_goc():
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    hd=_bill_hoan()
    tra=make_sales_return(hd.name)
    for d in tra.items:
        if d.get('vgb_combo_luong'):
            for k in ('sales_invoice_item','vgb_combo_luong','vgb_combo_tien','vgb_combo_ma','vgb_combo_ten'):
                d.set(k,None)
    try:
        tra.insert(ignore_permissions=True)
    except frappe.ValidationError as e:
        dung('chỉ đường chọn dòng gốc','hóa đơn gốc' in str(e))
    else:
        nen._DA_TAO.append((tra.doctype,tra.name))
        dung('không được bỏ liên kết dòng combo',False)


@ca('#261 KMCB API: ba diem ban, 2 bo, luu lai va huy mem khong dem trung')
def _combo():
    ct, tk, mau = _nen()
    mon = _mon(tk)
    cha = frappe.copy_doc(frappe.get_doc('Item', mon))
    cha.item_code = 'KMCB-KIEM-' + frappe.generate_hash(length=8)
    cha.item_name = 'Combo kiểm ba bánh'
    cha.insert(ignore_permissions=True)
    nen._DA_TAO.append((cha.doctype, cha.name))
    cb = frappe.get_doc(dict(doctype='Vagabond Combo',ten='Combo kiểm ba bánh',ma_hang=cha.name,bat=1,
        kieu='Gia tron goi',gia_combo=140000,dong=[dict(item_code=mon,so_luong=3,gia_goc=50000)]))
    cb.insert(ignore_permissions=True)
    nen._DA_TAO.append((cb.doctype,cb.name))
    kh = frappe.db.get_value('Customer', {'disabled':0,'is_internal_customer':0}, 'name')
    from frappe.utils import today
    for diem in ('SALES','TCV','NVHTN'):
        khoa_diem = '' if diem == 'SALES' else diem
        cu = kiem_kho.da_ban(khoa_diem,today()).get(mon,0)
        with patch.object(ban_hang,'_cong_ty',return_value=ct), patch.object(ban_hang,'_khach_le',return_value=kh), patch.object(diem_ban,'diem_cua_nguon',return_value=['SALES','TCV','NVHTN']):
            ra = ban_hang.tao_don_tay(nguon='GrabFood',quay=diem,ma_don='GF-'+str(2611 + ('SALES','TCV','NVHTN').index(diem)),
                items=[dict(item_code=cha.name,qty=2,rate=140000)],tam_tinh=0)
        nen._DA_TAO.append(('Sales Invoice',ra['name']))
        hd = frappe.get_doc('Sales Invoice',ra['name'])
        la('không còn mã cha',[d.item_code for d in hd.items],[mon])
        la('6 bánh',hd.items[0].qty,6)
        la('giữ tổng gồm VAT',hd.grand_total,280000)
        dung('nhãn mã/tên',cha.name+' - '+cb.ten in hd.items[0].description)
        la('bán đúng điểm',kiem_kho.da_ban(khoa_diem,today()).get(mon,0),cu+6)
        hd.save(ignore_permissions=True); hd.reload()
        la('lưu lại không rã đôi',hd.items[0].qty,6)
        with patch.object(ban_hang, '_otp_la_sep', return_value=True), patch.object(ban_hang, '_otp_kiem', return_value='quản lý kiểm'):
            ban_hang.pos_sua_don(hd.name,items=[dict(item_code=d.item_code,qty=d.qty,rate=d.rate,dong_goc=d.name) for d in hd.items],ghi_chu='Đổi ghi chú')
        hd.reload()
        la('sửa qua app giữ tổng',hd.grand_total,280000)
        dung('sửa qua app giữ nhãn',cha.name+' - '+cb.ten in hd.items[0].description)
        hd.vgb_huy=1; hd.save(ignore_permissions=True)
        la('hủy mềm nhả số',kiem_kho.da_ban(khoa_diem,today()).get(mon,0),cu)
        la('không tạo SLE riêng',frappe.db.count('Stock Ledger Entry',{'voucher_no':hd.name}),0)


@ca('#261 combo 155000: rate 0/2 so le, luu lai, GL va payload khong mat dong')
def _tien():
    from vagabond.khung.kiem_that.thu_thue_vnd_225 import _doi_chieu
    from frappe.model.base_document import BaseDocument
    ct, tk, mau = _nen()
    a, b = _mon(tk), _mon(tk)
    cha = frappe.copy_doc(frappe.get_doc('Item', a))
    cha.item_code = 'KMCB-KIEM-' + frappe.generate_hash(length=8)
    cha.insert(ignore_permissions=True); nen._DA_TAO.append((cha.doctype, cha.name))
    cb = frappe.get_doc(dict(doctype='Vagabond Combo',ten='Combo kiểm tiền',ma_hang=cha.name,bat=1,
        kieu='Gia tron goi',gia_combo=155000,dong=[dict(item_code=a,so_luong=3,gia_goc=45000),
        dict(item_code=b,so_luong=1,gia_goc=60000)]))
    cb.insert(ignore_permissions=True); nen._DA_TAO.append((cb.doctype, cb.name))
    # Giữ khách thường cố định: vòng OWNER tạo khách mới trong cùng điểm lưu.
    kh = frappe.db.get_value('Customer', {'disabled':0,'is_internal_customer':0}, 'name')
    goc = BaseDocument.precision
    for le, loai in ((0,''),(2,''),(0,'giam'),(2,'giam'),(0,'OWNER'),(2,'OWNER')):
        def do_chinh_xac(d, fieldname, *args, **kwargs):
            if d.doctype == 'Sales Invoice Item' and fieldname in ('rate', 'base_rate'):
                return le
            return goc(d, fieldname, *args, **kwargs)
        # Chỉ thay metadata precision; core thật vẫn tính tiền, thuế, sổ cái.
        with patch.object(BaseDocument, 'precision', do_chinh_xac):
            hd = frappe.get_doc(dict(doctype='Sales Invoice',company=ct,currency='VND',conversion_rate=1,
                customer=kh,
                items=[dict(item_code=a,qty=1,rate=10000)]))
            hd.insert(ignore_permissions=True); nen._DA_TAO.append((hd.doctype, hd.name))
            ten_dong = hd.items[0].name
            hd.append('items',dict(item_code=cha.name,qty=1,rate=155000))
            hd.save(ignore_permissions=True); hd.reload()
            la('giữ tên dòng cũ',hd.items[0].name,ten_dong)
            la('thành tiền chia đúng',[d.amount for d in hd.items],[10000,107308,47692])
            la('gross gồm món lẻ',hd.grand_total,165000)
            hd.save(ignore_permissions=True); hd.reload()
            la('lưu lại giữ tiền',hd.grand_total,165000)
            if not loai:
                _chan_sua_rieng(hd)
            elif loai == 'giam':
                hd.apply_discount_on = 'Grand Total'
                hd.discount_amount = 5000
                hd.save(ignore_permissions=True); hd.reload()
                la('giảm 5000 đúng tổng',hd.grand_total,160000)
                la('giảm đầu phiếu giữ tiền dòng',[d.amount for d in hd.items],[10000,107308,47692])
            else:
                chu = frappe.copy_doc(frappe.get_doc('Customer',hd.customer))
                chu.customer_name = 'OWNER combo ' + frappe.generate_hash(length=8)
                chu.vgb_hang = 'OWNER'
                chu.insert(ignore_permissions=True); nen._DA_TAO.append((chu.doctype,chu.name))
                hd.customer = chu.name
                hd.contact_person = hd.customer_address = hd.shipping_address_name = None
                hd.save(ignore_permissions=True); hd.reload()
                la('hook OWNER áp 100%',hd.additional_discount_percentage,100)
                la('OWNER tổng 0',hd.grand_total,0)
                hd.flags.ignore_permissions=True
                hd.submit(); hd.reload()
                la('OWNER ghi sổ tổng 0',hd.grand_total,0)
                continue
            _doi_chieu(hd,tk)
            la('ghi sổ giữ tiền',hd.grand_total,160000 if loai else 165000)
            _sao_tra_sua(hd)


def _chan_sua_rieng(hd):
    """Đi qua Document.save thật, không gọi riêng bộ kiểm metadata."""
    def thu(ten, sua, cau):
        hd.reload()
        sua(hd)
        try:
            hd.save(ignore_permissions=True)
        except frappe.ValidationError as e:
            dung(ten + ': đúng cửa combo', cau in str(e))
        else:
            dung(ten + ': phải chặn', False)
    thu('xóa một thành phần',lambda d:d.remove(d.items[-1]),'xóa riêng món')
    thu('xóa dấu tiền',lambda d:d.items[1].set('vgb_combo_luong',0),'bỏ dấu combo')
    thu('đổi lượng',lambda d:d.items[1].set('qty',2),'không được sửa riêng')
    thu('đổi tiền',lambda d:d.items[1].set('vgb_combo_tien',1),'không được sửa riêng')
    ma_bo = hd.items[1].vgb_combo_ma
    thu('phiếu có số phát hành không rã lại',
        lambda d:(d.set('custom_hddt_so','KIEM261-DA-PHAT-HANH'),d.append('items',dict(item_code=ma_bo,qty=1,rate=155000))),
        'không tự rã lại')
    thu('ngoại tệ không nhận phân bổ VND',
        lambda d:(d.set('currency','USD'),d.set('conversion_rate',25000)),
        'cần hoá đơn VND')
    hd.reload()
    hd.db_set({'vgb_quay':'TCV','custom_nguon':'GrabFood','vgb_pt_thanh_toan':'GrabFood'})
    gui = [dict(item_code=d.item_code,qty=d.qty,rate=d.rate,dong_goc=d.name) for d in hd.items]
    for ten, ds, cau in (('app xóa một món',gui[:-1],'xóa riêng món'),
            ('app bỏ dòng gốc',[dict(d,dong_goc=None) for d in gui],'thiếu dòng gốc'),
            ('app đổi giá',[gui[0],dict(gui[1],rate=1),gui[2]],'không sửa riêng')):
        with patch.object(ban_hang,'_otp_la_sep',return_value=True), patch.object(ban_hang,'_otp_kiem',return_value='quản lý kiểm'):
            try:
                ban_hang.pos_sua_don(hd.name,items=ds)
            except frappe.ValidationError as e:
                dung(ten + ': đúng cửa combo',cau in str(e))
            else:
                dung(ten + ': phải chặn',False)
    hd.reload()
    # Món lẻ cùng mã vẫn thêm được với giá danh mục, không mượn giá combo.
    frappe.db.set_value('Item',hd.items[1].item_code,'standard_rate',45000)
    gui = [dict(item_code=d.item_code,qty=d.qty,rate=d.rate,dong_goc=d.name) for d in hd.items]
    gui.append(dict(item_code=hd.items[1].item_code,qty=1,rate=45000))
    with patch.object(ban_hang,'_otp_la_sep',return_value=True), patch.object(ban_hang,'_otp_kiem',return_value='quản lý kiểm'):
        ban_hang.pos_sua_don(hd.name,items=gui)
    hd.reload()
    la('app thêm món lẻ cùng mã dùng giá danh mục',hd.grand_total,210000)
    hd.remove(hd.items[-1]); hd.save(ignore_permissions=True); hd.reload()
    # Xóa trọn bộ phải lưu được và chỉ còn món lẻ; hoàn lại bằng mã cha.
    ma = hd.items[1].vgb_combo_ma
    hd.set('items',[hd.items[0]])
    hd.save(ignore_permissions=True); hd.reload()
    la('xóa trọn bộ còn món lẻ',hd.grand_total,10000)
    hd.append('items',dict(item_code=ma,qty=1,rate=155000))
    hd.save(ignore_permissions=True); hd.reload()
    la('chọn lại bộ đúng tiền',hd.grand_total,165000)


def _sao_tra_sua(hd):
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    def ma_moi(d):
        d.custom_pancake_id = None
        d.custom_pancake_display_id = None
        d.custom_hddt_so = None
        d.vgb_ma_tham_chieu = 'KT261-'+frappe.generate_hash(length=8)
        d.docstatus = 0
        return d
    tong = hd.grand_total
    sao = ma_moi(frappe.copy_doc(hd))
    # Đặt combo trước món lẻ để lộ lỗi giữ idx cũ khi rã lại.
    sao.set('items',[sao.items[1],sao.items[2],sao.items[0]])
    thu_tu = [(d.item_code,d.qty) for d in sao.items]
    sao.insert(ignore_permissions=True); nen._DA_TAO.append((sao.doctype,sao.name))
    sao.reload()
    la('Duplicate tính đủ tiền',sao.grand_total,tong)
    la('Duplicate giữ thứ tự đã chọn',[(d.item_code,d.qty) for d in sao.items],thu_tu)
    la('idx liên tục',[d.idx for d in sao.items],[1,2,3])
    tra = ma_moi(make_sales_return(hd.name))
    tra.update_outstanding_for_self = 0
    tra.insert(ignore_permissions=True); nen._DA_TAO.append((tra.doctype,tra.name))
    tra.submit(); tra.reload(); hd.reload()
    la('trả hết không mất đồng',tra.grand_total,-tong)
    la('trả hết xóa đủ nợ',hd.outstanding_amount,0)
    la('trả hết giữ phân bổ dòng',[d.amount for d in tra.items],[-10000,-107308,-47692])
    tra.cancel(); hd.reload()
    la('hủy trả hồi đủ nợ',hd.outstanding_amount,tong)
    # Ba lần trả từng bánh phải cộng đúng 107308, không thành 107307.
    cac = []
    for _ in range(0 if hd.discount_amount else 3):
        d = ma_moi(make_sales_return(hd.name))
        mon = next(x for x in d.items if x.sales_invoice_item == hd.items[1].name)
        mon.qty = -1
        d.set('items',[mon]); d.update_outstanding_for_self = 0
        d.insert(ignore_permissions=True); nen._DA_TAO.append((d.doctype,d.name))
        d.submit(); d.reload(); cac.append(d)
    if cac:
        la('trả từng bánh đủ tiền thành phần',sum(d.items[0].amount for d in cac),-107308)
    for d in reversed(cac):
        d.cancel()
    hd.reload(); hd.cancel()
    sua = ma_moi(frappe.copy_doc(hd))
    sua.amended_from = hd.name
    sua.insert(ignore_permissions=True); nen._DA_TAO.append((sua.doctype,sua.name))
    sua.submit(); sua.reload()
    la('amend giữ đúng tiền',sua.grand_total,tong)
