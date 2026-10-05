/* Bo ca kiem HANH VI v575: gom hoa don cua NHIEU phap nhan vao mot phieu.
 *
 * Loan Anh bao 05/10/2026: "Cong ty TNHH Oshima's dang co 3 bill, anh Vu
 * Oshima dang co 10 bill. Em can gom chung 2 phap nhan nay de tick chung 13
 * bill ra chung 1 de nghi thanh toan."
 *
 * Chay THAT man Cong no (11-khach-ca-hop-dong.js), khung app (01-khung-app.js),
 * thanh cong cu (15-khuon-danh-sach.js) va hop chon sheet() (00-nen.js). May
 * chu va confirmSheet la ban gia. Ca kiem chi bam nhu nguoi dung: mo the
 * khach, tick, bam Gom chung, chon khach dung ten trong hop. Khong goi ham
 * nao cua man ngoai chuoi do (quy tac 15).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/gom_chung_575.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

/* Dung so lieu man Loan Anh chup: Oshima's 3 bill 4.540.000, anh Vu 10 bill. */
var OSHIMA = { khach: 'CUS-OSHIMA', ten: "CÔNG TY TNHH OSHIMA'S", so_hd: 3, tien: 4540000, so_ngay: 56, hd: [
  { name: 'HDB-2026-01066', tien: 1580000, ngay: '2026-08-10', nguon: 'Pancake' },
  { name: 'HDB-2026-01972', tien: 1480000, ngay: '2026-08-14', nguon: 'Pancake' },
  { name: 'HDB-26-09-00153', tien: 1480000, ngay: '2026-09-01', nguon: 'Pancake' }] };
var VU = { khach: 'CUS-VU', ten: 'Anh Vũ Oshima', so_hd: 10, tien: 0, so_ngay: 40, hd: [] };
for (var i = 1; i <= 10; i++) { VU.hd.push({ name: 'HDB-26-09-0' + (200 + i), tien: 500000, ngay: '2026-09-0' + ((i % 9) + 1) }); VU.tien += 500000; }

var THEM_KHACH = [];
function mayChu() {
  var goi = [];
  return {
    goi: goi,
    cuoi: function (m) { var r = goi.filter(function (x) { return x.m === m; }); return r[r.length - 1]; },
    dem: function (m) { return goi.filter(function (x) { return x.m === m; }).length; },
    api: async function (m, a) {
      goi.push({ m: m, a: JSON.parse(JSON.stringify(a || {})) });
      if (m === 'vagabond.cong_no.ds_khach_no') {
        var ds = [OSHIMA, VU].concat(THEM_KHACH).filter(function (k) { return !a.tim || k.ten.toLowerCase().indexOf(a.tim.toLowerCase()) >= 0; });
        return { khach: ds, tong: OSHIMA.tien + VU.tien, so_khach_tat_ca: 2, dang_loc: a.tim ? 1 : 0,
          tong_loc: ds.reduce(function (t, k) { return t + k.tien; }, 0), cho_ghi_so: { so_hd: 0, tien: 0 } };
      }
      if (m === 'vagabond.cong_no.ds_phieu') return { phieu: [] };
      if (m === 'vagabond.cong_no.ds_tien_da_ve') return { dong: [], tong_dong: 0, dem: {}, cac_nguon: [] };
      if (m === 'vagabond.cong_no.tao_phieu') return { name: 'CN-1', ma_phieu: 'DNTT-26-10-00001' };
      if (m === 'vagabond.cong_no.xem_phieu') {
        var hd = JSON.parse(goi.filter(function (x) { return x.m === 'vagabond.cong_no.tao_phieu'; }).pop().a.hoa_don);
        return { name: 'CN-1', ma_phieu: 'DNTT-26-10-00001', khach: 'CUS-VU', ten_khach: 'Anh Vũ Oshima',
          tong_tien: 9540000, da_thu: 0, sepay: 0, da_nhan: 0, con_thieu: 9540000, trang_thai: 'Cho thu', qr: {},
          han_qr: '2026-10-12', thieu_phieu_thu: 0,
          cac_khach: [{ khach: 'CUS-OSHIMA', ten: "CÔNG TY TNHH OSHIMA'S", so_hd: 3, tien: 4540000 },
            { khach: 'CUS-VU', ten: 'Anh Vũ Oshima', so_hd: 10, tien: 5000000 }],
          dong: hd.map(function (x) { return { hoa_don: x, khach: x.indexOf('HDB-26-09-02') === 0 ? 'CUS-VU' : 'CUS-OSHIMA', so_tien: 1, ngay: '' }; }) };
      }
      return {};
    },
  };
}

function appMoi() {
  var tl = domGia.taiLieuGia();
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var mc = mayChu();
  var tin = [], hoi = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN, Date: Date,
    encodeURIComponent: encodeURIComponent,
    document: tl,
    frappe: { session: { user: 'ntla.3008@gmail.com' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f) { f(); return 1; }, clearTimeout: function () {},
  };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push("toast:" + s); }',
    'function busy() {}',
    'function baoTin(s) { __tin.push("baoTin:" + s); return Promise.resolve(); }',
    'function dSkin() {}',
    'function money(x) { return String(x); }',
    'function posNgayVn(x) { return String(x || ""); }',
    'function posChipNut(thuoc, nhan, bat) { return "<button class=\\"chip\\" data-bat=\\"" + (bat ? 1 : 0) + "\\" " + thuoc + ">" + nhan + "</button>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function confirmSheet(t, m) { __hoi.push(t + "\\n" + m); return Promise.resolve(__dongY); }',
    'function locHang() { return ""; }',
    'function locTim(ds) { return ds[0]; }',
    'async function scrHome() { frame(APPNAME, "<div></div>"); }',
  ].join('\n'), Object.assign(g, { __tin: tin, __mc: mc, __hoi: hoi, __dongY: true }));
  var nen = doc('00-nen.js');
  vm.runInContext(nen.slice(nen.indexOf('function sheet('), nen.indexOf('function confirmSheet(')), g);
  vm.runInContext(doc('01-khung-app.js'), g);
  vm.runInContext(doc('15-khuon-danh-sach.js'), g);
  vm.runInContext(doc('11-khach-ca-hop-dong.js'), g);
  var app = {
    g: g, tl: tl, mc: mc, tin: tin, hoi: hoi,
    tim: function (chon) { return tl.body.querySelectorAll(chon); },
    mot: function (chon) { var r = tl.body.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(domGia.suKien('click', {}, el)); await nghi(); await nghi(); },
    goTim: async function (chu) {
      var o = tl.body.querySelectorAll('input').filter(function (x) { return x.id && x.id.indexOf('cnno') === 0; })[0];
      if (!o) throw new Error('khong thay o tim');
      o.value = chu;
      o.dispatchEvent(domGia.suKien('keydown', { key: 'Enter' }, o));
      await nghi(); await nghi();
    },
  };
  return app;
}

async function moCongNo() {
  var app = appMoi();
  await app.g.reset(app.g.scrCongNo); await nghi(); await nghi();
  return app;
}
/* Mo the khach roi bam Chon het, dung nhu Loan Anh lam tren man. */
async function tickHet(app, kh) {
  await app.bam(app.mot('[data-cnmo="' + kh + '"]'));
  await app.bam(app.mot('[data-cnall="' + kh + '"]'));
}
function chu(el) { return String(el.textContent || el.innerHTML || ''); }

(async function () {
  await ca('Loan Anh 05/10: tick het Oshima\'s va anh Vu thi hien the Gom chung 13 hoa don cua 2 khach', async function () {
    var app = await moCongNo();
    bang('chua tick thi khong co the gom chung', app.tim('[data-cngomchungthe]').length, 0);
    await tickHet(app, 'CUS-OSHIMA');
    bang('moi mot khach: chua co the gom chung', app.tim('[data-cngomchungthe]').length, 0);
    await tickHet(app, 'CUS-VU');
    var the = app.mot('[data-cngomchungthe]');
    dung('dem 13 hoa don 2 khach: ' + chu(the), chu(the).indexOf('13 hoá đơn của 2 khách') >= 0);
    dung('tong tien 9540000', chu(the).indexOf('9540000') >= 0);
    dung('the khach dong van bao da tick', app.tim('[data-cndatick="CUS-OSHIMA"]').length === 1);
  });

  await ca('Bam Gom chung, chon anh Vu dung ten: may chu nhan dung 13 hoa don, nhieu_khach=1, khach=CUS-VU', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.bam(app.mot('[data-cngomchung]'));
    var mucs = app.tim('.shi');
    bang('hop chon co 2 khach', mucs.length, 2);
    /* Goi y dau tien la khach nhieu tien nhat (anh Vu 5.000.000). */
    dung('muc dau la anh Vu', chu(mucs[0]).indexOf('Anh Vũ Oshima') >= 0);
    await app.bam(mucs[0]);
    var t = app.mc.cuoi('vagabond.cong_no.tao_phieu');
    dung('co goi tao phieu', !!t);
    bang('khach dung ten', t.a.khach, 'CUS-VU');
    bang('nhieu khach', t.a.nhieu_khach, 1);
    var hd = JSON.parse(t.a.hoa_don);
    bang('13 hoa don', hd.length, 13);
    dung('du ca 3 bill Oshima', ['HDB-2026-01066', 'HDB-2026-01972', 'HDB-26-09-00153'].every(function (x) { return hd.indexOf(x) >= 0; }));
    dung('hop xac nhan ke tung khach', app.hoi[0].indexOf("CÔNG TY TNHH OSHIMA'S: 3 hoá đơn") >= 0 && app.hoi[0].indexOf('Phiếu đứng tên: Anh Vũ Oshima') >= 0);
    /* Sau khi tao: sang man phieu, ke ra 2 khach, dau tick sach. */
    dung('man phieu ke cac khach', app.tim('[data-cnphieukhach]').length === 1);
    await app.g.reset(app.g.scrCongNo); await nghi(); await nghi();
    bang('dau tick da xoa', app.tim('[data-cngomchungthe]').length, 0);
  });

  await ca('Chon Oshima\'s dung ten (muc thu hai) thi khach gui len la CUS-OSHIMA', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.bam(app.mot('[data-cngomchung]'));
    await app.bam(app.tim('.shi')[1]);
    bang('khach dung ten', app.mc.cuoi('vagabond.cong_no.tao_phieu').a.khach, 'CUS-OSHIMA');
  });

  await ca('Dong hop chon khong chon ai thi khong lap phieu', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.bam(app.mot('[data-cngomchung]'));
    await app.bam(app.mot('.x'));
    bang('khong goi tao phieu', app.mc.dem('vagabond.cong_no.tao_phieu'), 0);
  });

  await ca('O tim an bot khach da tick: the gom chung van dem du ca hai khach', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.goTim('vũ');
    bang('chi con 1 the khach hien', app.tim('[data-cnmo]').length, 1);
    var the = app.mot('[data-cngomchungthe]');
    dung('van 13 hoa don 2 khach: ' + chu(the), chu(the).indexOf('13 hoá đơn của 2 khách') >= 0);
  });

  await ca('Bo chon het thi the gom chung bien mat', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.bam(app.mot('[data-cnbohet]'));
    bang('khong con the', app.tim('[data-cngomchungthe]').length, 0);
    bang('khong con dau da tick', app.tim('[data-cndatick]').length, 0);
  });

  await ca('Nut gom trong the khach van chi gom khach do, nhu cu', async function () {
    var app = await moCongNo();
    await tickHet(app, 'CUS-OSHIMA');
    await tickHet(app, 'CUS-VU');
    await app.bam(app.mot('[data-cngom="CUS-VU"]'));
    var t = app.mc.cuoi('vagabond.cong_no.tao_phieu');
    bang('khach', t.a.khach, 'CUS-VU');
    bang('khong co co nhieu khach', t.a.nhieu_khach, undefined);
    bang('10 hoa don', JSON.parse(t.a.hoa_don).length, 10);
  });

  await ca('Codex #443: nhieu phap nhan thi hop chon co o tim, hop xac nhan chi ke 3 khach', async function () {
    THEM_KHACH = [];
    for (var j = 1; j <= 3; j++) THEM_KHACH.push({ khach: 'CUS-K' + j, ten: 'Khach ' + j, so_hd: 1, tien: 100000, so_ngay: 5,
      hd: [{ name: 'HDB-K' + j, tien: 100000, ngay: '2026-09-10' }] });
    try {
      var app = await moCongNo();
      var cac = ['CUS-OSHIMA', 'CUS-VU', 'CUS-K1', 'CUS-K2', 'CUS-K3'];
      for (var i = 0; i < cac.length; i++) await tickHet(app, cac[i]);
      dung('the gom chung dem 5 khach', chu(app.mot('[data-cngomchungthe]')).indexOf('của 5 khách') >= 0);
      await app.bam(app.mot('[data-cngomchung]'));
      bang('hop chon co o tim', app.tim('input').filter(function (x) { return x.getAttribute('placeholder') === 'Tìm nhanh...'; }).length, 1);
      bang('hop chon du 5 khach', app.tim('.shi').length, 5);
      await app.bam(app.tim('.shi')[0]);
      var cau = app.hoi[0];
      bang('chi ke 3 dong khach', (cau.match(/\n• [^v]/g) || []).length, 3);
      dung('ghi so khach con lai: ' + cau, cau.indexOf('và 2 khách nữa') >= 0);
      bang('van gui du 16 hoa don', JSON.parse(app.mc.cuoi('vagabond.cong_no.tao_phieu').a.hoa_don).length, 16);
    } finally { THEM_KHACH = []; }
  });

  console.log('Bo ca kiem HANH VI v575: gom chung nhieu phap nhan (Loan Anh, Oshima)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
