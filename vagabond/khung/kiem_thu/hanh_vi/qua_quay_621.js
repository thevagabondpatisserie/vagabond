/* Bo ca kiem HANH VI v621: ap ma qua chao mung (va ma gan nguoi nhan) tren man
 * tinh tien quay. Codex PR #503: ma gan nguoi nhan ma hoa don chua chon khach
 * thi phai gan nguoi nhan vao hoa don (tich diem dung nguoi); ma qua chao mung
 * ma hoa don dang chon khach khac thi khong ap.
 *
 * CHAY THAT: nap nguyen 13-khuyen-mai.js vao DOM gia, mo tam "Ma uu dai cua
 * khach" bang posSheetMaVc, go ma vao o, bam "Ap ma" nhu thu ngan; may chu la
 * ban gia ghi lai tung loi goi. Khong goi them ham nao ngoai chuoi do.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/qua_quay_621.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var domGia = require('./dom_gia.js');

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

function khoi(traMa) {
  var goi = [];
  var tin = [];
  var g = { console: console, JSON: JSON, Math: Math, Number: Number, String: String, Object: Object, Array: Array,
    Promise: Promise, Error: Error, RegExp: RegExp, setTimeout: function (f) { return 1; }, clearTimeout: function () {},
    document: domGia.taiLieuGia(), __goi: goi, __tin: tin,
    __api: function (m, a) { goi.push({ m: m, a: a }); return Promise.resolve(m === 'vagabond.khuyen_mai.tra_ma' ? traMa(a) : {}); } };
  g.window = g;
  vm.createContext(g);
  vm.runInContext([
    'var posDon = { mon: [{ item_code: "BANH", qty: 1, rate: 300000 }], ctkm: [], combo: [], maVc: "", khach_ma: "", khach_no: null, sdt: "", ten: "", kmKq: null, diemThe: { x: 1 } };',
    'var posQuay = { ma: "TCV" }; var __ve = 0;',
    'function posNguonThuc() { return "Tại chỗ"; }',
    'function posDoc() {}',
    'function scrPosQuay() {} function go() { __ve++; } function toast(s) { __tin.push(s); }',
    'function h(s) { return String(s == null ? "" : s); } function money(x) { return String(x); }',
    'function api(m, a) { return __api(m, a); }',
  ].join('\n'), g);
  vm.runInContext(fs.readFileSync(path.join(BEP, '13-khuyen-mai.js'), 'utf8'), g);
  return g;
}

function tam(g) { var ds = g.document.body.children; return ds[ds.length - 1]; }

async function apMa(g, ma) {
  g.posSheetMaVc();
  var sh = tam(g);
  var o = g.document.getElementById('vcO');
  o.value = ma;
  var nut = sh.querySelectorAll('[data-y]')[0];
  sh.onclick({ target: nut });
  await nghi();
  return sh;
}

var QUA = { loai: 'mot_lan', ma: 'QK7M2P', ctkm: 'QUA-CHAO-MUNG', ten: 'Quà chào mừng thành viên', dung_duoc: 1, ly_do: '',
  danh_cho: 'KL0412', ten_khach: 'Nguyễn Lan Anh', rang_buoc: 1 };

(async function () {
  await ca('hoá đơn chưa chọn khách: áp mã quà thì gắn người nhận vào hoá đơn, đặt lại điểm của khách cũ, báo tên', async function () {
    var g = khoi(function () { return QUA; });
    await apMa(g, 'qk7m2p');
    bang('mã', g.posDon.maVc, 'QK7M2P');
    bang('gắn người nhận', [g.posDon.khach_ma, g.posDon.ten], ['KL0412', 'Nguyễn Lan Anh']);
    bang('đặt lại điểm', g.posDon.diemThe, null);
    dung('báo tên', g.__tin.some(function (t) { return t.indexOf('hoá đơn của Nguyễn Lan Anh') >= 0; }));
    bang('hỏi máy chủ đúng mã, đúng quầy', g.__goi.map(function (x) { return [x.a.ma, x.a.quay]; }), [['QK7M2P', 'TCV']]);
  });

  await ca('hoá đơn đang chọn khách khác: mã quà KHÔNG áp, nói rõ phải bỏ khách đang chọn', async function () {
    var g = khoi(function () { return QUA; });
    g.posDon.khach_ma = 'KL9999'; g.posDon.ten = 'Khách khác';
    var sh = await apMa(g, 'QK7M2P');
    bang('không áp mã', g.posDon.maVc, '');
    bang('giữ khách đang chọn', g.posDon.khach_ma, 'KL9999');
    var bao = g.document.getElementById('vcBao');
    dung('câu báo', bao && String(bao.textContent).indexOf('chỉ dùng cho hoá đơn của chính khách đó') >= 0);
    dung('tấm còn mở', g.document.body.children.indexOf(sh) >= 0);
  });

  await ca('đúng khách đang chọn: áp mã bình thường', async function () {
    var g = khoi(function () { return QUA; });
    g.posDon.khach_ma = 'KL0412';
    await apMa(g, 'QK7M2P');
    bang('áp', [g.posDon.maVc, g.posDon.khach_ma], ['QK7M2P', 'KL0412']);
  });

  await ca('voucher thường (tin Zalo) cho hoá đơn khách khác vẫn áp như cũ; chưa có khách thì gắn người nhận', async function () {
    var vc = Object.assign({}, QUA, { ma: 'SN1234', ctkm: 'KM-SN', ten: 'Quà sinh nhật', rang_buoc: 0 });
    var g = khoi(function () { return vc; });
    g.posDon.khach_ma = 'KL9999';
    await apMa(g, 'SN1234');
    bang('áp, giữ khách', [g.posDon.maVc, g.posDon.khach_ma], ['SN1234', 'KL9999']);
    g = khoi(function () { return vc; });
    await apMa(g, 'SN1234');
    bang('chưa có khách: gắn người nhận', g.posDon.khach_ma, 'KL0412');
  });

  await ca('mã không gắn ai (mã cố định, lô mã): không đụng khách', async function () {
    var g = khoi(function () { return { loai: 'co_dinh', ctkm: 'KM-X', ten: 'Tết', dung_duoc: 1 }; });
    await apMa(g, 'TET2026');
    bang('áp, không gắn khách', [g.posDon.maVc, g.posDon.khach_ma], ['TET2026', '']);
  });

  console.log('Bo ca kiem HANH VI v621 (ma qua chao mung tai quay)');
  ket.loi.forEach(function (l) { console.log('  HONG ' + l); });
  console.log(ket.dat + ' ca đạt, ' + ket.hong + ' ca hỏng, tổng ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
