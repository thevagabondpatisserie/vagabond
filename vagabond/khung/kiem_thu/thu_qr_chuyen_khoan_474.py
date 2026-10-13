"""PR474: golden từ ảnh thật; kiểm chéo, network guard, DOM và nguồn BIN."""
import ast
import binascii
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.qr_chuyen_khoan import chuoi
GOC = Path(__file__).resolve().parents[3]
GOLDEN = '00020101021238570010A000000727012700069704220113VQRQALEAF29990208QRIBFTTA530370454061600005802VN62120808TCVG8FRJ630450D4'
# Giải mã PNG thật img.vietqr.io ngày 13/10/2026 bằng zxing-cpp.
BO = [dict(bin='970422',stk='VQRQALEAF2999',tien=160000,noi_dung='TCVG8FRJ'),dict(bin='970422',stk='VQRQALEAI0938',tien=120000,noi_dung='NVHTN thử'),dict(bin='970436',stk='001234567890',tien=0,noi_dung=''),dict(bin='970416',stk='0123456789',tien=123456.5,noi_dung='Thanh toán đơn bánh'),dict(bin='970422',stk='VQRQALEAF2999',tien=999999999,noi_dung='A'*80)]
def node(ma):
 r=subprocess.run(['node','-e',ma],cwd=str(GOC),text=True,capture_output=True,timeout=30)
 if r.returncode: raise AssertionError(r.stderr or r.stdout)
 return r.stdout
@ca('QR474: ảnh tham chiếu thật khớp từng byte và CRC kiểm độc lập')
def _golden():
 la('chuỗi thật',chuoi('970422','VQRQALEAF2999',160000,'TCVG8FRJ'),GOLDEN)
 la('CRC thư viện chuẩn', '%04X'%binascii.crc_hqx(GOLDEN[:-4].encode(),0xffff),GOLDEN[-4:])
@ca('QR474: JS/Python khớp năm bộ, tiền 0, Việt, dài, thường, ảo')
def _cheo():
 ra=json.loads(node("const {nap}=require('./vagabond/khung/kiem_thu/hanh_vi/qr_474_chung');let c=nap({});console.log(JSON.stringify("+json.dumps(BO)+".map(d=>c.VgbQr.chuoi(d))));"))
 la('năm bộ',ra,[chuoi(d['bin'],d['stk'],d['tien'],d['noi_dung']) for d in BO])
 for x in ra: la('CRC độc lập',x[-4:],'%04X'%binascii.crc_hqx(x[:-4].encode(),0xffff))
@ca('QR474: dữ liệu sai không tự đoán BIN, cắt nội dung hay nhận tiền âm')
def _sai():
 for b,s,t,n in [('', '1',1,''),('MB','1',1,''),('970422','',1,''),('970422','1',-0.1,''),('970422','1',float('nan'),''),('970422','1',1,'A'*96)]:
  try: chuoi(b,s,t,n)
  except ValueError: pass
  else: raise AssertionError('Phải báo lỗi')
 la('Pancake giữ nguyên',chuoi('','',qr_text='Pancake nguyên chuỗi'),'Pancake nguyên chuỗi')
@ca('QR474: POS/Sales DOM khi chặn mạng ngoài')
def _dom():
 node("require('./vagabond/khung/kiem_thu/hanh_vi/qr_chuyen_khoan_474')")
 node("require('./vagabond/khung/kiem_thu/hanh_vi/qr_trang_474')")
 node("require('./vagabond/khung/kiem_thu/hanh_vi/qr_quay_dom_474')")
 node("require('./vagabond/khung/kiem_thu/hanh_vi/qr_dot_bien_474')")
@ca('QR474: không còn URL dịch vụ ảnh ngoài trong mã chạy')
def _khong_mang():
 files=list((GOC/'vagabond/public/js/bep').glob('*.js'))+[GOC/'vagabond/trang/tt.html',GOC/'vagabond/www/man-hinh-khach.html',GOC/'vagabond/thanh_toan.py',GOC/'vagabond/cong_no.py']
 for p in files:
  for host in ['https://img.vietqr.io','https://api.vietqr.io/image','https://api.qrserver.com']:
   dung(str(p)+' không tải ảnh QR ngoài',host not in p.read_text())
@ca('QR474: PDF gọi bộ dựng tại máy, chặn socket, nhúng SVG hoặc báo lỗi')
def _pdf():
 # Chạy đúng thân hàm thật; không cần khởi tạo nghiệp vụ kế toán trong bộ thuần.
 import types
 import sys
 import vagabond.qr_chuyen_khoan as q
 tree=ast.parse((GOC/'vagabond/cong_no.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_qr_data_uri')
 env={'frappe':types.SimpleNamespace(log_error=lambda *a:None,get_traceback=lambda:'lỗi')};exec(compile(ast.Module(body=[f],type_ignores=[]),'cong_no.py','exec'),env)
 from vagabond import tai_khoan
 la('BIN MB cùng nguồn',tai_khoan.bin_cho('MB'),'970422')
 with patch('socket.socket',side_effect=AssertionError('Không được gọi mạng')),patch.object(q,'anh',side_effect=lambda s:'data:image/svg+xml;base64,'+s):
  la('PDF dựng đúng payload',env['_qr_data_uri']({'bank':'MB','stk':'VQRQALEAF2999'},160000,'TCVG8FRJ'),'data:image/svg+xml;base64,'+GOLDEN)
 with patch.object(q,'anh',side_effect=RuntimeError('thư viện hỏng')):
  la('trả về để hiện chuyển tay',env['_qr_data_uri']({'bank':'MB','stk':'1'},1,''),'')
