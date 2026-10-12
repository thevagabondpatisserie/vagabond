/* Bo ca kiem HANH VI v583: mot phep tim cho moi o tim tren app.
 *
 * Anh Viet 07/10/2026: "go co dau, khong dau, dau phay, cham, ma,... go kieu
 * nao cung phai ra cai mon ay". Ca that De 06/10/2026: Phieu yeu cau san xuat
 * go "chocolatine mini" khong ra "Bánh Chocolatine, Mini size".
 *
 * Nap THAT vgbChuan, vgbKhop, getList, timList (00-nen.js), hopKhung, hoiChon,
 * vgbOTim, vgbNoiOTim (07-hop-thoai.js) vao DOM gia; chi thay api. Bang mau
 * dung CHUNG voi ca kiem Python (mau_tim/mau_tim_583.json), nen hai ben may
 * khach va may chu khong lech nhau duoc.
 *
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/tim_583.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), HOP = doc('07-hop-thoai.js');
var MAU = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'mau_tim', 'mau_tim_583.json'), 'utf8')).ca;

function layHam(src, ten) {
  var dau = src.indexOf('\nfunction ' + ten + '(');
  if (dau < 0) dau = src.indexOf('\nasync function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  dau += 1;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.message)); }
}
async function nghi() { for (var i = 0; i < 6; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

function dung_man() {
  var tai = dg.taiLieuGia();
  var goi = [];
  var that = {
    document: tai, console: console, Promise: Promise, JSON: JSON, String: String, Object: Object, RegExp: RegExp,
    setTimeout: function (f) { f(); return 1; },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); },
    api: function (m, a) { goi.push({ m: m, a: a }); return Promise.resolve([{ name: 'BANU00050' }]); },
  };
  that.window = that;
  var ma = [layHam(NEN, 'vgbChuan'), layHam(NEN, 'vgbKhop'), layHam(NEN, 'getList'), layHam(NEN, 'timList'),
    layHam(HOP, 'hopKhung'), layDong(HOP, 'var VGB_NGUONG_TIM'), layHam(HOP, 'vgbCanOTim'), layHam(HOP, 'vgbOTim'),
    layHam(HOP, 'vgbNoiOTim'), layHam(HOP, 'hoiChon')].join('\n');
  vm.runInNewContext(ma, that, { filename: 'tim583.js' });
  return { g: that, tai: tai, goi: goi };
}

(async function () {
  await ca('Bang mau chung: tung dong vgbKhop ra dung nhu may chu', async function () {
    var m = dung_man(), sai = [];
    MAU.forEach(function (d) { if (m.g.vgbKhop(d[0], d[1]) !== d[2]) sai.push(d[0] + ' / ' + d[1] + ' (' + d[3] + ')'); });
    bang('so dong sai', sai, []);
  });

  await ca('vgbKhop nhan mang cot, bo qua null', async function () {
    var m = dung_man();
    dung('ten + ma', m.g.vgbKhop(['Bánh Chocolatine, Mini size', null, 'BANU00050'], 'mini banu00050'));
    dung('thieu tu', !m.g.vgbKhop(['Bánh Chocolatine', 'BANU00008'], 'mini'));
  });

  await ca('Hop chon co o tim: go "chocolatine mini" chi con dung Bánh Chocolatine, Mini size', async function () {
    var m = dung_man();
    var ds = [
      { k: 'BANU00008', nhan: 'Bánh Chocolatine, Full size' },
      { k: 'BANU00050', nhan: 'Bánh Chocolatine, Mini size' },
      { k: 'BANU00064', nhan: 'Bông lan Chuối Đường đen' },
      { k: 'BAWC00001', nhan: 'Bánh Ổ Roman' },
      { k: 'BAWC00002', nhan: 'Bánh Croissant Avocado' },
      { k: 'BANU00030', nhan: 'Bánh Chocolate Brioche' },
      { k: 'BANU00016', nhan: 'Bánh Triple Chocolatine, Full size' },
    ];
    var p = m.g.hoiChon('Chọn món', '', ds, null);
    await nghi();
    var o = m.tai.body.querySelector('#hcTim');
    dung('co o tim', !!o);
    function hien() {
      return Array.prototype.filter.call(m.tai.body.querySelectorAll('[data-hc]'), function (el) { return el.style.display !== 'none'; })
        .map(function (el) { return el.getAttribute('data-hc'); });
    }
    o.value = 'chocolatine mini'; o.dispatchEvent(dg.suKien('input', {}, o)); await nghi();
    bang('chocolatine mini', hien(), ['BANU00050']);
    o.value = 'Mini, CHOCOLATINE.'; o.dispatchEvent(dg.suKien('input', {}, o)); await nghi();
    bang('dao thu tu, dau cau, hoa', hien(), ['BANU00050']);
    o.value = 'duong den'; o.dispatchEvent(dg.suKien('input', {}, o)); await nghi();
    bang('duong den', hien(), ['BANU00064']);
    o.value = 'banh o'; o.dispatchEvent(dg.suKien('input', {}, o)); await nghi();
    bang('banh o khong ra croissant', hien(), ['BAWC00001']);
    o.value = ''; o.dispatchEvent(dg.suKien('input', {}, o)); await nghi();
    bang('xoa o tim hien lai het', hien().length, ds.length);
    m.tai.body.querySelector('[data-hc="BANU00050"]').click(); await nghi();
    bang('bam chon dung mon', await p, 'BANU00050');
  });

  await ca('timList hoi may chu dung cua tim_kiem.tim, giu bo loc va cot', async function () {
    var m = dung_man();
    var r = await m.g.timList('Item', 'chocolatine mini', ['name', 'item_name'],
      { fields: ['name', 'item_name'], filters: { disabled: 0 }, limit_page_length: 300, order_by: 'item_name' });
    bang('ket qua', r, [{ name: 'BANU00050' }]);
    bang('mot luot hoi', m.goi.length, 1);
    var a = m.goi[0].a;
    bang('cua', m.goi[0].m, 'vagabond.tim_kiem.tim');
    bang('tu khoa nguyen van', a.tu_khoa, 'chocolatine mini');
    bang('cot', JSON.parse(a.cot), ['name', 'item_name']);
    bang('bo loc', JSON.parse(a.filters), { disabled: 0 });
    bang('so dong', a.gioi_han, 300);
  });

  console.log('Bo ca kiem HANH VI v583: mot phep tim cho moi o tim');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
