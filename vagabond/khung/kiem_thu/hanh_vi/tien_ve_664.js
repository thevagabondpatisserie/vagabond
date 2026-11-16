/* Ca kiểm HÀNH VI v664: âm báo tiền chuyển khoản về (anh Việt 16/11/2026,
 * "giọng người đọc đã nhận chuyển khoản bằng tiếng Anh cho sang").
 *
 * Nạp THẬT 66-goi-mon-tai-ban.js, 77-chuong-mau.js và hai hàm của màn tính tiền
 * (posPollBat: màn bill đang chờ tiền; posQrSheet: bảng mã QR sau khi lưu bill)
 * vào DOM giả. Giọng đọc là speechSynthesis giả ghi lại câu và giọng đã chọn;
 * chuông là AudioContext giả đếm số nút tổng nối vào loa. setInterval và
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
  ['posPollTat', 'posPollBat', 'flt0', 'posQrSheet'].map(function (t) { return layHam(POS, t); }).join('\n') + '\n' +
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

/* o.giong: danh sách giọng của máy; o.ss: sessionStorage dùng chung (tải lại trang);
   o.sepay: hàm trả kết quả pos_kiem_sepay theo lượt hỏi. */
function dung_may(o) {
  o = o || {};
  var tai = dg.taiLieuGia(), keu = [], noi = [], hen = [], lap = [];
  var posNd = new dg.ElementGia('div'); posNd.setAttribute('id', 'posNd');
  tai.body.appendChild(posNd);
  tai.body.contains = function (el) { var x = el; while (x) { if (x === tai.body) return true; x = x.parentNode; } return false; };
  var luot = 0, ve = [];
  var g = {
    console: console, document: tai, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
    RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, isNaN: isNaN, parseInt: parseInt, parseFloat: parseFloat,
    encodeURIComponent: encodeURIComponent,
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
    }
  };
  g.window = g;
  g.window.AudioContext = function () {
    var ac = { currentTime: 0, state: 'running', destination: {}, resume: function () {},
      createOscillator: function () { return { frequency: {}, connect: function () {}, start: function () {}, stop: function () {} }; },
      createGain: function () { return { gain: { value: 1, setValueAtTime: function () {}, linearRampToValueAtTime: function () {}, exponentialRampToValueAtTime: function () {} },
        connect: function (dich) { if (dich === ac.destination) keu.push(1); } }; } };
    return ac;
  };
  if (o.coGiong !== false) {
    g.window.SpeechSynthesisUtterance = function (cau) { this.text = cau; };
    g.window.speechSynthesis = { getVoices: function () { return o.giong || []; }, cancel: function () {},
      speak: function (u) { noi.push({ cau: u.text, giong: u.voice ? u.voice.name : null, lang: u.lang }); } };
  }
  vm.runInNewContext(MA, g, { filename: 'tien-ve.js' });
  async function hoi() {
    for (var i = 0; i < lap.length; i++) if (lap[i]) await lap[i]();
    for (var k = 0; k < 5; k++) await Promise.resolve();
    while (hen.length) hen.shift()();
  }
  return { g: g, tai: tai, keu: keu, noi: noi, hoi: hoi, luot: function () { return luot; }, posNd: posNd };
}

var GIONG_IPAD = [{ name: 'Linh', lang: 'vi-VN' }, { name: 'Samantha', lang: 'en-US' }, { name: 'Daniel', lang: 'en-GB' },
  { name: 'Karen', lang: 'en-AU' }];

(async function () {
  console.log('v664 âm báo tiền chuyển khoản về');

  await ca('câu đọc của từng mẫu: số tiền viết 95,000 để giọng Anh đọc đúng; không có số tiền thì đọc câu cảm ơn; Chỉ chuông không đọc', function () {
    var m = dung_may();
    bang('đọc số tiền', m.g.tienCauDoc('so_tien', 95000), 'Payment received, 95,000 dong.');
    bang('số lớn', m.g.tienCauDoc('so_tien', 1250000.4), 'Payment received, 1,250,000 dong.');
    bang('không số tiền', m.g.tienCauDoc('so_tien', 0), 'Payment received. Thank you.');
    bang('cảm ơn', m.g.tienCauDoc('cam_on', 95000), 'Payment received. Thank you.');
    bang('chuyển khoản', m.g.tienCauDoc('chuyen_khoan', 95000), 'Bank transfer received.');
    bang('xác nhận', m.g.tienCauDoc('xac_nhan', 95000), 'Payment confirmed.');
    bang('chỉ chuông', m.g.tienCauDoc('chi_chuong', 95000), '');
    bang('năm mẫu, mặc định đọc số tiền', [m.g.TIEN_MAU_BAO.length, m.g.tienMauBao()], [5, 'so_tien']);
    m.g.TIEN_MAU_BAO.forEach(function (x) { dung('mẫu ' + x.ma + ' có tên và mô tả có dấu', x.ten && x.mo_ta && /[àáảãạâăđêôơưéèíóúý]/i.test(x.mo_ta)); });
  });

  await ca('chọn giọng: iPad có Daniel (Anh-Anh) thì chọn Daniel, không chọn giọng Việt hay Mỹ; giọng Premium đứng trước; máy không có giọng Anh thì không có giọng', function () {
    var m = dung_may();
    bang('iPad', m.g.tienChonGiong(GIONG_IPAD).name, 'Daniel');
    bang('Serena trước Daniel', m.g.tienChonGiong(GIONG_IPAD.concat([{ name: 'Serena (Premium)', lang: 'en-GB' }])).name, 'Serena (Premium)');
    bang('Edge Windows', m.g.tienChonGiong([{ name: 'Microsoft David', lang: 'en-US' }, { name: 'Microsoft Sonia Online (Natural) - English (United Kingdom)', lang: 'en-GB' }]).name,
      'Microsoft Sonia Online (Natural) - English (United Kingdom)');
    bang('Android lạ: Anh-Anh trước Úc', m.g.tienChonGiong([{ name: 'English Australia', lang: 'en-AU' }, { name: 'English UK', lang: 'en_GB' }]).name, 'English UK');
    bang('không giọng Anh', m.g.tienChonGiong([{ name: 'Linh', lang: 'vi-VN' }]), null);
    bang('danh sách rỗng', m.g.tienChonGiong([]), null);
  });

  await ca('màn bill đang chờ chuyển khoản: SePay báo đủ thì kêu chuông rồi đọc "Payment received, 95,000 dong" bằng giọng Daniel, đúng một lần', async function () {
    var m = dung_may({ giong: GIONG_IPAD, sepay: function (l) { return l === 1 ? { nhan: 0 } : { nhan: 95000, du: 1 }; } });
    m.g.posPollBat('TCVG8FRJ', 95000);
    await m.hoi();
    bang('chưa đủ tiền thì im', [m.keu.length, m.noi.length], [0, 0]);
    await m.hoi();
    bang('một hồi chuông', m.keu.length, 1);
    bang('đọc', m.noi, [{ cau: 'Payment received, 95,000 dong.', giong: 'Daniel', lang: 'en-GB' }]);
    await m.hoi();
    bang('đủ rồi thì thôi hỏi SePay, không đọc lại', [m.luot(), m.noi.length], [2, 1]);
  });

  await ca('bảng mã QR sau khi lưu bill và màn bill cùng thấy tiền về cho một bill: chỉ báo một lần; bảng QR vẫn hiện ĐÃ NHẬN ĐỦ', async function () {
    var m = dung_may({ giong: GIONG_IPAD });
    m.g.posPollBat('TCVG8FRJ', 95000);
    m.g.posQrSheet('TCVG8FRJ', 95000, null, '', 'TCV');
    await m.hoi();
    bang('một chuông, một câu', [m.keu.length, m.noi.length], [1, 1]);
    var bao = m.tai.body.querySelector('#qrsBao');
    dung('bảng QR báo đủ', bao && /ĐÃ NHẬN ĐỦ 95/.test(bao.innerHTML));
  });

  await ca('bill khác thì báo riêng; tải lại trang khi bill cũ còn mở thì không đọc lại bill cũ', async function () {
    var ss = nho();
    var m = dung_may({ giong: GIONG_IPAD, ss: ss });
    m.g.posQrSheet('BILL-1', 95000, null, '', 'TCV');
    await m.hoi();
    m.g.posQrSheet('BILL-2', 120000, null, '', 'TCV');
    await m.hoi();
    bang('hai bill hai lần', m.noi.length, 2);
    var m2 = dung_may({ giong: GIONG_IPAD, ss: ss });
    m2.g.posPollBat('BILL-1', 95000);
    await m2.hoi();
    bang('tải lại không đọc lại', [m2.keu.length, m2.noi.length], [0, 0]);
  });

  await ca('máy không có giọng tiếng Anh hoặc không hỗ trợ đọc: vẫn kêu chuông, không lỗi', async function () {
    var m = dung_may({ giong: [{ name: 'Linh', lang: 'vi-VN' }] });
    m.g.posQrSheet('BILL-3', 50000, null, '', 'TCV');
    await m.hoi();
    bang('chuông', m.keu.length, 1);
    bang('vẫn đọc tiếng Anh mặc định của máy', m.noi, [{ cau: 'Payment received, 50,000 dong.', giong: null, lang: 'en-GB' }]);
    var k = dung_may({ coGiong: false });
    k.g.posQrSheet('BILL-4', 50000, null, '', 'TCV');
    await k.hoi();
    bang('không có speechSynthesis vẫn kêu', k.keu.length, 1);
  });

  await ca('bảng Chọn chuông: có khối Âm báo tiền với 5 chip cao 44, chọn Payment confirmed thì lưu trên máy, đọc thử ngay; Chỉ chuông thì không đọc', async function () {
    var m = dung_may({ giong: GIONG_IPAD });
    m.g.gmbMoChonChuong();
    var ds = m.tai.body.children, ov = ds[ds.length - 1];
    var chip = ov.querySelectorAll('[data-tienmau]');
    bang('năm chip', chip.length, 5);
    chip.forEach(function (c) { dung('chip cao 44: ' + c.getAttribute('data-tienmau'), /min-height:44px/.test(c.getAttribute('style') || '')); });
    dung('nút Nghe thử', ov.querySelector('[data-tiennghe]'));
    ov.onclick({ target: ov.querySelector('[data-tienmau="xac_nhan"]') });
    await m.hoi();
    bang('lưu trên máy', m.g.localStorage.getItem('vgb_tien_mau_bao'), 'xac_nhan');
    bang('đọc thử', m.noi[m.noi.length - 1].cau, 'Payment confirmed.');
    var ov2 = m.tai.body.children[m.tai.body.children.length - 1];
    dung('chip vừa chọn sáng lên', /aria-pressed="true"[^>]*>Payment confirmed/.test(ov2.innerHTML) || ov2.querySelector('[data-tienmau="xac_nhan"]').getAttribute('aria-pressed') === 'true');
    var truoc = m.noi.length;
    ov2.onclick({ target: ov2.querySelector('[data-tienmau="chi_chuong"]') });
    await m.hoi();
    bang('chỉ chuông không đọc', m.noi.length, truoc);
    m.g.posQrSheet('BILL-5', 70000, null, '', 'TCV');
    await m.hoi();
    bang('bill thật theo mẫu đã chọn: không đọc', m.noi.length, truoc);
  });

  await ca('bảng mã QR có nút Đổi âm báo tiền về cao 44, bấm mở bảng Chọn chuông và âm báo', async function () {
    var m = dung_may({ giong: GIONG_IPAD });
    m.g.posQrSheet('BILL-6', 70000, null, '', 'TCV');
    var ds = m.tai.body.children, qr = ds[ds.length - 1];
    var nut = qr.querySelector('[data-amchon]');
    dung('có nút', nut && /min-height:44px/.test(nut.getAttribute('style')));
    await qr.onclick({ target: nut });
    var moi = m.tai.body.children[m.tai.body.children.length - 1];
    dung('mở bảng chọn', moi !== qr && moi.querySelectorAll('[data-tienmau]').length === 5);
  });

  console.log('\n' + ket.dat + ' ca dat, ' + ket.hong + ' ca hong.');
  process.exitCode = ket.hong ? 1 : 0;
})();
