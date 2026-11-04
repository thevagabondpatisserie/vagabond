/* v638: khách đặt bánh trên web thanh toán NGAY trên web (anh Việt 04/11/2026).

   MOUNT THẬT bằng Vue thật của repo (bộ dịch khuôn có trong bản esm-browser),
   qua một bộ dựng cây tối giản (createRenderer của Vue, nút là đối tượng JS):
   - Bước đặt bánh: khối Thanh toán, Mã ưu đãi, Mã giới thiệu và câu dưới tổng
     cắt từ ĐÚNG khuôn MAU, kho là kho thật (taoKho) với mạng giả. Khách bấm,
     gõ, rời ô; gửi đơn đi qua submitOrder thật, đọc đúng thân gửi máy chủ.
   - Biên nhận: thành phần taoTrang thật (trang/app.js), hẹn giờ bấm tay, mạng
     giả trả lời lượt hỏi trạng thái.
   Không dò chuỗi trong mã nguồn. Bố cục 390 px, vùng bấm đo trên Chromium thật.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/thanh_toan_web_638.mjs */
import {createRenderer, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {PAYS} from '../../../public/web_vue/banh/du-lieu.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {DongChu} from '../../../public/web_vue/banh/thanh-phan.js';
import {t, tMon} from '../../../public/web_vue/kho/chu.js';
import {taoTrang, NHIP_HOI} from '../../../public/web_vue/trang/app.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* ---------- bộ dựng cây của Vue, nút là đối tượng thường ---------- */
const nut = the => ({the, props: {}, con: [], cha: null, nghe: {}, value: '',
  addEventListener(ev, f) { (this.nghe[ev] = this.nghe[ev] || []).push(f); },
  removeEventListener(ev, f) { this.nghe[ev] = (this.nghe[ev] || []).filter(x => x !== f); }});
const {createApp} = createRenderer({
  createElement: the => nut(the),
  createText: chu => ({chu, cha: null}),
  createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; },
  setElementText: (n, chu) => { n.con = chu ? [{chu, cha: n}] : []; },
  insert: (con, cha, moc) => {
    if (con.cha) con.cha.con.splice(con.cha.con.indexOf(con), 1);
    const i = moc ? cha.con.indexOf(moc) : -1;
    if (i >= 0) cha.con.splice(i, 0, con); else cha.con.push(con);
    con.cha = cha;
  },
  remove: con => { if (con.cha) { con.cha.con.splice(con.cha.con.indexOf(con), 1); con.cha = null; } },
  parentNode: n => n.cha,
  nextSibling: n => (n.cha ? n.cha.con[n.cha.con.indexOf(n) + 1] || null : null),
  patchProp: (n, k, cu, moi) => { if (moi == null) delete n.props[k]; else n.props[k] = moi; },
  setScopeId: () => {}, insertStaticContent: () => { throw new Error('không dùng'); }
});
const chu = n => (n == null ? '' : n.chu != null ? n.chu : (n.con || []).map(chu).join(''));
function tim(n, dk, ra = []) { if (!n || !n.con) return ra; if (n.the && dk(n)) ra.push(n); n.con.forEach(x => tim(x, dk, ra)); return ra; }
const theoId = (goc, i) => tim(goc, n => n.props.id === i)[0];
const cho = async () => { for (let i = 0; i < 4; i++) { await nextTick(); await new Promise(r => setTimeout(r, 0)); } };
/* Khách gõ vào ô có v-model: đặt giá trị rồi phát sự kiện input như trình duyệt. */
function go(n, gt) { n.value = gt; (n.nghe.input || []).forEach(f => f({target: n})); }

/* ---------- bước đặt bánh: cắt đúng khuôn MAU ---------- */
const TT = MAU.slice(MAU.indexOf('<div id="payList">'), MAU.indexOf('<div class="sum" id="sum">'));
const CANH = MAU.match(/<div class="warn" id="warn">[\s\S]*?<\/div>/)[0];
dung('cắt được khối thanh toán', TT.includes('payList') && TT.includes('f-gt'));

function moiTruong(mang = {}, gio = '2026-10-11T08:00:00') {
  const vet = [], hen = [];
  const mt = {
    t, tMon, bayGio: () => new Date(gio),
    hen: (f, ms) => { hen.push({f, ms}); return hen.length; }, huyHen: () => {},
    doc: async (p, th) => { vet.push(['GET', p, th]); if (!mang[p]) return {}; return mang[p](th); },
    ghi: async (p, th) => { vet.push(['POST', p, th]); return mang[p] ? mang[p](th) : {ok: true}; },
    luuTru: null, suKien: () => {}, nd: {nhan: {}}
  };
  const chayHen = async () => { await nextTick(); const ds = hen.splice(0); for (const x of ds) await x.f(); await cho(); };
  return {mt, vet, hen, chayHen};
}
async function veBuocDat(kho) {
  const goc = nut('goc');
  createApp({template: '<div>' + TT + CANH + '</div>', components: {DongChu}, setup: () => ({S: kho.S, kho, t, PAYS})}).mount(goc);
  await cho();
  return goc;
}
const cauHinh = onepay => ({mien_phi_tu: 1000000, onepay, lien_he: {}, chinh_sach: [], quan: []});
const nutPt = goc => tim(theoId(goc, 'payList'), n => n.the === 'button').map(b => b.props['data-pt']);

await ca('Bước đặt bánh: cổng thẻ tắt thì chỉ Chuyển khoản, Tiền mặt; bật thì đủ 4 cách, mỗi cách một dòng giải thích; mặc định Chuyển khoản', async () => {
  for (const [bat, can] of [[0, ['bank', 'cash']], [1, ['bank', 'card', 'atm', 'cash']]]) {
    const {mt} = moiTruong({'vagabond.don_web.cau_hinh_web': () => cauHinh(bat)});
    const kho = taoKho(mt); await kho.napCauHinh();
    const goc = await veBuocDat(kho);
    la('các cách khi onepay=' + bat, nutPt(goc), can);
    tim(theoId(goc, 'payList'), n => n.the === 'button').forEach(b => {
      la('mỗi nút có tên và dòng giải thích', [tim(b, n => n.the === 'b').length, tim(b, n => n.the === 'span').length], [1, 1]);
      dung('dòng giải thích có chữ', chu(tim(b, n => n.the === 'span')[0]).length > 10);
    });
    la('mặc định', kho.S.CO.pay, 'bank');
  }
  const {mt} = moiTruong();
  const kho = taoKho(mt);
  la('chưa nạp cấu hình: chưa hứa cách thẻ', nutPt(await veBuocDat(kho)), ['bank', 'cash']);
});

await ca('Bước đặt bánh: bấm Thẻ ATM nội địa là chọn, câu dưới tổng nói đúng việc sau khi gửi (không còn hứa 15 phút, tự huỷ); cổng tắt giữa chừng thì về Chuyển khoản', async () => {
  const ch = {v: cauHinh(1)};
  const {mt} = moiTruong({'vagabond.don_web.cau_hinh_web': () => ch.v});
  const kho = taoKho(mt); await kho.napCauHinh();
  const goc = await veBuocDat(kho);
  const atm = tim(theoId(goc, 'payList'), n => n.props['data-pt'] === 'atm')[0];
  atm.props.onClick(); await cho();
  la('đã chọn', kho.S.CO.pay, 'atm');
  dung('nút sáng', String(atm.props.class).includes('on'));
  const canh = chu(theoId(goc, 'warn'));
  dung('nói bấm Thanh toán bằng thẻ trên biên nhận', canh.includes('Thanh toán bằng thẻ') && canh.includes('OnePay'));
  dung('không hứa 15 phút, tự huỷ', !/15 phút|tự huỷ/.test(canh));
  tim(theoId(goc, 'payList'), n => n.props['data-pt'] === 'cash')[0].props.onClick(); await cho();
  dung('tiền mặt', chu(theoId(goc, 'warn')).includes('tiền mặt khi nhận bánh'));
  tim(theoId(goc, 'payList'), n => n.props['data-pt'] === 'bank')[0].props.onClick(); await cho();
  dung('chuyển khoản: VietQR trên biên nhận, tự xác nhận', /VietQR/.test(chu(theoId(goc, 'warn'))) && /tự xác nhận/.test(chu(theoId(goc, 'warn'))));
  kho.S.CO.ship = null; kho.S.CO.shipTrangThai = 'chua_ro'; await cho();
  la('phí chưa rõ: thêm câu phí giao trả khi nhận', kho.cauThanhToan.value.length, 2);
  tim(theoId(goc, 'payList'), n => n.props['data-pt'] === 'card')[0].props.onClick(); await cho();
  ch.v = cauHinh(0); await kho.napCauHinh(); await cho();
  la('cổng tắt: cách đang chọn về chuyển khoản', [kho.S.CO.pay, nutPt(goc)], ['bank', ['bank', 'cash']]);
});

await ca('Mã giới thiệu: gõ số nhân viên rồi rời ô thì hiện tên; không thấy thì câu nhẹ; cửa lỗi hay chưa có thì im lặng; số sai độ dài không hỏi', async () => {
  const tra = {v: {ok: 1, ten: 'Lan'}};
  const {mt, vet} = moiTruong({'vagabond.gioi_thieu.kiem': () => { if (tra.v instanceof Error) throw tra.v; return tra.v; }});
  const kho = taoKho(mt);
  const goc = await veBuocDat(kho);
  const o = theoId(goc, 'f-gt');
  dung('ô có nhãn không bắt buộc', chu(goc).includes('Mã giới thiệu (không bắt buộc)'));
  go(o, '0909 123 456'); await cho();
  la('v-model nhận số', kho.S.f.gt, '0909 123 456');
  o.props.onBlur(); await cho();
  la('hỏi đúng cửa bằng POST, chỉ chữ số', vet.filter(x => x[1] === 'vagabond.gioi_thieu.kiem').map(x => [x[0], x[2]]), [['POST', {sdt: '0909123456'}]]);
  la('hiện tên', chu(theoId(goc, 'gtHint')), 'Nhân viên giới thiệu: Lan');
  tra.v = {ok: 0}; o.props.onBlur(); await cho();
  dung('không thấy', chu(theoId(goc, 'gtHint')).startsWith('Không tìm thấy nhân viên'));
  tra.v = new Error('HTTP 404'); o.props.onBlur(); await cho();
  la('cửa chưa có: im lặng', chu(theoId(goc, 'gtHint')), '');
  tra.v = {ok: 0, tat: 1}; o.props.onBlur(); await cho();
  la('công tắc vừa tắt: im lặng', chu(theoId(goc, 'gtHint')), '');
  tra.v = {exc_type: 'TooManyRequestsError'}; o.props.onBlur(); await cho();
  la('bị giới hạn lượt (lỗi máy chủ): im lặng, không báo nhầm là không thấy', chu(theoId(goc, 'gtHint')), '');
  const n = vet.length;
  go(o, '12345'); o.props.onBlur(); await cho();
  la('số quá ngắn không hỏi', [vet.length, chu(theoId(goc, 'gtHint'))], [n, '']);
});

await ca('v638 công tắc Hoa hồng giới thiệu tắt (cau_hinh_web.gioi_thieu = 0): ô Mã giới thiệu ẩn, không hỏi máy chủ, đơn gửi mã rỗng; bật lại thì ô hiện', async () => {
  const gui = [], ch = {v: Object.assign(cauHinh(1), {gioi_thieu: 0})};
  const {mt, vet} = moiTruong({'vagabond.don_web.cau_hinh_web': () => ch.v,
    'vagabond.don_hang.tao_don': th => { gui.push(JSON.parse(th.don)); return {ok: 1}; }});
  const kho = taoKho(mt);
  const goc0 = await veBuocDat(kho);
  dung('chưa nạp cấu hình: ô vẫn hiện', !!theoId(goc0, 'f-gt'));
  await kho.napCauHinh(); await cho();
  dung('tắt: không còn ô', !theoId(goc0, 'f-gt') && !chu(goc0).includes('Mã giới thiệu'));
  kho.S.f.gt = '0909123456'; await kho.kiemGioiThieu(); await cho();
  la('tắt: không hỏi cửa kiem', vet.filter(x => x[1] === 'vagabond.gioi_thieu.kiem').length, 0);
  kho.moBanh(kho.S.CAKES.find(c => c.k === 'CANDLE')); kho.addToCart(); kho.pick(3); kho.pickSlot(6);
  Object.assign(kho.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ'});
  kho.S.CO.dongy = true;
  await kho.submitOrder();
  la('tắt: đơn gửi mã rỗng dù khách đã gõ trước đó', gui[0].ma_gioi_thieu, '');
  ch.v = cauHinh(1); await kho.napCauHinh(); await cho();
  la('bật lại (cấu hình không có cờ tắt): ô hiện', !!theoId(goc0, 'f-gt'), true);
});

await ca('Gửi đơn: thân gửi máy chủ mang đúng thanh_toan khách chọn và ma_gioi_thieu chỉ chữ số; cách bị ẩn thì gửi bank', async () => {
  const gui = [];
  const {mt} = moiTruong({'vagabond.don_web.cau_hinh_web': () => cauHinh(1),
    'vagabond.don_hang.tao_don': th => { gui.push(JSON.parse(th.don)); return {ok: 1, duong_dan: '/banh/xong/' + 'a'.repeat(43)}; }});
  const kho = taoKho(mt); await kho.napCauHinh();
  const goc = await veBuocDat(kho);
  kho.moBanh(kho.S.CAKES.find(c => c.k === 'CANDLE')); kho.addToCart(); kho.pick(3); kho.pickSlot(6);
  Object.assign(kho.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ'});
  kho.S.CO.dongy = true;
  tim(theoId(goc, 'payList'), n => n.props['data-pt'] === 'atm')[0].props.onClick();
  go(theoId(goc, 'f-gt'), '0909-123-456'); await cho();
  la('gửi được', (await kho.submitOrder()).buoc, 'xong');
  la('thân gửi', [gui[0].thanh_toan, gui[0].ma_gioi_thieu], ['atm', '0909123456']);
  const {mt: mt2} = moiTruong({'vagabond.don_hang.tao_don': th => { gui.push(JSON.parse(th.don)); return {ok: 1}; }});
  const k2 = taoKho(mt2);
  k2.moBanh(k2.S.CAKES.find(c => c.k === 'CANDLE')); k2.addToCart(); k2.pick(3); k2.pickSlot(6);
  Object.assign(k2.S.f, {name: 'Khách', phone: '0901234567', addr: '12 Nguyễn Huệ', gt: '12'});
  k2.S.CO.dongy = true; k2.S.CO.pay = 'card';
  await k2.submitOrder();
  la('chưa biết cổng thẻ: gửi bank; mã sai bỏ', [gui[1].thanh_toan, gui[1].ma_gioi_thieu], ['bank', '']);
});

/* ---------- biên nhận Vue ---------- */
const TOKEN = 'T'.repeat(43);
const CK = {ngan_hang: 'MB Bank', stk: '0931224334', ten: 'CONG TY VAGABOND', noi_dung: 'S67355O91853T DW261100123',
  anh: 'data:image/svg+xml;base64,QUJD'};
function bienNhan(tt, them = {}) {
  return Object.assign({loai: 'bien_nhan', nhan: {}, bang: {gia_tri: {}, tien_to: []}, lien_he: [{href: 'https://zalo.me/thevagabondsaigon', khoa: '', ten: 'Nhắn Zalo'}],
    bien_nhan: {ma: 'DW-2611-00123', mon: [], tien_banh: '900.000 đ', phi_giao: '36.000 đ', tong: '936.000 đ', thanh_toan: 'Chuyển khoản (mã VietQR)', tt}}, them);
}
function cuaSo(duong = '/banh/xong/' + TOKEN, kho = new Map()) {
  const win = {location: {pathname: duong, replace() {}}, document: {title: ''},
    history: {replaceState(a, b, p) { win.location.pathname = p; }},
    sessionStorage: {getItem: k => (kho.has(k) ? kho.get(k) : null), setItem: (k, v) => kho.set(k, v)}};
  return {win, kho};
}
async function veBienNhan(D, mang = {}, win = cuaSo().win) {
  const vet = [], hen = [], di = [], chep = [];
  const mt = {win, hen: (f, ms) => { hen.push({f, ms}); }, dieuHuong: u => di.push(u), chep: async s => { chep.push(s); },
    ghi: async (p, th) => { vet.push([p, th]); return mang[p] ? mang[p](th) : {}; }};
  const goc = nut('goc');
  createApp(taoTrang(D, mt)).mount(goc);
  await cho();
  const chayHen = async () => { const ds = hen.splice(0); for (const x of ds) await x.f(); await cho(); };
  return {goc, vet, hen, di, chep, chayHen, win};
}
const ttCho = (them = {}) => Object.assign({cach: 'bank', trang_thai: 'cho', so: 936000, so_chu: '936.000 đ', con: 936000, con_chu: '936.000 đ',
  phi_sau: false, da_thu_chu: '', cach_thu: '', ck: CK}, them);

await ca('Biên nhận chuyển khoản: hiện VietQR, tài khoản, nội dung khớp đơn, nút chép; không còn câu "chưa thu tiền"; Zalo là hỗ trợ phụ', async () => {
  const b = await veBienNhan(bienNhan(ttCho()));
  const khoi = theoId(b.goc, 'bn-tt');
  dung('có khối thanh toán', khoi);
  la('ảnh QR', tim(khoi, n => n.the === 'img').map(n => n.props.src), [CK.anh]);
  const s = chu(khoi);
  dung('số tiền, số tài khoản, nội dung', s.includes('936.000 đ') && s.includes(CK.stk) && s.includes(CK.noi_dung));
  dung('không còn câu chưa thu tiền', !chu(b.goc).includes('chưa thu tiền'));
  theoId(b.goc, 'nut-chep').props.onClick(); await cho();
  la('chép đúng nội dung', b.chep, [CK.noi_dung]);
  dung('báo đã chép', chu(theoId(b.goc, 'nut-chep')) === 'Đã chép nội dung');
  dung('câu hỗ trợ đứng trước nút Zalo', chu(b.goc).indexOf('Cần hỗ trợ thanh toán') < chu(b.goc).indexOf('Nhắn Zalo'));
  const img = tim(khoi, n => n.the === 'img')[0];
  la('ảnh có kích thước', [img.props.width, img.props.height], [220, 220]);
});

await ca('Biên nhận chuyển khoản: hỏi lại mỗi 5 giây bằng token của tab; còn chờ thì hỏi tiếp; tiền về thì đổi sang Đã nhận tiền, bỏ QR, thôi hỏi; tải lại vẫn thấy đã nhận', async () => {
  const tra = [ttCho(), ttCho({trang_thai: 'da_thu', da_thu_chu: '936.000 đ', cach_thu: 'Chuyển khoản', ck: undefined})];
  const cs = cuaSo();
  const b = await veBienNhan(bienNhan(ttCho()), {'vagabond.thanh_toan_web.trang_thai': () => tra.shift()}, cs.win);
  la('hẹn hỏi sau 5 giây', b.hen.map(x => x.ms), [NHIP_HOI]);
  la('đường dẫn đã gỡ token', cs.win.location.pathname, '/banh/xong');
  await b.chayHen();
  la('hỏi đúng cửa, đúng token', b.vet, [['vagabond.thanh_toan_web.trang_thai', {token: TOKEN}]]);
  la('còn chờ: hẹn tiếp', b.hen.length, 1);
  dung('vẫn có QR', tim(b.goc, n => n.the === 'img').length === 1);
  await b.chayHen();
  const s = chu(theoId(b.goc, 'bn-tt'));
  dung('đã nhận', s.includes('Đã nhận tiền') && s.includes('936.000 đ · Chuyển khoản'));
  la('bỏ QR', tim(b.goc, n => n.the === 'img').length, 0);
  la('thôi hỏi', b.hen.length, 0);
  const r = await veBienNhan({loai: 'bien_nhan', khong_token: 1, nhan: {}, bang: {}}, {}, cuaSo('/banh/xong', cs.kho).win);
  dung('tải lại không token: đọc bản đã nhận trong tab', chu(theoId(r.goc, 'bn-tt')).includes('Đã nhận tiền'));
  la('không hỏi nữa', r.hen.length, 0);
});

await ca('Biên nhận thẻ: nút Thanh toán bằng thẻ tạo giao dịch đúng mã, khoá rồi chuyển sang OnePay; máy chủ từ chối thì hiện câu của máy chủ, cho bấm lại', async () => {
  const the = {ma: 'DW261100123', k: 'abcdef0123456789', duong: '/tra-the/DW261100123?k=abcdef0123456789'};
  let lan = 0;
  const b = await veBienNhan(bienNhan(ttCho({cach: 'atm', ck: undefined, the})), {'vagabond.onepay.tao_gd': () => (++lan === 1
    ? {_server_messages: JSON.stringify([JSON.stringify({message: 'Thanh toán thẻ đang tạm ngưng. Quý khách vui lòng chuyển khoản theo mã trên biên nhận.'})])}
    : {url: 'https://mtf.onepay.vn/paygate/vpcpay.op?vpc_CardList=DOMESTIC'})});
  la('không QR', tim(b.goc, n => n.the === 'img').length, 0);
  theoId(b.goc, 'nut-the').props.onClick(); await cho();
  la('gửi đúng mã, khoá', b.vet.filter(x => x[0] === 'vagabond.onepay.tao_gd').map(x => x[1]), [{ma: the.ma, k: the.k}]);
  dung('hiện câu máy chủ', chu(theoId(b.goc, 'bn-tt')).includes('Thanh toán thẻ đang tạm ngưng'));
  la('chưa chuyển trang, nút bấm lại được', [b.di, !!theoId(b.goc, 'nut-the').props.disabled], [[], false]);
  theoId(b.goc, 'nut-the').props.onClick(); await cho();
  la('chuyển sang OnePay', b.di, ['https://mtf.onepay.vn/paygate/vpcpay.op?vpc_CardList=DOMESTIC']);
});

await ca('Biên nhận tiền mặt: một câu, không QR, không nút thẻ, không hỏi lại; đơn huỷ không đòi tiền', async () => {
  const b = await veBienNhan(bienNhan({cach: 'cash', trang_thai: 'tien_mat', so: 936000, so_chu: '936.000 đ', con: 0, phi_sau: false}));
  const s = chu(theoId(b.goc, 'bn-tt'));
  dung('câu tiền mặt', s.includes('thanh toán tiền mặt khi nhận bánh'));
  la('không QR, không nút thẻ, không hỏi', [tim(b.goc, n => n.the === 'img').length, !!theoId(b.goc, 'nut-the'), b.hen.length], [0, false, 0]);
  const h = await veBienNhan(bienNhan({cach: 'bank', trang_thai: 'huy'}));
  la('đơn huỷ: không khối thanh toán', [!!theoId(h.goc, 'bn-tt'), h.hen.length], [false, 0]);
});

await ca('Biên nhận phí giao chưa rõ: QR đòi tiền bánh, nói phí giao trả khi nhận; quay về từ trang thẻ (không token) thì hỏi ngay', async () => {
  const cs = cuaSo();
  const b = await veBienNhan(bienNhan(ttCho({phi_sau: true, so_chu: '900.000 đ', con_chu: '900.000 đ'})), {}, cs.win);
  dung('câu phí giao', chu(theoId(b.goc, 'bn-tt')).includes('Phí giao quý khách trả khi nhận bánh'));
  const r = await veBienNhan({loai: 'bien_nhan', khong_token: 1, nhan: {}, bang: {}}, {}, cuaSo('/banh/xong', cs.kho).win);
  la('khôi phục từ tab, hỏi ngay', r.hen.map(x => x.ms), [0]);
});

console.log('Bo ca kiem thanh toan ngay tren web (v638)');
loi.forEach(d => console.log('  HONG  ' + d));
console.log(dat + ' ca dat, ' + hong + ' ca hong, tong ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);
