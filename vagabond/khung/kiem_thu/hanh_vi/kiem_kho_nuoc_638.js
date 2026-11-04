/* v638: mục "Đồ uống" trên bảng kiểm kho của quầy (trang /kiem-banh, tab Kiểm
 * bánh District 1 / NVHTN).
 *
 * Anh Việt duyệt 04/11/2026: bảng tự có TOÀN BỘ món nước của quầy, không đếm
 * số, chỉ có công tắc "Bán trên web" (tắt tới hết hôm nay, sáng mai tự bật).
 * Ca kiểm nạp THẬT bộ lọc KB_LOC và khối Kiểm kho điểm của kiem-banh.js vào DOM
 * giả, máy chủ giả trả bảng như kiem_kho.bang; bấm đúng chuỗi người dùng: mở
 * tab điểm, nhìn mục Đồ uống, bấm công tắc; đọc đúng cửa đã gọi.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/kiem_kho_nuoc_638.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(path.join(GOC, 'vagabond', 'trang', 'kiem-banh.js'), 'utf8');
/* Bộ lọc dùng chung KB_LOC (đầu tệp) và khối Kiểm kho điểm (khối cuối). Cắt
   theo mốc ở cột 0; tệp đổi cấu trúc thì phép cắt hỏng và ca nổ ngay. */
var dauLoc = SRC.indexOf('var KB_LOC = (function () {'), cuoiLoc = SRC.indexOf('\n}());', dauLoc);
var dauKk = SRC.lastIndexOf('\n(function () {');
if (dauLoc < 0 || cuoiLoc < 0 || dauKk < 0 || SRC.slice(dauKk).indexOf('vagabond.kiem_kho.') < 0) throw new Error('kiem-banh.js doi cau truc, sua phep cat');
var MA = SRC.slice(dauLoc, cuoiLoc + '\n}());'.length) + '\n' + SRC.slice(dauKk);

var HTML = '<div id="kb-tabs"></div><div id="kb-goc"></div><div id="kk" style="display:none">' +
  '<span id="kk-diem-to"></span><div id="kk-chips"></div><div id="kk-phu"></div>' +
  '<button id="kk-them"></button><button id="kk-chot"></button><button id="kk-mo-lai"></button><div id="kk-dachot"></div>' +
  '<div id="kk-bao"></div><div id="kk-them-hop" style="display:none"><input id="kk-tim"><div id="kk-goiy"></div></div>' +
  '<div id="kk-loc"></div><div id="kk-luoi"></div><div id="kk-nuoc"></div></div>';

function bangMay(suaWeb, tat) {
  return { diem: 'TCV', ngay: '2026-11-04', tinh_trang: 'Dang ban', sua_duoc: 1, sua_web: suaWeb, so_dot: 6, ghi_chu: '',
    dong: [{ ma_hang: 'BAWC00115', ten_banh: 'Mousse', hinh: '', ton_dau: 2, nhap: [0, 0, 0, 0, 0, 0], tong_nhap: 0, da_ban: 0, hong: 0,
      dieu_chinh: 0, co_the_ban: 2, kiem_tay: 0, da_kiem: 0, theo_doi: 1, lech: 0, ghi_chu: '' }],
    do_uong: [
      { ma_hang: 'NUTR00021', ten: 'Trà Hoa Lài', hinh: '', gia: 45000, nhom: 'Trà', ban_web: 1, den_ngay: '' },
      { ma_hang: 'NUCF00003', ten: 'Cà phê sữa', hinh: '', gia: 40000, nhom: 'Cà phê', ban_web: tat ? 0 : 1, den_ngay: tat ? '2026-11-04' : '' },
      { ma_hang: 'NUIC00002', ten: 'Kem Vani', hinh: '', gia: 30000, nhom: 'Ice Cream - Kem', ban_web: 1, den_ngay: '' }] };
}

function dungMan(canh) {
  var tai = dg.taiLieuGia();
  tai.body.innerHTML = HTML;
  tai.readyState = 'complete';
  tai.visibilityState = 'visible';
  var goi = [];
  var g = {
    console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, isNaN: isNaN, parseInt: parseInt, setTimeout: setTimeout, clearTimeout: clearTimeout,
    setInterval: function () { return 1; }, clearInterval: function () {},
    sessionStorage: { getItem: function () { return 'TCV'; }, setItem: function () {} },
    document: tai,
    fetch: function (duong, tuy) {
      var ten = String(duong).split('/api/method/vagabond.kiem_kho.')[1];
      var ts = JSON.parse((tuy && tuy.body) || '{}');
      goi.push({ ten: ten, ts: ts });
      var than = ten === 'diem_ds' ? [{ ma: 'TCV', ten: 'District 1', phu: '9 TCV' }]
        : ten === 'bang' ? canh.bang(goi) : { ok: 1 };
      return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: than }); } });
    }
  };
  g.window = g;
  g.window.addEventListener = function () {};
  g.window.confirm = function () { return true; };
  g.csrf_token = 'x';
  vm.runInNewContext(MA, g, { filename: 'kiem-banh-kk.js' });
  return { g: g, tai: tai, goi: goi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
async function choToi(mo, dk) { for (var i = 0; i < 200; i++) { if (dk()) return; await new Promise(function (r) { setTimeout(r, 0); }); } throw new Error('Cho mai khong thay: ' + mo); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}

(async function () {
  console.log('v638 bảng kiểm kho: mục Đồ uống');

  await ca('Mở tab District 1: mục "Đồ uống · 3 món · 1 đang tắt web", mỗi món một dòng có ảnh, giá, công tắc; không có ô đếm số', async function () {
    var m = dungMan({ bang: function () { return bangMay(1, true); } });
    await choToi('mục đồ uống', function () { return chu(m.tai.getElementById('kk-nuoc')).indexOf('Đồ uống') >= 0; });
    var o = m.tai.getElementById('kk-nuoc');
    dung('tiêu đề đếm', chu(o).indexOf('Đồ uống · 3 món · 1 đang tắt web') >= 0);
    var nut = o.querySelectorAll('[data-nuoc]');
    bang('ba công tắc', nut.map(function (n) { return [n.getAttribute('data-nuoc'), n.getAttribute('data-bat'), chu(n)]; }),
      [['NUTR00021', '1', 'Bán trên web'], ['NUCF00003', '0', 'Đang tắt web'], ['NUIC00002', '1', 'Bán trên web']]);
    bang('không có ô số trong mục đồ uống', o.querySelectorAll('.kb-o').length, 0);
    dung('câu giải thích sáng mai tự bán lại', chu(o).indexOf('sáng mai tự bán lại') >= 0);
  });

  await ca('Bấm tắt Trà: gọi kiem_kho.ban_web_do_uong đúng điểm, mã, bat 0, ngày đang xem; rồi tải lại bảng', async function () {
    var lan = 0;
    var m = dungMan({ bang: function () { lan++; return bangMay(1, false); } });
    await choToi('mục đồ uống', function () { return m.tai.getElementById('kk-nuoc').querySelectorAll('[data-nuoc]').length === 3; });
    var o = m.tai.getElementById('kk-nuoc');
    var nut = o.querySelector('[data-nuoc="NUTR00021"]');
    o.dispatchEvent(dg.suKien('click', {}, nut));
    await choToi('gọi công tắc', function () { return m.goi.some(function (x) { return x.ten === 'ban_web_do_uong'; }); });
    var x = m.goi.filter(function (x) { return x.ten === 'ban_web_do_uong'; })[0].ts;
    bang('tham số', [x.diem, x.ma_hang, x.bat], ['TCV', 'NUTR00021', 0]);
    dung('kèm ngày đang xem', /^\d{4}-\d{2}-\d{2}$/.test(x.ngay));
    await choToi('tải lại bảng', function () { return lan >= 2; });
  });

  await ca('Xem ngày cũ (máy chủ báo sua_web 0): công tắc tắt, bấm không gọi máy chủ, câu nói chỉ đổi được hôm nay', async function () {
    var m = dungMan({ bang: function () { return bangMay(0, false); } });
    await choToi('mục đồ uống', function () { return m.tai.getElementById('kk-nuoc').querySelectorAll('[data-nuoc]').length === 3; });
    var o = m.tai.getElementById('kk-nuoc');
    var nut = o.querySelector('[data-nuoc="NUTR00021"]');
    dung('nút tắt', nut.hasAttribute('disabled'));
    nut.disabled = true;
    o.dispatchEvent(dg.suKien('click', {}, nut));
    await new Promise(function (r) { setTimeout(r, 10); });
    bang('không gọi', m.goi.filter(function (x) { return x.ten === 'ban_web_do_uong'; }).length, 0);
    dung('câu', chu(o).indexOf('Chỉ đổi được ở ngày hôm nay') >= 0);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();
