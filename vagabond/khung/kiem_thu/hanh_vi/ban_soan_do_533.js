/* Bo ca kiem HANH VI v533: tu luu phieu dang soan tren may.
 *
 * Loan Anh bao anh Viet 27/09/2026: soan bao gia tren app, chua bam Luu ma
 * lo thoat ra hoac may sap nguon la mat het. Bo ca nay CHAY THAT:
 *   - khung app that (01-khung-app.js: go, back, reset, render, frame),
 *   - man bao gia that (22-bao-gia.js: bgMoi, scrBgSua, bgLuu),
 *   - phan tu luu that (48-ban-soan-do.js), nap SAU CUNG nhu ban ghep that.
 * May chu, hop hoi va trang chu la ban gia. "May sap nguon" dung bang cach
 * dung MOT app moi tinh tren cung kho localStorage: bo nho trong trang mat
 * het, chi con nhung gi da ghi xuong may.
 *
 * Dong ho tre (setTimeout) do ca kiem tua tay, khong cho that.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/ban_soan_do_533.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var KHUNG = doc('01-khung-app.js');
var BAO_GIA = doc('22-bao-gia.js');
var DON_HUY = doc('29-don-huy.js');
var SOAN_DO = doc('48-ban-soan-do.js');

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}

/* localStorage gia, song qua nhieu "lan mo app" (may sap nguon van con). */
function khoMay() {
  var m = new Map();
  return {
    _m: m,
    get length() { return m.size; },
    key: function (i) { return Array.from(m.keys())[i] || null; },
    getItem: function (k) { return m.has(k) ? m.get(k) : null; },
    setItem: function (k, v) { m.set(k, String(v)); },
    removeItem: function (k) { m.delete(k); },
  };
}
function cacKhoa(kho) { return Array.from(kho._m.keys()).filter(function (k) { return k.indexOf('vgbSoanDo:') === 0; }).sort(); }

/* May chu gia cua bao gia. */
function mayChu(canh) {
  var goi = [];
  var so = 0;
  return {
    goi: goi,
    api: async function (m, a) {
      goi.push({ m: m, a: a });
      if (m === 'vagabond.bao_gia.cai_dat') return { song_ngu: 0, chip_hieu_luc: [7, 15, 30] };
      if (m === 'vagabond.bao_gia.moi') {
        return { name: '', ten: '', ten_khach: '', dia_chi: '', song_ngu: 0, gia_da_gom_vat: 0, phien_ban: 1,
          ngay_bao_gia: '2026-09-27', hieu_luc_ngay: 30,
          dong: [{ ten_mon: '', so_luong: 1, don_gia: 0, chiet_khau: 0, thue_pt: 8 }], dich_vu: [], moc: [] };
      }
      if (m === 'vagabond.bao_gia.chi_tiet') {
        return { name: a.name, ten: 'Báo giá cũ ' + a.name, ten_khach: 'Công ty cũ', song_ngu: 0, phien_ban: 1,
          ngay_bao_gia: '2026-09-20', hieu_luc_ngay: 30,
          dong: [{ ten_mon: 'Bánh cũ', so_luong: 2, don_gia: 100000, chiet_khau: 0, thue_pt: 8 }], dich_vu: [], moc: [] };
      }
      if (m === 'vagabond.bao_gia.luu') {
        if (canh && canh.luuLoi) throw new Error('Mất mạng');
        so++;
        return { name: 'BG-26-' + so };
      }
      if (m === 'vagabond.don_huy.xem_hoan') {
        return { duoc: 1, ma_don: a.ma_don, ma_hien_thi: 'W' + a.ma_don, ten_khach: 'Chị Hoa', sdt: '0909',
          tong_don: 500000, da_nhan: 500000, muc_hoan: 500000, noi_dung_ck: 'HOAN ' + a.ma_don };
      }
      if (m === 'vagabond.don_huy.tao_hoan') return { ho_so: 'HS-1', phieu_thu: 'PT-1', phieu_chi: 'PC-1' };
      /* Khuon that cua nop_quy.tao: lech tu 1.000d ma chua co ly do thi TRA
         VE THANH CONG voi co can_ly_do, CHUA tao phieu. */
      if (m === 'vagabond.nop_quy.tao') return (a && a.ly_do_lech) ? { ok: 1, ma: 'NQ-26-1' } : { can_ly_do: 1, lech: 5000 };
      return {};
    },
  };
}

/* Dung mot app moi tinh. kho: localStorage cua may (dung chung giua cac lan
   mo de gia lap may sap nguon). */
function appMoi(kho, canh) {
  canh = canh || {};
  var tl = domGia.taiLieuGia();
  var ngheTL = {};
  tl.addEventListener = function (loai, ham) { (ngheTL[loai] = ngheTL[loai] || []).push(ham); };
  tl.createEvent = function () { return { initEvent: function (t) { this.type = t; } }; };
  var vgb = tl.createElement('div'); vgb.id = 'vgb'; tl.body.appendChild(vgb);
  var hen = [], soHen = 0, bayGio = 1790000000000;
  var mc = mayChu(canh);
  var hoi = [], tin = [];
  var g = {
    console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN,
    Date: (function () { function D(x) { return x === undefined ? new Date(bayGio) : new Date(x); } D.now = function () { return bayGio; }; return D; })(),
    document: tl,
    frappe: { session: { user: 'loananh@vagabond.vn' } },
    location: { href: 'https://app.x/bep', pathname: '/bep', hostname: 'app.x', search: '', hash: '', replace: function () {} },
    history: { pushState: function () {}, replaceState: function () {}, back: function () {} },
    requestAnimationFrame: function (f) { f(); },
    setTimeout: function (f, ms) { soHen++; hen.push({ id: soHen, f: f, luc: bayGio + (ms || 0) }); return soHen; },
    clearTimeout: function (id) { hen = hen.filter(function (x) { return x.id !== id; }); },
  };
  g.window = g;
  g.localStorage = kho;
  g.addEventListener = function (loai, ham) { (ngheTL['w:' + loai] = ngheTL['w:' + loai] || []).push(ham); };
  vm.createContext(g);

  /* Tien ich nen ma khung va bao gia can luc chay. Ban gia, khong phai phan
     dang kiem. */
  vm.runInContext([
    'var root = document.getElementById("vgb");',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"); }',
    'function toast(s) { __tin.push(String(s)); }',
    'function busy() {}',
    'function baoTin(s) { __tin.push("baoTin:" + s); }',
    'function dSkin() {}',
    'function vgbCss() {}',
    'function shortWh(x) { return String(x || "").replace(/ - TV$/, ""); }',
    'function money(x) { return String(x); }',
    'function vgbSo(x) { return Number(String(x == null ? "" : x).replace(/[^0-9.-]/g, "")) || 0; }',
    'function posChipNut(thuoc, nhan, bat) { return "<button class=\\"chip\\" " + thuoc + ">" + h(nhan) + "</button>"; }',
    'function confirmSheet() { return Promise.resolve(true); }',
    'function hoiChon(t, m, ds) { __hoi.push({ t: t, m: m, ds: ds.map(function (x) { return x.k; }) }); return Promise.resolve(__canh.chon === undefined ? "tiep" : __canh.chon); }',
    'function api(m, a) { return __mc.api(m, a); }',
    'function vgbGomNhom() { var b = document.getElementById("vgbBody"); if (b) b.innerHTML = "<div class=\\"gwrap\\"><div class=\\"gt\\" data-nhom=\\"BH\\">Bán hàng</div></div>"; }',
    'function kmHangChip(noiDung) { return "<div>" + noiDung + "</div>"; }',
    'function hqLaHop() { return false; }',
    'function vgbTienGo(x) { return String(x == null ? "" : x); }',
    'function rndLbl(t) { return "<div>" + h(t) + "</div>"; }',
    'function oTep(o) { return "<span>" + h(o.ten) + "</span>"; }',
    'function errMsg(e) { return String((e && e.message) || e); }',
    'async function scrDonHuy() { frame("Đơn đã huỷ", "<div>ds</div>"); }',
    'async function scrHome() { frame(APPNAME, "<div class=\\"emp\\">...</div>"); vgbGomNhom(); }',
  ].join('\n'), Object.assign(g, { __tin: tin, __hoi: hoi, __canh: canh, __mc: mc }));
  vm.runInContext(KHUNG, g);
  vm.runInContext(BAO_GIA, g);
  vm.runInContext(DON_HUY, g);
  /* Moi man lap phieu KHAC ma 48 boc: ca nay khong nap that, chi can co ten
     de 48 boc duoc luc nap. Man that cua bao gia thi da nap o tren. */
  var boc = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(function (x) { return x.split(' ')[0]; });
  boc.forEach(function (t) {
    if (typeof g[t] !== 'function') vm.runInContext('function ' + t + '() {}', g);
  });
  ['bgMoRong', 'tvTay', 'XK', 'rnd', 'dsTay', 'hdTay', 'hdSua', 'hdGsDong', 'hdGsKieu', 'vdTay', 'cpTay', 'kgForm', 'nccF',
    'dncForm', 'nqSuaMa', 'ctE', 'tcX', 'tq', 'tqd', 'XKT', 'XPV', 'rcvD', 'nhpD', 'mfgD', 'htF', 'htFHop', 'dhF', 'dhOv', 'kmSua']
    .forEach(function (t) { if (!(t in g)) g[t] = null; });
  vm.runInContext(SOAN_DO, g);

  var app = {
    g: g, tl: tl, mc: mc, hoi: hoi, tin: tin,
    /* Tua dong ho: chay moi hen toi han. */
    tua: async function (ms) {
      bayGio += ms;
      for (var vong = 0; vong < 20; vong++) {
        var toi = hen.filter(function (x) { return x.luc <= bayGio; });
        if (!toi.length) break;
        hen = hen.filter(function (x) { return x.luc > bayGio; });
        toi.forEach(function (x) { x.f(); });
        await nghi();
      }
    },
    el: function (id) { return tl.getElementById(id); },
    /* Go chu vao o nhu nguoi dung: doi value, ban input, su kien noi len toi document. */
    go: function (id, chu) {
      var o = tl.getElementById(id);
      if (!o) throw new Error('khong thay o #' + id);
      o.value = chu;
      var ev = domGia.suKien('input', {}, o);
      (ngheTL.input || []).forEach(function (f) { f(ev); });
      o.dispatchEvent(ev);
    },
    /* Bam: document bat truoc (giai doan bat), roi toi nut. */
    bam: async function (el) {
      if (typeof el === 'string') { var id = el; el = tl.getElementById(id); if (!el) throw new Error('khong thay nut #' + id); }
      var ev = domGia.suKien('click', {}, el);
      (ngheTL.click || []).forEach(function (f) { f(ev); });
      el.dispatchEvent(ev);
      await nghi();
    },
    /* Trinh duyet an tab / dong trang. */
    anTab: function () { (ngheTL['w:pagehide'] || []).forEach(function (f) { f({}); }); },
    cho: nghi,
  };
  return app;
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

async function moTrangChu(app) { await app.g.reset(app.g.scrHome); await app.cho(); }
async function moBaoGiaMoi(app) { await app.g.bgMoi(''); await app.cho(); await app.cho(); }

async function chayHet() {
  await ca('Loan Anh: go bao gia moi, may sap nguon, mo lai app thi the Phieu dang soan do dua ve DUNG to dang go', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    dung('man soan bao gia da ve', !!a.el('bgf_ten'));
    a.go('bgf_ten', 'Tiệc cưới ABC 12/10');
    a.go('bgf_ten_khach', 'Công ty ABC');
    a.go('dg_0_ten_mon', 'Bánh kem 3 tầng');
    await a.tua(700);
    bang('dung mot ban nhap cho bao gia moi', cacKhoa(kho), ['vgbSoanDo:loananh@vagabond.vn:bao_gia:moi']);
    /* Sap nguon: khong bam Luu, khong roi man, bo nho trong trang mat het. */
    var b = appMoi(kho);
    await moTrangChu(b);
    var the = b.el('sdThe');
    dung('trang chu co the Phieu dang soan do', !!the);
    var dong = the.querySelectorAll('[data-sdmo]');
    bang('the co dung mot dong', dong.length, 1);
    dung('dong ghi ten bao gia dang go', dong[0].textContent.indexOf('Tiệc cưới ABC 12/10') >= 0);
    await b.bam(dong[0]);
    await b.cho(); await b.cho();
    bang('mo lai khong hoi them', b.hoi.length, 0);
    bang('tieu de dien lai', b.el('bgf_ten').value, 'Tiệc cưới ABC 12/10');
    bang('ten khach dien lai', b.el('bgf_ten_khach').value, 'Công ty ABC');
    bang('dong san pham dien lai', b.el('dg_0_ten_mon').value, 'Bánh kem 3 tầng');
    /* Bam Luu: may chu nhan dung chu da go, ban nhap bien mat. */
    await b.bam('bgLuu');
    await b.cho(); await b.cho();
    var luu = b.mc.goi.filter(function (x) { return x.m === 'vagabond.bao_gia.luu'; });
    bang('goi luu mot lan', luu.length, 1);
    var du = JSON.parse(luu[0].a.du_lieu);
    bang('may chu nhan tieu de', du.ten, 'Tiệc cưới ABC 12/10');
    bang('may chu nhan ten mon', du.dong[0].ten_mon, 'Bánh kem 3 tầng');
    bang('luu xong thi het ban nhap', cacKhoa(kho), []);
  });

  await ca('Lo bam lui khi dang go (chua het 0,6 giay): van ghi kip, mo bao gia moi thi hoi va Mo tiep dien lai', async function () {
    var kho = khoMay();
    var a = appMoi(kho, { chon: 'tiep' });
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Sinh nhật bé Na');
    /* Khong tua dong ho: bam lui ngay sau khi go. */
    await a.bam('vgbBack');
    await a.cho();
    bang('da ve trang chu', a.g.S.stack.length, 1);
    bang('ban nhap da ghi truoc khi man bi xoa', cacKhoa(kho).length, 1);
    await moBaoGiaMoi(a);
    bang('hoi mot lan', a.hoi.length, 1);
    bang('hai lua chon', a.hoi[0].ds, ['tiep', 'moi']);
    bang('mo tiep dien lai tieu de', a.el('bgf_ten').value, 'Sinh nhật bé Na');
  });

  await ca('Nut Back cua trinh duyet (khong co cu bam nao trong trang): van ghi not truoc khi man bi xoa', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Vuốt lùi');
    /* back() goi thang, y nhu duong popstate: khong qua su kien click. */
    await a.g.back(); await a.cho();
    bang('da ve trang chu', a.g.S.stack.length, 1);
    var k = cacKhoa(kho);
    bang('co ban nhap', k.length, 1);
    dung('ban nhap mang chu vua go', kho.getItem(k[0]).indexOf('Vuốt lùi') >= 0);
  });

  await ca('Man tu xoa trang thai roi moi roi di (kieu bo phieu nhap): giu ban da luu, khong ghi to rong de len', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Đã lưu nháp');
    await a.tua(700);
    a.go('bgf_ten', 'Đã lưu nháp, gõ thêm');
    a.g.bgTay = null;
    await a.g.reset(a.g.scrHome); await a.cho();
    var k = cacKhoa(kho);
    bang('van mot ban nhap', k.length, 1);
    var rec = JSON.parse(kho.getItem(k[0]));
    dung('trang thai trong ban nhap khong rong', JSON.parse(rec.js).s !== null);
    var b = appMoi(kho);
    await moTrangChu(b);
    await b.bam(b.el('sdThe').querySelectorAll('[data-sdmo]')[0]);
    await b.cho(); await b.cho();
    dung('mo lai duoc man soan', !!b.el('bgf_ten'));
  });

  await ca('Chon Soan moi: to trang, ban cu KHONG mat, van nam tren the o trang chu', async function () {
    var kho = khoMay();
    var a = appMoi(kho, { chon: 'moi' });
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Bản A');
    await a.tua(700);
    await a.bam('vgbBack'); await a.cho();
    await moBaoGiaMoi(a);
    bang('hoi mot lan', a.hoi.length, 1);
    bang('to moi de trong', a.el('bgf_ten').value, '');
    var k = cacKhoa(kho);
    bang('ban cu cat sang khoa rieng', k.length, 1);
    dung('khoa rieng mang dau ~', k[0].indexOf('bao_gia:moi~') > 0);
    a.go('bgf_ten', 'Bản B');
    await a.tua(700);
    bang('hai ban nhap cung ton tai', cacKhoa(kho).length, 2);
    await a.bam('vgbBack'); await a.cho();
    var the = a.el('sdThe');
    bang('the co hai dong', the.querySelectorAll('[data-sdmo]').length, 2);
    dung('co Ban A', the.textContent.indexOf('Bản A') >= 0);
    dung('co Ban B', the.textContent.indexOf('Bản B') >= 0);
  });

  await ca('Mo roi thoat khong go gi: khong de lai ban nhap rac', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    await a.tua(700);
    await a.bam('vgbBack'); await a.cho();
    a.anTab();
    bang('khong co ban nhap', cacKhoa(kho), []);
    dung('trang chu khong co the', !a.el('sdThe'));
  });

  await ca('Go roi xoa ve y nhu luc mo: ban nhap tu xoa', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'x');
    await a.tua(700);
    bang('co ban nhap', cacKhoa(kho).length, 1);
    a.go('bgf_ten', '');
    await a.tua(700);
    bang('xoa ve nhu cu thi het ban nhap', cacKhoa(kho), []);
  });

  await ca('Luu loi (mat mang): ban nhap VAN CON, khong xoa', async function () {
    var kho = khoMay();
    var a = appMoi(kho, { luuLoi: 1 });
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Tiệc công ty');
    a.go('bgf_ten_khach', 'Công ty X');
    a.go('dg_0_ten_mon', 'Bánh mì');
    await a.bam('bgLuu');
    await a.cho(); await a.cho();
    dung('may chu da bi goi', a.mc.goi.some(function (x) { return x.m === 'vagabond.bao_gia.luu'; }));
    bang('ban nhap con', cacKhoa(kho).length, 1);
  });

  await ca('Sua bao gia da co: ban nhap theo MA bao gia, khong lan voi bao gia moi', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    a.g.bgTay = null;
    await a.g.go(function () { return a.g.scrBgSua('BG-26-7'); }); await a.cho(); await a.cho();
    bang('doc dung bao gia cu', a.el('bgf_ten').value, 'Báo giá cũ BG-26-7');
    a.go('bgf_ten', 'Báo giá cũ BG-26-7 (sửa giá)');
    await a.tua(700);
    bang('khoa theo ma', cacKhoa(kho), ['vgbSoanDo:loananh@vagabond.vn:bao_gia:BG-26-7']);
  });

  await ca('Sang man con (chon khach) roi quay ve: khong hoi lai, go tiep van ghi vao DUNG ban do', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Có màn con');
    await a.tua(700);
    a.g.bgDoc();
    await a.g.go(function () { a.g.frame('Chọn khách', '<div class="card">danh sách khách</div>'); }); await a.cho();
    /* Man chon khach doi trang thai bao gia roi lui ve, y nhu bgChonKhach. */
    a.g.bgTay.khach_hang = 'KH-00012';
    await a.bam('vgbBack'); await a.cho(); await a.cho();
    bang('khong hoi', a.hoi.length, 0);
    bang('o tieu de van con', a.el('bgf_ten').value, 'Có màn con');
    dung('khach vua chon hien tren man', a.el('vgbBody').textContent.indexOf('KH-00012') >= 0);
    a.go('bgf_ten', 'Có màn con - sửa tiếp');
    await a.tua(700);
    var k = cacKhoa(kho);
    bang('van mot ban nhap', k.length, 1);
    dung('ban nhap mang chu moi', kho.getItem(k[0]).indexOf('sửa tiếp') >= 0);
  });

  await ca('Tai khoan khac tren cung may khong thay ban nhap cua Loan Anh', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Của Loan Anh');
    await a.tua(700);
    var b = appMoi(kho);
    b.g.S.user = 'ketoan@vagabond.vn';
    await moTrangChu(b);
    dung('khong co the', !b.el('sdThe'));
    await moBaoGiaMoi(b);
    bang('khong hoi', b.hoi.length, 0);
  });

  await ca('Ban nhap qua 14 ngay tu don, khong hien tren the', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await moBaoGiaMoi(a);
    a.go('bgf_ten', 'Cũ lắm rồi');
    await a.tua(700);
    await a.bam('vgbBack'); await a.cho();
    dung('hom nay con the', !!a.el('sdThe'));
    await a.tua(15 * 864e5);
    await moTrangChu(a);
    dung('15 ngay sau het the', !a.el('sdThe'));
    bang('kho sach', cacKhoa(kho), []);
  });

  await ca('Hop hoan tien don da huy (hop noi, trang thai dung trong ham): sap nguon, mo lai tu the, gui duoc va het ban nhap', async function () {
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    await a.g.dhMo('DH-77'); await a.cho();
    dung('hop da mo', !!a.el('dhSTK'));
    /* Chon ly do bang chip, go so tai khoan va ten chu tai khoan. */
    await a.bam(a.tl.querySelectorAll('[data-dhly]').filter(function (x) { return x.getAttribute('data-dhly') === 'Trung don'; })[0]);
    await a.cho();
    a.go('dhSTK', '0123456789');
    a.go('dhTenTK', 'NGUYEN THI HOA');
    /* Anh bang chung da tai len may chu (chi con duong dan): day la ket qua
       cua dhThemBangChung, buoc tai tep khong gia lap duoc trong node. */
    a.g.dhF.bang_chung = [{ ma: 'F-1', ten: 'chat.jpg', url: '/files/chat.jpg' }];
    a.g.dhF.ngan_hang = 'MB - Ngân hàng TMCP Quân đội';
    a.go('dhGhi', 'Khách đặt trùng');
    await a.tua(700);
    bang('mot ban nhap theo ma don', cacKhoa(kho), ['vgbSoanDo:loananh@vagabond.vn:don_huy_hoan:DH-77']);

    var b = appMoi(kho);
    await moTrangChu(b);
    var dong = b.el('sdThe').querySelectorAll('[data-sdmo]');
    bang('the co mot dong', dong.length, 1);
    await b.bam(dong[0]); await b.cho(); await b.cho();
    bang('khong hoi', b.hoi.length, 0);
    bang('so tai khoan dien lai', b.el('dhSTK').value, '0123456789');
    bang('ten chu tai khoan dien lai', b.el('dhTenTK').value, 'NGUYEN THI HOA');
    bang('ly do ghep lai vao trang thai', b.g.dhF.ly_do, 'Trung don');
    bang('ngan hang ghep lai', b.g.dhF.ngan_hang, 'MB - Ngân hàng TMCP Quân đội');
    bang('bang chung da tai len van con', b.g.dhF.bang_chung.length, 1);
    bang('so tien lay lai tu may chu', b.g.dhF.tien, 500000);
    await b.bam(b.tl.querySelectorAll('[data-dhok]')[0]); await b.cho(); await b.cho();
    var gui = b.mc.goi.filter(function (x) { return x.m === 'vagabond.don_huy.tao_hoan'; });
    bang('gui mot lan', gui.length, 1);
    bang('gui dung so tai khoan', gui[0].a.so_tk, '0123456789');
    bang('gui dung ly do', gui[0].a.ly_do, 'Trung don');
    bang('gui xong het ban nhap', cacKhoa(kho), []);
  });

  await ca('Codex #378: may chu tra can_ly_do (chua tao phieu) thi KHONG xoa nhap; tra phieu that moi xoa', async function () {
    /* Codex #378 (74dbae0b): nop_quy.tao va tao_theo_ngay tra thanh cong
       {can_ly_do: 1} truoc khi insert. Ban cu xoa nhap ngay luot goi dau.
       Tai hien truoc khi sua: sau luot 1 con 0 ban nhap. */
    var kho = khoMay();
    var a = appMoi(kho);
    await moTrangChu(a);
    var g = a.g;
    var dk = g.sdKhoa('nop_quy', '');
    g.sdDangKy('nop_quy', 'scrNopQuyTao', dk, g.S.stack[g.S.stack.length - 1], [], '', '');
    g.sdGhi(dk, { v: 1, loai: 'nop_quy', man: 'scrNopQuyTao', ma: '', args: [], luc: Date.now(), tieu_de: '', anh: 0, js: '{"s":null,"o":{"@data-mg=500000":"3"}}' });
    var kq1 = await g.api('vagabond.nop_quy.tao', { ca: ['CA-1'] });
    bang('luot 1 may chu hoi ly do', kq1.can_ly_do, 1);
    bang('luot 1: nhap van con', cacKhoa(kho).length, 1);
    bang('luot 1: van theo doi', g.SD.dk, dk);
    var kq2 = await g.api('vagabond.nop_quy.tao', { ca: ['CA-1'], ly_do_lech: 'Thiếu tiền lẻ' });
    bang('luot 2 tao phieu', kq2.ma, 'NQ-26-1');
    bang('luot 2: het nhap', cacKhoa(kho), []);
  });

  await ca('Anh chup (base64, File) khong luu vao ban nhap; mo lai bo dung phan tu anh, giu phan con lai', async function () {
    var a = appMoi(khoMay());
    var g = a.g;
    var dai = 'data:image/jpeg;base64,' + 'A'.repeat(5000);
    var dem = { n: 0 };
    var js = JSON.stringify({ s: { photos: [{ name: 'a.jpg', b64: dai }, { name: 'b.jpg', b64: dai }], anh: dai, url: '/files/x.jpg', ghi: 'giữ' }, o: {} }, g.sdLoc(dem));
    bang('dem hai anh trong mang va mot anh le', dem.n, 3);
    dung('khong con base64 trong ban nhap', js.indexOf('base64') < 0);
    var v = g.sdMoJs({ js: js });
    bang('mang anh rong', v.s.photos, []);
    dung('bo thuoc tinh anh', !('anh' in v.s));
    bang('giu duong dan tep da tai len', v.s.url, '/files/x.jpg');
    bang('giu ghi chu', v.s.ghi, 'giữ');
  });

  await ca('Nap CA app ghep that (app_bep.js): nap khong loi, moi man duoc boc dung ten, moi dong khai doc/dat duoc trang thai that', async function () {
    /* Bat loi khong ca nao khac bat duoc: go sai ten mot bien trong dong khai
       (vi du hsHdTu) thi luc chay sdChup nuot loi va ban nhap lang le khong
       bao gio luu. Nap ca app, xuat SD_MAN ra ngoai vo roi goi tung dong. */
    var src = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'app_bep.js'), 'utf8');
    var i = src.lastIndexOf('})();');
    var ten = SOAN_DO.match(/^(\w+) = sdBoc(?:Hop)?\(/gm).map(function (x) { return x.split(' ')[0]; });
    var xuat = '\nwindow.__sdKiem = { SD_MAN: SD_MAN, giong: {' +
      ten.map(function (t) { return t + ': ' + t + ' === SD_BOC.' + t; }).join(', ') + '} };\n';
    src = src.slice(0, i) + xuat + src.slice(i);
    var tl = domGia.taiLieuGia();
    tl.head = tl.createElement('head'); tl.documentElement = tl.createElement('html');
    tl.addEventListener = function () {}; tl.readyState = 'complete';
    var kho = khoMay();
    var g = {
      console: { log: function () {}, warn: function () {}, error: function () {} }, document: tl,
      navigator: { userAgent: 'node' },
      location: { hostname: 'app.x', pathname: '/bep', search: '', hash: '', href: 'https://app.x/bep', replace: function () {} },
      history: { pushState: function () {}, replaceState: function () {}, back: function () {}, state: null },
      frappe: { session: { user: 'loananh@vagabond.vn' }, csrf_token: 'x' }, localStorage: kho, sessionStorage: khoMay(),
      fetch: function () { return Promise.resolve({ ok: false, status: 401, json: function () { return Promise.resolve({}); }, text: function () { return Promise.resolve(''); } }); },
      setTimeout: function () { return 0; }, clearTimeout: function () {}, setInterval: function () { return 0; }, clearInterval: function () {},
      requestAnimationFrame: function () {}, matchMedia: function () { return { matches: false, addEventListener: function () {}, addListener: function () {} }; },
      addEventListener: function () {}, removeEventListener: function () {}, getComputedStyle: function () { return {}; },
      URL: URL, URLSearchParams: URLSearchParams, Blob: Blob, Intl: Intl, TextEncoder: TextEncoder,
    };
    g.window = g; g.self = g;
    vm.createContext(g);
    vm.runInContext(src, g, { filename: 'app_bep.js' });
    var k = g.__sdKiem;
    dung('xuat duoc SD_MAN', !!k);
    var sai = [];
    Object.keys(k.giong).forEach(function (t) { if (!k.giong[t]) sai.push('ten ' + t + ' khong tro vao ban boc'); });
    Object.keys(k.SD_MAN).forEach(function (l) {
      var c = k.SD_MAN[l];
      try {
        var v = c.lay ? c.lay() : null;
        if (c.dat) c.dat(v && typeof v === 'object' ? JSON.parse(JSON.stringify(v)) : {}, []);
        if (typeof c.ghep === 'function') c.ghep({ lines: [] }, {});
        if (c.ma) c.ma(['X']);
        if (c.tieuDe) c.tieuDe({}, {});
        if (c.hop) c.hop();
      } catch (e) { sai.push(l + ': ' + e.message); }
    });
    bang('khong dong khai nao loi', sai, []);
    bang('du 40 loai phieu', Object.keys(k.SD_MAN).length, 40);
  });

  console.log('ban_soan_do_533: dat ' + ket.dat + ', hong ' + ket.hong);
  if (ket.hong) { ket.loi.forEach(function (l) { console.log('  HONG ' + l); }); process.exit(1); }
}

chayHet().catch(function (e) { console.error(e); process.exit(1); });
