/* UI Nghệ sĩ công nghệ (Codex #600): chạy NGUYÊN tệp app_bep.js như trang thật nạp nó.
 *
 * Trang /bep chèn app_bep.js bằng thẻ script động (vagabond/trang/bep.js), nên lúc tệp chạy
 * thì document.readyState thường đã là 'complete' và __boot() chạy NGAY trong phần 12, khi
 * các phần sau (13 tới 99) chưa chạy câu lệnh cấp ngoài cùng nào. Máy chụp nạp bằng thẻ
 * script thẳng trong HTML nên không đi qua nhánh này.
 *
 * Cách dùng: node ui_b_nap_sau_load.js <app_bep.js> <complete|loading> [lech]
 * In JSON: số thẻ style giao diện mới, CSS của nó, số bộ theo dõi DOM đã tạo.
 * Không giả lập gì thêm ngoài cây DOM tối thiểu: mạng trả lời không bao giờ tới (whoAmI treo),
 * đúng như lúc trang vừa mở, chưa vẽ màn nào. */
'use strict';
const fs = require('fs');
const vm = require('vm');
const [tep, trangThai, cheDo] = process.argv.slice(2);  /* cheDo 'lech': HTML ghi phiên bản khác app */
const ma = fs.readFileSync(tep, 'utf8');
const appver = (ma.match(/var APPVER = '(\d+)'/) || [])[1];

/* Vật thay thế cho mọi thứ không quan tâm: gọi được, đọc thuộc tính nào cũng ra chính nó,
   await thì treo mãi (then không bao giờ gọi lại). */
function bong() {
  const f = function () { return p; };
  const p = new Proxy(f, {
    get(t, k) {
      if (k === Symbol.toPrimitive) return () => '';
      if (k === 'then') return undefined;
      if (k === 'length') return 0;
      return p;
    },
    apply() { return p; },
    construct() { return p; },
    set() { return true; },
    has() { return true; },
  });
  return p;
}
function hua() { return new Promise(() => { }); }

const theStyle = [];
const choLoad = [];
let soTheoDoi = 0;
const lop = new Set(['ui-b']);
function phanTu(ten) {
  const o = {
    tagName: String(ten).toUpperCase(), id: '', textContent: '', style: {}, dataset: {}, children: [], childNodes: [],
    classList: { add: (c) => { }, remove: (c) => { }, contains: () => false, toggle: () => { } },
    setAttribute() { }, getAttribute() { return null }, removeAttribute() { },
    appendChild(c) { this.children.push(c); return c; }, insertBefore(c) { this.children.push(c); return c; }, removeChild() { },
    addEventListener() { }, removeEventListener() { }, querySelector() { return null; }, querySelectorAll() { return []; },
    getBoundingClientRect() { return { top: 0, left: 0, width: 0, height: 0 }; },
  };
  return o;
}
const vgb = phanTu('div'); vgb.id = 'vgb';
const head = phanTu('head');
/* Máy chủ đã chèn meta màu vỏ app của giao diện mới (giao_dien.dau_trang_html). */
let metaVo = phanTu('meta'); metaVo.name = 'theme-color'; metaVo.content = '#EAF4F3';
head.appendChild = function (c) {
  if (c.id === 'vgbUiB') theStyle.push(c);
  if (c.name === 'theme-color') metaVo = c;
  this.children.push(c); return c;
};
const html = phanTu('html');
html.classList = { contains: (c) => lop.has(c), add: (c) => lop.add(c), remove: (c) => lop.delete(c), toggle: () => { } };
const document = new Proxy({
  readyState: trangThai,
  documentElement: html, head: head, body: phanTu('body'),
  createElement: phanTu, createElementNS: (n, t) => phanTu(t),
  getElementById: (id) => id === 'vgb' ? vgb : (id === 'vgbUiB' ? (theStyle[0] || null) : null),
  querySelector: (q) => (/theme-color/.test(q) ? metaVo : null), querySelectorAll: () => [],
  addEventListener() { }, removeEventListener() { },
  cookie: '', title: '', visibilityState: 'visible', hidden: false,
}, { get(t, k) { return k in t ? t[k] : bong(); } });

/* Đếm riêng bộ theo dõi của giao diện mới (tạo trong uiBTheoDoi). Bộ theo dõi hộp dùng chung
   (hopGan, phần 00) chạy ở cả hai giao diện, đếm riêng để ca biết nó cũng chỉ một. */
let soTheoDoiHop = 0;
class MutationObserver {
  constructor() {
    const ngan = String(new Error().stack || '');
    if (/uiBTheoDoi/.test(ngan)) soTheoDoi++;
    else if (/hopGan/.test(ngan)) soTheoDoiHop++;
  }
  observe() { } disconnect() { }
}
const cuaSo = {
  document, MutationObserver, console: { log() { }, warn() { }, error() { }, info() { } },
  __VGB_UI: { b: 1, v: cheDo === 'lech' ? '1' : appver },
  setTimeout: () => 0, clearTimeout() { }, setInterval: () => 0, clearInterval() { },
  requestAnimationFrame: () => 0, queueMicrotask: (f) => Promise.resolve().then(f),
  fetch: hua, Promise, JSON, Math, Date, Object, Array, String, Number, Boolean, RegExp, Error, Map, Set, Symbol, Proxy, Reflect,
  encodeURIComponent, decodeURIComponent, parseInt, parseFloat, isNaN, isFinite,
  frappe: { csrf_token: 'thu', session: { user: 'thu@vgb' }, boot: {}, call: hua },
  location: { href: 'http://vgb.thu/bep', pathname: '/bep', search: '', hash: '', hostname: 'vgb.thu', origin: 'http://vgb.thu', reload() { }, replace() { } },
  addEventListener(ten, f) { if (ten === 'load') choLoad.push(f); }, removeEventListener() { },
};
const goc = new Proxy(cuaSo, {
  get(t, k) { if (k === Symbol.unscopables) return undefined; if (k in t) return t[k]; if (k === 'window' || k === 'self' || k === 'globalThis') return goc; return bong(); },
  has() { return true; },
  set(t, k, v) { t[k] = v; return true; },
});
let loi = null;
try { vm.runInNewContext('with (__goc) {' + ma + '\n}', { __goc: goc }, { filename: 'app_bep.js' }); }
catch (e) { loi = String(e && e.message || e); }
/* Trang còn đang nạp: sự kiện load tới SAU khi toàn bộ tệp đã chạy xong. */
choLoad.forEach((f) => { try { f(); } catch (e) { loi = loi || String(e && e.message || e); } });
Promise.resolve().then(() => Promise.resolve()).then(() => {
  const css = theStyle.map((s) => s.textContent).join('');
  console.log(JSON.stringify({ loi, appver, so_the: theStyle.length, so_theo_doi: soTheoDoi, co_lop: lop.has('ui-b'), so_theo_doi_hop: soTheoDoiHop, mau_vo: metaVo && metaVo.content, css_dai: css.length, css }));
});
