"""Chạy đúng vòng kéo với DB có savepoint giả, bắt lỗi một tờ làm mất cả trang."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from vagabond.khung.kiem_thu.nen import ca, la, dung


def _nap(trang, hong=(), tran=300, mat_diem=False, ma_nguon=None):
    p = Path(__file__).resolve().parents[2] / 'minvoice_dong_bo.py'
    cay = ast.parse(ma_nguon or p.read_text())
    ham = [n for n in cay.body if isinstance(n, ast.FunctionDef)
           and n.name in ('_keo', 'doc_trang', 'vo_ruot')]
    class DB:
        def __init__(self):
            self.ds = {}; self.da_ghi = {}; self.diem = {}; self.loi = []; self.so_commit = 0
        def savepoint(self, ten):
            self.diem[ten] = deepcopy(self.ds)
        def rollback(self, save_point=None):
            if save_point and mat_diem:
                raise RuntimeError('mất điểm lưu')
            self.ds = deepcopy(self.diem[save_point] if save_point else self.da_ghi)
        def commit(self):
            self.so_commit += 1
            self.da_ghi = deepcopy(self.ds)
        def exists(self, loai, ma):
            return ma in self.ds
        def get_value(self, loai, ma, o):
            return self.ds[ma].get(o)
        def set_value(self, loai, ma, du):
            self.ds[ma].update(du)
    db = DB()
    class Doc:
        def __init__(self, du):
            self.ma = du['ma_hd_id']; self.du = {}
        def update(self, du):
            self.du.update(du)
        def insert(self, **kw):
            db.ds[self.ma] = self.du.copy()
            if self.ma in hong:
                raise ValueError('hook ghi một phần rồi lỗi')
    da_goi = []
    def goi(cd, ts):
        da_goi.append(ts['page'])
        return trang[ts['page']]
    env = dict(frappe=SimpleNamespace(db=db, get_doc=Doc, get_traceback=lambda: 'lỗi thử',
        log_error=lambda *a: db.loi.append(a)), cint=lambda n: int(n or 0),
        _cai_dat=lambda: dict(so_ngay=7, keo_vao=1, keo_ra=0), _goi_minvoice=goi,
        _du_lieu=lambda inv, loai: dict(so_hd=inv.get('shdon', 1)), _extra=lambda inv, loai: {},
        LOAI_VAO='Đầu vào', LOAI_RA='Đầu ra', DT_HD='MInvoice Invoice', TRANG_TOI_DA=tran)
    exec(compile(ast.Module(body=ham, type_ignores=[]), str(p), 'exec'), env)
    return lambda: env['_keo'](tu_ngay='01/08/2026', den_ngay='09/09/2026'), db, da_goi


@ca('#227 kéo: một hóa đơn hỏng không nuốt tờ phía sau hoặc trang sau, retry không trùng')
def _mot_to_hong():
    chay, db, da_goi = _nap({1: dict(listInvoice=[{'id': 'a'}, {'id': 'hong'}, {'id': 'b'}], totalPage=2),
                            2: dict(listInvoice=[{'id': 'c'}], totalPage=2)}, hong={'hong'})
    kq = chay()
    la('đủ hai trang', da_goi, [1, 2])
    la('commit theo trang, không theo hóa đơn', db.so_commit, 2)
    la('giữ đúng ba tờ lành', sorted(db.da_ghi), ['a', 'b', 'c'])
    la('không đếm tờ rollback', kq['moi'], 3)
    la('báo chưa hoàn tất', kq['hoan_tat'], False)
    la('chỉ rõ tờ lỗi', kq['loi_hoa_don'], [{'loai': 'Đầu vào', 'trang': 1, 'ma': 'hong'}])
    la('chạy lại không tạo trùng', chay()['moi'], 0)
    la('DB vẫn đúng', sorted(db.da_ghi), ['a', 'b', 'c'])


@ca('#227 kéo: payload lỗi, thiếu mã, trang rỗng giữa chừng và chạm trần phải báo chưa đủ')
def _phan_hoi():
    for payload in ({'error': 'hết phiên'}, {'listInvoice': {}},
                    {'listInvoice': [], 'totalPage': 2}, {'listInvoice': [], 'totalPage': 'sai'}):
        chay, db, _ = _nap({1: payload})
        la('không báo xanh payload sai', chay()['hoan_tat'], False)
        la('không ghi dữ liệu sai', db.da_ghi, {})
    chay, db, _ = _nap({1: dict(listInvoice=[{}, {'id': 'a'}], totalPage=1)})
    kq = chay()
    la('thiếu mã là lỗi có đếm', kq['so_loi_hoa_don'], 1)
    la('vẫn giữ tờ phía sau', sorted(db.da_ghi), ['a'])
    chay, db, _ = _nap({1: dict(listInvoice=[{'id': 'a'}], totalPage=2)}, tran=1)
    la('chạm trần không nhận đủ', chay()['hoan_tat'], False)
    la('trang đã commit vẫn giữ', sorted(db.da_ghi), ['a'])


@ca('#227 kéo: mất savepoint thì rollback cả trang, không đếm hoặc commit hóa đơn dở')
def _mat_diem():
    chay, db, da_goi = _nap({1: dict(listInvoice=[{'id': 'a'}, {'id': 'hong'}], totalPage=2)},
                          hong={'hong'}, mat_diem=True)
    kq = chay()
    la('không commit phần dở', db.da_ghi, {})
    la('không báo đã thêm tờ rollback', kq['moi'], 0)
    la('không tiếp trang khi rollback hỏng', da_goi, [1])
    la('phải báo lỗi loại', kq['loi_o_loai'], ['Đầu vào'])


@ca('#227 kéo: trang rỗng hợp lệ là hoàn tất, không báo lỗi giả')
def _rong():
    chay, db, da_goi = _nap({1: dict(listInvoice=[], totalPage=0)})
    la('hoàn tất thật', chay()['hoan_tat'], True)
    la('chỉ hỏi một trang', da_goi, [1])
