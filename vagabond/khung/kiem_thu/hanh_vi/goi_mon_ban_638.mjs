/* v638: khách gọi món tại bàn qua QR, trang khách Vue (anh Việt duyệt 04/11/2026).

   MOUNT THẬT bằng Vue thật của repo qua bộ dựng cây tối giản (như
   thanh_toan_web_638.mjs): cắt ĐÚNG khối <main id="store"> của khuôn MAU, kho
   là kho thật (taoKho, kho-goi-ban), phần tab Tại quầy tính bằng đúng
   dungQuayHien mà app.js dùng, thành phần GoiTaiBan thật. Mạng giả. Khách bấm
   đúng chuỗi: mở link, bấm +, chọn đá đường, mở giỏ, gõ ghi chú, tên, mã giới
   thiệu, rời ô, bấm Gọi món; đọc đúng thân gửi máy chủ, rồi trạng thái đơn.
   Hai khối nội dung marketing (khoi-noi-dung, tieu-de-muc) thay bằng khối rỗng:
   chúng không dính gì tới gọi món.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/goi_mon_ban_638.mjs */
import {createRenderer, nextTick, computed} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {dungQuayHien} from '../../../public/web_vue/banh/kho-goi-ban.js';
import {GoiTaiBan} from '../../../public/web_vue/banh/goi-tai-ban.js';
import {AnhMon} from '../../../public/web_vue/banh/thanh-phan.js';
import {t, tMon} from '../../../public/web_vue/kho/chu.js';
import * as T from '../../../public/web_vue/kho/thuan.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

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
const cho = async () => { for (let i = 0; i < 5; i++) { await nextTick(); await new Promise(r => setTimeout(r, 0)); } };
function go(n, gt) { n.value = gt; (n.nghe.input || []).forEach(f => f({target: n})); }
const bam = async n => { dung('có nút để bấm', n); n.props.onClick(); await cho(); };

/* v-model của Vue hỏi document.activeElement lúc cập nhật ô; trình duyệt nào
   cũng có, node thì không. Chỉ cấp đúng ô đó, không dựng DOM giả. */
globalThis.document = globalThis.document || {activeElement: null};

const KHOI = MAU.match(/<main id="store"[\s\S]*?<\/main>/)[0];
dung('cắt được khối Tại quầy', KHOI.includes('storeBody') && KHOI.includes('goi-tai-ban'));
const Rong = {template: '<span></span>', props: ['viTri', 'dong']};

const K = 'c14c0648854b57a1';
const STORE = {ngay: '2026-11-04', cap_nhat: '2026-11-04 10:00', quay: [
  {ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1', dia_chi: '9 Trần Cao Vân',
    mon: [{ma: 'BAWC00115', ten: 'Mousse Chanh Dây', gia: 95000, anh: '', con: 1, nhom: 'Bánh lạnh'}],
    do_uong: [
      {ma: 'NUTR00021', ten: 'Trà Hoa Lài', gia: 45000, anh: '', nhom: 'Đồ uống',
        tc: [{nhom: 'Đá', lua_chon: ['Ít đá', 'Không đá']}, {nhom: 'Đường', lua_chon: ['50% đường']}]},
      {ma: 'NUIC00002', ten: 'Kem Vani', gia: 30000, anh: '', nhom: 'Đồ uống', tc: []}]},
  {ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', dia_chi: '21 Phạm Ngọc Thạch', mon: [], do_uong: []}]};

function moiTruong({tim: timKiem = '?diem=TCV&ban=5&k=' + K, mo = {ok: 1, diem: 'TCV', ten: 'District 1', ban: 5, mo_cua: 1, gio: '7:00 - 22:00'},
  goi = () => ({ok: 1, ma: 'TQ-261104-0001', token: 'a'.repeat(32)}), tt = () => ({ok: 1, trang_thai: 'Chờ nhận', mon: []})} = {}) {
  const vet = [], hen = [];
  const mang = {
    'vagabond.kiem_kho.con_tren_quay_web': () => JSON.parse(JSON.stringify(STORE)),
    'vagabond.goi_mon_ban.mo_ban': () => mo,
    'vagabond.goi_mon_ban.trang_thai': th => tt(th),
    'vagabond.gioi_thieu.kiem': th => (th.sdt === '0909123456' ? {ok: 1, ten: 'Chị Dễ'} : {ok: 0}),
    'vagabond.goi_mon_ban.goi': th => goi(th)
  };
  const mt = {
    t, tMon, bayGio: () => new Date('2026-11-04T10:00:00'),
    hen: (f, ms) => { hen.push({f, ms}); return hen.length; }, huyHen: () => {},
    doc: async (p, th) => { vet.push(['GET', p, th]); return mang[p] ? mang[p](th) : {}; },
    ghi: async (p, th) => { vet.push(['POST', p, th]); return mang[p] ? mang[p](th) : {ok: true}; },
    luuTru: null, suKien: () => {}, nd: {nhan: {}}, timKiem: () => timKiem,
    ngauNhien: n => Array.from({length: n}, () => Math.floor(Math.random() * 256))
  };
  const chayHen = async () => { await nextTick(); const ds = hen.splice(0); for (const x of ds) await x.f(); await cho(); };
  return {mt, vet, chayHen};
}

async function moTrang(o = {}) {
  const m = moiTruong(o);
  const kho = taoKho(m.mt);
  await kho.napQuay();
  await kho.goiBan.kiemLink();
  const goc = nut('goc');
  createApp({
    template: '<div>' + KHOI + '</div>',
    components: {AnhMon, GoiTaiBan, KhoiNoiDung: Rong, TieuDeMuc: Rong},
    setup: () => ({S: kho.S, kho, t, tMon, tab: computed(() => 'store'), quayHien: computed(() => dungQuayHien(kho.S, kho.goiBan.G, t)),
      tienTom: n => T.tienVN(n), mxh: (k, d) => d, telSo: () => '0931224334', telChu: () => '0931 224 334'})
  }).mount(goc);
  await cho();
  return {...m, kho, goc};
}
const nutThem = goc => tim(goc, n => n.props['data-them']);
const chip = goc => tim(theoId(goc, 'storeChip'), n => n.the === 'button').map(b => chu(b));

await ca('Link có k: chế độ gọi món của ĐÚNG quầy, nhãn "District 1 · Bàn 5", không còn chọn quầy khác, chip Tất cả / Bánh trên tủ / Đồ uống, nút + trên từng món', async () => {
  const {goc, kho} = await moTrang();
  la('chế độ', kho.goiBan.cheDo.value, 'goi');
  dung('nhãn bàn', chu(theoId(goc, 'gbDau')).includes('District 1 · Bàn 5'));
  la('không còn hàng chọn quầy', tim(goc, n => n.props.class === 'quay-chon').length, 0);
  la('chip', chip(goc), ['Tất cả · 3', 'Bánh trên tủ · 1', 'Đồ uống · 2']);
  la('nút + cho cả ba món', nutThem(goc).map(n => n.props['data-them']), ['BAWC00115', 'NUTR00021', 'NUIC00002']);
  dung('bánh có số còn, đồ uống không', chu(tim(goc, n => n.props['data-ma'] === 'BAWC00115')[0]).includes('Còn 1')
    && !chu(tim(goc, n => n.props['data-ma'] === 'NUTR00021')[0]).includes('Còn'));
  await bam(tim(theoId(goc, 'storeChip'), n => n.props['data-nhom'] === 'nuoc')[0]);
  la('chip Đồ uống chỉ còn đồ uống', nutThem(goc).map(n => n.props['data-them']), ['NUTR00021', 'NUIC00002']);
});

await ca('Không có link, hay link sai khoá: tab giữ chế độ xem như hiện nay (chọn quầy, không nút +, không thanh giỏ)', async () => {
  for (const o of [{tim: ''}, {mo: {ok: 0}}, {tim: '?diem=TCV&ban=5&k=xyz'}]) {
    const {goc, kho, vet} = await moTrang(o);
    la('chế độ xem', kho.goiBan.cheDo.value, '');
    la('không nút +', nutThem(goc).length, 0);
    la('còn chọn quầy', tim(goc, n => n.props.class === 'quay-chon').length, 1);
    dung('không thanh giỏ gọi món', !theoId(goc, 'gbBar'));
    if (o.tim !== undefined) la('link thiếu, sai dạng thì không hỏi máy chủ', vet.filter(x => x[1] === 'vagabond.goi_mon_ban.mo_ban').length, 0);
  }
});

await ca('Ngoài giờ mở cửa: link đúng nhưng chỉ xem, nói rõ giờ, không nút +', async () => {
  const {goc, kho} = await moTrang({mo: {ok: 1, diem: 'TCV', ten: 'District 1', ban: 5, mo_cua: 0, gio: '7:00 - 22:00'}});
  la('chế độ', kho.goiBan.cheDo.value, 'dong');
  dung('câu ngoài giờ', chu(theoId(goc, 'gbDau')).includes('ngoài giờ mở cửa (7:00 - 22:00)'));
  la('không nút +', nutThem(goc).length, 0);
});

await ca('Thêm món: bánh thêm thẳng và không quá số còn; đồ uống mở bảng chọn đá đường, chọn Ít đá rồi Thêm vào giỏ; thanh giỏ "2 món · 140.000 đ"', async () => {
  const {goc, kho} = await moTrang();
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  la('giỏ có bánh', G.gio.map(x => [x.ma, x.sl]), [['BAWC00115', 1]]);
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  la('còn 1 thì không thêm cái thứ hai', G.gio.map(x => [x.ma, x.sl]), [['BAWC00115', 1]]);
  dung('báo khách', kho.S.toast.chu.includes('chỉ còn 1'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  dung('bảng chọn mở', String(theoId(goc, 'gbChon').props.class).includes('open'));
  la('hai nhóm lựa chọn', tim(theoId(goc, 'gbChon'), n => n.the === 'h3').map(chu), ['Đá', 'Đường']);
  await bam(tim(goc, n => n.props['data-tc'] === 'Đá=Ít đá')[0]);
  dung('lựa chọn sáng', String(tim(goc, n => n.props['data-tc'] === 'Đá=Ít đá')[0].props.class).includes('on'));
  await bam(theoId(goc, 'gbThemLy'));
  dung('bảng chọn đóng', !String(theoId(goc, 'gbChon').props.class).includes('open'));
  la('giỏ', G.gio.map(x => [x.ma, x.sl, x.tc]), [['BAWC00115', 1, {}], ['NUTR00021', 1, {'Đá': 'Ít đá'}]]);
  dung('thanh giỏ hiện', String(theoId(goc, 'gbBar').props.class).includes('on'));
  la('thanh giỏ', chu(tim(theoId(goc, 'gbBar'), n => n.the === 'b')[0]), '2 món · 140.000 đ');
});

await ca('Giỏ và gọi món: ghi chú, tên, mã giới thiệu (rời ô hỏi gioi_thieu.kiem, hiện tên); Gọi món gửi đúng điểm, bàn, k, nonce, món không kèm giá; xong thì giỏ trống, đơn hiện Chờ quầy nhận rồi Đã nhận', async () => {
  let tt = {ok: 1, trang_thai: 'Chờ nhận', mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: ['Ít đá']}]};
  const {goc, kho, vet, chayHen} = await moTrang({tt: () => tt});
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  await bam(tim(goc, n => n.props['data-tc'] === 'Đá=Ít đá')[0]);
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  dung('giỏ mở', String(theoId(goc, 'gbGio').props.class).includes('open'));
  const dong = tim(theoId(goc, 'gbGio'), n => n.props['data-dong'] === 'NUTR00021')[0];
  dung('dòng ghi lựa chọn', chu(dong).includes('Ít đá'));
  await bam(tim(dong, n => n.the === 'button')[1]);
  la('nút + trong giỏ', G.gio[0].sl, 2);
  dung('dòng thanh toán tại quầy', chu(theoId(goc, 'gbCuoi')) === 'Thanh toán tại quầy khi dùng xong. Nhân viên mang món ra bàn 5.');
  dung('nút gọi có tổng', chu(theoId(goc, 'gbGoi')) === 'Gọi món · 90.000 đ');
  go(theoId(goc, 'gb-ghi'), 'mang ra trước'); go(theoId(goc, 'gb-ten'), 'Lan'); go(theoId(goc, 'gb-gt'), '0909 123 456');
  await cho();
  theoId(goc, 'gb-gt').props.onBlur(); await cho();
  la('hỏi giới thiệu bằng chữ số', vet.filter(x => x[1] === 'vagabond.gioi_thieu.kiem').map(x => x[2]), [{sdt: '0909123456'}]);
  la('hiện tên nhân viên', chu(theoId(goc, 'gbGtHint')), 'Nhân viên giới thiệu: Chị Dễ');
  await bam(theoId(goc, 'gbGoi'));
  const gui = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi');
  la('gửi một lần', gui.length, 1);
  const th = gui[0][2];
  la('thân gửi', [th.diem, th.ban, th.k, th.ghi_chu, th.ten, th.sdt_gioi_thieu], ['TCV', 5, K, 'mang ra trước', 'Lan', '0909123456']);
  dung('nonce 32 ký tự', /^[A-Za-z0-9_-]{32}$/.test(th.nonce));
  la('món gửi không kèm giá', JSON.parse(th.mon), [{ma: 'NUTR00021', sl: 2, tc: {'Đá': 'Ít đá'}}]);
  la('giỏ trống, giỏ đóng', [G.gio.length, G.moGio], [0, false]);
  dung('đơn hiện Chờ quầy nhận', chu(theoId(goc, 'gbDon')).includes('Chờ quầy nhận'));
  dung('có nút Gọi thêm món', theoId(goc, 'gbGoiThem'));
  tt = {ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:02', mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: ['Ít đá']}]};
  await chayHen();
  la('hỏi trạng thái bằng mã và khoá khách', vet.filter(x => x[1] === 'vagabond.goi_mon_ban.trang_thai').map(x => x[2]).slice(-1),
    [{ma: 'TQ-261104-0001', token: 'a'.repeat(32)}]);
  dung('đã nhận lúc ... đang pha chế', chu(theoId(goc, 'gbDon')).includes('Đã nhận lúc 10:02, đang pha chế'));
  dung('dòng món của đơn', chu(theoId(goc, 'gbDon')).includes('2 Trà Hoa Lài (Ít đá)'));
});

await ca('Gọi thêm món: đơn mới là lần gửi mới (nonce khác); quầy bận hết hạn thì báo nhắn nhân viên; máy chủ chặn thì giữ giỏ và nói lý do', async () => {
  let lan = 0;
  const {goc, kho, vet, chayHen} = await moTrang({
    goi: () => (++lan === 3 ? {ok: 0, cau: 'Mousse Chanh Dây vừa hết trên tủ. Quý khách bỏ món này ra khỏi giỏ.'} : {ok: 1, ma: 'TQ-' + lan, token: String(lan).repeat(32)}),
    tt: th => ({ok: 1, trang_thai: th.ma === 'TQ-1' ? 'Hết hạn' : 'Chờ nhận', mon: []})});
  const G = kho.goiBan.G;
  for (let i = 0; i < 2; i++) {
    await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
    await bam(theoId(goc, 'gbXemGio'));
    await bam(theoId(goc, 'gbGoi'));
  }
  const nonce = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi').map(x => x[2].nonce);
  dung('hai lần gửi hai nonce', nonce.length === 2 && nonce[0] !== nonce[1]);
  la('hai đơn', G.don.map(d => d.ma), ['TQ-1', 'TQ-2']);
  await chayHen();
  dung('đơn hết hạn: quầy đang bận', chu(theoId(goc, 'gbDon')).includes('Quầy đang bận, quý khách nhắn nhân viên gần nhất'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  dung('nói lý do', chu(theoId(goc, 'gbLoi')).includes('vừa hết trên tủ'));
  la('giữ giỏ để khách sửa', G.gio.map(x => x.ma), ['BAWC00115']);
});

await ca('Đồ uống không có bảng chọn (kem) thêm thẳng; lựa chọn lạ không lọt vào giỏ', async () => {
  const {goc, kho} = await moTrang();
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
  la('kem thêm thẳng', kho.goiBan.G.gio.map(x => [x.ma, x.tc]), [['NUIC00002', {}]]);
  kho.goiBan.them(STORE.quay[0].do_uong[0], {'Đá': 'Nhiều đá', 'Size': 'L'});
  la('lựa chọn lạ bị bỏ', kho.goiBan.G.gio[1].tc, {});
});

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong');
if (hong) { console.log(loi.join('\n')); process.exit(1); }
