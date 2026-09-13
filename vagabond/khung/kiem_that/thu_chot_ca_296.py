"""#296.3: mở/chốt ca thật, tổng từ SI thật, reload biên bản và tiền nộp quỹ."""
from unittest.mock import patch
import frappe
from vagabond import ca_quay, ban_hang
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don


@ca('#296.3 ca thật giữ số máy CK/thẻ 0; chỉ tiền mặt lệch và giữ số nộp quỹ')
def chot():
    diem='KT296-'+frappe.generate_hash(length=10)
    ds=[]
    # Chỉ khai phạm vi fixture; phép cộng đọc SI và lưu bảng con là thật.
    with patch.object(ban_hang,'_loc_diem_ban',side_effect=lambda q:{'name':['in',ds or ['khong-co']]}), \
         patch.object(ca_quay,'_co_quay',return_value=True), \
         patch.object(ca_quay,'_pt_cua_diem',return_value=['Tiền mặt','Chuyển khoản','Thẻ - Payoo']):
        mo=ca_quay.mo_ca(diem,tien_le_dau_ca=500000)
        nen._DA_TAO.append((ca_quay.CA,mo['ma']))
        for pt in ('Tiền mặt','Chuyển khoản'):
            hd=_hoa_don(False);hd.vgb_pt_thanh_toan=pt
            hd.save(ignore_permissions=True);ds.append(hd.name)
        so=frappe.db.get_value('Sales Invoice',ds[0],'grand_total')
        lan1=ca_quay.chot_ca(diem,so+500000-50000)
        la('chưa chốt vì thiếu tiền mặt',lan1['can_ly_do'],1)
        la('giữ ca mở',frappe.db.get_value(ca_quay.CA,mo['ma'],'trang_thai'),ca_quay.TT_DANG_MO)
        ket=ca_quay.chot_ca(diem,so+500000-50000,ly_do_lech='Thiếu tiền mặt trong fixture')
        la('đã chốt',ket['da_chot'],1)
    doc=frappe.get_doc(ca_quay.CA,mo['ma'])
    dong={d.phuong_thuc:d for d in doc.dong}
    la('đủ cả dòng không bán',set(dong),{'Tiền mặt','Chuyển khoản','Thẻ - Payoo'})
    la('CK giữ số máy',dong['Chuyển khoản'].may,so);la('CK không lệch',dong['Chuyển khoản'].lech,0)
    la('thẻ không bán vẫn có',dong['Thẻ - Payoo'].may,0)
    la('tiền mặt đúng số đếm',doc.tien_mat_dem,so+450000)
    la('chỉ thiếu tiền mặt',doc.tong_lech,-50000)


@ca('#296.3 API không ghi số tiền sai hoặc NaN vào ca thật')
def so_sai():
    diem='KT296-'+frappe.generate_hash(length=10)
    mo=ca_quay.mo_ca(diem,0);nen._DA_TAO.append((ca_quay.CA,mo['ma']))
    for so in ('nan','inf','{"Tiền mặt":"abc"}'):
        try:ca_quay.chot_ca(diem,so)
        except frappe.ValidationError as e:dung('nhắc tiền mặt','tiền mặt' in str(e))
        else:dung('phải chặn '+so,False)
    doc=frappe.get_doc(ca_quay.CA,mo['ma'])
    la('ca vẫn mở',doc.trang_thai,ca_quay.TT_DANG_MO);la('không biên bản dở',len(doc.dong),0)
