"""#257: dữ liệu thanh toán tổng hợp cho driver HTTP, chỉ trên CI dùng một lần.

Không gọi hàm ghi nhận thanh toán trong lúc dựng; hành động đó thuộc UI.
"""
import json
import os
from pathlib import Path
from vagabond.khung.staging.van_don_ci import khoa


def tao():
    import frappe
    from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _nen
    khoa()
    frappe.set_user('Administrator')
    tep = Path(os.environ['VGB_ARTIFACTS']) / 'thanh-toan-fixture.json'
    if tep.exists():
        raise RuntimeError('Fixture thanh toán đã có, cần bench CI mới.')
    # Nền bench đã dựng công ty/NCC/dịch vụ. Giữ validation và UNC thật
    # (nội dung tệp ghi rõ giả lập); không mock controller thanh toán.
    h, g = _nen(12345, tay=True)
    if h.trang_thai != 'Da duyet' or h.ma_giao_dich:
        raise RuntimeError('Hồ sơ thử phải chưa được đối chiếu/ghi nhận.')
    from vagabond import ho_so_tt as hs
    if hs._but_toan_cua_ho_so(h.name) or g.payment_entries:
        raise RuntimeError('Fixture đã có thanh toán trước thao tác UI.')
    if float(g.unallocated_amount) != 12345:
        raise RuntimeError('Sao kê thử không còn đủ tiền để đối chiếu.')
    hd = frappe.get_doc('Purchase Invoice', h.dong[0].hoa_don)
    if hd.docstatus != 1 or float(hd.outstanding_amount) != 12345:
        raise RuntimeError('Hoá đơn nguồn thử không còn nợ đúng số tiền.')
    frappe.db.commit()
    tep.write_text(json.dumps({'ho_so': h.name, 'giao_dich': g.name,
        'hoa_don': hd.name, 'cong_ty': hd.company, 'tien': 12345,
        'ghi_chu': 'Dữ liệu tổng hợp CI; chưa thao tác UI, chưa đạt E2E'},
        ensure_ascii=False, indent=2))


def kiem():
    import frappe
    from vagabond import ho_so_tt as hs
    khoa()
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'thanh-toan-fixture.json').read_text())
    h = frappe.get_doc('Vagabond Ho So TT', f['ho_so'])
    g = frappe.get_doc('Bank Transaction', f['giao_dich'])
    hd = frappe.get_doc('Purchase Invoice', f['hoa_don'])
    assert h.trang_thai == 'Da thanh toan', 'Hồ sơ chưa thanh toán'
    assert h.ma_giao_dich == g.name, 'Mất giao dịch đã chọn'
    assert hd.docstatus == 1 and float(hd.outstanding_amount) == 0, 'Công nợ chưa hết'
    bo = hs._but_toan_cua_ho_so(h.name)
    assert len(bo) == 1, 'Phải có đúng một bút toán chi'
    assert g.status == 'Reconciled' and float(g.unallocated_amount) == 0, 'Sao kê chưa đối chiếu hết'
    assert len(g.payment_entries) == 1, 'Liên kết sao kê thiếu/trùng'
    b = bo[0]
    browser = json.loads((goc / 'thanh-toan-browser.json').read_text())
    assert browser['dat'] and browser['chan_bo_khi_con_but_toan'], 'UI chưa chạy đủ chuỗi'
    assert b['name'] == browser['but_toan_moi'], 'Bút toán cuối không đúng UI'
    cu = frappe.get_doc('Payment Entry', browser['but_toan_cu'])
    assert cu.docstatus == 2, 'Bút toán cũ chưa huỷ'
    # Sổ cái bất biến có thể giữ dòng đảo; tổng tác động phiếu cũ phải bằng0.
    gl_cu = frappe.get_all('GL Entry', filters={'voucher_type': 'Payment Entry',
        'voucher_no': cu.name, 'is_cancelled': 0}, fields=['account', 'debit', 'credit'], limit_page_length=0)
    tong_cu = {}
    for r in gl_cu:
        tong_cu[r.account] = tong_cu.get(r.account, 0) + float(r.debit) - float(r.credit)
    assert all(v == 0 for v in tong_cu.values()), 'Bút toán cũ còn tác động sổ cái'
    assert g.payment_entries[0].payment_document == b['doctype'], 'Sai loại bút toán'
    assert g.payment_entries[0].payment_entry == b['name'], 'Nối nhầm bút toán'
    doc = frappe.get_doc(b['doctype'], b['name'])
    assert doc.docstatus == 1, 'Bút toán chưa ghi sổ'
    tk_ngan_hang = frappe.db.get_value('Bank Account', g.bank_account, 'account')
    assert b['doctype'] == 'Payment Entry' and doc.payment_type == 'Pay', 'Sai loại chi tiền'
    assert doc.paid_from == tk_ngan_hang and doc.paid_to == hd.credit_to, 'Chi sai tài khoản ngân hàng/công nợ'
    assert doc.party_type == 'Supplier' and doc.party == hd.supplier, 'Sai nhà cung cấp'
    assert len(doc.references) == 1, 'Thừa/thiếu hoá đơn đối ứng'
    ref = doc.references[0]
    assert ref.reference_doctype == 'Purchase Invoice' and ref.reference_name == hd.name, 'Chi nhầm hoá đơn'
    assert float(ref.allocated_amount) == f['tien'], 'Phân bổ sai số tiền'
    assert str(doc.clearance_date) == str(g.date), 'Ngày đối chiếu sai'
    gl = frappe.get_all('GL Entry', filters={'voucher_type': b['doctype'],
        'voucher_no': b['name'], 'is_cancelled': 0}, fields=['account', 'party_type', 'party', 'debit', 'credit'], limit_page_length=0)
    assert gl, 'Thiếu sổ cái'
    no = sum(float(x.debit) for x in gl)
    co = sum(float(x.credit) for x in gl)
    assert no == co == f['tien'], 'Bút toán không cân hoặc sai số tiền'
    thuc = {}
    for r in gl:
        key = (r.account, r.party_type or '', r.party or '')
        thuc[key] = thuc.get(key, 0) + float(r.debit) - float(r.credit)
    thuc = {k: v for k, v in thuc.items() if v}
    assert thuc == {(hd.credit_to, 'Supplier', hd.supplier): f['tien'],
        (tk_ngan_hang, '', ''): -f['tien']}, 'Sổ cái sai tài khoản hoặc đối tượng'
    (goc / 'thanh-toan-db.json').write_text(json.dumps({'dat': True,
        'ho_so': h.name, 'but_toan': b, 'no': no, 'co': co,
        'con_no': 0, 'lien_ket': 1, 'pham_vi': 'ghi nhận, hủy, bỏ đối chiếu, ghi nhận lại'},
        ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        kiem()
    finally:
        frappe.destroy()
