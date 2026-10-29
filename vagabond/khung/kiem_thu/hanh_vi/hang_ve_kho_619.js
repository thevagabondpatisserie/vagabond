/* Ca kiểm HÀNH VI v619: tin Zalo mở thẳng đúng phiếu trên màn "Hàng chuyển về kho tôi".
 *
 * Anh Việt 28/10/2026: link trong thông báo Zalo phải là link app. Tin "Đã chuyển
 * hàng giữa kho" nay mở /hang-chuyen-ve-kho-toi?mo=PDC-2026-00602. Ca nạp THẬT
 * hvkTuDiaChi và scrHangVeKho của 03-kho-chung-tu.js vào DOM giả, chạy đúng như lúc
 * app khởi động từ link đó: đọc địa chỉ, mở màn, máy chủ giả trả danh sách phiếu.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/hang_ve_kho_619.js
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
var NEN = doc('00-nen.js'), KHO = doc('03-kho-chung-tu.js');

/* Đoạn khởi động THẬT của tệp: từ "var HVK" tới hết khối try đọc địa chỉ. */
function doanKhoiDong(src) {
  var dau = src.indexOf('var HVK = {');
  var cuoi = src.indexOf('} catch (eHvk) { }', dau);
  if (dau < 0 || cuoi < 0) throw new Error('Khong thay doan khoi dong HVK');
  return src.slice(dau, cuoi + '} catch (eHvk) { }'.length);
}

var dat = 0, hong = 0;
function la(nhan, duoc, mong) {
  var a = JSON.stringify(duoc), b = JSON.stringify(mong);
  if (a === b) { dat++; console.log('  DAT   ' + nhan); }
  else { hong++; console.log('  HONG  ' + nhan + '\n        duoc ' + a + '\n        mong ' + b); }
}

var DS = [
  { ma: 'PDC-2026-00601', kho_xuat: 'Baker - Thành phẩm', kho_nhan: 'Kho D1', ngay: '2026-10-28', gio: '19:05', nguoi_ten: 'Kiên',
    so_dong: 6, tong_sl: 20, hang: [{ ten: 'Croissant Loaf', ma: 'TP-1', sl: 4, dvt: 'Món' }] },
  { ma: 'PDC-2026-00602', kho_xuat: 'Baker - Thành phẩm', kho_nhan: 'Kho D1', ngay: '2026-10-28', gio: '19:06', nguoi_ten: 'Kiên',
    so_dong: 1, tong_sl: 5, hang: [{ ten: 'Mini Foccacia Thảo mộc Địa Trung Hải', ma: 'TP-2', sl: 5, dvt: 'Món' }] },
];

function moApp(diaChi) {
  var u = new URL('https://app.thevagabondpatisserie.com' + diaChi);
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], cuon = [];
  dg.ElementGia.prototype.scrollIntoView = function () { cuon.push(this.getAttribute('data-hvm')); };
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, URLSearchParams: URLSearchParams,
    location: { search: u.search, pathname: u.pathname },
    frame: function (t, html) { khung.innerHTML = html; that._t = t; return khung; },
    go: function (fn) { return fn(); },
    vgbCss: function () { },
    dmy: function (d) { return String(d || '').split('-').reverse().join('/'); },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      return Promise.resolve({ co_kho: 1, kho: ['Kho D1'], ds: JSON.parse(JSON.stringify(DS)) });
    },
  };
  that.window = that;
  var src = ['h', 'money'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
    doanKhoiDong(KHO) + '\n' + layHam(KHO, 'scrHangVeKho') + '\nthis.HVK = HVK;';
  vm.runInNewContext(src, that, { filename: '03-kho-chung-tu.js' });
  return { g: that, khung: khung, goi: goi, cuon: cuon };
}

(async function () {
  console.log('v619 hành vi: tin Zalo mở thẳng phiếu trên màn Hàng chuyển về kho tôi');

  // Đúng link trong tin đã đổi: app khởi động ở địa chỉ này rồi mở màn.
  var a = moApp('/hang-chuyen-ve-kho-toi?mo=PDC-2026-00602');
  await a.g.scrHangVeKho();
  la('đọc mã phiếu từ địa chỉ', a.g.HVK.mo, 'PDC-2026-00602');
  la('mở rộng ra 30 ngày để phiếu cũ vẫn thấy', a.goi[0].ts, { so_ngay: 30 });
  var mo = a.khung.querySelectorAll('[data-hvx]').map(function (n) { return n.getAttribute('data-hvx'); });
  la('đúng phiếu trong tin đang mở, có nút xác nhận', mo, ['PDC-2026-00602']);
  la('thấy món của phiếu', a.khung.innerHTML.indexOf('Mini Foccacia') >= 0, true);
  la('phiếu kia vẫn gập', a.khung.innerHTML.indexOf('Croissant Loaf') >= 0, false);
  la('cuộn tới đúng phiếu', a.cuon, ['PDC-2026-00602']);

  // Mở app bình thường: không có tham số thì như cũ.
  var b = moApp('/hang-chuyen-ve-kho-toi');
  await b.g.scrHangVeKho();
  la('không có mã thì không mở phiếu nào, 14 ngày', [b.g.HVK.mo, b.goi[0].ts.so_ngay, b.khung.querySelectorAll('[data-hvx]').length], ['', 14, 0]);

  // Tham số ?mo ở màn khác không được làm gì màn này.
  var c = moApp('/doanh-so?mo=PDC-2026-00602');
  la('màn khác không đọc tham số', c.g.HVK.mo, '');

  // Mã lạ (chèn mã HTML, quá dài) bị bỏ.
  ['<img src=x>', 'PDC"]', 'x'.repeat(60), ''].forEach(function (x) {
    var d = moApp('/hang-chuyen-ve-kho-toi?mo=' + encodeURIComponent(x));
    la('bỏ mã lạ ' + JSON.stringify(x.slice(0, 12)), d.g.HVK.mo, '');
  });
  var e = moApp('/hang-chuyen-ve-kho-toi/?mo=PDC-2026-00602');
  la('địa chỉ có gạch chéo cuối vẫn nhận', e.g.HVK.mo, 'PDC-2026-00602');

  console.log('\n' + dat + ' ca đạt, ' + hong + ' ca hỏng.');
  process.exit(hong ? 1 : 0);
})().catch(function (e) { console.error(e); process.exit(1); });
