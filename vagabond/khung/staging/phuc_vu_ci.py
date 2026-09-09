"""#257: phục vụ app thật ở loopback CI, không mở staging ra Internet.

Dùng cùng bench/core của ca tích hợp. Không chạy worker; chặn kết nối ra
ngoài ở tầng socket để tác vụ web không vô tình gọi dịch vụ thật.
"""
import os
import socket
import json
import hashlib
from pathlib import Path



def tao_cau_truc_cu():
    """Trường Desk cũ chưa thuộc truong_tu_them; chỉ dựng trên CI trắng.

    Đọc metadata trên Desk ngày09/09/2026, không sửa schema production.
    Chỉ dùng metadata đã đọc; thiếu loại chứng từ cũ vẫn phải xử lý riêng.
    """
    import frappe
    from vagabond.khung.staging.van_don_ci import khoa
    khoa()
    frappe.set_user('Administrator')
    mau = json.loads(Path(__file__).with_name('cau_truc_cu.json').read_text())
    # Bảng con trước bảng cha; không dựng bảng rỗng chỉ để hết lỗi get_list.
    # Không ghi đè DocType đã tồn tại trên một nền không rõ nguồn.
    for row in mau['doctypes']:
        if frappe.db.exists('DocType', row['name']):
            raise RuntimeError('DocType cũ đã tồn tại, cần kiểm nền CI: ' + row['name'])
        for perm in row['permissions']:
            if not frappe.db.exists('Role', perm['role']):
                frappe.get_doc({'doctype': 'Role', 'role_name': perm['role']}).insert()
        doc = frappe.get_doc(dict(row, doctype='DocType')).insert()
        doc.reload()
        for key in ('custom', 'istable', 'is_submittable', 'autoname', 'title_field'):
            if (doc.get(key) or '') != (row[key] or ''):
                raise RuntimeError('Thuộc tính DocType khác mẫu: ' + row['name'] + '/' + key)
        if len(doc.permissions) != len(row['permissions']):
            raise RuntimeError('Số dòng quyền khác mẫu: ' + row['name'])
        for actual, expected in zip(doc.permissions, row['permissions']):
            for key, value in expected.items():
                if actual.get(key) != value:
                    raise RuntimeError('Quyền DocType khác mẫu: ' + row['name'] + '/' + key)
        for expected in row['fields']:
            actual = next((f for f in doc.fields if f.fieldname == expected['fieldname']), None)
            if actual is None:
                raise RuntimeError('Thiếu trường sau dựng DocType: ' + row['name'])
            for key in ('fieldtype', 'options', 'reqd', 'read_only', 'default'):
                a, b = actual.get(key), expected[key]
                if key in ('options', 'default'):
                    a, b = a or '', b or ''
                if a != b:
                    raise RuntimeError('DocType khác mẫu đã xác minh: ' + row['name'] + '/' + expected['fieldname'] + '/' + key)
    for row in mau['fields']:
        ten = row['dt'] + '-' + row['fieldname']
        if not frappe.db.exists('Custom Field', ten):
            frappe.get_doc(dict(row, doctype='Custom Field')).insert()
        f = frappe.get_doc('Custom Field', ten)
        for key in ('fieldtype', 'options', 'reqd', 'read_only'):
            actual, expected = f.get(key), row[key]
            if key == 'options':
                actual, expected = actual or '', expected or ''
            if actual != expected:
                raise RuntimeError('Schema fixture khác metadata đã xác minh: ' + ten + '/' + key)
    frappe.db.commit()
    frappe.clear_cache()
    # Gọi đúng cửa boot thay vì đợi10 màn timeout cùng một lỗi thiếu nền.
    from vagabond.nhan_su import khoi_dong
    kq = khoi_dong()
    if not isinstance(kq.get('nhom'), list) or not isinstance(kq.get('kho'), list):
        raise RuntimeError('API khởi động không trả danh mục hợp lệ.')


def tao_trang():
    """Migrate chỉ cập nhật Web Page có sẵn; CI trắng phải dựng nền từ repo."""
    import frappe
    from vagabond import trang
    from vagabond.khung.staging.van_don_ci import khoa
    khoa()
    frappe.set_user('Administrator')
    bang = []
    for route in ('bep', 'kiem-banh'):
        if frappe.db.exists('Web Page', {'route': route}):
            raise RuntimeError('Trang fixture đã có, cần kiểm nền CI thay vì ghi đè.')
        noi_dung = trang.doc_mot(route)
        if not noi_dung.get('main_section_html') or not noi_dung.get('javascript'):
            raise RuntimeError('Thiếu nội dung trang trong repo: ' + route)
        d = frappe.get_doc(dict(noi_dung, doctype='Web Page', route=route))
        d.insert(ignore_permissions=True)
        d.reload()
        # Chốt byte nội dung dùng thật, không chèn script thay thế vào browser.
        for o, _ in trang.O_NOI_DUNG:
            if (d.get(o) or '') != (noi_dung.get(o) or ''):
                raise RuntimeError('Nội dung Web Page khác repo: ' + route + '/' + o)
        bang.append({'route': route, 'name': d.name, 'published': d.published,
            'javascript_sha256': hashlib.sha256(d.javascript.encode()).hexdigest()})
    frappe.db.commit()
    frappe.clear_cache()
    (Path(os.environ['VGB_ARTIFACTS']) / 'web-pages.json').write_text(json.dumps(bang))


def chan_mang():
    ket_noi = socket.socket.connect
    def noi_bo(sock, dia_chi):
        if isinstance(dia_chi, tuple) and dia_chi[0] not in ('127.0.0.1', '::1', 'localhost'):
            raise RuntimeError('Staging CI chặn kết nối ngoài.')
        return ket_noi(sock, dia_chi)
    socket.socket.connect = noi_bo
    ket_noi_ex = socket.socket.connect_ex
    def noi_bo_ex(sock, dia_chi):
        if isinstance(dia_chi, tuple) and dia_chi[0] not in ('127.0.0.1', '::1', 'localhost'):
            raise RuntimeError('Staging CI chặn kết nối ngoài.')
        return ket_noi_ex(sock, dia_chi)
    socket.socket.connect_ex = noi_bo_ex


def chay():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Chỉ dùng runner CI riêng.')
    chan_mang()
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        if not all(frappe.conf.get(k) for k in ('vagabond_bench_thu', 'mute_emails', 'disable_scheduler')):
            raise RuntimeError('Thiếu khoá site thử hoặc khoá gửi ra ngoài.')
        # Setup wizard có thể đã đổi mật khẩu; chỉ đặt lại sau khoá site thử.
        from frappe.utils.password import update_password
        update_password('Administrator', 'bench-only-admin')
        frappe.db.commit()
        tao_cau_truc_cu()
        tao_trang()
        if os.environ.get('VGB_STAGING_VAN_DON') == '1':
            from vagabond.khung.staging.van_don_ci import tao
            from vagabond.khung.staging.nguon_pancake import gan
            thu = tao()
            gan(thu['don'], Path(os.environ['VGB_ARTIFACTS']) / 'pancake-http.jsonl')
        if os.environ.get('VGB_STAGING_NHAN') == '1':
            from vagabond.khung.staging.nhan_hang_ci import tao as tao_nhan
            tao_nhan()
        if os.environ.get('VGB_STAGING_SAN_XUAT') == '1':
            from vagabond.khung.staging.san_xuat_ci import tao as tao_sx
            tao_sx()
        if os.environ.get('VGB_STAGING_HANG_TANG') == '1':
            from vagabond.khung.staging.hang_tang_ci import tao as tao_tang
            tao_tang()
        if os.environ.get('VGB_STAGING_THANH_TOAN') == '1':
            from vagabond.khung.staging.thanh_toan_ci import tao as tao_tt
            tao_tt()
    finally:
        frappe.destroy()
    from frappe.app import application
    from werkzeug.serving import run_simple
    # Header site cố định tại gateway, không nhận chọn site từ client.
    def ung_dung(environ, start_response):
        environ['HTTP_X_FRAPPE_SITE_NAME'] = 'bench-ci.localhost'
        return application(environ, start_response)
    run_simple('127.0.0.1', 8000, ung_dung, use_reloader=False, threaded=True,
               static_files={'/assets': str(Path.cwd() / 'assets')})


if __name__ == '__main__':
    chay()
