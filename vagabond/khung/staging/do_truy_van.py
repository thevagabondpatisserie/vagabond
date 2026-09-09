"""Đo API trên bench CI để tối ưu bằng số liệu, không lưu SQL/dữ liệu/người dùng.

ContextVar cách ly request của máy chủ threaded. Không dùng số đếm toàn cục
vì hai màn mở cùng lúc sẽ làm sai phép đo. Chỉ cài sau khoá site thử.
"""
import json
from contextvars import ContextVar
from functools import wraps
from threading import Lock
from time import perf_counter

_hien_tai = ContextVar('vgb_do_api', default=None)
_khoa_ghi = Lock()


def boc_sql(ham):
    @wraps(ham)
    def goi(*args, **kwargs):
        do = _hien_tai.get()
        if do is None:
            return ham(*args, **kwargs)
        dau = perf_counter()
        do['so_truy_van'] += 1
        try:
            return ham(*args, **kwargs)
        finally:
            do['sql_ms'] += (perf_counter() - dau) * 1000
    return goi


def ghi_goi_nguon():
    """Gateway HTTP giả ghi số lần nguồn trong đúng request, không lưu payload."""
    do = _hien_tai.get()
    if do is not None:
        do['so_goi_nguon'] += 1


def gan():
    from vagabond.khung.staging.van_don_ci import khoa
    khoa()
    from frappe.database.database import Database
    if getattr(Database.sql, '_vgb_do', False):
        raise RuntimeError('Bộ đo đã cài; cần kiểm lifecycle CI.')
    Database.sql = boc_sql(Database.sql)
    Database.sql._vgb_do = True


def boc_web(ung_dung, tep):
    def phuc_vu(environ, start_response):
        duong = environ.get('PATH_INFO', '')
        if not duong.startswith('/api/method/'):
            ket_ngoai = ung_dung(environ, start_response)
            try:
                for chunk in ket_ngoai:
                    yield chunk
            finally:
                if hasattr(ket_ngoai, 'close'):
                    ket_ngoai.close()
            return
        do = {'duong': duong, 'status': None, 'so_truy_van': 0, 'sql_ms': 0.0, 'so_goi_nguon': 0}
        moc = _hien_tai.set(do)
        dau = perf_counter()
        ket = None
        def tra(status, headers, exc_info=None):
            do['status'] = int(status.split()[0])
            return start_response(status, list(headers) + [('X-VGB-CI-Source-Calls', str(do['so_goi_nguon']))], exc_info)
        try:
            ket = ung_dung(environ, tra)
            for chunk in ket:
                yield chunk
        finally:
            try:
                if ket is not None and hasattr(ket, 'close'):
                    ket.close()
            finally:
                do['ms'] = (perf_counter() - dau) * 1000
                _hien_tai.reset(moc)
                with _khoa_ghi:
                    with tep.open('a') as f:
                        f.write(json.dumps(do) + '\n')
    return phuc_vu
