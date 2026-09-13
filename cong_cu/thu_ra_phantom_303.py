"""Giữ công cụ chẩn đoán #303 chỉ đọc và không truy vấn lan khi thiếu mã."""
import unittest
from ra_phantom_303 import doc


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


if __name__ == '__main__':
    unittest.main()
