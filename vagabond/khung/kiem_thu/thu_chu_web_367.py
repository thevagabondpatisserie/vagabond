"""#367: nội dung Marketing là chữ, có phiên bản; không là mã hoặc số bán hàng.

Ca hồi quy chạy renderer thật với nhãn chứa thẻ HTML và kiểm cửa địa chỉ
cũ bằng phiên OTP giả. Không gọi thông tin khách hay gửi đơn ra ngoài.
"""
import ast
import copy
import json
import sys
import re
import subprocess
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import noi_dung_web

GOC = Path(__file__).resolve().parents[2]


@ca('#367 chữ web: đủ khóa nguồn, không để markup thành nội dung sửa')
def _danh_muc():
    mau = json.loads((GOC / 'public/web_order/chu-mac-dinh.json').read_text())
    tep = [GOC / 'trang/banh.html', GOC / 'trang_khach.py'] + list((GOC / 'public/web_order').glob('*.js')) + list((GOC / 'www').rglob('*.html'))
    for p in tep:
        s = p.read_text()
        for k in re.findall(r'(?:htmlChuWeb|chuWeb)\([\'"]([^\'"]+)[\'"]', s):
            dung(str(p.name) + ' có khóa ' + k, k == '%s' or k in noi_dung_web.NHAN)
        for k in re.findall(r'data-vgb-(?:chu|placeholder|aria-label|title|alt)=[\'"]([^\'"]+)[\'"]', s):
            dung(str(p.name) + ' có khóa ' + k, k == '%s' or k in noi_dung_web.NHAN)
    for k, v in mau.items():
        dung(k + ' không có markup', not re.search(r'<|>|=\"', v['mac_dinh']))
        dung(k + ' không còn đại từ cũ', not re.search(r'\b(?:tiệm|mình|anh chị|em)\b', v['mac_dinh'].replace('trẻ em','trẻ nhỏ'), re.I))
    dung('đúng lời chào đã duyệt', any(v['mac_dinh'] == 'Chúng tôi mong được phục vụ cho quý khách' for v in mau.values()))


@ca('#367 chữ web: lưu mẫu có số và sản phẩm, chặn thay giá hoặc trường lạ')
def _cau_truc():
    nd = copy.deepcopy(noi_dung_web.MAC_DINH)
    nd['nhan'] = {'them_nhanh_mon':'Chọn {ten} <b>giữ là chữ</b>'}
    nd['san_pham'] = {'BAWC00139':{'ten':'Candle', 'mo_ta':'Bản mô tả mới', 'tang':'Tầng 1\nTầng 2'}}
    la('lưu đầy đủ', noi_dung_web.chuan_hoa(nd), nd)
    for mon in ({'BAWC00139':{'gia':1}}, {'__proto__':{'ten':'x'}}, {'BAWC00139':{'ten':'x'*4001}}):
        bad = dict(nd, san_pham=mon)
        try: noi_dung_web.chuan_hoa(bad)
        except ValueError: pass
        else: dung('chặn trường hoặc mã nguy hiểm', False)
    bad = dict(nd, nhan={'them_nhanh_mon':'Bỏ mất tên'})
    try: noi_dung_web.chuan_hoa(bad)
    except ValueError: pass
    else: dung('giữ biến tên', False)
    bad = dict(nd, nhan={'them_nhanh_mon':'{ten} {gia_tu_them}'})
    try: noi_dung_web.chuan_hoa(bad)
    except ValueError: pass
    else: dung('không tự thêm biến', False)


@ca('#367 tra địa chỉ: Guest và phiên sai số không gọi Pancake, đúng số mới đọc')
def _dia_chi():
    import vagabond
    from vagabond.lib import sdt84
    dang_nhap = types.SimpleNamespace(_phien=lambda token:None, _chuan_sdt=sdt84)
    thanh_vien = types.SimpleNamespace(COOKIE="vgb_thanh_vien")
    # Nạp thân hàm thật, bỏ decorator để kiểm riêng ranh giới trước HTTP.
    tree = ast.parse((GOC / 'api.py').read_text())
    ham = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'tra_khach')
    ham.decorator_list = []
    goi = []
    def lay(*a, **kw):
        goi.append(kw)
        return types.SimpleNamespace(status_code=200, json=lambda:{'data':[{'name':'Khách giả', 'shop_customer_addresses':[{'phone_number':'0900000001','full_address':'Địa chỉ giả'}]}]})
    fp = types.SimpleNamespace(local=types.SimpleNamespace(response_headers={}), request=types.SimpleNamespace(cookies={thanh_vien.COOKIE:'fixture'}))
    ns={'frappe':fp,'re':re,'requests':types.SimpleNamespace(get=lay),'cfg':lambda:types.SimpleNamespace(pancake_shop_id=1), 'key':lambda *a:'fixture','PANCAKE':'https://fixture.invalid','TIMEOUT':1}
    exec(compile(ast.Module(body=[ham], type_ignores=[]), 'api.py', 'exec'), ns)
    with patch.object(vagabond, 'dang_nhap', dang_nhap, create=True), patch.dict(sys.modules, {'vagabond.thanh_vien':thanh_vien}):
        with patch.object(dang_nhap, '_phien', return_value=None):
            la('khách vãng lai không lộ địa chỉ', ns['tra_khach']('0900000001')['addresses'], [])
        with patch.object(dang_nhap, '_phien', return_value='84900000002'):
            la('phiên số khác không đọc', ns['tra_khach']('0900000001')['addresses'], [])
        la('chưa xác thực không gọi nhà cung cấp', len(goi), 0)
        with patch.object(dang_nhap, '_phien', return_value='84900000001'):
            la('số đã xác thực đọc được', len(ns['tra_khach']('0900000001')['addresses']), 1)
        la('không cache dữ liệu cá nhân', fp.local.response_headers['Cache-Control'], 'private, no-store')



@ca('#367 chữ web: renderer thật chặn nhãn HTML, không đổi giá hay mã món')
def _render():
    mau = json.loads((GOC / 'public/web_order/chu-mac-dinh.json').read_text())
    nhan = {k:'<vgb-canary data-x="1">' + ' '.join(noi_dung_web.cho_dien(v['mac_dinh'])) for k,v in mau.items()}
    kich = '''
window.vgbNhan=NHAN;
window.vgbSanPham={BAWC00139:{ten:'<vgb-canary>',mo_ta:'<vgb-canary>',tang:'<vgb-canary>'}};
TODAY[CAKES[0].sizes[0].id]=4;renderToday();renderCakes();renderSheet(CAKES[0]);
pick(1);pickSlot(6);addToCart();drawCoDate();drawCo();
MUA={co:1,ten_mua:'Mùa thử',mon:[{ma:'TEST',ten:'Hộp thử',con:3,gia:100000,het:false}]};veHangMua();veSheetMua(MUA.mon[0]);
RA({ma:CART[0].id,gia:CART[0].price,html:Object.fromEntries(['#grid-today','#grid-cake','#s-avail','#s-sizes','#s-acc','#s-addons','#s-layers','#cartList','#sum','#warn','#c-prep','#c-tomtat','#rail','#muaLuoi','#sm-avail','#payList'].map(k=>[k,EL(k).innerHTML]))});
'''.replace('NHAN', json.dumps(nhan,ensure_ascii=False))
    r=subprocess.run(['node',str(GOC/'khung/kiem_thu/gia_lap_trang.js'),str(GOC/'trang/banh.html'),'2026-10-03T08:00:00+07:00',kich],capture_output=True,text=True,timeout=30)
    la('renderer chạy được',r.returncode,0)
    if r.returncode: raise AssertionError(r.stderr[:1000])
    d=json.loads(r.stdout)
    for k,v in d['html'].items(): dung(k+' không tạo thẻ từ nhãn', '<vgb-canary' not in v)
    la('mã đơn giữ từ danh mục',d['ma'],'BAWC00139')
    la('giá giữ từ danh mục',d['gia'],650000)


@ca('#367 xuất bản: không đẩy nháp riêng ra web, chuyển lặp lại không đổi')
def _chuyen():
    cu = copy.deepcopy(noi_dung_web.MAC_DINH)
    cu['khoi'] = cu['khoi'][:5]
    cu['khoi'][2]['tieu_de'] = 'Tiêu đề Marketing tự sửa'
    cu['khoi'][4]['nhan'] = 'TỪ TIỆM BÁNH'
    cu['nhan'] = {'dat_ban_tieu_de':'Đặt bàn tại tiệm.', 'tab_today':'Bánh vừa làm'}
    cu['chinh_sach'] = {'dieu_khoan':{'hien':False,'vn':'Bản đang soạn riêng','en':''}}
    moi = noi_dung_web.noi_dung_da_duyet_367(cu)
    la('nhãn cũ chuyển đúng', moi['nhan']['dat_ban_tieu_de'], 'Đặt bàn tại Vagabond.')
    la('giữ chữ tự sửa', moi['nhan']['tab_today'], 'Bánh vừa làm')
    la('giữ chính sách nháp', moi['chinh_sach'], cu['chinh_sach'])
    la('không sửa nguồn', cu['khoi'][4]['nhan'], 'TỪ TIỆM BÁNH')
    la('lặp lại không thêm khối', noi_dung_web.noi_dung_da_duyet_367(moi), moi)
    # Chạy patch thật với Document fixture: hai bản không nhập làm một.
    fp = noi_dung_web.frappe
    cong_khai = copy.deepcopy(cu); cong_khai.pop('chinh_sach')
    d = types.SimpleNamespace(ban_nhap=json.dumps(cu), ban_cong_khai=json.dumps(cong_khai), phien_ban=7, lich_su='[]', flags=types.SimpleNamespace())
    da_luu=[]; d.save=lambda **kw: da_luu.append(kw)
    with patch.object(fp, 'db', types.SimpleNamespace(exists=lambda *a:True, sql=lambda *a:None)), patch.object(fp, 'session', types.SimpleNamespace(user='Administrator'), create=True), patch.object(fp.utils, 'now', lambda:'2026-10-03 12:00:00', create=True), patch.object(noi_dung_web, '_doc', return_value=d):
        dung('patch ghi một lần', noi_dung_web.xuat_ban_chu_da_duyet_367())
        la('không công khai nháp', 'chinh_sach' in json.loads(d.ban_cong_khai), False)
        la('giữ lịch sử cũ', json.loads(d.lich_su)[0]['noi_dung'], cong_khai)
        la('chạy lại no-op', noi_dung_web.xuat_ban_chu_da_duyet_367(), False)
    la('lưu một lần',len(da_luu),1)


@ca("#424 R1: lỗi thuế, địa chỉ, phí giao và quầy không diễn giải chữ thành HTML")
def _loi_html():
    nhan = {k:"<vgb-canary>" + " ".join(noi_dung_web.cho_dien(v["mac_dinh"])) for k,v in noi_dung_web.NHAN.items()}
    kich = "window.vgbNhan=" + json.dumps(nhan) + ";" + r'''
const ketQua={};
EL('#f-mst').value='0318561568';
GHI.traLoi=()=>({message:{ok:0}});lookupMst();await CHO_XONG();ketQua.thueLoi=EL('#mstHint').innerHTML;
GHI.traLoi=()=>({message:{ok:1,ten:'<vgb-company>',nghi_thieu:true}});lookupMst();await CHO_XONG();ketQua.thueThieu=EL('#mstHint').innerHTML;
GHI.traLoi=()=>({message:{ok:1,ten:'<vgb-company>',dia_chi:'Thử'}});lookupMst();await CHO_XONG();ketQua.thueTimThay=EL('#mstHint').innerHTML;
EL('#f-phone').value='0900000001';GHI.traLoi=()=>({message:{addresses:[]}});lookupPhone();await CHO_XONG();ketQua.diaChiTrong=EL('#phoneHint').innerHTML;
CO.addrList=[{full_name:'<vgb-customer>',phone_number:'0900000001',full_address:'9 <vgb-address>'}];drawSaved();ketQua.diaChi=EL('#savedAddr').innerHTML;
TODAY[CAKES[0].sizes[0].id]=4;renderSheet(CAKES[0]);pick(2);pickSlot(6);addToCart();
for(const kieu of ['du_kien','chinh_xac']){apPhiGiao({ok:1,total_fee:30000,diem_lay:'Bep Vagabond',distance:4},kieu,{ten:'Quận thử'});ketQua['phi'+kieu]=EL('#shipHint').innerHTML;}
MIEN_PHI_TU=500000;apPhiGiao({ok:1,total_fee:30000,diem_lay:'Bep Vagabond',distance:4},'chinh_xac',null);ketQua.phiMien=EL('#shipHint').innerHTML;
STORE={quay:[{ten:'Quầy thử',mon:[{ma:'TEST',ten:'Bánh',con:2,gia:10000}]}]};veTonQuay();ketQua.quay=EL('#storeBody').innerHTML;
RA(ketQua);
'''
    r = subprocess.run(["node", str(GOC/"khung/kiem_thu/gia_lap_trang.js"),str(GOC/"trang/banh.html"),"2026-10-03T08:00:00+07:00",kich],capture_output=True,text=True,timeout=30)
    la("chạy nhánh lỗi thật",r.returncode,0)
    if r.returncode: raise AssertionError(r.stderr)
    d=json.loads(r.stdout)
    for k,v in d.items(): dung(k+" không tạo thẻ", "<vgb-" not in v)
    dung("có nhãn xấu trong fixture", "&lt;vgb-canary&gt;" in d["thueLoi"])


@ca("#424 R2: preview đổi chữ hộp đang mở, giữ lựa chọn và cuộn")
def _preview_mo():
    kich = r'''
TODAY[CAKES[0].sizes[0].id]=4;renderSheet(CAKES[0]);
if(cur.sizes[1])setSize(cur.sizes[1].id);
picked_nums=[2,6];picked_add=new Set([ADDONS[0].id]);EL('#s-wish').value='Mừng sinh nhật';
const truoc={ma:curSize.id,gia:curSize.p};
MUA={co:1,ten_mua:'Mùa thử',mon:[{ma:'TEST',ten:'Hộp thử',ruot:'Nội dung cũ',con:3,gia:100000,het:false}]};
veSheetMua(MUA.mon[0]);EL('#sheetMua').scrollTop=123;
window.vgbNhan={phu_kien_e0fe21772:'Nến bản mới',san_pham_co_san:'Sẵn sàng mới',dat_banh_b742ca205:'Thêm bản mới'};
window.vgbSanPham={[curSize.id]:{ten:'Tên mới',mo_ta:'Mô tả mới'},TEST:{ten:'Hộp mới',mo_ta:'Ruột mới'}};
document.dispatchEvent({type:'vgb-nhan'});
RA({truoc,sau:{ma:curSize.id,gia:curSize.p},nums:picked_nums,them:[...picked_add],themMong:ADDONS[0].id,loi:EL('#s-wish').value,
ten:EL('#s-name').textContent,moTa:EL('#s-desc').textContent,phuKien:EL('#s-acc').innerHTML,coSan:EL('#s-avail').innerHTML,
tenMua:EL('#sm-name').textContent,ruotMua:EL('#sm-ruot').innerHTML,nutMua:EL('#sm-cta').textContent,cuon:EL('#sheetMua').scrollTop});
'''
    r=subprocess.run(['node',str(GOC/'khung/kiem_thu/gia_lap_trang.js'),str(GOC/'trang/banh.html'),'2026-10-03T08:00:00+07:00',kich],capture_output=True,text=True,timeout=30)
    la('chạy sự kiện preview thật',r.returncode,0)
    if r.returncode: raise AssertionError(r.stderr)
    d=json.loads(r.stdout)
    la('giữ size và giá',d['sau'],d['truoc'])
    la('giữ nến số',d['nums'],[2,6])
    la('giữ phụ kiện',d['them'],[d['themMong']])
    la('giữ lời chúc',d['loi'],'Mừng sinh nhật')
    la('tên sản phẩm',d['ten'],'Tên mới')
    la('mô tả sản phẩm',d['moTa'],'Mô tả mới')
    dung('nhãn phụ kiện cập nhật', 'Nến bản mới' in d['phuKien'])
    dung('nhãn có sẵn cập nhật', 'Sẵn sàng mới' in d['coSan'])
    la('tên mùa cập nhật',d['tenMua'],'Hộp mới')
    dung('mô tả mùa cập nhật','Ruột mới' in d['ruotMua'])
    la('nút mùa cập nhật',d['nutMua'],'Thêm bản mới')
    la('giữ vị trí cuộn',d['cuon'],123)


@ca("#431 F2: thêm vào giỏ báo đúng tên bánh Marketing đã đổi (bánh, thêm nhanh, hàng mùa)")
def _toast_ten_moi():
    kich = r'''
const c=CAKES[0], s=c.sizes[0];
window.vgbSanPham={[s.id]:{ten:'Tên mới'},TEST:{ten:'Hộp mới'}};
TODAY[s.id]=4;renderSheet(c);setSize(s.id);addToCart();
const t1=EL('#toast').textContent;
CART.length=0;EL('#toast').textContent='';for(const z of c.sizes)TODAY[z.id]=0;TODAY[s.id]=4;themNhanh(c.k,true);
const t2=EL('#toast').textContent;
MUA={co:1,ten_mua:'Mùa thử',mon:[{ma:'TEST',ten:'Hộp cũ',con:3,gia:100000,het:false}]};
CART.length=0;EL('#toast').textContent='';themHangMua('TEST');
RA({t1,t2,t3:EL('#toast').textContent,cu:c.k});
'''
    r=subprocess.run(['node',str(GOC/'khung/kiem_thu/gia_lap_trang.js'),str(GOC/'trang/banh.html'),'2026-10-03T08:00:00+07:00',kich],capture_output=True,text=True,timeout=30)
    la('chạy chuỗi bấm thật',r.returncode,0)
    if r.returncode: raise AssertionError(r.stderr[:1000])
    d=json.loads(r.stdout)
    dung('thêm từ hộp bánh: tên mới (%s)' % d['t1'], 'Tên mới' in d['t1'] and d['cu'] not in d['t1'])
    dung('thêm nhanh: tên mới (%s)' % d['t2'], 'Tên mới' in d['t2'] and d['cu'] not in d['t2'])
    dung('hàng mùa: tên mới (%s)' % d['t3'], 'Hộp mới' in d['t3'] and 'Hộp cũ' not in d['t3'])


@ca("#367 duyệt 04/10: sửa chữ pháp lý chân trang trong Editor, giữ nguồn mặc định")
def _phap_ly():
    # Chỉ đổi chữ hiển thị website; không ghi Company/Tax ID của ERP.
    keys = ('dat_banh_15f2c7f29','dat_banh_2085c9658','dat_banh_2f7b911ea','dat_banh_cc4a76159')
    sua = {k:'Chữ mới <vgb-canary>' for k in keys}
    nd = copy.deepcopy(noi_dung_web.MAC_DINH)
    nd['nhan'] = sua
    da_luu = noi_dung_web.chuan_hoa(nd)
    la('máy chủ chấp nhận cả bốn nhãn', da_luu['nhan'], sua)
    la('bản công khai nhận chữ đã soạn', {k:noi_dung_web.nhan_day_du(da_luu)[k] for k in keys}, sua)
    trang = (GOC / 'trang/banh.html').read_text()
    for k in keys:
        dung(k+' dùng marker text an toàn', 'data-vgb-chu="'+k+'"' in trang)
        dung(k+' vẫn có chữ mặc định', noi_dung_web.NHAN[k]['mac_dinh'] in trang)
    la('để trống về mặc định',noi_dung_web.nhan_day_du({'nhan':{keys[0]:''}})[keys[0]],noi_dung_web.NHAN[keys[0]]['mac_dinh'])


@ca("#432 P1: dòng Đã chọn thêm không diễn giải nhãn phụ kiện, nến số thành HTML")
def _da_chon_them():
    # Chuỗi bấm của khách: mở hộp bánh, chọn phụ kiện, bỏ chọn, chọn nến số. Đọc #s-addsum
    # sau từng bước; ca R1 cũ không chọn phụ kiện nên bỏ sót vùng này (Codex #432).
    kich = r'''
window.vgbNhan={phu_kien_91d4d0b6f:'<vgb-canary>Phụ kiện</vgb-canary>',dat_banh_909dfa9ae:'<vgb-canary>Nến</vgb-canary>'};
TODAY[CAKES[0].sizes[0].id]=4;renderSheet(CAKES[0]);
toggleAdd('BAPK00002');const a=EL('#s-addsum').innerHTML;
toggleAdd('BAPK00002');toggleNum(2);const b=EL('#s-addsum').innerHTML;
RA({a,b});
'''
    r=subprocess.run(['node',str(GOC/'khung/kiem_thu/gia_lap_trang.js'),str(GOC/'trang/banh.html'),'2026-10-03T08:00:00+07:00',kich],capture_output=True,text=True,timeout=30)
    la('chạy chuỗi bấm thật',r.returncode,0)
    if r.returncode: raise AssertionError(r.stderr[:1000])
    d=json.loads(r.stdout)
    dung('phụ kiện: không tạo thẻ (%s)' % d['a'][:120], '<vgb-canary' not in d['a'] and '&lt;vgb-canary&gt;' in d['a'])
    dung('nến số: không tạo thẻ (%s)' % d['b'][:120], '<vgb-canary' not in d['b'] and '&lt;vgb-canary&gt;' in d['b'])


@ca('#367 mở rộng: CMS giữ ảnh thay được, hạn và email; từ chối cấu hình sai')
def _marketing_moi():
    for loai in ('uu_dai', 'tuyen_dung'):
        k={'id':'marketing-test','loai':loai,'hien':True,'vi_tri':loai,'tieu_de':'Bản kiểm',
           'anh':'/files/anh-moi.jpg','bat_dau':'2026-10-01','ket_thuc':'2026-10-31','email':'hr@example.com'}
        la('giữ dữ liệu '+loai,noi_dung_web.chuan_hoa({'khoi':[k]})['khoi'][0],k)
        for sua in ({'ket_thuc':'2026-09-30'},{'bat_dau':'2026-02-30'},{'anh':'javascript:alert(1)'},{'email':'bad@example.com\nBcc:x@y.com'},{'tieu_de':''}):
            try:noi_dung_web.chuan_hoa({'khoi':[dict(k,**sua)]})
            except ValueError:pass
            else:dung('chặn dữ liệu sai '+str(sua),False)
    k.update(email='',lien_ket='')
    try:noi_dung_web.chuan_hoa({'khoi':[k]})
    except ValueError:pass
    else:dung('vị trí bật phải có nơi nhận hồ sơ',False)
    k['hien']=False
    la('bản nháp chưa có email vẫn lưu được',noi_dung_web.chuan_hoa({'khoi':[k]})['khoi'][0]['hien'],False)


@ca('#367 mở rộng: chi tiết chọn đúng cỡ đặt trước, sửa không cộng thêm và reload giữ giỏ')
def _gio_moi():
    from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay
    r=_chay('2026-10-05T08:00:00',r'''
const c=CAKES.find(c=>c.sizes.length>1), z=c.sizes[c.sizes.length-1];
tabNow='order';TRUOC={[z.id]:5};TODAY={};renderSheet(c);
const selected=curSize.id;
EL('#s-wish').value='Lời chúc trước';EL('#s-nia').value='2';addToCart();
suaDongGio(0);EL('#s-wish').value='Lời chúc sau';addToCart();
const edited={count:CART.length,qty:CART[0].qty,wish:CART[0].wish,nia:CART[0].dung_cu.nia};
luuGioDangSoan();CART=[];phucHoiGio();
RA({selected,expected:z.id,edited,restored:CART.map(o=>({id:o.id,wish:o.wish,qty:o.qty,price:o.price,nia:o.dung_cu.nia}))});
''')
    la('mở chi tiết đúng cỡ thẻ',r['selected'],r['expected'])
    la('sửa đúng một dòng',r['edited'],{'count':1,'qty':1,'wish':'Lời chúc sau','nia':2})
    la('tải lại giữ một dòng',len(r['restored']),1)
    la('giữ lời chúc',r['restored'][0]['wish'],'Lời chúc sau')
    la('giữ dụng cụ',r['restored'][0]['nia'],2)


@ca('#367 mở rộng: khung giờ hết hạn không chọn và không hiện như đã xác nhận')
def _gio_het():
    from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay
    r=_chay('2026-10-05T23:00:00',r'''
picked=0;daChonGio=false;pickSlot(0);renderRail();
RA({chon:daChonGio,note:EL('#orderNote').innerHTML});
''')
    la('không chọn giờ hết hạn',r['chon'],False)
    dung('mời chọn giờ còn nhận', 'Vui lòng chọn khung giờ còn nhận' in r['note'])


@ca('#367 mở rộng: trang chiến dịch lọc ẩn/hết hạn, giữ chữ nguyên văn và thay ảnh')
def _render_chien_dich():
    script=r'''
const fs=require('fs'),vm=require('vm');
class El{constructor(t){this.tagName=t;this.children=[];this.dataset={};this.attrs={};this.textContent='';}append(...a){this.children.push(...a);}replaceChildren(...a){this.children=[...a];}setAttribute(k,v){this.attrs[k]=v;}}
const roots={'noi-uu_dai':new El('div'),'noi-tuyen_dung':new El('div')};
const document={createElement:t=>new El(t),getElementById:k=>roots[k],addEventListener(){}};
const window={};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window,document,Date,Intl,Set,encodeURIComponent});
const base={id:'a',loai:'uu_dai',hien:true,tieu_de:'<img onerror=alert(1)>',anh:'/files/one.jpg',nhom:'Web'};
const data={khoi:[base,{...base,id:'hidden',hien:false},{...base,id:'expired',ket_thuc:'2000-01-01'},{...base,id:'future',bat_dau:'2099-01-01'},{id:'job',loai:'tuyen_dung',hien:true,tieu_de:'Thợ bánh',email:'hr@example.com'}]};
const walk=e=>[e,...e.children.flatMap(walk)];
window.vgbVeChuyenMuc(data);let all=walk(roots['noi-uu_dai']);
const first={count:all.filter(e=>e.tagName==='article').length,text:all.find(e=>e.tagName==='h2').textContent,src:all.find(e=>e.tagName==='img').src,href:walk(roots['noi-tuyen_dung']).find(e=>e.tagName==='a').href};
base.anh='/files/two.jpg';window.vgbVeChuyenMuc(data);all=walk(roots['noi-uu_dai']);
console.log(JSON.stringify({first,newSrc:all.find(e=>e.tagName==='img').src}));
'''
    r=subprocess.run(['node','-e',script,str(GOC/'public/web_order/chuyen-muc.js')],capture_output=True,text=True,timeout=30)
    la('renderer chạy',r.returncode,0)
    if r.returncode:raise AssertionError(r.stderr)
    d=json.loads(r.stdout)
    la('ẩn/hết hạn không hiện',d['first']['count'],2)
    la('tiêu đề là chữ',d['first']['text'],'<img onerror=alert(1)>')
    la('ảnh đã thay',d['newSrc'],'/files/two.jpg')
    dung('ứng tuyển đúng vị trí',d['first']['href'].startswith('mailto:hr@example.com?subject='))


@ca('#367 mở rộng: link bánh đặt trước mở mới vẫn chọn đúng cỡ có bán')
def _link_moi():
    from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay
    r=_chay('2026-10-05T08:00:00',r'''
const c=CAKES.find(c=>c.sizes.length>1),z=c.sizes[c.sizes.length-1];
TODAY={OTHER:2};TRUOC={[z.id]:3};tabNow='today';location.hash='#/banh/'+slug(c.k);applyRoute();
RA({tab:tabNow,selected:curSize.id,expected:z.id});
''')
    la('link mở mới sang đặt trước khi không có bánh hôm nay',r['tab'],'order')
    la('đúng cỡ còn nhận',r['selected'],r['expected'])


@ca('#436 giỏ phục hồi: phản hồi danh mục đến trễ cập nhật giá và tổng, kể cả giá 0')
def _gia_sau_nap():
    from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay
    r = _chay('2026-10-06T08:00:00', r'''
await napTonHomNay();
const c=CAKES[0],z=c.sizes[0];TODAY={[z.id]:5};tabNow='today';z.p=100000;
renderSheet(c);addToCart();luuGioDangSoan();CART=[];phucHoiGio();
const truoc=cartTotal();let tra;
fetch=()=>new Promise(r=>{tra=r;});
const cho=napTonHomNay();const dangCho=cartTotal();
tra({json:async()=>({message:{banh:{[z.id]:5},nhom:[{ten:c.k,sizes:[{ma:z.id,cm:z.cm,gia:200000}]}]}})});
await cho;
const sau=cartTotal(),daLuu=JSON.parse(sessionStorage.getItem('vgb-gio-v1')).gio[0].price;
fetch=async()=>({json:async()=>({message:{banh:{[z.id]:5},nhom:[{ten:c.k,sizes:[{ma:z.id,cm:z.cm,gia:0}]}]}})});
await napTonHomNay();RA({truoc,dangCho,sau,daLuu,gia0:cartTotal(),qty:CART[0].qty});
''')
    la('giá trước khi phản hồi',r['truoc'],100000)
    la('phản hồi thực sự đang chờ',r['dangCho'],100000)
    la('tổng dùng danh mục mới',r['sau'],200000)
    la('lưu giá đã làm mới',r['daLuu'],200000)
    la('giá 0 không giữ giá cũ',r['gia0'],0)
    la('không đổi số lượng',r['qty'],1)


@ca('#436 CMS: chặn vị trí mất khối, link lạ và Zalo cá nhân; nâng cấp không mất chữ')
def _kenh_noi_va_vi_tri():
    nd = copy.deepcopy(noi_dung_web.MAC_DINH)
    for k in nd['khoi']:
        if k['id'] in ('loi-chao','ho-tro'):k['hien']=True;k['noi_dung']='Bản sửa riêng'
    nd['nhan']={'them_nhanh_mon':'Chọn {ten}'}
    moi=noi_dung_web.rut_gon_va_kenh_436(nd)
    la('lặp lại không đổi',noi_dung_web.rut_gon_va_kenh_436(moi),moi)
    for k in moi['khoi']:
        if k['id'] in ('loi-chao','ho-tro'):
            la('ẩn đúng khối',k['hien'],False);la('không xoá chữ',k['noi_dung'],'Bản sửa riêng')
    la('không đụng bản đầu',next(k for k in nd['khoi'] if k['id']=='ho-tro')['hien'],True)
    for loai,vi_tri,link in [('thong_bao','uu_dai',''),('anh_chu','tuyen_dung',''),('kenh_dat_hang','cuoi_trang','javascript:alert(1)'),('zalo_oa','cuoi_trang','https://zalo.me/0931224334'),('zalo_oa','cuoi_trang','https://example.com/1234567890123456789')]:
        try:noi_dung_web.chuan_hoa({'khoi':[{'id':'test','loai':loai,'vi_tri':vi_tri,'hien':True,'tieu_de':'Test','lien_ket':link}]})
        except ValueError:pass
        else:dung('chặn sai '+loai+' '+vi_tri+' '+link,False)
    k={'id':'test','loai':'zalo_oa','hien':True,'tieu_de':'Zalo','lien_ket':'https://zalo.me/1234567890123456789'}
    la('OA đúng cấu trúc lưu được',noi_dung_web.chuan_hoa({'khoi':[k]})['khoi'][0],k)
    k['lien_ket']='https://zalo.me/thevagabondsaigon'
    la('OA tên công khai lưu được',noi_dung_web.chuan_hoa({'khoi':[k]})['khoi'][0],k)
    for url in ['https://zalo.me.evil.test/thevagabondsaigon','https://user:pass@zalo.me/thevagabondsaigon','http://zalo.me/thevagabondsaigon','https://zalo.me/thevagabondsaigon/extra']:
        try:noi_dung_web.chuan_hoa({'khoi':[dict(k,lien_ket=url)]})
        except ValueError:pass
        else:dung('chặn OA sai '+url,False)
    oa=next(k for k in moi['khoi'] if k['id']=='kenh-zalo')
    la('OA mặc định được bật',oa['hien'],True)
    la('OA anh Việt cung cấp',oa['lien_ket'],'https://zalo.me/thevagabondsaigon')



@ca('#436 nút nổi: bỏ link nguy hiểm, sửa nhãn nguyên văn, Escape không chạy điều hướng khác')
def _render_kenh_noi():
    script=r'''
const fs=require('fs'),vm=require('vm'),suKien={};
class El{constructor(t){this.tagName=t;this.children=[];this.dataset={};this.attrs={};this.style={};this.textContent='';}append(...a){this.children.push(...a);}replaceChildren(...a){this.children=[...a];}setAttribute(k,v){this.attrs[k]=v;}focus(){this.focused=true;}contains(x){return walk(this).includes(x);}querySelector(){return walk(this).find(e=>e.className==='kenh-bang'&&!e.hidden);}}
const walk=e=>[e,...e.children.flatMap(walk)],body=new El('body');
const document={body,createElement:t=>new El(t),getElementById:()=>null,addEventListener:(k,f,capture)=>{suKien[k]={f,capture};}};
const window={addEventListener(){}};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window,document,URL});
const k={id:'app',loai:'kenh_dat_hang',hien:true,tieu_de:'<img onerror=x>',lien_ket:'https://example.com/menu'};
window.vgbVeKenhNoi({khoi:[k,{...k,id:'bad',lien_ket:'javascript:alert(1)'},{...k,id:'hidden',hien:false},{id:'z',loai:'zalo_oa',hien:true,tieu_de:'Zalo',lien_ket:'https://zalo.me/0931224334'}]});
let all=walk(body),links=all.filter(e=>e.tagName==='a'),b=all.find(e=>e.className==='kenh-bong kenh-app');b.onclick();
let stopped=false;suKien.keydown.f({key:'Escape',preventDefault(){},stopImmediatePropagation(){stopped=true;}});
const first={links:links.length,label:links[0].children[1].textContent,expanded:b.attrs['aria-expanded'],focus:b.focused,capture:suKien.keydown.capture,stopped};
window.vgbVeKenhNoi({nhan:{kenh_noi_nut:'Đặt món'},khoi:[{...k,tieu_de:'App mới',lien_ket:'https://example.com/new'}]});all=walk(body);links=all.filter(e=>e.tagName==='a');
const appButton=all.find(e=>e.className==='kenh-bong kenh-app').children[1].textContent;
window.vgbVeKenhNoi({khoi:[{id:'oa',loai:'zalo_oa',hien:true,tieu_de:'Nhắn Zalo',lien_ket:'https://zalo.me/thevagabondsaigon'}]});const oa=walk(body).find(e=>e.className==='kenh-bong kenh-zalo');
console.log(JSON.stringify({oaHref:oa.href,oaTarget:oa.target,first,href:links[0].href,title:links[0].children[1].textContent,button:appButton}));
'''
    r=subprocess.run(['node','-e',script,str(GOC/'public/web_order/kenh-noi.js')],capture_output=True,text=True,timeout=30)
    if r.returncode:raise AssertionError(r.stderr)
    d=json.loads(r.stdout)
    la('OA tên hiển thị đúng',d['oaHref'],'https://zalo.me/thevagabondsaigon')
    la('OA mở tab mới',d['oaTarget'],'_blank')
    la('chỉ một link hợp lệ',d['first']['links'],1)
    la('nhãn không trở thành HTML',d['first']['label'],'<img onerror=x>')
    la('Escape đóng và giữ focus',d['first']['expanded'],'false')
    dung('chặn trước handler điều hướng',d['first']['capture'] and d['first']['stopped'] and d['first']['focus'])
    la('đổi link trong preview',d['href'],'https://example.com/new')
    la('đổi nhãn trong preview',d['button'],'Đặt món')
