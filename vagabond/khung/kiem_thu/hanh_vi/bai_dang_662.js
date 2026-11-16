/* Ca kiểm HÀNH VI v662: Bài đăng mạng xã hội (75-bai-dang.js).
 *
 * Nạp THẬT 75-bai-dang.js cùng các hàm nền nó dùng vào DOM giả (khuôn của
 * zalo_kb_621.js). Máy chủ giả trả đúng hình dạng vagabond/bai_dang.py và ghi
 * lại lời gọi; luật trạng thái, khoá, bảng Kiểm chạy thật ở thu_bai_dang_662.py.
 * Mỗi ca bấm đúng chuỗi thao tác của Marketing, không gọi hàm nội bộ "cho chắc".
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/bai_dang_662.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js'), CRM = doc('58-crm.js');
var MAN = doc('75-bai-dang.js');

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
var HAM = ['h', 'money'].map(function (t) { return layHam(NEN, t); })
  .concat([layHam(POS, 'posChipNut'), layHam(KM, 'kmHangChip'), layHam(KHO, 'errMsg')])
  .concat(['crmTrong', 'crmMoSheet', 'crmCongTac', 'crmDatCongTac'].map(function (t) { return layHam(CRM, t); })).join('\n');

var P = 'vagabond.bai_dang.';

function the(name, gio, tt, kenh, them) {
  var b = { name: name, tieu_de: 'Bài ' + name, trang_thai: tt, gio: gio, ngay: '2026-11-17', luc: '2026-11-17 ' + gio, anh: '/f/' + name + '.jpg', kieu: 'Bài đăng',
    kenh: kenh.map(function (k) { return { k: k, tt: '' }; }) };
  Object.keys(them || {}).forEach(function (k) { b[k] = them[k]; });
  return b;
}
function lichMau() {
  var ngay = ['16', '17', '18', '19', '20', '21', '22'].map(function (d) { return { ngay: '2026-11-' + d, hom_nay: false, da_qua: false, bai: [] }; });
  ngay[1].bai = [the('BD-1', '07:30', 'Chờ duyệt', ['fb', 'ig', 'th', 'zl']), the('BD-2', '08:30', 'Nháp', ['ig', 'th'], { trung: 'Instagram cách bài 07:30 1 giờ' }),
    the('BD-3', '19:00', 'Đã hẹn giờ', ['fb', 'zl'])];
  ngay[1].trong = ['11:30'];
  return { xem: 'tuan', moc: '2026-11-17', hom_nay: '2026-11-15', gio_nay: '20:00', loc_kenh: [], duyet: true, gio_vang: ['07:30', '11:30', '19:30'],
    viec: { cho_duyet: 2, dang_tay: 1, chua_gio: 0 }, ky_chu: '16/11 - 22/11/2026', ngay: ngay };
}
function baiMau(them) {
  var b = { name: 'BD-1', tieu_de: 'Croissant', trang_thai: 'Nháp', kieu: 'Bài đăng', y_chinh: 'Croissant ra lò', kenh_chon: ['fb', 'th'],
    hen_luc: '2026-11-17 07:30', ban_luu: 5, sua: true, luu_luc: '20:41', duyet_luc: '',
    anh: [{ ten: 'a1', url: '/f/1.jpg', rong: 1080, cao: 1080, khung: '1:1' }, { ten: 'a2', url: '/f/2.jpg', rong: 1080, cao: 1350, khung: '4:5' }],
    ban: { fb: { chu: 'Bánh fb', tieu_de: '', ai: 1 }, th: { chu: 'Bánh th', tieu_de: '', ai: 1 } },
    cho_kenh: { fb: [{ ten: 'a1', url: '/f/1.jpg', khung: '1:1', cat: false }, { ten: 'a2', url: '/f/2.jpg', khung: '1:1', cat: true }],
      th: [{ ten: 'a1', url: '/f/1.jpg', khung: '4:5', cat: true }, { ten: 'a2', url: '/f/2.jpg', khung: '4:5', cat: false }] },
    kenh: [], kiem: [{ muc: 'ok', chu: 'Đủ ảnh và chữ cho 2 kênh' }] };
  Object.keys(them || {}).forEach(function (k) { b[k] = them[k]; });
  return { bai: b, duyet: true, gio_vang: ['07:30', '11:30', '19:30'] };
}

function dungMoi(vai, traLoi) {
  var tai = dg.taiLieuGia();
  var goc = new dg.ElementGia('div');
  goc.parentNode = tai.body; tai.body.children.push(goc);
  var goi = [], toastDs = [], hoi = [];
  var that = {
    document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object, RegExp: RegExp, Promise: Promise,
    Number: Number, Date: Date, setTimeout: setTimeout, clearTimeout: clearTimeout, isNaN: isNaN, parseInt: parseInt, navigator: {},
    S: { roles: vai, stack: [1, 2], chuaLuu: '' }, frappe: { csrf_token: 'x' },
    hasRole: function (r) { return vai.indexOf(r) >= 0; },
    frame: function (t, html, opt) {
      opt = opt || {};
      goc.innerHTML = '<div class="vb" id="vgbBody">' + html + '</div>' + (opt.footer ? '<div class="vf">' + opt.footer + '</div>' : '') +
        (opt.action ? '<button id="vgbAct">' + opt.action + '</button>' : '');
      that._t = t;
      return goc.querySelector('#vgbBody');
    },
    go: function (fn) { return fn(); },
    back: function () { that._lui = (that._lui || 0) + 1; },
    busy: function () {},
    vgbBoChuaLuu: function () { that.S.chuaLuu = ''; },
    toast: function (m) { toastDs.push(m); },
    confirmSheet: function (t, m) { hoi.push(t + '|' + m); return Promise.resolve(that._dongY !== false); },
    /* Hộp nhập chữ giả: chạy đúng hàm kiem của màn như hộp thật; người dùng "dán" that._link. */
    hoiChu: function (t, m, md, o) {
      hoi.push(t + '|' + m + '|' + ((o || {}).nut || ''));
      if (that._dongY === false) return Promise.resolve(null);
      var v = that._link || '';
      var sai = o && o.kiem ? o.kiem(v) : '';
      if (sai) { that._loiHop = sai; return Promise.resolve(null); }
      return Promise.resolve(v);
    },
    api: function (duong, ts) {
      goi.push({ duong: duong, ts: ts });
      var f = (traLoi || {})[duong.replace(P, '')];
      if (typeof f === 'function') { try { return Promise.resolve(f(ts)); } catch (e) { return Promise.reject(e); } }
      if (f !== undefined) return Promise.resolve(JSON.parse(JSON.stringify(f)));
      return Promise.resolve(duong.indexOf('lich') >= 0 ? lichMau() : baiMau());
    }
  };
  that.window = that;
  vm.runInNewContext(HAM, that, { filename: 'ham-nen.js' });
  vm.runInNewContext(MAN, that, { filename: '75-bai-dang.js' });
  return { g: that, tai: tai, goc: goc, goi: goi, toast: toastDs, hoi: hoi };
}

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) { var x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y); }
function cho(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
async function choDen(dk) { for (var i = 0; i < 150 && !dk(); i++) await cho(10); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }
function sheet(m) { var ds = m.tai.body.children; return ds.length > 1 ? ds[ds.length - 1] : null; }
function bam(m, el) { if (!el) throw new Error('khong co nut de bam'); el.dispatchEvent(dg.suKien('click', {}, el)); }
function go(m, el, gt) { el.value = gt; el.dispatchEvent(dg.suKien('input', {}, el)); }
function goiTen(m, t) { return m.goi.filter(function (x) { return x.duong === P + t; }); }
function mot(el, chon) { return el.querySelectorAll(chon)[0]; }
var MKT = ['Marketing'];

(async function () {
  console.log('v662 Bài đăng mạng xã hội');

  await ca('lịch tuần: ba thẻ của ngày chọn theo giờ, khung giờ vàng trống máy chủ trả (11:30) xếp đúng giữa; thẻ trùng ghi câu đỏ', async function () {
    var m = dungMoi(MKT);
    m.g.BD.ngay = '2026-11-17';
    await m.g.scrBaiDang();
    bang('tiêu đề', m.g._t, 'Bài đăng mạng xã hội');
    var dong = m.goc.querySelectorAll('[data-bdbai],[data-bdtrong]').map(function (x) { return x.getAttribute('data-bdbai') || x.getAttribute('data-bdtrong'); });
    bang('thứ tự theo giờ', dong, ['BD-1', 'BD-2', '2026-11-17 11:30', 'BD-3']);
    dung('câu trùng', chu(mot(m.goc, '[data-bdbai="BD-2"]')).indexOf('Instagram cách bài 07:30 1 giờ') >= 0);
    dung('dải việc: 2 bài chờ duyệt, 1 kênh chờ đăng tay', chu(m.goc).indexOf('bài chờ duyệt') >= 0 && chu(m.goc).indexOf('kênh chờ đăng tay') >= 0);
    bang('hỏi lịch một lần', goiTen(m, 'lich').length, 1);
  });

  await ca('chạm khung giờ vàng trống: tạo bài đúng giờ đó rồi mở màn soạn của bài vừa tạo', async function () {
    var m = dungMoi(MKT, { tao: baiMau({ name: 'BD-9', hen_luc: '2026-11-17 11:30', anh: [], ban: {}, cho_kenh: {} }) });
    m.g.BD.ngay = '2026-11-17';
    await m.g.scrBaiDang();
    bam(m, mot(m.goc, '[data-bdtrong]'));
    await choDen(function () { return m.g._t === 'Bài đăng'; });
    bang('tạo đúng giờ', goiTen(m, 'tao')[0].ts, { hen_luc: '2026-11-17 11:30' });
    dung('ô tải ảnh lớn khi chưa có ảnh', chu(m.goc).indexOf('Tải ảnh designer lên') >= 0);
    dung('chưa có ảnh thì không có khay ảnh', m.goc.querySelectorAll('[data-bdanh]').length === 0);
  });

  await ca('đổi Tháng, chạm một ngày: về Tuần đúng tuần đó; lọc kênh Facebook gửi kenh=fb; Mọi kênh bỏ lọc', async function () {
    var m = dungMoi(MKT, { lich: function (ts) { var d = lichMau(); if (ts.xem === 'thang') { d.xem = 'thang'; d.thang = [null, { ngay: '2026-11-02', bai: [] }]; d.ky_chu = 'Tháng 11/2026'; } return d; } });
    await m.g.scrBaiDang();
    bam(m, mot(m.goc, '[data-bdxem="thang"]'));
    await choDen(function () { return !!mot(m.goc, '[data-bdngay="2026-11-02"]'); });
    bang('xem tháng', goiTen(m, 'lich')[1].ts.xem, 'thang');
    dung('có ô ngày 2', !!mot(m.goc, '[data-bdngay="2026-11-02"]'));
    bam(m, mot(m.goc, '[data-bdngay="2026-11-02"]'));
    await choDen(function () { return goiTen(m, 'lich').length === 3 && !!mot(m.goc, '[data-bdngay="2026-11-16"]'); });
    bang('về tuần đúng mốc', [goiTen(m, 'lich')[2].ts.xem, goiTen(m, 'lich')[2].ts.moc], ['tuan', '2026-11-02']);
    bam(m, mot(m.goc, '[data-bdlockenh="fb"]'));
    await choDen(function () { return !!mot(m.goc, '[data-bdlockenh=""]'); });
    bang('lọc Facebook', goiTen(m, 'lich')[3].ts.kenh, 'fb');
    bam(m, mot(m.goc, '[data-bdlockenh=""]'));
    await choDen(function () { return goiTen(m, 'lich').length === 5; });
    bang('bỏ lọc', goiTen(m, 'lich')[4].ts.kenh, '');
  });

  await ca('màn soạn: khay ảnh đánh số, ba dòng thuộc tính, AI soạn chữ, xem trước từng kênh; kênh chỉ chọn ở MỘT chỗ', async function () {
    var m = dungMoi(MKT);
    await m.g.scrBaiDangSoan('BD-1');
    bang('hai ảnh', m.goc.querySelectorAll('[data-bdanh]').length, 2);
    dung('ba dòng thuộc tính', !!mot(m.goc, '[data-bdkieu]') && !!mot(m.goc, '[data-bdgio]') && !!mot(m.goc, '[data-bdchonkenh]'));
    bang('xem trước đúng kênh đã chọn', m.goc.querySelectorAll('[data-bdthe]').map(function (x) { return x.getAttribute('data-bdthe'); }), ['fb', 'th']);
    bang('không có hàng chip kênh thứ hai', m.goc.querySelectorAll('[data-bdkenh],[data-bdtab]').length, 0);
    dung('Threads ghi ảnh cắt tự động 4:5', chu(mot(m.goc, '[data-bdthe="th"]')).indexOf('Ảnh cắt tự động 4:5') >= 0);
    dung('Facebook ghi lưới dự kiến', chu(mot(m.goc, '[data-bdthe="fb"]')).indexOf('Facebook tự xếp theo ảnh đầu') >= 0);
    dung('nút duyệt nói rõ việc', chu(mot(m.goc, '.vf')).indexOf('Duyệt · hẹn T3 17/11 · 07:30 · 2 kênh') >= 0);
  });

  await ca('còn lỗi đỏ: nút Duyệt khoá và ghi số lỗi; bấm nút sửa Threads cuộn tới ô chữ Threads', async function () {
    var m = dungMoi(MKT, { xem: baiMau({ kiem: [{ muc: 'chan', chu: 'Threads dài 519/500 ký tự', nut: ['chu:th', 'Rút gọn'] }] }) });
    await m.g.scrBaiDangSoan('BD-1');
    var n = mot(m.goc, '[data-bdduyet]');
    dung('khoá', n.hasAttribute('disabled'));
    dung('ghi số lỗi', chu(n).indexOf('Còn 1 lỗi đỏ') >= 0);
    var cuon = 0; mot(m.goc, '[data-bdthe="th"]').scrollIntoView = function () { cuon++; };
    bam(m, mot(m.goc, '[data-bdsua="chu:th"]'));
    bang('cuộn tới Threads', cuon, 1);
  });

  await ca('tự lưu: gõ hai lần nhanh chỉ lưu MỘT lượt, gửi đúng số lần lưu đang thấy, gộp cả hai ô; lưu xong bỏ câu hỏi rời màn', async function () {
    var m = dungMoi(MKT, { luu: function (ts) { var d = baiMau({ ban_luu: 6 }); return d; } });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="th"]'), 'Chữ Threads mới');
    go(m, mot(m.goc, '#bdY'), 'Ý chính mới');
    dung('đang lưu dở thì có câu hỏi rời màn', !!m.g.S.chuaLuu);
    bang('chưa gọi ngay', goiTen(m, 'luu').length, 0);
    await cho(950);
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    var l = goiTen(m, 'luu');
    bang('một lượt', l.length, 1);
    bang('số lần lưu', l[0].ts.ban_luu, 5);
    bang('gộp hai ô', JSON.parse(l[0].ts.thay), { ban: { th: { chu: 'Chữ Threads mới' } }, y_chinh: 'Ý chính mới' });
    await choDen(function () { return !m.g.S.chuaLuu; });
    bang('bỏ câu hỏi rời màn', m.g.S.chuaLuu, '');
    bang('lượt sau gửi số mới', m.g.BD.ban, 6);
  });

  await ca('tự lưu bị máy khác sửa trước (xung đột): báo và vẽ lại bản mới, không gửi lại chữ cũ', async function () {
    var m = dungMoi(MKT, { luu: function () { var d = baiMau({ ban_luu: 9, y_chinh: 'Bản máy khác' }); d.xung_dot = 1; return d; } });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'chữ của tôi');
    await cho(950);
    await choDen(function () { return m.toast.length > 0; });
    dung('báo xung đột', m.toast[0].indexOf('đã nạp bản mới nhất') >= 0);
    bang('vẽ lại bản mới', mot(m.goc, '#bdY').value, 'Bản máy khác');
    await cho(950);
    bang('không gửi lại chữ cũ', goiTen(m, 'luu').length, 1);
  });

  await ca('đã rời màn soạn rồi lượt lưu mới trả về (kể cả xung đột): KHÔNG kéo người dùng quay lại bài cũ', async function () {
    var m = dungMoi(MKT, { luu: function () { var d = baiMau({ ban_luu: 9 }); d.xung_dot = 1; return d; } });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'gõ dở');
    await m.g.scrBaiDang();
    await cho(950);
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    await cho(30);
    bang('vẫn ở lịch', m.g._t, 'Bài đăng mạng xã hội');
    dung('không có màn soạn', !mot(m.goc, '[data-bdman]'));
  });

  await ca('đổi Tuần sang Tháng liên tiếp: lượt trả lời cũ đến muộn KHÔNG vẽ đè lượt mới', async function () {
    var tre = [];
    var m = dungMoi(MKT, { lich: function (ts) {
      var d = lichMau();
      if (ts.xem === 'thang') { d.xem = 'thang'; d.thang = [{ ngay: '2026-11-02', bai: [] }]; d.ky_chu = 'Tháng 11/2026'; return d; }
      return new Promise(function (r) { tre.push(function () { r(d); }); });
    } });
    var dau = m.g.scrBaiDang();
    m.g.BD.xem = 'thang';
    await m.g.scrBaiDang();
    dung('đang ở tháng', !!mot(m.goc, '[data-bdngay="2026-11-02"]'));
    tre.forEach(function (f) { f(); });
    await dau; await cho(20);
    dung('lượt tuần trễ không vẽ đè', !!mot(m.goc, '[data-bdngay="2026-11-02"]') && !mot(m.goc, '[data-bdbai]'));
  });

  await ca('Duyệt có điều cần để ý: hỏi lại kèm từng điều; đồng ý thì gửi lần hai với đã đọc; không đồng ý thì không gửi lần hai', async function () {
    var lan = 0;
    var m = dungMoi(MKT, { duyet: function (ts) { lan++; var d = baiMau(); if (!ts.da_doc_nhac) { d.can_doc_nhac = ['Ảnh này đã đăng trong bài "Mekong" ngày 03/11']; return d; } d.bai.trang_thai = 'Chờ đăng tay'; d.bai.sua = false; d.bai.kenh = [{ k: 'fb', tt: 'Chờ đăng tay' }, { k: 'th', tt: 'Chờ đăng tay' }]; return d; } });
    await m.g.scrBaiDangSoan('BD-1');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return lan === 2; });
    dung('hỏi kèm điều nhắc', m.hoi[0].indexOf('Mekong') >= 0);
    bang('lần hai có đã đọc', goiTen(m, 'duyet')[1].ts.da_doc_nhac, 1);
    await choDen(function () { return !!mot(m.goc, '[data-bdmotay]'); });
    bang('hai kênh đăng tay', m.goc.querySelectorAll('[data-bdmotay]').length, 2);
    var x = dungMoi(MKT, { duyet: function () { var d = baiMau(); d.can_doc_nhac = ['nhắc']; return d; } });
    x.g._dongY = false;
    await x.g.scrBaiDangSoan('BD-1');
    bam(x, mot(x.goc, '[data-bdduyet]'));
    await cho(50);
    bang('không đồng ý thì một lượt', goiTen(x, 'duyet').length, 1);
  });

  await ca('Đã đăng: hỏi lại đúng tên kênh rồi mới ghi; không đồng ý thì không gọi máy chủ', async function () {
    var dl = baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Đã đăng', luc: '09:12', link: 'https://fb.com/1' }, { k: 'th', tt: 'Chờ đăng tay' }] });
    var m = dungMoi(MKT, { xem: dl });
    await m.g.scrBaiDangSoan('BD-1');
    dung('không còn nút Trả về nháp khi đã có kênh lên', !mot(m.goc, '[data-bdtrave]'));
    bang('chỉ Threads còn nút', m.goc.querySelectorAll('[data-bddadang]').map(function (x) { return x.getAttribute('data-bddadang'); }), ['th']);
    m.g._dongY = false;
    bam(m, mot(m.goc, '[data-bddadang="th"]'));
    await cho(30);
    bang('không ghi', goiTen(m, 'da_dang').length, 0);
    m.g._dongY = true;
    bam(m, mot(m.goc, '[data-bddadang="th"]'));
    await choDen(function () { return goiTen(m, 'da_dang').length === 1; });
    dung('hỏi đúng kênh', m.hoi[m.hoi.length - 1].indexOf('Đã đăng Threads?') === 0);
    bang('gửi đúng kênh, chưa dán link', goiTen(m, 'da_dang')[0].ts, { ma: 'BD-1', kenh: 'th', link: '' });
  });

  await ca('Codex #572: Đã đăng có ô dán link và gửi link lên; link lạ bị giữ lại trong hộp; kênh đã đăng chưa có link có nút Thêm link', async function () {
    var dl = baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Đã đăng', luc: '09:12', link: '' }, { k: 'th', tt: 'Chờ đăng tay' }] });
    var m = dungMoi(MKT, { xem: dl, da_dang: dl });
    await m.g.scrBaiDangSoan('BD-1');
    m.g._link = 'javascript:alert(1)';
    bam(m, mot(m.goc, '[data-bddadang="th"]'));
    await cho(30);
    dung('link lạ: hộp báo lỗi', (m.g._loiHop || '').indexOf('https://') >= 0);
    bang('link lạ: không gọi máy chủ', goiTen(m, 'da_dang').length, 0);
    m.g._link = 'https://www.threads.net/@thevagabond.patisserie/post/1';
    bam(m, mot(m.goc, '[data-bddadang="th"]'));
    await choDen(function () { return goiTen(m, 'da_dang').length === 1; });
    bang('gửi link', goiTen(m, 'da_dang')[0].ts, { ma: 'BD-1', kenh: 'th', link: 'https://www.threads.net/@thevagabond.patisserie/post/1' });
    dung('nút trong hộp ghi đúng việc', m.hoi[m.hoi.length - 1].indexOf('|Đã đăng Threads') > 0);
    var n = mot(m.goc, '[data-bdthemlink="fb"]');
    dung('Facebook đã đăng chưa có link: có nút Thêm link', !!n);
    m.g._link = 'https://facebook.com/p/9';
    bam(m, n);
    await choDen(function () { return goiTen(m, 'da_dang').length === 2; });
    bang('thêm link Facebook', goiTen(m, 'da_dang')[1].ts, { ma: 'BD-1', kenh: 'fb', link: 'https://facebook.com/p/9' });
  });

  await ca('Codex #572: bài A lưu hỏng, chọn Rời đi bỏ thay đổi, mở bài B: KHÔNG ghi nội dung A vào B, lượt lưu của B chỉ có chữ B và đúng số lần lưu của B', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      xem: function (ts) { return baiMau(ts.ma === 'BD-2' ? { name: 'BD-2', ban_luu: 11, y_chinh: 'Ý của B' } : {}); },
      luu: function (ts) { lan++; if (lan === 1) throw new Error('mất mạng'); return baiMau({ name: ts.ma, ban_luu: 12 }); }
    });
    m.g.bdLoi = function () {};
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'chữ của A chưa lưu');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    m.g.S.chuaLuu = '';
    await m.g.scrBaiDangSoan('BD-2');
    mot(m.goc, '#bdY').dispatchEvent(dg.suKien('focusout', {}, mot(m.goc, '#bdY')));
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await cho(50);
    bang('mở B rồi rời ô: không lưu gì lên B', goiTen(m, 'luu').filter(function (x) { return x.ts.ma === 'BD-2'; }).length, 0);
    go(m, mot(m.goc, '#bdY'), 'Ý của B sửa');
    await cho(950);
    await choDen(function () { return goiTen(m, 'luu').length === 2; });
    var l = goiTen(m, 'luu')[1].ts;
    bang('lượt lưu của B', [l.ma, l.ban_luu, JSON.parse(l.thay)], ['BD-2', 11, { y_chinh: 'Ý của B sửa' }]);
  });

  await ca('Codex #572 vòng 2: bài A lưu hỏng, bỏ thay đổi, mở bài B đã lưu đủ: Duyệt B chạy ngay, kết quả hỏng của A không chặn B', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      xem: function (ts) { return baiMau(ts.ma === 'BD-2' ? { name: 'BD-2', ban_luu: 11 } : {}); },
      luu: function () { lan++; throw new Error('mất mạng'); },
      duyet: function (ts) { var d = baiMau({ name: ts.ma, trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); return d; }
    });
    m.g.bdLoi = function () {};
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'chữ A');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    m.g.S.chuaLuu = '';
    await m.g.scrBaiDangSoan('BD-2');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('duyệt đúng bài B', goiTen(m, 'duyet').map(function (x) { return x.ts.ma; }), ['BD-2']);
    bang('không lưu gì thêm', lan, 1);
    dung('không báo chưa lưu được', !m.toast.some(function (t) { return t.indexOf('chưa lưu được') >= 0; }));
  });

  await ca('Codex #572 vòng 3: bấm Duyệt lúc lượt lưu của CHÍNH bài đang chạy mà máy khác vừa sửa: không duyệt, nạp bản mới; bấm lại mới duyệt đúng bản mới', async function () {
    var nha = null;
    var m = dungMoi(MKT, {
      luu: function () { return new Promise(function (r) { nha = function () { var d = baiMau({ ban_luu: 6, y_chinh: 'Bản máy khác' }); d.xung_dot = 1; r(d); }; }); },
      duyet: function (ts) { var d = baiMau({ trang_thai: 'Chờ đăng tay', sua: false, ban_luu: ts.ban_luu + 1, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); return d; }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Chú thích của tôi');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await choDen(function () { return !!nha; });
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await cho(20);
    nha();
    await choDen(function () { return m.toast.some(function (t) { return t.indexOf('Xem lại rồi bấm lại') >= 0; }); });
    await cho(20);
    bang('chưa duyệt', goiTen(m, 'duyet').length, 0);
    bang('đã nạp bản mới', mot(m.goc, '#bdY').value, 'Bản máy khác');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('bấm lại: duyệt đúng số lần lưu của bản mới', goiTen(m, 'duyet')[0].ts.ban_luu, 6);
  });

  await ca('Codex #572 vòng 4: bấm đúp Duyệt lúc lượt lưu đang chạy rồi bị xung đột: KHÔNG lần bấm nào duyệt; bấm lại sau khi thấy bản mới mới duyệt', async function () {
    var nha = null;
    var m = dungMoi(MKT, {
      luu: function () { return new Promise(function (r) { nha = function () { var d = baiMau({ ban_luu: 6, y_chinh: 'Bản máy khác' }); d.xung_dot = 1; r(d); }; }); },
      duyet: function (ts) { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Chú thích của tôi');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await choDen(function () { return !!nha; });
    var nut = mot(m.goc, '[data-bdduyet]');
    bam(m, nut); bam(m, nut);
    await cho(20);
    nha();
    await cho(60);
    bang('hai lần bấm trước xung đột: không duyệt', goiTen(m, 'duyet').length, 0);
    dung('không báo Đã duyệt', !m.toast.some(function (t) { return t.indexOf('Đã duyệt') === 0; }));
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('bấm lại sau khi thấy bản mới thì duyệt', goiTen(m, 'duyet')[0].ts.ban_luu, 6);
  });

  await ca('Codex #572 vòng 4: bấm Duyệt lúc đang lưu, rồi sửa tiếp và rời ô trước khi lượt đầu trả về: Duyệt chỉ chạy SAU lượt lưu cuối, đúng số lần lưu cuối', async function () {
    var nha = [], thuTu = [];
    var m = dungMoi(MKT, {
      luu: function (ts) { return new Promise(function (r) { nha.push(function () { thuTu.push('luu:' + ts.ban_luu); r(baiMau({ ban_luu: ts.ban_luu + 1 })); }); }); },
      duyet: function (ts) { thuTu.push('duyet:' + ts.ban_luu); return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    var vb = function () { m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody'))); };
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần một'); vb();
    await choDen(function () { return nha.length === 1; });
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await cho(10);
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần hai'); vb();
    await cho(10);
    nha[0]();
    await choDen(function () { return nha.length === 2; });
    await cho(30);
    bang('chưa duyệt khi lượt hai còn chờ', goiTen(m, 'duyet').length, 0);
    nha[1]();
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('thứ tự', thuTu, ['luu:5', 'luu:6', 'duyet:7']);
  });

  await ca('Codex #572 vòng 5: bấm Duyệt lúc lượt đầu đang chạy, sửa tiếp rời ô; lượt đầu xung đột: Duyệt đó dừng, lượt sửa viết trên bản cũ không ghi đè bản mới; bấm lại mới duyệt', async function () {
    var nha = [];
    var m = dungMoi(MKT, {
      luu: function (ts) { var so = nha.length + 1; return new Promise(function (r) { nha.push(function () { var d = baiMau({ ban_luu: so === 1 ? 6 : ts.ban_luu + 1, y_chinh: 'Bản máy khác' }); if (so === 1) d.xung_dot = 1; r(d); }); }); },
      duyet: function (ts) { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    var vb = function () { m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody'))); };
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần một'); vb();
    await choDen(function () { return nha.length === 1; });
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await cho(10);
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần hai'); vb();
    await cho(10);
    nha[0]();
    await cho(80);
    bang('lượt sửa trên bản cũ bị bỏ, không ghi đè bản máy khác', goiTen(m, 'luu').length, 1);
    bang('Duyệt đang chờ không chạy', goiTen(m, 'duyet').length, 0);
    dung('không báo Đã duyệt', !m.toast.some(function (t) { return t.indexOf('Đã duyệt') === 0; }));
    bang('màn hiện bản mới', mot(m.goc, '#bdY').value, 'Bản máy khác');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('bấm lại thì duyệt đúng bản mới', goiTen(m, 'duyet')[0].ts.ban_luu, 6);
  });

  await ca('H8 loại 4: bấm đúp Duyệt lúc lượt lưu đang chạy (không xung đột): chỉ MỘT lần gọi Duyệt', async function () {
    var nha = null;
    var m = dungMoi(MKT, {
      luu: function () { return new Promise(function (r) { nha = function () { r(baiMau({ ban_luu: 6 })); }; }); },
      duyet: function () { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Chú thích');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await choDen(function () { return !!nha; });
    var nut = mot(m.goc, '[data-bdduyet]');
    bam(m, nut); bam(m, nut);
    nha();
    await choDen(function () { return goiTen(m, 'duyet').length >= 1; });
    await cho(50);
    bang('một lần Duyệt', goiTen(m, 'duyet').length, 1);
  });

  await ca('H8 loại 8: bài A lưu hỏng, bỏ thay đổi, mở lại CHÍNH bài A từ lịch: Duyệt chạy, không bị chặn vì lần hỏng cũ', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      luu: function () { lan++; throw new Error('mất mạng'); },
      duyet: function () { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    m.g.bdLoi = function () {};
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'chữ chưa lưu');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    m.g.S.chuaLuu = '';
    await m.g.scrBaiDang();
    await m.g.scrBaiDangSoan('BD-1');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('duyệt, không lưu lại phần đã bỏ', [goiTen(m, 'duyet').length, lan], [1, 1]);
  });

  await ca('Codex #572 vòng 4: bấm Duyệt lúc đang lưu, rồi gõ thêm (chưa rời ô): Duyệt lưu nốt phần vừa gõ rồi mới duyệt, không báo chưa lưu được', async function () {
    var nha = [], thuTu = [];
    var m = dungMoi(MKT, {
      luu: function (ts) { var p = new Promise(function (r) { nha.push(function () { thuTu.push('luu:' + ts.ban_luu); r(baiMau({ ban_luu: ts.ban_luu + 1 })); }); }); if (nha.length > 1) nha[nha.length - 1](); return p; },
      duyet: function (ts) { thuTu.push('duyet:' + ts.ban_luu); return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần một');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await choDen(function () { return nha.length === 1; });
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await cho(10);
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Lần hai');
    nha[0]();
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('thứ tự', thuTu, ['luu:5', 'luu:6', 'duyet:7']);
    dung('không báo chưa lưu được', !m.toast.some(function (t) { return t.indexOf('chưa lưu được') >= 0; }));
  });

  await ca('Codex #572 vòng 3: tự lưu bị máy khác sửa trước, rời về lịch rồi mở lại bài: Duyệt chạy ngay (không còn bị chặn vì lần xung đột cũ)', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      luu: function () { lan++; var d = baiMau({ ban_luu: 9 }); d.xung_dot = 1; return d; },
      duyet: function () { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'gõ');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    await m.g.scrBaiDang();
    await m.g.scrBaiDangSoan('BD-1');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('duyệt một lần', goiTen(m, 'duyet').length, 1);
  });

  await ca('Codex #572 vòng 3: sau lần xung đột đã nạp bản mới, người dùng sửa tiếp và lưu được: Duyệt chạy ngay', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      luu: function () { lan++; var d = baiMau({ ban_luu: 8 + lan }); if (lan === 1) d.xung_dot = 1; return d; },
      duyet: function () { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'gõ lần một');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    go(m, mot(m.goc, '#bdY'), 'sửa trên bản mới');
    await cho(950);
    await choDen(function () { return lan === 2; });
    await cho(20);
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('duyệt đúng bản vừa lưu', goiTen(m, 'duyet')[0].ts.ban_luu, 10);
  });

  await ca('Codex #572 vòng 3: lưu hỏng rồi mạng có lại: bấm Duyệt lưu lại phần sửa trước, lưu được thì duyệt', async function () {
    var lan = 0;
    var m = dungMoi(MKT, {
      luu: function (ts) { lan++; if (lan === 1) throw new Error('mất mạng'); return baiMau({ ban_luu: 7 }); },
      duyet: function (ts) { return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kenh: [{ k: 'fb', tt: 'Chờ đăng tay' }] }); }
    });
    m.g.bdLoi = function () {};
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Chú thích mới');
    await cho(950);
    await choDen(function () { return lan === 1; });
    await cho(20);
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'duyet').length === 1; });
    bang('lượt hai gửi lại phần sửa', JSON.parse(goiTen(m, 'luu')[1].ts.thay), { ban: { fb: { chu: 'Chú thích mới' } } });
    bang('duyệt đúng bản vừa lưu', goiTen(m, 'duyet')[0].ts.ban_luu, 7);
  });

  await ca('H8 loại 8 (quét vòng 3): đang tải 2 ảnh cho bài A thì mở bài B: ảnh thứ hai vẫn vào bài A với số lần lưu của A', async function () {
    var nhaAnh = null, lanAnh = 0;
    var m = dungMoi(MKT, {
      xem: function (ts) { return baiMau(ts.ma === 'BD-2' ? { name: 'BD-2', ban_luu: 11 } : {}); },
      them_anh: function (ts) { lanAnh++; if (lanAnh === 1) return new Promise(function (r) { nhaAnh = function () { r(baiMau({ ban_luu: 6 })); }; }); return baiMau({ ban_luu: 7 }); }
    });
    m.g.bdTaiTep = function (f, ma) { return Promise.resolve('/files/' + f.name + '@' + ma); };
    await m.g.scrBaiDangSoan('BD-1');
    m.g.bdChonAnh();
    var inp = m.tai.body.children.filter(function (x) { return x.tagName && String(x.tagName).toLowerCase() === 'input'; }).pop();
    dung('có ô chọn tệp', !!inp);
    inp.files = [{ name: 'a1.jpg' }, { name: 'a2.jpg' }];
    var xong = inp.onchange();
    await choDen(function () { return !!nhaAnh; });
    await m.g.scrBaiDangSoan('BD-2');
    nhaAnh();
    await xong;
    var g = goiTen(m, 'them_anh').map(function (x) { return [x.ts.ma, x.ts.ban_luu, x.ts.file_url]; });
    bang('hai ảnh vào bài A', g, [['BD-1', 5, '/files/a1.jpg@BD-1'], ['BD-1', 6, '/files/a2.jpg@BD-1']]);
    dung('màn vẫn ở bài B', !!mot(m.goc, '[data-bdman="BD-2"]'));
    bang('bài đang mở trong bộ nhớ vẫn là B (không bị ảnh của A kéo về A)', [m.g.BD.bai.name, m.g.BD.ban], ['BD-2', 11]);
  });

  await ca('H8 loại 8 (quét vòng 3): sheet giờ chạm ngày 18 rồi ngày 19, lượt ngày 18 trả về muộn KHÔNG vẽ đè ô giờ ngày 19', async function () {
    var tre = [];
    var m = dungMoi(MKT, { gio_trong: function (ts) {
      var d = { ngay: ['2026-11-17', '2026-11-18', '2026-11-19'], chon: ts.ngay || '2026-11-17', gio: '', khung: [{ gio: ts.ngay === '2026-11-18' ? '18:00' : '19:00', vang: 0, qua: false, trung: '' }] };
      if (ts.ngay === '2026-11-18') return new Promise(function (r) { tre.push(function () { r(d); }); });
      return d;
    } });
    await m.g.scrBaiDangSoan('BD-1');
    bam(m, mot(m.goc, '[data-bdgio]'));
    await choDen(function () { return !!sheet(m); });
    bam(m, mot(sheet(m), '[data-bdsgngay="2026-11-18"]'));
    await cho(10);
    bam(m, mot(sheet(m), '[data-bdsgngay="2026-11-19"]'));
    await choDen(function () { return !!mot(sheet(m), '[data-bdsggio="19:00"]') && chu(mot(sheet(m), '[data-bdsgok]')).indexOf('Chọn một ô giờ') >= 0; });
    tre.forEach(function (f) { f(); });
    await cho(30);
    dung('vẫn là ô giờ ngày 19', !!mot(sheet(m), '[data-bdsggio="19:00"]') && !mot(sheet(m), '[data-bdsggio="18:00"]'));
    bam(m, mot(sheet(m), '[data-bdsggio="19:00"]'));
    bam(m, mot(sheet(m), '[data-bdsgok]'));
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    bang('lưu đúng ngày 19', JSON.parse(goiTen(m, 'luu')[0].ts.thay), { hen_luc: '2026-11-19 19:00' });
  });

  await ca('Codex #572: lượt lưu bài A còn xếp hàng khi đã mở bài B: lượt đó gửi đúng mã A và số lần lưu A vừa nhận, không lấy số của B', async function () {
    var nhaDau = null;
    var m = dungMoi(MKT, {
      xem: function (ts) { return baiMau(ts.ma === 'BD-2' ? { name: 'BD-2', ban_luu: 11 } : {}); },
      luu: function (ts) {
        if (!nhaDau) return new Promise(function (r) { nhaDau = function () { r(baiMau({ ban_luu: 6 })); }; });
        return baiMau({ name: ts.ma, ban_luu: 7 });
      }
    });
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '#bdY'), 'lần một');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await choDen(function () { return !!nhaDau; });
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'lần hai');
    m.goc.querySelector('#vgbBody').dispatchEvent(dg.suKien('focusout', {}, m.goc.querySelector('#vgbBody')));
    await m.g.scrBaiDangSoan('BD-2');
    nhaDau();
    await choDen(function () { return goiTen(m, 'luu').length === 2; });
    var l = goiTen(m, 'luu')[1].ts;
    bang('lượt hai của A', [l.ma, l.ban_luu, JSON.parse(l.thay)], ['BD-1', 6, { ban: { fb: { chu: 'lần hai' } } }]);
  });

  await ca('Codex #572: sửa chú thích rồi bấm Duyệt mà lượt lưu hỏng: KHÔNG gọi Duyệt trên bản cũ, báo chưa lưu được', async function () {
    var m = dungMoi(MKT, { luu: function () { throw new Error('mất mạng'); } });
    m.g.bdLoi = function () {};
    await m.g.scrBaiDangSoan('BD-1');
    go(m, mot(m.goc, '[data-bdchu="fb"]'), 'Chú thích mới');
    bam(m, mot(m.goc, '[data-bdduyet]'));
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    await cho(30);
    bang('không duyệt', goiTen(m, 'duyet').length, 0);
    bang('lưu hỏng thì không gửi lại liên tục', goiTen(m, 'luu').length, 1);
    dung('báo chưa lưu được', m.toast.some(function (t) { return t.indexOf('chưa lưu được') >= 0; }));
    bang('phần sửa còn giữ để lưu lại', m.g.BD.thay, { ban: { fb: { chu: 'Chú thích mới' } } });
    var x = dungMoi(MKT, { luu: function () { throw new Error('mất mạng'); } });
    x.g.bdLoi = function () {};
    await x.g.scrBaiDangSoan('BD-1');
    go(x, mot(x.goc, '#bdY'), 'Ý mới');
    bam(x, mot(x.goc, '[data-bdsoan]'));
    await choDen(function () { return goiTen(x, 'luu').length === 1; });
    await cho(30);
    bang('AI soạn cũng dừng', goiTen(x, 'soan_ai').length, 0);
  });

  await ca('Story: tấm Kênh chỉ bật tắt Facebook, Instagram; không có ô AI soạn chữ; xem trước 9:16 ghi rõ không có sticker', async function () {
    var dl = baiMau({ kieu: 'Story', kenh_chon: ['ig'], ban: {}, cho_kenh: { ig: [{ ten: 'a1', url: '/f/1.jpg', khung: '9:16', cat: true }] } });
    var m = dungMoi(MKT, { xem: dl });
    await m.g.scrBaiDangSoan('BD-1');
    dung('không có ô AI', !mot(m.goc, '#bdY'));
    dung('ghi không có sticker', chu(mot(m.goc, '[data-bdthe="ig"]')).indexOf('Không có sticker') >= 0);
    bam(m, mot(m.goc, '[data-bdchonkenh]'));
    var sh = sheet(m);
    bang('chỉ hai công tắc', sh.querySelectorAll('[data-bdbatkenh]').map(function (x) { return x.getAttribute('data-bdbatkenh'); }), ['fb', 'ig']);
    dung('Threads ghi không có Story', chu(sh).indexOf('Threads không có Story') >= 0);
    bam(m, mot(sh, '[data-bdbatkenh="fb"]'));
    bam(m, mot(sh, '[data-bdxongkenh]'));
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    bang('lưu kênh mới', JSON.parse(goiTen(m, 'luu')[0].ts.thay), { kenh_chon: ['fb', 'ig'] });
  });

  await ca('chọn giờ: ô đã qua bị khoá, ô trùng ghi tên kênh; chọn 11:30 rồi bấm Chọn thì lưu đúng ngày giờ', async function () {
    var m = dungMoi(MKT, { gio_trong: { ngay: ['2026-11-17', '2026-11-18'], chon: '2026-11-17', gio: '07:30',
      khung: [{ gio: '07:30', vang: 1, qua: false, trung: '' }, { gio: '08:00', vang: 0, qua: false, trung: 'Instagram 08:30' }, { gio: '11:30', vang: 1, qua: false, trung: '' }, { gio: '06:00', qua: true }, { gio: '09:00', vang: 0, qua: false, trung: 'Facebook 09:00', da_co: 'Facebook' }] } });
    await m.g.scrBaiDangSoan('BD-1');
    bam(m, mot(m.goc, '[data-bdgio]'));
    await choDen(function () { return !!sheet(m); });
    var sh = sheet(m);
    dung('ô trùng', chu(mot(sh, '[data-bdsggio="08:00"]')).indexOf('Trùng Instagram 08:30') >= 0);
    dung('ô đã qua khoá', mot(sh, '[data-bdsggio="06:00"]').hasAttribute('disabled'));
    dung('Codex #572: ô kênh đã có bài đúng giờ bị khoá, ghi tên kênh', mot(sh, '[data-bdsggio="09:00"]').hasAttribute('disabled') && chu(mot(sh, '[data-bdsggio="09:00"]')).indexOf('Facebook đã có bài giờ này') >= 0);
    bam(m, mot(sh, '[data-bdsggio="11:30"]'));
    bam(m, mot(sheet(m), '[data-bdsgok]'));
    await choDen(function () { return goiTen(m, 'luu').length === 1; });
    bang('lưu giờ', JSON.parse(goiTen(m, 'luu')[0].ts.thay), { hen_luc: '2026-11-17 11:30' });
  });

  /* ------------------------------------------------------------ v664 */
  function baiDuyet() {
    return baiMau({ trang_thai: 'Chờ đăng tay', sua: false, kiem: [], kenh_chon: ['fb', 'ig', 'th', 'zl'], hen_luc: '', tu_dong: ['fb', 'ig', 'th'],
      kenh: [{ k: 'fb', tt: 'Đã đăng', tu: 1, luc: '19:30', link: 'https://facebook.com/p/1' },
        { k: 'ig', tt: 'Chờ đăng tay', tu: 1, loi: 'Instagram từ chối bài: Ảnh quá nhỏ', dang_duoc: 1 },
        { k: 'th', tt: 'Đã đăng', tu: 1, luc: '19:31' }, { k: 'zl', tt: 'Chờ đăng tay', tu: 0 }] });
  }

  await ca('v664 Kho bản thảo: phân đoạn Bản thảo hỏi lịch kiểu bt, hiện thẻ bản thảo (người sửa, số ảnh), nút đáy tạo Bản thảo mới, có nút nhập Word, Excel', async function () {
    var m = dungMoi(MKT, { lich: { xem: 'bt', moc: '2026-11-16', duyet: true, viec: {}, ky_chu: '2 bản thảo', bt: [
      { name: 'BD-7', tieu_de: 'Cheesecake', trich: 'Dâu tây, mâm xôi', trang_thai: 'Nháp', luc: '2026-11-16 12:58', nguoi: 'Minh Vũ', so_anh: 3, anh: '/f/1.jpg' },
      { name: 'BD-8', tieu_de: 'Giáng sinh', trich: 'Tuần 1', trang_thai: 'Chờ duyệt', luc: '2026-11-16 09:10', nguoi: 'Viet Nguyen', so_anh: 0, anh: '' }] } });
    await m.g.scrBaiDang();
    bam(m, mot(m.goc, '[data-bdxem="bt"]'));
    await choDen(function () { return goiTen(m, 'lich').length === 2 && m.goc.querySelectorAll('[data-bdbai]').length; });
    bang('hỏi kiểu bt', goiTen(m, 'lich')[1].ts.xem, 'bt');
    bang('hai thẻ', m.goc.querySelectorAll('[data-bdbai]').map(function (x) { return x.getAttribute('data-bdbai'); }), ['BD-7', 'BD-8']);
    dung('người sửa, số ảnh', chu(mot(m.goc, '[data-bdbai="BD-7"]')).indexOf('Minh Vũ · 3 ảnh') >= 0);
    dung('chưa có ảnh, chờ duyệt', chu(mot(m.goc, '[data-bdbai="BD-8"]')).indexOf('chưa có ảnh · Chờ duyệt') >= 0);
    dung('nút nhập', !!mot(m.goc, '[data-bdnhap]'));
    dung('nút đáy', chu(mot(m.goc, '[data-bdmoi]')).indexOf('Bản thảo mới') >= 0);
    bam(m, mot(m.goc, '[data-bdmoi]'));
    await choDen(function () { return goiTen(m, 'tao').length === 1; });
    bang('tạo không hẹn giờ', goiTen(m, 'tao')[0].ts.hen_luc, '');
  });

  await ca('v664 sau duyệt: kênh tự đăng lỗi hiện lý do và nút Thử lại; bấm hỏi lại rồi gửi đúng kênh; bấm đúp chỉ gửi một lần; kênh Zalo OA chỉ có đăng tay', async function () {
    var m = dungMoi(MKT, { xem: baiDuyet(), thu_lai: function () { return new Promise(function (ok) { setTimeout(function () { ok(baiDuyet()); }, 30); }); } });
    await m.g.scrBaiDangSoan('BD-1');
    dung('lý do', chu(m.goc).indexOf('Instagram từ chối bài: Ảnh quá nhỏ') >= 0);
    dung('dòng phụ', chu(mot(m.goc, '[data-bdthulai="ig"]').parentNode.parentNode).indexOf('Hệ thống chưa tự đăng được') >= 0);
    bang('chỉ Instagram có Thử lại', m.goc.querySelectorAll('[data-bdthulai]').map(function (x) { return x.getAttribute('data-bdthulai'); }), ['ig']);
    dung('Zalo OA vẫn đăng tay', !!mot(m.goc, '[data-bdmotay="zl"]') && !!mot(m.goc, '[data-bddadang="zl"]'));
    dung('Facebook hệ thống tự đăng', chu(m.goc).indexOf('Đã đăng 19:30 · hệ thống tự đăng') >= 0);
    bam(m, mot(m.goc, '[data-bdthulai="ig"]'));
    bam(m, mot(m.goc, '[data-bdthulai="ig"]'));
    await choDen(function () { return goiTen(m, 'thu_lai').length >= 1; });
    await cho(80);
    bang('một lần, đúng kênh', goiTen(m, 'thu_lai').map(function (x) { return x.ts.kenh; }), ['ig']);
    dung('hỏi lại nhắc kiểm trên kênh trước', m.hoi.some(function (x) { return x.indexOf('chưa thấy bài') >= 0; }));
  });

  await ca('v664 máy tính: chạm tên kênh đổi bài xem trước, không vẽ lại màn, không mất chữ đang gõ', async function () {
    var m = dungMoi(MKT, { xem: baiMau({ kenh_chon: ['fb', 'th'] }) });
    await m.g.scrBaiDangSoan('BD-1');
    bang('mặc định kênh đầu', m.goc.querySelectorAll('[data-bdthe]').map(function (x) { return x.getAttribute('data-bdthe') + ':' + x.classList.contains('on'); }), ['fb:true', 'th:false']);
    go(m, mot(m.goc, '#bdY'), 'đang gõ');
    var y = mot(m.goc, '#bdY');
    bam(m, mot(m.goc, '[data-bdxemk="th"]'));
    bang('đổi', m.goc.querySelectorAll('[data-bdthe]').map(function (x) { return x.getAttribute('data-bdthe') + ':' + x.classList.contains('on'); }), ['fb:false', 'th:true']);
    dung('không vẽ lại', mot(m.goc, '#bdY') === y && y.value === 'đang gõ');
    bang('nút chọn', mot(m.goc, '[data-bdxemk="th"]').getAttribute('aria-pressed'), 'true');
  });

  await ca('v664 đang đăng: màn tự đọc lại bài để hiện kết quả; đã rời bài thì lượt đọc muộn không kéo màn về bài cũ', async function () {
    var dang = baiDuyet(); dang.bai.kenh[1] = { k: 'ig', tt: 'Đang đăng', tu: 1 };
    var xong = baiDuyet(); xong.bai.kenh[1] = { k: 'ig', tt: 'Đã đăng', tu: 1, luc: '19:32' };
    var lan = 0;
    var m = dungMoi(MKT, { xem: function () { lan++; return lan === 1 ? dang : xong; } });
    m.g.BD.tdCho = 15;
    await m.g.scrBaiDangSoan('BD-1');
    dung('đang đăng', chu(m.goc).indexOf('Hệ thống đang đăng lên Instagram') >= 0);
    await choDen(function () { return chu(m.goc).indexOf('Đã đăng 19:32') >= 0; });
    dung('đã cập nhật', chu(m.goc).indexOf('Đã đăng 19:32') >= 0);
    var m2 = dungMoi(MKT, { xem: function () { return dang; } });
    m2.g.BD.tdCho = 15;
    await m2.g.scrBaiDangSoan('BD-1');
    m2.goc.innerHTML = '<div>màn khác</div>';
    await cho(60);
    bang('không kéo về', chu(m2.goc), 'màn khác');
    bang('không đọc khi đã rời', goiTen(m2, 'xem').length, 1);
  });

  await ca('v664 Kết nối kênh: sheet cài đặt ghi kênh nào tự đăng, kênh nào đăng tay, kênh lỗi; Kiểm lại hỏi máy chủ đọc mới; không có ô token', async function () {
    var cd = { gio_vang: ['07:30'], sua: true, quan_tri: true, ket_noi: { fb: { ok: 1, chu: 'Tự đăng lên Trang Vagabond' },
      ig: { ok: 0, loi: 1, chu: 'Token Facebook hết hạn' }, th: { ok: 0, chu: 'Chưa nối. Bài lên Threads phải đăng tay.' }, zl: { ok: 0, chu: 'Zalo OA đăng tay.' } } };
    var m = dungMoi(MKT, { cai_dat: cd });
    await m.g.scrBaiDang();
    bam(m, m.tai.getElementById ? (m.goc.querySelectorAll('#vgbAct')[0]) : null);
    await choDen(function () { return !!sheet(m); });
    var t = chu(sheet(m));
    dung('ba trạng thái', t.indexOf('Tự đăng lên Trang Vagabond') >= 0 && t.indexOf('Token Facebook hết hạn') >= 0 && t.indexOf('Lỗi') >= 0 && t.indexOf('Đăng tay') >= 0);
    dung('không có ô nhập token', !sheet(m).querySelectorAll('input').some(function (x) { return x.getAttribute('id') !== 'bdGioVang'; }));
    bam(m, mot(sheet(m), '[data-bdkiemkn]'));
    await choDen(function () { return goiTen(m, 'cai_dat').length === 2; });
    bang('kiểm lại', goiTen(m, 'cai_dat')[1].ts.kiem_lai, 1);
  });

  await ca('v664 Codex #576: ô tìm nhanh đầu Kho bản thảo và Danh sách: gõ không dấu là lọc, không thấy thì nói rõ, ô tìm không bị vẽ lại', async function () {
    var m = dungMoi(MKT, { lich: { xem: 'bt', moc: '2026-11-16', duyet: true, viec: {}, ky_chu: '2 bản thảo', bt: [
      { name: 'BD-7', tieu_de: 'Cheesecake', trich: 'Dâu tây, mâm xôi', trang_thai: 'Nháp', luc: '2026-11-16 12:58', nguoi: 'Minh Vũ', so_anh: 3, anh: '' },
      { name: 'BD-8', tieu_de: 'Bánh khúc cây Giáng sinh', trich: 'Tuần 1', trang_thai: 'Nháp', luc: '2026-11-16 09:10', nguoi: 'Viet Nguyen', so_anh: 0, anh: '' }],
      ds: [the('BD-1', '07:30', 'Chờ duyệt', ['fb', 'ig']), the('BD-2', '08:30', 'Nháp', ['th'])] } });
    m.g.BD.xem = 'bt';
    await m.g.scrBaiDang();
    var o = mot(m.goc, '#bdTim');
    go(m, o, 'banh khuc');
    bang('lọc không dấu', m.goc.querySelectorAll('[data-bdbai]').map(function (x) { return x.getAttribute('data-bdbai'); }), ['BD-8']);
    dung('ô tìm giữ nguyên', mot(m.goc, '#bdTim') === o);
    go(m, o, 'mam xoi');
    bang('lọc theo nội dung', m.goc.querySelectorAll('[data-bdbai]').map(function (x) { return x.getAttribute('data-bdbai'); }), ['BD-7']);
    go(m, o, 'xyz');
    dung('không thấy', chu(m.goc).indexOf('Không thấy bản thảo nào khớp') >= 0);
    bam(m, mot(m.goc, '[data-bdxem="ds"]'));
    await choDen(function () { return !!mot(m.goc, '#bdDsO') && m.goc.querySelectorAll('[data-bdbai]').length === 2; });
    bang('đổi sang Danh sách thì ô tìm trống', mot(m.goc, '#bdTim').value, '');
    go(m, mot(m.goc, '#bdTim'), 'threads');
    bang('Danh sách lọc theo kênh', m.goc.querySelectorAll('[data-bdbai]').map(function (x) { return x.getAttribute('data-bdbai'); }), ['BD-2']);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})();
