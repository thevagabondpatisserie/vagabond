/* v646 Codex 549 (vòng 43956a7): màn Gom yêu cầu mua giữ số thu mua đã sửa.
   Chạy THẬT khung app (01), màn Gom yêu cầu mua (70) và phần tự lưu (48, nạp
   sau 70 như bản ghép thật thì 48 đứng trước 70; ở đây nạp 70 trước để 48 bọc
   được tên scrGomMua, giống thứ tự hàm được nâng lên trong vỏ ghép).
   "Tải lại trang" = dựng một app mới tinh trên cùng kho localStorage.
   Chốt:
     1. sửa số rồi tải lại trang: mở lại còn số đã sửa (trước bản sửa: mất);
     2. bấm làm mới trên màn: số đã sửa không bị xoá;
     3. số máy điền sẵn đổi theo phiếu xin mới thì món CHƯA sửa hiện số mới,
        không bị điền đè số cũ;
     4. chốt một nhóm khi nhóm khác còn số đã sửa: bản nháp còn, tải lại vẫn
        còn số nhóm kia; chốt nốt thì bản nháp xoá;
     5. (Codex 549, 1eefda8) phiếu xin mới của món vừa chốt hiện số máy mới,
        cả trong cùng phiên lẫn sau khi tải lại trang. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
const KHUNG = doc('01-khung-app.js'), GOM = doc('70-gom-mua.js'), SOAN_DO = doc('48-ban-soan-do.js');
/* Ô tìm nhanh dùng chung của app: lấy nguyên hàm thật từ 00-nen và 07-hop-thoai. */
function layHam(src, ten) {
  const dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Không thấy hàm ' + ten);
  let i = src.indexOf('{', dau), sau = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Hàm ' + ten + ' không đóng ngoặc');
}
const NEN = doc('00-nen.js'), HOP = doc('07-hop-thoai.js');
const TIM = [layHam(NEN, 'vgbChuan'), layHam(NEN, 'vgbKhop'), HOP.match(/^var VGB_NGUONG_TIM = \d+;$/m)[0],
  layHam(HOP, 'vgbCanOTim'), layHam(HOP, 'vgbOTim')].join('\n');

function khoMay() {
  const m = new Map();
  return { _m: m, get length() { return m.size; }, key: i => Array.from(m.keys())[i] || null,
    getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) };
}
async function nghi() { for (let i = 0; i < 12; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

function duLieu(muaBo) {
  return { so_dong: 3, so_phieu: 3, nhom: [
    { ncc: 'NCC-A', ten_ncc: 'Bơ sữa An Phú', so_mon: 1, so_phieu: 1,
      mon: [{ ma: 'BO', ten: 'Bơ lạt', mua: muaBo, xin: muaBo, dvt: 'Gram', ton: 0, cho_ve: 0, gia: 0.25, phieu: [{ phieu: 'YC-1', xin: muaBo }] }] },
    { ncc: 'NCC-B', ten_ncc: 'Sữa Long Thành', so_mon: 2, so_phieu: 2,
      mon: [{ ma: 'SUA', ten: 'Sữa tươi', mua: 12, xin: 12, dvt: 'Hộp', ton: 0, cho_ve: 0, gia: 30000, phieu: [{ phieu: 'YC-2', xin: 12 }] },
        { ma: 'KEM', ten: 'Kem', mua: 6, xin: 6, dvt: 'Hộp', ton: 0, cho_ve: 0, gia: 90000, phieu: [{ phieu: 'YC-3', xin: 6 }] }] }] };
}

function appMoi(kho, may) {
  const tl = dom.taiLieuGia(), nghe = {};
  tl.addEventListener = (l, f) => (nghe[l] = nghe[l] || []).push(f);
  tl.createEvent = () => ({ initEvent(t) { this.type = t; } });
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  let hen = [], soHen = 0, bayGio = 1790000000000;
  const goi = [];
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, parseFloat, parseInt, isNaN,
    Date: (function () { function D(x) { return x === undefined ? new Date(bayGio) : new Date(x); } D.now = () => bayGio; return D; })(),
    document: tl, frappe: { session: { user: 'uyen@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: (f, ms) => { soHen++; hen.push({ id: soHen, f, luc: bayGio + (ms || 0) }); return soHen; },
    clearTimeout: id => { hen = hen.filter(x => x.id !== id); } };
  g.window = g; g.localStorage = kho; g.addEventListener = (l, f) => (nghe['w:' + l] = nghe['w:' + l] || []).push(f);
  vm.createContext(g);
  g.__api = async (m, a) => {
    goi.push({ m, a });
    if (m === 'vagabond.gom_mua.ds') return JSON.parse(JSON.stringify(may.d));
    if (m === 'vagabond.gom_mua.chot') {
      const ma = JSON.parse(a.dong).map(x => x.ma);
      may.d.nhom = may.d.nhom.filter(n => !n.mon.some(x => ma.indexOf(x.ma) >= 0));
      /* Chốt xong máy mở đơn mua vừa lập (rời màn, không tải lại danh sách). */
      return { ghi_chu: 'Đã chốt', don: 'PUR-ORD-' + (++may.so) };
    }
    return {};
  };
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'var __tin = []; function toast(s) { __tin.push(String(s)); } function busy() {} function baoTin(s) { __tin.push("baoTin:" + s); }',
    'function dSkin() {} function vgbCss() {} function money(x) { return String(x); } function kl(v, d) { return v + " " + d; }',
    'function anhMon() { return ""; } function dmy(x) { return String(x); }',
    /* v650: màn Gom có chip ngày cần và thuế, cần thêm hai hàm của 00-nen. */
    'function today() { return "2026-11-12"; } function num(x) { return String(x); }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'function hoiChon(t, m, ds) { return Promise.resolve("tiep"); }',
    'function api(m, a) { return __api(m, a); }',
    'function vgbGomNhom() {} function hqLaHop() { return false; }',
    'async function scrHome() { frame(APPNAME, "<div class=\\"emp\\">...</div>"); }',
    'var poXem = ""; function scrDonMuaXem() {}',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(TIM, g);
  vm.runInContext('S.user = "uyen@vagabond.vn"; S.roles = ["Purchase User"]; coQuyenMua = function () { return true; };', g);
  vm.runInContext(GOM, g);
  const boc = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(x => x.split(' ')[0]);
  boc.forEach(t => { if (typeof g[t] !== 'function') vm.runInContext('function ' + t + '() {}', g); });
  ['bgMoRong', 'bgTay', 'tvTay', 'XK', 'rnd', 'dsTay', 'hdTay', 'hdSua', 'hdGsDong', 'hdGsKieu', 'vdTay', 'cpTay', 'kgForm', 'nccF',
    'dncForm', 'nqSuaMa', 'ctE', 'tcX', 'tq', 'tqd', 'XKT', 'XPV', 'rcvD', 'nhpD', 'mfgD', 'htF', 'htFHop', 'dhF', 'dhOv', 'kmSua']
    .forEach(t => { if (!(t in g)) g[t] = null; });
  vm.runInContext(SOAN_DO, g);
  const o = ma => tl.querySelector('[data-gmsl="' + ma + '"]');
  return {
    g, tl, goi, o,
    async tua(ms) { bayGio += ms; for (let v = 0; v < 20; v++) { const toi = hen.filter(x => x.luc <= bayGio); if (!toi.length) break; hen = hen.filter(x => x.luc > bayGio); toi.forEach(x => x.f()); await nghi(); } },
    async go(ma, chu) { const el = o(ma); assert(el, 'thiếu ô ' + ma); el.value = chu; const ev = dom.suKien('input', {}, el); (nghe.input || []).forEach(f => f(ev)); el.dispatchEvent(ev); if (el.oninput) el.oninput(ev); await nghi(); },
    async bamChot(i) { const el = tl.querySelector('[data-gmchot="' + i + '"]'); assert(el, 'thiếu nút chốt ' + i); const ev = dom.suKien('click', {}, el); (nghe.click || []).forEach(f => f(ev)); const b = tl.getElementById('vgbBody'); assert(b && b.onclick, 'màn chưa nối nút'); await b.onclick({ target: el }); await nghi(); },
    async lamMoi() { await g.reset(g.scrHome); await nghi(); g.go(function () { g.GM.d = null; return g.scrGomMua(); }); await nghi(); await nghi(); },
    async moMan() { await g.reset(g.scrHome); await nghi(); g.go(function () { return g.scrGomMua(); }); await nghi(); await nghi(); },
  };
}

const nhap = kho => Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0);

/* Codex 549 (4204048): danh sách dài có ô tìm nhanh (AGENTS.md 2b.5). */
function duLieuDai() {
  const mon = (ma, ten) => ({ ma, ten, mua: 1, xin: 1, dvt: 'Cái', ton: 0, cho_ve: 0, gia: 0, phieu: [{ phieu: 'YC-' + ma, xin: 1 }] });
  return { so_dong: 8, so_phieu: 8, nhom: [
    { ncc: 'NCC-A', ten_ncc: 'Bơ sữa An Phú', so_mon: 4, so_phieu: 4, mon: [mon('BO', 'Bơ lạt'), mon('KEM', 'Kem tươi'), mon('PHO', 'Phô mai'), mon('SUA', 'Sữa tươi')] },
    { ncc: 'NCC-B', ten_ncc: 'Bột Đông Á', so_mon: 4, so_phieu: 4, mon: [mon('BOT', 'Bột mì số 8'), mon('DUONG', 'Đường cát'), mon('MUOI', 'Muối'), mon('MEN', 'Men nở')] }] };
}

(async () => {
  {
    /* Codex #553 (P1, AGENTS.md mục 13): cả dòng món là vùng bấm mở phiếu xin
       (cao ít nhất 44 điểm), không phải một chip nhỏ 24 điểm; bấm ô số mua thì
       không mở; chữ trên màn tối thiểu 13 điểm. Bấm THẬT qua onclick của màn. */
    const kho = khoMay(), may = { d: duLieu(8000), so: 0 };
    const a = appMoi(kho, may);
    await a.moMan();
    const bam = async el => { assert(el, 'thiếu chỗ bấm'); await a.tl.getElementById('vgbBody').onclick({ target: el }); await nghi(); };
    const dong = a.tl.querySelector('[data-gmmo="BO"]');
    assert(dong && /(^|\s)li(\s|$)/.test(dong.getAttribute('class') || ''), 'cả dòng món Bơ là vùng bấm');
    assert(/min-height:\s*44px/.test(dong.getAttribute('style') || ''), 'dòng cao ít nhất 44 điểm');
    await bam(a.o('BO'));
    assert(!a.g.GM.mo.BO, 'bấm ô số mua không mở phiếu xin');
    await bam(a.tl.querySelector('[data-gmmo="BO"]'));
    assert.equal(a.g.GM.mo.BO, 1, 'bấm dòng món mở phiếu xin');
    assert(a.tl.getElementById('vgbBody').innerHTML.indexOf('YC-1') >= 0, 'hiện phiếu YC-1');
    const nho = (a.tl.getElementById('vgbBody').innerHTML.match(/font-size:\s*(\d+(?:\.\d+)?)px/g) || [])
      .map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
    assert.deepEqual(nho, [], 'không còn chữ nhỏ hơn 13 điểm trên màn Gom');
  }
  {
    const kho = khoMay(), may = { d: duLieuDai(), so: 0 };
    const a = appMoi(kho, may);
    await a.moMan();
    const o = a.tl.getElementById('gmTim');
    assert(o, 'danh sách 8 món có ô tìm nhanh');
    await a.go('BO', '5');
    const tim = async chu => { o.value = chu; o.oninput(); await nghi(); };
    const hien = sel => a.tl.querySelectorAll(sel).filter(x => x.style.display !== 'none').map(x => x.getAttribute(sel.slice(1, -1)));
    await tim('duong');
    assert.deepEqual(hien('[data-gmmon]'), ['DUONG'], 'gõ không dấu "duong" ra Đường cát');
    assert.deepEqual(hien('[data-gmnhom]'), ['1'], 'nhóm không còn món khớp thì ẩn');
    await tim('an phu');
    assert.deepEqual(hien('[data-gmmon]'), ['BO', 'KEM', 'PHO', 'SUA'], 'gõ tên nhà cung cấp ra cả nhóm');
    await tim('xyz');
    assert.equal(a.tl.getElementById('gmTimTrong').style.display, '', 'không khớp gì thì có câu chỉ đường');
    assert.equal(a.g.GM.sua.BO, 5, 'tìm không làm mất số đã sửa');
    await tim('men no');
    a.g.GM.d = null; await a.g.scrGomMua(); await nghi();
    assert.equal(a.tl.getElementById('gmTim').value, 'men no', 'vẽ lại vẫn giữ chữ đang tìm');
    assert.deepEqual(hien('[data-gmmon]'), ['MEN'], 'vẽ lại vẫn lọc');
  }
  // 1. Sửa số, tải lại trang: còn số đã sửa.
  const kho = khoMay(), may = { d: duLieu(8000), so: 0 };
  const a = appMoi(kho, may);
  await a.moMan();
  assert(a.o('BO'), 'màn mở được');
  await a.go('BO', '6000'); await a.go('KEM', '0');
  await a.tua(1000);
  assert.equal(nhap(kho).length, 1, 'đã có bản nháp trên máy');
  const b = appMoi(kho, may);
  await b.moMan();
  assert.equal(String(b.o('BO').value), '6000', 'tải lại trang vẫn còn số Bơ đã sửa');
  assert.equal(String(b.o('KEM').value), '0', 'tải lại trang vẫn còn số 0 (từ chối) của Kem');
  assert.equal(String(b.o('SUA').value), '12', 'món chưa sửa giữ số máy');

  // 2. Bấm nút làm mới (↻) ngay trên màn, rồi mở lại màn: không mất số đã sửa.
  b.g.GM.d = null; await b.g.scrGomMua(); await nghi();
  assert.equal(String(b.o('BO').value), '6000', 'nút làm mới trên màn không xoá số đã sửa');
  await b.lamMoi();
  assert.equal(String(b.o('BO').value), '6000', 'mở lại màn không xoá số đã sửa');

  // 3. Có phiếu xin mới: Bơ máy điền 9000, nhưng Bơ đã sửa nên giữ 6000; Sữa chưa sửa thì theo số mới.
  may.d.nhom[1].mon[0].mua = 20; may.d.nhom[1].mon[0].xin = 20;
  const c = appMoi(kho, may);
  await c.moMan();
  assert.equal(String(c.o('SUA').value), '20', 'món chưa sửa hiện số máy MỚI, không bị điền đè số cũ');
  assert.equal(String(c.o('BO').value), '6000', 'món đã sửa vẫn theo số đã sửa');

  // 4. Chốt nhóm An Phú (Bơ) khi nhóm Long Thành còn Kem đã sửa: bản nháp còn.
  await c.bamChot(0);
  const gui = c.goi.filter(x => x.m === 'vagabond.gom_mua.chot');
  assert.equal(gui.length, 1, 'đã chốt một nhóm');
  assert.deepEqual(JSON.parse(gui[0].a.dong), [{ ma: 'BO', sl: 6000 }], 'chốt đúng số đã sửa');
  await c.tua(1000);
  assert.equal(nhap(kho).length, 1, 'nhóm khác còn số đã sửa thì bản nháp còn');
  const d = appMoi(kho, may);
  await d.moMan();
  assert(!d.o('BO'), 'Bơ đã chốt không còn trên màn');
  assert.equal(String(d.o('KEM').value), '0', 'tải lại sau khi chốt một nhóm vẫn còn số Kem đã sửa');
  // 5. Codex 549 (1eefda8): phiếu xin MỚI của món vừa chốt phải hiện số máy mới, không mang số cũ.
  may.d.nhom.unshift({ ncc: 'NCC-A', ten_ncc: 'Bơ sữa An Phú', so_mon: 1, so_phieu: 1,
    mon: [{ ma: 'BO', ten: 'Bơ lạt', mua: 9000, xin: 9000, dvt: 'Gram', ton: 0, cho_ve: 0, gia: 0.25, phieu: [{ phieu: 'YC-9', xin: 9000 }] }] });
  await c.lamMoi();
  assert.equal(String(c.o('BO').value), '9000', 'cùng phiên: Bơ mới hiện 9000, không phải 6000 đã chốt');
  const e = appMoi(kho, may);
  await e.moMan();
  assert.equal(String(e.o('BO').value), '9000', 'tải lại trang: bản nháp không còn số Bơ đã chốt');
  assert.equal(String(e.o('KEM').value), '0', 'số Kem đã sửa vẫn còn');
  may.d.nhom.shift();
  await d.lamMoi();
  await d.bamChot(0);
  await d.tua(1000);
  assert.equal(nhap(kho).length, 0, 'chốt nốt thì xoá bản nháp');
  console.log('PASS 646 Gom yêu cầu mua: tải lại trang, làm mới, phiếu xin mới, chốt từng nhóm đều giữ đúng số đã sửa');
})().catch(e => { console.error(e); process.exit(1); });
