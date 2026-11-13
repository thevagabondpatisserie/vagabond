/* v654 (Thu mua 13/11/2026, ảnh màn đợt 20/11): ô chọn từng hoá đơn, chọn hàng
   loạt theo chip lọc và ô tìm, tổng đợt thanh toán theo hoá đơn đã chọn. Chạy
   THẬT 71-du-chi.js trong node, máy chủ giả (dựng lại khung của du_chi_653.js).
   Chốt:
     1. Bấm ô chọn một hoá đơn: chọn là trả hết, bỏ là 0; dòng không mở chi tiết.
     2. Thanh chọn: Đã chọn m/n hoá đơn, tổng đợt thanh toán đúng số.
     3. Chip Chưa chọn + Chọn hết đang lọc: chỉ chọn đúng các hoá đơn đang hiện.
     4. Gõ tìm tên nhà cung cấp rồi Bỏ chọn đang lọc: chỉ bỏ hoá đơn của nhà đó.
     5. Lưu gửi đúng số trả của các dòng đã đổi; nút Gửi duyệt ghi số hoá đơn.
     6. Hoá đơn đã lập APP không có ô chọn; đợt đã gửi duyệt không có ô chọn.
     7. Ô chọn, nút hàng loạt cao từ 44 điểm, chữ từ 13 điểm. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const dom = require('./dom_gia.js');
const BEP = path.resolve(__dirname, '../../../public/js/bep');
const doc = n => fs.readFileSync(path.join(BEP, n), 'utf8');
const KHUNG = doc('01-khung-app.js'), DCN = doc('71-du-chi.js'), SOAN_DO = doc('48-ban-soan-do.js');
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

const MA = 'DC-26-11-20';
function dong(ncc, ten, hd, so, co, tra, han) {
  return { idx: 0, ncc, ten_ncc: ten, nhom: 'Nguyên liệu', hoa_don: hd, so_hd: so, ngay_hd: '2026-10-20', han: han || '2026-11-19',
    con_no: co, dang_giu: 0, co_the_tra: co, so_tra: tra, gia_han: co - tra, ghi_chu: '', hen_dot: '', app: '', ket_qua: '' };
}
function duLieu(tt, them) {
  const d = { ma: MA, ngay_dot: '2026-11-20', trang_thai: tt || 'Nhap', nhan: 'Thu mua đang thương lượng', so_du: 500000000,
    dong: [dong('NCC-P', 'Printeco', 'PI-1', '0001234', 100000000, 100000000),
      dong('NCC-P', 'Printeco', 'PI-2', '0001240', 30000000, 0, '2026-12-05'),
      dong('NCC-H', 'Phương Hoàng Phát', 'PI-3', '0000777', 50000000, 50000000)],
    so_ngay_no: { 'NCC-P': { so: 30, nguon: 'mac_dinh', goi_y: null }, 'NCC-H': { so: 45, nguon: 'khai', goi_y: 40 } },
    quyen: { sua: 1, fin: 0, gd: 0 }, ly_do_tra_lai: '', fin_boi: '', gd_boi: '' };
  (them || []).forEach(x => d.dong.push(x));
  d.dong.forEach((x, i) => { x.idx = i + 1; });
  return d;
}

function appMoi(kho, may) {
  const tl = dom.taiLieuGia(), nghe = {};
  tl.addEventListener = (l, f) => (nghe[l] = nghe[l] || []).push(f);
  tl.createEvent = () => ({ initEvent(t) { this.type = t; } });
  const vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  let hen = [], soHen = 0, bayGio = 1790000000000;
  const goi = [], hop = [];
  const g = { console, JSON, Math, Number, String, Object, Array, Promise, Error, RegExp, parseFloat, parseInt, isNaN,
    Date: (function () { function D(x) { return x === undefined ? new Date(bayGio) : new Date(x); } D.now = () => bayGio; return D; })(),
    document: tl, frappe: { session: { user: 'uyen@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace() {} },
    history: { pushState() {}, replaceState() {}, back() {} }, requestAnimationFrame: f => f(),
    setTimeout: (f, ms) => { soHen++; hen.push({ id: soHen, f, luc: bayGio + (ms || 0) }); return soHen; },
    clearTimeout: id => { hen = hen.filter(x => x.id !== id); } };
  g.window = g; g.localStorage = kho; g.addEventListener = (l, f) => (nghe['w:' + l] = nghe['w:' + l] || []).push(f);
  vm.createContext(g);
  g.__hop = hop;
  g.__api = async (m, a) => {
    goi.push({ m, a });
    const d = may.d;
    if (m === 'vagabond.du_chi.chi_tiet') return JSON.parse(JSON.stringify(d));
    if (m === 'vagabond.du_chi.luu') {
      JSON.parse(a.dong).forEach(x => {
        const r = d.dong.filter(y => y.hoa_don === x.hoa_don)[0];
        if (x.so_tra != null) { r.so_tra = x.so_tra; r.gia_han = r.co_the_tra - x.so_tra; }
        if (x.ghi_chu != null) r.ghi_chu = x.ghi_chu;
        if (x.hen_dot != null) r.hen_dot = x.hen_dot;
      });
      return JSON.parse(JSON.stringify(d));
    }
    if (m === 'vagabond.du_chi.gui') { d.trang_thai = 'Cho ke toan'; return JSON.parse(JSON.stringify(d)); }
    if (m === 'vagabond.du_chi.duyet') { d.trang_thai = a.buoc === 'fin' ? 'Cho giam doc' : a.buoc === 'tra_lai' ? 'Nhap' : d.trang_thai; return JSON.parse(JSON.stringify(d)); }
    return {};
  };
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'var __tin = []; function toast(s) { __tin.push(String(s)); } function busy() {} function baoTin(s) { __tin.push("baoTin:" + s); }',
    'function dSkin() {} function vgbCss() {} function money(x) { return String(Math.round(Number(x) || 0)); }',
    'function dmy(x) { var s = String(x || ""); return s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4); }',
    'function today() { return "2026-11-12"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function confirmSheet(t) { __hop.push(["confirm", t]); return Promise.resolve(true); }',
    'var __chu = null; function hoiChu(t, n, m, o) { __hop.push(["hoiChu", t, !!(o && o.bat_buoc)]); return Promise.resolve(__chu); }',
    'function hoiChon(t, m, ds) { __hop.push(["hoiChon", t]); return Promise.resolve("tiep"); }',
    'function api(m, a) { return __api(m, a); }',
    'function vgbGomNhom() {} function hqLaHop() { return false; }',
    'async function scrHome() { frame(APPNAME, "<div class=\\"emp\\">...</div>"); }',
    'function scrHoSoTTView() {}',
  ].join('\n'), g);
  vm.runInContext(KHUNG, g);
  vm.runInContext(TIM, g);
  vm.runInContext('S.user = "uyen@vagabond.vn"; S.roles = ["Purchase User"]; coQuyenMua = function () { return true; };', g);
  vm.runInContext(DCN, g);
  const boc = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(x => x.split(' ')[0]);
  boc.forEach(t => { if (typeof g[t] !== 'function') vm.runInContext('function ' + t + '() {}', g); });
  ['bgMoRong', 'bgTay', 'tvTay', 'XK', 'rnd', 'dsTay', 'hdTay', 'hdSua', 'hdGsDong', 'hdGsKieu', 'vdTay', 'cpTay', 'kgForm', 'nccF',
    'dncForm', 'nqSuaMa', 'ctE', 'tcX', 'tq', 'tqd', 'XKT', 'XPV', 'rcvD', 'nhpD', 'mfgD', 'htF', 'htFHop', 'dhF', 'dhOv', 'kmSua', 'GM', 'gmKhoiPhuc']
    .forEach(t => { if (!(t in g)) g[t] = null; });
  vm.runInContext(SOAN_DO, g);
  const o = hd => tl.querySelector('[data-dcntra="' + hd + '"]');
  const than = () => tl.getElementById('vgbBody');
  return {
    g, tl, goi, hop, o, than,
    async tua(ms) { bayGio += ms; for (let v = 0; v < 20; v++) { const toi = hen.filter(x => x.luc <= bayGio); if (!toi.length) break; hen = hen.filter(x => x.luc > bayGio); toi.forEach(x => x.f()); await nghi(); } },
    async go(hd, chu) {
      const el = o(hd); assert(el, 'thiếu ô ' + hd); el.value = chu;
      const ev = dom.suKien('input', {}, el); (nghe.input || []).forEach(f => f(ev)); el.dispatchEvent(ev); if (el.oninput) el.oninput(ev);
      await nghi();
      if (el.onchange) { el.onchange(); await nghi(); }
    },
    async bam(el) { assert(el, 'thiếu chỗ bấm'); const ev = dom.suKien('click', {}, el); (nghe.click || []).forEach(f => f(ev)); await than().onclick({ target: el }); await nghi(); },
    async bamNut(id) { const el = tl.getElementById(id); assert(el, 'thiếu nút ' + id); assert(el.onclick, 'nút ' + id + ' chưa nối'); await el.onclick(); await nghi(); await nghi(); },
    async moMan() { await g.reset(g.scrHome); await nghi(); g.DCN.ma = MA; g.go(function () { g.DCN.d = null; return g.scrDuChiXem(); }); await nghi(); await nghi(); },
  };
}

const nhap = kho => Array.from(kho._m.keys()).filter(k => k.indexOf('vgbSoanDo:') === 0);

(async () => {
  const chon = (a, hd) => a.tl.querySelector('[data-dcnchon="' + hd + '"]');
  const thanh = a => { const so = a.tl.getElementById('dcnSoChon').innerHTML.split('/').map(Number); return [so[0], so[1], Number(a.tl.getElementById('dcnTongChon').innerHTML.replace(/[^0-9]/g, ''))]; };
  {
    const them = [];
    for (let i = 0; i < 6; i++) them.push(dong('NCC-D' + i, 'Đông Á ' + i, 'PI-D' + i, '00099' + i, 1000000, 0, '2026-12-30'));
    const kho = khoMay(), may = { d: duLieu('Nhap', them) };
    const a = appMoi(kho, may);
    await a.moMan();
    assert.deepEqual(thanh(a), [2, 9, 150000000], 'mở đợt: 2/9 hoá đơn máy chọn sẵn, tổng 150 triệu');
    assert.equal(chon(a, 'PI-2').getAttribute('aria-checked'), 'false', 'hoá đơn chưa tới hạn chưa chọn');
    await a.bam(chon(a, 'PI-2'));
    assert.equal(String(a.o('PI-2').value), '30000000', 'chọn là trả hết 30 triệu');
    assert(!a.g.DCN.mo['PI-2'], 'bấm ô chọn không mở chi tiết dòng');
    assert.deepEqual(thanh(a), [3, 9, 180000000], 'tổng đợt lên 180 triệu');
    await a.bam(chon(a, 'PI-1'));
    assert.equal(String(a.o('PI-1').value), '0', 'bỏ chọn là 0');
    assert.deepEqual(thanh(a), [2, 9, 80000000], 'tổng đợt 80 triệu');
    assert(a.tl.getElementById('dcnGui').innerHTML.indexOf('Gửi duyệt 2 HĐ · 80000000 đ') >= 0, 'nút Gửi duyệt ghi số hoá đơn và tổng');
    /* Chip Chưa chọn + Chọn hết đang lọc. */
    await a.bam(a.tl.querySelector('[data-dcnloc="chua"]'));
    assert(a.tl.getElementById('dcnChonHetSo').innerHTML === '7', 'nút ghi 7 hoá đơn đang lọc (chưa chọn)');
    await a.bam(a.tl.getElementById('dcnChonHet'));
    assert.deepEqual(thanh(a), [9, 9, 186000000], 'chọn hết đang lọc: thêm đúng 7 hoá đơn chưa chọn');
    /* Tìm theo nhà cung cấp rồi bỏ chọn đúng nhà đó. */
    await a.bam(a.tl.querySelector('[data-dcnloc=""]'));
    const o = a.tl.getElementById('dcnTim'); o.value = 'phuong hoang'; o.oninput(); await nghi();
    assert(a.tl.getElementById('dcnBoHetSo').innerHTML === '1', 'gõ tìm thì số trên nút theo lọc');
    await a.bam(a.tl.getElementById('dcnBoHet'));
    assert.equal(String(a.o('PI-3').value), '0', 'Phương Hoàng Phát bỏ chọn');
    assert.deepEqual([String(a.o('PI-1').value), String(a.o('PI-2').value)], ['100000000', '30000000'], 'Printeco giữ nguyên');
    await a.bamNut('dcnLuu');
    const l = JSON.parse(a.goi.filter(x => x.m === 'vagabond.du_chi.luu')[0].a.dong);
    const ls = {}; l.forEach(x => { ls[x.hoa_don] = x.so_tra; });
    assert.deepEqual([ls['PI-1'], ls['PI-2'], ls['PI-3'], l.filter(x => x.hoa_don.indexOf('PI-D') === 0 && x.so_tra === 1000000).length],
      [100000000, 30000000, 0, 6], 'Lưu gửi đúng số trả của mọi dòng đã đổi');
    /* Chuẩn chạm. */
    const html = a.than().innerHTML;
    const nho = (html.match(/font-size:\s*(\d+(?:\.\d+)?)px/g) || []).map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
    if (nho.length) console.error((html.match(/.{80}font-size:\s*1[0-2](\.\d+)?px.{40}/g) || []).slice(0, 3));
    assert.deepEqual(nho, [], 'chữ từ 13 điểm');
    ['[data-dcnchon]', '#dcnChonHet', '#dcnBoHet', '[data-dcnloc]'].forEach(sel => a.tl.querySelectorAll(sel).forEach(el =>
      assert(/min-height:\s*44px/.test(el.getAttribute('style') || ''), sel + ' cao 44 điểm')));
  }
  {
    /* Hoá đơn đã lập APP và đợt đã gửi duyệt. */
    const may = { d: duLieu() };
    may.d.dong[0].app = 'APP.26.11.001';
    const a = appMoi(khoMay(), may);
    await a.moMan();
    assert(!chon(a, 'PI-1') && chon(a, 'PI-3'), 'hoá đơn đã lập APP không có ô chọn');
    const b = appMoi(khoMay(), { d: Object.assign(duLieu('Cho ke toan'), { quyen: { sua: 0, fin: 1, gd: 0 } }) });
    await b.moMan();
    assert(!b.tl.querySelector('[data-dcnchon]') && !b.tl.getElementById('dcnChonHet'), 'đợt đã gửi duyệt không có ô chọn');
  }
  console.log('PASS 654 chọn hoá đơn: từng dòng, hàng loạt theo lọc, tổng đợt thanh toán');
})().catch(e => { console.error(e); process.exit(1); });
