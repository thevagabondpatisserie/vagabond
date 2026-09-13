"""Giữ công cụ chẩn đoán #303 chỉ đọc và không truy vấn lan khi thiếu mã."""
import unittest
import importlib.util
from pathlib import Path
from vagabond.khung.kiem_thu.nen import ca
_duong = Path(__file__).resolve().parents[3] / 'cong_cu' / 'ra_phantom_303.py'
_dac_ta = importlib.util.spec_from_file_location('ra_phantom303', _duong)
_mo_dun = importlib.util.module_from_spec(_dac_ta)
_dac_ta.loader.exec_module(_mo_dun)
doc = _mo_dun.doc


class Nguon:
    def __init__(self, co_mon=True):
        self.goi = []
        self.co_mon = co_mon

    def get_all(self, loai, **tham_so):
        self.goi.append((loai, tham_so))
        if loai == 'Item' and self.co_mon:
            return [{'name': 'MASS', 'is_stock_item': 0}]
        return []


class Thu(unittest.TestCase):
    def test_thieu_ma_khong_doc_db(self):
        n = Nguon()
        for gia in [None, [], 'MASS', [''], [None]]:
            with self.assertRaises(ValueError):
                doc(n, gia)
        self.assertEqual(n.goi, [])

    def test_ma_khong_co_dung_truoc_bom(self):
        n = Nguon(False)
        with self.assertRaisesRegex(ValueError, 'MASS'):
            doc(n, ['MASS'])
        self.assertEqual(len(n.goi), 1)

    def test_khong_bom_khong_quet_toan_bang_con(self):
        n = Nguon()
        k = doc(n, ['MASS', ' MASS '])
        self.assertTrue(k['chi_doc'])
        self.assertEqual(k['thanh_phan'], [])
        self.assertEqual(k['bom_cha'], [])
        for loai, tham_so in n.goi:
            self.assertEqual(tham_so['limit_page_length'], 0)
            self.assertTrue(tham_so['filters'])
            self.assertNotIn(['in', []], tham_so['filters'].values())
        self.assertEqual(n.goi[0][1]['filters']['name'], ['in', ['MASS']])


@ca('#303: thiếu mã dừng trước DB')
def _thieu():
    Thu().test_thieu_ma_khong_doc_db()

@ca('#303: mã không có dừng trước BOM')
def _khong_co():
    Thu().test_ma_khong_co_dung_truoc_bom()

@ca('#303: không BOM không quét bảng con rộng')
def _rong():
    Thu().test_khong_bom_khong_quet_toan_bang_con()

@ca('#303: giữ trạng thái BOM huỷ và BOM chỉ còn trong bảng nổ')
def _lich_su():
    class DuLieu(Nguon):
        def get_all(self, loai, **kw):
            if loai == 'BOM Item':
                return [{'parent': 'BOM-HUY'}]
            if loai == 'BOM Explosion Item':
                assert kw['filters']['parenttype'] == 'BOM'
                return [{'parent': 'BOM-NO'}]
            if loai == 'BOM' and 'name' in kw['filters']:
                assert kw['filters']['name'] == ['in', ['BOM-HUY', 'BOM-NO']]
                return [{'name': 'BOM-HUY', 'docstatus': 2, 'is_active': 0},
                        {'name': 'BOM-NO', 'docstatus': 1, 'is_active': 1}]
            if loai == 'Item':
                assert 'default_bom' in kw['fields'] and 'custom_chang_btp' in kw['fields']
            return super().get_all(loai, **kw)
    k = doc(DuLieu(), ['MASS'])
    assert k['dong_cha'][0]['bom_docstatus'] == 2
    assert not k['dong_cha'][0]['dang_chay']
    assert k['la_con_trong_bang_no'][0]['dang_chay']

