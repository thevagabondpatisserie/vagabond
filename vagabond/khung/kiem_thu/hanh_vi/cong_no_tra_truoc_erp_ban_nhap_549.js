/* v549 Codex #403: màn "Đã trả trước khi lên ERP" có bản nháp tự lưu.
   Chạy THẬT khung app (01), màn công nợ (đoạn Công nợ NCC của 16) và phần tự
   lưu (48, nạp sau cùng như bản ghép). "Máy sập nguồn" = dựng một app mới
   tinh trên cùng kho localStorage. Chốt hai điều:
     1. số tiền, ngày, ghi chú gõ dở còn nguyên sau khi mở lại;
     2. MÃ LẦN giữ nguyên: mất phản hồi rồi tải lại vẫn gửi cùng mã, máy chủ
        nhận ra lần cũ, không lập bút toán thứ hai. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
const KHUNG = doc('01-khung-app.js'), DS = doc('15-khuon-danh-sach.js'), MUA = doc('16-mua-hang.js'), SOAN_DO = doc('48-ban-soan-do.js');
const CNT = MUA.slice(MUA.indexOf('/* Công nợ NCC:'), MUA.indexOf('/* ---------------- Hoa don ban ra'));

function khoMay() {
  const m = new Map();
  return { _m: m, get length() { return m.size; }, key: i => Array.from(m.keys())[i] || null,
    getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) };
}
async function nghi() { for (let i = 0; i < 12; i++) await Promise.resolve(); await new Promise(r => setImmediate(r)); }

function appMoi(kho, mat) {
  const tl = dom.taiLieuGia(), nghe = {};
  tl.addEventListener = (l, f) => (nghe[l] = nghe[l] || []).push(f);
  tl.createEvent = () => ({ initEvent(t) { this.type = t; } });
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  let hen = [], soHen = 0, bayGio = 1790000000000, soMa = 0;
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
    if (m.endsWith('xem_truoc_erp')) return { hoa_don: 'PI-1', bill_no: '74', ten_ncc: 'PRINTECO', con_no: 212090400, dang_cho: 0, cho_duyet: [], ke_toan: false, tk_tam: 'Temporary Opening - TV' };
    if (m.endsWith('lap_truoc_erp')) { if (mat) throw new Error('Mất mạng'); return { je: 'PKT-1', da_ghi_so: false }; }
    if (m.endsWith('danh_sach')) return { cong_ty: 'CTY', cac_cong_ty: ['CTY'], cac_nhom: [], ngay_doc: '2026-10-01', so_hd: 0, so_ncc: 0, tong_theo_tien: {}, dem: { tat_ca: 0 }, con_nua: false, dong: [], ke_toan: false };
    return {};
  };
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'var __tin = []; function toast(s) { __tin.push(String(s)); } function busy() {} function baoTin(s) { __tin.push("baoTin:" + s); }',
    'function dSkin() {} function vgbCss() {} function money(x) { return String(x); } function ngayNgan(x) { return String(x); }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'function hoiChon(t, m, ds) { return Promise.resolve("tiep"); }',
    'function api(m, a) { return __api(m, a); }',
    'function vgbGomNhom() {} function kmHangChip(s) { return "<div>" + s + "</div>"; } function posChipNut(a, n) { return "<button " + a + ">" + n + "</button>"; }',
    'function hqLaHop() { return false; }',
    'var __tep = {}; function tdkNap(id, a) { __tep[id] = (a || []).slice(); } function tdkDs(id) { return __tep[id] || []; }',
    'function tdkKhoi() { return "<div></div>"; } function tdkNoi() {} function tdkVeLai() {}',
    'function hsCoQuyenCanCoc() { return false; } var hsCocLan = null; function hsThuLaiCanCoc() {}',
    'function sinhMaLanNhan() { return "LN-" + (++__soMa) + "-" + Math.random().toString(36).slice(2, 8); } var __soMa = 0;',
    'async function scrHome() { frame(APPNAME, "<div class=\\"emp\\">...</div>"); }',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g); vm.runInContext(DS, g);
  vm.runInContext('S.user = "uyen@vagabond.vn"; S.roles = ["Purchase User"];', g);
  vm.runInContext(CNT, g);
  const boc = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(x => x.split(' ')[0]);
  boc.forEach(t => { if (typeof g[t] !== 'function') vm.runInContext('function ' + t + '() {}', g); });
  ['bgMoRong', 'bgTay', 'tvTay', 'XK', 'rnd', 'dsTay', 'hdTay', 'hdSua', 'hdGsDong', 'hdGsKieu', 'vdTay', 'cpTay', 'kgForm', 'nccF',
    'dncForm', 'nqSuaMa', 'ctE', 'tcX', 'tq', 'tqd', 'XKT', 'XPV', 'rcvD', 'nhpD', 'mfgD', 'htF', 'htFHop', 'dhF', 'dhOv', 'kmSua']
    .forEach(t => { if (!(t in g)) g[t] = null; });
  vm.runInContext(SOAN_DO, g);
  return {
    g, tl, goi,
    async tua(ms) { bayGio += ms; for (let v = 0; v < 20; v++) { const toi = hen.filter(x => x.luc <= bayGio); if (!toi.length) break; hen = hen.filter(x => x.luc > bayGio); toi.forEach(x => x.f()); await nghi(); } },
    go(id, chu) { const o = tl.getElementById(id); assert(o, 'thiếu ô ' + id); o.value = chu; const ev = dom.suKien('input', {}, o); (nghe.input || []).forEach(f => f(ev)); o.dispatchEvent(ev); },
    async bam(id) { const el = tl.getElementById(id); assert(el, 'thiếu nút ' + id); const ev = dom.suKien('click', {}, el); (nghe.click || []).forEach(f => f(ev)); el.dispatchEvent(ev); await nghi(); },
    async moMan() { await g.reset(g.scrHome); await nghi(); g.go(function () { g.scrCntTruocErp('PI-1'); }); await nghi(); await nghi(); },
  };
}

(async () => {
  const kho = khoMay();
  // Lần 1: Uyên gõ dở, bấm gửi thì mất mạng, rồi máy sập.
  const a = appMoi(kho, true);
  await a.moMan();
  assert(a.tl.getElementById('cntTeTien'), 'màn mở được');
  a.go('cntTeTien', '150000000'); a.go('cntTeNgay', '2026-04-10'); a.go('cntTeGhiChu', 'MB 1234');
  a.g.tdkNap('cnttruoc', ['/private/files/unc-printeco.pdf']);
  await a.bam('cntTeGui');
  const lan1 = a.goi.filter(x => x.m.endsWith('lap_truoc_erp'));
  assert.equal(lan1.length, 1, 'đã gửi một lần');
  await a.tua(1000);
  const khoa = Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0);
  assert.equal(khoa.length, 1, 'có đúng một bản nháp trên máy');
  assert(/tra_truoc_erp:PI-1$/.test(khoa[0]), 'bản nháp theo hóa đơn: ' + khoa[0]);

  // Lần 2: app mới tinh, cùng máy. Mở lại màn: chữ còn nguyên, gửi cùng mã lần.
  const b = appMoi(kho, false);
  await b.moMan();
  assert.equal(b.tl.getElementById('cntTeTien').value, '150000000', 'số tiền còn');
  assert.equal(b.tl.getElementById('cntTeNgay').value, '2026-04-10', 'ngày còn');
  assert.equal(b.tl.getElementById('cntTeGhiChu').value, 'MB 1234', 'ghi chú còn');
  await b.bam('cntTeGui');
  const lan2 = b.goi.filter(x => x.m.endsWith('lap_truoc_erp'));
  assert.equal(lan2.length, 1);
  assert.equal(lan2[0].a.ma_lan, lan1[0].a.ma_lan, 'tải lại vẫn gửi CÙNG mã lần');
  assert.deepEqual(JSON.parse(lan2[0].a.unc), ['/private/files/unc-printeco.pdf'], 'UNC đã chọn còn');
  await b.tua(1000);
  assert.equal(Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0).length, 0, 'gửi thành công thì xóa bản nháp');
  console.log('PASS 549 bản nháp: mở lại còn số tiền, ngày, ghi chú, UNC và cùng mã lần; gửi xong xóa nháp');
})().catch(e => { console.error(e); process.exit(1); });
