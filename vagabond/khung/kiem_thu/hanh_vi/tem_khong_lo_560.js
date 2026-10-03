/* v560: tem HACCP khi da tat lo (anh Viet chot 03/10/2026, viec so 1).
 * Chay THAT cac ham cua 05-san-xuat.js: man In tem va in ca nhom, khi mon
 * khong co lo. Truoc v560 hai duong nay chi bao "chua bat theo doi lo".
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/tem_khong_lo_560.js
 */
'use strict';
var fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
var src = fs.readFileSync(path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '05-san-xuat.js'), 'utf8');
function layHam(ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function moiTruong() {
  var ghi = { in: [], api: [], body: '', toast: [], lo: 0 }, els = {};
  var ctx = {
    console: console, Math: Math, Date: Date, encodeURIComponent: encodeURIComponent, parseInt: parseInt,
    h: function (s) { return String(s == null ? '' : s).replace(/</g, '&lt;'); },
    ymdOf: function () { return '2026-10-03'; }, hmOf: function () { return '09:30:00'; },
    addDays: function () { return '2026-10-05'; }, dmy: function (s) { return s; },
    mfgBqText: function () { return ''; }, busy: function () {}, toast: function (x) { ghi.toast.push(x); },
    frame: function (t, b) { ghi.body = b; els = {}; return { addEventListener: function () {}, onclick: null }; },
    document: { getElementById: function (id) { return els[id] || (els[id] = { id: id, value: '', onclick: null, textContent: '' }); } },
    inMoCuaSoNeuCan: function () { return null; }, inKho: function () { return { rong: 62 }; },
    inSanSang: function () { return true; }, confirmSheet: async function () { return true; },
    inToTuDuongDan: async function (v, t, url) { ghi.in.push(url); return 'qz'; },
    api: async function (m, p) { ghi.api.push([m, p]); return {}; },
    mfgLoadItem: async function () { return { has_batch_no: 0 }; },
    mfgBatchOf: async function () { ghi.lo++; return null; },
    mfgMakeBatch: async function () { ghi.lo++; return null; },
    mfgPrintCho: async function () { ghi.lo++; },
    errMsg: function (e) { return String(e); }, r3: function (x) { return x; }
  };
  vm.createContext(ctx);
  ['scrMfgLabel', 'mfgTemLenhUrl', 'mfgInTem', 'mfgPrint', 'mfgTemUrl', 'mfgInTemNhom'].forEach(function (t) {
    vm.runInContext(layHam(t), ctx);
  });
  vm.runInContext('var mfgL = null;', ctx);
  return { ctx: ctx, ghi: ghi, els: function () { return els; } };
}
(async function () {
  // 1. Man In tem cua lenh khong co lo: hien dong Ngay de dien tay, in theo lenh
  var m = moiTruong();
  vm.runInContext("mfgL = { batch: '', lenh: 'MFG-WO-2026-00001', item: 'TP001', name: 'Bánh Su Kem', qty: 3, meta: {} };", m.ctx);
  m.ctx.scrMfgLabel();
  assert(m.ghi.body.indexOf('Ngày:') >= 0, 'man tem phai co dong Ngay de dien tay');
  m.els().mlGo.onclick();
  assert.strictEqual(m.ghi.in.length, 1, 'phai day 1 lenh in');
  var u = m.ghi.in[0];
  assert(u.indexOf('/api/method/vagabond.tem_lenh.trang?') === 0, 'in qua trang tem theo lenh: ' + u);
  assert(u.indexOf('ma=TP001') > 0 && u.indexOf('lenh=MFG-WO-2026-00001') > 0 && u.indexOf('n=3') > 0, u);
  assert(!m.ghi.api.some(function (c) { return /Batch/.test(JSON.stringify(c)); }), 'khong dung toi Batch');
  // 2. Van con lo (ma cu chua tat): giu duong in theo lo nhu truoc
  m = moiTruong();
  vm.runInContext("mfgL = { batch: 'LO-1', lenh: '', item: 'TP001', name: 'X', qty: 1, meta: {} };", m.ctx);
  m.ctx.scrMfgLabel();
  assert(m.ghi.body.indexOf('LO-1') >= 0 && m.ghi.body.indexOf('Ngày:') < 0);
  m.els().mlOne.onclick();
  await new Promise(function (r) { setTimeout(r, 0); });
  assert(m.ghi.in[0].indexOf('/printview?doctype=Batch&name=LO-1') === 0, 'giu duong in theo lo: ' + m.ghi.in[0]);
  // 3. In ca nhom khi mon khong co lo: moi lenh mot xap, khong tao lo
  m = moiTruong();
  await m.ctx.mfgInTemNhom({ ma_mon: 'TP001', ten_mon: 'Bánh Su Kem', con: [
    { ten: 'WO-1', so_da: 4, so_can: 4 }, { ten: 'WO-2', so_da: 0, so_can: 2.5 }, { ten: 'WO-3', nhap: 1 } ] });
  assert.strictEqual(m.ghi.in.length, 2, 'lenh con nhap thi bo qua');
  assert(m.ghi.in[0].indexOf('lenh=WO-1') > 0 && m.ghi.in[0].indexOf('n=4') > 0, m.ghi.in[0]);
  assert(m.ghi.in[1].indexOf('lenh=WO-2') > 0 && m.ghi.in[1].indexOf('n=3') > 0, m.ghi.in[1]);
  assert.strictEqual(m.ghi.lo, 0, 'khong duoc tao hay doc lo');
  assert(!m.ghi.toast.some(function (t) { return /chưa bật theo dõi lô/.test(t); }));
  console.log('PASS 3 ca tem khong lo: man tem dong Ngay, giu duong co lo, in ca nhom theo lenh');
})().catch(function (e) { console.error(e); process.exitCode = 1; });
