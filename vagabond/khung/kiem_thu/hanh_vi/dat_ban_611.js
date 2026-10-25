/* Ca kiểm HÀNH VI v611: màn Thông tin đặt bàn (phân hệ Bán hàng).
 *
 * Anh Việt 25/10/2026 duyệt mockup: chip khoảng ngày, thẻ tóm tắt bốn ô bấm
 * được, ô tìm tên hoặc SĐT, thẻ từng bàn có Gọi, Xác nhận, Huỷ, Khách đã đến;
 * bảng Xác nhận có lời nhắn và công tắc gửi email; bảng Huỷ bắt buộc lý do có
 * chip mẫu.
 *
 * Nạp THẬT 57-dat-ban.js cùng các hàm nền nó dùng vào DOM giả. Máy chủ giả chỉ
 * trả danh sách phiếu và ghi lại lời gọi; phép đổi trạng thái, gửi thư, báo Zalo
 * chạy thật ở thu_dat_ban_zalo_611.py. Mỗi ca bấm đúng chuỗi thao tác của quản
 * lý, không gọi thêm hàm nội bộ nào "cho chắc" (điều 15).
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/dat_ban_611.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KHUON = doc('15-khuon-danh-sach.js');
var KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js');
var MAN = doc('57-dat-ban.js');

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
var HAM = ['h', 'money', 'today', 'vgbChuan', 'vgbKhop'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut')])
  .concat(['dsccHang', 'dsCongCu', 'dsCongCuNoi'].map(function (t) { return layHam(KHUON, t); }))
  .concat(['var scanBarcode = function () { return Promise.resolve(null); };'])
  .concat([layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')]).join('\n');

function ngayCong(n) {
  var d = new Date(); d.setDate(d.getDate() + n);
  return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
}
var MAI = ngayCong(1), QUA = ngayCong(-1);
function rows() {
  return [
    { name: 'DB-1', ten: 'Nguyễn Minh Anh', sdt: '0909 123 456', co_so: 'TCV', ten_co_so: 'District 1', ngay: MAI, gio: '18:30',
      so_khach: 4, tre_em: 1, dip: 'Sinh nhật', khu_vuc: 'Bàn sofa thấp', email: 'minhanh@gmail.com',
      banh_kem_theo: '1 Entremet Pistachio 16cm', ghi_chu: 'Cho em xin góc yên tĩnh', trang_thai: 'Chờ xác nhận' },
    { name: 'DB-2', ten: 'Trần Hoàng Long', sdt: '0912345678', co_so: 'TCV', ten_co_so: 'District 1', ngay: MAI, gio: '19:00',
      so_khach: 2, tre_em: 0, dip: 'Không có dịp riêng', khu_vuc: 'Phòng áp mái', email: '', trang_thai: 'Chờ xác nhận' },
    { name: 'DB-3', ten: 'Lê Thu', sdt: '0987654321', co_so: 'TCV', ten_co_so: 'District 1', ngay: MAI, gio: '16:00',
      so_khach: 3, tre_em: 0, email: 'thu@x.vn', trang_thai: 'Đã xác nhận', xu_ly_boi: 'Lê Hoàng Dễ',
      xu_ly_luc: MAI + ' 10:12:00', thu_khach: 'đã gửi email cho khách lúc 10:12' },
    { name: 'DB-4', ten: 'Phạm Thu Hà', sdt: '0901111222', co_so: 'TCV', ten_co_so: 'District 1', ngay: QUA, gio: '10:00',
      so_khach: 4, tre_em: 0, trang_thai: 'Đã đến', xu_ly_boi: 'Dễ' },
    { name: 'DB-5', ten: 'Khách quá giờ', sdt: '0903 678 345', co_so: 'TCV', ten_co_so: 'District 1', ngay: QUA, gio: '11:00',
      so_khach: 2, tre_em: 0, email: 'q@x.vn', trang_thai: 'Chờ xác nhận' },
  ];
}
var LY_DO = ['Hết chỗ khung giờ này', 'Khách xin huỷ', 'Không liên lạc được khách', 'Tiệm đóng cửa hôm đó'];
var QLCH = ['VGB - Quản lý cửa hàng'];
var QUAY = ['VGB - Nhân viên bán hàng'];

function dungMoi(vai, loi) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], hoi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
    S: { roles: vai, stack: [] },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html) {
      khung.innerHTML = html; khung._nghe = {}; khung.onclick = null; that._t = t; return khung;
    },
    go: function (fn) { return fn(); },
    busy: function () {},
    toast: function (m) { toastDs.push(m); },
    confirmSheet: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(true); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.dat_ban.ds_dat_ban') {
        return Promise.resolve({ rows: rows(), dem: { hom_nay: 0, ngay_mai: 3, '7_ngay': 3, da_qua: 2 },
          hom_nay: ngayCong(0), khoang: ts.khoang, ly_do_mau: LY_DO });
      }
      if (loi) return Promise.reject(new Error(loi));
      return Promise.resolve({ ok: 1, thu_khach: 'đã gửi email cho khách lúc 15:00' });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '57-dat-ban.js' });
  return { g: that, tai: tai, khung: khung, goi: goi, toast: toastDs, hoi: hoi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 25); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(m, el) { el.dispatchEvent(dg.suKien('click', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === 'vagabond.dat_ban.' + t; }); }
function the(m, ten) { return m.khung.querySelectorAll('[data-dbthe="' + ten + '"]')[0]; }
function nutTrong(el, attr) { return el ? el.querySelectorAll('[' + attr + ']')[0] : null; }

async function mo(vai, loi, dat) {
  var m = dungMoi(vai || QLCH, loi);
  if (dat) vm.runInNewContext(dat, m.g);
  await m.g.scrDatBan();
  await tick();
  return m;
}

(async function () {
  console.log('v611 Thông tin đặt bàn: màn danh sách, Xác nhận, Huỷ, Khách đã đến');

  await ca('quản lý mở màn: chip khoảng ngày, thẻ tóm tắt bốn ô, thẻ bàn đủ thông tin và đúng nút theo trạng thái', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bang('tiêu đề', m.g._t, 'Thông tin đặt bàn');
    bang('hỏi đúng khoảng', goiTen(m, 'ds_dat_ban')[0].ts, { khoang: '7_ngay' });
    var chip = m.khung.querySelectorAll('[data-dscc]').map(function (x) { return x.getAttribute('data-dscc') + '=' + chu(x); });
    bang('bốn chip luôn hiện, có số bàn còn giữ', chip, ['khoang|hom_nay=Hôm nay', 'khoang|ngay_mai=Ngày mai 3',
      'khoang|7_ngay=7 ngày tới 3', 'khoang|da_qua=Đã qua']);
    var tom = chu(m.khung.querySelectorAll('[data-dbtom]')[0]);
    dung('tổng bàn còn giữ và khách: ' + tom, tom.indexOf('5 bàn · 15 khách') >= 0);
    bang('bốn ô số', m.khung.querySelectorAll('[data-dbtt]').map(function (x) { return x.getAttribute('data-dbtt') + ':' + chu(x).match(/(\d+) bàn/)[1]; }),
      ['Chờ xác nhận:3', 'Đã xác nhận:1', 'Đã đến:1', 'Đã hủy:0']);
    var t1 = the(m, 'DB-1'), s1 = chu(t1);
    ['18:30', 'Nguyễn Minh Anh · 4 khách (1 trẻ em)', '0909 123 456', 'Bàn sofa thấp', 'Sinh nhật', 'Bánh đặt sẵn: 1 Entremet',
      'Khách nhắn: Cho em xin góc yên tĩnh', 'Chờ xác nhận'].forEach(function (x) { dung('thẻ DB-1 có ' + x, s1.indexOf(x) >= 0); });
    var goi = t1.querySelectorAll('[data-dbgoi]')[0];
    bang('nút Gọi một chạm, số không dấu cách', goi && goi.getAttribute('href'), 'tel:0909123456');
    dung('chờ xác nhận có Xác nhận và Huỷ', !!nutTrong(t1, 'data-dbxn') && !!nutTrong(t1, 'data-dbhuy') && !nutTrong(t1, 'data-dbden'));
    var t3 = the(m, 'DB-3');
    dung('đã xác nhận có Khách đã đến và Huỷ, không Xác nhận', !!nutTrong(t3, 'data-dbden') && !!nutTrong(t3, 'data-dbhuy') && !nutTrong(t3, 'data-dbxn'));
    dung('đã xác nhận ghi người và giờ', chu(t3).indexOf('Xác nhận bởi Lê Hoàng Dễ lúc 10:12') >= 0);
    dung('đã đến không còn nút', !nutTrong(the(m, 'DB-4'), 'data-dbxn') && !nutTrong(the(m, 'DB-4'), 'data-dbhuy') && !nutTrong(the(m, 'DB-4'), 'data-dbden'));
    var t5 = the(m, 'DB-5');
    dung('chờ xác nhận mà quá giờ: không có Xác nhận, vẫn Huỷ được', !nutTrong(t5, 'data-dbxn') && !!nutTrong(t5, 'data-dbhuy') && chu(t5).indexOf('Đã quá giờ hẹn') >= 0);
    dung('đầu nhóm theo ngày', chu(m.khung).indexOf('NGÀY MAI · ') >= 0 && chu(m.khung).indexOf('HÔM QUA · ') >= 0);
  });

  await ca('bấm ô Chờ xác nhận: chỉ còn bàn chờ, có thanh đang lọc; bấm lại là bỏ lọc', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, m.khung.querySelectorAll('[data-dbtt="Chờ xác nhận"]')[0]);
    await choDen(function () { return goiTen(m, 'ds_dat_ban').length === 2; });
    await tick();
    var ten = m.khung.querySelectorAll('[data-dbthe]').map(function (x) { return x.getAttribute('data-dbthe'); }).sort();
    bang('đúng ba bàn chờ', ten, ['DB-1', 'DB-2', 'DB-5']);
    dung('thanh đang lọc nêu số: ' + chu(m.khung.querySelectorAll('[data-dbtongloc]')[0] || m.khung),
      chu(m.khung.querySelectorAll('[data-dbtongloc]')[0]).indexOf('3 bàn · 8 khách') >= 0);
    bam(m, m.khung.querySelectorAll('[data-dbtt="Chờ xác nhận"]')[0]);
    await choDen(function () { return goiTen(m, 'ds_dat_ban').length === 3; });
    await tick();
    bang('bỏ lọc: đủ năm bàn', m.khung.querySelectorAll('[data-dbthe]').length, 5);
  });

  await ca('gõ số điện thoại có dấu cách hoặc tên không dấu: lọc ngay trên máy, không hỏi lại máy chủ', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    var o = m.tai.getElementById('dbDsTim');
    dung('có ô tìm', !!o);
    /* Gõ số là tìm dãy số LIỀN NHAU trong SĐT: DB-5 (0903 678 345) có đủ hai cụm
       345 và 678 nhưng không liền, không được ra (đột biến M15). */
    o.value = '345 678';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('chỉ bàn số đuôi 345678', m.khung.querySelectorAll('[data-dbthe]').map(function (x) { return x.getAttribute('data-dbthe'); }), ['DB-2']);
    o.value = 'nguyen minh';
    o.dispatchEvent(dg.suKien('input', {}, o));
    bang('tên không dấu', m.khung.querySelectorAll('[data-dbthe]').map(function (x) { return x.getAttribute('data-dbthe'); }), ['DB-1']);
    bang('không hỏi lại máy chủ', goiTen(m, 'ds_dat_ban').length, 1);
    dung('ô tìm vẫn nguyên (không vẽ lại cả màn)', m.tai.getElementById('dbDsTim') === o);
  });

  await ca('bấm chip Ngày mai: hỏi máy chủ đúng khoảng, bỏ lọc trạng thái và chữ tìm', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = "Đã đến"; dbTim = "abc";');
    bam(m, m.khung.querySelectorAll('[data-dscc="khoang|ngay_mai"]')[0]);
    await choDen(function () { return goiTen(m, 'ds_dat_ban').length === 2; });
    bang('khoảng', goiTen(m, 'ds_dat_ban')[1].ts, { khoang: 'ngay_mai' });
    bang('bỏ lọc cũ', vm.runInNewContext('[dbTt, dbTim]', m.g), ['', '']);
  });

  await ca('Xác nhận: bảng có thông tin bàn, lời nhắn, công tắc email bật sẵn; gửi đúng tham số rồi tải lại', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, nutTrong(the(m, 'DB-1'), 'data-dbxn'));
    var sh = sheet(m);
    dung('mở bảng', !!sh);
    var s = chu(sh);
    ['Xác nhận đặt bàn', 'Nguyễn Minh Anh', '0909 123 456', '18:30', '4 khách (1 trẻ em)', 'District 1', 'Bàn sofa thấp',
      'Lời nhắn gửi khách (không bắt buộc)', 'Gửi email xác nhận tới minhanh@gmail.com', 'nhóm Zalo Bán hàng'].forEach(function (x) {
      dung('bảng có ' + x, s.indexOf(x) >= 0);
    });
    var sw = sh.querySelectorAll('#dbGuiMail')[0];
    bang('công tắc bật sẵn', sw.getAttribute('aria-checked'), 'true');
    var ok = sh.querySelectorAll('[data-dbok]')[0];
    bang('nút chính', chu(ok), 'Xác nhận và gửi email');
    bam(m, sw);
    bang('tắt email', [sw.getAttribute('aria-checked'), ok.textContent], ['false', 'Xác nhận, không gửi email']);
    bam(m, sw);
    sh.querySelectorAll('#dbLoiNhan')[0].value = '  Tiệm chuẩn bị nến  ';
    bam(m, ok);
    await choDen(function () { return goiTen(m, 'ds_dat_ban').length === 2; });
    bang('gọi xác nhận', goiTen(m, 'xac_nhan').map(function (x) { return x.ts; }),
      [{ name: 'DB-1', loi_nhan: 'Tiệm chuẩn bị nến', gui_email: 1 }]);
    dung('báo xong kèm trạng thái email', (m.toast[0] || '').indexOf('Đã xác nhận bàn của Nguyễn Minh Anh. đã gửi email') === 0);
    dung('đóng bảng', sheet(m) === null);
  });

  await ca('Xác nhận khách không để email: công tắc tắt và khoá, nhắc gọi khách, gửi gui_email 0', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, nutTrong(the(m, 'DB-2'), 'data-dbxn'));
    var sh = sheet(m), sw = sh.querySelectorAll('#dbGuiMail')[0];
    bang('tắt, khoá', [sw.getAttribute('aria-checked'), sw.hasAttribute('disabled')], ['false', true]);
    bam(m, sw);
    bang('bấm công tắc khoá không đổi', sw.getAttribute('aria-checked'), 'false');
    dung('nhắc gọi khách', chu(sh).indexOf('Khách không để email') >= 0 && chu(sh).indexOf('nhớ gọi báo khách') >= 0);
    bang('nút chính', chu(sh.querySelectorAll('[data-dbok]')[0]), 'Xác nhận');
    bam(m, sh.querySelectorAll('[data-dbok]')[0]);
    await choDen(function () { return goiTen(m, 'xac_nhan').length; });
    bang('không gửi email', goiTen(m, 'xac_nhan')[0].ts.gui_email, 0);
  });

  await ca('Huỷ: thiếu lý do thì không gọi máy chủ; bấm chip mẫu là điền lý do; gửi đúng lý do và email', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, nutTrong(the(m, 'DB-1'), 'data-dbhuy'));
    var sh = sheet(m);
    dung('nói rõ khách sẽ đọc lý do', chu(sh).indexOf('Lý do (bắt buộc, khách sẽ đọc câu này)') >= 0);
    bang('bốn chip mẫu', sh.querySelectorAll('[data-dbly]').map(chu), LY_DO);
    bam(m, sh.querySelectorAll('[data-dbok]')[0]);
    await tick();
    bang('không gọi huỷ', goiTen(m, 'huy').length, 0);
    dung('nhắc ghi lý do', (m.toast[0] || '').indexOf('Ghi lý do huỷ') === 0);
    var chip = sh.querySelectorAll('[data-dbly]')[0];
    bam(m, chip);
    bang('điền lý do', sh.querySelectorAll('#dbLyDo')[0].value, 'Hết chỗ khung giờ này');
    bang('chip sáng', chip.style.background, '#4338ca');
    bam(m, sh.querySelectorAll('[data-dbok]')[0]);
    await choDen(function () { return goiTen(m, 'huy').length; });
    bang('gọi huỷ', goiTen(m, 'huy')[0].ts, { name: 'DB-1', ly_do: 'Hết chỗ khung giờ này', gui_email: 1 });
  });

  await ca('Khách đã đến: hỏi xác nhận rồi gọi đúng phiếu, không có email', async function () {
    var m = await mo(QLCH, null, 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, nutTrong(the(m, 'DB-3'), 'data-dbden'));
    await choDen(function () { return goiTen(m, 'da_den').length; });
    dung('hỏi đúng khách, nói không gửi gì: ' + m.hoi[0], m.hoi[0].indexOf('Khách đã đến?|Lê Thu · 3 khách · 16:00') === 0 && m.hoi[0].indexOf('không gửi email') >= 0);
    bang('gọi da_den', goiTen(m, 'da_den')[0].ts, { name: 'DB-3' });
  });

  await ca('máy chủ từ chối: báo đúng câu, bảng vẫn mở, bấm lại được', async function () {
    var m = await mo(QLCH, 'Đã quá giờ hẹn của đặt bàn này', 'dbKhoang = "7_ngay"; dbTt = ""; dbTim = "";');
    bam(m, nutTrong(the(m, 'DB-1'), 'data-dbxn'));
    var sh = sheet(m), ok = sh.querySelectorAll('[data-dbok]')[0];
    bam(m, ok);
    await choDen(function () { return m.toast.length; });
    await tick();
    dung('báo câu máy chủ', m.toast[0].indexOf('Đã quá giờ hẹn') === 0);
    dung('bảng còn, nút mở lại', sheet(m) === sh && !ok.disabled);
    bang('không tải lại danh sách', goiTen(m, 'ds_dat_ban').length, 1);
  });

  await ca('thu ngân không có quyền: không hỏi máy chủ, nói rõ ai xem được', async function () {
    var m = await mo(QUAY);
    bang('không gọi', m.goi.length, 0);
    dung('câu khoá', chu(m.khung).indexOf('Chỉ quản lý cửa hàng và Sales xem được đặt bàn.') >= 0);
    dung('quản lý có quyền', dungMoi(QLCH).g.coQuyenDatBan() && dungMoi(['Sales User']).g.coQuyenDatBan());
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
