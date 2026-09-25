"""#300: đọc lịch sử thật qua cửa nguồn, giữ quyền và ảnh khi đổi nhận diện."""
import subprocess
from pathlib import Path
from types import SimpleNamespace as NS
from vagabond.khung.kiem_thu.nen import ca, la, dung
from vagabond.khung.kiem_thu.thu_su_co_290 import nap
from vagabond.lib import nhan_trang_thai_pancake, sdt
from vagabond.ngay_pancake import ngay_tu_iso
import re

GOC = Path(__file__).resolve().parents[3]

@ca('#300 lịch sử lọc khách trước khi tra ảnh theo một lô, trạng thái từ máy chủ')
def lich_su():
    ds = [dict(id=i, bill_phone_number=so, status_name=tt, inserted_at='2026-09-19T17:30:00Z',
          items=[dict(variation_info=dict(display_id=ma, name='Bánh'), quantity=2)])
          for i,so,tt,ma in [(1,'0901234567','new','BANH1'),
          (2,'84901234567','delivered','BANH2'),(3,'0901234568','new','RIENG'),
          (4,'rác','new','RAC')]]
    vet=[]
    def doc(dt, **kw):
        vet.append((dt,kw));return [dict(name='BANH1',image='/files/banh.jpg')]
    anh=nap('chon_mon.py','anh_theo_ma',dict(frappe=NS(get_all=doc),ma_goc=nap('chon_mon.py','ma_goc',dict(re=re))))
    g=dict(requests=NS(get=lambda *a,**k:NS(raise_for_status=lambda:None,json=lambda:dict(data=ds))),
           PANCAKE='https://fixture.invalid',TIMEOUT=1,_so=lambda x:x,
           _chuan_sdt=sdt,nhan_trang_thai_pancake=nhan_trang_thai_pancake,
           chon_mon=NS(anh_theo_ma=anh),ngay_tu_iso=ngay_tu_iso)
    ham=nap('dang_nhap.py','_don_pancake',g)
    ra=ham(NS(pancake_shop_id='TEST'),'', '0901234567',bao_loi=True)
    la('chỉ hai đơn của khách',len(ra),2)
    la('một lần tra ảnh',len(vet),1)
    la('không tra mã khách khác',vet[0][1]['filters'],{'name':['in',['BANH1','BANH2']]})
    la('ngày Việt Nam',ra[0]['ngay_dat'],'2026-09-20')
    la('nhãn mới',ra[0]['trang_thai'],'Đơn mới')
    la('đã giao',ra[1]['trang_thai'],'Đã giao')
    la('màu đã giao',ra[1]['mau_trang_thai'],'xanh')
    la('ảnh thật',ra[0]['mon'][0]['hinh'],'/files/banh.jpg')
    la('thiếu ảnh giữ rỗng',ra[1]['mon'][0]['hinh'],'')
    vet.clear();la('số rác không thấy đơn rác',ham(NS(pancake_shop_id='TEST'),'','rác'),[])
    la('không truy vấn toàn Item khi rỗng',vet,[])

@ca('#300 mã hủy thắng tên cũ, trạng thái chưa biết không giả nhận thành công')
def trang_thai():
    la('hủy',nhan_trang_thai_pancake(6,'delivered')['nhan'],'Đã huỷ')
    la('xóa',nhan_trang_thai_pancake('7','new')['mau'],'xam')
    la('lạ',nhan_trang_thai_pancake(999,'unknown')['nhan'],'Tiệm đang cập nhật trạng thái')

@ca('#300 ba trang tiêu thụ cùng nền, không còn tệp CSS cũ hoặc font nhúng')
def nen_chung():
    for tep in ('vagabond/trang/banh.html','vagabond/www/thanh-vien.html','vagabond/www/dat-ban.html'):
        s=(GOC/tep).read_text()
        dung(tep+' dùng nền', '/assets/vagabond/web_order/nen.css' in s)
        dung(tep+' không CSS cũ', 'dich-vu.css' not in s)
        dung(tep+' không font nhúng','data:font/' not in s)
    dung('đã bỏ CSS cũ',not (GOC/'vagabond/public/web_order/dich-vu.css').exists())

@ca('#300 chạy DOM lịch sử, ảnh hỏng và thử lại')
def dom():
    r=subprocess.run(['node','vagabond/khung/kiem_thu/hanh_vi/thanh_vien_245.cjs'],cwd=GOC,capture_output=True,text=True,timeout=30)
    la(r.stdout+r.stderr,r.returncode,0)

@ca('#300 F2/F3 mã đã hoàn tất và ảnh có hậu tố size')
def ma_da_biet():
    la('đã nhận',nhan_trang_thai_pancake(3,None)['nhan'],'Đã giao')
    la('đã thu tiền',nhan_trang_thai_pancake(16,'received_money')['mau'],'xanh')
    vet=[]
    def doc(dt,**kw):
        vet.append(kw['filters']['name'][1]);return [dict(name='BANH1',image='/files/goc.jpg'),dict(name='BANH1S18CM',image='/files/rieng.jpg')]
    g=dict(re=re,frappe=NS(get_all=doc));g['ma_goc']=nap('chon_mon.py','ma_goc',g)
    r=nap('chon_mon.py','anh_theo_ma',g)(['BANH1S16CM','BANH1S18CM','BANH1MINI12CM'])
    la('một lô',len(vet),1);dung('có mã gốc','BANH1' in vet[0])
    la('size về gốc',r['BANH1S16CM'],'/files/goc.jpg')
    la('ưu tiên mã thật',r['BANH1S18CM'],'/files/rieng.jpg')
    la('mini',r['BANH1MINI12CM'],'/files/goc.jpg')

@ca('#310 JS/CSS đổi nội dung phải đổi URL để vượt cache immutable trên site')
def ma_bam_asset():
    import hashlib
    # #367: thêm trang biên nhận, trang chính sách và bảng marketing cùng các
    # tệp của chúng. bien-tap.js/css đổi nội dung trong #367 nên cũng phải đổi URL.
    for ten in ('vagabond/trang/banh.html','vagabond/www/thanh-vien.html','vagabond/www/dat-ban.html',
                'vagabond/www/banh/xong.html','vagabond/www/chinh-sach.html','vagabond/www/bien-tap-web.html'):
        s=(GOC/ten).read_text()
        for tep in ('nen.css','thanh-vien.css','thanh-vien.js','dat-ban.js','trang-khach.css','bien-nhan.js',
                    'bien-tap.css','bien-tap.js'):
            duong='/assets/vagabond/web_order/'+tep
            if duong not in s:continue
            bam=hashlib.sha256((GOC/'vagabond/public/web_order'/tep).read_bytes()).hexdigest()[:12]
            dung(ten+' '+tep,duong+'?v='+bam in s)
