/* v653 Dự chi công nợ (#555): chạy THẬT khung app (01), màn Dự chi (71) và
   phần tự lưu (48) trong node, máy chủ giả. Dựng đúng chuỗi thao tác của Uyên,
   kế toán, giám đốc; không gọi thêm hàm "cho chắc" (bài học #205).
   Chốt:
     1. Ca 100/60/40 trong bảng tay của anh Việt: hoá đơn còn 100 triệu, gõ trả
        60 triệu thì màn hiện gia hạn 40 triệu; Lưu chỉ gửi đúng dòng đã sửa.
     2. Gõ dở rồi tải lại trang: còn số đã gõ; bấm Lưu thì bản nháp xoá.
     3. Số trả vượt phần còn đề nghị được: dòng đỏ, không gọi máy chủ.
     4. Trả hết, Không trả đợt này của một nhà cung cấp.
     5. Đợt chờ kế toán: không có ô gõ số, có nút Kế toán đã soát, bấm thì gửi
        bước fin; trả lại phải ghi lý do.
     6. Danh sách dài có ô tìm, gõ không dấu tên nhà cung cấp hay số hoá đơn.
     7. Chuẩn chạm: mọi dòng, chip, nút mới cao từ 44 điểm, chữ từ 13 điểm. */
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
  {
    /* 1, 2. Ca 100/60/40, tải lại trang, Lưu. */
    const kho = khoMay(), may = { d: duLieu() };
    const a = appMoi(kho, may);
    await a.moMan();
    assert(a.o('PI-1'), 'màn mở được, có ô số trả');
    assert.equal(String(a.o('PI-1').value), '100000000', 'máy gợi ý trả hết hoá đơn tới hạn');
    assert.equal(String(a.o('PI-2').value), '0', 'hoá đơn chưa tới hạn máy để 0');
    await a.go('PI-1', '60.000.000');
    assert.equal(a.g.DCN.sua['PI-1'].so_tra, 60000000, 'gõ có dấu chấm vẫn nhận 60 triệu');
    assert(a.than().innerHTML.indexOf('Gia hạn 40000000 đ') >= 0, 'màn hiện gia hạn 40 triệu ngay trên dòng');
    assert(a.than().innerHTML.indexOf('>110000000 đ</div>') >= 0, 'ô Trả đợt này của cả đợt: 60 + 50 triệu');
    const tp = a.g.dcnTong(a.g.DCN.d.dong.filter(x => x.ncc === 'NCC-P'));
    assert.deepEqual([tp.tra, tp.gia_han], [60000000, 70000000], 'Printeco: trả 60 triệu, gia hạn 40 + 30 triệu');
    await a.tua(1000);
    assert.equal(nhap(kho).length, 1, 'đã có bản nháp trên máy');
    const b = appMoi(kho, may);
    await b.moMan();
    assert.equal(String(b.o('PI-1').value), '60000000', 'tải lại trang vẫn còn số 60 triệu đã gõ');
    await b.bamNut('dcnLuu');
    const luu = b.goi.filter(x => x.m === 'vagabond.du_chi.luu');
    assert.equal(luu.length, 1, 'bấm Lưu gọi máy chủ một lần');
    assert.deepEqual(JSON.parse(luu[0].a.dong), [{ hoa_don: 'PI-1', so_tra: 60000000 }], 'chỉ gửi đúng dòng đã sửa');
    await b.tua(1000);
    assert.equal(nhap(kho).length, 0, 'Lưu xong thì bản nháp xoá');
    assert.equal(may.d.dong[0].gia_han, 40000000, 'máy chủ giả ghi gia hạn 40 triệu');
  }
  {
    /* 3. Vượt phần còn đề nghị được. */
    const kho = khoMay(), may = { d: duLieu() };
    const a = appMoi(kho, may);
    await a.moMan();
    await a.go('PI-3', '70000000');
    assert(a.than().innerHTML.indexOf('Số trả phải từ 0 tới 50000000 đ.') >= 0, 'dòng vượt số hiện câu đỏ chỉ cách sửa');
    await a.bamNut('dcnGui');
    assert.equal(a.goi.filter(x => x.m === 'vagabond.du_chi.luu' || x.m === 'vagabond.du_chi.gui').length, 0, 'số sai thì không gọi máy chủ');
    assert(a.g.__tin.some(t => t.indexOf('số trả sai') >= 0), 'báo còn hoá đơn có số trả sai');
  }
  {
    /* 4. Trả hết và Không trả đợt này. */
    const kho = khoMay(), may = { d: duLieu() };
    const a = appMoi(kho, may);
    await a.moMan();
    await a.bam(a.tl.querySelector('[data-dcnhet="0"]'));
    assert.equal(String(a.o('PI-2').value), '30000000', 'Trả hết điền đủ cả hoá đơn chưa tới hạn');
    await a.bam(a.tl.querySelector('[data-dcnkhong="1"]'));
    assert.equal(String(a.o('PI-3').value), '0', 'Không trả đợt này đưa về 0');
    assert(a.than().innerHTML.indexOf('Gia hạn 50000000 đ') >= 0, 'không trả thì gia hạn cả 50 triệu');
    /* Hẹn đợt và ghi chú: mở dòng, chọn đợt 10/12. */
    await a.bam(a.tl.querySelector('[data-dcnmo="PI-3"]'));
    await a.bam(a.tl.querySelectorAll('[data-dcnhen="PI-3"]').filter(x => x.getAttribute('data-ngay') === '2026-12-10')[0]);
    assert.equal(a.g.DCN.sua['PI-3'].hen_dot, '2026-12-10', 'hẹn trả đợt 10/12');
    await a.bamNut('dcnLuu');
    const l = JSON.parse(a.goi.filter(x => x.m === 'vagabond.du_chi.luu')[0].a.dong);
    assert.deepEqual(l.filter(x => x.hoa_don === 'PI-3')[0], { hoa_don: 'PI-3', so_tra: 0, hen_dot: '2026-12-10' }, 'gửi số 0 và đợt hẹn');
  }
  {
    /* 5. Đợt chờ kế toán soát. */
    const kho = khoMay(), may = { d: duLieu('Cho ke toan') };
    may.d.quyen = { sua: 0, fin: 1, gd: 0 };
    const a = appMoi(kho, may);
    await a.moMan();
    assert(!a.o('PI-1'), 'đợt đã gửi duyệt thì không còn ô gõ số');
    assert(!a.tl.getElementById('dcnLuu'), 'không có nút Lưu');
    a.g.__chu = null;
    await a.bamNut('dcnTraLai');
    assert.deepEqual(a.hop.filter(x => x[0] === 'hoiChu').map(x => x[2]), [true], 'trả lại thì hỏi lý do, bắt buộc điền');
    assert.equal(a.goi.filter(x => x.m === 'vagabond.du_chi.duyet').length, 0, 'bấm Thôi ở ô lý do thì không trả lại');
    await a.bamNut('dcnFin');
    const dy = a.goi.filter(x => x.m === 'vagabond.du_chi.duyet');
    assert.deepEqual(dy.map(x => x.a.buoc), ['fin'], 'Kế toán đã soát gửi đúng bước fin');
  }
  {
    /* 6. Ô tìm khi danh sách dài, gõ không dấu. */
    const them = [];
    for (let i = 0; i < 6; i++) them.push(dong('NCC-D' + i, 'Đông Á ' + i, 'PI-D' + i, '00099' + i, 1000000, 0, '2026-12-30'));
    const kho = khoMay(), may = { d: duLieu('Nhap', them) };
    const a = appMoi(kho, may);
    await a.moMan();
    const o = a.tl.getElementById('dcnTim');
    assert(o, 'danh sách 9 hoá đơn có ô tìm nhanh');
    const hien = () => a.tl.querySelectorAll('[data-dcndong]').filter(x => x.style.display !== 'none').map(x => x.getAttribute('data-dcndong'));
    o.value = 'phuong hoang'; o.oninput(); await nghi();
    assert.deepEqual(hien(), ['PI-3'], 'gõ không dấu tên nhà cung cấp');
    o.value = '0001240'; o.oninput(); await nghi();
    assert.deepEqual(hien(), ['PI-2'], 'gõ số hoá đơn');
    await a.go('PI-1', '1');
    assert.equal(a.tl.getElementById('dcnTim').value, '0001240', 'vẽ lại vẫn giữ chữ đang tìm');
    assert.deepEqual(hien(), ['PI-2'], 'vẽ lại vẫn lọc');
    await a.bam(a.tl.querySelector('[data-dcnloc="han"]'));
    o.value = ''; a.tl.getElementById('dcnTim').value = ''; a.tl.getElementById('dcnTim').oninput(); await nghi();
    assert.deepEqual(hien(), ['PI-1', 'PI-3'], 'chip Tới hạn chỉ còn hoá đơn tới hạn trước ngày đợt');
  }
  {
    /* 7. Chuẩn chạm và chữ. */
    const kho = khoMay(), may = { d: duLieu() };
    const a = appMoi(kho, may);
    await a.moMan();
    await a.bam(a.tl.querySelector('[data-dcnmo="PI-1"]'));
    const html = a.than().innerHTML + a.tl.querySelector('.vf').innerHTML;
    const nho = (html.match(/font-size:\s*(\d+(?:\.\d+)?)px/g) || []).map(x => parseFloat(x.replace(/[^\d.]/g, ''))).filter(x => x < 13);
    assert.deepEqual(nho, [], 'không có chữ nhỏ hơn 13 điểm');
    ['[data-dcnmo]', '[data-dcnloc]', '[data-dcnhen]', '[data-dcnno]'].forEach(sel => {
      const ds = a.tl.querySelectorAll(sel);
      assert(ds.length, 'có ' + sel);
      ds.forEach(el => assert(/min-height:\s*44px/.test(el.getAttribute('style') || ''), sel + ' cao ít nhất 44 điểm'));
    });
    assert(!/<select/i.test(html), 'không dùng hộp select');
  }
  console.log('PASS 653 Dự chi công nợ: 100/60/40, tải lại trang, số vượt, trả hết, kế toán soát, tìm nhanh, chuẩn chạm');
})().catch(e => { console.error(e); process.exit(1); });
