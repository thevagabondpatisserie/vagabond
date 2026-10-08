/* Bo ca kiem HANH VI v586: trinh bien tap website theo viec va the Tiec.
 *
 * Minh Vu de xuat, anh Viet duyet 07/10/2026: bang bien tap theo khoi kho
 * dung, chia lai theo viec (Uu dai, Tiec, Tuyen dung, Cua hang, Trang va chu,
 * Lien he), luu la khach thay ngay.
 *
 * Nap THAT chuyen-muc.js va bien-tap-moi.js vao DOM gia; chi may chu la ban
 * gia. Ca kiem bam, go, bat tat nhu nguoi dung, khong goi ham noi bo nao
 * "cho chac" (quy tac 15). Bang mau trang thai dung CHUNG voi ca kiem Python.
 *
 * Chay: node vagabond/khung/kiem_thu/hanh_vi/bien_tap_586.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var WEB = path.join(GOC, 'vagabond', 'public', 'web_order');
function doc(t) { return fs.readFileSync(path.join(WEB, t), 'utf8'); }
var MAU_TT = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'mau_web', 'trang_thai_586.json'), 'utf8'));

var ket = { dat: 0, hong: 0, loi: [] };
var xongHet = false;
process.on('exit', function () { if (!xongHet) { console.log('  HONG  bo kiem dung giua chung: co loi hua treo mai'); process.exitCode = 1; } });
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
function dung(mo, x) { if (!x) throw new Error(mo); }
async function ca(ten, ham) { try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : e)); } }
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

function dau(x) { return 'd-' + JSON.stringify(x).length + '-' + (x.tieu_de || x.ten || ''); }
function duLieu() {
  var khoi = [
    { id: 'u1', loai: 'uu_dai', vi_tri: 'uu_dai', hien: true, tieu_de: 'Giảm 10% sinh nhật', ma_uu_dai: 'SN10', don_toi_thieu: '500000', bat_dau: '2026-09-25', ket_thuc: '2026-10-20', gio_bat_dau: '07:00', gio_ket_thuc: '21:00' },
    { id: 'u2', loai: 'uu_dai', vi_tri: 'uu_dai', hien: true, tieu_de: 'Hết hạn', ket_thuc: '2026-10-01' },
    { id: 'td1', loai: 'tuyen_dung', vi_tri: 'tuyen_dung', hien: true, tieu_de: 'Thợ bánh mì (Boulanger)', noi_lam: 'Bếp Tân Sơn Hoà', hinh_thuc: 'Toàn thời gian, ca sáng sớm', email: 'hr@vgb.vn' },
    { id: 'tiec-1', loai: 'tiec', vi_tri: 'tiec', hien: true, tieu_de: 'Trà chiều', bat_dau: '2026-10-18', gio_bat_dau: '15:00', gio_ket_thuc: '17:00', dia_diem: 'Cửa hàng Sài Gòn', gia_ve: '350000', so_ve: '40' },
  ];
  var B = {
    khoi: khoi, dau: {}, thong_tin: { cua_hang: [
      { id: 'bep-tan-son-hoa', ten: 'Bếp Tân Sơn Hoà', dia_chi: '307/1 Nguyễn Văn Trỗi', gio_mo_cua: '', hotline: '', chi_duong: '', loai: 'bep', nhan_banh: true, hien: false },
      { id: 'cua-hang-sai-gon', ten: 'Cửa hàng Sài Gòn', dia_chi: '9 Trần Cao Vân', gio_mo_cua: '', hotline: '', chi_duong: '', loai: 'cua_hang', nhan_banh: true, hien: true },
    ] }, dau_thong_tin: { cua_hang: 'dch' },
    lien_he: { dien_thoai: '0931 224 334', email: 'hello@thevagabondpatisserie.com', zalo: '', messenger: 'https://m.me/a', facebook: '', instagram: '', tiktok: '' },
    dau_lien_he: 'dlh', nhan: { tab_today: 'Bánh vừa ra lò' },
    nhan_mau: {
      tab_today: { ten: 'Tab bánh có sẵn hôm nay', mac_dinh: 'Có sẵn hôm nay' },
      cau_co_san: { ten: 'Dòng số bánh có sẵn', mac_dinh: '{so} bánh có sẵn' },
      dat_ban_tieu_de: { ten: 'Đặt bàn: tiêu đề', mac_dinh: 'Đặt bàn tại Vagabond.', nhom: 'dat_ban' },
    },
    nhom_nhan: { '': 'Thanh chọn và đầu trang', dat_ban: 'Trang đặt bàn' },
    ve: { 'tiec-1': 12 }, hom_nay: '2026-10-07',
    phap_nhan: { ten: 'Công ty TNHH Patisserie Vagabond', mst: '0318561568', dia_chi: [{ ten: 'Cửa hàng Sài Gòn', dia_chi: '9 Trần Cao Vân' }] },
    nhap_chua_xuat_ban: 0, phien_ban: 7,
  };
  khoi.forEach(function (k) { B.dau[k.id] = dau(k); });
  return B;
}

function appMoi(tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc('<main id="bt-moi"><p id="bt-trang-thai"></p><nav id="bt-the"></nav><div id="bt-noi"></div></main><div id="bt-cu" hidden><button id="tai-lai"></button><button id="bt-ve-moi"></button></div>', tl.body);
  var B = duLieu();
  var goi = [];
  var taiLai = 0;
  tl.getElementById('tai-lai').onclick = function () { taiLai++; };
  function tra(msg) { return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: msg }); } }); }
  function loi(chu) { return Promise.resolve({ ok: false, status: 417, json: function () { return Promise.resolve({ exc: 'x', _server_messages: JSON.stringify([JSON.stringify({ message: chu })]) }); } }); }
  function fetchGia(url, cau) {
    var ham = String(url).split('.').pop();
    var a = cau && cau.body ? JSON.parse(cau.body) : null;
    goi.push({ ham: ham, a: a });
    if (tuy.loi && tuy.loi[ham]) return loi(tuy.loi[ham]);
    if (ham === 'bang_moi') return tra(JSON.parse(JSON.stringify(B)));
    if (ham === 'luu_muc') {
      var i = B.khoi.findIndex(function (k) { return k.id === a.muc.id; });
      if (i >= 0) B.khoi[i] = a.muc; else B.khoi.unshift(a.muc);
      B.dau[a.muc.id] = dau(a.muc);
      return tra(JSON.parse(JSON.stringify(B)));
    }
    if (ham === 'xoa_muc_web') { B.khoi = B.khoi.filter(function (k) { return k.id !== a.id_muc; }); return tra(JSON.parse(JSON.stringify(B))); }
    if (ham === 'luu_thong_tin') { B.thong_tin.cua_hang = a.gia_tri; return tra(JSON.parse(JSON.stringify(B))); }
    if (ham === 'luu_lien_he') { B.lien_he = a.gia_tri; return tra(JSON.parse(JSON.stringify(B))); }
    if (ham === 'luu_nhan') { Object.keys(a.thay).forEach(function (k) { if (a.thay[k][1]) B.nhan[k] = a.thay[k][1]; else delete B.nhan[k]; }); return tra(JSON.parse(JSON.stringify(B))); }
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
    RegExp: RegExp, Date: Date, Intl: Intl, Set: Set, parseInt: parseInt, encodeURIComponent: encodeURIComponent, document: docu, fetch: fetchGia };
  g.window = g;
  vm.createContext(g);
  vm.runInContext(doc('chuyen-muc.js'), g, { filename: 'chuyen-muc.js' });
  vm.runInContext(doc('bien-tap-moi.js'), g, { filename: 'bien-tap-moi.js' });
  var app = {
    g: g, tl: tl, goi: goi, B: function () { return B; }, taiLai: function () { return taiLai; },
    tim: function (c) { return tl.body.querySelectorAll(c); },
    mot: function (c) { var r = tl.body.querySelectorAll(c); if (r.length !== 1) throw new Error('mong dung 1 ' + c + ', co ' + r.length); return r[0]; },
    bam: async function (el) { el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); },
    go: async function (el, v) { el.value = v; el.oninput(); await nghi(); },
    oTen: function (ten) { return app.mot('[name="' + ten + '"]'); },
    luu: async function () { var f = app.mot('.bt-form'); f.onsubmit({ preventDefault: function () {} }); await nghi(); },
    dem: function (ham) { return goi.filter(function (x) { return x.ham === ham; }).length; },
    cuoi: function (ham) { var r = goi.filter(function (x) { return x.ham === ham; }); return r[r.length - 1].a; },
    bao: function () { return String(tl.getElementById('bt-trang-thai').textContent); },
    the: async function (k) { await app.bam(app.mot('[data-the="' + k + '"]')); },
  };
  return app;
}

(async function () {
  await ca('Bang mau trang thai chung voi may chu', async function () {
    var app = appMoi(); await nghi();
    var sai = MAU_TT.ca.filter(function (c) { return JSON.stringify(app.g.VgbBienTapMoi.trangThai(c[0], MAU_TT.hom_nay)) !== JSON.stringify([c[1], c[2]]); });
    bang('khong dong nao lech', sai, []);
  });

  await ca('Sau the va Nang cao, co dem so muc, the Uu dai mo san voi trang thai dung', async function () {
    var app = appMoi(); await nghi();
    bang('7 o the', app.tim('[data-the]').map(function (b) { return b.dataset.the; }), ['uu_dai', 'tiec', 'tuyen_dung', 'cua_hang', 'chu', 'lien_he', 'nang_cao']);
    dung('dem uu dai', String(app.mot('[data-the="uu_dai"]').textContent).indexOf('Ưu đãi2') === 0);
    var u1 = String(app.mot('[data-muc="u1"]').textContent);
    dung('dang dien ra', u1.indexOf('Đang diễn ra') >= 0);
    dung('dong tom tat', u1.indexOf('Mã SN10 · Đơn từ 500.000 đ · 7g00 - 21g00 · 25/09/2026 - 20/10/2026') >= 0);
    dung('khach dang thay', u1.indexOf('Khách đang thấy') >= 0);
    var u2 = String(app.mot('[data-muc="u2"]').textContent);
    dung('het han noi ro khach khong thay', u2.indexOf('Đã kết thúc') >= 0 && u2.indexOf('Đã hết hạn, khách không thấy') >= 0);
  });

  await ca('Them vi tri tuyen dung: chon noi lam, hinh thuc nhieu, email dien san, luu goi luu_muc dung', async function () {
    var app = appMoi(); await nghi();
    await app.the('tuyen_dung');
    await app.bam(app.mot('[data-them="tuyen_dung"]'));
    bang('email dien san tu the Lien he', app.oTen('email').value, 'hello@thevagabondpatisserie.com');
    await app.go(app.oTen('tieu_de'), 'Barista');
    await app.bam(app.tim('[data-chip="Cửa hàng Sài Gòn"]')[0]);
    await app.bam(app.mot('[data-chip="Bán thời gian"]'));
    await app.go(app.oTen('yeu_cau'), 'Thân thiện\nĐược ăn bánh');
    await app.luu();
    bang('goi mot lan', app.dem('luu_muc'), 1);
    var a = app.cuoi('luu_muc');
    bang('muc moi', [a.dau_cu, a.muc.loai, a.muc.tieu_de, a.muc.noi_lam, a.muc.hinh_thuc, a.muc.hien], ['', 'tuyen_dung', 'Barista', 'Cửa hàng Sài Gòn', 'Toàn thời gian / Bán thời gian', true]);
    dung('ve lai danh sach', app.tim('.bt-form').length === 0 && app.tim('[data-muc]').length === 2);
    dung('bao da luu', app.bao().indexOf('Đã lưu vị trí "Barista"') === 0);
  });

  await ca('Hinh thuc cu go tay khong mat khi bam chip', async function () {
    var app = appMoi(); await nghi();
    await app.the('tuyen_dung');
    var d0 = app.B().dau.td1;
    await app.bam(app.mot('[data-sua="td1"]'));
    bang('chu cu nam o o ghi them', app.oTen('hinh_thuc_khac').value, 'Toàn thời gian, ca sáng sớm');
    await app.bam(app.mot('[data-chip="Bán thời gian"]'));
    await app.luu();
    var a = app.cuoi('luu_muc');
    bang('giu chu cu', a.muc.hinh_thuc, 'Bán thời gian / Toàn thời gian, ca sáng sớm');
    bang('dau cu la dau luc mo form', a.dau_cu, d0);
  });

  await ca('Cong tac Hien tren web luu ngay voi dau cu cua muc', async function () {
    var app = appMoi(); await nghi();
    var d0 = app.B().dau.u1;
    var i = app.mot('[data-cong-tac="u1"]').querySelector('input');
    i.checked = false; i.onchange(); await nghi();
    var a = app.cuoi('luu_muc');
    bang('tat hien', [a.muc.id, a.muc.hien, a.dau_cu], ['u1', false, d0]);
    dung('ve lai thanh dang an', String(app.mot('[data-muc="u1"]').textContent).indexOf('Đang ẩn') >= 0);
  });

  await ca('Xoa: hoi lai, bam Thoi khong xoa, bam Xoa moi goi may chu', async function () {
    var app = appMoi(); await nghi();
    await app.bam(app.mot('[data-xoa="u1"]'));
    await app.bam(app.mot('[data-hop-thoi]'));
    bang('khong xoa', app.dem('xoa_muc_web'), 0);
    await app.bam(app.mot('[data-xoa="u1"]'));
    await app.bam(app.mot('[data-hop-co]'));
    bang('xoa dung muc', [app.dem('xoa_muc_web'), app.cuoi('xoa_muc_web').id_muc], [1, 'u1']);
    bang('con mot uu dai', app.tim('[data-muc]').length, 1);
  });

  await ca('Uu dai: o so chi nhan chu so, khung xem truoc hien dieu kien nhu trang khach', async function () {
    var app = appMoi(); await nghi();
    await app.bam(app.mot('[data-them="uu_dai"]'));
    await app.go(app.oTen('tieu_de'), 'Giảm 15%');
    await app.go(app.oTen('don_toi_thieu'), '500.000đ');
    bang('chi con chu so', app.oTen('don_toi_thieu').value, '500000');
    await app.go(app.oTen('gio_bat_dau'), '07:00');
    await app.go(app.oTen('gio_ket_thuc'), '21:00');
    var xem = String(app.mot('.bt-xem').textContent);
    dung('xem truoc co dieu kien', xem.indexOf('Đơn từ 500.000 đ · Khung giờ 7g00 - 21g00') >= 0);
    dung('xem truoc co ten', xem.indexOf('Giảm 15%') >= 0);
    dung('dong tom tat dieu kien', String(app.mot('[data-dieu-kien]').textContent).indexOf('Khách sẽ thấy điều kiện: Đơn từ 500.000 đ · Khung giờ 7g00 - 21g00') === 0);
  });

  await ca('Thieu mot o gio thi chan ngay o may khach, khong goi may chu', async function () {
    var app = appMoi(); await nghi();
    await app.bam(app.mot('[data-them="uu_dai"]'));
    await app.go(app.oTen('tieu_de'), 'Giảm');
    await app.go(app.oTen('gio_bat_dau'), '07:00');
    await app.luu();
    bang('khong goi', app.dem('luu_muc'), 0);
    dung('bao ro', app.bao().indexOf('cả hai ô giờ') >= 0);
  });

  await ca('Dang sua chua luu ma doi the: hoi lai, Thoi thi o lai form', async function () {
    var app = appMoi(); await nghi();
    await app.bam(app.mot('[data-sua="u1"]'));
    await app.go(app.oTen('tieu_de'), 'Đổi tên');
    await app.the('tiec');
    dung('co hop hoi', app.tim('[data-hop-thoi]').length === 1);
    await app.bam(app.mot('[data-hop-thoi]'));
    dung('van o form', app.tim('.bt-form').length === 1 && app.oTen('tieu_de').value === 'Đổi tên');
    await app.the('tiec');
    await app.bam(app.mot('[data-hop-co]'));
    dung('sang the Tiec', app.tim('[data-muc="tiec-1"]').length === 1);
  });

  await ca('Tiec: dong tom tat co ngay, gio, gia, so ve da dang ky', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    var t = String(app.mot('[data-muc="tiec-1"]').textContent);
    dung('tom tat', t.indexOf('Chủ nhật, 18/10/2026 · 15g00 - 17g00 · Cửa hàng Sài Gòn · 350.000 đ/vé · Đã đăng ký 12/40 vé') >= 0);
  });

  await ca('Loi may chu hien nguyen cau, form giu nguyen chu dang go', async function () {
    var app = appMoi({ loi: { luu_muc: 'Có người vừa sửa hoặc xoá mục này. Tải lại để xem bản mới rồi sửa tiếp.' } }); await nghi();
    await app.bam(app.mot('[data-sua="u1"]'));
    await app.go(app.oTen('tieu_de'), 'Tên mới');
    await app.luu();
    dung('cau bao', app.bao().indexOf('Có người vừa sửa') === 0);
    bang('van giu chu', app.oTen('tieu_de').value, 'Tên mới');
  });

  await ca('Cua hang: sua gio mo cua, luu ca danh sach voi dau cu', async function () {
    var app = appMoi(); await nghi();
    await app.the('cua_hang');
    await app.bam(app.mot('[data-sua="cua-hang-sai-gon"]'));
    await app.go(app.oTen('gio_mo_cua'), '7:00 - 21:00');
    await app.luu();
    var a = app.cuoi('luu_thong_tin');
    bang('phan', a.phan, 'cua_hang');
    bang('ca danh sach, dung thu tu', a.gia_tri.map(function (c) { return c.id; }), ['bep-tan-son-hoa', 'cua-hang-sai-gon']);
    bang('gio moi', a.gia_tri[1].gio_mo_cua, '7:00 - 21:00');
    bang('dau cu', a.dau_cu, 'dch');
  });

  await ca('Lien he: luu bay o vao luu_lien_he, cong ty chi doc', async function () {
    var app = appMoi(); await nghi();
    await app.the('lien_he');
    dung('cong ty chi doc', String(app.mot('.bt-chi-doc').textContent).indexOf('0318561568') >= 0 && app.tim('[name="mst"]').length === 0);
    await app.go(app.oTen('dien_thoai'), '0909 000 111');
    await app.luu();
    var a = app.cuoi('luu_lien_he');
    bang('so moi', a.gia_tri.dien_thoai, '0909 000 111');
    bang('dau cu', a.dau_cu, 'dlh');
    bang('du bay o', Object.keys(a.gia_tri).sort(), ['dien_thoai', 'email', 'facebook', 'instagram', 'messenger', 'tiktok', 'zalo']);
  });

  await ca('Trang va chu: thieu cho dien thi chan, sua dung thi gui cap [chu cu, chu moi]', async function () {
    var app = appMoi(); await nghi();
    await app.the('chu');
    var o = app.mot('[data-khoa="cau_co_san"]').querySelector('input');
    await app.go(o, 'bánh có sẵn');
    dung('bao giu cho dien', String(app.mot('[data-khoa="cau_co_san"]').textContent).indexOf('Giữ nguyên {so}') >= 0);
    await app.bam(app.mot('.bt-chan-luu').querySelector('[data-luu]'));
    bang('khong goi', app.dem('luu_nhan'), 0);
    await app.go(o, 'Còn {so} bánh');
    await app.go(app.mot('[data-khoa="tab_today"]').querySelector('input'), '');
    await app.bam(app.mot('.bt-chan-luu').querySelector('[data-luu]'));
    bang('gui cap', app.cuoi('luu_nhan').thay, { cau_co_san: ['', 'Còn {so} bánh'], tab_today: ['Bánh vừa ra lò', ''] });
  });

  await ca('Nang cao mo bang cu va tai lai ban moi nhat, quay ve thi tai lai the', async function () {
    var app = appMoi(); await nghi();
    await app.the('nang_cao');
    dung('an trinh moi', app.tl.getElementById('bt-moi').hidden === true && app.tl.getElementById('bt-cu').hidden === false);
    bang('bam Tai lai cua bang cu', app.taiLai(), 1);
    var truoc = app.dem('bang_moi');
    await app.bam(app.tl.getElementById('bt-ve-moi'));
    bang('tai lai the', app.dem('bang_moi'), truoc + 1);
  });

  /* ---------------- trang khach: the Tiec (chuyen-muc.js) ---------------- */
  function trangKhach(ve, them, khoiThem) {
    var tl = dg.taiLieuGia();
    dg.doc('<button data-tab="tiec" hidden></button><div id="noi-uu_dai"></div><div id="noi-tuyen_dung"></div><div id="noi-tiec"></div>', tl.body);
    var guiDi = [];
    var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise, Error: Error,
      RegExp: RegExp, Date: Date, Intl: Intl, Set: Set, parseInt: parseInt, encodeURIComponent: encodeURIComponent,
      crypto: { randomUUID: function () { return '0f0e0d0c-0b0a-4908-8706-050403020100'; } },
      document: { body: tl.body, createElement: tl.createElement, getElementById: tl.getElementById, addEventListener: function () {},
        querySelector: function (c) { return tl.querySelector(c); }, querySelectorAll: function (c) { return tl.querySelectorAll(c); } },
      fetch: function (url, cau) { guiDi.push({ url: url, body: JSON.parse(cau.body), headers: cau.headers, credentials: cau.credentials }); return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: { ok: 1, ma: 'AB12CD34' } }); } }); } };
    g.window = g;
    Object.assign(g, them || {});
    vm.createContext(g);
    vm.runInContext(doc('chuyen-muc.js'), g);
    var homNay = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    var mai = new Date(Date.parse(homNay) + 86400000 * 10).toISOString().slice(0, 10);
    var hom_qua = new Date(Date.parse(homNay) - 86400000).toISOString().slice(0, 10);
    g.vgbVeChuyenMuc({ khoi: [
      { id: 't1', loai: 'tiec', hien: true, tieu_de: 'Trà chiều', bat_dau: mai, gia_ve: '350000', so_ve: '40' },
      { id: 't2', loai: 'tiec', hien: true, tieu_de: 'Hết vé', bat_dau: mai, so_ve: '10' },
      { id: 't3', loai: 'tiec', hien: true, tieu_de: 'Đã qua', bat_dau: hom_qua },
      { id: 't4', loai: 'tiec', hien: false, tieu_de: 'Ẩn', bat_dau: mai },
    ].concat(khoiThem || []), ve: ve || { t1: 38, t2: 10 } });
    return { tl: tl, g: g, guiDi: guiDi, mot: function (c) { return tl.body.querySelector(c); } };
  }

  await ca('Trang khach: chi hien tiec chua dien ra va dang bat, hien so ve con, het ve thi khong co nut', async function () {
    var t = trangKhach();
    var the = t.tl.body.querySelectorAll('[data-khoi]').map(function (e) { return e.dataset.khoi; });
    bang('tiec hien', the, ['t1', 't2']);
    dung('tab Tiec bat len', t.mot('[data-tab="tiec"]').hidden === false);
    var t1 = String(t.tl.body.querySelector('[data-khoi="t1"]').textContent);
    dung('gia va ve con', t1.indexOf('350.000 đ / vé') >= 0 && t1.indexOf('Còn 2 vé') >= 0);
    var t2 = t.tl.body.querySelector('[data-khoi="t2"]');
    dung('het ve', String(t2.textContent).indexOf('Đã hết vé') >= 0 && t2.querySelectorAll('button').length === 0);
  });

  await ca('Trang khach: dang ky tiec gui dung du lieu, so ve toi da bang so ve con', async function () {
    var t = trangKhach();
    var the = t.tl.body.querySelector('[data-khoi="t1"]');
    await (async function () { the.querySelector('button').dispatchEvent(dg.suKien('click', {}, the.querySelector('button'))); await nghi(); })();
    var f = the.querySelector('form');
    dung('mo form', !!f);
    bang('toi da 2 ve', f.querySelector('[name="so_ve"]').max, 2);
    f.querySelector('[name="ten"]').value = 'Lan';
    f.querySelector('[name="sdt"]').value = '0909123456';
    f.querySelector('[name="so_ve"]').value = '2';
    f.onsubmit({ preventDefault: function () {} }); await nghi();
    bang('mot lan gui', t.guiDi.length, 1);
    dung('dung cua', t.guiDi[0].url.indexOf('vagabond.tiec_web.dang_ky') >= 0);
    bang('du lieu', t.guiDi[0].body.du_lieu, { tiec_id: 't1', ten: 'Lan', sdt: '0909123456', so_ve: '2', ghi_chu: '' });
    dung('bao ma', String(the.textContent).indexOf('mã AB12CD34') >= 0);
  });

  async function guiDangKy(t) {
    var the = t.tl.body.querySelector('[data-khoi="t1"]');
    the.querySelector('button').dispatchEvent(dg.suKien('click', {}, the.querySelector('button'))); await nghi();
    var f = the.querySelector('form');
    f.querySelector('[name="ten"]').value = 'Lan'; f.querySelector('[name="sdt"]').value = '0909123456'; f.querySelector('[name="so_ve"]').value = '1';
    f.onsubmit({ preventDefault: function () {} }); await nghi();
    return t.guiDi[0];
  }

  await ca('Trang khach (Codex #454): nhan vien dang dang nhap gui dang ky tiec co kem CSRF', async function () {
    var g1 = await guiDangKy(trangKhach(null, { frappe: { csrf_token: 'tk-frappe' } }));
    bang('lay tu frappe.csrf_token', g1.headers['X-Frappe-CSRF-Token'], 'tk-frappe');
    bang('gui kem cookie cung nguon', g1.credentials, 'same-origin');
    var g2 = await guiDangKy(trangKhach(null, { csrf_token: 'tk-win' }));
    bang('hoac window.csrf_token', g2.headers['X-Frappe-CSRF-Token'], 'tk-win');
    var g3 = await guiDangKy(trangKhach(null, { csrf_token: 'None' }));
    dung('khach vang lai: khong gui token gia', !('X-Frappe-CSRF-Token' in g3.headers));
  });

  /* ---------------- v587 phuong an B: chu dai gap, thuc don nhan, ten muc (Minh Vu 08/10) ---------------- */
  var CHU_DAI = new Array(60).join('Mùa xuân năm 1934, báo Phong Hóa mở chuyên mục. ');
  var MON_12 = ['Bánh dẻo trứng muối', 'Bánh bò thốt nốt', 'Bánh đậu xanh', 'Bánh lọt', 'Kem dừa sáp', 'Gỏi bưởi', 'Bánh ram ít', 'Bánh ít khổ qua', 'Bánh da lợn', 'Chè trôi nước', 'Bánh cam', 'Bánh tiêu'].join('\n');

  await ca('v587 tiec: chu dai gap 5 dong co nut Doc tiep, bam thi mo roi Thu gon; chu ngan khong co nut', async function () {
    var t = trangKhach(null, null, [
      { id: 'td', loai: 'tiec', hien: true, tieu_de: 'Dài', bat_dau: '2099-01-01', noi_dung: CHU_DAI, yeu_cau: MON_12, so_ve: '40', gia_ve: '550000' },
      { id: 'tn', loai: 'tiec', hien: true, tieu_de: 'Ngắn', bat_dau: '2099-01-01', noi_dung: 'Một câu.', so_ve: '40' },
    ]);
    var dai = t.tl.body.querySelector('[data-khoi="td"]'), ngan = t.tl.body.querySelector('[data-khoi="tn"]');
    var doan = dai.querySelector('.cm-doan'), nut = dai.querySelector('.cm-doc-tiep');
    dung('chu dai co lop gap va nut Doc tiep', doan.className.indexOf('cm-gap') >= 0 && nut && String(nut.textContent) === 'Đọc tiếp');
    nut.onclick();
    dung('bam thi bo gap, nut thanh Thu gon', doan.className.indexOf('cm-gap') < 0 && String(nut.textContent) === 'Thu gọn' && nut.getAttribute('aria-expanded') === 'true');
    nut.onclick();
    dung('bam lan nua thi gap lai', doan.className.indexOf('cm-gap') >= 0);
    dung('chu ngan khong co nut', !ngan.querySelector('.cm-doc-tiep') && ngan.querySelector('.cm-doan').className.indexOf('cm-gap') < 0);
  });

  await ca('v587 tiec: thuc don 12 mon hien 8 nhan va "+ 4 mon nua", bam thi hien du 12', async function () {
    var t = trangKhach(null, null, [{ id: 'td', loai: 'tiec', hien: true, tieu_de: 'Dài', bat_dau: '2099-01-01', noi_dung: 'x', yeu_cau: MON_12, so_ve: '40' }]);
    var dai = t.tl.body.querySelector('[data-khoi="td"]');
    var nhan = function () { return dai.querySelectorAll('.cm-mon-nhan').filter(function (x) { return x.className.indexOf('cm-mon-them') < 0; }); };
    var them = dai.querySelector('.cm-mon-them');
    bang('8 nhan dau', nhan().length, 8);
    bang('nut mo phan con lai', String(them.textContent), '+ 4 món nữa');
    bang('dem mon o tieu de', String(dai.querySelector('.cm-dem').textContent), '12 món');
    them.onclick();
    bang('du 12 nhan', nhan().length, 12);
    dung('nut bien mat', !dai.querySelector('.cm-mon-them'));
    dung('khong con danh sach cham cu', !dai.querySelector('.cm-ds'));
  });

  await ca('v587 tiec: hop thong tin tren anh co nhan gop, gia, vach ve con, nut Dang ky; form mo duoi than', async function () {
    var t = trangKhach();
    var the = t.tl.body.querySelector('[data-khoi="t1"]');
    var hop = the.querySelector('.cm-hop');
    dung('hop nam trong hero', hop && hop.parentNode.className.indexOf('cm-hero') >= 0);
    dung('nhan gop trang thai va ve con', String(hop.querySelector('.cm-nhan').textContent).indexOf('Còn 2 vé') >= 0);
    dung('vach ve con 95%', hop.querySelector('.cm-vach-thanh').querySelector('i').style.width === '95%');
    var nut = hop.querySelector('.cm-nut');
    dung('nut Dang ky trong hop', nut && String(nut.textContent) === 'Đăng ký tham gia');
    nut.dispatchEvent(dg.suKien('click', {}, nut)); await nghi();
    dung('form mo trong than, khong trong hop', the.querySelector('.cm-than').querySelector('.cm-dk') && !hop.querySelector('.cm-dk'));
    var het = t.tl.body.querySelector('[data-khoi="t2"]');
    dung('het ve: khong co nut, nhan bao het', !het.querySelector('.cm-nut') && String(het.querySelector('.cm-nhan').textContent).indexOf('Đã hết vé') >= 0);
  });

  await ca('v587 uu dai: nhan va Sap dien ra mot dong, ngay trung ghi mot lan, ma uu dai co o rieng', async function () {
    var mai = new Date(Date.now() + 86400000 * 10).toISOString().slice(0, 10);
    var t = trangKhach(null, null, [{ id: 'u9', loai: 'uu_dai', hien: true, nhom: 'Sinh nhật', tieu_de: 'Freeship 15k', bat_dau: mai, ket_thuc: mai, ma_uu_dai: 'SINHNHAT10', noi_dung: 'x' }]);
    var u = t.tl.body.querySelector('[data-khoi="u9"]');
    bang('nhan gop', String(u.querySelector('.cm-nhan').textContent), 'Sinh nhật · Sắp diễn ra');
    bang('ngay mot lan', String(u.querySelector('.cm-ngay').textContent), mai.split('-').reverse().join('/'));
    bang('ma trong o rieng', String(u.querySelector('.cm-ma').querySelector('b').textContent), 'SINHNHAT10');
    bang('khong con dong trang thai rieng', u.querySelectorAll('.cm-trang-thai').length, 0);
  });

  /* ---------------- Nang cao (bien-tap.js): tran so khoi do may chu quyet (Codex #454) ---------------- */
  function nangCao(soKhoi, toiDa) {
    // DOM gia thieu vai API ma bien-tap.js dung luc dung bang; bu toi thieu.
    var EP = dg.ElementGia.prototype;
    if (!EP.before) EP.before = function () { var p = this.parentNode, me = this; [].slice.call(arguments).forEach(function (n) { p.insertBefore(n, me); }); };
    if (!Object.getOwnPropertyDescriptor(EP, 'classList')) Object.defineProperty(EP, 'classList', { get: function () {
      var el = this; function ds() { return (el.getAttribute('class') || '').split(/\s+/).filter(Boolean); }
      return { add: function (c) { var d = ds(); if (d.indexOf(c) < 0) d.push(c); el.setAttribute('class', d.join(' ')); },
        remove: function (c) { el.setAttribute('class', ds().filter(function (x) { return x !== c; }).join(' ')); },
        toggle: function (c, f) { var d = ds(), co = d.indexOf(c) >= 0; if (f === undefined) f = !co; d = d.filter(function (x) { return x !== c; }); if (f) d.push(c); el.setAttribute('class', d.join(' ')); return f; },
        contains: function (c) { return ds().indexOf(c) >= 0; } }; } });
    var ht = fs.readFileSync(path.join(GOC, 'vagabond', 'www', 'bien-tap-web.html'), 'utf8');
    var than = ht.slice(ht.indexOf('<div id="bt-cu"'), ht.indexOf('<script src="/assets/vagabond/web_order/khoi.js'));
    var tl = dg.taiLieuGia(); dg.doc(than, tl.body); tl.body.dataset.nguoi = 'mv';
    tl.getElementById('preview').contentWindow = { postMessage: function () {} };
    var khoi = [];
    for (var i = 0; i < soKhoi; i++) khoi.push({ id: 'k' + i, loai: 'thong_bao', hien: true, vi_tri: 'cuoi_trang', tieu_de: 'K' + i, noi_dung: '', nhan: '', anh: '', mo_ta_anh: '', nut: '', lien_ket: '' });
    var nd = { khoi: khoi, nhan: {}, chinh_sach: {} };
    var B = { nhap: nd, cong_khai: nd, phien_ban: 1, lich_su: [], nhan_mau: {}, so_khoi_toi_da: toiDa };
    var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise, Error: Error,
      RegExp: RegExp, Date: Date, Intl: Intl, Set: Set, Map: Map, parseInt: parseInt, encodeURIComponent: encodeURIComponent, setTimeout: setTimeout,
      structuredClone: function (x) { return JSON.parse(JSON.stringify(x)); }, crypto: { randomUUID: function () { return 'u' + Math.random(); } },
      sessionStorage: { getItem: function () { return null; }, setItem: function () {}, removeItem: function () {} }, location: { origin: 'x' },
      ResizeObserver: function () { this.observe = function () {}; },
      document: { body: tl.body, createElement: tl.createElement, getElementById: tl.getElementById, addEventListener: function () {},
        createTextNode: function (x) { var e = tl.createElement('span'); e.textContent = x; return e; },
        querySelector: function (c) { return c.indexOf('meta') === 0 ? { content: 'csrf' } : (tl.querySelector(c) || {}); },
        querySelectorAll: function (c) { return tl.querySelectorAll(c); } },
      fetch: function () { return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: JSON.parse(JSON.stringify(B)) }); } }); } };
    g.window = g; g.addEventListener = function () {}; g.confirm = function () { return true; };
    vm.createContext(g);
    vm.runInContext(doc('khoi.js'), g, { filename: 'khoi.js' });
    vm.runInContext(doc('bien-tap.js'), g, { filename: 'bien-tap.js' });
    return { tl: tl,
      them: async function (ten) { await nghi(); var b = [].slice.call(tl.getElementById('them-khoi').children).filter(function (x) { return String(x.textContent).indexOf(ten) >= 0; })[0]; b.onclick(); await nghi(); },
      so: function () { return String(tl.getElementById('so-khoi').textContent); },
      bao: function () { return String(tl.getElementById('trang-thai').textContent); } };
  }

  await ca('Nang cao: may chu cho 80 khoi thi da co 30 van them duoc (truoc v586b bi chan o 30)', async function () {
    var n = nangCao(30, 80);
    await n.them('Thông báo');
    bang('them duoc khoi thu 31', n.so(), '31');
  });

  await ca('Nang cao: cham tran may chu dat thi chan, cau bao noi dung so may chu', async function () {
    var n = nangCao(12, 12);
    await n.them('Thông báo');
    bang('khong them', n.so(), '12');
    dung('cau bao dung tran', n.bao().indexOf('Đã có 12 khối') >= 0);
  });

  console.log('Bo ca kiem HANH VI v586: trinh bien tap theo the va the Tiec');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  xongHet = true;
  process.exit(ket.hong ? 1 : 0);
})();
