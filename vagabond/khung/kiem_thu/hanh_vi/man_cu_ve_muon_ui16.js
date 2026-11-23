/* Codex kiểm v685, UI16 (loại 8, liên quan loại 4): màn async về muộn vẽ đè màn
   đang đứng.

   Cách Codex làm lại trên site: mạng 3G, Bán hàng -> Đơn còn treo -> bấm Quay lại
   ngay lúc "Đang soát đơn chưa ghi sổ..." -> màn Bán hàng hiện -> lời đáp Đơn còn
   treo về và vẽ đè: tiêu đề, nội dung đổi thành Đơn còn treo, địa chỉ vẫn là phân
   hệ Bán hàng.

   Ca này chạy THẬT khung điều hướng (go, back, render, vgbManNay của phần 01) và
   THÂN THẬT của từng màn async thuộc Bán hàng và Giao hàng, tách khỏi tệp nguồn.
   Mọi tên khác màn dùng (hàm vẽ phụ, biến bộ lọc) được thay bằng một bản giả trơ,
   để màn chạy hết đường mà không cần dựng cả app. Máy chủ giả GIỮ mọi lời đáp tới
   khi ca cho trả. Với mỗi màn, ba cảnh:
     1. Mở màn, sang màn khác (Đối soát COD) trước khi lời đáp về, rồi trả lời đáp.
     2. Mở màn, bấm Quay lại trước khi lời đáp về, rồi trả lời đáp.
     3. Như cảnh 1 nhưng máy chủ trả LỖI (nhánh lỗi cũng không được vẽ đè).
   Chốt: sau khi trả lời đáp, không có lần vẽ nào mang tiêu đề khác màn đang đứng,
   và chồng màn giữ đúng màn đang đứng.
   Thêm hai cảnh của Đơn còn treo: đổi kỳ (bấm chip, vẽ lại chính màn) khi hai lời
   đáp về ngược thứ tự, và gọi thẳng màn hai lần không qua điều hướng.

   Chạy:  node vagabond/khung/kiem_thu/hanh_vi/man_cu_ve_muon_ui16.js
   Chạy trên mã cũ để thấy đỏ:  NGUON_BEP=/tmp/bep-main node ... (thư mục chứa các
   phần bep/ của main). */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = process.env.NGUON_BEP || path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');

/* Màn async của phân hệ Bán hàng và Giao hàng: tên hàm và tệp chứa. */
const MAN = [
  ['scrPosChonQuay', '09-tinh-tien-quay.js'], ['scrOtp', '10-bill-quay.js'],
  ['scrMuaVuDs', '11-khach-ca-hop-dong.js'], ['scrCongNo', '11-khach-ca-hop-dong.js'],
  ['scrVanDon', '12-van-don.js'], ['scrVdCod', '12-van-don.js'], ['scrVdChiPhi', '12-van-don.js'], ['scrVdPhiApp', '12-van-don.js'],
  ['scrKhuyenMai', '13-khuyen-mai.js'], ['scrDonTreo', '18-doi-chieu-may-in.js'], ['scrCanhBaoTT', '21-ke-toan-khac.js'],
  ['scrHopDongHub', '22-bao-gia.js'], ['scrBntDs', '39-bien-nhan-tien.js'], ['scrPhieuHoanHuy', '40-phieu-hoan-huy.js'],
  ['scrDuyetTang', '41-duyet-don-tang.js'], ['scrSoDuTraTruoc', '55-so-du-tra-truoc.js'], ['scrDoiSoatCk', '56-doi-soat-ck.js'],
  ['scrDatBan', '57-dat-ban.js'], ['scrDonDatTruoc', '63-don-dat-truoc.js'], ['scrDonSiWeb', '64-banh-si.js'],
  ['scrKhachSiWeb', '64-banh-si.js'], ['scrGmbInQr', '66-goi-mon-tai-ban.js'], ['scrBienTapMenu', '68-bien-tap-menu.js'],
  ['scrKhachSuKien', '74-khach-su-kien.js'], ['scrDonGiaoQuay', '76-don-giao-quay.js']
];

/* Bộ nhớ đệm danh mục, cấu hình dùng chung (không thuộc riêng lượt mở nào): lời
   đáp về muộn vẫn được giữ, vì đó là cùng một dữ liệu cho lần mở sau. */
const GHI_BO_NHO = [];

function layHam(src, ten) {
  const dau = src.search(new RegExp('\\n(?:async )?function ' + ten + '\\s*\\('));
  if (dau < 0) throw new Error('Không thấy hàm ' + ten);
  let i = src.indexOf('{', dau), sau = 0, q = null;
  for (let j = i; j < src.length; j++) {
    const c = src[j];
    if (q) { if (c === '\\') { j++; continue; } if (c === q) q = null; continue; }
    if (c === '\'' || c === '"' || c === '`') { q = c; continue; }
    if (c === '{') sau++;
    else if (c === '}') { sau--; if (!sau) return src.slice(dau + 1, j + 1); }
  }
  throw new Error('Hàm ' + ten + ' không đóng ngoặc');
}

async function nghi() { for (let i = 0; i < 40; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

function appMoi() {
  const tl = dom.taiLieuGia();
  tl.addEventListener = () => {};
  if (!tl.head) tl.head = tl.createElement('head');
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  const may = { cho: [], loi: false };
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, Date, parseFloat, parseInt, isNaN,
    document: tl, frappe: { session: { user: 'thu@vagabond.invalid' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {} };
  g.window = g; g.localStorage = { getItem: () => null, setItem() {}, removeItem() {} }; g.sessionStorage = g.localStorage; g.addEventListener = () => {};
  vm.createContext(g);
  /* Máy chủ giả: mọi lời gọi đều chờ tới khi ca cho trả; may.loi thì trả lỗi. */
  /* Lời đáp thành công là bản giả trơ TRO (dựng ở dưới): màn đọc trường nào
     cũng được, để đi tới lần vẽ thật. */
  g.__api = () => new Promise((r, j) => may.cho.push(() => (may.loi ? j(new Error('Máy chủ lỗi thử')) : r(g.troMoi()))));
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'var VE = [];',
    'function h(s) { return String(s == null ? "" : s); }',
    'function toast() {} function busy() {} function dSkin() {} function money(x) { return String(x); }',
    'function today() { return "2026-11-23"; } function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __api(m, a); }',
    'function getList() { return __api(); } function nenDemDanhSach() { return __api(); }'
  ].join('\n'), g);
  vm.runInContext(doc('01-khung-app.js'), g);
  /* Ghi lại mọi lần vẽ kèm màn đang đứng đầu chồng lúc vẽ; vẽ thật vẫn chạy. */
  vm.runInContext([
    'var __frameThat = frame;',
    'frame = function (t, html, opt) { VE.push({ t: String(t), dau: S.stack[S.stack.length - 1] }); return __frameThat(t, "", opt); };',
    'getList = function () { return __api(); }; nenDemDanhSach = function () { return __api(); };',
    'loadMasters = function () { return Promise.resolve(); };',
    'S.user = "thu@vagabond.invalid"; S.wh = ["Kho"]; S.roles = ["System Manager"];',
    /* Bản giả trơ cho mọi tên màn dùng mà ca không dựng: gọi được, đọc thuộc
       tính được, nối chuỗi ra rỗng, không phải lời hứa. */
    'var TRO_XU = { get: function (t, k) { if (k === "then") return undefined; if (k === Symbol.toPrimitive) return function () { return ""; }; if (k === "length") return 0; if (k === Symbol.iterator) return [][Symbol.iterator]; return TRO; }, apply: function () { return TRO; }, construct: function () { return TRO; } };',
    'var TRO = new Proxy(function () {}, TRO_XU);',
    /* Mỗi lời đáp là một bản giả RIÊNG, để phân biệt lời đáp nào đã được ghi. */
    'globalThis.troMoi = function () { return new Proxy(function () {}, TRO_XU); };',
    'var GHI = {};',
    'globalThis.TRO = TRO;',
    'var THIEU = new Proxy({}, { has: function (t, k) { return typeof k === "string" && !(k in globalThis); }, get: function (t, k) { if (k === Symbol.unscopables) return undefined; return Object.prototype.hasOwnProperty.call(GHI, k) ? GHI[k] : TRO; }, set: function (t, k, v) { GHI[k] = v; return true; } });'
  ].join('\n'), g);
  const man = {};
  for (const [ten, tep] of MAN) {
    const than = layHam(doc(tep), ten);
    /* Biểu thức hàm có tên: hàm thấy chính nó (vgbManNay(scrDonTreo)). */
    man[ten] = vm.runInContext('(function () { with (THIEU) { return (' + than + '); } })()', g);
  }
  /* Vài tên phải là thật để màn đi tới chỗ chờ máy chủ: cấu hình bán hàng đọc
     qua máy chủ; Biên tập menu chưa có menu trong bộ nhớ và người mở có quyền. */
  vm.runInContext('GHI.cfgBanHang = function () { return __api(); }; GHI.BTM = null; GHI.coQuyenBtm = function () { return true; };', g);
  const khac = vm.runInContext('(function manKhac() { frame("Đối soát COD", "<div></div>"); })', g);
  const cha = vm.runInContext('(function manCha() { frame("Bán hàng", "<div></div>"); })', g);
  return {
    g, may, man, khac, cha,
    async tha() { for (let i = 0; i < 20 && may.cho.length; i++) { const c = may.cho.splice(0); c.forEach(f => f()); await nghi(); } },
    ve() { return vm.runInContext('VE', g); },
    /* Ảnh chụp các biến của màn (tên ngoài phần 01) để bắt lời đáp cũ ghi đè. */
    bien() { return Object.assign({}, vm.runInContext('GHI', g)); },
    dau() { return vm.runInContext('S.stack[S.stack.length - 1]', g); }
  };
}

/* Màn nổ ở đâu đó sau lần vẽ (bản giả trơ không đủ cho mọi phép) thì bỏ qua:
   ca chỉ chốt chuyện vẽ đè, đếm bằng VE. Lỗi nổ được ghi để soi khi cần. */
const NO = [];
process.on('unhandledRejection', e => NO.push(String(e && e.message)));
if (process.env.CHI_TIET) process.on('exit', () => console.log('Lỗi nổ sau lần vẽ (bỏ qua): ' + NO.slice(0, 12).join(' | ')));

let dat = 0, hong = 0;
const hongDs = [];
async function ca(ten, f) {
  try { await f(); dat++; }
  catch (e) { hong++; hongDs.push(ten + '\n        ' + (e && e.message)); }
}

(async function () {
  console.log('\nUI16: màn async về muộn không vẽ đè màn đang đứng (' + MAN.length + ' màn Bán hàng, Giao hàng)\n');
  for (const [ten] of MAN) {
    await ca(ten + ': sang màn khác trước khi lời đáp về', async () => {
      const a = appMoi();
      a.g.reset(a.cha); await nghi();
      a.g.go(a.man[ten]); await nghi();
      const moc = a.ve().length;
      a.g.go(a.khac); await nghi();
      const truoc = a.bien();
      await a.tha();
      const sau = a.ve().slice(moc + 1).filter(v => v.t !== 'Đối soát COD');
      assert.equal(sau.length, 0, 'màn đã rời vẫn vẽ: ' + sau.map(v => v.t).join(', '));
      assert.strictEqual(a.dau(), a.khac, 'chồng màn không còn đứng ở màn mới');
      const ghiDe = Object.keys(a.bien()).filter(k => a.bien()[k] !== truoc[k] && GHI_BO_NHO.indexOf(k) < 0);
      assert.equal(ghiDe.length, 0, 'lời đáp của màn đã rời vẫn ghi đè: ' + ghiDe.join(', '));
    });
    await ca(ten + ': bấm Quay lại trước khi lời đáp về', async () => {
      const a = appMoi();
      a.g.reset(a.cha); await nghi();
      a.g.go(a.man[ten]); await nghi();
      a.g.back(); await nghi();
      const moc = a.ve().length;
      await a.tha();
      const sau = a.ve().slice(moc).filter(v => v.t !== 'Bán hàng');
      assert.equal(sau.length, 0, 'màn đã lùi vẫn vẽ đè màn cha: ' + sau.map(v => v.t).join(', '));
    });
    await ca(ten + ': máy chủ trả lỗi sau khi đã sang màn khác', async () => {
      const a = appMoi(); a.may.loi = true;
      a.g.reset(a.cha); await nghi();
      a.g.go(a.man[ten]); await nghi();
      const moc = a.ve().length;
      a.g.go(a.khac); await nghi();
      await a.tha();
      const sau = a.ve().slice(moc + 1).filter(v => v.t !== 'Đối soát COD');
      assert.equal(sau.length, 0, 'nhánh lỗi của màn đã rời vẫn vẽ: ' + sau.map(v => v.t).join(', '));
    });
  }

  await ca('Đơn còn treo: bấm chip đổi kỳ, hai lời đáp về ngược thứ tự, chỉ lượt mới vẽ', async () => {
    const a = appMoi();
    a.g.reset(a.cha); await nghi();
    a.g.go(a.man.scrDonTreo); await nghi();
    a.g.go(a.man.scrDonTreo, true); await nghi();
    const moc = a.ve().length;
    const c = a.may.cho.splice(0);
    assert.equal(c.length, 2, 'mong hai lời gọi đang chờ, có ' + c.length);
    c[1](); await nghi();
    const sauMoi = a.ve().length;
    c[0](); await nghi(); await a.tha();
    assert.equal(sauMoi - moc, 1, 'lượt mới không vẽ');
    assert.equal(a.ve().length, sauMoi, 'lượt cũ về sau vẫn vẽ đè lượt mới');
  });

  await ca('Đơn giao quầy: gọi thẳng màn hai lần không qua điều hướng, lượt cũ về sau không ghi đè', async () => {
    const a = appMoi();
    a.g.reset(a.cha); await nghi();
    a.g.go(function () { a.man.scrDonGiaoQuay(); }); await nghi();
    a.man.scrDonGiaoQuay(); await nghi();
    const c = a.may.cho.splice(0);
    assert.equal(c.length, 2, 'mong hai lời gọi đang chờ, có ' + c.length);
    c[1](); await nghi();
    const sauMoi = vm.runInContext('GHI.DQ', a.g);
    c[0](); await nghi();
    assert.strictEqual(vm.runInContext('GHI.DQ', a.g), sauMoi, 'lời đáp cũ ghi đè danh sách của lượt mới');
  });

  hongDs.forEach(s => console.log('  HỎNG  ' + s));
  console.log('\n' + dat + ' đạt, ' + hong + ' hỏng');
  process.exit(hong ? 1 : 0);
})();
