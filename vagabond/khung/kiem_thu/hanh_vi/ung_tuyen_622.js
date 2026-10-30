/* Ca kiểm HÀNH VI v622: trang /ung-tuyen (form nộp hồ sơ của mục Tuyển dụng).
 *
 * Nạp THẬT vagabond/www/ung-tuyen.html và public/web_order/ung-tuyen.js vào
 * DOM giả; chỉ máy chủ là giả (fetch). Bấm, gõ, tích như ứng viên thật, không
 * gọi hàm nội bộ nào "cho chắc" (quy tắc 15).
 *
 * Giữ ba điều anh Việt chốt 30/10/2026: vị trí lấy thẳng từ app (bật tắt trên
 * app là trang đổi theo), BẮT BUỘC tích đồng ý lưu hồ sơ, và mất mạng thì gửi
 * lại CÙNG mã lần gửi để máy chủ không tạo hồ sơ thứ hai.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/ung_tuyen_622.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var HTML = fs.readFileSync(path.join(GOC, 'vagabond', 'www', 'ung-tuyen.html'), 'utf8');
var JS = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'web_order', 'ung-tuyen.js'), 'utf8');

var VI_TRI = [
  { id: 'erp-td-VTT-0001', loai: 'tuyen_dung', tieu_de: 'Thu ngân ca tối', noi_dung: 'Tính tiền, đóng gói.', yeu_cau: 'Mức lương: 25.000 đ/giờ\nNhanh nhẹn',
    noi_lam: 'The Vagabond District 1', hinh_thuc: 'Bán thời gian', ket_thuc: '2026-11-15', lien_ket: '/ung-tuyen?vt=VTT-0001' },
  { id: 'erp-td-VTT-0003', loai: 'tuyen_dung', tieu_de: 'Phụ bếp Pastry', noi_dung: '', yeu_cau: '', noi_lam: 'Xưởng sản xuất Tân Bình',
    hinh_thuc: 'Toàn thời gian', ket_thuc: '', lien_ket: '/ung-tuyen?vt=VTT-0003' },
];

var ket = { dat: 0, hong: 0 };
function dung(mo, x) { if (!x) throw new Error(mo); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message)); }
}
async function nghi() { for (var i = 0; i < 20; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

function trang(tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc(HTML.slice(HTML.indexOf('<main'), HTML.indexOf('</main>') + 7), tl.body);
  var goi = [];
  function tra(status, body) { return Promise.resolve({ ok: status < 300, status: status, json: function () { return Promise.resolve(body); } }); }
  function fetchGia(url, cau) {
    var a = cau && cau.body ? JSON.parse(cau.body) : null;
    goi.push({ url: url, a: a, cau: cau });
    if (String(url).indexOf('vi_tri_cong_khai') >= 0) {
      return tra(200, { message: { vi_tri: tuy.viTri || VI_TRI, ca_ranh: ['Sáng', 'Chiều', 'Tối', 'Cuối tuần', 'Linh hoạt'], cau_dong_y: 'Tôi đồng ý ... lưu hồ sơ trong 12 tháng ...', thang_luu: 12 } });
    }
    var tl_ = (tuy.traLoi || []).shift();
    if (tl_ === 'mat_mang') return Promise.reject(new TypeError('Failed to fetch'));
    if (tl_ === 'loi') return tra(417, { exc: 'x', _server_messages: JSON.stringify([JSON.stringify({ message: 'Vị trí này đã ngừng nhận hồ sơ. Chọn một vị trí khác đang tuyển.' })]) });
    return tra(200, { message: { ok: 1, ma: 'UV-26-10-0007' } });
  }
  var docu = {
    body: tl.body, createElement: tl.createElement, getElementById: tl.getElementById,
    querySelector: function (c) { return c.indexOf('meta') === 0 ? { content: 'csrf-gia' } : tl.querySelector(c); },
    querySelectorAll: function (c) { return tl.querySelectorAll(c); },
  };
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise,
    Error: Error, TypeError: TypeError, RegExp: RegExp, Date: Date, URLSearchParams: URLSearchParams, document: docu, fetch: fetchGia,
    location: { search: tuy.search || '' }, crypto: { randomUUID: function () { return '1b4e28ba-2fa1-11d2-883f-0016d3cca427'; } } };
  g.window = g;
  vm.createContext(g);
  vm.runInContext(JS, g, { filename: 'ung-tuyen.js' });
  return {
    tl: tl, goi: goi,
    id: function (x) { return tl.getElementById(x); },
    bao: function () { return String(tl.getElementById('trang-thai').textContent); },
    gui: async function () { var f = tl.getElementById('ung-tuyen'); f.onsubmit({ preventDefault: function () {} }); await nghi(); },
    bam: async function (el) { el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); },
    post: function () { return goi.filter(function (x) { return String(x.url).indexOf('ung_tuyen') >= 0; }); },
  };
}

function dien(t) {
  t.id('ho-ten').value = 'Nguyễn Văn An';
  t.id('sdt').value = '0909 123 456';
  t.id('dong-y').checked = true;
}

(async function () {
  console.log('v622 trang /ung-tuyen: vị trí từ app, bắt buộc đồng ý, gửi lại cùng mã');

  await ca('mở từ nút Ứng tuyển của một vị trí: hai vị trí từ app, vị trí đó được chọn sẵn, hiện mô tả và câu đồng ý', async function () {
    var t = trang({ search: '?vt=VTT-0001' }); await nghi();
    bang('form hiện', t.id('ung-tuyen').hidden, false);
    var nut = t.tl.body.querySelectorAll('[data-vt]');
    bang('hai vị trí', nut.map(function (b) { return b.dataset.vt; }), ['VTT-0001', 'VTT-0003']);
    bang('chọn sẵn', nut.map(function (b) { return b.getAttribute('aria-pressed'); }), ['true', 'false']);
    dung('dòng phụ có nơi làm và hạn', String(nut[0].textContent).indexOf('The Vagabond District 1 · Bán thời gian · hạn 15/11/2026') >= 0);
    dung('mô tả, lương', String(t.id('vt-chi-tiet').textContent).indexOf('Mức lương: 25.000 đ/giờ') >= 0);
    dung('câu đồng ý từ máy chủ', String(t.id('cau-dong-y').textContent).indexOf('12 tháng') >= 0);
    bang('không báo lỗi', t.bao(), '');
  });

  await ca('chưa tích đồng ý thì không gửi, nhắc tích', async function () {
    var t = trang({ search: '?vt=VTT-0001' }); await nghi();
    t.id('ho-ten').value = 'An'; t.id('sdt').value = '0909123456';
    await t.gui();
    bang('không gọi máy chủ', t.post().length, 0);
    dung('nhắc', t.bao().indexOf('Tích ô đồng ý') === 0);
  });

  await ca('chưa chọn vị trí (nhiều vị trí, mở thẳng trang) thì nhắc chọn', async function () {
    var t = trang(); await nghi();
    dien(t);
    await t.gui();
    bang('không gọi', t.post().length, 0);
    dung('nhắc chọn vị trí', t.bao().indexOf('Chọn vị trí') === 0);
  });

  await ca('gửi đủ: đúng vị trí, ca rảnh nhiều chip, nguồn web, đồng ý 1, mã lần gửi; báo mã hồ sơ', async function () {
    var t = trang({ search: '?vt=VTT-0001' }); await nghi();
    dien(t);
    var ca_ = t.tl.body.querySelectorAll('#ca-ranh')[0].children;
    await t.bam(ca_[2]); await t.bam(ca_[3]); await t.bam(ca_[0]); await t.bam(ca_[0]);
    await t.gui();
    var p = t.post();
    bang('một lần gửi', p.length, 1);
    var d = p[0].a.du_lieu;
    bang('dữ liệu', [d.vi_tri, d.ho_ten, d.sdt, d.ca_ranh, d.nguon, d.dong_y, d.web], ['VTT-0001', 'Nguyễn Văn An', '0909 123 456', ['Tối', 'Cuối tuần'], 'Web Vagabond', 1, '']);
    bang('mã lần gửi', p[0].a.ma_lan_gui, '1b4e28ba-2fa1-11d2-883f-0016d3cca427');
    bang('có CSRF', p[0].cau.headers['X-Frappe-CSRF-Token'], 'csrf-gia');
    dung('báo đã nhận kèm mã', t.bao().indexOf('Đã nhận hồ sơ UV-26-10-0007') === 0);
    bang('ẩn form', t.id('ung-tuyen').hidden, true);
  });

  await ca('quét mã QR ở cửa hàng: nguồn ghi QR tại cửa hàng', async function () {
    var t = trang({ search: '?vt=VTT-0003&nguon=qr' }); await nghi();
    dien(t);
    await t.gui();
    bang('nguồn', t.post()[0].a.du_lieu.nguon, 'QR tại cửa hàng');
  });

  await ca('mất mạng: báo gửi lại, lần sau gửi CÙNG mã và cùng dữ liệu (máy chủ trả hồ sơ cũ, không tạo thêm)', async function () {
    var t = trang({ search: '?vt=VTT-0001', traLoi: ['mat_mang'] }); await nghi();
    dien(t);
    await t.gui();
    dung('báo mất kết nối', t.bao().indexOf('Mất kết nối') === 0);
    bang('nút Gửi lại', String(t.id('gui').textContent), 'Gửi lại');
    dung('ô đã khoá để không sửa dở', t.id('ho-ten').disabled === true && t.id('gui').disabled === false);
    t.id('ho-ten').value = 'Tên khác';
    await t.gui();
    var p = t.post();
    bang('hai lần gửi', p.length, 2);
    bang('cùng mã', p[1].a.ma_lan_gui, p[0].a.ma_lan_gui);
    bang('cùng dữ liệu', p[1].a.du_lieu, p[0].a.du_lieu);
    dung('lần hai thành công', t.bao().indexOf('Đã nhận hồ sơ') === 0);
  });

  await ca('máy chủ từ chối (vị trí vừa tắt): hiện nguyên câu, mở lại form để chọn vị trí khác', async function () {
    var t = trang({ search: '?vt=VTT-0001', traLoi: ['loi'] }); await nghi();
    dien(t);
    await t.gui();
    dung('câu máy chủ', t.bao().indexOf('Vị trí này đã ngừng nhận hồ sơ') === 0);
    dung('form mở lại', t.id('ho-ten').disabled === false && t.id('ung-tuyen').hidden === false);
    await t.bam(t.tl.body.querySelectorAll('[data-vt="VTT-0003"]')[0]);
    await t.gui();
    bang('lần gửi mới dùng vị trí mới', t.post()[1].a.du_lieu.vi_tri, 'VTT-0003');
  });

  await ca('mở link vị trí đã tắt trên app: báo ngừng nhận, vẫn cho chọn vị trí khác', async function () {
    var t = trang({ search: '?vt=VTT-0002' }); await nghi();
    dung('báo', t.bao().indexOf('đã ngừng nhận hồ sơ') >= 0);
    bang('form vẫn hiện', t.id('ung-tuyen').hidden, false);
    bang('không vị trí nào chọn sẵn', t.tl.body.querySelectorAll('[data-vt]').map(function (b) { return b.getAttribute('aria-pressed'); }), ['false', 'false']);
  });

  await ca('app tắt hết vị trí: trang báo chưa có vị trí, không hiện form', async function () {
    var t = trang({ viTri: [] }); await nghi();
    dung('báo', t.bao().indexOf('chưa có vị trí nào đang tuyển') >= 0);
    dung('form ẩn', t.id('ung-tuyen').hidden !== false);
  });

  await ca('một vị trí duy nhất thì chọn sẵn', async function () {
    var t = trang({ viTri: [VI_TRI[1]] }); await nghi();
    bang('chọn sẵn', t.tl.body.querySelectorAll('[data-vt]')[0].getAttribute('aria-pressed'), 'true');
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})().catch(function (e) { console.log('NO TUNG: ' + (e && e.stack || e)); process.exit(1); });
