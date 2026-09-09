"""Ba cửa kho #243 cần giao dịch thật, CHỈ trên bench dùng một lần.

Từ thư mục sites của bench:
    ../env/bin/python -m vagabond.khung.bench_thu.kho_tang_243

Có commit và hai tiến trình MariaDB riêng. Không nhập vào nen.CA, không
chạy bằng savepoint, không chạy trên site thật. Kết quả nằm trong
VGB_ARTIFACTS/kho-tang-243.json. Bench CI bị huỷ sau job.
"""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import socket
import sys
import time
import traceback

import frappe

SITE = 'bench-ci.localhost'
_KET_NOI = socket.socket.connect


def _noi_noi_bo(sock, dia_chi):
    if isinstance(dia_chi, tuple) and dia_chi[0] not in ('127.0.0.1', '::1', 'localhost'):
        raise RuntimeError('Bench cấm kết nối ra ngoài: %s' % dia_chi[0])
    return _KET_NOI(sock, dia_chi)


def _tep(hd):
    return hashlib.sha256(hd.encode()).hexdigest()


def _mo():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Chỉ chạy trong GitHub Actions trên bench dùng một lần.')
    socket.socket.connect = _noi_noi_bo
    frappe.init(site=SITE, sites_path='.')
    frappe.connect()
    if not frappe.conf.get('vagabond_bench_thu'):
        raise RuntimeError('Thiếu khoá vagabond_bench_thu.')
    frappe.set_user('Administrator')
    frappe.flags.vagabond_kiem_that = True


def _dong():
    frappe.db.rollback()
    frappe.destroy()


def _dung(dieu, ten):
    if not dieu:
        raise AssertionError(ten)


def _duyet(hd):
    from vagabond import hang_tang
    hd.save(ignore_permissions=True)
    hang_tang.duyet(hd.name, 'Kiểm bench giao dịch thật #243, không giao bánh')
    hd.reload()
    hd.flags.ignore_permissions = True


def _anh(hd):
    """Giữ cả tên dòng, số lượng và tiền để phát hiện bút toán thay/nhân đôi."""
    return {
        'status': frappe.db.get_value('Sales Invoice', hd, 'docstatus'),
        'sle': frappe.get_all('Stock Ledger Entry', filters={
            'voucher_type': 'Sales Invoice', 'voucher_no': hd},
            fields=['name', 'actual_qty', 'stock_value_difference', 'is_cancelled'], order_by='name'),
        'gl': frappe.get_all('GL Entry', filters={
            'voucher_type': 'Sales Invoice', 'voucher_no': hd},
            fields=['name', 'account', 'debit', 'credit', 'is_cancelled'], order_by='name'),
        'bundle': frappe.get_all('Serial and Batch Bundle', filters={
            'voucher_type': 'Sales Invoice', 'voucher_no': hd},
            fields=['name', 'docstatus', 'total_qty'], order_by='name'),
    }


def _tien(anh, cty):
    tk = frappe.db.get_value('Account', {'company': cty, 'account_number': '64181'}, 'name')
    gia = -sum(d.stock_value_difference for d in anh['sle'] if not d.is_cancelled)
    chi = sum(d.debit-d.credit for d in anh['gl'] if not d.is_cancelled and d.account == tk)
    _dung(gia > 0 and abs(gia-chi) < 0.01, '64181 phải bằng giá vốn thực SLE')
    _dung(abs(sum(d.debit-d.credit for d in anh['gl'] if not d.is_cancelled)) < 0.01, 'GL phải cân')


def _con(hd, thu_muc, mat_phan_hoi=False):
    _mo()
    try:
        doc = frappe.get_doc('Sales Invoice', hd)
        doc.flags.ignore_permissions = True
        thu_muc = Path(thu_muc)
        (thu_muc / (_tep(hd) + '.ready')).touch()
        han = time.monotonic() + 30
        while not (thu_muc / 'go').exists():
            if time.monotonic() > han:
                raise TimeoutError('Không nhận được hàng rào bắt đầu')
            time.sleep(0.02)
        try:
            doc.submit()
            frappe.db.commit()
            kq = {'hoa_don': hd, 'ghi_so': True, 'pid': os.getpid()}
        except Exception as e:
            frappe.db.rollback()
            kq = {'hoa_don': hd, 'ghi_so': False, 'pid': os.getpid(), 'loi': str(e)}
        if mat_phan_hoi:
            # Commit đã thành công nhưng không trả kết quả cho caller.
            # Không ném trong bench execute vì cửa đó có thể gọi lại hàm.
            _dung(kq['ghi_so'], 'Không mô phỏng mất phản hồi khi submit thực sự thất bại')
        else:
            (thu_muc / (_tep(hd) + '.json')).write_text(json.dumps(kq, ensure_ascii=False))
    finally:
        _dong()


def _tien_trinh(ds, ten, mat_phan_hoi=False):
    thu_muc = Path(os.environ['VGB_ARTIFACTS']) / ten
    thu_muc.mkdir(parents=True, exist_ok=False)
    tien_trinh = []
    try:
        for hd in ds:
            args = [sys.executable, '-m', 'vagabond.khung.bench_thu.kho_tang_243', '--con', hd, str(thu_muc)]
            if mat_phan_hoi:
                args.append('--mat-phan-hoi')
            tien_trinh.append(subprocess.Popen(args))
        han = time.monotonic() + 30
        while not all((thu_muc / (_tep(hd) + '.ready')).exists() for hd in ds):
            _dung(all(p.poll() is None for p in tien_trinh), 'Tiến trình con hỏng trước hàng rào')
            if time.monotonic() > han:
                raise TimeoutError('Hai tiến trình không tới hàng rào đúng hạn')
            time.sleep(0.02)
        (thu_muc / 'go').touch()
        for p in tien_trinh:
            _dung(p.wait(timeout=90) == 0, 'Tiến trình con thoát lỗi')
        if mat_phan_hoi:
            _dung(not (thu_muc / (_tep(ds[0]) + '.json')).exists(), 'Caller không nhận phản hồi')
            return []
        return [json.loads((thu_muc / (_tep(hd) + '.json')).read_text()) for hd in ds]
    finally:
        for p in tien_trinh:
            if p.poll() is None:
                p.kill()
                p.wait()


def dong_thoi():
    from vagabond.khung.kiem_that.thu_hang_tang_kho_243 import _nen
    _mo()
    try:
        hd, kho, lo = _nen()
        hd.items[0].qty = 4
        _duyet(hd)
        hd2 = frappe.copy_doc(hd)
        hd2.insert(ignore_permissions=True)
        _duyet(hd2)
        ds, mon, cty = [hd.name, hd2.name], hd.items[0].item_code, hd.company
        frappe.db.commit()
    finally:
        _dong()
    kq = _tien_trinh(ds, 'dong-thoi-243-' + frappe.generate_hash(length=6))
    _mo()
    try:
        _dung(len({d['pid'] for d in kq}) == 2, 'Phải là hai tiến trình riêng')
        _dung(sum(d['ghi_so'] for d in kq) == 1, 'Chỉ một hoá đơn 4 bánh được ghi sổ khi tồn 5')
        thang = next(d['hoa_don'] for d in kq if d['ghi_so'])
        thua = next(d['hoa_don'] for d in kq if not d['ghi_so'])
        a, b = _anh(thang), _anh(thua)
        _dung(a['status'] == 1 and b['status'] == 0, 'Một đã ghi, một nháp')
        _dung(sum(d.actual_qty for d in a['sle']) == -4, 'Chỉ xuất 4 bánh')
        _dung(not b['sle'] and not b['gl'] and not b['bundle'], 'Hoá đơn bị chặn không để lại SLE/GL/bundle')
        _dung(frappe.db.get_value('Bin', {'item_code': mon, 'warehouse': kho}, 'actual_qty') == 1, 'Tồn còn 1, không âm')
        # Nếu lượt tranh chấp gặp deadlock thì thử lại chứng từ thua sau
        # khi giao dịch thắng đã commit: phải bị chặn vì thiếu tồn.
        lai = frappe.get_doc('Sales Invoice', thua)
        lai.flags.ignore_permissions = True
        try:
            lai.submit()
        except frappe.ValidationError as e:
            _dung(kho in str(e) and 'không xuất âm' in str(e), 'Lần thử lại phải bị chặn đúng vì thiếu tồn')
        else:
            raise AssertionError('Hoá đơn thua không được ghi sổ khi chỉ còn 1 bánh')
        _dung(_anh(thua) == b, 'Thử lại hoá đơn thua không để lại chứng từ dở')
        _tien(a, cty)
        return {'dat': True, 'ket_qua_con': kq, 'thang': a, 'thua': b, 'kho': kho, 'lo': lo}
    finally:
        _dong()


def nhieu_dong_nhieu_lo():
    from vagabond.khung.kiem_that.thu_hang_tang_kho_243 import _nen
    from vagabond.khung.kiem_that.thu_ma_cap_so import _lo_thu
    from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
    _mo()
    try:
        hd, kho, lo1 = _nen()
        mon = hd.items[0].item_code
        lo2 = _lo_thu(mon).name
        ph = make_stock_entry(item_code=mon, qty=3, company=hd.company,
            to_warehouse=kho, rate=18000, do_not_save=True)
        ph.items[0].batch_no = lo2
        ph.items[0].use_serial_batch_fields = 1
        ph.insert(ignore_permissions=True)
        ph.submit()
        hd.set_posting_time = 1
        hd.posting_date = frappe.utils.today()
        hd.posting_time = frappe.utils.nowtime()
        hd.items[0].qty = 4
        hd.append('items', {'item_code': mon, 'qty': 4, 'rate': 108000})
        _duyet(hd)
        hd.submit()
        hd.reload()
        a = _anh(hd.name)
        _dung(sum(d.actual_qty for d in a['sle']) == -8, 'Hai dòng phải xuất đủ 8')
        _dung(frappe.db.get_value('Bin', {'item_code': mon, 'warehouse': kho}, 'actual_qty') == 0, 'Tồn hai lô phải hết')
        tong = {}
        for d in hd.items:
            _dung(bool(d.serial_and_batch_bundle), 'Mỗi dòng cần bundle')
            bo = frappe.get_doc('Serial and Batch Bundle', d.serial_and_batch_bundle)
            _dung(sum(abs(e.qty) for e in bo.entries) == 4, 'Bundle mỗi dòng đúng 4 bánh')
            for e in bo.entries:
                tong[e.batch_no] = tong.get(e.batch_no, 0) + abs(e.qty)
        _dung(tong == {lo1: 5, lo2: 3}, 'Không dùng lại tồn lô giữa hai dòng')
        _tien(a, hd.company)
        frappe.db.commit()
        return {'dat': True, 'hoa_don': hd.name, 'phan_bo': tong, 'anh': a}
    finally:
        _dong()


def mat_phan_hoi():
    from vagabond.khung.kiem_that.thu_hang_tang_kho_243 import _nen
    _mo()
    try:
        hd, kho, lo = _nen()
        ten, cty = hd.name, hd.company
        frappe.db.commit()
    finally:
        _dong()
    _tien_trinh([ten], 'mat-phan-hoi-243-' + frappe.generate_hash(length=6), mat_phan_hoi=True)
    _mo()
    try:
        truoc = _anh(ten)
        _dung(truoc['status'] == 1, 'Commit phải tồn tại dù caller không nhận phản hồi')
        _dung(sum(d.actual_qty for d in truoc['sle']) == -2, 'Lần đầu xuất đúng 2')
        for _ in range(2):
            hd = frappe.get_doc('Sales Invoice', ten)
            hd.flags.ignore_permissions = True
            try:
                hd.submit()
            except frappe.ValidationError:
                pass
            frappe.db.commit()
            _dung(_anh(ten) == truoc, 'Thử lại sau reload không thêm hoặc sửa dòng SLE/GL/bundle')
        _tien(truoc, cty)
        return {'dat': True, 'hoa_don': ten, 'anh': truoc, 'lan_thu_lai': 2}
    finally:
        _dong()


def chay():
    tep = Path(os.environ['VGB_ARTIFACTS']) / 'kho-tang-243.json'
    kq = {}
    try:
        for ten, ham in [('dong_thoi', dong_thoi), ('nhieu_dong_nhieu_lo', nhieu_dong_nhieu_lo), ('mat_phan_hoi', mat_phan_hoi)]:
            kq[ten] = ham()
            tep.write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
            print('PASS ' + ten, flush=True)
    except Exception:
        kq['loi'] = traceback.format_exc()
        tep.write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
        raise


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--con':
        _con(sys.argv[2], sys.argv[3], '--mat-phan-hoi' in sys.argv)
    else:
        chay()
