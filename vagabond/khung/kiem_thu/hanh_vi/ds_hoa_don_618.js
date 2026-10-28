/* Ca kiểm HÀNH VI v618: màn Hoá đơn hôm nay của quầy (scrPosDs).
 *
 * Chị Dễ báo 28/10/2026 (ảnh quầy NVHTN): "phần xem lại danh sách hoá đơn
 * đang bị lỗi", chữ "16 hoá đơn · 2.458.528 đ" dựng đứng từng ký tự một.
 * Nguyên nhân: v617 trả `.card` về hàng ngang (Bootstrap của Frappe để cột);
 * ba thẻ của màn này khai display:flex mà không ghi hướng, nút `.btn`
 * width:100% chiếm trọn hàng, chữ bên cạnh co còn 0 điểm. Đo trên site thật
 * 375 điểm: thẻ tổng 351 điểm, khối chữ 0, hai nút 321 điểm mỗi nút.
 *
 * Ca này nạp THẬT scrPosDs, posChipBill, chipNgay, locHang... vào DOM giả và
 * bấm đúng chuỗi thao tác. DOM giả không tính bố cục: phần đo kích thước nằm
 * ở PR (đo trên site thật). Ở đây chốt CẤU TRÚC gây ra lỗi (thẻ flex phải ghi
 * hướng, nút trong hàng phải width:auto) và các hành vi chống thao tác nhầm.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/ds_hoa_don_618.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var BEP = path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
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
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), BQ = doc('10-bill-quay.js'), DS = doc('08-doanh-so-sales.js');
var HAM = ['h', 'money'].map(function (t) { return layHam(NEN, t); })
  .concat(['posNgayVn', 'locTim', 'posChipNut', 'locHddt', 'locKhoiTong', 'locHang', 'locNguonPt'].map(function (t) { return layHam(POS, t); }))
  .concat(['chipNgay', 'timDonO', 'ngayCong'].map(function (t) { return layHam(DS, t); }))
  .concat(['posChipBill', 'scrPosDs'].map(function (t) { return layHam(BQ, t); }))
  .concat(["var posLocTt = 'tat_ca', posLocNg = '', posLocHd = '', posDsNgay = '', posQuay = null, DS_MAU_HD = {};"]).join('\n');

var HOM_NAY = '2026-10-28';
function bill(ten, tien, them) {
  var r = { name: ten, grand_total: tien, docstatus: 1, creation: HOM_NAY + ' 09:15:00', custom_nguon: 'GrabFood',
    vgb_pt_thanh_toan: 'GrabFood', total_qty: 2 };
  Object.keys(them || {}).forEach(function (k) { r[k] = them[k]; });
  return r;
}
function dsMay() {
  return { bill: [
    bill('HD-1', 1724750),
    bill('HD-2', 375000, { custom_nguon: 'Tại chỗ', vgb_pt_thanh_toan: 'Chuyển khoản', docstatus: 0 }),
    bill('HD-3', 50000, { custom_nguon: 'Tại chỗ', vgb_pt_thanh_toan: 'Tiền mặt', cho_kho: 1 })] };
}

function dungMoi() {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], ve = 0;
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN,
    today: function () { return HOM_NAY; },
    frame: function (t, html) { khung.innerHTML = html; khung.onclick = null; khung._nghe = []; that._t = t; return khung; },
    go: function (fn) { ve++; return fn(); },
    toast: function (s) { that._toast = s; },
    veODate: function () {}, timDonGan: function () {},
    tkLoc: function () { return []; },
    tkConCho: function (r) { return !!r.cho_kho; },
    tkChip: function () { return null; },
    khachTrenDon: function () { return {}; },
    hddtChoXuatChu: function () { return ''; },
    hdThuoc: function () { return false; },
    scrPosQuay: function () { that._mo = 'moi'; },
    scrPosChotCa: function () { that._mo = 'chot'; },
    scrPosBill: function (n) { that._mo = 'bill:' + n; },
    scrTruKho: function () { that._mo = 'kho'; },
    api: function (duong, ts) { goi.push({ duong: duong, ts: ts }); return Promise.resolve(dsMay()); },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham.js' });
  that.posQuay = { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên' };
  vm.runInNewContext("posQuay = { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên' };", that);
  return { g: that, khung: khung, goi: goi, ve: function () { return ve; } };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
async function nghi() { for (var i = 0; i < 6; i++) await new Promise(function (r) { setTimeout(r, 2); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function mot(el, chon) { var r = el.querySelectorAll(chon); if (r.length !== 1) throw new Error('mong dung 1 ' + chon + ', co ' + r.length); return r[0]; }
async function bam(m, el) { if (!el) throw new Error('khong co nut'); el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); }
function kieu(el) { return el.style || {}; }

(async function () {
  console.log('v618 Hoá đơn hôm nay của quầy');

  await ca('ba thẻ từng vỡ ghi rõ hướng: tổng xếp CỘT, kho và ngày xếp HÀNG', async function () {
    var m = dungMoi();
    await m.g.scrPosDs(); await nghi();
    bang('thẻ tổng', [kieu(mot(m.khung, '[data-pdtong]')).display, kieu(mot(m.khung, '[data-pdtong]')).flexDirection], ['flex', 'column']);
    bang('thẻ kho', kieu(mot(m.khung, '[data-pdkho]')).flexDirection, 'row');
    bang('thẻ ngày', [kieu(mot(m.khung, '[data-pdngay]')).flexDirection, kieu(mot(m.khung, '[data-pdngay]')).flexWrap], ['row', 'wrap']);
    dung('chữ tổng đủ: ' + chu(mot(m.khung, '[data-pdtong]')), chu(mot(m.khung, '[data-pdtong]')).indexOf('3 hoá đơn · 2.149.750 đ') >= 0);
  });

  await ca('mọi thẻ .card khai display:flex trên màn đều ghi flex-direction', async function () {
    var m = dungMoi();
    await m.g.scrPosDs(); await nghi();
    var thieu = m.khung.querySelectorAll('.card').filter(function (c) {
      return kieu(c).display === 'flex' && !kieu(c).flexDirection;
    }).map(function (c) { return chu(c).slice(0, 30); });
    bang('thẻ thiếu hướng', thieu, []);
  });

  await ca('nút .btn trong hàng ngang không chiếm 100%: width:auto, cao ít nhất 44', async function () {
    var m = dungMoi();
    await m.g.scrPosDs(); await nghi();
    ['#posDsMoi', '#posDsChotCa', '#posDsTruKho'].forEach(function (id) {
      var b = mot(m.khung, id);
      bang(id + ' width', kieu(b).width, 'auto');
      bang(id + ' min-height', kieu(b).minHeight, '44px');
    });
  });

  await ca('nút Hoá đơn mới và Chốt ca vẫn đưa đúng màn', async function () {
    var m = dungMoi();
    await m.g.scrPosDs(); await nghi();
    await bam(m, mot(m.khung, '#posDsMoi')); bang('hoá đơn mới', m.g._mo, 'moi');
    await m.g.scrPosDs(); await nghi();
    await bam(m, mot(m.khung, '#posDsChotCa')); bang('chốt ca', m.g._mo, 'chot');
  });

  await ca('xem ngày khác: biển vàng nói rõ không phải hôm nay, bấm Về hôm nay thì về và bỏ lọc', async function () {
    var m = dungMoi();
    vm.runInNewContext("posDsNgay = '2026-10-26'; posLocHd = 'da_ky';", m.g);
    await m.g.scrPosDs(); await nghi();
    var bien = mot(m.khung, '[data-pdkhac]');
    dung('nói ngày: ' + chu(bien), chu(bien).indexOf('26/10/2026') >= 0 && chu(bien).indexOf('không phải hôm nay') >= 0);
    dung('ngày khác thì không có nút Hoá đơn mới', m.khung.querySelectorAll('#posDsMoi').length === 0);
    var nut = m.khung.querySelectorAll('[data-pdbuoc="0"]').filter(function (x) { return bien.contains ? bien.contains(x) : true; })[0];
    await bam(m, nut);
    bang('về hôm nay', vm.runInNewContext('posDsNgay', m.g), HOM_NAY);
    bang('bỏ cả lọc hoá đơn điện tử', vm.runInNewContext('posLocHd', m.g), '');
    bang('hôm nay không còn biển', m.khung.querySelectorAll('[data-pdkhac]').length, 0);
  });

  await ca('đổi ngày bằng chip Hôm trước cũng bỏ CẢ BA bộ lọc', async function () {
    var m = dungMoi();
    vm.runInNewContext("posLocTt = 'da_ghi'; posLocNg = 'ng:GrabFood'; posLocHd = 'da_ky';", m.g);
    await m.g.scrPosDs(); await nghi();
    await bam(m, m.khung.querySelectorAll('[data-pdbuoc="-1"]')[0]);
    bang('ngày lùi', vm.runInNewContext('posDsNgay', m.g), '2026-10-27');
    bang('ba bộ lọc', vm.runInNewContext('[posLocTt, posLocNg, posLocHd]', m.g), ['tat_ca', '', '']);
  });

  await ca('đổi ngày bằng ô lịch cũng bỏ CẢ BA bộ lọc', async function () {
    var m = dungMoi();
    vm.runInNewContext("posLocTt = 'da_ghi'; posLocNg = 'ng:GrabFood'; posLocHd = 'da_ky';", m.g);
    await m.g.scrPosDs(); await nghi();
    var o = m.g.document.getElementById('posDsDate');
    o.value = '2026-10-20';
    o.onchange(); await nghi();
    bang('ngày theo ô lịch', vm.runInNewContext('posDsNgay', m.g), '2026-10-20');
    bang('ba bộ lọc', vm.runInNewContext('[posLocTt, posLocNg, posLocHd]', m.g), ['tat_ca', '', '']);
  });

  await ca('đang lọc thì nói lọc gì và có Bỏ lọc; bấm Bỏ lọc hiện lại đủ hoá đơn', async function () {
    var m = dungMoi();
    vm.runInNewContext("posLocTt = 'da_ghi'; posLocNg = 'ng:GrabFood';", m.g);
    await m.g.scrPosDs(); await nghi();
    var dl = mot(m.khung, '[data-pddangloc]');
    dung('nói rõ lọc: ' + chu(dl), chu(dl).indexOf('Đã ghi sổ') >= 0 && chu(dl).indexOf('GrabFood') >= 0);
    bang('đang lọc chỉ hiện 1', m.khung.querySelectorAll('[data-bill]').length, 1);
    await bam(m, mot(m.khung, '[data-pbo]'));
    bang('đủ 3 hoá đơn', m.khung.querySelectorAll('[data-bill]').length, 3);
    bang('không còn dòng đang lọc', m.khung.querySelectorAll('[data-pddangloc]').length, 0);
  });

  await ca('không lọc gì thì không hiện dòng Đang lọc', async function () {
    var m = dungMoi();
    await m.g.scrPosDs(); await nghi();
    bang('không có', m.khung.querySelectorAll('[data-pddangloc]').length, 0);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
