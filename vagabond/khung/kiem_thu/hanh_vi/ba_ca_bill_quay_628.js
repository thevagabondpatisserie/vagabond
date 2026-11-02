/* Ca kiểm HÀNH VI v628: ba ca bill quầy Dễ báo ngày 02/11/2026.
 *
 * TH1: bill NVHCXVC4 đang hiện mã QR thì app tải lại. Nạp THẬT các hàm giữ
 *      bill chờ chuyển khoản của 09-tinh-tien-quay.js vào hai "lần mở app"
 *      dùng chung một bộ nhớ máy, xem lần sau còn thấy bill cũ không.
 * Dò tiền: nạp THẬT posSheetDoTien, máy chủ giả trả dòng có câu giải thích
 *      (khoản của bill đã huỷ), xem dòng hiện câu và hộp xác nhận nhắc lại.
 * TH3: nạp THẬT posHuyCoTien của 10-bill-quay.js, bấm đúng chuỗi của thu
 *      ngân: chọn cách xử lý tiền, chọn điểm, bấm Tiếp tục.
 *
 * Phần CHƯA có ca hành vi (ghi thật trong PR): nhánh tự chuyển tiền sau khi
 * lưu bill (posLuuDon) và khối "khách chuyển thừa" trên màn bill (scrPosBill),
 * vì hai màn đó kéo theo cả trăm hàm của màn tính tiền.
 *
 * Chạy:  node vagabond/khung/kiem_thu/hanh_vi/ba_ca_bill_quay_628.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
function doc(t) { return fs.readFileSync(path.join(BEP, t), 'utf8'); }
var NEN = doc('00-nen.js'), POS = doc('09-tinh-tien-quay.js'), BILL = doc('10-bill-quay.js');
var KHUON = doc('15-khuon-danh-sach.js'), KM = doc('13-khuyen-mai.js'), KHO = doc('03-kho-chung-tu.js');

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
var NEN3 = ['h', 'money', 'today'].map(function (t) { return layHam(NEN, t); }).join('\n');
var CHO_CK = 'var POS_CHO_CK = \'vgb_pos_cho_ck\';\n' +
  ['posChoCkDoc', 'posChoCkLuu', 'posChoCkGhi', 'posChoCkXoa', 'posChoCkCua', 'posChoCkKhoi']
    .map(function (t) { return layHam(POS, t); }).join('\n');

var ket = { dat: 0, hong: 0 };
function dung(mo, dk) { if (!dk) throw new Error(mo); }
function bang(mo, a, b) {
  var x = JSON.stringify(a), y = JSON.stringify(b);
  if (x !== y) throw new Error(mo + ': duoc ' + x + ', mong ' + y);
}
function tick() { return new Promise(function (r) { setTimeout(r, 5); }); }
async function choDen(dk) { for (var i = 0; i < 80 && !dk(); i++) await new Promise(function (r) { setTimeout(r, 20); }); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  DAT   ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function chu(el) { var s = el._chu || ''; (el.children || []).forEach(function (c) { s += chu(c); }); return s; }

/* Bộ nhớ máy dùng chung giữa các lần mở app (localStorage giả). */
function boNho(hong) {
  var kho = {};
  return {
    kho: kho,
    getItem: function (k) { if (hong) throw new Error('chặn bộ nhớ'); return Object.prototype.hasOwnProperty.call(kho, k) ? kho[k] : null; },
    setItem: function (k, v) { if (hong) throw new Error('chặn bộ nhớ'); kho[k] = String(v); }
  };
}
function moApp(ls, ngay) {
  var g = { console: console, JSON: JSON, Math: Math, Date: Date, Number: Number, String: String, Object: Object, Array: Array,
    localStorage: ls };
  g.window = g;
  vm.runInNewContext(NEN3 + '\n' + CHO_CK, g, { filename: 'cho-ck.js' });
  if (ngay) g.today = function () { return ngay; };
  return g;
}
var DON_NVH = { bill: 'NVHCXVC4', che_do: 'Mang về', pt: 'Chuyển khoản',
  mon: [{ item_code: 'NUTR00021', ten: 'Trà Hoa Lài Trái Hồng', qty: 1, rate: 40000, tc: [], gc: '' }] };
var NVH = { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên' };

(async function () {
  console.log('v628 ba ca bill quầy: giữ bill chờ chuyển khoản, Dò tiền, huỷ bill đã nhận tiền');

  await ca('TH1: bill đang hiện QR được giữ trên máy; mở app lại vẫn thấy đúng mã, đúng giỏ, đúng quầy', async function () {
    var ls = boNho();
    var lan1 = moApp(ls);
    lan1.posChoCkGhi(DON_NVH, NVH, 40000);
    var lan2 = moApp(ls);
    var ds = lan2.posChoCkCua('NVHTN', 'NVHMOI01');
    bang('còn đúng một bill', ds.map(function (x) { return x.bill; }), ['NVHCXVC4']);
    bang('giỏ giữ nguyên', ds[0].don.mon, DON_NVH.mon);
    bang('số tiền', ds[0].tien, 40000);
    var o = new dg.ElementGia('div');
    o.innerHTML = lan2.posChoCkKhoi(ds);
    var h = chu(o);
    dung('thẻ nói bill đang chờ chuyển khoản', h.indexOf('Bill đang chờ khách chuyển khoản') >= 0);
    dung('thẻ nêu mã và số tiền', h.indexOf('NVHCXVC4') >= 0 && h.indexOf('40.000 đ') >= 0);
    dung('có nút Mở lại bill gắn đúng mã', !!o.querySelector('[data-ckmo="NVHCXVC4"]'));
    dung('có nút Bỏ bill này gắn đúng mã', !!o.querySelector('[data-ckbo="NVHCXVC4"]'));
  });

  await ca('TH1: quầy khác không thấy bill của NVH; bill đang mở không tự báo chính nó', async function () {
    var ls = boNho();
    moApp(ls).posChoCkGhi(DON_NVH, NVH, 40000);
    var g = moApp(ls);
    bang('quầy TCV không thấy', g.posChoCkCua('TCV', 'TCVMOI01').length, 0);
    bang('đang mở đúng bill đó thì không báo', g.posChoCkCua('NVHTN', 'NVHCXVC4').length, 0);
  });

  await ca('TH1: lưu xong (hoặc bỏ) thì xoá; sang ngày khác thì tự dọn', async function () {
    var ls = boNho();
    var g = moApp(ls, '2026-11-01');
    g.posChoCkGhi(DON_NVH, NVH, 40000);
    g.posChoCkXoa('NVHCXVC4');
    bang('xoá xong', g.posChoCkCua('NVHTN', '').length, 0);
    g.posChoCkGhi(DON_NVH, NVH, 40000);
    var mai = moApp(ls, '2026-11-02');
    bang('ngày hôm sau không còn', mai.posChoCkCua('NVHTN', '').length, 0);
    bang('đã dọn khỏi bộ nhớ', JSON.parse(ls.kho.vgb_pos_cho_ck), {});
  });

  await ca('TH1: máy chặn bộ nhớ thì màn tính tiền vẫn chạy, không nổ', async function () {
    var g = moApp(boNho(true));
    g.posChoCkGhi(DON_NVH, NVH, 40000);
    bang('không có gì để báo', g.posChoCkCua('NVHTN', '').length, 0);
    g.posChoCkXoa('NVHCXVC4');
  });

  /* ---------------- Dò tiền: dòng của bill đã huỷ ---------------- */
  var HAM_DO = NEN3 + '\n' + ['posChipNut', 'posNgayVn', 'posDtCong', 'posSheetDoTien'].map(function (t) { return layHam(POS, t); }).join('\n') +
    '\n' + ['dsccHang', 'dsCongCu', 'dsCongCuNoi'].map(function (t) { return layHam(KHUON, t); }).join('\n') +
    '\nvar scanBarcode = function () { return Promise.resolve(null); };\n' + layHam(KM, 'kmHangChip') + '\n' + layHam(KHO, 'errMsg');
  var CAU = 'Bill SOL3D4A9 (HDB-26-11-00292) đã huỷ lúc 11:05 ngày 02/11 (lý do: OUT NHẦM NGUỒN CỦA SALE Ạ), chưa hoàn tiền cho khách.';
  function moDo(vai) {
    var tai = dg.taiLieuGia();
    var goi = [], hoi = [];
    var g = { document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
      RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout, isNaN: isNaN,
      posQuay: { ma: 'TCV' }, S: { roles: vai, stack: [] }, busy: function () {}, toast: function () {},
      hasRole: function (r) { return vai.indexOf(r) >= 0; },
      confirmSheet: function (t, m) { hoi.push(m); return Promise.resolve(true); },
      api: function (duong, ts) {
        goi.push({ duong: duong, ts: ts });
        if (duong === 'vagabond.ban_hang.pos_do_tien') {
          return Promise.resolve({ nguon: 'tat_ca', tien: 1130000, ngay: '2026-11-02', diem: 'TCV', tk_rieng: 1, tk_stk: 'VQRQALEAF2999',
            so_khop: 1, so_khop_nguon: { diem: 0, cty: 0, tat_ca: 1 }, so_dong_nguon: { diem: 0, cty: 0, tat_ca: 1 }, gan_ngoai: 1,
            gd: [{ ten: 'BT-SOL', tien: 1130000, gio: '10:50', mo_ta: 'QALEAI2626 VAGABOND SOL3D4A9', khop: 1, cua_bill: '',
              ghi_chu: CAU, tk_nhan: 'Sales Online', duoc_gan: 1 }] });
        }
        if (duong === 'vagabond.ban_hang.pos_gan_tien') return Promise.resolve({ ma_tham_chieu: 'FT26306111111111', nhan: 1130000, lech: 0 });
        return Promise.reject(new Error('api la: ' + duong));
      } };
    g.window = g;
    vm.runInNewContext(HAM_DO, g, { filename: 'do-tien.js' });
    return { g: g, tai: tai, goi: goi, hoi: hoi };
  }
  function sheet(m) { var ds = m.tai.body.children; return ds[ds.length - 1]; }

  await ca('Dò tiền: khoản của bill đã huỷ hiện câu giải thích ngay trên dòng, gắn được, hộp xác nhận nhắc lại câu đó', async function () {
    var m = moDo(['VGB - Quản lý cửa hàng']);
    await m.g.posSheetDoTien(1130000, 'HDB-26-11-00295', function () {});
    await tick();
    var d0 = sheet(m).querySelectorAll('[data-gan]')[0];
    dung('dòng hiện câu bill đã huỷ', chu(d0).indexOf('SOL3D4A9 (HDB-26-11-00292) đã huỷ') >= 0);
    dung('dòng có nút Chọn', chu(d0).indexOf('Chọn') >= 0);
    sheet(m).onclick({ target: d0 });
    await choDen(function () { return m.goi.some(function (x) { return x.duong === 'vagabond.ban_hang.pos_gan_tien'; }); });
    dung('xác nhận nhắc câu giải thích', (m.hoi[0] || '').indexOf('chưa hoàn tiền cho khách') >= 0);
    bang('gắn đúng dòng vào đúng bill', m.goi.filter(function (x) { return x.duong === 'vagabond.ban_hang.pos_gan_tien'; })[0].ts,
      { name: 'HDB-26-11-00295', gd: 'BT-SOL' });
  });

  /* ---------------- TH3: huỷ bill đã nhận tiền ---------------- */
  var HAM_HUY = NEN3 + '\n' + layHam(POS, 'posChipNut') + '\n' + layHam(BILL, 'posHuyCoTien');
  var DIEM = [{ ma: 'SALES', ten: 'Sales Online', ten_ngan: 'Sales Online' },
    { ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1' },
    { ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN' }];
  var D_CU = { name: 'HDB-26-11-00292', vgb_quay: '', discount_amount: 0, grand_total: 1130000 };
  var MON = [{ item_code: 'BANH01', ten: 'Entremet Pistachio', qty: 1, rate: 1130000, tc: [], gc: 'ghi tên', combo: '' }];
  function moHuy(otp) {
    var tai = dg.taiLieuGia();
    var goi = [], tin = [], di = [], hoan = [];
    var g = { document: tai, console: console, Math: Math, JSON: JSON, String: String, Array: Array, Object: Object,
      RegExp: RegExp, Promise: Promise, Number: Number, Date: Date, setTimeout: setTimeout,
      CFGBH: { diem: DIEM }, posQuay: null, posDon: null, posHomNayTxt: 'x',
      busy: function () {}, toast: function (s) { tin.push(s); },
      posXinPhep: function () { return Promise.resolve(otp === undefined ? '123456' : otp); },
      posMoi: function () { return { bill: 'TCVMOI01', mon: [], pt: 'Tiền mặt', giam: '', quay: g.posQuay && g.posQuay.ma }; },
      hoanMoFormHuy: function (d) { hoan.push(d.name); },
      scrPosQuay: function () {}, scrPosDs: function () {},
      go: function (fn) { di.push(fn === g.scrPosQuay ? 'quay' : (fn === g.scrPosDs ? 'ds' : '?')); },
      api: function (duong, ts) { goi.push({ duong: duong, ts: ts }); return Promise.resolve({ ok: 1 }); } };
    g.window = g;
    vm.runInNewContext(HAM_HUY, g, { filename: 'huy-co-tien.js' });
    return { g: g, tai: tai, goi: goi, tin: tin, di: di, hoan: hoan };
  }
  function sh(m) { var ds = m.tai.body.children; return ds[ds.length - 1]; }
  function bamVao(m, chon) { var el = sh(m).querySelector(chon); if (!el) throw new Error('khong thay ' + chon); sh(m).onclick({ target: el }); }

  await ca('TH3: bill đã nhận 1.130.000, chọn nhầm điểm: chọn District 1, OTP, huỷ với lý do rõ, mở bill mới ở D1 mang giỏ và tiền cần chuyển', async function () {
    var m = moHuy();
    m.g.posHuyCoTien(D_CU, 'SOL3D4A9', MON, { nhan: 1130000 });
    var h0 = chu(sh(m));
    dung('nói bill đã nhận tiền', h0.indexOf('Bill này đã nhận 1.130.000 đ chuyển khoản.') >= 0);
    dung('không cho chọn lại chính Sales Online', !sh(m).querySelector('[data-hdiem="SALES"]'));
    bamVao(m, '[data-hdiem="TCV"]');
    bamVao(m, '[data-hct]');
    await choDen(function () { return m.di.length; });
    var xoa = m.goi.filter(function (x) { return x.duong === 'vagabond.ban_hang.pos_xoa'; });
    bang('huỷ đúng bill, có OTP và lý do', xoa.map(function (x) { return [x.ts.name, x.ts.otp, x.ts.ly_do]; }),
      [['HDB-26-11-00292', '123456', 'Chọn nhầm điểm bán, lập lại ở District 1']]);
    bang('đứng ở District 1', m.g.posQuay.ma, 'TCV');
    bang('bill mới mang giỏ cũ', m.g.posDon.mon.map(function (x) { return [x.item_code, x.qty, x.rate, x.gc]; }), [['BANH01', 1, 1130000, 'ghi tên']]);
    bang('bill mới ghi tiền cần chuyển', m.g.posDon.chuyen_tu, { name: 'HDB-26-11-00292', ma: 'SOL3D4A9', tien: 1130000 });
    bang('phương thức chuyển khoản', m.g.posDon.pt, 'Chuyển khoản');
    bang('mở màn tính tiền', m.di, ['quay']);
  });

  await ca('TH3: chọn nhầm điểm mà chưa chọn điểm đúng thì không huỷ, nhắc chọn điểm', async function () {
    var m = moHuy();
    m.g.posHuyCoTien(D_CU, 'SOL3D4A9', MON, { nhan: 1130000 });
    bamVao(m, '[data-hct]');
    await tick();
    bang('không gọi huỷ', m.goi.length, 0);
    dung('nhắc chọn điểm', (m.tin[0] || '').indexOf('Chọn điểm bán đúng') >= 0);
  });

  await ca('TH3: huỷ, lập lại sau: huỷ với ghi thêm, về danh sách, nhắc bấm Dò tiền', async function () {
    var m = moHuy();
    m.g.posHuyCoTien(D_CU, 'SOL3D4A9', MON, { nhan: 1130000 });
    bamVao(m, '[data-cach="sau"]');
    sh(m).querySelector('#hctGhi').value = 'khách mua tại D1';
    bamVao(m, '[data-hct]');
    await choDen(function () { return m.di.length; });
    bang('lý do', m.goi[0].ts.ly_do, 'Huỷ, lập lại bill sau. khách mua tại D1');
    bang('về danh sách', m.di, ['ds']);
    dung('nhắc Dò tiền', (m.tin[0] || '').indexOf('bấm Dò tiền') >= 0);
    bang('không đổi điểm', m.g.posQuay, null);
  });

  await ca('TH3: khách không mua nữa: mở đúng phiếu huỷ và hoàn tiền có sẵn, không tự huỷ', async function () {
    var m = moHuy();
    m.g.posHuyCoTien(D_CU, 'SOL3D4A9', MON, { nhan: 1130000 });
    bamVao(m, '[data-cach="hoan"]');
    bamVao(m, '[data-hct]');
    await tick();
    bang('mở phiếu hoàn của bill cũ', m.hoan, ['HDB-26-11-00292']);
    bang('không gọi huỷ', m.goi.length, 0);
  });

  await ca('TH3: không có OTP thì không huỷ gì', async function () {
    var m = moHuy(null);
    m.g.posHuyCoTien(D_CU, 'SOL3D4A9', MON, { nhan: 1130000 });
    bamVao(m, '[data-hdiem="TCV"]');
    bamVao(m, '[data-hct]');
    await tick(); await tick();
    bang('không gọi huỷ', m.goi.length, 0);
    bang('không đổi màn', m.di, []);
  });

  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
