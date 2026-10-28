/* Ca kiểm HÀNH VI v619 (Codex 4402066952 trên 88fff67c): link trong tin Zalo
 * phải đưa tới đúng màn, đúng phiếu, kể cả khi nhân viên chưa đăng nhập.
 *
 * Chuỗi thật Codex nêu: mở /hang-chuyen-ve-kho-toi?mo=PDC-2026-00602 khi chưa
 * đăng nhập. __boot thấy Guest nên reset(scrLogin); khung app đặt lại địa chỉ
 * thành /bep. Đăng nhập xong app tải lại location.pathname (lúc đó là /bep), nên
 * nhân viên về trang chủ, mất phiếu.
 *
 * Ca này CHẠY THẬT, theo đúng thứ tự trình duyệt nạp app:
 *   - khung app 01-khung-app.js (reset, render, đặt địa chỉ),
 *   - bảng đường dẫn và các hàm địa chỉ của 02-trang-chu.js (từ VGB_DUONG tới
 *     vgbMoTheoDiaChi), đọc địa chỉ lúc nạp,
 *   - đoạn khởi động màn Hàng chuyển về kho tôi của 03-kho-chung-tu.js (đọc ?mo),
 *   - màn đăng nhập thật scrLogin của 06-nhap-kho-kiem-ke.js,
 *   - khởi động thật của 12-van-don.js (APPVER, hardNav, whoAmI, __boot).
 * Bản giả: máy chủ (fetch), trang chủ, vgbGo (chỉ ghi khoá màn sẽ mở). Lần nạp
 * thứ hai dựng lại từ ĐÚNG địa chỉ mà lần một gọi location.replace, giống
 * trình duyệt tải lại trang; sessionStorage giữ nguyên như cùng một thẻ.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/dang_nhap_giu_dich_619.js
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
  var h = layHam(src.slice(a), cuoiHam);
  var b = src.indexOf(h, a);
  return src.slice(a, b + h.length);
}
var KHUNG = doc('01-khung-app.js');
var TC = doc('02-trang-chu.js');
var KHO = doc('03-kho-chung-tu.js');
var NK = doc('06-nhap-kho-kiem-ke.js');
var VD = doc('12-van-don.js');

var DIA_CHI = doan(TC, 'var VGB_DUONG = {', 'vgbMoTheoDiaChi');
var KHOI_HVK = (function () {
  var a = KHO.indexOf('var HVK = {'), b = KHO.indexOf('} catch (eHvk) { }', a);
  if (a < 0 || b < 0) throw new Error('Khong thay doan khoi dong HVK');
  return KHO.slice(a, b + '} catch (eHvk) { }'.length);
})();
var KHOI_DONG = doan(VD, 'var APPVER =', '__boot');

var dat = 0, hong = 0;
function la(nhan, duoc, mong) {
  var a = JSON.stringify(duoc), b = JSON.stringify(mong);
  if (a === b) { dat++; console.log('  DAT   ' + nhan); }
  else { hong++; console.log('  HONG  ' + nhan + '\n        duoc ' + a + '\n        mong ' + b); }
}
async function nghi() { for (var i = 0; i < 20; i++) await new Promise(function (r) { setImmediate(r); }); }

function khoMoi() {
  var m = {};
  return {
    getItem: function (k) { return Object.prototype.hasOwnProperty.call(m, k) ? m[k] : null; },
    setItem: function (k, v) { m[k] = String(v); },
    removeItem: function (k) { delete m[k]; },
    _m: m,
  };
}

/* Nạp app ở một địa chỉ. `nguoi` là người máy chủ trả về (Guest nếu chưa đăng nhập). */
function napApp(diaChi, phien, nguoi) {
  var u = new URL('https://app.thevagabondpatisserie.com' + diaChi);
  var tl = dg.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var ve = { replace: [], mo: [], home: 0 };
  var loc = {
    pathname: u.pathname, search: u.search, hash: '', hostname: u.hostname,
    get href() { return 'https://' + u.hostname + this.pathname + this.search; },
    replace: function (x) { ve.replace.push(String(x)); },
  };
  function datDiaChi(x) {
    if (x == null) return;
    var v = new URL(String(x), 'https://' + u.hostname);
    loc.pathname = v.pathname; loc.search = v.search;
  }
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseInt: parseInt, parseFloat: parseFloat, isNaN: isNaN,
    Date: Date, URL: URL, URLSearchParams: URLSearchParams,
    document: tl, location: loc, sessionStorage: phien, localStorage: khoMoi(),
    frappe: { session: { user: nguoi === 'Guest' ? 'Guest' : nguoi } },
    history: {
      state: null,
      replaceState: function (st, t, x) { this.state = st; datDiaChi(x); },
      pushState: function (st, t, x) { this.state = st; datDiaChi(x); },
      back: function () {},
    },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { return 0; }, clearTimeout: function () {},
    fetch: async function (url) {
      if (url.indexOf('get_logged_user') >= 0) return { ok: true, status: 200, json: async function () { return { message: nguoi }; } };
      if (url === '/api/method/login') return { ok: true, status: 200, json: async function () { return {}; } };
      throw new Error('mang la ' + url);
    },
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast() {}', 'function sheet() {}', 'function dSkin() {}', 'function busy() {}', 'function syncUser() {}',
    'function shortWh(x) { return String(x || ""); }', 'function inNapJs() { return Promise.resolve(); }',
    'function confirmSheet() { return Promise.resolve(true); }', 'function pwaXinQuyenThongBao() {}',
    'var APPNAME = "Vagabond";',
    'async function scrHome() { __ve.home++; frame(APPNAME, "<div>trang chu</div>"); }',
    'function vgbGo(k) { __ve.mo.push(k); }',
  ].join('\n'), Object.assign(g, { __ve: ve }));
  vm.runInContext(KHUNG, g);
  vm.runInContext(DIA_CHI, g);
  vm.runInContext(KHOI_HVK + '\nthis.HVK = HVK;', g);
  vm.runInContext(layHam(NK, 'scrLogin'), g);
  vm.runInContext(KHOI_DONG, g);
  return { g: g, tl: tl, ve: ve, loc: loc };
}

/* Đúng thao tác của nhân viên trên màn đăng nhập: gõ hai ô rồi bấm nút. */
async function dangNhap(app) {
  app.tl.getElementById('lgU').value = 'kien@vagabond.vn';
  app.tl.getElementById('lgP').value = 'mat-khau-thu';
  await app.tl.getElementById('lgGo').onclick();
  await nghi();
  return app.ve.replace[app.ve.replace.length - 1] || '';
}

/* Trình duyệt tải lại: bỏ phần gốc máy, giữ đường và tham số. */
function duongCua(x) { var v = new URL(x, 'https://app.thevagabondpatisserie.com'); return v.pathname + v.search; }

(async function () {
  console.log('v619 hành vi: link tin Zalo qua bước đăng nhập vẫn tới đúng màn, đúng phiếu');

  // Ca Codex: chưa đăng nhập, bấm link phiếu điều chuyển trong tin Zalo.
  var phien = khoMoi();
  var a = napApp('/hang-chuyen-ve-kho-toi?mo=PDC-2026-00602', phien, 'Guest');
  await a.g.__boot(); await nghi();
  la('chưa đăng nhập thì hiện màn đăng nhập', !!a.tl.getElementById('lgGo'), true);
  var toi = await dangNhap(a);
  var d = duongCua(toi);
  la('đăng nhập xong tải lại đúng màn trong tin', d.split('?')[0], '/hang-chuyen-ve-kho-toi');
  la('giữ mã phiếu trong địa chỉ tải lại', new URL(toi, 'https://x').searchParams.get('mo'), 'PDC-2026-00602');
  var b = napApp(d, phien, 'kien@vagabond.vn');
  await b.g.__boot(); await nghi();
  la('lần nạp sau đăng nhập mở màn Hàng chuyển về kho tôi', b.ve.mo, ['NHANDC']);
  la('màn đó mở thẳng đúng phiếu trong tin', [b.g.HVK.mo, b.g.HVK.ngay], ['PDC-2026-00602', 30]);
  la('đích đã dùng thì xoá, không kéo theo lần đăng nhập sau', phien.getItem('vgb_dich'), null);

  // Link màn khác (không có mã phiếu) cũng giữ được màn.
  var p2 = khoMoi();
  var c = napApp('/xuat-huy', p2, 'Guest');
  await c.g.__boot(); await nghi();
  la('link màn Xuất huỷ qua đăng nhập vẫn về Xuất huỷ', duongCua(await dangNhap(c)).split('?')[0], '/xuat-huy');

  // Mở app bình thường ở trang chủ: như cũ.
  var p3 = khoMoi();
  var e = napApp('/bep', p3, 'Guest');
  await e.g.__boot(); await nghi();
  la('mở trang chủ rồi đăng nhập vẫn về trang chủ', duongCua(await dangNhap(e)).split('?')[0], '/bep');

  // Đang dùng màn Sản xuất thì phiên hết (dòng reset(scrLogin) của sessionGone).
  var p4 = khoMoi();
  var f = napApp('/bep', p4, 'kien@vagabond.vn');
  await f.g.__boot(); await nghi();
  f.g.history.replaceState(null, '', '/san-xuat');
  f.g.reset(f.g.scrLogin); await nghi();
  la('phiên hết giữa chừng: đăng nhập lại về đúng màn đang dùng', duongCua(await dangNhap(f)).split('?')[0], '/san-xuat');

  // Giá trị lạ trong kho phiên (không do app ghi) không được dẫn đi đâu.
  for (var x of ['//la.example.com/bep', 'https://la.example.com/', '/app/stock-entry/PDC-1', '/khong-co-man-nay', 'javascript:alert(1)']) {
    var p5 = khoMoi();
    var k = napApp('/bep', p5, 'Guest');
    await k.g.__boot(); await nghi();
    p5.setItem('vgb_dich', x);
    la('bỏ đích lạ ' + JSON.stringify(x), duongCua(await dangNhap(k)).split('?')[0], '/bep');
  }

  console.log('\n' + dat + ' ca đạt, ' + hong + ' ca hỏng.');
  process.exit(hong ? 1 : 0);
})().catch(function (e) { console.error(e); process.exit(1); });
