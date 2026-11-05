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
  la('chip', chip(goc), ['Tất cả · 4', 'Bánh trên tủ · 1', 'Trà · 2', 'Cà phê · 1']);
  la('bốn dòng, size gộp', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['BAWC00115', 'NUTR00031', 'NUCF00003', 'NUTR00040']);
  const dong = tim(goc, n => n.props['data-ma'] === 'NUTR00031')[0];
  dung('tên gộp không còn size, ghi Size M · L, có mô tả', chu(dong).includes('Trà Sữa Lài Kem Phô Mai') && !chu(dong).includes('Size M, Đá') && chu(dong).includes('Size M · L') && chu(dong).includes('Trà lài ủ lạnh'));
  await bam(tim(theoId(goc, 'storeChip'), n => n.props['data-nhom'] === 'nuoc:Trà')[0]);
  la('chip Trà', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), ['NUTR00031', 'NUTR00040']);
  go(theoId(goc, 'gbTimO'), 'ca phe'); await cho();
  la('tìm "ca phe" (đang ở chip Trà vẫn ra vì chip Trà không có, coi như không khớp)', tim(goc, n => n.props['data-ma']).map(n => n.props['data-ma']), []);
  dung('báo không khớp', chu(theoId(goc, 'gbTimRong')).includes('"ca phe"'));
  await bam(tim(theoId(goc, 'storeChip'), n => n.props['data-nhom'] === '')[0]);
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
  la('chip theo thứ tự menu', tim(theoId(goc, 'storeChip'), n => n.the === 'button').map(n => n.props['data-nhom']), ['', 'g:n-tra-sua', 'banh', 'g:n-ca-phe']);
  la('tên chip', tim(theoId(goc, 'storeChip'), n => n.the === 'button').map(n => chu(n)), ['Tất cả · 3', 'Trà sữa · 1', 'Bánh trên tủ · 1', 'Cà phê · 1']);
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

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong');
if (hong) { console.log(loi.join('\n')); process.exit(1); }
