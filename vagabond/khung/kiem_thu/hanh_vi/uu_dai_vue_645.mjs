/* Ca kiểm HÀNH VI v645: mục Ưu đãi trên web bản Vue dàn lại theo kiểu Tuyển
   dụng (anh Việt 08/11/2026): danh sách thẻ ảnh gọn, bấm mới ra trang chi tiết
   #/uu-dai/<mã thẻ> có bốn ô tóm tắt, mã kèm nút chép, điều kiện, nút đặt bánh.

   Chạy THẬT các thành phần của web_vue/banh/noi-dung.js với Vue thật. Thẻ ERP
   dựng bằng ĐÚNG phép máy chủ khuyen_mai.the_web (python3, Frappe giả) trên hai
   chương trình kiểu thật (mã cố định SN10, quà sinh nhật mã dùng một lần theo
   hạng), không chép tay; ngày tính theo hôm nay để ca không hỏng theo lịch.
   Phần bấm trên trình duyệt thật kiểm ở cong_cu/kiem_web_vue_dom.cjs (F44).

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/uu_dai_vue_645.mjs */
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {ChuyenMuc, UD, ngayVN, tachUuDai, thoiGianUuDai, hanUuDai, oUuDai, moUuDai, ChepMa} from '../../../public/web_vue/banh/noi-dung.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const HOM_NAY = ngayVN();
const MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import datetime, json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond import khuyen_mai as km
hn = datetime.date.fromisoformat(sys.argv[2])
d = lambda n: str(hn + datetime.timedelta(days=n))
def ct(**k):
    c = {"name": "SN10", "ten": "Giảm 10% sinh nhật", "cach_thuc": "Giam tong hoa don", "kieu_giam": "Phan tram",
         "gia_tri": 10, "bat": 1, "hien_web": 1, "cach_ma": "Ma co dinh", "ma_co_dinh": "sn10", "can_otp": 0,
         "doi_tuong": "Moi khach", "kenh": "", "quay": "", "hd_toi_thieu": 500000, "sl_toi_thieu": 0,
         "tu_ngay": d(-7), "den_ngay": d(3), "gio_tu": None, "gio_den": None, "uu_tien": 10,
         "cong_don": 0, "giam_toi_da": 0, "web_mo_ta": "Mừng sinh nhật", "web_anh": "/files/sn.jpg",
         "dong_mon": [], "dong_bac": []}
    for t in km.THU_TRONG_TUAN:
        c.setdefault(t, 0)
    c.update(k)
    return c
ma = km.the_web(ct(), str(hn))
qua = km.the_web(ct(name="QUA-SINH-NHAT", ten="Quà sinh nhật thành viên", cach_thuc="Giam gia mon", gia_tri=100,
    giam_toi_da=185000, cach_ma="Ma dung mot lan", ma_co_dinh="", doi_tuong="Theo hang khach", hd_toi_thieu=0,
    tu_ngay=d(-7), den_ngay="", web_anh="", web_mo_ta="Tặng 1 bánh entremet trong tháng sinh nhật."), str(hn))
print(json.dumps({"ma": ma, "qua": qua, "sap": d(12), "het": d(20)}, ensure_ascii=False))
`, GOC, HOM_NAY]).toString());
const TAY = {id: 'tay-tra-chieu', loai: 'uu_dai', hien: true, tieu_de: 'Tiệc trà chiều cuối tuần', nhom: 'Ưu đãi',
  noi_dung: 'Một bánh và một ly trà.', dieu_kien: 'Áp dụng thứ Bảy, Chủ nhật', bat_dau: MAY.sap, ket_thuc: MAY.het,
  lien_ket: '/tiec', nut: 'Xem thực đơn'};

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Dựng cây như Vue: gặp thành phần thì gọi render() với props, data() và methods. */
function dung_cay(v) {
  if (v == null || v === false) return null;
  if (Array.isArray(v)) return v.map(dung_cay).filter(Boolean);
  if (typeof v !== 'object') return String(v);
  if (typeof v.type === 'object' && v.type.render) {
    const ctx = Object.assign({}, v.props || {}, v.type.data ? v.type.data() : {});
    Object.entries(v.type.methods || {}).forEach(([k, f]) => { ctx[k] = f.bind(ctx); });
    return dung_cay(v.type.render.call(ctx));
  }
  const con = typeof v.children === 'string' ? [v.children] : dung_cay(v.children || []);
  return {the: typeof v.type === 'string' ? v.type : '', props: v.props || {}, con};
}
function chu(n) { return n == null ? '' : typeof n === 'string' ? n : Array.isArray(n) ? n.map(chu).join('') : chu(n.con); }
function tim(n, dk, ra = []) {
  if (!n || typeof n === 'string') return ra;
  if (Array.isArray(n)) { n.forEach(x => tim(x, dk, ra)); return ra; }
  if (dk(n)) ra.push(n);
  tim(n.con, dk, ra);
  return ra;
}
const lop = c => n => String(n.props.class || '').split(' ').includes(c);
function ve() { return dung_cay(ChuyenMuc.render.call({loai: 'uu_dai'})); }
function napXong() { ND.khoi = [MAY.ma, MAY.qua, TAY]; ND.daTai = true; ND.xemThu = false; UD.mo = ''; }

await ca('máy chủ ra đúng hai thẻ ERP để dựng (không có thì mọi ca sau vô nghĩa)', async () => {
  la('mã', [MAY.ma.id, MAY.ma.ma_uu_dai, MAY.ma.dung_web], ['erp-SN10', 'SN10', 1]);
  la('quà', [MAY.qua.id, MAY.qua.ma_uu_dai, MAY.qua.dung_web], ['erp-QUA-SINH-NHAT', '', 0]);
});

await ca('danh sách: thẻ ảnh gọn như Tuyển dụng, chip nhóm, chip hạn, thời gian, mức giảm, bấm mở #/uu-dai/<mã>', async () => {
  napXong();
  const c = ve();
  dung('lưới td-ds', tim(c, lop('td-ds')).length === 1);
  const the = tim(c, lop('ud-the'));
  la('ba thẻ', the.map(x => x.props.href), ['#/uu-dai/erp-SN10', '#/uu-dai/erp-QUA-SINH-NHAT', '#/uu-dai/tay-tra-chieu']);
  la('tên', the.map(x => chu(tim(x, n => n.the === 'h2'))), ['Giảm 10% sinh nhật', 'Quà sinh nhật thành viên', 'Tiệc trà chiều cuối tuần']);
  la('chip nhóm', the.map(x => chu(tim(x, lop('td-bp')))), ['Mã giảm giá', 'Mã giảm giá', 'Ưu đãi']);
  la('chip hạn', the.map(x => chu(tim(x, lop('td-gap')))), ['Còn 3 ngày', '', 'Sắp diễn ra']);
  la('mức giảm (dòng đầu điều kiện của máy chủ)', the.map(x => chu(tim(x, lop('ud-muc')))),
    ['Giảm 10%', 'Giảm 100%, tối đa 185.000đ cho món áp dụng', 'Xem chi tiết']);
  dung('thời gian thẻ mã có khoảng ngày', / - /.test(chu(tim(the[0], lop('td-meta')))));
  la('thẻ quà không hạn', chu(tim(the[1], lop('td-meta'))), 'Từ ' + MAY.qua.bat_dau.split('-').reverse().join('/'));
  la('có ảnh thì ảnh, không thì nền ghi mức giảm gọn', [tim(the[0], n => n.the === 'img').length, chu(tim(the[1], lop('ud-nen-chu')))], [1, 'Giảm 100%']);
  dung('không hiện mã nội bộ', !chu(c).includes('erp-') && !chu(c).includes('QUA-SINH-NHAT'));
});

await ca('chi tiết thẻ mã cố định: bốn ô, mã kèm nút chép, Chi tiết, Điều kiện (đơn tối thiểu), nút Đặt bánh ngay', async () => {
  napXong(); UD.mo = 'erp-SN10';
  const c = ve(), ct = tim(c, lop('ud-chi-tiet'))[0];
  dung('mở chi tiết, ẩn danh sách', !!ct && tim(c, lop('ud-the')).length === 0);
  la('tên', chu(tim(ct, n => n.the === 'h1')), 'Giảm 10% sinh nhật');
  la('dòng trên tên', chu(tim(ct, lop('td-tren'))), 'Mã giảm giá · Còn 3 ngày');
  const o = tim(ct, n => String(n.props.class || '').startsWith('td-o')).map(chu);
  la('ô ưu đãi, áp dụng, mã', [o[0], o[2], o[3]], ['Ưu đãiGiảm 10%', 'Áp dụngĐặt bánh trên web', 'MãSN10']);
  dung('ô thời gian', /^Thời gian\d\d\/\d\d\/2026 - /.test(o[1]));
  la('mã chép', chu(tim(ct, lop('ud-ma-chu'))), 'Mã ưu đãiSN10');
  la('nút chép', chu(tim(ct, lop('ud-chep'))), 'Chép mã');
  la('các mục', tim(ct, lop('td-muc')).map(m => chu(tim(m, n => n.the === 'h3'))), ['Chi tiết', 'Điều kiện']);
  la('điều kiện', tim(ct, lop('td-muc'))[1].con[1].con.map(chu), ['Đơn từ 500.000 đ', 'Đặt bánh trên web: nhập mã ở bước thanh toán.']);
  const nut = tim(ct, lop('td-ung'))[0];
  la('nút đặt bánh', [nut.props.href, chu(nut)], ['#/dat-truoc', 'Đặt bánh ngay']);
  la('nút quay lại', tim(ct, lop('td-lui'))[0].props.href, '#/uu-dai');
});

await ca('chi tiết quà sinh nhật (theo hạng, mã dùng một lần): Tại cửa hàng, tiệm gửi mã riêng, KHÔNG mời đặt trên web', async () => {
  napXong(); UD.mo = 'erp-QUA-SINH-NHAT';
  const ct = tim(ve(), lop('ud-chi-tiet'))[0];
  const o = tim(ct, n => String(n.props.class || '').startsWith('td-o')).map(chu);
  la('ô', [o[0], o[2], o[3]], ['Ưu đãiGiảm 100%, tối đa 185.000đ cho món áp dụng', 'Áp dụngTại cửa hàng', 'MãThe Vagabond gửi riêng từng khách']);
  la('dòng trên tên', chu(tim(ct, lop('td-tren'))), 'Mã giảm giá · Đang diễn ra');
  la('không ô chép mã', tim(ct, lop('ud-ma')).length, 0);
  la('không nút đặt bánh', tim(ct, lop('td-ung')).length, 0);
  la('điều kiện không lặp dòng mức giảm', tim(ct, lop('td-muc'))[1].con[1].con.map(chu),
    ['Mã dùng một lần, tiệm gửi riêng cho từng khách.', 'Chương trình theo hạng hoặc nhóm khách chỉ dùng tại cửa hàng.']);
});

await ca('chi tiết thẻ Marketing soạn tay: liên kết riêng thay nút đặt bánh, chữ nút lấy từ thẻ, Sắp diễn ra', async () => {
  napXong(); UD.mo = 'tay-tra-chieu';
  const ct = tim(ve(), lop('ud-chi-tiet'))[0];
  const nut = tim(ct, lop('td-ung'))[0];
  la('nút riêng', [nut.props.href, chu(nut), typeof nut.props.onClick], ['/tiec', 'Xem thực đơn', 'undefined']);
  la('dòng trên tên', chu(tim(ct, lop('td-tren'))), 'Ưu đãi · Sắp diễn ra');
  const o = tim(ct, n => String(n.props.class || '').startsWith('td-o')).map(chu);
  la('ô ưu đãi và mã', [o[0], o[2], o[3]], ['Ưu đãiƯu đãi', 'Áp dụngXem điều kiện bên dưới', 'MãKhông cần mã']);
  la('điều kiện giữ nguyên chữ soạn', tim(ct, lop('td-muc'))[1].con[1].con.map(chu), ['Áp dụng thứ Bảy, Chủ nhật']);
});

await ca('liên kết ngoài không an toàn (javascript:) thì không dùng, quay về nút Đặt bánh ngay', async () => {
  napXong();
  ND.khoi = [Object.assign({}, TAY, {lien_ket: 'javascript:alert(1)'})]; UD.mo = 'tay-tra-chieu';
  const nut = tim(tim(ve(), lop('ud-chi-tiet'))[0], lop('td-ung'))[0];
  la('nút', [nut.props.href, chu(nut)], ['#/dat-truoc', 'Đặt bánh ngay']);
});

await ca('mở link ưu đãi đã kết thúc hay mã lạ: báo kết thúc, có nút xem ưu đãi khác; chưa tải xong thì Đang tải', async () => {
  napXong(); UD.mo = 'erp-CU';
  const c = ve();
  dung('báo', chu(c).includes('Ưu đãi này đã kết thúc'));
  la('nút', tim(c, n => n.props.href === '#/uu-dai').length, 1);
  ND.daTai = false;
  dung('đang tải', chu(ve()).includes('Đang tải ưu đãi'));
  ND.daTai = true; UD.mo = '';
});

await ca('nút Chép mã: chép đúng mã và báo; trình duyệt chặn thì báo cách chép tay', async () => {
  const vet = [];
  const cu = Object.getOwnPropertyDescriptor(globalThis, 'navigator');
  const dat_nav = cb => Object.defineProperty(globalThis, 'navigator', {value: {clipboard: {writeText: cb}}, configurable: true});
  try {
    dat_nav(async s => { vet.push(s); });
    const ctx = Object.assign({ma: 'SN10'}, ChepMa.data());
    await ChepMa.methods.chep.call(ctx);
    la('đã chép', [vet, ctx.bao], [['SN10'], 'Đã chép mã']);
    dat_nav(async () => { throw new Error('NotAllowedError'); });
    const ctx2 = Object.assign({ma: 'SN10'}, ChepMa.data());
    await ChepMa.methods.chep.call(ctx2);
    la('bị chặn', ctx2.bao, 'Chưa chép được, quý khách giữ lâu vào mã để chép.');
  } finally { if (cu) Object.defineProperty(globalThis, 'navigator', cu); }
});

await ca('bấm thẻ: đổi đường dẫn bằng pushState rồi phát popstate, cuộn về đầu; xem thử trong trình biên tập thì chỉ chọn khối', async () => {
  const vet = [];
  const win = {location: {pathname: '/banh', search: ''}, history: {pushState: (s, t, u) => vet.push(['push', u])},
    dispatchEvent: e => vet.push(['su_kien', e.type]), PopStateEvent: class { constructor(t) { this.type = t; } }, scrollTo: (x, y) => vet.push(['cuon', x, y])};
  moUuDai('erp-SN10', win);
  moUuDai('', win);
  la('vết', vet, [['push', '/banh#/uu-dai/erp-SN10'], ['su_kien', 'popstate'], ['cuon', 0, 0], ['push', '/banh#/uu-dai'], ['su_kien', 'popstate'], ['cuon', 0, 0]]);
  napXong();
  const the = tim(ve(), lop('ud-the'))[0];
  let chan = 0;
  ND.xemThu = true;
  const goc = globalThis.window;
  globalThis.window = {parent: {postMessage: m => vet.push(['chon', m.id])}, location: {origin: 'http://x'}};
  try { the.props.onClick({preventDefault: () => { chan++; }}); } finally { globalThis.window = goc; ND.xemThu = false; }
  la('xem thử chỉ chọn khối', [chan, vet[vet.length - 1]], [1, ['chon', 'erp-SN10']]);
});

await ca('phép thuần: tách mức giảm, thời gian, hạn (biên 0, 7, 8 ngày), ô mã', async () => {
  la('tách ERP', tachUuDai({nguon: 'erp', dieu_kien: 'Giảm 10%\nA\n\nB'}), {muc: 'Giảm 10%', dk: ['A', 'B']});
  la('tách tay', tachUuDai({dieu_kien: 'A\nB'}), {muc: '', dk: ['A', 'B']});
  la('thời gian', [thoiGianUuDai({bat_dau: '2026-11-01', ket_thuc: '2026-11-30'}), thoiGianUuDai({bat_dau: '2026-11-01', ket_thuc: '2026-11-01'}),
    thoiGianUuDai({ket_thuc: '2026-11-30'}), thoiGianUuDai({})], ['01/11/2026 - 30/11/2026', '01/11/2026', 'Đến 30/11/2026', 'Đang diễn ra']);
  const hn = '2026-11-08';
  la('hạn', [hanUuDai({ket_thuc: '2026-11-08'}, hn), hanUuDai({ket_thuc: '2026-11-15'}, hn), hanUuDai({ket_thuc: '2026-11-16'}, hn),
    hanUuDai({bat_dau: '2026-11-09'}, hn), hanUuDai({}, hn)], ['Ngày cuối', 'Còn 7 ngày', '', 'Sắp diễn ra', '']);
  la('ô mã', [oUuDai({ma_uu_dai: 'A1'})[3].chu, oUuDai({nguon: 'erp', dieu_kien: 'x\nMã dùng một lần, tiệm gửi'})[3].chu, oUuDai({})[3].chu],
    ['A1', 'The Vagabond gửi riêng từng khách', 'Không cần mã']);
  la('dung_web 0 mà không nói cửa hàng (kênh khác): không khẳng định Tại cửa hàng',
    oUuDai({nguon: 'erp', dung_web: 0, dieu_kien: 'x\nChương trình không mở cho kênh Website.'})[2].chu, 'Xem điều kiện bên dưới');
});

console.log('Ca hanh vi web Vue Uu dai v645');
loi.forEach(l => console.log('  HONG  ' + l));
console.log(dat + ' ca dat, ' + hong + ' ca hong');
process.exit(hong ? 1 : 0);
