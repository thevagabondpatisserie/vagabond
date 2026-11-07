/* Bo ca kiem HANH VI v644: the Banh cua trinh bien tap website.
 *
 * Anh Viet 07/11/2026 (duyet mau cung ngay): anh, mo ta, tang huong vi tung
 * BANH (moi size dung chung) quan o the Banh; banh chua co anh thi khach
 * khong thay; anh trung (cung tam, khac ten tep) may khong them lan nua.
 *
 * Nap THAT chuyen-muc.js va bien-tap-moi.js vao DOM gia; chi may chu la ban
 * gia (giu dung hop dong cua banh_web.py: ds_bien_tap, them_anh, luu). Ca kiem
 * bam, go, chon tep nhu nguoi dung, khong goi ham noi bo nao.
 *
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/bien_tap_banh_644.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
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

var CHO = 'Chờ ảnh', HIEN = 'Đang hiện', AN = 'Đã ẩn';
function mayChu() {
  var banh = [
    { khoa: 'very berry', ten: 'Very Berry', trang_thai: HIEN, anh: [{ url: '/files/vb.png', bam: 'aa' }, { url: 'https://p/can.jpg', bam: 'bb' }],
      mo_ta: 'Vỏ sô cô la.', tang: 'Vỏ - shell', ma_hang: ['BAWC00086', 'BAWC00087'], sizes: [{ ma: 'BAWC00086', cm: 12, gia: 620000 }, { ma: 'BAWC00087', cm: 16, gia: 900000 }] },
    { khoa: 'banh moi', ten: 'Bánh Mới', trang_thai: CHO, anh: [], mo_ta: '', tang: '', ma_hang: ['BAWC00200'], sizes: [{ ma: 'BAWC00200', cm: 16, gia: 700000 }] },
    { khoa: 'hannari', ten: 'Hannari', trang_thai: AN, anh: [{ url: '/files/h.png', bam: 'cc' }], mo_ta: '', tang: '', ma_hang: ['BAWC00024'], sizes: [{ ma: 'BAWC00024', cm: 0, gia: 650000 }] },
  ];
  return banh;
}
function dem(banh) { var d = {}; d[CHO] = 0; d[HIEN] = 0; d[AN] = 0; banh.forEach(function (x) { d[x.trang_thai]++; }); return d; }

function appMoi(tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc('<main id="bt-moi"><p id="bt-trang-thai"></p><nav id="bt-the"></nav><div id="bt-noi"></div></main><div id="bt-cu" hidden><button id="tai-lai"></button><button id="bt-ve-moi"></button></div>', tl.body);
  var banh = mayChu();
  var B = { khoi: [], dau: {}, thong_tin: { cua_hang: [] }, dau_thong_tin: {}, lien_he: {}, dau_lien_he: '', nhan: {}, nhan_mau: {}, nhom_nhan: {},
    ve: {}, hom_nay: '2026-11-07', uu_dai_erp: [], tuyen_dung_erp: [], nhap_chua_xuat_ban: 0, phien_ban: 1, banh_cho_anh: 1 };
  var goi = [];
  var soTai = 0;
  function tra(msg) { return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: msg }); } }); }
  function loi(chu) { return Promise.resolve({ ok: false, status: 417, json: function () { return Promise.resolve({ exc: 'x', _server_messages: JSON.stringify([JSON.stringify({ message: chu })]) }); } }); }
  function goiDs() { return JSON.parse(JSON.stringify({ banh: banh, dem: dem(banh) })); }
  function fetchGia(url, cau) {
    var ham = String(url).split('.').pop();
    var mo = String(url).split('/').pop().split('.').slice(0, -1).join('.');
    var a = cau && cau.body ? (typeof cau.body === 'string' ? JSON.parse(cau.body) : cau.body) : null;
    goi.push({ ham: ham, mo: mo, a: a });
    if (tuy.loi && tuy.loi[ham]) return loi(tuy.loi[ham]);
    if (ham === 'bang_moi') return tra(JSON.parse(JSON.stringify(B)));
    if (ham === 'ds_bien_tap') return tra(goiDs());
    if (ham === 'tai_anh') { soTai++; return tra({ url: '/files/web-moi-' + soTai + '.jpg' }); }
    if (ham === 'them_anh') {
      var x = banh.find(function (b) { return b.khoa === a.khoa; });
      /* Ảnh thứ hai trở đi trong ca trùng: máy chủ báo giống ảnh đã có. */
      if (tuy.trung && x.anh.length) { var r = goiDs(); r.khoa = a.khoa; r.trung = x.anh[0].url; return tra(r); }
      x.anh.push({ url: a.url, bam: 'b' + soTai });
      var r2 = goiDs(); r2.khoa = a.khoa; r2.trung = ''; r2.them = a.url; return tra(r2);
    }
    if (ham === 'luu') {
      var y = banh.find(function (b) { return b.khoa === a.khoa; });
      if (a.trang_thai === HIEN && !a.anh.length) return loi('Thêm ít nhất một ảnh trước khi bật Hiện trên web.');
      var cu = {}; y.anh.forEach(function (t) { cu[t.url] = t; });
      y.anh = a.anh.filter(function (t) { return cu[t.url]; }).map(function (t) { return cu[t.url]; });
      y.mo_ta = a.mo_ta; y.tang = a.tang; y.trang_thai = y.anh.length ? a.trang_thai : CHO;
      var r3 = goiDs(); r3.khoa = a.khoa; return tra(r3);
    }
    throw new Error('may chu gia khong biet ' + mo + '.' + ham);
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
    FormData: function () { this.tep = []; this.append = function (k, v) { this.tep.push([k, v && v.name]); }; } };
  g.window = g;
  vm.createContext(g);
  vm.runInContext(doc('chuyen-muc.js'), g, { filename: 'chuyen-muc.js' });
  vm.runInContext(doc('bien-tap-moi.js'), g, { filename: 'bien-tap-moi.js' });
  var app = {
    banh: banh, goi: goi,
    tim: function (c) { return tl.body.querySelectorAll(c); },
    mot: function (c) { var r = tl.body.querySelectorAll(c); if (r.length !== 1) throw new Error('mong dung 1 ' + c + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); },
    go: async function (el, v) { el.value = v; el.oninput(); await nghi(); },
    oTen: function (ten) { return app.mot('[name="' + ten + '"]'); },
    dem: function (ham) { return goi.filter(function (x) { return x.ham === ham; }).length; },
    cuoi: function (ham) { var r = goi.filter(function (x) { return x.ham === ham; }); return r[r.length - 1]; },
    bao: function () { return String(tl.getElementById('bt-trang-thai').textContent); },
    chu: function () { return String(tl.getElementById('bt-noi').textContent); },
    the: async function (k) { await app.bam(app.mot('[data-the="' + k + '"]')); await nghi(); },
    chon: async function (khoa) { await app.bam(app.mot('[data-banh="' + khoa + '"]')); },
    anh: function () { return app.tim('[data-anh-i]').map(function (o) { return o.querySelector('img').src; }); },
    nutAnh: function (i, nhan) { return app.mot('[data-anh-i="' + i + '"]').querySelectorAll('button').find(function (b) { return String(b.getAttribute('aria-label')).indexOf(nhan) === 0; }); },
    congTac: function () { return app.mot('[data-cong-tac-banh]').querySelector('input'); },
    taiTep: async function (ten) { var f = app.oTen('anh_banh'); f.files = (Array.isArray(ten) ? ten : [ten]).map(function (t) { return { name: t, size: 1000 }; }); f.onchange(); await nghi(); await nghi(); },
  };
  return app;
}

(async function () {
  await ca('The Banh: dem banh cho anh, mo the tai danh sach, Cho anh dung dau, chip loc dem dung', async function () {
    var app = appMoi(); await nghi();
    dung('o the Banh dem 1 banh cho anh', String(app.mot('[data-the="banh"]').textContent).indexOf('Bánh1') === 0);
    await app.the('banh');
    bang('goi dung module banh_web', [app.cuoi('ds_bien_tap').mo], ['vagabond.banh_web']);
    bang('ba banh', app.tim('[data-banh]').map(function (b) { return b.dataset.banh; }), ['very berry', 'banh moi', 'hannari']);
    var vb = String(app.mot('[data-banh="very berry"]').textContent);
    dung('dong tom tat size va so anh', vb.indexOf('Size 12 cm, 16 cm · 2 ảnh') >= 0 && vb.indexOf('Đang hiện') >= 0);
    bang('chip', app.tim('[data-loc-banh]').map(function (b) { return String(b.textContent); }), ['Tất cả · 3', 'Chờ ảnh · 1', 'Đang hiện · 1', 'Đã ẩn · 1']);
    await app.bam(app.mot('[data-loc-banh="Chờ ảnh"]'));
    bang('loc cho anh', app.tim('[data-banh]').map(function (b) { return b.dataset.banh; }), ['banh moi']);
    await app.bam(app.mot('[data-loc-banh="tat_ca"]'));
    await app.go(app.oTen('tim_banh'), 'BAWC00024');
    bang('tim theo ma', app.tim('[data-banh]').map(function (b) { return b.dataset.banh; }), ['hannari']);
    dung('chi tiet banh dau, anh dau la anh bia', app.chu().indexOf('Ảnh bìa') >= 0 && app.chu().indexOf('giá và tồn theo ERP') >= 0);
  });

  await ca('Banh Cho anh: bat Hien tren web khi chua co anh bi chan ngay o may khach, khong goi luu', async function () {
    var app = appMoi(); await nghi(); await app.the('banh'); await app.chon('banh moi');
    var i = app.congTac(); i.checked = true; i.onchange(); await nghi();
    dung('cong tac tat lai', app.congTac().checked === false);
    dung('bao viec can lam', app.chu().indexOf('Thêm ít nhất một ảnh trước khi bật Hiện trên web.') >= 0);
    await app.bam(app.mot('[data-luu-banh]'));
    bang('luu gui trang thai an', [app.cuoi('luu').a.trang_thai, app.cuoi('luu').a.anh], [AN, []]);
  });

  await ca('Tai anh: tai_anh roi them_anh dung khoa; anh dau la anh bia; anh trung may chu bao thi khong them va bao ro', async function () {
    var app = appMoi({ trung: 1 }); await nghi(); await app.the('banh'); await app.chon('banh moi');
    await app.taiTep('a.jpg');
    bang('them_anh dung khoa va url vua tai', [app.cuoi('them_anh').a.khoa, app.cuoi('them_anh').a.url], ['banh moi', '/files/web-moi-1.jpg']);
    bang('mot anh, la anh bia', app.anh(), ['/files/web-moi-1.jpg']);
    dung('nhan anh bia', String(app.mot('[data-anh-i="0"]').textContent).indexOf('Ảnh bìa') >= 0);
    await app.taiTep('b.jpg');
    bang('anh trung khong them', app.anh(), ['/files/web-moi-1.jpg']);
    dung('bao trung', app.chu().indexOf('giống một ảnh đã có') >= 0);
    /* Ảnh vừa thêm đã nằm ở máy chủ: không tính là thay đổi chưa lưu khi chuyển bánh. */
    await app.chon('hannari');
    bang('khong hoi, chuyen ngay', app.anh(), ['/files/h.png']);
  });

  await ca('Very Berry: dat anh 2 lam bia, bo anh, sua mo ta roi Luu gui dung thu tu, chu va trang thai', async function () {
    var app = appMoi(); await nghi(); await app.the('banh');
    await app.bam(app.nutAnh(1, 'Đặt ảnh 2 làm ảnh bìa'));
    bang('doi thu tu', app.anh(), ['https://p/can.jpg', '/files/vb.png']);
    await app.go(app.oTen('mo_ta_banh'), 'Vỏ sô cô la đen, trái cây tươi.');
    await app.go(app.oTen('tang_banh'), 'Vỏ - shell\nKem - cream');
    await app.bam(app.mot('[data-luu-banh]'));
    var a = app.cuoi('luu').a;
    bang('payload', [a.khoa, a.anh.map(function (x) { return x.url; }), a.mo_ta, a.tang, a.trang_thai],
      ['very berry', ['https://p/can.jpg', '/files/vb.png'], 'Vỏ sô cô la đen, trái cây tươi.', 'Vỏ - shell\nKem - cream', HIEN]);
    dung('bao khach thay ngay', app.bao().indexOf('Khách thấy ngay') >= 0);
    await app.bam(app.nutAnh(1, 'Bỏ ảnh 2'));
    await app.bam(app.nutAnh(0, 'Bỏ ảnh 1'));
    dung('het anh thi cong tac tu tat', app.congTac().checked === false);
    await app.bam(app.mot('[data-luu-banh]'));
    bang('luu het anh thanh an, may chu dua ve Cho anh', [app.cuoi('luu').a.trang_thai, app.banh[0].trang_thai], [AN, CHO]);
  });

  await ca('Dang sua chua luu ma chon banh khac: hoi lai, bam Thoi thi giu nguyen', async function () {
    var app = appMoi(); await nghi(); await app.the('banh');
    await app.go(app.oTen('mo_ta_banh'), 'Đang gõ dở');
    await app.chon('hannari');
    await app.bam(app.mot('[data-hop-thoi]'));
    bang('van o Very Berry, chu con', app.oTen('mo_ta_banh').value, 'Đang gõ dở');
    await app.chon('hannari');
    await app.bam(app.mot('[data-hop-co]'));
    bang('bo thay doi, sang Hannari', app.anh(), ['/files/h.png']);
  });

  await ca('Loi may chu khi luu: bao dung cau may chu, giu nguyen chu dang go', async function () {
    var app = appMoi({ loi: { luu: 'Mô tả và tầng hương vị mỗi ô tối đa 4.000 ký tự.' } }); await nghi(); await app.the('banh');
    await app.go(app.oTen('mo_ta_banh'), 'Chữ mới');
    await app.bam(app.mot('[data-luu-banh]'));
    dung('bao loi', app.bao().indexOf('tối đa 4.000 ký tự') >= 0);
    bang('giu chu', app.oTen('mo_ta_banh').value, 'Chữ mới');
  });

  /* Codex PR #547 (1c8d221f): bỏ một ảnh rồi tải ảnh thay trước khi Lưu, máy
     chủ trả cả bộ đã lưu (còn ảnh vừa bỏ). Bản sửa chỉ ghép đúng ảnh vừa tải,
     không kéo ảnh đã bỏ trở lại. */
  await ca('Codex 547: bo anh roi tai anh thay truoc khi Luu thi anh da bo khong quay lai', async function () {
    var app = appMoi(); await nghi(); await app.the('banh');
    await app.bam(app.nutAnh(0, 'Bỏ ảnh 1'));
    bang('da bo vb', app.anh(), ['https://p/can.jpg']);
    await app.taiTep('moi.jpg');
    bang('chi them anh vua tai', app.anh(), ['https://p/can.jpg', '/files/web-moi-1.jpg']);
    await app.bam(app.mot('[data-luu-banh]'));
    bang('luu khong con vb', app.cuoi('luu').a.anh.map(function (x) { return x.url; }), ['https://p/can.jpg', '/files/web-moi-1.jpg']);
  });

  await ca('Codex 547: bo anh roi tai lai dung tam do (may chu bao trung) thi anh do tro lai ban dang sua', async function () {
    var app = appMoi({ trung: 1 }); await nghi(); await app.the('banh');
    await app.bam(app.nutAnh(0, 'Bỏ ảnh 1'));
    await app.taiTep('vb-nen-lai.jpg');
    bang('anh nguoi dung muon giu tro lai', app.anh(), ['https://p/can.jpg', '/files/vb.png']);
    dung('bao da co san', app.chu().indexOf('đã có sẵn') >= 0);
  });

  xongHet = true;
  console.log('Bo ca kiem HANH VI v644: the Banh cua trinh bien tap');
  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  if (ket.hong) process.exitCode = 1;
}());
