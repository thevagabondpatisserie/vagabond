"""Hai kết nối cùng gửi APP giữ 7/10 triệu. Chỉ một bên được giữ tiền."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def _con(ten, thu_muc):
    _mo()
    root = Path(thu_muc)
    try:
        doc = frappe.get_doc("Vagabond Ho So TT", ten)
        (root / (ten + '.ready')).touch()
        han = time.monotonic() + 30
        while not (root / 'go').exists():
            if time.monotonic() > han:
                raise TimeoutError('Hết hạn chờ tiến trình APP')
            time.sleep(.02)
        try:
            doc.trang_thai = 'Cho ke toan'
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            kq = {'dat': True, 'pid': os.getpid(), 'name': ten}
        except Exception as e:
            frappe.db.rollback()
            kq = {'dat': False, 'pid': os.getpid(), 'name': ten, 'loi': str(e), 'loai': type(e).__name__}
        (root / (ten + '.json')).write_text(json.dumps(kq))
    finally:
        _dong()


def chay():
    root = Path(os.environ['VGB_ARTIFACTS']) / ('phan-bo-247-' + str(os.getpid()))
    root.mkdir()
    children, kq = [], {}
    try:
        _mo()
        try:
            from vagabond.khung.kiem_that.thu_phan_bo_app import _app
            from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua
            hd = _hoa_don_mua(10000000)
            ds = [_app(hd, 7000000, 'Nhap').name for _ in range(2)]
            frappe.db.commit()
        finally:
            _dong()
        for ten in ds:
            children.append(subprocess.Popen([sys.executable, '-m', 'vagabond.khung.bench_thu.phan_bo_247', '--con', ten, str(root)]))
        han = time.monotonic() + 40
        while not all((root / (ten + '.ready')).exists() for ten in ds):
            _dung(all(p.poll() is None for p in children), 'Con phải đến hàng rào')
            if time.monotonic() > han:
                raise TimeoutError('Chưa đủ hai kết nối')
            time.sleep(.02)
        (root / 'go').touch()
        for p in children:
            _dung(p.wait(timeout=90) == 0, 'Con phải ghi kết quả')
        ket = [json.loads((root / (ten + '.json')).read_text()) for ten in ds]
        _dung(len({r['pid'] for r in ket}) == 2 and sum(r['dat'] for r in ket) == 1, 'Đúng một APP được giữ 7 triệu')
        _mo()
        try:
            from vagabond.phan_bo_app import dang_giu
            _dung(float(dang_giu().get(hd.name, 0)) == 7000000, 'DB chỉ giữ 7 triệu')
            _dung(float(frappe.db.get_value('Purchase Invoice', hd.name, 'outstanding_amount')) == 10000000, 'Gửi duyệt chưa giảm công nợ')
            kq = {'dat': True, 'ket_qua': ket}
        finally:
            _dong()
    except Exception:
        kq['loi'] = traceback.format_exc()
        raise
    finally:
        for p in children:
            if p.poll() is None:
                p.kill()
        (root / 'ket-qua.json').write_text(json.dumps(kq, ensure_ascii=False))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        _con(sys.argv[2], sys.argv[3])
    else:
        chay()
