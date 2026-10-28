/* Ca kiểm HÀNH VI v619: chuông thông báo trong app (anh Việt chọn 28/10/2026).
 *
 * CHẠY THẬT:
 *   - khung app 01-khung-app.js (frame, go, reset, back),
 *   - bảng đường dẫn và vgbGo THẬT của 02-trang-chu.js (nhánh CHUONG, BCHH, VCL),
 *   - today, addDays của 00-nen.js,
 *   - toàn bộ 59-chuong.js (nút chuông, đeo số, màn Chuông thông báo).
 * Máy chủ là bản giả trả đúng hình dạng của vagabond/chuong.py. Trang chủ, màn Việc
 * cần làm và màn xem báo cáo là bản giả chỉ ghi lại việc được mở. Mỗi ca bấm đúng
 * chuỗi thao tác của nhân viên, không gọi thêm hàm nào "cho chắc".
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/chuong_619.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var BEP = path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
function layHam(src, ten) {
  var m = new RegExp('(?:async )?function ' + ten + '\\(').exec(src);
  if (!m) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', m.index), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(m.index, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function doan(src, dau, cuoiHam) {
  var a = src.indexOf(dau);
  if (a < 0) throw new Error('Khong thay ' + dau);
  var hm = layHam(src.slice(a), cuoiHam);
  return src.slice(a, src.indexOf(hm, a) + hm.length);
}
var NEN = doc('00-nen.js'), KHUNG = doc('01-khung-app.js'), TC = doc('02-trang-chu.js'), CH = doc('59-chuong.js');

var dat = 0, hong = 0;
function la(nhan, duoc, mong) {
  var a = JSON.stringify(duoc), b = JSON.stringify(mong);
  if (a === b) { dat++; console.log('  DAT   ' + nhan); }
  else { hong++; console.log('  HONG  ' + nhan + '\n        duoc ' + a + '\n        mong ' + b); }
}
async function nghi() { for (var i = 0; i < 20; i++) await new Promise(function (r) { setImmediate(r); }); }

var APP = 'https://app.thevagabondpatisserie.com';
var TIN = {
  ds: [
    { ten: 't1', ma_tin: 'kt_du_lieu_hao_hut', tieu_de: '📊 BẢN TIN: Dữ liệu hao hụt tuần 21/10 - 27/10',
      than: 'Chưa đủ dữ liệu.\n- a\n- b\n- c\n- d', link: APP + '/du-lieu-hao-hut', luc: '2026-10-28 08:00:05.000001', moi: 1 },
    { ten: 't2', ma_tin: 'kho_da_chuyen', tieu_de: 'ℹ️ THÔNG BÁO: Đã chuyển hàng giữa kho', than: '',
      link: APP + '/hang-chuyen-ve-kho-toi?mo=PDC-1', luc: '2026-10-27 19:06:00.000001', moi: 1 },
    { ten: 't3', ma_tin: 'bh_dat_ban', tieu_de: '✅ VIỆC CẦN LÀM: Đặt bàn mới', than: '- 4 khách', link: '',
      luc: '2026-10-26 10:00:00.000001', moi: 0 },
  ], co_phong_ban: 1, so_ngay: 14,
};

function napApp(nguoi, traTin) {
  var tl = dg.taiLieuGia();
  tl.head = new dg.ElementGia('head');
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var ve = { api: [], mo: [], href: [], mo_tab: [] };
  var loc = { href: APP + '/bep', pathname: '/bep', hostname: 'app.thevagabondpatisserie.com', search: '', hash: '' };
  Object.defineProperty(loc, 'href', { get: function () { return APP + this.pathname + this.search; },
    set: function (v) { ve.href.push(String(v)); } });
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date, URL: URL,
    document: tl, location: loc, APPNAME: 'Vagabond',
    frappe: { session: { user: nguoi } },
    history: { state: null, pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 0; }, clearTimeout: function () {},
    open: function (u) { ve.mo_tab.push(u); },
    api: function (m, ts) {
      ve.api.push(m);
      if (m === 'vagabond.chuong.dem') return Promise.resolve({ viec: 3, tin: 2, tong: 5 });
      if (m === 'vagabond.chuong.thong_bao') return Promise.resolve(JSON.parse(JSON.stringify(traTin || TIN)));
      if (m === 'vagabond.chuong.da_xem') return Promise.resolve({ luc: 'x' });
      return Promise.reject(new Error('api la ' + m));
    },
  };
  g.window = g;
  g.addEventListener = function () {};
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast() {}', 'function sheet() {}', 'function dSkin() {}', 'function vgbCss() {}',
    'function shortWh(x) { return String(x || ""); }', 'function inNapJs() { return Promise.resolve(); }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'var bcMa = null, bcKy = "ngay", bcMoc = null;',
    'async function scrHome() { frame(APPNAME, "<div>trang chu</div>"); }',
    'async function scrVclList() { __ve.mo.push("VCL"); frame("Việc cần làm", "<div>viec</div>"); }',
    'async function scrBaoCaoXem() { __ve.mo.push("BCX:" + bcMa + ":" + bcKy + ":" + bcMoc); frame("Báo cáo", "<div></div>"); }',
  ].join('\n'), Object.assign(g, { __ve: ve }));
  vm.runInContext(layHam(NEN, 'today') + '\n' + layHam(NEN, 'addDays'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(doan(TC, 'var VGB_DUONG = {', 'vgbMoTheoDiaChi') + '\n' + layHam(TC, 'vgbGo'), g);
  vm.runInContext(CH, g);
  g.S.user = nguoi;
  return { g: g, tl: tl, ve: ve };
}
function bam(a, el) { return el.onclick({ target: el, preventDefault: function () {} }); }
function bamTrong(a, el) { return a.tl.getElementById('vgbBody').onclick({ target: el, preventDefault: function () {} }); }

(async function () {
  console.log('v619 hành vi: chuông thông báo trong app');

  var a = napApp('kt@vagabond.vn');
  await a.g.reset(a.g.scrHome); await nghi();
  var nut = a.tl.getElementById('vgbChuong');
  la('trang chủ có chuông', !!nut, true);
  la('chuông đeo số việc + tin chưa đọc', [a.tl.getElementById('vgbChuongSo').textContent, a.tl.getElementById('vgbChuongSo').style.display], ['5', '']);

  // Vẽ lại trang chủ trong một phút: không hỏi máy chủ lần nữa, số vẫn còn.
  await a.g.reset(a.g.scrHome); await nghi();
  la('một phút chỉ hỏi số một lần', a.ve.api.filter(function (m) { return m === 'vagabond.chuong.dem'; }).length, 1);
  la('số vẫn đeo sau khi vẽ lại', a.tl.getElementById('vgbChuongSo').textContent, '5');

  // Bấm chuông: màn Chuông thông báo, hai thẻ, ba tin, đánh dấu đã đọc.
  bam(a, a.tl.getElementById('vgbChuong')); await nghi();
  la('mở màn Chuông thông báo', a.g.S.stack.length, 2);
  la('không còn chuông ở màn con (có nút lui)', [!!a.tl.getElementById('vgbChuong'), !!a.tl.getElementById('vgbBack')], [false, true]);
  var chu = a.tl.getElementById('vgbBody').textContent;
  la('thẻ Thông báo nói 2 mới, thẻ Việc nói 3', [chu.indexOf('🔔 Thông báo · 2 mới') >= 0, chu.indexOf('📌 Việc cần làm · 3') >= 0], [true, true]);
  la('ba tin', a.tl.querySelectorAll('[data-chi]').length, 3);
  la('hai nút Mở (tin không đường thì không có)', a.tl.querySelectorAll('[data-chmo]').length, 2);
  la('mở thẻ là đánh dấu đã đọc', a.ve.api.indexOf('vagabond.chuong.da_xem') >= 0, true);
  la('thân dài thì thu gọn', [chu.indexOf('- d') < 0, a.tl.querySelectorAll('[data-chxem]').length], [true, 1]);
  bamTrong(a, a.tl.querySelectorAll('[data-chxem]')[0]); await nghi();
  la('bấm Xem hết thì hiện đủ', a.tl.getElementById('vgbBody').textContent.indexOf('- d') >= 0, true);

  // Mở tin có mã phiếu: tải lại đúng địa chỉ để màn đọc ?mo.
  var moTin = function (i) { return a.tl.querySelectorAll('[data-chmo]').filter(function (n) { return n.getAttribute('data-chmo') === String(i); })[0]; };
  bamTrong(a, moTin(1)); await nghi();
  la('tin chuyển hàng: tải lại đúng phiếu', a.ve.href, ['/hang-chuyen-ve-kho-toi?mo=PDC-1']);
  bamTrong(a, moTin(0)); await nghi();
  la('tin hao hụt: mở báo cáo BC18 tuần trước, không tải lại', [a.ve.mo[a.ve.mo.length - 1], a.ve.href.length],
    ['BCX:BC18:tuan:' + a.g.addDays(a.g.today(), -7), 1]);

  // Thẻ Việc cần làm: sang màn đã có.
  a.g.back(); await nghi();
  bam(a, a.tl.getElementById('chViec')); await nghi();
  la('thẻ Việc cần làm mở màn Việc cần làm', a.ve.mo[a.ve.mo.length - 1], 'VCL');

  // Sau khi đã đọc: về trang chủ, số chỉ còn việc.
  await a.g.reset(a.g.scrHome); await nghi();
  la('về trang chủ số còn 3 việc', a.tl.getElementById('vgbChuongSo').textContent, '3');

  // Khách chưa đăng nhập: không có chuông.
  var b = napApp('Guest');
  await b.g.reset(b.g.scrHome); await nghi();
  la('chưa đăng nhập không có chuông', !!b.tl.getElementById('vgbChuong'), false);

  // Chưa gắn phòng ban: nói rõ phải làm gì.
  var c = napApp('moi@vagabond.vn', { ds: [], co_phong_ban: 0, so_ngay: 14 });
  await c.g.reset(c.g.scrHome); await nghi();
  bam(c, c.tl.getElementById('vgbChuong')); await nghi();
  la('chưa gắn phòng ban có câu hướng dẫn', c.tl.getElementById('vgbBody').textContent.indexOf('chưa gắn phòng ban') >= 0, true);

  // Đường ngoài app mở thẻ mới, không rời app.
  var d = napApp('kt@vagabond.vn', { ds: [{ ten: 'x', tieu_de: 'T', than: '', link: 'https://maps.google.com/?q=1', luc: '', moi: 0 }],
    co_phong_ban: 1, so_ngay: 14 });
  await d.g.reset(d.g.scrHome); await nghi();
  bam(d, d.tl.getElementById('vgbChuong')); await nghi();
  bamTrong(d, d.tl.querySelectorAll('[data-chmo]')[0]); await nghi();
  la('đường ngoài mở thẻ mới', [d.ve.mo_tab, d.ve.href], [['https://maps.google.com/?q=1'], []]);

  console.log('\n' + dat + ' ca đạt, ' + hong + ' ca hỏng.');
  process.exit(hong ? 1 : 0);
})().catch(function (e) { console.error(e); process.exit(1); });
