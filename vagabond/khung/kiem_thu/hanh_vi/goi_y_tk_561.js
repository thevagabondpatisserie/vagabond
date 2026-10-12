/* v561: man Ghi so kiem ke dien san tai khoan ke toan chon lan truoc, va
 * ghi so xong thi bao may chu nho lai. Chay THAT kkpGoiYTk va kkpSubmit cua
 * 06-nhap-kho-kiem-ke.js voi may chu gia.
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/goi_y_tk_561.js
 */
'use strict';
var fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
var src = fs.readFileSync(path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '06-nhap-kho-kiem-ke.js'), 'utf8');
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
function moiTruong(goiY, hongGoiY) {
  var ghi = { api: [] };
  var ctx = {
    console: console, Math: Math, Date: Date, parseFloat: parseFloat, isNaN: isNaN,
    r3: function (x) { return Math.round(x * 1000) / 1000; },
    toast: function () {}, busy: function () {}, confirmSheet: async function () { return true; },
    shortWh: function (w) { return w; }, ymdOf: function () { return '2026-10-03'; }, hmOf: function () { return '09:00:00'; },
    COMPANY: 'TVD', reset: function () {}, go: function () {}, scrHome: 0, scrKkList: 0, kk: {},
    errMsg: function (e) { return String(e); }, kkBatchId: function (a, b) { return a + b; }, getList: async function () { return []; },
    api: async function (m, p) {
      ghi.api.push([m, p]);
      if (m === 'vagabond.kiem_ke.tk_goi_y') { if (hongGoiY) throw new Error('mat mang'); return goiY; }
      if (m === 'frappe.client.insert') return { name: 'MAT-RECO-1' };
      return {};
    }
  };
  vm.createContext(ctx);
  vm.runInContext(layHam('kkNum') + '\n' + layHam('kkpGoiYTk') + '\n' + layHam('kkpSubmit'), ctx);
  vm.runInContext("var kkp = { doc: { name: 'PKK-1', kho: 'Kho Bếp - TVD', pham_vi: 'NVL' }, rows: [{ item_code: 'NVL1', so_luong: 5, ton_he_thong: 5 }], rates: { NVL1: 1000 }, opening: 0, info: {}, cc: '', acc: '632 - TVD' };", ctx);
  return { ctx: ctx, ghi: ghi };
}
(async function () {
  // 1. Co lan truoc cho kho nay: dien san va ghi nguon
  var m = moiTruong({ tk: '811 - TVD', nguon: 'lan_truoc_kho' });
  await m.ctx.kkpGoiYTk();
  assert.strictEqual(vm.runInContext('kkp.acc', m.ctx), '811 - TVD');
  assert.strictEqual(vm.runInContext('kkp.accNguon', m.ctx), 'lan_truoc_kho');
  var hoi = m.ghi.api.find(function (c) { return c[0] === 'vagabond.kiem_ke.tk_goi_y'; });
  assert.strictEqual(JSON.stringify(hoi[1]), JSON.stringify({ kho: 'Kho Bếp - TVD', dau_ky: 0 }));
  // 2. Ghi so xong thi bao may chu nho dung tai khoan dang chon, sau khi da nop phieu
  vm.runInContext("kkp.acc = '6328 - TVD';", m.ctx);
  await m.ctx.kkpSubmit();
  var ten = m.ghi.api.map(function (c) { return c[0]; });
  var iNop = ten.indexOf('frappe.client.submit'), iNho = ten.indexOf('vagabond.kiem_ke.nho_tk');
  assert(iNop >= 0 && iNho > iNop, 'nho sau khi nop: ' + ten.join(','));
  assert.strictEqual(JSON.stringify(m.ghi.api[iNho][1]), JSON.stringify({ kho: 'Kho Bếp - TVD', tk: '6328 - TVD', dau_ky: 0 }));
  // 3. May chu khong tra loi thi giu mac dinh da dien
  m = moiTruong(null, true);
  await m.ctx.kkpGoiYTk();
  assert.strictEqual(vm.runInContext('kkp.acc', m.ctx), '632 - TVD');
  assert.strictEqual(vm.runInContext('kkp.accNguon', m.ctx), '');
  console.log('PASS 3 ca goi y tai khoan kiem ke: dien theo lan truoc, nho sau khi nop, mat mang giu mac dinh');
})().catch(function (e) { console.error(e); process.exitCode = 1; });
