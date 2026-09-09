"""Cửa kiểm web riêng trên runner dùng một lần, không chạy site thật."""
import json
import os
import socket
from pathlib import Path
from unittest.mock import patch
import frappe

if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise RuntimeError('Chỉ dùng trên GitHub Actions.')
frappe.init(site='bench-ci.localhost',sites_path='.')
frappe.connect()
try:
    frappe.set_user('Administrator')
    from vagabond.khung.bench_thu.web_editor_245 import chay as editor
    from vagabond.khung.bench_thu.web_khach_245 import chay as khach
    noi = socket.socket.connect
    def noi_bo(sock,dia_chi):
        if isinstance(dia_chi,tuple) and dia_chi[0] not in ('127.0.0.1','localhost','::1'):
            raise RuntimeError('Bộ kiểm web không kết nối ra ngoài.')
        return noi(sock,dia_chi)
    with patch.object(socket.socket,'connect',noi_bo):
        ket={'editor':editor(),'khach':khach()}
    Path(os.environ['VGB_ARTIFACTS'],'web-245.json').write_text(json.dumps(ket,ensure_ascii=False,indent=2,default=str))
    print(json.dumps(ket,ensure_ascii=False,default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
