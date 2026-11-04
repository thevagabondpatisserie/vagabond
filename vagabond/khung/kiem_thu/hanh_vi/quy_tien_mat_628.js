/* Ca kiểm HÀNH VI v628: màn Quỹ tiền mặt công ty (anh Việt duyệt ảnh mẫu 02/11/2026).
 *
 * Nạp THẬT 61-tai-chinh.js và 62-quy-tien-mat.js vào DOM giả. Máy chủ giả chỉ trả dữ
 * liệu màn và ghi lại lời gọi; phép tính quỹ chạy thật ở thu_quy_tien_mat_628.py.
 * Mỗi ca gõ, bấm đúng chuỗi thao tác của người dùng.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/quy_tien_mat_628.js
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
var HAM = ['h', 'money', 'today'].map(function (t) { return layHam(NEN, t); }).concat([layHam(KHO, 'errMsg')]).join('\n');

function manQuy(o) {
  o = o || {};
  var chua = !!o.chua_chot;
  return {
    so_du: chua ? null : 45200000, moc: chua ? null : { ngay_chot: '2026-10-31', so_du: 40000000 },
    lan_kiem: chua ? null : { name: 'PQ-1', luc: '2026-10-31 16:30:00', lech: -150000, ten_nguoi: 'Dung', trang_thai: 'Đã ghi' },
    cho_duyet: o.cho || [], ba_lan: [{ ngay: '2026-10-31', lech: -150000 }],
    lich_su: [
      { luc: '2026-11-02 09:12', loai: 'nop_quy', ma: 'NQ-1', tien: 8350000, ten: 'Biên nhận nộp tiền mặt', phu: 'Trần Cao Vân · Dung ký nhận' },
      { luc: '2026-11-01 10:00', loai: 'so_cai', ma: 'PQ-2', tien: -20000000, ten: 'Nộp vào MB Bank ···1568', phu: 'Dung', chip: 'Đã khớp SePay', huy: 'nop' },
      { luc: '2026-10-31 16:30', loai: 'so_cai', ma: 'PQ-1', tien: -150000, ten: 'Kiểm quỹ: thiếu', phu: 'Lý do: Chưa rõ', huy: 'kiem' },
    ],
    tai_khoan_nh: [{ ma: 'MB-CTY', ten: 'MB Bank ···1568', tk: '1121 - MB' }, { ma: 'SHB', ten: 'Shinhan ···9585', tk: '1121 - SHB' }],
    menh_gia: [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500],
    ly_do: [{ ma: 'chi_chua_nhap', ten: 'Chi chưa nhập app' }, { ma: 'thu_chua_nhap', ten: 'Thu chưa nhập app' },
      { ma: 'dem_sai', ten: 'Lần trước đếm sai' }, { ma: 'chua_ro', ten: 'Chưa rõ' }],
    nguong: 2000000, duoc_lam: o.lam === undefined ? 1 : o.lam, duoc_duyet: o.duyet || 0, toi: o.toi || 'dung@x',
    tk: { tk_quy: { ma: '', ten: '', goi_y: '1111 - Tiền mặt', ten_goi_y: '1111 - Tiền mặt' },
      tk_thieu: { ma: '', ten: '', goi_y: '', ten_goi_y: '' }, tk_thua: { ma: '3381', ten: '3381 - Tài sản thừa', goi_y: '', ten_goi_y: '' } },
    hom_nay: '2026-11-02',
  };
}

function dungMoi(duLieu, anh) {
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goi = [], toastDs = [], dieuHuong = [], hoi = [], vgbGoDs = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt,
    S: { roles: ['Accounts Manager'], stack: [], quyenNen: { tai_chinh: true } },
    hasRole: function () { return false; },
    frame: function (t, html) { khung.innerHTML = html; khung.onclick = null; khung.oninput = null; that._t = t; that.VGB_TD = t; return khung; },
    go: function (fn) { dieuHuong.push(fn.name || 'anDanh'); return fn(); },
    back: function () { dieuHuong.push('back'); },
    vgbGo: function (k) { vgbGoDs.push(k); },
    toast: function (m) { toastDs.push(m); },
    hoiCo: function (t, nd) { hoi.push(t); return Promise.resolve(true); },
    hoiChu: function () { return Promise.resolve('Đếm lại tờ 500.000'); },
    sheet: function () {},
    tdkKhoi: function (id) { return '<div data-tdk="' + id + '"></div>'; },
    tdkNoi: function () {}, tdkXoaHet: function () {},
    tdkDs: function (id) { return (anh || {})[id] || []; },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      if (duong === 'vagabond.quy_tien_mat.man_quy') return Promise.resolve(JSON.parse(JSON.stringify(duLieu)));
      if (duong === 'vagabond.quy_tien_mat.kiem_quy') return Promise.resolve({ ok: 1, trang_thai: 'Chờ duyệt', lech: -2500000 });
      if (duong === 'vagabond.quy_tien_mat.chot_dau') return Promise.resolve({ ok: 1, name: 'MOC-1', ngay_chot: '2026-11-01', so_du: 40100000, co_phat_sinh: 0 });
      if (duong === 'vagabond.quy_tien_mat.nop_ngan_hang') return Promise.resolve({ ok: 1, trang_thai: 'Chờ tiền về' });
      return Promise.resolve({ ok: 1 });
    },
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(doc('61-tai-chinh.js'), that, { filename: '61-tai-chinh.js' });
  vm.runInNewContext(doc('62-quy-tien-mat.js'), that, { filename: '62-quy-tien-mat.js' });
  return { g: that, khung: khung, goi: goi, toast: toastDs, dieuHuong: dieuHuong, hoi: hoi, vgbGo: vgbGoDs };
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
function mot(m, c) { return m.khung.querySelectorAll(c)[0]; }
function ds(m, c) { return m.khung.querySelectorAll(c); }
function go_(m, mg, v) { var o = ds(m, '[data-qtmmg]').filter(function (x) { return x.getAttribute('data-qtmmg') === String(mg); })[0]; o.value = String(v); m.khung.oninput({ target: o }); }
function goiDuong(m) { return m.goi.map(function (x) { return x.duong; }); }

(async function () {
  console.log('v628 Quỹ tiền mặt công ty: màn chính, kiểm quỹ, nộp ngân hàng, duyệt');

  await ca('màn chính: số quỹ, chip lần kiểm, hai nút cho kế toán, không có ô gõ số dư', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    dung('số quỹ', chu(mot(m, '[data-qtmso]')).indexOf('45.200.000') >= 0 || chu(mot(m, '[data-qtmso]')).indexOf('45,200,000') >= 0);
    dung('chip lần kiểm', chu(m.khung).indexOf('Kiểm quỹ 31/10 16:30 · Dung · lệch -150') >= 0);
    dung('nút Kiểm quỹ và Nộp', !!mot(m, '[data-qtmkiem]') && !!mot(m, '[data-qtmnop]'));
    dung('lịch sử có biên nhận và nộp ngân hàng', chu(m.khung).indexOf('Biên nhận nộp tiền mặt') >= 0 && chu(m.khung).indexOf('Đã khớp SePay') >= 0);
    bang('không ô nào gõ số dư', ds(m, 'input').length, 0);
    dung('tài khoản thiếu chưa có thì đỏ', chu(m.khung).indexOf('Chưa có tài khoản') >= 0);
  });

  await ca('người chỉ được xem: không có nút Kiểm quỹ, Nộp, không có mục chọn tài khoản', async function () {
    var m = dungMoi(manQuy({ lam: 0 }));
    await m.g.scrQuyTm(); await tick();
    dung('không nút', !mot(m, '[data-qtmkiem]') && !mot(m, '[data-qtmnop]') && !mot(m, '[data-qtmtk]'));
  });

  await ca('kiểm quỹ: gõ số tờ ra số đếm và lệch; khớp thì không hỏi lý do; lệch thì bắt lý do trước khi gửi', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmkiem]').onclick(); await tick();
    bang('mở màn kiểm', m.g._t, 'Kiểm quỹ');
    go_(m, 500000, 90); go_(m, 200000, 1);
    bang('khớp', mot(m, '[data-qtmlech]').getAttribute('data-qtmlech'), '0');
    bang('khớp thì ẩn lý do', m.g.document.getElementById('qtmLyDoKhoi').style.display, 'none');
    go_(m, 500000, 85);
    bang('lệch -2.500.000', mot(m, '[data-qtmlech]').getAttribute('data-qtmlech'), '-2500000');
    bang('lệch thì hiện lý do', m.g.document.getElementById('qtmLyDoKhoi').style.display, 'block');
    dung('quá 2 triệu: báo chờ Giám đốc duyệt', chu(m.g.document.getElementById('qtmCanhBao')).indexOf('gửi Giám đốc duyệt') >= 0);
    await mot(m, '[data-qtmluu]').onclick(); await tick();
    dung('chưa chọn lý do: không gửi', goiDuong(m).indexOf('vagabond.quy_tien_mat.kiem_quy') < 0);
    dung('báo chọn lý do', m.toast.indexOf('Quỹ lệch: chọn lý do lệch.') >= 0);
    var ly = ds(m, '[data-qtmly]').filter(function (x) { return x.getAttribute('data-qtmly') === 'chi_chua_nhap'; })[0];
    ly.onclick();
    m.g.document.getElementById('qtmGhiChu').value = 'Trả tiền ga';
    await mot(m, '[data-qtmluu]').onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.kiem_quy'; })[0];
    dung('đã gửi', !!g);
    bang('bảng đếm đúng số đã gõ', JSON.parse(g.ts.bang), { '200000': '1', '500000': '85' });
    bang('lý do, ghi chú', [g.ts.ly_do, g.ts.ghi_chu], ['chi_chua_nhap', 'Trả tiền ga']);
    dung('báo chờ duyệt rồi quay lại', m.toast.indexOf('Đã gửi Giám đốc duyệt khoản lệch -2.500.000') >= 0 && m.dieuHuong.indexOf('back') >= 0);
  });

  await ca('kiểm quỹ: chưa gõ số nào thì không gửi; lệch nhỏ báo ghi ngay', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmkiem]').onclick(); await tick();
    await mot(m, '[data-qtmluu]').onclick(); await tick();
    dung('không gửi', goiDuong(m).indexOf('vagabond.quy_tien_mat.kiem_quy') < 0);
    go_(m, 500000, 90); go_(m, 50000, 1);
    dung('lệch +50.000 ghi ngay', chu(m.g.document.getElementById('qtmCanhBao')).indexOf('máy ghi ngay') >= 0);
    go_(m, 500000, 'a9');
    bang('ô số tờ bỏ chữ', ds(m, '[data-qtmmg]')[0].value, '9');
  });

  await ca('Codex #527 vòng 4: quỹ hết tiền, gõ 0 tờ là đã đếm; hỏi lại rồi gửi phiếu thiếu toàn bộ quỹ máy', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmkiem]').onclick(); await tick();
    go_(m, 500000, 0);
    bang('lệch thiếu toàn bộ quỹ máy', mot(m, '[data-qtmlech]').getAttribute('data-qtmlech'), '-45200000');
    ds(m, '[data-qtmly]').filter(function (x) { return x.getAttribute('data-qtmly') === 'chua_ro'; })[0].onclick();
    m.g.document.getElementById('qtmGhiChu').value = 'Két trống khi mở ca';
    await mot(m, '[data-qtmluu]').onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.kiem_quy'; })[0];
    dung('đã gửi lần kiểm quỹ rỗng', !!g);
    bang('bảng đếm gửi đúng số 0 đã gõ', JSON.parse(g.ts.bang), { '500000': '0' });
    dung('hỏi lại trước khi gửi quỹ đếm được 0 đồng', m.hoi.indexOf('Quỹ đếm được 0 đồng') >= 0);
    /* Gõ rồi xoá trắng là CHƯA đếm: vẫn chặn như cũ. */
    var m2 = dungMoi(manQuy());
    await m2.g.scrQuyTm(); await tick();
    mot(m2, '[data-qtmkiem]').onclick(); await tick();
    go_(m2, 500000, 3); go_(m2, 500000, '');
    await mot(m2, '[data-qtmluu]').onclick(); await tick();
    dung('xoá trắng thì không gửi', goiDuong(m2).indexOf('vagabond.quy_tien_mat.kiem_quy') < 0);
    dung('báo gõ số tờ', m2.toast.some(function (t) { return t.indexOf('Gõ số tờ đã đếm được') === 0; }));
  });

  await ca('Codex #527 vòng 6: kế toán huỷ phiếu nộp ghi nhầm ngay từ lịch sử quỹ, ghi lý do rồi máy gọi cửa huỷ; phiếu kiểm quỹ chỉ Giám đốc huỷ', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    var nut = ds(m, '[data-qtmhuy]').map(function (x) { return x.getAttribute('data-qtmhuy'); });
    bang('kế toán thấy nút huỷ phiếu nộp, không thấy nút huỷ phiếu kiểm', nut, ['PQ-2']);
    await mot(m, '[data-qtmhuy]').onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.huy_phieu'; });
    bang('gọi cửa huỷ đúng phiếu, đúng lý do', g.map(function (x) { return [x.ts.name, x.ts.ly_do]; }), [['PQ-2', 'Đếm lại tờ 500.000']]);
    dung('huỷ xong mở lại màn quỹ', m.dieuHuong.indexOf('scrQuyTm') >= 0 && m.toast.some(function (t) { return t.indexOf('Đã huỷ phiếu PQ-2') === 0; }));
    var gd = dungMoi(manQuy({ duyet: 1, lam: 0 }));
    await gd.g.scrQuyTm(); await tick();
    bang('Giám đốc thấy nút huỷ phiếu kiểm', ds(gd, '[data-qtmhuy]').map(function (x) { return x.getAttribute('data-qtmhuy'); }), ['PQ-1']);
  });

  await ca('v635 chị Dung: quỹ chưa chốt thì có nút Chốt số dư đầu ngay trên màn, không còn chỉ sang Cài đặt tài chính; chưa có nút Kiểm quỹ, Nộp', async function () {
    var m = dungMoi(manQuy({ chua_chot: 1 }));
    await m.g.scrQuyTm(); await tick();
    dung('có nút chốt', !!mot(m, '[data-qtmchot]'));
    dung('không còn chỉ sang Cài đặt tài chính', chu(m.khung).indexOf('chốt ở Cài đặt tài chính') < 0);
    dung('chưa có Kiểm quỹ, Nộp', !mot(m, '[data-qtmkiem]') && !mot(m, '[data-qtmnop]'));
    var xem = dungMoi(manQuy({ chua_chot: 1, lam: 0 }));
    await xem.g.scrQuyTm(); await tick();
    dung('người chỉ xem: không nút, có câu nhờ kế toán', !mot(xem, '[data-qtmchot]') && chu(xem.khung).indexOf('Nhờ kế toán hoặc Giám đốc') >= 0);
  });

  await ca('v635 chốt số dư đầu: đếm theo mệnh giá ra tổng, chưa gõ thì không gửi, hỏi lại rồi gửi đúng bảng đếm và ghi chú', async function () {
    var m = dungMoi(manQuy({ chua_chot: 1 }));
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmchot]').onclick(); await tick();
    bang('mở màn chốt', m.g._t, 'Chốt số dư đầu quỹ');
    bang('không ô gõ tay số dư: chỉ ô số tờ và ô ghi chú', ds(m, 'input').length, 11);
    await mot(m, '[data-qtmchotluu]').onclick(); await tick();
    dung('chưa gõ: không gửi', goiDuong(m).indexOf('vagabond.quy_tien_mat.chot_dau') < 0 && m.toast.indexOf('Gõ số tờ đã đếm được. Quỹ trống thì gõ 0.') >= 0);
    go_(m, 500000, 80); go_(m, 50000, 2);
    bang('tổng đếm', mot(m, '[data-qtmdem]').getAttribute('data-qtmdem'), '40100000');
    m.g.document.getElementById('qtmGhiChuChot').value = 'đếm đầu ngày';
    await mot(m, '[data-qtmchotluu]').onclick(); await tick();
    dung('hỏi lại đúng số', m.hoi.length === 1 && (m.hoi[0].indexOf('40.100.000') >= 0 || m.hoi[0].indexOf('40,100,000') >= 0));
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.chot_dau'; });
    bang('gửi một lần, đúng bảng và ghi chú', g.map(function (x) { return [JSON.parse(x.ts.bang), x.ts.ghi_chu]; }),
      [[{ '500000': '80', '50000': '2' }, 'đếm đầu ngày']]);
    dung('báo đã chốt đúng số đếm rồi quay lại', m.toast.some(function (t) { return t.indexOf('Đã chốt quỹ 40') === 0; }) && m.dieuHuong.indexOf('back') >= 0);
  });

  await ca('v635 quỹ trống: gõ 0 tờ vẫn chốt được 0 đồng', async function () {
    var m = dungMoi(manQuy({ chua_chot: 1 }));
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmchot]').onclick(); await tick();
    go_(m, 500000, 0);
    await mot(m, '[data-qtmchotluu]').onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.chot_dau'; })[0];
    bang('gửi bảng 0', JSON.parse(g.ts.bang), { '500000': '0' });
  });

  await ca('nộp ngân hàng: thiếu ảnh giấy nộp thì không gửi; đủ thì hỏi lại rồi gửi đúng tài khoản đã chọn', async function () {
    var m = dungMoi(manQuy());
    await m.g.scrQuyTm(); await tick();
    mot(m, '[data-qtmnop]').onclick(); await tick();
    bang('mở màn nộp', m.g._t, 'Nộp tiền mặt vào ngân hàng');
    m.g.document.getElementById('qtmSoTien').value = '20.000.000';
    await mot(m, '[data-qtmnopluu]').onclick(); await tick();
    dung('chưa ảnh: không gửi', goiDuong(m).indexOf('vagabond.quy_tien_mat.nop_ngan_hang') < 0 && m.toast.indexOf('Chụp ảnh giấy nộp tiền của ngân hàng.') >= 0);
    var m2 = dungMoi(manQuy(), { qtmGiayNop: ['/private/files/giay.jpg'] });
    await m2.g.scrQuyTm(); await tick();
    mot(m2, '[data-qtmnop]').onclick(); await tick();
    m2.g.document.getElementById('qtmSoTien').value = '20.000.000';
    ds(m2, '[data-qtmnh]').filter(function (x) { return x.getAttribute('data-qtmnh') === 'SHB'; })[0].onclick();
    await mot(m2, '[data-qtmnopluu]').onclick(); await tick();
    var g = m2.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.nop_ngan_hang'; })[0];
    dung('hỏi lại trước khi trừ quỹ', m2.hoi.length === 1 && (m2.hoi[0].indexOf('20.000.000') >= 0 || m2.hoi[0].indexOf('20,000,000') >= 0));
    bang('gửi đúng', [g.ts.so_tien, g.ts.bank_account, g.ts.ngay, JSON.parse(g.ts.anh)], ['20.000.000', 'SHB', '2026-11-02', ['/private/files/giay.jpg']]);
  });

  await ca('duyệt: Giám đốc thấy nút Duyệt, Trả lại; người tự kiểm không tự duyệt; trả lại gửi lý do', async function () {
    var cho = [{ name: 'PQ-9', luc: '2026-11-02 16:30:00', so_may: 45200000, so_dem: 42700000, lech: -2500000, ly_do: 'chi_chua_nhap',
      ly_do_ten: 'Chi chưa nhập app', ghi_chu: 'Trả tiền ga', anh: [], nguoi: 'dung@x', ten_nguoi: 'Dung' }];
    var m = dungMoi(manQuy({ cho: cho, duyet: 1, toi: 'viet@x' }));
    await m.g.scrQuyTm(); await tick();
    dung('có thẻ chờ duyệt', chu(mot(m, '[data-qtmcho]')).indexOf('-2.500.000') >= 0 || chu(mot(m, '[data-qtmcho]')).indexOf('-2,500,000') >= 0);
    await mot(m, '[data-qtmtra]').onclick(); await tick();
    var g = m.goi.filter(function (x) { return x.duong === 'vagabond.quy_tien_mat.duyet_kiem_quy'; })[0];
    bang('trả lại kèm lý do', [g.ts.name, g.ts.dong_y, g.ts.ly_do], ['PQ-9', 0, 'Đếm lại tờ 500.000']);
    var m2 = dungMoi(manQuy({ cho: cho, duyet: 1, toi: 'dung@x' }));
    await m2.g.scrQuyTm(); await tick();
    dung('người kiểm không thấy nút duyệt phiếu của mình', !mot(m2, '[data-qtmduyet]') && chu(mot(m2, '[data-qtmcho]')).indexOf('Chờ Giám đốc duyệt') >= 0);
  });

  await ca('Tiền hiện có: dòng Quỹ công ty bấm được, mở màn Quỹ tiền mặt', async function () {
    var m = dungMoi(manQuy());
    m.g.api = function (d) {
      if (d === 'vagabond.tai_chinh.tien_hien_co') return Promise.resolve({ luc: '2026-11-02 08:00', sepay_doc_duoc: 1, tong: { tong: 1 },
        dong: [{ nguon: 'tm:QUY', loai: 'Tiền mặt', ten: 'Quỹ tiền mặt công ty', moc: null, so_du: 45200000, ghi: [] },
          { nguon: 'tm:TCV', loai: 'Tiền mặt', ten: 'Két District 1', so_du: 1, ghi: [] }] });
      return Promise.resolve({});
    };
    m.g.S.roles = ['Giám đốc']; m.g.hasRole = function (r) { return r === 'Giám đốc'; };
    await m.g.scrTcTien(); await tick();
    var q = ds(m, '[data-tcnguon]').filter(function (x) { return x.getAttribute('data-tcnguon') === 'tm:QUY'; })[0];
    bang('dòng quỹ mang khoá mở màn', q.getAttribute('data-tcgo'), 'TCQUY');
    q.onclick();
    bang('mở màn Quỹ', m.vgbGo, ['TCQUY']);
    var ket2 = ds(m, '[data-tcnguon]').filter(function (x) { return x.getAttribute('data-tcnguon') === 'tm:TCV'; })[0];
    dung('dòng két không mở màn quỹ', !ket2.getAttribute('data-tcgo'));
  });

  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exit(ket.hong ? 1 : 0);
})();
