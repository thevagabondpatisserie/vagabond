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
import {GoiTaiBan, GoiTaiBanNoi} from '../../../public/web_vue/banh/goi-tai-ban.js';
import {KenhNoi} from '../../../public/web_vue/banh/noi-dung.js';
import {gomSize, tachSize, khopTim, chipNhom, LY_DO_GOI} from '../../../public/web_vue/banh/kho-goi-ban.js';
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

/* v639: phần nổi (thanh giỏ, bảng chọn, giỏ, chuông) nằm NGOÀI main để không bị
   dải tab đè; cắt cả hai khối của khuôn thật. */
const KHOI = MAU.match(/<main id="store"[\s\S]*?<\/main>/)[0] + MAU.match(/<goi-tai-ban-noi[^>]*>/)[0];
dung('cắt được khối Tại quầy', KHOI.includes('storeBody') && KHOI.includes('<goi-tai-ban ') && KHOI.includes('<goi-tai-ban-noi'));
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
  return {mt, vet, chayHen, mang};
}

async function moTrang(o = {}) {
  const m = moiTruong(o);
  const kho = taoKho(m.mt);
  await kho.napQuay();
  await kho.goiBan.kiemLink();
  const goc = nut('goc');
  createApp({
    template: '<div>' + KHOI + '</div>',
    components: {AnhMon, GoiTaiBan, GoiTaiBanNoi, KhoiNoiDung: Rong, TieuDeMuc: Rong},
    setup: () => {
      const quayHien = computed(() => dungQuayHien(kho.S, kho.goiBan.G, t));
      return {S: kho.S, kho, t, tMon, tab: computed(() => 'store'), quayHien, nhacQr: computed(() => kho.goiBan.G.daKiem && !!quayHien.value),
        tienTom: n => T.tienVN(n), mxh: (k, d) => d, telSo: () => '0931224334', telChu: () => '0931 224 334'};
    }
  }).mount(goc);
  await cho();
  return {...m, kho, goc};
}
const nutThem = goc => tim(goc, n => n.props['data-them']);
const chip = goc => tim(theoId(goc, 'storeChip'), n => n.the === 'button').map(b => chu(b));
/* v655: hàng tầng lớn (Tất cả, Combo, Bánh, Đồ uống): "mã=số". */
const tang = goc => tim(theoId(goc, 'storeTang'), n => n.the === 'button').map(b => b.props['data-tang'] + '=' + chu(b).replace(/\D/g, ''));
const bamTang = async (goc, n) => bam(tim(theoId(goc, 'storeTang'), x => x.props['data-tang'] === n)[0]);

await ca('Link có k: chế độ gọi món của ĐÚNG quầy, nhãn "District 1 · Bàn 5", không còn chọn quầy khác, chip Tất cả / Bánh trên tủ / Đồ uống, nút + trên từng món', async () => {
  const {goc, kho} = await moTrang();
  la('chế độ', kho.goiBan.cheDo.value, 'goi');
  dung('nhãn bàn', chu(theoId(goc, 'gbDau')).includes('District 1 · Bàn 5'));
  la('không còn hàng chọn quầy', tim(goc, n => n.props.class === 'quay-chon').length, 0);
  la('tầng lớn', tang(goc), ['=3', 'banh=1', 'nuoc=2']);
  la('Tất cả: không có hàng chip nhỏ', chip(goc), []);
  la('nút + cho cả ba món', nutThem(goc).map(n => n.props['data-them']), ['BAWC00115', 'NUTR00021', 'NUIC00002']);
  dung('bánh có số còn, đồ uống không', chu(tim(goc, n => n.props['data-ma'] === 'BAWC00115')[0]).includes('Còn 1')
    && !chu(tim(goc, n => n.props['data-ma'] === 'NUTR00021')[0]).includes('Còn'));
  await bamTang(goc, 'nuoc');
  la('đồ uống chỉ một nhóm: không bày chip nhỏ', chip(goc), []);
  la('tầng Đồ uống chỉ còn đồ uống', nutThem(goc).map(n => n.props['data-them']), ['NUTR00021', 'NUIC00002']);
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
  dung('đã nhận lúc ... đang pha chế (ngay trên dòng tóm tắt)', chu(theoId(goc, 'gbDon')).includes('Đã nhận lúc 10:02, đang pha chế'));
  dung('đơn đã nhận: chi tiết còn gập', !theoId(goc, 'gbDonChiTiet'));
  await bam(theoId(goc, 'gbDonXem'));
  dung('dòng món của đơn sau khi mở', chu(theoId(goc, 'gbDon')).includes('2 Trà Hoa Lài (Ít đá)'));
});

await ca('Codex PR #542 vòng 1 (AGENTS.md 2b.17): khối đã gọi thu thành một dòng đếm số kèm trạng thái đơn mới nhất, nút Gọi thêm đứng trước chi tiết; đơn bị từ chối tự mở; dòng món hai món đầu rồi "và N nữa"', async () => {
  let lan = 0;
  const TT = {};
  const {goc, kho, chayHen} = await moTrang({
    goi: () => ({ok: 1, ma: 'TQ-' + (++lan), token: String(lan).repeat(32)}),
    tt: th => TT[th.ma] || {ok: 1, trang_thai: 'Chờ nhận', mon: []}});
  for (let i = 0; i < 3; i++) {
    await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
    await bam(theoId(goc, 'gbXemGio'));
    await bam(theoId(goc, 'gbGoi'));
  }
  la('ba đơn', kho.goiBan.G.don.length, 3);
  const don = theoId(goc, 'gbDon');
  dung('một dòng đếm số', chu(theoId(goc, 'gbDonXem')).includes('Đã gọi 3 đơn'));
  dung('kèm trạng thái đơn mới nhất', chu(theoId(goc, 'gbDonXem')).includes('Chờ quầy nhận'));
  dung('chưa có thẻ đơn nào khi gập', !theoId(goc, 'gbDonChiTiet') && tim(don, n => n.props && n.props['data-don']).length === 0);
  dung('nhãn mở là Xem chi tiết', chu(theoId(goc, 'gbDonXem')).includes('Xem chi tiết'));
  /* nút Gọi thêm nằm TRƯỚC chi tiết trong cây, cùng dòng tóm tắt */
  const tom = tim(don, n => n.props && n.props.class === 'gb-tom')[0];
  dung('Gọi thêm nằm trong dòng tóm tắt', tom && tim(tom, n => n.props && n.props.id === 'gbGoiThem').length === 1);
  await bam(theoId(goc, 'gbDonXem'));
  la('mở ra đủ ba thẻ, mới nhất trước', tim(theoId(goc, 'gbDonChiTiet'), n => n.props && n.props['data-don']).map(n => n.props['data-don']), ['TQ-3', 'TQ-2', 'TQ-1']);
  dung('nhãn đổi thành Thu gọn', chu(theoId(goc, 'gbDonXem')).includes('Thu gọn'));
  await bam(theoId(goc, 'gbDonXem'));
  dung('gập lại được', !theoId(goc, 'gbDonChiTiet'));
  /* đơn giữa bị từ chối: khách phải xử lý nên tự mở, dù đơn mới nhất vẫn chờ */
  TT['TQ-2'] = {ok: 1, trang_thai: 'Từ chối', ly_do: 'Hết Trà Hoa Lài', mon: []};
  TT['TQ-3'] = {ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:05', mon: [
    {ten: 'Trà Hoa Lài', sl: 2, tc: ['Ít đá']}, {ten: 'Cà Phê Sữa', sl: 1, tc: []}, {ten: 'Matcha Latte', sl: 1, tc: ['Ít ngọt']}, {ten: 'Bánh Mì', sl: 3, tc: []}]};
  await chayHen();
  dung('tự mở khi có đơn từ chối', !!theoId(goc, 'gbDonChiTiet'));
  dung('thẻ từ chối ghi lý do', chu(theoId(goc, 'gbDon')).includes('Quầy từ chối: Hết Trà Hoa Lài'));
  const the3 = tim(theoId(goc, 'gbDonChiTiet'), n => n.props && n.props['data-don'] === 'TQ-3')[0];
  la('dòng món: hai món đầu rồi và N nữa', chu(tim(the3, n => n.the === 'span')[0]), '2 Trà Hoa Lài (Ít đá), 1 Cà Phê Sữa và 2 nữa');
  dung('không nối cả bốn món', !chu(the3).includes('Matcha'));
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

/* ====================== v639 vòng 2 (anh Việt duyệt mẫu 05/11/2026) ====================== */
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
const STORE2 = {ngay: '2026-11-05', cap_nhat: '2026-11-05 10:00', quay: [
  {ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1', dia_chi: '9 Trần Cao Vân',
    mon: [{ma: 'BAWC00115', ten: 'Mousse Chanh Dây', gia: 95000, anh: '', con: 3, nhom: 'Bánh lạnh', mo_ta: 'Chanh dây Đà Lạt'}],
    do_uong: [
      {ma: 'NUTR00031', ten: 'Trà Sữa Lài Kem Phô Mai, Size M, Đá/Iced', gia: 75000, anh: '/files/tsl.jpg', nhom: 'Đồ uống', nhom_goc: 'Trà', mo_ta: 'Trà lài ủ lạnh', khong_pha: 0,
        tc: [{nhom: 'Đá', lua_chon: ['Ít đá', 'Không đá']}]},
      {ma: 'NUTR00032', ten: 'Trà Sữa Lài Kem Phô Mai, Size L, Đá/Iced', gia: 85000, anh: '', nhom: 'Đồ uống', nhom_goc: 'Trà', mo_ta: '', khong_pha: 0,
        tc: [{nhom: 'Đá', lua_chon: ['Ít đá', 'Không đá']}]},
      {ma: 'NUCF00003', ten: 'Cà phê sữa', gia: 40000, anh: '', nhom: 'Đồ uống', nhom_goc: 'Cà phê', mo_ta: '', khong_pha: 0, tc: []},
      {ma: 'NUTR00040', ten: 'Kombucha Chill , Chai 300ml', gia: 100000, anh: '', nhom: 'Đồ uống', nhom_goc: 'Trà', mo_ta: '', khong_pha: 1, tc: []}],
    topping: [{ma: 'TPNC00001', ten: 'Trân châu ô long', gia: 10000}, {ma: 'TPNC00002', ten: 'Thay sữa yến mạch', gia: 20000}]},
  {ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', dia_chi: '21 Phạm Ngọc Thạch', mon: [], do_uong: [], topping: []}]};

async function moTrang2(o = {}) {
  const m = moiTruong(o);
  m.mang['vagabond.kiem_kho.con_tren_quay_web'] = () => JSON.parse(JSON.stringify(o.store || STORE2));
  m.mang['vagabond.goi_mon_ban.goi_nhan_vien'] = th => (o.chuong ? o.chuong(th) : {ok: 1, ma: 'GNV-261105-0001', luc: '10:58'});
  const kho = taoKho(m.mt);
  await kho.napQuay();
  await kho.goiBan.kiemLink();
  const g = nut('goc');
  createApp({
    template: '<div>' + KHOI + '</div>',
    components: {AnhMon, GoiTaiBan, GoiTaiBanNoi, KhoiNoiDung: Rong, TieuDeMuc: Rong},
    setup: () => {
      const quayHien = computed(() => dungQuayHien(kho.S, kho.goiBan.G, t));
      return {S: kho.S, kho, t, tMon, tab: computed(() => 'store'), quayHien, nhacQr: computed(() => kho.goiBan.G.daKiem && !!quayHien.value),
        tienTom: n => T.tienVN(n), mxh: (k, d) => d, telSo: () => '0931224334', telChu: () => '0931 224 334'};
    }
  }).mount(g);
  await cho();
  return {...m, kho, goc: g};
}

await ca('v639 phép thuần: tách size khỏi tên, gộp size cùng tên một dòng (M trước L, giá thấp nhất), tìm bỏ dấu, chip theo nhóm gốc', async () => {
  /* Ảnh anh Việt chụp 05/11: bảng nằm trong <main> (z-index riêng) bị dải tab đè. Phần nổi phải đứng sau mọi </main>. */
  dung('phần nổi (thanh giỏ, bảng chọn, giỏ, chuông) nằm ngoài mọi <main>', MAU.lastIndexOf('</main>') < MAU.indexOf('<goi-tai-ban-noi') && MAU.indexOf('<goi-tai-ban-noi') > 0);
  dung('phần trong dòng (món đã gọi) nằm trước danh sách món của tab Tại quầy', MAU.indexOf('<goi-tai-ban ') < MAU.indexOf('id="gbTim"'));
  la('tách size', tachSize('Hồng Trà Vải Thiều, Size L, Đá/Iced'), {goc: 'Hồng Trà Vải Thiều', size: 'L', nong: false});
  la('set trà nóng', tachSize('Trà Earl Grey, Set trà 2 người, Nóng/Hot'), {goc: 'Trà Earl Grey, Set trà 2 người', size: '', nong: true});
  la('không size', tachSize('Cà phê sữa'), {goc: 'Cà phê sữa', size: '', nong: false});
  const ds = gomSize([{ma: 'B', ten: 'Trà Lài, Size L, Đá/Iced', gia: 85000, anh: ''}, {ma: 'A', ten: 'Trà Lài, Size M, Đá/Iced', gia: 75000, anh: '/x.jpg', mo_ta: 'mô tả'},
    {ma: 'C', ten: 'Cà phê sữa', gia: 40000, anh: ''}, {ma: 'D', ten: 'Trà Lài, Size M, Nóng/Hot', gia: 70000, anh: ''}]);
  la('ba dòng: lạnh gộp, nóng riêng, cà phê riêng', ds.map(x => [x.ma, x.ten, x.gia, x.gop, x.bienThe.map(b => b.size + ':' + b.ma)]),
    [['A', 'Trà Lài', 75000, true, ['M:A', 'L:B']], ['C', 'Cà phê sữa', 40000, false, [':C']], ['D', 'Trà Lài, Size M, Nóng/Hot', 70000, false, ['M:D']]]);
  la('ảnh, mô tả lấy từ size có', [ds[0].anh, ds[0].mo_ta], ['/x.jpg', 'mô tả']);
  dung('tìm bỏ dấu, từng từ', khopTim('Trà Sữa Lài Kem Phô Mai', '', 'tra lai') && khopTim('Bánh Canelé', '', 'CANELE') && !khopTim('Cà phê sữa', '', 'trà'));
  dung('tìm trong mô tả', khopTim('Mousse', 'Chanh dây Đà Lạt', 'chanh day'));
  la('chip', chipNhom([{loai: 'banh'}], [{nhom_goc: 'Trà'}, {nhom_goc: 'Trà'}, {nhom_goc: 'Cacao'}, {nhom_goc: ''}], t).map(n => n.n + '=' + n.ten + '·' + n.so),
    ['=Tất cả·5', 'banh=Bánh trên tủ·1', 'nuoc:Trà=Trà·2', 'nuoc:Cacao=Cacao·1', 'nuoc=Đồ uống·1']);
});

await ca('v639 thực đơn: chip theo nhóm (Bánh trên tủ, Trà, Cà phê), size M và L gộp một dòng ghi "Size M · L", ô tìm lọc bỏ dấu và báo khi không khớp', async () => {
  const {goc, kho} = await moTrang2();
  la('tầng', tang(goc), ['=4', 'banh=1', 'nuoc=3']);
  la('bốn dòng, size gộp', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['BAWC00115', 'NUTR00031', 'NUCF00003', 'NUTR00040']);
  const dong = tim(goc, n => n.props['data-ma'] === 'NUTR00031')[0];
  dung('tên gộp không còn size, ghi Size M · L, có mô tả', chu(dong).includes('Trà Sữa Lài Kem Phô Mai') && !chu(dong).includes('Size M, Đá') && chu(dong).includes('Size M · L') && chu(dong).includes('Trà lài ủ lạnh'));
  await bamTang(goc, 'nuoc');
  la('chip nhỏ của Đồ uống', chip(goc), ['Tất cả đồ uống · 3', 'Trà · 2', 'Cà phê · 1']);
  await bam(tim(theoId(goc, 'storeChip'), n => n.props['data-nhom'] === 'nuoc:Trà')[0]);
  la('chip Trà', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['NUTR00031', 'NUTR00040']);
  go(theoId(goc, 'gbTimO'), 'ca phe'); await cho();
  la('tìm "ca phe" (đang ở chip Trà vẫn ra vì chip Trà không có, coi như không khớp)', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), []);
  dung('báo không khớp', chu(theoId(goc, 'gbTimRong')).includes('"ca phe"'));
  await bamTang(goc, '');
  la('tìm ở Tất cả', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['NUCF00003']);
  go(theoId(goc, 'gbTimO'), 'chanh day'); await cho();
  la('tìm theo mô tả bánh', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['BAWC00115']);
  kho.S.timQuay = ''; await cho();
  la('xoá chữ tìm', tim(goc, n => n.props['data-ma']).length, 4);
});

await ca('v639 bảng chọn: size đổi giá, đá đường, topping có giá cộng vào, số lượng; giỏ ghi size và topping; Gọi món gửi mã topping; thanh giỏ tính đủ', async () => {
  const {goc, kho, vet} = await moTrang2();
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00031'));
  dung('bảng chọn mở', String(theoId(goc, 'gbChon').props.class).includes('open'));
  la('hai size', tim(theoId(goc, 'gbSize'), n => n.props['data-size']).map(n => n.props['data-size']), ['NUTR00031', 'NUTR00032']);
  la('giá size M trước', chu(theoId(goc, 'gbGiaChon')), '75.000 đ');
  await bam(tim(goc, n => n.props['data-size'] === 'NUTR00032')[0]);
  la('chọn L', chu(theoId(goc, 'gbGiaChon')), '85.000 đ');
  await bam(tim(goc, n => n.props['data-tc'] === 'Đá=Ít đá')[0]);
  la('hai topping có giá', tim(theoId(goc, 'gbTopping'), n => n.props['data-tp']).map(n => chu(n)), ['Trân châu ô long+10.000 đ', 'Thay sữa yến mạch+20.000 đ']);
  await bam(tim(goc, n => n.props['data-tp'] === 'TPNC00001')[0]);
  la('topping cộng giá', chu(theoId(goc, 'gbGiaChon')), '95.000 đ');
  la('ô tích sáng', tim(goc, n => n.props['data-tp'] === 'TPNC00001')[0].props['aria-checked'], 'true');
  await bam(tim(goc, n => n.props['data-tp'] === 'TPNC00001')[0]);
  await bam(tim(goc, n => n.props['data-tp'] === 'TPNC00001')[0]);
  const qty = tim(theoId(goc, 'gbChon'), n => n.props.class === 'gb-step')[0];
  await bam(tim(qty, n => n.the === 'button')[1]);
  la('số lượng 2, nút ghi tổng', [chu(theoId(goc, 'gbSlChon')), chu(theoId(goc, 'gbThemLy'))], ['2', 'Thêm · 190.000 đ']);
  await bam(theoId(goc, 'gbThemLy'));
  la('giỏ: mã size L, tên có (L), đá, topping, 2 ly', G.gio.map(x => [x.ma, x.ten, x.sl, x.tc, x.tp.map(y => y.ma), x.gia]),
    [['NUTR00032', 'Trà Sữa Lài Kem Phô Mai (L)', 2, {'Đá': 'Ít đá'}, ['TPNC00001'], 85000]]);
  la('thanh giỏ', chu(tim(theoId(goc, 'gbBar'), n => n.the === 'b')[0]), '2 món · 190.000 đ');
  dung('nút + của dòng gộp tô đặc', String(tim(goc, n => n.props['data-them'] === 'NUTR00031')[0].props.class).includes('co'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUCF00003'));
  dung('cà phê không đá đường nhưng có topping quầy: vẫn mở bảng', String(theoId(goc, 'gbChon').props.class).includes('open') && !theoId(goc, 'gbSize'));
  await bam(theoId(goc, 'gbThemLy'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00040'));
  dung('Kombucha chai: thêm thẳng, không hỏi gì', !String(theoId(goc, 'gbChon').props.class).includes('open'));
  la('giỏ ba dòng', G.gio.map(x => [x.ma, x.tp.length]), [['NUTR00032', 1], ['NUCF00003', 0], ['NUTR00040', 0]]);
  await bam(theoId(goc, 'gbXemGio'));
  const d = tim(theoId(goc, 'gbGio'), n => n.props['data-dong'] === 'NUTR00032')[0];
  dung('dòng giỏ ghi topping và thành tiền', chu(d).includes('Ít đá · + Trân châu ô long') && chu(d).includes('190.000 đ'));
  await bam(theoId(goc, 'gbGoi'));
  const th = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi')[0][2];
  la('thân gửi có tp theo mã, dòng không topping không có khoá tp', JSON.parse(th.mon),
    [{ma: 'NUTR00032', sl: 2, tc: {'Đá': 'Ít đá'}, tp: ['TPNC00001']}, {ma: 'NUCF00003', sl: 1, tc: {}}, {ma: 'NUTR00040', sl: 1, tc: {}}]);
  la('bảng thuần: tối đa 5 topping', (() => { kho.goiBan.moBangChon(dungQuayHien(kho.S, G, t).mon.find(m => m.ma === 'NUTR00031')); ['a', 'b', 'c', 'd', 'e', 'f'].forEach(x => kho.goiBan.chonTp(x)); return Object.keys(G.chon.tp).length; })(), 5);
});

await ca('v639 chuông gọi nhân viên: chọn lý do một chạm, Việc khác có ô chữ, gửi đúng điểm bàn khoá nonce lý do; xong hiện giờ báo; Xin tính tiền trong giỏ chọn sẵn lý do; máy chủ chặn thì nói lý do; ngoài giờ không mở', async () => {
  const {goc, kho, vet} = await moTrang2();
  dung('mở chuông', kho.goiBan.moChuong(''));
  await cho();
  dung('bảng chuông mở', String(theoId(goc, 'gbChuong').props.class).includes('open'));
  la('năm lý do', tim(theoId(goc, 'gbChuong'), n => n.props['data-lydo']).map(n => n.props['data-lydo']), LY_DO_GOI);
  dung('chưa chọn thì nút Báo quầy khoá', theoId(goc, 'gbChuongGui').props.disabled === true);
  await bam(tim(goc, n => n.props['data-lydo'] === 'Việc khác')[0]);
  dung('Việc khác có ô chữ', theoId(goc, 'gb-chuong-chi-tiet'));
  go(theoId(goc, 'gb-chuong-chi-tiet'), 'xin thêm ghế em bé'); await cho();
  await bam(theoId(goc, 'gbChuongGui'));
  const gui = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi_nhan_vien');
  la('gửi một lần', gui.length, 1);
  la('thân gửi', [gui[0][2].diem, gui[0][2].ban, gui[0][2].k, gui[0][2].ly_do, gui[0][2].chi_tiet], ['TCV', 5, K, 'Việc khác', 'xin thêm ghế em bé']);
  dung('nonce 32 ký tự', /^[A-Za-z0-9_-]{32}$/.test(gui[0][2].nonce));
  dung('hiện đã báo', chu(theoId(goc, 'gbChuongXong')).includes('Đã báo quầy lúc 10:58. Nhân viên tới bàn 5'));
  kho.goiBan.dongChuong(); await cho();
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00040'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGioTinhTien'));
  la('giỏ đóng, chuông mở với lý do Xin tính tiền', [kho.goiBan.G.moGio, kho.goiBan.G.chuong.mo, kho.goiBan.G.chuong.lyDo], [false, true, 'Xin tính tiền']);
});

await ca('v639 chuông: máy chủ chặn thì giữ bảng và nói câu của máy chủ; ngoài giờ mở cửa không mở được chuông', async () => {
  const {goc, kho} = await moTrang2({chuong: () => ({ok: 0, cau: 'Bàn này vừa gọi 3 lần. Nhân viên đang tới.'})});
  kho.goiBan.moChuong('Xin thêm nước lọc, đá'); await cho();
  await bam(theoId(goc, 'gbChuongGui'));
  la('bị chặn, vẫn mở bảng, không "đã báo"', [kho.goiBan.G.chuong.mo, chu(theoId(goc, 'gbChuongLoi')), kho.goiBan.G.chuong.xong],
    [true, 'Bàn này vừa gọi 3 lần. Nhân viên đang tới.', null]);
  const {kho: k2} = await moTrang2({mo: {ok: 1, diem: 'TCV', ten: 'District 1', ban: 5, mo_cua: 0, gio: '7:00 - 22:00'}});
  la('ngoài giờ', k2.goiBan.moChuong(''), false);
});

await ca('v639 không có mã QR: tab Tại quầy hiện banner nhắc quét mã, lưới thẻ như cũ; có mã thì không có banner', async () => {
  const {goc} = await moTrang2({tim: ''});
  dung('banner nhắc', chu(theoId(goc, 'gbNhacQr')).includes('Quét mã QR dán trên bàn'));
  la('tên gộp size cả ở chế độ xem', chu(tim(goc, n => n.props['data-ma'] === 'NUTR00031')[0]).includes('Size M · L'), true);
  const {goc: g2} = await moTrang2();
  dung('có mã thì không banner', !theoId(g2, 'gbNhacQr'));
});

await ca('v639 nút nổi Gọi nhân viên nằm trong cụm kênh nối (dưới Nhắn Zalo), nâng theo thanh giỏ', async () => {
  const bam2 = [];
  const vn = KenhNoi.render.call({chuong: ly => bam2.push(ly), nang: 82, day: 0, mo: false, $refs: {}});
  const con = (vn.children || []);
  const nut = con.find(c => c && c.props && c.props.id === 'kenhChuong');
  dung('có nút chuông', nut);
  /* v640: icon chuông riêng (component BieuTuong), không còn emoji 🔔. */
  const icon = nut.children[0];
  dung('icon chuông riêng, không emoji', icon.props.class.includes('kenh-icon-chuong') && icon.children[0].props && icon.children[0].props.ten === 'chuong'
    && !EMOJI.test(JSON.stringify(nut.children.map(c => c.children))));
  nut.props.onClick();
  la('bấm mở chuông', bam2, ['']);
  dung('nâng 82 + 16', String(vn.props.style).includes('calc(98px'));
  const vn2 = KenhNoi.render.call({chuong: null, nang: 0, day: 0, mo: false, $refs: {}});
  dung('không QR thì không nút', !(vn2.children || []).some(c => c && c.props && c.props.id === 'kenhChuong'));
});

await ca('Codex PR #542 vòng 1: gửi chuông mất phản hồi rồi khách đổi lý do: lần gửi mới phải mang nonce MỚI (máy chủ không trả nhầm lời cũ); thử lại cùng nội dung thì giữ nonce', async () => {
  let lan = 0;
  const {kho, vet} = await moTrang2({chuong: th => (++lan === 1 ? (() => { throw new Error('mất mạng'); })() : {ok: 1, ma: 'GNV-' + lan, luc: '10:5' + lan})});
  kho.goiBan.moChuong('Gọi nhân viên tới bàn');
  await kho.goiBan.goiNhanVien();
  dung('lần đầu lỗi, chưa đã báo', !!kho.goiBan.G.chuong.loi && !kho.goiBan.G.chuong.xong);
  kho.goiBan.dongChuong();
  kho.goiBan.moChuong('Xin tính tiền');
  await kho.goiBan.goiNhanVien();
  const gui = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi_nhan_vien').map(x => x[2]);
  la('hai lần gửi, hai lý do', gui.map(x => x.ly_do), ['Gọi nhân viên tới bàn', 'Xin tính tiền']);
  dung('đổi lý do thì nonce khác', gui[0].nonce !== gui[1].nonce);
  la('đã báo với đúng lý do', kho.goiBan.G.chuong.xong.lyDo, 'Xin tính tiền');
  /* thử lại cùng nội dung sau khi lỗi: giữ nonce để máy chủ gộp */
  lan = 0;
  const m2 = await moTrang2({chuong: th => (++lan === 1 ? (() => { throw new Error('mất mạng'); })() : {ok: 1, ma: 'GNV-9', luc: '11:00'})});
  m2.kho.goiBan.moChuong('Xin thêm nước lọc, đá');
  await m2.kho.goiBan.goiNhanVien();
  await m2.kho.goiBan.goiNhanVien();
  const g2 = m2.vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi_nhan_vien').map(x => x[2]);
  dung('cùng nội dung thì cùng nonce', g2.length === 2 && g2[0].nonce === g2[1].nonce);
});

/* v640: menu đang chạy của điểm (Biên tập menu) gửi nhom_menu theo thứ tự quản lý
   kéo thả; đồ uống mang nhom_hien, tc có mac_dinh, tp là mã topping kèm được. */
const STORE3 = JSON.parse(JSON.stringify(STORE2));
{
  const q = STORE3.quay[0];
  const tcTs = [{nhom: 'Đá', lua_chon: ['Bình thường', 'Ít đá', 'Không đá'], mac_dinh: 'Bình thường'},
    {nhom: 'Đường', lua_chon: ['Bình thường', '50% đường'], mac_dinh: 'Bình thường'}];
  q.nhom_menu = [{ma: 'n-tra-sua', ten: 'Trà sữa', loai: 'nuoc'}, {ma: 'banh', ten: 'Bánh trên tủ', loai: 'banh'}, {ma: 'n-ca-phe', ten: 'Cà phê', loai: 'nuoc'}];
  q.do_uong = [
    {...q.do_uong[0], nhom_hien: 'n-tra-sua', tc: tcTs, tp: ['TPNC00001', 'TPNC00002']},
    {...q.do_uong[1], nhom_hien: 'n-tra-sua', tc: tcTs, tp: ['TPNC00001']},
    {...q.do_uong[2], nhom_hien: 'n-ca-phe', tc: [], tp: ['TPNC00002']}];
}

await ca('v640 trang bàn theo menu của điểm: chip và món theo thứ tự quản lý kéo thả; Đá, Đường mỗi nhóm chọn một, mặc định sáng sẵn và không gửi lên; topping theo món và theo size; giỏ có ảnh; icon riêng, không emoji; nút đóng nằm trong tiêu đề', async () => {
  const {goc, kho, vet} = await moTrang2({store: STORE3});
  const G = kho.goiBan.G;
  la('tầng', tang(goc), ['=3', 'banh=1', 'nuoc=2']);
  la('món theo thứ tự nhóm', nutThem(goc).map(n => n.props['data-them']), ['NUTR00031', 'BAWC00115', 'NUCF00003']);
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00031'));
  const chon = theoId(goc, 'gbChon');
  dung('tiêu đề bảng ghi nhóm', chu(tim(chon, n => n.the === 'small')[0]) === 'Trà sữa');
  const dau = tim(chon, n => n.props.class === 'gb-dau-bang')[0];
  dung('nút đóng nằm trong dòng tiêu đề', dau && tim(dau, n => n.props.class === 'gb-x').length === 1);
  dung('không còn lớp close, qty dính luật chung thao-tac.css', !tim(chon, n => /\b(close|qty)\b/.test(String(n.props.class || ''))).length);
  const nutTc = k => tim(goc, n => n.props['data-tc'] === k)[0];
  la('mặc định sáng sẵn', [nutTc('Đá=Bình thường').props['aria-pressed'], nutTc('Đường=Bình thường').props['aria-pressed']], ['true', 'true']);
  await bam(nutTc('Đá=Ít đá'));
  la('chọn Ít đá thì Bình thường tắt', [nutTc('Đá=Ít đá').props['aria-pressed'], nutTc('Đá=Bình thường').props['aria-pressed']], ['true', 'false']);
  await bam(nutTc('Đá=Ít đá'));
  la('bấm lại Ít đá thì về mặc định', nutTc('Đá=Bình thường').props['aria-pressed'], 'true');
  await bam(nutTc('Đường=50% đường'));
  la('size M: hai topping', tim(theoId(goc, 'gbTopping'), n => n.props['data-tp']).map(n => n.props['data-tp']), ['TPNC00001', 'TPNC00002']);
  await bam(tim(goc, n => n.props['data-tp'] === 'TPNC00002')[0]);
  dung('ô tích có dấu tick SVG đặt trong ô', tim(tim(goc, n => n.props['data-tp'] === 'TPNC00002')[0], n => n.the === 'svg' && n.props['data-bt'] === 'tick').length === 1);
  await bam(tim(goc, n => n.props['data-size'] === 'NUTR00032')[0]);
  la('size L: topping riêng của L, topping không kèm được bị bỏ', [tim(theoId(goc, 'gbTopping'), n => n.props['data-tp']).map(n => n.props['data-tp']), Object.keys(G.chon.tp)], [['TPNC00001'], []]);
  await bam(theoId(goc, 'gbThemLy'));
  la('giỏ: chỉ gửi mức khác mặc định', G.gio.map(x => [x.ma, x.tc]), [['NUTR00032', {'Đường': '50% đường'}]]);
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUCF00003'));
  la('cà phê: chỉ topping khai cho cà phê', tim(theoId(goc, 'gbTopping'), n => n.props['data-tp']).map(n => n.props['data-tp']), ['TPNC00002']);
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  const gio = theoId(goc, 'gbGio');
  const dong = tim(gio, n => n.props['data-dong'] === 'NUTR00032')[0];
  la('dòng giỏ có ảnh món', tim(dong, n => n.the === 'img')[0].props.src, '/files/tsl.jpg');
  dung('dòng giỏ ghi mức đã chọn', chu(dong).includes('50% đường'));
  la('hai nút cuối giỏ dùng icon riêng', ['gbGioChuong', 'gbGioTinhTien'].map(i => tim(theoId(goc, i), n => n.the === 'svg')[0].props['data-bt']), ['chuong', 'hoaDon']);
  dung('không còn emoji trong giỏ', !EMOJI.test(chu(gio)));
  await bam(theoId(goc, 'gbGioChuong'));
  la('năm lý do, năm icon riêng', tim(theoId(goc, 'gbChuong'), n => n.props.class === 'gb-ly-ic').map(n => tim(n, x => x.the === 'svg')[0].props['data-bt']),
    ['vayTay', 'hoaDon', 'lyDa', 'daoNia', 'chat']);
  dung('không còn emoji trong bảng chuông', !EMOJI.test(chu(theoId(goc, 'gbChuong'))));
  await bam(theoId(goc, 'gbChuong') && tim(theoId(goc, 'gbChuong'), n => n.props['data-lydo'] === 'Xin tính tiền')[0]);
  dung('vết gửi chưa có gì', !vet.some(x => x[1] === 'vagabond.goi_mon_ban.goi'));
});

/* Codex PR #543: quản lý tắt riêng tuỳ chọn cho size L nhưng giữ cho size M. Đổi
   size trong bảng phải đổi luôn nhóm tuỳ chọn, bỏ mức không còn hợp lệ; giỏ và
   lần gửi chỉ mang tuỳ chọn của đúng size đã chọn (cửa gọi món từ chối nếu sai). */
const STORE4 = JSON.parse(JSON.stringify(STORE3));
STORE4.quay[0].do_uong[1].tc = [];
await ca('v640 Codex #543: đổi size thì đổi nhóm tuỳ chọn theo size; size L không có tuỳ chọn thì không mang mức của M vào giỏ', async () => {
  const {goc, kho} = await moTrang2({store: STORE4});
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00031'));
  const nutTc = k => tim(goc, n => n.props['data-tc'] === k)[0];
  await bam(nutTc('Đá=Ít đá'));
  la('size M: có Đá, Đường', tim(theoId(goc, 'gbChon'), n => n.props['data-tc']).length, 5);
  await bam(tim(goc, n => n.props['data-size'] === 'NUTR00032')[0]);
  la('size L: không còn nhóm tuỳ chọn nào', tim(theoId(goc, 'gbChon'), n => n.props['data-tc']).length, 0);
  await bam(theoId(goc, 'gbThemLy'));
  la('giỏ: L không mang Ít đá của M', G.gio.map(x => [x.ma, x.tc]), [['NUTR00032', {}]]);
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00031'));
  await bam(tim(goc, n => n.props['data-size'] === 'NUTR00032')[0]);
  await bam(tim(goc, n => n.props['data-size'] === 'NUTR00031')[0]);
  /* Lớp thứ hai: them() tự lọc theo nhóm của đúng size, kể cả khi lựa chọn cũ lọt
     tới (gọi thẳng, không qua bảng chọn). */
  const mGop = G.chon.m, btL = mGop.bienThe.find(b => b.ma === 'NUTR00032');
  G.gio.splice(0);
  kho.goiBan.them(mGop, {'Đá': 'Ít đá'}, {bt: btL});
  la('them(): size L bỏ mức Đá không có', G.gio.map(x => [x.ma, x.tc]), [['NUTR00032', {}]]);
  la('quay lại M: nhóm của M hiện lại, mặc định sáng sẵn', [nutTc('Đá=Bình thường') && nutTc('Đá=Bình thường').props['aria-pressed'], nutTc('Đường=Bình thường') && nutTc('Đường=Bình thường').props['aria-pressed']], ['true', 'true']);
});

/* Codex PR #543 vòng 2: menu có mặt nhưng RỖNG (quản lý tắt hết nhóm, kể cả Bánh
   trên tủ) không được coi là máy chủ bản cũ; bánh đã tắt không hiện lại. */
await ca('v640 Codex #543: menu rỗng thì không hiện món nào; menu không có nhóm Bánh thì bánh ẩn và đầu mục không đếm; máy chủ cũ không gửi menu thì như trước', async () => {
  const quay = x => ({STORE: {quay: [Object.assign({ma: 'TCV', mon: [{ma: 'B1', ten: 'Canelé', gia: 65000, con: 5}],
    do_uong: [{ma: 'N1', ten: 'Cà phê sữa', gia: 40000, nhom_hien: 'n-ca-phe', tc: [], tp: []}]}, x)]}, quayChon: 'TCV', timQuay: '', nhomQuay: ''});
  const r0 = dungQuayHien(quay({nhom_menu: []}), null, t);
  la('menu rỗng: không món, không đếm bánh', [r0.mon.map(m => m.ma), r0.tong, r0.soBanh], [[], 0, 0]);
  const r1 = dungQuayHien(quay({nhom_menu: [{ma: 'n-ca-phe', ten: 'Cà phê', loai: 'nuoc'}]}), null, t);
  la('tắt nhóm Bánh: chỉ cà phê, không có tầng Bánh', [r1.mon.map(m => m.ma), r1.tong, r1.tang.map(n => n.n)], [['N1'], 0, ['', 'nuoc']]);
  const r2 = dungQuayHien(quay({}), null, t);
  la('máy chủ cũ: bày như trước', [r2.mon.map(m => m.ma), r2.tong], [['B1', 'N1'], 5]);
});

await ca('v642 gọi xong (anh Việt 06/11/2026: màn co lại, không xem được đơn, không có chỗ tính tiền): thanh đơn luôn hiện ở đáy; màn Đơn của bàn có từng lượt, giờ, trạng thái, tiền từng dòng, tạm tính bỏ lượt bị từ chối; Thanh toán chọn mang bill ra bàn hay trả tại quầy, ô mã số thuế hoặc email, báo quầy bằng chuông Xin tính tiền', async () => {
  const theoMa = {
    'TQ-1': {ok: 1, trang_thai: 'Chờ nhận', luc: '10:00', tam_tinh: 45000, mon: [{ten: 'Trà Hoa Lài', sl: 1, tc: ['Ít đá'], gia: 45000, tien: 45000}]},
    'TQ-2': {ok: 1, trang_thai: 'Từ chối', luc: '10:05', ly_do: 'Hết kem', tam_tinh: 30000, mon: [{ten: 'Kem Vani', sl: 1, tc: [], gia: 30000, tien: 30000}]}};
  let so = 0;
  const {goc, kho, vet, chayHen, mang} = await moTrang({tt: th => theoMa[th.ma], goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so).repeat(32)})});
  let traLoi = {ok: 1, ma: 'TG-1', luc: '10:58'};
  mang['vagabond.goi_mon_ban.goi_nhan_vien'] = () => traLoi;
  const G = kho.goiBan.G;
  const on = id => String(theoId(goc, id).props.class).split(/\s+/).includes('on');
  const mo = id => String(theoId(goc, id).props.class).includes('open');
  dung('chưa gọi: không có thanh đơn', !on('gbBarDon'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  await bam(tim(goc, n => n.props['data-tc'] === 'Đá=Ít đá')[0]);
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  la('giỏ trống sau khi gọi', G.gio.length, 0);
  dung('thanh đơn hiện ngay, không co lại', on('gbBarDon'));
  const bar = chu(theoId(goc, 'gbBarDon'));
  dung('thanh đơn: bàn và số lượt ' + bar, bar.includes('Bàn 5 · Đã gọi 1 lượt'));
  dung('thanh đơn: tạm tính và lượt chờ ' + bar, bar.includes('Tạm tính 45.000 đ') && bar.includes('1 lượt chờ quầy nhận'));
  await bam(theoId(goc, 'gbXemDon'));
  dung('mở màn Đơn của bàn', mo('gbDonBan'));
  dung('màn đơn mở thì thanh đơn nhường chỗ', !on('gbBarDon'));
  const d1 = chu(theoId(goc, 'gbDonBan'));
  dung('lượt có giờ và trạng thái ' + d1, d1.includes('Lượt 1 · 10:00') && d1.includes('Chờ quầy nhận'));
  dung('dòng có tuỳ chọn và tiền ' + d1, d1.includes('1 × Trà Hoa Lài') && d1.includes('Ít đá') && d1.includes('45.000 đ'));
  dung('tạm tính và cần thanh toán ' + d1, d1.includes('Món gọi từ máy này (1 món)') && d1.includes('Cần thanh toán'));
  dung('nút Thanh toán có số tiền', chu(theoId(goc, 'gbDonTra')) === 'Thanh toán · 45.000 đ');
  dung('có Gọi thêm món, Gọi nhân viên', theoId(goc, 'gbDonGoiThem') && theoId(goc, 'gbDonChuong'));
  await bam(theoId(goc, 'gbDonGoiThem'));
  dung('Gọi thêm món: đóng màn đơn, về danh sách', !mo('gbDonBan') && on('gbBarDon'));
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {trang_thai: 'Đã nhận', nhan_luc: '10:02'});
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
  dung('giỏ có món: thanh giỏ đứng chỗ thanh đơn', on('gbBar') && !on('gbBarDon'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  await bam(theoId(goc, 'gbXemDon'));
  await cho();
  la('lượt mới nhất trên cùng', tim(theoId(goc, 'gbDonBan'), n => n.props && n.props['data-luot']).map(n => n.props['data-luot']), ['TQ-2', 'TQ-1']);
  const l2 = tim(theoId(goc, 'gbDonBan'), n => n.props && n.props['data-luot'] === 'TQ-2')[0];
  dung('lượt bị từ chối hiện mờ, ghi lý do', String(l2.props.class).includes('tat') && chu(l2).includes('Quầy từ chối: Hết kem'));
  const d2 = chu(theoId(goc, 'gbDonBan'));
  dung('lượt đã nhận ghi giờ nhận ' + d2, d2.includes('Đã nhận lúc 10:02'));
  dung('tạm tính bỏ lượt bị từ chối', chu(theoId(goc, 'gbTongBan')).includes('Món gọi từ máy này (1 món)') && chu(theoId(goc, 'gbDonTra')) === 'Thanh toán · 45.000 đ');
  await bam(theoId(goc, 'gbDonTra'));
  dung('mở Thanh toán, đóng màn đơn', mo('gbTra') && !mo('gbDonBan'));
  la('hai cách trả, chưa mở trả online', tim(theoId(goc, 'gbTra'), n => n.props['data-cach']).map(n => n.props['data-cach']), ['ban', 'quay']);
  dung('chưa chọn cách thì khoá nút', theoId(goc, 'gbTraGui').props.disabled === true);
  await bam(tim(goc, n => n.props['data-cach'] === 'ban')[0]);
  go(theoId(goc, 'gb-tra-hd'), '12345'); await cho();
  await bam(theoId(goc, 'gbTraGui'));
  dung('mã số thuế sai dạng: nói rõ, không gửi', chu(theoId(goc, 'gbTraLoi')).includes('10 số') && !vet.some(x => x[1] === 'vagabond.goi_mon_ban.goi_nhan_vien'));
  go(theoId(goc, 'gb-tra-hd'), '0311 638 525'); await cho();
  traLoi = {ok: 0, cau: 'Bàn này vừa gọi 3 lần. Nhân viên đang tới, quý khách đợi một chút hoặc nhắn Zalo.'};
  await bam(theoId(goc, 'gbTraGui'));
  dung('máy chủ chặn: nói câu máy chủ, giữ bảng', chu(theoId(goc, 'gbTraLoi')).includes('vừa gọi 3 lần') && mo('gbTra'));
  traLoi = {ok: 1, ma: 'TG-1', luc: '10:58'};
  await bam(theoId(goc, 'gbTraGui'));
  const gui = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi_nhan_vien').map(x => x[2]);
  la('gửi đúng chuông Xin tính tiền kèm cách trả và mã số thuế', gui.map(x => [x.diem, x.ban, x.k, x.ly_do, x.chi_tiet]),
    [['TCV', 5, K, 'Xin tính tiền', 'Mang bill ra bàn · Xuất hoá đơn: 0311638525'], ['TCV', 5, K, 'Xin tính tiền', 'Mang bill ra bàn · Xuất hoá đơn: 0311638525']]);
  la('thử lại cùng nội dung: giữ nonce để máy chủ gộp', gui[0].nonce === gui[1].nonce && /^[A-Za-z0-9_-]{32}$/.test(gui[0].nonce), true);
  dung('báo đã gửi, nói gọi thêm thành bill mới', chu(theoId(goc, 'gbTraXong')).includes('Nhân viên mang bill ra bàn 5') && chu(theoId(goc, 'gbTraXong')).includes('bill mới'));
});

await ca('v642 combo quán đang chạy (anh Việt 06/11/2026): chip Combo đứng sau Tất cả, combo đầu danh sách có giá bộ, giá gốc gạch, món thành phần; bấm + vào giỏ thẳng, giỏ ghi món thành phần; Gọi món gửi mã combo không kèm giá; không có QR thì không bày combo', async () => {
  const CB = {ma: 'KMCB00001', ten: 'Trà chiều', gia: 120000, goc: 140000, mo_ta: '', anh: '', con: 2, loai: 'combo',
    thanh_phan: [{ma: 'NUTR00021', ten: 'Trà Hoa Lài', sl: 1, loai: 'nuoc'}, {ma: 'BAWC00115', ten: 'Mousse Chanh Dây', sl: 2, loai: 'banh'}]};
  const goc = JSON.parse(JSON.stringify(STORE));
  goc.quay[0].combo = [CB, Object.assign({}, CB, {ma: 'KMCB00009', con: 0})];
  const m = moiTruong();
  m.mang['vagabond.kiem_kho.con_tren_quay_web'] = () => JSON.parse(JSON.stringify(goc));
  const kho = taoKho(m.mt);
  await kho.napQuay();
  await kho.goiBan.kiemLink();
  const q = dungQuayHien(kho.S, kho.goiBan.G, t);
  la('tầng Combo sau Tất cả, chỉ combo còn bộ', q.tang.slice(0, 2).map(n => [n.n, n.so]), [['', q.mon.length], ['combo', 1]]);
  la('combo đứng đầu', [q.mon[0].ma, q.mon[0].gia, q.mon[0].gocHien, q.mon[0].mo_ta], ['KMCB00001', 120000, 140000, 'Trà Hoa Lài, 2 Mousse Chanh Dây']);
  kho.S.tangQuay = 'combo';
  la('tầng Combo chỉ còn combo', dungQuayHien(kho.S, kho.goiBan.G, t).mon.map(x => x.ma), ['KMCB00001']);
  kho.S.tangQuay = '';
  la('không có QR: không bày combo', dungQuayHien(kho.S, null, t).mon.some(x => x.loai === 'combo'), false);
  la('bấm + combo: thêm thẳng', kho.goiBan.bamThem(q.mon[0]), true);
  la('giỏ: giá bộ, ghi món thành phần', [kho.goiBan.G.gio[0].ma, kho.goiBan.G.gio[0].gia, kho.goiBan.G.gio[0].thanhPhan.length], ['KMCB00001', 120000, 2]);
  kho.goiBan.bamThem(q.mon[0]);
  la('tối đa 2 bộ theo bánh còn', kho.goiBan.bamThem(q.mon[0]), false);
  await kho.goiBan.goiMon();
  const gui = m.vet.filter(x => x[1] === 'vagabond.goi_mon_ban.goi');
  la('gửi mã combo, không giá', JSON.parse(gui[0][2].mon), [{ma: 'KMCB00001', sl: 2, tc: {}}]);
  la('đơn của bàn chép món thành phần', kho.goiBan.G.don[0].tt.mon[0].tc, ['Trà Hoa Lài, 2 Mousse Chanh Dây']);
});

await ca('v642 Codex #545 vòng 1: khách trả bill xong rồi gọi tiếp mà không tải lại trang: lượt đã tính tiền không cộng vào bill mới, thanh đơn và Đơn của bàn chỉ còn lượt của bill đang mở', async () => {
  const theoMa = {
    'TQ-1': {ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:02', luc: '10:00', tam_tinh: 90000, mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: [], gia: 45000, tien: 90000}]},
    'TQ-2': {ok: 1, trang_thai: 'Chờ nhận', luc: '11:00', tam_tinh: 30000, mon: [{ten: 'Kem Vani', sl: 1, tc: [], gia: 30000, tien: 30000}]}};
  let so = 0;
  const {goc, kho, chayHen} = await moTrang({tt: th => theoMa[th.ma], goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so).repeat(32)})});
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  dung('bill đầu: tạm tính 90.000 đ', chu(theoId(goc, 'gbBarDon')).includes('Tạm tính 90.000 đ'));
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {da_tra: 1});
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  const bar = chu(theoId(goc, 'gbBarDon'));
  dung('bill mới chỉ tính lượt mới: ' + bar, bar.includes('Tạm tính 30.000 đ') && bar.includes('Đã gọi 1 lượt'));
  la('lượt đã tính tiền rời khỏi đơn của bàn', G.don.map(d => d.ma), ['TQ-2']);
});

await ca('v642 Codex #545 vòng 4: bàn gọi hơn mười lượt chưa trả, tải lại trang vẫn đủ mọi lượt, tổng cần thanh toán không hụt', async () => {
  const kho = new Map();
  const luuTru = {getItem: k => (kho.has(k) ? kho.get(k) : null), setItem: (k, v) => { kho.set(k, String(v)); }, removeItem: k => kho.delete(k)};
  let so = 0;
  const tt = () => ({ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:02', luc: '10:00', tam_tinh: 30000, mon: [{ten: 'Kem Vani', sl: 1, tc: [], gia: 30000, tien: 30000}]});
  const m1 = moiTruong({tt, goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so % 10).repeat(32)})});
  m1.mt.luuTru = luuTru;
  const k1 = taoKho(m1.mt);
  await k1.napQuay();
  await k1.goiBan.kiemLink();
  const kem = dungQuayHien(k1.S, k1.goiBan.G, t).mon.find(x => x.ma === 'NUIC00002');
  for (let i = 0; i < 12; i++) { k1.goiBan.bamThem(kem); await k1.goiBan.goiMon(); }
  await m1.chayHen();
  la('trước khi tải lại: 12 lượt, 360.000 đ', [k1.goiBan.G.don.length, k1.goiBan.tom.value.tamTinh], [12, 360000]);
  const m2 = moiTruong({tt});
  m2.mt.luuTru = luuTru;
  const k2 = taoKho(m2.mt);
  await k2.napQuay();
  await k2.goiBan.kiemLink();
  await m2.chayHen();
  la('sau khi tải lại: vẫn 12 lượt, 360.000 đ', [k2.goiBan.G.don.length, k2.goiBan.tom.value.tamTinh], [12, 360000]);
  const K3 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  const nhieu = Array.from({length: 205}, (_, i) => ({ma: 'TQ-' + i, tt: {trang_thai: i < 10 ? 'Từ chối' : 'Đã nhận'}}));
  const giu = K3.donCanLuu(nhieu);
  la('quá trần: chỉ bỏ lượt từ chối cũ, giữ mọi lượt còn tính tiền', [giu.length, giu.filter(d => d.tt.trang_thai === 'Đã nhận').length], [200, 195]);
  const song = Array.from({length: 210}, (_, i) => ({ma: 'TQ-' + i, tt: {trang_thai: 'Đã nhận'}}));
  la('toàn lượt còn tính tiền: không cắt lượt nào', K3.donCanLuu(song).length, 210);
});

await ca('v642 phép thuần thanh toán tại bàn: ô hoá đơn nhận mã số thuế 10, 12, 10-3 số hoặc email; chi tiết gửi quầy không quá 120 ký tự; tạm tính bỏ lượt từ chối, hết hạn', async () => {
  const K2 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  la('rỗng là hợp lệ', K2.chuanHoaDon('  '), {ok: true, gt: ''});
  la('10 số có dấu cách', K2.chuanHoaDon('0311 638 525').gt, '0311638525');
  la('12 số', K2.chuanHoaDon('079123456789').gt, '079123456789');
  la('chi nhánh', [K2.chuanHoaDon('0311638525-027').gt, K2.chuanHoaDon('0311638525027').gt], ['0311638525-027', '0311638525-027']);
  la('email chữ thường', K2.chuanHoaDon(' KeToan@CongTy.vn ').gt, 'ketoan@congty.vn');
  la('sai dạng', [K2.chuanHoaDon('12345').ok, K2.chuanHoaDon('a@b').ok], [false, false]);
  la('trả tại quầy', K2.chiTietTra('quay', ''), 'Khách ra quầy trả');
  la('cách lạ: rỗng', K2.chiTietTra('online', ''), '');
  dung('không quá 120 ký tự', K2.chiTietTra('ban', 'x'.repeat(200) + '@a.vn').length === 120);
  la('tạm tính', K2.tomDon([{tt: {trang_thai: 'Đã nhận', tam_tinh: 100, mon: [{sl: 2}]}}, {tt: {trang_thai: 'Hết hạn', tam_tinh: 50, mon: [{sl: 1}]}},
    {tt: {trang_thai: 'Từ chối', tam_tinh: 70}}, {tt: null}]), {soLuot: 2, soMon: 2, tamTinh: 100, choNhan: 1, coHoaDon: false, hoaDon: 0, ngoaiHoaDon: 100, coNgoai: false, canTra: 100,
    giamUd: 0, uuDai: null}); /* v643: thêm hai khoá ưu đãi, không đổi số cũ. */
});

await ca('v642 Codex #545 vòng 6: hai điện thoại cùng bàn, quầy thêm món: cần thanh toán lấy theo hoá đơn của bàn trên máy chủ, không chỉ món gọi từ máy này; lượt chờ quầy nhận cộng thêm, ghi rõ chưa vào hoá đơn', async () => {
  /* Đúng chuỗi của khách: máy A gọi 1 lượt 100.000 đ, quầy nhận vào phiếu tạm
     của bàn; máy B (hay thu ngân) thêm 40.000 đ vào CÙNG phiếu. Máy chủ trả
     hoá đơn của bàn kèm lượt của máy A. */
  const theoMa = {'TQ-1': {ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:02', luc: '10:00', tam_tinh: 100000,
    mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: [], gia: 50000, tien: 100000}], bill: {khoa: 'b1', tong: 140000}}};
  let so = 0;
  const {goc, kho, chayHen} = await moTrang({tt: th => theoMa[th.ma] || {ok: 1, trang_thai: 'Chờ nhận', luc: '10:20', tam_tinh: 30000,
    mon: [{ten: 'Kem Vani', sl: 1, tc: [], gia: 30000, tien: 30000}]}, goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so).repeat(32)})});
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  await bam(theoId(goc, 'gbXemDon'));
  await cho();
  const tb = chu(theoId(goc, 'gbTongBan'));
  dung('màn Đơn của bàn: cần thanh toán theo hoá đơn của bàn ' + tb, tb.includes('Cần thanh toán140.000 đ'));
  dung('ghi rõ món gọi từ máy này và hoá đơn của bàn ' + tb, tb.includes('Món gọi từ máy này (2 món)100.000 đ') && tb.includes('Hoá đơn của bàn140.000 đ'));
  la('nút Thanh toán theo hoá đơn của bàn', chu(theoId(goc, 'gbDonTra')), 'Thanh toán · 140.000 đ');
  await bam(theoId(goc, 'gbDonTra'));
  dung('màn Thanh toán: 140.000 đ', chu(theoId(goc, 'gbTra')).includes('Cần thanh toán140.000 đ'));
  await bam(tim(theoId(goc, 'gbTra'), n => n.the === 'button' && String(n.props.class).includes('gb-x'))[0]);
  dung('thanh đơn: 140.000 đ ' + chu(theoId(goc, 'gbBarDon')), chu(theoId(goc, 'gbBarDon')).includes('Tạm tính 140.000 đ'));
  /* Máy A gọi thêm một lượt, quầy chưa nhận: chưa vào hoá đơn, cộng thêm. */
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  await bam(theoId(goc, 'gbXemDon'));
  await cho();
  const tb2 = chu(theoId(goc, 'gbTongBan'));
  dung('lượt chờ nhận cộng thêm, ghi chưa vào hoá đơn ' + tb2, tb2.includes('Chưa vào hoá đơn30.000 đ') && tb2.includes('Cần thanh toán170.000 đ'));
  /* Thu ngân thêm món nữa vào phiếu: mở lại màn đơn là thấy số mới. */
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {bill: {khoa: 'b1', tong: 185000}});
  await bam(theoId(goc, 'gbDonGoiThem'));
  await bam(theoId(goc, 'gbXemDon'));
  await cho();
  dung('mở lại màn đơn: hỏi lại hoá đơn của bàn ' + chu(theoId(goc, 'gbTongBan')), chu(theoId(goc, 'gbTongBan')).includes('Cần thanh toán215.000 đ'));
  la('kho', kho.goiBan.tom.value.canTra, 215000);
});

await ca('v642 Codex #545 vòng 6 phép thuần: cần thanh toán = các hoá đơn mở của bàn (mỗi hoá đơn một lần) + lượt chưa vào hoá đơn; lượt đã nhận mà máy chủ không báo hoá đơn thì tính theo lượt; từ chối, hết hạn không tính', async () => {
  const K2 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  const r = K2.tomDon([
    {tt: {trang_thai: 'Đã nhận', tam_tinh: 100, mon: [{sl: 2}], bill: {khoa: 'b1', tong: 140}}},
    {tt: {trang_thai: 'Đã nhận', tam_tinh: 20, mon: [{sl: 1}], bill: {khoa: 'b1', tong: 150}}},
    {tt: {trang_thai: 'Chờ nhận', tam_tinh: 30, mon: [{sl: 1}], bill: {khoa: 'b9', tong: 999}}},
    {tt: {trang_thai: 'Từ chối', tam_tinh: 70, mon: [{sl: 1}]}}]);
  la('một hoá đơn tính một lần, số mới nhất; lượt chờ nhận cộng thêm', [r.tamTinh, r.hoaDon, r.coHoaDon, r.ngoaiHoaDon, r.canTra], [150, 150, true, 30, 180]);
  const r2 = K2.tomDon([{tt: {trang_thai: 'Đã nhận', tam_tinh: 100, mon: [{sl: 2}]}}, {tt: {trang_thai: 'Chờ nhận', tam_tinh: 30, mon: [{sl: 1}]}}]);
  la('máy chủ chưa báo hoá đơn: tính theo lượt', [r2.coHoaDon, r2.canTra], [false, 130]);
  const r3 = K2.tomDon([{tt: {trang_thai: 'Đã nhận', tam_tinh: 50, bill: {khoa: 'b1', tong: 80}}}, {tt: {trang_thai: 'Đã nhận', tam_tinh: 60, bill: {khoa: 'b2', tong: 90}}}]);
  la('hai hoá đơn mở khác nhau: cộng cả hai', r3.canTra, 170);
});

await ca('v642 Codex #545 vòng 7: quầy nhận lượt MỚI trước rồi lượt CŨ sau; nhịp tự động chỉ hỏi lượt còn chờ; thanh đơn phải theo số phiếu hỏi sau cùng (140.000 đ), không theo lượt đứng cuối danh sách (40.000 đ)', async () => {
  const BILL = 'k-bill-ban-5';
  const theoMa = {
    'TQ-1': {ok: 1, trang_thai: 'Chờ nhận', luc: '10:00', tam_tinh: 100000, mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: [], gia: 50000, tien: 100000}]},
    'TQ-2': {ok: 1, trang_thai: 'Chờ nhận', luc: '10:05', tam_tinh: 40000, mon: [{ten: 'Kem Vani', sl: 1, tc: [], gia: 40000, tien: 40000}]}};
  let so = 0;
  const {goc, kho, chayHen, vet} = await moTrang({tt: th => Object.assign({}, theoMa[th.ma]), goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so).repeat(32)})});
  for (const ma of ['NUTR00021', 'NUIC00002']) {
    await bam(nutThem(goc).find(n => n.props['data-them'] === ma));
    if (ma === 'NUTR00021') await bam(theoId(goc, 'gbThemLy'));
    await bam(theoId(goc, 'gbXemGio'));
    await bam(theoId(goc, 'gbGoi'));
  }
  await chayHen();
  /* Quầy nhận lượt 2 (40.000 đ) trước: phiếu của bàn 40.000 đ. */
  theoMa['TQ-2'] = Object.assign({}, theoMa['TQ-2'], {trang_thai: 'Đã nhận', nhan_luc: '10:06', bill: {khoa: BILL, tong: 40000}});
  await chayHen();
  dung('nhận lượt 2: thanh đơn 40.000 đ + lượt 1 chờ 100.000 đ ' + chu(theoId(goc, 'gbBarDon')), chu(theoId(goc, 'gbBarDon')).includes('Tạm tính 140.000 đ'));
  /* Rồi nhận lượt 1 vào CÙNG phiếu: phiếu 140.000 đ. Nhịp tự động không hỏi lại lượt 2 (đã xong). */
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {trang_thai: 'Đã nhận', nhan_luc: '10:07', bill: {khoa: BILL, tong: 140000}});
  theoMa['TQ-2'] = Object.assign({}, theoMa['TQ-2'], {bill: {khoa: BILL, tong: 140000}});
  const truoc = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.trang_thai').length;
  await chayHen();
  /* v643: nhịp tự động hỏi lượt còn chờ (lượt 1) và lượt đại diện của hoá đơn còn mở (lượt 2), không hỏi lại mọi lượt. */
  /* Bộ hẹn giờ giả không huỷ hẹn cũ nên có thể chạy lặp: so theo tập lượt được hỏi. */
  la('nhịp tự động hỏi lượt chờ và lượt đại diện hoá đơn', [...new Set(vet.filter(x => x[1] === 'vagabond.goi_mon_ban.trang_thai').slice(truoc).map(x => x[2].ma))].sort(), ['TQ-1', 'TQ-2']);
  const bar = chu(theoId(goc, 'gbBarDon'));
  dung('thanh đơn theo số phiếu mới nhất: ' + bar, bar.includes('Tạm tính 140.000 đ'));
  la('kho', [kho.goiBan.tom.value.canTra, kho.goiBan.tom.value.hoaDon], [140000, 140000]);
});

await ca('v642 Codex #545 vòng 7: máy chủ đọc tổng phiếu lỗi ở một lượt vẫn báo khoá phiếu; lượt khác cùng phiếu đọc được tổng thì không cộng trùng (140.000 đ, không phải 240.000 đ); cả phiếu chưa đọc được thì tạm tính theo lượt', async () => {
  const K2 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  const l1 = (bill, hoi) => ({tt: {trang_thai: 'Đã nhận', tam_tinh: 100000, mon: [{sl: 2}], bill, hoi}});
  const l2 = (bill, hoi) => ({tt: {trang_thai: 'Đã nhận', tam_tinh: 40000, mon: [{sl: 1}], bill, hoi}});
  la('lượt 1 đọc lỗi, lượt 2 đọc được', K2.tomDon([l1({khoa: 'b1', tong: null}, 1), l2({khoa: 'b1', tong: 140000}, 2)]).canTra, 140000);
  la('lượt đọc lỗi hỏi sau cùng: giữ số đọc được', K2.tomDon([l2({khoa: 'b1', tong: 140000}, 1), l1({khoa: 'b1', tong: null}, 2)]).canTra, 140000);
  const r = K2.tomDon([l1({khoa: 'b1', tong: null}, 1), l2({khoa: 'b1', tong: null}, 2), {tt: {trang_thai: 'Chờ nhận', tam_tinh: 30000}}]);
  la('cả phiếu chưa đọc được: theo lượt, không ghi là hoá đơn của bàn', [r.coHoaDon, r.hoaDon, r.canTra], [false, 0, 170000]);
  la('số hỏi sau cùng thắng dù lượt đứng trước', K2.tomDon([l1({khoa: 'b1', tong: 140000}, 5), l2({khoa: 'b1', tong: 40000}, 3)]).canTra, 140000);
  la('tổng 0 đ (quầy giảm hết) vẫn là số đọc được', K2.tomDon([l1({khoa: 'b1', tong: 0}, 1)]).canTra, 0);
});

await ca('v643 (còn tồn v642): không còn lượt chờ, bàn còn hoá đơn mở: thanh đơn vẫn tự hỏi lại tổng hoá đơn theo nhịp thưa, máy khác gọi thêm hay quầy thêm món là thanh đơn đổi số; hoá đơn đã chốt thì thôi hỏi', async () => {
  const K3 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  const theoMa = {'TQ-1': {ok: 1, trang_thai: 'Chờ nhận', luc: '10:00', tam_tinh: 100000, mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: [], gia: 50000, tien: 100000}]}};
  let so = 0;
  const {goc, chayHen, vet, kho} = await moTrang({tt: th => Object.assign({}, theoMa[th.ma]), goi: () => ({ok: 1, ma: 'TQ-' + (++so), token: String(so).repeat(32)})});
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUTR00021'));
  await bam(theoId(goc, 'gbThemLy'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {trang_thai: 'Đã nhận', nhan_luc: '10:02', bill: {khoa: 'b1', tong: 100000}});
  await chayHen();
  dung('quầy nhận: 100.000 đ', chu(theoId(goc, 'gbBarDon')).includes('Tạm tính 100.000 đ'));
  /* Máy khác gọi thêm 40.000 đ vào cùng hoá đơn; máy này không còn lượt chờ. */
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {bill: {khoa: 'b1', tong: 140000}});
  await chayHen();
  const bar = chu(theoId(goc, 'gbBarDon'));
  dung('thanh đơn tự đổi sang 140.000 đ: ' + bar, bar.includes('Tạm tính 140.000 đ'));
  /* Thu ngân chốt bill: lượt rời đơn, thôi hỏi. */
  theoMa['TQ-1'] = Object.assign({}, theoMa['TQ-1'], {da_tra: 1, bill: undefined});
  await chayHen();
  const truoc = vet.filter(x => x[1] === 'vagabond.goi_mon_ban.trang_thai').length;
  await chayHen();
  la('bill đã chốt: không hỏi nữa', vet.filter(x => x[1] === 'vagabond.goi_mon_ban.trang_thai').length - truoc, 0);
  la('nhịp hoá đơn thưa hơn nhịp lượt chờ', K3.NHIP_HOA_DON > K3.NHIP_TRANG_THAI, true);
  la('kho không còn lượt', kho.goiBan.G.don.length, 0);
});

await ca('v643 ưu đãi tại bàn (mẫu anh Việt duyệt 07/11/2026, "Máy tự trừ ngay"): Đơn của bàn có ô Ưu đãi; chưa đăng nhập thì gửi mã Zalo, nhập sai báo lỗi, đúng thì ra Ví quà và chương trình; chọn là máy chủ trừ ngay, Cần thanh toán và thanh đơn đổi theo hoá đơn; bỏ thì về số cũ; máy chủ từ chối thì nói lý do, màn ở lại', async () => {
  let bill = {khoa: 'b1', tong: 185000};
  const tt = () => ({ok: 1, trang_thai: 'Đã nhận', nhan_luc: '10:02', luc: '10:00', tam_tinh: 185000, bill,
    mon: [{ten: 'Trà Hoa Lài', sl: 2, tc: [], gia: 45000, tien: 90000}, {ten: 'Mousse Chanh Dây', sl: 1, tc: [], gia: 95000, tien: 95000}]});
  const {goc, vet, mang, chayHen} = await moTrang({tt});
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  await bam(theoId(goc, 'gbXemGio'));
  await bam(theoId(goc, 'gbGoi'));
  await chayHen();
  let dangNhap = 0, chonCo = null;
  const DS = [{loai: 'ma', ma: 'VC-8K2Q', nhom: 'vi', ten: 'Giảm 10% hoá đơn', phu: 'Mã VC-8K2Q · hạn 30/11', giam: 18500, ly_do: '', dung_duoc: 1},
    {loai: 'ctkm', ma: 'CTKM-HH', nhom: 'ctkm', ten: 'Happy hour trà', phu: 'Giảm 20% đồ uống', giam: 0, ly_do: 'ngoài khung giờ 15:00 - 17:00', dung_duoc: 0}];
  mang['vagabond.uu_dai_ban.ds'] = () => (dangNhap ? {ok: 1, dang_nhap: 1, sdt: '0909 *** 412', co_hoa_don: 1, chon: chonCo, ds: DS} : {ok: 1, dang_nhap: 0});
  mang['vagabond.thanh_vien.gui_ma'] = () => ({ok: 1, song_giay: 300});
  mang['vagabond.thanh_vien.xac_thuc'] = th => (th.ma === '482913' ? (dangNhap = 1, {ok: 1}) : {ok: 0, ly_do: 'ma_khong_dung'});
  await bam(theoId(goc, 'gbBarDonChu'));
  const o = chu(theoId(goc, 'gbUdO'));
  dung('ô Ưu đãi mời đăng nhập: ' + o, o.includes('Ưu đãi thành viên') && o.includes('Đăng nhập bằng Zalo') && o.includes('Chọn'));
  await bam(theoId(goc, 'gbUdO'));
  dung('màn ưu đãi mở, Đơn của bàn đóng', String(theoId(goc, 'gbUd').props.class).includes('open') && !String(theoId(goc, 'gbDonBan').props.class).includes('open'));
  dung('bước số điện thoại', theoId(goc, 'gb-ud-sdt') && theoId(goc, 'gbUdGuiMa') && !theoId(goc, 'gb-ud-ma'));
  go(theoId(goc, 'gb-ud-sdt'), '0909 123 412');
  await cho();
  await bam(theoId(goc, 'gbUdGuiMa'));
  la('gửi mã qua cửa Thành viên, số chỉ còn chữ số', vet.filter(x => x[1] === 'vagabond.thanh_vien.gui_ma').map(x => [x[0], x[2]]), [['POST', {sdt: '0909123412'}]]);
  dung('bước nhập mã, có Sửa số', theoId(goc, 'gb-ud-ma') && theoId(goc, 'gbUdXacMinh') && theoId(goc, 'gbUdSuaSo'));
  dung('báo đã gửi', chu(theoId(goc, 'gbUdBao')).includes('Đã gửi mã qua Zalo'));
  go(theoId(goc, 'gb-ud-ma'), '482910');
  await cho();
  await bam(theoId(goc, 'gbUdXacMinh'));
  dung('mã sai: ' + chu(theoId(goc, 'gbUdLoi')), chu(theoId(goc, 'gbUdLoi')).includes('Mã chưa đúng'));
  go(theoId(goc, 'gb-ud-ma'), '482913');
  await cho();
  await bam(theoId(goc, 'gbUdXacMinh'));
  la('xác minh đúng số đúng mã', vet.filter(x => x[1] === 'vagabond.thanh_vien.xac_thuc').map(x => x[2]).pop(), {sdt: '0909123412', ma: '482913'});
  const k = tim(theoId(goc, 'gbUd'), n => n.props['data-ud']);
  la('ví trước, chương trình sau', k.map(n => n.props['data-ud']), ['ma:VC-8K2Q', 'ctkm:CTKM-HH']);
  la('chọn sẵn mã giảm nhiều nhất dùng được', k.map(n => n.props['aria-pressed']), ['true', 'false']);
  dung('chương trình ngoài giờ mờ, không bấm được, có lý do', k[1].props.disabled && chu(k[1]).includes('ngoài khung giờ 15:00 - 17:00'));
  dung('thẻ số giảm', chu(k[0]).includes('Giảm 18.500 đ'));
  dung('đầu màn có số che', chu(theoId(goc, 'gbUd')).includes('Số 0909 *** 412'));
  /* Máy chủ từ chối (số khác cùng bàn đã chọn): báo đúng câu, màn ở lại. */
  mang['vagabond.uu_dai_ban.chon'] = () => ({ok: 0, cau: 'Bàn đã dùng ưu đãi của số 0912 *** 111. Mỗi hoá đơn một ưu đãi.'});
  await bam(theoId(goc, 'gbUdDung'));
  dung('từ chối có lý do', chu(theoId(goc, 'gbUdLoi')).includes('0912 *** 111') && String(theoId(goc, 'gbUd').props.class).includes('open'));
  mang['vagabond.uu_dai_ban.chon'] = th => { bill = {khoa: 'b1', tong: 166500, ud: {ten: 'Giảm 10% hoá đơn', giam: 18500, ly_do: '', sdt: '0909 *** 412'}};
    chonCo = {ten: 'Giảm 10% hoá đơn', giam: 18500}; return {ok: 1, chon: chonCo, tong: 166500}; };
  await bam(theoId(goc, 'gbUdDung'));
  la('gửi đúng bàn, đúng ưu đãi', vet.filter(x => x[1] === 'vagabond.uu_dai_ban.chon').map(x => [x[0], x[2]]).pop(),
    ['POST', {diem: 'TCV', ban: 5, k: K, loai: 'ma', ma: 'VC-8K2Q'}]);
  dung('về lại Đơn của bàn', String(theoId(goc, 'gbDonBan').props.class).includes('open') && !String(theoId(goc, 'gbUd').props.class).includes('open'));
  dung('hoá đơn của bàn trước ưu đãi', chu(theoId(goc, 'gbHoaDonBan')).includes('185.000 đ'));
  dung('dòng ưu đãi đã trừ', chu(theoId(goc, 'gbUdTru')).includes('- 18.500 đ'));
  const tong = chu(theoId(goc, 'gbTongBan'));
  dung('Cần thanh toán 166.500 đ: ' + tong, tong.includes('Cần thanh toán166.500 đ'));
  dung('nút Thanh toán theo số mới', chu(theoId(goc, 'gbDonTra')).includes('166.500 đ'));
  const o2 = chu(theoId(goc, 'gbUdO'));
  dung('ô Ưu đãi đã chọn: ' + o2, o2.includes('Giảm 10% hoá đơn') && o2.includes('Đã trừ 18.500 đ') && o2.includes('Đổi'));
  await bam(theoId(goc, 'gbUd').con[0] && tim(theoId(goc, 'gbUd'), n => n.props.class === 'gb-x')[0]);
  await bam(tim(theoId(goc, 'gbDonBan'), n => n.props.class === 'gb-x')[0]);
  dung('thanh đơn theo số mới', chu(theoId(goc, 'gbBarDon')).includes('Tạm tính 166.500 đ'));
  /* Quầy bớt món dưới mức: máy chủ giữ lựa chọn, giảm 0 kèm lý do. */
  bill = {khoa: 'b1', tong: 90000, ud: {ten: 'Giảm 10% hoá đơn', giam: 0, ly_do: 'hoá đơn chưa đủ 150.000 đ', sdt: '0909 *** 412'}};
  await bam(theoId(goc, 'gbBarDonChu'));
  dung('chưa trừ kèm lý do', chu(theoId(goc, 'gbUdO')).includes('Chưa trừ: hoá đơn chưa đủ 150.000 đ') && !theoId(goc, 'gbUdTru'));
  /* Bỏ ưu đãi. */
  bill = {khoa: 'b1', tong: 166500, ud: {ten: 'Giảm 10% hoá đơn', giam: 18500, ly_do: '', sdt: '0909 *** 412'}};
  await chayHen();
  mang['vagabond.uu_dai_ban.bo'] = () => { bill = {khoa: 'b1', tong: 185000}; chonCo = null; return {ok: 1, tong: 185000}; };
  await bam(theoId(goc, 'gbUdO'));
  await bam(theoId(goc, 'gbUdBo'));
  la('bỏ qua đúng cửa', vet.filter(x => x[1] === 'vagabond.uu_dai_ban.bo').map(x => [x[0], x[2]]).pop(), ['POST', {diem: 'TCV', ban: 5, k: K}]);
  dung('về 185.000 đ, không còn dòng ưu đãi', chu(theoId(goc, 'gbTongBan')).includes('Cần thanh toán185.000 đ') && !theoId(goc, 'gbUdTru'));
  dung('ô Ưu đãi mời chọn lại', chu(theoId(goc, 'gbUdO')).includes('Chọn'));
});

await ca('v643 ưu đãi tại bàn phép thuần: Cần thanh toán = hoá đơn sau ưu đãi + lượt chưa vào hoá đơn; chọn sẵn; số điện thoại; câu lỗi đăng nhập', async () => {
  const K4 = await import('../../../public/web_vue/banh/kho-goi-ban.js');
  const d = (ma, tt, tam, bill, hoi) => ({ma, tt: {trang_thai: tt, tam_tinh: tam, bill, hoi, mon: []}});
  const r = K4.tomDon([d('A', 'Đã nhận', 185000, {khoa: 'b1', tong: 166500, ud: {ten: 'X', giam: 18500}}, 2), d('B', 'Chờ nhận', 40000, null, 3)]);
  la('hoá đơn trước ưu đãi, giảm, cần trả', [r.hoaDon, r.giamUd, r.ngoaiHoaDon, r.canTra, r.uuDai.ten], [185000, 18500, 40000, 206500, 'X']);
  const r2 = K4.tomDon([d('A', 'Đã nhận', 185000, {khoa: 'b1', tong: 185000}, 2)]);
  la('không ưu đãi thì như cũ', [r2.hoaDon, r2.giamUd, r2.canTra, r2.uuDai], [185000, 0, 185000, null]);
  la('ưu đãi theo lần hỏi mới nhất', K4.tomDon([d('A', 'Đã nhận', 1, {khoa: 'b1', tong: 166500, ud: {giam: 18500}}, 5), d('B', 'Đã nhận', 1, {khoa: 'b1', tong: 185000}, 2)]).canTra, 166500);
  la('chọn sẵn', [K4.chonSanUd([{loai: 'ma', ma: 'A', giam: 1, dung_duoc: 1}, {loai: 'ctkm', ma: 'B', giam: 5, dung_duoc: 1}, {loai: 'ma', ma: 'C', giam: 9, dung_duoc: 0}]),
    K4.chonSanUd([{loai: 'ma', ma: 'A', ten: 'Đang dùng', giam: 1, dung_duoc: 1}, {loai: 'ctkm', ma: 'B', giam: 5, dung_duoc: 1}], {ten: 'Đang dùng'}), K4.chonSanUd([], null)],
    ['ctkm:B', 'ma:A', '']);
  la('số điện thoại', ['0909 123 412', '+84909123412', '12345', ''].map(K4.soDt), ['0909123412', '84909123412', '', '']);
  la('mỗi lý do đăng nhập có câu', K4.LY_DO_DN.every(x => K4.cauDn(x, t).length > 5), true);
  la('lý do lạ không câu', K4.cauDn('khac', t), '');
});

await ca('v655 (Dễ báo 13/11, anh Việt chọn A): hai tầng Bánh và Đồ uống; Bánh chia chip nhỏ theo nhóm món (Bánh lạnh, Bánh nướng, Bánh khô trước); đổi tầng thì chip nhỏ về Tất cả; menu xếp nhóm đồ uống vẫn giữ thứ tự', async () => {
  const st = JSON.parse(JSON.stringify(STORE3));
  st.quay[0].mon = [{ma: 'B1', ten: 'Canelé', gia: 65000, con: 4, nhom: 'Bánh nướng'}, {ma: 'B2', ten: 'Mousse Chanh Dây', gia: 95000, con: 2, nhom: 'Bánh lạnh'},
    {ma: 'B3', ten: 'Entremet Xoài', gia: 120000, con: 1, nhom: 'Entremets'}, {ma: 'B4', ten: 'Cookie', gia: 45000, con: 6, nhom: 'Bánh khô'},
    {ma: 'B5', ten: 'Tart Chanh', gia: 85000, con: 3, nhom: 'Bánh lạnh'}];
  const {goc} = await moTrang2({store: st});
  la('tầng', tang(goc), ['=7', 'banh=5', 'nuoc=2']);
  await bamTang(goc, 'banh');
  la('chip nhỏ của Bánh', chip(goc), ['Tất cả bánh · 5', 'Bánh lạnh · 2', 'Bánh nướng · 1', 'Bánh khô · 1', 'Entremets · 1']);
  la('tầng Bánh chỉ bánh', nutThem(goc).map(n => n.props['data-them']).sort(), ['B1', 'B2', 'B3', 'B4', 'B5']);
  await bam(tim(theoId(goc, 'storeChip'), n => n.props['data-nhom'] === 'b:Bánh lạnh')[0]);
  la('Bánh lạnh', nutThem(goc).map(n => n.props['data-them']).sort(), ['B2', 'B5']);
  await bamTang(goc, 'nuoc');
  la('đổi tầng: chip nhỏ về Tất cả đồ uống', [tim(theoId(goc, 'storeChip'), n => n.props['aria-pressed'] === 'true').map(n => n.props['data-nhom']), nutThem(goc).length], [[''], 2]);
  la('chip nhỏ Đồ uống theo thứ tự menu', tim(theoId(goc, 'storeChip'), n => n.the === 'button').map(n => n.props['data-nhom']), ['', 'g:n-tra-sua', 'g:n-ca-phe']);
});

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong');
if (hong) { console.log(loi.join('\n')); process.exit(1); }
