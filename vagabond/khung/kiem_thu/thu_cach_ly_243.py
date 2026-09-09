"""#243: chạy chính khung với DB giao dịch giả để bắt rò trạng thái giữa ca.

Không thay cho bench: các ca này kiểm khung điều phối, không chứng minh
GL/SLE. Có cả ca phá savepoint và thử commit để tránh xanh giả khi mất khoá.
"""
from collections import deque
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
import sys

from vagabond.khung.kiem_thu.nen import ca, la, dung

TEP = Path(__file__).parents[1] / 'kiem_that' / 'nen.py'


class TuDien(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class CSDL:
    def __init__(self):
        self._disable_transaction_control = 2
        self.value_cache = {}
        self.du_lieu = {}
        self.moc = {}
        self.so_commit = 0
        for k in ('before_commit', 'after_commit', 'before_rollback', 'after_rollback'):
            setattr(self, k, SimpleNamespace(_functions=deque([k])))

    def count(self, dt):
        return sum(1 for d, n in self.du_lieu if d == dt)

    def exists(self, dt, name):
        return (dt, name) in self.du_lieu

    def sql(self, query, *a, **kw):
        cau = query.lower()
        if cau.startswith('savepoint '):
            self.moc[cau.split()[-1]] = deepcopy(self.du_lieu)
        elif cau.startswith('rollback to savepoint '):
            self.du_lieu = deepcopy(self.moc[cau.split()[-1]])
        elif cau == 'commit':
            self.moc.clear(); self.so_commit += 1

    def sql_ddl(self, *a, **kw):
        self._disable_transaction_control = 0
        self.sql('commit')

    def savepoint(self, name):
        self.sql('savepoint ' + name)

    def rollback(self, *, save_point):
        self.sql('rollback to savepoint ' + save_point)
        self.value_cache.clear()


def _nap(nguon=None):
    f = ModuleType('frappe')
    f.db = CSDL()
    f.flags = TuDien(vagabond_kiem_that='co cua caller', warehouse_account_map={'cu': 1})
    f.local = SimpleNamespace(request_cache={'cu': {}}, _realtime_log=['chuong caller'])
    f.bo_nho = {}
    def xoa(dt, name=None):
        f.bo_nho.pop((dt, name), None)
        f.db.after_commit._functions.append(('xoa', dt, name))
        f.db.after_rollback._functions.append(('xoa', dt, name))
    f.clear_document_cache = xoa
    ns = {}
    with patch.dict(sys.modules, frappe=f):
        exec(compile(nguon or TEP.read_text(), str(TEP), 'exec'), ns)
    return f, ns


def _hai_ca(nguon=None):
    f, n = _nap(nguon)
    def dau():
        f.db.du_lieu['Warehouse', 'kho1'] = 1
        n['_DA_TAO'].append(('Warehouse', 'kho1'))
        f.flags.warehouse_account_map = {'kho1': 'tk1'}
        f.clear_document_cache('Stock Settings')
        f.bo_nho['Stock Settings', None] = 'gia tri tam'
        f.local._realtime_log.append('chuong thu')
        for k in ('before_commit', 'after_commit', 'before_rollback', 'after_rollback'):
            getattr(f.db, k)._functions.append('job thu')
    def sau():
        n['dung']('không giữ kho trước', not f.flags.get('warehouse_account_map'))
        n['dung']('DB đã lùi', not f.db.du_lieu)
        n['dung']('cache cấu hình đã dọn', not f.bo_nho)
        n['la']('chuông không rò', f.local._realtime_log, ['chuong caller'])
        for k in ('before_commit', 'after_commit', 'before_rollback', 'after_rollback'):
            n['la']('không giữ callback ' + k, list(getattr(f.db,k)._functions), [k])
    n['CA'].extend([('dau', dau), ('sau', sau)])
    return f, n['chay_het'](im=0)


@ca('#243 khung: hai ca nối tiếp không giữ kho, cache, callback và chuông')
def _noi_tiep():
    f, k = _hai_ca()
    la('hai ca đạt', k['dat'], 2); la('không hỏng', k['hong'], 0)
    la('không rác', k['chung_tu_con_sot'], []); la('không lệch', k['so_luong_lech'], {})
    la('khoá caller nguyên', f.db._disable_transaction_control, 2)
    la('cờ caller nguyên', f.flags.vagabond_kiem_that, 'co cua caller')
    la('bản đồ caller nguyên', f.flags.warehouse_account_map, {'cu': 1})
    la('không commit', f.db.so_commit, 0)


@ca('#243 khung: lỗi ca vẫn lùi và ca sau chạy trên nền sạch')
def _loi_ca():
    f, n = _nap()
    def hong():
        f.db.du_lieu['Sales Invoice', 'thu'] = 1
        n['_DA_TAO'].append(('Sales Invoice','thu'))
        raise ValueError('Lỗi thật không được nuốt')
    def sau(): n['dung']('không SI dở', not f.db.du_lieu)
    n['CA'].extend([('hong', hong), ('sau', sau)])
    k=n['chay_het']()
    la('đỏ đúng ca', k['hong'], 1);la('ca sau chạy', k['dat'], 1)
    la('lùi sạch',k['sach'],1)
    dung('giữ nguyên lỗi', 'Lỗi thật không được nuốt' in str(k['ket_qua']))


@ca('#243 khung: ca import danh sách chứng từ vẫn dọn cache qua hai lượt')
def _giu_danh_sach():
    f,n=_nap()
    da_tao=n['_DA_TAO']
    def tao():
        da_tao.append(('File','unc-thu'))
        f.bo_nho['File','unc-thu']='cache thử'
    n['CA'].append(('tạo từ tham chiếu import',tao))
    for _ in range(2):
        k=n['chay_het']()
        la('lượt sạch',k['sach'],1)
        la('cache được dọn qua tham chiếu cũ',f.bo_nho,{})
        la('không nhân danh sách lượt trước',len(da_tao),1)


@ca('#243 khung: mất điểm lưu dừng lượt, không báo sạch dù đếm chưa lệch')
def _mat_moc():
    f,n=_nap();chay=[]
    def pha(): f.db.moc.clear()
    n['CA'].extend([('pha',pha),('khong duoc chay',lambda: chay.append(1))])
    k=n['chay_het']()
    la('dừng ngay',chay,[]);la('chưa chạy',k['chua_chay'],1)
    la('không xanh giả',k['sach'],0);la('đỏ',k['hong'],1)
    la('phục hồi khoá',f.db._disable_transaction_control,2)


@ca('#243 khung: chặn DDL và SQL thoát giao dịch trước khi mất savepoint')
def _chan_giao_dich():
    for cau in ('commit','/* hook */ COMMIT','rollback','START TRANSACTION','truncate tabX'):
        f,n=_nap()
        n['CA'].append((cau,lambda cau=cau: f.db.sql(cau)))
        k=n['chay_het']()
        la(cau+' đỏ',k['hong'],1);la(cau+' không commit',f.db.so_commit,0)
        la(cau+' vẫn lùi được',k['mat_diem_luu'],False)
    f,n=_nap();n['CA'].append(('ddl',lambda: f.db.sql_ddl('alter table')))
    k=n['chay_het']()
    la('DDL đỏ',k['hong'],1);la('DDL không mở khoá',f.db._disable_transaction_control,2)
    la('DDL không commit',f.db.so_commit,0)


@ca('#243 khung: ca hồi quy bắt được khi bỏ dọn cache hoặc callback')
def _pha_lai():
    goc=TEP.read_text()
    # Chạy cùng hai ca trên khung đã bị phá, không kiểm bằng chuỗi có mặt.
    for cu,moi in [('frappe.flags.pop("warehouse_account_map", None)','None'),
                   ('bo._functions = cu','pass'),
                   ('frappe.local._realtime_log = chuong_cu','pass')]:
        f,k=_hai_ca(goc.replace(cu,moi))
        dung('phá bị bắt: '+cu,k['hong']>0)


@ca('#243 khung: cửa POST ném lỗi khi chưa sạch để không tự commit chứng từ thử')
def _cua_khong_commit_rac():
    import ast
    cay=ast.parse((TEP.parent/'cua.py').read_text())
    ham=next(n for n in cay.body if isinstance(n,ast.FunctionDef) and n.name=='chay')
    ham.decorator_list=[]
    def nem(cau): raise RuntimeError(cau)
    kq={'sach':0,'mat_diem_luu':True}
    ns={'_chan':lambda:None,'nen':SimpleNamespace(chay_het=lambda **kw:kq),
        'frappe':SimpleNamespace(throw=nem,as_json=str)}
    exec(compile(ast.Module(body=[ham],type_ignores=[]),'<cua>', 'exec'),ns)
    try: ns['chay']()
    except RuntimeError as e: dung('có chẩn đoán', 'mat_diem_luu' in str(e))
    else: dung('phải ném lỗi ra request',False)
    kq['sach']=1
    la('ca đỏ nhưng rollback sạch vẫn trả chẩn đoán',ns['chay'](),kq)
