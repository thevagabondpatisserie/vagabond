/* Bo ca kiem HANH VI v697: muc "Kem theo moi banh" o the Banh cua trinh bien tap.
 *
 * Anh Viet chot 27/11/2026 (Danh sach co dinh): moi banh Marketing tich chon do
 * kem, banh nhieu size chon ap cho size nao; chua chon thi banh theo bo mac
 * dinh. Nhan vien bao Buche thieu nen xoan, dao go, co cam; Minh Vu bao Panettone
 * lon va Mini dung chung mot o Tui.
 *
 * Nap THAT chuyen-muc.js, bien-tap-moi.js va du-lieu.js (danh muc do kem cua
 * trang khach); chi may chu la ban gia giu dung hop dong banh_web.py
 * (ds_bien_tap, luu). Ca bam nhu nguoi dung, khong goi ham noi bo.
 *
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/bien_tap_kem_697.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var url = require('url');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var WEB = path.join(GOC, 'vagabond', 'public', 'web_order');
function doc(t) { return fs.readFileSync(path.join(WEB, t), 'utf8'); }

var ket = { dat: 0, hong: 0, loi: [] };
var xongHet = false;
process.on('exit', function () { if (!xongHet) { console.log('  HONG  bo kiem dung giua chung: co loi hua treo mai'); process.exitCode = 1; } });
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) { try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : e)); } }
async function nghi() { for (var i = 0; i < 16; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

var AN = 'Đã ẩn', HIEN = 'Đang hiện';
function mayChu(kemPan) {
  return [
    { khoa: 'classic panettone', ten: 'Classic Panettone', trang_thai: AN, mua_vu: 1, loai: 'panettone', anh: [], mo_ta: '', tang: '', ma_hang: ['GIA-P1', 'GIA-P2'],
      kem_theo: kemPan === undefined ? null : kemPan,
      sizes: [{ ma: 'GIA-P1', cm: 0, gia: 780000, nhan: 'Bánh Lớn 680gr' }, { ma: 'GIA-P2', cm: 0, gia: 320000, nhan: 'Bánh Mini 250gr' }] },
    { khoa: 'greenwood buche', ten: 'Greenwood Bûche', trang_thai: AN, mua_vu: 1, loai: 'buche', anh: [], mo_ta: '', tang: '', ma_hang: ['GIA-B1'], kem_theo: null,
      sizes: [{ ma: 'GIA-B1', cm: 0, gia: 900000, nhan: 'Greenwood Bûche' }] },
    { khoa: 'very berry', ten: 'Very Berry', trang_thai: HIEN, mua_vu: 0, loai: '', anh: [{ url: '/files/vb.png', bam: 'aa' }], mo_ta: '', tang: '', ma_hang: ['GIA-V12', 'GIA-V16'], kem_theo: null,
      sizes: [{ ma: 'GIA-V12', cm: 12, gia: 620000, nhan: 'Very Berry 12cm' }, { ma: 'GIA-V16', cm: 16, gia: 900000, nhan: 'Very Berry 16cm' }] },
  ];
}

function appMoi(DL, tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc('<main id="bt-moi"><p id="bt-trang-thai"></p><nav id="bt-the"></nav><div id="bt-noi"></div></main><div id="bt-cu" hidden><button id="tai-lai"></button><button id="bt-ve-moi"></button></div>', tl.body);
  var banh = mayChu(tuy.kemPan);
  var B = { khoi: [], dau: {}, thong_tin: { cua_hang: [] }, dau_thong_tin: {}, lien_he: {}, dau_lien_he: '', nhan: { mv_kem_tui_pan: 'Túi giấy Panettone' }, nhan_mau: {}, nhom_nhan: {},
    ve: {}, hom_nay: '2026-11-27', uu_dai_erp: [], tuyen_dung_erp: [], nhap_chua_xuat_ban: 0, phien_ban: 1, banh_cho_anh: 0 };
  var goi = [];
  function tra(msg) { return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: msg }); } }); }
  function goiDs() { return JSON.parse(JSON.stringify({ banh: banh, dem: { 'Chờ ảnh': 0, 'Đang hiện': 1, 'Đã ẩn': 2 } })); }
  function fetchGia(u, cau) {
    var ham = String(u).split('.').pop();
    var a = cau && cau.body ? JSON.parse(cau.body) : null;
    goi.push({ ham: ham, a: a });
    if (ham === 'bang_moi') return tra(JSON.parse(JSON.stringify(B)));
    if (ham === 'ds_bien_tap') return tra(goiDs());
    if (ham === 'luu') {
      var y = banh.find(function (b) { return b.khoa === a.khoa; });
      /* Giữ đúng hợp đồng banh_web.luu: chuỗi rỗng là về mặc định, mảng là chọn riêng. */
      if (a.kem_theo === '') y.kem_theo = null;
      else if (Array.isArray(a.kem_theo)) y.kem_theo = a.kem_theo;
      var r = goiDs(); r.khoa = a.khoa; return tra(r);
    }
    throw new Error('may chu gia khong biet ' + ham);
  }
  var docu = {
    body: tl.body, readyState: 'complete',
    createElement: tl.createElement, getElementById: tl.getElementById,
    addEventListener: function () {},
    querySelector: function (c) { return c.indexOf('meta') === 0 ? { content: 'csrf' } : tl.querySelector(c); },
    querySelectorAll: function (c) { return tl.querySelectorAll(c); },
  };
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise, Error: Error,
    RegExp: RegExp, Date: Date, Intl: Intl, Set: Set, parseInt: parseInt, encodeURIComponent: encodeURIComponent, document: docu, fetch: fetchGia,
    FormData: function () {} };
  g.window = g;
  /* Trang thật nạp du-lieu.js bằng import(); trong node nạp sẵn đúng tệp đó vào chỗ trình biên tập giữ dữ liệu. */
  if (DL) g.VgbDuLieuWeb = DL;
  vm.createContext(g);
  vm.runInContext(doc('chuyen-muc.js'), g, { filename: 'chuyen-muc.js' });
  vm.runInContext(doc('bien-tap-moi.js'), g, { filename: 'bien-tap-moi.js' });
  var app = {
    banh: banh, goi: goi,
    tim: function (c) { return tl.body.querySelectorAll(c); },
    mot: function (c) { var r = tl.body.querySelectorAll(c); if (r.length !== 1) throw new Error('mong dung 1 ' + c + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); },
    cuoi: function (ham) { var r = goi.filter(function (x) { return x.ham === ham; }); return r[r.length - 1]; },
    bao: function () { return String(tl.getElementById('bt-trang-thai').textContent); },
    the: async function (k) { await app.bam(app.mot('[data-the="' + k + '"]')); await nghi(); await nghi(); },
    chon: async function (khoa) { await app.bam(app.mot('[data-banh="' + khoa + '"]')); },
    /* Các đồ kèm đang bật: [mã, size đang chọn] như người dùng thấy trên màn. */
    dangBat: function () {
      return app.tim('[data-kem]').filter(function (h) { return /(^| )dang( |$)/.test(h.className); }).map(function (h) {
        var c = h.querySelectorAll('[data-kem-size]').filter(function (x) { return /(^| )dang( |$)/.test(x.className); }).map(function (x) { return x.dataset.kemSize; });
        return [h.dataset.kem, c.join(',')];
      });
    },
    nutKem: function (ma) { return app.mot('[data-kem="' + ma + '"]').querySelector('.bt-kem-nut'); },
    chipSize: function (ma, sz) { return app.mot('[data-kem="' + ma + '"]').querySelectorAll('[data-kem-size]').find(function (x) { return x.dataset.kemSize === sz; }); },
    trangThai: function () { return String(app.mot('[data-kem-theo]').querySelector('.bt-kem-dau').querySelector('.bt-tt').textContent); },
    luu: async function () { await app.bam(app.mot('[data-luu-banh]')); await nghi(); },
  };
  return app;
}

(async function () {
  var DL = await import(url.pathToFileURL(path.join(GOC, 'vagabond', 'public', 'web_vue', 'banh', 'du-lieu.js')).href);

  await ca('Panettone chua chon: hien bo mac dinh, banh lon va Mini moi size mot hop, mot tui; ten sua o Trang va chu duoc dung', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('classic panettone');
    bang('trang thai', app.trangThai(), 'Bộ mặc định');
    bang('dang bat', app.dangBat(), [['hop_pan_lon', 'GIA-P1'], ['hop_pan_mini', 'GIA-P2'], ['tui_pan_lon', 'GIA-P1'], ['tui_pan_mini', 'GIA-P2'], ['thiep_noel', '']]);
    dung('ten tui lon theo chu Marketing da sua', String(app.mot('[data-kem="tui_pan_lon"]').textContent).indexOf('Túi giấy Panettone') >= 0);
    dung('tui Mini la mot dong rieng', String(app.mot('[data-kem="tui_pan_mini"]').textContent).indexOf('Túi Panettone Mini') >= 0);
    bang('du 13 do kem de chon', app.tim('[data-kem]').length, 13);
  });

  await ca('Buche chua chon: mac dinh co nen xoan, dao go, co cam; banh mot size khong hien chip size', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('greenwood buche');
    bang('dang bat', app.dangBat().map(function (x) { return x[0]; }), ['dao_go', 'nen_xoan', 'co_cam', 'hop_buche', 'tui_buche', 'thiep_buche']);
    bang('khong chip size', app.tim('[data-kem-size]').length, 0);
  });

  await ca('Them dao go cho Panettone roi Luu: gui du bo da trai theo size cong dao go Moi size; may chu nhan, trang thai Da chon rieng', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('classic panettone');
    await app.bam(app.nutKem('dao_go'));
    bang('trang thai', app.trangThai(), 'Đã chọn riêng');
    await app.luu();
    bang('gui len may chu', app.cuoi('luu').a.kem_theo, [{ ma: 'dao_go', size: '' }, { ma: 'hop_pan_lon', size: 'GIA-P1' }, { ma: 'hop_pan_mini', size: 'GIA-P2' },
      { ma: 'tui_pan_lon', size: 'GIA-P1' }, { ma: 'tui_pan_mini', size: 'GIA-P2' }, { ma: 'thiep_noel', size: '' }]);
    dung('bao da luu', app.bao().indexOf('Đã lưu') >= 0);
    bang('mo lai van la ban rieng', app.trangThai(), 'Đã chọn riêng');
  });

  await ca('Chip size: tui Mini ap them cho banh lon; bo het size thi ve Moi size; Moi size thay moi size le', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('classic panettone');
    await app.bam(app.chipSize('tui_pan_mini', 'GIA-P1'));
    bang('tui Mini hai size', app.dangBat().filter(function (x) { return x[0] === 'tui_pan_mini'; }), [['tui_pan_mini', 'GIA-P1,GIA-P2']]);
    await app.bam(app.chipSize('tui_pan_mini', 'GIA-P1'));
    await app.bam(app.chipSize('tui_pan_mini', 'GIA-P2'));
    bang('bo size cuoi thi ve Moi size', app.dangBat().filter(function (x) { return x[0] === 'tui_pan_mini'; }), [['tui_pan_mini', '']]);
    await app.bam(app.chipSize('hop_pan_lon', ''));
    bang('hop lon Moi size', app.dangBat().filter(function (x) { return x[0] === 'hop_pan_lon'; }), [['hop_pan_lon', '']]);
    await app.luu();
    var gui = app.cuoi('luu').a.kem_theo.filter(function (e) { return e.ma === 'hop_pan_lon' || e.ma === 'tui_pan_mini'; });
    bang('gui dung size', gui, [{ ma: 'hop_pan_lon', size: '' }, { ma: 'tui_pan_mini', size: '' }]);
  });

  await ca('Bat roi tat lai dung bo mac dinh: van la Bo mac dinh, khong hoi luu; Luu gui chuoi rong (giu theo mac dinh)', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('greenwood buche');
    await app.bam(app.nutKem('tui_vai'));
    bang('dang chon rieng', app.trangThai(), 'Đã chọn riêng');
    await app.bam(app.nutKem('tui_vai'));
    bang('ve mac dinh', app.trangThai(), 'Bộ mặc định');
    await app.chon('very berry');
    bang('doi banh khong hoi', app.tim('[data-hop-thoi]').length + app.tim('[data-hop-co]').length, 0);
    await app.luu();
    bang('banh thuong mac dinh: gui chuoi rong', app.cuoi('luu').a.kem_theo, '');
    bang('banh thuong hai size, mac dinh Moi size', app.dangBat(), [['hop_banh', ''], ['tui_vai', ''], ['dao_go', ''], ['nen_xoan', ''], ['co_cam', '']]);
  });

  await ca('Bo het do kem: gui mang rong (khong bi thay bang mac dinh); Ve mac dinh gui chuoi rong', async function () {
    var app = appMoi(DL); await nghi(); await app.the('banh');
    await app.chon('greenwood buche');
    var ds = app.dangBat().map(function (x) { return x[0]; });
    for (var i = 0; i < ds.length; i++) await app.bam(app.nutKem(ds[i]));
    bang('khong con do kem', app.dangBat(), []);
    await app.luu();
    bang('gui mang rong', app.cuoi('luu').a.kem_theo, []);
    bang('may chu giu mang rong', app.banh[1].kem_theo, []);
    bang('van la chon rieng', app.trangThai(), 'Đã chọn riêng');
    await app.bam(app.mot('[data-kem-mac-dinh]'));
    await app.luu();
    bang('ve mac dinh', [app.cuoi('luu').a.kem_theo, app.banh[1].kem_theo, app.trangThai()], ['', null, 'Bộ mặc định']);
  });

  await ca('Banh da chon rieng tu truoc: hien dung ban da luu; luu bo khac khong dong vao do kem', async function () {
    var app = appMoi(DL, { kemPan: [{ ma: 'thiep_noel', size: '' }, { ma: 'tui_pan_mini', size: 'GIA-P2' }] }); await nghi(); await app.the('banh');
    await app.chon('classic panettone');
    bang('dung ban da luu', app.dangBat(), [['tui_pan_mini', 'GIA-P2'], ['thiep_noel', '']]);
    await app.luu();
    bang('gui lai dung ban da luu', app.cuoi('luu').a.kem_theo, [{ ma: 'thiep_noel', size: '' }, { ma: 'tui_pan_mini', size: 'GIA-P2' }]);
  });

  await ca('Khong nap duoc danh muc do kem: bao cau co huong xu ly, van luu duoc anh va chu, khong xoa do kem da chon', async function () {
    var app = appMoi(null, { kemPan: [{ ma: 'thiep_noel', size: '' }] }); await nghi(); await app.the('banh');
    await app.chon('classic panettone'); await nghi(); await nghi();
    dung('cau bao', String(app.mot('[data-kem-theo]').textContent).indexOf('Chưa tải được danh sách đồ kèm') >= 0);
    await app.luu();
    bang('gui lai ban da luu', app.cuoi('luu').a.kem_theo, [{ ma: 'thiep_noel', size: '' }]);
  });

  xongHet = true;
  console.log('Bo ca kiem HANH VI v697: Kem theo moi banh o the Banh');
  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) process.exitCode = 1;
}());
