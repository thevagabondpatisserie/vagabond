/* v636: nút "Khách sỉ" trên đầu trang đặt bánh bản Vue (anh Việt 03/11/2026:
   "làm nút Khách sỉ trên đầu trang, kế bên nút Đặt bàn").

   Dựng THẬT khuôn đầu trang trong MAU (web_vue/banh/mau.js) bằng Vue thật của
   repo (bộ dịch khuôn có sẵn trong bản esm-browser), nút là đối tượng thường,
   rồi đọc cây đã vẽ: thứ tự nút, đường dẫn, chữ. Không dò chuỗi trong MAU.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/dau_trang_636.mjs */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createRenderer, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {ND, t, apNoiDung} from '../../../public/web_vue/kho/chu.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }

const nut = (the) => ({the, props: {}, con: [], cha: null});
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

/* Đúng khuôn đầu trang khách thấy: khối <header> đầu tiên của MAU. */
const DAU = MAU.slice(MAU.indexOf('<header>'), MAU.indexOf('</header>') + '</header>'.length);

async function veDau(nhan = {}) {
  apNoiDung({nhan, san_pham: {}, lien_he: {}, khoi: [], thong_tin: {}, ve: {}});
  const goc = nut('goc');
  createApp({template: DAU, setup: () => ({t, nav: () => {}, LOGO: '/logo.png', telSo: () => '0931224334', telChu: () => '0931 224 334'})}).mount(goc);
  await nextTick();
  const nav = tim(goc, n => n.the === 'nav' && String(n.props.class || '').split(' ').includes('dich-vu'));
  la('đúng một hàng nút dịch vụ', nav.length, 1);
  return tim(nav[0], n => n.the === 'a').map(a => [chu(a).trim(), a.props.href]);
}

await ca('đầu trang: Đặt bàn, Khách sỉ (mở /banh-si), Thành viên đúng thứ tự', async () => {
  la('ba nút', await veDau(), [['Đặt bàn', '/dat-ban'], ['Khách sỉ', '/banh-si'], ['Thành viên', '/thanh-vien']]);
});

await ca('chữ nút Khách sỉ sửa được ở trình biên tập web (khoá nut_khach_si), mặc định trùng sổ nhãn', async () => {
  const so = JSON.parse(readFileSync(path.join(GOC, 'vagabond/public/web_order/chu-mac-dinh.json'), 'utf8'));
  la('sổ nhãn có khoá', [so.nut_khach_si && so.nut_khach_si.mac_dinh, so.nut_khach_si && so.nut_khach_si.nhom], ['Khách sỉ', 'dat_banh']);
  la('đổi chữ thì nút đổi theo, đường dẫn giữ', (await veDau({nut_khach_si: 'Quán đặt sỉ'}))[1], ['Quán đặt sỉ', '/banh-si']);
  ND.nhan = {};
});

console.log('Bo ca kiem dau trang web Vue (v636)');
loi.forEach(d => console.log('  HONG  ' + d));
console.log(dat + ' ca dat, ' + hong + ' ca hong, tong ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);
