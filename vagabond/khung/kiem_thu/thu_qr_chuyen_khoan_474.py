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

@ca('QR474: tiền rỗng lỗi ở hai phía, số 0 tường minh dùng QR tĩnh')
def _tien_rong():
 from vagabond.khung.kiem_thu.nen import nem
 for t in [None, '', '   ']:
  nem('Python từ chối tiền rỗng',lambda:chuoi('970422','123',t),ValueError)
 la('QR tĩnh',chuoi('970422','123',0)[6:12],'010211')
 node("const assert=require('assert'),{nap}=require('./vagabond/khung/kiem_thu/hanh_vi/qr_474_chung');const c=nap({});for(const tien of [null,undefined,'','   '])assert.throws(()=>c.VgbQr.chuoi({bin:'970422',stk:'123',tien}));assert.equal(c.VgbQr.chuoi({bin:'970422',stk:'123',tien:0}).slice(6,12),'010211');")

@ca('QR474: tk_cho thực sự gửi BIN cho tài khoản riêng và mặc định')
def _bin_may_chu():
 from vagabond import tai_khoan as tk
 md=dict(bank='MB',stk='123',ten='Mặc định')
 rieng=dict(nguon='Sales',dung=1,bank='VCB',stk='456',ten='Riêng')
 with patch.object(tk,'cai',return_value=dict(mac_dinh=md,theo_nguon=[rieng])):
  for nguon,bin_ in [('Sales','970436'),('Khác','970422')]:
   ra=tk.tk_cho(nguon)
   la('BIN từ máy chủ',ra.get('bin'),bin_)
   dung('Máy khách vẽ được từ payload thật',bool(json.loads(node("const {nap}=require('./vagabond/khung/kiem_thu/hanh_vi/qr_474_chung');const c=nap({});console.log(JSON.stringify(c.VgbQr.tao("+json.dumps(dict(ra,tien=1000))+")));"))['anh']))

@ca('QR474: PDF lỗi QR giữ cùng khung và thông tin chuyển tay')
def _khung_pdf():
 import html,re,types
 tree=ast.parse((GOC/'vagabond/cong_no.py').read_text())
 f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_phieu_html')
 d=dict(qr=dict(bank='MB',stk='123',ten='Vagabond'),tong_tien=1000,ma_phieu='THUQR')
 env=dict(xem_phieu=lambda name:d,frappe=types.SimpleNamespace(utils=types.SimpleNamespace(escape_html=html.escape),db=types.SimpleNamespace(get_value=lambda *a:""),session=types.SimpleNamespace(user="test")),flt=lambda v:float(v or 0),_ngay_vn=lambda v:'',_tien_vn=lambda v:str(v),_chu_so_tien=lambda v:'Một nghìn',TEN_NGAN_HANG_DAY_DU={})
 exec(compile(ast.Module(body=[f],type_ignores=[]),'cong_no.py','exec'),env)
 env['_qr_data_uri']=lambda *a:'data:image/svg+xml;base64,QR'
 co=env['_phieu_html']('THUQR')
 env['_qr_data_uri']=lambda *a:''
 loi=env['_phieu_html']('THUQR')
 khung=lambda s:re.search(r'<td style="([^"]*width:170px[^"]*)">',s).group(1)
 la('khung như nhau',khung(loi),khung(co))
 dung('chuyển tay rõ', 'Vui lòng chuyển tay' in loi and 'THUQR' in loi)
 dung('không ảnh QR rỗng', 'src=""' not in loi)
