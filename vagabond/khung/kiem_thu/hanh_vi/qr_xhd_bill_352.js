/* Bo ca kiem HANH VI: ma QR xuat hoa don tren bill quay (22/09/2026).
 *
 * Ca that: bill HDB-26-09-04366 in cau "Quy khach vui long quet ma QR ...
 * de nhap thong tin xuat hoa don" ma KHONG co ma QR (De bao). Anh QR khi do
 * tai tu api.qrserver.com, mang ngoai khong ve kip la mat anh ma chu van in.
 *
 * Nap THAT posInBill (10-bill-quay.js), inQrAnh va inNapJs (27-in-ngam.js),
 * va thu vien vendor/qrcode.js qua dung duong the <script> gia. Mang ngoai
 * bi CHAN hoan toan: moi <img> tro ra ngoai trong to in la hong. Ca kiem
 * chi goi posInBill nhu nut In bill, khong goi them ham nao (bai hoc 06/09).
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/qr_xhd_bill_352.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var BILL = fs.readFileSync(path.join(BEP, '10-bill-quay.js'), 'utf8');
var IN = fs.readFileSync(path.join(BEP, '27-in-ngam.js'), 'utf8');
var QR = fs.readFileSync(path.join(GOC, 'vagabond', 'public', 'js', 'vendor', 'qrcode.js'), 'utf8');

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
function layBien(src, ten) {
  var dau = src.indexOf('var ' + ten + ' = {');
  if (dau < 0) throw new Error('Khong thay bien ' + ten);
  return src.slice(dau, src.indexOf('};', dau) + 2);
}

function dung(canh) {
  canh = canh || {};
  var ket = { html: '', toast: [], nap: [] };
  var ctx = {
    console: console, Math: Math, JSON: JSON, Date: Date, String: String, Number: Number, Array: Array,
    Object: Object, RegExp: RegExp, Promise: Promise, setTimeout: setTimeout, encodeURIComponent: encodeURIComponent,
    location: { origin: 'https://vagabond.s.frappe.cloud' },
    S: { me: { full_name: 'Thu ngân thử' }, user: 'tn@vgb' },
    CFGBH: {}, posQuay: { ten: 'The Vagabond District 1', phu: '9 Trần Cao Vân' },
    document: {
      createElement: function () { return {}; },
      head: {
        /* The <script> gia: nap dung tep vendor vao cung ngu canh, nhu trinh
           duyet. canh.hongNap: may chu tra loi, onerror. */
        appendChild: function (s) {
          ket.nap.push(s.src);
          setTimeout(function () {
            if (canh.hongNap) return s.onerror();
            vm.runInContext(QR, ctx, { filename: 'qrcode.js' });
            s.onload();
          }, 1);
        }
      }
    },
    inMoCuaSoNeuCan: function () { return null; },
    posCanInKemPhieuMon: function () { return false; },
    inMau: function () { return { qr_xhd: 1, co_chu: 12, chan_trang: 'Cảm ơn quý khách!', web: 'thevagabondpatisserie.com' }; },
    inKho: function () { return { css: '80mm auto', rong: 72 }; },
    inTo: function (vt, td, html) { ket.html = html; return Promise.resolve('qz'); },
    posGopDongMon: function (m) { return m; },
    api: function (duong) {
      if (duong === 'vagabond.ban_hang.pos_link_xhd') {
        if (canh.hongLink) return Promise.reject(new Error('mất mạng'));
        return Promise.resolve({ url: 'https://thevagabondpatisserie.com/xhd/TCV8A4GK-abc' });
      }
      if (duong === 'vagabond.ban_hang.pos_bill_them') return Promise.resolve({ diem: null, thu_ngan: 'Nguyễn Phương Gia Bảo' });
      return Promise.resolve({});
    },
    toast: function (m) { ket.toast.push(String(m)); },
    money: function (n) { return String(n); },
    h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); },
  };
  vm.createContext(ctx);
  vm.runInContext(
    layBien(IN, 'IN_VENDOR') + '\nvar inDaNap = {};\n' + layHam(IN, 'inNapJs') + '\n' + layHam(IN, 'inQrAnh') + '\n' +
    layHam(BILL, 'posInBill'), ctx, { filename: 'bill.js' });
  return { ctx: ctx, ket: ket };
}

function bill() {
  return { name: 'HDB-26-09-04366', bill: 'TCV8A4GK', thu: 625000, tong: 625000, pt: 'Thẻ - ShinhanBank',
    mon: [{ ten: 'Americano Dừa Xiêm Xanh', qty: 1, rate: 85000 }] };
}

var ket = { dat: 0, hong: 0, loi: [] };
function dungDk(mo, dk) { if (!dk) throw new Error(mo + ': duoc false, mong true'); }
function bang(mo, a, b) { if (a !== b) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}
function anhNgoai(html) {
  return (html.match(/<img[^>]+src="([^"]+)"/g) || []).filter(function (t) { return /src="https?:/.test(t) && t.indexOf('/files/logo-in.png') < 0; });
}

async function chayHet() {
  await ca('bill that: ma QR ve tai may thanh anh nhung, khong tro ra mang ngoai, ma dung link xuat hoa don', async function () {
    var m = dung();
    await m.ctx.posInBill(bill());
    var html = m.ket.html;
    dungDk('co cau quet ma QR', html.indexOf('Quý khách vui lòng quét mã QR') >= 0);
    var the = html.match(/<div class="qr"><img src="(data:image\/gif;base64,[^"]+)">/);
    dungDk('cau quet ma di kem anh QR nhung data:', !!the);
    bang('khong con anh nao tai tu mang ngoai', anhNgoai(html).length, 0);
    dungDk('khong con goi api.qrserver.com', html.indexOf('qrserver') < 0);
    /* Noi dung ma: dung lai thu vien that voi dung link ma may chu tra,
       anh phai trung tung byte voi anh da in. */
    var q = m.ctx.qrcode(0, 'M'); q.addData('https://thevagabondpatisserie.com/xhd/TCV8A4GK-abc', 'Byte'); q.make();
    var n = q.getModuleCount();
    bang('anh in la ma cua dung link xuat hoa don', the[1], q.createDataURL(Math.max(2, Math.floor(190 / (n + 8))), 4));
    bang('nap thu vien tu repo, khong CDN', m.ket.nap[0], '/assets/vagabond/js/vendor/qrcode.js');
    bang('khong bao loi thu ngan', m.ket.toast.length, 0);
  });
  await ca('in lan hai: thu vien da nap thi khong nap lai', async function () {
    var m = dung();
    await m.ctx.posInBill(bill());
    await m.ctx.posInBill(bill());
    bang('nap dung mot lan', m.ket.nap.length, 1);
  });
  await ca('khong nap duoc thu vien: KHONG in cau "quet ma QR" ma in link bang chu va bao thu ngan', async function () {
    var m = dung({ hongNap: 1 });
    await m.ctx.posInBill(bill());
    var html = m.ket.html;
    dungDk('khong in cau quet ma khi khong co ma', html.indexOf('quét mã QR') < 0);
    dungDk('in link bang chu', html.indexOf('https://thevagabondpatisserie.com/xhd/TCV8A4GK-abc') >= 0);
    dungDk('bao thu ngan', m.ket.toast.some(function (t) { return t.indexOf('Không vẽ được mã QR') >= 0; }));
  });
  await ca('xin link that bai: bill khong co ma, bao thu ngan cach tao link', async function () {
    var m = dung({ hongLink: 1 });
    await m.ctx.posInBill(bill());
    dungDk('khong in cau quet ma', m.ket.html.indexOf('quét mã QR') < 0);
    dungDk('bao thu ngan', m.ket.toast.some(function (t) { return t.indexOf('Tạo link điền thông tin xuất hoá đơn') >= 0; }));
  });
}

chayHet().then(function () {
  console.log('Bo ca kiem HANH VI ma QR xuat hoa don tren bill (#352)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
}, function (e) { console.log('VO KHUNG: ' + (e && e.stack ? e.stack : e)); process.exit(1); });
