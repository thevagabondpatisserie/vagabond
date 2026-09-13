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
    hd.vgb_pt_thanh_toan='';hd.save(ignore_permissions=True)
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
    with patch.object(ban_hang,'_tu_xuat_hddt',side_effect=xuat):
        ket=hang_tang.duyet(hd.name,'Duyệt fixture cũ qua API thật')
    hd.reload();la('duyệt',hd.vgb_tang_duyet,hang_tang.TT_DUYET)
    la('kết quả', (ket['ghi_so'],ket['xuat_hddt'],ket['loi']),(1,1,''))
    la('một lần gọi',goi,[hd.name]);la('xuất đúng lượng',sum(d.actual_qty for d in _sle(hd)),-2)
    dung('GL cân',abs(sum(d.debit-d.credit for d in _gl(hd)))<0.01)


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
        raise frappe.ValidationError('Lỗi thử sau khi sổ đã ghi')
    with patch.object(lop,'submit',hong), patch.object(ban_hang,'_tu_xuat_hddt',side_effect=AssertionError('Không gửi')):
        ket=hang_tang.duyet(hd.name,'Duyệt fixture lỗi sau GL')
    hd.reload();la('nháp',hd.docstatus,0);la('giữ duyệt',hd.vgb_tang_duyet,hang_tang.TT_DUYET)
    dung('đúng điểm lỗi','Lỗi thử sau khi sổ đã ghi' in ket['loi'])
    la('GL đã lùi',_gl(hd),[]);la('SLE đã lùi',_sle(hd),[])
