/* Bo ca kiem HANH VI: man Mo ma hang bo luot xem truoc ve tre (v525, Codex #365 v2).
 *
 * Nguoi dung doi nhom hoac go them ten trong luc mot luot xem truoc dang cho
 * may tra loi. Luot cu ve SAU luot moi thi khong duoc de len ket qua dang hien,
 * neu khong man bay ma du kien, mon trung va cau "Di 242" cua form cu.
 *
 * Nap THAT dmHoiXem (17-cai-dat.js). Chi thay api, dmVeXem va dong ho.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/xem_truoc_tre_525.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'bep', '17-cai-dat.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

function dung_man(ve) {
  var cho = [], hen = [], xem = [];
  var g = {
    JSON: JSON, String: String, Promise: Promise,
    dmVe: ve, dmKq: null, dmTre: null, dmHoiLuot: 0,
    api: function (m, a) { return new Promise(function (tra) { cho.push({ a: JSON.parse(JSON.stringify(a)), tra: tra }); }); },
    dmVeXem: function () { xem.push(g.dmKq); },
    setTimeout: function (f) { hen.push(f); return hen.length; },
    clearTimeout: function () {},
  };
  vm.createContext(g);
  // dmHoiLuot la bien cap tep; nap cung ham de ca kiem khong phu thuoc no co hay khong.
  vm.runInContext(layHam(SRC, 'dmHoiXem'), g);
  return { g: g, cho: cho, hen: hen, xem: xem };
}

(async function () {
  await ca('doi nhom trong luc cho: luot cu ve sau khong de len ket qua cua nhom moi', async function () {
    var m = dung_man({ nhom: 'Công cụ Dụng cụ', loai: 'nvl', ten: 'Quạt đứng', quy_cach: '' });
    m.g.dmHoiXem(); var l1 = m.hen[m.hen.length - 1]();
    m.g.dmVe.nhom = 'Bao bì';
    m.g.dmHoiXem(); var l2 = m.hen[m.hen.length - 1]();
    m.cho[1].tra({ ma_du_kien: 'BB00010', canh_bao: [] }); await l2;
    m.cho[0].tra({ ma_du_kien: 'CCDC00300', canh_bao: ['Đi 242'] }); await l1;
    bang('hai luot da hoi', m.cho.map(function (c) { return c.a.nhom; }), ['Công cụ Dụng cụ', 'Bao bì']);
    bang('ket qua dang giu la cua nhom moi', m.g.dmKq && m.g.dmKq.ma_du_kien, 'BB00010');
    bang('man chi ve ket qua moi', m.xem.map(function (k) { return k && k.ma_du_kien; }), ['BB00010']);
  });
  await ca('go them ten trong luc cho: luot cu ve sau khong de len luot moi', async function () {
    var m = dung_man({ nhom: 'Công cụ Dụng cụ', loai: 'nvl', ten: 'Quạt', quy_cach: '' });
    m.g.dmHoiXem(); var l1 = m.hen[m.hen.length - 1]();
    m.g.dmVe.ten = 'Quạt đứng Midea';
    m.g.dmHoiXem(); var l2 = m.hen[m.hen.length - 1]();
    m.cho[1].tra({ ten_day_du: 'Quạt đứng Midea' }); await l2;
    m.cho[0].tra({ ten_day_du: 'Quạt' }); await l1;
    bang('ten dang hien la cua luot moi', m.g.dmKq && m.g.dmKq.ten_day_du, 'Quạt đứng Midea');
  });
  await ca('doi nhom truoc khi luot moi kip gui: ket qua cua nhom cu ve thi bo', async function () {
    var m = dung_man({ nhom: 'Công cụ Dụng cụ', loai: 'nvl', ten: 'Quạt', quy_cach: '' });
    m.g.dmHoiXem(); var l1 = m.hen[m.hen.length - 1]();
    // Nguoi vua doi nhom, hen 320ms cua luot moi chua toi thi luot cu ve.
    m.g.dmVe.nhom = 'Bao bì';
    m.cho[0].tra({ ma_du_kien: 'CCDC00300', canh_bao: ['Đi 242'] }); await l1;
    bang('khong giu ket qua nhom cu', m.g.dmKq, null);
    bang('khong ve ket qua nhom cu', m.xem.length, 0);
  });
  await ca('mot luot binh thuong van ve va hien', async function () {
    var m = dung_man({ nhom: 'Công cụ Dụng cụ', loai: 'nvl', ten: 'Quạt', quy_cach: '' });
    m.g.dmHoiXem(); var l1 = m.hen[m.hen.length - 1]();
    m.cho[0].tra({ ma_du_kien: 'CCDC00300' }); await l1;
    bang('hien ket qua', m.xem.map(function (k) { return k && k.ma_du_kien; }), ['CCDC00300']);
  });
  console.log('Bo ca kiem HANH VI luot xem truoc ve tre (v525)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
