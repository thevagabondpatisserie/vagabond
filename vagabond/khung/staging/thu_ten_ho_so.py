"""Giữ bộ đổi tên hiện hành và giới hạn nhớ tên trong một request."""
import ast
import unittest
from pathlib import Path


class ThuTen(unittest.TestCase):
    def test_khong_doc_lap_va_khong_nho_sang_request_sau(self):
        tree = ast.parse((Path(__file__).parents[2] / 'ho_so_tt.py').read_text())
        ham = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_bo_doi_ten_trong_luot')
        calls = []
        ten = {'a': 'Tên thật', 'b': 'Tên nhân viên dự phòng', None: ''}
        def doi(ma):
            calls.append(ma)
            return ten[ma]
        ns = {'_ten_nguoi': doi}
        exec(compile(ast.Module(body=[ham], type_ignores=[]), 'ho_so_tt.py', 'exec'), ns)
        f = ns[ham.name]()
        for _ in range(300):
            self.assertEqual([f(x) for x in ('a', 'b', None)], ['Tên thật', 'Tên nhân viên dự phòng', ''])
        self.assertEqual(calls, ['a', 'b', None])
        ten['a'] = 'Tên mới'
        self.assertEqual(ns[ham.name]()('a'), 'Tên mới')
        self.assertEqual(calls, ['a', 'b', None, 'a'])


if __name__ == '__main__': unittest.main()
