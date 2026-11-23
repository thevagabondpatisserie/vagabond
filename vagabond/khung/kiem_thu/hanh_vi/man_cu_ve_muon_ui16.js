/* Codex kiểm v685, UI16 (loại 8, liên quan loại 4): màn async về muộn vẽ đè màn
   đang đứng.

   Cách Codex làm lại trên site: mạng 3G, Bán hàng -> Đơn còn treo -> bấm Quay lại
   ngay lúc "Đang soát đơn chưa ghi sổ..." -> màn Bán hàng hiện -> lời đáp Đơn còn
   treo về và vẽ đè: tiêu đề, nội dung đổi thành Đơn còn treo, địa chỉ vẫn là phân
   hệ Bán hàng.

   Ca này nạp NGUYÊN app_bep.js như trang /bep (khung điều hướng, màn, biến cấp
   tệp đều thật), chỉ thay cửa ra mạng rawCall bằng máy chủ giả GIỮ mọi lời đáp
   tới khi ca cho trả. Mỗi cảnh chốt màn ĐANG chờ máy chủ trước khi người dùng
   rời đi, và đọc biến thật của màn để bắt lời đáp cũ ghi đè (Codex #616). Với mỗi màn, ba cảnh:
     1. Mở màn, sang màn khác (Đối soát COD) trước khi lời đáp về, rồi trả lời đáp.
     2. Mở màn, bấm Quay lại trước khi lời đáp về, rồi trả lời đáp.
     3. Như cảnh 1 nhưng máy chủ trả LỖI (nhánh lỗi cũng không được vẽ đè).
   Chốt: sau khi trả lời đáp, không có lần vẽ nào mang tiêu đề khác màn đang đứng,
   và chồng màn giữ đúng màn đang đứng.
   Thêm hai cảnh của Đơn còn treo: đổi kỳ (bấm chip, vẽ lại chính màn) khi hai lời
   đáp về ngược thứ tự, và gọi thẳng màn hai lần không qua điều hướng.

   Chạy:  node vagabond/khung/kiem_thu/hanh_vi/man_cu_ve_muon_ui16.js
   Chạy trên mã cũ để thấy đỏ:  NGUON_APP=/tmp/app_bep_main.js node ... (app_bep.js
   ghép của main). */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
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
const GHI_BO_NHO = [
  'vtShipper', 'vtDiem',  /* danh sách shipper, điểm lấy hàng (Vận đơn) */
  'kmDm'                  /* danh mục hạng khách, nhóm món, quầy (Khuyến mãi) */
];
/* Lời gọi nền của vỏ app (chuông đếm việc, gọi trong frame), không phải của màn. */
const NEN = ['vagabond.chuong.dem'];
function choCuaMan(a) { return a.may.cho.filter(f => NEN.indexOf(f.m) < 0).length; }
/* Lấy riêng các lời gọi đang chờ của một hàm máy chủ, theo thứ tự gọi. */
function layCho(a, m) {
  const c = a.may.cho.filter(f => f.m === m);
  const con = a.may.cho.filter(f => f.m !== m);
  a.may.cho.splice(0, a.may.cho.length, ...con);
  return c;
}

/* Bộ chọn mà DOM giả không hiểu (meta[name=viewport], input[type="date"]) thì
   coi như không có phần tử, CHỈ trong ca này: ca chốt chuyện vẽ đè và biến của
   màn, không chốt phần tử con. Lỗi khác của DOM giả vẫn nổ như cũ. */
{
  const qsa = dom.ElementGia.prototype.querySelectorAll;
  dom.ElementGia.prototype.querySelectorAll = function (q) {
    try { return qsa.call(this, q); } catch (e) { if (/khong hieu/.test(e.message)) return []; throw e; }
  };
}

async function nghi() { for (let i = 0; i < 40; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

/* Codex #616 vòng 2 (P2): nạp từng tệp trong một hàm bọc riêng thì biến cấp tệp
   (DQ, MV, BTM...) nằm trong bao đóng, ca không đọc được trạng thái thật và hai
   lần đọc đều ra undefined. Nay nạp NGUYÊN app_bep.js như trang /bep nạp nó, chèn
   một cửa eval ngay trong vỏ app (cách của ban_soan_do_533) để đọc, đặt đúng biến
   thật. Chỉ thay một chỗ: rawCall, cửa ra mạng duy nhất, thành máy chủ giả GIỮ
   lời đáp. api(), getList(), loadMasters(), cfgBanHang()... đều là mã thật. */
const APP = process.env.NGUON_APP || path.resolve(__dirname, '../../../public/js/app_bep.js');
let KICH = null;
function kichBan() {
  if (KICH) return KICH;
  let src = fs.readFileSync(APP, 'utf8');
  const k = src.lastIndexOf('\n})();');
  src = src.slice(0, k) + '\nwindow.__k = { chay: function (c) { return eval(c); } };' + src.slice(k);
  KICH = new vm.Script(src, { filename: 'app_bep.js' });
  return KICH;
}
/* Tên biến cấp tệp của từng màn: ảnh chụp trước, sau khi trả lời đáp để bắt lời
   đáp cũ ghi đè (cả thuộc tính một tầng, như MV.ds). */
const BIEN = {};
for (const [ten, tep] of MAN) {
  const ds = [];
  for (const m of doc(tep).matchAll(/^(?:var|let)\s+([^\n]*)/gm)) {
    for (const n of m[1].replace(/(['"`])(?:\\.|(?!\1).)*\1/g, '""').replace(/[[{(][^\]})]*[\]})]/g, '0')
      .matchAll(/(?:^|,)\s*([A-Za-z_$][\w$]*)\s*(?==|,|;|$)/g)) ds.push(n[1]);
  }
  BIEN[ten] = ds;
}

function appMoi() {
  const tl = dom.taiLieuGia();
  tl.addEventListener = () => {}; tl.readyState = 'loading';
  if (!tl.head) tl.head = tl.createElement('head');
  if (!tl.documentElement) tl.documentElement = tl.createElement('html');
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  const may = { cho: [], loi: false, goi: [] };
  const kho = () => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, removeItem: k => { delete m[k]; } }; };
  const g = {
    console: { log() {}, warn() {}, error() {}, info() {} }, document: tl,
    navigator: { userAgent: 'node', onLine: true },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', origin: 'https://app.x', replace() {}, reload() {} },
    history: { pushState() {}, replaceState() {}, back() {}, state: null },
    frappe: { session: { user: 'thu@vagabond.invalid' }, csrf_token: 'x' },
    localStorage: kho(), sessionStorage: kho(),
    fetch: () => new Promise(() => {}),
    setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {},
    requestAnimationFrame: f => f(), matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
    addEventListener() {}, removeEventListener() {}, getComputedStyle: () => ({}),
    URL, URLSearchParams, Blob, Intl, TextEncoder
  };
  g.window = g; g.self = g;
  /* Lời đáp thành công là một bản giả trơ RIÊNG mỗi lần (đọc trường nào cũng
     được, phân biệt được lời đáp nào đã được lưu); may.loi thì trả lỗi. */
  g.__api = (m) => new Promise((r, j) => { may.goi.push(m); const f = () => (may.loi ? j(new Error('Máy chủ lỗi thử')) : r(g.troMoi())); f.m = m; may.cho.push(f); });
  vm.createContext(g);
  kichBan().runInContext(g);
  const chay = c => g.__k.chay(c);
  chay([
    'window.VE = [];',
    'frame = (function (f) { return function (t, html, opt) { window.VE.push({ t: String(t), dau: S.stack[S.stack.length - 1] }); return f(t, html, opt); }; })(frame);',
    'rawCall = function (m, a) { return window.__api(m, a); };',
    'S.user = "thu@vagabond.invalid"; S.wh = ["Kho"]; S.roles = ["System Manager"];',
    'window.troMoi = (function () { var XU = { get: function (t, k) { if (k === "then") return undefined; if (k === Symbol.toPrimitive) return function () { return ""; }; if (k === "length") return 0; if (k === Symbol.iterator) return [][Symbol.iterator]; return new Proxy(function () {}, XU); }, apply: function () { return new Proxy(function () {}, XU); }, construct: function () { return new Proxy(function () {}, XU); } }; return function () { return new Proxy(function () {}, XU); }; })();'
  ].join('\n'));
  const man = {};
  for (const [ten] of MAN) man[ten] = chay(ten);
  const khac = chay('(function manKhac() { frame("Đối soát COD", "<div></div>"); })');
  const cha = chay('(function manCha() { frame("Bán hàng", "<div></div>"); })');
  return {
    g, may, man, khac, cha, chay,
    go: (f, x) => chay('go')(f, x), back: () => chay('back')(), reset: f => chay('reset')(f),
    async tha() { for (let i = 0; i < 30 && may.cho.length; i++) { const c = may.cho.splice(0); c.forEach(f => f()); await nghi(); } },
    ve() { return chay('window.VE'); },
    /* Ảnh chụp biến cấp tệp THẬT của màn và thuộc tính một tầng của chúng. */
    bien(ten) {
      const o = {};
      for (const b of BIEN[ten]) {
        let v; try { v = chay(b); } catch (e) { continue; }
        o[b] = v;
        if (v && typeof v === 'object' && !Array.isArray(v)) for (const k of Object.keys(v)) o[b + '.' + k] = v[k];
      }
      return o;
    },
    dau() { return chay('S.stack[S.stack.length - 1]'); }
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
      a.reset(a.cha); await nghi();
      a.go(a.man[ten]); await nghi();
      assert(choCuaMan(a) > 0, 'màn không chờ máy chủ nên ca không kiểm được gì (đi nhánh bộ nhớ hay nổ trước khi gọi)');
      const moc = a.ve().length;
      a.go(a.khac); await nghi();
      const truoc = a.bien(ten);
      await a.tha();
      const sau = a.ve().slice(moc + 1).filter(v => v.t !== 'Đối soát COD');
      assert.equal(sau.length, 0, 'màn đã rời vẫn vẽ: ' + sau.map(v => v.t).join(', '));
      assert.strictEqual(a.dau(), a.khac, 'chồng màn không còn đứng ở màn mới');
      const sauB = a.bien(ten);
      const ghiDe = Object.keys(sauB).filter(k => sauB[k] !== truoc[k] && GHI_BO_NHO.indexOf(k) < 0);
      assert.equal(ghiDe.length, 0, 'lời đáp của màn đã rời vẫn ghi đè: ' + ghiDe.join(', '));
    });
    await ca(ten + ': bấm Quay lại trước khi lời đáp về', async () => {
      const a = appMoi();
      a.reset(a.cha); await nghi();
      a.go(a.man[ten]); await nghi();
      assert(choCuaMan(a) > 0, 'màn không chờ máy chủ nên ca không kiểm được gì (đi nhánh bộ nhớ hay nổ trước khi gọi)');
      a.back(); await nghi();
      const moc = a.ve().length;
      await a.tha();
      const sau = a.ve().slice(moc).filter(v => v.t !== 'Bán hàng');
      assert.equal(sau.length, 0, 'màn đã lùi vẫn vẽ đè màn cha: ' + sau.map(v => v.t).join(', '));
    });
    await ca(ten + ': máy chủ trả lỗi sau khi đã sang màn khác', async () => {
      const a = appMoi(); a.may.loi = true;
      a.reset(a.cha); await nghi();
      a.go(a.man[ten]); await nghi();
      assert(choCuaMan(a) > 0, 'màn không chờ máy chủ nên ca không kiểm được gì (đi nhánh bộ nhớ hay nổ trước khi gọi)');
      const moc = a.ve().length;
      a.go(a.khac); await nghi();
      await a.tha();
      const sau = a.ve().slice(moc + 1).filter(v => v.t !== 'Đối soát COD');
      assert.equal(sau.length, 0, 'nhánh lỗi của màn đã rời vẫn vẽ: ' + sau.map(v => v.t).join(', '));
    });
  }

  await ca('Đơn còn treo: bấm chip đổi kỳ, hai lời đáp về ngược thứ tự, chỉ lượt mới vẽ', async () => {
    const a = appMoi();
    a.reset(a.cha); await nghi();
    a.go(a.man.scrDonTreo); await nghi();
    a.go(a.man.scrDonTreo, true); await nghi();
    const moc = a.ve().length;
    const c = layCho(a, 'vagabond.ban_hang.don_treo');
    assert.equal(c.length, 2, 'mong hai lời gọi đang chờ, có ' + c.length + ': ' + a.may.goi.join(', '));
    c[1](); await nghi();
    const sauMoi = a.ve().length;
    c[0](); await nghi(); await a.tha();
    assert.equal(sauMoi - moc, 1, 'lượt mới không vẽ');
    assert.equal(a.ve().length, sauMoi, 'lượt cũ về sau vẫn vẽ đè lượt mới');
  });

  await ca('Đơn giao quầy: gọi thẳng màn hai lần không qua điều hướng, lượt cũ về sau không ghi đè', async () => {
    const a = appMoi();
    a.reset(a.cha); await nghi();
    a.go(function () { a.man.scrDonGiaoQuay(); }); await nghi();
    a.man.scrDonGiaoQuay(); await nghi();
    const c = layCho(a, 'vagabond.don_quay.danh_sach');
    assert.equal(c.length, 2, 'mong hai lời gọi đang chờ, có ' + c.length + ': ' + a.may.goi.join(', '));
    const dau = a.chay('DQ');
    c[1](); await nghi();
    const sauMoi = a.chay('DQ');
    assert.notStrictEqual(sauMoi, dau, 'lời đáp của lượt mới chưa được lưu vào DQ, ca không đọc được trạng thái thật');
    assert(sauMoi != null, 'DQ của lượt mới rỗng');
    c[0](); await nghi();
    assert.strictEqual(a.chay('DQ'), sauMoi, 'lời đáp cũ ghi đè danh sách của lượt mới');
  });

  hongDs.forEach(s => console.log('  HỎNG  ' + s));
  console.log('\n' + dat + ' đạt, ' + hong + ' hỏng');
  process.exit(hong ? 1 : 0);
})();
