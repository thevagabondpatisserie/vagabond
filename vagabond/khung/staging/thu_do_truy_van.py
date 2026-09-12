"""Giữ phép đo đúng khi request đồng thời, báo lỗi hoặc bị ngắt giữa chừng."""
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from .do_truy_van import boc_sql, boc_web, ghi_goi_nguon, _hien_tai


class ThuDo(unittest.TestCase):
    def test_ngat_va_doc_het_dong_dung_mot_lan(self):
        class Dong:
            def __init__(self):
                self.so_dong = 0
                self.so_dong_lai = 0
            def __iter__(self): return self
            def __next__(self):
                if self.so_dong == 2: raise StopIteration
                self.so_dong += 1
                return b'x'
            def close(self): self.so_dong_lai += 1
        with tempfile.TemporaryDirectory() as d:
            tep = Path(d) / 'do.jsonl'
            for api in (True, False):
                for ngat in (True, False):
                    with self.subTest(api=api, ngat=ngat):
                        dong = Dong()
                        def app(e, tra):
                            tra('200 OK', [])
                            return dong
                        g = boc_web(app, tep)({'PATH_INFO': '/api/method/thu' if api else '/bep'}, lambda *a: None)
                        if ngat:
                            next(g)
                            g.close()
                        else: self.assertEqual(b''.join(g), b'xx')
                        self.assertEqual(dong.so_dong_lai, 1)
                        self.assertIsNone(_hien_tai.get())
            self.assertEqual(len(tep.read_text().splitlines()), 2)

    def test_dong_thoi_khong_tron_va_khong_dem_ngoai(self):
        bar = Barrier(2)
        @boc_sql
        def sql(): return 1
        def app(e, tra):
            bar.wait(timeout=5)
            for _ in range(e['n']):
                sql()
                ghi_goi_nguon()
            tra('200 OK', [])
            return [b'ok']
        with tempfile.TemporaryDirectory() as d:
            tep = Path(d) / 'do.jsonl'
            w = boc_web(app, tep)
            def chay(n): return b''.join(w({'PATH_INFO': '/api/method/thu', 'n': n}, lambda *a: None))
            with ThreadPoolExecutor(2) as pool:
                self.assertEqual(list(pool.map(chay, [2, 7])), [b'ok', b'ok'])
            rows = [json.loads(s) for s in tep.read_text().splitlines()]
            self.assertEqual(sorted(r['so_truy_van'] for r in rows), [2, 7])
            self.assertEqual(sorted(r['so_goi_nguon'] for r in rows), [2, 7])
            self.assertTrue(all(r['ms'] >= r['sql_ms'] >= 0 for r in rows))
            sql()
            self.assertEqual(len(tep.read_text().splitlines()), 2)

    def test_loi_sql_khong_mat_so_do_va_reset_context(self):
        @boc_sql
        def sql(): raise ValueError('loi thu')
        def app(e, tra): sql()
        with tempfile.TemporaryDirectory() as d:
            tep = Path(d) / 'do.jsonl'
            with self.assertRaisesRegex(ValueError, 'loi thu'):
                list(boc_web(app, tep)({'PATH_INFO': '/api/method/thu'}, lambda *a: None))
            r = json.loads(tep.read_text())
            self.assertEqual(r['so_truy_van'], 1)
            self.assertIsNone(r['status'])
            self.assertIsNone(_hien_tai.get())


if __name__ == '__main__': unittest.main()
