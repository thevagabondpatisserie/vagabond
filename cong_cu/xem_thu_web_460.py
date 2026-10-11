#!/usr/bin/env python3
"""PR460: xem giao diện bằng dữ liệu giả, không cần Frappe, không gửi đơn.
Chạy từ repo: python3 cong_cu/xem_thu_web_460.py
Mở http://127.0.0.1:8789/banh. Chỉ lắng nghe localhost và chỉ hỗ trợ GET.
Ảnh/font/mã đọc trực tiếp từ checkout. Giá/tồn là fixture, không là dữ liệu sống.
Editor chỉ để kiểm nhãn; lưu/xuất bản không được hỗ trợ.
"""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import json,ast,re,mimetypes
ROOT=Path(__file__).resolve().parents[1]
# Read pure constants only; no Frappe or production connections.
tree=ast.parse((ROOT/'vagabond/noi_dung_web.py').read_text()); nd=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MAC_DINH' for t in n.targets)); labels=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NHAN' for t in n.targets)); nd['nhan']={}
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='extend':nd['khoi'].extend((ast.literal_eval(n.value.args[0]) if not isinstance(n.value.args[0],ast.Name) else next(ast.literal_eval(a.value) for a in tree.body if isinstance(a,ast.Assign) and any(isinstance(t,ast.Name) and t.id==n.value.args[0].id for t in a.targets))))
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  p=self.path.split('?')[0]; ct='text/html; charset=utf-8'; out=''
  catalog=json.loads((ROOT/'vagabond/public/web_order/chu-mac-dinh.json').read_text()); all_labels=dict(labels,**catalog)
  if p.startswith('/api/'):
   ct='application/json'; method=p.split('.')[-1]
   d={'nhap':nd,'cong_khai':nd,'phien_ban':1,'lich_su':[],'nhan_mau':all_labels} if method=='doc_bang' else {'khoi':nd['khoi'],'nhan':{k:v['mac_dinh'] for k,v in all_labels.items()}} if method=='cong_khai' else {'banh':{'BAWC00139':4},'nhom':[],'dat_truoc':{'nhom':[]}} if method=='co_the_ban_hom_nay' else json.loads((ROOT/'vagabond/public/web_order/san-pham-mac-dinh.json').read_text()) if method=='san_pham_bien_tap' else {'quay':[{'ma':'TCV','ten':'Trần Cao Vân','dia_chi':'9 Trần Cao Vân','mon':[{'ma':'TEST1','ten':'Biscotti','nhom':'Bánh nhẹ','con':12,'gia':90000,'anh':'/assets/vagabond/web_order/anh-bia.png'}]},{'ma':'NVHTN','ten':'Nhà Văn hoá Thanh Niên','dia_chi':'21 Phạm Ngọc Thạch','mon':[]}]} if method=='con_tren_quay_web' else {}
   if method=='bang_moi':d={'khoi':nd['khoi'],'thong_tin':{},'lien_he':{},'nhan':{},'nhan_mau':all_labels,'nhom_nhan':{'dat_banh':'Trang đặt bánh'},'uu_dai_erp':[]}
   out=json.dumps({'message':d},ensure_ascii=False).encode()
  elif p.startswith('/assets/vagabond/'):
   f=(ROOT/'vagabond/public'/p.removeprefix('/assets/vagabond/')).resolve()
   if not f.is_relative_to(ROOT/'vagabond/public'):
    self.send_error(404);return
   ct=mimetypes.guess_type(str(f))[0] or 'application/octet-stream';out=f.read_bytes() if f.exists() else b''
  else:
   f=ROOT/({'/banh':'vagabond/trang/banh.html','/bien-tap-web':'vagabond/www/bien-tap-web.html','/dat-ban':'vagabond/www/dat-ban.html','/thanh-vien':'vagabond/www/thanh-vien.html'}.get(p,'vagabond/trang/banh.html'))
   s=f.read_text();s=re.sub(r'{% if khong_quyen %}.*?{% else %}','',s,flags=re.S).replace('{% endif %}','');s=s.replace('{{ nguoi | e }}','preview-user').replace('{{ ten_nguoi | e }}','Local Preview').replace('{{ ten_nguoi }}','Local Preview').replace('{{ csrf_token }}','fixture')
   for k,v in all_labels.items():s=s.replace('{{ nhan.'+k+' | e }}',v['mac_dinh'])
   out=s.encode()
  self.send_response(200);self.send_header('Content-Type',ct);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(out)
 def log_message(self,*a):pass
if __name__=='__main__':
 print('Fixture PR460: http://127.0.0.1:8789/banh (GET only)',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8789),H).serve_forever()
