/* v649 (Loan Anh báo, anh Việt chọn tách đơn 11/11/2026): tab Đặt bánh trước
   không còn ngày Hôm nay; giỏ không trộn bánh Có sẵn hôm nay với bánh đặt trước.

   Chạy THẬT kho trang đặt bánh (kho-banh.js) với Vue thật, đồng hồ cố định,
   mạng giả ghi vết; khuôn lịch cắt đúng từ MAU rồi MOUNT bằng bộ dựng cây của
   Vue. Mỗi ca dựng đúng chuỗi bấm của khách, không gọi thêm hàm "cho chắc".

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/dat_truoc_tu_mai_649.mjs */
import {createRenderer, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {t0} from '../../../public/web_vue/kho/thuan.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten); console.log('  HONG  ' + ten + '\n        ' + (e && e.message || e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* Thứ Tư 11/11/2026 10:00 sáng, như ảnh Loan Anh gửi. */
function moiTruong(gio = '2026-11-11T10:00:00', luu = null) {
  const vet = [];
  const kho = new Map(luu ? [['vgb-gio-v1', luu]] : []);
  const mt = {
    t: t0, tMon: (ma, tr, d) => d || '', bayGio: () => new Date(gio),
    hen: () => 0, huyHen: () => {},
    doc: async (p, th) => { vet.push(['GET', p, th]); return {}; },
    ghi: async (p, th) => { vet.push(['POST', p, th]); return {ok: true}; },
    luuTru: {getItem: k => (kho.has(k) ? kho.get(k) : null), setItem: (k, v) => kho.set(k, v), removeItem: k => kho.delete(k)},
    suKien: () => {}, nd: {nhan: {}}
  };
  return {mt, vet};
}
/* Khách đứng ở tab nào thì bấm thêm bánh ở tab đó. */
function them(k, tab, ten = 'CANDLE') { k.S.tab = tab; k.moBanh(k.S.CAKES.find(c => c.k === ten)); return k.addToCart(); }

/* ---------- bộ dựng cây của Vue, nút là đối tượng thường ---------- */
const nut = the => ({the, props: {}, con: [], cha: null, nghe: {},
  addEventListener(ev, f) { (this.nghe[ev] = this.nghe[ev] || []).push(f); },
  removeEventListener(ev, f) { this.nghe[ev] = (this.nghe[ev] || []).filter(x => x !== f); }});
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
const DAU = MAU.indexOf('<div class="rail" id="rail">'), CUOI = MAU.indexOf('<div class="note" id="orderNote">');
dung('cắt được lịch tab Đặt bánh trước', DAU > 0 && CUOI > DAU);
const LICH = MAU.slice(DAU, CUOI);

await ca('1. Tab Đặt bánh trước: lịch bắt đầu từ Ngày mai 12/11, không còn ô Hôm nay; dưới lịch có dòng dẫn sang tab Có sẵn hôm nay', async () => {
  const {mt} = moiTruong();
  const k = taoKho(mt);
  k.S.tab = 'order';
  const goc = nut('goc');
  createApp({template: '<div>' + LICH + '</div>', setup: () => ({S: k.S, kho: k, t: t0})}).mount(goc);
  await nextTick();
  const ngay = tim(goc, n => n.the === 'button' && /\bday\b/.test(n.props.class || '')).map(n => chu(n));
  la('ô đầu là Ngày mai 12/11', ngay[0], 'Ngày mai12/11');
  dung('không còn Hôm nay', !ngay.some(x => x.includes('Hôm nay') || x.includes('11/11')));
  la('đủ 13 ngày', ngay.length, 13);
  const a = tim(goc, n => n.the === 'a')[0];
  dung('có dòng dẫn', a && chu(a).includes('Cần bánh hôm nay? Xem tab Có sẵn hôm nay'));
  la('dẫn sang tab Có sẵn hôm nay', a.props.href, '#/');
});

await ca('2. Giỏ có bánh đặt trước: ô Hôm nay ở bước Ngày và giờ nhận mờ, bấm vào thì báo tách đơn và không đổi ngày', async () => {
  const {mt} = moiTruong();
  const k = taoKho(mt);
  la('thêm bánh đặt trước', them(k, 'order'), 'them');
  dung('ô Hôm nay mờ', k.ngayRail.value[0].off);
  const truoc = k.S.ngayChon;
  k.pick(0);
  la('không đổi ngày', k.S.ngayChon, truoc);
  dung('báo tách đơn', k.S.toast.chu.includes('nhận từ ngày mai'));
  k.pick(1);
  la('chọn ngày mai được', k.S.ngayChon, '2026-11-12');
});

await ca('3. Giỏ chỉ có bánh Có sẵn hôm nay: vẫn nhận hôm nay như cũ', async () => {
  const {mt} = moiTruong();
  const k = taoKho(mt);
  la('thêm bánh hôm nay', them(k, 'today'), 'them');
  dung('ô Hôm nay không mờ', !k.ngayRail.value[0].off);
  k.pick(0);
  la('chọn hôm nay được', k.S.ngayChon, '2026-11-11');
});

await ca('4. Tách đơn: giỏ có bánh hôm nay thì không thêm bánh đặt trước, và ngược lại (nút chi tiết lẫn nút +)', async () => {
  const {mt} = moiTruong();
  const k = taoKho(mt);
  them(k, 'today');
  la('không thêm bánh đặt trước', them(k, 'order'), false);
  dung('câu báo', k.S.toast.chu.includes('Giỏ đang có bánh có sẵn hôm nay'));
  la('giỏ vẫn 1 dòng', k.S.CART.length, 1);
  const k2 = taoKho(moiTruong().mt);
  them(k2, 'order');
  k2.S.TODAY = {BAWC00122: 3};
  la('nút + bánh hôm nay bị chặn', k2.themNhanh(k2.S.CAKES.find(c => c.k === 'Kankin'), 'today'), 'chan');
  dung('câu báo', k2.S.toast.chu.includes('Giỏ đang có bánh đặt trước'));
  la('giỏ vẫn 1 dòng', k2.S.CART.length, 1);
});

await ca('5. Giỏ lưu hôm trước còn ngày nhận là hôm nay: thêm bánh đặt trước thì máy dời sang ngày mai và nhờ chọn lại lịch', async () => {
  const luu = JSON.stringify({luc: new Date('2026-11-11T09:00:00').getTime(), gio: [], ngay: '2026-11-11', slot: 8,
    daChonNgay: true, daChonGio: true, truong: {}, co: {}});
  const {mt} = moiTruong('2026-11-11T10:00:00', luu);
  const k = taoKho(mt);
  if (k.phucHoiGio) k.phucHoiGio();
  la('ngày lưu là hôm nay', k.picked.value, 0);
  them(k, 'order');
  la('dời sang ngày mai', k.S.ngayChon, '2026-11-12');
  la('nhờ khách xác nhận lại ngày', k.S.daChonNgay, false);
});

await ca('6. Giỏ cũ trộn hai loại (lưu từ trước v649): bấm Gửi đơn thì báo tách đơn, không gửi gì lên máy chủ', async () => {
  const {mt, vet} = moiTruong();
  const k = taoKho(mt);
  them(k, 'today');
  /* Dòng đặt trước nằm sẵn trong giỏ lưu cũ, không đi qua nút thêm. */
  k.S.CART.push(Object.assign({}, k.S.CART[0], {nguon: 'order'}));
  k.pick(1); k.pickSlot(8);
  k.S.f.name = 'Khách thử'; k.S.f.phone = '0900000000';
  const kq = await k.submitOrder();
  la('dừng ở giỏ', kq && kq.buoc, 'gio');
  dung('câu báo', k.S.toast.chu.includes('đặt đơn riêng'));
  la('không gửi đơn', vet.filter(x => x[0] === 'POST' && x[1] === 'vagabond.don_hang.tao_don').length, 0);
});

console.log('\n' + dat + ' dat, ' + hong + ' hong');
process.exit(hong ? 1 : 0);
