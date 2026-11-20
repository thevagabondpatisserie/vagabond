/* Ca kiểm HÀNH VI v664: âm báo tiền chuyển khoản về (anh Việt 16/11/2026,
 * "giọng người đọc đã nhận chuyển khoản bằng tiếng Anh cho sang").
 *
 * Nạp THẬT 66-goi-mon-tai-ban.js, 77-chuong-mau.js và hai hàm của màn tính tiền
 * (posPollBat: màn bill đang chờ tiền; posQrSheet: bảng mã QR sau khi lưu bill)
 * vào DOM giả. Âm báo là tệp thu sẵn: fetch giả đọc đúng tệp mp3 trong repo,
 * AudioContext giả ghi lại tệp đã phát và đếm hồi chuông tổng hợp. setInterval và
 * setTimeout giả để chạy đúng lượt hỏi SePay mà không chờ 5 giây thật.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/tien_ve_664.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js');

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

var MA = ['h', 'money'].map(function (t) { return layHam(NEN, t); }).join('\n') + '\n' +
  'var posPollId = null, posSepayNhan = 0, posSepayGoiY = 0;\n' +
  ['posPollTat', 'posPollBat', 'flt0', 'posQrSheet', 'posCfgCk', 'posLaCk', 'posTkCk'].map(function (t) { return layHam(POS, t); }).join('\n') + '\n' +
  doc('66-goi-mon-tai-ban.js') + '\n' + doc('77-chuong-mau.js');

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n        ') : e)); }
}
function nho() {
  var kho = {};
  return { getItem: function (k) { return k in kho ? kho[k] : null; }, setItem: function (k, v) { kho[k] = String(v); },
    removeItem: function (k) { delete kho[k]; }, _kho: kho };
}

/* o.ss: sessionStorage dùng chung (tải lại trang); o.sepay: hàm trả kết quả
   pos_kiem_sepay theo lượt hỏi; o.giaiMaHong: số lần giải mã đầu bị hỏng;
   o.khongOffline: máy không có OfflineAudioContext. fetch giả chỉ để ghi lại:
   âm báo nằm trong app, không được tải qua mạng (anh Việt 16/11). */
function dung_may(o) {
  o = o || {};
  var tai = dg.taiLieuGia(), keu = [], phat = [], tai_tep = [], hen = [], lap = [], nghe = [];
  var posNd = new dg.ElementGia('div'); posNd.setAttribute('id', 'posNd');
  tai.body.appendChild(posNd);
  tai.body.contains = function (el) { var x = el; while (x) { if (x === tai.body) return true; x = x.parentNode; } return false; };
  tai.addEventListener = function (loai, f) { nghe.push([loai, f]); };
  tai.removeEventListener = function (loai, f) { nghe = nghe.filter(function (x) { return x[1] !== f; }); };
  var luot = 0, ve = [];
  var g = {
    console: console, document: tai, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, isNaN: isNaN, parseInt: parseInt, parseFloat: parseFloat,
    encodeURIComponent: encodeURIComponent, Error: Error,
    localStorage: o.ls || nho(), sessionStorage: o.ss || nho(),
    setTimeout: function (f) { hen.push(f); return hen.length; },
    setInterval: function (f) { lap.push(f); return lap.length; }, clearInterval: function (id) { lap[id - 1] = null; },
    toast: function () {}, go: function (f) { ve.push(f); }, scrPosQuay: function () {},
    posTaiKhoan: function () { return { ten: 'Vagabond', bank: 'MB', stk: '0001' }; }, posQrUrl: function () { return ''; },
    posQrLoi: function () { return ''; }, posNutIn: function () { return ''; }, posBillVua: null, siName: null,
    api: function (duong, args) {
      if (duong !== 'vagabond.ban_hang.pos_kiem_sepay') return Promise.reject(new Error('api la: ' + duong));
      luot++;
      return Promise.resolve((o.sepay || function (l, a) { return { nhan: a.tien, du: 1 }; })(luot, args));
    },
    fetch: function (url) { tai_tep.push(url); return Promise.reject(new Error('khong duoc tai qua mang')); },
    atob: function (b) { return Buffer.from(b, 'base64').toString('latin1'); }, Uint8Array: Uint8Array
  };
  g.window = g;
  var hong = o.giaiMaHong || 0, giai_ma = [];
  /* Bộ giải mã giả: nhận đúng byte mp3 (đầu tệp ID3 hay khung MPEG), ghi lại byte. */
  function giaiMa(b, ok, loi) {
    var u = new Uint8Array(b), mp3 = (u[0] === 0x49 && u[1] === 0x44 && u[2] === 0x33) || (u[0] === 0xFF && (u[1] & 0xE0) === 0xE0);
    giai_ma.push(u.length);
    if (hong > 0) { hong--; var e0 = new Error('giai ma hong'); loi(e0); return Promise.reject(e0); }
    var buf = { byte: u.length, sha1: require('crypto').createHash('sha1').update(Buffer.from(u)).digest('hex'), duration: 3.2 };
    if (mp3) { ok(buf); return Promise.resolve(buf); }
    var e = new Error('khong phai mp3'); loi(e); return Promise.reject(e);
  }
  if (!o.khongOffline) g.window.OfflineAudioContext = function () { return { decodeAudioData: giaiMa }; };
  g.window.AudioContext = function () {
    var ac = { currentTime: 0, state: 'running', destination: {}, resume: function () {},
      createOscillator: function () { return { frequency: {}, connect: function () {}, start: function () {}, stop: function () {} }; },
      createGain: function () { var gn = { gain: { value: 1, setValueAtTime: function () {}, linearRampToValueAtTime: function () {}, exponentialRampToValueAtTime: function () {} },
        connect: function (dich) { if (dich === ac.destination && gn.gain.value === 0.32) keu.push(1); } }; return gn; },
      decodeAudioData: giaiMa,
      createBufferSource: function () { var s = { connect: function () {}, start: function () { phat.push(s.buffer); } }; return s; } };
    return ac;
  };
  vm.runInNewContext(MA, g, { filename: 'tien-ve.js' });
  async function hoi() {
    for (var i = 0; i < lap.length; i++) if (lap[i]) await lap[i]();
    for (var k = 0; k < 10; k++) await new Promise(function (r) { setImmediate(r); });
    while (hen.length) hen.shift()();
  }
  return { g: g, tai: tai, keu: keu, phat: phat, tai_tep: tai_tep, giai_ma: giai_ma, nghe: function () { return nghe; }, hoi: hoi, luot: function () { return luot; } };
}

var TEP = path.join(GOC, 'vagabond', 'public', 'am_thanh', 'tien-ve-payment-received.mp3');

(async function () {
  console.log('v664 âm báo tiền chuyển khoản về (tệp thu sẵn mẫu 2 anh Việt chọn, nằm trong app)');

  await ca('hai mẫu: Payment received (mặc định) và Chỉ chuông; mẫu cũ đã lưu trên máy (so_tien...) về mặc định', function () {
    var m = dung_may();
    bang('mẫu', m.g.TIEN_MAU_BAO.map(function (x) { return x.ma; }), ['giong', 'chi_chuong']);
    bang('mặc định', m.g.tienMauBao(), 'giong');
    m.g.TIEN_MAU_BAO.forEach(function (x) { dung('mẫu ' + x.ma + ' có tên và mô tả có dấu', x.ten && x.mo_ta && /[àáảãạâăđêôơưéèíóúý]/i.test(x.mo_ta)); });
    var ls = nho(); ls.setItem('vgb_tien_mau_bao', 'so_tien');
    bang('giá trị cũ', dung_may({ ls: ls }).g.tienMauBao(), 'giong');
  });

  await ca('âm báo nằm ngay trong app: trùng từng byte tệp mp3 anh đã nghe (sha1), không tải qua mạng', async function () {
    var m = dung_may();
    var tep = fs.readFileSync(TEP), sha = require('crypto').createHash('sha1').update(tep).digest('hex');
    bang('byte trong app', Buffer.from(m.g.TIEN_AM_B64, 'base64').equals(tep), true);
    bang('sha1 tệp đã duyệt', sha, '02c3e730b4fecdabc4766556dea6ac02558722cd');
    m.g.posQrSheet('BILL-0', 50000, null, '', 'TCV');
    await m.hoi();
    bang('phát đúng tệp', m.phat.map(function (b) { return b.sha1; }), [sha]);
    bang('không gọi mạng', m.tai_tep, []);
  });

  await ca('mở app chưa chạm gì: đã giải mã sẵn trong nền; tiền về là phát ngay trong cùng lượt, không chờ', async function () {
    var m = dung_may();
    await m.hoi();
    bang('giải mã một lần lúc mở app', m.giai_ma.length, 1);
    m.g.tienBao(50000, 'ck:BILL-9');
    bang('phát ngay', m.phat.length, 1);
    m.g.posQrSheet('BILL-10', 50000, null, '', 'TCV');
    await m.hoi();
    bang('bill sau không giải mã lại', [m.phat.length, m.giai_ma.length], [2, 1]);
  });

  await ca('màn bill đang chờ chuyển khoản: SePay báo đủ thì phát tệp "Payment received. Thank you." đúng một lần, không kêu thêm chuông tổng hợp', async function () {
    var m = dung_may({ sepay: function (l) { return l === 1 ? { nhan: 0 } : { nhan: 95000, du: 1 }; } });
    m.g.posPollBat('TCVG8FRJ', 95000);
    await m.hoi();
    bang('chưa đủ tiền thì im', [m.phat.length, m.keu.length], [0, 0]);
    await m.hoi();
    bang('phát tệp', m.phat.length, 1);
    bang('đúng byte tệp thật', m.phat[0].byte, fs.statSync(TEP).size);
    bang('không chuông tổng hợp', m.keu.length, 0);
    await m.hoi();
    bang('đủ rồi thì thôi hỏi SePay, không phát lại', [m.luot(), m.phat.length], [2, 1]);
  });

  await ca('bảng mã QR sau khi lưu bill và màn bill cùng thấy tiền về cho một bill: chỉ báo một lần; bảng QR vẫn hiện ĐÃ NHẬN ĐỦ', async function () {
    var m = dung_may();
    m.g.posPollBat('TCVG8FRJ', 95000);
    m.g.posQrSheet('TCVG8FRJ', 95000, null, '', 'TCV');
    await m.hoi();
    bang('một lần', m.phat.length + m.keu.length, 1);
    var bao = m.tai.body.querySelector('#qrsBao');
    dung('bảng QR báo đủ', bao && /ĐÃ NHẬN ĐỦ 95/.test(bao.innerHTML));
  });

  await ca('bill khác thì báo riêng, tệp chỉ giải mã một lần; tải lại trang khi bill cũ còn mở thì không báo lại bill cũ', async function () {
    var ss = nho();
    var m = dung_may({ ss: ss });
    m.g.posQrSheet('BILL-1', 95000, null, '', 'TCV');
    await m.hoi();
    m.g.posQrSheet('BILL-2', 120000, null, '', 'TCV');
    await m.hoi();
    bang('hai bill hai lần', m.phat.length, 2);
    bang('giải mã một lần', m.giai_ma.length, 1);
    var m2 = dung_may({ ss: ss });
    m2.g.posPollBat('BILL-1', 95000);
    await m2.hoi();
    bang('tải lại không báo lại', [m2.phat.length, m2.keu.length], [0, 0]);
  });

  await ca('giải mã hỏng: vẫn kêu chuông thay; bill sau giải mã lại và phát được', async function () {
    var m = dung_may({ giaiMaHong: 2 });
    await m.hoi();
    m.g.posQrSheet('BILL-3', 50000, null, '', 'TCV');
    await m.hoi();
    bang('chuông thay tệp', [m.keu.length, m.phat.length], [1, 0]);
    m.g.posQrSheet('BILL-4', 50000, null, '', 'TCV');
    await m.hoi();
    bang('lần sau phát được', m.phat.length, 1);
  });

  await ca('máy không có OfflineAudioContext: lần chạm đầu vào app mở loa và giải mã, tiền về phát ngay', async function () {
    var m = dung_may({ khongOffline: true });
    await m.hoi();
    bang('chưa giải mã', m.giai_ma.length, 0);
    var ds = m.nghe().filter(function (x) { return x[0] === 'click'; });
    bang('có nghe lần chạm đầu', ds.length, 1);
    ds[0][1]();
    await m.hoi();
    bang('giải mã ở lần chạm', m.giai_ma.length, 1);
    bang('chạm xong thì thôi nghe', m.nghe().filter(function (x) { return x[0] === 'click'; }).length, 0);
    m.g.tienBao(50000, 'ck:BILL-7');
    bang('phát ngay', m.phat.length, 1);
  });

  await ca('bảng Chọn chuông: khối Âm báo tiền 2 chip cao 44; chọn Chỉ chuông thì lưu trên máy, nghe thử là chuông; bill thật theo mẫu đã chọn', async function () {
    var m = dung_may();
    m.g.gmbMoChonChuong();
    var ds = m.tai.body.children, ov = ds[ds.length - 1];
    var chip = ov.querySelectorAll('[data-tienmau]');
    bang('hai chip', chip.length, 2);
    chip.forEach(function (c) { dung('chip cao 44: ' + c.getAttribute('data-tienmau'), /min-height:44px/.test(c.getAttribute('style') || '')); });
    dung('nút Nghe thử', ov.querySelector('[data-tiennghe]'));
    ov.onclick({ target: ov.querySelector('[data-tiennghe]') });
    await m.hoi();
    bang('nghe thử mặc định là tệp', [m.phat.length, m.keu.length], [1, 0]);
    ov.onclick({ target: ov.querySelector('[data-tienmau="chi_chuong"]') });
    await m.hoi();
    bang('lưu trên máy', m.g.localStorage.getItem('vgb_tien_mau_bao'), 'chi_chuong');
    bang('nghe ngay: chuông', [m.phat.length, m.keu.length], [1, 1]);
    var ov2 = m.tai.body.children[m.tai.body.children.length - 1];
    bang('chip vừa chọn sáng lên', ov2.querySelector('[data-tienmau="chi_chuong"]').getAttribute('aria-pressed'), 'true');
    m.g.posQrSheet('BILL-5', 70000, null, '', 'TCV');
    await m.hoi();
    bang('bill thật: chuông, không phát tệp', [m.phat.length, m.keu.length], [1, 2]);
  });

  await ca('bảng mã QR có nút Đổi âm báo tiền về cao 44, bấm mở bảng Chọn chuông và âm báo', async function () {
    var m = dung_may();
    m.g.posQrSheet('BILL-6', 70000, null, '', 'TCV');
    var ds = m.tai.body.children, qr = ds[ds.length - 1];
    var nut = qr.querySelector('[data-amchon]');
    dung('có nút', nut && /min-height:44px/.test(nut.getAttribute('style')));
    await qr.onclick({ target: nut });
    var moi = m.tai.body.children[m.tai.body.children.length - 1];
    dung('mở bảng chọn', moi !== qr && moi.querySelectorAll('[data-tienmau]').length === 2);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})();
