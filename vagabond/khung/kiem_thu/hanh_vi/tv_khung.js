/* Khung chạy THẬT trang /thanh-vien (www/thanh-vien.html + web_order/chu.js +
 * web_order/thanh-vien.js) trên DOM giả. Máy chủ là bản giả ghi lại từng lời
 * gọi /api/method/vagabond.thanh_vien.*; ca kiểm bấm, gõ như khách rồi đọc
 * đúng tham số máy chủ nhận được và chữ khách thấy.
 *
 * Dùng chung cho thanh_vien_245.cjs và thanh_vien_621.js (v621).
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
function doc(t) { return fs.readFileSync(path.join(GOC, t), 'utf8'); }

async function nghi(n) { for (var k = 0; k < (n || 3); k++) { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); } }

/* tra: { ten_ham: function (thamSo) -> message } */
async function dungTrang(tra, timKiem) {
  var html = doc('vagabond/www/thanh-vien.html');
  var main = html.slice(html.indexOf('<main'), html.indexOf('</main>') + 7);
  var tl = dg.taiLieuGia();
  dg.doc(main, tl.body);
  var goc = tl.querySelector.bind(tl);
  tl.querySelector = function (chon) { return chon === 'meta[name=csrf-token]' ? { content: 'csrf-gia' } : goc(chon); };
  var goi = [], qr = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise,
    Error: Error, RegExp: RegExp, Date: Date, URLSearchParams: URLSearchParams, setTimeout: setTimeout, clearTimeout: clearTimeout,
    document: tl, location: { search: timKiem || '', origin: 'https://thevagabond.vn', assign: function (u) { goi.push({ ham: '__di', a: u }); } },
    __goi: goi, __qr: qr,
    qrcode: function () {
      var nd = '';
      return { addData: function (x) { nd = x; }, make: function () {}, createDataURL: function () { qr.push(nd); return 'data:image/gif;base64,R0lG'; } };
    },
    fetch: async function (url, c) {
      var ham = String(url).split('vagabond.thanh_vien.')[1];
      var a = c && c.body ? JSON.parse(c.body) : null;
      goi.push({ ham: ham, a: a, csrf: c && c.headers && c.headers['X-Frappe-CSRF-Token'] });
      var f = tra[ham];
      var m = typeof f === 'function' ? f(a) : (f || { ok: 1 });
      return { ok: true, json: async function () { return { message: m }; } };
    },
  };
  g.window = g;
  g.scrollTo = function () {};
  vm.createContext(g);
  vm.runInContext(doc('vagabond/public/web_order/chu.js').split('(function ()')[0], g);
  vm.runInContext(doc('vagabond/public/web_order/thanh-vien.js'), g);
  await nghi(4);
  return { g: g, tl: tl, goi: goi, qr: qr, tim: function (id) { return tl.getElementById(id); },
    cac: function (ham) { return goi.filter(function (x) { return x.ham === ham; }); } };
}

function an(el) { return !el || el.hasAttribute('hidden'); }

module.exports = { dungTrang: dungTrang, nghi: nghi, an: an, dg: dg };
