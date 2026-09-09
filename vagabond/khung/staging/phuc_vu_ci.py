"""#257: phục vụ app thật ở loopback CI, không mở staging ra Internet.

Dùng cùng bench/core của ca tích hợp. Không chạy worker; chặn kết nối ra
ngoài ở tầng socket để tác vụ web không vô tình gọi dịch vụ thật.
"""
import os
import socket
from pathlib import Path


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
