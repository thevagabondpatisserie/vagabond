/* Ca kiểm HÀNH VI v671: khối "Tìm mã cũ để đẩy sang Pancake" của màn Danh mục sản phẩm
 * (17-cai-dat.js, dmTimChay). Minh Vũ chụp 18/11/2026: ba nút Đẩy, Kiểm lại, Lên web
 * bung to chồng lệch nhau (lớp "sm", "ghost" không có trong app) và combo bánh bò
 * chưa có giá chỉ biết khi bấm Lên web rồi bị báo lỗi.
 * Nạp THẬT dmTimChay cùng hàm nền vào DOM giả (khuôn mon_di_kem_668.js).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/tim_ma_web_671.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), CD = doc('17-cai-dat.js');
function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
var MA = ['h', 'anhMon'].map(function (t) { return layHam(NEN, t); })
  .concat(['dmChuWeb', 'dmTimChay', 'dmWebMot', 'dmDayMot', 'dmKiemMot'].map(function (t) { return layHam(CD, t); }))
  .concat(['var dmTimTu = "", dmTimTre = null, dmTimDs = null, dmTimTrang = 1, dmTimLuot = 0, dmVuaTao = null;']).join('\n');

function dungMoi(tra) {
  var tai = dg.taiLieuGia();
  var goc = new dg.ElementGia('div');
  goc.parentNode = tai.body; tai.body.children.push(goc);
  goc.innerHTML = '<div id="dmTimKq"></div>';
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt, navigator: {},
    api: function (duong, ts) { goi.push({ duong: duong, ts: ts }); return Promise.resolve(JSON.parse(JSON.stringify(tra))); }
  };
  that.window = that;
  vm.runInNewContext(MA, that, { filename: '17-cai-dat.js' });
  return { g: that, goc: goc, goi: goi };
}
var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); } catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

var MAU = { mon: [
  { name: 'KMCB00024', item_name: 'Combo 12 Bánh bò và sốt chấm', standard_rate: 0, day_duoc: 1, web: '', image: '' },
  { name: 'BACF00051', item_name: 'Bánh Stollen Cookie, Hũ 200 gr', standard_rate: 180000, day_duoc: 1, web: '', image: '' },
  { name: 'BAWC00139', item_name: 'Candle 12cm', standard_rate: 650000, day_duoc: 1, web: 'Đang hiện', image: '' },
  { name: 'XX0001', item_name: 'Mã ngừng dùng', standard_rate: 1, day_duoc: 0, web: '', image: '' }], con_nua: 1 };

(async function () {
  console.log('v671 Tìm mã cũ để đẩy sang Pancake');
  await ca('Combo bánh bò chưa có giá: nói ngay "Chưa có giá bán", không có nút Lên web; mã có giá chưa lên web có nút Lên web; mã đã lên web không có', async function () {
    var m = dungMoi(MAU);
    await m.g.dmTimChay(1);
    var web = m.goc.querySelectorAll('[data-dmweb]').map(function (b) { return b.getAttribute('data-dmweb'); });
    bang('nút Lên web chỉ cho mã có giá, chưa lên web', web, ['BACF00051']);
    dung('câu chưa có giá bán', chu(m.goc).indexOf('Chưa có giá bán: nhờ kế toán đặt giá ở hồ sơ món') >= 0);
    bang('nút Đẩy cho mọi mã đẩy được', m.goc.querySelectorAll('[data-dmday]').length, 3);
    dung('mã ngừng dùng ghi rõ', chu(m.goc).indexOf('Ngừng dùng hoặc không phải hàng bán') >= 0);
  });
  await ca('Mọi nút của khối cao 44 điểm, rộng theo chữ, nằm trong một hàng có xuống dòng; không còn lớp không có thật (sm, ghost)', async function () {
    var m = dungMoi(MAU);
    await m.g.dmTimChay(2);
    var nut = m.goc.querySelectorAll('button');
    dung('có nút', nut.length >= 9);
    var sai = nut.filter(function (b) {
      var st = String(b.getAttribute('style') || ''), lop = String(b.className || '').split(/\s+/);
      return st.indexOf('min-height:44px') < 0 || st.indexOf('width:auto') < 0 || lop.indexOf('sm') >= 0 || lop.indexOf('ghost') >= 0;
    }).map(function (b) { return chu(b); });
    bang('nút sai chuẩn', sai, []);
    dung('có Trang trước và Trang sau', !!m.goc.querySelector('#dmTruoc') && !!m.goc.querySelector('#dmSau'));
  });
  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
