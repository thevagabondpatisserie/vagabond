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
           and n.name in ('_keo', 'doc_trang', 'vo_ruot', 'chi_co_ma')]
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
    local = SimpleNamespace(message_log=[])
    db.local = local
    class Doc:
        def __init__(self, du):
            self.ma = du['ma_hd_id']; self.du = {}
        def update(self, du):
            self.du.update(du)
        def insert(self, **kw):
            db.ds[self.ma] = self.du.copy()
            if self.ma in hong:
                local.message_log.append({'message': 'hook lỗi', 'raise_exception': 1})
                raise ValueError('hook ghi một phần rồi lỗi')
    da_goi = []
    def goi(cd, ts):
        da_goi.append(ts['page'])
        return trang[ts['page']]
    env = dict(frappe=SimpleNamespace(local=local, db=db, get_doc=Doc, get_traceback=lambda: 'lỗi thử',
        log_error=lambda *a: db.loi.append(a)), cint=lambda n: int(n or 0),
        _cai_dat=lambda: dict(so_ngay=7, keo_vao=1, keo_ra=0), _goi_minvoice=goi,
        _du_lieu=lambda inv, loai: dict(so_hd=inv.get('shdon', 1)), _extra=lambda inv, loai: {},
        LOAI_VAO='Đầu vào', LOAI_RA='Đầu ra', DT_HD='MInvoice Invoice', TRANG_TOI_DA=tran)
    exec(compile(ast.Module(body=ham, type_ignores=[]), str(p), 'exec'), env)
    return lambda: env['_keo'](tu_ngay='01/08/2026', den_ngay='09/09/2026'), db, da_goi


def _to(ma, so=1):
    """Một tờ hoá đơn THẬT của nguồn: có mã, có số, có ngày lập.

    Từ v519 dòng nguồn không có cả số lẫn ngày bị coi là vật tạm và không
    được lưu (xem chi_co_ma). Các ca về phân trang, lỗi và rollback nói về
    hoá đơn thật, nên tờ mẫu phải có đủ ruột, đừng rút lại thành {'id': ma}.
    """
    return {'id': ma, 'shdon': so, 'tdlap': '2026-09-20T17:00:00Z'}


@ca('#227 kéo: một hóa đơn hỏng không nuốt tờ phía sau hoặc trang sau, retry không trùng')
def _mot_to_hong():
    chay, db, da_goi = _nap({1: dict(listInvoice=[_to('a'), _to('hong'), _to('b')], totalPage=2),
                            2: dict(listInvoice=[_to('c')], totalPage=2)}, hong={'hong'})
    kq = chay()
    la('đủ hai trang', da_goi, [1, 2])
    la('commit theo trang, không theo hóa đơn', db.so_commit, 2)
    la('giữ đúng ba tờ lành', sorted(db.da_ghi), ['a', 'b', 'c'])
    la('không đếm tờ rollback', kq['moi'], 3)
    la('báo chưa hoàn tất', kq['hoan_tat'], False)
    la('chỉ rõ tờ lỗi', kq['loi_hoa_don'], [{'loai': 'Đầu vào', 'trang': 1, 'ma': 'hong'}])
    la('chạy lại không tạo trùng', chay()['moi'], 0)
    la('DB vẫn đúng', sorted(db.da_ghi), ['a', 'b', 'c'])
    la('lỗi đã xử lý không phủ modal kết quả', db.local.message_log, [])


@ca('#227 kéo: payload lỗi, thiếu mã, trang rỗng giữa chừng và chạm trần phải báo chưa đủ')
def _phan_hoi():
    for payload in ({'error': 'hết phiên'}, {'listInvoice': {}},
                    {'listInvoice': [], 'totalPage': 2}, {'listInvoice': [], 'totalPage': 'sai'}):
        chay, db, _ = _nap({1: payload})
        la('không báo xanh payload sai', chay()['hoan_tat'], False)
        la('không ghi dữ liệu sai', db.da_ghi, {})
    chay, db, _ = _nap({1: dict(listInvoice=[{}, _to('a')], totalPage=1)})
    kq = chay()
    la('thiếu mã là lỗi có đếm', kq['so_loi_hoa_don'], 1)
    la('vẫn giữ tờ phía sau', sorted(db.da_ghi), ['a'])
    chay, db, _ = _nap({1: dict(listInvoice=[_to('a')], totalPage=2)}, tran=1)
    la('chạm trần không nhận đủ', chay()['hoan_tat'], False)
    la('trang đã commit vẫn giữ', sorted(db.da_ghi), ['a'])


@ca('#227 kéo: mất savepoint thì rollback cả trang, không đếm hoặc commit hóa đơn dở')
def _mat_diem():
    chay, db, da_goi = _nap({1: dict(listInvoice=[_to('a'), _to('hong')], totalPage=2)},
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


@ca('#227 + #519 nguồn chỉ trả mã: đếm riêng, KHÔNG lưu bản ghi, không cản tờ đầy đủ')
def _nguon_chua_du():
    # Đổi hợp đồng ở v519. Trước đó giữ lại mã để kéo lần sau, nhưng đo trên
    # site thật 23/09/2026 thì mã đó là vật tạm của M-Invoice, mỗi lượt một
    # mã mới, nên bản ghi giữ lại không bao giờ lành. Xem chi_co_ma().
    chay, db, _ = _nap({1: dict(listInvoice=[{'_id': 'rong', 'type': 'INPUT_ELECTRONIC_INVOICE'},
        {'id': 'du', 'shdon': 123, 'tdlap': '2026-09-20T17:00:00Z'}], totalPage=1)})
    # Fixture Doc dùng ma_hd_id; _du_lieu stub không suy số thật.
    kq = chay()
    la('một dòng chỉ có mã', kq['dong_chi_ma'], 1)
    la('KHÔNG đếm vào ô chờ nguồn, vì nó không phải lỗi', kq['nguon_chua_du'], 0)
    la('chỉ giữ tờ đầy đủ', sorted(db.da_ghi), ['du'])
    la('không đếm dòng chỉ có mã là tờ mới', kq['moi'], 1)
    la('không coi nguồn chờ là lỗi lưu hóa đơn', kq['so_loi_hoa_don'], 0)


@ca('#352 Claude: nguồn trả rút gọn cho tờ trong máy đã đủ số thì không đếm "chưa đủ"; tờ trong máy còn trống số thì vẫn đếm')
def _nguon_rut_gon_da_du():
    # Tái hiện đúng lời Codex trên 75fb6563: lượt 1 kéo đủ, lượt 2 nguồn trả
    # rút gọn cho cùng tờ. Bản cũ đếm 1 và dong_bo_ngay báo cam mãi.
    # 'trong' là VỎ RUỘT thật: có ngày lập, chưa có số. Đừng bỏ tdlap đi,
    # làm vậy là biến nó thành dòng chỉ có mã và từ v519 nó không được lưu,
    # ca kiểm sẽ nổ chứ không nói lên điều đang cần nói.
    trang = {1: dict(listInvoice=[{'id': 'du', 'shdon': 123, 'tdlap': '2026-09-20T17:00:00Z'},
        {'id': 'trong', 'shdon': 0, 'tdlap': '2026-09-21T17:00:00Z'}], totalPage=1)}
    chay, db, _ = _nap(trang)
    chay()
    db.ds['trong']['so_hd'] = ''  # tờ trong máy còn trống số
    db.commit()
    trang[1] = dict(listInvoice=[{'_id': 'du'}, {'_id': 'trong'}], totalPage=1)
    kq = chay()
    la('chỉ đếm tờ trong máy còn trống số', kq['nguon_chua_du'], 1)
    la('không ghi đè tờ đã đủ', db.da_ghi['du']['so_hd'], 123)
