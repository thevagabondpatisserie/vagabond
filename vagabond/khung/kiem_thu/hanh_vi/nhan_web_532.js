/* Bo ca kiem HANH VI cho nhan marketing tren trang order (v532).
 *
 * Vi sao co tep nay: cua-hang.js la tep nap nhan da xuat ban vao thanh chon
 * va nut dau trang. Do chuoi trong ma nguon khong chung minh duoc rang chu
 * cua marketing THAT SU thay chu goc, rang de trong thi tra ve chu goc, va
 * rang chu co the <script> khong thanh HTML. Nen o day nap THAT cua-hang.js
 * vao DOM gia dung DUNG doan HTML thanh chon cua banh.html, roi ban tin
 * preview hoac tra loi fetch gia, va soi DOM.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/nhan_web_532.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var TRANG = fs.readFileSync(path.join(GOC, 'vagabond', 'trang', 'banh.html'), 'utf8');
var CUA_HANG = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'web_order', 'cua-hang.js'), 'utf8');

function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* Lay DUNG doan HTML cua trang that, khong che lai trong ca kiem. */
function htmlThanhChon() {
  var nav = /<nav class="dich-vu"[\s\S]*?<\/nav>/.exec(TRANG);
  var tabs = /<nav class="tabs">[\s\S]*?<\/nav>/.exec(TRANG);
  if (!nav || !tabs) throw new Error('Khong thay thanh chon trong banh.html');
  return nav[0] + tabs[0] + '<span data-vgb-tieu-de="today">Bánh<br>hôm nay</span>';
}

function dungTrang(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  dg.doc(htmlThanhChon(), tai.body);
  var suKien = [], ngheWindow = {}, ngheDoc = [];
  var win = {
    vgbXemThu: !!canh.xemThu,
    VgbKhoi: { ve: function () {} },
    addEventListener: function (loai, ham) { ngheWindow[loai] = ham; },
  };
  var chaGia = { postMessage: function (d) { suKien.push(d); } };
  tai.addEventListener = function (loai, ham) { ngheDoc.push(loai); };
  tai.dispatchEvent = function (ev) { suKien.push({ loai: 'doc:' + ev.type }); };
  var that = {
    window: win, document: tai, console: console, parent: chaGia,
    location: { origin: 'https://order.test' },
    CustomEvent: function (t) { this.type = t; },
    Error: Error, JSON: JSON, Object: Object, Array: Array, String: String, Promise: Promise,
    fetch: function () {
      return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ message: canh.traLoi }); } });
    },
  };
  vm.runInNewContext(CUA_HANG, that, { filename: 'cua-hang.js' });
  return {
    tai: tai, win: win, suKien: suKien,
    guiPreview: function (nd) { ngheWindow.message({ origin: 'https://order.test', source: chaGia, data: { loai: 'vgb-noi-dung', noi_dung: nd, chon: '' } }); },
    chu: function (khoa) { return tai.querySelector('[data-vgb-nhan="' + khoa + '"]').textContent; },
  };
}

var ket = { dat: 0, hong: 0 };
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  ok  ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG ' + ten + '\n       ' + (e && e.message)); }
}

(async function () {
  await ca('trang that: nhan da xuat ban thay chu tren tab va nut, roi bao vgb-nhan', async function () {
    var m = dungTrang({ traLoi: { khoi: [], nhan: { tab_today: 'Bánh sinh nhật hôm nay', nut_dat_ban: 'Giữ bàn', tab_order: 'Đặt bánh trước' } } });
    await new Promise(function (r) { setTimeout(r, 0); });
    bang('tab hom nay doi', m.chu('tab_today'), 'Bánh sinh nhật hôm nay');
    bang('nut dat ban doi', m.chu('nut_dat_ban'), 'Giữ bàn');
    bang('tab dat truoc giu nguyen', m.chu('tab_order'), 'Đặt bánh trước');
    bang('tab store khong co trong nhan thi giu chu goc', m.chu('tab_store'), 'In store');
    dung('bo nhan ra window cho cac cau co so', m.win.vgbNhan && m.win.vgbNhan.tab_today === 'Bánh sinh nhật hôm nay');
    dung('ban su kien vgb-nhan de trang ve lai cau gio', m.suKien.some(function (s) { return s.loai === 'doc:vgb-nhan'; }));
  });

  await ca('preview: nhap doi roi xoa trang thi tra ve dung chu goc, khong ke chu cu', async function () {
    var m = dungTrang({ xemThu: true });
    m.guiPreview({ khoi: [], nhan: { tab_today: 'Bánh hôm nay của bạn' } });
    bang('doi theo nhap', m.chu('tab_today'), 'Bánh hôm nay của bạn');
    m.guiPreview({ khoi: [], nhan: { tab_today: '   ' } });
    bang('de trong thi ve chu goc trong HTML', m.chu('tab_today'), 'Có sẵn hôm nay');
    m.guiPreview({ khoi: [] });
    bang('khong co khoa nhan cung ve chu goc', m.chu('tab_today'), 'Có sẵn hôm nay');
  });

  await ca('chu cua marketing co the HTML thi van la chu, khong thanh phan tu', async function () {
    var m = dungTrang({ xemThu: true });
    m.guiPreview({ khoi: [], nhan: { tab_today: '<b onclick="x()">Hôm nay</b>' } });
    var tab = m.tai.querySelector('[data-vgb-nhan="tab_today"]');
    bang('giu nguyen chuoi', tab.textContent, '<b onclick="x()">Hôm nay</b>');
    bang('khong sinh phan tu con', tab.children.length, 0);
  });

  await ca('khoa nhan la khoa cua may chu, tab khong co trong nhan thi khong bi xoa chu', async function () {
    var m = dungTrang({ xemThu: true });
    m.guiPreview({ khoi: [], nhan: { khoa_la: 'x' } });
    bang('tab season giu', m.chu('tab_season'), 'In season');
    bang('nut thanh vien giu', m.chu('nut_thanh_vien'), 'Thành viên');
  });

  console.log(ket.hong ? 'HONG ' + ket.hong + '/' + (ket.dat + ket.hong) : 'PASS ' + ket.dat + ' ca hanh vi nhan web (v532)');
  process.exitCode = ket.hong ? 1 : 0;
})().catch(function (e) { console.error(e); process.exitCode = 1; });
