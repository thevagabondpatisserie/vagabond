/* Bo ca kiem HANH VI cho man Chot ca (#296 muc 3): chi dem tien mat.
 *
 * Vi sao co tep nay: tu 12/09/2026 man chot ca chi con MOT o dem la tien
 * mat. Do chuoi trong ma nguon khong chung minh duoc rang thu ngan bam
 * "Chot ca" thi may chu nhan dung mot dong Tien mat, cung khong chung minh
 * duoc rang bang doi soat tra ve khong tinh lech cho chuyen khoan. Nen o
 * day nap THAT scrChotCa va scrDoiSoatCa tu 09-tinh-tien-quay.js vao DOM
 * gia, bam nut, roi soi payload va HTML ve ra.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/chot_ca_296.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');
var dg = require('./dom_gia.js');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');

function docTep(ten) { return fs.readFileSync(path.join(BEP, ten), 'utf8'); }

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  if (src.slice(Math.max(0, dau - 6), dau) === 'async ') dau -= 6;
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

function dung(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) {
  if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b));
}

/* Bang doi soat ma may chu ban v487 tra ve: chi Tien mat co lech. */
function bangMayChu(lechTienMat, lechCk) {
  lechCk = lechCk || 0;
  return [
    { phuong_thuc: 'Tiền mặt', so_bill: 41, may: 4850000, phai_co: 5350000, dem: 5350000 + lechTienMat, lech: lechTienMat },
    /* lechCk chi khac 0 khi gia lap MAY CHU BAN CU (truoc v487) con tinh
       lech cho chuyen khoan vi app cu tung gui o do. Man hinh moi phai
       khong keo dong do vao cau hoi ly do. */
    { phuong_thuc: 'Chuyển khoản', so_bill: 18, may: 3200000, phai_co: 3200000, dem: 3200000 + lechCk, lech: lechCk },
    { phuong_thuc: 'Quẹt thẻ', so_bill: 5, may: 950000, phai_co: 950000, dem: 950000, lech: 0 },
  ];
}

function dungMan(canh) {
  canh = canh || {};
  var tai = dg.taiLieuGia();
  var khung = new dg.ElementGia('div');
  khung.parentNode = tai.body;
  tai.body.children.push(khung);
  var goiApi = [], daToast = [], hoi = [];

  var that = {
    document: tai, console: console,
    Math: Math, JSON: JSON, Date: Date, String: String, Number: Number,
    Array: Array, Object: Object, Promise: Promise, RegExp: RegExp,
    setTimeout: setTimeout, parseFloat: parseFloat, parseInt: parseInt, isNaN: isNaN,
    frame: function (tieuDe, html) { khung.innerHTML = html; return khung; },
    go: function (fn) { return fn(); },
    busy: function () {},
    toast: function (t) { daToast.push(String(t)); },
    baoTin: function (t) { daToast.push(String(t)); },
    money: function (n) { return String(Math.round(Number(n) || 0)); },
    hoiChu: function (tieuDe, chu) { hoi.push(chu); return Promise.resolve(canh.lyDo === undefined ? 'đếm sót' : canh.lyDo); },
    scrPosQuay: function () {},
    posQuay: { ma: 'D1', ten: 'Quầy Trần Cao Vân' },
    caPos: {
      dang_mo: 1, ma: 'CA-2026-00042', mo_luc: '2026-09-13 08:00:00', tien_le_dau_ca: 500000,
      phuong_thuc: ['Tiền mặt', 'Chuyển khoản', 'Quẹt thẻ'], chi_dem_tien_mat: 1,
    },
    api: function (duong, ts) {
      goiApi.push({ duong: duong, ts: ts });
      if (duong !== 'vagabond.ca_quay.chot_ca') return Promise.reject(new Error('Cua la: ' + duong));
      var lech = canh.lech || 0;
      if (Math.abs(lech) >= 1000 && !ts.ly_do_lech) {
        return Promise.resolve({ can_ly_do: 1, bang: bangMayChu(lech, canh.lechCk), tong_lech: Math.abs(lech), chi_dem_tien_mat: 1, nhac: 'Gõ lý do' });
      }
      return Promise.resolve({ ma: 'CA-2026-00042', da_chot: 1, bang: bangMayChu(lech), tong_lech: Math.abs(lech), tien_mat_dem: 5350000 + lech, chi_dem_tien_mat: 1 });
    },
  };
  that.globalThis = that;


  var nen = docTep('00-nen.js');
  var quay = docTep('09-tinh-tien-quay.js');
  var ma = [
    layHam(nen, 'h'),
    layHam(quay, 'scrChotCa'),
    layHam(quay, 'caLechChu'),
    layHam(quay, 'scrDoiSoatCa'),
  ].join('\n;\n');
  vm.runInNewContext(ma, that, { filename: '09-tinh-tien-quay.js' });
  return { g: that, tai: tai, khung: khung, goiApi: goiApi, toast: daToast, hoi: hoi };
}

async function bamChot(m, tienMat) {
  await m.g.scrChotCa();
  var o = m.tai.getElementById('caDemTienMat');
  if (!o) throw new Error('Man chot ca khong co o #caDemTienMat');
  if (tienMat !== null) o.value = String(tienMat);
  var nut = m.tai.getElementById('caChotNut');
  await nut.onclick(dg.suKien('click', {}, nut));
}

var ket = { dat: 0, hong: 0 };
async function ca(ten, ham) {
  try { await ham(); ket.dat++; console.log('  ok  ' + ten); }
  catch (e) { ket.hong++; console.log('  HONG ' + ten + '\n       ' + (e && e.message)); }
}

(async function () {
  await ca('may chu cu khong co co ho tro thi khong gui so dem', async function () {
    var m = dungMan(); delete m.g.caPos.chi_dem_tien_mat;
    await m.g.scrChotCa();
    dung('khong co nut chot', !m.tai.getElementById('caChotNut'));
    bang('khong goi API', m.goiApi.length, 0);
    dung('noi ro cho cap nhat', m.khung.innerHTML.includes('chưa sẵn sàng'));
  });
  await ca('chu sai, am, NaN khong bien thanh 0; dau nghin doc dung', async function () {
    for (var so of ['abc', '-5', 'NaN', 'Infinity', '1.5']) {
      var m = dungMan(); await bamChot(m, so);
      bang('khong gui '+so, m.goiApi.length, 0);
    }
    var m = dungMan(); await bamChot(m, '5.000');
    bang('nam nghin', JSON.parse(m.goiApi[0].ts.dem)['Tiền mặt'], 5000);
  });
  await ca('man chot ca chi ve MOT o dem, khong con o nao theo phuong thuc', async function () {
    var m = dungMan();
    await m.g.scrChotCa();
    var oCu = m.tai.querySelectorAll('.caDem');
    bang('khong con o .caDem cua ban cu', oCu.length, 0);
    dung('co o tien mat', !!m.tai.getElementById('caDemTienMat'));
    var chu = m.khung.innerHTML;
    dung('ke ten cac phuong thuc khong can dem', chu.indexOf('Chuyển khoản, Quẹt thẻ') >= 0);
    dung('khong ve so may truoc khi chot (dem mu)', chu.indexOf('3200000') < 0 && chu.indexOf('4850000') < 0);
  });

  await ca('bam Chot khi o tien mat trong thi nhac, khong goi may chu', async function () {
    var m = dungMan();
    await bamChot(m, null);
    bang('khong goi API', m.goiApi.length, 0);
    dung('co cau nhac ve tien mat', m.toast.length === 1 && m.toast[0].indexOf('tiền mặt') >= 0);
  });

  await ca('bam Chot thi may chu nhan DUNG mot dong Tien mat', async function () {
    var m = dungMan();
    await bamChot(m, 5350000);
    bang('mot lan goi', m.goiApi.length, 1);
    var dem = JSON.parse(m.goiApi[0].ts.dem);
    bang('chi mot khoa', Object.keys(dem).length, 1);
    bang('la Tien mat', dem['Tiền mặt'], 5350000);
    bang('dung quay', m.goiApi[0].ts.quay, 'D1');
  });

  await ca('go 0 van chot duoc (ket rong la mot con so that)', async function () {
    var m = dungMan();
    await bamChot(m, 0);
    bang('goi may chu', m.goiApi.length, 1);
    bang('gui so 0', JSON.parse(m.goiApi[0].ts.dem)['Tiền mặt'], 0);
  });

  await ca('bang doi soat: dong Tien mat co lech, dong khac chi hien so may', async function () {
    var m = dungMan({ lech: 0 });
    await bamChot(m, 5350000);
    var chu = m.khung.innerHTML;
    dung('tieu de noi tien mat khop', chu.indexOf('Tiền mặt khớp') >= 0);
    dung('chuyen khoan van co so may', chu.indexOf('3200000') >= 0);
    bang('hai dong khong dem', (chu.match(/không đếm/g) || []).length, 2);
    bang('hai dong khong tinh lech', (chu.match(/không tính lệch/g) || []).length, 2);
  });

  await ca('lech tien mat thi hoi ly do, cau hoi chi noi Tien mat, roi goi lai kem ly do', async function () {
    var m = dungMan({ lech: -50000, lechCk: -3200000 });
    await bamChot(m, 5300000);
    bang('hai lan goi', m.goiApi.length, 2);
    bang('lan hai co ly do', m.goiApi[1].ts.ly_do_lech, 'đếm sót');
    bang('mot cau hoi', m.hoi.length, 1);
    dung('cau hoi neu tien mat thieu', m.hoi[0].indexOf('Tiền mặt: thiếu 50000') >= 0);
    dung('cau hoi khong keo chuyen khoan vao', m.hoi[0].indexOf('Chuyển khoản') < 0);
  });

  await ca('bo ly do thi khong chot, khong goi lan hai', async function () {
    var m = dungMan({ lech: -50000, lyDo: null });
    await bamChot(m, 5300000);
    bang('chi mot lan goi', m.goiApi.length, 1);
    dung('nhac chua chot', m.toast.some(function (t) { return t.indexOf('Chưa chốt') >= 0; }));
  });

  console.log(ket.hong ? 'HONG ' + ket.hong + '/' + (ket.dat + ket.hong) : 'PASS ' + ket.dat + ' ca hanh vi man Chot ca (#296 muc 3)');
  process.exitCode = ket.hong ? 1 : 0;
})().catch(function (e) { console.error(e); process.exitCode = 1; });
