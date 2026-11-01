/* Ca kiểm HÀNH VI v626: phân hệ Tài chính.
 *
 * Anh Việt 31/10/2026: tổng tiền mặt, tổng ngân hàng (số dư chốt anh đưa,
 * app tự tính), lãi lỗ, hao hụt, công nợ, chờ chi. Chỉ Giám đốc và người Giám
 * đốc chọn được xem.
 *
 * Nạp THẬT 61-tai-chinh.js cùng các hàm nền nó dùng vào DOM giả. Máy chủ giả
 * chỉ trả dữ liệu màn và ghi lại lời gọi; phép tính chạy thật ở
 * thu_tai_chinh_626.py. Mỗi ca bấm đúng chuỗi thao tác của người dùng.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/tai_chinh_626.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), KHO = doc('03-kho-chung-tu.js');
var MAN = doc('61-tai-chinh.js');

function layHam(src, ten) {
  var dau = src.search(new RegExp('(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}
var HAM = ['h', 'money', 'today'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(KHO, 'errMsg')]).join('\n');

var HOM = new Date();
var THANG_NAY = HOM.getFullYear() + '-' + ('0' + (HOM.getMonth() + 1)).slice(-2);

function tongQuan(loiLaiLo) {
  return {
    thang: THANG_NAY, la_giam_doc: 1,
    tien: { ok: 1, v: { tong: 1842350000, ngan_hang: 1710000000, tien_mat: 132350000, tam_ung: 81850000, chua_chot: 2 } },
    dong7: { ok: 1, v: { vao: 318000000, ra: 276000000, rong: 42000000 } },
    lai_lo: loiLaiLo ? { ok: 0, loi: 'x' } : { ok: 1, v: { lai_rong: 120000000, ti_le_lai_rong: 6.1, food_cost: 22.5, doanh_thu_thuan: 1953867209 } },
    phai_thu: { ok: 1, v: 126000000 },
    phai_tra: { ok: 1, v: { tong: 212000000, qua_han: 18000000 } },
    cho_chi: { ok: 1, v: { so: 15, tien: 108715080, so_cho_duyet: 2, tien_cho_duyet: 3000000 } },
    tra_truoc: { ok: 1, v: { tong: 47000000, so_khach: 6 } },
  };
}
function tien() {
  return {
    luc: '2026-10-31 08:15', sepay_doc_duoc: 1,
    tong: { tong: 1429490597, ngan_hang: 1422990597, tien_mat: 6500000, tam_ung: 0, chua_chot: 4 },
    dong: [
      { nguon: 'nh:31561568', loai: 'Ngân hàng', ten: 'MB Bank ···1568', tam_ung: 0, dong_bo: 1, so_bao: 1179800000,
        moc: { ngay_chot: '2026-10-01', so_du: 1000000000 }, vao: 300000000, ra: 120000000, so_du: 1180000000,
        doi_chieu: { tt: 'lech', lech: 200000 }, ghi: [] },
      { nguon: 'nh:700037279585', loai: 'Ngân hàng', ten: 'Shinhan Bank ···9585', tam_ung: 0, dong_bo: 0, so_bao: 242995597,
        moc: null, vao: 0, ra: 0, so_du: 242990597, ghi: ['Số dư SePay báo'] },
      { nguon: 'nh:0901486556', loai: 'Ngân hàng', ten: 'OCB ···6556 (tạm ứng)', tam_ung: 1, dong_bo: 1, so_bao: 0,
        moc: null, so_du: null, ghi: ['Chưa chốt số dư đầu'] },
      { nguon: 'tm:TCV', loai: 'Tiền mặt', ten: 'Két District 1', diem: 'TCV', moc: { ngay_chot: '2026-10-30', so_du: 5000000 },
        vao: 4500000, ra: 3000000, so_du: 6500000, ca: { luc: '2026-10-31 22:23:58', dem: 4560000 }, ghi: [] },
      { nguon: 'tm:QUY', loai: 'Tiền mặt', ten: 'Quỹ tiền mặt công ty', moc: null, so_du: null, ghi: ['Chưa chốt số dư đầu'] },
    ],
  };
}
function caiDat(gd) {
  return {
    hom_nay: '2026-10-31', la_giam_doc: gd ? 1 : 0,
    nguon: [
      { nguon: 'nh:31561568', loai: 'Ngân hàng', ten: 'MB Bank ···1568', dong_bo: 1, so_bao: 0,
        lich_su: [{ ngay_chot: '2026-10-01', so_du: 1000000000, nguoi: 'viet@x', ghi_chu: '' }, { ngay_chot: '2026-09-01', so_du: 900000000, nguoi: 'viet@x', ghi_chu: 'cũ' }] },
      { nguon: 'nh:0901486556', loai: 'Ngân hàng', ten: 'OCB ···6556 (tạm ứng)', dong_bo: 1, so_bao: 0, lich_su: [] },
      { nguon: 'tm:QUY', loai: 'Tiền mặt', ten: 'Quỹ tiền mặt công ty', lich_su: [] },
    ],
    nguoi_dung: gd ? [{ email: 'dung@vagabond.vn', ten: 'Ngô Hoàng Ngọc Dung', chon: 0 }, { email: 'khai@vagabond.vn', ten: 'Lâm Quang Khải', chon: 0 }] : undefined,
  };
}

function dungMoi(vai, quyenNen, traLoi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], dieuHuong = [], vgbGoDs = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
    S: { roles: vai, stack: [], quyenNen: quyenNen || null },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html) {
      khung.innerHTML = html; khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { dieuHuong.push(fn.name || 'anDanh'); return fn(); },
    vgbGo: function (k) { vgbGoDs.push(k); },
    toast: function (m) { toastDs.push(m); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = (traLoi || {})[duong];
      if (f) return Promise.resolve(f(ts));
      return Promise.resolve({ ok: 1 });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '61-tai-chinh.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, dieuHuong: dieuHuong, vgbGo: vgbGoDs };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function bam(el) { if (el.onclick) return el.onclick({ target: el }); el.dispatchEvent(dg.suKien('click', {}, el)); }
function mot(m, chon) { return m.khung.querySelectorAll(chon)[0]; }
var GD = ['Giám đốc'];
var KT = ['Accounts Manager', 'Accounts User', 'AP Kiểm soát (FIN)'];
var TL = {
  'vagabond.tai_chinh.tong_quan': function () { return tongQuan(false); },
  'vagabond.tai_chinh.tien_hien_co': tien,
  'vagabond.tai_chinh.cai_dat': function () { return caiDat(true); },
  'vagabond.tai_chinh.dong_tien': function (ts) {
    var ngay = [];
    for (var i = 0; i < ts.so_ngay; i++) ngay.push({ ngay: '2026-10-' + ('0' + (i + 1)).slice(-2), vao: 1000000 * i, ra: 500000, rong: 0 });
    return { ngay: ngay, vao: 5, ra: 3, rong: 2, tu: '2026-10-01', den: '2026-10-31', so_ngay: ts.so_ngay,
      lon_nhat: { vao: [{ ngay: '2026-10-05', so: 50000000, tk: 'MB Bank ···1568', mo_ta: 'CONG TY ABC TRA NO' }], ra: [] },
      noi_bo: { so: 2, tien: 20000000 } };
  },
  'vagabond.tai_chinh.lai_lo_thang': function (ts) {
    var t = ts.thang || THANG_NAY;
    return { thang: t, thang_truoc: '2026-09', dang_chay: t === THANG_NAY ? 1 : 0,
      ky: { doanh_thu: 100, doanh_thu_thuan: 100, gia_von: 30, lai_gop: 70, lai_rong: 10, food_cost: 30, prime_cost: 55, ti_le_lai_gop: 70, ti_le_lai_rong: 10 },
      ky_truoc: { doanh_thu: 90, doanh_thu_thuan: 90, lai_rong: 5 } };
  },
  'vagabond.tai_chinh.ti_le_thang': function (ts) {
    return { thang: ts.thang || THANG_NAY, food_cost: 22.5, prime_cost: 32.7, gia_von: 439381018, nhan_vien: 200000000,
      hao_hut: { ti_le_huy: 0.1, ti_le_kiem_ke: 109.4, huy: 1109141, thieu: 303585914, da_dung: 277520231,
        dong: [{ kho: 'Baker - Nguyên liệu - TV', thieu: 301717253, thua: 0, da_dung: 185710171, huy: 0, ti_le_kiem_ke: 162.5, bat_thuong: 1 },
          { kho: 'Pastry - Nguyên liệu - TV', thieu: 1868661, thua: 0, da_dung: 93430060, huy: 0, ti_le_kiem_ke: 2, bat_thuong: 0 }] } };
  },
};

(async function () {
  console.log('v626 Tài chính: tổng quan, tiền hiện có, dòng tiền, lãi lỗ, tỉ lệ, cài đặt');

  await ca('kế toán viên không được chọn: khoá mọi màn, không hỏi máy chủ', async function () {
    var m = dungMoi(KT, { tai_chinh: false }, TL);
    for (var t of ['scrTcTongQuan', 'scrTcTien', 'scrTcDong', 'scrTcDuBao', 'scrTcLaiLo', 'scrTcTiLe', 'scrTcCaiDat']) {
      await m.g[t](); await tick();
      dung(t + ': câu khoá', chu(m.khung).indexOf('chỉ mở cho Giám đốc') >= 0);
    }
    bang('không gọi máy chủ', m.goi.length, 0);
  });

  await ca('kế toán trưởng được Giám đốc chọn (cờ máy chủ) mở được, không cần vai Giám đốc', async function () {
    var m = dungMoi(KT, { tai_chinh: true }, TL);
    await m.g.scrTcTongQuan(); await tick();
    bang('tiêu đề', m.g._t, 'Tổng quan tài chính');
    bang('một lời gọi', m.goi.map(function (x) { return x.duong; }), ['vagabond.tai_chinh.tong_quan']);
  });

  await ca('tổng quan: tổng tiền đủ số, báo chỗ chưa chốt; phần lãi lỗ hỏng chỉ thẻ đó báo; bấm thẻ mở đúng màn', async function () {
    var m = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.tong_quan': function () { return tongQuan(true); } }));
    await m.g.scrTcTongQuan(); await tick();
    var t = chu(mot(m, '[data-tctong]'));
    dung('tổng tiền đủ số', t.indexOf('1.842.350.000 đ') >= 0 || t.indexOf('1,842,350,000 đ') >= 0);
    dung('ghi tạm ứng', t.indexOf('gồm tạm ứng') >= 0);
    dung('báo chỗ chưa chốt', !!mot(m, '[data-tcchuachot]') && chu(mot(m, '[data-tcchuachot]')).indexOf('Còn 2') >= 0);
    var ll = mot(m, '[data-tcgo="TCLL"]');
    dung('thẻ lãi lỗ báo chưa đọc được', chu(ll).indexOf('Chưa đọc được') >= 0);
    var cc = chu(mot(m, '[data-tcgo="TCCHO"]'));
    dung('chờ chi số hồ sơ và chờ duyệt', cc.indexOf('15 hồ sơ') >= 0 && cc.indexOf('2 hồ sơ chờ duyệt') >= 0);
    bam(mot(m, '[data-tcgo="TCPTR"]'));
    bam(mot(m, '[data-tcgo="TCTIEN"]'));
    bang('mở đúng màn', m.vgbGo, ['TCPTR', 'TCTIEN']);
  });

  await ca('tiền hiện có: chia công ty, tạm ứng, tiền mặt; chip lệch có số, Shinhan ghi nguồn SePay, chưa chốt ghi rõ', async function () {
    var m = dungMoi(GD, null, TL);
    await m.g.scrTcTien(); await tick();
    var mb = chu(mot(m, '[data-tcnguon="nh:31561568"]'));
    dung('MB có mốc và phát sinh', mb.indexOf('Chốt 01/10/2026') >= 0 && mb.indexOf('vào +') >= 0);
    dung('MB chip lệch kèm số', mb.indexOf('Lệch SePay 200') >= 0);
    dung('Shinhan ghi nguồn', chu(mot(m, '[data-tcnguon="nh:700037279585"]')).indexOf('Số dư SePay báo') >= 0);
    dung('OCB chưa chốt', chu(mot(m, '[data-tcnguon="nh:0901486556"]')).indexOf('Chưa chốt') >= 0);
    dung('két có chốt ca', chu(mot(m, '[data-tcnguon="tm:TCV"]')).indexOf('Chốt ca 31/10/2026 22:23') >= 0);
    var toan = chu(m.khung);
    dung('ba nhóm', toan.indexOf('Ngân hàng công ty') >= 0 && toan.indexOf('Tài khoản tạm ứng') >= 0 && toan.indexOf('Tiền mặt') >= 0);
    dung('không lộ số tài khoản đầy đủ', toan.indexOf('31561568') < 0 && toan.indexOf('0901486556') < 0);
    bam(mot(m, '[data-tcgo="TCCD"]'));
    bang('nút chốt mở cài đặt', m.vgbGo, ['TCCD']);
  });

  await ca('dòng tiền: mặc định 7 ngày, bấm 30 ngày hỏi lại đúng kỳ; báo số lần chuyển nội bộ đã bỏ', async function () {
    var m = dungMoi(GD, null, TL);
    vm.runInNewContext('tcKyDong = 7;', m.g);
    await m.g.scrTcDong(); await tick();
    bang('kỳ đầu', m.goi[0].ts, { so_ngay: 7 });
    dung('nội bộ', chu(m.khung).indexOf('Đã bỏ 2 lần chuyển') >= 0);
    bam(mot(m, '[data-tcky="30"]')); await tick();
    bang('kỳ sau', m.goi[1].ts, { so_ngay: 30 });
  });

  await ca('lãi lỗ: tháng đang chạy có cảnh báo; lùi tháng hỏi tháng trước; không tiến quá tháng này', async function () {
    var m = dungMoi(GD, null, TL);
    vm.runInNewContext('tcThang = "";', m.g);
    await m.g.scrTcLaiLo(); await tick();
    dung('cảnh báo tháng đang chạy', chu(m.khung).indexOf('Tháng đang chạy') >= 0);
    dung('bảng có lãi ròng', chu(mot(m, '[data-tcbanglailo]')).indexOf('Lãi ròng') >= 0);
    bam(mot(m, '[data-tcthang="1"]')); await tick();
    bang('không hỏi tháng sau', m.goi.length, 1);
    bam(mot(m, '[data-tcthang="-1"]')); await tick();
    var y = +THANG_NAY.slice(0, 4), mm = +THANG_NAY.slice(5, 7) - 1;
    if (!mm) { mm = 12; y--; }
    bang('hỏi tháng trước', m.goi[1].ts, { thang: y + '-' + ('0' + mm).slice(-2) });
  });

  await ca('tỉ lệ: bốn ô tỉ lệ, kho Baker gắn chip Bất thường, Pastry không; nút mở Dữ liệu hao hụt', async function () {
    var m = dungMoi(GD, null, TL);
    vm.runInNewContext('tcThang = "";', m.g);
    await m.g.scrTcTiLe(); await tick();
    var kho = m.khung.querySelectorAll('[data-tckho]');
    bang('hai kho', kho.length, 2);
    dung('Baker bất thường', chu(kho[0]).indexOf('Bất thường') >= 0);
    dung('Pastry không', chu(kho[1]).indexOf('Bất thường') < 0);
    dung('food cost', chu(m.khung).indexOf('22,5%') >= 0);
    bam(mot(m, '[data-tcgo="BCHH"]'));
    bang('mở dữ liệu hao hụt', m.vgbGo, ['BCHH']);
  });

  await ca('cài đặt: chốt số dư OCB, gõ số có dấu chấm, lưu đúng nguồn, ngày, số; số trống thì nhắc, không gọi máy chủ', async function () {
    var m = dungMoi(GD, null, TL);
    vm.runInNewContext('tcMoChot = "";', m.g);
    await m.g.scrTcCaiDat(); await tick();
    dung('MB đang dùng mốc', chu(mot(m, '[data-tccd="nh:31561568"]')).indexOf('Đang dùng mốc 01/10/2026') >= 0);
    bam(mot(m, '[data-tcmochot="nh:0901486556"]')); await tick();
    dung('form mở', !!mot(m, '[data-tcform]'));
    var luu = mot(m, '[data-tcluu="nh:0901486556"]');
    await bam(luu); await tick();
    dung('nhắc gõ số', m.toast.some(function (t) { return t.indexOf('Gõ số dư') >= 0; }));
    bang('chưa gọi lưu', m.goi.filter(function (x) { return x.duong === 'vagabond.tai_chinh.luu_moc'; }).length, 0);
    m.tai.getElementById('tcSoDu').value = '52.100.000';
    m.tai.getElementById('tcNgayChot').value = '2026-10-30';
    m.tai.getElementById('tcGhiChu').value = 'theo sao kê';
    await bam(mot(m, '[data-tcluu="nh:0901486556"]')); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.tai_chinh.luu_moc'; });
    bang('gọi lưu một lần', g.length, 1);
    bang('đúng tham số', g[0].ts, { nguon: 'nh:0901486556', ngay_chot: '2026-10-30', so_du: '52.100.000', ghi_chu: 'theo sao kê' });
  });

  await ca('cài đặt: Giám đốc tích kế toán trưởng rồi lưu người xem; người không phải Giám đốc không thấy mục này', async function () {
    var m = dungMoi(GD, null, TL);
    await m.g.scrTcCaiDat(); await tick();
    var nhan = m.khung.querySelectorAll('[data-tcnx]');
    bang('hai người', nhan.length, 2);
    nhan[0].querySelectorAll('input')[0].checked = true;
    await bam(mot(m, '[data-tcluunx]')); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.tai_chinh.luu_nguoi_xem'; });
    bang('gửi đúng danh sách', g[0].ts, { ds: JSON.stringify(['dung@vagabond.vn']) });
    var m2 = dungMoi(KT, { tai_chinh: true }, Object.assign({}, TL, { 'vagabond.tai_chinh.cai_dat': function () { return caiDat(false); } }));
    await m2.g.scrTcCaiDat(); await tick();
    bang('không có mục người xem', m2.khung.querySelectorAll('[data-tcnx]').length, 0);
    bang('không có nút lưu người xem', m2.khung.querySelectorAll('[data-tcluunx]').length, 0);
  });

  await ca('dự báo (Codex #524): nợ NCC đọc hỏng thì ghi Chưa đọc được, báo phần thiếu, không hiện số cuối kỳ', async function () {
    function duBao(hong) {
      return { so_du: 100000000, chua_chot: 0, hom_nay: '2026-10-31', phai_thu: 15000000, cho_chi: 0, cho_duyet: 0,
        theo_tuan: hong ? null : { qua_han: 0, tuan_1: 30000000, tuan_2: 0, tuan_3: 0, tuan_4: 0 },
        tra_ncc: hong ? null : 30000000, sau_30: hong ? null : 0,
        cuoi_ky: hong ? null : 85000000, cuoi_ky_khong_thu: hong ? null : 70000000, thieu: hong ? ['Nợ nhà cung cấp'] : [] };
    }
    var m = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.du_bao_30': function () { return duBao(true); } }));
    await m.g.scrTcDuBao(); await tick();
    dung('báo phần thiếu', chu(mot(m, '[data-tcthieu]')).indexOf('Nợ nhà cung cấp') >= 0);
    bang('không có số cuối kỳ', m.khung.querySelectorAll('[data-tccuoiky]').length, 0);
    bang('năm dòng nợ NCC ghi Chưa đọc được', m.khung.querySelectorAll('[data-tcchuadoc]').length, 5);
    var m2 = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.du_bao_30': function () { return duBao(false); } }));
    await m2.g.scrTcDuBao(); await tick();
    bang('đủ nguồn: không báo thiếu', m2.khung.querySelectorAll('[data-tcthieu]').length, 0);
    bang('đủ nguồn: có số cuối kỳ', m2.khung.querySelectorAll('[data-tccuoiky]').length, 1);
    bang('đủ nguồn: không ô nào Chưa đọc được', m2.khung.querySelectorAll('[data-tcchuadoc]').length, 0);
  });

  await ca('tính hỏng (Codex #524 vòng 3): Tổng quan và Tiền hiện có báo đỏ chỗ chưa tính được, Dòng tiền báo két thiếu', async function () {
    function tienLoi() {
      var t = tien();
      t.tong.loi = 1;
      t.dong[0] = Object.assign({}, t.dong[0], { so_du: null, loi: 1, doi_chieu: null, ghi: ['Chưa tính được, báo kỹ thuật'] });
      return t;
    }
    var tq = tongQuan(false);
    tq.tien.v.loi = 1;
    tq.dong7.v.thieu = 2;
    var m = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.tong_quan': function () { return tq; } }));
    await m.g.scrTcTongQuan(); await tick();
    dung('Tổng quan báo chỗ chưa tính được', chu(mot(m, '[data-tcloi]')).indexOf('chưa tính được') >= 0);
    dung('thẻ Dòng tiền nói thiếu két', chu(m.khung).indexOf('Thiếu tiền mặt 2 lượt két') >= 0);
    var m2 = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.tien_hien_co': tienLoi }));
    await m2.g.scrTcTien(); await tick();
    bang('Tiền hiện có: dòng báo đỏ', m2.khung.querySelectorAll('[data-tcdongloi]').length, 1);
    dung('Tiền hiện có: dòng tổng nói thiếu', chu(mot(m2, '[data-tcloi]')).indexOf('tổng đang thiếu') >= 0);
    var dongThieu = function (ts) { var k = TL['vagabond.tai_chinh.dong_tien'](ts); k.thieu = ['District 1 ngày 30/10']; return k; };
    var m3 = dungMoi(GD, null, Object.assign({}, TL, { 'vagabond.tai_chinh.dong_tien': dongThieu }));
    await m3.g.scrTcDong(); await tick();
    dung('Dòng tiền: báo két và ngày thiếu', chu(mot(m3, '[data-tcthieu]')).indexOf('District 1 ngày 30/10') >= 0);
    var m4 = dungMoi(GD, null, TL);
    await m4.g.scrTcDong(); await tick();
    bang('đủ dữ liệu: không báo thiếu', m4.khung.querySelectorAll('[data-tcthieu]').length, 0);
  });

  console.log('');
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
