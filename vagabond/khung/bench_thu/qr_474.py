"""QR PDF thật trên bench dùng một lần; không dùng dịch vụ QR ngoài."""
import base64
import io
import json
import os
from pathlib import Path
from unittest.mock import patch


def chay():
 if os.environ.get('GITHUB_ACTIONS') != 'true':
  raise RuntimeError('Chỉ chạy trên bench CI dùng một lần')
 import frappe
 from frappe.utils.pdf import get_pdf
 from pypdf import PdfReader
 from vagabond.cong_no import _qr_data_uri
 from vagabond.qr_chuyen_khoan import chuoi
 frappe.init(site='bench-ci.localhost',sites_path='.')
 frappe.connect()
 try:
  assert frappe.conf.get('vagabond_bench_thu')
  # Thư viện pyqrcode là dependency thật của bench, không giả lập ảnh.
  with patch('socket.socket.connect',side_effect=AssertionError('QR không được nối mạng')):
   uri=_qr_data_uri({'bank':'MB','stk':'VQRQALEAF2999'},160000,'TCVG8FRJ')
  assert uri.startswith('data:image/svg+xml;base64,'), 'Thiếu thư viện QR trên bench'
  svg=base64.b64decode(uri.split(',',1)[1]);assert b'<svg' in svg and b'<path' in svg
  # Tắt tải ngoài trong wkhtmltopdf bằng network proxy chết. Chỉ có data URI.
  pdf=get_pdf('<html><body><img width="230" src="'+uri+'"><p>TCVG8FRJ 160000</p></body></html>',options={'proxy':'http://127.0.0.1:1'})
  reader=PdfReader(io.BytesIO(pdf));assert len(reader.pages)==1
  # SVG được vẽ thành path trong PDF, không chỉ còn chữ chuyển khoản.
  content=reader.pages[0].get_contents().get_data();assert content.count(b' l')>100 or content.count(b' re')>100, 'PDF thiếu nét QR'
  out=Path(os.environ['VGB_ARTIFACTS']);(out/'qr-474.pdf').write_bytes(pdf)
  (out/'qr-474.json').write_text(json.dumps({'svg':True,'pdf':True,'external_network':False,'payload':chuoi('970422','VQRQALEAF2999',160000,'TCVG8FRJ')}))
 finally:
  frappe.db.rollback();frappe.destroy()

if __name__=='__main__': chay()
