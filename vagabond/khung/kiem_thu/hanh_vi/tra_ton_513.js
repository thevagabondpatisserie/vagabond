/* Bo ca kiem HANH VI cho man Tra ton kho (v513, anh Viet 20/09/2026).
 *
 * Chay THAT scrStock / stkChiTiet lay tu 05-san-xuat.js, DOM gia, api gia.
 * Chung minh: chip bam la goi may chu voi dung chip; sap xep cung vay; bam
 * mot dong la mo chi tiet cua DUNG ma; dong ton am va lo can han co nhan;
 * anh mon hien khi co, bieu tuong loai khi khong.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/tra_ton_513.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var SRC = fs.readFileSync(path.join(BEP, '05-san-xuat.js'), 'utf8');

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
function layDong(src, dau) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay dong ' + dau);
  return src.slice(i, src.indexOf('\n', i));
}

var DU_LIEU = {
  kho: 'Kho tổng 307 - TV',
  ds: [
    { ma: 'BPKG00001', ten: 'Túi Croissant', nhom: 'Bao bì', anh: '/files/tui.jpg', ton: 100, dvt: 'Cái', loai: 'bao_bi', can_han: 0, qua_han: 0 },
    { ma: 'NVLT00007', ten: 'Bơ lạt', nhom: 'Nguyên liệu', anh: '', ton: 12, dvt: 'Kg', loai: 'nguyen_lieu', can_han: 2, qua_han: 0 },
    { ma: 'CCDC00012', ten: 'Khay', nhom: 'Công cụ', anh: '', ton: -3, dvt: 'Cái', loai: 'ccdc', can_han: 0, qua_han: 0 },
  ],
  tong_dong: 3,
  dem: { '': 3, bao_bi: 1, ccdc: 1, nguyen_lieu: 1, btp: 0, thanh_pham: 0, khac: 0, can_han: 1, am: 1 },
  loai: [
    { ma: 'bao_bi', ten: 'Bao bì', icon: '🛍️' }, { ma: 'ccdc', ten: 'Công cụ', icon: '🧰' },
    { ma: 'nguyen_lieu', ten: 'Nguyên liệu', icon: '🥚' }, { ma: 'btp', ten: 'Bán thành phẩm', icon: '🥣' },
    { ma: 'thanh_pham', ten: 'Thành phẩm', icon: '🎂' }, { ma: 'khac', ten: 'Khác', icon: '📦' },
  ],
  tom_tat: '3 mã có tồn · ⏰ 1 mã có lô cận hạn hoặc quá hạn · ⚠ 1 mã tồn âm',
  xem_gia_tri: 0,
  ngay_can_han: 7,
};

function dungMan() {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, RegExp: RegExp, Promise: Promise, setTimeout: setTimeout, clearTimeout: clearTimeout,
    frame: function (t, html) { khung.innerHTML = html; return khung; },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: JSON.parse(JSON.stringify(ts || {})) });
      if (duong === 'vagabond.tra_ton.ton_kho') {
        var d = JSON.parse(JSON.stringify(DU_LIEU));
        if (ts.chip === 'am') { d.ds = d.ds.filter(function (x) { return x.ton < 0; }); d.tong_dong = 1; }
        return Promise.resolve(d);
      }
      if (duong === 'vagabond.tra_ton.chi_tiet_ma') {
        return Promise.resolve({ ma: ts.ma, ten: 'Bơ lạt', nhom: 'Nguyên liệu', anh: '', dvt: 'Kg', loai: 'nguyen_lieu', tong: 12,
          kho: [{ kho: 'Kho tổng 307 - TV', sl: 12 }], lo: [{ lo: 'LO-1', kho: 'Kho tổng 307 - TV', sl: 5, han: '2026-09-25', tt: 'can_han' }] });
      }
      return Promise.resolve({});
    },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
    num: function (n) { return String(n); }, money: function (n) { return String(n); },
    shortWh: function (w) { return String(w || '').replace(/ - TV$/, ''); },
    srchBox: function (id, ph, val) { return '<input id="' + id + '" value="' + (val || '') + '"><span id="' + id + 'scan"></span>'; },
    sheet: function () {}, whOpts: function () { return []; }, scanBarcode: function () { return Promise.resolve(null); },
    itemByBarcode: function () { return Promise.resolve(null); },
    busy: function () {}, toast: function () {}, errMsg: function (e) { return String(e); },
  };
  that.globalThis = that;
  var ma = [
    layDong(SRC, 'var stk = {'), layDong(SRC, 'var STK_SAP = ['),
    layHam(SRC, 'stkIcon'), layHam(SRC, 'stkAnh'), layHam(SRC, 'stkTag'), layHam(SRC, 'stkTai'),
    layHam(SRC, 'scrStock'), layHam(SRC, 'stkChiTiet'), layHam(SRC, 'stkSheetHtml'),
  ].join('\n');
  vm.runInNewContext(ma, that, { filename: '05-san-xuat.js#tra-ton' });
  return { g: that, tai: tai, khung: khung, goi: goi };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}
function bam(m, el) { el.dispatchEvent(dg.suKien('click', {}, el)); }

async function chayHet() {
  await ca('mo man: goi may chu voi kho dang chon, ve du chip va nhan', async function () {
    var m = dungMan();
    await m.g.scrStock(); await tick();
    bang('goi ton_kho', m.goi[0].duong, 'vagabond.tra_ton.ton_kho');
    bang('dung kho', m.goi[0].ts.kho, 'Kho tổng 307 - TV');
    var html = m.khung.innerHTML;
    dung('chip Tat ca co so 3', html.indexOf('Tất cả <b>3</b>') >= 0);
    dung('chip Bao bi', html.indexOf('Bao bì <b>1</b>') >= 0);
    dung('chip Can han hien vi co 1', html.indexOf('Cận hạn <b>1</b>') >= 0);
    dung('chip Ton am hien vi co 1', html.indexOf('Tồn âm <b>1</b>') >= 0);
    dung('chip Khac KHONG hien vi 0', html.indexOf('Khác <b>0</b>') < 0);
    dung('anh mon khi co', html.indexOf('src="/files/tui.jpg"') >= 0);
    dung('bieu tuong loai khi khong anh', html.indexOf('🥚') >= 0);
    dung('nhan lo can han', html.indexOf('2 lô cận hạn') >= 0);
    dung('nhan ton am', html.indexOf('Tồn âm</span>') >= 0);
    dung('tom tat', html.indexOf('3 mã có tồn') >= 0);
  });
  await ca('bam chip Ton am: goi lai may chu voi chip=am, danh sach chi con dong am', async function () {
    var m = dungMan();
    await m.g.scrStock(); await tick();
    var chip = m.khung.querySelectorAll('[data-sc]').filter(function (c) { return c.getAttribute('data-sc') === 'am'; })[0];
    dung('co chip am', !!chip);
    bam(m, chip); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1];
    bang('goi lai ton_kho', cuoi.duong, 'vagabond.tra_ton.ton_kho');
    bang('chip gui len', cuoi.ts.chip, 'am');
    var html = m.khung.innerHTML;
    dung('chip am dang on', /data-sc="am"/.test(html) && html.indexOf('chip on" data-sc="am"') >= 0);
    dung('chi con Khay', html.indexOf('Khay') >= 0 && html.indexOf('Túi Croissant') < 0);
  });
  await ca('bam sap xep Ton nhieu: goi may chu voi sap=nhieu', async function () {
    var m = dungMan();
    await m.g.scrStock(); await tick();
    var s = m.khung.querySelectorAll('[data-ss]').filter(function (c) { return c.getAttribute('data-ss') === 'nhieu'; })[0];
    bam(m, s); await tick(); await tick();
    bang('sap gui len', m.goi[m.goi.length - 1].ts.sap, 'nhieu');
  });
  await ca('bam mot dong: mo chi tiet cua DUNG ma, hien kho va lo can han', async function () {
    var m = dungMan();
    await m.g.scrStock(); await tick();
    var dong = m.khung.querySelectorAll('[data-sm]').filter(function (c) { return c.getAttribute('data-sm') === 'NVLT00007'; })[0];
    dung('co dong NVLT00007', !!dong);
    bam(m, dong); await tick(); await tick();
    var cuoi = m.goi[m.goi.length - 1];
    bang('goi chi_tiet_ma', cuoi.duong, 'vagabond.tra_ton.chi_tiet_ma');
    bang('dung ma', cuoi.ts.ma, 'NVLT00007');
    var tam = m.tai.body.children[m.tai.body.children.length - 1];
    var html = (tam.children[0] || tam).innerHTML;
    dung('tam chi tiet mo', html.indexOf('Chi tiết tồn') >= 0);
    dung('co ton theo kho', html.indexOf('TỒN THEO KHO') >= 0 && html.indexOf('Kho tổng 307') >= 0);
    dung('co lo can han voi HSD', html.indexOf('LO-1') >= 0 && html.indexOf('HSD 2026-09-25') >= 0 && html.indexOf('Cận hạn') >= 0);
  });
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI man Tra ton kho (v513)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) { console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e)); process.exit(1); });
