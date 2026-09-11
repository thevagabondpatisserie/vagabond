"""#261: mã KMCB đi qua API bán thật, lưu/reload và đếm theo ba điểm bán."""
import frappe
from unittest.mock import patch
from vagabond import ban_hang, kiem_kho, diem_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon


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
    goc = BaseDocument.precision
    for le, loai in ((0,''),(2,''),(0,'giam'),(2,'giam'),(0,'OWNER'),(2,'OWNER')):
        def do_chinh_xac(d, fieldname, *args, **kwargs):
            if d.doctype == 'Sales Invoice Item' and fieldname in ('rate', 'base_rate'):
                return le
            return goc(d, fieldname, *args, **kwargs)
        # Chỉ thay metadata precision; core thật vẫn tính tiền, thuế, sổ cái.
        with patch.object(BaseDocument, 'precision', do_chinh_xac):
            hd = frappe.get_doc(dict(doctype='Sales Invoice',company=ct,currency='VND',conversion_rate=1,
                customer=frappe.db.get_value('Customer',{'disabled':0,'is_internal_customer':0},'name'),
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
                hd.save(ignore_permissions=True); hd.reload()
                la('hook OWNER áp 100%',hd.additional_discount_percentage,100)
                la('OWNER tổng 0',hd.grand_total,0)
                hd.flags.ignore_permissions=True
                hd.submit(); hd.reload()
                la('OWNER ghi sổ tổng 0',hd.grand_total,0)
                continue
            _doi_chieu(hd,tk)
            la('ghi sổ giữ tiền',hd.grand_total,160000 if loai else 165000)


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
    hd.reload()
    hd.db_set({'vgb_quay':'TCV','custom_nguon':'GrabFood','vgb_pt_thanh_toan':'GrabFood',
        'vgb_ma_tham_chieu':'KT261-'+frappe.generate_hash(length=8)})
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
    # Xóa trọn bộ phải lưu được và chỉ còn món lẻ; hoàn lại bằng mã cha.
    ma = hd.items[1].vgb_combo_ma
    hd.set('items',[hd.items[0]])
    hd.save(ignore_permissions=True); hd.reload()
    la('xóa trọn bộ còn món lẻ',hd.grand_total,10000)
    hd.append('items',dict(item_code=ma,qty=1,rate=155000))
    hd.save(ignore_permissions=True); hd.reload()
    la('chọn lại bộ đúng tiền',hd.grand_total,165000)
