/* v671 (Minh Vũ 18/11/2026): món của đợt "Đặc biệt tuần này" lên tab theo ĐỢT,
   không theo tồn tủ hay ô Đủ decor của Kiểm bánh.

   Ca thật trên site: đợt có Hũ Stollen (chưa có trên tủ, bếp chưa điền decor),
   tab báo "Món của tuần này đang được cập nhật". Ca dưới nạp THẬT kho trang đặt
   bánh (kho-banh.js) với Vue thật, máy chủ giả trả đúng khuôn co_the_ban_hom_nay,
   rồi vẽ THẬT thành phần DacBietTuan. Luật máy chủ ở thu_dac_biet_tuan_671.py.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/dac_biet_tuan_671.mjs */
import {createRenderer, h, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {t0} from '../../../public/web_vue/kho/thuan.js';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {DacBietTuan} from '../../../public/web_vue/banh/dac-biet-tuan.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + (e && e.message || e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

const STOLLEN = 'bánh stollen cookie, hũ 200 gr';
function dotMau(mon) {
  return {id: 'dbt-28', loai: 'dac_biet_tuan', hien: true, nhan: 'CHỈ CUỐI TUẦN', tieu_de: 'CUỐI TUẦN\n28 · 29/11',
    bat_dau: '2026-11-17', ket_thuc: '2026-11-29', mo_don: '2026-11-17T08:00', chot_don: '2026-11-27T20:00',
    ngay_giao: ['2026-11-28', '2026-11-29'], dem_nguoc: '1', dem_chu_1: '', dem_chu_2: '',
    moc: [{nhan: 'MỞ ĐƠN', chu_ngay: 'T3 17/11', luc: '2026-11-17T08:00'}, {nhan: 'CHỐT ĐƠN', chu_ngay: 'T6 27/11', luc: '2026-11-27T20:00'}],
    mon_dt: mon || [{khoa: STOLLEN, mo_ta: 'Bơ, quế, hạnh nhân', anh: '', nhan_goc: '', toi_da: '30'}]};
}
/* Khuôn trả của kiem_banh.co_the_ban_hom_nay trên site (chi_hien 1: bảng Bánh trên web đang dùng). */
const NHOM_STOLLEN = {ten: 'Bánh Stollen Cookie, Hũ 200 gr', anh: '/files/stollen.jpg', anhs: ['/files/stollen.jpg'], mo_ta: 'Bánh quy Stollen',
  tang: [], tu_web: 1, sizes: [{ma: 'BACF00051', cm: 0, gia: 180000}]};
function mayChu(them = {}) {
  return Object.assign({ngay: '2026-11-18', banh: {}, mon: [], nhom: [], chi_hien: 1,
    dat_truoc: {nhom: [{ten: 'CANDLE', anh: '', sizes: [{ma: 'BAWC00139', cm: 12, gia: 650000, con: 2}]}]},
    dac_biet: [NHOM_STOLLEN]}, them);
}
async function khoMoi(gio, dot, tra) {
  const k = taoKho({t: t0, tMon: (m, tr, x) => x || '', bayGio: () => new Date(gio), hen: () => 0, huyHen: () => {},
    doc: async ham => (ham === 'vagabond.kiem_banh.co_the_ban_hom_nay' ? JSON.parse(JSON.stringify(tra)) : {}),
    ghi: async () => ({ok: true}), luuTru: null, suKien: () => {}, nd: {nhan: {}, khoi: [dot], dac_biet_da_dat: {}}});
  await k.napTon();
  return k;
}

/* ---------- vẽ thành phần bằng bộ dựng cây của Vue (cùng khuôn dac_biet_tuan_667.mjs) ---------- */
const nut = the => ({the, props: {}, con: [], cha: null});
const {createApp} = createRenderer({
  createElement: the => nut(the), createText: chu => ({chu, cha: null}), createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; }, setElementText: (n, chu) => { n.con = chu ? [{chu, cha: n}] : []; },
  insert: (con, cha, moc) => { if (con.cha) con.cha.con.splice(con.cha.con.indexOf(con), 1); const i = moc ? cha.con.indexOf(moc) : -1; if (i >= 0) cha.con.splice(i, 0, con); else cha.con.push(con); con.cha = cha; },
  remove: con => { if (con.cha) { con.cha.con.splice(con.cha.con.indexOf(con), 1); con.cha = null; } },
  parentNode: n => n.cha, nextSibling: n => (n.cha ? n.cha.con[n.cha.con.indexOf(n) + 1] || null : null),
  patchProp: (n, k, cu, moi) => { if (moi == null) delete n.props[k]; else n.props[k] = moi; },
  setScopeId: () => {}, insertStaticContent: () => { throw new Error('không dùng'); }
});
const chu = n => (n == null ? '' : n.chu != null ? n.chu : (n.con || []).map(chu).join(''));
function tim(n, dk, ra = []) { if (!n || !n.con) return ra; if (n.the && dk(n)) ra.push(n); n.con.forEach(x => tim(x, dk, ra)); return ra; }
const lop = (n, l) => String(n.props.class || '').split(' ').includes(l);
async function ve(k) {
  ND.dac_biet_da_dat = {};
  const mo = [];
  const goc = nut('div');
  createApp({render: () => h(DacBietTuan, {kho: k, mo: c => mo.push(c.k)})}).mount(goc);
  await nextTick();
  return {goc, mo};
}

await ca('1. Hũ Stollen chỉ làm cho đợt (không có trên tủ, chưa có Đủ decor): tab hiện thẻ món, nút Đặt món này mở đúng bánh; không còn câu "đang được cập nhật"', async () => {
  const k = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu());
  const {goc, mo} = await ve(k);
  dung('không còn câu đang cập nhật', !/đang được cập nhật/.test(chu(goc)));
  la('một thẻ lớn', tim(goc, n => lop(n, 'dbt-mot')).length, 1);
  dung('tên món', /Stollen/.test(chu(goc)));
  dung('giá lấy từ máy chủ', /180\.000/.test(chu(goc)));
  tim(goc, n => lop(n, 'dbt-dat'))[0].props.onClick();
  la('bấm Đặt món này mở đúng bánh', mo, ['Bánh Stollen Cookie, Hũ 200 gr']);
});

await ca('2. Món của đợt KHÔNG lọt sang tab Đặt bánh trước hay Có sẵn hôm nay (không dùng ô Đủ decor sai mục đích)', async () => {
  const k = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu());
  la('Đặt bánh trước chỉ có CANDLE', k.banhDatTruoc.value.map(c => c.k), ['CANDLE']);
  la('Có sẵn hôm nay trống', k.banhHomNay.value.map(c => c.k), []);
  const k2 = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu({chi_hien: 0, dat_truoc: {nhom: []}}));
  dung('bảng Bánh trên web chưa dùng, không có Đủ decor: Đặt trước vẫn không có Hũ Stollen',
    !k2.banhDatTruoc.value.some(c => /Stollen/.test(c.k)));
});

await ca('3. Thêm Hũ Stollen vào giỏ từ tab Đặc biệt: dòng đặt trước, mã đúng, ngày dời sang ngày giao của đợt; giỏ ghi "Một cỡ", không "Ø 0cm"', async () => {
  const k = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu());
  k.S.tab = 'dac_biet';
  k.moBanh(k.S.CAKES.find(c => /Stollen/.test(c.k)));
  la('size của đợt', k.kichThuocDangBan(k.S.cur).map(s => s.id), ['BACF00051']);
  la('thêm vào giỏ', k.addToCart(), 'them');
  la('dòng giỏ', [k.S.CART[0].id, k.S.CART[0].nguon, k.S.CART[0].price], ['BACF00051', 'order', 180000]);
  la('ngày dời sang ngày giao đầu của đợt', k.T.isoNgay(k.ngayDangChon.value), '2026-11-28');
  const d = k.dongGio.value[0];
  la('dòng phụ giỏ', d.phu, 'Một cỡ, mã BACF00051');
});

await ca('4. Bánh vừa trong đợt vừa có Đủ decor 2 cái ở size 12: đợt bán mọi size bán được của thẻ Bánh, số lượng theo đợt (30), không bị chặn ở 2 cái decor', async () => {
  const dot = dotMau([{khoa: 'candle', mo_ta: '', anh: '', nhan_goc: '', toi_da: '30'}]);
  const tra = mayChu({dac_biet: [{ten: 'CANDLE', anh: '/files/c.jpg', anhs: ['/files/c.jpg'], mo_ta: '', tang: [], tu_web: 1,
    sizes: [{ma: 'BAWC00139', cm: 12, gia: 650000}, {ma: 'BAWC00140', cm: 16, gia: 880000}]}]});
  const k = await khoMoi('2026-11-18T10:00:00+07:00', dot, tra);
  k.S.tab = 'dac_biet';
  const c = k.S.CAKES.find(x => x.k === 'CANDLE');
  k.moBanh(c);
  la('hai size của đợt', k.kichThuocDangBan(c).map(s => s.id), ['BAWC00139', 'BAWC00140']);
  k.S.curSizeId = 'BAWC00139'; k.S.soLuong = 3;
  la('3 cái size 12 (decor chỉ 2): vẫn nhận theo đợt', k.addToCart(), 'them');
  k.cartQty(0, 1);
  la('bấm + trong giỏ lên 4', k.S.CART[0].qty, 4);
});

await ca('5. Giỏ lưu có Hũ Stollen (cỡ 0, có nguồn đặt trước): mở lại trang vẫn còn, không bị coi là hàng mùa vụ rồi mất', async () => {
  const kho = {};
  const luuTru = {getItem: k => kho[k] || null, setItem: (k, v) => { kho[k] = v; }, removeItem: k => { delete kho[k]; }};
  const tao = () => taoKho({t: t0, tMon: (m, tr, x) => x || '', bayGio: () => new Date('2026-11-18T10:00:00+07:00'), hen: () => 0, huyHen: () => {},
    doc: async ham => (ham === 'vagabond.kiem_banh.co_the_ban_hom_nay' ? JSON.parse(JSON.stringify(mayChu())) : {}),
    ghi: async () => ({ok: true}), luuTru, suKien: () => {}, nd: {nhan: {}, khoi: [dotMau()], dac_biet_da_dat: {}}});
  const k = tao();
  await k.napTon();
  k.S.daPhucHoi = true;
  k.S.tab = 'dac_biet'; k.moBanh(k.S.CAKES.find(c => /Stollen/.test(c.k))); k.addToCart();
  k.luuGio();
  const k2 = tao();
  k2.phucHoiGio();
  await k2.napTon();
  la('giỏ khôi phục còn Hũ Stollen', k2.S.CART.map(o => o.id), ['BACF00051']);
  la('không nằm trong hàng mùa vụ chờ', k2.S.gioCho.mua.length, 0);
});

await ca('Codex #594: dị ứng, bảo quản của thẻ Bánh còn nguyên sau khi trộn món của đợt (napTon): nhóm hôm nay và nhóm của đợt cùng mang hai mục; nguồn cũ không gửi hai khoá thì không xoá', async () => {
  const NHOM = {ten: 'Bánh Stollen Cookie, Hũ 200 gr', anh: '/files/stollen.jpg', anhs: ['/files/stollen.jpg'], mo_ta: 'Bánh quy Stollen', tang: [],
    di_ung: 'Bơ, bột mì, hạnh nhân', bao_quan: 'Nơi khô ráo, dùng trong 30 ngày', tu_web: 1, sizes: [{ma: 'BACF00051', cm: 0, gia: 180000}]};
  const k = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu({nhom: [NHOM], dac_biet: [NHOM]}));
  const c = k.S.CAKES.find(x => x.sizes.some(z => z.id === 'BACF00051'));
  la('hai mục còn sau khi trộn', [c.diUng, c.baoQuan], ['Bơ, bột mì, hạnh nhân', 'Nơi khô ráo, dùng trong 30 ngày']);
  const cu = Object.assign({}, NHOM); delete cu.di_ung; delete cu.bao_quan;
  const k2 = await khoMoi('2026-11-18T10:00:00+07:00', dotMau(), mayChu({nhom: [NHOM], dac_biet: [cu]}));
  const c2 = k2.S.CAKES.find(x => x.sizes.some(z => z.id === 'BACF00051'));
  la('nhóm của đợt không mang khoá: giữ giá trị nhóm hôm nay', [c2.diUng, c2.baoQuan], ['Bơ, bột mì, hạnh nhân', 'Nơi khô ráo, dùng trong 30 ngày']);
});

console.log(`\n${dat} đạt, ${hong} hỏng`);
if (hong) { console.log('Hỏng: ' + loi.join(' | ')); process.exit(1); }
