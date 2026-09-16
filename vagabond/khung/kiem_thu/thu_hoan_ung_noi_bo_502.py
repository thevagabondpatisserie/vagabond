"""Gợi ý là trợ giúp chọn; chứng từ và sao kê vẫn phải đúng chủ quỹ."""
from unittest.mock import patch
import frappe
from vagabond import hoan_ung_noi_bo as hu
from vagabond.khung.kiem_thu.nen import ca, la, dung


@ca('502 gợi ý: cùng giao dịch, đúng mã, đúng tiền rồi mới nhất')
def _xep():
    ds = [dict(name='TTNB-26-09-00001', tong_tien=100, creation='2026-09-16'),
          dict(name='TTNB-26-09-00002', tong_tien=100, creation='2026-09-15'),
          dict(name='TTNB-26-09-00003', tong_tien=99, creation='2026-09-14'),
          dict(name='TTNB-26-09-00004', tong_tien=200, creation='2026-09-13', ma_gd='BT1'),
          dict(name='TTNB-26-09-00005', tong_tien=300, creation='2026-09-12')]
    ra = hu.xep_goi_y(ds, 100, 'THE VAGABOND TTNB260900005', 'BT1')
    la('thứ tự', [r['name'][-1] for r in ra], ['4', '5', '1', '2', '3'])
    la('lý do', [r['goi_y'] for r in ra[:3]], ['Cùng giao dịch', 'Đúng mã phiếu', 'Đúng số tiền'])
    dung('không sửa đầu vào', 'goi_y' not in ds[0])


@ca('502 gợi ý: cùng tiền xếp mới trước, không ưu tiên gần tiền')
def _ngay():
    ds = [dict(name='A', tong_tien=102, creation='2026-09-12'),
          dict(name='B', tong_tien=900, creation='2026-09-16'),
          dict(name='C', tong_tien=100, creation='2026-09-10')]
    la('gợi ý rồi mới nhất', [r['name'] for r in hu.xep_goi_y(ds,100)], ['C','B','A'])


@ca('502 nguồn chi: 141 đúng chủ hợp lệ, tài khoản cá nhân thường không hợp lệ')
def _nguon():
    def nguon(so, party='NGUOI-UNG', disabled=0, company=0):
        with patch.object(frappe.db, 'get_value', side_effect=[
            dict(name='MB',account='TK',is_company_account=company,party_type='Supplier',party=party,disabled=0),
            dict(account_number=so,disabled=disabled,is_group=0)]):
            return hu.nguon_chi('MB')
    dung('1413 được ứng', nguon('1413')['tam_ung'])
    dung('không đổi thành công ty', not nguon('1413')['cong_ty'])
    dung('thiếu chủ không được ứng', not nguon('1413',party='')['tam_ung'])
    dung('112 cá nhân không được ứng', not nguon('112')['tam_ung'])
    dung('112 công ty vẫn được chi', nguon('112',company=1)['cong_ty'])
    la('ngưng dùng bị loại', nguon('1413',disabled=1), {})


@ca('502 giữ sao kê: mã FT và BT khóa cùng dòng thật')
def _khoa():
    g = frappe._dict(name='BT1',reference_number='FT1')
    with patch.object(hu,'giao_dich',return_value=g), patch.object(frappe.db,'sql') as sql:
        la('hai mã', hu.khoa_ma_giao_dich('FT1'), {'BT1','FT1'})
        dung('khóa đúng BT', 'for update' in sql.call_args[0][0] and sql.call_args[0][1] == ('BT1',))


@ca('502 gợi ý: phiếu đúng ngoài 60 dòng vẫn đứng đầu')
def _ngoai_60():
    ds = [dict(name='TTNB-26-09-%05d' % i, tong_tien=200, creation='2026-09-16') for i in range(1,70)]
    ds.append(dict(name='TTNB-26-08-00001',tong_tien=100,creation='2026-08-01'))
    la('không bỏ sót', hu.xep_goi_y(ds,100)[0]['name'], 'TTNB-26-08-00001')


def _doc_kiem(nhan='NGUOI-UNG', lien_ket=''):
    class Doc(frappe._dict):
        def get_doc_before_save(self):
            return None
    doc=Doc(name='APP1',loai='Hoan ung',trang_thai='Nhap',tk_nhan='MB',nha_cung_cap=nhan,
        dong=[frappe._dict(name='D1',de_nghi_chi='TTNB1',so_tien=100,ma_giao_dich='FT1')])
    p=frappe._dict(name='TTNB1',trang_thai='Da chi',ma_gd='BT1',ho_so_tt=lien_ket,tong_tien=100,so_tien=100)
    g=frappe._dict(name='BT1',reference_number='FT1',bank_account='MB',withdrawal=100,docstatus=1)
    return doc,p,g


@ca('502 nối APP: đúng chủ giữ phiếu và chuẩn hóa sao kê, không commit')
def _noi():
    doc,p,g=_doc_kiem()
    with patch.object(frappe.db,'sql',return_value=[p]) as sql, \
         patch.object(frappe.db,'set_value') as luu, patch.object(frappe.db,'commit') as commit, \
         patch.object(hu,'giao_dich',return_value=g), \
         patch.object(hu,'nguon_chi',return_value={'tam_ung':True,'party':'NGUOI-UNG'}):
        hu.kiem_ho_so(doc)
        la('mã BT',doc.dong[0].ma_giao_dich,'BT1')
        dung('giữ khóa phiếu', 'for update' in sql.call_args[0][0])
        la('giữ đúng APP',luu.call_args[0][3],'APP1')
        dung('không commit giữa chừng',not commit.called)


@ca('502 nối APP: khác chủ và phiếu đã giữ không ghi đè')
def _sai():
    for nhan,lien,loi in [('KHAC','','đúng người'),('NGUOI-UNG','APP2','đã nối hồ sơ')]:
        doc,p,g=_doc_kiem(nhan,lien)
        with patch.object(frappe.db,'sql',return_value=[p]), patch.object(frappe.db,'set_value') as luu, \
             patch.object(hu,'giao_dich',return_value=g), \
             patch.object(hu,'nguon_chi',return_value={'tam_ung':True,'party':'NGUOI-UNG'}):
            try:
                hu.kiem_ho_so(doc)
            except frappe.ValidationError as e:
                dung('lý do sửa được',loi in str(e))
            else:
                dung('phải chặn hoàn sai người hoặc trùng',False)
            dung('không ghi đè',not luu.called)


@ca('502 hủy và gửi lại: nhả đúng phiếu, không ghi đè người vừa giữ')
def _huy_gui_lai():
    doc,p,g=_doc_kiem()
    cu=frappe._dict(name='APP1',loai='Hoan ung',trang_thai='Nhap',tk_nhan='MB',nha_cung_cap='NGUOI-UNG',
        dong=[frappe._dict(doc.dong[0])])
    doc.get_doc_before_save=lambda: cu
    doc['trang_thai']='Huy'
    with patch.object(frappe.db,'sql') as sql, patch.object(frappe.db,'set_value') as luu:
        hu.kiem_ho_so(doc)
        dung('nhả có điều kiện chủ cũ', 'ho_so_tt=%s' in sql.call_args[0][0])
        la('đúng phiếu đúng hồ sơ',sql.call_args[0][1],('TTNB1','APP1'))
        dung('không giữ lại sau hủy',not luu.called)
    cu['trang_thai']='Tu choi'
    doc['trang_thai']='Cho ke toan'
    p.ho_so_tt='APP2'
    with patch.object(frappe.db,'sql',return_value=[p]), patch.object(frappe.db,'set_value') as luu:
        try:
            hu.kiem_ho_so(doc)
        except frappe.ValidationError as e:
            dung('báo hồ sơ mới', 'APP2' in str(e))
        else:
            dung('không bỏ qua vì dòng không đổi',False)
        dung('không ghi đè',not luu.called)
