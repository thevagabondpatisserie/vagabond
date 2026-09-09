"""Hai tiến trình giành sao kê thật #247, chỉ chạy trên bench CI dùng một lần.

Giữ hàng rào sau khi mỗi tiến trình đã khoá hồ sơ riêng, trước khoá BT,
để tái hiện deadlock reviewer gặp. Có commit thật, không chạy trong nen.CA.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from unittest.mock import patch
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def _con(ho_so, giao_dich, thu_muc):
    _mo()
    from vagabond import doi_chieu_app as dc
    thu_muc = Path(thu_muc)
    goc = dc._ho_so
    def doi(*args, **kwargs):
        doc = goc(*args, **kwargs)
        (thu_muc / (ho_so + '.ready')).touch()
        han = time.monotonic() + 30
        while not (thu_muc / 'go').exists():
            if time.monotonic() > han:
                raise TimeoutError('Hết hạn hàng rào #247')
            time.sleep(0.02)
        return doc
    try:
        try:
            with patch.object(dc, '_ho_so', doi):
                dc.gan(ho_so, giao_dich)
            frappe.db.commit()
            kq = {'ho_so': ho_so, 'dat': True, 'pid': os.getpid()}
        except Exception as e:
            frappe.db.rollback()
            kq = {'ho_so': ho_so, 'dat': False, 'pid': os.getpid(), 'loi': str(e), 'loai': type(e).__name__}
        (thu_muc / (ho_so + '.json')).write_text(json.dumps(kq, ensure_ascii=False))
    finally:
        _dong()


def chay():
    thu_muc = Path(os.environ['VGB_ARTIFACTS']) / ('doi-chieu-247-' + str(os.getpid()))
    thu_muc.mkdir()
    tien_trinh = []
    kq = {}
    try:
        _mo()
        try:
            from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _nen
            from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _hoa_don_mua
            h, g = _nen(44444, tay=True)
            h2 = _ho_so_ncc([_hoa_don_mua(44444)])
            ds, gd = [h.name, h2.name], g.name
            frappe.db.commit()
        finally:
            _dong()
        for ten in ds:
            tien_trinh.append(subprocess.Popen([sys.executable, '-m', 'vagabond.khung.bench_thu.doi_chieu_247', '--con', ten, gd, str(thu_muc)]))
        han = time.monotonic() + 40
        while not all((thu_muc / (ten + '.ready')).exists() for ten in ds):
            _dung(all(p.poll() is None for p in tien_trinh), 'Tiến trình hỏng trước hàng rào')
            if time.monotonic() > han:
                raise TimeoutError('Hai tiến trình chưa sẵn sàng')
            time.sleep(0.02)
        (thu_muc / 'go').touch()
        for p in tien_trinh:
            _dung(p.wait(timeout=90) == 0, 'Tiến trình phải trả bằng chứng')
        ket = [json.loads((thu_muc / (ten + '.json')).read_text()) for ten in ds]
        _dung(len({r['pid'] for r in ket}) == 2, 'Phải là hai tiến trình riêng')
        _dung(sum(r['dat'] for r in ket) == 1, 'Chính xác một bên thắng')
        thua = next(r for r in ket if not r['dat'])
        _dung('Deadlock' not in thua['loi'] and thua['loai'] == 'ValidationError', 'Không lộ lỗi DB')
        _dung('Tải lại hồ sơ' in thua['loi'] or 'sử dụng' in thua['loi'], 'Câu lỗi phải chỉ việc tiếp theo')
        _mo()
        try:
            from vagabond import doi_chieu_app as dc, ho_so_tt as hs
            chu = frappe.get_all(dc.DT, filters={'ma_giao_dich': gd}, pluck='name')
            _dung(len(chu) == 1, 'DB chỉ có một chủ')
            for ten in ds:
                _dung(not hs._but_toan_cua_ho_so(ten), 'Chọn sao kê chưa được ghi sổ')
            g = frappe.get_doc(dc.BT, gd)
            _dung(not g.payment_entries and not g.allocated_amount and float(g.unallocated_amount) == 44444, 'Sao kê chưa phân bổ, không liên kết dở')
            try:
                dc.gan(thua['ho_so'], gd)
            except frappe.ValidationError as e:
                _dung(chu[0] in str(e), 'Thử lại phải nêu chủ hiện tại')
            else:
                raise AssertionError('Thử lại không được chiếm sao kê')
            kq = {'dat': True, 'ket_qua': ket, 'chu': chu, 'giao_dich': gd, 'but_toan': 0, 'lien_ket': 0}
        finally:
            _dong()
    except Exception:
        kq['loi'] = traceback.format_exc()
        raise
    finally:
        for p in tien_trinh:
            if p.poll() is None:
                p.kill()
                p.wait()
        (Path(os.environ['VGB_ARTIFACTS']) / 'doi-chieu-247.json').write_text(json.dumps(kq, ensure_ascii=False, indent=2))
        print(json.dumps(kq, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--con':
        _con(*sys.argv[2:])
    else:
        chay()
