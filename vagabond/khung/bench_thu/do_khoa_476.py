"""Đo P2 trước/sau trên bench dùng một lần. Không thay hàm khóa đang đo.

Các hàng rào chỉ dừng tiến trình ở biên hàm thật; SQL và Document chạy thật.
Mọi tiến trình hoàn nguyên thao tác đo, chỉ fixture riêng được commit.
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


def cho(folder, ten):
    han = time.monotonic() + 35
    while not (folder / ten).exists():
        if time.monotonic() > han:
            raise TimeoutError('Hàng rào ' + ten)
        time.sleep(.02)


def con(vai, thu_muc):
    folder = Path(thu_muc)
    cfg = json.loads((folder / 'cfg.json').read_text())
    _mo()
    ket = {'vai': vai, 'pid': os.getpid()}
    bat_dau = time.monotonic()
    try:
        frappe.db.sql('set session innodb_lock_wait_timeout=15')
        ket['isolation'] = frappe.db.sql('select @@tx_isolation')[0][0]
        from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs
        if vai == 'A':
            ham = dc._ho_so
            def dung_sau_khoa(*a, **kw):
                d = ham(*a, **kw)
                (folder / 'A.locked').touch()
                cho(folder, 'A.go')
                return d
            with patch.object(dc, '_ho_so', dung_sau_khoa):
                dc.gan(cfg['app'], json.dumps([{'name': cfg['x'], 'phan_bo': 60000}]))
        elif vai == 'B':
            ham = bs._cac_bo
            def do_quet(*a, **kw):
                (folder / 'B.scan').touch()
                return ham(*a, **kw)
            from vagabond.khung.kiem_that.thu_bo_sao_ke_595 import _noi
            g = frappe.get_doc('Bank Transaction', cfg['y'])
            pe = frappe.get_doc('Payment Entry', cfg['pe'])
            (folder / 'B.start').touch()
            t = time.monotonic()
            with patch.object(bs, '_cac_bo', do_quet):
                _noi(g, pe)
            ket['thao_tac_giay'] = time.monotonic() - t
            _dung(len(g.payment_entries) == 1 and not g.unallocated_amount, 'Lõi đã phân bổ BT Y')
            (folder / 'B.done').touch()
            if cfg['giu_B']:
                cho(folder, 'B.go')
        elif vai == 'C':
            from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc
            hd = frappe.get_doc('Purchase Invoice', cfg['hd_moi'])
            (folder / 'C.start').touch()
            t = time.monotonic()
            doc = _ho_so_ncc([hd])
            ket['thao_tac_giay'] = time.monotonic() - t
            ket['phieu_moi'] = doc.name
        ket['dat'] = True
    except Exception as e:
        ket.update(dat=False, loai=type(e).__name__, loi=str(e), traceback=traceback.format_exc())
    finally:
        ket['tong_giay'] = time.monotonic() - bat_dau
        _dong()
        (folder / (vai + '.json')).write_text(json.dumps(ket, ensure_ascii=False, indent=2))


def mot_ca(ten):
    folder = Path(os.environ['VGB_ARTIFACTS']) / ('do-khoa-476-' + ten)
    folder.mkdir()
    _mo()
    try:
        from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _nen
        from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua
        from vagabond.khung.kiem_that.thu_bo_sao_ke_595 import _pe
        # Có một hồ sơ đứng trước X trong chỉ mục chính, để đo vòng chờ.
        _nen(10000, tay=True)
        h, x = _nen(60000, tay=True)
        _, y = _nen(20000, tay=True)
        pe = _pe(20000, frappe.get_doc('Bank Account', y.bank_account))
        hd = _hoa_don_mua(30000)
        cfg = dict(app=h.name, x=x.name, y=y.name, pe=pe.name, hd_moi=hd.name, giu_B=ten=='tao_moi')
        frappe.db.commit()
    finally:
        _dong()
    (folder / 'cfg.json').write_text(json.dumps(cfg))
    ps = []
    def mo(vai):
        ps.append(subprocess.Popen([sys.executable, '-m', __spec__.name, '--con', vai, str(folder)]))
    try:
        if ten == 'tao_moi':
            mo('B'); cho(folder, 'B.done')
            mo('C'); cho(folder, 'C.start'); time.sleep(2)
            (folder / 'B.go').touch()
        else:
            mo('A'); cho(folder, 'A.locked')
            mo('B'); cho(folder, 'B.start'); cho(folder, 'B.scan')
            # Ca 1: A nhả khóa bằng rollback trước khi tiếp tục thao tác;
            # ca 2: A tiếp tục quét trong khi B đang chờ X.
            time.sleep(2)
            if ten == 'khong_lien_quan':
                ps[0].terminate(); ps[0].wait(timeout=10)
            else:
                (folder / 'A.go').touch()
        for p in ps:
            p.wait(timeout=45)
        return {p.stem: json.loads(p.read_text()) for p in folder.glob('?.json')}
    finally:
        for p in ps:
            if p.poll() is None:
                p.kill(); p.wait()


def chay():
    ket = {}
    try:
        for ten in ('khong_lien_quan', 'dao_thoi_diem', 'tao_moi'):
            ket[ten] = mot_ca(ten)
            print('DO KHOA ' + ten + ': ' + json.dumps(ket[ten], ensure_ascii=False), flush=True)
    finally:
        (Path(os.environ['VGB_ARTIFACTS']) / 'do-khoa-476.json').write_text(json.dumps(ket, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--con':
        con(*sys.argv[2:])
    else:
        chay()
