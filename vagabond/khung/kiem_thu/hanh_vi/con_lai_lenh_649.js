/* v649, Codex #552 vòng 2: số còn phải làm của một lệnh sản xuất phải trừ cả
 * hao hụt đã ghi (process_loss_qty), như ERPNext đóng lệnh khi
 * produced_qty + process_loss_qty >= qty. Một hàm mfgConLai cho mọi nơi.
 *
 * Nạp THẬT mfgConLai, mfgChayHoanTat (nút Hoàn tất, cả nút ✓ nhanh) và
 * openWoQty (Kế hoạch đếm hàng đang làm) của 05-san-xuat.js, máy chủ giả chỉ
 * trả đúng các cột app xin như Frappe thật.
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/con_lai_lenh_649.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '05-san-xuat.js'), 'utf8');

function layHam(src, ten) {
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

var ket = { dat: 0, hong: 0 };
function bang(mo, a, b) {
  if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}
async function ca(ten, fn) {
  try { await fn(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message || e)); }
}

function theGioi(lenhMay) {
  var nhat = { toast: [], sheet: [] };
  var the = {
    console: console, Math: Math, JSON: JSON, Object: Object, Array: Array, Promise: Promise, String: String,
    WODONE: ['Completed', 'Stopped', 'Closed', 'Cancelled'], WOST: {},
    r3: function (n) { return Math.round(n * 1000) / 1000; },
    num: function (n) { return String(n); },
    toast: function (c) { nhat.toast.push(c); },
    mfgSheetHoanTat: async function (left) { nhat.sheet.push(left); return null; },
    inChunks: async function (codes, n, fn) { return fn(codes); },
    getList: async function (dt, o) {
      if (dt !== 'Work Order') throw new Error('getList la: ' + dt);
      return (lenhMay || []).map(function (w) {
        var r = {};
        (o.fields || []).forEach(function (k) { if (k in w) r[k] = w[k]; });
        return r;
      });
    }
  };
  vm.createContext(the);
  ['mfgConLai', 'mfgChayHoanTat', 'openWoQty'].forEach(function (t) { vm.runInContext(layHam(SRC, t), the); });
  the.nhat = nhat;
  return the;
}

(async function () {
  /* Lệnh 10 cái, đã làm 6, ghi hao 3: chỉ còn 1. */
  var HAO = { name: 'WO-HAO', production_item: 'X', qty: 10, produced_qty: 6, process_loss_qty: 3, status: 'In Process', stock_uom: 'Cái', docstatus: 1 };

  await ca('1. nut Hoan tat: lenh 10, da lam 6, hao 3: hop hoi so chi cho toi da 1, khong phai 4', async function () {
    var t = theGioi();
    await t.mfgChayHoanTat(Object.assign({}, HAO), null);
    bang('so con lai dua vao hop', t.nhat.sheet, [1]);
  });

  await ca('2. nut Hoan tat: da lam 6 + hao 4 = 10: bao da lam du, khong mo hop', async function () {
    var t = theGioi();
    var kq = await t.mfgChayHoanTat(Object.assign({}, HAO, { process_loss_qty: 4 }), null);
    bang('khong mo hop', [kq, t.nhat.sheet], [0, []]);
    bang('bao da du', t.nhat.toast, ['Lệnh này đã làm đủ số rồi']);
  });

  await ca('3. Ke hoach dem hang dang lam: lenh co hao chi tinh phan con that (1), lenh khong hao tinh du', async function () {
    var t = theGioi([HAO, { production_item: 'X', qty: 5, produced_qty: 2, status: 'In Process' }]);
    var m = await t.openWoQty(['X']);
    bang('dang lam X', m, { X: 4 });
  });

  console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
  process.exit(ket.hong ? 1 : 0);
})();
