/* v677 (Codex #596): bảng BTP (/btp) ghi ĐÚNG số web nhận theo từng ngày.
 *
 * Bánh có đợt refill phủ ngày kia, ngày thứ ba thì web nhận theo đợt, không theo
 * BTP sẵn. Ô Web nhận của /btp phải đọc trường `web` (ba ngày, máy chủ tính bằng
 * chính phép của trang đặt bánh), không đọc `con_nhan` (chỉ là BTP sẵn còn nhận).
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/btp_web_677.js
 * Dùng DOM giả của bộ hành vi, nạp nguyên tệp trang, chỉ bắn sự kiện load.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var TEP = path.join(GOC, 'vagabond', 'trang', 'btp.js');

function moMan(bang) {
  var tai = dg.taiLieuGia();
  tai.body.innerHTML = '<span id="bt-luc"></span><button id="bt-them"></button><button id="bt-gieo"></button>'
    + '<div id="bt-bao"></div><div id="bt-luoi"></div>';
  tai.readyState = 'complete';
  var that = {
    console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number, Array: Array,
    Object: Object, RegExp: RegExp, Promise: Promise, parseInt: parseInt, isNaN: isNaN,
    setTimeout: setTimeout, clearTimeout: clearTimeout, setInterval: function () { return 0; },
    document: tai, location: {},
    fetch: function () {
      return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: bang }); } });
    },
  };
  that.window = that;
  that.window.addEventListener = function () {};
  vm.runInNewContext(fs.readFileSync(TEP, 'utf8'), that, { filename: 'btp.js' });
  return tai;
}

async function cho(tai) {
  for (var i = 0; i < 200; i++) {
    if (tai.getElementById('bt-luoi').querySelectorAll('.bt-o').length) return;
    await new Promise(function (r) { setTimeout(r, 0); });
  }
  throw new Error('Lưới /btp không vẽ');
}

function dong(web, con) {
  return { cap_nhat_luc: '', dong: [{ ma_hang: 'BAWC00068', ten_banh: 'Roman 18', hinh: '', so_btp: 10, so_decor: 6,
    dang_giu: 0, con_nhan: con, doi: {}, refill: [], web: web }] };
}

var ket = { dat: 0, hong: 0 };
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  dat   ' + ten); } catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function la(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }

(async function () {
  console.log('Bo ca kiem HANH VI trang /btp (DOM gia)');
  await ca('Codex #596: banh co dot refill ca ba ngay thi o Web nhan ghi 20 theo dot, khong ghi BTP 10', async function () {
    var tai = moMan(dong([['2026-11-11', 20, 'refill'], ['2026-11-12', 20, 'refill'], ['2026-11-13', 20, 'refill']], 10));
    await cho(tai);
    var chu = tai.getElementById('bt-luoi').textContent;
    la('ba o theo ngay', ['Web 11/11', 'Web 12/11', 'Web 13/11'].map(function (x) { return chu.indexOf(x) >= 0; }), [true, true, true]);
    var so = tai.getElementById('bt-luoi').querySelectorAll('.bt-web').map(function (x) { return x.querySelector('b').textContent; });
    la('so cua ba o', so, ['20', '20', '20']);
  });
  await ca('ngay mai theo phieu, ngay kia theo BTP; chua biet ghi dau hoi', async function () {
    var tai = moMan(dong([['2026-11-11', null, 'phieu'], ['2026-11-12', 4, 'btp'], ['2026-11-13', -1, 'btp']], 4));
    await cho(tai);
    var o = tai.getElementById('bt-luoi').querySelectorAll('.bt-web');
    la('so', o.map(function (x) { return x.querySelector('b').textContent; }), ['?', '4', '-1']);
    la('so am to do', (o[2].className || '').indexOf('am') >= 0, true);
  });
  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) process.exit(1);
})();
