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


@ca("#431 F1: tên công ty, mã số thuế, địa chỉ pháp lý không nằm trong chữ Marketing sửa được")
def _phap_ly():
    mau = json.loads((GOC / 'public/web_order/chu-mac-dinh.json').read_text())
    chu = json.dumps(mau, ensure_ascii=False)
    for x in ('0318561568', 'Công ty TNHH Patisserie Vagabond', '9 Trần Cao Vân', '307/1 Nguyễn Văn Trỗi'):
        dung('không có khóa sửa được chứa %s' % x, x not in chu)
    trang = (GOC / 'trang/banh.html').read_text()
    dung('chân trang vẫn in mã số thuế cố định', 'Mã số thuế 0318561568' in trang)
    dung('mã số thuế không gắn data-vgb-chu', re.search(r'data-vgb-chu="[^"]+">Mã số thuế 0318561568', trang) is None)
