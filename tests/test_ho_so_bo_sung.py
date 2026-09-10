"""Giữ liên kết hóa đơn đến sau qua sửa/xóa dòng và nén PDF không mất trang."""
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest

class O(dict):
    __getattr__ = dict.get

class Loi(Exception):
    pass

def nem(s):
    raise Loi(s)

frappe = types.ModuleType('frappe')
frappe.whitelist = lambda: lambda f: f
frappe.throw = nem
utils = types.ModuleType('frappe.utils')
utils.cint = lambda x: int(x or 0)
sys.modules['frappe'] = frappe
sys.modules['frappe.utils'] = utils
spec = importlib.util.spec_from_file_location('bo_sung', Path(__file__).resolve().parents[1] / 'vagabond/ho_so_bo_sung.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class HoSo(O):
    def get_doc_before_save(self):
        return self.cu

def dong(ma='PI1'):
    return O(name='D1', idx=1, hoa_don_bo_sung=ma, cho_hoa_don=1)

class Kiem(unittest.TestCase):
    def test_xoa_link_cuoi_bi_chan(self):
        d = HoSo(dong=[dong('')], cu=O(dong=[dong()]))
        with self.assertRaises(Loi): m.kiem_bo_sung(d)

    def test_xoa_dong_co_link_bi_chan(self):
        d = HoSo(dong=[], cu=O(dong=[dong()]))
        with self.assertRaises(Loi): m.kiem_bo_sung(d)

    def test_ghi_de_bi_chan(self):
        d = HoSo(dong=[dong('PI2')], cu=O(dong=[dong()]))
        with self.assertRaises(Loi): m.kiem_bo_sung(d)

    def test_giu_link_khi_huy_ho_so(self):
        d = HoSo(dong=[dong()], cu=O(dong=[dong()]), trang_thai='Huy')
        m.kiem_bo_sung(d)

    def test_ho_so_cu_khong_link(self):
        m.kiem_bo_sung(HoSo(dong=[dong('')], cu=None))

    def test_doi_ncc_khi_giu_link_bi_chan(self):
        d = HoSo(dong=[dong()], nha_cung_cap='NCC2', cu=O(dong=[dong()], nha_cung_cap='NCC1'))
        with self.assertRaises(Loi): m.kiem_bo_sung(d)

    def test_bo_co_khi_giu_link_bi_chan(self):
        r = dong(); r['cho_hoa_don'] = 0
        d = HoSo(dong=[r], cu=O(dong=[dong()]))
        with self.assertRaises(Loi): m.kiem_bo_sung(d)

    def test_nen_khong_mat_trang(self):
        from pypdf import PdfReader, PdfWriter
        w = PdfWriter()
        w.add_blank_page(width=595, height=842)
        w.add_blank_page(width=842, height=595)
        b = io.BytesIO(); w.write(b)
        g = m.nen_pdf(b.getvalue())
        self.assertLessEqual(len(g), len(b.getvalue()))
        pages = PdfReader(io.BytesIO(g)).pages
        self.assertEqual(len(pages), 2)
        self.assertEqual(float(pages[1].mediabox.width), 842)

    def test_pdf_hong_bi_chan(self):
        with self.assertRaises(Exception): m.nen_pdf(b'not a pdf')

if __name__ == '__main__': unittest.main()
