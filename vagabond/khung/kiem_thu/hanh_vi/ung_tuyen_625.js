/* Ca kiểm HÀNH VI v625: trang /ung-tuyen, form 3 bước dựng từ câu hỏi của
 * trình biên tập (mặc định 14 câu form Lark, anh Việt 31/10/2026).
 *
 * Nạp THẬT vagabond/www/ung-tuyen.html và public/web_order/ung-tuyen.js vào
 * DOM giả; chỉ máy chủ là giả (fetch). Câu hỏi lấy từ ĐÚNG hàm Python
 * tuyen_dung_form.mac_dinh() (chạy python3), không chép tay. Bấm, gõ, tích
 * như ứng viên thật, không gọi hàm nội bộ nào "cho chắc" (quy tắc 15).
 *
 * Giữ ba điều v622: bắt buộc tích đồng ý; mất mạng thì gửi lại CÙNG mã và
 * CÙNG dữ liệu (ô khoá lại); vị trí lấy thẳng từ app.
 *
 * Thay ung_tuyen_622.js (form cũ cố định đã bỏ).
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/ung_tuyen_625.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');
var cp = require('child_process');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var HTML = fs.readFileSync(path.join(GOC, 'vagabond', 'www', 'ung-tuyen.html'), 'utf8');
var JS = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'web_order', 'ung-tuyen.js'), 'utf8');
var MAU = JSON.parse(cp.execFileSync('python3', ['-B', '-c',
  'import json,sys; sys.path.insert(0, sys.argv[1]); from vagabond import tuyen_dung_form as tf; ' +
  'print(json.dumps({"cau_hoi": tf.mac_dinh()["cau_hoi"], "buoc": tf.BUOC, "gioi_thieu": tf.GIOI_THIEU_MAC_DINH}, ensure_ascii=False))', GOC]).toString());

var VI_TRI = [
  { ma: 'VTT-0002', tieu_de: 'Sales Online', luong_gon: 'Từ 7,5 triệu/tháng', noi_lam: 'Xưởng Tân Bình', hinh_thuc: 'Toàn thời gian', lien_ket: '/ung-tuyen?vt=VTT-0002' },
  { ma: 'VTT-0001', tieu_de: 'Bếp Pastry', luong_gon: 'Từ 7 triệu · 32.000đ/giờ', noi_lam: 'Xưởng Tân Bình', hinh_thuc: 'Toàn thời gian', lien_ket: '/ung-tuyen?vt=VTT-0001' },
];

var ket = { dat: 0, hong: 0 };
function dung(mo, x) { if (!x) throw new Error(mo); }
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.message)); }
}
async function nghi() { for (var i = 0; i < 20; i++) await Promise.resolve(); await new Promise(function (r) { setImmediate(r); }); }

function FormDataGia() { this.muc = []; }
FormDataGia.prototype.append = function (k, v, ten) { this.muc.push([k, v, ten]); };

function trang(tuy) {
  tuy = tuy || {};
  var tl = dg.taiLieuGia();
  dg.doc(HTML.slice(HTML.indexOf('<main'), HTML.indexOf('</main>') + 7), tl.body);
  /* Trình duyệt hiểu thuộc tính hidden trong HTML là el.hidden = true. */
  (function an(n) { n.children.forEach(function (c) { if (c.attrs && c.attrs.hidden != null) c.hidden = true; an(c); }); })(tl.body);
  var goi = [];
  function tra(status, body) { return Promise.resolve({ ok: status < 300, status: status, json: function () { return Promise.resolve(body); } }); }
  function fetchGia(url, cau) {
    var a = cau && cau.body && typeof cau.body === 'string' ? JSON.parse(cau.body) : (cau && cau.body) || null;
    goi.push({ url: url, a: a, cau: cau });
    if (String(url).indexOf('vi_tri_cong_khai') >= 0) {
      return tra(200, { message: { vi_tri: tuy.viTri || VI_TRI, cau_hoi: tuy.cauHoi || MAU.cau_hoi, buoc: MAU.buoc, gioi_thieu: MAU.gioi_thieu,
        cau_dong_y: 'Tôi đồng ý ... gửi qua dịch vụ AI (Anthropic) ... lưu 12 tháng', cv_toi_da_mb: 8 } });
    }
    if (String(url).indexOf('tai_cv') >= 0) {
      if (tuy.cvLoi) return tra(417, { _server_messages: JSON.stringify([JSON.stringify({ message: 'Chỉ nhận CV dạng PDF, JPG hoặc PNG.' })]) });
      return tra(200, { message: { ma_cv: 'c'.repeat(24), ten: 'cv-binh.pdf', kb: 120 } });
    }
    var tl_ = (tuy.traLoi || []).shift();
    if (tl_ === 'mat_mang') return Promise.reject(new TypeError('Failed to fetch'));
    if (tl_ === 'loi') return tra(417, { exc: 'x', _server_messages: JSON.stringify([JSON.stringify({ message: 'Trả lời câu "Trình độ học vấn cao nhất".' })]) });
    return tra(200, { message: { ok: 1, ma: 'UV-26-10-0007' } });
  }
  var docu = {
    body: tl.body, createElement: tl.createElement, getElementById: tl.getElementById,
    querySelector: function (c) { return c.indexOf('meta') === 0 ? { content: 'csrf-gia' } : tl.querySelector(c); },
    querySelectorAll: function (c) { return tl.querySelectorAll(c); },
  };
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array, Promise: Promise, Set: Set,
    Error: Error, TypeError: TypeError, RegExp: RegExp, Date: Date, URLSearchParams: URLSearchParams, document: docu, fetch: fetchGia,
    FormData: FormDataGia, location: { search: tuy.search || '' }, crypto: { randomUUID: function () { return '1b4e28ba-2fa1-11d2-883f-0016d3cca427'; } } };
  g.window = g;
  vm.createContext(g);
  vm.runInContext(JS, g, { filename: 'ung-tuyen.js' });
  var t = {
    tl: tl, goi: goi,
    id: function (x) { return tl.getElementById(x); },
    bao: function () { return String(tl.getElementById('trang-thai').textContent); },
    cau: function (ma) { return tl.body.querySelectorAll('[data-ma="' + ma + '"]')[0] || null; },
    cacCau: function () { return tl.body.querySelectorAll('.ut-cau').map(function (k) { return k.dataset.ma; }); },
    tiep: async function () { tl.getElementById('ung-tuyen').onsubmit({ preventDefault: function () {} }); await nghi(); },
    bam: async function (el) { el.dispatchEvent(dg.suKien('click', {}, el)); await nghi(); },
    go: function (ma, gt, thu) {
      var o = t.cau(ma).querySelectorAll('input,textarea')[thu || 0];
      o.value = gt; o.oninput && o.oninput(dg.suKien('input', {}, o));
      return o;
    },
    chip: async function (ma, chu) {
      var b = t.cau(ma).querySelectorAll('button').filter(function (x) { return String(x.textContent) === chu; })[0];
      if (!b) throw new Error('không thấy chip ' + chu + ' ở câu ' + ma);
      await t.bam(b);
    },
    post: function () { return goi.filter(function (x) { return /\.ung_tuyen$/.test(String(x.url)); }); },
  };
  return t;
}

async function buoc1(t) {
  t.go('ho_ten', 'Trần Thị Bình');
  await t.chip('gioi_tinh', 'Nữ (Female)');
  t.go('sinh_nhat', '17', 0); t.go('sinh_nhat', '5', 1); t.go('sinh_nhat', '2001', 2);
  t.go('sdt', '0909 123 456');
  t.go('email', 'binh@gmail.com');
  await t.tiep();
}
async function buoc2(t) {
  await t.chip('hoc_van', 'Tốt nghiệp THPT');
  await t.tiep();
}
async function buoc3(t) {
  t.go('luong', '9000000');
  await t.chip('biet_tin', 'Mạng xã hội');
  t.id('dong-y').checked = true;
}

(async function () {
  console.log('v625 trang /ung-tuyen: form 3 bước theo câu hỏi trình biên tập');

  await ca('mở từ nút Ứng tuyển: vị trí chọn sẵn, bước 1 đúng 5 câu Lark, có lời giới thiệu và thanh 3 bước', async function () {
    var t = trang({ search: '?vt=VTT-0002' }); await nghi();
    bang('form hiện', t.id('ung-tuyen').hidden, false);
    bang('tên vị trí', String(t.id('ten-vt').textContent), 'Sales Online');
    bang('bước 1', t.cacCau(), ['ho_ten', 'gioi_tinh', 'sinh_nhat', 'sdt', 'email']);
    bang('nhãn bước', String(t.id('buoc-nhan').textContent), 'BƯỚC 1 / 3');
    bang('thanh tiến độ', t.id('tien').children.map(function (i) { return i.className; }), ['on', '', '']);
    dung('lời giới thiệu', String(t.id('gioi-thieu').textContent).indexOf('Điền vài phút') >= 0 && !t.id('gioi-thieu').hidden);
    dung('câu đồng ý chưa hiện ở bước 1', t.id('khung-dong-y').hidden === true);
    bang('câu bắt buộc có dấu sao', String(t.cau('ho_ten').querySelectorAll('.ut-hoi')[0].textContent), 'Họ và tên ứng viên *');
    bang('không báo lỗi', t.bao(), '');
  });

  await ca('bấm Tiếp tục khi thiếu: nói đúng câu còn thiếu, không sang bước', async function () {
    var t = trang({ search: '?vt=VTT-0002' }); await nghi();
    t.go('ho_ten', 'Bình');
    await t.tiep();
    dung('nhắc câu giới tính', t.bao().indexOf('Bạn tự định nghĩa giới') >= 0);
    bang('vẫn bước 1', String(t.id('buoc-nhan').textContent), 'BƯỚC 1 / 3');
    await t.chip('gioi_tinh', 'Khác...');
    t.go('gioi_tinh', 'Genderfluid');
    t.go('sinh_nhat', '17', 0); t.go('sinh_nhat', '5', 1);
    t.go('sdt', '0909123456'); t.go('email', 'binh@gmail.com');
    await t.tiep();
    dung('ngày dở dang: nhắc đủ ngày tháng năm', t.bao().indexOf('điền đủ ngày, tháng và năm') >= 0);
    t.go('sinh_nhat', '2001', 2); t.go('email', 'binh@');
    await t.tiep();
    dung('email sai', t.bao().indexOf('Kiểm tra lại email') === 0);
    t.go('email', 'binh@gmail.com');
    await t.tiep();
    bang('sang bước 2', String(t.id('buoc-nhan').textContent), 'BƯỚC 2 / 3');
    dung('nút lùi hiện', t.id('lui').hidden === false);
  });

  await ca('đi đủ 3 bước và gửi: đúng dữ liệu (lương bỏ dấu chấm, sinh nhật năm-tháng-ngày), mã lần gửi, CSRF; báo mã hồ sơ', async function () {
    var t = trang({ search: '?vt=VTT-0002' }); await nghi();
    await buoc1(t);
    bang('bước 2 có vị trí, CV', t.cacCau(), ['vi_tri', 'tham_nien', 'thoi_gian', 'hoc_van', 'cv']);
    await buoc2(t);
    bang('bước 3', t.cacCau(), ['luong', 'biet_tin', 'nguoi_gioi_thieu', 'nhan_them']);
    dung('gợi ý lương theo vị trí', String(t.cau('luong').querySelectorAll('.ut-goi')[0].textContent).indexOf('Vị trí này từ 7,5 triệu/tháng') === 0);
    var o = t.go('luong', '9000000');
    bang('ô tiền tự chấm nghìn', o.value, '9.000.000');
    await t.chip('biet_tin', 'Mạng xã hội');
    bang('nút cuối', String(t.id('gui').textContent), 'Gửi hồ sơ');
    await t.tiep();
    dung('chưa tích đồng ý: nhắc', t.bao().indexOf('Tích ô đồng ý') === 0);
    bang('chưa gửi', t.post().length, 0);
    t.id('dong-y').checked = true;
    await t.tiep();
    var p = t.post();
    bang('một lần gửi', p.length, 1);
    var d = p[0].a.du_lieu;
    bang('đầu hồ sơ', [d.vi_tri, d.ma_cv, d.nguon, d.dong_y, d.web], ['VTT-0002', '', 'Web Vagabond', 1, '']);
    bang('câu trả lời', d.tra_loi, { ho_ten: 'Trần Thị Bình', gioi_tinh: 'Nữ (Female)', sinh_nhat: '2001-05-17', sdt: '0909 123 456',
      email: 'binh@gmail.com', hoc_van: 'Tốt nghiệp THPT', luong: '9000000', biet_tin: 'Mạng xã hội' });
    bang('mã lần gửi', p[0].a.ma_lan_gui, '1b4e28ba-2fa1-11d2-883f-0016d3cca427');
    bang('CSRF', p[0].cau.headers['X-Frappe-CSRF-Token'], 'csrf-gia');
    bang('ẩn form, hiện cảm ơn', [t.id('ung-tuyen').hidden, t.id('xong').hidden], [true, false]);
    dung('mã hồ sơ', String(t.id('xong-chu').textContent).indexOf('UV-26-10-0007') >= 0);
  });

  await ca('chọn CV: tải lên ngay, hiện tên tệp, gửi hồ sơ mang mã tạm; máy chủ từ chối tệp thì nói lý do', async function () {
    var t = trang({ search: '?vt=VTT-0002' }); await nghi();
    await buoc1(t);
    var vao = t.cau('cv').querySelectorAll('#tep-cv')[0];
    vao.files = [{ name: 'cv-binh.pdf', type: 'application/pdf', size: 120 * 1024 }];
    vao.onchange(); await nghi(); await nghi();
    var tai = t.goi.filter(function (x) { return /tai_cv$/.test(String(x.url)); });
    bang('một lần tải', tai.length, 1);
    bang('gửi đúng tệp, có CSRF', [tai[0].a.muc[0][0], tai[0].a.muc[0][2], tai[0].cau.headers['X-Frappe-CSRF-Token']], ['tep', 'cv-binh.pdf', 'csrf-gia']);
    dung('hiện tên tệp', String(t.cau('cv').textContent).indexOf('cv-binh.pdf') >= 0 && String(t.cau('cv').textContent).indexOf('Đã tải lên') >= 0);
    await buoc2(t); await buoc3(t); await t.tiep();
    bang('mang mã tạm', t.post()[0].a.du_lieu.ma_cv, 'c'.repeat(24));
    var t2 = trang({ search: '?vt=VTT-0002', cvLoi: 1 }); await nghi();
    await buoc1(t2);
    var v2 = t2.cau('cv').querySelectorAll('#tep-cv')[0];
    v2.files = [{ name: 'cv.docx', type: 'application/pdf', size: 1000 }];
    v2.onchange(); await nghi(); await nghi();
    bang('câu máy chủ', t2.bao(), 'Chỉ nhận CV dạng PDF, JPG hoặc PNG.');
    var v3 = t2.cau('cv').querySelectorAll('#tep-cv')[0];
    v3.files = [{ name: 'to.pdf', type: 'application/pdf', size: 9 * 1024 * 1024 }];
    v3.onchange(); await nghi();
    dung('tệp quá 8 MB chặn ở máy', t2.bao().indexOf('lớn hơn 8 MB') >= 0);
    bang('tệp quá lớn không gửi lên', t2.goi.filter(function (x) { return /tai_cv$/.test(String(x.url)); }).length, 1);
  });

  await ca('mất mạng: báo Gửi lại, ô khoá; lần sau gửi CÙNG mã và CÙNG dữ liệu', async function () {
    var t = trang({ search: '?vt=VTT-0002', traLoi: ['mat_mang'] }); await nghi();
    await buoc1(t); await buoc2(t); await buoc3(t); await t.tiep();
    dung('báo mất kết nối', t.bao().indexOf('Mất kết nối') === 0);
    bang('nút Gửi lại', String(t.id('gui').textContent), 'Gửi lại');
    var o = t.cau('luong').querySelectorAll('input')[0];
    dung('ô đã khoá, nút gửi mở', o.disabled === true && t.id('gui').disabled === false && t.id('dong-y').disabled === true);
    dung('không lùi được', t.id('lui').hidden === true);
    await t.tiep();
    var p = t.post();
    bang('hai lần gửi', p.length, 2);
    bang('cùng mã', p[1].a.ma_lan_gui, p[0].a.ma_lan_gui);
    bang('cùng dữ liệu', p[1].a.du_lieu, p[0].a.du_lieu);
    dung('lần hai thành công', t.id('xong').hidden === false);
  });

  await ca('máy chủ từ chối (thiếu câu): hiện nguyên câu, mở khoá để sửa, lần sau gửi dữ liệu mới', async function () {
    var t = trang({ search: '?vt=VTT-0002', traLoi: ['loi'] }); await nghi();
    await buoc1(t); await buoc2(t); await buoc3(t); await t.tiep();
    dung('câu máy chủ', t.bao().indexOf('Trả lời câu "Trình độ học vấn cao nhất"') === 0);
    dung('ô mở lại', t.cau('luong').querySelectorAll('input')[0].disabled === false);
    t.go('luong', '10000000');
    await t.tiep();
    bang('lần gửi mới mang dữ liệu mới', t.post()[1].a.du_lieu.tra_loi.luong, '10000000');
  });

  await ca('câu chỉ hỏi ở vị trí bếp: đổi vị trí là danh sách câu đổi theo', async function () {
    var them = MAU.cau_hoi.concat([{ ma: 'c_banh01', hoi: 'Bạn đã làm entremet chưa?', goi_y: '', loai: 'chon_mot', lua_chon: ['Rồi', 'Chưa'],
      cho_khac: false, bat_buoc: true, buoc: 2, vi_tri: ['VTT-0001'], ai: true }]);
    var t = trang({ search: '?vt=VTT-0002', cauHoi: them }); await nghi();
    await buoc1(t);
    dung('sales: không có câu bếp', t.cacCau().indexOf('c_banh01') < 0);
    await t.bam(t.tl.body.querySelectorAll('[data-vt="VTT-0001"]')[0]);
    dung('bếp: có câu bếp', t.cacCau().indexOf('c_banh01') >= 0);
    bang('tên vị trí đổi', String(t.id('ten-vt').textContent), 'Bếp Pastry');
    await t.chip('hoc_van', 'Tốt nghiệp THPT');
    await t.tiep();
    dung('câu bếp bắt buộc', t.bao().indexOf('entremet') >= 0);
  });

  await ca('quét QR ở cửa hàng: nguồn QR; mở link vị trí đã tắt: báo, vẫn chọn được vị trí khác', async function () {
    var t = trang({ search: '?vt=VTT-0002&nguon=qr' }); await nghi();
    await buoc1(t); await buoc2(t); await buoc3(t); await t.tiep();
    bang('nguồn', t.post()[0].a.du_lieu.nguon, 'QR tại cửa hàng');
    var t2 = trang({ search: '?vt=VTT-0009' }); await nghi();
    dung('báo ngừng nhận', t2.bao().indexOf('đã ngừng nhận hồ sơ') >= 0);
    await buoc1(t2);
    await t2.chip('hoc_van', 'Tốt nghiệp THPT');
    await t2.tiep();
    dung('bước 2 bắt chọn vị trí', t2.bao().indexOf('Chọn vị trí') === 0);
  });

  await ca('app tắt hết vị trí: báo chưa có vị trí, không hiện form', async function () {
    var t = trang({ viTri: [] }); await nghi();
    dung('báo', t.bao().indexOf('chưa có vị trí nào đang tuyển') >= 0);
    dung('form ẩn', t.id('ung-tuyen').hidden !== false);
  });

  console.log('\n' + ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng.');
  process.exit(ket.hong ? 1 : 0);
})().catch(function (e) { console.log('NO TUNG: ' + (e && e.stack || e)); process.exit(1); });
