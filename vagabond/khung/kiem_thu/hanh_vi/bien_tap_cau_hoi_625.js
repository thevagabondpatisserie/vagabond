/* Ca kiểm HÀNH VI v625: thẻ "Câu hỏi ứng tuyển" của trình biên tập web
 * (anh Việt 31/10/2026: Minh Vũ thêm bớt câu hỏi của form /ung-tuyen).
 *
 * Nạp THẬT bien-tap-moi.js vào DOM giả, máy chủ giả trả bang_moi với cấu hình
 * lấy từ ĐÚNG noi_dung_web._mau_form() (chạy python3). Khung chép từ
 * bien_tap_586.js. Phép chuẩn hoá phía máy chủ kiểm ở thu_tuyen_dung_625.py.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/bien_tap_cau_hoi_625.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var WEB = path.join(GOC, 'vagabond', 'public', 'web_order');
function doc(t) { return fs.readFileSync(path.join(WEB, t), 'utf8'); }
var cp = require('child_process');
var MAU_FORM = JSON.parse(cp.execFileSync('python3', ['-B', '-c',
  'import json,sys; sys.path.insert(0, sys.argv[1]); from vagabond.khung.kiem_thu import nen; nen.gia_lap(); from vagabond import noi_dung_web as nw; ' +
  'print(json.dumps(nw._mau_form(), ensure_ascii=False))', GOC]).toString());
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
      { id: 'erp-td-VTT-0001', ma_vi_tri: 'VTT-0001', loai: 'tuyen_dung', tieu_de: 'Thu ngân ca tối', noi_lam: 'The Vagabond District 1', hinh_thuc: 'Bán thời gian', ket_thuc: '', khach_thay: 1, trang_thai_erp: 'Khách đang thấy' },
      { id: 'erp-td-VTT-0002', ma_vi_tri: 'VTT-0002', loai: 'tuyen_dung', tieu_de: 'Phụ bếp Pastry', noi_lam: '', hinh_thuc: 'Toàn thời gian', ket_thuc: '2026-10-31', khach_thay: 0, trang_thai_erp: 'Đang tắt trên app, khách không thấy' },
    ],
  };
  B.tuyen_dung_form = JSON.parse(JSON.stringify(MAU_FORM.mac_dinh));
  B.dau_tuyen_dung_form = 'dtf-1';
  B.tuyen_dung_mau = JSON.parse(JSON.stringify(MAU_FORM));
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
    if (ham === 'luu_form_tuyen_dung') { B.tuyen_dung_form = a.gia_tri; B.dau_tuyen_dung_form = 'dtf-2'; return tra(JSON.parse(JSON.stringify(B))); }
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


function maCau(app) { return app.tim('[data-cau]').map(function (x) { return x.dataset.cau; }); }
function nutChu(el, chu) { return el.querySelectorAll('button').filter(function (b) { return String(b.textContent) === chu; })[0]; }
(async function () {
  await ca('Thẻ Câu hỏi ứng tuyển: 14 câu Lark theo 3 bước; câu gốc có ổ khoá, không có nút Xoá', async function () {
    var app = appMoi(); await nghi();
    dung('đếm 14', String(app.mot('[data-the="cau_hoi"]').textContent).indexOf('Câu hỏi ứng tuyển14') === 0);
    await app.the('cau_hoi');
    bang('thứ tự', maCau(app), MAU_FORM.mac_dinh.cau_hoi.map(function (c) { return c.ma; }));
    ['ho_ten', 'sdt', 'vi_tri'].forEach(function (m) {
      var d = app.mot('[data-cau="' + m + '"]');
      dung(m + ' có ổ khoá', String(d.textContent).indexOf('Câu gốc') >= 0);
      bang(m + ' không xoá', d.querySelectorAll('[data-xoa-cau]').length, 0);
    });
    bang('câu thường có Xoá', app.mot('[data-cau="tham_nien"]').querySelectorAll('[data-xoa-cau]').length, 1);
    dung('nhãn loại tiếng Việt, không mã', String(app.mot('[data-cau="luong"]').textContent).indexOf('Số tiền') >= 0 && String(app.mot('[data-cau="luong"]').textContent).indexOf('so_tien') < 0);
    dung('có link xem trang thật', app.tim('[href="/ung-tuyen"]').length === 1);
  });

  await ca('Sửa câu thu nhập: đổi chữ gợi ý, tắt Cho AI dùng, Lưu và đăng gửi đúng cấu hình và dấu cũ', async function () {
    var app = appMoi(); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-sua-cau="luong"]'));
    var f = app.mot('[data-form-cau="luong"]');
    dung('câu hệ thống: nói rõ loại giữ nguyên', String(f.textContent).indexOf('Loại câu trả lời: Số tiền') >= 0);
    dung('gợi ý nói máy tự thêm lương vị trí', String(f.textContent).indexOf('Vị trí này từ') >= 0);
    await app.go(f.querySelectorAll('[name="goi_y"]')[0], 'Ghi tổng thu nhập mỗi tháng.');
    var ai = f.querySelectorAll('input').filter(function (i) { return i.getAttribute('role') === 'switch'; });
    var tat = ai[ai.length - 1]; tat.checked = false; tat.onchange(); await nghi();
    await app.bam(app.mot('[data-luu-form]'));
    var a = app.cuoi('luu_form_tuyen_dung');
    var c = a.gia_tri.cau_hoi.filter(function (x) { return x.ma === 'luong'; })[0];
    bang('gửi đúng', [c.goi_y, c.ai, a.dau_cu, a.gia_tri.cau_hoi.length], ['Ghi tổng thu nhập mỗi tháng.', false, 'dtf-1', 14]);
    dung('báo khách thấy ngay', app.bao().indexOf('Ứng viên thấy ngay') >= 0);
  });

  await ca('Giới tính, sinh nhật: không có công tắc Cho AI dùng, ghi rõ AI không bao giờ dùng', async function () {
    var app = appMoi(); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-sua-cau="gioi_tinh"]'));
    var f = app.mot('[data-form-cau="gioi_tinh"]');
    dung('câu ghi rõ', String(f.textContent).indexOf('AI không bao giờ dùng câu này') >= 0);
    dung('không công tắc AI', String(f.textContent).indexOf('Cho AI dùng câu này') < 0);
  });

  await ca('Thêm câu chọn một: thiếu lựa chọn thì chặn ở máy, đủ thì gửi; chỉ hỏi ở một vị trí', async function () {
    var app = appMoi(); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-them-cau]'));
    var moi = maCau(app).filter(function (m) { return /^c_/.test(m); });
    bang('một câu mới ở bước 3', moi.length, 1);
    var f = app.mot('[data-form-cau="' + moi[0] + '"]');
    await app.go(f.querySelectorAll('[name="hoi"]')[0], 'Bạn có làm được ca sáng sớm 5 giờ không?');
    await app.bam(nutChu(f, 'Chọn một'));
    f = app.mot('[data-form-cau="' + moi[0] + '"]');
    await app.go(f.querySelectorAll('[name="lua_chon"]')[0], 'Được');
    await app.bam(app.mot('[data-luu-form]'));
    bang('chưa gửi', app.dem('luu_form_tuyen_dung'), 0);
    dung('nhắc 2 lựa chọn', app.bao().indexOf('cần ít nhất 2 lựa chọn') >= 0);
    await app.go(f.querySelectorAll('[name="lua_chon"]')[0], 'Được\nKhông được');
    await app.bam(nutChu(f, 'Phụ bếp Pastry'));
    await app.bam(app.mot('[data-luu-form]'));
    var c = app.cuoi('luu_form_tuyen_dung').gia_tri.cau_hoi.filter(function (x) { return x.ma === moi[0]; })[0];
    bang('câu mới', [c.loai, c.lua_chon, c.vi_tri, c.buoc], ['chon_mot', ['Được', 'Không được'], ['VTT-0002'], 3]);
    dung('mã câu đúng mẫu máy chủ', /^c_[a-z0-9]{4,12}$/.test(c.ma));
  });

  await ca('Lên, xuống: đổi chỗ trong bước; câu đầu bước 2 bấm lên là sang cuối bước 1', async function () {
    var app = appMoi(); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-xuong-cau="tham_nien"]'));
    var ds = maCau(app);
    dung('đổi chỗ trong bước 2', ds.indexOf('thoi_gian') < ds.indexOf('tham_nien'));
    await app.bam(app.mot('[data-len-cau="vi_tri"]'));
    await app.bam(app.mot('[data-luu-form]'));
    var g = app.cuoi('luu_form_tuyen_dung').gia_tri.cau_hoi;
    var vt = g.filter(function (x) { return x.ma === 'vi_tri'; })[0];
    bang('vị trí sang bước 1, đứng cuối bước 1', [vt.buoc, g.filter(function (x) { return x.buoc === 1; }).map(function (x) { return x.ma; }).pop()], [1, 'vi_tri']);
    bang('câu đầu tiên không lên được', app.mot('[data-len-cau="ho_ten"]').disabled, true);
  });

  await ca('Xoá câu hỏi qua hộp hỏi; rời thẻ khi chưa lưu thì hỏi; Hoàn tác về bản ứng viên đang thấy', async function () {
    var app = appMoi(); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-xoa-cau="nhan_them"]'));
    await app.bam(app.mot('[data-hop-co]'));
    dung('đã bỏ khỏi danh sách', maCau(app).indexOf('nhan_them') < 0);
    await app.bam(app.mot('[data-the="tiec"]'));
    dung('hỏi bỏ thay đổi', app.tim('[data-hop-thoi]').length === 1);
    await app.bam(app.mot('[data-hop-thoi]'));
    await app.bam(app.mot('[data-hoan-tac]'));
    await app.bam(app.mot('[data-hop-co]'));
    dung('hoàn tác', maCau(app).indexOf('nhan_them') >= 0);
    bang('không gửi gì', app.dem('luu_form_tuyen_dung'), 0);
  });

  await ca('Máy chủ báo người khác vừa sửa: hiện nguyên câu, chữ đang sửa còn trên màn', async function () {
    var app = appMoi({ loi: { luu_form_tuyen_dung: 'Có người vừa sửa câu hỏi ứng tuyển. Tải lại để xem bản mới rồi sửa tiếp.' } }); await nghi();
    await app.the('cau_hoi');
    await app.bam(app.mot('[data-xoa-cau="nhan_them"]'));
    await app.bam(app.mot('[data-hop-co]'));
    await app.bam(app.mot('[data-luu-form]'));
    dung('câu máy chủ', app.bao().indexOf('Có người vừa sửa') === 0);
    dung('thay đổi còn', maCau(app).indexOf('nhan_them') < 0);
  });

  xongHet = true;
  console.log('Bo ca kiem HANH VI v625: the Cau hoi ung tuyen');
  ket.loi.forEach(function (l) { console.log('  HONG  ' + l); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
