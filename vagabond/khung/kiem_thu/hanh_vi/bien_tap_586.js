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
    { id: 'td2', loai: 'tuyen_dung', vi_tri: 'tuyen_dung', hien: true, tieu_de: 'Thu ngân', noi_lam: 'Cửa hàng Sài Gòn', hinh_thuc: 'Bán thời gian', email: 'hr@vgb.vn' },
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
    /* v589: ưu đãi lấy từ ERP (khuyen_mai.ds_web_bien_tap). Hai mục u1, u2 gõ
       tay ở trên vẫn nằm trong dữ liệu cũ nhưng thẻ Ưu đãi không còn hiện. */
    uu_dai_erp: [
      { id: 'erp-SN10', ma_ctkm: 'SN10', loai: 'uu_dai', tieu_de: 'Giảm 10% sinh nhật', ma_uu_dai: 'SN10', don_toi_thieu: 500000, bat_dau: '2026-09-25', ket_thuc: '2026-10-20', gio_bat_dau: '07:00', gio_ket_thuc: '21:00', dung_web: 1, khach_thay: 1, trang_thai_erp: 'Khách đang thấy' },
      { id: 'erp-TANG', ma_ctkm: 'TANG', loai: 'uu_dai', tieu_de: 'Tặng ly trà', dung_web: 0, khach_thay: 0, trang_thai_erp: 'Đang tắt trên ERP, khách không thấy' },
    ],
    /* v622: vị trí tuyển dụng lấy từ app (tuyen_dung.ds_web_bien_tap). Hai mục
       td1, td2 gõ tay ở trên vẫn nằm trong dữ liệu cũ nhưng thẻ không còn hiện. */
    tuyen_dung_erp: [
      /* v630: anh_the là ảnh khách thấy, anh_web là ảnh đã chọn (trống: tự chọn theo bộ phận). */
      { id: 'erp-td-VTT-0001', ma_vi_tri: 'VTT-0001', loai: 'tuyen_dung', tieu_de: 'Thu ngân ca tối', noi_lam: 'The Vagabond District 1', hinh_thuc: 'Bán thời gian', ket_thuc: '', khach_thay: 1, trang_thai_erp: 'Khách đang thấy',
        anh_the: '/assets/vagabond/images/quay-sales.jpg', anh_web: '' },
      { id: 'erp-td-VTT-0002', ma_vi_tri: 'VTT-0002', loai: 'tuyen_dung', tieu_de: 'Phụ bếp Pastry', noi_lam: '', hinh_thuc: 'Toàn thời gian', ket_thuc: '2026-10-31', khach_thay: 0, trang_thai_erp: 'Đang tắt trên app, khách không thấy',
        anh_the: '/files/web-pastry.jpg', anh_web: '/files/web-pastry.jpg' },
    ],
  };
  khoi.forEach(function (k) { B.dau[k.id] = dau(k); });
  return B;
}

function appMoi(tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc('<main id="bt-moi"><p id="bt-trang-thai"></p><nav id="bt-the"></nav><div id="bt-noi"></div></main><div id="bt-cu" hidden><button id="tai-lai"></button><button id="bt-ve-moi"></button></div>', tl.body);
  var B = duLieu();
  (tuy.themKhoi || []).forEach(function (k) { B.khoi.unshift(k); B.dau[k.id] = dau(k); });
  var goi = [];
  var taiLai = 0;
  tl.getElementById('tai-lai').onclick = function () { taiLai++; };
  function tra(msg) { return Promise.resolve({ ok: true, status: 200, json: function () { return Promise.resolve({ message: msg }); } }); }
  function loi(chu) { return Promise.resolve({ ok: false, status: 417, json: function () { return Promise.resolve({ exc: 'x', _server_messages: JSON.stringify([JSON.stringify({ message: chu })]) }); } }); }
  function fetchGia(url, cau) {
    var ham = String(url).split('.').pop();
    /* v630: ảnh gửi bằng FormData (tai_anh), các hàm lưu gửi JSON. */
    var a = cau && cau.body ? (typeof cau.body === 'string' ? JSON.parse(cau.body) : cau.body) : null;
    goi.push({ ham: ham, a: a });
    if (tuy.loi && tuy.loi[ham]) return loi(tuy.loi[ham]);
    if (ham === 'bang_moi') return tra(JSON.parse(JSON.stringify(B)));
    if (ham === 'luu_muc') {
      var i = B.khoi.findIndex(function (k) { return k.id === a.muc.id; });
      if (i >= 0) B.khoi[i] = a.muc; else B.khoi.unshift(a.muc);
      B.dau[a.muc.id] = dau(a.muc);
      return tra(JSON.parse(JSON.stringify(B)));
    }
    if (ham === 'tai_anh') return tra({ url: '/files/web-moi.png' });
    if (ham === 'doi_anh_tuyen_dung') {
      B.tuyen_dung_erp.forEach(function (v) { if (v.ma_vi_tri === a.ma_vi_tri) { v.anh_web = a.anh; v.anh_the = a.anh || '/assets/vagabond/images/quay-sales.jpg'; } });
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
    RegExp: RegExp, Date: Date, Intl: Intl, Set: Set, parseInt: parseInt, encodeURIComponent: encodeURIComponent, document: docu, fetch: fetchGia,
    FormData: function () { this.tep = []; this.append = function (k, v) { this.tep.push([k, v && v.name]); }; } };
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

  await ca('Sau the va Nang cao, the Uu dai chi doc tu ERP: dem, trang thai, chi dung tai cua hang, khong co nut them sua xoa', async function () {
    var app = appMoi(); await nghi();
    /* v625: thêm thẻ Câu hỏi ứng tuyển ngay sau Tuyển dụng. */
    /* v630: thêm thẻ Thiết kế riêng ngay sau Tiệc. */
    /* v644: thêm thẻ Bánh ngay sau Ưu đãi (ảnh, mô tả, tầng hương vị từng bánh). */
    /* v647: thêm thẻ Banner ngay sau Ưu đãi. */
    bang('11 o the', app.tim('[data-the]').map(function (b) { return b.dataset.the; }), ['uu_dai', 'banner', 'banh', 'tiec', 'thiet_ke_rieng', 'tuyen_dung', 'cau_hoi', 'cua_hang', 'chu', 'lien_he', 'nang_cao']);
    dung('dem uu dai tu ERP', String(app.mot('[data-the="uu_dai"]').textContent).indexOf('Ưu đãi2') === 0);
    bang('khong hien uu dai go tay', app.tim('[data-muc]').length, 0);
    var u1 = String(app.mot('[data-muc-erp="SN10"]').textContent);
    dung('khach dang thay', u1.indexOf('Khách đang thấy') >= 0);
    dung('dong tom tat', u1.indexOf('Mã SN10 · Đơn từ 500.000 đ · 7g00 - 21g00 · 25/09/2026 - 20/10/2026') >= 0);
    var u2 = String(app.mot('[data-muc-erp="TANG"]').textContent);
    dung('tat tren ERP va chi tai cua hang', u2.indexOf('Đang tắt trên ERP') >= 0 && u2.indexOf('Chỉ dùng tại cửa hàng') >= 0);
    bang('khong co nut them, sua, xoa, cong tac', [app.tim('[data-them="uu_dai"]').length, app.tim('[data-sua]').length, app.tim('[data-xoa]').length, app.tim('[data-cong-tac]').length], [0, 0, 0, 0]);
    bang('co duong sang ERP', app.tim('[href="/khuyen-mai"]').length, 1);
  });

  /* v622 (anh Việt 30/10/2026): tuyển dụng lấy từ app như ưu đãi. Ba ca cũ của
     form tuyển dụng (thêm vị trí, giữ hình thức gõ tay, bật tắt) bỏ vì form
     không còn mở được; ca cơ chế lưu (công tắc, xoá, rời form, lỗi máy chủ)
     chuyển sang mục tiệc, loại duy nhất còn gõ tay, cơ chế lưu y hệt. */
  await ca('The Tuyen dung chi doc tu app ERP: dem, trang thai, khong co nut them sua xoa, co duong sang app', async function () {
    var app = appMoi(); await nghi();
    dung('dem vi tri tu app', String(app.mot('[data-the="tuyen_dung"]').textContent).indexOf('Tuyển dụng2') === 0);
    await app.the('tuyen_dung');
    bang('khong hien vi tri go tay', app.tim('[data-muc]').length, 0);
    var v1 = String(app.mot('[data-muc-erp="VTT-0001"]').textContent);
    dung('khach dang thay', v1.indexOf('Khách đang thấy') >= 0 && v1.indexOf('The Vagabond District 1') >= 0);
    dung('dang tat tren app', String(app.mot('[data-muc-erp="VTT-0002"]').textContent).indexOf('Đang tắt trên app') >= 0);
    bang('khong co nut them, sua, xoa, cong tac', [app.tim('[data-them="tuyen_dung"]').length, app.tim('[data-sua]').length, app.tim('[data-xoa]').length, app.tim('[data-cong-tac]').length], [0, 0, 0, 0]);
    bang('co duong sang app', app.tim('[href="/tuyen-dung"]').length, 1);
  });

  await ca('Cong tac Hien tren web luu ngay voi dau cu cua muc', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    var d0 = app.B().dau['tiec-1'];
    var i = app.mot('[data-cong-tac="tiec-1"]').querySelector('input');
    i.checked = false; i.onchange(); await nghi();
    var a = app.cuoi('luu_muc');
    bang('tat hien', [a.muc.id, a.muc.hien, a.dau_cu], ['tiec-1', false, d0]);
    dung('ve lai thanh dang an', String(app.mot('[data-muc="tiec-1"]').textContent).indexOf('Đang ẩn') >= 0);
  });

  await ca('Xoa: hoi lai, bam Thoi khong xoa, bam Xoa moi goi may chu', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    await app.bam(app.mot('[data-xoa="tiec-1"]'));
    await app.bam(app.mot('[data-hop-thoi]'));
    bang('khong xoa', app.dem('xoa_muc_web'), 0);
    await app.bam(app.mot('[data-xoa="tiec-1"]'));
    await app.bam(app.mot('[data-hop-co]'));
    bang('xoa dung muc', [app.dem('xoa_muc_web'), app.cuoi('xoa_muc_web').id_muc], [1, 'tiec-1']);
    bang('khong con tiec nao', app.tim('[data-muc]').length, 0);
  });

  await ca('Thieu mot o gio thi chan ngay o may khach, khong goi may chu', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    await app.bam(app.mot('[data-them="tiec"]'));
    await app.go(app.oTen('tieu_de'), 'Trà chiều');
    await app.go(app.oTen('bat_dau'), '2026-10-30');
    await app.go(app.oTen('gio_bat_dau'), '07:00');
    await app.luu();
    bang('khong goi', app.dem('luu_muc'), 0);
    dung('bao ro', app.bao().indexOf('cả hai ô giờ') >= 0);
  });

  await ca('Dang sua chua luu ma doi the: hoi lai, Thoi thi o lai form', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    await app.bam(app.mot('[data-sua="tiec-1"]'));
    await app.go(app.oTen('tieu_de'), 'Đổi tên');
    await app.the('cua_hang');
    dung('co hop hoi', app.tim('[data-hop-thoi]').length === 1);
    await app.bam(app.mot('[data-hop-thoi]'));
    dung('van o form', app.tim('.bt-form').length === 1 && app.oTen('tieu_de').value === 'Đổi tên');
    await app.the('cua_hang');
    await app.bam(app.mot('[data-hop-co]'));
    dung('sang the Cua hang', app.tim('[data-sua="cua-hang-sai-gon"]').length === 1);
  });

  await ca('Tiec: dong tom tat co ngay, gio, gia, so ve da dang ky', async function () {
    var app = appMoi(); await nghi();
    await app.the('tiec');
    var t = String(app.mot('[data-muc="tiec-1"]').textContent);
    dung('tom tat', t.indexOf('Chủ nhật, 18/10/2026 · 15g00 - 17g00 · Cửa hàng Sài Gòn · 350.000 đ/vé · Đã đăng ký 12/40 vé') >= 0);
  });

  await ca('Loi may chu hien nguyen cau, form giu nguyen chu dang go', async function () {
    var app = appMoi({ loi: { luu_muc: 'Có người vừa sửa hoặc xoá mục này. Tải lại để xem bản mới rồi sửa tiếp.' } }); await nghi();
    await app.the('tiec');
    await app.bam(app.mot('[data-sua="tiec-1"]'));
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
  function nangCao(soKhoi, toiDa, themKhoi) {
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
    (themKhoi || []).forEach(function (k) { khoi.push(k); });
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
    return { tl: tl, g: g,
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


  /* v630 (Minh Vũ 02/11/2026): thẻ Tuyển dụng không còn chỉ xem, đổi được ảnh
     từng vị trí. Bấm đúng chuỗi của Minh Vũ: Đổi ảnh, chọn tệp, máy tải rồi ghi. */
  await ca('v630 the Tuyen dung: moi vi tri co anh khach dang thay, ghi chu nguon anh, nut Doi anh; Dung anh tu chon chi hien khi da tai rieng', async function () {
    var app = appMoi(); await nghi();
    await app.the('tuyen_dung');
    var v1 = app.mot('[data-muc-erp="VTT-0001"]'), v2 = app.mot('[data-muc-erp="VTT-0002"]');
    bang('anh dang dung', [v1.querySelector('img').src, v2.querySelector('img').src], ['/assets/vagabond/images/quay-sales.jpg', '/files/web-pastry.jpg']);
    bang('ghi chu nguon anh', [String(app.mot('[data-nguon-anh="VTT-0001"]').textContent), String(app.mot('[data-nguon-anh="VTT-0002"]').textContent)],
      ['Ảnh tự chọn theo bộ phận', 'Ảnh tải riêng cho vị trí này']);
    bang('nut Doi anh moi vi tri', app.tim('[data-doi-anh]').length, 2);
    bang('Dung anh tu chon chi o vi tri da tai rieng', app.tim('[data-anh-tu-chon]').map(function (b) { return b.dataset.anhTuChon; }), ['VTT-0002']);
    bang('van khong co them, sua noi dung, xoa', [app.tim('[data-them="tuyen_dung"]').length, app.tim('[data-sua]').length, app.tim('[data-xoa]').length], [0, 0, 0]);
  });

  await ca('v630 Doi anh: bam nut mo chon tep, chon xong tai anh roi ghi vao dung vi tri, the ve lai anh moi', async function () {
    var app = appMoi(); await nghi();
    await app.the('tuyen_dung');
    var tep = app.mot('[data-tep-anh="VTT-0001"]'), mo = 0;
    tep.click = function () { mo++; };
    await app.bam(app.mot('[data-doi-anh="VTT-0001"]'));
    bang('mo hop chon tep', mo, 1);
    tep.files = [{ name: 'quay-moi.png', size: 300000 }];
    await tep.onchange(); await nghi();
    bang('tai roi ghi, dung thu tu', app.goi.map(function (x) { return x.ham; }).slice(-2), ['tai_anh', 'doi_anh_tuyen_dung']);
    bang('ghi dung vi tri va anh vua tai', app.cuoi('doi_anh_tuyen_dung'), { ma_vi_tri: 'VTT-0001', anh: '/files/web-moi.png' });
    bang('the ve lai anh moi', app.mot('[data-muc-erp="VTT-0001"]').querySelector('img').src, '/files/web-moi.png');
    bang('ghi chu doi theo', String(app.mot('[data-nguon-anh="VTT-0001"]').textContent), 'Ảnh tải riêng cho vị trí này');
    dung('bao da doi: ' + app.bao(), app.bao().indexOf('Đã đổi ảnh của Thu ngân ca tối') === 0);
  });

  await ca('v630 Doi anh: tai anh hong thi khong ghi vi tri, bao loi may chu; anh qua 10 MB chan ngay tai may', async function () {
    var app = appMoi({ loi: { tai_anh: 'Không đọc được ảnh. Chọn ảnh PNG, JPG hoặc WebP dưới 25 triệu điểm ảnh.' } }); await nghi();
    await app.the('tuyen_dung');
    var tep = app.mot('[data-tep-anh="VTT-0001"]');
    tep.files = [{ name: 'x.png', size: 1000 }];
    await tep.onchange(); await nghi();
    bang('khong ghi vi tri', app.dem('doi_anh_tuyen_dung'), 0);
    dung('cau loi may chu: ' + app.bao(), app.bao().indexOf('Không đọc được ảnh') === 0);
    var truoc = app.dem('tai_anh');
    tep = app.mot('[data-tep-anh="VTT-0001"]');
    tep.files = [{ name: 'to.png', size: 11 * 1024 * 1024 }];
    await tep.onchange(); await nghi();
    bang('qua 10 MB khong gui', [app.dem('tai_anh') - truoc, app.dem('doi_anh_tuyen_dung')], [0, 0]);
    dung('bao chon anh nho hon', app.bao().indexOf('Chọn ảnh dưới 10 MB') === 0);
  });

  await ca('v630 Dung anh tu chon: ghi anh trong, the ve ve anh theo bo phan; may chu tu choi thi giu nguyen va bao', async function () {
    var app = appMoi(); await nghi();
    await app.the('tuyen_dung');
    await app.bam(app.mot('[data-anh-tu-chon="VTT-0002"]'));
    bang('ghi anh trong', app.cuoi('doi_anh_tuyen_dung'), { ma_vi_tri: 'VTT-0002', anh: '' });
    bang('het nut Dung anh tu chon', app.tim('[data-anh-tu-chon]').length, 0);
    bang('ghi chu ve tu chon', String(app.mot('[data-nguon-anh="VTT-0002"]').textContent), 'Ảnh tự chọn theo bộ phận');
    var app2 = appMoi({ loi: { doi_anh_tuyen_dung: 'Bạn cần quyền Marketing để chỉnh nội dung website.' } }); await nghi();
    await app2.the('tuyen_dung');
    await app2.bam(app2.mot('[data-anh-tu-chon="VTT-0002"]'));
    dung('bao loi quyen', app2.bao().indexOf('quyền Marketing') >= 0);
    bang('giu anh cu', app2.mot('[data-muc-erp="VTT-0002"]').querySelector('img').src, '/files/web-pastry.jpg');
  });

  await ca('v630 Nang cao: khoi Tuyen dung, Uu dai go tay chi con cau chi duong, khong o sua; khong them moi duoc; nut mo dung the', async function () {
    var n = nangCao(1, 80, [
      { id: 'td-cu', loai: 'tuyen_dung', vi_tri: 'tuyen_dung', hien: true, tieu_de: 'Thợ bánh cũ', noi_dung: '', nhan: '', anh: '/files/cu.jpg', mo_ta_anh: '', nut: '', lien_ket: '' },
      { id: 'ud-cu', loai: 'uu_dai', vi_tri: 'uu_dai', hien: true, tieu_de: 'Giảm cũ', noi_dung: '', nhan: '', anh: '', mo_ta_anh: '', nut: '', lien_ket: '' }]);
    await nghi();
    var moThe = [];
    n.g.VgbBienTapMoi = { moThe: function (k) { moThe.push(k); } };
    var chonKhoi = function (ten) { return n.tl.getElementById('danh-sach').querySelectorAll('.chon-khoi').filter(function (b) { return String(b.textContent).indexOf(ten) >= 0; })[0]; };
    chonKhoi('Thợ bánh cũ').onclick(); await nghi();
    var tt = n.tl.getElementById('thuoc-tinh');
    dung('cau chi duong tuyen dung', String(tt.textContent).indexOf('không còn ra trang khách') >= 0 && String(tt.textContent).indexOf('thẻ Tuyển dụng') >= 0);
    bang('khong con o sua nao', [tt.querySelectorAll('input').length, tt.querySelectorAll('textarea').length], [0, 0]);
    tt.querySelectorAll('[data-ve-the]')[0].onclick();
    bang('mo dung the Tuyen dung', moThe, ['tuyen_dung']);
    chonKhoi('Giảm cũ').onclick(); await nghi();
    tt = n.tl.getElementById('thuoc-tinh');
    dung('cau chi duong uu dai', String(tt.textContent).indexOf('Chương trình khuyến mãi') >= 0);
    bang('khong o sua uu dai', tt.querySelectorAll('input').length, 0);
    var them = [].slice.call(n.tl.getElementById('them-khoi').children).map(function (b) { return String(b.textContent); });
    bang('khong con nut them Uu dai, Tuyen dung', them.filter(function (t) { return t === '+ Ưu đãi' || t === '+ Tuyển dụng'; }), []);
    dung('van them duoc Thong bao', them.indexOf('+ Thông báo') >= 0);
  });

  /* v630: thẻ Thiết kế riêng (anh Việt chốt 02/11/2026). Marketing thêm tác phẩm,
     size và giá gồm VAT, trang trí theo nhóm, số ngày đặt trước. */
  await ca('v630 Them tac pham thiet ke rieng: size, trang tri, so ngay; luu gui dung cau truc cho may chu', async function () {
    var app = appMoi(); await nghi();
    await app.the('thiet_ke_rieng');
    bang('chua co tac pham', app.tim('[data-muc]').length, 0);
    await app.bam(app.mot('[data-them="thiet_ke_rieng"]'));
    await app.go(app.oTen('tieu_de'), 'Croquembouche');
    await app.go(app.oTen('kich_co_gia_0'), '5.940.000');
    await app.bam(app.mot('[data-them-dong="kich_co"]'));
    await app.go(app.oTen('kich_co_ten_1'), 'M');
    await app.go(app.oTen('kich_co_gia_1'), '7560000');
    await app.bam(app.mot('[data-them-dong="trang_tri"]'));
    await app.go(app.oTen('trang_tri_ten_0'), 'Hoa lan trắng');
    await app.go(app.oTen('trang_tri_nhom_0'), 'Hoa');
    await app.luu();
    var a = app.cuoi('luu_muc').muc;
    bang('cau truc gui', [a.loai, a.tieu_de, a.so_ngay, a.kich_co, a.trang_tri],
      ['thiet_ke_rieng', 'Croquembouche', '7', [{ ten: 'S', mo_ta: '', gia: '5940000' }, { ten: 'M', mo_ta: '', gia: '7560000' }], [{ ten: 'Hoa lan trắng', gia_them: '0', nhom: 'Hoa' }]]);
    dung('dong danh sach co gia', String(app.mot('[data-muc="' + a.id + '"]').textContent).indexOf('S 5.940.000 đ, M 7.560.000 đ') >= 0);
    dung('nhan Dang nhan dat', String(app.mot('[data-muc="' + a.id + '"]').textContent).indexOf('Đang nhận đặt') >= 0);
  });

  await ca('v630 Tac pham thieu gia, trung size, so ngay duoi 7: bao ngay, khong goi may chu; bo dong size', async function () {
    var app = appMoi(); await nghi();
    await app.the('thiet_ke_rieng');
    await app.bam(app.mot('[data-them="thiet_ke_rieng"]'));
    await app.go(app.oTen('tieu_de'), 'Tháp');
    await app.luu();
    dung('bao thieu gia', app.bao().indexOf('giá gồm VAT') >= 0);
    await app.go(app.oTen('kich_co_gia_0'), '100000');
    await app.bam(app.mot('[data-them-dong="kich_co"]'));
    await app.go(app.oTen('kich_co_ten_1'), 's');
    await app.go(app.oTen('kich_co_gia_1'), '200000');
    await app.luu();
    dung('bao trung size', app.bao().indexOf('trùng') >= 0);
    await app.bam(app.mot('[data-bo-dong="kich_co-1"]'));
    bang('con mot dong size', app.tim('[data-dong-o]').filter(function (x) { return x.dataset.dongO.indexOf('kich_co') === 0; }).length, 1);
    await app.go(app.oTen('so_ngay'), '5');
    await app.luu();
    dung('bao so ngay', app.bao().indexOf('tối thiểu là 7') >= 0);
    bang('khong goi luu', app.dem('luu_muc'), 0);
  });

  /* v647 (anh Viet 10/11/2026): the Banner. Minh Vu tu thay anh banner o ba cho
     da chot (Dau trang, Gio hang, Dat xong), mac dinh bam mo trang thanh vien. */
  await ca('v647 Banner: them banner, chon cho Dat xong, tai anh may tinh va dien thoai, luu dung vi tri va link', async function () {
    var app = appMoi(); await nghi();
    await app.the('banner');
    bang('the Banner chua co banner nao', app.tim('[data-muc]').length, 0);
    await app.bam(app.mot('[data-them="banner"]'));
    await app.go(app.oTen('tieu_de'), 'Sinh nhật nhận quà');
    bang('link mac dinh trang thanh vien', app.oTen('lien_ket').value, '/thanh-vien');
    await app.bam(app.mot('[data-chip="Đặt xong"]'));
    dung('mo ta cho dat doi theo: ' + app.mot('[data-mo-cho]').textContent, String(app.mot('[data-mo-cho]').textContent).indexOf('gửi đơn thành công') >= 0);
    var tep = app.mot('[data-tep-anh="anh"]');
    tep.files = [{ name: 'banner-pc.png', size: 400000 }];
    await tep.onchange(); await nghi();
    var tepDt = app.mot('[data-tep-anh="anh_dt"]');
    tepDt.files = [{ name: 'banner-dt.png', size: 300000 }];
    await tepDt.onchange(); await nghi();
    bang('xem truoc hai khung', app.tim('.bt-xem-banner-o').map(function (f) { return f.querySelectorAll('img').length; }), [1, 1]);
    await app.go(app.oTen('mo_ta_anh'), 'Cập nhật ngày sinh để nhận quà bánh');
    await app.luu();
    var m = app.cuoi('luu_muc').muc;
    bang('luu dung banner', [m.loai, m.vi_tri, m.lien_ket, m.anh, m.anh_dt, m.hien, m.mo_ta_anh],
      ['banner', 'dat_xong', '/thanh-vien', '/files/web-moi.png', '/files/web-moi.png', true, 'Cập nhật ngày sinh để nhận quà bánh']);
    dung('bao khach thay ngay: ' + app.bao(), app.bao().indexOf('Khách thấy ngay') >= 0);
    var dong = app.mot('[data-muc="' + m.id + '"]');
    dung('dong co ten cho dat va link: ' + dong.textContent, String(dong.textContent).indexOf('Đặt xong') >= 0 && String(dong.textContent).indexOf('/thanh-vien') >= 0);
    dung('dong co nhan Dang hien', String(dong.textContent).indexOf('Đang hiện') >= 0);
  });

  await ca('v647 Banner: bat hien ma chua co anh thi chan tai may, khong goi luu; bo chon cho cung chan', async function () {
    var app = appMoi(); await nghi();
    await app.the('banner');
    await app.bam(app.mot('[data-them="banner"]'));
    await app.go(app.oTen('tieu_de'), 'Banner thử');
    await app.luu();
    dung('bao can anh: ' + app.bao(), app.bao().indexOf('Tải ảnh máy tính') === 0);
    await app.bam(app.mot('[data-chip="Giỏ hàng"]'));
    await app.luu();
    dung('bo chon cho thi bao chon cho: ' + app.bao(), app.bao().indexOf('Chọn chỗ đặt banner') === 0);
    bang('khong goi luu', app.dem('luu_muc'), 0);
  });

  await ca('v647 Banner: banner chua toi ngay hien thi nhan va cong tac noi ro khach chua thay', async function () {
    var app = appMoi({ themKhoi: [{ id: 'banner-sn', loai: 'banner', vi_tri: 'gio_hang', hien: true, tieu_de: 'Sinh nhật', anh: '/files/b.png', anh_dt: '',
      mo_ta_anh: '', lien_ket: '/thanh-vien', bat_dau: '2099-01-01', ket_thuc: '' }] }); await nghi();
    await app.the('banner');
    var dong = app.mot('[data-muc="banner-sn"]');
    dung('nhan Chua toi ngay hien: ' + dong.textContent, String(dong.textContent).indexOf('Chưa tới ngày hiện') >= 0);
    dung('cong tac noi ro: ' + dong.textContent, String(dong.textContent).indexOf('Chưa tới ngày, khách chưa thấy') >= 0);
    dung('mo ta co Gio hang va dung chung anh: ' + dong.textContent, String(dong.textContent).indexOf('Giỏ hàng') >= 0 && String(dong.textContent).indexOf('dùng chung ảnh máy tính') >= 0);
  });

  console.log('Bo ca kiem HANH VI v586: trinh bien tap theo the va the Tiec');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  xongHet = true;
  process.exit(ket.hong ? 1 : 0);
})();
