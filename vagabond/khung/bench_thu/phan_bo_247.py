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


def _con_coc(ten, pe, ncc, hd, thu_muc):
    _mo()
    root = Path(thu_muc)
    try:
        from vagabond import coc_app
        # Cố ý mở snapshot trước hàng rào để thử cả trường hợp chờ khóa
        # xong mà truy vấn thường của lõi vẫn nhìn bản cũ trên MariaDB.
        frappe.db.get_value("Payment Entry", pe, "unallocated_amount")
        (root / (ten + '.ready')).touch()
        han = time.monotonic() + 30
        while not (root / 'go-coc').exists():
            if time.monotonic() > han:
                raise TimeoutError('Hết hạn chờ cọc')
            time.sleep(.02)
        try:
            r = coc_app.can_coc(ncc, pe, [{"hoa_don": hd, "so_tien": 2000000}], ten + '-request-247')
            frappe.db.commit()
            ket = {"dat": bool(r["ok"]), "pid": os.getpid(), "ket_qua": r}
        except Exception as e:
            frappe.db.rollback()
            ket = {"dat": False, "pid": os.getpid(), "loi": str(e)}
        (root / (ten + '.json')).write_text(json.dumps(ket))
    finally:
        _dong()


def _thu_coc(root):
    _mo()
    try:
        from vagabond.khung.kiem_that.thu_phan_bo_app import _coc
        hd, pe, _ = _coc()
        pe_ma, ncc, hd_ma = pe.name, hd.supplier, hd.name
        frappe.db.commit()
    finally:
        _dong()
    ds = ['coc-a', 'coc-b']
    ps = []
    try:
        for ten in ds:
            ps.append(subprocess.Popen([sys.executable, '-m', 'vagabond.khung.bench_thu.phan_bo_247',
                '--coc', ten, pe_ma, ncc, hd_ma, str(root)]))
        han = time.monotonic() + 40
        while not all((root / (ten + '.ready')).exists() for ten in ds):
            _dung(all(p.poll() is None for p in ps), 'Hai kết nối cọc phải tới hàng rào')
            if time.monotonic() > han:
                raise TimeoutError('Chưa đủ hai kết nối cọc')
            time.sleep(.02)
        (root / 'go-coc').touch()
        for p in ps:
            _dung(p.wait(timeout=90) == 0, 'Con cọc ghi đủ bằng chứng')
        ket = [json.loads((root / (ten + '.json')).read_text()) for ten in ds]
        _dung(sum(r['dat'] for r in ket) == 1, 'Chỉ cấn được một lần 2 triệu từ cọc3 triệu')
        _mo()
        try:
            _dung(float(frappe.db.get_value('Purchase Invoice', hd_ma, 'outstanding_amount')) == 8000000, 'Nợ chỉ giảm2 triệu')
            _dung(float(frappe.db.get_value('Payment Entry', pe_ma, 'unallocated_amount')) == 1000000, 'Cọc còn1 triệu')
            from vagabond.khung.kiem_that.thu_phan_bo_app import _app
            from vagabond import ho_so_tt as hs
            from frappe.utils.pdf import get_pdf
            from pypdf import PdfReader
            import io
            h = _app(frappe.get_doc("Purchase Invoice", hd_ma), 4000000)
            html = hs._to_app_html(h.name)
            pdf = get_pdf(html, options={"page-size": "A4", "orientation": "Portrait"})
            (root / "app-267-phan-bo.pdf").write_bytes(pdf)
            pages = PdfReader(io.BytesIO(pdf)).pages
            _dung(len(pages) == 1, "Tờ một hóa đơn và lịch sử cọc phải nằm gọn1 trang")
            text = " ".join(p.extract_text() or "" for p in pages)
            _dung(pe_ma in "".join(text.split()), "PDF thật có tham chiếu phiếu cọc, kể cả xuống dòng")
        finally:
            _dong()
        return ket
    finally:
        for p in ps:
            if p.poll() is None:
                p.kill()


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
            thua = next(r for r in ket if not r['dat'])
            _dung('Tải lại' in thua['loi'] or 'đề nghị' in thua['loi'], 'Lỗi chỉ dẫn bằng tiếng Việt')
            doc = frappe.get_doc('Vagabond Ho So TT', thua['name'])
            doc.trang_thai = 'Cho ke toan'
            try:
                doc.save(ignore_permissions=True)
            except frappe.ValidationError as e:
                _dung('3.000.000' in str(e), 'Thử lại phải báo chỉ còn được giữ 3 triệu')
            else:
                raise AssertionError('Bên thua không được giữ thêm 7 triệu khi thử lại')
            _dung(float(frappe.db.get_value('Purchase Invoice', hd.name, 'outstanding_amount')) == 10000000, 'Gửi duyệt chưa giảm công nợ')
            kq = {'dat': True, 'ket_qua': ket}
        finally:
            _dong()
        kq['can_coc_dong_thoi'] = _thu_coc(root)
    except Exception:
        kq['loi'] = traceback.format_exc()
        raise
    finally:
        for p in children:
            if p.poll() is None:
                p.kill()
        (root / 'ket-qua.json').write_text(json.dumps(kq, ensure_ascii=False))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--coc':
        _con_coc(*sys.argv[2:])
    elif len(sys.argv) > 1:
        _con(sys.argv[2], sys.argv[3])
    else:
        chay()
