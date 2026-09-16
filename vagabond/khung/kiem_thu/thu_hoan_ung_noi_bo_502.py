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
