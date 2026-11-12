/* v650 (anh Việt 12/11/2026): màn Gom yêu cầu mua có chip trạng thái từng món,
 * chip lọc đầu màn, dải tiến độ, tạm tính có VAT, nút Chốt không tràn ngang.
 * CHẠY THẬT các hàm của 70-gom-mua.js trong vm.
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/gom_chip_650.js
 */
'use strict';
var fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
var GOC = path.resolve(__dirname, '..', '..', '..', '..');
var SRC = fs.readFileSync(process.env.NGUON || path.join(GOC, 'vagabond', 'public', 'js', 'bep', '70-gom-mua.js'), 'utf8');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) return '';
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error(ten);
}
var g = {
  GM: { d: null, sua: {}, mo: {}, tim: '', loc: '' },
  h: function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); },
  kl: function (v, d) { return String(v).replace('.', ',') + ' ' + d; },
  num: function (v) { return String(v); }, money: function (v) { return Number(v).toLocaleString('vi-VN'); },
  dmy: function (x) { var p = String(x).split('-'); return p[2] + '/' + p[1] + '/' + p[0]; },
  anhMon: function () { return ''; }, today: function () { return '2026-11-12'; }, Math: Math, Date: Date, Number: Number, String: String
};
vm.createContext(g);
['gmSoMua', 'gmTien', 'gmCachNgay', 'gmGap', 'gmChipMon', 'gmHopLoc', 'gmThue', 'gmStChip', 'gmMon', 'gmNhom', 'gmTienDo', 'gmChipLoc'].forEach(function (t) {
  var ma = layHam(SRC, t); if (ma) vm.runInContext(ma, g);
});

var ket = { dat: 0, hong: 0 };
function ca(ten, fn) {
  try { fn(); ket.dat++; console.log('  DAT   ' + ten); } catch (e) { ket.hong++; console.log('  HONG  ' + ten + '\n        ' + e.message); }
}
function mon(x) { return Object.assign({ ma: 'M', ten: 'Hũ sốt giấy', dvt: 'Cái', xin: 2000, mua: 2000, ton: 0, cho_ve: 0, gia: 310, thue: 8, phieu: [{ phieu: 'YCMH-1' }], ngay_can: '' }, x); }
var NCC_DAI = 'CÔNG TY CỔ PHẦN PARADISE FINE FOODS VIỆT NAM';

ca('1. chip mon: ngay can (qua, hom nay, mai, sau), kho tong (het, con, du), cho ve, VAT, da sua', function () {
  var c = function (x, sua) { return JSON.parse(JSON.stringify(g.gmChipMon(mon(x), '2026-11-12', sua).map(function (y) { return y.c + ':' + y.t; }))); };
  assert.deepStrictEqual(c({ ngay_can: '2026-11-10' })[0], 'r:Quá ngày cần 10/11');
  assert.deepStrictEqual(c({ ngay_can: '2026-11-12' })[0], 'r:Cần hôm nay');
  assert.deepStrictEqual(c({ ngay_can: '2026-11-13' })[0], 'w:Cần ngày mai');
  assert.deepStrictEqual(c({ ngay_can: '2026-11-20' })[0], 'n:Cần 20/11');
  assert.deepStrictEqual(c({}), ['n:Kho tổng hết', 'b:VAT 8%']);
  assert.deepStrictEqual(c({ ton: 500 })[0], 'w:Kho tổng còn 500 Cái');
  assert.deepStrictEqual(c({ ton: 2000 })[0], 'g:Kho tổng đủ 2000 Cái');
  assert.deepStrictEqual(c({ cho_ve: 6 })[1], 'w:Đang chờ về 6 Cái');
  assert.deepStrictEqual(c({ thue: null })[1], 'w:Món chưa khai VAT');
  assert.deepStrictEqual(c({}, true).slice(-1)[0], 'b:Đã sửa số mua');
});

ca('2. tam tinh co VAT: 2000 x 310 = 620.000 d, VAT 8% = 49.600 d (khong hai lan)', function () {
  var nhom = { ncc: 'N1', ten_ncc: 'The Minhs', so_mon: 1, so_phieu: 1, mon: [mon({})] };
  assert.strictEqual(g.gmTien(nhom), 620000);
  assert.strictEqual(g.gmThue(nhom), 49600);
  var html = g.gmNhom(nhom, 0);
  assert.ok(html.indexOf('Tạm tính 620.000 đ + VAT 49.600 đ = <b>669.600 đ</b>') >= 0, html);
});

ca('3. ten nha cung cap dai khong nam trong nut Chot (het tran ngang), ten duoc xuong dong', function () {
  var html = g.gmNhom({ ncc: 'N2', ten_ncc: NCC_DAI, so_mon: 1, so_phieu: 1, mon: [mon({})] }, 0);
  var nut = html.slice(html.indexOf('<button class="btn gr"'));
  assert.ok(nut.indexOf(NCC_DAI) < 0, 'nut khong mang ten NCC');
  assert.ok(nut.indexOf('width:auto') < 0 && nut.indexOf('flex:0 0 auto') < 0, 'nut khong co chieu rong theo chu');
  assert.ok(html.indexOf('word-break:break-word">' + NCC_DAI) >= 0, 'ten NCC xuong dong');
});

ca('4. chip loc: dem dung, an chip rong; loc can gap, kho con hang, chua co NCC', function () {
  g.GM.loc = '';
  var nhom = [{ ncc: 'N1', mon: [mon({ ma: 'A', ngay_can: '2026-11-12' }), mon({ ma: 'B', ton: 5 })] }, { ncc: '', mon: [mon({ ma: 'C' })] }];
  var html = g.gmChipLoc(nhom);
  assert.ok(html.indexOf('Tất cả 3') >= 0 && html.indexOf('Cần gấp 1') >= 0 && html.indexOf('Kho tổng còn hàng 1') >= 0 && html.indexOf('Chưa có nhà cung cấp 1') >= 0, html);
  assert.ok(html.indexOf('Đã sửa số') < 0, 'chip rong thi an');
  assert.ok(g.gmHopLoc(nhom[0].mon[0], nhom[0], 'gap', '2026-11-12') && !g.gmHopLoc(nhom[0].mon[1], nhom[0], 'gap', '2026-11-12'));
  assert.ok(g.gmGap(mon({ ngay_can: '2026-11-13' }), '2026-11-12'), 'can ngay mai la gap');
  assert.ok(!g.gmGap(mon({ ngay_can: '2026-11-14' }), '2026-11-12'), 'can ngay kia chua gap');
  assert.ok(g.gmHopLoc(nhom[1].mon[0], nhom[1], 'ncc', '2026-11-12') && !g.gmHopLoc(nhom[0].mon[0], nhom[0], 'ncc', '2026-11-12'));
});

ca('5. dai tien do: buoc 2 dang o day', function () {
  var t = g.gmTienDo();
  assert.ok(t.indexOf('Thu mua gom, chốt đơn (đang ở đây)') >= 0 && t.indexOf('Kho nhận hàng') >= 0);
});

console.log('\n' + ket.dat + ' dat, ' + ket.hong + ' hong');
process.exit(ket.hong ? 1 : 0);
