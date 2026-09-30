"""#389: điền mã hàng loạt phải bỏ MST nhiều mã, kiểm SQL MariaDB thật.

Fixture tạo trong savepoint, mô phỏng dữ liệu cũ bằng set_value trên chính
chứng từ thử. Không sửa hồ sơ thật, không commit, không gửi HĐĐT.
"""
from uuid import uuid4
import frappe
from vagabond import ma_ke_toan as mk
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon, _app


@ca('#389 mã KT: SQL thật bỏ MST đa mã ở cả hai đường, giữ ô cũ, retry không đổi')
def _dien_ma_sql():
    dung('bench có mã khách', frappe.db.has_column('Customer', 'custom_ma_khach'))
    ct, tk, _ = _nen()
    mon = _mon(tk)
    # Dãy ngẫu nhiên riêng để không đụng MST của fixture khác.
    so = str(uuid4().int % 1000000000).zfill(9)
    mst = '7' + so
    mst_don = '8' + so
    khach = []
    for tax, ma in ((mst, 'KH900001'), (mst[:4]+' '+mst[4:], 'KH900002'),
                    (mst_don+'-001', 'KH900003'), (mst_don+'001', ' kh900003 ')):
        d = frappe.get_doc(dict(doctype='Customer', customer_name='KT389-'+frappe.generate_hash(length=10),
            customer_type='Company', customer_group=frappe.db.get_value('Customer Group', {'is_group':0}, 'name'),
            territory=frappe.db.get_value('Territory', {'is_group':0}, 'name')))
        d.insert(ignore_permissions=True); _DA_TAO.append((d.doctype,d.name))
        frappe.db.set_value('Customer', d.name, {'tax_id':tax, 'custom_ma_khach':ma})
        khach.append(d.name)
    la('SQL tra MST giữ xung đột cả cách viết khoảng trắng', mk.ma_theo_mst('Customer', mst), '')
    la('SQL tra nhánh có/không gạch dùng một mã', mk.ma_theo_mst('Customer', mst_don+'001'), 'KH900003')
    la('bảng mã báo cáo cũng bỏ xung đột', mk.bang_ma_theo_mst([mst,mst_don+'001']), {mk.chuan_mst(mst_don+'001'):'KH900003'})
    hd = []
    for kh, tax, ma in ((khach[0],mst,''), (khach[0],'',''),
                        (khach[2],mst_don+'001',''), (khach[2],'',''),
                        (khach[0],mst,'KH999999')):
        d = _app(ct, [dict(item_code=mon, qty=1, rate=108000)])
        frappe.db.set_value('Sales Invoice', d.name, dict(customer=kh,vgb_xhd_mst=tax,vgb_ma_khach_ke_toan=ma))
        hd.append(d)
    def doc_ma():
        return [frappe.db.get_value('Sales Invoice',d.name,'vgb_ma_khach_ke_toan') or '' for d in hd]
    truoc = [(d.name,d.grand_total,d.outstanding_amount,d.docstatus) for d in hd]
    mk.dien_ma_hang_loat()
    la('bỏ xung đột, nhận một mã chuẩn, giữ ô đã có', doc_ma(), ['', '', 'KH900003', 'KH900003', 'KH999999'])
    mk.dien_ma_hang_loat()
    la('lặp lại không nhận mã ngẫu nhiên', doc_ma(), ['', '', 'KH900003', 'KH900003', 'KH999999'])
    sau = []
    for d in hd:
        d.reload(); sau.append((d.name,d.grand_total,d.outstanding_amount,d.docstatus))
    la('không đổi tiền, trạng thái chứng từ', sau, truoc)
