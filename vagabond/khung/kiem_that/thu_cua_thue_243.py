"""#243: tái hiện hai lỗi bằng đường app thật, không tự gắn taxes vào SI.

Mẫu thuế và món đều tạo trong savepoint. Chỉ cấu hình công ty/khách của
bench được định tuyến; không mock tính tiền, insert, submit hoặc GL.
"""
import frappe
from unittest.mock import patch
from vagabond import ban_hang
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, la, dung
from vagabond.khung.kiem_that.thu_thue_vnd_225 import _mau, _doi_chieu
from vagabond.hang_tang_so_cai import tai_khoan


def _nen():
    ct=cong_ty(); tk=tai_khoan(ct,'33311','Liability')
    frappe.db.set_single_value('Accounts Settings','add_taxes_from_taxes_and_charges_template',0)
    frappe.db.set_single_value('Accounts Settings','add_taxes_from_item_tax_template',1)
    # Chỉ thay is_default tạm trong điểm lưu; không commit hoặc đổi site thật lâu dài.
    for d in frappe.get_all('Sales Taxes and Charges Template',filters={'company':ct,'is_default':1},pluck='name'):
        frappe.db.set_value('Sales Taxes and Charges Template',d,'is_default',0)
    mau=frappe.get_doc(dict(doctype='Sales Taxes and Charges Template',title='KIEM243-'+frappe.generate_hash(length=8),
        company=ct,is_default=1,taxes=[dict(charge_type='On Net Total',account_head=tk,
        description='VAT đã gồm giá',rate=8,included_in_print_rate=1)]))
    mau.insert(ignore_permissions=True); nen._DA_TAO.append((mau.doctype,mau.name))
    return ct,tk,mau


def _mon(tk,ts=None):
    d=frappe.get_doc(dict(doctype='Item',item_code='KT243-'+frappe.generate_hash(length=10),
        item_name='Món kiểm thuế app',item_group=frappe.db.get_value('Item Group',{'is_group':0},'name'),
        stock_uom=frappe.db.get_value('UOM',{},'name'),is_stock_item=0,is_sales_item=1))
    if ts is not None: d.append('taxes',dict(item_tax_template=_mau(tk,ts)))
    d.insert(ignore_permissions=True); nen._DA_TAO.append((d.doctype,d.name))
    return d.name


def _app(ct,rows):
    kh=frappe.db.get_value('Customer',{'disabled':0,'is_internal_customer':0},'name')
    # Đi đúng tao_don_tay; tam_tinh chỉ bỏ yêu cầu đã thu tiền tại quầy.
    # Ba hàng rào nen.py vẫn khoá commit và gửi ngoài của toàn bộ hàm app.
    with patch.object(ban_hang,'_cong_ty',return_value=ct), patch.object(ban_hang,'_khach_le',return_value=kh):
        ra=ban_hang.tao_don_tay(nguon='GrabFood',ma_don='KT243-'+frappe.generate_hash(length=10),items=rows,tam_tinh=1)
    nen._DA_TAO.append(('Sales Invoice',ra['name']))
    hd=frappe.get_doc('Sales Invoice',ra['name'])
    return hd


@ca('#243 app thật: không gắn mẫu món vẫn nạp VAT đã gồm giá ở máy chủ')
def _app_khong_mau_mon():
    ct,tk,mau=_nen(); ma=_mon(tk)
    hd=_app(ct,[dict(item_code=ma,qty=1,rate=10420000)])
    la('mẫu từ cấu hình',hd.taxes_and_charges,mau.name)
    la('thuế được áp',hd.vgb_thue_vnd,1)
    la('net',hd.net_total,9648148); la('VAT',hd.total_taxes_and_charges,771852)
    la('gross giữ nguyên',hd.grand_total,10420000)


@ca('#243 app thật: mẫu món 8/10 không đẩy bill 220.000 thành 239.000')
def _app_hon_hop():
    ct,tk,mau=_nen()
    hd=_app(ct,[dict(item_code=_mon(tk,8),qty=1,rate=150000),dict(item_code=_mon(tk,10),qty=1,rate=70000)])
    la('giữ bill',hd.grand_total,220000)
    la('mẫu gồm giá',hd.taxes[0].included_in_print_rate,1)
    from vagabond.thue_vnd import doc_dong
    la('giữ từng thuế suất',[x['rate'] for x in doc_dong(hd)],[8,10])
    # Sửa nháp và reload lần nữa phải giữ cùng chính sách.
    hd.save(ignore_permissions=True); hd.reload()
    la('lưu lại không cộng VAT lần hai',hd.grand_total,220000)


@ca('#243 core: SI có tên mẫu nhưng trống bảng vẫn nạp đầy đủ khi insert')
def _server():
    ct,tk,mau=_nen()
    hd=frappe.get_doc(dict(doctype='Sales Invoice',company=ct,currency='VND',conversion_rate=1,
        customer=frappe.db.get_value('Customer',{'disabled':0,'is_internal_customer':0},'name'),
        taxes_and_charges=mau.name,items=[dict(item_code=_mon(tk),qty=1,rate=108000)]))
    hd.insert(ignore_permissions=True); nen._DA_TAO.append((hd.doctype,hd.name)); hd.reload()
    la('bảng thuế đầy đủ',len(hd.taxes),1)
    _doi_chieu(hd,tk)


@ca('#243 core: phần trăm chiết khấu và qty phân số giữ SI/GL/payload cùng tiền')
def _le():
    from vagabond.khung.kiem_that.thu_thue_vnd_225 import _dung
    for gia in (99999,100.33,100.55):
        hd,tk=_dung([gia],[8])
        # Đơn vị riêng cho ca phân số; không nới quy tắc UOM của món thật.
        uom='KT243-'+frappe.generate_hash(length=8)
        u=frappe.get_doc(dict(doctype='UOM',uom_name=uom,must_be_whole_number=0));u.insert(ignore_permissions=True)
        nen._DA_TAO.append((u.doctype,u.name))
        it=frappe.get_doc('Item',_mon(tk))
        it.stock_uom=u.name;it.set('uoms',[]);it.append('uoms',dict(uom=u.name,conversion_factor=1));it.save(ignore_permissions=True)
        hd.items[0].item_code=it.name;hd.items[0].uom=u.name;hd.items[0].stock_uom=u.name
        hd.items[0].qty=1.25;hd.additional_discount_percentage=7.5
        hd.save(ignore_permissions=True);hd.reload();_doi_chieu(hd,tk)
