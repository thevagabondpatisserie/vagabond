"""Giữ nhãn/audit nguồn khi giảm việc giải mã JSON, không cần site thật."""
import ast
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch


def nap():
    tep = Path(__file__).parents[2] / 'kiem_banh.py'
    tree = ast.parse(tep.read_text())
    ham = {'_doc_kiem_dem_ghi', '_nguon_ton_cho_man', 'trang_thai_o'}
    bien = {'NGUON_MAY', 'NGUON_TAY', 'NGUON_TRONG', 'O_TON', 'NHAN_NGUON'}
    nodes = [n for n in tree.body if
        isinstance(n, ast.FunctionDef) and n.name in ham or
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in bien for t in n.targets)]
    ns = {'json': json}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(tep), 'exec'), ns)
    return ns['_nguon_ton_cho_man']


class ThuNguon(unittest.TestCase):
    def test_du_lieu_cu_va_hong_giu_nhan_nguon(self):
        ham = nap()
        for raw in (None, '', '{bad', '[]', '{}'):
            with self.subTest(raw=raw):
                d = {'kiem_dem_ghi': raw, 'nguon_ton_cu': 'Da kiem dem',
                     'nguon_ton_d2': 'Tu chuyen', 'nguon_ton_d1': '', 'may_chuyen_ton_cu': 4}
                cu = copy.deepcopy(d)
                with patch.object(json, 'loads', wraps=json.loads) as loads:
                    r = ham(d)
                    self.assertEqual(loads.call_count, 1)
                self.assertEqual(r, {
                    'ton_cu': {'trang_thai': 'Đã kiểm đếm', 'may_chuyen': 4, 'ai': '', 'luc': ''},
                    'ton_d2': {'trang_thai': 'Tự chuyển', 'may_chuyen': 0, 'ai': '', 'luc': ''},
                    'ton_d1': {'trang_thai': 'Cần xác nhận', 'may_chuyen': 0, 'ai': '', 'luc': ''}})
                self.assertEqual(d, cu)

    def test_giu_nguoi_luc_va_nguon_trong(self):
        r = nap()({'kiem_dem_ghi': json.dumps({'ton_cu': {'ai': 'Kho', 'luc': '2026-09-10 08:00'}}),
                   'nguon_ton_d1': 'Chua ghi'})
        self.assertEqual(r['ton_cu']['ai'], 'Kho')
        self.assertEqual(r['ton_cu']['luc'], '2026-09-10 08:00')
        self.assertEqual(r['ton_d1']['trang_thai'], '')
        self.assertEqual(r['ton_d2']['ai'], '')

    def test_khong_nuot_them_loi_du_lieu_con(self):
        with self.assertRaises(AttributeError):
            nap()({'kiem_dem_ghi': '{"ton_cu": "sai kieu"}'})


if __name__ == '__main__': unittest.main()
