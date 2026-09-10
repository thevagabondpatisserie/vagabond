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
            ra = ban_hang.tao_don_tay(nguon='GrabFood',quay=diem,ma_don='KT261-'+frappe.generate_hash(length=8),
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
        hd.vgb_huy=1; hd.save(ignore_permissions=True)
        la('hủy mềm nhả số',kiem_kho.da_ban(khoa_diem,today()).get(mon,0),cu)
        la('không tạo SLE riêng',frappe.db.count('Stock Ledger Entry',{'voucher_no':hd.name}),0)
