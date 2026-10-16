"""v597: ba lỗi giao diện web anh Việt chỉ ngày 15/10/2026.

1. Mục phụ kiện: khách tưởng phải mua thêm hộp và túi vì mục "tặng kèm"
   không nhắc tới, còn mục "mua thêm" lại có giá hộp, túi (Minh Vũ báo).
   Nay mục 03 liệt kê đúng đồ có sẵn trong giá bánh, mục 04 chỉ còn đồ
   trang trí, hộp, túi, nến dự phòng thu vào một dòng gấp.
2. Nút "Cách chọn size" mở hộp hướng dẫn theo poster Serving & Cutting Guide.
3. Trang Thành viên, Đặt bàn, Chính sách, Biên nhận: logo ảnh như /banh,
   tiêu đề nhỏ lại, bỏ dòng "Điểm đọc từ sổ điểm", ảnh thẻ hạng của designer
   cắt đúng góc bo, không còn góc trắng.

Ca kiểm chạy trang THẬT trong node (gia_lap_trang.js), bấm như khách, không gọi
thêm hàm nào ngoài chuỗi thao tác của khách (điều 15).
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]


def _chay(kich):
    r = subprocess.run(['node', str(GOC / 'khung/kiem_thu/gia_lap_trang.js'), str(GOC / 'trang/banh.html'),
                        '2026-10-16T08:00:00+07:00', kich], capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise AssertionError(r.stderr[-800:])
    return json.loads(r.stdout)


@ca('v597 mục 03: đủ năm đồ có sẵn trong giá bánh, mỗi dòng nhãn Có sẵn, không còn nĩa và dĩa')
def _co_san():
    d = _chay(r'''
const c=CAKES[0]; TODAY[c.sizes[0].id]=3; renderSheet(c);
const h=EL('#s-acc').innerHTML;
RA({h, so:(h.match(/<li>/g)||[]).length, co:(h.match(/tag-co-san/g)||[]).length,
    hop:ADDONS.find(a=>a.id==='BAPK00016').img, tui:ADDONS.find(a=>a.id==='BAPK00015').img});
''')
    la('năm dòng', d['so'], 5)
    la('mỗi dòng có nhãn Có sẵn', d['co'], 5)
    for ten in ('Hộp bánh', 'Túi vải đen The Vagabond', 'Dao gỗ cắt bánh', 'Nến xoắn', 'vỉ 6 cây', 'Cờ cắm in lời chúc'):
        dung('có ' + ten, ten in d['h'])
    dung('không liệt kê nĩa (đã sang phần theo yêu cầu)', 'Nĩa gỗ' not in d['h'])
    dung('không liệt kê dĩa', 'Dĩa' not in d['h'])
    dung('ảnh hộp dùng chung nguồn với dòng mua thêm', d['hop'] and ('src="' + d['hop'] + '"') in d['h'])
    dung('ảnh túi dùng chung nguồn', d['tui'] and ('src="' + d['tui'] + '"') in d['h'])


@ca('v597 mục 04: chỉ đồ trang trí hiện thẳng; hộp, túi, nến dự phòng nằm trong dòng gấp, chọn được, cộng tiền')
def _mua_them():
    d = _chay(r'''
const c=CAKES[0]; const s=c.sizes[0]; TODAY[s.id]=3; renderSheet(c); setSize(s.id);
const a=EL('#s-addons').innerHTML, b=EL('#s-addons-dp').innerHTML, moTruoc=!!EL('#s-duphong').open;
toggleAdd('BAPK00016');
const moSau=!!EL('#s-duphong').open, gia=curSize.p+chosenAddons().reduce((x,y)=>x+y.p,0);
addToCart();
RA({a,b,moTruoc,moSau,gia,giaMong:s.p+22000,adds:CART[0].adds.map(x=>x.id)});
''')
    for ma in ('BAPK00002', 'BAPK00024', 'BAPK00025'):
        dung('trang trí hiện thẳng ' + ma, ma in d['a'])
    for ma in ('BAPK00016', 'BAPK00015', 'BAPK00001'):
        dung('dự phòng không hiện thẳng ' + ma, ma not in d['a'])
        dung('dự phòng nằm trong dòng gấp ' + ma, ma in d['b'])
    la('dòng gấp đóng sẵn', d['moTruoc'], False)
    la('chọn đồ dự phòng thì dòng gấp mở', d['moSau'], True)
    la('cộng đúng giá hộp', d['gia'], d['giaMong'])
    la('giỏ có hộp', d['adds'], ['BAPK00016'])


@ca('v597 sửa lại dòng giỏ có hộp dự phòng: dòng gấp tự mở để khách thấy đồ đã chọn')
def _sua_dong():
    d = _chay(r'''
const c=CAKES[0]; const s=c.sizes[0]; TODAY[s.id]=3; renderSheet(c); setSize(s.id);
toggleAdd('BAPK00015'); addToCart();
renderSheet(CAKES[1]||c);
const moKhac=!!EL('#s-duphong').open; EL('#s-duphong').open=false;
suaDongGio(0);
RA({moKhac, moSua:!!EL('#s-duphong').open});
''')
    la('mở lại khi sửa dòng có đồ dự phòng', d['moSua'], True)


@ca('v597 thiệp nhỏ theo yêu cầu: vào giỏ, tách dòng, khôi phục khi sửa, có trên phiếu bếp nhân số lượng')
def _thiep():
    d = _chay(r'''
const c=CAKES[0]; const s=c.sizes[0]; TODAY[s.id]=5; renderSheet(c); setSize(s.id);
EL('#s-thiep').value='2'; EL('#s-nia').value='1'; addToCart();
renderSheet(c); setSize(s.id);
const veKhong=EL('#s-thiep').value;
EL('#s-thiep').value='0'; EL('#s-nia').value='1'; addToCart();
const soDong=CART.length, gio=EL('#cartList').innerHTML;
suaDongGio(0); const khoiPhuc=EL('#s-thiep').value;
CART[0].qty=3;
RA({dc:CART[0].dung_cu, soDong, gio, veKhong, khoiPhuc, bep:chuDungCu(CART[0]), bep2:chuDungCu({qty:2,dung_cu:{nia:0,dia:0,thiep:1}}),
    trong:chuDungCu({qty:1,dung_cu:{nia:0,dia:0,thiep:0}}), quaTay:chuanDungCu({nia:'99',dia:'-3',thiep:'x'})});
''')
    la('giỏ giữ thiệp', d['dc'], {'nia': 1, 'dia': 0, 'thiep': 2})
    la('khác số thiệp là hai dòng', d['soDong'], 2)
    dung('giỏ hiện thiệp', '2 thiệp nhỏ' in d['gio'])
    la('mở bánh mới thì ô thiệp về 0', str(d['veKhong']), '0')
    la('sửa dòng khôi phục thiệp', str(d['khoiPhuc']), '2')
    la('phiếu bếp nhân số lượng, giữ chữ cũ cho nĩa dĩa', d['bep'], '3 nĩa gỗ, 0 dĩa giấy, 6 thiệp nhỏ')
    la('chỉ có thiệp', d['bep2'], '2 thiệp nhỏ')
    la('không có gì thì rỗng', d['trong'], '')
    la('chặn số lạ trong khoảng 0 đến 30', d['quaTay'], {'nia': 30, 'dia': 0, 'thiep': 0})


@ca('v597 nút Cách chọn size: mở đủ bốn size theo poster, đóng bằng X, Escape và bấm nền; trả con trỏ về nút')
def _huong_size():
    d = _chay(r'''
const c=CAKES[0]; TODAY[c.sizes[0].id]=3; renderSheet(c);
const hop=EL('#huongSize'); hop.hidden=true;
const nut=EL('#s-huongsize'); nut.focus(); document.activeElement=nut;
moHuongSize();
const mo=!hop.hidden, luoi=EL('#hs-luoi').innerHTML, troMo=GHI.troVao, khoa=document.body.classList.contains('hs-mo');
let chan=0; document.dispatchEvent({type:'keydown',key:'Escape',stopImmediatePropagation(){chan++;}});
const dongEsc=hop.hidden, troVe=GHI.troVao, moKhoa=!document.body.classList.contains('hs-mo');
let chanKhiDong=0; document.dispatchEvent({type:'keydown',key:'Escape',stopImmediatePropagation(){chanKhiDong++;}});
moHuongSize(); dongHuongSize(); const dongX=hop.hidden;
moHuongSize(); hop.onclick&&hop.onclick({target:hop});
RA({mo,luoi,troMo,khoa,dongEsc,troVe,moKhoa,dongX,chan,chanKhiDong});
''')
    la('mở', d['mo'], True)
    la('khoá cuộn trang khi mở', d['khoa'], True)
    la('con trỏ vào nút đóng', d['troMo'], '#hs-dong')
    for cm, mieng, nguoi in (('12', '4 miếng', '2 - 4 người'), ('16', '8 miếng', '6 - 8 người'),
                             ('18', '12 miếng', '8 - 10 người'), ('20', '14 - 16 miếng', '10 - 12 người')):
        dung('Ø %s cm' % cm, ('Ø %s cm' % cm) in d['luoi'])
        dung(mieng, mieng in d['luoi'])
        dung(nguoi, nguoi in d['luoi'])
    la('bốn hình cắt', d['luoi'].count('<svg'), 4)
    la('Escape đóng', d['dongEsc'], True)
    la('Escape khi hộp mở không lan xuống bảng chi tiết bánh (bảng cũng đóng bằng Escape)', d['chan'], 1)
    la('hộp đã đóng thì Escape đi tiếp như cũ để đóng bảng', d['chanKhiDong'], 0)
    la('con trỏ trả về nút Cách chọn size', d['troVe'], '#s-huongsize')
    la('mở khoá cuộn', d['moKhoa'], True)
    la('nút đóng chạy', d['dongX'], True)


@ca('v597 tĩnh: nút Cách chọn size nằm trong mục Giá bánh của bánh thường, không ở bảng hàng mùa')
def _vi_tri_nut():
    s = (GOC / 'trang/banh.html').read_text()
    i = s.index('id="s-huongsize"')
    dung('nằm trước ô size của bánh thường', s.index('id="s-sizes"') > i > s.index('<section class="sheet" id="sheet">'))
    la('một nút', s.count('id="s-huongsize"'), 1)
    la('một hộp', s.count('id="huongSize"'), 1)
    dung('hộp là dialog modal có tiêu đề', 'role="dialog" aria-modal="true" aria-labelledby="hs-tieu-de"' in s)


@ca('v597 trang dịch vụ: logo ảnh đúng mã băm, có thanh điều hướng đánh dấu trang đang mở, không còn chữ VAGABOND tạm')
def _dau_trang():
    bam = hashlib.sha256((GOC / 'public/web_order/logo-trang.png').read_bytes()).hexdigest()[:12]
    for tep, dang in (('www/thanh-vien.html', '/thanh-vien'), ('www/dat-ban.html', '/dat-ban'),
                      ('www/chinh-sach.html', None), ('www/banh/xong.html', None)):
        s = (GOC / tep).read_text()
        dung(tep + ' logo ảnh đúng mã băm', '/assets/vagabond/web_order/logo-trang.png?v=' + bam in s)
        dung(tep + ' bỏ logo chữ', 'logo-chu' not in s and 'THE VAGABOND</span>' not in s)
        if dang:
            la(tep + ' đánh dấu đúng một trang', s.count('aria-current="page"'), 1)
            dung(tep + ' đánh dấu đúng trang', ('href="%s" aria-current="page"' % dang) in s)


@ca('v597 Thành viên: bỏ dòng sổ điểm, tiêu đề nhỏ lại, ảnh thẻ của designer cắt đúng góc bo')
def _thanh_vien():
    js = (GOC / 'public/web_order/thanh-vien.js').read_text()
    css = (GOC / 'public/web_order/thanh-vien.css').read_text()
    dung('không còn câu sổ điểm', 'thanh_vien_62cff3945' not in js and 'sổ điểm' not in js)
    dung('dòng trạng thái rỗng thì ẩn', '.thong-bao:empty{display:none}' in css)
    m = re.search(r'\.trang-dich-vu \.h1\{font-size:clamp\((\d+)px,[\d.]+vw,(\d+)px\)', css)
    dung('có cỡ tiêu đề', bool(m))
    dung('tiêu đề tối đa 60px (cũ 100px)', m and int(m.group(2)) <= 60)
    # Ảnh thẻ designer 1012x638, góc bo 48px (đo trên site 16/10): bán kính cắt phải >= 4.74% ngang, 7.52% dọc.
    m = re.search(r'\.the-hang\{[^}]*clip-path:inset\(([\d.]+)% ([\d.]+)% ([\d.]+)% ([\d.]+)% round ([\d.]+)% / ([\d.]+)%\)', css)
    dung('cắt ảnh thẻ bằng clip-path', bool(m))
    if m:
        dung('bán kính ngang đủ lớn', float(m.group(5)) >= 4.74)
        dung('bán kính dọc đủ lớn', float(m.group(6)) >= 7.52)
        dung('bỏ viền trắng đáy 6px trên 638px', float(m.group(3)) >= 6 / 638 * 100)
    dung('không tự vẽ thẻ, vẫn dùng ảnh hạng', 'id="anh-the"' in (GOC / 'www/thanh-vien.html').read_text())


@ca('v597 nhãn mới đều có trong sổ nhãn Editor, không đại từ cũ')
def _nhan():
    mau = json.loads((GOC / 'public/web_order/chu-mac-dinh.json').read_text())
    for k in ('huong_size_nut', 'huong_size_tieu_de', 'huong_size_mo_ta', 'huong_size_meo', 'huong_size_ok', 'huong_size_dong',
              'huong_size_so', 'huong_size_mieng', 'huong_size_nguoi', 'pk_co_san_muc', 'pk_co_san_tieu_de', 'pk_co_san_mo_ta',
              'pk_co_san_nhan', 'pk_theo_yeu_cau', 'pk_theo_yeu_cau_mo', 'so_dia_ba_mia', 'so_thiep_nho', 'dung_cu_thiep_gio',
              'pk_mua_them_muc', 'pk_mua_them_dan', 'pk_mua_them_mo', 'pk_du_phong_hoi', 'pk_du_phong_mo', 'pk_hop_banh',
              'pk_tui_vai', 'pk_nen_xoan_mo', 'pk_co_cam_mo', 'dv_nav_dat_ban', 'dv_nav_thanh_vien', 'dv_nav_nhan'):
        dung('có nhãn ' + k, k in mau)
    la('nến tặng là vỉ 6 cây (anh Việt chốt 16/10)', mau['pk_nen_xoan_mo']['mac_dinh'], 'vỉ 6 cây')
