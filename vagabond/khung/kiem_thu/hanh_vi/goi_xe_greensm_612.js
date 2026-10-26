/* Ca kiểm HÀNH VI v612: màn Gọi xe dùng chung cho Ahamove và GreenSM.
 *
 * Anh Việt 26/10/2026: nối GreenSM thật. GreenSM bắt xem giá trước (giá gắn
 * mã fee_id có hạn), và còn ở môi trường thử thì giá là giá giả. Màn phải:
 *   - GreenSM đang thử: hiện cảnh báo, xem giá được, KHÔNG gọi xe được.
 *   - GreenSM thật: xem giá rồi gọi xe, gửi đúng loại xe và dịch vụ thêm đã tick.
 *   - Đổi xe hay dịch vụ thêm sau khi xem giá: giá cũ bỏ, phải xem lại.
 *   - Ahamove vẫn đi đúng ba cửa cũ.
 *   - Hộp "Book xe qua app" chọn GreenSM thì mở màn này, không book thẳng.
 *
 * Nạp THẬT hàm scrVdGoiXe từ 12-van-don.js vào DOM giả, máy chủ giả chỉ ghi
 * lời gọi. Mỗi ca bấm đúng chuỗi của Sales, không gọi hàm nội bộ "cho chắc"
 * (điều 15). Phần máy chủ (giữ bản giá, chặn môi trường thử) chạy thật ở
 * thu_greensm_612.py.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/goi_xe_greensm_612.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), VD = doc('12-van-don.js');

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
function layKhoi(src, dau, cuoi) {
  var i = src.indexOf(dau);
  if (i < 0) throw new Error('Khong thay ' + dau);
  var j = src.indexOf(cuoi, i);
  if (j < 0) throw new Error('Khong thay ' + cuoi);
  return src.slice(i, j);
}
var HAM = ['h', 'money', 'num'].map(function (t) { return layHam(NEN, t); }).join('\n');
var MAN = layKhoi(VD, 'var VD_GOI_XE = {', 'var VD_APPS = [');
/* Nhánh 'book' của màn chi tiết vận đơn, nạp nguyên văn. */
var BOOK = layKhoi(VD, "    if (k === 'book') {", "  });\n}\n\nvar vdTay");

var DV_GSM = { dich_vu: [
  { id: 1878, ten: 'Express for partner', xe_may: true, addon: [{ id: 10, ten: 'Giao hàng tận tay' }] },
  { id: 2099, ten: 'Van Express', xe_may: false, addon: [] }], mac_dinh: 1878 };
var DV_AHA = { dich_vu: [{ id: 'SGN-BIKE', ten: 'Siêu Tốc', addon: [{ id: 'SGN-BIKE-FRAGILE', ten: 'Dễ vỡ', gia: 10000 }] }], mac_dinh: 'SGN-BIKE' };

function dungMoi(dangThu) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], hoi = [], tin = [], sheetCb = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout,
    frame: function (t, html, o) {
      khung.innerHTML = html + ((o && o.footer) || ''); khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { return fn(); },
    busy: function () {},
    toast: function (m) { tin.push(m); },
    baoTin: function (m) { tin.push('LOI ' + m); },
    xacNhan: function (m) { hoi.push(m); return Promise.resolve(true); },
    scrVdView: function () { that._ve = 'view'; },
    sheet: function (t, ops, cur, cb) { sheetCb.push({ t: t, ops: ops, cb: cb }); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'frappe.client.get') return Promise.resolve({ name: 'VD-1', ma_don: '91500', khach: 'Chị Lan', dia_chi: '208 Nguyễn Hữu Cảnh' });
      if (duong === 'vagabond.van_don.gsm_dich_vu') return Promise.resolve(Object.assign({ dang_thu: dangThu }, JSON.parse(JSON.stringify(DV_GSM))));
      if (duong === 'vagabond.van_don.aha_dich_vu') return Promise.resolve(JSON.parse(JSON.stringify(DV_AHA)));
      if (/bao_gia$/.test(duong)) return Promise.resolve({ tong: 80000, km: 5.33, dang_thu: dangThu });
      return Promise.resolve({});
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '12-van-don.js#goi-xe' });
  return { g: that, tai: tai, khung: khung, goi: goi, hoi: hoi, tin: tin, sheetCb: sheetCb };
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
function bam(el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function nut(m, id) { return m.tai.getElementById(id); }
function khoa(el) { return el.hasAttribute('disabled'); }
async function bamNut(m, id) { await nut(m, id).onclick(); await tick(); }
function cua(m, duong) { return m.goi.filter(function (x) { return x.duong === duong; }); }

async function mo(kenh, dangThu) {
  var m = dungMoi(dangThu);
  await m.g.scrVdGoiXe('VD-1', kenh);
  await tick();
  return m;
}

(async function () {
  console.log('v612 Gọi xe GreenSM: xem giá, gọi xe, môi trường thử');

  await ca('GreenSM đang chạy thử: có cảnh báo, xem giá được, nút Gọi xe khoá và bấm không gọi máy chủ', async function () {
    var m = await mo('GreenSM', true);
    bang('tiêu đề', m.g._t, 'Gọi xe GreenSM');
    dung('cảnh báo chạy thử', chu(m.khung).indexOf('GreenSM đang chạy thử') >= 0);
    dung('xe máy chọn sẵn', chu(m.khung.querySelectorAll('[data-dv="1878"]')[0]).indexOf('✓') >= 0);
    dung('Gọi xe khoá trước khi xem giá', khoa(nut(m, 'gxDat')));
    await bamNut(m, 'gxGia');
    bang('hỏi giá đúng cửa và tham số', cua(m, 'vagabond.van_don.gsm_bao_gia')[0].ts, { name: 'VD-1', service_id: 1878, addon_ids: '[]' });
    dung('hiện cước và chữ giá thử', chu(m.khung).indexOf('Cước: 80.000 đ') >= 0 && chu(m.khung).indexOf('giá thử') >= 0);
    dung('Gọi xe VẪN khoá ở môi trường thử', khoa(nut(m, 'gxDat')));
    await bamNut(m, 'gxDat');
    bang('không gọi book_xe', cua(m, 'vagabond.van_don.book_xe').length, 0);
    bang('không hỏi xác nhận', m.hoi.length, 0);
  });

  await ca('GreenSM thật: tick Giao hàng tận tay, xem giá, gọi xe gửi đúng xe và dịch vụ thêm', async function () {
    var m = await mo('GreenSM', false);
    dung('không có cảnh báo chạy thử', chu(m.khung).indexOf('đang chạy thử') < 0);
    bam(m.khung.querySelectorAll('[data-add="10"]')[0]);
    await bamNut(m, 'gxGia');
    bang('hỏi giá kèm add-on', cua(m, 'vagabond.van_don.gsm_bao_gia')[0].ts.addon_ids, '["10"]');
    dung('Gọi xe mở', !khoa(nut(m, 'gxDat')));
    await bamNut(m, 'gxDat');
    await tick();
    bang('hỏi xác nhận có số tiền', m.hoi, ['Gọi xe GreenSM cho đơn này, cước 80.000 đ?']);
    bang('book_xe đúng tham số', cua(m, 'vagabond.van_don.book_xe')[0].ts,
      { name: 'VD-1', kenh: 'GreenSM', service_id: 1878, requests_them: '["10"]' });
    bang('về màn vận đơn', m.g._ve, 'view');
  });

  await ca('đổi loại xe hay dịch vụ thêm sau khi xem giá: bỏ giá cũ, khoá Gọi xe', async function () {
    var m = await mo('GreenSM', false);
    await bamNut(m, 'gxGia');
    dung('có giá', !khoa(nut(m, 'gxDat')));
    bam(m.khung.querySelectorAll('[data-add="10"]')[0]);
    dung('tick thêm: khoá lại', khoa(nut(m, 'gxDat')));
    dung('bảo bấm Xem giá', chu(m.khung).indexOf('Bấm Xem giá để GreenSM báo cước') >= 0);
    await bamNut(m, 'gxGia');
    bam(m.khung.querySelectorAll('[data-dv="2099"]')[0]);
    dung('đổi xe: khoá lại', khoa(nut(m, 'gxDat')));
    dung('đổi xe thì bỏ tick cũ', chu(m.khung).indexOf('☑️') < 0);
    await bamNut(m, 'gxGia');
    bang('lần hỏi sau theo xe mới', cua(m, 'vagabond.van_don.gsm_bao_gia')[2].ts, { name: 'VD-1', service_id: '2099', addon_ids: '[]' });
  });

  await ca('Ahamove vẫn đi ba cửa cũ, không bị khoá vì cờ chạy thử của GreenSM', async function () {
    var m = await mo('Ahamove', false);
    bang('hỏi danh sách xe Ahamove', cua(m, 'vagabond.van_don.aha_dich_vu').length, 1);
    bam(m.khung.querySelectorAll('[data-add="SGN-BIKE-FRAGILE"]')[0]);
    await bamNut(m, 'gxGia');
    bang('báo giá Ahamove', cua(m, 'vagabond.van_don.aha_bao_gia')[0].ts,
      { name: 'VD-1', service_id: 'SGN-BIKE', requests_them: '["SGN-BIKE-FRAGILE"]' });
    await bamNut(m, 'gxDat');
    await tick();
    bang('gọi xe Ahamove', cua(m, 'vagabond.van_don.book_xe')[0].ts,
      { name: 'VD-1', kenh: 'Ahamove', service_id: 'SGN-BIKE', requests_them: '["SGN-BIKE-FRAGILE"]' });
  });

  await ca('hộp "Book xe qua app": chọn GreenSM thì mở màn gọi xe, không book thẳng', async function () {
    var m = dungMoi(false);
    var mo2 = [];
    m.g.scrVdGoiXe = function (name, kenh) { mo2.push([name, kenh]); };
    vm.runInNewContext('var k = "book", name = "VD-1"; (async function(){' + BOOK + '})()', m.g);
    await tick();
    var s = m.sheetCb[0];
    dung('có hộp chọn', !!s);
    var gsm = s.ops.filter(function (o) { return o.value === 'GreenSM'; })[0];
    dung('nhãn không còn "chờ key"', gsm.label.indexOf('chờ') < 0);
    await s.cb(gsm);
    bang('mở màn gọi xe GreenSM', mo2, [['VD-1', 'GreenSM']]);
    bang('không book thẳng', cua(m, 'vagabond.van_don.book_xe').length, 0);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
