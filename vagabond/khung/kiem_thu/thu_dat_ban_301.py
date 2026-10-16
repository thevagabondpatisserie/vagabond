"""#301: chốt các ô đã duyệt và đường gửi FOH, không gọi Lark thật."""
from functools import partial
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, la, dung
from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
from vagabond.khung.kiem_thu.thu_dat_ban_web import ns, chuan, cau, nd, luc

GOC=Path(__file__).resolve().parents[3]
soan=ns['soan_tin_dat_ban']

@ca('#301 bỏ trống vẫn gửi, chặn lựa chọn và số trẻ sai tại máy chủ')
def truong():
    c=dict(cau,khu_vuc=['Bàn ghế cao'])
    r=chuan(nd,c,luc)
    la('mặc định trẻ',r['tre_em'],0)
    for ten,v in [('tre_em',-1),('tre_em',3),('tre_em',1.2),('tre_em',True),('dip','Lạ'),('khu_vuc','Phòng khác'),('email','abc'),('email','a@b.c\nxx'),('banh_kem_theo','a'*1001)]:
        try: chuan(dict(nd,**{ten:v}),c,luc)
        except ValueError as e: dung('có hướng dẫn',len(str(e))>15)
        else: raise AssertionError('Bỏ lọt '+ten)
    r=chuan(dict(nd,dip='Sinh nhật',khu_vuc='Bàn ghế cao',tre_em=1,email=' a@example.com ',banh_kem_theo=' Bánh '),c,luc)
    la('email',r['email'],'a@example.com');la('bánh',r['banh_kem_theo'],'Bánh')

@ca('#301 tin FOH chỉ có ô đã chốt, bỏ dòng rỗng và ngày dd/mm')
def tin():
    d=dict(nd,tre_em=1,email='a@example.com',dip='Sinh nhật',khu_vuc='Bàn ghế cao',banh_kem_theo='Bánh',ghi_chu='Nến',url='https://fixture.invalid/app/vagabond-dat-ban/TEST')
    s=soan(d)
    for chu in ('10/09','1 trẻ em','Dịp: Sinh nhật','Khu vực: Bàn ghế cao','Email: a@example.com','Bánh kèm theo: Bánh','Ghi chú: Nến','/app/vagabond-dat-ban/TEST'):dung(chu,chu in s)
    s=soan(dict(nd,tre_em=0,dip='Không có dịp riêng',url='TEST'))
    for chu in ('Dịp:','Khu vực:','Email:','Bánh kèm theo:','Ghi chú:','0 trẻ em','SĐT liên hệ',chr(0x2014),chr(0x2013)):dung('bỏ '+chu,chu not in s)

@ca('#301 hook chỉ tạo mới (v597: báo nhóm Zalo chủ đề Đặt bàn thay Lark), tin việc có hỏi lại trước khi gửi')
def hook():
    cay=ast.parse((GOC/'vagabond/hooks.py').read_text())
    n=next(n for n in cay.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='doc_events' for t in n.targets))
    su_kien=ast.literal_eval(n.value)
    la('đúng doctype',su_kien['Vagabond Dat Ban'],{'after_insert':'vagabond.dat_ban.bao_dat_ban_moi'})
    dung('không hook wildcard','dat_ban' not in str(su_kien.get('*',{})))
    from vagabond import kenh_zalo
    vet=[]; loi=[]
    kz=NS(tach_tin=kenh_zalo.tach_tin, bao_hoac_ghi_loi=lambda *a,**k: vet.append((a,k)) or ['Z1'])
    dm=NS(theo_ma=lambda ma:{'ten':'Tiệm Trần Cao Vân'})
    f=NS(flags=NS(),utils=NS(get_url_to_form=lambda dt,n:'https://fixture.invalid/app/vagabond-dat-ban/'+n),log_error=lambda **k:loi.append(k))
    g=dict(frappe=f,DOCTYPE='Vagabond Dat Ban',soan_tin_dat_ban=soan,_loi_zalo=lambda t:loi.append(t))
    doc=D(name='TEST'); doc.as_dict=lambda:dict(nd,name='TEST')
    with patch.dict(sys.modules,{'vagabond.kenh_zalo':kz,'vagabond.diem_ban':dm}), patch.object(__import__('vagabond'),'kenh_zalo',kz,create=True), patch.object(__import__('vagabond'),'diem_ban',dm,create=True):
        nap('dat_ban.py','bao_dat_ban_moi',g)(doc)
    la('một tin',len(vet),1)
    a,k=vet[0]
    la('loại việc, chủ đề đặt bàn',a[:2],('viec','dat_ban'))
    la('tiêu đề',a[2],'YÊU CẦU ĐẶT BÀN MỚI')
    dung('có tên cơ sở',any('Cơ sở: Tiệm Trần Cao Vân' in x for x in a[3]))
    dung('có đường mở phiếu',any('/app/vagabond-dat-ban/TEST' in x for x in a[3]))
    la('khoá chống trùng',k.get('khoa'),'dat-ban:TEST')
    la('hỏi lại việc còn chờ',(k.get('kiem'),k.get('nguon')),('dat_ban_cho','TEST'))
    dung('mã kiểm có trong danh mục',kenh_zalo.DIEU_KIEN.get('dat_ban_cho')=='vagabond.dat_ban.con_cho_xac_nhan')
    la('không lỗi',loi,[])
    # Soạn tin hỏng thì ghi tên phiếu, không gửi, không làm hỏng phiếu khách.
    vet.clear(); g['soan_tin_dat_ban']=lambda d:(_ for _ in ()).throw(ValueError('x'))
    with patch.dict(sys.modules,{'vagabond.kenh_zalo':kz,'vagabond.diem_ban':dm}), patch.object(__import__('vagabond'),'kenh_zalo',kz,create=True), patch.object(__import__('vagabond'),'diem_ban',dm,create=True):
        nap('dat_ban.py','bao_dat_ban_moi',g)(doc)
    la('không gửi',vet,[]); la('ghi tên phiếu',loi,['TEST'])

@ca('#301 sender giữ mặc định, URL riêng không đọc nhóm quản trị, bắt HTTP và Lark lỗi')
def sender():
    for url,code,http_loi in [(None,0,False),('https://fixture.invalid/foh',0,False),('https://fixture.invalid/foh',19021,False),('https://fixture.invalid/foh',0,True),('',0,False)]:
        vet=[]
        def mac_dinh():vet.append('doc_quan_tri');return 'https://fixture.invalid/admin'
        def gui(u,**kw):
            vet.append(u)
            def kiem():
                if http_loi:raise RuntimeError('URL chứa bí mật không được log')
            return NS(raise_for_status=kiem,json=lambda:dict(code=code))
        g=dict(_webhook=mac_dinh,json=json,frappe=NS(log_error=lambda *a:vet.append(a)))
        with patch.dict(sys.modules,{'requests':NS(post=gui)}):
            ra=nap('gui_thu.py','ban_webhook',g)('Yêu cầu',url=url)
        la('kết quả',ra,bool(url is None or (url and code==0 and not http_loi)))
        if url is None:la('đọc nhóm cũ',vet,['doc_quan_tri','https://fixture.invalid/admin'])
        elif url:la('chỉ nhóm riêng',vet,[url])
        else:la('rỗng không rơi nhóm cũ',vet,[])

@ca('#301 schema đúng năm ô, seed lặp lại không ghi đè cấu hình')
def schema_seed():
    d=json.loads((GOC/'vagabond/vagabond/doctype/vagabond_dat_ban/vagabond_dat_ban.json').read_text())
    ds={x['fieldname']:x for x in d['fields']}
    for t in ('dip','khu_vuc','tre_em','email','banh_kem_theo'):dung(t,t in ds and not ds[t].get('reqd'))
    la('Desk chỉ đọc khu khách đã chọn', ds['khu_vuc'].get('read_only'), 1)
    for t in ('di_ung','kenh_lien_he','sdt_lien_he'):dung('không thêm '+t,t not in ds)
    for cu in ('', 'Khu riêng'):
        vet=[];db=D(gia=cu)
        def luu(*a):db.gia=a[-1];vet.append(a[-1])
        g=dict(frappe=NS(reload_doc=lambda *a:None,db=NS(get_single_value=lambda *a:db.gia,set_single_value=luu)))
        ham=nap('patches/dat_ban_foh_301.py','execute',g);ham();ham()
        la('số lần ghi',len(vet),0 if cu else 1)
        if cu:la('giữ cấu hình',db.gia,cu)

@ca('#301 form thật gửi năm ô và giữ yêu cầu sau lỗi mạng')
def giao_dien():
    import subprocess
    r=subprocess.run(['node','vagabond/khung/kiem_thu/hanh_vi/dat_ban_301.cjs'],cwd=GOC,capture_output=True,text=True,timeout=30)
    la(r.stdout+r.stderr,r.returncode,0)

@ca('#301 v597 không còn đường Lark cho đặt bàn và tiệc; tiệc đi cùng nhóm Zalo chủ đề Đặt bàn')
def khong_lark():
    for tep in ('vagabond/dat_ban.py','vagabond/tiec_web.py'):
        x=(GOC/tep).read_text()
        for chu in ('gui_lark','webhook_dat_ban','ban_webhook'):
            dung(tep+' bỏ '+chu, chu not in x)
    x=(GOC/'vagabond/tiec_web.py').read_text()
    dung('tiệc chủ đề đặt bàn, hỏi lại việc', 'kenh_zalo.bao_hoac_ghi_loi("viec", "dat_ban"' in x and 'kiem="tiec_cho"' in x)
    from vagabond import kenh_zalo
    la('tách tin', kenh_zalo.tach_tin('A\n\n B \nC'), ('A',['B','C']))
    la('tin rỗng', kenh_zalo.tach_tin(''), ('',[]))

@ca('#301 nhân viên đổi trạng thái không được sửa thông tin khách đã gửi')
def bat_bien():
    def chan(msg):raise ValueError(msg)
    for ten in ('dip','khu_vuc','tre_em','email','banh_kem_theo'):
        cu=D(trang_thai='Chờ xác nhận',**{ten:'Cũ'})
        d=D(trang_thai='Đã xác nhận',**{ten:'Mới'})
        d.is_new=lambda:False;d.get_doc_before_save=lambda:cu
        g=dict(frappe=NS(throw=chan),TRANG_THAI=ns['TRANG_THAI'])
        try:nap('dat_ban.py','kiem_phieu',g)(d)
        except ValueError as e:dung('hướng dẫn ghi chú xử lý','ghi chú xử lý' in str(e))
        else:raise AssertionError('Cho sửa '+ten)


@ca('#310 F1 phiếu trước migrate có NULL vẫn đổi trạng thái, không đổi yêu cầu')
def phieu_cu():
    def chan(msg):raise ValueError(msg)
    cu=D(trang_thai='Chờ xác nhận',khu_vuc=None,tre_em=None)
    d=D(trang_thai='Đã xác nhận',khu_vuc='',tre_em=0)
    d.is_new=lambda:False;d.get_doc_before_save=lambda:cu
    nap('dat_ban.py','kiem_phieu',dict(frappe=NS(throw=chan),TRANG_THAI=ns['TRANG_THAI']))(d)

@ca('#310 tin nhóm không cho dữ liệu khách giả dòng trạng thái hoặc đường dẫn phiếu')
def dong_gia():
    gia='Khách\nTrạng thái: Đã xác nhận. Mở phiếu: https://evil.invalid/x'
    d=dict(nd,ten=gia,ghi_chu=gia,banh_kem_theo=gia,url='https://fixture.invalid/app/TEST')
    tin=soan(d).splitlines()
    la('chỉ một dòng trạng thái thật',len([x for x in tin if x.startswith('Trạng thái:')]),1)
    la('đường dẫn thật ở cuối',tin[-1],'Trạng thái: Chờ xác nhận. Mở phiếu: https://fixture.invalid/app/TEST')
    la('không sửa dữ liệu nguồn',d['ghi_chu'],gia)

@ca('#310 F3 lỗi webhook cũ giữ loại lỗi/mã HTTP, không lưu URL bí mật')
def loi_http():
    vet=[]
    class LoiHTTP(Exception):pass
    def gui(*a,**kw):
        e=LoiHTTP('https://fixture.invalid/secret');e.response=NS(status_code=503);raise e
    g=dict(_webhook=lambda:'https://fixture.invalid/secret',json=json,frappe=NS(log_error=lambda *a:vet.append(a)))
    with patch.dict(sys.modules,{'requests':NS(post=gui)}):
        la('không nhận gửi xong',nap('gui_thu.py','ban_webhook',g)('Thử'),False)
    dung('giữ loại và mã', 'LoiHTTP' in str(vet) and '503' in str(vet))
    dung('không bí mật', 'fixture.invalid' not in str(vet))
