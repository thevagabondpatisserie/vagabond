/* Ca kiểm HÀNH VI v638: màn Hoa hồng giới thiệu (anh Việt duyệt 04/11/2026).
 *
 * Nạp THẬT 67-hoa-hong-gioi-thieu.js cùng các hàm nền thật (h, money, vgbKhop,
 * errMsg, posChipNut, kmHangChip) vào DOM giả. Máy chủ giả trả dữ liệu đúng
 * dạng gioi_thieu.cua_toi / toan_tiem / dua_vao_kpi và ghi lại lời gọi; phép
 * tính số chạy thật ở thu_gioi_thieu_638.py. Mỗi ca bấm đúng chuỗi thao tác.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/hoa_hong_gioi_thieu_638.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
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
var NEN = doc('00-nen.js');
var HAM = ['h', 'money', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(doc('03-kho-chung-tu.js'), 'errMsg'), layHam(doc('09-tinh-tien-quay.js'), 'posChipNut'),
    layHam(doc('13-khuyen-mai.js'), 'kmHangChip')]).join('\n');

function dong(ma, tt, hh, them) {
  var nhan = { ghi_so: 'Đã ghi sổ', cho: 'Chờ', huy: 'Đơn huỷ', hoan: 'Đã hoàn tiền' };
  return Object.assign({ ma: ma, nguon: 'hd', hien: 'Đơn #' + ma, ngay: '2026-11-03', loai: 'web', nhan_loai: 'Đặt bánh web',
    nguoi: 'ngan@x', ten_nguoi: 'Nguyễn Thị Ngân', tien_hang: 900000, pt: 2, hoa_hong: hh, tt: tt, nhan_tt: nhan[tt],
    ghi_chu: '', doi_boi: '', doi_luc: '' }, them || {});
}
function cuaToi(o) {
  o = o || {};
  var ds = o.ds || [dong('91428', 'ghi_so', 18000), dong('SI-2', 'ghi_so', 10000, { loai: 'tai_ban', nhan_loai: 'Tại bàn', hien: 'SI-2' }),
    dong('SI-3', 'cho', 6000), dong('DW-1', 'cho', 10000), dong('SI-9', 'huy', 0)];
  return { ky: '2026-11', ds: ds, bat: o.bat === undefined ? 1 : o.bat, xem_toan_tiem: o.tiem || 0, pt_web: 2, pt_tai_ban: 2,
    tong: { ghi_so: { so_don: 2, tien_hang: 1400000, hoa_hong: 28000 }, cho: { so_don: 2, tien_hang: 800000, hoa_hong: 16000 },
      huy: { so_don: 1, tien_hang: 0, hoa_hong: 0 } } };
}
function toanTiem() {
  return { ky: '2026-11', bat: 1, doi_duoc: 1,
    bang: [{ nguoi: 'ngan@x', ten_nguoi: 'Nguyễn Thị Ngân', so_don: 2, so_cho: 2, tien_hang: 1400000, hoa_hong: 28000, hoa_hong_cho: 16000 },
      { nguoi: 'lan@x', ten_nguoi: 'Trần Lan', so_don: 1, so_cho: 0, tien_hang: 1000000, hoa_hong: 20000, hoa_hong_cho: 0 }],
    ds: [dong('91428', 'ghi_so', 18000), dong('SI-5', 'ghi_so', 20000, { nguoi: 'lan@x', ten_nguoi: 'Trần Lan' }),
      dong('SI-6', 'hoan', 0, { nguoi: 'lan@x', ten_nguoi: 'Trần Lan' })],
    tong: { ghi_so: { so_don: 3, tien_hang: 2400000, hoa_hong: 48000 }, cho: { so_don: 2, tien_hang: 800000, hoa_hong: 16000 },
      huy: { so_don: 1, tien_hang: 0, hoa_hong: 0 } } };
}

function dungMoi(duLieu) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div'), day = new dg.ElementGia('div');
  khung.parentNode = tai.body; day.parentNode = tai.body;
  tai.body.children.push(khung, day);
  var goi = [], toastDs = [], hoi = [], xuat = [], sheetDs = [], chuDs = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
    today: function () { return '2026-11-15'; },
    frame: function (t, html, opt) {
      khung.innerHTML = html; khung.onclick = null; that._t = t;
      day.innerHTML = (opt && opt.footer) || '';
      return khung;
    },
    go: function (fn) { return fn(); },
    toast: function (m) { toastDs.push(m); },
    hoiCo: function (t) { hoi.push(t); return Promise.resolve(that._dongY !== false); },
    hoiChu: function (t) { chuDs.push(t); return Promise.resolve('Khách báo gõ nhầm số'); },
    sheet: function (t, items, cur, onPick) { sheetDs.push({ t: t, items: items, onPick: onPick }); },
    dsXuatExcel: function (man, loc) { xuat.push([man, loc]); return Promise.resolve(); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var d = duLieu[duong];
      if (d instanceof Error) return Promise.reject(d);
      return Promise.resolve(typeof d === 'function' ? d(ts) : JSON.parse(JSON.stringify(d || { ok: 1 })));
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(doc('67-hoa-hong-gioi-thieu.js'), that, { filename: '67-hoa-hong-gioi-thieu.js' });
  return { g: that, khung: khung, day: day, goi: goi, toast: toastDs, hoi: hoi, xuat: xuat, sheet: sheetDs, chu: chuDs };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function ds(m, c) { return m.khung.querySelectorAll(c); }
function thuocTinh(m, c, t) { return ds(m, c).map(function (x) { return x.getAttribute(t); }); }
function goiDuong(m) { return m.goi.map(function (x) { return x.duong; }); }
async function bam(el) { var r = el.click(); await tick(); return r; }

(async function () {
  console.log('v638 Hoa hồng giới thiệu: màn của tôi, toàn tiệm, đưa vào KPI, đổi người, xuất Excel');

  await ca('của tôi: hiện đúng từng đơn (mã đơn, loại, tiền hàng, hoa hồng, trạng thái) và dòng tạm tính đã ghi sổ, đang chờ; không có chế độ toàn tiệm', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.cua_toi': cuaToi() });
    await m.g.scrHhgt(); await tick();
    bang('gọi đúng tháng này', m.goi.map(function (x) { return [x.duong, x.ts.ky]; }), [['vagabond.gioi_thieu.cua_toi', '2026-11']]);
    bang('năm đơn', thuocTinh(m, '[data-hhgtdon]', 'data-hhgtdon'), ['91428', 'SI-2', 'SI-3', 'DW-1', 'SI-9']);
    bang('hoa hồng từng đơn', thuocTinh(m, '[data-hhgthh]', 'data-hhgthh'), ['18000', '10000', '6000', '10000', '0']);
    bang('trạng thái từng đơn', thuocTinh(m, '[data-hhgttt]', 'data-hhgttt'), ['ghi_so', 'ghi_so', 'cho', 'cho', 'huy']);
    var t = chu(m.khung);
    dung('mã đơn, loại, tiền hàng hiện ra', t.indexOf('Đơn #91428') >= 0 && t.indexOf('Tại bàn') >= 0 && t.indexOf('900.000') >= 0);
    bang('tạm tính: đã ghi sổ và đang chờ', [ds(m, '[data-hhgtghiso]')[0].getAttribute('data-hhgtghiso'), ds(m, '[data-hhgtcho]')[0].getAttribute('data-hhgtcho')], ['28000', '16000']);
    dung('chữ tiền có dấu chấm', t.indexOf('28.000 đ') >= 0 && t.indexOf('16.000 đ') >= 0);
    bang('không có chip toàn tiệm, không nút đáy', [ds(m, '[data-hhgtche]').length, m.day.querySelectorAll('[data-hhgtkpi]').length], [0, 0]);
    bang('không ô select', ds(m, 'select').length, 0);
  });

  await ca('của tôi: chip trạng thái lọc tại chỗ (Chờ chỉ còn 2 đơn), ô tìm theo mã đơn; tháng trước gọi lại máy chủ', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.cua_toi': cuaToi() });
    await m.g.scrHhgt(); await tick();
    await bam(ds(m, '[data-hhgttt-chon]').filter(function (x) { return x.getAttribute('data-hhgttt-chon') === 'cho'; })[0]);
    bang('chỉ đơn chờ', thuocTinh(m, '[data-hhgtdon]', 'data-hhgtdon'), ['SI-3', 'DW-1']);
    bang('không gọi thêm máy chủ khi lọc', goiDuong(m).length, 1);
    await bam(ds(m, '[data-hhgttt-chon]').filter(function (x) { return x.getAttribute('data-hhgttt-chon') === ''; })[0]);
    var o = m.g.document.getElementById('hhgtTim');
    o.value = '91428'; o.dispatchEvent(dg.suKien('change', {}, o)); await tick();
    bang('tìm mã đơn', thuocTinh(m, '[data-hhgtdon]', 'data-hhgtdon'), ['91428']);
    m.g.HHGT.tim = '';
    await bam(ds(m, '[data-hhgtky]').filter(function (x) { return x.getAttribute('data-hhgtky') === '2026-10'; })[0]);
    bang('tháng trước', m.goi[m.goi.length - 1].ts.ky, '2026-10');
  });

  await ca('của tôi: tháng chưa có đơn thì câu chỉ đường; công tắc tắt thì có câu báo; máy chủ lỗi thì câu đọc được', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.cua_toi': cuaToi({ ds: [], bat: 0 }) });
    m.g.HHGT.ky = '2026-11'; m.g.HHGT.tt = ''; m.g.HHGT.che = 'toi';
    await m.g.scrHhgt(); await tick();
    var t = chu(m.khung);
    dung('rỗng: chỉ cách mời khách', t.indexOf('Mời khách gõ số điện thoại của bạn vào ô Mã giới thiệu') >= 0);
    dung('tắt: báo ô đã ẩn', t.indexOf('đang tắt trong Cài đặt') >= 0);
    var m2 = dungMoi({ 'vagabond.gioi_thieu.cua_toi': new Error('Mất mạng') });
    await m2.g.scrHhgt(); await tick();
    dung('lỗi', chu(m2.khung).indexOf('Mất mạng') >= 0);
  });

  await ca('quản lý: chip Toàn tiệm mở bảng nhân viên đúng số; bấm một người mở đơn của người đó; Xuất Excel đúng màn và tháng', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.cua_toi': cuaToi({ tiem: 1 }), 'vagabond.gioi_thieu.toan_tiem': toanTiem() });
    m.g.HHGT.che = 'toi'; m.g.HHGT.mo = '';
    await m.g.scrHhgt(); await tick();
    await bam(ds(m, '[data-hhgtche]').filter(function (x) { return x.getAttribute('data-hhgtche') === 'tiem'; })[0]);
    bang('gọi toàn tiệm', goiDuong(m)[goiDuong(m).length - 1], 'vagabond.gioi_thieu.toan_tiem');
    bang('bảng nhân viên', thuocTinh(m, '[data-hhgtnv]', 'data-hhgtnv'), ['ngan@x', 'lan@x']);
    bang('hoa hồng từng người', thuocTinh(m, '[data-hhgtnvhh]', 'data-hhgtnvhh'), ['28000', '20000']);
    bang('tổng đã ghi sổ toàn tiệm', ds(m, '[data-hhgtghiso]')[0].getAttribute('data-hhgtghiso'), '48000');
    dung('số đơn, tiền hàng', chu(m.khung).indexOf('2 đơn đã ghi sổ · tiền hàng 1.400.000 đ · 2 đơn chờ') >= 0);
    await bam(ds(m, '[data-hhgtnv]').filter(function (x) { return x.getAttribute('data-hhgtnv') === 'lan@x'; })[0]);
    bang('mở đơn của Lan', thuocTinh(m, '[data-hhgtdon]', 'data-hhgtdon'), ['SI-5', 'SI-6']);
    bang('đơn hoàn tiền không có nút đổi', thuocTinh(m, '[data-hhgtdoi]', 'data-hhgtdoi'), ['SI-5']);
    m.day.querySelectorAll('[data-hhgtxuat]')[0].onclick(); await tick();
    bang('xuất Excel', m.xuat, [['hoa_hong_gioi_thieu', { ky: '2026-11' }]]);
  });

  await ca('quản lý: Đưa vào phiếu KPI tháng hỏi lại rồi gọi máy chủ một lần, báo đúng số; bấm Thôi thì không gọi', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.toan_tiem': toanTiem(),
      'vagabond.gioi_thieu.dua_vao_kpi': { ky: '2026-11', tong: 48000, tao: [{ nguoi: 'ngan@x' }], cap_nhat: [{ nguoi: 'lan@x' }], giu: [], da_chot: [{ nguoi: 'a@x' }] } });
    m.g.HHGT.che = 'tiem';
    await m.g.scrHhgt(); await tick();
    m.g._dongY = false;
    await m.day.querySelectorAll('[data-hhgtkpi]')[0].onclick(); await tick();
    dung('Thôi: không gọi', goiDuong(m).indexOf('vagabond.gioi_thieu.dua_vao_kpi') < 0);
    m.g._dongY = true;
    await m.day.querySelectorAll('[data-hhgtkpi]')[0].onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.gioi_thieu.dua_vao_kpi'; });
    bang('gọi một lần đúng tháng', g.map(function (x) { return x.ts.ky; }), ['2026-11']);
    dung('hỏi lại nói rõ không cộng hai lần', m.hoi.length === 2);
    bang('báo kết quả', m.toast[m.toast.length - 1], 'Đã đưa 48.000 đ vào phiếu KPI: lập 1 phiếu mới, cập nhật 1 phiếu, 1 phiếu đã chốt, để nguyên.');
  });

  await ca('quản lý: Đổi người giới thiệu mở danh sách tìm được (có Gỡ), hỏi lý do, gửi đúng đơn, người, lý do rồi tải lại', async function () {
    var m = dungMoi({ 'vagabond.gioi_thieu.toan_tiem': toanTiem(),
      'vagabond.gioi_thieu.nhan_vien': { ds: [{ ma: 'lan@x', ten: 'Trần Lan', duoi: '0111' }, { ma: 'ngan@x', ten: 'Nguyễn Thị Ngân', duoi: '3456' }] },
      'vagabond.gioi_thieu.doi_nguoi': { ok: 1 } });
    m.g.HHGT.che = 'tiem'; m.g.HHGT.mo = 'ngan@x';
    await m.g.scrHhgt(); await tick();
    await bam(ds(m, '[data-hhgtdoi]').filter(function (x) { return x.getAttribute('data-hhgtdoi') === '91428'; })[0]);
    bang('mở danh sách', m.sheet.map(function (s) { return [s.t, s.items.map(function (i) { return i.value; })]; }),
      [['Người giới thiệu mới', ['', 'lan@x', 'ngan@x']]]);
    dung('mỗi lựa chọn có một dòng giải thích', m.sheet[0].items.every(function (i) { return !!i.phu; }));
    await m.sheet[0].onPick(m.sheet[0].items[1]); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.gioi_thieu.doi_nguoi'; });
    bang('gửi', g.map(function (x) { return [x.ts.ma, x.ts.nguoi, x.ts.ly_do]; }), [['91428', 'lan@x', 'Khách báo gõ nhầm số']]);
    dung('hỏi lý do', m.chu.indexOf('Lý do đổi') >= 0);
    dung('báo đã đổi và tải lại', m.toast.indexOf('Đã đổi người giới thiệu thành Trần Lan.') >= 0 && goiDuong(m).filter(function (d) { return d === 'vagabond.gioi_thieu.toan_tiem'; }).length === 2);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong');
  process.exit(ket.hong ? 1 : 0);
})();
