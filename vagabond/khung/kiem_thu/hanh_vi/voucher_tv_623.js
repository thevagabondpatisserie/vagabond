/* Bo ca kiem HANH VI v623: voucher danh cho thanh vien.
 *
 * Phan 1 - phieu Chuong trinh khuyen mai tren app (13-khuyen-mai.js THAT nap
 * vao DOM gia): quan ly bam chip Ma dung mot lan, bat Phat vao Vi qua, chon
 * Dip phat va So lan nhan, bam Luu; may chu gia ghi lai dung du lieu gui len.
 *
 * Phan 2 - trang thanh vien (www/thanh-vien.html + thanh-vien.js THAT, khung
 * tv_khung.js): khach mo trang, ho so bao con qua cho (vi_cho) thi trang tu
 * xin cap ma, mo Vi qua va bao; khach khong phai bam.
 *
 * Khong goi ham noi bo nao ngoai dung chuoi thao tac cua nguoi dung.
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/voucher_tv_623.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');
var K = require('./tv_khung.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');

var ket = { dat: 0, hong: 0, loi: [] };
function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n         ') : String(e))); }
}
async function nghi() { for (var i = 0; i < 12; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }
function chuOf(el) { return el ? String(el.textContent || '') : ''; }

/* ---------------- phan 1: phieu chuong trinh tren app ---------------- */

/* posChipNut that nam o 09-tinh-tien-quay.js (tep lon, keo ca man quay). Cat
   dung ham do ra nap, khong viet ban gia. */
function hamPosChip() {
  var s = fs.readFileSync(path.join(BEP, '09-tinh-tien-quay.js'), 'utf8');
  var i = s.indexOf('function posChipNut(');
  var j = s.indexOf('\n}\n', i);
  return s.slice(i, j + 2);
}

function khoiApp(kmCo) {
  var goi = [], tin = [];
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, parseFloat: parseFloat, parseInt: parseInt,
    setTimeout: function () { return 1; }, clearTimeout: function () {},
    document: domGia.taiLieuGia(), __goi: goi, __tin: tin,
    __api: function (m, a) { goi.push({ m: m, a: a }); return Promise.resolve(m === 'vagabond.khuyen_mai.xem_ctkm' ? { km: kmCo } : {}); } };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var CFGBH = null; /* 08-doanh-so-sales.js: cấu hình bán hàng chưa nạp */',
    'function toast(s) { __tin.push(s); } function go() {} function scrKhuyenMai() {}',
    'function h(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }',
    'function money(x) { return String(x); } function num(x) { return String(x); }',
    'function api(m, a) { return __api(m, a); }',
    hamPosChip(),
  ].join('\n'), g);
  vm.runInContext(fs.readFileSync(path.join(BEP, '13-khuyen-mai.js'), 'utf8'), g);
  return g;
}
function tam(g) { var ds = g.document.body.children; return ds[ds.length - 1]; }
function chip(g, sel) { var o = tam(g).querySelector(sel); if (!o) throw new Error('khong co chip ' + sel); return o; }
async function bamChip(g, sel) { chip(g, sel).onclick({}); await nghi(); }
function coChu(g, s) { return chuOf(tam(g)).indexOf(s) >= 0; }
function dangChon(g, sel) { return chip(g, sel).getAttribute('aria-pressed') === 'true'; }
function duLieuLuu(g) {
  var l = g.__goi.filter(function (x) { return x.m === 'vagabond.khuyen_mai.luu_ctkm'; });
  return l.length ? JSON.parse(l[l.length - 1].a.du_lieu) : null;
}

/* ---------------- chay ---------------- */

(async function () {
  await ca('app: chương trình mới chưa chọn Mã dùng một lần thì không có mục Ví quà; chọn rồi mới hiện, mặc định tắt và nói rõ bật thì sao', async function () {
    var g = khoiApp(null);
    await g.kmSheetCtkm('');
    dung('chưa có mục Ví quà', !coChu(g, 'VÍ QUÀ THÀNH VIÊN'));
    await bamChip(g, '[data-kmcm="Ma co dinh"]');
    dung('mã cố định: vẫn không có', !coChu(g, 'VÍ QUÀ THÀNH VIÊN'));
    await bamChip(g, '[data-kmcm="Ma dung mot lan"]');
    dung('mã dùng một lần: có mục', coChu(g, 'VÍ QUÀ THÀNH VIÊN'));
    dung('mặc định tắt', !dangChon(g, '[data-kmvi]') && coChu(g, 'Không phát vào Ví quà'));
    dung('câu giải thích khi tắt', coChu(g, 'tự thấy mã trong Ví quà khi mở trang thành viên'));
    dung('chưa bật thì chưa hỏi dịp phát', !coChu(g, 'DỊP PHÁT'));
  });

  await ca('app: bật Ví quà, chọn Tháng sinh nhật và Mỗi năm một lần rồi Lưu gửi đúng giá trị lưu; Tháng sinh nhật không hỏi số ngày', async function () {
    var g = khoiApp(null);
    await g.kmSheetCtkm('');
    tam(g).querySelector('#kmTen').value = 'Quà sinh nhật thành viên';
    await bamChip(g, '[data-kmcm="Ma dung mot lan"]');
    await bamChip(g, '[data-kmvi]');
    dung('đã bật', dangChon(g, '[data-kmvi]') && coChu(g, 'Đang phát vào Ví quà'));
    dung('mặc định Mọi lúc, Một lần', dangChon(g, '[data-kmvidip="Moi luc"]') && dangChon(g, '[data-kmvisl="Mot lan"]'));
    bang('ô số ngày mặc định 30', tam(g).querySelector('#kmViHan').value, '30');
    dung('nói ai nhận', coChu(g, 'theo mục Đối tượng khách ở trên'));
    await bamChip(g, '[data-kmvidip="Thang sinh nhat"]');
    dung('giải thích tháng sinh nhật', coChu(g, 'mã dùng tới hết tháng đó'));
    dung('không hỏi số ngày', !tam(g).querySelector('#kmViHan'));
    await bamChip(g, '[data-kmvisl="Moi nam mot lan"]');
    dung('giải thích mỗi năm', coChu(g, 'Sang năm mới khách được nhận lại'));
    dung('tên vẫn giữ sau khi bấm chip', tam(g).querySelector('#kmTen').value === 'Quà sinh nhật thành viên');
    tam(g).querySelector('#kmLuu').onclick();
    await nghi();
    var d = duLieuLuu(g);
    bang('gửi lên', [d.ten, d.cach_ma, d.vi_phat, d.vi_dip, d.vi_so_lan], ['Quà sinh nhật thành viên', 'Ma dung mot lan', 1, 'Thang sinh nhat', 'Moi nam mot lan']);
  });

  await ca('app: Mọi lúc thì gõ số ngày dùng được; đổi sang mã cố định thì Ví quà tự tắt (máy chủ chặn tổ hợp đó)', async function () {
    var g = khoiApp(null);
    await g.kmSheetCtkm('');
    tam(g).querySelector('#kmTen').value = 'Voucher VIP';
    await bamChip(g, '[data-kmcm="Ma dung mot lan"]');
    await bamChip(g, '[data-kmvi]');
    tam(g).querySelector('#kmViHan').value = '14';
    tam(g).querySelector('#kmLuu').onclick();
    await nghi();
    bang('gửi số ngày', [duLieuLuu(g).vi_phat, duLieuLuu(g).vi_han_ngay], [1, 14]);
    var g2 = khoiApp(null);
    await g2.kmSheetCtkm('');
    tam(g2).querySelector('#kmTen').value = 'Voucher VIP';
    await bamChip(g2, '[data-kmcm="Ma dung mot lan"]');
    await bamChip(g2, '[data-kmvi]');
    await bamChip(g2, '[data-kmcm="Ma co dinh"]');
    tam(g2).querySelector('#kmMaCd').value = 'VIP10';
    tam(g2).querySelector('#kmLuu').onclick();
    await nghi();
    bang('tắt Ví quà khi đổi cách phát mã', [duLieuLuu(g2).cach_ma, duLieuLuu(g2).vi_phat], ['Ma co dinh', 0]);
  });

  await ca('app: mở lại chương trình đã cài hiện đúng lựa chọn đã lưu; danh sách có chip Ví quà', async function () {
    var g = khoiApp({ name: 'KMSN01', ten: 'Quà sinh nhật', cach_thuc: 'Giam gia mon', kieu_giam: 'Phan tram', gia_tri: 100,
      pham_vi: 'Nhom mon chi dinh', nhom_mon: 'Bánh lạnh', doi_tuong: 'Theo hang khach', hang_khach: 'VOYAGER', cach_ma: 'Ma dung mot lan',
      vi_phat: 1, vi_dip: 'Thang sinh nhat', vi_so_lan: 'Moi nam mot lan', vi_han_ngay: 30, bat: 1, dong_mon: [], dong_bac: [] });
    await g.kmSheetCtkm('KMSN01');
    dung('bật', dangChon(g, '[data-kmvi]'));
    dung('đúng dịp và số lần', dangChon(g, '[data-kmvidip="Thang sinh nhat"]') && dangChon(g, '[data-kmvisl="Moi nam mot lan"]'));
    var html = g.kmHtmlCt([{ name: 'KMSN01', ten: 'Quà sinh nhật', cach_thuc: 'Giam gia mon', cach_ma: 'Ma dung mot lan', vi_phat: 1, vi_dip: 'Thang sinh nhat', bat: 1, kieu_giam: 'Phan tram', gia_tri: 100 }]);
    dung('chip danh sách', html.indexOf('Ví quà, tháng sinh nhật') >= 0);
    dung('chương trình thường không có chip', g.kmHtmlCt([{ name: 'KMA', ten: 'A', cach_thuc: 'Giam tong hoa don', cach_ma: 'Ma dung mot lan', bat: 1, kieu_giam: 'So tien', gia_tri: 1 }]).indexOf('Ví quà') < 0);
  });

  /* ---------------- phan 2: trang thanh vien ---------------- */

  var SS = { otp: 1, qua: { mo: 1, uu_dai: 'Giảm 20.000đ' } };
  function hoSo(them) {
    var d = {
      ok: 1, ten: 'Nguyễn Lan Anh', sdt: '0909123412', diem: 184200, co_ho_so: true, don: [], don_loi: false, don_chua_mo: false,
      hang: { ten_hang: 'VOYAGER', anh: '', mo_ta: '', giam_gia: 0, tich_diem: 3 },
      ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: 14, thang: 11, nam: '' }, email: '', so_thich: [], dong_y_zalo: 1, anh_mau: '' },
      anh: '', muc: { du: 4, tong: 5, thieu_qua: [] }, vi: [],
      qua: { mo: 1, uu_dai: 'Giảm 20.000đ', han: '', so_ngay: 7, da_nhan: 1 },
      tien_do: null, ma_tv: 'KL0412', tu_nam: '2024', vi_cho: 0,
    };
    Object.keys(them || {}).forEach(function (k) { d[k] = them[k]; });
    return d;
  }
  var MA_SN = { ma: 'VT0001', ten: 'Quà sinh nhật thành viên', uu_dai: 'Giảm 100%', dieu_kien: 'Dùng 1 lần cho 1 hoá đơn', han: '30/11/2026', trang_thai: 'dung_duoc', ngay_dung: '' };

  await ca('trang thành viên: tới tháng sinh nhật, khách mở trang là mã tự hiện trong Ví quà, không phải bấm; trang báo và mở Ví quà', async function () {
    var cap = false;
    var t = await K.dungTrang({
      san_sang: SS,
      toi: function () { return cap ? hoSo({ vi: [MA_SN] }) : hoSo({ vi_cho: 1 }); },
      cap_vi_tv: function () { cap = true; return { ok: 1, moi: [{ ma: 'VT0001', ten: 'Quà sinh nhật thành viên', uu_dai: 'Giảm 100%', han: '30/11/2026' }] }; },
    });
    bang('xin cấp đúng một lần, gửi POST có CSRF', t.cac('cap_vi_tv').map(function (x) { return [x.a !== null, x.csrf]; }), [[true, 'csrf-gia']]);
    bang('đọc lại hồ sơ sau khi cấp', t.cac('toi').length, 2);
    dung('mở Ví quà', !K.an(t.tim('tab-vi')));
    dung('mã có trong ví', t.tim('vi').querySelectorAll('[data-vc]').map(function (v) { return v.getAttribute('data-vc'); }).indexOf('VT0001') >= 0);
    dung('báo khách', chuOf(t.tim('trang-thai')).indexOf('vừa nhận 1 quà mới trong Ví quà') >= 0);
  });

  await ca('trang thành viên: không có quà chờ thì không xin cấp; máy chủ không cấp thêm thì không báo, không đọc lại', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSo() });
    bang('không gọi', t.cac('cap_vi_tv').length, 0);
    dung('ở trang chính', !K.an(t.tim('tab-chinh')));
    var t2 = await K.dungTrang({ san_sang: SS, toi: hoSo({ vi_cho: 1 }), cap_vi_tv: { ok: 1, moi: [] } });
    bang('gọi một lần, không đọc lại', [t2.cac('cap_vi_tv').length, t2.cac('toi').length], [1, 1]);
    dung('không báo gì', chuOf(t2.tim('trang-thai')) === '' && !K.an(t2.tim('tab-chinh')));
  });

  await ca('trang thành viên: xin cấp lỗi mạng thì hồ sơ vẫn hiện bình thường', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSo({ vi_cho: 2 }), cap_vi_tv: function () { throw new Error('mat mang'); } });
    dung('hồ sơ hiện', !K.an(t.tim('ho-so')) && chuOf(t.tim('ten')) === 'Lan Anh');
    dung('không báo lỗi đỏ', !t.tim('trang-thai').classList.contains('loi'));
  });

  await ca('trang quà tại quầy (?qua=TCV): không xin cấp voucher thành viên, giữ đúng luồng quà chào mừng', async function () {
    var t = await K.dungTrang({ san_sang: SS, toi: hoSo({ vi_cho: 1 }) }, '?qua=TCV');
    bang('không gọi', t.cac('cap_vi_tv').length, 0);
  });

  await ca('trang thành viên: khai ngày sinh đúng tháng sinh nhật rồi Lưu là nhận quà sinh nhật ngay, câu báo nói đúng quà mới', async function () {
    var da = { luu: false, cap: false };
    var t = await K.dungTrang({
      san_sang: SS,
      toi: function () { return da.cap ? hoSo({ vi: [MA_SN] }) : da.luu ? hoSo({ vi_cho: 1 }) : hoSo({ ho_so: { ten: 'Lan Anh', sinh_nhat: { ngay: '', thang: '', nam: '' }, email: '', so_thich: [], dong_y_zalo: 1, anh_mau: '' } }); },
      luu_ho_so: function () { da.luu = true; return { ok: 1 }; },
      cap_vi_tv: function () { da.cap = true; return { ok: 1, moi: [{ ma: 'VT0001' }] }; },
    });
    bang('mở trang chưa có quà chờ: chưa gọi', t.cac('cap_vi_tv').length, 0);
    t.tl.querySelector('[data-tab="ho-so"]').onclick && t.tl.querySelector('[data-tab="ho-so"]').onclick({ target: t.tl.querySelector('[data-tab="ho-so"]') });
    var f = t.tim('form-ho-so');
    f.querySelector('#o-ngay').value = '14';
    f.querySelector('#o-thang').value = '11';
    f.onsubmit({ preventDefault: function () {} });
    await K.nghi(6);
    bang('lưu rồi xin cấp một lần', [t.cac('luu_ho_so').length, t.cac('cap_vi_tv').length], [1, 1]);
    dung('mở Ví quà', !K.an(t.tim('tab-vi')));
    dung('báo quà mới, không phải chỉ Đã lưu', chuOf(t.tim('trang-thai')).indexOf('vừa nhận 1 quà mới') >= 0);
  });

  console.log('Bo ca kiem HANH VI v623 (voucher danh cho thanh vien: phieu chuong trinh tren app, trang thanh vien)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
