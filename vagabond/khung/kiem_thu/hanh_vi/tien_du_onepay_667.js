/* v667 (Loan Anh 17/11/2026, đơn Pancake 97790): CHẠY THẬT ba hàm của màn
 * Sales (hoanMoFormDu, hoanChonDonCu, htFGui trong 11-khach-ca-hop-dong.js)
 * với máy chủ giả ghi lại từng lời gọi. Chuỗi thao tác đúng của Sales: bấm
 * Chuyển lại tiền dư, máy chưa thấy dư, chạm gợi ý đơn cũ 97615 (hoặc gõ số),
 * form mở với phần dư 880.000, bấm Gửi duyệt; đọc tham số máy chủ nhận.
 *
 * Chạy: node vagabond/khung/kiem_thu/hanh_vi/tien_du_onepay_667.js
 * In một dòng JSON {dat, hong, loi}; mã 0 là đạt.
 */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var BEP = path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep');
var NGUON = fs.readFileSync(path.join(BEP, '11-khach-ca-hop-dong.js'), 'utf8');
function layHam(src, ten) {
  var dau = src.search(new RegExp('\\n(?:async )?function ' + ten + '\\('));
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

function dung(ctx, traLoi, chon, go) {
  var goi = [];
  var g = {
    console: console, Promise: Promise, JSON: JSON, Number: Number, String: String, Math: Math, setTimeout: setTimeout,
    htF: null, busy: function () {}, toast: function (m) { goi.push(['toast', m]); },
    baoTin: function (m, t) { goi.push(['baoTin', m, t]); },
    money: function (n) { return String(Math.round(n || 0)); }, ngayNgan: function (s) { return String(s || ''); },
    hoanVeForm: function () { goi.push(['form', JSON.parse(JSON.stringify(g.htF))]); }, htNapGoiY: function () {},
    htFDong: function () {}, go: function () {}, scrHoanTien: function () {},
    confirmSheet: function () { return Promise.resolve(true); }, posXinPhep: function () { return Promise.resolve(''); },
    sheet: function (title, items, cur, onPick) { goi.push(['sheet', title, items]); var it = chon(items); if (it) onPick(it); },
    promptSheet: function () { return Promise.resolve(go); },
    api: function (m, a) { goi.push(['api', m, a]); return Promise.resolve(traLoi(m, a)); }
  };
  g.window = g;
  vm.runInNewContext(['hoanMoFormDu', 'hoanChonDonCu', 'htFGui'].map(function (t) { return layHam(NGUON, t); }).join('\n'), g);
  return { g: g, goi: goi };
}

function mayChu(m, a) {
  if (m === 'vagabond.hoan_tien.xem_tien_du') {
    if (!a.don_cu) return { duoc: 0, vi_sao: 'Đơn này chưa nhận dư đồng nào', cho_chon_don_cu: 1,
      goi_y_don_cu: [{ so: '97615', tien: 1650000, ngay: '2026-11-14' }] };
    return { duoc: 1, tran: 880000, da_nhan: 1650000, tong_don: 770000, don_cu: a.don_cu, ly_do: [] };
  }
  if (m === 'vagabond.hoan_tien.tao_tien_du') return { ho_so: 'HT-1', so_tien: 880000, noi_dung_ck: 'X' };
  return {};
}
function nghi() { return new Promise(function (r) { setTimeout(r, 15); }); }

var ket = { dat: 0, hong: 0, loi: [] };
async function ca(ten, ham) { try { await ham(); ket.dat++; } catch (e) { ket.hong++; ket.loi.push(ten + ': ' + e.message); } }
function la(nhan, a, b) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(nhan + ' được ' + JSON.stringify(a) + ' mong ' + JSON.stringify(b)); }

(async function () {
  await ca('chạm gợi ý đơn cũ 97615: form mở với phần dư 880.000 và gửi đúng số đơn cũ', async function () {
    var x = dung(null, mayChu, function (items) { return items[0]; });
    await x.g.hoanMoFormDu({ name: 'HDB-26-11-03188' });
    await nghi();
    var s = x.goi.filter(function (c) { return c[0] === 'sheet'; });
    la('hiện bảng chọn đơn cũ', s.length, 1);
    la('gợi ý đúng đơn, kèm ô gõ tay', s[0][2].map(function (i) { return i.value; }), ['97615', '']);
    var hoi = x.goi.filter(function (c) { return c[0] === 'api'; }).map(function (c) { return c[2].don_cu; });
    la('hỏi lại máy chủ với đơn cũ', hoi, ['', '97615']);
    var f = x.goi.filter(function (c) { return c[0] === 'form'; });
    la('form mở, phần dư và đơn cũ', [f.length, f[0][1].tran, f[0][1].don_cu], [1, 880000, '97615']);
    Object.assign(x.g.htF, { ly_do: 'Khac', dien_giai: 'Khách huỷ 1 bánh', ten_tk: 'NGUYEN A', so_tk: '0123', ngan_hang: 'MB' });
    await x.g.htFGui();
    var tao = x.goi.filter(function (c) { return c[0] === 'api' && c[1] === 'vagabond.hoan_tien.tao_tien_du'; });
    la('gửi phiếu nộp thừa kèm đơn cũ', [tao.length, tao[0][2].don_cu, tao[0][2].so_tien], [1, '97615', 880000]);
  });
  await ca('gõ tay số đơn cũ khi không có gợi ý', async function () {
    var x = dung(null, function (m, a) {
      var r = mayChu(m, a); if (r.goi_y_don_cu) r.goi_y_don_cu = []; return r;
    }, function (items) { return items[items.length - 1]; }, '97615');
    await x.g.hoanMoFormDu({ name: 'HDB-26-11-03188' });
    await nghi();
    var hoi = x.goi.filter(function (c) { return c[0] === 'api'; }).map(function (c) { return c[2].don_cu; });
    la('hỏi lại với số đã gõ', hoi, ['', '97615']);
  });
  await ca('đơn không trả OnePay, không có gợi ý: vẫn báo như cũ, không hiện bảng chọn', async function () {
    var x = dung(null, function () { return { duoc: 0, vi_sao: 'Đơn này chưa nhận dư đồng nào', cho_chon_don_cu: 0 }; },
      function (items) { return items[0]; });
    await x.g.hoanMoFormDu({ name: 'HDB-1' });
    await nghi();
    la('không bảng chọn', x.goi.filter(function (c) { return c[0] === 'sheet'; }).length, 0);
    la('báo lý do', x.goi.filter(function (c) { return c[0] === 'baoTin'; })[0][1], 'Đơn này chưa nhận dư đồng nào');
  });
  await ca('đơn có phần dư từ đầu (chuyển khoản dư): không hỏi đơn cũ, không gửi đơn cũ', async function () {
    var x = dung(null, function (m, a) {
      if (m === 'vagabond.hoan_tien.xem_tien_du') return { duoc: 1, tran: 50000, da_nhan: 820000, tong_don: 770000, don_cu: '' };
      return mayChu(m, a);
    }, function () { return null; });
    await x.g.hoanMoFormDu({ name: 'HDB-2' });
    await nghi();
    Object.assign(x.g.htF, { ly_do: 'Khac', dien_giai: 'Ship', ten_tk: 'A', so_tk: '1', ngan_hang: 'MB' });
    await x.g.htFGui();
    var tao = x.goi.filter(function (c) { return c[0] === 'api' && c[1] === 'vagabond.hoan_tien.tao_tien_du'; });
    la('không có ô đơn cũ', 'don_cu' in tao[0][2], false);
  });
  console.log(JSON.stringify(ket));
  process.exit(ket.hong ? 1 : 0);
})();
