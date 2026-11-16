/* v664 Google Analytics 4 (Minh Vũ 16/11/2026). CHẠY THẬT:
   - thẻ gtag do máy chủ dựng (do_luong_ga.the_ga) chạy trong vm với window giả:
     page_location đã gỡ mã biên nhận, chỉ giữ tham số quảng cáo; khung xem thử
     của Biên tập web không nạp GA; mã dán chữ thường vẫn ra đúng G-XXXX.
   - gaTuMeta (kho/thuan.js) đổi sự kiện Pixel sang GA4.
   - bienNhan (trang/app.js) bắn purchase một lần sau khi gỡ token, mở lại không bắn nữa.
   Chạy: node vagabond/khung/kiem_thu/hanh_vi/ga_664.mjs */
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gaTuMeta, itemsGuiDon} from '../../../public/web_vue/kho/thuan.js';
import {bienNhan} from '../../../public/web_vue/trang/app.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
let dat = 0, hong = 0;
function ca(ten, f) {
  try { f(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
const bang = (mo, a, b) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); };
const dung = (mo, x) => { if (!x) throw new Error(mo); };

function theGa(ma) {
  const r = spawnSync('python3', ['-B', '-c', 'import sys;from vagabond.do_luong_ga import the_ga;sys.stdout.write(the_ga(sys.argv[1]))', ma],
    {cwd: GOC, encoding: 'utf8', env: Object.assign({}, process.env, {PYTHONPATH: GOC})});
  if (r.status !== 0) throw new Error(r.stderr);
  return r.stdout;
}
function chay(html, href, opt = {}) {
  const js = (html.match(/^<script>([\s\S]*)<\/script>$/) || [])[1];
  if (!js) throw new Error('không thấy thẻ script');
  const u = new URL(href), them = [];
  const win = {location: {href, search: u.search, origin: u.origin, pathname: u.pathname}};
  win.parent = opt.trongKhung ? {} : win;
  const doc = {referrer: opt.referrer || '', head: {appendChild: s => them.push(s.src)}, createElement: () => ({})};
  const g = {window: win, document: doc, URL, URLSearchParams, Date, encodeURIComponent};
  vm.createContext(g);
  vm.runInContext(js, g);
  return {win, them, config: (win.dataLayer || []).map(a => Array.from(a)).find(a => a[0] === 'config')};
}

ca('thẻ GA: mã dán chữ thường, có khoảng trắng vẫn ra đúng G-RMWD2XHNZ8; trống hay sai mẫu thì không có thẻ', () => {
  dung('có thẻ', theGa('  g-rmwd2xhnz8 ').includes('"G-RMWD2XHNZ8"'));
  bang('trống', theGa(''), '');
  bang('mã Universal cũ', theGa('UA-12345-1'), '');
  const doc = theGa('G-ABCD1234"</script><script>alert(1)//');
  dung('không chèn được mã lạ', !doc.includes('alert') && doc.includes('"G-ABCD1234"'));
});

ca('biên nhận: page_location gỡ mã biên nhận và số điện thoại, giữ utm và gclid; nạp đúng gtag.js', () => {
  const tok = 'A'.repeat(43);
  const r = chay(theGa('G-RMWD2XHNZ8'), 'https://order.thevagabondpatisserie.com/banh/xong/' + tok + '?sdt=0909123456&utm_source=fb&gclid=xyz');
  bang('config', r.config, ['config', 'G-RMWD2XHNZ8', {page_location: 'https://order.thevagabondpatisserie.com/banh/xong?utm_source=fb&gclid=xyz'}]);
  bang('nạp gtag', r.them, ['https://www.googletagmanager.com/gtag/js?id=G-RMWD2XHNZ8']);
  dung('có hàm gtag', typeof r.win.gtag === 'function');
});

ca('trang trước là biên nhận cùng site: page_referrer cũng gỡ token; trang ngoài chỉ còn tên miền', () => {
  const tok = 'B'.repeat(43);
  const r = chay(theGa('G-RMWD2XHNZ8'), 'https://order.thevagabondpatisserie.com/banh',
    {referrer: 'https://order.thevagabondpatisserie.com/web_moi/banh/xong/' + tok});
  bang('referrer cùng site', r.config[2].page_referrer, 'https://order.thevagabondpatisserie.com/web_moi/banh/xong');
  const n = chay(theGa('G-RMWD2XHNZ8'), 'https://order.thevagabondpatisserie.com/dat-ban', {referrer: 'https://l.facebook.com/l.php?u=abc'});
  bang('referrer ngoài', n.config[2].page_referrer, 'https://l.facebook.com/');
});

ca('khung xem thử của Biên tập web (bien_tap=1 trong iframe) không nạp GA', () => {
  const r = chay(theGa('G-RMWD2XHNZ8'), 'https://order.thevagabondpatisserie.com/banh?bien_tap=1', {trongKhung: true});
  bang('không nạp', r.them, []);
  dung('không có gtag', r.win.gtag === undefined);
});

ca('sự kiện Pixel sang GA4: xem bánh, thêm giỏ, bắt đầu thanh toán; sự kiện khác không gửi', () => {
  bang('xem bánh', gaTuMeta('ViewContent', {content_ids: ['B1', 'B2'], content_name: 'Mousse', value: 450000, currency: 'VND'}),
    ['view_item', {currency: 'VND', value: 450000, items: [{item_id: 'B1', item_name: 'Mousse'}, {item_id: 'B2', item_name: 'Mousse'}]}]);
  bang('thêm giỏ', gaTuMeta('AddToCart', {content_ids: ['B1'], value: 900000}), ['add_to_cart', {currency: 'VND', value: 900000, items: [{item_id: 'B1'}]}]);
  bang('bắt đầu thanh toán', gaTuMeta('InitiateCheckout', {content_ids: ['B1', 'B3'], value: 1200000})[0], 'begin_checkout');
  bang('PageView không gửi qua đây', gaTuMeta('PageView', {}), null);
});

ca('Codex #575 số lượng: thêm 3 bánh cùng mã là quantity 3; giỏ hai dòng cùng mã gộp lại; biên nhận ba bánh cùng mã là 3', () => {
  bang('thêm 3', gaTuMeta('AddToCart', {content_ids: ['B1'], contents: [{id: 'B1', quantity: 3}], value: 1350000})[1].items, [{item_id: 'B1', quantity: 3}]);
  bang('giỏ', gaTuMeta('InitiateCheckout', {content_ids: ['B1', 'B2', 'B1'], contents: [{id: 'B1', quantity: 2}, {id: 'B2', quantity: 1}, {id: 'B1', quantity: 1}], value: 1})[1].items,
    [{item_id: 'B1', quantity: 3}, {item_id: 'B2', quantity: 1}]);
  bang('biên nhận mon_sl', itemsGuiDon({mon_sl: [{ma: 'BAWC00139', sl: 3}], ma_mon: ['BAWC00139']}), [{item_id: 'BAWC00139', quantity: 3}]);
  bang('máy chủ cũ chỉ có ma_mon', itemsGuiDon({ma_mon: ['A', 'B']}), [{item_id: 'A', quantity: 1}, {item_id: 'B', quantity: 1}]);
});

ca('biên nhận gửi đơn: bắn purchase đúng một lần, mã giao dịch là mã sự kiện; mở lại không bắn', () => {
  const tok = 'C'.repeat(43), kho = {}, gui = [];
  const win = {
    location: {pathname: '/banh/xong/' + tok, search: ''},
    history: {replaceState: (a, b, u) => { win.location.pathname = u; }},
    sessionStorage: {getItem: k => (k in kho ? kho[k] : null), setItem: (k, v) => { kho[k] = String(v); }},
    gtag: (...a) => gui.push(a), document: {createElement: () => ({}), head: {appendChild() {}}},
  };
  const D = {bien_nhan: {ma: 'DW-1'}, pixel_id: '', su_kien: {ban: 1, event_id: 'EV-77', gia_tri: 1950000, ma_mon: ['BAWC00139'], mon_sl: [{ma: 'BAWC00139', sl: 3}]}};
  bienNhan(D, win);
  bang('một purchase, ba bánh cùng mã', gui, [['event', 'purchase', {transaction_id: 'EV-77', value: 1950000, currency: 'VND', items: [{item_id: 'BAWC00139', quantity: 3}]}]]);
  win.location.pathname = '/banh/xong/' + tok;
  bienNhan(D, win);
  bang('mở lại không bắn thêm', gui.length, 1);
});

ca('biên nhận trang cũ (bien-nhan.js chạy thật): purchase một lần, ba bánh cùng mã là quantity 3, không cần Pixel', () => {
  const fs = globalThis.process.getBuiltinModule('node:fs');
  const src = fs.readFileSync(path.join(GOC, 'vagabond/public/web_order/bien-nhan.js'), 'utf8');
  const kho = {}, gui = [];
  const mo = () => {
    const win = {VGB_BIEN_NHAN: {than: '<main></main>', pixel_id: '', su_kien: {ban: true, event_id: 'EV-9', gia_tri: 1950000,
      ma_mon: ['B1', 'B2'], mon_sl: [{ma: 'B1', sl: 3}, {ma: 'B2', sl: 1}]}},
      location: {pathname: '/banh/xong/' + 'D'.repeat(43), search: ''}, history: {replaceState() {}},
      sessionStorage: {getItem: k => (k in kho ? kho[k] : null), setItem: (k, v) => { kho[k] = String(v); }},
      gtag: (...a) => gui.push(a)};
    const g = {window: win, document: {getElementById: () => ({}), createElement: () => ({}), getElementsByTagName: () => [{parentNode: {insertBefore() {}}}]},
      Math, Number, String};
    vm.createContext(g); vm.runInContext(src, g);
  };
  mo(); mo();
  bang('một purchase', gui, [['event', 'purchase', {transaction_id: 'EV-9', value: 1950000, currency: 'VND',
    items: [{item_id: 'B1', quantity: 3}, {item_id: 'B2', quantity: 1}]}]]);
});

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong.');
process.exitCode = hong ? 1 : 0;
