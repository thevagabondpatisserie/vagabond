/* Bo ca kiem HANH VI: dinh uy nhiem chi o buoc xac nhan da chuyen tien (app).
 *
 * Ca that APP-26-09-799 (anh Viet 22/09/2026): ke toan tai to UNC len o
 * "Dinh uy nhiem chi", thumbnail hien ra, bam "Xac nhan da chuyen tien" thi
 * may chu bao "Chua dinh uy nhiem chi". tdkDs tra mang DUONG DAN (chuoi),
 * pvXacNhan lai lay x.url nen gui len [null] tu v414.
 *
 * Nap THAT pvXacNhan (04-tao-phieu.js) va tdkNap/tdkDs/tdkKho
 * (43-tep-dinh-kem.js). Chi bam nhu nguoi dung: tep da tai len o, bam xac nhan.
 *
 * Chay:  node vagabond/khung/kiem_thu/hanh_vi/unc_app_518.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var BEP = path.join(GOC, 'vagabond', 'public', 'js', 'bep');
var TP = fs.readFileSync(path.join(BEP, '04-tao-phieu.js'), 'utf8');
var TDK = fs.readFileSync(path.join(BEP, '43-tep-dinh-kem.js'), 'utf8');

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

var ket = { dat: 0, hong: 0, loi: [] };
function bang(mo, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(mo + ': duoc ' + JSON.stringify(a) + ', mong ' + JSON.stringify(b)); }
async function ca(ten, ham) {
  try { await ham(); ket.dat++; }
  catch (e) { ket.hong++; ket.loi.push(ten + '\n         ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n         ') : String(e))); }
}

function dung(th) {
  var goi = [], bao = [];
  var g = {
    TDK: {}, JSON: JSON, money: String, busy: function () {}, back: function () {}, toast: function () {},
    baoTin: function (s) { bao.push(s); },
    promptSheet: async function () { return ''; },
    confirmSheet: async function () { return true; },
    errMsg: function (e) { return String(e); },
    api: async function (m, a) { goi.push({ m: m, a: a }); return { ok: 1 }; },
    pvTh: th,
  };
  vm.createContext(g);
  vm.runInContext('var TDK = {};\n' + layHam(TDK, 'tdkKho') + '\n' + layHam(TDK, 'tdkNap') + '\n' +
    layHam(TDK, 'tdkDs') + '\n' + layHam(TP, 'pvXacNhan'), g);
  return { g: g, goi: goi, bao: bao };
}

(async function () {
  await ca('APP-26-09-799: tep UNC da tai len o, bam xac nhan thi gui DUNG duong dan len may chu', async function () {
    var m = dung({ so_unc: 0, du_tien: 1 });
    /* Nhu tdkTaiLen sau khi nap_tam tra ve: o giu doi tuong {url, ten, anh}. */
    m.g.tdkNap('pvunc', [{ url: '/private/files/vgb-unc-799.png', ten: 'screenshot-2026.png', anh: 1 }]);
    await m.g.pvXacNhan({ paid_amount: 5580000, party_name: 'PHÚC AN' }, 'APP-26-09-799');
    var x = m.goi.filter(function (c) { return c.m === 'vagabond.duyet_chi.xac_nhan_da_chuyen'; });
    bang('goi xac nhan mot lan', x.length, 1);
    bang('gui dung duong dan UNC', JSON.parse(x[0].a.unc), ['/private/files/vgb-unc-799.png']);
  });
  await ca('chua dinh UNC nao thi van chan ngay tren man, khong goi may chu', async function () {
    var m = dung({ so_unc: 0, du_tien: 1 });
    m.g.tdkNap('pvunc', []);
    await m.g.pvXacNhan({ paid_amount: 1, party_name: 'X' }, 'APP-1');
    bang('khong goi may chu', m.goi.length, 0);
    bang('bao thieu UNC', m.bao.length, 1);
  });
  console.log('Bo ca kiem HANH VI dinh uy nhiem chi o buoc xac nhan (APP-26-09-799)');
  ket.loi.forEach(function (d) { console.log('  HONG  ' + d); });
  console.log(ket.dat + ' ca dat, ' + ket.hong + ' ca hong, tong ' + (ket.dat + ket.hong) + ' ca.');
  process.exit(ket.hong ? 1 : 0);
})();
