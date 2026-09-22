"""Lỗi từng tờ phải nằm trong báo cáo đồng bộ, không tràn modal của Desk."""
import ast
from pathlib import Path
from types import SimpleNamespace
from vagabond.khung.kiem_thu.nen import ca, la, nem


def _nap(mat_rollback=False):
    p = Path(__file__).resolve().parents[2] / 'minvoice_chung_tu.py'
    ham = [n for n in ast.parse(p.read_text()).body
           if isinstance(n, ast.FunctionDef) and n.name == '_mot_to']
    da_ghi = []
    f = SimpleNamespace(local=SimpleNamespace(message_log=[{'message': 'Thông báo trước lượt'}]))
    def dung_phieu(r):
        f.local.message_log.append({'message': 'Cần khai quy cách mua', 'raise_exception': 1})
        raise ValueError('chưa xác định quy đổi')
    def lui():
        if mat_rollback:
            raise RuntimeError('rollback thất bại')
    f.db = SimpleNamespace(rollback=lui)
    f.get_traceback = lambda: 'traceback thử'
    f.log_error = lambda *a: None
    env = dict(frappe=f, khoi_dung_duoc=lambda x: False,
               _da_co_chung_tu=lambda ma: None, _trung_theo_so_hoa_don=lambda r: None,
               dung_hoa_don_mua=dung_phieu, _ghi_hong=lambda ma,e: da_ghi.append(ma),
               rut_gon_loi=str, LOAI_RA='Đầu ra')
    exec(compile(ast.Module(body=ham, type_ignores=[]), str(p), 'exec'), env)
    return env['_mot_to'], f, da_ghi


@ca('đồng bộ: lỗi đã bắt giữ nguyên lý do nhưng không tràn modal, giữ thông báo trước lượt')
def _loi_da_bat():
    chay, f, da_ghi = _nap()
    for ma in ('a', 'b'):
        la('lý do về báo cáo', chay({'name': ma, 'loai': 'Đầu vào'}), (0, 'chưa xác định quy đổi'))
    la('hai tờ lỗi đều có dấu để thử lại', da_ghi, ['a', 'b'])
    la('không rò lỗi đã xử lý vào response', f.local.message_log, [{'message': 'Thông báo trước lượt'}])


@ca('đồng bộ: rollback hỏng phải dừng, không ghi trạng thái lỗi rồi để caller commit phần dở')
def _rollback_hong():
    chay, f, da_ghi = _nap(True)
    nem('đẩy lỗi rollback ra caller', lambda: chay({'name': 'a', 'loai': 'Đầu vào'}), RuntimeError)
    la('không ghi thêm sau rollback hỏng', da_ghi, [])


@ca('hóa đơn âm: quà tặng giá0 không bị đảo qty âm thành dương, dòng mô tả không chặn phiếu')
def _dong_am_khong_tien():
    from vagabond.minvoice_chung_tu import dong_tu_hoa_don
    for d in ({'sluong': -1, 'dgia': 0, 'thtien': 0, 'tchat': 2},
              {'sluong': None, 'dgia': None, 'thtien': 0, 'ten': 'Điều chỉnh giảm'}):
        x = dong_tu_hoa_don(d, -1)
        la('qty âm hợp core', x['sl'], -1)
        la('không tạo thêm tiền', x['tien'], 0)
    x = dong_tu_hoa_don({'sluong': 2, 'dgia': 100, 'thtien': 200}, -1)
    la('dòng tiền dương trong điều chỉnh hỗn hợp không bị đổi dấu để ép qua', x['tien'], 200)


@ca('đồng bộ tự động: lỗi giao dịch phải tới worker, không trả thành công để commit phần dở')
def _worker_khong_nuot_loi():
    p = Path(__file__).resolve().parents[2] / 'minvoice_chung_tu.py'
    ham = [n for n in ast.parse(p.read_text()).body
           if isinstance(n, ast.FunctionDef) and n.name == 'chay_tu_dong']
    for rollback_hong in (False, True):
        da_lui = []
        def chay():
            raise RuntimeError('giao dịch dựng phiếu hỏng')
        def lui():
            da_lui.append(1)
            if rollback_hong:
                raise RuntimeError('rollback vẫn hỏng')
        f = SimpleNamespace(db=SimpleNamespace(exists=lambda *a: True, rollback=lui),
                            log_error=lambda *a, **k: None, get_traceback=lambda: 'traceback thử')
        env = dict(frappe=f, DT_HD='MInvoice Invoice', _chay=chay)
        exec(compile(ast.Module(body=ham, type_ignores=[]), str(p), 'exec'), env)
        nem('worker nhận exception cả khi rollback hỏng', env['chay_tu_dong'], RuntimeError)
        la('thử hoàn nguyên trước khi báo lỗi', da_lui, [1])


@ca('#352 Claude: Error Log của nhịp tự động còn lại sau khi worker Frappe rollback')
def _error_log_song_qua_worker():
    # Dựng đúng thứ tự của Frappe v16 ScheduledJobType.execute: gọi hàm, gặp
    # exception thì frappe.db.rollback() rồi mới ghi Failed. Bản insert thường
    # nằm trong giao dịch nên bị cuộn; bản defer_insert nằm ở hàng chờ redis.
    p = Path(__file__).resolve().parents[2] / 'minvoice_chung_tu.py'
    ham = [n for n in ast.parse(p.read_text()).body
           if isinstance(n, ast.FunctionDef) and n.name == 'chay_tu_dong']
    giao_dich, hang_cho = [], []
    def log_error(tb, tieu_de, defer_insert=False):
        (hang_cho if defer_insert else giao_dich).append(tieu_de)
    def lui():
        del giao_dich[:]
    def chay():
        raise RuntimeError('dựng phiếu hỏng')
    f = SimpleNamespace(db=SimpleNamespace(exists=lambda *a: True, rollback=lui),
                        log_error=log_error, get_traceback=lambda: 'tb')
    env = dict(frappe=f, DT_HD='MInvoice Invoice', _chay=chay)
    exec(compile(ast.Module(body=ham, type_ignores=[]), str(p), 'exec'), env)
    try:
        env['chay_tu_dong']()
    except RuntimeError:
        f.db.rollback()  # worker Frappe rollback lần nữa trước khi ghi Failed
    la('Error Log còn sau rollback của worker', giao_dich + hang_cho, ['minvoice_chung_tu: nhip tu dong vo loi'])


@ca('#352 Claude: tờ âm có dòng quà qty DƯƠNG giá 0 thì dòng đó mang qty âm, tiền 0; dòng có tiền giữ dấu')
def _qua_qty_duong_to_am():
    from vagabond.minvoice_chung_tu import dong_tu_hoa_don
    x = dong_tu_hoa_don({'ten': 'Quà', 'sluong': 2, 'dgia': 0, 'thtien': 0}, -1)
    la('dòng quà qty dương thành âm, tiền 0', (x['sl'], x['tien']), (-2, 0))
    x = dong_tu_hoa_don({'ten': 'Quà', 'sluong': 2, 'dgia': 0, 'thtien': 0}, 1)
    la('tờ dương giữ nguyên dòng quà', x['sl'], 2)
    x = dong_tu_hoa_don({'sluong': 2, 'dgia': 100, 'thtien': 200}, -1)
    la('dòng có tiền dương trong tờ âm không bị đảo', x['tien'], 200)
