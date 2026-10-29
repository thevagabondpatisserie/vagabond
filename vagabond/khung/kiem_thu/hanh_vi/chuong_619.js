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
  ], co_phong_ban: 1, so_ngay: 14, con_nua: 1, moc_moi: '2026-10-28 08:00:05.000001',
};
/* Codex 4407978626: trang sau mở đầu bằng bản sao (gửi nhóm khác) của tin cuối trang trước. */
var TRANG2 = { ds: [{ ten: 't3b', ma_tin: 'bh_dat_ban', tieu_de: '✅ VIỆC CẦN LÀM: Đặt bàn mới', than: '- 4 khách', link: '',
      luc: '2026-10-26 09:59:58.000001', moi: 0 }, { ten: 't4', ma_tin: 'bh_dat_ban', tieu_de: 'Tin cũ hơn', than: '', link: '', luc: '2026-10-20 10:00:00.000001', moi: 0 }],
  co_phong_ban: 1, so_ngay: 14, con_nua: 0, moc_moi: '2026-10-20 10:00:00.000001' };

function napApp(nguoi, traTin, trangSau) {
  var tl = dg.taiLieuGia();
  tl.head = new dg.ElementGia('head');
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var ve = { api: [], ts: [], mo: [], href: [], mo_tab: [] };
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
      ve.api.push(m); ve.ts.push([m, JSON.stringify(ts || {})]);
      if (m === 'vagabond.chuong.dem') return Promise.resolve({ viec: 3, tin: 2, tong: 5 });
      if (m === 'vagabond.chuong.thong_bao') return Promise.resolve(JSON.parse(JSON.stringify(ts && ts.truoc ? (trangSau ? trangSau(ts.truoc) : TRANG2) : (traTin || TIN))));
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
  la('số đỏ của chuông chữ từ 13 trở lên', (a.tl.getElementById('vgb').innerHTML.match(/id="vgbChuongSo" style="[^"]*font-size:\s*([\d.]+)px/) || [])[1] >= 13, true);
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
  // Codex 4408181761: AGENTS.md 2b.13, chữ tối thiểu 13 điểm trên màn mới (cả số đỏ của chuông).
  var coChu = function () {
    var html = a.tl.getElementById('vgb').innerHTML, ra = [], m, re = /font-size:\s*([\d.]+)px/g;
    while ((m = re.exec(html))) ra.push(+m[1]);
    return ra;
  };
  la('màn có ghi cỡ chữ (điều kiện của ca)', coChu().length > 3, true);
  la('mọi cỡ chữ trên màn Chuông từ 13 trở lên', coChu().filter(function (x) { return x < 13; }), []);
  la('hai nút Mở (tin không đường thì không có)', a.tl.querySelectorAll('[data-chmo]').length, 2);
  la('mở thẻ là đánh dấu đã đọc, chỉ tới tin mới nhất đã hiện', a.ve.ts.filter(function (x) { return x[0] === 'vagabond.chuong.da_xem'; }),
    [['vagabond.chuong.da_xem', JSON.stringify({ den: '2026-10-28 08:00:05.000001' })]]);
  // Codex 4404477923: còn tin cũ hơn thì có nút tải thêm, không cắt mất.
  var cuHon = a.tl.getElementById('chCuHon');
  la('còn tin cũ hơn thì có nút Xem tin cũ hơn', !!cuHon, true);
  await cuHon.onclick(); await nghi();
  la('bấm là hỏi trang trước tin cuối đang hiện', a.ve.ts.filter(function (x) { return x[0] === 'vagabond.chuong.thong_bao'; }).pop(),
    ['vagabond.chuong.thong_bao', JSON.stringify({ truoc: '2026-10-26 10:00:00.000001' })]);
  la('tin gửi nhiều nhóm nằm hai bên ranh trang chỉ hiện một lần', a.tl.getElementById('vgbBody').textContent.split('Đặt bàn mới').length - 1, 1);
  la('tin cũ hơn nối vào cuối, hết thì mất nút', [a.tl.querySelectorAll('[data-chi]').length,
    a.tl.getElementById('vgbBody').textContent.indexOf('Tin cũ hơn') >= 0, !!a.tl.getElementById('chCuHon')], [4, true, false]);
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

  // Codex 4408086813: trang sau chỉ toàn bản sao tin đã hiện. Màn gộp hết, nhưng mốc phải theo
  // máy chủ để lần bấm sau đi tiếp, không hỏi lại đúng trang cũ mãi.
  var mot = function (ten, luc) { return { ten: ten, ma_tin: 'bh_dat_ban', tieu_de: 'Tin ' + ten, than: '', link: '', luc: luc, moi: 0 }; };
  var hoi = [];
  var e = napApp('kt@vagabond.vn', { ds: [mot('a', '2026-10-28 10:00:00.000001'), mot('b', '2026-10-28 09:00:00.000001')],
    co_phong_ban: 1, so_ngay: 14, con_nua: 1, moc_moi: '2026-10-28 10:00:00.000001', tiep: '2026-10-28 09:00:00.000001' },
    function (truoc) {
      hoi.push(truoc);
      if (truoc === '2026-10-28 09:00:00.000001') return { ds: [mot('a', '2026-10-28 08:59:00.000001'), mot('b', '2026-10-28 08:58:00.000001')],
        con_nua: 1, tiep: '2026-10-28 08:58:00.000001' };
      return { ds: [mot('c', '2026-10-27 08:00:00.000001')], con_nua: 0, tiep: '2026-10-27 08:00:00.000001' };
    });
  await e.g.reset(e.g.scrHome); await nghi();
  bam(e, e.tl.getElementById('vgbChuong')); await nghi();
  await e.tl.getElementById('chCuHon').onclick(); await nghi();
  la('trang toàn bản sao: không thêm tin, vẫn còn nút', [e.tl.querySelectorAll('[data-chi]').length, !!e.tl.getElementById('chCuHon')], [2, true]);
  await e.tl.getElementById('chCuHon').onclick(); await nghi();
  la('lần bấm sau đi tiếp theo mốc máy chủ, tới được tin cũ hơn', [hoi, e.tl.querySelectorAll('[data-chi]').length, !!e.tl.getElementById('chCuHon')],
    [['2026-10-28 09:00:00.000001', '2026-10-28 08:58:00.000001'], 3, false]);

  console.log('\n' + dat + ' ca đạt, ' + hong + ' ca hỏng.');
  process.exit(hong ? 1 : 0);
})().catch(function (e) { console.error(e); process.exit(1); });
